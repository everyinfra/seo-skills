#!/usr/bin/env python3
"""SSRF/输入防护测试(pipeline-completeness.md R5 安全节:12 脚本零 SSRF 的 5 脚本切片
——llmstxt/robots_posture/schema_lint/ai_views/core_eeat)。零网络:DNS 打桩(host 当
IP 字面量直通,monitor 加固测试同款)+ opener 打桩;302 跳私网走 _RedirectGuard 逐跳
复查路径。覆盖:
  ① 入口 URL 校验:仅 http(s),file:///etc/passwd、ftp:// 等拒
  ② 私网/环回/链路本地/保留段拒连(含 http://169.254.169.254/ 云元数据端点)
  ③ 重定向逐跳复查:302 跳私网/非 http(s) 必须拒
  ④ core_eeat read() 2MB 上限
  ⑤ ai_views <a href> 仅留 http(s)/mailto/相对路径(javascript:/data: 弃置并计数)
  ⑥ 正常 http(s) URL 不受影响(DNS+opener 双打桩全链路放行)
用法: python3 tests/test_ssrf_guard.py(tests/run_tests.py 自动发现本文件)"""
import contextlib
import os
import socket
import subprocess
import sys
import unittest
from unittest import mock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import ai_views        # noqa: E402 (需先入 SCRIPTS 路径)
import core_eeat       # noqa: E402
import llmstxt         # noqa: E402
import robots_posture  # noqa: E402
import schema_lint     # noqa: E402

MODULES = [llmstxt, robots_posture, schema_lint, ai_views, core_eeat]
PUBLIC_IP = "93.184.216.34"          # example.com 公网 IP(打桩用,零网络)


@contextlib.contextmanager
def stub_dns(ip_of=None):
    """DNS 打桩:ssrf_guard 走 getaddrinfo 判 IP——host 原样直通(按 IP 字面量判定)
    或映射到固定 IP;不受本机 fake-IP 代理影响(monitor 加固测试同款)。"""
    resolve = (lambda host: host) if ip_of is None else ip_of

    def fake_getaddrinfo(host, *a, **k):
        return [(socket.AF_INET, 1, 6, "", (resolve(host), 0))]

    orig = socket.getaddrinfo
    socket.getaddrinfo = fake_getaddrinfo
    try:
        yield
    finally:
        socket.getaddrinfo = orig


class _FakeResp:
    """打桩响应:记录 read(n) 的上限(验 2MB 帽),回 canned body。"""

    status = 200

    def __init__(self, body=b"<html><body>ok</body></html>"):
        self._body = body
        self.read_limit = None

    def read(self, n=-1):
        self.read_limit = n
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class _FakeOpener:
    """打桩 opener:fetch 的唯一网络出口替换件,记录请求 URL。"""

    def __init__(self, resp=None):
        self.resp = resp or _FakeResp()
        self.seen = []

    def open(self, req, timeout=None):
        self.seen.append(req.full_url)
        return self.resp


class SsrfGuardCase(unittest.TestCase):
    """公共底座:每个用例前后清空各模块 _ssrf_cache,防跨用例缓存污染。"""

    def setUp(self):
        for m in MODULES:
            m._ssrf_cache.clear()

    def tearDown(self):
        for m in MODULES:
            m._ssrf_cache.clear()


class SchemeGuardTests(SsrfGuardCase):
    """① 入口 URL 校验:http(s) 仅——scheme 检查发生在任何 DNS/网络之前。"""

    EVIL = ["file:///etc/passwd",
            "ftp://example.com/f",
            "gopher://127.0.0.1/x",
            "data:text/html,<script>alert(1)</script>"]

    def test_entry_scheme_rejected(self):
        for mod in MODULES:
            for url in self.EVIL:
                with self.assertRaises(mod.FetchError,
                                       msg="%s 应拒 %s" % (mod.__name__, url)):
                    mod.fetch(url)

    def test_load_document_url_guarded(self):
        """core_eeat --url 入口(load_document)同样被守卫。"""
        with self.assertRaises(core_eeat.FetchError):
            core_eeat.load_document(None, "file:///etc/passwd")


class PrivateRangeTests(SsrfGuardCase):
    """② 私网/环回/链路本地/保留段拒连(DNS 打桩,IP 字面量直通,零网络)。"""

    PRIVATE = ["http://127.0.0.1:8080/admin",            # 环回
               "http://10.0.0.5/internal",               # 私网 RFC1918
               "http://192.168.1.10/router",             # 私网 RFC1918
               "http://169.254.169.254/latest/meta-data",  # 云元数据端点(链路本地)
               "http://0.0.0.0/x",                       # 未指定地址
               "http://[::1]/x"]                         # IPv6 环回

    def test_private_ranges_rejected(self):
        for mod in MODULES:
            for url in self.PRIVATE:
                with stub_dns():
                    with self.assertRaises(mod.FetchError,
                                           msg="%s 应拒 %s" % (mod.__name__, url)):
                        mod.fetch(url)


class RedirectHopTests(SsrfGuardCase):
    """③ 重定向逐跳复查:302 跳私网/元数据端点/非 http(s) 必须拒(fetch 打桩路径)。"""

    REDIRECT_EVIL = ["http://169.254.169.254/latest/meta-data",
                     "http://127.0.0.1:8080/x",
                     "http://10.0.0.5/internal",
                     "file:///etc/passwd",
                     "ftp://example.com/f"]

    def test_302_to_private_rejected_per_hop(self):
        for mod in MODULES:
            for evil in self.REDIRECT_EVIL:
                with stub_dns():
                    with self.assertRaises(mod.FetchError,
                                           msg="%s 302→%s 应拒" % (mod.__name__, evil)):
                        # newurl(第 6 参)是重定向目标——这才是被逐跳复查的 URL
                        mod._RedirectGuard().redirect_request(
                            None, None, 302, "Found", {}, evil)


class NormalUrlTests(SsrfGuardCase):
    """⑥ 正常 http(s) URL 不受影响:DNS 映射公网 IP + opener 打桩,全链路放行。"""

    def test_public_url_passes_end_to_end(self):
        for mod in MODULES:
            opener = _FakeOpener()
            with stub_dns(ip_of=lambda host: PUBLIC_IP):
                with mock.patch.object(mod, "_opener", opener):
                    out = mod.fetch("https://example.com/page")
            self.assertEqual(opener.seen, ["https://example.com/page"],
                             mod.__name__)
            # 返回形状按各脚本契约:llmstxt/ai_views → (status, body);其余 → body
            if isinstance(out, tuple):
                self.assertEqual(out[0], 200)
                self.assertIn("ok", out[1])
            else:
                self.assertIn("ok", out)

    def test_ssrf_guard_caches_public_host(self):
        for mod in MODULES:
            with stub_dns(ip_of=lambda host: PUBLIC_IP):
                mod.ssrf_guard("example.com")           # 首查通过
                self.assertIn("example.com", mod._ssrf_cache)
                mod.ssrf_guard("example.com")           # 命中缓存,不再解析


class CoreEeatReadCapTests(SsrfGuardCase):
    """④ core_eeat read() 2MB 上限(R5:core_eeat read 无上限)。"""

    def test_read_capped_at_2mb(self):
        resp = _FakeResp()
        with stub_dns(ip_of=lambda host: PUBLIC_IP):
            with mock.patch.object(core_eeat, "_opener", _FakeOpener(resp)):
                body = core_eeat.fetch("https://example.com/huge")
        self.assertEqual(resp.read_limit, core_eeat.MAX_READ_BYTES)
        self.assertEqual(core_eeat.MAX_READ_BYTES, 2_000_000)
        self.assertIn("ok", body)


class AiViewsHrefFilterTests(unittest.TestCase):
    """⑤ ai_views 采集的 <a href> 仅保留 http(s)/mailto/相对路径;
    javascript:/data: 等危险 scheme 弃置并计数(XSS 载体防线)。"""

    HTML = ('<html><body><p>'
            '<a href="javascript:alert(1)">js</a> '
            '<a href="DATA:text/html;base64,PHNjcmlwdD4=">data</a> '
            '<a href="https://ok.test/a">https</a> '
            '<a href="http://ok.test/b">http</a> '
            '<a href="/rel/path">rel</a> '
            '<a href="#frag">frag</a> '
            '<a href="mailto:hi@ok.test">mail</a>'
            '</p></body></html>')

    def test_dangerous_schemes_dropped_and_counted(self):
        p, ai_html, ai_md = ai_views.build_views(self.HTML, base_url="https://ok.test/page")
        self.assertEqual(p.stats["href_dropped"], 2)      # javascript: + DATA:
        for gone in ("javascript:", "data:", "base64"):
            self.assertNotIn(gone, ai_html)
            self.assertNotIn(gone, ai_md)
        # 白名单存活:http(s) 相对路径经 urljoin 绝对化;mailto 原样;#frag 相对保留
        for kept in ('href="https://ok.test/a"', 'href="http://ok.test/b"',
                     'href="https://ok.test/rel/path"', 'href="mailto:hi@ok.test"',
                     'href="https://ok.test/page#frag"'):
            self.assertIn(kept, ai_html, kept)
        self.assertIn("[https](https://ok.test/a)", ai_md)
        self.assertIn("[rel](https://ok.test/rel/path)", ai_md)
        self.assertIn("[mail](mailto:hi@ok.test)", ai_md)
        self.assertNotIn("[js](", ai_md)                  # 弃置 href 的链接退化为纯文本

    def test_stats_json_carries_counter(self):
        p, _html, _md = ai_views.build_views(self.HTML)
        self.assertEqual(p.stats["href_dropped"], 2)      # blocks 统计随 stats.json 落盘


class CliRejectionTests(unittest.TestCase):
    """CLI 入口:恶意 URL 以非零退出码明确拒绝——拒绝发生在任何网络之前,零网络可测。"""

    @staticmethod
    def run_cli(name, *args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                              capture_output=True, text=True, encoding="utf-8",
                              env=env, timeout=60)

    def test_llmstxt_check_rejects_file_scheme(self):
        r = self.run_cli("llmstxt.py", "check", "file:///etc/passwd")
        self.assertEqual(r.returncode, 2)
        self.assertIn("http(s)", r.stderr)

    def test_llmstxt_generate_rejects_file_sitemap(self):
        r = self.run_cli("llmstxt.py", "generate", "--sitemap", "file:///etc/passwd")
        self.assertEqual(r.returncode, 1)
        self.assertIn("http(s)", r.stderr)

    def test_robots_posture_rejects_file_and_metadata(self):
        r = self.run_cli("robots_posture.py", "file:///etc/passwd")
        self.assertEqual(r.returncode, 1)
        self.assertIn("http(s)", r.stderr)
        r2 = self.run_cli("robots_posture.py", "http://169.254.169.254/robots.txt")
        self.assertEqual(r2.returncode, 1)                # IP 字面量本地判定,零网络
        self.assertIn("169.254.169.254", r2.stderr)

    def test_schema_lint_rejects_file_scheme(self):
        r = self.run_cli("schema_lint.py", "file:///etc/passwd")
        self.assertEqual(r.returncode, 2)
        self.assertIn("http(s)", r.stderr)

    def test_ai_views_rejects_file_scheme(self):
        r = self.run_cli("ai_views.py", "--url", "file:///etc/passwd")
        self.assertEqual(r.returncode, 2)
        self.assertIn("http(s)", r.stdout + r.stderr)

    def test_core_eeat_rejects_metadata_url(self):
        r = self.run_cli("core_eeat.py", "page.html", "--url", "http://169.254.169.254/")
        self.assertEqual(r.returncode, 1)
        self.assertIn("无法读取文档", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
