#!/usr/bin/env python3
"""forecast.py golden 用例(stdlib unittest,合成数据,零网络)。
seoClarity 六步口径钉死 references/research/borrow-specs.md E1:
步2 est_traffic 计算 / 默认曲线锚点插值 / 自有曲线替换 / 三 scenario 官方枚举
(>30 位排除、rank 不预测退步、pct/pos clamp≥1) / 校准系数持久化与套用 /
orders·value·acquisition·ROI / 无 cpc 列 N/A / 商业提案双结构与 ROI 五法 /
管理层模板七段式。独立可运行:python3 tests/test_forecast.py;也被
tests/run_tests.py 自动发现。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)


def run_script(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "forecast.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_file(content, suffix=".csv"):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


# 自有曲线:锚点 (1,.2)(2,.1)(3,.05)(4,.02)(5,.01),5 位以外 clamp
CURVE_CSV = ("position,ctr\n"
             "1,20%\n"
             "2,0.10\n"
             "3,5%\n"
             "4,0.02\n"
             "5,1%\n")

# k1/k2 入榜(≤30);k3=35 位 >30 → 排除出情景,但计入步 2 est
KWS_CSV = ("keyword,search_volume,current_position,cpc\n"
           "k1,1000,4,1.0\n"
           "k2,500,2,2.0\n"
           "k3,200,35,5.0\n")

KWS_NO_CPC = ("keyword,search_volume,current_position\n"
              "k1,1000,4\n"
              "k2,500,2\n"
              "k3,200,35\n")

# 默认曲线 [est] 下:alpha pos1=280 + beta pos4 插值 .09=45 + gamma pos31≈.00994
KWS_DEFAULT_CURVE = ("keyword,search_volume,current_position\n"
                     "alpha,1000,1\n"
                     "beta,500,4\n"
                     "gamma,100,31\n")


def kws_and_curve(kws=KWS_CSV, extra=(), as_json=True):
    p = tmp_file(kws)
    c = tmp_file(CURVE_CSV)
    args = ["--kws", p, "--ctr", c]
    if as_json:
        args.append("--json")
    return p, c, run_script([*args, *extra])


class CurveAndEstimateTests(unittest.TestCase):
    """--help / 默认曲线锚点+插值 / 自有曲线替换 / 步2 est 全词口径"""

    def test_help(self):
        r = run_script(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage:", r.stdout)
        self.assertIn("--scenario", r.stdout)
        self.assertIn("rank3", r.stdout)      # 官方三枚举进 help
        self.assertIn("pct10", r.stdout)
        self.assertIn("pos2", r.stdout)

    def test_default_curve_interpolation(self):
        import forecast as fc
        self.assertEqual(fc.ctr_at(1), 0.28)          # 锚点原值(与 gsc_mining EXP_CTR 同源)
        self.assertEqual(fc.ctr_at(2), 0.15)
        self.assertEqual(fc.ctr_at(3), 0.11)
        self.assertAlmostEqual(fc.ctr_at(4), 0.09)    # (3,.11)-(5,.07) 线性插值
        self.assertAlmostEqual(fc.ctr_at(2.5), 0.13)  # (2,.15)-(3,.11) 中点
        self.assertEqual(fc.ctr_at(999), 0.005)       # 末锚点
        self.assertEqual(fc.ctr_at(2000), 0.005)      # 尾档 clamp

    def test_est_traffic_all_keywords_default_curve(self):
        """步 2 est 含 >30 位词(gamma),>30 排除只作用于情景(步 5)。"""
        import forecast as fc
        p = tmp_file(KWS_DEFAULT_CURVE)
        r = run_script(["--kws", p, "--json"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        expected = 1000 * 0.28 + 500 * 0.09 + 100 * fc.ctr_at(31)
        self.assertAlmostEqual(rep["est_traffic"], round(expected, 2), places=1)
        self.assertEqual(rep["baseline"]["excluded_gt30"], 1)
        self.assertEqual(rep["inputs"]["ctr_curve"]["source"],
                         "内置行业默认 [est](官方建议换自有 GSC 90 天非品牌曲线)")

    def test_custom_curve_replaces_default(self):
        p, c, r = kws_and_curve()
        os.unlink(p); os.unlink(c)
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        # est = 1000×.02 + 500×.10 + 200×.01(35 位 clamp 到末锚点)= 72
        self.assertAlmostEqual(rep["est_traffic"], 72.0, places=1)
        self.assertIn("custom", rep["inputs"]["ctr_curve"]["source"])
        self.assertEqual([a[0] for a in rep["inputs"]["ctr_curve"]["anchors"]], [1, 2, 3, 4, 5])


class ScenarioTests(unittest.TestCase):
    """官方三枚举数学 / >30 排除 / 主情景选择与非法值"""

    def test_three_official_scenarios(self):
        p, c, r = kws_and_curve()
        os.unlink(p); os.unlink(c)
        rep = json.loads(r.stdout)
        by = {s["name"]: s for s in rep["scenarios"]}
        self.assertEqual(set(by), {"pct10", "pos2", "rank3"})
        # 基线(入榜 2 词):1000×.02 + 500×.10 = 70
        self.assertAlmostEqual(rep["baseline"]["traffic"], 70.0, places=1)
        self.assertEqual(rep["baseline"]["eligible_kws"], 2)
        # pct10:k1 4→3.6(.032)=32 + k2 2→1.8(.12)=60 = 92
        self.assertAlmostEqual(by["pct10"]["traffic"], 92.0, places=1)
        self.assertAlmostEqual(by["pct10"]["uplift_traffic"], 22.0, places=1)
        # pos2:k1 4→2(.10)=100 + k2 2→1(.20)=100 = 200
        self.assertAlmostEqual(by["pos2"]["traffic"], 200.0, places=1)
        # rank3:k1 4→3(.05)=50 + k2 已优于 3 保持 2(.10)=50 = 100(不预测退步)
        self.assertAlmostEqual(by["rank3"]["traffic"], 100.0, places=1)
        # k3(35 位)不进任何情景
        for s in by.values():
            self.assertAlmostEqual(s["traffic"], round(s["traffic"], 1), places=1)
        self.assertLess(by["pct10"]["traffic"], by["rank3"]["traffic"])

    def test_primary_scenario_default_and_selection(self):
        p, c, r = kws_and_curve()                       # 不给 --scenario → 默认 pct10
        os.unlink(p); os.unlink(c)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["primary_scenario"], "pct10")
        self.assertAlmostEqual(rep["primary"]["traffic"], 92.0, places=1)
        p, c, r = kws_and_curve(extra=["--scenario", "rank3"])
        os.unlink(p); os.unlink(c)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["primary_scenario"], "rank3")
        self.assertAlmostEqual(rep["primary"]["traffic"], 100.0, places=1)

    def test_invalid_scenario_rejected(self):
        p, c, r = kws_and_curve(extra=["--scenario", "xyz"])
        os.unlink(p); os.unlink(c)
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知 --scenario", r.stderr)


class CalibrationTests(unittest.TestCase):
    """步 3 模型自校准:--actual 算系数 → --save-calibration 持久化 → --load-calibration 套用"""

    def test_save_and_load_calibration(self):
        p, c = tmp_file(KWS_CSV), tmp_file(CURVE_CSV)
        cal = os.path.join(tempfile.gettempdir(), "fc_cal_test.json")
        r1 = run_script(["--kws", p, "--ctr", c, "--actual", "144",
                         "--save-calibration", cal, "--json"])
        self.assertEqual(r1.returncode, 0, r1.stderr)
        rep1 = json.loads(r1.stdout)
        self.assertAlmostEqual(rep1["calibration"]["factor"], 2.0, places=3)  # 144/72
        self.assertEqual(rep1["calibration"]["source"], "actual")
        self.assertAlmostEqual(rep1["baseline"]["traffic"], 140.0, places=1)  # 70×2
        with open(cal, encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved["schema_version"], 1)
        self.assertAlmostEqual(saved["calibration_factor"], 2.0, places=3)
        # 第二次:--load-calibration 自动套用(流量/价值全 ×2)
        r2 = run_script(["--kws", p, "--ctr", c, "--load-calibration", cal, "--json"])
        os.unlink(p); os.unlink(c); os.unlink(cal)
        self.assertEqual(r2.returncode, 0, r2.stderr)
        rep2 = json.loads(r2.stdout)
        self.assertIn("loaded", rep2["calibration"]["source"])
        self.assertAlmostEqual(rep2["calibration"]["factor"], 2.0, places=3)
        by = {s["name"]: s for s in rep2["scenarios"]}
        self.assertAlmostEqual(by["pct10"]["traffic"], 184.0, places=1)   # 92×2
        self.assertAlmostEqual(by["pct10"]["value"], 368.0, places=1)    # ×CVR×AOV
        self.assertAlmostEqual(by["pos2"]["traffic"], 400.0, places=1)

    def test_save_requires_actual(self):
        p, c = tmp_file(KWS_CSV), tmp_file(CURVE_CSV)
        cal = os.path.join(tempfile.gettempdir(), "fc_cal_noscope.json")
        r = run_script(["--kws", p, "--ctr", c, "--save-calibration", cal])
        os.unlink(p); os.unlink(c)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--actual", r.stderr)

    def test_nonpositive_position_rejected(self):
        p = tmp_file("keyword,search_volume,current_position\nbad,100,0\n")
        c = tmp_file(CURVE_CSV)
        r = run_script(["--kws", p, "--ctr", c])
        os.unlink(p); os.unlink(c)
        self.assertEqual(r.returncode, 2)
        self.assertIn("current_position", r.stderr)


class MoneyTests(unittest.TestCase):
    """orders/value/acquisition_value/ROI 数学 + 无 cpc 列 N/A + --lead-value 口径"""

    def test_orders_value_roi_acquisition(self):
        p, c, r = kws_and_curve(extra=["--scenario", "pos2", "--invest", "100"])
        os.unlink(p); os.unlink(c)
        rep = json.loads(r.stdout)
        prim = rep["primary"]
        self.assertAlmostEqual(prim["traffic"], 200.0, places=1)
        self.assertAlmostEqual(prim["orders"], 4.0, places=2)          # 200×0.02
        self.assertAlmostEqual(prim["value"], 400.0, places=1)         # ×AOV 100
        self.assertAlmostEqual(prim["acquisition_value"], 300.0, places=1)  # 100×1+100×2
        self.assertAlmostEqual(prim["roi"], 3.0, places=2)             # (400−100)/100
        # 步 4(当前,全词含 >30):20×1+50×2+2×5=130
        self.assertAlmostEqual(rep["step4_current_acquisition"], 130.0, places=1)
        # 省钱结构:等效付费 300 → 提案投 10% = 30
        sm = rep["proposal"]["save_money"]
        self.assertAlmostEqual(sm["equivalent_paid_cost"], 300.0, places=1)
        self.assertAlmostEqual(sm["propose_invest_10pct"], 30.0, places=1)

    def test_no_cpc_column_marks_na(self):
        p = tmp_file(KWS_NO_CPC)
        c = tmp_file(CURVE_CSV)
        r = run_script(["--kws", p, "--ctr", c, "--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        self.assertIsNone(rep["primary"]["acquisition_value"])
        self.assertIsNone(rep["baseline"]["acquisition_value"])
        self.assertIsNone(rep["step4_current_acquisition"])
        self.assertIsNone(rep["proposal"]["save_money"]["equivalent_paid_cost"])
        rt = run_script(["--kws", p, "--ctr", c])
        os.unlink(p); os.unlink(c)
        self.assertIn("N/A", rt.stdout)

    def test_lead_value_variant(self):
        p, c, r = kws_and_curve(extra=["--scenario", "pos2", "--lead-value", "25"])
        os.unlink(p); os.unlink(c)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["inputs"]["value_label"], "lead_value")
        self.assertEqual(rep["inputs"]["value_per_conversion"], 25.0)
        self.assertAlmostEqual(rep["primary"]["orders"], 4.0, places=2)
        self.assertAlmostEqual(rep["primary"]["value"], 100.0, places=1)  # 4×25


class ProposalAndTemplateTests(unittest.TestCase):
    """商业提案双结构文本渲染 + ROI 五法 + 管理层模板七段式与口径声明"""

    def test_proposal_dual_structure_and_roi_five(self):
        p, c, r = kws_and_curve(extra=["--invest", "50"], as_json=False)
        os.unlink(p); os.unlink(c)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("省钱", out)                 # 省钱结构:Traffic Potential × CPC
        self.assertIn("赚钱", out)                 # 赚钱结构:流量 × CVR × AOV
        self.assertIn("等效付费成本", out)
        self.assertIn("10%", out)                  # 提案只投等效付费成本的 10%
        self.assertIn("ROI 五法", out)
        for m in ("实际转化", "Traffic Value", "相对付费省钱", "付费 CVR", "tag 归因"):
            self.assertIn(m, out)
        self.assertIn("[est]", out)                # 反编造:估算打标
        self.assertIn(">30", out)                  # 排除口径声明
        self.assertIn("calibration", out)          # 自校准指引
        self.assertIn("seoClarity", out)           # 方法论署名

    def test_template_carries_required_sections(self):
        t = os.path.join(BASE, "templates", "monitor", "forecast-report.md")
        with open(t, encoding="utf-8") as f:
            body = f.read()
        for sec in ("The answer", "What could change this conclusion", "Method Notes"):
            self.assertIn(sec, body)               # self_check 七段式契约
        # 漏斗五级 current vs forecast 对照
        for level in ("rank", "visibility", "traffic", "conversions", "revenue"):
            self.assertIn(level, body)
        # 三档情景对照 + 假设与局限声明
        for s in ("pct10", "pos2", "rank3"):
            self.assertIn(s, body)
        self.assertIn("[est]", body)
        self.assertIn(">30", body)
        self.assertIn("省钱结构", body)
        self.assertIn("赚钱结构", body)
        self.assertIn("ROI 五法", body)


if __name__ == "__main__":
    unittest.main(verbosity=1)
