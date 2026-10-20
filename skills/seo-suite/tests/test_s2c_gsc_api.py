#!/usr/bin/env python3
"""gsc_api.py --dimensions 扩维回归测试(B10;零网络,_http_json 打桩)。

期望值来源:Search Console API「Search Analytics: query」参考页(developers.google.com/
webmaster-tools/v1/searchanalytics/query,Last updated 2026-08-11,2026-10-21 读取):
- dimensions[]「You can use any dimension name in dimensionFilterGroups[].filters[].dimension
  as well as "date" and "hour"」;filters[].dimension 可选值 country / device / page / query /
  searchAppearance;示例 "dimensions": ["country","device"]。
- country 值是 ISO 3166-1 alpha-3;device 值 DESKTOP / MOBILE / TABLET。
- dataState「hourly_all」… should be used when grouping by the HOUR API dimension。
- rows[].keys[] 顺序 = 请求里的 dimensions 顺序。
market_fit.py --gsc-country 读 Country 列(英文国名),所以 country 维 CSV 要能直接喂它。
"""
import contextlib
import csv
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import gsc_api  # noqa: E402


class Stub:
    def __init__(self, rows):
        self.rows, self.bodies = rows, []

    def __call__(self, url, data=None, headers=None, timeout=30):
        assert "searchAnalytics/query" in url, url
        body = json.loads(data.decode("utf-8"))
        self.bodies.append(body)
        return {"rows": self.rows if body["startRow"] == 0 else []}


def run(argv, rows):
    st = Stub(rows)
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.object(gsc_api, "_http_json", st), \
            mock.patch.object(gsc_api, "resolve_sa_path", lambda a: "sa.json"), \
            mock.patch.object(gsc_api, "load_sa", lambda p: {"client_email": "x@y"}), \
            mock.patch.object(gsc_api, "get_access_token", lambda *a, **k: "tok"):
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = gsc_api.main(argv)
    return rc, out.getvalue(), err.getvalue(), st


BASE_ARGS = ["query", "--site", "sc-domain:example.com", "--start", "2026-09-01", "--end", "2026-09-28"]


class DimensionTests(unittest.TestCase):
    def test_country_device_accepted_and_columns(self):
        rows = [{"keys": ["usa", "MOBILE"], "clicks": 10, "impressions": 200, "ctr": 0.05, "position": 3.2},
                {"keys": ["jpn", "DESKTOP"], "clicks": 4, "impressions": 90, "ctr": 0.0444, "position": 5.0}]
        rc, out, err, st = run(BASE_ARGS + ["--dimensions", "country,device"], rows)
        self.assertEqual(rc, 0, err)                                        # 修前 exit 2「不支持的维度」
        self.assertEqual(st.bodies[0]["dimensions"], ["country", "device"])
        recs = list(csv.DictReader(io.StringIO(out)))
        self.assertEqual(recs[0]["Device"], "MOBILE")
        self.assertIn("Country", recs[0])

    def test_country_csv_feeds_market_fit(self):
        import market_fit
        rows = [{"keys": ["usa"], "clicks": 10, "impressions": 200, "ctr": 0.05, "position": 3.2},
                {"keys": ["jpn"], "clicks": 4, "impressions": 90, "ctr": 0.0444, "position": 5.0}]
        d = tempfile.mkdtemp()
        p = os.path.join(d, "country.csv")
        rc, out, err, st = run(BASE_ARGS + ["--dimensions", "country", "--out", p], rows)
        self.assertEqual(rc, 0, err)
        by, tc, ti = market_fit.parse_gsc_country(p)
        self.assertEqual(tc, 14)
        self.assertIn("United States", by)                                 # market_fit 按英文国名映射市场
        self.assertIn("Japan", by)

    def test_search_appearance_case_and_api_name(self):
        rows = [{"keys": ["VIDEO"], "clicks": 1, "impressions": 5, "ctr": 0.2, "position": 2.0}]
        rc, out, err, st = run(BASE_ARGS + ["--dimensions", "searchappearance"], rows)
        self.assertEqual(rc, 0, err)
        self.assertEqual(st.bodies[0]["dimensions"], ["searchAppearance"])  # API 原名(驼峰)

    def test_hour_sets_hourly_data_state(self):
        rows = [{"keys": ["2026-09-01T10:00:00-07:00"], "clicks": 1, "impressions": 5, "ctr": 0.2, "position": 2.0}]
        rc, out, err, st = run(BASE_ARGS + ["--dimensions", "hour"], rows)
        self.assertEqual(rc, 0, err)
        self.assertEqual(st.bodies[0].get("dataState"), "hourly_all")

    def test_query_page_output_unchanged(self):
        rows = [{"keys": ["kw", "https://example.com/a"], "clicks": 1, "impressions": 5, "ctr": 0.2, "position": 2.0}]
        rc, out, err, st = run(BASE_ARGS + ["--dimensions", "query,page"], rows)
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.splitlines()[0], "Query,Page,Clicks,Impressions,CTR,Position")
        self.assertNotIn("dataState", st.bodies[0])

    def test_unknown_dimension_still_rejected(self):
        rc, out, err, st = run(BASE_ARGS + ["--dimensions", "browser"], [])
        self.assertEqual(rc, 2)
        self.assertIn("不支持的维度", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
