#!/usr/bin/env python3
"""site_crawl 摘要出链计数(B27)与重定向页孤儿判定(B28,含 orphan_fix)回归测试。
合成站点,http_fetch/DNS 打桩,零网络(复用 test_site_crawl 的 FakeWeb 写法)。

期望值来源:bug 卡——
- B27:「外链 197181」实际是全部出链(内链 193,438 + 外链 3,743)→ 内链、外链、总出链分开显示。
- B28:301 到主站的 www.、api. 子域首页被当成孤儿,orphan_fix 建议从首页给它们加链接 →
  重定向页不算孤儿,不建议加内链(内链该指向重定向目标,而不是被重定向的 URL)。
"""
import argparse
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import orphan_fix as of  # noqa: E402
import site_crawl as sc  # noqa: E402

HOME = "https://example.com/"


class FakeWeb:
    def __init__(self):
        self.routes = {}

    def add(self, url, status=200, body="", chain=None, final_url=None):
        self.routes[url] = (status, body, chain or [], final_url)

    def __call__(self, url, timeout=10.0, method="GET"):
        status, body, chain, final = self.routes.get(url, (404, "", [], None))
        return {"status": status, "final_url": final or url, "chain": chain, "headers": {},
                "body": body, "body_bytes": body.encode()}


@contextlib.contextmanager
def patched(web, dns_hosts=()):
    orig = sc.http_fetch, sc.dns_resolve, sc._sleep
    sc.http_fetch = web

    def fake_dns(host):
        if host in dns_hosts:
            return ["93.184.216.34"]
        raise OSError("NXDOMAIN")
    sc.dns_resolve, sc._sleep = fake_dns, lambda t: None
    sc._ssrf_cache.clear()
    try:
        yield
    finally:
        sc.http_fetch, sc.dns_resolve, sc._sleep = orig
        sc._ssrf_cache.clear()


def make_ns(**kw):
    d = dict(site="https://example.com", urls=None, max_pages=500, delay=0.0,
             ignore_robots=False, strip_params=False, same_host=False,
             include_subdomains=True, subs="dns", check_external=False,
             timeout=5.0, out="crawl.json", urls_out=None, json=False)
    d.update(kw)
    return argparse.Namespace(**d)


def html_links(title, hrefs):
    return "<html><head><title>%s</title></head><body>%s</body></html>" % (
        title, "".join('<a href="%s">x</a>' % h for h in hrefs))


def urlset(locs):
    return "<urlset>" + "".join("<url><loc>%s</loc></url>" % u for u in locs) + "</urlset>"


class OutlinkSummaryTests(unittest.TestCase):
    def test_internal_external_total_shown_separately(self):
        web = FakeWeb()
        web.add("https://example.com/sitemap.xml", body=urlset([HOME, "https://example.com/p1"]))
        web.add(HOME, body=html_links("Home", ["/p1", "https://github.com/a"]))
        web.add("https://example.com/p1", body=html_links("P1", ["/", "https://twitter.com/x",
                                                                   "https://github.com/b"]))
        with patched(web):
            rep, rc = sc.Crawler(make_ns()).run()
        st = rep["stats"]
        self.assertEqual(st["total_out_internal"], 2)
        self.assertEqual(st["total_out_external"], 3)
        self.assertEqual(st["total_outlinks"], 5)                          # 总出链语义不变
        md = sc.render_markdown(rep)
        self.assertIn("外链 3", md)                                         # 修前「外链 5」(=总出链)
        self.assertIn("总出链 5", md)
        self.assertNotIn("外链 5", md)


class RedirectOrphanTests(unittest.TestCase):
    def _crawl(self):
        web = FakeWeb()
        web.add("https://example.com/sitemap.xml", body=urlset([
            HOME, "https://example.com/p1", "https://example.com/real-orphan",
            "https://www.example.com/", "https://api.example.com/"]))
        web.add(HOME, body=html_links("Home", ["/p1"]))
        web.add("https://example.com/p1", body=html_links("P1", ["/"]))
        web.add("https://example.com/real-orphan", body=html_links("Real orphan", []))
        for sub in ("https://www.example.com/", "https://api.example.com/"):
            web.add(sub, status=200, body=html_links("Home", ["/p1"]),
                    chain=[{"status": 301, "location": HOME}], final_url=HOME)
        with patched(web, dns_hosts={"www.example.com", "api.example.com"}):
            rep, rc = sc.Crawler(make_ns()).run()
        return rep

    def test_redirected_subdomain_roots_not_orphans(self):
        rep = self._crawl()
        self.assertIn("https://example.com/real-orphan", rep["orphans"])
        self.assertNotIn("https://www.example.com/", rep["orphans"])       # 修前算孤儿
        self.assertNotIn("https://api.example.com/", rep["orphans"])

    def test_orphan_fix_skips_redirected_even_in_old_crawl_json(self):
        # 旧版 crawl.json 已把重定向页写进 orphans:orphan_fix 也要自己剔除
        rep = {"domain": "example.com", "orphans": [
                   "https://www.example.com/", "https://example.com/blog/lost"],
               "pages": [
                   {"url": HOME, "status": 200, "inlinks": 3, "out_internal": 4},
                   {"url": "https://example.com/blog/hub", "status": 200, "inlinks": 2, "out_internal": 3},
                   {"url": "https://example.com/blog/lost", "status": 200, "inlinks": 0, "out_internal": 0},
                   {"url": "https://www.example.com/", "status": 200, "inlinks": 0, "out_internal": 1,
                    "final_url": HOME}]}
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(rep, f)
        f.close()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            of.main(["--crawl", f.name, "--json"])
        os.unlink(f.name)
        payload = json.loads(out.getvalue())
        orphans = [p["orphan"] for p in payload["plans"]]
        self.assertEqual(orphans, ["https://example.com/blog/lost"])        # 修前含 www 根页


if __name__ == "__main__":
    unittest.main(verbosity=2)
