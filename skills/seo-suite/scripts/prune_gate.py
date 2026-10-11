#!/usr/bin/env python3
"""零点击页退役/合并决策闸(prune_gate;stdlib only)。

规格:skills/seo-suite/references/overview/pipeline-completeness.md R3-10
(零点击页×入链×外链三查→prune/merge/watch 三判,外链>0 或有排名词 NO-GO)。
口径:候选页 = in_serps(GSC impressions>0)且非 with_clicks(clicks=0)——即
"在搜索结果里露过脸但从没人点"的页;判定要求 GSC 导出窗口≥90 天(默认 90,
--window-days 可调;窗口长度无法从导出文件推断,由调用方保证,输出注明)。

三查(每页,缺数据=该查不可用,不猜):
  ① 入链  --crawl(site_crawl.py 的 crawl.json:edges[]{src,dst} 计数;
          edges 为空时回落 pages[].inlinks 字段;两者皆缺 → 入链不可用)
  ② 外链  --backlinks(带 target 列的外链导出 CSV:GSC Links 简易表
          [无表头两列=引荐页,目标页]/Ahrefs/Semrush 带 Target 列变体;
          无 target 列(如 backlink_import.py 统一 schema 只有引荐侧)→
          按页外链核对不可用 → 保守 watch)
  ③ 排名词 --gsc 有 Query+Position 列的导出(query 级):该页存在
          Position≤20 的 query 即有排名词(平均排名≤20 视作尚有排面)。

判定(决策表,按序短路):
  外链>0 或 排名词>0        → NO-GO(红线,列原因——有外部资产/排面的页绝不动)
  红线两查任一不可用         → watch(缺证据不下刀)
  入链不可用                → watch
  入链≤2                    → prune(410:近孤儿页,内链资产可弃)
  入链>2 且同目录有其他页    → merge(301 目标=同目录最高入链页,平票取 URL 序)
  入链>2 但同目录无候选      → watch(无 301 目标)
  --funnel 模式上游 dropped_urls 每阶段截断前 20,dropped_total>20 时注明
  并建议 --urls+--gsc 全量口径。

输出:决策表 markdown(按 NO-GO/prune/merge/watch 分组)/ --json(schema_version
+decisions 计数+逐页证据)/ --as-remediation(工单草稿,字段对齐 remediation.py
的 item 形状,按 prune/merge 归并 affected_urls,附 redirect_map 边车)。

用法:
  python3 prune_gate.py --funnel traffic_funnel.json [--crawl crawl.json] \
      [--backlinks backlinks.csv] [--gsc queries.csv] [--window-days 90] \
      [--json] [--as-remediation tickets.json]
  python3 prune_gate.py --urls urls.txt --gsc gsc.csv [--crawl ...] \
      [--backlinks ...] [--window-days 90] [--json] [--as-remediation ...]

退出码:0 无待执行决策(零候选/全 NO-GO·watch)/ 1 有 prune/merge 决策待人工
执行(CI 语义同 trend_watch 的 GO)/ 2 输入或参数错误。"""
import argparse
import csv
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone

SCHEMA_VERSION = 1
WINDOW_DAYS_DEFAULT = 90        # 零点击判定的最短观察窗(口径注明,不参与计算)
INLINKS_PRUNE_MAX = 2           # 入链≤2 → prune(410);>2 → merge(301)
RANKING_POS_MAX = 20.0          # 排名词红线:query 平均排名 ≤20
MERGE_PHASE = "month"           # 工单 phase(remediation 口径:month=月内,+30d)
DEADLINE_DAYS = 30              # remediation month phase 的 deadline 天数

USAGE_EPILOG = """\
判定(按序短路):
  外链>0 或 排名词(Position≤20)>0 → NO-GO(红线:有外部资产/排面的页绝不退役)
  红线证据不全(外链或排名词不可查)→ watch
  入链数据缺失                      → watch
  入链≤2                            → prune(410)
  入链>2 且同目录有其他页            → merge(301 → 同目录最高入链页)
  其余                              → watch
输入:
  --funnel PATH   traffic_funnel.py --json 六阶段输出:候选=with_clicks 阶段
                  dropped_urls(in_serps 且非 with_clicks);漏斗截断(上游无
                  --gsc)→ 退出码 2;dropped_urls 截断前 20 时注明建议全量口径
  --urls PATH     URL 清单(每行一个;#注释跳过):配 --gsc 自算候选
                  (impressions>0 且 clicks=0;跳过 availability/indexability/
                  uniqueness 三层,输出注明——funnel 口径的降级版)
  --gsc PATH      GSC 导出 CSV:query 级(Page+Query+Position+Clicks/Impressions,
                  兼容导出前两行题头)供排名词红线+零点击判定;page 级
                  (Page+Impressions+Clicks)只供零点击判定,排名词不可查→watch
  --crawl PATH    site_crawl.py 输出 crawl.json:edges[]{src,dst} 数入链,
                  edges 空时回落 pages[].inlinks
  --backlinks PATH 外链导出 CSV(带目标列):GSC Links 简易表(无表头两列=
                  引荐页,目标页)/带 Target/Target URL/Linked Page 列变体;
                  分隔符 , ; \\t 自动嗅探;无目标列 → 外链核对不可用→watch
  --window-days N 零点击观察窗口下限(默认 90;仅口径注明,不参与计算)
  --json          结构化输出(schema_version/decisions/逐页证据/notes)
  --as-remediation PATH  工单草稿 JSON:items 字段对齐 remediation.py
                  (rule_id=prune-gate/prune|merge,area=content,status=proposed,
                  id 留空由并入时 next_id 顺延),附 redirect_map 边车
退出码:0 无待执行决策 / 1 有 prune/merge 待执行 / 2 输入或参数错误。\
"""

# 列头别名(小写+去空格归一;GSC 导出头两行题头兼容见 load_gsc)
PAGE_ALIASES = ("page", "url", "landing page", "page url")
QUERY_ALIASES = ("query", "search query", "top queries", "queries")
POS_ALIASES = ("position", "avg position", "average position")
TARGET_ALIASES = ("target", "target url", "target page", "destination",
                  "destination url", "linked page", "link target", "to url",
                  "目标页", "目标url")
REFERRING_ALIASES = ("referring page", "referring page url", "referring url",
                     "linking page", "referrer", "ref page", "source url",
                     "source page", "page url", "url", "link url",
                     "referring domain", "source domain", "domain", "引荐页")


def die(msg, code=2):
    """输入/参数错误统一出口:stderr + 退出码 2(套件契约:exit 2=用法/输入错)。"""
    sys.stderr.write(msg + "\n")
    sys.exit(code)


def norm_url(u):
    """跨源 join 归一化(traffic_funnel 同法):去 scheme、小写 host、去 fragment、
    非根路径去尾斜杠——http/https 混用与尾斜杠差异不影响 join。"""
    p = urllib.parse.urlparse(str(u).strip())
    path = p.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urllib.parse.urlunparse(("", p.netloc.lower(), path, p.params, p.query, ""))


def _norm_col(name):
    """列头归一:strip+BOM+引号+前导 #,lowercase,内部空白折叠(backlink_import 同法)。"""
    s = (name or "").strip().lstrip("\ufeff").strip().strip('"').strip()
    if s.startswith("#"):
        s = s[1:].strip()
    return re.sub(r"\s+", " ", s).lower()


def _num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# 输入加载
# ---------------------------------------------------------------------------

def load_json(path, what):
    """JSON 文件 → dict;读不了/解析不了 → exit 2。"""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        return die("%s 无法读取 %s: %s" % (what, path, e))
    except ValueError as e:
        return die("%s JSON 无法解析 %s: %s" % (what, path, e))


def load_urls(path, what):
    """URL 清单:每行一个,空行/# 注释跳过。"""
    try:
        with open(path, encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
    except OSError as e:
        return die("%s 无法读取 %s: %s" % (what, path, e))


def _sniff_delim(line):
    """首行 → 最可能分隔符(切出非空列最多者;平手按 , ; \\t 顺序)。"""
    best, best_n = ",", -1
    for d in (",", ";", "\t"):
        try:
            fields = next(csv.reader([line], delimiter=d))
        except (csv.Error, StopIteration):
            continue
        n = len([f for f in fields if _norm_col(f)])
        if n > best_n:
            best, best_n = d, n
    return best


def load_gsc(path):
    """GSC 导出 CSV → (per_page, has_query)。
    per_page: {norm_url: {"clicks","impressions","queries":[(query,pos)]}};
    has_query=导出带 Query 列(query 级,排名词红线可查),否则 page 级。
    兼容导出前两行题头:表头行=首个含 page/query 列的行(content_queue 同法);
    同页多行累加(query 级按词导出)。"""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
    except OSError as e:
        return die("--gsc 无法读取 %s: %s" % (path, e))
    header_idx, header = None, None
    for i, r in enumerate(rows):
        cells = [_norm_col(c) for c in r]
        if any(any(c == a or c.startswith(a) for a in PAGE_ALIASES + QUERY_ALIASES)
               for c in cells if c):
            header_idx, header = i, cells
            break
    if header_idx is None:
        return die("--gsc CSV 找不到表头(需 Page/Query 列;%s)" % path)
    col = {}
    for i, c in enumerate(header):
        if c in PAGE_ALIASES and "page" not in col:
            col["page"] = i
        elif c in QUERY_ALIASES and "query" not in col:
            col["query"] = i
        elif c in POS_ALIASES and "position" not in col:
            col["position"] = i
        elif c == "clicks" and "clicks" not in col:
            col["clicks"] = i
        elif c == "impressions" and "impressions" not in col:
            col["impressions"] = i
    if "page" not in col:
        return die("--gsc CSV 缺 Page 列(实际列:%s)" % header)
    has_query = "query" in col and "position" in col
    if not has_query and not ("clicks" in col and "impressions" in col):
        return die("--gsc CSV 缺 Clicks/Impressions 列且无 Query+Position(page 级"
                   "至少要 Clicks+Impressions;实际列:%s)" % header)
    per_page = {}
    for r in rows[header_idx + 1:]:
        r = list(r) + [""] * (max(col.values()) - len(r) + 1 if col else 0)
        raw = (r[col["page"]] or "").strip()
        key = norm_url(raw)
        if not key or key == "//":
            continue
        d = per_page.setdefault(key, {"clicks": 0.0, "impressions": 0.0, "queries": []})
        if "clicks" in col:
            d["clicks"] += _num(r[col["clicks"]])
        if "impressions" in col:
            d["impressions"] += _num(r[col["impressions"]])
        if has_query:
            q = (r[col["query"]] or "").strip()
            if q:
                d["queries"].append((q, _num(r[col["position"]])))
    return per_page, has_query


def load_backlinks(path):
    """外链导出 CSV → (per_target, note)。
    per_target: {norm_url(target): {"count","referrers"}}(按 引荐url+target 去重);
    无目标列(backlink_import 统一 schema 只有引荐侧)→ per_target=None +
    note(按页外链核对不可用→保守 watch)。无表头两列=引荐页,目标页
    (GSC Latest links 简易表,backlink_import 同口径)。"""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
    except OSError as e:
        return die("--backlinks 无法读取 %s: %s" % (path, e))
    if not lines:
        return die("--backlinks 文件为空: %s" % path)
    delim = _sniff_delim(lines[0])
    try:
        records = [r for r in csv.reader(lines, delimiter=delim) if r]
    except csv.Error as e:
        return die("--backlinks CSV 解析失败(%s,分隔符 %r): %s" % (path, delim, e))
    headerless = bool(re.match(r"^https?://", (records[0][0] or "").strip(), re.I))
    tcol = rcol = None
    if not headerless:
        cells = [_norm_col(c) for c in records[0]]
        for i, c in enumerate(cells):
            if c in TARGET_ALIASES and tcol is None:
                tcol = i
            elif c in REFERRING_ALIASES and rcol is None:
                rcol = i
        if tcol is None:
            return None, ("外链导出无目标列(%s):按页外链核对不可用——backlink_import.py "
                          "统一 schema 只保留引荐侧;红线①无法证实 → 全部候选保守 watch"
                          % ", ".join(c for c in cells if c))
        if rcol is None:                                # 只有目标列:计数按行
            rcol = tcol
        data_rows = records[1:]
    else:
        if len(records[0]) < 2:                         # 单列引荐表:无目标侧
            return None, "外链导出仅单列(无目标页):按页外链核对不可用 → 全部候选保守 watch"
        rcol, tcol, data_rows = 0, 1, records
    per_target, seen = {}, set()
    for r in data_rows:
        r = list(r) + [""] * (max(rcol, tcol) - len(r) + 1)
        tgt = norm_url(r[tcol])
        ref = (r[rcol] or "").strip()
        if not tgt or tgt == "//":
            continue
        pair = (ref or "-", tgt)
        if pair in seen:                                # 同 引荐+目标 去重
            continue
        seen.add(pair)
        d = per_target.setdefault(tgt, {"count": 0, "referrers": []})
        d["count"] += 1
        if ref and ref not in d["referrers"]:
            d["referrers"].append(ref)
    if not per_target:
        return None, "外链导出无有效行(目标列全空):按页外链核对不可用 → 全部候选保守 watch"
    return per_target, None


def load_inlinks(path):
    """site_crawl.py 输出 → (inlinks, pool, display, note)。
    inlinks: {norm_url: 入链数}(edges[]{src,dst} 计数;edges 空时回落
    pages[].inlinks 字段——站点 sitemap-only 模式没有 edges);
    pool: 同目录 merge 目标候选(norm_url 键,含 edges 指向的站内页);
    display: {norm_url: 原始 URL}(决策表/redirect map 展示用;edges 独有键
    无原始 URL,展示时按 https: 前缀还原);
    无 crawl 文件 → (None, [], {}, None),调用方按不可用处理。"""
    data = load_json(path, "--crawl")
    pages = data.get("pages") if isinstance(data, dict) else None
    edges = data.get("edges") if isinstance(data, dict) else None
    if not isinstance(pages, list) and not isinstance(edges, list):
        return die("--crawl JSON 非 site_crawl 输出(缺 pages/edges):%s" % path)
    page_urls, display, inlink_field = [], {}, {}
    if isinstance(pages, list):
        for p in pages:
            if isinstance(p, dict) and p.get("url"):
                k = norm_url(p["url"])
                if k not in display:
                    page_urls.append(k)
                    display[k] = str(p["url"])
                    il = p.get("inlinks")
                    if isinstance(il, (int, float)) and il >= 0:
                        inlink_field[k] = int(il)
    inlinks, note = {}, None
    if isinstance(edges, list) and edges:
        for e in edges:
            if isinstance(e, dict) and e.get("src") and e.get("dst"):
                k = norm_url(e["dst"])
                inlinks[k] = inlinks.get(k, 0) + 1
            elif isinstance(e, (list, tuple)) and len(e) >= 2 and e[0] and e[1]:
                k = norm_url(e[1])
                inlinks[k] = inlinks.get(k, 0) + 1
        note = "入链来源:crawl edges(%d 条)" % len(edges)
    elif inlink_field:
        inlinks = dict(inlink_field)
        note = "入链来源:crawl pages[].inlinks 字段(edges 为空,回落口径)"
    else:
        note = "crawl 无 edges 且页对象缺 inlinks 字段:入链核对不可用 → 保守 watch"
        return None, [], {}, note
    # 页清单与计数键对齐(edges 的 dst 可能指向未在 pages 的 URL——保留计数进候选池)
    for k in inlinks:
        if k not in display:
            page_urls.append(k)
    return inlinks, sorted(set(page_urls)), display, note


# ---------------------------------------------------------------------------
# 候选与判定
# ---------------------------------------------------------------------------

def candidates_from_funnel(path):
    """--funnel:traffic_funnel --json → [(url, reason)]。
    候选 = with_clicks 阶段 dropped_urls(in_serps 且非 with_clicks);
    漏斗截断(上游无 GSC)/无该阶段 → exit 2;
    dropped_total>len(dropped_urls) → 上游每阶段截前 20,注明建议全量口径。"""
    rep = load_json(path, "--funnel")
    if not isinstance(rep, dict) or not isinstance(rep.get("stages"), list):
        return die("--funnel JSON 非 traffic_funnel.py --json 输出(缺 stages):%s" % path)
    if rep.get("funnel_truncated_at"):
        return die("--funnel 漏斗截断于 %s(上游未给 --gsc):with_clicks 判定为 null——"
                   "请带 --gsc 重跑 traffic_funnel.py,或改用 --urls+--gsc 口径" % rep["funnel_truncated_at"])
    stage = next((s for s in rep["stages"] if s.get("stage") == "with_clicks"), None)
    if stage is None or stage.get("pages_in") is None:
        return die("--funnel 无 with_clicks 阶段判定:%s" % path)
    dropped = [(d["url"], d.get("reason") or "")
               for d in stage.get("dropped_urls") or [] if isinstance(d, dict) and d.get("url")]
    total = stage.get("dropped_total")
    note = None
    if isinstance(total, int) and total > len(dropped):
        note = ("上游 traffic_funnel 每阶段 dropped_urls 截断前 20:with_clicks 流失 "
                "%d 页仅见 %d——全量判定请改用 --urls+--gsc 口径" % (total, len(dropped)))
    return dropped, note


def candidates_from_urls_gsc(urls_path, gsc_path):
    """--urls+--gsc:候选 = impressions>0 且 clicks=0(降级口径:跳过
    availability/indexability/uniqueness 三层——funnel 的 in_serps 是六层过滤
    后的集合,本模式只按 GSC 曝光判定,输出注明;候选相对 funnel 口径偏宽)。"""
    urls = load_urls(urls_path, "--urls")
    per_page, has_query = load_gsc(gsc_path)
    out = []
    for u in urls:
        d = per_page.get(norm_url(u))
        if d and d["impressions"] > 0 and d["clicks"] <= 0:
            out.append((u, "GSC impressions=%g clicks=0" % d["impressions"]))
    note = ("--urls+--gsc 降级口径:in_serps 仅按 GSC impressions>0 判定,跳过 "
            "availability/indexability/uniqueness 三层(无 audit 数据)——候选相对 "
            "funnel 口径偏宽,prune 执行前建议跑一遍 site_audit 排除 noindex/重复页")
    return out, note


def _dirname(key):
    """norm_url 键 → 目录前缀(最后一段前的路径;根路径 → "/")。"""
    path = urllib.parse.urlparse("//" + key).path or "/"
    return path.rsplit("/", 1)[0] or "/"


def same_dir_merge_target(url_key, inlinks, page_pool):
    """同目录最高入链页(merge 的 301 目标建议):排除自身;平票取 URL 序(确定性);
    无候选 → None。"""
    d = _dirname(url_key)
    cands = [p for p in page_pool if p != url_key and _dirname(p) == d]
    if not cands:
        return None
    return sorted(cands, key=lambda p: (-inlinks.get(p, 0), p))[0]


def display_url(key, display):
    """norm_url 键 → 展示 URL(crawl 原始 URL;edges 独有键无原始值,按 https:
    前缀还原——redirect map 目标建议用)。"""
    if key in display:
        return display[key]
    return "https:" + key if key.startswith("//") else key


def decide(pages, inlinks, page_pool, backlinks, gsc_rank, window_days, display):
    """三查+三判。pages=[(url, reason)];inlinks={norm:count}|None;
    backlinks={norm:{count,referrers}}|None;gsc_rank={norm:[(q,pos)]}|None;
    display={norm:原始URL}。返回逐页决策记录列表(确定性:决策序+URL 序)。"""
    out = []
    for url, why in pages:
        key = norm_url(url)
        rec = {"url": url, "inlinks": None, "inlinks_known": inlinks is not None,
               "backlinks": 0, "backlinks_known": backlinks is not None,
               "ranking_words": [], "ranking_known": gsc_rank is not None,
               "reasons": [], "decision": None, "action": "", "merge_target": None,
               "candidate_reason": why}
        if inlinks is not None:
            rec["inlinks"] = inlinks.get(key, 0)
        bl = (backlinks or {}).get(key)
        if bl:
            rec["backlinks"] = bl["count"]
        rec["ranking_words"] = sorted({q for q, pos in (gsc_rank or {}).get(key, [])
                                       if pos <= RANKING_POS_MAX})
        # ① 红线:外链>0 或 排名词>0 → NO-GO
        if rec["backlinks"] > 0:
            rec["reasons"].append("外链 %d>0(%s)" % (
                rec["backlinks"], "; ".join(bl["referrers"][:3]) +
                ("…" if len(bl["referrers"]) > 3 else "")))
        if rec["ranking_words"]:
            rec["reasons"].append("排名词 %d 个(Position≤20):%s" % (
                len(rec["ranking_words"]), ", ".join(rec["ranking_words"][:5]) +
                ("…" if len(rec["ranking_words"]) > 5 else "")))
        if rec["reasons"]:
            rec["decision"] = "nogo"
            rec["action"] = "保留(红线:外部资产/排面在,不退役)"
            out.append(rec)
            continue
        # ② 红线证据不全 → watch(缺证据不下刀)
        if not rec["backlinks_known"]:
            rec["reasons"].append("外链核对不可用(--backlinks 未提供或无目标列)")
        if not rec["ranking_known"]:
            rec["reasons"].append("排名词核对不可用(GSC 导出无 Query+Position 列)")
        if rec["reasons"]:
            rec["decision"] = "watch"
            rec["action"] = "watch(补数据后复跑)"
            out.append(rec)
            continue
        # ③ 入链不可用 → watch
        if not rec["inlinks_known"]:
            rec["reasons"].append("入链核对不可用(--crawl 未提供或 crawl 无 edges/inlinks)")
            rec["decision"] = "watch"
            rec["action"] = "watch(补 --crawl 后复跑)"
            out.append(rec)
            continue
        # ④ 入链≤2 → prune(410);>2 → merge(301 同目录最高入链页)
        if rec["inlinks"] <= INLINKS_PRUNE_MAX:
            rec["decision"] = "prune"
            rec["action"] = "prune → 410(零点击+零外链+无排名词+入链≤%d)" % INLINKS_PRUNE_MAX
            rec["reasons"].append("入链 %d≤%d,近孤儿页,内链资产可弃" % (rec["inlinks"], INLINKS_PRUNE_MAX))
        else:
            target = same_dir_merge_target(key, inlinks or {}, page_pool)
            if target is None:
                rec["decision"] = "watch"
                rec["action"] = "watch"
                rec["reasons"].append("入链 %d>%d 但同目录无其他页:无 301 目标" % (rec["inlinks"], INLINKS_PRUNE_MAX))
            else:
                target_url = display_url(target, display)
                rec["decision"] = "merge"
                rec["action"] = "merge → 301 %s(同目录最高入链页,入链 %d)" % (
                    target_url, (inlinks or {}).get(target, 0))
                rec["merge_target"] = target_url
                rec["reasons"].append("入链 %d>%d,301 保权重" % (rec["inlinks"], INLINKS_PRUNE_MAX))
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------

def render_markdown(rep):
    L = ["## 零点击页退役/合并决策(prune_gate)", ""]
    mode = {"funnel": "--funnel(traffic_funnel 六阶段输出)",
            "urls_gsc": "--urls+--gsc(直接口径)"}[rep["mode"]]
    L.append("候选口径:in_serps(impressions>0)且非 with_clicks(clicks=0)· 模式:%s" % mode)
    L.append("窗口口径:GSC 导出窗口须≥%d 天(默认 90,--window-days 可调)——窗口长度"
             "无法从导出文件推断,由调用方保证;窗口不足请勿据此 prune" % rep["window_days"])
    d = rep["decisions"]
    L.append("候选 %d 页:NO-GO %d(红线)/ prune %d(410)/ merge %d(301)/ watch %d"
             % (rep["candidates"], d["nogo"], d["prune"], d["merge"], d["watch"]))
    L.append("")
    sections = [
        ("nogo", "### NO-GO 红线(%d 页)——外链>0 或排名词(Position≤20)>0,不可退役" % d["nogo"],
         ["外链", "排名词(P≤20)", "原因"]),
        ("prune", "### prune → 410(%d 页)——零点击+零外链+无排名词+入链≤%d" % (d["prune"], INLINKS_PRUNE_MAX),
         ["入链", "理由"]),
        ("merge", "### merge → 301(%d 页)——入链>%d,合并保权重" % (d["merge"], INLINKS_PRUNE_MAX),
         ["入链", "301 目标(同目录最高入链)", "理由"]),
        ("watch", "### watch(%d 页)——数据不全或无目标,补数据后复跑" % d["watch"],
         ["入链", "原因"]),
    ]
    for key, title, cols in sections:
        pages = [p for p in rep["pages"] if p["decision"] == key]
        L.append(title)
        L.append("")
        if not pages:
            L.append("(无)")
            L.append("")
            continue
        L.append("| URL | " + " | ".join(cols) + " |")
        L.append("|---" * (len(cols) + 1) + "|")
        for p in pages:
            extra = []
            if key == "nogo":
                extra = [str(p["backlinks"]) if p["backlinks_known"] else "?",
                         ", ".join(p["ranking_words"][:3]) + ("…" if len(p["ranking_words"]) > 3 else "")
                         if p["ranking_known"] else "?",
                         "; ".join(p["reasons"])]
            elif key == "prune":
                extra = [_fmt_int(p["inlinks"]), "; ".join(p["reasons"])]
            elif key == "merge":
                extra = [_fmt_int(p["inlinks"]), p["merge_target"] or "",
                         "; ".join(p["reasons"])]
            else:
                extra = [_fmt_int(p["inlinks"]), "; ".join(p["reasons"])]
            L.append("| %s | %s |" % (p["url"], " | ".join(extra)))
        L.append("")
    if rep["redirect_map"]:
        L.append("### redirect map 草稿(merge)")
        L.append("")
        for src, dst in sorted(rep["redirect_map"].items()):
            L.append("- %s → 301 → %s" % (src, dst))
        L.append("")
    for n in rep["notes"]:
        L.append("> 降级声明:%s" % n)
    if not rep["notes"]:
        L.append("> 三查数据齐备(edges 入链/目标列外链/query 级 GSC),无降级项")
    return "\n".join(L)


def _fmt_int(v):
    return "?" if v is None else str(v)


def build_remediation_draft(rep, now):
    """--as-remediation:工单草稿(remediation.py item 形状;按 prune/merge 归并
    affected_urls,redirect_map 作边车;NO-GO/watch 不开工单)。"""
    items = []
    common = {"area": "content", "phase": MERGE_PHASE, "status": "proposed",
              "closed": None,
              "verify_hint": "执行后该 URL 在新 GSC 导出中不再出现零点击清单即核销"}
    created = now.isoformat()
    deadline = (now + timedelta(days=DEADLINE_DAYS)).isoformat()
    prunes = [p["url"] for p in rep["pages"] if p["decision"] == "prune"]
    merges = [p["url"] for p in rep["pages"] if p["decision"] == "merge"]
    if prunes:
        items.append(dict(common, rule_id="prune-gate/prune", severity="WARN",
                          affected_urls=prunes, created=created, deadline=deadline,
                          action="410 退役零点击页(≥%d 天窗口零点击+零外链+无排名词+入链≤%d;"
                                 "执行前人工复核,先确认无近期外链增长)" % (rep["window_days"], INLINKS_PRUNE_MAX),
                          note="prune_gate %s 生成;红线已核:外链=0、排名词(P≤20)=0" % rep["mode"]))
    if merges:
        items.append(dict(common, rule_id="prune-gate/merge", severity="INFO",
                          affected_urls=merges, created=created, deadline=deadline,
                          action="301 合并零点击页至同目录最高入链页(逐页目标见 redirect_map)",
                          note="prune_gate %s 生成;红线已核:外链=0、排名词(P≤20)=0" % rep["mode"]))
    return {"schema_version": SCHEMA_VERSION, "tool": "prune_gate",
            "generated": created, "source_mode": rep["mode"],
            "note": "工单草稿(接 remediation.py):items 字段对齐 remediations.json 的 "
                    "item;id 未填,并入时由 remediation.next_id 顺延(append 进 items "
                    "数组即可);redirect_map 为 merge 的逐页 301 目标",
            "items": items, "redirect_map": rep["redirect_map"]}


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="prune_gate.py",
        description="零点击页退役/合并决策闸(R3-10):三查(入链/外链/排名词)→"
                    " NO-GO(prune 红线)/ prune(410)/ merge(301)/ watch 三判。",
        epilog=USAGE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--funnel", help="traffic_funnel.py --json 六阶段输出(候选源一)")
    ap.add_argument("--urls", help="URL 清单(候选源二,配 --gsc)")
    ap.add_argument("--gsc", help="GSC 导出 CSV(query 级供排名词红线;page 级仅供零点击)")
    ap.add_argument("--crawl", help="site_crawl.py 输出 crawl.json(入链:edges/inlinks)")
    ap.add_argument("--backlinks", help="外链导出 CSV(带目标列;红线①)")
    ap.add_argument("--window-days", type=int, default=WINDOW_DAYS_DEFAULT,
                    help="零点击观察窗口下限(默认 90;口径注明用)")
    ap.add_argument("--json", action="store_true", help="结构化输出")
    ap.add_argument("--as-remediation", metavar="PATH",
                    help="工单草稿 JSON 写入 PATH(remediation item 形状)")
    args = ap.parse_args(argv)

    notes = []
    if not args.funnel and not (args.urls and args.gsc):
        ap.error("需要 --funnel,或 --urls+--gsc 至少一组候选源")
    if args.funnel and args.urls:
        ap.error("--funnel 与 --urls 互斥(两个候选源二选一)")
    if args.funnel:
        cands, note = candidates_from_funnel(args.funnel)
        mode = "funnel"
        if note:
            notes.append(note)
    else:
        cands, note = candidates_from_urls_gsc(args.urls, args.gsc)
        mode = "urls_gsc"
        notes.append(note)

    inlinks, page_pool, display, inote = (None, [], {}, None)
    if args.crawl:
        inlinks, page_pool, display, inote = load_inlinks(args.crawl)
        if inote:
            notes.append(inote)
    else:
        notes.append("--crawl 未提供:入链核对不可用 → 入链依赖的判定全部保守 watch")

    backlinks, bnote = (None, None)
    if args.backlinks:
        backlinks, bnote = load_backlinks(args.backlinks)
        if bnote:
            notes.append(bnote)
    else:
        notes.append("--backlinks 未提供:外链红线核对不可用 → 全部候选保守 watch")

    gsc_rank, gnote = (None, None)
    if args.gsc:
        per_page, has_query = load_gsc(args.gsc)
        if has_query:
            gsc_rank = {k: d["queries"] for k, d in per_page.items() if d["queries"]}
        else:
            gnote = ("--gsc 为 page 级导出(无 Query+Position 列):排名词红线核对不可用"
                     " → 全部候选保守 watch;补 query 级导出可解除")
            notes.append(gnote)
    else:
        notes.append("--gsc 未提供:排名词红线核对不可用 → 全部候选保守 watch"
                     "(--funnel 模式下 --gsc 仅用于排名词核对)")

    seen = set()
    pages = []
    for url, why in cands:                              # 去重保序
        k = norm_url(url)
        if k in seen:
            continue
        seen.add(k)
        pages.append((url, why))
    recs = decide(pages, inlinks, page_pool, backlinks, gsc_rank, args.window_days, display)
    recs.sort(key=lambda r: ({"nogo": 0, "prune": 1, "merge": 2, "watch": 3}[r["decision"]], r["url"]))
    counts = {k: sum(1 for r in recs if r["decision"] == k)
              for k in ("nogo", "prune", "merge", "watch")}
    rep = {"schema_version": SCHEMA_VERSION, "tool": "prune_gate", "mode": mode,
           "window_days": args.window_days, "candidates": len(recs),
           "decisions": counts, "pages": recs,
           "redirect_map": {r["url"]: r["merge_target"] for r in recs
                            if r["decision"] == "merge" and r["merge_target"]},
           "notes": notes}
    if args.as_remediation:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        draft = build_remediation_draft(rep, now)
        try:
            with open(args.as_remediation, "w", encoding="utf-8") as f:
                json.dump(draft, f, ensure_ascii=False, indent=1)
        except OSError as e:
            return die("--as-remediation 写入失败 %s: %s" % (args.as_remediation, e))
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(render_markdown(rep))
    return 1 if (counts["prune"] or counts["merge"]) else 0


if __name__ == "__main__":
    sys.exit(main())
