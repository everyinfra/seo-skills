#!/usr/bin/env python3
"""market_lint.py 回归测试(B20 代码部分、B33;合成页面,零网络)。

期望值来源:
- Google「Localized versions of your pages」(developers.google.com/search/docs/specialty/
  international/localized-versions,2026-09-21 更新):只支持 ISO 639-1 + 可选 ISO 3166-1 Alpha-2,
  「other codes ... such as es-419, aren't supported」;文字码 zh-Hans/zh-Hant 是可用写法之一——
  zh-CN(639-1 + 3166-1)本身合法,不是「裸区域码」错误。
- B33:语言 ≠ 市场 ≠ 币种,全球统一美元定价是正当做法 → 外币符号只 INFO,不计 WARN/FAIL。
"""
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import market_lint as ml  # noqa: E402


def lint(market, content, suffix=".html"):
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8") as f:
        f.write(content)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "market_lint.py"), "--market", market, f.name],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    os.unlink(f.name)
    return r


def zh_ctx(raw):
    return {"body": "这是一个简体中文页面的正文内容。", "raw": raw, "is_html": True}


class ZhHreflangTests(unittest.TestCase):
    def test_zh_cn_is_valid(self):
        raw = ('<link rel="alternate" hreflang="zh-CN" href="https://example.com/zh">'
               '<link rel="alternate" hreflang="zh-TW" href="https://example.com/tw">'
               '<link rel="alternate" hreflang="en" href="https://example.com/en">')
        state, detail = ml.r_zh_script(zh_ctx(raw))
        self.assertEqual(state, "OK", detail)                       # 修前 FAIL「裸区域码」
        self.assertNotIn("裸区域码", detail)

    def test_script_subtag_valid(self):
        raw = '<link rel="alternate" hreflang="zh-Hans" href="https://example.com/zh">'
        self.assertEqual(ml.r_zh_script(zh_ctx(raw))[0], "OK")

    def test_invalid_zh_code_still_flagged(self):
        raw = '<link rel="alternate" hreflang="zh-419" href="https://example.com/zh">'
        state, detail = ml.r_zh_script(zh_ctx(raw))
        self.assertEqual(state, "FAIL")                             # UN M.49 区域码 Google 不支持
        self.assertIn("zh-419", detail)

    def test_end_to_end_no_bare_region_warning(self):
        html = ('<html><head><title>示例接口平台</title><meta name="description" content="示例描述文字">'
                '<link rel="alternate" hreflang="zh-CN" href="https://example.com/zh"></head>'
                '<body><p>这是一个简体中文页面的正文内容。</p></body></html>')
        r = lint("zh", html)
        self.assertNotIn("裸区域码", r.stdout)


class Es419Tests(unittest.TestCase):
    def test_es_419_flagged_unsupported(self):
        raw = ('<link rel="alternate" hreflang="es" href="https://example.com/es">'
               '<link rel="alternate" hreflang="es-419" href="https://example.com/latam">')
        state, detail = ml.r_es_419({"raw": raw, "is_html": True})
        self.assertEqual(state, "FAIL", detail)                     # 修前 OK「唯一 UN 区域码」
        self.assertNotIn("唯一 UN 区域码", detail)

    def test_es_country_codes_without_419_ok(self):
        raw = ('<link rel="alternate" hreflang="es" href="https://example.com/es">'
               '<link rel="alternate" hreflang="es-MX" href="https://example.com/mx">')
        state, detail = ml.r_es_419({"raw": raw, "is_html": True})
        self.assertEqual(state, "OK", detail)                       # 修前 FAIL「有 es-MX 而无 es-419」

    def test_classify_survives_rewritten_special_check(self):
        # markets.json 的文案由别的组改写;只要仍是 es-419 的 hreflang 检查,就要映射到同一规则
        self.assertEqual(ml.classify("es", "es-419 hreflang 检查(Google 不支持 es-419)"), "es_419")
        self.assertIsNone(ml.classify("es", "半岛偏置对抗:es-419 独立测 SERP"))


class CurrencyTests(unittest.TestCase):
    def test_usd_on_zh_page_is_info(self):
        r = lint("zh", "示例接口平台\n按次计费说明\n每次调用 $0.002,失败不扣费,全球统一美元定价。", ".txt")
        self.assertNotIn("[v3-FAIL] 货币符号", r.stdout)             # 修前 FAIL「价格未本地化」
        self.assertIn("[v3-INFO] 货币符号", r.stdout)
        self.assertIn("有意", r.stdout)

    def test_usd_on_es_page_is_info(self):
        r = lint("es", "Plataforma de API\nPrecios\nCada llamada cuesta $0.002 y no se cobra si falla.", ".txt")
        self.assertNotIn("[v3-FAIL] 货币符号", r.stdout)
        self.assertIn("[v3-INFO] 货币符号", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
