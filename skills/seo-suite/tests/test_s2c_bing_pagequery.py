#!/usr/bin/env python3
"""bing_wmt.py pagequery 子命令回归测试(B30;_http_json 打桩,零网络)。

期望值来源:learn.microsoft.com「IWebmasterApi.GetPageQueryStats(String, String) Method」
(2026-10-21 读取):参数 siteUrl、page;JSON 请求样例
  GET /webmaster/api.svc/json/GetPageQueryStats?siteUrl=http://example.com
      &page=%22http%3a%5c%2f%5c%2fexample.com%5c%2furl1.html%22&apikey=…
即 page 值是 JSON 字符串(带引号);响应 {"d":[QueryStats…]},字段 AvgClickPosition /
AvgImpressionPosition / Clicks / Date(WCF) / Impressions / Query——与 GetQueryStats 同型,
CSV 契约沿用 stats(Date,Query,Clicks,Impressions,CTR,Position)。
"""
import contextlib
import io
import json
import os
import sys
import unittest
import urllib.parse
from unittest import mock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import bing_wmt as BW  # noqa: E402

KEY = "TESTKEY0123456789abcdef"
ROWS = [{"__type": "QueryStats:#Microsoft.Bing.Webmaster.Api", "AvgClickPosition": 18,
         "AvgImpressionPosition": 17, "Clicks": 15, "Date": "/Date(1316156400000-0700)/",
         "Impressions": 100, "Query": "query"}]


class Stub:
    def __init__(self, resp):
        self.resp, self.calls = resp, []

    def __call__(self, url, data=None, headers=None, timeout=BW.DEFAULT_TIMEOUT):
        self.calls.append(url)
        return self.resp


def run(argv, resp):
    st = Stub(resp)
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(BW, "_http_json", st), contextlib.redirect_stdout(out), \
            contextlib.redirect_stderr(err):
        rc = BW.main(argv)
    return rc, out.getvalue(), err.getvalue(), st


class PageQueryTests(unittest.TestCase):
    def test_calls_getpagequerystats_with_json_quoted_page(self):
        rc, out, err, st = run(["pagequery", "--site", "example.com", "--page",
                                "https://example.com/url1.html", "--key", KEY], {"d": ROWS})
        self.assertEqual(rc, 0, err)                                        # 修前:无此子命令
        u = urllib.parse.urlsplit(st.calls[0])
        self.assertTrue(u.path.endswith("/GetPageQueryStats"))
        q = urllib.parse.parse_qs(u.query)
        self.assertEqual(q["siteUrl"], ["https://example.com"])
        self.assertEqual(json.loads(q["page"][0]), "https://example.com/url1.html")
        lines = out.splitlines()
        self.assertEqual(lines[0], "Date,Query,Clicks,Impressions,CTR,Position")
        self.assertTrue(lines[1].endswith(",query,15,100,0.15,17.0"), lines[1])

    def test_empty_is_not_zero(self):
        rc, out, err, st = run(["pagequery", "--site", "example.com", "--page",
                                "https://example.com/x", "--key", KEY, "--json"], {"d": []})
        self.assertEqual(rc, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["rows"], [])
        self.assertTrue(payload["note_empty"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
