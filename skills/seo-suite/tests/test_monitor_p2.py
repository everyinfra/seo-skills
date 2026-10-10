#!/usr/bin/env python3
"""monitor.py D1 P2 扩展测试(standalone,合成 config/快照,零网络;
tests/run_tests.py 自动发现本文件)。覆盖七项:
1 title/meta removed 语义:新值为空串/缺失且旧值非空 → meta_removed(warn,
  "被移除——若非有意立即回滚")区别于普通 changed(info title_meta_drift);
  404/抓取失败页面不判(渲染守卫);旧快照缺字段不触发
2 h1 与 hreflang 进指纹:check_page 提取首个 h1 与 hreflang 集哈希(顺序无关);
  h1_changed(info)/hreflang_changed(warn"国际化注解变更可能整组失效")
3 GA 跟踪消失:key_pages assertions.must_contain("gtag(")消失 → ga_tracking_removed(warn)
4 非规范域名重定向失效:http:// 形态与裸域各 probe 一次,期望 301→canonical host;
  变体直接 200 → redirect_chain_broken(warn);probe 网络失败=error 不判失效(防假 0)
5 main_content_change:快照存 word_count,变化 pct≥thresholds.content_change_pct(默认 30)
  → info"主内容字数 {old}→{new}({pct}%)"
6 digest 头部:report 顶部"N improved, M declined"(对比最近两期告警指纹集合;
  improved=上期有本期无,declined=本期新增)
7 多断言:expect 单条→数组向后兼容;max_latency_ms 绝对时延上限(对接 latency_spike);
  selector_stable:true 快照存首个 h2,变了 → layout_shift(info)
附:防假 0 纪律复核(visibility blocked/skipped 不判排名消失)。"""
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

RENDERED = {"status": 200}


def _fresh_dir():
    tmp = tempfile.mkdtemp(prefix="mon_p2_")
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


def _codes(alerts):
    return {a["code"] for a in alerts}


def _hits(alerts, code):
    return [a for a in alerts if a["code"] == code]


# ---------- 1. title/meta removed 语义 ----------

class MetaRemovedTests(unittest.TestCase):
    """新值空+旧值非空=removed(warn);普通变化=changed(info);渲染守卫/旧库兼容。"""

    def test_removed_is_warn_distinct_from_changed(self):
        prev = {"pages": {"/p": {"status": 200, "title": "Old Title", "meta_desc": "M"}}}
        curr = {"pages": {"/p": {"status": 200, "title": "", "meta_desc": "M"}}}
        alerts = M.compute_alerts(prev, curr, CFG)
        removed = _hits(alerts, "meta_removed")
        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]["level"], "warn")
        self.assertIn("被移除", removed[0]["message"])
        self.assertIn("立即回滚", removed[0]["message"])
        self.assertEqual(removed[0]["details"]["fields"], ["title"])
        # 移除的字段不再重复进 changed(info)清单
        drift = _hits(alerts, "title_meta_drift")
        self.assertFalse(drift, "title 已按 removed 报,不应再走 title_meta_drift")

    def test_normal_change_stays_info_drift(self):
        prev = {"pages": {"/p": {"status": 200, "title": "A", "meta_desc": "M"}}}
        curr = {"pages": {"/p": {"status": 200, "title": "B", "meta_desc": "M"}}}
        alerts = M.compute_alerts(prev, curr, CFG)
        self.assertFalse(_hits(alerts, "meta_removed"))
        drift = _hits(alerts, "title_meta_drift")
        self.assertEqual(len(drift), 1)
        self.assertEqual(drift[0]["level"], "info")
        self.assertEqual(drift[0]["details"]["fields"], ["title"])

    def test_mixed_removed_and_changed_split(self):
        """同页 title 被移除 + meta_desc 普通变化 → 两条各按各的级别。"""
        prev = {"pages": {"/p": {"status": 200, "title": "T", "meta_desc": "M1"}}}
        curr = {"pages": {"/p": {"status": 200, "title": "", "meta_desc": "M2"}}}
        alerts = M.compute_alerts(prev, curr, CFG)
        self.assertEqual(_hits(alerts, "meta_removed")[0]["details"]["fields"], ["title"])
        self.assertEqual(_hits(alerts, "title_meta_drift")[0]["details"]["fields"], ["meta_desc"])

    def test_down_page_not_judged_as_removal(self):
        """渲染守卫:404/抓取失败页面没有"字段被移除"的证据 → 不产 meta_removed。"""
        prev = {"pages": {"/p": {"status": 200, "title": "T", "meta_desc": "M",
                                 "h1": "A", "hreflang_hash": "h", "word_count": 100,
                                 "must_contain_missing": []}}}
        down = {"pages": {"/p": {"state": "http_error", "status": 404, "title": "",
                                 "h1": "", "hreflang_hash": "z", "word_count": 0,
                                 "must_contain_missing": ["gtag("]}}}
        err = {"pages": {"/p": {"state": "error", "error": "x", "title": "",
                                "must_contain_missing": ["gtag("]}}}
        for bad_curr in (down, err):
            alerts = M.compute_alerts(prev, bad_curr, CFG)
            for code in ("meta_removed", "h1_changed", "hreflang_changed",
                         "ga_tracking_removed", "main_content_change", "layout_shift"):
                self.assertFalse(_hits(alerts, code), "%s 不该在未渲染页面上触发" % code)

    def test_old_snapshot_and_field_added(self):
        """旧快照缺字段→不触发;字段从无到有(添加)→ 只算 changed,不算 removed。"""
        prev = {"pages": {"/p": {"status": 200}}}                   # 旧库形态:无新字段
        curr = {"pages": {"/p": {"status": 200, "title": "T"}}}
        alerts = M.compute_alerts(prev, curr, CFG)
        self.assertFalse(_hits(alerts, "meta_removed"))
        self.assertEqual(_hits(alerts, "title_meta_drift")[0]["details"]["fields"], ["title"])


# ---------- 2. h1 与 hreflang 进指纹 ----------

class H1HreflangTests(unittest.TestCase):
    """check_page 提取 / 顺序无关哈希 / h1_changed(info)/hreflang_changed(warn)。"""

    BODY = ("<title>t</title><h1>First Head</h1><h1>Second Head</h1>"
            "<link rel='alternate' hreflang='en' href='https://x/'>"
            "<link rel='alternate' hreflang='fr' href='https://x/fr'>"
            "<link rel='canonical' href='https://x/'>")

    @staticmethod
    def _check(body):
        orig_get, orig_head = M.http_get, M.http_head
        M.http_get = lambda url, timeout=M.FETCH_TIMEOUT: {
            "status": 200, "final_url": url, "elapsed_ms": 5.0, "body": body, "headers": {}}
        M.http_head = lambda u, timeout=M.FETCH_TIMEOUT: {"status": 200}
        try:
            return M.check_page("https://x/p")["metrics"]
        finally:
            M.http_get, M.http_head = orig_get, orig_head

    def test_check_page_extracts_fingerprints(self):
        m = self._check(self.BODY)
        self.assertEqual(m["h1"], "First Head")                          # 首个 h1
        self.assertEqual(m["hreflang_hash"],
                         M.hreflang_hash("<link rel='alternate' hreflang='en' href='https://x/'>"
                                         "<link rel='alternate' hreflang='fr' href='https://x/fr'>"))
        self.assertIsInstance(m["word_count"], int)
        self.assertGreater(m["word_count"], 0)

    def test_hreflang_order_insensitive_and_membership_sensitive(self):
        reordered = ("<link rel='alternate' hreflang='fr' href='https://x/fr'>"
                     "<link rel='alternate' hreflang='en' href='https://x/'>")
        self.assertEqual(M.hreflang_hash(self.BODY), M.hreflang_hash(reordered))   # 重排=同指纹
        added = reordered + "<link rel='alternate' hreflang='de' href='https://x/de'>"
        self.assertNotEqual(M.hreflang_hash(self.BODY), M.hreflang_hash(added))    # 增删语言=变更
        # 无 hreflang 的 alternate(RSS)与 rel=canonical 不入集
        self.assertEqual(M.extract_hreflangs("<link rel='alternate' type='rss' href='https://x/f'>"),
                         [])
        self.assertEqual(M.extract_hreflangs("<link rel='canonical' href='https://x/'>"), [])

    def test_diff_h1_and_hreflang_alerts(self):
        prev = {"pages": {"/p": {"status": 200, "h1": "A", "hreflang_hash": "hh1",
                                 "title": "t", "meta_desc": "m"}}}
        curr = {"pages": {"/p": {"status": 200, "h1": "B", "hreflang_hash": "hh2",
                                 "title": "t", "meta_desc": "m"}}}
        alerts = M.compute_alerts(prev, curr, CFG)
        h1 = _hits(alerts, "h1_changed")
        self.assertEqual(len(h1), 1) and self.assertEqual(h1[0]["level"], "info")
        self.assertEqual(h1[0]["details"], {"prev_h1": "A", "curr_h1": "B"})
        hl = _hits(alerts, "hreflang_changed")
        self.assertEqual(len(hl), 1) and self.assertEqual(hl[0]["level"], "warn")
        self.assertIn("国际化注解变更可能整组失效", hl[0]["message"])
        self.assertEqual(hl[0]["details"], {"prev_hash": "hh1", "curr_hash": "hh2"})
        # h1/hreflang 不再进通用漂移清单(专用规则,防双报)
        drift_fields = _hits(alerts, "title_meta_drift")
        self.assertFalse(drift_fields, "title/meta 未变,不该有字段漂移")

    def test_old_snapshot_without_fingerprint_no_alarm(self):
        """旧 monitor.db 快照缺 h1/hreflang_hash → 按 None 不触发(升级后首 diff 不误报)。"""
        prev = {"pages": {"/p": {"status": 200, "title": "t"}}}
        curr = {"pages": {"/p": {"status": 200, "title": "t", "h1": "A",
                                 "hreflang_hash": "q", "word_count": 5}}}
        alerts = M.compute_alerts(prev, curr, CFG)
        for code in ("h1_changed", "hreflang_changed", "main_content_change"):
            self.assertFalse(_hits(alerts, code))


# ---------- 3. GA 跟踪消失(must_contain) ----------

class MustContainTests(unittest.TestCase):
    """assertions.must_contain 消失 → ga_tracking_removed(warn)。"""

    BODY_WITH_GA = "<title>t</title><script>gtag('config','G-1');</script><p>x</p>"

    def test_check_page_must_contain_missing(self):
        orig_get, orig_head = M.http_get, M.http_head
        M.http_get = lambda url, timeout=M.FETCH_TIMEOUT: {
            "status": 200, "final_url": url, "elapsed_ms": 5.0,
            "body": "<title>t</title><p>no tracking here</p>", "headers": {}}
        M.http_head = lambda u, timeout=M.FETCH_TIMEOUT: {"status": 200}
        try:
            m = M.check_page("https://x/p", must_contain=["gtag(", "dataLayer"])["metrics"]
        finally:
            M.http_get, M.http_head = orig_get, orig_head
        self.assertEqual(m["must_contain_missing"], ["gtag(", "dataLayer"])
        # 在场 → 空缺失清单
        M.http_get = lambda url, timeout=M.FETCH_TIMEOUT: {
            "status": 200, "final_url": url, "elapsed_ms": 5.0,
            "body": self.BODY_WITH_GA, "headers": {}}
        try:
            m2 = M.check_page("https://x/p", must_contain=["gtag("])["metrics"]
        finally:
            M.http_get, M.http_head = orig_get, orig_head
        self.assertEqual(m2["must_contain_missing"], [])

    def test_ga_tracking_removed_warn(self):
        prev = {"pages": {"/p": {"status": 200, "must_contain_missing": []}}}
        curr = {"pages": {"/p": {"status": 200, "must_contain_missing": ["gtag("]}}}
        alerts = M.compute_alerts(prev, curr, CFG)
        hit = _hits(alerts, "ga_tracking_removed")
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["level"], "warn")
        self.assertEqual(hit[0]["details"]["missing"], ["gtag("])
        # 未配置断言(快照无键)→ 不触发
        none_curr = {"pages": {"/p": {"status": 200}}}
        self.assertFalse(_hits(M.compute_alerts(prev, none_curr, CFG), "ga_tracking_removed"))


# ---------- 4. 非规范域名重定向失效 ----------

class RedirectVariantTests(unittest.TestCase):
    """http:// 形态与裸域各 probe / broken→warn / error 防假 0 / 旧库兼容。"""

    def test_redirect_variant_urls(self):
        self.assertEqual(M.redirect_variant_urls("https://www.example.com"),
                         ["http://www.example.com", "https://example.com"])   # 降级+裸域
        self.assertEqual(M.redirect_variant_urls("https://example.com"),
                         ["http://example.com"])                              # 裸域站只剩降级形态
        self.assertEqual(M.redirect_variant_urls("http://example.com"), [])   # 无变体可测

    @staticmethod
    def _probe(site, responder):
        """responder(url) → {status, final_url} 或抛 FetchError。"""
        orig_get = M.http_get

        def fake_get(url, timeout=M.FETCH_TIMEOUT):
            r = responder(url)
            if isinstance(r, Exception):
                raise r
            return {"status": r["status"], "final_url": r["final_url"],
                    "elapsed_ms": 5.0, "body": "", "headers": {}}
        M.http_get = fake_get
        try:
            return M.check_redirect_variants(site)
        finally:
            M.http_get = orig_get

    def test_probe_ok_broken_error_states(self):
        site = "https://www.example.com"
        # 两个变体都 301 到 canonical host → ok
        out = self._probe(site, lambda u: {"status": 200, "final_url": site + "/"})
        self.assertEqual(out["state"], "ok")
        self.assertEqual(out["metrics"]["variants"],
                         {"http://www.example.com": "ok", "https://example.com": "ok"})
        # 变体在自己 host 直接 200(不再重定向)→ broken
        out2 = self._probe(site, lambda u: {"status": 200, "final_url": u})
        self.assertEqual(out2["state"], "ok")
        self.assertEqual(set(out2["metrics"]["variants"].values()), {"broken"})

    def test_probe_error_never_broken(self):
        """防假 0:probe 网络失败 = error,绝不判 broken(半数以上失败 → check 记 error)。"""
        site = "https://www.example.com"

        def responder(u):
            return {"status": 200, "final_url": u} if u.startswith("http://www.") \
                else M.FetchError("conn refused")
        out = self._probe(site, responder)
        self.assertEqual(out["metrics"]["variants"]["https://example.com"], "error")
        self.assertEqual(out["metrics"]["variants"]["http://www.example.com"], "broken")  # 真信号保留
        self.assertEqual(out["state"], "ok")                       # 1/2 失败=恰半数,不整判 error
        # 两个都失败 → 多数失败 → check state=error,无任何 broken
        out2 = self._probe(site, lambda u: M.FetchError("down"))
        self.assertEqual(out2["state"], "error")
        self.assertEqual(set(out2["metrics"]["variants"].values()), {"error"})
        self.assertTrue(any("防假 0" in n or "不当重定向失效" in n for n in out2["notes"]))

    def test_diff_redirect_chain_broken_and_old_db(self):
        prev = {"redirects": {"variants": {"http://example.com": "ok",
                                           "https://www.example.com": "ok"}}}
        curr = {"redirects": {"variants": {"http://example.com": "broken",
                                           "https://www.example.com": "error"}}}
        alerts = M.compute_alerts(prev, curr, CFG)
        hits = _hits(alerts, "redirect_chain_broken")
        self.assertEqual(len(hits), 1)                                   # 只 broken 告警,error 不判
        self.assertEqual(hits[0]["level"], "warn")
        self.assertEqual(hits[0]["key"], "http://example.com")
        self.assertIn("停止重定向——重复内容风险", hits[0]["message"])
        # 旧库无 redirects 快照键 → 不触发
        self.assertFalse(_hits(M.compute_alerts({}, {"pages": {}}, CFG), "redirect_chain_broken"))

    def test_end_to_end_snapshot_and_diff(self):
        """run→snapshot→diff 全链:variants 落快照,broken 进 diff 告警(离线合成结果)。"""
        mdir = _fresh_dir()
        results = {"redirects": {"check": "redirects", "state": "ok",
                                 "metrics": {"variants": {"http://www.example.com": "ok",
                                                          "https://example.com": "broken"}},
                                 "notes": []}}
        snap = M.snapshot_from_results(results)
        _insert_run(mdir, {"redirects": {"variants": {"http://www.example.com": "ok",
                                                      "https://example.com": "ok"}}})
        _insert_run(mdir, snap)
        out = os.path.join(mdir, "alerts.json")
        rc, _, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 2, "redirect_chain_broken warn → rc=2")
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertTrue(any(a["code"] == "redirect_chain_broken" for a in payload["alerts"]))


# ---------- 5. main_content_change(word_count 阈值) ----------

class WordCountTests(unittest.TestCase):
    """快照存 word_count;pct≥content_change_pct(默认 30)→ info。"""

    def test_word_count_html(self):
        html = "<p>alpha beta gamma</p><script>var junk='one two three four';</script>"
        self.assertEqual(M.word_count_html(html), 3)                     # script 剥离
        self.assertEqual(M.word_count_html("<style>.a{color:red}</style><p>one</p>"), 1)
        self.assertEqual(M.word_count_html(""), 0)
        self.assertGreaterEqual(M.word_count_html("<p>这是中文正文内容</p>"), 8)  # CJK 按字符计

    def test_threshold_default_and_custom(self):
        prev = {"pages": {"/p": {"status": 200, "word_count": 1000, "title": "t"}}}
        at30 = {"pages": {"/p": {"status": 200, "word_count": 700, "title": "t"}}}
        hit = _hits(M.compute_alerts(prev, at30, CFG), "main_content_change")
        self.assertEqual(len(hit), 1) and self.assertEqual(hit[0]["level"], "info")
        self.assertIn("主内容字数 1000→700(30%)", hit[0]["message"])    # 恰 30% ≥ 阈值触发
        self.assertEqual(hit[0]["details"]["pct"], 30.0)
        below = {"pages": {"/p": {"status": 200, "word_count": 750, "title": "t"}}}
        self.assertFalse(_hits(M.compute_alerts(prev, below, CFG), "main_content_change"))
        # 自定义阈值 10% → 25% 也触发
        cfg10 = {"site": "https://example.com",
                 "thresholds": dict(M.DEFAULT_THRESHOLDS, content_change_pct=10)}
        hit10 = _hits(M.compute_alerts(prev, below, cfg10), "main_content_change")
        self.assertTrue(hit10) and self.assertEqual(hit10[0]["details"]["pct"], 25.0)
        # 增长同样计(体量骤增也是改版信号)
        grew = {"pages": {"/p": {"status": 200, "word_count": 2000, "title": "t"}}}
        self.assertTrue(_hits(M.compute_alerts(prev, grew, CFG), "main_content_change"))
        # 旧库/prev 为 0 → 不猜
        self.assertFalse(_hits(M.compute_alerts(
            {"pages": {"/p": {"status": 200}}}, at30, CFG), "main_content_change"))
        zero_prev = {"pages": {"/p": {"status": 200, "word_count": 0}}}
        self.assertFalse(_hits(M.compute_alerts(zero_prev, at30, CFG), "main_content_change"))


# ---------- 6. digest 头部(improved / declined) ----------

class DigestTests(unittest.TestCase):
    """report 顶部 N improved, M declined(improved=上期有本期无;declined=本期新增)。"""

    def test_improved_then_declined_arc(self):
        mdir = _fresh_dir()
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 100}}})      # 基线
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 70}}})      # 掉 30% → warn
        rc, _, _ = _run_cmd(["diff", "--dir", mdir])
        self.assertEqual(rc, 2)
        rc, jout, _ = _run_cmd(["report", "--dir", mdir, "--days", "7", "--json"])
        rep = json.loads(jout)
        self.assertEqual(rep["declined"], ["gsc_clicks_drop:file"])     # 首次出现=新增
        self.assertEqual(rep["improved"], [])
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 100}}})     # 恢复
        rc, _, _ = _run_cmd(["diff", "--dir", mdir])
        self.assertEqual(rc, 0)
        rc, jout, _ = _run_cmd(["report", "--dir", mdir, "--days", "7", "--json"])
        rep2 = json.loads(jout)
        self.assertEqual(rep2["improved"], ["gsc_clicks_drop:file"])    # 上期有本期无
        self.assertEqual(rep2["declined"], [])
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 70}}})      # 再掉
        _run_cmd(["diff", "--dir", mdir])
        rc, tout, _ = _run_cmd(["report", "--dir", mdir, "--days", "7"])
        self.assertIn("0 improved, 1 declined", tout)
        rc, jout3, _ = _run_cmd(["report", "--dir", mdir, "--days", "7", "--json"])
        rep3 = json.loads(jout3)
        self.assertEqual(rep3["improved"], [])
        self.assertEqual(rep3["declined"], ["gsc_clicks_drop:file"])

    def test_no_history_yields_zero_zero(self):
        mdir = _fresh_dir()
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 100}}})
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 100}}})
        _run_cmd(["diff", "--dir", mdir])                               # 无告警
        rc, tout, _ = _run_cmd(["report", "--dir", mdir, "--days", "7"])
        self.assertEqual(rc, 0)
        self.assertIn("0 improved, 0 declined", tout)                   # 窗口内不足两期=不猜
        rc, jout, _ = _run_cmd(["report", "--dir", mdir, "--days", "7", "--json"])
        rep = json.loads(jout)
        self.assertEqual((rep["improved"], rep["declined"]), ([], []))


# ---------- 7. 多断言(expect 数组 / max_latency_ms / selector_stable) ----------

class MultiAssertionTests(unittest.TestCase):
    """expect 单条→数组向后兼容;绝对时延上限;首个 h2 布局锚。"""

    @staticmethod
    def _check(body, **kw):
        orig_get, orig_head = M.http_get, M.http_head
        M.http_get = lambda url, timeout=M.FETCH_TIMEOUT: {
            "status": 200, "final_url": url, "elapsed_ms": kw.pop("elapsed_ms", 5.0),
            "body": body, "headers": {}}
        M.http_head = lambda u, timeout=M.FETCH_TIMEOUT: {"status": 200}
        try:
            return M.check_page("https://example.com/p", **kw)["metrics"]
        finally:
            M.http_get, M.http_head = orig_get, orig_head

    def test_parse_key_page_backcompat_and_assertions(self):
        # 单条 str(P1 前形态)→ 列表
        o = M.parse_key_page({"path": "/p", "expect_substring": "Price"})
        self.assertEqual(o["expect"], ["Price"])
        # 数组形态
        o2 = M.parse_key_page({"path": "/p", "expect_substring": ["Price", "Buy"]})
        self.assertEqual(o2["expect"], ["Price", "Buy"])
        # assertions 嵌套与顶层同名键等价;空串过滤
        o3 = M.parse_key_page({"path": "/p", "assertions": {
            "must_contain": ["gtag(", ""], "max_latency_ms": 800, "selector_stable": True}})
        self.assertEqual(o3["must_contain"], ["gtag("])
        self.assertEqual(o3["max_latency_ms"], 800.0)
        self.assertTrue(o3["selector_stable"])
        o4 = M.parse_key_page({"path": "/p", "max_latency_ms": "900", "selector_stable": 1})
        self.assertEqual(o4["max_latency_ms"], 900.0)
        self.assertTrue(o4["selector_stable"])
        # 坏值容错
        o5 = M.parse_key_page({"path": "/p", "max_latency_ms": "fast"})
        self.assertIsNone(o5["max_latency_ms"])
        # str 条目与裸 path 补斜杠
        self.assertEqual(M.parse_key_page("/x")["path"], "/x")
        self.assertEqual(M.parse_key_page("x")["path"], "/x")

    def test_expect_array_partial_missing(self):
        body = "<title>t</title><p>Price list here</p>"
        m = self._check(body, expect=["Price", "Stock", ""])           # 空串丢弃
        self.assertIs(m["expect_ok"], False)
        self.assertEqual(m["expect_missing"], ["Stock"])
        prev = {"pages": {"/p": {"status": 200, "expect_ok": True}}}
        curr = {"pages": {"/p": {"status": 200, "expect_ok": False,
                                 "expect_missing": ["Stock"]}}}
        hit = _hits(M.compute_alerts(prev, curr, CFG), "content_regression")
        self.assertEqual(len(hit), 1) and self.assertEqual(hit[0]["level"], "warn")
        self.assertEqual(hit[0]["details"]["missing"], ["Stock"])

    def test_max_latency_ms_absolute_assert(self):
        cfg = {"site": "https://example.com", "thresholds": dict(M.DEFAULT_THRESHOLDS),
               "key_pages": [{"path": "/p", "assertions": {"max_latency_ms": 300}}]}
        prev = {"pages": {"/p": {"status": 200, "latency_ms": 100.0}}}
        curr = {"pages": {"/p": {"status": 200, "latency_ms": 500.0}}}
        hits = _hits(M.compute_alerts(prev, curr, cfg), "latency_spike")
        self.assertTrue(any("max_latency_ms=300ms" in h["message"] for h in hits))   # 绝对口径
        # 低于上限 → 无绝对告警(pct 相对阈值 100/500 也不触发)
        curr_ok = {"pages": {"/p": {"status": 200, "latency_ms": 200.0}}}
        self.assertFalse(_hits(M.compute_alerts(prev, curr_ok, cfg), "latency_spike"))
        # 未配置该断言的页不受影响
        plain = {"site": "https://example.com", "thresholds": dict(M.DEFAULT_THRESHOLDS)}
        self.assertFalse(any("max_latency_ms" in h["message"]
                             for h in M.compute_alerts(prev, curr, plain)))

    def test_selector_stable_layout_shift(self):
        body = "<title>t</title><h1>H</h1><h2>Original Section</h2><p>x</p>"
        m = self._check(body, selector_stable=True)
        self.assertEqual(m["h2"], "Original Section")                   # 快照存首个 h2
        m2 = self._check(body.replace("Original Section", "New Section"))
        self.assertNotIn("h2", m2)                                      # 未开断言不存
        prev = {"pages": {"/p": {"status": 200, "h2": "Original Section", "title": "t"}}}
        curr = {"pages": {"/p": {"status": 200, "h2": "New Section", "title": "t"}}}
        hit = _hits(M.compute_alerts(prev, curr, CFG), "layout_shift")
        self.assertEqual(len(hit), 1) and self.assertEqual(hit[0]["level"], "info")
        self.assertEqual(hit[0]["details"], {"prev_h2": "Original Section",
                                            "curr_h2": "New Section"})
        # 旧快照无 h2 键 → 不触发
        self.assertFalse(_hits(M.compute_alerts(
            {"pages": {"/p": {"status": 200}}}, curr, CFG), "layout_shift"))


# ---------- 防假 0 纪律复核(serpbear) ----------

class AntiFakeZeroTests(unittest.TestCase):
    """请求失败/被拦 → error/skipped/blocked,绝不判"排名消失/重定向失效"。"""

    def test_visibility_blocked_not_rank_loss(self):
        prev = {"visibility": {"site": {"state": "ok", "visible_pages": 5}}}
        for bad_state in ("blocked", "skipped", "unparseable", "error"):
            curr = {"visibility": {"site": {"state": bad_state}}}
            alerts = M.compute_alerts(prev, curr, CFG)
            self.assertFalse(_hits(alerts, "visibility_zero"),
                             "%s 不该被当成可见性归零" % bad_state)
            self.assertFalse(_hits(alerts, "visibility_drop"))
        # 端点 ok 且样本过地板 → 真 0 才告(守卫不吞真信号)
        true_zero = {"visibility": {"site": {"state": "ok", "visible_pages": 0}}}
        self.assertTrue(_hits(M.compute_alerts(prev, true_zero, CFG), "visibility_zero"))

    def test_redirect_probe_error_not_ranked_broken(self):
        prev = {"redirects": {"variants": {"https://example.com": "ok"}}}
        curr = {"redirects": {"variants": {"https://example.com": "error"}}}
        self.assertFalse(_hits(M.compute_alerts(prev, curr, CFG), "redirect_chain_broken"))
        # check 级多数失败 → state=error 落快照后同样不产告警
        err_state = {"redirects": {"variants": {"state": "error"}}}
        self.assertFalse(_hits(M.compute_alerts(prev, err_state, CFG), "redirect_chain_broken"))

    def test_fetch_error_not_field_removal(self):
        """连续抓取失败(fetch_error_confirmed)不连带误报 meta_removed(渲染守卫)。"""
        prev = {"pages": {"/p": {"status": 200, "title": "T", "meta_desc": "M"}}}
        curr = {"pages": {"/p": {"state": "error", "error": "timeout"}}}
        alerts = M.compute_alerts(prev, curr, CFG)
        self.assertFalse(_hits(alerts, "meta_removed"))
        self.assertTrue(_hits(alerts, "fetch_error_single"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
