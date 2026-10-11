#!/usr/bin/env python3
"""R5 已复现 5 bug 的修复回归(references/overview/pipeline-completeness.md §R5;
grounding_page.py + trend_watch.py,合成 fixture,零网络)。逐条对应:
①grounding sameAs `h in host` 子串误配(x.com 命中 box.com)→ 可注册域相等
②同标签 volatile 事实 ≥3 条,第 3 条起被静默丢弃 → _add_faq 撞已用问题时并入既有条目
③volatile 日期仅认 %Y-%m-%d,解析失败静默回退今天 → 告警 + last_reviewed=None(宁缺勿假)
④trend _strip_publisher 从第一个 ' - ' 截到尾 → rfind 取最后一个(尾段≤40 字符才截)
⑤compute_velocity 跨源排位不可比(hn 1-15 vs weibo 1-50 混样)→ 仅同 src 可比,
  同源样本不足 → None(不可判);无 src 键的旧状态样本按同源处理(向后兼容)
standalone: python3 tests/test_fix_grounding_trend.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载(勿 import 期副作用)。"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import grounding_page as gp  # noqa: E402  (需先入 SCRIPTS 路径;import 期无副作用)
import trend_watch as tw     # noqa: E402


def run_script(name, *args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_file(content, suffix):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


# ---------------------------------------------------------------- ① sameAs 可注册域相等

FACTS_SAMEAS = """\
brand: Acme
facts:
  - fact: "Acme 是一家 CRM 软件公司"
    record: company
    source: https://acme.ai/about
    date: 2026-09-01
    confidence: high
  - fact: "Acme 的 X 档案是 https://x.com/acme"
    record: execution
    source: https://box.com/s/acme-files
    date: 2026-10-01
    confidence: high
"""


class SameAsRegistrableDomainTests(unittest.TestCase):
    """①子串含入→可注册域相等:box.com 不再被 x.com 收进 sameAs。"""

    def test_box_com_not_substring_matched(self):
        facts = [{"fact": "文件存在 https://box.com/s/acme", "source": ""},
                 {"fact": "X 档案 https://x.com/acme", "source": ""}]
        self.assertEqual(gp.extract_sameas(facts), ["https://x.com/acme"])

    def test_host_match_by_registrable_domain(self):
        ok = ["x.com", "www.linkedin.com", "de.linkedin.com", "wikidata.org",
              "mastodon.social", "foo.mastodon.online", "zhihu.com"]
        for host in ok:
            self.assertTrue(gp._host_is_social(host), host)
        bad = ["box.com", "notx.com", "linkedin.evil.com", "x.company",
               "mastodon.evil.com", "acme.ai", ""]
        for host in bad:
            self.assertFalse(gp._host_is_social(host), host)

    def test_end_to_end_jsonld_sameas(self):
        p = tmp_file(FACTS_SAMEAS, ".yaml")
        try:
            r = run_script("grounding_page.py", "--facts", p, "--name", "Acme", "--json")
            self.assertEqual(r.returncode, 0)
            ld = json.loads(r.stdout)["jsonld"]
            self.assertEqual(ld["sameAs"], ["https://x.com/acme"])   # box.com 出局
        finally:
            os.unlink(p)


# ---------------------------------------------------------------- ② 同标签 volatile 并入既有 FAQ 条目

FACTS_MULTI_PRICE = """\
brand: Multi
facts:
  - fact: "Multi 是一家在线表单工具公司"
    record: company
    source: https://multi.io/about
    date: 2026-09-01
    confidence: high
  - fact: "Multi 成立于 2020 年"
    record: company
    source: https://multi.io/about
    date: 2026-09-01
    confidence: high
  - fact: "Multi 总部在西雅图"
    record: company
    source: https://multi.io/about
    date: 2026-09-01
    confidence: high
  - fact: "Multi 的创始人是王某"
    record: company
    source: https://multi.io/about
    date: 2026-09-01
    confidence: high
  - fact: "Multi 免费版定价为 $0"
    record: offerings
    source: https://multi.io/pricing
    date: 2026-10-01
    confidence: high
  - fact: "Multi Pro 定价为 $15/月"
    record: offerings
    source: https://multi.io/pricing
    date: 2026-10-01
    confidence: high
  - fact: "Multi Team 定价为 $50/月"
    record: offerings
    source: https://multi.io/pricing
    date: 2026-10-01
    confidence: high
"""


class VolatileFaqMergeTests(unittest.TestCase):
    """②同标签(定价)volatile 3 条:并入同一问题答案,不再从第 3 条起静默丢弃。"""

    @classmethod
    def setUpClass(cls):
        cls.facts = tmp_file(FACTS_MULTI_PRICE, ".yaml")
        cls.dir = tempfile.mkdtemp(prefix="gp_fix_")
        r = run_script("grounding_page.py", "--facts", cls.facts, "--name", "Multi", "--json")
        assert r.returncode == 0, r.stderr
        cls.payload = json.loads(r.stdout)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.facts)
        for n in os.listdir(cls.dir):
            os.unlink(os.path.join(cls.dir, n))
        os.rmdir(cls.dir)

    def test_third_same_label_fact_not_dropped(self):
        faq = self.payload["faq"]
        pricing = [f for f in faq if f["question"] == "Multi 的定价是多少?"]
        self.assertEqual(len(pricing), 1, "同标签多条只开一个问题")
        answer = pricing[0]["answer"]
        for price in ("$0", "$15/月", "$50/月"):          # 第 3 条不再被丢弃
            self.assertIn(price, answer)
        self.assertTrue(5 <= len(faq) <= 10)
        self.assertTrue(all("Multi" in f["answer"] for f in faq))   # 含名率不破

    def test_markdown_faq_section_carries_all_three(self):
        m = re.search(r'<section id="faq">(.*?)</section>', self.payload["markdown"], re.S)
        for price in ("$0", "$15/月", "$50/月"):
            self.assertIn(price, m.group(1))

    def test_check_still_all_pass(self):
        page = os.path.join(self.dir, "multi.md")
        r = run_script("grounding_page.py", "--facts", self.facts, "--name", "Multi",
                       "--out", page)
        self.assertEqual(r.returncode, 0)
        c = run_script("grounding_page.py", "--check", page, "--name", "Multi")
        self.assertEqual(c.returncode, 0)
        self.assertNotIn("[FAIL]", c.stdout)


# ---------------------------------------------------------------- ③ volatile 日期:宁缺勿假

FACTS_BAD_DATE = """\
brand: Multi
facts:
  - fact: "Multi 是一家在线表单工具公司"
    record: company
    source: https://multi.io/about
    date: 2026-09-01
    confidence: high
  - fact: "Multi 成立于 2020 年"
    record: company
    source: https://multi.io/about
    date: 2026-09-01
    confidence: high
  - fact: "Multi 总部在西雅图"
    record: company
    source: https://multi.io/about
    date: 2026-09-01
    confidence: high
  - fact: "Multi 的创始人是王某"
    record: company
    source: https://multi.io/about
    date: 2026-09-01
    confidence: high
  - fact: "Multi Pro 定价为 $15/月"
    record: offerings
    source: https://multi.io/pricing
    date: 2026/10/01
    confidence: high
  - fact: "Multi 支持 iOS 与 Android"
    record: offerings
    source: https://multi.io/mobile
    confidence: high
"""

FACTS_MIXED_DATE = FACTS_BAD_DATE.replace("date: 2026/10/01", "date: 15/09/2026") + """\
  - fact: "Multi 支持 SSO 登录"
    record: offerings
    source: https://docs.multi.io/sso
    date: 2026-09-15
    confidence: high
"""


class VolatileDateIntegrityTests(unittest.TestCase):
    """③解析失败不再静默回退今天:告警 + last_reviewed=None(宁缺勿假)。"""

    def test_all_unparseable_yields_none_and_warning(self):
        p = tmp_file(FACTS_BAD_DATE, ".yaml")
        try:
            r = run_script("grounding_page.py", "--facts", p, "--name", "Multi", "--json")
            self.assertEqual(r.returncode, 0)
            payload = json.loads(r.stdout)
            self.assertIsNone(payload["volatile_last_reviewed"])       # 不伪造今天
            self.assertIn("<p>Last reviewed: ?</p>", payload["markdown"])
            self.assertIn("无法解析", r.stderr)                        # 告警明说
            self.assertIn("宁缺勿假", r.stderr)
            self.assertIn("(空)", r.stderr)                            # 缺 date 键也点名
            today_damaged = "Last reviewed: %s" % datetime.now().date().isoformat()
            self.assertNotIn(today_damaged, payload["markdown"])       # volatile 区不是今天
        finally:
            os.unlink(p)

    def test_mixed_dates_use_parsed_max_and_warn_bad_one(self):
        p = tmp_file(FACTS_MIXED_DATE, ".yaml")
        try:
            r = run_script("grounding_page.py", "--facts", p, "--name", "Multi", "--json")
            self.assertEqual(r.returncode, 0)
            payload = json.loads(r.stdout)
            self.assertEqual(payload["volatile_last_reviewed"], "2026-09-15")  # 用真日期
            self.assertIn("无法解析", r.stderr)                        # 坏格式逐条告警
            self.assertNotIn("宁缺勿假", r.stderr)                     # 有可解析日期→不置空
        finally:
            os.unlink(p)

    def test_generated_page_still_checks_ok(self):
        p = tmp_file(FACTS_BAD_DATE, ".yaml")
        page = os.path.join(tempfile.mkdtemp(prefix="gp_bd_"), "page.md")
        try:
            r = run_script("grounding_page.py", "--facts", p, "--name", "Multi", "--out", page)
            self.assertEqual(r.returncode, 0)
            c = run_script("grounding_page.py", "--check", page, "--name", "Multi")
            self.assertEqual(c.returncode, 0)                         # 第 5/10 条仍机检通过
            self.assertIn("[PASS] 05", c.stdout)
        finally:
            os.unlink(p)
            os.unlink(page)
            os.rmdir(os.path.dirname(page))


# ---------------------------------------------------------------- ④ _strip_publisher 取最后一个 " - "

TITLE_GO = "OpenAI launches GPT-6 benchmark suite"


class StripPublisherTests(unittest.TestCase):
    """④标题含 ' - ' 时从第一个截到尾会吞标题中段;改 rfind 取最后一个。"""

    def test_strips_at_last_dash_only(self):
        self.assertEqual(tw._strip_publisher("AI agents - the next era - TechCrunch"),
                         "AI agents - the next era")                  # 标题中段保留
        self.assertEqual(tw._strip_publisher("A - B - C - Pub"), "A - B - C")

    def test_single_dash_unchanged_behavior(self):
        self.assertEqual(tw._strip_publisher("%s - TechCrunch" % TITLE_GO), TITLE_GO)
        self.assertEqual(tw._strip_publisher("No dash here"), "No dash here")

    def test_long_or_empty_tail_kept(self):
        long_tail = "A - " + "b" * 45                                 # 尾段>40 字符=标题本体
        self.assertEqual(tw._strip_publisher(long_tail), long_tail)
        self.assertEqual(tw._strip_publisher("Title - "), "Title - ")  # 空尾段不截

    def test_google_news_source_end_to_end(self):
        rss = ('<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>'
               '<item><title>Acme raises - Series B - TechCrunch</title>'
               '<link>https://techcrunch.com/a</link>'
               '<source url="https://techcrunch.com">TechCrunch</source></item>'
               '</channel></rss>')
        with patch.object(tw, "fetch_url", lambda url: rss):
            items = tw._src_google_news({"market": "en", "tokens": ["acme"]})
        self.assertEqual(items[0]["title"], "Acme raises - Series B")


# ---------------------------------------------------------------- ⑤ compute_velocity 仅同源可比

class VelocitySameSourceTests(unittest.TestCase):
    """⑤跨源排位量纲不可比(hn 1-15 vs weibo 1-50):只与最新样本同 src 的历史比;
    同源样本不足 → None(不可判);无 src 键的旧状态样本视为同源(向后兼容)。"""

    def setUp(self):
        self.now = datetime(2026, 10, 12, 12, 0, tzinfo=timezone.utc)
        self.ts = lambda mins: (self.now - timedelta(minutes=mins)).isoformat()

    def test_cross_source_positions_not_compared(self):
        # 旧实现:weibo#30 vs hn#2 → 假 "fading";weibo 1-50 榜内 30 本就可能 hotter
        self.assertIsNone(tw.compute_velocity(
            [{"ts": self.ts(40), "pos": 2, "src": "hn"},
             {"ts": self.ts(0), "pos": 30, "src": "weibo"}], self.now, 30))
        # 反向同理:hn#1 vs weibo#45 → 不得判 "rising"
        self.assertIsNone(tw.compute_velocity(
            [{"ts": self.ts(40), "pos": 45, "src": "weibo"},
             {"ts": self.ts(0), "pos": 1, "src": "hn"}], self.now, 30))

    def test_same_src_with_cross_src_interloper(self):
        # 最新样本 weibo#10;更近的 hn#1 是异源,不得参与 → weibo 50→10 = rising
        self.assertEqual(tw.compute_velocity(
            [{"ts": self.ts(40), "pos": 50, "src": "weibo"},
             {"ts": self.ts(35), "pos": 1, "src": "hn"},
             {"ts": self.ts(0), "pos": 10, "src": "weibo"}], self.now, 30), "rising")
        # 同源 hn 3→14 = fading(中间 weibo 样本无视)
        self.assertEqual(tw.compute_velocity(
            [{"ts": self.ts(40), "pos": 3, "src": "hn"},
             {"ts": self.ts(35), "pos": 45, "src": "weibo"},
             {"ts": self.ts(0), "pos": 14, "src": "hn"}], self.now, 30), "fading")

    def test_insufficient_same_src_history_is_none(self):
        self.assertIsNone(tw.compute_velocity(
            [{"ts": self.ts(5), "pos": 3, "src": "hn"}], self.now, 30))       # 样本不足
        self.assertIsNone(tw.compute_velocity(                                  # 唯一同源样本太新
            [{"ts": self.ts(10), "pos": 5, "src": "hn"},
             {"ts": self.ts(0), "pos": 2, "src": "hn"}], self.now, 30))
        self.assertIsNone(tw.compute_velocity(                                  # pos 非整数
            [{"ts": self.ts(40), "pos": 5, "src": "hn"},
             {"ts": self.ts(0), "pos": None, "src": "hn"}], self.now, 30))

    def test_legacy_samples_without_src_still_compared(self):
        self.assertEqual(tw.compute_velocity(
            [{"ts": self.ts(40), "pos": 5}, {"ts": self.ts(0), "pos": 2}],
            self.now, 30), "rising")


RSS_ONE = ('<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>'
           '<item><title>%s - TechCrunch</title><link>https://techcrunch.com/a</link>'
           '<source url="https://techcrunch.com">TechCrunch</source></item></channel></rss>'
           % TITLE_GO)


def _watch_stub(url):
    if "/rss/search" in url or "news.google.com" in url:
        return RSS_ONE
    if "topstories" in url:
        return "[1]"
    if "/item/" in url:
        return json.dumps({"id": 1, "title": TITLE_GO, "url": "https://openai.com/gpt6"})
    raise AssertionError("stub: 未预期的 URL %s" % url)


class VelocityWatchIntegrationTests(unittest.TestCase):
    """⑤watch 级端到端:预置 40min 前的 gn#5 样本,本轮最新样本来自 hn →
    不可判 None(旧实现拿 gn 5→hn 1 造假 rising);同源预置(hn)仍判 rising。"""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.state = os.path.join(self.dir.name, "state.json")
        self.briefs = os.path.join(self.dir.name, "briefs")
        self.addCleanup(self.dir.cleanup)

    def _watch(self):
        buf = io.StringIO()
        with patch.object(tw, "fetch_url", _watch_stub), contextlib.redirect_stdout(buf):
            rc = tw.main(["watch", "--state", self.state, "--brief-dir", self.briefs,
                          "--market", "en", "--vertical", "openai llm",
                          "--sources", "google-news,hn", "--json"])
        return rc

    def _sig(self):
        with open(self.state, encoding="utf-8") as f:
            st = json.load(f)
        sig = [s for s in st["signals"].values() if s["title"] == TITLE_GO]
        self.assertTrue(sig, "TITLE_GO 应已登记")
        return st, sig[0]

    def _seed_sample(self, src):
        st, sig = self._sig()
        old = (datetime.now(timezone.utc) - timedelta(minutes=40)).isoformat()
        sig["samples"] = [{"ts": old, "pos": 5, "src": src}]
        with open(self.state, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False)

    def test_cross_src_seed_none_then_same_src_seed_rising(self):
        self.assertEqual(self._watch(), 0)
        self._seed_sample("google-news")      # 历史 gn#5,最新样本 hn#1:跨源不可比
        self._watch()
        _, sig = self._sig()
        self.assertIsNone(sig["velocity"])
        self._seed_sample("hn")               # 同源 hn#5→hn#1:rising(既有口径不回归)
        self._watch()
        _, sig = self._sig()
        self.assertEqual(sig["velocity"], "rising")


if __name__ == "__main__":
    unittest.main(verbosity=1)
