#!/usr/bin/env python3
"""B61 回归(S4,2026-10-21):content_score.py / text_metrics.py / pseo_batch_gate.py 各自的
wc() 与 site_audit.wc(B47 已修)同口径:天城体 matra(Mc)/virama(Mn)附着在词内不断词,
非 ASCII 字母也算词;英文 ASCII 计数不变;CJK 仍逐字计。
修前:content_score 在 matra 处断词(「बेस्ट लैपटॉप कैसे खरीदें」>4),text_metrics 与
pseo_batch_gate 只认 ASCII(计 0)。合成文本。"""
import os
import subprocess
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)
import content_score  # noqa: E402
import pseo_batch_gate  # noqa: E402
import site_audit  # noqa: E402
import text_metrics  # noqa: E402

HI = "बेस्ट लैपटॉप कैसे खरीदें"
CASES = {
    HI: 4,
    "How to buy the best laptop in 2026, it's easy": 10,
    "最好的笔记本 laptop": 7,
    "Привет мир": 2,
    "मूल्य ₹45,000 है": 4,        # 2 个天城体词 + 数字 45、000 两段(逗号断词,₹ 不计)
}


class WordCountParity(unittest.TestCase):
    def test_hindi_four_words_all_scripts(self):
        for mod in (content_score, text_metrics, pseo_batch_gate):
            with self.subTest(mod=mod.__name__):
                self.assertEqual(mod.wc(HI), 4)

    def test_matches_site_audit(self):
        for text in CASES:
            want = site_audit.wc(text)
            for mod in (content_score, text_metrics, pseo_batch_gate):
                with self.subTest(mod=mod.__name__, text=text):
                    self.assertEqual(mod.wc(text), want)

    def test_english_unchanged(self):
        # 不含撇号的 ASCII 英文三脚本修前修后都是 13;"it's" 在 pseo 修前计 2,
        # 现与 site_audit 对齐计 1(撇号附着在词内),见 test_matches_site_audit
        en = "How to buy the best laptop in 2026, a quick guide for teams"
        for mod in (content_score, text_metrics, pseo_batch_gate):
            with self.subTest(mod=mod.__name__):
                self.assertEqual(mod.wc(en), 13)
        self.assertEqual(pseo_batch_gate.wc("snake_case token"), 2)   # 下划线连词旧口径保留

    def test_text_metrics_cli_hindi(self):
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "text_metrics.py"),
                            "--market", "hi"], input=HI, capture_output=True, text=True,
                           encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        self.assertIn("词数(CJK感知): 4", r.stderr)


if __name__ == "__main__":
    unittest.main()
