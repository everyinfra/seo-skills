#!/usr/bin/env python3
"""R5 GEO 节四 bug 修复回归(citation_panel.py;stdlib unittest,合成数据,零网络,
standalone——助手照抄 run_tests.py 顶部,不 import run_tests,被其按 test_*.py
自动发现加载)。钉死 references/overview/pipeline-completeness.md R5「GEO 家族」四项:
  1. wilson_ci 换真 Wilson score interval:
     (p̂+z²/2n ± z√(p̂(1-p̂)/n + z²/4n²))/(1+z²/n),k=0/n 时区间非零宽
     (旧 Wald 近似 CI=p±z·√(p(1-p)/n) 在 0/全命中时宽 0 → 误判 stable);
     已知值锚点(独立推导钉死): k=0,n=3,z=1.96 → 上界≈0.556(真值 0.5615),
     k=3,n=3 → 下界≈0.444(真值 0.4385),k=2,n=3 → [0.208,0.939]。
  2. panel.json / runs/<id>.json 全部原子写(tempfile 同目录 + fsync + os.replace):
     半写不留盘,失败时目标文件保持原内容且无 .tmp 残留。
  3. decay 的 run 日期解析失败不再静默 continue——stderr 打警告并列出被跳过的
     run_id;analyze_decay 结果新增 skipped_runs;render_decay 单列一行。
  4. stable 判定在真 Wilson 下复核: 区间与 0.5 线的重叠逻辑(lo<0.5<hi)不变,
     但改用新 CI——k=0/n=3、k=n=3 由假 stable 翻成 UNSTABLE;k=0,n=20 仍 stable
     (真公式不把已收敛的样本误伤),stats 的判定与独立复算的公式严格一致。"""
import io
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import citation_panel as cp  # noqa: E402  (需先入 SCRIPTS 路径)

Z = cp.Z          # 1.96,与被测代码同一常数;期望值独立按公式手工推导钉死


def run_script(name, args=(), stdin=None):
    env = dict(os.environ, PYTHONIOENCING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def wilson_reference(k, n):
    """测试内独立复算的 Wilson score interval(不抄被测代码的实现路径)。"""
    p, z2 = k / n, Z * Z
    den = 1 + z2 / n
    ctr = (p + z2 / (2 * n)) / den
    half = Z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / den
    return ctr - half, ctr + half


def cell(mentioned=0, cited=0):
    state = "cited_brand" if cited else ("name_only_mention" if mentioned else "brand_absent")
    return {"state": state, "mentioned": mentioned, "cited": cited, "cited_urls": []}


def runs_of(engine, first_date, seq):
    """seq=[(prompt, cell)] × 逐日一份 → run 列表(日期顺推一天)。"""
    d0 = datetime.fromisoformat(first_date)
    out = []
    for i, results in enumerate(seq):
        date = (d0 + timedelta(days=i)).isoformat()
        out.append({"run_id": "%s-%d" % (engine, i), "engine": engine, "date": date,
                    "brand": "Acme", "results": dict(results)})
    return out


def stability_panel():
    """p0×3 次全未提及(k=0,n=3)/ p3×3 次全被引(k=n=3)/ p20×20 次全未提及(k=0,n=20)。
    每个 run 只含一个 prompt,保证各 prompt 的 n 即其 run 数。"""
    runs = (runs_of("chatgpt", "2026-01-01", [[("p0", cell(0, 0))]] * 3)
            + runs_of("chatgpt", "2026-02-01", [[("p3", cell(1, 1))]] * 3)
            + runs_of("chatgpt", "2026-03-01", [[("p20", cell(0, 0))]] * 20))
    return {"brand": "Acme", "domain": "acme.ai", "aliases": [],
            "prompts": ["p0", "p3", "p20"], "engines": ["chatgpt"], "runs": runs}


class WilsonRealFormulaTests(unittest.TestCase):
    """①+④: 真 Wilson 公式数值锚点 / 退化样本非零宽 / 判定与独立复算一致。"""

    def test_known_values_anchored(self):
        """k=0,n=3 上界≈0.556(真值 0.5615);k=3,n=3 下界≈0.444(真值 0.4385);
        k=2,n=3 → [0.208,0.939];k=0,n=10 上界≈0.278(经典教材值)。"""
        p, lo, hi, uns = cp.wilson_ci(0, 3)
        self.assertEqual(p, 0.0)
        self.assertAlmostEqual(hi, 0.561506, places=5)
        self.assertLess(abs(hi - 0.556), 0.01)          # 任务口径已知值 ≈0.556
        self.assertGreater(hi, 0.5)                     # 区间跨 0.5 → 不再假 stable
        self.assertTrue(uns)
        self.assertGreater(hi - lo, 0.5)                # k=0 区间宽度非零(旧 Wald 宽 0)
        p, lo, hi, uns = cp.wilson_ci(3, 3)
        self.assertEqual(p, 1.0)
        self.assertAlmostEqual(lo, 0.438494, places=5)
        self.assertLess(abs(lo - 0.444), 0.01)          # 任务口径已知值 ≈0.444
        self.assertTrue(uns)                            # k=n=3 同样跨 0.5
        self.assertGreater(hi - lo, 0.5)
        p, lo, hi, uns = cp.wilson_ci(2, 3)
        self.assertAlmostEqual(lo, 0.207655, places=5)
        self.assertAlmostEqual(hi, 0.938510, places=5)
        self.assertTrue(uns)
        _, lo10, hi10, uns10 = cp.wilson_ci(0, 10)
        self.assertAlmostEqual(hi10, 0.277540, places=5)
        self.assertFalse(uns10)                         # 上界<0.5 → stable(真稳定)
        self.assertIsNone(cp.wilson_ci(0, 0))           # 空分母 → None 不崩

    def test_matches_reference_and_symmetry(self):
        """与测试内独立复算公式逐点一致;k↔n-k 镜像对称 lo(k,n)=1−hi(n−k,n)。"""
        for k, n in [(0, 1), (1, 4), (7, 21), (10, 20), (5, 5), (0, 20), (3, 3)]:
            _, lo, hi, uns = cp.wilson_ci(k, n)
            rlo, rhi = wilson_reference(k, n)
            self.assertAlmostEqual(lo, max(0.0, rlo), places=12, msg=(k, n))
            self.assertAlmostEqual(hi, min(1.0, rhi), places=12, msg=(k, n))
            self.assertEqual(uns, max(0.0, rlo) < 0.5 < min(1.0, rhi), msg=(k, n))
            jlo, jhi = wilson_reference(n - k, n)
            self.assertAlmostEqual(lo, 1 - jhi, places=9, msg=(k, n))

    def test_stability_verdicts_flip_for_degenerate_cases(self):
        """④复核: stats 稳定性判定 = 真 Wilson 的区间跨 0.5 判定。
        k=0,n=3 与 k=n=3 由假 stable 翻 UNSTABLE;k=0,n=20 仍 stable;
        report 渲染与 stats 一致(区间重叠逻辑不变,换新 CI)。"""
        panel = stability_panel()
        stats = cp.compute_stats(panel)
        for prompt, k, n, want in [("p0", 0, 3, True), ("p3", 3, 3, True),
                                   ("p20", 0, 20, False)]:
            entry = stats["stability"][prompt]
            self.assertEqual(entry[:2], (k, n), prompt)
            self.assertEqual(entry[5], want, prompt)            # unstable 判定
            self.assertEqual(entry[5], cp.wilson_ci(k, n)[3])   # 与公式直算一致
            self.assertEqual(entry[5], wilson_reference(k, n)[0] < 0.5 < wilson_reference(k, n)[1])
        report = cp.render_report(panel, stats)
        lines = {ln.split()[0]: ln for ln in report.splitlines()
                 if ln.strip().startswith(("p0 ", "p3 ", "p20 "))}
        self.assertIn("UNSTABLE", lines["p0"])
        self.assertIn("UNSTABLE", lines["p3"])
        self.assertIn("stable", lines["p20"])
        self.assertNotIn("UNSTABLE", lines["p20"])

    def test_self_test_cli_green(self):
        """--self-test 的自检断言已换成真公式期望值,子进程整跑必须 rc=0。"""
        r = run_script("citation_panel.py", ["--self-test"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("[self-test] PASS", r.stdout)


class AtomicWriteTests(unittest.TestCase):
    """②: panel.json / runs 双写全部走 tempfile+os.replace,半写不留盘。"""

    def test_failed_dump_leaves_original_intact_and_no_tmp(self):
        tmp = tempfile.mkdtemp(prefix="fix_panel_atomic_")
        path = os.path.join(tmp, "panel.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"brand": "ORIGINAL"}')
        with self.assertRaises(TypeError):        # set 不可 JSON 序列化 → 中途抛
            cp.save_panel(path, {"brand": "X", "runs": [set()]})
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), '{"brand": "ORIGINAL"}')   # 目标文件未动
        self.assertEqual([p for p in os.listdir(tmp) if p.endswith(".tmp")], [])

    def test_record_and_score_replace_atomically(self):
        """init/record/score 的 panel.json 与 runs/<id>.json 落盘均经过 os.replace,
        成功后无 .tmp 残留且内容可解析(record 与 score 双写都覆盖)。"""
        import argparse
        tmp = tempfile.mkdtemp(prefix="fix_panel_cli_")
        panel_path = os.path.join(tmp, "panel.json")
        prompts = os.path.join(tmp, "prompts.csv")
        with open(prompts, "w", encoding="utf-8") as f:
            f.write("prompt\np1\n")
        calls = []
        orig_replace = os.replace

        def spy(src, dst):
            calls.append(dst)
            return orig_replace(src, dst)
        os.replace = spy
        try:
            self.assertEqual(cp.cmd_init(cp.build_parser().parse_args(
                ["init", "--brand", "Acme", "--domain", "acme.ai",
                 "--prompts", prompts, "--panel", panel_path])), 0)
            run_csv = os.path.join(tmp, "run.csv")
            with open(run_csv, "w", encoding="utf-8") as f:
                f.write("prompt,mentioned,cited,cited_urls\np1,1,0,\n")
            self.assertEqual(cp.cmd_record(cp.build_parser().parse_args(
                ["record", "--engine", "chatgpt", "--file", run_csv,
                 "--panel", panel_path, "--date", "2026-10-01"])), 0)
            scores = os.path.join(tmp, "scores.json")
            with open(scores, "w", encoding="utf-8") as f:
                json.dump({"p1": {"geo_score": 45, "presence": "name_only_mention",
                                  "recommendation": "honorable_mention"}}, f)
            self.assertEqual(cp.cmd_score(cp.build_parser().parse_args(
                ["score", "--last", "--scores", scores, "--panel", panel_path])), 0)
        finally:
            os.replace = orig_replace
        replaced = [os.path.basename(d) for d in calls]
        self.assertIn("panel.json", replaced)                    # init/record/score 均原子
        run_files = sorted(p for p in os.listdir(os.path.join(tmp, "runs")))
        self.assertEqual(len(run_files), 1)
        self.assertIn(run_files[0], replaced)                    # run 文件走 replace
        self.assertEqual([p for p in os.listdir(tmp) if p.endswith(".tmp")], [])
        with open(panel_path, encoding="utf-8") as f:
            self.assertEqual(json.load(f)["runs"][0]["results"]["p1"]["geo"]["geo_score"], 45)
        with open(os.path.join(tmp, "runs", run_files[0]), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["results"]["p1"]["geo"]["presence"],
                             "name_only_mention")                # run 双写同步


class DecayBadDateWarningTests(unittest.TestCase):
    """③: 日期解析失败的 run 不再静默 continue——警告 + 列出 run_id。"""

    def _panel(self):
        good = [{"run_id": "chatgpt-good-1", "engine": "chatgpt", "date": "2026-01-01",
                 "brand": "Acme", "results": {"p1": cell(1, 1)}},
                {"run_id": "chatgpt-good-2", "engine": "chatgpt", "date": "2026-02-15",
                 "brand": "Acme", "results": {"p1": cell(0, 0)}}]
        bad = [{"run_id": "chatgpt-BAD-date", "engine": "chatgpt", "date": "not-a-date",
                "brand": "Acme", "results": {"p2": cell(1, 1)}}]
        return {"brand": "Acme", "domain": "acme.ai", "aliases": [],
                "prompts": ["p1", "p2"], "engines": ["chatgpt"],
                "runs": good[:1] + bad + good[1:]}

    def test_collect_series_reports_skipped(self):
        skipped = []
        series = cp.collect_cell_series(self._panel(), skipped=skipped)
        self.assertEqual(skipped, [{"run_id": "chatgpt-BAD-date", "date": "not-a-date"}])
        self.assertIn(("p1", "chatgpt"), series)          # 有效 run 照常入序列
        self.assertNotIn(("p2", "chatgpt"), series)       # 坏日期 run 的 cell 不在
        self.assertEqual(cp.collect_cell_series(self._panel()),
                         series)                          # 不传 skipped 向后兼容

    def test_analyze_decay_warns_and_lists_run_ids(self):
        err = io.StringIO()
        with redirect_stderr(err):
            result = cp.analyze_decay(self._panel(), metric="cited")
        self.assertEqual([s["run_id"] for s in result["skipped_runs"]], ["chatgpt-BAD-date"])
        self.assertIn("[!]", err.getvalue())
        self.assertIn("chatgpt-BAD-date", err.getvalue())
        out = cp.render_decay(self._panel(), result)
        self.assertIn("chatgpt-BAD-date", out)            # markdown 输出也单列
        # 全部日期有效 → 不产警告、skipped_runs 为空(不误伤正常面板)
        panel = {"brand": "Acme", "prompts": ["p1"], "engines": ["chatgpt"],
                 "runs": runs_of("chatgpt", "2026-01-01", [[("p1", cell(1, 1))]] * 3)}
        err2 = io.StringIO()
        with redirect_stderr(err2):
            result2 = cp.analyze_decay(panel)
        self.assertEqual(result2["skipped_runs"], [])
        self.assertEqual(err2.getvalue(), "")

    def test_decay_cli_stderr_lists_run_id(self):
        tmp = tempfile.mkdtemp(prefix="fix_panel_decay_")
        panel_path = os.path.join(tmp, "panel.json")
        with open(panel_path, "w", encoding="utf-8") as f:
            json.dump(self._panel(), f, ensure_ascii=False)
        r = run_script("citation_panel.py", ["decay", "--panel", panel_path])
        self.assertEqual(r.returncode, 0)
        self.assertIn("[!]", r.stderr)
        self.assertIn("chatgpt-BAD-date", r.stderr)
        self.assertIn("date 解析失败", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
