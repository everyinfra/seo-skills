#!/usr/bin/env python3
"""test_fix_multiling.py — 多语言分词断层修复回归(R5 多语言节 6 处;合成 ko/ja/th 文本,
零网络,standalone——助手照抄 test_content_score.py 顶部,被 run_tests.py 自动发现加载):
①content_score CJK_RUN 对齐 CJK_RE:纯谚文竞品术语表不再恒空 FATAL(谚文音节 bigram/
  假名 run 成 token;汉字口径逐字节不变)
②quality_rater CJK_RE/LATIN_WORD_RE 同扩:纯谚文词数不再恒 0;假名 run 进 first_100_words
③market_lint proxy_kw 按语系分支:ja 假名 run 也取;ko 谚文音节/th 泰文 run——
  纯文正文不再 proxy_kw=None(标题关键词位次不再恒 MANUAL)
④market_lint split_sents cjk/latin 两分支补全角！?
⑤market_lint th 支柱长度:words 不再用 split()(恒 1 词)——字素/4 近似并标注
⑥market_lint th newline 句切:HTML 正文折叠前按块级标签/换行切块,不再折叠后恒 1 句"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)


def run_script(name, args=(), stdin=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def tmp_file(content, suffix=".txt"):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


# ---- 合成韩文语料: 3 个不同来源纯谚文竞品 + 1 份有缺口的草稿(修复前术语表恒空→FATAL) ----
KO_KW = "프로젝트 관리"
KO_C1 = ("# 프로젝트 관리 가이드\n\n"
         "프로젝트 관리는 팀 협업의 핵심 도구입니다. 2026년 주요 도구는 40개가 넘습니다.\n\n"
         "## 일정 관리\n\n일정 관리와 자원 분배가 중요합니다.\n\n"
         "![대시보드](dash.png)\n\n[가이드](/guide)\n\n"
         "<script type=\"application/ld+json\">{\"@type\":\"Article\"}</script>\n")
KO_C2 = ("프로젝트 관리 비교: 일정 관리와 자원 분배가 주요 축입니다. "
         "자원 분배 보고서가 유료 이유입니다. 2026년 평균 좌석당 15달러입니다.\n")
KO_C3 = ("프로젝트 관리 선택 방법: 팀 규모를 먼저 확인하세요. "
         "일정 관리 도구와 자원 분배 기능이 필수입니다.\n")
KO_DRAFT = ("# 협업 도구 이야기\n\n"
            "협업 도구에는 많은 이야기가 있습니다. 여기서는 배경과 생각을 천천히 적습니다.\n")

HANGUL = re.compile(r"^[\uac00-\ud7af]+$")
NO_HAN_KANA = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff]")   # 汉字/假名不得混入


# ---------------------------------------------------------------- ① content_score
class ContentScoreCJKRunAlignmentTests(unittest.TestCase):
    """①CJK_RUN 与 CJK_RE 对齐:纯谚文不再空 token 流;谚文音节 bigram/假名 run token;
    纯汉字 bigram 口径不变(冻结 fixture 不受影响)。"""

    def test_han_bigrams_unchanged(self):
        import content_score as cs
        self.assertEqual(cs.cjk_bigrams("项目管理软件"),
                         ["项目", "目管", "管理", "理软", "软件"])   # 汉字口径逐字节不变
        self.assertEqual(cs.CJK_RUN.findall("项目管理"), ["项目管理"])

    def test_hangul_syllable_bigrams(self):
        import content_score as cs
        self.assertEqual(cs.CJK_RUN.findall("프로젝트 관리"), ["프로젝트", "관리"])
        self.assertEqual(cs.cjk_bigrams("프로젝트 관리"),
                         ["프로", "로젝", "젝트", "관리"])            # 谚文按音节 bigram
        self.assertTrue(cs.tokenize("한국어 도구 비교"))              # 纯谚文 token 流非空

    def test_kana_run_is_single_token(self):
        import content_score as cs
        self.assertEqual(cs.cjk_bigrams("プロジェクト管理ツール"),
                         ["プロジェクト", "管理", "ツール"])          # 假名 run 成 token
        # 平/片假名各成 run:片假名内容词不与平假名助词粘连(を 单假名=助词跳过)
        self.assertEqual(cs.cjk_bigrams("プロジェクトを管理する"),
                         ["プロジェクト", "管理", "する"])

    def test_extract_terms_pure_hangul_nonempty(self):
        import content_score as cs
        terms = [t["term"] for t in cs.extract_terms([KO_C2, KO_C3, KO_DRAFT])]
        self.assertTrue(terms)                                        # 修复前恒 [] → FATAL
        self.assertFalse([t for t in terms if NO_HAN_KANA.search(t)])  # 无汉字/假名混入
        self.assertTrue([t for t in terms if HANGUL.match(t)])

    def test_pure_hangul_competitors_e2e_not_fatal(self):
        import json
        a, b, c, d = (tmp_file(x, ".md") for x in (KO_C1, KO_C2, KO_C3, KO_DRAFT))
        try:
            r = run_script("content_score.py",
                           ["--draft", d, "--competitors", ",".join([a, b, c]),
                            "--keyword", KO_KW, "--json"])
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)    # 修复前 rc=2 术语表为空
            p = json.loads(r.stdout)
            self.assertGreater(p["term_model"]["n_terms"], 0)
            self.assertFalse([row for row in p["term_table"] if NO_HAN_KANA.search(row["term"])])
            self.assertTrue([row for row in p["term_table"] if HANGUL.match(row["term"])])
            self.assertTrue(any(row["importance"] == 10 for row in p["term_table"]))
        finally:
            for p2 in (a, b, c, d):
                os.unlink(p2)


# ---------------------------------------------------------------- ② quality_rater
class QualityRaterScriptExpansionTests(unittest.TestCase):
    """②CJK_RE/LATIN_WORD_RE 扩假名+谚文:纯谚文词数=0 修复;假名 run 进 first_100_words;
    汉字口径不变。"""

    def test_cjk_re_now_covers_hangul_kana(self):
        import quality_rater as qr
        self.assertTrue(qr.CJK_RE.search("한국어"))      # 谚文 \uac00-\ud7af
        self.assertTrue(qr.CJK_RE.search("テスト"))      # 假名 \u3040-\u30ff
        self.assertFalse(qr.CJK_RE.search("ABC"))

    def test_latin_word_re_includes_kana_run(self):
        import quality_rater as qr
        self.assertEqual(qr.LATIN_WORD_RE.findall("プロジェクト管理"), ["プロジェクト"])

    def test_pure_hangul_word_count_not_zero(self):
        import quality_rater as qr
        self.assertEqual(qr.cjk_words("프로젝트 관리"), 6)     # 修复前恒 0
        self.assertEqual(qr.cjk_words("项目管理软件"), 6)      # 汉字逐字口径不变

    def test_kana_run_in_first_100_words(self):
        import quality_rater as qr
        window = qr.first_100_words_text("プロジェクト管理ツールの比較")
        self.assertIn("プロジェクト", window)                  # 修复前假名整段被丢
        self.assertIn("管理", window)
        self.assertEqual(qr.first_100_words_text("项目管理软件介绍"), "项目管理软件介绍")

    def test_korean_draft_word_count_e2e(self):
        p = tmp_file("프로젝트 관리 가이드\n소프트웨어 설명\n프로젝트 관리는 팀 협업의 핵심 도구입니다.\n")
        r = run_script("quality_rater.py", [p, "--keyword", KO_KW])
        self.assertRegex(r.stdout, r"词数\(CJK 感知\): [1-9]\d*")   # 修复前恒 0
        os.unlink(p)


# ---------------------------------------------------------------- ③ market_lint proxy_kw
class MarketLintProxyKeywordTests(unittest.TestCase):
    """③proxy_kw 按语系分支:ja 假名 run 也取;ko 谚文音节 bigram/th 泰文 run——
    纯文正文不再 None(标题关键词位次不再恒 MANUAL);zh/en 口径不变。"""

    def test_proxy_keyword_units(self):
        import market_lint as ml
        self.assertEqual(ml.proxy_keyword("zh", "项目管理软件 项目管理软件"), "项目管理软件"[:2])
        self.assertEqual(ml.proxy_keyword("en", "analysis tools analysis"), "analysis")
        self.assertEqual(ml.proxy_keyword("ja", "プロジェクトの管理。プロジェクト比較。"), "プロジェクト")
        self.assertEqual(ml.proxy_keyword("ko", "관리 도구 관리 관리"), "관리")
        self.assertEqual(ml.proxy_keyword("th", "สวัสดีครับ สวัสดีครับ"), "สวัสดีครับ")
        self.assertIsNone(ml.proxy_keyword("th", ""))                       # 空正文仍 None

    def test_ja_kana_proxy_not_manual(self):
        p = tmp_file("プロジェクト比較ガイド\nプロジェクトの説明\n"
                     "プロジェクトの選び方。プロジェクト管理の要点。プロジェクト比較の方法。\n")
        r = run_script("market_lint.py", ["--market", "ja", p])
        self.assertNotIn("正文高频词不可用", r.stdout)          # 修复前纯假名正文恒 MANUAL
        self.assertIn("「プロジェクト」位次 0", r.stdout)      # 假名 run 高频词进 title 位次检查
        os.unlink(p)

    def test_ko_hangul_proxy_not_manual(self):
        p = tmp_file("관리 가이드\n관리 도구 안내\n"
                     "관리 도구 비교. 관리 도구 비교. 관리 관리 관리 관리.\n")
        r = run_script("market_lint.py", ["--market", "ko", p])
        self.assertNotIn("正文高频词不可用", r.stdout)          # 修复前纯谚文正文恒 MANUAL
        self.assertIn("「관리」位次 0", r.stdout)
        os.unlink(p)

    def test_thai_proxy_not_manual(self):
        # สวัสดีครับ 含 Mn 声调/元音记号:旧 \w 口径把 run 切碎(<5)→ proxy 恒 None
        p = tmp_file("สวัสดีครับไทย\nสวัสดีครับ\nสวัสดีครับ สวัสดีครับ สวัสดีครับ\n")
        r = run_script("market_lint.py", ["--market", "th", p])
        self.assertNotIn("正文高频词不可用", r.stdout)          # 修复前纯泰文正文恒 MANUAL
        self.assertIn("「สวัสดีครับ」位次 0", r.stdout)
        os.unlink(p)


# ---------------------------------------------------------------- ④ split_sents 全角！?
class MarketLintFullwidthSentenceTests(unittest.TestCase):
    """④cjk/latin 两分支补全角！?(原 cjk 分支字符类里 ！？ 实为半角 !? 重复,全角句终不切)。"""

    def test_cjk_rule_fullwidth_breaks(self):
        import market_lint as ml
        self.assertEqual(ml.split_sents("第一句！第二句？第三句。", "cjk"),
                         ["第一句", "第二句", "第三句"])         # 修复前恒 1 句
        self.assertEqual(ml.split_sents("第一句!第二句?第三句。", "cjk"),
                         ["第一句", "第二句", "第三句"])         # 半角口径不变

    def test_latin_rule_fullwidth_breaks(self):
        import market_lint as ml
        self.assertEqual(ml.split_sents("Hello! World？ Next.", "latin"),
                         ["Hello", "World", "Next"])            # 修复前 World？ Next 不切
        self.assertEqual(ml.split_sents("A. B. C.", "latin"), ["A", "B", "C"])


# ---------------------------------------------------------------- ⑤⑥ th 支柱长度与句切
class MarketLintThaiTests(unittest.TestCase):
    """⑤支柱长度:th 无词间空格,split() 恒 1 词→字素/4 近似(带标注);
    ⑥newline 句切:HTML 正文折叠前按块级标签/换行切块,不再折叠后恒 1 句。"""

    def test_thai_pillar_grapheme_approx(self):
        body = "สวัสดีครับ" * 3                                    # 21 字素,无空格:split() 恒 1 词
        p = tmp_file('<html><head><title>ทดสอบ</title></head>'
                     '<body><p>%s</p></body></html>' % body)
        r = run_script("market_lint.py", ["--market", "th", p])
        m = re.search(r"正文 (\d+) words\(th 字素/4 近似\[推断\]\) < 支柱建议 1500", r.stdout)
        self.assertIsNotNone(m)                                 # 修复前输出 "正文 1 words"
        self.assertGreaterEqual(int(m.group(1)), 2)             # 字素/4≈5,不再是 1
        os.unlink(p)

    def test_thai_pillar_long_body_no_info(self):
        body = "สวัสดีครับ" * 1000                                 # 7000 字素 /4 = 1750 ≥ 1500
        p = tmp_file('<html><head><title>ทดสอบ</title></head>'
                     '<body><p>%s</p></body></html>' % body)
        r = run_script("market_lint.py", ["--market", "th", p])
        self.assertNotIn("< 支柱建议", r.stdout)                # 达标不再报支柱 INFO
        os.unlink(p)

    def test_thai_html_sentence_split_by_block(self):
        html = ('<html><head><title>ทดสอบ</title></head><body>'
                '<p>สวัสดีครับ</p><p>สวัสดีครับ</p><p>สวัสดีครับ</p></body></html>')
        p = tmp_file(html)
        r = run_script("market_lint.py", ["--market", "th", p])
        self.assertIn("句长 4 句", r.stdout)                     # 修复前折叠后恒 1 句
        os.unlink(p)

    def test_thai_plaintext_sentence_split_keeps_lines(self):
        p = tmp_file("ทดสอบ\nคำอธิบาย\nสวัสดีครับ\nสวัสดีครับ\nสวัสดีครับ\n")
        r = run_script("market_lint.py", ["--market", "th", p])
        self.assertIn("句长 3 句", r.stdout)                     # 纯文本换行拼回(原空格拼丢行界)
        os.unlink(p)


if __name__ == "__main__":
    unittest.main(verbosity=1)
