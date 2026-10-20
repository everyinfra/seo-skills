#!/usr/bin/env python3
"""question_align.py — 提问对齐候选页清单(stdlib only)。

方法见 references/content/question-alignment.md:页面的 title、H1、首段和 meta description
用买家提问的原词,首段第一句直接回答。本脚本只做「找页 + 量差距」,不改写文案。

输入:
  --gsc FILE            查询×页面 CSV。列名接受 gsc_api.py 规范化输出(Query,Page,Clicks,Impressions,CTR,Position),
                        也接受 GSC 网页导出的 "Top queries" / "Top pages" 写法;CTR 可以是 0.031 或 "3.1%"。
  --pages FILE          页面级 CSV(Page,Clicks,Impressions,CTR,Position;gsc_api.py query --dimensions page)。
                        建议给:查询×页面导出不含匿名查询,只有页面级数据才能按真实展示选页、算匿名占比。
  --min-impressions N   选页门槛:页面展示 ≥ N(默认 20,本套件口径,各站自定)
  --max-clicks N        选页门槛:页面点击 ≤ N(默认 0)
  --max-position P      平均排名 > P 的页标 rank_first:先查排名,不先改标题(默认 10,本套件口径)
  --brand REGEX         品牌查询正则(大小写不敏感),从查询覆盖计算中排除
  --top-queries N       每页列出的查询数(默认 5)
  --fetch               抓取线上页面的 title / H1 / meta description / 首段(仅 http(s);拒私网、环回、链路本地;
                        重定向逐跳复查;不发 Accept-Language,和 Googlebot 一致)
  --html-dir DIR        离线读取页面 HTML:文件名 = URL 的 sha1 前 16 位 + ".html"(测试和无网环境用)
  --page URL            单页网页导出(Queries.csv 没有页面列)时,把所有行记到这个 URL
  --json                结构化输出(schema_version=1)

诊断标签(每页可多个):
  rank_first   平均排名 > --max-position:问题主要在排名,标题改写收益小
  anonymized   可见查询的展示不到页面展示的 20%(GSC 隐去了大部分查询;--pages 缺省时只看有没有可见查询):
               只能按页面主题、工单原话、Bing 查询推断提问,不据可见查询判断覆盖
  title_gap    展示最多的可见查询(且展示 ≥ 3),在 title 里的词覆盖率 < 0.5
  lead_gap     同一查询在「首段 + description」里的词覆盖率 < 0.5
  aligned      title、首段覆盖率都 ≥ 0.8 仍零点击:去看 SERP(结果类型、摘要是否被改写)
  (anonymized 的页不打 title_gap / lead_gap / aligned:可见查询太少,覆盖率没有代表性)
  no_fetch     没有页面内容(未用 --fetch / --html-dir,或抓取失败):只给数据,不给覆盖率

每个查询另给 missing_terms(title / h1 / lead 各缺哪些查询词,改写素材;脚本不生成文案)。
每页给 expected_clicks = 页面展示 × 本站同排名段 CTR(段:1–3 / 4–6 / 7–10 / 11–20 / 21+,
用 --pages 的全部页面算;没有 --pages 时用查询行;给了 --brand 时,可见查询里品牌词展示 ≥ 50% 的页
不进基线,避免品牌导航页拉高 CTR),报告头部列出各段 CTR。

词覆盖率:查询切成「词」后,在目标文本里出现的比例。字母文字按 Unicode 字母连续段分词(长度 ≥ 2,
小写;土耳其 İ 先折成 i);汉字与泰文按相邻两字(bigram;泰文以近似字素为单位);混排时合并。这是本套件口径,只用来排序和提示,不是 Google 的算法。

退出码:0 正常;2 输入错误(文件缺失、列名不认识、参数不合法)。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import ipaddress
import json
import os
import re
import socket
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

SCHEMA_VERSION = 1
ANON_SHARE = 0.8        # 可见查询展示 < 20% → anonymized(本套件口径)
MIN_QUERY_IMPR = 3      # 主查询展示 < 3 时不判覆盖(本套件口径:1–2 次展示没有代表性)
UA = "Mozilla/5.0 (compatible; seo-suite-question-align/1.0)"
CJK_RE = re.compile(r"[㐀-䶿一-鿿豈-﫿]")

QUERY_COLS = ("query", "top queries", "queries", "consulta", "查询")
PAGE_COLS = ("page", "top pages", "pages", "url", "landing page", "网页", "页面")


class InputError(Exception):
    pass


# ---------------------------------------------------------------- CSV 读取 --

def _norm_key(k: str) -> str:
    return (k or "").strip().lower().lstrip("﻿")


def _pick(row: dict, names) -> str | None:
    for n in names:
        if n in row:
            return row[n]
    return None


def parse_number(v) -> float:
    s = (v or "").strip().replace(",", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        raise InputError(f"不是数字: {v!r}")


def parse_ctr(v) -> float:
    """CTR 统一成小数。带 % 的一律 /100(GSC 网页导出是 "3.1%");不带 % 的按小数(API 输出 0.031)。"""
    s = (v or "").strip()
    if not s:
        return 0.0
    if s.endswith("%"):
        return parse_number(s[:-1]) / 100.0
    return parse_number(s)


def read_rows(path: str, need_query: bool, page_override: str | None = None) -> list[dict]:
    if not os.path.isfile(path):
        raise InputError(f"文件不存在: {path}")
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [{_norm_key(k): v for k, v in r.items()} for r in reader]
    if not rows:
        return []
    keys = set(rows[0])
    if not any(c in keys for c in PAGE_COLS) and not page_override:
        raise InputError(f"{path}: 找不到页面列(接受 {', '.join(PAGE_COLS)});单页导出请加 --page URL")
    if need_query and not any(c in keys for c in QUERY_COLS):
        raise InputError(f"{path}: 找不到查询列(接受 {', '.join(QUERY_COLS)})")
    out = []
    for r in rows:
        rec = {
            "page": (page_override or _pick(r, PAGE_COLS) or "").strip(),
            "clicks": parse_number(_pick(r, ("clicks", "点击次数", "clics")) or "0"),
            "impressions": parse_number(_pick(r, ("impressions", "展示", "展示次数", "impresiones")) or "0"),
            "ctr": parse_ctr(_pick(r, ("ctr",)) or "0"),
            "position": parse_number(_pick(r, ("position", "排名", "平均排名", "posición")) or "0"),
        }
        if need_query:
            rec["query"] = (_pick(r, QUERY_COLS) or "").strip()
        out.append(rec)
    return out


# ---------------------------------------------------------------- 分词与覆盖 --

def _fold(text: str) -> str:
    """NFC + 土耳其 İ→i 再小写(İ.lower() 会变 i+U+0307,组合点把词劈开或对不上)。"""
    t = unicodedata.normalize("NFC", text or "").replace("İ", "i")
    return t.lower().replace("i\u0307", "i")


def _is_thai(c: str) -> bool:
    return "\u0e00" <= c <= "\u0e7f"


def _clusters(run: str) -> list[str]:
    """泰文近似字素:组合符号(M*)与 SARA AM(U+0E33)并入前一字符。"""
    out: list[str] = []
    for c in run:
        if out and (unicodedata.category(c)[0] == "M" or c == "\u0e33"):
            out[-1] += c
        else:
            out.append(c)
    return out


def tokens(text: str) -> set[str]:
    """按 Unicode 字母类分词(B51 修,2026-10-21):字母/数字连续段为词,组合符号附着在词内;
    汉字与泰文(都不用空格分词)取相邻二元组。修前 ASCII+拉丁扩展字符表把越南 thế 截成 th、
    丢 İ、泰文返回空集。"""
    t = _fold(text)
    toks: set[str] = set()
    runs: list[str] = []
    cur = ""
    for c in t:
        cat = unicodedata.category(c)[0]
        if cat in ("L", "N") or (cat == "M" and cur):
            cur += c
        else:
            if cur:
                runs.append(cur)
            cur = ""
    if cur:
        runs.append(cur)
    han = ""
    for r in runs:
        # 同一连续段内按文字切换再分:拉丁/西里尔等成词,泰文取二元组,汉字并入 han
        segs: list[list] = []
        for c in r:
            kind = "han" if CJK_RE.match(c) else ("thai" if _is_thai(c) else "word")
            if segs and segs[-1][0] == kind:
                segs[-1][1] += c
            else:
                segs.append([kind, c])
        for kind, seg in segs:
            if kind == "han":
                han += seg
            elif kind == "word":
                if len(seg) >= 2:
                    toks.add(seg)
            else:
                cl = _clusters(seg)
                if len(cl) == 1:
                    toks.add(cl[0])
                toks.update(cl[i] + cl[i + 1] for i in range(len(cl) - 1))
    if len(han) == 1:
        toks.add(han)
    toks.update(han[i:i + 2] for i in range(len(han) - 1))
    return toks


def missing_terms(query: str, target: str) -> list[str]:
    tt = _fold(target)
    return sorted(x for x in tokens(query) if x not in tt)


POS_BUCKETS = ((1, 3), (4, 6), (7, 10), (11, 20), (21, 10**9))


def bucket_of(pos: float):
    for lo, hi in POS_BUCKETS:
        if lo <= round(pos) <= hi:
            return (lo, hi)
    return POS_BUCKETS[0]


def site_ctr_by_bucket(rows) -> dict:
    """本站分段 CTR:按平均排名分 1–3 / 4–6 / 7–10 / 11–20 / 21+,各段 Σ点击 ÷ Σ展示。"""
    agg: dict = {}
    for r in rows:
        if r["impressions"] <= 0:
            continue
        b = bucket_of(r["position"] or 1)
        a = agg.setdefault(b, [0.0, 0.0])
        a[0] += r["clicks"]
        a[1] += r["impressions"]
    return {b: (c / i if i else 0.0) for b, (c, i) in agg.items()}


def coverage(query: str, target: str) -> float | None:
    qt = tokens(query)
    if not qt:
        return None
    tt = _fold(target)
    return round(sum(1 for x in qt if x in tt) / len(qt), 2)


# ---------------------------------------------------------------- 页面解析 --

class PageParser(HTMLParser):
    """取 <head> 里的第一个 <title>(忽略 body 里 SVG 的 <title>)、第一个 H1、meta description、
    <main>(没有 main 时用 body)里第一段 ≥ 30 字符的 <p>。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.h1 = ""
        self.description = None
        self.lead = ""
        self._stack = []
        self._in_title = False
        self._title_done = False
        self._in_h1 = False
        self._h1_done = False
        self._in_svg = 0
        self._main_depth = 0
        self._saw_main = False
        self._p_buf = None
        self._p_in_main = False
        self._body_lead = ""

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "svg":
            self._in_svg += 1
        elif tag == "title" and not self._title_done and not self._in_svg:
            self._in_title = True
        elif tag == "h1" and not self._h1_done:
            self._in_h1 = True
        elif tag == "meta" and a.get("name", "").lower() == "description" and self.description is None:
            self.description = a.get("content", "")
        elif tag == "main":
            self._main_depth += 1
            self._saw_main = True
        elif tag == "p" and self._p_buf is None:
            self._p_buf = []
            self._p_in_main = self._main_depth > 0

    def handle_endtag(self, tag):
        if tag == "svg" and self._in_svg:
            self._in_svg -= 1
        elif tag == "title" and self._in_title:
            self._in_title = False
            self._title_done = True
        elif tag == "h1" and self._in_h1:
            self._in_h1 = False
            self._h1_done = True
        elif tag == "main" and self._main_depth:
            self._main_depth -= 1
        elif tag == "p" and self._p_buf is not None:
            txt = re.sub(r"\s+", " ", "".join(self._p_buf)).strip()
            if len(txt) >= 30:
                if self._p_in_main and not self.lead:
                    self.lead = txt
                elif not self._body_lead:
                    self._body_lead = txt
            self._p_buf = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_h1:
            self.h1 += data
        if self._p_buf is not None:
            self._p_buf.append(data)

    def result(self) -> dict:
        lead = self.lead or ("" if self._saw_main else self._body_lead)
        return {"title": re.sub(r"\s+", " ", self.title).strip(),
                "h1": re.sub(r"\s+", " ", self.h1).strip(),
                "description": (self.description or "").strip(),
                "lead": lead}


def parse_page(html: str) -> dict:
    p = PageParser()
    p.feed(html)
    return p.result()


def html_cache_name(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16] + ".html"


def _reject_private(host: str):
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as e:
        raise InputError(f"解析不了主机 {host}: {e}")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise InputError(f"拒绝访问内网/保留地址: {host} → {ip}")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002(接口签名固定)
        return None


def fetch(url: str, timeout: float = 20.0, max_hops: int = 5, max_bytes: int = 4_000_000) -> tuple[str, str]:
    """返回 (最终 URL, HTML)。逐跳检查 scheme 与主机,不发 Accept-Language。"""
    opener = urllib.request.build_opener(_NoRedirect)
    cur = url
    for _ in range(max_hops + 1):
        parts = urllib.parse.urlsplit(cur)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise InputError(f"只接受 http(s) URL: {cur}")
        _reject_private(parts.hostname)
        req = urllib.request.Request(cur, headers={"User-Agent": UA, "Accept": "text/html,*/*;q=0.8"})
        try:
            resp = opener.open(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
                cur = urllib.parse.urljoin(cur, e.headers["Location"])
                continue
            raise
        body = resp.read(max_bytes)
        charset = resp.headers.get_content_charset() or "utf-8"
        return cur, body.decode(charset, "replace")
    raise InputError(f"重定向超过 {max_hops} 跳: {url}")


# ---------------------------------------------------------------- 分析 --

def build_report(qrows, prows, *, min_impr=20.0, max_clicks=0.0, max_pos=10.0, brand=None,
                 top_n=5, page_content=None) -> dict:
    brand_re = re.compile(brand, re.I) if brand else None
    by_page_q: dict[str, list] = {}
    brand_impr: dict[str, float] = {}
    all_q_impr: dict[str, float] = {}
    for r in qrows:
        if not r["page"] or not r.get("query"):
            continue
        all_q_impr[r["page"]] = all_q_impr.get(r["page"], 0.0) + r["impressions"]
        if brand_re and brand_re.search(r["query"]):
            brand_impr[r["page"]] = brand_impr.get(r["page"], 0.0) + r["impressions"]
            continue
        by_page_q.setdefault(r["page"], []).append(r)
    brand_pages = {p for p, bi in brand_impr.items() if all_q_impr.get(p) and bi / all_q_impr[p] >= 0.5}

    if prows:
        totals = {r["page"]: r for r in prows if r["page"]}
    else:  # 没有页面级数据:用查询×页面求和(会漏掉匿名查询,报告里注明)
        totals = {}
        for r in qrows:
            t = totals.setdefault(r["page"], {"page": r["page"], "clicks": 0.0, "impressions": 0.0,
                                              "_pos_w": 0.0})
            t["clicks"] += r["clicks"]
            t["impressions"] += r["impressions"]
            t["_pos_w"] += r["position"] * r["impressions"]
        for t in totals.values():
            t["position"] = round(t["_pos_w"] / t["impressions"], 2) if t["impressions"] else 0.0
            t["ctr"] = t["clicks"] / t["impressions"] if t["impressions"] else 0.0

    bucket_ctr = site_ctr_by_bucket([v for k, v in totals.items() if k not in brand_pages])
    pages = []
    for url, t in totals.items():
        if t["impressions"] < min_impr or t["clicks"] > max_clicks:
            continue
        qs = sorted(by_page_q.get(url, []), key=lambda r: -r["impressions"])
        q_impr = sum(r["impressions"] for r in by_page_q.get(url, []))
        content = (page_content or {}).get(url)
        rec = {
            "page": url,
            "impressions": int(t["impressions"]),
            "clicks": int(t["clicks"]),
            "ctr": round(t.get("ctr") or 0.0, 4),
            "position": round(t.get("position") or 0.0, 2),
            "visible_query_impressions": int(q_impr),
            "anonymized_share": round(max(0.0, 1 - q_impr / t["impressions"]), 2) if t["impressions"] else None,
            "expected_clicks": round(t["impressions"] * bucket_ctr.get(bucket_of(t.get("position") or 1), 0.0), 1),
            "queries": [],
            "flags": [],
        }
        if content:
            rec.update({k: content.get(k, "") for k in ("title", "h1", "description", "lead")})
        for r in qs[:top_n]:
            q = {"query": r["query"], "impressions": int(r["impressions"]), "clicks": int(r["clicks"]),
                 "position": round(r["position"], 2)}
            if content:
                q["cov_title"] = coverage(r["query"], content.get("title", ""))
                q["cov_h1"] = coverage(r["query"], content.get("h1", ""))
                q["cov_lead"] = coverage(r["query"], (content.get("lead", "") + " " + content.get("description", "")))
                q["missing_terms"] = {
                    "title": missing_terms(r["query"], content.get("title", "")),
                    "h1": missing_terms(r["query"], content.get("h1", "")),
                    "lead": missing_terms(r["query"], content.get("lead", "") + " " + content.get("description", "")),
                }
            rec["queries"].append(q)
        if rec["position"] > max_pos:
            rec["flags"].append("rank_first")
        anonymized = (not qs) or (rec["anonymized_share"] is not None and prows and rec["anonymized_share"] > ANON_SHARE)
        if anonymized:
            rec["flags"].append("anonymized")
        if not content:
            rec["flags"].append("no_fetch")
        elif rec["queries"] and not anonymized and rec["queries"][0]["impressions"] >= MIN_QUERY_IMPR:
            top = rec["queries"][0]
            ct, cl = top.get("cov_title"), top.get("cov_lead")
            if ct is not None and ct < 0.5:
                rec["flags"].append("title_gap")
            if cl is not None and cl < 0.5:
                rec["flags"].append("lead_gap")
            if ct is not None and cl is not None and ct >= 0.8 and cl >= 0.8:
                rec["flags"].append("aligned")
        pages.append(rec)
    pages.sort(key=lambda r: (-r["impressions"], r["page"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "site_ctr_by_position": {f"{lo}-{hi if hi < 10**9 else ''}": round(v, 4) for (lo, hi), v in sorted(bucket_ctr.items())},
        "ctr_baseline_excluded_brand_pages": len(brand_pages),
        "params": {"min_impressions": min_impr, "max_clicks": max_clicks, "max_position": max_pos,
                   "brand": brand, "top_queries": top_n,
                   "page_totals_source": "pages_csv" if prows else "sum_of_query_rows"},
        "candidates": pages,
        "summary": {
            "candidates": len(pages),
            "impressions": sum(p["impressions"] for p in pages),
            "rank_first": sum(1 for p in pages if "rank_first" in p["flags"]),
            "anonymized": sum(1 for p in pages if "anonymized" in p["flags"]),
            "title_gap": sum(1 for p in pages if "title_gap" in p["flags"]),
            "lead_gap": sum(1 for p in pages if "lead_gap" in p["flags"]),
            "aligned": sum(1 for p in pages if "aligned" in p["flags"]),
        },
    }


def render_markdown(rep: dict) -> str:
    s = rep["summary"]
    p = rep["params"]
    lines = [
        "## question_align:提问对齐候选页",
        "",
        f"- 选页:展示 ≥ {p['min_impressions']:g}、点击 ≤ {p['max_clicks']:g};排名 > {p['max_position']:g} 标 rank_first。",
        f"- 页面展示来源:{'页面级 CSV' if p['page_totals_source'] == 'pages_csv' else '查询×页面求和(不含匿名查询,会低估展示)'}。",
        f"- 候选 {s['candidates']} 页,合计展示 {s['impressions']};rank_first {s['rank_first']}、anonymized {s['anonymized']}、"
        f"title_gap {s['title_gap']}、lead_gap {s['lead_gap']}、aligned {s['aligned']}。",
        "",
        "| 页面 | 展示 | 点击 | 期望点击 | 排名 | 匿名占比 | 标签 | 主查询(展示/排名/title 覆盖/首段覆盖) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rep["candidates"]:
        if r["queries"]:
            q = r["queries"][0]
            qs = f"{q['query']}({q['impressions']}/{q['position']:g}/{q.get('cov_title', '-')}/{q.get('cov_lead', '-')})"
        else:
            qs = "—"
        anon = "-" if r["anonymized_share"] is None else f"{r['anonymized_share']:.0%}"
        lines.append(f"| {r['page']} | {r['impressions']} | {r['clicks']} | {r['expected_clicks']:g} | {r['position']:g} | {anon} | "
                     f"{', '.join(r['flags']) or '-'} | {qs} |")
    lines += ["", "下一步:按 references/content/question-alignment.md 改写 title、首段;rank_first 先查排名。"]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="提问对齐候选页清单(stdlib only;方法见 references/content/question-alignment.md)")
    ap.add_argument("--gsc", required=True, metavar="FILE", help="查询×页面 CSV")
    ap.add_argument("--pages", metavar="FILE", help="页面级 CSV(建议给)")
    ap.add_argument("--min-impressions", type=float, default=20.0, metavar="N")
    ap.add_argument("--max-clicks", type=float, default=0.0, metavar="N")
    ap.add_argument("--max-position", type=float, default=10.0, metavar="P")
    ap.add_argument("--brand", metavar="REGEX")
    ap.add_argument("--top-queries", type=int, default=5, metavar="N")
    ap.add_argument("--page", metavar="URL", help="单页导出没有页面列时,所有行记到这个 URL")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--fetch", action="store_true", help="抓取线上页面内容")
    src.add_argument("--html-dir", metavar="DIR", help="离线 HTML 目录(文件名=URL sha1 前 16 位 + .html)")
    ap.add_argument("--timeout", type=float, default=20.0, metavar="SEC")
    ap.add_argument("--json", action="store_true", help="结构化输出")
    a = ap.parse_args(argv)
    try:
        if a.min_impressions < 0 or a.max_clicks < 0 or a.top_queries < 1:
            raise InputError("门槛不能为负,--top-queries 至少 1")
        if a.brand:
            try:
                re.compile(a.brand)
            except re.error as e:
                raise InputError(f"--brand 不是合法正则: {e}")
        qrows = read_rows(a.gsc, need_query=True, page_override=a.page)
        prows = read_rows(a.pages, need_query=False) if a.pages else []
    except InputError as e:
        sys.stderr.write(f"输入错误: {e}\n")
        return 2
    pre = build_report(qrows, prows, min_impr=a.min_impressions, max_clicks=a.max_clicks,
                       max_pos=a.max_position, brand=a.brand, top_n=a.top_queries)
    content = {}
    if a.fetch or a.html_dir:
        for r in pre["candidates"]:
            url = r["page"]
            try:
                if a.html_dir:
                    path = os.path.join(a.html_dir, html_cache_name(url))
                    if not os.path.isfile(path):
                        continue
                    with open(path, encoding="utf-8", errors="replace") as f:
                        html = f.read()
                    final = url
                else:
                    final, html = fetch(url, timeout=a.timeout)
                parsed = parse_page(html)
                if final != url:
                    parsed["redirected_to"] = final
                content[url] = parsed
            except (InputError, urllib.error.URLError, OSError) as e:
                sys.stderr.write(f"[warn] 取不到 {url}: {e}\n")
    rep = build_report(qrows, prows, min_impr=a.min_impressions, max_clicks=a.max_clicks,
                       max_pos=a.max_position, brand=a.brand, top_n=a.top_queries, page_content=content)
    for r in rep["candidates"]:
        red = content.get(r["page"], {}).get("redirected_to")
        if red:
            r["redirected_to"] = red
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(render_markdown(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
