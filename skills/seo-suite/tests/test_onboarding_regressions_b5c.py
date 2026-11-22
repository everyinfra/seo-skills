#!/usr/bin/env python3
"""开局流程第 5 批修复后第 3 次试跑记下的回归,逐条单测(stdlib unittest,零外网;本机回环上起临时站)。

期望值的来源(不从实现反推):
- 试跑转录里的真实输入:产品上下文文件写「monthly subscription from $20/month」、站点首页写「from $22」,
  用户回「The site is right: the subscription is $22 a month … Everything else in that file is still right」;
  站点目录是 /shop/<x>、/gear/<x>、/brew-guides/<x>、/subscription/(没有 /products/);工作区旁 data/ 里有
  两期 GSC 网页导出 Pages_起_止.csv(上一期只有表头)和逐日 gsc-pages.csv;registry.json 末尾被追加了一行
  「# changed by someone else」;德语页 hreflang="en" 指向会 301 的旧地址、只靠 x-default 指回英语页;
  用户教的规则「对比文都要放一张价格对照表」(适用 brief、plan);check try 的判定行和用户原话印在同一行。
- 本轮修复清单写明的行为:对不上的地方两边都写、标「对不上」、进第 1 问;产品线从已有上下文文件取,取不到用
  sitemap 里有子页的一级目录当候选(标推测),超过上限照旧不当产品线;部分回答只再问没答到的必答项;
  registry 读不了按「已停用、等重新确认」处理并拒写;hreflang 指向跳转地址记硬失败并写出最终地址、x-default
  不算回指、补抓到不动点;方案带「按你的规则」一节;check try 判定行只印判定和网址;answer --confirm 之后提示
  原话只确认了这一环;start 时读 data/ 里的 GSC 导出。
站点、品牌都是合成的。
"""
import contextlib
import functools
import http.server
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from email.message import Message
from unittest import mock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)
import hreflang_cluster as hc  # noqa: E402
import product_scan  # noqa: E402

BLOCK_START = "===== 下面这块原样发给用户"
BLOCK_END = "===== 原样发给用户到这里为止"


def run(script, args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", env=env)


def block_of(out):
    a = out.rindex(BLOCK_START)
    return out[a:out.index(BLOCK_END, a)]


def q1_line(block):
    return next(ln for ln in block.splitlines() if ln.startswith("1. "))


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


P = '<!doctype html><html lang="en"><head><title>%s</title></head><body><h1>%s</h1><p>%s</p></body></html>'
HOME = ('<!doctype html><html lang="en"><head><title>Tidewater Roasters</title>'
        '<meta name="description" content="Small-batch coffee roasted to order."></head><body>'
        '<h1>Fresh coffee, roasted to order</h1>'
        '<p>Buy a bag, start a monthly subscription from $22, or grab a starter kit. Free US shipping on orders over $40.</p>'
        '<a href="/shop/">Shop</a> <a href="/subscription/">Subscribe</a></body></html>')
SITE_PAGES = {"shop/index.html": P % ("Shop", "Shop", "All coffees"),
              "shop/ethiopia/index.html": P % ("Ethiopia", "Ethiopia", "12 oz bag $24. Add to cart"),
              "shop/kenya/index.html": P % ("Kenya", "Kenya", "12 oz bag $26. Add to cart"),
              "subscription/index.html": P % ("Subscription", "Subscription", "One bag a month for $22/month"),
              "gear/index.html": P % ("Gear", "Gear", "Brewing gear"),
              "gear/starter-kit/index.html": P % ("Starter kit", "Starter kit", "Kit $45. Add to cart"),
              "brew-guides/index.html": P % ("Guides", "Guides", "How to brew"),
              "brew-guides/v60/index.html": P % ("V60", "V60", "Use 15 g of coffee"),
              "brew-guides/aeropress/index.html": P % ("AeroPress", "AeroPress", "Press slowly"),
              "about/index.html": P % ("About", "About", "We roast in small batches")}
PM_FILE = """# Product Marketing Context

**Document version:** v1
**Last updated:** 2026-11-01

## Product Overview
**One-liner:** Small-batch single-origin coffee, roasted to order and shipped across the US.
**What it does:** Customers buy single bags, start a monthly subscription, or pick up a pour-over starter kit.
**Business model:** Single 12 oz bags $18–$26; monthly subscription from $20/month (two bags $40/month); starter kit $45.
%(extra)s
## Target Audience
**Target companies:** n/a (B2C)

## Goals
**Conversion action:** Start a subscription
"""


def make_site(t, home=HOME, pages=None):
    root = os.path.realpath(tempfile.mkdtemp(prefix="b5c_site_"))
    t.addCleanup(shutil.rmtree, root, True)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=root))
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    files = dict({"index.html": home}, **(SITE_PAGES if pages is None else pages))
    paths = ["/"] + ["/" + k[:-len("index.html")] for k in files if k != "index.html"]
    files["robots.txt"] = "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % base
    files["sitemap.xml"] = ('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                            + "".join("<url><loc>%s%s</loc></url>" % (base, p) for p in paths) + "</urlset>")
    for rel, body in files.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    t.addCleanup(httpd.server_close)
    t.addCleanup(httpd.shutdown)
    return base


class Repo:
    """临时站点仓库:可选 .agents/product-marketing.md 和 data/ 下的 GSC 导出;cwd 是仓库根。"""

    def __init__(self, t, pm_extra=None, data=None):
        self.t = t
        self.dir = os.path.realpath(tempfile.mkdtemp(prefix="obb5c_"))
        t.addCleanup(shutil.rmtree, self.dir, True)
        self.ws = os.path.join(self.dir, "seo-ops")
        if pm_extra is not None:
            os.makedirs(os.path.join(self.dir, ".agents"))
            with open(os.path.join(self.dir, ".agents", "product-marketing.md"), "w", encoding="utf-8") as f:
                f.write(PM_FILE % {"extra": pm_extra})
        for name, text in (data or {}).items():
            os.makedirs(os.path.join(self.dir, "data"), exist_ok=True)
            with open(os.path.join(self.dir, "data", name), "w", encoding="utf-8") as f:
                f.write(text)

    def ob(self, *a):
        return run("onboard.py", list(a) + ["--ws", self.ws] if a and a[0] != "start" else list(a), self.dir)

    def start(self, site):
        r = run("onboard.py", ["start", "--site", site, "--repo", ".", "--allow-local", "--no-wayback",
                               "--max-pages", "12"], self.dir)
        self.t.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r.stdout

    def profile(self):
        with open(os.path.join(self.ws, "context", "profile.json"), encoding="utf-8") as f:
            return json.load(f)


# ---------------------------------------------------------------------------
# S1 已有上下文文件和站点对不上的地方由脚本印出来;产品线不再因为目录名不是 /products/ 就成必答
# ---------------------------------------------------------------------------

class ContextConflictTests(unittest.TestCase):
    def setUp(self):
        self.site = make_site(self)
        self.repo = Repo(self, pm_extra="")
        self.out = self.repo.start(self.site)
        self.block = block_of(self.out)

    def test_conflict_shows_both_values_and_sources(self):
        """文件 $20、站点 $22:那一块里两个值、两个出处都在,标「对不上」。"""
        self.assertIn("对不上", self.block)
        self.assertIn("$20/month", self.block)
        self.assertIn("$22", self.block)
        self.assertIn(".agents/product-marketing.md", self.block)
        self.assertIn(self.site + "/", self.block)

    def test_conflict_goes_into_first_question(self):
        """用户一次回答就能定:第 1 问里点名两个订阅价,问哪个对。"""
        q = q1_line(self.block)
        self.assertIn("$20", q)
        self.assertIn("$22", q)
        self.assertRegex(q, r"subscription")
        self.assertIn("哪个对", q)

    def test_product_lines_not_required_when_sitemap_has_sections(self):
        """站点目录是 /shop/<x>、/gear/<x>:有子页的一级目录当候选(推测),不再「没读到可靠的产品线」必答。"""
        self.assertNotIn("没读到可靠的产品线", self.block)
        line = next(ln for ln in self.block.splitlines() if ln.startswith("- 产品线:"))
        self.assertIn("Shop", line)
        self.assertIn("Gear", line)
        self.assertIn("推测", line)
        self.assertNotIn("About", line)                 # 只有一页的目录不算

    def test_correction_only_answer_does_not_reask_merged_question(self):
        """用户纠正了订阅价、其余没否认:不带 --confirm 的 answer 不把第 1 问整条再打一遍。"""
        quote = ("The site is right: the subscription is $22 a month, the marketing file is out of date there. "
                 "Everything else in that file is still right.")
        r = self.repo.ob("answer", "--ring", "1", "--correct",
                         "pricing.model=Single 12 oz bags $18–$26; monthly subscription $22/month; starter kit $45",
                         "--quote", quote)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("上面这份产品理解", r.stdout)
        self.assertNotIn(BLOCK_START, r.stdout)
        r = self.repo.ob("answer", "--ring", "1", "--quote", quote, "--confirm")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)

    def test_confirm_prints_quote_only_confirms_this_ring(self):
        r = self.repo.ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--quote",
                         "Go with your best guess and move on to the next part.", "--confirm")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        tail = r.stdout[r.stdout.index("下一环"):]
        self.assertIn("只确认了", tail)
        self.assertIn("第 1 环", tail)
        self.assertIn("新的回话", tail)


class ContextLinesTests(unittest.TestCase):
    def test_lines_read_from_context_file(self):
        """文件里写了产品清单:取来当草稿,出处写这份文件。"""
        site = make_site(self, pages={"about/index.html": P % ("About", "About", "x")})
        repo = Repo(self, pm_extra="**Products:** Single-origin bags; Monthly subscription; Starter kit\n")
        block = block_of(repo.start(site))
        line = next(ln for ln in block.splitlines() if ln.startswith("- 产品线:"))
        self.assertIn("Monthly subscription", line)
        self.assertIn(".agents/product-marketing.md", line)
        self.assertNotIn("没读到可靠的产品线", block)

    def test_too_many_sections_are_not_product_lines(self):
        """有子页的一级目录超过 LINES_MAX:照旧不当产品线。"""
        n = product_scan.LINES_MAX + 1
        paths = ["/dir%d/item/" % i for i in range(n)]
        self.assertEqual(len(product_scan.section_lines(paths)), n)
        site_scan = {"homepage": {"status": 200, "url": "https://x.example/", "final_url": "https://x.example/",
                                  "title": "X", "h2": [], "prices": [], "ctas": []}, "samples": [],
                     "sitemap": {"url_count": n, "sources": ["https://x.example/sitemap.xml"], "truncated": False}, "llms": {}, "page_types": {},
                     "locales": {}, "robots": {"status": 200, "disallow_all": False, "sitemaps": []}}
        facts = product_scan.build_facts(site_scan, {"pool_paths": paths, "pool_src": "https://x.example/sitemap.xml",
                                                     "home_extra": {}}, None, [])
        f = next(x for x in facts if x["key"] == "product.lines")
        self.assertIsNone(f["value"])

    def test_partial_answer_reasks_only_missing_required_part(self):
        """产品线确实读不到时:用户纠正了收费方式,只再问产品线,不再问「上面这份产品理解对吗」。"""
        site = make_site(self, pages={"about/index.html": P % ("About", "About", "x")})
        repo = Repo(self, pm_extra="")
        out = repo.start(site)
        self.assertIn("没读到可靠的产品线", block_of(out))
        r = repo.ob("answer", "--ring", "1", "--correct", "pricing.model=Monthly subscription $22/month",
                    "--quote", "The subscription is $22 a month now, the rest of the file is right.")
        self.assertEqual(r.returncode, 0, r.stderr)
        blk = block_of(r.stdout)
        qs = [ln for ln in blk.splitlines() if re.match(r"^\d+\. ", ln)]
        self.assertEqual(len(qs), 1, blk)
        self.assertIn("产品线", qs[0])
        self.assertNotIn("上面这份产品理解", qs[0])


class GscExportAtStartTests(unittest.TestCase):
    def test_start_reads_period_exports_into_metrics(self):
        site = make_site(self)
        cur = ("Top pages,Clicks,Impressions,CTR,Position\n%(b)s/,6,210,2.86%%,18.4\n%(b)s/shop/kenya/,3,96,3.12%%,24.1\n"
               "%(b)s/subscription/,2,64,3.12%%,27.5\n" % {"b": site})
        repo = Repo(self, data={"Pages_2026-09-13_2026-10-10.csv": "Top pages,Clicks,Impressions,CTR,Position\n",
                                "Pages_2026-10-11_2026-11-07.csv": cur})
        block = block_of(repo.start(site))
        self.assertNotIn("没有 GSC 数据", block)
        m = repo.profile()["metrics"]
        self.assertEqual(m.get("gsc_clicks_28d"), 11)
        self.assertEqual(m.get("gsc_impressions_28d"), 370)
        self.assertEqual(m.get("gsc_clicks_prev_28d"), 0)
        src = repo.profile()["metric_sources"]["gsc_clicks_28d"]
        self.assertIn("Pages_2026-10-11_2026-11-07.csv", src)

    def test_start_reads_daily_export_when_28_days_covered(self):
        site = make_site(self)
        import datetime as dt
        rows = ["page,date,clicks,impressions"]
        d0 = dt.date(2026, 10, 1)
        for i in range(28):
            rows.append("%s/,%s,2,30" % (site, (d0 + dt.timedelta(i)).isoformat()))
        repo = Repo(self, data={"gsc-pages.csv": "\n".join(rows) + "\n"})
        repo.start(site)
        m = repo.profile()["metrics"]
        self.assertEqual(m.get("gsc_clicks_28d"), 56)
        self.assertEqual(m.get("gsc_impressions_28d"), 840)
        self.assertIn("gsc-pages.csv", repo.profile()["metric_sources"]["gsc_clicks_28d"])


# ---------------------------------------------------------------------------
# S3 registry.json 读不了不能当空表
# ---------------------------------------------------------------------------

CHECK_PAGES = {"/item/a/": "<html><body><h1>A</h1><button>Add to cart</button></body></html>",
               "/item/b/": "<html><body><h1>B</h1><button>Add to cart</button></body></html>",
               "/about/": "<html><body><h1>About</h1></body></html>"}


class CheckWs(unittest.TestCase):
    """临时工作区:一条禁用规则 + 一个试跑过、启用了的自定义检查,检查的页面挂在 127.0.0.1。"""

    def setUp(self):
        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                body = CHECK_PAGES.get(self.path)
                self.send_response(200 if body else 404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write((body or "nope").encode("utf-8"))

            def log_message(self, *a):
                pass
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        self.urls = ["http://127.0.0.1:%d%s" % (srv.server_address[1], p) for p in CHECK_PAGES]
        self.dir = os.path.realpath(tempfile.mkdtemp(prefix="b5c_reg_"))
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.ws = os.path.join(self.dir, "seo-ops")
        os.makedirs(self.ws)
        with open(os.path.join(self.ws, "project.yaml"), "w", encoding="utf-8") as f:
            f.write("site: https://shop.example\nmarket: en\n")
        self.teach("rule", "add", "--quote", "别再建议我们去做 Reddit 外链了,我们不做", "--deny", "reddit")
        self.teach("check", "new", "cart-button", "--desc", "每个商品页都要有加购按钮", "--pattern", "Add to cart",
                   "--match", "/item/", "--quote", "加一个检查:每个商品页都要有加购按钮")
        self.try_()
        self.teach("check", "enable", "cart-button", "--quote", "结果对,启用吧。")
        self.reg = os.path.join(self.ws, "playbook", "checks", "registry.json")

    def teach(self, *a, ok=True):
        r = run("teach.py", list(a), self.dir)
        if ok:
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r

    def try_(self):
        args = ["check", "try", "cart-button", "--allow-local"]
        for u in self.urls:
            args += ["--url", u]
        return self.teach(*args)


class RegistryUnreadableTests(CheckWs):
    def setUp(self):
        super().setUp()
        with open(self.reg, "a", encoding="utf-8") as f:
            f.write("# changed by someone else\n")
        with open(self.reg, "rb") as f:
            self.bytes = f.read()

    def test_check_list_names_check_as_disabled(self):
        out = self.teach("check", "list").stdout
        line = next(ln for ln in out.splitlines() if "cart-button" in ln)
        self.assertIn("已停用", line)
        self.assertIn("registry.json 读不了", line)
        self.assertNotIn("草稿", line)

    def test_context_names_check(self):
        out = run("playbook.py", ["context", "--ws", self.ws], self.dir).stdout
        line = next((ln for ln in out.splitlines() if "cart-button" in ln), "")
        self.assertIn("已停用", line)
        self.assertIn("registry.json 读不了", line)

    def test_weekly_names_check(self):
        r = run("project.py", ["ops", "weekly", "--no-net", "--date", "2030-01-07", "--ws", self.ws], self.dir)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(os.path.join(self.ws, "runs", "2030-01-07", "agenda.md"), encoding="utf-8") as f:
            sec = f.read().split("## 2.6")[1].split("\n## ")[0]
        line = next((ln for ln in sec.splitlines() if "cart-button" in ln), "")
        self.assertIn("registry.json 读不了", line)
        self.assertIn("已停用", line)

    def test_writes_refused_and_file_not_overwritten(self):
        r = self.teach("check", "enable", "cart-button", "--quote", "结果对,启用吧。", ok=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("teach.py check enable cart-button --quote", r.stderr + r.stdout)
        r = self.teach("check", "new", "other", "--desc", "每页都要有标题", "--quote", "加一个检查:每页都要有标题",
                       ok=False)
        self.assertNotEqual(r.returncode, 0)
        with open(self.reg, "rb") as f:
            self.assertEqual(f.read(), self.bytes)

    def test_missing_registry_is_still_empty_table(self):
        os.remove(self.reg)
        out = self.teach("check", "list").stdout
        line = next(ln for ln in out.splitlines() if "cart-button" in ln)
        self.assertIn("草稿", line)


# ---------------------------------------------------------------------------
# S6 check try:判定行只印判定和网址
# ---------------------------------------------------------------------------

class CheckTryOutputTests(CheckWs):
    def test_verdict_line_has_no_findings(self):
        out = self.try_().stdout
        lines = out.splitlines()
        about = next(i for i, ln in enumerate(lines) if ln.strip().endswith("/about/"))
        self.assertRegex(lines[about].strip(), r"^\[✗ fail\] http://127\.0\.0\.1:\d+/about/$")
        self.assertIn("加购按钮", lines[about + 1])
        self.assertTrue(lines[about + 1].startswith("      "))
        ok = next(ln for ln in lines if ln.strip().endswith("/item/a/"))
        self.assertRegex(ok.strip(), r"^\[✓ pass\] http://")


# ---------------------------------------------------------------------------
# S4 hreflang_cluster 漏报断簇
# ---------------------------------------------------------------------------

def hl_page(alts):
    links = "".join('<link rel="alternate" hreflang="%s" href="%s">' % a for a in alts)
    return ("<html><head>%s</head><body>x</body></html>" % links).encode()


def fake_fetch(pages, redirects):
    def f(url, timeout=12.0, max_bytes=3_000_000, follow=True):
        m = Message()
        m["Content-Type"] = "text/html; charset=utf-8"
        hops = 0
        while url in redirects:
            if not follow:
                m["Location"] = redirects[url]
                return 301, m, url, b""
            url = redirects[url]
            hops += 1
            if hops > 5:
                break
        if url in pages:
            return 200, m, url, pages[url]
        return 404, m, url, b""
    return f


class HreflangClusterTests(unittest.TestCase):
    EN, DE, OLD = "https://g.example/articles/guide/", "https://g.example/de/artikel/ratgeber/", "https://g.example/blog/guide/"

    def run_main(self, pages, redirects, urls, *extra):
        out = io.StringIO()
        with mock.patch.object(hc, "fetch", side_effect=fake_fetch(pages, redirects)), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            rc = hc.main([*urls, "--no-sitemap", *extra])
        return rc, out.getvalue()

    def broken(self):
        return ({self.EN: hl_page([("en", self.EN), ("de", self.DE), ("x-default", self.EN)]),
                 self.DE: hl_page([("de", self.DE), ("en", self.OLD), ("x-default", self.EN)])},
                {self.OLD: self.EN})

    def test_alternate_pointing_at_redirect_is_hard_failure(self):
        pages, red = self.broken()
        for entry in (self.DE, self.EN):
            rc, out = self.run_main(pages, red, [entry])
            self.assertEqual(rc, 1, out)
            self.assertIn("hreflang 指向跳转地址,应写 %s" % self.EN, out)
            self.assertNotIn("簇校验通过", out)

    def test_x_default_does_not_count_as_return_link(self):
        """德语页只用 x-default 指回英语页:英语页那一对的回指不成立(就算 en 指向的不是跳转地址)。"""
        pages = {self.EN: hl_page([("en", self.EN), ("de", self.DE)]),
                 self.DE: hl_page([("de", self.DE), ("x-default", self.EN)])}
        rc, out = self.run_main(pages, {}, [self.EN, self.DE])
        self.assertEqual(rc, 1, out)
        self.assertIn("x-default", out.split("回链缺失")[1])

    def test_closure_fetches_alternates_of_fetched_pages(self):
        """从英语页入口:英→德,德→法(英语页没列法语),法不指回德:要报出来。"""
        fr = "https://g.example/fr/guide/"
        pages = {self.EN: hl_page([("en", self.EN), ("de", self.DE)]),
                 self.DE: hl_page([("de", self.DE), ("en", self.EN), ("fr", fr)]),
                 fr: hl_page([("fr", fr)])}
        rc, out = self.run_main(pages, {}, [self.EN])
        self.assertEqual(rc, 1, out)
        self.assertIn(fr, out)

    def test_entry_redirect_is_followed_and_reported(self):
        pages = {self.EN: hl_page([("en", self.EN)])}
        rc, out = self.run_main(pages, {self.OLD: self.EN}, [self.OLD])
        self.assertIn("跳到了 %s" % self.EN, out)

    def test_closure_is_bounded(self):
        urls = ["https://g.example/l%d/" % i for i in range(30)]
        pages = {u: hl_page([("en", urls[0])] + [("de-%s" % c, v) for c, v in zip(
            ["AT", "CH", "DE", "LU", "BE", "IT"] * 6, urls[i + 1:i + 2])]) for i, u in enumerate(urls)}
        rc, out = self.run_main(pages, {}, [urls[0]], "--max-extra", "5")
        self.assertIn("--max-extra=5", out)


# ---------------------------------------------------------------------------
# S5 方案带上用户教的非禁用类规则
# ---------------------------------------------------------------------------

RULE_Q = "以后我们的对比文都要放一张价格对照表"


class PlanRulesTests(unittest.TestCase):
    def test_plan_outputs_carry_user_rules(self):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="b5c_plan_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        scan = {"schema": 1, "site": "https://acme.example",
                "signals": {"site_live": True, "robots_block_all": False, "homepage_noindex": False, "url_count": 1200,
                            "first_seen": "2025-06-01", "has_llms_txt": True},
                "site_scan": {"page_types": {"pricing": 1, "docs": 30, "blog": 40, "compare": 2}},
                "facts": [{"key": "product.name", "value": "Acme", "source": "https://acme.example/", "kind": "fact"},
                          {"key": "product.lines", "value": ["Invoices", "Expenses"], "source": "llms.txt",
                           "kind": "inferred"},
                          {"key": "market.languages", "value": ["en"], "source": "hreflang", "kind": "fact"}],
                "errors": []}
        with open(os.path.join(tmp, "scan.json"), "w", encoding="utf-8") as f:
            json.dump(scan, f)
        ws = os.path.join(tmp, "seo-ops")

        def ob(*a):
            r = run("onboard.py", list(a) + ["--ws", ws] if a[0] != "start" else list(a), tmp)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        ob("start", "--site", "https://acme.example", "--scan", "scan.json", "--market", "en")
        ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册", "--set", "customers=小团队",
           "--set", "main_line=Invoices", "--quote", "都对,要注册,客户是小团队,先做发票", "--confirm")
        ob("skip", "--quote", "跳过,直接出方案")
        r = run("teach.py", ["rule", "add", "--quote", RULE_Q, "--no-deny", "--applies", "brief,plan", "--ws", ws], tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run("plan.py", ["build", "--ws", ws], tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        d = os.path.join(ws, "plan")
        with open(os.path.join(d, "plan.json"), encoding="utf-8") as f:
            plan = json.load(f)
        self.assertIn(RULE_Q, json.dumps(plan.get("user_rules"), ensure_ascii=False))
        for name, head in (("plan.md", "## 按你的规则"), ("roadmap.md", "## 按你的规则"),
                           ("strategy-book.zh.md", "## 按你的规则"), ("strategy-book.en.md", "## Your rules")):
            with open(os.path.join(d, name), encoding="utf-8") as f:
                text = f.read()
            self.assertIn(head, text, name)
            self.assertIn(RULE_Q, text.split(head)[1], name)


if __name__ == "__main__":
    unittest.main()
