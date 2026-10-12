#!/usr/bin/env python3
"""outreach_tracker.py 回归(R4-1;stdlib unittest,合成 citation_gaps --json,零网络,
standalone——助手照抄 test_remediation.py,被 run_tests.py 按 test_*.py 自动发现加载)。
口径钉死脚本自身契约:
add 从 citation_gaps --json 闭环(priority/outreach_tip 原样搬入;域不在 domains → 2;
同域重复 → 2)/update 状态机(candidate→drafted→sent→replied→linked 逐级,跳级/回退/
同态拒绝,refused 仅 replied 可进,linked/refused 终态,--note/--url 落盘,history 留档)/
next_review 按新 status 重设(drafted+14d/sent+7d/replied+3d;candidate 与终态 null)/
due 复查日到期清单(该跟进谁 + 退出码 1 接 notify)/report 转化漏斗(曾到达口径 +
平均回复天数)/--json 全子命令/--help/输入错退出码 2。时间不打桩:复查日用
next_review-created 精确差值断言,到期/漏斗用手写 history 时间戳构造。"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

GAPS_TIP_G2 = "竞品 hubspot.com 在 g2.com 被引用——考虑贡献内容或争取列表位直接竞争"
GAPS_TIP_HS = "AI 模型在 1 个追踪 prompt 引用 hubspot.co.uk,获得收录可提升 AI 可见性"


def run_outreach(args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "outreach_tracker.py"),
                           *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def make_gaps():
    """合成 citation_gaps.py --json 输出(结构照 _dom_row/outreach_tips 契约)。"""
    return json.dumps({
        "schema_version": 1, "tool": "citation_gaps.py", "brand": "Acme",
        "brand_domains": ["acme.ai"],
        "stats": {"runs": 2, "cells": 4, "qualifying": 3, "urls": 3, "domains": 2,
                  "high_priority": 2, "own_cited": 0},
        "domains": [
            {"domain": "g2.com", "count": 3, "pages": ["https://www.g2.com/crm/best"],
             "prompts": ["best crm"], "providers": ["chatgpt"],
             "has_competitor_run": True, "competitors": ["hubspot.com"],
             "priority": "High", "source_class": "UGC"},
            {"domain": "hubspot.co.uk", "count": 1,
             "pages": ["https://blog.hubspot.co.uk/pricing"],
             "prompts": ["crm pricing"], "providers": ["perplexity"],
             "has_competitor_run": False, "competitors": [],
             "priority": "Standard", "source_class": "Corporate"}],
        "outreach_tips": {"g2.com": GAPS_TIP_G2, "hubspot.co.uk": GAPS_TIP_HS}},
        ensure_ascii=False)


def parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def hand_item(i, domain, status="candidate", history=(), **extra):
    d = {"id": i, "domain": domain, "status": status, "priority": "Standard",
         "outreach_tip": "", "source": "manual",
         "created": "2026-10-01T00:00:00+00:00",
         "updated": "2026-10-01T00:00:00+00:00", "next_review": None, "url": None,
         "note": "", "history": list(history)}
    d.update(extra)
    return d


class OutreachCase(unittest.TestCase):
    """公共助手:每用例独立 tmpdir(默认数据文件落在其中)。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="outreach-test-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def run_cli(self, *args):
        return run_outreach(list(args), self.tmp)

    def data(self):
        with open(os.path.join(self.tmp, "outreach.json"), encoding="utf-8") as f:
            return json.load(f)["items"]

    def write_data(self, items):
        with open(os.path.join(self.tmp, "outreach.json"), "w", encoding="utf-8") as f:
            json.dump({"items": items}, f, ensure_ascii=False)

    def add_gaps(self):
        gaps = os.path.join(self.tmp, "gaps.json")
        with open(gaps, "w", encoding="utf-8") as f:
            f.write(make_gaps())
        assert self.run_cli("add", "--domain", "g2.com", "--source", gaps).returncode == 0
        assert self.run_cli("add", "--domain", "hubspot.co.uk", "--source",
                            gaps).returncode == 0
        return gaps


class OutreachCliTests(unittest.TestCase):
    """--help / 无子命令 / 未知子命令"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="outreach-cli-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_help(self):
        r = run_outreach(["--help"], self.tmp)
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage: outreach_tracker.py", r.stdout)
        for sub in ("add", "list", "update", "due", "report"):
            self.assertIn(sub, r.stdout)
        self.assertIn("退出码: 0 正常 / 1", r.stdout)

    def test_no_subcommand_and_unknown(self):
        self.assertEqual(run_outreach([], self.tmp).returncode, 2)
        r = run_outreach(["explode"], self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知子命令", r.stderr)


class OutreachAddTests(OutreachCase):
    """add:gaps 闭环(priority/tip 原样)/手工登记/重复与未命中拒绝"""

    def test_add_from_gaps_json_verbatim(self):
        gaps = self.add_gaps()
        items = self.data()
        self.assertEqual([it["id"] for it in items], ["OUT-001", "OUT-002"])
        g2, hs = items
        self.assertEqual((g2["domain"], g2["priority"], g2["outreach_tip"], g2["status"]),
                         ("g2.com", "High", GAPS_TIP_G2, "candidate"))     # 原样搬入
        self.assertEqual((hs["domain"], hs["priority"], hs["outreach_tip"]),
                         ("hubspot.co.uk", "Standard", GAPS_TIP_HS))
        self.assertEqual(g2["source"], os.path.abspath(gaps))
        self.assertIsNone(g2["next_review"])          # candidate 无复查日
        self.assertEqual(g2["history"], [])
        r = self.run_cli("add", "--domain", "g2.com", "--source", gaps, "--json")
        self.assertEqual(r.returncode, 2)             # 同域重复 → 2(上面已建,改断言前先建)

    def test_add_duplicate_and_unmatched_rejected(self):
        gaps = os.path.join(self.tmp, "gaps.json")
        with open(gaps, "w", encoding="utf-8") as f:
            f.write(make_gaps())
        r = self.run_cli("add", "--domain", "g2.com", "--source", gaps)
        self.assertEqual(r.returncode, 0)
        r = self.run_cli("add", "--domain", "g2.com", "--source", gaps)     # 重复
        self.assertEqual(r.returncode, 2)
        self.assertIn("已在库中", r.stderr)
        r = self.run_cli("add", "--domain", "notlist.ed", "--source", gaps)  # 域不在 gaps
        self.assertEqual(r.returncode, 2)
        self.assertIn("不在", r.stderr)
        r = self.run_cli("add", "--source", gaps)                            # 缺 --domain
        self.assertEqual(r.returncode, 2)
        r = self.run_cli("add", "--domain", "a.com", "--source",
                         os.path.join(self.tmp, "nope.json"))                 # 缺文件
        self.assertEqual(r.returncode, 2)

    def test_add_manual_without_source(self):
        r = self.run_cli("add", "--domain", "ManualBlog.com")                # 大写归一
        self.assertEqual(r.returncode, 0)
        it = self.data()[0]
        self.assertEqual((it["domain"], it["priority"], it["outreach_tip"], it["source"]),
                         ("manualblog.com", "Standard", "", "manual"))


class OutreachUpdateTests(OutreachCase):
    """update:状态机 happy path/复查日重设/跳级回退同态拒绝/终态/note·url"""

    def setUp(self):
        super().setUp()
        assert self.run_cli("add", "--domain", "g2.com").returncode == 0

    def advance(self, tid, *statuses, **kw):
        for st in statuses:
            args = ["update", tid, "--status", st]
            for k, v in kw.items():
                args += ["--" + k, v]
            r = self.run_cli(*args)
            self.assertEqual(r.returncode, 0, st)

    def test_happy_path_review_dates_and_history(self):
        self.advance("OUT-001", "drafted")
        self.advance("OUT-001", "sent", note="首封已发")
        self.advance("OUT-001", "replied")
        self.advance("OUT-001", "linked", url="https://g2.com/best", note="拿到列表位")
        it = self.data()[0]
        self.assertEqual(it["status"], "linked")
        self.assertEqual(it["url"], "https://g2.com/best")               # 产出链接落盘
        self.assertEqual(it["note"], "拿到列表位")
        self.assertEqual([(h["from"], h["to"]) for h in it["history"]],
                         [("candidate", "drafted"), ("drafted", "sent"),
                          ("sent", "replied"), ("replied", "linked")])
        self.assertIn("首封已发", it["history"][1]["note"])               # note 随 history 留档

    def test_review_date_offsets_per_status(self):
        """复查日按新 status 重设:drafted+14d / sent+7d / replied+3d;linked 清空。"""
        for st, days in (("drafted", 14), ("sent", 7), ("replied", 3)):
            self.advance("OUT-001", st)
            it = self.data()[0]
            delta = parse_dt(it["next_review"]) - parse_dt(it["updated"])
            self.assertEqual(delta.total_seconds(), days * 86400, st)
        self.advance("OUT-001", "linked")
        self.assertIsNone(self.data()[0]["next_review"])                 # 终态无复查日

    def test_skip_backward_and_same_rejected(self):
        self.advance("OUT-001", "drafted")
        for bad in ("replied", "linked"):                                # drafted 跳级
            r = self.run_cli("update", "OUT-001", "--status", bad)
            self.assertEqual(r.returncode, 2, bad)
            self.assertIn("非法状态转换", r.stderr)
        r = self.run_cli("update", "OUT-001", "--status", "candidate")   # 回退
        self.assertEqual(r.returncode, 2)
        r = self.run_cli("update", "OUT-001", "--status", "drafted")     # 同态
        self.assertEqual(r.returncode, 2)

    def test_refused_only_from_replied_and_terminal(self):
        for st in ("candidate", "drafted", "sent"):                      # 拒绝=回复的分支
            self.write_data([hand_item("OUT-001", "x.com", status=st)])
            r = self.run_cli("update", "OUT-001", "--status", "refused")
            self.assertEqual(r.returncode, 2, st)
            self.assertIn("refused 仅 replied", r.stderr)
        self.write_data([hand_item("OUT-001", "x.com", status="replied")])
        r = self.run_cli("update", "OUT-001", "--status", "refused", "--note", "对方明确拒绝")
        self.assertEqual(r.returncode, 0)
        it = self.data()[0]
        self.assertEqual((it["status"], it["note"], it["next_review"]),
                         ("refused", "对方明确拒绝", None))
        for nxt in ("linked", "drafted", "refused"):                     # 终态不可再转
            r = self.run_cli("update", "OUT-001", "--status", nxt)
            self.assertEqual(r.returncode, 2, nxt)
            self.assertIn("终态", r.stderr)
        self.write_data([hand_item("OUT-001", "x.com", status="linked")])
        r = self.run_cli("update", "OUT-001", "--status", "refused")
        self.assertEqual(r.returncode, 2)                                # linked 也是终态

    def test_bad_target_and_unknown_id(self):
        self.assertEqual(self.run_cli("update", "OUT-001", "--status", "candidate").returncode, 2)
        self.assertEqual(self.run_cli("update", "OUT-001", "--status", "nope").returncode, 2)
        self.assertEqual(self.run_cli("update", "OUT-999", "--status", "drafted").returncode, 2)
        self.assertEqual(self.run_cli("update", "OUT-001").returncode, 2)
        self.assertEqual(self.run_cli("update", "--status", "drafted").returncode, 2)


class OutreachListTests(OutreachCase):
    """list:表格/过滤/--json/缺文件与坏文件退出码 2"""

    def test_table_status_filter_and_json(self):
        self.add_gaps()
        assert self.run_cli("update", "OUT-001", "--status", "drafted").returncode == 0
        r = self.run_cli("list")
        self.assertEqual(r.returncode, 0)
        self.assertIn("OUT-001", r.stdout)
        self.assertIn("g2.com", r.stdout)
        self.assertIn("drafted", r.stdout)
        self.assertIn("共 2 条", r.stdout)
        r = self.run_cli("list", "--status", "drafted")
        self.assertIn("OUT-001", r.stdout)
        self.assertNotIn("OUT-002", r.stdout)
        r = self.run_cli("list", "--status", "nope")
        self.assertEqual(r.returncode, 2)
        r = self.run_cli("list", "--json")
        payload = json.loads(r.stdout)
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["count"], 2)
        self.assertEqual([it["domain"] for it in payload["items"]],
                         ["g2.com", "hubspot.co.uk"])

    def test_missing_and_broken_store_exit_2(self):
        self.assertEqual(self.run_cli("list").returncode, 2)
        with open(os.path.join(self.tmp, "outreach.json"), "w") as f:
            f.write('{"items": [{"id": "X"}]}')                          # 缺 domain/status
        self.assertEqual(self.run_cli("list").returncode, 2)


class OutreachDueTests(OutreachCase):
    """due:到期清单+该跟进谁文案+退出码 1(candidate/终态/未到期不入)"""

    def test_due_lists_overdue_with_action_and_exit_1(self):
        old = "2026-01-01T00:00:00+00:00"
        sent = [{"ts": old, "from": "drafted", "to": "sent"}]
        self.write_data([
            hand_item("OUT-001", "g2.com", status="sent", next_review=old, history=sent),
            hand_item("OUT-002", "a.com", status="drafted", next_review=old),
            hand_item("OUT-003", "b.com", status="replied", next_review=old),
            hand_item("OUT-004", "c.com", status="candidate"),            # 无复查日
            hand_item("OUT-005", "d.com", status="linked"),               # 终态
            hand_item("OUT-006", "e.com", status="drafted",
                      next_review="2099-01-01T00:00:00+00:00")])          # 未到期
        r = self.run_cli("due")
        self.assertEqual(r.returncode, 1)                                 # 有到期 → notify
        for i in ("OUT-001", "OUT-002", "OUT-003"):
            self.assertIn(i, r.stdout)
        for i in ("OUT-004", "OUT-005", "OUT-006"):
            self.assertNotIn(i, r.stdout)
        self.assertIn("该跟进谁", r.stdout)
        self.assertIn("该催了", r.stdout)                                  # sent 文案
        self.assertIn("该发了", r.stdout)                                  # drafted 文案
        self.assertIn("该收链了", r.stdout)                                # replied 文案
        r = self.run_cli("due", "--json")
        self.assertEqual(r.returncode, 1)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["due"], 3)
        self.assertEqual([it["id"] for it in payload["items"]],
                         ["OUT-001", "OUT-002", "OUT-003"])

    def test_due_empty_exit_0(self):
        self.write_data([hand_item("OUT-001", "g2.com", status="candidate")])
        r = self.run_cli("due")
        self.assertEqual(r.returncode, 0)
        self.assertIn("(无到期", r.stdout)


class OutreachReportTests(OutreachCase):
    """report:漏斗(曾到达口径)/平均回复天数/--json/空库 N/A"""

    T0 = "2026-09-01T00:00:00+00:00"

    @staticmethod
    def hist(*pairs):
        """((from,to), days_after_T0) → history 列表。"""
        return [{"ts": (datetime(2026, 9, 1, tzinfo=timezone.utc)
                        + timedelta(days=d)).isoformat(), "from": f, "to": t}
                for (f, t), d in pairs]

    def test_funnel_rates_and_avg_reply_days(self):
        """5 候选:3 曾发送(linked 1 + sent 在途 1 + refused 1)→ 比率+均回复 2.0 天。"""
        self.write_data([
            hand_item("OUT-001", "a.com", status="linked",
                      history=self.hist((("drafted", "sent"), 3),
                                        (("sent", "replied"), 5),
                                        (("replied", "linked"), 9))),
            hand_item("OUT-002", "b.com", status="sent",
                      history=self.hist((("drafted", "sent"), 1))),
            hand_item("OUT-003", "c.com", status="drafted"),
            hand_item("OUT-004", "d.com", status="candidate"),
            hand_item("OUT-005", "e.com", status="refused",
                      history=self.hist((("drafted", "sent"), 2),
                                        (("sent", "replied"), 4),
                                        (("replied", "refused"), 6)))])
        r = self.run_cli("report")
        self.assertEqual(r.returncode, 0)
        self.assertIn("候选 5", r.stdout)
        self.assertIn("发送 3(60%)", r.stdout)          # 3/5 曾到达 sent
        self.assertIn("回复 2(67%)", r.stdout)          # 2/3 曾到达 replied
        self.assertIn("获得链接 1(50%)", r.stdout)       # 1/2 replied → linked
        self.assertIn("平均回复天数: 2.0(发出→首次回复,2 个样本)", r.stdout)
        r = self.run_cli("report", "--json")
        payload = json.loads(r.stdout)
        f = payload["funnel"]
        self.assertEqual((f["candidates"], f["sent"], f["replied"], f["linked"]),
                         (5, 3, 2, 1))
        self.assertEqual(f["rates"], {"candidate_to_sent": 0.6,
                                      "sent_to_replied": round(2 / 3, 3),
                                      "replied_to_linked": 0.5})
        self.assertEqual(f["avg_days_to_reply"], 2.0)                    # (5-3)+(4-2) /2
        self.assertEqual(f["refused"], 1)

    def test_report_empty_and_no_sent_na(self):
        self.write_data([])                                               # 空库 rc=0
        r = self.run_cli("report")
        self.assertEqual(r.returncode, 0)
        self.assertIn("候选 0", r.stdout)
        self.assertIn("平均回复天数: N/A", r.stdout)
        self.write_data([hand_item("OUT-001", "a.com", status="drafted")])
        r = self.run_cli("report")
        self.assertIn("发送 0(0%)", r.stdout)         # 0/1=0%,分母为 0 才 N/A
        self.assertIn("回复 0(N/A)", r.stdout)
        self.assertIn("平均回复天数: N/A", r.stdout)


class OutreachJsonEverywhereTests(OutreachCase):
    """--json 全子命令:add/update/due/report 顶层均带 schema_version=1。"""

    def test_all_subcommands_emit_json(self):
        r = self.run_cli("add", "--domain", "g2.com", "--json")
        self.assertEqual(json.loads(r.stdout)["schema_version"], 1)
        r = self.run_cli("update", "OUT-001", "--status", "drafted", "--json")
        payload = json.loads(r.stdout)
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["updated"]["status"], "drafted")
        r = self.run_cli("due", "--json")                                 # 无到期 rc=0
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["due"], 0)
        r = self.run_cli("report", "--json")
        self.assertEqual(json.loads(r.stdout)["schema_version"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
