#!/usr/bin/env python3
"""plan.py / launch_check.py 回归(RQ-237 第 2 批;stdlib unittest,零外网)。

期望值的来源(不从实现反推):
- 需求卡 RQ-237 例 3:前 10 条里 ≥8 条引用档案里的产品事实;10 条都属于本阶段,增长期不出「去提交 GSC 验证」,
  想法阶段不出「刷新旧文」;每条写动哪类页面、预期动哪个数、怎么量、第几周做。
- 例 4:想法阶段不跑技术体检,改给需求验证和信息架构;上线前在本地预览上跑上线清单。
- 例 6 / 红队 9:「明确不做」是结构化禁用清单,推荐代码直接过滤。
- 第 1 环必须确认才出方案(Echo 11-08 选「至少答完第 1 环」)。
- 真实回放发现的 bug:只给仓库、没给站点时阶段判「未知」,第 1 环照样能确认、之后方案出不来(11-08 跑 PetLedger)。
"""
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)
import lifecycle as LC  # noqa: E402

AUDIT_CMDS = ("site_crawl", "project.py run triage", "launch_check", "health_score", "site_audit")


def run(script, args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", env=env)


def scan_for(stage):
    sig = {"idea": {"site_live": False, "repo_public_routes": 0},
           "prelaunch": {"site_live": True, "robots_block_all": True, "url_count": 8, "repo_public_routes": 8},
           "growth": {"site_live": True, "robots_block_all": False, "homepage_noindex": False, "url_count": 1200,
                      "first_seen": "2025-06-01", "has_llms_txt": True, "analytics": ["gtag"],
                      "same_as": ["https://x.com/acme"]}}[stage]
    return {"schema": 1, "site": "https://acme.example", "signals": sig,
            "site_scan": {"page_types": {"pricing": 1, "docs": 30, "blog": 40, "compare": 2}},
            "facts": [{"key": "product.name", "value": "Acme", "source": "https://acme.example/", "kind": "fact"},
                      {"key": "product.lines", "value": ["发票", "报销"], "source": "llms.txt", "kind": "inferred"},
                      {"key": "market.languages", "value": ["zh"], "source": "hreflang", "kind": "fact"}],
            "errors": []}


class Workspace:
    """在临时目录里走一遍开局:start(--scan 喂草稿)→ 第 1 环确认 → 其余环答完或跳过。"""

    def __init__(self, test, stage, metrics=None):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="plan_test_"))
        test.addCleanup(shutil.rmtree, self.tmp, True)
        with open(os.path.join(self.tmp, "scan.json"), "w", encoding="utf-8") as f:
            json.dump(scan_for(stage), f, ensure_ascii=False)
        self.ws = os.path.join(self.tmp, "seo-ops")
        r = self.ob("start", "--site", "https://acme.example", "--scan", "scan.json", "--market", "zh")
        test.assertEqual(r.returncode, 0, r.stderr)
        if metrics:
            r = self.ob("metric", *sum((["--set", "%s=%s" % kv] for kv in metrics.items()), []), "--source", "测试")
            test.assertEqual(r.returncode, 0, r.stderr)
        self.test = test

    def ob(self, *args):
        return run("onboard.py", list(args), self.tmp)

    def ring1(self):
        r = self.ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册",
                    "--set", "customers=中小企业财务", "--set", "main_line=发票",
                    "--quote", "都对,要注册,客户是中小企业财务,先做发票", "--confirm")
        self.test.assertEqual(r.returncode, 0, r.stderr)

    def rest(self, deny="没有"):
        answers = {2: ["jargon=开票"], 3: ["real_competitors=Rival", "compliance=没有"], 4: ["capacity=每月 4 篇"],
                   5: ["market_first=zh", "deny_topics=%s" % deny]}
        for r_, sets in answers.items():
            self.test.assertEqual(self.ob("show", "--ring", str(r_)).returncode, 0)
            args = ["answer", "--ring", str(r_)] + sum((["--set", s] for s in sets), []) + ["--quote", "答 %d" % r_, "--confirm"]
            res = self.ob(*args)
            self.test.assertEqual(res.returncode, 0, res.stderr)
        self.ob("show", "--ring", "6")

    def plan(self):
        r = run("plan.py", ["build", "--ws", self.ws, "--json"], self.tmp)
        self.test.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)


def stages_of():
    with open(os.path.join(BASE, "data", "playbooks.json"), encoding="utf-8") as f:
        pb = json.load(f)
    return {p["id"]: p["stages"] for p in pb["plays"]}


class PlanExample3Tests(unittest.TestCase):
    def full(self, stage, **kw):
        w = Workspace(self, stage, **kw)
        w.ring1()
        w.rest()
        return w, w.plan()

    def test_growth_plan_is_stage_bound_and_cites_facts(self):
        _, p = self.full("growth", metrics={"gsc_clicks_28d": 1200, "gsc_clicks_prev_28d": 1000,
                                            "gsc_impressions_28d": 50000})
        self.assertEqual(p["stage"]["id"], 3)
        recs = p["recommendations"]
        self.assertEqual(len(recs), 10)
        st = stages_of()
        self.assertTrue(all(3 in st[r["id"]] for r in recs), [r["id"] for r in recs])
        self.assertGreaterEqual(sum(1 for r in recs if r["facts_used"]), 8)
        self.assertFalse([r for r in recs if "GSC" in r["title"] and ("验证" in r["title"] or "提交" in r["title"])])
        for r in recs:
            self.assertTrue(r["page_types"] and r["metric"] and r["measure"] and r["weeks"], r["id"])

    def test_idea_plan_has_no_audit_and_no_refresh(self):
        w = Workspace(self, "idea")
        w.ring1()
        w.rest()
        p = w.plan()
        self.assertEqual(p["stage"]["id"], 0)
        recs = p["recommendations"]
        self.assertFalse([r["id"] for r in recs if any(c in r["cmd"] for c in AUDIT_CMDS)])
        self.assertFalse([r for r in recs if "刷新" in r["title"] or "旧文" in r["title"]])
        themes = {r["theme"] for r in recs}
        self.assertIn("validate", themes)        # 需求验证
        self.assertIn("architecture", themes)    # 信息架构
        self.assertGreaterEqual(sum(1 for r in recs if r["facts_used"]), 8)

    def test_prelaunch_plan_runs_launch_checklist_locally(self):
        w = Workspace(self, "prelaunch")
        w.ring1()
        w.rest()
        p = w.plan()
        self.assertEqual(p["stage"]["id"], 1)
        launch = [r for r in p["recommendations"] if "launch_check" in r["cmd"]]
        self.assertTrue(launch)
        self.assertIn("--allow-local", launch[0]["cmd"])

    def test_books_written_in_both_languages(self):
        w = Workspace(self, "growth")
        w.ring1()
        w.rest()
        w.plan()
        for name in ("plan.json", "roadmap.md", "strategy-book.zh.md", "strategy-book.en.md"):
            self.assertTrue(os.path.isfile(os.path.join(w.ws, "plan", name)), name)
        with open(os.path.join(w.ws, "plan", "strategy-book.en.md"), encoding="utf-8") as f:
            en = f.read()
        self.assertIn("90-day roadmap", en)
        self.assertIn("Acme", en)


class PlanGateTests(unittest.TestCase):
    def test_no_plan_before_ring1(self):
        w = Workspace(self, "growth")
        r = run("plan.py", ["build", "--ws", w.ws], w.tmp)
        self.assertEqual(r.returncode, 3)
        self.assertFalse(os.path.exists(os.path.join(w.ws, "plan", "plan.json")))

    def test_deny_list_filters_recommendations(self):
        w = Workspace(self, "growth")
        w.ring1()
        w.rest(deny="对比页、程序化")
        p = w.plan()
        ids = [r["id"] for r in p["recommendations"] + p["more"]]
        self.assertNotIn("compare-pages", ids)
        self.assertNotIn("pseo-gated", ids)
        denied = {x["id"] for x in p["skipped"]["denied"]}
        self.assertTrue({"compare-pages", "pseo-gated"} <= denied)

    def test_ring6_approval_marks_plan_approved(self):
        w = Workspace(self, "growth")
        w.ring1()
        w.rest()
        w.plan()
        r = w.ob("answer", "--ring", "6", "--set", "approve_plan=可以", "--quote", "可以,就这么做", "--confirm")
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(w.ws, "plan", "plan.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["status"], "approved")


class RepoOnlyStageRegressionTests(unittest.TestCase):
    """11-08 真实回放:PetLedger 只给了空仓库,阶段判「未知」、第 1 环照样确认,方案出不来。"""

    def test_repo_only_empty_is_idea_guess(self):
        d = LC.diagnose({"signals": {"repo_public_routes": 0, "site_live": None}, "facts": []})
        self.assertEqual((d["stage"]["stage"], d["stage"]["confidence"]), (0, "guess"))

    def test_ring1_cannot_confirm_with_unknown_stage(self):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="plan_test_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        with open(os.path.join(tmp, "scan.json"), "w", encoding="utf-8") as f:
            json.dump({"schema": 1, "signals": {}, "facts": [], "errors": []}, f)
        self.assertEqual(run("onboard.py", ["start", "--site", "https://acme.example", "--scan", "scan.json"], tmp).returncode, 0)
        r = run("onboard.py", ["answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册",
                               "--set", "customers=x", "--set", "main_line=y", "--quote", "都对", "--confirm"], tmp)
        self.assertEqual(r.returncode, 3)
        r = run("onboard.py", ["answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册",
                               "--set", "customers=x", "--set", "main_line=y", "--correct", "stage=0",
                               "--quote", "还只是个想法", "--confirm"], tmp)
        self.assertEqual(r.returncode, 0, r.stderr)


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class LaunchCheckTests(unittest.TestCase):
    """例 4:上线前在本地预览上跑上线清单;预发的全站封锁不能带上线。"""

    def setUp(self):
        self.dir = os.path.realpath(tempfile.mkdtemp(prefix="launch_test_"))
        self.addCleanup(shutil.rmtree, self.dir, True)
        page = ('<!doctype html><html lang="en"><head><title>Acme invoicing</title>'
                '<meta name="description" content="Invoices for small teams">'
                '<meta name="viewport" content="width=device-width">'
                '<link rel="canonical" href="https://acme.example/"></head><body><h1>Acme</h1></body></html>')
        with open(os.path.join(self.dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
        with open(os.path.join(self.dir, "robots.txt"), "w", encoding="utf-8") as f:
            f.write("User-agent: *\nDisallow: /\n")
        handler = lambda *a, **k: _Quiet(*a, directory=self.dir, **k)  # noqa: E731
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.shutdown)
        self.url = "http://127.0.0.1:%d" % self.srv.server_address[1]

    def test_staging_block_is_a_blocker(self):
        r = run("launch_check.py", ["--url", self.url, "--allow-local", "--prod-host", "acme.example", "--json"], self.dir)
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        self.assertFalse(rep["summary"]["ready"])
        self.assertIn("robots", rep["summary"]["blockers"])
        manual = [i for i in rep["items"] if i["kind"] == "manual"]
        self.assertTrue(manual and all(i["owner"] for i in manual))   # 手动项都有负责人

    def test_local_preview_refused_without_flag(self):
        r = run("launch_check.py", ["--url", self.url, "--json"], self.dir)
        rep = json.loads(r.stdout)
        self.assertFalse(rep["summary"]["ready"])
        self.assertTrue(rep["errors"])


if __name__ == "__main__":
    unittest.main()
