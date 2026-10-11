#!/usr/bin/env python3
"""indexnow.py 测试(R2-5 之一:零 key 秒收协议提交器)。零网络:_http_post 打桩
(唯一网络出口);CLI 拒绝路径用 subprocess(校验发生在任何网络之前)。
覆盖:
  ① key 子命令:uuid4 形态(32 位小写 hex)/协议字符集校验/--out 写 {key}.txt
     (内容恰为 key,无尾换行)/部署指引含根目录 {key}.txt
  ② SSRF 白名单:四个内置端点放行;http://、白名单域后缀伪装(evil.com)、
     非白名单域拒
  ③ URL 收集:文件 # 注释/空行跳过、去重、空清单用法错、跨 host URL 本地先拒
     (引擎 422 的主因;拒在触网之前——打桩断言"不应触网")
  ④ POST 载荷:{host,key,keyLocation=https://host/{key}.txt,urlList} 逐字段;
     --endpoint 别名路由到引擎专属端点(官方 meta.json 口径)
  ⑤ 响应判读:200/202=ok(202 附 key 校验说明);422=key 未部署提示(含 {key}.txt
     指引);429=限速;403/400/意外码=失败;URLError→网络错误批(exit 1)
  ⑥ 批次:25000 URL 按 10000 上限分 3 批
  ⑦ Google 口径注释在场(docstring + --json note_google)
用法: python3 tests/test_indexnow.py(tests/run_tests.py 自动发现本文件)"""
import contextlib
import io
import os
import re
import subprocess
import sys
import unittest
import urllib.error
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import indexnow as IN   # noqa: E402 (需先入 SCRIPTS 路径)

KEY = "a1b2c3d4e5f60718293a4b5c6d7e8f90"      # 32 位 hex,uuid4 形态


def run_cli(*args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "indexnow.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)


class _StubPoster:
    """_http_post 打桩:记录 (url, payload),按序回 canned 状态码。"""

    def __init__(self, statuses=(200,)):
        self.statuses = list(statuses)
        self.calls = []

    def __call__(self, url, payload, timeout=IN.DEFAULT_TIMEOUT):
        self.calls.append((url, payload))
        return self.statuses.pop(0) if self.statuses else 200


def run_main(argv):
    """in-process main():捕获 stdout/stderr,返回 (rc, out, err)。"""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = IN.main(argv)
    return rc, out.getvalue(), err.getvalue()


class KeyCommandTests(unittest.TestCase):
    """① key 子命令:形态/部署指引/--out 写文件。"""

    def test_generate_key_shape(self):
        key = IN.generate_key()
        self.assertEqual(len(key), 32)
        self.assertRegex(key, r"^[0-9a-f]{32}$")           # uuid4().hex
        self.assertIs(IN.validate_key(key), key)           # 通过协议校验
        self.assertIs(IN.validate_key(KEY), KEY)
        # uuid 带连字符形态(36 位)也在协议字符集内
        self.assertIs(IN.validate_key("a1b2c3d4-e5f6-0718-293a-4b5c6d7e8f90"),
                      "a1b2c3d4-e5f6-0718-293a-4b5c6d7e8f90")

    def test_validate_key_rejects(self):
        for bad in ("", "short", "有中文!", "a" * 129, "space inside"):
            with self.assertRaises(IN.UsageError, msg=repr(bad)):
                IN.validate_key(bad)

    def test_key_cli_guidance_and_out_file(self):
        r = run_cli("key", "--json")
        self.assertEqual(r.returncode, 0)
        self.assertIn("IndexNow key:", r.stdout)
        m = re.search(r"IndexNow key: ([0-9a-f]{32})", r.stdout)
        self.assertTrue(m)
        key = m.group(1)
        self.assertIn("/%s.txt" % key, r.stdout)            # 根目录放置指引
        self.assertIn("内容恰为 key", r.stdout)
        self.assertIn("Google 不支持", r.stdout)             # 口径注释随 key 输出
        # --out:写出 {key}.txt,内容恰为 key(无尾换行)
        with tempfile.TemporaryDirectory() as d:
            r2 = run_cli("key", "--out", d)
            self.assertEqual(r2.returncode, 0)
            files = os.listdir(d)
            self.assertEqual(len(files), 1)
            self.assertTrue(files[0].endswith(".txt"))
            with open(os.path.join(d, files[0]), encoding="utf-8") as f:
                self.assertEqual(f.read(), files[0][:-4])   # 文件名去掉 .txt == 内容


class GuardTests(unittest.TestCase):
    """② SSRF 端点白名单(零网络,纯 URL 判定)。"""

    def test_builtin_endpoints_allowed(self):
        for url in IN.ENDPOINTS.values():
            self.assertTrue(IN.guard_endpoint(url), url)

    def test_evil_endpoints_rejected(self):
        for evil in ("http://api.indexnow.org/indexnow",          # 非 https
                     "https://evil.example.com/indexnow",         # 非白名单域
                     "https://api.indexnow.org.evil.com/x",       # 白名单域做后缀伪装
                     "https://evil-bing.com/indexnow",            # 连字符伪装(精确匹配才放行)
                     "file:///etc/passwd",                        # 非 http(s)
                     ""):
            with self.assertRaises(IN.GuardError, msg=evil):
                IN.guard_endpoint(evil)


class UrlCollectionTests(unittest.TestCase):
    """③ URL 收集与属主预检(全部拒在触网之前)。"""

    def test_load_urls_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as f:
            f.write("# 注释\n"
                    "https://example.com/a\n"
                    "\n"
                    "https://example.com/a\n"          # 去重
                    "https://example.com/b\n")
            path = f.name
        try:
            self.assertEqual(IN.collect_urls([], path),
                             ["https://example.com/a", "https://example.com/b"])
        finally:
            os.unlink(path)

    def test_collect_urls_empty_usage_error(self):
        with self.assertRaises(IN.UsageError):
            IN.collect_urls([], None)
        with self.assertRaises(IN.UsageError):           # 文件里全是注释/空行
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                             encoding="utf-8") as f:
                f.write("# only comment\n\n")
                path = f.name
            try:
                IN.collect_urls([], path)
            finally:
                os.unlink(path)

    def test_missing_urls_file_usage_error(self):
        with self.assertRaises(IN.UsageError):
            IN.load_urls_file("/nonexistent/urls.txt")

    def test_host_mismatch_rejected_before_network(self):
        """跨 host URL 本地先拒(引擎 422 主因);打桩断言全程未触网。"""
        orig = IN._http_post
        IN._http_post = lambda *a, **k: (_ for _ in ()).throw(
            AssertionError("不应触网:属主校验必须发生在网络之前"))
        try:
            rc, _out, err = run_main(["submit", "--host", "example.com", "--key", KEY,
                                      "--url", "https://example.com/ok",
                                      "--url", "https://other.com/bad"])
        finally:
            IN._http_post = orig
        self.assertEqual(rc, 2)
        self.assertIn("不属于 host example.com", err)
        self.assertIn("https://other.com/bad", err)

    def test_normalize_host(self):
        self.assertEqual(IN.normalize_host("Example.com"), "example.com")
        self.assertEqual(IN.normalize_host("https://example.com/"), "example.com")
        for bad in ("", "example.com/path", "https://example.com/x?q=1", "ftp://x"):
            with self.assertRaises(IN.UsageError, msg=repr(bad)):
                IN.normalize_host(bad)


class SubmitPayloadTests(unittest.TestCase):
    """④ POST 载荷与端点路由(打桩 _http_post)。"""

    def _run_submit(self, stub, extra=()):
        orig = IN._http_post
        IN._http_post = stub
        try:
            return run_main(["submit", "--host", "example.com", "--key", KEY,
                             "--url", "https://example.com/a",
                             "--url", "https://example.com/b", *extra])
        finally:
            IN._http_post = orig

    def test_payload_fields_and_key_location(self):
        stub = _StubPoster(statuses=[200])
        rc, out, _ = self._run_submit(stub)
        self.assertEqual(rc, 0)
        url, payload = stub.calls[0]
        self.assertEqual(url, "https://api.indexnow.org/indexnow")     # 默认共享端点
        self.assertEqual(payload["host"], "example.com")
        self.assertEqual(payload["key"], KEY)
        self.assertEqual(payload["keyLocation"], "https://example.com/%s.txt" % KEY)
        self.assertEqual(payload["urlList"], ["https://example.com/a",
                                              "https://example.com/b"])

    def test_endpoint_aliases(self):
        for alias, expected in (("naver", "https://searchadvisor.naver.com/indexnow"),
                                ("bing", "https://www.bing.com/indexnow"),
                                ("yandex", "https://yandex.com/indexnow")):
            stub = _StubPoster(statuses=[200])
            rc, _out, _err = self._run_submit(stub, extra=["--endpoint", alias])
            self.assertEqual(rc, 0)
            self.assertEqual(stub.calls[0][0], expected)

    def test_batches_chunked_at_10000(self):
        urls = ["https://example.com/p%d" % i for i in range(25000)]
        stub = _StubPoster(statuses=[200, 200, 200])
        orig = IN._http_post
        IN._http_post = stub
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                             encoding="utf-8") as f:
                f.write("\n".join(urls))
                path = f.name
            try:
                rc, out, _err = run_main(["submit", "--host", "example.com", "--key", KEY,
                                          "--urls", path, "--json"])
            finally:
                os.unlink(path)
        finally:
            IN._http_post = orig
        self.assertEqual(rc, 0)
        self.assertEqual([len(c[1]["urlList"]) for c in stub.calls],
                         [10000, 10000, 5000])                        # 协议上限分批
        import json as _json
        data = _json.loads(out)
        self.assertEqual(data["submitted_urls"], 25000)
        self.assertEqual(data["failed_batches"], 0)
        self.assertEqual([b["status"] for b in data["batches"]], [200, 200, 200])


class StatusVerdictTests(unittest.TestCase):
    """⑤ 协议响应码判读(200/202=ok;422 key 未部署;429 限速)。"""

    def test_verdict_for_status(self):
        ok_codes = (200, 202)
        for code in ok_codes:
            verdict, note = IN.verdict_for_status(code)
            self.assertEqual(verdict, "ok", code)
        v, note = IN.verdict_for_status(202)
        self.assertIn("key 校验", note)                              # 202 附校验说明
        v422, note422 = IN.verdict_for_status(422, "example.com", KEY)
        self.assertEqual(v422, "fail")
        self.assertIn("key 未部署", note422)
        self.assertIn("https://example.com/%s.txt" % KEY, note422)    # 指到具体 key 文件
        v429, note429 = IN.verdict_for_status(429)
        self.assertEqual(v429, "fail")
        self.assertIn("限速", note429)
        for code in (400, 403, 500):
            self.assertEqual(IN.verdict_for_status(code)[0], "fail", code)

    def test_submit_202_is_ok_exit_0(self):
        stub = _StubPoster(statuses=[202])
        orig = IN._http_post
        IN._http_post = stub
        try:
            rc, out, err = run_main(["submit", "--host", "example.com", "--key", KEY,
                                     "--url", "https://example.com/a"])
        finally:
            IN._http_post = orig
        self.assertEqual(rc, 0)                                      # 202 计 ok
        self.assertIn("202", out)
        self.assertIn("key 校验", out)

    def test_submit_429_fails_exit_1(self):
        stub = _StubPoster(statuses=[429])
        orig = IN._http_post
        IN._http_post = stub
        try:
            rc, out, err = run_main(["submit", "--host", "example.com", "--key", KEY,
                                     "--url", "https://example.com/a"])
        finally:
            IN._http_post = orig
        self.assertEqual(rc, 1)
        self.assertIn("限速", out)

    def test_submit_422_hints_key_file(self):
        stub = _StubPoster(statuses=[422])
        orig = IN._http_post
        IN._http_post = stub
        try:
            rc, out, err = run_main(["submit", "--host", "example.com", "--key", KEY,
                                     "--url", "https://example.com/a"])
        finally:
            IN._http_post = orig
        self.assertEqual(rc, 1)
        self.assertIn("key 未部署", out)
        self.assertIn("https://example.com/%s.txt" % KEY, out)       # 指到具体文件

    def test_submit_network_error_exit_1(self):
        def boom(url, payload, timeout=IN.DEFAULT_TIMEOUT):
            raise urllib.error.URLError("connection refused")
        orig = IN._http_post
        IN._http_post = boom
        try:
            rc, out, err = run_main(["submit", "--host", "example.com", "--key", KEY,
                                     "--url", "https://example.com/a", "--json"])
        finally:
            IN._http_post = orig
        self.assertEqual(rc, 1)
        import json as _json
        data = _json.loads(out)
        self.assertEqual(data["ok"], False)
        self.assertEqual(data["batches"][0]["verdict"], "network_error")

    def test_submit_json_masks_key_and_notes_google(self):
        stub = _StubPoster(statuses=[200])
        orig = IN._http_post
        IN._http_post = stub
        try:
            rc, out, _ = run_main(["submit", "--host", "example.com", "--key", KEY,
                                   "--url", "https://example.com/a", "--json"])
        finally:
            IN._http_post = orig
        import json as _json
        data = _json.loads(out)
        self.assertNotIn(KEY, data["key"])                           # key 打码不泄
        self.assertIn("Google 不支持", data["note_google"])           # 口径注释在场


class GoogleNoteTests(unittest.TestCase):
    """⑦ Google 不支持 IndexNow 的口径注释(套件事实,防误当 Google 通道)。"""

    def test_docstring_and_cli_carry_note(self):
        self.assertIn("Google 不支持", IN.__doc__)
        self.assertIn("Google 不支持", IN.NOTE_GOOGLE)
        for args in (["--help"], ["submit", "--help"]):
            r = run_cli(*args)
            self.assertIn("Google 不支持", r.stdout + r.stderr, args)


if __name__ == "__main__":
    unittest.main(verbosity=1)
