#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""content_score.py — 透明内容评分器(MarketMuse 话题公式 + Surfer 双轨,stdlib,standalone).

用法:
  python3 content_score.py --draft draft.md --competitors c1.md,c2.md,c3.md --keyword "项目管理软件"
  cat draft.md | python3 content_score.py --competitors c1.md,c2.md,c3.md,c4.md --intent comparison
  python3 content_score.py --draft draft.md --competitors c1.md,c2.md,c3.md --terms terms.json --json
  python3 content_score.py --draft draft.md --competitors c1.md,c2.md,c3.md --facts facts.md

口径(references/research/borrow-specs.md C1;【官方】=一手,[推断]=自定并注明):
  * 竞品 <3 个不同来源 → 拒绝评分并说明【官方,Surfer】(去重后按内容哈希计来源数)。
  * 术语提取自竞品正文: CJK 按字 bigram + 语料词典(在 ≥2 个竞品中完整出现的 2-4 字
    连续段[推断:词典=竞品共现段]),拉丁按词;重要度 1-10 = ceil(命中竞品数/竞品总数×10)
    【官方,Clearscope】;取前 50 为话题清单。
  * SEO 轨权重[推断] (总和 0.90,缺数据维度 N/A 后重归一——同 health_score 的 Lumar 语义):
      term_coverage     0.35  MarketMuse 公式【官方】: Σ min(提及,2) / (50×2) 满分 100
      term_importance   0.10  仅 importance≥8 术语强制计入(Clearscope 8+ 规则);无 8+ → N/A
      structure         0.10  词数/标题数/段落数 vs 竞品中位数区间 [0.7,1.3]×med[推断]
      title_h1          0.05  主词或变体在 title/H1
      images_alt        0.05  alt 覆盖率;无图给中性 50[推断]
      internal_links    0.05  相对链接≥2 满[推断]
      keyword_variations 0.10 变体出现在 H2-H4 加分;精确堆砌不加分
      bolded            0.05  加粗含术语 ≥2 处满[推断]
      schema_focused    0.05  1 种相关 schema 满分,>3 扣【官方口径,扣幅推断】
  * AI 轨: facts_coverage 0.60(--facts 事实清单;缺省以术语表前 20 作事实代理并注明[推断])
            + upfront_intent 0.40(前三查【官方】: 首句点名主题/首 100 词含数字或具体事实/
            先答案后展开——首段结论性句式正则[推断:句式表])。
  * 总分 = 0.5×SEO + 0.5×AI[推断];分档 0-33 弱 / 34-66 中 / 67+ 强【官方】。
  * 目标行: 竞品均值 → 建议目标 min(max(均值+15, 70), 85)(官方"超越 10-20 分+甜区 70-85")。
  * 意图系数【官方,100 万 SERP 研究】: consequence 0.296 / definition 0.271 /
    comparison 0.225 / instructional 0.19 —— 该意图下内容分预测力,作优先级参考不改分值。
  * 关键词密度不计分【官方,Surfer 与 MarketMuse 均明确否定】—— 本脚本没有任何密度维度。

standalone 约定: 不 import 本目录其他脚本;CJK 词数/词边界计数复用 quality_rater.py
与 site_audit.py 的函数思路,独立实现。竞品均值 = 各竞品正文过同一评分器后取均值[推断]。

退出码: 评分完成 0;拒绝评分/输入不可读 2。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata

SCHEMA_VERSION = "1"

# ---- 意图系数【官方】(预测力,不改分值) ----
INTENT_COEF = {"consequence": 0.296, "definition": 0.271,
               "comparison": 0.225, "instructional": 0.19}
INTENT_NOTE = "该意图下内容分预测力,作优先级参考不改分值"

# ---- 双轨权重[推断](改权重必炸 tests/test_content_score.py 的守恒断言) ----
SEO_WEIGHTS = {
    "term_coverage": 0.35,      # MarketMuse 公式【官方】
    "term_importance": 0.10,    # Clearscope 8+ 强制计入
    "structure": 0.10,
    "title_h1": 0.05,
    "images_alt": 0.05,
    "internal_links": 0.05,
    "keyword_variations": 0.10,
    "bolded": 0.05,
    "schema_focused": 0.05,     # 1 种相关 schema 满分,>3 扣【官方口径】
}                               # 总和 0.90(true_density 已按官方否定密度剔除)——N/A 重归一
AI_WEIGHTS = {"facts_coverage": 0.60, "upfront_intent": 0.40}
assert abs(sum(SEO_WEIGHTS.values()) - 0.90) < 1e-9, "SEO 权重守恒被破坏"
assert abs(sum(AI_WEIGHTS.values()) - 1.00) < 1e-9, "AI 权重守恒被破坏"

TOP_N_TERMS = 50                # MarketMuse: 50 话题 × min(提及,2) = 满分 100【官方】
IMPORTANCE_MUST = 8             # Clearscope: importance 8+ 术语强制计入
FACTS_PROXY_N = 20              # 无 --facts 时取术语表前 20 作事实代理[推断]
TARGET_BEAT = 15.0              # 超越竞品均值 15 分(官方区间 10-20 的中值)[推断]
TARGET_FLOOR, TARGET_CAP = 70.0, 85.0   # 甜区 70-85【官方】

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
CJK_RUN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
LATIN_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*")
MD_HEAD_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.M)
HTML_HEAD_RE = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.I | re.S)
MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
HTML_IMG_RE = re.compile(r"<img\b[^>]*?alt=[\"']([^\"']*)[\"'][^>]*>", re.I)
MD_LINK_RE = re.compile(r"(?<!\!)\[[^\]]+\]\(([^)\s]+)\)")
HTML_A_RE = re.compile(r"<a\b[^>]*?href=[\"']([^\"']+)[\"']", re.I)
BOLD_RE = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__|<(?:b|strong)\b[^>]*>.*?</(?:b|strong)>", re.I | re.S)
SCHEMA_TYPE_RE = re.compile(r"['\"]@type['\"]\s*:\s*['\"]([A-Za-z]+)['\"]")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
DIGIT_RE = re.compile(r"[0-9０-９%％]")
CONCLUSIVE_RE = re.compile(
    r"简而言之|简言之|总而言之|总之|总的来说|答案是|结论是|核心结论|一句话概括|直白地说|"
    r"tl;?dr|in short|in summary|bottom line|the answer is|key takeaways?|to put it simply", re.I)
RELEVANT_SCHEMA = {"Article", "BlogPosting", "NewsArticle", "TechArticle", "FAQPage",
                   "HowTo", "Product", "Organization", "WebPage", "WebSite",
                   "BreadcrumbList", "Review", "Person", "VideoObject", "Recipe",
                   "LocalBusiness", "Course", "Event", "SoftwareApplication", "ItemList"}

EN_STOP = {"the", "a", "an", "of", "to", "for", "and", "or", "in", "on", "with", "your",
           "you", "how", "what", "why", "best", "guide", "ultimate", "complete", "is",
           "are", "be", "it", "this", "that", "by", "from", "at", "as", "we", "our",
           "can", "will", "its", "into", "than", "then", "when", "which", "while"}
ZH_FUNC_CHARS = set("的了么呢吧啊呗在于和与或及等是我不你他她它这那也都很还把被让给")


# ---------------------------------------------------------------- 基础文本函数
def read_text(path):
    if path in (None, "-", ""):
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def wc(text):
    """CJK 感知词数(site_audit.py 思路独立实现): 汉字/假名/谚文逐字计,
    其余按字母数字连续段计词;土耳其 İ 先折叠防拆词。"""
    text = text.replace("İ", "i")
    perchar = words = 0
    prev = False
    for c in text:
        if CJK_RE.match(c):
            perchar += 1
            prev = False
        else:
            is_l = unicodedata.category(c)[0] == "L" or c.isdigit()
            if is_l and not prev:
                words += 1
            prev = is_l or (c == "'" and prev)
    return perchar + words


def first_100_words(text):
    """前 100 词原文窗口(quality_rater.py 思路): 汉字单字/拉丁词逐 token 保序拼接。"""
    out, size = [], 0
    for tok in re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]"
                          r"|[A-Za-z0-9][A-Za-z0-9'\-]*|\s+", text):
        if not tok.strip() and not CJK_RE.match(tok):
            if out:
                out.append(tok)
            continue
        out.append(tok)
        size += 1
        if size >= 100:
            break
    return "".join(out)


def cjk_bigrams(text):
    """CJK 字 bigram(跳过功能字组合)。"""
    grams = []
    for run in CJK_RUN.findall(text):
        for i in range(len(run) - 1):
            g = run[i:i + 2]
            if g[0] in ZH_FUNC_CHARS and g[1] in ZH_FUNC_CHARS:
                continue
            grams.append(g)
    return grams


def latin_words(text):
    return [w.lower() for w in LATIN_WORD.findall(text)]


def tokenize(text):
    """统一 token 流: CJK bigram + 拉丁小写词(停用词滤除)——facts 覆盖/标题共现共用。"""
    toks = list(cjk_bigrams(text))
    toks += [w for w in latin_words(text) if w not in EN_STOP and len(w) > 1]
    return toks


def term_count(term, text):
    """术语出现次数: CJK 子串计数,拉丁词边界计数(空白弹性匹配)[推断]。"""
    if not term:
        return 0
    if CJK_RE.search(term):
        return text.count(term)
    pat = r"\b" + r"\s+".join(re.escape(w) for w in term.lower().split()) + r"\b"
    return len(re.findall(pat, text, re.I))


def headings_of(text):
    """[(level, text)]: markdown # 行 + HTML <h1>-<h6>;标题内联标记剥除。"""
    heads = []
    for m in MD_HEAD_RE.finditer(text):
        heads.append((len(m.group(1)), clean_inline(m.group(2))))
    for m in HTML_HEAD_RE.finditer(text):
        heads.append((int(m.group(1)), clean_inline(m.group(2))))
    return heads


def clean_inline(s):
    return re.sub(r"[*_`]+", "", re.sub(r"<[^>]+>", "", s)).strip()


def title_and_h1(text):
    """title = 首个非空行(剥 #/内联标记);H1 = 首个一级标题(# 或 <h1>),缺省回落 title。"""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = lines[0] if lines else ""
    m = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", title)
    if m:
        title = m.group(1)
    title = clean_inline(title)
    h1 = title
    for lv, t in headings_of(text):
        if lv == 1:
            h1 = t
            break
    return title, h1


def paragraphs_count(text):
    return len([b for b in re.split(r"\n\s*\n", text) if b.strip()])


def percentile(vals, q):
    """线性插值分位数(numpy 默认口径)[推断]。"""
    s = sorted(vals)
    if not s:
        return 0.0
    if len(s) == 1:
        return float(s[0])
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


# ---------------------------------------------------------------- 术语模型
def extract_terms(comp_texts):
    """从竞品正文提术语表: {term, importance, freqs, source} 按重要度/频次取前 50。
    CJK = 2-6 字 n-gram 词典式简单切分(长优先+包含吸收,首尾功能字滤除)[推断];
    拉丁 = 词。importance = ceil(命中竞品数/竞品总数×10)【官方,Clearscope】。"""
    n = len(comp_texts)
    cand = {}

    def add(term, hits, freq):
        cur = cand.get(term)
        if cur is None or (hits, freq) > (cur[0], cur[1]):
            cand[term] = [hits, freq]

    grams = set()
    for t in comp_texts:
        for run in CJK_RUN.findall(t):
            for ln in range(2, 7):                     # 2-6 字候选段
                for i in range(len(run) - ln + 1):
                    g = run[i:i + ln]
                    if g[0] in ZH_FUNC_CHARS or g[-1] in ZH_FUNC_CHARS:
                        continue
                    if ln >= 5 and any(c in ZH_FUNC_CHARS for c in g):
                        continue                        # 长段含功能字≈跨界拼接噪声[推断]
                    grams.add(g)
    for g in grams:
        hits = sum(1 for t in comp_texts if g in t)
        if hits:
            add(g, hits, sum(t.count(g) for t in comp_texts))
    latin_docs, latin_freq = {}, {}
    for t in comp_texts:
        tl = t.lower()
        for w in set(latin_words(tl)):
            latin_docs[w] = latin_docs.get(w, 0) + 1
        for w in latin_words(tl):
            latin_freq[w] = latin_freq.get(w, 0) + 1
    for w, d in latin_docs.items():
        if w not in EN_STOP and len(w) > 1:
            add(w, d, latin_freq.get(w, 0))

    # 排序: 命中竞品数 desc → 段长 desc(词典优先长词)→ 总频次 desc → 字典序
    ranked = sorted(cand.items(), key=lambda kv: (-kv[1][0], -len(kv[0]), -kv[1][1], kv[0]))
    terms, chosen = [], []
    for term, (hits, freq) in ranked:
        if len(terms) >= TOP_N_TERMS:
            break
        if CJK_RE.search(term) and any(term in c for c in chosen):
            continue                        # 被更长已选术语包含的子段去重[推断]
        freqs = [term_count(term, t) for t in comp_texts]
        terms.append({"term": term,
                      "importance": max(1, min(10, math.ceil(hits / n * 10))),
                      "freqs": freqs, "source": "serp"})
        chosen.append(term)
    return terms


def load_terms_file(path, comp_texts):
    """--terms terms.json: 接受 [ {...} ] 或 {"terms": [...]};term 必填,
    importance 缺省 5[推断];recommended_range 缺省时从竞品词频补[推断]。"""
    data = json.loads(read_text(path))
    items = data.get("terms", data) if isinstance(data, dict) else data
    out = []
    for it in items:
        if isinstance(it, str):
            it = {"term": it}
        term = str(it.get("term", "")).strip()
        if not term:
            continue
        out.append({"term": term,
                    "importance": max(1, min(10, int(it.get("importance", 5)))),
                    "freqs": [term_count(term, t) for t in comp_texts] if comp_texts else [],
                    "source": str(it.get("source", "nlp"))})
    return out


def recommended_range(freqs):
    """竞品词频四分位 P25-P75[borrow-specs C1: 竞品四分位 inferred]。"""
    if not freqs:
        return "-"
    lo = int(math.floor(percentile(freqs, 0.25)))
    hi = int(math.ceil(percentile(freqs, 0.75)))
    return "%d-%d" % (lo, hi)


# ---------------------------------------------------------------- 各维度打分
def score_term_coverage(terms, text):
    """MarketMuse【官方】: Σ min(提及, 2) ÷ (话题数×2) × 100。"""
    if not terms:
        return None, "无术语表"
    got = sum(min(term_count(t["term"], text), 2) for t in terms)
    note = "命中 %s/%s(min(提及,2) 封顶)——MarketMuse 50 话题×2=满分 100" % (got, len(terms) * 2)
    return got / (len(terms) * 2.0) * 100.0, note


def score_term_importance(terms, text):
    """Clearscope: importance≥8 术语强制计入;无 8+ 术语 → N/A(不计权重)。"""
    must = [t for t in terms if t["importance"] >= IMPORTANCE_MUST]
    if not must:
        return None, "无 importance≥%d 术语(竞品共识弱)→ N/A 不计权重" % IMPORTANCE_MUST
    used = sum(1 for t in must if term_count(t["term"], text) > 0)
    return used / len(must) * 100.0, "8+ 术语命中 %d/%d(强制计入)" % (used, len(must))


def score_structure(text, comp_texts):
    """词数/标题数/段落数 vs 竞品中位数区间 [0.7,1.3]×med[推断];med=0 → 该子项 N/A。"""
    def stat(t):
        return (wc(t), len(headings_of(t)), paragraphs_count(t))
    mine = stat(text)
    meds = [percentile([stat(c)[i] for c in comp_texts], 0.5) for i in range(3)]
    names = ("词数", "标题数", "段落数")
    subs, notes = [], []
    for val, med, nm in zip(mine, meds, names):
        if med <= 0:
            notes.append("%s: 竞品中位 0 → N/A" % nm)
            continue
        ratio = val / med
        if 0.7 <= ratio <= 1.3:
            subs.append(100.0)
            notes.append("%s %d(中位 %.0f,在带内)" % (nm, val, med))
        else:
            d = (0.7 - ratio) if ratio < 0.7 else (ratio - 1.3)
            subs.append(max(0.0, 100.0 - d / 0.35 * 50.0))
            notes.append("%s %d(中位 %.0f,带外 ×%.2f)" % (nm, val, med, ratio))
    if not subs:
        return None, "; ".join(notes) or "竞品无结构数据"
    return sum(subs) / len(subs), "; ".join(notes)


def keyword_variants(keyword):
    """主词变体[推断]: CJK 取 2..len-1 字连续子串;拉丁取连续词子序列(≥2 词)
    及 ≥4 字母单词。用于 title/H1 与 H2-H4 加分;精确堆砌不计。"""
    out = []
    if not keyword:
        return out
    if CJK_RE.search(keyword):
        for ln in range(2, len(keyword)):
            for i in range(len(keyword) - ln + 1):
                sub = keyword[i:i + ln]
                if sub not in out and not (sub[0] in ZH_FUNC_CHARS or sub[-1] in ZH_FUNC_CHARS):
                    out.append(sub)
    else:
        ws = keyword.lower().split()
        if len(ws) >= 3:
            for ln in range(2, len(ws)):
                for i in range(len(ws) - ln + 1):
                    out.append(" ".join(ws[i:i + ln]))
        elif len(ws) == 2:
            out += [w for w in ws if len(w) >= 4]
        out += [w for w in ws if len(w) >= 4 and w not in out]
    return [v for v in out if v != keyword.lower()]


def score_title_h1(text, keyword):
    if not keyword:
        return None, "无主词 → N/A"
    title, h1 = title_and_h1(text)
    hits = []
    for label, hay in (("title", title), ("H1", h1)):
        if term_count(keyword, hay) > 0:
            hits.append(label + "=精确")
        elif any(term_count(v, hay) > 0 for v in keyword_variants(keyword)):
            hits.append(label + "=变体")
    note = "title「%s」/H1「%s」命中: %s" % (title[:30], h1[:30], ",".join(hits) or "无")
    return (100.0 if hits else 0.0), note


def score_images_alt(text):
    """alt 覆盖率(markdown ![alt]() + html <img alt>);无图中性 50[推断]。"""
    alts = [m for m in MD_IMG_RE.findall(text)]
    alts += HTML_IMG_RE.findall(text)
    n = len(alts)
    if n == 0:
        return 50.0, "无图片(正文文件可能已剥离图片)→ 中性 50[推断]"
    ok = sum(1 for a in alts if a.strip())
    return ok / n * 100.0, "图片 %d 张,alt 覆盖 %d" % (n, ok)


def score_internal_links(text):
    """内链 = 相对链接(无 scheme、非 mailto)——无 --site 参数下的站点无关代理[推断]。"""
    urls = MD_LINK_RE.findall(text) + HTML_A_RE.findall(text)
    internal = [u for u in urls if not SCHEME_RE.match(u) and not u.startswith("mailto:")]
    s = min(100.0, len(internal) / 2.0 * 100.0)
    return s, "相对内链 %d 条(≥2 满)" % len(internal)


def score_keyword_variations(text, keyword):
    """变体出现在 H2-H4 各加 25 分封顶 100[推断];精确主词堆砌不加分(密度不计分)。"""
    variants = keyword_variants(keyword)
    if not keyword or not variants:
        return None, "无可生成变体 → N/A"
    heads = " ".join(t for lv, t in headings_of(text) if 2 <= lv <= 4)
    hit = [v for v in variants if term_count(v, heads) > 0]
    note = "H2-H4 命中变体 %d/%d: %s" % (len(hit), len(variants), ", ".join(hit[:5]) or "无")
    return min(100.0, len(hit) * 25.0), note


def score_bolded(text, terms):
    """加粗含术语 ≥2 处满[推断](Surfer bolded 因素)。"""
    spans = BOLD_RE.findall(text)
    spans = [clean_inline(s) for s in spans if s and s.strip()]
    useful = [s for s in spans if any(term_count(t["term"], s) > 0 for t in terms[:20])]
    s = min(100.0, len(useful) / 2.0 * 100.0)
    return s, "术语加粗 %d 处(≥2 满)" % len(useful)


def score_schema_focused(text):
    """1 种相关 schema 满分,>3 扣【官方口径,扣幅 20/个推断】;无关类型折半。"""
    types = sorted(set(SCHEMA_TYPE_RE.findall(text)))
    if not types:
        return 0.0, "未检出 schema(@type)"
    rel = [t for t in types if t in RELEVANT_SCHEMA]
    if not rel:
        return 50.0, "schema %s 均非内容相关类型 → 折半" % types
    s = 100.0
    if len(types) > 3:
        s = max(0.0, 100.0 - (len(types) - 3) * 20.0)
    return s, "schema 类型 %d 种 %s" % (len(types), types)


# ---------------------------------------------------------------- AI 轨
def load_facts(path):
    if not path:
        return None
    facts = []
    for line in read_text(path).splitlines():
        s = re.sub(r"^[\s\-*•]+\s*", "", line.strip())
        if s and not s.startswith("#"):
            facts.append(s)
    return facts


def fact_covered(fact, draft_token_set):
    """事实覆盖[推断]: 事实 token(CJK bigram/拉丁词,滤停用词)≥60% 出现在正文。"""
    toks = tokenize(fact)
    if not toks:
        return False
    hit = sum(1 for t in toks if t in draft_token_set)
    return hit / len(toks) >= 0.6


def score_facts_coverage(text, facts, terms, notes):
    """"--facts 事实清单;缺省以术语表前 20 作事实代理并注明[推断]。"""
    if facts:
        src = "--facts 清单 %d 条" % len(facts)
    else:
        facts = [t["term"] for t in terms[:FACTS_PROXY_N]]
        src = "未提供 --facts → 术语表前 %d 作事实代理[推断]" % len(facts)
        notes.append("facts_coverage 使用事实代理: " + src)
    if not facts:
        return None, "无事实可核"
    tset = set(tokenize(text))
    covered = sum(1 for f in facts if fact_covered(f, tset))
    return covered / len(facts) * 100.0, "事实覆盖 %d/%d(%s)" % (covered, len(facts), src)


def body_blocks(text):
    """正文块序列: 剥代码围栏后,按空行/标题/表格/图片行切块;内联标记剥除。"""
    blocks, cur = [], []
    fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        s = line.strip()
        if not s or s.startswith(("#", "---", "|", "![", "[", "<")):
            if cur:
                blocks.append(" ".join(cur))
                cur = []
            continue
        cur.append(re.sub(r"[*_`]+", "", s))
    if cur:
        blocks.append(" ".join(cur))
    return blocks


def first_sentence(text):
    """首句: 第一个正文块内首个强终止符(.!?。!?; ;)之前的部分(CJK 无空格也切)。"""
    for b in body_blocks(text):
        parts = re.split(r"(?<=[.!?。!?;；])", b)
        for p in parts:
            if p.strip():
                return p.strip()
        return b
    return ""


def upfront_three_checks(text, keyword, variants):
    """前三查【官方】(首 100 词内): ①首句点名主词或同义词 ②含数字/具体事实
    ③先答案后展开——首段结论性句式[推断:句式表]。返回 [bool,bool,bool]。"""
    sent = first_sentence(text)
    c1 = bool(keyword) and (term_count(keyword, sent) > 0
                            or any(term_count(v, sent) > 0 for v in variants))
    window = first_100_words("".join(body_blocks(text)[:2]))
    c2 = bool(DIGIT_RE.search(window))
    first_para = body_blocks(text)[0] if body_blocks(text) else ""
    c3 = bool(CONCLUSIVE_RE.search(first_para))
    return [c1, c2, c3]


def score_upfront_intent(text, keyword, variants):
    checks = upfront_three_checks(text, keyword, variants)
    names = ("首句含主词或同义词", "首 100 词含数字/具体事实", "先答案后展开(结论性句式)")
    note = "; ".join("%s:%s" % (n, "过" if c else "缺") for n, c in zip(names, checks))
    return sum(checks) / 3.0 * 100.0, note


# ---------------------------------------------------------------- 双轨合成
def weighted(dims):
    """N/A(score=None)维度剔除后重归一[推断,同 health_score Lumar 语义]。
    score 已是 0-100 制:num/den 即加权均分,不再乘 100。"""
    num = den = 0.0
    for d in dims.values():
        if d["score"] is not None:
            num += d["weight"] * d["score"]
            den += d["weight"]
    return (num / den) if den > 0 else 0.0


def score_text(text, model, keyword, facts):
    """对任意正文(草稿或竞品)过同一评分器;model 带 terms/竞品统计。"""
    terms, comp_texts = model["terms"], model["comp_texts"]
    notes = []
    variants = keyword_variants(keyword)
    seo_dims = {}
    for name, fn in (
            ("term_coverage", lambda: score_term_coverage(terms, text)),
            ("term_importance", lambda: score_term_importance(terms, text)),
            ("structure", lambda: score_structure(text, comp_texts)),
            ("title_h1", lambda: score_title_h1(text, keyword)),
            ("images_alt", lambda: score_images_alt(text)),
            ("internal_links", lambda: score_internal_links(text)),
            ("keyword_variations", lambda: score_keyword_variations(text, keyword)),
            ("bolded", lambda: score_bolded(text, terms)),
            ("schema_focused", lambda: score_schema_focused(text))):
        s, note = fn()
        seo_dims[name] = {"weight": SEO_WEIGHTS[name], "score": s, "note": note}
    ai_dims = {}
    s, note = score_facts_coverage(text, facts, terms, notes)
    ai_dims["facts_coverage"] = {"weight": AI_WEIGHTS["facts_coverage"], "score": s, "note": note}
    s, note = score_upfront_intent(text, keyword, variants)
    ai_dims["upfront_intent"] = {"weight": AI_WEIGHTS["upfront_intent"], "score": s, "note": note}
    seo = weighted(seo_dims)
    ai = weighted(ai_dims)
    total = 0.5 * seo + 0.5 * ai
    return {"seo": seo, "ai": ai, "total": total, "seo_dims": seo_dims,
            "ai_dims": ai_dims, "notes": notes}


def band(total):
    """分档【官方】: 0-33 弱 / 34-66 中 / 67+ 强(按四舍五入取整归档)。"""
    t = int(round(total))
    if t <= 33:
        return "weak", "0-33"
    if t <= 66:
        return "mid", "34-66"
    return "strong", "67+"


def target_score(comp_avg):
    """官方: 超越竞品 10-20 分+甜区 70-85 → min(max(avg+15,70),85)[推断取 15]。"""
    return min(max(comp_avg + TARGET_BEAT, TARGET_FLOOR), TARGET_CAP)


# ---------------------------------------------------------------- 报告
def build_report(res, args, model, keyword, facts, comp_results, out_json=False):
    terms = model["terms"]
    b, brange = band(res["total"])
    comp_scores = [round(c["total"], 1) for c in comp_results]
    comp_avg = sum(c["total"] for c in comp_results) / len(comp_results)
    tgt = target_score(comp_avg)

    table = []
    for t in terms:
        table.append({"term": t["term"], "importance": t["importance"],
                      "recommended_range": recommended_range(t["freqs"]),
                      "used": term_count(t["term"], res["_text"]),
                      "in_heading": any(term_count(t["term"], h) > 0
                                        for _lv, h in headings_of(res["_text"])),
                      "source": t["source"]})

    heads = headings_of(res["_text"])
    missing = []
    for row in table:
        if row["used"] == 0:
            missing.append({"term": row["term"], "importance": row["importance"],
                            "recommended_range": row["recommended_range"],
                            "suggestion": suggest_insertion(row, heads)})

    payload = {
        "schema_version": SCHEMA_VERSION,
        "keyword": keyword,
        "intent": args.intent,
        "intent_coefficient": INTENT_COEF[args.intent],
        "intent_note": INTENT_NOTE,
        "density_scored": False,   # 关键词密度不计分【官方,Surfer/MarketMuse 明确否定】
        "term_model": {"n_terms": len(terms), "source": model["source"],
                       "n_competitors": model["n_comps"],
                       "competitor_files": model["files"]},
        "seo": {"score": round(res["seo"], 1), "dims": {
            k: {"weight": v["weight"],
                "score": None if v["score"] is None else round(v["score"], 1),
                "note": v["note"]} for k, v in res["seo_dims"].items()}},
        "ai": {"score": round(res["ai"], 1), "dims": {
            k: {"weight": v["weight"], "score": round(v["score"], 1), "note": v["note"]}
            for k, v in res["ai_dims"].items()}},
        "total": round(res["total"], 1), "band": b, "band_range": brange,
        "target": {"competitor_average": round(comp_avg, 1),
                   "competitor_scores": comp_scores,
                   "recommended": round(tgt, 1), "cap": TARGET_CAP},
        "term_table": table,
        "missing_terms": missing,
        "notes": res["notes"] + ["关键词密度不计分(Surfer 与 MarketMuse 官方明确否定)"],
    }
    if out_json:
        return json.dumps(payload, ensure_ascii=False, indent=1)

    L = []
    L.append("# content_score 报告(透明内容评分器)")
    L.append("- draft: %s | 主词: %s | 意图: %s" % (args.draft, keyword or "-", args.intent))
    L.append("- 意图系数: %s r=%.3f【官方,100 万 SERP 研究】—— %s"
             % (args.intent, INTENT_COEF[args.intent], INTENT_NOTE))
    L.append("- 术语模型: %d 条(来源 %s,竞品 %d 个不同来源)" %
             (len(terms), model["source"], model["n_comps"]))
    L.append("- 口径注: 关键词密度不计分(Surfer 与 MarketMuse 官方明确否定)")
    L.append("")
    L.append("## SEO 轨: %.1f / 100" % res["seo"])
    L.append("| 维度 | 权重 | 得分 | 说明 |")
    L.append("|---|---|---|---|")
    for k, w in SEO_WEIGHTS.items():
        v = res["seo_dims"][k]
        sc = "N/A" if v["score"] is None else "%.0f" % v["score"]
        L.append("| %s | %.2f | %s | %s |" % (k, w, sc, v["note"].replace("|", "/")))
    L.append("")
    L.append("## AI 轨: %.1f / 100" % res["ai"])
    L.append("| 维度 | 权重 | 得分 | 说明 |")
    L.append("|---|---|---|---|")
    for k, w in AI_WEIGHTS.items():
        v = res["ai_dims"][k]
        sc = "N/A" if v["score"] is None else "%.0f" % v["score"]
        L.append("| %s | %.2f | %s | %s |" % (k, w, sc, v["note"].replace("|", "/")))
    L.append("")
    L.append("- 总分 = 0.5×SEO + 0.5×AI = **%.1f** → 分档: %s(%s)" % (res["total"], b, brange))
    L.append("- 目标行: 竞品均值 %.1f → 建议目标 min(max(%.1f+15, 70), 85) = **%.1f** 封顶 %d"
             "(官方: 超越竞品 10-20 分,甜区 70-85)" % (comp_avg, comp_avg, tgt, TARGET_CAP))
    L.append("- 竞品各自得分: %s" % ", ".join(str(s) for s in comp_scores))
    L.append("")
    L.append("## 术语表 Top 20")
    L.append("| # | term | importance | recommended_range | used | in_heading | source |")
    L.append("|---|---|---|---|---|---|---|")
    for i, row in enumerate(table[:20], 1):
        L.append("| %d | %s | %d | %s | %d | %s | %s |" % (
            i, row["term"], row["importance"], row["recommended_range"],
            row["used"], "Y" if row["in_heading"] else "-", row["source"]))
    L.append("")
    if missing:
        L.append("## 缺失术语清单(可自然补齐的插入建议点)")
        for m in sorted(missing, key=lambda x: -x["importance"])[:15]:
            rng = m["recommended_range"] if m["recommended_range"] != "-" else "1-2"
            L.append("- **%s**(importance %d,竞品区间 %s)→ %s" %
                     (m["term"], m["importance"], rng, m["suggestion"]))
    else:
        L.append("## 缺失术语清单: 无(话题全覆盖)")
    for n in res["notes"]:
        L.append("")
        L.append("> 注: " + n)
    return "\n".join(L) + "\n"


def suggest_insertion(row, heads):
    """缺失术语的自然插入建议点[推断]: 高共识→新增小节;能与现有 H2-H4 共享
    token → 并入该小节;低共识 → FAQ/结尾补一笔。"""
    if row["importance"] >= IMPORTANCE_MUST:
        return "必补(8+ 高共识):新增 H2 小节直击该话题,或在首段后的定义段自然带出"
    toks = set(tokenize(row["term"]))
    best, best_ov = None, 0
    for lv, h in heads:
        if 2 <= lv <= 4:
            ov = len(toks & set(tokenize(h)))
            if ov > best_ov:
                best, best_ov = h, ov
    if best:
        return "并入现有小节「%s」自然提及 1-2 次(标题共现)" % best[:30]
    return "低共识话题:在 FAQ 或结尾延伸段自然补齐 1 次即可"


# ---------------------------------------------------------------- main
def parse_competitors(spec):
    files = [p.strip() for p in (spec or "").split(",") if p.strip()]
    out, seen = [], set()
    for p in files:
        try:
            body = read_text(p)
        except OSError as e:
            print("[FATAL] 竞品文件不可读 %s: %s" % (p, e), file=sys.stderr)
            sys.exit(2)
        h = hashlib.sha1(body.encode("utf-8", "ignore")).hexdigest()
        if h in seen:                       # 同内容去重——"不同来源"按内容计[推断]
            continue
        seen.add(h)
        out.append((p, body))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="content_score.py",
        description="透明内容评分器(MarketMuse 话题公式 + Surfer 双轨;关键词密度不计分)")
    ap.add_argument("--draft", default="-", help="草稿 markdown/纯文本路径,'-' 或缺省读 stdin")
    ap.add_argument("--competitors", default="",
                    help="竞品正文文件,逗号分隔(≥3 个不同来源才评分,Surfer 官方规则)")
    ap.add_argument("--terms", default=None,
                    help="直接给术语表 JSON([{term,importance,source}] 或 {terms:[...]})")
    ap.add_argument("--keyword", default=None, help="主词;缺省取术语表首位并注明")
    ap.add_argument("--intent", choices=sorted(INTENT_COEF), default="definition",
                    help="搜索意图(默认 definition,只影响输出的意图系数行,不改分值)")
    ap.add_argument("--facts", default=None, help="AI 事实清单文件(每行一条)")
    ap.add_argument("--json", action="store_true", help="JSON 输出(含 schema_version)")
    args = ap.parse_args(argv)

    try:
        draft = read_text(args.draft)
    except OSError as e:
        print("[FATAL] 草稿不可读 %s: %s" % (args.draft, e), file=sys.stderr)
        return 2
    if not draft.strip():
        print("[FATAL] 草稿为空", file=sys.stderr)
        return 2

    comps = parse_competitors(args.competitors)
    if len(comps) < 3:
        print("[REFUSED] 拒绝评分: 竞品仅 %d 个不同来源(去重后),<3 —— Surfer 官方规则:"
              "少于 3 个不同来源的样本不足以建话题模型,评分不可靠。"
              "请补足 --competitors c1,c2,c3(同内容文件按同来源去重)。"
              % len(comps))
        return 2

    comp_texts = [b for _p, b in comps]
    if args.terms:
        try:
            terms = load_terms_file(args.terms, comp_texts)
        except (OSError, ValueError) as e:
            print("[FATAL] --terms 解析失败: %s" % e, file=sys.stderr)
            return 2
        model_source = "terms-file"
    else:
        terms = extract_terms(comp_texts)
        model_source = "serp"
    if not terms:
        print("[FATAL] 术语表为空(竞品正文无可提取术语或 --terms 为空)", file=sys.stderr)
        return 2

    model = {"terms": terms, "comp_texts": comp_texts, "source": model_source,
             "n_comps": len(comps), "files": [p for p, _b in comps]}

    keyword = (args.keyword or "").strip()
    if not keyword:
        top = max(terms, key=lambda t: (t["importance"], sum(t["freqs"])))
        keyword = top["term"]

    facts = load_facts(args.facts)
    res = score_text(draft, model, keyword, facts)
    res["_text"] = draft
    if not args.keyword:
        res["notes"].append("主词未指定 → 自动取术语表首位「%s」[推断]" % keyword)
    comp_results = []
    for _p, body in comps:
        c = score_text(body, model, keyword, facts)
        c["_text"] = body
        comp_results.append(c)

    out = build_report(res, args, model, keyword, facts, comp_results, out_json=args.json)
    print(out)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        sys.exit(130)
