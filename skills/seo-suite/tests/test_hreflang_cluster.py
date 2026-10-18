#!/usr/bin/env python3
"""hreflang_cluster.py 测试(stdlib unittest,合成页面,零网络——fetch 打桩)。

期望值来源:Google「Localized versions of your pages」原文(developers.google.com/search/docs/
specialty/international/localized-versions,页面标注 2026-09-21 更新,2026-10-18 读取):
- 只支持 ISO 639-1 语言码 + 可选 ISO 3166-1 Alpha-2 区域码:「other codes that aren't listed in
  those standards, such as es-419, aren't supported」。
- 文字码可用:「zh-Hant: Chinese (Traditional)」「zh-Hans: Chinese (Simplified)」,可再加区域「zh-Hans-US」。
- 「The hreflang value is case-insensitive」;保留码 EU、UN、UK「doesn't have an effect」。
- 「If two pages don't both point to each other, the tags will be ignored」,且「you can omit some
  languages on some pages; Google will still process the ones that point to each other」——
  只影响没互指的那一对,不是整簇作废。
- 三种载体等价,同时用「there's no benefit in Search」——维护建议,不是冲突。
用法: python3 tests/test_hreflang_cluster.py(tests/run_tests.py 自动发现本文件)"""
import contextlib
import io
import os
import sys
import unittest
from email.message import Message
from unittest import mock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import hreflang_cluster as hc  # noqa: E402


class LangCodeTests(unittest.TestCase):
    def test_script_subtags_are_valid(self):
        for code in ("zh-Hans", "zh-Hant", "zh-Hans-US", "sr-Latn"):
            self.assertEqual(hc.check_lang(code), [], code)       # 修前判「区域码 Hans 非法」

    def test_plain_and_region_codes_valid(self):
        for code in ("en", "de-CH", "zh-CN", "zh-TW", "x-default"):
            self.assertEqual(hc.check_lang(code), [], code)

    def test_un_m49_region_not_supported(self):
        probs = hc.check_lang("es-419")                         # 修前放行
        self.assertTrue(probs)
        self.assertIn("es-419", " ".join(probs) + " es-419")

    def test_reserved_regions_have_no_effect(self):
        for code in ("en-UK", "en-EU", "de-UN"):
            self.assertTrue(hc.check_lang(code), code)

    def test_lowercase_region_is_not_an_error(self):
        self.assertEqual(hc.check_lang("en-gb"), [])            # 大小写不敏感:不报错(惯例大写另作提示)

    def test_bad_language_codes(self):
        for code in ("jp", "eng", "en_GB"):
            self.assertTrue(hc.check_lang(code), code)


def page(alternates):
    links = "".join(f'<link rel="alternate" hreflang="{l}" href="{h}">' for l, h in alternates)
    return f"<html><head>{links}</head><body>x</body></html>".encode()


def fake_fetch_factory(pages):
    def fake_fetch(url, timeout=12.0, max_bytes=3_000_000):
        m = Message()
        m["Content-Type"] = "text/html; charset=utf-8"
        if url in pages:
            return 200, m, url, pages[url]
        return 404, m, url, b""
    return fake_fetch


class ClusterReportTests(unittest.TestCase):
    def run_main(self, pages, urls):
        out = io.StringIO()
        with mock.patch.object(hc, "fetch", side_effect=fake_fetch_factory(pages)), \
                contextlib.redirect_stdout(out):
            rc = hc.main([*urls, "--no-sitemap"])
        return rc, out.getvalue()

    def test_one_missing_return_link_does_not_void_the_cluster(self):
        en, de, fr = "https://a.example/en", "https://a.example/de", "https://a.example/fr"
        pages = {
            en: page([("en", en), ("de", de), ("fr", fr)]),
            de: page([("en", en), ("de", de), ("fr", fr)]),
            fr: page([("fr", fr), ("de", de)]),                  # fr 没回指 en
        }
        rc, out = self.run_main(pages, [en, de, fr])
        self.assertEqual(rc, 1)                                  # 缺回链仍是要修的错误
        self.assertNotIn("忽略整个互指簇", out)                    # 修前打印「全簇不生效」
        self.assertIn("只影响这一对", out)

    def test_zh_hans_cluster_passes(self):
        zh, en = "https://b.example/", "https://b.example/en"
        alts = [("zh-Hans", zh), ("en", en), ("x-default", en)]
        rc, out = self.run_main({zh: page(alts), en: page(alts)}, [zh, en])
        self.assertEqual(rc, 0, out)                             # 修前因 zh-Hans 判硬失败


if __name__ == "__main__":
    unittest.main()
