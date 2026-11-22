#!/usr/bin/env python3
"""二次补跑记下的回归:教规则、加检查的流程里,要用户拍板的确认照常编号问、停下;顺带的待办才写成陈述句
(stdlib unittest,零外网,本机起一个临时站点)。

期望值的来源(不从实现反推):
- 二次补跑转录:`check try` 的输出只说「问对不对」,`rule add` 输出末尾的收尾句写着「不编号、不问要不要补」;
  被测把试跑结果贴出来以后问「**请确认**:这样判对不对?对的话回「对」或「启用」」,没编号。对方没把这当成停下来问,
  这一段就结束了,检查一直没启用,每周运营单也没跑它。
- SKILL.md 启动协议:提问是「列编号问题后结束回合」;上一次修复要保留的:规则碰到的现有页面、试跑没过的页面
  写成陈述句的待办,不编号、不问要不要补。
- 同一份转录:用户原话是「别再建议我们去做 Reddit 外链了，我们不做」(全角逗号),记进 rules.md 的却是半角逗号
  (被测照着说明里的例句抄了)。原话要逐字记下。
站点、品牌都是合成的。
"""
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_onboarding_regressions_b5c import P, Repo, make_site, run  # noqa: E402

DENY_QUOTE = "别再建议我们去做 Reddit 外链了，我们不做"
PAGES = {"platforms/index.html": P % ("Platforms", "Platforms", "All platforms"),
         "platforms/alpha/index.html": P % ("Alpha", "Alpha", "POST /mcp tools/call example"),
         "platforms/beta/index.html": P % ("Beta", "Beta", "No example yet"),
         "platforms/gamma/index.html": P % ("Gamma", "Gamma", "tools/call sample request")}


class TeachConfirmTests(unittest.TestCase):
    def setUp(self):
        self.repo = Repo(self)
        os.makedirs(self.repo.ws)

    def teach(self, *args):
        r = run("teach.py", [*args, "--ws", self.repo.ws], self.repo.dir)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def assert_closing_note(self, out):
        self.assertIn("不编号、不问要不要补", out)          # 上一次修复:顺带的待办写陈述句
        self.assertIn("照常编号问", out)                   # 这一次:要拍板的事照常编号问

    def test_check_try_asks_a_numbered_question_and_stops(self):
        base = make_site(self, pages=PAGES)
        self.teach("check", "new", "mcp-example", "--desc", "每个平台页都要有 MCP 调用示例",
                   "--pattern", "tools/call", "--match", "/platforms/")
        urls = [a for p in ("alpha", "beta", "gamma") for a in ("--url", "%s/platforms/%s/" % (base, p))]
        out = self.teach("check", "try", "mcp-example", "--allow-local", *urls)
        line = next(ln for ln in out.splitlines() if "check enable" in ln)
        self.assertIn("编号问", line)
        self.assertIn("停下等回复", line)
        ask = re.search(r"「(1\. [^」]*[?？][^」]*)」", line)
        self.assertTrue(ask, line)                         # 给的问法本身就是一条编号问题
        out = self.teach("check", "enable", "mcp-example", "--quote", "结果对,启用吧。")
        self.assert_closing_note(out)

    def test_rule_add_keeps_decisions_numbered(self):
        out = self.teach("rule", "add", "--quote", "以后每篇教程都要放一段能直接复制运行的代码", "--no-deny")
        self.assert_closing_note(out)

    def test_rule_quote_is_stored_verbatim(self):
        out = self.teach("rule", "add", "--quote", DENY_QUOTE, "--deny", "reddit")
        self.assertIn("逐字", out)
        with open(os.path.join(self.repo.ws, "playbook", "rules.md"), encoding="utf-8") as f:
            self.assertIn("「%s」" % DENY_QUOTE, f.read())


if __name__ == "__main__":
    unittest.main()
