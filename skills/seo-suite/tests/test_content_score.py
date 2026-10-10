#!/usr/bin/env python3
"""content_score.py 回归(stdlib unittest,合成数据,零网络,standalone——
助手照抄 run_tests.py 顶部,不 import run_tests,被其 test_*.py 自动发现加载)。
口径钉死 references/research/borrow-specs.md C1:
MarketMuse Σmin(提及,2)/(50×2)=满分 100【官方】/Clearscope importance=ceil(命中竞品数/
竞品总数×10) 8+ 强制计入/竞品<3 不同来源拒绝评分【Surfer 官方】/总分=0.5×SEO+0.5×AI[推断]/
分档 0-33/34-66/67+【官方】/意图系数 0.296|0.271|0.225|0.19【官方,不改分值】/前三查【官方】/
关键词密度不计分【两家官方明确否定】。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)


def run_script(args=(), stdin=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "content_score.py"), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def tmp_file(content, suffix=".md"):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


# ---- 中文合成语料: 3 个不同来源竞品 + 1 份有缺口的草稿(术语表/结构可复现) ----
KW = "项目管理软件"
C1 = ("# 项目管理软件选型指南\n\n"
      "项目管理软件是团队协作的核心工具。简而言之,选型先看甘特图与任务分配。\n"
      "2026 年主流工具超过 40 款,资源负载与工时统计决定付费价值。\n\n"
      "## 甘特图与看板\n\n甘特图可视化里程碑,看板适合敏捷流转。\n\n"
      "## 资源负载与工时统计\n\n资源负载过高要重排任务,工时统计支撑成本核算。\n\n"
      "![仪表盘](dash.png)\n\n[选型指南](/guide) 与 [定价说明](/pricing)。\n\n"
      "<script type=\"application/ld+json\">{\"@type\":\"Article\"}</script>\n")
C2 = ("项目管理软件对比盘点:任务分配、甘特图与时间跟踪是三大主线。总之,没有最好只有最合适。\n"
      "资源负载监控与工时统计报表是付费理由;看板与里程碑提醒降低延期风险。2026 年均价每席位 15 元。\n")
C3 = ("如何挑选项目管理软件:先看任务分配与看板,再看甘特图与时间跟踪。答案是先明确团队规模。\n"
      "工时统计与里程碑管理是高频需求,资源负载视图与时间跟踪精度决定成本核算质量。\n")
DRAFT_MISSING = ("# 协作工具漫谈\n\n"
                 "协作工具有很多门道,值得慢慢展开讨论,这里先聊一些背景与想法。\n"
                 "下文再谈预算、会议与文档的一些观察,供参考。\n")


def _files():
    return (tmp_file(C1), tmp_file(C2), tmp_file(C3), tmp_file(DRAFT_MISSING))


class WeightAndCoefficientTests(unittest.TestCase):
    """权重守恒断言(改权重必炸)与官方意图系数钉死"""

    def test_weights_sum(self):
        import content_score as cs
        self.assertAlmostEqual(sum(cs.SEO_WEIGHTS.values()), 0.90)   # true_density 剔除后 0.90
        self.assertAlmostEqual(sum(cs.AI_WEIGHTS.values()), 1.00)

    def test_intent_coefficients_official(self):
        import content_score as cs
        self.assertEqual(cs.INTENT_COEF, {"consequence": 0.296, "definition": 0.271,
                                          "comparison": 0.225, "instructional": 0.19})


class TermExtractionTests(unittest.TestCase):
    """Clearscope 公式: importance = ceil(命中竞品数/竞品总数×10),1-10"""

    def test_importance_formula(self):
        import content_score as cs
        comps = ["alpha beta gamma", "alpha beta delta", "alpha gamma epsilon"]
        imp = {t["term"]: t["importance"] for t in cs.extract_terms(comps)}
        self.assertEqual(imp["alpha"], 10)    # 3/3 → ceil(10)
        self.assertEqual(imp["beta"], 7)      # 2/3 → ceil(6.67)
        self.assertEqual(imp["gamma"], 7)
        self.assertEqual(imp["delta"], 4)     # 1/3 → ceil(3.33)
        self.assertTrue(all(1 <= v <= 10 for v in imp.values()))

    def test_cjk_long_term_preferred_over_subgrams(self):
        import content_score as cs
        comps = ["项目管理软件是工具", "项目管理软件看任务", "项目管理软件选型"]
        terms = [t["term"] for t in cs.extract_terms(comps)]
        self.assertIn("项目管理软件", terms)             # 词典式长词优先
        self.assertNotIn("项目", terms)                  # 子段被包含吸收
        self.assertNotIn("理软", terms)


class MarketMuseFormulaTests(unittest.TestCase):
    """MarketMuse【官方】: Σ min(提及,2) ÷ (话题数×2) —— 提及封顶 2"""

    def test_min_mentions_cap(self):
        import content_score as cs
        model = [{"term": "alpha", "importance": 10, "freqs": [2, 2, 2]},
                 {"term": "beta", "importance": 7, "freqs": [1, 0, 0]}]
        s5, _ = cs.score_term_coverage(model, "alpha alpha alpha alpha alpha")
        s2, _ = cs.score_term_coverage(model, "alpha alpha")
        self.assertEqual(s5, s2)                          # 5 次 == 2 次(封顶)
        s1, _ = cs.score_term_coverage(model, "alpha")
        self.assertAlmostEqual(s1, 1.0 / 4 * 100)         # 1 次只计 1
        s0, _ = cs.score_term_coverage(model, "gamma gamma")
        self.assertEqual(s0, 0.0)

    def test_fifty_topics_full_marks(self):
        import content_score as cs
        terms = [{"term": "t%02d" % i, "importance": 10, "freqs": [2] * 3} for i in range(50)]
        text = (" ".join(t["term"] for t in terms) + " ") * 2   # 每话题 2 次
        s, note = cs.score_term_coverage(terms, text)
        self.assertAlmostEqual(s, 100.0)
        self.assertIn("min(提及,2)", note)


class RefusalTests(unittest.TestCase):
    """竞品<3 个不同来源 → 拒绝评分并说明【Surfer 官方】"""

    def test_two_competitors_refused(self):
        a, b, _c, d = _files()
        r = run_script(["--draft", d, "--competitors", ",".join([a, b]), "--keyword", KW])
        self.assertEqual(r.returncode, 2)
        self.assertIn("拒绝评分", r.stdout + r.stderr)
        self.assertIn("Surfer", r.stdout + r.stderr)
        for p in (a, b, d):
            os.unlink(p)

    def test_duplicate_content_counts_as_one_source(self):
        a, _b, _c, d = _files()
        r = run_script(["--draft", d, "--competitors", ",".join([a, a, a]), "--keyword", KW])
        self.assertEqual(r.returncode, 2)
        self.assertIn("1 个不同来源", r.stdout + r.stderr)
        os.unlink(a)
        os.unlink(d)


class DualTrackTests(unittest.TestCase):
    """总分=0.5×SEO+0.5×AI[推断];--json 带 schema_version;密度不计分"""

    def test_total_is_half_and_half(self):
        a, b, c, d = _files()
        r = run_script(["--draft", d, "--competitors", ",".join([a, b, c]),
                        "--keyword", KW, "--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        p = json.loads(r.stdout)
        self.assertEqual(p["schema_version"], "1")
        self.assertAlmostEqual(p["total"], 0.5 * p["seo"]["score"] + 0.5 * p["ai"]["score"],
                               delta=0.11)
        self.assertFalse(p["density_scored"])                       # 官方明确否定密度计分
        self.assertNotIn("density", p["seo"]["dims"])
        for p2 in (a, b, c, d):
            os.unlink(p2)

    def test_seo_dims_match_pinned_weights(self):
        a, b, c, d = _files()
        r = run_script(["--draft", d, "--competitors", ",".join([a, b, c]),
                        "--keyword", KW, "--json"])
        p = json.loads(r.stdout)
        self.assertEqual(set(p["seo"]["dims"]), set(json.loads(json.dumps(
            {"term_coverage": 1, "term_importance": 1, "structure": 1, "title_h1": 1,
             "images_alt": 1, "internal_links": 1, "keyword_variations": 1,
             "bolded": 1, "schema_focused": 1}))))
        for p2 in (a, b, c, d):
            os.unlink(p2)


class IntentLineTests(unittest.TestCase):
    """意图系数行: 官方数值 + "不改分值"(换意图分数不变)"""

    def test_intent_coefficient_line_and_score_invariance(self):
        a, b, c, d = _files()
        args = ["--draft", d, "--competitors", ",".join([a, b, c]), "--keyword", KW]
        r_def = run_script(args)                                   # 默认 definition
        self.assertIn("0.271", r_def.stdout)
        self.assertIn("不改分值", r_def.stdout)
        j1 = json.loads(run_script(args + ["--json"]).stdout)
        j2 = json.loads(run_script(args + ["--intent", "consequence", "--json"]).stdout)
        self.assertEqual(j2["intent_coefficient"], 0.296)
        self.assertEqual(j1["total"], j2["total"])                 # 系数不改分值
        self.assertEqual(j1["seo"]["score"], j2["seo"]["score"])
        for p in (a, b, c, d):
            os.unlink(p)


class UpfrontThreeChecksTests(unittest.TestCase):
    """前三查【官方】: 首句主词/首 100 词数字/先答案后展开"""

    def test_all_pass(self):
        import content_score as cs
        text = ("# 标题\n\n"
                "项目管理软件是团队协作的核心工具。简而言之,选型先看甘特图与预算 2026。\n\n"
                "后续再展开各维度细节。\n")
        checks = cs.upfront_three_checks(text, KW, cs.keyword_variants(KW))
        self.assertEqual(checks, [True, True, True])

    def test_all_fail(self):
        import content_score as cs
        text = "# 标题\n\n这个话题很重要。很多细节值得慢慢讨论,这里不着急下结论。\n\n后面再说。\n"
        checks = cs.upfront_three_checks(text, KW, cs.keyword_variants(KW))
        self.assertEqual(checks, [False, False, False])

    def test_partial_digit_only(self):
        import content_score as cs
        text = "# 标题\n\n有些观点值得留意。更多的背景铺垫与闲谈继续展开没有结论。\n"
        checks = cs.upfront_three_checks(text, KW, cs.keyword_variants(KW))
        self.assertEqual(checks, [False, False, False])
        text2 = "# 标题\n\n有些观点值得留意,涨价 15 元。更多的背景铺垫继续展开没有结论段。\n"
        self.assertEqual(cs.upfront_three_checks(text2, KW, cs.keyword_variants(KW))[1], True)


class BandAndTargetTests(unittest.TestCase):
    """分档 0-33/34-66/67+【官方】;目标=min(max(竞品均值+15,70),85)【官方甜区】"""

    def test_bands(self):
        import content_score as cs
        for t, exp in ((0, "weak"), (33, "weak"), (33.4, "weak"), (34, "mid"), (50, "mid"),
                       (66, "mid"), (66.6, "strong"), (67, "strong"), (100, "strong")):
            self.assertEqual(cs.band(t)[0], exp, "total=%s" % t)
        self.assertEqual(cs.band(50)[1], "34-66")

    def test_target_formula(self):
        import content_score as cs
        self.assertEqual(cs.target_score(40.0), 70.0)     # max(55,70)=70
        self.assertEqual(cs.target_score(55.0), 70.0)     # max(70,70)=70
        self.assertEqual(cs.target_score(60.0), 75.0)     # 60+15
        self.assertEqual(cs.target_score(80.0), 85.0)     # 封顶
        self.assertEqual(cs.target_score(95.0), 85.0)

    def test_markdown_target_line(self):
        a, b, c, d = _files()
        r = run_script(["--draft", d, "--competitors", ",".join([a, b, c]), "--keyword", KW])
        self.assertIn("目标行: 竞品均值", r.stdout)
        self.assertIn("封顶 85", r.stdout)
        self.assertIn("甜区 70-85", r.stdout)
        for p in (a, b, c, d):
            os.unlink(p)


class TermTableTests(unittest.TestCase):
    """术语表 schema {term,importance,recommended_range,used,in_heading,source}
    + 缺失术语清单带自然插入建议点"""

    def test_table_fields_and_missing(self):
        a, b, c, d = _files()
        r = run_script(["--draft", d, "--competitors", ",".join([a, b, c]),
                        "--keyword", KW, "--json"])
        p = json.loads(r.stdout)
        self.assertTrue(p["term_table"])
        for row in p["term_table"]:
            self.assertEqual(set(row), {"term", "importance", "recommended_range",
                                        "used", "in_heading", "source"})
            self.assertRegex(row["recommended_range"], r"^\d+-\d+$")
        self.assertLessEqual(len(p["term_table"]), 50)
        missing_terms = {m["term"] for m in p["missing_terms"]}
        used = {row["term"]: row["used"] for row in p["term_table"]}
        self.assertTrue(missing_terms)
        self.assertTrue(all(used[t] == 0 for t in missing_terms))
        for m in p["missing_terms"]:
            self.assertTrue(m["suggestion"])
        # markdown: Top20 表 + 缺失清单 + 建议箭头
        r2 = run_script(["--draft", d, "--competitors", ",".join([a, b, c]), "--keyword", KW])
        self.assertIn("术语表 Top 20", r2.stdout)
        self.assertIn("缺失术语清单", r2.stdout)
        self.assertIn("→", r2.stdout)
        for p2 in (a, b, c, d):
            os.unlink(p2)


class TermsFileTests(unittest.TestCase):
    """--terms 直接给术语表: importance/source 保留,recommended_range 从竞品补"""

    def test_terms_json(self):
        a, b, c, d = _files()
        tj = tmp_file(json.dumps({"terms": [
            {"term": "甘特图", "importance": 9, "source": "ai"},
            {"term": "不存在词", "importance": 3}]}, ensure_ascii=False), suffix=".json")
        r = run_script(["--draft", d, "--competitors", ",".join([a, b, c]),
                        "--terms", tj, "--keyword", KW, "--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        p = json.loads(r.stdout)
        self.assertEqual(p["term_model"]["source"], "terms-file")
        by = {row["term"]: row for row in p["term_table"]}
        self.assertEqual(by["甘特图"]["importance"], 9)
        self.assertEqual(by["甘特图"]["source"], "ai")
        self.assertEqual(by["不存在词"]["importance"], 3)
        self.assertEqual(by["不存在词"]["source"], "nlp")     # 缺省来源
        self.assertEqual(by["甘特图"]["used"], 0)             # 草稿 C 缺口不含甘特图
        for p2 in (a, b, c, d, tj):
            os.unlink(p2)

    def test_keyword_autopick_noted(self):
        a, b, c, d = _files()
        r = run_script(["--draft", a, "--competitors", ",".join([b, c, d]), "--json"])
        p = json.loads(r.stdout)
        self.assertTrue(p["keyword"])                          # 自动取术语表首位
        self.assertTrue(any("自动取术语表首位" in n for n in p["notes"]))
        for p2 in (a, b, c, d):
            os.unlink(p2)


class FactsTests(unittest.TestCase):
    """--facts 缺省以术语表前 20 作事实代理并注明[推断];显式给则按清单核"""

    def test_proxy_note_without_facts(self):
        a, b, c, d = _files()
        r = run_script(["--draft", d, "--competitors", ",".join([a, b, c]),
                        "--keyword", KW, "--json"])
        p = json.loads(r.stdout)
        self.assertTrue(any("事实代理" in n for n in p["notes"]))
        self.assertIn("术语表前 20 作事实代理", p["ai"]["dims"]["facts_coverage"]["note"])
        for p2 in (a, b, c, d):
            os.unlink(p2)

    def test_explicit_facts_coverage(self):
        a, b, c, d = _files()
        fj = tmp_file("- 甘特图可视化里程碑\n- 完全不相关的量子涨落事实\n", suffix=".md")
        r = run_script(["--draft", a, "--competitors", ",".join([b, c, d]),
                        "--facts", fj, "--keyword", KW, "--json"])
        p = json.loads(r.stdout)
        note = p["ai"]["dims"]["facts_coverage"]["note"]
        self.assertIn("--facts 清单 2 条", note)
        self.assertIn("1/2", note)                       # 草稿 A 覆盖甘特图,不含量子事实
        self.assertAlmostEqual(p["ai"]["dims"]["facts_coverage"]["score"], 50.0)
        self.assertFalse(any("事实代理" in n for n in p["notes"]))
        for p2 in (a, b, c, d, fj):
            os.unlink(p2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
