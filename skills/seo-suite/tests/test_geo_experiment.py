#!/usr/bin/env python3
"""geo_experiment.py 测试(Meridian GeoX 思路薄封装): 分组+平衡性 / 手写 OLS 2×2
DiD / 分国别异质性 / 诚实边界。
standalone(自带 run_script 助手,合成 geo CSV,零网络):
python3 tests/test_geo_experiment.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。

合成数据口径: 4 国共同趋势 +2/日;treated 国 post +lift;组级日总量平衡
(US 偶日 +3 / JP 偶日 −3 / FR 奇日 +2 / DE 奇日 +1 → 两组 pre 日均差≈1.5,
远小于趋势方差 → Welch p>0.1);pre 14 天(post 8 天=4 偶 4 奇,与 pre 同
奇偶构成 → 噪声在 DiD 中精确对消,β3 精确回收)。"""
import csv
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import geo_experiment as gx  # noqa: E402  (需先入 SCRIPTS 路径)

D0 = date(2026, 7, 1)
N = 22
IV = D0 + timedelta(days=14)          # pre 14 天 / post 8 天
IVS = IV.isoformat()
# (country, base, 偶日噪声, 奇日噪声, group)
SPEC = (("US", 100.0, 3.0, 0.0, "treated"),
        ("JP", 80.0, -3.0, 0.0, "treated"),
        ("FR", 97.0, 0.0, 2.0, "control"),
        ("DE", 83.0, 0.0, 1.0, "control"))


def make_rows(lift_map=None, spec=SPEC):
    """lift_map={country: 日增量(post 起)};缺省 treated 无 lift。"""
    rows = []
    for c, base_v, even_n, odd_n, grp in spec:
        for i in range(N):
            d = D0 + timedelta(days=i)
            v = base_v + i * 2.0 + (even_n if i % 2 == 0 else odd_n)
            if lift_map and d >= IV:
                v += lift_map.get(c, 0.0)
            rows.append({"country": c, "clicks": v, "date": d, "group": grp})
    return rows


def write_matrix(path, rows, with_group=True):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Country", "Clicks", "Date"] + (["group"] if with_group else []))
        for r in rows:
            out = [r["country"], round(r["clicks"], 2), r["date"].isoformat()]
            if with_group:
                out.append(r["group"])
            w.writerow(out)
    return path


def run_cli(*args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "geo_experiment.py"),
                            *args], capture_output=True, text=True,
                           encoding="utf-8", env=env)


class DidTests(unittest.TestCase):
    """手写 OLS 2×2: 已知效应回收 / null / 不带 group 列报错。"""

    def test_known_effect_recovered(self):
        """treated 国 post +30/日 → β3=30 精确,naive DiD 同值,p<1e-4 significant。"""
        an = gx.analyze_geo(make_rows({"US": 30.0, "JP": 30.0}), IV)
        self.assertAlmostEqual(an["ols"]["beta_interaction"], 30.0, delta=1e-6)
        self.assertAlmostEqual(an["naive_2x2"]["did"], 30.0, delta=1e-6)
        self.assertLess(an["ols"]["p_beta3"], 1e-4)
        self.assertEqual(an["verdict"], "significant")
        self.assertEqual(an["balance"]["status"], "PASS")
        # CI 覆盖真值
        self.assertLess(an["ols"]["ci_low"], 30.0)
        self.assertGreater(an["ols"]["ci_high"], 30.0)

    def test_null_no_effect_inconclusive(self):
        """无干预 → β3=0,t≈0,p≈1 → inconclusive;平衡仍 PASS。"""
        an = gx.analyze_geo(make_rows(), IV)
        self.assertAlmostEqual(an["ols"]["beta_interaction"], 0.0, delta=1e-6)
        self.assertAlmostEqual(an["ols"]["t_beta3"], 0.0, delta=1e-6)
        self.assertGreater(an["ols"]["p_beta3"], 0.9)
        self.assertEqual(an["verdict"], "inconclusive")
        self.assertEqual(an["balance"]["status"], "PASS")

    def test_per_country_heterogeneity(self):
        """US +100 / JP +20 → adjusted Δ 各自回收(对照调整后 control ≈0),排序正确;
        OLS β3 = 两 treated 国平均 lift=60。"""
        an = gx.analyze_geo(make_rows({"US": 100.0, "JP": 20.0}), IV)
        het = {h["country"]: h for h in an["per_country"]}
        self.assertAlmostEqual(het["US"]["adjusted_delta"], 100.0, delta=1.0)
        self.assertAlmostEqual(het["JP"]["adjusted_delta"], 20.0, delta=1.0)
        self.assertAlmostEqual(het["FR"]["adjusted_delta"], 0.0, delta=1.0)
        self.assertAlmostEqual(het["DE"]["adjusted_delta"], 0.0, delta=1.0)
        self.assertEqual([h["country"] for h in an["per_country"]][:2], ["US", "JP"])
        self.assertAlmostEqual(an["ols"]["beta_interaction"], 60.0, delta=1e-6)

    def test_analyze_requires_group_column(self):
        """矩阵无 group 列 → CLI rc=2,提示先 assign。"""
        tmp = tempfile.mkdtemp(prefix="geo_ng_")
        p = write_matrix(os.path.join(tmp, "geo.csv"), make_rows(), with_group=False)
        r = run_cli("analyze", "--geo-matrix", p, "--intervention", IVS)
        self.assertEqual(r.returncode, 2)
        self.assertIn("group", (r.stderr + r.stdout))


class StatisticsTests(unittest.TestCase):
    """stdlib 手写 t 分布与 Welch 检验的数值钉死。"""

    def test_welch_known_values(self):
        """均值差 9,se=√(3.5/6+3.5/6)=1.0801 → t=8.3324;df=10(Welch 精确)。"""
        t, df, p = gx.welch_ttest([10.0, 11, 12, 13, 14, 15], [1.0, 2, 3, 4, 5, 6])
        self.assertAlmostEqual(t, 8.3324, delta=1e-3)
        self.assertAlmostEqual(df, 10.0, delta=1e-9)
        self.assertLess(p, 0.001)
        # 两常数样本 → 零方差 → None(不可检验,不假装 p=1)
        self.assertIsNone(gx.welch_ttest([5.0, 5, 5], [5.0, 5, 5]))
        self.assertIsNone(gx.welch_ttest([1.0], [2.0, 3]))

    def test_t_distribution_p_and_quantiles(self):
        """t=0 → p=1;|t| 大 → p≈0;t_{0.975}: df=1≈12.706,df=10≈2.228;
        双侧 p(2.7764, df=4)≈0.05(t 分布表值)。"""
        self.assertEqual(gx.t_two_sided_p(0.0, 10), 1.0)
        self.assertLess(gx.t_two_sided_p(30.0, 50), 1e-20)
        self.assertAlmostEqual(gx.t_critical_975(1), 12.7062, delta=1e-3)
        self.assertAlmostEqual(gx.t_critical_975(10), 2.2281, delta=1e-3)
        self.assertAlmostEqual(gx.t_two_sided_p(2.7764, 4), 0.05, delta=5e-4)

    def test_auto_split_snake(self):
        """按 pre 总量降序 snake 对半: 0→T,1→C,2→C,3→T;奇数国规模差≤1。"""
        g = gx.auto_split(["A", "B", "C", "D"], {"A": 100, "B": 80, "C": 60, "D": 40})
        self.assertEqual(g, {"A": "treated", "B": "control",
                             "C": "control", "D": "treated"})
        g5 = gx.auto_split(["A", "B", "C", "D", "E"],
                           {"A": 100, "B": 80, "C": 60, "D": 40, "E": 20})
        n_t = sum(1 for v in g5.values() if v == "treated")
        self.assertIn(abs(n_t - 2), (0, 1))                 # 对半,规模差 ≤1
        self.assertEqual(len(g5), 5)

    def test_solve_linear_and_inverse(self):
        """高斯消元/求逆的手算对照。"""
        self.assertEqual(gx.solve_linear([[2, 0], [0, 4]], [4, 8]), [2.0, 2.0])
        self.assertIsNone(gx.solve_linear([[1, 1], [1, 1]], [1, 2]))   # 奇异
        inv = gx.invert_matrix([[4, 0], [0, 2]])
        self.assertAlmostEqual(inv[0][0], 0.25)
        self.assertAlmostEqual(inv[1][1], 0.5)
        inv2 = gx.invert_matrix([[2, 1], [1, 3]])
        # 手算: 1/5·[[3,−1],[−1,2]]
        self.assertAlmostEqual(inv2[0][0], 0.6)
        self.assertAlmostEqual(inv2[0][1], -0.2)
        self.assertAlmostEqual(inv2[1][1], 0.4)


class AssignCliTests(unittest.TestCase):
    """assign CLI: 显式分组 / 自动对半 / 平衡 FAIL 退出码 / --out 回写。"""

    def test_assign_explicit_balance_pass(self):
        tmp = tempfile.mkdtemp(prefix="geo_ex_")
        p = write_matrix(os.path.join(tmp, "geo.csv"), make_rows(), with_group=False)
        r = run_cli("assign", "--geo-matrix", p, "--intervention", IVS,
                    "--treated-geo", "US,JP")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("分组方法   : explicit(--treated-geo US,JP)", r.stdout)
        self.assertIn("US         treated", r.stdout)
        self.assertIn("FR         control", r.stdout)
        self.assertIn("→ PASS", r.stdout)
        self.assertIn("p>0.1", r.stdout)

    def test_assign_auto_snake(self):
        tmp = tempfile.mkdtemp(prefix="geo_au_")
        p = write_matrix(os.path.join(tmp, "geo.csv"), make_rows(), with_group=False)
        r = run_cli("assign", "--geo-matrix", p, "--intervention", IVS, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        pl = json.loads(r.stdout)
        self.assertIn("auto-snake", pl["method"])
        groups = pl["groups"]
        self.assertEqual(sorted(groups), ["DE", "FR", "JP", "US"])
        n_t = sum(1 for v in groups.values() if v == "treated")
        self.assertEqual(n_t, 2)                             # 4 国对半
        self.assertEqual(pl["balance"]["status"], "PASS")    # 组级日总量平衡构造
        # 未知国家报错
        r2 = run_cli("assign", "--geo-matrix", p, "--intervention", IVS,
                     "--treated-geo", "US,XX")
        self.assertEqual(r2.returncode, 2)
        self.assertIn("不存在的国家", r2.stderr)

    def test_assign_balance_fail_rc1(self):
        """对照组基线高一倍 → Welch p≈0 → FAIL,rc=1(仍输出完整报告)。"""
        bad_spec = (("US", 100.0, 3.0, 0.0, "treated"),
                    ("JP", 80.0, -3.0, 0.0, "treated"),
                    ("FR", 197.0, 0.0, 2.0, "control"),
                    ("DE", 183.0, 0.0, 1.0, "control"))
        tmp = tempfile.mkdtemp(prefix="geo_bf_")
        p = write_matrix(os.path.join(tmp, "geo.csv"),
                         make_rows(spec=bad_spec), with_group=False)
        r = run_cli("assign", "--geo-matrix", p, "--intervention", IVS,
                    "--treated-geo", "US,JP")
        self.assertEqual(r.returncode, 1)
        self.assertIn("→ FAIL", r.stdout)
        self.assertIn("先换分组", r.stdout)

    def test_assign_out_roundtrip_with_analyze(self):
        """assign --out 写回 group 列,analyze 吃回写文件出 DiD + 诚实边界。"""
        tmp = tempfile.mkdtemp(prefix="geo_rt_")
        p = write_matrix(os.path.join(tmp, "geo.csv"),
                         make_rows({"US": 30.0, "JP": 30.0}), with_group=False)
        out = os.path.join(tmp, "assigned.csv")
        r = run_cli("assign", "--geo-matrix", p, "--intervention", IVS,
                    "--treated-geo", "US,JP", "--out", out)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.assertIn("group", reader.fieldnames)
            rows = list(reader)
        self.assertEqual(len(rows), 4 * N)
        self.assertEqual({r_["group"] for r_ in rows if r_["Country"] == "US"},
                         {"treated"})
        r2 = run_cli("analyze", "--geo-matrix", out, "--intervention", IVS)
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIn("β3(交互项=DiD 估计)= +30.0000", r2.stdout)
        self.assertIn("SIGNIFICANT", r2.stdout)
        self.assertIn("naive DiD = +30.0000", r2.stdout)

    def test_analyze_json_and_honesty_footer(self):
        """analyze --json 结构 + 诚实边界(索引级 holdout 不可行,引 kpi-definitions)。"""
        tmp = tempfile.mkdtemp(prefix="geo_js_")
        p = write_matrix(os.path.join(tmp, "geo.csv"),
                         make_rows({"US": 30.0, "JP": 30.0}))
        r = run_cli("analyze", "--geo-matrix", p, "--intervention", IVS, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        pl = json.loads(r.stdout)
        for key in ("ols", "naive_2x2", "balance", "per_country", "verdict",
                    "n_obs", "df", "honesty", "intervention"):
            self.assertIn(key, pl, key)
        self.assertAlmostEqual(pl["ols"]["beta_interaction"], 30.0, delta=1e-6)
        self.assertEqual(pl["verdict"], "significant")
        self.assertEqual(len(pl["per_country"]), 4)
        for frag in ("SEO 无法做索引级 holdout", "kpi-definitions",
                     "分国别可暂停的活动"):
            self.assertIn(frag, pl["honesty"], frag)
        # markdown 也带诚实边界
        r2 = run_cli("analyze", "--geo-matrix", p, "--intervention", IVS)
        self.assertIn("SEO 无法做索引级 holdout", r2.stdout)
        self.assertIn("未做国家级聚类稳健", r2.stdout)      # SE 口径诚实注记

    def test_self_test_flag_and_help(self):
        r = run_cli("--self-test")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("[self-test] PASS geo_experiment", r.stdout)
        for sub in ("assign", "analyze"):
            h = run_cli(sub, "--help")
            self.assertEqual(h.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
