#!/usr/bin/env python3
"""B41 / B54 llmstxt.py validate 回归(stdlib unittest,合成 llms.txt,零网络)。

期望值来源:
- llmstxt.org v2 规范(2026-10-21 打开核对)Format 节:文件按序为「可选 BOM → H1(唯一必需)
  → blockquote → …」。所以开头的 BOM 合法,不能因此判缺 H1 或判水印字符。
- 脚本自身规则「非绝对 URL」+ references/content/llms-txt-guide.md「链接用绝对 URL」:
  `/docs/x.md`、`#anchor` 这类相对链接要报出来(修前 startswith(("http","/","#")) 放过)。
- B54:缺 H1 的文件不得同时打印「H1 ✓」。
用法: python3 tests/test_s3_llmstxt_validate.py(tests/run_tests.py 自动发现本文件)"""
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")

GOOD = ("# Acme Docs\n\n> Acme API reference.\n\n## Docs\n\n"
        "- [Start](https://acme.example/docs/start.md): intro\n"
        "- [Auth](https://acme.example/docs/auth.md): keys\n"
        "- [Errors](https://acme.example/docs/errors.md): codes\n")


def validate(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, "llmstxt.py"), "validate", f.name],
                              capture_output=True, text=True, encoding="utf-8", env=env)
    finally:
        os.unlink(f.name)


class RelativeLinkTests(unittest.TestCase):
    def test_root_relative_link_flagged(self):
        r = validate(GOOD + "- [Rel](/docs/rate-limits.md): limits\n")
        self.assertIn("非绝对 URL", r.stdout)
        self.assertIn("/docs/rate-limits.md", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_fragment_link_flagged(self):
        r = validate(GOOD + "- [Here](#auth): same page\n")
        self.assertIn("非绝对 URL", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_absolute_links_pass(self):
        r = validate(GOOD)
        self.assertNotIn("非绝对 URL", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)


class BomTests(unittest.TestCase):
    def test_leading_bom_is_allowed(self):
        r = validate("﻿" + GOOD)
        self.assertNotIn("缺 H1", r.stdout)
        self.assertNotIn("水印", r.stdout)
        self.assertIn("H1 ✓", r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_missing_h1_never_prints_h1_ok(self):
        r = validate("> summary only\n\n- [a](https://x.example/a): d\n"
                     "- [b](https://x.example/b): d\n- [c](https://x.example/c): d\n")
        self.assertIn("缺 H1", r.stdout)
        self.assertNotIn("H1 ✓", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_bom_in_middle_still_flagged(self):
        r = validate(GOOD + "extra﻿text\n")
        self.assertIn("水印", r.stdout)


if __name__ == "__main__":
    unittest.main()
