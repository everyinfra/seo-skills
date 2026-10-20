#!/usr/bin/env python3
"""site_audit 把 alt="" 当成 alt 缺失(B63,2026-10-21 在真实站点重跑时发现:首页 357 张装饰图都写了 alt="")。

期望值来源:W3C WAI 图片教程「Decorative Images」——装饰图应提供空 alt(alt=""),
让读屏软件跳过(https://www.w3.org/WAI/tutorials/images/decorative/);HTML 规范同样把空 alt
定义为「图片不是内容的一部分」。所以只有完全没有 alt 属性的 <img> 才算缺失。
用法: python3 tests/test_b63_alt_empty.py(tests/run_tests.py 自动发现本文件)"""
import os
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

import site_audit as sa  # noqa: E402


def parse(html):
    p = sa.Page()
    p.feed(html)
    return p


class AltEmptyIsNotMissing(unittest.TestCase):
    def test_empty_alt_not_counted_missing(self):
        p = parse('<html><body><img src="a.webp" alt=""><img src="b.webp" alt="">'
                  '<img src="c.webp" alt="产品截图"><img src="d.webp"></body></html>')
        self.assertEqual(p.imgs, 4)
        self.assertEqual(p.img_noalt, 1)

    def test_bare_alt_attribute_not_missing(self):
        p = parse('<html><body><img src="a.webp" alt></body></html>')
        self.assertEqual(p.img_noalt, 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
