#!/usr/bin/env python3
"""multimodal_report.py 回归(GSC multimodal 采集 vertical;stdlib unittest,合成 CSV,
零网络,standalone——被 run_tests.py 按 test_*.py 自动发现加载)。口径钉死脚本自身
契约:诚实口径(有 Search Appearance 列→精确;无→按落地页目录特征代理,数字标
[est])/ 候选=高曝光(≥--min-impr)低点击(CTR<--ctr)的图床/产品目录/视频页 /
videos.csv join 找孤儿视频 / video-geo-guide 接线建议按数据形态生成 / --json /
缺列 rc2。走子进程 CLI(纯 CSV 输入,无需打桩)。"""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")

GSC_NO_APPEARANCE = [
    ["Date", "Page", "Clicks", "Impressions"],
    ["2026-10-01", "https://example.com/gallery/rooms", "12", "5000"],
    ["2026-10-01", "https://example.com/p/blue-widget", "30", "8000"],
    ["2026-10-01", "https://example.com/blog/how-to", "500", "20000"],
    ["2026-10-01", "https://example.com/watch/fix-it", "8", "900"],
    ["2026-10-02", "https://example.com/gallery/rooms", "5", "1200"],  # 跨日聚合同页
]


def tmp_csv(rows):
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                    encoding="utf-8", newline="")
    w = csv.writer(f)
    w.writerows(rows)
    f.close()
    return f.name


def run_mm(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "multimodal_report.py"),
                           *args], capture_output=True, text=True, encoding="utf-8",
                          env=env)


class MultimodalReportTests(unittest.TestCase):
    def setUp(self):
        self.gsc = tmp_csv(GSC_NO_APPEARANCE)
        self.addCleanup(os.unlink, self.gsc)

    def test_help_smoke(self):
        r = run_mm(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("multimodal", r.stdout)

    def test_missing_page_column_rc2(self):
        p = tmp_csv([["Date", "Clicks"], ["2026-10-01", "5"]])
        self.addCleanup(os.unlink, p)
        r = run_mm(["--gsc", p])
        self.assertEqual(r.returncode, 2)
        self.assertIn("缺 Page", r.stderr)

    def test_est_basis_directory_classification(self):
        r = run_mm(["--gsc", self.gsc])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = r.stdout
        self.assertIn("落地页目录特征代理", out)
        self.assertIn("[est]", out)                             # 代理口径显式标注
        self.assertIn("图片向页面 [est]: 2 页", out)              # gallery + /p/ 目录页
        self.assertIn("视频向页面 [est]: 1 页", out)              # /watch/

    def test_aggregates_same_page_across_dates(self):
        r = run_mm(["--gsc", self.gsc])
        # gallery/rooms 两天合计:clicks 17 / impressions 6200
        self.assertIn("17", r.stdout.split("-- §2")[0] + r.stdout)  # 总览含 17
        self.assertIn("gallery/rooms", r.stdout)

    def test_candidates_high_impr_low_ctr(self):
        r = run_mm(["--gsc", self.gsc])
        out = r.stdout
        self.assertIn("-- §2 视觉搜索候选页", out)
        self.assertIn("gallery/rooms", out)                     # CTR 17/6200≈0.27% → 候选
        self.assertIn("p/blue-widget", out)                     # 0.375% → 候选
        self.assertIn("watch/fix-it", out)                      # 0.89% → 候选(视频向)
        self.assertNotIn("blog/how-to", out)                    # 未分类页不进候选

    def test_top_limit(self):
        r = run_mm(["--gsc", self.gsc, "--top", "1"])
        out = r.stdout
        self.assertIn("TOP 1", out)
        self.assertIn("p/blue-widget", out)                     # 曝光最大者保留
        self.assertNotIn("gallery/rooms", out.split("-- §3")[0])

    def test_search_appearance_exact_basis(self):
        rows = [["Date", "Page", "Clicks", "Impressions", "Search Appearance"],
                ["2026-10-01", "https://example.com/any/lens-page", "5", "1000",
                 "Images results"],
                ["2026-10-01", "https://example.com/plain", "10", "500", "Web results"]]
        p = tmp_csv(rows)
        self.addCleanup(os.unlink, p)
        r = run_mm(["--gsc", p])
        out = r.stdout
        self.assertIn("Search Appearance 列在场 → 精确", out)
        self.assertIn("图片向页面: 1 页", out)                    # appearance 命中 image
        self.assertIn("any/lens-page", out)
        self.assertNotIn("plain", out)                          # Web results 非视觉行被排除

    def test_video_wiring_advice_present(self):
        r = run_mm(["--gsc", self.gsc])
        out = r.stdout
        self.assertIn("-- §3 video-geo-guide 接线建议", out)
        self.assertIn("VideoObject", out)
        self.assertIn("人工校对字幕", out)
        self.assertIn("multimodal 过滤器", out)                  # [est] 口径的换精确建议

    def test_videos_join_orphan(self):
        vp = tmp_csv([["Url", "Title"],
                      ["https://example.com/watch/fix-it", "Fix It"],
                      ["https://youtube.com/watch?v=abc", "Orphan Video"]])
        self.addCleanup(os.unlink, vp)
        r = run_mm(["--gsc", self.gsc, "--videos", vp])
        out = r.stdout
        self.assertIn("videos.csv 登记 2 条;孤儿 1 条", out)
        self.assertIn("watch page", out)                        # 孤儿→自建 watch page 建议

    def test_json_output_shape(self):
        r = run_mm(["--gsc", self.gsc, "--json"])
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["tool"], "multimodal_report")
        self.assertEqual(data["overview"]["basis"], "directory_est")
        self.assertEqual(data["overview"]["image_pages"], 2)
        self.assertEqual(data["overview"]["video_pages"], 1)
        self.assertTrue(all(c["est"] for c in data["candidates"]))
        self.assertTrue(data["video_wiring"])

    def test_min_impr_threshold(self):
        r = run_mm(["--gsc", self.gsc, "--min-impr", "5000"])
        out = r.stdout
        self.assertIn("p/blue-widget", out)                     # 8000 过阈值
        self.assertNotIn("watch/fix-it", out.split("-- §3")[0])  # 900 被阈值滤掉

    def test_empty_csv_rc2(self):
        p = tmp_csv([["Date", "Page", "Clicks", "Impressions"]])
        self.addCleanup(os.unlink, p)
        r = run_mm(["--gsc", p])
        self.assertEqual(r.returncode, 2)
        self.assertIn("空表", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
