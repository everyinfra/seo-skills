#!/usr/bin/env python3
"""content_queue.py 回归(stdlib unittest,合成三源,零网络,standalone——助手照抄
run_tests.py 顶部,不 import run_tests,被其 test_*.py 自动发现加载)。口径钉死
脚本自身契约(规格=pipeline-completeness.md R1-8 + 内容生产体系报告):

collect 三源合并与缺源降级(trend 只收 WATCH 态/go·pivot·drop 不收;serp 只收
共享≥4 的缺口行,互链/分开只计数;缺源=未提供或文件不存在 → 跳过告警不猜,三源
全缺退出码 1;文件在但解析不了 → 退出码 2)/评分口径(score=流量潜力×意图系数×
时效加成,合成输入钉死精确值)/striking 与衰退阈值(pos 5-20 且曝光≥20;28v28、
prev≥10 且降幅≤-25%,只统计两期都出现的词)/去重幂等(同源同题不重复入库)/
--gsc-out 预跑输出与现算等价/plan 周排期(Top N 按分数、WIP 上限超限只列不排、
源→建议管线映射)/track 状态机(六态逐级、跳级回退同态拒绝=降级拒绝、published
必须 --url(http/https)、gated --reject 打回计次且唯一合法回退)/report 遥测
(lead time=created→published_at 天数分布、WIP=briefed+drafting+gated、按闸拒收率
=Σ打回÷进闸条数)与状态分布/--json。

时间不打桩:trend 时效加成用 now-3h(<24h→1.5)与 now-30d(→1.0)宽窗构造;
lead time 用固定 created/published_at 精确差值断言(remediation 测试同法)。"""
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

URL_OK = "https://example.com/post"


def run_cq(args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "content_queue.py"), *args],
                          cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=env)


# ---------------------------------------------------------------- 合成三源
def trend_state(watch=(), others=()):
    """合成 .trend-state.json:watch=[(sid,title,first_seen,rel)];others=[(sid,status,title)]。"""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    signals = {}
    for sid, title, first_seen, rel in watch:
        signals[sid] = {"signal_id": sid, "title": title, "status": "watch",
                        "sources": ["hn", "google-news"], "tokens": [],
                        "first_seen": first_seen.isoformat(),
                        "last_seen": now.isoformat(), "rel_score": rel,
                        "deadline": None, "velocity": None}
    for sid, status, title in others:
        signals[sid] = {"signal_id": sid, "title": title, "status": status,
                        "sources": ["hn"], "first_seen": now.isoformat(),
                        "last_seen": now.isoformat(), "rel_score": 40}
    return json.dumps({"checked_at": now.isoformat(), "sources": {}, "signals": signals,
                       "seen": {}}, ensure_ascii=False)


def gsc_csv(rows):
    """合成 GSC 单表导出:rows=[(query,clicks,impr,ctr,position)]。"""
    out = ["Query,Clicks,Impressions,CTR,Position"]
    out += ["%s,%d,%d,%s,%s" % r for r in rows]
    return "\n".join(out) + "\n"


def serp_text(pairs):
    """合成 serp_overlap.py 存盘输出:pairs=[(a,b,shared,verdict)](列宽照抄上游)。"""
    out = ["%s%s%s%s" % ("关键词对".ljust(50), "共享".ljust(4), "判据", "")]
    for a, b, shared, verdict in pairs:
        out.append("%s × %-24s%-4d%s" % (a[:22], b[:24], shared, verdict))
    return "\n".join(out) + "\n"


def hand_item(i, source="gsc_mining:striking", topic="t", status="idea", score=5.0,
              created="2026-10-01T00:00:00+00:00", **extra):
    d = {"id": i, "source": source, "topic": topic, "evidence": "synthetic",
         "score": score, "status": status, "created": created, "url": None,
         "published_at": None, "gate_rejections": 0, "entered_gated": False,
         "history": [], "note": ""}
    d.update(extra)
    return d


class ContentQueueCase(unittest.TestCase):
    """公共助手:每用例独立 tmpdir(contentops.json 与三源文件都落在其中)。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="content-queue-test-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.now = datetime.now(timezone.utc).replace(microsecond=0)

    def write(self, name, text):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def run_cli(self, *args):
        return run_cq(list(args), self.tmp)

    def data(self):
        with open(os.path.join(self.tmp, "contentops.json"), encoding="utf-8") as f:
            return json.load(f)["items"]

    def write_data(self, items):
        self.write("contentops.json",
                   json.dumps({"schema_version": 1, "items": items}, ensure_ascii=False))

    # 三源齐全的标准夹具:1 条 WATCH(新)+ go/drop 各 1(不收)+ striking 3 词
    # (1 词出界)+ 衰退 2 词 + serp 1 缺口行 + 1 互链行(不收)
    def std_sources(self):
        fresh = (self.now - timedelta(hours=3)).isoformat()
        old = (self.now - timedelta(days=30)).isoformat()
        self.write(".trend-state.json", trend_state(
            watch=[("t1", "AI search launches new mode", datetime.fromisoformat(fresh), 30),
                   ("t4", "Old watched signal", datetime.fromisoformat(old), 20)],
            others=[("t2", "go", "Go signal"), ("t3", "drop", "Dropped signal")]))
        self.write("cur.csv", gsc_csv([
            ("best crm pricing", 10, 1000, "1%", 7.2),
            ("how to backup phone", 5, 400, "1.25%", 12.0),
            ("plain informational query", 3, 400, "0.75%", 9.0),
            ("out of range pos", 9, 3000, "0.3%", 3.0)]))
        self.write("prev.csv", gsc_csv([
            ("best crm pricing", 60, 900, "6%", 9.0),
            ("declining guide query", 120, 800, "15%", 6.0)]))
        with open(os.path.join(self.tmp, "cur.csv"), "a", encoding="utf-8") as f:
            f.write("declining guide query,40,700,5%,25.0\n")   # pos 25:只在衰退桶,不进 striking
        self.write("serp.txt", serp_text([
            ("crm vs salesforce", "best crm software", 6, "同簇(一页可服务)"),
            ("alpha tool", "beta tool", 2, "互链")]))


class ContentQueueCliTests(unittest.TestCase):
    """--help / 无子命令 / 未知子命令"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="content-queue-cli-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_help(self):
        r = run_cq(["--help"], self.tmp)
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage: content_queue.py", r.stdout)
        for sub in ("collect", "plan", "track", "report"):
            self.assertIn(sub, r.stdout)
        self.assertIn("退出码: 0 正常 / 1 collect 三源全缺 / 2 输入或参数错误", r.stdout)
        self.assertIn("流量潜力", r.stdout)                      # 评分口径进 help

    def test_no_subcommand_and_unknown(self):
        self.assertEqual(run_cq([], self.tmp).returncode, 2)
        r = run_cq(["explode"], self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知子命令", r.stderr)


class CollectTests(ContentQueueCase):
    """collect:三源合并/口径与阈值/评分/缺源降级/损坏退出码 2/幂等/预跑等价"""

    def full_collect(self, *extra):
        return self.run_cli("collect", "--gsc", "cur.csv", "--gsc", "prev.csv",
                            "--serp-out", "serp.txt", *extra)

    def test_three_source_merge_and_exclusions(self):
        self.std_sources()
        r = self.full_collect()
        self.assertEqual(r.returncode, 0)
        self.assertIn("新增 8 条", r.stdout)
        items = self.data()
        by = {(it["source"], it["topic"]): it for it in items}
        # 统一 idea 五字段 + 生命周期初始态
        for it in items:
            for k in ("id", "source", "topic", "evidence", "score"):
                self.assertIn(k, it, it["id"])
            self.assertEqual(it["status"], "idea")
            self.assertTrue(it["id"].startswith("CQ-"))
            self.assertTrue(it["created"].endswith("+00:00"))    # timezone.utc 口径
        # 三源各就位:trend 2(WATCH 才收,go/drop 不收)/striking 3/decay 2/serp 1
        self.assertEqual(sorted(it["source"] for it in items).count("trend_watch"), 2)
        self.assertNotIn(("trend_watch", "Go signal"), by)
        self.assertNotIn(("trend_watch", "Dropped signal"), by)
        self.assertIn(("trend_watch", "AI search launches new mode"), by)
        self.assertIn(("gsc_mining:striking", "best crm pricing"), by)
        self.assertIn(("gsc_mining:striking", "how to backup phone"), by)
        self.assertIn(("gsc_mining:striking", "plain informational query"), by)
        self.assertNotIn(("gsc_mining:striking", "out of range pos"), by)  # pos 3 出界
        self.assertIn(("gsc_mining:decay", "declining guide query"), by)
        self.assertIn(("gsc_mining:decay", "best crm pricing"), by)
        self.assertIn(("serp_overlap", "crm vs salesforce × best crm software"), by)
        self.assertEqual(len(items), 8)
        # 互链行(共享 2)不入队,只在源摘要计数
        self.assertNotIn("alpha tool", json.dumps(items, ensure_ascii=False))
        self.assertIn("跳过 1 条(互链/分开", r.stdout)
        # evidence 带底层数字(不猜:数字来自源数据)
        self.assertIn("pos=7.2", by[("gsc_mining:striking", "best crm pricing")]["evidence"])
        self.assertIn("impr=1000", by[("gsc_mining:striking", "best crm pricing")]["evidence"])
        self.assertIn("120→40", by[("gsc_mining:decay", "declining guide query")]["evidence"])
        self.assertIn("6/10", by[("serp_overlap",
                                  "crm vs salesforce × best crm software")]["evidence"])

    def test_score_formula_pinned(self):
        """score = 流量潜力 × 意图系数 × 时效加成,合成输入钉死:
        striking: 10×min(1,impr/2000)×IC(BOFU 1.2/MOFU 1.0/其余 0.8)
        decay:    10×min(1,prev/500)×IC      trend: 5×0.8×FB(新 1.5/旧 1.0)
        serp:     5×IC(关键词含 vs→1.2)"""
        self.std_sources()
        self.assertEqual(self.full_collect().returncode, 0)
        sc = {(it["source"], it["topic"]): it["score"] for it in self.data()}
        self.assertEqual(sc[("gsc_mining:striking", "best crm pricing")], 6.0)     # 5.0×1.2×1.0
        self.assertEqual(sc[("gsc_mining:striking", "how to backup phone")], 2.0)  # 2.0×1.0×1.0
        self.assertEqual(sc[("gsc_mining:striking", "plain informational query")],
                         1.6)                                                     # 2.0×0.8×1.0
        self.assertEqual(sc[("gsc_mining:decay", "declining guide query")], 2.4)  # 2.4×1.0×1.0
        self.assertEqual(sc[("gsc_mining:decay", "best crm pricing")], 1.44)      # 1.2×1.2×1.0
        self.assertEqual(sc[("trend_watch", "AI search launches new mode")], 6.0)  # 5×0.8×1.5
        self.assertEqual(sc[("trend_watch", "Old watched signal")], 4.0)          # 5×0.8×1.0
        self.assertEqual(sc[("serp_overlap", "crm vs salesforce × best crm software")],
                         6.0)                                                     # 5×1.2×1.0
        # 排序:plan 的 Top 选取按分数降序(同分按 id)
        r = self.run_cli("plan", "--wip", "1", "--top", "2")
        self.assertEqual(r.returncode, 0)
        first_ids = [ln.split()[0] for ln in r.stdout.splitlines()
                     if ln.startswith("CQ-")][:2]
        self.assertEqual(len(first_ids), 2)
        scores = {it["id"]: it["score"] for it in self.data()}
        self.assertGreaterEqual(scores[first_ids[0]], scores[first_ids[1]])

    def test_striking_and_decay_thresholds(self):
        self.write("cur.csv", gsc_csv([
            ("pos just below", 5, 300, "1%", 4.9),        # pos<5 出界
            ("pos at floor", 5, 300, "1%", 5.0),          # 恰 5 → 入
            ("impr just below", 1, 19, "5%", 8.0),        # 曝光<20 出界
            ("impr at floor", 1, 20, "5%", 8.0),          # 恰 20 → 入
            ("only in cur", 50, 300, "1%", 7.0)]))        # 不在 prev → 衰退不判
        self.write("prev.csv", gsc_csv([
            ("prev below ten", 9, 300, "1%", 7.0),        # prev<10 → 衰退不判
            ("drop twenty pct", 100, 300, "1%", 7.0),     # 降幅 -20% → 不判
            ("drop at line", 100, 300, "1%", 7.0)]))
        with open(os.path.join(self.tmp, "cur.csv"), "a", encoding="utf-8") as f:
            f.write("prev below ten,5,300,1%,8.0\n"
                    "drop twenty pct,80,300,1%,8.0\n"
                    "drop at line,75,300,1%,8.0\n")       # -25% 恰线 → 入
        r = self.run_cli("collect", "--gsc", "cur.csv", "--gsc", "prev.csv")
        self.assertEqual(r.returncode, 0)
        got = {(it["source"], it["topic"]) for it in self.data()}
        self.assertIn(("gsc_mining:striking", "pos at floor"), got)
        self.assertIn(("gsc_mining:striking", "impr at floor"), got)
        self.assertNotIn(("gsc_mining:striking", "pos just below"), got)
        self.assertNotIn(("gsc_mining:striking", "impr just below"), got)
        self.assertIn(("gsc_mining:decay", "drop at line"), got)
        self.assertNotIn(("gsc_mining:decay", "drop twenty pct"), got)
        self.assertNotIn(("gsc_mining:decay", "prev below ten"), got)
        self.assertNotIn(("gsc_mining:decay", "only in cur"), got)

    def test_missing_source_degradation(self):
        self.write("serp.txt", serp_text([("a vs b", "c tool", 5, "同簇(一页可服务)")]))
        r = self.run_cli("collect", "--serp-out", "serp.txt")
        self.assertEqual(r.returncode, 0)                       # 单源可用 → 0
        self.assertIn("跳过 trend 源", r.stderr)                 # 缺源告警,不猜
        self.assertIn("跳过 gsc 源", r.stderr)
        items = self.data()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["source"], "serp_overlap")
        # 三源全缺 → 退出码 1,且不建库(清掉上一步建的库再验)
        os.unlink(os.path.join(self.tmp, "contentops.json"))
        r = self.run_cli("collect")
        self.assertEqual(r.returncode, 1)
        self.assertIn("三源全缺", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "contentops.json")))

    def test_corrupt_source_files_exit_2(self):
        p = self.write("bad-state.json", "not json {")
        r = self.run_cli("collect", "--trend-state", p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--trend-state 解析失败", r.stderr)
        q = self.write("bad-out.json", "]]]")
        r = self.run_cli("collect", "--gsc-out", q)
        self.assertEqual(r.returncode, 2)
        q2 = self.write("wrong-out.json", json.dumps({"mode": "matrix"}))
        r = self.run_cli("collect", "--gsc-out", q2)
        self.assertEqual(r.returncode, 2)
        self.assertIn("缺 striking_distance/declined", r.stderr)

    def test_idempotent_dedupe(self):
        self.std_sources()
        self.assertEqual(self.full_collect().returncode, 0)
        r = self.full_collect()
        self.assertEqual(r.returncode, 0)
        self.assertIn("新增 0 条", r.stdout)
        self.assertIn("去重跳过 8", r.stdout)
        self.assertEqual(len(self.data()), 8)                   # 同源同题不重复入库

    def test_gsc_out_prerun_equivalence(self):
        """--gsc-out 预跑输出与 --gsc 现算同分同题(gsc_mining --json 形态)。"""
        self.write("cur.csv", gsc_csv([("best crm pricing", 10, 1000, "1%", 7.2)]))
        self.write("prev.csv", gsc_csv([("declining guide query", 120, 800, "15%", 6.0)]))
        with open(os.path.join(self.tmp, "cur.csv"), "a", encoding="utf-8") as f:
            f.write("declining guide query,40,700,5%,25.0\n")  # pos 25:只进衰退桶
        self.assertEqual(self.run_cli("collect", "--gsc", "cur.csv",
                                      "--gsc", "prev.csv").returncode, 0)
        live = {(it["source"], it["topic"]): it["score"] for it in self.data()}
        prerun = self.write("mining.json", json.dumps({
            "mode": "decay", "declined": [
                {"query": "declining guide query", "prev": 120, "cur": 40, "delta": "-67%"}]}))
        qrun = self.write("mining-q.json", json.dumps({
            "mode": "query", "striking_distance": [
                {"query": "best crm pricing", "pos": 7.2, "impressions": 1000, "clicks": 10}]}))
        os.unlink(os.path.join(self.tmp, "contentops.json"))
        r = self.run_cli("collect", "--gsc-out", prerun, "--gsc-out", qrun)
        self.assertEqual(r.returncode, 0)
        pre = {(it["source"], it["topic"]): it["score"] for it in self.data()}
        self.assertEqual(live, pre)                             # 预跑=现算(逐键)


class PlanTests(ContentQueueCase):
    """plan:WIP 上限超限只列不排/建议管线映射/Top N/缺文件退出码 2"""

    def test_wip_cap_and_pipeline_mapping(self):
        self.write_data([
            hand_item("CQ-001", status="briefed", topic="wip one", score=1.0),
            hand_item("CQ-002", status="gated", topic="wip two", score=2.0),
            hand_item("CQ-003", "trend_watch", "fresh trend", score=9.0),
            hand_item("CQ-004", "gsc_mining:striking", "kw idea", score=8.0),
            hand_item("CQ-005", "serp_overlap", "a × b", score=7.0)])
        r = self.run_cli("plan", "--wip", "3", "--week", "2026-W42")
        self.assertEqual(r.returncode, 0)
        self.assertIn("# 内容周排期:2026-W42", r.stdout)
        self.assertIn("WIP: 当前 2 / 上限 3 → 本周可排 1 条", r.stdout)
        self.assertIn("## 在制(WIP 2/3)", r.stdout)
        self.assertIn("## 本周排期(1 条;Top 10 按分数)", r.stdout)
        self.assertIn("CQ-003", r.stdout.split("## 本周排期")[1].split("## 候补")[0])
        # 超限只列不排:候补区含 CQ-004/CQ-005
        cand = r.stdout.split("## 候补(超 WIP 上限,只列不排;2 条)")[1]
        self.assertIn("CQ-004", cand)
        self.assertIn("CQ-005", cand)
        # 建议管线映射:trend→trend-jack / 关键词→content-brief / 缺口→对比页
        self.assertIn("trend-jack 管线", r.stdout)
        self.assertIn("templates/content/trend-jack-playbook.md", r.stdout)
        self.assertIn("content-brief 管线", r.stdout)
        self.assertIn("templates/content/content-brief.md", r.stdout)
        self.assertIn("对比页模板", r.stdout)
        self.assertIn("content-structure-templates.md §对比(A vs B)", r.stdout)

    def test_wip_full_zero_scheduled_and_top_n(self):
        self.write_data([
            hand_item("CQ-001", status="drafting", topic="wip one"),
            hand_item("CQ-002", status="briefed", topic="wip two"),
            hand_item("CQ-003", topic="a", score=9.0),
            hand_item("CQ-004", topic="b", score=8.0),
            hand_item("CQ-005", topic="c", score=7.0)])
        r = self.run_cli("plan", "--wip", "2")
        self.assertEqual(r.returncode, 0)
        self.assertIn("本周可排 0 条", r.stdout)
        self.assertIn("(0 条 —— WIP 已满或无 idea", r.stdout)
        self.assertIn("## 候补(超 WIP 上限,只列不排;3 条)", r.stdout)
        r = self.run_cli("plan", "--wip", "2", "--top", "1")    # Top 1 只看最高分
        self.assertEqual(r.returncode, 0)
        self.assertIn("## 候补(超 WIP 上限,只列不排;1 条)", r.stdout)
        body = r.stdout.split("## 候补")[1]
        self.assertIn("CQ-003", body)
        self.assertNotIn("CQ-004", body)

    def test_plan_missing_file_exit_2(self):
        r = self.run_cli("plan")
        self.assertEqual(r.returncode, 2)
        self.assertIn("先运行 collect", r.stderr)


class TrackTests(ContentQueueCase):
    """track:六态状态机/降级拒绝/published 需 URL/--reject 打回计次"""

    def track(self, tid, *extra):
        return self.run_cli("track", tid, *extra)

    def seeded(self):
        self.write_data([hand_item("CQ-001", topic="first"),
                         hand_item("CQ-002", topic="second")])
        return self.data

    def test_happy_path_full_chain(self):
        self.seeded()
        for st in ("briefed", "drafting", "gated"):
            r = self.track("CQ-001", "--status", st)
            self.assertEqual(r.returncode, 0, st)
            self.assertIn("→ %s" % st, r.stdout)
            self.assertIn("遥测: ", r.stdout)                   # 推进后即出遥测
        r = self.track("CQ-001", "--status", "published", "--url", URL_OK,
                       "--note", "上线")
        self.assertEqual(r.returncode, 0)
        it = self.data()[0]
        self.assertEqual((it["status"], it["url"], it["note"]),
                         ("published", URL_OK, "上线"))
        self.assertTrue(it["entered_gated"])                    # 过闸留痕(拒收率分母)
        pub = datetime.fromisoformat(it["published_at"])
        self.assertLess(abs((datetime.now(timezone.utc) - pub).total_seconds()), 600)
        self.assertGreaterEqual(pub.utcoffset(), timezone.utc.utcoffset(pub))
        r = self.track("CQ-001", "--status", "measured")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.data()[0]["status"], "measured")  # 终态
        self.assertIn("WIP 当前 0", r.stdout)                    # published 出制

    def test_backward_skip_same_rejected(self):
        self.seeded()
        r = self.track("CQ-001", "--status", "drafting")         # 跳级
        self.assertEqual(r.returncode, 2)
        self.assertIn("非法状态转换", r.stderr)
        self.track("CQ-001", "--status", "briefed")
        r = self.track("CQ-001", "--status", "briefed")          # 同态
        self.assertEqual(r.returncode, 2)
        r = self.track("CQ-001", "--status", "idea")             # 回退到初始态
        self.assertEqual(r.returncode, 2)
        self.track("CQ-001", "--status", "drafting")
        r = self.track("CQ-001", "--status", "briefed")          # 降级(回退一级)
        self.assertEqual(r.returncode, 2)
        self.assertIn("降级拒绝", r.stderr)
        for st in ("gated", "published", "measured"):            # 走到终态
            self.track("CQ-001", "--status", st,
                       *(["--url", URL_OK] if st == "published" else []))
        for st in ("published", "idea", "briefed"):              # measured 终态不可再动
            r = self.track("CQ-001", "--status", st)
            self.assertEqual(r.returncode, 2, st)

    def test_published_requires_valid_url(self):
        self.write_data([hand_item("CQ-001", status="gated")])
        r = self.track("CQ-001", "--status", "published")        # 缺 --url
        self.assertEqual(r.returncode, 2)
        self.assertIn("必须带合法 --url", r.stderr)
        r = self.track("CQ-001", "--status", "published", "--url", "ftp://x.com/a")
        self.assertEqual(r.returncode, 2)                        # 仅 http/https
        r = self.track("CQ-001", "--status", "drafting", "--url", URL_OK)
        self.assertEqual(r.returncode, 2)                        # --url 仅 published 接受
        r = self.track("CQ-001", "--status", "published", "--url", URL_OK)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self.data()[0]["url"], URL_OK)

    def test_gate_reject_flow_and_counting(self):
        self.write_data([hand_item("CQ-001", status="drafting")])
        r = self.track("CQ-001", "--reject")                     # 非 gated 不可打回
        self.assertEqual(r.returncode, 2)
        self.track("CQ-001", "--status", "gated")
        r = self.track("CQ-001", "--reject", "--note", "证据不足")
        self.assertEqual(r.returncode, 0)
        it = self.data()[0]
        self.assertEqual((it["status"], it["gate_rejections"]), ("drafting", 1))
        self.assertEqual(it["note"], "证据不足")
        self.assertIn("按闸打回,累计 1 次", r.stdout)
        self.track("CQ-001", "--status", "gated")
        self.track("CQ-001", "--reject")                         # 二次打回
        it = self.data()[0]
        self.assertEqual((it["status"], it["gate_rejections"]), ("drafting", 2))
        self.assertTrue(any(h["event"] == "gate-reject" for h in it["history"]))

    def test_unknown_id_and_mutual_exclusion(self):
        self.seeded()
        self.assertEqual(self.track("CQ-999", "--status", "briefed").returncode, 2)
        self.assertEqual(self.track("CQ-001").returncode, 2)     # 缺 --status/--reject
        r = self.track("CQ-001", "--status", "briefed", "--reject")
        self.assertEqual(r.returncode, 2)                        # 互斥
        self.assertIn("互斥", r.stderr)


class ReportTests(ContentQueueCase):
    """report:遥测三指标(lead time 分布/WIP/按闸拒收率)+ 状态分布"""

    FILE = [
        hand_item("CQ-001", topic="fast", status="measured",
                  created="2026-10-01T00:00:00+00:00",
                  published_at="2026-10-03T00:00:00+00:00",     # 2.0d
                  entered_gated=True),
        hand_item("CQ-002", topic="slow", status="published",
                  created="2026-10-01T00:00:00+00:00",
                  published_at="2026-10-11T00:00:00+00:00",     # 10.0d
                  entered_gated=True, gate_rejections=1),
        hand_item("CQ-003", topic="wip a", status="briefed"),
        hand_item("CQ-004", topic="wip b", status="gated", gate_rejections=0),
        hand_item("CQ-005", topic="backlog a"),
        hand_item("CQ-006", topic="backlog b"),
    ]

    def test_telemetry_and_distribution(self):
        self.write_data(self.FILE)
        r = self.run_cli("report")
        self.assertEqual(r.returncode, 0)
        self.assertIn("# 内容队列 ContentOps 报告", r.stdout)
        self.assertIn("状态分布: idea 2 / briefed 1 / drafting 0 / gated 1 /"
                      " published 1 / measured 1", r.stdout)
        self.assertIn("WIP 当前: 2", r.stdout)
        self.assertIn("按闸拒收: 1 次打回 / 2 条进闸 = 50%", r.stdout)
        self.assertIn("Lead time(idea→published): n=2,中位 6.0d,均值 6.0d,"
                      "区间 2.0-10.0d", r.stdout)
        self.assertIn("CQ-001 2.0d", r.stdout)                   # 分布明细
        self.assertIn("CQ-002 10.0d", r.stdout)
        self.assertIn("## 在制清单(2)", r.stdout)
        payload = json.loads(self.run_cli("report", "--json").stdout)
        self.assertEqual(payload["total"], 6)
        self.assertEqual(payload["counts"]["idea"], 2)
        self.assertEqual(payload["wip"], 2)
        lt = payload["telemetry"]["lead_time_days"]
        self.assertEqual((lt["n"], lt["median"], lt["mean"], lt["min"], lt["max"]),
                         (2, 6.0, 6.0, 2.0, 10.0))
        self.assertEqual(lt["items"], [{"id": "CQ-001", "days": 2.0},
                                       {"id": "CQ-002", "days": 10.0}])
        self.assertEqual(payload["telemetry"]["gate_rejections"],
                         {"count": 1, "entered_gated": 2, "rate": 0.5})

    def test_na_when_no_published_and_missing_file(self):
        self.write_data([hand_item("CQ-001", status="drafting")])
        r = self.run_cli("report")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Lead time(idea→published): N/A", r.stdout)
        self.assertIn("按闸拒收: 0 次打回 / 0 条进闸 = N/A", r.stdout)
        payload = json.loads(self.run_cli("report", "--json").stdout)
        self.assertIsNone(payload["telemetry"]["lead_time_days"])
        self.assertIsNone(payload["telemetry"]["gate_rejections"]["rate"])
        self.assertEqual(self.run_cli("report", "--file",
                                      os.path.join(self.tmp, "nope.json")).returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
