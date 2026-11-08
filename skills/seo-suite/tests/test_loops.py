#!/usr/bin/env python3
"""loops.py 回归(RQ-237 第 3 批;stdlib unittest,零网络)。

期望值来源:需求卡 RQ-237 例 5(Echo 11-08 确认的例子)——
- 第二次打开不重新从头问,一屏说清:档案上次确认是哪天、在哪个阶段、方案进行到第几周、本周路线项。
- 档案超过 30 天没核 → 加「档案核对」,问 1–3 个问题;
- 产品变了(新产品线、定价改了、sitemap 出现新页面类型)→ 回第 1 环只问变了的部分;
- 到了下一阶段门槛(连续 4 周)→ 提示换阶段;
- 「30 天后」「新增一条产品线」「流量过了阶段门槛」三个状态各触发对应规则;没变化时不重复提问。
红队 7:运营单优先级 硬告警 > 路线本周项 > 原「只做这一件」。
"""
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
TODAY = dt.date.today()


def run(script, args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", env=env)


def scan(lines=("发票", "报销"), page_types=None, first_seen="2025-06-01"):
    return {"schema": 1, "site": "https://acme.example",
            "signals": {"site_live": True, "robots_block_all": False, "homepage_noindex": False, "url_count": 400,
                        "first_seen": first_seen, "has_llms_txt": True, "analytics": ["gtag"]},
            "site_scan": {"page_types": page_types or {"pricing": 1, "docs": 30, "blog": 40}},
            "facts": [{"key": "product.name", "value": "Acme", "source": "https://acme.example/", "kind": "fact"},
                      {"key": "product.lines", "value": list(lines), "source": "llms.txt", "kind": "inferred"},
                      {"key": "pricing.prices", "value": ["$12 per mo"], "source": "/pricing", "kind": "fact"}],
            "errors": []}


class Ws:
    def __init__(self, t, metrics=None):
        self.t = t
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="loops_test_"))
        t.addCleanup(shutil.rmtree, self.tmp, True)
        self.ws = os.path.join(self.tmp, "seo-ops")
        with open(os.path.join(self.tmp, "scan.json"), "w", encoding="utf-8") as f:
            json.dump(scan(), f, ensure_ascii=False)
        self.ok(self.ob("start", "--site", "https://acme.example", "--scan", "scan.json", "--market", "zh"))
        if metrics:
            self.ok(self.ob("metric", *sum((["--set", "%s=%s" % kv] for kv in metrics.items()), []), "--source", "测试"))

    def ok(self, r):
        self.t.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r

    def ob(self, *a):
        return run("onboard.py", list(a), self.tmp)

    def lp(self, *a):
        return run("loops.py", list(a) + ["--ws", self.ws], self.tmp)

    def onboard_all(self, approve=True):
        self.ok(self.ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册",
                        "--set", "customers=中小企业财务", "--set", "main_line=发票", "--quote", "都对", "--confirm"))
        for r_, sets in {2: ["jargon=开票"], 3: ["real_competitors=Rival"], 4: ["capacity=每月 4 篇"],
                         5: ["market_first=zh", "deny_topics=没有"]}.items():
            self.ok(self.ob("show", "--ring", str(r_)))
            self.ok(self.ob("answer", "--ring", str(r_), *sum((["--set", s] for s in sets), []), "--quote", "答", "--confirm"))
        self.ok(self.ob("show", "--ring", "6"))
        self.ok(run("plan.py", ["build", "--ws", self.ws], self.tmp))
        if approve:
            self.ok(self.ob("answer", "--ring", "6", "--set", "approve_plan=可以", "--quote", "可以", "--confirm"))

    def loops_json(self, *a):
        r = self.lp("run", "--json", *a)
        self.t.assertIn(r.returncode, (0, 1), r.stderr)
        return json.loads(r.stdout), r.returncode


def d(n):
    return (TODAY + dt.timedelta(days=n)).isoformat()


class SecondOpenTests(unittest.TestCase):
    def test_status_one_screen(self):
        w = Ws(self)
        w.onboard_all()
        r = w.lp("status", "--today", d(8))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(TODAY.isoformat(), r.stdout)          # 档案上次核对日
        self.assertIn("增长期", r.stdout)                    # 阶段
        self.assertIn("第 2 周", r.stdout)                   # 方案第几周
        self.assertIn("本周路线项", r.stdout)

    def test_no_change_no_questions_and_no_repeat(self):
        w = Ws(self)
        w.onboard_all()
        ev, code = w.loops_json("--today", d(7))
        self.assertEqual((ev["questions"], code), ([], 0))
        ev, code = w.loops_json("--today", d(8), "--scan", os.path.join(w.tmp, "scan.json"))
        self.assertEqual((ev["questions"], code), ([], 0))

    def test_loops_wait_until_onboarding_done(self):
        w = Ws(self)
        r = w.lp("run", "--today", d(40))
        self.assertEqual(r.returncode, 3)


class ThirtyDaysTests(unittest.TestCase):
    def test_profile_review_after_30_days_asked_once(self):
        w = Ws(self)
        w.onboard_all()
        ev, code = w.loops_json("--today", d(31))
        self.assertEqual(code, 1)
        pr = next(x for x in ev["loops"] if x["id"] == "profile-review")
        self.assertEqual(pr["status"], "ask")
        self.assertTrue(1 <= len(ev["questions"]) <= 3)
        ev, code = w.loops_json("--today", d(33))           # 没回复:不重复问
        self.assertEqual(code, 0)
        self.assertEqual(next(x for x in ev["loops"] if x["id"] == "profile-review")["status"], "waiting")
        w.ok(w.lp("resolve", "profile-review", "--quote", "都没变", "--today", d(33)))
        ev, code = w.loops_json("--today", d(40))
        self.assertEqual(code, 0)


class ProductChangeTests(unittest.TestCase):
    def test_new_product_line_asks_only_what_changed(self):
        w = Ws(self)
        w.onboard_all()
        p = os.path.join(w.tmp, "scan2.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(scan(lines=("发票", "报销", "差旅")), f, ensure_ascii=False)
        ev, code = w.loops_json("--today", d(10), "--scan", p)
        self.assertEqual(code, 1)
        pc = next(x for x in ev["loops"] if x["id"] == "product-change")
        self.assertEqual(pc["status"], "ask")
        self.assertEqual([c["key"] for c in pc["changes"]], ["product.lines"])
        self.assertEqual(pc["ring"], 1)
        self.assertTrue(any("差旅" in q["text"] for q in ev["questions"]))
        self.assertFalse(any("定价" in q["text"] for q in ev["questions"]))   # 没变的不问
        w.ok(w.lp("resolve", "product-change", "--quote", "对,新加了差旅", "--set", "product.lines=发票,报销,差旅",
                  "--today", d(10)))
        ev, code = w.loops_json("--today", d(11), "--scan", p)
        self.assertEqual(code, 0)

    def test_new_page_type_detected(self):
        w = Ws(self)
        w.onboard_all()
        p = os.path.join(w.tmp, "scan3.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(scan(page_types={"pricing": 1, "docs": 30, "blog": 40, "integrations": 12}), f)
        ev, _ = w.loops_json("--today", d(10), "--scan", p)
        pc = next(x for x in ev["loops"] if x["id"] == "product-change")
        self.assertEqual([c["kind"] for c in pc.get("changes", [])], ["new_page_type"])


class StageThresholdTests(unittest.TestCase):
    def test_four_weeks_over_threshold_prompts_growth(self):
        w = Ws(self, metrics={"gsc_impressions_28d": 400, "gsc_clicks_28d": 8, "gsc_clicks_prev_28d": 6})
        w.onboard_all()
        with open(os.path.join(w.ws, "context", "profile.json"), encoding="utf-8") as f:
            prof = json.load(f)
        self.assertEqual(prof["stage"]["value"], 2)
        ev, code = w.loops_json("--today", d(3))
        self.assertEqual(next(x for x in ev["loops"] if x["id"] == "stage-threshold")["status"], "quiet")
        for i, at in enumerate((d(7), d(14), d(21), d(28))):
            w.ok(w.ob("metric", "--set", "gsc_impressions_28d=%d" % (5000 + i * 500), "--set", "gsc_clicks_28d=%d" % (300 + i * 30),
                      "--set", "gsc_clicks_prev_28d=200", "--source", "测试", "--at", at))
        ev, code = w.loops_json("--today", d(29))
        st = next(x for x in ev["loops"] if x["id"] == "stage-threshold")
        self.assertEqual((st["status"], st.get("to_stage")), ("ask", 3))
        self.assertTrue(any("增长期" in q["text"] for q in ev["questions"]))

    def test_one_spike_is_not_enough(self):
        w = Ws(self, metrics={"gsc_impressions_28d": 400, "gsc_clicks_28d": 8, "gsc_clicks_prev_28d": 6})
        w.onboard_all()
        w.ok(w.ob("metric", "--set", "gsc_impressions_28d=9000", "--set", "gsc_clicks_28d=400",
                  "--set", "gsc_clicks_prev_28d=200", "--source", "测试", "--at", d(7)))
        ev, _ = w.loops_json("--today", d(8))
        self.assertEqual(next(x for x in ev["loops"] if x["id"] == "stage-threshold")["status"], "quiet")


class OpsPriorityTests(unittest.TestCase):
    """红队 7:硬告警 > 路线本周项 > 原「只做这一件」;让位的那件照样列出来。"""

    def setUp(self):
        sys.path.insert(0, SCRIPTS)
        import ops
        self.ops = ops
        self.road = {"week": 2, "approved_at": "2026-11-08",
                     "items": [{"rank": 1, "title": "对比页", "do": "做 Acme vs Rival", "metric": "非品牌点击", "measure": "GSC"}]}
        self.pick = {"what": "改写 /x 的标题", "why": "展示多点击少", "url": "https://acme.example/x", "source": "GSC"}

    def test_roadmap_beats_single_pick(self):
        rec, sp = self.ops.with_plan([], self.pick, self.road)
        self.assertIn("本周路线项", rec["what"])
        self.assertEqual(sp, self.pick)

    def test_hard_alert_beats_roadmap(self):
        hard_rec = {"what": "先处理硬告警:首页 500", "why": "x", "url": None, "source": "轻检"}
        rec, sp = self.ops.with_plan([{"title": "首页 500"}], hard_rec, self.road)
        self.assertEqual((rec, sp), (hard_rec, None))

    def test_ops_weekly_feeds_metrics_history(self):
        w = Ws(self)
        w.onboard_all()
        rows = [{"date": (TODAY - dt.timedelta(days=i)).isoformat(), "clicks": 10, "impressions": 200} for i in range(56)]
        ev, road, _ = self.ops.lifecycle_loops(w.ws, {"sources": {"gsc_totals": {"rows": rows[::-1]}}}, d(8))
        self.assertEqual(road["week"], 2)
        with open(os.path.join(w.ws, "context", "metrics_history.jsonl"), encoding="utf-8") as f:
            last = [json.loads(x) for x in f if x.strip()][-1]
        self.assertEqual(last["metrics"]["gsc_impressions_28d"], 28 * 200)


if __name__ == "__main__":
    unittest.main()
