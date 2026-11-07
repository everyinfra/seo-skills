#!/usr/bin/env python3
"""R5 修复回归(详单三项),stdlib unittest、合成数据、零网络(发送层 monkeypatch):
① notify.py critical 即时告警渠道全败 → 降级暂存 pending_critical 批(指纹去重、
   incident_key 随批保留、未送达不记 incident),下次 --flush 优先于 warn/info 重发,
   送达即出批并照常记 incident,再败整批保留;
② remediation.py save_data 原子写(tempfile+os.replace:replace 前异常 → 原文件
   完好、临时文件清理)+ data_lock 数据文件级 flock(互斥、超时 → 警告跳过);
③ remediation update 与 verify 并发(线程 Barrier 同起 + 真两 subprocess 交替写):
   锁后 load→改→save 串行化,无覆盖丢单。standalone,被 tests/run_tests.py 自动装载。"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import notify as N        # noqa: E402
import remediation as R   # noqa: E402

A = "https://s.com/a"
B = "https://s.com/b"
VERIFY_HINT = "该 finding 在新体检中消失即自动核销"


# ---------- notify 助手 ----------

def notify_dir(channels):
    tmp = tempfile.mkdtemp(prefix="fix_nfy_")
    mdir = os.path.join(tmp, ".seo-monitor")
    os.makedirs(mdir)
    with open(os.path.join(mdir, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"site": "https://example.com", "run_cadence_hours": 24,
                   "channels": channels}, f)
    return mdir


def alerts_file(mdir, alerts):
    path = os.path.join(mdir, "alerts-%d.json" % int(time.time() * 1e6))
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"site": "https://example.com",
                   "generated": datetime.now().isoformat(timespec="seconds"),
                   "alerts": alerts}, f)
    return path


def critical_alert(code="key_page_down", key="/pricing"):
    return {"level": "critical", "code": code, "key": key, "message": "404",
            "action": "回滚", "boundary": "auto"}


@contextlib.contextmanager
def fake_targets(behaviors):
    """替换 N.channel_targets:behaviors={渠道名: (st, detail) 或 None(全抛 IOError)};
    yield sent=[(渠道名, 消息)] 记录全部发送尝试(零网络)。"""
    sent = []

    def build(cfg):
        out = []
        for name, beh in behaviors.items():
            def mk(nm, b):
                def fn(msg):
                    sent.append((nm, msg))
                    if b is None:
                        raise IOError("net down")
                    return b
                return fn
            out.append((name, mk(name, beh)))
        return out

    orig = N.channel_targets
    N.channel_targets = build
    try:
        yield sent
    finally:
        N.channel_targets = orig


def run_notify(mdir, *extra):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = N.cmd_notify(N.build_parser().parse_args(
            ["run", "--dir", mdir, *extra]))
    return rc, buf.getvalue()


# ---------- remediation 助手 ----------

def hand_item(i, rule="title", area="rankability", urls=(A,), status="proposed"):
    return {"id": i, "rule_id": rule, "area": area, "action": "修", "phase": "now",
            "severity": "WARN", "affected_urls": list(urls), "status": status,
            "created": "2026-01-01T00:00:00+00:00",
            "deadline": "2099-01-01T00:00:00+00:00",
            "closed": None, "verify_hint": VERIFY_HINT, "note": ""}


def make_audit(by_url):
    results = {u: {"findings": [{"severity": s, "area": a, "message": m}
                                for s, a, m in fs], "meta": {}}
               for u, fs in by_url.items()}
    return json.dumps({"audited": len(results), "critical": 0, "results": results},
                      ensure_ascii=False)


# ① notify:critical 渠道全败降级暂存 + flush 优先重发
class CriticalDegradeTests(unittest.TestCase):
    """R5-①:全败暂存 pending_critical / 部分成功不暂存 / 无渠道同样暂存 /
    flush 优先重发(先于 warn 批)且送达出批记 incident / 再败保留 / 旧 state 兼容。"""

    def setUp(self):
        self.mdir = notify_dir({"slack": {}})
        self.addCleanup(shutil.rmtree, os.path.dirname(self.mdir), ignore_errors=True)
        self.state_path = os.path.join(self.mdir, N.STATE_FILE)

    def test_all_channels_fail_stashes_pending_critical(self):
        """两渠道全抛错:rc=1,告警进 pending_critical(fp/incident_key 保留),
        未送达不记 incident,输出明示降级暂存。"""
        alerts = [critical_alert()]
        af = alerts_file(self.mdir, alerts)
        with fake_targets({"slack": None, "discord": None}) as sent:
            rc, out = run_notify(self.mdir, "--alerts", af)
        self.assertEqual(rc, 1)
        self.assertEqual(len(sent), 2)                          # 两渠道都试过
        st = N.load_state(self.state_path)
        self.assertEqual(len(st["pending_critical"]), 1)
        p = st["pending_critical"][0]
        self.assertEqual((p["code"], p["key"], p["fp"]),
                         ("key_page_down", "/pricing", "key_page_down:/pricing"))
        self.assertEqual(p.get("incident_key"), N.incident_key(alerts[0]))
        self.assertFalse(os.path.exists(os.path.join(self.mdir, N.INCIDENTS_FILE)))
        self.assertIn("渠道全败", out)
        self.assertIn("pending_critical", out)

    def test_repeated_failures_dedup_no_unbounded_growth(self):
        """同指纹 critical 连续多轮全败:pending_critical 恒 1 条(指纹去重)。"""
        af = alerts_file(self.mdir, [critical_alert()])
        with fake_targets({"slack": None}):
            for extra in (("--alerts", af), ("--alerts", af, "--flush", "warn")):
                rc, _ = run_notify(self.mdir, *extra)
                self.assertEqual(rc, 1)
        self.assertEqual(len(N.load_state(self.state_path)["pending_critical"]), 1)

    def test_partial_channel_success_not_stashed(self):
        """任一渠道送达即视为已发:不暂存、不降级,incident 照常记录。"""
        alerts = [critical_alert()]
        af = alerts_file(self.mdir, alerts)
        with fake_targets({"slack": (200, "ok"), "discord": None}):
            rc, _ = run_notify(self.mdir, "--alerts", af)
        self.assertEqual(rc, 1)                                 # discord 仍算失败
        self.assertEqual(N.load_state(self.state_path)["pending_critical"], [])
        inc = N.load_incidents(os.path.join(self.mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertEqual(list(inc), [N.incident_key(alerts[0])])

    def test_no_channels_stashes_critical(self):
        """全无已配置渠道 = 无处送达:critical 同样降级暂存(与批口径一致)。"""
        af = alerts_file(self.mdir, [critical_alert()])
        rc, out = run_notify(self.mdir, "--alerts", af)          # 真实 channel_targets=[]
        self.assertEqual(rc, 0)
        st = N.load_state(self.state_path)
        self.assertEqual(len(st["pending_critical"]), 1)
        self.assertIn("降级暂存", out)

    def test_flush_resent_first_and_incident_recorded(self):
        """flush 时 pending_critical 优先于 warn 日批重发;送达出批并记 incident。"""
        crit, warn = critical_alert(), {"level": "warn", "code": "gsc_clicks_drop",
                                        "key": "file", "message": "-30%"}
        af = alerts_file(self.mdir, [crit, warn])
        with fake_targets({"slack": None}):
            rc, _ = run_notify(self.mdir, "--alerts", af)        # 全败:critical 降级
            self.assertEqual(rc, 1)
            self.assertEqual(len(N.load_state(self.state_path)["pending_warn"]), 1)
        with fake_targets({"slack": (200, "ok")}) as sent:
            rc, _ = run_notify(self.mdir, "--alerts", af, "--flush", "warn")
            self.assertEqual(rc, 0)
            msgs = [m for _, m in sent]
        i_resend = [n for n, m in enumerate(msgs) if "重发" in m and "key_page_down" in m]
        i_digest = [n for n, m in enumerate(msgs) if "[WARN] gsc_clicks_drop" in m]
        self.assertTrue(i_resend and i_digest, msgs)
        self.assertLess(i_resend[0], i_digest[0], "critical 降级批必须先于 warn 摘要重发")
        self.assertIn("CRITICAL", msgs[i_resend[0]])
        st = N.load_state(self.state_path)
        self.assertEqual(st["pending_critical"], [])             # 送达出批
        self.assertEqual(st["pending_warn"], [])                 # warn 批也成功清空
        inc = N.load_incidents(os.path.join(self.mdir, N.INCIDENTS_FILE))["incidents"]
        self.assertIn(N.incident_key(crit), inc)                 # 重发送达照常记 incident

    def test_resend_failure_keeps_batch(self):
        """flush 重发仍全败:pending_critical 保留(不丢告警),rc=1。"""
        af = alerts_file(self.mdir, [critical_alert()])
        with fake_targets({"slack": None}):
            run_notify(self.mdir, "--alerts", af)
            rc, out = run_notify(self.mdir, "--alerts", af, "--flush", "info")
        self.assertEqual(rc, 1)
        self.assertEqual(len(N.load_state(self.state_path)["pending_critical"]), 1)
        self.assertIn("保留", out)

    def test_old_state_file_without_key_still_loads(self):
        """旧版 state(无 pending_critical 键)加载补空,不炸。"""
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump({"pending_warn": [], "pending_info": []}, f)
        st = N.load_state(self.state_path)
        self.assertEqual(st["pending_critical"], [])


# ② remediation:save_data 原子写 + data_lock
class AtomicSaveTests(unittest.TestCase):
    """R5-②:replace 前异常原文件完好、临时文件清理、成功路径格式不变。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fix_rem_atomic-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.path = os.path.join(self.tmp, "remediations.json")
        self.old = {"items": [hand_item("REM-001")]}
        R.save_data(self.path, self.old)

    def test_content_format_unchanged(self):
        """原子写后序列化格式与旧实现一致(indent=1 + 尾换行,LF)。"""
        with open(self.path, encoding="utf-8") as f:
            text = f.read()
        self.assertEqual(text, json.dumps(self.old, ensure_ascii=False, indent=1) + "\n")
        self.assertEqual(json.loads(text), self.old)

    def test_failed_replace_keeps_old_file_and_cleans_temp(self):
        """os.replace 抛错(模拟崩溃/磁盘满):原文件内容完好(无半截写)、
        无遗留临时文件。"""
        new = {"items": [hand_item("REM-001"), hand_item("REM-002")]}
        orig_replace = os.replace

        def boom(*a, **k):
            raise OSError("disk full")

        os.replace = boom
        try:
            with self.assertRaises(OSError):
                R.save_data(self.path, new)
        finally:
            os.replace = orig_replace
        with open(self.path, encoding="utf-8") as f:
            self.assertEqual(json.load(f), self.old)             # 原文件未被破坏
        leftovers = [p for p in os.listdir(self.tmp)
                     if p.startswith(".remediations.json.tmp-")]
        self.assertEqual(leftovers, [])                          # 临时文件已清理


class DataLockTests(unittest.TestCase):
    """R5-②:flock 互斥(第二写者阻塞至释放)/ 超时 → 警告并跳过(SystemExit)。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fix_rem_lock-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.path = os.path.join(self.tmp, "remediations.json")
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"items": [hand_item("REM-001"), hand_item("REM-002")]}, f)

    def status(self, tid):
        with open(self.path, encoding="utf-8") as f:
            return next(i["status"] for i in json.load(f)["items"] if i["id"] == tid)

    def test_second_writer_blocks_until_lock_released(self):
        """持锁方未 save 前,并发 update 阻塞等锁(不读旧数据不写);释放后完成。"""
        result = {}

        def upd():
            result["rc"] = R.cmd_update(["REM-001", "--status", "accepted",
                                         "--file", self.path])

        with R.data_lock(self.path):                             # 模拟另一事务持锁中
            t = threading.Thread(target=upd)
            t.start()
            t.join(timeout=1.0)
            self.assertTrue(t.is_alive(), "等锁方必须阻塞,不得先写")
            self.assertEqual(self.status("REM-001"), "proposed")  # 未被覆盖写入
        t.join(timeout=10)
        self.assertFalse(t.is_alive())
        self.assertEqual(result.get("rc"), 0)
        self.assertEqual(self.status("REM-001"), "accepted")     # 释放后完成写入

    def test_lock_timeout_warns_and_skips(self):
        """等锁超时 → SystemExit 且消息含警告与跳过说明(照 monitor.py 惯例)。"""
        with R.data_lock(self.path):
            with self.assertRaises(SystemExit) as cm:
                with R.data_lock(self.path, timeout=0.6):
                    pass
        self.assertIn("警告", str(cm.exception))
        self.assertIn("跳过", str(cm.exception))


# ③ remediation:update 与 verify 并发,锁后无覆盖丢失
class ConcurrencyTests(unittest.TestCase):
    """R5-③:update 与 verify 两路并发写同一数据文件(线程 Barrier 同起 +
    真两 subprocess 交替写):锁后两写并存,无 read-modify-write 覆盖丢失。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="fix_rem_conc-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.path = os.path.join(self.tmp, "remediations.json")
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"items": [hand_item("REM-001", rule="title", area="rankability"),
                                 hand_item("REM-002", rule="robots",
                                           area="indexability", urls=(A, B)),
                                 hand_item("REM-003", rule="og", area="rankability")]}, f)
        self.old_audit = self.write("old.json", make_audit(
            {A: [("CRITICAL", "robots", "noindex")], B: [("CRITICAL", "robots", "noindex")]}))
        self.new_audit = self.write("new.json", make_audit({A: [], B: []}))

    def write(self, name, text):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p

    def items(self, path=None):
        with open(path or self.path, encoding="utf-8") as f:
            return {i["id"]: i for i in json.load(f)["items"]}

    def test_update_and_verify_threads_no_lost_update(self):
        """update(REM-001→accepted)与 verify(REM-002→verified)线程同起:
        终态两变并存——锁串行化了 load→改→save,后写者基于前写者的结果。"""
        results = {}
        barrier = threading.Barrier(2)

        def upd():
            barrier.wait()
            results["update"] = R.cmd_update(["REM-001", "--status", "accepted",
                                              "--file", self.path])

        def ver():
            barrier.wait()
            results["verify"] = R.cmd_verify(["--old", self.old_audit,
                                              "--new", self.new_audit,
                                              "--file", self.path])

        ts = [threading.Thread(target=upd), threading.Thread(target=ver)]
        for t in ts:
            t.start()
        for t in ts:
            t.join(timeout=30)
        self.assertFalse(any(t.is_alive() for t in ts))
        self.assertEqual(results["update"], 0)
        self.assertEqual(results["verify"], 0)                  # 新审计无新 finding
        got = self.items()
        self.assertEqual(got["REM-001"]["status"], "accepted")  # update 的写未丢
        self.assertEqual(got["REM-002"]["status"], "verified")  # verify 的写未丢
        self.assertTrue(got["REM-002"]["closed"])
        self.assertEqual(got["REM-003"]["status"], "proposed")

    def test_two_update_processes_no_lost_update(self):
        """真两进程交替写:并发 update 两张不同单,终态两单都已 accepted。"""
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        procs = [subprocess.Popen(
            [sys.executable, os.path.join(SCRIPTS, "remediation.py"),
             "update", tid, "--status", "accepted"],
            cwd=self.tmp, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8")
            for tid in ("REM-001", "REM-002")]
        for p in procs:
            out, err = p.communicate(timeout=60)
            self.assertEqual(p.returncode, 0, err or out)
        got = self.items()
        self.assertEqual(got["REM-001"]["status"], "accepted")  # 无覆盖丢失
        self.assertEqual(got["REM-002"]["status"], "accepted")
        self.assertEqual(got["REM-003"]["status"], "proposed")


if __name__ == "__main__":
    unittest.main(verbosity=1)
