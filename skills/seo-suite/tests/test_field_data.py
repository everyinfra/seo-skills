#!/usr/bin/env python3
"""field_data.py golden 用例(stdlib unittest,合成 PSI/CrUX 响应,fetch 全打桩零网络)。
覆盖:PSI 现场 vs 实验分开解析(CLS 百分之一表示 ÷100)/ CrUX p75 解析(2 位小数字符串)
与无 key 整源跳过 / 官方阈值边界(2.5s·200ms·0.1 含等号)/ --as-cwv-csv 被
traffic_funnel.py --cwv 实际接受的端到端 / 批量 --delay 礼貌间隔 / 退出码矩阵(0/1/2/3)/
429 配额提示 / SSRF 输入拒绝。独立可运行:python3 tests/test_field_data.py;
也被 run_tests.py 自动发现(tests/test_*.py)。"""
import contextlib
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import field_data as fd  # noqa: E402  (import 后无任何网络副作用)


def tmp_file(content, suffix=".csv"):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def http_err(code, msg, body=b""):
    return urllib.error.HTTPError("https://api.test/x", code, msg, {}, io.BytesIO(body))


def psi_payload(lcp=1200, cls_score=5, inp=120, ttfb=600, fcp=900,
                lab_lcp=1100, lab_cls=0.02, lab_tbt=150, lab_fcp=800,
                lab_inp=None, perf=0.95, field=True):
    """合成 PSI v5 响应:loadingExperience=现场(CrUX 页级 p75;CLS 为百分之一表示),
    lighthouseResult.audits=实验(numericValue 毫秒/小数 + score 0-1)。"""
    audits = {"largest-contentful-paint": {"numericValue": lab_lcp, "score": 0.9},
              "cumulative-layout-shift": {"numericValue": lab_cls, "score": 1},
              "total-blocking-time": {"numericValue": lab_tbt, "score": 0.95},
              "first-contentful-paint": {"numericValue": lab_fcp, "score": 0.9}}
    if lab_inp is not None:
        audits["experimental-interaction-to-next-paint"] = {"numericValue": lab_inp, "score": 0.9}
    out = {"lighthouseResult": {"categories": {"performance": {"score": perf}}, "audits": audits}}
    if field:
        out["loadingExperience"] = {
            "id": "https://example.com/", "overall_category": "FAST", "metrics": {
                "LARGEST_CONTENTFUL_PAINT_MS": {"percentile": lcp, "category": "FAST"},
                "CUMULATIVE_LAYOUT_SHIFT_SCORE": {"percentile": cls_score, "category": "FAST"},
                "INTERACTION_TO_NEXT_PAINT": {"percentile": inp, "category": "FAST"},
                "EXPERIMENT_TIME_TO_FIRST_BYTE": {"percentile": ttfb, "category": "AVERAGE"},
                "FIRST_CONTENTFUL_PAINT_MS": {"percentile": fcp, "category": "FAST"}}}
    else:
        out["loadingExperience"] = {"overall_category": "NONE", "metrics": {}}
    return out


def crux_payload(lcp=2063, cls="0.23", inp=180, ttfb=700, fcp=1200, list_form=False):
    """合成 CrUX records:queryRecord 响应:percentiles.p75;CLS 官方为 2 位小数字符串。"""
    def pc(v):
        return [{"percentile": 0.75, "p75": v}] if list_form else {"p75": v}
    return {"record": {"key": {"url": "https://example.com/", "formFactor": "PHONE"},
                       "metrics": {
                           "largest_contentful_paint": {"histogram": [], "percentiles": pc(lcp)},
                           "cumulative_layout_shift": {"percentiles": pc(cls)},
                           "interaction_to_next_paint": {"percentiles": pc(inp)},
                           "experimental_time_to_first_byte": {"percentiles": pc(ttfb)},
                           "first_contentful_paint": {"percentiles": pc(fcp)}},
                       "collectionPeriod": {"firstDate": {"year": 2026, "month": 9, "day": 14},
                                            "lastDate": {"year": 2026, "month": 10, "day": 11}}}}


def psi_responder_by_url(spec, default=None):
    """按查询串里的 url= 参数路由到不同合成响应(urlencode 往返同时被验证)。"""
    def respond(url, payload=None):
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        target = q.get("url", [""])[0]
        if target in spec:
            out = spec[target]
        elif default is not None:
            out = default
        else:
            raise AssertionError("意外的 PSI 查询: %s" % target)
        if isinstance(out, Exception):
            raise out
        return out
    return respond


class _FakeTime:
    def __init__(self):
        self.sleeps = []

    def sleep(self, s):
        self.sleeps.append(s)


class FieldHarness(unittest.TestCase):
    """进程内跑 fd.main():fetch_json/ssrf_guard/time 全打桩,stdout/stderr 重定向。"""

    def setUp(self):
        self._saved = (fd.fetch_json, fd.ssrf_guard, fd.time)
        self._env = {k: os.environ.pop(k) for k in ("PSI_API_KEY", "CRUX_API_KEY")
                     if k in os.environ}
        self.calls = []
        self.fake_time = _FakeTime()
        fd.time = self.fake_time
        fd.ssrf_guard = lambda host: None            # 零网络:不做 DNS
        fd._ssrf_cache.clear()

    def tearDown(self):
        fd.fetch_json, fd.ssrf_guard, fd.time = self._saved
        fd._ssrf_cache.clear()
        os.environ.update(self._env)

    def stub(self, psi=None, crux=None):
        def fake(url, payload=None, timeout=fd.DEFAULT_TIMEOUT):
            self.calls.append(url)
            responder = psi if payload is None else crux
            if responder is None:
                raise AssertionError("不该发生的请求: %s %s" % (url, payload))
            out = responder(url, payload)
            if isinstance(out, Exception):
                raise out
            return out
        fd.fetch_json = fake

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = fd.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class ParsingTests(unittest.TestCase):
    """纯函数解析:PSI 现场/实验分离与 CLS 百分之一表示;CrUX p75 字符串小数。"""

    def test_psi_field_vs_lab_separated(self):
        """现场取 loadingExperience(含 category),实验取 lighthouseResult.audits——
        两口径键集不同、数值独立;PSI CLS 为百分之一表示(5 → 0.05)。"""
        d = psi_payload(lcp=2500, cls_score=5, inp=250, ttfb=800, fcp=900,
                        lab_lcp=2100, lab_cls=0.02, lab_tbt=650, lab_fcp=800)
        field = fd.parse_psi_field(d["loadingExperience"])
        lab = fd.parse_psi_lab(d["lighthouseResult"])
        self.assertEqual(set(field), {"LCP", "CLS", "INP", "TTFB", "FCP"})   # 现场五项
        self.assertEqual(set(lab), {"LCP", "CLS", "TBT", "FCP"})             # 实验四项(无 INP 审计时)
        self.assertEqual(field["LCP"], (2500.0, "FAST"))                     # 毫秒原值
        self.assertAlmostEqual(field["CLS"][0], 0.05)                        # 5(百分之一)→ 0.05
        self.assertEqual(field["TTFB"], (800.0, "AVERAGE"))                  # category 分指标保留
        self.assertEqual(lab["LCP"]["numeric"], 2100.0)                      # 实验值独立于现场
        self.assertEqual(lab["CLS"]["numeric"], 0.02)                        # 实验 CLS 已是小数,不再÷100
        self.assertEqual(lab["TBT"]["value"], 650)                           # TBT 展示单位 ms
        self.assertEqual(lab["LCP"]["score"], 0.9)                           # Lighthouse 评分随行
        # 实验性 INP 审计 id 也能落到 lab["INP"]
        d2 = psi_payload(lab_inp=310)
        self.assertEqual(fd.parse_psi_lab(d2["lighthouseResult"])["INP"]["numeric"], 310.0)

    def test_psi_no_field_data(self):
        """loadingExperience 存在但无 metrics(样本不足)→ 现场空,不算解析崩溃。"""
        d = psi_payload(field=False)
        self.assertEqual(fd.parse_psi_field(d["loadingExperience"]), {})
        self.assertEqual(fd.parse_psi_field({}), {})

    def test_crux_p75_parsing(self):
        """CrUX p75:CLS 为 2 位小数字符串("0.23"),其余 int 毫秒;list 形态 percentiles 兼容。"""
        rec = crux_payload()
        got = fd.parse_crux(rec)
        self.assertEqual(got["LCP"], 2063.0)
        self.assertAlmostEqual(got["CLS"], 0.23)                             # "0.23" 字符串 → 小数
        self.assertEqual(got["INP"], 180.0)
        self.assertEqual(got["TTFB"], 700.0)
        self.assertEqual(fd.parse_crux(crux_payload(list_form=True))["LCP"], 2063.0)
        self.assertEqual(fd.parse_crux({}), {})

    def test_official_threshold_boundaries(self):
        """官方口径边界(含等号):2.5s/200ms/0.1 恰好为 good;NI 上界 4s/500ms/0.25。"""
        self.assertEqual(fd.cwv_verdict("LCP", 2500), "good")
        self.assertEqual(fd.cwv_verdict("LCP", 2500.1), "needs_improvement")
        self.assertEqual(fd.cwv_verdict("LCP", 4000), "needs_improvement")
        self.assertEqual(fd.cwv_verdict("LCP", 4000.1), "poor")
        self.assertEqual(fd.cwv_verdict("INP", 200), "good")
        self.assertEqual(fd.cwv_verdict("INP", 201), "needs_improvement")
        self.assertEqual(fd.cwv_verdict("INP", 500), "needs_improvement")
        self.assertEqual(fd.cwv_verdict("INP", 501), "poor")
        self.assertEqual(fd.cwv_verdict("CLS", 0.1), "good")
        self.assertEqual(fd.cwv_verdict("CLS", 0.1000001), "needs_improvement")
        self.assertEqual(fd.cwv_verdict("CLS", 0.25), "needs_improvement")
        self.assertEqual(fd.cwv_verdict("CLS", 0.2500001), "poor")
        self.assertEqual(fd.cwv_verdict("TTFB", 800), "good")                # 参考口径 0.8s/1.8s
        self.assertEqual(fd.cwv_verdict("TTFB", 1800), "needs_improvement")
        self.assertEqual(fd.cwv_verdict("TTFB", 1801), "poor")


class RequestShapeTests(unittest.TestCase):
    """请求构造:PSI urlencode 往返与可选 key;CrUX POST body 的 page/origin 双模式。"""

    def test_psi_url_encoding_and_key(self):
        u = fd.psi_request_url("https://example.com/a?b=1&c=2", "mobile")
        self.assertTrue(u.startswith(fd.PSI_ENDPOINT + "?"))
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)            # 目标 URL 里的 & 不得劈开请求
        self.assertEqual(q["url"], ["https://example.com/a?b=1&c=2"])
        self.assertEqual(q["strategy"], ["mobile"])
        self.assertNotIn("key", q)                                          # 无 key 不携带
        q2 = urllib.parse.parse_qs(urllib.parse.urlsplit(
            fd.psi_request_url("https://example.com/", "desktop", "K1")).query)
        self.assertEqual(q2["key"], ["K1"])

    def test_crux_body_page_origin_and_form_factor(self):
        body = fd.crux_request_body("https://example.com/p", "page", "PHONE")
        self.assertEqual(body["url"], "https://example.com/p")
        self.assertNotIn("origin", body)
        self.assertEqual(body["formFactor"], "PHONE")
        self.assertIn("largest_contentful_paint", body["metrics"])          # 显式 metrics 列表
        self.assertEqual(fd.crux_request_body("https://example.com/x", "origin", "DESKTOP")["origin"],
                         "https://example.com")
        self.assertEqual(fd.FORM_FACTOR, {"mobile": "PHONE", "desktop": "DESKTOP"})

    def test_query_crux_origin_target(self):
        calls = []

        def fake(url, payload=None, timeout=fd.DEFAULT_TIMEOUT):
            calls.append((url, payload))
            return crux_payload()
        orig = fd.fetch_json
        fd.fetch_json = fake
        try:
            data, err = fd.query_crux("https://example.com/deep/path?q=1", "mobile", "KEY", "origin")
        finally:
            fd.fetch_json = orig
        self.assertIsNone(err)
        self.assertIn("key=KEY", calls[0][0])
        self.assertEqual(calls[0][1]["origin"], "https://example.com")       # origin 模式剥路径
        self.assertAlmostEqual(fd.parse_crux(data)["CLS"], 0.23)


class SourceBehaviourTests(FieldHarness):
    """双源行为:无 key crux 整源跳过(不算失败)/ 429 配额提示 / 404 无数据为 note。"""

    def test_crux_skipped_without_key(self):
        """无 crux key:不发起任何 chromeuxreport 请求,源标记仅 psi,不算失败。"""
        self.stub(psi=psi_responder_by_url({"https://example.com/": psi_payload()}))
        code, out, err = self.run_main("--url", "https://example.com/", "--json")
        self.assertEqual(code, 0)
        self.assertTrue(all("pagespeedonline" in u for u in self.calls))     # 只打了 PSI
        rep = json.loads(out)
        self.assertEqual(rep["results"][0]["source"], "psi")
        self.assertTrue(any("crux 源跳过" in n for n in rep["notes"]), rep["notes"])
        self.assertIn("[warn] crux 源跳过", err)                             # 跳过要告警
        self.assertEqual(rep["exit_code"], 0)

    def test_both_sources_merged(self):
        """有 key:两源都被查询,现场以 PSI 页级优先、CrUX 补缺,source=psi+crux。"""
        self.stub(psi=psi_responder_by_url({"https://example.com/": psi_payload(lcp=1400)}),
                  crux=lambda u, p: crux_payload(lcp=9999))                  # CrUX LCP 不覆盖 PSI
        code, out, _ = self.run_main("--url", "https://example.com/", "--key", "K", "--json")
        self.assertEqual(code, 0)
        r = json.loads(out)["results"][0]
        self.assertEqual(r["source"], "psi+crux")
        self.assertEqual(r["field"]["LCP"]["p75"], 1400.0)                   # PSI 优先
        self.assertEqual(r["field"]["LCP"]["source"], "psi")
        self.assertTrue(any("chromeuxreport" in u for u in self.calls))

    def test_429_quota_hint(self):
        """PSI 429 → 错误条目带"加 key 或降频"提示(配额纪律);全 URL 429 → 退出码 3。"""
        self.stub(psi=lambda u, p: http_err(429, "Too Many Requests",
                                            b'{"error":{"message":"Quota exceeded"}}'))
        code, _, err = self.run_main("--url", "https://example.com/", "--json")
        self.assertEqual(code, 3)
        self.assertIn("加 key", err)
        self.assertIn("PSI_API_KEY", err)
        data, e = None, None
        orig = fd.fetch_json
        fd.fetch_json = lambda u, payload=None, timeout=60: (_ for _ in ()).throw(
            http_err(429, "Too Many Requests"))
        try:
            data, e = fd.query_psi("https://example.com/", "mobile")
        finally:
            fd.fetch_json = orig
        self.assertIsNone(data)
        self.assertEqual(e["code"], 429)
        self.assertIn("降频", e["hint"])

    def test_crux_404_no_data_is_note_not_error(self):
        """CrUX 404(样本不足)→ note 而非 error;PSI 实验数据在场则不算全源失败。"""
        self.stub(psi=psi_responder_by_url({"https://example.com/": psi_payload(field=False)}),
                  crux=lambda u, p: http_err(404, "Not Found",
                                             b'{"error":{"message":"Chromium UX Report data not found"}}'))
        code, out, _ = self.run_main("--url", "https://example.com/", "--key", "K", "--json")
        self.assertEqual(code, 0)                                           # 实验数据在场,非全源失败
        r = json.loads(out)["results"][0]
        self.assertEqual(r["errors"], [])
        self.assertTrue(any("404" in n for n in r["notes"]), r["notes"])
        self.assertEqual(r["source"], "psi")


class CliExitCodeTests(FieldHarness):
    """退出码矩阵:0 正常 / 1 现场核心三项 poor / 2 输入错 / 3 全源失败;批量 delay。"""

    def test_exit_matrix(self):
        good = psi_responder_by_url({"https://a.example.com/": psi_payload()})
        poor = psi_responder_by_url({"https://a.example.com/": psi_payload(lcp=4100)})       # 现场 LCP poor
        ttfb_poor = psi_responder_by_url({"https://a.example.com/": psi_payload(ttfb=2500)})  # 仅参考项 poor
        cases = [
            (good, 0, "现场全 good → 0"),
            (poor, 1, "现场 LCP 4.1s poor → 1"),
            (lambda u, p: http_err(500, "Internal", b"Lighthouse returned error"), 3, "PSI 500 全失败 → 3"),
            (lambda u, p: {}, 3, "PSI 200 但零数据 → 3"),
        ]
        for responder, want, why in cases:
            self.stub(psi=responder)
            self.assertEqual(self.run_main("--url", "https://a.example.com/")[0], want, why)
        # 参考项(TTFB)poor 不触发退出码 1
        self.stub(psi=ttfb_poor)
        self.assertEqual(self.run_main("--url", "https://a.example.com/")[0], 0)
        # 实验指标 poor 也不触发(退出码只看现场核心三项)
        self.stub(psi=psi_responder_by_url({"https://a.example.com/": psi_payload(lab_tbt=900)}))
        self.assertEqual(self.run_main("--url", "https://a.example.com/")[0], 0)

    def test_input_errors_exit_2(self):
        self.assertEqual(self.run_main("--url", "https://a.example.com/", "--strategy", "tablet")[0], 2)
        self.assertEqual(self.run_main("--strategy", "mobile")[0], 2)       # 无 --url/--urls
        self.assertEqual(self.run_main("--url", "https://a.example.com/", "--crux-scope", "site")[0], 2)
        self.assertEqual(self.run_main("--url", "https://a.example.com/", "--delay", "abc")[0], 2)
        self.assertEqual(self.run_main("--url", "https://a.example.com/", "--bogus")[0], 2)
        self.assertEqual(self.run_main("--url", "https://a.example.com/", "--urls", "/nonexistent/x.txt")[0], 2)

    def test_ssrf_input_rejection_exit_2(self):
        """非 http(s) 与私网/环回 URL 是输入错(退出码 2);stub DNS 字面量直通,零网络。"""
        fd.ssrf_guard = self._saved[1]         # 本用例需要真 guard(setUp 默认打桩跳过 DNS)
        orig_gai = socket.getaddrinfo
        socket.getaddrinfo = lambda host, *a, **k: [(2, 1, 6, "", (host, 0))]
        fd._ssrf_cache.clear()
        try:
            self.assertTrue(fd.validate_url("ftp://example.com/f").startswith("仅允许 http(s)"))
            for evil in ("http://127.0.0.1:8080/x", "http://10.0.0.5/internal",
                         "http://169.254.169.254/meta", "https://192.168.1.2/"):
                self.assertTrue(fd.validate_url(evil).startswith("SSRF guard"), evil)
            code, _, err = self.run_main("--url", "http://10.0.0.5/internal", "--json")
            self.assertEqual(code, 2)
            self.assertIn("SSRF", err)
        finally:
            socket.getaddrinfo = orig_gai
            fd._ssrf_cache.clear()

    def test_batch_delay_between_urls(self):
        """批量:每对相邻 URL 之间睡 --delay 秒(末个不睡);单 URL 不睡。"""
        spec = {u: psi_payload() for u in ("https://a.example.com/", "https://b.example.com/")}
        self.stub(psi=psi_responder_by_url(spec))
        urls = tmp_file("https://a.example.com/\nhttps://b.example.com/\n", suffix=".txt")
        try:
            code, _, _ = self.run_main("--urls", urls, "--delay", "1.5", "--json")
            self.assertEqual(code, 0)
            self.assertEqual(self.fake_time.sleeps, [1.5])                  # 2 URL → 恰好睡 1 次
            self.assertEqual(len(self.calls), 2)                            # 1 策略 × 2 URL
            self.fake_time.sleeps.clear()
            code, _, _ = self.run_main("--url", "https://a.example.com/", "--delay", "1.5", "--json")
            self.assertEqual(self.fake_time.sleeps, [])                     # 单 URL 不睡
        finally:
            os.unlink(urls)

    def test_json_schema_and_both_strategies(self):
        """--json:schema_version=1,每 URL {url,strategy,field,lab,source};both=两条结果。"""
        self.stub(psi=psi_responder_by_url({"https://a.example.com/": psi_payload()}))
        code, out, _ = self.run_main("--url", "https://a.example.com/", "--strategy", "both", "--json")
        self.assertEqual(code, 0)
        rep = json.loads(out)
        self.assertEqual(rep["schema_version"], 1)
        self.assertEqual(len(rep["results"]), 2)                            # mobile+desktop 各一条
        r = rep["results"][0]
        self.assertEqual(r["strategy"], "mobile")
        for key in ("url", "strategy", "field", "lab", "source"):
            self.assertIn(key, r)
        self.assertEqual(sorted(r["field"]), ["CLS", "FCP", "INP", "LCP", "TTFB"])
        for key in ("value", "unit", "verdict"):
            self.assertIn(key, r["field"]["LCP"])
        self.assertEqual(r["field"]["LCP"], {"value": 1.2, "unit": "s", "verdict": "good",
                                             "p75": 1200.0, "category": "FAST", "source": "psi"})

    def test_markdown_labels_field_vs_lab(self):
        """markdown:现场与实验分开成表并显式标注;p75 与判定记号在场。"""
        self.stub(psi=psi_responder_by_url({"https://a.example.com/": psi_payload(lcp=4100)}))
        code, out, err = self.run_main("--url", "https://a.example.com/")
        self.assertEqual(code, 1)
        self.assertIn("现场 field(真实用户 p75", out)
        self.assertIn("实验 lab(Lighthouse", out)
        self.assertIn("p75", out)
        self.assertIn("✗ poor", out)                                       # 现场 LCP 4.1s
        self.assertIn("[warn] crux 源跳过", err)


class CwvCsvContractTests(FieldHarness):
    """--as-cwv-csv 输出契约与 traffic_funnel --cwv 端到端衔接。"""

    E2E_SPEC = {
        "https://example.com/": psi_payload(lcp=2500, cls_score=10, lab_fcp=1500),   # 边界:LCP2.5/CLS0.1/DCL1.5 全等号→pass
        "https://example.com/slow": psi_payload(lcp=4200, cls_score=5, lab_fcp=1000),  # 现场 LCP 4.2s=poor→退出码 1;funnel 流失
        "https://example.com/nodata": {"loadingExperience": {"metrics": {}},
                                       "lighthouseResult": {}},                # 零数据 → 全空行 → funnel N/A
    }

    AUDIT = {"results": {
        "https://example.com/": {"verdict": "pass", "findings": [],
                                 "meta": {"title": "Home Widgets", "description": "Widgets home page for everyone"}},
        "https://example.com/slow": {"verdict": "pass", "findings": [],
                                     "meta": {"title": "Slow Page", "description": "A slower widgets landing page"}},
        "https://example.com/nodata": {"verdict": "pass", "findings": [],
                                       "meta": {"title": "No Data Page", "description": "A page without any field data"}},
    }}
    GSC = ("Page,Clicks,Impressions,CTR,Position\n"
           "https://example.com/,10,500,2%,5.0\n"
           "https://example.com/slow,5,100,5%,8.0\n"
           "https://example.com/nodata,5,100,5%,6.0\n")

    def test_csv_header_and_blank_cells(self):
        """表头 URL,LCP,CLS,DCL;无现场/实验数据的格留空;traffic_funnel.load_cwv 吃下为 None。
        单 URL 全源无数据 → 退出码 3(诚实报告"什么都没拿到"),但 CSV 仍照常写出。"""
        self.stub(psi=psi_responder_by_url(self.E2E_SPEC))
        csv_path = os.path.join(tempfile.mkdtemp(prefix="fd_cwv_"), "cwv.csv")
        code, _, _ = self.run_main("--url", "https://example.com/nodata", "--as-cwv-csv", csv_path, "--json")
        self.assertEqual(code, 3)                                           # 唯一 URL 零数据 → 全源失败
        with open(csv_path, encoding="utf-8-sig") as f:
            lines = f.read().strip().splitlines()
        self.assertEqual(lines[0], "URL,LCP,CLS,DCL")                       # load_cwv 识别并跳过的表头
        self.assertEqual(lines[1], "https://example.com/nodata,,,")         # 缺数据 → 空单元格
        import traffic_funnel as tf
        parsed = tf.load_cwv(csv_path)
        self.assertEqual(parsed["https://example.com/nodata"],
                         {"lcp": None, "cls": None, "dcl": None})           # 空格 → None(funnel N/A 口径)

    def test_csv_values_boundary_and_units(self):
        """CSV 单位契约:LCP 秒(2.500)/CLS 小数(0.100)/DCL=实验 FCP 秒(1.500)。"""
        self.stub(psi=psi_responder_by_url(self.E2E_SPEC))
        csv_path = os.path.join(tempfile.mkdtemp(prefix="fd_cwv_"), "cwv.csv")
        code, _, _ = self.run_main("--url", "https://example.com/", "--as-cwv-csv", csv_path, "--json")
        self.assertEqual(code, 0)
        with open(csv_path, encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        self.assertEqual(lines[1], "https://example.com/,2.500,0.100,1.500")

    def test_csv_mobile_preference_when_both(self):
        """--strategy both:每 URL 一行,取 mobile 现场值(Search 排名口径)。"""
        def by_strategy(url, payload=None):
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            return psi_payload(lcp=1200 if q["strategy"] == ["mobile"] else 3000)  # desktop 3.0s=NI 不触发退出码 1
        self.stub(psi=by_strategy)
        csv_path = os.path.join(tempfile.mkdtemp(prefix="fd_cwv_"), "cwv.csv")
        code, _, _ = self.run_main("--url", "https://a.example.com/", "--strategy", "both",
                                   "--as-cwv-csv", csv_path, "--json")
        self.assertEqual(code, 0)
        with open(csv_path, encoding="utf-8") as f:
            lines = [l for l in f.read().strip().splitlines() if l]
        self.assertEqual(len(lines), 2)                                     # 表头 + 单行数据
        self.assertEqual(lines[1], "https://a.example.com/,1.200,0.050,0.800")

    def test_end_to_end_accepted_by_traffic_funnel(self):
        """端到端:field_data --as-cwv-csv 的产物被 traffic_funnel --cwv 实际接受——
        good_ux 阶段 pages_in=2(1 页 N/A)/通过 1(边界值 LCP2.5·CLS0.1·DCL1.5 全过)/
        流失 1(slow,理由 LCP 4.2>2.5——CSV 秒值被 funnel 原样判定)。"""
        self.stub(psi=psi_responder_by_url(self.E2E_SPEC))
        d = tempfile.mkdtemp(prefix="fd_e2e_")
        csv_path = os.path.join(d, "cwv.csv")
        code, _, _ = self.run_main("--urls", self._urls_file(d), "--as-cwv-csv", csv_path, "--json")
        self.assertEqual(code, 1, "slow 页现场 LCP 4.2s=poor → 退出码 1")
        self.assertTrue(os.path.exists(csv_path))
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "traffic_funnel.py"),
                            "--audit", self._audit_file(d), "--gsc", self._gsc_file(d),
                            "--cwv", csv_path, "--json"],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        stages = {s["stage"]: s for s in json.loads(r.stdout)["stages"]}
        ux = stages["good_ux"]
        self.assertEqual((ux["pages_in"], ux["pages_through"], ux["dropped"]), (2, 1, 1))
        self.assertEqual(ux["pages_na"], 1)                                 # nodata 页 → N/A 不计入
        self.assertEqual(ux["dropped_urls"][0]["url"], "https://example.com/slow")
        self.assertIn("LCP 4.2>2.5", ux["dropped_urls"][0]["reason"])       # CSV 秒值被 funnel 原样判定
        self.assertNotIn("https://example.com/", [d0["url"] for d0 in ux["dropped_urls"]])

    @staticmethod
    def _urls_file(d):
        p = os.path.join(d, "urls.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(CwvCsvContractTests.E2E_SPEC) + "\n")
        return p

    @staticmethod
    def _audit_file(d):
        p = os.path.join(d, "audit.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(CwvCsvContractTests.AUDIT, f)
        return p

    @staticmethod
    def _gsc_file(d):
        p = os.path.join(d, "gsc.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write(CwvCsvContractTests.GSC)
        return p


class HelpTests(unittest.TestCase):
    def test_help_and_no_network_import(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "field_data.py"), "--help"],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage:", r.stdout)
        self.assertIn("--as-cwv-csv", r.stdout)
        self.assertIn("PSI_API_KEY", r.stdout)                              # 配额纪律写进帮助
        self.assertIn("退出码", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
