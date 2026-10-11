#!/usr/bin/env python3
"""test_market_fit.py — market_fit.py 回归(stdlib unittest,合成 GSC 国别 CSV,零网络,
standalone——不 import run_tests,被其 test_*.py 自动发现加载)。口径钉死脚本自身契约
(规格=pipeline-completeness.md R3-8:GSC 国别流量×markets.json→市场组合优先级矩阵):
- 结构因素模式(无 GSC):全候选需求等权 0.5+显著标注"缺数据按结构因素";Top3 恒 3 个
- GSC 国别:英文国名→市场码映射聚合(Japan→ja/Germany→de);份额=占全表总点击;未映射
  国家不丢弃(进清单);utf-8-sig 容 BOM;缺 Country 列→退出码 2
- 四因子:竞争密度=engines 本地引擎梯度(th google 单引擎 1.0;ko/ru 本地引擎≥3 减分
  但注生态位)/语言成本=文字系距离(en 源:de 同系 1.0>ja/ar;zh 源:ja 汉字共享更高)/
  合规成本=markets.json 文本关键词罚分(fr Bill 96、ru 152-ФЗ;tr 无→1.0)
- 适配度=四因子连乘×100(json 逐行复算);排序 fit 降序;暂缓行有最短板理由
- 机会注:国别无记录市场挂小语种唯一源红利(引 multilingual-geo-evidence.md U5)
- 用法错(未知市场/未知源语言/文件不可读/空 --markets)→退出码 2

用法: python3 tests/test_market_fit.py(tests/run_tests.py 自动发现本文件)"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)


def run_cli(args=()):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "market_fit.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_file(content, suffix=".csv", encoding="utf-8"):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding=encoding)
    f.write(content)
    f.close()
    return f.name


def run_json(args=()):
    r = run_cli(list(args) + ["--json"])
    assert r.returncode == 0, "exit=%s stderr=%s" % (r.returncode, r.stderr)
    return json.loads(r.stdout)


def by_market(doc):
    return {m["market"]: m for m in doc["markets"]}


GSC_CSV = ("Country,Clicks,Impressions,CTR,Position\n"
           "United States,5000,100000,5%,8.0\n"
           "Japan,400,8000,5%,7.0\n"
           "Germany,100,3000,3%,12.0\n"
           "Atlantis,55,1000,5%,9.0\n"
           "Turkey,0,50,0%,15.0\n")


class MarketFitUsageTests(unittest.TestCase):
    """--help / 用法错退出码 2(未知市场/未知源语言/坏文件/空候选)"""

    def test_help_prints_usage(self):
        r = run_cli(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("R3-8", r.stdout)
        self.assertIn("--gsc-country", r.stdout)

    def test_unknown_market_exit_2(self):
        r = run_cli(["--markets", "ja,xx"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知市场 xx", r.stderr)
        self.assertIn("可用:", r.stderr)

    def test_unknown_source_lang_exit_2(self):
        r = run_cli(["--source-lang", "qq"])
        self.assertEqual(r.returncode, 2)

    def test_missing_gsc_file_exit_2(self):
        r = run_cli(["--gsc-country", "/nonexistent/gsc.csv"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("不可读", r.stderr)

    def test_gsc_without_country_column_exit_2(self):
        p = tmp_file("Query,Clicks\nfoo,1\n")
        r = run_cli(["--gsc-country", p])
        self.assertEqual(r.returncode, 2)
        self.assertIn("缺 Country 列", r.stderr)
        os.unlink(p)

    def test_markets_filter_selects_candidates(self):
        doc = run_json(["--markets", "ja,ko,de"])
        self.assertEqual(sorted(doc["candidates"]), ["de", "ja", "ko"])


class MarketFitStructuralTests(unittest.TestCase):
    """无 GSC=结构因素模式:等权需求+诚实标注;Top3 结构;因子来自 markets.json"""

    def test_default_all_18_markets_equal_demand(self):
        doc = run_json([])
        self.assertEqual(len(doc["markets"]), 18)
        self.assertEqual(doc["demand_basis"], "structural-only(缺数据按结构因素)")
        demands = {m["factors"]["demand"]["score"] for m in doc["markets"]}
        self.assertEqual(demands, {0.5})          # 全候选等权——不编数字

    def test_structural_mode_markdown_annotation(self):
        r = run_cli([])
        self.assertIn("缺数据按结构因素", r.stdout)
        self.assertIn("市场进入优先级矩阵", r.stdout)

    def test_recommended_is_top3_sorted_desc(self):
        doc = run_json([])
        rec = doc["recommended"]
        self.assertEqual(len(rec), 3)
        fits = [m["fit"] for m in doc["markets"]]
        self.assertEqual(fits, sorted(fits, reverse=True))
        self.assertEqual(rec[0]["fit"], max(fits))
        # 全部候选里 CJK/RTL 语言成本显著拖后(ko<de 稳健断言,不钉死具体名次)
        bm = by_market(doc)
        self.assertLess(bm["ko"]["fit"], bm["de"]["fit"])

    def test_deferred_have_weakest_factor_reason(self):
        doc = run_json(["--markets", "ja,ko,de,fr,ru"])
        self.assertTrue(doc["deferred"])
        for d in doc["deferred"]:
            self.assertTrue(d["reason"])
            self.assertRegex(d["reason"], r"(需求|竞争|语言|合规)是最短板")

    def test_structural_opportunity_note_cites_u5(self):
        doc = run_json([])
        joined = " ".join(doc["opportunity_notes"])
        self.assertIn("multilingual-geo-evidence.md", joined)
        self.assertIn("唯一源", joined)


class MarketFitGscTests(unittest.TestCase):
    """GSC 国别导出:映射聚合/份额口径/未映射不丢/BOM/零足迹机会注"""

    @classmethod
    def setUpClass(cls):
        cls.path = tmp_file(GSC_CSV)
        cls.doc = run_json(["--gsc-country", cls.path,
                            "--markets", "ja,de,tr,en,ko"])
        cls.bm = by_market(cls.doc)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.path)

    def test_basis_and_totals(self):
        self.assertTrue(self.doc["demand_basis"].startswith("gsc-country:"))
        self.assertEqual(self.doc["gsc"]["total_clicks"], 5555)   # 含未映射国家(份额分母诚实)

    def test_country_aggregation_into_markets(self):
        ja = self.bm["ja"]["factors"]["demand"]
        self.assertEqual(ja["clicks"], 400)
        self.assertEqual(ja["countries"], ["Japan"])
        self.assertAlmostEqual(ja["share"], 400 / 5555, places=3)

    def test_demand_formula_abs_and_share(self):
        # ja:绝对档 400→0.85;份额 7.2%/15%→0.480 → 0.6*0.85+0.4*0.480=0.702
        self.assertAlmostEqual(self.bm["ja"]["factors"]["demand"]["score"], 0.702, places=3)
        self.assertGreater(self.bm["ja"]["factors"]["demand"]["score"],
                           self.bm["de"]["factors"]["demand"]["score"])

    def test_zero_click_with_impressions_weak_evidence(self):
        # Turkey 0 点击 50 曝光 → 绝对档 0.25(需求存在的弱证据,不是 0.1 无记录档)
        self.assertAlmostEqual(self.bm["tr"]["factors"]["demand"]["score"], 0.15, places=3)

    def test_absent_market_zero_footprint_and_opportunity(self):
        ko = self.bm["ko"]["factors"]["demand"]
        self.assertEqual(ko["score"], 0.1)
        self.assertTrue(ko["no_evidence"])
        notes = " ".join(self.doc["opportunity_notes"])
        self.assertIn("ko", notes)
        self.assertIn("multilingual-geo-evidence.md", notes)

    def test_unmapped_country_listed_not_dropped(self):
        self.assertIn("Atlantis", self.doc["gsc"]["unmapped_countries"])

    def test_bom_csv_accepted(self):
        p = tmp_file(GSC_CSV, encoding="utf-8-sig")
        r = run_cli(["--gsc-country", p, "--markets", "ja", "--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        doc = json.loads(r.stdout)
        self.assertEqual(doc["gsc"]["total_clicks"], 5555)
        os.unlink(p)


class MarketFitFactorTests(unittest.TestCase):
    """四因子口径:引擎格局梯度/文字系距离(含 zh 源)/合规关键词罚分/连乘一致"""

    @staticmethod
    def _factors(markets_args):
        doc = run_json(markets_args)
        return by_market(doc)

    def test_competition_google_only_beats_local_engine_markets(self):
        bm = self._factors(["--markets", "th,ko,ru,de"])
        f = {m: bm[m]["factors"]["competition"] for m in bm}
        self.assertEqual(f["th"]["score"], 1.0)               # google 单引擎
        self.assertEqual(f["de"]["score"], 1.0)               # google+bing
        self.assertLess(f["ko"]["score"], f["th"]["score"])   # naver+daum+briefing ≥3 本地
        self.assertLess(f["ru"]["score"], f["th"]["score"])   # yandex 系
        self.assertIn("生态位", f["ko"]["evidence"])           # 减分但注明生态位

    def test_language_script_distance_from_en(self):
        bm = self._factors(["--markets", "de,ja,ar,th"])
        f = {m: bm[m]["factors"]["language"] for m in bm}
        self.assertEqual(f["de"]["score"], 1.0)               # 同 latin 文字系
        self.assertLess(f["ja"]["score"], f["de"]["score"])   # latin→jamix
        self.assertLess(f["ar"]["score"], f["de"]["score"])
        self.assertIn("RTL 全链", f["ar"]["evidence"])          # direction=rtl 推导标注
        self.assertTrue(any("空格" in a for a in f["th"]["assumptions"]))  # newline 切句推导

    def test_language_source_zh_ja_closer_than_from_en(self):
        bm_en = self._factors(["--source-lang", "en", "--markets", "ja"])
        bm_zh = self._factors(["--source-lang", "zh", "--markets", "ja"])
        self.assertGreater(bm_zh["ja"]["factors"]["language"]["score"],
                           bm_en["ja"]["factors"]["language"]["score"])   # 汉字共享 0.60>0.35

    def test_compliance_flags_derived_from_markets_json(self):
        bm = self._factors(["--markets", "fr,ru,de,tr"])
        f = {m: bm[m]["factors"]["compliance"] for m in bm}
        self.assertIn("Bill 96", " ".join(f["fr"]["flags"]))
        self.assertIn("152-ФЗ", " ".join(f["ru"]["flags"]))
        self.assertIn("Impressum", " ".join(f["de"]["flags"]))
        self.assertEqual(f["tr"]["flags"], [])                 # 无合规关键词→成本 1.0
        self.assertEqual(f["tr"]["score"], 1.0)
        self.assertLess(f["fr"]["score"], f["tr"]["score"])

    def test_fit_is_factor_product(self):
        p = tmp_file(GSC_CSV)
        doc = run_json(["--gsc-country", p, "--markets", "ja,de,ko"])
        os.unlink(p)
        for m in doc["markets"]:
            fac = m["factors"]
            expect = round(fac["demand"]["score"] * fac["competition"]["score"]
                           * fac["language"]["score"] * fac["compliance"]["score"] * 100, 1)
            self.assertAlmostEqual(m["fit"], expect, places=1)

    def test_markdown_matrix_and_sections(self):
        p = tmp_file(GSC_CSV)
        r = run_cli(["--gsc-country", p, "--markets", "ja,de,ko"])
        os.unlink(p)
        self.assertIn("| 市场 | 适配度 | 需求 | 竞争 | 语言 | 合规 | 判定 |", r.stdout)
        self.assertIn("推荐进入(Top 3)", r.stdout)
        self.assertIn("暂缓:", r.stdout)
        self.assertIn("## 因子证据", r.stdout)
        self.assertIn("## 机会注", r.stdout)
        self.assertIn("market_batch.py", r.stdout)             # 下一步接线提示


if __name__ == "__main__":
    unittest.main(verbosity=2)
