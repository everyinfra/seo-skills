#!/usr/bin/env python3
"""monitor.py R5 监控节 6 项修复的回归测试(standalone,合成 config/db,零网络;
tests/run_tests.py 自动发现本文件)。覆盖:
① cooldown 按 (code,key) 取最新 ts 判龄——旧行为命中最旧行即 break:告警持续超
  一个冷却窗后,最旧行龄期已超窗,冷却整体失效(每个 diff 都重报);修复后取最新
  行判龄,持续告警在每次重报后的窗口期内仍被抑制,且确实超窗的重报不被吞
② diff 选 prev 优先同 kind 的最近 ok run(weekly 不拿 daily 当基线——否则 weekly
  的 sitemap/llms/ssl 字段对 daily 的缺失会被当"没变/被删");无同 kind 时回退最近
  ok 并在 payload 标 baseline_kind_mismatch:true + stderr WARNING 一行
③ 字段漂移 changed 加 page_rendered 门:state=error/http_error 的残缺快照缺
  title/meta 等键,不再被当 "(旧值→空)" 假漂移(与 removed/h1 门对齐)
④ 被抑制树折叠的 (code,key) 并入"仍在场"集合——不算自愈/resolved、不丢冷却态;
  真消失时照常 healed+resolved
⑤ apply_accepted 先于 apply_inhibition:accepted 告警不因根因在场被折叠蒸发,
  保留"接受≠消失"的周报计数
⑥ check_ssl 弃用 utcnow → datetime.now(timezone.utc),notAfter 统一 aware 比较"""
import contextlib
import inspect
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import monitor as M  # noqa: E402

CFG = {"site": "https://example.com", "thresholds": dict(M.DEFAULT_THRESHOLDS)}


def _fresh_dir():
    tmp = tempfile.mkdtemp(prefix="mon_r5_")
    mdir = os.path.join(tmp, ".seo-monitor")
    rc = M.cmd_init(M.build_parser().parse_args(
        ["init", "--site", "https://example.com", "--market", "us", "--dir", mdir]))
    assert rc == 0
    return mdir


def _insert_run(mdir, snapshots, ts_offset_days=0, status="ok", kind="daily"):
    """snapshots: {check: {key: value}} 直接落快照(绕过网络);kind 可选 daily/weekly。"""
    conn = M.open_db(mdir)
    ts = (datetime.now() - timedelta(days=ts_offset_days)).isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO runs(ts,kind,status,checks_run,budget_used_sec,summary) "
        "VALUES(?,?,?,?,0,'')", (ts, kind, status, kind))
    rid = cur.lastrowid
    for check, kv in snapshots.items():
        for key, value in kv.items():
            conn.execute(
                "INSERT INTO snapshots(run_id,ts,\"check\",key,value,hash) VALUES(?,?,?,?,?,?)",
                (rid, ts, check, key, json.dumps(value), "h%d%s%s" % (rid, check, key)))
    conn.commit()
    conn.close()
    return rid


def _insert_alert(mdir, run_id, code, key, level, ts_offset_hours=0, resolved=0):
    """手工落一条 alerts 行(控制 ts,模拟冷却历史;绕过 diff)。"""
    conn = M.open_db(mdir)
    ts = (datetime.now() - timedelta(hours=ts_offset_hours)).isoformat(timespec="seconds")
    conn.execute(
        "INSERT INTO alerts(run_id, ts, level, code, key, message, details, suppressed, resolved) "
        "VALUES(?,?,?,?,?,?,?,0,?)",
        (run_id, ts, level, code, key, "m", "{}", resolved))
    conn.commit()
    conn.close()


def _run_cmd(args_list):
    """直接经 parser 分发 cmd_*(不打 subprocess),捕获 stdout/stderr → (rc, out, err)。"""
    out, err = io.StringIO(), io.StringIO()
    args = M.build_parser().parse_args(args_list)
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = args.func(args)
    return rc, out.getvalue(), err.getvalue()


def _hits(alerts, code):
    return [a for a in alerts if a["code"] == code]


# ---------- ① cooldown 按 (code,key) 最新 ts 判龄 ----------

class CooldownLatestTsTests(unittest.TestCase):
    """持续超一个冷却窗后冷却不得整体失效(取最新行判龄,不是最旧行)。"""

    def test_persistent_alert_stays_suppressed_beyond_first_window(self):
        """旧行 72h(超 critical 12h 窗)+ 新行刚入库 → 按最新行判:抑制。
        修复前:命中最旧行即 break → 72h>12h → 不抑制 → 每个 diff 都重报。"""
        mdir = _fresh_dir()
        r1 = _insert_run(mdir, {"pages": {"/": {"status": 200, "title": "T"}}})
        r2 = _insert_run(mdir, {"pages": {"/": {"status": 404, "title": "T"}}})
        _insert_alert(mdir, r1, "homepage_down", "/", "critical", ts_offset_hours=72)
        out = os.path.join(mdir, "alerts.json")
        rc1, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc1, 1, "旧行已超窗:本轮重报(入库新行 ts=now)")
        rc2, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc2, 0, "最新行(now)仍在 12h 窗内 → 抑制;旧行超窗不得让冷却失效")
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["counts"]["critical"], 0)
        self.assertEqual(payload["suppressed"], ["homepage_down:/"])
        self.assertTrue(all(a.get("suppressed") for a in payload["alerts"]))
        conn = M.open_db(mdir)
        n_open = conn.execute(
            "SELECT COUNT(*) AS c FROM alerts WHERE code='homepage_down' AND key='/' "
            "AND resolved=0").fetchone()["c"]
        conn.close()
        self.assertEqual(n_open, 2, "新旧两行都未结(在场,不丢冷却态)")

    def test_truly_expired_cooldown_still_realerts(self):
        """唯一一行确实超窗 → 照常重报(修复不吞真信号)。"""
        mdir = _fresh_dir()
        r1 = _insert_run(mdir, {"pages": {"/": {"status": 200, "title": "T"}}})
        r2 = _insert_run(mdir, {"pages": {"/": {"status": 404, "title": "T"}}})
        _insert_alert(mdir, r2, "homepage_down", "/", "critical", ts_offset_hours=13)
        rc, _, _ = _run_cmd(["diff", "--dir", mdir])
        self.assertEqual(rc, 1, "13h > critical 12h 冷却窗:不抑制")


# ---------- ② prev 基线优先同 kind ----------

class PrevKindSelectionTests(unittest.TestCase):
    """weekly 不拿 daily 当基线;无同 kind 回退 + baseline_kind_mismatch 标记。"""

    def test_prefers_same_kind_over_newer_other_kind(self):
        """curr=daily:prev 取更早的 daily(100),不是更新的 weekly(50)——
        100→70=−30% 触发 warn;若错拿 weekly 50 当基线,+40% 无告警。"""
        mdir = _fresh_dir()
        r1 = _insert_run(mdir, {"gsc": {"file": {"clicks_total": 100}}}, kind="daily")
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 50}}}, kind="weekly")
        r3 = _insert_run(mdir, {"gsc": {"file": {"clicks_total": 70}}}, kind="daily")
        out = os.path.join(mdir, "alerts.json")
        rc, _, err = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 2, "prev=daily r1:100→70 −30% 过 20% 阈值 → warn")
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["curr_run"], r3)
        self.assertEqual(payload["prev_run"], r1, "prev 必须是同 kind 的 daily run")
        self.assertIs(payload["baseline_kind_mismatch"], False)
        self.assertNotIn("WARNING", err)

    def test_fallback_to_other_kind_flags_mismatch(self):
        """curr=daily 而此前只有 weekly → 回退最近 ok + payload 标记 + WARNING 恰一行。"""
        mdir = _fresh_dir()
        r1 = _insert_run(mdir, {"gsc": {"file": {"clicks_total": 100}}}, kind="weekly")
        r2 = _insert_run(mdir, {"gsc": {"file": {"clicks_total": 60}}}, kind="daily")
        out = os.path.join(mdir, "alerts.json")
        rc, _, err = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 2)
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["prev_run"], r1)
        self.assertIs(payload["baseline_kind_mismatch"], True)
        self.assertEqual(err.count("WARNING"), 1, "回退时 stderr 恰一行 WARNING")
        self.assertIn("kind", err)

    def test_explicit_prev_run_id_no_kind_warning(self):
        """--prev-run-id 显式指定:用户自选基线,不按 kind 警告。"""
        mdir = _fresh_dir()
        r1 = _insert_run(mdir, {"gsc": {"file": {"clicks_total": 100}}}, kind="weekly")
        r2 = _insert_run(mdir, {"gsc": {"file": {"clicks_total": 60}}}, kind="daily")
        out = os.path.join(mdir, "alerts.json")
        rc, _, err = _run_cmd(["diff", "--dir", mdir, "--run-id", str(r2),
                               "--prev-run-id", str(r1), "--out", out])
        self.assertEqual(rc, 2)
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertIs(payload["baseline_kind_mismatch"], False)
        self.assertNotIn("WARNING", err)


# ---------- ③ 字段漂移 changed 的渲染门 ----------

class FieldDriftRenderGateTests(unittest.TestCase):
    """state=error/http_error 的残缺快照不产假 title_meta_drift(与 removed/h1 门对齐)。"""

    def test_unrendered_curr_no_false_drift(self):
        prev = {"pages": {"/p": {"status": 200, "title": "T", "meta_desc": "M"}}}
        bads = ({"state": "error", "error": "timeout"},                    # 抓取失败残缺快照
                {"state": "http_error", "status": 404, "title": ""})      # 404 残缺快照
        for bad in bads:
            alerts = M.compute_alerts(prev, {"pages": {"/p": bad}}, CFG)
            self.assertFalse(_hits(alerts, "title_meta_drift"),
                             "%s 不该产字段漂移(残缺快照缺键≠字段变空)" % bad)
            self.assertFalse(_hits(alerts, "meta_removed"))

    def test_rendered_change_still_drifts(self):
        """门不放过头:真实渲染页面的字段变化照常 info 漂移。"""
        prev = {"pages": {"/p": {"status": 200, "title": "A", "meta_desc": "M"}}}
        curr = {"pages": {"/p": {"status": 200, "title": "B", "meta_desc": "M"}}}
        drift = _hits(M.compute_alerts(prev, curr, CFG), "title_meta_drift")
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0]["level"], "info")
        self.assertEqual(drift[0]["details"]["fields"], ["title"])


# ---------- ④ 被抑制折叠的指纹并入"仍在场"集合 ----------

class InhibitedStillPresentTests(unittest.TestCase):
    """抑制树折叠的 (code,key) 不算自愈/resolved,不丢冷却态;真消失才 healed。"""

    def test_inhibited_fingerprint_not_healed_or_resolved(self):
        mdir = _fresh_dir()
        _insert_run(mdir, {"pages": {"/": {"status": 200}, "/a": {"status": 200}}})
        _insert_run(mdir, {"pages": {"/": {"status": 200}, "/a": {"status": 404}}})
        rc1, _, _ = _run_cmd(["diff", "--dir", mdir])
        self.assertEqual(rc1, 1, "阶段A:/a 单独宕 → key_page_down:/a critical 入库")
        # 阶段B:首页也宕 → homepage_down(根因)折叠 key_page_down:/a(派生)
        _insert_run(mdir, {"pages": {"/": {"status": 503}, "/a": {"status": 404}}})
        out = os.path.join(mdir, "alerts.json")
        rc2, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc2, 1, "homepage_down critical 仍在")
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["healed"], [],
                         "被折叠的 key_page_down:/a 仍在场,不算自愈")
        self.assertTrue(any(i["code"] == "key_page_down" and i["key"] == "/a"
                            for i in payload["inhibited"]))
        conn = M.open_db(mdir)
        n_open = conn.execute(
            "SELECT COUNT(*) AS c FROM alerts WHERE code='key_page_down' AND key='/a' "
            "AND resolved=0").fetchone()["c"]
        n_resolved = conn.execute(
            "SELECT COUNT(*) AS c FROM alerts WHERE code='key_page_down_resolved'").fetchone()["c"]
        conn.close()
        self.assertEqual(n_open, 1, "冷却态未结行保留(resolved=0)")
        self.assertEqual(n_resolved, 0, "不得插入 *_resolved 自愈行")
        # 阶段C:根因与派生都真消失 → 此时才 healed + resolved
        _insert_run(mdir, {"pages": {"/": {"status": 200}, "/a": {"status": 200}}})
        rc3, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc3, 0)
        with open(out, encoding="utf-8") as f:
            payload3 = json.load(f)
        self.assertEqual(set(payload3["healed"]), {"homepage_down:/", "key_page_down:/a"})
        conn = M.open_db(mdir)
        n_open3 = conn.execute(
            "SELECT COUNT(*) AS c FROM alerts WHERE code='key_page_down' AND key='/a' "
            "AND resolved=0").fetchone()["c"]
        conn.close()
        self.assertEqual(n_open3, 0, "真消失时照常 resolved")


# ---------- ⑤ accepted 先于抑制 ----------

class AcceptedBeforeInhibitionTests(unittest.TestCase):
    """accepted 告警不因根因在场被抑制树折叠蒸发(接受≠消失)。"""

    def test_accepted_survives_inhibition_unit(self):
        cfg = {"site": "https://example.com", "thresholds": dict(M.DEFAULT_THRESHOLDS),
               "accepted_codes": ["noindex_added:/p"]}
        prev = {"robots": {"robots": {"hash": "h1", "sitewide_block": False}},
                "pages": {"/p": {"status": 200, "indexable": True}}}
        curr = {"robots": {"robots": {"hash": "h2", "sitewide_block": True}},
                "pages": {"/p": {"status": 200, "indexable": False,
                                 "noindex_source": "meta"}}}
        inhib = []
        alerts = M.compute_alerts(prev, curr, cfg, inhibited_out=inhib)
        hit = _hits(alerts, "noindex_added")
        self.assertEqual(len(hit), 1, "已接受的派生告警不被根因折叠蒸发")
        self.assertTrue(hit[0]["accepted"])
        self.assertEqual(hit[0]["level"], "low")
        self.assertEqual(hit[0]["from_level"], "critical")
        self.assertFalse(any(i["code"] == "noindex_added" for i in inhib))
        self.assertTrue(any(a["code"] == "robots_sitewide_block" and a["level"] == "critical"
                            for a in alerts), "根因告警照常保留")
        # 未接受时保持旧行为:sitewide 根因折叠 noindex_added
        inhib2 = []
        alerts2 = M.compute_alerts(prev, curr,
                                   {"site": "https://example.com",
                                    "thresholds": dict(M.DEFAULT_THRESHOLDS)},
                                   inhibited_out=inhib2)
        self.assertFalse(_hits(alerts2, "noindex_added"))
        self.assertTrue(any(i["code"] == "noindex_added" for i in inhib2))

    def test_end_to_end_payload_and_report_counting(self):
        mdir = _fresh_dir()
        cfg = M.load_config(mdir)
        cfg["accepted_codes"] = ["noindex_added:/p"]
        M.save_config(mdir, cfg)
        _insert_run(mdir, {"robots": {"robots": {"hash": "h1", "sitewide_block": False}},
                           "pages": {"/p": {"status": 200, "indexable": True}}})
        _insert_run(mdir, {"robots": {"robots": {"hash": "h2", "sitewide_block": True}},
                           "pages": {"/p": {"status": 200, "indexable": False,
                                            "noindex_source": "meta"}}})
        out = os.path.join(mdir, "alerts.json")
        rc, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 1, "robots_sitewide_block critical 仍计退出码")
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["accepted"], 1)
        hit = [a for a in payload["alerts"] if a["code"] == "noindex_added"]
        self.assertEqual(len(hit), 1)
        self.assertTrue(hit[0]["accepted"])
        # 周报"已接受告警数"仍计数(接受≠消失)
        _, jout, _ = _run_cmd(["report", "--dir", mdir, "--days", "7", "--json"])
        self.assertEqual(json.loads(jout)["accepted_alerts"], 1)


# ---------- ⑥ check_ssl aware 比较 ----------

class SslAwareNotAfterTests(unittest.TestCase):
    """notAfter(GMT)按 UTC 定位成 aware,与 now(timezone.utc) 统一比较。"""

    class _TLS:
        def __init__(self, cert):
            self._cert = cert

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def getpeercert(self):
            return self._cert

    class _Ctx:
        def __init__(self, cert):
            self._cert = cert

        def wrap_socket(self, sock, server_hostname=None):
            return SslAwareNotAfterTests._TLS(self._cert)

    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    @classmethod
    def _check_with_cert(cls, cert):
        orig_conn = M.socket.create_connection
        orig_ctx = M.ssl.create_default_context
        M.socket.create_connection = lambda a, timeout=None: cls._Conn()
        M.ssl.create_default_context = lambda: cls._Ctx(cert)
        try:
            return M.check_ssl("https://example.com")
        finally:
            M.socket.create_connection = orig_conn
            M.ssl.create_default_context = orig_ctx

    def test_days_left_aware_utc_math(self):
        future = datetime.now(timezone.utc) + timedelta(days=40)
        not_after = future.strftime("%b %d %H:%M:%S %Y GMT")
        out = self._check_with_cert({"notAfter": not_after,
                                     "issuer": ((("commonName", "Test CA"),),)})
        self.assertEqual(out["state"], "ok")
        self.assertEqual(out["metrics"]["days_left"], (future - datetime.now(timezone.utc)).days)
        self.assertEqual(out["metrics"]["issuer"], "Test CA")

    def test_unparsable_not_after_is_error(self):
        out = self._check_with_cert({"notAfter": "not a date"})
        self.assertEqual(out["state"], "error")
        self.assertIn("不可解析", out["metrics"]["error"])

    def test_no_deprecated_utcnow_in_check_ssl(self):
        self.assertNotIn("utcnow(", inspect.getsource(M.check_ssl))


if __name__ == "__main__":
    unittest.main(verbosity=1)
