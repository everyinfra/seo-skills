#!/usr/bin/env python3
"""citation_gaps.py 测试:qualifying 过滤(五状态)/自有域排除/域名分组聚合/
has_competitor_run 高优先排序/CSV 列格式/registrable_domain 双段后缀/JSON 形状。
standalone(自带 run_script 助手,合成 panel.json,零网络):
python3 tests/test_citation_gaps.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。"""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import citation_gaps as cg  # noqa: E402  (需先入 SCRIPTS 路径)


def run_script(name, args=(), stdin=None):
    """独立助手(与 run_tests.py 同形):子进程跑 scripts/ 下脚本,捕获输出。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def make_panel():
    """合成面板:2 runs / 8 cells / 5 qualifying;覆盖五状态、自有域混入、
    双段后缀域、同 cell 重复 URL(每答案每 URL 至多计 1 次)。"""
    P = ["best crm", "crm pricing", "helpdesk tools", "crm comparison", "crm migration"]
    return {
        "brand": "Acme", "aliases": [], "domain": "acme.ai", "prompts": P,
        "engines": ["chatgpt", "perplexity"],
        "runs": [
            {"run_id": "r1", "engine": "chatgpt", "date": "2026-10-01T00:00:00",
             "brand": "Acme", "results": {
                 P[0]: {"state": "brand_absent", "mentioned": 0, "cited": 0,
                        "cited_urls": ["https://www.g2.com/crm/best",
                                       "https://hubspot.com/crm"]},
                 P[1]: {"state": "name_only_mention", "mentioned": 1, "cited": 0,
                        "cited_urls": ["https://www.g2.com/crm/best",
                                       "https://docs.zendesk.com/pricing"]},
                 P[2]: {"state": "cited_brand", "mentioned": 1, "cited": 1,
                        "cited_urls": ["https://acme.ai/helpdesk",
                                       "https://g2.com/helpdesk"]},
                 P[3]: {"state": "failed", "mentioned": 0, "cited": 0, "cited_urls": []},
                 P[4]: {"state": "no_answer", "mentioned": 0, "cited": 0,
                        "cited_urls": []}}},
            {"run_id": "r2", "engine": "perplexity", "date": "2026-10-02T00:00:00",
             "brand": "Acme", "results": {
                 P[0]: {"state": "brand_absent", "mentioned": 0, "cited": 0,
                        "cited_urls": ["https://www.g2.com/crm/best",
                                       "https://www.g2.com/crm/best"]},   # 同 cell 重复 → 去重
                 P[1]: {"state": "brand_absent", "mentioned": 0, "cited": 0,
                        "cited_urls": ["https://blog.hubspot.co.uk/pricing-guide"]},
                 P[2]: {"state": "brand_absent", "mentioned": 0, "cited": 0,
                        "cited_urls": ["https://acme.ai/guide-untracked",
                                       "https://www.capterra.com/helpdesk"]}}},
        ]}


G2_URL = "https://www.g2.com/crm/best"


class RegistrableDomainTests(unittest.TestCase):
    """双段后缀(co.uk/com.cn/co.jp)取三段;www/端口/userinfo/query 清洗;单段原样。"""

    def test_two_label_suffixes_take_three(self):
        self.assertEqual(cg.registrable_domain("https://www.acme.co.uk/a?b=1"), "acme.co.uk")
        self.assertEqual(cg.registrable_domain("https://shop.example.com.cn/x#f"), "example.com.cn")
        self.assertEqual(cg.registrable_domain("http://u:pw@www.site.co.jp:8080/x"), "site.co.jp")
        self.assertEqual(cg.registrable_domain("https://blog.hubspot.co.uk/pricing-guide"),
                         "hubspot.co.uk")

    def test_plain_two_labels_and_edges(self):
        self.assertEqual(cg.registrable_domain("https://www.g2.com/crm/best"), "g2.com")
        self.assertEqual(cg.registrable_domain("https://docs.zendesk.com/pricing"), "zendesk.com")
        self.assertEqual(cg.registrable_domain("example.com"), "example.com")
        self.assertEqual(cg.registrable_domain("not-a-url"), "not-a-url")   # 单段原样
        self.assertEqual(cg.registrable_domain(""), "")


class AlgorithmTests(unittest.TestCase):
    """纯函数:qualifying 过滤 / 自有域排除 / 域名分组 / 高优先排序 / brand-domains 并集。"""

    @classmethod
    def setUpClass(cls):
        cls.panel = make_panel()
        cls.brands = cg.parse_brand_domains("acme.ai, ACME-CDN.com", cls.panel)
        cls.urls, cls.doms, cls.stats = cg.compute_opps(cls.panel, cls.brands)
        cls.by_url = {o["url"]: o for o in cls.urls}

    def test_brand_domains_union_with_panel(self):
        self.assertEqual(self.brands, {"acme.ai", "acme-cdn.com"})   # 面板 domain 自动并入

    def test_qualifying_filter_five_states(self):
        """cited_brand 的 cell(含其竞品 URL)与 failed/no_answer 均不入;仅
        brand_absent/name_only_mention 且有 cited_urls 的 cell 计入。"""
        self.assertEqual((self.stats["runs"], self.stats["cells"], self.stats["qualifying"]),
                         (2, 8, 5))
        self.assertNotIn("https://g2.com/helpdesk", self.by_url)   # cited_brand cell 不算缺口
        self.assertEqual(len(self.by_url), 5)

    def test_own_domains_excluded(self):
        self.assertFalse(any("acme.ai" in u or "acme-cdn.com" in u for u in self.by_url))
        self.assertEqual(self.stats["own_cited"], 1)               # qualifying cell 内自有域 1 次
        self.assertIn("https://www.capterra.com/helpdesk", self.by_url)  # 同 cell 非自有域照常计入

    def test_accumulation_and_per_cell_dedupe(self):
        g2 = self.by_url[G2_URL]
        self.assertEqual(g2["count"], 3)                           # r1×2 + r2×1(重复 URL 去重)
        self.assertEqual(g2["prompts"], {"best crm", "crm pricing"})
        self.assertEqual(g2["providers"], {"chatgpt", "perplexity"})
        self.assertTrue(g2["has_competitor_run"])
        self.assertEqual(g2["competitors"], {"hubspot.com", "zendesk.com"})

    def test_domain_grouping(self):
        g2 = next(g for g in self.doms if g["domain"] == "g2.com")
        self.assertEqual(g2["count"], 3)                           # 总引用 = 域内 URL count 之和
        self.assertEqual(g2["pages"], {G2_URL})                    # 页面数 = 去重 URL 集
        self.assertEqual(g2["prompts"], {"best crm", "crm pricing"})
        self.assertEqual(g2["competitors"], {"hubspot.com", "zendesk.com"})
        self.assertEqual(self.stats["domains"], 5)

    def test_has_competitor_run_priority_sort(self):
        """竞品同场降序 → count 降序;高优先 URL/域一律排在 Standard 之前。"""
        self.assertEqual([o["url"] for o in self.urls[:3]],
                         [G2_URL, "https://docs.zendesk.com/pricing", "https://hubspot.com/crm"])
        self.assertTrue(all(o["has_competitor_run"] for o in self.urls[:3]))
        self.assertFalse(any(o["has_competitor_run"] for o in self.urls[3:]))
        self.assertEqual(self.doms[0]["domain"], "g2.com")         # 总引用最高且竞品同场
        self.assertEqual([g["domain"] for g in self.doms][-2:],
                         ["capterra.com", "hubspot.co.uk"])        # Standard 殿后,按域名升序
        self.assertEqual(cg.priority_of(True), "High")
        self.assertEqual(cg.priority_of(False), "Standard")

    def test_outreach_tip_copy(self):
        g2 = next(g for g in self.doms if g["domain"] == "g2.com")
        cap = next(g for g in self.doms if g["domain"] == "capterra.com")
        self.assertEqual(cg.outreach_tip(g2),
                         "竞品 hubspot.com,zendesk.com 在 g2.com 被引用"
                         "——考虑贡献内容或争取列表位直接竞争")
        self.assertEqual(cg.outreach_tip(cap),
                         "AI 模型在 1 个追踪 prompt 引用 capterra.com,"
                         "获得收录可提升 AI 可见性")


class CliTests(unittest.TestCase):
    """CLI 全链路(subprocess,合成 panel.json 临时文件):markdown/CSV/JSON/--help。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="citation_gaps_")
        cls.panel_path = os.path.join(cls.tmp, "panel.json")
        with open(cls.panel_path, "w", encoding="utf-8") as f:
            json.dump(make_panel(), f, ensure_ascii=False, indent=2)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _run(self, *extra):
        return run_script("citation_gaps.py",
                          ["--panel", self.panel_path,
                           "--brand-domains", "acme.ai,acme-cdn.com", *extra])

    def test_markdown_report_tables_and_copy(self):
        r = self._run()
        self.assertEqual(r.returncode, 0)
        self.assertIn("qualifying=5", r.stdout)
        self.assertIn("自有域被引 1 次不计", r.stdout)
        self.assertIn("| g2.com | 3 | 1 | hubspot.com,zendesk.com | 2 | chatgpt,perplexity | High |",
                      r.stdout)
        self.assertIn("[High] g2.com:竞品 hubspot.com,zendesk.com 在 g2.com 被引用"
                      "——考虑贡献内容或争取列表位直接竞争", r.stdout)
        self.assertIn("[Standard] capterra.com:AI 模型在 1 个追踪 prompt 引用 capterra.com,"
                      "获得收录可提升 AI 可见性", r.stdout)
        self.assertIn("cite_domain.py", r.stdout)                  # 串联提示在场

    def test_csv_columns_and_rows(self):
        path = os.path.join(self.tmp, "gaps.csv")
        r = self._run("--csv", path)
        self.assertEqual(r.returncode, 0)
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[0], ["Domain", "URL", "Citations", "Prompts", "Providers",
                                   "Competitors Mentioned", "Priority"])
        self.assertEqual(len(rows), 6)                            # 表头 + 5 URL
        self.assertEqual(rows[1], ["g2.com", G2_URL, "3", "best crm|crm pricing",
                                   "chatgpt,perplexity", "hubspot.com,zendesk.com", "High"])
        self.assertEqual(rows[2][0], "zendesk.com")               # 竞品同场(count 1)先于 Standard
        self.assertEqual(rows[-1], ["capterra.com", "https://www.capterra.com/helpdesk", "1",
                                    "helpdesk tools", "perplexity", "", "Standard"])
        self.assertEqual({r[-1] for r in rows[1:]}, {"High", "Standard"})

    def test_json_shape(self):
        path = os.path.join(self.tmp, "gaps.json")
        r = self._run("--json", path)
        self.assertEqual(r.returncode, 0)
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertEqual(payload["stats"]["qualifying"], 5)
        self.assertEqual(payload["stats"]["high_priority"], 3)
        self.assertEqual(sorted(payload["brand_domains"]), ["acme-cdn.com", "acme.ai"])
        self.assertEqual(payload["urls"][0]["url"], G2_URL)
        self.assertEqual(payload["urls"][0]["priority"], "High")
        self.assertEqual(payload["urls"][0]["competitors"], ["hubspot.com", "zendesk.com"])
        self.assertEqual(payload["domains"][0]["domain"], "g2.com")
        self.assertEqual(payload["domains"][0]["pages"], [G2_URL])
        self.assertIn("直接竞争", payload["outreach_tips"]["g2.com"])

    def test_no_gap_panel_exits_clean(self):
        p2 = os.path.join(self.tmp, "panel2.json")
        panel = make_panel()
        panel["runs"] = [panel["runs"][0]]                          # 只剩含 cited_brand 的 run
        panel["runs"][0] = {"run_id": "x", "engine": "chatgpt", "date": "d",
                            "brand": "Acme",
                            "results": {"helpdesk tools": panel["runs"][0]["results"]["helpdesk tools"]}}
        with open(p2, "w", encoding="utf-8") as f:
            json.dump(panel, f)
        r = run_script("citation_gaps.py", ["--panel", p2, "--brand-domains", "acme.ai"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("无引用缺口", r.stdout)

    def test_help_and_self_test(self):
        r = run_script("citation_gaps.py", ["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("citation_panel", r.stdout + r.stderr)
        st = run_script("citation_gaps.py", ["--self-test"])
        self.assertEqual(st.returncode, 0)
        self.assertIn("[self-test] PASS citation_gaps", st.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
