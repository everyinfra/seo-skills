#!/usr/bin/env python3
"""prune_gate.py(R3-10)+ content_inventory.py(R6 四轴治理)golden 用例
(stdlib unittest,合成 funnel/crawl/gsc/backlinks/panel,零网络)。

覆盖:三查红线(外链>0/排名词 Position≤20 边界)/三态判定(prune 410·merge 301
同目录最高入链·watch 缺证据)/funnel 模式(截断 exit 2·dropped_urls 截断声明)/
--as-remediation 工单草稿形状;四轴分桶(keep·update·consolidate·remove)/
AI 引用保护(被引页绝不入 remove)/redirect map(remove 兜底目标·410 建议)/
季度节奏/降级声明/CLI 契约(exit 2)。

独立可运行:python3 tests/test_prune_inventory.py(退出码 0=全绿)。
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

HOST = "https://example.com"


def run_script(name, args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


class WorkDir(unittest.TestCase):
    """每用例临时目录 + 合成数据落地助手。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = self._tmp.name
        self.addCleanup(self._tmp.cleanup)

    def write(self, name, content):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def write_json(self, name, obj):
        return self.write(name, json.dumps(obj, ensure_ascii=False))

    # ---- 合成站点:9 页 + edges(入链精确受控) ----
    def crawl(self):
        pages = [
            {"url": HOST + "/", "status": 200, "title": "Example Home", "word_count": 800},
            {"url": HOST + "/pricing", "status": 200, "title": "Pricing Plans", "word_count": 450},
            {"url": HOST + "/blog/hero-guide", "status": 200, "title": "Hero Widgets Guide",
             "word_count": 1200},
            {"url": HOST + "/blog/thin-guide", "status": 200, "title": "Thin Draft Notes",
             "word_count": 150},
            {"url": HOST + "/blog/dupe-a", "status": 200,
             "title": "Widget Guide Detailed Comparison", "word_count": 900},
            {"url": HOST + "/blog/dupe-b", "status": 200,
             "title": "Widget Guide Detailed Comparison", "word_count": 700},
            {"url": HOST + "/blog/zero-value", "status": 200, "title": "Zero Value Old Note",
             "word_count": 100},
            {"url": HOST + "/legal/island", "status": 200, "title": "Legal Island Page",
             "word_count": 600},
            {"url": HOST + "/blog/ai-cited", "status": 200, "title": "AI Cited Reference",
             "word_count": 400},
            {"url": HOST + "/blog/backlinked", "status": 200, "title": "Backlinked No Traffic",
             "word_count": 500},
            {"url": HOST + "/blog/ranked", "status": 200, "title": "Ranked No Clicks",
             "word_count": 500},
            {"url": HOST + "/blog/prune-me", "status": 200, "title": "Prune Me Post",
             "word_count": 300},
            {"url": HOST + "/blog/merge-me", "status": 200, "title": "Merge Me Post",
             "word_count": 300},
            {"url": HOST + "/blog/edge20", "status": 200, "title": "Edge Twenty Post",
             "word_count": 300},
            {"url": HOST + "/blog/edge21", "status": 200, "title": "Edge Twenty One Post",
             "word_count": 300},
            {"url": HOST + "/solo/island", "status": 200, "title": "Solo Island Post",
             "word_count": 300},
        ]
        edges = [
            ("/", "/blog/hero-guide"), ("/blog/dupe-a", "/blog/hero-guide"),
            ("/pricing", "/blog/hero-guide"), ("/blog/dupe-b", "/blog/hero-guide"),
            ("/", "/blog/dupe-a"), ("/blog/hero-guide", "/blog/dupe-a"),
            ("/", "/blog/prune-me"),
            ("/", "/blog/merge-me"), ("/pricing", "/blog/merge-me"),
            ("/blog/dupe-a", "/blog/merge-me"),
            ("/", "/solo/island"), ("/pricing", "/solo/island"),
            ("/blog/hero-guide", "/solo/island"),
            ("/", "/blog/backlinked"), ("/", "/blog/ranked"),
            ("/", "/blog/edge20"), ("/", "/blog/edge21"),
            ("/", "/blog/ai-cited"), ("/", "/blog/thin-guide"),
            ("/", "/blog/zero-value"), ("/", "/legal/island"),
        ]
        return {"schema_version": 1, "domain": "example.com",
                "pages": pages,
                "edges": [{"src": HOST + a, "dst": HOST + b} for a, b in edges],
                "orphans": [], "external_domains": {}}

    def crawl_file(self):
        return self.write_json("crawl.json", self.crawl())

    def gsc_query_file(self):
        """query 级导出(供 prune_gate 排名词红线):候选=零点击且曝光>0 的 7 页。"""
        rows = [
            (HOST + "/", "home brand", 150, 3000, 1.0),
            (HOST + "/pricing", "pricing plans", 35, 800, 2.0),
            (HOST + "/blog/hero-guide", "hero widgets", 90, 1500, 2.1),
            (HOST + "/blog/thin-guide", "thin notes", 8, 300, 4.0),
            (HOST + "/blog/dupe-a", "widget comparison", 15, 700, 3.0),
            (HOST + "/blog/backlinked", "backlinked page query", 0, 110, 35.0),
            (HOST + "/blog/ranked", "ranked page query", 0, 130, 7.2),
            (HOST + "/blog/prune-me", "prune query", 0, 90, 44.0),
            (HOST + "/blog/merge-me", "merge query", 0, 95, 48.0),
            (HOST + "/solo/island", "island query", 0, 70, 55.0),
            (HOST + "/blog/edge20", "edge twenty query", 0, 60, 20.0),
            (HOST + "/blog/edge21", "edge twentyone query", 0, 60, 20.5),
        ]
        lines = ["Page,Query,Clicks,Impressions,CTR,Position"]
        lines += ["%s,%s,%d,%d,0%%,%.1f" % r for r in rows]
        return self.write("gsc_query.csv", "\n".join(lines) + "\n")

    def gsc_page_file(self):
        """page 级导出(无 Query 列:排名词核对不可用)。"""
        rows = [
            (HOST + "/", 150, 3000), (HOST + "/pricing", 35, 800),
            (HOST + "/blog/hero-guide", 90, 1500), (HOST + "/blog/thin-guide", 8, 300),
            (HOST + "/blog/dupe-a", 15, 700),
            (HOST + "/blog/backlinked", 0, 110), (HOST + "/blog/ranked", 0, 130),
            (HOST + "/blog/prune-me", 0, 90), (HOST + "/blog/merge-me", 0, 95),
            (HOST + "/solo/island", 0, 70), (HOST + "/blog/edge20", 0, 60),
            (HOST + "/blog/edge21", 0, 60),
        ]
        lines = ["Page,Clicks,Impressions"]
        lines += ["%s,%d,%d" % r for r in rows]
        return self.write("gsc_page.csv", "\n".join(lines) + "\n")

    def backlinks_file(self):
        """带目标列外链导出:backlinked 页 1 条外链(红线①)。"""
        return self.write("backlinks.csv",
                          "Linking Page,Target\n"
                          "https://ext-a.com/post-1," + HOST + "/blog/backlinked\n"
                          "https://ext-b.org/page-2," + HOST + "/blog/hero-guide\n")

    def urls_file(self):
        urls = [HOST + p for p in (
            "/", "/pricing", "/blog/hero-guide", "/blog/thin-guide", "/blog/dupe-a",
            "/blog/backlinked", "/blog/ranked", "/blog/prune-me", "/blog/merge-me",
            "/solo/island", "/blog/edge20", "/blog/edge21", "/blog/zero-value",
            "/legal/island", "/blog/ai-cited")]
        return self.write("urls.txt", "\n".join(urls) + "\n")

    def panel_file(self):
        """citation_panel panel.json 形态:ai-cited 被引 2 次;not-in-crawl 同域被引;
        other.io 异域被引(不进 crawl 未覆盖清单)。"""
        return self.write_json("panel.json", {
            "brand": "Example", "domain": "example.com", "runs": [
                {"run_id": "chatgpt-1", "engine": "chatgpt", "results": {
                    "best widgets": {"cited": 1, "cited_urls": [
                        HOST + "/blog/ai-cited", "https://other.io/x"]},
                    "reference question": {"cited": 1, "cited_urls": [
                        HOST + "/not-in-crawl", HOST + "/blog/ai-cited"]}}},
                {"run_id": "pplx-1", "engine": "perplexity", "results": {
                    "best widgets": {"cited": 0, "cited_urls": []}}}]})

    def keep_file(self):
        return self.write("keep.txt", HOST + "/pricing\n")

    # ---- 运行助手 ----
    def run_prune(self, *extra, urls=True, funnel=None, gsc="gsc_query.csv",
                  crawl=True, backlinks=True):
        args = []
        if funnel:
            args += ["--funnel", funnel]
        elif urls:
            args += ["--urls", os.path.join(self.dir, "urls.txt")]
        if gsc:
            args += ["--gsc", os.path.join(self.dir, gsc)]
        if crawl:
            args += ["--crawl", os.path.join(self.dir, "crawl.json")]
        if backlinks:
            args += ["--backlinks", os.path.join(self.dir, "backlinks.csv")]
        return run_script("prune_gate.py", args + list(extra))

    def prune_json(self, **kw):
        r = self.run_prune("--json", **kw)
        self.assertIn(r.returncode, (0, 1), r.stderr)   # 0=无待执行 / 1=有 prune/merge
        return json.loads(r.stdout)

    def ci_json(self, **kw):
        args = ["--crawl", os.path.join(self.dir, "crawl.json"),
                "--gsc", os.path.join(self.dir, kw.pop("gsc", "gsc_page.csv"))]
        if kw.pop("panel", True):
            args += ["--panel", os.path.join(self.dir, "panel.json")]
        if kw.pop("backlinks", True):
            args += ["--backlinks", os.path.join(self.dir, "backlinks.csv")]
        if "keep" in kw:
            args += ["--keep", self.write("keep.txt", kw.pop("keep"))]
        for rx in kw.pop("keep_regex", []):
            args += ["--keep-regex", rx]
        if "words" in kw:
            args += ["--words", self.write("words.csv", kw.pop("words"))]
        if "word_floor" in kw:
            args += ["--word-floor", str(kw.pop("word_floor"))]
        self.assertFalse(kw, "未知 kw: %s" % kw)
        r = run_script("content_inventory.py", args + ["--json"])
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout)


# ===========================================================================
# prune_gate.py
# ===========================================================================

class PruneGateTests(WorkDir):

    def setUp(self):
        super().setUp()
        self.crawl_file()
        self.gsc_query_file()
        self.gsc_page_file()
        self.backlinks_file()
        self.urls_file()

    def test_help_contract(self):
        r = run_script("prune_gate.py", ["--help"])
        self.assertEqual(r.returncode, 0)
        for token in ("NO-GO", "prune", "merge", "watch", "入链", "外链", "排名词"):
            self.assertIn(token, r.stdout)

    def test_redline_backlinks_nogo(self):
        """红线①:外链>0(引荐页列出)→ NO-GO。"""
        rep = self.prune_json()
        page = next(p for p in rep["pages"] if p["url"].endswith("/blog/backlinked"))
        self.assertEqual(page["decision"], "nogo")
        self.assertEqual(page["backlinks"], 1)
        self.assertTrue(any("外链 1>0" in x for x in page["reasons"]), page["reasons"])

    def test_redline_ranking_words_nogo(self):
        """红线③:Position≤20 的 query 存在 → NO-GO,原因列词。"""
        rep = self.prune_json()
        page = next(p for p in rep["pages"] if p["url"].endswith("/blog/ranked"))
        self.assertEqual(page["decision"], "nogo")
        self.assertIn("ranked page query", page["ranking_words"])
        self.assertTrue(any("排名词 1 个" in x for x in page["reasons"]), page["reasons"])

    def test_ranking_position_boundary(self):
        """Position=20 计入排名词(NO-GO);20.5 不计(走 prune)。"""
        rep = self.prune_json()
        p20 = next(p for p in rep["pages"] if p["url"].endswith("/blog/edge20"))
        p21 = next(p for p in rep["pages"] if p["url"].endswith("/blog/edge21"))
        self.assertEqual(p20["decision"], "nogo")
        self.assertIn("edge twenty query", p20["ranking_words"])
        self.assertEqual(p21["decision"], "prune")
        self.assertEqual(p21["ranking_words"], [])

    def test_prune_decision_410(self):
        """零点击+零外链+无排名词+入链≤2 → prune(410)。"""
        rep = self.prune_json()
        page = next(p for p in rep["pages"] if p["url"].endswith("/blog/prune-me"))
        self.assertEqual(page["decision"], "prune")
        self.assertEqual(page["inlinks"], 1)
        self.assertIn("410", page["action"])

    def test_merge_decision_same_dir_target(self):
        """入链>2 → merge,301 目标=同目录最高入链页(hero-guide,入链 4)。"""
        rep = self.prune_json()
        page = next(p for p in rep["pages"] if p["url"].endswith("/blog/merge-me"))
        self.assertEqual(page["decision"], "merge")
        self.assertEqual(page["inlinks"], 3)
        self.assertEqual(page["merge_target"], HOST + "/blog/hero-guide")
        self.assertEqual(rep["redirect_map"][page["url"]], HOST + "/blog/hero-guide")

    def test_watch_no_same_dir_target(self):
        """入链>2 但同目录无其他页 → watch(无 301 目标)。"""
        rep = self.prune_json()
        page = next(p for p in rep["pages"] if p["url"].endswith("/solo/island"))
        self.assertEqual(page["decision"], "watch")
        self.assertIsNone(page["merge_target"])
        self.assertTrue(any("同目录无其他页" in x for x in page["reasons"]))

    def test_missing_backlinks_all_watch(self):
        """红线证据缺一 → 无正证据的候选全保守 watch(--backlinks 缺省;
        排名词正证据仍可独立触发 NO-GO)。"""
        rep = self.prune_json(backlinks=False)
        self.assertEqual(rep["decisions"]["prune"], 0)
        self.assertEqual(rep["decisions"]["merge"], 0)
        self.assertEqual(rep["decisions"]["nogo"], 2)    # ranked/edge20(排名词正证据)
        self.assertEqual(rep["decisions"]["watch"], rep["candidates"] - 2)
        page = next(p for p in rep["pages"] if p["url"].endswith("/blog/prune-me"))
        self.assertEqual(page["decision"], "watch")
        self.assertTrue(any("外链核对不可用" in x for x in page["reasons"]))
        self.assertTrue(any("--backlinks 未提供" in n for n in rep["notes"]))

    def test_page_level_gsc_ranking_unknown(self):
        """page 级 GSC(无 Query 列):排名词不可查 → 除正证据 NO-GO 外全 watch。"""
        rep = self.prune_json(gsc="gsc_page.csv")
        self.assertEqual(rep["decisions"]["nogo"], 1)    # backlinked(外链>0)
        self.assertEqual(rep["decisions"]["watch"], rep["candidates"] - 1)
        page = next(p for p in rep["pages"] if p["url"].endswith("/blog/ranked"))
        self.assertEqual(page["decision"], "watch")
        self.assertTrue(any("排名词核对不可用" in x for x in page["reasons"]))

    def test_funnel_mode_decisions(self):
        """--funnel:候选=with_clicks 阶段 dropped_urls,三查照常。"""
        funnel = self.write_json("funnel.json", {
            "schema_version": 1, "tool": "traffic_funnel", "entered": 5, "through": 3,
            "funnel_truncated_at": None,
            "stages": [
                {"stage": "availability", "pages_in": 5, "pages_through": 5,
                 "dropped": 0, "dropped_urls": []},
                {"stage": "indexability", "pages_in": 5, "pages_through": 5,
                 "dropped": 0, "dropped_urls": []},
                {"stage": "uniqueness", "pages_in": 5, "pages_through": 5,
                 "dropped": 0, "dropped_urls": []},
                {"stage": "in_serps", "pages_in": 5, "pages_through": 4, "dropped": 1,
                 "dropped_urls": [{"url": HOST + "/noimpr", "reason": "GSC impressions=0"}]},
                {"stage": "with_clicks", "pages_in": 4, "pages_through": 2,
                 "dropped": 2, "dropped_total": 2, "dropped_urls": [
                     {"url": HOST + "/blog/prune-me", "reason": "GSC clicks=0"},
                     {"url": HOST + "/blog/merge-me", "reason": "GSC clicks=0"}]},
                {"stage": "good_ux", "pages_in": 2, "pages_through": 2,
                 "dropped": 0, "dropped_urls": []}]})
        rep = self.prune_json(funnel=funnel)
        self.assertEqual(rep["mode"], "funnel")
        self.assertEqual(rep["candidates"], 2)
        self.assertEqual(rep["decisions"], {"nogo": 0, "prune": 1, "merge": 1, "watch": 0})

    def test_funnel_truncated_exits_2(self):
        """漏斗截断(上游无 GSC)→ exit 2,不给候选。"""
        funnel = self.write_json("funnel_truncated.json", {
            "schema_version": 1, "tool": "traffic_funnel",
            "funnel_truncated_at": "uniqueness", "stages": []})
        r = self.run_prune(funnel=funnel)
        self.assertEqual(r.returncode, 2)
        self.assertIn("截断", r.stderr)

    def test_funnel_dropped_cap_note(self):
        """dropped_total>len(dropped_urls) → 上游前 20 截断声明。"""
        funnel = self.write_json("funnel_capped.json", {
            "schema_version": 1, "tool": "traffic_funnel",
            "funnel_truncated_at": None,
            "stages": [{"stage": "with_clicks", "pages_in": 30, "pages_through": 5,
                        "dropped": 25, "dropped_total": 25,
                        "dropped_urls": [{"url": HOST + "/blog/prune-me",
                                          "reason": "GSC clicks=0"}]}]})
        rep = self.prune_json(funnel=funnel)
        self.assertTrue(any("截断前 20" in n and "--urls+--gsc" in n for n in rep["notes"]),
                        rep["notes"])

    def test_window_note_and_exit_codes(self):
        """≥90 天窗口口径注明;有待执行决策 exit 1,全 NO-GO/watch exit 0。"""
        r = self.run_prune()
        self.assertEqual(r.returncode, 1)
        self.assertIn("≥90 天", r.stdout)
        only_nogo = self.write("urls_nogo.txt",
                               HOST + "/blog/backlinked\n" + HOST + "/blog/ranked\n")
        r2 = run_script("prune_gate.py", [
            "--urls", only_nogo, "--gsc", os.path.join(self.dir, "gsc_query.csv"),
            "--crawl", os.path.join(self.dir, "crawl.json"),
            "--backlinks", os.path.join(self.dir, "backlinks.csv")])
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    def test_json_schema_counts(self):
        rep = self.prune_json()
        self.assertEqual(rep["schema_version"], 1)
        self.assertEqual(rep["tool"], "prune_gate")
        self.assertEqual(sum(rep["decisions"].values()), rep["candidates"])
        self.assertEqual(len(rep["pages"]), rep["candidates"])
        # 预期全集:backlinked/ranked/edge20=NO-GO,prune-me/edge21=prune,
        # merge-me=merge,island=watch
        self.assertEqual(rep["decisions"], {"nogo": 3, "prune": 2, "merge": 1, "watch": 1})

    def test_as_remediation_shape(self):
        """工单草稿:remediation item 字段齐全,prune/merge 归并,redirect_map 边车。"""
        out = os.path.join(self.dir, "tickets.json")
        self.run_prune("--as-remediation", out)
        with open(out, encoding="utf-8") as f:
            draft = json.load(f)
        self.assertEqual(draft["schema_version"], 1)
        self.assertEqual(draft["tool"], "prune_gate")
        self.assertEqual(len(draft["items"]), 2)         # prune + merge(无 watch/nogo 单)
        for it in draft["items"]:
            for field in ("rule_id", "area", "action", "phase", "severity",
                          "affected_urls", "status", "created", "deadline",
                          "closed", "verify_hint", "note"):
                self.assertIn(field, it, it)
            self.assertEqual(it["status"], "proposed")
            self.assertEqual(it["area"], "content")
            self.assertIsNone(it["closed"])
            self.assertNotIn("id", it)                   # id 由并入时 next_id 顺延
        by_rule = {it["rule_id"]: it for it in draft["items"]}
        self.assertEqual(sorted(by_rule["prune-gate/prune"]["affected_urls"]),
                         [HOST + "/blog/edge21", HOST + "/blog/prune-me"])
        self.assertEqual(by_rule["prune-gate/merge"]["affected_urls"],
                         [HOST + "/blog/merge-me"])
        self.assertEqual(draft["redirect_map"],
                         {HOST + "/blog/merge-me": HOST + "/blog/hero-guide"})

    def test_usage_errors(self):
        """缺候选源/两源互斥/未知参数 → exit 2(套件契约)。"""
        self.assertEqual(run_script("prune_gate.py", ["--crawl", "x"]).returncode, 2)
        self.assertEqual(self.run_prune(
            urls=None, funnel=os.path.join(self.dir, "funnel.json")).returncode, 2)
        self.assertEqual(run_script("prune_gate.py", ["--bogus"]).returncode, 2)


# ===========================================================================
# content_inventory.py
# ===========================================================================

class ContentInventoryTests(WorkDir):

    def setUp(self):
        super().setUp()
        self.crawl_file()
        self.gsc_page_file()
        self.backlinks_file()
        self.panel_file()

    def test_help_contract(self):
        r = run_script("content_inventory.py", ["--help"])
        self.assertEqual(r.returncode, 0)
        for token in ("keep", "update", "consolidate", "remove", "四轴", "AI 引用"):
            self.assertIn(token, r.stdout)

    def test_all_zero_page_remove_candidate(self):
        """四轴全零 → remove 候选。"""
        rep = self.ci_json()
        self.assertIn(HOST + "/blog/zero-value", rep["buckets"]["remove"])
        page = next(p for p in rep["pages"] if p["url"].endswith("/blog/zero-value"))
        self.assertEqual(page["axes"], {"traffic_clicks": 0, "backlinks": 0,
                                        "ai_citations": 0, "strategic": False})

    def test_one_axis_strong_keep(self):
        """一轴强 → keep:流量轴(hero-guide)/外链轴(backlinked)/战略轴(--keep-regex)。"""
        rep = self.ci_json(keep_regex=["/pricing"])
        for url in (HOST + "/blog/hero-guide",          # 流量 90
                    HOST + "/blog/backlinked",           # 外链 1,流量 0
                    HOST + "/pricing"):                  # 战略(正则)+流量
            self.assertIn(url, rep["buckets"]["keep"], url)
        page = next(p for p in rep["pages"] if p["url"].endswith("/blog/backlinked"))
        self.assertEqual(page["axes"]["backlinks"], 1)
        pricing = next(p for p in rep["pages"] if p["url"].endswith("/pricing"))
        self.assertTrue(pricing["axes"]["strategic"])

    def test_keep_list_file_strategic(self):
        """--keep 清单(人工指定)同样点亮战略轴。"""
        rep = self.ci_json(keep=HOST + "/legal/island\n")
        self.assertIn(HOST + "/legal/island", rep["buckets"]["keep"])
        island = next(p for p in rep["pages"] if p["url"].endswith("/legal/island"))
        self.assertTrue(island["axes"]["strategic"])

    def test_ai_citation_protection(self):
        """AI 引用保护:被引 2 次且其余轴全零的页 → keep,绝不入 remove;
        remove 桶被引命中恒 0。"""
        rep = self.ci_json()
        cited = next(p for p in rep["pages"] if p["url"].endswith("/blog/ai-cited"))
        self.assertEqual(cited["axes"]["ai_citations"], 2)
        self.assertEqual(cited["bucket"], "keep")
        self.assertNotIn(cited["url"], rep["buckets"]["remove"])
        guard = rep["ai_citation_guard"]
        self.assertEqual(guard["cited_pages"] >= 1, True)
        self.assertEqual(guard["remove_bucket_hits"], 0)
        r = run_script("content_inventory.py", [
            "--crawl", os.path.join(self.dir, "crawl.json"),
            "--gsc", os.path.join(self.dir, "gsc_page.csv"),
            "--panel", os.path.join(self.dir, "panel.json"),
            "--backlinks", os.path.join(self.dir, "backlinks.csv")])
        self.assertIn("被引页绝不入 remove 桶", r.stdout)

    def test_stale_update_bucket(self):
        """有流量轴但词数 150<地板 300 → update。"""
        rep = self.ci_json()
        self.assertIn(HOST + "/blog/thin-guide", rep["buckets"]["update"])
        page = next(p for p in rep["pages"] if p["url"].endswith("/blog/thin-guide"))
        self.assertTrue(page["stale"])
        self.assertEqual(page["axes"]["traffic_clicks"], 8)

    def test_consolidate_duplicate_cluster(self):
        """title Simhash 重复组:弱成员 dupe-b → consolidate,301 并入组内
        价值最高页 dupe-a(流量 15 vs 0)。"""
        rep = self.ci_json()
        self.assertIn(HOST + "/blog/dupe-b", rep["buckets"]["consolidate"])
        self.assertIn(HOST + "/blog/dupe-a", rep["buckets"]["keep"])
        self.assertEqual(rep["redirect_map"][HOST + "/blog/dupe-b"],
                         HOST + "/blog/dupe-a")
        self.assertEqual(len(rep["clusters"]), 1)

    def test_all_zero_cluster_full_remove(self):
        """重复组内全零 → 整组 remove(不 redirect 到同样要删的 winner)。"""
        crawl = {"schema_version": 1, "domain": "example.com",
                 "pages": [
                     {"url": HOST + "/", "status": 200, "title": "Home", "word_count": 800},
                     {"url": HOST + "/dup/a", "status": 200,
                      "title": "Identical Duplicate Title", "word_count": 500},
                     {"url": HOST + "/dup/b", "status": 200,
                      "title": "Identical Duplicate Title", "word_count": 500}],
                 "edges": [], "orphans": [], "external_domains": {}}
        self.write_json("crawl_dup.json", crawl)
        self.write("gsc_dup.csv", "Page,Clicks,Impressions\n%s,50,900\n" % HOST + "/")
        rep = run_script("content_inventory.py", [
            "--crawl", os.path.join(self.dir, "crawl_dup.json"),
            "--gsc", os.path.join(self.dir, "gsc_dup.csv"), "--json"])
        self.assertEqual(rep.returncode, 0, rep.stderr)
        d = json.loads(rep.stdout)
        self.assertEqual(sorted(d["buckets"]["remove"]),
                         [HOST + "/dup/a", HOST + "/dup/b"])
        self.assertEqual(d["buckets"]["consolidate"], [])
        self.assertEqual(d["buckets"]["keep"], [HOST + "/"])

    def test_redirect_map_and_410_suggestion(self):
        """remove 候选:同目录有强页 → 301 兜底目标;无 → 410 建议。"""
        rep = self.ci_json()
        self.assertEqual(rep["redirect_map"][HOST + "/blog/zero-value"],
                         HOST + "/blog/hero-guide")      # /blog 同目录最强页
        island = next(p for p in rep["pages"] if p["url"].endswith("/legal/island"))
        self.assertEqual(island["bucket"], "remove")
        self.assertIsNone(island["redirect_target"])     # /legal 目录无其他页
        r = run_script("content_inventory.py", [
            "--crawl", os.path.join(self.dir, "crawl.json"),
            "--gsc", os.path.join(self.dir, "gsc_page.csv"),
            "--panel", os.path.join(self.dir, "panel.json"),
            "--backlinks", os.path.join(self.dir, "backlinks.csv")])
        self.assertIn("410 建议", r.stdout)
        self.assertIn(HOST + "/legal/island", r.stdout)

    def test_json_schema_buckets_sum(self):
        rep = self.ci_json()
        self.assertEqual(rep["schema_version"], 1)
        self.assertEqual(rep["tool"], "content_inventory")
        total = sum(len(v) for v in rep["buckets"].values())
        self.assertEqual(total, rep["universe"]["pages"])
        self.assertEqual(len(rep["pages"]), rep["universe"]["pages"])
        self.assertEqual(set(rep["buckets"]), {"keep", "update", "consolidate", "remove"})
        # 决策表与逐页记录一致
        for p in rep["pages"]:
            self.assertIn(p["url"], rep["buckets"][p["bucket"]])

    def test_cadence_and_degradation_notes(self):
        """季度节奏(下次全量清点=下季度首日)与轴缺失降级声明。"""
        rep = self.ci_json(panel=False, backlinks=False)
        import re
        self.assertTrue(re.match(r"^\d{4}-\d{2}-\d{2}$", rep["cadence"]["next_full_audit"]))
        self.assertTrue(any("AI 引用" in s for s in rep["cadence"]["suggestions"]))
        joined = "\n".join(rep["notes"])
        self.assertIn("AI 引用轴不可用", joined)
        self.assertIn("外链轴不可用", joined)
        self.assertIn("战略轴未指定", joined)

    def test_cited_not_in_crawl_listing(self):
        """同域被引但不在 crawl 清单 → guard 清单(补爬,绝不删除);
        异域引用不计入。"""
        rep = self.ci_json()
        not_in_crawl = rep["ai_citation_guard"]["cited_not_in_crawl"]
        self.assertEqual([c["url"] for c in not_in_crawl], [HOST + "/not-in-crawl"])
        self.assertEqual(not_in_crawl[0]["citations"], 1)
        r = run_script("content_inventory.py", [
            "--crawl", os.path.join(self.dir, "crawl.json"),
            "--gsc", os.path.join(self.dir, "gsc_page.csv"),
            "--panel", os.path.join(self.dir, "panel.json")])
        self.assertIn("补爬入册,绝不删除", r.stdout)
        self.assertNotIn("other.io", r.stdout)

    def test_words_csv_and_floor_override(self):
        """--words CSV 补词数;--word-floor 500 把 hero-guide(800)留在 keep、
        把 thin-guide(150)打入 update,把 dupe-a(900→499)打入 update。"""
        words = "\n".join("%s,%d" % (HOST + p, w) for p, w in (
            ("/blog/hero-guide", 800), ("/blog/thin-guide", 150),
            ("/blog/dupe-a", 499), ("/blog/dupe-b", 700),
            ("/", 800), ("/pricing", 450), ("/blog/zero-value", 100),
            ("/legal/island", 600), ("/blog/ai-cited", 400),
            ("/blog/backlinked", 500), ("/blog/ranked", 500),
            ("/blog/prune-me", 300), ("/blog/merge-me", 300),
            ("/blog/edge20", 300), ("/blog/edge21", 300),
            ("/solo/island", 300))) + "\n"
        rep = self.ci_json(words=words, word_floor=500)
        self.assertIn(HOST + "/blog/dupe-a", rep["buckets"]["update"])
        thin = next(p for p in rep["pages"] if p["url"].endswith("/blog/dupe-a"))
        self.assertEqual(thin["word_count"], 499)
        self.assertTrue(thin["stale"])
        # dupe-b(词数 700≥500)仍按重复组 consolidate,不受地板影响
        self.assertIn(HOST + "/blog/dupe-b", rep["buckets"]["consolidate"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
