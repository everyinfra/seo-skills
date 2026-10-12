#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""news_sitemap_check.py — news sitemap 专属体检(discover-news-seo.md 四连 curl 脚本化+扩展;stdlib only)。

用法:
  python3 news_sitemap_check.py --url https://example.com/news-sitemap.xml \
      [--pub-name "Example News"] [--sample 3] [--timeout 15] [--json]

四连 curl 脚本化(references/content/discover-news-seo.md「News sitemap 验收命令」逐条对接):
  [curl1] 48h 窗口   每条 news:publication_date(fallback lastmod)距今 ≤48h——协议红线,
                       超龄逐条列出(错误清单 #1:塞入 >48h 旧文最常见);
  [curl2] 条数上限   >1,000 → WARN(48h 窗口天然应远小于;异常大=窗口滚动逻辑坏了),
                       >50,000 → FAIL(通用硬上限);
  [curl3] 必填三件套 每条 <url> 应同时有 news:publication(name+language)/
                       news:publication_date/news:title,缺项逐条列出;
  [curl4] 200 直返    sitemap URL 自身不得 3xx 重定向(http→https/加尾斜杠都会
                       "Sitemap could not be read");非 200/不可达 → 退出码 2;
  [curl5] noindex 抽查 --sample N(默认 3)条文章页现场核验 meta robots/x-robots-tag
                       是否 noindex(错误清单 #2)。

扩展项(错误清单 #4-#6 + robots 一致性):
  存在率/混入    <news:news> 标签存在率;无标签条目=混入非新闻 URL(逐条列前 10);
  publication name 一致性 站内各条 name 应一致;--pub-name 给定时与站名比对
                       (错误清单 #6:名称漂移削弱 News 关联);
  时间戳精度     publication_date 只有日期(无时间/时区)→ WARN(错误清单 #5:
                       建议 ISO 8601 精确到秒含时区);
  title 格式     news:title ≥100 字符 → WARN;标题呈「站名在前/后缀」逆序格式
                       (Site - 标题 / 标题 - Site)→ WARN——news:title 应为纯文章标题;
  loc 绝对 URL   <loc> 必须是含协议的绝对 URL(错误清单 #4);
  robots 声明一致 {origin}/robots.txt 的 Sitemap: 行是否声明本 sitemap
                       (未声明 → WARN,可发现性)。

退出码: 0 无 FAIL / 1 有 FAIL / 2 sitemap 不可达/不可解析/sitemapindex(传具体文件)。
网络走模块级 http_fetch()(单点,测试打桩;SSRF:仅 http(s),私网/环回/链路本地拒)。"""
import argparse
import gzip
import ipaddress
import json
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

SCHEMA_VERSION = 1
UA = "Mozilla/5.0 (compatible; seo-suite-news-sitemap-check/1.0)"
FETCH_TIMEOUT = 15.0
FRESH_HOURS = 48            # 协议红线:news sitemap 仅含近 48h 文章
SOFT_URL_LIMIT = 1000       # 最佳实践(48h 窗口天然远小于)
HARD_URL_LIMIT = 50000      # 通用单 sitemap 硬上限
PASS, WARN, FAIL, UNVERIFIED = "pass", "warn", "fail", "unverified"
SYMBOL = {PASS: "✓", WARN: "⚠", FAIL: "✗", UNVERIFIED: "－"}


class FetchError(Exception):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _guard_url(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ("http", "https"):
        raise FetchError("仅接受 http(s) URL,得到 scheme=%r" % (p.scheme or "(空)"))
    host = p.hostname or ""
    if not host:
        raise FetchError("URL 缺主机名")
    try:
        infos = socket.getaddrinfo(host, 443 if p.scheme == "https" else 80)
    except OSError as e:
        raise FetchError("DNS 解析失败 %s: %s" % (host, e))
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified):
            raise FetchError("目标 %s(%s) 属私网/保留/环回段,已拒绝(SSRF 防护)" % (host, ip))


def _decode(raw, headers):
    ct = ""
    try:
        ct = headers.get("Content-Type") or "" if headers else ""
    except Exception:
        ct = ""
    charset = None
    if ct:
        m = re.search(r"charset=([\w\-]+)", ct, re.I)
        if m:
            charset = m.group(1)
    if not charset and raw:
        m = re.search(rb'charset=["\']?([\w\-]+)', raw[:4096], re.I)
        if m:
            charset = m.group(1).decode("ascii", "replace")
    for enc in (charset, "utf-8", "gb18030", "latin-1"):
        if not enc:
            continue
        try:
            return raw.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", "replace")


def http_fetch(url, timeout=FETCH_TIMEOUT, max_bytes=50 * 1024 * 1024 + 1):
    """单点网络入口(测试打桩点);不跟随重定向。返回 (status, headers, body_bytes)。"""
    _guard_url(url)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/xml,text/xml,*/*;q=0.8"})
    try:
        with _OPENER.open(req, timeout=timeout) as resp:
            return resp.status, resp.headers, resp.read(max_bytes)
    except urllib.error.HTTPError as e:
        try:
            body = e.read(65536)
        except Exception:
            body = b""
        return e.code, getattr(e, "headers", None), body


def ln(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def parse_ts(value):
    """W3C 常见时间戳 → aware UTC datetime;失败 None。"""
    if not value:
        return None
    v = value.strip()
    v = re.sub(r"[Zz]$", "+0000", v)
    v = re.sub(r"\.(\d{1,6})\d*", lambda m: "." + m.group(1), v)
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
        try:
            d = datetime.strptime(v, fmt)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def parse_entries(root):
    """urlset → [{loc,lastmod,news|None}];news={name,language,date,title}。"""
    entries = []
    for node in root.iter():
        if ln(node.tag) != "url":
            continue
        e = {"loc": "", "lastmod": "", "news": None}
        for c in node:
            t = ln(c.tag)
            if t == "loc" and c.text:
                e["loc"] = c.text.strip()
            elif t == "lastmod" and c.text:
                e["lastmod"] = c.text.strip()
            elif t == "news":
                n = {"name": "", "language": "", "date": "", "title": ""}
                for nc in c.iter():
                    nt = ln(nc.tag)
                    if nt == "name" and nc.text:
                        n["name"] = nc.text.strip()
                    elif nt == "language" and nc.text:
                        n["language"] = nc.text.strip()
                    elif nt == "publication_date" and nc.text:
                        n["date"] = nc.text.strip()
                    elif nt == "title" and nc.text:
                        n["title"] = nc.text.strip()
                e["news"] = n
        entries.append(e)
    return entries


def norm_sitemap_url(u):
    p = urllib.parse.urlsplit((u or "").strip())
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path or "/", "", ""))


def parse_robots_sitemaps(text):
    out = []
    for line in (text or "").splitlines():
        m = re.match(r"\s*sitemap\s*:\s*(\S+)", line, re.I)
        if m:
            out.append(m.group(1).strip())
    return out


def page_is_noindex(body_str, headers):
    try:
        xr = headers.get_all("X-Robots-Tag") or [] if headers else []
    except Exception:
        xr = []
    if any("noindex" in (v or "").lower() for v in xr):
        return True
    for m in re.finditer(r"<meta\b[^>]*>", body_str or "", re.I):
        tag = m.group(0)
        if re.search(r'name\s*=\s*["\']?robots', tag, re.I) and \
                re.search(r'content\s*=\s*["\'][^"\']*noindex', tag, re.I):
            return True
    return False


def build_items(entries, sitemap_status, sitemap_headers, sitemap_bytes,
                args, now):
    items = []
    total = len(entries)
    with_news = [e for e in entries if e["news"]]
    # ---- curl4: 200 直返 ----
    if 300 <= sitemap_status < 400:
        loc = ""
        try:
            loc = sitemap_headers.get("Location") or "" if sitemap_headers else ""
        except Exception:
            loc = ""
        items.append(dict(id="http.direct_200", status=FAIL,
                          detail="sitemap URL 自身 %d 重定向 → %s(Yoast 错误 #3:读取失败)" % (
                              sitemap_status, loc or "?")))
    else:
        items.append(dict(id="http.direct_200", status=PASS,
                          detail="HTTP %d 直返(%d bytes)" % (sitemap_status, len(sitemap_bytes))))
    # ---- 空表 ----
    if total == 0:
        items.append(dict(id="coverage.news_tag", status=FAIL, detail="空 sitemap(0 条 <url>)"))
        return items
    # ---- curl2: 条数 ----
    if total > HARD_URL_LIMIT:
        items.append(dict(id="count.limit", status=FAIL,
                          detail="%d 条 > 通用硬上限 %d——必须拆分" % (total, HARD_URL_LIMIT)))
    elif total > SOFT_URL_LIMIT:
        items.append(dict(id="count.limit", status=WARN,
                          detail="%d 条 > %d 最佳实践(48h 窗口天然应远小于;异常大=窗口滚动逻辑坏了)" % (
                              total, SOFT_URL_LIMIT)))
    else:
        items.append(dict(id="count.limit", status=PASS, detail="%d 条(≤%d 最佳实践)" % (total, SOFT_URL_LIMIT)))
    # ---- 存在率 / 混入非新闻 ----
    ratio = len(with_news) / total
    mixed = [e["loc"] for e in entries if not e["news"]]
    if not with_news:
        items.append(dict(id="coverage.news_tag", status=FAIL,
                          detail="0/%d 条含 <news:news>——这不是 news sitemap(普通 urlset?)" % total))
    elif mixed:
        items.append(dict(id="coverage.news_tag", status=WARN,
                          detail="存在率 %.1f%%(%d/%d);混入非新闻 URL %d 条: %s" % (
                              ratio * 100, len(with_news), total, len(mixed),
                              ", ".join(mixed[:10]) + ("…" if len(mixed) > 10 else ""))))
    else:
        items.append(dict(id="coverage.news_tag", status=PASS,
                          detail="<news:news> 存在率 100%%(%d/%d)" % (len(with_news), total)))
    # ---- curl3: 必填三件套 ----
    missing = []
    for e in with_news:
        n = e["news"]
        lack = [k for k, v in (("publication.name", n["name"]),
                               ("publication.language", n["language"]),
                               ("publication_date", n["date"]),
                               ("title", n["title"])) if not v]
        if lack:
            missing.append("%s 缺 %s" % (e["loc"] or "(空 loc)", "+".join(lack)))
    if missing:
        items.append(dict(id="trio.required", status=FAIL,
                          detail="%d/%d 条必填三件套不全: %s" % (
                              len(missing), len(with_news),
                              "; ".join(missing[:5]) + ("…" if len(missing) > 5 else ""))))
    else:
        items.append(dict(id="trio.required", status=PASS,
                          detail="publication(name+language)/publication_date/title %d/%d 齐" % (
                              len(with_news), len(with_news))))
    # ---- curl1: 48h 窗口 ----
    stale, freshest_h = [], None
    for e in with_news:
        raw = e["news"]["date"] or e["lastmod"]
        ts = parse_ts(raw)
        if not ts:
            stale.append("%s(publication_date/lastmod 不可解析: %r)" % (e["loc"], raw))
            continue
        age_h = (now - ts).total_seconds() / 3600
        if age_h < 0:
            age_h = 0.0
        freshest_h = age_h if freshest_h is None else min(freshest_h, age_h)
        if age_h > FRESH_HOURS:
            stale.append("%s(%.1fh 前)" % (e["loc"], age_h))
    if stale:
        items.append(dict(id="window.48h", status=FAIL,
                          detail="协议红线:超 48h/不可解析 %d 条——逐条: %s" % (
                              len(stale), "; ".join(stale[:10]) + ("…" if len(stale) > 10 else ""))))
    else:
        items.append(dict(id="window.48h", status=PASS,
                          detail="全部 ≤48h(最新 %.1fh 前)" % (freshest_h if freshest_h is not None else -1)))
    # ---- 时间戳精度 ----
    date_only = [e["loc"] for e in with_news
                 if e["news"]["date"] and re.fullmatch(r"\d{4}-\d{2}-\d{2}", e["news"]["date"])]
    if date_only:
        items.append(dict(id="precision.ts", status=WARN,
                          detail="%d 条 publication_date 只有日期无时间/时区(建议 ISO 8601 精确到秒)" % len(date_only)))
    else:
        items.append(dict(id="precision.ts", status=PASS, detail="时间戳均带时间(部分 date-only 属错误清单 #5)"))
    # ---- publication name 一致性 ----
    names = {}
    for e in with_news:
        if e["news"]["name"]:
            names[e["news"]["name"]] = names.get(e["news"]["name"], 0) + 1
    if not names:
        items.append(dict(id="pubname.consistency", status=FAIL, detail="全部条目缺 publication name"))
    else:
        details = []
        st = PASS
        if len(names) > 1:
            st = WARN
            details.append("站内不一致 %d 个名: %s" % (
                len(names), ", ".join("%s×%d" % kv for kv in sorted(names.items()))))
        else:
            details.append("站内一致: %s" % next(iter(names)))
        if args.pub_name:
            want = args.pub_name.strip().casefold()
            mismatch = [n for n in names if n.casefold() != want]
            if mismatch:
                st = WARN
                details.append("--pub-name %r 不匹配: %s" % (args.pub_name, ", ".join(mismatch[:5])))
            else:
                details.append("与 --pub-name 一致")
        items.append(dict(id="pubname.consistency", status=st, detail=";".join(details)))
    # ---- title 格式 ----
    long_titles, reversed_titles = [], []
    for e in with_news:
        t, nm = e["news"]["title"], e["news"]["name"]
        if len(t) >= 100:
            long_titles.append(e["loc"])
        if nm:
            tl, nl = t.casefold(), nm.casefold()
            if (tl.endswith(" - " + nl) or tl.endswith(" | " + nl)
                    or tl.startswith(nl + " - ") or tl.startswith(nl + " | ")):
                reversed_titles.append(e["loc"])
    if long_titles or reversed_titles:
        d = []
        if long_titles:
            d.append("%d 条 title ≥100 字符" % len(long_titles))
        if reversed_titles:
            d.append("%d 条呈站名前/后缀逆序格式(news:title 应为纯文章标题)" % len(reversed_titles))
        items.append(dict(id="title.format", status=WARN, detail=";".join(d)))
    else:
        items.append(dict(id="title.format", status=PASS, detail="title 长度/格式无异常"))
    # ---- loc 绝对 URL ----
    rel = [e["loc"] for e in entries
           if not re.match(r"^https?://\S+$", e["loc"] or "", re.I) or " " in (e["loc"] or "")]
    if rel:
        items.append(dict(id="loc.absolute", status=FAIL,
                          detail="%d 条 loc 非绝对 http(s) URL(错误清单 #4): %s" % (
                              len(rel), ", ".join((x or "(空)")[:60] for x in rel[:5]))))
    else:
        items.append(dict(id="loc.absolute", status=PASS, detail="loc 均为绝对 URL"))
    return items


def check_robots_declaration(sitemap_url, args, items):
    p = urllib.parse.urlsplit(sitemap_url)
    origin = "%s://%s" % (p.scheme, p.netloc)
    try:
        status, headers, body = http_fetch(origin + "/robots.txt", timeout=args.timeout,
                                           max_bytes=1_000_000)
    except Exception as e:
        items.append(dict(id="robots.sitemap_decl", status=UNVERIFIED,
                          detail="robots.txt 拉取失败(%s)——声明一致性未核" % type(e).__name__))
        return
    declared = parse_robots_sitemaps(_decode(body, headers)) if status == 200 else []
    if status != 200:
        items.append(dict(id="robots.sitemap_decl", status=UNVERIFIED,
                          detail="robots.txt HTTP %d——无法核对 Sitemap 声明" % status))
        return
    mine = norm_sitemap_url(sitemap_url)
    if any(norm_sitemap_url(d) == mine for d in declared):
        items.append(dict(id="robots.sitemap_decl", status=PASS, detail="robots.txt 已声明本 sitemap"))
    else:
        items.append(dict(id="robots.sitemap_decl", status=WARN,
                          detail="robots.txt 的 %d 条 Sitemap 声明均不含本 sitemap(非协议必需;影响发现速度)" % len(declared)))


def check_sample_noindex(entries, args, items):
    if args.sample <= 0:
        items.append(dict(id="noindex.sample", status=UNVERIFIED, detail="--sample 0 已关闭抽查"))
        return
    targets = [e["loc"] for e in entries if e["news"] and
               re.match(r"^https?://\S+$", e["loc"] or "", re.I)][:args.sample]
    if not targets:
        items.append(dict(id="noindex.sample", status=UNVERIFIED, detail="无可抽查的新闻 URL"))
        return
    bad, unver = [], 0
    for u in targets:
        try:
            status, headers, body = http_fetch(u, timeout=args.timeout, max_bytes=2_000_000)
        except Exception:
            unver += 1
            continue
        if status != 200:
            unver += 1
            continue
        if page_is_noindex(_decode(body, headers), headers):
            bad.append(u)
    if bad:
        items.append(dict(id="noindex.sample", status=FAIL,
                          detail="抽查 %d 条中 %d 条 noindex(错误清单 #2): %s" % (
                              len(targets), len(bad), ", ".join(bad))))
    else:
        items.append(dict(id="noindex.sample", status=PASS,
                          detail="抽查 %d/%d 条可索引(%d 条不可达未计)" % (
                              len(targets) - unver, len(targets), unver)))


def render(items, meta):
    print("=" * 64)
    print("news_sitemap_check | %s" % meta["url"])
    titles = [
        ("http.direct_200", "curl4  200 直返无重定向"),
        ("count.limit", "curl2  条数上限"),
        ("coverage.news_tag", "ext    <news:news> 存在率 / 混入非新闻 URL"),
        ("trio.required", "curl3  必填三件套(publication/date/title)"),
        ("window.48h", "curl1  48h 窗口(协议红线)"),
        ("precision.ts", "ext    时间戳精度"),
        ("pubname.consistency", "ext    publication name 一致性"),
        ("title.format", "ext    title 格式(长度/站名逆序)"),
        ("loc.absolute", "ext    loc 绝对 URL"),
        ("noindex.sample", "curl5  引用页 noindex 抽查"),
        ("robots.sitemap_decl", "ext    robots.txt Sitemap 声明一致"),
    ]
    tmap = dict(titles)
    counts = {PASS: 0, WARN: 0, FAIL: 0, UNVERIFIED: 0}
    for iid, title in titles:
        it = next((x for x in items if x["id"] == iid), None)
        if not it:
            continue
        counts[it["status"]] += 1
        print("%s %-44s %s" % (SYMBOL[it["status"]], title, it["detail"]))
    for it in items:
        if it["id"] not in tmap:
            counts[it["status"]] += 1
            print("%s %-44s %s" % (SYMBOL[it["status"]], it["id"], it["detail"]))
    print("\n==== 结果: %d ✓ / %d ⚠ / %d ✗ / %d unverified => %s ====" % (
        counts[PASS], counts[WARN], counts[FAIL], counts[UNVERIFIED],
        "FAIL(退出码 1)" if counts[FAIL] else "PASS(退出码 0)"))
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="news_sitemap_check.py",
        description="news sitemap 专属体检:48h 窗口红线 / 必填三件套 / 200 直返 / noindex 抽查 "
                    "/ 存在率 / publication name / 时间戳精度 / title 格式 / robots 声明(stdlib)")
    ap.add_argument("--url", required=True, help="news sitemap XML 的 URL(具体文件,勿传 index)")
    ap.add_argument("--pub-name", help="站名(与各条 news:publication>name 比对;缺省只查站内一致性)")
    ap.add_argument("--sample", type=int, default=3,
                    help="引用页 noindex 抽查条数(默认 3;0=关闭)")
    ap.add_argument("--timeout", type=float, default=FETCH_TIMEOUT, help="单请求超时秒(默认 15)")
    ap.add_argument("--json", dest="as_json", action="store_true", help="结构化输出")
    args = ap.parse_args(argv)

    p = urllib.parse.urlsplit(args.url)
    if p.scheme not in ("http", "https") or not p.netloc:
        sys.stderr.write("[FATAL] --url 仅接受 http(s) URL: %r\n" % args.url)
        return 2
    try:
        status, headers, body = http_fetch(args.url, timeout=args.timeout)
    except FetchError as e:
        sys.stderr.write("[FATAL] %s\n" % e)
        return 2
    except Exception as e:
        sys.stderr.write("[FATAL] 无法获取 %s: %s\n" % (args.url, e))
        return 2
    # 3xx 重定向是可判定 FAIL(检查项),其余非 200 按不可读致命处理
    if status != 200 and not (300 <= status < 400):
        sys.stderr.write("[FATAL] sitemap HTTP %d(不可读)\n" % status)
        return 2
    if 300 <= status < 400:
        # 重定向体不是 sitemap XML——直接以单项 FAIL 收口(Yoast 错误 #3)
        loc = ""
        try:
            loc = headers.get("Location") or "" if headers else ""
        except Exception:
            loc = ""
        items = [dict(id="http.direct_200", status=FAIL,
                      detail="sitemap URL 自身 %d 重定向 → %s(Yoast 错误 #3:读取失败)" % (
                          status, loc or "?"))]
        if args.as_json:
            print(json.dumps({"schema_version": SCHEMA_VERSION, "tool": "news_sitemap_check",
                              "url": args.url, "entries": 0, "news_entries": 0,
                              "counts": {PASS: 0, WARN: 0, FAIL: 1, UNVERIFIED: 0},
                              "items": items}, ensure_ascii=False, indent=1))
        else:
            render(items, {"url": args.url})
        return 1
    if body[:2] == b"\x1f\x8b":
        try:
            body = gzip.decompress(body)
        except OSError:
            pass
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        sys.stderr.write("[FATAL] XML 解析失败: %s\n" % e)
        return 2
    kind = ln(root.tag)
    if kind == "sitemapindex":
        sys.stderr.write("[FATAL] 传入的是 sitemapindex——请用 --url 指向具体的 news sitemap 文件\n")
        return 2
    if kind != "urlset":
        sys.stderr.write("[FATAL] 根元素是 %r,不是 urlset\n" % kind)
        return 2

    entries = parse_entries(root)
    now = datetime.now(timezone.utc)
    items = build_items(entries, status, headers, body, args, now)
    check_robots_declaration(args.url, args, items)
    check_sample_noindex(entries, args, items)

    counts = {s: sum(1 for it in items if it["status"] == s)
              for s in (PASS, WARN, FAIL, UNVERIFIED)}
    payload = {
        "schema_version": SCHEMA_VERSION, "tool": "news_sitemap_check",
        "url": args.url, "entries": len(entries),
        "news_entries": sum(1 for e in entries if e["news"]),
        "counts": counts, "items": items,
    }
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        render(items, {"url": args.url})
    return 1 if counts[FAIL] else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.stderr.write("\n[interrupted]\n")
        sys.exit(130)
