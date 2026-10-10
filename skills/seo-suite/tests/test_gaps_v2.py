#!/usr/bin/env python3
"""citation_gaps.py / cite_domain.py v2 扩展测试:来源五分类(Peec 口径,含 overrides)/
gapLabel 七叉决策树(每分支 ≥1 用例)/cite_domain 引用证据清单与 --json/
--json 向后兼容(只新增)。standalone(自带 run_script 助手,合成数据,零网络):
python3 tests/test_gaps_v2.py
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

import citation_gaps as cg   # noqa: E402  (需先入 SCRIPTS 路径)
import cite_domain as cd     # noqa: E402


def run_script(name, args=()):
    """独立助手(与 run_tests.py 同形):子进程跑 scripts/ 下脚本,捕获输出。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def cell(state="brand_absent", mentioned=0, cited=0, urls=()):
    return {"state": state, "mentioned": mentioned, "cited": cited, "cited_urls": list(urls)}


def panel_runs(runs, prompts=None, engines=("chatgpt", "perplexity")):
    """runs = [该 run 的 {prompt: cell}, ...];多 run 同 prompt 用于跨 run 聚合。"""
    prompts = prompts if prompts is not None else sorted({p for r in runs for p in r})
    return {"brand": "Acme", "domain": "acme.ai", "prompts": prompts,
            "engines": list(engines),
            "runs": [{"run_id": "r%d" % i, "engine": engines[i % len(engines)],
                      "date": "2026-10-0%d" % (i + 1), "brand": "Acme", "results": r}
                     for i, r in enumerate(runs)]}


BRANDS = {"acme.ai"}


# ---------- 来源五分类(Peec Source 五分类) ----------

class FiveClassTests(unittest.TestCase):
    """已知清单/词元启发式[推断]/自有域/人工覆盖优先级/行动提示口径。"""

    def test_known_and_token_heuristics(self):
        self.assertEqual(cg.classify_domain("wikipedia.org", set())[0], "Reference")
        self.assertEqual(cg.classify_domain("wikihow.com", set())[1], "token:wiki")
        self.assertEqual(cg.classify_domain("dictionary.com", set())[0], "Reference")
        self.assertEqual(cg.classify_domain("reddit.com", set())[0], "UGC")
        self.assertEqual(cg.classify_domain("forum.acme.io", set())[1], "token:forum")
        self.assertEqual(cg.classify_domain("techcrunch.com", set())[0], "Editorial")
        self.assertEqual(cg.classify_domain("dailywidget.com", set())[1], "token:daily")

    def test_default_corporate_marked_inferred(self):
        cls, basis = cg.classify_domain("hubspot.com", set())
        self.assertEqual((cls, basis), ("Corporate", "default:corporate[推断]"))

    def test_own_domain_detected(self):
        self.assertEqual(cg.classify_domain("acme.ai", BRANDS), ("Own", "own-domain"))

    def test_override_beats_own_and_heuristics(self):
        self.assertEqual(cg.classify_domain("acme.ai", BRANDS, {"acme.ai": "Editorial"}),
                         ("Editorial", "override"))
        self.assertEqual(cg.classify_domain("reddit.com", set(), {"reddit.com": "Corporate"}),
                         ("Corporate", "override"))

    def test_class_actions_peec_mapping(self):
        self.assertIn("PR outreach", cg.SOURCE_CLASS_ACTIONS["Editorial"])
        self.assertIn("合作目录", cg.SOURCE_CLASS_ACTIONS["Corporate"])
        self.assertIn("社区运营", cg.SOURCE_CLASS_ACTIONS["UGC"])
        self.assertIn("更正词条", cg.SOURCE_CLASS_ACTIONS["Reference"])
        self.assertIn("站内改造", cg.SOURCE_CLASS_ACTIONS["Own"])

    def test_load_domain_overrides_valid_and_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok = os.path.join(tmp, "o.json")
            with open(ok, "w", encoding="utf-8") as f:
                json.dump({"G2.com": "ugc", "example.com": "Own website"}, f)
            self.assertEqual(cg.load_domain_overrides(ok),
                             {"g2.com": "UGC", "example.com": "Own"})
            bad = os.path.join(tmp, "bad.json")
            with open(bad, "w", encoding="utf-8") as f:
                json.dump({"g2.com": "Blog"}, f)
            with self.assertRaises(ValueError):
                cg.load_domain_overrides(bad)
            with open(bad, "w", encoding="utf-8") as f:
                json.dump(["g2.com"], f)
            with self.assertRaises(ValueError):
                cg.load_domain_overrides(bad)


# ---------- gapLabel 七叉决策树(niubigeo 口径,每分支 ≥1 用例) ----------

class GapLabelTreeTests(unittest.TestCase):
    """七叉顺序固定,自上而下首个命中;ownedRelevance 缺省时分支 4 降级。"""

    def _one(self, runs, owned=None, prompt="best crm"):
        rows = cg.compute_gap_labels(panel_runs(runs, prompts=[prompt]), BRANDS, owned)
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_branch_0_no_valid_answers(self):
        r = self._one([{"best crm": cell("failed")},
                       {"best crm": cell("no_answer")}])
        self.assertEqual(r["label"], "No completed AI answers")
        self.assertEqual(r["valid_answers"], 0)
        r2 = self._one([{}])                       # prompt 在清单但从未采样
        self.assertEqual(r2["label"], "No completed AI answers")

    def test_branch_1_competitors_own_space(self):
        r = self._one([{"best crm": cell(urls=["https://hubspot.com/x"])},
                       {"best crm": cell(urls=["https://www.g2.com/y"])}])
        self.assertEqual(r["label"], "Competitors own this AI answer space")
        self.assertEqual((r["mentioned"], r["competitor_only_runs"]), (0, 2))

    def test_branch_2_target_absent(self):
        r = self._one([{"best crm": cell(urls=[])},
                       {"best crm": cell(urls=["https://acme.ai/x"])}])  # 仅自有域被引
        self.assertEqual(r["label"], "Target absent from AI answers")
        self.assertEqual(r["competitor_only_runs"], 0)

    def test_branch_3_owned_not_reflected_with_owned_input(self):
        runs = [{"best crm": cell("cited_brand", mentioned=1, cited=1,
                                  urls=["https://acme.ai/x"])},
                {"best crm": cell(urls=["https://acme.ai/guide"])},
                {"best crm": cell(urls=[])}]
        r = self._one(runs, owned={"best crm": 0.7})     # 提及率 1/3<0.5 且 owned≥0.6
        self.assertEqual(r["label"], "Owned content is not reflected")
        self.assertAlmostEqual(r["mention_rate"], 1 / 3)

    def test_branch_3_degrades_without_owned_input(self):
        runs = [{"best crm": cell("cited_brand", mentioned=1, cited=1,
                                  urls=["https://acme.ai/x"])},
                {"best crm": cell(urls=[])},
                {"best crm": cell(urls=[])}]
        r = self._one(runs)                              # 无 owned → 已引=Covered
        self.assertEqual(r["label"], "Covered in this audit")

    def test_branch_4_mentioned_without_citation(self):
        r = self._one([{"best crm": cell("name_only_mention", mentioned=1, cited=0,
                                         urls=["https://g2.com/x"])}])
        self.assertEqual(r["label"], "Mentioned without official citation")
        self.assertEqual(r["own_cited"], 0)

    def test_branch_5_competitors_sporadic(self):
        r = self._one([{"best crm": cell("cited_brand", mentioned=1, cited=1,
                                         urls=["https://acme.ai/x"])},
                       {"best crm": cell(urls=["https://hubspot.com/y"])}])
        self.assertEqual(r["label"], "Competitors still appear without target")

    def test_branch_6_covered(self):
        r = self._one([{"best crm": cell("cited_brand", mentioned=1, cited=1,
                                         urls=["https://acme.ai/x"])},
                       {"best crm": cell("cited_brand", mentioned=1, cited=1,
                                         urls=["https://acme.ai/y"])}])
        self.assertEqual(r["label"], "Covered in this audit")
        self.assertEqual(r["action"], "已覆盖:保持监测,暂不动")

    def test_severity_sort_and_all_labels_present(self):
        panel = panel_runs([{"best crm": cell(urls=["https://hubspot.com/x"])},
                            {"crm pricing": cell("failed")},
                            {"helpdesk": cell("name_only_mention", mentioned=1)}],
                           prompts=["best crm", "crm pricing", "helpdesk"])
        rows = cg.compute_gap_labels(panel, BRANDS)
        self.assertEqual([r["prompt"] for r in rows],
                         ["crm pricing", "best crm", "helpdesk"])   # 按标签严重度升序
        self.assertEqual([r["code"] for r in rows],
                         ["no_valid", "competitor_owned", "mention_no_citation"])


# ---------- citation_gaps CLI:五分类 + gapLabel + 兼容性 ----------

CLI_PANEL = panel_runs([
    {"best crm": cell(urls=["https://www.g2.com/crm/best", "https://hubspot.com/crm"]),
     "crm pricing": cell("name_only_mention", mentioned=1, cited=0,
                         urls=["https://en.wikipedia.org/wiki/CRM"]),
     "helpdesk tools": cell("cited_brand", mentioned=1, cited=1,
                            urls=["https://acme.ai/hd", "https://reddit.com/r/helpdesk"]),
     "crm migration": cell("failed")},
    {"best crm": cell(urls=["https://www.g2.com/crm/best"]),
     "helpdesk tools": cell(urls=["https://reddit.com/r/helpdesk"])}],
    prompts=["best crm", "crm pricing", "helpdesk tools", "crm migration"])

OLD_PAYLOAD_KEYS = {"tool", "panel", "brand", "brand_domains", "stats",
                    "domains", "urls", "outreach_tips"}
OLD_DOM_KEYS = {"domain", "count", "pages", "prompts", "providers",
                "has_competitor_run", "competitors", "priority"}
OLD_URL_KEYS = {"url", "domain", "count", "prompts", "providers",
                "has_competitor_run", "competitors", "priority"}


class GapsCliV2Tests(unittest.TestCase):
    """CLI 全链路:overrides/--owned-relevance/JSON 新字段(只新增)/CSV 列不变。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="gaps_v2_")
        cls.panel_path = os.path.join(cls.tmp, "panel.json")
        with open(cls.panel_path, "w", encoding="utf-8") as f:
            json.dump(CLI_PANEL, f, ensure_ascii=False, indent=2)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _run(self, *extra):
        return run_script("citation_gaps.py",
                          ["--panel", self.panel_path, "--brand-domains", "acme.ai", *extra])

    def test_markdown_new_sections_and_classes(self):
        r = self._run()
        self.assertEqual(r.returncode, 0)
        self.assertIn("来源五分类", r.stdout)
        self.assertIn("| g2.com | Corporate | default:corporate[推断] | 合作目录", r.stdout)
        self.assertIn("| wikipedia.org | Reference | known:wikipedia.org | 更正词条", r.stdout)
        self.assertIn("| reddit.com | UGC | known:reddit.com | 社区运营", r.stdout)
        self.assertIn("gapLabel 七叉", r.stdout)
        self.assertIn("| best crm | Competitors own this AI answer space |", r.stdout)
        self.assertIn("| crm migration | No completed AI answers |", r.stdout)
        self.assertIn("| crm pricing | Mentioned without official citation |", r.stdout)
        self.assertIn("| helpdesk tools | Competitors still appear without target |", r.stdout)
        self.assertIn("ownedRelevance 未提供", r.stdout)          # 降级注明在场

    def test_json_new_fields_and_backward_compat(self):
        path = os.path.join(self.tmp, "gaps.json")
        self.assertEqual(self._run("--json", path).returncode, 0)
        with open(path, encoding="utf-8") as f:
            p = json.load(f)
        self.assertTrue(OLD_PAYLOAD_KEYS <= set(p))               # 旧键全保留
        self.assertEqual(p["source_class_counts"],
                         {"Corporate": 2, "Reference": 1, "UGC": 1})
        by_dom = {d["domain"]: d for d in p["domains"]}
        self.assertTrue(OLD_DOM_KEYS <= set(by_dom["g2.com"]))    # 旧行键全保留
        self.assertEqual(by_dom["g2.com"]["source_class"], "Corporate")
        self.assertEqual(by_dom["reddit.com"]["source_class"], "UGC")
        self.assertTrue(all(OLD_URL_KEYS <= set(u) for u in p["urls"]))
        self.assertEqual(p["owned_relevance_available"], False)
        labels = {g["prompt"]: g["label"] for g in p["gap_labels"]}
        self.assertEqual(labels["best crm"], "Competitors own this AI answer space")
        self.assertEqual(labels["helpdesk tools"], "Competitors still appear without target")

    def test_domain_class_overrides_apply(self):
        ov = os.path.join(self.tmp, "ov.json")
        with open(ov, "w", encoding="utf-8") as f:
            json.dump({"g2.com": "UGC"}, f)
        path = os.path.join(self.tmp, "g2.json")
        r = self._run("--domain-class", ov, "--json", path)
        self.assertEqual(r.returncode, 0)
        with open(path, encoding="utf-8") as f:
            p = json.load(f)
        by_dom = {d["domain"]: d for d in p["domains"]}
        self.assertEqual(by_dom["g2.com"]["source_class"], "UGC")
        self.assertEqual(by_dom["g2.com"]["class_basis"], "override")
        self.assertIn("社区运营", by_dom["g2.com"]["class_action"])
        self.assertEqual(p["source_class_overrides"], ["g2.com"])
        self.assertEqual(p["source_class_counts"], {"Corporate": 1, "Reference": 1, "UGC": 2})
        self.assertIn("| g2.com | UGC | override | 社区运营", r.stdout)

    def test_owned_relevance_flag_end_to_end(self):
        ow = os.path.join(self.tmp, "ow.json")
        with open(ow, "w", encoding="utf-8") as f:
            json.dump({"best crm": 0.9, "crm pricing": 0.2}, f)
        path = os.path.join(self.tmp, "ow.json.out")
        r = self._run("--owned-relevance", ow, "--json", path)
        self.assertEqual(r.returncode, 0)
        with open(path, encoding="utf-8") as f:
            p = json.load(f)
        self.assertTrue(p["owned_relevance_available"])
        by_prompt = {g["prompt"]: g for g in p["gap_labels"]}
        self.assertEqual(by_prompt["best crm"]["owned_relevance"], 0.9)
        self.assertEqual(by_prompt["best crm"]["label"],            # 提及=0 分支先于 owned 分支
                         "Competitors own this AI answer space")
        self.assertIn("ownedRelevance 由 --owned-relevance 提供", r.stdout)

    def test_invalid_domain_class_and_owned_range_exit_1(self):
        bad = os.path.join(self.tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as f:
            json.dump({"g2.com": "Blog"}, f)
        r = self._run("--domain-class", bad)
        self.assertEqual(r.returncode, 1)
        self.assertIn("无效", r.stderr)
        ow = os.path.join(self.tmp, "ow_bad.json")
        with open(ow, "w", encoding="utf-8") as f:
            json.dump({"best crm": 1.5}, f)
        self.assertEqual(self._run("--owned-relevance", ow).returncode, 1)

    def test_csv_header_unchanged_seven_columns(self):
        path = os.path.join(self.tmp, "gaps.csv")
        self.assertEqual(self._run("--csv", path).returncode, 0)
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[0], ["Domain", "URL", "Citations", "Prompts", "Providers",
                                   "Competitors Mentioned", "Priority"])
        self.assertTrue(all(len(r) == 7 for r in rows))


# ---------- cite_domain:证据清单 + --json ----------

CITE_INPUT = {
    "referring_domains": 1200,
    "dr_distribution": {"0-30": 400, "30-50": 400, "50-70": 300, "70-100": 100},
    "anchor_exact_ratio": 0.25,
    "c_block_concentration": 0.15,
    "months": [{"month": "2026-%02d" % i, "links": 40 + i} for i in range(1, 13)],
    "engines_cited": {"chatgpt": 25, "perplexity": 12, "gemini": 3},
    "reviews": ["Acme is great", "Acme saved us", "Acme support is good",
                "love Acme", "Acme forever", "meh", "ok", "Acme again"],
    "brand": "Acme",
    "outbound_links": 800,
    "editorial_ratio": 0.65,
    "link_traffic_coherent": True,
    "manual_penalty": False,
}


class CiteDomainEvidenceTests(unittest.TestCase):
    """CITATION_EVIDENCE(5 家字段路径)/文本报告尾节/--json payload/退出码不变。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="cite_v2_")
        cls.input_path = os.path.join(cls.tmp, "answers.json")
        with open(cls.input_path, "w", encoding="utf-8") as f:
            json.dump(CITE_INPUT, f, ensure_ascii=False, indent=2)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_evidence_constant_five_providers(self):
        providers = cd.CITATION_EVIDENCE["providers"]
        self.assertEqual([p["engine"] for p in providers],
                         ["openai-chat", "openai-responses", "anthropic",
                          "perplexity", "gemini"])
        paths = {p["engine"]: p["payload_path"] for p in providers}
        self.assertEqual(paths["openai-chat"],
                         "choices[0].message.annotations[].url | .url_citation.url")
        self.assertEqual(paths["openai-responses"], "output[i].content[j].annotations[]")
        self.assertEqual(paths["anthropic"], "content[i].citations[].url")
        self.assertEqual(paths["perplexity"], "citations[] + search_results[].url")
        self.assertEqual(paths["gemini"],
                         "candidates[0].groundingMetadata.groundingChunks[].web.uri")
        self.assertEqual(set(cd.CITATION_EVIDENCE["source_classes"]),
                         {"provider_citation", "provider_search_result", "answer_text_url"})

    def test_render_appends_evidence_section(self):
        r = run_script("cite_domain.py", ["--input", self.input_path])
        self.assertEqual(r.returncode, 0)
        self.assertIn("CITE 域名评级", r.stdout)                  # 既有正文不变
        self.assertIn("引用证据核验", r.stdout)
        self.assertIn("provider_citation", r.stdout)
        for engine in ("openai-chat", "openai-responses", "anthropic",
                       "perplexity", "gemini"):
            self.assertIn(engine, r.stdout)

    def test_json_flag_payload(self):
        path = os.path.join(self.tmp, "rating.json")
        r = run_script("cite_domain.py", ["--input", self.input_path, "--json", path])
        self.assertEqual(r.returncode, 0)
        with open(path, encoding="utf-8") as f:
            p = json.load(f)
        self.assertEqual(p["tool"], "cite_domain.py")
        self.assertEqual(p["brand"], "Acme")
        self.assertEqual({i["code"] for i in p["items"]},
                         {"C1", "C2", "C3", "C4", "C5", "C6", "I1", "I2",
                          "T1", "T2", "T3", "T4", "E1", "E2"})
        self.assertAlmostEqual(p["total"], 90.0)
        self.assertTrue(p["band"].startswith("A"))
        self.assertFalse(p["blocked"])
        self.assertEqual(p["citation_evidence"]["providers"],
                         cd.CITATION_EVIDENCE["providers"])

    def test_blocked_still_exit_2_with_json(self):
        d = dict(CITE_INPUT, c_block_concentration=0.30, manual_penalty=True)
        p2 = os.path.join(self.tmp, "blocked.json")
        with open(p2, "w", encoding="utf-8") as f:
            json.dump(d, f)
        out = os.path.join(self.tmp, "blocked.out.json")
        r = run_script("cite_domain.py", ["--input", p2, "--json", out])
        self.assertEqual(r.returncode, 2)                          # 退出码语义不变
        with open(out, encoding="utf-8") as f:
            payload = json.load(f)
        self.assertTrue(payload["blocked"])
        self.assertEqual(len(payload["vetoes"]), 2)


class HelpAndSelfTestTests(unittest.TestCase):
    """--help 正常;两脚本 --self-test 全绿(现有断言保持)。"""

    def test_help_both_scripts(self):
        for name in ("citation_gaps.py", "cite_domain.py"):
            r = run_script(name, ["--help"])
            self.assertEqual(r.returncode, 0, name)

    def test_self_tests_both_scripts(self):
        for name in ("citation_gaps.py", "cite_domain.py"):
            r = run_script(name, ["--self-test"])
            self.assertEqual(r.returncode, 0, name)
            self.assertIn("[self-test] PASS", r.stdout, name)


if __name__ == "__main__":
    unittest.main(verbosity=1)
