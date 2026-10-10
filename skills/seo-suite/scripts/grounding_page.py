#!/usr/bin/env python3
"""品牌实体事实页(Grounding Page)生成器 + 11 条合规检查器(stdlib-only)。

口径:references/content/brand-records.md §六(Rankscale 官方 11 条)、
references/research/borrow-specs.md E7(页结构)与 E5(FAQPage 富结果 2026-05-07 退役)。
输入为 Brand Records 事实库 brand.yaml(受限 YAML 子集,形状契约同 oracle_check.py,
解析器独立实现):顶层 brand + facts 列表,每条
{fact, record, source, date, confidence, keywords?, disambiguation?}。

生成模式(--facts;--name 缺省取 YAML 顶层 brand),11 条逐条落实:
  1  H1=实体名,唯一、不加修饰
  2  首段一句事实定义 "{name} is a {category} that {function}"(中文 facts→中文句式)
  3  Core facts 用 <dl><dt><dd>,不用 table
  4  FAQ 5-10 条:问题化标题(定价/成立/总部/创始人/平台支持…),每条答案含实体名
  5  Volatile facts(定价/客户数/平台支持等易变项)独立区块 + Last reviewed 行
  6  is-NOT 消歧区块(facts 有消歧记录→生成;没有→占位注释提示人工填)
  7  JSON-LD 镜像页面事实:@type 按 --type;sameAs 取 facts 中的权威档案链接;
     FAQPage JSON-LD 不生成(2026-05 退役,注释注明),FAQ 用纯 HTML
  8  hub-and-spoke:facts 含多产品时打印 spoke 候选清单(有独立搜索需求建议拆页,不自动拆)
  9  交叉链接谓词建议以注释输出(spoke→hub 用 isPartOf;hub→spoke 用 hasPart)
  10 复核日期=今天,注释"≤6 个月否则不可信"
  11 URL 简短建议(/about 或 /brand)打印提示

检查模式(--check existing.md):11 条逐条 PASS/FAIL/MANUAL 清单——单 H1/dl 使用/
FAQ 含名率/volatile 区块/JSON-LD 镜像/复核日期年龄为机检,其余 MANUAL;任一 FAIL 退出码 1。

用法:
  python3 grounding_page.py --facts brand.yaml --name "Acme" \
      [--type Organization|SoftwareApplication|Person] [--out grounding-page.md] [--json]
  python3 grounding_page.py --check grounding-page.md [--name "Acme"] [--json]
"""
import argparse
import calendar
import json
import os
import re
import sys
from datetime import date, datetime
from urllib.parse import urlparse

SCHEMA_VERSION = 1
SIX_RECORDS = ("company", "market", "offerings", "audience", "strategy", "execution")
ENTITY_TYPES = ("Organization", "SoftwareApplication", "Person")
REVIEW_MAX_DAYS = 183          # 11 条之 10:页面可见复核日期 ≤6 个月

CONF_MAP = {"high": "high", "med": "med", "medium": "med", "low": "low",
            "高": "high", "中": "med", "低": "low"}
RECORD_PRIORITY = {r: i for i, r in enumerate(SIX_RECORDS)}
RECORD_LABEL_ZH = {"company": "公司", "market": "市场", "offerings": "产品",
                   "audience": "受众", "strategy": "战略", "execution": "运营"}
RECORD_LABEL_EN = {"company": "company", "market": "market", "offerings": "product",
                   "audience": "audience", "strategy": "strategy", "execution": "operations"}

# sameAs 只收权威档案/官方社媒域名(Rankscale 第 7 条;官网本身不算)
SOCIAL_HOSTS = ("wikidata.org", "linkedin.com", "twitter.com", "x.com", "github.com",
                "youtube.com", "facebook.com", "instagram.com", "crunchbase.com",
                "medium.com", "bsky.app", "mastodon", "tiktok.com",
                "weibo.com", "zhihu.com", "bilibili.com")

# ---- 抽取正则(中/英) ----
RE_FOUNDED_ZH = re.compile(r"(?:成立|创办)于\s*((?:19|20)\d{2})\s*年?")
RE_FOUNDED_EN = re.compile(r"founded in ((?:19|20)\d{2})", re.I)
RE_HQ_ZH = re.compile(r"总部(?:位于|在)([^,。;、]+)")
RE_HQ_EN = re.compile(r"(?:headquartered|based) in ([^,.;]+)", re.I)
RE_CATEGORY_ZH = re.compile(r"类目是([^,。;]+)")
RE_CATEGORY_EN = re.compile(r"categor(?:y|ies) (?:is|are) ([^,.;]+)", re.I)
RE_ISA_ZH = re.compile(r"是一家([^,。;]+)")
RE_ISA_EN = re.compile(r"\bis\s+an?\s+([^,.;]+)", re.I)
RE_FOUNDER_ZH = re.compile(r"创始人(?:是|为)([^,。;]+)")
RE_FOUNDER_EN = re.compile(r"founded by ([^,.;]+)", re.I)
RE_COMPET_ZH = re.compile(r"主要竞对(?:是|为)([^,。;]+)")
RE_COMPET_EN = re.compile(r"competitors?\s+(?:are|is|include[sd]?)[:\s]+([^,.;]+)", re.I)
RE_AUDIENCE_ZH = re.compile(r"首要客户画像[:：]\s*([^,。;]+)")
RE_AUDIENCE_EN = re.compile(r"primary audience[:\s]+([^,.;]+)", re.I)
RE_LINEUP_ZH = re.compile(r"产品线[^:：]*[:：]\s*([^;。]+)")
RE_LINEUP_EN = re.compile(r"(?:product lineup|product line|plans?\s+(?:are|include))[:：]?\s*(.+?)[.;]", re.I)
RE_DIFF_ZH = re.compile(r"差异化是[“\"]?([^”\",。;]+)")
RE_DIFF_EN = re.compile(r"differentiat\w*\s+(?:is|by)\s+([^,.;]+)", re.I)
RE_FUNC_EN = re.compile(r"\b(help|enable|let|allow)s?\s+(.+?)[.;]", re.I)

# 易变事实(第 5 条):定价/客户数/平台支持/版本/路线图等
VOLATILE_RE = re.compile(
    r"价格|定价|费用|收费|免费|付费|优惠|\$[0-9]|€[0-9]|£[0-9]|¥[0-9]|/月|每月|per month|per user"
    r"|\b(?:price|pricing|cost|fee|paid|free)\b"
    r"|客户数|用户数|订阅数|订阅者|\b(?:customers?|users?|subscribers?)\b"
    r"|平台|支持|集成|插件|\b(?:integrat\w*|plugins?|platforms?|supports?)\b"
    r"|版本|\b(?:versions?|releases?)\b"
    r"|即将发布|路线图|优先级|\b(?:roadmap|coming soon|priority)\b", re.I)
VOLATILE_LABELS = [
    (re.compile(r"价格|定价|费用|收费|免费|付费|\$|/月|每月|\b(?:price|pricing|cost|fee|paid)\b", re.I),
     "定价", "Pricing"),
    (re.compile(r"客户数|用户数|订阅数|\b(?:customers?|users?|subscribers?)\b", re.I),
     "客户数", "Customers"),
    (re.compile(r"即将发布|路线图|优先级|\b(?:roadmap|coming soon|priority)\b", re.I),
     "路线图", "Roadmap"),
    (re.compile(r"版本|\b(?:versions?|releases?)\b", re.I), "版本", "Versions"),
    (re.compile(r"产品线|产品组合|\b(?:lineup|plans?)\b", re.I), "产品线", "Product lineup"),
    (re.compile(r"平台|支持|集成|插件|\b(?:integrat\w*|plugins?|platforms?|supports?)\b", re.I),
     "平台与功能", "Platforms & features"),
]
# 政策/流程类表述(never-do、审批链、claims 白黑名单)不是易变事实值,即使提及价格词
POLICY_RE = re.compile(r"从不|不做的事|审批|可以宣称|不能宣称|白名单|黑名单|never-?do|approval", re.I)
VOLATILE_Q_ZH = {"定价": "%s 的定价是多少?", "客户数": "%s 有多少客户?",
                 "平台与功能": "%s 支持哪些平台与功能?", "版本": "%s 的最新版本是什么?",
                 "路线图": "%s 即将发布什么?"}
VOLATILE_Q_EN = {"Pricing": "How much does %s cost?", "Customers": "How many customers does %s have?",
                 "Platforms & features": "What platforms does %s support?",
                 "Versions": "What is the latest version of %s?",
                 "Roadmap": "What is %s releasing next?"}

DISAMBIG_MARKER_RE = re.compile(r"消歧|同名不同实体|disambiguation", re.I)
LD_JSON_RE = re.compile(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)


# ---------- YAML 受限子集解析(形状契约同 oracle_check.py;独立实现) ----------

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
    顶层 `brand:`;`facts:` 列表,每条 `- fact:` 起行,其余键缩进续行;
    行内列表用 [a, b];不用锚点/多行块/嵌套。"""
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
            warnings.append("第 %d 条 record=%r 不在六记录内(按原样保留)" % (i, record or "(缺)"))
        out.append({"fact": fact_text, "record": record,
                    "source": str(d.get("source", "")).strip(),
                    "date": str(d.get("date", "")).strip(),
                    "confidence": CONF_MAP.get(str(d.get("confidence", "")).strip().lower(), ""),
                    "disambiguation": str(d.get("disambiguation", "")).strip().lower()})
    return brand, out, warnings


# ---------- 语言检测与事实抽取 ----------

def detect_language(facts):
    """中/英句式选择:URL 与数字不参与;CJK 字数 vs 拉丁词数(品牌名/产品名不至翻转判定)。"""
    text = re.sub(r"https?://\S+", " ", " ".join(f["fact"] for f in facts))
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    lat = len(re.findall(r"[A-Za-z]+", text))
    return "zh" if cjk >= lat else "en"


def _find(pattern, texts):
    for t in texts:
        m = pattern.search(t)
        if m:
            return m.group(1).strip()
    return None


def _zspace(prefix, value):
    """中英混排补空格:前缀末字符为 CJK、值首字符为拉丁/数字时加一空格。"""
    if prefix and value and re.search(r"[\u4e00-\u9fff]$", prefix) \
            and re.match(r"[A-Za-z0-9$@]", value):
        return prefix + " " + value
    return prefix + value


def _add_months(d, n):
    y, m = d.year + (d.month - 1 + n) // 12, (d.month - 1 + n) % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def extract_sameas(facts):
    """sameAs:facts(source+正文)中的权威档案/官方社媒链接,去重保序。"""
    urls, seen = [], set()
    for f in facts:
        for u in re.findall(r"https?://[^\s)】\]]+", f["source"] + " " + f["fact"]):
            u = u.rstrip(".,;。")
            host = urlparse(u).netloc.lower()
            if any(h in host for h in SOCIAL_HOSTS) and u not in seen:
                seen.add(u)
                urls.append(u)
    return urls


def extract_is_not(facts, name):
    """is-NOT 消歧:显式 disambiguation 键 / “消歧·同名不同实体”标记 /
    “{实体} 不是 {另一实体}”句式(目标须像另一实体,避免把定位句误当消歧)。"""
    items, seen = [], set()
    nlow = name.lower()

    def _add(s):
        if s and s not in seen:
            seen.add(s)
            items.append(s)

    for f in facts:
        text = f["fact"]
        if f.get("disambiguation") in ("true", "yes", "1") or DISAMBIG_MARKER_RE.search(text):
            _add(re.sub(r"^消歧\s*[:：]\s*", "", text).strip())
            continue
        for m in re.finditer(re.escape(name) + r"\s*(?:不是|is not|isn'?t)\s*([^,。;]+)", text, re.I):
            tgt = m.group(1).strip()
            low = tgt.lower()
            if not tgt or low == nlow:
                continue
            looks_entity = (low.startswith(nlow) and len(low) > len(nlow)) \
                or re.match(r"[A-Z][A-Za-z0-9]*\s+[A-Z]", tgt) \
                or re.match(r"[\u4e00-\u9fff]{2,}(?:公司|集团|科技|实验室|工作室)", tgt)
            if looks_entity:
                _add("%s 不是 %s——同名不同实体" % (name, tgt))
    return items


def extract_products(lineup, zh):
    if not lineup:
        return []
    parts = re.split(r"[、,,/]|\s+与\s+|\s+和\s+", lineup) if zh else re.split(r",|\s+and\s+", lineup)
    out = []
    for p in parts:
        p = p.strip(" 。.;“”\"'")
        if p:
            out.append(p)
    return out


def generate(facts, name, etype, today):
    """从 facts 抽实体事实并组装 grounding page 的全部构件。"""
    lang = detect_language(facts)
    zh = lang == "zh"
    ordered = sorted(facts, key=lambda f: RECORD_PRIORITY.get(f["record"], 9))
    otexts = [f["fact"] for f in ordered]
    warnings = []

    # ---- 2 首段一句事实定义 ----
    isa = _find(RE_ISA_ZH, otexts) if zh else _find(RE_ISA_EN, otexts)
    cat = _find(RE_CATEGORY_ZH, otexts) if zh else _find(RE_CATEGORY_EN, otexts)
    diff = _find(RE_DIFF_ZH, otexts) if zh else _find(RE_DIFF_EN, otexts)
    hq = _find(RE_HQ_ZH, otexts) if zh else _find(RE_HQ_EN, otexts)
    func = None
    if zh:
        if diff:
            func = "以%s为差异化" % diff
        elif hq:
            func = "总部位于%s" % hq
    else:
        if diff:
            func = "is differentiated by %s" % diff
        else:
            for t in otexts:
                m = RE_FUNC_EN.search(t)
                if m:
                    func = "%s %s" % (m.group(1).lower(), m.group(2))
                    break
        if not func and hq:
            func = "is headquartered in %s" % hq
    base = isa or cat
    if not base:
        lead = "%s 是一家公司(类目待补)。" % name if zh else "%s is a company (category TBD)." % name
        warnings.append("未抽到类目(“是一家…”/“类目是…”):首段定义降级,走缺口协议补 Company/Market 记录")
    elif zh:
        lead = "%s 是一家%s%s。" % (name, base, ",%s" % func if func else "")
    else:
        lead = "%s is a %s%s." % (name, base, " that %s" % func if func else "")
    if not func:
        warnings.append("未抽到差异点(“差异化是…”/“differentiator”):首段缺可验证差异点")

    # ---- 3 Core facts(dl) ----
    founded = _find(RE_FOUNDED_ZH, otexts) or _find(RE_FOUNDED_EN, otexts)
    founder = _find(RE_FOUNDER_ZH, otexts) or _find(RE_FOUNDER_EN, otexts)
    compet = _find(RE_COMPET_ZH, otexts) or _find(RE_COMPET_EN, otexts)
    aud = _find(RE_AUDIENCE_ZH, otexts) or _find(RE_AUDIENCE_EN, otexts)
    lineup = _find(RE_LINEUP_ZH, otexts) or _find(RE_LINEUP_EN, otexts)
    core = []
    if cat or isa:
        core.append(("类目" if zh else "Category", cat or isa))
    if founded:
        core.append(("成立" if zh else "Founded", "%s 年" % founded if zh else founded))
    if hq:
        core.append(("总部" if zh else "Headquarters", hq))
    if founder:
        core.append(("创始人" if zh else "Founders", founder))
    if compet:
        core.append(("主要竞对" if zh else "Main competitors", compet))
    if aud:
        core.append(("首要客户" if zh else "Primary audience", aud))
    if lineup:
        core.append(("产品线" if zh else "Product lineup", lineup))

    # ---- 5 Volatile facts 独立区块 ----
    volatile = []
    for f in facts:
        if not VOLATILE_RE.search(f["fact"]) or POLICY_RE.search(f["fact"]):
            continue
        label = "易变事实" if zh else "Volatile"
        for pat, zh_l, en_l in VOLATILE_LABELS:
            if pat.search(f["fact"]):
                label = zh_l if zh else en_l
                break
        volatile.append({"label": label, "fact": f["fact"], "date": f["date"],
                         "source": f["source"]})
    vdates = []
    for v in volatile:
        try:
            vdates.append(datetime.strptime(v["date"], "%Y-%m-%d").date())
        except ValueError:
            pass
    last_reviewed = str(max(vdates)) if vdates else str(today)

    # ---- 6 is-NOT ----
    is_not_items = extract_is_not(facts, name)
    if not is_not_items:
        warnings.append("facts 中未找到消歧记录:is-NOT 区块为占位,需人工填写常见混淆实体")

    # ---- 7 sameAs / JSON-LD ----
    sameas = extract_sameas(facts)
    if not sameas:
        warnings.append("facts 中未发现权威档案链接(Wikidata/LinkedIn/官方社媒):sameAs 为空,人工补充")
    jsonld = {"@context": "https://schema.org", "@type": etype,
              "name": name, "description": lead}
    if founded and etype != "Person":
        jsonld["foundingDate"] = founded      # 只镜像页面可见事实(Core facts dl 中的成立年份)
    jsonld["sameAs"] = sameas

    # ---- 4 FAQ(每答含实体名) ----
    faq = []
    used_q = set()

    def _add_faq(q, a):
        if q in used_q:
            return False                        # 同一问题不重复(多事实同标签→答案并入区块)
        if name not in a:
            a = "%s:%s" % (name, a)           # 兜底:答案独立成句也必含实体名
        used_q.add(q)
        faq.append({"question": q, "answer": a.rstrip("。.;") + ("。" if zh else ".")})
        return True

    if zh:
        if cat or isa:
            _add_faq("%s 是做什么的?" % name,
                     _zspace("%s 所在类目是" % name, (cat or isa).rstrip("。")))
        if founded:
            _add_faq("%s 是哪一年成立的?" % name, "%s 成立于 %s 年" % (name, founded))
        if hq:
            _add_faq("%s 的总部在哪里?" % name, _zspace("%s 的总部位于" % name, hq))
        if founder:
            _add_faq("%s 的创始人是谁?" % name, _zspace("%s 的创始人是" % name, founder))
        if lineup:
            _add_faq("%s 有哪些产品线?" % name, _zspace("%s 的产品线:" % name, lineup))
        if compet:
            _add_faq("%s 的主要竞品有哪些?" % name, _zspace("%s 的主要竞对是" % name, compet))
        if aud:
            _add_faq("%s 适合什么样的客户?" % name, _zspace("%s 的首要客户画像:" % name, aud))
        for v in volatile:
            qtpl = VOLATILE_Q_ZH.get(v["label"])
            q = qtpl % name if qtpl else "%s 的%s情况如何?" % (name, v["label"])
            if not _add_faq(q, v["fact"]):     # 同标签已问过→换通用问法
                _add_faq("%s 的%s情况如何?" % (name, v["label"]), v["fact"])
    else:
        if cat or isa:
            _add_faq("What does %s do?" % name,
                     "%s operates in the %s category" % (name, (cat or isa).rstrip(".")))
        if founded:
            _add_faq("When was %s founded?" % name, "%s was founded in %s" % (name, founded))
        if hq:
            _add_faq("Where is %s headquartered?" % name, "%s is headquartered in %s" % (name, hq))
        if founder:
            _add_faq("Who founded %s?" % name, "%s was founded by %s" % (name, founder))
        if lineup:
            _add_faq("What products does %s offer?" % name, "%s offers %s" % (name, lineup))
        if compet:
            _add_faq("Who are %s's main competitors?" % name,
                     "%s's main competitors are %s" % (name, compet))
        if aud:
            _add_faq("Who is %s for?" % name, "%s's primary audience: %s" % (name, aud))
        for v in volatile:
            qtpl = VOLATILE_Q_EN.get(v["label"])
            q = qtpl % name if qtpl else "What about %s's %s?" % (name, v["label"])
            if not _add_faq(q, v["fact"]):
                _add_faq("What about %s's %s?" % (name, v["label"]), v["fact"])
    if len(faq) < 5:                          # 不足 5 条→按记录补通用问题
        for f in ordered:
            if len(faq) >= 5:
                break
            if VOLATILE_RE.search(f["fact"]) or DISAMBIG_MARKER_RE.search(f["fact"]):
                continue
            if any(f["fact"] in item["answer"] for item in faq):
                continue
            rec = f["record"] if f["record"] in SIX_RECORDS else "company"
            if zh:
                _add_faq({"company": "%s 是一家什么公司?", "market": "%s 的市场定位是什么?",
                          "offerings": "%s 提供哪些产品与服务?", "audience": "%s 服务于哪些客户?",
                          "strategy": "%s 当前的发展重点是什么?",
                          "execution": "%s 的运营方式是怎样的?"}[rec] % name, f["fact"])
            else:
                _add_faq({"company": "What kind of company is %s?",
                          "market": "What is %s's market positioning?",
                          "offerings": "What does %s offer?",
                          "audience": "Who does %s serve?",
                          "strategy": "What is %s focusing on?",
                          "execution": "How does %s operate?"}[rec] % name, f["fact"])
    faq = faq[:10]                            # 上限 10 条
    if len(faq) < 5:
        warnings.append("FAQ 仅 %d 条(<5):facts 不足,走缺口协议补齐后重生成" % len(faq))

    # ---- 8 hub-and-spoke 候选 ----
    products = extract_products(lineup, zh)

    return {"name": name, "etype": etype, "lang": lang, "zh": zh,
            "generated": datetime.now().isoformat(timespec="seconds"),
            "today": str(today), "review_expiry": str(_add_months(today, 6)),
            "lead": lead, "core": core, "volatile": volatile,
            "last_reviewed": last_reviewed, "is_not": is_not_items,
            "sameas": sameas, "jsonld": jsonld, "faq": faq, "products": products,
            "facts": facts, "warnings": warnings}


# ---------- 页面渲染 ----------

def render_page(g):
    name, zh = g["name"], g["zh"]
    lbl = RECORD_LABEL_ZH if zh else RECORD_LABEL_EN
    L = []
    L.append("<!-- grounding page:由 scripts/grounding_page.py 生成;%s;生成时间 %s -->"
             % ("facts 源见文末 Sources", g["generated"]))
    L.append("<!-- 不生成 FAQPage JSON-LD:Google 2026-05-07 起全站退役"
             "(references/research/borrow-specs.md E5);FAQ 用下方纯 HTML 呈现 -->")
    # 9 交叉链接谓词建议(注释形式)
    L.append("<!-- 交叉链接谓词建议:spoke 页→本 hub 页用 isPartOf;本 hub 页→spoke 页用 hasPart;"
             "锚文本须说明关系(如“%s 的定价页”),不用裸 “read more” -->" % name)
    L.append("")
    L.append("# %s" % name)                                   # 1 H1=实体名
    L.append("")
    L.append(g["lead"])                                       # 2 首段一句定义
    L.append("")
    L.append("Entity type: %s · Status: verified · Updated: %s" % (g["etype"], g["today"]))
    L.append("")
    L.append("## Core facts%s" % ("(稳定事实)" if zh else " (stable facts)"))
    L.append("")
    if g["core"]:
        L.append("<dl>")                                      # 3 dl,不用 table
        for dt, dd in g["core"]:
            L.append("  <dt>%s</dt><dd>%s</dd>" % (dt, dd))
        L.append("</dl>")
    else:
        L.append("<!-- [人工填写] 未抽到稳定事实:请补 Company/Market 记录后重生成 -->")
    L.append("")
    # 5 Volatile 独立区块
    L.append('<section id="volatile">')
    L.append("<h2>易变事实(定价/客户数/平台与功能…)</h2>" if zh
             else "<h2>Volatile facts (pricing/customers/platforms…)</h2>")
    L.append("<p>Last reviewed: %s</p>" % g["last_reviewed"])
    if g["volatile"]:
        L.append("<dl>")
        for v in g["volatile"]:
            L.append("  <dt>%s</dt><dd>%s(%s 复核)</dd>" % (v["label"], v["fact"], v["date"] or "?"))
        L.append("</dl>")
    else:
        L.append("<!-- [人工填写] 未检出易变事实;若实体有定价/版本/平台项,单独维护于此区块 -->")
    L.append("</section>")
    L.append("")
    # 6 is-NOT 消歧
    L.append('<section id="is-not">')
    L.append("<h2>%s 不是</h2>" % name if zh else "<h2>%s is NOT</h2>" % name)
    if g["is_not"]:
        L.append("<ul>")
        for item in g["is_not"]:
            L.append("  <li>%s</li>" % item)
        L.append("</ul>")
    else:
        L.append("<!-- [人工填写] facts 中未找到消歧记录(“%s 不是 …”或含“消歧/同名不同实体”的 fact):"
                 "请列出常见混淆实体,如“%s 不是 {另一同名实体}(不同行业/地区的另一实体)”。 -->" % (name, name))
    L.append("</section>")
    L.append("")
    # 4 FAQ:纯 HTML,无 FAQPage JSON-LD
    L.append('<section id="faq">')
    L.append("<h2>常见问题</h2>" if zh else "<h2>FAQ</h2>")
    for item in g["faq"]:
        L.append("<p><strong>%s</strong> %s</p>" % (item["question"], item["answer"]))
    L.append("</section>")
    L.append("")
    # Sources(谓词式锚文本)
    L.append("## Sources%s" % ("(事实出处)" if zh else " (fact sources)"))
    L.append("")
    seen_src = {}
    for f in g["facts"]:
        src = f["source"]
        if src and src not in seen_src:
            seen_src[src] = f["record"] if f["record"] in SIX_RECORDS else "company"
    for src, rec in seen_src.items():
        label = "%s 的%s事实出处" % (name, lbl[rec]) if zh else "%s %s fact source" % (name, lbl[rec])
        if re.match(r"https?://", src):
            L.append("- [%s](%s)" % (label, src))
        else:
            L.append("- %s —— %s(内部文档,人工溯源)" % (label, src))
    L.append("")
    # 10 review date=今天 + ≤6 个月注释
    L.append("最后复核:%s · Status: verified · Entity type: %s" % (g["today"], g["etype"])
             if zh else "Last reviewed: %s · Status: verified · Entity type: %s" % (g["today"], g["etype"]))
    L.append("<!-- 复核日期须 ≤6 个月,超期页面不可信(先复核再谈 AI 可见性);本页复核到期日:%s -->"
             % g["review_expiry"])
    L.append("")
    # 7 JSON-LD 镜像页面事实
    L.append('<script type="application/ld+json">')
    L.append(json.dumps(g["jsonld"], ensure_ascii=False))
    L.append("</script>")
    if not g["sameas"]:
        L.append("<!-- [人工填写] sameAs 为空:补充 Wikidata/LinkedIn/官方社媒等权威档案 URL"
                 "(必须真实档案,不得用官网首页或占位符) -->")
    return "\n".join(L) + "\n"


def build_hints(g):
    """8/11 两条打印提示(不写进页面)。"""
    hints = []
    if len(g["products"]) >= 2:
        hints.append("[提示] hub-and-spoke:检测到 %d 个产品,以下若有独立搜索需求,"
                     "建议拆独立 spoke 页(本实体页保持 hub,不自动拆):" % len(g["products"]))
        for p in g["products"]:
            hints.append("  - %s" % p)
        hints.append("  (拆分后交叉链接:spoke→hub 用 isPartOf,hub→spoke 用 hasPart,见页内注释)")
    elif g["products"]:
        hints.append("[提示] 仅检测到 1 个产品(%s):暂无 spoke 拆分必要" % g["products"][0])
    slug = re.sub(r"\s+", "-", g["name"].strip().lower())
    hints.append("[提示] URL 简短:实体名 slug、无参数、无深层级"
                 "(建议 /about 或 /brand 这类一级路径;本实体如 /%s)" % slug)
    return hints


# ---------- 检查模式(--check) ----------

CHECK_ITEMS = [
    (1, "H1 唯一且=实体名"), (2, "首段一句事实定义"), (3, "Core facts 用 dl 不用 table"),
    (4, "FAQ 5-10 条且每答含实体名"), (5, "Volatile 独立区块+Last reviewed"),
    (6, "is-NOT 消歧区块"), (7, "JSON-LD 镜像且无 FAQPage"), (8, "hub-and-spoke 拆分"),
    (9, "交叉链接谓词"), (10, "复核日期 ≤6 个月"), (11, "URL 简短"),
]


def _strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def _heading_span(text, pattern):
    """以标题(## …)起始的区块:到下一标题为止。"""
    h = re.search(pattern, text, re.M)
    if not h:
        return None
    rest = text[h.end():]
    nxt = re.search(r"^#{1,3} ", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def _faq_pairs(text):
    """FAQ QA 对:(strong 问题, 纯文本答案)。"""
    m = re.search(r'<section id="faq"[^>]*>(.*?)</section>', text, re.S | re.I)
    if m:
        sec = m.group(1)
    else:
        sec = _heading_span(text, r"^#{1,3}[^\n]*(?:常见问题|FAQ)[^\n]*$", )
        if sec is None:
            return None
    pairs = []
    for p in re.finditer(r"<p>(.*?)</p>", sec, re.S):
        q = re.search(r"<strong>(.*?)</strong>", p.group(1), re.S)
        if not q:
            continue
        a = _strip_tags(p.group(1)[q.end():]).strip()
        pairs.append((_strip_tags(q.group(1)).strip(), a))
    return pairs


def check_page(text, name_hint, today):
    """11 条逐条机检:PASS / FAIL / MANUAL。返回 checks 列表。"""
    lines = text.splitlines()
    checks = []

    def add(no, status, detail):
        checks.append({"no": no, "item": CHECK_ITEMS[no - 1][1],
                       "status": status, "detail": detail})

    # 1 H1
    h1s = [l[2:].strip() for l in lines if re.match(r"^# ", l)]
    name = name_hint or (h1s[0] if len(h1s) == 1 else "")
    if len(h1s) != 1:
        add(1, "FAIL", "H1 数量=%d(须唯一)" % len(h1s))
    elif name_hint and h1s[0] != name_hint:
        add(1, "FAIL", "H1=%r 与实体名 %r 不符(H1 须=实体名,不加修饰)" % (h1s[0], name_hint))
    else:
        add(1, "PASS", "H1=%r" % h1s[0])

    # 2 首段一句定义
    lead = None
    started = False
    for l in lines:
        if re.match(r"^# ", l):
            started = True
            continue
        if not started or not l.strip() or l.lstrip().startswith("<!--") or l.startswith("#"):
            continue
        lead = l.strip()
        break
    if not lead:
        add(2, "FAIL", "H1 后未找到首段")
    else:
        sents = re.findall(r"[。.!?](?=\s|$)", lead)
        if name and name in lead and len(sents) == 1 and len(lead) <= 300:
            add(2, "PASS", "一句定义含实体名:%s…" % lead[:50])
        else:
            why = []
            if name and name not in lead:
                why.append("未含实体名")
            if len(sents) != 1:
                why.append("非单句(%d 个句末标点)" % len(sents))
            add(2, "FAIL", "首段须为一句含实体名的事实定义;" + ";".join(why or ["格式异常"]))

    # 3 dl 不用 table
    low = text.lower()
    ndt = len(re.findall(r"<dt>", low))
    if ndt >= 1 and "<table" not in low:
        add(3, "PASS", "<dt>×%d,无 <table>" % ndt)
    else:
        why = []
        if ndt < 1:
            why.append("未检出 <dl>/<dt>")
        if "<table" in low:
            why.append("含 <table>(Core facts 不得用表格)")
        add(3, "FAIL", ";".join(why))

    # 4 FAQ
    pairs = _faq_pairs(text)
    if not pairs:
        add(4, "FAIL", "未找到 FAQ 区块(section id=faq 或 常见问题/FAQ 标题)")
    elif not (5 <= len(pairs) <= 10):
        add(4, "FAIL", "FAQ %d 条,不在 5-10 区间" % len(pairs))
    elif not name:
        add(4, "MANUAL", "缺实体名(--name/H1),无法校验含名率")
    else:
        hit = sum(1 for _, a in pairs if name in a)
        if hit == len(pairs):
            add(4, "PASS", "%d 条,含名率 %d/%d(每个答案含实体名)" % (len(pairs), hit, len(pairs)))
        else:
            add(4, "FAIL", "含名率 %d/%d(每个答案须独立成句且含实体名)" % (hit, len(pairs)))

    # 5 volatile
    mv = re.search(r'<section id="volatile"[^>]*>(.*?)</section>', text, re.S | re.I)
    vsec = mv.group(1) if mv else _heading_span(text, r"^#{1,3}[^\n]*(?:易变|volatile)", )
    if vsec is None:
        add(5, "FAIL", "缺 volatile 区块(易变事实须与稳定事实分开)")
    elif not re.search(r"Last reviewed\s*[:：]", vsec):
        add(5, "FAIL", "volatile 区块缺 Last reviewed 行")
    else:
        add(5, "PASS", "独立区块 + Last reviewed 行在场")

    # 6 is-NOT
    mn = re.search(r'<section id="is-not"[^>]*>(.*?)</section>', text, re.S | re.I)
    nsec = mn.group(1) if mn else _heading_span(
        text, r"^#{1,3}[^\n]*(?:不是|is not|is-not)", )
    if nsec is None:
        add(6, "FAIL", "缺 is-NOT 消歧区块")
    elif "人工填写" in nsec:
        add(6, "PASS", "区块在场(占位注释待人工填混淆实体)")
    else:
        add(6, "PASS", "消歧条目在场")

    # 7 JSON-LD 镜像 + 无 FAQPage
    lds = LD_JSON_RE.findall(text)
    if not lds:
        add(7, "FAIL", "未见 JSON-LD(script application/ld+json)")
    else:
        reasons, parsed = [], []
        for raw in lds:
            try:
                obj = json.loads(raw)
            except ValueError:
                reasons.append("JSON-LD 解析失败")
                continue
            parsed.append(obj)
            if "FAQPage" in str(obj.get("@type", "")):
                reasons.append("JSON-LD @type=FAQPage(2026-05-07 退役,不生成)")
        if parsed:
            main_obj = parsed[0]
            if name and main_obj.get("name") != name:
                reasons.append("JSON-LD name=%r 与实体名 %r 不符" % (main_obj.get("name"), name))
            visible = _strip_tags(re.sub(r"<script.*?</script>", "", text, flags=re.S))
            for k, v in main_obj.items():
                if k in ("@context", "@type", "sameAs") or not isinstance(v, str) or not v:
                    continue
                if v not in visible:
                    reasons.append("镜像违规:%s=%r 不在页面可见内容中(不得添加页面没有的事实)"
                                   % (k, v[:40]))
        add(7, "FAIL" if reasons else "PASS",
            ";".join(reasons) if reasons
            else "@type=%s,name/sameAs 与页面事实镜像一致" % parsed[0].get("@type"))

    # 8 hub-and-spoke(需人工判断独立搜索需求)
    add(8, "MANUAL", "哪些产品有独立搜索需求需人工判断;多产品时拆 spoke 页,本页保持 hub")

    # 9 交叉链接谓词
    if re.search(r"isPartOf", text) and re.search(r"hasPart", text):
        add(9, "PASS", "isPartOf/hasPart 谓词建议在场")
    else:
        add(9, "MANUAL", "未见谓词建议(spoke→hub isPartOf;hub→spoke hasPart;锚文本说明关系)")

    # 10 复核日期年龄(取最后一次出现:页面级复核行在页脚,先于 volatile 区块的行)
    dates = re.findall(r"(?:最后复核|Last reviewed)\s*[:：]\s*(\d{4}-\d{2}-\d{2})", text)
    if not dates:
        add(10, "FAIL", "未见页面可见复核日期(最后复核:/Last reviewed:)")
    else:
        dstr = dates[-1]
        try:
            d = date(*(int(x) for x in dstr.split("-")))
        except ValueError:
            add(10, "FAIL", "复核日期 %s 无法解析" % dstr)
            d = None
        if d:
            age = (today - d).days
            if age <= REVIEW_MAX_DAYS:
                add(10, "PASS", "%s(距今 %d 天 ≤ %d)" % (dstr, age, REVIEW_MAX_DAYS))
            else:
                add(10, "FAIL", "%s 距今 %d 天 > %d(≤6 个月,否则不可信,先复核)"
                    % (dstr, age, REVIEW_MAX_DAYS))

    # 11 URL(文件内容无法判定)
    add(11, "MANUAL", "URL 无法从页面内容判定;须实体名 slug、无参数、无深层级(/about 或 /brand)")
    return checks


def render_check(checks, path):
    n_pass = sum(1 for c in checks if c["status"] == "PASS")
    n_fail = sum(1 for c in checks if c["status"] == "FAIL")
    n_man = sum(1 for c in checks if c["status"] == "MANUAL")
    L = ["[i] grounding page 合规检查(Rankscale 11 条): %s" % path, ""]
    for c in checks:
        L.append("[%s] %02d %s: %s" % (c["status"], c["no"], c["item"], c["detail"]))
    L.append("")
    L.append("汇总: PASS %d / FAIL %d / MANUAL %d → %s"
             % (n_pass, n_fail, n_man,
                "机检全部通过(MANUAL 项需人工确认)" if n_fail == 0 else "存在不合规项"))
    return "\n".join(L), n_fail


# ---------- main ----------

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="grounding_page.py",
        description="品牌实体事实页(Grounding Page)生成器 + 11 条合规检查器"
                    "(Rankscale 口径,输入为 Brand Records brand.yaml)",
        epilog="示例:\n"
               "  grounding_page.py --facts brand.yaml --name \"Acme\" --out grounding-page.md\n"
               "  grounding_page.py --facts brand.yaml --name \"Acme\" --type SoftwareApplication --json\n"
               "  grounding_page.py --check grounding-page.md --name \"Acme\"",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--facts", help="brand.yaml:Brand Records 受限 YAML 子集"
                    "(references/content/brand-records.md;生成模式必需)")
    ap.add_argument("--name", help="实体名(缺省取 YAML 顶层 brand;H1 与 JSON-LD name 用)")
    ap.add_argument("--type", choices=ENTITY_TYPES, default="Organization",
                    help="JSON-LD @type(默认 Organization)")
    ap.add_argument("--out", help="生成页写出路径(缺省打印到 stdout)")
    ap.add_argument("--check", metavar="EXISTING_MD",
                    help="检查既有 grounding page 的 11 条合规性,输出 PASS/FAIL/MANUAL 清单")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON(生成产物或检查清单)")
    args = ap.parse_args(argv)

    today = date.today()

    if args.check:                                     # ---- 检查模式 ----
        try:
            with open(args.check, encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            print("错误: 无法读取 %s: %s" % (args.check, e), file=sys.stderr)
            return 1
        checks = check_page(text, args.name, today)
        if args.json:
            n_fail = sum(1 for c in checks if c["status"] == "FAIL")
            print(json.dumps({"schema_version": SCHEMA_VERSION, "mode": "check",
                              "file": args.check,
                              "generated": datetime.now().isoformat(timespec="seconds"),
                              "name": args.name, "checks": checks,
                              "pass_count": sum(1 for c in checks if c["status"] == "PASS"),
                              "fail_count": n_fail,
                              "manual_count": sum(1 for c in checks if c["status"] == "MANUAL"),
                              "ok": n_fail == 0}, ensure_ascii=False, indent=2))
            return 1 if n_fail else 0
        report, n_fail = render_check(checks, args.check)
        print(report)
        return 1 if n_fail else 0

    # ---- 生成模式 ----
    if not args.facts:
        ap.error("--facts 为生成模式必需(或改用 --check 检查既有页面)")
    try:
        brand, facts, warnings = parse_facts_yaml(args.facts)
    except (OSError, ValueError) as e:
        print("错误: 无法解析 facts: %s" % e, file=sys.stderr)
        return 1
    name = args.name or brand
    if not name:
        print("错误: 缺实体名(--name 或 YAML 顶层 brand)", file=sys.stderr)
        return 1

    g = generate(facts, name, args.type, today)
    page = render_page(g)
    for w in warnings + g["warnings"]:
        print("[!] %s" % w, file=sys.stderr)
    for h in build_hints(g):
        print(h, file=sys.stderr)

    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(page)
        except OSError as e:
            print("错误: 无法写 %s: %s" % (args.out, e), file=sys.stderr)
            return 1
        print("[i] 已写入: %s" % args.out, file=sys.stderr)

    if args.json:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "mode": "generate",
                          "generated": g["generated"],
                          "entity": {"name": g["name"], "type": g["etype"], "language": g["lang"]},
                          "review_date": g["today"], "review_expiry": g["review_expiry"],
                          "lead_definition": g["lead"],
                          "core_facts": [{"dt": dt, "dd": dd} for dt, dd in g["core"]],
                          "volatile_facts": [{"dt": v["label"], "dd": v["fact"],
                                              "date": v["date"], "source": v["source"]}
                                             for v in g["volatile"]],
                          "volatile_last_reviewed": g["last_reviewed"],
                          "faq": g["faq"],
                          "is_not": {"found": bool(g["is_not"]), "items": g["is_not"]},
                          "sameas": g["sameas"], "jsonld": g["jsonld"],
                          "faqpage_jsonld": "not_generated (retired 2026-05-07)",
                          "spoke_candidates": g["products"],
                          "hints": build_hints(g),
                          "warnings": warnings + g["warnings"],
                          "markdown": page}, ensure_ascii=False, indent=2))
    elif not args.out:
        sys.stdout.write(page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
