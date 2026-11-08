#!/usr/bin/env python3
"""onboard.py / lifecycle.py 回归(RQ-237;stdlib unittest,零网络)。

期望值的来源:需求卡 RQ-237 第 1 节阶段表和第 2 节例 1、例 2、例 6(Echo 11-08 确认的例子)
与红队意见 1、10(第 1 环必须由用户原话确认、自动读来的条目一律未确认、敏感答案不进 git)。
不从实现反推。product_scan 用 --scan 喂一份固定草稿,不抓网。"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)
import lifecycle as LC  # noqa: E402

SCAN = {
    "schema": 1, "site": "https://acme.example",
    "signals": {"site_live": True, "robots_block_all": False, "homepage_noindex": False, "url_count": 120,
                "has_llms_txt": True, "has_jsonld": True, "analytics": True, "same_as": ["https://x.com/acme"]},
    "site_scan": {"page_types": {"pricing": 1, "docs": 20, "blog": 12, "compare": 2}},
    "facts": [
        {"key": "product.name", "value": "Acme", "source": "https://acme.example/", "kind": "fact"},
        {"key": "product.one_liner", "value": "Acme 帮团队开发票", "source": "https://acme.example/llms.txt", "kind": "fact"},
        {"key": "product.lines", "value": ["发票", "报销"], "source": "https://acme.example/llms.txt", "kind": "inferred"},
        {"key": "conversion.ctas", "value": [{"text": "免费注册", "href": "/signup"}], "source": "https://acme.example/", "kind": "fact"},
        {"key": "market.languages", "value": ["zh", "en"], "source": "hreflang", "kind": "fact"},
    ],
    "errors": [],
}


def run(args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "onboard.py"), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", env=env)


class OnboardGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="onboard_test_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        with open(os.path.join(self.tmp, "scan.json"), "w", encoding="utf-8") as f:
            json.dump(SCAN, f, ensure_ascii=False)
        r = run(["start", "--site", "https://acme.example", "--scan", "scan.json", "--market", "zh"], self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.first_screen = r.stdout
        self.ws = os.path.join(self.tmp, "seo-ops")

    def prof(self):
        with open(os.path.join(self.ws, "context", "profile.json"), encoding="utf-8") as f:
            return json.load(f)

    def confirm_ring1(self):
        r = run(["answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册",
                 "--set", "customers=中小企业财务", "--set", "main_line=发票",
                 "--quote", "都对,要注册,客户是中小企业财务,先做发票", "--confirm"], self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)

    # 例 1:第一屏先不给建议,是草稿 + 问题 + 停
    def test_first_screen_is_draft_questions_and_stop(self):
        s = self.first_screen
        self.assertIn("第 1 环", s)
        self.assertIn("https://acme.example/llms.txt", s)         # 草稿带出处
        self.assertIn("## 停", s)
        self.assertLessEqual(s.count("[id="), 4)                  # 每环最多 4 个问题
        self.assertNotIn("下一件事", s)                             # 没有建议

    # 红队 10:自动读来的条目一律未确认
    def test_scanned_facts_start_unconfirmed(self):
        self.assertTrue(all(f["status"] == "unconfirmed" for f in self.prof()["facts"]))

    # 红队 1:没有用户原话不能确认
    def test_confirm_requires_user_quote(self):
        r = run(["answer", "--ring", "1", "--set", "conversion=注册", "--confirm"], self.tmp)
        self.assertEqual(r.returncode, 3)
        self.assertEqual(self.prof()["rings"]["1"]["status"], "asking")

    # 例 2:必答题没答齐不能确认
    def test_confirm_requires_all_required(self):
        r = run(["answer", "--ring", "1", "--set", "conversion=注册", "--quote", "要注册", "--confirm"], self.tmp)
        self.assertEqual(r.returncode, 3)
        self.assertNotEqual(self.prof()["rings"]["1"]["status"], "confirmed")

    # 例 2:第 1 环就说「别问了」→ 不放行
    def test_skip_refused_before_ring1(self):
        r = run(["skip", "--quote", "别问了,直接给方案"], self.tmp)
        self.assertEqual(r.returncode, 3)
        r = run(["show", "--ring", "2"], self.tmp)
        self.assertEqual(r.returncode, 3)

    # 例 2:纠正后档案改掉,后面用改后的值
    def test_correction_propagates(self):
        r = run(["answer", "--ring", "1", "--set", "profile_ok=要改", "--set", "conversion=注册",
                 "--set", "customers=做 AI agent 的团队", "--set", "main_line=发票",
                 "--correct", "product.one_liner=Acme 给 AI agent 团队开发票",
                 "--quote", "你理解错了,主要客户是做 AI agent 的团队", "--confirm"], self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        p = self.prof()
        f = next(x for x in p["facts"] if x["key"] == "product.one_liner")
        self.assertEqual((f["value"], f["status"]), ("Acme 给 AI agent 团队开发票", "corrected"))
        self.assertIn("做 AI agent 的团队", p["rings"]["1"]["answers"]["customers"])
        with open(os.path.join(self.ws, "context", "product.md"), encoding="utf-8") as fh:
            self.assertIn("Acme 给 AI agent 团队开发票", fh.read())

    # 例 2:「不知道」标未确认继续往下,不卡住
    def test_unknown_does_not_block(self):
        self.confirm_ring1()
        self.assertEqual(run(["show", "--ring", "2"], self.tmp).returncode, 0)
        r = run(["answer", "--ring", "2", "--unknown", "jargon", "--quote", "这个不知道", "--confirm"], self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        p = self.prof()
        self.assertEqual(p["rings"]["2"]["status"], "confirmed")
        self.assertEqual(p["rings"]["2"]["answers"]["jargon"], "(用户不知道)")

    # 每环都停:没发给用户的环不能确认
    def test_cannot_confirm_unasked_ring(self):
        self.confirm_ring1()
        r = run(["answer", "--ring", "3", "--set", "ignore=无", "--quote", "无", "--confirm"], self.tmp)
        self.assertEqual(r.returncode, 3)

    # 例 2:第 1 环确认后可以跳过剩下的,并列出没确认的猜测
    def test_skip_after_ring1_lists_unconfirmed(self):
        self.confirm_ring1()
        r = run(["skip", "--quote", "别问了"], self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("market.languages", r.stdout)
        p = self.prof()
        self.assertTrue(all(p["rings"][str(i)]["status"] == "skipped" for i in range(2, 7)))

    # 红队 10:敏感答案不进档案正文,目录进 .gitignore
    def test_sensitive_answer_goes_private(self):
        self.confirm_ring1()
        for r_ in (2, 3, 4):
            run(["show", "--ring", str(r_)], self.tmp)
        r = run(["answer", "--ring", "4", "--set", "history=2024 年买过链接,被手动处罚过",
                 "--quote", "2024 年买过链接,被手动处罚过"], self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.ws, "context", "profile.json"), encoding="utf-8") as fh:
            self.assertNotIn("手动处罚", fh.read())
        with open(os.path.join(self.ws, ".gitignore"), encoding="utf-8") as fh:
            self.assertIn("context/private/", fh.read())

    # 例 6 / 红队 9:「明确不做」进结构化禁用清单
    def test_deny_list_structured(self):
        self.confirm_ring1()
        for r_ in range(2, 6):
            run(["show", "--ring", str(r_)], self.tmp)
        r = run(["answer", "--ring", "5", "--set", "deny_topics=Reddit 外链、站群",
                 "--quote", "别再建议我们去做 Reddit 外链了,站群也不做"], self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual([d["item"] for d in self.prof()["deny"]], ["Reddit 外链", "站群"])


class LifecycleStageTests(unittest.TestCase):
    """阶段判定,期望值来自需求卡第 1 节阶段表的「怎么判断」一列。"""

    def stage_of(self, signals, metrics=None, events=None):
        tmp = tempfile.mkdtemp(prefix="lc_test_")
        self.addCleanup(shutil.rmtree, tmp, True)
        if events:
            os.makedirs(os.path.join(tmp, "context"))
            with open(os.path.join(tmp, "context", "profile.json"), "w", encoding="utf-8") as f:
                json.dump({"events": events, "rings": {}}, f)
        d = LC.diagnose({"signals": signals, "facts": []}, tmp, metrics)
        return d["stage"]["stage"]

    def test_idea_no_site_no_routes(self):
        self.assertEqual(self.stage_of({"site_live": False, "repo_public_routes": 0}), 0)

    def test_prelaunch_repo_routes_no_site(self):
        self.assertEqual(self.stage_of({"site_live": False, "repo_public_routes": 6}), 1)

    def test_prelaunch_site_blocked(self):
        self.assertEqual(self.stage_of({"site_live": True, "robots_block_all": True}), 1)

    def test_launched_low_impressions(self):
        self.assertEqual(self.stage_of({"site_live": True}, {"gsc_impressions_28d": 400, "gsc_clicks_28d": 9,
                                                             "gsc_clicks_prev_28d": 5}), 2)

    def test_growth_clicks_up(self):
        self.assertEqual(self.stage_of({"site_live": True, "first_seen": "2024-01-01"},
                                       {"gsc_impressions_28d": 50000, "gsc_clicks_28d": 1200,
                                        "gsc_clicks_prev_28d": 1000}), 3)

    def test_mature_clicks_down(self):
        self.assertEqual(self.stage_of({"site_live": True, "first_seen": "2019-01-01"},
                                       {"gsc_impressions_28d": 90000, "gsc_clicks_28d": 850,
                                        "gsc_clicks_prev_28d": 1000}), 4)

    def test_change_event_wins(self):
        self.assertEqual(self.stage_of({"site_live": True}, None, ["migration"]), 5)

    def test_no_gsc_is_a_guess(self):
        d = LC.diagnose({"signals": {"site_live": True, "url_count": 3000}, "facts": []})
        self.assertEqual(d["stage"]["confidence"], "guess")
        self.assertTrue(d["stage"]["candidates"])

    def test_missing_evidence_is_unknown_not_zero(self):
        # data/lifecycle.json about:某一级缺证据就停在下面一级并列出缺什么,不当成 0
        d = LC.diagnose({"signals": {"site_live": True, "robots_block_all": False}, "facts": []})
        g = d["maturity"]["geo"]
        self.assertEqual((g["level"], g["status"]), (1, "partial"))
        self.assertIn("signals.has_llms_txt", g["missing"])

if __name__ == "__main__":
    unittest.main()
