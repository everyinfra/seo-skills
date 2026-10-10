#!/usr/bin/env python3
"""changelog.py 测试(Conductor Changelog 官方口径,standalone,合成快照,零网络):
五枚举事件生成 / 字段白名单过滤与不追踪提示 / hreflang 顺序无关 / 14 天日粒度
与更早周折叠(保留最后一次+计数) / 检索过滤(窗+url+type) / summary 频次 /
首见=added / monitor.db 输入对齐 / noindex 翻转根因场景 / CLI 契约。
python3 tests/test_changelog.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。

时间基准全部用 --to 2026-10-10 钉死(粒度规则: 距该日<14 天按日,更早按周),
不依赖真实今天。ISO 周标签用被测模块的 week_label 现算,避免手写错周号。"""
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import changelog as cg  # noqa: E402  (需先入 SCRIPTS 路径)


def run_script(name, args=()):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def snaps_file(records):
    fd, path = tempfile.mkstemp(suffix=".json", prefix="chlog_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False)
    return path


def snap(url, ts, **fields):
    return {"url": url, "ts": ts, "fields": fields}


def cli_payload(records, *extra):
    """"合成快照 → CLI --json(默认钉 --to 2026-10-10)→ 解析后的 payload。"""
    path = snaps_file(records)
    argv = ["--snaps", path, "--json", "--to", "2026-10-10", *extra]
    r = run_script("changelog.py", argv)
    os.unlink(path)
    if r.returncode != 0:
        raise AssertionError("CLI 失败 rc=%d: %s%s" % (r.returncode, r.stdout, r.stderr))
    return json.loads(r.stdout)


def cli_text(records, *extra):
    path = snaps_file(records)
    argv = ["--snaps", path, "--to", "2026-10-10", *extra]
    r = run_script("changelog.py", argv)
    os.unlink(path)
    if r.returncode != 0:
        raise AssertionError("CLI 失败 rc=%d: %s%s" % (r.returncode, r.stdout, r.stderr))
    return r.stdout


class EventGenerationTests(unittest.TestCase):
    """change_type 5 枚举【官方】/ hreflang 顺序无关 / 事件 schema 键。"""

    MULTI = [
        snap("https://x.com/a", "2026-10-01T00:00:00", status=200, title="A1"),
        snap("https://x.com/a", "2026-10-03T00:00:00", status=200, title="A2"),
        snap("https://x.com/a", "2026-10-05T00:00:00", status=404),
        snap("https://x.com/b", "2026-10-02T00:00:00", status=200, title="B1"),
        snap("https://x.com/b", "2026-10-04T00:00:00", status=301),
        snap("https://x.com/c", "2026-10-02T00:00:00", status=200, title="C1"),
        snap("https://x.com/c", "2026-10-06T00:00:00", status=503),
    ]

    def test_five_change_types(self):
        """"首见=added、title 变=changed、404=removed、301=redirected、503=other,
        5 枚举齐全;事件 schema 含官方 6 键+snapshot 溯源。"""
        events = cli_payload(self.MULTI)["events"]
        self.assertEqual({e["change_type"] for e in events},
                         {"changed", "added", "removed", "redirected", "other"})
        for e in events:
            self.assertTrue({"url", "ts", "change_type", "property", "old", "new"}
                            <= set(e), e)
        ch = [e for e in events if e["change_type"] == "changed"][0]
        self.assertEqual((ch["property"], ch["old"], ch["new"]), ("title", "A1", "A2"))
        rm = [e for e in events if e["change_type"] == "removed"][0]
        self.assertEqual((rm["property"], rm["old"], rm["new"]), ("status", 200, 404))
        rd = [e for e in events if e["change_type"] == "redirected"][0]
        self.assertEqual((rd["property"], rd["new"]), ("status", 301))
        ot = [e for e in events if e["change_type"] == "other"][0]
        self.assertEqual((ot["property"], ot["new"]), ("status", 503))
        ad = [e for e in events if e["change_type"] == "added"
              and e["url"] == "https://x.com/a"][0]
        self.assertEqual((ad["property"], ad["old"], ad["new"]), (None, None, "A1"))

    def test_unreachable_and_string_status_classified(self):
        """网络层不可达(fields.error,无 status)→ other;"404" 字符串 status → removed。"""
        self.assertEqual(cg.snapshot_class({"status": None, "fields": {"error": "timeout"}}),
                         "other")
        self.assertEqual(cg.snapshot_class({"status": 503, "fields": {}}), "other")
        self.assertEqual(cg.snapshot_class({"status": "404", "fields": {}}), "removed")
        self.assertEqual(cg.snapshot_class({"status": 301, "fields": {}}), "redirected")
        self.assertEqual(cg.snapshot_class({"status": 200, "fields": {}}), "ok")
        self.assertEqual(cg.snapshot_class({"status": None, "fields": {"title": "T"}}), "ok")

    def test_hreflang_order_insensitive(self):
        """hreflang 列表比较忽略顺序(重排不产事件);增删语言才记 changed。"""
        records = [
            snap("https://x.com/h", "2026-10-01T00:00:00", status=200,
                 hreflang=["en", "fr"]),
            snap("https://x.com/h", "2026-10-02T00:00:00", status=200,
                 hreflang=["fr", "en"]),
            snap("https://x.com/h", "2026-10-03T00:00:00", status=200,
                 hreflang=["fr", "en", "de"]),
        ]
        href = [e for e in cli_payload(records)["events"] if e["property"] == "hreflang"]
        self.assertEqual(len(href), 1)                       # 仅 03 日一条
        self.assertEqual(sorted(href[0]["old"]), ["en", "fr"])
        self.assertEqual(sorted(href[0]["new"]), ["de", "en", "fr"])


class WhitelistTests(unittest.TestCase):
    """白名单外字段不产事件;入链/出链/PageSpeed(官方"仅当前值无历史")跳过并提示。"""

    def test_not_tracked_skipped_with_notice(self):
        records = [
            snap("https://x.com/w", "2026-10-01T00:00:00", status=200, title="T1",
                 inlinks=5, outlinks=10, pagespeed=90, og_title="O1"),
            snap("https://x.com/w", "2026-10-02T00:00:00", status=200, title="T2",
                 inlinks=8, outlinks=12, pagespeed=70, og_title="O2"),
        ]
        payload = cli_payload(records)
        props = [e["property"] for e in payload["events"]]
        self.assertEqual(props, [None, "title"])             # added + title 变更,别无其他
        self.assertNotIn("og_title", json.dumps(payload["events"]))  # 非白名单静默忽略
        self.assertEqual(set(payload["skipped_not_tracked"]), {"入链", "出链", "PageSpeed"})
        md = cli_text(records)
        self.assertIn("不追踪字段", md)
        self.assertIn("仅当前值无历史", md)                   # 官方口径原话
        self.assertIn("入链", md)
        self.assertIn("PageSpeed", md)


class GranularityTests(unittest.TestCase):
    """粒度【官方】: 近 14 天按日;更早按周,同周同 URL 同字段折叠保留最后一次+计数。"""

    WEEKLY = [
        snap("/u", "2026-09-14T00:00:00", status=200, canonical="c0", title="T0"),
        snap("/u", "2026-09-15T00:00:00", status=200, canonical="c1", title="T0"),
        snap("/u", "2026-09-17T00:00:00", status=200, canonical="c2", title="T0"),
        snap("/u", "2026-10-09T00:00:00", status=200, canonical="c3", title="T1"),
    ]   # 09-14/15/17 同一 ISO 周(周一=09-14),距 --to 2026-10-10 ≥14 天 → 周折叠
        # (每条快照携带完整字段——稀疏字段会把未提及键当成置空,产生假变更)

    def test_weekly_folding_keeps_last_with_count(self):
        """"09-15 与 09-17 两条 canonical 变更同周 → 折叠为 1 条(×2),ts=最后一条;
        10-09 的 canonical/title 变更在 14 天内 → 日粒度不折叠。"""
        payload = cli_payload(self.WEEKLY)
        events = payload["events"]
        self.assertEqual(len(events), 4)                     # added + 折叠canonical + 日canonical + 日title
        wl = cg.week_label(date(2026, 9, 17))
        folded = [e for e in events if e["property"] == "canonical" and e["granularity"] == "week"]
        self.assertEqual(len(folded), 1)
        self.assertEqual((folded[0]["count"], folded[0]["bucket"], folded[0]["ts"],
                          folded[0]["new"]), (2, wl, "2026-09-17T00:00:00", "c2"))
        daily = [e for e in events if e["granularity"] == "day"]
        self.assertEqual({e["bucket"] for e in daily}, {"2026-10-09"})
        self.assertTrue(all(e["count"] == 1 for e in daily))
        md = cli_text(self.WEEKLY)
        self.assertIn("canonical (×2)", md)
        self.assertIn(wl, md)

    def test_daily_no_fold_within_14_days(self):
        records = [
            snap("/d", "2026-10-06T00:00:00", status=200, title="D0"),
            snap("/d", "2026-10-07T00:00:00", status=200, title="D1"),
            snap("/d", "2026-10-08T00:00:00", status=200, title="D2"),
        ]
        events = cli_payload(records)["events"]
        titles = [e for e in events if e["property"] == "title"]
        self.assertEqual([e["bucket"] for e in titles], ["2026-10-07", "2026-10-08"])
        self.assertTrue(all(e["granularity"] == "day" and e["count"] == 1 for e in titles))
        md = cli_text(records)
        self.assertNotIn("×2", md)


class FilterTests(unittest.TestCase):
    """--from/--to 窗(含端点)+ --url 子串 + --type 枚举过滤。"""

    def test_window_url_type_filters(self):
        multi = EventGenerationTests.MULTI
        win = cli_payload(multi, "--from", "2026-10-03", "--to", "2026-10-05")["events"]
        self.assertEqual({(e["change_type"], e["url"]) for e in win},
                         {("changed", "https://x.com/a"), ("removed", "https://x.com/a"),
                          ("redirected", "https://x.com/b")})
        byurl = cli_payload(multi, "--url", "x.com/b")["events"]
        self.assertTrue(byurl)
        self.assertEqual({e["url"] for e in byurl}, {"https://x.com/b"})
        rm = cli_payload(multi, "--type", "removed")["events"]
        self.assertEqual({e["change_type"] for e in rm}, {"removed"})

    def test_bad_type_rejected(self):
        path = snaps_file([snap("/x", "2026-10-01T00:00:00", status=200)])
        r = run_script("changelog.py", ["--snaps", path, "--type", "deleted"])
        os.unlink(path)
        self.assertEqual(r.returncode, 2)
        self.assertIn("changed,added,removed,redirected,other", r.stderr)


class SummaryTests(unittest.TestCase):
    """--summary: 每字段变更频次表 + 最多字段(root-cause 线索)+ 类型分布。"""

    RECORDS = [
        snap("/s", "2026-10-01T00:00:00", status=200, title="S1", canonical="ca0",
             indexable=True),
        snap("/s", "2026-10-02T00:00:00", status=200, title="S2", canonical="ca0",
             indexable=True),
        snap("/s", "2026-10-03T00:00:00", status=200, title="S3", canonical="ca0",
             indexable=True),
        snap("/s", "2026-10-04T00:00:00", status=200, title="S4", canonical="ca1",
             indexable=True),
        snap("/s", "2026-10-05T00:00:00", status=200, title="S5", canonical="ca1",
             indexable=False),
    ]   # 每条快照携带完整字段(只变更目标键),title×4 / canonical×1 / indexable×1

    def test_frequency_table(self):
        payload = cli_payload(self.RECORDS, "--summary")
        s = payload["summary"]
        self.assertEqual(s["by_property"]["title"], 4)
        self.assertEqual(s["by_property"]["canonical"], 1)
        self.assertEqual(s["by_property"]["indexable"], 1)
        self.assertEqual((s["top_property"], s["top_count"]), ("title", 4))
        self.assertEqual(s["by_change_type"]["changed"], 6)
        self.assertEqual(s["by_change_type"]["added"], 1)
        md = cli_text(self.RECORDS, "--summary")
        self.assertIn("| title | 4 |", md)
        self.assertIn("最多变更字段: title(4 次)", md)
        self.assertIn("类型分布: changed 6 · added 1", md)


class DbInputTests(unittest.TestCase):
    """--db 输入对齐 monitor.py 的 snapshots 表(check='pages', value=指标 JSON):
    字段名归一(meta_desc→meta_description)/ 非 白名单量(latency/hash)不产事件 /
    run_id 写入 snapshot 溯源 / 恢复(404→200)记 changed(status)。"""

    @staticmethod
    def _db():
        fd, path = tempfile.mkstemp(suffix=".db", prefix="chlogdb_")
        os.close(fd)
        os.unlink(path)                                      # connect 需全新建
        conn = sqlite3.connect(path)
        conn.executescript("""
        CREATE TABLE runs(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT,
          status TEXT, checks_run TEXT, budget_used_sec REAL, summary TEXT);
        CREATE TABLE snapshots(run_id INTEGER, ts TEXT, "check" TEXT, key TEXT,
          value TEXT, hash TEXT);
        """)
        rows = [
            (1, "2026-10-01T02:00:00", "/pricing",
             {"status": 200, "title": "P1", "meta_desc": "M1", "indexable": True,
              "latency_ms": 100.0, "title_meta_hash": "h1"}),
            (2, "2026-10-05T02:00:00", "/pricing",
             {"status": 200, "title": "P2", "meta_desc": "M1", "indexable": True,
              "latency_ms": 90.0, "title_meta_hash": "h2"}),
            (3, "2026-10-07T02:00:00", "/pricing",
             {"status": 404}),
            (4, "2026-10-08T02:00:00", "/pricing",
             {"status": 200, "title": "P2", "meta_desc": "M1", "indexable": True}),
        ]
        for rid, ts, key, metrics in rows:
            conn.execute(
                'INSERT INTO snapshots(run_id, ts, "check", key, value, hash) '
                "VALUES(?,?,?,?,?,?)",
                (rid, ts, "pages", key, json.dumps(metrics), "h%d" % rid))
        conn.commit()
        conn.close()
        return path

    def test_db_events_and_field_mapping(self):
        path = self._db()
        try:
            r = run_script("changelog.py", ["--db", path, "--json", "--to", "2026-10-10"])
            self.assertEqual(r.returncode, 0, r.stderr)
            events = json.loads(r.stdout)["events"]
        finally:
            os.unlink(path)
        kinds = [(e["change_type"], e["property"]) for e in events]
        self.assertIn(("added", None), kinds)
        self.assertIn(("changed", "title"), kinds)           # P1 → P2
        self.assertNotIn(("changed", "meta_description"), kinds)   # M1 未变
        self.assertNotIn(("changed", "latency_ms"), kinds)   # 非白名单
        self.assertNotIn(("changed", "title_meta_hash"), kinds)
        self.assertIn(("removed", "status"), kinds)          # 200 → 404
        rec = [e for e in events if e["change_type"] == "removed"][0]
        self.assertEqual((rec["old"], rec["new"]), (200, 404))
        self.assertEqual(rec["snapshot"], 3)                 # run_id 溯源
        rec_ch = [e for e in events if (e["change_type"], e["property"]) == ("changed", "title")][0]
        self.assertEqual((rec_ch["old"], rec_ch["new"], rec_ch["snapshot"]),
                         ("P1", "P2", 2))


class RootCauseScenarioTests(unittest.TestCase):
    """用途链: "流量下跌那天页面改了什么"——noindex 翻转按日定位;
    首见=added 与窗口过滤组合。"""

    def test_noindex_flip_pinned_to_day(self):
        """"10-06 indexable true→false 且 noindex_source (无)→meta:
        --from 2026-10-06 恰好圈出这两条(10-01 首见被窗排除)。"""
        records = [
            snap("https://x.com/p", "2026-10-01T00:00:00", status=200,
                 title="T", indexable=True),
            snap("https://x.com/p", "2026-10-06T00:00:00", status=200,
                 title="T", indexable=False, noindex_source="meta"),
        ]
        payload = cli_payload(records, "--from", "2026-10-06")
        self.assertEqual(payload["n_events"], 2)
        self.assertEqual({e["property"] for e in payload["events"]},
                         {"indexable", "noindex_source"})
        md = cli_text(records, "--from", "2026-10-06")
        self.assertIn("indexable", md)
        self.assertIn("true → false", md)
        self.assertIn("(无) → meta", md)
        # 不加窗: added(10-01)+两条 changed
        self.assertEqual(cli_payload(records)["n_events"], 3)

    def test_first_seen_added_filtered_by_window(self):
        """"每 URL 时间序列首见即 added(old@10-01 与 new@10-05 各一条);
        --from 10-06 后窗内无任何事件。"""
        records = [
            snap("https://x.com/old", "2026-10-01T00:00:00", status=200),
            snap("https://x.com/new", "2026-10-05T00:00:00", status=200, title="N"),
        ]
        payload = cli_payload(records)
        added = [e for e in payload["events"] if e["change_type"] == "added"]
        self.assertEqual({(e["url"], e["ts"]) for e in added},
                         {("https://x.com/old", "2026-10-01T00:00:00"),
                          ("https://x.com/new", "2026-10-05T00:00:00")})
        self.assertEqual(cli_payload(records, "--from", "2026-10-06")["n_events"], 0)


class CliContractTests(unittest.TestCase):
    """--help 正常 / 缺输入源 exit 2 / 空库零事件 exit 0。"""

    def test_help(self):
        r = run_script("changelog.py", ["--help"])
        self.assertEqual(r.returncode, 0)
        for token in ("--db", "--snaps", "--from", "--to", "--url", "--type",
                      "--summary", "--json"):
            self.assertIn(token, r.stdout)

    def test_missing_source_rejected(self):
        r = run_script("changelog.py", [])
        self.assertEqual(r.returncode, 2)

    def test_empty_snaps_zero_events(self):
        path = snaps_file([])
        r = run_script("changelog.py", ["--snaps", path, "--to", "2026-10-10"])
        os.unlink(path)
        self.assertEqual(r.returncode, 0)
        self.assertIn("窗内无匹配事件", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
