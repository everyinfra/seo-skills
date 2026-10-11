#!/usr/bin/env python3
"""monitor.py visibility SERP 源适配层测试(borrow-specs D1 P2 第 13 条,serpbear 式;
standalone,fetch 打桩合成 Bing/DDG HTML,零网络;tests/run_tests.py 自动发现本文件)。
覆盖:
1 默认源与向后兼容:无 serp_source 配置 → bing,输出与旧版逐字节一致
  (ok/skipped/blocked/unparseable 四态的 metrics 与 notes 原文全钉死);
  显式 {"id":"bing"} ≡ 默认(不新增 metrics 键/警告)
2 源选择:{"id":"duckduckgo"} 与裸字符串 → DDG html 端点
  (html.duckduckgo.com/html/?q=),解析 result 链接与排名(ranks),留 serp_source 痕迹
3 DDG 解析:uddg= 跳转包装解包 / result__a 属性顺序无关 / 去重 / 解不出目标的包装不计
4 坏配置回退:未知 id(含注册位 serper/serpapi)/ 缺 id / enabled=false / 坏形态
  → 回退 bing + notes 警告(防静默失明)
5 源对照表:SERP_SOURCE_TABLE 含 源|价格|限额|状态 四源
  (serpbear 对照口径:serper $1/1k、serpapi $50/5k 起)
6 防假 0 纪律对新源生效:ddg 抓取失败/非 200/反爬页/解析不出 → skipped/blocked/
  unparseable,diff 不产 visibility_zero;真 0(state ok)仍告警且 method_note 源感知
7 run_checks 接线:cfg.serp_source 透传 check_visibility"""
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

BING_HTML = (
    "<html><body><ol>"
    "<li><h2><a href='/r'>Pricing</a></h2><cite>https://example.com › pricing</cite></li>"
    "<li><cite>https://example.com › docs › guide</cite></li>"
    "<li><cite>https://other.org › elsewhere</cite></li>"
    "<li><cite>example.com › blog</cite></li>"
    "</ol></body></html>")

DDG_HTML = (
    "<html><body>"
    '<div class="result results_links web-result"><h2 class="result__title">'
    '<a rel="nofollow" class="result__a" href="https://example.com/pricing">Pricing</a>'
    "</h2></div>"
    '<div class="result"><h2 class="result__title">'
    '<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fdocs&amp;rut=abc">Docs</a>'
    "</h2></div>"
    '<div class="result"><h2 class="result__title">'
    '<a href="https://example.com/blog" class="result__a">Blog</a>'
    "</h2></div>"
    '<div class="result"><h2 class="result__title">'
    '<a class="result__a" href="https://other.org/x">Other</a>'
    "</h2></div>"
    "</body></html>")


def _fresh_dir():
    tmp = tempfile.mkdtemp(prefix="mon_serp_")
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


class _StubGet:
    """M.http_get 打桩:responder(url) → body(str)|{"status","body"}|Exception;记录调用 URL。"""

    def __init__(self, responder):
        self.responder = responder
        self.calls = []

    def __enter__(self):
        self._orig = M.http_get

        def fake(url, timeout=M.FETCH_TIMEOUT):
            self.calls.append(url)
            r = self.responder(url)
            if isinstance(r, Exception):
                raise r
            if isinstance(r, dict):
                return {"status": r.get("status", 200), "final_url": url,
                        "elapsed_ms": 1.0, "body": r.get("body", ""), "headers": {}}
            return {"status": 200, "final_url": url, "elapsed_ms": 1.0, "body": r, "headers": {}}
        M.http_get = fake
        return self

    def __exit__(self, *exc):
        M.http_get = self._orig
        return False


# ---------- 1. 默认 bing 与向后兼容(逐字节一致) ----------

class DefaultBingCompatTests(unittest.TestCase):
    """无 serp_source 配置 → bing 默认;ok/skipped/blocked/unparseable 四态输出钉死旧版原文。"""

    def test_ok_path_full_dict_identical_to_legacy(self):
        with _StubGet(lambda u: BING_HTML) as st:
            out = M.check_visibility("https://example.com")
        self.assertEqual(st.calls, ["https://www.bing.com/search?q=site%3Aexample.com"])
        self.assertEqual(out, {
            "check": "visibility", "state": "ok",
            "metrics": {"status": 200, "visible_pages": 3,
                        "sample": ["https://example.com/pricing",
                                   "https://example.com/docs/guide",
                                   "example.com/blog"]},
            "notes": ["方法限制:Bing HTML 端点无 SLA,非官方索引数;仅作抽查方向"]})

    def test_failure_states_identical_to_legacy(self):
        with _StubGet(lambda u: M.FetchError("net down")):
            out = M.check_visibility("https://example.com")
        self.assertEqual(out, {"check": "visibility", "state": "skipped",
                               "metrics": {"error": "net down"},
                               "notes": ["可见性端点抓取失败→skipped 不告警(不猜)"]})
        with _StubGet(lambda u: {"status": 429, "body": ""}):
            out2 = M.check_visibility("https://example.com")
        self.assertEqual(out2, {"check": "visibility", "state": "blocked",
                                "metrics": {"status": 429},
                                "notes": ["site: 端点返回 429→blocked 不告警"]})
        with _StubGet(lambda u: "<html>unusual traffic detected</html>"):
            out3 = M.check_visibility("https://example.com")
        self.assertEqual(out3["state"], "blocked")
        self.assertIn("site: 端点疑似人机验证→blocked 不告警", out3["notes"])
        with _StubGet(lambda u: "<html>redesigned dom</html>"):
            out4 = M.check_visibility("https://example.com")
        self.assertEqual(out4, {"check": "visibility", "state": "unparseable",
                                "metrics": {"status": 200, "cite_tags": 0},
                                "notes": ["Bing 端点 200 但解析不出 cite(DOM 疑似改版)"
                                          "→unparseable 不告警,不当真 0"]})

    def test_explicit_bing_config_same_as_default(self):
        with _StubGet(lambda u: BING_HTML):
            default = M.check_visibility("https://example.com")
            explicit = M.check_visibility("https://example.com", serp_cfg={"id": "bing"})
        self.assertEqual(default, explicit)          # 显式 bing ≡ 默认:无警告、无新 metrics 键


# ---------- 2/3. DDG 源选择与解析 ----------

class DuckDuckGoSourceTests(unittest.TestCase):
    """{"id":"duckduckgo"}/裸字符串 → html.duckduckgo.com;链接、排名、serp_source 留痕。"""

    def test_source_selection_and_ranked_metrics(self):
        with _StubGet(lambda u: DDG_HTML) as st:
            out = M.check_visibility("https://example.com", serp_cfg={"id": "duckduckgo"})
        self.assertEqual(st.calls, ["https://html.duckduckgo.com/html/?q=site%3Aexample.com"])
        self.assertEqual(out["state"], "ok")
        self.assertEqual(out["metrics"]["visible_pages"], 3)          # other.org 不计
        self.assertEqual(out["metrics"]["sample"],
                         ["https://example.com/pricing", "https://example.com/docs",
                          "https://example.com/blog"])
        self.assertEqual(out["metrics"]["ranks"], [1, 2, 3])          # 排名=SERP 顺序(1 基)
        self.assertEqual(out["metrics"]["serp_source"], "duckduckgo")  # 非默认源留痕
        self.assertTrue(any("DuckDuckGo" in n for n in out["notes"]))  # method_note 用源自己的文案

    def test_ddg_parse_uddg_unwrap_order_dedupe(self):
        html = (
            '<a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fa&amp;rut=1">A</a>'
            '<a href="https://example.com/b" class="result__a">B</a>'            # 属性反序
            '<a class="result__a" href="https://example.com/a">A-dup</a>'        # 重复(裸直链形态)
            '<a class="result__snippet" href="https://example.com/c">C</a>'      # 非 result__a 不计
            '<a class="result__a" href="//duckduckgo.com/l/?rut=only">bad</a>')  # 解不出目标的包装
        self.assertEqual(M._serp_ddg_parse(html), ["https://example.com/a", "https://example.com/b"])
        self.assertEqual(M.SERP_SOURCES["duckduckgo"]["parse"](DDG_HTML),
                         ["https://example.com/pricing", "https://example.com/docs",
                          "https://example.com/blog", "https://other.org/x"])

    def test_ddg_bare_string_config(self):
        with _StubGet(lambda u: DDG_HTML) as st:
            out = M.check_visibility("https://example.com", serp_cfg="duckduckgo")
        self.assertTrue(st.calls[0].startswith("https://html.duckduckgo.com/html/?q="))
        self.assertEqual(out["metrics"]["serp_source"], "duckduckgo")


# ---------- 4. 坏配置回退 bing + 警告 ----------

class BadConfigFallbackTests(unittest.TestCase):
    """未知 id/注册位 id/缺 id/enabled=false/坏形态 → 回退 bing 并警告,不静默失明。"""

    def test_unknown_id_falls_back_to_bing_with_warning(self):
        with _StubGet(lambda u: BING_HTML) as st:
            out = M.check_visibility("https://example.com", serp_cfg={"id": "google"})
        self.assertTrue(st.calls[0].startswith("https://www.bing.com/search?q="))
        self.assertEqual(out["state"], "ok")
        self.assertEqual(out["metrics"]["visible_pages"], 3)
        self.assertTrue(any("未知源 id=google" in n and "回退默认 bing" in n for n in out["notes"]))
        self.assertNotIn("serp_source", out["metrics"])     # 回退=默认源,不留 serp_source 键

    def test_registration_slots_not_callable(self):
        """serper/serpapi 是注册位:不在 SERP_SOURCES(不实现付费源调用),配了 → 回退+警告。"""
        self.assertEqual(set(M.SERP_SOURCES), {"bing", "duckduckgo"})
        for slot in ("serper", "serpapi"):
            with _StubGet(lambda u: BING_HTML) as st:
                out = M.check_visibility("https://example.com", serp_cfg={"id": slot})
            self.assertTrue(st.calls[0].startswith("https://www.bing.com/"))
            self.assertEqual(out["metrics"]["visible_pages"], 3)
            self.assertTrue(any(slot in n and "注册位未接入" in n for n in out["notes"]),
                            "%s 注册位必须回退并警告" % slot)

    def test_malformed_configs_fall_back_with_warning(self):
        for bad in ({"id": ""}, {"enabled": True}, {"id": "duckduckgo", "enabled": False},
                    ["duckduckgo"], 42):
            with _StubGet(lambda u: BING_HTML) as st:
                out = M.check_visibility("https://example.com", serp_cfg=bad)
            self.assertTrue(st.calls[0].startswith("https://www.bing.com/"),
                            "%r 应回退 bing" % (bad,))
            self.assertTrue(any("回退默认 bing" in n for n in out["notes"]),
                            "%r 应带回退警告" % (bad,))

    def test_resolve_unit(self):
        self.assertEqual(M.DEFAULT_SERP_SOURCE_ID, "bing")
        self.assertEqual(M.resolve_serp_source(None), (M.SERP_SOURCES["bing"], []))
        self.assertEqual(M.resolve_serp_source(""), (M.SERP_SOURCES["bing"], []))
        self.assertEqual(M.resolve_serp_source({"id": "bing"}), (M.SERP_SOURCES["bing"], []))
        self.assertIs(M.resolve_serp_source("duckduckgo")[0], M.SERP_SOURCES["duckduckgo"])
        self.assertIs(M.resolve_serp_source({"id": "duckduckgo"})[0], M.SERP_SOURCES["duckduckgo"])
        fb, warns = M.resolve_serp_source({"id": "serpapi"})
        self.assertEqual((fb["id"], bool(warns)), ("bing", True))


# ---------- 5. 源对照表(serpbear 式) ----------

class SourceTableTests(unittest.TestCase):
    """SERP_SOURCE_TABLE:源|价格|限额|状态;四源全列;注册表条目带 serpbear 式字段。"""

    def test_table_exists_and_complete(self):
        t = M.SERP_SOURCE_TABLE
        for needle in ("bing", "duckduckgo", "serper", "serpapi",
                       "$1 / 1k", "$50 / 5k",      # serpbear 对照口径:serper $1/1k、serpapi $50/5k 起
                       "价格", "限额", "状态", "注册位", "默认"):
            self.assertIn(needle, t)
        self.assertEqual(t.count("注册位,未接入"), 2)   # 两个付费源都只登记不接入

    def test_registry_entries_carry_spec_fields(self):
        for sid, src in M.SERP_SOURCES.items():
            self.assertEqual(src["id"], sid)
            self.assertIsInstance(src["enabled"], bool)
            for f in ("name", "website", "price_note", "build_url", "parse",
                      "blocked_re", "zero_metrics_key", "unparseable_note", "method_note"):
                self.assertIn(f, src, "%s 缺 %s" % (sid, f))
            self.assertTrue(callable(src["build_url"]) and callable(src["parse"]))
        self.assertEqual(M.SERP_SOURCES["bing"]["build_url"]("https://example.com"),
                         "https://www.bing.com/search?q=site%3Aexample.com")
        self.assertEqual(M.SERP_SOURCES["duckduckgo"]["build_url"]("https://example.com"),
                         "https://html.duckduckgo.com/html/?q=site%3Aexample.com")


# ---------- 6. 防假 0 纪律在新源上生效 ----------

class AntiFakeZeroOnNewSourceTests(unittest.TestCase):
    """ddg 失败态不当排名消失;真 0 仍告警且 method_note 源感知;端到端快照/告警链。"""

    def test_ddg_failure_states_never_rank_loss(self):
        prev = {"visibility": {"site": {"state": "ok", "visible_pages": 5}}}
        cases = [
            (lambda u: M.FetchError("ddg unreachable"), "skipped", None),
            (lambda u: {"status": 403, "body": ""}, "blocked", None),
            (lambda u: "<html>Unfortunately, bots use DuckDuckGo too...</html>", "blocked", None),
            (lambda u: "<html>did not match any documents</html>", "unparseable",
             {"status": 200, "result_links": 0}),
        ]
        for responder, want_state, want_metrics in cases:
            with _StubGet(responder):
                out = M.check_visibility("https://example.com", serp_cfg={"id": "duckduckgo"})
            self.assertEqual(out["state"], want_state)
            self.assertNotIn("visible_pages", out["metrics"])
            if want_metrics is not None:
                self.assertEqual(out["metrics"], want_metrics)
            curr = {"visibility": {"site": {"state": out["state"]}}}
            alerts = M.compute_alerts(prev, curr, CFG)
            self.assertFalse([a for a in alerts
                              if a["code"] in ("visibility_zero", "visibility_drop")],
                             "%s 不该被当成可见性归零" % want_state)

    def test_ddg_true_zero_still_alerts_with_source_aware_note(self):
        """守卫不吞真信号:ddg 端点 ok 且真 0(样本过地板)→ visibility_zero 照告;
        method_note 源感知;旧 bing 快照(无 serp_source 键)保持原文。"""
        prev = {"visibility": {"site": {"state": "ok", "visible_pages": 5}}}
        curr = {"visibility": {"site": {"state": "ok", "visible_pages": 0, "sample": [],
                                        "serp_source": "duckduckgo"}}}
        hit = [a for a in M.compute_alerts(prev, curr, CFG) if a["code"] == "visibility_zero"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["level"], "critical")
        self.assertEqual(hit[0]["details"]["method_note"], "duckduckgo 端点方向抽样,非官方索引数")
        curr_bing = {"visibility": {"site": {"state": "ok", "visible_pages": 0, "sample": []}}}
        hit2 = [a for a in M.compute_alerts(prev, curr_bing, CFG)
                if a["code"] == "visibility_zero"]
        self.assertEqual(hit2[0]["details"]["method_note"],
                         "Bing HTML 端点方向抽样,非官方索引数")

    def test_end_to_end_blocked_vs_true_zero(self):
        """run→snapshot→diff 全链(离线合成快照):ddg blocked 落 {"state":"blocked"} →
        无 visibility_zero;紧随的 ddg 真 0 run 与更早的 ok 基线 diff → critical。"""
        mdir = _fresh_dir()
        _insert_run(mdir, {"visibility": {"site": {"state": "ok", "visible_pages": 5,
                                                   "sample": []}}})
        snap_blocked = M.snapshot_from_results(
            {"visibility": {"check": "visibility", "state": "blocked",
                            "metrics": {"status": 403}, "notes": []}})
        self.assertEqual(snap_blocked["visibility"]["site"], {"state": "blocked"})
        _insert_run(mdir, snap_blocked)
        out = os.path.join(mdir, "alerts.json")
        rc, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 0, "blocked ≠ 排名消失,不该有告警")
        with open(out, encoding="utf-8") as f:
            self.assertFalse(any(a["code"].startswith("visibility_")
                                 for a in json.load(f)["alerts"]))
        # 恢复正常(ok 5)后再真 0 → 与最近 ok run 对比出 critical(基线链不被 blocked run 污染)
        _insert_run(mdir, {"visibility": {"site": {"state": "ok", "visible_pages": 5,
                                                   "sample": []}}})
        _insert_run(mdir, {"visibility": {"site": {"state": "ok", "visible_pages": 0,
                                                   "sample": [], "serp_source": "duckduckgo"}}})
        rc2, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc2, 1)
        with open(out, encoding="utf-8") as f:
            hit = [a for a in json.load(f)["alerts"] if a["code"] == "visibility_zero"]
        self.assertEqual(len(hit), 1)


# ---------- 7. run_checks 接线 ----------

class RunChecksWiringTests(unittest.TestCase):
    """cfg.serp_source 透传 check_visibility(缺省 None/对象/裸字符串三种形态)。"""

    def test_serp_cfg_passthrough(self):
        captured = {}
        orig_cv = M.check_visibility
        orig_others = (M.check_robots, M.check_page, M.check_redirect_variants)
        M.check_robots = lambda site, market=None: {"state": "ok", "metrics": {}, "notes": []}
        M.check_page = lambda url, **kw: {"state": "ok", "metrics": {}, "notes": []}
        M.check_redirect_variants = lambda site: {"state": "ok", "metrics": {}, "notes": []}
        M.check_visibility = lambda site, serp_cfg=None: (
            captured.update({"site": site, "serp_cfg": serp_cfg})
            or {"state": "ok", "metrics": {}, "notes": []})
        try:
            for cfg_node, want in ((None, None),
                                   ({"id": "duckduckgo"}, {"id": "duckduckgo"}),
                                   ("duckduckgo", "duckduckgo")):
                cfg = {"site": "https://example.com", "key_pages": ["/"],
                       "serp_source": cfg_node}
                M.run_checks(os.path.join(tempfile.gettempdir(), "mon_serp_none"), cfg,
                             "daily", M.Budget(None))
                self.assertEqual(captured["serp_cfg"], want)
                self.assertEqual(captured["site"], "https://example.com")
        finally:
            M.check_visibility = orig_cv
            M.check_robots, M.check_page, M.check_redirect_variants = orig_others


if __name__ == "__main__":
    unittest.main(verbosity=1)
