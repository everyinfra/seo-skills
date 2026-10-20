#!/usr/bin/env python3
"""S2a 回归 B2/B3:prioritize / envelope 的修复建议按 --market 阈值,不写「官方阈值」。

期望值来源:
- site_audit.py --market 的阈值来自 markets.json(--help 契约);同一条审计链里
  prioritize/envelope 的建议不得与 site_audit 的上限矛盾(zh:title 30 全角、description 78 字)。
- 「Botify 官方阈值」:Google 文档对 title/description 无字数要求
  (title-link:「there's no limit on how long a <title> element can be」;snippet:
  「There's no limit on how long a meta description can be」)→ 长度建议只能标本套件口径,
  不能写成任何官方阈值。
- B3:已检测到服务端内容的页面,rendering 建议不得是「关键内容服务端渲染」。
合成 site_audit --json 输入,零网络。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
sys.path.insert(0, SCRIPTS)


def run(name, *args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def write_audit(results, market=None, limits=None):
    blob = {"schema_version": 1, "audited": len(results), "critical": 0, "results": results}
    if market:
        blob["market"] = market
    if limits:
        blob["limits"] = limits
    fd, path = tempfile.mkstemp(suffix=".json", prefix="s2a_adv_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(blob, f, ensure_ascii=False)
    return path


ZH_LIMITS = {"title": {"unit": "fullwidth", "min": 20, "max": 30, "ideal_min": None},
             "description": {"unit": "chars", "min": 39, "max": 78}}


def zh_page(desc_len, title_len, findings=()):
    return {"verdict": "pass", "findings": [dict(severity=s, area=a, message=m) for s, a, m in findings],
            "meta": {"title": "数" * title_len, "title_len": "%d fullwidth/30" % title_len,
                     "desc_len": "%d chars/78" % desc_len, "words": 800, "h1": 1}}


class PrioritizeMarketTests(unittest.TestCase):

    def test_no_official_threshold_wording(self):
        import prioritize as pr
        for r in pr.RULES:
            with self.subTest(rule=r["id"]):
                self.assertNotIn("官方阈值", r["fix"])

    def test_zh_in_range_page_not_told_to_expand(self):
        """zh 页:title 28/30 全角、description 70/78 字——都在 site_audit 区间内,
        prioritize 不得再建议扩到 50-60 / ~155。"""
        path = write_audit({"https://zh.test/a": zh_page(70, 28)}, "zh", ZH_LIMITS)
        r = run("prioritize.py", "--audit", path, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        hit = {i["rule"] for i in rep["fix_now"] + rep["explore"] if i.get("hit_urls")}
        self.assertNotIn("desc_short", hit)
        self.assertNotIn("title_short", hit)

    def test_zh_short_desc_fix_uses_market_limits(self):
        path = write_audit({"https://zh.test/a": zh_page(20, 28)}, "zh", ZH_LIMITS)
        rep = json.loads(run("prioritize.py", "--audit", path, "--json").stdout)
        item = [i for i in rep["fix_now"] if i["rule"] == "desc_short"][0]
        self.assertIn("78", item["fix_instruction"])
        self.assertNotIn("155", item["fix_instruction"])

    def test_market_flag_without_payload_market(self):
        """--market 显式给出时(health_score 摘要等无 market 键的输入),阈值取该市场。"""
        page = zh_page(70, 28)
        path = write_audit({"https://zh.test/a": page})
        rep = json.loads(run("prioritize.py", "--audit", path, "--market", "zh", "--json").stdout)
        hit = {i["rule"] for i in rep["fix_now"] + rep["explore"] if i.get("hit_urls")}
        self.assertNotIn("desc_short", hit)


class EnvelopeMarketTests(unittest.TestCase):

    def envelope(self, path):
        r = run("envelope.py", "--audit", path, "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        env = json.loads(r.stdout)
        return {f["rule_id"]: f for c in env["categories"] for f in c["findings"]}

    def test_zh_description_reco_uses_zh_limits(self):
        path = write_audit({"https://zh.test/a": zh_page(
            0, 28, [("WARN", "description", "缺失"), ("WARN", "title", "35 fullwidth 超上限 30")])},
            "zh", ZH_LIMITS)
        f = self.envelope(path)
        self.assertNotIn("155", f["description"]["recommendation"])
        self.assertIn("78", f["description"]["recommendation"])
        self.assertNotIn("50-60", f["title"]["recommendation"])
        self.assertIn("30", f["title"]["recommendation"])

    def test_server_rendered_js_weight_reco_has_no_ssr_advice(self):
        msg = ("JS 重量:外部 script 20 个(>15)/内联 JS 0KB(>100KB)——已检测到服务端内容"
               "(纯文本 9000 字),只提示体积,无需改渲染方式")
        path = write_audit({"https://en.test/a": {"verdict": "pass", "meta": {},
                            "findings": [{"severity": "INFO", "area": "rendering", "message": msg}]}})
        reco = self.envelope(path)["rendering"]["recommendation"]
        self.assertNotIn("服务端渲染", reco)


if __name__ == "__main__":
    unittest.main()
