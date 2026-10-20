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

=============================================================================
第二部分(2026-10-12 扩展):三高危零捕获 bug 的回归钉死 + 新管线链路冒烟(零网络)
=============================================================================
A. 回归钉死(测试审计报告②的三高危,脚本已修——此处防复发):
  A1 oracle_check 币种冲突:货币按 ISO 币种分桶,$49(USD) vs €49(EUR)/49元(CNY)
     数值相同币种不同 → 必须判冲突(旧实现只比数值,会把跨币种报一致);
     $49 vs $49(同币种同数值)→ 不报。fixture: oracle-brand.yaml/oracle-responses.json。
  A2 site_audit GBK 解码:fetch 解码链 Content-Type charset → BOM → 前 2KB meta
     charset 嗅探 → utf-8 replace 兜底。fixture gbk-page.html 为真 GBK 字节;测试
     打桩 urllib.request.urlopen(保留 sa.fetch→detect_encoding→decode 全真码路径),
     两条解码路由(响应头 charset=GBK / 无头靠 meta 嗅探)各自不乱码。
  A3 citation_panel.wilson_ci 真公式:Wald 近似在 k=0/n 时区间宽 0 → 零命中样本被
     误判 stable;真 Wilson k=0,n=3 → 上界≈0.5615(非零),k=n=3 → 下界≈0.4385,
     区间跨 0.5 → unstable。模块级断言钉死。
B. 新管线链路冒烟(上一步 stdout/文件 即 下一步输入):
  B1 pseo 生产线:pseo_pattern_mining(合成 GSC → GO 模式)→ pseo_batch_gate
     (同轴 batch.jsonl → PASS;title+h1 全同批 → STOP)→ pseo_cohort
     (init 冻结判读 + 两周 ingest + report PASS;同 id 重建拒绝)。
  B2 project.py run triage:SEO_PROJECT_SCRIPTS_DIR 打桩五脚本(site_crawl/
     site_audit/health_score/prioritize/envelope),断言编排序、审计 URL 选取
     (crawl 产物 status<400 前 5)、envelope 增量 --health/--priority、health 步
     失败时的容错降级与退出码。
  B3 content_queue collect 三源:trend_watch(只收 WATCH 态)+ gsc_mining(striking/
     decay 双桶,缺桶不猜)+ serp_overlap(真跑 serp_overlap.py 的存盘输出 → 共享
     ≥4 才入队);幂等去重;track 状态机 + report 遥测。
  B4 backlink_import → monitor 月检:ahrefs 原始导出 --out 统一格式;monitor
     check_backlinks 直接 import 兄弟模块 parse_export,原始/统一两形态通吃;
     缺文件 skipped 不猜、损坏 error 不猜(防假 0)。
  B5 split_test plan→assign→analyze:plan --save-plan 冻结预注册 → assign 分层
     随机(period1 分组)→ 按 assign 输出构造两臂 GSC CSV → analyze --plan 按冻结
     口径判读 significant_positive。
C. 输出契约快照:对上述全部新链的关键 JSON 字段做轻量形状断言
   (schema_version/verdict/judgment 等键存在与类型)。
新增 fixture(全部合成,域名 *.test 保留 TLD 永不可解析):oracle-brand.yaml、
oracle-responses.json、gbk-page.html(GBK 字节)、pseo-queries.csv、pseo-urls.txt、
pseo-batch.jsonl、pseo-batch-stop.jsonl、pseo-cohort-urls.txt、pseo-cohort-week1/2.csv、
cq-trend-state.json、cq-gsc-cur/prev.csv、cq-serp-keywords.csv、backlinks-ahrefs.csv、
st-urls.txt。
"""
import contextlib
import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime

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
    INFO finding)。返回完整 stdout 原文(S2a B4 起 --json 时只有 JSON 对象,人读行在 stderr;
    消费者的「前部文本行」容错仍保留,用于旧审计文件)。"""
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


# ---------------------------------------------------------------- 助手(第二部分)
def run_script_env(name, args=(), env_extra=None):
    """run_script + 额外环境变量(project triage 打桩需要 SEO_PROJECT_SCRIPTS_DIR)。"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8", **(env_extra or {}))
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def read_fixture_bytes(name):
    with open(os.path.join(FIXTURES, name), "rb") as f:
        return f.read()


def run_site_audit_real_fetch(pages, extra=None, market="zh"):
    """真实运行 site_audit.main() 且**保留 sa.fetch 真码路径**(fetch→detect_encoding
    →decode),仅打桩 urllib.request.urlopen(零网络;编码探测/解码与联网运行一致)。
    pages: {url: (status, headers, body_bytes)};extra 同型(根文件)。
    返回 (完整 stdout, 退出码)。"""
    import site_audit as sa
    import urllib.request
    responses = dict(pages)
    if extra:
        responses.update(extra)

    class _Resp:
        def __init__(self, status, headers, body):
            self.status, self.headers, self._body = status, headers, body

        def read(self, n=-1):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def stub_open(req, timeout=15):
        url = getattr(req, "full_url", None) or str(req)
        if url in responses:
            st, hdrs, body = responses[url]
            return _Resp(st, dict(hdrs), body)
        raise OSError("unreachable stub: %s" % url)

    orig_open, orig_argv = urllib.request.urlopen, sys.argv
    urllib.request.urlopen = stub_open
    buf = io.StringIO()
    sys.argv = ["site_audit.py", *pages.keys(), "--market", market, "--json"]
    rc = 0
    try:
        with contextlib.redirect_stdout(buf):
            sa.main()
    except SystemExit as e:
        rc = e.code or 0
    finally:
        urllib.request.urlopen = orig_open
        sys.argv = orig_argv
    return buf.getvalue(), rc


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
        """S2a B4 改:--json 时原始 stdout 只有一个 JSON 对象(--help「供 agent 消费」;
        jq 可直接解析),人读行走 stderr;有 CRITICAL(noindex)→ 退出码 1。"""
        with open(self.art["audit_before_raw"], encoding="utf-8") as f:
            raw = f.read()
        self.assertEqual(self.art["audit_rc_before"], 1)
        self.assertNotIn("== %s ==" % URL_PROBLEM, raw)       # 人读行不再混进 stdout
        self.assertEqual(json.loads(raw), self.art["blob_before"])
        blob = self.art["blob_before"]
        self.assertEqual(blob["schema_version"], 1)
        self.assertEqual(blob["audited"], 2)
        self.assertEqual(blob["critical"], 1)                 # S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15):只剩 noindex
        self.assertIsInstance(blob["results"], dict)

    def test_problem_page_schema_contract(self):
        """问题页:verdict/findings{severity,area,message}/meta{title,words,h1,jsonld}/
        ai_search_health{score,checks} —— 下一步逐字段的互操作契约。"""
        r = self.art["blob_before"]["results"][URL_PROBLEM]
        self.assertEqual(r["verdict"], "pass")                # S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15),本页无 CRITICAL
        finds = {(f["severity"], f["area"]) for f in r["findings"]}
        self.assertIn(("WARN", "description"), finds)         # 缺 description
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
        """S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15):只有 noindex 页带 CRITICAL → 主分 50.0/Fair。"""
        h = self.art["health"]
        self.assertEqual(self.art["audit_rc_before"], 1)
        self.assertEqual(h["main_score"], 50.0)
        self.assertEqual(h["band"], "Fair")
        self.assertEqual(h["urls_total"], 2)
        self.assertEqual(h["urls_clean"], 1)
        self.assertEqual(h["urls_refused"], 0)
        self.assertIn("coverage_note", h)

    def test_impact_and_categories(self):
        """impacts(Ryte 口径)按规则输出且可被 prioritize 摘要路径吃(rule/severity/hit_urls)。"""
        h = self.art["health"]
        top = h["impacts"][0]
        self.assertEqual(top["rule"], "robots")               # 1/2 命中 × CRITICAL²=4.5(S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15))
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
        self.assertEqual(by_rule["desc_missing"]["impact"], 1.0)   # 1/2 × WARN 权重 2(S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15))


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
        # S2a B2 改:修复文案按审计市场阈值(en:desc_min 77–上限 155),不再写死 ~155
        self.assertTrue(desc["recommendation"].startswith("补 meta description(77-155 chars)"),
                        desc["recommendation"])
        # 行动计划分派:CRITICAL → 立即(本周);S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15) → description 进短期(月内)
        phase0 = env["action_plan"]["phases"][0]
        self.assertEqual(phase0["name"], "立即(本周)")
        self.assertEqual({i["rule_id"] for i in phase0["items"]}, {"robots"})
        self.assertIn("description", {i["rule_id"] for i in env["action_plan"]["phases"][1]["items"]})
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
        self.assertEqual(rep["delta"]["main_score"], 50.0)     # 50.0 → 100.0(S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15))
        self.assertEqual(rep["delta"]["ai_search_health_mean"], 7.5)
        self.assertEqual(rep["delta"]["coverage_ratio"], 1.0)

    def test_verdict_page_and_ai_changes(self):
        rep = self.art["compare"]
        vc = {v["url"]: (v["old"], v["new"]) for v in rep["verdict_changes"]}
        self.assertEqual(vc, {URL_NOINDEX: ("fail", "pass")})   # 问题页修复前已是 pass(S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15))
        ai = {a["url"]: a for a in rep["ai_health_changes"]}
        self.assertEqual(ai[URL_PROBLEM]["delta"], 15)         # semantic_html 修复 +15
        pc = {p["url"]: {c["field"] for c in p["changes"]} for p in rep["pages_changed"]}
        self.assertTrue({"word_count", "h1"} <= pc[URL_PROBLEM])  # meta.words/meta.h1 被吃

    def test_baseline_gate_trips_on_regression(self):
        """反向对比(跌 50 分)> 阈值 5 → tripped + 退出码 1(Lumar Protect 语义)。"""
        gate = self.art["compare_gate"]["baseline_gate"]
        self.assertTrue(gate["tripped"])
        self.assertEqual(gate["drop"], 50.0)                   # 100 → 50(S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15))


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
        # S2a B3 改:noindex 页有服务端内容,不再报「无 noscript 回退」→ 13+3
        self.assertEqual(len(run["results"]), 16)              # 13(问题页)+3(noindex 页)条非 SKIP finding
        self.assertEqual({r["level"] for r in run["results"]},
                         {"error", "warning", "note"})         # CRITICAL/WARN/INFO 三档映射
        for r in run["results"]:
            uri = r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
            self.assertTrue(uri.startswith(HOST))              # uri=被审计 URL
        self.assertIn("description", {r["ruleId"] for r in run["results"]})
        props = run["invocations"][0]["properties"]
        self.assertEqual(props["main_score"], 50.0)            # S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15)
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
        self.assertEqual(props["audit.score"], "50.0")          # S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15)
        self.assertEqual(props["ai_search_health"], "77.5")

    def test_github_annotations(self):
        lines = self.art["github"].splitlines()
        self.assertTrue(lines[0].startswith("::notice title=SEO::"))
        self.assertIn("::warning title=SEO::[description]", self.art["github"])   # S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15)
        self.assertIn("::error title=SEO::[robots]", self.art["github"])

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
        self.assertEqual(fp["verdict"], "pass")                # S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15):问题页无 CRITICAL
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
        # 主分样本 = {50.0(修复前,S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15)), 100.0(修复后), 55, 62, 71, 88}
        self.assertEqual(b["main"]["p50"], 66.5)
        self.assertEqual(b["main"]["mean"], 71.0)
        self.assertEqual(b["main"]["min"], 50.0)
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
        with self.subTest(stage="2 health_score 吃 raw 审计 → Fair/50.0"):   # S2a 2026-10-21:description 缺失按 Google 文档降 WARN(B15)
            self.assertEqual((art["health"]["main_score"], art["health"]["band"]), (50.0, "Fair"))
        with self.subTest(stage="3 prioritize 吃审计 → desc_missing/noindex_intent"):
            rules = {d["rule"] for d in art["priority"]["fix_now"]}
            self.assertTrue({"desc_missing", "noindex_intent"} <= rules)
        with self.subTest(stage="4 envelope 三源 → audit-data.json"):
            self.assertEqual(art["envelope"]["inputs"]["health"], "ok")
            self.assertEqual(art["envelope"]["summary"]["main_score"], 50.0)
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


# =====================================================================
# 第二部分 A:三高危零捕获 bug 的回归钉死(脚本已修,此处防复发)
# =====================================================================

# ---- A1 oracle 币种冲突:工件(惰性一次构建) ----
_ORACLE_ART = None


def oracle_artifacts():
    """oracle_check 真跑:brand.yaml($49/月 定价事实)× responses(€49/$49/49元)。"""
    global _ORACLE_ART
    if _ORACLE_ART is not None:
        return _ORACLE_ART
    tmp = tempfile.mkdtemp(prefix="seo_chain_oracle_")
    out_state = os.path.join(tmp, "findings.json")
    r = run_script("oracle_check.py",
                   ["--facts", os.path.join(FIXTURES, "oracle-brand.yaml"),
                    "--responses", os.path.join(FIXTURES, "oracle-responses.json"),
                    "--out", out_state, "--json"])
    assert r.returncode == 0, "oracle_check 失败: %s" % r.stderr[:400]
    art = {"payload": json.loads(r.stdout), "state_path": out_state,
           "report": run_script("oracle_check.py", [
               "--facts", os.path.join(FIXTURES, "oracle-brand.yaml"),
               "--responses", os.path.join(FIXTURES, "oracle-responses.json"),
               "--out", out_state]).stdout}
    with open(out_state, encoding="utf-8") as f:
        art["state"] = json.load(f)
    _ORACLE_ART = art
    return art


class TestRegressionOracleCurrency(unittest.TestCase):
    """R5 回归钉死①:$49(USD) vs €49(EUR)/49元(CNY) 数值相同币种不同 → 必须判冲突;
    $49 vs $49 同币种同数值 → 不报(货币按 ISO 分桶,数值与币种都相同才判一致)。"""

    @classmethod
    def setUpClass(cls):
        cls.art = oracle_artifacts()

    def test_currency_conflicts_flagged(self):
        p = self.art["payload"]
        self.assertEqual(p["schema_version"], 2)
        self.assertEqual(p["facts_count"], 3)
        self.assertEqual(len(p["findings"]), 2)              # €49 与 49元 两条冲突
        for f in p["findings"]:
            self.assertEqual(f["kind"], "number")
            self.assertEqual(f["severity"], "critical")      # 定价事实 → critical
            self.assertIn("currency/USD", f["why_flagged"])  # 已验证事实按币种标 USD
        claims = {f["ai_claim"] for f in p["findings"]}
        self.assertTrue(any("€49" in c for c in claims))
        self.assertTrue(any("49元" in c for c in claims))

    def test_same_currency_not_flagged_and_metrics(self):
        """同币种同数值($49 USD)的响应不产 finding;指标只按 active finding 计。"""
        p = self.art["payload"]
        flagged_idx = {f["source_response"]["index"] for f in p["findings"]}
        self.assertEqual(flagged_idx, {0, 2})                # 响应 1($49 一致)干净
        m = p["metrics"]
        self.assertEqual(m["inaccuracy_pct"], 66.7)          # 2/3 响应含 active finding
        self.assertEqual(m["model_accuracy"], {"chatgpt": 50.0, "perplexity": 0.0})
        self.assertEqual(m["topics_ai_gets_wrong"], {"offerings": 2})
        for f in p["findings"]:                              # Athena finding 字段契约
            for key in ("fingerprint", "status", "possible_sources", "source_response"):
                self.assertIn(key, f)
            self.assertEqual(f["status"], "pending")
            self.assertEqual(f["possible_sources"], [])      # 由 agent 调查后填写
        self.assertIn("样本不足", "".join(p["warnings"]))    # <25 条 facts 的置信警告


# ---- A2 GBK 解码:真 fetch→detect_encoding→decode,仅 urlopen 打桩 ----
_GBK_ART = None


def gbk_artifacts():
    """GBK 字节 fixture 走两条解码路由:响应头 charset=GBK / 无头 meta 嗅探。"""
    global _GBK_ART
    if _GBK_ART is not None:
        return _GBK_ART
    gbk_body = read_fixture_bytes("gbk-page.html")
    raw, rc = run_site_audit_real_fetch({
        HOST + "/gbk-meta": (200, {"Content-Type": "text/html"}, gbk_body),
        HOST + "/gbk-ctype": (200, {"Content-Type": "text/html; charset=GBK"}, gbk_body),
    }, extra={HOST + "/robots.txt": (200, {}, read_fixture("robots.txt").encode("utf-8")),
              HOST + "/sitemap.xml": (200, {}, read_fixture("sitemap.xml").encode("utf-8"))})
    _GBK_ART = {"raw": raw, "rc": rc, "blob": extract_audit_blob(raw)}
    return _GBK_ART


class TestRegressionGbkDecoding(unittest.TestCase):
    """R5 回归钉死②:site_audit fetch 解码链(Content-Type charset→BOM→meta 嗅探→
    utf-8 兜底)——GBK 页面不再全量乱码(旧实现 utf-8 replace 把 GBK 双字节打烂)。"""

    @classmethod
    def setUpClass(cls):
        cls.art = gbk_artifacts()

    def _page(self, url):
        r = self.art["blob"]["results"][HOST + url]
        title = r["meta"]["title"]
        self.assertNotIn("\ufffd", title)                    # 无替换符(乱码标志)
        self.assertNotIn("锟斤拷", title)                    # 无 GBK→UTF8 双重错译特征
        return r, title

    def test_meta_charset_sniffing_route(self):
        """无响应头 charset → 前 2KB meta charset=gbk 嗅探命中。"""
        r, title = self._page("/gbk-meta")
        self.assertEqual(title, "项目管理软件选购指南")       # 逐字符精确解码
        self.assertEqual(r["verdict"], "pass")               # 无 CRITICAL
        self.assertGreater(r["meta"]["words"], 200)          # CJK 逐字计词不丢

    def test_content_type_charset_route(self):
        """响应头 charset=GBK 优先命中(同字节,同解码结果)。"""
        r, title = self._page("/gbk-ctype")
        self.assertEqual(title, "项目管理软件选购指南")
        self.assertEqual(self.art["rc"], 0)                  # 双页 pass → 退出码 0

    def test_decoding_does_not_fabricate_findings(self):
        """解码正确性以"不产解码类噪音 finding"为证:两页只允许结构性
        WARN/INFO(og/canonical 等),不得出现因乱码导致的标题/描述长度误判 CRITICAL。"""
        for url in ("/gbk-meta", "/gbk-ctype"):
            r = self.art["blob"]["results"][HOST + url]
            crit = [f for f in r["findings"] if f["severity"] == "CRITICAL"]
            self.assertEqual(crit, [], url)
            descs = [f for f in r["findings"] if f["area"] == "description"]
            self.assertTrue(all(f["severity"] != "CRITICAL" for f in descs), url)


# ---- A3 Wilson 真公式:模块级断言 ----
class TestRegressionWilsonCi(unittest.TestCase):
    """R5 回归钉死③:Wilson score interval 真公式(旧 Wald 近似 k=0/n 时区间宽 0,
    零命中/全命中样本被误判 stable)。k=0,n=3 → 上界≈0.5615 非零、跨 0.5 → unstable。"""

    def test_zero_hits_interval_nonzero_width(self):
        import citation_panel as cp
        p, lo, hi, unstable = cp.wilson_ci(0, 3)             # 零命中样本
        self.assertEqual(p, 0.0)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.5615, places=3)         # 非零上界(Wald 会得 0)
        self.assertGreater(hi, 0.5)                          # 区间跨 0.5 线
        self.assertTrue(unstable)                            # 不得误判 stable
        p, lo, hi, unstable = cp.wilson_ci(3, 3)             # 全命中样本
        self.assertEqual(p, 1.0)
        self.assertAlmostEqual(lo, 0.4385, places=3)         # 非零宽下界
        self.assertLess(lo, 0.5)
        self.assertTrue(unstable)

    def test_typical_cases_and_guard(self):
        import citation_panel as cp
        p, lo, hi, unstable = cp.wilson_ci(2, 3)             # p̂=2/3 → CI 跨 0.5
        self.assertAlmostEqual(p, 2 / 3, places=6)
        self.assertAlmostEqual(lo, 0.2077, places=3)
        self.assertAlmostEqual(hi, 0.9385, places=3)
        self.assertTrue(unstable)
        _p, lo, hi, unstable = cp.wilson_ci(80, 100)         # 80% 大样本 → 不跨 0.5
        self.assertGreater(lo, 0.5)
        self.assertLess(hi, 1.0)
        self.assertFalse(unstable)
        self.assertIsNone(cp.wilson_ci(0, 0))                # n=0 守卫 → None(不猜)


# =====================================================================
# 第二部分 B1:pseo 生产线链(pattern_mining → batch_gate → cohort)
# =====================================================================
_PSEO_ART = None


def pseo_artifacts():
    """pseo 三件套真跑:模式挖掘(GO 判定)→ 批次闸门(PASS/STOP)→ cohort 两周判读。"""
    global _PSEO_ART
    if _PSEO_ART is not None:
        return _PSEO_ART
    tmp = tempfile.mkdtemp(prefix="seo_chain_pseo_")
    art = {"tmp": tmp}

    mining = run_script("pseo_pattern_mining.py", [
        "--gsc", os.path.join(FIXTURES, "pseo-queries.csv"),
        "--urls", os.path.join(FIXTURES, "pseo-urls.txt"), "--json"])
    assert mining.returncode == 0, mining.stderr[:400]
    art["mining"] = json.loads(mining.stdout)

    gate = run_script("pseo_batch_gate.py",
                      ["--records", os.path.join(FIXTURES, "pseo-batch.jsonl"), "--json"])
    assert gate.returncode == 0, gate.stderr[:400]
    art["gate_pass"] = json.loads(gate.stdout)
    gate_stop = run_script("pseo_batch_gate.py",
                           ["--records", os.path.join(FIXTURES, "pseo-batch-stop.jsonl"),
                            "--json"])
    assert gate_stop.returncode == 1, "must_differ 批次应 STOP 阻断(exit 1)"
    art["gate_stop"] = json.loads(gate_stop.stdout)

    state = os.path.join(tmp, "pseo_cohorts.json")
    crit = '{"weeks":2,"min_index_rate":0.6,"consec_pos_wow":1}'
    art["init"] = run_script("pseo_cohort.py", [
        "init", "--cohort_id", "vs-batch-01", "--template-version", "v1",
        "--urls", os.path.join(FIXTURES, "pseo-cohort-urls.txt"),
        "--criteria", crit, "--state", state, "--json"])
    art["ing1"] = run_script("pseo_cohort.py", [
        "ingest", "--cohort", "vs-batch-01",
        "--gsc", os.path.join(FIXTURES, "pseo-cohort-week1.csv"),
        "--week", "2026-09-28", "--state", state, "--json"])
    art["ing2"] = run_script("pseo_cohort.py", [
        "ingest", "--cohort", "vs-batch-01",
        "--gsc", os.path.join(FIXTURES, "pseo-cohort-week2.csv"),
        "--week", "2026-10-05", "--state", state, "--json"])
    rep = run_script("pseo_cohort.py", ["report", "--cohort", "vs-batch-01",
                                        "--state", state, "--json"])
    assert rep.returncode == 0, rep.stderr[:400]
    art["report"] = json.loads(rep.stdout)
    art["reinit"] = run_script("pseo_cohort.py", [
        "init", "--cohort_id", "vs-batch-01", "--template-version", "v2",
        "--urls", os.path.join(FIXTURES, "pseo-cohort-urls.txt"), "--state", state])
    _PSEO_ART = art
    return art


class TestPseoPipelineChain(unittest.TestCase):
    """pseo 生产线三件互操作:挖掘的 GO 模式 → 同轴批次过闸 → 发布成 cohort 周喂判读。"""

    @classmethod
    def setUpClass(cls):
        cls.art = pseo_artifacts()

    def test_pattern_mining_go_verdict(self):
        m = self.art["mining"]
        self.assertEqual(m["tool"], "pseo_pattern_mining")
        self.assertEqual(sum(m["weights"].values()), 100)    # gates §八 30/25/20/15/10
        by_id = {r["id"]: r for r in m["patterns"]}
        vs = by_id["vs"]
        self.assertEqual(vs["variants"], 5)                  # 4 英文 + 1 中文变体
        self.assertEqual(vs["verdict"], "GO")                # score 97 ≥50 且变体 ≥3
        self.assertEqual(vs["score"], 97)
        self.assertEqual(vs["coverage_urls"], 1)             # urls 清单命中 /vs/acme-vs-hubspot
        self.assertEqual(vs["entities_distinct"], 5)         # acme/hubspot/zoho/salesforce/pipedrive
        self.assertEqual(by_id["pricing"]["verdict"], "WHITE_SPACE")   # 变体 2<3
        self.assertEqual(by_id["glossary"]["verdict"], "WHITE_SPACE")
        self.assertEqual(m["meta"]["editorial"], 2)          # /blog/ 编辑页排除出分析
        self.assertEqual(m["meta"]["unmatched_count"], 1)

    def test_batch_gate_pass(self):
        g = self.art["gate_pass"]
        self.assertEqual(g["verdict"], "PASS")
        st = g["stats"]
        self.assertEqual(st["records_kept"], 4)
        self.assertEqual(st["facts_total"], 8)
        self.assertEqual(st["warnings"], 0)
        self.assertGreaterEqual(st["uniqueness_pct"], 40)    # 唯一度闸
        self.assertLess(st["boilerplate_pct"], 60)           # 样板比闸
        self.assertGreaterEqual(st["word_count_min"], 400)   # 页型地板闸
        self.assertEqual(st["near_dup_pairs"], 0)
        self.assertEqual(g["stop_items"], [])

    def test_batch_gate_stops_must_differ(self):
        """title+h1(必须不同区块)全同 → STOP 阻断发布并退回数据层清单。"""
        g = self.art["gate_stop"]
        self.assertEqual(g["verdict"], "STOP")
        kinds = [s["kind"] for s in g["stop_items"]]
        self.assertIn("must_differ_duplicate", kinds)
        self.assertEqual(sorted(g["stats"]["return_to_data"]), ["dup-a", "dup-b"])

    def test_cohort_two_week_pass(self):
        i1, i2 = json.loads(self.art["ing1"].stdout), json.loads(self.art["ing2"].stdout)
        init = json.loads(self.art["init"].stdout)
        self.assertTrue(init["criteria_frozen"])             # 预注册判读冻结
        self.assertEqual(init["criteria"], {"weeks": 2, "min_index_rate": 0.6,
                                            "consec_pos_wow": 1})
        self.assertEqual((i1["source_rows"], i1["matched_urls"], i1["indexed_proxy_est"]),
                         (5, 4, 3))                          # cohort 外行(/blog/)被忽略
        self.assertEqual((i2["matched_urls"], i2["indexed_proxy_est"]), (5, 4))
        rep = self.art["report"]
        self.assertEqual(rep["judgment"]["state"], "PASS")
        checks = rep["judgment"]["checks"]
        self.assertEqual(checks["index_rate_cum_est"]["value"], 0.8)   # 累计 4/5
        self.assertTrue(checks["index_rate_cum_est"]["pass"])
        self.assertEqual(checks["consec_pos_wow"]["value"], 1)         # 周环比上行为
        self.assertEqual([s["week"] for s in rep["series"]],
                         ["2026-09-28", "2026-10-05"])
        self.assertIn("[est]", rep["disclaimers"][0])        # 索引代理口径声明

    def test_cohort_reinit_refused(self):
        """同 id 重复 init 直接拒绝(判读标准冻结,防事后移动球门)。"""
        self.assertEqual(self.art["reinit"].returncode, 2)
        self.assertIn("禁止同 id 重建", self.art["reinit"].stderr)


# =====================================================================
# 第二部分 B2:project.py run triage 编排(SEO_PROJECT_SCRIPTS_DIR 打桩)
# =====================================================================
_TRIAGE_SITE = "https://proj-fixture.test"
_TRIAGE_PAGES = [(_TRIAGE_SITE + "/pricing/acme-pro", 200),
                 (_TRIAGE_SITE + "/pricing/acme-team", 200),
                 (_TRIAGE_SITE + "/features/board", 200),
                 (_TRIAGE_SITE + "/features/timeline", 200),
                 (_TRIAGE_SITE + "/docs/setup", 200),
                 (_TRIAGE_SITE + "/broken-link", 404)]
_TRIAGE_STUB_HDR = '''import json, os, sys
LOG = os.environ.get("TRIAGE_STUB_LOG")
if LOG:
    with open(LOG, "a") as f:
        f.write(json.dumps({"script": "%(name)s", "argv": sys.argv[1:]}) + "\\n")
'''
_TRIAGE_STUBS = {
    "site_crawl.py": (
        'site, rest = sys.argv[1], sys.argv[2:]\n'
        'out = rest[rest.index("--out") + 1]; urls_out = rest[rest.index("--urls-out") + 1]\n'
        'pages = ' + repr(_TRIAGE_PAGES) + '\n'
        'doc = {"schema_version": 1, "site": site, "pages": [{"url": u, "status": s} for u, s in pages]}\n'
        'json.dump(doc, open(out, "w"))\n'
        'open(urls_out, "w").write("\\n".join(u for u, _ in pages))\n'
        'print("crawl stub done")\n'),
    "site_audit.py": (
        'urls = [a for a in sys.argv[1:] if "://" in a]\n'
        'results = {}\n'
        'for u in urls:\n'
        '    results[u] = {"verdict": "fail", "findings": [{"severity": "CRITICAL", "area": "description", "message": "stub: 缺失"}], "meta": {"title": "t", "words": 300, "h1": 1}}\n'
        'print("== 审计(stub) ==")\n'
        'print(json.dumps({"schema_version": 1, "audited": len(urls), "critical": len(urls), "results": results}))\n'),
    "health_score.py": 'print(json.dumps({"main_score": 0.0, "band": "Weak", "urls_total": 5, "urls_clean": 0}))\n',
    "prioritize.py": 'print(json.dumps({"input_format": "site_audit", "fix_now": [{"rule": "desc_missing"}], "degraded_rules": []}))\n',
    "envelope.py": (
        'rest = sys.argv[1:]\n'
        'od = rest[rest.index("--out-dir") + 1]\n'
        'os.makedirs(od, exist_ok=True)\n'
        'cats = [{"name": "rankability", "findings": [{"rule_id": "description", "title": "缺失 meta description", "severity": "CRITICAL", "affected": 5, "recommendation": "补 meta description"}]}]\n'
        'json.dump({"inputs": {"audit": "ok"}, "categories": cats, "summary": {"main_score": 0.0}}, open(os.path.join(od, "audit-data.json"), "w"))\n'
        'print("envelope stub done")\n'),
}
_TRIAGE_HEALTH_FAIL = ('import sys\nsys.stderr.write("stub health failure\\n")\nsys.exit(2)\n')
_TRIAGE_ART = None


def _write_triage_stubs(stubs_dir, health_fail=False):
    os.makedirs(stubs_dir, exist_ok=True)
    for name, body in _TRIAGE_STUBS.items():
        if name == "health_score.py" and health_fail:
            body = _TRIAGE_HEALTH_FAIL
        with open(os.path.join(stubs_dir, name), "w", encoding="utf-8") as f:
            f.write(_TRIAGE_STUB_HDR % {"name": name[:-3]} + body)


def triage_artifacts():
    """打桩脚本下真实跑 project.py init + run triage 两次(健康步失败降级向)。"""
    global _TRIAGE_ART
    if _TRIAGE_ART is not None:
        return _TRIAGE_ART
    tmp = tempfile.mkdtemp(prefix="seo_chain_triage_")
    ws = os.path.join(tmp, "proj-fixture.seo")
    stubs = os.path.join(tmp, "stubs")
    _write_triage_stubs(stubs)
    assert run_script("project.py", ["init", "--site", _TRIAGE_SITE, "--market", "en",
                                     "--dir", ws, "--json"]).returncode == 0
    log1 = os.path.join(tmp, "calls-1.jsonl")
    r1 = run_script_env("project.py", ["run", "triage", "--dir", ws, "--max", "5", "--json"],
                        env_extra={"SEO_PROJECT_SCRIPTS_DIR": stubs, "TRIAGE_STUB_LOG": log1})
    assert r1.returncode == 0, r1.stderr[:600]
    art = {"tmp": tmp, "ws": ws, "stubs": stubs,
           "triage": json.loads(r1.stdout), "log_path": log1,
           "calls": [json.loads(ln) for ln in open(log1, encoding="utf-8")]}

    # 第二轮:health 步失败(rc=2)→ envelope 不吃 --health,prioritize 照跑,总 rc=1
    _write_triage_stubs(stubs, health_fail=True)
    log2 = os.path.join(tmp, "calls-2.jsonl")
    r2 = run_script_env("project.py", ["run", "triage", "--dir", ws, "--max", "5", "--json"],
                        env_extra={"SEO_PROJECT_SCRIPTS_DIR": stubs, "TRIAGE_STUB_LOG": log2})
    art["triage_degraded"] = (r2.returncode, json.loads(r2.stdout))
    art["calls_degraded"] = [json.loads(ln) for ln in open(log2, encoding="utf-8")]
    _TRIAGE_ART = art
    return art


class TestProjectTriageOrchestration(unittest.TestCase):
    """run triage 编排契约:五步子进程顺序、审计样本选取、产物落 history/、容错降级。"""

    @classmethod
    def setUpClass(cls):
        cls.art = triage_artifacts()

    def test_step_order_and_audit_sampling(self):
        """编排序 = crawl→audit→health→prioritize→envelope;审计 URL = crawl 产物
        status<400 的前 5(404 剔除);envelope 增量拿到 --health/--priority。"""
        self.assertEqual([s["name"] for s in self.art["triage"]["steps"]],
                         ["crawl", "audit", "health", "prioritize", "envelope"])
        self.assertTrue(all(s["ok"] for s in self.art["triage"]["steps"]))
        order = [c["script"] for c in self.art["calls"]]
        self.assertEqual(order, ["site_crawl", "site_audit", "health_score",
                                 "prioritize", "envelope"])
        audit_call = next(c for c in self.art["calls"] if c["script"] == "site_audit")
        audited = [a for a in audit_call["argv"] if a.startswith("http")]
        self.assertEqual(len(audited), 5)
        self.assertNotIn(_TRIAGE_SITE + "/broken-link", audited)   # 404 不喂审计
        env_call = next(c for c in self.art["calls"] if c["script"] == "envelope")
        self.assertIn("--health", env_call["argv"])
        self.assertIn("--priority", env_call["argv"])

    def test_triage_json_contract_and_artifacts(self):
        t = self.art["triage"]
        self.assertEqual(t["schema_version"], 1)
        self.assertEqual(t["site"], _TRIAGE_SITE)
        for s in t["steps"]:                                 # 逐步完整命令/退出码契约
            self.assertIn("cmd", s)
            self.assertIsInstance(s["rc"], int)
            self.assertIsNone(s["skipped"])
        hist = t["run_dir"]
        for rel in ("crawl.json", "urls.txt", "audit.json", "health.json",
                    "priority.json", "envelope/audit-data.json", "triage.json"):
            self.assertTrue(os.path.isfile(os.path.join(hist, rel)), rel)
        v = t["verdict"]
        self.assertEqual(v["site_type"]["suggested"], "SaaS / 软件营销站")
        self.assertEqual(v["site_type"]["share"], 0.667)     # /pricing,/features 4/6 页
        self.assertEqual(v["basis"], "envelope summary")
        self.assertEqual([(a["severity"], a["rule_id"], a["affected"])
                          for a in v["top_actions"]],
                         [("CRITICAL", "description", 5)])   # envelope 透传的修复建议

    def test_health_failure_degrades_not_halts(self):
        """health 步 rc=2 → envelope 少吃 --health(仍吃 --priority),总退出码 1。"""
        rc, t = self.art["triage_degraded"]
        self.assertEqual(rc, 1)
        by_name = {s["name"]: s for s in t["steps"]}
        self.assertFalse(by_name["health"]["ok"])
        self.assertTrue(by_name["prioritize"]["ok"])         # 失败不终止,续跑其余
        self.assertTrue(by_name["envelope"]["ok"])
        env_call = next(c for c in self.art["calls_degraded"]
                        if c["script"] == "envelope")
        self.assertNotIn("--health", env_call["argv"])       # 缺输入的下游增量不传
        self.assertIn("--priority", env_call["argv"])


# =====================================================================
# 第二部分 B3:content_queue collect 三源(serp_overlap 真跑 → 存盘输出入队)
# =====================================================================
_CQ_ART = None


def cq_artifacts():
    global _CQ_ART
    if _CQ_ART is not None:
        return _CQ_ART
    tmp = tempfile.mkdtemp(prefix="seo_chain_cq_")
    serp_out = os.path.join(tmp, "serp-out.txt")
    so = run_script("serp_overlap.py", [os.path.join(FIXTURES, "cq-serp-keywords.csv")])
    assert so.returncode == 0, so.stderr[:300]
    with open(serp_out, "w", encoding="utf-8") as f:
        f.write(so.stdout)
    ops = os.path.join(tmp, "contentops.json")
    c1 = run_script("content_queue.py", [
        "collect", "--trend-state", os.path.join(FIXTURES, "cq-trend-state.json"),
        "--gsc", os.path.join(FIXTURES, "cq-gsc-cur.csv"),
        "--gsc", os.path.join(FIXTURES, "cq-gsc-prev.csv"),
        "--serp-out", serp_out, "--file", ops, "--json"])
    assert c1.returncode == 0, c1.stderr[:400]
    art = {"tmp": tmp, "serp_out_text": so.stdout, "collect": json.loads(c1.stdout),
           "ops_path": ops}
    art["collect_again"] = json.loads(run_script("content_queue.py", [
        "collect", "--gsc", os.path.join(FIXTURES, "cq-gsc-cur.csv"),
        "--file", ops, "--json"]).stdout)
    for status in ("briefed", "drafting", "gated"):
        r = run_script("content_queue.py", ["track", "CQ-002", "--status", status,
                                            "--file", ops])
        assert r.returncode == 0, r.stderr[:300]
    assert run_script("content_queue.py", [
        "track", "CQ-002", "--status", "published", "--url",
        "https://chain-fixture.test/crm-vs-alternatives", "--file", ops]).returncode == 0
    art["report"] = json.loads(run_script("content_queue.py", [
        "report", "--file", ops, "--json"]).stdout)
    art["skip_transition"] = run_script("content_queue.py", [
        "track", "CQ-001", "--status", "published", "--file", ops])
    _CQ_ART = art
    return art


class TestContentQueueCollectChain(unittest.TestCase):
    """collect 三源合并:trend 只收 WATCH 态、gsc 双桶、serp 共享≥4 才入队;幂等去重。"""

    @classmethod
    def setUpClass(cls):
        cls.art = cq_artifacts()

    def test_three_sources_merged(self):
        c = self.art["collect"]
        self.assertEqual(c["schema_version"], 1)
        self.assertEqual(c["new"], 8)                        # trend1 + gsc6 + serp1
        self.assertEqual(c["skipped_dup"], 0)
        by_src = {}
        for it in c["ideas"]:
            by_src[it["source"]] = by_src.get(it["source"], 0) + 1
            for key in ("id", "source", "topic", "evidence", "score", "status",
                        "created", "history"):
                self.assertIn(key, it)                       # idea 统一形状
            self.assertEqual(it["status"], "idea")
        self.assertEqual(by_src, {"trend_watch": 1, "gsc_mining:striking": 3,
                                  "gsc_mining:decay": 3, "serp_overlap": 1})
        self.assertEqual([it["id"] for it in c["ideas"]],
                         ["CQ-%03d" % i for i in range(1, 9)])   # id 连续分配
        topics = {it["topic"] for it in c["ideas"]}
        self.assertIn("AI 搜索引用新规", topics)              # watch 态收录
        self.assertNotIn("已过闸走 trend-jack 的热点", topics)  # go 态不收
        self.assertNotIn("尚未机检完的信号", topics)           # open 态不收

    def test_source_routing_and_scoring(self):
        """serp 源吃的是 serp_overlap.py 真实存盘输出(共享 5 → 缺口;共享 2 → 互链跳过);
        gsc striking 门槛(pos 5-20 且曝光≥20)与评分口径(TP×IC,常青 FB=1)。"""
        self.assertIn("crm for startups × crm for agencies", self.art["serp_out_text"])
        self.assertIn("同簇", self.art["serp_out_text"])
        serp_ideas = [it for it in self.art["collect"]["ideas"]
                      if it["source"] == "serp_overlap"]
        self.assertEqual(len(serp_ideas), 1)                 # 共享 5 的对入队
        self.assertIn("SERP 重叠 5/10", serp_ideas[0]["evidence"])
        topics = {it["topic"] for it in self.art["collect"]["ideas"]}
        self.assertNotIn("crm for startups × crm for clinics", topics)  # 互链不入队
        by_topic = {it["topic"]: it for it in self.art["collect"]["ideas"]}
        striking_top = next(it for it in self.art["collect"]["ideas"]
                            if it["source"] == "gsc_mining:striking"
                            and it["topic"] == "crm vs alternatives")
        self.assertAlmostEqual(striking_top["score"], 4.8)   # 10×800/2000×1.2
        self.assertNotIn("best crm for startups", topics)    # pos 3.1<5 不进 striking
        self.assertNotIn("deep dive niche topic", topics)    # 曝光 5<20 不进 striking
        self.assertIn("crm pricing calculator", topics)      # striking + decay 双桶
        trend = by_topic["AI 搜索引用新规"]
        self.assertTrue(4.0 <= trend["score"] <= 6.0)        # 5×0.8×FB(first_seen 时效)

    def test_collect_idempotent_and_state_machine(self):
        self.assertEqual((self.art["collect_again"]["new"],
                          self.art["collect_again"]["skipped_dup"]), (0, 3))  # 同源同题不重复
        rep = self.art["report"]
        self.assertEqual(rep["total"], 8)
        self.assertEqual(rep["counts"], {"idea": 7, "briefed": 0, "drafting": 0,
                                         "gated": 0, "published": 1, "measured": 0})
        self.assertEqual(rep["wip"], 0)                      # published 即出制
        self.assertEqual(rep["telemetry"]["lead_time_days"]["n"], 1)
        self.assertEqual(self.art["skip_transition"].returncode, 2)   # idea→published 跳级拒绝


# =====================================================================
# 第二部分 B4:backlink_import → monitor 月检(第 6 检查组)
# =====================================================================
_BL_ART = None


def backlink_artifacts():
    global _BL_ART
    if _BL_ART is not None:
        return _BL_ART
    import monitor
    tmp = tempfile.mkdtemp(prefix="seo_chain_bl_")
    unified = os.path.join(tmp, "unified.csv")
    payload = os.path.join(tmp, "bi.json")
    r = run_script("backlink_import.py", [os.path.join(FIXTURES, "backlinks-ahrefs.csv"),
                                          "--out", unified, "--brand", "acme",
                                          "--json", payload])
    assert r.returncode == 0, r.stderr[:400]
    with open(payload, encoding="utf-8") as f:
        bi = json.load(f)
    frozen_now = datetime(2026, 10, 12, 12, 0, 0)
    checks = {
        "ahrefs": monitor.check_backlinks(
            tmp, cfg={"backlinks_csv": os.path.join(FIXTURES, "backlinks-ahrefs.csv")},
            now=frozen_now),
        "unified": monitor.check_backlinks(tmp, cfg={"backlinks_csv": unified},
                                           now=frozen_now),
        "missing": monitor.check_backlinks(
            tmp, cfg={"backlinks_csv": os.path.join(tmp, "nope.csv")}, now=frozen_now),
    }
    bad = os.path.join(tmp, "bad.csv")
    with open(bad, "w", encoding="utf-8") as f:
        f.write("garbage header\nno structure here\n")
    checks["corrupt"] = monitor.check_backlinks(tmp, cfg={"backlinks_csv": bad},
                                                now=frozen_now)
    _BL_ART = {"tmp": tmp, "unified_path": unified, "bi": bi, "checks": checks,
               "unified_head": open(unified, encoding="utf-8").readline().strip()}
    return _BL_ART


class TestBacklinkMonitorChain(unittest.TestCase):
    """BYO 导入统一 → monitor 月检直接 import 兄弟 parse_export 消费(四形态通吃);
    缺文件 skipped 不猜、损坏 error 不猜(防假 0:绝不把读不了当外链归零)。"""

    @classmethod
    def setUpClass(cls):
        cls.art = backlink_artifacts()

    def test_backlink_import_unifies_ahrefs(self):
        bi = self.art["bi"]
        self.assertEqual(bi["format"], "ahrefs")             # 列头特征嗅探
        self.assertEqual(bi["input_rows"], 5)
        self.assertEqual(bi["dedup_dropped"], 0)
        self.assertEqual(len(bi["rows"]), 5)
        self.assertEqual(self.art["unified_head"],
                         "referring_domain,url,dr_or_urgency,anchor,first_seen,"
                         "last_seen,dofollow,type")          # 统一 8 列 schema
        for row in bi["rows"]:
            self.assertEqual(sorted(row), sorted(["referring_domain", "url",
                                                  "dr_or_urgency", "anchor",
                                                  "first_seen", "last_seen",
                                                  "dofollow", "type"]))
        feed = bi["summary"]["cite_domain_feed"]             # 直喂 cite_domain 契约
        self.assertEqual(feed["referring_domains"], 5)
        self.assertEqual(feed["dr_distribution"], {"0-30": 1, "30-50": 2,
                                                  "50-70": 1, "70-100": 1})
        self.assertEqual(len(feed["months"]), 5)             # first_seen 按月新链计数
        self.assertIsInstance(feed["anchor_exact_ratio"], float)

    def test_monitor_monthly_eats_both_forms(self):
        """月检消费原始 Ahrefs 导出与统一格式 CSV 同口径(引荐域总数/当月新增/清单)。"""
        for form in ("ahrefs", "unified"):
            c = self.art["checks"][form]
            self.assertEqual(c["state"], "ok", form)
            self.assertEqual(c["check"], "backlinks")
            self.assertEqual(c["metrics"]["format"], form)   # parse_export 嗅探互操作
            self.assertEqual(c["metrics"]["refdomains_total"], 5)
            self.assertEqual(c["metrics"]["refdomains_new"], 2)   # 近 31 天 first_seen
            self.assertEqual(c["metrics"]["domains"],
                             ["blog-partner.test", "dev-notes.test", "indie-blog.test",
                              "news-site.test", "roundup.test"])
            self.assertFalse(c["metrics"]["domains_truncated"])

    def test_monitor_never_guesses_on_bad_input(self):
        self.assertEqual(self.art["checks"]["missing"]["state"], "skipped")
        self.assertIn("不猜", self.art["checks"]["missing"]["notes"][0])
        self.assertEqual(self.art["checks"]["corrupt"]["state"], "error")
        self.assertIn("error", self.art["checks"]["corrupt"]["metrics"])


# =====================================================================
# 第二部分 B5:split_test plan→assign→analyze 数据流
# =====================================================================
_ST_ART = None


def split_artifacts():
    global _ST_ART
    if _ST_ART is not None:
        return _ST_ART
    tmp = tempfile.mkdtemp(prefix="seo_chain_st_")
    plan_file = os.path.join(tmp, "plan.json")
    pl = run_script("split_test.py", ["plan", "--pages", "24", "--baseline-clicks", "1.5",
                                      "--weeks", "2", "--mde", "0.1",
                                      "--save-plan", plan_file, "--json"])
    assert pl.returncode == 0, pl.stderr[:300]
    asg = run_script("split_test.py", ["assign", "--urls",
                                       os.path.join(FIXTURES, "st-urls.txt"),
                                       "--ratio", "0.5", "--seed", "42",
                                       "--crossover", "4", "--json"])
    assert asg.returncode == 0, asg.stderr[:300]
    assign = json.loads(asg.stdout)
    treated = [r["url"] for r in assign["assignments"] if r["period1"] == "treatment"]
    control = [r["url"] for r in assign["assignments"] if r["period1"] == "control"]
    t_csv, c_csv = os.path.join(tmp, "treated.csv"), os.path.join(tmp, "control.csv")
    with open(t_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Page", "Clicks", "Date"])
        for i, u in enumerate(treated):
            w.writerow([u, 20 + (i % 5) * 3, "2026-09-2%d" % (1 + i % 8)])
            w.writerow([u, 21 + (i % 4) * 3, "2026-10-0%d" % (1 + i % 8)])
    with open(c_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Page", "Clicks", "Date"])
        for i, u in enumerate(control):
            w.writerow([u, 10 + (i % 4) * 2, "2026-09-2%d" % (1 + i % 8)])
            w.writerow([u, 11 + (i % 5) * 2, "2026-10-0%d" % (1 + i % 8)])
    an = run_script("split_test.py", ["analyze", "--treated", t_csv, "--control", c_csv,
                                      "--weeks", "2", "--plan", plan_file, "--json"])
    assert an.returncode == 0, an.stderr[:400]
    _ST_ART = {"tmp": tmp, "plan": json.loads(pl.stdout),
               "plan_file": json.load(open(plan_file, encoding="utf-8")),
               "assign": assign, "analyze": json.loads(an.stdout),
               "n_treated": len(treated), "n_control": len(control)}
    return _ST_ART


class TestSplitTestDataFlow(unittest.TestCase):
    """plan 冻结预注册 → assign 分层随机 → analyze 吃 assign 产出的两臂数据并按冻结口径判读。"""

    @classmethod
    def setUpClass(cls):
        cls.art = split_artifacts()

    def test_plan_freezes_preregistration(self):
        p = self.art["plan"]
        self.assertEqual(p["schema_version"], 1)
        self.assertEqual(p["inputs"]["pages"], 24)
        self.assertEqual(p["power_at_mde"]["mde"], 0.1)
        self.assertIn("power", p["power_at_mde"])            # 功效 + adequate 旗标
        self.assertIn("adequate", p["power_at_mde"])
        self.assertEqual([r["power"] for r in p["requirements"]], [0.6, 0.8, 0.9])
        pf = self.art["plan_file"]                           # --save-plan 落档内容
        self.assertEqual(pf["params"]["weeks"], 2)
        self.assertEqual(pf["params"]["mde"], 0.1)
        self.assertEqual(pf["judgement"]["direction"], "positive")   # 判读口径冻结
        self.assertIn("read_when", pf["judgement"])

    def test_assign_strata_and_crossover(self):
        a = self.art["assign"]
        self.assertEqual(a["counts"], {"pages": 24, "treatment": 12, "control": 12})
        self.assertEqual(sorted(a["strata"]), ["how-to", "pricing", "vs"])   # 目录首段分层
        for st in a["strata"].values():
            self.assertEqual(st["treatment"], st["control"])  # 层内均分
        self.assertEqual(a["crossover_week"], 4)
        for r in a["assignments"]:                            # 第 4 周组间互换计划
            expected = {"treatment": "control", "control": "treatment"}[r["period1"]]
            self.assertEqual(r["period2"], expected)

    def test_analyze_eats_assign_output(self):
        """两臂 CSV 由 assign 的 period1 分组构造 → analyze 检出显著正向且达预注册 MDE。"""
        d = self.art["analyze"]
        self.assertEqual(d["schema_version"], 1)
        self.assertEqual((d["n_treated"], d["n_control"]),
                         (self.art["n_treated"], self.art["n_control"]))   # 12/12 全有效
        self.assertEqual(d["preprocess"]["treated"]["zero_click_removed"], 0)
        self.assertTrue(d["preregistered"])                  # --plan 预注册判读
        self.assertEqual(d["alpha_used"], 0.05)              # α 按冻结档
        self.assertEqual(d["verdict"], "significant_positive")
        self.assertGreater(d["ci95"][0], 0)                  # CI 下界>0
        self.assertGreater(d["relative_lift"], 0.5)          # ~2× 提升
        self.assertTrue(d["meets_preregistered_mde"])        # lift ≥ MDE 0.1
        self.assertEqual(d["weeks"], 2)


# =====================================================================
# 第二部分 C:新链输出契约快照(关键 JSON 字段形状断言)
# =====================================================================
class TestNewChainContractSnapshots(unittest.TestCase):
    """轻量形状快照:各新链输出的关键键存在性与类型(供 agent/CI 消费的字段名冻结)。"""

    def test_oracle_state_file_contract(self):
        state = oracle_artifacts()["state"]
        self.assertEqual(state["schema_version"], 2)
        self.assertIn("generated", state)
        self.assertTrue(all(f["fingerprint"] for f in state["findings"]))

    def test_pseo_and_triage_key_fields(self):
        self.assertIn("verdict", pseo_artifacts()["gate_pass"])
        self.assertIn("stats", pseo_artifacts()["gate_pass"])
        self.assertIn("judgment", pseo_artifacts()["report"])
        self.assertIn("series", pseo_artifacts()["report"])
        t = triage_artifacts()["triage"]
        for key in ("schema_version", "site", "run_dir", "steps", "verdict"):
            self.assertIn(key, t)
        self.assertIn("top_actions", t["verdict"])
        self.assertIn("recheck", t["verdict"])

    def test_queue_backlink_split_key_fields(self):
        cq = cq_artifacts()["collect"]
        for key in ("schema_version", "file", "new", "total", "sources", "ideas"):
            self.assertIn(key, cq)
        self.assertIn("wip", cq_artifacts()["report"])
        bi = backlink_artifacts()["bi"]
        for key in ("tool", "format", "rows", "summary"):
            self.assertIn(key, bi)
        an = split_artifacts()["analyze"]
        for key in ("verdict", "ci95", "relative_lift", "preprocess", "warnings"):
            self.assertIn(key, an)


if __name__ == "__main__":
    unittest.main(verbosity=2)
