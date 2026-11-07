#!/usr/bin/env python3
"""ste_lint.py 测试(stdlib unittest,合成文本,零网络)。

期望值来源:ASD-STE100 Issue 9 的规则条件(规则编号与数字的出处见
references/content/asd-ste100-web-writing.md 第二节):程序句 ≤20 词(5.1)、描述句 ≤25 词(6.3)、
括号内文本算 1 词(8.5)、带单位的数字算 1 词(8.6,按 TechScribe 举例)、连字符词算 1 词(8.7)、
被动语态(3.6;"The wires are disconnected." 是 3.3 的歧义例,只能提示、不能判 FAIL)、
缩写形式(4.2)、分号(8.1)、术语一致(1.11、9.4)。用例按规则条件构造,不按实现反推。
用法: python3 tests/test_ste_lint.py(tests/run_tests.py 自动发现本文件)"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import ste_lint  # noqa: E402


def rules(rep, rule=None):
    return [f for f in rep["findings"] if rule is None or f["rule"] == rule]


def proc(n_words):
    """一个祈使句,正好 n_words 个词(Send + 若干 data)。"""
    return "Send " + " ".join(["data"] * (n_words - 1)) + "."


def desc(n_words):
    """一个描述句,正好 n_words 个词(The + 若干 system)。"""
    return "The " + " ".join(["system"] * (n_words - 1)) + "."


class SentenceLengthTests(unittest.TestCase):
    def test_procedure_20_ok_21_fail(self):                     # STE 5.1
        self.assertEqual(rules(ste_lint.lint(proc(20)), "STE-LEN-P"), [])
        r = rules(ste_lint.lint(proc(21)), "STE-LEN-P")
        self.assertEqual(len(r), 1)
        self.assertEqual((r[0]["severity"], r[0]["measured"], r[0]["limit"]), ("FAIL", 21, 20))

    def test_description_25_ok_26_fail(self):                   # STE 6.3
        self.assertEqual(rules(ste_lint.lint(desc(25)), "STE-LEN-D"), [])
        r = rules(ste_lint.lint(desc(26)), "STE-LEN-D")
        self.assertEqual((r[0]["severity"], r[0]["measured"]), ("FAIL", 26))

    def test_parenthesized_text_counts_as_one_word(self):        # STE 8.5
        s = "Send " + " ".join(["data"] * 17) + " (this counts as one)."
        self.assertEqual(ste_lint.count_words_en(s), 19)
        self.assertEqual(rules(ste_lint.lint(s), "STE-LEN-P"), [])

    def test_hyphenated_word_counts_as_one(self):                # STE 8.7
        s = "Send " + " ".join(["data"] * 18) + " built-in."
        self.assertEqual(ste_lint.count_words_en(s), 20)

    def test_number_with_unit_counts_as_one(self):               # STE 8.6(TechScribe 举例)
        s = "Send " + " ".join(["data"] * 18) + " 10 MB."
        self.assertEqual(ste_lint.count_words_en(s), 20)

    def test_ordered_list_item_is_procedure(self):
        md = "1. " + desc(21)       # 句首不是祈使动词,但在有序列表里 → 程序句,21 词超 20
        r = rules(ste_lint.lint(md), "STE-LEN-P")
        self.assertEqual(len(r), 1)


class StyleRuleTests(unittest.TestCase):
    def test_adjectival_passive_is_hint_not_fail(self):          # STE 3.3 歧义例
        r = rules(ste_lint.lint("The wires are disconnected."), "STE-PASSIVE")
        self.assertEqual(len(r), 1)
        self.assertNotEqual(r[0]["severity"], "FAIL")

    def test_contraction_and_semicolon(self):                    # STE 4.2、8.1
        rep = ste_lint.lint("Do not open the file; it isn't ready.")
        self.assertTrue(rules(rep, "STE-CONTR"))
        self.assertTrue(rules(rep, "STE-SEMI"))

    def test_paragraph_more_than_six_sentences(self):             # STE 段落规则
        para = " ".join(desc(5) for _ in range(7))
        r = rules(ste_lint.lint(para), "STE-PARA")
        self.assertEqual((r[0]["severity"], r[0]["measured"]), ("FAIL", 7))

    def test_chinese_passive_and_then(self):                     # 中文为本套件口径
        rep = ste_lint.lint("1. 点击「设置」，然后选择「导出」。\n\n文件被系统删除。", lang="zh")
        self.assertTrue(rules(rep, "STE-ONE"))
        self.assertTrue(rules(rep, "STE-PASSIVE"))


class HtmlInputTests(unittest.TestCase):
    def test_head_title_and_inline_code_are_not_body_text(self):
        # <title> 不是正文(网页标题按 title 规则另查);行内 <code> 里的分号是代码,不算 STE 8.1
        html = ("<html><head><title>Broken; a title that is far too long to be a sentence anyway ok</title>"
                "</head><body><p>Use <code>a; b</code> in the call.</p></body></html>")
        rep = ste_lint.lint(html)
        self.assertEqual(rules(rep, "STE-SEMI"), [])
        self.assertEqual(rules(rep, "STE-LEN-D"), [])

    def test_term_variant_after_article_is_found(self):           # STE 9.4;「The API key」不被「The API」吞掉
        rep = ste_lint.lint("<p>Create the API key. Copy the API-key to the server.</p>")
        tv = rules(rep, "STE-TERM-VAR")
        self.assertEqual(len(tv), 1)
        self.assertIn("API-key", tv[0]["excerpt"])


class GlossaryAndCliTests(unittest.TestCase):
    def test_forbidden_variant_is_fail(self):                    # STE 1.11、9.4
        gl = [("api key", "API key", ["api-key", "apikey"])]
        rep = ste_lint.lint("Create an API key. Copy the api-key to the server.", glossary=gl)
        r = rules(rep, "STE-TERM")
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["severity"], "FAIL")

    def test_cli_json_exit_codes_and_no_compliance_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok = os.path.join(tmp, "ok.txt")
            bad = os.path.join(tmp, "bad.txt")
            with open(ok, "w", encoding="utf-8") as f:
                f.write(proc(10) + "\n")
            with open(bad, "w", encoding="utf-8") as f:
                f.write(proc(25) + "\n")
            run = lambda *a: subprocess.run([sys.executable, os.path.join(SCRIPTS, "ste_lint.py"), *a],
                                            capture_output=True, text=True, encoding="utf-8",
                                            env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            r_ok = run(ok, "--json")
            r_bad = run(bad)
            r_missing = run(os.path.join(tmp, "nope.txt"))
        self.assertEqual(r_ok.returncode, 0)
        self.assertEqual(json.loads(r_ok.stdout)["tool"], "ste_lint")
        self.assertNotIn("compliant", r_ok.stdout.lower())
        self.assertEqual(r_bad.returncode, 1)
        self.assertNotIn("compliant", r_bad.stdout.lower())
        self.assertEqual(r_missing.returncode, 2)


if __name__ == "__main__":
    unittest.main()
