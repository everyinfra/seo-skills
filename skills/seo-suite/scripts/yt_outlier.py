#!/usr/bin/env python3
"""YouTube 离群检测(stdlib)。输入 CSV: title,duration_s,views[,is_short][,channel]。
按 频道×形态 分组(≤60s=Short,长短视频基线分开),离群=播放>该组均值 2×;
对离群标题分词(60 词停用表 + len>2 过滤)Counter 取前 15 高频词。
输出按 multiplier 降序的离群清单 + 标题高频词。

用法: python3 yt_outlier.py videos.csv
退出码:0=跑完;2=文件/格式错误。"""
import csv
import re
import sys
from collections import Counter, defaultdict

# 60 个常用停用词(规格要求恰好 60,含 the/a/to/and/in/of/for/how/with/your)
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "else", "when",
    "while", "of", "to", "in", "on", "at", "by", "for", "with", "from",
    "into", "over", "under", "about", "after", "before", "between", "during",
    "through", "up", "down", "out", "off", "again", "how", "what", "why",
    "who", "whom", "whose", "which", "where", "this", "that", "these",
    "those", "you", "your", "i", "we", "our", "they", "them", "their",
    "it", "its", "is", "are", "was", "were",
}
assert len(_STOPWORDS) == 60, "停用表必须恰好 60 词"

MIN_TOKEN_LEN = 3          # len>2
OUTLIER_MULT = 2.0         # 播放 > 2× 组均值
SHORT_MAX_S = 60           # ≤60s = Short
TOP_TOKENS = 15


def truthy(v):
    return (v or "").strip().lower() in ("1", "true", "yes", "y", "t")


def load(path):
    try:
        f = open(path, encoding="utf-8-sig", newline="")
    except OSError as e:
        print(f"[error] 无法读取 {path}: {e}", file=sys.stderr)
        sys.exit(2)
    with f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames:
            print(f"[error] {path}: 空 CSV", file=sys.stderr)
            sys.exit(2)
        cols = {c.strip().lower(): c for c in rdr.fieldnames if c}
        tk = next((cols[k] for k in ("title",) if k in cols), None)
        dk = next((cols[k] for k in ("duration_s", "duration", "duration_sec") if k in cols), None)
        vk = next((cols[k] for k in ("views", "view_count") if k in cols), None)
        if not (tk and dk and vk):
            print(f"[error] {path}: 需要 title,duration_s,views 列,实际={list(rdr.fieldnames)}",
                  file=sys.stderr)
            sys.exit(2)
        sk = next((cols[k] for k in ("is_short",) if k in cols), None)
        ck = next((cols[k] for k in ("channel", "channel_name") if k in cols), None)
        vids = []
        for i, row in enumerate(rdr, 2):
            title = (row.get(tk) or "").strip()
            try:
                dur = float((row.get(dk) or "0").replace(",", ""))
                views = float((row.get(vk) or "0").replace(",", ""))
            except ValueError:
                print(f"[warn] 第 {i} 行数值非法,跳过: {row}", file=sys.stderr)
                continue
            if not title:
                continue
            sk_val = (row.get(sk) or "").strip() if sk else ""
            is_short = truthy(sk_val) if sk_val else dur <= SHORT_MAX_S  # 空值回退时长判断
            channel = (row.get(ck) or "(default)").strip() if ck else "(default)"
            vids.append({"title": title, "dur": dur, "views": views,
                         "is_short": is_short, "channel": channel})
    return vids


def tokens_of(titles):
    c = Counter()
    for t in titles:
        for w in re.findall(r"[a-z0-9']+", t.lower()):
            if len(w) >= MIN_TOKEN_LEN and w not in _STOPWORDS:
                c[w] += 1
    return c


def main():
    import argparse
    ap = argparse.ArgumentParser(description="YouTube 离群检测(离群 = views > 2× 频道×形态 组均值)")
    ap.add_argument("csv", help="视频清单 CSV: title,duration_s,views[,is_short][,channel]")
    a = ap.parse_args()
    vids = load(a.csv)
    if not vids:
        print("[error] 无有效行", file=sys.stderr)
        sys.exit(2)

    groups = defaultdict(list)
    for v in vids:
        groups[(v["channel"], "short" if v["is_short"] else "long")].append(v)

    W = 64
    print("=" * W); print("YouTube 离群检测(离群 = views > 2× 组均值)".center(W)); print("=" * W)
    print(f"共 {len(vids)} 条视频,{len(groups)} 个 频道×形态 组(≤{SHORT_MAX_S}s=Short,基线分开)")
    all_outlier_titles = []
    n_out = 0
    for (channel, fmt), members in sorted(groups.items()):
        views = [m["views"] for m in members]
        mean = sum(views) / len(views)
        print("-" * W)
        print(f"channel={channel}  format={fmt}  n={len(members)}  mean_views={mean:.0f}"
              + ("   [跳过:组均值=0]" if mean == 0 else ""))
        if mean == 0:
            continue
        outs = [(m, m["views"] / mean) for m in members if m["views"] > OUTLIER_MULT * mean]
        outs.sort(key=lambda x: -x[1])
        n_out += len(outs)
        if not outs:
            print("  (无离群:没有视频超过 2× 均值)")
        for rank, (m, mult) in enumerate(outs, 1):
            print(f"  {rank:>2}. ×{mult:.2f}  views={m['views']:.0f}  dur={m['dur']:.0f}s  {m['title']}")
            all_outlier_titles.append(m["title"])

    print("=" * W)
    print(f"离群合计:{n_out} 条;离群标题高频词(去 60 停用词、len>2,Top {TOP_TOKENS}):")
    if all_outlier_titles:
        for w, n in tokens_of(all_outlier_titles).most_common(TOP_TOKENS):
            bar = "█" * min(n, 30)
            print(f"  {w:<16} {n:>3}  {bar}")
    else:
        print("  (无离群标题,无词频)")
    print("=" * W)
    print("用法提示:高频词=离群选题信号,优先复制其选题/封面/结构做下一条。")


if __name__ == "__main__":
    main()
