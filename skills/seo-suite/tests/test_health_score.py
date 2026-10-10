#!/usr/bin/env python3
"""health_score.py 回归(stdlib unittest,合成数据,零网络,standalone——
助手照抄 run_tests.py 顶部,不 import run_tests,被其 test_*.py 自动发现加载)。
口径钉死 references/research/borrow-specs.md A1:
主分(Ahrefs)=(无 CRITICAL URL÷总 URL)×100,分档 0-30/31-70/71-90/91-100;
类树(Lumar)每类 100 起步仅负号扣分,无数据源类 N/A(data_source_missing)不计入合成分;
--ignore 不进分(Ahrefs);--severity 降级后退出主分扣分项。"""
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


def score(by_url, *extra, metas=None):
    """跑 --json 并解析;返回 (report_dict, returncode)。"""
    p = tmp_file(make_audit(by_url, metas))
    r = run_script("health_score.py", ["--input", p, "--json", *extra])
    os.unlink(p)
    return json.loads(r.stdout), r.returncode


class HealthScoreMainTests(unittest.TestCase):
    """主分公式 / 仅 CRITICAL 扣分 / 拒审 URL 不进分母"""

    def test_main_score_formula(self):
        rep, rc = score({
            "https://s.com/a": [],
            "https://s.com/b": [("CRITICAL", "robots", "noindex")],
            "https://s.com/c": []})
        self.assertEqual(rep["main_score"], 66.7)        # 2/3×100,四舍五入 1 位
        self.assertEqual(rep["band"], "Fair")
        self.assertEqual((rep["urls_total"], rep["urls_clean"]), (3, 2))
        self.assertEqual(rc, 0)

    def test_only_critical_deducts_main_score(self):
        rep, _ = score({
            "https://s.com/a": [("WARN", "title", "18 chars <20")],
            "https://s.com/b": [("WARN", "og", "og:title 缺失"),
                                ("INFO", "sitemap", "/sitemap.xml 不可达")]})
        self.assertEqual(rep["main_score"], 100.0)       # WARN/INFO 完全不扣主分(Ahrefs)
        self.assertEqual(rep["band"], "Excellent")
        self.assertEqual(rep["warn_score"], 0.0)         # 两个 URL 都带 WARN → 子分 0
        self.assertEqual(rep["info_score"], 50.0)        # 仅 /b 带 INFO → 1/2

    def test_refused_url_excluded_from_denominator(self):
        rep, _ = score({
            "https://s.com/a": [],
            "https://s.com/b": [("SKIP", "fetch guard", "refusing to audit")]})
        self.assertEqual(rep["urls_total"], 1)           # 拒审 URL 不进分母
        self.assertEqual(rep["urls_refused"], 1)
        self.assertEqual(rep["main_score"], 100.0)

    def test_unmapped_area_still_deducts_main_and_is_listed(self):
        # Ahrefs 主分公式按严重度与规则无关:site_audit 未来新增 area 未跟进 MAPPING 时,
        # CRITICAL 仍必须扣主分,且显式列在 unmapped 防"掉分看不到原因"
        rep, _ = score({"https://s.com/a": [("CRITICAL", "future-rule", "x")]})
        self.assertEqual(rep["main_score"], 0.0)
        self.assertEqual(rep["unmapped"],
                         [{"area": "future-rule", "severity": "CRITICAL", "hit_urls": 1}])

    def test_s3_areas_mapped_to_page_content(self):
        # site_audit S3 扩展(2026-10-10)的 rendering/semantic-html/bluf/freshness 已进 MAPPING
        rep, _ = score({"https://s.com/a": [("WARN", "rendering", "CSR 疑似"),
                                            ("INFO", "bluf", "BLUF 密度不足")]})
        r = next(i for i in rep["impacts"] if i["rule"] == "rendering")
        self.assertEqual((r["category"], r["subgroup"]), ("rankability", "page_content"))
        self.assertEqual(rep["unmapped"], [])


class HealthScoreBandTests(unittest.TestCase):
    """分档映射【Ahrefs 官方】:0-30 Weak / 31-70 Fair / 71-90 Good / 91-100 Excellent"""

    def test_band_thresholds(self):
        crit = [("CRITICAL", "robots", "noindex")]
        cases = [  # (CRITICAL URL 数, 总 URL 数) → 期望档
            (0, 1, "Excellent"),   # 100
            (1, 10, "Good"),       # 90 → 上边界含 90
            (2, 10, "Good"),       # 80
            (3, 10, "Fair"),       # 70
            (5, 10, "Fair"),       # 50
            (7, 10, "Weak"),       # 30 → 下边界含 30
            (1, 1, "Weak"),        # 0
        ]
        for n_crit, total, want in cases:
            by_url = {f"https://s.com/{i}": (crit if i < n_crit else []) for i in range(total)}
            rep, rc = score(by_url)
            self.assertEqual(rep["band"], want, "CRITICAL=%d/%d" % (n_crit, total))
            self.assertEqual(rc, 1 if want == "Weak" else 0, "Weak 档退出码 1")


class HealthScoreCategoryTests(unittest.TestCase):
    """Lumar 六类:N/A(data_source_missing)不计入合成分 / 派生 duplicate_title"""

    def test_na_category_null_and_excluded_from_composite(self):
        rep, _ = score({"https://s.com/a": [("CRITICAL", "fetch", "HTTP Error 404")],
                        "https://s.com/b": []})
        exp = rep["category_scores"]["experience"]
        self.assertIsNone(exp["score"])                  # site_audit 无速度/安全/外链数据源
        self.assertEqual(exp["reason"], "data_source_missing")
        # 合成分只由 score!=null 的类加权:Σ(类分×类权重)÷Σ类权重(类权重=负号检查权重和)
        num = den = 0.0
        for v in rep["category_scores"].values():
            if v["score"] is not None:
                num += v["score"] * v["weight"]
                den += v["weight"]
        self.assertAlmostEqual(rep["composite_score"], round(num / den, 1), delta=0.11)
        # availability:fetch CRITICAL 命中 1/2 → 100-(1/2)×3=98.5
        self.assertEqual(rep["category_scores"]["availability"]["score"], 98.5)

    def test_duplicate_title_derived_from_batch_meta(self):
        rep, _ = score(
            {"https://s.com/a": [], "https://s.com/b": [], "https://s.com/c": []},
            metas={"https://s.com/a": {"title": "同一标题"},
                   "https://s.com/b": {"title": "同一标题"},
                   "https://s.com/c": {"title": "独一标题"}})
        dup = next(i for i in rep["impacts"] if i["rule"] == "duplicate_title")
        self.assertEqual(dup["hit_urls"], 2)             # 同 title 的 2 个 URL 各记命中
        self.assertEqual(dup["severity"], "WARN")
        self.assertEqual(dup["action"], "立即处理")
        # uniqueness:扣 (2/3)×1 → 99.3
        self.assertEqual(rep["category_scores"]["uniqueness"]["score"], 99.3)


class HealthScoreOverrideTests(unittest.TestCase):
    """--ignore 抬分(Ahrefs 官方:不进 findings 不进分)/ --severity 降级退出主分扣分 /
    --config 持久化(enabled:false=忽略,severity=降级)"""

    BASE_URLS = {
        "https://s.com/a": [],
        "https://s.com/b": [("CRITICAL", "robots", "noindex"), ("WARN", "canonical", "缺失")],
        "https://s.com/c": [],
    }

    def test_ignore_raises_score_and_lists_rule(self):
        rep, _ = score(self.BASE_URLS, "--ignore", "robots")
        self.assertEqual(rep["main_score"], 100.0)       # 唯一 CRITICAL 被忽略 → 抬到 100
        self.assertEqual(rep["ignored"], ["robots"])
        self.assertNotIn("robots", [i["rule"] for i in rep["impacts"]])  # 不进任何计分

    def test_severity_downgrade_exits_main_deduction(self):
        rep, _ = score(self.BASE_URLS, "--severity", "robots=warn")
        self.assertEqual(rep["main_score"], 100.0)       # 降级后不再是 CRITICAL → 退出主分扣分
        self.assertEqual(rep["band"], "Excellent")
        rob = next(i for i in rep["impacts"] if i["rule"] == "robots")
        self.assertEqual(rob["severity"], "WARN")        # impact/类权重按降级后档位计
        self.assertEqual(rep["warn_score"], 66.7)        # /b 落入 WARN 档(1/3 URL 带 WARN)

    def test_config_file_persists_rules(self):
        cfg = tmp_file(json.dumps({"rules": {
            "robots": {"enabled": False},                # 等价 --ignore robots
            "canonical": {"severity": "warn"}}}))       # 等价 --severity canonical=warn
        p = tmp_file(make_audit(self.BASE_URLS))
        r = run_script("health_score.py", ["--input", p, "--json", "--config", cfg])
        os.unlink(cfg)
        os.unlink(p)
        rep = json.loads(r.stdout)
        self.assertEqual(rep["ignored"], ["robots"])
        self.assertEqual(rep["main_score"], 100.0)
        can = next(i for i in rep["impacts"] if i["rule"] == "canonical")
        self.assertEqual(can["severity"], "WARN")


class HealthScoreCliTests(unittest.TestCase):
    """--help / 未知规则退出码 2 / coverage_note 恒在"""

    def test_help(self):
        r = run_script("health_score.py", ["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage: health_score.py", r.stdout)
        self.assertIn("--input", r.stdout)

    def test_unknown_rule_rejected(self):
        p = tmp_file(make_audit({"https://s.com/a": []}))
        r = run_script("health_score.py", ["--input", p, "--ignore", "nope"])
        os.unlink(p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知规则", r.stderr)

    def test_coverage_note_always_present(self):
        rep, _ = score({"https://s.com/a": []})
        self.assertEqual(rep["coverage_note"], "基于样本,分数不可与全站直接比较")
        self.assertEqual(rep["schema_version"], "1.0")


if __name__ == "__main__":
    unittest.main(verbosity=1)
