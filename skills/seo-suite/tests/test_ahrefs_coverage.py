#!/usr/bin/env python3
"""RQ-229 例 3:Ahrefs Site Audit 121 项「脚本实跑能报出来」补项的夹具测试(stdlib unittest,零网络)。

每一项都有两半:命中夹具必须报出来;对照夹具(按 Ahrefs 定义不该报)必须不报。
期望值来自 Ahrefs 官方帮助文(help.ahrefs.com/en/articles/<编号>)和 Ahrefs 博客原文,编号写在各用例里;
Ahrefs 没公布阈值的项(Slow page、Too slow/heavy for AI crawlers、Inconsistent AI bot policies、
HTML file size too large)按 references/technical/ahrefs-site-audit-coverage.md 写明的本套件口径。
逐项对照表:references/technical/ahrefs-site-audit-coverage.md。
独立可运行:python3 tests/test_ahrefs_coverage.py"""
import argparse
import contextlib
import io
import os
import sys
import unittest
import urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import redirect_chain  # noqa: E402
import robots_posture  # noqa: E402
import schema_lint  # noqa: E402
import site_audit as sa  # noqa: E402
import site_crawl as sc  # noqa: E402

HOME = "https://example.com/"
FILLER = " ".join("word%d" % i for i in range(120))


# ---------------------------------------------------------------------------
# site_crawl 夹具:路由表 → http_fetch 桩(带响应头、重定向链、计时 meta)
# ---------------------------------------------------------------------------

class Site:
    def __init__(self):
        self.routes = {}

    def page(self, path, body="", status=200, headers=None, redirect_to=None, redirect_status=301,
             final_status=None, meta=None, chain=None):
        url = path if path.startswith("http") else "https://example.com" + path
        self.routes[url] = dict(body=body, status=status, headers=headers or {}, redirect_to=redirect_to,
                                redirect_status=redirect_status, meta=meta or {}, chain=chain)
        return url

    def __call__(self, url, timeout=10.0, method="GET"):
        r = self.routes.get(url)
        if r is None:
            return {"status": 404, "final_url": url, "chain": [], "headers": {}, "body": "",
                    "body_bytes": b"", "meta": {}}
        chain = []
        cur, hops = url, 0
        while r and r["redirect_to"] and hops < 10:
            nxt = r["redirect_to"] if r["redirect_to"].startswith("http") else "https://example.com" + r["redirect_to"]
            chain.append({"status": r["redirect_status"], "location": nxt})
            cur, r, hops = nxt, self.routes.get(nxt), hops + 1
        if r is None:
            return {"status": 404, "final_url": cur, "chain": chain, "headers": {}, "body": "",
                    "body_bytes": b"", "meta": {}}
        body = r["body"]
        return {"status": r["status"], "final_url": cur, "chain": chain, "headers": dict(r["headers"]),
                "body": body, "body_bytes": body.encode("utf-8"), "meta": dict(r["meta"])}


def html(title="Page", links=(), head="", body_text=None, lang="en", extra_body=""):
    a = "".join('<a href="%s">%s link</a>' % (h, h) for h in links)
    text = body_text if body_text is not None else "Unique text for %s. %s" % (title, title)
    return ('<!doctype html><html lang="%s"><head><title>%s</title>%s</head><body><h1>%s</h1><p>%s</p>%s%s</body></html>'
            % (lang, title, head, title, text, a, extra_body))


def ns(**kw):
    d = dict(site="https://example.com", urls=None, max_pages=500, delay=0.0, ignore_robots=False,
             strip_params=False, same_host=False, include_subdomains=False, subs="none", check_external=False,
             timeout=5.0, out="crawl.json", urls_out=None, json=False, check_resources=False, slow_ms=None)
    d.update(kw)
    return argparse.Namespace(**d)


def run_crawl(site, **kw):
    orig = (sc.http_fetch, sc.dns_resolve, sc._sleep)
    sc.http_fetch = site
    sc.dns_resolve = lambda host: ["93.184.216.34"]
    sc._sleep = lambda s: None
    sc._ssrf_cache.clear()
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            report, _rc = sc.Crawler(ns(**kw)).run()
    finally:
        sc.http_fetch, sc.dns_resolve, sc._sleep = orig
        sc._ssrf_cache.clear()
    return report["site_issues"]


def urls_of(rows):
    out = []
    for r in rows:
        out.append(r if isinstance(r, str) else r.get("url"))
    return out


U = lambda p: "https://example.com" + p  # noqa: E731


class CrawlInternalPagesTests(unittest.TestCase):
    def test_double_slash_in_url(self):
        # help 2596665:「URLs that contain a double slash (after the domain part)」
        s = Site()
        s.page("/", html("Home", ["/x//y", "/x/y"]))
        s.page("/x//y", html("Dbl"))
        s.page("/x/y", html("Ok"))
        si = run_crawl(s)
        self.assertEqual(si["double_slash_in_url"], [U("/x//y")])

    def test_html_size_two_levels(self):
        # Oversized HTML:Googlebot 只抓前 2MB;HTML file size too large:Ahrefs 博客「250-300KB or more」→ 300KB
        s = Site()
        s.page("/", html("Home", ["/big", "/mid", "/small"]))
        s.page("/big", html("Big", body_text="x " * (1100 * 1024)))        # ≈2.2MB
        s.page("/mid", html("Mid", body_text="x " * (200 * 1024)))         # ≈400KB
        s.page("/small", html("Small"))
        si = run_crawl(s)
        self.assertEqual(urls_of(si["oversized_html"]), [U("/big")])
        self.assertEqual(sorted(urls_of(si["html_file_size_too_large"])), [U("/big"), U("/mid")])


class CrawlIndexabilityTests(unittest.TestCase):
    def test_nofollow_page_and_directives_in_both_places(self):
        # help 2478724 Nofollow page;help 2465780 Nofollow in HTML and HTTP header;noindex 同理
        s = Site()
        s.page("/", html("Home", ["/nf", "/both", "/one"]))
        s.page("/nf", html("NF", head='<meta name="robots" content="nofollow">'))
        s.page("/both", html("Both", head='<meta name="robots" content="noindex,nofollow">'),
               headers={"X-Robots-Tag": "noindex, nofollow"})
        s.page("/one", html("One", head='<meta name="robots" content="noindex">'))
        si = run_crawl(s)
        self.assertEqual(sorted(si["nofollow_page"]), [U("/both"), U("/nf")])
        self.assertEqual(si["noindex_in_html_and_header"], [U("/both")])
        self.assertEqual(si["nofollow_in_html_and_header"], [U("/both")])
        self.assertEqual(sorted(si["noindex_page"]), [U("/both"), U("/one")])

    def test_canonical_targets(self):
        # 2427853 → 4XX;2491113 → 5XX;2753767 → redirect;2526305 目标页自己又 canonical 到别处
        s = Site()
        s.page("/", html("Home", ["/p4", "/p5", "/pr", "/pc", "/ok"]))
        canon = lambda h: '<link rel="canonical" href="%s">' % h  # noqa: E731
        s.page("/p4", html("P4", head=canon("/c404")))
        s.page("/p5", html("P5", head=canon("/c500")))
        s.page("/c500", "err", status=503)
        s.page("/pr", html("PR", head=canon("/cred")))
        s.page("/cred", redirect_to="/final")
        s.page("/final", html("Final"))
        s.page("/pc", html("PC", head=canon("/cmid")))
        s.page("/cmid", html("Cmid", head=canon("/elsewhere")))
        s.page("/ok", html("OK", head=canon("/okt")))
        s.page("/okt", html("OKT", head=canon("/okt")))
        si = run_crawl(s)
        self.assertEqual(urls_of(si["canonical_points_to_4xx"]), [U("/p4")])
        self.assertEqual(urls_of(si["canonical_points_to_5xx"]), [U("/p5")])
        self.assertEqual(urls_of(si["canonical_points_to_redirect"]), [U("/pr")])
        self.assertEqual(urls_of(si["non_canonical_page_specified_as_canonical"]), [U("/pc")])

    def test_canonical_protocol(self):
        # 2434581 HTTPS 页 canonical 指 HTTP;2478867 HTTP 页 canonical 指 HTTPS
        s = Site()
        s.page("/", html("Home", ["/a", "http://example.com/h"]))
        s.page("/a", html("A", head='<link rel="canonical" href="http://example.com/a">'))
        s.page("http://example.com/h", html("H", head='<link rel="canonical" href="https://example.com/h">'))
        s.page("/h", html("H2"))
        si = run_crawl(s)
        self.assertEqual(urls_of(si["canonical_from_https_to_http"]), [U("/a")])
        self.assertEqual(urls_of(si["canonical_from_http_to_https"]), ["http://example.com/h"])

    def test_duplicate_pages(self):
        # 2115215 bad duplicates = 没用 canonical/hreflang 处理的重复;2596742 重复且没声明 canonical(noindex 除外)
        same = "Identical body " + FILLER
        s = Site()
        s.page("/", html("Home", ["/d1", "/d2", "/g1", "/g2", "/n1"]))
        s.page("/d1", html("D1", body_text=same))
        s.page("/d2", html("D2", body_text=same))
        good = "Other identical body " + " ".join("term%d" % i for i in range(120))
        s.page("/g1", html("G1", body_text=good, head='<link rel="canonical" href="/g1">'))
        s.page("/g2", html("G2", body_text=good, head='<link rel="canonical" href="/g1">'))
        s.page("/n1", html("N1", body_text=same, head='<meta name="robots" content="noindex">'))
        si = run_crawl(s)
        groups = [sorted(g["urls"]) for g in si["duplicate_content_bad"]]
        self.assertEqual(groups, [[U("/d1"), U("/d2"), U("/n1")]])
        self.assertEqual(si["duplicate_pages_without_canonical"], [U("/d1"), U("/d2")])   # /n1 noindex 不算

    def test_duplicate_title_description_h1(self):
        s = Site()
        d = '<meta name="description" content="Same description text">'
        s.page("/", html("Home", ["/t1", "/t2", "/t3"]))
        s.page("/t1", html("Same Title", head=d, body_text="one " + FILLER))
        s.page("/t2", html("Same Title", head=d, body_text="two"))
        s.page("/t3", html("Same Title", head=d + '<meta name="robots" content="noindex">', body_text="three"))
        si = run_crawl(s)
        for key in ("duplicate_title", "duplicate_meta_description", "duplicate_h1"):
            self.assertEqual([g["urls"] for g in si[key]], [[U("/t1"), U("/t2")]], key)   # 只算可索引页


class CrawlLinksTests(unittest.TestCase):
    def test_nofollow_incoming(self):
        # 2746992 只有 nofollow 入链;2734983 nofollow 与 dofollow 都有
        s = Site()
        s.page("/", html("Home", ["/b"], extra_body='<a rel="nofollow" href="/only">x</a><a rel="nofollow" href="/mixed">x</a>'))
        s.page("/b", html("B", ["/mixed", "/normal"]))
        for p in ("/only", "/mixed", "/normal"):
            s.page(p, html(p, ["/"]))
        si = run_crawl(s)
        self.assertEqual(urls_of(si["nofollow_incoming_internal_links_only"]), [U("/only")])
        self.assertEqual(urls_of(si["nofollow_and_dofollow_incoming_internal_links"]), [U("/mixed")])
        self.assertEqual(urls_of(si["nofollow_outgoing_internal_links"]), [HOME])

    def test_no_outgoing_links(self):
        # 2734700:「pages that have no outgoing links」
        s = Site()
        s.page("/", html("Home", ["/dead", "/alive"]))
        s.page("/dead", html("Dead"))
        s.page("/alive", html("Alive", ["/"]))
        si = run_crawl(s)
        self.assertEqual(si["no_outgoing_links"], [U("/dead")])

    def test_links_to_redirect_and_broken(self):
        # 2724308 链到重定向;2721106 链到坏页——Ahrefs 2021-09 起只算 404 和 410,403/5xx 不算
        s = Site()
        s.page("/", html("Home", ["/old", "/gone", "/gone410", "/forbidden", "/fine"]))
        s.page("/old", redirect_to="/fine")
        s.page("/gone", "nope", status=404)
        s.page("/gone410", "nope", status=410)
        s.page("/forbidden", "no", status=403)
        s.page("/fine", html("Fine", ["/"]))
        si = run_crawl(s)
        self.assertEqual(si["links_to_redirect"][0]["links"], [U("/old")])
        broken = si["links_to_broken_page"][0]
        self.assertEqual(broken["url"], HOME)
        self.assertEqual(sorted(x["url"] for x in broken["links"]), [U("/gone"), U("/gone410")])

    def test_canonical_url_without_inlinks(self):
        # 2595174:被声明为规范版本的 URL 没有站内入链
        s = Site()
        s.page("/", html("Home", ["/v1", "/linked"]))
        s.page("/v1", html("V1", ["/"], head='<link rel="canonical" href="/main">'))
        s.page("/main", html("Main", ["/"]))
        s.page("/linked", html("Linked", ["/", "/target"], head='<link rel="canonical" href="/target">'))
        s.page("/target", html("Target", ["/"]))
        si = run_crawl(s)
        self.assertEqual(si["canonical_url_no_incoming_internal_links"], [U("/main")])

    def test_canonical_url_without_inlinks_skipped_when_truncated(self):
        # --max 截断:样本外的页可能链着它,不判(everyinfra.com 80/5580+ 页实跑误报 1 条后加)
        s = Site()
        s.page("/", html("Home", ["/v1", "/a", "/b", "/c"]))
        s.page("/v1", html("V1", ["/"], head='<link rel="canonical" href="/main">'))
        for p in ("/a", "/b", "/c", "/main"):
            s.page(p, html(p, ["/"]))
        si = run_crawl(s, max_pages=3)
        self.assertEqual(si["canonical_url_no_incoming_internal_links"], [])
        self.assertIn("canonical_url_no_incoming_internal_links", si["partial"]["skipped"])


class CrawlRedirectsTests(unittest.TestCase):
    def test_302_broken_meta_refresh(self):
        # 2427783 302;2456799 重定向到 4xx/5xx;2433739 meta refresh
        s = Site()
        s.page("/", html("Home", ["/tmp", "/br", "/mr", "/mr0", "/perm"]))
        s.page("/tmp", redirect_to="/a", redirect_status=302)
        s.page("/perm", redirect_to="/a", redirect_status=301)
        s.page("/a", html("A", ["/"]))
        s.page("/br", redirect_to="/missing")
        s.page("/mr", html("MR", head='<meta http-equiv="refresh" content="0; url=/a">'))
        s.page("/mr0", html("MR0", head='<meta http-equiv="refresh" content="300">'))   # 只刷新本页,不是跳转
        si = run_crawl(s)
        self.assertEqual(urls_of(si["redirect_302"]), [U("/tmp")])
        self.assertEqual(urls_of(si["broken_redirect"]), [U("/br")])
        self.assertEqual(urls_of(si["meta_refresh_redirect"]), [U("/mr")])

    def test_http_to_https_redirect(self):
        s = Site()
        s.page("/", html("Home", ["http://example.com/p", "/q"]))
        s.page("http://example.com/p", redirect_to="https://example.com/p")
        s.page("/p", html("P", ["/"]))
        s.page("/q", html("Q", ["/"]))
        si = run_crawl(s)
        self.assertEqual(si["http_to_https_redirect"], ["http://example.com/p"])


class CrawlContentSocialLocaleTests(unittest.TestCase):
    def test_multiple_tags_and_og_url(self):
        # 2754360 多个 title;2652405 多个 description;canonical 文第 10 条 og:url 与 canonical 不一致
        s = Site()
        s.page("/", html("Home", ["/m", "/og", "/ogok"]))
        s.page("/m", html("M", head='<title>Second</title><meta name="description" content="a">'
                                    '<meta name="description" content="b">'))
        s.page("/og", html("OG", head='<link rel="canonical" href="https://example.com/og">'
                                      '<meta property="og:url" content="https://example.com/other">'))
        s.page("/ogok", html("OGOK", head='<link rel="canonical" href="https://example.com/ogok">'
                                          '<meta property="og:url" content="https://example.com/ogok">'))
        si = run_crawl(s)
        self.assertEqual(urls_of(si["multiple_title_tags"]), [U("/m")])
        self.assertEqual(urls_of(si["multiple_meta_description_tags"]), [U("/m")])
        self.assertEqual(urls_of(si["og_url_not_matching_canonical"]), [U("/og")])

    def test_svg_title_not_counted(self):
        s = Site()
        s.page("/", html("Home", ["/svg"]))
        s.page("/svg", html("SVG", extra_body="<svg><title>icon</title></svg>"))
        si = run_crawl(s)
        self.assertEqual(si["multiple_title_tags"], [])

    def test_html_lang_and_hreflang(self):
        # 2601025 lang 须 ISO 639-1(+ISO 3166-1);2747339 同一 URL 标多种语言(同语言不同地区不算);
        # 2598523 hreflang 语言与目标页 html lang 不一致;2608450 hreflang 指向非规范页
        alt = lambda c, h: '<link rel="alternate" hreflang="%s" href="%s">' % (c, h)  # noqa: E731
        s = Site()
        s.page("/", html("Home", ["/bad-lang", "/en", "/fr", "/es"],
                         head=alt("en-GB", "/en") + alt("en-US", "/en")))
        s.page("/bad-lang", html("Bad", lang="english"))
        s.page("/en", html("EN", ["/"], head=alt("en", "/en") + alt("de", "/en") + alt("fr", "/fr") + alt("es", "/es")))
        s.page("/fr", html("FR", ["/"], lang="de"))
        s.page("/es", html("ES", ["/"], lang="es", head='<link rel="canonical" href="/es-main">'))
        s.page("/es-main", html("ESM", ["/"], lang="es"))
        si = run_crawl(s)
        self.assertEqual(urls_of(si["html_lang_invalid"]), [U("/bad-lang")])
        self.assertEqual(urls_of(si["page_referenced_for_more_than_one_language"]), [U("/en")])
        # /fr 被标 fr、页面 lang=de;/en 被另一条 hreflang 标成 de、页面 lang=en——两者都是定义里的不一致
        self.assertEqual(urls_of(si["hreflang_and_html_lang_mismatch"]), [U("/en"), U("/fr")])
        self.assertEqual(urls_of(si["hreflang_to_non_canonical"]), [U("/en")])

    def test_hreflang_on_non_canonical_page_ignored(self):
        # Ahrefs 2021-09:「We now ignore hreflangs on non-canonical pages」
        alt = lambda c, h: '<link rel="alternate" hreflang="%s" href="%s">' % (c, h)  # noqa: E731
        s = Site()
        s.page("/", html("Home", ["/dupe"]))
        s.page("/dupe", html("D", ["/"], head='<link rel="canonical" href="/">' + alt("en", "/x") + alt("fr", "/x")))
        s.page("/x", html("X", ["/"]))
        si = run_crawl(s)
        self.assertEqual(si["page_referenced_for_more_than_one_language"], [])


class CrawlPerformanceTests(unittest.TestCase):
    def test_slow_compression_ai_heavy(self):
        s = Site()
        many = "".join('<script src="/s%d.js"></script>' % i for i in range(16))
        s.page("/", html("Home", ["/slow", "/plain", "/heavy"]), meta={"load_ms": 200, "encoding": "gzip"})
        s.page("/slow", html("Slow", ["/"]), meta={"load_ms": 5200, "encoding": "gzip"})
        s.page("/plain", html("Plain", ["/"]), meta={"load_ms": 100, "encoding": "identity"})
        s.page("/heavy", html("Heavy", ["/"], head=many), meta={"load_ms": 100, "encoding": "br"})
        si = run_crawl(s)
        self.assertEqual(urls_of(si["slow_page"]), [U("/slow")])
        self.assertEqual(si["not_compressed"], [U("/plain")])
        # AI 爬虫只取 HTML、不跑 JS:script 多不算重(everyinfra.com 实跑误报后改),慢才算
        self.assertEqual(urls_of(si["too_slow_or_heavy_for_ai_crawlers"]), [U("/slow")])

    def test_slow_threshold_flag(self):
        s = Site()
        s.page("/", html("Home", ["/x"]), meta={"load_ms": 900})
        s.page("/x", html("X", ["/"]), meta={"load_ms": 1500})
        self.assertEqual(run_crawl(s)["slow_page"], [])
        self.assertEqual(urls_of(run_crawl(s, slow_ms=1000)["slow_page"]), [U("/x")])


class CrawlResourceTests(unittest.TestCase):
    def test_resources(self):
        # Image broken 2628254 / Page has broken image 2699397 / JavaScript broken 2750495 / CSS broken 2759921:
        # 资源返回 4xx/5xx;CSS file size too large 2760432:>15kB;Image file size too large:>100KB
        s = Site()
        head = ('<link rel="stylesheet" href="/big.css"><link rel="stylesheet" href="/small.css">'
                '<script src="/bad.js"></script><script src="/moved.js"></script>')
        imgs = ('<img src="/missing.png" alt="m"><img src="/huge.jpg" alt="h"><img src="/ok.jpg" alt="o">'
                '<img src="http://example.com/insecure.png" alt="i">')
        s.page("/", html("Home", ["/clean"], head=head, extra_body=imgs))
        s.page("/clean", html("Clean", ["/"], extra_body='<img src="/ok.jpg" alt="o">'))
        s.page("/big.css", "x", headers={"Content-Length": str(20 * 1024)})
        s.page("/small.css", "x", headers={"Content-Length": str(10 * 1024)})
        s.page("/bad.js", "", status=500)
        s.page("/moved.js", redirect_to="/new.js")
        s.page("/new.js", "x", headers={"Content-Length": "10"})
        s.page("/huge.jpg", "x", headers={"Content-Length": str(150 * 1024)})
        s.page("/ok.jpg", "x", headers={"Content-Length": str(50 * 1024)})
        s.page("http://example.com/insecure.png", "x", headers={"Content-Length": "10"})
        si = run_crawl(s, check_resources=True)
        self.assertEqual(urls_of(si["image_broken"]), [U("/missing.png")])
        self.assertEqual(urls_of(si["page_has_broken_image"]), [HOME])
        self.assertEqual(urls_of(si["image_file_size_too_large"]), [U("/huge.jpg")])
        self.assertEqual(urls_of(si["javascript_broken"]), [U("/bad.js")])
        self.assertEqual(urls_of(si["page_has_broken_javascript"]), [HOME])
        self.assertEqual(urls_of(si["javascript_redirects"]), [U("/moved.js")])
        self.assertEqual(urls_of(si["css_file_size_too_large"]), [U("/big.css")])
        self.assertEqual(si["css_broken"], [])
        self.assertEqual(urls_of(si["https_page_links_to_http_image"]), [HOME])

    def test_resources_not_checked_without_flag(self):
        s = Site()
        s.page("/", html("Home", extra_body='<img src="/missing.png" alt="m">'))
        si = run_crawl(s)
        self.assertNotIn("image_broken", si)


# ---------------------------------------------------------------------------
# site_audit 单页
# ---------------------------------------------------------------------------

ROOT = {"/robots.txt": (200, {}, "User-agent: *\nAllow: /\n"), "/sitemap.xml": (200, {}, "<urlset/>"),
        "/llms.txt": (200, {}, "# llms\n")}
TW = ('<meta name="twitter:card" content="summary"><meta name="twitter:title" content="t">'
      '<meta name="twitter:description" content="d"><meta name="twitter:image" content="https://example.com/i.png">')


def audit_page(head="", url="https://example.com/self", headers=None, lang="en", body=None, robots=None):
    page = ('<!doctype html><html lang="%s"><head><title>Example Article Page Title Long Enough</title>'
            '<meta name="description" content="A sufficiently long description text that exceeds eighty characters easily.">'
            '%s</head><body><main><article><h1>Heading</h1><p>%s</p></article></main></body></html>'
            % (lang, head, body if body is not None else "In short, the answer. " + "filler word " * 150))
    root = "%s://%s" % tuple(url.split("://", 1)[0:1] + [url.split("/")[2]])
    table = {root + p: v for p, v in ROOT.items()}
    if robots is not None:
        table[root + "/robots.txt"] = (200, {}, robots)
    table[url] = (200, headers or {}, page)

    def fake(u, timeout=15):
        if u in table:
            return table[u]
        raise urllib.error.HTTPError(u, 404, "nf", {}, None)
    orig = sa.fetch
    sa.fetch = fake
    try:
        F = sa.audit(url)[0]
    finally:
        sa.fetch = orig
    return {sa.rule_slug(a, m): sev for sev, a, m in F}


class SiteAuditTests(unittest.TestCase):
    def test_multiple_title_and_description(self):
        got = audit_page('<title>Second</title><meta name="description" content="Another description">' + TW)
        self.assertEqual(got.get("title-multiple"), "WARN")
        self.assertEqual(got.get("description-multiple"), "WARN")
        ctl = audit_page(TW, body="In short. " + "filler word " * 150 + "<svg><title>icon</title></svg>")
        self.assertNotIn("title-multiple", ctl)
        self.assertNotIn("description-multiple", ctl)

    def test_canonical_protocol_and_og_url(self):
        got = audit_page('<link rel="canonical" href="http://example.com/self">'
                         '<meta property="og:url" content="https://example.com/other">' + TW)
        self.assertEqual(got.get("canonical-https-to-http"), "WARN")
        self.assertEqual(got.get("og-url-canonical-mismatch"), "INFO")
        ctl = audit_page('<link rel="canonical" href="https://example.com/self">'
                         '<meta property="og:url" content="https://example.com/self">' + TW)
        self.assertNotIn("canonical-https-to-http", ctl)
        self.assertNotIn("og-url-canonical-mismatch", ctl)
        h2s = audit_page('<link rel="canonical" href="https://example.com/self">' + TW, url="http://example.com/self")
        self.assertEqual(h2s.get("canonical-http-to-https"), "INFO")

    def test_twitter_card(self):
        self.assertEqual(audit_page().get("twitter-card-missing"), "INFO")
        self.assertEqual(audit_page('<meta name="twitter:card" content="summary">').get("twitter-card-incomplete"), "INFO")
        full = audit_page(TW)
        self.assertNotIn("twitter-card-missing", full)
        self.assertNotIn("twitter-card-incomplete", full)

    def test_lang_and_hreflang(self):
        self.assertEqual(audit_page(TW, lang="english").get("lang-invalid"), "WARN")
        self.assertNotIn("lang-invalid", audit_page(TW, lang="en-GB"))
        alt = lambda c, h: '<link rel="alternate" hreflang="%s" href="%s">' % (c, h)  # noqa: E731
        multi = audit_page(TW + alt("en", "https://example.com/x") + alt("fr", "https://example.com/x"))
        self.assertEqual(multi.get("hreflang-multi-language"), "WARN")
        regions = audit_page(TW + alt("en-GB", "https://example.com/x") + alt("en-US", "https://example.com/x"))
        self.assertNotIn("hreflang-multi-language", regions)
        mismatch = audit_page(TW + alt("en", "https://example.com/self"), lang="de")
        self.assertEqual(mismatch.get("hreflang-lang-mismatch"), "WARN")
        self.assertNotIn("hreflang-lang-mismatch", audit_page(TW + alt("en", "https://example.com/self"), lang="en"))

    def test_robots_directives(self):
        nf = audit_page(TW + '<meta name="robots" content="nofollow">')
        self.assertEqual(nf.get("robots-nofollow"), "WARN")
        both = audit_page(TW + '<meta name="robots" content="noindex">', headers={"X-Robots-Tag": "noindex"})
        self.assertEqual(both.get("robots-noindex-html-and-header"), "INFO")
        one = audit_page(TW, headers={"X-Robots-Tag": "noindex"})
        self.assertNotIn("robots-noindex-html-and-header", one)
        self.assertNotIn("robots-nofollow", one)

    def test_meta_refresh_and_double_slash(self):
        self.assertEqual(audit_page(TW + '<meta http-equiv="refresh" content="0; url=/new">').get("redirect-meta-refresh"),
                         "WARN")
        self.assertNotIn("redirect-meta-refresh", audit_page(TW + '<meta http-equiv="refresh" content="300">'))
        self.assertEqual(audit_page(TW, url="https://example.com/a//b").get("url-double-slash"), "WARN")
        self.assertNotIn("url-double-slash", audit_page(TW, url="https://example.com/a/b"))

    def test_size_and_compression(self):
        big = audit_page(TW, body="x " * (1100 * 1024))
        self.assertEqual(big.get("size-html-too-large"), "WARN")
        self.assertNotIn("size-html-too-large", audit_page(TW))
        asked = {sa.ASKED_ENCODING_HDR: "gzip, deflate"}
        self.assertEqual(audit_page(TW, headers=asked).get("compression-none"), "WARN")
        self.assertNotIn("compression-none", audit_page(TW, headers=dict(asked, **{"Content-Encoding": "gzip"})))
        self.assertNotIn("compression-none", audit_page(TW))     # 没真的发过 Accept-Encoding(桩、离线)不判

    def test_user_triggered_bots_severity(self):
        got = audit_page(TW, robots="User-agent: Claude-User\nDisallow: /\n\nUser-agent: *\nAllow: /\n")
        self.assertEqual(got.get("ai-bots-user-fetch-blocked"), "WARN")
        got = audit_page(TW, robots="User-agent: ChatGPT-User\nDisallow: /\n\nUser-agent: *\nAllow: /\n")
        self.assertEqual(got.get("ai-bots-user-fetch-blocked"), "INFO")
        self.assertNotIn("CRITICAL", got.values())


# ---------------------------------------------------------------------------
# redirect_chain / robots_posture / schema_lint
# ---------------------------------------------------------------------------

def chain_run(hops, final_body=""):
    orig = redirect_chain.request_once

    def fake(u, t, ua=None):
        st, loc = hops[u]
        if not (300 <= st < 400):
            redirect_chain.LAST_BODY["text"] = final_body
        return st, loc, 1.0
    redirect_chain.request_once = fake
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            rc = redirect_chain.main([next(iter(hops))])
    finally:
        redirect_chain.request_once = orig
    return rc, out.getvalue()


class RedirectChainTests(unittest.TestCase):
    def test_302_hop(self):
        rc, out = chain_run({"https://e.com/a": (302, "/b"), "https://e.com/b": (200, None)})
        self.assertIn("[INFO] 第 1 跳用 302", out)
        rc, out = chain_run({"https://e.com/a": (301, "/b"), "https://e.com/b": (200, None)})
        self.assertNotIn("302", out.split("---- 问题 ----")[-1] if "---- 问题 ----" in out else "")

    def test_broken_redirect(self):
        rc, out = chain_run({"https://e.com/a": (301, "/b"), "https://e.com/b": (404, None)})
        self.assertEqual(rc, 1)
        self.assertIn("重定向终点返回 HTTP 404", out)

    def test_meta_refresh_on_final_page(self):
        rc, out = chain_run({"https://e.com/a": (200, None)},
                            final_body='<meta http-equiv="refresh" content="4; URL=\'https://e.com/z\'">')
        self.assertIn("meta refresh 再跳到 https://e.com/z", out)
        rc, out = chain_run({"https://e.com/a": (200, None)}, final_body='<meta http-equiv="refresh" content="60">')
        self.assertNotIn("meta refresh", out)

    def test_http_to_https_hop(self):
        rc, out = chain_run({"http://e.com/a": (301, "https://e.com/a"), "https://e.com/a": (200, None)})
        self.assertIn("HTTP→HTTPS (Ahrefs HTTP to HTTPS redirect", out)


class RobotsPolicyTests(unittest.TestCase):
    def kinds(self, txt):
        return {(x["kind"], x["vendor"]) for x in robots_posture.analyze(txt)["inconsistent_ai_policies"]}

    def test_inconsistent(self):
        k = self.kinds("User-agent: ChatGPT-User\nDisallow: /\n\nUser-agent: *\nAllow: /\n")
        self.assertIn(("same_vendor_answer_bots", "OpenAI"), k)
        k = self.kinds("User-agent: OAI-SearchBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n")
        self.assertIn(("training_open_search_closed", "OpenAI"), k)
        self.assertIn(("across_ai_search_bots", None), k)

    def test_consistent(self):
        self.assertEqual(self.kinds("User-agent: *\nAllow: /\n"), set())
        self.assertEqual(self.kinds("User-agent: *\nDisallow: /\n"), set())


def lint(html_text):
    orig, argv = schema_lint.fetch, sys.argv
    schema_lint.fetch = lambda u, *a, **k: html_text
    sys.argv = ["schema_lint.py", "https://shop.test/"]   # example.com 在占位符黑名单里,夹具不用它
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            try:
                schema_lint.main()
                rc = 0
            except SystemExit as e:
                rc = e.code
    finally:
        schema_lint.fetch, sys.argv = orig, argv
    return rc, out.getvalue()


def ld(obj):
    import json
    return '<script type="application/ld+json">%s</script>' % json.dumps(obj)


class SchemaLintTests(unittest.TestCase):
    """Ahrefs「Structured data Google rich results validation error」(help 8223239):按 Google 文档的必填项查。"""

    def test_product_required(self):
        rc, out = lint(ld({"@context": "https://schema.org", "@type": "Product", "name": "P"}))
        self.assertEqual(rc, 1)
        self.assertIn("review / aggregateRating / offers 三选一", out)
        rc, out = lint(ld({"@context": "https://schema.org", "@type": "Product", "name": "P",
                           "offers": {"@type": "Offer", "price": "9.99", "priceCurrency": "USD"}}))
        self.assertEqual(rc, 0, out)

    def test_breadcrumb_last_item_may_omit_item(self):
        good = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://shop.test/"},
            {"@type": "ListItem", "position": 2, "name": "Here"}]}
        self.assertEqual(lint(ld(good))[0], 0)
        bad = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home"},
            {"@type": "ListItem", "position": 2, "name": "Here"}]}
        rc, out = lint(ld(bad))
        self.assertEqual(rc, 1)
        self.assertIn("itemListElement[0].item", out)

    def test_rating_range(self):
        rc, out = lint(ld({"@context": "https://schema.org", "@type": "Product", "name": "P",
                           "aggregateRating": {"@type": "AggregateRating", "ratingValue": 6, "reviewCount": 3}}))
        self.assertEqual(rc, 1)
        self.assertIn("ratingValue 6 超出范围", out)
        rc, _ = lint(ld({"@context": "https://schema.org", "@type": "Product", "name": "P",
                         "aggregateRating": {"@type": "AggregateRating", "ratingValue": 8, "bestRating": 10,
                                             "reviewCount": 3}}))
        self.assertEqual(rc, 0)

    def test_nested_reference_not_checked(self):
        # itemReviewed / publisher 下的实体只是引用,不单独按富结果必填查
        rc, out = lint(ld({"@context": "https://schema.org", "@type": "Review", "author": {"@type": "Person", "name": "A"},
                           "reviewRating": {"@type": "Rating", "ratingValue": 4},
                           "itemReviewed": {"@type": "Product", "name": "P"}}))
        self.assertEqual(rc, 0, out)

    def test_exit_codes(self):
        self.assertEqual(lint("<html><body>no json-ld</body></html>")[0], 3)
        rc, out = lint('<script type="application/ld+json">{bad json</script>')
        self.assertEqual(rc, 1)
        self.assertIn("结论: 退出码 1", out)
        rc, out = lint(ld({"@context": "https://schema.org", "@type": "Article", "headline": "h"}))
        self.assertEqual(rc, 0)
        self.assertIn("结论: 退出码 0", out)


if __name__ == "__main__":
    unittest.main()
