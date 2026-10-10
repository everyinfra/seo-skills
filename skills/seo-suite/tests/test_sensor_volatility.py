#!/usr/bin/env python3
"""sensor_volatility.py 测试: 自有词集 SERP 波动分(Semrush Sensor 口径的自研版)。
standalone(自带 run_script 助手,合成 CSV,零网络):
  python3 tests/test_sensor_volatility.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。

口径(与脚本一致): D_k=|Δpos|/20(Top-20,丢失=新进=1.0,单查询封顶 1.0);
score=clamp(round(10×mean,1),0,10);分档 0-2/2-5/5-8/8-10(边界值归上档);
z30=前置 ≤30 天窗 z(总体 std),基线<2 天或 std=0→null,|z|≥2=异常日。
所有期望值均按上述规则手工推导后在断言中钉死。

合成数据(spike_csv,20 词 ×6 日,offset 为全体词的日偏移):
  10-01 off=0 | 10-02 off=2 | 10-03 off=2 | 10-04 off=0 | 10-05 off=0 | 10-06 off=22
逐日分: 1.0 / 0.0 / 1.0 / 0.0 / 10.0;z30: null / null / +1.0 / -1.41 / +19.0
(d6 基线=[1,0,1,0] → mean .5 std .5 → z=(10-.5)/.5=19 → 异常日+疑似算法更新)。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import sensor_volatility as sv  # noqa: E402  (需先入 SCRIPTS 路径)


def run_script(*args):
    """独立助手(与 run_tests.py 同形):子进程跑 scripts/sensor_volatility.py。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "sensor_volatility.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_csv(text):
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    f.write(text)
    f.close()
    return f.name


def build_csv(days):
    """{date: {query: pos}} → Date,Query,Position 三列 CSV。"""
    lines = ["Date,Query,Position"]
    for d in sorted(days):
        for q in sorted(days[d]):
            lines.append(f"{d},{q},{days[d][q]}")
    return "\n".join(lines) + "\n"


def gsc_csv(days):
    """同数据按 GSC 导出格式(Date,Query,Clicks,Impressions,CTR,Position)。"""
    lines = ["Date,Query,Clicks,Impressions,CTR,Position"]
    for d in sorted(days):
        for q in sorted(days[d]):
            lines.append(f"{d},{q},5,100,3.2%,{days[d][q]}")
    return "\n".join(lines) + "\n"


def spike_days():
    """20 词 ×6 日;q_i 基准位次=i,日偏移见模块 docstring。"""
    offsets = {"2026-10-01": 0, "2026-10-02": 2, "2026-10-03": 2,
               "2026-10-04": 0, "2026-10-05": 0, "2026-10-06": 22}
    return {d: {f"q{i:02d}": float(i + off) for i in range(1, 21)}
            for d, off in offsets.items()}


def movers_days():
    """13 词(并集)×2 日:q01 涨(5→2)/q02 跌(3→16)/q03 丢失/q99 新进,9 个 filler 不动。
    单日分 = (0.15+0.65+1+1)/13×10 = 2.2 → normal 档(丢失/新进计入并集分母)。"""
    filler = {f"f{i:02d}": 20.0 for i in range(4, 13)}
    return {"2026-10-01": dict({"q01": 5.0, "q02": 3.0, "q03": 10.0}, **filler),
            "2026-10-02": dict({"q01": 2.0, "q02": 16.0, "q99": 4.0}, **filler)}


class SensorVolatilityUnitTests(unittest.TestCase):
    """纯函数口径:D_k 特判 / 缩放 clamp / 分档边界 / z 空值。"""

    def test_day_deltas_basic_lost_new(self):
        d = sv.day_deltas({"a": 5.0, "b": 10.0}, {"a": 7.0, "c": 3.0})
        self.assertAlmostEqual(d["a"], 0.1)          # |5-7|/20
        self.assertEqual(d["b"], 1.0)                # 丢失=1.0
        self.assertEqual(d["c"], 1.0)                # 新进=1.0
        self.assertAlmostEqual(sv.score_from_deltas(d), 7.0)  # 10×(2.1/3)

    def test_day_deltas_cap_and_score_clamp(self):
        d = sv.day_deltas({"a": 1.0}, {"a": 50.0})
        self.assertEqual(d["a"], 1.0)                # 49/20 封顶 1.0(Top-20 口径)
        self.assertEqual(sv.score_from_deltas(d), 10.0)  # 满幅 → 10,不越界

    def test_score_rounding(self):
        self.assertEqual(sv.score_from_deltas({"a": 0.1, "b": 0.2}), 1.5)  # round(10×0.15,1)
        self.assertEqual(sv.score_from_deltas({"a": 0.0, "b": 0.0}), 0.0)

    def test_band_boundaries(self):
        self.assertEqual(sv.band_of(0.0), "low")
        self.assertEqual(sv.band_of(1.99), "low")
        self.assertEqual(sv.band_of(2.0), "normal")    # 边界归上档
        self.assertEqual(sv.band_of(4.9), "normal")
        self.assertEqual(sv.band_of(5.0), "high")
        self.assertEqual(sv.band_of(7.9), "high")
        self.assertEqual(sv.band_of(8.0), "very high")
        self.assertEqual(sv.band_of(10.0), "very high")

    def test_zscore_null_cases(self):
        self.assertIsNone(sv.zscore(5.0, []))          # 基线<2 天
        self.assertIsNone(sv.zscore(5.0, [0.0]))       # 基线<2 天
        self.assertIsNone(sv.zscore(5.0, [1.0, 1.0]))  # std=0
        self.assertEqual(sv.zscore(1.0, [1.0, 0.0]), 1.0)  # (1-.5)/.5


class SensorVolatilityCliTests(unittest.TestCase):
    """CLI 子进程:spike 异常日 / context JSON / 退出码 / 警告 / markdown。"""

    def test_spike_day_score_band_abnormal(self):
        p = tmp_csv(build_csv(spike_days()))
        self.addCleanup(os.unlink, p)
        r = run_script("--positions", p, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        o = json.loads(r.stdout)
        self.assertEqual(o["query_count"], 20)
        self.assertEqual(o["warnings"], [])
        self.assertEqual(len(o["days"]), 5)  # 6 数据日 → 5 可评分日
        self.assertEqual(o["days"][0], {"date": "2026-10-02", "score": 1.0,
                                        "band": "low", "z30": None, "abnormal": False})
        self.assertEqual(o["days"][3]["z30"], -1.41)   # 基线 [1,0,1] → z=-1.4142
        self.assertEqual(o["days"][4], {"date": "2026-10-06", "score": 10.0,
                                        "band": "very high", "z30": 19.0, "abnormal": True})
        self.assertEqual(o["abnormal_days"], ["2026-10-06"])
        self.assertTrue(o["algorithm_update_suspected"])   # score≥8 提示
        self.assertEqual(o["algorithm_update_days"], ["2026-10-06"])

    def test_context_json_shape_and_default_date(self):
        p = tmp_csv(build_csv(spike_days()))
        self.addCleanup(os.unlink, p)
        r = run_script("--positions", p, "--context", "--date", "2026-10-06")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(r.stdout.strip().splitlines()), 1)  # 单行 JSON
        o = json.loads(r.stdout)
        self.assertEqual(set(o), {"date", "score", "band", "z30", "verdict"})
        self.assertEqual(o, {"date": "2026-10-06", "score": 10.0, "band": "very high",
                             "z30": 19.0, "verdict": "high_volatility"})
        rd = run_script("--positions", p, "--context")           # 缺省=最新可评分日
        self.assertEqual(json.loads(rd.stdout), o)

    def test_context_normal_day(self):
        p = tmp_csv(build_csv(spike_days()))
        self.addCleanup(os.unlink, p)
        r = run_script("--positions", p, "--context", "--date", "2026-10-04")
        self.assertEqual(json.loads(r.stdout), {"date": "2026-10-04", "score": 1.0,
                                                "band": "low", "z30": 1.0,
                                                "verdict": "normal"})

    def test_context_missing_date_exit_2(self):
        p = tmp_csv(build_csv(spike_days()))
        self.addCleanup(os.unlink, p)
        r = run_script("--positions", p, "--context", "--date", "2026-01-01")
        self.assertEqual(r.returncode, 2)
        self.assertIn("无波动分", r.stderr)
        r2 = run_script("--positions", p, "--context", "--date", "2026-10-01")  # 首日无分
        self.assertEqual(r2.returncode, 2)

    def test_single_day_exit_2(self):
        p = tmp_csv(build_csv({"2026-10-01": {"a": 1.0, "b": 2.0}}))
        self.addCleanup(os.unlink, p)
        r = run_script("--positions", p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("单日", r.stderr)

    def test_small_wordset_warning(self):
        days = {"2026-10-01": {"a": 1.0, "b": 5.0, "c": 9.0},
                "2026-10-02": {"a": 3.0, "b": 5.0, "c": 9.0}}  # 3 词 <10
        p = tmp_csv(build_csv(days))
        self.addCleanup(os.unlink, p)
        r = run_script("--positions", p)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("词集过小(3<10),分数不稳定", r.stderr)  # 警告走 stderr
        self.assertIn("词集过小,分数不稳定", r.stdout)        # 也进正文
        rj = run_script("--positions", p, "--json")
        self.assertEqual(json.loads(rj.stdout)["warnings"],
                         ["词集过小(3<10),分数不稳定"])

    def test_markdown_sections_and_movers(self):
        p = tmp_csv(build_csv(movers_days()))
        self.addCleanup(os.unlink, p)
        r = run_script("--gsc", p)
        self.assertEqual(r.returncode, 0, r.stderr)
        for sec in ("# 自有词集 SERP 波动分", "## 逐日分数", "## 波动图",
                    "## 异常日", "## Top 涨跌查询(2026-10-02 vs 2026-10-01)"):
            self.assertIn(sec, r.stdout)
        self.assertIn("| 2026-10-02 | 2.2 | normal | — | — |", r.stdout)  # 逐日表
        self.assertIn("*", r.stdout.split("波动图")[1].split("```")[1])    # ASCII 图有点
        self.assertIn("q01: 5.0 → 2.0(+3.0 位)", r.stdout)                 # 涨
        self.assertIn("q02: 3.0 → 16.0(-13.0 位)", r.stdout)               # 跌
        self.assertIn("\n- q03\n", r.stdout)                             # 丢失清单行
        self.assertIn("\n- q99\n", r.stdout)                             # 新进清单行

    def test_gsc_columns_equivalent(self):
        days = spike_days()
        p1, p2 = tmp_csv(build_csv(days)), tmp_csv(gsc_csv(days))
        self.addCleanup(os.unlink, p1)
        self.addCleanup(os.unlink, p2)
        o1 = json.loads(run_script("--positions", p1, "--json").stdout)
        o2 = json.loads(run_script("--gsc", p2, "--json").stdout)
        self.assertEqual(o1["days"], o2["days"])  # 多余 Clicks/Impressions/CTR 列不影响

    def test_help(self):
        r = run_script("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("sensor_volatility.py", r.stdout)
        for flag in ("--gsc", "--positions", "--context", "--date", "--json", "--top"):
            self.assertIn(flag, r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
