#!/usr/bin/env python3
"""question_align.py 测试(stdlib unittest,合成数据,零网络)。

期望值来源:
- CSV 列名与 CTR 写法:GSC 网页导出用 "Top queries"/"Top pages" 列和 "3.1%" 这样的百分比字符串;
  gsc_api.py 规范化输出用 Query,Page,…,CTR 为小数(见 gsc_api.py --help 的 CSV 契约)。
- 选页门槛、标签、词覆盖率的定义:question_align.py 文件头与 references/content/question-alignment.md
  写定的本套件口径(展示 ≥ 20、点击 0、排名 > 10 标 rank_first、可见查询 < 20% 标 anonymized)。
- 页面解析:真实站点常在 body 里放带 <title> 的内联 SVG(图表无障碍标题),
  Google 用的是 <head> 里的 <title>,所以解析只取 head 的第一个 title。
用法: python3 tests/test_question_align.py(tests/run_tests.py 自动发现本文件)"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import question_align as qa  # noqa: E402


def write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def run(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "question_align.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


PAGE_HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>Foo Data API: profiles and posts · Example</title>
<meta name="description" content="Get Foo profiles and posts as JSON with one API call.">
</head><body>
<svg role="img"><title>Foo search call flow</title></svg>
<main><h1>Foo Data API</h1>
<p>short</p>
<p>The Foo Data API returns public profiles and posts as JSON. Send a username, get the data.</p>
</main></body></html>"""


class CsvParsingTests(unittest.TestCase):
    def test_gsc_ui_export_columns_and_percent_ctr(self):
        # 网页导出:按页筛选后导出的 Queries.csv 只有 "Top queries" 列、没有页面列(页面靠 --page 指定);
        # Pages.csv 的页面列是 "Top pages"。两者不在同一个文件里。
        with tempfile.TemporaryDirectory() as tmp:
            q = write(tmp, "Queries.csv", "Top queries,Clicks,Impressions,CTR,Position\n"
                                          "foo api,0,40,0%,6.5\n"
                                          "foo api pricing,1,200,0.5%,4\n")
            pg = write(tmp, "Pages.csv", "Top pages,Clicks,Impressions,CTR,Position\n"
                                         "https://example.com/foo,1,260,0.38%,4.5\n")
            rows = qa.read_rows(q, need_query=True, page_override="https://example.com/foo")
            prows = qa.read_rows(pg, need_query=False)
        self.assertEqual(rows[0]["query"], "foo api")
        self.assertEqual(rows[0]["page"], "https://example.com/foo")
        self.assertAlmostEqual(rows[1]["ctr"], 0.005)   # "0.5%" 是 0.5%,不是 50%
        self.assertEqual(rows[1]["impressions"], 200)
        self.assertEqual(prows[0]["page"], "https://example.com/foo")
        self.assertAlmostEqual(prows[0]["ctr"], 0.0038)

    def test_api_normalized_decimal_ctr(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "q.csv", "Query,Page,Clicks,Impressions,CTR,Position\n"
                                    "foo api,https://example.com/foo,3,100,0.03,2.0\n")
            rows = qa.read_rows(p, need_query=True)
        self.assertAlmostEqual(rows[0]["ctr"], 0.03)

    def test_missing_query_column_is_input_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = write(tmp, "q.csv", "Page,Clicks,Impressions,CTR,Position\nhttps://example.com/,0,10,0,3\n")
            r = run(["--gsc", p])
        self.assertEqual(r.returncode, 2)
        self.assertIn("查询列", r.stderr)


class CoverageTests(unittest.TestCase):
    def test_latin_word_coverage(self):
        # 查询词 {foo, api, pricing};标题含 foo、api → 2/3
        self.assertEqual(qa.coverage("foo api pricing", "Foo Data API · Example"), 0.67)

    def test_cjk_bigram_coverage(self):
        # 「小红书api」→ {小红, 红书, api};标题全含 → 1.0
        self.assertEqual(qa.coverage("小红书api", "小红书爬虫 API：笔记、评论数据"), 1.0)
        # 「小红书笔记点赞」→ {小红,红书,书笔,笔记,记点,点赞};标题含 小红、红书、笔记 → 0.5
        self.assertEqual(qa.coverage("小红书笔记点赞", "小红书爬虫 API：笔记、评论数据"), 0.5)


class PageParserTests(unittest.TestCase):
    def test_head_title_not_svg_title_and_main_lead(self):
        r = qa.parse_page(PAGE_HTML)
        self.assertEqual(r["title"], "Foo Data API: profiles and posts · Example")
        self.assertEqual(r["h1"], "Foo Data API")
        self.assertTrue(r["lead"].startswith("The Foo Data API returns public profiles"))
        self.assertEqual(r["description"], "Get Foo profiles and posts as JSON with one API call.")


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.q = write(self.tmp, "q.csv",
                       "Query,Page,Clicks,Impressions,CTR,Position\n"
                       "foo api,https://example.com/foo,0,30,0,6.0\n"
                       "brandco foo,https://example.com/foo,0,5,0,1.0\n"
                       "bar api,https://example.com/bar,0,25,0,14.0\n"
                       "baz api,https://example.com/baz,2,60,0.033,3.0\n"
                       "qux api,https://example.com/qux,0,2,0,5.0\n")
        self.p = write(self.tmp, "p.csv",
                       "Page,Clicks,Impressions,CTR,Position\n"
                       "https://example.com/foo,0,40,0,6.0\n"
                       "https://example.com/bar,0,25,0,14.0\n"
                       "https://example.com/baz,2,60,0.033,3.0\n"
                       "https://example.com/qux,0,90,0,4.0\n"
                       "https://example.com/low,0,19,0,4.0\n")
        os.makedirs(os.path.join(self.tmp, "html"))
        write(os.path.join(self.tmp, "html"), qa.html_cache_name("https://example.com/foo"), PAGE_HTML)

    def report(self, *extra):
        r = run(["--gsc", self.q, "--pages", self.p, "--brand", "brandco",
                 "--html-dir", os.path.join(self.tmp, "html"), "--json", *extra])
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_threshold_selection(self):
        rep = self.report()
        pages = {c["page"] for c in rep["candidates"]}
        # baz 有点击、low 展示 19 → 都不选
        self.assertEqual(pages, {"https://example.com/foo", "https://example.com/bar", "https://example.com/qux"})

    def test_flags(self):
        rep = {c["page"]: c for c in self.report()["candidates"]}
        self.assertIn("rank_first", rep["https://example.com/bar"]["flags"])        # 排名 14 > 10
        self.assertIn("anonymized", rep["https://example.com/qux"]["flags"])        # 可见 2/90 < 20%
        foo = rep["https://example.com/foo"]
        self.assertEqual([q["query"] for q in foo["queries"]], ["foo api"])          # 品牌词已排除
        self.assertEqual(foo["queries"][0]["cov_title"], 1.0)
        self.assertIn("aligned", foo["flags"])
        self.assertEqual(foo["anonymized_share"], 0.25)                              # 1 - 30/40
        self.assertIn("no_fetch", rep["https://example.com/bar"]["flags"])           # html-dir 里没有 bar

    def test_missing_terms_and_expected_clicks(self):
        rep = self.report()
        foo = [c for c in rep["candidates"] if c["page"] == "https://example.com/foo"][0]
        self.assertEqual(foo["queries"][0]["missing_terms"]["title"], [])        # foo、api 都在标题里
        # 本站分段 CTR:排名 4–6 段只有 foo(0/40)与 qux 不在此段;baz 在 1–3 段(2/60)
        self.assertEqual(rep["site_ctr_by_position"]["1-3"], round(2 / 60, 4))
        self.assertEqual(foo["expected_clicks"], 0.0)                             # 4–6 段 CTR 为 0
        qux = [c for c in rep["candidates"] if c["page"] == "https://example.com/qux"][0]
        self.assertEqual(qux["expected_clicks"], 0.0)                             # 排名 4 → 4–6 段

    def test_single_page_export_needs_page_flag(self):
        q = write(self.tmp, "single.csv", "Top queries,Clicks,Impressions,CTR,Position\nfoo api,0,30,0%,5\n")
        r = run(["--gsc", q])
        self.assertEqual(r.returncode, 2)
        self.assertIn("--page", r.stderr)
        r2 = run(["--gsc", q, "--page", "https://example.com/foo", "--json"])
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertEqual(json.loads(r2.stdout)["candidates"][0]["page"], "https://example.com/foo")

    def test_without_pages_csv_sums_query_rows(self):
        r = run(["--gsc", self.q, "--json"])
        rep = json.loads(r.stdout)
        self.assertEqual(rep["params"]["page_totals_source"], "sum_of_query_rows")
        foo = [c for c in rep["candidates"] if c["page"] == "https://example.com/foo"][0]
        self.assertEqual(foo["impressions"], 35)   # 30 + 5(没给 --brand,品牌行也算进页面展示)


if __name__ == "__main__":
    unittest.main()
