#!/usr/bin/env python3
"""did_attribution EPOCH_END(B36)与 health_score duplicate_description(B37)回归测试。

期望值来源:
- B36:Google Search Console「Data anomalies in Search Console」(support.google.com/webmasters/
  answer/6211453,2026-10-21 读取)2026「April 3」条:logging error「from May 13, 2025 until
  April 27, 2026」,只影响 impressions 及 CTR、平均排名。→ 断代窗口 2025-05-13 ~ 2026-04-27。
- B37:bug 卡「规则表列了 duplicate_description,没有实现——实现或从规则表删掉」;
  site_audit --json 的 meta 只给 desc_len(长度串),没有描述原文,无从判重 → 删掉。
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import did_attribution as da  # noqa: E402
import health_score as hs  # noqa: E402


class EpochTests(unittest.TestCase):
    def test_epoch_bounds_match_gsc_anomaly_page(self):
        self.assertEqual(da.EPOCH_START, date(2025, 5, 13))
        self.assertEqual(da.EPOCH_END, date(2026, 4, 27))           # 修前 2026-04-30

    def test_window_after_fix_date_not_flagged(self):
        hit, _ = da.overlaps_epoch((date(2026, 4, 28), date(2026, 5, 20)))
        self.assertFalse(hit)                                        # 修前 True
        hit, _ = da.overlaps_epoch((date(2026, 4, 27), date(2026, 5, 20)))
        self.assertTrue(hit)                                         # 04-27 当天仍受影响


class DuplicateDescriptionTests(unittest.TestCase):
    def _audit_file(self):
        results = {
            "https://example.com/a": {"verdict": "pass", "findings": [],
                                      "meta": {"title": "A", "desc_len": "120 chars/160"}},
            "https://example.com/b": {"verdict": "pass", "findings": [],
                                      "meta": {"title": "B", "desc_len": "120 chars/160"}},
        }
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump({"results": results}, f)
        f.close()
        return f.name

    def test_not_listed_as_rule(self):
        subs = [s for v in hs.TREE.values() for s in v]
        self.assertNotIn("duplicate_description", subs)              # 修前在规则表里但无实现

    def test_not_in_rendered_report(self):
        p = self._audit_file()
        out = io.StringIO()
        old = sys.argv
        sys.argv = ["health_score.py", "--input", p]
        try:
            with contextlib.redirect_stdout(out):
                try:
                    hs.main()
                except SystemExit:
                    pass
        finally:
            sys.argv = old
            os.unlink(p)
        self.assertIn("uniqueness", out.getvalue())
        self.assertNotIn("duplicate_description", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
