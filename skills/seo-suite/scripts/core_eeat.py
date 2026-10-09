#!/usr/bin/env python3
r"""CORE-EEAT 80 项基准的机械化子集(stdlib-only)。

CORE(C/O/R/E)管内容体 = GEO 分;EEAT(Exp/Ept/A/T)管作者组织站 = SEO 分。
本脚本只机判可机判的切片(三态:pass / fail / not_applicable;na 离开分母),
不可机判的项(如 ≥3 查询变体)固定记 na,不虚稀释。

覆盖项:
  C 清晰: C1 前150词直接答案(首段含数字或结论句) / C2 ≥3 查询变体(无法机判→na)
          / C3 术语首用即定义(引号定义或"是指") / C4 段落 3-5 句
  O 组织: O1 单 H1 / O2 对比表存在 / O3 列表每 500 词 1-2 块
  R 可引用: R1 ≥5 带单位数字(正则 \d+(\.\d+)?\s?(%|万|亿|元|$|€|£|ms|s|倍))
          / R2 引用标记 ≥1 每千词(脚标/URL/来源行)
  E 独占: E1 一手数据词(实测/问卷/our survey…) / E2 原创图标记(![](/<img>/<figure>)
  Exp 体验: 第一人称+动作动词 / 时间戳 / 前后对比词
  Ept 专业: 作者行 / bio
  A 权威: 奖项/featured/媒体名
  T 信任: 隐私条款链接 / 全 HTTPS / 联系信息
  VETO(3 项,任一命中总分封顶 59):
    V1 利益冲突标记(赞助/sponsored/affiliate…)
    V2 标题承诺与首段断裂(标题含承诺词但首段几乎无重叠)
    V3 内部矛盾数字(同一上下文同一指标出现不同数值)

输出: GEO=(C+O+R+E)/4,SEO=(Exp+Ept+A+T)/4,总分=两者均值,band A/B/C/D。

用法:
  python3 core_eeat.py FILE            # 纯文本/markdown/HTML 文件
  python3 core_eeat.py FILE --url URL  # 额外拉取线上页面(结构检查用原始 HTML)
  python3 core_eeat.py --self-test
"""
import argparse
import os
import re
import sys
import tempfile
import traceback
from html.parser import HTMLParser
from urllib.request import Request, urlopen

UNIT_NUM_RE = re.compile(r"\d+(?:\.\d+)?\s?(?:%|万|亿|元|\$|€|£|ms|s|倍)")
CONCLUSION_RE = re.compile(
    r"因此|总之|结论|答案是|简而言之|一句话|i recommend|we recommend|bottom line|in short|the answer",
    re.I)
_QO = "「『\"'“«"          # 开引号集合
_QC = "」』\"'”»"          # 闭引号集合
DEFINITION_RE = re.compile(
    "[" + re.escape(_QO) + "]([^" + re.escape(_QC) + "\\n]{2,20})"
    "[" + re.escape(_QC) + r"]\s*(?:是指|指的是|means|is defined as)"
    r"|([\w\u4e00-\u9fff]{2,12})(?:是指|指的是)"
    r"|(?:所谓|defined as|definition of)")
FIRST_PERSON_RE = re.compile(r"(?<![a-z])(?:我们|笔者|亲身|我个人)(?![a-z])|(?<![a-z])(?:I|we)(?![a-z])",
                             re.I)
ACTION_VERB_RE = re.compile(
    r"测试|试用|实测|部署|搭建|安装|跑了|采集|used|tested|tried|deployed|built|installed|measured",
    re.I)
TIMESTAMP_RE = re.compile(r"\d{4}[-/年.]\s?\d{1,2}|上周|上个月|上季度|last week|last month")
BEFORE_AFTER_RE = re.compile(
    r"之前|之后|以前|原先|相比|提升|下降|翻倍|before|after|improved from|went from")
FIRST_PARTY_RE = re.compile(
    r"我们的实测|实测|亲自测试|我们的调查|我们调研|问卷|受访|样本量|our survey|we surveyed|"
    r"our own data|our research|first-party|第一手", re.I)
BYLINE_RE = re.compile(
    r"(?m)^\s*(?:作者|撰文|文|By|Written by|Author)s?\s*[::]?\s*[\w\u4e00-\u9fff]", re.I)
BIO_RE = re.compile(r"作者简介|个人简介|about the author|\bbio\b", re.I)
AUTHORITY_RE = re.compile(
    r"award|获奖|殊荣|featured in|as seen in|mentioned in|被.{0,8}报道|forbes|techcrunch|"
    r"纽约时报|华尔街日报|36氪|wikipedia|维基百科", re.I)
PRIVACY_TERMS_RE = re.compile(r"隐私|privacy|服务条款|terms of (?:service|use)|用户协议|免责声明", re.I)
CONTACT_RE = re.compile(
    r"contact|联系我们|联系方式|邮箱|电子邮箱|mailto|[\w.+-]+@[\w-]+\.[\w.]+", re.I)
COI_RE = re.compile(
    r"赞助|sponsored|广告合作|affiliate|联盟营销|联盟计划|paid partnership|promoted by|"
    r"本内容由.{0,12}(?:赞助|赞助商)", re.I)
PROMISE_RE = re.compile(
    r"最好|最佳|终极|全攻略|完全指南|彻底|top\s*\d+|best|\d+\s*(?:个|种|条|steps?|ways?|方法|技巧|秘诀)",
    re.I)
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s)")
TABLE_SEP_RE = re.compile(r"^[\s|:-]+$")
CITATION_MARK_RE = re.compile(
    r"\[\d+\]|【\d+】|https?://|(?:来源|出处|source|参考)\s*[::]", re.I)


def count_words(text):
    """CJK 感知词数:ASCII 词 + CJK 字(近似,密度用途)。"""
    return len(re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*", text)) \
        + len(re.findall(r"[\u4e00-\u9fff]", text))


def sentences(par):
    parts = re.split(r"[。!?!?;;]+|\.\s+", par)
    return [p.strip() for p in parts if p.strip()]


def split_paragraphs(text):
    """空行分块;剔除标题/列表/表格/图片行,保留 >=30 字符的正文段。"""
    paras, block = [], []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            if block:
                paras.append(" ".join(block))
                block = []
            continue
        if s.startswith("#") or LIST_ITEM_RE.match(s) or s.startswith("|") \
                or s.startswith("![") or s.startswith("<"):
            if block:
                paras.append(" ".join(block))
                block = []
            continue
        block.append(s)
    if block:
        paras.append(" ".join(block))
    return [p for p in paras if len(p) >= 30]


def markdown_structure(text):
    h1 = len(re.findall(r"(?m)^#\s+\S", text))
    any_header = bool(re.search(r"(?m)^#{1,6}\s+\S", text))
    tables = sum(1 for l in text.splitlines()
                 if "|" in l and "-" in l and TABLE_SEP_RE.match(l.strip()))
    images = len(re.findall(r"!\[[^\]]*\]\(", text)) + len(re.findall(r"<img\b", text, re.I)) \
        + len(re.findall(r"<figure\b", text, re.I))
    list_blocks, in_list = 0, False
    for l in text.splitlines():
        if LIST_ITEM_RE.match(l):
            if not in_list:
                list_blocks += 1
            in_list = True
        else:
            in_list = False
    return {"h1": h1, "any_header": any_header, "tables": tables,
            "images": images, "list_blocks": list_blocks}


class _HTMLDoc(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.buf, self.h1, self.tables, self.images, self.lists = [], 0, 0, 0, 0
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "template"):
            self._skip += 1
        elif tag == "h1":
            self.h1 += 1
            self.buf.append("\n")
        elif tag == "table":
            self.tables += 1
            self.buf.append("\n")
        elif tag == "img":
            self.images += 1
        elif tag in ("ul", "ol"):
            self.lists += 1
            self.buf.append("\n")
        elif tag in ("h2", "h3", "h4", "h5", "h6", "p", "div", "li", "tr",
                     "br", "blockquote"):
            self.buf.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "template") and self._skip:
            self._skip -= 1
        elif tag in ("p", "div", "li", "tr", "table", "h1", "h2", "h3", "blockquote"):
            self.buf.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.buf.append(data)


def html_structure(raw):
    p = _HTMLDoc()
    p.feed(raw)
    text = re.sub(r"[ \t]+", " ", "".join(p.buf))
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return {"text": text, "h1": p.h1, "any_header": True, "tables": p.tables,
            "images": p.images + len(re.findall(r"<figure\b", raw, re.I)),
            "list_blocks": p.lists}


def load_document(path=None, url=None, raw=None):
    if raw is None:
        if url:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0 (seo-suite core_eeat)"})
            with urlopen(req, timeout=20) as r:
                raw = r.read().decode("utf-8", errors="replace")
        elif path:
            if path == "-":
                raw = sys.stdin.read()
            else:
                with open(path, encoding="utf-8", errors="replace") as f:
                    raw = f.read()
    if not raw.strip():
        raise ValueError("文档为空")
    low = raw.lstrip().lower()
    if low.startswith("<!doctype html") or "</html>" in low or "<body" in low:
        h = html_structure(raw)
        return {"raw": raw, "text": h["text"], "h1": h["h1"], "any_header": True,
                "tables": h["tables"], "images": h["images"], "list_blocks": h["list_blocks"],
                "urls": re.findall(r'''https?://[^\s"'<>)]+''', raw)}
    st = markdown_structure(raw)
    return {"raw": raw, "text": raw, "h1": st["h1"], "any_header": st["any_header"],
            "tables": st["tables"], "images": st["images"], "list_blocks": st["list_blocks"],
            "urls": re.findall(r"https?://[^\s)\]]+", raw)}


def analyze(doc):
    text = doc["text"]
    words = count_words(text)
    paras = split_paragraphs(text)
    first_para = paras[0] if paras else " ".join(
        re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", text)[:150])
    first_zone = re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", first_para)[:150]
    first_zone_text = " ".join(first_zone)
    items = []

    def add(group, code, name, verdict, note=""):
        items.append({"group": group, "code": code, "name": name,
                      "verdict": verdict, "note": note})

    # ---- C 清晰 ----
    has_digit = any(re.search(r"\d", t) for t in first_zone[:150])
    add("C", "C1", "前 150 词直接答案(首段含数字或结论句)",
        "pass" if (has_digit or CONCLUSION_RE.search(first_zone_text)) else "fail",
        "首段含数字" if has_digit else
        ("含结论句标记" if CONCLUSION_RE.search(first_zone_text) else "首段无数字且无结论句"))
    add("C", "C2", "≥3 查询变体覆盖", "not_applicable", "需查询变体数据,无法机判")
    dmatch = DEFINITION_RE.search(text)
    add("C", "C3", "术语首用即定义(引号定义或「是指」)",
        "pass" if dmatch else "fail", "命中: %s" % dmatch.group(0)[:24] if dmatch else "")
    if len(paras) < 2:
        add("C", "C4", "段落 3-5 句", "not_applicable", "正文段不足 2 段")
    else:
        in_range = sum(1 for p in paras if 3 <= len(sentences(p)) <= 5)
        frac = in_range / len(paras)
        add("C", "C4", "段落 3-5 句", "pass" if frac >= 0.5 else "fail",
            "%d/%d 段在 3-5 句(%.0f%%)" % (in_range, len(paras), 100 * frac))

    # ---- O 组织 ----
    if doc["h1"] == 0 and not doc["any_header"]:
        add("O", "O1", "单 H1", "not_applicable", "未见任何标题标记(非 markdown/HTML?)")
    else:
        add("O", "O1", "单 H1", "pass" if doc["h1"] == 1 else "fail",
            "H1=%d" % doc["h1"])
    add("O", "O2", "对比表存在", "pass" if doc["tables"] >= 1 else "fail",
        "表 %d 张" % doc["tables"])
    if words < 1:
        add("O", "O3", "列表每 500 词 1-2 块", "not_applicable", "词数为 0")
    else:
        per500 = doc["list_blocks"] * 500 / words
        add("O", "O3", "列表每 500 词 1-2 块",
            "pass" if 1 <= per500 <= 2 else "fail",
            "列表块 %d / 词 %d = %.2f 块每 500 词" % (doc["list_blocks"], words, per500))

    # ---- R 可引用 ----
    unit_nums = UNIT_NUM_RE.findall(text)
    add("R", "R1", "≥5 带单位数字", "pass" if len(unit_nums) >= 5 else "fail",
        "命中 %d 处" % len(unit_nums))
    cites = len(CITATION_MARK_RE.findall(text))
    cite_per_1k = cites * 1000 / max(words, 1)
    add("R", "R2", "引用标记 ≥1 每千词", "pass" if cite_per_1k >= 1 else "fail",
        "标记 %d 个,%.2f/千词" % (cites, cite_per_1k))

    # ---- E 独占 ----
    fp = FIRST_PARTY_RE.findall(text)
    add("E", "E1", "一手数据词(实测/问卷/our survey)", "pass" if fp else "fail",
        "命中 %d 处" % len(fp))
    add("E", "E2", "原创图标记(图片/figure)", "pass" if doc["images"] >= 1 else "fail",
        "图 %d 张" % doc["images"])

    # ---- Exp 体验 ----
    has_fp_person = bool(FIRST_PERSON_RE.search(text))
    has_action = bool(ACTION_VERB_RE.search(text))
    add("Exp", "Exp1", "第一人称 + 动作动词",
        "pass" if (has_fp_person and has_action) else "fail",
        "人称=%s 动作动词=%s" % (has_fp_person, has_action))
    ts = TIMESTAMP_RE.findall(text)
    add("Exp", "Exp2", "时间戳", "pass" if ts else "fail", "命中 %d 处" % len(ts))
    ba = BEFORE_AFTER_RE.findall(text)
    add("Exp", "Exp3", "前后对比词", "pass" if ba else "fail", "命中 %d 处" % len(ba))

    # ---- Ept 专业 ----
    add("Ept", "Ept1", "作者行(byline)", "pass" if BYLINE_RE.search(text) else "fail", "")
    add("Ept", "Ept2", "作者 bio", "pass" if BIO_RE.search(text) else "fail", "")

    # ---- A 权威 ----
    au = AUTHORITY_RE.findall(text)
    add("A", "A1", "奖项/featured/媒体名", "pass" if au else "fail", "命中 %d 处" % len(au))

    # ---- T 信任 ----
    add("T", "T1", "隐私/条款链接或字样", "pass" if PRIVACY_TERMS_RE.search(text) else "fail", "")
    urls = doc["urls"]
    insecure = [u for u in urls if u.startswith("http://")]
    if not urls:
        add("T", "T2", "全 HTTPS", "not_applicable", "文中无外部链接")
    else:
        add("T", "T2", "全 HTTPS", "fail" if insecure else "pass",
            "http:// 链接 %d 个" % len(insecure))
    add("T", "T3", "联系信息", "pass" if CONTACT_RE.search(text) else "fail", "")

    # ---- VETO ----
    vetoes = []
    if COI_RE.search(text):
        vetoes.append("V1 利益冲突标记: %s" % COI_RE.search(text).group(0))
    title = ""
    m = re.search(r"(?m)^#\s+(.+)$", text) or re.search(r"(?m)^(.+)$", text.strip())
    if m:
        title = m.group(1).strip()
    if PROMISE_RE.search(title):
        tt = set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", title.lower()))
        pt = set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", first_para.lower()))
        overlap = len(tt & pt) / max(len(tt), 1)
        if overlap < 0.2:
            vetoes.append("V2 标题承诺与首段断裂(重叠 %.0f%% < 20%%)" % (100 * overlap))
    contra = {}
    for m2 in UNIT_NUM_RE.finditer(text):
        num = re.match(r"\d+(?:\.\d+)?", m2.group(0)).group(0)
        ctx = text[max(0, m2.start() - 15):m2.start()] + "#" + text[m2.end():m2.end() + 15]
        unit_part = re.sub(r"\d+(?:\.\d+)?\s?", "", m2.group(0), count=1)
        key = (unit_part, ctx)
        contra.setdefault(key, set()).add(num)
    for key, nums in contra.items():
        if len(nums) > 1:
            vetoes.append("V3 内部矛盾数字: 同一上下文出现 %s"
                          % " vs ".join(sorted(nums)))
            break
    return {"items": items, "vetoes": vetoes, "words": words, "paras": len(paras),
            "title": title}


def score(result):
    groups = {}
    for g in ("C", "O", "R", "E", "Exp", "Ept", "A", "T"):
        gi = [i for i in result["items"] if i["group"] == g]
        passed = sum(1 for i in gi if i["verdict"] == "pass")
        failed = sum(1 for i in gi if i["verdict"] == "fail")
        groups[g] = (passed, failed,
                     100.0 * passed / (passed + failed) if passed + failed else None)
    geo_groups = [groups[g][2] for g in ("C", "O", "R", "E") if groups[g][2] is not None]
    seo_groups = [groups[g][2] for g in ("Exp", "Ept", "A", "T") if groups[g][2] is not None]
    geo = sum(geo_groups) / len(geo_groups) if geo_groups else None
    seo = sum(seo_groups) / len(seo_groups) if seo_groups else None
    parts = [x for x in (geo, seo) if x is not None]
    total = sum(parts) / len(parts) if parts else None
    capped = False
    if result["vetoes"] and total is not None and total > 59:
        total, capped = 59.0, True
    return {"groups": groups, "geo": geo, "seo": seo, "total": total,
            "capped": capped,
            "band": None if total is None else
            "A(优)" if total >= 80 else "B(良)" if total >= 60 else
            "C(中)" if total >= 40 else "D(差)"}


def render(result, sc):
    L = ["== CORE-EEAT 机械化子集(80 项基准的可机判切片;三态,na 离开分母) =="]
    L.append("词数 %d | 正文段 %d | 标题: %s" % (result["words"], result["paras"],
                                             result["title"][:50] or "(无)"))
    gname = {"C": "C 清晰", "O": "O 组织", "R": "R 可引用", "E": "E 独占",
             "Exp": "Exp 体验", "Ept": "Ept 专业", "A": "A 权威", "T": "T 信任"}
    for g in ("C", "O", "R", "E", "Exp", "Ept", "A", "T"):
        passed, failed, gs = sc["groups"][g]
        L.append("[%s] pass %d / fail %d / na %d → %s"
                 % (gname[g], passed, failed,
                    sum(1 for i in result["items"] if i["group"] == g
                        and i["verdict"] == "not_applicable"),
                    "N/A" if gs is None else "%.0f" % gs))
        for i in result["items"]:
            if i["group"] == g:
                L.append("  %-6.6s %-34.34s %-4.4s %s" % (i["code"], i["name"],
                                                          i["verdict"], i["note"]))
    L.append("GEO = (C+O+R+E)/4 = %s" % ("N/A" if sc["geo"] is None else "%.1f" % sc["geo"]))
    L.append("SEO = (Exp+Ept+A+T)/4 = %s" % ("N/A" if sc["seo"] is None else "%.1f" % sc["seo"]))
    if result["vetoes"]:
        L.append("VETO: ")
        for v in result["vetoes"]:
            L.append("  [X] %s" % v)
    else:
        L.append("VETO: 无(利益冲突/标题断裂/内部矛盾均未命中)")
    if sc["total"] is None:
        L.append("总分 = N/A(无任何可机判项)")
    else:
        L.append("总分 = %.1f → band %s%s"
                 % (sc["total"], sc["band"], "(veto 命中,封顶 59)" if sc["capped"] else ""))
    return "\n".join(L)


GOOD_DOC = """# Best CRM for Small Business 2026

The answer is Acme CRM for most small teams. It costs $29 per seat. It scored 92% in our tests. We tested 12 tools over 3 months.

"TCO" means total cost of ownership. It is the key metric here. We use it below. It matters most for small teams.

## Comparison

| Tool | Price |
| --- | --- |
| Acme | $29 |
| Beta | $49 |

- Fast setup in 10 minutes
- Cheap for teams
- Great support

Our survey of 500 users started in 2026-03. Latency dropped from 320ms to 180ms after switching. Before the switch we used spreadsheets; after, we saved 40%. 我们实测了 5 个场景,转化率提升了 2倍,节省 3.2万元,合计 80% 的团队满意。

![our test lab](https://acme.ai/lab.png)

Acme won the Best SaaS Award 2026. It was featured in TechCrunch. Forbes also mentioned it. Readers voted it first.

About the author: Jane Doe has 10 years in CRM. She has implemented 40+ rollouts. She writes this bio herself. Her email is jane@acme.ai.

See our privacy policy and our terms of service. You can contact us anytime via email. We answer within one business day. Our address is public too.

Padding paragraph one exists for word count purposes. Each sentence stays plain and short. No extra claims are made here. This keeps the density checks honest.

Padding paragraph two also exists for word count purposes. Each sentence stays plain and short. No extra claims are made here. This keeps the density checks honest.

Author: Jane Doe
"""

BAD_DOC = """# 10 个终极方法

今天我们来聊聊早餐吃什么。豆浆和油条是经典搭配。粥品也很不错。包子馅料多种多样。

在方法一里,我们的首屏加载时间实测为 320ms,这是在 2026-03 的测试机上测得的,样本量足够大,结论可靠,没有其他干扰因素,数据全部来自我们的日志系统。

在方法一里,我们的首屏加载时间实测为 280ms,这是在 2026-03 的测试机上测得的,样本量足够大,结论可靠,没有其他干扰因素,数据全部来自我们的日志系统。

本内容由 Acme 赞助。
"""


def _self_test():
    doc = load_document_from_string(GOOD_DOC)
    result = analyze(doc)
    sc = score(result)
    verdicts = {i["code"]: i["verdict"] for i in result["items"]}
    assert verdicts["C1"] == "pass", verdicts           # 首段含数字 29/92
    assert verdicts["C2"] == "not_applicable"
    assert verdicts["C3"] == "pass", verdicts           # "TCO" means
    assert verdicts["C4"] == "pass", verdicts
    assert verdicts["O1"] == "pass" and verdicts["O2"] == "pass"
    assert verdicts["O3"] == "pass", (doc["list_blocks"], result["words"])
    assert verdicts["R1"] == "pass" and verdicts["R2"] == "pass"
    assert verdicts["E1"] == "pass" and verdicts["E2"] == "pass"
    for code in ("Exp1", "Exp2", "Exp3", "Ept1", "Ept2", "A1", "T1", "T2", "T3"):
        assert verdicts[code] == "pass", (code, verdicts)
    assert not result["vetoes"], result["vetoes"]
    assert sc["total"] >= 80, sc["total"]
    assert sc["band"].startswith("A"), sc["band"]

    bad = analyze(load_document_from_string(BAD_DOC))
    bsc = score(bad)
    codes = {v[:2] for v in bad["vetoes"]}
    assert codes == {"V1", "V2", "V3"}, bad["vetoes"]   # 赞助 + 标题断裂 + 320/280 矛盾
    assert bsc["total"] <= 59, bsc                       # veto 之下总分不得高于 59

    # 好文档 + 单一 veto → 高分被封顶到 59
    hybrid = analyze(load_document_from_string(GOOD_DOC + "\n本内容由 Acme 赞助。\n"))
    hsc = score(hybrid)
    assert len(hybrid["vetoes"]) == 1 and hsc["total"] == 59.0 and hsc["capped"], hsc

    # HTML 输入路径
    html = ("<html><body><h1>Only One</h1><p>Answer: 42% of users. Three sentences here. "
            "Yes really. Done.</p><table><tr><td>a</td></tr></table>"
            "<img src='https://x/i.png'></body></html>")
    hdoc = load_document_from_string(html)
    hres = analyze(hdoc)
    assert hdoc["h1"] == 1 and hdoc["tables"] == 1 and hdoc["images"] == 1
    hv = {i["code"]: i["verdict"] for i in hres["items"]}
    assert hv["O1"] == "pass" and hv["O2"] == "pass"
    print("[self-test] PASS core_eeat(好文档全绿 band A;坏文档 3 veto;高分+单 veto 封顶 59;"
          "markdown 与 HTML 双路径)")


def load_document_from_string(raw):
    return load_document(None, None, raw=raw)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?", help="纯文本/markdown/HTML 文件('-' 为 stdin)")
    ap.add_argument("--url", default=None, help="可选:拉取线上页面(需网络)")
    ap.add_argument("--self-test", action="store_true", help="冒烟自测(不联网)")
    args = ap.parse_args(argv)
    if args.self_test:
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL core_eeat")
            return 1
    if not args.file and not args.url:
        ap.error("需要 FILE 或 --url(或 --self-test)")
    try:
        doc = load_document(args.file, args.url)
    except Exception as e:
        print("错误: 无法读取文档: %s" % e, file=sys.stderr)
        return 1
    result = analyze(doc)
    sc = score(result)
    print(render(result, sc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
