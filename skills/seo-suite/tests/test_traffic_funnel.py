#!/usr/bin/env python3
"""traffic_funnel.py golden 用例(stdlib unittest,合成数据,零网络)。
Lumar 六阶段判定口径钉死 references/research/borrow-specs.md A1:
阶段过滤正确性 / 无 GSC 截断声明 / Simhash 聚类+DeepRank primary /
drop_rate·cumulative 数学 / markdown 漏斗渲染(█ 条形+前 20 流失清单)/
--urls 可达性抽测(fetch 打桩)+ SSRF 拒内网 / Ryte coverage 声明。
独立可运行:python3 tests/test_traffic_funnel.py;也被 run_tests.py 自动发现。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)


def run_script(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "traffic_funnel.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_file(content, suffix=".csv"):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def page(verdict="pass", findings=None, meta=None, **kw):
    entry = {"verdict": verdict, "findings": findings or [], "meta": meta or {}}
    entry.update(kw)
    return entry


def full_audit():
    """11 页合成站:1 不可达 / 1 noindex / 3 页重复组 / 1 零曝光 / 1 零点击 /
    1 CWV 超阈 / 1 缺 CWV / 1 阈值边界通过 / 首页全程通过。"""
    return {
        "https://example.com/": page(meta={"title": "Example Site Home",
                                           "description": "Welcome to the Example Site home page with widgets and gadgets"}),
        "https://example.com/gone": page(
            verdict="fail",
            findings=[{"severity": "CRITICAL", "area": "fetch", "message": "HTTP Error 404: Not Found"}]),
        "https://example.com/noindex": page(
            findings=[{"severity": "CRITICAL", "area": "robots", "message": "noindex"}]),
        # 三页 Simhash 汉明距离 0(dup-c 仅标点差异,token 化后同指纹)
        "https://example.com/dup-a": page(meta={"title": "Blue Widgets Buying Guide",
                                                "description": "How to choose blue widgets for your home office and team needs"}),
        "https://example.com/dup-b": page(meta={"title": "Blue Widgets Buying Guide",
                                                "description": "How to choose blue widgets for your home office and team needs"}),
        "https://example.com/dup-c": page(meta={"title": "Blue Widgets Buying Guide",
                                                "description": "How to choose blue widgets for your home, office and team needs."}),
        "https://example.com/serp0": page(meta={"title": "Red Widgets Review",
                                                "description": "Independent review of the red widgets lineup this year"}),
        "https://example.com/click0": page(meta={"title": "Green Widgets FAQ",
                                                 "description": "Frequently asked questions about green widgets answered"}),
        "https://example.com/slow": page(meta={"title": "Widget Pricing Explained",
                                               "description": "A clear breakdown of widget pricing tiers and discounts"}),
        "https://example.com/good": page(meta={"title": "Widget Care Instructions",
                                               "description": "How to clean and maintain your widgets safely every week"}),
        "https://example.com/nocwv": page(meta={"title": "Widget History Archive",
                                                "description": "The complete history of widgets from 1900 to today"}),
    }


GSC_CSV = ("Page,Clicks,Impressions,CTR,Position\n"
           "https://example.com/,10,500,2%,5.1\n"
           "https://example.com/dup-a,8,200,4%,7.2\n"
           "https://example.com/click0,0,50,0%,12.0\n"
           "https://example.com/serp0,0,0,0%,0.0\n"
           "https://example.com/slow,5,100,5%,8.0\n"
           "https://example.com/good,5,100,5%,9.0\n"
           "https://example.com/nocwv,5,100,5%,6.0\n")

CWV_CSV = ("URL,LCP,CLS,DCL\n"
           "https://example.com/,1.2,0.01,0.9\n"
           "https://example.com/dup-a,1.8,0.05,1.2\n"
           "https://example.com/slow,3.9,0.05,1.0\n"
           "https://example.com/good,2.5,0.1,1.5\n")   # 阈值边界:LCP=2.5/CLS=0.1/DCL=1.5 均 ≤ 通过

# (stage, pages_in, pages_through, dropped, drop_rate, cumulative_rate)
EXPECTED_STAGES = [
    ("availability",   11, 10, 1, 0.0909, 0.9091),
    ("indexability",   10,  9, 1, 0.1,    0.8182),
    ("uniqueness",      9,  7, 2, 0.2222, 0.6364),
    ("in_serps",        7,  6, 1, 0.1429, 0.5455),
    ("with_clicks",     6,  5, 1, 0.1667, 0.4545),
    ("good_ux",         4,  3, 1, 0.25,   0.2727),
]


class FunnelStageTests(unittest.TestCase):
    """六阶段嵌套过滤的逐阶段计数(合成 11 页站,三输入齐全)。"""

    @staticmethod
    def run_full(as_json=True):
        a = tmp_file(json.dumps({"audited": 11, "critical": 2, "results": full_audit()}),
                     suffix=".json")
        g = tmp_file(GSC_CSV)
        c = tmp_file(CWV_CSV)
        args = ["--audit", a, "--gsc", g, "--cwv", c] + (["--json"] if as_json else [])
        r = run_script(args)
        for p in (a, g, c):
            os.unlink(p)
        return r

    def test_full_funnel_stage_counts(self):
        r = self.run_full()
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        got = [(s["stage"], s["pages_in"], s["pages_through"], s["dropped"],
                s["drop_rate"], s["cumulative_rate"]) for s in rep["stages"]]
        self.assertEqual(got, EXPECTED_STAGES)
        self.assertEqual((rep["entered"], rep["through"], rep["cumulative_rate"]), (11, 3, 0.2727))
        self.assertIsNone(rep["funnel_truncated_at"])

    def test_dropped_reasons_per_stage(self):
        rep = json.loads(self.run_full().stdout)
        by = {s["stage"]: s for s in rep["stages"]}
        self.assertEqual(by["availability"]["dropped_urls"][0]["url"], "https://example.com/gone")
        self.assertIn("404", by["availability"]["dropped_urls"][0]["reason"])
        self.assertEqual(by["indexability"]["dropped_urls"][0]["url"], "https://example.com/noindex")
        self.assertIn("noindex", by["indexability"]["dropped_urls"][0]["reason"])
        self.assertEqual(by["in_serps"]["dropped_urls"][0]["url"], "https://example.com/serp0")
        self.assertIn("impressions=0", by["in_serps"]["dropped_urls"][0]["reason"])
        self.assertEqual(by["with_clicks"]["dropped_urls"][0]["url"], "https://example.com/click0")
        self.assertIn("clicks=0", by["with_clicks"]["dropped_urls"][0]["reason"])
        self.assertEqual(by["good_ux"]["dropped_urls"][0]["url"], "https://example.com/slow")
        self.assertIn("LCP 3.9>2.5", by["good_ux"]["dropped_urls"][0]["reason"])

    def test_no_gsc_truncates_at_uniqueness(self):
        """无 --gsc:漏斗截断到 uniqueness;in_serps/with_clicks/good_ux=null+截断声明。
        audit 文件混入 site_audit --json 的前置文本行(解析须从行首 '{' 起截取)。"""
        audit = full_audit()
        a = tmp_file("== https://example.com/ ==\n[WARN] content: 词数 120 <200\n\n"
                     + json.dumps({"audited": 11, "critical": 0, "results": audit}, ensure_ascii=False),
                     suffix=".json")
        r = run_script(["--audit", a])
        os.unlink(a)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("漏斗截断于 uniqueness", r.stdout)
        a2 = tmp_file(json.dumps({"audited": 11, "critical": 0, "results": full_audit()}), suffix=".json")
        r2 = run_script(["--audit", a2, "--json"])
        os.unlink(a2)
        rep = json.loads(r2.stdout)
        self.assertEqual(rep["funnel_truncated_at"], "uniqueness")
        names = [s["stage"] for s in rep["stages"]]
        self.assertEqual(names, ["availability", "indexability", "uniqueness",
                                 "in_serps", "with_clicks", "good_ux"])
        for s in rep["stages"][3:]:
            self.assertIsNone(s["pages_in"])
            self.assertIsNone(s["pages_through"])
            self.assertIsNone(s["drop_rate"])
        for s in rep["stages"][:3]:                      # 截断不影响前三阶段
            self.assertIsNotNone(s["pages_in"])
        self.assertEqual(rep["through"], 7)              # uniqueness 后即终点


class SimhashUniquenessTests(unittest.TestCase):
    """Simhash 聚类 + primary 判定(静态 1/depth 平票→URL 序;内链图 DeepRank→最高者)。"""

    def test_simhash_identification(self):
        import traffic_funnel as tf
        a = "How to choose blue widgets for your home office and team needs"
        self.assertEqual(tf.simhash(a), tf.simhash(a))                      # 确定性
        self.assertEqual(tf.hamming(tf.simhash(a),
                                    tf.simhash("How to choose blue widgets, for your home office and team needs.")), 0)
        far = tf.hamming(tf.simhash(a), tf.simhash(
            "Independent review of the red widgets lineup this year"))
        self.assertGreater(far, 3)                                          # 非重复页远离阈值
        groups = tf.cluster_by_simhash({
            "https://x/a": tf.simhash(a), "https://x/b": tf.simhash(a),
            "https://x/c": tf.simhash("Widget History Archive since 1900 today")})
        dup = [g for g in groups if len(g) == 2]
        self.assertEqual(sorted(dup[0]), ["https://x/a", "https://x/b"])

    def test_primary_tie_breaks_by_url_in_full_run(self):
        """无 links 字段→静态 DeepRank=1/depth;重复组三页同为 0.5 → URL 序最小者为 primary。"""
        a = tmp_file(json.dumps({"results": full_audit()}), suffix=".json")
        r = run_script(["--audit", a, "--json"])
        os.unlink(a)
        uniq = [s for s in json.loads(r.stdout)["stages"] if s["stage"] == "uniqueness"][0]
        self.assertEqual({d["url"] for d in uniq["dropped_urls"]},
                         {"https://example.com/dup-b", "https://example.com/dup-c"})
        self.assertIn("primary https://example.com/dup-a=0.5", uniq["dropped_urls"][0]["reason"])

    def test_deeprank_graph_beats_url_order(self):
        """有 links 列表字段→简化 PageRank(20 轮,值=入链之和):/zz 有内链(稳态 1),
        /aa 无入链(0)→ primary=/zz,证明 DeepRank 压过 URL 字典序。"""
        txt = "Duplicate Landing Page Best deals on widgets this season only here"
        audit = {
            "https://example.com/x": page(meta={"title": "Hub Page", "description": "Hub"},
                                          links=["https://example.com/zz"]),
            "https://example.com/zz": page(meta={"title": "Dup", "description": txt},
                                           links=["https://example.com/x"]),
            "https://example.com/aa": page(meta={"title": "Dup", "description": txt}),
        }
        a = tmp_file(json.dumps({"results": audit}), suffix=".json")
        r = run_script(["--audit", a, "--json"])
        os.unlink(a)
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        uniq = [s for s in rep["stages"] if s["stage"] == "uniqueness"][0]
        self.assertEqual([d["url"] for d in uniq["dropped_urls"]], ["https://example.com/aa"])
        self.assertIn("primary https://example.com/zz=1", uniq["dropped_urls"][0]["reason"])

    def test_dropped_url_list_capped_at_20(self):
        audit = {f"https://example.com/p{i:02d}":
                 page(findings=[{"severity": "CRITICAL", "area": "robots", "message": "noindex"}])
                 for i in range(25)}
        audit["https://example.com/"] = page()
        a = tmp_file(json.dumps({"results": audit}), suffix=".json")
        r = run_script(["--audit", a, "--json"])
        os.unlink(a)
        idx = [s for s in json.loads(r.stdout)["stages"] if s["stage"] == "indexability"][0]
        self.assertEqual((idx["dropped"], idx["dropped_total"], len(idx["dropped_urls"])), (25, 25, 20))


class RatesAndRenderingTests(unittest.TestCase):
    """drop_rate/cumulative_rate 数学 + markdown 漏斗渲染(█ 条形按比例、前 20 清单)。"""

    def test_rate_math(self):
        a = tmp_file(json.dumps({"results": full_audit()}), suffix=".json")
        g = tmp_file(GSC_CSV)
        c = tmp_file(CWV_CSV)
        r = run_script(["--audit", a, "--gsc", g, "--cwv", c, "--json"])
        for p in (a, g, c):
            os.unlink(p)
        stages = json.loads(r.stdout)["stages"]
        for s in stages:                                   # drop_rate=dropped/pages_in
            self.assertAlmostEqual(s["drop_rate"], s["dropped"] / s["pages_in"], places=4)
        for s in stages:                                   # cumulative=through/entered(11)
            self.assertAlmostEqual(s["cumulative_rate"], s["pages_through"] / 11, places=4)

    def test_markdown_funnel_bars_and_lists(self):
        a = tmp_file(json.dumps({"results": full_audit()}), suffix=".json")
        g = tmp_file(GSC_CSV)
        c = tmp_file(CWV_CSV)
        r = run_script(["--audit", a, "--gsc", g, "--cwv", c])
        for p in (a, g, c):
            os.unlink(p)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("█", out)                            # 漏斗条形
        self.assertIn("availability", out)
        self.assertIn("good_ux", out)
        self.assertIn("进入 11 页 → 最终通过 3 页", out)
        self.assertIn("前 20", out)                        # 流失清单标头
        self.assertIn("https://example.com/gone", out)     # 流失 URL 在列
        self.assertIn("1 页缺 CWV 数据", out)              # N/A 声明
        lines = [ln for ln in out.splitlines() if "█" in ln]
        self.assertTrue(all(ln.count("█") <= 24 for ln in lines))   # 条宽上限=BAR_WIDTH
        bar_av = max(ln.count("█") for ln in lines if ln.startswith("availability"))
        bar_ux = max(ln.count("█") for ln in lines if ln.startswith("good_ux"))
        self.assertEqual(bar_av, round(24 * 10 / 11))      # 条宽∝累计通过率(10/11)
        self.assertEqual(bar_ux, round(24 * 3 / 11))
        self.assertGreater(bar_av, bar_ux)                 # 漏斗逐级收窄

    def test_good_ux_na_not_counted_and_boundary_pass(self):
        a = tmp_file(json.dumps({"results": full_audit()}), suffix=".json")
        g = tmp_file(GSC_CSV)
        c = tmp_file(CWV_CSV)
        r = run_script(["--audit", a, "--gsc", g, "--cwv", c, "--json"])
        for p in (a, g, c):
            os.unlink(p)
        ux = [s for s in json.loads(r.stdout)["stages"] if s["stage"] == "good_ux"][0]
        dropped_urls = {d["url"] for d in ux["dropped_urls"]}
        self.assertEqual(ux["pages_na"], 1)                # /nocwv 缺 CWV → N/A
        self.assertNotIn("https://example.com/nocwv", dropped_urls)   # N/A 不计入流失
        self.assertNotIn("https://example.com/good", dropped_urls)    # LCP=2.5/CLS=0.1/DCL=1.5 边界通过
        self.assertEqual(ux["pages_in"], 4)                # 只计入有完整 CWV 数据的页


class CoverageAndSampleTests(unittest.TestCase):
    """Ryte coverage 声明 / --urls 可达性抽测(fetch 打桩零网络)/ SSRF 拒内网。"""

    def test_coverage_statement_when_sample_below_site(self):
        audit = {f"https://example.com/p{i}": page() for i in range(5)}
        a = tmp_file(json.dumps({"results": audit}), suffix=".json")
        u = tmp_file("\n".join(f"https://example.com/p{i}" for i in range(20)) + "\n", suffix=".txt")
        r = run_script(["--audit", a, "--urls", u, "--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        cov = json.loads(r.stdout)["coverage"]
        self.assertEqual((cov["sample"], cov["site"], cov["coverage_ratio"]), (5, 20, 0.25))
        self.assertIn("样本分不可与全站分直接比较", cov["note"])
        rm = run_script(["--audit", a, "--urls", u])
        for p in (a, u):
            os.unlink(p)
        self.assertIn("覆盖率声明(Ryte)", rm.stdout)
        self.assertIn("样本分不可与全站分直接比较", rm.stdout)

    def test_urls_sample_mode_with_patched_fetch(self):
        import traffic_funnel as tf
        orig = tf.fetch

        def fake(url, timeout=tf.FETCH_TIMEOUT):
            if "ok" in url:
                return 200, {}, "<html></html>"
            if "found" in url:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            raise OSError("connection refused")

        tf.fetch = fake
        try:
            rep = tf.availability_sample(
                ["https://ok.example.com/", "https://found.example.com/", "https://dead.example.com/"])
        finally:
            tf.fetch = orig
        self.assertEqual((rep["entered"], rep["through"], rep["mode"]), (3, 1, "availability_sample"))
        st = rep["stages"][0]
        self.assertEqual((st["pages_in"], st["pages_through"], st["dropped"]), (3, 1, 2))
        self.assertEqual(st["drop_rate"], round(2 / 3, 4))
        reasons = {d["url"]: d["reason"] for d in st["dropped_urls"]}
        self.assertIn("404", reasons["https://found.example.com/"])
        self.assertIn("connection refused", reasons["https://dead.example.com/"])
        self.assertIn("样本分不可与全站分直接比较", rep["coverage"]["note"])   # Ryte 样本口径声明

    def test_ssrf_guard_rejects_internal_ips(self):
        """IP 字面量本地解析即拒(零网络):环回/私网/链路本地/保留段与非 http(s) scheme。"""
        import traffic_funnel as tf
        for host in ("127.0.0.1", "10.0.0.5", "192.168.1.2", "169.254.169.254", "::1"):
            with self.assertRaises(tf.GuardError):
                tf.ssrf_guard(host)
        with self.assertRaises(tf.GuardError):
            tf.fetch("ftp://example.com/data", timeout=1)   # scheme 先拒,不出网

    def test_help_and_usage_errors(self):
        r = run_script(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage:", r.stdout)
        self.assertIn("availability", r.stdout)
        r2 = run_script([])
        self.assertEqual(r2.returncode, 2)
        r3 = run_script(["--audit"])
        self.assertNotEqual(r3.returncode, 0)               # --audit 缺路径参数


if __name__ == "__main__":
    unittest.main(verbosity=1)
