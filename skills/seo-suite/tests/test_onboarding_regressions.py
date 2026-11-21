#!/usr/bin/env python3
"""开局流程(onboard / product_scan / plan / loops / project)的一批回归(stdlib unittest,零外网)。

期望值的来源(不从实现反推):
- 行为评测里记下的真实失败输入:只给仓库时阶段候选是整数列表(第 1 环第一屏直接崩);手写或旧版档案缺 rings / stage;
  plan.json 里的 weeks 被写成 "1"、"1-2";首页 h2 被当成产品线;工具路由池被当成产品线;定价被压成一个枚举词;
  模拟用户回「Go with your best guess…」「Carry on.」之后被当成跳过;「X 最重要」被记成把产品线改成只剩 X;
  只剩 1 问时没编号;第一屏改写掉出处。
- 行为要求(本批修复清单逐条写明的行为):原文价格和计费方式带出处;产品线拿不准标「未知」、第 1 环问;
  第 1 环最多 3 问,已有 .agents/product-marketing.md 覆盖的不再问;show 复述已确认和刚纠正的值;
  方案读第 1 环的目标、按已确认的单语市场不出多语言建议、写进量到的掉量页型和数字;skip 只认明确的跳过;
  --quote 太短拒绝(短确认词在没有纠正时照收);档案被手改要报警并重新确认;本机站点不查外部历史服务;
  project.py run triage 认 --allow-local。
- tools/testsites/lifecycle_sites.py 造的合成站(徒步内容站两期点击 1,850 → 1,450,掉量集中在评测、对比、best-of 页)。
"""
import contextlib
import datetime as dt
import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
# 扫描文件造的站没有真站可体检:第 4 环走逃生口(站点已上线时确认第 4 环要体检记录)
NO_AUDIT = ["--no-audit", "测试用扫描文件造的站,没有真站可体检"]
ROOT = os.path.dirname(os.path.dirname(BASE))
SITES = os.path.join(ROOT, "tools", "testsites", "lifecycle_sites.py")
sys.path.insert(0, SCRIPTS)

import site_crawl as sc  # noqa: E402
import product_scan as ps  # noqa: E402

TODAY = dt.datetime.now(dt.timezone.utc).date()
BLOCK_START = "===== 下面这块原样发给用户"
BLOCK_END = "===== 原样发给用户到这里为止"
QLINE = re.compile(r"^\s*\d+[.、]")


def run(script, args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", env=env)


def user_block(screen):
    """show 输出里给用户原样贴的那一块。"""
    a = screen.index(BLOCK_START)
    b = screen.index(BLOCK_END, a)
    return screen[screen.index("\n", a) + 1:b]


def numbered_questions(block):
    return [ln for ln in block.splitlines() if QLINE.match(ln) and ("?" in ln or "？" in ln)]


class FakeWeb:
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url, timeout=10.0, method="GET"):
        self.calls.append(url)
        status, headers, body = self.routes.get(url, (404, {}, "not found"))
        return {"status": status, "final_url": url, "chain": [], "headers": headers, "body": body,
                "body_bytes": body.encode("utf-8"), "meta": {}}


@contextlib.contextmanager
def patched_web(routes, ip="93.184.216.34", allow_local=False):
    fake = FakeWeb(routes)
    orig = (sc.http_fetch, sc._sleep, sc.dns_resolve, sc.ALLOW_LOCAL)
    sc.http_fetch, sc._sleep = fake, (lambda t: None)
    sc.dns_resolve = lambda host: [ip]
    sc.ALLOW_LOCAL = allow_local
    sc._ssrf_cache.clear()
    try:
        yield fake
    finally:
        sc.http_fetch, sc._sleep, sc.dns_resolve, sc.ALLOW_LOCAL = orig
        sc._ssrf_cache.clear()


def site_routes(origin, home, extra=None, sitemap_paths=()):
    html = {"content-type": "text/html"}
    r = {origin + "/": (200, html, home)}
    if sitemap_paths:
        locs = "".join("<url><loc>%s%s</loc></url>" % (origin, p) for p in sitemap_paths)
        r[origin + "/sitemap.xml"] = (200, {"content-type": "application/xml"}, "<urlset>%s</urlset>" % locs)
    for p, body in (extra or {}).items():
        r[origin + p] = (200, html, body)
    return r


def scan_report(origin, routes, wayback=False, ip="93.184.216.34", allow_local=False):
    with patched_web(routes, ip, allow_local) as fake:
        rep = ps.build_report(origin + "/", None, max_pages=10, max_urls=1000, wayback=wayback, cwd=tempfile.mkdtemp())
    return rep, fake.calls


def fact(rep, key):
    return next((f for f in rep["facts"] if f["key"] == key), None)


HOME = ('<!doctype html><html lang="en"><head><title>Acme API</title></head><body><h1>Data APIs</h1>'
        '<h2>Why teams pick Acme</h2><h2>Roasted to order</h2><a href="/pricing/">Pricing</a></body></html>')


# ---------------------------------------------------------------------------
# 1. 定价:原文价格、档位、计费方式,带出处
# ---------------------------------------------------------------------------

class PricingFactsTests(unittest.TestCase):
    O = "https://acme.example"

    def test_usage_based_pricing_keeps_page_text_and_billing_modes(self):
        page = ('<!doctype html><html><head><title>Pricing</title></head><body><h1>Pricing</h1>'
                '<h2>Pay as you go</h2><p>Top up from $10. Requests cost $0.50 per 1,000.</p>'
                '<h2>Credit packs</h2><p>Buy 100,000 credits for $40; credits never expire.</p>'
                '<p>Every account gets 1,000 free requests each month.</p></body></html>')
        rep, _ = scan_report(self.O, site_routes(self.O, HOME, {"/pricing/": page}, ("/", "/pricing/")))
        f = fact(rep, "pricing.model")
        self.assertIsNotNone(f)
        v = str(f["value"])
        for s in ("Top up from $10", "$0.50 per 1,000", "$40"):
            self.assertIn(s, v)
        self.assertEqual(f["kind"], "fact")
        self.assertTrue(f["source"].endswith("/pricing/"), f["source"])
        modes = " ".join(f.get("billing") or [])
        for m in ("预充值", "按量", "额度包", "免费额度"):
            self.assertIn(m, modes)
        self.assertIn(f.get("enum"), ("freemium", "paid", "contact", "free", "unknown"))

    def test_tier_names_and_trial_kept(self):
        page = ('<!doctype html><html><head><title>Pricing</title></head><body><h1>Simple pricing</h1>'
                '<p>Free: up to 3 clients, unlimited invoices.</p>'
                '<p>Pro: $12 per month or $120 per year, unlimited clients.</p>'
                '<p>Studio: $29 per seat per month for teams of 2 to 10.</p>'
                '<p>Start a 14-day free trial of Pro, no credit card.</p></body></html>')
        rep, _ = scan_report(self.O, site_routes(self.O, HOME, {"/pricing/": page}, ("/", "/pricing/")))
        v = str(fact(rep, "pricing.model")["value"])
        for s in ("Pro: $12 per month", "Studio: $29 per seat per month", "14-day free trial"):
            self.assertIn(s, v)
        modes = " ".join(fact(rep, "pricing.model").get("billing") or [])
        self.assertIn("订阅", modes)
        self.assertIn("试用", modes)


# ---------------------------------------------------------------------------
# 2. 产品线:不拿首页 h2 兜底;路由池是条目清单时标未知
# ---------------------------------------------------------------------------

class ProductLinesTests(unittest.TestCase):
    O = "https://acme.example"

    def test_home_h2_is_not_product_lines(self):
        rep, _ = scan_report(self.O, site_routes(self.O, HOME))
        f = fact(rep, "product.lines")
        self.assertIsNotNone(f, "产品线要留一条「未知」,第 1 环才会问")
        self.assertIsNone(f["value"])
        self.assertEqual(f["kind"], "unknown")
        self.assertNotIn("Roasted to order", json.dumps(rep["facts"], ensure_ascii=False).split("product.lines")[-1][:200])

    def test_large_route_pool_is_unknown_not_lines(self):
        paths = ["/"] + ["/tools/tool-%02d/" % i for i in range(20)]
        rep, _ = scan_report(self.O, site_routes(self.O, HOME, sitemap_paths=paths))
        f = fact(rep, "product.lines")
        self.assertIsNone(f["value"])
        self.assertEqual(f["kind"], "unknown")
        self.assertIn("20", f.get("note", ""))

    def test_inferred_route_lines_asked_in_ring1(self):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="obreg_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        scan = {"schema": 1, "site": self.O, "signals": {"site_live": True, "url_count": 30, "first_seen": "2024-01-01"},
                "facts": [{"key": "product.name", "value": "Acme", "source": self.O + "/", "kind": "fact"},
                          {"key": "product.lines", "value": ["Invoicing", "Time tracking"],
                           "source": self.O + "/sitemap.xml", "kind": "inferred"}], "errors": []}
        with open(os.path.join(tmp, "scan.json"), "w", encoding="utf-8") as f:
            json.dump(scan, f)
        r = run("onboard.py", ["start", "--site", self.O, "--scan", "scan.json"], tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        qs = numbered_questions(user_block(r.stdout))
        self.assertTrue(any("产品线" in q and ("推" in q or "对吗" in q) for q in qs), qs)


# ---------------------------------------------------------------------------
# 15. 本机站点不查 Wayback
# ---------------------------------------------------------------------------

class LocalNoWaybackTests(unittest.TestCase):
    def test_loopback_site_skips_wayback(self):
        for o in ("http://127.0.0.1:8765", "http://localhost:8765"):
            rep, calls = scan_report(o, site_routes(o, HOME), wayback=True, ip="127.0.0.1", allow_local=True)
            self.assertFalse([c for c in calls if "archive.org" in c], calls)
            self.assertTrue(rep["site_scan"]["reachable"])

    def test_private_host_detection(self):
        for h in ("127.0.0.1", "localhost", "dev.localhost", "10.0.0.5", "192.168.1.20", "172.16.3.4", "::1"):
            self.assertTrue(ps.is_local_host(h), h)
        for h in ("example.com", "93.184.216.34"):
            self.assertFalse(ps.is_local_host(h), h)


# ---------------------------------------------------------------------------
# onboard 工作区夹具
# ---------------------------------------------------------------------------

def base_scan(lines=("Invoicing", "Time tracking", "Client portal"), signals=None, extra=()):
    sig = {"site_live": True, "robots_block_all": False, "homepage_noindex": False, "url_count": 120,
           "first_seen": "2024-03-01", "has_llms_txt": True}
    sig.update(signals or {})
    facts = [{"key": "product.name", "value": "Acme", "source": "https://acme.example/", "kind": "fact"},
             {"key": "product.one_liner", "value": "Invoices for freelancers", "source": "https://acme.example/", "kind": "fact"},
             {"key": "conversion.ctas", "value": ["注册"], "source": "https://acme.example/", "kind": "inferred"},
             {"key": "market.languages", "value": ["en"], "source": "https://acme.example/", "kind": "fact"}]
    if lines is not None:
        facts.append({"key": "product.lines", "value": list(lines), "source": "https://acme.example/llms.txt", "kind": "fact"})
    return {"schema": 1, "site": "https://acme.example", "signals": sig,
            "site_scan": {"page_types": {"pricing": 1, "blog": 10}}, "facts": facts + list(extra), "errors": []}


class Ws:
    def __init__(self, t, scan=None, start_args=("--site", "https://acme.example"), pmm=None, metrics=None):
        self.t = t
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="obreg_"))
        t.addCleanup(shutil.rmtree, self.tmp, True)
        self.ws = os.path.join(self.tmp, "seo-ops")
        if pmm:
            os.makedirs(os.path.join(self.tmp, ".agents"))
            with open(os.path.join(self.tmp, ".agents", "product-marketing.md"), "w", encoding="utf-8") as f:
                f.write(pmm)
        with open(os.path.join(self.tmp, "scan.json"), "w", encoding="utf-8") as f:
            json.dump(scan or base_scan(), f, ensure_ascii=False)
        self.start = self.ok(self.ob("start", *start_args, "--scan", "scan.json", *(("--repo", ".") if pmm else ())))
        if metrics:
            self.ok(self.ob("metric", *sum((["--set", "%s=%s" % kv] for kv in metrics.items()), []), "--source", "测试"))

    def ok(self, r):
        self.t.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.t.assertNotIn("Traceback", r.stderr)
        return r

    def ob(self, *a):
        return run("onboard.py", list(a), self.tmp)

    def prof(self):
        with open(os.path.join(self.ws, "context", "profile.json"), encoding="utf-8") as f:
            return json.load(f)

    def write_prof(self, prof):
        with open(os.path.join(self.ws, "context", "profile.json"), "w", encoding="utf-8") as f:
            json.dump(prof, f, ensure_ascii=False, indent=1)

    def ring1(self, *extra, quote="都对,要注册,客户是自由职业设计师,先做 Invoicing", customers="自由职业设计师"):
        return self.ok(self.ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册",
                               "--set", "customers=" + customers, "--set", "main_line=Invoicing", *extra,
                               "--quote", quote, "--confirm"))

    def rest(self, market="en", deny="没有", conversion_check=None):
        answers = {2: ["jargon=开票"], 3: ["real_competitors=Rival", "compliance=没有"], 4: ["capacity=每月 4 篇"],
                   5: ["market_first=%s" % market, "deny_topics=%s" % deny]}
        for r_, sets in answers.items():
            self.ok(self.ob("show", "--ring", str(r_)))
            self.ok(self.ob("answer", "--ring", str(r_), *sum((["--set", s] for s in sets), []),
                            "--quote", "第 %d 环的回答就是这些" % r_, *(NO_AUDIT if r_ == 4 else []), "--confirm"))
        self.ok(self.ob("show", "--ring", "6"))


# ---------------------------------------------------------------------------
# 3. 三处崩溃
# ---------------------------------------------------------------------------

class CrashTests(unittest.TestCase):
    def test_repo_only_stage_candidates_render(self):
        """只给仓库、没给站点:lifecycle 给的候选是 [0, 1, 2],第一屏要能渲染出来。"""
        scan = {"schema": 1, "signals": {"repo_public_routes": 0}, "facts": [], "errors": []}
        w = Ws(self, scan=scan, start_args=("--repo", "."))
        self.assertIn("候选", w.start.stdout)
        self.assertIn("想法", w.start.stdout)

    def test_handwritten_profile_missing_rings_and_stage(self):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="obreg_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        ctx = os.path.join(tmp, "seo-ops", "context")
        os.makedirs(ctx)
        for args in (["status"], ["show"], ["status", "--json"]):
            with open(os.path.join(ctx, "profile.json"), "w", encoding="utf-8") as f:
                json.dump({"schema": 1, "site": "https://acme.example",
                           "facts": [{"key": "product.name", "value": "Acme"}]}, f)
            r = run("onboard.py", args, tmp)
            self.assertNotIn("Traceback", r.stderr, args)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("rings", r.stderr)              # 说清楚哪里不合格
        os.makedirs(os.path.join(tmp, "seo-ops", "plan"))
        with open(os.path.join(tmp, "seo-ops", "plan", "plan.json"), "w", encoding="utf-8") as f:
            json.dump({"items": [{"title": "Fix titles", "weeks": "1-2"}, {"title": "Write docs", "weeks": "3"}]}, f)
        r = run("plan.py", ["show", "--ws", "seo-ops"], tmp)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Fix titles", r.stdout)

    def test_string_weeks_do_not_crash_roadmap(self):
        import loops
        plan = {"status": "approved", "approved_at": (TODAY - dt.timedelta(days=7)).isoformat(),
                "items": [{"rank": 1, "title": "a", "weeks": "1"}, {"rank": 2, "title": "b", "weeks": "1-2"},
                          {"rank": 3, "title": "c", "weeks": [2, "3"]}, {"rank": 4, "title": "d", "weeks": "Week 2"},
                          {"title": "e", "weeks": "第 2–4 周"}]}
        wk, items = loops.roadmap_this_week(plan, TODAY)
        self.assertEqual(wk, 2)
        self.assertEqual([r["title"] for r in items], ["b", "c", "d", "e"])

    def test_plan_build_writes_integer_week_ranges(self):
        w = Ws(self)
        w.ring1()
        w.rest()
        self.assertEqual(run("plan.py", ["build", "--ws", w.ws], w.tmp).returncode, 0)
        with open(os.path.join(w.ws, "plan", "plan.json"), encoding="utf-8") as f:
            items = json.load(f)["items"]
        for it in items:
            self.assertTrue(isinstance(it["weeks"], list) and len(it["weeks"]) == 2
                            and all(isinstance(x, int) for x in it["weeks"]), it["weeks"])


# ---------------------------------------------------------------------------
# 5 / 10. 第 1 环问题数、product-marketing.md、可原样贴出的停下文本
# ---------------------------------------------------------------------------

PMM = """# Product Marketing Context

**Document version:** v2
**Last updated:** 2026-10-01

## Product Overview
**One-liner:** Invoicing for freelance designers
**Business model:** Subscription, $12/mo

## Target Audience
**Target companies:** Freelance designers and small studios

## Goals
**Conversion action:** Start a 14-day free trial

## Changelog
- v2 (2026-10-01) — first draft
"""


class StopTextTests(unittest.TestCase):
    def test_ring1_at_most_three_questions_and_block_is_pasteable(self):
        w = Ws(self)
        block = user_block(w.start.stdout)
        qs = numbered_questions(block)
        self.assertTrue(1 <= len(qs) <= 3, qs)
        self.assertNotIn("[id=", block)
        facts = [ln for ln in block.split(qs[0])[0].splitlines() if ln.lstrip().startswith("- ")]
        self.assertTrue(facts)
        for ln in facts:
            self.assertIn("←", ln)
        for q in qs:
            nxt = block.split(q, 1)[1].splitlines()[1] if len(block.split(q, 1)[1].splitlines()) > 1 else ""
            self.assertTrue(("A." in q and "B." in q) or "我猜" in nxt or "我猜" in q, q)
        self.assertIn("原样", w.start.stdout.split(BLOCK_END)[1])

    def test_pmm_covered_questions_not_asked_and_single_question_numbered(self):
        w = Ws(self, pmm=PMM)
        block = user_block(w.start.stdout)
        qs = numbered_questions(block)
        self.assertTrue(1 <= len(qs) <= 2, qs)
        self.assertTrue(qs[0].lstrip().startswith("1."))
        joined = "\n".join(qs)
        self.assertNotIn("主要客户是谁", joined)
        self.assertNotIn("最想让 SEO 带来什么结果", joined)
        self.assertIn(".agents/product-marketing.md", block)
        w.ok(w.ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "main_line=Invoicing",
                  "--quote", "都对,就按这份文件来", "--confirm"))
        ans = w.prof()["rings"]["1"]["answers"]
        self.assertEqual(ans.get("customers"), "Freelance designers and small studios")
        self.assertEqual(ans.get("conversion"), "Start a 14-day free trial")

    def test_unknown_lines_are_asked_in_ring1(self):
        unk = {"key": "product.lines", "value": None, "kind": "unknown", "source": None,
               "note": "llms.txt 没有产品段"}
        w = Ws(self, scan=base_scan(lines=None, extra=[unk]))
        block = user_block(w.start.stdout)
        self.assertRegex(block, r"产品线.*未知")
        qs = numbered_questions(block)
        self.assertTrue(len(qs) <= 3, qs)
        self.assertTrue(any("产品线" in q for q in qs), qs)
        r = w.ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册",
                 "--set", "customers=自由职业设计师", "--quote", "都对,客户是自由职业设计师", "--confirm")
        self.assertEqual(r.returncode, 3)                 # 产品线没答不能确认
        self.assertIn("main_line", r.stderr)


# ---------------------------------------------------------------------------
# 6. show 复述已确认的内容,刚纠正的值原样显示新值
# ---------------------------------------------------------------------------

class RecapTests(unittest.TestCase):
    def test_show_recaps_confirmed_and_corrected_values(self):
        w = Ws(self)
        w.ring1(customers="中小企业财务")
        w.ok(w.ob("show", "--ring", "2"))
        w.ok(w.ob("answer", "--ring", "1", "--correct", "customers=做 AI agent 的团队",
                  "--quote", "你理解错了,主要客户是做 AI agent 的团队"))
        r = w.ok(w.ob("show", "--ring", "2"))
        block = user_block(r.stdout)
        self.assertIn("做 AI agent 的团队", block)
        self.assertIn("Invoicing", block)
        for ln in block.splitlines():
            self.assertFalse("中小企业财务" in ln and "主要客户" in ln, ln)
        self.assertEqual(w.prof()["rings"]["1"]["answers"]["customers"], "做 AI agent 的团队")


# ---------------------------------------------------------------------------
# 9. skip 只认明确的跳过
# ---------------------------------------------------------------------------

class SkipQuoteTests(unittest.TestCase):
    def test_best_guess_is_not_skip(self):
        w = Ws(self)
        w.ring1()
        for q in ("Go with your best guess and move on to the next part.", "按你的猜测来,继续下一环。",
                  "按你的判断来", "Carry on.", "好"):
            r = w.ob("skip", "--quote", q)
            self.assertEqual(r.returncode, 3, q)
            self.assertIn("按草稿继续下一环", r.stderr, q)
        self.assertFalse([k for k, v in w.prof()["rings"].items() if v["status"] == "skipped"])

    def test_explicit_skip_accepted(self):
        for q in ("跳过剩下的,直接出方案", "Skip the rest, just give me the plan.", "不用问了"):
            w = Ws(self)
            w.ring1()
            r = w.ob("skip", "--quote", q)
            self.assertEqual(r.returncode, 0, q + r.stderr)
            self.assertTrue(all(w.prof()["rings"][str(i)]["status"] == "skipped" for i in range(2, 7)))


# ---------------------------------------------------------------------------
# 11. --correct 对列表字段只改一项;「X 最重要」提示 main_line
# ---------------------------------------------------------------------------

class ListCorrectionTests(unittest.TestCase):
    LINES = ("Trail guides", "Gear reviews and buying guides", "Trailmark Pro membership")

    def test_most_important_is_main_line_not_list(self):
        w = Ws(self, scan=base_scan(lines=self.LINES))
        r = w.ob("answer", "--ring", "1", "--correct", "product.lines=Gear reviews",
                 "--quote", "Gear reviews are the most important part.")
        self.assertEqual(r.returncode, 3)
        self.assertIn("main_line", r.stderr)
        lines = next(f for f in w.prof()["facts"] if f["key"] == "product.lines")["value"]
        self.assertEqual(lines, list(self.LINES))

    def test_single_value_replaces_one_item(self):
        w = Ws(self, scan=base_scan(lines=self.LINES))
        w.ok(w.ob("answer", "--ring", "1", "--correct", "product.lines=Gear reviews and comparisons",
                  "--quote", "The second line is really called Gear reviews and comparisons."))
        lines = next(f for f in w.prof()["facts"] if f["key"] == "product.lines")["value"]
        self.assertEqual(lines, ["Trail guides", "Gear reviews and comparisons", "Trailmark Pro membership"])


# ---------------------------------------------------------------------------
# 12. --quote 太短拒绝;短确认词在没有纠正时照收
# ---------------------------------------------------------------------------

class QuoteLengthTests(unittest.TestCase):
    def ring1_args(self, quote, *extra):
        return ["answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册",
                "--set", "customers=自由职业设计师", "--set", "main_line=Invoicing", *extra, "--quote", quote, "--confirm"]

    def test_short_non_confirmation_refused(self):
        for q in ("abc", "你好", "ok?"):
            w = Ws(self)
            r = w.ob(*self.ring1_args(q))
            self.assertEqual(r.returncode, 3, q)
            self.assertNotEqual(w.prof()["rings"]["1"]["status"], "confirmed")

    def test_short_confirmation_accepted_without_corrections(self):
        for q in ("Yes.", "对", "是的", "好"):
            w = Ws(self)
            w.ok(w.ob(*self.ring1_args(q)))
            self.assertEqual(w.prof()["rings"]["1"]["status"], "confirmed")

    def test_short_confirmation_with_correction_refused(self):
        w = Ws(self)
        r = w.ob(*self.ring1_args("对", "--correct", "product.one_liner=Invoices for studios"))
        self.assertEqual(r.returncode, 3)


# ---------------------------------------------------------------------------
# 13. 档案被手改:报警、受影响的环重新确认
# ---------------------------------------------------------------------------

class TamperTests(unittest.TestCase):
    def test_hand_edit_detected_and_ring_reopened(self):
        w = Ws(self)
        w.ring1()
        p = w.prof()
        for f in p["facts"]:
            if f["key"] == "customers":
                f["value"] = ["Enterprise CFOs"]
        w.write_prof(p)
        r = w.ob("status")
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("手改", r.stderr + r.stdout)
        self.assertIn("第 1 环", r.stderr + r.stdout)
        self.assertNotEqual(w.prof()["rings"]["1"]["status"], "confirmed")
        r = run("plan.py", ["build", "--ws", w.ws], w.tmp)
        self.assertEqual(r.returncode, 3)

    def test_script_writes_are_not_flagged(self):
        w = Ws(self)
        w.ring1()
        r = w.ok(w.ob("status"))
        self.assertNotIn("手改", r.stderr + r.stdout)
        self.assertEqual(w.prof()["rings"]["1"]["status"], "confirmed")

    def test_plan_gate_on_hand_edit(self):
        w = Ws(self)
        w.ring1()
        p = w.prof()
        p["stage"]["value"] = 4
        w.write_prof(p)
        r = run("plan.py", ["build", "--ws", w.ws], w.tmp)
        self.assertEqual(r.returncode, 3)
        self.assertIn("手改", r.stderr)


# ---------------------------------------------------------------------------
# 7 / 8. 方案:第 1 环的目标、单语市场、量到的掉量
# ---------------------------------------------------------------------------

def items_text(it):
    out = []

    def walk(x):
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(it)
    return " ".join(out)


class PlanGoalAndMarketTests(unittest.TestCase):
    def test_idea_goal_ranked_and_single_market_no_hreflang(self):
        scan = {"schema": 1, "signals": {"site_live": False, "repo_public_routes": 0},
                "facts": [{"key": "product.name", "value": "PetLedger", "source": "README.md", "kind": "fact"},
                          {"key": "product.lines", "value": ["健康提醒", "病历档案"], "source": "README.md", "kind": "fact"}],
                "errors": []}
        w = Ws(self, scan=scan, start_args=("--repo", "."))
        w.ok(w.ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=上线前攒候补名单,先攒 2000 个",
                  "--set", "customers=一二线城市养猫狗的上班族", "--set", "main_line=健康提醒", "--correct", "stage=0",
                  "--quote", "对。最想要的是上线前攒候补名单,先攒 2000 个", "--confirm"))
        w.rest(market="只做中国大陆、简体中文")
        r = run("plan.py", ["build", "--ws", w.ws, "--json"], w.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        plan = json.loads(r.stdout)
        top5 = [items_text(it) for it in plan["items"][:5]]
        self.assertTrue(any("候补名单" in t for t in top5), [it["title"] for it in plan["items"][:5]])
        for it in plan["items"]:
            t = items_text({k: it[k] for k in ("title", "title_en", "do", "do_en")})
            self.assertNotIn("hreflang", t.lower(), it["id"])
            self.assertNotIn("多语言", t, it["id"])


class PlanDropTests(unittest.TestCase):
    def test_measured_drop_written_into_plan(self):
        w = Ws(self)
        site = os.path.join(w.tmp, "mature")
        p = subprocess.run([sys.executable, SITES, "build", "--product", "mature", "--out", site,
                            "--base", "http://127.0.0.1:9"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        shutil.copytree(os.path.join(site, "gsc"), os.path.join(w.tmp, "data"))
        w.ring1("--correct", "stage=4", quote="对,我们现在是成熟期,流量在掉")
        w.rest()
        r = run("plan.py", ["build", "--ws", w.ws, "--json"], w.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        plan = json.loads(r.stdout)
        hit = [items_text(it) for it in plan["items"]
               if re.search(r"review|评测", items_text(it), re.I) and "1,850" in items_text(it)
               and "1,450" in items_text(it)]
        self.assertTrue(hit, [it["title"] for it in plan["items"]])
        self.assertRegex(hit[0], r"[-−]21\.6%")


# ---------------------------------------------------------------------------
# 4. 阶段趋势从逐日 gsc-pages.csv 回填
# ---------------------------------------------------------------------------

def write_daily(path, end, days, impressions_of):
    rows = ["page,date,clicks,impressions"]
    for i in range(days, 0, -1):
        d = end - dt.timedelta(days=i)
        imp = impressions_of(d)
        rows.append("https://acme.example/,%s,%d,%d" % (d.isoformat(), max(1, imp // 20), imp))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")


class StageTrendBackfillTests(unittest.TestCase):
    def onboarded(self):
        w = Ws(self, metrics={"gsc_impressions_28d": 400, "gsc_clicks_28d": 8, "gsc_clicks_prev_28d": 6})
        w.ring1()
        w.rest()
        w.ok(run("plan.py", ["build", "--ws", w.ws], w.tmp))
        w.ok(w.ob("answer", "--ring", "6", "--set", "approve_plan=可以", "--quote", "可以,就按这个方案做", "--confirm"))
        self.assertEqual(w.prof()["stage"]["value"], 2)
        return w

    def loops_run(self, w, today):
        r = run("loops.py", ["run", "--ws", w.ws, "--json", "--today", today.isoformat()], w.tmp)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        ev = json.loads(r.stdout)
        return next(x for x in ev["loops"] if x["id"] == "stage-threshold")

    def test_daily_csv_over_threshold_prompts_new_stage(self):
        w = self.onboarded()
        T = TODAY + dt.timedelta(days=30)
        write_daily(os.path.join(w.tmp, "data", "gsc-pages.csv"), T, 90,
                    lambda d: 200 if d >= T - dt.timedelta(days=35) else 23)
        st = self.loops_run(w, T)
        self.assertEqual((st["status"], st.get("to_stage")), ("ask", 3), st)
        with open(os.path.join(w.ws, "context", "metrics_history.jsonl"), encoding="utf-8") as f:
            rows = [json.loads(x) for x in f if x.strip()]
        self.assertGreaterEqual(len([x for x in rows if "gsc-pages.csv" in str(x.get("source"))]), 4)

    def test_single_spike_in_daily_csv_is_not_enough(self):
        w = self.onboarded()
        T = TODAY + dt.timedelta(days=30)
        write_daily(os.path.join(w.tmp, "data", "gsc-pages.csv"), T, 90,
                    lambda d: 1500 if d == T - dt.timedelta(days=3) else 23)
        self.assertEqual(self.loops_run(w, T)["status"], "quiet")


# ---------------------------------------------------------------------------
# 15. project.py run triage --allow-local
# ---------------------------------------------------------------------------

class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class TriageAllowLocalTests(unittest.TestCase):
    def test_triage_allow_local(self):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="triage_local_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        site = os.path.join(tmp, "site")
        os.makedirs(site)
        with open(os.path.join(site, "index.html"), "w", encoding="utf-8") as f:
            f.write('<!doctype html><html lang="en"><head><title>Local dev site</title>'
                    '<meta name="description" content="A local preview"></head><body><h1>Hi</h1></body></html>')
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=site))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        url = "http://127.0.0.1:%d/" % srv.server_address[1]
        ws = os.path.join(tmp, "seo-ops")
        self.assertEqual(run("project.py", ["init", "--site", url, "--dir", ws], tmp).returncode, 0)
        r = run("project.py", ["run", "triage", "--dir", ws, "--allow-local", "--max", "3", "--json"], tmp)
        self.assertNotEqual(r.returncode, 2, r.stderr)
        crawl = next(s for s in json.loads(r.stdout)["steps"] if s["name"] == "crawl")
        self.assertTrue(crawl["ok"], crawl)
        self.assertIn("--allow-local", crawl["cmd"])


if __name__ == "__main__":
    unittest.main()
