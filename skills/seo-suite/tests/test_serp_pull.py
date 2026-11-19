#!/usr/bin/env python3
"""serp_pull.py 测试(standalone 零网络:HTTP 层打桩,只断言脚本自己的契约)。

覆盖:
1 请求构造:stable 用 query / standard 与 multi 用 q;gl/hl/device/start 固定;
  端点为 /api/v1/serp-stable(1 credit 版),不静默换版次
2 解析:data.result.results[](stable 口径 url+rank+type);非有机类型(ads 等)不计;
  同 URL 去重保首次名次;--top 截断;缺 result/空 results → 空(不补位)
3 计费:以 data.costCredits 为准;缺失时按版次单价保守计入(1/2/3)
4 关键词文件:空行与 # 注释跳过、重复词去重且保序
5 端到端(打桩):CSV 逐字节等于 `keyword,url1;url2`;empty 词不写行;报告分档准确
6 预算:--max-credits 用尽 → 剩余词 skipped 且不发请求,已抓到的照常落盘,退出码 3
7 致命错误:401/402/403 → 立刻中止(后续词不再请求),退出码 3
8 缓存:第二次跑同词只读缓存、不再发请求;--refresh 强制重抓
9 前置校验:缺 Key / 无关键词 → 退出码 2;--dry-run 不发请求且打印 credit 上限
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

import serp_pull as S  # noqa: E402

STABLE_PAYLOAD = {
    "code": 200,
    "data": {
        "endpoint": "/api/v1/serp-stable",
        "costCredits": 1,
        "remainingCredits": 999,
        "result": {
            "results": [
                {"title": "Pricing", "url": "https://example.com/pricing", "rank": 1,
                 "type": "organic", "snippet": "..."},
                {"title": "Ads", "url": "https://ads.example.net/x", "rank": 2,
                 "type": "ads"},
                {"title": "Docs", "url": "https://example.com/docs", "rank": 3,
                 "type": "organic", "position": {"absolute": 3}},
                {"title": "Dup", "url": "https://example.com/pricing", "rank": 4,
                 "type": "organic"},
            ],
            "has_next_page": False,
        },
    },
}


def _tmpdir():
    return tempfile.mkdtemp(prefix="serp-pull-test-")


def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def _run(argv, fetcher=None):
    """跑 main();fetcher=(url → (status,payload)),返回 (code, out, err, calls)。

    Key 用占位值写在环境变量里(只在打桩的 HTTP 层存在,不发真实请求);
    测缺 Key 的分支时传 --key-file 指向不存在的文件,优先级高于环境变量。
    """
    os.environ["GOANYAPI_API_KEY"] = "YOUR_API_KEY"
    calls = []

    def fake(url, key, timeout=45):
        calls.append(url)
        if fetcher is None:
            return 200, STABLE_PAYLOAD
        return fetcher(url)

    real = S._http_get_json
    S._http_get_json = fake
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = S.main(argv)
    finally:
        S._http_get_json = real
    return code, out.getvalue(), err.getvalue(), calls


class BuildUrlTests(unittest.TestCase):
    def test_stable_uses_query_param(self):
        url = S.build_url("coffee shops", "tr", "tr", "desktop", "stable")
        self.assertIn("/api/v1/serp-stable?", url)
        self.assertIn("query=coffee+shops", url)
        self.assertIn("gl=tr", url)
        self.assertIn("start=0", url)

    def test_standard_and_multi_use_q(self):
        self.assertIn("q=coffee+shops", S.build_url("coffee shops", "us", "en", "desktop", "standard"))
        self.assertIn("q=coffee+shops", S.build_url("coffee shops", "us", "en", "desktop", "multi"))

    def test_edition_prices_are_the_documented_ones(self):
        self.assertEqual([S.ENDPOINTS[e][1] for e in ("stable", "standard", "multi")], [1, 2, 3])


class ExtractOrganicTests(unittest.TestCase):
    def test_reads_results_url_and_skips_non_organic(self):
        urls = S.extract_organic(STABLE_PAYLOAD, 10)
        self.assertEqual(urls, ["https://example.com/pricing", "https://example.com/docs"])

    def test_top_truncates(self):
        self.assertEqual(len(S.extract_organic(STABLE_PAYLOAD, 1)), 1)

    def test_empty_payload_is_empty_not_fabricated(self):
        for payload in ({}, {"data": None}, {"data": {"result": {"results": []}}}):
            self.assertEqual(S.extract_organic(payload, 10), [])

    def test_standard_shape_also_parsed(self):
        payload = {"data": {"result": {"organic_results": [
            {"link": "https://a.example/1", "position": 1}]}}}
        self.assertEqual(S.extract_organic(payload, 10), ["https://a.example/1"])


class CreditsTests(unittest.TestCase):
    def test_uses_response_cost(self):
        self.assertEqual(S.credits_used({"data": {"costCredits": 4}}, "stable"), 4)

    def test_falls_back_to_edition_price(self):
        self.assertEqual(S.credits_used({}, "multi"), 3)


class KeywordFileTests(unittest.TestCase):
    def test_skips_blank_and_comments_dedupes(self):
        p = _write(os.path.join(_tmpdir(), "k.txt"),
                   "\ufeff# seed\ncoffee shops\n\nCoffee Shops\ncoffee shops\nshoe store\n")
        self.assertEqual(S.read_keywords(p), ["coffee shops", "Coffee Shops", "shoe store"])


class EndToEndTests(unittest.TestCase):
    def test_csv_contract_and_report(self):
        d = _tmpdir()
        kws = _write(os.path.join(d, "k.txt"), "coffee shops\nempty word\n")
        out = os.path.join(d, "serp.csv")
        rep = os.path.join(d, "report.json")

        def fetcher(url):
            return (200, STABLE_PAYLOAD) if "coffee" in url else (200, {
                "code": 200, "data": {"costCredits": 1, "result": {"results": []}}})

        code, stdout, stderr, calls = _run(
            ["--keywords", kws, "--out", out, "--json", rep, "--rps", "1000"], fetcher)
        self.assertEqual(code, 0)   # empty 是有效响应,不算失败;但报告单列
        self.assertEqual(len(calls), 2)
        with open(out, encoding="utf-8") as f:
            self.assertEqual(f.read(), "coffee shops,https://example.com/pricing;https://example.com/docs\n")
        with open(rep, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["summary"]["ok"], 1)
        self.assertEqual(data["summary"]["empty"], 1)
        self.assertEqual(data["summary"]["credits_spent"], 2)
        self.assertIn("empty", stdout)

    def test_header_flag(self):
        d = _tmpdir()
        kws = _write(os.path.join(d, "k.txt"), "coffee shops\n")
        out = os.path.join(d, "serp.csv")
        code, _, _, _ = _run(["--keywords", kws, "--out", out, "--header", "--rps", "1000"])
        self.assertEqual(code, 0)
        with open(out, encoding="utf-8") as f:
            self.assertTrue(f.read().startswith("keyword,top10\n"))

    def test_budget_stops_and_keeps_observed_rows(self):
        d = _tmpdir()
        kws = _write(os.path.join(d, "k.txt"), "one\ntwo\nthree\n")
        out = os.path.join(d, "serp.csv")
        code, _, _, calls = _run(
            ["--keywords", kws, "--out", out, "--max-credits", "1", "--rps", "1000"])
        self.assertEqual(code, 3)
        self.assertEqual(len(calls), 1)
        with open(out, encoding="utf-8") as f:
            self.assertEqual(len(f.read().splitlines()), 1)

    def test_fatal_aborts_immediately(self):
        d = _tmpdir()
        kws = _write(os.path.join(d, "k.txt"), "one\ntwo\n")
        out = os.path.join(d, "serp.csv")
        code, _, err, calls = _run(
            ["--keywords", kws, "--out", out, "--rps", "1000"],
            lambda url: (402, {"message": "insufficient credits"}))
        self.assertEqual(code, 3)
        self.assertEqual(len(calls), 1)          # 余下词不再请求
        self.assertIn("insufficient credits", err)

    def test_cache_avoids_second_spend(self):
        d = _tmpdir()
        kws = _write(os.path.join(d, "k.txt"), "coffee shops\n")
        out = os.path.join(d, "serp.csv")
        self.assertEqual(_run(["--keywords", kws, "--out", out, "--rps", "1000"])[0], 0)
        code, _, _, calls = _run(["--keywords", kws, "--out", out, "--rps", "1000"])
        self.assertEqual((code, len(calls)), (0, 0))
        code, _, _, calls = _run(["--keywords", kws, "--out", out,
                                  "--refresh", "--rps", "1000"])
        self.assertEqual((code, len(calls)), (0, 1))

    def test_missing_key_and_empty_keywords_exit_2(self):
        d = _tmpdir()
        kws = _write(os.path.join(d, "k.txt"), "coffee shops\n")
        code, _, err, calls = _run(
            ["--keywords", kws, "--out", os.path.join(d, "s.csv"),
             "--key-file", os.path.join(d, "nokey.txt")])
        self.assertEqual((code, len(calls)), (2, 0))
        self.assertIn("key", err.lower())
        empty = _write(os.path.join(d, "empty.txt"), "# nothing\n")
        self.assertEqual(_run(["--keywords", empty, "--out", os.path.join(d, "s.csv")])[0], 2)

    def test_dry_run_spends_nothing(self):
        d = _tmpdir()
        kws = _write(os.path.join(d, "k.txt"), "a\nb\n")
        code, stdout, _, calls = _run(
            ["--keywords", kws, "--out", os.path.join(d, "s.csv"), "--dry-run"])
        self.assertEqual((code, len(calls)), (0, 0))
        self.assertIn("2 credit", stdout)

    def test_usage_without_args(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(S.main([]), 2)
        self.assertIn("usage: serp_pull.py", out.getvalue())


if __name__ == "__main__":
    unittest.main()
