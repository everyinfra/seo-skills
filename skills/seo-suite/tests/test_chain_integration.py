#!/usr/bin/env python3
"""seo-suite 端到端链路集成测试(全链冒烟,零网络,合成数据)。

覆盖链路(上一步的 stdout/文件 即 下一步的输入,重点断言互操作契约):
  1. site_audit.py --json(问题页:缺 description/多 H1/canonical 指向 noindex 目标/
     语义标签少 + noindex 目标页)——**真实运行** scripts/site_audit.py 的 main(),
     仅把模块级 fetch() 打桩为本地 fixture(无 --html 模式;打桩是任务允许的零网络手段,
     代码路径/解析/评分与联网运行完全一致)。原始 stdout(逐 URL 文本行 + JSON blob)
     原样落盘,后续各环照单全收。
  2. health_score.py --input <raw audit> --json      (容忍前部文本行 → 主分/分档/impacts)
  3. prioritize.py --audit <raw audit> --json        (site_audit 逐页路径 + health_score 摘要路径)
  4. envelope.py --audit --health --priority 三源     (audit-data.json/REPORT.md/findings/*.md)
  5. audit_compare.py --old <修复前> --new <修复后>   (第二份"修复后" fixture 真实重跑生成;
                                                       断言 fixed_issues 里有对应修复项)
  6. ci_format.py sarif/junit/github                 (断言结构;含 audit_compare diff → sarif 归一化路径)
  7. fix_plan.py --audit <audit> --json              (断言 FixItem 六类契约)
  8. citation_panel.py init/record(合成 run.csv) → citation_gaps.py --csv/--json
  9. benchmark_report.py --audits(两份真实审计) + --scores(合成 6 站 CSV)→ 分布报告与偏差自白

零网络保证: site_audit fetch 全部打桩(fixture 域名 chain-fixture.test 为保留 TLD,永不可解析);
其余脚本全部走文件输入/文件输出,无任何联网代码路径。fixture 见 tests/fixtures/chain/。

=============================================================================
发现的断裂清单(真实互操作断裂;脚本禁改 → 以 @unittest.expectedFailure 钉死,
脚本修复后请删掉装饰器并让测试转绿):
=============================================================================
断裂 1  site_audit.py --json 的原始 stdout → fix_plan.py --audit
  现象:  `site_audit.py URL... --json > audit.json && fix_plan.py --audit audit.json`
         退出码 2,"[fix_plan] 审计文件不可读 ... Expecting value"。
  根因:  site_audit --json 的 stdout 在 JSON blob 之前有逐 URL 人读文本行(== url ==/
         [SEV] area/meta: {...}),链上其他**全部**消费者(health_score.load_audit/
         prioritize.load_json_blob/audit_compare.load_audit/envelope.load_blob/
         ci_format.load_payload/benchmark_report._parse_audit_blob)都实现了
         "从每个 '{' 起点试解" 的容错,**唯独 fix_plan.view_from_audit_file 用裸
         json.load**(scripts/fix_plan.py 第 397 行附近),自然流水线到此断裂。
  绕过:  本测试主链路用 extract_audit_blob()(与健康_score 同款 '{' 扫描)提取纯 JSON
         落盘为 *.clean.json 再喂 fix_plan;原始 raw 文件仍喂给其余全部消费者。

断裂 2  citation_panel.py init --prompts-file(对象化 prompt 形态)→ citation_gaps.py
  现象:  面板 prompts 为对象形态(citation_panel v2+ 的正式输出,init --prompts-file
         的 markdown 表格/带表头 CSV 路径产出 {text,stage,...} 字典)时,
         citation_gaps --json 退出码 1,TypeError: unhashable type: 'dict',
         --csv/--json 均未写出。
  根因:  citation_gaps.compute_gap_labels 直接把 panel["prompts"] 元素当字符串用:
         `owned_relevance.get(p)`(dict 不可哈希)当场抛 TypeError;即便绕过,
         后续 rows.sort(key=lambda t: (t[0], t[1]["prompt"])) 在同标签并列时对 dict
         做 '<' 比较同样崩。citation_gaps 只兼容 init --prompts(纯 CSV 字符串形态)。
  绕过:  本测试主链路用字符串形态 prompts.csv;对象形态断裂以 expectedFailure 钉死。

语义注记(非断裂,记录在案):
  - audit_compare.PAGE_FIELDS 的 canonical 页级对比是死代码——site_audit meta 不输出
    canonical 键,两侧皆缺自动跳过;site_audit 补字段后自动生效(脚本内已注释说明)。
  - prioritize 吃 health_score 摘要时,不在 AREA_RULE 映射表的 area(og/schema/bluf/
    rendering 等)按恒等透传(rule==source_rule),修复文案退化为通用占位——可用但
    信息量降级,envelope 侧靠 RULE_TO_AREA/恒等映射接得住。
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SCRIPTS = os.path.join(BASE, "scripts")
FIXTURES = os.path.join(HERE, "fixtures", "chain")
sys.path.insert(0, SCRIPTS)

HOST = "https://chain-fixture.test"                       # 保留 TLD,永不可解析
URL_PROBLEM = HOST + "/problem-page"                      # 问题页(修复前)
URL_NOINDEX = HOST + "/noindex-target"                    # canonical 指向的 noindex 目标页


# ---------------------------------------------------------------- 助手(standalone)
def run_script(name, args=()):
    """子进程跑 scripts/<name>(与 tests/run_tests.py 同款;文件进出,零网络)。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def read_fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


def run_site_audit(pages, extra=None):
    """真实运行 site_audit.main()(真实解析/评分/JSON 契约),仅 fetch 打桩。

    pages: {url: (status, headers, body)} 要**作为 URL 审计**的页面;
    extra: 同型 dict,只作为根文件被抓取(robots.txt/sitemap.xml/llms.txt),不进审计列表。
    未登记的 URL(如 /llms.txt)抛 OSError,与真实 urllib 行为同向(根文件不可达 →
    INFO finding)。返回完整 stdout 原文(逐 URL 文本行 + 末尾 JSON blob,
    即其他消费者约定要容忍的工件形态)。"""
    import site_audit as sa
    responses = dict(pages)
    if extra:
        responses.update(extra)

    def stub(url, timeout=15):
        if url in responses:
            st, hdrs, body = responses[url]
            return st, dict(hdrs), body
        raise OSError("unreachable stub: %s" % url)

    orig_fetch, orig_argv = sa.fetch, sys.argv
    sa.fetch = stub
    buf = io.StringIO()
    sys.argv = ["site_audit.py", *pages.keys(), "--json"]
    rc = 0
    try:
        with contextlib.redirect_stdout(buf):
            sa.main()
    except SystemExit as e:
        rc = e.code or 0
    finally:
        sa.fetch = orig_fetch
        sys.argv = orig_argv
    return buf.getvalue(), rc


def extract_audit_blob(text):
    """health_score.load_audit 同款 '{' 起点扫描:取末位含 results 字典的 JSON 候选。"""
    try:
        data = json.loads(text)
        if isinstance(data.get("results"), dict):
            return data
    except json.JSONDecodeError:
        pass
    data = None
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            cand = json.loads(text[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(cand, dict) and isinstance(cand.get("results"), dict):
            data = cand          # 不 break:末位的完整 blob 赢过早位的 meta 行片段
    if data is None:
        raise AssertionError("无法从文本提取 site_audit JSON blob")
    return data


# ---------------------------------------------------------------- 链路工件(惰性,一次构建全链共享)
_ARTIFACTS = None


def _stage_assert(stage, proc, expect=(0,)):
    if proc.returncode not in expect:
        raise AssertionError("链路阶段 [%s] 失败 rc=%s(期望 %s)\nstderr 头:\n%s"
                             % (stage, proc.returncode, expect, proc.stderr[:3000]))
    return proc


def chain_artifacts():
    """按链路顺序生成全部中间工件;任一环失败时异常信息标注断在哪一环。"""
    global _ARTIFACTS
    if _ARTIFACTS is not None:
        return _ARTIFACTS
    tmp = tempfile.mkdtemp(prefix="seo_chain_")
    art = {"tmp": tmp}
    root_files = {
        HOST + "/robots.txt": (200, {}, read_fixture("robots.txt")),
        HOST + "/sitemap.xml": (200, {}, read_fixture("sitemap.xml")),
    }

    # ---- 环 1:site_audit --json(修复前,真实 main() + fetch 打桩) ----
    raw_before, rc_before = run_site_audit(
        {URL_PROBLEM: (200, {}, read_fixture("problem.html")),
         URL_NOINDEX: (200, {}, read_fixture("noindex-target.html"))},
        extra=root_files)
    art["audit_before_raw"] = os.path.join(tmp, "audit-before.json")
    with open(art["audit_before_raw"], "w", encoding="utf-8") as f:
        f.write(raw_before)
    art["audit_rc_before"] = rc_before
    art["blob_before"] = extract_audit_blob(raw_before)
    art["audit_before_clean"] = os.path.join(tmp, "audit-before.clean.json")
    with open(art["audit_before_clean"], "w", encoding="utf-8") as f:
        f.write(json.dumps(art["blob_before"], ensure_ascii=False, indent=1))

    # ---- 环 1b:修复后审计(第二份 fixture 真实重跑,同一 stub 通道) ----
    raw_after, rc_after = run_site_audit(
        {URL_PROBLEM: (200, {}, read_fixture("problem-fixed.html")),
         URL_NOINDEX: (200, {}, read_fixture("noindex-target-fixed.html"))},
        extra=root_files)
    art["audit_after_raw"] = os.path.join(tmp, "audit-after.json")
    with open(art["audit_after_raw"], "w", encoding="utf-8") as f:
        f.write(raw_after)
    art["audit_rc_after"] = rc_after
    art["blob_after"] = extract_audit_blob(raw_after)

    # ---- 环 2:health_score(吃 raw 文件,验证前部文本行容错契约) ----
    h = _stage_assert("health_score --input", run_script(
        "health_score.py", ["--input", art["audit_before_raw"], "--json"]), expect=(0, 1))
    art["health"] = json.loads(h.stdout)
    art["health_path"] = os.path.join(tmp, "health.json")
    with open(art["health_path"], "w", encoding="utf-8") as f:
        f.write(h.stdout)

    # ---- 环 3:prioritize(逐页路径 + health_score 摘要路径) ----
    p = _stage_assert("prioritize --audit(site_audit)", run_script(
        "prioritize.py", ["--audit", art["audit_before_raw"], "--json"]))
    art["priority"] = json.loads(p.stdout)
    art["priority_path"] = os.path.join(tmp, "priority.json")
    with open(art["priority_path"], "w", encoding="utf-8") as f:
        f.write(p.stdout)
    ph = _stage_assert("prioritize --audit(health_score 摘要)", run_script(
        "prioritize.py", ["--audit", art["health_path"], "--json"]))
    art["priority_from_health"] = json.loads(ph.stdout)

    # ---- 环 4:envelope 三源 ----
    art["envelope_dir"] = os.path.join(tmp, "envelope-out")
    _stage_assert("envelope 三源", run_script(
        "envelope.py", ["--audit", art["audit_before_raw"], "--health", art["health_path"],
                        "--priority", art["priority_path"], "--out-dir", art["envelope_dir"]]))
    with open(os.path.join(art["envelope_dir"], "audit-data.json"), encoding="utf-8") as f:
        art["envelope"] = json.load(f)

    # ---- 环 5:audit_compare(修复前 vs 修复后)+ baseline gate 触发向 ----
    c = _stage_assert("audit_compare --old/--new", run_script(
        "audit_compare.py", ["--old", art["audit_before_raw"], "--new",
                             art["audit_after_raw"], "--json"]))
    art["compare"] = json.loads(c.stdout)
    art["compare_path"] = os.path.join(tmp, "compare.json")
    with open(art["compare_path"], "w", encoding="utf-8") as f:
        f.write(c.stdout)
    # 反向对比(修复后→修复前)= 主分跌 100,gate 必触发(Lumar Protect 语义)
    g = _stage_assert("audit_compare --baseline-gate(触发向)", run_script(
        "audit_compare.py", ["--old", art["audit_after_raw"], "--new",
                             art["audit_before_raw"], "--baseline-gate", "5", "--json"]),
        expect=(1,))
    art["compare_gate"] = json.loads(g.stdout)

    # ---- 环 6:ci_format(sarif/junit/github + diff 归一化路径) ----
    s = _stage_assert("ci_format sarif", run_script(
        "ci_format.py", [art["audit_before_raw"], "--format", "sarif"]))
    art["sarif"] = json.loads(s.stdout)
    j = _stage_assert("ci_format junit", run_script(
        "ci_format.py", [art["audit_before_raw"], "--format", "junit"]))
    art["junit"] = j.stdout
    art["github"] = _stage_assert("ci_format github", run_script(
        "ci_format.py", [art["audit_before_raw"], "--format", "github"])).stdout
    sd = _stage_assert("ci_format sarif(吃 audit_compare diff)", run_script(
        "ci_format.py", [art["compare_path"], "--format", "sarif"]))
    art["sarif_from_diff"] = json.loads(sd.stdout)

    # ---- 环 7:fix_plan(clean JSON;raw 文件喂不进 = 断裂 1,单独以 expectedFailure 钉死) ----
    fpx = _stage_assert("fix_plan --audit", run_script(
        "fix_plan.py", ["--audit", art["audit_before_clean"], "--json"]))
    art["fixplan"] = json.loads(fpx.stdout)

    # ---- 环 8:citation 链(panel init/record 真实跑 → citation_gaps) ----
    art["panel_path"] = os.path.join(tmp, "panel.json")
    _stage_assert("citation_panel init", run_script(
        "citation_panel.py", ["init", "--brand", "Acme", "--domain", "acme-corp.test",
                              "--prompts", os.path.join(FIXTURES, "prompts.csv"),
                              "--engines", "chatgpt,perplexity",
                              "--panel", art["panel_path"]]))
    _stage_assert("citation_panel record(chatgpt)", run_script(
        "citation_panel.py", ["record", "--engine", "chatgpt", "--file",
                              os.path.join(FIXTURES, "run-chatgpt.csv"),
                              "--panel", art["panel_path"]]))
    _stage_assert("citation_panel record(perplexity)", run_script(
        "citation_panel.py", ["record", "--engine", "perplexity", "--file",
                              os.path.join(FIXTURES, "run-perplexity.csv"),
                              "--panel", art["panel_path"]]))
    art["gaps_json_path"] = os.path.join(tmp, "gaps.json")
    art["gaps_csv_path"] = os.path.join(tmp, "gaps.csv")
    gp = _stage_assert("citation_gaps --panel", run_script(
        "citation_gaps.py", ["--panel", art["panel_path"], "--brand-domains", "acme-corp.test",
                             "--csv", art["gaps_csv_path"], "--json", art["gaps_json_path"]]))
    art["gaps_report"] = gp.stdout
    with open(art["gaps_json_path"], encoding="utf-8") as f:
        art["gaps"] = json.load(f)

    # ---- 环 9:benchmark_report(两份真实审计 + 合成 4 站 CSV = 6 站) ----
    audits_dir = os.path.join(tmp, "audits")
    os.makedirs(audits_dir, exist_ok=True)
    for src, dst in ((art["audit_before_raw"], "site-a.json"),
                     (art["audit_after_raw"], "site-b.json")):
        with open(src, encoding="utf-8") as f_in, \
                open(os.path.join(audits_dir, dst), "w", encoding="utf-8") as f_out:
            f_out.write(f_in.read())
    art["audits_dir"] = audits_dir
    scores4 = os.path.join(FIXTURES, "scores-4.csv")
    bj = _stage_assert("benchmark_report --json", run_script(
        "benchmark_report.py", ["--audits", audits_dir, "--scores", scores4, "--json"]))
    art["bench"] = json.loads(bj.stdout)
    art["bench_md"] = _stage_assert("benchmark_report markdown", run_script(
        "benchmark_report.py", ["--audits", audits_dir, "--scores", scores4])).stdout
    art["bench_gate"] = run_script("benchmark_report.py",
                                   ["--scores", os.path.join(FIXTURES, "scores-3.csv")])

    _ARTIFACTS = art
    return art


# ---------------------------------------------------------------- 环 1:site_audit 契约
class TestStage1SiteAuditContract(unittest.TestCase):
    """真实 site_audit.main() + fetch 打桩:--json 原始工件形态与逐页 schema 契约
    (下游 health_score/prioritize/audit_compare/envelope/fix_plan 全靠这些字段名)。"""

    @classmethod
    def setUpClass(cls):
        cls.art = chain_artifacts()

    def test_raw_stdout_shape_and_exit_code(self):
        """原始 stdout = 逐 URL 文本行 + 末尾 JSON blob;有 CRITICAL → 退出码 1。"""
        with open(self.art["audit_before_raw"], encoding="utf-8") as f:
            raw = f.read()
        self.assertEqual(self.art["audit_rc_before"], 1)
        self.assertIn("== %s ==" % URL_PROBLEM, raw)          # 逐 URL 文本行(容错契约的来源)
        self.assertIn("[CRITICAL] description: 缺失", raw)
        blob = self.art["blob_before"]
        self.assertEqual(blob["schema_version"], 1)
        self.assertEqual(blob["audited"], 2)
        self.assertGreaterEqual(blob["critical"], 2)
        self.assertIsInstance(blob["results"], dict)

    def test_problem_page_schema_contract(self):
        """问题页:verdict/findings{severity,area,message}/meta{title,words,h1,jsonld}/
        ai_search_health{score,checks} —— 下一步逐字段的互操作契约。"""
        r = self.art["blob_before"]["results"][URL_PROBLEM]
        self.assertEqual(r["verdict"], "fail")
        finds = {(f["severity"], f["area"]) for f in r["findings"]}
        self.assertIn(("CRITICAL", "description"), finds)     # 缺 description
        self.assertIn(("WARN", "h1"), finds)                  # 多 H1
        self.assertEqual(r["meta"]["h1"], 2)
        self.assertLess(r["meta"]["words"], 200)              # soft-thin
        for key in ("title", "words", "h1", "jsonld"):        # prioritize/audit_compare 依赖的 meta 键
            self.assertIn(key, r["meta"])
        ai = r["ai_search_health"]
        self.assertIsInstance(ai["score"], int)
        self.assertEqual({c["id"] for c in ai["checks"]} >=        # fix_plan estimate 依赖 checks
                         {"bots", "llms_txt", "freshness", "semantic_html", "content_length", "bluf"},
                         True)

    def test_noindex_target_page(self):
        """canonical 目标页:noindex CRITICAL + a11y WARN(无 lang),其余干净。"""
        r = self.art["blob_before"]["results"][URL_NOINDEX]
        self.assertEqual(r["verdict"], "fail")
        robots = [f for f in r["findings"] if f["area"] == "robots"]
        self.assertEqual(len(robots), 1)
        self.assertEqual(robots[0]["severity"], "CRITICAL")
        self.assertIn("noindex", robots[0]["message"])
        self.assertIn(("WARN", "a11y"),
                      {(f["severity"], f["area"]) for f in r["findings"]})
        self.assertGreaterEqual(r["meta"]["words"], 200)      # 非 thin → 不产 content 噪音

    def test_after_audit_is_clean(self):
        """修复后重跑:0 critical、双 pass、meta 字段可被 audit_compare 页级对比吃。"""
        blob = self.art["blob_after"]
        self.assertEqual(self.art["audit_rc_after"], 0)
        self.assertEqual(blob["critical"], 0)
        for url in (URL_PROBLEM, URL_NOINDEX):
            self.assertEqual(blob["results"][url]["verdict"], "pass")
            self.assertIn("words", blob["results"][url]["meta"])
            self.assertIn("h1", blob["results"][url]["meta"])


# ---------------------------------------------------------------- 环 2:health_score
class TestStage2HealthScoreEatsAudit(unittest.TestCase):
    """health_score --input 直吃 site_audit 原始 stdout 文件(前部文本行容错契约)。"""

    @classmethod
    def setUpClass(cls):
        cls.art = chain_artifacts()

    def test_scores_and_exit_code(self):
        """2 URL 全有 CRITICAL → 主分 0.0/Weak → 退出码 1(Weak 档约定)。"""
        h = self.art["health"]
        self.assertEqual(self.art["audit_rc_before"], 1)
        self.assertEqual(h["main_score"], 0.0)
        self.assertEqual(h["band"], "Weak")
        self.assertEqual(h["urls_total"], 2)
        self.assertEqual(h["urls_clean"], 0)
        self.assertEqual(h["urls_refused"], 0)
        self.assertIn("coverage_note", h)

    def test_impact_and_categories(self):
        """impacts(Ryte 口径)按规则输出且可被 prioritize 摘要路径吃(rule/severity/hit_urls)。"""
        h = self.art["health"]
        top = h["impacts"][0]
        self.assertEqual(top["rule"], "description")          # 1/2 命中 × CRITICAL²=4.5,并列按名序
        self.assertEqual(top["impact"], 4.5)
        for d in h["impacts"]:
            for key in ("rule", "severity", "hit_urls", "total_urls", "impact"):
                self.assertIn(key, d)
        self.assertEqual(h["unmapped"], [])                    # site_audit 全部 area 均已映射
        self.assertLess(h["category_scores"]["rankability"]["score"], 100)


# ---------------------------------------------------------------- 环 3:prioritize
class TestStage3Prioritize(unittest.TestCase):
    """prioritize 两种输入:site_audit 逐页(完整引擎)与 health_score 摘要(降级声明)。"""

    @classmethod
    def setUpClass(cls):
        cls.art = chain_artifacts()

    def test_site_audit_input_full_engine(self):
        p = self.art["priority"]
        self.assertEqual(p["input_format"], "site_audit")
        by_rule = {d["rule"]: d for d in p["fix_now"]}
        self.assertIn("desc_missing", by_rule)                # 吃到 findings.area=description
        self.assertEqual(by_rule["desc_missing"]["url_query"], [URL_PROBLEM])
        noindex = by_rule["noindex_intent"]                   # noindex → 条件依赖型(intent_hint)
        self.assertEqual(noindex["url_query"], [URL_NOINDEX])
        self.assertTrue(noindex["conditional"]["needs_human"])
        self.assertIn("thin_content", by_rule)                # 吃到 meta.words
        degraded = {d["rule"] for d in p["degraded_rules"]}
        self.assertIn("depth_deep", degraded)                 # site_audit 无 depth 字段 → 降级声明

    def test_health_score_summary_input(self):
        """health_score --json 摘要也能吃:优先识别 + 降级声明 + AREA_RULE 映射。"""
        p = self.art["priority_from_health"]
        self.assertEqual(p["input_format"], "health_score")
        self.assertTrue(p["degradation_notes"])               # 无逐页字段 → 必须声明降级
        by_rule = {d["rule"]: d for d in p["fix_now"]}
        self.assertIn("desc_missing", by_rule)                # health area description → 内置规则
        self.assertEqual(by_rule["desc_missing"]["source_rule"], "description")
        self.assertEqual(by_rule["desc_missing"]["impact"], 1.5)


# ---------------------------------------------------------------- 环 4:envelope
class TestStage4EnvelopeThreeSources(unittest.TestCase):
    """envelope 三源合一:health 的分、prioritize 的 impact/修复文案、audit 的发现。"""

    @classmethod
    def setUpClass(cls):
        cls.art = chain_artifacts()

    def test_envelope_files_written(self):
        for rel in ("audit-data.json", "REPORT.md"):
            self.assertTrue(os.path.isfile(os.path.join(self.art["envelope_dir"], rel)), rel)
        fdir = os.path.join(self.art["envelope_dir"], "findings")
        mds = [n for n in os.listdir(fdir) if n.endswith(".md")]
        self.assertTrue(mds)
        for n in mds:                                         # 机器回读标记(--resume 依赖)
            with open(os.path.join(fdir, n), encoding="utf-8") as f:
                self.assertIn("envelope-category-v1", f.read(), n)

    def test_three_source_propagation(self):
        env = self.art["envelope"]
        self.assertEqual(env["inputs"], {"audit": "ok", "health": "ok", "priority": "ok"})
        self.assertEqual(env["summary"]["main_score"], self.art["health"]["main_score"])  # health 透传
        self.assertEqual(env["summary"]["band"], self.art["health"]["band"])
        self.assertEqual(env["summary"]["ai_search_health"], 77.5)   # (70+85)/2,site_audit 均值
        cats = {c["name"]: [f["rule_id"] for f in c["findings"]] for c in env["categories"]}
        self.assertEqual(set(cats), {"indexability", "discoverability", "rankability"})
        self.assertIn("robots", cats["indexability"])         # noindex → Lumar indexability
        self.assertIn("description", cats["rankability"])
        # 修复文案来自 prioritize(desc_missing.fix,经 RULE_TO_AREA 桥接)——三源互操作核心断言
        desc = [f for c in env["categories"] for f in c["findings"]
                if f["rule_id"] == "description"][0]
        self.assertEqual(desc["recommendation"], "补 meta description(~155 字符)")
        # 行动计划分派:CRITICAL → 立即(本周)
        phase0 = env["action_plan"]["phases"][0]
        self.assertEqual(phase0["name"], "立即(本周)")
        self.assertIn("description", {i["rule_id"] for i in phase0["items"]})
        self.assertLessEqual(len(env["summary"]["quick_wins"]), 3)
        self.assertIn("description", {q["rule_id"] for q in env["summary"]["quick_wins"]})


# ---------------------------------------------------------------- 环 5:audit_compare
class TestStage5AuditCompare(unittest.TestCase):
    """修复前 vs 修复后:fixed_issues 对应项、无新增、verdict/分数/页级变化、baseline gate。"""

    @classmethod
    def setUpClass(cls):
        cls.art = chain_artifacts()

    def test_fixed_and_no_new_issues(self):
        rep = self.art["compare"]
        fixed = {(f["url"], f["rule"]) for f in rep["fixed_issues"]}
        expected = {
            (URL_PROBLEM, "description"),      # 补了 meta description
            (URL_PROBLEM, "h1"),               # 2 H1 → 1
            (URL_PROBLEM, "og"),               # 补 og 三件套
            (URL_PROBLEM, "schema"),           # 补 JSON-LD
            (URL_PROBLEM, "content"),          # 42 词 → 297 词
            (URL_PROBLEM, "a11y"),             # 补 lang
            (URL_PROBLEM, "semantic-html"),    # 语义标签比值 8.7% → 47%
            (URL_NOINDEX, "robots"),           # 去掉 noindex
            (URL_NOINDEX, "a11y"),             # 补 lang
        }
        for pair in expected:
            self.assertIn(pair, fixed, "修复后清单缺少: %s" % (pair,))
        self.assertEqual(rep["new_issues"], [])                # 修复不得引入新问题
        self.assertEqual(rep["delta"]["main_score"], 100.0)    # 0.0 → 100.0
        self.assertEqual(rep["delta"]["ai_search_health_mean"], 7.5)
        self.assertEqual(rep["delta"]["coverage_ratio"], 1.0)

    def test_verdict_page_and_ai_changes(self):
        rep = self.art["compare"]
        vc = {v["url"]: (v["old"], v["new"]) for v in rep["verdict_changes"]}
        self.assertEqual(vc, {URL_PROBLEM: ("fail", "pass"), URL_NOINDEX: ("fail", "pass")})
        ai = {a["url"]: a for a in rep["ai_health_changes"]}
        self.assertEqual(ai[URL_PROBLEM]["delta"], 15)         # semantic_html 修复 +15
        pc = {p["url"]: {c["field"] for c in p["changes"]} for p in rep["pages_changed"]}
        self.assertTrue({"word_count", "h1"} <= pc[URL_PROBLEM])  # meta.words/meta.h1 被吃

    def test_baseline_gate_trips_on_regression(self):
        """反向对比(跌 100 分)> 阈值 5 → tripped + 退出码 1(Lumar Protect 语义)。"""
        gate = self.art["compare_gate"]["baseline_gate"]
        self.assertTrue(gate["tripped"])
        self.assertEqual(gate["drop"], 100.0)


# ---------------------------------------------------------------- 环 6:ci_format
class TestStage6CiFormat(unittest.TestCase):
    """site_audit JSON / audit_compare diff → sarif 2.1.0 / junit XML / github 注解结构。"""

    @classmethod
    def setUpClass(cls):
        cls.art = chain_artifacts()

    def test_sarif_structure(self):
        s = self.art["sarif"]
        self.assertEqual(s["version"], "2.1.0")
        run = s["runs"][0]
        self.assertTrue(run["tool"]["driver"]["rules"])        # rules 与 results 对齐登记
        self.assertEqual(len(run["results"]), 17)              # 13(问题页)+4(noindex 页)条非 SKIP finding
        self.assertEqual({r["level"] for r in run["results"]},
                         {"error", "warning", "note"})         # CRITICAL/WARN/INFO 三档映射
        for r in run["results"]:
            uri = r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            self.assertTrue(uri.startswith(HOST))              # uri=被审计 URL
        self.assertIn("description", {r["ruleId"] for r in run["results"]})
        props = run["invocations"][0]["properties"]
        self.assertEqual(props["main_score"], 0.0)
        self.assertEqual(props["ai_search_health"], 77.5)

    def test_junit_structure(self):
        root = ET.fromstring(self.art["junit"])                # 必须是良构 XML
        self.assertEqual(root.tag, "testsuites")
        suites = root.findall("testsuite")                     # 每个 area 一个 testsuite
        self.assertEqual(int(root.attrib["tests"]), len(suites))
        nfail = sum(len(ts.findall("testcase/failure")) for ts in suites)
        self.assertEqual(int(root.attrib["failures"]), nfail)
        failing = {ts.attrib["name"] for ts in suites if ts.findall("testcase/failure")}
        self.assertIn("a11y", failing)                         # a11y 命中 2/2 URL → 类目得分 0<50
        props = {p.attrib["name"]: p.attrib["value"]
                 for p in root.findall("properties/property")}
        self.assertEqual(props["audit.score"], "0.0")
        self.assertEqual(props["ai_search_health"], "77.5")

    def test_github_annotations(self):
        lines = self.art["github"].splitlines()
        self.assertTrue(lines[0].startswith("::notice title=SEO::"))
        self.assertIn("::error title=SEO::[description]", self.art["github"])

    def test_sarif_eats_audit_compare_diff(self):
        """audit_compare --json 的 diff 输出(new_issues)→ ci_format 归一化路径。"""
        s = self.art["sarif_from_diff"]
        self.assertEqual(s["version"], "2.1.0")
        self.assertEqual(s["runs"][0]["results"], [])          # 修复方向对比:new_issues 为空
        self.assertIsNone(s["runs"][0]["invocations"][0]["properties"]["main_score"])


# ---------------------------------------------------------------- 环 7:fix_plan
class TestStage7FixPlan(unittest.TestCase):
    """fix_plan --audit(clean JSON)→ FixItem 六类契约 + 收益预估。"""

    @classmethod
    def setUpClass(cls):
        cls.art = chain_artifacts()

    def test_fix_items_contract(self):
        fp = self.art["fixplan"]
        self.assertEqual(fp["verdict"], "fail")
        fixes = fp["fixes"]
        self.assertEqual({f["category"] for f in fixes},
                         {"llms", "schema", "meta", "content"})   # robots 放行无失败 → 不产
        for fx in fixes:
            self.assertEqual(set(fx), {"category", "description", "content",
                                       "file_name", "action"})     # FixItem 固定五字段
            self.assertIn(fx["action"], ("create", "append", "snippet"))
            self.assertEqual(os.path.basename(fx["file_name"]), fx["file_name"])  # 裸文件名
        meta = [f for f in fixes if f["category"] == "meta"][0]
        self.assertIn("description", meta["description"])
        self.assertIn('meta name="description"', meta["content"])  # 审计"缺失"→ 补全片段
        self.assertIn("og:title", meta["description"])

    def test_estimate_uses_ai_search_health(self):
        """收益预估吃 ai_search_health.checks(llms/semantic 修复 +15+15)。"""
        est = self.art["fixplan"]["estimate"]
        a_ai = self.art["blob_before"]["results"][URL_PROBLEM]["ai_search_health"]["score"]
        self.assertEqual(est["before"], a_ai)
        self.assertEqual(est["gain"], 30)
        self.assertEqual(set(est["breakdown"]), {"llms:+15", "schema:+15"})
        self.assertEqual(est["after"], 100)


# ---------------------------------------------------------------- 环 8:citation 链
class TestCitationChain(unittest.TestCase):
    """citation_panel init/record(合成 run.csv)→ citation_gaps 报告/CSV/JSON。"""

    @classmethod
    def setUpClass(cls):
        cls.art = chain_artifacts()

    def test_panel_recorded_two_runs(self):
        with open(self.art["panel_path"], encoding="utf-8") as f:
            panel = json.load(f)
        self.assertEqual(len(panel["runs"]), 2)
        self.assertEqual({r["engine"] for r in panel["runs"]}, {"chatgpt", "perplexity"})

    def test_gaps_stats_and_priority(self):
        g = self.art["gaps"]
        st = g["stats"]
        self.assertEqual((st["runs"], st["cells"], st["qualifying"]), (2, 6, 4))
        self.assertEqual((st["urls"], st["domains"]), (3, 3))
        self.assertEqual(st["high_priority"], 2)               # g2/crm/best 与 hubspot.com/crm 竞品同场
        top = g["domains"][0]
        self.assertEqual(top["domain"], "g2.com")              # 竞品同场降序 → 引用数降序
        self.assertEqual(top["priority"], "High")
        self.assertIn("g2.com", g["outreach_tips"])
        self.assertIn("竞品", g["outreach_tips"]["g2.com"])    # 外联提示口径(borrow-specs B2)

    def test_gap_labels_seven_way_tree(self):
        labels = {r["prompt"]: r["label"] for r in self.art["gaps"]["gap_labels"]}
        self.assertEqual(labels["best crm"], "Competitors own this AI answer space")
        self.assertEqual(labels["crm pricing"], "Mentioned without official citation")
        self.assertEqual(labels["helpdesk tools"], "Covered in this audit")

    def test_gaps_csv_contract(self):
        import csv
        with open(self.art["gaps_csv_path"], newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[0], ["Domain", "URL", "Citations", "Prompts", "Providers",
                                   "Competitors Mentioned", "Priority"])
        self.assertEqual(len(rows), 4)                         # 表头 + 3 URL
        self.assertEqual(rows[1][0], "g2.com")
        self.assertEqual(rows[1][2], "3")
        self.assertEqual(rows[1][6], "High")

    def test_report_mentions_own_domain_exclusion(self):
        self.assertIn("acme-corp.test", self.art["gaps_report"])   # 自有域排除声明
        self.assertIn("引用缺口报告", self.art["gaps_report"])


# ---------------------------------------------------------------- 环 9:benchmark_report
class TestBenchmarkChain(unittest.TestCase):
    """两份真实审计(audits 目录)+ 合成 4 站 CSV → 匿名分布报告 + 偏差自白 + 样本闸门。"""

    @classmethod
    def setUpClass(cls):
        cls.art = chain_artifacts()

    def test_aggregation_across_sources(self):
        b = self.art["bench"]
        self.assertEqual(b["n_sites"], 6)
        self.assertEqual(b["by_source"], {"audits": 2, "monitor_db": 0, "scores": 4})
        # 主分样本 = {0.0(修复前), 100.0(修复后), 55, 62, 71, 88}
        self.assertEqual(b["main"]["p50"], 66.5)
        self.assertEqual(b["main"]["mean"], 62.7)
        self.assertEqual(b["main"]["min"], 0.0)
        self.assertEqual(b["main"]["max"], 100.0)
        # 失败规则按"命中站数"聚合,规则 id 即 site_audit area
        rules = {r["rule"]: r["sites"] for r in b["top_failed_rules"]}
        self.assertIn("description", rules)
        self.assertEqual(rules["description"], 1)

    def test_anonymization_and_bias_confession(self):
        """站点标识(URL/域名/site 列)绝不进输出;偏差自白 markdown 首尾各一次。"""
        self.assertNotIn("chain-fixture.test", json.dumps(self.art["bench"], ensure_ascii=False))
        self.assertNotIn("chain-fixture.test", self.art["bench_md"])
        self.assertNotIn("anon-site-1", self.art["bench_md"])
        self.assertEqual(self.art["bench_md"].count("偏差自白"), 2)
        self.assertIn("自选样本", self.art["bench"]["bias_confession"])

    def test_min_sites_gate_refuses_small_sample(self):
        g = self.art["bench_gate"]
        self.assertEqual(g.returncode, 2)
        self.assertIn("拒绝出报告", g.stderr)


# ---------------------------------------------------------------- 全链冒烟(单测版本)
class TestFullChainSmoke(unittest.TestCase):
    """一条测试走完整链,subTest 标注环名——中途断掉时报告指出断在哪一环。"""

    def test_chain_smoke(self):
        art = chain_artifacts()
        with self.subTest(stage="1 site_audit --json(修复前 fail/修复后 pass)"):
            self.assertEqual(art["audit_rc_before"], 1)
            self.assertEqual(art["audit_rc_after"], 0)
        with self.subTest(stage="2 health_score 吃 raw 审计 → Weak/0.0"):
            self.assertEqual((art["health"]["main_score"], art["health"]["band"]), (0.0, "Weak"))
        with self.subTest(stage="3 prioritize 吃审计 → desc_missing/noindex_intent"):
            rules = {d["rule"] for d in art["priority"]["fix_now"]}
            self.assertTrue({"desc_missing", "noindex_intent"} <= rules)
        with self.subTest(stage="4 envelope 三源 → audit-data.json"):
            self.assertEqual(art["envelope"]["inputs"]["health"], "ok")
            self.assertEqual(art["envelope"]["summary"]["main_score"], 0.0)
        with self.subTest(stage="5 audit_compare → fixed 含 description/robots"):
            fixed = {(f["url"], f["rule"]) for f in art["compare"]["fixed_issues"]}
            self.assertIn((URL_PROBLEM, "description"), fixed)
            self.assertIn((URL_NOINDEX, "robots"), fixed)
        with self.subTest(stage="6 ci_format sarif/junit 结构"):
            self.assertEqual(art["sarif"]["version"], "2.1.0")
            ET.fromstring(art["junit"])
        with self.subTest(stage="7 fix_plan → FixItem 四类"):
            self.assertEqual({f["category"] for f in art["fixplan"]["fixes"]},
                             {"llms", "schema", "meta", "content"})
        with self.subTest(stage="8 citation_gaps → 高优先 g2.com"):
            self.assertEqual(art["gaps"]["domains"][0]["domain"], "g2.com")
        with self.subTest(stage="9 benchmark_report → 6 站分布"):
            self.assertEqual(art["bench"]["n_sites"], 6)


# ---------------------------------------------------------------- 发现的断裂(expectedFailure 钉死)
class TestDiscoveredInteropBreaks(unittest.TestCase):
    """真实互操作断裂(见文件头"发现的断裂清单");脚本修复后请移除装饰器。"""

    def setUp(self):
        self.art = chain_artifacts()

    def test_break1_fix_plan_rejects_raw_site_audit_stdout(self):
        """已修复(2026-10-11):fix_plan 现与链上其他消费者同款容错,从每个 '{' 试解。"""
        r = run_script("fix_plan.py", ["--audit", self.art["audit_before_raw"], "--json"])
        self.assertEqual(r.returncode, 0,
                         "fix_plan 应能吃 site_audit --json 原始 stdout;实际 rc=%s stderr=%s"
                         % (r.returncode, r.stderr.splitlines()[:1]))
        self.assertTrue(json.loads(r.stdout)["fixes"])

    def test_break2_citation_gaps_crashes_on_object_form_prompts(self):
        """已修复(2026-10-11):compute_gap_labels 经 _prompt_key 归一字符串/对象两种形态。"""
        tmp = tempfile.mkdtemp(prefix="seo_chain_brk2_")
        panel = os.path.join(tmp, "panel.json")
        self.assertEqual(run_script("citation_panel.py", [
            "init", "--brand", "Acme2", "--domain", "acme-corp.test",
            "--prompts-file", os.path.join(FIXTURES, "prompt-bank.md"),
            "--panel", panel]).returncode, 0)
        self.assertEqual(run_script("citation_panel.py", [
            "record", "--engine", "chatgpt", "--file",
            os.path.join(FIXTURES, "run-all-cited.csv"), "--panel", panel]).returncode, 0)
        gaps = os.path.join(tmp, "gaps.json")
        r = run_script("citation_gaps.py", ["--panel", panel, "--json", gaps])
        self.assertEqual(r.returncode, 0,
                         "citation_gaps 应能吃对象化 prompt 面板;实际 rc=%s stderr=%s"
                         % (r.returncode, r.stderr.strip().splitlines()[-1:]))
        self.assertTrue(os.path.exists(gaps))


if __name__ == "__main__":
    unittest.main(verbosity=2)
