#!/usr/bin/env python3
"""link_graph.py — 内链图分析器(stdlib only,离线读 crawl.json,零网络)。

消费 site_crawl.py 产的 edges 内链图(规格 references/overview/pipeline-completeness.md
R3-4——此前 edges 零下游消费者;deeprank 口径可移植):
  ① PageRank:20 轮迭代 / 阻尼 0.85 / dangling 页质量均摊回全图(质量和恒 1)→
     Top/Bottom N(默认 20)+ 归一 0-10 分(最高页=10.0;归一分是人读权重序,非概率)。
  ② 点击深度直方图:>3 层占比(深埋页抓取与权重双弱,是内链架构首要体检项);
     不可达(depth=None,图上从首页走不到)单列。
  ③ 入链 0/1 页清单:零入链判定默认排除首页(path 为根)与 sitemap-only 页
     (source=sitemap——大站 sitemap 模式下爬虫兜底关闭,边欠采样会制造假孤儿;
     --include-sitemap-only 可配回),4xx/传输失败页不计(给死链加链无意义);
     单入链页=脆弱页(唯一入口一断即孤)。
  ④ 锚文本审计(R3-5 接线):带锚边的锚分布;精确匹配域名锚占比 > 阈值(默认
     0.60,--exact-threshold 可配,带锚边 <10 不告警防小样本噪音)→ 过度优化警告;
     泛化锚(click here/了解更多…)清单;Top 目标页的锚分布(同目标锚是否多样)。

输入:--crawl crawl.json(site_crawl.py --out 产物)。旧版 edges 无 anchor 键亦可——
锚审计按 0 带锚边处理,其余三件不受影响。输出:markdown 人读(默认)/ --json 结构化,
均打 stdout。退出码:0 正常;1 精确匹配域名锚过度优化警告触发;2 输入坏(文件缺失/
非 JSON/缺 pages·edges 键)。

用法: python3 link_graph.py --crawl crawl.json [--top 20] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from collections import Counter, defaultdict

SCHEMA_VERSION = 1
PR_ITERS = 20                     # PageRank 迭代轮数(规格钉死)
PR_DAMPING = 0.85                 # 阻尼系数(规格钉死)
DEFAULT_TOP = 20
EXACT_WARN_RATIO = 0.60           # 精确匹配域名锚占比告警阈值
MIN_ANCHORED_FOR_WARN = 10        # 带锚边少于此数不告警(小样本噪音)
TOP_ANCHORS_SHOWN = 10            # 锚分布/目标页展示条数
TOP_TARGETS_SHOWN = 10
GENERIC_ANCHORS = {               # 泛化锚(无语义,不传递主题信号;大小写不敏感)
    "click here", "here", "link", "this page", "this link", "more", "read more",
    "learn more", "details", "see more", "view more", "check this out", "go",
    "点击这里", "点这里", "点击", "这里", "了解更多", "查看更多", "阅读全文",
    "更多", "详情", "查看详情", "点击查看",
}


def load_crawl(path):
    """读 crawl.json 并校验最小契约(pages/edges 列表);坏输入抛 ValueError。"""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        raise ValueError("无法读取 %s: %s" % (path, e))
    except ValueError as e:
        raise ValueError("非 JSON 文件 %s: %s" % (path, e))
    if not isinstance(data, dict) or not isinstance(data.get("pages"), list) \
            or not isinstance(data.get("edges"), list):
        raise ValueError("%s 缺 pages/edges 列表(应为 site_crawl.py --out 产物)" % path)
    return data


def site_domain(report):
    """站点域:优先 crawl.json 的 domain 字段,缺则取首个页面 host。"""
    d = report.get("domain")
    if d:
        return d
    for p in report["pages"]:
        u = p.get("url") or ""
        h = urllib.parse.urlsplit(u).hostname
        if h:
            return h.lower()
    return ""


def is_home(url):
    """首页判定:path 为根(""或"/")——覆盖主站与子域根页。"""
    try:
        return urllib.parse.urlsplit(url or "").path.strip("/") == ""
    except ValueError:
        return False


def is_live(page):
    """活页:抓到且非 4xx/5xx(传输失败 status=None 也不算)。"""
    s = page.get("status")
    return s is not None and s < 400


# ---------------------------------------------------------------------------
# ① PageRank(迭代式;dangling 质量均摊,总和守恒 1)
# ---------------------------------------------------------------------------

def build_graph(report):
    """crawl.json → (pages, urls, edges):只留两端都在 pages 里的边(图外目标不计)。"""
    pages = report["pages"]
    urls = [p["url"] for p in pages if p.get("url")]
    known = set(urls)
    edges = []
    for e in report["edges"]:
        s, d = e.get("src"), e.get("dst")
        if s not in known:
            continue
        if d not in known and d and "?" in d:
            # 站内链接带跟踪参数(?iref= 等)、页面集是 sitemap 干净 URL 时,按去参数后的页面计
            # (与 site_crawl 孤儿判定同口径;2026-10-24 asahi.com 实测修前边数为 0)
            bare = urllib.parse.urlunsplit(urllib.parse.urlsplit(d)._replace(query="", fragment=""))
            if bare in known and bare != s:
                d = bare
        if d in known:
            edges.append((s, d))
    return pages, urls, edges


def pagerank(urls, edges, iters=PR_ITERS, damping=PR_DAMPING):
    """PageRank:均匀初值 1/N,迭代 iters 轮;无出链页(dangling)的质量按
    damping 均摊回所有页,保证 ΣPR=1。返回 {url: pr}。urls 顺序决定确定性。"""
    n = len(urls)
    if n == 0:
        return {}
    idx = {u: i for i, u in enumerate(urls)}
    outdeg = [0] * n
    incoming = [[] for _ in range(n)]
    for s, d in edges:
        si, di = idx[s], idx[d]
        outdeg[si] += 1
        incoming[di].append(si)
    pr = [1.0 / n] * n
    for _ in range(iters):
        dangling = sum(pr[i] for i in range(n) if outdeg[i] == 0)
        base = (1.0 - damping) / n + damping * dangling / n
        nxt = [base] * n
        for di, srcs in enumerate(incoming):
            share = 0.0
            for si in srcs:
                share += pr[si] / outdeg[si]
            nxt[di] += damping * share
        pr = nxt
    return {u: pr[i] for u, i in idx.items()}


def normalize_scores(pr):
    """归一 0-10:最高页=10.0(人读权重序,非概率);空图返回空。"""
    if not pr:
        return {}
    mx = max(pr.values())
    if mx <= 0:
        return {u: 0.0 for u in pr}
    return {u: round(10.0 * v / mx, 2) for u, v in pr.items()}


def rank_rows(pages, urls, edges, pr):
    """PageRank 排序行:降序(-pr, url 平局字典序保确定性);行含入链/深度供人读。"""
    incnt = Counter(d for _s, d in edges)
    by = {p.get("url"): p for p in pages}
    rows = [{"url": u, "pagerank": round(pr[u], 6),
             "norm_0_10": normalize_scores(pr)[u],
             "inlinks": incnt.get(u, 0),
             "depth": by.get(u, {}).get("depth")}
            for u in urls]
    rows.sort(key=lambda r: (-r["pagerank"], r["url"]))
    return rows


# ---------------------------------------------------------------------------
# ② 深度直方图 / ③ 入链 0/1 清单
# ---------------------------------------------------------------------------

def depth_histogram(pages):
    """→ (hist, deep, deep_pct):>3 层占比按全部页面计;不可达(depth=None)单列。"""
    hist = {"0": 0, "1": 0, "2": 0, "3": 0, ">3": 0, "unreachable": 0}
    for p in pages:
        d = p.get("depth")
        if d is None:
            hist["unreachable"] += 1
        elif d > 3:
            hist[">3"] += 1
        else:
            hist[str(d)] += 1
    deep = hist[">3"]
    pct = round(deep * 100.0 / len(pages), 1) if pages else 0.0
    return hist, deep, pct


def inlink_lists(report, include_sitemap_only=False):
    """入链 0/1 页清单(入链从 edges 现算,不信任快照字段)。
    零入链判定排除:首页(自然根)/ sitemap-only 页(默认,--include-sitemap-only
    配回)/ 非活页(4xx·传输失败)。返回 (zero, one, excluded, incnt)。"""
    pages, urls, edges = build_graph(report)
    incnt = Counter(d for _s, d in edges)
    by = {p.get("url"): p for p in pages}
    zero, one = [], []
    excluded = {"home": [], "sitemap_only": [], "dead": []}
    for u in urls:
        p = by.get(u, {})
        c = incnt.get(u, 0)
        if not is_live(p):
            if c == 0:
                excluded["dead"].append(u)
            continue
        if c == 0:
            if is_home(u):
                excluded["home"].append(u)
            elif p.get("source") == "sitemap" and not include_sitemap_only:
                excluded["sitemap_only"].append(u)
            else:
                zero.append(u)
        elif c == 1:
            one.append(u)
    return zero, one, excluded, incnt


# ---------------------------------------------------------------------------
# ④ 锚文本审计
# ---------------------------------------------------------------------------

def _domain_anchor_key(a):
    """锚文本 → 域名形态键:去 scheme/www 前缀与尾部标点,小写。"""
    t = (a or "").strip().lower()
    t = re.sub(r"^https?://", "", t)
    t = re.sub(r"^www\.", "", t)
    return t.rstrip("/.,;:!)")


def is_exact_match_anchor(anchor, domain):
    """精确匹配域名锚:归一后等于域名或以其子域结尾(www. 变体/裸域皆算)。"""
    if not domain:
        return False
    k = _domain_anchor_key(anchor)
    return bool(k) and (k == domain.lower() or k.endswith("." + domain.lower()))


def anchor_audit(report, domain, threshold=EXACT_WARN_RATIO):
    """锚文本审计:整体分布 + 精确匹配域名占比(>threshold 且带锚边 ≥
    MIN_ANCHORED_FOR_WARN → 警告)+ 泛化锚清单 + Top 目标页锚分布。"""
    _pages, _urls, edges = build_graph(report)
    anchored = [e for e in report["edges"]
                if (e.get("anchor") or "").strip()
                and e.get("src") and e.get("dst")]
    counter = Counter(e["anchor"].strip() for e in anchored)
    total = len(anchored)
    exact_n = sum(1 for e in anchored if is_exact_match_anchor(e["anchor"], domain))
    exact_pct = round(exact_n * 100.0 / total, 1) if total else 0.0
    warn = total >= MIN_ANCHORED_FOR_WARN and exact_n * 1.0 / max(total, 1) > threshold
    distribution = [{"anchor": a, "count": c, "pct": round(c * 100.0 / total, 1)}
                    for a, c in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
                    [:TOP_ANCHORS_SHOWN]]
    generic_counts = Counter()
    for a, c in counter.items():     # 泛化锚大小写不敏感归并("Click Here"→click here)
        la = a.strip().lower()
        if la in GENERIC_ANCHORS:
            generic_counts[la] += c
    generic = [{"anchor": a, "count": c}
               for a, c in sorted(generic_counts.items(), key=lambda kv: (-kv[1], kv[0]))]
    tgt = Counter(e["dst"] for e in anchored)
    by_target = []
    for dst, n in sorted(tgt.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_TARGETS_SHOWN]:
        tcounter = Counter(e["anchor"].strip() for e in anchored if e["dst"] == dst)
        by_target.append({"target": dst, "anchored_inlinks": n,
                          "anchors": [{"anchor": a, "count": c}
                                      for a, c in sorted(tcounter.items(),
                                                         key=lambda kv: (-kv[1], kv[0]))[:5]]})
    warnings = []
    if warn:
        warnings.append("精确匹配域名锚占比 %.1f%%(%.0f%% 阈值):过度优化风险——"
                        "丰富描述性锚/关键词变体锚" % (exact_pct, threshold * 100))
    return {"total_edges": len(edges), "anchored_edges": total,
            "distribution": distribution,
            "exact_match": {"count": exact_n, "pct": exact_pct,
                            "threshold": threshold, "warn": warn,
                            "min_sample": MIN_ANCHORED_FOR_WARN},
            "generic": generic, "by_target": by_target, "warnings": warnings}


# ---------------------------------------------------------------------------
# 汇总 / 渲染 / CLI
# ---------------------------------------------------------------------------

def build_payload(report, top_n=DEFAULT_TOP, exact_threshold=EXACT_WARN_RATIO,
                  include_sitemap_only=False):
    pages, urls, edges = build_graph(report)
    domain = site_domain(report)
    pr = pagerank(urls, edges)
    rows = rank_rows(pages, urls, edges, pr)
    hist, deep, deep_pct = depth_histogram(pages)
    zero, one, excluded, _incnt = inlink_lists(report, include_sitemap_only)
    anchors = anchor_audit(report, domain, exact_threshold)
    warnings = list(anchors["warnings"])
    disc = report.get("discovery") or {}
    counts = disc.get("counts") or {}
    if disc.get("mode") in ("sitemap", "robots+sitemap") and not counts.get("crawl") \
            and report.get("orphans"):
        warnings.append("sitemap-only 爬取(爬虫兜底关闭):内链边可能欠采样,"
                        "孤儿/入链结论按 --include-sitemap-only 复核")
    if report.get("orphans_partial"):
        warnings.append("site_crawl 被 --max 截断:孤儿与入链只在已抓样本内计算,不等于站内结论")
    return {
        "schema_version": SCHEMA_VERSION,
        "site": domain,
        "input": {"pages": len(pages), "edges": len(edges),
                  "anchored_edges": anchors["anchored_edges"]},
        "pagerank": {
            "iterations": PR_ITERS, "damping": PR_DAMPING,
            "top": rows[:top_n],
            "bottom": list(reversed(rows[-top_n:])),   # 升序,最低在前
            "stats": {"min": round(min(pr.values()), 6) if pr else None,
                      "max": round(max(pr.values()), 6) if pr else None,
                      "sum": round(sum(pr.values()), 6) if pr else None},
        },
        "depth": {"histogram": hist, "deep_pages": deep, "deep_pct": deep_pct,
                  "unreachable": hist["unreachable"]},
        "inlinks": {"zero": zero, "one": one, "excluded": excluded,
                    "include_sitemap_only": include_sitemap_only},
        "anchors": anchors,
        "warnings": warnings,
    }, rows


def _fmt_row(r, i):
    return "%2d. %s pr=%.4f 归一=%.2f 入链=%d 深=%s" % (
        i, r["url"], r["pagerank"], r["norm_0_10"], r["inlinks"],
        r["depth"] if r["depth"] is not None else "不可达")


def render_markdown(p, rows, top_n):
    L = ["## link_graph: %s" % p["site"], ""]
    L.append("- 页面 %d / 内链边 %d(带锚 %d)/ 孤儿 %d" % (
        p["input"]["pages"], p["input"]["edges"], p["input"]["anchored_edges"],
        len(p.get("orphans") or []) if "orphans" in p else "-"))
    pr = p["pagerank"]
    L.append("")
    L.append("### PageRank(%d 轮,d=%.2f,归一 0-10;Σ=%.4f)" % (
        pr["iterations"], pr["damping"], pr["stats"]["sum"] or 0.0))
    L.append("")
    L.append("Top %d:" % min(top_n, len(rows)))
    L += [_fmt_row(r, i + 1) for i, r in enumerate(pr["top"])]
    L.append("")
    L.append("Bottom %d(最低在前):" % min(top_n, len(rows)))
    L += [_fmt_row(r, i + 1) for i, r in enumerate(pr["bottom"])]
    d = p["depth"]
    h = d["histogram"]
    L.append("")
    L.append("### 深度直方图")
    L.append("- 0 层 %s / 1 层 %s / 2 层 %s / 3 层 %s / >3 层 %s(%.1f%%)/ 不可达 %s"
             % (h["0"], h["1"], h["2"], h["3"], h[">3"], d["deep_pct"],
                h["unreachable"]))
    il = p["inlinks"]
    L.append("")
    L.append("### 入链 0/1")
    L.append("- 零入链 %d 页(排除首页 %d/sitemap-only %d/死页 %d%s):%s" % (
        len(il["zero"]), len(il["excluded"]["home"]), len(il["excluded"]["sitemap_only"]),
        len(il["excluded"]["dead"]),
        ",含 sitemap-only" if il["include_sitemap_only"] else "",
        ", ".join(il["zero"][:20]) if il["zero"] else "无"))
    L.append("- 单入链(脆弱页)%d 页:%s" % (
        len(il["one"]), ", ".join(il["one"][:20]) if il["one"] else "无"))
    a = p["anchors"]
    L.append("")
    L.append("### 锚文本审计")
    L.append("- 带锚边 %d/%d;精确匹配域名锚 %d(%.1f%%,阈值 %.0f%%)" % (
        a["anchored_edges"], a["total_edges"], a["exact_match"]["count"],
        a["exact_match"]["pct"], a["exact_match"]["threshold"] * 100))
    if a["distribution"]:
        L.append("- 锚分布 Top: " + ", ".join(
            "%s×%d(%.1f%%)" % (d["anchor"], d["count"], d["pct"])
            for d in a["distribution"]))
    if a["generic"]:
        L.append("- 泛化锚(无语义): " + ", ".join(
            "%s×%d" % (g["anchor"], g["count"]) for g in a["generic"]))
    for t in a["by_target"][:5]:
        L.append("- 目标 %s ← %s" % (t["target"], ", ".join(
            "\"%s\"×%d" % (x["anchor"], x["count"]) for x in t["anchors"])))
    for w in p.get("warnings", []):
        L.append("- ⚠ %s" % w)
    return "\n".join(L)


USAGE_EPILOG = """\
输入:site_crawl.py --out 产物 crawl.json(旧版无 anchor 键亦可,锚审计按 0 带锚处理)。
①PageRank 20 轮/阻尼 0.85/dangling 均摊 → Top/Bottom + 归一 0-10;②深度直方图
(>3 层占比);③入链 0/1 清单(零入链默认排除首页与 sitemap-only 页,可配);
④锚文本审计(精确匹配域名 >60% 警告过度优化 + 泛化锚清单 + 目标页锚分布)。
输出:markdown(默认)/ --json。退出码:0 正常 / 1 锚过度优化警告 / 2 输入坏。\
"""


def build_parser():
    ap = argparse.ArgumentParser(
        prog="link_graph.py",
        description="内链图分析器:crawl.json edges → PageRank 排序/深度直方图/入链 0-1 "
                    "清单/锚文本审计(stdlib only,离线;规格 pipeline-completeness.md R3-4)",
        epilog=USAGE_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crawl", required=True, metavar="FILE",
                    help="site_crawl.py 产物 crawl.json")
    ap.add_argument("--top", type=int, default=DEFAULT_TOP, metavar="N",
                    help="PageRank Top/Bottom 展示数(默认 %d)" % DEFAULT_TOP)
    ap.add_argument("--exact-threshold", dest="exact_threshold", type=float,
                    default=EXACT_WARN_RATIO, metavar="R",
                    help="精确匹配域名锚占比告警阈值(默认 %.2f)" % EXACT_WARN_RATIO)
    ap.add_argument("--include-sitemap-only", dest="include_sitemap_only",
                    action="store_true",
                    help="零入链清单计入 sitemap-only 页(默认排除:大站 sitemap 模式边欠采样防假孤儿)")
    ap.add_argument("--json", action="store_true", help="结构化 JSON 打 stdout(替代 markdown)")
    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.top <= 0:
        ap.error("--top 必须为正整数")
    if not (0.0 <= args.exact_threshold <= 1.0):
        ap.error("--exact-threshold 须在 [0,1]")
    try:
        report = load_crawl(args.crawl)
    except ValueError as e:
        sys.stderr.write("[link_graph] 输入错: %s\n" % e)
        return 2
    payload, rows = build_payload(report, top_n=args.top,
                                  exact_threshold=args.exact_threshold,
                                  include_sitemap_only=args.include_sitemap_only)
    payload["orphans"] = report.get("orphans") or []
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print(render_markdown(payload, rows, args.top))
    for w in payload.get("warnings", []):
        sys.stderr.write("[link_graph] ⚠ %s\n" % w)
    return 1 if payload["anchors"]["exact_match"]["warn"] else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        sys.exit(130)
