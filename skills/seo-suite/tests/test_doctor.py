#!/usr/bin/env python3
"""doctor.py 回归:凭证分层 T0→T3 逐级 / gsc.json 只探键名不读值(输出无真实值)/
redact 三正则 / 编译检查抓故意语法错 / 退出码契约 0|3 / --json 形状 / channels 只报
渠道名不报值。standalone:临时 HOME 与注入 env dict,零网络(--net 路径不触发)。
可直接 `python3 tests/test_doctor.py`,亦被 tests/run_tests.py 自动装载。"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import doctor as D  # noqa: E402

DOCTOR = os.path.join(SCRIPTS, "doctor.py")


def _home_with_gsc(payload=None):
    """临时 HOME;payload 非 None 时写 ~/.config/seo-suite/gsc.json。"""
    home = tempfile.mkdtemp(prefix="doc_home_")
    if payload is not None:
        d = os.path.join(home, ".config", "seo-suite")
        os.makedirs(d)
        with open(os.path.join(d, "gsc.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f)
    return home


def _scrub_env(home=None):
    """子进程环境:剥掉凭证变量,注入临时 HOME(tier 判定确定性 T0/T2/T3)。"""
    env = {k: v for k, v in os.environ.items()
           if k not in ("PSI_API_KEY", "CRUX_API_KEY")}
    env["PYTHONIOENCODING"] = "utf-8"
    if home is not None:
        env["HOME"] = home
    return env


def _run_cli(args, home):
    return subprocess.run([sys.executable, DOCTOR, *args], capture_output=True,
                          text=True, encoding="utf-8", env=_scrub_env(home))


class DetectTierTests(unittest.TestCase):
    """T0 无凭证 → T1 环境变量 → T2 gsc.json credentials 键 → T3 ga4_property_id。"""

    def test_tier0_no_credentials(self):
        t = D.detect_tier(env={}, home=tempfile.mkdtemp(prefix="doc_t0_"))
        self.assertEqual(t["tier"], 0)
        self.assertEqual(t["capabilities"], ["static-audit"])
        self.assertIn("PSI_API_KEY", t["missing"])            # 升级指引指向 T1

    def test_tier1_env_keys(self):
        home = tempfile.mkdtemp(prefix="doc_t1_")
        t = D.detect_tier(env={"PSI_API_KEY": "k", "CRUX_API_KEY": "k"}, home=home)
        self.assertEqual(t["tier"], 1)
        self.assertEqual(t["capabilities"], ["static-audit", "psi", "crux"])
        self.assertIn("gsc.json", t["missing"])               # 指引指向 T2
        only_crux = D.detect_tier(env={"CRUX_API_KEY": "k"}, home=home)
        self.assertEqual(only_crux["capabilities"], ["static-audit", "crux"])

    def test_tier2_gsc_credentials_key(self):
        home = _home_with_gsc({"credentials": {"client_id": "x", "token": "y"}})
        t = D.detect_tier(env={}, home=home)
        self.assertEqual(t["tier"], 2)
        self.assertIn("gsc", t["capabilities"])
        self.assertIn("ga4_property_id", t["missing"])        # 指引指向 T3

    def test_tier3_ga4_property_id(self):
        home = _home_with_gsc({"credentials": {}, "ga4_property_id": "123"})
        t = D.detect_tier(env={"PSI_API_KEY": "k"}, home=home)
        self.assertEqual(t["tier"], 3)
        self.assertEqual(t["capabilities"], ["static-audit", "psi", "gsc", "ga4"])
        self.assertEqual(t["missing"], "")                    # 全解锁

    def test_ga4_without_credentials_grants_nothing(self):
        """ga4_property_id 单独在场不解锁——T2 的闸门是 credentials 键。"""
        t = D.detect_tier(env={}, home=_home_with_gsc({"ga4_property_id": "123"}))
        self.assertEqual(t["tier"], 0)
        self.assertNotIn("gsc", t["capabilities"])

    def test_gsc_unparseable_json_no_crash(self):
        home = _home_with_gsc({})                             # 先建文件,再覆写坏 JSON
        with open(os.path.join(home, ".config", "seo-suite", "gsc.json"),
                  "w", encoding="utf-8") as f:
            f.write("{not-json")
        t = D.detect_tier(env={"PSI_API_KEY": "k"}, home=home)
        self.assertEqual(t["tier"], 1)                        # 坏文件按无 GSC 计,不炸


class RedactTests(unittest.TestCase):
    """redact 三正则(claude-seo doctor 口径):home / email / secret 键值 + 幂等。"""

    def test_three_regexes(self):
        home = tempfile.mkdtemp(prefix="doc_red_")
        s = ("config at %s token=abc123 password: hunter2 "
             "ops@example.com api_key: \"sk-xyz\"" % os.path.join(home, "gsc.json"))
        r = D.redact(s, home=home)
        self.assertNotIn(home, r)
        self.assertIn("<home>/gsc.json", r)                   # 1) home 路径
        self.assertNotIn("ops@example.com", r)
        self.assertIn("<redacted-email>", r)                  # 2) email
        for leak in ("abc123", "hunter2", "sk-xyz"):          # 3) token/password/api_key 值
            self.assertNotIn(leak, r)
        self.assertIn("token=<redacted>", r)                  # 键名保留便于排查
        self.assertIn("api_key", r)
        self.assertEqual(D.redact(r, home=home), r)           # 幂等


class CompileCheckTests(unittest.TestCase):
    """py_compile 批量:能抓故意语法错;失败清单只列 basename。"""

    def test_syntax_error_caught_with_basename_only(self):
        td = tempfile.mkdtemp(prefix="doc_cpl_")
        with open(os.path.join(td, "ok_file.py"), "w") as f:
            f.write("x = 1\n")
        with open(os.path.join(td, "broken.py"), "w") as f:
            f.write("def f(:\n    pass\n")
        c = D.check_scripts(td)
        self.assertFalse(c["pass"])
        self.assertIn("1/2 编译失败", c["detail"])
        names = re.findall(r"[\w.-]+\.py", c["detail"])
        self.assertEqual(names, ["broken.py"])                # 好文件不被点名
        self.assertNotIn(td, c["detail"])                     # 不泄绝对路径

    def test_empty_scripts_dir_fails(self):
        c = D.check_scripts(tempfile.mkdtemp(prefix="doc_empty_"))
        self.assertFalse(c["pass"])


class CheckItemsTests(unittest.TestCase):
    """markets 18 断言 / channels 只报渠道名与已配/未配,绝不打印值。"""

    def test_markets_pass_on_repo_and_fail_on_bad_json(self):
        c = D.check_markets(os.path.join(SCRIPTS, "markets.json"))
        self.assertTrue(c["pass"])
        self.assertIn("18/18", c["detail"])
        bad = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        bad.write("{broken")
        bad.close()
        try:
            c2 = D.check_markets(bad.name)
            self.assertFalse(c2["pass"])
            self.assertIn("不可解析", c2["detail"])
        finally:
            os.unlink(bad.name)

    def test_channels_names_and_states_without_values(self):
        env = {"SEO_MONITOR_SLACK_WEBHOOK": "https://hooks.slack.example/T00/B00/zzz",
               "SEO_MONITOR_TG_TOKEN": "111:AAA-secret", "SEO_MONITOR_TG_CHAT": "42",
               "SEO_MONITOR_SMTP_PASS": "smtp-pass-xyz"}
        tmp = tempfile.mkdtemp(prefix="doc_ch_")
        cfg = os.path.join(tmp, "config.json")
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump({"site": "https://example.com", "channels": {
                "email": {"smtp_host": "smtp.example.com", "from": "a@example.com",
                          "to": ["b@example.com"]},
                "discord": {}}}, f)
        st = D.channel_states(env, cfg)
        self.assertTrue(all(st[k] for k in ("slack", "telegram", "email")))
        self.assertFalse(st["discord"] and st["webhook"])
        c = D.check_channels(env, cfg)
        self.assertTrue(c["pass"])                            # 信息项恒 pass
        self.assertIn("slack=已配", c["detail"])
        self.assertIn("discord=未配", c["detail"])
        for leak in ("zzz", "111:AAA-secret", "smtp-pass-xyz", "smtp.example.com"):
            self.assertNotIn(leak, c["detail"])               # 值绝不出现


class CliContractTests(unittest.TestCase):
    """--json 形状 / 人读标签与省略声明 / 退出码 0=ready、3=需处理 / --fix-tips。"""

    def test_json_shape_and_exit_zero(self):
        home = _home_with_gsc()
        r = _run_cli(["--json"], home)
        self.assertEqual(r.returncode, 0)                     # 本仓环境应 ready
        data = json.loads(r.stdout)
        self.assertEqual(set(data), {"ready", "tier", "checks", "reasons"})
        self.assertTrue(data["ready"])
        self.assertEqual(data["reasons"], [])
        self.assertEqual(set(data["tier"]), {"tier", "capabilities", "missing"})
        self.assertTrue(data["checks"])
        for c in data["checks"]:
            self.assertEqual(set(c), {"id", "pass", "detail"})
        ids = {c["id"] for c in data["checks"]}
        self.assertTrue({"python", "markets", "templates", "scripts",
                         "tests", "channels"} <= ids)
        self.assertNotIn("net", ids)                          # 默认零网络

    def test_human_labels_and_omission_note(self):
        r = _run_cli([], _home_with_gsc())
        self.assertEqual(r.returncode, 0)
        for label in ("Python:", "markets:", "templates:", "scripts:",
                      "channels:", "tier:", "ready:"):
            self.assertIn(label, r.stdout)
        self.assertIn("intentionally omits absolute paths and environment values",
                      r.stdout)
        self.assertNotIn("net:", r.stdout)                    # 未开 --net 无该行

    def test_gsc_probe_reports_keys_not_values(self):
        """键名探测:升级指引可见键名(credentials/ga4_property_id),值绝不进输出。"""
        secret = "GSC-REFRESH-TOKEN-DO-NOT-PRINT"
        home = _home_with_gsc({"credentials": {"refresh_token": secret}})
        r = _run_cli(["--json"], home)
        self.assertNotIn(secret, r.stdout)
        data = json.loads(r.stdout)
        self.assertEqual(data["tier"]["tier"], 2)
        self.assertIn("ga4_property_id", r.stdout)            # 键名可见(升级指引)
        home3 = _home_with_gsc({"credentials": {"refresh_token": secret},
                                "ga4_property_id": "properties/42"})
        r3 = _run_cli(["--json"], home3)
        self.assertNotIn(secret, r3.stdout)
        self.assertNotIn("properties/42", r3.stdout)          # 值(ga4)绝不出现
        self.assertEqual(json.loads(r3.stdout)["tier"]["tier"], 3)

    def test_exit_3_and_fix_tips_on_broken_base(self):
        """坏基座(markets 坏 JSON/缺 templates+tests/scripts 语法错)→ ready=no、
        rc=3,--fix-tips 对每个硬失败给一条建议(python 通过则不给 python 的)。"""
        base = tempfile.mkdtemp(prefix="doc_base_")
        os.makedirs(os.path.join(base, "scripts"))
        with open(os.path.join(base, "scripts", "markets.json"), "w") as f:
            f.write("{bad")
        with open(os.path.join(base, "scripts", "broken.py"), "w") as f:
            f.write("def (:\n")
        orig = D.BASE
        D.BASE = base
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = D.main([])
            self.assertEqual(rc, 3)
            out = buf.getvalue()
            self.assertIn("ready: no", out)
            buf2 = io.StringIO()
            with contextlib.redirect_stdout(buf2):
                rc2 = D.main(["--fix-tips"])
            self.assertEqual(rc2, 3)
            tips = buf2.getvalue()
            self.assertEqual(tips.count("fix-tip("), 4)       # markets/templates/scripts/tests
            self.assertNotIn("fix-tip(Python)", tips)         # python 项通过,不凑数
            self.assertIn("py_compile", tips)
        finally:
            D.BASE = orig


class WizardUnitTests(unittest.TestCase):
    """--wizard 数据接入向导(单元层):--want 解析/锚点内链守护/复用 detect_tier 的
    逐 tier 状态/探测只看徽章绝不读值。"""

    def test_parse_want_default_dedupe_and_invalid(self):
        self.assertEqual(D.parse_want(""), list(D.WANT_CHOICES))   # 空 → 全列 8 项
        self.assertEqual(D.parse_want("  "), list(D.WANT_CHOICES))
        self.assertEqual(D.parse_want("rank, rank,CWV"), ["rank", "cwv"])  # 去重+去空白+大小写
        with self.assertRaises(ValueError):
            D.parse_want("rank,nope")

    def test_anchors_resolve_in_onboarding_doc(self):
        """向导输出的每个锚点必须真实存在于 data-onboarding.md(内链纪律)。"""
        doc = os.path.join(os.path.dirname(SCRIPTS), "references", "overview",
                           "data-onboarding.md")
        with open(doc, encoding="utf-8") as f:
            body = f.read()
        self.assertEqual(sorted(D.WANT_ITEMS), sorted(D.WANT_CHOICES))  # 目录=枚举,一一对应
        for spec in D.WANT_ITEMS.values():
            self.assertIn('id="%s"' % spec["anchor"], body)             # 锚点在场
            self.assertIn("data-onboarding.md", D.ONBOARDING_DOC)

    def test_wizard_report_t0_states(self):
        home = _home_with_gsc()
        tier, wiz = D.wizard_report(["seo-audit", "rank", "backlinks", "cwv", "keywords"],
                                    env={}, home=home)
        st = {i["id"]: i["configured"] for i in wiz["items"]}
        self.assertEqual(tier["tier"], 0)
        self.assertEqual((st["seo-audit"], st["rank"], st["backlinks"], st["cwv"],
                          st["keywords"]), (True, False, False, False, False))
        self.assertEqual(wiz["items_ready"], 1)
        self.assertEqual(wiz["items_total"], 5)
        self.assertEqual(wiz["runnable_capabilities"], 1)               # static-audit
        kw = next(i for i in wiz["items"] if i["id"] == "keywords")
        self.assertIn("自备导出文件", kw["status"])                     # 自带导出类如实说明

    def test_wizard_report_t1_cwv_and_t2_gsc(self):
        home = _home_with_gsc()
        t1, w1 = D.wizard_report(["cwv"], env={"PSI_API_KEY": "k"}, home=home)
        self.assertEqual(t1["tier"], 1)
        self.assertTrue(w1["items"][0]["configured"])
        home2 = _home_with_gsc({"credentials": {"client_id": "x"}})
        t2, w2 = D.wizard_report(["rank", "backlinks"], env={}, home=home2)
        self.assertEqual(t2["tier"], 2)
        self.assertTrue(all(i["configured"] for i in w2["items"]))      # T2 解锁两项

    def test_wizard_report_never_leaks_secret_values(self):
        """gsc.json 里放了显眼 secret:向导条目任何字段不得出现该值(只看徽章不读值)。"""
        secret = "GSC-WIZARD-REFRESH-TOKEN-X"
        home = _home_with_gsc({"credentials": {"refresh_token": secret}})
        _, wiz = D.wizard_report(list(D.WANT_CHOICES), env={}, home=home)
        self.assertNotIn(secret, json.dumps(wiz, ensure_ascii=False))


class WizardCliTests(unittest.TestCase):
    """--wizard CLI 契约:人读四行结构+结尾 tier 行/--want 子集与非法值 exit 2/
    --json 形状/已配 ✓ 且值不外泄/退出码契约不因向导改变。"""

    def test_human_wizard_full_list_and_summary(self):
        r = _run_cli(["--wizard"], _home_with_gsc())
        self.assertEqual(r.returncode, 0)
        self.assertIn("wizard: 数据接入清单(8 项", r.stdout)
        self.assertIn("[1/8] seo-audit — 全站体检", r.stdout)
        for line in ("  数据: ", "  状态: ", "  获取: ", "  降级: "):
            self.assertIn(line, r.stdout)
        self.assertIn("data-onboarding.md#want-seo-audit", r.stdout)   # 锚点引用可见
        self.assertRegex(r.stdout, r"tier: T\d — 立即可跑能力 \d+ 项")
        self.assertIn("清单就绪 2/8", r.stdout)                        # T0:seo-audit+geo
        self.assertIn("ready: yes", r.stdout)
        self.assertIn("intentionally omits absolute paths", r.stdout)

    def test_wizard_want_subset_only_lists_asked(self):
        r = _run_cli(["--wizard", "--want", "rank,cwv"], _home_with_gsc())
        self.assertEqual(r.returncode, 0)
        self.assertIn("wizard: 数据接入清单(2 项", r.stdout)
        self.assertIn("[1/2] rank", r.stdout)
        self.assertIn("[2/2] cwv", r.stdout)
        self.assertNotIn("[3/", r.stdout)                              # 未点名的项不出现

    def test_wizard_invalid_want_and_orphan_want_exit_2(self):
        bad = _run_cli(["--wizard", "--want", "nope"], _home_with_gsc())
        self.assertEqual(bad.returncode, 2)
        self.assertIn("--want", bad.stderr)
        orphan = _run_cli(["--want", "rank"], _home_with_gsc())        # --want 不得脱离向导
        self.assertEqual(orphan.returncode, 2)

    def test_wizard_json_shape(self):
        r = _run_cli(["--wizard", "--json"], _home_with_gsc())
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(set(data), {"ready", "tier", "wizard", "reasons"})  # 同构扩展
        self.assertEqual(set(data["tier"]), {"tier", "capabilities", "missing"})
        w = data["wizard"]
        self.assertEqual(set(w), {"want", "items", "runnable_capabilities",
                                  "items_ready", "items_total"})
        self.assertEqual([i["id"] for i in w["items"]], list(D.WANT_CHOICES))
        for it in w["items"]:
            self.assertEqual(set(it), {"id", "label", "sources", "configured", "status",
                                       "how", "anchor", "doc", "fallback"})
            self.assertIsInstance(it["configured"], bool)
        self.assertEqual(w["items_total"], 8)

    def test_wizard_configured_checkmark_and_no_key_leak(self):
        """注入临时 PSI key → cwv 行 ✓ 已配;key 值本身绝不进输出(只探存在性+redact)。"""
        env = _scrub_env(_home_with_gsc())
        env["PSI_API_KEY"] = "WIZ-SECRET-PSI-KEY-42"
        r = subprocess.run([sys.executable, DOCTOR, "--wizard", "--want", "cwv"],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("✓ 已配(PSI/CrUX key 在场)", r.stdout)
        self.assertNotIn("WIZ-SECRET-PSI-KEY-42", r.stdout)
        self.assertIn("清单就绪 1/1", r.stdout)

    def test_wizard_exit_code_follows_ready_contract(self):
        """向导不改 ready 判定:坏基座(markets 坏 JSON+语法错)→ --wizard rc=3。"""
        base = tempfile.mkdtemp(prefix="doc_wiz_")
        os.makedirs(os.path.join(base, "scripts"))
        with open(os.path.join(base, "scripts", "markets.json"), "w") as f:
            f.write("{bad")
        with open(os.path.join(base, "scripts", "broken.py"), "w") as f:
            f.write("def (:\n")
        orig = D.BASE
        D.BASE = base
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = D.main(["--wizard"])
            self.assertEqual(rc, 3)
            self.assertIn("ready: no", buf.getvalue())     # 契约信息仍在结尾
            self.assertIn("wizard: 数据接入清单", buf.getvalue())
        finally:
            D.BASE = orig


if __name__ == "__main__":
    unittest.main(verbosity=1)
