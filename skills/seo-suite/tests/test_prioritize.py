#!/usr/bin/env python3
"""prioritize.py 回归(stdlib unittest,合成数据,零网络,standalone——
助手照抄 run_tests.py 顶部,不 import run_tests,被其 test_*.py 自动发现加载)。
口径钉死 references/research/borrow-specs.md E2(Botify ActionBoard 条件规则):
官方阈值(depth≥6/inlinks<4/title<50/desc<100/thin<100 词/重复≥90%/canonical 配对<75%)/
放大器(被内链>10 次→×1.5)/条件依赖型(noindex 出提示而非 critical;canonical 看
PageRank 对比;未索引×GSC 三档,缺 GSC 降级"按中优先级")/segment 切换重算/
两栏排序(Ryte)/--rules-json 合并/health_score --json 摘要输入。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)


def run_script(name, args=(), stdin=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def tmp_file(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def make_audit(by_url, metas=None):
    """合成 site_audit --json 输出:by_url={url:[(sev,area,msg)]},metas={url:{...}}。"""
    results = {}
    for url, findings in by_url.items():
        results[url] = {
            "verdict": "fail" if any(s == "CRITICAL" for s, _, _ in findings)
                       else ("refused" if any(s == "SKIP" for s, _, _ in findings) else "pass"),
            "findings": [{"severity": s, "area": a, "message": m} for s, a, m in findings],
            "meta": (metas or {}).get(url, {})}
    return json.dumps({"audited": len(results), "critical": 0, "results": results},
                      ensure_ascii=False)


def pri(by_url, *extra, metas=None):
    """跑 --json 并解析;返回 report dict(找不到规则时用 .get 防 KeyError)。"""
    p = tmp_file(make_audit(by_url, metas))
    r = run_script("prioritize.py", ["--audit", p, "--json", *extra])
    os.unlink(p)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def item(rep, rule_id, column="fix_now"):
    hits = [d for d in rep[column] if d["rule"] == rule_id]
    return hits[0] if hits else None


class PrioritizeThresholdTests(unittest.TestCase):
    """Botify 官方阈值:命中边界两侧各一 URL,只命中越界侧"""

    def test_depth_and_inlinks_official_thresholds(self):
        rep = pri({"https://s.com/a": [], "https://s.com/b": []},
                  metas={"https://s.com/a": {"depth": 7, "inlinks": 2},
                         "https://s.com/b": {"depth": 5, "inlinks": 6}})
        self.assertEqual(item(rep, "depth_deep")["hit_urls"], 1)      # 7≥6 命中,5 不命中
        self.assertEqual(item(rep, "depth_deep")["url_query"], ["https://s.com/a"])
        self.assertEqual(item(rep, "inlinks_low")["hit_urls"], 1)     # 2<4 命中,6 不命中

    def test_title_desc_short_thresholds(self):
        rep = pri({"https://s.com/a": [], "https://s.com/b": []},
                  metas={"https://s.com/a": {"title": "a" * 40, "desc_len": "80 chars/160"},
                         "https://s.com/b": {"title": "b" * 55, "desc_len": "120 chars/160"}})
        self.assertEqual(item(rep, "title_short")["hit_urls"], 1)     # <50 命中;55 不
        self.assertEqual(item(rep, "desc_short")["hit_urls"], 1)      # <100 命中;120 不

    def test_thin_content_threshold_and_template_note(self):
        rep = pri({"https://s.com/a": [], "https://s.com/b": []},
                  metas={"https://s.com/a": {"words": 80}, "https://s.com/b": {"words": 120}})
        thin = item(rep, "thin_content")
        self.assertEqual(thin["hit_urls"], 1)                          # <100 词命中【官方】
        self.assertIn("模板页", thin["conditional"]["question"])       # 条件注:模板页除外

    def test_duplicate_and_canonical_similarity_thresholds(self):
        rep = pri({"https://s.com/a": [], "https://s.com/b": []},
                  metas={"https://s.com/a": {"similarity": 92, "canonical_similarity": 70},
                         "https://s.com/b": {"similarity": 88, "canonical_similarity": 80}})
        self.assertEqual(item(rep, "duplicate_body")["hit_urls"], 1)   # ≥90% 命中
        self.assertEqual(item(rep, "canonical_mismatch")["hit_urls"], 1)  # <75% 命中

    def test_redirect_canonical_combo(self):
        rep = pri({"https://s.com/old": [], "https://s.com/ok": []},
                  metas={"https://s.com/old": {"status": 301, "canonical": "https://s.com/new"},
                         "https://s.com/ok": {"status": 301, "canonical": "https://s.com/ok"}})
        combo = item(rep, "redirect_canonical_conflict")               # 组合信号:3xx×指他页
        self.assertEqual(combo["hit_urls"], 1)                         # 自指 canonical 不算他页
        self.assertEqual(combo["url_query"], ["https://s.com/old"])
        self.assertIn("重定向", combo["conditional"]["question"])


class PrioritizeAmplifierTests(unittest.TestCase):
    """放大器【Botify 官方】:问题页被内链>10 次 → impact×1.5"""

    def test_amplifier_multiplies_impact_by_1_5(self):
        base = {"https://s.com/a": [], "https://s.com/b": []}
        quiet = pri(base, metas={"https://s.com/a": {"depth": 7, "inlinks": 2},
                                 "https://s.com/b": {"depth": 1, "inlinks": 2}})
        loud = pri(base, metas={"https://s.com/a": {"depth": 7, "inlinks": 12},
                                "https://s.com/b": {"depth": 1, "inlinks": 2}})
        q, l = item(quiet, "depth_deep"), item(loud, "depth_deep")
        self.assertEqual(q["impact"], 1.0)          # 1/2 × WARN2 × 1.0
        self.assertEqual(l["impact"], 1.5)          # 1/2 × WARN2 × 1.5【官方】
        self.assertIsNone(q["amplifier"])           # 被链≤10 不触发
        self.assertEqual(l["amplifier"]["factor"], 1.5)
        self.assertEqual(l["amplifier"]["amplified_urls"], 1)


class PrioritizeConditionalTests(unittest.TestCase):
    """条件依赖型【Botify 精髓】:提示而非 critical / PageRank 对比 / GSC 三档分流"""

    def test_noindex_conditional_hint_not_critical(self):
        rep = pri({"https://s.com/thanks": [("CRITICAL", "robots", "noindex")],
                   "https://s.com/ok": []})
        hint = item(rep, "noindex_intent")
        self.assertNotEqual(hint["severity"], "CRITICAL")             # 不直接 critical
        self.assertEqual(hint["severity"], "WARN")
        self.assertTrue(hint["conditional"]["needs_human"])           # 输出 conditional 提示
        self.assertIn("意图", hint["conditional"]["question"])
        # markdown 同样呈现"需人工判定"
        p = tmp_file(make_audit({"https://s.com/thanks": [("CRITICAL", "robots", "noindex")]}))
        r = run_script("prioritize.py", ["--audit", p])
        os.unlink(p)
        self.assertIn("noindex_intent", r.stdout)
        self.assertIn("需人工判定", r.stdout)

    def test_canonical_pagerank_auto_and_human(self):
        by_url = {"https://s.com/ok": [], "https://s.com/wrong": [], "https://s.com/unknown": []}
        metas = {  # 让渡对象更强=对(剔除)/更弱=错(命中)/缺数据=需人工
            "https://s.com/ok": {"canonical": "https://s.com/hub", "pagerank": 5,
                                 "canonical_pagerank": 8},
            "https://s.com/wrong": {"canonical": "https://s.com/hub", "pagerank": 8,
                                    "canonical_pagerank": 5},
            "https://s.com/unknown": {"canonical": "https://s.com/hub"}}
        rep = pri(by_url, metas=metas)
        cp = item(rep, "canonical_pagerank")
        self.assertEqual(cp["hit_urls"], 2)                            # wrong + unknown
        self.assertEqual(cp["conditional"]["verdicts"],
                         {"auto_correct": 1, "auto_wrong": 1, "needs_human": 1})
        self.assertTrue(cp["conditional"]["needs_human"])
        # 全部让渡正确时 0 命中 → 进 no_hit_rules
        ok = pri({"https://s.com/a": []},
                 metas={"https://s.com/a": {"canonical": "https://s.com/hub",
                                            "pagerank": 1, "canonical_pagerank": 9}})
        self.assertIn("canonical_pagerank", ok["no_hit_rules"])
        # 完全缺数据:保留命中 + 降级注
        nodata = pri({"https://s.com/a": []},
                     metas={"https://s.com/a": {"canonical": "https://s.com/hub"}})
        self.assertTrue(any("需人工判定" in n for n in
                            pri({"https://s.com/a": []},
                                metas={"https://s.com/a": {"canonical": "https://s.com/hub"}})
                            ["degradation_notes"]))

    def test_gsc_urgency_triage_and_degradation(self):
        noindex = [("CRITICAL", "robots", "noindex")]
        rep = pri({"https://s.com/u1": noindex, "https://s.com/u2": noindex,
                   "https://s.com/u3": noindex},
                  metas={"https://s.com/u1": {"gsc_clicks": 50},
                         "https://s.com/u2": {"gsc_clicks": 0},
                         "https://s.com/u3": {}})
        t = item(rep, "not_indexed_with_traffic")
        self.assertEqual(t["severity"], "CRITICAL")                    # 有历史流量=紧急
        self.assertEqual(t["conditional"]["urgency_split"],
                         {"紧急(历史 clicks>0)": 1, "低(零流量)": 1, "中(缺 GSC 上下文)": 1})
        self.assertEqual(t["conditional"]["urgent_urls"], ["https://s.com/u1"])
        self.assertTrue(any("缺 GSC 上下文" in n and "中优先级" in n
                            for n in rep["degradation_notes"]))        # 降级标注原文
        self.assertTrue(rep["context"]["gsc"])
        # 纯零流量:整体降为 INFO/低
        zero = pri({"https://s.com/z": noindex}, metas={"https://s.com/z": {"gsc_clicks": 0}})
        self.assertEqual(item(zero, "not_indexed_with_traffic")["severity"], "INFO")
        # 完全缺 GSC:按中优先级(WARN)且 context.gsc=False
        mid = pri({"https://s.com/z": noindex})
        self.assertEqual(item(mid, "not_indexed_with_traffic")["severity"], "WARN")
        self.assertFalse(mid["context"]["gsc"])


class PrioritizeSegmentTests(unittest.TestCase):
    """segment 切换重算优先级【Botify 官方行为】"""

    AUDIT = {"https://s.com/pricing/deep": [], "https://s.com/docs/shallow": []}
    METAS = {"https://s.com/pricing/deep": {"depth": 7},
             "https://s.com/docs/shallow": {"depth": 2}}

    def test_segment_recomputes_priorities(self):
        full = pri(self.AUDIT, metas=self.METAS)
        seg = pri(self.AUDIT, "--segment", "/docs", metas=self.METAS)
        self.assertEqual((full["urls_total"], full["segment"]), (2, None))
        self.assertEqual(item(full, "depth_deep")["hit_urls"], 1)      # 全站:1/2 命中
        self.assertEqual((seg["urls_total"], seg["segment"]), (1, "/docs"))
        self.assertIn("depth_deep", seg["no_hit_rules"])               # segment 内重算→0 命中
        self.assertIsNone(item(seg, "depth_deep"))
        self.assertEqual(seg["urls_matched_segment"], 1)

    def test_segment_zero_match_rejected(self):
        p = tmp_file(make_audit(self.AUDIT, self.METAS))
        r = run_script("prioritize.py", ["--audit", p, "--segment", "/nothing"])
        os.unlink(p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("匹配 0 URL", r.stderr)


class PrioritizeColumnsTests(unittest.TestCase):
    """两栏(Ryte 口径):立即处理 impact>0 降序;Opportunity 类进值得探索栏"""

    def test_two_columns_sorted_and_opportunity_in_explore(self):
        long_url = "https://s.com/" + "x" * 130
        rep = pri({"https://s.com/deep": [], "https://s.com/h1": [("CRITICAL", "h1", "无 H1")],
                   long_url: []},
                  metas={"https://s.com/deep": {"depth": 7},
                         "https://s.com/h1": {}, long_url: {"depth": 1}})
        # fix_now:impact>0 且非 opportunity,降序
        impacts = [d["impact"] for d in rep["fix_now"]]
        self.assertEqual(impacts, sorted(impacts, reverse=True))
        self.assertTrue(all(d["impact"] > 0 for d in rep["fix_now"]))
        # h1_missing CRITICAL(权重3)排在 depth WARN(权重2)前
        rules = [d["rule"] for d in rep["fix_now"]]
        self.assertLess(rules.index("h1_missing"), rules.index("depth_deep"))
        # opportunity 类(url>115,SF 官方 Opportunity 定级)只进 explore
        self.assertIsNone(item(rep, "url_long"))
        opp = item(rep, "url_long", column="explore")
        self.assertEqual((opp["hit_urls"], opp["severity"]), (1, "INFO"))
        # 每条附 fix_instruction 与 url_query(前 20)
        for d in rep["fix_now"] + rep["explore"]:
            self.assertTrue(d["fix_instruction"])
            self.assertLessEqual(len(d["url_query"]), 20)

    def test_refused_urls_excluded(self):
        rep = pri({"https://s.com/a": [],
                   "https://s.com/b": [("SKIP", "fetch guard", "refusing to audit")]},
                  metas={"https://s.com/a": {"depth": 7}})
        self.assertEqual((rep["urls_total"], rep["urls_refused"]), (1, 1))
        self.assertEqual(item(rep, "depth_deep")["impact"], 2.0)       # 1/1×WARN2


class PrioritizeCustomRulesTests(unittest.TestCase):
    """--rules-json:同 schema 按 id 覆盖内置 / 新 id 追加合并"""

    def test_override_and_append(self):
        custom = {"rules": [
            {"id": "depth_deep", "category": "information_architecture", "detect": "depth",
             "thresholds": {"gte": 3}, "severity": "WARN", "fix": "自定义:depth>=3 上移"},
            {"id": "alt_missing", "category": "content", "detect": "finding",
             "thresholds": {"area": "images", "severity": "WARN"}, "fix": "补 alt"}]}
        by_url = {"https://s.com/a": [("WARN", "images", "alt 缺失 3/5")],
                  "https://s.com/b": []}
        metas = {"https://s.com/a": {"depth": 4}, "https://s.com/b": {"depth": 2}}
        pc = tmp_file(json.dumps(custom))
        p = tmp_file(make_audit(by_url, metas))
        r = run_script("prioritize.py", ["--audit", p, "--json", "--rules-json", pc])
        os.unlink(pc)
        os.unlink(p)
        rep = json.loads(r.stdout)
        deep = item(rep, "depth_deep")                                 # 覆盖阈值:4 现在命中
        self.assertEqual(deep["hit_urls"], 1)
        self.assertEqual(deep["fix_instruction"], "自定义:depth>=3 上移")
        alt = item(rep, "alt_missing")                                 # 追加规则生效
        self.assertEqual((alt["hit_urls"], alt["fix_instruction"]), (1, "补 alt"))

    def test_bad_schema_rejected(self):
        for bad in ({"rules": [{"id": "x", "category": "c", "detect": "nope", "fix": "f"}]},
                    {"rules": [{"id": "x", "category": "c", "detect": "depth", "fix": ""}]},
                    {"rules": [{"id": "x", "category": "c", "detect": "finding",
                                "thresholds": {}, "fix": "f"}]}):      # finding 缺 thresholds.area
            pc = tmp_file(json.dumps(bad))
            p = tmp_file(make_audit({"https://s.com/a": []}))
            r = run_script("prioritize.py", ["--audit", p, "--rules-json", pc])
            os.unlink(pc)
            os.unlink(p)
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("自定义规则", r.stderr)


class PrioritizeHealthScoreInputTests(unittest.TestCase):
    """health_score.py --json 摘要输入:优先识别/area 映射/条件依赖型降级为提示"""

    HS = {"schema_version": "1.0", "main_score": 50.0, "band": "Fair",
          "warn_score": 75.0, "info_score": 100.0, "category_scores": {},
          "ignored": [], "unmapped": [], "coverage_note": "x",
          "impacts": [
              {"rule": "title", "category": "rankability", "subgroup": "page_content",
               "severity": "CRITICAL", "hit_urls": 2, "total_urls": 4, "impact": 4.5,
               "action": "立即处理"},
              {"rule": "robots", "category": "indexability", "subgroup": "non_indexable",
               "severity": "CRITICAL", "hit_urls": 1, "total_urls": 4, "impact": 2.25,
               "action": "立即处理"},
              {"rule": "sitemap", "category": "discoverability", "subgroup": "sitemaps",
               "severity": "INFO", "hit_urls": 0, "total_urls": 4, "impact": 0.0,
               "action": "opportunity 值得探索"}],
          "urls_total": 4, "urls_clean": 2, "urls_refused": 0}

    def test_summary_input_mapped_and_degraded(self):
        p = tmp_file(json.dumps(self.HS))
        r = run_script("prioritize.py", ["--audit", p, "--json"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["input_format"], "health_score")          # 优先识别
        tm = item(rep, "title_missing")                                # area title→补 title 语义
        self.assertEqual((tm["hit_urls"], tm["severity"]), (2, "CRITICAL"))
        self.assertEqual(tm["impact"], 1.5)                            # 2/4×CRITICAL3 重算
        ni = item(rep, "noindex_intent")                               # robots→条件依赖型
        self.assertNotEqual(ni["severity"], "CRITICAL")                # 摘要无意图数据:不直接 critical
        self.assertTrue(ni["conditional"]["needs_human"])
        self.assertEqual(item(rep, "title_missing")["url_query"], [])  # 摘要无逐页清单
        self.assertIn("sitemap", rep["no_hit_rules"])
        # 页面级字段规则全部降级声明
        degraded = {d["rule"] for d in rep["degraded_rules"]}
        self.assertIn("depth_deep", degraded)
        self.assertIn("canonical_pagerank", degraded)
        self.assertTrue(any("逐页" in n for n in rep["degradation_notes"]))


class PrioritizeCliTests(unittest.TestCase):
    """--help / 输入错误退出码 2 / coverage_note 与 schema 恒在"""

    def test_help(self):
        r = run_script("prioritize.py", ["--help"])
        self.assertEqual(r.returncode, 0)
        for frag in ("usage: prioritize.py", "--audit", "--segment", "--rules-json",
                     "depth_deep", "×1.5"):
            self.assertIn(frag, r.stdout)

    def test_input_errors_exit_2(self):
        p = tmp_file(make_audit({"https://s.com/a": []}))
        for args in (["--audit", "/nonexistent.json"],
                     ["--audit", p, "--segment", "["],          # 非法 regex
                     ["--audit", p, "--nope"],                  # 未知参数
                     []):                                       # 缺 --audit
            r = run_script("prioritize.py", args)
            self.assertEqual(r.returncode, 2, args)
        os.unlink(p)
        bad = tmp_file('{"hello": "world"}')                    # 既无 results 也无 impacts
        r = run_script("prioritize.py", ["--audit", bad])
        os.unlink(bad)
        self.assertEqual(r.returncode, 2)
        self.assertIn("无法识别的输入格式", r.stderr)

    def test_schema_and_coverage_always_present(self):
        rep = pri({"https://s.com/a": []})
        self.assertEqual(rep["schema_version"], "1.0")
        self.assertEqual(rep["input_format"], "site_audit")
        self.assertIn("不可外推", rep["coverage_note"])

    def test_degraded_rules_reported_when_field_missing(self):
        # 无任何 depth 字段 → depth_deep 降级声明而非静默消失
        rep = pri({"https://s.com/a": []})
        self.assertIn("depth_deep", {d["rule"] for d in rep["degraded_rules"]})
        self.assertIsNone(item(rep, "depth_deep"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
