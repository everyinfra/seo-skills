#!/usr/bin/env python3
"""R5 三 bug 修复回归:health_score 除零/分档边界 + audit_compare 已修复清单污染
(stdlib unittest,合成数据,零网络,standalone——助手照抄 run_tests.py 顶部,
不 import run_tests,被其 test_*.py 自动发现加载)。
钉死 references/overview/pipeline-completeness.md R5「审计链」三项:
  1. health_score 全拒审(total=0)不得除零崩溃——compute 前拦截,退出码 2(输入错);
  2. band 边界:round(score) 取整后再分档(30.4→30→Weak;70.6→71→Good);
  3. audit_compare 已修复清单污染:fixed 只认新审计在场且 verdict≠refused 的 URL,
     拒审/消失 URL 的旧 issue 另列 disappeared_or_refused,不算修复(拒审≠修复)。"""
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
    return {"audited": len(results), "critical": 0, "results": results}


def score(by_url, *extra):
    """跑 health_score --json 并解析;返回 (report_dict|None, returncode, stderr)。"""
    p = tmp_file(json.dumps(make_audit(by_url), ensure_ascii=False))
    r = run_script("health_score.py", ["--input", p, "--json", *extra])
    os.unlink(p)
    rep = json.loads(r.stdout) if r.stdout.strip() else None
    return rep, r.returncode, r.stderr


def diff(old_by, new_by, *cli):
    """写两份合成审计 → 跑 audit_compare --json;返回 (报告 dict, 退出码)。"""
    po = tmp_file(json.dumps(make_audit(old_by), ensure_ascii=False))
    pn = tmp_file(json.dumps(make_audit(new_by), ensure_ascii=False))
    r = run_script("audit_compare.py", ["--old", po, "--new", pn, "--json", *cli])
    os.unlink(po)
    os.unlink(pn)
    return json.loads(r.stdout), r.returncode


A = "https://s.com/a"
B = "https://s.com/b"
SKIP = ("SKIP", "fetch guard", "refusing to audit")


class HealthScoreZeroTotalTests(unittest.TestCase):
    """R5-①:全拒审/空 results 不得除零崩溃——compute 前拦截,退出码 2"""

    def test_all_refused_exits_2_not_crash(self):
        _, rc, err = score({A: [SKIP], B: [SKIP]})
        self.assertEqual(rc, 2)                        # 输入错,而非 ZeroDivisionError 崩溃
        self.assertIn("无可评分 URL", err)
        self.assertNotIn("Traceback", err)             # 不许以崩溃伪装退出码 1
        self.assertNotIn("ZeroDivisionError", err)

    def test_empty_results_exits_2(self):
        _, rc, err = score({})
        self.assertEqual(rc, 2)
        self.assertIn("无可评分 URL", err)
        self.assertNotIn("Traceback", err)

    def test_partial_refused_still_scores(self):
        """部分拒审不受影响:可评分 URL 正常计分,拒审单列。"""
        rep, rc, _ = score({A: [SKIP], B: [("WARN", "title", "18 chars <20")]})
        self.assertEqual(rc, 0)
        self.assertEqual((rep["urls_total"], rep["urls_refused"]), (1, 1))
        self.assertEqual(rep["main_score"], 100.0)


class HealthScoreBandRoundingTests(unittest.TestCase):
    """R5-②:分档按 round 后的整数取档(30.4→30→Weak;70.6→71→Good)"""

    def test_band_of_rounds_before_banding(self):
        import health_score as hs
        self.assertEqual(hs.band_of(70.6), "Good")     # 取整 71 ≥ 71;未取整 70.6<71 误落 Fair
        self.assertEqual(hs.band_of(90.6), "Excellent")
        self.assertEqual(hs.band_of(30.4), "Weak")     # docstring 钉死例:取整 30 → Weak
        self.assertEqual(hs.band_of(70.4), "Fair")     # 取整 70 → 不跨档
        self.assertEqual(hs.band_of(30), "Weak")
        self.assertEqual(hs.band_of(31), "Fair")

    def test_end_to_end_score_70_6_bands_good(self):
        # 500 URL 中 147 个 CRITICAL → 主分 353/500=70.6 → 取整 71 → Good(退出码 0)
        crit = [("CRITICAL", "robots", "noindex")]
        by_url = {f"https://s.com/{i}": (crit if i < 147 else []) for i in range(500)}
        rep, rc, _ = score(by_url)
        self.assertEqual(rep["main_score"], 70.6)
        self.assertEqual(rep["band"], "Good")
        self.assertEqual(rc, 0)

    def test_end_to_end_score_30_4_bands_weak_exit_1(self):
        # 500 URL 中 348 个 CRITICAL → 主分 30.4 → 取整 30 → Weak(退出码 1)
        crit = [("CRITICAL", "robots", "noindex")]
        by_url = {f"https://s.com/{i}": (crit if i < 348 else []) for i in range(500)}
        rep, rc, _ = score(by_url)
        self.assertEqual(rep["main_score"], 30.4)
        self.assertEqual(rep["band"], "Weak")
        self.assertEqual(rc, 1)


class AuditCompareFixedPollutionTests(unittest.TestCase):
    """R5-③:拒审≠修复——fixed 限定新审计在场且 verdict≠refused 的 URL"""

    def test_refused_url_old_issues_not_counted_fixed(self):
        rep, rc = diff({A: [("CRITICAL", "robots", "noindex")]},
                       {A: [SKIP]})                     # 新审计拒审 A,旧 issue 未复检
        self.assertEqual(rc, 0)
        self.assertEqual(rep["fixed_issues"], [])       # 拒审不是修复
        self.assertEqual(rep["disappeared_or_refused"],
                         [{"url": A, "reason": "refused", "held_issues": 1}])

    def test_disappeared_url_old_issues_not_counted_fixed(self):
        rep, _ = diff({A: [("WARN", "title", "18 chars <20")], B: []},
                      {B: []})                          # 新审计里 A 直接消失
        self.assertEqual(rep["fixed_issues"], [])
        self.assertEqual(rep["disappeared_or_refused"],
                         [{"url": A, "reason": "disappeared", "held_issues": 1}])

    def test_audited_url_still_counts_fixed(self):
        """URL 在场且未拒审、旧 issue 未复现 → 仍算修复(回归守卫)。"""
        rep, _ = diff({A: [("WARN", "sitemap", "/sitemap.xml 不可达"),
                           ("INFO", "bluf", "BLUF 密度不足")]},
                      {A: [("INFO", "bluf", "BLUF 密度不足")]})
        self.assertEqual([(f["url"], f["rule"]) for f in rep["fixed_issues"]],
                         [(A, "sitemap")])
        self.assertEqual(rep["disappeared_or_refused"], [])

    def test_mixed_urls_split_correctly(self):
        rep, _ = diff({A: [("CRITICAL", "robots", "noindex")],
                       B: [("WARN", "title", "18 chars <20")],
                       "https://s.com/c": [("INFO", "sitemap", "/sitemap.xml 不可达")]},
                      {A: [SKIP],                         # 拒审 → held
                       "https://s.com/c": []})            # 在场复检干净 → 修复;B 消失 → held
        self.assertEqual([(f["url"], f["rule"]) for f in rep["fixed_issues"]],
                         [("https://s.com/c", "sitemap")])
        self.assertEqual(rep["disappeared_or_refused"],
                         [{"url": A, "reason": "refused", "held_issues": 1},
                          {"url": B, "reason": "disappeared", "held_issues": 1}])
        self.assertEqual(rep["new_issues"], [])          # 拒审也不产生新增 issue

    def test_multiple_held_issues_counted_per_url(self):
        rep, _ = diff({A: [("CRITICAL", "robots", "noindex"),
                           ("WARN", "og", "og:title 缺失")]},
                      {A: [SKIP]})
        self.assertEqual(rep["fixed_issues"], [])
        self.assertEqual(rep["disappeared_or_refused"],
                         [{"url": A, "reason": "refused", "held_issues": 2}])

    def test_markdown_lists_disappeared_or_refused_section(self):
        po = tmp_file(json.dumps(make_audit({A: [("CRITICAL", "robots", "noindex")]}),
                                 ensure_ascii=False))
        pn = tmp_file(json.dumps(make_audit({A: [SKIP]}), ensure_ascii=False))
        r = run_script("audit_compare.py", ["--old", po, "--new", pn])
        os.unlink(po)
        os.unlink(pn)
        self.assertEqual(r.returncode, 0)
        self.assertIn("已修复 issue(0)", r.stdout)       # 不再被拒审 URL 污染成 1
        self.assertIn("无法判定(拒审/消失 URL,1)", r.stdout)
        self.assertIn("refused", r.stdout)
        self.assertIn("拒审≠修复", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
