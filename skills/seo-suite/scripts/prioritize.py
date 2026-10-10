#!/usr/bin/env python3
"""条件优先级引擎(Botify ActionBoard "it depends" 口径;stdlib only)。
读 site_audit.py --json(逐页数据,完整引擎)或 health_score.py --json(摘要,优先识别,
但无逐页字段——条件依赖型规则降级)→ 声明式规则库打分排序:
- impact = 命中 URL 占比 × 严重度权重(CRITICAL=3/WARN=2/INFO=1)× 放大器【Ryte 公式形制】
- 两栏输出(Ryte 口径):"立即处理"(impact>0 降序)/"值得探索"(Opportunity 类)
- 放大器【Botify 官方】:问题页被内链指向>10 次 → 该规则 impact×1.5
- 条件依赖型【Botify 精髓】:
  noindex 是否问题取决于意图(输出 conditional 提示而非直接 critical);
  canonical 对错取决于 PageRank 对比(有数据自动判,缺数据标"需人工判定");
  未索引 + GSC clicks>0 = 紧急 / 未索引 + 零流量 = 低 / 缺 GSC 上下文 = 按中优先级(降级标注)
- 组合信号型:重定向 × canonical 交叉(3xx 页再指他页 canonical = 信号打架)
- --segment regex:切换 segment 重算优先级【Botify 官方行为】
- --rules-json custom.json:用户自定义规则(同 schema,按 id 覆盖内置/新 id 追加合并)
用法: python3 prioritize.py --audit audit.json [--segment "/pricing|/docs"]
                             [--rules-json custom.json] [--json]
退出码: 0 正常 / 2 输入或参数错误。"""
import json
import os
import re
import sys
from urllib.parse import urlparse

SCHEMA_VERSION = "1.0"
SEVS = ("CRITICAL", "WARN", "INFO")
SEV_WEIGHT = {"CRITICAL": 3.0, "WARN": 2.0, "INFO": 1.0}  # 严重度权重[推断,与 health_score 数值映射同源]
COVERAGE_NOTE = "基于样本,优先级不可外推到未爬取页面(Ryte/Botify 口径)"
# 放大器【Botify 官方】:内链指向问题页且被链>10 次 → impact×1.5
AMPLIFIER = {"signal": "inlinks", "gt": 10, "factor": 1.5}
URL_QUERY_LIMIT = 20  # 每条规则附过滤后 URL 清单的前 20 条


def die(msg):
    """输入/参数错误 → stderr + 退出码 2。"""
    sys.stderr.write(msg + "\n")
    sys.exit(2)


# ---------------------------------------------------------------- 页级信号提取
# Botify 精髓:规则引用页面级字段做条件;字段可来自 site_audit meta,或外链抓取工具
# (Botify/Screaming Frog 导出)合入 record/meta 的 depth/inlinks/gsc_clicks 等扩展键。
# 信号返回 None = 该 URL 无此数据(规则可降级),False/数值 = 已判定。

def _pick(rec, *names):
    """从 record 顶层与 meta 里依序取第一个非 None 值。"""
    meta = rec.get("meta") if isinstance(rec.get("meta"), dict) else {}
    for n in names:
        for src in (meta, rec):
            if isinstance(src, dict) and src.get(n) is not None:
                return src[n]
    return None


def _num(v):
    """数值化:int/float 直取;"52 chars/60" 这类字符串取前缀数字;bool 记 None。"""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.match(r"\s*(\d+(?:\.\d+)?)", str(v))
    return float(m.group(1)) if m else None


def _findings(rec):
    return [f for f in (rec.get("findings") or []) if isinstance(f, dict)]


def sig_depth(rec, url):
    return _num(_pick(rec, "depth", "click_depth", "clicks_from_home"))


def sig_inlinks(rec, url):
    return _num(_pick(rec, "inlinks", "incoming_links", "internal_inlinks"))


def sig_title_len(rec, url):
    t = _pick(rec, "title")
    if isinstance(t, str) and t.strip():
        return float(len(t))
    return _num(_pick(rec, "title_len"))


def sig_desc_len(rec, url):
    d = _pick(rec, "description", "desc")
    if isinstance(d, str) and d.strip():
        return float(len(d))
    return _num(_pick(rec, "desc_len"))


def sig_words(rec, url):
    return _num(_pick(rec, "words", "word_count"))


def sig_similarity(rec, url):
    return _num(_pick(rec, "similarity", "duplicate_similarity"))


def sig_canonical_similarity(rec, url):
    return _num(_pick(rec, "canonical_similarity"))


def sig_noindex(rec, url):
    """noindex 可从 meta.robots/meta.noindex 或 site_audit findings(area=robots)确证;
    无证据 = False(已判定:未设 noindex)——与 not_indexed 的 None 语义区分。"""
    if _pick(rec, "noindex") is True:
        return True
    mr = str(_pick(rec, "robots", "meta_robots", "x_robots_tag") or "").lower()
    if "noindex" in mr:
        return True
    for f in _findings(rec):
        if f.get("area") == "robots" and "noindex" in str(f.get("message", "")).lower():
            return True
    return False


def sig_indexed(rec, url):
    v = _pick(rec, "indexed", "in_index")
    return None if v is None else bool(v)


def sig_not_indexed(rec, url):
    """未索引:noindex 自设屏蔽,或外链工具的 indexed=False;两者皆缺 → None(不可判定)。"""
    if sig_noindex(rec, url):
        return True
    idx = sig_indexed(rec, url)
    return None if idx is None else (not idx)


def sig_gsc_clicks(rec, url):
    c = _pick(rec, "gsc_clicks", "clicks")
    if c is None:
        g = _pick(rec, "gsc")
        if isinstance(g, dict):
            c = g.get("clicks")
    return _num(c)


def sig_pagerank(rec, url):
    return _num(_pick(rec, "pagerank", "deeprank", "authority"))


def sig_canonical_pagerank(rec, url):
    return _num(_pick(rec, "canonical_pagerank", "canonical_deeprank"))


def sig_canonical_target(rec, url):
    c = _pick(rec, "canonical", "canonical_url")
    return c if isinstance(c, str) and c.strip() else None


def sig_canonical_other(rec, url):
    """canonical 指向他页(非自指)→ True;自指 → False;无 canonical 字段 → None。"""
    ct = sig_canonical_target(rec, url)
    if ct is None:
        return None
    cu = urlparse(ct if "://" in ct else "//" + urlparse(url).netloc +
                  (ct if ct.startswith("/") else "/" + ct))
    uu = urlparse(url)
    return not (cu.netloc.lower() == uu.netloc.lower()
                and cu.path.rstrip("/") == uu.path.rstrip("/"))


def sig_redirect(rec, url):
    st = _num(_pick(rec, "status", "http_status"))
    if st in (301.0, 302.0, 307.0, 308.0):
        return True
    if _pick(rec, "redirect_to", "redirects_to"):
        return True
    return None if st is None and not _pick(rec, "redirect_to", "redirects_to") else False


def sig_redirect_and_canonical_other(rec, url):
    r, c = sig_redirect(rec, url), sig_canonical_other(rec, url)
    if r is None or c is None:
        return None
    return r and c


def sig_url_len(rec, url):
    return float(len(url))


SIGNALS = {
    "depth": sig_depth, "inlinks": sig_inlinks,
    "title_len": sig_title_len, "desc_len": sig_desc_len,
    "words": sig_words, "similarity": sig_similarity,
    "canonical_similarity": sig_canonical_similarity,
    "noindex": sig_noindex, "indexed": sig_indexed, "not_indexed": sig_not_indexed,
    "gsc_clicks": sig_gsc_clicks, "pagerank": sig_pagerank,
    "canonical_pagerank": sig_canonical_pagerank,
    "canonical_target": sig_canonical_target, "canonical_other": sig_canonical_other,
    "redirect": sig_redirect, "redirect_and_canonical_other": sig_redirect_and_canonical_other,
    "url_len": sig_url_len,
    # "finding" 是特殊 detect:按 thresholds{area[,severity][,message_contains]} 匹配
    # site_audit findings,不走本数值信号表(引擎单独处理)。
}


# ---------------------------------------------------------------- 声明式规则库
# 内置 18 条;阈值注明【Botify 官方】的为官方口径,其余为映射自 site_audit findings
# 的等价规则。conditional_mode 三种:intent_hint(永远不直接 critical)/
# pagerank_compare(有数据自动判,缺数据需人工)/ gsc_traffic(GSC 三档分流)。
RULES = [
    {"id": "depth_deep", "category": "information_architecture", "severity": "WARN",
     "detect": "depth", "thresholds": {"gte": 6},
     "conditional": "是否上移取决于页面价值:重要页(转化/收入路径)优先上移,低价值深层页可留原位",
     "fix": "上移:距首页点击深度≥6 的页压缩到≤5(导航/面包屑/相关内链)【Botify 官方阈值】"},
    {"id": "inlinks_low", "category": "internal_linking", "severity": "WARN",
     "detect": "inlinks", "thresholds": {"lt": 4},
     "fix": "入链<4:增至≥5 条内链(从相关主题页/枢纽页补链)【Botify 官方阈值】"},
    {"id": "title_short", "category": "meta_tags", "severity": "WARN",
     "detect": "title_len", "thresholds": {"gt": 0, "lt": 50},
     "fix": "title<50 字符:扩到 50-60(保留主关键词,自然语句)【Botify 官方阈值】"},
    {"id": "desc_short", "category": "meta_tags", "severity": "WARN",
     "detect": "desc_len", "thresholds": {"gt": 0, "lt": 100},
     "fix": "description<100 字符:扩到 ~155(补齐利益点+CTA)【Botify 官方阈值】"},
    {"id": "thin_content", "category": "content", "severity": "WARN",
     "detect": "words", "thresholds": {"lt": 100},
     "conditional": "模板页(联系/法务/登录)词数低是合理的——命中后先分型再修",
     "fix": "thin content<100 词:增补实质内容(模板页除外)【Botify 官方阈值】"},
    {"id": "duplicate_body", "category": "duplication", "severity": "WARN",
     "detect": "similarity", "thresholds": {"gte": 90},
     "fix": "批内相似度≥90%:合并成一篇或差异化改写+canonical 收敛【Botify 官方阈值】"},
    {"id": "canonical_mismatch", "category": "canonicalization", "severity": "WARN",
     "detect": "canonical_similarity", "thresholds": {"lt": 75},
     "fix": "canonical 配对相似度<75%:canonical 不成立,移除【Botify 官方阈值】"},
    {"id": "noindex_intent", "category": "indexability", "severity": "WARN",
     "detect": "noindex", "thresholds": {"truthy": True},
     "conditional_mode": "intent_hint",
     "conditional": "noindex 是否问题取决于意图:感谢页/站内搜索/隐私页 noindex 是正确的",
     "fix": "按意图判定:该有搜索流量的页→移除 noindex;故意不索引→保持并留档"},
    {"id": "canonical_pagerank", "category": "canonicalization", "severity": "WARN",
     "detect": "canonical_other", "thresholds": {"truthy": True},
     "conditional_mode": "pagerank_compare",
     "conditional": "canonical 对错取决于 PageRank 对比:指向页权重更高=对,反之=错",
     "fix": "对比两页权重(PageRank/内链):让渡对象更强→保留;更弱→回撤 canonical"},
    {"id": "redirect_canonical_conflict", "category": "combination", "severity": "WARN",
     "detect": "redirect_and_canonical_other", "thresholds": {"truthy": True},
     "conditional": "组合信号(重定向×canonical):3xx 已声明权威指向,canonical 再指他页=信号打架",
     "fix": "重定向页不留 canonical(或只指向最终目标),消除 3xx×canonical 交叉【Botify 组合信号型】"},
    {"id": "not_indexed_with_traffic", "category": "indexability", "severity": "WARN",
     "detect": "not_indexed", "thresholds": {"truthy": True},
     "conditional_mode": "gsc_traffic",
     "conditional": "未索引+历史流量[GSC clicks>0]=紧急;未索引+零流量=低;缺 GSC 上下文=按中优先级",
     "fix": "恢复索引:有历史流量的页优先(检查 noindex/robots 屏蔽/canonical 让渡)"},
    {"id": "title_missing", "category": "meta_tags", "severity": "CRITICAL",
     "detect": "finding", "thresholds": {"area": "title", "severity": "CRITICAL"},
     "fix": "补 title(缺失)——每页唯一,50-60 字符"},
    {"id": "desc_missing", "category": "meta_tags", "severity": "CRITICAL",
     "detect": "finding", "thresholds": {"area": "description", "severity": "CRITICAL"},
     "fix": "补 meta description(~155 字符)"},
    {"id": "h1_missing", "category": "content", "severity": "CRITICAL",
     "detect": "finding", "thresholds": {"area": "h1", "severity": "CRITICAL"},
     "fix": "补唯一 H1(与 title 呼应但不重复)"},
    {"id": "fetch_error", "category": "crawlability", "severity": "CRITICAL",
     "detect": "finding", "thresholds": {"area": "fetch", "severity": "CRITICAL"},
     "fix": "修复抓取失败(HTTP 错误/超时):先恢复 200 可达再谈其他"},
    {"id": "staging_exposed", "category": "crawlability", "severity": "CRITICAL",
     "detect": "finding", "thresholds": {"area": "staging", "severity": "CRITICAL"},
     "fix": "staging 子域加鉴权或整站屏蔽(防重复内容/内部泄漏)"},
    {"id": "canonical_invalid", "category": "canonicalization", "severity": "CRITICAL",
     "detect": "finding", "thresholds": {"area": "canonical", "severity": "CRITICAL"},
     "fix": "修 canonical:相对 URL → 绝对 URL"},
    {"id": "url_long", "category": "opportunity", "severity": "INFO",
     "detect": "url_len", "thresholds": {"gt": 115},
     "fix": "URL>115 字符:缩短层级/参数(SF 官方定级 Opportunity——不扣分,值得探索)"},
]

# health_score --json 摘要输入的 area → 内置规则映射(该输入无逐页字段,findings 型
# 规则的修复文案从这里取;robots/canonical 保留条件依赖型语义)
AREA_RULE = {"title": "title_missing", "description": "desc_missing", "h1": "h1_missing",
             "fetch": "fetch_error", "staging": "staging_exposed", "canonical": "canonical_invalid",
             "robots": "noindex_intent", "content": "thin_content", "duplicate_title": "duplicate_body"}
# robots/canonical 在摘要输入下按条件依赖型处理:降为 WARN + 需人工判定,不直接 critical
AREA_CONDITIONAL = {"robots": "noindex_intent", "canonical": "canonical_pagerank"}

USAGE = """usage: prioritize.py --audit audit.json [--segment regex] [--rules-json custom.json] [--json]
条件优先级引擎(Botify ActionBoard 口径):
  impact = 命中 URL 占比 × 严重度权重(CRITICAL=3/WARN=2/INFO=1)× 放大器
  放大器【Botify 官方】:问题页被内链指向>10 次 → 该规则 impact×1.5
  两栏输出(Ryte 口径):"立即处理"(impact>0 降序) / "值得探索"(Opportunity 类)
  条件依赖型(输出 conditional 提示而非直接 critical):
    noindex 是否问题取决于意图(需人工判定);
    canonical 对错取决于 PageRank 对比(pagerank/canonical_pagerank 字段在场则自动判);
    未索引+GSC clicks>0=紧急 / 零流量=低 / 缺 GSC 上下文=按中优先级(降级标注);
    组合信号:重定向×canonical 交叉。
选项:
  --audit audit.json    site_audit.py --json 输出(逐页数据,完整引擎);也接受
                        health_score.py --json 摘要(优先识别——条件依赖型规则降级)
  --segment regex       URL 正则(如 "/pricing|/docs")——切换 segment 重算优先级【Botify 官方行为】
  --rules-json custom   自定义规则 {"rules":[{id,category,detect,thresholds,severity,
                        conditional,conditional_mode,fix}]};按 id 覆盖内置,新 id 追加
  --json                结构化输出 {schema_version,input_format,segment,urls_total,
                        context,fix_now[],explore[],no_hit_rules[],degraded_rules[],
                        degradation_notes[],coverage_note};每条含 impact/amplifier/
                        conditional/fix_instruction/url_query(命中 URL 前 20)
可用信号(detect): %s
内置规则: %s
退出码: 0 正常 / 2 输入或参数错误(文件缺/JSON 不可解析/regex 非法/segment 0 命中/自定义规则 schema 不合)。""" % (
    ", ".join(sorted(SIGNALS)) + ", finding", ", ".join(r["id"] for r in RULES))


# ---------------------------------------------------------------- 输入装载
def load_json_blob(path):
    """读入并解析 JSON;容忍文件前部混有逐 URL 文本行(与 health_score.load_audit 同法):
    整体解析失败时从每个 '{' 起点试解,取能解析成 dict 的末位候选。"""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        die("读不了输入文件: %s" % e)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = None
        for i, ch in enumerate(text):
            if ch != "{":
                continue
            try:
                cand = json.loads(text[i:])
            except json.JSONDecodeError:
                continue
            if isinstance(cand, dict):
                data = cand
    if not isinstance(data, dict):
        die("无法从 %s 解析出 JSON(应为 site_audit.py --json 或 health_score.py --json 输出)" % path)
    return data


def detect_format(data):
    """health_score --json 优先识别:含 impacts 列表即摘要格式;含 results 字典为 site_audit。"""
    if isinstance(data.get("impacts"), list) and "main_score" in data:
        return "health_score"
    if isinstance(data.get("results"), dict):
        return "site_audit"
    die("无法识别的输入格式(既无 results 也无 impacts;应为 site_audit.py --json 或 "
        "health_score.py --json 输出)")


def load_custom_rules(path, builtin):
    """--rules-json:同 schema 合并内置(同 id 覆盖缺省键,新 id 追加);schema 不合退出码 2。"""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        die("读不了自定义规则 %s: %s" % (path, e))
    raw = data.get("rules") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        die("自定义规则应为 {\"rules\":[...]} 或裸列表,得到 %s" % type(raw).__name__)
    merged = {r["id"]: dict(r) for r in builtin}
    order = [r["id"] for r in builtin]
    for r in raw:
        if not isinstance(r, dict):
            die("自定义规则每条须为对象: %r" % (r,))
        rid = r.get("id")
        for key in ("id", "category", "detect", "fix"):
            if not isinstance(r.get(key), str) or not r[key].strip():
                die("自定义规则缺少必填字符串字段 %s: %r" % (key, r))
        if r["detect"] not in SIGNALS and r["detect"] != "finding":
            die("自定义规则 %r 的 detect %r 未知;可用: %s, finding"
                % (rid, r["detect"], ", ".join(sorted(SIGNALS))))
        sev = str(r.get("severity", "WARN")).upper()
        if sev not in SEVS:
            die("自定义规则 %r 的 severity %r 未知;可用: %s" % (rid, r.get("severity"), "|".join(SEVS)))
        th = r.get("thresholds", {})
        if not isinstance(th, dict):
            die("自定义规则 %r 的 thresholds 须为对象" % rid)
        if r["detect"] == "finding" and not isinstance(th.get("area"), str):
            die("自定义规则 %r 为 finding 型,thresholds.area 必填(site_audit area 名)" % rid)
        norm = {"id": rid, "category": r["category"], "detect": r["detect"],
                "severity": sev, "thresholds": th, "fix": r["fix"]}
        for k in ("conditional", "conditional_mode"):
            if isinstance(r.get(k), str) and r[k].strip():
                norm[k] = r[k]
        if rid in merged:
            base = dict(merged[rid])
            base.update(norm)
            merged[rid] = base
        else:
            merged[rid] = norm
            order.append(rid)
    return [merged[i] for i in order]


# ---------------------------------------------------------------- 判定引擎
def threshold_hit(v, th):
    """阈值判定(gte/gt/lte/lt/truthy 全部满足才命中);v=None 一律不命中。"""
    if v is None:
        return False
    if "gte" in th and not v >= th["gte"]:
        return False
    if "gt" in th and not v > th["gt"]:
        return False
    if "lte" in th and not v <= th["lte"]:
        return False
    if "lt" in th and not v < th["lt"]:
        return False
    if th.get("truthy") and not v:
        return False
    return True


def base_hits(rule, records):
    """第一遍:阈值/finding 初筛命中(未做条件依赖型后处理)。返回 (hit_urls, covered)。"""
    det = rule["detect"]
    hits, covered = [], 0
    if det == "finding":
        th = rule["thresholds"]
        for url, rec in records.items():
            for f in _findings(rec):
                if f.get("area") != th.get("area"):
                    continue
                if "severity" in th and f.get("severity") != th["severity"]:
                    continue
                mc = th.get("message_contains")
                if mc and mc.lower() not in str(f.get("message", "")).lower():
                    continue
                hits.append(url)
                break
        covered = len(records)  # findings 结构恒在场(site_audit 输出),不算缺数据
        return hits, covered
    fn = SIGNALS[det]
    for url, rec in records.items():
        v = fn(rec, url)
        if v is not None:
            covered += 1
            if threshold_hit(v, rule["thresholds"]):
                hits.append(url)
    return hits, covered


def amplify(hits, records):
    """放大器【Botify 官方】:命中页被内链指向>10 次 → 规则 impact×1.5。"""
    amp = [u for u in hits
           if (sig_inlinks(records[u], u) or 0) > AMPLIFIER["gt"]]
    return amp


def apply_conditional(rule, hits, records):
    """条件依赖型后处理【Botify 精髓】。返回 (hits, severity, conditional, note)。
    - intent_hint:noindex 输出 conditional 提示而非直接 critical(恒 WARN + 需人工)
    - pagerank_compare:canonical 对错取决于 PageRank 对比——两字段在场自动判
      (让渡对象更强→从命中中剔除),缺数据→保留命中并标需人工
    - gsc_traffic:未索引 三档分流(紧急/低/中),缺 GSC 记降级注"""
    mode = rule.get("conditional_mode")
    sev, cond, note = rule["severity"], None, None
    if mode == "intent_hint":
        # 官方语义:"noindex 是否问题取决于意图"——不直接给 critical,交人工判定
        sev = "WARN" if sev == "CRITICAL" else sev
        cond = {"question": rule.get("conditional", ""), "needs_human": True,
                "verdict_hint": "感谢页/站内搜索/隐私页→保持 noindex;内容页/落地页→移除"}
        return hits, sev, cond, note
    if mode == "pagerank_compare":
        keep, auto_ok, auto_bad, human = [], 0, 0, 0
        for u in hits:
            pr = sig_pagerank(records[u], u)
            cpr = sig_canonical_pagerank(records[u], u)
            if pr is not None and cpr is not None:
                if cpr >= pr:
                    auto_ok += 1            # 让渡对象权重更高 → canonical 正确,剔除
                else:
                    auto_bad += 1
                    keep.append(u)
            else:
                human += 1
                keep.append(u)
        verdicts = {"auto_correct": auto_ok, "auto_wrong": auto_bad, "needs_human": human}
        cond = {"question": rule.get("conditional", ""), "needs_human": human > 0,
                "verdicts": verdicts,
                "verdict_hint": "canonical 目标页 PageRank≥本页 → 保留;更低 → 回撤"}
        if human:
            note = "canonical_pagerank: 缺 PageRank 对比数据,%d URL 需人工判定" % human
        sev = "WARN" if sev == "CRITICAL" else sev
        return keep, sev, cond, note
    if mode == "gsc_traffic":
        urgent, low, mid = [], [], []
        for u in hits:
            c = sig_gsc_clicks(records[u], u)
            if c is None:
                mid.append(u)
            elif c > 0:
                urgent.append(u)
            else:
                low.append(u)
        sev = "CRITICAL" if urgent else ("WARN" if mid else "INFO")
        cond = {"question": rule.get("conditional", ""), "needs_human": False,
                "urgency_split": {"紧急(历史 clicks>0)": len(urgent),
                                  "低(零流量)": len(low),
                                  "中(缺 GSC 上下文)": len(mid)},
                "urgent_urls": urgent[:URL_QUERY_LIMIT]}
        if mid:
            note = "not_indexed_with_traffic: 缺 GSC 上下文,%d URL 按中优先级" % len(mid)
        return hits, sev, cond, note
    if isinstance(rule.get("conditional"), str) and rule["conditional"]:
        cond = {"question": rule["conditional"], "needs_human": False}
    return hits, sev, cond, note


def make_item(rule, hits, sev, cond, amp_urls, total):
    factor = AMPLIFIER["factor"] if amp_urls else 1.0
    impact = round(len(hits) / total * SEV_WEIGHT[sev] * factor, 4) if total else 0.0
    item = {"rule": rule["id"], "category": rule["category"], "severity": sev,
            "hit_urls": len(hits), "total_urls": total, "impact": impact,
            "amplifier": ({"applied": True, "factor": AMPLIFIER["factor"],
                           "amplified_urls": len(amp_urls),
                           "urls": amp_urls[:URL_QUERY_LIMIT]} if amp_urls else None),
            "conditional": cond,
            "fix_instruction": rule["fix"],
            "url_query": hits[:URL_QUERY_LIMIT]}
    return item


def compute(records, rules):
    """site_audit 逐页路径:一遍阈值/finding 初筛 → 条件依赖型后处理 → 放大器 → impact。"""
    total = len(records)
    by_id, degraded, notes, no_hit = {}, [], [], []
    ctx_fields = {}
    for sig_name in sorted(SIGNALS):
        ctx_fields[sig_name] = sum(1 for u, r in records.items()
                                   if SIGNALS[sig_name](r, u) is not None)
    gsc_ok = ctx_fields.get("gsc_clicks", 0) > 0
    pr_ok = ctx_fields.get("pagerank", 0) > 0 and ctx_fields.get("canonical_pagerank", 0) > 0
    for rule in rules:
        hits, covered = base_hits(rule, records)
        if rule["detect"] != "finding" and covered == 0:
            degraded.append({"rule": rule["id"],
                             "reason": "缺 %s 数据(输入 audit 无该页面级字段),规则未生效" % rule["detect"]})
            continue
        hits, sev, cond, note = apply_conditional(rule, hits, records)
        if note:
            notes.append(note)
        amp_urls = amplify(hits, records) if rule.get("amplifier", True) else []
        item = make_item(rule, hits, sev, cond, amp_urls, total)
        by_id[rule["id"]] = item
    fix_now = [d for d in by_id.values() if d["impact"] > 0 and d["category"] != "opportunity"]
    fix_now.sort(key=lambda d: (-d["impact"], d["rule"]))
    explore = [d for d in by_id.values()
               if d["category"] == "opportunity" and d["hit_urls"] > 0]
    explore.sort(key=lambda d: (-d["impact"], d["rule"]))
    no_hit = sorted(rid for rid, d in by_id.items()
                    if d["hit_urls"] == 0 and all(dd["rule"] != rid for dd in degraded))
    return {"fix_now": fix_now, "explore": explore, "no_hit_rules": no_hit,
            "degraded_rules": degraded, "degradation_notes": notes,
            "context": {"gsc": gsc_ok, "pagerank_compare": pr_ok,
                        "field_coverage": ctx_fields}}


def compute_from_health_score(data, rules):
    """health_score --json 摘要路径(优先识别):按 area 映射内置规则语义;无逐页字段,
    depth/inlinks/title_short 等页面级规则与放大器全部降级声明。"""
    impacts = data["impacts"]
    total = data.get("urls_total") or (impacts[0].get("total_urls", 0) if impacts else 0)
    builtin = {r["id"]: r for r in rules}
    fix_now, notes = [], []
    degraded_ids = set()
    for r in rules:
        if r["detect"] != "finding":
            degraded_ids.add(r["id"])
    if degraded_ids:
        notes.append("health_score 摘要输入无逐页字段(depth/inlinks/pagerank/GSC 等),"
                     "页面级条件规则与放大器不可判定——已降级,需 site_audit --json 重跑")
    for d in impacts:
        rid = d.get("rule", "")
        mapped = AREA_RULE.get(rid)
        src = builtin.get(mapped) if mapped else None
        sev = str(d.get("severity", "WARN")).upper()
        cond = None
        if rid in AREA_CONDITIONAL:
            # 摘要输入无 pagerank/意图数据:条件依赖型降为 WARN + 需人工,不直接 critical
            base = builtin[AREA_CONDITIONAL[rid]]
            sev = "WARN" if sev == "CRITICAL" else sev
            cond = {"question": base["conditional"], "needs_human": True,
                    "verdict_hint": "摘要输入缺逐页上下文,按 Botify 口径需人工判定"}
        item = {"rule": mapped or rid, "source_rule": rid,
                "category": (src or {}).get("category", d.get("category", "imported")),
                "severity": sev,
                "hit_urls": d.get("hit_urls", 0), "total_urls": total,
                "impact": round(d.get("hit_urls", 0) / total * SEV_WEIGHT.get(sev, 1.0), 4)
                          if total else 0.0,
                "amplifier": None,
                "conditional": cond,
                "fix_instruction": (src or {}).get(
                    "fix", "见 health_score.py 报告中 %s 的检查说明(摘要输入无逐页修复定位)" % rid),
                "url_query": []}
        if item["impact"] > 0 and item["category"] != "opportunity":
            fix_now.append(item)
    fix_now.sort(key=lambda d: (-d["impact"], d["rule"]))
    return {"fix_now": fix_now, "explore": [],
            "no_hit_rules": sorted({d.get("rule", "") for d in impacts
                                    if not d.get("hit_urls")}),
            "degraded_rules": [{"rule": rid,
                                "reason": "health_score 摘要输入无逐页字段,规则未生效"}
                               for rid in sorted(degraded_ids)],
            "degradation_notes": notes,
            "context": {"gsc": False, "pagerank_compare": False, "field_coverage": {}}}


# ---------------------------------------------------------------- 渲染
def render(rep):
    """人读 markdown:两栏(Ryte 口径)+ 条件提示 + 降级声明。"""
    seg = ("segment %r(命中 %d/%d URL,优先级已按 segment 重算)"
           % (rep["segment"], rep["urls_total"], rep["urls_matched_segment"])
           if rep["segment"] else "全站样本")
    L = ["# 优先级引擎(Botify ActionBoard 口径)",
         "",
         "- 输入: %s --json;%d URL 可评分(%d 拒审未计入);%s"
         % (rep["input_format"], rep["urls_total"], rep["urls_refused"], seg),
         "- 上下文: GSC 逐页流量 %s · PageRank 对比 %s"
         % ("✓" if rep["context"]["gsc"] else "✗", "✓" if rep["context"]["pagerank_compare"] else "✗"),
         "- impact = 命中占比 × 严重度(CRITICAL=3/WARN=2/INFO=1) × 放大器(内链>10 次 → ×1.5)",
         "- coverage: %s" % rep["coverage_note"],
         "",
         "## 立即处理(impact>0,降序)"]
    if not rep["fix_now"]:
        L.append("- (无命中规则)")
    for i, d in enumerate(rep["fix_now"], 1):
        L.append("%d. **%s** [%s] impact %s —— 命中 %d/%d(%s)"
                 % (i, d["rule"], d["severity"], d["impact"], d["hit_urls"],
                    d["total_urls"], d["category"]))
        L.append("   - 修复: %s" % d["fix_instruction"])
        if d.get("conditional"):
            c = d["conditional"]
            tag = "需人工判定" if c.get("needs_human") else "条件上下文"
            extra = ""
            if "urgency_split" in c:
                extra = ";" + ",".join("%s %d" % kv for kv in c["urgency_split"].items())
            if "verdicts" in c:
                extra = ";自动判定 %s" % c["verdicts"]
            L.append("   - 条件(%s): %s%s" % (tag, c.get("question", ""), extra))
            if c.get("verdict_hint"):
                L.append("     - 判定线索: %s" % c["verdict_hint"])
        if d.get("amplifier"):
            L.append("   - 放大器: %d URL 被内链>%d 次 → impact×%s【Botify 官方】"
                     % (d["amplifier"]["amplified_urls"], AMPLIFIER["gt"],
                        d["amplifier"]["factor"]))
        if d["url_query"]:
            shown = d["url_query"][:10]
            more = d["hit_urls"] - len(shown)
            L.append("   - URL(%d): %s%s"
                     % (d["hit_urls"], " ".join(shown),
                        (" …(+%d,--json 取前 %d)" % (more, URL_QUERY_LIMIT)) if more > 0 else ""))
    L += ["", "## 值得探索(Opportunity 类)"]
    if not rep["explore"]:
        L.append("- (无)")
    for d in rep["explore"]:
        L.append("- **%s** [%s] impact %s —— %s" % (d["rule"], d["severity"], d["impact"],
                                                     d["fix_instruction"]))
    if rep["no_hit_rules"]:
        L += ["", "未命中(本 segment 内 0 命中): %s" % ", ".join(rep["no_hit_rules"])]
    if rep["degraded_rules"]:
        L += ["", "## 降级声明(缺数据源的规则,未生效)"]
        L += ["- %s: %s" % (d["rule"], d["reason"]) for d in rep["degraded_rules"]]
    if rep["degradation_notes"]:
        L += ["", "## 降级标注"]
        L += ["- %s" % n for n in rep["degradation_notes"]]
    return "\n".join(L)


# ---------------------------------------------------------------- main
def main():
    argv = sys.argv[1:]
    if any(a in ("-h", "--help") for a in argv):
        print(USAGE)
        return
    audit_path, seg_re, rules_path, as_json = None, None, None, False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--audit" and i + 1 < len(argv):
            audit_path = argv[i + 1]; i += 2
        elif a == "--segment" and i + 1 < len(argv):
            try:
                seg_re = re.compile(argv[i + 1])
            except re.error as e:
                die("--segment 正则非法: %s" % e)
            i += 2
        elif a == "--rules-json" and i + 1 < len(argv):
            rules_path = argv[i + 1]; i += 2
        elif a == "--json":
            as_json = True; i += 1
        else:
            sys.stderr.write(USAGE + "\n")
            sys.exit(2)
    if not audit_path:
        sys.stderr.write("缺少 --audit\n" + USAGE + "\n")
        sys.exit(2)
    data = load_json_blob(audit_path)
    fmt = detect_format(data)
    rules = load_custom_rules(rules_path, RULES) if rules_path else [dict(r) for r in RULES]
    rep = {"schema_version": SCHEMA_VERSION, "input_format": fmt, "segment":
           (seg_re.pattern if seg_re else None), "coverage_note": COVERAGE_NOTE}
    if fmt == "health_score":
        rep["urls_refused"] = data.get("urls_refused", 0)
        rep["urls_matched_segment"] = data.get("urls_total", 0)
        rep["urls_total"] = data.get("urls_total", 0)
        rep.update(compute_from_health_score(data, rules))
    else:
        results = data["results"]
        scored = {u: r for u, r in results.items()
                  if r.get("verdict") != "refused"
                  and not any(f.get("severity") == "SKIP" for f in r.get("findings", []) or [])}
        refused = len(results) - len(scored)
        matched = scored
        if seg_re is not None:
            matched = {u: r for u, r in scored.items() if seg_re.search(u)}
            if not matched:
                die("--segment %r 匹配 0 URL(共 %d 可评分 URL)" % (seg_re.pattern, len(scored)))
        if not matched:
            die("无可评分 URL(全部拒审或空 results)")
        rep["urls_refused"] = refused
        rep["urls_matched_segment"] = len(matched)
        rep["urls_total"] = len(matched)
        rep.update(compute(matched, rules))
    if as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(render(rep))
    sys.exit(0)


if __name__ == "__main__":
    main()
