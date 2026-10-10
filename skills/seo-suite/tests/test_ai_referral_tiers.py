#!/usr/bin/env python3
"""ai_referral_log.py B5 扩展(bot 分类与归因)测试:
bot 四桶分类(含未知 unclassified)/failure_rate 两级(按 bot 与按桶)/
llms.txt 双基线(Otterly 90 天口径)/--attribution 正则内容/
retrieval-training 分层结论/JSON 日志行/向后兼容。
standalone(自带 run_script 助手,合成 CLF+JSON 日志行,零网络):
python3 tests/test_ai_referral_tiers.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。"""
import os
import subprocess
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import ai_referral_log as ar  # noqa: E402  (需先入 SCRIPTS 路径)

GPTBOT_UA = "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)"
CHATGPT_USER_UA = "Mozilla/5.0 ChatGPT-User/1.0; +https://openai.com/bot"
PPLX_BOT_UA = "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexity-bot)"
META_AGENT_UA = "Mozilla/5.0 (compatible; Meta-ExternalAgent/1.0)"


def clf(ip, path, status, ua="Mozilla/5.0", referer="-"):
    """合成一行 combined(CLF)日志。"""
    return ('%s - - [09/Oct/2026:10:00:00 +0800] "GET %s HTTP/1.1" %s 128 "%s" "%s"'
            % (ip, path, status, referer, ua))


def run_script(args=(), stdin=None):
    """独立助手(与 run_tests.py 同形):子进程跑脚本,捕获输出。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "ai_referral_log.py"),
                           *args], input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


class TierClassificationTests(unittest.TestCase):
    """四桶:显式三桶 + agent_visits 宽匹配 + 未知单列 unclassified。"""

    def test_four_tiers_and_unclassified(self):
        lines = [
            clf("1.1.1.1", "/a", "200", ua=GPTBOT_UA),
            clf("1.1.1.1", "/b", "200", ua=CHATGPT_USER_UA),
            clf("1.1.1.1", "/c", "200", ua=PPLX_BOT_UA),
            clf("1.1.1.1", "/d", "200", ua=META_AGENT_UA),
            clf("1.1.1.1", "/e", "200"),                       # 普通浏览器 UA
        ]
        res = ar.analyze(lines)
        t = res["tiers"]
        self.assertEqual((t["training"]["hits"], t["on_demand_fetcher"]["hits"],
                          t["search_index"]["hits"], t["agent_visits"]["hits"],
                          t["unclassified"]["hits"]), (1, 1, 1, 1, 1))
        self.assertEqual(res["ai_bot_total"], 4)
        # 规格名单抽查(三家口径合并的显式映射)
        for tok in ("ChatGPT-User", "Claude-User", "Perplexity-User",
                    "Gemini-Deep-Research", "MistralAI-User", "Manus-User",
                    "Meta-ExternalFetcher"):
            self.assertIn(tok, ar.BOT_TIERS["on_demand_fetcher"])
        for tok in ("PerplexityBot", "OAI-SearchBot", "Claude-SearchBot",
                    "AzureAI-SearchBot", "Amzn-SearchBot"):
            self.assertIn(tok, ar.BOT_TIERS["search_index"])
        for tok in ("GPTBot", "ClaudeBot", "Claude-Web", "CCBot", "Google-Extended",
                    "GoogleOther", "Bytespider", "DeepSeekBot", "GrokBot"):
            self.assertIn(tok, ar.BOT_TIERS["training"])
        # 显式映射优先于宽匹配:Fetcher=on_demand,Agent=agent_visits
        self.assertEqual(ar.classify_ua("x Meta-ExternalFetcher/1.0"),
                         ("Meta-ExternalFetcher", "on_demand_fetcher"))
        self.assertEqual(ar.classify_ua("x Meta-ExternalAgent/1.0"),
                         ("Meta-ExternalAgent", "agent_visits"))
        self.assertEqual(ar.classify_ua("Mozilla/5.0"), (None, "unclassified"))
        # 旧 6 bot 名全部有桶归属(向后兼容)
        for b in ar.BOT_UAS:
            self.assertIn(b, ar._BOT_TIER_OF)

    def test_json_log_lines(self):
        lines = [
            '{"path": "/json-a", "status": 200, "user_agent": "%s", "referer": "-", "ip": "9.9.9.9", "time": "2026-10-09T10:00:00Z"}' % GPTBOT_UA,
            '{"request": "GET /json-b HTTP/1.1", "status_code": 403, "agent": "ChatGPT-User/1.0", "referrer": "https://chatgpt.com/"}',
            '{"path": "/x"}',          # 缺 status → 不计入
            'not json at all',
        ]
        res = ar.analyze(lines)
        self.assertEqual(res["parsed"], 2)
        t = res["tiers"]
        self.assertEqual((t["training"]["hits"], t["training"]["fail"]), (1, 0))
        self.assertEqual((t["on_demand_fetcher"]["hits"], t["on_demand_fetcher"]["fail"]),
                         (1, 1))                                    # 403 计失败
        self.assertEqual(res["stats"]["chatgpt.com"]["hits"], 1)   # JSON referrer 也归因
        self.assertEqual(res["bot_rows"]["GPTBot"]["statuses"], {"200": 1})


class FailureRateTests(unittest.TestCase):
    """failure_rate=4xx+5xx 占比,按 bot 与按桶两级。"""

    def test_failure_rate_per_bot_and_tier(self):
        lines = [
            clf("1.1.1.1", "/a", "200", ua=GPTBOT_UA),
            clf("1.1.1.1", "/a", "404", ua=GPTBOT_UA),
            clf("1.1.1.1", "/a", "503", ua=GPTBOT_UA),
            clf("2.2.2.2", "/b", "200", ua=PPLX_BOT_UA),
            clf("2.2.2.2", "/b", "200", ua=PPLX_BOT_UA),
            clf("3.3.3.3", "/", "301"),                           # 3xx 不算失败
        ]
        res = ar.analyze(lines)
        row = res["bot_rows"]["GPTBot"]
        self.assertEqual((row["hits"], row["fail"]), (3, 2))
        tr = res["tiers"]["training"]
        self.assertEqual((tr["hits"], tr["fail"]), (3, 2))        # 桶级同值
        si = res["tiers"]["search_index"]
        self.assertEqual((si["hits"], si["fail"]), (2, 0))
        unc = res["tiers"]["unclassified"]
        self.assertEqual((unc["hits"], unc["fail"]), (1, 0))      # 301 不进 4xx/5xx
        out = ar.render(res, classify=True)
        self.assertIn("66.7%", out)          # GPTBot(bot 级)= training(桶级)
        self.assertIn("0.0%", out)           # search_index / unclassified
        self.assertIn("[training]", out)     # bot 行带桶标签
        self.assertIn("bot×status 矩阵", out)
        # 矩阵行:GPTBot 200/404/503 各 1,total=3
        self.assertTrue(any(l.split() == ["GPTBot", "1", "1", "1", "3"]
                            for l in out.splitlines()))

    def test_top_url_per_tier(self):
        lines = [clf("2.2.2.2", "/blog", "200", ua=PPLX_BOT_UA) for _ in range(3)]
        lines.append(clf("2.2.2.2", "/docs", "200", ua=PPLX_BOT_UA))
        out = ar.render(ar.analyze(lines), classify=True)
        self.assertIn("/blog(3)", out)
        self.assertIn("/docs(1)", out)


class LlmsBaselineTests(unittest.TestCase):
    """llms.txt 双基线(Otterly 90 天实验口径);日志无 /llms.txt 请求时不输出。"""

    def _log(self):
        lines = [clf("5.5.5.5", "/llms.txt", "200", ua=PPLX_BOT_UA)]
        lines += [clf("5.5.5.5", "/blog", "200", ua=PPLX_BOT_UA) for _ in range(9)]
        lines += [clf("8.8.8.8", "/p%d" % i, "200") for i in range(10)]
        return lines

    def test_dual_baseline_numbers_and_conclusion(self):
        res = ar.analyze(self._log())
        self.assertEqual(res["llms"], {"hits": 1, "bot_hits": 1})
        self.assertEqual(res["ai_bot_total"], 10)
        self.assertAlmostEqual(res["site_avg_per_page"], 20 / 12, places=4)
        out = ar.render(res, classify=True)
        self.assertIn("10.00%", out)                    # 基线 1: 1/10
        self.assertIn("0.1%", out)                      # 实测参考值
        self.assertIn("84 vs 265", out)                 # 站均基线参考值
        self.assertIn("llms.txt 是编程 agent 基础设施非可见性杠杆", out)

    def test_absent_llms_txt_no_section(self):
        out = ar.render(ar.analyze([clf("8.8.8.8", "/", "200")]), classify=True)
        self.assertNotIn("llms.txt 双基线", out)
        self.assertNotIn("84 vs 265", out)


class AttributionTests(unittest.TestCase):
    """--attribution:GA4 正则内容 + 三条纪律注记 + 自报归因问卷两问。"""

    def test_attribution_output(self):
        r = run_script(["--attribution"], stdin="")
        self.assertEqual(r.returncode, 0)
        out = r.stdout
        self.assertIn(r"chat\.openai\.com|chatgpt\.com|perplexity\.ai"
                      r"|gemini\.google\.com|copilot\.microsoft\.com|claude\.ai"
                      r"|grok\.com|i\.meta\.ai", out)
        self.assertIn("utm_source", out)                # 同名匹配规则在场
        for note in ("referrer=google.com 无法与自然结果区分",
                     "一切 AI referrer 数字当下限",
                     "不要给入站 AI 链接发明 UTM"):
            self.assertIn(note, out)
        self.assertIn("从哪听说我们", out)
        self.assertIn("你问了 AI 什么", out)


class PolicyVerdictTests(unittest.TestCase):
    """retrieval vs training 分层结论:training 封=授权决策([i] 只提示);
    on_demand/search 封=可见性失败([!] WARN);实测失败时另出 WARN 行。"""

    def test_separation_and_observed_warn(self):
        lines = [
            clf("1.1.1.1", "/a", "403", ua=GPTBOT_UA),        # training 失败 → 只 [i]
            clf("2.2.2.2", "/b", "403", ua=CHATGPT_USER_UA),  # on-demand 失败 → WARN
            clf("3.3.3.3", "/c", "200", ua=PPLX_BOT_UA),
        ]
        out = ar.render(ar.analyze(lines), classify=True)
        tr_line = [l for l in out.splitlines() if "授权决策" in l]
        self.assertEqual(len(tr_line), 1)
        self.assertIn("[i]", tr_line[0])
        self.assertNotIn("WARN", tr_line[0])            # training 不告警
        vis_line = [l for l in out.splitlines()
                    if "可见性失败" in l and "授权决策" not in l]
        self.assertTrue(vis_line)
        self.assertIn("[!]", vis_line[0])
        self.assertIn("WARN 实测", out)
        self.assertIn("100.0%", out)                    # retrieval 1/1

    def test_clean_retrieval_no_warn(self):
        lines = [clf("2.2.2.2", "/b", "200", ua=CHATGPT_USER_UA),
                 clf("3.3.3.3", "/c", "200", ua=PPLX_BOT_UA),
                 clf("1.1.1.1", "/a", "404", ua=GPTBOT_UA)]   # 只有 training 失败
        out = ar.render(ar.analyze(lines), classify=True)
        self.assertNotIn("WARN 实测", out)
        self.assertIn("未观测到 4xx/5xx", out)
        self.assertIn("授权决策", out)                    # training 结论仍在([i])


class BackwardCompatTests(unittest.TestCase):
    """旧 flag/输出不变;--self-test 与 --help 正常;--classify 端到端。"""

    def test_legacy_output_and_flags(self):
        log = "\n".join([
            clf("1.2.3.4", "/pricing", "200", referer="https://chatgpt.com/"),
            clf("3.3.3.3", "/api", "200", ua=GPTBOT_UA),
            "garbage line",
        ])
        r = run_script(["--bot-ua", "--top", "5"], stdin=log)
        self.assertEqual(r.returncode, 0)
        self.assertIn("AI 爬虫到访", r.stdout)
        self.assertIn("GPTBot", r.stdout)
        self.assertIn("下界", r.stdout)
        self.assertNotIn("bot 四桶", r.stdout)          # 不加 --classify 不出新段
        rc = run_script(["--self-test"])
        self.assertEqual(rc.returncode, 0)
        self.assertIn("PASS", rc.stdout)
        rh = run_script(["--help"])
        self.assertEqual(rh.returncode, 0)
        for flag in ("--classify", "--attribution", "--bot-ua"):
            self.assertIn(flag, rh.stdout)

    def test_classify_cli_end_to_end(self):
        log = "\n".join([
            clf("1.1.1.1", "/llms.txt", "200", ua=PPLX_BOT_UA),
            clf("2.2.2.2", "/p", "403", ua=CHATGPT_USER_UA),
            clf("8.8.8.8", "/", "200"),
        ])
        r = run_script(["--classify"], stdin=log)
        self.assertEqual(r.returncode, 0)
        for frag in ("bot 四桶", "search_index", "on_demand_fetcher", "training",
                     "agent_visits", "unclassified", "llms.txt 双基线",
                     "授权决策", "可见性失败", "WARN 实测"):
            self.assertIn(frag, r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
