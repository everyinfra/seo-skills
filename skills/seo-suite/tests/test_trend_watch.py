#!/usr/bin/env python3
"""trend_watch.py 测试(热点监控与选题闸门;合成 RSS/JSON fixture,零网络)。
所有外部拉取打桩:patch trend_watch.fetch_url(脚本唯一网络出口),fixture 按
URL 模式/查询词路由;时钟不全局打桩(velocity 用预置样本时间戳构造)。
覆盖:watch 登记/去重/跨源合并/Q1 三分支/单源 WATCH/整源失败跳过与退出码/
velocity 二次采样/gate 四问各分支/判定矩阵(GO·PIVOT·WATCH·DROP)/重复否决/
deadline/backlog 过滤与到期标记/SSRF 防护/--help。
standalone: python3 tests/test_trend_watch.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载(勿 import 期副作用)。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import trend_watch as tw  # noqa: E402  (需先入 SCRIPTS 路径;import 期无副作用)


def run_script(*args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "trend_watch.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_file(content, suffix=".md"):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


# ---------------------------------------------------------------- 合成 fixture
TITLE_GO = "OpenAI launches GPT-6 benchmark suite"      # 3 源同事件 → open
TITLE_MED = "seotrends rising fast in 2026"             # 部分命中 +10 → watch 相关性不足
TITLE_SOLO = "llm citation study drops"                 # 单源 HIGH → watch 单源
TITLE_JUNK = "Unrelated gadget sale"                    # 0 分 → drop
TITLE_DUP = "OpenAI launches GPT-6 benchmark suite details"  # 与 TITLE_GO 重叠 85.7%
VERTICAL = "openai llm seotrend"                        # openai/llm 整词;seotrend 部分

GN_FEED = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>%s - TechCrunch</title><link>https://techcrunch.com/a</link>
<source url="https://techcrunch.com">TechCrunch</source></item>
</channel></rss>""" % TITLE_GO

GN_WIRE_LOW = """<?xml version="1.0"?><rss version="2.0"><channel><title>s</title>
<item><title>w1 - Example</title><link>https://example.com/1</link>
<source url="https://example.com">Example</source></item>
<item><title>w2 - Another</title><link>https://another.org/2</link>
<source url="https://another.org">Another</source></item>
</channel></rss>"""

GN_WIRE_HEAVY = """<?xml version="1.0"?><rss version="2.0"><channel><title>s</title>
<item><title>w1 - Reuters</title><link>https://www.reuters.com/1</link>
<source url="https://www.reuters.com">Reuters</source></item>
<item><title>w2 - AP</title><link>https://apnews.com/2</link>
<source url="https://apnews.com">AP</source></item>
<item><title>w3 - AFP</title><link>https://www.afp.com/3</link>
<source url="https://www.afp.com">AFP</source></item>
<item><title>w4 - Example</title><link>https://example.com/4</link>
<source url="https://example.com">Example</source></item>
</channel></rss>"""

HN_TOP = "[1, 2, 3, 4]"
HN_ITEMS = {
    "1": {"id": 1, "title": TITLE_GO, "url": "https://openai.com/gpt6"},
    "2": {"id": 2, "title": TITLE_MED, "url": "https://example.com/med"},
    "3": {"id": 3, "title": TITLE_JUNK, "url": "https://giz.example/junk"},
    "4": {"id": 4, "title": TITLE_DUP, "url": "https://example.com/dup"},
}
REDDIT = json.dumps({"data": {"children": [
    {"data": {"title": TITLE_GO, "permalink": "/r/technology/go", "score": 9}},
    {"data": {"title": TITLE_MED, "permalink": "/r/seo/med", "score": 4}},
    {"data": {"title": TITLE_SOLO, "permalink": "/r/seo/solo", "score": 6}},
    {"data": {"title": TITLE_DUP, "permalink": "/r/startups/dup", "score": 7}},
]}})
WEIBO = json.dumps({"ok": 1, "data": {"realtime": [
    {"word": "大模型 发布 会 直播", "rank": 0}, {"word": "台风 路径 实况", "rank": 1}]}})
# 百度实测形状(2026-10):cards[].content[].content[] 嵌套两层(tab 包装→词条)
BAIDU_LIVE_SHAPE = json.dumps({"success": 1, "data": {"cards": [
    {"component": "tabTextList", "title": "热搜榜", "content": [
        {"content": [{"word": "大模型 发布 会"}, {"word": "新能源 产业"}], "moreType": "x"}]}]}})

ANGLE_6 = "# 角度\n" + "\n".join("| %d | 净新观点%d | data | 内部基准 | 1h |" % (i, i)
                                for i in range(1, 7)) + "\n"
ANGLE_3 = "# 角度\n" + "\n".join("| %d | 观点%d | data | x | 1h |" % (i, i)
                                for i in range(1, 4)) + "\n"


def make_stub(wire_body=GN_WIRE_LOW, wire_fail_titles=(), base_fail=False,
              fail_sources=("top.baidu.com",)):
    """fetch_url 桩:按 URL 路由合成响应;/rss/search 的 q= 区分 vertical 检索与 wire 查询。
    fail_sources:命中子串即整源失败(默认百度——无契约端点被拦是常态,失败明说)。"""
    wire_titles = {TITLE_GO, TITLE_MED, TITLE_SOLO, TITLE_JUNK, TITLE_DUP}

    def stub(url):
        if base_fail:
            raise tw.FetchError("all down (stub)")
        for pat in fail_sources:
            if pat in url:
                raise tw.FetchError("source blocked (stub): %s" % pat)
        if "/rss/search" in url:
            import urllib.parse
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).get("q", [""])[0]
            if q in wire_fail_titles:
                raise tw.FetchError("wire query blocked (stub)")
            return wire_body if q in wire_titles else GN_FEED
        if "news.google.com" in url:
            return GN_FEED
        if "topstories" in url:
            return HN_TOP
        if "/item/" in url:
            iid = url.rsplit("/item/", 1)[1].split(".")[0]
            return json.dumps(HN_ITEMS[iid])
        if "reddit.com" in url:
            return REDDIT
        if "weibo.com" in url:
            return WEIBO
        raise AssertionError("stub: 未预期的 URL %s" % url)
    return stub


class TrendWatchCase(unittest.TestCase):
    """公共助手:每个用例独立 state/briefs 临时目录;tw.main(argv) 直调收退出码。"""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.state = os.path.join(self.dir.name, "state.json")
        self.briefs = os.path.join(self.dir.name, "briefs")
        self.addCleanup(self.dir.cleanup)

    def watch(self, *extra, stub=None):
        with patch.object(tw, "fetch_url", stub or make_stub()):
            import contextlib, io
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = tw.main(["watch", "--state", self.state, "--brief-dir", self.briefs,
                              "--market", "en", "--vertical", VERTICAL, "--json", *extra])
            out = buf.getvalue()
            return rc, (json.loads(out) if out.strip().startswith("{") else None)

    def gate(self, sid, *extra, stub=None):
        with patch.object(tw, "fetch_url", stub or make_stub()):
            import contextlib, io
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = tw.main(["gate", "--signal-id", sid, "--state", self.state,
                              "--brief-dir", self.briefs, "--json", *extra])
            out = buf.getvalue()
            return rc, (json.loads(out) if out.strip().startswith("{") else None)

    def sid_of(self, payload, title):
        for s in (payload or {}).get("new_signals") or []:
            if s["title"] == title:
                return s["signal_id"]
        for s in self.load_state()["signals"].values():            # 已登记(非本轮新建)也允许
            if s["title"] == title:
                return s["signal_id"]
        raise AssertionError("信号未登记: %s(new=%s)" % (title, (payload or {}).get("new_signals")))

    def load_state(self):
        with open(self.state, encoding="utf-8") as f:
            return json.load(f)

    def save_state(self, st):
        with open(self.state, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False)


# ---------------------------------------------------------------- 单元口径
class TrendWatchUnitTests(unittest.TestCase):
    """纯函数:打分口径(CJK/整词/部分)/tokenizer/重叠/角度计数/velocity/SSRF。"""

    def test_relevance_scoring(self):
        # CJK 无空格分词:子串命中即整词(HIGH);拉丁 \b 整词 vs 部分命中
        self.assertEqual(tw.relevance("llm seo 实战指南", ["llm"]), (25, "HIGH"))
        self.assertEqual(tw.relevance("人工智能 大会", ["人工智能"]), (25, "HIGH"))
        self.assertEqual(tw.relevance("seotrends rising", ["seotrend"]), (10, "MED"))
        self.assertEqual(tw.relevance("nothing here", ["llm", "seo"]), (0, ""))
        self.assertEqual(tw.relevance("llm and seo together", ["llm", "seo"]), (50, "HIGH"))

    def test_tokenize_cjk_bigrams_and_latin(self):
        toks = tw.tokenize("LLM SEO 人工智能大会")
        self.assertIn("llm", toks)
        self.assertIn("人工", toks)      # bigram
        self.assertIn("智能", toks)
        self.assertNotIn("智能大会"[1:], toks or [])   # 跨段不组词
        self.assertNotIn("the", tw.tokenize("the best of seo"))

    def test_word_overlap_containment(self):
        a = tw.tokenize(TITLE_GO)
        b = tw.tokenize(TITLE_DUP)      # 多 1 词 → 包含度 6/7≈0.857
        self.assertGreater(tw.word_overlap(a, b), 0.7)
        self.assertLess(tw.word_overlap(a, tw.tokenize(TITLE_JUNK)), 0.7)
        self.assertEqual(tw.word_overlap([], ["x"]), 0.0)

    def test_count_angle_points_table_and_list(self):
        self.assertEqual(tw.count_angle_points(ANGLE_6), 6)
        self.assertEqual(tw.count_angle_points(ANGLE_3), 3)
        self.assertEqual(tw.count_angle_points("- a\n- b\n- c\n"), 3)
        self.assertEqual(tw.count_angle_points("1. x\n2. y\n"), 2)
        self.assertEqual(tw.count_angle_points("无观点"), 0)

    def test_velocity_resample_rules(self):
        now = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)
        ts = lambda mins: (now - timedelta(minutes=mins)).isoformat()
        self.assertIsNone(tw.compute_velocity([{"ts": ts(5), "pos": 3}], now, 30))       # 样本不足
        self.assertIsNone(tw.compute_velocity(                                            # 间隔 <30min
            [{"ts": ts(10), "pos": 5}, {"ts": ts(0), "pos": 2}], now, 30))
        self.assertEqual(tw.compute_velocity(                                             # ≥30min:升位
            [{"ts": ts(40), "pos": 5}, {"ts": ts(0), "pos": 2}], now, 30), "rising")
        self.assertEqual(tw.compute_velocity(
            [{"ts": ts(40), "pos": 2}, {"ts": ts(0), "pos": 5}], now, 30), "fading")
        self.assertEqual(tw.compute_velocity(
            [{"ts": ts(40), "pos": 3}, {"ts": ts(0), "pos": 3}], now, 30), "peaked")

    def test_ssrf_guard_and_scheme_check(self):
        with self.assertRaises(tw.FetchError):
            tw.fetch_url("ftp://example.com/x")                    # 仅 http(s)
        with self.assertRaises(tw.FetchError):
            tw.fetch_url("http://127.0.0.1:8000/admin")            # 环回拒连(IP 字面量,DNS 零网络)
        with self.assertRaises(tw.FetchError):
            tw.fetch_url("http://192.168.1.10/router")             # 私网拒连
        self.assertEqual(tw.registrable_domain("https://www.reuters.com/article/1"), "reuters.com")

    def test_signal_id_deterministic(self):
        self.assertEqual(tw.signal_id_of("hn", "Some Title"),
                         tw.signal_id_of("hn", "some  title "))     # 归一后幂等
        self.assertNotEqual(tw.signal_id_of("hn", "T"), tw.signal_id_of("reddit-rising", "T"))

    def test_baidu_live_nested_shape_parses(self):
        """百度实测(2026-10)cards[].content[].content[] 两层嵌套必须能抽出词条。"""
        with patch.object(tw, "fetch_url", lambda url: BAIDU_LIVE_SHAPE):
            items = tw._src_baidu({"market": "zh", "tokens": []})
        self.assertEqual([i["title"] for i in items], ["大模型 发布 会", "新能源 产业"])
        self.assertEqual([i["pos"] for i in items], [1, 2])


# ---------------------------------------------------------------- watch
class WatchTests(TrendWatchCase):
    """watch:登记/跨源合并/去重/Q1 分支/单源/整源失败/退出码/active GO。"""

    def test_registers_merges_and_statuses(self):
        rc, p = self.watch()
        self.assertEqual(rc, 0)
        by_title = {s["title"]: s for s in p["new_signals"]}
        self.assertEqual(len(by_title), 5)                          # 8 条原始 → 5 信号
        go = by_title[TITLE_GO]
        self.assertEqual(go["status"], "open")                      # 双(三)源+HIGH+窗口 → open
        self.assertEqual(set(go["sources"]), {"google-news", "reddit-rising", "hn"})
        self.assertEqual(go["rel_score"], 25)
        self.assertEqual(p["merged"], 4)                            # GO 并 2(gn/hn)+ MED 并 1(hn)+ DUP 并 1(hn)
        self.assertEqual(by_title[TITLE_MED]["status"], "watch")    # Q1=10 相关性不足
        self.assertIn("相关性不足", by_title[TITLE_MED]["reason"])
        self.assertEqual(by_title[TITLE_SOLO]["status"], "watch")   # 单源=传闻只 WATCH
        self.assertIn("单源", by_title[TITLE_SOLO]["reason"])
        self.assertEqual(by_title[TITLE_JUNK]["status"], "drop")    # Q1=0
        self.assertEqual(by_title[TITLE_DUP]["status"], "open")     # 85.7% 重叠但尚未有活跃判定→登记
        self.assertEqual(p["wire_checked"], 1)                      # 每 run 至多 1 条 wire 机检
        self.assertIn("sources_ok", p)

    def test_second_run_dedupes_seen(self):
        self.watch()
        rc, p2 = self.watch()
        self.assertEqual(rc, 0)
        self.assertEqual(p2["new_signals"], [])
        self.assertEqual(p2["created"], 0)
        st = self.load_state()
        self.assertLessEqual(len(st["seen"]["hn"]), tw.SEEN_CAP)

    def test_velocity_from_seeded_sample(self):
        _, p = self.watch()
        sid = self.sid_of(p, TITLE_GO)
        st = self.load_state()
        old = (datetime.now(timezone.utc) - timedelta(minutes=40)).isoformat()
        st["signals"][sid]["samples"] = [{"ts": old, "pos": 5, "src": "hn"}]  # 预置 40min 前第 5 位
        self.save_state(st)
        _, p2 = self.watch()
        self.assertEqual(self.load_state()["signals"][sid]["velocity"], "rising")

    def test_source_failure_skips_and_all_fail_exit2(self):
        # weibo 失败 → 整源跳过,其余照常,退出 0
        rc, p = self.watch("--sources", "hn,weibo", stub=make_stub(fail_sources=("weibo.com",)))
        self.assertEqual(rc, 0)
        self.assertEqual(p["sources_failed"].keys(), {"weibo"})
        self.assertEqual(p["sources_ok"], ["hn"])
        # 全源失败 → 退出 2(明说)
        with patch.object(tw, "fetch_url", make_stub(base_fail=True)):
            import contextlib, io
            buf, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
                rc2 = tw.main(["watch", "--state", self.state, "--brief-dir", self.briefs,
                               "--vertical", VERTICAL, "--json"])
            self.assertEqual(rc2, 2)
            self.assertIn("源失败", err.getvalue())

    def test_zh_market_defaults_include_weibo_baidu(self):
        with patch.object(tw, "fetch_url", make_stub()):
            import contextlib, io
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = tw.main(["watch", "--state", self.state, "--brief-dir", self.briefs,
                              "--market", "zh", "--vertical", "大模型", "--json"])
            p = json.loads(buf.getvalue())
        self.assertEqual(rc, 0)
        self.assertIn("weibo", p["sources_ok"])
        self.assertIn("baidu", p["sources_failed"])                 # 桩未配 baidu → 失败明说
        zh = [s for s in p["new_signals"] if "weibo" in s["sources"]]
        self.assertTrue(zh, "weibo 热搜词应已登记")

    def test_unknown_source_and_bad_market_exit3(self):
        rc, _ = self.watch("--sources", "nosuch")
        self.assertEqual(rc, 3)
        rc, _ = self.watch("--market", "qq")
        self.assertEqual(rc, 3)
        rc, _ = self.watch("--topics", "/nonexistent/tokens.txt")
        self.assertEqual(rc, 3)

    def test_watch_exit1_with_active_go(self):
        _, p = self.watch()
        sid = self.sid_of(p, TITLE_GO)
        angle = tmp_file(ANGLE_6)
        grc, _ = self.gate(sid, "--angle", angle, "--exclusive", "data")
        self.assertEqual(grc, 0)
        rc, p2 = self.watch()                                       # 库里存在活跃 GO → exit 1
        self.assertEqual(rc, 1)
        self.assertIn(sid, p2["active_go"])

    def test_topics_file_and_panel(self):
        topics = tmp_file("openai\nllm, seotrend\n", suffix=".txt")
        panel = tmp_file(json.dumps({"rows": [{"query": TITLE_GO, "cited": True}]}), suffix=".json")
        rc, p = self.watch("--topics", topics, "--panel", panel)
        self.assertEqual(rc, 0)
        st = self.load_state()
        sid = self.sid_of(p, TITLE_GO)
        self.assertIn("panel 命中", st["signals"][sid]["existing"])   # 已被引 → 优先刷新既有页


# ---------------------------------------------------------------- gate
class GateTests(TrendWatchCase):
    """gate:四问各分支与判定矩阵(GO/PIVOT/WATCH/DROP)/重复否决/输入缺失。"""

    def seeded_sid(self, title=TITLE_GO):
        _, p = self.watch()
        return self.sid_of(p, title)

    def test_gate_go_news(self):
        sid = self.seeded_sid()
        angle = tmp_file(ANGLE_6)
        rc, g = self.gate(sid, "--angle", angle, "--exclusive", "data")
        self.assertEqual(rc, 0)                                     # 0=过闸
        self.assertEqual(g["verdict"], "go")
        self.assertEqual(g["verdict_type"], "News 型")              # <24h → News 候选
        st = self.load_state()["signals"][sid]
        fs, dl = tw.parse_iso(st["first_seen"]), tw.parse_iso(st["deadline"])
        self.assertEqual((dl - fs).total_seconds(), 24 * 3600)      # 发布截止=first_seen+24h
        self.assertEqual(st["q4"], "data")
        self.assertIn("PASS", st["q2"])
        brief = os.path.join(self.briefs, "trend-%s-%s.md"
                             % (sid, tw._now().strftime("%Y%m%d")))
        self.assertTrue(os.path.exists(brief))                      # 决策件按占位符预填落盘
        body = open(brief, encoding="utf-8").read()
        for needle in ("## 1. 信号登记表", "## 判定:GO(News 型", "signal_id | %s" % sid,
                       "wire 占位", "{{选题人"):
            self.assertIn(needle, body)

    def test_gate_go_analysis(self):
        sid = self.seeded_sid()
        st = self.load_state()
        st["signals"][sid]["first_seen"] = (datetime.now(timezone.utc)
                                            - timedelta(hours=30)).isoformat()   # 24-72h 窗口
        self.save_state(st)
        rc, g = self.gate(sid, "--angle", tmp_file(ANGLE_6), "--exclusive", "quote")
        self.assertEqual(rc, 0)
        self.assertEqual(g["verdict_type"], "Analysis 型")
        st = self.load_state()["signals"][sid]
        fs, dl = tw.parse_iso(st["first_seen"]), tw.parse_iso(st["deadline"])
        self.assertEqual((dl - fs).total_seconds(), 72 * 3600)

    def test_gate_pivot_wire_veto(self):
        sid = self.seeded_sid()
        rc, g = self.gate(sid, "--angle", tmp_file(ANGLE_6), "--exclusive", "data",
                          stub=make_stub(wire_body=GN_WIRE_HEAVY))
        self.assertEqual(rc, 1)
        self.assertEqual(g["verdict"], "pivot")                     # wire≥3 且 <24h → 硬新闻降级
        self.assertTrue(any("wire" in r for r in g["reasons"]))
        self.assertIn("触发", g["q"]["wire"])

    def test_gate_pivot_no_exclusive(self):
        sid = self.seeded_sid()
        rc, g = self.gate(sid, "--angle", tmp_file(ANGLE_6))        # 无 --exclusive
        self.assertEqual(rc, 1)
        self.assertEqual(g["verdict"], "pivot")
        self.assertIn("Q4 UNKNOWN", " ".join(g["reasons"]))

    def test_gate_q2_unknown_and_few_points(self):
        sid = self.seeded_sid()
        rc, g = self.gate(sid, "--exclusive", "data")               # 缺 --angle → Q2 UNKNOWN
        self.assertEqual(rc, 1)
        self.assertEqual(g["verdict"], "watch")
        self.assertIn("UNKNOWN", g["q"]["q2"])
        self.assertIsNotNone(g["deadline"])
        rc, g = self.gate(sid, "--angle", tmp_file(ANGLE_3), "--exclusive", "data")
        self.assertEqual(rc, 1)                                     # 3<5 观点 → 不过闸
        self.assertIn("FAIL(3", g["q"]["q2"])
        self.assertEqual(g["verdict"], "watch")

    def test_gate_q1_med_watch_and_low_drop(self):
        sid = self.seeded_sid(TITLE_MED)                            # Q1=10(10-24)
        rc, g = self.gate(sid, "--angle", tmp_file(ANGLE_6), "--exclusive", "data")
        self.assertEqual(rc, 1)
        self.assertEqual(g["verdict"], "watch")
        self.assertIn("相关性不足", g["reason"])
        sid = self.seeded_sid(TITLE_JUNK)                           # Q1=0(<10)
        rc, g = self.gate(sid, "--angle", tmp_file(ANGLE_6), "--exclusive", "data")
        self.assertEqual(rc, 1)
        self.assertEqual(g["verdict"], "drop")

    def test_gate_dup_active_go_drop(self):
        _, p = self.watch()
        sid_a = self.sid_of(p, TITLE_GO)
        sid_b = self.sid_of(p, TITLE_DUP)                           # 与 A 词重叠 85.7%
        rc, _ = self.gate(sid_a, "--angle", tmp_file(ANGLE_6), "--exclusive", "data")
        self.assertEqual(rc, 0)
        rc, g = self.gate(sid_b, "--angle", tmp_file(ANGLE_6), "--exclusive", "data")
        self.assertEqual(rc, 1)                                     # 重复否决:合并,不新开
        self.assertEqual(g["verdict"], "drop")
        self.assertIn("重复否决", g["reason"])
        self.assertIn(sid_a, g["reason"])

    def test_gate_wire_failure_tolerated(self):
        sid = self.seeded_sid()
        rc, g = self.gate(sid, "--angle", tmp_file(ANGLE_6), "--exclusive", "access",
                          stub=make_stub(wire_fail_titles={TITLE_GO}))
        self.assertEqual(rc, 0)                                     # wire 未检 → 明说不猜,按未触发
        self.assertIn("未检", g["q"]["wire"])

    def test_gate_input_errors_exit3(self):
        self.watch()
        rc, g = self.gate("deadbeef01", "--angle", tmp_file(ANGLE_6))   # 信号不在库
        self.assertEqual(rc, 3)
        _, p = self.watch()
        sid = self.sid_of(p, TITLE_GO)
        rc, _ = self.gate(sid, "--angle", "/nonexistent/angle.md")      # 角度文件缺失
        self.assertEqual(rc, 3)


# ---------------------------------------------------------------- backlog
class BacklogTests(TrendWatchCase):
    """backlog:总览/状态过滤/deadline 到期升退级标记。"""

    def test_lists_filters_and_json(self):
        _, p = self.watch()
        sid = self.sid_of(p, TITLE_GO)
        self.gate(sid, "--angle", tmp_file(ANGLE_6), "--exclusive", "data")
        import contextlib, io
        buf = io.StringIO()
        with patch.object(tw, "fetch_url", make_stub()), contextlib.redirect_stdout(buf):
            rc = tw.main(["backlog", "--state", self.state])
        out = buf.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn(sid, out)
        self.assertIn("| go(News 型) |", out)
        self.assertIn("| watch |", out)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = tw.main(["backlog", "--state", self.state, "--status", "go", "--json"])
        rows = json.loads(buf.getvalue())
        self.assertEqual(rc, 0)
        self.assertEqual(rows["counts"], {"go": 1})
        self.assertEqual(rows["signals"][0]["signal_id"], sid)

    def test_expired_deadline_flagged(self):
        _, p = self.watch()
        sid = self.sid_of(p, TITLE_GO)
        self.gate(sid, "--angle", tmp_file(ANGLE_6), "--exclusive", "data")
        st = self.load_state()
        st["signals"][sid]["deadline"] = (datetime.now(timezone.utc)
                                          - timedelta(hours=2)).isoformat()
        self.save_state(st)
        import contextlib, io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            tw.main(["backlog", "--state", self.state])
        out = buf.getvalue()
        self.assertIn("到期未处理", out)
        self.assertIn("建议降级", out)                              # 防过期 GO 还在写


# ---------------------------------------------------------------- CLI 契约
class CliTests(unittest.TestCase):
    """/--help 与参数错误退出码(subprocess,零网络:help 不触发 fetch)。"""

    def test_help_and_noargs(self):
        r = run_script("--help")
        self.assertEqual(r.returncode, 0)
        for word in ("watch", "gate", "backlog"):
            self.assertIn(word, r.stdout)
        for cmd in ("watch", "gate", "backlog"):
            self.assertEqual(run_script(cmd, "--help").returncode, 0)
        self.assertEqual(run_script().returncode, 3)                # 无子命令 → 参数错误

    def test_bad_args_exit3(self):
        self.assertEqual(run_script("watch", "--sources", "bogus").returncode, 3)
        self.assertEqual(run_script("gate").returncode, 3)          # 缺 --signal-id


if __name__ == "__main__":
    unittest.main(verbosity=2)
