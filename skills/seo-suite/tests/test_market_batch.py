#!/usr/bin/env python3
"""test_market_batch.py — market_batch.py 回归(stdlib unittest,合成声明+打桩子脚本,
零网络,standalone——不 import run_tests,被其 test_*.py 自动发现加载)。口径钉死脚本
自身契约(规格=pipeline-completeness.md R3-9:一份声明→批量跑 market_lint/serp_occupancy
→跨市场周报;单市场失败不拖垮):

- 受限 YAML 声明:site 标量+market 块+key_pages/domains 列表+domains_file 标量;
  缺 site/缺 market 块/缺 key_pages/重复市场/未知行/缩进错位 → 退出码 2
- 批量编排:market_lint 每市场恰 1 代表页(key_pages[0];https?:// 走 --url,本地路径走
  位置参数);SEO_MARKET_BATCH_SCRIPTS_DIR 打桩(零网络),markets.json 校验恒读真表
- serp_occupancy:语言码→区域码(ko→kr/ja→jp)且仅当占位表存在才跑;表外/无 domains
  输入 → skipped 记因;domains_file 文件喂入
- 失败隔离:单市场 lint 崩溃(退出码 9/坏输出/超时)只记因续跑,批退出码 1;lint FAIL
  (critical>0,退出码 1)是有效结果——批退出码仍 0
- 周报:并排表(每市场 lint ✓/✗/CRIT/WARN/占位命中/UGC/比价/投诉)+ lint 通过率行 +
  逐市场明细;--out 落盘;--json 契约(markets[]/summary.failed_steps)
- 真链路(零网络):真 market_lint 吃本地文件代表页(ja 超限→critical≥1→FAIL 行)

用法: python3 tests/test_market_batch.py(tests/run_tests.py 自动发现本文件)"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")

# ---- 打桩件(SEO_MARKET_BATCH_SCRIPTS_DIR 指到临时目录;行为由 env/页面名驱动) ----
STUB_LINT = '''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
m = args[args.index("--market") + 1]
pos = [a for a in args if not a.startswith("--") and a != m]
page = pos[0] if pos else (args[args.index("--url") + 1] if "--url" in args else "")
log = os.environ.get("MB_LOG")
if log:
    open(log, "a").write("LINT %s %s%s\\n" % (m, "URL:" if "--url" in args else "FILE:", page))
crash = os.environ.get("MB_LINT_CRASH")
if crash == m:
    sys.stderr.write("stub boom for %s\\n" % m)
    sys.exit(9)
crit = 1 if "bad" in page else 0
out = ["[CRITICAL] title 40/32 fullwidth 超限,超出 8"] if crit else []
print(json.dumps({"market": m, "exit_code": crit, "critical": crit, "warn": 2,
                  "output": out}, ensure_ascii=False))
sys.exit(crit)
'''
STUB_OCC = '''#!/usr/bin/env python3
import os, sys
args = sys.argv[1:]
m = args[args.index("--market") + 1]
doms = [a for a in args if not a.startswith("--") and a != m]
log = os.environ.get("MB_LOG")
if log:
    open(log, "a").write("OCC %s %s\\n" % (m, " ".join(doms)))
rc = os.environ.get("MB_OCC_RC")
if rc:
    sys.exit(int(rc))
print("市场 %s:SERP 10 席 → 占位表命中 4" % m)
print("UGC 平台 2 席 | 比价 1 席 | 投诉/评测 1 席")
'''


def write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def run_cli(decl_text, args=(), stub=True, env_extra=None, decl_name="decl.yaml"):
    """写声明 → 跑 market_batch → (CompletedProcess, stub 目录/日志路径 或 None)。"""
    tmp = tempfile.mkdtemp(prefix="mbatch_")
    decl = write(os.path.join(tmp, decl_name), decl_text)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    stubdir = log = None
    if stub:
        stubdir = os.path.join(tmp, "stubs")
        os.makedirs(stubdir)
        write(os.path.join(stubdir, "market_lint.py"), STUB_LINT)
        write(os.path.join(stubdir, "serp_occupancy.py"), STUB_OCC)
        log = os.path.join(tmp, "calls.log")
        env["SEO_MARKET_BATCH_SCRIPTS_DIR"] = stubdir
        env["MB_LOG"] = log
    env.update(env_extra or {})
    r = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS, "market_batch.py"),
         "--decl", decl, *args],
        capture_output=True, text=True, encoding="utf-8", env=env, timeout=90)
    return r, tmp, log


def read_log(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


DECL = """site: https://example.com
market: ja
key_pages:
  - https://example.com/ja/
  - https://example.com/ja/pricing
domains:
  - note.com
market: de
key_pages:
  - /tmp/rep-de.html
"""

DECL_KO = """site: https://example.com
market: ko
key_pages:
  - https://example.com/ko/
domains:
  - blog.naver.com
  - kin.naver.com
"""


class MarketBatchUsageTests(unittest.TestCase):
    """--help / 声明解析与用法错(全走打桩或纯解析路径,退出码 2)"""

    def test_help_prints_usage(self):
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "market_batch.py"),
                            "--help"], capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0)
        self.assertIn("R3-9", r.stdout)
        self.assertIn("key_pages", r.stdout)

    def test_missing_decl_file_exit_2(self):
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "market_batch.py"),
                            "--decl", "/nonexistent/decl.yaml"],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 2)
        self.assertIn("不可读", r.stderr)

    def test_decl_requires_site(self):
        r, tmp, _ = run_cli("market: ja\nkey_pages:\n  - https://e.com/ja/\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("缺 site", r.stderr)
        shutil.rmtree(tmp)

    def test_decl_requires_market_blocks(self):
        r, tmp, _ = run_cli("site: https://example.com\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("缺 market", r.stderr)
        shutil.rmtree(tmp)

    def test_decl_requires_key_pages(self):
        r, tmp, _ = run_cli("site: https://e.com\nmarket: ja\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("ja 缺 key_pages", r.stderr)
        shutil.rmtree(tmp)

    def test_decl_duplicate_market_exit_2(self):
        r, tmp, _ = run_cli(DECL + "market: ja\nkey_pages:\n  - https://e.com/ja2/\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("重复声明", r.stderr)
        shutil.rmtree(tmp)

    def test_decl_unknown_line_exit_2(self):
        r, tmp, _ = run_cli("site: https://e.com\nfrobnicate: yes\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("无法解析", r.stderr)
        shutil.rmtree(tmp)

    def test_decl_unknown_market_exit_2(self):
        r, tmp, _ = run_cli("site: https://e.com\nmarket: xx\nkey_pages:\n  - https://e.com/\n")
        self.assertEqual(r.returncode, 2)
        self.assertIn("未知市场 xx", r.stderr)
        self.assertIn("可用:", r.stderr)   # markets.json 恒读真表(不受打桩影响)
        shutil.rmtree(tmp)


class MarketBatchOrchestrationTests(unittest.TestCase):
    """批量编排:代表页口径/--url 分流/占位区域映射/domains_file/失败隔离"""

    def test_lint_representative_page_only(self):
        r, tmp, log = run_cli(DECL, args=["--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        logtxt = read_log(log)
        self.assertIn("LINT ja URL:https://example.com/ja/", logtxt)   # https 走 --url
        self.assertIn("LINT de FILE:/tmp/rep-de.html", logtxt)          # 本地路径走位置参数
        self.assertNotIn("pricing", logtxt)                             # 只用 key_pages[0]
        shutil.rmtree(tmp)

    def test_occupancy_region_mapping_and_table_gate(self):
        no_dom = "market: tr\nkey_pages:\n  - https://e.com/tr/\n"   # 表内(tr)但无 domains
        r, tmp, log = run_cli(DECL + DECL_KO.split("\n", 1)[1] + no_dom, args=["--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        logtxt = read_log(log)
        self.assertIn("OCC kr blog.naver.com", logtxt)                  # ko→kr,表内才跑
        self.assertIn("OCC jp note.com", logtxt)                        # ja 有 domains→跑
        self.assertNotIn("OCC tr", logtxt)                              # tr 无 domains→不跑
        doc = json.loads(r.stdout)
        occ = {m["market"]: m["occupancy"] for m in doc["markets"]}
        self.assertEqual(occ["ko"]["status"], "ok")
        self.assertEqual(occ["de"]["status"], "skipped")                # 表外市场
        self.assertIn("占位表无该市场区域", occ["de"]["reason"])
        self.assertIn("无 domains 输入", occ["tr"]["reason"])
        shutil.rmtree(tmp)

    def test_domains_file_feeds_occupancy(self):
        tmp = tempfile.mkdtemp(prefix="mbatch_df_")
        df = write(os.path.join(tmp, "serp-ja.txt"),
                   "note.com\nchiebukuro.yahoo.co.jp, qiita.com\n")
        decl = write(os.path.join(tmp, "d.yaml"),
                     "site: https://e.com\nmarket: ja\nkey_pages:\n  - https://e.com/ja/\n"
                     "domains_file: %s\n" % df)
        stubdir = os.path.join(tmp, "stubs")
        os.makedirs(stubdir)
        write(os.path.join(stubdir, "market_lint.py"), STUB_LINT)
        write(os.path.join(stubdir, "serp_occupancy.py"), STUB_OCC)
        log = os.path.join(tmp, "calls.log")
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "market_batch.py"), "--decl", decl, "--json"],
            capture_output=True, text=True, encoding="utf-8", timeout=90,
            env=dict(os.environ, SEO_MARKET_BATCH_SCRIPTS_DIR=stubdir,
                     MB_LOG=log, PYTHONIOENCODING="utf-8"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OCC jp note.com,chiebukuro.yahoo.co.jp,qiita.com", read_log(log))
        doc = json.loads(r.stdout)
        self.assertEqual(doc["markets"][0]["occupancy"]["status"], "ok")
        shutil.rmtree(tmp)

    def test_single_market_crash_does_not_kill_batch(self):
        r, tmp, log = run_cli(DECL, args=["--json"],
                              env_extra={"MB_LINT_CRASH": "de"})
        self.assertEqual(r.returncode, 1)                       # 汇总退出码 1,不是崩溃
        logtxt = read_log(log)
        self.assertIn("LINT ja", logtxt)                        # 其余市场照跑
        self.assertIn("LINT de", logtxt)
        doc = json.loads(r.stdout)
        bm = {m["market"]: m for m in doc["markets"]}
        self.assertTrue(bm["ja"]["lint"]["pass"])
        self.assertIsNotNone(bm["de"]["lint"]["error"])
        self.assertEqual(doc["summary"]["failed_steps"], ["de:lint"])
        shutil.rmtree(tmp)

    def test_lint_fail_is_valid_result_not_execution_failure(self):
        r, tmp, log = run_cli(DECL.replace("/tmp/rep-de.html", "/tmp/rep-bad.html"))
        self.assertEqual(r.returncode, 0, r.stderr)             # critical=1 → 批仍 0
        self.assertIn("| de | ✗ | 1 |", r.stdout)
        self.assertIn("lint 通过率: 1/2", r.stdout)
        shutil.rmtree(tmp)

    def test_occupancy_nonzero_rc_recorded_not_fatal(self):
        r, tmp, log = run_cli(DECL_KO, args=["--json"], env_extra={"MB_OCC_RC": "2"})
        self.assertEqual(r.returncode, 1)
        doc = json.loads(r.stdout)
        occ = doc["markets"][0]["occupancy"]
        self.assertEqual(occ["status"], "failed")
        self.assertIn("退出码 2", occ["error"])
        self.assertEqual(doc["summary"]["failed_steps"], ["ko:occupancy"])
        shutil.rmtree(tmp)


class MarketBatchReportTests(unittest.TestCase):
    """周报 markdown 与 --json 契约/--out 落盘/占位解析"""

    def test_report_side_by_side_table(self):
        r, tmp, log = run_cli(DECL + DECL_KO.split("\n", 1)[1])
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        self.assertIn("# 多市场周报 — https://example.com", out)
        self.assertIn("## 跨市场并排", out)
        self.assertIn("| 市场 | lint | CRIT | WARN | 占位命中 | UGC/比价/投诉 | 投诉警告 |", out)
        self.assertIn("| ja | ✓ | 0 | 2 |", out)
        self.assertIn("| ko | ✓ | 0 | 2 | 4/10 | 2/1/1 | ⚠ 1 |", out)   # 占位解析并排
        self.assertIn("lint 通过率: 3/3", out)
        self.assertIn("投诉/评测类占位警告合计: 2", out)   # ja+ko 两市场各投诉 1 席
        self.assertIn("## 逐市场明细", out)
        self.assertIn("serp_occupancy(kr): SERP 10 席命中 4;UGC 2/比价 1/投诉 1", out)
        shutil.rmtree(tmp)

    def test_json_contract(self):
        r, tmp, log = run_cli(DECL, args=["--json"])
        doc = json.loads(r.stdout)
        self.assertEqual(doc["tool"], "market_batch.py")
        self.assertEqual(doc["site"], "https://example.com")
        for m in doc["markets"]:
            self.assertIn("rep_page", m)
            self.assertTrue({"ran", "pass", "critical", "warn"} <= set(m["lint"]))
            self.assertTrue({"status", "region", "hits", "complaint"} <= set(m["occupancy"]))
        self.assertEqual(doc["summary"]["lint_pass"], 2)
        self.assertEqual(doc["summary"]["lint_ran"], 2)
        self.assertEqual(doc["summary"]["failed_steps"], [])
        shutil.rmtree(tmp)

    def test_out_writes_markdown_file(self):
        tmp = tempfile.mkdtemp(prefix="mbatch_out_")
        out_path = os.path.join(tmp, "weekly.md")
        decl = write(os.path.join(tmp, "d.yaml"), DECL)
        stubdir = os.path.join(tmp, "stubs")
        os.makedirs(stubdir)
        write(os.path.join(stubdir, "market_lint.py"), STUB_LINT)
        write(os.path.join(stubdir, "serp_occupancy.py"), STUB_OCC)
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "market_batch.py"),
             "--decl", decl, "--out", out_path],
            capture_output=True, text=True, encoding="utf-8", timeout=90,
            env=dict(os.environ, SEO_MARKET_BATCH_SCRIPTS_DIR=stubdir,
                     MB_LOG=os.devnull, PYTHONIOENCODING="utf-8"))
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out_path, encoding="utf-8") as f:
            saved = f.read()
        self.assertIn("# 多市场周报", saved)
        self.assertIn("## 跨市场并排", saved)
        shutil.rmtree(tmp)


class MarketBatchRealLintTests(unittest.TestCase):
    """真链路(零网络):真 market_lint 吃本地文件代表页——ja 全角超限→FAIL 入周报"""

    def test_real_market_lint_local_file(self):
        tmp = tempfile.mkdtemp(prefix="mbatch_real_")
        page = write(os.path.join(tmp, "ja.html"), "ラ" * 40 + "\n" + "ラ" * 40 + "\n本文です。\n")
        decl = write(os.path.join(tmp, "d.yaml"),
                     "site: https://e.com\nmarket: ja\nkey_pages:\n  - %s\n" % page)
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "market_batch.py"), "--decl", decl],
            capture_output=True, text=True, encoding="utf-8", timeout=90,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"))    # 不打桩→真 scripts 目录
        self.assertEqual(r.returncode, 0, r.stderr)            # FAIL 是有效结果
        self.assertIn("| ja | ✗ | 1 |", r.stdout)
        self.assertIn("FAIL(CRITICAL 1", r.stdout)
        self.assertIn("[CRITICAL] title 40/32", r.stdout)      # 明细含 top 行
        shutil.rmtree(tmp)

    def test_real_market_lint_pass_page(self):
        tmp = tempfile.mkdtemp(prefix="mbatch_real2_")
        page = write(os.path.join(tmp, "de.txt"),
                     "Produktvergleich\nKaufberatung\n" +
                     "\n".join("Dieser Satz hat genau neun Worte hier drin." for _ in range(6)))
        decl = write(os.path.join(tmp, "d.yaml"),
                     "site: https://e.com\nmarket: de\nkey_pages:\n  - %s\n" % page)
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "market_batch.py"), "--decl", decl, "--json"],
            capture_output=True, text=True, encoding="utf-8", timeout=90,
            env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        self.assertEqual(r.returncode, 0, r.stderr)
        doc = json.loads(r.stdout)
        lint = doc["markets"][0]["lint"]
        self.assertTrue(lint["ran"])
        self.assertEqual(lint["critical"], 0)                  # 真脚本对合成合规页 0 CRITICAL
        self.assertTrue(lint["pass"])
        shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
