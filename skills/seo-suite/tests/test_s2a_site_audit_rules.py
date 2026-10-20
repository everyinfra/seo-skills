#!/usr/bin/env python3
"""S2a 回归:site_audit.py 的判定口径(B3/B4/B11/B12/B13/B14/B15/B38)。

期望值来源(一手规范原文,读取日期 2026-10-21):
- B15 description 缺失不是 CRITICAL:Google「How to Write Meta Descriptions」
  https://developers.google.com/search/docs/appearance/snippet ——
  "Google primarily uses the content on the page to automatically determine the appropriate snippet";
  "There's no limit on how long a meta description can be"。
- B38 H1 缺失不是 CRITICAL:Google SEO Starter Guide「Number and order of headings」——
  "from Google Search perspective, it doesn't matter if you're using them out of order …
  There's also no magical, ideal amount of headings"。
  相对 canonical 不是 CRITICAL:https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls ——
  "Even though relative paths are supported by Google, they can cause problems in the long run …
  we don't recommend them";Bad example: `/dresses/green/green-dress.html`(根相对路径也算相对)。
- B12 标题长度:https://developers.google.com/search/docs/appearance/title-link ——
  "there's no limit on how long a <title> element can be … truncated … to fit the device width"
  (按显示宽度截断,不是按字符数)→ 中文市场按显示宽度计(全角 2、半角 1,上限等价 60)。
- B13 description 下限必须小于上限(否则没有任何长度能通过,结构性矛盾)。
- B14 >100 链接:现行 Google 文档无此数(SEO Starter Guide 链接一节无数量限制)→ INFO 并标「工具约定」。
- B11 挑战页结构特征:Cloudflare 文档 —— Challenge Page 是拦在目标页前的整页
  (https://developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/);
  JavaScript Detections 会在**每个** HTML 页注入 `/cdn-cgi/challenge-platform/…` 脚本
  (https://developers.cloudflare.com/cloudflare-challenges/challenge-types/javascript-detections/)
  → 单凭该脚本不能判挑战页;页面正文谈论 CAPTCHA 也不能判。
- B4 `--json`:--help 契约「结构化输出(findings+meta+verdict+ai_search_health,供 agent 消费)」
  → stdout 必须能被 json.loads 整体解析。
- B3 rendering:已检测到服务端内容(纯文本>500 且有 main/article/section,脚本自身口径)时,
  无 JS 客户端不会拿到空页;JS 只提示体积。
合成页面全部为 example.com / *.test 域,零网络。"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import site_audit as sa  # noqa: E402

ROOT = "https://example.com"
ROOT_FILES = {
    "/robots.txt": (200, {}, "User-agent: *\nAllow: /\n"),
    "/sitemap.xml": (200, {}, "<urlset/>"),
    "/llms.txt": (200, {}, "# llms\n"),
}


def stub_fetch(pages):
    table = {ROOT + p: v for p, v in {**ROOT_FILES, **pages}.items()}

    def _fetch(url, timeout=15):
        if url in table:
            return table[url]
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
    return _fetch


def html(title="Example Data API: Pricing, Docs and Limits Explained",
         desc="Example Data API returns structured records over HTTPS. Read the pricing, "
              "rate limits and quickstart before you call it.",
         canonical="https://example.com/page", h1="Example Data API", lang="en",
         body_words=400, extra_head="", extra_body="", main=True):
    head = ["<title>%s</title>" % title if title is not None else ""]
    if desc is not None:
        head.append('<meta name="description" content="%s">' % desc)
    if canonical is not None:
        head.append('<link rel="canonical" href="%s">' % canonical)
    head.append('<meta property="og:title" content="t"><meta property="og:description" content="d">'
                '<meta property="og:image" content="https://example.com/i.png">'
                '<script type="application/ld+json">{"@context":"https://schema.org"}</script>')
    head.append(extra_head)
    wrap_o, wrap_c = ("<main><article>", "</article></main>") if main else ("<div>", "</div>")
    return ('<!doctype html><html lang="%s"><head>%s</head><body>%s%s'
            '<p>In short, the answer comes first. %s</p><h2>One</h2><h2>Two</h2>'
            '<ul><li>a</li><li>b</li><li>c</li><li>d</li></ul>%s%s</body></html>'
            % (lang, "".join(head), wrap_o, ("<h1>%s</h1>" % h1) if h1 else "",
               "record field value " * (body_words // 3), extra_body, wrap_c))


def audit(page_html, market="en", path="/page", status=200):
    orig = sa.fetch
    sa.fetch = stub_fetch({path: (status, {}, page_html)})
    try:
        return sa.audit(ROOT + path, market)
    finally:
        sa.fetch = orig


def findings(page_html, market="en"):
    return audit(page_html, market)[0]


def by_area(F, area):
    return [(s, m) for s, a, m in F if a == area]


# ---------------------------------------------------------------- B11 挑战页守卫
class ChallengeGuardTests(unittest.TestCase):

    def test_page_about_captcha_is_audited(self):
        """页面谈论 CAPTCHA(描述、标题、正文)不是挑战页 → 正常审计,不出 SKIP。"""
        p = html(title="CAPTCHA Solving API: Pricing and Docs",
                 desc="Solve reCAPTCHA, hCaptcha and Cloudflare Turnstile with one API call. "
                      "Access denied responses are retried. Pay only for solved captcha tasks.",
                 extra_body="<p>Verify you are human prompts and unusual traffic pages are "
                            "explained here.</p>")
        F = findings(p)
        self.assertFalse([f for f in F if f[0] == "SKIP"], F)

    def test_long_page_with_js_detection_script_is_audited(self):
        """Cloudflare JS Detections 在每个 HTML 页注入 /cdn-cgi/challenge-platform/ 脚本;
        正常长页面带这个脚本不能拒审。"""
        p = html(extra_head='<script src="/cdn-cgi/challenge-platform/scripts/jsd/main.js" defer></script>')
        F = findings(p)
        self.assertFalse([f for f in F if f[0] == "SKIP"], F)

    def test_cloudflare_interstitial_is_refused(self):
        """结构特征:标题 "Just a moment..." + challenge-platform 脚本 + 正文极短 → 拒审。"""
        p = ('<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title>'
             '<meta http-equiv="refresh" content="390"></head><body>'
             '<div class="main-wrapper" role="main"><div class="main-content">'
             '<h1 class="zone-name-title h1">example.com</h1>'
             '<noscript><div class="h2">Enable JavaScript and cookies to continue</div></noscript>'
             '</div></div><script>(function(){window._cf_chl_opt={cvId: "3"};'
             'var a=document.createElement("script");'
             'a.src="/cdn-cgi/challenge-platform/h/b/orchestrate/chl_page/v1?ray=abc";'
             'document.getElementsByTagName("head")[0].appendChild(a);}());</script>'
             + " " * 400 + '</body></html>')
        F = findings(p)
        self.assertEqual([f[0] for f in F], ["SKIP"], F)

    def test_short_access_denied_page_is_refused(self):
        """正文极短 + 拦截措辞(CDN 拒绝页形态)→ 拒审。"""
        p = ('<HTML><HEAD><TITLE>Access Denied</TITLE></HEAD><BODY><H1>Access Denied</H1>'
             'You don\'t have permission to access "http://example.com/page" on this server.'
             '<P>Reference #18.6f2d3e17.1729500000.1a2b3c4d</BODY></HTML>' + " " * 300)
        F = findings(p)
        self.assertEqual([f[0] for f in F], ["SKIP"], F)


# ---------------------------------------------------------------- B15 / B38 严重度
class SeverityTests(unittest.TestCase):

    def test_missing_description_is_warn(self):
        F = findings(html(desc=None))
        self.assertEqual(by_area(F, "description"), [("WARN", "缺失")])

    def test_missing_h1_is_warn(self):
        F = findings(html(h1=None))
        self.assertEqual([s for s, _ in by_area(F, "h1")], ["WARN"])

    def test_relative_canonical_is_warn_with_absolute_hint(self):
        for href in ("page", "/page"):          # 文档 Bad example 即根相对路径
            with self.subTest(href=href):
                F = findings(html(canonical=href))
                rel = [(s, m) for s, m in by_area(F, "canonical") if "相对" in m]
                self.assertEqual(len(rel), 1, F)
                self.assertEqual(rel[0][0], "WARN")
                self.assertIn("绝对", rel[0][1])

    def test_absolute_canonical_not_flagged(self):
        F = findings(html(canonical="https://example.com/page"))
        self.assertFalse([m for _, m in by_area(F, "canonical") if "相对" in m], F)

    def test_page_with_only_these_gaps_exits_zero(self):
        """缺 description + 缺 H1 + 相对 canonical:都不是 CRITICAL → 退出码 0。"""
        orig, argv = sa.fetch, sys.argv
        sa.fetch = stub_fetch({"/page": (200, {}, html(desc=None, h1=None, canonical="/page"))})
        sys.argv = ["site_audit.py", ROOT + "/page"]
        rc = 0
        try:
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                try:
                    sa.main()
                except SystemExit as e:
                    rc = e.code or 0
        finally:
            sa.fetch, sys.argv = orig, argv
        self.assertEqual(rc, 0)


# ---------------------------------------------------------------- B14 链接数
class LinkCountTests(unittest.TestCase):

    def test_over_100_links_is_info_tool_convention(self):
        links = "".join('<a href="/p%d">p%d</a>' % (i, i) for i in range(150))
        F = findings(html(extra_body=links))
        got = by_area(F, "links")
        self.assertEqual(len(got), 1, F)
        self.assertEqual(got[0][0], "INFO")
        self.assertIn("工具约定", got[0][1])


# ---------------------------------------------------------------- B12 中文标题显示宽度
class ZhTitleWidthTests(unittest.TestCase):

    def test_mixed_latin_cjk_title_within_width(self):
        """拉丁 29 字符(宽 29)+ 汉字 8 个(宽 16)= 显示宽度 45 ≤ 60;按码点数是 37 > 30。"""
        t = "ExampleCloud Social Data API 社交数据接口文档"
        F = findings(html(title=t, desc="示例云社交数据接口返回结构化记录。" * 3, lang="zh"), "zh")
        self.assertFalse([m for _, m in by_area(F, "title") if "超上限" in m], F)

    def test_pure_cjk_title_over_width_flagged(self):
        """31 个汉字 = 显示宽度 62 > 60 → 仍报超上限。"""
        F = findings(html(title="数" * 31, desc="示例云社交数据接口返回结构化记录。" * 3, lang="zh"), "zh")
        self.assertTrue([m for _, m in by_area(F, "title") if "超上限" in m], F)


# ---------------------------------------------------------------- B13 description 下限
class DescMinTests(unittest.TestCase):

    def test_every_market_min_below_limit(self):
        with open(os.path.join(SCRIPTS, "markets.json"), encoding="utf-8") as f:
            ms = json.load(f)["markets"]
        for code in ms:
            with self.subTest(market=code):
                mk = sa.load_market(code)
                lo, hi = sa.desc_bounds(mk)
                self.assertLess(lo, hi)
                self.assertGreater(lo, 0)

    def test_zh_mid_length_description_passes(self):
        """60 个汉字的描述:zh 上限 78,任何口径下都应可通过(修复前 <80 必报)。"""
        F = findings(html(title="示例数据接口价格与文档", desc="数" * 60, lang="zh"), "zh")
        self.assertEqual(by_area(F, "description"), [], F)

    def test_ko_mid_length_description_passes(self):
        F = findings(html(title="예시 데이터 API 가격과 문서 안내", desc="가" * 60, lang="ko"), "ko")
        self.assertEqual(by_area(F, "description"), [], F)

    def test_short_description_reports_market_min(self):
        F = findings(html(desc="Short text."))
        got = by_area(F, "description")
        self.assertEqual(len(got), 1)
        lo, _ = sa.desc_bounds(sa.load_market("en"))
        self.assertIn(str(lo), got[0][1])
        self.assertEqual(sa.rule_slug("description", got[0][1]), "description-too-short")


# ---------------------------------------------------------------- B3 rendering
class RenderingTests(unittest.TestCase):

    def test_server_rendered_page_no_empty_page_or_ssr_advice(self):
        scripts = "".join('<script src="/_next/static/chunks/%d.js"></script>' % i for i in range(20))
        F = findings(html(body_words=3000, extra_head=scripts))
        r = by_area(F, "rendering")
        self.assertFalse([m for _, m in r if "空页" in m], r)
        self.assertFalse([m for _, m in r if "服务端渲染" in m and "无需" not in m], r)
        js = [(s, m) for s, m in r if "JS 重量" in m]
        self.assertEqual(len(js), 1, r)
        self.assertEqual(js[0][0], "INFO")                 # 只提示体积

    def test_csr_shell_still_warned(self):
        p = ('<!doctype html><html lang="en"><head><title>App Shell Page For Tests</title>'
             '<meta name="description" content="x"></head><body><div id="root"></div>'
             + "".join('<script src="/s%d.js"></script>' % i for i in range(20))
             + "<!-- " + "pad " * 100 + "--></body></html>")
        F = findings(p)
        r = by_area(F, "rendering")
        self.assertTrue([1 for s, m in r if s == "WARN" and "CSR" in m], r)
        self.assertTrue([1 for s, m in r if s == "WARN" and "JS 重量" in m], r)


# ---------------------------------------------------------------- B4 --json stdout 纯 JSON
class JsonStdoutTests(unittest.TestCase):

    def run_main(self, argv, pages):
        orig, old_argv = sa.fetch, sys.argv
        sa.fetch = stub_fetch(pages)
        sys.argv = ["site_audit.py", *argv]
        out, err = io.StringIO(), io.StringIO()
        rc = 0
        try:
            with redirect_stdout(out), redirect_stderr(err):
                try:
                    sa.main()
                except SystemExit as e:
                    rc = e.code or 0
        finally:
            sa.fetch, sys.argv = orig, old_argv
        return out.getvalue(), err.getvalue(), rc

    def test_stdout_is_only_json(self):
        out, err, _ = self.run_main([ROOT + "/a", ROOT + "/b", "--json", "--market", "zh"],
                                    {"/a": (200, {}, html()), "/b": (200, {}, html(desc=None))})
        payload = json.loads(out)                          # 整体可解析(jq 同口径)
        self.assertEqual(set(payload["results"]), {ROOT + "/a", ROOT + "/b"})
        self.assertEqual(payload["market"], "zh")
        self.assertIn("== %s/a ==" % ROOT, err)            # 人读行仍在,改走 stderr

    def test_downstream_consumers_read_pure_json(self):
        """全部读 audit.json 的下游脚本对纯 JSON 输入可用(project.py 把 stdout 存成 audit.json)。"""
        out, _, _ = self.run_main([ROOT + "/a", "--json"], {"/a": (200, {}, html(desc=None))})
        d = tempfile.mkdtemp(prefix="s2a_json_")
        path = os.path.join(d, "audit.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        env = dict(os.environ, PYTHONIOENCODING="utf-8")

        def run(name, *args):
            return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                                  capture_output=True, text=True, encoding="utf-8", env=env)
        cases = [
            ("health_score.py", ["--input", path, "--json"], (0, 1)),
            ("prioritize.py", ["--audit", path, "--json"], (0,)),
            ("envelope.py", ["--audit", path, "--json"], (0,)),
            ("ci_format.py", [path, "--format", "json"], (0, 1)),
            ("audit_compare.py", ["--old", path, "--new", path, "--json"], (0, 1)),
            ("fix_plan.py", ["--audit", path], (0, 1)),
            ("traffic_funnel.py", ["--audit", path, "--json"], (0, 1)),
        ]
        for name, args, ok in cases:
            with self.subTest(script=name):
                r = run(name, *args)
                self.assertIn(r.returncode, ok, r.stderr[-800:])
        audits = os.path.join(d, "audits")
        os.makedirs(audits)
        with open(os.path.join(audits, "a.json"), "w", encoding="utf-8") as f:
            f.write(out)
        r = run("benchmark_report.py", "--audits", audits, "--json")
        self.assertNotIn("解析不出", r.stderr)


if __name__ == "__main__":
    unittest.main()
