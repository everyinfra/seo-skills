#!/usr/bin/env python3
"""parity_check.py golden 用例(stdlib unittest,合成双语 HTML fixture,零网络)。
口径钉死 pipeline-completeness.md R2-7(双语 parity_check):
  长度平价带(markets.json 膨胀口径 de+25-35/ja-25~-10/zh-40~-20/ar~20→+10~30;
  无口径通用 ±30 标[推断];长度单位=可见文本非空白字符)/ H2 结构对照(位置差列表)/
  FAQ 块与表格块存在性对照 / JSON-LD description 同为缺·同为有 /
  canonical 互指(相同=warn 缺失=warn)/ hreflang 对仅提示不计退出码 /
  --json 结构与退出码(0 全过/1 warn/2 参数错)。
独立可运行:python3 tests/test_parity_check.py;也被 tests/run_tests.py 自动发现。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import parity_check as pc  # noqa: E402


def run_script(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "parity_check.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_html(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def page(lang, para_n, h2s, canonical=None, alternate=None, jsonld=None, table=True):
    """合成双语页:可见文本长度=Σ(h2 非空白字符)+para 非空白字符+表格格 data(4)。"""
    links = ('<link rel="canonical" href="%s">' % canonical) if canonical else ""
    if alternate:
        links += '<link rel="alternate" hreflang="%s" href="https://ex.com/%s/">' % (alternate[0], alternate[1])
    ld = ('<script type="application/ld+json">%s</script>' % jsonld) if jsonld else ""
    h2_html = "".join("<h2>%s</h2>" % h for h in h2s)
    tbl = "<table><tr><td>data</td></tr></table>" if table else ""
    return ('<!doctype html><html lang="%s"><head><meta charset="utf-8"><title>T</title>'
            '%s%s</head><body>%s<p>%s</p>%s</body></html>') % (lang, links, ld, h2_html, "x" * para_n, tbl)


def vlen(para_n, h2s=(), table=True):
    """与脚本口径一致的可见文本长度(非空白字符)。"""
    return para_n + sum(len("".join(h.split())) for h in h2s) + (4 if table else 0)


SRC_H2 = ("Overview", "FAQ")
TGT_DE_H2 = ("Überblick", "FAQ")


class LengthParityTests(unittest.TestCase):
    """长度平价带:markets.json 膨胀口径直读;无口径通用带 ±30 标[推断]"""

    def test_de_band_pass_from_markets_json(self):
        """de 带 [+25,+35]:目标长度落带 → 6 项全过 rc=0,口径文案来自 markets.json。"""
        src = tmp_html(page("en", 100, SRC_H2, canonical="https://ex.com/en/",
                            alternate=("de", "de"), jsonld='{"@type":"WebPage","description":"d"}'))
        src_len = vlen(100, SRC_H2)                      # 115
        tgt = tmp_html(page("de", round(src_len * 1.30) - vlen(0, TGT_DE_H2), TGT_DE_H2,
                            canonical="https://ex.com/de/", alternate=("en", "en"),
                            jsonld='{"@type":"WebPage","description":"z"}'))
        r = run_script(["--source", src, "--target", tgt, "--market", "de"])
        os.unlink(src); os.unlink(tgt)
        self.assertEqual(r.returncode, 0)
        self.assertIn("✓ length_parity", r.stdout)
        self.assertIn("落在带 [1.25, 1.35]", r.stdout)
        self.assertIn("比英语长 25-35%", r.stdout)        # markets.json 口径原短语
        self.assertIn("判定: 6 pass / 0 warn", r.stdout)

    def test_de_band_too_short_warn(self):
        """目标过短(+10%<+25%)→ length_parity warn,rc=1。"""
        src = tmp_html(page("en", 100, SRC_H2, canonical="https://ex.com/en/",
                            alternate=("de", "de"), jsonld='{"@type":"WebPage","description":"d"}'))
        src_len = vlen(100, SRC_H2)
        tgt = tmp_html(page("de", round(src_len * 1.10) - vlen(0, TGT_DE_H2), TGT_DE_H2,
                            canonical="https://ex.com/de/", alternate=("en", "en"),
                            jsonld='{"@type":"WebPage","description":"z"}'))
        r = run_script(["--source", src, "--target", tgt, "--market", "de"])
        os.unlink(src); os.unlink(tgt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("[WARN] length_parity", r.stdout)
        self.assertIn("出带", r.stdout)
        self.assertIn("判定: 5 pass / 1 warn", r.stdout)

    def test_ja_band_autodetected_from_target_lang(self):
        """无 --market:按目标页 lang 主子 tag 取 ja 带 [-25,-10],落带 pass。"""
        ja_h2 = ("概要", "FAQ")
        src = tmp_html(page("en", 100, SRC_H2, canonical="https://ex.com/en/",
                            alternate=("ja", "ja"), jsonld='{"@type":"WebPage","description":"d"}'))
        src_len = vlen(100, SRC_H2)
        tgt = tmp_html(page("ja", round(src_len * 0.82) - vlen(0, ja_h2), ja_h2,
                            canonical="https://ex.com/ja/", alternate=("en", "en"),
                            jsonld='{"@type":"WebPage","description":"z"}'))
        r = run_script(["--source", src, "--target", tgt])       # 无 --market
        os.unlink(src); os.unlink(tgt)
        self.assertEqual(r.returncode, 0)
        self.assertIn("✓ length_parity", r.stdout)
        self.assertIn("比英语短 10-25%", r.stdout)               # ja 带自动套用

    def test_generic_band_marked_inferred(self):
        """无膨胀口径市场(es)→ 通用带 ±30 且标 [推断]。"""
        es_h2 = ("Resumen", "FAQ")
        src = tmp_html(page("en", 100, SRC_H2, canonical="https://ex.com/en/",
                            alternate=("es", "es"), jsonld='{"@type":"WebPage","description":"d"}'))
        src_len = vlen(100, SRC_H2)
        tgt = tmp_html(page("es", round(src_len * 1.0) - vlen(0, es_h2), es_h2,
                            canonical="https://ex.com/es/", alternate=("en", "en"),
                            jsonld='{"@type":"WebPage","description":"z"}'))
        r = run_script(["--source", src, "--target", tgt, "--market", "es"])
        os.unlink(src); os.unlink(tgt)
        self.assertEqual(r.returncode, 0)
        self.assertIn("带 [0.70, 1.30]", r.stdout)
        self.assertIn("[推断]", r.stdout)

    def test_ar_point_estimate_expands_to_band(self):
        """ar 单点口径「膨胀 ~20%」→ 展成带 [+10,+30](±50% 展开 documented)。"""
        ar_h2 = ("نظرة", "FAQ")
        src = tmp_html(page("en", 100, SRC_H2, canonical="https://ex.com/en/",
                            alternate=("ar", "ar"), jsonld='{"@type":"WebPage","description":"d"}'))
        src_len = vlen(100, SRC_H2)
        tgt = tmp_html(page("ar", round(src_len * 1.18) - vlen(0, ar_h2), ar_h2,
                            canonical="https://ex.com/ar/", alternate=("en", "en"),
                            jsonld='{"@type":"WebPage","description":"z"}'))
        r = run_script(["--source", src, "--target", tgt, "--market", "ar"])
        os.unlink(src); os.unlink(tgt)
        self.assertEqual(r.returncode, 0)
        self.assertIn("带 [1.10, 1.30]", r.stdout)
        self.assertIn("膨胀 ~20%", r.stdout)

    def test_expansion_band_unit_from_markets_json(self):
        """纯函数钉死四市场带(直读 markets.json notes/pillar_note)+无口径回落。"""
        mk = pc.load_markets()
        self.assertEqual(pc.expansion_band(mk["de"])[0], (25.0, 35.0))
        self.assertEqual(pc.expansion_band(mk["ja"])[0], (-25.0, -10.0))
        self.assertEqual(pc.expansion_band(mk["zh"])[0], (-40.0, -20.0))
        self.assertEqual(pc.expansion_band(mk["ar"])[0], (10.0, 30.0))
        self.assertEqual(pc.expansion_band(mk["es"]), ((-30.0, 30.0), None))   # 通用[推断]


class StructureParityTests(unittest.TestCase):
    """H2 结构对照 / FAQ 块 / 表格块 / JSON-LD description(单边存在 → warn)"""

    @staticmethod
    def _pair(src_h2s, tgt_h2s, src_jsonld='{"@type":"WebPage","description":"d"}',
              tgt_jsonld='{"@type":"WebPage","description":"z"}', src_table=True, tgt_table=True):
        src_len = vlen(100, src_h2s, src_table)
        other = vlen(0, tgt_h2s, tgt_table)
        tgt_n = max(0, round(src_len * 1.30) - other)     # de 带内取中,长度项不干扰
        src = tmp_html(page("en", 100, src_h2s, canonical="https://ex.com/en/",
                            alternate=("de", "de"), jsonld=src_jsonld, table=src_table))
        tgt = tmp_html(page("de", tgt_n, tgt_h2s, canonical="https://ex.com/de/",
                            alternate=("en", "en"), jsonld=tgt_jsonld, table=tgt_table))
        return src, tgt

    def _run(self, src, tgt, *extra):
        r = run_script(["--source", src, "--target", tgt, "--market", "de", *extra])
        os.unlink(src); os.unlink(tgt)
        return r

    def test_h2_count_mismatch_warns_with_positional_diff(self):
        src, tgt = self._pair(("Overview", "FAQ", "Pricing"), TGT_DE_H2)
        r = self._run(src, tgt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("[WARN] h2_structure", r.stdout)
        self.assertIn("仅源有第 3 个 H2「Pricing」", r.stdout)      # 位置差列表
        self.assertIn("源 3/目标 2", r.stdout)

    def test_faq_block_single_sided_via_jsonld(self):
        """源 FAQPage JSON-LD / 目标 WebPage(标题不含 FAQ 词)→ faq_block 单边 warn。"""
        src, tgt = self._pair(("Overview", "Details"), ("Überblick", "Details"),
                              src_jsonld='{"@type":"FAQPage","description":"d"}')
        r = self._run(src, tgt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("[WARN] faq_block", r.stdout)
        self.assertIn("源 True/目标 False", r.stdout)
        self.assertIn("判定: 5 pass / 1 warn", r.stdout)

    def test_faq_block_both_present_via_heading_pass(self):
        src, tgt = self._pair(("Overview", "FAQ"), TGT_DE_H2)      # 双方 H2 标题词命中
        r = self._run(src, tgt)
        self.assertEqual(r.returncode, 0)
        self.assertIn("✓ faq_block: FAQ 块同为有", r.stdout)

    def test_table_block_single_sided_warn(self):
        src, tgt = self._pair(("Overview", "Details"), ("Überblick", "Details"),
                              src_table=True, tgt_table=False)
        r = self._run(src, tgt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("[WARN] table_block", r.stdout)
        self.assertIn("源 True/目标 False", r.stdout)

    def test_jsonld_description_single_sided_warn_and_both_absent_pass(self):
        h2s_src, h2s_tgt = ("Overview", "Details"), ("Überblick", "Details")
        src, tgt = self._pair(h2s_src, h2s_tgt, src_jsonld='{"@type":"WebPage","description":"d"}',
                              tgt_jsonld=None)
        r = self._run(src, tgt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("[WARN] jsonld_description", r.stdout)
        self.assertIn("源 True/目标 False", r.stdout)
        src2, tgt2 = self._pair(h2s_src, h2s_tgt, src_jsonld=None, tgt_jsonld=None)
        r2 = self._run(src2, tgt2)
        self.assertIn("✓ jsonld_description: JSON-LD description 同为缺", r2.stdout)


class CanonicalHreflangTests(unittest.TestCase):
    """canonical 互指(相同/缺失=warn)与 hreflang 对(仅提示,不计退出码)"""

    @staticmethod
    def _pair(src_canonical, tgt_canonical, tgt_alternate=("en", "en")):
        src_len = vlen(100, SRC_H2)
        tgt_n = round(src_len * 1.30) - vlen(0, TGT_DE_H2)
        src = tmp_html(page("en", 100, SRC_H2, canonical=src_canonical,
                            alternate=("de", "de"), jsonld='{"@type":"WebPage","description":"d"}'))
        tgt = tmp_html(page("de", tgt_n, TGT_DE_H2, canonical=tgt_canonical,
                            alternate=tgt_alternate, jsonld='{"@type":"WebPage","description":"z"}'))
        return src, tgt

    def _run(self, src, tgt):
        r = run_script(["--source", src, "--target", tgt, "--market", "de"])
        os.unlink(src); os.unlink(tgt)
        return r

    def test_identical_canonical_warns_merge_risk(self):
        src, tgt = self._pair("https://ex.com/en/", "https://ex.com/en/")   # 目标指回源
        r = self._run(src, tgt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("[WARN] canonical: 两页 canonical 相同", r.stdout)
        self.assertIn("并入源语言索引", r.stdout)

    def test_missing_canonical_warns(self):
        src, tgt = self._pair(None, "https://ex.com/de/")
        r = self._run(src, tgt)
        self.assertEqual(r.returncode, 1)
        self.assertIn("[WARN] canonical: canonical 缺失", r.stdout)

    def test_distinct_canonicals_pass(self):
        src, tgt = self._pair("https://ex.com/en/", "https://ex.com/de/")
        r = self._run(src, tgt)
        self.assertEqual(r.returncode, 0)
        self.assertIn("✓ canonical: 两页 canonical 互不相同", r.stdout)

    def test_hreflang_pair_incomplete_is_note_only(self):
        """hreflang 对不完整 → 提示行输出但不计入退出码(其余全过 rc=0)。"""
        src, tgt = self._pair("https://ex.com/en/", "https://ex.com/de/", tgt_alternate=None)
        r = self._run(src, tgt)
        self.assertEqual(r.returncode, 0, "hreflang 对仅提示,不影响退出码")
        self.assertIn("提示: hreflang 对不完整", r.stdout)
        self.assertIn("目标页含源语言 en=False", r.stdout)
        self.assertIn("判定: 6 pass / 0 warn", r.stdout)

    def test_hreflang_bidirectional_note(self):
        src, tgt = self._pair("https://ex.com/en/", "https://ex.com/de/")
        r = self._run(src, tgt)
        self.assertIn("提示: hreflang 双向在场(源含 de,目标含 en)", r.stdout)


class OutputAndCliTests(unittest.TestCase):
    """--json 结构 / 参数与文件错误路径(exit 2)"""

    def test_json_payload(self):
        src_len = vlen(100, SRC_H2)
        tgt_n = round(src_len * 1.30) - vlen(0, TGT_DE_H2)
        src = tmp_html(page("en", 100, SRC_H2, canonical="https://ex.com/en/",
                            alternate=("de", "de"), jsonld='{"@type":"WebPage","description":"d"}'))
        tgt = tmp_html(page("de", tgt_n, TGT_DE_H2, canonical="https://ex.com/de/",
                            alternate=("en", "en"), jsonld='{"@type":"WebPage","description":"z"}'))
        r = run_script(["--source", src, "--target", tgt, "--market", "de", "--json"])
        os.unlink(src); os.unlink(tgt)
        self.assertEqual(r.returncode, 0)
        payload = json.loads(r.stdout[r.stdout.index("{"):])
        self.assertEqual(payload["verdict"], "pass")
        self.assertEqual(payload["band_pct"], [25.0, 35.0])
        self.assertEqual(payload["length"]["source"], src_len)
        self.assertEqual(payload["length"]["target"], vlen(tgt_n, TGT_DE_H2))
        self.assertEqual(len(payload["checks"]), 6)
        self.assertEqual(payload["h2"]["source"], list(SRC_H2))
        self.assertTrue(payload["notes"])

    def test_missing_file_exits_2(self):
        r = run_script(["--source", "/nonexistent/a.html", "--target", "/nonexistent/b.html"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("文件不存在", r.stderr)

    def test_missing_required_args_exits_2(self):
        r = run_script(["--target", "x.html"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("需要 --source 与 --target", r.stderr)

    def test_unknown_market_exits_2(self):
        a = tmp_html(page("en", 10, ("A",)))
        b = tmp_html(page("de", 10, ("B",)))
        r = run_script(["--source", a, "--target", b, "--market", "xx"])
        os.unlink(a); os.unlink(b)
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知市场 xx", r.stderr)

    def test_zero_length_body_warns(self):
        a = tmp_html('<html lang="en"><body></body></html>')
        b = tmp_html('<html lang="de"><body><p>y</p></body></html>')
        r = run_script(["--source", a, "--target", b, "--market", "de"])
        os.unlink(a); os.unlink(b)
        self.assertEqual(r.returncode, 1)
        self.assertIn("可见文本长度为 0", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
