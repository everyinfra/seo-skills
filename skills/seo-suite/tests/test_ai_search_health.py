#!/usr/bin/env python3
"""site_audit.py S3 扩展测试:AI Search Health 子分(Semrush 8 bot 名单)/
rendering 5 检查(CSR 与 SSR 赦免)/BLUF 密度公式边界/语义 HTML 比值/子分聚合。
standalone(自带 run_script 助手,合成 HTML fixture + stub fetch,零网络):
python3 tests/test_ai_search_health.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。"""
import io
import json
import re
import subprocess
import sys
import os
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import site_audit as sa  # noqa: E402  (需先入 SCRIPTS 路径)

EIGHT_BOTS = {"ChatGPT-User", "OAI-SearchBot", "Googlebot", "Google-Extended",
              "Perplexity-User", "PerplexityBot", "Claude-User", "Claude-SearchBot"}


def run_script(name, args=(), stdin=None):
    """独立助手(与 run_tests.py 同形):子进程跑 scripts/ 下脚本,捕获输出。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def plain_of(html):
    """与 audit() 同口径的规范化纯文本(测试助手,复刻脚本内两步正则)。"""
    body = re.sub(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>", " ", html, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()


def page_of(html):
    p = sa.Page()
    p.feed(html)
    return p


GOOD_HTML = (
    '<!doctype html><html lang="en"><head><title>Example Article Page Title Long Enough</title>'
    '<meta name="description" content="A sufficiently long description text that exceeds eighty characters easily for tests.">'
    '<meta property="og:title" content="t"><meta property="og:description" content="d">'
    '<meta property="og:image" content="https://example.com/i.png">'
    '<script type="application/ld+json">{"@context":"https://schema.org"}</script></head><body>'
    '<header><nav>nav links here</nav></header><main><article>'
    '<h1>Main Heading of the Page</h1>'
    '<p>In short, here is the direct answer with facts. ' + "filler content word " * 120 + '</p>'
    '<h2>Section One</h2><ul><li>alpha</li><li>beta</li><li>gamma</li><li>delta</li></ul>'
    '<h2>Section Two</h2><p>more body content for the test page</p>'
    '</article></main><footer>footer text</footer></body></html>')


def httpdate(days_ago):
    return format_datetime(datetime.now(timezone.utc) - timedelta(days=days_ago))


def stub_fetch(pages, root="https://example.com"):
    """零网络 fetch 替身:pages={路径: (status, headers, body) 或 None=404};精确 URL 键优先。"""
    table = {root + path: v for path, v in pages.items()}

    def _fetch(url, timeout=15):
        if url in table and table[url] is not None:
            st, hdrs, body = table[url]
            return st, hdrs, body
        import urllib.error
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
    return _fetch


class StubbedAudit(unittest.TestCase):
    """stub fetch 下跑完整 audit()(零网络):子分字段形状/findings 级别/兼容旧字段。"""

    def _audit(self, pages, url="https://example.com/"):
        orig = sa.fetch
        sa.fetch = stub_fetch(pages)
        try:
            return sa.audit(url, "en")
        finally:
            sa.fetch = orig

    def test_all_good_page_scores_100(self):
        F, meta, ai = self._audit({
            "/": (200, {"Last-Modified": httpdate(10)}, GOOD_HTML),
            "/robots.txt": (200, {}, "User-agent: *\nAllow: /\n"),
            "/sitemap.xml": (200, {}, "<urlset/>"),
            "/llms.txt": (200, {}, "# llms\n")})
        self.assertEqual(ai["score"], 100)
        self.assertEqual(ai["bots"]["allowed"], sa.SEARCH_BOTS)   # 8 bot 全放行
        self.assertEqual(ai["bots"]["blocked"], [])
        self.assertEqual(ai["last_modified_days"], 10)
        self.assertEqual({c["id"] for c in ai["checks"]},
                         {"bots", "llms_txt", "freshness", "semantic_html", "content_length", "bluf"})
        self.assertTrue(all(c["pass"] for c in ai["checks"]))
        # 旧输出兼容:meta 字段一仍其旧;被禁 bot 为 0 → 无 ai-bots CRITICAL
        self.assertEqual(meta["h1"], 1)
        self.assertNotIn(("CRITICAL", "ai-bots"), [(s, a) for s, a, _ in F])

    def test_blocked_search_bots_critical_and_score_drop(self):
        robots = ("User-agent: PerplexityBot\nDisallow: /\n"
                  "User-agent: Perplexity-User\nDisallow: /\n"
                  "User-agent: Google-Extended\nDisallow: /\n"
                  "User-agent: *\nAllow: /\n")
        F, _, ai = self._audit({
            "/": (200, {"Last-Modified": httpdate(10)}, GOOD_HTML),
            "/robots.txt": (200, {}, robots),
            "/sitemap.xml": (200, {}, "<urlset/>"),
            "/llms.txt": (200, {}, "# llms\n")})
        self.assertEqual(ai["bots"]["blocked"], ["Google-Extended", "Perplexity-User", "PerplexityBot"])
        self.assertEqual(ai["score"], 60)                        # bots 0.4 丢光,其余全过
        bots = [(s, m) for s, a, m in F if a == "ai-bots"]
        self.assertEqual([s for s, _ in bots].count("CRITICAL"), 2)   # 两个爬虫型被禁
        self.assertIn("WARN", [s for s, _ in bots])              # Google-Extended 单列 WARN
        ge = [m for s, m in bots if s == "WARN"][0]
        self.assertIn("robots token", ge)

    def test_training_bots_notice_only_not_failure(self):
        F, _, ai = self._audit({
            "/": (200, {}, GOOD_HTML),
            "/robots.txt": (200, {}, "User-agent: GPTBot\nDisallow: /\nUser-agent: *\nAllow: /\n"),
            "/sitemap.xml": (200, {}, "<urlset/>"),
            "/llms.txt": (200, {}, "# llms\n")})
        infos = [m for s, a, m in F if a == "ai-bots" and s == "INFO"]
        self.assertTrue(any("GPTBot" in m and "训练型" in m for m in infos))
        self.assertNotIn("GPTBot", ai["bots"]["blocked"])        # 不在 8 bot 失败项
        self.assertEqual(ai["score"], 100)                       # 不影响子分

    def test_missing_llms_and_stale_last_modified(self):
        F, _, ai = self._audit({
            "/": (200, {"Last-Modified": httpdate(400)}, GOOD_HTML),
            "/robots.txt": (200, {}, "User-agent: *\nAllow: /\n")})
        # llms.txt 404 → 既有 INFO 不可达照旧 + 子分 llms_txt fail;400 天 → freshness fail
        self.assertTrue(any(a == "llms.txt" and s == "INFO" for s, a, _ in F))
        by_id = {c["id"]: c["pass"] for c in ai["checks"]}
        self.assertFalse(by_id["llms_txt"])
        self.assertFalse(by_id["freshness"])
        self.assertEqual(ai["last_modified_days"], 400)
        self.assertEqual(ai["score"], 70)                        # 0.15+0.15 丢光
        self.assertTrue(any(a == "freshness" and s == "INFO" for s, a, _ in F))

    def test_csr_shell_renders_warn_not_critical(self):
        csr_html = ('<!doctype html><html lang="en"><head><title>SPA Shell Page</title>'
                    '<meta name="description" content="' + "x" * 90 + '"></head><body>'
                    '<div id="root"></div><script src="/app.js"></script>'
                    '<noscript>This page requires JavaScript enabled to see any content at all.</noscript>'
                    '</body></html>')
        F, _, ai = self._audit({
            "/": (200, {}, csr_html),
            "/robots.txt": (200, {}, "User-agent: *\nAllow: /\n")})
        rend = [(s, m) for s, a, m in F if a == "rendering"]
        self.assertTrue(any(s == "WARN" and "CSR" in m for s, m in rend))
        # rendering 只出 WARN/INFO,不产生 CRITICAL
        self.assertFalse(any(s == "CRITICAL" and a == "rendering" for s, a, _ in F))

    def test_main_json_contains_ai_search_health_section(self):
        argv_orig, fetch_orig = sys.argv, sa.fetch
        sys.argv = ["site_audit.py", "https://example.com/", "--json"]
        sa.fetch = stub_fetch({
            "/": (200, {"Last-Modified": httpdate(10)}, GOOD_HTML),
            "/robots.txt": (200, {}, "User-agent: *\nAllow: /\n"),
            "/sitemap.xml": (200, {}, "<urlset/>"),
            "/llms.txt": (200, {}, "# llms\n")})
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                with self.assertRaises(SystemExit) as cm:
                    sa.main()
        finally:
            sys.argv, sa.fetch = argv_orig, fetch_orig
        self.assertEqual(cm.exception.code, 0)
        out = buf.getvalue()
        self.assertIn("ai_search_health: 100/100", out)          # 文本报告与主审计并列
        payload = json.loads(out[out.rindex("\n{"):])
        r = payload["results"]["https://example.com/"]
        # 旧字段不删不改;新增 ai_search_health 节
        for legacy in ("verdict", "findings", "meta"):
            self.assertIn(legacy, r)
        ai = r["ai_search_health"]
        for key in ("score", "bots", "last_modified_days", "semantic_ratio", "checks"):
            self.assertIn(key, ai)
        self.assertIn("allowed", ai["bots"])
        self.assertIn("blocked", ai["bots"])

    def test_help_mentions_ai_search_health(self):
        r = run_script("site_audit.py", ["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("ai_search_health", r.stdout + r.stderr)
        self.assertIn("Google-Extended", r.stdout)


class BotListRobotsTests(unittest.TestCase):
    """Semrush 8 bot 名单 + 自写最长匹配 robots 判定。"""

    def test_search_bot_list_is_exactly_eight(self):
        self.assertEqual(set(sa.SEARCH_BOTS), EIGHT_BOTS)
        self.assertEqual(len(sa.SEARCH_BOTS), 8)
        self.assertEqual(sa.TRAINING_BOTS, ["GPTBot", "ClaudeBot"])
        self.assertNotIn("GPTBot", sa.SEARCH_BOTS)
        self.assertNotIn("ClaudeBot", sa.SEARCH_BOTS)

    def test_wildcard_group_blocks_and_specific_group_beats_wildcard(self):
        g = sa.parse_robots_groups("User-agent: *\nDisallow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n")
        self.assertFalse(sa.robots_allows(g, "ChatGPT-User", "https://e.com/x"))   # 落入 *
        self.assertTrue(sa.robots_allows(g, "OAI-SearchBot", "https://e.com/x"))   # 专属组优先

    def test_longest_match_allow_overrides_disallow(self):
        g = sa.parse_robots_groups("User-agent: Claude-User\nDisallow: /\nAllow: /public/\n")
        self.assertTrue(sa.robots_allows(g, "Claude-User", "https://e.com/public/page"))
        self.assertFalse(sa.robots_allows(g, "Claude-User", "https://e.com/other"))
        self.assertTrue(sa.robots_allows(g, "Claude-SearchBot", "https://e.com/other"))  # 无组无 * → 默认放行

    def test_consecutive_user_agents_share_group_and_case_insensitive(self):
        g = sa.parse_robots_groups("user-agent: GPTBot\nUser-agent: ClaudeBot\nDisallow: /private # 训练\n")
        self.assertFalse(sa.robots_allows(g, "GPTBot", "https://e.com/private/x"))
        self.assertFalse(sa.robots_allows(g, "ClaudeBot", "https://e.com/private/x"))
        self.assertTrue(sa.robots_allows(g, "GPTBot", "https://e.com/open"))       # 注释剥离,规则只限 /private

    def test_google_extended_token_checked_separately(self):
        g = sa.parse_robots_groups("User-agent: Google-Extended\nDisallow: /\n")
        self.assertFalse(sa.robots_allows(g, "Google-Extended", "https://e.com/"))  # token 单列被禁
        self.assertTrue(sa.robots_allows(g, "Googlebot", "https://e.com/"))        # Googlebot 不受牵连

    def test_empty_disallow_and_empty_groups_default_allow(self):
        g = sa.parse_robots_groups("User-agent: *\nDisallow:\n")
        self.assertTrue(sa.robots_allows(g, "Googlebot", "https://e.com/anything"))
        self.assertTrue(sa.robots_allows({}, "Googlebot", "https://e.com/"))        # robots 不可达 → 放行


class CSRDetectionTests(unittest.TestCase):
    """CSR 检测(#root/#app/#__next/#svelte + 文本/比值阈值)与 SSR 赦免。"""

    SHELL = ('<html><head><title>t</title></head><body><div id="root"></div>'
             '<script src="/app.js"></script></body></html>')

    def test_empty_mount_thin_text_triggers(self):
        p = page_of(self.SHELL)
        self.assertIsNotNone(sa.detect_csr(p, plain_of(self.SHELL), len(self.SHELL)))
        csr = sa.detect_csr(p, plain_of(self.SHELL), len(self.SHELL))
        self.assertEqual(csr["mounts"], ["root"])
        self.assertLess(csr["text_chars"], 200)

    def test_next_data_amnesty(self):
        html = self.SHELL.replace('<script src="/app.js"></script>',
                                  '<script id="__NEXT_DATA__">{"props":{}}</script>')
        p = page_of(html)
        self.assertIsNone(sa.detect_csr(p, plain_of(html), len(html)))

    def test_reactroot_amnesty(self):
        html = '<html><body><div id="app" data-reactroot=""></div></body></html>'
        p = page_of(html)
        self.assertIsNone(sa.detect_csr(p, plain_of(html), len(html)))

    def test_text_rich_mount_page_not_flagged(self):
        html = ('<html><body><div id="app"><h1>Hi</h1><p>' + "dense text " * 200 +
                '</p></div></body></html>')
        p = page_of(html)
        self.assertIsNone(sa.detect_csr(p, plain_of(html), len(html)))   # 文本≥200 且比值≥0.02

    def test_low_text_html_ratio_triggers_even_over_200_chars(self):
        fat = "a" * 20000                                              # 无文本的肥标记
        html = (f'<html><body><div id="__next"></div><p>{"x" * 250}</p>'
                f'<span style="padding:{fat}"></span></body></html>')
        p = page_of(html)
        plain = plain_of(html)
        self.assertGreaterEqual(len(plain), 200)                        # 文本条件不命中
        csr = sa.detect_csr(p, plain, len(html))
        self.assertIsNotNone(csr)                                       # 靠 text/HTML<0.02 命中
        self.assertLess(csr["ratio"], 0.02)

    def test_page_collects_rendering_signals(self):
        p = page_of('<body><div id="__next"></div><script src="a.js"></script>'
                    '<script>var x=1;</script><noscript>enable js please now</noscript>'
                    '<ul><li>1</li><li>2</li></ul></body>')
        self.assertEqual(p.mounts, {"__next"})
        self.assertEqual(p.ext_scripts, 1)
        self.assertGreater(p.inline_js_bytes, 0)                         # 内联 JS 计字节(ld+json 不计)
        self.assertIn("enable js", "".join(p.noscript_text))
        self.assertEqual(p.li_count, 2)
        ld = page_of('<script type="application/ld+json">{"a":"' + "b" * 500 + '"}</script>')
        self.assertEqual(ld.inline_js_bytes, 0)                          # JSON-LD 不算内联 JS


class BLUFDensityTests(unittest.TestCase):
    """BLUF 公式边界:first_chunk=max(20%×长,400);score=min(1,(短语+li>3+首块>100)/2);pass≥0.5。"""

    def test_all_absent_short_text_scores_zero(self):
        s, _ = sa.bluf_score("x" * 100, 3)                              # 首块恰 100 字(不含>100)
        self.assertEqual(s, 0.0)

    def test_first_chunk_101_chars_boundary(self):
        s, _ = sa.bluf_score("x" * 101, 0)
        self.assertEqual(s, 0.5)                                        # 仅"首块>100"一条 → 0.5 达标

    def test_li_count_boundary_three_vs_four(self):
        self.assertEqual(sa.bluf_score("x" * 100, 3)[0], 0.0)           # li=3 不算
        self.assertEqual(sa.bluf_score("x" * 100, 4)[0], 0.5)           # li=4 计入

    def test_direct_phrase_alone_passes(self):
        s, d = sa.bluf_score("In short, yes it is.", 0)
        self.assertEqual(s, 0.5)
        self.assertIn("命中", d)

    def test_cap_at_one(self):
        text = "TL;DR the answer is here. " + "detail " * 200
        s, _ = sa.bluf_score(text, 10)
        self.assertEqual(s, 1.0)                                        # (1+1+1)/2=1.5 → 封顶 1

    def test_phrase_variants_and_non_match(self):
        for hit in ("Here's how to start", "the bottom line is", "Key Takeaways:",
                    "Here's why it works", "The answer is 42"):
            self.assertGreaterEqual(sa.bluf_score(hit, 0)[0], 0.5)
        self.assertEqual(sa.bluf_score("summarize the long story", 0)[0], 0.0)  # summarize 不含 summary
        self.assertEqual(sa.bluf_score("x" * 100, 0)[0], 0.0)

    def test_first_chunk_is_max_of_20pct_and_400(self):
        text = "y" * 10000
        s, d = sa.bluf_score(text, 0)
        self.assertIn("2000 字", d)                                     # 20%×10000=2000 > 400


class SemanticRatioTests(unittest.TestCase):
    """语义标签数 ÷ 非语义标签数;<10% 触发;边界与除零。"""

    def test_page_counts_semantic_vs_all(self):
        p = page_of("<html><body><header><nav>n</nav></header><main><article>"
                    "<h1>t</h1><p>words</p></article></main></body></html>")
        # 语义:header nav main article h1=5;非语义:html body p=3
        self.assertEqual((p.semantic_tags, p.all_tags), (5, 8))
        self.assertAlmostEqual(sa.semantic_ratio(p.semantic_tags, p.all_tags), 5 / 3)

    def test_div_soup_below_threshold(self):
        p = page_of("<html><body>" + "<div><span>s</span></div>" * 10 + "<main>m</main></body></html>")
        ratio = sa.semantic_ratio(p.semantic_tags, p.all_tags)
        self.assertLess(ratio, 0.10)                                    # 触发 <10%

    def test_ratio_boundary_exactly_ten_percent(self):
        self.assertEqual(sa.semantic_ratio(1, 11), 0.1)                 # 1/(11-1)=10% → 恰过线(>=)
        self.assertLess(sa.semantic_ratio(1, 12), 0.10)                 # 1/11≈9.1% → 触发

    def test_zero_division_guards(self):
        self.assertEqual(sa.semantic_ratio(5, 5), 1.0)                  # 全语义 → 1.0
        self.assertEqual(sa.semantic_ratio(0, 0), 0.0)                  # 空页 → 0.0

    def test_semantic_tag_set_matches_spec(self):
        for t in ("header", "nav", "main", "article", "section", "aside", "footer",
                  "h1", "h2", "h3", "h4", "h5", "h6", "figure", "time", "mark", "details"):
            self.assertIn(t, sa.SEMANTIC_TAGS)


class HealthScoreAggregationTests(unittest.TestCase):
    """子分聚合:通过率加权 bots 0.4/其余各 0.15;bluf 只记录不计分。"""

    @staticmethod
    def checks(**over):
        base = {"bots": True, "llms_txt": True, "freshness": True,
                "semantic_html": True, "content_length": True, "bluf": True}
        base.update(over)
        return [{"id": k, "pass": v, "detail": ""} for k, v in base.items()]

    def test_weights_sum_to_one_and_cover_five_checks(self):
        self.assertAlmostEqual(sum(sa.AI_HEALTH_WEIGHTS.values()), 1.0)
        self.assertEqual(set(sa.AI_HEALTH_WEIGHTS),
                         {"bots", "llms_txt", "freshness", "semantic_html", "content_length"})

    def test_all_pass_100(self):
        self.assertEqual(sa.ai_health_score(self.checks()), 100)

    def test_bots_fail_costs_40(self):
        self.assertEqual(sa.ai_health_score(self.checks(bots=False)), 60)

    def test_two_minor_fail_costs_30(self):
        self.assertEqual(sa.ai_health_score(self.checks(llms_txt=False, freshness=False)), 70)

    def test_bluf_has_no_weight(self):
        self.assertEqual(sa.ai_health_score(self.checks(bluf=False)), 100)


class FreshnessTests(unittest.TestCase):
    """Last-Modified:响应头优先 → meta http-equiv 回退 → 无则 None(跳过)。"""

    def test_header_days_and_meta_fallback(self):
        d = sa.last_modified_days({"Last-Modified": httpdate(200)}, None)
        self.assertGreater(d, 195)                                      # 头口径
        d2 = sa.last_modified_days({}, httpdate(200))
        self.assertGreater(d2, 195)                                     # meta 回退同值量级
        self.assertIsNone(sa.last_modified_days({}, None))              # 双缺失 → 跳过

    def test_header_wins_over_meta(self):
        d = sa.last_modified_days({"Last-Modified": httpdate(5)}, httpdate(400))
        self.assertLess(d, 30)

    def test_garbage_value_skipped(self):
        self.assertIsNone(sa.last_modified_days({"Last-Modified": "yesterday-ish"}, None))

    def test_header_lookup_case_insensitive(self):
        self.assertEqual(sa.get_header({"LAST-MODIFIED": "x"}, "last-modified"), "x")
        self.assertIsNone(sa.get_header({"Content-Type": "text/html"}, "last-modified"))

    def test_meta_http_equiv_captured_by_parser(self):
        p = page_of('<head><meta http-equiv="Last-Modified" content="' + httpdate(300) + '"></head>')
        self.assertIsNotNone(p.meta_last_modified)
        self.assertGreater(sa.last_modified_days({}, p.meta_last_modified), 295)


if __name__ == "__main__":
    unittest.main(verbosity=1)
