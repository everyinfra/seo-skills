#!/usr/bin/env python3
"""backlink_import.py 测试(R2-3,standalone,合成导出文件,零网络;
tests/run_tests.py 自动发现本文件)。覆盖:
1 三格式各一 fixture:Ahrefs Backlinks(逗号,Referring Page/Domain Rating/First Seen/
  Last Checked/Anchor/Type)/Semrush Backlinks(分号常见,Domain/Rating/Anchor text/
  Page URL/First seen/Last seen/Type/Dofollow,引号内逗号)/GSC Links 简易表
  (无表头 referrer,target 两列);
2 列头变体容错(大小写/空格/别名:referring page url/Domain rating/Anchor Text/
  first_seen/last seen/dofollow);
3 分隔符自动检测(逗号/分号);4 去重(同 referring url 留首行);
5 嗅探错误退出 2(乱列头/文件不存在);6 dofollow 值归一(显式列+type 反推);
7 直喂 cite_domain 证据摘要(dr_distribution 分桶/months 按月/anchor_exact_ratio
  需 --brand;GSC 无 first_seen 不猜);8 统一 CSV 回灌(unified 嗅探+--out 文件)。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
SCRIPT = os.path.join(SCRIPTS, "backlink_import.py")
sys.path.insert(0, SCRIPTS)

import backlink_import as BI  # noqa: E402

AHREFS_CSV = (
    '"#","Referring Page","Domain Rating","First Seen","Last Checked","Anchor","Type"\n'
    '"1","https://blog.example-a.com/post-1","62","2026-09-03 10:00:00",'
    '"2026-10-01 10:00:00","best crm tools","Text"\n'
    '"2","https://news.example-b.org/page","31","2026-08-11",'
    '"2026-09-30","crm comparison","Nofollow"\n')

SEMRUSH_CSV = (
    "Domain;Rating;Anchor text;Page URL;First seen;Last seen;Type;Dofollow\n"
    '"shop.example-c.de";45;"acme, inc review";https://shop.example-c.de/reviews;'
    '2026-07-04;2026-09-28;Text;Yes\n'
    "forum.example-d.com;12;acme thread;https://forum.example-d.com/t/9;"
    "15.03.2026;01.10.2026;Text;No\n")

GSC_CSV = ("https://ref-1.example.com/page,https://www.mysite.com/a\n"
           "https://ref-2.example.org/x,https://www.mysite.com/b\n")


def run_script(*args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, SCRIPT, *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def _fixture(name, content):
    tmp = tempfile.mkdtemp(prefix="bli_")
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return p, tmp


class ThreeFormatFixtureTests(unittest.TestCase):
    """三格式各一 fixture:嗅探正确 + 统一 schema 全字段 + 域推导/回退。"""

    def test_ahrefs_fixture(self):
        p, tmp = _fixture("ahrefs.csv", AHREFS_CSV)
        out = os.path.join(tmp, "payload.json")
        r = run_script(p, "--json", out)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["format"], "ahrefs")
        self.assertEqual(len(payload["rows"]), 2)
        r1 = payload["rows"][0]
        self.assertEqual(set(r1), set(BI.UNIFIED_FIELDS))          # 统一 schema 全字段
        self.assertEqual(r1["referring_domain"], "example-a.com")  # url host 推导
        self.assertEqual((r1["dr_or_urgency"], r1["anchor"], r1["first_seen"]),
                         ("62", "best crm tools", "2026-09-03 10:00:00"))
        self.assertEqual(payload["rows"][1]["dofollow"], "nofollow")   # Type=Nofollow 反推

    def test_semrush_fixture(self):
        p, tmp = _fixture("semrush.csv", SEMRUSH_CSV)
        out = os.path.join(tmp, "payload.json")
        r = run_script(p, "--json", out)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["format"], "semrush")                 # 分号嗅探
        s1, s2 = payload["rows"]
        self.assertEqual(s1["anchor"], "acme, inc review")             # 引号内逗号保留
        self.assertEqual(s1["referring_domain"], "shop.example-c.de")  # Domain 列直取
        self.assertEqual((s1["dr_or_urgency"], s1["dofollow"]), ("45", "dofollow"))
        self.assertEqual(s2["dofollow"], "nofollow")
        self.assertEqual(BI.parse_date(s2["first_seen"]).isoformat(), "2026-03-15")  # 欧式日期

    def test_gsc_simple_table(self):
        p, tmp = _fixture("gsc.csv", GSC_CSV)
        out = os.path.join(tmp, "payload.json")
        r = run_script(p, "--json", out)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["format"], "gsc")
        r1 = payload["rows"][0]
        self.assertEqual(r1["url"], "https://ref-1.example.com/page")  # 目标列(本站)被忽略
        self.assertEqual(r1["referring_domain"], "example.com")
        self.assertEqual(r1["dr_or_urgency"], "" and r1["dr_or_urgency"])  # 无 DR 列=空
        self.assertEqual((r1["anchor"], r1["first_seen"], r1["dofollow"]), ("", "", ""))


class ColumnVariantTests(unittest.TestCase):
    """列头变体容错:大小写/空格/别名形态仍归一到 canonical 列。"""

    def test_ahrefs_header_variants(self):
        p, _ = _fixture("variant.csv",
                        "referring page url,Domain rating,Anchor Text,first_seen,last seen,dofollow\n"
                        "https://x.example.net/a,88,acme,2026-01-02,2026-02-03,Yes\n")
        out = BI.parse_export(p)
        self.assertEqual(out["format"], "ahrefs")
        r = out["rows"][0]
        self.assertEqual((r["dr_or_urgency"], r["anchor"], r["dofollow"]),
                         ("88", "acme", "dofollow"))
        self.assertEqual(r["last_seen"], "2026-02-03")

    def test_delimiter_detection(self):
        self.assertEqual(BI.detect_delimiter("a;b;c;d"), ";")
        self.assertEqual(BI.detect_delimiter('"a,b","c"'), ",")
        self.assertEqual(BI.detect_delimiter("a\tb"), "\t")

    def test_domain_column_preferred_over_derivation(self):
        p, _ = _fixture("dom.csv",
                        "Domain;Rating;Anchor text;Page URL;First seen\n"
                        "custom-domain.com;20;x;https://other.example.org/p;2026-05-05\n")
        r = BI.parse_export(p)["rows"][0]
        self.assertEqual(r["referring_domain"], "custom-domain.com")  # 显式列优先于 host 推导


class DedupTests(unittest.TestCase):
    """同 referring url 去重留首行;域级行按 域+锚 不误合并。"""

    def test_same_url_first_wins(self):
        p, _ = _fixture("dup.csv",
                        "Referring Page,Anchor\n"
                        "https://d.example.com/p,first\n"
                        "https://d.example.com/p,second\n"
                        "https://e.example.com/q,x\n")
        out = BI.parse_export(p)
        self.assertEqual(len(out["rows"]), 2)
        self.assertEqual(out["dedup_dropped"], 1)
        self.assertEqual(out["rows"][0]["anchor"], "first")

    def test_domain_level_rows_not_collapsed(self):
        p, _ = _fixture("domrows.csv",
                        "Domain,Anchor,First Seen\n"
                        "a.example.com,anchor1,2026-01-01\n"
                        "a.example.com,anchor2,2026-02-01\n")
        out = BI.parse_export(p)
        self.assertEqual(len(out["rows"]), 2)                    # 无 url:域+锚 为 key


class FailureExitTests(unittest.TestCase):
    """嗅探不出/文件不存在 → 退出码 2(数据错误,不猜)。"""

    def test_sniff_failure_exit_2(self):
        p, _ = _fixture("junk.csv", "foo,bar,baz\n1,2,3\n")
        r = run_script(p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("嗅探", r.stderr)

    def test_missing_file_exit_2(self):
        r = run_script("/nonexistent/nowhere.csv")
        self.assertEqual(r.returncode, 2)

    def test_empty_file_exit_2(self):
        p, _ = _fixture("empty.csv", "\n")
        r = run_script(p)
        self.assertEqual(r.returncode, 2)


class ValueNormalizationTests(unittest.TestCase):
    """dofollow 值归一 + 日期变体 + DR 解析。"""

    def test_dofollow_matrix(self):
        for v in ("Dofollow", "dofollow", "Follow", "Yes", "TRUE", "1"):
            self.assertEqual(BI.parse_dofollow(v), "dofollow", v)
        for v in ("Nofollow", "noFollow", "No", "false", "0", "ugc nofollow"):
            self.assertEqual(BI.parse_dofollow(v), "nofollow", v)
        self.assertEqual(BI.parse_dofollow(""), "")                       # unknown 不猜
        self.assertEqual(BI.parse_dofollow("", "Image nofollow"), "nofollow")   # type 反推
        self.assertEqual(BI.parse_dofollow("", "Text"), "")                # Text 不携带状态

    def test_date_variants(self):
        from datetime import date
        self.assertEqual(BI.parse_date("2026-09-01"), date(2026, 9, 1))
        self.assertEqual(BI.parse_date("2026-09-01 12:34:56"), date(2026, 9, 1))
        self.assertEqual(BI.parse_date("01.09.2026"), date(2026, 9, 1))
        self.assertEqual(BI.parse_date("9/1/2026"), date(2026, 9, 1))
        self.assertIsNone(BI.parse_date(""))
        self.assertIsNone(BI.parse_date("not a date"))

    def test_dr_parse(self):
        self.assertEqual(BI.parse_dr("77.5"), "77")
        self.assertEqual(BI.parse_dr("DR 62"), "62")
        self.assertEqual(BI.parse_dr("150"), "100")                       # 钳到 0-100
        self.assertEqual(BI.parse_dr(""), "")


class CiteDomainFeedTests(unittest.TestCase):
    """直喂 cite_domain 证据摘要:dr 分桶/月度计数/anchor_exact_ratio 需品牌词。"""

    ROWS = [
        {"referring_domain": "a.com", "url": "https://a.com/1", "dr_or_urgency": "62",
         "anchor": "Acme", "first_seen": "2026-08-03", "last_seen": "", "dofollow": "dofollow",
         "type": ""},
        {"referring_domain": "b.com", "url": "https://b.com/2", "dr_or_urgency": "31",
         "anchor": "acme alternatives", "first_seen": "2026-08-20", "last_seen": "",
         "dofollow": "nofollow", "type": ""},
        {"referring_domain": "c.com", "url": "https://c.com/3", "dr_or_urgency": "",
         "anchor": "", "first_seen": "", "last_seen": "", "dofollow": "", "type": ""},
    ]

    def test_feed_stats(self):
        feed = BI.cite_domain_feed(self.ROWS, brand="acme")
        self.assertEqual(feed["referring_domains"], 3)                    # C1 口径
        self.assertEqual(feed["dr_distribution"],
                         {"0-30": 0, "30-50": 1, "50-70": 1, "70-100": 0})
        self.assertEqual(feed["months"], [{"month": "2026-08", "links": 2}])   # C4 口径
        self.assertEqual(feed["anchor_exact_ratio"], 0.5)                 # T2:Acme/acme 全等
        self.assertEqual(feed["dofollow_ratio"], 0.5)

    def test_feed_without_brand_no_guess(self):
        feed = BI.cite_domain_feed(self.ROWS)
        self.assertIsNone(feed["anchor_exact_ratio"])                     # 缺品牌词不猜
        self.assertIn("cite_domain", feed["note"])                        # 直喂说明在场

    def test_gsc_feed_months_empty(self):
        rows = [{"referring_domain": "x.com", "url": "https://x.com/a", "dr_or_urgency": "",
                 "anchor": "", "first_seen": "", "last_seen": "", "dofollow": "", "type": ""}]
        feed = BI.cite_domain_feed(rows)
        self.assertEqual(feed["months"], [])                              # 无 first_seen 不猜
        self.assertEqual(feed["referring_domains"], 1)


class UnifiedOutputTests(unittest.TestCase):
    """统一 CSV 输出(--out)与回灌(unified 嗅探)。"""

    def test_out_csv_and_roundtrip(self):
        p, tmp = _fixture("ahrefs.csv", AHREFS_CSV)
        out_csv = os.path.join(tmp, "unified.csv")
        r = run_script(p, "--out", out_csv)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out_csv, encoding="utf-8") as f:
            header = f.readline().strip().split(",")
        self.assertEqual(header, BI.UNIFIED_FIELDS)
        self.assertNotIn("example-a.com", r.stdout)                       # CSV 落文件不进 stdout
        back = BI.parse_export(out_csv)                                   # 回灌:统一格式可再解析
        self.assertEqual(back["format"], "unified")
        self.assertEqual(back["rows"][0]["dr_or_urgency"], "62")          # DR 不丢
        self.assertEqual(back["rows"][1]["dofollow"], "nofollow")

    def test_stdout_csv_by_default(self):
        p, _ = _fixture("ahrefs.csv", AHREFS_CSV)
        r = run_script(p)
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0].split(","), BI.UNIFIED_FIELDS)
        self.assertEqual(len(lines), 3)
        self.assertIn("格式=ahrefs", r.stderr)                            # 摘要走 stderr

    def test_self_test_flag(self):
        r = run_script("--self-test")
        self.assertEqual(r.returncode, 0)
        self.assertIn("[self-test] PASS", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
