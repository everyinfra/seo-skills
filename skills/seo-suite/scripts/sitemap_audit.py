#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sitemap_audit.py — Sitemap 六坏桶审计 + lastmod 三判定 (仅标准库).

用法:
  python3 sitemap_audit.py https://example.com
  python3 sitemap_audit.py https://example.com/sitemap.xml --check-limit 20
  python3 sitemap_audit.py https://example.com --must-include https://example.com/pricing

规则摘要:
  * 入口 URL 不以 .xml/.gz 结尾时自动请求 {origin}/sitemap.xml; 支持 sitemapindex 递归 1 层
    (子节点若仍是 index, 提示不再下钻)
  * 六坏桶:
      桶1 非200      : loc 返回 4xx/5xx 或抓取失败
      桶2 3xx重定向  : loc 返回 301/302/303/307/308 (sitemap 中不应有重定向)
      桶3 noindex    : meta robots 或 x-robots-tag 含 noindex
      桶4 canonical他指: <link rel=canonical> 规范化后 != 自身 URL
      桶5 robots屏蔽 : robots.txt 按 Googlebot 判定 can_fetch() = False
      桶6 参数重复   : 同一 path 不同 query 的多组 URL
  * lastmod 三判定:
      Coverage     = 有 lastmod 条目占比 (期望 1.0)
      Freshness    = 最新 lastmod 距今 <= 30 天
      Truthfulness = 最大"单日簇"占比 > 50% 且该日 == 今天 -> 疑似构建期伪造
  * 规模提示: 单文件 > 50,000 URL 或 > 50MB 超出 Google 单 sitemap 上限, 建议拆分
  * --check-limit N 限制逐条抓取检查的 loc 数 (默认 50, 0=全部);
    参数重复与 lastmod 统计始终基于全量 loc

退出码: 六坏桶任一非空或 --must-include 有缺失 -> 1; sitemap 不可达/不可解析 -> 2; 正常 0.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; SEOSkill-SitemapAudit/1.0)"
FIFTY_MB = 50 * 1024 * 1024
FIFTY_K = 50000


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """禁用自动跟随重定向, 以便把 3xx 本身当作审计结果."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def fetch(url, timeout=10.0, max_bytes=5_000_000):
    """GET 且不跟随重定向. 返回 (status, headers, body_bytes); 网络层异常向上抛."""
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    try:
        with _OPENER.open(req, timeout=timeout) as resp:
            return resp.status, resp.headers, resp.read(max_bytes)
    except urllib.error.HTTPError as e:
        try:
            body = e.read(65536)
        except Exception:
            body = b""
        return e.code, getattr(e, "headers", None), body


def decode(body, headers):
    """按 Content-Type / meta charset / 常见兜底顺序解码字节流."""
    charset = None
    ct = ""
    try:
        ct = headers.get("Content-Type") or "" if headers else ""
    except Exception:
        ct = ""
    if ct:
        m = re.search(r"charset=([\w\-]+)", ct, re.I)
        if m:
            charset = m.group(1)
    if not charset and body:
        m = re.search(rb'charset=["\']?([\w\-]+)', body[:4096], re.I)
        if m:
            charset = m.group(1).decode("ascii", "replace")
    for enc in (charset, "utf-8", "gb18030", "latin-1"):
        if not enc:
            continue
        try:
            return body.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", "replace")


class HeadParser(HTMLParser):
    """仅提取 meta robots 与 link rel=canonical."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta_robots = []
        self.canonical = None

    def handle_starttag(self, tag, attrs):
        try:
            a = {k.lower(): (v or "") for k, v in attrs}
            if tag == "meta" and a.get("name", "").lower() == "robots":
                self.meta_robots.append(a.get("content", ""))
            elif tag == "link" and "canonical" in a.get("rel", "").lower().split():
                if a.get("href") and not self.canonical:
                    self.canonical = a["href"]
        except Exception:
            pass


def norm_url(u, base=None):
    """规范化 URL: 补 base, 小写 scheme/host, 去默认端口/fragment, 排序 query."""
    try:
        if base and not urllib.parse.urlsplit(u).scheme:
            u = urllib.parse.urljoin(base, u)
        p = urllib.parse.urlsplit(u)
        netloc = p.netloc.lower()
        try:
            if (p.scheme == "https" and p.port == 443) or (p.scheme == "http" and p.port == 80):
                netloc = (p.hostname or p.netloc).lower()
        except ValueError:
            pass
        q = "&".join(sorted(p.query.split("&"))) if p.query else ""
        return urllib.parse.urlunsplit((p.scheme.lower(), netloc, p.path or "/", q, ""))
    except ValueError:
        return u


def parse_lastmod(value):
    """解析 W3C/Dublin Core 常见 lastmod 格式, 失败返回 None."""
    if not value:
        return None
    v = value.strip()
    v = re.sub(r"[Zz]$", "+0000", v)
    v = re.sub(r"\.(\d{1,6})\d*", lambda m: "." + m.group(1), v)
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    return None


_ROBOTS_CACHE = {}


def robots_for(url, timeout=10.0):
    """按 origin 缓存 robots.txt 判定器; 拉不到视为无限制(全放行)."""
    p = urllib.parse.urlsplit(url)
    origin = "{0}://{1}".format(p.scheme, p.netloc)
    if origin in _ROBOTS_CACHE:
        return _ROBOTS_CACHE[origin]
    rp = urllib.robotparser.RobotFileParser()
    lines = []
    try:
        status, headers, body = fetch(origin + "/robots.txt", timeout=timeout, max_bytes=1_000_000)
        if status == 200:
            lines = decode(body, headers).splitlines()
    except Exception:
        lines = []
    try:
        rp.parse(lines)
    except Exception:
        rp.parse([])
    _ROBOTS_CACHE[origin] = rp
    return rp


def ln(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def parse_sitemap_bytes(blob):
    """解析 sitemap 字节流 -> (kind, [{loc,lastmod}], [child_sitemap_url])."""
    try:
        root = ET.fromstring(blob)
    except ET.ParseError as e:
        raise ValueError("XML 解析失败: {0}".format(e))
    kind = ln(root.tag)
    if kind not in ("urlset", "sitemapindex"):
        return "unknown", [], []
    urls, children = [], []
    for node in root.iter():
        t = ln(node.tag)
        if t == "url":
            entry = {"loc": "", "lastmod": "", "src": kind}
            for c in node:
                ct = ln(c.tag)
                if ct == "loc" and c.text:
                    entry["loc"] = c.text.strip()
                elif ct == "lastmod" and c.text:
                    entry["lastmod"] = c.text.strip()
            if entry["loc"]:
                urls.append(entry)
        elif t == "sitemap":
            for c in node:
                if ln(c.tag) == "loc" and c.text and c.text.strip():
                    children.append(c.text.strip())
    return kind, urls, children


def fetch_sitemap(url, timeout):
    status, headers, body = fetch(url, timeout=timeout, max_bytes=FIFTY_MB + 1)
    if status != 200:
        raise IOError("HTTP {0}".format(status))
    if body[:2] == b"\x1f\x8b":
        import gzip
        body = gzip.decompress(body)
    kind, urls, children = parse_sitemap_bytes(body)
    return kind, urls, children, len(body)


def print_bucket(no, name, items):
    print("\n[桶{0} {1}] 命中 {2}".format(no, name, len(items)))
    for s in items[:10]:
        print("   - {0}".format(s))
    if len(items) > 10:
        print("   ... 共 {0} 条, 仅示前 10".format(len(items)))


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="sitemap_audit.py",
        description="Sitemap 六坏桶审计 + lastmod 三判定 (stdlib only)")
    ap.add_argument("url", help="站点或 sitemap URL, 如 https://example.com")
    ap.add_argument("--check-limit", type=int, default=50, metavar="N",
                    help="逐条抓取检查的 loc 上限, 0=全部 (默认 50)")
    ap.add_argument("--timeout", type=float, default=10.0, help="单请求超时秒数 (默认 10)")
    ap.add_argument("--max-child", type=int, default=100,
                    help="sitemapindex 展开的子 sitemap 上限 (默认 100)")
    ap.add_argument("--must-include", action="append", default=[], metavar="URL",
                    help="必须出现在 sitemap 中的 URL, 可重复传入")
    args = ap.parse_args(argv)

    target = args.url.strip()
    if not target.lower().startswith(("http://", "https://")):
        target = "https://" + target
    try:
        parts = urllib.parse.urlsplit(target)
        if not parts.netloc:
            raise ValueError("缺少主机名")
    except ValueError as e:
        print("[FATAL] URL 无法解析: {0}".format(e), file=sys.stderr)
        return 2
    origin = "{0}://{1}".format(parts.scheme, parts.netloc)
    path_l = (parts.path or "").lower()
    sitemap_url = target if (path_l.endswith(".xml") or path_l.endswith(".gz")) else origin + "/sitemap.xml"

    notes = []
    entries = []
    total_bytes = 0
    oversize_files = 0
    over50k_files = 0

    try:
        kind, urls, children, nbytes = fetch_sitemap(sitemap_url, args.timeout)
    except Exception as e:
        print("[FATAL] 无法获取/解析 {0}: {1}".format(sitemap_url, e), file=sys.stderr)
        return 2
    total_bytes += nbytes
    if nbytes > FIFTY_MB:
        oversize_files += 1
    if kind == "urlset":
        entries.extend(urls)
    elif kind == "sitemapindex":
        if len(children) > args.max_child:
            notes.append("sitemapindex 含 {0} 个子 sitemap, 超过 --max-child={1}, 仅展开前 {1} 个".format(
                len(children), args.max_child))
        for child in children[:args.max_child]:
            try:
                k2, u2, c2, n2 = fetch_sitemap(child, args.timeout)
            except Exception as e:
                notes.append("子 sitemap 获取失败: {0}: {1}".format(child, e))
                continue
            total_bytes += n2
            if n2 > FIFTY_MB:
                oversize_files += 1
            if k2 == "urlset":
                entries.extend(u2)
            elif k2 == "sitemapindex":
                notes.append("嵌套 sitemapindex 超过 1 层, 未继续下钻: {0} ({1} 个子)".format(child, len(c2)))
    else:
        print("[FATAL] 根元素不是 urlset/sitemapindex: {0}".format(sitemap_url), file=sys.stderr)
        return 2

    # 去重 (保序)
    locs = []
    seen_norm = set()
    for e in entries:
        n = norm_url(e["loc"])
        if n in seen_norm:
            continue
        seen_norm.add(n)
        e["norm"] = n
        locs.append(e)
    total = len(locs)

    print("=" * 62)
    print("sitemap_audit | 入口: {0}".format(sitemap_url))
    print("sitemap 类型: {0} | 累计抓取 {1} 字节 | loc 总数: {2} (去重后)".format(
        kind, total_bytes, total))
    if total > FIFTY_K:
        over50k_files += 1
    if over50k_files:
        print("[提示] URL 总数 {0} > 50,000: 超出 Google 单 sitemap 上限, 建议拆分为多个 sitemap + index".format(total))
    if oversize_files:
        print("[提示] 存在 > 50MB 的 sitemap 文件: 超出 Google 上限, 建议拆分")

    # ---------- lastmod 三判定 ----------
    now = datetime.now(timezone.utc)

    def to_utc(d):
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)

    dated = []
    for e in locs:
        d = parse_lastmod(e.get("lastmod"))
        if d:
            dated.append(to_utc(d))
    coverage = (len(dated) / total) if total else 0.0
    latest = max(dated) if dated else None
    fresh_days = (now - latest).days if latest else None
    day_counter = Counter(d.date() for d in dated)
    top_day, top_count = (day_counter.most_common(1)[0] if day_counter else (None, 0))
    share = (top_count / total) if total else 0.0
    fabricated = total > 0 and share > 0.5 and top_day == now.date()

    print("\n---- lastmod 三判定 ----")
    print("Coverage     : {0:.3f}  (有 lastmod 条目占比, 期望 1.0)".format(coverage))
    if latest:
        print("Freshness    : 最新 lastmod {0} 距今 {1} 天 {2}".format(
            latest.isoformat()[:19], fresh_days, "(<=30 天, OK)" if fresh_days <= 30 else "(>30 天, 过期)"))
    else:
        print("Freshness    : 无任何可解析的 lastmod, 无法判定")
    print("Truthfulness : 最大单日簇 {0} 占 {1:.1%} {2}".format(
        top_day or "-", share,
        "-> 疑似构建期伪造(大量条目 lastmod=今天)" if fabricated else "(未触发伪造特征)"))

    # ---------- 六坏桶 ----------
    b_non200, b_redir, b_noindex, b_canonical, b_robots, b_dup = [], [], [], [], [], []

    limit = args.check_limit if args.check_limit > 0 else total
    checked = 0
    for e in locs[:limit]:
        u = e["loc"]
        try:
            rp = robots_for(u, args.timeout)
            if not rp.can_fetch("Googlebot", u):
                b_robots.append(u)
                continue
        except Exception as err:
            notes.append("robots.txt 判定失败 {0}: {1}".format(u, err))
        try:
            status, headers, body = fetch(u, timeout=args.timeout)
        except Exception as err:
            b_non200.append("{0}  (抓取失败: {1})".format(u, type(err).__name__))
            continue
        checked += 1
        if 300 <= status < 400:
            loc_hdr = ""
            try:
                loc_hdr = headers.get("Location") or "" if headers else ""
            except Exception:
                loc_hdr = ""
            b_redir.append("{0} -> {1} (HTTP {2})".format(u, loc_hdr, status))
            continue
        if status != 200:
            b_non200.append("{0}  (HTTP {1})".format(u, status))
            continue
        try:
            text = decode(body, headers)
            hp = HeadParser()
            hp.feed(text[:200000])
        except Exception as err:
            notes.append("HTML 解析失败 {0}: {1}".format(u, err))
            continue
        xr = []
        try:
            xr = headers.get_all("X-Robots-Tag") or [] if headers else []
        except Exception:
            xr = []
        noindex = any("noindex" in v.lower() for v in hp.meta_robots) or \
            any("noindex" in v.lower() for v in xr)
        if noindex:
            b_noindex.append(u)
            continue
        if hp.canonical:
            cnorm = norm_url(hp.canonical, base=u)
            if cnorm and cnorm != norm_url(u):
                b_canonical.append("{0} -> {1}".format(u, hp.canonical))
                continue

    # 桶6: 参数重复 (基于全量 loc)
    groups = {}
    for e in locs:
        try:
            sp = urllib.parse.urlsplit(e["loc"])
        except ValueError:
            continue
        key = (sp.scheme.lower(), sp.netloc.lower(), sp.path or "/")
        groups.setdefault(key, []).append(e["loc"])
    for _key, us in groups.items():
        qs = set(urllib.parse.urlsplit(x).query for x in us)
        if len(us) > 1 and len(qs) > 1:
            b_dup.extend(sorted(us))

    if checked < total:
        print("\n[范围] 逐条抓取检查了前 {0}/{1} 个 loc (--check-limit 可调)".format(checked, total))

    print("\n---- 六坏桶 ----")
    print_bucket(1, "非 200 / 抓取失败", b_non200)
    print_bucket(2, "3xx 重定向", b_redir)
    print_bucket(3, "noindex 页", b_noindex)
    print_bucket(4, "canonical 指向他址", b_canonical)
    print_bucket(5, "robots.txt 屏蔽 (Googlebot)", b_robots)
    print_bucket(6, "参数重复 URL (同 path 不同 query)", b_dup)

    # ---------- 反向检查 ----------
    missing = []
    if args.must_include:
        print("\n---- --must-include 反向检查 ----")
        loc_norms = set(e["norm"] for e in locs)
        for m in args.must_include:
            ok = norm_url(m) in loc_norms
            print("   {0} {1}".format("OK  " if ok else "MISS", m))
            if not ok:
                missing.append(m)

    if notes:
        print("\n---- 过程备注 ----")
        for n in notes[:20]:
            print("   * {0}".format(n))
        if len(notes) > 20:
            print("   ... 共 {0} 条".format(len(notes)))

    bad_total = sum(len(x) for x in (b_non200, b_redir, b_noindex, b_canonical, b_robots, b_dup))
    print("\n==== 结论: 坏桶命中 {0} 条, must-include 缺失 {1} 个 => {2} ====".format(
        bad_total, len(missing), "FAIL (退出码 1)" if (bad_total or missing) else "PASS"))
    return 1 if (bad_total or missing) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        sys.exit(130)
