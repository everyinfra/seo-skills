#!/usr/bin/env python3
"""monitor.py D1 P1 扩展测试(standalone,合成 config/db,零网络;
tests/run_tests.py 自动发现本文件)。覆盖五项:
1 segments 模型:regex 归属(首个命中)/importance(static|gsc_clicks,无数据=1)/
  受影响度=Σimportance 替代纯页数/10% 档触发(Conductor 7 档中的 10% 档)/
  sitewide 根因抑制/GSC 页级点击解析(page_clicks)
2 accepted_codes 白名单:命中降 low+accepted:true(不计 counts/退出码)/
  code:key 指纹形态/周报"已接受告警数"仍计数(接受≠消失)
3 diff --ci:checks 结构 {metric,operator,threshold,actual,passed} 每条阈值规则一行
  (含通过项)/任一失败 exit 10(siteone 契约)/--ci-format junit
4 sample-keypages:末段 slug 归一/模板分组随机抽 N(默认 8,seed 可复现)/
  ∪ 现有手工 key_pages/默认不写 config(--write 才合并)/maxRoutes=200 上限警告
5 baseline 缺失响亮警告:库龄>7 天无 7 天基线 → stderr 大写 WARNING +
  payload baseline_missing:true(绝不静默);库龄≤7 天不误报。"""
import contextlib
import io
import json
import os
import random
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import monitor as M  # noqa: E402

CFG = {"site": "https://example.com", "thresholds": dict(M.DEFAULT_THRESHOLDS)}

HEALTHY = {"status": 200, "indexable": True}


def _fresh_dir(key_pages="/"):
    tmp = tempfile.mkdtemp(prefix="mon_p1_")
    mdir = os.path.join(tmp, ".seo-monitor")
    rc = M.cmd_init(M.build_parser().parse_args(
        ["init", "--site", "https://example.com", "--market", "us",
         "--key-pages", key_pages, "--dir", mdir]))
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


# ---------- 1. segments 模型 ----------

class SegmentModelTests(unittest.TestCase):
    """regex 归属 / importance 口径 / 健康集判定。"""

    def test_segment_attribution_first_match(self):
        cfg = {"segments": [
            {"name": "docs", "match": "^/docs/", "importance": "static"},
            {"name": "docs-old", "match": "^/docs/", "importance": "static"},
            {"name": "shop", "match": r"^/shop/"}]}
        self.assertEqual(M.segment_of("/docs/guide", cfg)["name"], "docs")       # 首个命中
        self.assertEqual(M.segment_of("/shop/item-1", cfg)["name"], "shop")      # 无 importance 默认 static
        self.assertIsNone(M.segment_of("/pricing", cfg))                         # 不命中 → 无归属
        self.assertIsNone(M.segment_of("/x", {}))                                # 无 segments
        bad = {"segments": [{"name": "bad", "match": "(", "importance": "static"}]}
        self.assertIsNone(M.segment_of("/x", bad))                               # 坏 regex 跳过不崩

    def test_page_importance_modes(self):
        docs = {"name": "docs", "importance": "static"}
        shop = {"name": "shop", "importance": "gsc_clicks"}
        clicks = {"/shop/a": 99, "/shop/b": 1}
        self.assertEqual(M.page_importance(docs, "/shop/a", clicks), 1.0)        # static 恒 1
        self.assertEqual(M.page_importance(shop, "/shop/a", clicks), 99.0)
        self.assertEqual(M.page_importance(shop, "/shop/b", clicks), 1.0)
        self.assertEqual(M.page_importance(shop, "/shop/z", clicks), 1.0)        # 未列出=1,不猜 0
        self.assertEqual(M.page_importance(shop, "/shop/a", {}), 1.0)            # 无 gsc 数据=1
        self.assertEqual(M.page_importance(shop, "/shop/a", None), 1.0)
        self.assertEqual(M.page_importance(None, "/any", clicks), 1.0)           # 无 segment

    def test_page_healthy_matrix(self):
        self.assertTrue(M.page_healthy(HEALTHY))
        self.assertTrue(M.page_healthy({"status": 200}))                  # 旧快照缺 indexable:猜不出 False
        self.assertFalse(M.page_healthy({"status": 404, "indexable": True}))
        self.assertFalse(M.page_healthy({"status": 200, "indexable": False}))    # noindex=退出健康集
        self.assertFalse(M.page_healthy({"state": "error", "error": "x"}))
        self.assertFalse(M.page_healthy({"state": "budget_skipped"}))
        self.assertFalse(M.page_healthy("junk"))


class SegmentAlertTests(unittest.TestCase):
    """pages_left_segment:10% 档(Conductor)/Σimportance 加权/sitewide 抑制。"""

    DOCS_CFG = {"segments": [{"name": "docs", "match": "^/docs/", "importance": "static"}],
                "thresholds": dict(M.DEFAULT_THRESHOLDS)}

    @staticmethod
    def _docs(n, broken=()):
        return {"/docs/p%02d" % i: ({"status": 404} if i in broken else dict(HEALTHY))
                for i in range(n)}

    def test_ten_pct_tier_fires(self):
        """10 页掉 1 = 恰 10%(7 档中的 10% 档边界,≥ 触发)→ warn。"""
        prev = {"pages": self._docs(10)}
        curr = {"pages": self._docs(10, broken={4})}
        hit = [a for a in M.compute_alerts(prev, curr, self.DOCS_CFG)
               if a["code"] == "pages_left_segment"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["level"], "warn")
        self.assertEqual(hit[0]["key"], "segment:docs")
        self.assertEqual(hit[0]["details"]["pct"], 10.0)
        self.assertEqual(hit[0]["details"]["prev_healthy"], 10)
        self.assertEqual(hit[0]["details"]["curr_healthy"], 9)
        self.assertEqual(hit[0]["details"]["dropped"], ["/docs/p04"])
        self.assertIn("Σimportance", hit[0]["message"])
        # 无流失 → 不告警
        self.assertFalse(any(a["code"] == "pages_left_segment"
                             for a in M.compute_alerts(prev, {"pages": self._docs(10)}, self.DOCS_CFG)))

    def test_below_ten_pct_no_fire(self):
        """20 页掉 1 = 5% <10% 档 → 不告警(单页由 key_page_down 自己报)。"""
        prev = {"pages": self._docs(20)}
        curr = {"pages": self._docs(20, broken={7})}
        self.assertFalse(any(a["code"] == "pages_left_segment"
                             for a in M.compute_alerts(prev, curr, self.DOCS_CFG)))
        self.assertTrue(any(a["code"] == "key_page_down"
                            for a in M.compute_alerts(prev, curr, self.DOCS_CFG)))

    def test_noindex_counts_as_leaving_and_absent_page_not_counted(self):
        prev = {"pages": self._docs(10)}
        noindex_curr = {"pages": self._docs(10)}
        noindex_curr["pages"]["/docs/p02"] = {"status": 200, "indexable": False,
                                              "noindex_source": "meta"}     # noindex=离开健康集
        self.assertTrue(any(a["code"] == "pages_left_segment"
                            for a in M.compute_alerts(prev, noindex_curr, self.DOCS_CFG)))
        gone_curr = {"pages": self._docs(10)}
        del gone_curr["pages"]["/docs/p03"]                                # 停止监控≠流失(不猜)
        self.assertFalse(any(a["code"] == "pages_left_segment"
                             for a in M.compute_alerts(prev, gone_curr, self.DOCS_CFG)))

    def test_importance_weighted_not_page_count(self):
        """受影响度=Σimportance 替代纯页数:2 页 segment 按页数掉 50%,
        但 gsc_clicks 加权后低重要页只占 1% → 不告警;高重要页占 99% → 告警。"""
        cfg = {"segments": [{"name": "shop", "match": "^/shop/", "importance": "gsc_clicks"}],
               "thresholds": dict(M.DEFAULT_THRESHOLDS)}
        prev = {"pages": {"/shop/a": dict(HEALTHY), "/shop/b": dict(HEALTHY)},
                "gsc": {"file": {"clicks_total": 100,
                                 "page_clicks": {"/shop/a": 99, "/shop/b": 1}}}}
        low_drops = {"pages": {"/shop/a": dict(HEALTHY), "/shop/b": {"status": 500}},
                     "gsc": prev["gsc"]}
        self.assertFalse(any(a["code"] == "pages_left_segment"
                             for a in M.compute_alerts(prev, low_drops, cfg)),
                         "页数掉 50% 但 Σimportance 只 1%:不该按页数地板告警")
        high_drops = {"pages": {"/shop/a": {"status": 500}, "/shop/b": dict(HEALTHY)},
                      "gsc": prev["gsc"]}
        hit = [a for a in M.compute_alerts(prev, high_drops, cfg)
               if a["code"] == "pages_left_segment"]
        self.assertTrue(hit)
        self.assertEqual(hit[0]["details"]["dropped_importance"], 99.0)
        self.assertEqual(hit[0]["details"]["total_importance"], 100.0)
        # 无 gsc 页级数据 → 每页 importance=1(2 页掉 1=50% ≥10% → 告警)
        no_gsc = {"pages": {"/shop/a": dict(HEALTHY), "/shop/b": {"status": 500}}}
        prev_pages_only = {"pages": dict(prev["pages"])}
        self.assertTrue(any(a["code"] == "pages_left_segment"
                            for a in M.compute_alerts(prev_pages_only, no_gsc, cfg)))

    def test_inhibited_by_sitewide_roots(self):
        """sitewide 根因(首页宕机)在场 → segment 聚合流失折叠(派生信号)。"""
        cfg = {"segments": [{"name": "docs", "match": "^/docs/", "importance": "static"}],
               "thresholds": dict(M.DEFAULT_THRESHOLDS)}
        prev = {"pages": dict({"/": dict(HEALTHY)}, **self._docs(10))}
        curr = {"pages": dict({"/": {"status": 503}},
                              **{k: ({"status": 404} if k == "/docs/p00" else dict(v))
                                 for k, v in self._docs(10).items()})}
        inhib = []
        alerts = M.compute_alerts(prev, curr, cfg, inhibited_out=inhib)
        self.assertFalse(any(a["code"] == "pages_left_segment" for a in alerts))
        self.assertTrue(any(i["code"] == "pages_left_segment"
                            and i["inhibited_by"] == "homepage_down" for i in inhib))


class GscPageClicksTests(unittest.TestCase):
    """check_gsc:页级导出(Page 列)→ page_clicks 归一化路径求和;无 Page 列不产出。"""

    def test_page_clicks_parsed_and_normalized(self):
        tmp = tempfile.mkdtemp(prefix="mon_gsc_")
        with open(os.path.join(tmp, "gsc.csv"), "w", encoding="utf-8") as f:
            f.write("Page,Query,Clicks,Impressions\n"
                    "https://example.com/docs/a,q1,3,10\n"
                    "https://example.com/docs/a,q2,2,10\n"
                    "https://example.com/docs/b,q1,1,10\n")
        out = M.check_gsc(tmp)
        self.assertEqual(out["state"], "ok")
        self.assertEqual(out["metrics"]["clicks_total"], 6)
        self.assertEqual(out["metrics"]["page_clicks"], {"/docs/a": 5, "/docs/b": 1})
        # 无 Page 列(纯 query 导出)→ 不产 page_clicks 键
        tmp2 = tempfile.mkdtemp(prefix="mon_gsc2_")
        with open(os.path.join(tmp2, "gsc.csv"), "w", encoding="utf-8") as f:
            f.write("Query,Clicks,Impressions\nq1,7,10\n")
        out2 = M.check_gsc(tmp2)
        self.assertEqual(out2["metrics"]["clicks_total"], 7)
        self.assertNotIn("page_clicks", out2["metrics"])


# ---------- 2. accepted_codes 白名单 ----------

class AcceptedCodesTests(unittest.TestCase):
    """命中降 low+accepted:true / code:key 指纹 / 周报已接受计数 / 不进退出码。"""

    def test_apply_accepted_bare_code_and_fingerprint(self):
        alerts = [
            {"level": "warn", "code": "gsc_clicks_drop", "key": "file", "message": "m1",
             "details": {}, "action": "a", "boundary": "human"},
            {"level": "critical", "code": "noindex_added", "key": "/x", "message": "m2",
             "details": {}, "action": "a", "boundary": "auto"},
            {"level": "info", "code": "title_meta_drift", "key": "/y", "message": "m3",
             "details": {}, "action": "a", "boundary": "human"}]
        n = M.apply_accepted(alerts, {"accepted_codes": ["gsc_clicks_drop", "noindex_added:/x"]})
        self.assertEqual(n, 2)
        lv = {a["code"]: a for a in alerts}
        self.assertEqual((lv["gsc_clicks_drop"]["level"], lv["gsc_clicks_drop"]["accepted"],
                          lv["gsc_clicks_drop"]["from_level"]), ("low", True, "warn"))
        self.assertTrue(lv["noindex_added"]["accepted"])                       # code:key 指纹命中
        self.assertNotIn("accepted", lv["title_meta_drift"])                   # 未命中原样
        self.assertEqual(lv["title_meta_drift"]["level"], "info")
        # 空/缺省配置零影响
        untouched = [dict(a) for a in alerts]
        self.assertEqual(M.apply_accepted(untouched, {}), 0)

    def test_end_to_end_diff_and_report_counting(self):
        mdir = _fresh_dir()
        cfg = M.load_config(mdir)
        cfg["accepted_codes"] = ["gsc_clicks_drop"]
        M.save_config(mdir, cfg)
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 100}}})
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 70}}})            # −30% 过 20% 阈值
        out = os.path.join(mdir, "alerts.json")
        rc, stdout, _ = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 0, "accepted 降 low 后不计入退出码(原本 warn 会 rc=2)")
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        hit = [a for a in payload["alerts"] if a["code"] == "gsc_clicks_drop"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["level"], "low")
        self.assertTrue(hit[0]["accepted"])
        self.assertEqual(hit[0]["from_level"], "warn")
        self.assertIn("接受≠消失", hit[0]["message"])
        self.assertEqual(payload["counts"]["warn"], 0)
        self.assertEqual(payload["suppressed"], [])                            # accepted 不走 cooldown
        self.assertEqual(payload["accepted"], 1)
        # 周报:"已接受告警数"单独列出(接受≠消失,仍计数)
        rc, jout, _ = _run_cmd(["report", "--dir", mdir, "--days", "7", "--json"])
        rep = json.loads(jout)
        self.assertEqual(rep["accepted_alerts"], 1)
        self.assertEqual(rep["alerts"][0]["level"], "low")
        rc2, tout, _ = _run_cmd(["report", "--dir", mdir, "--days", "7"])
        self.assertIn("已接受告警", tout)
        self.assertIn("1 条", tout)
        # 未接受对照组:同数据无白名单 → warn rc=2
        mdir2 = _fresh_dir()
        _insert_run(mdir2, {"gsc": {"file": {"clicks_total": 100}}})
        _insert_run(mdir2, {"gsc": {"file": {"clicks_total": 70}}})
        rc3, _, _ = _run_cmd(["diff", "--dir", mdir2])
        self.assertEqual(rc3, 2)


# ---------- 3. diff --ci ----------

class CiModeTests(unittest.TestCase):
    """checks 结构(每条阈值规则一行,含通过项)/exit 10(siteone 契约)/junit。"""

    @staticmethod
    def _healthy_dir():
        mdir = _fresh_dir()
        snap = {"pages": {"/": {"status": 200, "latency_ms": 100.0, "title": "T"}},
                "visibility": {"site": {"state": "ok", "visible_pages": 5}}}
        _insert_run(mdir, snap)
        _insert_run(mdir, snap)
        return mdir

    def test_ci_pass_all_checks_listed(self):
        mdir = self._healthy_dir()
        rc, out, _ = _run_cmd(["diff", "--dir", mdir, "--ci"])
        self.assertEqual(rc, 0)
        ci = json.loads(out)
        self.assertTrue(ci["passed"])
        self.assertEqual(ci["exit_code"], 0)
        metrics = {c["metric"] for c in ci["checks"]}
        for m in ("visibility_drop_pct", "visibility_min_sample", "sitemap_urls_drop_pct",
                  "sitemap_min_sample", "gsc_clicks_drop_pct", "gsc_min_clicks",
                  "latency_increase_pct", "latency_min_ms", "mixed_content_min",
                  "critical_alerts", "warn_alerts"):
            self.assertIn(m, metrics, "每条阈值规则一行(含通过项)")
        for c in ci["checks"]:
            self.assertEqual(set(c), {"metric", "operator", "threshold", "actual", "passed"})
            self.assertTrue(c["passed"])
            self.assertIn(c["operator"], ("<", ">=", "=="))
        by = {c["metric"]: c for c in ci["checks"]}
        self.assertEqual(by["visibility_min_sample"]["actual"], 5)             # 通过项也带 actual
        self.assertEqual(by["visibility_drop_pct"]["actual"], 0.0)

    def test_ci_breach_exit_10(self):
        mdir = _fresh_dir()
        base = {"pages": {"/": {"status": 200, "latency_ms": 100.0, "title": "T"}},
                "visibility": {"site": {"state": "ok", "visible_pages": 5}},
                "gsc": {"file": {"clicks_total": 100}}}
        _insert_run(mdir, base)                                             # run1(兼 7 天基线候选)
        _insert_run(mdir, base)                                             # prev
        _insert_run(mdir, {"pages": base["pages"],
                           "visibility": base["visibility"],
                           "gsc": {"file": {"clicks_total": 70}}})          # curr:−30% 过 20% 阈值
        rc, out, _ = _run_cmd(["diff", "--dir", mdir, "--ci", "--dry-run"])
        self.assertEqual(rc, 10, "任一 check 失败 → exit 10(siteone 契约)")
        ci = json.loads(out)
        self.assertFalse(ci["passed"])
        self.assertEqual(ci["exit_code"], 10)
        failing = {c["metric"] for c in ci["checks"] if not c["passed"]}
        self.assertEqual(failing, {"gsc_clicks_drop_pct", "warn_alerts"})
        by = {c["metric"]: c for c in ci["checks"]}
        self.assertEqual(by["gsc_clicks_drop_pct"]["actual"], 30.0)           # 100→70 = −30%
        self.assertEqual(by["gsc_clicks_drop_pct"]["threshold"], 20)
        self.assertEqual(by["gsc_clicks_drop_pct"]["operator"], "<")
        self.assertTrue(by["gsc_min_clicks"]["passed"])                       # min(100,70)≥5
        self.assertTrue(by["critical_alerts"]["passed"])
        self.assertTrue(by["visibility_min_sample"]["passed"])                # 样本 5 ≥ 地板 3
        # 普通模式仍是 monitor 契约 rc=2,互不干扰(dry-run 防两次 diff 间 cooldown 抑制串扰)
        rc2, _, _ = _run_cmd(["diff", "--dir", mdir, "--dry-run"])
        self.assertEqual(rc2, 2)

    def test_ci_junit_xml(self):
        mdir = _fresh_dir()
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 100}}})
        _insert_run(mdir, {"gsc": {"file": {"clicks_total": 70}}})
        rc, out, _ = _run_cmd(["diff", "--dir", mdir, "--ci", "--ci-format", "junit"])
        self.assertEqual(rc, 10)
        self.assertTrue(out.startswith("<?xml"))
        self.assertIn('<testsuites name="monitor-diff"', out)
        self.assertIn('failures="2"', out)                                    # drop 行+warn 聚合行
        self.assertIn("ThresholdBreached", out)
        self.assertIn("gsc_clicks_drop_pct", out)
        self.assertIn('classname="monitor.diff"', out)
        # 全绿 → junit 无 failure 节点,rc=0
        mdir2 = self._healthy_dir()
        rc2, out2, _ = _run_cmd(["diff", "--dir", mdir2, "--ci", "--ci-format", "junit"])
        self.assertEqual(rc2, 0)
        self.assertNotIn("<failure", out2)
        self.assertIn('failures="0"', out2)


# ---------- 4. sample-keypages ----------

class SampleKeypagesTests(unittest.TestCase):
    """slug 归一 / 模板分组抽样 ∪ 手工 / seed 复现 / --write / maxRoutes 200。"""

    def test_slug_template_normalization(self):
        self.assertEqual(M.slug_template("/blog/seo-tips-2026"), "/blog/slug")
        self.assertEqual(M.slug_template("/blog/"), "/blog/")             # 尾斜杠=栏目页,末段空不替换
        self.assertEqual(M.slug_template("/"), "/")
        self.assertEqual(M.slug_template("https://example.com/products/12345?utm=x"),
                         "/products/slug")                                 # 查询/锚点丢弃
        self.assertEqual(M.slug_template("/about"), "/slug")               # 单段页 → /slug
        self.assertEqual(M.slug_template("/a/b/c.html"), "/a/b/slug")

    def test_sampling_per_group_and_union_with_manual(self):
        urls = ["https://example.com/blog/p%02d" % i for i in range(20)] \
            + ["https://example.com/shop/%d" % i for i in range(3)]
        res = M.sample_keypages(urls, 8, ["/pricing"], random.Random(0))
        blog = [p for p in res["new"] if p.startswith("/blog/")]
        shop = [p for p in res["new"] if p.startswith("/shop/")]
        self.assertEqual(len(blog), 8)                                     # 20 页模板每组抽 8
        self.assertEqual(len(shop), 3)                                     # 不足 8 全取
        self.assertEqual(res["picked"][0], "/pricing")                     # ∪ 手工(在前,保序)
        self.assertEqual(len(res["picked"]), 1 + 8 + 3)
        # 同 seed 可复现;不同 per-group 生效
        res2 = M.sample_keypages(urls, 8, ["/pricing"], random.Random(0))
        self.assertEqual(res["new"], res2["new"])
        res3 = M.sample_keypages(urls, 2, [], random.Random(0))
        self.assertEqual(len(res3["new"]), 2 + 2)                          # 两组都超 2 → 各抽 2
        # 手工页在 sitemap 里也出现 → 去重不重复列
        res4 = M.sample_keypages(["https://example.com/pricing", "https://example.com/x"],
                                 8, ["/pricing"], random.Random(0))
        self.assertEqual(res4["picked"].count("/pricing"), 1)

    def test_cli_prints_only_until_write(self):
        mdir = _fresh_dir(key_pages="/pricing,/about")
        urls_file = os.path.join(os.path.dirname(mdir), "urls.txt")
        with open(urls_file, "w", encoding="utf-8") as f:
            f.write("\n".join(
                ["https://example.com/blog/%s" % chr(ord("a") + i) for i in range(26)]
                + ["https://example.com/pricing"]            # 已在手工 → 去重
                + ["https://example.com/shop/%d" % i for i in range(5)]))
        rc, out, err = _run_cmd(["sample-keypages", "--urls", urls_file, "--dir", mdir])
        self.assertEqual(rc, 0)
        self.assertIn("/blog/slug", out)
        self.assertIn("/shop/slug", out)
        self.assertIn("← 新增", out)
        self.assertEqual(err, "")                                          # 200 内不告警
        self.assertEqual(M.load_config(mdir)["key_pages"], ["/pricing", "/about"],
                         "默认不写 config")
        # --write:合并去重,手工条目保留在最前
        rc2, out2, _ = _run_cmd(["sample-keypages", "--urls", urls_file, "--dir", mdir, "--write"])
        self.assertEqual(rc2, 0)
        kp = M.load_config(mdir)["key_pages"]
        self.assertEqual(kp[:2], ["/pricing", "/about"])
        self.assertEqual(len([p for p in kp if p.startswith("/blog/")]), 8)
        self.assertEqual(len([p for p in kp if p.startswith("/shop/")]), 5)
        self.assertEqual(len(kp), 2 + 8 + 5)
        self.assertEqual(len(set(kp)), len(kp), "无重复")

    def test_maxroutes_cap_warning(self):
        mdir = _fresh_dir()
        urls_file = os.path.join(os.path.dirname(mdir), "urls2.txt")
        with open(urls_file, "w", encoding="utf-8") as f:
            f.write("\n".join("https://example.com/t%03d/x" % i for i in range(250)))
        rc, out, err = _run_cmd(["sample-keypages", "--urls", urls_file, "--dir", mdir,
                                 "--per-group", "1"])
        self.assertEqual(rc, 0)
        self.assertIn("WARNING", err)
        self.assertIn("maxRoutes=200", err)
        self.assertEqual(out.count("← 新增"), M.MAX_ROUTES, "截断到 200 条")
        self.assertEqual(len(M.load_config(mdir)["key_pages"]), 1)         # 未 --write 不动 config


# ---------- 5. baseline 缺失响亮警告 ----------

class BaselineMissingTests(unittest.TestCase):
    """库龄>7 天取不到 7 天基线 → stderr 大写 WARNING + payload baseline_missing:true。"""

    def test_old_library_warns_loudly(self):
        mdir = _fresh_dir()
        snap = {"pages": {"/": {"status": 200, "title": "T"}}}
        _insert_run(mdir, snap, ts_offset_days=8)                          # 唯一可用基线候选太老
        _insert_run(mdir, snap)
        out = os.path.join(mdir, "alerts.json")
        rc, _, err = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 0)
        self.assertIn("WARNING", err)
        self.assertIn("无 7 天基线", err)
        self.assertIn("双窗口降级未生效", err)
        self.assertRegex(err, r"库龄 8\.\dd")
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertIs(payload["baseline_missing"], True)
        self.assertIsNone(payload["baseline_run"])

    def test_young_library_no_false_alarm(self):
        mdir = _fresh_dir()
        snap = {"pages": {"/": {"status": 200, "title": "T"}}}
        _insert_run(mdir, snap, ts_offset_days=3)                          # 库龄 3 天:取不到基线属预期
        _insert_run(mdir, snap)
        out = os.path.join(mdir, "alerts.json")
        rc, _, err = _run_cmd(["diff", "--dir", mdir, "--out", out])
        self.assertEqual(rc, 0)
        self.assertNotIn("WARNING", err)
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertIs(payload["baseline_missing"], False)                  # 键恒在,不静默真缺失


if __name__ == "__main__":
    unittest.main(verbosity=1)
