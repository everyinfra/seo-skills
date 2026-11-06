"""选题按「同类页带来的注册」加权(0.43.0)。

夹具是 everyinfra.com 11-07 的真实外部数据包节选。期望值来自线上结果,不来自读实现:
- 旧排法把 /es/partners/power-bi 排第一(展示 309、点击 0),它的搜索词是「servicios power bi」,
  合作伙伴页类在 10-21～10-31 带来 0 个注册;
- 能力页类(*-api、*-api/*)和文档页在 11-01～11-06 带来 50、37、8 个注册(回放检验期,排法没看过)。
"""
import copy
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import ops  # noqa: E402

FX = os.path.join(HERE, "fixtures", "ops_conversions_everyinfra_20261107.json")


def load():
    with open(FX, encoding="utf-8") as f:
        return json.load(f)


class SignupPriority(unittest.TestCase):
    def test_without_conversions_keeps_old_pick(self):
        ext = load()
        del ext["sources"]["conversions"]
        self.assertIsNone(ops.conversion_model(ext))
        top = ops.ctr_opportunity(ext, None)
        self.assertEqual(top[0]["page"], "https://everyinfra.com/es/partners/power-bi")

    def test_zero_signup_class_sinks(self):
        ext = load()
        model = ops.conversion_model(ext)
        top = ops.ctr_opportunity(ext, model)
        self.assertNotIn("https://everyinfra.com/es/partners/power-bi", [p["page"] for p in top[:3]])
        self.assertIn(top[0]["page_class"], ("docs", "*-api", "*-api/*"))
        rec = ops.recommend([], [], None, top, None, {}, None)
        self.assertIn("同类页", rec["why"])

    def test_page_class_groups_platform_pages(self):
        cls = ops.page_classer(["https://x.com/en/taobao-api", "https://x.com/douyin-api/search",
                                "https://x.com/xianyu-api", "https://x.com/partners/a", "https://x.com/en"])
        self.assertEqual(cls("https://x.com/ja/taobao-api"), "*-api")
        self.assertEqual(cls("https://x.com/douyin-api/search"), "*-api/*")
        self.assertEqual(cls("https://x.com/es/partners/power-bi"), "partners/*")
        self.assertEqual(cls("https://x.com/en"), "/")

    def test_prune_skips_roots_and_sections(self):
        ext = load()
        ext2 = copy.deepcopy(ext)
        del ext2["sources"]["conversions"]
        for e in (ext, ext2):
            got = [p["page"] for p in ops.monthly_extras(e, ops.conversion_model(e))["prune_candidates"]]
            for u in ("https://everyinfra.com/en/about", "https://everyinfra.com/en/build",
                      "https://everyinfra.com/en/guides"):
                self.assertNotIn(u, got)


if __name__ == "__main__":
    unittest.main()
