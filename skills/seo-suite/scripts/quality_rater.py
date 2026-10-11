#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quality_rater.py — 内容质量六维评分 (读纯文本, 仅标准库).

用法:
  python3 quality_rater.py draft.txt
  python3 quality_rater.py draft.txt --market zh --keyword "项目管理软件"
  cat draft.md | python3 quality_rater.py - --market en
  python3 quality_rater.py draft.txt --evidence-source src.txt   (追加证据纪律节)

约定 (纯文本近似):
  * 首个非空行 = title, 同时也当作 H1
  * H2 计数: markdown ##/### 行 + (zh 市场) 2-30 字、无句末标点的短行
  * 词数为 CJK 感知: 每个汉字计 1 词, 其余按空白分词

六维 (加权总分 100):
  content     0.20 : 词数 <2000 扣 30 / <2500 扣 10 / >3000 扣 5
  keywords    0.25 : H1(首行)缺主词扣 20; 前 100 词缺主词扣 15; 密度>3.5% 判 stuffing 扣 20
                     (主词: --keyword 指定, 否则按词频自动推断)
  meta        0.15 : title(首行)长度落在 50-60 满分, 每偏差 1 字符扣 3
  structure   0.15 : H2 >= 4; 每缺 1 个扣 15; 零列表再扣 5
  links       0.15 : 链接样文本(markdown 链接 / http(s):// / www.) >= 3 满分, 按比例
  readability 0.10 : 平均句长 <= 25 词满分, 每超 1 词扣 4; >20% 句子超 37.5 词再扣 10

publishing_ready = 总分 >= 80 且 0 个 critical.
critical: 主词未在正文出现 / 密度>5% 硬 stuffing / title 长度 <25 或 >90 /
          H2 为 0 / 词数 <800 (薄内容).

证据纪律节 (niubigeo 深读 §3 N8/N9, references/research/niubigeo-deep-read.md;
标注层——不改六维分数/critical/publishing_ready/退出码, 恒输出在评分之后):
  * N8 D/K 分报【仓库,docs/measurement-methodology.md】: D(点名域名)≠K(中性词不点名),
    指标永不混算,"复述已点名的域名不能叫自然发现率";分母=0 → null 永不报 0%;
    pointState=complete/partial/no_data。内容侧映射[推断]:
    D=点名声明级证据(引语/链接——显式归属出处), K=中性观察级(裸数字——无出处断言);
    两类各留分母分报, 引语内数字归 D 不重复计 K。
  * N9 UTF-16 证据核验【仓库,docs/evidence-model.md】: 证据偏移 = UTF-16 code unit
    (非 UTF-8 字节;Python str 按 code point, CJK BMP 内等同, 增补平面按 2 单元);
    核验条件 raw.slice(start,end)===quote; 定位失败 → evidence=null 不虚构偏移;
    同文多次出现取首次精确匹配; recordHash=sha256(JSON.stringify(value))
    无缩进无末尾换行。--evidence-source 给源文时逐元素定位核验(引语/数字/链接)。
  * 编码级假证据扫描[推断,N9 同形字/代理字符防护]: 证据元素内检出
    孤立代理字符(U+D800-DFFF, UTF-16 偏移不可信)/西里尔·希腊同形拉丁字母/
    全角数字·字母(与 ASCII 同形, 精确匹配必败)→ 风险标注。

退出码: publishing_ready -> 0; 否则 1; 文件读不到 -> 2.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys

# ②多语言断层修复(R5): CJK_RE 对齐 content_score.py 口径扩假名+谚文——纯谚文/假名
# 正文词数不再恒 0(cjk_words 逐字计);LATIN_WORD_RE 同扩假名 run(平/片假名各成 run,
# 片假名内容词不与平假名助词粘连;cjk_words 里 CJK_RE 先替走假名不会双计;
# auto_keyword 非 zh 分支与 first_100_words 由它接管假名 run)。
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
KANA_RUN_RE = re.compile(r"[\u3041-\u309f]+|[\u30a0-\u30ff]+")   # 平假名/片假名 run(含 ー)
LATIN_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*|[\u3041-\u309f]+|[\u30a0-\u30ff]+")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?。！？;；])\s+|\n+")
MD_H2_RE = re.compile(r"^#{2,6}\s+\S")
LIST_RE = re.compile(r"^\s*(?:[-*\u2022\u00b7]|\d+[.)、\uFF09])\s+\S")
LINK_LIKE_RE = re.compile(r"\[[^\]]+\]\([^)\s]+\)|https?://\S+|www\.\S+", re.I)
TITLE_END_PUNCT = tuple(".。!!??;；:：,，")

STOPWORDS = {
    "the", "a", "an", "of", "to", "for", "and", "or", "in", "on", "with", "your",
    "you", "how", "what", "why", "best", "guide", "ultimate", "complete", "is",
    "are", "be", "it", "this", "that", "by", "from", "at", "as",
    "的", "与", "和", "及", "或", "在", "是", "如何", "最", "完全", "指南", "大全",
    "一个", "我们", "你", "您的", "什么", "为什么", "哪些",
}


def read_text(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def cjk_words(text):
    """CJK 感知词数: 汉字/假名/谚文逐字计 1(②与 CJK_RE 同口径), 其余按空白/字母数字分词."""
    cjk = len(CJK_RE.findall(text))
    latin = len(LATIN_WORD_RE.findall(CJK_RE.sub(" ", text)))
    return cjk + latin


def first_100_words_text(text):
    """截取约前 100 词的原文窗口 (保持 CJK 字符连续).
    ②假名 run 整段进窗口(1 run=1 token,假名不再被整段丢弃);谚文/汉字仍逐字计。"""
    words = []
    size = 0
    # 把文本切成 汉字/谚文/假名run(平/片各成run)/拉丁词/其他 token, 保留原文顺序
    for tok in re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]"
                          r"|[\u3041-\u309f]+|[\u30a0-\u30ff]+"
                          r"|[A-Za-z0-9][A-Za-z0-9'\-]*|\s+", text):
        if tok.strip() == "" and not CJK_RE.match(tok):
            if words:
                words.append(tok)
            continue
        words.append(tok)
        size += 1
        if size >= 100:
            break
    return "".join(words)


def keyword_occurrences(kw, text):
    """主词出现次数: CJK 用子串计数, 拉丁用词边界计数 (大小写不敏感)."""
    if not kw:
        return 0
    if CJK_RE.search(kw):
        return text.count(kw)
    return len(re.findall(r"\b" + re.escape(kw) + r"\b", text, re.I))


def auto_keyword(text, market):
    """按词频自动推断主词: zh 取高频二字组, en 取高频词组; 跳过停用词."""
    body = text
    if market == "zh":
        seg = re.findall(r"[\u4e00-\u9fff]{2,}", body)
        gram_counter = {}
        for chunk in seg:
            for i in range(len(chunk) - 1):
                g = chunk[i:i + 2]
                if g[0] in STOPWORDS or g[1] in STOPWORDS:
                    continue
                gram_counter[g] = gram_counter.get(g, 0) + 1
        if gram_counter:
            best = max(gram_counter.items(), key=lambda kv: kv[1])
            if best[1] >= 3:
                return best[0]
        return seg[0] if seg else ""
    words = [w.lower() for w in LATIN_WORD_RE.findall(body) if w.lower() not in STOPWORDS and len(w) > 2]
    if not words:
        return ""
    bigrams = {}
    for i in range(len(words) - 1):
        g = words[i] + " " + words[i + 1]
        bigrams[g] = bigrams.get(g, 0) + 1
    uni = {}
    for w in words:
        uni[w] = uni.get(w, 0) + 1
    best_bi = max(bigrams.items(), key=lambda kv: kv[1]) if bigrams else ("", 0)
    best_uni = max(uni.items(), key=lambda kv: kv[1])
    if best_bi[1] >= 3:
        return best_bi[0]
    return best_uni[0]


def heading_like(line, market):
    s = line.strip()
    if not s or len(s) > 40:
        return False
    if MD_H2_RE.match(s):
        return True
    if LIST_RE.match(s):
        return False
    if s.endswith(TITLE_END_PUNCT):
        return False
    if market == "zh":
        return bool(CJK_RE.search(s)) and len(s) <= 30
    # en: 短行且无句末标点, 且不像整段正文 (首词大写近似)
    return bool(re.match(r"^[A-Z]", s)) and len(s.split()) <= 8


# ---------------------------------------------------------------- 证据纪律节
# (niubigeo 深读 §3 N8 D/K 分报 + N9 UTF-16 偏移核验;标注层——不改六维分数/
#  critical/publishing_ready/退出码。出处逐条标注 references/research/
#  niubigeo-deep-read.md,只借规格不搬代码。)
EVID_NUMBER_RE = re.compile(r"[0-9]+(?:[,.][0-9]+)*[%％]?|[０-９]+")
EVID_QUOTE_RE = re.compile(r"「[^」]{2,}」|『[^』]{2,}』|“[^”]{2,}”|\"[^\"]{4,}\"")

# 编码级假证据字符[推断,N9 同形字/代理字符防护]: 西里尔/希腊同形拉丁字母
# (键=原字符 \u 转义, 值=同形 ASCII);全角数字 U+FF10-19、全角字母 U+FF21-3A/FF41-5A。
CYRILLIC_HOMOGLYPHS = {
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c",
    "\u0443": "y", "\u0445": "x", "\u0456": "i", "\u0455": "s", "\u0458": "j",
    "\u04bb": "h", "\u051b": "q", "\u051d": "w",
    "\u0410": "A", "\u0412": "B", "\u0415": "E", "\u041a": "K", "\u041c": "M",
    "\u041d": "H", "\u041e": "O", "\u0420": "P", "\u0421": "C", "\u0422": "T",
    "\u0423": "Y", "\u0425": "X",
}
GREEK_HOMOGLYPHS = {
    "\u03bf": "o", "\u03b1": "a", "\u03b5": "e", "\u03b9": "i", "\u03bd": "v",
    "\u03c1": "p", "\u03c5": "u", "\u03ba": "k",
    "\u0391": "A", "\u0392": "B", "\u0395": "E", "\u0396": "Z", "\u0397": "H",
    "\u039a": "K", "\u039c": "M", "\u039d": "N", "\u039f": "O", "\u03a1": "P",
    "\u03a4": "T", "\u03a5": "Y", "\u03a7": "X",
}
FULLWIDTH_DIGITS = {chr(0xFF10 + i): str(i) for i in range(10)}
FULLWIDTH_LETTERS = {}
for _i in range(26):
    FULLWIDTH_LETTERS[chr(0xFF21 + _i)] = chr(65 + _i)     # Ａ-Ｚ
    FULLWIDTH_LETTERS[chr(0xFF41 + _i)] = chr(97 + _i)     # ａ-ｚ
CONFUSABLE_SCRIPT = dict(CYRILLIC_HOMOGLYPHS)
CONFUSABLE_SCRIPT.update(GREEK_HOMOGLYPHS)
RISK_LABEL = {"lone_surrogate": "孤立代理字符(UTF-16 偏移不可信)",
              "confusable_script": "西里尔/希腊同形拉丁",
              "fullwidth_digit": "全角数字(同形 ASCII 数字)",
              "fullwidth_letter": "全角字母(同形 ASCII 字母)"}


def utf16_unit_len(s):
    """UTF-16 code unit 数【仓库,N9】: BMP 字符 1 单元, 增补平面(emoji 等)2 单元;
    孤立代理字符 1 单元(surrogatepass——JS 同口径)。"""
    return len(s.encode("utf-16-le", "surrogatepass")) // 2


def utf16_slice(text, start, end):
    """按 UTF-16 code unit 切片(N9: rawAnswer.slice(start,end) 同口径, 非字节偏移)。
    越界/负值 → None(不虚构偏移);切在代理对中间会得到孤立代理字符,
    与任何正常引语的 === 比较必败——由 verify_evidence_location 判 null。"""
    try:
        b = text.encode("utf-16-le", "surrogatepass")
    except UnicodeEncodeError:
        return None
    if start < 0 or end < start or 2 * end > len(b):
        return None
    try:
        return b[2 * start:2 * end].decode("utf-16-le", "surrogatepass")
    except UnicodeDecodeError:
        return None


def verify_evidence_location(raw_text, start, end, quote):
    """N9 核验条件: utf16_slice(raw_text, start, end) == quote → 返回 quote;
    失败 → None(evidence=null, 不虚构偏移)。"""
    got = utf16_slice(raw_text, start, end)
    if got is not None and got == quote:
        return quote
    return None


def locate_first_evidence(raw_text, quote):
    """同文多次出现取首次精确匹配(N9);返回 (start, end) UTF-16 偏移或 None。
    code point 首中与 code unit 首中同位(编码序一致), 再换算单元偏移。"""
    if not quote:
        return None
    idx = raw_text.find(quote)
    if idx < 0:
        return None
    start = utf16_unit_len(raw_text[:idx])
    return (start, start + utf16_unit_len(quote))


def record_hash(value):
    """N9 recordHash=sha256(JSON.stringify(value)): 无缩进、无分隔空格、无末尾换行。
    Python 口径[推断]: json.dumps(ensure_ascii=False, separators=(",",":"))
    ——JSON.stringify 不转义非 ASCII, 键序=插入序(Python 3.7+ dict 保序)。"""
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8", "surrogatepass")).hexdigest()


def scan_evidence_risks(elem_text):
    """编码级假证据扫描[推断,N9 防护]: 证据元素内逐字符检出——孤立代理字符
    (U+D800-DFFF, 不可编码 UTF-8, UTF-16 偏移不可信)/西里尔·希腊同形拉丁字母/
    全角数字·字母(与 ASCII 同形, 对干净源文的精确匹配必败)。
    返回 [{code, char, resembles}] 去重保序。"""
    seen, out = set(), []
    for ch in elem_text:
        cp = ord(ch)
        if 0xD800 <= cp <= 0xDFFF:
            code, resembles = "lone_surrogate", "U+%04X" % cp
        elif ch in CONFUSABLE_SCRIPT:
            code, resembles = "confusable_script", CONFUSABLE_SCRIPT[ch]
        elif ch in FULLWIDTH_DIGITS:
            code, resembles = "fullwidth_digit", FULLWIDTH_DIGITS[ch]
        elif ch in FULLWIDTH_LETTERS:
            code, resembles = "fullwidth_letter", FULLWIDTH_LETTERS[ch]
        else:
            continue
        key = (code, ch)
        if key not in seen:
            seen.add(key)
            out.append({"code": code, "char": ch, "resembles": resembles})
    return out


def extract_evidence_elements(text):
    """抽取证据元素并按 N8 D/K 分级[推断:内容侧映射——引语/链接=点名声明级 D
    (显式归属出处), 不在引语/链接内的裸数字=中性观察级 K(无出处断言);
    "复述已点名的域名不能叫自然发现率"→引语内数字归 D, 不重复计 K]。
    偏移按 UTF-16 code unit 记(N9 口径)。"""
    links = [(m.start(), m.end(), m.group(0), "link") for m in LINK_LIKE_RE.finditer(text)]
    quotes = [(m.start(), m.end(), m.group(0), "quote") for m in EVID_QUOTE_RE.finditer(text)
              if not any(s <= m.start() < e for s, e, _t, _k in links)]
    nums = [(m.start(), m.end(), m.group(0), "number") for m in EVID_NUMBER_RE.finditer(text)
            if not any(s <= m.start() < e for s, e, _t, _k in links + quotes)]
    elems = []
    for s, e, t, kind in links + quotes + nums:
        elems.append({"kind": kind, "dk": "D" if kind in ("link", "quote") else "K",
                      "text": t,
                      "utf16_start": utf16_unit_len(text[:s]),
                      "utf16_end": utf16_unit_len(text[:s]) + utf16_unit_len(t)})
    return elems


def build_evidence_discipline(text, source_text=None):
    """组装证据纪律节(N8 D/K 分报 + N9 UTF-16 核验 + 编码级假证据扫描)。
    返回 dict(纯标注数据): dk 两类各留分母(分母=0 → 计数 null 语义, 永不报 0%)、
    point_state 三态(N8)、char_risks 逐元素风险、verification(source_text 给定时
    逐元素首次精确匹配定位 + utf16 偏移核验 + record_hash, 定位失败 evidence=null
    不虚构偏移;核验失败≠证据不存在)。"""
    elems = extract_evidence_elements(text)
    dk = {}
    for cls in ("D", "K"):
        subset = [el for el in elems if el["dk"] == cls]
        dk[cls] = {"n": len(subset),
                   "flagged": sum(1 for el in subset if scan_evidence_risks(el["text"]))}
    if not elems:
        point_state = "no_data"
    elif dk["D"]["n"] and dk["K"]["n"]:
        point_state = "complete"
    else:
        point_state = "partial"
    char_risks = []
    for el in elems:
        for r in scan_evidence_risks(el["text"]):
            char_risks.append({"kind": el["kind"], "dk": el["dk"],
                               "text": el["text"][:40], **r})
    verification = None
    if source_text is not None:
        verified, unverified = [], []
        for el in elems:
            loc = locate_first_evidence(source_text, el["text"])
            if loc is None or verify_evidence_location(
                    source_text, loc[0], loc[1], el["text"]) is None:
                unverified.append({"kind": el["kind"], "dk": el["dk"],
                                   "text": el["text"][:40], "reason": "not_located"})
                continue
            verified.append({"kind": el["kind"], "dk": el["dk"], "text": el["text"][:40],
                             "start": loc[0], "end": loc[1],
                             "record_hash": record_hash(
                                 {"text": el["text"], "start": loc[0], "end": loc[1]})})
        verification = {"n": len(elems), "verified": len(verified),
                        "records": verified, "unverified": unverified}
    return {"dk": dk, "point_state": point_state, "char_risks": char_risks,
            "verification": verification,
            "note": "标注层: 不改六维分数/critical/publishing_ready/退出码;"
                    "核验失败≠证据不存在(evidence=null 只是无法定位)"}


def _safe_text(s):
    """孤立代理字符转 \\uXXXX 转义后返回(repr 不转义 Cs 类, 直接 print 会炸
    stdout 的 UTF-8 编码)——展示层专用, 不改数据本身。"""
    return "".join(ch if not (0xD800 <= ord(ch) <= 0xDFFF) else "\\u%04x" % ord(ch)
                   for ch in s)


def print_evidence_section(ev, source_name=None):
    """渲染证据纪律节(追加在评分之后;N8 分报措辞 + N9 null 纪律)。"""
    print()
    print("=" * 80)
    print("证据纪律节 (niubigeo N8 D/K 分报 + N9 UTF-16 核验; 标注层——"
          "不改上面任何分数/critical/退出码)")
    for cls, desc in (("D", "D(点名声明: 引语/链接)"), ("K", "K(中性观察: 裸数字)")):
        d = ev["dk"][cls]
        if d["n"] == 0:
            print("{0}: n=0 → null(不能计算, 永不报 0%)".format(desc))
        else:
            print("{0}: n={1}, 同形字/代理字符风险 {2}".format(desc, d["n"], d["flagged"]))
    print("pointState: {0} (complete=D、K 皆有元素 / partial=仅一类 / no_data=无证据元素)"
          .format(ev["point_state"]))
    if ev["char_risks"]:
        print("编码级假证据风险 (同形字/代理字符——对干净源文的 UTF-16 精确匹配必败):")
        for r in ev["char_risks"][:8]:
            print("  !! [{0}/{1}] {2!r} 中 {3!r} → {4} (同形 {5})".format(
                r["kind"], r["dk"], _safe_text(r["text"][:40]), _safe_text(r["char"]),
                RISK_LABEL[r["code"]], r["resembles"]))
        if len(ev["char_risks"]) > 8:
            print("  ... 共 {0} 处".format(len(ev["char_risks"])))
    v = ev["verification"]
    if v is None:
        print("UTF-16 定位核验: 未提供 --evidence-source → 跳过定位核验"
              "(no_data; 同形字/代理字符扫描照常执行)")
    else:
        src = source_name or "-"
        print("UTF-16 定位核验 (源文: {0}): 定位精确 {1}/{2}"
              "(偏移=UTF-16 code unit;同文多次出现取首次精确匹配)".format(src, v["verified"], v["n"]))
        for rec in v["records"][:5]:
            print("  [ok] [{0}/{1}] {2!r} @utf16[{3},{4}) record_hash={5}..".format(
                rec["kind"], rec["dk"], _safe_text(rec["text"][:30]), rec["start"],
                rec["end"], rec["record_hash"][:12]))
        if v["unverified"]:
            print("  ! 未定位 {0} 条 → evidence=null(不虚构偏移;核验失败≠证据不存在):".format(
                len(v["unverified"])))
            for u in v["unverified"][:8]:
                print("    - [{0}/{1}] {2!r}".format(u["kind"], u["dk"],
                                                     _safe_text(u["text"][:40])))


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="quality_rater.py",
        description="内容质量六维评分 (纯文本, CJK 感知, stdlib only)")
    ap.add_argument("file", help="纯文本/markdown 文件路径, '-' 表示 stdin")
    ap.add_argument("--market", choices=("zh", "en"), default="zh",
                    help="市场: zh 汉字感知分词与标题启发 (默认 zh)")
    ap.add_argument("--keyword", default=None,
                    help="主词; 不给则按词频自动推断")
    ap.add_argument("--evidence-source", default=None, dest="evidence_source",
                    help="证据源文路径(N9 UTF-16 定位核验用;给定时证据纪律节对引语/"
                         "数字/链接逐元素在源文做首次精确匹配定位+偏移核验+record_hash, "
                         "定位失败 evidence=null 不虚构偏移;不可读则警告并跳过)")
    args = ap.parse_args(argv)

    try:
        text = read_text(args.file)
    except OSError as e:
        print("[FATAL] 无法读取 {0}: {1}".format(args.file, e), file=sys.stderr)
        return 2
    if not text.strip():
        print("[FATAL] 输入为空", file=sys.stderr)
        return 2

    lines = text.splitlines()
    nonempty = [l for l in lines if l.strip()]
    title = nonempty[0].strip() if nonempty else ""
    body = "\n".join(nonempty[1:]) if len(nonempty) > 1 else title

    total_words = cjk_words(text)
    body_words = cjk_words(body)
    kw = (args.keyword or "").strip() or auto_keyword(body, args.market)

    critical = []

    # ---- content 0.20 ----
    if total_words < 2000:
        c_score, c_note = 70, "词数 {0} < 2000, 扣 30".format(total_words)
    elif total_words < 2500:
        c_score, c_note = 90, "词数 {0} < 2500, 扣 10".format(total_words)
    elif total_words > 3000:
        c_score, c_note = 95, "词数 {0} > 3000, 扣 5 (略超长)".format(total_words)
    else:
        c_score, c_note = 100, "词数 {0} 在 2500-3000 区间".format(total_words)
    if total_words < 800:
        critical.append("薄内容: 词数 {0} < 800".format(total_words))

    # ---- keywords 0.25 ----
    k_score = 100
    k_notes = []
    if not kw:
        k_score = 0
        k_notes.append("无法确定主词 (--keyword 指定)")
        critical.append("主词未知")
    else:
        occ = keyword_occurrences(kw, text)
        density = (occ / total_words * 100.0) if total_words else 0.0
        in_h1 = kw.lower() in title.lower()
        in_head = kw.lower() in first_100_words_text(text).lower()
        if not in_h1:
            k_score -= 20
            k_notes.append("H1(首行)缺主词, 扣 20")
        if not in_head:
            k_score -= 15
            k_notes.append("前 100 词缺主词, 扣 15")
        if density > 3.5:
            k_score -= 20
            k_notes.append("密度 {0:.1f}% > 3.5%, 判 stuffing, 扣 20".format(density))
            if density > 5:
                critical.append("硬 stuffing: 密度 {0:.1f}% > 5%".format(density))
        if occ == 0:
            critical.append("主词 '{0}' 未在正文出现".format(kw))
        k_notes.insert(0, "主词 \"{0}\": 出现 {1} 次, 密度 {2:.2f}%".format(kw, occ, density))
    k_score = max(0, k_score)

    # ---- meta 0.15 ----
    tlen = len(title)
    if 50 <= tlen <= 60:
        m_score, m_note = 100, "title 长度 {0} (50-60)".format(tlen)
    else:
        dist = (tlen - 60) if tlen > 60 else (50 - tlen)
        m_score = max(0, 100 - 3 * dist)
        m_note = "title 长度 {0} 距 50-60 区间 {1} 字符, 每字符扣 3".format(tlen, dist)
        if tlen < 25 or tlen > 90:
            critical.append("title 长度 {0} 越界 (<25 或 >90)".format(tlen))

    # ---- structure 0.15 ----
    h2_count = sum(1 for l in nonempty[1:] if heading_like(l, args.market))
    has_list = any(LIST_RE.match(l) for l in nonempty)
    s_score = 100
    s_notes = ["H2 级标题 {0} 个 (要求 >=4)".format(h2_count)]
    if h2_count < 4:
        s_score -= 15 * (4 - h2_count)
    if not has_list:
        s_score -= 5
        s_notes.append("零列表, 扣 5")
    s_score = max(0, s_score)
    if h2_count == 0:
        critical.append("结构缺失: 无任何 H2 级标题")

    # ---- links 0.15 ----
    link_count = len(LINK_LIKE_RE.findall(text))
    l_score = min(100, int(round(link_count / 3.0 * 100)))
    l_note = "链接样文本 {0} 处 (>=3 满分)".format(link_count)

    # ---- readability 0.10 ----
    sentences = [s.strip() for s in SENT_SPLIT_RE.split(text) if s.strip()]
    r_notes = []
    if sentences:
        mean_len = sum(cjk_words(s) for s in sentences) / len(sentences)
        r_score = 100
        if mean_len > 25:
            r_score = max(0, 100 - int(round((mean_len - 25) * 4)))
            r_notes.append("平均句长 {0:.1f} 词 > 25, 每词扣 4".format(mean_len))
        long_ratio = sum(1 for s in sentences if cjk_words(s) > 37.5) / len(sentences)
        if long_ratio > 0.20:
            r_score = max(0, r_score - 10)
            r_notes.append("{0:.0%} 句子超 37.5 词 (>20%), 再扣 10".format(long_ratio))
        r_notes.insert(0, "句子 {0}, 平均句长 {1:.1f} 词 (<=25 满)".format(len(sentences), mean_len))
    else:
        r_score, r_notes = 0, ["无法切分句子"]

    dims = [
        ("content", 0.20, c_score, c_note),
        ("keywords", 0.25, k_score, "; ".join(k_notes)),
        ("meta", 0.15, m_score, m_note),
        ("structure", 0.15, s_score, "; ".join(s_notes)),
        ("links", 0.15, l_score, l_note),
        ("readability", 0.10, r_score, "; ".join(r_notes)),
    ]
    total = sum(w * s for _n, w, s, _d in dims)
    ready = total >= 80 and not critical

    print("=" * 80)
    print("quality_rater | {0} (market={1})".format(args.file, args.market))
    print("title(首行): \"{0}\"".format(title[:70]))
    print("词数(CJK 感知): {0} | 句子: {1}".format(total_words, len(sentences) if sentences else 0))
    print("-" * 80)
    print("{0:<13} {1:>6} {2:>7} {3:>7}  说明".format("维度", "权重", "得分", "加权"))
    for name, w, s, d in dims:
        print("{0:<13} {1:>6.2f} {2:>7.0f} {3:>7.2f}  {4}".format(name, w, s, w * s, d))
    print("-" * 80)
    print("加权总分: {0:.1f} / 100".format(total))
    if critical:
        print("critical ({0}):".format(len(critical)))
        for c in critical:
            print("  !! {0}".format(c))
    else:
        print("critical: 无")
    print("publishing_ready: {0} (条件: 总分>=80 且 0 critical)".format("YES" if ready else "NO"))

    # ---- 证据纪律节 (niubigeo N8/N9; 标注层——不改上面任何分数/critical/退出码) ----
    src_text, src_name = None, None
    if args.evidence_source:
        if args.evidence_source == "-":
            print("[WARN] --evidence-source 不支持 '-'(stdin 已被正文占用) → 跳过定位核验",
                  file=sys.stderr)
        else:
            try:
                src_text = read_text(args.evidence_source)
                src_name = args.evidence_source
            except OSError as e:
                print("[WARN] --evidence-source 不可读: {0} → 跳过定位核验".format(e),
                      file=sys.stderr)
    ev = build_evidence_discipline(text, src_text)
    print_evidence_section(ev, src_name)
    return 0 if ready else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        sys.exit(130)
