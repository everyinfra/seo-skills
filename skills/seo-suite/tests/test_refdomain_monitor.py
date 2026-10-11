#!/usr/bin/env python3
"""monitor.py 引荐域月检测试(R2-4 第 6 检查组,standalone,合成导出/快照,零网络;
tests/run_tests.py 自动发现本文件)。覆盖:
1 check_backlinks:<dir>/backlinks.csv 同 gsc.csv 模式(无文件→skipped 不猜;统一
  格式/原始 Ahrefs/GSC 简易表均经 backlink_import 归一);当月新增域=各域最早
  first_seen 落在近 31 天(无任何可解日期→None 不猜);域清单截断;cfg 路径覆盖
2 run --checks monthly:月检挂 backlinks(daily 不挂);文件损坏→run 落 partial
  +退出码 2(防假 0:读不了绝不判外链归零,且不充当 diff 基线);--backlinks 路径覆盖
3 diff 四级告警:新增引荐域数暴跌>50%→backlink_drop(warn,"引荐域新增 N→M,
  外链获取停滞或丢失");总引荐域降>10%→backlink_loss(critical,带丢失域样本);
  阈值边界(恰 10%/50% 不触发,严格大于才触发);首月无 prev/非 ok 态不猜。"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import monitor as M  # noqa: E402

CFG = {"site": "https://example.com", "thresholds": dict(M.DEFAULT_THRESHOLDS)}
NOW = datetime(2026, 10, 12, 9, 0, 0)


def _fresh_dir():
    tmp = tempfile.mkdtemp(prefix="mon_bl_")
    mdir = os.path.join(tmp, ".seo-monitor")
    rc = M.cmd_init(M.build_parser().parse_args(
        ["init", "--site", "https://example.com", "--market", "us", "--dir", mdir]))
    assert rc == 0
    return mdir


def _write_backlinks(mdir, domains):
    """domains: [(domain, first_seen 'YYYY-MM-DD' 或 ''), ...] → 统一格式 backlinks.csv。
    每行 url 唯一(同域多行不被 referring-url 去重吞掉)。"""
    lines = ["referring_domain,url,dr_or_urgency,anchor,first_seen,last_seen,dofollow,type"]
    for i, (dom, fs) in enumerate(domains):
        lines.append("%s,https://%s/page-%d,,acme,%s,,dofollow,Text" % (dom, dom, i, fs))
    with open(os.path.join(mdir, "backlinks.csv"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _insert_run(mdir, snapshots, ts_offset_days=0, status="ok", kind="monthly"):
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


def _run_cmd(args_list):
    out, err = io.StringIO(), io.StringIO()
    args = M.build_parser().parse_args(args_list)
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = args.func(args)
    return rc, out.getvalue(), err.getvalue()


def _hits(alerts, code):
    return [a for a in alerts if a["code"] == code]


def _snap_from_check(mdir, now=None):
    return M.snapshot_from_results({"backlinks": M.check_backlinks(mdir, now=now)})


# ---------- 1. check_backlinks ----------

class CheckBacklinksTests(unittest.TestCase):
    """缺文件 skip / 统一与原始格式 / 新增域口径 / 损坏 error / 路径覆盖。"""

    def test_missing_export_skipped(self):
        mdir = _fresh_dir()
        out = M.check_backlinks(mdir, now=NOW)
        self.assertEqual(out["state"], "skipped")
        self.assertNotIn("refdomains_total", out["metrics"])       # 不猜数
        self.assertTrue(any("跳过" in n and "不猜" in n for n in out["notes"]))

    def test_unified_export_metrics(self):
        mdir = _fresh_dir()
        _write_backlinks(mdir, [
            ("old1.com", "2026-01-10"), ("old2.com", "2026-03-20"),
            ("new1.com", "2026-10-05"),                              # 窗口内
            ("new2.com", "2026-09-25"),                              # 窗口内(31 天边界内)
            ("mixed.com", "2026-09-20"), ("mixed.com", "2026-01-01"),  # 最早 fs 在窗外
        ])
        out = M.check_backlinks(mdir, now=NOW)
        self.assertEqual(out["state"], "ok")
        m = out["metrics"]
        self.assertEqual(m["refdomains_total"], 5)                  # 去重后的域数
        self.assertEqual(m["refdomains_new"], 2)                    # new1/new2;mixed 取最早 fs
        self.assertEqual(m["format"], "unified")
        self.assertEqual(sorted(m["domains"]),
                         ["mixed.com", "new1.com", "new2.com", "old1.com", "old2.com"])
        self.assertFalse(m["domains_truncated"])
        # 快照形状:snapshot_from_results 落 backlinks.refdomains
        snap = M.snapshot_from_results({"backlinks": out})
        self.assertEqual(snap["backlinks"]["refdomains"]["refdomains_total"], 5)

    def test_raw_exports_accepted_and_gsc_new_none(self):
        mdir = _fresh_dir()
        with open(os.path.join(mdir, "backlinks.csv"), "w", encoding="utf-8") as f:
            f.write('"#","Referring Page","Domain Rating","First Seen","Last Checked",'
                    '"Anchor","Type"\n'
                    '"1","https://a.example.com/p","55","2026-10-10","2026-10-11","x","Text"\n'
                    '"2","https://b.example.org/q","20","2026-02-02","2026-03-01","y","Text"\n')
        out = M.check_backlinks(mdir, now=NOW)
        self.assertEqual(out["state"], "ok")
        self.assertEqual(out["metrics"]["format"], "ahrefs")        # 原始导出自动归一
        self.assertEqual(out["metrics"]["refdomains_total"], 2)
        self.assertEqual(out["metrics"]["refdomains_new"], 1)
        # GSC 简易表(无 first_seen)→ 新增数 None 不猜
        with open(os.path.join(mdir, "backlinks.csv"), "w", encoding="utf-8") as f:
            f.write("https://r1.example.com/p,https://www.mysite.com/a\n"
                    "https://r2.example.org/x,https://www.mysite.com/b\n")
        out2 = M.check_backlinks(mdir, now=NOW)
        self.assertEqual(out2["state"], "ok")
        self.assertEqual(out2["metrics"]["refdomains_total"], 2)
        self.assertIsNone(out2["metrics"]["refdomains_new"])        # 不猜

    def test_corrupt_export_error_state(self):
        mdir = _fresh_dir()
        with open(os.path.join(mdir, "backlinks.csv"), "w", encoding="utf-8") as f:
            f.write("totally,unknown,header\n1,2,3\n")
        out = M.check_backlinks(mdir, now=NOW)
        self.assertEqual(out["state"], "error")
        self.assertIn("error", out["metrics"])
        self.assertNotIn("refdomains_total", out["metrics"])        # 防假 0:不产数字
        self.assertTrue(any("退出码 2" in n for n in out["notes"]))

    def test_path_override_via_cfg(self):
        mdir = _fresh_dir()
        custom = os.path.join(os.path.dirname(mdir), "custom-backlinks.csv")
        _write_backlinks(mdir, [])
        with open(custom, "w", encoding="utf-8") as f:
            f.write("referring_domain,url,dr_or_urgency,anchor,first_seen,last_seen,dofollow,type\n"
                    "z.example.com,https://z.example.com/a,,q,2026-10-10,,,Text\n")
        out = M.check_backlinks(mdir, cfg={"backlinks_csv": custom}, now=NOW)
        self.assertEqual(out["state"], "ok")
        self.assertEqual(out["metrics"]["refdomains_total"], 1)     # 读的是 custom 路径


# ---------- 2. run --checks monthly ----------

class _StubDailyChecks:
    """daily 计划的四个网络检查打桩(run_checks/cmd_run 测试用)。"""

    def __enter__(self):
        self._orig = (M.check_robots, M.check_page, M.check_redirect_variants, M.check_visibility)
        M.check_robots = lambda site, market=None: {"state": "ok", "metrics": {}, "notes": []}
        M.check_page = lambda url, **kw: {"state": "ok", "metrics": {}, "notes": []}
        M.check_redirect_variants = lambda site: {"state": "ok", "metrics": {}, "notes": []}
        M.check_visibility = lambda site, serp_cfg=None: {"state": "ok", "metrics": {}, "notes": []}
        return self

    def __exit__(self, *exc):
        (M.check_robots, M.check_page, M.check_redirect_variants,
         M.check_visibility) = self._orig
        return False


class MonthlyRunTests(unittest.TestCase):
    """monthly 挂 backlinks / 损坏 rc=2+partial / --backlinks 路径覆盖写库。"""

    def test_monthly_gate_in_run_checks(self):
        mdir = _fresh_dir()
        _write_backlinks(mdir, [("a.com", "2026-10-01")])
        cfg = M.load_config(mdir)
        with _StubDailyChecks():
            res = M.run_checks(mdir, cfg, "monthly", M.Budget(None))
            res_daily = M.run_checks(mdir, cfg, "daily", M.Budget(None))
        self.assertEqual(res["backlinks"]["state"], "ok")
        self.assertEqual(res["backlinks"]["metrics"]["refdomains_total"], 1)
        self.assertNotIn("backlinks", res_daily)                    # 日检不挂

    def test_corrupt_export_run_partial_exit_2(self):
        mdir = _fresh_dir()
        with open(os.path.join(mdir, "backlinks.csv"), "w", encoding="utf-8") as f:
            f.write("junk,header,here\nx,y,z\n")
        with _StubDailyChecks():
            rc, out, err = _run_cmd(["run", "--checks", "monthly", "--dir", mdir])
        self.assertEqual(rc, 2, "backlinks.csv 损坏 → 退出码 2(数据错误,防假 0)")
        self.assertIn("backlinks: error", out)
        conn = M.open_db(mdir)
        row = conn.execute("SELECT status FROM runs ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual(row["status"], "partial")                  # 半截数据不充当基线
        self.assertEqual(M.latest_run_ids(conn, 5), [])
        conn.close()

    def test_run_monthly_snapshot_in_db_with_flag(self):
        mdir = _fresh_dir()
        custom = os.path.join(os.path.dirname(mdir), "my-export.csv")
        with open(custom, "w", encoding="utf-8") as f:
            f.write("referring_domain,url,dr_or_urgency,anchor,first_seen,last_seen,dofollow,type\n"
                    "q.example.com,https://q.example.com/a,,acme,,,dofollow,Text\n")
        with _StubDailyChecks():
            rc, _, _ = _run_cmd(["run", "--checks", "monthly", "--backlinks", custom,
                                 "--dir", mdir])
        self.assertEqual(rc, 0)
        conn = M.open_db(mdir)
        row = conn.execute(
            "SELECT value FROM snapshots WHERE \"check\"='backlinks' AND key='refdomains' "
            "ORDER BY run_id DESC LIMIT 1").fetchone()
        conn.close()
        self.assertIsNotNone(row)
        snap = json.loads(row["value"])
        self.assertEqual(snap["refdomains_total"], 1)               # GSC 形态无日期:new=None
        self.assertIsNone(snap["refdomains_new"])


# ---------- 3. diff 四级告警 ----------

class RefdomainDiffTests(unittest.TestCase):
    """backlink_drop(warn)/backlink_loss(critical)/阈值边界/不猜口径。"""

    @staticmethod
    def _snap(total, new, domains):
        return {"backlinks": {"refdomains": {"refdomains_total": total,
                                             "refdomains_new": new,
                                             "domains": domains}}}

    def test_backlink_drop_end_to_end(self):
        """两期月检快照:新增 6→2(−67%)→ backlink_drop warn,diff rc=2。"""
        mdir = _fresh_dir()
        old = [("old%02d.com" % i, "2026-01-%02d" % (i + 1)) for i in range(10)]
        wave_a = [("w%d.com" % i, "2026-10-0%d" % (i + 1)) for i in range(6)]     # 上月新增 6
        wave_b = [("v%d.com" % i, "2026-10-1%d" % i) for i in range(2)]           # 本月新增 2
        _write_backlinks(mdir, old + wave_a)
        snap_a = _snap_from_check(mdir, now=NOW)
        _write_backlinks(mdir, old + wave_a + wave_b)
        snap_b = _snap_from_check(mdir, now=NOW + timedelta(days=28))            # wave_a 出 31 天窗
        _insert_run(mdir, snap_a, ts_offset_days=28)
        _insert_run(mdir, snap_b)
        out = os.path.join(mdir, "alerts.json")
        rc, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 2, "backlink_drop warn → rc=2")
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        hit = [a for a in payload["alerts"] if a["code"] == "backlink_drop"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["level"], "warn")
        self.assertEqual(hit[0]["message"], "引荐域新增 6→2,外链获取停滞或丢失")
        self.assertEqual(hit[0]["details"], {"prev_new": 6, "curr_new": 2, "pct": 66.7})
        self.assertIn("核查外链获取", hit[0]["action"])                # PLAYBOOK 接线
        # 总数 16→16 持平 → 无 backlink_loss
        self.assertFalse([a for a in payload["alerts"] if a["code"] == "backlink_loss"])

    def test_backlink_loss_critical_end_to_end(self):
        """总引荐域 100→89(−11%)→ backlink_loss critical,diff rc=1,带丢失样本。"""
        mdir = _fresh_dir()
        doms = ["d%02d.com" % i for i in range(100)]
        _insert_run(mdir, self._snap(100, 5, doms), ts_offset_days=28)
        _insert_run(mdir, self._snap(89, 5, doms[:89]))
        out = os.path.join(mdir, "alerts.json")
        rc, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 1, "backlink_loss critical → rc=1")
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        hit = [a for a in payload["alerts"] if a["code"] == "backlink_loss"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["level"], "critical")
        self.assertEqual(hit[0]["key"], "refdomains")
        self.assertEqual(hit[0]["details"]["lost_total"], 11)
        self.assertEqual(hit[0]["details"]["lost_sample"], doms[89:99])   # 样本截 10 个
        self.assertIn("处罚", hit[0]["message"])

    def test_threshold_boundaries_strictly_greater(self):
        prev = self._snap(100, 4, [])
        exact_total = self._snap(90, 2, [])                        # 总数恰 −10%:不触发
        alerts = M.compute_alerts(prev, exact_total, CFG)
        self.assertFalse(_hits(alerts, "backlink_loss"))
        self.assertFalse(_hits(alerts, "backlink_drop"))            # 新增 4→2 恰 −50%:不触发
        over_total = self._snap(89, 4, [])                         # −11% → critical
        alerts2 = M.compute_alerts(prev, over_total, CFG)
        self.assertEqual(_hits(alerts2, "backlink_loss")[0]["level"], "critical")
        self.assertFalse(_hits(alerts2, "backlink_drop"))           # 新增持平无 drop
        over_new = self._snap(100, 4, [])                          # (4→4) 不触发
        prev10 = self._snap(100, 10, [])
        alerts3 = M.compute_alerts(prev10, over_new, CFG)          # 10→4 = −60% → warn
        drop = _hits(alerts3, "backlink_drop")
        self.assertEqual(drop[0]["level"], "warn")
        self.assertEqual(drop[0]["message"], "引荐域新增 10→4,外链获取停滞或丢失")
        to_zero = self._snap(100, 0, [])
        self.assertEqual(_hits(M.compute_alerts(prev, to_zero, CFG), "backlink_drop")[0]
                         ["details"]["pct"], 100.0)                 # 2→0 也算暴跌
        # 自定义阈值:total 阈值放宽到 20% → −11% 不触发
        cfg20 = {"site": "https://example.com",
                 "thresholds": dict(M.DEFAULT_THRESHOLDS, backlink_total_drop_pct=20)}
        self.assertFalse(_hits(M.compute_alerts(prev, over_total, cfg20), "backlink_loss"))

    def test_no_prev_or_non_ok_states_never_guess(self):
        prev = self._snap(100, 5, ["a.com"])
        # 首月基线(prev 无 backlinks 快照)→ 不告警
        self.assertFalse(_hits(M.compute_alerts({}, prev, CFG), "backlink_loss"))
        self.assertFalse(_hits(M.compute_alerts({}, prev, CFG), "backlink_drop"))
        # check 侧 skipped/error 只落 state(读不了≠外链归零)
        for bad_state in ("skipped", "error"):
            curr = {"backlinks": {"refdomains": {"state": bad_state}}}
            alerts = M.compute_alerts(prev, curr, CFG)
            self.assertFalse(_hits(alerts, "backlink_loss"), bad_state)
            self.assertFalse(_hits(alerts, "backlink_drop"), bad_state)
        # GSC 形态(new=None)→ 只有总数判定,新增暴跌不猜
        prev_none = self._snap(100, None, [])
        curr_none = self._snap(89, None, [])
        alerts = M.compute_alerts(prev_none, curr_none, CFG)
        self.assertTrue(_hits(alerts, "backlink_loss"))
        self.assertFalse(_hits(alerts, "backlink_drop"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
