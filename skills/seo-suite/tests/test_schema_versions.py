#!/usr/bin/env python3
"""schema_version 输出契约测试(R2-8/R2-9)。

Part A:四个数据脚本的 --json 顶层输出必含 schema_version=1(只加键不动行为——
  gsc_mining 三模式 / traffic_funnel(截断漏斗仍出封套)/ citation_gaps(--json 落文件)/
  sensor_volatility(--json 全量;--context 单行口径不在契约内,键集钉死不动)。
Part B:doctor --keys 键清单模式(R2-9)——env 模板生成 + 已配校验:键全集落地
  (T1-T4 + SEO_MONITOR_* 组,除 BING_WMT_KEY 外均有真实脚本消费者)、模板形状与
  键序、校验只探存在性绝不读值、空串算未配、keys 模式独立 exit 0(坏基座也 0)、
  孤儿/互斥参数 exit 2。

standalone(自带 run_script 助手,合成数据,零网络):
  python3 tests/test_schema_versions.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import doctor as D  # noqa: E402  (需先入 SCRIPTS 路径)


def run_script(name, args=()):
    """独立助手(与 run_tests.py 同形):子进程跑 scripts/ 下脚本。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_file(content, suffix=".csv"):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


# ---------- Part A:schema_version=1(逐脚本打桩跑一次,断言键存在且值=1) ----------

GSC_QUERY_CSV = ("Query,Clicks,Impressions,CTR,Position\n"
                 "best crm,5,100,5%,8.2\n"
                 "crm pricing,1,60,1.6%,14.0\n"
                 "zero query,0,5,0%,3.0\n")

GSC_MATRIX_CSV = ("Query,Page,Clicks,Impressions,CTR,Position\n"
                  "crm,https://example.com/a,3,50,6%,12.0\n"
                  "crm,https://example.com/b,0,30,0%,18.5\n")

GSC_DECAY_CUR = "Query,Clicks,Impressions,CTR,Position\ncrm software,20,300,6%,7\n"
GSC_DECAY_PREV = "Query,Clicks,Impressions,CTR,Position\ncrm software,100,300,33%,7\n"


class GscMiningSchemaTests(unittest.TestCase):
    """gsc_mining --json 三模式(query/matrix/decay)顶层均带 schema_version=1。"""

    def _run_json(self, args):
        r = run_script("gsc_mining.py", args + ("--json",))
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)

    def test_query_mode_schema_version(self):
        p = tmp_file(GSC_QUERY_CSV)
        self.addCleanup(os.unlink, p)
        o = self._run_json((p,))
        self.assertEqual(o.get("schema_version"), 1)      # 键存在且值=1
        self.assertEqual(o["mode"], "query")              # 原有键不动
        self.assertIn("striking_distance", o)
        self.assertIn("low_ctr", o)

    def test_matrix_mode_schema_version(self):
        p = tmp_file(GSC_MATRIX_CSV)
        self.addCleanup(os.unlink, p)
        o = self._run_json((p, "--mode", "matrix"))
        self.assertEqual(o.get("schema_version"), 1)
        self.assertEqual(o["mode"], "matrix")
        self.assertEqual(len(o["cannibalization"]), 1)    # 同 query 两页 → 1 组

    def test_decay_mode_schema_version(self):
        cur, prev = tmp_file(GSC_DECAY_CUR), tmp_file(GSC_DECAY_PREV)
        self.addCleanup(os.unlink, cur)
        self.addCleanup(os.unlink, prev)
        o = self._run_json((cur, prev, "--decay"))
        self.assertEqual(o.get("schema_version"), 1)
        self.assertEqual(o["mode"], "decay")
        self.assertEqual(len(o["declined"]), 1)           # -80% 衰退命中


class TrafficFunnelSchemaTests(unittest.TestCase):

    def test_audit_only_truncated_funnel_has_schema_version(self):
        """无 --gsc → 漏斗截断,但 JSON 封套仍出且带 schema_version=1。"""
        audit = {"audited": 2, "critical": 0, "results": {
            "https://example.com/": {"verdict": "pass", "findings": [],
                                     "meta": {"title": "Home", "description": "x"}},
            "https://example.com/u": {"verdict": "pass", "findings": [],
                                      "meta": {"title": "U page", "description": "y"}}}}
        a = tmp_file(json.dumps(audit), suffix=".json")
        self.addCleanup(os.unlink, a)
        r = run_script("traffic_funnel.py", ("--audit", a, "--json"))
        self.assertEqual(r.returncode, 0, r.stderr)
        rep = json.loads(r.stdout)
        self.assertEqual(rep.get("schema_version"), 1)
        self.assertEqual(rep["tool"], "traffic_funnel")   # 原有键不动
        self.assertEqual(rep["funnel_truncated_at"], "uniqueness")


class CitationGapsSchemaTests(unittest.TestCase):

    def test_json_file_has_schema_version(self):
        """citation_gaps 的 --json 是输出路径(写文件不写 stdout):读回断言。"""
        tmp = tempfile.mkdtemp(prefix="cg_schema_")
        self.addCleanup(lambda: __import__("shutil").rmtree(tmp, ignore_errors=True))
        panel = {"brand": "Acme", "aliases": [], "domain": "acme.ai",
                 "prompts": ["best crm"], "engines": ["chatgpt"],
                 "runs": [{"run_id": "r1", "engine": "chatgpt", "date": "2026-10-01",
                           "brand": "Acme", "results": {
                               "best crm": {"state": "brand_absent", "mentioned": 0,
                                            "cited": 0,
                                            "cited_urls": ["https://www.g2.com/crm/best"]}}}]}
        p = os.path.join(tmp, "panel.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(panel, f, ensure_ascii=False)
        out = os.path.join(tmp, "gaps.json")
        r = run_script("citation_gaps.py", ("--panel", p, "--brand-domains",
                                            "acme.ai", "--json", out))
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload.get("schema_version"), 1)
        self.assertEqual(payload["tool"], "citation_gaps.py")   # 原有键不动
        self.assertEqual(len(payload["urls"]), 1)


class SensorVolatilitySchemaTests(unittest.TestCase):

    def test_json_payload_has_schema_version(self):
        csv = ("Date,Query,Position\n"
               "2026-10-01,q1,5\n2026-10-01,q2,8\n"
               "2026-10-02,q1,7\n2026-10-02,q2,9\n")
        p = tmp_file(csv)
        self.addCleanup(os.unlink, p)
        r = run_script("sensor_volatility.py", ("--positions", p, "--json"))
        self.assertEqual(r.returncode, 0, r.stderr)
        o = json.loads(r.stdout)
        self.assertEqual(o.get("schema_version"), 1)
        self.assertEqual(o["tool"], "sensor_volatility")  # 原有键不动

    def test_context_mode_keyset_unchanged(self):
        """--context 是 monitor 消费的单行口径(键集钉死),不混入 schema_version。"""
        csv = ("Date,Query,Position\n"
               "2026-10-01,q1,5\n2026-10-02,q1,7\n")
        p = tmp_file(csv)
        self.addCleanup(os.unlink, p)
        r = run_script("sensor_volatility.py", ("--positions", p, "--context"))
        self.assertEqual(r.returncode, 0, r.stderr)
        o = json.loads(r.stdout)
        self.assertEqual(set(o), {"date", "score", "band", "z30", "verdict"})
        self.assertNotIn("schema_version", o)


# ---------- Part B:doctor --keys(R2-9:env 模板生成 + 已配校验) ----------

DOCTOR = os.path.join(SCRIPTS, "doctor.py")


def _scrub_keys_env(extra=None):
    """子进程环境:剥掉 manifest 全部键(判定确定性),可选注入 extra。"""
    drop = {k for k, _, _ in D.KEY_MANIFEST}
    env = {k: v for k, v in os.environ.items() if k not in drop}
    env["PYTHONIOENCODING"] = "utf-8"
    env.update(extra or {})
    return env


def _run_doctor(args, extra_env=None):
    return subprocess.run([sys.executable, DOCTOR, *args], capture_output=True,
                          text=True, encoding="utf-8", env=_scrub_keys_env(extra_env))


class KeysManifestTests(unittest.TestCase):
    """键全集落地:T1-T4 + SEO_MONITOR_* 组;除规划中的 BING_WMT_KEY 外,
    每个键名必须在 scripts/ 有真实消费者(manifest 不得登记无人读的键)。"""

    def test_required_keys_present_unique_and_wellformed(self):
        names = [k for k, _, _ in D.KEY_MANIFEST]
        self.assertEqual(len(names), len(set(names)))               # 无重复
        for required in ("PSI_API_KEY", "CRUX_API_KEY", "GSC_SA_FILE",
                         "BING_WMT_KEY"):
            self.assertIn(required, names)                          # T1-T4 全集
        monitor_group = [n for n in names if n.startswith("SEO_MONITOR_")]
        self.assertGreaterEqual(len(monitor_group), 6)              # 通知/监控组
        for n in names:
            self.assertRegex(n, r"^[A-Z][A-Z0-9_]+$")               # env 名形态
        for _, tier, note in D.KEY_MANIFEST:
            self.assertIn(tier, D.KEY_GROUP_LABELS)                 # 组标签可解析
            self.assertTrue(note)                                   # 一行注释非空

    def test_every_key_has_a_real_consumer_in_scripts(self):
        """排除 doctor.py 自身与规划键 BING_WMT_KEY(R2-5 未落地)后,
        键名必须出现在某脚本源码里(防登记幻觉键)。"""
        corpus = []
        for fn in os.listdir(SCRIPTS):
            if fn.endswith(".py") and fn != "doctor.py":
                with open(os.path.join(SCRIPTS, fn), encoding="utf-8") as f:
                    corpus.append(f.read())
        blob = "\n".join(corpus)
        for name in {k for k, _, _ in D.KEY_MANIFEST} - {"BING_WMT_KEY"}:
            self.assertIn(name, blob, "manifest 键 %s 无脚本消费者" % name)


class KeysPrintEnvTests(unittest.TestCase):
    """--keys --print-env:shell 模板(键名+一行注释,值留空),独立 exit 0。"""

    def test_template_shape_and_exit_zero(self):
        r = _run_doctor(["--keys", "--print-env"])
        self.assertEqual(r.returncode, 0)
        lines = r.stdout.splitlines()
        self.assertTrue(lines[0].startswith("#"))                   # 头部是注释
        exports = [l for l in lines if l.startswith("export ")]
        self.assertEqual(len(exports), len(D.KEY_MANIFEST))         # 每键一条 export
        for _, _, note in D.KEY_MANIFEST:
            self.assertIn(note, r.stdout)                           # 一行注释在场
        for l in exports:
            self.assertRegex(l, r'^export [A-Z][A-Z0-9_]+=""')      # 值留空
        for l in lines:
            self.assertTrue(l.startswith("#") or l.startswith("export ")
                            or not l.strip())                       # 可整段 source

    def test_template_groups_in_tier_order(self):
        r = _run_doctor(["--keys", "--print-env"])
        self.assertEqual(r.returncode, 0)
        pos = [r.stdout.index(D.KEY_GROUP_LABELS[t]) for t in
               ("T1", "T2", "T4", "notify", "monitor")]
        self.assertEqual(pos, sorted(pos))                          # T1→T2→T4→通知→监控

    def test_template_survives_redact_and_leaks_no_values(self):
        """注入真值环境后出模板:模板值本就留空,真实值绝不出现;过 redact 不变形。"""
        r = _run_doctor(["--keys", "--print-env"],
                        {"PSI_API_KEY": "REAL-PSI-SECRET-99"})
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("REAL-PSI-SECRET-99", r.stdout)
        self.assertEqual(D.redact(r.stdout), r.stdout)              # 模板本身已脱敏幂等


class KeysCheckTests(unittest.TestCase):
    """--keys --check:只探存在性(非空才算已配),绝不读值;--json 形状。"""

    def test_check_counts_and_marks(self):
        r = _run_doctor(["--keys", "--check"],
                        {"PSI_API_KEY": "k", "SEO_MONITOR_TG_TOKEN": "t",
                         "SEO_MONITOR_TG_CHAT": "c"})
        self.assertEqual(r.returncode, 0)
        self.assertIn("keys: 已配置 3/%d(只探存在性,不读值)" % len(D.KEY_MANIFEST),
                      r.stdout)
        self.assertIn("[✓] PSI_API_KEY", r.stdout)
        self.assertIn("[✗] CRUX_API_KEY", r.stdout)
        self.assertIn("(输出 intentionally omits absolute paths and environment values)",
                      r.stdout)

    def test_check_never_prints_values(self):
        """注入显眼 secret:校验输出只出键名与 ✓/✗,值绝不出现。"""
        r = _run_doctor(["--keys", "--check"],
                        {"SEO_MONITOR_SLACK_WEBHOOK": "https://hooks.slack.example/T00/B00/zzz",
                         "SEO_MONITOR_SMTP_PASS": "SUPER-SMTP-PASS-77"})
        self.assertEqual(r.returncode, 0)
        for leak in ("zzz", "SUPER-SMTP-PASS-77"):
            self.assertNotIn(leak, r.stdout)

    def test_check_empty_string_counts_as_unconfigured(self):
        r = _run_doctor(["--keys", "--check"], {"PSI_API_KEY": ""})
        self.assertEqual(r.returncode, 0)
        self.assertIn("已配置 0/%d" % len(D.KEY_MANIFEST), r.stdout)
        self.assertIn("[✗] PSI_API_KEY", r.stdout)

    def test_check_json_shape(self):
        r = _run_doctor(["--keys", "--check", "--json"], {"CRUX_API_KEY": "k"})
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)                                 # 纯 JSON 可解析
        self.assertEqual(set(data), {"keys", "configured", "total"})
        self.assertEqual(data["total"], len(D.KEY_MANIFEST))
        self.assertEqual(data["configured"], 1)
        for i in data["keys"]:
            self.assertEqual(set(i), {"env", "tier", "note", "configured"})
            self.assertIsInstance(i["configured"], bool)
        by_name = {i["env"]: i["configured"] for i in data["keys"]}
        self.assertTrue(by_name["CRUX_API_KEY"])
        self.assertFalse(by_name["PSI_API_KEY"])

    def test_keys_mode_unit_check_with_injected_env(self):
        items = D.keys_check(env={"GSC_SA_FILE": "/tmp/sa.json"})
        self.assertEqual([i["configured"] for i in items],
                         [k == "GSC_SA_FILE" for k, _, _ in D.KEY_MANIFEST])


class KeysExitContractTests(unittest.TestCase):
    """keys 模式独立 exit 0(不跑基座检查、不受坏基座影响);孤儿/互斥参数 exit 2。"""

    def test_keys_mode_exit_zero_on_broken_base(self):
        """坏基座(markets 坏 JSON+语法错)下普通模式 rc=3,keys 模式仍 rc=0。"""
        import contextlib
        import io
        from unittest import mock
        base = tempfile.mkdtemp(prefix="keys_base_")
        os.makedirs(os.path.join(base, "scripts"))
        with open(os.path.join(base, "scripts", "markets.json"), "w") as f:
            f.write("{bad")
        with open(os.path.join(base, "scripts", "broken.py"), "w") as f:
            f.write("def (:\n")
        scrubbed = {k: v for k, v in os.environ.items()
                    if k not in {n for n, _, _ in D.KEY_MANIFEST}}
        orig = D.BASE
        D.BASE = base
        try:
            outs = {}
            for argv in (["--keys", "--print-env"], ["--keys", "--check"],
                         ["--keys", "--check", "--json"]):
                buf = io.StringIO()
                with mock.patch.dict(os.environ, scrubbed, clear=True), \
                        contextlib.redirect_stdout(buf):
                    self.assertEqual(D.main(argv), 0)               # 独立 exit 0
                outs[tuple(argv)] = buf.getvalue()
            self.assertIn("export PSI_API_KEY", outs[("--keys", "--print-env")])
            self.assertIn("已配置 0/%d" % len(D.KEY_MANIFEST),
                          outs[("--keys", "--check")])
            self.assertEqual(json.loads(outs[("--keys", "--check", "--json")])["total"],
                             len(D.KEY_MANIFEST))
        finally:
            D.BASE = orig

    def test_orphan_and_conflicting_flags_exit_2(self):
        for args in (["--keys"],                                 # 缺动作
                     ["--print-env"], ["--check"],               # 脱离 --keys
                     ["--keys", "--print-env", "--check"],       # 两动作互斥
                     ["--keys", "--check", "--wizard"],          # 与向导互斥
                     ["--keys", "--check", "--want", "rank"]):   # 与 --want 互斥
            r = _run_doctor(args)
            self.assertEqual(r.returncode, 2, args)
            self.assertIn("doctor.py: error:", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
