#!/usr/bin/env python3
"""above_fold.py 首屏取样回归测试(B31;合成页面,fetch 打桩,零网络)。

期望值来源:bug 卡 B31——/en 首页按 DOM 顺序取前 700 字符,取到的是导航下拉菜单文字;
首屏取样要跳过 nav/header 菜单、role=navigation、aria-hidden 的下拉和 Cookie/同意横幅。
页面结构按 Next.js 站点常见写法合成(header>nav 带 mega-menu、aria-hidden 下拉、
OneTrust/通用 cookie 横幅、main>h1 首屏)。
"""
import contextlib
import io
import os
import sys
import unittest
from unittest import mock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import above_fold as af  # noqa: E402

MENU = " ".join("Menu item %d data catalog" % i for i in range(60))
PAGE = (
    '<html><body>'
    '<div id="onetrust-banner-sdk" class="cookie-banner"><p>We use cookies to improve your experience. '
    'Accept all cookies or manage preferences.</p><button>Accept</button></div>'
    '<header class="site-header"><a href="/">ExampleAPI</a>'
    '<nav aria-label="Main"><ul><li><h3>Products</h3><a href="/p">' + MENU + '</a></li></ul></nav>'
    '<div aria-hidden="true" class="dropdown"><a href="/x">Hidden dropdown entry about pricing tiers</a></div>'
    '<div role="navigation"><a href="/docs">Docs Blog Changelog Status</a></div>'
    '</header>'
    '<main><h1>Scrape 50 platforms with one API</h1>'
    '<p>Get structured data from 50 platforms in under 2 seconds. Failed calls are not charged.</p>'
    '<a href="/signup">Start free</a></main>'
    '</body></html>')


def run(html):
    out = io.StringIO()
    with mock.patch.object(af, "fetch", lambda url, timeout=15.0: (200, url, html.encode())):
        with contextlib.redirect_stdout(out):
            rc = af.main(["https://example.com/en"])
    return rc, out.getvalue()


class FoldSamplingTests(unittest.TestCase):
    def test_preview_starts_at_main_content(self):
        rc, out = run(PAGE)
        preview = next(ln for ln in out.splitlines() if ln.startswith("首屏文本预览"))
        self.assertIn("Scrape 50 platforms", preview)                      # 修前是菜单文字
        for junk in ("Menu item", "cookies", "Hidden dropdown", "Docs Blog"):
            self.assertNotIn(junk, preview)

    def test_headline_is_h1_not_menu_heading(self):
        rc, out = run(PAGE)
        self.assertIn('首个标题(h1): "Scrape 50 platforms', out)          # 修前取 nav 里的 h3 Products

    def test_page_without_chrome_unchanged(self):
        html = ('<html><body><h1>Plain heading 2026</h1><p>Body text with 30 items.</p>'
                '<a href="/go">Get started</a></body></html>')
        rc, out = run(html)
        self.assertIn("Plain heading 2026", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
