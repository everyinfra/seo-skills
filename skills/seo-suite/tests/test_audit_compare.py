#!/usr/bin/env python3
"""audit_compare.py + ci_format.py 回归(stdlib unittest,合成两个 audit JSON,
零网络,standalone——助手照抄 run_tests.py 顶部,不 import run_tests,被其 test_*.py
自动发现加载)。口径钉死 references/research/borrow-specs.md A1(Ahrefs Crawl
Comparison/主分公式/Lumar Protect 语义)与 D 节 CI 输出(SARIF/JUnit/注解)。
覆盖:新增/修复/严重度升级三态、delta 三清单、页级 changed、baseline-gate 退出码、
to_sarif 结构(ruleId/level/helpUri 条件添加)、to_junit testsuite/properties、
to_github 注解格式与每 URL 十行截断、diff 输入归一、--help。"""
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


def make_audit(by_url, ai=None, metas=None):
    """合成 site_audit --json 输出:by_url={url:[(sev,area,msg)]},
    ai={url:{"score":N}},metas={url:{title/words/h1/canonical...}}。"""
    results = {}
    for url, findings in by_url.items():
        results[url] = {
            "verdict": "fail" if any(s == "CRITICAL" for s, _, _ in findings)
                       else ("refused" if any(s == "SKIP" for s, _, _ in findings) else "pass"),
            "findings": [{"severity": s, "area": a, "message": m} for s, a, m in findings],
            "meta": (metas or {}).get(url) or {},
            "ai_search_health": (ai or {}).get(url)}
    return {"audited": len(results), "critical": 0, "results": results}


def diff(old_by, new_by, *cli, ai_old=None, ai_new=None, metas_old=None, metas_new=None):
    """写两份合成审计 → 跑 audit_compare --json;返回 (报告 dict, 退出码)。"""
    po = tmp_file(json.dumps(make_audit(old_by, ai_old, metas_old), ensure_ascii=False))
    pn = tmp_file(json.dumps(make_audit(new_by, ai_new, metas_new), ensure_ascii=False))
    r = run_script("audit_compare.py", ["--old", po, "--new", pn, "--json", *cli])
    os.unlink(po)
    os.unlink(pn)
    return json.loads(r.stdout), r.returncode


A = "https://s.com/a"
B = "https://s.com/b"


class AuditCompareIssueTests(unittest.TestCase):
    """新增/已修复/严重度升级(按 URL+rule 认定)"""

    def test_new_issues_detected(self):
        rep, rc = diff({A: [("WARN", "title", "18 chars <20")]},
                       {A: [("WARN", "title", "18 chars <20")],
                        B: [("CRITICAL", "robots", "noindex")]})
        self.assertEqual(rc, 0)
        self.assertEqual(len(rep["new_issues"]), 1)
        it = rep["new_issues"][0]
        self.assertEqual((it["url"], it["rule"], it["severity"]), (B, "robots", "CRITICAL"))
        self.assertFalse(it["escalated"])
        self.assertEqual(rep["fixed_issues"], [])

    def test_fixed_issues_detected(self):
        rep, _ = diff({A: [("WARN", "canonical", "缺失"), ("INFO", "sitemap", "/sitemap.xml 不可达")]},
                      {A: [("WARN", "canonical", "缺失")]})
        fixed = rep["fixed_issues"]
        self.assertEqual(len(fixed), 1)
        self.assertEqual((fixed[0]["url"], fixed[0]["rule"]), (A, "sitemap"))
        self.assertEqual(rep["new_issues"], [])

    def test_same_url_rule_both_sides_not_listed(self):
        rep, _ = diff({A: [("WARN", "title", "18 chars <20")]},
                      {A: [("WARN", "title", "22 chars <20")]})   # 消息抖动不算增删
        self.assertEqual(rep["new_issues"], [])
        self.assertEqual(rep["fixed_issues"], [])

    def test_severity_escalation_counts_as_new(self):
        rep, _ = diff({A: [("WARN", "content", "词数 150 <200")]},
                      {A: [("CRITICAL", "content", "词数 0 <200")]})
        self.assertEqual(len(rep["new_issues"]), 1)
        it = rep["new_issues"][0]
        self.assertTrue(it["escalated"])
        self.assertEqual((it["severity_before"], it["severity"]), ("WARN", "CRITICAL"))
        self.assertEqual(rep["fixed_issues"], [])   # 升级不是修复

    def test_skip_findings_are_not_issues(self):
        rep, _ = diff({A: []},
                      {A: [], B: [("SKIP", "fetch guard", "refusing to audit")]})
        self.assertEqual(rep["new_issues"], [])     # 拒审不产生 issue


class AuditCompareDeltaTests(unittest.TestCase):
    """分数与覆盖面 delta:主分/AI 健康/verdict/URL 增删/受影响面"""

    def test_main_score_and_delta(self):
        rep, _ = diff({A: [("CRITICAL", "robots", "noindex")], B: [], "https://s.com/c": []},
                      {A: [("CRITICAL", "robots", "noindex")], B: [("CRITICAL", "h1", "无 H1")],
                       "https://s.com/c": [("CRITICAL", "title", "缺失")]})
        self.assertEqual(rep["old"]["main_score"], 66.7)   # 2/3 无 CRITICAL
        self.assertEqual(rep["new"]["main_score"], 0.0)
        self.assertEqual(rep["delta"]["main_score"], -66.7)
        self.assertEqual(rep["old"]["affected_urls"], 1)
        self.assertEqual(rep["new"]["affected_urls"], 3)
        self.assertEqual(rep["delta"]["affected_urls"], 2)

    def test_ai_health_changes(self):
        rep, _ = diff({A: [], B: []}, {A: [], B: []},
                      ai_old={A: {"score": 40}, B: {"score": 60}},
                      ai_new={A: {"score": 70}, B: {"score": 60}})
        self.assertEqual(rep["old"]["ai_search_health_mean"], 50.0)
        self.assertEqual(rep["new"]["ai_search_health_mean"], 65.0)
        self.assertEqual(rep["delta"]["ai_search_health_mean"], 15.0)
        ch = rep["ai_health_changes"]
        self.assertEqual(len(ch), 1)
        self.assertEqual((ch[0]["url"], ch[0]["old"], ch[0]["new"], ch[0]["delta"]),
                         (A, 40, 70, 30))

    def test_verdict_changes_and_url_coverage(self):
        rep, _ = diff({A: [], B: []}, {A: [("CRITICAL", "robots", "noindex")], "https://s.com/c": []})
        vc = rep["verdict_changes"]
        self.assertEqual(len(vc), 1)
        self.assertEqual((vc[0]["url"], vc[0]["old"], vc[0]["new"]), (A, "pass", "fail"))
        self.assertEqual(rep["delta"]["urls_added"], ["https://s.com/c"])
        self.assertEqual(rep["delta"]["urls_removed"], [B])
        self.assertEqual(rep["delta"]["coverage_ratio"], 0.5)   # 交集 1 ÷ max(2,2)

    def test_pages_changed_fields(self):
        rep, _ = diff({A: [], B: []}, {A: [], B: []},
                      metas_old={A: {"title": "T1", "words": 100},
                                 B: {"title": "同", "words": 100, "canonical": None}},
                      metas_new={A: {"title": "T2", "words": 150, "canonical": "https://x/c"},
                                 B: {"title": "同", "words": 100}})
        pages = {p["url"]: p["changes"] for p in rep["pages_changed"]}
        self.assertEqual(set(pages), {A})                     # B 无字段变化
        fields = {c["field"]: c for c in pages[A]}
        # canonical 旧侧缺失→新侧有值 = 变化;两侧皆缺不报
        self.assertEqual(set(fields), {"title", "word_count", "canonical"})
        self.assertEqual((fields["title"]["old"], fields["title"]["new"]), ("T1", "T2"))
        self.assertEqual((fields["word_count"]["old"], fields["word_count"]["new"]), (100, 150))
        self.assertEqual(fields["canonical"]["new"], "https://x/c")


class AuditCompareGateTests(unittest.TestCase):
    """--baseline-gate(Lumar Protect 语义):主分跌幅>N → 退出码 1;默认不启用"""

    DROP = {A: [], B: []}, {A: [("CRITICAL", "robots", "noindex")], B: []}   # 100 → 50

    def test_gate_trips_exit_1(self):
        rep, rc = diff(*self.DROP, "--baseline-gate", "10")
        self.assertEqual(rep["baseline_gate"]["drop"], 50.0)
        self.assertTrue(rep["baseline_gate"]["tripped"])
        self.assertEqual(rc, 1)

    def test_gate_within_threshold_and_default_off(self):
        rep, rc = diff(*self.DROP, "--baseline-gate", "60")   # 跌幅 50 ≤ 60 → 不触发
        self.assertFalse(rep["baseline_gate"]["tripped"])
        self.assertEqual(rc, 0)
        rep2, rc2 = diff(*self.DROP)                          # 默认不启用
        self.assertIsNone(rep2["baseline_gate"])
        self.assertEqual(rc2, 0)

    def test_markdown_sections_and_help(self):
        po = tmp_file(json.dumps(make_audit({A: []}), ensure_ascii=False))
        pn = tmp_file(json.dumps(make_audit({B: [("CRITICAL", "robots", "noindex")]}),
                                 ensure_ascii=False))
        r = run_script("audit_compare.py", ["--old", po, "--new", pn])
        os.unlink(po)
        os.unlink(pn)
        self.assertEqual(r.returncode, 0)
        for sec in ("新增 issue", "已修复 issue", "分数与覆盖面 delta", "页级 changed"):
            self.assertIn(sec, r.stdout)
        self.assertIn("coverage_ratio", r.stdout)
        h = run_script("audit_compare.py", ["--help"])
        self.assertEqual(h.returncode, 0)
        self.assertIn("usage: audit_compare.py", h.stdout)


AUDIT = make_audit(
    {A: [("CRITICAL", "robots", "noindex"), ("WARN", "og", "og:title 缺失"),
         ("INFO", "sitemap", "/sitemap.xml 不可达")],
     B: [("SKIP", "fetch guard", "refusing to audit")]},
    ai={A: {"score": 40}, B: {"score": 60}})


class CiFormatSarifTests(unittest.TestCase):
    """to_sarif:ruleId {area}-{简名}/level 三档/uri/helpUri 条件添加/invocations"""

    def test_sarif_structure(self):
        import ci_format as cf
        sarif = cf.to_sarif(AUDIT)
        self.assertEqual(sarif["version"], "2.1.0")
        run = sarif["runs"][0]
        self.assertEqual(len(run["results"]), 3)             # SKIP 不进 result
        by_sev = {r["level"] for r in run["results"]}
        self.assertEqual(by_sev, {"error", "warning", "note"})   # CRITICAL/WARN/INFO
        rids = {r["ruleId"] for r in run["results"]}
        self.assertIn("robots-noindex", rids)                # 消息前导 ASCII 标识作简名
        self.assertIn("og-og-title", rids)
        self.assertIn("sitemap", rids)                       # "/sitemap.xml..." 以 / 开头无标识 → 退化 area
        for r in run["results"]:
            uri = r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            self.assertEqual(uri, A)                          # uri=被审计 URL(拒审页无 result)
        self.assertTrue(all("helpUri" not in rule for rule in
                            run["tool"]["driver"]["rules"]))   # 无真实文档 URL → 不添加(空串会崩)
        props = run["invocations"][0]["properties"]
        self.assertEqual(props["main_score"], 0.0)            # 拒审不进分母,1/1 可评分且带 CRITICAL
        self.assertEqual(props["ai_search_health"], 50.0)     # (40+60)/2

    def test_sarif_help_uri_conditional(self):
        import ci_format as cf
        cf.HELP_URIS["robots"] = "https://example.com/docs/robots"
        try:
            sarif = cf.to_sarif(AUDIT)
        finally:
            del cf.HELP_URIS["robots"]
        rules = {r["id"]: r for r in sarif["runs"][0]["tool"]["driver"]["rules"]}
        self.assertEqual(rules["robots-noindex"]["helpUri"], "https://example.com/docs/robots")
        self.assertNotIn("helpUri", rules["sitemap"])         # 其他 area 仍不添加


class CiFormatJunitTests(unittest.TestCase):
    """to_junit:每 area 一个 testsuite;类目得分<50% 满分即 failure;顶层 properties"""

    def test_junit_failure_below_half(self):
        import ci_format as cf
        audit = make_audit({A: [("WARN", "content", "词数 100 <200")],
                            B: [("WARN", "content", "词数 120 <200")]},
                           ai={A: {"score": 40}, B: {"score": 60}})
        xml = cf.to_junit(audit)
        self.assertTrue(xml.startswith("<?xml"))
        self.assertIn('<testsuite name="content" tests="1" failures="1">', xml)
        self.assertIn('<failure type="AreaScoreBelow50"', xml)          # 0/2 未命中 → 0 分 <50
        self.assertIn('<property name="audit.score" value="100.0"/>', xml)   # WARN 不扣主分
        self.assertIn('<property name="ai_search_health" value="50.0"/>', xml)
        self.assertTrue(xml.startswith('<?xml version="1.0" encoding="UTF-8"?>\n'
                                       '<testsuites name="seo-site-audit" tests="1" failures="1">'))

    def test_junit_passing_area_and_clean_audit(self):
        import ci_format as cf
        urls = {f"https://s.com/{i}": [] for i in range(10)}
        urls[A] = [("WARN", "content", "词数 100 <200")]        # 9/10 未命中 → 90 分
        xml = cf.to_junit(make_audit(urls))
        self.assertIn('<testsuite name="content" tests="1" failures="0">', xml)
        self.assertNotIn("<failure", xml)
        clean = cf.to_junit(make_audit({A: [], B: []}))          # 无任何 finding
        self.assertIn('name="no-findings"', clean)


class CiFormatGithubTests(unittest.TestCase):
    """to_github:注解格式/严重度映射/每 URL 前十行截断防刷屏"""

    def test_annotation_format(self):
        import ci_format as cf
        out = cf.to_github(AUDIT).splitlines()
        self.assertTrue(out[0].startswith("::notice title=SEO::audited="))   # 首行摘要
        ann = [l for l in out if "(%s)" % A in l]
        self.assertEqual(len(ann), 3)                            # SKIP 不出注解
        self.assertIn("::error title=SEO::[robots] noindex (%s)" % A, out)
        self.assertIn("::warning title=SEO::[og] og:title 缺失 (%s)" % A, out)
        self.assertIn("::notice title=SEO::[sitemap] /sitemap.xml 不可达 (%s)" % A, out)

    def test_per_url_ten_line_truncation(self):
        import ci_format as cf
        audit = make_audit({A: [("INFO", "rule-%d" % i, "msg %d" % i) for i in range(12)]})
        out = cf.to_github(audit).splitlines()
        mentions = [l for l in out if A in l]
        self.assertEqual(len(mentions), 11)                      # 10 条注解 + 1 条截断提示
        self.assertEqual(len([l for l in mentions if l.startswith("::error")]), 0)
        self.assertEqual(len([l for l in mentions if l.startswith("::notice title=SEO::[rule-")]), 10)
        self.assertTrue(any("[truncated]" in l and "其余 2 条" in l for l in mentions))


class CiFormatCliTests(unittest.TestCase):
    """CLI:--help / diff 输入归一(audit_compare --json → SARIF)/junit 直出"""

    def test_help(self):
        r = run_script("ci_format.py", ["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage: ci_format.py", r.stdout)
        self.assertIn("--format sarif|junit|github|json", r.stdout)

    def test_diff_input_normalized(self):
        d = {"schema_version": "1.0", "new_issues": [
            {"url": A, "rule": "robots", "severity": "CRITICAL",
             "message": "noindex", "escalated": False}],
            "fixed_issues": [], "baseline_gate": None}
        p = tmp_file(json.dumps(d, ensure_ascii=False))
        r = run_script("ci_format.py", [p, "--format", "sarif"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        sarif = json.loads(r.stdout)
        res = sarif["runs"][0]["results"]
        self.assertEqual(len(res), 1)
        self.assertEqual((res[0]["ruleId"], res[0]["level"]), ("robots-noindex", "error"))
        self.assertEqual(res[0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"], A)

    def test_cli_junit_output(self):
        p = tmp_file(json.dumps(AUDIT, ensure_ascii=False))
        r = run_script("ci_format.py", [p, "--format", "junit"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        self.assertIn('<testsuites name="seo-site-audit"', r.stdout)
        self.assertIn('name="robots"', r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
