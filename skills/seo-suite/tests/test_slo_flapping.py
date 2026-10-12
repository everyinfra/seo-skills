#!/usr/bin/env python3
"""R4 监控对标①④(pipeline-completeness.md §五)回归:SLO+错误预算 / flapping / ack 超时。
standalone:合成 db/config/state/incidents,零网络(发送层全部 monkeypatch);
可直接 `python3 tests/test_slo_flapping.py`,亦被 tests/run_tests.py 自动装载。

① SLO(monitor):三指标计算口径(keypage_indexable / canonical_ok / healthy_pages,
  缺证据样本不计不猜)、剩余错误预算四档(≥100% / 中段 / <25% / 超耗 0%)、
  window_days 窗口裁剪、自定义 target、diff 集成(slo_budget_low warn,rc=2)、
  report 顶部 SLO 条形(文本+JSON)与按模板分账注记(crawl.page 口径)
④ flapping(monitor):同 (code,key) 7 天内 fire+resolved≥3 次(≥1 次 resolved)→
  降 info+附 flap_count+"建议修阈值";阈值下不降;纯持续(无 resolved)不降;
  7 天窗外历史不计
④ ack 超时(notify):critical 即时消息带 ack_deadline(默认 30min,
  ack_timeout_minutes 可调)、warn 不带;--flush 升级超期未 ack 的 critical
  (全渠道无视 route)且只升一次;`ack` 子命令停升级(未知 key 跳过不判错);
  pending_critical 重发刷新 ack 期限。"""
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import monitor as M   # noqa: E402
import notify as N    # noqa: E402


# ---------- monitor 侧助手(合成 db,零网络) ----------

def _fresh_dir(prefix="mon_r4_"):
    tmp = tempfile.mkdtemp(prefix=prefix)
    mdir = os.path.join(tmp, ".seo-monitor")
    rc = M.cmd_init(M.build_parser().parse_args(
        ["init", "--site", "https://example.com", "--market", "us", "--dir", mdir]))
    assert rc == 0
    return mdir


def _insert_run(mdir, snapshots, ts_offset_days=0, status="ok"):
    """snapshots: {check: {key: value}} 直接落快照(绕过网络)。"""
    conn = M.open_db(mdir)
    ts = (datetime.now() - timedelta(days=ts_offset_days)).isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO runs(ts,kind,status,checks_run,budget_used_sec,summary) "
        "VALUES(?,?,?,'daily',0,'')", (ts, "daily", status))
    rid = cur.lastrowid
    for check, kv in snapshots.items():
        for key, value in kv.items():
            conn.execute(
                "INSERT INTO snapshots(run_id,ts,\"check\",key,value,hash) VALUES(?,?,?,?,?,?)",
                (rid, ts, check, key, json.dumps(value), "h%d%s%s" % (rid, check, key)))
    conn.commit()
    conn.close()
    return rid


def _run_cmd(args_list):
    """直接经 parser 分发 cmd_*(不打 subprocess),捕获 stdout/stderr → (rc, out, err)。"""
    out, err = io.StringIO(), io.StringIO()
    args = M.build_parser().parse_args(args_list)
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = args.func(args)
    return rc, out.getvalue(), err.getvalue()


def _set_config(mdir, **over):
    cfg = M.load_config(mdir)
    cfg.update(over)
    M.save_config(mdir, cfg)
    return cfg


def _slo_cfg(metrics):
    return {"site": "https://example.com", "thresholds": dict(M.DEFAULT_THRESHOLDS),
            "slo": metrics}


def _idx_pages(n, n_bad):
    """n 页合成快照:前 n_bad 页 indexable=False(noindex),其余 True。"""
    return {"/p%04d" % i: {"status": 200, "indexable": i >= n_bad} for i in range(n)}


def _seed_flap_history(mdir, code, key, fires=(), resolved=(), fire_resolved=True):
    """直接落 alerts 历史行(小时偏移,负=过去):fires=fire 行,resolved=code+'_resolved'
    自愈行。fire 行的 resolved 标志可配(True=已自愈,不进 cooldown 未结集)。"""
    conn = M.open_db(mdir)
    now = datetime.now()
    for hrs in fires:
        ts = (now - timedelta(hours=hrs)).isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO alerts(run_id, ts, level, code, key, message, details, suppressed, resolved) "
            "VALUES(1, ?, 'warn', ?, ?, 'm', '{}', 0, ?)",
            (ts, code, key, 1 if fire_resolved else 0))
    for hrs in resolved:
        ts = (now - timedelta(hours=hrs)).isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO alerts(run_id, ts, level, code, key, message, details, suppressed, resolved) "
            "VALUES(1, ?, 'low', ?, ?, '自愈', '{}', 0, 1)", (ts, code + "_resolved", key))
    conn.commit()
    conn.close()


def _hits(alerts, code):
    return [a for a in alerts if a["code"] == code]


# ---------- notify 侧助手(合成 config/incidents,发送层 monkeypatch) ----------

_file_seq = [0]


def _nfy_dir(channels, extra_cfg=None):
    tmp = tempfile.mkdtemp(prefix="nfy_r4_")
    mdir = os.path.join(tmp, ".seo-monitor")
    os.makedirs(mdir)
    cfg = {"site": "https://example.com", "run_cadence_hours": 24, "channels": channels}
    if extra_cfg:
        cfg.update(extra_cfg)
    with open(os.path.join(mdir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return mdir


def _alerts_file(mdir, alerts):
    _file_seq[0] += 1
    path = os.path.join(mdir, "alerts-%d-%d.json" % (os.getpid(), _file_seq[0]))
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"site": "https://example.com",
                   "generated": datetime.now().isoformat(timespec="seconds"),
                   "alerts": alerts}, f)
    return path


class _FakeTargets:
    """替换 N.channel_targets:记录 (渠道名, 消息),全部返回成功(零网络)。"""

    def __init__(self, names):
        self.names = names
        self.sent = []

    def __call__(self, cfg):
        def mk(nm):
            def fn(msg):
                self.sent.append((nm, msg))
                return 200, "ok"
            return fn
        return [(nm, mk(nm)) for nm in self.names]


# ================= ① SLO:计算口径与预算档位 =================

class SloComputeTests(unittest.TestCase):
    """compute_slo 三指标样本口径 + 剩余错误预算四档(≥100%/中段/<25%/超耗)。"""

    def test_slo_disabled_without_config(self):
        """未配 slo 节 → configured=False,再差的快照也不产 slo_budget_low(不猜)。"""
        mdir = _fresh_dir()
        _insert_run(mdir, {"pages": _idx_pages(100, 50)})     # 一半 noindex 也不告
        conn = M.open_db(mdir)
        slo = M.compute_slo(conn, {"site": "https://example.com"})
        conn.close()
        self.assertFalse(slo["configured"])
        self.assertEqual(slo["metrics"], {})
        self.assertEqual(M.slo_alerts_from(slo), [])

    def test_slo_budget_four_tiers(self):
        """预算档位:0 坏=≥100% 不告;2/1000=剩 60% 不告;4/1000=剩 20% 告;10/1000=超耗 0% 告。"""
        for n_bad, expect_alert, expect_pct in ((0, False, None), (2, False, 60),
                                                (4, True, 20), (10, True, 0)):
            mdir = _fresh_dir(prefix="mon_r4_tier_")
            _insert_run(mdir, {"pages": _idx_pages(1000, n_bad)})
            conn = M.open_db(mdir)
            slo = M.compute_slo(conn, _slo_cfg(
                {"keypage_indexable": {"target": 0.995, "window_days": 30}}))
            alerts = M.slo_alerts_from(slo)
            conn.close()
            hit = _hits(alerts, "slo_budget_low")
            self.assertEqual(len(hit), 1 if expect_alert else 0, "n_bad=%d" % n_bad)
            if not expect_alert:
                continue
            self.assertEqual(hit[0]["level"], "warn")
            self.assertEqual(hit[0]["key"], "keypage_indexable")
            self.assertIn("索引健康 SLO 99.50%", hit[0]["message"])
            self.assertIn("错误预算剩 %d%%" % expect_pct, hit[0]["message"])
            self.assertIn("接近耗尽将建议冻结发布", hit[0]["message"])
            self.assertEqual(hit[0]["details"]["budget_remaining"],
                             round(1 - (n_bad / 1000) / 0.005, 4))

    def test_slo_indexable_semantics(self):
        """可索引率:indexable True/False 计好/坏;缺键(旧库)不计——不毒化 SLO。"""
        mdir = _fresh_dir()
        pages = {"/old%02d" % i: {"status": 200} for i in range(50)}   # 旧快照:无键
        pages.update(_idx_pages(50, 1))                                # 49 好 1 坏
        _insert_run(mdir, {"pages": pages})
        conn = M.open_db(mdir)
        slo = M.compute_slo(conn, _slo_cfg(
            {"keypage_indexable": {"target": 0.995, "window_days": 30}}))
        conn.close()
        m = slo["metrics"]["keypage_indexable"]
        self.assertEqual((m["good"], m["bad"], m["samples"]), (49, 1, 50))
        self.assertEqual(m["actual"], 0.98)
        self.assertTrue(_hits(M.slo_alerts_from(slo), "slo_budget_low"))

    def test_slo_canonical_semantics(self):
        """canonical 正确率:404/不可达=坏;200 与 None(自指/无 canonical)=好;缺键不计。"""
        mdir = _fresh_dir()
        pages = {}
        for i in range(100):
            if i < 3:
                pages["/c%02d" % i] = {"status": 200, "canonical_target_status": 404}
            elif i < 5:
                pages["/c%02d" % i] = {"status": 200}                    # 缺键不计
            else:
                pages["/c%02d" % i] = {"status": 200,
                                       "canonical_target_status": 200 if i % 2 else None}
        _insert_run(mdir, {"pages": pages})
        conn = M.open_db(mdir)
        slo = M.compute_slo(conn, _slo_cfg(
            {"canonical_ok": {"target": 0.995, "window_days": 30}}))
        conn.close()
        m = slo["metrics"]["canonical_ok"]
        self.assertEqual((m["good"], m["bad"], m["samples"]), (95, 3, 98))
        self.assertTrue(_hits(M.slo_alerts_from(slo), "slo_budget_low"))

    def test_slo_healthy_semantics(self):
        """健康页率:error/http_error=坏;ok/无 state 键(旧库)=好。"""
        mdir = _fresh_dir()
        pages = {"/ok": {"status": 200}, "/ok2": {"state": "ok", "status": 200},
                 "/e1": {"state": "error", "error": "x"}, "/e2": {"state": "error"},
                 "/h1": {"state": "http_error", "status": 404},
                 "/h2": {"state": "http_error", "status": 500},
                 "/h3": {"state": "http_error", "status": 503}}
        for i in range(93):
            pages["/f%02d" % i] = {"status": 200}
        _insert_run(mdir, {"pages": pages})
        conn = M.open_db(mdir)
        slo = M.compute_slo(conn, _slo_cfg(
            {"healthy_pages": {"target": 0.995, "window_days": 30}}))
        conn.close()
        m = slo["metrics"]["healthy_pages"]
        self.assertEqual((m["good"], m["bad"], m["samples"]), (95, 5, 100))
        self.assertTrue(_hits(M.slo_alerts_from(slo), "slo_budget_low"))

    def test_slo_window_trims_old_runs(self):
        """window_days 裁剪:20 天前的坏 run 在 7 天窗不计(不告),30 天窗计入(告)。"""
        mdir = _fresh_dir()
        _insert_run(mdir, {"pages": _idx_pages(100, 10)}, ts_offset_days=20)
        _insert_run(mdir, {"pages": _idx_pages(100, 0)})
        conn = M.open_db(mdir)
        slo7 = M.compute_slo(conn, _slo_cfg(
            {"keypage_indexable": {"target": 0.995, "window_days": 7}}))
        slo30 = M.compute_slo(conn, _slo_cfg(
            {"keypage_indexable": {"target": 0.995, "window_days": 30}}))
        conn.close()
        self.assertEqual(slo7["metrics"]["keypage_indexable"]["samples"], 100)
        self.assertFalse(_hits(M.slo_alerts_from(slo7), "slo_budget_low"))
        self.assertEqual(slo30["metrics"]["keypage_indexable"]["samples"], 200)
        self.assertTrue(_hits(M.slo_alerts_from(slo30), "slo_budget_low"))

    def test_slo_custom_target(self):
        """自定义 target:0.99(容错 1%)下 5/1000 坏=剩 50% 不告;默认 0.995 则告。"""
        mdir = _fresh_dir()
        _insert_run(mdir, {"pages": _idx_pages(1000, 5)})
        conn = M.open_db(mdir)
        loose = M.compute_slo(conn, _slo_cfg(
            {"keypage_indexable": {"target": 0.99, "window_days": 30}}))
        strict = M.compute_slo(conn, _slo_cfg(
            {"keypage_indexable": {"target": 0.995, "window_days": 30}}))
        conn.close()
        self.assertEqual(loose["metrics"]["keypage_indexable"]["budget_remaining"], 0.5)
        self.assertFalse(_hits(M.slo_alerts_from(loose), "slo_budget_low"))
        self.assertTrue(_hits(M.slo_alerts_from(strict), "slo_budget_low"))

    def test_slo_no_samples_no_guess(self):
        """空库/无 pages 快照 → actual=None 不猜,不产告警;裸 true 条目按全默认算。"""
        mdir = _fresh_dir()
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 10}}})   # 无 pages 快照
        conn = M.open_db(mdir)
        slo = M.compute_slo(conn, _slo_cfg({"keypage_indexable": True}))
        conn.close()
        m = slo["metrics"]["keypage_indexable"]
        self.assertIsNone(m["actual"])
        self.assertEqual((m["target"], m["window_days"]),
                         (M.SLO_DEFAULT_TARGET, M.SLO_DEFAULT_WINDOW_DAYS))
        self.assertEqual(M.slo_alerts_from(slo), [])


# ================= ① SLO:diff 集成与 report 条形 =================

class SloDiffReportTests(unittest.TestCase):
    """slo_budget_low 进 diff 告警链(rc=2,payload 带 slo 段)+ report 顶部条形。"""

    def test_diff_emits_slo_budget_low(self):
        """两 run 各 4/1000 noindex(无状态翻转,不产 noindex_added)→ 唯一告警
        slo_budget_low(warn)→ rc=2;payload.slo 携带口径。"""
        mdir = _fresh_dir()
        pages = _idx_pages(1000, 4)
        _insert_run(mdir, {"pages": pages})
        _insert_run(mdir, {"pages": dict(pages)})
        _set_config(mdir, slo={"keypage_indexable": {"target": 0.995, "window_days": 30}})
        out = os.path.join(mdir, "alerts.json")
        rc, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 2, "slo_budget_low warn → rc=2")
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        hit = _hits(payload["alerts"], "slo_budget_low")
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["level"], "warn")
        self.assertIn("错误预算剩 20%", hit[0]["message"])
        self.assertEqual(payload["counts"]["warn"], 1)
        self.assertIsNotNone(payload["slo"])
        row = next(m for m in payload["slo"] if m["metric"] == "keypage_indexable")
        self.assertEqual(row["samples"], 2000)
        self.assertEqual(row["budget_remaining"], 0.2)

    def test_diff_without_slo_config_no_alert(self):
        """未配 slo 节:同样的坏快照不产 slo_budget_low(rc=0),payload.slo=None。"""
        mdir = _fresh_dir()
        pages = _idx_pages(1000, 4)
        _insert_run(mdir, {"pages": pages})
        _insert_run(mdir, {"pages": dict(pages)})
        out = os.path.join(mdir, "alerts.json")
        rc, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 0)
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertFalse(_hits(payload["alerts"], "slo_budget_low"))
        self.assertIsNone(payload["slo"])

    def test_report_slo_bar_text(self):
        """report 文本顶部:SLO 段=各指标 实际/目标 条形+剩余预算+模板分账注记。"""
        mdir = _fresh_dir()
        _insert_run(mdir, {"pages": _idx_pages(1000, 4)})
        _set_config(mdir, slo={"keypage_indexable": {"target": 0.995, "window_days": 30},
                               "canonical_ok": {"target": 0.995, "window_days": 30},
                               "healthy_pages": {"target": 0.995, "window_days": 30}})
        rc, tout, _ = _run_cmd(["report", "--dir", mdir, "--days", "7"])
        self.assertEqual(rc, 0)
        self.assertIn("-- SLO 索引健康(错误预算", tout)
        self.assertIn("优先页可索引率", tout)
        self.assertRegex(tout, r"优先页可索引率\s+实际\s+99\.60% / 目标\s+99\.50%")
        self.assertIn("错误预算剩 20%", tout)
        self.assertIn("(slo_budget_low:已建议冻结发布)", tout)
        self.assertIn("█", tout)                                    # 条形在场
        self.assertIn("无样本(不猜)", tout)                       # canonical 缺证据
        # 按模板分账注记:全站 SLO 会藏住单模板回归 → 指向 site_crawl(crawl.page 口径)
        self.assertIn("全站 SLO 会藏住单模板回归", tout)
        self.assertIn("site_crawl", tout) and self.assertIn("crawl.page", tout)

    def test_report_slo_json_and_unconfigured(self):
        """report --json 带 slo 段(configured/metrics 口径);未配时给配置示例提示。"""
        mdir = _fresh_dir()
        _insert_run(mdir, {"pages": _idx_pages(1000, 4)})
        _set_config(mdir, slo={"keypage_indexable": {"target": 0.995, "window_days": 30}})
        rc, jout, _ = _run_cmd(["report", "--dir", mdir, "--days", "7", "--json"])
        self.assertEqual(rc, 0)
        rep = json.loads(jout)
        self.assertTrue(rep["slo"]["configured"])
        row = next(m for m in rep["slo"]["metrics"] if m["metric"] == "keypage_indexable")
        self.assertEqual(row["budget_remaining"], 0.2)
        self.assertEqual(row["actual"], 0.996)
        # 未配置:文本提示 + json configured=False
        mdir2 = _fresh_dir()
        _insert_run(mdir2, {"pages": _idx_pages(10, 0)})
        rc, tout, _ = _run_cmd(["report", "--dir", mdir2, "--days", "7"])
        self.assertIn("(config 未配 slo 节", tout)
        rc, jout2, _ = _run_cmd(["report", "--dir", mdir2, "--days", "7", "--json"])
        self.assertFalse(json.loads(jout2)["slo"]["configured"])


# ================= ④ flapping(monitor) =================

class FlappingTests(unittest.TestCase):
    """fire+resolved≥3(≥1 次 resolved)降 info;阈值下/纯持续/窗外不降。"""

    @staticmethod
    def _flap_diff(mdir):
        out = os.path.join(mdir, "alerts.json")
        rc, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        return rc, payload

    def test_flapping_downgrades_to_info(self):
        """7 天内 2 fire+1 resolved=3 次 → homepage_down 降 info+flap_count+修阈值附注。"""
        mdir = _fresh_dir()
        _seed_flap_history(mdir, "homepage_down", "/",
                           fires=(48, 24), resolved=(36,))
        _insert_run(mdir, {"pages": {"/": {"status": 200, "title": "T"}}})
        _insert_run(mdir, {"pages": {"/": {"status": 404, "title": "T"}}})
        rc, payload = self._flap_diff(mdir)
        self.assertEqual(rc, 0, "critical 已降 info → 无 critical/warn → rc=0")
        hit = _hits(payload["alerts"], "homepage_down")
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["level"], "info")
        self.assertEqual(hit[0]["details"]["flap_count"], 3)
        self.assertEqual(hit[0]["details"]["flap_from_level"], "critical")
        self.assertIn("建议修阈值", hit[0]["message"])
        self.assertIn("反复触发/自愈=阈值贴边", hit[0]["message"])
        self.assertEqual(payload["counts"]["critical"], 0)
        self.assertEqual(payload["counts"]["info"], 1)

    def test_flapping_below_threshold_stays_critical(self):
        """1 fire+1 resolved=2 次(<3)→ 不降级,critical 保持,rc=1。"""
        mdir = _fresh_dir()
        _seed_flap_history(mdir, "homepage_down", "/",
                           fires=(24,), resolved=(12,))
        _insert_run(mdir, {"pages": {"/": {"status": 200, "title": "T"}}})
        _insert_run(mdir, {"pages": {"/": {"status": 404, "title": "T"}}})
        rc, payload = self._flap_diff(mdir)
        self.assertEqual(rc, 1)
        hit = _hits(payload["alerts"], "homepage_down")
        self.assertEqual(hit[0]["level"], "critical")
        self.assertNotIn("flap_count", hit[0]["details"])

    def test_persistent_alert_without_resolved_not_downgraded(self):
        """纯持续告警(3 fire 无任何 resolved)不降级——持续事故不是抖动,
        降级会吞掉真 critical 的翻页;rc=1 保持。"""
        mdir = _fresh_dir()
        _seed_flap_history(mdir, "homepage_down", "/",
                           fires=(39, 26, 13), fire_resolved=False)
        _insert_run(mdir, {"pages": {"/": {"status": 200, "title": "T"}}})
        _insert_run(mdir, {"pages": {"/": {"status": 404, "title": "T"}}})
        rc, payload = self._flap_diff(mdir)
        self.assertEqual(rc, 1)
        hit = _hits(payload["alerts"], "homepage_down")
        self.assertEqual(hit[0]["level"], "critical")

    def test_flapping_window_seven_days(self):
        """fire/resolved 全在 7 天窗外(>168h)→ 不计数,不降级。"""
        mdir = _fresh_dir()
        _seed_flap_history(mdir, "homepage_down", "/",
                           fires=(200, 192), resolved=(180,))
        _insert_run(mdir, {"pages": {"/": {"status": 200, "title": "T"}}})
        _insert_run(mdir, {"pages": {"/": {"status": 404, "title": "T"}}})
        rc, payload = self._flap_diff(mdir)
        self.assertEqual(rc, 1)
        hit = _hits(payload["alerts"], "homepage_down")
        self.assertEqual(hit[0]["level"], "critical")

    def test_flap_history_count_unit(self):
        """flap_history_count:fire 行(suppressed=0,level!=low)与 _resolved 行分开计数。"""
        mdir = _fresh_dir()
        _seed_flap_history(mdir, "gsc_clicks_drop", "file",
                           fires=(10, 30), resolved=(20,))
        conn = M.open_db(mdir)
        cutoff = (datetime.now() - timedelta(days=7)).isoformat(timespec="seconds")
        fires, resolved = M.flap_history_count(conn, "gsc_clicks_drop", "file", cutoff)
        conn.close()
        self.assertEqual((fires, resolved), (2, 1))


# ================= ④ ack 超时(notify) =================

class AckDeadlineTests(unittest.TestCase):
    """critical 即时消息带 ack_deadline(默认 30min/可调);warn 不带;
    pending_critical 重发送达时刷新期限。"""

    def test_critical_message_carries_ack_deadline(self):
        """默认 30min:消息含 ack 期限行与 ack 命令提示;incidents 记录 ack_deadline。"""
        mdir = _nfy_dir({"slack": {}})
        fake = _FakeTargets(["slack"])
        alert = {"level": "critical", "code": "noindex_added", "key": "/p", "message": "x"}
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            rc = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", _alerts_file(mdir, [alert])]))
        finally:
            N.channel_targets = orig
        self.assertEqual(rc, 0)
        msg = fake.sent[0][1]
        self.assertIn("[CRITICAL] noindex_added", msg)
        self.assertIn("ack 期限:", msg)
        self.assertIn("notify.py ack", msg)
        m = re.search(r"ack 期限: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", msg)
        self.assertIsNotNone(m, "ack 期限行必须是 ISO 时间: %r" % msg)
        remain = (datetime.fromisoformat(m.group(1)) - datetime.now()).total_seconds() / 60
        self.assertTrue(25 <= remain <= 30.5, "默认期限≈30min,实得 %.1f" % remain)
        inc = N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"]
        rec = inc[N.incident_key(alert)]
        self.assertEqual(rec["level"], "critical")
        self.assertIn("ack_deadline", rec)

    def test_refire_keeps_original_ack_deadline(self):
        """持续重发的 critical 不重置 ack 时钟:再次触发沿用首次期限(消息同源),
        期限过后同一 run 的 --flush 即升级——重置时钟会让持续 critical 永不超期。"""
        mdir = _nfy_dir({"slack": {}})
        alert = {"level": "critical", "code": "key_page_down", "key": "/x", "message": "503"}
        af = _alerts_file(mdir, [alert])
        fake = _FakeTargets(["slack"])
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            self.assertEqual(N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", af])), 0)     # 首次送达
            # 模拟 30 分钟过去:把已记录期限改到过去
            p = os.path.join(mdir, N.INCIDENTS_FILE)
            data = N.load_incidents(p)
            data["incidents"][N.incident_key(alert)]["ack_deadline"] = \
                (datetime.now() - timedelta(minutes=1)).isoformat(timespec="seconds")
            N.save_incidents(p, data)
            rc = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", af, "--flush", "warn"]))
        finally:
            N.channel_targets = orig
        self.assertEqual(rc, 0)
        # 即时重发(消息沿用旧期限)+ 超期升级都发生
        self.assertTrue(any("ack 期限" in m for _, m in fake.sent))
        esc = [m for _, m in fake.sent if "ESCALATION" in m]
        self.assertEqual(len(esc), 1, "重发未重置期限 → 超期必须升级")
        self.assertIn(N.incident_key(alert), esc[0])

    def test_ack_timeout_minutes_config(self):
        """config ack_timeout_minutes=10 → 期限≈10min(消息与 incidents 一致)。"""
        mdir = _nfy_dir({"slack": {}}, extra_cfg={"ack_timeout_minutes": 10})
        fake = _FakeTargets(["slack"])
        alert = {"level": "critical", "code": "key_page_down", "key": "/a", "message": "404"}
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", _alerts_file(mdir, [alert])]))
        finally:
            N.channel_targets = orig
        m = re.search(r"ack 期限: (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", fake.sent[0][1])
        remain = (datetime.fromisoformat(m.group(1)) - datetime.now()).total_seconds() / 60
        self.assertTrue(9 <= remain <= 10.5, "自定义期限≈10min,实得 %.1f" % remain)
        inc = N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertIn("ack_deadline", inc[N.incident_key(alert)])

    def test_warn_alert_has_no_ack_deadline(self):
        """warn 走日批:flush 摘要无 ack 期限行,incidents 记录不带 ack_deadline。"""
        mdir = _nfy_dir({"slack": {}})
        alert = {"level": "warn", "code": "gsc_clicks_drop", "key": "file", "message": "-30%"}
        fake = _FakeTargets(["slack"])
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            af = _alerts_file(mdir, [alert])
            N.cmd_notify(N.build_parser().parse_args(["run", "--dir", mdir, "--alerts", af]))
            rc = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", af, "--flush", "warn"]))
        finally:
            N.channel_targets = orig
        self.assertEqual(rc, 0)
        self.assertTrue(fake.sent)
        self.assertNotIn("ack 期限", fake.sent[0][1])
        inc = N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertNotIn("ack_deadline", inc[N.incident_key(alert)])

    def test_pending_critical_resend_refreshes_ack_deadline(self):
        """R5 批×R4 ack:渠道全败降级暂存 → flush 重发送达时刷新 ack 期限并记 incident。"""
        mdir = _nfy_dir({"slack": {}})
        crit = [{"level": "critical", "code": "key_page_down", "key": "/pricing",
                 "message": "404", "action": "回滚", "boundary": "auto"}]
        af = _alerts_file(mdir, crit)
        orig = N.channel_targets
        N.channel_targets = lambda cfg: [
            ("slack", lambda msg: (_ for _ in ()).throw(IOError("net down")))]
        try:
            self.assertEqual(N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", af])), 1)      # 全败 → 暂存
        finally:
            N.channel_targets = orig
        st = N.load_state(os.path.join(mdir, N.STATE_FILE))
        self.assertEqual(len(st["pending_critical"]), 1)
        fake = _FakeTargets(["slack"])
        N.channel_targets = fake
        try:
            rc = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", _alerts_file(mdir, []), "--flush", "warn"]))
        finally:
            N.channel_targets = orig
        self.assertEqual(rc, 0)
        resent = [m for _, m in fake.sent if "重发" in m or "key_page_down" in m]
        self.assertTrue(resent and any("ack 期限" in m for m in resent))
        inc = N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertIn("ack_deadline", inc[N.incident_key(crit[0])])


class AckEscalationTests(unittest.TestCase):
    """--flush 升级超期未 ack 的 critical(全渠道无视 route,只升一次);ack 停升级。"""

    @staticmethod
    def _overdue_incident(mdir, code="title_missing", key="/about", level="critical"):
        alert = {"level": level, "code": code, "key": key, "message": "m"}
        now = datetime.now()
        rec = {"code": code, "key": key, "level": level, "message": "m",
               "sent_at": now.isoformat(timespec="seconds"),
               "ack_deadline": (now - timedelta(minutes=5)).isoformat(timespec="seconds")}
        N.save_incidents(os.path.join(mdir, N.INCIDENTS_FILE), {"incidents": {
            N.incident_key(alert): rec}})
        return N.incident_key(alert), rec

    def test_overdue_unacked_selection(self):
        """只挑 critical+未 ack+未 escalated+期限已过:未到期/已 ack/已升级/warn/无期限不选。"""
        now = datetime.now()
        iso = lambda dt: dt.isoformat(timespec="seconds")
        data = {"incidents": {
            "a@1": {"level": "critical", "ack_deadline": iso(now - timedelta(minutes=1))},
            "b@2": {"level": "critical", "ack_deadline": iso(now + timedelta(minutes=30))},
            "c@3": {"level": "critical", "ack_deadline": iso(now - timedelta(minutes=1)),
                    "acked_at": iso(now)},
            "d@4": {"level": "critical", "ack_deadline": iso(now - timedelta(minutes=1)),
                    "escalated_at": iso(now)},
            "e@5": {"level": "warn", "ack_deadline": iso(now - timedelta(minutes=1))},
            "f@6": {"level": "critical"},
        }}
        self.assertEqual([k for k, _ in N.overdue_unacked(data)], ["a@1"])

    def test_flush_escalates_all_channels_and_marks(self):
        """超期未 ack → --flush 升级:全渠道再发(升级无视 route,被筛渠道也收)
        + 标记 escalated;消息带 ack 提示与单向 webhook 注记。"""
        mdir = _nfy_dir({"slack-tech": {"type": "slack", "route": {"codes": ["noindex_*"]}},
                         "slack-all": {"type": "slack"}})
        k, _ = self._overdue_incident(mdir)                    # code=title_missing 不匹配 noindex_*
        fake = _FakeTargets(["slack-tech", "slack-all"])
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            rc = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", _alerts_file(mdir, []), "--flush", "warn"]))
        finally:
            N.channel_targets = orig
        self.assertEqual(rc, 0)
        esc = [(n, m) for n, m in fake.sent if "ESCALATION" in m]
        self.assertEqual(sorted(n for n, _ in esc), ["slack-all", "slack-tech"],
                         "升级必须无视 route 全渠道可达")
        self.assertIn("title_missing", esc[0][1])
        self.assertIn("notify.py ack %s" % k, esc[0][1])
        self.assertIn("/ack", esc[0][1])                       # GH 形态 issue /ack 约定注记
        inc = N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertIn("escalated_at", inc[k])

    def test_escalation_happens_only_once(self):
        """已标记 escalated 的超期 critical:再次 --flush 不再升级(只升一次)。"""
        mdir = _nfy_dir({"slack": {}})
        k, _ = self._overdue_incident(mdir)
        fake = _FakeTargets(["slack"])
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            rc1 = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", _alerts_file(mdir, []), "--flush", "warn"]))
            n_after_first = len([m for _, m in fake.sent if "ESCALATION" in m])
            rc2 = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", _alerts_file(mdir, []), "--flush", "warn"]))
        finally:
            N.channel_targets = orig
        self.assertEqual((rc1, rc2), (0, 0))
        self.assertEqual(n_after_first, 1)
        self.assertEqual(len([m for _, m in fake.sent if "ESCALATION" in m]), 1)

    def test_ack_stops_escalation_and_is_idempotent(self):
        """ack 子命令:acked_at 落盘 → --flush 不升级;未知 key 跳过不判错;重复 ack 幂等。"""
        mdir = _nfy_dir({"slack": {}})
        k, _ = self._overdue_incident(mdir)
        self.assertEqual(N.cmd_ack(N.build_parser().parse_args(
            ["ack", "--dir", mdir, k])), 0)
        inc = N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertIn("acked_at", inc[k])
        # 未知/不存在 key:跳过不判错;空清单:输入错误
        self.assertEqual(N.cmd_ack(N.build_parser().parse_args(
            ["ack", "--dir", mdir, "ghost@000000000000"])), 0)
        self.assertEqual(N.cmd_ack(N.build_parser().parse_args(
            ["ack", "--dir", mdir])), 4)
        # 重复 ack:幂等提示,rc=0
        self.assertEqual(N.cmd_ack(N.build_parser().parse_args(
            ["ack", "--dir", mdir, k])), 0)
        # ack 过的超期 critical:flush 不升级
        fake = _FakeTargets(["slack"])
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            rc = N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", _alerts_file(mdir, []), "--flush", "warn"]))
        finally:
            N.channel_targets = orig
        self.assertEqual(rc, 0)
        self.assertFalse(any("ESCALATION" in m for _, m in fake.sent))

    def test_escalation_without_channels_deferred(self):
        """无已配置渠道:升级暂缓不标记 escalated(下次 flush 再试,与 R5 不丢口径一致)。"""
        mdir = _nfy_dir({})
        k, _ = self._overdue_incident(mdir)
        rc = N.cmd_notify(N.build_parser().parse_args(
            ["run", "--dir", mdir, "--alerts", _alerts_file(mdir, []), "--flush", "all"]))
        self.assertEqual(rc, 0)
        inc = N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertNotIn("escalated_at", inc[k])

    def test_ack_after_escalation_still_recorded(self):
        """已升级后再 ack:仍记录(防后续同 key 再升),提示带升级时间。"""
        mdir = _nfy_dir({"slack": {}})
        k, rec = self._overdue_incident(mdir)
        fake = _FakeTargets(["slack"])
        orig = N.channel_targets
        N.channel_targets = fake
        try:
            N.cmd_notify(N.build_parser().parse_args(
                ["run", "--dir", mdir, "--alerts", _alerts_file(mdir, []), "--flush", "warn"]))
        finally:
            N.channel_targets = orig
        self.assertTrue(any("ESCALATION" in m for _, m in fake.sent))
        self.assertEqual(N.cmd_ack(N.build_parser().parse_args(
            ["ack", "--dir", mdir, k])), 0)
        inc = N.load_incidents(os.path.join(mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertIn("acked_at", inc[k])
        self.assertIn("escalated_at", inc[k])


if __name__ == "__main__":
    unittest.main(verbosity=1)
