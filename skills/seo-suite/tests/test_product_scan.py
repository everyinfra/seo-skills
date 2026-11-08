#!/usr/bin/env python3
"""product_scan.py golden 用例(stdlib unittest,合成数据,零网络、零真实延时)。
假站:一个小 SaaS「Acme Cloud」——首页带 og:site_name、JSON-LD Organization+sameAs、两个 h2、注册按钮;
/pricing/ 带 $9/mo;robots 声明 sitemap(index → 子 sitemap,含 /en/ /es/ 前缀的 pricing、docs、blog、vs 页);
llms.txt 带 # 标题、> 摘要、## 两条产品线。假仓库:临时 Next.js 目录。
期望值全部来自本文件写下的假站 / 假仓库内容(输入已知),不从实现反推。
独立可运行:python3 -m unittest tests/test_product_scan.py;也被 tests/run_tests.py 自动发现。"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import site_crawl as sc  # noqa: E402
import product_scan as ps  # noqa: E402

ORIGIN = "https://acme.example"

HOME = """<!doctype html><html lang="en"><head>
<title>Acme Cloud | Deploy APIs in minutes</title>
<meta name="description" content="Acme Cloud hosts your APIs.">
<meta property="og:site_name" content="Acme Cloud">
<link rel="alternate" hreflang="en" href="https://acme.example/en/">
<link rel="alternate" hreflang="es" href="https://acme.example/es/">
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[
 {"@type":"Organization","name":"Acme Cloud Inc","sameAs":["https://github.com/acme","https://x.com/acme"]},
 {"@type":"WebSite","name":"Acme Cloud"}]}</script>
</head><body>
<h1>Ship APIs faster</h1>
<h2>Hosting</h2><h2>Monitoring</h2>
<a href="/signup">Sign up</a>
<a href="/about">About</a>
<p>Everything you need to run APIs in production.</p>
</body></html>"""

PRICING = """<!doctype html><html lang="en"><head><title>Pricing · Acme Cloud</title></head><body>
<h1>Pricing</h1><p>Starter is free. Pro costs $9/mo per workspace.</p>
<button>Start free trial</button></body></html>"""

ROBOTS = "User-agent: *\nDisallow: /admin\nSitemap: https://acme.example/sitemap_index.xml\n"

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<sitemap><loc>https://acme.example/sitemap-pages.xml</loc></sitemap>
</sitemapindex>"""

PAGE_URLS = [
    "https://acme.example/",
    "https://acme.example/pricing/",
    "https://acme.example/en/pricing/",
    "https://acme.example/es/pricing/",
    "https://acme.example/en/docs/getting-started",
    "https://acme.example/es/docs/getting-started",
    "https://acme.example/en/blog/hello-world",
    "https://acme.example/es/blog/hello-world",
    "https://acme.example/en/vs/rival",
    "https://acme.example/pricing/",            # 重复,去重后不计
]
SITEMAP_PAGES = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                 + "".join("<url><loc>%s</loc></url>" % u for u in PAGE_URLS) + "</urlset>")

LLMS = """# Acme Cloud

> API hosting and monitoring for small teams.

## Hosting
- [Deploy](https://acme.example/en/docs/getting-started)

## Monitoring
- [Alerts](https://acme.example/en/docs/getting-started)
"""

SIMPLE = '<!doctype html><html lang="%s"><head><title>%s</title></head><body><h1>%s</h1></body></html>'

FAKE_SITE = {
    ORIGIN + "/": (200, {}, HOME),
    ORIGIN + "/robots.txt": (200, {}, ROBOTS),
    ORIGIN + "/sitemap_index.xml": (200, {}, SITEMAP_INDEX),
    ORIGIN + "/sitemap-pages.xml": (200, {}, SITEMAP_PAGES),
    ORIGIN + "/llms.txt": (200, {}, LLMS),
    ORIGIN + "/pricing/": (200, {}, PRICING),
    ORIGIN + "/en/docs/getting-started": (200, {}, SIMPLE % ("en", "Docs", "Getting started")),
    ORIGIN + "/en/blog/hello-world": (200, {}, SIMPLE % ("en", "Blog", "Hello world")),
    ORIGIN + "/en/vs/rival": (200, {}, SIMPLE % ("en", "Acme vs Rival", "Acme vs Rival")),
}


class FakeWeb:
    """sc.http_fetch 桩:{url: (status, headers, body)};未登记的 URL 回 404(含 /sitemap.xml、/llms-full.txt)。"""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url, timeout=10.0, method="GET"):
        self.calls.append(url)
        status, headers, body = self.routes.get(url, (404, {}, "not found"))
        return {"status": status, "final_url": url, "chain": [], "headers": headers, "body": body,
                "body_bytes": body.encode("utf-8"), "meta": {}}


@contextlib.contextmanager
def patched_web(routes):
    fake = FakeWeb(routes)
    orig = (sc.http_fetch, sc._sleep, sc.dns_resolve)
    sc.http_fetch, sc._sleep = fake, (lambda t: None)
    sc.dns_resolve = lambda host: ["93.184.216.34"]
    sc._ssrf_cache.clear()
    try:
        yield fake
    finally:
        sc.http_fetch, sc._sleep, sc.dns_resolve = orig
        sc._ssrf_cache.clear()


def make_next_repo(root):
    files = {
        "package.json": json.dumps({"name": "acme-web", "description": "Acme Cloud website",
                                    "homepage": "https://acme.example",
                                    "dependencies": {"next": "15.0.0", "react": "19.0.0"}}),
        "app/page.tsx": "export default function Home(){return <main>Home</main>}\n",
        "app/pricing/page.tsx": "export default function P(){return null}\n",
        "app/blog/[slug]/page.tsx": "export default function B(){return null}\n",
        "app/sitemap.ts": "export default function sitemap(){return []}\n",
        "app/layout.tsx": "<Script src='https://www.googletagmanager.com/gtag/js?id=G-ABC1234XYZ'/>\n"
                          "gtag('config', 'G-ABC1234XYZ');\n",
        "README.md": "# Acme Web\n\nMarketing site for Acme Cloud.\n",
        "node_modules/x/page.tsx": "posthog.init()\n",       # 必须跳过
    }
    for rel, txt in files.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(txt)


def facts_by_key(rep):
    out = {}
    for f in rep["facts"]:
        out.setdefault(f["key"], []).append(f)
    return out


class SiteScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patched_web(FAKE_SITE) as fake:
            cls.rep = ps.build_report(ORIGIN + "/", None, max_pages=20, max_urls=50000, wayback=False,
                                      cwd=tempfile.mkdtemp())
            cls.calls = list(fake.calls)

    def test_top_level_contract(self):
        r = self.rep
        self.assertEqual(set(r), {"schema", "generated_at", "site", "repo", "site_scan", "repo_scan",
                                  "existing_context", "errors", "facts", "signals"})
        self.assertEqual(r["schema"], 1)
        self.assertIsNone(r["repo_scan"])
        self.assertEqual(r["existing_context"], [])
        self.assertTrue(r["generated_at"].endswith("+00:00"))
        self.assertEqual(set(r["signals"]), {"site_live", "homepage_noindex", "robots_block_all", "url_count",
                                             "first_seen", "repo_public_routes", "analytics", "has_llms_txt",
                                             "has_jsonld", "jsonld_types", "hreflang_locales", "same_as"})
        self.assertEqual(set(r["site_scan"]), {"reachable", "homepage", "robots", "sitemap", "llms", "page_types",
                                               "locales", "samples", "first_seen"})

    def test_homepage_features(self):
        h = self.rep["site_scan"]["homepage"]
        self.assertEqual(h["status"], 200)
        self.assertEqual(h["og_site_name"], "Acme Cloud")
        self.assertEqual(h["h1"], ["Ship APIs faster"])
        self.assertEqual(h["h2"], ["Hosting", "Monitoring"])
        self.assertEqual(h["lang"], "en")
        self.assertEqual(h["hreflang_count"], 2)
        self.assertEqual(sorted(h["jsonld_types"]), ["Organization", "WebSite"])
        self.assertEqual(h["same_as"], ["https://github.com/acme", "https://x.com/acme"])
        self.assertEqual(h["ctas"], [{"text": "Sign up", "href": "https://acme.example/signup"}])
        self.assertFalse(h["noindex"])

    def test_robots_sitemap_llms(self):
        s = self.rep["site_scan"]
        self.assertEqual(s["robots"], {"status": 200, "disallow_all": False,
                                       "sitemaps": ["https://acme.example/sitemap_index.xml"]})
        self.assertEqual(s["sitemap"]["url_count"], 9)          # 10 条 loc 去掉 1 条重复
        self.assertFalse(s["sitemap"]["truncated"])
        self.assertIn("https://acme.example/sitemap-pages.xml", s["sitemap"]["sources"])
        self.assertEqual(s["llms"], {"llms_txt": True, "llms_full": False, "title": "Acme Cloud",
                                     "summary": "API hosting and monitoring for small teams.",
                                     "sections": {"Hosting": ["Deploy"], "Monitoring": ["Alerts"]}})

    def test_page_types_and_locales(self):
        s = self.rep["site_scan"]
        self.assertEqual(s["page_types"].get("pricing"), 3)
        self.assertEqual(s["page_types"].get("docs"), 2)
        self.assertEqual(s["page_types"].get("blog"), 2)
        self.assertEqual(s["page_types"].get("compare"), 1)
        self.assertEqual(s["page_types"].get("other"), 1)       # 首页 /
        self.assertEqual(s["locales"], {"en": 4, "es": 3})

    def test_samples(self):
        samples = {x["type"]: x for x in self.rep["site_scan"]["samples"]}
        self.assertEqual(samples["pricing"]["url"], "https://acme.example/pricing/")   # 无语言前缀优先
        self.assertIn("$9/mo", samples["pricing"]["prices"])
        self.assertEqual(samples["pricing"]["ctas"], [{"text": "Start free trial", "href": None}])
        self.assertEqual(samples["compare"]["url"], "https://acme.example/en/vs/rival")
        self.assertEqual(set(samples), {"pricing", "docs", "blog", "compare"})

    def test_facts(self):
        fk = facts_by_key(self.rep)
        allowed = {"product.name", "product.one_liner", "product.lines", "pricing.prices", "pricing.model",
                   "conversion.ctas", "conversion.buttons", "market.languages", "site.page_types", "site.url_count", "tech.framework",
                   "tech.rendering", "measurement.analytics", "entity.same_as", "history.first_seen",
                   "context.existing"}
        self.assertTrue(set(fk) <= allowed, set(fk) - allowed)
        for f in self.rep["facts"]:
            self.assertIn(f["kind"], ("fact", "inferred"))
            self.assertTrue(f["source"])
        name = fk["product.name"][0]
        self.assertEqual((name["value"], name["source"], name["kind"]), ("Acme Cloud", ORIGIN + "/", "fact"))
        ol = fk["product.one_liner"][0]
        self.assertEqual((ol["value"], ol["source"], ol["kind"]),
                         ("API hosting and monitoring for small teams.", ORIGIN + "/llms.txt", "fact"))
        lines = fk["product.lines"][0]
        self.assertEqual((lines["value"], lines["kind"]), (["Hosting", "Monitoring"], "inferred"))
        pr = fk["pricing.prices"][0]
        self.assertEqual((pr["source"], pr["kind"]), (ORIGIN + "/pricing/", "fact"))
        self.assertIn("$9/mo", pr["value"])
        self.assertEqual(fk["pricing.model"][0]["value"], "freemium")       # 有价 + 页面写 free
        self.assertEqual(fk["pricing.model"][0]["kind"], "inferred")
        self.assertEqual(fk["market.languages"][0]["value"], ["en", "es"])
        self.assertEqual(fk["entity.same_as"][0]["value"], ["https://github.com/acme", "https://x.com/acme"])
        self.assertEqual(fk["site.url_count"][0]["value"], "9")
        self.assertEqual(fk["site.url_count"][0]["kind"], "inferred")
        self.assertNotIn("history.first_seen", fk)                           # --no-wayback

    def test_signals(self):
        sg = self.rep["signals"]
        self.assertTrue(sg["site_live"])
        self.assertFalse(sg["homepage_noindex"])
        self.assertFalse(sg["robots_block_all"])
        self.assertEqual(sg["url_count"], 9)
        self.assertTrue(sg["has_llms_txt"])
        self.assertTrue(sg["has_jsonld"])
        self.assertEqual(sg["hreflang_locales"], ["en", "es"])
        self.assertIsNone(sg["repo_public_routes"])
        self.assertIsNone(sg["first_seen"])

    def test_no_wayback_call(self):
        self.assertFalse(any("archive.org" in u for u in self.calls))


class SiteEdgeTests(unittest.TestCase):
    def test_noindex_block_all_and_wayback(self):
        routes = {
            ORIGIN + "/": (200, {"X-Robots-Tag": "noindex"}, "<html><head><title>Acme</title></head></html>"),
            ORIGIN + "/robots.txt": (200, {}, "User-agent: *\nDisallow: /\n"),
            "https://archive.org/wayback/available?url=acme.example&timestamp=19960101": (
                200, {}, json.dumps({"archived_snapshots": {"closest": {"timestamp": "20190722082333"}}})),
        }
        with patched_web(routes):
            rep = ps.build_report(ORIGIN + "/", None, wayback=True, cwd=tempfile.mkdtemp())
        self.assertTrue(rep["signals"]["homepage_noindex"])
        self.assertTrue(rep["signals"]["robots_block_all"])
        self.assertEqual(rep["site_scan"]["first_seen"], "2019-07-22")
        fs = facts_by_key(rep)["history.first_seen"][0]
        self.assertEqual((fs["value"], fs["kind"]), ("2019-07-22", "inferred"))

    def test_network_down_no_crash(self):
        def boom(url, timeout=10.0, method="GET"):
            raise OSError("connection refused")
        with patched_web({}):
            sc.http_fetch = boom
            rep = ps.build_report(ORIGIN + "/", None, wayback=True, cwd=tempfile.mkdtemp())
        self.assertFalse(rep["site_scan"]["reachable"])
        self.assertFalse(rep["signals"]["site_live"])
        self.assertTrue(rep["errors"])

    def test_cli_usage_errors(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(ps.main([]), 2)
            self.assertEqual(ps.main(["--site", "ftp://x.example"]), 2)
            self.assertEqual(ps.main(["--repo", "/nonexistent/dir/xyz"]), 2)


class RepoScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp()
        make_next_repo(cls.dir)
        os.makedirs(os.path.join(cls.dir, ".agents"))
        with open(os.path.join(cls.dir, ".agents/product-marketing-context.md"), "w", encoding="utf-8") as fh:
            fh.write("# Product\n\n## Audience\nDevs\n")
        cls.rep = ps.build_report(None, cls.dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir, ignore_errors=True)

    def test_repo_fields(self):
        r = self.rep["repo_scan"]
        self.assertIsNone(self.rep["site_scan"])
        self.assertEqual(r["framework"], "next")
        self.assertEqual(r["rendering"], "ssr")
        self.assertEqual(sorted(r["routes"]), ["/", "/blog/[slug]", "/pricing"])
        self.assertEqual(r["route_count"], 3)
        self.assertEqual(r["seo_files"]["sitemap"], ["app/sitemap.ts"])
        self.assertIsNone(r["seo_files"]["robots"])
        self.assertIsNone(r["seo_files"]["llms"])
        self.assertIn("gtag", r["analytics"])
        self.assertIn("googletagmanager", r["analytics"])
        self.assertNotIn("posthog", r["analytics"])                 # node_modules 已跳过
        self.assertEqual(r["readme_summary"], "Marketing site for Acme Cloud.")
        self.assertEqual(r["package"], {"name": "acme-web", "description": "Acme Cloud website",
                                        "homepage": "https://acme.example"})

    def test_repo_facts_and_context(self):
        fk = facts_by_key(self.rep)
        fw = fk["tech.framework"][0]
        self.assertEqual((fw["value"], fw["source"], fw["kind"]), ("next", "package.json", "fact"))
        self.assertEqual(fk["tech.rendering"][0]["kind"], "inferred")
        an = fk["measurement.analytics"][0]
        self.assertEqual(an["source"], "app/layout.tsx")
        self.assertEqual(self.rep["signals"]["repo_public_routes"], 3)
        self.assertIsNone(self.rep["signals"]["site_live"])
        ec = self.rep["existing_context"]
        self.assertEqual(ec, [{"path": ".agents/product-marketing-context.md", "headings": ["Product", "Audience"],
                               "chars": len("# Product\n\n## Audience\nDevs\n")}])
        self.assertEqual(fk["context.existing"][0]["value"], [".agents/product-marketing-context.md"])

    def test_cli_out_file_and_md(self):
        out = os.path.join(self.dir, "out", "scan.json")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(ps.main(["--repo", self.dir, "--out", out, "--md"]), 0)
        with open(out, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["repo_scan"]["framework"], "next")
        self.assertIn("tech.framework", err.getvalue())
        self.assertIn("package.json", err.getvalue())



class RealRunRegressionTests(unittest.TestCase):
    """11-08 everyinfra.com 实跑发现的两个问题(修前红、修后绿):
    1. llms.txt 的 ## 标题多半是栏目名(What's new、Guides),产品线应取「Products」那一节的条目;
    2. 「免费开始」按钮链到 .../login?first_screen=register 是注册,不是登录;「登录」不算转化。"""

    def test_product_lines_from_products_section(self):
        body = ("# EveryInfra\n\n> Data APIs for AI agents.\n\n## What's new\n\n- [New: Bing data API](https://x/b): live\n\n"
                "## Guides\n\n- [Full API guide](https://x/g): all\n\n## Products\n\n- [EveryData](https://x/d): data\n"
                "- [EverySearch](https://x/s): search\n- [EverySolve](https://x/c): captcha\n")

        class F:
            def get(self, url, quiet_404=False):
                if url.endswith("/llms.txt"):
                    return {"status": 200, "body": body, "final_url": url}
                return {"status": 404, "body": ""}
        out, _h2, _src = ps.scan_llms(F(), "https://everyinfra.com")
        self.assertEqual(out["sections"]["Products"], ["EveryData", "EverySearch", "EverySolve"])

    def test_cta_kinds(self):
        self.assertEqual(ps.cta_kind("免费开始", "https://everyinfra.com/auth/logto/login?first_screen=register"), "注册")
        self.assertIsNone(ps.cta_kind("登录", "https://everyinfra.com/auth/logto/login?first_screen=sign_in"))
        self.assertIsNone(ps.cta_kind("快速开始", "https://everyinfra.com/docs#quickstart"))

    def test_product_lines_from_routes_not_home_h2(self):
        """第 3 批:Quillbill 测试站(brief 写明三条产品线 Invoicing / Time tracking / Client portal)没有 llms 产品段,
        旧版取首页 h2「Why freelancers pick Quillbill」当产品线;应按 /features/<x> 路由取。"""
        o = "https://quillbill.example"
        home = ('<!doctype html><html lang="en"><head><title>Quillbill</title></head><body><h1>Invoices for freelancers</h1>'
                '<h2>Why freelancers pick Quillbill</h2></body></html>')
        locs = "".join("<url><loc>%s%s</loc></url>" % (o, p) for p in
                       ("/", "/pricing/", "/features/invoicing/", "/features/time-tracking/", "/features/client-portal/", "/blog/"))
        routes = {o + "/": (200, {"content-type": "text/html"}, home),
                  o + "/sitemap.xml": (200, {"content-type": "application/xml"}, "<urlset>%s</urlset>" % locs)}
        with patched_web(routes):
            rep = ps.build_report(o + "/", None, max_pages=5, max_urls=1000, wayback=False, cwd=tempfile.mkdtemp())
        lines = facts_by_key(rep)["product.lines"][0]["value"]
        self.assertEqual(lines, ["Invoicing", "Time tracking", "Client portal"])

if __name__ == "__main__":
    unittest.main(verbosity=1)
