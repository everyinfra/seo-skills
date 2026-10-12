#!/usr/bin/env python3
"""synthetic_control.py 测试(合成数据已知干预效应回收 + placebo 校准)。
standalone(自带 run_script 助手,合成 Date,Metric CSV,零网络):
python3 tests/test_synthetic_control.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。

合成数据口径: donor 形状互异(趋势/周周期/U 形/余弦/周期阶梯)避免共线;
treated = donor 加权组合,post 期加性 lift → mean_gap 应精确回收 lift;
placebo 期望值按"每个 donor 当假处理组(真处理组不入池)"手工推导后钉死。"""
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

import synthetic_control as sc  # noqa: E402  (需先入 SCRIPTS 路径)

D0 = date(2026, 7, 1)
N = 30
IV = D0 + timedelta(days=20)          # pre 20 点 / post 10 点
IVS = IV.isoformat()

# 5 个互异形状的 donor(共线会让坐标下降收敛变慢,形状互异 10 轮即收敛)
SHAPES = [
    lambda i: 100 + 2 * i,
    lambda i: 80 + 15 * math.sin(2 * math.pi * i / 7),
    lambda i: 60 + (i - 15) ** 2 * 0.3,
    lambda i: 90 + 10 * math.cos(2 * math.pi * i / 5) + i * 0.8,
    lambda i: 70 + 5 * (i % 3),
]
TRUE_W = [0.3, 0.25, 0.2, 0.15, 0.1]


def mk(shape):
    return {D0 + timedelta(days=i): shape(i) for i in range(N)}


DONORS5 = [mk(f) for f in SHAPES]
BASE5 = {d: sum(w * m[d] for w, m in zip(TRUE_W, DONORS5)) for d in DONORS5[0]}
DONORS3 = [mk(f) for f in SHAPES[:3]]
TRUE_W3 = [0.5, 0.3, 0.2]
BASE3 = {d: sum(w * m[d] for w, m in zip(TRUE_W3, DONORS3)) for d in DONORS3[0]}


def lifted(base, lift):
    return {d: (v + lift if d >= IV else v) for d, v in base.items()}


def write_csv(path, series, skip_dates=()):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Metric"])
        for d in sorted(series):
            if d in skip_dates:
                continue
            w.writerow([d.isoformat(), round(series[d], 4)])
    return path


def make_files(tmp, treated, donors):
    tp = write_csv(os.path.join(tmp, "treated.csv"), treated)
    dps = [write_csv(os.path.join(tmp, "d%d.csv" % i), m)
           for i, m in enumerate(donors, 1)]
    return tp, dps


def run_cli(treated_path, donor_paths, *extra):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "synthetic_control.py"),
         "--treated", treated_path, "--donors", ",".join(donor_paths),
         "--intervention", IVS, *extra],
        capture_output=True, text=True, encoding="utf-8", env=env)


class SolverTests(unittest.TestCase):
    """简化 simplex 坐标下降: 权重回收 / pre RMSE / 确定性 / 数值尘埃守卫。"""

    def test_exact_mix_weight_recovery(self):
        """treated = 0.5d1+0.3d2+0.2d3(零噪声)→ 权重 1e-3 内回收,pre RMSE≈0。"""
        res = sc.analyze(BASE3, DONORS3, IV)
        for got, want in zip(res["weights"], TRUE_W3):
            self.assertAlmostEqual(got, want, delta=1e-3)
        self.assertLess(res["pre_rmse"], 1e-4)

    def test_solver_deterministic(self):
        """同输入同输出: 两次求解权重/gap 逐位一致(无随机源)。"""
        a = sc.analyze(lifted(BASE5, 100), DONORS5, IV)
        b = sc.analyze(lifted(BASE5, 100), DONORS5, IV)
        self.assertEqual(a["weights"], b["weights"])
        self.assertEqual(a["gaps"], b["gaps"])

    def test_numeric_dust_guard_zero_noise_null(self):
        """零噪声合成数据: 数值尘埃(1e-9 级 gap)不触发假显著(verdict=inconclusive)。"""
        res = sc.run_scm(BASE3, DONORS3, IV)
        self.assertLess(abs(res["mean_gap"]), 1e-6)
        self.assertEqual(res["verdict"], "inconclusive")

    def test_rounds_argument_changes_iterations(self):
        """--rounds 传递到位(1 轮比 10 轮的 pre RMSE 不更优——同目标单调下降)。"""
        y = [BASE3[d] for d in sorted(BASE3) if d < IV]
        D = [[m[d] for d in sorted(m) if d < IV] for m in DONORS3]
        w1 = sc.solve_weights(y, D, rounds=1)
        w10 = sc.solve_weights(y, D, rounds=10)
        self.assertNotEqual(w1, w10)                     # 1 轮未收敛
        for got, want in zip(w10, TRUE_W3):
            self.assertAlmostEqual(got, want, delta=1e-3)


class EffectRecoveryTests(unittest.TestCase):
    """已知干预效应回收: 正/负/相对口径/总效应。"""

    def test_additive_effect_recovered(self):
        """post +20/日 → mean_gap=20,累计=20×10 天,rel=20/反事实 post 均值。"""
        res = sc.analyze(lifted(BASE3, 20.0), DONORS3, IV)
        self.assertAlmostEqual(res["mean_gap"], 20.0, delta=1e-4)
        self.assertAlmostEqual(res["total_gap"], 200.0, delta=1e-3)
        synth_post_mean = sum(BASE3[d] for d in BASE3 if d >= IV) / 10
        self.assertAlmostEqual(res["rel_lift_pct"], 20.0 / synth_post_mean * 100,
                                delta=1e-6)
        self.assertEqual(res["verdict"], "likely_positive")

    def test_negative_effect_recovered(self):
        """post −40/日 → mean_gap=−40,likely_negative,p 值按 ≤ 方向计。"""
        res = sc.analyze(lifted(BASE5, -40.0), DONORS5, IV)
        self.assertAlmostEqual(res["mean_gap"], -40.0, delta=0.05)
        self.assertEqual(res["verdict"], "likely_negative")
        self.assertEqual(res["placebo"]["p_value"], 0.0)   # 无假效应 ≤ −40

    def test_bad_donor_fit_high_pre_rmse(self):
        """donor 与 treated 完全不相关 → pre RMSE 占均值 >20%,渲染出告警行。"""
        flat = {D0 + timedelta(days=i): 5.0 for i in range(N)}     # 常数 5
        treated = {D0 + timedelta(days=i): 500.0 + i for i in range(N)}
        res = sc.analyze(treated, [flat, flat], IV)   # 两常数 donor 合成仍是常数
        self.assertGreater(res["pre_rmse_pct"], 20)
        out = sc.render(res, "t.csv", ["d1.csv", "d2.csv"], IV)
        self.assertIn("pre RMSE>20%", out)


class PlaceboTests(unittest.TestCase):
    """placebo 检验(每个 donor 当假处理组,真处理组不入池)。"""

    def test_big_effect_placebo_p_zero(self):
        """+100/日大效应: 5 个假效应(39.4/-6.2/11.6/-4.9/-7.0)全部 < 真效应 → p=0。"""
        res = sc.analyze(lifted(BASE5, 100.0), DONORS5, IV)
        self.assertAlmostEqual(res["mean_gap"], 100.0, delta=0.05)
        gaps = [p["mean_gap"] for p in res["placebo"]["placebos"]]
        self.assertEqual(len(gaps), 5)
        self.assertTrue(all(g < 100 for g in gaps), gaps)
        self.assertEqual(res["placebo"]["p_value"], 0.0)
        self.assertEqual(res["placebo"]["p_abs"], 0.0)
        self.assertFalse(res["placebo"]["weak"])            # 5 个 donor 不标 weak

    def test_null_world_placebo_calibration(self):
        """null 世界(无干预): 真效应≈0,|真|小于全部假效应 → p_abs=1.0
        (placebo 说'在 donor 池噪声之内';描述性 CI 可能因 0.01 级偏差偏乐观,
        这正是报告里 placebo 才是校准依据的原因)。"""
        res = sc.analyze(BASE5, DONORS5, IV)
        self.assertLess(abs(res["mean_gap"]), 0.05)
        self.assertEqual(res["placebo"]["p_abs"], 1.0)
        self.assertGreaterEqual(res["placebo"]["p_value"], 0.2)   # 2/5 假效应 ≥ 真效应

    def test_single_donor_no_valid_placebo(self):
        """单 donor: 安慰剂池为空 → n=0,p=N/A,渲染含 N/A 行。"""
        res = sc.analyze(lifted(BASE3, 20.0), DONORS3[:1], IV)
        self.assertEqual(res["placebo"]["n"], 0)
        self.assertIsNone(res["placebo"]["p_value"])
        out = sc.render(res, "t.csv", ["d1.csv"], IV)
        self.assertIn("p 值 = N/A", out)
        self.assertIn("安慰剂池为空", out)


class CliTests(unittest.TestCase):
    """CLI: markdown 效应曲线 / --json 结构 / 日期对齐 / 闸门错误。"""

    def test_cli_markdown_report(self):
        tmp = tempfile.mkdtemp(prefix="sc_md_")
        tp, dps = make_files(tmp, lifted(BASE3, 20.0), DONORS3)
        r = run_cli(tp, dps)
        self.assertEqual(r.returncode, 0, r.stderr)
        for frag in ("合成控制", IVS, "pre 拟合优度] RMSE",
                     "post 因果效应估计", "LIKELY_POSITIVE", "placebo 检验",
                     "[效应曲线 post 期]", "2026-07-21", "gap 曲线",
                     "诚实边界", "简化 simplex 坐标下降", "非 CausalImpact BSTS"):
            self.assertIn(frag, r.stdout, frag)
        self.assertIn("+20.00", r.stdout)                    # 效应曲线首行 gap

    def test_cli_json_structure(self):
        tmp = tempfile.mkdtemp(prefix="sc_js_")
        tp, dps = make_files(tmp, lifted(BASE3, 20.0), DONORS3)
        r = run_cli(tp, dps, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        pl = json.loads(r.stdout)
        for key in ("tool", "intervention", "treated", "donors", "solver", "weights",
                    "pre_fit", "effect", "effect_curve", "placebo", "caveat"):
            self.assertIn(key, pl, key)
        self.assertEqual(pl["intervention"], IVS)
        self.assertEqual(len(pl["effect_curve"]), 10)        # post 10 天
        self.assertAlmostEqual(pl["effect"]["mean_gap"], 20.0, delta=1e-3)
        self.assertEqual(pl["effect"]["verdict"], "likely_positive")
        self.assertEqual(len(pl["placebo"]["placebos"]), 3)
        self.assertIn("非 CausalImpact BSTS", pl["solver"])

    def test_date_alignment_drop_count(self):
        """donor 缺 3 个日期 → 交集对齐,dropped=3,post 点随之减少。"""
        tmp = tempfile.mkdtemp(prefix="sc_al_")
        miss = {D0 + timedelta(days=22 + i) for i in range(3)}
        tp = write_csv(os.path.join(tmp, "t.csv"), lifted(BASE3, 20.0))
        dps = [write_csv(os.path.join(tmp, "d%d.csv" % k),
                         m if k != 2 else {d: v for d, v in m.items() if d not in miss},
                         skip_dates=miss if k == 2 else ())
               for k, m in enumerate(DONORS3, 1)]
        r = run_cli(tp, dps, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        pl = json.loads(r.stdout)
        # donor2 缺 3 天 → 交集少 3 天;treated + 3 个 donor 各弃 3 个日期点 = 9
        self.assertEqual(pl["pre_fit"]["dropped_dates"], 9)
        self.assertEqual(len(pl["effect_curve"]), 7)         # post 10−3

    def test_gate_errors_exit_2(self):
        tmp = tempfile.mkdtemp(prefix="sc_gt_")
        tp, dps = make_files(tmp, BASE3, DONORS3)
        short = {D0 + timedelta(days=i): 100.0 + i
                 for i in (0, 1, 2, 3, 4, 20, 21)}                     # pre 5 点 + post 2 点
        sp = write_csv(os.path.join(tmp, "short.csv"), short)
        r = run_cli(sp, dps)
        self.assertEqual(r.returncode, 2)
        self.assertIn("pre 期 5 点<6", r.stderr)
        # 干预日早于全部数据 → post 全有 pre 没有
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r2 = subprocess.run([sys.executable, os.path.join(SCRIPTS, "synthetic_control.py"),
                             "--treated", tp, "--donors", ",".join(dps),
                             "--intervention", "2026-06-01"],
                            capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r2.returncode, 2)
        self.assertIn("两侧都有数据", r2.stderr)
        # 文件不存在 / 缺列 / 缺参数
        r3 = run_cli(tp, [os.path.join(tmp, "nope.csv")])
        self.assertEqual(r3.returncode, 2)
        bad = os.path.join(tmp, "bad.csv")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("Foo,Bar\n1,2\n")
        r4 = run_cli(tp, [bad])
        self.assertEqual(r4.returncode, 2)
        self.assertIn("Date 和 Metric", r4.stderr)
        r5 = subprocess.run([sys.executable, os.path.join(SCRIPTS, "synthetic_control.py")],
                            capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r5.returncode, 2)
        self.assertIn("缺少必选参数", r5.stderr)

    def test_single_donor_cli_note_and_help(self):
        tmp = tempfile.mkdtemp(prefix="sc_sd_")
        tp, dps = make_files(tmp, lifted(BASE3, 20.0), DONORS3[:1])
        r = run_cli(tp, dps, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("退化为单对照", r.stderr)
        self.assertEqual(json.loads(r.stdout)["placebo"]["n"], 0)
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        h = subprocess.run([sys.executable, os.path.join(SCRIPTS, "synthetic_control.py"),
                            "--help"], capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(h.returncode, 0)
        self.assertIn("--intervention", h.stdout)

    def test_self_test_flag(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "synthetic_control.py"),
                            "--self-test"], capture_output=True, text=True,
                           encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("[self-test] PASS synthetic_control", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
