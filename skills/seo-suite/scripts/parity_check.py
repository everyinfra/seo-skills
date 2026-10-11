#!/usr/bin/env python3
"""双语对照页 QA(pipeline-completeness R2-7,stdlib only)。
发布前把"源语言页 ↔ 目标语言页"并排对照,替人工逐项核对:
  长度平价带   目标/源可见文本长度比落在市场膨胀带内——markets.json 语言相关字段的
               膨胀率口径(de「德语版比英语长 25-35%」/ja「日语版比英语短 10-25%」/
               zh「中文比英文短 20-40%」/ar「膨胀 ~20%」,正则直读 notes/pillar_note);
               无口径市场用通用带 ±30% 并标 [推断]。长度口径=可见文本非空白字符数
               (跨语言统一可比单位;en 词 vs de 词的口径差由市场带吸收)。
  H2 结构对照 数量一致 pass;不一致列位置差(仅源有第 N 个/仅目标有第 N 个;
               跨语言文本不可逐字比对,按位置对齐列差)。
  FAQ 块对照  JSON-LD FAQPage / class·id 含 faq / 疑问式 FAQ 标题(10 语区词表)——
               同为有或同为缺 pass,单边有 warn。
  表格块对照  <table> 存在性对照(数据表是内容承诺,翻译丢表=丢信息)。
  JSON-LD description 跨语言一致性:同为缺/同为有(非空)pass,单边有 warn——
               结构化摘要不应只在一种语言存在。
  canonical 互指检查:两页 canonical 相同 → warn(目标语言页会被并入源语言索引,
               翻译白做);任一缺失 → warn;两页不同 → pass。自指核对需在线 URL,离线只比互指。
  hreflang 对存在性:仅提示(note,不计退出码)——源页 alternate 是否含目标语言码、
               目标页是否含源语言码(主子tag前缀匹配)。
用法: python3 parity_check.py --source zh.html --target en.html [--market XX] [--json]
退出码: 0 全部 pass(note 不计);1 存在 warn;2 参数/文件/市场错误。"""
import json
import os
import re
import sys
from html.parser import HTMLParser

BASE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_VERSION = 1
GENERIC_BAND = (-30.0, 30.0)     # 无市场口径时的通用带 ±30%(标 [推断])

FAQ_HEAD_RE = re.compile(
    r"faq|常见问题|よくある質問|자주\s*묻는|preguntas frecuentes|questions fr[ée]quentes|"
    r"foire aux questions|الأسئلة الشائعة|سوالات متکرار|câu hỏi thường gặp|pertanyaan umum|"
    r"सामान्य प्रश्न|częste pytania|veelgestelde vragen|domande frequenti|sık sorulan|常見問答",
    re.I)


class Page(HTMLParser):
    """一页的结构化抽取:lang/title/h2 序列/canonical/hreflang 集/JSON-LD/FAQ·table 存在/可见文本长。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = ""
        self.h2 = []                 # (序号, 文本) 按出现顺序
        self.canonical = ""
        self.hreflangs = []          # [(hreflang 值, href)]
        self.has_table = False
        self.faq_jsonld = False
        self.has_faq_block = False   # jsonld ∨ class/id ∑ 标题词
        self.jsonld_blocks = []
        self.text_n = 0              # 可见文本非空白字符数
        self._cur_h2 = None
        self._skip_depth = 0         # script/style/noscript/head 内不计数
        self._in_body = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = (a.get("lang") or "").strip()
        elif tag == "body":
            self._in_body = True
        elif tag == "link":
            rel = (a.get("rel") or "").lower()
            if "canonical" in rel:
                self.canonical = (a.get("href") or "").strip()
            if "alternate" in rel and a.get("hreflang"):
                self.hreflangs.append((a["hreflang"].strip().lower(), (a.get("href") or "").strip()))
        elif tag == "table":
            self.has_table = True
        elif tag == "h2":
            self._cur_h2 = ""
        elif tag in ("script", "style", "noscript"):
            self._skip_depth += 1
            if tag == "script" and "application/ld+json" in (a.get("type") or "").lower():
                self._ld_buf = []
                self._in_ld = True
        cls_id = " ".join(filter(None, (a.get("class"), a.get("id")))).lower()
        if "faq" in cls_id:
            self.has_faq_block = True

    def handle_startendtag(self, tag, attrs):
        # 自闭合 <link .../> 不进文本流;交给 starttag 逻辑
        self.handle_starttag(tag, attrs)
        if tag in ("script", "style", "noscript"):
            self._skip_depth -= 1
            self._in_ld = False

    def handle_endtag(self, tag):
        if tag == "h2" and self._cur_h2 is not None:
            t = re.sub(r"\s+", " ", self._cur_h2).strip()
            self.h2.append(t)
            self._cur_h2 = None
            if FAQ_HEAD_RE.search(t):
                self.has_faq_block = True
        elif tag in ("script", "style", "noscript"):
            self._skip_depth = max(0, self._skip_depth - 1)
            if tag == "script" and getattr(self, "_in_ld", False):
                self._in_ld = False
                self.jsonld_blocks.append("".join(self._ld_buf))
                self._ld_buf = []

    def handle_data(self, data):
        if getattr(self, "_in_ld", False):
            self._ld_buf.append(data)
            return
        if self._skip_depth or not self._in_body:
            return
        if self._cur_h2 is not None:
            self._cur_h2 += data
        self.text_n += sum(1 for ch in data if not ch.isspace())


def parse_page(path):
    if not os.path.isfile(path):
        sys.stderr.write("[ERROR] 文件不存在: %s\n" % path)
        raise SystemExit(2)
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            html = f.read()
    except OSError as e:
        sys.stderr.write("[ERROR] 文件不可读 %s: %s\n" % (path, e))
        raise SystemExit(2)
    p = Page()
    p.feed(html)
    p.close()
    return p


def jsonld_description(blocks):
    """任一 JSON-LD 块(顶层或 @graph 内)存在非空 description → 返回首个;解析失败忽略。"""
    def walk(node):
        if isinstance(node, dict):
            d = node.get("description")
            if isinstance(d, str) and d.strip():
                return d.strip()
            if isinstance(d, list) and any(isinstance(x, str) and x.strip() for x in d):
                return " ".join(x for x in d if isinstance(x, str)).strip()
            for v in node.values():
                r = walk(v)
                if r:
                    return r
        elif isinstance(node, list):
            for v in node:
                r = walk(v)
                if r:
                    return r
        return None
    for b in blocks:
        try:
            found = walk(json.loads(b))
        except (ValueError, TypeError):
            continue
        if found:
            return found
    return None


def jsonld_types(blocks):
    """全部 @type 值(小写)——FAQPage 检测用。"""
    out = set()

    def walk(node):
        if isinstance(node, dict):
            t = node.get("@type")
            if isinstance(t, str):
                out.add(t.lower())
            elif isinstance(t, list):
                out.update(str(x).lower() for x in t)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    for b in blocks:
        try:
            walk(json.loads(b))
        except (ValueError, TypeError):
            continue
    return out


def load_markets():
    with open(os.path.join(BASE, "markets.json"), encoding="utf-8") as f:
        return json.load(f)["markets"]


# 长度膨胀带:markets.json 语言相关字段(notes/pillar_note/title·desc limit note)直读。
# 口径短语:「比英语长 25-35%」「比英语短 10-25%」「比英文短 20-40%」「膨胀 ~20%」。
_RANGE_RE = re.compile(r"比英[语文]\s*[长短]\s*([0-9.]+)(?:\s*[-–~至]\s*([0-9.]+))?\s*%")
_EXPAND_RE = re.compile(r"膨胀\s*~?\s*([0-9.]+)(?:\s*[-–~至]\s*([0-9.]+))?\s*%")


def expansion_band(market_cfg):
    """市场膨胀带(%):markets.json 口径返回 (min, max, 依据);无口径返回通用 ±30 带+[推断]。"""
    text = json.dumps(market_cfg, ensure_ascii=False)
    m = _RANGE_RE.search(text)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2) or m.group(1))
        sign = -1.0 if "短" in m.group(0) else 1.0
        return tuple(sorted((sign * lo, sign * hi))), m.group(0).strip()
    m = _EXPAND_RE.search(text)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2) or m.group(1))
        return tuple(sorted((lo * 0.5, hi * 1.5))), m.group(0).strip()   # 单点估计 ±50% 展成带(ar 口径 ~20% → +10~30)
    return GENERIC_BAND, None


def primary(lang):
    return (lang or "").split("-")[0].strip().lower()


def h2_diff(src, tgt):
    """位置对齐的 H2 差列表(跨语言不可逐字比对,按序号列单边存在项)。"""
    diffs = []
    n, m = len(src.h2), len(tgt.h2)
    for i in range(min(n, m), max(n, m)):
        if i < n:
            diffs.append("仅源有第 %d 个 H2「%s」" % (i + 1, src.h2[i][:30] or "(空)"))
        if i < m:
            diffs.append("仅目标有第 %d 个 H2「%s」" % (i + 1, tgt.h2[i][:30] or "(空)"))
    return diffs


def check(source_path, target_path, market):
    markets = load_markets()
    src, tgt = parse_page(source_path), parse_page(target_path)

    market_cfg = None
    if market:
        market_cfg = markets.get(market)
        if not market_cfg:
            sys.stderr.write("[ERROR] 未知市场 %s;可用: %s\n" % (market, ", ".join(sorted(markets))))
            raise SystemExit(2)
    else:   # 未指定市场:按目标页 lang 主子 tag 在 markets.json 找带
        tgt_lang = primary(tgt.lang)
        if tgt_lang and tgt_lang in markets:
            market_cfg = markets[tgt_lang]

    band, basis = expansion_band(market_cfg) if market_cfg else (GENERIC_BAND, None)
    band_pct = (min(band), max(band))
    src_len, tgt_len = src.text_n, tgt.text_n
    checks, notes = [], []

    # ① 长度平价带
    if src_len == 0 or tgt_len == 0:
        checks.append(("length_parity", "warn", "可见文本长度为 0(源 %d/目标 %d)——无法评平价带"
                       % (src_len, tgt_len)))
    else:
        ratio = tgt_len / src_len
        lo, hi = 1 + band_pct[0] / 100.0, 1 + band_pct[1] / 100.0
        basis_txt = "markets.json 口径「%s」" % basis if basis else "通用带[推断](markets.json 无该语言膨胀口径)"
        if lo <= ratio <= hi:
            checks.append(("length_parity", "pass",
                           "长度比 %.2f 落在带 [%.2f, %.2f](目标 %d/源 %d 字符;%s)"
                           % (ratio, lo, hi, tgt_len, src_len, basis_txt)))
        else:
            checks.append(("length_parity", "warn",
                           "长度比 %.2f 出带 [%.2f, %.2f](目标 %d/源 %d 字符;%s)——疑截断或未本地化"
                           % (ratio, lo, hi, tgt_len, src_len, basis_txt)))

    # ② H2 结构对照
    diffs = h2_diff(src, tgt)
    if diffs:
        checks.append(("h2_structure", "warn", "H2 数量不一致(源 %d/目标 %d):%s"
                       % (len(src.h2), len(tgt.h2), ";".join(diffs))))
    else:
        checks.append(("h2_structure", "pass", "H2 数量一致(源/目标各 %d,按位置对齐)" % len(src.h2)))

    # ③ FAQ 块对照
    src_faq = src.has_faq_block or "faqpage" in jsonld_types(src.jsonld_blocks)
    tgt_faq = tgt.has_faq_block or "faqpage" in jsonld_types(tgt.jsonld_blocks)
    if src_faq != tgt_faq:
        checks.append(("faq_block", "warn", "FAQ 块单边存在(源 %s/目标 %s)——翻译丢了 FAQ 或源新增未同步"
                       % (src_faq, tgt_faq)))
    else:
        checks.append(("faq_block", "pass", "FAQ 块同为%s" % ("有" if src_faq else "缺")))

    # ④ 表格块对照
    if src.has_table != tgt.has_table:
        checks.append(("table_block", "warn", "表格块单边存在(源 %s/目标 %s)——数据表是内容承诺,丢表=丢信息"
                       % (src.has_table, tgt.has_table)))
    else:
        checks.append(("table_block", "pass", "表格块同为%s" % ("有" if src.has_table else "缺")))

    # ⑤ JSON-LD description 跨语言一致性(同为缺/同为有)
    src_d, tgt_d = jsonld_description(src.jsonld_blocks), jsonld_description(tgt.jsonld_blocks)
    if bool(src_d) != bool(tgt_d):
        checks.append(("jsonld_description", "warn", "JSON-LD description 单边存在(源 %s/目标 %s)——结构化摘要不应只在一语存在"
                       % (bool(src_d), bool(tgt_d))))
    else:
        checks.append(("jsonld_description", "pass", "JSON-LD description 同为%s" % ("有" if src_d else "缺")))

    # ⑥ canonical 互指检查
    if not src.canonical or not tgt.canonical:
        checks.append(("canonical", "warn", "canonical 缺失(源 %s/目标 %s)"
                       % (src.canonical or "缺", tgt.canonical or "缺")))
    elif src.canonical == tgt.canonical:
        checks.append(("canonical", "warn", "两页 canonical 相同(%s)——目标页被并入源语言索引,翻译页不自指"
                       % src.canonical))
    else:
        checks.append(("canonical", "pass", "两页 canonical 互不相同(离线只验互指;自指核对需在线 URL)"))

    # ⑦ hreflang 对存在性(仅提示)
    tgt_lang = primary(market_cfg.get("hreflang_codes", [""])[0]) if market_cfg else primary(tgt.lang)
    src_lang = primary(src.lang)
    if src_lang and tgt_lang:
        src_has = any(h.startswith(tgt_lang) for h, _ in src.hreflangs)
        tgt_has = any(h.startswith(src_lang) for h, _ in tgt.hreflangs)
        if src_has and tgt_has:
            notes.append("hreflang 双向在场(源含 %s,目标含 %s)" % (tgt_lang, src_lang))
        else:
            notes.append("hreflang 对不完整: 源页含目标语言 %s=%s, 目标页含源语言 %s=%s(仅提示,请核对 alternate 对)"
                         % (tgt_lang, src_has, src_lang, tgt_has))
    else:
        notes.append("语言码不可得(源 lang=%r/目标 lang=%r)——hreflang 对跳过(仅提示)" % (src.lang, tgt.lang))

    return {"source": source_path, "target": target_path, "market": market,
            "lang": {"source": src.lang, "target": tgt.lang},
            "band_pct": list(band_pct), "band_basis": basis or "generic±30[推断]",
            "length": {"source": src_len, "target": tgt_len},
            "h2": {"source": src.h2, "target": tgt.h2},
            "checks": [{"id": cid, "status": st, "detail": d} for cid, st, d in checks],
            "notes": notes}


def main():
    args = sys.argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(__doc__.strip())
        return
    opts = {"--source": None, "--target": None, "--market": None}
    i = 0
    while i < len(args):
        a = args[i]
        if a in opts:
            opts[a] = args[i + 1] if i + 1 < len(args) else None
            i += 2
        elif a == "--json":
            opts["--json"] = True
            i += 1
        else:
            sys.stderr.write("[ERROR] 未知参数 %s\n\n%s\n" % (a, __doc__.strip()))
            raise SystemExit(2)
    if not opts["--source"] or not opts["--target"]:
        sys.stderr.write("[ERROR] 需要 --source 与 --target\n\n" + __doc__.strip() + "\n")
        raise SystemExit(2)

    result = check(opts["--source"], opts["--target"], opts["--market"])
    warns = [c for c in result["checks"] if c["status"] == "warn"]
    for c in result["checks"]:
        mark = "✓" if c["status"] == "pass" else "[WARN]"
        print("%s %s: %s" % (mark, c["id"], c["detail"]))
    for n in result["notes"]:
        print("提示: %s" % n)
    print("判定: %d pass / %d warn%s" % (len(result["checks"]) - len(warns), len(warns),
                                         "(全过)" if not warns else ""))
    if opts.get("--json"):
        payload = dict(result)
        payload["schema_version"] = SCHEMA_VERSION
        payload["verdict"] = "pass" if not warns else "warn"
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    sys.exit(1 if warns else 0)


if __name__ == "__main__":
    main()
