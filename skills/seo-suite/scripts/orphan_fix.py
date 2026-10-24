#!/usr/bin/env python3
"""orphan_fix.py — 孤儿页内链修复规划器(stdlib only,离线读 crawl.json,零网络)。

内链架构管线的执行计划件(规格 references/overview/pipeline-completeness.md R3-6):
site_crawl.py 产孤儿清单,本工具把"孤儿 × 同主题候选源页"配成可执行的加链清单,
作为 hub-spoke 内链规划的直接输入。

被重定向的 URL(final_url≠url 或 3xx)不算孤儿,不给它们出加链建议。
候选源页规则(目录前缀聚类):
  取与孤儿 URL 路径首段相同(如 /blog/deep → "blog")的已链出活页
  (out_internal≥1、2xx/3xx、非孤儿自身),按入链数降序(平局按出链数/URL)
  每孤儿最多 3 候选——同目录=同主题簇,从簇内权威页加链最自然;
  无同目录候选时不做跨主题硬配(空候选 + 提示:该孤儿需要导航级入口或新 hub,
  散链跨主题反而稀释相关性)。

建议锚文本:取孤儿 title 首段(品牌分隔符 | · – — - :: 之前),去空白截 60 字;
  title 缺失时回退路径末段人类化(-/_ → 空格)。

输出:"源页 → 孤儿页 → 建议锚文本" markdown 清单(每候选一行)/ --json 结构化;
--max 限制处理孤儿数(默认 50,防大站刷屏)。
退出码:0 正常(规划工具,发现孤儿不算失败);2 输入坏(文件缺失/非 JSON/缺键)。

用法: python3 orphan_fix.py --crawl crawl.json [--max 50] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from collections import defaultdict

SCHEMA_VERSION = 1
MAX_CANDIDATES = 3                # 每孤儿候选源页上限(规格钉死)
DEFAULT_MAX = 50                  # 处理孤儿数上限
ANCHOR_MAX_LEN = 60               # 建议锚文本截断
TITLE_SEPS = (" | ", " · ", " – ", " — ", " - ", " :: ")


def load_crawl(path):
    """读 crawl.json 并校验最小契约;坏输入抛 ValueError(与 link_graph 同口径)。"""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        raise ValueError("无法读取 %s: %s" % (path, e))
    except ValueError as e:
        raise ValueError("非 JSON 文件 %s: %s" % (path, e))
    if not isinstance(data, dict) or not isinstance(data.get("pages"), list):
        raise ValueError("%s 缺 pages 列表(应为 site_crawl.py --out 产物)" % path)
    if not isinstance(data.get("orphans"), list):
        data["orphans"] = []
    return data


def first_segment(url):
    """URL 路径首段(目录前缀聚类的主题键):/blog/a → "blog";根页 → ""。"""
    try:
        path = urllib.parse.urlsplit(url or "").path or "/"
    except ValueError:
        return ""
    stripped = path.strip("/")
    return stripped.split("/")[0] if stripped else ""


def humanize_segment(seg):
    """路径段人类化:coffee-grinders_2026 → Coffee Grinders 2026。"""
    words = [w for w in seg.replace("_", "-").split("-") if w]
    return " ".join(words)


def suggest_anchor(title, url):
    """建议锚文本:取 title 品牌分隔符前首段,去空白截 60 字;缺 title 回退
    路径末段人类化,再回退 host(根页)——保证永不为空,加链必须带锚。"""
    text = (title or "").strip()
    if text:
        for sep in TITLE_SEPS:
            if sep in text:
                text = text.split(sep)[0]
                break
        text = " ".join(text.split())
    if not text:
        try:
            last = urllib.parse.urlsplit(url or "").path.rstrip("/").rsplit("/", 1)[-1]
        except ValueError:
            last = ""
        text = humanize_segment(last)
    if not text:
        try:
            text = urllib.parse.urlsplit(url or "").netloc
        except ValueError:
            text = ""
    return (text[:ANCHOR_MAX_LEN].rstrip()) or "(未命名页面)"


def is_live(page):
    s = page.get("status")
    return s is not None and s < 400


def is_redirected(page):
    """被重定向的 URL(如 www./api. 子域 301 到主站)不是孤儿:内链该指向目标页,不给它加链。"""
    s = page.get("status")
    if s is not None and 300 <= s < 400:
        return True
    fu = page.get("final_url")
    return bool(fu) and fu != page.get("url")


def build_plan(report, max_orphans=DEFAULT_MAX):
    """孤儿清单 → 加链计划:每孤儿 ≤MAX_CANDIDATES 个同目录候选源页(入链降序)。"""
    pages = report["pages"]
    by = {p.get("url"): p for p in pages if p.get("url")}
    # 旧版 site_crawl 会把重定向页写进 orphans:这里再剔一次
    orphans = [u for u in (report.get("orphans") or []) if not is_redirected(by.get(u) or {})]
    orphan_set = set(orphans)
    # 预聚类:路径首段 → 已链出活页(非孤儿)
    clusters = defaultdict(list)
    for p in pages:
        u = p.get("url")
        if not u or u in orphan_set or not is_live(p):
            continue
        if (p.get("out_internal") or 0) < 1:
            continue                                  # 已链出页=自然插入点
        clusters[first_segment(u)].append(p)
    for seg in clusters:
        clusters[seg].sort(key=lambda p: (-(p.get("inlinks") or 0),
                                          -(p.get("out_internal") or 0), p["url"]))
    plans = []
    for u in orphans[:max_orphans]:
        p = by.get(u) or {}
        topic = first_segment(u)
        cands = clusters.get(topic, [])[:MAX_CANDIDATES]
        plans.append({
            "orphan": u,
            "topic": topic or "(根)",
            "title": p.get("title"),
            "depth": p.get("depth"),
            "suggested_anchor": suggest_anchor(p.get("title"), u),
            "candidates": [{"url": c["url"], "inlinks": c.get("inlinks") or 0,
                            "out_internal": c.get("out_internal") or 0}
                           for c in cands],
        })
    return plans, len(orphans)


def render_markdown(payload):
    L = ["## orphan_fix: %s" % payload["site"], ""]
    if payload.get("orphans_partial"):
        L.append("- ⚠ 上游 site_crawl 被 --max 截断:孤儿只在已抓样本内判定,改内链前先全量抓取复核")
    L.append("- 孤儿 %d 个,处理 %d(--max %d);每孤儿 ≤%d 候选源页(同目录前缀聚类,"
             "入链降序)" % (payload["orphans_total"], payload["processed"],
                            payload["max"], payload["max_candidates"]))
    no_cand = 0
    for pl in payload["plans"]:
        L.append("")
        if pl["title"]:
            L.append("### %s(title: %s)" % (pl["orphan"], pl["title"]))
        else:
            L.append("### %s" % pl["orphan"])
        if pl["candidates"]:
            for c in pl["candidates"]:
                L.append("- 源页 %s(入链 %d)→ 孤儿 %s → 建议锚文本 \"%s\""
                         % (c["url"], c["inlinks"], pl["orphan"], pl["suggested_anchor"]))
        else:
            no_cand += 1
            L.append("- ⚠ 无同主题候选源页(%s 目录无已链出活页)——考虑导航级入口"
                     "或新建 hub,不做跨主题硬配" % pl["topic"])
    covered = payload["processed"] - no_cand
    if payload["plans"]:
        L.append("")
        L.append("- 汇总: %d/%d 孤儿有同目录候选;%d 个需导航/hub 级入口"
                 % (covered, payload["processed"], no_cand))
    return "\n".join(L)


USAGE_EPILOG = """\
候选源页=与孤儿路径首段相同的已链出活页(out_internal≥1),入链降序取前 3;
无同目录候选时空缺提示(需导航/hub 级入口),不跨主题硬配。
建议锚文本=孤儿 title 品牌分隔符前首段(截 60 字;缺 title 回退路径末段人类化)。
输出:markdown(默认)/ --json;--max 限处理孤儿数(默认 50)。
退出码:0 正常(规划工具,发现孤儿不算失败)/ 2 输入坏。\
"""


def build_parser():
    ap = argparse.ArgumentParser(
        prog="orphan_fix.py",
        description="孤儿页内链修复规划:crawl.json orphans × 同目录候选源页 → "
                    "\"源页→孤儿页→建议锚文本\"清单(hub-spoke 规划输入;规格 "
                    "pipeline-completeness.md R3-6)",
        epilog=USAGE_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crawl", required=True, metavar="FILE",
                    help="site_crawl.py 产物 crawl.json")
    ap.add_argument("--max", type=int, default=DEFAULT_MAX, metavar="N",
                    help="处理孤儿数上限(默认 %d)" % DEFAULT_MAX)
    ap.add_argument("--json", action="store_true", help="结构化 JSON 打 stdout(替代 markdown)")
    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.max <= 0:
        ap.error("--max 必须为正整数")
    try:
        report = load_crawl(args.crawl)
    except ValueError as e:
        sys.stderr.write("[orphan_fix] 输入错: %s\n" % e)
        return 2
    plans, total = build_plan(report, max_orphans=args.max)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "site": report.get("domain") or "",
        "orphans_total": total,
        "processed": len(plans),
        "max": args.max,
        "max_candidates": MAX_CANDIDATES,
        "plans": plans,
        "orphans_partial": bool(report.get("orphans_partial")),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print(render_markdown(payload))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        sys.exit(130)
