#!/usr/bin/env python3
"""head_check.py 回归测试(B21–B25;stdlib unittest,合成 HTML,本机回环 HTTP,零外网)。

期望值来源(一手原文,2026-10-21 读取):
- B21:Googlebot 抓取一般不带 Accept-Language;按语言跳转的站会把 / 302 到 /en。
  脚本契约:审的是哪个 URL 就报哪个 URL——最终 URL ≠ 请求 URL 时必须明说。
- B22:X Cards markup「Tag Reference」表逐行列出 OpenGraph 回落:twitter:title→og:title、
  twitter:description→og:description、twitter:image→og:image(Wayback 2026-02-01 存档)。
  回落 ≠ 弃用:有 OG 时 twitter:* 冗余可省,最多 INFO,不得让退出码变 1。
- B23:Google「Meta tags and attributes that Google supports」列表无 geo.* / ICBM,且
  「Google will ignore meta tags that it doesn't support」→ 缺失不 WARN。
- B24:显式 --market 优先于内容自动识别。
- B25:WHATWG「The element containing the character encoding declaration must be
  serialized completely within the first 1024 bytes of the document」——唯一位置硬约束;
  其余顺序无 SEO 依据,最多 INFO。
"""
import http.server
import os
import subprocess
import sys
import threading
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(BASE, "scripts", "head_check.py")


def run_head(html, *extra):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, SCRIPT, "-", *extra], input=html,
                          capture_output=True, text=True, encoding="utf-8", env=env)


def lines_with(stdout, level):
    return [ln for ln in stdout.splitlines() if ln.startswith(f"[{level}")]


HEAD_OK = ('<meta charset="utf-8"><meta name="viewport" content="width=device-width">'
           '<title>Example API Platform</title>')


class AcceptLanguageAndRedirectTests(unittest.TestCase):
    """B21:不发 Accept-Language;被重定向时报告最终 URL。"""

    @classmethod
    def setUpClass(cls):
        seen = cls.seen = []

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                seen.append((self.path, self.headers.get("Accept-Language")))
                if self.path == "/":
                    self.send_response(302)
                    self.send_header("Location", "/en")
                    self.end_headers()
                    return
                body = (f'<!doctype html><html lang="en"><head>{HEAD_OK}'
                        '<meta property="og:image" content="https://example.com/i.png">'
                        '</head><body><p>hello</p></body></html>').encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        cls.srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_no_accept_language_and_final_url_reported(self):
        self.seen.clear()
        url = f"http://127.0.0.1:{self.port}/"
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, SCRIPT, url], capture_output=True, text=True,
                           encoding="utf-8", env=env)
        self.assertTrue(self.seen, r.stderr)
        for path, al in self.seen:
            self.assertIsNone(al, f"{path} 收到 Accept-Language={al}")   # 修前发 en,zh;q=0.8
        final = f"http://127.0.0.1:{self.port}/en"
        self.assertIn(final, r.stdout)                                     # 修前只报请求 URL
        self.assertIn("最终 URL", r.stdout)


class TwitterCardTests(unittest.TestCase):
    """B22:twitter:* 不是弃用。"""

    def test_twitter_with_og_is_not_error(self):
        html = (f'<!doctype html><html lang="en"><head>{HEAD_OK}'
                '<meta property="og:title" content="T"><meta property="og:description" content="D">'
                '<meta property="og:image" content="https://example.com/i.png">'
                '<meta name="twitter:card" content="summary_large_image">'
                '<meta name="twitter:title" content="T"><meta name="twitter:description" content="D">'
                '<meta name="twitter:image" content="https://example.com/i.png">'
                '</head><body></body></html>')
        r = run_head(html)
        self.assertEqual(r.returncode, 0, r.stdout)                         # 修前 1
        errs = [ln for ln in lines_with(r.stdout, "ERROR") if "twitter" in ln]
        warns = [ln for ln in lines_with(r.stdout, "WARN") if "twitter" in ln]
        self.assertEqual(errs + warns, [])
        self.assertNotIn("twitter:* 卡片全套冗余", r.stdout)

    def test_twitter_without_og_not_flagged(self):
        # 没有 OG 时 twitter:title 就是 X 唯一的来源,不能建议删除
        html = (f'<!doctype html><html lang="en"><head>{HEAD_OK}'
                '<meta name="twitter:title" content="T">'
                '</head><body></body></html>')
        r = run_head(html)
        self.assertEqual([ln for ln in r.stdout.splitlines() if "twitter:title" in ln
                          and ("ERROR" in ln or "WARN" in ln or "冗余" in ln or "弃用" in ln)], [])


class GeoMetaTests(unittest.TestCase):
    """B23:geo meta 缺失不 WARN。"""

    def test_missing_geo_not_warn(self):
        html = (f'<!doctype html><html lang="en"><head>{HEAD_OK}'
                '<meta property="og:image" content="https://example.com/i.png"></head><body></body></html>')
        r = run_head(html)
        self.assertEqual([ln for ln in lines_with(r.stdout, "WARN") if "geo" in ln.lower()], [])
        self.assertEqual([ln for ln in lines_with(r.stdout, "ERROR") if "geo" in ln.lower()], [])


class ExplicitMarketTests(unittest.TestCase):
    """B24:显式 --market 优先于自动识别中文。"""

    HTML = ('<!doctype html><html><head>' + HEAD_OK +
            '<meta property="og:image" content="https://example.com/i.png"></head><body>'
            '<p>Language: English | Español | 简体中文</p>'
            '<p>客户评价:这个接口很稳定,响应速度很快,我们团队已经用了一年多了。</p></body></html>')

    def test_market_en_skips_wechat(self):
        for m in ("en", "es"):
            r = run_head(self.HTML, "--market", m)
            self.assertNotIn("微信/QQ 分享 itemprop", r.stdout, m)          # 修前 WARN

    def test_auto_detect_still_works_without_market(self):
        r = run_head(self.HTML)
        self.assertIn("微信/QQ 分享 itemprop", r.stdout)                   # 不传 --market 时仍按内容识别


class OrderTests(unittest.TestCase):
    """B25:顺序只 INFO;charset 超 1024 字节仍是 ERROR。"""

    def test_meta_before_title_is_info(self):
        html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="description" content="d"><meta property="og:title" content="t">'
                '<title>Example</title><meta name="viewport" content="width=device-width">'
                '<meta property="og:image" content="https://example.com/i.png"></head><body></body></html>')
        r = run_head(html)
        self.assertEqual([ln for ln in lines_with(r.stdout, "WARN") if "顺序" in ln], [])
        self.assertEqual([ln for ln in lines_with(r.stdout, "ERROR") if "顺序" in ln], [])
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_charset_beyond_1024_still_error(self):
        pad = "<!-- " + "x" * 1100 + " -->"
        html = (f'<!doctype html><html lang="en"><head>{pad}<meta charset="utf-8">'
                '<title>Example</title><meta name="viewport" content="width=device-width">'
                '</head><body></body></html>')
        r = run_head(html)
        self.assertEqual(r.returncode, 1)
        self.assertTrue([ln for ln in lines_with(r.stdout, "ERROR") if "charset" in ln])


if __name__ == "__main__":
    unittest.main(verbosity=2)
