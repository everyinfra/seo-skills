#!/usr/bin/env python3
"""RQ-229 例 7 缺口回归(2026-11-06):规模站上脚本链找不到 / 只找到一部分的几类问题(stdlib unittest,合成小页面,零网络)。

期望值来源(不是读实现写的):
  --allow-local          任务要求原文:只放行回环(127.0.0.0/8、::1、localhost),私网照旧拒;不加时报错写明「--allow-local」
  链到 4xx 的站内链接    Google「All 4xx errors, except 429, are treated the same ... the content doesn't exist」
                         https://developers.google.com/search/docs/crawling-indexing/http-network-errors
  重定向链               Ahrefs「"Redirect chain" ... for redirect chains URLs ≤ 5」「"Redirect chain too long" ... URLs > 5」
                         https://ahrefs.com/blog/site-audit-issues-update-september-2021/
  软 404                 Google「a URL that returns a page telling the user that the page does not exist and also a 200」
                         https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors#soft-404-errors;
                         Screaming Frog 例句「Page Not Found」「404 Page Can't Be Found」「Error 404. Page no longer exists」
                         https://www.screamingfrog.co.uk/seo-spider/issues/content/soft-404-pages/
  canonical 指向 noindex  Screaming Frog「Non-Indexable Canonical」:canonical 目标「are 'noindex'」
                         https://www.screamingfrog.co.uk/seo-spider/issues/canonicals/non-indexable-canonical/
  孤儿页(sitemap 里)    Ahrefs「Canonical URL has no incoming internal links」:「URLs in the website's sitemap files that have
                         no incoming internal links」https://help.ahrefs.com/en/articles/2595174
  重复 title             Ahrefs「Duplicate title tag」按组列页(health_score 列出撞在一起的 URL)
独立可运行:python3 tests/test_crawl_gaps_20261106.py"""
import contextlib
import io
import os
import subprocess
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import health_score as hs  # noqa: E402
import link_graph as lg  # noqa: E402
import site_crawl as sc  # noqa: E402
from test_ahrefs_coverage import FILLER, Site, U, html, ns  # noqa: E402


def big_sitemap(site, extra_paths=(), n=60):
    """≥50 条 loc 的 sitemap(爬虫兜底关闭的规模),每页互不相同、互相不链。"""
    paths = ["/p%02d" % i for i in range(n)] + list(extra_paths)
    locs = "".join("<url><loc>%s</loc></url>" % U(p) for p in paths)
    site.page("/sitemap.xml", '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
              + locs + "</urlset>")
    for p in paths[:n]:
        if U(p) not in site.routes:
            site.page(p, html("Item %s" % p, body_text="item %s %s" % (p, FILLER)))
    return paths


def run(site, **kw):
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
    return report


class AllowLocalTests(unittest.TestCase):
    def _guard(self, ip, allow):
        orig, orig_flag = sc.dns_resolve, sc.ALLOW_LOCAL
        sc.dns_resolve = lambda host: [ip]
        sc.ALLOW_LOCAL = allow
        sc._ssrf_cache.clear()
        try:
            sc.ssrf_guard("dev.example")
            return None
        except sc.GuardError as e:
            return str(e)
        finally:
            sc.dns_resolve, sc.ALLOW_LOCAL = orig, orig_flag
            sc._ssrf_cache.clear()

    def test_loopback_needs_flag(self):
        for ip in ("127.0.0.1", "127.8.9.10", "::1"):
            msg = self._guard(ip, False)
            self.assertIsNotNone(msg, ip)
            self.assertIn("--allow-local", msg)
            self.assertIsNone(self._guard(ip, True), ip)

    def test_private_ranges_still_refused_with_flag(self):
        for ip in ("10.0.0.5", "172.16.3.4", "192.168.1.20", "169.254.169.254", "fd00::1"):
            self.assertIsNotNone(self._guard(ip, True), ip)

    def test_cli_without_flag_exits_2_with_hint(self):
        p = subprocess.run([sys.executable, os.path.join(SCRIPTS, "site_crawl.py"), "http://127.0.0.1:9/",
                            "--out", os.devnull], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 2)
        self.assertIn("--allow-local", p.stderr)

    def test_ip_host_is_its_own_domain(self):
        self.assertEqual(sc.registrable("127.0.0.1"), "127.0.0.1")
        self.assertEqual(sc.registrable("localhost"), "localhost")


class LinkTargetsInBigSitemapTests(unittest.TestCase):
    """sitemap ≥50 条时,站内链接指向、sitemap 没列的 URL 仍要请求(在 --max 内)。"""

    def test_link_to_404_reported_with_source(self):
        s = Site()
        big_sitemap(s)
        s.page("/p03", html("Item p03", ["/gone-product"], body_text="p03 " + FILLER))
        rep = run(s)
        si = rep["site_issues"]
        rows = [r for r in si["links_to_4xx_page"] if r["url"] == U("/gone-product")]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], 404)
        self.assertEqual(rows[0]["linked_from"], [U("/p03")])
        self.assertEqual(urls_of_broken(si), [U("/p03")])        # Ahrefs 口径 404/410 一项也报

    def test_other_4xx_counts_429_does_not(self):
        # 403/503 在同站先给过 2xx 之后另按「疑似限流」处理(site_crawl 既有口径),这里用 401、410
        s = Site()
        big_sitemap(s)
        s.page("/p01", html("Item p01", ["/members", "/removed", "/busy"], body_text="p01 " + FILLER))
        s.page("/members", "", status=401)
        s.page("/removed", "", status=410)
        s.page("/busy", "", status=429)
        si = run(s)["site_issues"]
        self.assertEqual([(r["url"], r["status"]) for r in si["links_to_4xx_page"]],
                         [(U("/members"), 401), (U("/removed"), 410)])

    def test_three_hop_chain_reported_with_start_and_source(self):
        s = Site()
        big_sitemap(s)
        s.page("/p05", html("Item p05", ["/old-guide"], body_text="p05 " + FILLER))
        s.page("/old-guide", redirect_to="/guide-v2")
        s.page("/guide-v2", redirect_to="/blog/guide")
        s.page("/blog/guide", redirect_to="/guides/guide")
        s.page("/guides/guide", html("Guide", body_text="guide " + FILLER))
        si = run(s)["site_issues"]
        rows = si["redirect_chain"]
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r["url"], r["hops"]), (U("/old-guide"), 3))
        self.assertEqual(r["chain"], [U("/old-guide"), U("/guide-v2"), U("/blog/guide"), U("/guides/guide")])
        self.assertEqual(r["linked_from"], [U("/p05")])
        self.assertEqual(si["redirect_chain_too_long"], [])

    def test_chain_length_buckets(self):
        s = Site()
        s.page("/", html("Home", ["/one-hop", "/five-hop"]))
        s.page("/one-hop", redirect_to="/final")                  # 1 跳:普通重定向,不是链
        s.page("/final", html("Final"))
        s.page("/five-hop", redirect_to="/h2")                     # 5 跳 = 链上 6 个 URL > 5
        for a, b in (("/h2", "/h3"), ("/h3", "/h4"), ("/h4", "/h5"), ("/h5", "/end")):
            s.page(a, redirect_to=b)
        s.page("/end", html("End"))
        si = run(s)["site_issues"]
        self.assertEqual(si["redirect_chain"], [])
        self.assertEqual([(r["url"], r["hops"]) for r in si["redirect_chain_too_long"]], [(U("/five-hop"), 5)])

    def test_sitemap_only_restores_old_behaviour(self):
        s = Site()
        big_sitemap(s)
        s.page("/p03", html("Item p03", ["/gone-product"], body_text="p03 " + FILLER))
        rep = run(s, sitemap_only=True)
        self.assertNotIn(U("/gone-product"), {p["url"] for p in rep["pages"]})
        self.assertEqual(rep["site_issues"]["links_to_4xx_page"], [])


def urls_of_broken(si):
    return [r["url"] for r in si["links_to_broken_page"]]


class Soft404Tests(unittest.TestCase):
    def _issues(self, page_html, status=200, headers=None):
        s = Site()
        s.page("/", html("Home", ["/x"]))
        s.page("/x", page_html, status=status, headers=headers)
        return run(s)["site_issues"]["soft_404"]

    def test_title_page_not_found(self):
        rows = self._issues(html("Page not found | Ridge Shop", body_text="Sorry, try the search. " + FILLER))
        self.assertEqual([r["url"] for r in rows], [U("/x")])
        self.assertEqual(rows[0]["linked_from"], [U("/")])

    def test_screaming_frog_examples(self):
        for h1 in ("404 Page Can't Be Found", "Error 404. Page no longer exists"):
            page = ('<html><head><title>Shop</title></head><body><h1>%s</h1><p>%s</p></body></html>' % (h1, FILLER))
            self.assertEqual(len(self._issues(page)), 1, h1)

    def test_short_body_message(self):
        page = '<html><head><title>Shop</title></head><body><h1>Shop</h1><p>Sorry, the page you were looking for does not exist.</p></body></html>'
        self.assertEqual(len(self._issues(page)), 1)

    def test_not_soft_404(self):
        # 讲 404 的长文章、真 404、noindex 的空搜索页、长正文里顺带一句都不算
        article = html("How to fix 404 Not Found errors | Blog", body_text="A page not found error means ... " + FILLER * 3)
        self.assertEqual(self._issues(article), [])
        self.assertEqual(self._issues(html("Page not found"), status=404), [])
        noidx = html("Page not found", head='<meta name="robots" content="noindex">')
        self.assertEqual(self._issues(noidx), [])
        long_body = html("Trail shoes", body_text=FILLER * 3 + " we could not find the page you linked yesterday. " + FILLER * 2)
        self.assertEqual(self._issues(long_body), [])


class CanonicalNoindexTests(unittest.TestCase):
    def test_canonical_to_meta_noindex_and_header_noindex(self):
        s = Site()
        s.page("/", html("Home", ["/a", "/b", "/c"]))
        s.page("/a", html("A", head='<link rel="canonical" href="https://example.com/a-bundle">'))
        s.page("/a-bundle", html("A bundle", head='<meta name="robots" content="noindex">'))     # 没被链接,只被 canonical 指
        s.page("/b", html("B", head='<link rel="canonical" href="https://example.com/b-main">'))
        s.page("/b-main", html("B main"), headers={"X-Robots-Tag": "noindex"})
        s.page("/c", html("C", head='<link rel="canonical" href="https://example.com/c-main">'))
        s.page("/c-main", html("C main"))                                                       # 可索引:不报
        rows = run(s)["site_issues"]["canonical_points_to_noindex"]
        self.assertEqual(sorted((r["url"], r["canonical"]) for r in rows),
                         [(U("/a"), U("/a-bundle")), (U("/b"), U("/b-main"))])


class OrphanInSitemapTests(unittest.TestCase):
    def test_link_graph_counts_sitemap_orphans_when_links_followed(self):
        s = Site()
        big_sitemap(s, extra_paths=["/lonely"])
        s.page("/", html("Home", ["/p%02d" % i for i in range(60)]))
        s.page("/lonely", html("Lonely", body_text="lonely " + FILLER))
        rep = run(s)
        self.assertIn(U("/lonely"), rep["orphans"])
        zero, _one, excluded, _c = lg.inlink_lists(rep)
        self.assertEqual(zero, [U("/lonely")])
        self.assertEqual(excluded["sitemap_only"], [])

    def test_link_graph_keeps_excluding_when_undersampled(self):
        s = Site()
        big_sitemap(s, extra_paths=["/lonely"])
        s.page("/lonely", html("Lonely", body_text="lonely " + FILLER))
        rep = run(s, sitemap_only=True)                       # 旧口径:链接只进图,边欠采样
        zero, _one, excluded, _c = lg.inlink_lists(rep)
        self.assertNotIn(U("/lonely"), zero)
        self.assertIn(U("/lonely"), excluded["sitemap_only"])

    def test_redirected_sitemap_url_not_orphan(self):
        s = Site()
        big_sitemap(s, extra_paths=["/old"])
        s.page("/", html("Home", ["/p%02d" % i for i in range(60)] + ["/new"]))
        s.page("/old", redirect_to="/new")
        s.page("/new", html("New", body_text="new " + FILLER))
        zero, _one, excluded, _c = lg.inlink_lists(run(s))
        self.assertNotIn(U("/old"), zero)
        self.assertIn(U("/old"), excluded["redirected"])


class DuplicateTitleGroupsTests(unittest.TestCase):
    def test_health_score_lists_colliding_urls(self):
        res = {u: {"findings": [], "meta": {"title": t}} for u, t in
               ((U("/a"), "Same"), (U("/b"), "Same"), (U("/c"), "Other"))}
        rep = hs.compute({"results": res}, set(), {})
        self.assertEqual(rep["duplicate_title_groups"], [{"title": "Same", "urls": [U("/a"), U("/b")]}])

    def test_redirecting_url_is_not_a_duplicate(self):
        # 旧网址 301 到新网址:site_audit 跟完重定向审到的是新网址的 title,不是第二个页面(Ahrefs 重复 title 只算可索引页)
        res = {U("/new"): {"findings": [], "meta": {"title": "Tent"}},
               U("/old"): {"findings": [], "meta": {"title": "Tent", "final_url": U("/new")}},
               U("/x"): {"findings": [], "meta": {"title": "X"}}}
        rep = hs.compute({"results": res}, set(), {})
        self.assertEqual(rep["duplicate_title_groups"], [])


if __name__ == "__main__":
    unittest.main()
