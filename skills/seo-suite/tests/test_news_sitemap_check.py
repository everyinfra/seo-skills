#!/usr/bin/env python3
"""news_sitemap_check.py 回归(discover-news-seo.md 四连 curl 脚本化+扩展;stdlib
unittest,合成 XML 打桩,零网络,standalone——被 run_tests.py 按 test_*.py 自动发现
加载)。口径钉死脚本自身契约:48h 窗口协议红线(超龄逐条列)/ 必填三件套 /
200 直返(3xx→FAIL、非 200→rc2)/ noindex 抽查 / 存在率与混入 / publication name
一致性(--pub-name)/ 时间戳精度 / title ≥100 字符与站名逆序 / loc 绝对 URL /
robots Sitemap 声明 / sitemapindex rc2。时间不打桩:新鲜度用 now±Δ 构造。
网络打桩:模块级 http_fetch() 单点(URL→(status,headers,body) 映射+默认兜底)。"""
import contextlib
import io
import json
import os
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import news_sitemap_check as ns  # noqa: E402

SMAP = "https://example.com/news-sitemap.xml"
ROBOTS = "https://example.com/robots.txt"
CLEAN_PAGE = b"<html><head><title>a</title></head><body>article</body></html>"


def run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = ns.main(argv)
        except SystemExit as e:
            rc = e.code
    return rc, out.getvalue(), err.getvalue()


def iso(hours_ago):
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def entry(loc, title="Something happened today", name="Example News", lang="en",
          date=None, news=True):
    return dict(loc=loc, title=title, name=name, lang=lang,
                date=date if date is not None else iso(2), news=news)


def news_xml(entries):
    urls = []
    for e in entries:
        if not e["news"]:
            urls.append("<url><loc>%s</loc><lastmod>%s</lastmod></url>"
                        % (e["loc"], e["date"]))
            continue
        urls.append(
            "<url><loc>%s</loc><lastmod>%s</lastmod>"
            "<news:news><news:publication><news:name>%s</news:name>"
            "<news:language>%s</news:language></news:publication>"
            "<news:publication_date>%s</news:publication_date>"
            "<news:title>%s</news:title></news:news></url>"
            % (e["loc"], e["date"], e["name"], e["lang"], e["date"], e["title"]))
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">'
            + "".join(urls) + "</urlset>").encode("utf-8")


class NewsSitemapCase(unittest.TestCase):
    """公共:http_fetch 按 URL 映射打桩;未登记 URL 走默认 200 干净页。"""

    def stub(self, mapping, default=(200, {}, CLEAN_PAGE)):
        orig = ns.http_fetch

        def fake(url, timeout=ns.FETCH_TIMEOUT, max_bytes=10 ** 9):
            if url in mapping:
                st, hd, body = mapping[url]
                return st, hd, body if isinstance(body, bytes) else body.encode()
            return default[0], default[1], default[2]

        ns.http_fetch = fake
        self.addCleanup(setattr, ns, "http_fetch", orig)

    def run_sitemap(self, entries, *extra, mapping=None, default=None):
        mp = {SMAP: (200, {}, news_xml(entries))}
        if mapping:
            mp.update(mapping)
        if default is not None:
            self.stub(mp, default=default)
        else:
            self.stub(mp)
        return run_cli(["--url", SMAP, *extra])


class CoreTests(NewsSitemapCase):
    def test_help_smoke(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "news_sitemap_check.py"),
                            "--help"], capture_output=True, text=True, encoding="utf-8",
                           env=env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("48h", r.stdout)

    def test_all_fresh_pass(self):
        ents = [entry("https://example.com/news/a"), entry("https://example.com/news/b")]
        rc, out, _ = self.run_sitemap(
            ents, mapping={ROBOTS: (200, {}, b"User-agent: *\nAllow: /\n"
                                             b"Sitemap: https://example.com/news-sitemap.xml\n")})
        self.assertEqual(rc, 0, out)
        self.assertIn("全部 ≤48h", out)
        self.assertIn("存在率 100%", out)
        self.assertIn("三件套", out)
        self.assertIn("已声明本 sitemap", out)
        self.assertIn("PASS(退出码 0)", out)

    def test_stale_entries_listed_per_url(self):
        ents = [entry("https://example.com/news/fresh", date=iso(2)),
                entry("https://example.com/news/stale", date=iso(49)),
                entry("https://example.com/news/older", date=iso(72))]
        rc, out, _ = self.run_sitemap(ents)
        self.assertEqual(rc, 1, out)
        self.assertIn("协议红线:超 48h/不可解析 2 条", out)
        self.assertIn("news/stale", out)                        # 超龄逐条列出
        self.assertIn("news/older", out)
        self.assertNotIn("news/fresh(4", out)                   # 新鲜条不进超龄清单

    def test_unparseable_date_is_stale(self):
        ents = [entry("https://example.com/news/x", date="not-a-date")]
        rc, out, _ = self.run_sitemap(ents)
        self.assertEqual(rc, 1, out)
        self.assertIn("不可解析", out)

    def test_window_uses_publication_date_over_lastmod(self):
        """lastmod 新但 publication_date 超龄——按协议字段判(红线是 publication_date)。"""
        e = entry("https://example.com/news/y", date=iso(50))
        rc, out, _ = self.run_sitemap([e])
        self.assertEqual(rc, 1, out)
        self.assertIn("50.0h 前", out)


class StructureTests(NewsSitemapCase):
    def test_news_tag_ratio_and_mixed_urls(self):
        ents = [entry("https://example.com/news/%d" % i) for i in range(3)]
        ents += [dict(loc="https://example.com/about", date=iso(1), news=False),
                 dict(loc="https://example.com/contact", date=iso(1), news=False)]
        rc, out, _ = self.run_sitemap(ents)
        self.assertIn("存在率 60.0%(3/5)", out)
        self.assertIn("混入非新闻 URL 2 条", out)
        self.assertIn("/about", out)
        self.assertIn("⚠", out)

    def test_zero_news_tags_is_not_news_sitemap(self):
        ents = [dict(loc="https://example.com/a", date=iso(1), news=False) for _ in range(3)]
        rc, out, _ = self.run_sitemap(ents)
        self.assertEqual(rc, 1, out)
        self.assertIn("0/3 条含 <news:news>", out)
        self.assertIn("不是 news sitemap", out)

    def test_required_trio_missing_listed(self):
        ents = [entry("https://example.com/news/t1", title="", lang=""),
                entry("https://example.com/news/t2")]
        rc, out, _ = self.run_sitemap(ents)
        self.assertEqual(rc, 1, out)
        self.assertIn("必填三件套不全", out)
        self.assertIn("publication.language+title", out)        # 缺项点名

    def test_relative_loc_fail(self):
        ents = [entry("/news/relative")]
        rc, out, _ = self.run_sitemap(ents)
        self.assertEqual(rc, 1, out)
        self.assertIn("loc 非绝对 http(s) URL", out)


class FormatTests(NewsSitemapCase):
    def test_pubname_inconsistent_and_flag_compare(self):
        ents = [entry("https://example.com/news/a", name="Example News"),
                entry("https://example.com/news/b", name="Other News")]
        rc, out, _ = self.run_sitemap(ents)
        self.assertIn("站内不一致 2 个名", out)
        self.assertIn("Other News", out)
        rc2, out2, _ = self.run_sitemap(ents, "--pub-name", "Example News")
        self.assertIn("不匹配: Other News", out2)               # 与站名比对逐条点名

    def test_date_only_precision_warn(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        ents = [entry("https://example.com/news/d", date=today)]
        rc, out, _ = self.run_sitemap(ents)
        self.assertEqual(rc, 0, out)                            # 当日 00:00 仍在 48h 内
        self.assertIn("只有日期无时间/时区", out)

    def test_long_title_and_site_name_suffix_warn(self):
        long_t = "突发快讯" * 30                                 # 120 字符 ≥100
        ents = [entry("https://example.com/news/long", title=long_t),
                entry("https://example.com/news/rev",
                      title="Example News - Big Story Unfolds Here")]
        rc, out, _ = self.run_sitemap(ents)
        self.assertIn("1 条 title ≥100 字符", out)
        self.assertIn("逆序格式", out)                          # 站名前缀/后缀都算


class TransportTests(NewsSitemapCase):
    def test_redirect_fails(self):
        self.stub({SMAP: (301, {"Location": "https://example.com/news-sitemap.xml/"},
                          b"<html>moved</html>")})
        rc, out, _ = run_cli(["--url", SMAP])
        self.assertEqual(rc, 1, out)
        self.assertIn("301 重定向", out)
        self.assertIn("Yoast 错误 #3", out)

    def test_non_200_fatal_rc2(self):
        self.stub({SMAP: (404, {}, b"not found")})
        rc, _, err = run_cli(["--url", SMAP])
        self.assertEqual(rc, 2)
        self.assertIn("HTTP 404", err)

    def test_sitemapindex_rejected_rc2(self):
        body = (b'<?xml version="1.0"?><sitemapindex '
                b'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                b"<sitemap><loc>https://example.com/news-sitemap-1.xml</loc></sitemap>"
                b"</sitemapindex>")
        self.stub({SMAP: (200, {}, body)})
        rc, _, err = run_cli(["--url", SMAP])
        self.assertEqual(rc, 2)
        self.assertIn("sitemapindex", err)

    def test_count_soft_limit_warn(self):
        ents = [entry("https://example.com/news/n%d" % i, title="T%d" % i)
                for i in range(1001)]
        rc, out, _ = self.run_sitemap(ents)
        self.assertEqual(rc, 0, out)
        self.assertIn("1001 条 > 1000 最佳实践", out)
        self.assertIn("窗口滚动逻辑坏了", out)


class RobotsAndSampleTests(NewsSitemapCase):
    def test_robots_undeclared_warn(self):
        ents = [entry("https://example.com/news/a")]
        rc, out, _ = self.run_sitemap(
            ents, mapping={ROBOTS: (200, {}, b"User-agent: *\nAllow: /\n")})
        self.assertEqual(rc, 0, out)
        self.assertIn("均不含本 sitemap", out)

    def test_robots_fetch_failure_unverified(self):
        def boom(url, timeout=ns.FETCH_TIMEOUT, max_bytes=10 ** 9):
            if url == ROBOTS:
                raise OSError("no route")
            return (200, {}, news_xml([entry("https://example.com/news/a")])
                    if url == SMAP else CLEAN_PAGE)
        orig = ns.http_fetch
        ns.http_fetch = boom
        self.addCleanup(setattr, ns, "http_fetch", orig)
        rc, out, _ = run_cli(["--url", SMAP])
        self.assertEqual(rc, 0, out)
        self.assertIn("robots.txt 拉取失败", out)

    def test_sample_noindex_fail(self):
        noindex_page = (b"<html><head><meta name=\"robots\" content=\"noindex,nofollow\">"
                        b"</head><body>x</body></html>")
        ents = [entry("https://example.com/news/bad"),
                entry("https://example.com/news/good")]
        rc, out, _ = self.run_sitemap(
            ents, "--sample", "2",
            mapping={"https://example.com/news/bad": (200, {}, noindex_page)})
        self.assertEqual(rc, 1, out)
        self.assertIn("noindex(错误清单 #2)", out)
        self.assertIn("news/bad", out)

    def test_sample_zero_disables(self):
        ents = [entry("https://example.com/news/a")]
        rc, out, _ = self.run_sitemap(ents, "--sample", "0")
        self.assertEqual(rc, 0, out)
        self.assertIn("--sample 0 已关闭抽查", out)


class JsonTests(NewsSitemapCase):
    def test_json_output_shape(self):
        ents = [entry("https://example.com/news/a", date=iso(50))]
        out_io, err_io = io.StringIO(), io.StringIO()
        mp = {SMAP: (200, {}, news_xml(ents))}
        self.stub(mp)
        with contextlib.redirect_stdout(out_io), contextlib.redirect_stderr(err_io):
            rc = ns.main(["--url", SMAP, "--json"])
        self.assertEqual(rc, 1)
        data = json.loads(out_io.getvalue())
        self.assertEqual(data["tool"], "news_sitemap_check")
        self.assertEqual(data["entries"], 1)
        window = next(i for i in data["items"] if i["id"] == "window.48h")
        self.assertEqual(window["status"], "fail")
        self.assertIn("news/a", window["detail"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
