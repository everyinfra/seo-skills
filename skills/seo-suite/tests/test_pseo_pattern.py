#!/usr/bin/env python3
"""pseo_pattern_mining.py 回归(stdlib unittest,合成 GSC CSV+URL 清单,零网络,
standalone——不 import run_tests,被其 test_*.py 自动发现加载)。口径钉死脚本
自身契约(规格=pipeline-completeness.md R3-1 + programmatic-seo-gates.md §八
模式评分权重 30/25/20/15/10 + programmatic-seo-playbook.md §一查询正则表与收口):

- 模式聚类:16 条英文查询各落声明模式;特异在前(best-for 先于 best/for-y、
  how-to-with/integration 先于 how-to/换算、beginners 先于 for-y)
- 权重累加:五维 30/25/20/15/10 相加封顶 100,合成输入钉死逐维精确值;
  demand/gap/data 三函数逐档边界钉死
- 三态门槛:score≥50 且变体≥3→GO(恰 50 边界含);变体<3→白空间(高分也压不住,
  5-10 页手工验证);其余 WATCH
- CJK:中文基础表(XX和XX哪个好/替代品/最好的XX/多少钱/是什么/值得买吗/集成/
  入门/附近/怎么用/模板)+ 容错(全角ＶＳ/versus/vs./全角空格→同一模式,实体归一)
- 覆盖度:--urls 路径正则首匹配;/blog/ 编辑页排除(gates §八);best_for/for_y
  同 /for- 页族并计;/alternative-to-x 无尾斜杠可匹配;gap 三态随覆盖变化
- 列头变体:BOM+旧版 Top queries、中文列头+Tab 分隔、缺 Impressions 列可跑
- addressable=变体数×有曝光变体均量(全有曝光=总曝光;零曝光行抬高均量)
- 输入校验:缺 query 列/文件不存在/file:// sitemap → 退出码 2(file:// 拒绝
  发生在任何网络之前,零网络可测);缺 --gsc → argparse 退出码 2
- sitemap:parse_locs 单层 urlset/index 解析;fetch_sitemap index 递归一层
  (DNS+opener 双打桩,test_ssrf_guard 同款,零网络)
- JSON 契约:顶层 tool/weights/meta/patterns,行含全字段,按 score 降序

用法: python3 tests/test_pseo_pattern.py(tests/run_tests.py 自动发现本文件)"""
import contextlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import pseo_pattern_mining as ppm  # noqa: E402 (需先入 SCRIPTS 路径)

PUBLIC_IP = "93.184.216.34"  # example.com 公网 IP(打桩用,零网络)


def run_cli(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "pseo_pattern_mining.py"), *args],
        capture_output=True, text=True, encoding="utf-8", env=env)


def write(content, suffix=".csv"):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def gsc(rows, header="Query,Clicks,Impressions,CTR,Position"):
    """合成 GSC 导出:rows=[(query, clicks, impressions)] → CSV 文本。"""
    return "\n".join([header] + ["%s,%d,%d" % r for r in rows]) + "\n"


def run_json(gsc_text, urls_text=None):
    """写临时输入 → CLI --json → 解析字典(退出码非 0 直接断言失败带 stderr)。"""
    args = ["--gsc", write(gsc_text), "--json"]
    if urls_text is not None:
        args += ["--urls", write(urls_text, ".txt")]
    r = run_cli(args)
    assert r.returncode == 0, "exit=%s stderr=%s" % (r.returncode, r.stderr)
    return json.loads(r.stdout)


def by_id(doc):
    return {p["id"]: p for p in doc["patterns"]}


# ---------------------------------------------------------------- 打桩件(零网络)
@contextlib.contextmanager
def stub_dns(ip_of=None):
    resolve = (lambda host: host) if ip_of is None else ip_of

    def fake_getaddrinfo(host, *a, **k):
        return [(socket.AF_INET, 1, 6, "", (resolve(host), 0))]

    orig = socket.getaddrinfo
    socket.getaddrinfo = fake_getaddrinfo
    try:
        yield
    finally:
        socket.getaddrinfo = orig


class _FakeResp:
    status = 200

    def __init__(self, body):
        self._b = body.encode() if isinstance(body, str) else body

    def read(self, n=-1):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeOpener:
    def __init__(self, bodies):
        self.bodies = bodies
        self.seen = []

    def open(self, req, timeout=None):
        self.seen.append(req.full_url)
        return _FakeResp(self.bodies[req.full_url])


# ---------------------------------------------------------------- CLI 与帮助
class CliTests(unittest.TestCase):
    def test_help_lists_flags_and_spec(self):
        r = run_cli(["--help"])
        self.assertEqual(r.returncode, 0)
        for flag in ("--gsc", "--sitemap", "--urls", "--json"):
            self.assertIn(flag, r.stdout)
        self.assertIn("gates", r.stdout)  # 规格出处随帮助可见

    def test_missing_gsc_flag_exits_2(self):
        r = run_cli([])
        self.assertEqual(r.returncode, 2)
        self.assertIn("--gsc", r.stderr)


# ---------------------------------------------------------------- 模式聚类
class ClusteringTests(unittest.TestCase):
    QUERIES = [("notion vs obsidian", 10, 200), ("slack vs teams", 20, 300),
               ("trello alternative", 3, 120), ("alternative to jira", 2, 80),
               ("best crm for dentists", 1, 90),
               ("how to connect slack to gmail", 0, 60),
               ("slack integrations", 1, 70), ("is notion worth it", 4, 70),
               ("coffee shops near me", 8, 300), ("python for beginners", 2, 40),
               ("slack pricing", 6, 250), ("what is schema markup", 1, 30),
               ("100 usd to eur", 0, 50), ("crm for startups", 1, 44),
               ("resume templates", 2, 66), ("hotels in paris", 5, 120)]

    def test_each_query_lands_in_declared_pattern(self):
        d = run_json(gsc(self.QUERIES))
        got = {pid: p["variants"] for pid, p in by_id(d).items()}
        self.assertEqual(got, {"vs": 2, "alternative": 2, "best_for": 1,
                               "howto_with": 1, "integration": 1, "worth": 1,
                               "near_me": 1, "beginners": 1, "pricing": 1,
                               "glossary": 1, "conversion": 1, "for_y": 1,
                               "template": 1, "local_in": 1})
        self.assertEqual(d["meta"]["matched"], 16)
        self.assertEqual(d["meta"]["unmatched_count"], 0)

    def test_specific_beats_generic(self):
        d = run_json(gsc([("best crm for dentists", 1, 90),
                          ("python for beginners", 2, 40),
                          ("how to connect slack to gmail", 0, 60),
                          ("crm for startups", 1, 44),
                          ("100 usd to eur", 0, 50),
                          ("best project management software", 3, 80)]))
        got = by_id(d)
        self.assertEqual(got["best_for"]["variants"], 1)   # best-for 不落 best/for-y
        self.assertEqual(got["best"]["variants"], 1)       # 纯 best 清单
        self.assertEqual(got["for_y"]["variants"], 1)      # for-startups
        self.assertNotIn("howto", got)                     # connect-to 归 how-to-with
        self.assertEqual(got["howto_with"]["variants"], 1)
        self.assertEqual(got["conversion"]["variants"], 1) # usd-to-eur 不被 how-to 吃掉


# ---------------------------------------------------------------- 打分权重
class ScoringTests(unittest.TestCase):
    def test_weight_accumulation_exact(self):
        # vs ×3 每条 200 曝光、零覆盖:demand 24(A=600≥500)+ intent 25 + 模板 20
        # + data 15(5 去重实体)+ gap 10 = 94
        d = run_json(gsc([("notion vs obsidian", 10, 200),
                          ("evernote vs notion", 5, 200),
                          ("slack vs teams", 20, 200)]))
        self.assertEqual(d["weights"],
                         {"demand": 30, "intent": 25, "feasibility": 20, "data": 15, "gap": 10})
        self.assertEqual(sum(d["weights"].values()), 100)   # 五维累加封顶 100
        p = by_id(d)["vs"]
        self.assertEqual(p["dimensions"],
                         {"demand": 24, "intent": 25, "feasibility": 20, "data": 15, "gap": 10})
        self.assertEqual(p["score"], sum(p["dimensions"].values()))
        self.assertEqual(p["score"], 94)
        self.assertEqual(p["entities_distinct"], 5)

    def test_demand_tier_boundaries(self):
        self.assertEqual(ppm.demand_score(1000), 30)
        self.assertEqual(ppm.demand_score(999), 24)
        self.assertEqual(ppm.demand_score(500), 24)
        self.assertEqual(ppm.demand_score(499), 19)
        self.assertEqual(ppm.demand_score(80), 11)
        self.assertEqual(ppm.demand_score(10), 3)
        self.assertEqual(ppm.demand_score(9), 1)

    def test_gap_tier_boundaries(self):
        self.assertEqual(ppm.gap_score(0, 3), 10)   # 零覆盖=缺口全开
        self.assertEqual(ppm.gap_score(1, 3), 7)
        self.assertEqual(ppm.gap_score(2, 3), 7)
        self.assertEqual(ppm.gap_score(3, 5), 5)    # 覆盖未盖满变体
        self.assertEqual(ppm.gap_score(5, 5), 2)    # 盖满=已做,缺口最小

    def test_data_tier_boundaries(self):
        self.assertEqual(ppm.data_score(5), 15)
        self.assertEqual(ppm.data_score(4), 12)
        self.assertEqual(ppm.data_score(3), 12)
        self.assertEqual(ppm.data_score(2), 9)
        self.assertEqual(ppm.data_score(1), 6)
        self.assertEqual(ppm.data_score(0), 0)

    def test_patterns_sorted_by_score_desc(self):
        d = run_json(gsc(ClusteringTests.QUERIES))
        scores = [p["score"] for p in d["patterns"]]
        self.assertEqual(scores, sorted(scores, reverse=True))


# ---------------------------------------------------------------- 三态门槛
class VerdictTests(unittest.TestCase):
    def test_go_at_score_boundary_50(self):
        # glossary:intent 5+模板 12+data 12(3 实体)+gap 10=39,demand 11(A=90∈[80,150))
        # → 恰 50,≥50 且 3 变体 → GO(边界含)
        d = run_json(gsc([("what is seo", 1, 30), ("what is schema", 1, 30),
                          ("what is serp", 1, 30)]))
        p = d["patterns"][0]
        self.assertEqual((p["id"], p["score"], p["verdict"]), ("glossary", 50, "GO"))

    def test_watch_when_score_below_50(self):
        # 同型但每条 20 曝光(A=60→demand 7)→ 46 → WATCH
        d = run_json(gsc([("what is seo", 1, 20), ("what is schema", 1, 20),
                          ("what is serp", 1, 20)]))
        p = d["patterns"][0]
        self.assertEqual((p["id"], p["score"], p["verdict"]), ("glossary", 46, "WATCH"))

    def test_white_space_beats_high_score(self):
        # vs 仅 2 变体:分数 97 仍判白空间(playbook §一:<3 真实变体=需求未验证)
        d = run_json(gsc([("notion vs obsidian", 10, 500), ("slack vs teams", 20, 500)]))
        p = d["patterns"][0]
        self.assertEqual(p["verdict"], "WHITE_SPACE")
        self.assertGreaterEqual(p["score"], 50)

    def test_markdown_table_and_gate_rule(self):
        doc = run_cli(["--gsc", write(gsc([
            ("notion vs obsidian", 10, 200), ("slack vs teams", 20, 200),
            ("evernote vs notion", 5, 200), ("slack vs trello", 1, 200),
            ("what is seo", 1, 20), ("what is schema", 1, 20), ("what is serp", 1, 20),
            ("jira pricing", 1, 50)]))])
        self.assertEqual(doc.returncode, 0, doc.stderr)
        self.assertIn("| 模式 | 变体 | 曝光 | 覆盖URL | addressable | score | 判定 |", doc.stdout)
        self.assertIn("GO", doc.stdout)
        self.assertIn("WATCH", doc.stdout)
        self.assertIn("白空间", doc.stdout)
        self.assertIn("5-10 页手工验证", doc.stdout)
        self.assertIn("score≥50", doc.stdout)


# ---------------------------------------------------------------- CJK 容错
class CjkTests(unittest.TestCase):
    def test_zh_pattern_base_table(self):
        rows = [("notion和obsidian哪个好", 2, 110), ("jira替代品", 3, 140),
                ("最好的笔记软件", 5, 220), ("notion多少钱", 7, 180),
                ("什么是seo", 1, 60), ("seo是什么", 1, 50),
                ("notion值得买吗", 2, 70), ("slack集成", 1, 40),
                ("python入门", 1, 30), ("咖啡店附近", 1, 45),
                ("excel怎么用", 2, 55), ("简历模板", 1, 65)]
        got = {pid: p["variants"] for pid, p in by_id(run_json(gsc(rows))).items()}
        self.assertEqual(got, {"vs": 1, "alternative": 1, "best": 1, "pricing": 1,
                               "glossary": 2, "worth": 1, "integration": 1,
                               "beginners": 1, "near_me": 1, "howto": 1, "template": 1})

    def test_zh_en_merge_into_same_pattern(self):
        # 中文变体与英文模式同批聚类:vs 计 2 变体,语种各计 1
        d = run_json(gsc([("notion vs obsidian", 1, 100), ("slack和teams哪个好", 1, 100)]))
        p = by_id(d)["vs"]
        self.assertEqual(p["variants"], 2)
        self.assertEqual(d["meta"]["langs"], {"en": 1, "zh": 1})

    def test_fullwidth_and_versus_tolerance(self):
        # 全角ＶＳ/versus/vs. 三种写法 → 同落 vs;全角与 vs. 写法的实体归一为 notion×2
        d = run_json(gsc([("ＮＯＴＩＯＮ ＶＳ ＯＢＳＩＤＩＡＮ", 1, 100),
                          ("a versus b", 1, 100), ("notion vs. obsidian", 1, 100)]))
        p = by_id(d)["vs"]
        self.assertEqual(p["variants"], 3)
        self.assertEqual(dict(p["axes"][0]["values"]).get("notion"), 2)


# ---------------------------------------------------------------- 覆盖度
class CoverageTests(unittest.TestCase):
    URLS = ("https://example.com/vs/notion-vs-obsidian\n"
            "https://example.com/compare/evernote-notion\n"
            "/alternatives/to-trello\n"
            "/alternative-to-jira\n"      # 无尾斜杠的 alternative-to slug
            "/notion-pricing\n/pricing\n"
            "/glossary/schema-markup\n/what-is-seo\n"
            "/for-dentists\n"             # best_for/for_y 同 /for- 页族并计
            "/templates/invoice\n/usd-to-eur\n"
            "/blog/notion-vs-obsidian\n"  # gates §八:blog=编辑内容,排除
            "/\n")
    MULTI = gsc([("notion vs obsidian", 1, 200), ("evernote vs notion", 1, 200),
                 ("slack vs teams", 1, 200),              # vs ×3
                 ("trello alternative", 1, 100),           # alternative
                 ("slack pricing", 1, 90),                 # pricing
                 ("what is seo", 1, 30),                   # glossary
                 ("best crm for dentists", 1, 60),         # best_for
                 ("crm for startups", 1, 40),              # for_y
                 ("resume templates", 1, 50),              # template
                 ("100 usd to eur", 1, 70)])               # conversion

    def test_coverage_counts_and_editorial_exclusion(self):
        d = run_json(self.MULTI, urls_text=self.URLS)
        got = by_id(d)
        self.assertEqual(got["vs"]["coverage_urls"], 2)
        self.assertEqual(got["pricing"]["coverage_urls"], 2)
        self.assertEqual(got["glossary"]["coverage_urls"], 2)
        self.assertEqual(got["best_for"]["coverage_urls"], 1)
        self.assertEqual(got["for_y"]["coverage_urls"], 1)  # 同页族并计
        self.assertEqual(got["template"]["coverage_urls"], 1)
        self.assertEqual(got["conversion"]["coverage_urls"], 1)
        self.assertEqual(d["meta"]["editorial"], 1)         # /blog/ 排除
        self.assertEqual(d["meta"]["url_count"], 13)        # "/" 根路径也计入清单
        self.assertEqual(got["vs"]["covered_samples"],
                         ["/vs/notion-vs-obsidian", "/compare/evernote-notion"])

    def test_alternative_slug_without_trailing_slash(self):
        d = run_json(gsc([("trello alternative", 1, 100), ("jira alternative", 1, 100),
                          ("asana alternative", 1, 100)]), urls_text=self.URLS)
        p = by_id(d)["alternative"]
        self.assertEqual(p["coverage_urls"], 2)  # /alternatives/to-trello + /alternative-to-jira

    def test_gap_moves_with_coverage(self):
        urls = "/alternatives/to-trello\n/alternative-to-jira\n/alternatives/asana\n"
        rows4 = [("trello alternative", 1, 50), ("jira alternative", 1, 50),
                 ("asana alternative", 1, 50), ("slack alternative", 1, 50)]
        d = run_json(gsc(rows4), urls_text=urls)
        p = by_id(d)["alternative"]
        self.assertEqual((p["variants"], p["coverage_urls"]), (4, 3))
        self.assertEqual(p["dimensions"]["gap"], 5)   # 3<4 未盖满
        d2 = run_json(gsc(rows4[:3]), urls_text=urls)
        p2 = by_id(d2)["alternative"]
        self.assertEqual(p2["dimensions"]["gap"], 2)  # 3>=3 盖满

    def test_full_coverage_lowers_score_below_uncovered(self):
        urls = "/vs/notion-vs-obsidian\n/vs/slack-vs-teams\n/vs/evernote-vs-notion\n"
        rows = [("notion vs obsidian", 1, 200), ("slack vs teams", 1, 200),
                ("evernote vs notion", 1, 200)]
        self.assertEqual(by_id(run_json(gsc(rows)))["vs"]["score"], 94)       # gap 10
        self.assertEqual(by_id(run_json(gsc(rows), urls))["vs"]["score"], 86)  # gap 2


# ---------------------------------------------------------------- 列头容错
class HeaderToleranceTests(unittest.TestCase):
    VS3_ROWS = [("notion vs obsidian", 10, 200), ("slack vs teams", 20, 300),
                ("evernote vs notion", 5, 150)]

    def test_top_queries_header_with_bom_and_minimal_columns(self):
        text = "﻿Top queries,Impressions\nnotion vs obsidian,200\n" \
               "slack vs teams,300\nevernote vs notion,150\n"
        d = run_json(text)
        p = by_id(d)["vs"]
        self.assertEqual((p["variants"], p["impressions"]), (3, 650))

    def test_chinese_headers_tab_separated(self):
        text = "热门查询\t点击\t展示次数\n" + "\n".join(
            "%s\t%d\t%d" % r for r in self.VS3_ROWS) + "\n"
        d = run_json(text)
        p = by_id(d)["vs"]
        self.assertEqual((p["variants"], p["impressions"]), (3, 650))

    def test_missing_query_column_exits_2(self):
        r = run_cli(["--gsc", write("Clicks,Impressions\nfoo,1\n")])
        self.assertEqual(r.returncode, 2)
        self.assertIn("query", r.stderr)

    def test_missing_file_exits_2(self):
        r = run_cli(["--gsc", os.path.join(tempfile.gettempdir(), "pseo_no_such_file.csv")])
        self.assertEqual(r.returncode, 2)


# ---------------------------------------------------------------- addressable 口径
class AddressableTests(unittest.TestCase):
    def test_addressable_equals_impressions_when_all_have_data(self):
        d = run_json(gsc([("notion vs obsidian", 10, 200), ("slack vs teams", 20, 300),
                          ("evernote vs notion", 5, 150)]))
        p = by_id(d)["vs"]
        self.assertEqual((p["variants"], p["impressions"], p["addressable"]), (3, 650, 650))

    def test_addressable_formula_with_zero_impression_row(self):
        # 变体 3(含 1 条零曝光)/总曝光 350/均量=350÷2(仅计有曝光变体)=175
        # → addressable = 3×175 = 525
        d = run_json(gsc([("notion vs obsidian", 1, 200), ("slack vs teams", 0, 0),
                          ("evernote vs notion", 1, 150)]))
        p = by_id(d)["vs"]
        self.assertEqual((p["variants"], p["impressions"], p["addressable"]), (3, 350, 525))


# ---------------------------------------------------------------- sitemap(零网络)
class SitemapTests(unittest.TestCase):
    def setUp(self):
        ppm._ssrf_cache.clear()

    def tearDown(self):
        ppm._ssrf_cache.clear()

    def test_rejects_file_scheme_before_any_network(self):
        r = run_cli(["--gsc", write(gsc([("notion vs obsidian", 1, 100)])),
                     "--sitemap", "file:///etc/passwd"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("http(s)", r.stdout + r.stderr)

    def test_parse_locs_urlset_and_sitemapindex(self):
        ns = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
        urlset = ('<urlset %s><url><loc>https://e.com/vs/a-vs-b</loc></url>'
                  '<url><loc>https://e.com/pricing</loc></url></urlset>' % ns)
        self.assertEqual(ppm.parse_locs(urlset),
                         ["https://e.com/vs/a-vs-b", "https://e.com/pricing"])
        idx = ('<sitemapindex %s><sitemap><loc>https://e.com/sitemap-1.xml</loc></sitemap>'
               '<sitemap><loc>https://e.com/sitemap-2.xml</loc></sitemap></sitemapindex>' % ns)
        self.assertEqual(ppm.parse_locs(idx),
                         ["https://e.com/sitemap-1.xml", "https://e.com/sitemap-2.xml"])
        self.assertEqual(ppm.parse_locs("<not-sitemap/>"), [])

    def test_fetch_sitemap_recurses_one_level(self):
        ns = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'

        def child(a, b):
            return ('<urlset %s><url><loc>https://example.com%s</loc></url>'
                    '<url><loc>https://example.com%s</loc></url></urlset>' % (ns, a, b))

        bodies = {
            "https://example.com/sitemap.xml":
                '<sitemapindex %s><sitemap><loc>https://example.com/sitemap-1.xml</loc>'
                '</sitemap><sitemap><loc>https://example.com/sitemap-2.xml</loc></sitemap>'
                '</sitemapindex>' % ns,
            "https://example.com/sitemap-1.xml": child("/vs/a-vs-b", "/vs/b-vs-c"),
            "https://example.com/sitemap-2.xml": child("/pricing", "/glossary/seo"),
        }
        opener = _FakeOpener(bodies)
        with stub_dns(ip_of=lambda _h: PUBLIC_IP):
            with mock.patch.object(ppm, "_opener", opener):
                locs = ppm.fetch_sitemap("https://example.com/sitemap.xml")
        self.assertEqual(len(locs), 4)
        self.assertEqual(set(locs),
                         {"https://example.com/vs/a-vs-b", "https://example.com/vs/b-vs-c",
                          "https://example.com/pricing", "https://example.com/glossary/seo"})
        self.assertEqual(len(opener.seen), 3)  # index + 2 子图,各抓一次


# ---------------------------------------------------------------- JSON 契约
class JsonContractTests(unittest.TestCase):
    def test_top_level_and_row_shape(self):
        d = run_json(gsc([("notion vs obsidian", 1, 200), ("slack vs teams", 1, 300),
                          ("unmatchable giberish query", 1, 10)]))
        self.assertEqual(d["tool"], "pseo_pattern_mining")
        self.assertEqual(set(d), {"tool", "weights", "meta", "patterns"})
        self.assertEqual((d["meta"]["total"], d["meta"]["matched"],
                          d["meta"]["unmatched_count"]), (3, 2, 1))
        p = d["patterns"][0]
        for key in ("id", "label", "variants", "impressions", "coverage_urls",
                    "addressable", "entities_distinct", "score", "dimensions",
                    "verdict", "axes", "top_queries", "covered_samples"):
            self.assertIn(key, p)
        self.assertEqual([q["query"] for q in p["top_queries"]][0], "slack vs teams")


if __name__ == "__main__":
    unittest.main(verbosity=1)
