#!/usr/bin/env python3
"""trust_signals.py 风险反转词表与建议文案回归测试(B32;合成页面,fetch 打桩,零网络)。

期望值来源:bug 卡 B32——API/按量计费产品真实的风险反转说法是「失败不扣费 / 按成功计费 /
not charged for failed calls / pay only for successful / refund」,词表要认得;建议文案不得
诱导站长写可能不真实的承诺(无需信用卡、随时取消、保证),改为「写出你真实提供的风险反转」。
"""
import contextlib
import io
import os
import sys
import unittest
from unittest import mock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import trust_signals as ts  # noqa: E402


class RiskVocabularyTests(unittest.TestCase):
    def test_english_pay_for_success_phrases(self):
        text = ("You are not charged for failed calls. Pay only for successful requests. "
                "Unused balance can be refunded on request.")
        score, detail, hits = ts.score_risk(text)
        self.assertGreaterEqual(len(hits), 2, detail)                       # 修前 0 类
        self.assertGreater(score, 0)

    def test_chinese_pay_for_success_phrases(self):
        score, detail, hits = ts.score_risk("调用失败不扣费,按成功计费;余额可申请退款。")
        self.assertGreaterEqual(len(hits), 2, detail)                       # 修前 0 类


class AdviceTextTests(unittest.TestCase):
    def _run(self, html):
        out = io.StringIO()
        with mock.patch.object(ts, "fetch", lambda url, timeout=15.0: (200, url, html.encode())):
            with contextlib.redirect_stdout(out):
                ts.main(["https://example.com/"])
        return out.getvalue()

    def test_advice_does_not_push_unverified_promises(self):
        out = self._run("<html><body><h1>Example API</h1><p>Plain page.</p></body></html>")
        tip = next(ln for ln in out.splitlines() if "风险反转" in ln and ln.strip().startswith("-"))
        for bad in ("no credit card", "cancel anytime", "guarantee", "无需信用卡", "随时取消", "保证"):
            self.assertNotIn(bad, tip)                                      # 修前列出这几项为「缺」
        self.assertIn("真实", tip)


if __name__ == "__main__":
    unittest.main(verbosity=2)
