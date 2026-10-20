#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""multimodal_report.py — GSC 图片/视频流量代理报告(视觉搜索候选页 + video-geo 接线;stdlib only)。

用法:
  python3 multimodal_report.py --gsc gsc.csv [--videos videos.csv]
      [--top 15] [--min-impr 100] [--ctr 0.03] [--json]

诚实口径(本脚本按落地页目录特征代理图片/视频流量;Search Console 2026-09-24 起有 multimodal 筛选,能导出时优先用它——references/content/image-search-seo.md 第一节):
  * gsc.csv 含 Search Appearance 列 → 精确口径:appearance 命中 image|video|lens|
    circle|multimodal 的行按页聚合(2026-09-24 起 GSC Performance 有 multimodal 过滤器,
    用它导出可去 [est]);
  * 无该列 → 代理口径,全部数字标 [est]:按 landing page 目录特征分类
      图片向  /img|images|photo(s)|gallery|media|cdn|asset(s)/ 或产品目录
              /p|product(s)|item(s)|listing(s)|collection(s)|c|category|shop|catalog/
      视频向  /video(s)|watch|tv|embed|short(s)|reel(s)|clip(s)|episode(s)|podcast(s)/
  列名宽容:page/landing page/url + clicks + impressions(+date 可无);数字带千分位可。

输出三节:
  §1 视觉流量代理总览(图片向/视频向页面数与 clicks/impressions 及全站占比)
  §2 视觉搜索候选页——高曝光低点击(曝光 ≥ --min-impr 且 CTR < --ctr,默认 3%,本套件口径,
     建议换成本站同类页的 CTR)的图床/产品目录页清单,按曝光排序
  §3 video-geo-guide 接线建议(按数据形态生成:视频页在场→VideoObject/字幕/章节;
     videos.csv 孤儿视频→自建 watch page;无 Search Appearance→GSC multimodal 重导出)

退出码: 0 正常(候选非空不是失败——本工具是报告器) / 2 输入错(文件缺/列缺)。"""
import argparse
import csv
import json
import os
import re
import sys
import urllib.parse

SCHEMA_VERSION = 1
IMAGE_PATH_RE = re.compile(
    r"/(?:img|images?|photos?|gallery|galleries|media|cdn|assets?|pics?)/", re.I)
CATALOG_PATH_RE = re.compile(
    r"/(?:p|products?|items?|listings?|collections?|c|categor(?:y|ies)|shop|catalog)/", re.I)
VIDEO_PATH_RE = re.compile(
    r"/(?:videos?|watch|tv|embed|shorts?|reels?|clips?|episodes?|podcasts?|vod)/", re.I)
APPEARANCE_VISUAL_RE = re.compile(r"image|video|lens|circle|multimodal", re.I)
APPEARANCE_VIDEO_RE = re.compile(r"video", re.I)

PAGE_KEYS = ("page", "landing page", "landing_page", "url")
CLICK_KEYS = ("clicks",)
IMPR_KEYS = ("impressions",)
APPEAR_KEYS = ("search appearance", "search_appearance", "appearance")
VIDEO_URL_KEYS = ("url", "video", "video url", "video_url", "page", "landing page", "link")


def die(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def read_csv(path):
    if not os.path.exists(path):
        die("文件不存在: %s" % path)
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return [{k.strip().lower(): (v or "").strip() for k, v in r.items() if k} for r in rows]


def col(row, names):
    for n in names:
        for k in row:
            if k == n or k.startswith(n):
                v = row[k]
                if v:
                    return v
    return ""


def num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def norm_url(u):
    u = (u or "").strip()
    if not u:
        return ""
    if "://" not in u:
        u = "https://" + u
    p = urllib.parse.urlsplit(u)
    path = re.sub(r"/+$", "", p.path or "")
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), path, "", ""))


def classify_path(page_url):
    path = (urllib.parse.urlsplit(page_url).path or "") if "://" in page_url else page_url
    if VIDEO_PATH_RE.search(path):
        return "video"
    if IMAGE_PATH_RE.search(path):
        return "image"
    if CATALOG_PATH_RE.search(path):
        return "catalog"
    return None


def load_gsc(path):
    rows = read_csv(path)
    if not rows:
        die("gsc.csv 是空表: %s" % path)
    probe = rows[0]
    if not col(probe, PAGE_KEYS):
        die("gsc.csv 缺 Page/Landing page 列(需要 Page+Clicks+Impressions)")
    if not col(probe, CLICK_KEYS) or not col(probe, IMPR_KEYS):
        die("gsc.csv 缺 Clicks/Impressions 列(需要 Page+Clicks+Impressions)")
    has_appearance = bool(col(probe, APPEAR_KEYS))
    return rows, has_appearance


def aggregate(rows, has_appearance):
    """→ (pages{norm_page:{clicks,impr,types:set,appearances:set}}, totals, visual_rows_n)"""
    pages, tot_c, tot_i, visual_rows = {}, 0.0, 0.0, 0
    for r in rows:
        page = col(r, PAGE_KEYS)
        if not page:
            continue
        c, i = num(col(r, CLICK_KEYS)), num(col(r, IMPR_KEYS))
        tot_c += c
        tot_i += i
        appear = col(r, APPEAR_KEYS) if has_appearance else ""
        is_visual = bool(APPEARANCE_VISUAL_RE.search(appear)) if has_appearance else True
        if has_appearance and not is_visual:
            continue
        visual_rows += 1
        d = pages.setdefault(norm_url(page), {"page": page, "clicks": 0.0,
                                              "impressions": 0.0,
                                              "types": set(), "appearances": set()})
        d["clicks"] += c
        d["impressions"] += i
        if has_appearance and appear:
            d["appearances"].add(appear)
            d["types"].add("video" if APPEARANCE_VIDEO_RE.search(appear) else "image")
        else:
            t = classify_path(page)
            if t:
                d["types"].add(t)
    return pages, {"clicks": tot_c, "impressions": tot_i}, visual_rows


def pct(x, total):
    return (x / total * 100) if total else 0.0


def build_report(pages, totals, has_appearance, args):
    basis = "appearance" if has_appearance else "directory_est"
    est = "" if has_appearance else "[est]"
    image_pages = [d for d in pages.values() if d["types"] & {"image", "catalog"}]
    video_pages = [d for d in pages.values() if "video" in d["types"]]

    def agg(subset):
        return (sum(d["clicks"] for d in subset), sum(d["impressions"] for d in subset))

    img_c, img_i = agg(image_pages)
    vid_c, vid_i = agg(video_pages)

    candidates = []
    for d in pages.values():
        if not d["types"]:
            continue
        if d["impressions"] >= args.min_impr and d["impressions"] > 0:
            ctr = d["clicks"] / d["impressions"]
            if ctr < args.ctr:
                candidates.append({
                    "page": d["page"], "clicks": int(d["clicks"]),
                    "impressions": int(d["impressions"]), "ctr": round(ctr, 4),
                    "types": sorted(d["types"]),
                    "est": not has_appearance,
                })
    candidates.sort(key=lambda x: -x["impressions"])
    candidates = candidates[:args.top]

    overview = {
        "basis": basis, "pages_total": len(pages),
        "image_pages": len(image_pages),
        "image_clicks": int(img_c), "image_impressions": int(img_i),
        "image_clicks_share_pct": round(pct(img_c, totals["clicks"]), 1),
        "image_impressions_share_pct": round(pct(img_i, totals["impressions"]), 1),
        "video_pages": len(video_pages),
        "video_clicks": int(vid_c), "video_impressions": int(vid_i),
        "video_clicks_share_pct": round(pct(vid_c, totals["clicks"]), 1),
        "video_impressions_share_pct": round(pct(vid_i, totals["impressions"]), 1),
        "site_totals": {"clicks": int(totals["clicks"]),
                        "impressions": int(totals["impressions"])},
        "threshold": {"min_impressions": args.min_impr, "ctr": args.ctr},
    }
    return overview, candidates, image_pages, video_pages


def video_wiring(args, video_pages, candidates, has_appearance):
    tips = []
    orphan_videos, unregistered = [], []
    if args.videos:
        vrows = read_csv(args.videos)
        gsc_pages = {d["page"] for d in video_pages}
        vurls = []
        for r in vrows:
            u = col(r, VIDEO_URL_KEYS)
            if u:
                vurls.append(u)
        for u in vurls:
            if norm_url(u) not in {norm_url(g) for g in gsc_pages}:
                orphan_videos.append(u)
        registered_norm = {norm_url(u) for u in vurls}
        unregistered = [g for g in gsc_pages if norm_url(g) not in registered_norm]
        if vurls:
            tips.append("videos.csv 登记 %d 条;孤儿 %d 条(无 GSC 落地页)——孤儿视频自建 "
                        "watch page 承接(transcript 全文页是播客/视频的 Google 流量主入口)"
                        % (len(vurls), len(orphan_videos)))
        else:
            tips.append("videos.csv 无可用 URL 列(需要 url/video 列)——跳过 join")
    if video_pages:
        tips.append("GSC 有 %d 个视频向落地页:VideoObject 必做(嵌 YouTube 用 embedUrl 版;"
                    "自托管再 + 视频 sitemap contentUrl 版——video-geo-guide 决策口诀:双做不叠加)"
                    % len(video_pages))
        tips.append("上传人工校对字幕(transcript 是唯一可控文本层——41%% 被引视频播放量<1000,"
                    "文本可及性才是被引门槛)+描述时间戳章节(Gemini 片内引用定位)")
    else:
        tips.append("GSC 未见视频向落地页——视频层接线从 YouTube 嵌入页的 VideoObject(embedUrl 版)起步")
    if candidates:
        tips.append("高曝光低 CTR 页(候选 %d 个):图片向查 og:image/schema image/"
                    "primaryImageOfPage 三处同 URL+≥1200px+robots 勿拦图目录;视频向把关键词"
                    "放进标题前 40-50 字符且缩略图文字不与标题重复" % len(candidates))
    if not has_appearance:
        tips.append("本次为 [est] 代理口径:GSC Performance 用 multimodal 过滤器"
                    "(2026-09-24 起)重导出,可换精确口径")
    return tips, orphan_videos, unregistered


def render(overview, candidates, tips, gsc_path):
    print("=" * 64)
    print("multimodal_report | %s" % gsc_path)
    if overview["basis"] == "appearance":
        print("口径: Search Appearance 列在场 → 精确(appearance 过滤)")
    else:
        print("口径: 按落地页目录特征代理图片/视频流量(能导出 Search Console multimodal 筛选时优先用它)——数字均 [est]")
    print("\n-- §1 视觉流量代理总览 --")
    est = "[est]" if overview["basis"] == "directory_est" else ""
    print("图片向页面%s: %d 页 | clicks %d(全站 %.1f%%)| impressions %d(%.1f%%)" % (
        est and " " + est or "",
        overview["image_pages"], overview["image_clicks"],
        overview["image_clicks_share_pct"], overview["image_impressions"],
        overview["image_impressions_share_pct"]))
    print("视频向页面%s: %d 页 | clicks %d(全站 %.1f%%)| impressions %d(%.1f%%)" % (
        est and " " + est or "",
        overview["video_pages"], overview["video_clicks"],
        overview["video_clicks_share_pct"], overview["video_impressions"],
        overview["video_impressions_share_pct"]))
    print("(全站 %s: clicks %d / impressions %d)" % (
        "含非视觉页" if overview["basis"] == "appearance" else "全页",
        overview["site_totals"]["clicks"], overview["site_totals"]["impressions"]))
    print("候选阈值: 曝光 ≥%d 且 CTR <%.1f%%(图搜常态 CTR ~3%% 口径)" % (
        overview["threshold"]["min_impressions"], overview["threshold"]["ctr"] * 100))
    print("\n-- §2 视觉搜索候选页(高曝光低点击,TOP %d) --" % len(candidates))
    if not candidates:
        print("(无候选)")
    for c in candidates:
        print("%-58s impr %-8d clicks %-6d CTR %.2f%%  %s%s" % (
            c["page"][:58], c["impressions"], c["clicks"], c["ctr"] * 100,
            "+".join(c["types"]), "[est]" if c["est"] else ""))
    print("\n-- §3 video-geo-guide 接线建议 --")
    for i, t in enumerate(tips, 1):
        print("%d. %s" % (i, t))


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="multimodal_report.py",
        description="GSC 图片/视频流量代理报告:视觉搜索候选页清单 + video-geo-guide 接线建议(stdlib)")
    ap.add_argument("--gsc", required=True,
                    help="GSC Performance 导出 CSV(Page+Clicks+Impressions;"
                         "含 Search Appearance 列则用精确口径,否则目录特征 [est])")
    ap.add_argument("--videos", help="可选视频清单 CSV(url/video 列)——与 GSC 落地页 join 找孤儿")
    ap.add_argument("--top", type=int, default=15, help="候选页清单上限(默认 15)")
    ap.add_argument("--min-impr", type=int, default=100, help="候选曝光阈值(默认 100)")
    ap.add_argument("--ctr", type=float, default=0.03, help="候选 CTR 上限(默认 0.03,本套件口径;建议换成本站同类页的 CTR)")
    ap.add_argument("--json", dest="as_json", action="store_true", help="结构化输出")
    args = ap.parse_args(argv)

    rows, has_appearance = load_gsc(args.gsc)
    pages, totals, visual_rows = aggregate(rows, has_appearance)
    overview, candidates, image_pages, video_pages = build_report(pages, totals, has_appearance, args)
    tips, orphan_videos, unregistered = video_wiring(args, video_pages, candidates, has_appearance)

    if args.as_json:
        print(json.dumps({
            "schema_version": SCHEMA_VERSION, "tool": "multimodal_report",
            "gsc": args.gsc, "videos": args.videos or "",
            "overview": overview,
            "candidates": candidates,
            "orphan_videos": orphan_videos[:50],
            "gsc_video_pages_unregistered": unregistered[:50],
            "video_wiring": tips,
        }, ensure_ascii=False, indent=1))
    else:
        render(overview, candidates, tips, args.gsc)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.stderr.write("\n[interrupted]\n")
        sys.exit(130)
