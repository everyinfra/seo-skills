#!/usr/bin/env python3
"""benchmark_report.py 测试: 匿名基准聚合(State of GEO 式,borrow-specs E8)。
standalone(自带 run_script 助手,合成数据,零网络):
  python3 tests/test_benchmark_report.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。

口径(与脚本一致,期望值手工推导钉死):
- 分位数: 线性插值。5 值 [40,50,60,80,90] → P25=50/P50=60/P75=80/均值 64.0。
- audits 主分【Ahrefs 公式】: (无 CRITICAL 的 URL 数÷可评分 URL 数)×100;
  WARN/INFO 不扣主分;verdict=refused/SKIP 不进分母。
- monitor-db 主分: ok/(ok+error)×100;skipped 等缺数据态=N/A 不计分母不罚分;
  --period YYYY-MM 取该月最新 ok run。
- 失败规则频次: audits=CRITICAL+WARN 的 area / monitor-db=critical+warn 告警 code,
  按"命中站数"计数;INFO 不进表。
- 偏差自白原文首尾各一次;输出(stdout/stderr/落盘文件)绝不含输入域名。"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import benchmark_report as br       # noqa: E402  (需先入 SCRIPTS 路径)
import monitor as _monitor          # noqa: E402  (只为复用其 SCHEMA DDL,建库口径不漂移)

# 输入站点标识(刻意用可 grep 的独特域名,匿名化断言逐个扫)
AUDIT_DOMAINS = ["alpha-leak.example.org", "beta-leak.example.org", "gamma-leak.example.org",
                 "delta-leak.example.org", "epsilon-leak.example.org", "refused-leak.example.org",
                 "zeta-leak.example.org"]
CSV_DOMAINS = ["eta-leak.example.net", "theta-leak.example.net"]
DB_SITE = "iota-leak.example.com"


def run_script(*args):
    """独立助手(与 run_tests.py 同形):子进程跑 scripts/benchmark_report.py。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "benchmark_report.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def audit_file(name, url_results):
    """site_audit --json 形状的合成输出;url_results=[(url, verdict, findings, ai_score)]。"""
    crit = sum(1 for _, _, fs, _ in url_results
               for f in fs if f[0] == "CRITICAL")
    return {"schema_version": 1, "audited": len(url_results), "critical": crit,
            "results": {u: {"verdict": v,
                            "findings": [{"severity": s, "area": a, "message": "m"}
                                          for s, a in fs],
                            "meta": {},
                            "ai_search_health": {"score": ai}}
                        for u, v, fs, ai in url_results}}


class _Sandbox(unittest.TestCase):
    """临时目录 + 逐用例清理。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="bm_report_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_audit(self, fname, data):
        path = os.path.join(self.tmp, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return path

    def make_monitor_db(self, fname, runs, alerts=()):
        """runs=[(ts, status, checks_dict)](summary 现场拼,site 字段即匿名化考验);
        alerts=[(run_ts, level, code, suppressed)]。"""
        path = os.path.join(self.tmp, fname)
        conn = sqlite3.connect(path)
        conn.executescript(_monitor.SCHEMA)
        rid_by_ts = {}
        for ts, status, checks in runs:
            summary = json.dumps({"site": "https://" + DB_SITE, "checks": checks},
                                 ensure_ascii=False)
            cur = conn.execute(
                "INSERT INTO runs(ts,kind,status,checks_run,budget_used_sec,summary) "
                "VALUES(?,?,?,?,?,?)", (ts, "daily", status, "daily", 1.0, summary))
            rid_by_ts[ts] = cur.lastrowid
        for run_ts, level, code, supp in alerts:
            conn.execute(
                "INSERT INTO alerts(run_id,ts,level,code,key,message,details,suppressed) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (rid_by_ts[run_ts], run_ts, level, code, "/", "m", "{}", supp))
        conn.commit()
        conn.close()
        return path

    # 常用合成集: 5 个有效 audits 站 + 1 个全拒审站(应被跳过)
    def five_audits(self):
        self.write_audit("a1.json", audit_file("a1", [
            ("https://%s/" % AUDIT_DOMAINS[0], "fail",
             [("CRITICAL", "ai-bots"), ("WARN", "title")], 40.0)]))
        self.write_audit("a2.json", audit_file("a2", [
            ("https://%s/pricing" % AUDIT_DOMAINS[1], "fail",
             [("CRITICAL", "canonical")], 30.0),
            ("https://%s/" % AUDIT_DOMAINS[1], "pass", [], 90.0)]))
        self.write_audit("a3.json", audit_file("a3", [
            ("https://%s/" % AUDIT_DOMAINS[2], "pass",
             [("WARN", "title"), ("INFO", "bluf")], 80.0)]))
        self.write_audit("a4.json", audit_file("a4", [
            ("https://%s/" % AUDIT_DOMAINS[3], "pass", [("WARN", "title")], 60.0)]))
        self.write_audit("a5.json", audit_file("a5", [
            ("https://%s/" % AUDIT_DOMAINS[4], "pass", [], 100.0)]))
        self.write_audit("a6_refused.json", audit_file("a6", [
            ("https://%s/" % AUDIT_DOMAINS[5], "refused",
             [("SKIP", "fetch guard")], 0.0)]))


class QuantileUnitTests(_Sandbox):
    """统计基元:线性插值分位数 / n=1 / ascii_bar 边界。"""

    def test_percentile_linear_interpolation(self):
        vals = [40, 50, 60, 80, 90]                 # 已知五点
        self.assertEqual(br.percentile(vals, 25), 50.0)
        self.assertEqual(br.percentile(vals, 50), 60.0)
        self.assertEqual(br.percentile(vals, 75), 80.0)
        self.assertEqual(br.percentile(vals, 0), 40.0)
        self.assertEqual(br.percentile(vals, 100), 90.0)
        self.assertEqual(br.percentile([3, 1, 2], 50), 2.0)     # 未排序输入自动排序
        self.assertAlmostEqual(br.percentile([0, 10], 25), 2.5)  # 两点插值
        self.assertIsNone(br.percentile([], 50))

    def test_percentile_single_value(self):
        self.assertEqual(br.percentile([77.5], 25), 77.5)       # n=1 三分位同值
        self.assertEqual(br.percentile([77.5], 75), 77.5)

    def test_stats_block_pinned(self):
        b = br.stats_block([40, 50, 60, 80, 90])
        self.assertEqual((b["n"], b["p25"], b["p50"], b["p75"], b["mean"], b["min"], b["max"]),
                         (5, 50.0, 60.0, 80.0, 64.0, 40.0, 90.0))
        self.assertIsNone(br.stats_block([]))

    def test_ascii_bar_bounds(self):
        self.assertEqual(br.ascii_bar(100), "#" * 20)
        self.assertEqual(br.ascii_bar(0), "." * 20)
        self.assertEqual(br.ascii_bar(50), "#" * 10 + "." * 10)
        self.assertEqual(br.ascii_bar(None), "." * 20)
        self.assertEqual(br.ascii_bar(150), "#" * 20)           # 越界截断
        self.assertEqual(br.ascii_bar(-5), "." * 20)
        self.assertTrue(set(br.ascii_bar(62.5)) <= set("#."))   # 纯 ASCII


class ScoresCsvTests(_Sandbox):
    """--scores: 分位数钉死 / 坏行跳过 / 表头缺失 rc=2。"""

    def scores_csv(self, rows, header="site,score,ai_search_health"):
        path = os.path.join(self.tmp, "scores.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + "\n" + "\n".join(rows) + "\n")
        return path

    def test_quantiles_pinned_from_csv(self):
        p = self.scores_csv(["%s,40,30" % CSV_DOMAINS[0], "x-leak.example.net,50,50",
                             "y-leak.example.net,60,70", "z-leak.example.net,80,",
                             "w-leak.example.net,90,95"])
        r = run_script("--scores", p, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        j = json.loads(r.stdout)
        self.assertEqual(j["n_sites"], 5)
        self.assertEqual((j["main"]["p25"], j["main"]["p50"],
                          j["main"]["p75"], j["main"]["mean"]), (50.0, 60.0, 80.0, 64.0))
        self.assertEqual(j["ai_search_health"]["n"], 4)         # 1 行缺 ai 列
        self.assertEqual(j["by_source"]["scores"], 5)

    def test_bad_rows_skipped_and_counted(self):
        p = self.scores_csv(["ok1-leak.example.net,50,40", "bad-leak.example.net,notanum,40",
                             "neg-leak.example.net,-3,40", "big-leak.example.net,300,40",
                             "ok2-leak.example.net,70,40", "ok3-leak.example.net,80,40",
                             "ok4-leak.example.net,90,40", "ok5-leak.example.net,95,40"])
        r = run_script("--scores", p, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        j = json.loads(r.stdout)
        self.assertEqual(j["n_sites"], 5)                       # 3 坏行(非数/越界)被拒
        self.assertEqual(j["skipped"]["bad_rows"], 3)
        self.assertEqual(j["main"]["min"], 50.0)

    def test_missing_header_rejected(self):
        p = self.scores_csv(["only-leak.example.net,50"], header="site,value")
        r = run_script("--scores", p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("需含 site,score 列", r.stderr)


class AuditsTests(_Sandbox):
    """--audits: Ahrefs 主分口径 / Top 失败规则频次 / 拒审站跳过。"""

    def test_main_score_and_top_rules(self):
        self.five_audits()
        r = run_script("--audits", self.tmp, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        j = json.loads(r.stdout)
        # 5 站有效 + 1 全拒审跳过;a1 主分 0(URL 有 CRITICAL)、a2 主分 50(2 URL 1 CRIT)、
        # a3/a4/a5 WARN/INFO 不扣主分 → 100
        self.assertEqual(j["n_sites"], 5)
        self.assertEqual(j["by_source"]["audits"], 5)
        self.assertEqual(j["skipped"]["unparsable"], 1)         # 全拒审文件不进样本
        self.assertEqual((j["main"]["min"], j["main"]["max"]), (0.0, 100.0))
        # Top 失败规则按命中站数: title=3(a1/a3/a4)> ai-bots=canonical=1;INFO(bluf)不进表
        top = j["top_failed_rules"]
        self.assertEqual(top[0], {"rule": "title", "sites": 3, "share": 0.6})
        rules = {t["rule"] for t in top}
        self.assertEqual(rules, {"title", "ai-bots", "canonical"})
        self.assertNotIn("bluf", rules)
        # AI 子分均值: 站级=(40+60+80+100)/5?——a2 站级=(30+90)/2=60 → 值集 [40,60,80,60,100]
        self.assertEqual(j["ai_search_health"]["n"], 5)
        self.assertEqual(j["ai_search_health"]["mean"], 68.0)

    def test_markdown_report_shape(self):
        self.five_audits()
        r = run_script("--audits", self.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("样本数 **5 站**", out)
        self.assertIn("主分: P25", out)
        self.assertIn("AI 子分: P25", out)
        self.assertIn("| title | 3/5 | 60.0% |", out)
        self.assertRegex(out, r"P25\s+[\d.]+ \|" + "#" * 8)     # ASCII 条形在统计行旁


class BiasConfessionTests(_Sandbox):
    """偏差自白原文首尾各一次(照抄 geo-optimizer 纪律,一字不差)。"""

    def test_confession_head_and_tail_in_markdown(self):
        self.five_audits()
        r = run_script("--audits", self.tmp)
        self.assertEqual(r.stdout.count(br.BIAS_CONFESSION), 2)
        head = r.stdout.index(br.BIAS_CONFESSION)
        tail = r.stdout.rindex(br.BIAS_CONFESSION)
        self.assertLess(head, r.stdout.index("## 样本"))         # 首次在报告头
        self.assertGreater(tail, r.stdout.index("## 方法与匿名化"))  # 末次在报告尾

    def test_confession_in_refusal_and_json(self):
        self.write_audit("only.json", audit_file("only", [
            ("https://%s/" % AUDIT_DOMAINS[0], "pass", [], 50.0)]))
        r = run_script("--audits", self.tmp)                     # 1 站 < 5
        self.assertEqual(r.returncode, 2)
        self.assertIn(br.BIAS_CONFESSION, r.stderr)              # 拒绝时也带自白
        self.assertNotIn("匿名基准报告", r.stdout)               # 不出报告本体
        r2 = run_script("--audits", self.tmp, "--min-sites", "1", "--json")
        self.assertEqual(r2.returncode, 0)
        self.assertEqual(json.loads(r2.stdout)["bias_confession"], br.BIAS_CONFESSION)


class MinSitesTests(_Sandbox):
    """样本<5 拒绝出报告(rc=2+说明);--min-sites 门槛可显式调整。"""

    def test_below_default_refused(self):
        p = os.path.join(self.tmp, "s.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write("site,score\nm-leak.example.net,50\nn-leak.example.net,60\n")
        r = run_script("--scores", p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("样本 2 站 < 最小样本阈值 5", r.stderr)
        self.assertIn("拒绝出报告", r.stderr)
        self.assertEqual(r.stdout, "")                           # 绝不输出半截报告

    def test_lowered_threshold_passes(self):
        p = os.path.join(self.tmp, "s.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write("site,score\nm-leak.example.net,50\nn-leak.example.net,60\n")
        r = run_script("--scores", p, "--min-sites", "2", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["n_sites"], 2)


class MonitorDbTests(_Sandbox):
    """--monitor-db: run 分数(ok/error 口径,缺数据不罚分)/ --period 按月过滤 / 告警进失败规则。"""

    def _checks(self, **states):
        return {k: {"state": v} for k, v in states.items()}

    def test_run_score_na_states_not_penalized(self):
        db = self.make_monitor_db("mon.db", [
            ("2026-10-01T08:00:00", "ok",
             self._checks(robots="ok", home="ok", sitemap="ok",
                          gsc="skipped", visibility="blocked"))])
        r = run_script("--monitor-db", db, "--min-sites", "1", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        j = json.loads(r.stdout)
        # ok=3 / error=0(skipped+blocked=N/A 不计分母)→ 100 分
        self.assertEqual(j["main"]["p50"], 100.0)
        self.assertEqual(j["main"]["n"], 1)
        self.assertIsNone(j["ai_search_health"])                # monitor 无 AI 子分

    def test_period_month_filter_and_alert_rules(self):
        # 告警挂在 run 上(run_ts=所属 run 的时间戳);10 月告警全挂 10-05 的 ok run
        db = self.make_monitor_db(
            "mon.db",
            runs=[("2026-09-20T08:00:00", "ok", self._checks(robots="ok", home="error")),
                  ("2026-10-05T08:00:00", "ok", self._checks(robots="ok", home="ok",
                                                             visibility="error")),
                  ("2026-10-20T08:00:00", "failed", self._checks(robots="error"))],
            alerts=[("2026-10-05T08:00:00", "warn", "homepage_down", 0),
                    ("2026-10-05T08:00:00", "critical", "robots_sitewide_block", 0),
                    ("2026-10-05T08:00:00", "warn", "gsc_clicks_drop", 1),   # suppressed 不计
                    ("2026-10-05T08:00:00", "info", "sitemap_urls_grew", 0),  # info 不进失败
                    ("2026-09-20T08:00:00", "warn", "ssl_cert_expiring", 0)])
        # 10 月:取 10-05 ok run(10-20 failed 不算)→ ok=2/error=1 → 66.7
        r = run_script("--monitor-db", db, "--period", "2026-10", "--min-sites", "1", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        j = json.loads(r.stdout)
        self.assertEqual(j["period"], "2026-10")
        self.assertEqual(j["main"]["p50"], 66.7)
        rules = {t["rule"] for t in j["top_failed_rules"]}
        self.assertEqual(rules, {"homepage_down", "robots_sitewide_block"})  # 10 月窗内 crit+warn
        # 9 月:ok=1/error=1 → 50;9 月窗的告警才进表
        r9 = run_script("--monitor-db", db, "--period", "2026-09", "--min-sites", "1", "--json")
        j9 = json.loads(r9.stdout)
        self.assertEqual(j9["main"]["p50"], 50.0)
        self.assertEqual({t["rule"] for t in j9["top_failed_rules"]}, {"ssl_cert_expiring"})
        # 11 月无 run → 拒绝
        r11 = run_script("--monitor-db", db, "--period", "2026-11", "--min-sites", "1")
        self.assertEqual(r11.returncode, 2)
        self.assertIn("无 ok run", r11.stderr)


class AnonymizationTests(_Sandbox):
    """输出绝不含输入标识:域名串不进 stdout/stderr/JSON/落盘文件(匿名化纪律)。"""

    def test_no_domain_leaks_across_all_modes(self):
        self.five_audits()
        csv_path = os.path.join(self.tmp, "scores.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("site,score,ai_search_health\n%s,72.5,55\n%s,88,91.2\n"
                    % tuple(CSV_DOMAINS))
        db = self.make_monitor_db("mon.db", [
            ("2026-10-05T08:00:00", "ok",
             {"robots": {"state": "ok"}, "home": {"state": "ok"}, "gsc": {"state": "skipped"}})])
        md_out = os.path.join(self.tmp, "benchmark-202610.md")
        r = run_script("--audits", self.tmp, "--monitor-db", db, "--scores", csv_path,
                       "--min-sites", "5", "--out", md_out)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(md_out, encoding="utf-8") as f:
            written = f.read()
        rj = run_script("--audits", self.tmp, "--monitor-db", db, "--scores", csv_path,
                        "--min-sites", "5", "--json")
        blob = r.stdout + r.stderr + written + rj.stdout
        for dom in AUDIT_DOMAINS + CSV_DOMAINS + [DB_SITE, "example.org", "example.net",
                                                  "example.com", "http"]:
            self.assertNotIn(dom, blob, "标识泄漏: %s" % dom)
        # 组合来源计数正确(audits 5 + db 1 + csv 2 = 8 站)
        j = json.loads(rj.stdout)
        self.assertEqual(j["n_sites"], 8)
        self.assertEqual((j["by_source"]["audits"], j["by_source"]["monitor_db"],
                          j["by_source"]["scores"]), (5, 1, 2))

    def test_bare_out_autonames_period_file(self):
        from datetime import datetime
        self.five_audits()
        r = run_script("--audits", self.tmp, "--out")           # 裸 --out → 自动文件名
        self.assertEqual(r.returncode, 0, r.stderr)
        month = "benchmark-%s.md" % datetime.now().strftime("%Y%m")
        auto = os.path.join(os.getcwd(), month)                 # 默认落当前目录
        try:
            self.assertTrue(os.path.exists(auto), auto)
            with open(auto, encoding="utf-8") as f:
                body = f.read()
            self.assertEqual(body.count(br.BIAS_CONFESSION), 2)
            self.assertNotIn("example.org", body)
        finally:
            if os.path.exists(auto):
                os.unlink(auto)


class CliContractTests(_Sandbox):
    """--help / 无输入 rc=2 / 坏 --period / --json×--out 互斥 / JSON 顶层形状。"""

    def test_help(self):
        r = run_script("--help")
        self.assertEqual(r.returncode, 0)
        self.assertIn("benchmark_report.py", r.stdout)
        self.assertIn("匿名基准聚合", r.stdout)
        self.assertIn("--min-sites", r.stdout)

    def test_no_input_rejected(self):
        r = run_script()
        self.assertEqual(r.returncode, 2)
        self.assertIn("需至少一种输入", r.stderr)

    def test_bad_period_rejected(self):
        p = os.path.join(self.tmp, "s.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write("site,score\nq-leak.example.net,50\n")
        for bad in ("2026-13", "202610", "26-10"):
            r = run_script("--scores", p, "--period", bad, "--min-sites", "1")
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("--period 需为 YYYY-MM", r.stderr)

    def test_json_and_out_mutex(self):
        p = os.path.join(self.tmp, "s.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write("site,score\nq-leak.example.net,50\n")
        r = run_script("--scores", p, "--min-sites", "1", "--json", "--out", "x.md")
        self.assertEqual(r.returncode, 2)
        self.assertIn("互斥", r.stderr)

    def test_json_shape(self):
        self.five_audits()
        r = run_script("--audits", self.tmp, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        j = json.loads(r.stdout)
        for key in ("schema_version", "generated", "period", "min_sites", "n_sites",
                    "by_source", "skipped", "main", "ai_search_health",
                    "top_failed_rules", "bias_confession"):
            self.assertIn(key, j)
        self.assertEqual(j["schema_version"], br.SCHEMA_VERSION)
        self.assertEqual(j["min_sites"], br.DEFAULT_MIN_SITES)
        for key in ("n", "min", "max", "p25", "p50", "p75", "mean"):
            self.assertIn(key, j["main"])
        for t in j["top_failed_rules"]:
            self.assertEqual(set(t), {"rule", "sites", "share"})
            self.assertIsInstance(t["sites"], int)
        self.assertEqual(j["by_source"].keys(), {"audits", "monitor_db", "scores"})
        # JSON 模式不得把 markdown 表格混进 stdout
        self.assertNotIn("匿名基准报告", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
