#!/usr/bin/env python3
"""S2a 回归:markets.json 数据口径(B12/B13/B17/B20/B34)。

期望值来源(一手原文,读取 2026-10-21):
- B17 https://developers.google.com/search/docs/specialty/international/localized-versions ——
  "Only language codes listed in ISO 639-1 and region codes listed in ISO 3166-1 Alpha 2 are
  supported; other codes that aren't listed in those standards, such as es-419, aren't supported."
  → es 市场推荐的 hreflang_codes 不得含 es-419;不得再写「es-419 是 Google 接受的唯一 UN 区域码」。
- B20 同页:zh-CN 是 ISO 639-1+ISO 3166-1 合法组合,zh-Hans/zh-Hant 是可选写法
  → 不得再写「不用 zh-CN 裸码」。
- B34 https://developers.google.com/search/docs/fundamentals/creating-helpful-content ——
  "Are you writing to a particular word count because you've heard or read that Google has a
  preferred word count? (No, we don't.)" → pillar_min 必须标明是本套件口径/第三方观察。
- B13 desc_min 必须存在且 0 < desc_min < desc_limit(同单位)。
- B12 title-link 文档:标题按设备宽度截断,无字符上限 → zh 标题不能按码点数计。
可用 SEO_MARKETS_JSON 环境变量指向另一份 markets.json(修前红验证用)。"""
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.environ.get("SEO_MARKETS_JSON") or os.path.join(os.path.dirname(HERE), "scripts", "markets.json")


def markets():
    with open(PATH, encoding="utf-8") as f:
        return json.load(f)["markets"]


class MarketsJsonTests(unittest.TestCase):

    def test_es_419_not_recommended_as_hreflang(self):
        es = markets()["es"]
        self.assertNotIn("es-419", [c.lower() for c in es["hreflang_codes"]])
        text = json.dumps(es, ensure_ascii=False)
        self.assertNotIn("唯一 UN 区域码", text)
        self.assertIn("不支持 es-419", text)

    def test_zh_cn_not_called_invalid(self):
        zh = markets()["zh"]
        text = json.dumps(zh, ensure_ascii=False)
        self.assertNotRegex(text, r"不用 zh-CN|zh-CN 裸码")
        self.assertIn("zh-CN", text)

    def test_pillar_min_marked_as_suite_convention(self):
        for code, mk in markets().items():
            if "pillar_min" not in mk:
                continue
            with self.subTest(market=code):
                note = mk.get("pillar_note") or ""
                self.assertIn("本套件口径", note)
                self.assertIn("不是排名要求", note)

    def test_desc_min_below_limit(self):
        for code, mk in markets().items():
            with self.subTest(market=code):
                lo = mk.get("desc_min")
                self.assertIsInstance(lo, int)
                self.assertTrue(0 < lo < mk["desc_limit"]["value"], (lo, mk["desc_limit"]))

    def test_zh_title_counts_display_width(self):
        tl = markets()["zh"]["title_limit"]
        self.assertNotEqual(tl["unit"], "chars")
        self.assertEqual((tl["unit"], tl["value"]), ("fullwidth", 30))   # 全角 1/半角 0.5 ≡ 宽 60


if __name__ == "__main__":
    unittest.main()
