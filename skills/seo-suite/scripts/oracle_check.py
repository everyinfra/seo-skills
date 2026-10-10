#!/usr/bin/env python3
"""Athena Oracle 协议的 agent 前置工具:用已验证品牌事实核查 AI 采样回答(stdlib-only)。

职责边界(先读):本脚本只做**可判定部分**——显式数字/日期/布尔冲突的正则近似。
语义级矛盾(定位漂移、受众错位、"最适合"式软冲突)不由本脚本判定,
由 agent 结合本输出人工复核。Possible sources 一律留空数组,由 agent 调查后填写
(Athena 口径:调查线索,非因果归因)。

输入:
  --facts      brand.yaml      Brand Records 事实库(格式见 references/content/brand-records.md:
               受限 YAML 子集:顶层 brand + facts 列表,每条
               {fact, record, source, date, confidence, keywords?};record 为六记录之一)
  --responses  responses.json  采样回答 [{prompt, engine, text, mentions?}]
               (由 citation_panel 导出或人工粘贴;mentions 容忍存在,不参与判定)
  --out        findings.json   状态文件(默认 findings.json):重跑时按 fingerprint
               保持人工状态 status: pending → acknowledged/ignored(可 reopen)
  --json                       输出 JSON 而非 markdown 报告

门槛(Athena 官方):已验证 facts <25 条 → 警告"样本不足,结论置信低"。

核查逻辑(可判定部分):
  1. 每条 fact 抽关键词组(显式 keywords 优先,否则自动:拉丁词 + CJK 去停词整段/二元组);
  2. 在每条 response 的每个句子中找相关表述(命中 ≥1 关键词才算相关);
  3. 冲突检测(正则近似):
     - 数字冲突:同 kind(货币/百分比/带单位数值)且数值不同;
     - 日期冲突:ISO 日期/年份不同;
     - 布尔冲突:同一关键词在事实与 AI 句中肯定/否定极性相反(分句内取反向窗口);
  4. finding 字段(Athena):ai_claim(命中句)/known_fact/why_flagged/severity
     (涉及价格/安全/合规=critical,否则 major)/source_response(引擎+prompt+序号)。

指标:
  Inaccuracy%          = 含 active(status≠ignored)finding 的响应数 ÷ 总响应数
  model_accuracy       = 按引擎分列的无 active finding 响应占比
  topics_ai_gets_wrong = active findings 按 fact 的 record(六记录)分组计数

用法:
  python3 oracle_check.py --facts brand.yaml --responses responses.json
  python3 oracle_check.py --facts brand.yaml --responses responses.json \
      --out findings.json --json
"""
import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

SIX_RECORDS = ("company", "market", "offerings", "audience", "strategy", "execution")
ATHENA_FACT_FLOOR = 25          # Athena 官方门槛:≥25 条已验证 facts 才能扫
STATUSES = ("pending", "acknowledged", "ignored", "reopen")
SCHEMA_VERSION = 1

BOUNDARY = ("正则近似只能抓显式数字/日期/布尔冲突;语义级矛盾(定位、受众、语气)由 agent "
            "结合本输出人工判定。Possible sources 为调查线索,非因果归因。")

# 涉及价格/安全/合规的 fact → critical,其余 → major
CRITICAL_RE = re.compile(
    r"价格|定价|费用|收费|免费|单价|付费|元/|price|pricing|cost|fee|paid|free"
    r"|安全|漏洞|加密|泄露|后门|security|vulnerab|encrypt|breach"
    r"|合规|监管|认证|审计|certif|compliance|gdpr|soc\s?2|iso\s?27001|hipaa|隐私|privacy"
    r"|sso|saml|oauth|2fa|mfa|单点登录|双因素|多因素", re.I)

STOP_EN = {"the", "a", "an", "of", "for", "in", "is", "are", "was", "were", "and", "or",
           "to", "with", "by", "on", "at", "as", "be", "been", "has", "have", "had",
           "it", "its", "we", "our", "you", "your", "their", "this", "that", "these",
           "those", "from", "not", "no", "can", "will", "per", "than", "more", "most",
           "also", "into", "over", "under", "but", "and", "all", "any"}
STOP_CJK_CHARS = set("的了是在和与及或等为有不于由从被把将其该各每所之以而就都还则等即可并但因故此那这外内去来")

_NUM = r"(?<![\d.])\d+(?:[.,]\d+)?(?!\d)"
VALUE_RE = re.compile(
    r"(?P<iso>(?<![\d.])(?:19|20)\d{2}[-/.]\d{1,2}(?:[-/.]\d{1,2})?(?!\d))"
    r"|(?P<csym>[$€£¥])\s*(?P<cnum1>" + _NUM + r")"
    r"|(?P<cnum2>" + _NUM + r")\s*(?:美元|美金|欧元|英镑|人民币|日元|港元|澳元|元)"
    r"|(?P<pct>" + _NUM + r")\s*%"
    r"|百分之\s*(?P<pct2>\d+(?:\.\d+)?)"
    r"|(?P<yr>(?<![\d.])(?:19|20)\d{2}(?!\d))(?:\s*(?:年|year|years))?"
    r"|(?P<gnum>" + _NUM + r")\s*(?:/\s*|per\s+|每\s*)?"
    r"(?P<gunit>(?:小时|分钟|秒钟|万个|[A-Za-z]{2,}|[个种条项名人次页台天月年周秒]))")

UNIT_SYN = {"day": "d", "days": "d", "天": "d", "hour": "h", "hours": "h", "小时": "h",
            "minute": "min", "minutes": "min", "分钟": "min",
            "second": "sec", "seconds": "sec", "秒": "sec", "秒钟": "sec",
            "week": "wk", "weeks": "wk", "周": "wk",
            "month": "mo", "months": "mo", "月": "mo",
            "year": "yr", "years": "yr", "年": "yr"}

NEG_BACK_EN = re.compile(r"\b(?:not|no|never|cannot|can'?t|don'?t|doesn'?t|didn'?t|"
                         r"isn'?t|aren'?t|wasn'?t|weren'?t|won'?t|without)\b", re.I)
NEG_BACK_ZH = re.compile(r"不|未|无|没有|无法|尚未")
FWD_NEG_EN = re.compile(r"\b(?:not|never)\s+(?:support|offer|offered|included?|provided?"
                        r"|available|compatible|free|open)\w*", re.I)
FWD_NEG_ZH = re.compile(r"(?:不|未|无法|没有)\s*(?:支持|提供|包含|兼容|可用|开放|免费)")
ASSERT_RE = re.compile(r"支持|提供|包含|包括|拥有|开源|免费|可用|允许|兼容|集成|开放|宣称"
                       r"|\b(?:support|offer|include|provide|available|open[-\s]?source"
                       r"|free|allow|integrate)\w*\b", re.I)
CLAUSE_SPLIT = re.compile(r"[,;;]|但是|但|\b(?:however|yet|while)\b")
SENT_SPLIT = re.compile(r"[。!?\n;；]+|(?<![\d.])\.(?!\d)")

CONF_MAP = {"high": "high", "med": "med", "medium": "med", "low": "low",
            "高": "high", "中": "med", "低": "low"}


# ---------- 输入解析(受限 YAML 子集;不依赖 PyYAML) ----------

def _parse_scalar(v):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [s.strip().strip("'\"") for s in inner.split(",") if s.strip()] if inner else []
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def parse_facts_yaml(path):
    """解析 brand.yaml 受限子集,返回 (brand, facts, warnings)。
    形状契约见 brand-records.md:顶层 `brand:`;`facts:` 列表,每条 `- fact:` 起行,
    其余键(record/source/date/confidence/keywords)缩进续行。"""
    brand, facts, warnings = "", [], []
    cur = None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            m_item = re.match(r"^\s+-\s+([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            m_kv = re.match(r"^\s+([A-Za-z_][\w-]*)\s*:\s*(.+)$", line)
            m_top = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            if m_item:
                cur = {m_item.group(1): _parse_scalar(m_item.group(2))}
                facts.append(cur)
            elif m_kv and cur is not None:
                cur[m_kv.group(1)] = _parse_scalar(m_kv.group(2))
            elif m_top:
                cur = None
                if m_top.group(1) == "brand":
                    brand = _parse_scalar(m_top.group(2))
    if not facts:
        raise ValueError("%s 中未解析到 facts(需顶层 facts: 与 '- fact:' 列表项)" % path)

    out = []
    for i, d in enumerate(facts, 1):
        fact_text = str(d.get("fact", "")).strip()
        if not fact_text:
            warnings.append("第 %d 条 fact 缺 fact 文本,已跳过" % i)
            continue
        record = str(d.get("record", "")).strip().lower()
        if record not in SIX_RECORDS:
            warnings.append("第 %d 条 record=%r 不在六记录内(按原样保留,分组时单列)"
                            % (i, record or "(缺)"))
        conf = CONF_MAP.get(str(d.get("confidence", "")).strip().lower(), "")
        kws = d.get("keywords", [])
        if isinstance(kws, str):
            kws = [kws]
        out.append({"fact": fact_text, "record": record,
                    "source": str(d.get("source", "")).strip(),
                    "date": str(d.get("date", "")).strip(),
                    "confidence": conf, "keywords": [str(k) for k in kws]})
    return brand, out, warnings


def load_responses(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("%s 应为 JSON 数组 [{prompt, engine, text, mentions?}]" % path)
    out = []
    for i, r in enumerate(data):
        if not isinstance(r, dict):
            continue
        text = str(r.get("text", "") or "")
        if not text.strip():
            continue
        out.append({"index_in_file": i, "prompt": str(r.get("prompt", "")),
                    "engine": str(r.get("engine", "") or "unknown"), "text": text})
    return out


# ---------- 关键词与数值抽取 ----------

def extract_topic_terms(text, explicit=None):
    """fact 的关键词组:显式 keywords 优先;否则自动抽(拉丁词 + CJK 去停词后整段与二元组)。"""
    if explicit:
        return [k.strip().lower() for k in explicit if k and k.strip()]
    terms = set()
    for m in re.finditer(r"[A-Za-z][A-Za-z0-9_-]*", text):
        w = m.group(0).lower()
        if len(w) >= 2 and w not in STOP_EN:
            terms.add(w)
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        s = "".join(ch for ch in run if ch not in STOP_CJK_CHARS)
        if not s:
            continue
        terms.add(s)
        for i in range(len(s) - 1):
            terms.add(s[i:i + 2])
    return sorted(terms)


def _tofloat(raw):
    s = raw.strip()
    if "," in s and "." in s:                    # 1,299.99 → 千分位
        s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", "") if re.fullmatch(r"\d{1,3}(?:,\d{3})+", s) else s.replace(",", ".")
    return float(s)


def _norm_unit(u):
    u = (u or "").strip().lower()
    u2 = u[:-1] if len(u) > 3 and u.endswith("s") else u
    return UNIT_SYN.get(u, UNIT_SYN.get(u2, u))


def extract_values(text):
    """抽取显式数值/日期:iso/currency/percent/year/generic(数字+单位)。裸数字不抽(噪音)。"""
    out = []
    for m in VALUE_RE.finditer(text or ""):
        if m.group("iso"):
            parts = re.split(r"[-/.]", m.group("iso"))
            out.append({"kind": "iso", "value": tuple(int(p) for p in parts),
                        "unit": "date", "raw": m.group("iso")})
        elif m.group("csym"):
            out.append({"kind": "currency", "value": _tofloat(m.group("cnum1")),
                        "unit": "cur", "raw": m.group(0)})
        elif m.group("cnum2"):
            out.append({"kind": "currency", "value": _tofloat(m.group("cnum2")),
                        "unit": "cur", "raw": m.group(0)})
        elif m.group("pct"):
            out.append({"kind": "percent", "value": _tofloat(m.group("pct")),
                        "unit": "pct", "raw": m.group(0)})
        elif m.group("pct2"):
            out.append({"kind": "percent", "value": _tofloat(m.group("pct2")),
                        "unit": "pct", "raw": m.group(0)})
        elif m.group("yr"):
            out.append({"kind": "year", "value": int(m.group("yr")),
                        "unit": "yr", "raw": m.group("yr")})
        elif m.group("gnum"):
            out.append({"kind": "generic", "value": _tofloat(m.group("gnum")),
                        "unit": _norm_unit(m.group("gunit")), "raw": m.group(0)})
    return out


def split_sentences(text):
    out = []
    for part in SENT_SPLIT.split(text or ""):
        p = part.strip()
        if len(p) >= 4:
            out.append(p)
    return out


# ---------- 冲突检测(正则近似层) ----------

def value_conflict(fact_vals, sent_vals):
    """同 (kind, unit) 桶内,句值与任一事实值相等→视为一致;否则首个不匹配者报冲突。"""
    for sv in sent_vals:
        key = (sv["kind"], sv["unit"])
        bucket = [fv for fv in fact_vals if (fv["kind"], fv["unit"]) == key]
        if not bucket:
            continue
        if sv["kind"] == "iso":
            if any(_iso_shared_equal(fv, sv) for fv in bucket):
                continue
        elif any(fv["value"] == sv["value"] for fv in bucket):
            continue
        fv = bucket[0]
        kind = "date" if sv["kind"] in ("iso", "year") else "number"
        return fv, sv, kind
    return None


def _iso_shared_equal(fv, sv):
    n = min(len(fv["value"]), len(sv["value"]))
    return all(fv["value"][k] == sv["value"][k] for k in range(n))


def _occurrence_negated(clause, pos, end):
    back = clause[max(0, pos - 26):pos]
    if NEG_BACK_ZH.search(back) or NEG_BACK_EN.search(back):
        return True
    fwd = clause[end:end + 20]
    return bool(FWD_NEG_ZH.search(fwd) or FWD_NEG_EN.search(fwd))


def polarity(text, term):
    """term 在 text 中的极性:任一非否定出现→pos,全否定→neg,未出现→None。分句评估。"""
    pols = []
    for cl in CLAUSE_SPLIT.split(text or ""):
        for m in re.finditer(re.escape(term), cl, re.I):
            pols.append("neg" if _occurrence_negated(cl, m.start(), m.end()) else "pos")
    if not pols:
        return None
    return "neg" if all(p == "neg" for p in pols) else "pos"


def _anchored_negation(text, term):
    """term 的某次出现其**前向**窗口内紧邻否定词(报告布尔冲突时优先这类术语,更具体)。"""
    for cl in CLAUSE_SPLIT.split(text or ""):
        for m in re.finditer(re.escape(term), cl, re.I):
            back = cl[max(0, m.start() - 26):m.start()]
            if NEG_BACK_ZH.search(back) or NEG_BACK_EN.search(back):
                return True
    return False


def _is_polarized(fact_text):
    return bool(ASSERT_RE.search(fact_text) or NEG_BACK_ZH.search(fact_text)
                or NEG_BACK_EN.search(fact_text))


def scan_responses(facts, responses):
    """逐 response × 逐 fact × 逐句:相关表述里的数字/日期/布尔冲突 → findings(pending)。"""
    prepared = []
    for fi, fact in enumerate(facts):
        terms = extract_topic_terms(fact["fact"], fact.get("keywords"))
        prepared.append({
            "fi": fi, "fact": fact, "terms": terms,
            "vals": extract_values(fact["fact"]),
            "pols": {t: polarity(fact["fact"], t) for t in terms},
            "polarized": _is_polarized(fact["fact"]),
        })
    findings, n = [], 0
    for ri, resp in enumerate(responses):
        seen = set()
        for p in prepared:
            for sent in split_sentences(resp["text"]):
                low = sent.lower()
                if not any(t in low for t in p["terms"]):
                    continue                              # 不相关表述不判定
                conf = value_conflict(p["vals"], extract_values(sent))
                if conf:
                    kind = conf[2]
                    if ("num", p["fi"]) not in seen:
                        seen.add(("num", p["fi"]))
                        n += 1
                        findings.append(_make_finding(
                            n, resp, ri, p["fact"], sent, kind, conf))
                    continue
                if p["polarized"]:
                    cands = []
                    for t in p["terms"]:
                        if len(t) < 2:
                            continue
                        fp, sp = p["pols"].get(t), polarity(sent, t)
                        if fp and sp and fp != sp:
                            cands.append((t, fp, sp, _anchored_negation(sent, t)))
                    if cands and ("bool", p["fi"]) not in seen:
                        cands.sort(key=lambda c: not c[3])   # 否定词紧邻的术语优先(更具体)
                        t, fp, sp = cands[0][:3]
                        seen.add(("bool", p["fi"]))
                        n += 1
                        findings.append(_make_finding(
                            n, resp, ri, p["fact"], sent, "boolean", None, term=t,
                            fp=fp, sp=sp))
    return findings


def _make_finding(n, resp, ri, fact, sent, kind, conf, term=None, fp=None, sp=None):
    if kind == "date":
        fv, sv = conf[0], conf[1]
        why = "日期冲突: 已验证事实=%s ↔ AI 表述=%s" % (fv["raw"], sv["raw"])
    elif kind == "number":
        fv, sv = conf[0], conf[1]
        why = ("数字冲突: 已验证事实=%s(kind=%s) ↔ AI 表述=%s(%s≠%s)"
               % (fv["raw"], fv["kind"] + "/" + fv["unit"], sv["raw"],
                  fv["value"], sv["value"]))
    else:
        why = ("布尔冲突: 事实与 AI 对「%s」极性相反(事实=%s, AI=%s;正则近似,需 agent 复核)"
               % (term, fp, sp))
    claim = sent if len(sent) <= 220 else sent[:217] + "..."
    return {
        "id": "F%03d" % n,
        "fingerprint": hashlib.sha1(
            ("%s|%s|%s" % (resp["engine"], resp["prompt"], fact["fact"]))
            .encode("utf-8")).hexdigest()[:12],
        "status": "pending",
        "severity": "critical" if CRITICAL_RE.search(fact["fact"]) else "major",
        "kind": kind,
        "ai_claim": claim,
        "known_fact": fact["fact"],
        "record": fact.get("record", ""),
        "fact_source": fact.get("source", ""),
        "fact_date": fact.get("date", ""),
        "confidence": fact.get("confidence", ""),
        "why_flagged": why,
        "source_response": {"index": ri, "engine": resp["engine"], "prompt": resp["prompt"]},
        "possible_sources": [],                          # ← 由 agent 调查后填写
    }


# ---------- 状态机(findings.json) ----------

def load_prev_state(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        return {f["fingerprint"]: f for f in payload.get("findings", [])
                if isinstance(f, dict) and f.get("fingerprint")}
    except (OSError, ValueError):
        return {}


def merge_state(findings, prev):
    """重跑保持人工状态:同 fingerprint 续 status 与 possible_sources。"""
    cur_fps = set()
    for f in findings:
        cur_fps.add(f["fingerprint"])
        old = prev.get(f["fingerprint"])
        if not old:
            continue
        if old.get("status") in STATUSES:
            f["status"] = old["status"]
        if isinstance(old.get("possible_sources"), list):
            f["possible_sources"] = old["possible_sources"]
    stale = [dict(v, recurred=False) for k, v in prev.items() if k not in cur_fps]
    return stale


# ---------- 指标与输出 ----------

def compute_metrics(findings, responses):
    active = [f for f in findings if f.get("status", "pending") != "ignored"]
    flagged = {f["source_response"]["index"] for f in active}
    total = len(responses)
    engines = {}
    for i, r in enumerate(responses):
        d = engines.setdefault(r["engine"], {"total": 0, "flagged": 0})
        d["total"] += 1
        d["flagged"] += (i in flagged)
    return {
        "inaccuracy_pct": round(100.0 * len(flagged) / total, 1) if total else None,
        "engines": engines,
        "model_accuracy": {e: round(100.0 * (d["total"] - d["flagged"]) / d["total"], 1)
                           for e, d in sorted(engines.items()) if d["total"]},
        "topics_ai_gets_wrong": dict(Counter(f["record"] for f in active if f.get("record"))),
    }


def _pct(x):
    return "N/A" if x is None else "%.1f%%" % x


def render_markdown(brand, facts, responses, warnings, findings, metrics):
    n_active = sum(1 for f in findings if f["status"] != "ignored")
    n_ignored = len(findings) - n_active
    L = ["# Oracle 品牌事实核查报告(正则近似层)", ""]
    L.append("- brand: %s" % (brand or "(未标)"))
    L.append("- facts: %d 条 · responses: %d · findings: %d(active %d / ignored %d)"
             % (len(facts), len(responses), len(findings), n_active, n_ignored))
    if metrics["engines"]:
        L.append("- engines: " + ", ".join("%s(%d)" % (e, d["total"])
                                            for e, d in sorted(metrics["engines"].items())))
    L.append("")
    for w in warnings:
        L.append("[!] %s" % w)
    if warnings:
        L.append("")
    L.append("## 指标")
    L.append("")
    flagged_n = len({f["source_response"]["index"]
                     for f in findings if f["status"] != "ignored"})
    L.append("- Inaccuracy%% = %s(%d/%d 响应含 active finding)"
             % (_pct(metrics["inaccuracy_pct"]), flagged_n, len(responses)))
    L.append("- Model accuracy(按引擎,无 active finding 响应占比):")
    for e, acc in metrics["model_accuracy"].items():
        d = metrics["engines"][e]
        L.append("  - %s: %s(%d/%d 无 finding)" % (e, _pct(acc), d["total"] - d["flagged"],
                                                   d["total"]))
    L.append("- Topics AI gets wrong(按 Brand Record 分组,active findings):")
    if metrics["topics_ai_gets_wrong"]:
        for rec, c in sorted(metrics["topics_ai_gets_wrong"].items(),
                             key=lambda kv: -kv[1]):
            L.append("  - %s: %d" % (rec, c))
    else:
        L.append("  - (无)")
    L.append("")
    L.append("## Findings(%d)" % len(findings))
    for f in findings:
        L.append("")
        L.append("### %s · %s · %s · [%s]" % (f["id"], f["severity"], f["kind"], f["status"]))
        sr = f["source_response"]
        L.append("- engine: %s · prompt: %s · response #%d" % (sr["engine"], sr["prompt"],
                                                               sr["index"]))
        L.append("- AI claim: “%s”" % f["ai_claim"])
        L.append("- Known fact: “%s”(%s · %s · %s · confidence=%s)"
                 % (f["known_fact"], f["record"] or "?", f["fact_source"] or "?",
                    f["fact_date"] or "?", f["confidence"] or "?"))
        L.append("- Why flagged: %s" % f["why_flagged"])
        L.append("- Possible sources: %s(由 agent 填写——调查线索,非因果归因)"
                 % json.dumps(f["possible_sources"], ensure_ascii=False))
    L.append("")
    L.append("## 边界(必读)")
    L.append("")
    L.append("- %s" % BOUNDARY)
    L.append("- 状态机: pending → 人工改 acknowledged/ignored(可 reopen)后重跑,"
             "状态经 findings.json 保持;ignored 不计入指标。")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Athena Oracle 前置核查:品牌 facts × AI 采样回答的冲突检测(正则近似层)",
        epilog="示例: python3 oracle_check.py --facts brand.yaml --responses responses.json"
               " --out findings.json")
    ap.add_argument("--facts", required=True,
                    help="brand.yaml(Brand Records 受限 YAML 子集,见 references/content/brand-records.md)")
    ap.add_argument("--responses", required=True,
                    help="responses.json: [{prompt, engine, text, mentions?}](citation_panel 导出或人工粘贴)")
    ap.add_argument("--out", default="findings.json",
                    help="findings 状态文件,重跑按 fingerprint 保持 status(默认 findings.json)")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而非 markdown 报告")
    args = ap.parse_args(argv)

    try:
        brand, facts, warnings = parse_facts_yaml(args.facts)
    except (OSError, ValueError) as e:
        print("错误: 无法解析 facts: %s" % e, file=sys.stderr)
        return 1
    try:
        responses = load_responses(args.responses)
    except (OSError, ValueError) as e:
        print("错误: 无法读取 responses: %s" % e, file=sys.stderr)
        return 1

    if len(facts) < ATHENA_FACT_FLOOR:
        warnings.append("样本不足: facts=%d < %d(Athena 官方门槛 25 条已验证 facts),结论置信低"
                        % (len(facts), ATHENA_FACT_FLOOR))
    if not responses:
        warnings.append("responses 为空,无可核查内容")

    prev = load_prev_state(args.out)
    findings = scan_responses(facts, responses)
    stale = merge_state(findings, prev)
    metrics = compute_metrics(findings, responses)

    state = {"schema_version": SCHEMA_VERSION,
             "generated": datetime.now().isoformat(timespec="seconds"),
             "findings": findings + stale}
    try:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print("错误: 无法写 %s: %s" % (args.out, e), file=sys.stderr)
        return 1

    if args.json:
        payload = {"schema_version": SCHEMA_VERSION,
                   "generated": state["generated"],
                   "brand": brand,
                   "facts_count": len(facts),
                   "responses_count": len(responses),
                   "warnings": warnings,
                   "metrics": metrics,
                   "findings": findings,
                   "boundary": BOUNDARY}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(brand, facts, responses, warnings, findings, metrics))
        print("\n[i] findings 状态已写入: %s(改 status 后重跑可保持)" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
