#!/usr/bin/env python3
"""split_test.py golden 用例(stdlib unittest,合成泊松点击数据,零网络)。
规格=pipeline-completeness.md 第五节 R6"归因实验:split_test+功效计算(最足)"
+ SearchPilot 口径(seo-drift-monitoring.md:页面级 split test 唯一真因果检验;
program-management.md:预注册判读防移动球门)。覆盖:--help 三子命令/功效与 MDE
下限金标值(测试内用 NormalDist 独立重算)/功效单调性(页数↑·MDE↑)/达标组合
回验/分层平衡(层内 |t−c|≤1)/seed 复现与敏感/crossover 两期互换/已知参数回收
(泊松 +10% 大样本检出)/无效应 inconclusive/小样本 insufficient+MDE 提示不猜/
零流量页剔除报告/Welch 金标(测试内独立算术)/周数标度不变性/95% CI 覆盖率仿真
(1000 次,93-97%)/预注册写档-核验-冻结 α/错误路径。
独立可运行:python3 tests/test_split_test.py;也被 run_tests.py 自动发现。"""
import json
import math
import os
import random
import shutil
import statistics
import subprocess
import sys
import tempfile
import unittest
from statistics import NormalDist

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import split_test as st  # noqa: E402  (in-process:覆盖率仿真/独立重算)

ND = NormalDist()


def run_script(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "split_test.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def poisson(rng, lam):
    """Knuth 泊松抽样(stdlib random 无 poisson,手写;小 λ 高效)。"""
    L = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


class SplitTestBase(unittest.TestCase):
    """tmp 目录夹具。"""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="split-test-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def path(self, name):
        return os.path.join(self.dir, name)

    def gsc_csv(self, name, base_url, values):
        """合成 GSC 页面级导出(Page,Clicks)。"""
        p = self.path(name)
        with open(p, "w", encoding="utf-8") as f:
            f.write("Page,Clicks\n")
            for i, v in enumerate(values):
                f.write(f"{base_url}/p{i},{v}\n")
        return p

    def poisson_csv(self, name, base_url, n, lam, rng):
        return self.gsc_csv(name, base_url, [poisson(rng, lam) for _ in range(n)])


class HelpAndPlanTests(SplitTestBase):

    def test_help_all_subcommands(self):
        for args in (["--help"], ["plan", "--help"], ["assign", "--help"],
                     ["analyze", "--help"]):
            r = run_script(args)
            self.assertEqual(r.returncode, 0, args)
        top = run_script(["--help"]).stdout
        for kw in ("plan", "assign", "analyze"):
            self.assertIn(kw, top)

    def test_plan_power_and_floor_golden(self):
        """/tmp 金标:120 页×8 周·基线 2.5·MDE 10% → 功效≈0.6878,下限≈11.44%
        (测试内用 NormalDist 独立重算,不吃脚本内部函数)。也钉 `--plan` 拼写兼容。"""
        r = run_script(["--plan", "--pages", "120", "--baseline-clicks", "2.5",
                        "--weeks", "8", "--json"])
        self.assertEqual(r.returncode, 0)
        rep = json.loads(r.stdout)
        sigma = math.sqrt(2.5)                       # 泊松 var=mean
        se = sigma * math.sqrt(2.0 / 480.0)          # 每臂 480 页·周
        lam = 0.25 / se
        z = ND.inv_cdf(0.975)
        want_power = ND.cdf(lam - z) + ND.cdf(-lam - z)
        want_floor = (z + ND.inv_cdf(0.80)) * se / 2.5
        self.assertAlmostEqual(rep["power_at_mde"]["power"], round(want_power, 4),
                               places=4)
        self.assertAlmostEqual(rep["mde_floor"]["value"], round(want_floor, 4), places=4)
        self.assertEqual([r["power"] for r in rep["requirements"]], [0.6, 0.8, 0.9])
        text = run_script(["plan", "--pages", "120", "--baseline-clicks", "2.5",
                           "--weeks", "8"]).stdout
        self.assertIn("组合表", text)                 # 人读组合表在场
        self.assertIn("0.6", text)

    def test_power_monotonicity(self):
        """页数↑功效↑ / MDE↑功效↑ / 页数↑ MDE 下限↓(功效单调性)。"""
        base = ["plan", "--baseline-clicks", "2.5", "--weeks", "8", "--json"]

        def power(pages, mde="0.1"):
            r = run_script(base + ["--pages", str(pages), "--mde", mde])
            return json.loads(r.stdout)

        p60, p120, p480 = (power(n)["power_at_mde"]["power"] for n in (60, 120, 480))
        self.assertLess(p60, p120)
        self.assertLess(p120, p480)
        self.assertLess(power(120, "0.05")["power_at_mde"]["power"],
                        power(120, "0.2")["power_at_mde"]["power"])
        f120, f480 = power(120)["mde_floor"]["value"], power(480)["mde_floor"]["value"]
        self.assertLess(f480, f120)

    def test_plan_requirements_reachable(self):
        """推荐组合(页数@当前周)回验:按该页数重算功效 ≥ 目标−0.005。"""
        r = run_script(["plan", "--pages", "120", "--baseline-clicks", "2.5",
                        "--weeks", "8", "--json"])
        rep = json.loads(r.stdout)
        sigma = math.sqrt(2.5)
        for req in rep["requirements"]:
            pages = req["pages_at_current_weeks"]
            n_arm = pages * 8 * 0.5
            pw = st.power_two_sample(0.25, sigma, n_arm, n_arm, 0.05)
            self.assertGreaterEqual(pw, req["power"] - 0.005, req)


class AssignTests(SplitTestBase):

    URLS = ([f"https://s.com/guides/g{i}" for i in range(9)]
            + [f"https://s.com/blog/b{i}" for i in range(14)]
            + [f"https://s.com/shop/p{i}" for i in range(3)]
            + ["https://s.com/"])

    def urls_file(self, urls=None):
        p = self.path("urls.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(urls if urls is not None else self.URLS) + "\n")
        return p

    def assign(self, *extra):
        return run_script(["assign", "--urls", self.urls_file(), *extra, "--json"])

    def test_stratified_balance(self):
        """层内 |treatment−control|≤1;每 URL 恰一组;组名只有两值。"""
        rep = json.loads(self.assign("--seed", "42").stdout)
        for name, s in rep["strata"].items():
            self.assertLessEqual(abs(s["treatment"] - s["control"]), 1, name)
            self.assertEqual(s["treatment"] + s["control"], s["pages"], name)
        asg = rep["assignments"]
        self.assertEqual(len(asg), len(self.URLS))
        self.assertEqual(len({a["url"] for a in asg}), len(self.URLS))
        self.assertTrue(all(a["period1"] in ("treatment", "control") for a in asg))
        self.assertEqual(sum(s["pages"] for s in rep["strata"].values()), len(self.URLS))
        # 层名 = URL 目录首段(小写):root 页归 (root)
        self.assertIn("(root)", rep["strata"])

    def test_seed_reproducible_and_sensitive(self):
        r1 = self.assign("--seed", "42")
        r2 = self.assign("--seed", "42")
        self.assertEqual(r1.stdout, r2.stdout)      # 同 seed 字节级复现
        r3 = json.loads(self.assign("--seed", "43").stdout)
        r1j = json.loads(r1.stdout)
        self.assertNotEqual([a["period1"] for a in r1j["assignments"]],
                            [a["period1"] for a in r3["assignments"]])

    def test_crossover_swaps_groups(self):
        """crossover=5:每个 URL 的 P2 = P1 互换;期标签含周 5。"""
        rep = json.loads(self.assign("--seed", "7", "--crossover", "5").stdout)
        self.assertEqual(rep["crossover_week"], 5)
        self.assertEqual(rep["period1_weeks"], "1-4")
        self.assertEqual(rep["period2_weeks"], "5+")
        swap = {"treatment": "control", "control": "treatment"}
        for a in rep["assignments"]:
            self.assertEqual(a["period2"], swap[a["period1"]], a["url"])
        text = run_script(["assign", "--urls", self.urls_file(),
                           "--crossover", "5"]).stdout
        self.assertIn("第 5 周起组间互换", text)


class AnalyzeTests(SplitTestBase):

    def test_known_effect_recovered(self):
        """已知参数回收:泊松 λ_t=5.5 vs λ_c=5.0(+10%),1500 页/臂 →
        检出 significant_positive,lift≈+10% 且 95% CI 覆盖真值 0.10。"""
        rng = random.Random(11)
        t = self.poisson_csv("t.csv", "https://s.com/guides", 1500, 5.5, rng)
        c = self.poisson_csv("c.csv", "https://s.com/blog", 1500, 5.0, rng)
        r = run_script(["analyze", "--treated", t, "--control", c,
                        "--weeks", "2", "--json"])
        self.assertEqual(r.returncode, 0)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["verdict"], "significant_positive")
        self.assertGreater(rep["relative_lift"], 0.06)
        self.assertLess(rep["relative_lift"], 0.14)
        self.assertLess(rep["ci95"][0], 0.5)          # 绝对真差 0.5 点击/页
        self.assertGreater(rep["ci95"][1], 0.5)
        self.assertLess(rep["p_value"], 0.001)

    def test_no_effect_inconclusive(self):
        """两臂同分布(λ=5.0)→ CI 跨 0 → inconclusive(不上方向)。"""
        rng = random.Random(3)
        t = self.poisson_csv("t.csv", "https://s.com/guides", 1500, 5.0, rng)
        c = self.poisson_csv("c.csv", "https://s.com/blog", 1500, 5.0, rng)
        r = run_script(["analyze", "--treated", t, "--control", c, "--json"])
        rep = json.loads(r.stdout)
        self.assertEqual(rep["verdict"], "inconclusive")
        self.assertLess(rep["ci95"][0], 0.0)
        self.assertGreater(rep["ci95"][1], 0.0)

    def test_small_sample_insufficient(self):
        """每臂 8 页(<10 闸门)→ insufficient_data + 只报 MDE 下限提示,不猜方向。"""
        rng = random.Random(5)
        t = self.poisson_csv("t.csv", "https://s.com/guides", 8, 5.5, rng)
        c = self.poisson_csv("c.csv", "https://s.com/blog", 8, 5.0, rng)
        r = run_script(["analyze", "--treated", t, "--control", c])
        self.assertEqual(r.returncode, 1)
        self.assertIn("insufficient_data", r.stdout)
        self.assertIn("只能检测", r.stdout)          # ">X% MDE"提示
        self.assertNotIn("significant_positive", r.stdout)
        self.assertNotIn("significant_negative", r.stdout)
        j = json.loads(run_script(["analyze", "--treated", t, "--control", c,
                                   "--json"]).stdout)
        self.assertGreater(j["mde_floor_power80"], 0.15)   # 小样本下限必然很宽

    def test_zero_traffic_preprocess_reported(self):
        """零流量页剔除并报比例;有效页均值不受零页影响。"""
        vals_t = [5, 6, 4, 7, 5, 6, 8, 5, 6, 7, 0, 0, 0]      # 13 行,3 零
        vals_c = [4, 5, 3, 6, 4, 5, 6, 4, 5, 5, 0, 0]         # 12 行,2 零
        t = self.gsc_csv("t.csv", "https://s.com/guides", vals_t)
        c = self.gsc_csv("c.csv", "https://s.com/blog", vals_c)
        r = run_script(["analyze", "--treated", t, "--control", c])
        self.assertIn("剔除零流量 3 页", r.stdout)
        self.assertIn("剔除零流量 2 页", r.stdout)
        rep = json.loads(run_script(["analyze", "--treated", t, "--control", c,
                                     "--json"]).stdout)
        self.assertEqual(rep["preprocess"]["treated"]["zero_click_removed"], 3)
        self.assertEqual(rep["preprocess"]["control"]["pages_used"], 10)
        self.assertAlmostEqual(rep["means"]["treated_window"],
                               statistics.fmean(vals_t[:10]), places=3)

    def test_welch_golden_independent_arithmetic(self):
        """Welch t/df/均值差金标:测试内独立算术(statistics)复算,不吃脚本函数。"""
        vt = [8, 9, 10, 11, 12, 13, 7, 12, 11, 10, 9, 12]
        vc = [6, 7, 8, 7, 9, 8, 6, 7, 9, 8, 7, 8]
        t = self.gsc_csv("t.csv", "https://s.com/guides", vt)
        c = self.gsc_csv("c.csv", "https://s.com/blog", vc)
        rep = json.loads(run_script(["analyze", "--treated", t, "--control", c,
                                     "--json"]).stdout)
        m1, m2 = statistics.fmean(vt), statistics.fmean(vc)
        v1, v2 = statistics.variance(vt), statistics.variance(vc)
        a1, a2 = v1 / 12, v2 / 12
        want_t = (m1 - m2) / math.sqrt(a1 + a2)
        want_df = (a1 + a2) ** 2 / (a1 ** 2 / 11 + a2 ** 2 / 11)
        self.assertAlmostEqual(rep["diff"], m1 - m2, places=4)
        self.assertAlmostEqual(rep["t"], round(want_t, 4), places=4)
        self.assertAlmostEqual(rep["df"], round(want_df, 2), places=2)
        # CI 关于均值差对称、α 更小(99%)→ CI 更宽、方向判定正确
        mid = (rep["ci95"][0] + rep["ci95"][1]) / 2
        self.assertAlmostEqual(mid, rep["diff"], places=3)
        rep01 = json.loads(run_script(["analyze", "--treated", t, "--control", c,
                                       "--alpha", "0.01", "--json"]).stdout)
        self.assertGreater(rep01["ci95"][1] - rep01["ci95"][0],
                           rep["ci95"][1] - rep["ci95"][0])
        self.assertEqual(rep["verdict"], "significant_positive")
        self.assertLess(rep["p_value"], 0.001)

    def test_weeks_scale_invariance(self):
        """--weeks 只换算周均,不改 t/CI/lift(标度不变性)。"""
        rng = random.Random(9)
        t = self.poisson_csv("t.csv", "https://s.com/guides", 40, 5.5, rng)
        c = self.poisson_csv("c.csv", "https://s.com/blog", 40, 5.0, rng)
        r1 = json.loads(run_script(["analyze", "--treated", t, "--control", c,
                                    "--weeks", "1", "--json"]).stdout)
        r2 = json.loads(run_script(["analyze", "--treated", t, "--control", c,
                                    "--weeks", "2", "--json"]).stdout)
        self.assertEqual(r1["t"], r2["t"])
        self.assertEqual(r1["ci95"], r2["ci95"])
        self.assertEqual(r1["relative_lift"], r2["relative_lift"])
        self.assertAlmostEqual(r2["means"]["treated_weekly"] * 2,
                               r1["means"]["treated_window"], places=3)
        self.assertEqual(r2["weeks"], 2)

    def test_ci_coverage_simulation(self):
        """95% CI 覆盖率仿真:同分布泊松(λ=5,n=60/臂)抽 1000 次,
        0 落入 Welch 95% CI 的比例须在 93-97%(标称 95%)。"""
        rng = random.Random(2026)
        covered = 0
        reps = 1000
        for _ in range(reps):
            xs = [poisson(rng, 5.0) for _ in range(60)]
            ys = [poisson(rng, 5.0) for _ in range(60)]
            w = st.welch(xs, ys, alpha=0.05)
            if w["ci_lo"] <= 0.0 <= w["ci_hi"]:
                covered += 1
        cov = covered / reps
        self.assertGreaterEqual(cov, 0.93)
        self.assertLessEqual(cov, 0.97)


class PreregTests(SplitTestBase):

    def plan_args(self):
        return ["plan", "--pages", "3000", "--baseline-clicks", "2.5",
                "--weeks", "2", "--mde", "0.1"]

    def test_prereg_write_verify_and_frozen_alpha(self):
        """写档冻结 → 同参核验一致(rc 0)→ 改 MDE 核验漂移(rc 1);
        analyze --plan 按冻结 α 判读(CLI --alpha 被忽略)+ 窗口漂移警告。"""
        plan = self.path("plan.json")
        r = run_script(self.plan_args() + ["--save-plan", plan])
        self.assertEqual(r.returncode, 0)
        with open(plan, encoding="utf-8") as f:
            frozen = json.load(f)
        self.assertEqual(frozen["params"]["mde"], 0.1)
        self.assertEqual(frozen["judgement"]["alpha"], 0.05)
        self.assertIn("read_when", frozen["judgement"])     # 防 peeking:读数时点写死
        # 同参核验一致
        rv = run_script(self.plan_args() + ["--verify-plan", plan])
        self.assertEqual(rv.returncode, 0)
        self.assertIn("参数一致", rv.stdout)
        # 改 MDE → 漂移 rc 1(移动球门)
        rv2 = run_script(["plan", "--pages", "3000", "--baseline-clicks", "2.5",
                          "--weeks", "2", "--mde", "0.05", "--verify-plan", plan])
        self.assertEqual(rv2.returncode, 1)
        self.assertIn("mde", rv2.stdout)
        # analyze 按冻结 α:CLI --alpha 0.01 被忽略 + 窗口警告
        rng = random.Random(11)
        t = self.poisson_csv("t.csv", "https://s.com/guides", 1500, 5.5, rng)
        c = self.poisson_csv("c.csv", "https://s.com/blog", 1500, 5.0, rng)
        ra = run_script(["analyze", "--treated", t, "--control", c, "--weeks", "2",
                         "--alpha", "0.01", "--plan", plan, "--json"])
        rep = json.loads(ra.stdout)
        self.assertTrue(rep["preregistered"])
        self.assertEqual(rep["alpha_used"], 0.05)
        self.assertTrue(any("冻结" in w for w in rep["warnings"]))
        ra2 = run_script(["analyze", "--treated", t, "--control", c, "--weeks", "4",
                          "--plan", plan, "--json"])
        self.assertTrue(any("窗口漂移" in w for w in json.loads(ra2.stdout)["warnings"]))


class ErrorPathTests(SplitTestBase):

    def test_error_paths_exit_2(self):
        cases = [
            ["analyze", "--treated", "/nope1.csv", "--control", "/nope2.csv"],
            ["plan", "--pages", "10", "--baseline-clicks", "2.5", "--weeks", "2",
             "--alpha", "1.5"],
            ["plan", "--pages", "10", "--baseline-clicks", "0", "--weeks", "2"],
            ["plan", "--pages", "10", "--baseline-clicks", "2.5", "--weeks", "2",
             "--mde", "-0.1"],
            ["assign", "--urls", "/nope-urls.txt"],
            ["assign", "--urls", self.gsc_csv("u.txt", "u", [1]), "--ratio", "1.0"],
        ]
        for args in cases:
            r = run_script(args)
            self.assertEqual(r.returncode, 2, args)
            self.assertIn("[error]", r.stderr, args)

    def test_assign_crossover_validation(self):
        p = self.gsc_csv("u.txt", "https://s.com/guides", [1, 2, 3])
        r = run_script(["assign", "--urls", p, "--crossover", "1"])
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
