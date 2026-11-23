#!/usr/bin/env python3
"""轻检对生产站要逐个抓、带间隔;按需渲染的页按位置抽样。

期望值来自一次真实事故:一个多语言站的每周运营单 4 路并发、不停顿地轻检 8,201 个 URL(约每秒 7 个),其中一半
是按需渲染的语种页,每抓一次源站就渲染一次、写一份缓存,20 分钟写了 6G 多,源站根盘到 82% 报警。站点负责人给的
要求:轻检带间隔(默认 0.5 秒,和 sitemap_audit.py 一样),不并发;按需渲染的页按位置抽样,不全量抓。
修前:light_check 没有间隔和抽样参数,请求互相重叠,路径匹配的页全抓。
"""
import http.server
import os
import sys
import threading
import time
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
import ops  # noqa: E402

EN = ["/en/p%d" % i for i in range(4)]
IT = ["/it/p%d" % i for i in range(12)]
CLICKED = "/it/p7"


class Site(http.server.BaseHTTPRequestHandler):
    hits = []                      # (path, 开始, 结束):只记页面请求
    lock = threading.Lock()
    base = ""

    def do_GET(self):  # noqa: N802 — 签名照基类
        if self.path == "/robots.txt":
            return self.reply("text/plain", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % self.base)
        if self.path == "/sitemap.xml":
            locs = "".join("<url><loc>%s%s</loc></url>" % (self.base, p) for p in EN + IT)
            return self.reply("application/xml",
                              '<?xml version="1.0" encoding="UTF-8"?>'
                              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % locs)
        start = time.monotonic()
        time.sleep(0.05)           # 模拟渲染耗时:并发时请求会互相重叠
        self.reply("text/html", '<!doctype html><html><head><title>%s</title><link rel="canonical" href="%s%s">'
                                '</head><body>ok</body></html>' % (self.path, self.base, self.path))
        with self.lock:
            self.hits.append((self.path, start, time.monotonic()))

    def reply(self, ctype, body):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):  # noqa: A002 — 签名照基类
        pass


class LightPacingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Site)
        Site.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        del Site.hits[:]
        cls.light = ops.light_check(Site.base + "/", [Site.base + CLICKED], workers=4, timeout=5,
                                    delay=0.2, samples=ops.parse_samples(["^/it/=4"]))
        cls.hits = sorted(Site.hits, key=lambda h: h[1])

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_one_at_a_time_with_delay(self):
        self.assertGreater(len(self.hits), 1)
        for prev, nxt in zip(self.hits, self.hits[1:]):
            gap = nxt[1] - prev[2]
            self.assertGreaterEqual(gap, 0.15, "%s 在 %s 结束后 %.3f 秒就开始了" % (nxt[0], prev[0], gap))

    def test_matching_pages_sampled_by_position(self):
        got = {h[0] for h in self.hits}
        it_sampled = sorted(p for p in got if p.startswith("/it/") and p != CLICKED)
        self.assertEqual(len(it_sampled), 4)
        self.assertIn("/it/p0", it_sampled)          # 首
        self.assertIn("/it/p11", it_sampled)         # 尾
        self.assertIn(CLICKED, got)                  # GSC 有点击的页不抽,照查
        self.assertTrue(set(EN) <= got)              # 不匹配规则的页全查
        self.assertEqual(self.light["sampled"], [{"rule": "^/it/=4", "total": 11, "checked": 4}])
        self.assertEqual(self.light["sampled_out"], 7)

    def test_sampled_out_pages_do_not_lower_coverage(self):
        self.assertEqual(ops.light_sitemap_coverage(self.light), 1.0)

    def test_defaults_and_bad_rules(self):
        args = ops.build_parser().parse_args(["weekly"])
        self.assertEqual(args.light_delay, 0.5)
        self.assertEqual(args.light_sample, [])
        for bad in ("^/it/", "^/it/=0", "^/it/=x", "[=3"):
            with self.assertRaises(ops.UsageError, msg=bad):
                ops.parse_samples([bad])


if __name__ == "__main__":
    unittest.main()
