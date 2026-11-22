#!/usr/bin/env python3
"""开局流程第 5 批修复后检查跑记下的回归,逐条单测(stdlib unittest,零外网;本机回环上起临时站)。

期望值的来源(不从实现反推):
- 检查跑转录里的真实输入:站点有 /shop/<x>、/gear/<x> 两个带子页的目录,栏目页大标题是「Shop coffee beans」
  「Brewing gear」,首页大标题是一句卖点「Fresh single-origin coffee, roasted to order」;脚本草稿把产品线写成
  目录名「Shop、Gear」,用户回「Yes … The subscription is the most important line」,档案里记成了 Shop,
  判分要的是说得出卖什么(咖啡豆)的名字。被测先试了 `answer --add product.lines=Subscription`(脚本不认),
  三次把第 5 环的问题 id 写成 market(脚本只认 market_first)。
- 用户教的规则「以后我们的对比文都要放一张价格对照表」(适用 brief、plan、weekly);方案里「对比页和替代页」
  那一项的做法没带这条规则,只在方案末尾单列。
- 第 6 环用户确认、方案定稿之后,被测为了看一眼又跑了 `plan.py build`,定稿方案被换成草稿。
- 本轮修复清单写明的行为:候选产品线的名字先取栏目页大标题,像一句话或读不到就用目录名;规则点到哪条路线项,
  原话写进那一项的做法;定稿方案不加 --replan 不重排;`answer --add` 往列表字段加一项;问题 id 只差后缀时代填。
站点、品牌都是合成的。
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import product_scan  # noqa: E402
from test_onboarding_regressions_b5c import HOME, P, RULE_Q, Repo, block_of, make_site, run  # noqa: E402

PAGES = {"shop/index.html": P % ("Shop single-origin coffee beans", "Shop coffee beans", "All coffees"),
         "shop/ethiopia/index.html": P % ("Ethiopia", "Ethiopia", "12 oz bag $24. Add to cart"),
         "shop/kenya/index.html": P % ("Kenya", "Kenya", "12 oz bag $26. Add to cart"),
         "gear/index.html": P % ("Pour-over brewing gear", "Brewing gear", "Kits and filters"),
         "gear/starter-kit/index.html": P % ("Starter kit", "Starter kit", "Kit $45. Add to cart"),
         "subscription/index.html": P % ("Subscription", "The coffee subscription", "One bag a month for $22/month"),
         "about/index.html": P % ("About", "About", "We roast in small batches")}


def lines_row(block):
    return next(ln for ln in block.splitlines() if ln.startswith("- 产品线:"))


class SectionNameTests(unittest.TestCase):
    def test_candidate_lines_take_section_page_heading(self):
        """草稿里的候选产品线写栏目页的大标题(说得出卖什么),不是光秃秃的目录名。"""
        repo = Repo(self)
        row = lines_row(block_of(repo.start(make_site(self, pages=PAGES))))
        self.assertIn("Shop coffee beans", row)
        self.assertIn("Brewing gear", row)
        self.assertIn("推测", row)
        lines = next(f for f in repo.profile()["facts"] if f["key"] == "product.lines")["value"]
        self.assertEqual(sorted(lines), ["Brewing gear", "Shop coffee beans"])

    def test_sentence_heading_falls_back_to_directory_name(self):
        """栏目页大标题是一句卖点(带逗号)时不拿来当名字,退回目录名。"""
        pages = dict(PAGES, **{"shop/index.html": P % ("Shop", "Fresh single-origin coffee, roasted to order", "x")})
        row = lines_row(block_of(Repo(self).start(make_site(self, pages=pages))))
        self.assertIn("Shop", row)
        self.assertNotIn("roasted to order", row)
        self.assertIn("Brewing gear", row)

    def test_same_heading_on_two_sections_falls_back(self):
        heads = {"shop": {"h1": "Our store"}, "gear": {"h1": "Our store"}}
        self.assertEqual(sorted(product_scan.section_lines(["/shop/a/", "/gear/b/"], None, heads)), ["Gear", "Shop"])


class AnswerArgsTests(unittest.TestCase):
    def setUp(self):
        self.repo = Repo(self)
        self.repo.start(make_site(self, pages=PAGES))
        self.quote = ("Yes. What matters most is subscription starts, one-off bags come second. "
                      "The subscription is the most important line.")

    def test_add_appends_one_line_and_keeps_the_rest(self):
        r = self.repo.ob("answer", "--ring", "1", "--set", "main_line=Subscription", "--add",
                         "product.lines=Subscription", "--quote", self.quote)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        lines = next(f for f in self.repo.profile()["facts"] if f["key"] == "product.lines")["value"]
        self.assertEqual(lines[-1], "Subscription")
        self.assertEqual(sorted(lines[:-1]), ["Brewing gear", "Shop coffee beans"])

    def test_add_on_scalar_key_is_refused(self):
        r = self.repo.ob("answer", "--ring", "1", "--add", "pricing.model=Monthly", "--quote", self.quote)
        self.assertEqual(r.returncode, 2, r.stderr + r.stdout)
        self.assertIn("--correct pricing.model", r.stderr + r.stdout)

    def test_question_id_missing_suffix_is_filled_in(self):
        r = self.repo.ob("answer", "--ring", "1", "--set", "main=Subscription", "--quote", self.quote)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("main_line", r.stdout)
        self.assertEqual(self.repo.profile()["rings"]["1"]["answers"].get("main_line"), "Subscription")


class PlanWs(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="b5d_plan_"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        scan = {"schema": 1, "site": "https://acme.example",
                "signals": {"site_live": True, "robots_block_all": False, "homepage_noindex": False, "url_count": 1200,
                            "first_seen": "2025-06-01", "has_llms_txt": True},
                "site_scan": {"page_types": {"pricing": 1, "docs": 30, "blog": 40, "compare": 2}},
                "facts": [{"key": "product.name", "value": "Acme", "source": "https://acme.example/", "kind": "fact"},
                          {"key": "product.lines", "value": ["Invoices", "Expenses"], "source": "llms.txt",
                           "kind": "inferred"},
                          {"key": "market.languages", "value": ["en"], "source": "hreflang", "kind": "fact"}],
                "errors": []}
        with open(os.path.join(self.tmp, "scan.json"), "w", encoding="utf-8") as f:
            json.dump(scan, f)
        self.ws = os.path.join(self.tmp, "seo-ops")
        self.ob("start", "--site", "https://acme.example", "--scan", "scan.json", "--market", "en")
        self.ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册", "--set",
                "customers=小团队", "--set", "main_line=Invoices", "--quote", "都对,要注册,客户是小团队,先做发票",
                "--confirm")
        self.ob("skip", "--quote", "跳过,直接出方案")

    def ob(self, *a):
        r = run("onboard.py", list(a) + ["--ws", self.ws] if a[0] != "start" else list(a), self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r

    def build(self, *extra):
        r = run("plan.py", ["build", "--ws", self.ws, *extra], self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r.stdout

    def plan(self):
        with open(os.path.join(self.ws, "plan", "plan.json"), encoding="utf-8") as f:
            return json.load(f)


class PlanRuleOnItemTests(PlanWs):
    def test_rule_is_written_into_the_item_it_names(self):
        """规则说的是对比文:方案里做对比页的那一项,做法里带规则原话;不相干的项不带。"""
        r = run("teach.py", ["rule", "add", "--quote", RULE_Q, "--no-deny", "--applies", "brief,plan,weekly",
                             "--ws", self.ws], self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.build()
        plan = self.plan()
        items = plan["items"] + plan["more"]
        compare = [it for it in items if "对比页" in (it.get("page_types") or [])]
        self.assertTrue(compare, [it["id"] for it in items])
        for it in compare:
            self.assertIn(RULE_Q, it["do"], it["id"])
            self.assertIn(RULE_Q, it["do_en"], it["id"])
            self.assertEqual([n["id"] for n in it["rule_notes"]], ["R1"])
        other = [it for it in items if it.get("theme") == "measure"]
        self.assertTrue(other)
        for it in other:
            self.assertNotIn(RULE_Q, it["do"], it["id"])
        with open(os.path.join(self.ws, "plan", "roadmap.md"), encoding="utf-8") as f:
            road = f.read()
        self.assertGreaterEqual(road.count(RULE_Q), 2)       # 那一项里一次,「按你的规则」一节一次


class ApprovedPlanTests(PlanWs):
    def approve(self):
        path = os.path.join(self.ws, "plan", "plan.json")
        plan = self.plan()
        plan.update({"status": "approved", "approved_at": "2026-11-22T01:37:10Z",
                     "approved_quote": "Looks good. Target: 30 new subscriptions a month."})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(plan, f, ensure_ascii=False, indent=1)
        return plan

    def test_build_again_leaves_approved_plan_alone(self):
        self.build()
        before = self.approve()
        out = self.build()
        self.assertIn("已定稿", out)
        self.assertIn("--replan", out)
        self.assertEqual(self.plan(), before)

    def test_replan_goes_back_to_draft_and_keeps_the_old_quote(self):
        self.build()
        self.approve()
        out = self.build("--replan")
        plan = self.plan()
        self.assertEqual(plan["status"], "draft")
        self.assertEqual(plan["previous_approved"]["approved_quote"], "Looks good. Target: 30 new subscriptions a month.")
        self.assertIn("等确认", out)


if __name__ == "__main__":
    unittest.main()
