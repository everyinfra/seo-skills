#!/usr/bin/env python3
"""remediation.py 回归(stdlib unittest,合成 envelope + 两份 site_audit JSON,
零网络,standalone——助手照抄 run_tests.py 顶部,不 import run_tests,被其 test_*.py
自动发现加载)。口径钉死脚本自身契约:
init 生成与幂等(rule_id+phase 去重、同键并单 affected_urls 合并、phase→deadline
now+7d/month+30d/ongoing+90d)/update 状态机(逐级前进、跳级回退同态拒绝、verified
仅 verify 可设、wontfix 任意态可进且强制 note、closed=今天)/verify 自动核销
(rule_id 直接命中 + area+URL 交集兜底、old 有 new 无 → verified+auto、部分命中 →
保持 implemented+partial、新 finding 无工单 → 建议 init 增补+退出码 1、wontfix/
verified 单跳过)/list 表格+超期 [!]+退出码 1/report 计数+SLA(closed≤deadline ÷
总 verified)/--json/--help/输入错退出码 2。时间不打桩:deadline 用 created+Δ 精确
差值断言,超期/SLA 用 2020/2026/2099 宽松窗口构造。"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

A = "https://s.com/a"
B = "https://s.com/b"
C = "https://s.com/c"
Z = "https://s.com/z"
VERIFY_HINT = "该 finding 在新体检中消失即自动核销"


def run_remediation(args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "remediation.py"), *args],
                          cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env)


def finding(rid, sev, urls, reco="修复文案"):
    return {"rule_id": rid, "title": rid, "severity": sev, "description": "desc",
            "recommendation": reco, "affected_urls": urls, "affected": len(urls)}


def phase(name, rules):
    return {"name": name, "items": [{"rule_id": r, "title": r, "severity": "WARN",
                                     "impact": 0.5, "impact_source": "estimated",
                                     "action": a} for r, a in rules]}


def make_envelope(categories, phases):
    return json.dumps({"schema_version": 1, "generated_at": "2026-10-01T00:00:00+00:00",
                       "source_urls": [], "inputs": {"audit": "ok"},
                       "summary": {"top_findings": [], "quick_wins": []},
                       "categories": categories,
                       "action_plan": {"phases": phases}}, ensure_ascii=False)


def make_audit(by_url):
    """合成 site_audit --json 输出:by_url={url:[(sev,area,msg)]}。"""
    results = {}
    for url, fs in by_url.items():
        results[url] = {"verdict": "fail" if any(s == "CRITICAL" for s, _, _ in fs) else "pass",
                        "findings": [{"severity": s, "area": a, "message": m} for s, a, m in fs],
                        "meta": {}}
    return json.dumps({"audited": len(results), "critical": 0, "results": results},
                      ensure_ascii=False)


# 标准三单 envelope:robots(CRITICAL→now)/title(WARN→month)/og(INFO→ongoing)
ENV_TEXT = make_envelope(
    [{"name": "indexability", "findings": [finding("robots", "CRITICAL", [A, B],
                                                   "检查 noindex 是否误设")]},
     {"name": "rankability", "findings": [finding("title", "WARN", [A], "补/改 title"),
                                          finding("og", "INFO", [C], "补 og 标签")]}],
    [phase("立即(本周)", [("robots", "检查 noindex 是否误设")]),
     phase("短期(月内)", [("title", "补/改 title:每页唯一")]),
     phase("持续", [("og", "补 og 标签")])])

OLD_ROBOTS = {A: [("CRITICAL", "robots", "noindex")], B: [("CRITICAL", "robots", "noindex")],
              Z: [("CRITICAL", "robots", "noindex")], C: []}
NEW_CLEAN = {A: [], B: [], C: []}
NEW_PARTIAL = {A: [], B: [("CRITICAL", "robots", "noindex")], C: []}
NEW_WITH_H1 = {A: [("CRITICAL", "robots", "noindex"), ("CRITICAL", "h1", "无 H1")],
               B: [("CRITICAL", "robots", "noindex")], C: []}


def parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def hand_item(i, rule="title", status="proposed", phase="now", sev="WARN",
              created="2020-01-01T00:00:00+00:00", deadline="2020-01-08T00:00:00+00:00",
              closed=None, urls=(A,), **extra):
    d = {"id": i, "rule_id": rule, "area": "rankability", "action": "修", "phase": phase,
         "severity": sev, "affected_urls": list(urls), "status": status, "created": created,
         "deadline": deadline, "closed": closed, "verify_hint": VERIFY_HINT, "note": ""}
    d.update(extra)
    return d


class RemediationCase(unittest.TestCase):
    """公共助手:每用例独立 tmpdir(默认数据文件落在其中),init 出标准三单。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="remediation-test-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def write(self, name, text):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def write_env(self, text=ENV_TEXT):
        return self.write("env.json", text)

    def write_audit_file(self, name, by_url):
        return self.write(name, make_audit(by_url))

    def run_cli(self, *args):
        return run_remediation(list(args), self.tmp)

    def data(self):
        with open(os.path.join(self.tmp, "remediations.json"), encoding="utf-8") as f:
            return json.load(f)["items"]

    def init(self, env_text=ENV_TEXT):
        env = self.write("env.json", env_text)
        return self.run_cli("init", "--envelope", env)

    def write_data(self, items):
        self.write("remediations.json", json.dumps({"items": items}, ensure_ascii=False))


class RemediationCliTests(unittest.TestCase):
    """--help / 无子命令 / 未知子命令"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="remediation-cli-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_help(self):
        r = run_remediation(["--help"], self.tmp)
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage: remediation.py", r.stdout)
        for sub in ("init", "list", "update", "verify", "report"):
            self.assertIn(sub, r.stdout)
        self.assertIn("退出码: 0 正常 / 1", r.stdout)

    def test_no_subcommand_and_unknown(self):
        self.assertEqual(run_remediation([], self.tmp).returncode, 2)
        r = run_remediation(["explode"], self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知子命令", r.stderr)


class RemediationInitTests(RemediationCase):
    """init:生成字段/phase→deadline 映射/幂等/同 rule+phase 并单"""

    def test_creates_tickets_with_fields(self):
        r = self.init()
        self.assertEqual(r.returncode, 0)
        self.assertIn("新建 3 张", r.stdout)
        items = self.data()
        self.assertEqual([it["id"] for it in items], ["REM-001", "REM-002", "REM-003"])
        robots, title, og = items
        self.assertEqual((robots["rule_id"], robots["area"], robots["phase"],
                          robots["severity"], robots["status"]),
                         ("robots", "indexability", "now", "CRITICAL", "proposed"))
        self.assertEqual(robots["affected_urls"], [A, B])
        self.assertEqual(robots["action"], "检查 noindex 是否误设")     # plan item 优先
        self.assertIsNone(robots["closed"])
        self.assertEqual(robots["verify_hint"], VERIFY_HINT)
        self.assertEqual((title["rule_id"], title["phase"], title["severity"],
                          title["action"], title["affected_urls"]),
                         ("title", "month", "WARN", "补/改 title:每页唯一", [A]))
        self.assertEqual((og["rule_id"], og["phase"], og["severity"]),
                         ("og", "ongoing", "INFO"))
        self.assertEqual(og["action"], "补 og 标签")

    def test_phase_to_deadline_mapping(self):
        self.init()
        for it, days in zip(self.data(), (7, 30, 90)):              # now/month/ongoing
            delta = parse_dt(it["deadline"]) - parse_dt(it["created"])
            self.assertEqual(delta.total_seconds(), days * 86400, it["id"])
            self.assertTrue(it["created"].endswith("+00:00"))       # timezone.utc 口径

    def test_idempotent_second_init_skips(self):
        self.assertEqual(self.init().returncode, 0)
        r = self.init()
        self.assertEqual(r.returncode, 0)
        self.assertIn("跳过 3 张已存在", r.stdout)
        self.assertIn("新建 0 张", r.stdout)
        self.assertEqual(len(self.data()), 3)

    def test_same_rule_phase_merged_across_categories(self):
        env = make_envelope(
            [{"name": "rankability", "findings": [finding("title", "WARN", [A])]},
             {"name": "other", "findings": [finding("title", "WARN", [C])]}],
            [phase("短期(月内)", [("title", "补/改 title")])])
        r = self.init(env)
        self.assertEqual(r.returncode, 0)
        items = self.data()
        self.assertEqual(len(items), 1)                              # 同 rule+phase 并单
        self.assertEqual(items[0]["affected_urls"], [A, C])          # urls 合并保序
        self.assertEqual(items[0]["area"], "rankability")            # area 取首见类别

    def test_missing_or_bad_envelope_exit_2(self):
        r = self.run_cli("init")                                     # 缺 --envelope
        self.assertEqual(r.returncode, 2)
        r = self.run_cli("init", "--envelope", os.path.join(self.tmp, "nope.json"))
        self.assertEqual(r.returncode, 2)
        p = self.write("bad.json", '{"categories": 3}')              # 结构不符不静默降级
        r = self.run_cli("init", "--envelope", p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("categories", r.stderr)


class RemediationUpdateTests(RemediationCase):
    """update:状态机 happy path/跳级回退同态拒绝/verified 不可手设/wontfix 强制 note"""

    def setUp(self):
        super().setUp()
        assert self.init().returncode == 0

    def test_happy_path_chain(self):
        r = self.run_cli("update", "REM-002", "--status", "accepted", "--note", "排期确认")
        self.assertEqual(r.returncode, 0)
        self.assertIn("排期确认", next(i for i in self.data() if i["id"] == "REM-002")["note"])
        for st in ("in_progress", "implemented"):
            r = self.run_cli("update", "REM-002", "--status", st)
            self.assertEqual(r.returncode, 0, st)
            self.assertEqual(next(i for i in self.data() if i["id"] == "REM-002")["status"], st)
        it = next(i for i in self.data() if i["id"] == "REM-002")
        self.assertIsNone(it["closed"])                              # 非 wontfix 不关闭

    def test_skip_backward_and_same_transitions_rejected(self):
        for bad in ("in_progress", "implemented"):
            r = self.run_cli("update", "REM-001", "--status", bad)  # proposed 跳级
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("非法状态转换", r.stderr)
        self.run_cli("update", "REM-001", "--status", "accepted")
        r = self.run_cli("update", "REM-001", "--status", "implemented")   # accepted 跳级
        self.assertEqual(r.returncode, 2)
        r = self.run_cli("update", "REM-001", "--status", "accepted")      # 同态
        self.assertEqual(r.returncode, 2)
        r = self.run_cli("update", "REM-001", "--status", "proposed")      # 回退
        self.assertEqual(r.returncode, 2)
        for st in ("accepted", "in_progress", "implemented"):
            self.run_cli("update", "REM-002", "--status", st)
        r = self.run_cli("update", "REM-002", "--status", "in_progress")   # 终点回退
        self.assertEqual(r.returncode, 2)

    def test_verified_and_proposed_targets_rejected(self):
        r = self.run_cli("update", "REM-001", "--status", "verified")
        self.assertEqual(r.returncode, 2)
        self.assertIn("verify", r.stderr)
        r = self.run_cli("update", "REM-001", "--status", "proposed")
        self.assertEqual(r.returncode, 2)

    def test_wontfix_from_any_state_requires_note(self):
        r = self.run_cli("update", "REM-003", "--status", "wontfix")      # 无 note
        self.assertEqual(r.returncode, 2)
        self.assertIn("note", r.stderr)
        r = self.run_cli("update", "REM-003", "--status", "wontfix",
                         "--note", "历史遗留不修")                        # proposed 直达 wontfix
        self.assertEqual(r.returncode, 0)
        it = next(i for i in self.data() if i["id"] == "REM-003")
        self.assertEqual(it["status"], "wontfix")
        self.assertEqual(it["note"], "历史遗留不修")
        closed = parse_dt(it["closed"])
        self.assertEqual(closed.tzinfo.utcoffset(closed), timezone.utc.utcoffset(closed))
        self.assertLess(abs((datetime.now(timezone.utc) - closed).total_seconds()), 600)
        r = self.run_cli("update", "REM-003", "--status", "accepted")     # wontfix 终态
        self.assertEqual(r.returncode, 2)

    def test_unknown_id_and_missing_status(self):
        self.assertEqual(self.run_cli("update", "REM-999", "--status", "accepted").returncode, 2)
        self.assertEqual(self.run_cli("update", "REM-001").returncode, 2)


class RemediationVerifyTests(RemediationCase):
    """verify:全量核销/partial 保持 implemented/增补建议/wontfix·verified 跳过/area 兜底"""

    def setUp(self):
        super().setUp()
        assert self.init().returncode == 0

    def verify(self, old_by, new_by, *extra):
        po = self.write_audit_file("old.json", old_by)
        pn = self.write_audit_file("new.json", new_by)
        return self.run_cli("verify", "--old", po, "--new", pn, *extra)

    def by_id(self, tid):
        return next(i for i in self.data() if i["id"] == tid)

    def test_full_close_sets_verified_and_auto(self):
        r = self.verify(OLD_ROBOTS, NEW_CLEAN)
        self.assertEqual(r.returncode, 0)
        self.assertIn("核销 1 张(REM-001)", r.stdout)
        self.assertIn("无增补建议", r.stdout)
        robots = self.by_id("REM-001")
        self.assertEqual(robots["status"], "verified")
        closed = parse_dt(robots["closed"])                          # closed=今天(±10min)
        self.assertLess(abs((datetime.now(timezone.utc) - closed).total_seconds()), 600)
        self.assertEqual(robots["auto"]["verified_by"], "audit diff")
        self.assertTrue(robots["auto"]["old_audit"].endswith("old.json"))
        self.assertTrue(robots["auto"]["new_audit"].endswith("new.json"))
        # title/og 在 old 审计无发现 → 未动;OLD_ROBOTS 多出的 Z(rule 级命中不限 URL)不碍核销
        self.assertEqual(self.by_id("REM-002")["status"], "proposed")
        self.assertEqual(self.by_id("REM-003")["status"], "proposed")

    def test_partial_keeps_implemented_with_detail(self):
        for st in ("accepted", "in_progress", "implemented"):
            self.run_cli("update", "REM-001", "--status", st)
        r = self.verify(OLD_ROBOTS, NEW_PARTIAL)
        self.assertEqual(r.returncode, 0)
        self.assertIn("部分 1 张(REM-001)", r.stdout)
        robots = self.by_id("REM-001")
        self.assertEqual(robots["status"], "implemented")             # 保持 implemented
        self.assertEqual(robots["auto"]["partial"], [{"url": B, "rule": "robots"}])
        self.assertIsNone(robots["closed"])

    def test_partial_on_proposed_keeps_status(self):
        r = self.verify(OLD_ROBOTS, NEW_PARTIAL)                     # 未推进状态机
        self.assertEqual(r.returncode, 0)
        robots = self.by_id("REM-001")
        self.assertEqual(robots["status"], "proposed")               # 非 implemented 不动状态
        self.assertEqual(robots["auto"]["partial"], [{"url": B, "rule": "robots"}])

    def test_new_findings_without_ticket_suggest_init_exit_1(self):
        po = self.write_audit_file("old.json", OLD_ROBOTS)
        pn = self.write_audit_file("new.json", NEW_WITH_H1)          # h1 为全新规则
        r = self.run_cli("verify", "--old", po, "--new", pn, "--json")
        self.assertEqual(r.returncode, 1)                            # 增补建议 → 退出码 1
        payload = json.loads(r.stdout)
        self.assertEqual(payload["suggested_init"], [{"rule": "h1", "urls": [A]}])
        r2 = self.verify(OLD_ROBOTS, NEW_WITH_H1)                    # 人读输出同信息
        self.assertEqual(r2.returncode, 1)
        self.assertIn("建议 init 增补", r2.stdout)
        self.assertIn("h1", r2.stdout)

    def test_wontfix_ticket_ignored_by_verify(self):
        self.run_cli("update", "REM-001", "--status", "wontfix", "--note", "策略保留")
        r = self.verify(OLD_ROBOTS, NEW_CLEAN)                       # robots 已消失也不核销
        self.assertEqual(r.returncode, 0)
        robots = self.by_id("REM-001")
        self.assertEqual(robots["status"], "wontfix")
        self.assertNotIn("auto", robots)

    def test_area_url_intersection_fallback(self):
        self.write_data([hand_item("REM-001", rule="custom-x", area="rankability",
                                   urls=(A,), deadline="2099-01-01T00:00:00+00:00")])
        po = self.write_audit_file("old.json", {A: [("WARN", "h1", "无 H1")]})
        pn = self.write_audit_file("new.json", {A: []})
        r = self.run_cli("verify", "--old", po, "--new", pn)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.by_id("REM-001")["status"], "verified")  # h1→rankability 兜底命中


class RemediationListTests(RemediationCase):
    """list:表格/超期 [!]/过滤/--json/缺文件退出码 2"""

    def test_table_overdue_marker_and_filters(self):
        self.write_data([
            hand_item("REM-001", status="proposed", deadline="2020-01-08T00:00:00+00:00"),
            hand_item("REM-002", rule="og", status="verified", closed="2026-10-10T00:00:00+00:00",
                      deadline="2026-10-18T00:00:00+00:00")])
        r = self.run_cli("list")
        self.assertEqual(r.returncode, 1)                            # 展示集含超期 → 1
        self.assertIn("REM-001", r.stdout)
        self.assertIn("[!]", r.stdout)
        self.assertIn("REM-002", r.stdout)
        self.assertIn("共 2 张(超期 1)", r.stdout)
        r = self.run_cli("list", "--overdue")                        # 只看超期
        self.assertEqual(r.returncode, 1)
        self.assertIn("REM-001", r.stdout)
        self.assertNotIn("REM-002", r.stdout)
        r = self.run_cli("list", "--status", "verified")             # 已核销不超期 → 0
        self.assertEqual(r.returncode, 0)
        self.assertIn("REM-002", r.stdout)
        self.assertNotIn("REM-001", r.stdout)
        r = self.run_cli("list", "--status", "nope")                 # 非法状态值
        self.assertEqual(r.returncode, 2)

    def test_json_output(self):
        self.write_data([
            hand_item("REM-001", deadline="2020-01-08T00:00:00+00:00"),
            hand_item("REM-002", status="wontfix", note="不修",
                      deadline="2020-01-08T00:00:00+00:00",
                      closed="2026-10-10T00:00:00+00:00")])
        r = self.run_cli("list", "--json")
        self.assertEqual(r.returncode, 1)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["overdue"], 1)                      # wontfix 已关闭不超期
        flags = {it["id"]: it["overdue"] for it in payload["items"]}
        self.assertEqual(flags, {"REM-001": True, "REM-002": False})

    def test_missing_file_and_empty_store(self):
        self.assertEqual(self.run_cli("list").returncode, 2)
        self.write_data([])
        r = self.run_cli("list")
        self.assertEqual(r.returncode, 0)
        self.assertIn("共 0 张", r.stdout)


class RemediationReportTests(RemediationCase):
    """report:计数/SLA 达成率/超期退出码 1/--json"""

    FILE = [
        hand_item("REM-001", status="verified", closed="2026-10-10T00:00:00+00:00",
                  deadline="2026-10-18T00:00:00+00:00"),             # met
        hand_item("REM-002", rule="og", status="verified",
                  closed="2026-12-01T00:00:00+00:00",
                  deadline="2026-10-18T00:00:00+00:00"),             # missed
        hand_item("REM-003", rule="h1", status="wontfix", note="不修",
                  closed="2026-10-09T00:00:00+00:00"),
        hand_item("REM-004", rule="schema", status="in_progress",
                  created="2026-10-01T00:00:00+00:00",
                  deadline="2099-01-01T00:00:00+00:00"),
        hand_item("REM-005", rule="links", status="proposed",
                  deadline="2020-01-08T00:00:00+00:00")]             # 超期

    def test_counts_sla_and_overdue_exit_1(self):
        self.write_data(self.FILE)
        r = self.run_cli("report")
        self.assertEqual(r.returncode, 1)                            # 有超期 → 1
        self.assertIn("# 修复项生命周期报告", r.stdout)
        self.assertIn("未关闭(open): 2", r.stdout)                   # in_progress+proposed
        self.assertIn("超期: 1", r.stdout)
        self.assertIn("verified 2", r.stdout)
        self.assertIn("wontfix: 1", r.stdout)
        self.assertIn("SLA 达成率: 50%", r.stdout)                    # 1/2 met
        self.assertIn("REM-005", r.stdout)                           # 超期清单

    def test_report_json(self):
        self.write_data(self.FILE)
        payload = json.loads(self.run_cli("report", "--json").stdout)
        self.assertEqual(payload["total"], 5)
        self.assertEqual(payload["counts"]["verified"], 2)
        self.assertEqual(payload["counts"]["wontfix"], 1)
        self.assertEqual(payload["open"], 2)
        self.assertEqual(payload["overdue"], ["REM-005"])
        self.assertEqual(payload["sla"], {"met": 1, "total": 2, "rate": 0.5})

    def test_no_overdue_exit_0_and_na_sla(self):
        self.write_data([hand_item("REM-001", status="accepted",
                                   deadline="2099-01-01T00:00:00+00:00")])
        r = self.run_cli("report")
        self.assertEqual(r.returncode, 0)
        self.assertIn("SLA 达成率: N/A", r.stdout)                    # 无 verified → N/A


if __name__ == "__main__":
    unittest.main(verbosity=1)
