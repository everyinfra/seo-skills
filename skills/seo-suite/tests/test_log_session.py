#!/usr/bin/env python3
"""log_session.py 测试 + monitor.py owner_team 透传测试(standalone,合成日志/合成 config+db,
零网络;tests/run_tests.py 自动发现本文件)。

Part A log_session(R4 监控对标③,≥12 例):会话切分边界(间隔恰=窗口并入 / >窗口切开)/
窗口单位解析(s/m/h/d/裸数字/非法)/按 IP 切分 / 乱序日志先排序再切分 /
三陷阱特征阈值(参数循环>10、深度>8、请求>500,恰等不触发)/UA 过滤(默认 Googlebot、
词边界、--ua "" 不过滤)/combined 与 CLF 两种格式 / 入口-离开-去重页数 / 命中率口径(仅 200)/
汇总(Top 入口页+平均深度)/markdown 与 JSON 双输出 / --self-test。

Part B monitor owner_team(R4 监控对标⑤,3 例):config 可选映射
owner_teams:{code_prefix:"team"} → 告警 payload 逐条透传 owner_team——最长前缀优先 /
未配置不写键 / 无命中前缀且非字符串值忽略。
python3 tests/test_log_session.py
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import log_session as LS  # noqa: E402  (需先入 SCRIPTS 路径)

GBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
BING = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"


def run_script(name, args=(), stdin=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def combined(ip, ts, path, status=200, ua=GBOT, referer="-"):
    """一行 combined 日志(CLF 超集)。"""
    return '%s - - [%s] "GET %s HTTP/1.1" %d 1024 "%s" "%s"' % (ip, ts, path, status, referer, ua)


def clf(ip, ts, path, status=200):
    """一行 CLF 日志(无 referer/UA 字段)。"""
    return '%s - - [%s] "GET %s HTTP/1.1" %d 1024' % (ip, ts, path, status)


def ts(h, m, s=0):
    return "12/Oct/2026:%02d:%02d:%02d +0000" % (h, m, s)


def run_json(lines, *extra):
    fd, path = tempfile.mkstemp(suffix=".log", prefix="gbot_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    try:
        r = run_script("log_session.py", ["--log", path, "--json", *extra])
        if r.returncode != 0:
            raise AssertionError("rc=%d stderr=%s" % (r.returncode, r.stderr))
        return json.loads(r.stdout)
    finally:
        os.unlink(path)


def run_md(lines, *extra):
    fd, path = tempfile.mkstemp(suffix=".log", prefix="gbot_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    try:
        return run_script("log_session.py", ["--log", path, *extra])
    finally:
        os.unlink(path)


# ---------- Part A:log_session ----------

class CliContractTests(unittest.TestCase):
    """--help / --self-test / 坏窗口 / 缺 --log。"""

    def test_help_exits_zero(self):
        r = run_script("log_session.py", ["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("--ua", r.stdout)
        self.assertIn("--window", r.stdout)

    def test_self_test_flag(self):
        r = run_script("log_session.py", ["--self-test"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("self-test OK", r.stdout)

    def test_bad_window_and_missing_log_exit_4(self):
        r = run_script("log_session.py", ["--log", "-", "--window", "abc"])
        self.assertEqual(r.returncode, 4)
        r2 = run_script("log_session.py", [])
        self.assertEqual(r2.returncode, 4)

    def test_window_units(self):
        for spec, sec in [("30m", 1800), ("90s", 90), ("2h", 7200), ("1d", 86400), ("5", 300)]:
            self.assertEqual(LS.parse_window(spec), sec)
        self.assertIsNone(LS.parse_window("3x"))


class SessionSplitTests(unittest.TestCase):
    """切分口径:间隔恰=窗口并入;>窗口切开;换 IP 切开;乱序先排序。"""

    def test_gap_equal_window_stays_one_session(self):
        d = run_json([combined("66.249.66.1", ts(10, 0), "/a"),
                      combined("66.249.66.1", ts(10, 30), "/b")], "--window", "30m")
        self.assertEqual(d["summary"]["session_count"], 1)          # 恰 30m ≤ 窗口
        self.assertEqual(d["sessions"][0]["requests"], 2)

    def test_gap_over_window_splits(self):
        d = run_json([combined("66.249.66.1", ts(10, 0), "/a"),
                      combined("66.249.66.1", ts(10, 30, 1), "/b")], "--window", "30m")
        self.assertEqual(d["summary"]["session_count"], 2)          # 30m+1s > 窗口
        self.assertEqual([s["entry"] for s in d["sessions"]], ["/a", "/b"])

    def test_sessions_split_by_ip(self):
        d = run_json([combined("66.249.66.1", ts(10, 0), "/a"),
                      combined("66.249.66.2", ts(10, 0), "/b"),
                      combined("66.249.66.1", ts(10, 1), "/c")])
        self.assertEqual(d["summary"]["session_count"], 2)
        self.assertEqual({s["ip"] for s in d["sessions"]}, {"66.249.66.1", "66.249.66.2"})
        by_ip = {s["ip"]: s for s in d["sessions"]}
        self.assertEqual(by_ip["66.249.66.1"]["requests"], 2)

    def test_unsorted_log_sorted_before_split(self):
        # 乱序写入:先 10:10 再 10:00——入口页必须取时间最早者(先排序再切分)
        d = run_json([combined("66.249.66.1", ts(10, 10), "/later"),
                      combined("66.249.66.1", ts(10, 0), "/first"),
                      combined("66.249.66.1", ts(10, 20), "/last")])
        self.assertEqual(d["summary"]["session_count"], 1)
        s = d["sessions"][0]
        self.assertEqual((s["entry"], s["exit"]), ("/first", "/last"))


class TrapTests(unittest.TestCase):
    """三陷阱特征(严格大于:恰 10 次/恰深度 8/恰 500 请求都不触发)。"""

    def test_param_loop_threshold(self):
        loop = [combined("66.249.66.1", ts(10, 0), "/search?page=%d" % i) for i in range(11)]
        d = run_json(loop)
        self.assertIn("param_loop", d["sessions"][0]["traps"])
        self.assertEqual(d["sessions"][0]["trap_detail"]["param_loop"]["param_requests"], 11)
        ctrl = run_json([combined("66.249.66.1", ts(10, 0), "/search?page=%d" % i)
                         for i in range(10)])
        self.assertEqual(ctrl["sessions"][0]["traps"], [])          # 恰 10 次:不触发

    def test_deep_crawl_threshold(self):
        deep = "/a/b/c/d/e/f/g/h/i"                                  # 9 段
        d = run_json([combined("66.249.66.1", ts(10, 0), deep)])
        self.assertEqual(d["sessions"][0]["max_depth"], 9)
        self.assertIn("deep_crawl", d["sessions"][0]["traps"])
        ok = run_json([combined("66.249.66.1", ts(10, 0), "/a/b/c/d/e/f/g/h")])   # 8 段
        self.assertEqual(ok["sessions"][0]["traps"], [])
        self.assertEqual(LS.path_depth("/"), 1)                      # 根页记 1

    def test_volume_threshold(self):
        rows = [combined("66.249.66.1", ts(10, 0), "/p") for _ in range(501)]
        d = run_json(rows)
        self.assertIn("volume", d["sessions"][0]["traps"])
        self.assertEqual(d["sessions"][0]["requests"], 501)
        ctrl = run_json([combined("66.249.66.1", ts(10, 0), "/p") for _ in range(500)])
        self.assertEqual(ctrl["sessions"][0]["traps"], [])           # 恰 500:不触发


class UaAndFormatTests(unittest.TestCase):
    """UA 前缀过滤(默认 Googlebot/词边界/--ua "" 全过)+ combined/CLF 两格式。"""

    def test_ua_filter_default_googlebot_only(self):
        d = run_json([combined("66.249.66.1", ts(10, 0), "/a"),
                      combined("157.55.39.1", ts(10, 0), "/b", ua=BING),
                      combined("1.2.3.4", ts(10, 0), "/c", ua="Mozilla/5.0")])
        self.assertEqual(d["matched"], 1)
        self.assertEqual(d["summary"]["session_count"], 1)
        self.assertEqual(d["sessions"][0]["ip"], "66.249.66.1")

    def test_ua_filter_custom_and_word_boundary(self):
        d = run_json([combined("157.55.39.1", ts(10, 0), "/b", ua=BING),
                      combined("1.2.3.4", ts(10, 0), "/x", ua="xGooglebot/1.0")],
                     "--ua", "bingbot")
        self.assertEqual(d["matched"], 1)                            # 换前缀换目标
        self.assertEqual(d["sessions"][0]["ip"], "157.55.39.1")
        self.assertFalse(LS.ua_matches("xGooglebot/1.0", "Googlebot"))   # 词边界:不命中
        self.assertTrue(LS.ua_matches("Googlebot-News", "Googlebot"))    # 变体命中

    def test_combined_format_with_referer_ua(self):
        d = run_json([combined("66.249.66.1", ts(10, 0), "/a", status=200,
                               referer="https://example.com/")])
        self.assertEqual(d["parsed"], 1)
        self.assertEqual(d["unparsed"], 0)
        self.assertEqual(d["matched"], 1)

    def test_clf_format_needs_empty_ua_filter(self):
        rows = [clf("10.0.0.1", ts(10, 0), "/z"), clf("10.0.0.2", ts(10, 0), "/y")]
        d = run_json(rows, "--ua", "")
        self.assertEqual(d["summary"]["session_count"], 2)           # CLF 无 UA:空过滤才可见
        self.assertEqual(d["sessions"][0]["entry"], "/z")
        default = run_md(rows)                                        # 默认 Googlebot → 如实报 0
        self.assertIn("0 行命中", default.stdout)
        self.assertIn("CLF", default.stdout)


class MetricsAndOutputTests(unittest.TestCase):
    """入口/离开/去重页数/命中率/汇总/双输出形态。"""

    def test_entry_exit_and_unique_pages(self):
        d = run_json([combined("66.249.66.1", ts(10, 0), "/in"),
                      combined("66.249.66.1", ts(10, 1), "/p?x=1"),
                      combined("66.249.66.1", ts(10, 2), "/p?x=2"),   # 同路径异参数:页数只算 1
                      combined("66.249.66.1", ts(10, 3), "/out")])
        s = d["sessions"][0]
        self.assertEqual((s["entry"], s["exit"]), ("/in", "/out"))
        self.assertEqual(s["pages"], 3)
        self.assertEqual(s["requests"], 4)

    def test_hit_rate_counts_only_200(self):
        d = run_json([combined("66.249.66.1", ts(10, 0), "/a", status=200),
                      combined("66.249.66.1", ts(10, 1), "/b", status=301),
                      combined("66.249.66.1", ts(10, 2), "/c", status=404),
                      combined("66.249.66.1", ts(10, 3), "/d", status=200)])
        self.assertEqual(d["sessions"][0]["hit_rate"], 0.5)          # 301 不计命中

    def test_summary_top_entries_and_avg_depth(self):
        # 会话1(深度 2,入口 /home)· 会话2(深度 1,入口 /home)· 会话3(深度 1,入口 /docs)
        rows = [combined("66.249.66.1", ts(10, 0), "/home"),
                combined("66.249.66.1", ts(10, 1), "/home/sub"),
                combined("66.249.66.2", ts(10, 0), "/home"),
                combined("66.249.66.3", ts(10, 0), "/docs")]
        d = run_json(rows)
        sm = d["summary"]
        self.assertEqual(sm["session_count"], 3)
        self.assertEqual(sm["avg_max_depth"], 1.3)                   # (2+1+1)/3 保留 1 位
        self.assertEqual(sm["top_entries"][0], ["/home", 2])
        self.assertEqual(dict(sm["top_entries"])["/docs"], 1)
        self.assertEqual(sm["trap_sessions"], [])

    def test_markdown_render_sections(self):
        rows = [combined("66.249.66.1", ts(10, 0), "/a"),
                combined("66.249.66.1", ts(10, 1), "/b")]
        r = run_md(rows)
        self.assertEqual(r.returncode, 0)
        for needle in ["Googlebot 会话追踪", "会话明细", "陷阱会话清单", "Top 入口页", "/a"]:
            self.assertIn(needle, r.stdout)


# ---------- Part B:monitor owner_team 透传(R4 监控对标⑤) ----------

import monitor as M  # noqa: E402  (需先入 SCRIPTS 路径)

HEALTHY = {"state": "ok", "status": 200, "indexable": True}
BROKEN = {"state": "http_error", "status": 500, "indexable": True}


def _fresh_monitor_dir():
    tmp = tempfile.mkdtemp(prefix="pm_owner_")
    mdir = os.path.join(tmp, ".seo-monitor")
    rc = M.cmd_init(M.build_parser().parse_args(
        ["init", "--site", "https://example.com", "--market", "us",
         "--key-pages", "/pricing", "--dir", mdir]))
    assert rc == 0
    return mdir


def _insert_run(mdir, pages):
    conn = M.open_db(mdir)
    ts = datetime.now().isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO runs(ts,kind,status,checks_run,budget_used_sec,summary) "
        "VALUES(?,?,?,'daily',0,'')", (ts, "daily", "ok"))
    rid = cur.lastrowid
    for path, value in pages.items():
        conn.execute(
            'INSERT INTO snapshots(run_id,ts,"check",key,value,hash) VALUES(?,?,?,?,?,?)',
            (rid, ts, "pages", path, json.dumps(value), "h%d%s" % (rid, path)))
    conn.commit()
    conn.close()
    return rid


def _run_monitor_cmd(args_list):
    out, err = io.StringIO(), io.StringIO()
    args = M.build_parser().parse_args(args_list)
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = args.func(args)
    return rc, out.getvalue(), err.getvalue()


class MonitorOwnerTeamTests(unittest.TestCase):
    """config owner_teams:{code_prefix:"team"} → 告警 payload 透传 owner_team。"""

    def _diff_payload(self, owner_teams=None):
        mdir = _fresh_monitor_dir()
        if owner_teams is not None:
            cfg = M.load_config(mdir)
            cfg["owner_teams"] = owner_teams
            M.save_config(mdir, cfg)
        _insert_run(mdir, {"/pricing": HEALTHY})
        _insert_run(mdir, {"/pricing": BROKEN})          # → critical key_page_down
        rc, stdout, _ = _run_monitor_cmd(["diff", "--dir", mdir, "--format", "json"])
        return rc, json.loads(stdout)

    def test_owner_team_longest_prefix_wins(self):
        rc, payload = self._diff_payload({"key_page": "infra",
                                          "key_page_down": "oncall",
                                          "homepage": "web"})
        self.assertEqual(rc, 1)                          # critical 退出码不变
        hit = [a for a in payload["alerts"] if a["code"] == "key_page_down"]
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0].get("owner_team"), "oncall")   # 最长前缀压过 key_page
        self.assertEqual(payload["counts"]["critical"], 1)

    def test_owner_team_absent_without_mapping(self):
        rc, payload = self._diff_payload(None)           # 未配置:不写键,零侵扰旧 payload
        self.assertEqual(rc, 1)
        hit = [a for a in payload["alerts"] if a["code"] == "key_page_down"]
        self.assertEqual(len(hit), 1)
        self.assertNotIn("owner_team", hit[0])

    def test_owner_team_no_match_and_non_string_values_ignored(self):
        rc, payload = self._diff_payload({"visibility": "seo", "gsc": 123, "": "x"})
        self.assertEqual(rc, 1)                          # 坏值/空前缀/无命中:不崩不写键
        hit = [a for a in payload["alerts"] if a["code"] == "key_page_down"]
        self.assertNotIn("owner_team", hit[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
