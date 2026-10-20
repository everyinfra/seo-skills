#!/usr/bin/env python3
"""B47 / B49 / B51 / B52 / B53 多文字分词与计数回归(stdlib unittest,真实文字合成输入,零网络)。

期望值来源:
- B47 site_audit.wc:天城体用空格分词(Unicode UAX #29 词边界在空格处断开,元音符号 matra 与
  virama 属 Mark 类,附着在词内)。「बेस्ट लैपटॉप कैसे खरीदें」= 4 词(修前按码点得 21)。
  泰语不用空格分词,stdlib 没有词典分词:按空格短语计并明确标近似(修前返回字素数)。
- B49 ste_lint.is_prose:越南语、泰语、土耳其语的正文段是散文,不能当数据块跳过(修前 ASCII 正则)。
- B51 question_align.tokens:按 Unicode 字母类分词,越南 `thế` 不得截成 `th`,土耳其 `İ` 不得丢;
  泰语无空格时退化为字符二元组(与汉字同法)。
- B52 keyword_variants:đ、ł、ø 等字母 NFD 分解不掉,需显式映射(đ→d、ł→l、ø→o、ß→ss…),
  `đường`/`duong`、`łódź`/`lodz` 应同组。
- B53 text_units th:外部判据为 Node 22 `Intl.Segmenter('th',{granularity:'grapheme'})`
  (2026-10-21 本机实测):「ภาษาไทยเป็นภาษาที่สวยงาม น้ำใจ กำลัง ที่สุด」= 33 个字素
  (修前 39:U+0E31/U+0E34–0E37/U+0E47/U+0E4C 的 combining class 为 0 被当基字符;U+0E33 SARA AM
  是 SpacingMark 也要并入前字)。脚本仍不是完整 UAX #29 实现,说明必须写「近似」。
用法: python3 tests/test_s3_unicode_text.py(tests/run_tests.py 自动发现本文件)"""
import os
import subprocess
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import keyword_variants as kv   # noqa: E402
import question_align as qa     # noqa: E402
import site_audit as sa         # noqa: E402
import ste_lint                 # noqa: E402

THAI = "ภาษาไทยเป็นภาษาที่สวยงาม น้ำใจ กำลัง ที่สุด"


def run(name, args=(), stdin=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args], input=stdin,
                          capture_output=True, text=True, encoding="utf-8", env=env)


class SiteAuditWordCountTests(unittest.TestCase):
    def test_devanagari_words_by_space(self):
        self.assertEqual(sa.wc("बेस्ट लैपटॉप कैसे खरीदें"), 4)
        self.assertEqual(sa.wc("यह एक हिन्दी वाक्य है"), 5)

    def test_thai_space_phrases_marked_approx(self):
        n, approx = sa.wc_info(THAI)
        self.assertEqual(n, 4)                 # 4 个空格分隔短语
        self.assertTrue(approx)
        self.assertEqual(sa.wc(THAI), 4)

    def test_non_thai_not_approx(self):
        self.assertEqual(sa.wc_info("thời trang nam giảm giá"), (5, False))
        self.assertEqual(sa.wc_info("SEO工具で分析"), (6, False))


class SteLintProseTests(unittest.TestCase):
    def test_vietnamese_prose(self):
        self.assertTrue(ste_lint.is_prose("Bạn cần kiểm tra thiết bị trước khi sử dụng nó.", "vi"))

    def test_thai_prose(self):
        self.assertTrue(ste_lint.is_prose("คุณต้องตรวจสอบอุปกรณ์ก่อนใช้งาน กรุณาอ่านคู่มือ", "th"))

    def test_turkish_accent_dense_prose(self):
        self.assertTrue(ste_lint.is_prose("Güçlü şifreler oluşturmak için çalışmalarımızı göğüslüyoruz.", "tr"))

    def test_numeric_table_still_skipped(self):
        self.assertFalse(ste_lint.is_prose("12 34 56 78 90 1.5 2.5", "vi"))


class QuestionAlignTokenTests(unittest.TestCase):
    def test_vietnamese_word_kept_whole(self):
        toks = qa.tokens("giá thế nào")
        self.assertIn("thế", toks)
        self.assertNotIn("th", toks)
        self.assertIn("nào", toks)

    def test_turkish_dotted_i_kept(self):
        toks = qa.tokens("İstanbul otelleri")
        self.assertIn("istanbul", toks)
        self.assertEqual(qa.coverage("İstanbul otelleri", "İstanbul otelleri rehberi"), 1.0)

    def test_thai_bigrams(self):
        toks = qa.tokens("ราคาดี")
        self.assertTrue(toks)
        self.assertIn("รา", toks)
        self.assertEqual(qa.coverage("ราคาดี", "ร้านนี้ราคาดีมาก"), 1.0)


class KeywordVariantsLetterMapTests(unittest.TestCase):
    def test_vietnamese_d_stroke(self):
        self.assertEqual(kv.canon("đường")[0], kv.canon("duong")[0])

    def test_polish_l_stroke(self):
        self.assertEqual(kv.canon("łódź")[0], kv.canon("lodz")[0])

    def test_other_non_decomposable(self):
        self.assertEqual(kv.canon("København")[0], kv.canon("kobenhavn")[0])
        self.assertEqual(kv.canon("Straße")[0], kv.canon("strasse")[0])

    def test_cyrillic_and_kana_untouched(self):
        self.assertEqual(kv.canon("й")[0], "й")       # 不得把 й 去成 и
        self.assertEqual(kv.canon("が")[0], "が")

    def test_end_to_end_grouping(self):
        r = run("keyword_variants.py", stdin="đường\nduong\nłódź\nlodz\n")
        self.assertIn("4 词 → 2 组(2 处合并)", r.stdout)


class TextUnitsThaiTests(unittest.TestCase):
    def test_thai_grapheme_matches_intl_sample(self):
        r = run("text_units.py", ["th"], stdin=THAI)
        self.assertIn("value=33", r.stdout)

    def test_sibling_grapheme_units_match(self):
        import market_lint as ml
        self.assertEqual(sa.unit_len(THAI, "grapheme"), 33)    # 同类修:SARA AM 并入前字
        self.assertEqual(ml.unit_len(THAI, "grapheme"), 33)

    def test_approx_wording_locked(self):
        r = run("text_units.py", ["th"], stdin=THAI)
        self.assertIn("近似", r.stdout)
        h = run("text_units.py", ["--help"])
        self.assertIn("近似", h.stdout)
        self.assertNotRegex(h.stdout, r"与\s*Intl\S*\s*一致")   # 不得声称与 Intl 一致


if __name__ == "__main__":
    unittest.main()
