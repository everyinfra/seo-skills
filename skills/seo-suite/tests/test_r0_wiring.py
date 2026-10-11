#!/usr/bin/env python3
"""R0 监控接线回归测试(pipeline-completeness.md R0 节;standalone,合成数据,零网络;
tests/run_tests.py 自动发现本文件)。覆盖三件接线:
① R0-2 sensor_volatility --context 接入——cmd_diff 产 gsc_clicks_drop/visibility 类
   跌幅告警前,项目目录 gsc.csv(含 Date+Query+Position)→ 当日波动上下文;
   verdict=high_volatility 时该告警降 info + message 附注"当日 SERP 高波动,疑似
   算法更新而非站点问题";列不齐/单日/无文件 → 原级别不动(静默跳过)
② R0-3 CWV 进周检——check_cwv_field(PSI key 缺=skipped 不猜;collect 打桩零网络),
   LCP/INP/CLS 任一 poor→cwv_poor(warn)/较上期跨档退步→cwv_regression(info);
   run_checks 周检挂接 + snapshot_from_results 落快照
③ R0-4 citation decay 注入——citation_panel decay-summary 子命令(--panel/--json 出
   {rewriting,decayed_count,per_engine} 轻摘要,复用 decay 计算);monitor 周检发现
   项目目录 panel.json 时同源计算,decayed_count>0 → citation_decay(warn)

合成数据口径: 波动分 gsc.csv 两日矩阵(前日 pos≈2 → 当日 pos≈20,score=9.0≥8=
high_volatility;两日同位次=score 0=normal);decay 面板 23 个 2 天等距采样(前 10
被引后 13 无,与 test_citation_decay.py 的 decayed 判例同构)。"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
import urllib.parse
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import monitor as M          # noqa: E402
import citation_panel as cp  # noqa: E402
import field_data as FD      # noqa: E402  (零依赖 import,仅用其纯函数构造打桩数据)

CFG = {"site": "https://example.com", "thresholds": dict(M.DEFAULT_THRESHOLDS)}
D0 = datetime(2026, 1, 1)


def run_script(name, args=(), stdin=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def _fresh_dir(prefix="mon_r0_"):
    tmp = tempfile.mkdtemp(prefix=prefix)
    mdir = os.path.join(tmp, ".seo-monitor")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):                      # init 的提示不进测试日志
        rc = M.cmd_init(M.build_parser().parse_args(
            ["init", "--site", "https://example.com", "--market", "us", "--dir", mdir]))
    assert rc == 0
    return tmp, mdir


def _insert_run(mdir, snapshots, ts_offset_days=0, status="ok", kind="daily"):
    """{check: {key: value}} 直接落快照(绕过网络;与 test_fix_monitor 同形)。"""
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
                (rid, ts, check, key, json.dumps(value), "h%s%s%s" % (rid, check, key)))
    conn.commit()
    conn.close()
    return rid


def _run_diff(mdir, *extra):
    """cmd_diff json+dry-run → (rc, payload dict);不打 subprocess。"""
    out, err = io.StringIO(), io.StringIO()
    args = M.build_parser().parse_args(["diff", "--format", "json", "--dry-run",
                                        "--dir", mdir, *extra])
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = args.func(args)
    return rc, json.loads(out.getvalue())


def write_gsc_csv(path, day1_pos, day2_pos, queries=10):
    """两日 GSC 矩阵导出(Date,Query,Clicks,Impressions,Position)。"""
    rows = ["Date,Query,Clicks,Impressions,Position"]
    for i in range(queries):
        rows.append("2026-10-10,q%d,5,100,%s" % (i, day1_pos))
        rows.append("2026-10-11,q%d,5,100,%s" % (i, day2_pos))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")


# ---------------- ① R0-2:sensor_volatility --context 接线 ----------------

class SensorContextUnitTests(unittest.TestCase):
    """sensor_volatility_context: 列闸门 / 高波动判定 / 静默跳过口径。"""

    def test_high_volatility_context(self):
        """pos 2→20(|Δ|/20=0.9×10 词)→ score 9.0≥8 → high_volatility(最新可评分日)。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "gsc.csv")
            write_gsc_csv(p, 2.0, 20.0)
            ctx = M.sensor_volatility_context(p)
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx["verdict"], "high_volatility")
        self.assertEqual(ctx["date"], "2026-10-11")
        self.assertEqual(ctx["score"], 9.0)
        self.assertIn("band", ctx)

    def test_normal_volatility_context(self):
        """两日位次不动 → score 0.0 → normal(不触发降级)。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "gsc.csv")
            write_gsc_csv(p, 5.0, 5.0)
            self.assertEqual(M.sensor_volatility_context(p)["verdict"], "normal")

    def test_missing_columns_or_single_day_or_absent(self):
        """页级导出(无 Position)/单日数据/文件不存在 → None 静默跳过,不猜。"""
        with tempfile.TemporaryDirectory() as tmp:
            pagelevel = os.path.join(tmp, "page.csv")
            with open(pagelevel, "w", encoding="utf-8") as f:
                f.write("Page,Clicks,Impressions\n/,\,5,100\n".replace("\\", ""))
            self.assertFalse(M._gsc_csv_has_sensor_columns(pagelevel))
            self.assertIsNone(M.sensor_volatility_context(pagelevel))
            single = os.path.join(tmp, "single.csv")
            write_gsc_csv(single, 2.0, 20.0)
            with open(single, encoding="utf-8") as f:        # 只留首日
                lines = [ln for ln in f.read().splitlines() if ln.startswith("2026-10-10") or ln.startswith("Date")]
            with open(single, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            self.assertIsNone(M.sensor_volatility_context(single))
            self.assertIsNone(M.sensor_volatility_context(os.path.join(tmp, "nope.csv")))


class SensorDiffTests(unittest.TestCase):
    """cmd_diff 接线: high_volatility → gsc/visibility 跌幅告警降 info+附注。"""

    GSC_SNAP = ({"gsc": {"file": {"clicks_total": 100}}},
                {"gsc": {"file": {"clicks_total": 70}}})       # −30% 过地板 → gsc_clicks_drop
    VIS_SNAP = ({"visibility": {"site": {"state": "ok", "visible_pages": 10}}},
                {"visibility": {"site": {"state": "ok", "visible_pages": 5}}})  # −50% → visibility_drop

    def _diff(self, snapshots, gsc_writer=None, kind="daily"):
        tmp, mdir = _fresh_dir("mon_r0_sensor_")
        self.addCleanup(lambda: None)
        prev, curr = snapshots
        _insert_run(mdir, prev, ts_offset_days=1, kind=kind)
        _insert_run(mdir, curr, ts_offset_days=0, kind=kind)
        if gsc_writer:
            gsc_writer(os.path.join(mdir, "gsc.csv"))
        rc, payload = _run_diff(mdir)
        return rc, {a["code"]: a for a in payload["alerts"]}

    def test_gsc_clicks_drop_downgraded_on_high_volatility(self):
        rc, alerts = self._diff(self.GSC_SNAP, lambda p: write_gsc_csv(p, 2.0, 20.0))
        a = alerts["gsc_clicks_drop"]
        self.assertEqual(a["level"], "info")                    # warn → info
        self.assertIn(M.SENSOR_HIGH_NOTE, a["message"])
        self.assertIn("疑似算法更新而非站点问题", a["message"])
        self.assertEqual(a["details"]["sensor_volatility"]["verdict"], "high_volatility")
        self.assertEqual(rc, 0)                                 # 无 warn/critical

    def test_gsc_clicks_drop_keeps_warn_without_context(self):
        """无 gsc.csv / 低波动 / 缺列 三种形态都保持原 warn(附注是增强不是干扰)。"""
        for writer in (None, lambda p: write_gsc_csv(p, 5.0, 5.0)):
            rc, alerts = self._diff(self.GSC_SNAP, writer)
            self.assertEqual(alerts["gsc_clicks_drop"]["level"], "warn", "未高波动不得降级")
            self.assertEqual(rc, 2)
        tmp, mdir = _fresh_dir("mon_r0_cols_")                  # 缺 Position 列(页级导出)
        _insert_run(mdir, self.GSC_SNAP[0], ts_offset_days=1)
        _insert_run(mdir, self.GSC_SNAP[1], ts_offset_days=0)
        with open(os.path.join(mdir, "gsc.csv"), "w", encoding="utf-8") as f:
            f.write("Page,Clicks,Impressions\n/,5,100\n")
        rc, alerts = _run_diff(mdir)
        hit = [a for a in alerts["alerts"] if a["code"] == "gsc_clicks_drop"]
        self.assertEqual(hit[0]["level"], "warn")

    def test_visibility_drop_downgraded_on_high_volatility(self):
        rc, alerts = self._diff(self.VIS_SNAP, lambda p: write_gsc_csv(p, 2.0, 20.0))
        self.assertEqual(alerts["visibility_drop"]["level"], "info")
        self.assertIn(M.SENSOR_HIGH_NOTE, alerts["visibility_drop"]["message"])
        self.assertEqual(rc, 0)
        rc2, alerts2 = self._diff(self.VIS_SNAP)                # 对照:无波动上下文 → warn
        self.assertEqual(alerts2["visibility_drop"]["level"], "warn")
        self.assertEqual(rc2, 2)


# ---------------- ② R0-3:CWV 进周检 ----------------

def fd_entry(metric, val):
    """真实 field_data.field_entry(官方阈值判档)构造成块,打桩零网络。"""
    return FD.field_entry(metric, val, None, "psi")


def fake_collect(url, strategy, psi_key=None, crux_key=None, scope="page", timeout=None):
    """field_data.collect 打桩:按 path 出三档 CWV 现场数据(p75 毫秒/小数)。"""
    specs = {
        "/":         {"LCP": 1800.0, "INP": 150.0, "CLS": 0.05},   # 全 good
        "/pricing":  {"LCP": 5200.0, "INP": 480.0, "CLS": 0.30},   # LCP/CLS poor,INP NI
        "/blog/a":   {"LCP": 3000.0, "INP": 250.0, "CLS": 0.15},   # 全 needs_improvement
    }
    path = urllib.parse.urlparse(url).path or "/"
    field = {k: fd_entry(k, v) for k, v in specs.get(path, {}).items()}
    return {"url": url, "strategy": strategy, "field": field, "lab": {},
            "field_category": None, "performance_score": None,
            "source": "psi", "errors": [], "notes": []}


FAKE_FD = types.SimpleNamespace(collect=fake_collect)


class CwvFieldCheckTests(unittest.TestCase):
    """check_cwv_field: 无 key=skipped 不猜;有 key+打桩 collect → ok 快照。"""

    def test_skipped_without_psi_key(self):
        os.environ.pop("PSI_API_KEY", None)
        out = M.check_cwv_field("https://example.com", {"key_pages": ["/"]})
        self.assertEqual(out["state"], "skipped")
        self.assertTrue(any("PSI_API_KEY" in n for n in out["notes"]), out["notes"])
        self.assertEqual(out["metrics"], {})                    # 不猜

    def test_collect_stub_produces_verdicts(self):
        os.environ["PSI_API_KEY"] = "test-key"
        self.addCleanup(os.environ.pop, "PSI_API_KEY", None)
        orig = M._import_sibling
        M._import_sibling = lambda name: FAKE_FD                # 打桩:零网络
        try:
            out = M.check_cwv_field("https://example.com",
                                    {"key_pages": ["/", "/pricing", "/blog/a"]})
        finally:
            M._import_sibling = orig
        self.assertEqual(out["state"], "ok")
        pages = out["metrics"]["pages"]
        self.assertEqual(sorted(pages), ["/", "/blog/a", "/pricing"])
        self.assertEqual(pages["/pricing"]["LCP"]["verdict"], "poor")     # 5200ms>4000
        self.assertEqual(pages["/"]["CLS"]["verdict"], "good")
        self.assertTrue(any("poor 页 1" in n for n in out["notes"]), out["notes"])

    def test_first_n_pages_only(self):
        """只采 key_pages 前 N 页(默认 CWV_FIELD_PAGES,配额预算)。"""
        os.environ["PSI_API_KEY"] = "test-key"
        self.addCleanup(os.environ.pop, "PSI_API_KEY", None)
        orig = M._import_sibling
        M._import_sibling = lambda name: FAKE_FD
        try:
            cfg = {"key_pages": ["/", "/pricing", "/blog/a"], "cwv_field_pages": 2}
            out = M.check_cwv_field("https://example.com", cfg)
        finally:
            M._import_sibling = orig
        self.assertEqual(sorted(out["metrics"]["pages"]), ["/", "/pricing"])


class CwvAlertTests(unittest.TestCase):
    """compute_alerts: 任一 poor→cwv_poor(warn);跨档退步→cwv_regression(info)。"""

    @staticmethod
    def _snap(pages):
        return {"cwv_field": {"field": {"pages": pages, "strategy": "mobile", "source": "psi"}}}

    def test_poor_warn_and_regression_info(self):
        prev = self._snap({"/": {"LCP": fd_entry("LCP", 1800.0)},          # good
                           "/pricing": {"LCP": fd_entry("LCP", 3000.0)}})  # NI
        curr = self._snap({"/": {"LCP": fd_entry("LCP", 3000.0)},          # good→NI 跨档
                           "/pricing": {"LCP": fd_entry("LCP", 5200.0)}})  # NI→poor
        alerts = M.compute_alerts(prev, curr, CFG)
        by_code = {a["code"]: a for a in alerts}
        self.assertEqual(by_code["cwv_poor"]["level"], "warn")
        self.assertEqual(by_code["cwv_poor"]["key"], "/pricing")
        self.assertIn("LCP", by_code["cwv_poor"]["message"])
        self.assertEqual(by_code["cwv_regression"]["level"], "info")
        self.assertEqual(by_code["cwv_regression"]["key"], "/")
        self.assertEqual(by_code["cwv_regression"]["details"]["prev_verdict"], "good")
        self.assertEqual(by_code["cwv_regression"]["details"]["curr_verdict"],
                         "needs_improvement")

    def test_no_alerts_when_good_or_missing(self):
        good = self._snap({"/": {"LCP": fd_entry("LCP", 1800.0)}})
        alerts = M.compute_alerts(good, good, CFG)              # 全 good 持平 → 无
        self.assertFalse([a for a in alerts if a["code"].startswith("cwv_")])
        alerts2 = M.compute_alerts({}, good, CFG)               # prev 无 cwv 且无 poor → 无
        self.assertFalse([a for a in alerts2 if a["code"].startswith("cwv_")])

    def test_snapshot_and_run_status_wiring(self):
        """snapshot_from_results 落 cwv_field/citation 快照;cmd_run 状态组覆盖新检查。"""
        import inspect
        results = {"cwv_field": {"state": "ok", "metrics": {"pages": {"/": {}}, "strategy": "mobile"}},
                   "cwv_field_skipped": {"state": "skipped"},
                   "citation": {"state": "ok", "metrics": {"decayed_count": 1}}}
        snap = M.snapshot_from_results(results)
        self.assertIn("pages", snap["cwv_field"]["field"])
        self.assertEqual(snap["citation"]["decay"]["decayed_count"], 1)
        snap2 = M.snapshot_from_results({"cwv_field": {"state": "skipped", "metrics": {}},
                                         "citation": {"state": "skipped", "metrics": {}}})
        self.assertEqual(snap2["cwv_field"]["field"], {"state": "skipped"})
        self.assertEqual(snap2["citation"]["decay"], {"state": "skipped"})
        self.assertIn("cwv_field", inspect.getsource(M.cmd_run))   # run 状态组已覆盖
        self.assertIn("citation", inspect.getsource(M.cmd_run))


class RunChecksWeeklyWiringTests(unittest.TestCase):
    """run_checks: weekly 挂 cwv_field+citation,daily 不挂(全部网络检查打桩)。"""

    def setUp(self):
        os.environ["PSI_API_KEY"] = "test-key"
        self._orig_import = M._import_sibling
        M._import_sibling = lambda name: FAKE_FD if name == "field_data" else cp
        self._orig_checks = (M.check_robots, M.check_page, M.check_redirect_variants,
                             M.check_visibility, M.check_sitemap, M.check_llms_txt,
                             M.check_ssl)
        M.check_robots = lambda site, market=None: {"state": "ok", "metrics": {}, "notes": []}
        M.check_page = lambda url, **kw: {"state": "ok", "metrics": {}, "notes": []}
        M.check_redirect_variants = lambda site: {"state": "ok", "metrics": {}, "notes": []}
        M.check_visibility = lambda site, serp_cfg=None: {"state": "ok", "metrics": {}, "notes": []}
        M.check_sitemap = lambda site, rm, budget: {"state": "ok", "metrics": {}, "notes": []}
        M.check_llms_txt = lambda site: {"state": "ok", "metrics": {}, "notes": []}
        M.check_ssl = lambda site: {"state": "ok", "metrics": {}, "notes": []}

    def tearDown(self):
        os.environ.pop("PSI_API_KEY", None)
        M._import_sibling = self._orig_import
        (M.check_robots, M.check_page, M.check_redirect_variants, M.check_visibility,
         M.check_sitemap, M.check_llms_txt, M.check_ssl) = self._orig_checks

    def test_weekly_runs_cwv_and_citation(self):
        tmp, mdir = _fresh_dir("mon_r0_weekly_")
        cp.save_panel(os.path.join(tmp, "panel.json"), decayed_panel())   # 项目根面板
        cfg = {"site": "https://example.com", "key_pages": ["/", "/pricing"]}
        res = M.run_checks(mdir, cfg, "weekly", M.Budget(None))
        self.assertEqual(res["cwv_field"]["state"], "ok")
        self.assertIn("/pricing", res["cwv_field"]["metrics"]["pages"])
        self.assertEqual(res["citation"]["state"], "ok")
        self.assertEqual(res["citation"]["metrics"]["decayed_count"], 1)
        snap = M.snapshot_from_results(res)
        self.assertTrue(snap["cwv_field"]["field"]["pages"])
        self.assertEqual(snap["citation"]["decay"]["decayed_count"], 1)
        res_daily = M.run_checks(mdir, cfg, "daily", M.Budget(None))     # 日检不挂
        self.assertNotIn("cwv_field", res_daily)
        self.assertNotIn("citation", res_daily)

    def test_weekly_citation_alert_end_to_end(self):
        """周检快照 → diff: decayed>0 产 citation_decay warn。"""
        tmp, mdir = _fresh_dir("mon_r0_weekly2_")
        cfg = {"site": "https://example.com", "key_pages": ["/"]}
        res_prev = M.run_checks(mdir, cfg, "weekly", M.Budget(None))     # 无 panel → skipped
        snap_prev = M.snapshot_from_results(res_prev)
        cp.save_panel(os.path.join(tmp, "panel.json"), decayed_panel())
        res_curr = M.run_checks(mdir, cfg, "weekly", M.Budget(None))
        snap_curr = M.snapshot_from_results(res_curr)
        _insert_run(mdir, snap_prev, ts_offset_days=7, kind="weekly")
        _insert_run(mdir, snap_curr, ts_offset_days=0, kind="weekly")
        rc, payload = _run_diff(mdir)
        hit = [a for a in payload["alerts"] if a["code"] == "citation_decay"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["level"], "warn")
        self.assertEqual(hit[0]["details"]["decayed_count"], 1)
        self.assertEqual(rc, 2)


# ---------------- ③ R0-4:citation decay 注入 ----------------

def decayed_panel():
    """23 个 2 天等距采样(前 10 被引后 13 无)→ 1 个 cell decayed(test_citation_decay
    同构判例: peak=1.0,半衰 14 天);面板窗 44 天≥28、峰值窗采样 7≥5 过 4 道闸门。"""
    prompt = "best crm for small business"
    by_date = {}
    for i in range(23):
        y = 1 if i < 10 else 0
        by_date[2 * i] = {prompt: {"state": "cited_brand" if y else "brand_absent",
                                   "mentioned": y, "cited": y, "cited_urls": []}}
    runs = [{"run_id": "chatgpt-d%02d" % off, "engine": "chatgpt",
             "date": (D0 + timedelta(days=off)).isoformat(), "brand": "Acme",
             "results": cells} for off, cells in sorted(by_date.items())]
    return {"brand": "Acme", "domain": "acme.ai", "aliases": [], "prompts": [prompt],
            "engines": ["chatgpt"], "runs": runs}


class DecaySummaryTests(unittest.TestCase):
    """decay_summary 函数 + decay-summary 子命令(复用 decay 计算,零网络)。"""

    def test_decay_summary_function(self):
        s = cp.decay_summary(decayed_panel())
        self.assertEqual(s["decayed_count"], 1)
        self.assertEqual(s["rewriting"], 1)
        self.assertEqual(s["per_engine"], {"chatgpt": {"decayed_count": 1, "rewriting": 1}})
        self.assertEqual(s["metric"], "cited")

    def test_decay_summary_cli_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "panel.json")
            cp.save_panel(p, decayed_panel())
            r = run_script("citation_panel.py", ["decay-summary", "--panel", p, "--json"])
            self.assertEqual(r.returncode, 0, r.stderr)
            s = json.loads(r.stdout)
            self.assertEqual(set(s) >= {"rewriting", "decayed_count", "per_engine"}, True)
            self.assertEqual(s["decayed_count"], 1)
            self.assertEqual(s["rewriting"], 1)
            r_text = run_script("citation_panel.py", ["decay-summary", "--panel", p])
            self.assertEqual(r_text.returncode, 0)
            self.assertIn("decayed(已过半衰)=1", r_text.stdout)

    def test_decay_summary_cli_no_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "panel.json")
            cp.save_panel(p, {"brand": "Acme", "prompts": ["x"], "engines": ["chatgpt"],
                              "aliases": [], "runs": []})
            r = run_script("citation_panel.py", ["decay-summary", "--panel", p, "--json"])
            self.assertEqual(r.returncode, 1)


class CitationDecayMonitorTests(unittest.TestCase):
    """monitor 侧: 项目目录 panel.json 发现 + decayed_count>0 → citation_decay warn。"""

    def test_check_citation_decay_finds_project_panel(self):
        """panel.json 在 monitor 目录的父目录(项目根)与 mdir 内都能被发现。"""
        with tempfile.TemporaryDirectory() as tmp:
            mdir = os.path.join(tmp, "proj", ".seo-monitor")
            os.makedirs(mdir)
            out = M.check_citation_decay(mdir)                 # 无面板 → skipped 不猜
            self.assertEqual(out["state"], "skipped")
            self.assertTrue(any("panel.json" in n for n in out["notes"]))
            root_panel = os.path.join(tmp, "proj", "panel.json")
            cp.save_panel(root_panel, decayed_panel())
            out2 = M.check_citation_decay(mdir)                # 项目根面板
            self.assertEqual(out2["state"], "ok")
            self.assertEqual(out2["metrics"]["decayed_count"], 1)
            self.assertEqual(out2["metrics"]["panel"], root_panel)
            inner = os.path.join(mdir, "panel.json")           # mdir 内面板优先
            cp.save_panel(inner, decayed_panel())
            out3 = M.check_citation_decay(mdir)
            self.assertEqual(out3["metrics"]["panel"], inner)

    def test_diff_citation_decay_alert(self):
        tmp, mdir = _fresh_dir("mon_r0_cit_")
        dec = {"decayed_count": 2, "rewriting": 1,
               "per_engine": {"chatgpt": {"decayed_count": 2, "rewriting": 1}}}
        _insert_run(mdir, {}, ts_offset_days=7, kind="weekly")
        _insert_run(mdir, {"citation": {"decay": dict(dec)}}, ts_offset_days=0, kind="weekly")
        rc, payload = _run_diff(mdir)
        hit = [a for a in payload["alerts"] if a["code"] == "citation_decay"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["level"], "warn")
        self.assertEqual(hit[0]["details"]["decayed_count"], 2)
        self.assertEqual(rc, 2)
        # decayed_count=0 / check skipped → 不产告警(不猜)
        tmp2, mdir2 = _fresh_dir("mon_r0_cit0_")
        _insert_run(mdir2, {}, ts_offset_days=7, kind="weekly")
        _insert_run(mdir2, {"citation": {"decay": dict(dec, decayed_count=0)}},
                    ts_offset_days=0, kind="weekly")
        rc2, payload2 = _run_diff(mdir2)
        self.assertFalse([a for a in payload2["alerts"] if a["code"] == "citation_decay"])
        tmp3, mdir3 = _fresh_dir("mon_r0_citsk_")
        _insert_run(mdir3, {}, ts_offset_days=7, kind="weekly")
        _insert_run(mdir3, {"citation": {"decay": {"state": "skipped"}}},
                    ts_offset_days=0, kind="weekly")
        rc3, payload3 = _run_diff(mdir3)
        self.assertFalse([a for a in payload3["alerts"] if a["code"] == "citation_decay"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
