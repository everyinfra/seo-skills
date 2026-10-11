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
  --out        findings.json   状态文件(默认 findings.json,原子写):重跑时按 fingerprint
               (engine|prompt|response 序号|fact|ai_claim)保持人工状态
               status: pending → acknowledged/ignored(reopen 是瞬态动作,重跑归一为 pending)
  --json                       输出 JSON 而非 markdown 报告

门槛(Athena 官方):已验证 facts <25 条 → 警告"样本不足,结论置信低"。

核查逻辑(可判定部分):
  1. 每条 fact 抽关键词组(显式 keywords 优先,否则自动分语系 run:拉丁词去停词、汉字去停字
     整段+二元组、谚文/假名/西里尔/天城文/泰文 run 各自成 token;术语与句子先过归一链
     ——NFKC 全半角/土 İ/俄 ё/阿文正字/越声调,思路参考 keyword_variants.py 的 canon,自实现);
  2. 在每条 response 的每个句子中找相关表述(命中 ≥1 关键词才算相关);
     句切含全角！？(U+FF01/U+FF1F)与阿文 ؟(U+061F);
  3. 冲突检测(正则近似):
     - 数字冲突:同 kind(货币/百分比/带单位数值)且数值不同;货币按币种(ISO)分桶,
       数值与币种都相同才判一致($99 与 99元 不再判一致,判币种冲突);
     - 日期冲突:ISO 日期/年份不同;
     - 布尔冲突:同一关键词在事实与 AI 句中肯定/否定极性相反(分句内取反向窗口;
       无限/未来/不断 等含否定字的普通词不算否定);
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
import unicodedata
from collections import Counter
from datetime import datetime

SIX_RECORDS = ("company", "market", "offerings", "audience", "strategy", "execution")
ATHENA_FACT_FLOOR = 25          # Athena 官方门槛:≥25 条已验证 facts 才能扫
STATUSES = ("pending", "acknowledged", "ignored", "reopen")
SCHEMA_VERSION = 2              # v2:fingerprint 纳入 response 序号+ai_claim(同 prompt 多采样互不覆盖)

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


# ---------- 归一链(R5 多语言;思路参考 keyword_variants.py 的 canon,自实现) ----------
# 术语与句子匹配前统一归一:NFKC 全/半角与数字形(泰文/天城文/阿拉伯数字→ASCII)→
# 土耳其 İ 先替换再折叠(去残留 U+0307)→ casefold → 俄语 ё→е →
# 阿拉伯正字(أإٱ→ا、ى→ي、ة→ه、去 tatweel)→ 越南声调剥离。
_AR_ORTHO = {"أ": "ا", "إ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"}
_TATWEEL = "\u0640"
_VI_BASE = set("ăâđêôơư")


def _canon(text):
    """归一化比较形:关键词抽取、句子相关性匹配、极性判定与数值抽取共用。"""
    w = unicodedata.normalize("NFKC", (text or "").strip())
    w = w.replace("İ", "i").casefold()
    if "\u0307" in w:                                   # İ 折叠残留的组合点
        w = w.replace("\u0307", "")
    if "ё" in w:
        w = w.replace("ё", "е")
    if any(c in _AR_ORTHO for c in w) or _TATWEEL in w:
        w = w.replace(_TATWEEL, "")
        w = "".join(_AR_ORTHO.get(c, c) for c in w)
    if any(c in _VI_BASE for c in w):                   # 越南声调剥离(仅越文字母在场时)
        w = unicodedata.normalize("NFC", "".join(
            c for c in unicodedata.normalize("NFD", w) if not unicodedata.combining(c)))
    return w


# ---------- Unicode 分语系 run(R5:ko/ru/ar/th/hi 事实不再静默 0 findings) ----------
# 谚文/假名/西里尔/天城文/泰文 run 各自成 token;汉字 run 去停字后整段+二元组;拉丁词去停词。
_SCRIPT_RANGES = (
    ("latin", ((0x41, 0x5A), (0x61, 0x7A), (0xC0, 0xD6), (0xD8, 0xF6), (0xF8, 0x24F),
               (0x1E00, 0x1EFF))),                      # 基本 Latin+Latin-1(除 ×÷)+扩展+越南
    ("hangul", ((0xAC00, 0xD7A3), (0x1100, 0x11FF), (0x3130, 0x318F))),
    ("kana", ((0x3041, 0x30FF), (0x31F0, 0x31FF))),
    ("cjk", ((0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0xF900, 0xFAFF))),
    ("cyrillic", ((0x400, 0x52F),)),
    ("arabic", ((0x600, 0x6FF), (0x750, 0x77F))),
    ("devanagari", ((0x900, 0x97F),)),
    ("thai", ((0xE01, 0xE5B),)),
)
_MARK_CATS = ("Mn", "Mc", "Me")
_FAMILY_CACHE = {}


def _char_family(ch):
    fam = _FAMILY_CACHE.get(ch)
    if fam is None:
        fam = ""
        for name, ranges in _SCRIPT_RANGES:
            if any(lo <= ord(ch) <= hi for lo, hi in ranges):
                fam = name
                break
        _FAMILY_CACHE[ch] = fam
    return fam or None


def _script_runs(text):
    """连续同语系字符成 run:组合标记(变音/声调/元音符)并入当前 run;
    拉丁 run 允许数字/-/_ 连写(兼容旧 [A-Za-z][A-Za-z0-9_-]* 口径)。yield (语系, token)。"""
    fam, buf = None, []
    for ch in text:
        f = _char_family(ch)
        if f is None:
            if buf and unicodedata.category(ch) in _MARK_CATS:
                buf.append(ch)
            elif fam == "latin" and (ch in "-_" or "0" <= ch <= "9"):
                buf.append(ch)
            else:
                if buf:
                    yield fam, "".join(buf)
                fam, buf = None, []
        elif f == fam:
            buf.append(ch)
        else:
            if buf:
                yield fam, "".join(buf)
            fam, buf = f, [ch]
    if buf:
        yield fam, "".join(buf)


# ---------- 货币分币种(R5:$99 与 99元 不再判一致;unit=ISO 代码) ----------
_CUR_SYMBOLS = ("US$", "CA$", "HK$", "A$", "S$", "R$",       # 多字符符号在前
                "$", "€", "£", "¥", "₹", "₽", "₺", "฿", "₩", "₫", "₱", "₪", "₴", "₦")
CUR_SYMBOL_MAP = {"US$": "USD", "CA$": "CAD", "HK$": "HKD", "A$": "AUD", "S$": "SGD",
                  "R$": "BRL", "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY",
                  "₹": "INR", "₽": "RUB", "₺": "TRY", "฿": "THB", "₩": "KRW",
                  "₫": "VND", "₱": "PHP", "₪": "ILS", "₴": "UAH", "₦": "NGN"}
_CUR_WORDS = [  # 币种词(重前轻后,防前缀吞字):中文/俄文/天城文/泰文/谚文 + 拉丁词与 ISO 码
    ("人民币", "CNY"), ("美元", "USD"), ("美金", "USD"), ("欧元", "EUR"), ("英镑", "GBP"),
    ("日元", "JPY"), ("港元", "HKD"), ("港币", "HKD"), ("澳元", "AUD"), ("韩元", "KRW"),
    ("泰铢", "THB"), ("卢比", "INR"), ("卢布", "RUB"), ("里拉", "TRY"), ("雷亚尔", "BRL"),
    ("рублей", "RUB"), ("рубля", "RUB"), ("рубль", "RUB"), ("руб", "RUB"),
    ("долларов", "USD"), ("доллара", "USD"), ("доллар", "USD"),  # 俄语美元
    ("달러", "USD"), ("디름", "USD"),                              # 韩语美元/第纳尔近似
    ("دولارا", "USD"), ("دولار", "USD"), ("دولارات", "USD"),       # 阿语美元
    ("ดอลลาร์", "USD"), ("เงิน", "THB"),                        # 泰语美元/钱(泰铢语境)

    ("रुपया", "INR"), ("रुपये", "INR"), ("บาท", "THB"), ("원", "KRW"),
    ("円", "JPY"), ("圆", "CNY"), ("元", "CNY"),
    ("dollars", "USD"), ("dollar", "USD"), ("euros", "EUR"), ("euro", "EUR"),
    ("pounds", "GBP"), ("pound", "GBP"), ("yens", "JPY"), ("yen", "JPY"),
    ("rupees", "INR"), ("rupee", "INR"), ("yuan", "CNY"), ("won", "KRW"),
    ("rub", "RUB"), ("usd", "USD"), ("eur", "EUR"), ("gbp", "GBP"), ("jpy", "JPY"),
    ("cny", "CNY"), ("rmb", "CNY"), ("inr", "INR"), ("thb", "THB"), ("krw", "KRW"),
    ("brl", "BRL"), ("hkd", "HKD"), ("aud", "AUD"), ("rs", "INR"), ("tl", "TRY"),
]
CUR_WORD_MAP = dict(_CUR_WORDS)
_CUR_SYM_RE = "|".join(re.escape(s) for s in _CUR_SYMBOLS)
_CUR_WORD_RE = "|".join(w for w, _ in _CUR_WORDS)

_NUM = r"(?<![\d.])\d+(?:[.,]\d+)?(?!\d)"
VALUE_RE = re.compile(
    r"(?P<iso>(?<![\d.])(?:19|20)\d{2}[-/.]\d{1,2}(?:[-/.]\d{1,2})?(?!\d))"
    r"|(?P<csym>" + _CUR_SYM_RE + r")\s*(?P<cnum1>" + _NUM + r")"
    r"|(?P<cnum2>" + _NUM + r")\s*(?P<ccy>" + _CUR_WORD_RE + r")(?![a-z])"
    r"|(?P<pct>" + _NUM + r")\s*%"
    r"|百分之\s*(?P<pct2>\d+(?:\.\d+)?)"
    r"|(?P<yr>(?<![\d.])(?:19|20)\d{2}(?!\d))(?:\s*(?:年|year|years))?"
    r"|(?P<cnum3>" + _NUM + r")\s*(?P<csym2>" + _CUR_SYM_RE + r")"
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
# R5:无限/未来/不断 等含否定字的普通词不算否定(回看窗口子串误判的根源)
NEG_BACK_ZH = re.compile(r"无法|尚未|没有|未(?!来)|无(?!限)|不(?!断)")
FWD_NEG_EN = re.compile(r"\b(?:not|never)\s+(?:support|offer|offered|included?|provided?"
                        r"|available|compatible|free|open)\w*", re.I)
FWD_NEG_ZH = re.compile(r"(?:不|未|无法|没有)\s*(?:支持|提供|包含|兼容|可用|开放|免费)")
ASSERT_RE = re.compile(r"支持|提供|包含|包括|拥有|开源|免费|可用|允许|兼容|集成|开放|宣称"
                       r"|\b(?:support|offer|include|provide|available|open[-\s]?source"
                       r"|free|allow|integrate)\w*\b", re.I)
CLAUSE_SPLIT = re.compile(r"[,;;]|但是|但|\b(?:however|yet|while)\b")
# R5:补全角！(U+FF01)/？(U+FF1F)与阿文 ؟(U+061F)——CJK/韩文/阿文问叹句不再粘连成一句
SENT_SPLIT = re.compile(r"[。!?\uFF01\uFF1F\u061F\n;；]+|(?<![\d.])\.(?!\d)")

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
    """fact 的关键词组:显式 keywords 优先(经归一链);否则自动分语系抽取——
    拉丁词(去停词)、汉字 run 去停字后整段+二元组、
    谚文/假名/西里尔/天城文/泰文 run 各自成 token(≥2 码点,单字符是虚词噪音)。"""
    if explicit:
        return sorted({t for t in (_canon(k) for k in explicit if k and str(k).strip()) if t})
    terms = set()
    for fam, tok in _script_runs(_canon(text)):
        if fam == "latin":
            if len(tok) >= 2 and tok not in STOP_EN:
                terms.add(tok)
        elif fam == "cjk":
            s = "".join(ch for ch in tok if ch not in STOP_CJK_CHARS)
            if not s:
                continue
            terms.add(s)
            for i in range(len(s) - 1):
                terms.add(s[i:i + 2])
        elif len(tok) >= 2:                       # 谚文/假名/西里尔/天城文/泰文
            terms.add(tok)
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
    """抽取显式数值/日期:iso/currency(带币种)/percent/year/generic(数字+单位)。
    输入先过归一链(全角/泰文/天城文/阿拉伯数字→ASCII);裸数字不抽(噪音)。"""
    out = []
    for m in VALUE_RE.finditer(_canon(text)):
        if m.group("iso"):
            parts = re.split(r"[-/.]", m.group("iso"))
            out.append({"kind": "iso", "value": tuple(int(p) for p in parts),
                        "unit": "date", "raw": m.group("iso")})
        elif m.group("csym"):
            out.append({"kind": "currency", "value": _tofloat(m.group("cnum1")),
                        "unit": CUR_SYMBOL_MAP.get(m.group("csym"), "cur"),
                        "raw": m.group(0)})
        elif m.group("cnum2"):
            out.append({"kind": "currency", "value": _tofloat(m.group("cnum2")),
                        "unit": CUR_WORD_MAP.get(m.group("ccy"), "cur"),
                        "raw": m.group(0)})
        elif m.group("pct"):
            out.append({"kind": "percent", "value": _tofloat(m.group("pct")),
                        "unit": "pct", "raw": m.group(0)})
        elif m.group("pct2"):
            out.append({"kind": "percent", "value": _tofloat(m.group("pct2")),
                        "unit": "pct", "raw": m.group(0)})
        elif m.group("yr"):
            out.append({"kind": "year", "value": int(m.group("yr")),
                        "unit": "yr", "raw": m.group("yr")})
        elif m.group("cnum3"):
            out.append({"kind": "currency", "value": _tofloat(m.group("cnum3")),
                        "unit": CUR_SYMBOL_MAP.get(m.group("csym2"), "cur"),
                        "raw": m.group(0)})
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
    """同 (kind, unit) 桶内,句值与任一事实值相等→视为一致;否则首个不匹配者报冲突。
    货币跨币种可比:数值与币种(ISO)都相同才判一致——$99 与 99元 不再判一致,判冲突。"""
    for sv in sent_vals:
        if sv["kind"] == "currency":
            bucket = [fv for fv in fact_vals if fv["kind"] == "currency"]
        else:
            key = (sv["kind"], sv["unit"])
            bucket = [fv for fv in fact_vals if (fv["kind"], fv["unit"]) == key]
        if not bucket:
            continue
        if sv["kind"] == "iso":
            if any(_iso_shared_equal(fv, sv) for fv in bucket):
                continue
        elif any(fv["value"] == sv["value"]
                 and (sv["kind"] != "currency" or fv["unit"] == sv["unit"])
                 for fv in bucket):
            continue
        if sv["kind"] == "currency":              # 优先报同数值异币种(更具体)
            fv = next((f for f in bucket if f["value"] == sv["value"]), bucket[0])
        else:
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
    for cl in CLAUSE_SPLIT.split(_canon(text)):
        for m in re.finditer(re.escape(term), cl, re.I):
            pols.append("neg" if _occurrence_negated(cl, m.start(), m.end()) else "pos")
    if not pols:
        return None
    return "neg" if all(p == "neg" for p in pols) else "pos"


def _anchored_negation(text, term):
    """term 的某次出现其**前向**窗口内紧邻否定词(报告布尔冲突时优先这类术语,更具体)。"""
    for cl in CLAUSE_SPLIT.split(_canon(text)):
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
