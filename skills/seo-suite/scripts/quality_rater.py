#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""quality_rater.py — 内容质量六维评分 (读纯文本, 仅标准库).

用法:
  python3 quality_rater.py draft.txt
  python3 quality_rater.py draft.txt --market zh --keyword "项目管理软件"
  cat draft.md | python3 quality_rater.py - --market en

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

退出码: publishing_ready -> 0; 否则 1; 文件读不到 -> 2.
"""
from __future__ import annotations

import argparse
import re
import sys

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
LATIN_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'\-]*")
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
    """CJK 感知词数: 汉字逐字计 1, 其余按空白/字母数字分词."""
    cjk = len(CJK_RE.findall(text))
    latin = len(LATIN_WORD_RE.findall(CJK_RE.sub(" ", text)))
    return cjk + latin


def first_100_words_text(text):
    """截取约前 100 词的原文窗口 (保持 CJK 字符连续)."""
    words = []
    size = 0
    # 把文本切成 汉字/拉丁词/其他 三类 token, 保留原文顺序
    for tok in re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]|[A-Za-z0-9][A-Za-z0-9'\-]*|\s+", text):
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


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="quality_rater.py",
        description="内容质量六维评分 (纯文本, CJK 感知, stdlib only)")
    ap.add_argument("file", help="纯文本/markdown 文件路径, '-' 表示 stdin")
    ap.add_argument("--market", choices=("zh", "en"), default="zh",
                    help="市场: zh 汉字感知分词与标题启发 (默认 zh)")
    ap.add_argument("--keyword", default=None,
                    help="主词; 不给则按词频自动推断")
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
    return 0 if ready else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        sys.exit(130)
