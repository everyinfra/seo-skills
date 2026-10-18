#!/usr/bin/env python3
"""gsc_mining.py 回归测试:2026-10-18 在一个真实站点实测时发现的 bug(修前红、修后绿)。

期望值来源:
- 输入格式:GSC 网页导出的 CTR 是百分比字符串(如 "0.5%"),查询列名是 "Top queries";
  gsc_api.py 规范化输出的 CTR 是小数(见 gsc_api.py --help 的 CSV 契约)。
- 衰退定义:脚本自己的 --help 与文件头写的口径——上期点击 ≥10、本期比上期下降 ≥25%。
  本期完全消失的查询本期点击就是 0(下降 100%),必须报出;本期新出现的查询没有上期,不算衰退、不能崩溃。
- 低 CTR:「期望 − 实际 > 2 个百分点」在脚本内置期望曲线下,只有排名 1–10 有可能成立
  (排名 11–20 的期望值只有 1%,差值永远到不了 2 个百分点),所以规则必须覆盖排名 1–10。
- 品牌词:--brand 正则命中的查询不参与机会挖掘(品牌导航不是内容机会)。
用法: python3 tests/test_gsc_mining_fixes.py(tests/run_tests.py 自动发现本文件)"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import gsc_mining as g  # noqa: E402


def write(tmp, name, text):
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def run(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "gsc_mining.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


class ParseCtrTests(unittest.TestCase):
    def test_percent_below_one_is_not_fifty_percent(self):
        self.assertAlmostEqual(g.parse_ctr("0.5%"), 0.005)       # 修前得 0.5(50%)
        self.assertAlmostEqual(g.parse_ctr("1%"), 0.01)
        self.assertAlmostEqual(g.parse_ctr("0.031"), 0.031)
        self.assertAlmostEqual(g.parse_ctr("12.5%"), 0.125)


class DecayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cur = write(self.tmp, "cur.csv", "Query,Clicks,Impressions,CTR,Position\n"
                                              "steady,40,400,0.1,3\n"
                                              "dropping,10,300,0.033,5\n"
                                              "brand new,25,200,0.125,2\n")
        self.prev = write(self.tmp, "prev.csv", "Query,Clicks,Impressions,CTR,Position\n"
                                                "steady,42,420,0.1,3\n"
                                                "dropping,40,380,0.105,4\n"
                                                "vanished,30,250,0.12,3\n")

    def test_new_query_does_not_crash(self):
        r = run([self.cur, self.prev, "--decay", "--json"])
        self.assertEqual(r.returncode, 0, r.stderr)              # 修前 KeyError: 'brand new'

    def test_vanished_query_is_reported(self):
        r = run([self.cur, self.prev, "--decay", "--json"])
        got = {d["query"]: d for d in json.loads(r.stdout)["declined"]}
        self.assertIn("vanished", got)                           # 修前漏报
        self.assertEqual((got["vanished"]["prev"], got["vanished"]["cur"]), (30, 0))
        self.assertIn("dropping", got)                           # 40→10 = -75%
        self.assertNotIn("steady", got)                          # 42→40 只降 5%
        self.assertNotIn("brand new", got)


class LowCtrTests(unittest.TestCase):
    def test_low_ctr_fires_for_top_ten_positions(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "q.csv", "Query,Clicks,Impressions,CTR,Position\n"
                                    "well ranked no clicks,0,200,0%,3.0\n"   # 期望 11%,实际 0
                                    "page two,0,200,0%,14.0\n")               # 第二页不进低 CTR
            r = run([p, "--json"])
        low = [x["query"] for x in json.loads(r.stdout)["low_ctr"]]
        self.assertEqual(low, ["well ranked no clicks"])

    def test_top_queries_column_from_web_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "Queries.csv", "Top queries,Clicks,Impressions,CTR,Position\n"
                                          "foo api,0,80,0%,8.0\n")
            r = run([p, "--json"])
        sd = json.loads(r.stdout)["striking_distance"]
        self.assertEqual(sd[0]["query"], "foo api")              # 修前查询列读成空串


class BrandTests(unittest.TestCase):
    def test_brand_queries_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "qp.csv", "Query,Page,Clicks,Impressions,CTR,Position\n"
                                     "acme,https://a.com/,50,80,0.6,1.2\n"
                                     "acme,https://a.com/docs,1,30,0.03,3\n"
                                     "acme,https://a.com/pricing,1,25,0.04,3\n"
                                     "widget api,https://a.com/w,0,40,0,6\n"
                                     "widget api,https://a.com/w2,0,30,0,9\n")
            r = run([p, "--mode", "matrix", "--brand", "acme", "--json"])
        groups = [c["query"] for c in json.loads(r.stdout)["cannibalization"]]
        self.assertEqual(groups, ["widget api"])


if __name__ == "__main__":
    unittest.main()
