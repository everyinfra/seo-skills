#!/usr/bin/env python3
"""directory_tracker.py 回归(R4-2;stdlib unittest,verify 全打桩,零网络,standalone——
被 run_tests.py 按 test_*.py 自动发现加载)。口径钉死脚本自身契约:
init 解析 references/research/directory-submissions.md 的「追踪 CSV 字段」列定义生成
空模板(骨=文档 14 列 + ID/Cost 管理列;已存在不覆写)/add 登记目录(Directory=可注册
域、Dofollow 缺省 ?、Tier 1-13、同域重复与非法值 → 2)/verify --entry 打桩核验
(HEAD/GET 活着 + 指向 --target 的 <a> rel=nofollow 检查:verified/removed/
nofollow_found/anchor_missing/unreachable 五路,Backlink Verified 只在核验成功时盖章)/
quarterly 季度复检队列(submitted/live 且 上次 verified>90d 或从未核验;非空 → 1)/
export→import CSV round-trip 按行等价/--json/--help/输入错退出码 2。
日期不打桩:90d 边界用 today±Δ 构造。"""
import contextlib
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

DOC = os.path.join(BASE, "references", "research", "directory-submissions.md")
DOC_COLUMNS = ["ID", "Directory", "Tier", "URL", "Category", "DR", "Dofollow", "Cost",
               "Submission Date", "Status", "Live URL", "Backlink Verified",
               "Positioning Variant Used", "Tags Used", "Account Email", "Notes"]
TARGET = "https://acme.com"
LISTING = "https://alternativeto.net/tool/acme/"
DOFOLLOW_PAGE = ('<html><body><h1>Best CRM</h1>'
                 '<a href="https://acme.com/">Acme</a></body></html>')
NOFOLLOW_PAGE = ('<html><body><h1>Best CRM</h1>'
                 '<a rel="ugc nofollow" href="https://www.acme.com/pricing">Acme</a>'
                 '</body></html>')
NO_ANCHOR_PAGE = '<html><body><h1>Best CRM</h1><a href="https://rival.com/">Rival</a></body></html>'


def run_dt(args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "directory_tracker.py"),
                           *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", env=env)


class DirectoryCase(unittest.TestCase):
    """公共助手:独立 tmpdir + init 自真实文档 + 打桩 import(verify 用)。"""

    def setUp(self):
        import directory_tracker as dt
        self.dt = dt
        self._orig_fetch = dt.fetch
        self.tmp = tempfile.mkdtemp(prefix="dirtrack-test-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.addCleanup(setattr, dt, "fetch", self._orig_fetch)
        r = run_dt(["init", "--directories", DOC], self.tmp)
        assert r.returncode == 0, r.stderr

    def store(self):
        with open(os.path.join(self.tmp, "directory-submissions.csv"), newline="",
                  encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def stub(self, body=DOFOLLOW_PAGE, status=200, error=None):
        def fake(url, timeout=self.dt.FETCH_TIMEOUT):
            if error:
                raise self.dt.FetchError(error)
            return {"head_status": status, "status": status, "body": body}
        self.dt.fetch = fake

    def add_listing(self, *ids_extra):
        r = run_dt(["add", "--directory", "https://alternativeto.net", "--tier", "2",
                    "--dofollow", "?", "--live-url", LISTING, "--status", "submitted",
                    *ids_extra], self.tmp)
        assert r.returncode == 0, r.stderr

    def set_row(self, **fields):
        """手改首行的列(构造 verified 日期等);键为 CSV 列名。"""
        path = os.path.join(self.tmp, "directory-submissions.csv")
        rows = self.store()
        rows[0].update({k: str(v) for k, v in fields.items()})
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=DOC_COLUMNS)
            w.writeheader()
            w.writerows(rows)


class DirectoryCliTests(unittest.TestCase):
    """--help / 无子命令 / 未知子命令"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="dirtrack-cli-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_help(self):
        r = run_dt(["--help"], self.tmp)
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage: directory_tracker.py", r.stdout)
        for sub in ("init", "add", "list", "verify", "quarterly", "export", "import"):
            self.assertIn(sub, r.stdout)
        self.assertIn("退出码: 0 正常 / 1", r.stdout)

    def test_no_subcommand_and_unknown(self):
        self.assertEqual(run_dt([], self.tmp).returncode, 2)
        r = run_dt(["explode"], self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知子命令", r.stderr)


class DirectoryInitTests(unittest.TestCase):
    """init:从文档解析列定义生成模板/不覆写/坏文档退出码 2"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="dirtrack-init-")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_template_from_real_doc(self):
        r = run_dt(["init", "--directories", DOC, "--json"], self.tmp)
        self.assertEqual(r.returncode, 0)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["columns"], DOC_COLUMNS)      # 骨=文档 14 列+ID/Cost
        self.assertEqual(len(payload["doc_columns"]), 14)
        with open(os.path.join(self.tmp, "directory-submissions.csv"), newline="",
                  encoding="utf-8") as f:
            self.assertEqual(next(csv.reader(f)), DOC_COLUMNS)  # 空模板只有表头
        r2 = run_dt(["init", "--directories", DOC], self.tmp)
        self.assertEqual(r2.returncode, 2)                      # 已存在不覆写

    def test_bad_doc_rejected(self):
        r = run_dt(["init"], self.tmp)                          # 缺 --directories
        self.assertEqual(r.returncode, 2)
        r = run_dt(["init", "--directories", os.path.join(self.tmp, "nope.md")], self.tmp)
        self.assertEqual(r.returncode, 2)
        p = os.path.join(self.tmp, "empty.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("# 目录提交\n无 schema 行\n")
        r = run_dt(["init", "--directories", p], self.tmp)      # 无「追踪 CSV 字段」行
        self.assertEqual(r.returncode, 2)
        self.assertIn("追踪 CSV", r.stderr)


class DirectoryAddTests(DirectoryCase):
    """add:字段落盘/缺省值/重复与非法值拒绝"""

    def test_add_defaults_and_fields(self):
        r = run_dt(["add", "--directory", "https://www.capterra.com/s/pricing",
                    "--tier", "7", "--cost", "99", "--dr", "93",
                    "--notes", "集成市场,DR 最高层"], self.tmp)
        self.assertEqual(r.returncode, 0)
        row = self.store()[0]
        self.assertEqual(row["ID"], "DIR-001")
        self.assertEqual(row["Directory"], "capterra.com")      # 可注册域归一(去 www)
        self.assertEqual(row["Tier"], "7")
        self.assertEqual(row["Dofollow"], "?")                  # 未知,待 verify
        self.assertEqual(row["Cost"], "99")
        self.assertEqual(row["Status"], "pending")
        self.assertEqual(row["DR"], "93")
        self.assertEqual(row["Submission Date"], "")            # 未提交不带日期
        self.assertEqual(row["Backlink Verified"], "")
        r = run_dt(["add", "--directory", "https://producthunt.com", "--tier", "1",
                    "--status", "submitted", "--json"], self.tmp)
        self.assertEqual(r.returncode, 0)
        row2 = json.loads(r.stdout)["added"]
        self.assertEqual(row2["ID"], "DIR-002")
        self.assertEqual(len(row2["Submission Date"]), 10)      # submitted → 今天

    def test_add_rejections(self):
        args = ["add", "--directory", "https://x.com", "--tier", "1"]
        self.assertEqual(run_dt(args, self.tmp).returncode, 0)
        r = run_dt(args, self.tmp)                               # 同域重复
        self.assertEqual(r.returncode, 2)
        self.assertIn("已登记", r.stderr)
        for bad_tier in ("0", "14", "x"):
            r = run_dt(["add", "--directory", "https://y.com", "--tier", bad_tier], self.tmp)
            self.assertEqual(r.returncode, 2, bad_tier)
            self.assertIn("--tier", r.stderr)
        r = run_dt(["add", "--directory", "https://z.com", "--tier", "2",
                    "--dofollow", "maybe"], self.tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--dofollow", r.stderr)
        r = run_dt(["add", "--directory", "ftp://z.com", "--tier", "2"], self.tmp)
        self.assertEqual(r.returncode, 2)                        # 仅 http(s)
        r = run_dt(["add", "--tier", "2"], self.tmp)
        self.assertEqual(r.returncode, 2)                        # 缺 --directory


class DirectoryVerifyTests(DirectoryCase):
    """verify --entry(打桩 fetch):五路结果与落盘/退出码"""

    def verify(self, *extra):
        return self.dt.cmd_verify(["--entry", "DIR-001", "--target", TARGET,
                                   "--file", os.path.join(self.tmp,
                                                          "directory-submissions.csv"),
                                   *extra])

    def test_verified_dofollow_stamps(self):
        self.add_listing()
        self.stub(body=DOFOLLOW_PAGE)
        rc = self.verify()
        self.assertEqual(rc, 0)
        row = self.store()[0]
        self.assertEqual((row["Status"], row["Dofollow"]), ("live", "dofollow"))
        self.assertEqual(len(row["Backlink Verified"]), 10)      # 盖章=今天
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = self.verify("--json")
        self.assertEqual(rc, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["result"], "verified")
        self.assertEqual(payload["checks"], {"reachable": True, "status_code": 200,
                                             "anchor_found": True, "dofollow": "dofollow"})
        self.assertEqual(payload["row"]["Dofollow"], "dofollow")

    def test_verify_missing_args_exit_2(self):
        r = run_dt(["verify", "--entry", "DIR-001", "--target", TARGET], self.tmp)
        self.assertEqual(r.returncode, 2)                        # 条目不存在(空库)
        r = run_dt(["verify", "--target", TARGET], self.tmp)
        self.assertEqual(r.returncode, 2)                        # 缺 --entry
        r = run_dt(["verify", "--entry", "DIR-001"], self.tmp)
        self.assertEqual(r.returncode, 2)                        # 缺 --target

    def test_nofollow_discovered(self):
        self.add_listing()
        self.stub(body=NOFOLLOW_PAGE)
        rc = self.verify()
        self.assertEqual(rc, 1)
        row = self.store()[0]
        self.assertEqual((row["Status"], row["Dofollow"]), ("live", "nofollow"))
        self.assertIn("悄悄转", row["Notes"])                    # 诚实条款留痕
        self.assertEqual(len(row["Backlink Verified"]), 10)

    def test_removed_on_404(self):
        self.add_listing()
        self.stub(status=404)
        rc = self.verify()
        self.assertEqual(rc, 1)
        row = self.store()[0]
        self.assertEqual(row["Status"], "removed")
        self.assertEqual(len(row["Backlink Verified"]), 10)      # 确认没了也算核验
        self.assertIn("HTTP 404", row["Notes"])

    def test_anchor_missing_and_unreachable_no_stamp(self):
        self.add_listing()
        self.stub(body=NO_ANCHOR_PAGE)
        rc = self.verify()
        self.assertEqual(rc, 1)                                  # 页在但没我们的链接
        row = self.store()[0]
        self.assertEqual(row["Backlink Verified"], "")           # 不盖 verified 章
        self.assertEqual(row["Dofollow"], "?")
        self.stub(error="DNS 解析失败")
        rc = self.verify()
        self.assertEqual(rc, 1)
        self.assertEqual(self.store()[0]["Status"], "submitted")  # 不可达行不动

    def test_fetch_head_then_get_and_ssrf(self):
        """真实 _request 路径的守卫:仅 http(s) + 私网地址拒(不解析真实 DNS,直用 IP)。"""
        for evil in ("file:///etc/passwd", "http://127.0.0.1/x", "http://10.0.0.5/x",
                     "http://169.254.169.254/latest/meta-data"):
            with self.assertRaises(self.dt.FetchError, msg=evil):
                self.dt._request(evil, "GET", 2)


class DirectoryQuarterlyTests(DirectoryCase):
    """quarterly:>90d 或从未核验入队;pending/removed/新鲜排除;退出码 1"""

    def test_quarterly_queue_boundaries(self):
        from datetime import datetime, timezone
        self.add_listing()                                        # DIR-001 submitted,未核验
        run_dt(["add", "--directory", "https://producthunt.com", "--tier", "1",
                "--status", "live"], self.tmp)                    # DIR-002 live
        rows = self.store()
        fresh = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
        edge = (datetime.now(timezone.utc) - timedelta(days=91)).date().isoformat()
        rows[0]["Backlink Verified"] = fresh                      # DIR-001:30d 前 → 排除
        rows[1]["Backlink Verified"] = edge                       # DIR-002:91d 前 → 入队
        def extra(rid, dom, url, status, verified):
            return dict(rows[1], **{"ID": rid, "Directory": dom, "URL": url,
                                    "Status": status, "Backlink Verified": verified})
        rows.append(extra("DIR-003", "capterra.com", "https://capterra.com",
                          "pending", edge))                       # DIR-003 pending → 排除
        rows.append(extra("DIR-004", "g2.com", "https://g2.com",
                          "removed", ""))                         # DIR-004 removed → 排除
        rows.append(extra("DIR-005", "slant.co", "https://slant.co",
                          "live", ""))                            # DIR-005 live 未核验 → 入队
        with open(os.path.join(self.tmp, "directory-submissions.csv"), "w",
                  newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=DOC_COLUMNS)
            w.writeheader()
            w.writerows(rows)
        r = run_dt(["quarterly"], self.tmp)
        self.assertEqual(r.returncode, 1)                         # 队列非空 → notify
        self.assertIn("季度复检队列", r.stdout)
        self.assertIn("DIR-002", r.stdout)
        self.assertIn("DIR-005", r.stdout)
        self.assertIn("从未核验", r.stdout)
        for absent in ("DIR-001", "DIR-003", "DIR-004"):
            self.assertNotIn(absent, r.stdout)
        r = run_dt(["quarterly", "--json"], self.tmp)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["queue"], 2)
        self.assertEqual([q["id"] for q in payload["items"]], ["DIR-002", "DIR-005"])

    def test_quarterly_empty_exit_0(self):
        r = run_dt(["quarterly"], self.tmp)                       # 空库 → 0
        self.assertEqual(r.returncode, 0)
        self.assertIn("(空", r.stdout)
        self.assertEqual(run_dt(["quarterly", "--file",
                                 os.path.join(self.tmp, "nope.csv")], self.tmp).returncode, 2)


class DirectoryRoundTripTests(DirectoryCase):
    """export→import round-trip 按行等价;import 参数校验"""

    def test_round_trip_row_equality(self):
        run_dt(["add", "--directory", "https://alternativeto.net", "--tier", "2",
                "--dofollow", "?", "--cost", "0", "--notes", "含,逗号 \"引号\""],
               self.tmp)
        run_dt(["add", "--directory", "https://producthunt.com", "--tier", "1",
                "--cost", "129"], self.tmp)
        src = self.store()
        out = os.path.join(self.tmp, "backup.csv")
        r = run_dt(["export", "--out", out], self.tmp)
        self.assertEqual(r.returncode, 0)
        # round-trip:export 出的 CSV import 进全新库 → 行内容等价(键值逐对)
        fresh = os.path.join(self.tmp, "fresh.csv")
        run_dt(["init", "--directories", DOC, "--file", fresh], self.tmp)
        r = run_dt(["import", "--csv", out, "--file", fresh], self.tmp)
        self.assertEqual(r.returncode, 0)
        with open(fresh, newline="", encoding="utf-8") as f:
            got = list(csv.DictReader(f))
        self.assertEqual(got, src)
        # 再 import 到已有同一份 → 按 ID 替换,不重复
        r = run_dt(["import", "--csv", out, "--file", fresh, "--json"], self.tmp)
        self.assertEqual(r.returncode, 0)
        payload = json.loads(r.stdout)
        self.assertEqual((payload["replaced"], payload["added"], payload["total"]), (2, 0, 2))

    def test_import_rejections(self):
        self.assertEqual(run_dt(["import"], self.tmp).returncode, 2)   # 缺 --csv
        p = os.path.join(self.tmp, "bad.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write("A,B\n1,2\n")                                      # 列集不符
        self.assertEqual(run_dt(["import", "--csv", p], self.tmp).returncode, 2)
        p2 = os.path.join(self.tmp, "badid.csv")
        with open(p2, "w", newline="", encoding="utf-8") as f:         # Status 非法
            w = csv.writer(f)
            w.writerow(DOC_COLUMNS)
            w.writerow(["DIR-001", "x.com", "1", "https://x.com", "", "", "?", "0",
                        "", "nope", "", "", "", "", "", ""])
        self.assertEqual(run_dt(["import", "--csv", p2], self.tmp).returncode, 2)


class DirectoryListTests(DirectoryCase):
    """list:表格/过滤/--json"""

    def test_list_table_and_filters(self):
        run_dt(["add", "--directory", "https://alternativeto.net", "--tier", "2"],
               self.tmp)
        r = run_dt(["list"], self.tmp)
        self.assertEqual(r.returncode, 0)
        self.assertIn("DIR-001", r.stdout)
        self.assertIn("alternativeto.net", r.stdout)
        self.assertIn("pending", r.stdout)
        self.assertIn("共 1 条", r.stdout)
        r = run_dt(["list", "--status", "live"], self.tmp)
        self.assertNotIn("DIR-001", r.stdout)
        r = run_dt(["list", "--json"], self.tmp)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["count"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
