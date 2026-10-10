#!/usr/bin/env python3
"""robots_posture.py 扩展测试(standalone,合成 robots.txt fixture,零网络;
tests/run_tests.py 自动发现本文件)。覆盖:四态判定 / via_wildcard / 两级评分 /
连续 UA 合并 / 最长匹配+Allow 平局 / BOM+500KB 截断 / crawl_delay+sitemap /
--fix-robots 输出格式 / --json 字段 / 27 bot 名单结构 / parse_groups 冻结契约。"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import robots_posture as rp


def run_cli(txt, *flags):
    """把合成 robots.txt 写进临时目录的 robots.txt,以 file:// 站点根跑 CLI
    (与线上抓取同一条代码路径,并覆盖 URL 自动拼 /robots.txt 的归一化)。"""
    d = tempfile.mkdtemp(prefix="rp-test-")
    with open(os.path.join(d, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    try:
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, "robots_posture.py"),
                               "file://" + d, *flags],
                              capture_output=True, text=True, encoding="utf-8",
                              env=env, timeout=60)
    finally:
        shutil.rmtree(d, ignore_errors=True)


class ParseRobotsTests(unittest.TestCase):
    """RFC 9309:连续 UA 合并 / BOM / 500KB 截断 / crawl_delay+sitemap"""

    def test_consecutive_useragent_lines_merged(self):
        doc = rp.parse_robots("User-agent: a\nUser-agent: b\nDisallow: /x\n\n"
                              "User-agent: c\nAllow: /\n")
        self.assertEqual(doc["groups"]["a"]["disallow"], ["/x"])
        self.assertEqual(doc["groups"]["b"]["disallow"], ["/x"])   # 连续 UA 行共享规则组
        self.assertEqual(doc["groups"]["c"]["disallow"], [])
        self.assertEqual(doc["groups"]["c"]["allow"], ["/"])

    def test_new_group_starts_after_rules(self):
        doc = rp.parse_robots("User-agent: a\nDisallow: /x\nUser-agent: b\nDisallow: /y\n")
        self.assertEqual(doc["groups"]["a"]["disallow"], ["/x"])   # 规则行后的 UA 开新组
        self.assertEqual(doc["groups"]["b"]["disallow"], ["/y"])

    def test_bom_stripped(self):
        doc = rp.parse_robots("\ufeffUser-agent: *\nAllow: /\n")
        self.assertIn("*", doc["groups"])

    def test_500k_truncation_guard(self):
        doc = rp.parse_robots("User-agent: *\nAllow: /\n#" + "x" * 600_000)
        self.assertTrue(doc["truncated"])
        self.assertIn("*", doc["groups"])

    def test_crawl_delay_from_star_group_and_sitemaps(self):
        doc = rp.parse_robots("User-agent: GPTBot\nCrawl-delay: 10\n\n"
                              "User-agent: *\nCrawl-delay: 2\n"
                              "Sitemap: https://s.com/a.xml\nSitemap: https://s.com/b.xml\n")
        self.assertEqual(doc["crawl_delay"], 2.0)                  # 取 * 组
        self.assertEqual(doc["sitemaps"], ["https://s.com/a.xml", "https://s.com/b.xml"])


class ClassifyTests(unittest.TestCase):
    """四态判定 + via_wildcard + 最长匹配/Allow 平局"""

    ROBOTS = ("User-agent: *\nDisallow: /admin\n\n"                       # 通配:基本放行
              "User-agent: GPTBot\nDisallow: /\n\n"                      # 全封
              "User-agent: ClaudeBot\nDisallow: /\nAllow: /blog/\n\n"    # 封但有开洞
              "User-agent: PerplexityBot\nAllow: /\n")                   # 专属放行

    def test_four_states(self):
        doc = rp.parse_robots(self.ROBOTS)
        self.assertEqual(rp.classify(doc, "Googlebot"), {"state": "allowed", "via_wildcard": True})
        self.assertEqual(rp.classify(doc, "GPTBot")["state"], "blocked")
        self.assertFalse(rp.classify(doc, "GPTBot")["via_wildcard"])
        self.assertEqual(rp.classify(doc, "ClaudeBot")["state"], "partial")
        self.assertEqual(rp.classify(doc, "PerplexityBot"), {"state": "allowed", "via_wildcard": False})

    def test_missing_when_no_group_and_no_star(self):
        doc = rp.parse_robots("User-agent: Googlebot\nDisallow: /private\n")
        self.assertEqual(rp.classify(doc, "GPTBot")["state"], "missing")

    def test_own_group_overrides_star(self):
        doc = rp.parse_robots("User-agent: *\nDisallow: /\nUser-agent: OAI-SearchBot\nAllow: /\n")
        self.assertEqual(rp.classify(doc, "OAI-SearchBot")["state"], "allowed")  # 专属组覆盖 *

    def test_longest_match_and_allow_tie(self):
        g = {"allow": ["/page/"], "disallow": ["/page"]}
        self.assertEqual(rp.effective_rule(g, "/page/"), ("allow", 6))   # 最长匹配:6>5
        self.assertEqual(rp.effective_rule(g, "/page2"), ("disallow", 5))
        tie = {"allow": ["/"], "disallow": ["/"]}
        self.assertEqual(rp.effective_rule(tie, "/")[0], "allow")        # 平局 Allow 胜出
        longer_disallow = {"allow": [""], "disallow": ["/"]}
        self.assertEqual(rp.effective_rule(longer_disallow, "/")[0], "disallow")
        self.assertEqual(rp.effective_rule({}, "/"), ("allow", -1))      # 无规则默认允许


class CitationScoringTests(unittest.TestCase):
    """两级评分:ok=5 个都 allowed(部分分);explicit=5 个都有专属规则(满分)"""

    def test_wildcard_allow_gets_partial_only(self):
        rep = rp.citation_report(rp.parse_robots("User-agent: *\nAllow: /\n"))
        self.assertTrue(rep["ok"])
        self.assertFalse(rep["explicit"])                          # 通配符 Allow 拿不到全分
        self.assertEqual(rep["explicit_count"], 0)

    def test_all_explicit_rules_get_full_score(self):
        txt = "User-agent: *\nDisallow: /\n\n" + \
              "".join(f"User-agent: {b}\nAllow: /\n\n" for b in rp.CITATION_BOTS)
        rep = rp.citation_report(rp.parse_robots(txt))
        self.assertTrue(rep["ok"])
        self.assertTrue(rep["explicit"])
        self.assertEqual(rep["explicit_count"], 5)

    def test_blocked_citation_bot_fails_ok(self):
        doc = rp.parse_robots("User-agent: *\nAllow: /\n\nUser-agent: PerplexityBot\nDisallow: /\n")
        rep = rp.citation_report(doc)
        self.assertFalse(rep["ok"])
        self.assertEqual(rep["allowed_count"], 4)

    def test_claudebot_deliberately_excluded(self):
        self.assertNotIn("ClaudeBot", rp.CITATION_BOTS)            # 刻意排除纯训练的 ClaudeBot
        self.assertEqual(rp.CITATION_BOTS,
                         ["OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "Googlebot", "Applebot"])


class RosterTests(unittest.TestCase):
    """27 bot 三层名单结构"""

    def test_27_bots_three_tiers(self):
        self.assertEqual(len(rp.AI_BOTS), 27)
        tiers = {"training": [], "search": [], "user": []}
        for b in rp.AI_BOTS:
            self.assertEqual(set(b), {"token", "desc", "tier"})
            self.assertIn(b["tier"], tiers)
            self.assertTrue(b["desc"])
            tiers[b["tier"]].append(b["token"])
        self.assertEqual(len(tiers["training"]), 12)
        self.assertEqual(len(tiers["search"]), 10)
        self.assertEqual(len(tiers["user"]), 5)
        for must in ("GPTBot", "ClaudeBot", "CCBot", "Google-Extended", "Google-CloudVertexBot"):
            self.assertIn(must, tiers["training"])
        self.assertNotIn("MistralAI-Training", tiers["training"])  # 法语区市场专属,不入 27 全局名单
        for must in ("OAI-SearchBot", "Claude-SearchBot", "Bingbot", "xAI-Bot", "DuckAssistBot"):
            self.assertIn(must, tiers["search"])
        for must in ("ChatGPT-User", "Claude-User", "Perplexity-User", "Meta-ExternalFetcher",
                     "facebookexternalhit"):
            self.assertIn(must, tiers["user"])

    def test_analyze_buckets_and_tier_stats(self):
        rep = rp.analyze("User-agent: *\nDisallow: /\n\nUser-agent: Googlebot\nAllow: /\n")
        self.assertEqual(len(rep["bots"]), 27)
        self.assertEqual(set(rep["bots_blocked"]) & set(rp.CITATION_BOTS),
                         {"OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "Applebot"})
        self.assertIn("Googlebot", rep["bots_allowed"])
        self.assertEqual(rep["tiers"]["search"]["allowed"], 1)
        self.assertFalse(rep["citation"]["ok"])
        self.assertIn("OAI-SearchBot", rep["visibility_failures"])
        self.assertNotIn("GPTBot", rep["visibility_failures"])     # 封 training 不算可见性失败


class CliTests(unittest.TestCase):
    """CLI:--fix-robots 格式 / --json 字段 / --help"""

    def test_fix_robots_block_format(self):
        r = run_cli("User-agent: OAI-SearchBot\nDisallow: /\n", "--fix-robots")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("Traceback", r.stderr)
        # 修复块三行格式:"# {desc}\nUser-agent: {token}\nAllow: /"
        self.assertIn("# Anthropic Claude 搜索索引(AI 引用入口)\nUser-agent: Claude-SearchBot\nAllow: /",
                      r.stdout)
        # 被封的检索 bot 也进修复建议
        self.assertIn("User-agent: OAI-SearchBot\nAllow: /", r.stdout)
        # 训练层带授权决策提示(封 training 是决策不是错误)
        self.assertIn("授权决策", r.stdout)
        # 只打印不写盘:脚本对源文件只读,不产生额外输出
        self.assertIn("只打印不写盘", r.stdout)

    def test_fix_robots_in_json_mode(self):
        r = run_cli("User-agent: *\nAllow: /\n", "--json", "--fix-robots")
        data = json.loads(r.stdout)
        self.assertIn("fix_robots", data)
        self.assertIn("User-agent: Googlebot\nAllow: /", data["fix_robots"])  # 通配放行→专属规则补全

    def test_json_fields(self):
        r = run_cli("User-agent: *\nAllow: /\nSitemap: https://s.com/x.xml\n", "--json")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        for k in ("bots", "bots_allowed", "bots_blocked", "bots_missing", "bots_partial",
                  "tiers", "citation", "crawl_delay", "sitemaps", "visibility_failures",
                  "content_signal", "cloudflare_injected", "deprecated_tokens"):
            self.assertIn(k, data)
        self.assertEqual(len(data["bots"]), 27)
        self.assertTrue(data["citation"]["ok"])
        self.assertFalse(data["citation"]["explicit"])
        self.assertEqual(data["sitemaps"], ["https://s.com/x.xml"])
        self.assertEqual(data["visibility_failures"], [])

    def test_help_lists_new_flags(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "robots_posture.py"), "--help"],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0)
        for frag in ("--fix-robots", "--json", "--signal"):
            self.assertIn(frag, r.stdout)


class BackwardCompatTests(unittest.TestCase):
    """旧 parse_groups 契约(tests/run_tests.py 冻结口径)"""

    def test_parse_groups_contract(self):
        groups, order = rp.parse_groups(
            "User-agent: *\nDisallow: /admin\nDisallow: /tmp\n\nUser-agent: GPTBot\nAllow: /\n")
        self.assertEqual(groups, {"*": {"allow": [], "disallow": ["/admin", "/tmp"]},
                                  "GPTBot": {"allow": ["/"], "disallow": []}})
        self.assertEqual(order, ["*", "GPTBot"])


if __name__ == "__main__":
    unittest.main(verbosity=1)
