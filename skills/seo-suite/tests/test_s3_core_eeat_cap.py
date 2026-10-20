#!/usr/bin/env python3
"""B40 core_eeat veto 封顶回归(stdlib unittest,合成文档,零网络)。

期望值来源:aaron-he-zhu/seo-geo-claude-skills `references/auditor-runbook.md` §2
(Runbook 1.2,2026-10-21 打开核对):
- 一项 veto 失败 → 总分 min(raw, 60),cap_applied=true;cap 是上限不是下限。
- 两项以上 veto 失败 → status BLOCKED,不出封顶后的分数(final 省略),raw 保留备查。
修前:脚本按 59 封顶,且多 veto 照样出一个 ≤59 的分数。
用法: python3 tests/test_s3_core_eeat_cap.py(tests/run_tests.py 自动发现本文件)"""
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import core_eeat as ce  # noqa: E402

SPONSOR = "\n本内容由 Acme 赞助。\n"   # 只命中 V1(利益关系)


def run_cli(text):
    f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    f.write(text)
    f.close()
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, "core_eeat.py"), f.name],
                              capture_output=True, text=True, encoding="utf-8", env=env)
    finally:
        os.unlink(f.name)


class SingleVetoCapTests(unittest.TestCase):
    def test_single_veto_caps_at_60(self):
        res = ce.analyze(ce.load_document_from_string(ce.GOOD_DOC + SPONSOR))
        self.assertEqual(len(res["vetoes"]), 1)
        sc = ce.score(res)
        self.assertGreater(sc["raw_total"], 60)          # 好文档原始分高于上限
        self.assertEqual(sc["total"], 60.0)              # Runbook §2:封顶 60(修前 59)
        self.assertTrue(sc["capped"])
        self.assertEqual(sc["status"], "DONE")

    def test_cli_shows_cap_60(self):
        r = run_cli(ce.GOOD_DOC + SPONSOR)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("总分 = 60.0", r.stdout)
        self.assertIn("封顶 60", r.stdout)
        self.assertNotIn("封顶 59", r.stdout)


class MultiVetoBlockedTests(unittest.TestCase):
    def test_two_plus_vetoes_blocked_no_final_score(self):
        res = ce.analyze(ce.load_document_from_string(ce.BAD_DOC))
        self.assertGreaterEqual(len(res["vetoes"]), 2)
        sc = ce.score(res)
        self.assertEqual(sc["status"], "BLOCKED")
        self.assertIsNone(sc["total"])                   # final_overall_score 省略
        self.assertIsNone(sc["band"])
        self.assertFalse(sc["capped"])                   # Runbook:BLOCKED 时 cap_applied=false
        self.assertIsNotNone(sc["raw_total"])            # raw 保留备查

    def test_cli_blocked_wording(self):
        r = run_cli(ce.BAD_DOC)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("BLOCKED", r.stdout)
        self.assertIn("人工复核", r.stdout)


if __name__ == "__main__":
    unittest.main()
