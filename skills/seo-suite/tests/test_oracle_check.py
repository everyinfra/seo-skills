#!/usr/bin/env python3
"""oracle_check.py 测试(Athena Oracle 前置核查,合成数据,零网络)。
覆盖:受限 YAML 子集解析 / 数字冲突(价格=critical) / 日期冲突 / 布尔冲突 /
无冲突不报 / 25 条门槛警告(两侧) / Inaccuracy% 与 model_accuracy 计算 /
findings.json 状态保持(ignored 退出指标、possible_sources 续传) / --json 形状 / --help。
standalone(自带 run_script 助手): python3 tests/test_oracle_check.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import oracle_check as oc  # noqa: E402  (需先入 SCRIPTS 路径;import 期无副作用)


def run_script(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "oracle_check.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_file(content, suffix):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


FACTS_YAML = """\
brand: Acme
facts:
  - fact: "Acme Pro 定价为 $49/月,按年计费为 $39/月"
    record: offerings
    source: https://acme.ai/pricing
    date: 2026-10-01
    confidence: high
  - fact: "Acme 成立于 2015 年"
    record: company
    source: https://acme.ai/about
    date: 2026-08-12
    confidence: high
  - fact: "Acme 支持 SSO 登录,仅 Pro 计划"
    record: offerings
    source: https://docs.acme.ai/sso
    date: 2026-07-20
    confidence: high
"""

RESPONSES = [
    {"prompt": "best crm pricing", "engine": "chatgpt",
     "text": "Acme Pro costs $29 per month and includes 20 seats.", "mentions": ["Acme"]},
    {"prompt": "acme company history", "engine": "chatgpt",
     "text": "Acme, founded in 2012, is a CRM vendor based in Berlin.", "mentions": ["Acme"]},
    {"prompt": "does acme support sso", "engine": "perplexity",
     "text": "Acme does not support SSO login at this time.", "mentions": ["Acme"]},
    {"prompt": "acme free plan limits", "engine": "perplexity",
     "text": "The free plan supports 3 projects and Acme Pro is $49 per month.",
     "mentions": ["Acme"]},
]


class OracleCheckTests(unittest.TestCase):
    """合成 fixtures:chatgpt×2(价格数字错/年份错) + perplexity×2(SSO 布尔错/干净)。"""

    @classmethod
    def setUpClass(cls):
        cls.facts = tmp_file(FACTS_YAML, ".yaml")
        cls.responses = tmp_file(json.dumps(RESPONSES, ensure_ascii=False), ".json")
        cls.state_dir = tempfile.mkdtemp(prefix="oracle_check_")

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.facts)
        os.unlink(cls.responses)
        for name in os.listdir(cls.state_dir):
            os.unlink(os.path.join(cls.state_dir, name))
        os.rmdir(cls.state_dir)

    def _run(self, *extra):
        # 默认 --out 指向临时目录:不向 CWD 滴 findings.json(显式 --out 在其后,可覆盖)
        return run_script(["--facts", self.facts, "--responses", self.responses,
                           "--out", os.path.join(self.state_dir, "findings.json"), *extra])

    # ---- 基础 ----

    def test_help_exits_zero(self):
        r = run_script(["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("brand.yaml", r.stdout)
        self.assertIn("--responses", r.stdout)

    def test_yaml_subset_parser(self):
        brand, facts, warnings = oc.parse_facts_yaml(self.facts)
        self.assertEqual(brand, "Acme")
        self.assertEqual(len(facts), 3)
        self.assertEqual((facts[0]["record"], facts[0]["confidence"]),
                         ("offerings", "high"))
        self.assertEqual(facts[1]["record"], "company")
        self.assertIn("$49", facts[0]["fact"])
        # 受限子集解析:整段/二元组关键词与货币值抽取
        terms = oc.extract_topic_terms(facts[0]["fact"])
        self.assertIn("acme", terms)
        self.assertIn("定价", terms)
        vals = oc.extract_values(facts[0]["fact"])
        self.assertEqual(sorted(v["value"] for v in vals if v["kind"] == "currency"),
                         [39.0, 49.0])

    # ---- 冲突检出 ----

    def test_number_conflict_price_is_critical(self):
        r = self._run()
        self.assertEqual(r.returncode, 0)
        self.assertIn("数字冲突", r.stdout)
        self.assertIn("$29", r.stdout)                      # AI 错误价格在命中句里
        self.assertIn("$49", r.stdout)                      # 已验证事实在报告里
        self.assertIn("F001", r.stdout)
        self.assertIn("critical", r.stdout)                 # 涉及定价 → critical

    def test_date_conflict_year_mismatch(self):
        r = self._run()
        self.assertIn("日期冲突", r.stdout)
        self.assertIn("2015", r.stdout)
        self.assertIn("2012", r.stdout)

    def test_boolean_conflict_negation_reversal(self):
        r = self._run()
        self.assertIn("布尔冲突", r.stdout)
        self.assertIn("sso", r.stdout.lower())
        self.assertIn("正则近似", r.stdout)

    def test_no_conflict_not_flagged(self):
        """正确价格($49)与无关句不产 finding;干净响应进 model_accuracy 分母。"""
        r = self._run()
        self.assertIn("F003", r.stdout)                     # 三条 finding:两条 chatgpt + 一条 perplexity
        self.assertNotIn("F004", r.stdout)                  # 第 4 条响应(正确 $49)不报
        self.assertNotIn("3 projects", r.stdout)

    # ---- 门槛警告 ----

    def test_fact_floor_warning_both_sides(self):
        r = self._run()
        self.assertIn("样本不足", r.stdout)                  # 3 条 <25
        self.assertIn("25 条已验证 facts", r.stdout)
        self.assertIn("facts=3 < 25", r.stdout)
        # 25 条整 → 无警告
        lines = ["brand: Acme", "facts:"]
        for i in range(25):
            lines += ['  - fact: "Acme 的内部事实第 %d 条说明"' % (i + 2),
                      "    record: company",
                      "    source: internal/handbook",
                      "    date: 2026-10-01",
                      "    confidence: med"]
        big = tmp_file("\n".join(lines) + "\n", ".yaml")
        clean = tmp_file(json.dumps(
            [{"prompt": "what is acme", "engine": "chatgpt",
              "text": "Acme is a CRM company.", "mentions": ["Acme"]}], ensure_ascii=False),
            ".json")
        try:
            r2 = run_script(["--facts", big, "--responses", clean,
                             "--out", os.path.join(self.state_dir, "floor.json")])
            self.assertEqual(r2.returncode, 0)
            self.assertNotIn("样本不足", r2.stdout)
        finally:
            os.unlink(big)
            os.unlink(clean)

    # ---- 指标 ----

    def test_inaccuracy_and_model_accuracy(self):
        r = self._run()
        self.assertIn("Inaccuracy% = 75.0%(3/4 响应含 active finding)", r.stdout)
        self.assertIn("chatgpt: 0.0%(0/2 无 finding)", r.stdout)
        self.assertIn("perplexity: 50.0%(1/2 无 finding)", r.stdout)
        self.assertIn("offerings: 2", r.stdout)             # 价格 + SSO 均为 offerings 记录
        self.assertIn("company: 1", r.stdout)               # 成立年份为 company 记录

    # ---- 状态机 ----

    def test_findings_state_preserved_across_reruns(self):
        tmp = tempfile.mkdtemp(prefix="oracle_state_")
        out = os.path.join(tmp, "findings.json")
        r1 = self._run("--out", out)
        self.assertIn("[pending]", r1.stdout)
        with open(out, encoding="utf-8") as f:
            state = json.load(f)
        self.assertEqual(len(state["findings"]), 3)
        self.assertTrue(all(f["status"] == "pending" for f in state["findings"]))
        # 人工裁决:F001(价格)确认属实但已由 agent 调查过来源;F003 改 ignored
        for f in state["findings"]:
            if f["id"] == "F001":
                f["possible_sources"] = ["https://g2.com/acme-pricing"]
            if f["id"] == "F003":
                f["status"] = "ignored"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
        r2 = self._run("--out", out)
        self.assertIn("[ignored]", r2.stdout)               # 状态续传
        self.assertIn("Inaccuracy% = 50.0%(2/4", r2.stdout)  # ignored 退出指标
        self.assertIn("https://g2.com/acme-pricing", r2.stdout)  # possible_sources 续传
        r3 = self._run("--out", out, "--json")
        payload = json.loads(r3.stdout)
        by_id = {f["id"]: f for f in payload["findings"]}
        self.assertEqual(by_id["F003"]["status"], "ignored")
        self.assertEqual(by_id["F001"]["possible_sources"],
                         ["https://g2.com/acme-pricing"])
        self.assertEqual(by_id["F002"]["status"], "pending")  # 未人工处理的保持 pending

    # ---- --json 输出形状 ----

    def test_json_output_shape(self):
        r = self._run("--json")
        self.assertEqual(r.returncode, 0)
        payload = json.loads(r.stdout)
        for key in ("schema_version", "brand", "facts_count", "responses_count",
                    "warnings", "metrics", "findings", "boundary"):
            self.assertIn(key, payload)
        self.assertEqual(payload["facts_count"], 3)
        self.assertEqual(payload["responses_count"], 4)
        self.assertEqual(payload["metrics"]["inaccuracy_pct"], 75.0)
        self.assertEqual(payload["metrics"]["model_accuracy"]["chatgpt"], 0.0)
        self.assertEqual(payload["metrics"]["topics_ai_gets_wrong"],
                         {"offerings": 2, "company": 1})
        self.assertEqual(len(payload["findings"]), 3)
        f1 = payload["findings"][0]
        for key in ("ai_claim", "known_fact", "why_flagged", "severity",
                    "source_response", "possible_sources", "status"):
            self.assertIn(key, f1)
        self.assertEqual(f1["possible_sources"], [])        # 留空由 agent 填
        self.assertEqual(f1["severity"], "critical")
        self.assertEqual(f1["source_response"]["engine"], "chatgpt")
        self.assertTrue(payload["boundary"])                # 边界声明在场


if __name__ == "__main__":
    unittest.main(verbosity=1)
