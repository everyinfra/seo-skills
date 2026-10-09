#!/usr/bin/env python3
"""趋势雷达(stdlib,免 key):HN topstories 前 30 + Reddit 6 个 sub 各 hot 5
(score>50 才收)。对 --vertical 词打相关性分:HIGH(整词命中)+25 / MED(部分命中)+10。
白名单门槛:HN·Reddit 相关条目合计 ≥15 才建议立项,输出角度 + 适配平台。
X/Twitter 无 key 时明说跳过,不猜。抓取并发(ThreadPoolExecutor),单源失败明说。

用法: python3 trend_scout.py [--vertical "llm seo"]
退出码:0=跑完(无论白名单过否);2=所有源都失败/无数据。"""
import argparse
import json
import re
import sys
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

UA = ("trend-scout/1.0 (seo-skills research bot; "
      "+https://github.com/everyinfra/seo-skills)")
HN_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"
REDDIT_SUBS = ["seo", "bigseo", "technology", "startups", "webdev", "marketing"]
HN_LIMIT = 30
REDDIT_LIMIT = 5
MIN_SCORE = 50          # reddit 收录门槛
WHITELIST_MIN = 15      # HN·Reddit 合计相关条目门槛
SCORE_HIGH, SCORE_MED = 25, 10
TIMEOUT = 10

_STOP = {"the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for",
         "with", "how", "your", "you", "is", "are", "was", "it", "its", "this",
         "that", "what", "why", "who", "new", "now", "best", "using", "from"}


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def _safe(fn, *args):
    """线程池里不能 try/except 住调用方,包一层返回异常对象。"""
    try:
        return fn(*args)
    except Exception as e:
        return e


def relevance(title, tokens):
    """返回 (得分, 标签):整词命中 HIGH+25,部分命中 MED+10。"""
    t = title.lower()
    score = 0
    for tok in tokens:
        if re.search(r"\b" + re.escape(tok) + r"\b", t):
            score += SCORE_HIGH
        elif tok in t:
            score += SCORE_MED
    tag = "HIGH" if score >= SCORE_HIGH else "MED" if score > 0 else ""
    return score, tag


def main():
    ap = argparse.ArgumentParser(description="HN+Reddit 趋势雷达(stdlib,免 key)")
    ap.add_argument("--vertical", default="", help="垂直词(空格分隔多个 token)")
    a = ap.parse_args()
    tokens = [t.lower() for t in re.split(r"[\s,]+", a.vertical.strip()) if t]

    W = 68
    print("=" * W); print("趋势雷达(HN + Reddit,免 key)".center(W)); print("=" * W)
    if tokens:
        print(f"vertical: {' '.join(tokens)}(HIGH 整词 +{SCORE_HIGH} / MED 部分 +{SCORE_MED})")
    else:
        print("vertical: 未指定 —— 仅输出原始信号列表,不做相关性打分")
    print("X/Twitter: SKIPPED —— 未提供 API key,不猜(需要时自行补 BEARER token 后接入)。")

    items, errors = [], []
    src_ok = set()

    # ---- HN(前 30 条 item 并发抓)----
    try:
        print(f"[fetch] HN topstories 前 {HN_LIMIT} 条 …", flush=True)
        ids = fetch_json(HN_TOP)[:HN_LIMIT]
        with ThreadPoolExecutor(max_workers=10) as pool:
            for it in pool.map(lambda i: _safe(fetch_json, HN_ITEM.format(i)), ids):
                if isinstance(it, Exception):
                    errors.append(f"HN item: {it}")
                    continue
                if it and it.get("title"):
                    src_ok.add("HN")
                    items.append({"src": "HN", "title": it["title"],
                                  "url": it.get("url") or f"https://news.ycombinator.com/item?id={it.get('id')}",
                                  "meta": it.get("score", 0)})
    except Exception as e:
        errors.append(f"HN topstories: {e}")

    # ---- Reddit(6 sub 并发,失败明说不猜)----
    def fetch_sub(sub):
        try:
            data = _safe(fetch_json, f"https://www.reddit.com/r/{sub}/hot.json?limit={REDDIT_LIMIT}")
            if isinstance(data, Exception):
                raise data
            out = []
            for ch in data.get("data", {}).get("children", []):
                d = ch.get("data", {})
                if d.get("score", 0) > MIN_SCORE and d.get("title"):
                    out.append({"src": f"r/{sub}", "title": d["title"],
                                "url": "https://www.reddit.com" + d.get("permalink", ""),
                                "meta": d.get("score", 0)})
            return sub, out, None
        except Exception as e:
            return sub, [], e

    print(f"[fetch] Reddit {len(REDDIT_SUBS)} sub × hot{REDDIT_LIMIT}(score>{MIN_SCORE})…", flush=True)
    with ThreadPoolExecutor(max_workers=len(REDDIT_SUBS)) as pool:
        for sub, out, err in pool.map(fetch_sub, REDDIT_SUBS):
            if err:
                errors.append(f"r/{sub}: {err}")
            else:
                src_ok.add(f"r/{sub}")
                items.extend(out)

    for e in errors:
        print(f"[warn] 源失败: {e}", file=sys.stderr)

    if not items:
        print(f"[error] 无任何数据(可用源: {sorted(src_ok) or '无'};检查网络/被墙)。", file=sys.stderr)
        sys.exit(2)

    matched = 0
    print("-" * W)
    print(f"信号池:HN {HN_LIMIT} 条 topstories + Reddit {len(REDDIT_SUBS)} sub × hot{REDDIT_LIMIT}"
          f"(score>{MIN_SCORE} 才收);实际收得 {len(items)} 条:")
    for it in items:
        if tokens:
            sc, tag = relevance(it["title"], tokens)
            if sc:
                matched += 1
                print(f"  [{tag:<4} +{sc:<3}] ({it['src']}, score={it['meta']}) {it['title']}")
                print(f"            {it['url']}")
        else:
            print(f"  ({it['src']}, score={it['meta']}) {it['title']}")
    if tokens and not matched:
        print("  (无 HIGH/MED 匹配条目)")

    # ---- 关键词聚合 → 角度 ----
    cnt = Counter(w for it in items
                  for w in re.findall(r"[a-z]{4,}", it["title"].lower()) if w not in _STOP)
    top_kw = cnt.most_common(10)

    print("-" * W)
    if tokens:
        verdict = "PASS" if matched >= WHITELIST_MIN else "FAIL"
        print(f"白名单门槛:相关条目 {matched} / {WHITELIST_MIN} → {verdict}")
        if verdict == "FAIL":
            print("  低于门槛:该垂直当下热信号太薄,不建议按它立项长内容;")
            print("  可作为次要章节或观察名单,隔期复扫。")
        else:
            print("  过门槛:信号足够密,值得进入内容白名单排期。")
    else:
        print("白名单门槛:未指定 --vertical,不做判定(门槛定义:HN·Reddit 相关条目≥15)。")

    print("-" * W)
    print("跨源热词(Top 10,选题角度原料):")
    print("  " + ", ".join(f"{w}({n})" for w, n in top_kw))
    print("建议角度与适配平台:")
    angles = [
        ("把热词 × 自己产品做一个可复现实验,给出数字结论", "HN(技术深潜/Show HN 结构)"),
        ("拆解该趋势对普通用户的代价与收益,列操作步骤", "Reddit(痛点帖/AMA 结构,先答后链)"),
        ("汇总正反双方论据做一个决策指南", "HN+Reddit 双发,各按社区口味改写"),
    ]
    for i, (ang, plat) in enumerate(angles, 1):
        print(f"  {i}. {ang}")
        print(f"     适配平台:{plat}")
    print("=" * W)
    print("注意:HN/Reddit 只是免费信号源,X/Twitter 已明说跳过;结论阈值 "
          f"(≥{WHITELIST_MIN}) 是经验门槛,不是统计检验。")


if __name__ == "__main__":
    main()
