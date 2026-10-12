#!/usr/bin/env python3
"""local_audit.py 回归(站型卡④ vertical;stdlib unittest,合成 HTML 打桩,零网络,
standalone——被 run_tests.py 按 test_*.py 自动发现加载)。口径钉死脚本自身契约:
§1 NAP 一致性(NFKC 全半角 / 套房号变体簇剔除 / 电话末 10 位 / 法律后缀);
§2 GBP 抽取(类别/评价数/营业时间块/照片数——抓得到什么查什么,拿不到 unverified);
§3 LocalBusiness 必填六件(name/address/telephone/geo/openingHours/url,host 不符→WARN);
§4 落地页本地信号(city 在 title/H1/正文密度,命中检测走 NFKC 折叠)。
网络打桩:模块级 http_fetch() 单点;SSRF:file:// 在 CLI 层拒(rc 2),
私网/环回/链路本地在 _guard_url 拒。"""
import contextlib
import io
import json
import os
import subprocess
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import local_audit as la  # noqa: E402


def run_cli(argv):
    """进程内跑 main(),返回 (rc, stdout, stderr)。"""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = la.main(argv)
        except SystemExit as e:
            rc = e.code
    return rc, out.getvalue(), err.getvalue()


GOOD_LB = ('{"@context":"https://schema.org","@type":"LocalBusiness",'
           '"name":"Acme Plumbing",'
           '"address":{"@type":"PostalAddress","streetAddress":"123 Main St",'
           '"addressLocality":"Austin","addressRegion":"TX"},'
           '"telephone":"+1-512-555-0100",'
           '"geo":{"@type":"GeoCoordinates","latitude":30.2,"longitude":-97.7},'
           '"openingHours":"Mo-Fr 08:00-18:00","url":"https://example.com/"}')
GOOD_HTML = (
    "<!doctype html><html><head><title>Plumber in Austin | Acme Plumbing</title></head>"
    "<body><h1>Austin Plumbing Services</h1>"
    "<p>Acme Plumbing serves Austin and nearby areas from 123 Main St, Suite 4, "
    "Austin, TX 78701. Call us at (512) 555-0100 for emergency plumbing in Austin TX. "
    "Our Austin team is available 24/7 and Austin homeowners trust us.</p>"
    '<script type="application/ld+json">' + GOOD_LB + "</script>"
    "</body></html>")


def args_for(name="Acme Plumbing LLC", addr="123 Main St, #4, Austin, TX 78701",
             city="Austin", phone="(512) 555-0100", url="https://example.com/"):
    a = ["--url", url, "--name", name, "--addr", addr]
    if city is not None:
        a += ["--city", city]
    if phone is not None:
        a += ["--phone", phone]
    return a


class StubMixin(unittest.TestCase):
    """公共:打桩 http_fetch 返回合成 HTML。"""

    def stub_html(self, html, status=200, final=None):
        orig = la.http_fetch

        def fake(url, timeout=la.FETCH_TIMEOUT, max_bytes=10 ** 9):
            return status, final or url, html

        la.http_fetch = fake
        self.addCleanup(setattr, la, "http_fetch", orig)


class LocalAuditCliTests(StubMixin):
    def test_help_smoke(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "local_audit.py"),
                            "--help"], capture_output=True, text=True,
                           encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("NAP", r.stdout)

    def test_file_scheme_rejected(self):
        rc, _, err = run_cli(args_for(url="file:///etc/passwd"))
        self.assertEqual(rc, 2)
        self.assertIn("仅接受 http(s)", err)

    def test_dash_n_alias_accepted(self):
        self.stub_html(GOOD_HTML)
        rc, out, _ = run_cli(["--url", "https://example.com/", "--n", "Acme Plumbing",
                              "--addr", "123 Main St, Suite 4, Austin, TX 78701"])
        self.assertEqual(rc, 0, out)
        self.assertIn("nap.name", out)


class NapTests(StubMixin):
    """§1 NAP:全绿 / 全半角+套房号变体 / 地址失配 FAIL / 部分匹配 WARN /
    电话一致与失配 / 店名缺失"""

    def test_nap_all_pass_exit0(self):
        self.stub_html(GOOD_HTML)
        rc, out, _ = run_cli(args_for())
        self.assertEqual(rc, 0, out)
        self.assertIn("页内店名一致(acme plumbing)", out)      # LLC 法律后缀已剥
        self.assertIn("套房号已归一", out)
        self.assertIn("页内电话一致(末 10 位 5125550100)", out)
        self.assertIn("PASS(退出码 0)", out)

    def test_fullwidth_and_suite_variant_normalized(self):
        html = ("<html><head><title>配管のＡｕｓｔｉｎ店</title></head><body>"
                "<h1>Ａｃｍｅ Ｐｌｕｍｂｉｎｇ</h1>"
                "<p>Ａｃｍｅ Ｐｌｕｍｂｉｎｇ ｜ １２３ Ｍａｉｎ Ｓｔ，Ｓｕｉｔｅ ４，"
                " Ａｕｓｔｉｎ， ＴＸ ７８７０１ ☎ ＋１－５１２－５５５－０１００ "
                "serving Ａｕｓｔｉｎ area.</p>"
                '<script type="application/ld+json">' + GOOD_LB + "</script>"
                "</body></html>")
        self.stub_html(html)
        rc, out, _ = run_cli(args_for(name="Acme Plumbing", addr="123 Main St, #4"))
        self.assertEqual(rc, 0, out)
        self.assertIn("页内店名一致", out)                       # 全角 Ａｃｍｅ ≡ ASCII
        self.assertIn("页内地址一致", out)                       # Ｓｕｉｔｅ ４ ≡ #4(全半角+簇剔)
        self.assertIn("页内电话一致", out)                       # ＋１ 全角数字 → NFKC

    def test_address_mismatch_fail(self):
        self.stub_html(GOOD_HTML)
        rc, out, _ = run_cli(args_for(addr="999 Oak Ave, Austin, TX"))
        self.assertEqual(rc, 1, out)
        self.assertIn("✗ nap.address", out)
        self.assertIn("999 oak ave", out)                       # 缺 token 逐个列出

    def test_address_partial_match_warn(self):
        self.stub_html(GOOD_HTML)
        rc, out, _ = run_cli(args_for(addr="123 Main St, Austin, TX 78702"))
        self.assertIn("⚠ nap.address", out)
        self.assertIn("地址部分匹配 83%", out)                   # 5/6 token(仅邮编差)
        self.assertEqual(rc, 0, out)                            # WARN 不拉退出码

    def test_phone_mismatch_fail(self):
        self.stub_html(GOOD_HTML)
        rc, out, _ = run_cli(args_for(phone="212-555-0000"))
        self.assertEqual(rc, 1, out)
        self.assertIn("2125550000 不在页内候选", out)

    def test_phone_absent_on_page_fail(self):
        self.stub_html(GOOD_HTML.replace("(512) 555-0100", ""))
        rc, out, _ = run_cli(args_for())
        self.assertEqual(rc, 1, out)
        self.assertIn("页内未检出任何电话", out)

    def test_name_missing_fail(self):
        self.stub_html(GOOD_HTML)
        rc, out, _ = run_cli(args_for(name="Zenith Roofing"))
        self.assertEqual(rc, 1, out)
        self.assertIn("页内未见店名", out)


class GbpTests(StubMixin):
    """§2 GBP:四项可抽→PASS / 抽不到→unverified 不 FAIL / 非 GBP URL→整节 unverified"""

    GBP_URL = "https://www.google.com/maps/place/Acme+Plumbing"

    def test_gbp_extraction_pass(self):
        html = ('<html><body>"category": "Plumber"'
                "<h1>Acme Plumbing</h1>327 reviews · 48 photos"
                "<table><tr><td>Monday</td><td>Tuesday</td><td>Wednesday</td>"
                "<td>Thursday</td><td>Friday</td><td>Saturday</td><td>Sunday</td></tr></table>"
                "<p>123 Main St, Austin, TX 78701 · (512) 555-0100</p></body></html>")
        self.stub_html(html)
        rc, out, _ = run_cli(args_for(url=self.GBP_URL, name="Acme Plumbing",
                                      addr="123 Main St, Austin, TX 78701",
                                      phone="+1 512 555 0100"))
        self.assertEqual(rc, 0, out)
        self.assertIn("类别: Plumber", out)
        self.assertIn("评价数: 327", out)
        self.assertIn("营业时间块在场", out)
        self.assertIn("照片数: 48", out)
        self.assertIn("(GBP 页)", out)                          # url_type 标注

    def test_gbp_unverified_not_failed(self):
        self.stub_html("<html><body>Before you continue to Google Maps. "
                       "Acme 123 Main St</body></html>")
        rc, out, _ = run_cli(args_for(url=self.GBP_URL, name="Acme",
                                      addr="123 Main St", city=None, phone=None))
        self.assertEqual(rc, 0, out)
        self.assertIn("未抓到类别", out)
        self.assertIn("未抓到评价数", out)
        self.assertIn("未抓到照片数", out)
        self.assertIn("0 ✗ / 8 unverified", out)               # 抓不到 ≠ FAIL

    def test_website_url_gbp_section_unverified(self):
        self.stub_html(GOOD_HTML)
        rc, out, _ = run_cli(args_for())
        self.assertEqual(rc, 0, out)
        self.assertIn("非 GBP 页", out)                         # 逐项转 unverified
        self.assertIn("需用 GBP 页 URL 复核", out)


class SchemaTests(StubMixin):
    """§3 schema:六件全齐 / 缺 geo+openingHours / host 不符 WARN / 无 schema FAIL / 子类识别"""

    def test_schema_complete_six_fields(self):
        self.stub_html(GOOD_HTML)
        rc, out, _ = run_cli(args_for())
        self.assertEqual(rc, 0, out)
        for fid in ("schema.name", "schema.address", "schema.telephone",
                    "schema.geo", "schema.openingHours", "schema.url"):
            self.assertIn("✓ %s" % fid, out)

    def test_schema_missing_geo_and_openinghours_fail(self):
        bad = GOOD_LB.replace(
            '"geo":{"@type":"GeoCoordinates","latitude":30.2,"longitude":-97.7},', ""
        ).replace('"openingHours":"Mo-Fr 08:00-18:00",', "")
        self.stub_html(GOOD_HTML.replace(GOOD_LB, bad))
        rc, out, _ = run_cli(args_for())
        self.assertEqual(rc, 1, out)
        self.assertIn("LocalBusiness 缺必填 geo", out)
        self.assertIn("LocalBusiness 缺必填 openingHours", out)

    def test_schema_url_host_mismatch_warn(self):
        bad = GOOD_LB.replace('"url":"https://example.com/"',
                              '"url":"https://other.example/x"')
        self.stub_html(GOOD_HTML.replace(GOOD_LB, bad))
        rc, out, _ = run_cli(args_for())
        self.assertIn("⚠ schema.url", out)
        self.assertIn("other.example ≠ 页面 host example.com", out)
        self.assertEqual(rc, 0, out)

    def test_no_schema_fail(self):
        self.stub_html("<html><head><title>t</title></head><body><h1>h</h1>"
                       "<p>plain</p></body></html>")
        rc, out, _ = run_cli(args_for())
        self.assertEqual(rc, 1, out)
        self.assertIn("页内未见 LocalBusiness", out)

    def test_subtype_dentist_recognized(self):
        lb = ('{"@context":"https://schema.org","@type":"Dentist","name":"Smile",'
              '"address":{"streetAddress":"1 A St"},"telephone":"+1-512-555-0100",'
              '"geo":{"latitude":1,"longitude":2},"openingHours":"Mo-Fr 09:00-17:00",'
              '"url":"https://example.com/"}')
        self.stub_html('<html><head><title>t</title></head><body><h1>h</h1>'
                       "<p>Smile, 1 A St. Call (512) 555-0100.</p>"
                       '<script type="application/ld+json">%s</script></body></html>' % lb)
        rc, out, _ = run_cli(args_for(name="Smile", addr="1 A St",
                                      phone="512-555-0100", city=None))
        self.assertEqual(rc, 0, out)


class LocalSignalTests(StubMixin):
    """§4 本地信号:city 命中三处 / 正文零提及 FAIL / city 未知 unverified"""

    def test_city_signals_all_hit(self):
        self.stub_html(GOOD_HTML)
        rc, out, _ = run_cli(args_for())
        self.assertEqual(rc, 0, out)
        self.assertIn("✓ local.title", out)
        self.assertIn("✓ local.h1", out)
        self.assertIn("✓ local.density", out)
        self.assertIn("次/千字符", out)

    def test_city_zero_density_fail(self):
        self.stub_html(GOOD_HTML)
        rc, out, _ = run_cli(args_for(city="Dallas"))
        self.assertEqual(rc, 1, out)
        self.assertIn("✗ local.density", out)
        self.assertIn("doorway 形态", out)
        self.assertIn("⚠ local.title", out)                     # title 无 Dallas → WARN

    def test_city_unknown_unverified(self):
        self.stub_html(GOOD_HTML)
        rc, out, _ = run_cli(args_for(addr="123 Main St", city=None))
        self.assertEqual(rc, 0, out)
        self.assertIn("city 未知", out)


class JsonAndGuardTests(StubMixin):
    """--json 结构 / SSRF 私网拒 / GBP 页 §3§4 转 unverified"""

    def test_json_output_shape(self):
        self.stub_html(GOOD_HTML)
        out_io, err_io = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out_io), contextlib.redirect_stderr(err_io):
            rc = la.main(args_for() + ["--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out_io.getvalue())
        self.assertEqual(data["tool"], "local_audit")
        self.assertEqual([s["id"] for s in data["sections"]],
                         ["nap", "gbp", "schema", "local"])
        self.assertEqual(data["counts"]["fail"], 0)
        self.assertEqual(data["url_type"], "website")

    def test_ssrf_private_addresses_rejected(self):
        orig = la.socket.getaddrinfo
        la.socket.getaddrinfo = lambda host, *a, **k: [(2, 1, 6, "", (host, 0))]
        try:
            for evil in ("http://169.254.169.254/latest/meta-data",
                         "http://127.0.0.1:8080/x", "https://10.0.0.5/internal"):
                with self.assertRaises(la.FetchError):
                    la._guard_url(evil)
        finally:
            la.socket.getaddrinfo = orig

    def test_gbp_page_schema_and_local_unverified(self):
        self.stub_html("<html><body><h1>Acme</h1>"
                       "<p>Acme, 123 Main St, Austin, TX 78701</p></body></html>")
        rc, out, _ = run_cli(args_for(url="https://www.google.com/maps/place/Acme",
                                      name="Acme", addr="123 Main St, Austin, TX 78701",
                                      city=None, phone=None))
        self.assertEqual(rc, 0, out)
        self.assertIn("GBP 页不承载站内 JSON-LD", out)
        self.assertIn("GBP 页不承载落地页信号", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
