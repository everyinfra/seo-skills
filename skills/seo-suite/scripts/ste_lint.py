#!/usr/bin/env python3
"""ste_lint.py — ASD-STE100 近似检查(stdlib only)。

口径与出处见 references/content/asd-ste100-web-writing.md 第六节。只做「近似检查」:
STE 的批准词典受版权保护,本脚本不内置;ASD 也不认证任何工具。报告里不写「符合 STE」。

用法:
  python3 ste_lint.py FILE [--lang en|zh|es|…] [--kind auto|procedure|description]
                      [--glossary terms.csv] [--json] [--fail-on fail|warn]
  FILE 可以是纯文本、Markdown 或 HTML;'-' 读 stdin。

规则(rule / 出处 / 严重度):
  STE-LEN-P     程序句 >20 词              STE 5.1           FAIL
  STE-LEN-D     描述句 >25 词              STE 6.3           FAIL
  STE-LEN-X     非英语句长 > markets.json sentence_ideal.max(单位同该字段)   本套件口径   WARN
  STE-PARA      描述段 >6 句               STE 段落规则(编号未核)  英文 FAIL / 其他 WARN
  STE-ONE       程序句里两个祈使动词由 and / then / 逗号 /「然后」「再」连接   STE 5.2(启发式)  WARN
  STE-PASSIVE   被动语态(be + 过去分词;中文「被」)   STE 3.6;3.3 的形容词用法会误报   程序 WARN / 描述 INFO
  STE-CONTR     缩写形式 n't 're 'm 'll 'd 've;'s 只查 it/that/there/what/here/let   STE 4.2   WARN
  STE-SEMI      正文分号(中文「；」)       STE 8.1;中文为本套件口径   WARN
  STE-COND      程序句里 if/when/unless(「如果」「当」)出现在第一个动词之后   官网 FAQ   WARN
  STE-TERM      出现术语表里的禁用写法     STE 1.11、9.4     FAIL
  STE-TERM-VAR  无术语表时,同一词组归一后有两种以上写法   STE 9.4(启发式)   WARN
  STE-MKT       营销词 >3 处(markets.json marketing_words)   本套件口径   WARN
  STE-NOUN / STE-DICT   多词名词、批准词:不机检   MANUAL

计词(英文):按空白切词;连字符词算 1 词(8.7);括号内文本算 1 词(8.5);引号内文本、
带单位的数字(10 MB)算 1 词(8.6,按 TechScribe 的举例);竖排列表前的冒号当句末(8.4)。
e.g. / i.e. / vs. / 小数点不切句。中文句长按字符数,与 market_lint 的 chars 单位一致。

退出码:0 无 FAIL;1 有 FAIL(--fail-on warn 时 WARN 也算);2 输入或参数错误。
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from html.parser import HTMLParser

SCHEMA_VERSION = 1
BASE = os.path.dirname(os.path.abspath(__file__))
STANDARD = "ASD-STE100 Issue 9 (approximate checks)"

PROC_MAX, DESC_MAX, PARA_MAX = 20, 25, 6
IMPERATIVE_EN = {
    "add", "allow", "apply", "attach", "build", "call", "change", "check", "choose", "clear", "click",
    "close", "configure", "connect", "copy", "create", "define", "delete", "deploy", "disable", "do",
    "download", "edit", "enable", "enter", "export", "fill", "find", "follow", "get", "give", "go",
    "import", "include", "insert", "install", "keep", "let", "log", "make", "move", "open", "paste",
    "pass", "pick", "poll", "press", "put", "read", "reduce", "refresh", "register", "remove",
    "rename", "replace", "request", "restart", "retry", "return", "run", "save", "scroll", "select",
    "send", "set", "sign", "specify", "start", "stop", "submit", "switch", "tap", "test", "try",
    "turn", "type", "update", "upload", "use", "verify", "visit", "wait", "write",
}
IMPERATIVE_ZH = ("点击", "单击", "选择", "打开", "输入", "复制", "粘贴", "运行", "发送", "添加", "设置",
                 "填写", "调用", "安装", "删除", "上传", "下载", "保存", "登录", "注册", "检查", "确认",
                 "进入", "创建", "修改", "提交", "重试", "等待", "切换", "启用", "关闭")
COND_EN = ("if", "when", "unless")
COND_ZH = ("如果", "当", "若")
IRREGULAR_PP = {
    "been", "begun", "bought", "brought", "built", "caught", "chosen", "done", "drawn", "found", "given",
    "gone", "got", "held", "kept", "known", "laid", "led", "left", "lost", "made", "meant", "met", "paid",
    "put", "read", "run", "said", "seen", "sent", "set", "shown", "shut", "sold", "spent", "split",
    "taken", "taught", "thought", "told", "understood", "won", "written",
}
BE_FORMS = r"(?:am|is|are|was|were|be|been|being)"
PASSIVE_EN = re.compile(r"\b" + BE_FORMS + r"\s+(?:\w+ly\s+)?(\w+)\b", re.I)
CONTRACTION = re.compile(r"\b\w+(?:n't|'re|'ve|'ll|'m|'d)\b|\b(?:it|that|there|what|here|let)'s\b", re.I)
UNITS = {"b", "kb", "mb", "gb", "tb", "ms", "s", "sec", "min", "h", "px", "%", "kib", "mib", "gib",
         "credits", "usd", "rpm", "rps", "qps"}
ABBREV = ("e.g.", "i.e.", "vs.", "etc.", "approx.", "no.", "fig.", "mr.", "mrs.", "dr.")
CJK_RE = re.compile(r"[\u3400-\u9fff]")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
TERM_STOP = {"a", "an", "the", "of", "to", "in", "on", "at", "by", "or", "and", "s", "is", "it", "as"}
BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer", "main", "aside", "blockquote",
              "h1", "h2", "h3", "h4", "h5", "h6", "tr", "td", "th", "dd", "dt", "figcaption"}


class InputError(Exception):
    pass


# ---------------------------------------------------------------- 读入与分块 --

class _HtmlBlocks(HTMLParser):
    """HTML → 块列表 [(kind, text)]。kind: para / ol / ul / heading。script、style、pre、code 块跳过。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self._buf = []
        self._list_stack = []
        self._skip = 0
        self._in_li = 0
        self._heading = False

    def _flush(self, kind=None):
        text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
        self._buf = []
        if text:
            if kind is None:
                kind = "heading" if self._heading else "para"
            self.blocks.append((kind, text))

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "pre", "template", "svg", "noscript", "title", "head", "code"):
            self._flush()
            self._skip += 1
        elif self._skip:
            return
        elif tag in ("ol", "ul"):
            self._flush()
            self._list_stack.append(tag)
        elif tag == "li":
            self._flush()
            self._in_li += 1
        elif tag == "br":
            self._buf.append(" ")
        elif tag in BLOCK_TAGS:
            self._flush()
            self._heading = tag in ("h1", "h2", "h3", "h4", "h5", "h6")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "pre", "template", "svg", "noscript", "title", "head", "code"):
            if self._skip:
                self._skip -= 1
            return
        if self._skip:
            return
        if tag == "li":
            kind = self._list_stack[-1] if self._list_stack else "ul"
            self._flush(kind)
            self._in_li = max(0, self._in_li - 1)
        elif tag in ("ol", "ul"):
            self._flush()
            if self._list_stack:
                self._list_stack.pop()
        elif tag in BLOCK_TAGS:
            self._flush()
            self._heading = False

    def handle_data(self, data):
        if not self._skip:
            self._buf.append(data)

    def close(self):
        super().close()
        self._flush()


def blocks_from_text(text: str) -> list[tuple[str, str]]:
    """纯文本 / Markdown → 块。空行分段;'1.'、'1)' 开头是有序列表项,'-'、'*'、'+' 开头是无序项;
    ``` 代码块与 4 空格缩进代码跳过;以 # 开头的是标题。"""
    blocks, para, in_code = [], [], False

    def flush():
        if para:
            blocks.append(("para", " ".join(para)))
            para.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            flush()
            in_code = not in_code
            continue
        if in_code or line.startswith("    ") or line.startswith("\t"):
            continue
        s = line.strip()
        if not s:
            flush()
            continue
        m_ol = re.match(r"^(\d+)[.)、]\s+(.*)$", s)
        m_ul = re.match(r"^[-*+•]\s+(.*)$", s)
        if s.startswith("#"):
            flush()
            blocks.append(("heading", s.lstrip("#").strip()))
        elif m_ol:
            flush()
            blocks.append(("ol", m_ol.group(2)))
        elif m_ul:
            flush()
            blocks.append(("ul", m_ul.group(1)))
        else:
            para.append(s)
    flush()
    return blocks


def read_blocks(text: str) -> list[tuple[str, str]]:
    if re.search(r"<(html|body|p|div|li|h[1-6]|title)\b", text, re.I):
        p = _HtmlBlocks()
        p.feed(text)
        p.close()
        return p.blocks
    return blocks_from_text(text)


# ---------------------------------------------------------------- 切句与计词 --

def split_sentences(text: str, lang: str) -> list[str]:
    if lang == "zh" or (lang not in ("en",) and CJK_RE.search(text) and lang in ("ja",)):
        parts = re.split(r"(?<=[。！？!?])", text)
        return [p.strip() for p in parts if p.strip()]
    protected = text
    for i, ab in enumerate(ABBREV):
        protected = re.sub(re.escape(ab), f"\u0000{i}\u0000", protected, flags=re.I)
    protected = re.sub(r"(\d)\.(\d)", "\\1\u0001\\2", protected)
    parts = re.split(r"(?<=[.!?])\s+|(?<=:)\s*$", protected)
    out = []
    for p in parts:
        p = p.replace("\u0001", ".")
        for i, ab in enumerate(ABBREV):
            p = p.replace(f"\u0000{i}\u0000", ab)
        if p.strip():
            out.append(p.strip())
    return out


def count_words_en(sentence: str) -> int:
    s = re.sub(r"\([^()]*\)", " PAREN ", sentence)               # 8.5 括号内文本算 1 词
    s = re.sub(r"[\"“][^\"”]*[\"”]", " QUOTE ", s)                # 8.6 引号内文本算 1 词
    toks = [t for t in re.split(r"\s+", s.strip()) if t and re.search(r"\w", t)]
    n, i = 0, 0
    while i < len(toks):
        t = toks[i]
        if re.fullmatch(r"[\d.,]+", t) and i + 1 < len(toks) and toks[i + 1].strip(".,;:").lower() in UNITS:
            i += 2                                                 # 8.6 带单位的数字算 1 词
        else:
            i += 1
        n += 1
    return n


def first_word(sentence: str) -> str:
    s = re.sub(r"^\W+", "", sentence)
    s = re.sub(r"^(?:if|when|before|after|unless|to|once)\b[^,]*,\s*", "", s, flags=re.I)  # 去句首条件从句
    m = re.match(r"([A-Za-z]+)", s)
    return m.group(1).lower() if m else ""


def classify(sentence: str, block_kind: str, lang: str, forced: str) -> str:
    if forced in ("procedure", "description"):
        return forced
    if block_kind == "ol":
        return "procedure"
    if lang == "zh":
        return "procedure" if sentence.lstrip("（(「“").startswith(IMPERATIVE_ZH) else "description"
    return "procedure" if first_word(sentence) in IMPERATIVE_EN else "description"


# ---------------------------------------------------------------- 规则 --

def load_market(lang: str) -> dict:
    with open(os.path.join(BASE, "markets.json"), encoding="utf-8") as f:
        ms = json.load(f)["markets"]
    return ms.get(lang, {})


def load_glossary(path: str) -> list[tuple[str, str, list[str]]]:
    if not os.path.isfile(path):
        raise InputError(f"术语表不存在: {path}")
    out = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            keys = {k.strip().lower(): (v or "").strip() for k, v in r.items()}
            if not keys.get("preferred"):
                raise InputError("术语表要有 concept,preferred,forbidden 三列")
            forb = [x.strip() for x in keys.get("forbidden", "").split("|") if x.strip()]
            out.append((keys.get("concept", ""), keys["preferred"], forb))
    return out


def lint(text: str, lang: str = "en", kind: str = "auto", glossary=None) -> dict:
    market = load_market(lang)
    blocks = read_blocks(text)
    findings, stats = [], {"sentences": 0, "paragraphs": 0, "procedure": 0, "description": 0}

    def add(rule, ref, sev, excerpt, measured=None, limit=None, k=None, line=None):
        findings.append({"rule": rule, "ref": ref, "severity": sev, "line": line,
                         "excerpt": excerpt[:160], "measured": measured, "limit": limit, "kind": k})

    sent_ideal = (market.get("sentence_ideal") or {})
    x_max, x_unit = sent_ideal.get("max"), sent_ideal.get("unit", "words")
    all_body = []
    skipped = 0
    for bi, (bkind, btext) in enumerate(blocks, 1):
        if bkind == "heading":
            continue
        if not is_prose(btext, lang):
            skipped += 1
            continue
        all_body.append(btext)
        sents = split_sentences(btext, lang)
        if bkind == "para":
            stats["paragraphs"] += 1
            desc_sents = [s for s in sents if classify(s, bkind, lang, kind) == "description"]
            if len(desc_sents) > PARA_MAX:
                add("STE-PARA", "STE 段落规则(编号未核)", "FAIL" if lang == "en" else "WARN",
                    btext, len(desc_sents), PARA_MAX, "description", bi)
        for s in sents:
            k = classify(s, bkind, lang, kind)
            stats["sentences"] += 1
            stats[k] += 1
            if lang == "en":
                n = count_words_en(s)
                if k == "procedure" and n > PROC_MAX:
                    add("STE-LEN-P", "STE 5.1", "FAIL", s, n, PROC_MAX, k, bi)
                elif k == "description" and n > DESC_MAX:
                    add("STE-LEN-D", "STE 6.3", "FAIL", s, n, DESC_MAX, k, bi)
                for m in PASSIVE_EN.finditer(s):
                    w = m.group(1).lower()
                    if w.endswith(("ed", "en")) or w in IRREGULAR_PP:
                        add("STE-PASSIVE", "STE 3.6(3.3 形容词用法会误报)",
                            "WARN" if k == "procedure" else "INFO", s, m.group(0), None, k, bi)
                        break
                for m in CONTRACTION.finditer(s):
                    add("STE-CONTR", "STE 4.2", "WARN", s, m.group(0), None, k, bi)
                if k == "procedure":
                    verbs = [w.lower() for w in re.findall(r"[A-Za-z]+", s)]
                    joined = re.search(r"\b(?:and(?: then)?|then)\s+([a-z]+)\b|,\s*([a-z]+)\b", s, re.I)
                    if joined:
                        nxt = (joined.group(1) or joined.group(2) or "").lower()
                        if nxt in IMPERATIVE_EN and verbs and verbs[0] in IMPERATIVE_EN | {first_word(s)}:
                            add("STE-ONE", "STE 5.2(启发式)", "WARN", s, joined.group(0).strip(), None, k, bi)
                    fw = first_word(s)
                    pos_v = next((i for i, w in enumerate(verbs) if w == fw), None)
                    for i, w in enumerate(verbs):
                        if w in COND_EN and pos_v is not None and i > pos_v:
                            add("STE-COND", "官网 FAQ(条件放句首)", "WARN", s, w, None, k, bi)
                            break
            else:
                if x_max:
                    n = len(s) if x_unit == "chars" else len(re.findall(r"\w+", s))
                    if n > x_max:
                        add("STE-LEN-X", "本套件口径(markets.json sentence_ideal)", "WARN", s, n, x_max, k, bi)
                if lang == "zh":
                    if re.search(r"被[\u4e00-\u9fff]", s):
                        add("STE-PASSIVE", "STE 3.6(中文为本套件口径)",
                            "WARN" if k == "procedure" else "INFO", s, "被", None, k, bi)
                    if k == "procedure" and re.search(r"然后|再(?=[\u4e00-\u9fff])", s):
                        add("STE-ONE", "STE 5.2(启发式;中文为本套件口径)", "WARN", s, "然后/再", None, k, bi)
                    if k == "procedure":
                        verb_pos = min((s.find(v) for v in IMPERATIVE_ZH if v in s), default=-1)
                        for c in COND_ZH:
                            ci = s.find(c)
                            if ci > verb_pos >= 0:
                                add("STE-COND", "官网 FAQ(条件放句首;中文为本套件口径)", "WARN", s, c, None, k, bi)
                                break
            if ";" in s or "；" in s:
                add("STE-SEMI", "STE 8.1" + ("" if lang == "en" else "(中文为本套件口径)"), "WARN", s, ";", None, k, bi)

    body = "\n".join(all_body)
    low = body.lower()
    mw = [w for w in (market.get("marketing_words") or []) if w.lower() in low]
    hits = sum(low.count(w.lower()) for w in mw)
    if hits > 3:
        add("STE-MKT", "本套件口径(markets.json marketing_words)", "WARN", ", ".join(mw), hits, 3)
    if glossary:
        for concept, preferred, forbidden in glossary:
            for f in forbidden:
                pat = re.compile(r"(?<!\w)" + re.escape(f) + r"(?!\w)", re.I)
                for m in pat.finditer(body):
                    if body[m.start():m.end()] == preferred:
                        continue
                    add("STE-TERM", "STE 1.11、9.4", "FAIL", body[max(0, m.start() - 40):m.end() + 40],
                        m.group(0), preferred)
    else:
        findings.extend(term_variants(body))
    sev_order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda f: (sev_order.get(f["severity"], 3), f["rule"], f["line"] or 0))
    summary = {"fail": sum(f["severity"] == "FAIL" for f in findings),
               "warn": sum(f["severity"] == "WARN" for f in findings),
               "info": sum(f["severity"] == "INFO" for f in findings),
               "manual": ["STE-NOUN 多词名词 ≤3 个名词(STE 2.1,需词性标注)",
                          "STE-DICT 批准词(STE 1.1–1.3,词典受版权保护)"]}
    stats["skipped_non_prose_blocks"] = skipped
    return {"schema_version": SCHEMA_VERSION, "tool": "ste_lint", "standard": STANDARD, "lang": lang,
            "stats": stats, "findings": findings, "summary": summary}


def is_prose(text: str, lang: str) -> bool:
    """跳过数据块:3 个以上 ISO 日期(状态时间线、更新日志),或字母词不到一半的块(表格数字、代码片段)。"""
    if len(DATE_RE.findall(text)) >= 3:
        return False
    if lang == "zh" or CJK_RE.search(text):
        return len(CJK_RE.findall(text)) >= max(4, len(text) * 0.3)
    toks = text.split()
    if not toks:
        return False
    words = sum(1 for x in toks if re.fullmatch(r"[A-Za-z][A-Za-z'’-]*[.,:;!?)]?", x))
    return words / len(toks) >= 0.5


def term_variants(body: str) -> list[dict]:
    """同一词组(连字符/空格/大小写不同)出现两种以上写法 → WARN。只看含连字符的词和它的空格/连写形式。"""
    forms: dict[str, set[str]] = {}
    for m in re.finditer(r"(?=\b([A-Za-z][A-Za-z0-9]*)([- ])([A-Za-z][A-Za-z0-9]*)\b)", body):   # 重叠匹配:The API key 里的 API key 不被吞掉
        a, sep, b = m.group(1), m.group(2), m.group(3)
        if len(a) < 3 or len(b) < 3 or a.lower() in TERM_STOP or b.lower() in TERM_STOP:
            continue
        if sep == "-" and a[0].isupper() and b[0].isupper():   # HTTP 头名、产品名(Retry-After、X-Foo)不算
            continue
        surf = a + sep + b
        key = (a + b).lower()
        forms.setdefault(key, set()).add(surf)
    for m in re.finditer(r"\b[A-Za-z][A-Za-z0-9]{3,}\b", body):        # 连写形式(apikey、signup)
        key = m.group(0).lower()
        if key in forms:
            forms[key].add(m.group(0))
    out = []
    for key, fs in sorted(forms.items()):
        shapes = {re.sub(r"[A-Za-z0-9]", "x", f.lower()) for f in fs}  # 只比连字符/空格/连写结构
        if len(shapes) >= 2 and any("-" in f for f in fs):         # 至少一种写法带连字符才算变体组
            out.append({"rule": "STE-TERM-VAR", "ref": "STE 9.4(启发式)", "severity": "WARN", "line": None,
                        "excerpt": " / ".join(sorted(fs)), "measured": len(fs), "limit": 1, "kind": None})
    return out


def render_markdown(rep: dict, path: str) -> str:
    st, sm = rep["stats"], rep["summary"]
    lines = [f"## ste_lint:{path}({rep['standard']};近似检查,不是合规认证)", "",
             f"- 语言 {rep['lang']};句 {st['sentences']}(程序 {st['procedure']} / 描述 {st['description']});段 {st['paragraphs']}", ""]
    for f in rep["findings"]:
        meas = "" if f["measured"] is None else f" {f['measured']}"
        lim = "" if f["limit"] is None else f" > {f['limit']}"
        lines.append(f"[{f['severity']}] {f['rule']}({f['ref']}){meas}{lim}:{f['excerpt']}")
    lines += ["", f"汇总:FAIL {sm['fail']} / WARN {sm['warn']} / INFO {sm['info']};人工项:{';'.join(sm['manual'])}"]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ASD-STE100 近似检查(stdlib only;口径见 references/content/asd-ste100-web-writing.md)")
    ap.add_argument("file", help="文本 / Markdown / HTML 文件,'-' 读 stdin")
    ap.add_argument("--lang", default="en", help="语言(markets.json 市场码;默认 en)")
    ap.add_argument("--kind", default="auto", choices=("auto", "procedure", "description"))
    ap.add_argument("--glossary", metavar="CSV", help="术语表:concept,preferred,forbidden(forbidden 用 | 分隔)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fail-on", default="fail", choices=("fail", "warn"))
    a = ap.parse_args(argv)
    try:
        if a.file == "-":
            text = sys.stdin.read()
        else:
            if not os.path.isfile(a.file):
                raise InputError(f"文件不存在: {a.file}")
            with open(a.file, encoding="utf-8", errors="replace") as f:
                text = f.read()
        gl = load_glossary(a.glossary) if a.glossary else None
    except InputError as e:
        sys.stderr.write(f"输入错误: {e}\n")
        return 2
    rep = lint(text, lang=a.lang, kind=a.kind, glossary=gl)
    rep["file"] = a.file
    print(json.dumps(rep, ensure_ascii=False, indent=1) if a.json else render_markdown(rep, a.file))
    bad = rep["summary"]["fail"] + (rep["summary"]["warn"] if a.fail_on == "warn" else 0)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
