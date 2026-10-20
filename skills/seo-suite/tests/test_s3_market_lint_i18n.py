#!/usr/bin/env python3
"""B48 / B50 market_lint.py 回归(stdlib unittest,合成印地语/土耳其语正文,零网络)。

期望值来源:
- B48 印度数字分组:三位一组之后按两位一组(lakh/crore),1 lakh = 1,00,000;所以 123456 在印度
  写作 1,23,456,写成 123,456 是西式分组(脚本自身规则文案「lakh/crore 口径应为 1,23,456.78」)。
  不足 1 lakh 的数(12,345)两种写法相同,不判。修前只认 7 位以上西式分组,₹123,456 漏报。
- B50 土耳其语大小写:Unicode SpecialCasing.txt 的 tr 条件映射 İ→i、I→ı;默认 casefold 把 İ 变成
  i + U+0307(组合点),与 markets.json 的营销词 `en iyi` 对不上。正文 11 处 `EN İYİ` 应计 11。
用法: python3 tests/test_s3_market_lint_i18n.py(tests/run_tests.py 自动发现本文件)"""
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")


def lint(market, content, *extra):
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "market_lint.py"),
                            "--market", market, *extra, f.name],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        return r.stdout
    finally:
        os.unlink(f.name)


def lakh_line(out):
    return [ln for ln in out.splitlines() if "lakh/crore" in ln][0]


HI_BODY = "लैपटॉप की कीमत %s है। यह अच्छा लैपटॉप है और इसकी बैटरी लंबी चलती है।\n"


class HindiLakhGroupingTests(unittest.TestCase):
    def test_six_digit_western_grouping_flagged(self):
        line = lakh_line(lint("hi", HI_BODY % "₹123,456", "--report"))
        self.assertIn("AUTO-FAIL", line)
        self.assertIn("123,456", line)

    def test_indian_grouping_ok(self):
        line = lakh_line(lint("hi", HI_BODY % "₹1,23,456", "--report"))
        self.assertIn("AUTO-OK", line)
        self.assertIn("1,23,456", line)

    def test_crore_indian_ok_and_western_flagged(self):
        self.assertIn("AUTO-OK", lakh_line(lint("hi", HI_BODY % "₹1,23,45,678", "--report")))
        self.assertIn("AUTO-FAIL", lakh_line(lint("hi", HI_BODY % "₹12,345,678", "--report")))

    def test_below_one_lakh_not_judged(self):
        line = lakh_line(lint("hi", HI_BODY % "₹12,345", "--report"))
        self.assertIn("AUTO-OK", line)
        self.assertNotIn("西方分组", line)


class TurkishMarketingCaseTests(unittest.TestCase):
    def test_uppercase_dotted_i_counted(self):
        body = "Laptop rehberi\n" + "EN İYİ fiyat burada. " * 11 + "\n"
        out = lint("tr", body)
        self.assertIn("营销词命中 11", out)

    def test_mixed_case_forms_counted(self):
        body = "Laptop rehberi\nEN İYİ fiyat. En iyi servis. en iyi destek.\n"
        out = lint("tr", body)
        self.assertIn("营销词命中 3", out)

    def test_uppercase_tanitim_detected(self):
        # 同类修:TANITIM 大写按土耳其规则折叠为 tanıtım(修前 .lower() 得 tanitim,漏检)
        html = ('<html><body><p>TANITIM YAZISI: <a href="https://x.example">link</a></p>'
                '</body></html>')
        f = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
        f.write(html)
        f.close()
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        try:
            out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "market_lint.py"),
                                  "--market", "tr", "--report", f.name],
                                 capture_output=True, text=True, encoding="utf-8", env=env).stdout
        finally:
            os.unlink(f.name)
        self.assertNotIn("未见 tanıtım", out)
        self.assertIn("无 rel=sponsored", out)


if __name__ == "__main__":
    unittest.main()
