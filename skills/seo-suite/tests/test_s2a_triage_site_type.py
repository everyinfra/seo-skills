#!/usr/bin/env python3
"""S2a 回归 B1:project.py triage 站型识别(suggest_site_type)。

期望值来源:
- 本套件判型规则 references/overview/site-type-playbooks.md「站型识别判别法」与各卡
  「识别信号」:⑤文档/开发者站 URL 型谱 `/docs/`、`/api/`·`/reference/`、`/guides/`、
  `/changelog`、版本路径 `/v1`;②电商 `/c/`·`/collections/`·`/category/` 与
  `/p/`·`/products/`,cart/checkout 路径——按**路径段**判,不是子串。
- 同文件判型纪律:模糊时「列前二站型连同证据让用户确认」;project.py --help 写明
  「自报站型 … 以自报为准」→ 自报后 suggested 必须是自报值,不得给出相反建议。
合成 crawl(域名 *.test,零网络)。"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

import project as pj  # noqa: E402

H = "https://api-saas.test"
# API SaaS 站:docs、x-api 能力页、pricing;另有 3 个 /products/ 数据产品页,没有 cart/checkout
# (旧实现按子串 "/product" 命中电商 → 3/10=30% 首位 → 建议「电商(DTC)」;判型规则要求
#  电商须 PDP 与 cart/checkout 或 PLP 并存)
API_SITE = {"pages": [{"url": H + p, "title": t} for p, t in [
    ("/", "Example Data API"),
    ("/en/pricing", "Pricing"),
    ("/en/docs", "Docs"),
    ("/en/docs/auth", "Authentication with an API key"),
    ("/en/tiktok-api/profile", "TikTok Profile API"),
    ("/en/tiktok-api/posts", "TikTok Posts API"),
    ("/en/products/social", "Social data"),
    ("/en/products/search", "Search data"),
    ("/en/products/captcha", "Captcha solving"),
    ("/en/status", "Status"),
]]}

SHOP = {"pages": [{"url": "https://shop.test" + p} for p in
                  ("/", "/collections/shoes", "/products/red-shoe", "/products/blue-shoe",
                   "/cart", "/products/green-shoe")]}


class SiteTypeTests(unittest.TestCase):

    def test_api_site_not_ecommerce(self):
        st = pj.suggest_site_type(API_SITE)
        self.assertNotIn("电商(DTC)", st["candidates"], st)
        self.assertEqual(st["suggested"], "文档 / 开发者站", st)

    def test_declared_type_wins(self):
        st = pj.suggest_site_type(API_SITE, "SaaS / 软件营销站")
        self.assertEqual(st["suggested"], "SaaS / 软件营销站", st)
        self.assertEqual(st["candidates"][0], "SaaS / 软件营销站")
        self.assertIn("自报", st["note"])

    def test_substring_not_segment_not_counted(self):
        crawl = {"pages": [{"url": "https://x.test" + p} for p in
                           ("/production-notes", "/en/productivity-tips", "/shopping-guide-api")]}
        st = pj.suggest_site_type(crawl)
        self.assertNotIn("电商(DTC)", st["candidates"], st)

    def test_real_shop_still_detected(self):
        st = pj.suggest_site_type(SHOP)
        self.assertEqual(st["suggested"], "电商(DTC)", st)


if __name__ == "__main__":
    unittest.main()
