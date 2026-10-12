#!/usr/bin/env python3
"""citation_panel.py triangulate 子命令测试(R6 归因: 三源分歧度报告)。
standalone(自带 run_script 助手,合成 panel/ referral/survey 文件,零网络):
python3 tests/test_citation_triangulate.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。

合成数据口径: 12 prompt × 2 run(6/9 提及)→ 窗口内 coverage 已知;
referral 三形态(ai_referral_log 文本 / date,hits[,total] CSV / 逐日 JSON)
的占比与窗口过滤手工推导后钉死。"""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import citation_panel as cp  # noqa: E402  (需先入 SCRIPTS 路径)


def run_script(name, args=()):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tri(args):
    return run_script("citation_panel.py", ["triangulate", *args])


class TriangulateFixture(unittest.TestCase):
    """共用面板: 12 prompts × 2 runs(2026-09-01 coverage=50%,2026-10-05 coverage=75%)。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="tri_t_")
        cls.panel = os.path.join(cls.tmp, "panel.json")
        prompts = os.path.join(cls.tmp, "p.csv")
        with open(prompts, "w", encoding="utf-8") as f:
            f.write("prompt\n" + "".join("q%d\n" % i for i in range(12)))
        r = run_script("citation_panel.py",
                       ["init", "--brand", "Acme", "--domain", "acme.ai",
                        "--prompts", prompts, "--panel", cls.panel])
        assert r.returncode == 0, r.stderr
        for engine, dt, cov in (("chatgpt", "2026-09-01", 6),
                                ("chatgpt", "2026-10-05", 9)):
            run_csv = os.path.join(cls.tmp, "run-%s.csv" % dt)
            with open(run_csv, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["prompt", "mentioned", "cited", "cited_urls"])
                for i in range(12):
                    w.writerow(["q%d" % i, 1 if i < cov else 0, 0, ""])
            r = run_script("citation_panel.py",
                           ["record", "--engine", engine, "--file", run_csv,
                            "--panel", cls.panel, "--date", dt])
            assert r.returncode == 0, r.stderr
        # ai_referral_log 文本输出形态(25/950 = 2.6316%)
        cls.ref_text = os.path.join(cls.tmp, "ref.txt")
        with open(cls.ref_text, "w", encoding="utf-8") as f:
            f.write("== AI 引用流量日志分析 ==\n"
                    "日志行 1000 | 可解析 950 | 无 referrer 50\n"
                    "-- AI referrer 域(请求数 / 独立路径数)--\n"
                    "  chatgpt.com                  20       5\n"
                    "  合计 AI referrer 请求: 25\n"
                    "[!] App 内打开常不带 referrer——测得的是下界;\n")
        # CSV 形态(date,hits,total)
        cls.ref_csv = os.path.join(cls.tmp, "ref.csv")
        with open(cls.ref_csv, "w", newline="", encoding="utf-8") as f:
            f.write("date,hits,total\n2026-08-30,10,100\n2026-09-02,30,100\n"
                    "2026-10-01,20,100\n")
        # 逐日 JSON 形态
        cls.ref_json = os.path.join(cls.tmp, "ref.json")
        with open(cls.ref_json, "w", encoding="utf-8") as f:
            json.dump({"2026-08-30": {"hits": 5, "total": 50},
                       "2026-09-02": {"hits": 20, "total": 100}}, f)
        # survey CSV(0-1 与 0-100 混排)
        cls.survey = os.path.join(cls.tmp, "survey.csv")
        with open(cls.survey, "w", newline="", encoding="utf-8") as f:
            f.write("date,recall\n2026-09-02,0.42\n2026-10-06,50\n")

    def _tri_json(self, *extra):
        r = tri(["--panel", self.panel, "--json", *extra])
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)


class ReferralFormsTests(TriangulateFixture):
    """--referral 三形态: ai_referral_log 文本 / CSV / 逐日 JSON。"""

    def test_ai_referral_log_text_form(self):
        """文本形态: 抓 '合计 AI referrer 请求: 25' 与 '可解析 950' → 2.6316%。"""
        src = cp.parse_referral_source(self.ref_text)
        self.assertEqual(src["form"], "ai_referral_log-text")
        self.assertEqual(src["hits"], 25.0)
        self.assertEqual(src["parsed"], 950.0)
        self.assertAlmostEqual(src["value_pct"], 100 * 25 / 950, delta=1e-9)

    def test_csv_form_with_window_filter(self):
        """CSV 形态: 窗口 09-01→09-30 只吃 09-02 行 → 30/100=30%(08-30/10-01 剔除)。"""
        since_until = dict(since=cp.parse_date("2026-09-01T00:00:00"),
                           until=cp.parse_date("2026-09-30T00:00:00"))
        src = cp.parse_referral_source(self.ref_csv, **since_until)
        self.assertEqual(src["form"], "csv")
        self.assertEqual(src["hits"], 30.0)
        self.assertEqual(src["parsed"], 100.0)
        self.assertAlmostEqual(src["value_pct"], 30.0)
        # 无窗口: 三行全算 60/300=20%
        src_all = cp.parse_referral_source(self.ref_csv)
        self.assertAlmostEqual(src_all["value_pct"], 20.0)

    def test_daily_json_form_with_since(self):
        """逐日 JSON: since=09-01 → 只吃 09-02 行 → 20%;08-30 行剔除。"""
        src = cp.parse_referral_source(
            self.ref_json, since=cp.parse_date("2026-09-01T00:00:00"))
        self.assertEqual(src["form"], "json")
        self.assertEqual(src["hits"], 20.0)
        self.assertEqual(src["parsed"], 100.0)
        self.assertAlmostEqual(src["value_pct"], 20.0)

    def test_unknown_form_rejected(self):
        bad = os.path.join(self.tmp, "bad.txt")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("random garbage\nno parseable markers\n")
        r = tri(["--panel", self.panel, "--referral", bad])
        self.assertEqual(r.returncode, 1)
        self.assertIn("不认识的形态", r.stderr)


class TriangulateCoreTests(TriangulateFixture):
    """panel 窗口 coverage / survey 换算 / 两两差 / 最大分歧源。"""

    def test_panel_window_coverage(self):
        pan = cp.panel_window_coverage(
            cp.load_panel(self.panel), since=cp.parse_date("2026-09-01T00:00:00"),
            until=cp.parse_date("2026-09-30T00:00:00"))
        self.assertEqual(pan["runs"], 1)                 # 只有 09-01 的 run
        self.assertEqual(pan["denominator"], 12)
        self.assertEqual(pan["mentioned_sum"], 6)
        self.assertAlmostEqual(pan["value_pct"], 50.0)
        self.assertAlmostEqual(pan["per_engine"]["chatgpt"]["coverage"], 0.5)

    def test_survey_scale_and_window(self):
        svy = cp.load_survey_csv(
            self.survey, since=cp.parse_date("2026-09-01T00:00:00"),
            until=cp.parse_date("2026-09-30T00:00:00"))
        self.assertEqual(svy["rows"], 1)
        self.assertAlmostEqual(svy["value_pct"], 42.0)   # 0.42 → 42%
        # 无窗口: (42+50)/2 = 46
        svy_all = cp.load_survey_csv(self.survey)
        self.assertAlmostEqual(svy_all["value_pct"], 46.0)
        # 越界值拒绝
        bad = os.path.join(self.tmp, "bad_survey.csv")
        with open(bad, "w", newline="", encoding="utf-8") as f:
            f.write("date,recall\n2026-09-01,120\n")
        with self.assertRaises(ValueError):
            cp.load_survey_csv(bad)

    def test_pairwise_and_max_divergence(self):
        """三源已知值: referral 2.63 / panel 62.5(全窗)/ survey 46 →
        两两差精确;最大分歧源=referral。"""
        pl = self._tri_json("--referral", self.ref_text, "--survey", self.survey)
        srcs = pl["sources"]
        self.assertAlmostEqual(srcs["referral"]["value_pct"], 100 * 25 / 950,
                               delta=1e-6)
        self.assertAlmostEqual(srcs["panel"]["value_pct"], 62.5)   # (6+9)/24
        self.assertAlmostEqual(srcs["survey"]["value_pct"], 46.0)
        pw = {(p["a"], p["b"]): p for p in pl["pairwise"]}
        self.assertEqual(len(pw), 3)
        self.assertAlmostEqual(pw[("referral", "panel")]["diff_pp"],
                               100 * 25 / 950 - 62.5, delta=0.02)
        self.assertAlmostEqual(pw[("panel", "survey")]["diff_pp"], 62.5 - 46.0,
                               delta=1e-6)
        # direction 措辞: 高者在前
        self.assertIn("panel 高于 survey", pw[("panel", "survey")]["direction"])
        self.assertIn("panel 高于 referral",
                      pw[("referral", "panel")]["direction"])
        self.assertEqual(pl["max_divergence"]["source"], "referral")
        self.assertIn("下限", pl["max_divergence"]["hint"])
        self.assertEqual(pl["n_comparable"], 3)

    def test_two_sources_when_survey_missing(self):
        """不给 --survey: 两源一对差;两源分歧对称(平手按 sorted 名单取首个=panel,
        确定性),|Δ| 与三源时的 referral-panel 对一致。"""
        pl = self._tri_json("--referral", self.ref_text)
        self.assertNotIn("survey", pl["sources"])
        self.assertEqual(len(pl["pairwise"]), 1)
        self.assertEqual(pl["n_comparable"], 2)
        self.assertAlmostEqual(pl["max_divergence"]["mean_abs_pp"],
                               62.5 - 100 * 25 / 950, delta=0.02)
        self.assertIn(pl["max_divergence"]["source"], ("panel", "referral"))

    def test_window_applies_to_all_sources(self):
        """--since/--until 同时过滤 panel runs / referral CSV / survey 行。"""
        pl = self._tri_json("--referral", self.ref_csv, "--survey", self.survey,
                            "--since", "2026-09-01", "--until", "2026-09-30")
        self.assertAlmostEqual(pl["sources"]["panel"]["value_pct"], 50.0)    # 只剩 09-01 run
        self.assertAlmostEqual(pl["sources"]["referral"]["value_pct"], 30.0) # 只剩 09-02 行
        self.assertAlmostEqual(pl["sources"]["survey"]["value_pct"], 42.0)
        pw = {(p["a"], p["b"]): p["diff_pp"] for p in pl["pairwise"]}
        self.assertAlmostEqual(pw[("referral", "panel")], 30.0 - 50.0, delta=1e-6)


class RenderCliTests(TriangulateFixture):
    """markdown 报告 / 错误路径 / 既有族冻结。"""

    def test_markdown_report_and_caveats(self):
        r = tri(["--panel", self.panel, "--referral", self.ref_text,
                 "--survey", self.survey])
        self.assertEqual(r.returncode, 0, r.stderr)
        for frag in ("三源分歧度报告(triangulate): Acme", "-- 三源 --",
                     "referral(ai_referral_log-text)", "-- 两两差(pp) --",
                     "最大分歧源: referral", "referral 是下限",
                     "永不跨源求和/平均", "chatgpt"):
            self.assertIn(frag, r.stdout, frag)

    def test_error_paths(self):
        # 无 runs 面板
        empty = os.path.join(self.tmp, "empty.json")
        prompts = os.path.join(self.tmp, "p1.csv")
        with open(prompts, "w", encoding="utf-8") as f:
            f.write("prompt\nq1\n")
        run_script("citation_panel.py", ["init", "--brand", "B", "--prompts",
                                         prompts, "--panel", empty])
        r = tri(["--panel", empty, "--referral", self.ref_text])
        self.assertEqual(r.returncode, 1)
        self.assertIn("尚无 runs", r.stderr)
        # 非法 --since
        r2 = tri(["--panel", self.panel, "--referral", self.ref_text,
                  "--since", "not-a-date"])
        self.assertEqual(r2.returncode, 1)
        self.assertIn("YYYY-MM-DD", r2.stderr)
        # 窗口内无 panel runs
        r3 = tri(["--panel", self.panel, "--referral", self.ref_text,
                  "--since", "2020-01-01", "--until", "2020-02-01"])
        self.assertEqual(r3.returncode, 1)
        self.assertIn("没有面板 runs", r3.stderr)

    def test_frozen_family_still_green(self):
        """triangulate 是增量子命令: --self-test 与 --help 原样保持绿。"""
        r = run_script("citation_panel.py", ["--self-test"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("[self-test] PASS citation_panel", r.stdout)
        for args in (["--help"], ["triangulate", "--help"]):
            h = run_script("citation_panel.py", args)
            self.assertEqual(h.returncode, 0, args)


if __name__ == "__main__":
    unittest.main(verbosity=2)
