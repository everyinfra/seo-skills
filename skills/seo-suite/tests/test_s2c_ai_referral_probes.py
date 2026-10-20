#!/usr/bin/env python3
"""ai_referral_log.py --classify 回归测试(B26;合成日志,零网络)。

期望值来源:bug 卡 B26——冒充 AI 爬虫 UA 的漏洞扫描(请求 /.env、/.git/HEAD、id_rsa、
../proc/self/environ 等)被算进 bot 失败率,得出「retrieval 层 failure = 可见性被封,排查 WAF/robots」
的错误结论。期望:失败率先剔除探测路径;结论写明「UA 未验证」;日志里有真实客户端 IP 时提示按
官方 IP 段/反查验证,没有(::1、内网)就明说无法验证;源站在 CDN 后,报告尾部写「bot 量以 CDN 的
bot 分析为准」。探测路径取漏洞扫描器真实会请求的路径(.env / .git / .aws/credentials /
docker-compose.yml / wp-config / .svn / id_rsa / 路径穿越)。
"""
import os
import subprocess
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(BASE, "scripts", "ai_referral_log.py")

PROBES = ["/.env", "/.env.production", "/.git/HEAD", "/.git/config", "/.aws/credentials",
          "/docker-compose.yml", "/wp-config.php.bak", "/.svn/entries", "/id_rsa",
          "/static/../../../../proc/self/environ", "/%2e%2e/%2e%2e/etc/passwd"]


def line(ip, path, status, ua):
    return '%s - - [18/Oct/2026:04:00:00 +0000] "GET %s HTTP/1.1" %d 0 "-" "%s"' % (ip, path, status, ua)


def run(lines):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, SCRIPT, "-", "--classify"], input="\n".join(lines) + "\n",
                          capture_output=True, text=True, encoding="utf-8", env=env).stdout


UA_CHATGPT = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; ChatGPT-User/1.0; +https://openai.com/bot"
UA_PPLX = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)"


class ProbeExclusionTests(unittest.TestCase):
    def test_scanner_404s_do_not_read_as_blocked_visibility(self):
        ls = [line("::1", p, 404, UA_CHATGPT if i % 2 else UA_PPLX) for i, p in enumerate(PROBES)]
        ls += [line("::1", "/pricing", 200, UA_CHATGPT), line("::1", "/docs", 200, UA_PPLX)] * 20
        out = run(ls)
        self.assertNotIn("可见性被封", out)                                  # 修前「= 事实上的可见性被封」
        self.assertIn("UA 未验证", out)
        self.assertIn("探测", out)
        self.assertIn(str(len(PROBES)), out)                                # 剔除条数要报出来
        self.assertIn("CDN", out)

    def test_loopback_only_says_cannot_verify(self):
        out = run([line("::1", "/pricing", 200, UA_CHATGPT), line("127.0.0.1", "/docs", 200, UA_PPLX)])
        self.assertIn("无法验证", out)

    def test_public_ip_suggests_official_ranges(self):
        out = run([line("1.2.3.4", "/pricing", 200, UA_CHATGPT)])
        self.assertIn("官方 IP 段", out)

    def test_real_retrieval_failure_still_warned_but_unverified(self):
        out = run([line("1.2.3.4", "/pricing", 403, UA_CHATGPT), line("1.2.3.4", "/docs", 200, UA_CHATGPT)])
        self.assertIn("WARN", out)
        self.assertIn("UA 未验证", out)
        self.assertNotIn("事实上的可见性被封", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
