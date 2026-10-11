#!/usr/bin/env python3
"""byo_import.py golden 用例(stdlib unittest,合成 CSV fixture,零网络)。
口径钉死 pipeline-completeness.md R2-6(BYO 解析器 pack):
  frog 千列取 20 列固定 schema / SF 数字后缀与同义词列头容错(大小写·空格·全半角)/
  serp 逗号·分号混杂(长表+宽表 URL 串格)→ query,url,position /
  kws keyword,search_volume,position[,cpc,kd] 变体+千分位归一 /
  --kind 嗅探(frog→kws→serp 特征链)与嗅探失败 / --urls-only / --json / 退出码。
独立可运行:python3 tests/test_byo_import.py;也被 tests/run_tests.py 自动发现。"""
import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import byo_import as bi  # noqa: E402


def run_script(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "byo_import.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_csv(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def parse_csv(stdout):
    return list(csv.DictReader(io.StringIO(stdout)))


# 真实形态的 SF internal.csv 切片:SF 后缀列(Title 1/H1-1/…) + 千列噪音列混入。
# 用 csv.writer 生成,保证行字段数与表头严格对齐(23 列)。
_SF_HEADERS = ["Address", "Content", "Status Code", "Status Message", "Title 1", "Title 1 Length",
               "Meta Description 1", "Meta Keyword 1", "H1-1", "H2-1", "H2-2",
               "Canonical Link Element 1", "Meta Robots 1", "Word Count", "Text Ratio",
               "Crawl Depth", "Inlinks", "Outlinks", "External Outlinks", "Response Time",
               "Last Modified", "Indexability", "Indexability Status"]
_SF_ROWS = [
    ["https://a.com/", "text/html; charset=utf-8", "200", "OK", "Alpha Title", "11",
     "Alpha desc", "", "Alpha H1", "Alpha H2a", "Alpha H2b", "https://a.com/", "", "520",
     "8.3", "1", "10", "3", "2", "120", "2026-09-01", "Indexable", ""],
    ["https://a.com/b", "text/html", "404", "Not Found", "", "", "", "", "", "Broken H2",
     "", "", "", "0", "", "0", "0", "0", "", "", "", "Non-Indexable", "Not Found 404"],
]


def _sf_csv():
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(_SF_HEADERS)
    w.writerows(_SF_ROWS)
    return buf.getvalue()


class FrogTests(unittest.TestCase):
    """Screaming Frog internal.csv → 20 列固定 schema(SF 后缀列+噪音列容错)"""

    def test_frog_basic_20col_schema(self):
        p = tmp_csv(_sf_csv())
        r = run_script([p, "--kind", "frog"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        rows = parse_csv(r.stdout)
        self.assertEqual(len(rows), 2)
        self.assertEqual(list(rows[0].keys()), bi.FROG_COLS)     # 恰 20 列固定 schema
        self.assertEqual(len(bi.FROG_COLS), 20)
        row = rows[0]
        self.assertEqual(row["address"], "https://a.com/")
        self.assertEqual(row["status_code"], "200")
        self.assertEqual(row["title"], "Alpha Title")            # SF「Title 1」→ title
        self.assertEqual(row["meta_description"], "Alpha desc")
        self.assertEqual(row["h1"], "Alpha H1")
        self.assertEqual(row["h2"], "Alpha H2a")                 # H2-1 优先,H2-2 忽略
        self.assertEqual(row["canonical"], "https://a.com/")
        self.assertEqual(row["word_count"], "520")
        self.assertEqual((row["inlinks"], row["outlinks"]), ("10", "3"))
        self.assertEqual(row["content_type"], "text/html; charset=utf-8")
        self.assertEqual(row["indexability"], "Indexable")
        self.assertEqual(rows[1]["indexability_status"], "Not Found 404")
        self.assertEqual(rows[1]["title"], "")                   # 空值照写空串

    def test_frog_header_variants_case_space_synonyms(self):
        """列头容错:大小写/前后空格/全半角(NFKC)/同义词(url 代替 Address/Indexable)。"""
        csv_txt = ("  URL ,STATUS CODE,  Word Count  ,Inlinks,Indexable\n"
                   "https://x.com/p,200,88,4,Indexable\n")
        p = tmp_csv(csv_txt)
        r = run_script([p, "--kind", "frog"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        row = parse_csv(r.stdout)[0]
        self.assertEqual(row["address"], "https://x.com/p")
        self.assertEqual(row["status_code"], "200")
        self.assertEqual(row["word_count"], "88")

    def test_frog_minimal_columns_filled_empty(self):
        """缺列容错:仅 Address 必需,其余列照出(空值),schema 完整不变。"""
        p = tmp_csv("Address\nhttps://m.com/only\n")
        r = run_script([p, "--kind", "frog"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        rows = parse_csv(r.stdout)
        self.assertEqual(list(rows[0].keys()), bi.FROG_COLS)
        self.assertEqual(rows[0]["address"], "https://m.com/only")
        self.assertEqual(rows[0]["indexability"], "")

    def test_frog_missing_address_rejected(self):
        p = tmp_csv("Status Code,Title\n200,T\n")
        r = run_script([p, "--kind", "frog"])
        os.unlink(p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("缺必需列", r.stderr)

    def test_frog_urls_only_dedup_feeds_site_audit(self):
        """--urls-only:一行一 URL 去重保序——site_audit 批量审计的 URL 清单入口。"""
        csv_txt = ("Address,Status Code,Indexability\n"
                   "https://d.com/1,200,Indexable\n"
                   "https://d.com/2,200,Indexable\n"
                   "https://d.com/1,200,Indexable\n"
                   ",200,Indexable\n")
        p = tmp_csv(csv_txt)
        r = run_script([p, "--kind", "frog", "--urls-only"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.split(), ["https://d.com/1", "https://d.com/2"])

    def test_frog_urls_only_rejects_serp(self):
        p = tmp_csv("query,url,position\nkw,https://x.com/a,1\n")
        r = run_script([p, "--kind", "serp", "--urls-only"])
        os.unlink(p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--urls-only 仅支持 frog", r.stderr)


class SerpTests(unittest.TestCase):
    """SERP top10 导出:逗号/分号混杂的长表与宽表 → query,url,position"""

    def test_serp_long_table_comma_with_rank_synonym(self):
        p = tmp_csv("Query,URL,Rank\nbuy shoes,https://x.com/a,1\nbuy shoes,https://x.com/b,2\n")
        r = run_script([p, "--kind", "serp"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        rows = parse_csv(r.stdout)
        self.assertEqual([row["position"] for row in rows], ["1", "2"])   # Rank→position 同义词
        self.assertEqual(rows[0]["query"], "buy shoes")
        self.assertEqual(rows[1]["url"], "https://x.com/b")

    def test_serp_semicolon_locale_export(self):
        """分号分隔导出(部分工具 locale 逗号是小数点)按表头嗅探 delimiter。"""
        p = tmp_csv("query;url;position\nschuhe kaufen;https://de.com/a;1\nschuhe kaufen;https://de.com/b;2\n")
        r = run_script([p, "--kind", "serp"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        rows = parse_csv(r.stdout)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["url"], "https://de.com/a")
        self.assertEqual(rows[1]["position"], "2")

    def test_serp_wide_url_cell_expands_positions(self):
        """宽表:一格塞 ; 分隔的 top10 串 → 按出现顺序枚举 position。"""
        p = tmp_csv('query,top urls\nbuy shoes,"https://x.com/a;https://x.com/b;https://y.co/c"\n')
        r = run_script([p, "--kind", "serp"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        rows = parse_csv(r.stdout)
        self.assertEqual([(row["url"], row["position"]) for row in rows],
                         [("https://x.com/a", "1"), ("https://x.com/b", "2"),
                          ("https://y.co/c", "3")])

    def test_serp_wide_unnamed_url_columns(self):
        """无表头 URL 列:行比表头长(query;u1;u2;…),未映射 URL 格按位置序收编。"""
        p = tmp_csv("query\nsocks;https://s.com/1;https://s.com/2\n")
        r = run_script([p, "--kind", "serp"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        rows = parse_csv(r.stdout)
        self.assertEqual([(row["url"], row["position"]) for row in rows],
                         [("https://s.com/1", "1"), ("https://s.com/2", "2")])


class KwsTests(unittest.TestCase):
    """kws.csv 变体:同义词列头/千分位搜索量/可选 cpc·kd"""

    def test_kws_basic(self):
        p = tmp_csv("keyword,search_volume,position\nrunning shoes,12000,3.5\n")
        r = run_script([p, "--kind", "kws"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        rows = parse_csv(r.stdout)
        self.assertEqual(list(rows[0].keys()), bi.KWS_COLS)
        self.assertEqual((rows[0]["keyword"], rows[0]["search_volume"], rows[0]["position"]),
                         ("running shoes", "12000", "3.5"))

    def test_kws_synonyms_and_thousands_separator(self):
        """Volume/Qty 同义词 + 千分位 "12,000" → 12000;KD/Keyword Difficulty 同义词。"""
        p = tmp_csv('Keyword,Volume,Rank,CPC,Keyword Difficulty\nrunning shoes,"12,000",3,1.20,45\n')
        r = run_script([p, "--kind", "kws"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        row = parse_csv(r.stdout)[0]
        self.assertEqual(row["search_volume"], "12000")
        self.assertEqual(row["position"], "3")
        self.assertEqual(row["cpc"], "1.20")
        self.assertEqual(row["kd"], "45")

    def test_kws_without_optional_columns(self):
        """无 cpc/kd 变体 → 列照出(空),schema 不缩水。"""
        p = tmp_csv("keyword,Qty,position\nboot,900,12\n")
        r = run_script([p, "--kind", "kws"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        row = parse_csv(r.stdout)[0]
        self.assertEqual(list(row.keys()), bi.KWS_COLS)
        self.assertEqual((row["search_volume"], row["cpc"], row["kd"]), ("900", "", ""))

    def test_kws_missing_volume_rejected(self):
        p = tmp_csv("keyword,position\nkw,3\n")
        r = run_script([p, "--kind", "kws"])
        os.unlink(p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("缺必需列", r.stderr)


class SniffTests(unittest.TestCase):
    """--kind 省略时的自动嗅探(frog→kws→serp 特征链)与失败路径"""

    def test_sniff_frog(self):
        p = tmp_csv("Address,Status Code,Inlinks,Indexability\nhttps://a.com/,200,3,Indexable\n")
        r = run_script([p])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        self.assertIn("kind=frog", r.stderr)
        self.assertEqual(parse_csv(r.stdout)[0]["address"], "https://a.com/")

    def test_sniff_kws(self):
        p = tmp_csv("Keyword,Search Volume,Position\nkw,100,4\n")
        r = run_script([p])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        self.assertIn("kind=kws", r.stderr)

    def test_sniff_serp(self):
        p = tmp_csv("keyword,url,position\nkw,https://x.com/a,1\n")
        r = run_script([p])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        self.assertIn("kind=serp", r.stderr)

    def test_sniff_failure_exits_2(self):
        p = tmp_csv("a,b,c\n1,2,3\n")
        r = run_script([p])
        os.unlink(p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("无法嗅探格式", r.stderr)
        self.assertIn("--kind", r.stderr)

    def test_unknown_kind_value_exits_2(self):
        p = tmp_csv("keyword,volume\nkw,1\n")
        r = run_script([p, "--kind", "bogus"])
        os.unlink(p)
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知 --kind bogus", r.stderr)

    def test_mixed_kind_inputs_rejected_before_output(self):
        """多文件嗅探出不同格式 → exit 2 且 stdout 无半途写出的 CSV。"""
        a = tmp_csv("Address,Status Code,Indexability\nhttps://a.com/,200,Indexable\n")
        b = tmp_csv("Keyword,Search Volume\nkw,100\n")
        r = run_script([a, b])
        os.unlink(a)
        os.unlink(b)
        self.assertEqual(r.returncode, 2)
        self.assertIn("不同格式", r.stderr)
        self.assertEqual(r.stdout, "")


class OutputAndUnitTests(unittest.TestCase):
    """--json 结构 / --out 文件 / 纯函数(表头归一·URL 串拆分)"""

    def test_json_payload_structure(self):
        p = tmp_csv("Address,Status Code,Indexability\nhttps://j.com/1,200,Indexable\nhttps://j.com/1,301,Indexable\n")
        r = run_script([p, "--json"])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        payload = json.loads(r.stdout)            # --json 独占 stdout(CSV 不混出)
        self.assertEqual(payload["kind"], "frog")
        self.assertEqual(payload["total_rows"], 2)
        self.assertEqual(payload["urls"], ["https://j.com/1"])   # 去重清单
        self.assertEqual(payload["inputs"][0]["rows"], 2)
        self.assertEqual(payload["schema_version"], bi.SCHEMA_VERSION)

    def test_out_file_written(self):
        out = os.path.join(tempfile.mkdtemp(prefix="byo_"), "norm.csv")
        p = tmp_csv("keyword,volume,position\nkw,10,2\n")
        r = run_script([p, "--out", out])
        os.unlink(p)
        self.assertEqual(r.returncode, 0)
        with open(out, encoding="utf-8") as f:
            self.assertEqual(f.readline().strip(), "keyword,search_volume,position,cpc,kd")
        os.unlink(out)

    def test_norm_header_variants(self):
        self.assertEqual(bi.norm_header("Title 1"), "title")          # SF 数字后缀
        self.assertEqual(bi.norm_header("H1-1"), "h1")
        self.assertEqual(bi.norm_header("  Meta  Description  1 "), "meta description")
        self.assertEqual(bi.norm_header("Ｓｅａｒｃｈ Ｖｏｌｕｍｅ"), "search volume")   # 全角 NFKC
        self.assertEqual(bi.norm_header("Status Code"), "status code")

    def test_split_url_cell(self):
        cell = "https://a.com/x; example.com/y ,https://b.co/z not-a-url"
        self.assertEqual(bi.split_url_cell(cell),
                         ["https://a.com/x", "example.com/y", "https://b.co/z"])

    def test_missing_input_file_exits_2(self):
        r = run_script(["/nonexistent/x.csv"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("输入不可读", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
