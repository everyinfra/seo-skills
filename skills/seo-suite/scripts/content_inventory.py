#!/usr/bin/env python3
"""站点内容库存四轴治理审计(content_inventory;stdlib only)。

规格:skills/seo-suite/references/overview/pipeline-completeness.md R6 内容体系
(content_inventory 四轴治理:keep·update·consolidate·remove + redirect map——
2026-10-11 第二轮 20 视角扫描前未登记项)。清点范围=--crawl 的 pages 全集
(site_crawl.py 输出,站点级审计口径);每页四轴:

  流量轴    --gsc(GSC 页面/query 级导出的 Clicks;query 级按页累加)
  外链轴    --backlinks(带 target 列的外链导出 CSV,同 prune_gate 口径:
            GSC Links 简易表/Ahrefs/Semrush Target 列变体;无 target 列 → 轴不可用)
  AI 引用轴 --panel(citation_panel.py 的 panel.json:runs[].results[*].cited_urls
            按页计被引次数——GEO 时代的"零流量≠零价值",被引页是资产)
  战略轴    --keep(URL 清单人工指定)或 --keep-regex(模板页 URL 正则,如
            /pricing|/about——商业必需页不问流量)

四桶判定(按序,注释即契约):
  ① 重复组(title Simhash 汉明距离≤3 聚类,traffic_funnel uniqueness 同法):
     组内有强轴成员 → winner(组内价值最高页)走 ②③,其余 → consolidate
     (301 并入 winner);组内全零 → 全组 → remove 候选(整组无保留价值)。
  ② 一轴强(任一轴>0:有点击/有外链/被 AI 引用/战略页)且内容陈旧
     (词数<地板,--word-floor 默认 300)→ update(薄而有值,刷新优先救)。
  ③ 一轴强且不陈旧(或词数未知)→ keep。
  ④ 四轴全零 → remove 候选(执行前人工复核;陈旧不救零价值页——update 只救
     有值的薄页)。
  AI 引用存量检查(防误删红线,审计报告强调):被引页(ai_citations>0)绝不入
  remove 桶——硬护栏在代码层执行(虽然被引即 AI 轴强、本就不该到 ④,护栏双保险),
  输出显式给出 remove 桶被引命中数(恒 0)与 crawl 未覆盖的被引页清单(补爬,不可删)。

输出:keep/update/consolidate/remove 四桶(markdown 分组决策表)+ redirect map
草稿(consolidate 并入组内 winner;remove 候选并入同目录最强页,无目标 → 410
建议)+ 季度节奏建议(下次全量清点日=下季度首日;各桶行动节奏)+ 降级声明
(轴数据缺失时 remove 候选的未核项逐条注明,不猜)。

用法:
  python3 content_inventory.py --crawl crawl.json --gsc gsc.csv [--panel panel.json]
      [--backlinks backlinks.csv] [--keep keep.txt] [--keep-regex '/pricing|/about']
      [--words words.csv] [--word-floor 300] [--json]

退出码:0 正常(审计报告,无闸语义)/ 2 输入或参数错误。"""
import argparse
import csv
import hashlib
import json
import re
import sys
import urllib.parse
from datetime import datetime, timezone

SCHEMA_VERSION = 1
WORD_FLOOR_DEFAULT = 300          # 词数地板:低于即"内容陈旧"(update 触发条件)
DUP_HAMMING = 3                   # 重复组阈值(traffic_funnel uniqueness 同口径)
SIMHASH_BITS = 64
WORD_FIELDS = ("word_count", "words", "wordcount", "content_words", "text_words")

USAGE_EPILOG = """\
四桶判定(按序):
  ① title Simhash 重复组(汉明≤3):组内有强轴成员 → 非 winner → consolidate
     (301 并入组内价值最高页);组内全零 → 全组 remove 候选
  ② 一轴强 + 词数<地板 → update(薄而有值,刷新优先)
  ③ 一轴强(不陈旧/词数未知)→ keep
  ④ 四轴全零 → remove 候选(人工复核;陈旧不救零价值页)
  AI 引用存量检查:被引页绝不入 remove 桶(硬护栏,防误删红线)。
输入:
  --crawl PATH    site_crawl.py 输出 crawl.json(清点范围=pages 全集;title 供
                  重复组聚类,inlinks/edges 供 winner 与 redirect 目标排序)
  --gsc PATH      GSC 导出 CSV(页面级 Page/Clicks/Impressions 或 query 级
                  Page/Query/.../Clicks 按页累加;兼容导出前两行题头)
  --panel PATH    citation_panel.py 的 panel.json(AI 引用轴:runs[].results[*]
                  .cited_urls 按页计被引次数;缺省 → AI 轴不可用,注明)
  --backlinks PATH 带目标列的外链导出 CSV(同 prune_gate 口径;无 target 列 →
                  外链轴不可用,注明)
  --keep PATH     战略页 URL 清单(完整 URL 每行一个,#注释跳过;norm_url 匹配)
  --keep-regex RE 战略页 URL 正则(re.search;可重复,如 /pricing|/about)
  --words PATH    词数 CSV(Page,Words;crawl 页对象缺 word_count 字段时补;
                  两处都有以 --words 为准)
  --word-floor N  词数地板(默认 300)
  --json          结构化输出(buckets/pages/redirect_map/ai_citation_guard/
                  cadence/notes)
退出码:0 正常 / 2 输入或参数错误。\
"""

PAGE_ALIASES = ("page", "url", "landing page", "page url")
QUERY_ALIASES = ("query", "search query", "top queries", "queries")
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


def _int_or_none(v):
    try:
        n = int(float(str(v).strip()))
        return n if n >= 0 else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Simhash 重复组(traffic_funnel uniqueness 同法拷贝,保持 standalone)
# ---------------------------------------------------------------------------

def simhash(text, bits=SIMHASH_BITS):
    r"""64 位 Simhash:token→md5 前 8 字节当指纹,逐位 ±1 加权,各位符号即输出。"""
    v = [0] * bits
    for tok in re.findall(r"\w+", text.lower()):
        h = int.from_bytes(hashlib.md5(tok.encode("utf-8")).digest()[:8], "big")
        for i in range(bits):
            v[i] += 1 if h >> i & 1 else -1
    f = 0
    for i in range(bits):
        if v[i] > 0:
            f |= 1 << i
    return f


def hamming(a, b):
    return bin(a ^ b).count("1")


def cluster_titles(pages):
    """[{key,title,...}] → 重复组列表([[key,...],...],组内 URL 升序;仅 ≥2 页组)。
    单链并查集,汉明距离≤DUP_HAMMING 视为重复(传递闭包);空 title 不参与。"""
    sigs = {}
    for p in pages:
        t = (p.get("title") or "").strip()
        if t:
            sigs[p["key"]] = simhash(t)
    parent = {u: u for u in sigs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    urls = sorted(sigs)
    for i, a in enumerate(urls):
        for b in urls[i + 1:]:
            if hamming(sigs[a], sigs[b]) <= DUP_HAMMING:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[rb] = ra
    groups = {}
    for u in urls:
        groups.setdefault(find(u), []).append(u)
    return [sorted(g) for g in groups.values() if len(g) >= 2]


# ---------------------------------------------------------------------------
# 输入加载
# ---------------------------------------------------------------------------

def load_json(path, what):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        return die("%s 无法读取 %s: %s" % (what, path, e))
    except ValueError as e:
        return die("%s JSON 无法解析 %s: %s" % (what, path, e))


def _sniff_delim(line):
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
    """GSC 导出 CSV → {norm_url: {"clicks","impressions"}}(query 级按页累加;
    兼容导出前两行题头:表头行=首个含 page/query 列的行)。"""
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
        return die("--gsc CSV 找不到表头(需 Page 列;%s)" % path)
    col = {}
    for i, c in enumerate(header):
        if c in PAGE_ALIASES and "page" not in col:
            col["page"] = i
        elif c == "clicks" and "clicks" not in col:
            col["clicks"] = i
        elif c == "impressions" and "impressions" not in col:
            col["impressions"] = i
    if "page" not in col:
        return die("--gsc CSV 缺 Page 列(实际列:%s)" % header)
    if "clicks" not in col:
        return die("--gsc CSV 缺 Clicks 列(实际列:%s)" % header)
    out = {}
    for r in rows[header_idx + 1:]:
        r = list(r) + [""] * (max(col.values()) - len(r) + 1)
        key = norm_url(r[col["page"]])
        if not key or key == "//":
            continue
        d = out.setdefault(key, {"clicks": 0.0, "impressions": 0.0})
        d["clicks"] += _num(r[col["clicks"]])
        if "impressions" in col:
            d["impressions"] += _num(r[col["impressions"]])
    return out


def load_backlinks(path):
    """带目标列的外链导出 → ({norm(target): {"count","referrers"}}, note|None);
    口径同 prune_gate.load_backlinks(无目标列 → 轴不可用)。"""
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
            return None, ("外链导出无目标列(%s):外链轴不可用——backlink_import.py 统一 "
                          "schema 只保留引荐侧;remove 候选未经外链核对,执行前必须补"
                          % ", ".join(c for c in cells if c))
        data_rows = records[1:]
    else:
        if len(records[0]) < 2:
            return None, "外链导出仅单列(无目标页):外链轴不可用,remove 候选未经外链核对"
        rcol, tcol, data_rows = 0, 1, records
    per_target, seen = {}, set()
    for r in data_rows:
        r = list(r) + [""] * (max(rcol, tcol) - len(r) + 1)
        tgt = norm_url(r[tcol])
        ref = (r[rcol] or "").strip()
        if not tgt or tgt == "//":
            continue
        if (ref or "-", tgt) in seen:
            continue
        seen.add((ref or "-", tgt))
        d = per_target.setdefault(tgt, {"count": 0, "referrers": []})
        d["count"] += 1
        if ref and ref not in d["referrers"]:
            d["referrers"].append(ref)
    if not per_target:
        return None, "外链导出无有效行(目标列全空):外链轴不可用,remove 候选未经外链核对"
    return per_target, None


def load_panel_citations(path):
    """panel.json → ({norm_url: 被引次数}, panel_domain|None)。
    被引次数=runs[].results[*].cited_urls 中该 URL 出现的 (run,结果) 次数;
    兼容 results 为 dict(prompt→result)或 list(result)两种形态。"""
    panel = load_json(path, "--panel")
    if not isinstance(panel, dict):
        return die("--panel JSON 非 citation_panel 的 panel.json:%s" % path)
    counts = {}
    runs = panel.get("runs")
    if not isinstance(runs, list):
        return die("--panel JSON 缺 runs 列表(citation_panel panel.json 结构):%s" % path)
    for run in runs:
        if not isinstance(run, dict):
            continue
        results = run.get("results")
        items = results.values() if isinstance(results, dict) else \
            (results if isinstance(results, list) else [])
        for res in items:
            if not isinstance(res, dict):
                continue
            for u in res.get("cited_urls") or []:
                k = norm_url(u)
                if k:
                    counts[k] = counts.get(k, 0) + 1
    return counts, (panel.get("domain") or None)


def load_keep(path):
    """--keep URL 清单(完整 URL 每行一个,空行/# 注释跳过)→ {norm_url}。"""
    try:
        with open(path, encoding="utf-8") as f:
            return {norm_url(ln) for ln in f if ln.strip() and not ln.strip().startswith("#")}
    except OSError as e:
        return die("--keep 无法读取 %s: %s" % (path, e))


def load_words(path):
    """--words CSV(Page,Words)→ {norm_url: 词数};列头别名 page/url/words/
    word_count;无表头两列(裸 URL,整数)也收。"""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            lines = [ln for ln in f.read().splitlines() if ln.strip()]
    except OSError as e:
        return die("--words 无法读取 %s: %s" % (path, e))
    if not lines:
        return {}
    delim = _sniff_delim(lines[0])
    rows = [r for r in csv.reader(lines, delimiter=delim) if r]
    if any(_norm_col(c) in ("page", "url", "words", "word_count", "wordcount")
           for c in rows[0]) and not re.match(r"^https?://",
                                              (rows[0][0] or "").strip(), re.I):
        col = {}
        for i, c in enumerate(_norm_col(x) for x in rows[0]):
            if c in ("page", "url") and "page" not in col:
                col["page"] = i
            elif c in ("words", "word_count", "wordcount") and "words" not in col:
                col["words"] = i
        if "page" not in col or "words" not in col:
            return die("--words CSV 缺 Page/Words 列(实际列:%s)" % rows[0])
        data = [[c for c in r] for r in rows[1:]]
    else:                                               # 无表头:URL,词数
        col, data = {"page": 0, "words": 1}, rows
    out = {}
    for r in data:
        r = list(r) + [""] * (max(col.values()) - len(r) + 1)
        k, w = norm_url(r[col["page"]]), _int_or_none(r[col["words"]])
        if k and w is not None:
            out[k] = w
    return out


def load_crawl(path):
    """site_crawl 输出 → 页记录列表(确定性:key 升序)。
    每记录:key(norm)/url(原始)/title/inlinks(计数值或 None)/word_count;
    inlinks 优先 edges 计数,edges 空时回落 pages[].inlinks 字段。"""
    data = load_json(path, "--crawl")
    if not isinstance(data, dict) or not isinstance(data.get("pages"), list):
        return die("--crawl JSON 非 site_crawl 输出(缺 pages 列表):%s" % path)
    edges = data.get("edges")
    in_from_edges = {}
    if isinstance(edges, list):
        for e in edges:
            if isinstance(e, dict) and e.get("src") and e.get("dst"):
                k = norm_url(e["dst"])
                in_from_edges[k] = in_from_edges.get(k, 0) + 1
            elif isinstance(e, (list, tuple)) and len(e) >= 2 and e[0] and e[1]:
                k = norm_url(e[1])
                in_from_edges[k] = in_from_edges.get(k, 0) + 1
    pages, seen = [], set()
    for p in data["pages"]:
        if not isinstance(p, dict) or not p.get("url"):
            continue
        k = norm_url(p["url"])
        if k in seen:
            continue
        seen.add(k)
        if k in in_from_edges:
            inlinks = in_from_edges[k]
        elif isinstance(p.get("inlinks"), (int, float)) and p["inlinks"] >= 0:
            inlinks = int(p["inlinks"])
        else:
            inlinks = None
        wc = None
        for f in WORD_FIELDS:
            wc = _int_or_none(p.get(f))
            if wc is not None:
                break
        pages.append({"key": k, "url": str(p["url"]),
                      "title": (p.get("title") or "").strip(),
                      "inlinks": inlinks, "word_count": wc})
    pages.sort(key=lambda p: p["key"])
    if not pages:
        return die("--crawl pages 为空:无清点范围(%s)" % path)
    return pages


# ---------------------------------------------------------------------------
# 四轴与四桶
# ---------------------------------------------------------------------------

def strong_axes(rec):
    """强轴名列表(流量/外链/AI 引用/战略——任一 >0 即强)。"""
    ax = rec["axes"]
    out = []
    if ax["traffic_clicks"] > 0:
        out.append("流量")
    if ax["backlinks"] > 0:
        out.append("外链")
    if ax["ai_citations"] > 0:
        out.append("AI 引用")
    if ax["strategic"]:
        out.append("战略")
    return out


def value_rank(rec):
    """组内 winner / redirect 目标排序键:强轴数 → 点击 → 入链(URL 序由调用方补)。"""
    return (len(strong_axes(rec)), rec["axes"]["traffic_clicks"],
            rec["inlinks"] or 0)


def _dirname(key):
    """norm_url 键 → 目录前缀(最后一段前的路径;根路径 → "/")。"""
    path = urllib.parse.urlparse("//" + key).path or "/"
    return path.rsplit("/", 1)[0] or "/"


def same_dir_target(key, pages, exclude_keys):
    """同目录最强页(remove 候选的 redirect 兜底目标):排除自身与同批 remove 页;
    排序=强轴数→点击→入链→URL 序;无候选 → None。"""
    d = _dirname(key)
    cands = [p for p in pages if p["key"] not in exclude_keys and _dirname(p["key"]) == d]
    if not cands:
        return None
    return sorted(cands, key=lambda p: (-value_rank(p)[0], -value_rank(p)[1],
                                        -value_rank(p)[2], p["key"]))[0]


def next_quarter_start(today):
    """下次全量清点日=下季度首日(季度节奏口径)。"""
    y, m = today.year, today.month
    if m < 4:
        return "%d-04-01" % y
    if m < 7:
        return "%d-07-01" % y
    if m < 10:
        return "%d-10-01" % y
    return "%d-01-01" % (y + 1)


def build_inventory(pages, gsc, backlinks, citations, citations_domain,
                    keep_set, keep_regexes, words_csv, word_floor, today):
    """四轴评估+四桶分桶+redirect map+AI 引用护栏+节奏建议(确定性;today 仅
    用于季度日期,不参与分桶)。"""
    notes = []
    # ---- 四轴填充 ----
    for p in pages:
        g = (gsc or {}).get(p["key"], {})
        p["axes"] = {
            "traffic_clicks": int(g.get("clicks", 0.0)),
            "backlinks": (backlinks or {}).get(p["key"], {}).get("count", 0),
            "ai_citations": citations.get(p["key"], 0) if citations else 0,
            "strategic": (p["key"] in keep_set) or
                         any(r.search(p["url"]) for r in keep_regexes),
        }
        p["axes_known"] = {
            "traffic": gsc is not None,
            "backlinks": backlinks is not None,
            "ai_citation": citations is not None,
        }
        if words_csv and p["key"] in words_csv:
            p["word_count"] = words_csv[p["key"]]
        p["stale"] = p["word_count"] is not None and p["word_count"] < word_floor
    if backlinks is None:
        notes.append("外链轴不可用(--backlinks 未提供或无目标列):remove 候选未经"
                     "外链核对,执行前必须补带 --backlinks 复跑")
    if citations is None:
        notes.append("AI 引用轴不可用(--panel 缺省):remove 候选未经 AI 引用核对——"
                     "防误删红线要求执行前必须补跑 citation_panel 后复跑本工具")
    if not keep_set and not keep_regexes:
        notes.append("战略轴未指定(--keep/--keep-regex 均缺省):全站按零战略值评估,"
                     "建议至少把模板页(/pricing、/about 等)列入再复跑")
    wc_missing = [p for p in pages if p["word_count"] is None]
    if wc_missing:
        notes.append("词数未知 %d/%d 页(crawl 页对象无 word_count 字段且未给 --words):"
                     "update 判定对这部分页跳过(不猜)" % (len(wc_missing), len(pages)))
    # ---- ① 重复组:title Simhash 聚类 ----
    clusters = cluster_titles(pages)
    by_key = {p["key"]: p for p in pages}
    cluster_winner_keys = []                            # 与 clusters 平行:每组 winner 的 key
    remove_keys = set()
    for p in pages:
        p["bucket"] = None
        p["cluster_winner"] = None
        p["redirect_target"] = None
        p["reasons"] = []
    for group in clusters:
        members = [by_key[k] for k in group]
        has_strong = any(strong_axes(m) for m in members)
        winner = max(members, key=lambda m: (value_rank(m), m["key"]))
        cluster_winner_keys.append(winner["key"])
        for m in members:
            if m["key"] == winner["key"]:
                continue
            m["cluster_winner"] = winner["key"]
            if has_strong:
                m["bucket"] = "consolidate"
                m["redirect_target"] = winner["url"]
                own = strong_axes(m)
                m["reasons"].append(
                    "title 与 %s 重复(组×%d):301 并入组内价值最高页%s" % (
                        winner["url"], len(group),
                        "(自身有%s轴,合并前人工权衡)" % "/".join(own) if own else ""))
            else:
                m["bucket"] = "remove"
                m["reasons"].append("title 重复组×%d 且组内四轴全零:整组无保留价值"
                                    % len(group))
                remove_keys.add(m["key"])
    # ---- ②③④ 非重复组成员与组 winner ----
    for p in pages:
        if p["bucket"]:
            continue
        strong = strong_axes(p)
        if strong:
            if p["stale"]:
                p["bucket"] = "update"
                p["reasons"].append("有%s轴但词数 %d<地板 %d:薄而有值,刷新优先"
                                    % ("/".join(strong), p["word_count"], word_floor))
            else:
                p["bucket"] = "keep"
                p["reasons"].append("有%s轴(词数未知,update 判定跳过)" % "/".join(strong)
                                    if p["word_count"] is None else
                                    "有%s轴" % "/".join(strong))
        else:
            p["bucket"] = "remove"
            p["reasons"].append("四轴全零(流量/外链/AI 引用/战略)")
            remove_keys.add(p["key"])
    # ---- AI 引用存量检查(防误删红线):被引页绝不入 remove 桶 ----
    cited_pages = [p for p in pages if p["axes"]["ai_citations"] > 0]
    guard_violations = [p for p in cited_pages if p["bucket"] == "remove"]
    for p in guard_violations:                          # 硬护栏:强制改判 keep
        p["bucket"] = "keep"
        p["reasons"].append("AI 引用保护:被引 %d 次的页绝不入 remove 桶(防误删红线)"
                            % p["axes"]["ai_citations"])
        remove_keys.discard(p["key"])
    # ---- remove 候选的 redirect 兜底目标(同目录最强页;无 → 410 建议) ----
    for p in pages:
        if p["bucket"] == "remove":
            t = same_dir_target(p["key"], pages, remove_keys)
            if t is not None:
                p["redirect_target"] = t["url"]
    # ---- 汇总 ----
    buckets = {b: sorted(p["url"] for p in pages if p["bucket"] == b)
               for b in ("keep", "update", "consolidate", "remove")}
    redirect_map = {p["url"]: p["redirect_target"] for p in pages
                    if p["bucket"] in ("consolidate", "remove") and p["redirect_target"]}
    domain_cited_not_in_crawl = []
    if citations and citations_domain:
        universe = {p["key"] for p in pages}
        for k, n in sorted(citations.items()):
            if k in universe:
                continue
            host = urllib.parse.urlparse(k).netloc.lower().split(":", 1)[0]
            if host == citations_domain or host.endswith("." + citations_domain):
                domain_cited_not_in_crawl.append(
                    {"url": "https:" + k if k.startswith("//") else k, "citations": n})
    elif citations and not citations_domain:
        notes.append("panel.json 无 domain 字段:crawl 未覆盖的被引页无法按站过滤,清单从缺")
    guard = {"cited_pages": len(cited_pages),
             "remove_bucket_hits": len(guard_violations),
             "note": "被引页绝不入 remove 桶(防误删红线);remove_bucket_hits 恒 0",
             "cited_not_in_crawl": domain_cited_not_in_crawl}
    return {"schema_version": SCHEMA_VERSION, "tool": "content_inventory",
            "generated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "word_floor": word_floor,
            "universe": {"pages": len(pages)},
            "axes": {
                "traffic": {"known": gsc is not None,
                            "pages_with_value": sum(1 for p in pages
                                                    if p["axes"]["traffic_clicks"] > 0)},
                "backlinks": {"known": backlinks is not None,
                              "pages_with_value": sum(1 for p in pages
                                                      if p["axes"]["backlinks"] > 0)},
                "ai_citation": {"known": citations is not None,
                                "pages_with_value": len(cited_pages)},
                "strategic": {"provided": bool(keep_set or keep_regexes),
                              "pages": sum(1 for p in pages if p["axes"]["strategic"])}},
            "buckets": buckets,
            "clusters": [{"winner": by_key[wk]["url"], "members": group}
                         for group, wk in zip(clusters, cluster_winner_keys)],
            "pages": [{"url": p["url"], "bucket": p["bucket"],
                       "axes": p["axes"], "axes_known": p["axes_known"],
                       "word_count": p["word_count"], "stale": p["stale"],
                       "cluster_winner": p["cluster_winner"],
                       "redirect_target": p["redirect_target"],
                       "reasons": p["reasons"]} for p in pages],
            "redirect_map": redirect_map,
            "ai_citation_guard": guard,
            "cadence": build_cadence(buckets, len(clusters), guard, today),
            "notes": notes}


def build_cadence(buckets, n_clusters, guard, today):
    """季度节奏建议(下次全量清点=下季度首日;各桶行动节奏)。"""
    suggestions = [
        "keep %d 页:季度复审即可(四轴再核),无动作" % len(buckets["keep"]),
        "update %d 页:按流量轴降序排入本季刷新计划(薄而有值优先救),刷新后复测"
        % len(buckets["update"]),
        "consolidate %d 页(%d 个重复组):本季内 301 合并(redirect map 草稿已给),"
        "合并后 30 天复跑核对收录" % (len(buckets["consolidate"]), n_clusters),
        "remove %d 页(候选):执行前 30 天内复跑本工具并强制带 --panel + --backlinks"
        "(AI 引用/外链再核对),仍全零才执行;能 301 尽量不 410" % len(buckets["remove"]),
        "AI 引用存量检查:%d 被引页,remove 桶命中 %d(被引页绝不入 remove)"
        % (guard["cited_pages"], guard["remove_bucket_hits"]),
    ]
    if guard["cited_not_in_crawl"]:
        suggestions.append("crawl 未覆盖的被引页 %d 个:补爬后入册(绝不删除)"
                           % len(guard["cited_not_in_crawl"]))
    return {"next_full_audit": next_quarter_start(today), "suggestions": suggestions}


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------

def render_markdown(rep):
    L = ["## 站点内容库存四轴审计(content_inventory)", ""]
    ax = rep["axes"]
    L.append("清点范围:crawl %d 页 · 轴覆盖:流量%s / 外链%s / AI 引用%s / 战略%s · 词数地板 %d"
             % (rep["universe"]["pages"],
                "✓" if ax["traffic"]["known"] else "✗",
                "✓" if ax["backlinks"]["known"] else "✗",
                "✓" if ax["ai_citation"]["known"] else "✗",
                "✓" if ax["strategic"]["provided"] else "✗",
                rep["word_floor"]))
    b = rep["buckets"]
    L.append("四桶:keep %d / update %d / consolidate %d / remove %d(候选)· 重复组 %d 组"
             % (len(b["keep"]), len(b["update"]), len(b["consolidate"]),
                len(b["remove"]), len(rep["clusters"])))
    L.append("")
    by_url = {p["url"]: p for p in rep["pages"]}
    sections = [
        ("keep", "### keep(%d 页)——至少一轴有值(流量/外链/AI 引用/战略)" % len(b["keep"])),
        ("update", "### update(%d 页)——有值但词数<地板 %d,刷新优先"
         % (len(b["update"]), rep["word_floor"])),
        ("consolidate", "### consolidate(%d 页)——title 重复组,301 并入组内价值最高页"
         % len(b["consolidate"])),
        ("remove", "### remove 候选(%d 页)——四轴全零(人工复核,执行前 30 天复跑)"
         % len(b["remove"])),
    ]
    for key, title in sections:
        L.append(title)
        L.append("")
        urls = b[key]
        if not urls:
            L.append("(无)")
            L.append("")
            continue
        L.append("| URL | 流量(点击) | 外链 | AI 引用 | 战略 | 词数 | 说明 |")
        L.append("|---|---|---|---|---|---|---|")
        for u in urls:
            p = by_url[u]
            a, kn = p["axes"], p["axes_known"]
            wc = "?" if p["word_count"] is None else str(p["word_count"])
            L.append("| %s | %s | %s | %s | %s | %s%s | %s |" % (
                u, a["traffic_clicks"],
                str(a["backlinks"]) if kn["backlinks"] else "?",
                str(a["ai_citations"]) if kn["ai_citation"] else "?",
                "✓" if a["strategic"] else "✗",
                wc, "(陈旧)" if p["stale"] else "",
                "; ".join(p["reasons"])))
        L.append("")
    if rep["redirect_map"]:
        L.append("### redirect map 草稿")
        L.append("")
        for src, dst in sorted(rep["redirect_map"].items()):
            p = by_url[src]
            kind = "consolidate 并入组内价值最高页" if p["bucket"] == "consolidate" \
                else "remove 候选并入同目录最强页"
            L.append("- %s → 301 → %s(%s)" % (src, dst, kind))
        L.append("")
    rm_no_target = sorted(p["url"] for p in rep["pages"]
                          if p["bucket"] == "remove" and not p["redirect_target"])
    if rm_no_target:
        L.append("- remove 候选无同目录目标(410 建议):%s" % ", ".join(rm_no_target))
        L.append("")
    g = rep["ai_citation_guard"]
    L.append("### AI 引用存量检查(防误删红线)")
    L.append("")
    L.append("- 被引页 %d 个(计入 AI 引用轴):remove 桶命中 %d——被引页绝不入 remove 桶"
             % (g["cited_pages"], g["remove_bucket_hits"]))
    if g["cited_not_in_crawl"]:
        L.append("- crawl 未覆盖的被引页 %d 个(补爬入册,绝不删除):%s"
                 % (len(g["cited_not_in_crawl"]),
                    ", ".join("%s(被引 %d 次)" % (c["url"], c["citations"])
                              for c in g["cited_not_in_crawl"])))
    L.append("")
    L.append("### 季度节奏建议")
    L.append("")
    L.append("- 下次全量清点:%s(季度节奏)" % rep["cadence"]["next_full_audit"])
    for s in rep["cadence"]["suggestions"]:
        L.append("- %s" % s)
    L.append("")
    if rep["notes"]:
        for n in rep["notes"]:
            L.append("> 降级声明:%s" % n)
    else:
        L.append("> 四轴数据齐备,无降级项")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="content_inventory.py",
        description="站点内容库存四轴治理审计(R6):流量/外链/AI 引用/战略四轴 →"
                    " keep/update/consolidate/remove 四桶 + redirect map 草稿 +"
                    " 季度节奏;被引页绝不入 remove 桶(防误删红线)。",
        epilog=USAGE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--crawl", required=True, help="site_crawl.py 输出 crawl.json(清点范围)")
    ap.add_argument("--gsc", required=True, help="GSC 导出 CSV(流量轴:Clicks)")
    ap.add_argument("--panel", help="citation_panel.py 的 panel.json(AI 引用轴)")
    ap.add_argument("--backlinks", help="带目标列的外链导出 CSV(外链轴)")
    ap.add_argument("--keep", help="战略页 URL 清单(完整 URL 每行一个)")
    ap.add_argument("--keep-regex", action="append", default=[], metavar="RE",
                    help="战略页 URL 正则(可重复,如 /pricing|/about)")
    ap.add_argument("--words", help="词数 CSV(Page,Words;补 crawl 缺失的 word_count)")
    ap.add_argument("--word-floor", type=int, default=WORD_FLOOR_DEFAULT,
                    help="词数地板(默认 300,低于即 update 触发条件)")
    ap.add_argument("--json", action="store_true", help="结构化输出")
    args = ap.parse_args(argv)

    pages = load_crawl(args.crawl)
    gsc = load_gsc(args.gsc)
    backlinks, bnote = (None, None)
    if args.backlinks:
        backlinks, bnote = load_backlinks(args.backlinks)
    citations, citations_domain = (None, None)
    if args.panel:
        citations, citations_domain = load_panel_citations(args.panel)
    keep_set = load_keep(args.keep) if args.keep else set()
    keep_regexes = []
    for r in args.keep_regex:
        try:
            keep_regexes.append(re.compile(r))
        except re.error as e:
            return die("--keep-regex 非法 %r: %s" % (r, e))
    words_csv = load_words(args.words) if args.words else {}
    today = datetime.now(timezone.utc).date()

    rep = build_inventory(pages, gsc, backlinks, citations, citations_domain,
                          keep_set, keep_regexes, words_csv, args.word_floor, today)
    if bnote:
        rep["notes"].append(bnote)
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(render_markdown(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
