#!/usr/bin/env python3
"""pseo_cohort.py golden 用例(stdlib unittest,合成多周 GSC CSV,零网络)。
规格=pipeline-completeness.md R3-3 + programmatic-seo-playbook §八(cohort 测量/
预注册判读/90 天淘汰阶梯)。覆盖:init 冻结(默认标准写死/重复建单拒绝/--criteria
仅 init 时可给且三键校验)/ingest 聚合边界(尾斜杠+大小写归一匹配、同 URL 多行
曝光加权位次、cohort 外行忽略、同周重喂覆盖、默认周=当前 ISO 周周一)/判读三态
(NOT_DUE 未到期/PASS/FAIL,索引率 0.6 边界含)/90 天 prune(未到期阶梯提示、
三选一 301 同轴目标选择、无同轴页回落 noindex、NO-GO 红线=外链+展示史、
--as-remediation 工单可被 remediation.py list --file 消费、窗口内无快照拒绝)/
多 cohort summary/帮助与用法错。时间全部用 --week/--as-of 显式锚定或相对今天
偏移,不依赖真实日历。
独立可运行:python3 tests/test_pseo_cohort.py;也被 run_tests.py 自动发现。"""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
TODAY = date.today()
UTC_TODAY = datetime.now(timezone.utc).date()   # 脚本口径统一 UTC(与本地可能差一天)


def run_script(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "pseo_cohort.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def monday_iso(s):
    d = date.fromisoformat(s)
    return (d - timedelta(days=d.weekday())).isoformat()


# cohort 夹具:两个 slack 目录页(同轴)+ notion 目录页(同首段)+ 两个零展示页
PURLS = [
    "https://example.com/apps/slack/integrations/trello",
    "https://example.com/apps/slack/integrations/asana",
    "https://example.com/apps/notion/integrations/trello",
    "https://example.com/apps/slack/integrations/zoom",
    "https://example.com/glossary/webhook",
]
UT = "https://example.com/apps/slack/integrations/trello"
UA = "https://example.com/apps/slack/integrations/asana"
UN = "https://example.com/apps/notion/integrations/trello"
UZ = "https://example.com/apps/slack/integrations/zoom"
UG = "https://example.com/glossary/webhook"
W1, W2, W3 = "2026-07-06", "2026-07-13", "2026-07-20"   # 已是周一;测试仍按 monday 归一断言


class CohortBase(unittest.TestCase):
    """tmp 目录 + --state 锚定(不污染 cwd;R0-7 状态落工作区)。"""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="pseo-cohort-test-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.state = os.path.join(self.dir, "pseo_cohorts.json")

    def wfile(self, name, content):
        p = os.path.join(self.dir, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return p

    def urls_file(self, urls=None):
        return self.wfile("urls.txt", "\n".join(urls if urls is not None else PURLS) + "\n")

    def gsc_csv(self, rows, name="gsc.csv", header=("Top pages", "Clicks", "Impressions", "Position")):
        """合成 GSC 页面导出:'Top pages' 列名变体 + CTR 列;utf-8-sig BOM 容错。"""
        p = os.path.join(self.dir, name)
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(list(header[:3]) + ["CTR"] + list(header[3:]))
            for r in rows:
                w.writerow(list(r[:3]) + ["3.0%"] + list(r[3:]))
        return p

    def init(self, cohort="batch-a", urls=None, criteria=None, expected=None, extra=()):
        args = ["init", "--cohort_id", cohort, "--template-version", "v1",
                "--urls", self.urls_file(urls), "--state", self.state, *extra]
        if criteria:
            args += ["--criteria", criteria]
        if expected is not None:
            args += ["--expected", str(expected)]
        return run_script(args)

    def ingest(self, cohort, path, week=None):
        args = ["ingest", "--cohort", cohort, "--gsc", path, "--state", self.state]
        if week:
            args += ["--week", week]
        return run_script(args)

    def state_json(self):
        with open(self.state, encoding="utf-8") as f:
            return json.load(f)


class InitTests(CohortBase):
    """init:预注册标准写死入档并冻结(防事后移动球门)。"""

    def test_init_registers_default_frozen_criteria(self):
        r = self.init()
        self.assertEqual(r.returncode, 0, r.stderr)
        c = self.state_json()["cohorts"][0]
        self.assertEqual(c["cohort_id"], "batch-a")
        self.assertEqual(c["template_version"], "v1")
        self.assertEqual(c["criteria"], {"weeks": 8, "min_index_rate": 0.6, "consec_pos_wow": 2})
        self.assertEqual(c["criteria_source"], "default")
        self.assertTrue(c["criteria_frozen"])
        self.assertEqual(c["expected"], len(PURLS))       # 缺省 expected=清单条数
        self.assertIn("冻结", r.stdout)

    def test_init_expected_override_and_contradiction(self):
        self.assertEqual(self.init(expected=500).returncode, 0)
        self.assertEqual(self.state_json()["cohorts"][0]["expected"], 500)
        self.assertEqual(self.init(cohort="bad", expected=2).returncode, 2)   # < URL 数=口径矛盾

    def test_init_duplicate_cohort_rejected(self):
        self.assertEqual(self.init().returncode, 0)
        r = self.init()
        self.assertEqual(r.returncode, 2)
        self.assertIn("冻结", r.stderr)                    # 同 id 重建=移动球门入口,拒绝

    def test_init_criteria_override_stored_and_frozen(self):
        crit = '{"weeks": 3, "min_index_rate": 0.5, "consec_pos_wow": 1}'
        self.assertEqual(self.init(criteria=crit).returncode, 0)
        c = self.state_json()["cohorts"][0]
        self.assertEqual(c["criteria"], {"weeks": 3, "min_index_rate": 0.5, "consec_pos_wow": 1})
        self.assertEqual(c["criteria_source"], "override")

    def test_init_criteria_validation(self):
        for bad in ('{"bogus": 1}', "not json", '{"weeks": "x"}', '{"min_index_rate": 1.5}',
                    '{"consec_pos_wow": 0}', '{"weeks": 0}'):
            r = self.init(criteria=bad)
            self.assertEqual(r.returncode, 2, bad)
        r = self.init(criteria='{"weeks": 2}')
        self.assertEqual(r.returncode, 0)                  # 部分覆盖=其余用默认
        self.assertEqual(self.state_json()["cohorts"][0]["criteria"]["min_index_rate"], 0.6)

    def test_init_urls_cleanup(self):
        content = "# 注释行\n" + UT + "\n\n" + UA + "\n" + UT + "/\n"
        p = self.wfile("urls2.txt", content)
        r = run_script(["init", "--cohort_id", "c2", "--template-version", "v1",
                        "--urls", p, "--state", self.state, "--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(out["urls"], 2)                   # 尾斜杠变体=重复,去重
        self.assertEqual(out["duplicates_dropped"], 1)
        self.assertEqual(run_script(["init", "--cohort_id", "c3", "--template-version", "v1",
                                     "--urls", "/nonexistent/urls.txt", "--state", self.state]).returncode, 2)


class IngestTests(CohortBase):
    """ingest:按 URL∈cohort 聚合;索引代理口径=当周有曝光 [est]。"""

    def test_ingest_aggregation_and_url_normalization(self):
        self.init()
        rows = [
            (UT + "/", 1, 10, 12),                         # 尾斜杠变体仍匹配
            ("HTTPS://Example.com" + UT[len("https://example.com"):], 2, 30, 18),  # 大小写容错
            (UA, 0, 5, 7),
            ("https://example.com/other/page", 9, 100, 1),  # cohort 外行忽略
        ]
        r = self.ingest("batch-a", self.gsc_csv(rows), W1)
        self.assertEqual(r.returncode, 0, r.stderr)
        w = self.state_json()["cohorts"][0]["weeks"][0]
        self.assertEqual(w["week"], monday_iso(W1))
        self.assertEqual(w["source_rows"], 4)
        self.assertEqual(w["matched_urls"], 2)
        self.assertEqual(w["pages"][UT]["clicks"], 3)      # 同 URL 多行合并
        self.assertEqual(w["pages"][UT]["impressions"], 40)
        self.assertEqual(w["pages"][UT]["position"], 16.5)  # (12*10+18*30)/40 曝光加权
        self.assertEqual(w["pages"][UA]["impressions"], 5)

    def test_ingest_default_week_and_reingest_replaces(self):
        self.init()
        self.assertEqual(self.ingest("batch-a", self.gsc_csv([(UT, 1, 10, 5)])).returncode, 0)
        self.assertEqual(self.state_json()["cohorts"][0]["weeks"][0]["week"],
                         (UTC_TODAY - timedelta(days=UTC_TODAY.weekday())).isoformat())  # 缺省=当前 ISO 周周一(UTC 口径)
        self.ingest("batch-a", self.gsc_csv([(UT, 5, 50, 9)]), W1)
        self.ingest("batch-a", self.gsc_csv([(UT, 2, 20, 9)], name="gsc2.csv"), W1)  # 同周重喂=覆盖
        weeks = self.state_json()["cohorts"][0]["weeks"]
        self.assertEqual(len([w for w in weeks if w["week"] == monday_iso(W1)]), 1)
        self.assertEqual([w for w in weeks if w["week"] == monday_iso(W1)][0]["pages"][UT]["impressions"], 20)

    def test_ingest_errors(self):
        self.init()
        self.assertEqual(self.ingest("nope", self.gsc_csv([(UT, 1, 1, 1)])).returncode, 2)  # cohort 不存在
        bad = self.wfile("bad.csv", "Page,Clicks,Position\n/x,1,2\n")          # 缺 Impressions 列
        self.assertEqual(self.ingest("batch-a", bad, W1).returncode, 2)
        self.assertEqual(self.ingest("batch-a", "/nonexistent/gsc.csv", W1).returncode, 2)
        self.assertEqual(self.ingest("batch-a", self.gsc_csv([(UT, 1, 1, 1)]), "2026-13-99").returncode, 2)


class ReportTests(CohortBase):
    """report:索引率曲线(累计并集)/趋势/预注册判读三态。"""

    CRIT3 = '{"weeks": 3, "min_index_rate": 0.6, "consec_pos_wow": 2}'

    def feed(self, weeks_rows):
        self.init(criteria=self.CRIT3)
        for wk, rows in weeks_rows:
            r = self.ingest("batch-a", self.gsc_csv(rows, name=wk), wk)
            self.assertEqual(r.returncode, 0, r.stderr)

    def report(self, *extra):
        return run_script(["report", "--cohort", "batch-a", "--state", self.state, *extra])

    def test_index_rate_cumulative_union_and_est_marker(self):
        # urlA 第 1 周有曝光、第 2 周缺席:累计口径仍计入(索引爬坡期周数据抖动)
        self.feed([(W1, [(UT, 0, 10, 9)]), (W2, [(UA, 0, 20, 9)])])
        r = self.report("--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        self.assertEqual([s["indexed_cum_est"] for s in rep["series"]], [1, 2])
        self.assertEqual(rep["series"][1]["index_rate_cum_est"], 0.4)     # 2/5
        self.assertEqual(rep["series"][1]["wow_impressions"], 10)
        md = self.report().stdout
        self.assertIn("[est]", md)                                        # 代理口径明示
        self.assertIn("URL Inspection", md)

    def test_judgment_pass_with_index_rate_boundary(self):
        # 3/5=0.6 恰好达阈(≥ 含边界);WoW 连续正 2 次(+40/+40)
        self.feed([(W1, [(UT, 0, 40, 9), (UA, 0, 30, 9)]),
                   (W2, [(UT, 0, 60, 9), (UA, 0, 40, 9), (UN, 0, 10, 9)]),
                   (W3, [(UT, 0, 80, 9), (UA, 0, 50, 9), (UN, 0, 20, 9)])])
        r = self.report("--json")
        self.assertEqual(r.returncode, 0, r.stderr)                       # PASS → 0
        j = json.loads(r.stdout)["judgment"]
        self.assertEqual(j["state"], "PASS")
        self.assertEqual(j["checks"]["index_rate_cum_est"]["value"], 0.6)
        self.assertTrue(j["checks"]["index_rate_cum_est"]["pass"])
        self.assertEqual(j["checks"]["consec_pos_wow"]["value"], 2)
        self.assertIn("判定: PASS", self.report().stdout)

    def test_judgment_fail_exit_1(self):
        self.feed([(W1, [(UT, 0, 40, 9)]), (W2, [(UT, 0, 60, 9), (UA, 0, 5, 9)]),
                   (W3, [(UT, 0, 80, 9)])])                                # 到期但索引率 2/5
        r = self.report("--json")
        self.assertEqual(r.returncode, 1)                                 # FAIL → 1
        j = json.loads(r.stdout)["judgment"]
        self.assertEqual(j["state"], "FAIL")
        self.assertFalse(j["checks"]["index_rate_cum_est"]["pass"])

    def test_judgment_not_due_with_default_8_weeks(self):
        self.init()                                                       # 默认标准:8 周
        for i in range(7):                                                # 只喂 7 周
            wk = (date(2026, 7, 6) + timedelta(weeks=i)).isoformat()
            self.assertEqual(self.ingest("batch-a", self.gsc_csv([(UT, 0, 10 + i, 9)], name=wk), wk).returncode, 0)
        r = self.report("--json")
        self.assertEqual(r.returncode, 0)
        j = json.loads(r.stdout)["judgment"]
        self.assertEqual(j["state"], "NOT_DUE")
        self.assertEqual(j["weeks_evaluated"], 7)
        self.assertEqual(j["weeks_required"], 8)
        self.assertIn("未到期", self.report().stdout)
        self.assertIn("冻结", self.report().stdout)                       # 预注册纪律明示


class PruneTests(CohortBase):
    """prune:90 天零展示 → 三选一工单;NO-GO 红线;--as-remediation。"""

    def setUp(self):
        super().setUp()
        self.as_of = TODAY + timedelta(days=100)                          # cohort 龄 ~100 天
        w = [(self.as_of - timedelta(days=7)).isoformat(),      # 窗口内 3 周
             (self.as_of - timedelta(days=14)).isoformat(),
             (self.as_of - timedelta(days=21)).isoformat()]
        self.win_weeks = w
        self.old_week = (self.as_of - timedelta(days=120)).isoformat()    # 窗口外(展示史判定用)

    def feed(self, extra_weeks=()):
        self.init()
        specs = [(wk, [(UT, 0, 50, 9), (UA, 0, 80, 9), (UN, 0, 10, 9)]) for wk in self.win_weeks]
        specs += list(extra_weeks)
        for wk, rows in specs:
            r = self.ingest("batch-a", self.gsc_csv(rows, name=wk), wk)
            self.assertEqual(r.returncode, 0, r.stderr)

    def prune(self, *extra):
        return run_script(["prune", "--cohort", "batch-a", "--state", self.state,
                           "--as-of", self.as_of.isoformat(), *extra])

    def test_prune_three_choice_301_same_axis_and_noindex_fallback(self):
        self.feed()
        r = self.prune("--json")
        self.assertEqual(r.returncode, 1, r.stderr)                       # 有工单 → 1
        out = json.loads(r.stdout)
        self.assertTrue(out["due_for_disposition"])
        tickets = {t["url"]: t for t in out["tickets"]}
        self.assertEqual(set(tickets), {UZ, UG})                          # 零展示=zoom+glossary
        z = tickets[UZ]
        self.assertEqual(z["recommended"], "301")
        self.assertEqual(z["options"]["301"]["target"], UA)               # 同父目录高展示页(asana 80>trello 50)
        self.assertEqual(z["no_go"], [])
        g = tickets[UG]
        self.assertEqual(g["recommended"], "noindex")                     # 无同轴健康页(glossary 轴全灭)
        self.assertIsNone(g["options"]["301"])
        for t in (z, g):                                                  # 三选一齐全
            self.assertEqual(set(t["options"]), {"301", "noindex", "410"})

    def test_prune_nogo_backlinks_redline(self):
        self.feed()
        bl = self.wfile("bl.csv", "url,backlinks\n%s,3\n%s,0\n" % (UZ, UG))
        r = self.prune("--backlinks", bl, "--json")
        self.assertEqual(r.returncode, 1, r.stderr)
        tickets = {t["url"]: t for t in json.loads(r.stdout)["tickets"]}
        self.assertIn("backlinks", ";".join(tickets[UZ]["no_go"]))
        self.assertEqual(tickets[UZ]["recommended"], "review")            # NO-GO → 人审,不自动处置
        self.assertEqual(tickets[UZ]["backlinks"], 3)
        self.assertEqual(tickets[UG]["no_go"], [])                        # 0 条外链不触红线

    def test_prune_nogo_ranking_history(self):
        # glossary 在 90 天窗口外(120 天前)有过展示:窗口内零展示仍列入,但 NO-GO
        self.feed(extra_weeks=[(self.old_week, [(UG, 1, 5, 12)])])
        r = self.prune("--json")
        tickets = {t["url"]: t for t in json.loads(r.stdout)["tickets"]}
        self.assertIn("ranking_history", ";".join(tickets[UG]["no_go"]))
        self.assertEqual(tickets[UG]["recommended"], "review")
        self.assertEqual(tickets[UZ]["recommended"], "301")               # 从未展示的 zoom 不受影响

    def test_prune_young_cohort_ladder_no_tickets(self):
        self.init()
        wk = (UTC_TODAY + timedelta(days=23)).isoformat()
        self.ingest("batch-a", self.gsc_csv([(UT, 0, 30, 9)], name=wk), wk)
        r = run_script(["prune", "--cohort", "batch-a", "--state", self.state,
                        "--as-of", (UTC_TODAY + timedelta(days=30)).isoformat(), "--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertFalse(out["due_for_disposition"])                      # 0-30 天:不动
        self.assertEqual(out["tickets"], [])
        self.assertIn("0-30 天", out["ladder"])
        self.assertGreaterEqual(out["zero_impression_pages"], 1)          # 只列数,不开单

    def test_prune_no_window_snapshot_rejected(self):
        self.init()
        self.ingest("batch-a", self.gsc_csv([(UT, 0, 30, 9)], name="w.csv"), W1)
        far = TODAY + timedelta(days=400)                                 # 快照全落窗口外
        r = run_script(["prune", "--cohort", "batch-a", "--state", self.state,
                        "--as-of", far.isoformat()])
        self.assertEqual(r.returncode, 2)
        self.assertIn("90 天", r.stderr)

    def test_prune_as_remediation_consumable(self):
        self.feed()
        r = self.prune("--as-remediation")
        self.assertEqual(r.returncode, 1, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(set(data), {"items"})
        it = data["items"][0]
        for k in ("id", "rule_id", "area", "action", "phase", "severity",
                  "affected_urls", "status", "created", "deadline"):
            self.assertIn(k, it)
        self.assertTrue(it["id"].startswith("PSEO-"))
        self.assertEqual(it["status"], "proposed")
        self.assertIn("301", data["items"][0]["action"])
        # 可消费性:remediation.py list --file 直接读这份工单
        p = self.wfile("tickets.json", r.stdout)
        rr = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "remediation.py"), "list", "--file", p],
            capture_output=True, text=True, encoding="utf-8",
            env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        self.assertEqual(rr.returncode, 0, rr.stderr)
        self.assertIn("PSEO-001", rr.stdout)


class SummaryTests(CohortBase):
    """summary:多 cohort 汇总。"""

    def test_summary_multiple_cohorts(self):
        self.assertEqual(self.init(cohort="batch-a").returncode, 0)
        self.assertEqual(self.init(cohort="batch-b",
                                   criteria='{"weeks": 2, "min_index_rate": 0.2, "consec_pos_wow": 1}').returncode, 0)
        self.ingest("batch-a", self.gsc_csv([(UT, 1, 10, 9)], name="a1.csv"), W1)
        self.ingest("batch-b", self.gsc_csv([(UT, 2, 20, 9), (UA, 1, 10, 9)], name="b1.csv"), W1)
        self.ingest("batch-b", self.gsc_csv([(UT, 3, 30, 9), (UA, 1, 10, 9)], name="b2.csv"), W2)
        r = run_script(["summary", "--state", self.state, "--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        out = json.loads(r.stdout)
        self.assertEqual(len(out["cohorts"]), 2)
        by = {c["cohort"]: c for c in out["cohorts"]}
        self.assertEqual(by["batch-a"]["judgment"], "NOT_DUE")
        self.assertEqual(by["batch-b"]["judgment"], "PASS")               # 1 周到期:2/5≥0.2,WoW 无需
        self.assertEqual(out["totals"]["cohorts"], 2)
        md = run_script(["summary", "--state", self.state]).stdout
        self.assertIn("batch-a", md)
        self.assertIn("batch-b", md)
        self.assertIn("[est]", md)

    def test_summary_empty_state(self):
        r = run_script(["summary", "--state", os.path.join(self.dir, "none.json")])
        self.assertEqual(r.returncode, 0)
        self.assertIn("无 cohort", r.stdout)


class HelpAndUsageTests(unittest.TestCase):
    def test_help(self):
        r = run_script(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage:", r.stdout)
        self.assertIn("init", r.stdout)
        self.assertIn("prune", r.stdout)
        self.assertIn("预注册", r.stdout)          # 纪律写进帮助
        self.assertIn("[est]", r.stdout)           # 代理口径明示
        for sub in ("init", "ingest", "report", "prune", "summary"):
            self.assertEqual(run_script([sub, "--help"]).returncode, 0, sub)

    def test_usage_errors(self):
        self.assertEqual(run_script([]).returncode, 2)                     # 无子命令
        self.assertEqual(run_script(["bogus"]).returncode, 2)
        self.assertEqual(run_script(["init"]).returncode, 2)               # 缺必填
        self.assertEqual(run_script(["report", "--cohort", "x",
                                     "--state", "/nonexistent/state.json"]).returncode, 2)
        self.assertEqual(run_script(["ingest", "--cohort", "x", "--gsc", "/nonexistent.csv",
                                     "--state", "/nonexistent/state.json"]).returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
