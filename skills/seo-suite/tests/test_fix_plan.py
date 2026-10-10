#!/usr/bin/env python3
"""fix_plan.py(审计→修复物生成器)测试:standalone、合成 fixture、fetch 全打桩零网络
(tests/run_tests.py 自动发现本文件)。覆盖:6 类生成条件(缺→生成/全好→零误报)/
dry-run 预览 30 行截断/--only 过滤与非法值报错/--apply 只写 seo-fixes/ 且内容 html.escape/
审计 refused 不生成·退出码 2/收益预估封顶 100/FixItem 形状与 CATEGORY_MAX 权重派生。
用法: python3 tests/test_fix_plan.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import fix_plan as fp      # noqa: E402  (需先入 SCRIPTS 路径;其内部复用 site_audit/robots_posture)
import site_audit as sa    # noqa: E402

ROOT = "https://unit.test"


def stub_fetch(pages, root=ROOT):
    """零网络 fetch 替身:pages={路径: (status, headers, body) 或 None=404}。"""
    table = {root + path: v for path, v in pages.items()}

    def _fetch(url, timeout=15):
        if url in table and table[url] is not None:
            st, hdrs, body = table[url]
            return st, hdrs, body
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
    return _fetch


GOOD_HTML = ('<!doctype html><html lang="en"><head>'
             '<title>Unit Test Site Everything Present</title>'
             '<meta name="description" content="A sufficiently long description text that exceeds eighty characters easily for tests.">'
             '<link rel="canonical" href="https://unit.test/">'
             '<meta property="og:title" content="Unit Test Site">'
             '<meta property="og:description" content="og desc">'
             '<meta property="og:image" content="https://unit.test/og.png">'
             '<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite"}</script>'
             '</head><body><main><article><h1>Unit Test Main Heading</h1>'
             '<p>In short, here is the direct answer with the key facts included. ' + "filler body word " * 80 + '</p>'
             '<h2>Section One</h2><ul><li>alpha</li><li>beta</li><li>gamma</li><li>delta</li></ul>'
             '<h2>Section Two</h2><p>more body content for the unit test page</p>'
             '</article></main></body></html>')

# 无 title/desc/canonical/og/JSON-LD + 纯 div 无语义标签 + 词数<200(soft-thin)。
# 字节垫到 >200:过 site_audit 的 fetch 质量守卫(太小会被 [SKIP] 拒审计);点号不计词数。
BROKEN_HTML = ('<!doctype html><html lang="en"><head></head><body>'
               '<div><span>thin page ' + '.' * 180 + '</span></div></body></html>')

ROBOTS_OK = "User-agent: *\nAllow: /\n"
ROBOTS_BLOCK_PPX = "User-agent: *\nAllow: /\n\nUser-agent: PerplexityBot\nDisallow: /\n"
VALID_LLMSTXT = ("# Unit Test Site\n\n> A test summary blockquote.\n\n## Pages\n\n"
                 "- [a](https://unit.test/a): d\n- [b](https://unit.test/b): d\n- [c](https://unit.test/c): d\n")
MALFORMED_LLMSTXT = "> only summary, no H1\n\n- [a](https://unit.test/a): d\n"

GOOD_PAGES = {"/": (200, {}, GOOD_HTML), "/robots.txt": (200, {}, ROBOTS_OK),
              "/sitemap.xml": (200, {}, "<urlset><loc>https://unit.test/a</loc></urlset>"),
              "/llms.txt": (200, {}, VALID_LLMSTXT)}
BROKEN_PAGES = {"/": (200, {}, BROKEN_HTML)}     # 根文件全 404


class LiveGenerationTests(unittest.TestCase):
    """--url 现场(stub fetch,零网络):6 类生成条件 + 全好站点零误报"""

    def _live_view(self, pages, url=ROOT + "/"):
        orig = sa.fetch
        sa.fetch = stub_fetch(pages)
        try:
            return fp.view_from_live(url)
        finally:
            sa.fetch = orig

    def test_broken_site_generates_five_default_categories(self):
        view = self._live_view(BROKEN_PAGES)
        self.assertEqual(view["verdict"], "fail")                    # title/h1 CRITICAL 可修,不拒
        fixes = fp.build_fixes(view)                                 # 默认 DEFAULT_ON
        self.assertEqual([f["category"] for f in fixes],
                         ["robots", "llms", "schema", "meta", "content"])
        only_ai = fp.build_fixes(view, ("ai_discovery",))            # 可选类默认关,显式开启才生成
        self.assertEqual([f["category"] for f in only_ai], ["ai_discovery"])
        self.assertEqual(only_ai[0]["file_name"], "ai-summary.json")

    def test_good_site_generates_nothing(self):
        view = self._live_view(GOOD_PAGES)
        self.assertEqual(view["verdict"], "pass")
        self.assertEqual(fp.build_fixes(view), [])                   # 全部通过 → 零误报

    def test_robots_missing_creates_27_bot_template(self):
        view = self._live_view(BROKEN_PAGES)                         # robots.txt 404
        fixes = fp.build_fixes(view, ("robots",))
        self.assertEqual(len(fixes), 1)
        f = fixes[0]
        self.assertEqual((f["action"], f["file_name"]), ("create", "robots.txt"))
        self.assertEqual(f["content"].count("User-agent:"), 27)      # 27 bot 全量模板
        self.assertIn("User-agent: OAI-SearchBot\nAllow: /", f["content"])   # 引用 bot 专属规则
        self.assertIn("Sitemap: https://unit.test/sitemap.xml", f["content"])

    def test_robots_blocked_bot_append_and_allowed_none(self):
        view = self._live_view(dict(GOOD_PAGES, **{"/robots.txt": (200, {}, ROBOTS_BLOCK_PPX)}))
        f = fp.build_fixes(view, ("robots",))[0]
        self.assertEqual((f["action"], f["file_name"]), ("append", "robots-append.txt"))
        self.assertIn("User-agent: PerplexityBot\nAllow: /", f["content"])   # rp.fix_robots 三行格式
        self.assertIn("引用层(search)", f["content"])                          # 三层标题复用
        view_ok = self._live_view(GOOD_PAGES)
        self.assertEqual(fp.build_fixes(view_ok, ("robots",)), [])            # 全放行→不生成

    def test_llms_missing_malformed_valid(self):
        miss = fp.build_fixes(self._live_view(BROKEN_PAGES), ("llms",))[0]
        self.assertEqual((miss["action"], miss["file_name"]), ("create", "llms.txt"))
        body = miss["content"]
        self.assertTrue(body.startswith("# YOUR_SITE_NAME"))          # 页面无 title → 占位符
        self.assertIn("> YOUR_SITE_DESCRIPTION", body)                # blockquote 摘要(llmstxt 同构)
        self.assertIn("## Pages", body)
        self.assertGreaterEqual(body.count("- ["), 3)                 # ≥3 条链接过 validate
        bad = fp.build_fixes(self._live_view(dict(GOOD_PAGES, **{"/llms.txt": (200, {}, MALFORMED_LLMSTXT)})),
                             ("llms",))[0]
        self.assertIn("结构缺陷", bad["description"])                  # 缺 H1/链接<3 → 缺结构分支
        self.assertIn("缺 H1", bad["description"])
        good = fp.build_fixes(self._live_view(GOOD_PAGES), ("llms",))
        self.assertEqual(good, [])                                    # 存在且结构合规 → 不生成

    def test_schema_webiste_org_and_no_faqpage(self):
        f = fp.build_fixes(self._live_view(BROKEN_PAGES), ("schema",))[0]
        self.assertEqual((f["action"], f["file_name"]), ("snippet", "schema-jsonld.html"))
        self.assertIn('"@type": "WebSite"', f["content"])
        self.assertIn('"@type": "Organization"', f["content"])
        self.assertIn("FAQPage 不生成", f["content"])                  # 退役注释在场
        self.assertNotIn('"@type": "FAQPage"', f["content"])          # 片段本身绝不生成 FAQPage
        good = fp.build_fixes(self._live_view(GOOD_PAGES), ("schema",))
        self.assertEqual(good, [])                                    # 已有 JSON-LD → 不误报

    def test_meta_placeholders_for_all_missing(self):
        f = fp.build_fixes(self._live_view(BROKEN_PAGES), ("meta",))[0]
        self.assertEqual((f["action"], f["file_name"]), ("snippet", "meta-tags.html"))
        self.assertIn("<title>YOUR_TITLE</title>", f["content"])
        self.assertIn('content="YOUR_DESCRIPTION"', f["content"])
        self.assertIn('href="https://unit.test/"', f["content"])      # canonical 缺失→自指页面 URL
        self.assertEqual(f["content"].count('property="og:'), 3)

    def test_meta_existing_values_html_escaped(self):
        # title 经实体注入解析为 'Bad "Title" & <b>';og:title 缺失 → 用现有 title 填值且必须 escape
        danger = GOOD_HTML.replace(
            "<title>Unit Test Site Everything Present</title>",
            '<title>Bad &quot;Title&quot; &amp; &lt;b&gt;</title>').replace(
            '<meta property="og:title" content="Unit Test Site">', "")
        view = self._live_view(dict(GOOD_PAGES, **{"/": (200, {}, danger)}))
        f = fp.build_fixes(view, ("meta",))[0]
        self.assertIn('content="Bad &quot;Title&quot; &amp; &lt;b&gt;"', f["content"])
        self.assertNotIn("<b>", f["content"])                         # 原样尖括号绝不落盘
        self.assertEqual(f["content"].count("<meta"), 1)              # 只补缺失的 og:title

    def test_content_thin_vs_rich(self):
        f = fp.build_fixes(self._live_view(BROKEN_PAGES), ("content",))[0]
        self.assertEqual((f["action"], f["file_name"]), ("create", "content-rewrite.md"))
        self.assertIn("不做自动重写", f["content"])                    # 只出提纲
        self.assertIn("词数", f["content"])
        self.assertIn("审计依据", f["content"])
        good = fp.build_fixes(self._live_view(GOOD_PAGES), ("content",))
        self.assertEqual(good, [])                                    # 词数/BLUF 达标 → 不生成

    def test_live_fetch_guard_refused(self):
        def refuse(url, timeout=15):
            raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
        orig = sa.fetch
        sa.fetch = refuse
        try:
            view = fp.view_from_live(ROOT + "/")
        finally:
            sa.fetch = orig
        self.assertEqual(view["verdict"], "refused")                  # site_audit SKIP 守卫透传
        with self.assertRaises(fp.AuditRefused):
            fp.ensure_auditable(view)                                 # 拒绝生成任何修复


class EstimateTests(unittest.TestCase):
    """收益预估:Y=X+Σ(类别满分-当前得分) 封顶 100;类别满分=ai_search_health 权重×100"""

    def test_category_max_derived_from_ai_health_weights(self):
        for cat, chk in fp.CHECK_OF_CATEGORY.items():
            self.assertEqual(fp.CATEGORY_MAX[cat], round(100 * sa.AI_HEALTH_WEIGHTS[chk]))
        self.assertEqual((fp.CATEGORY_MAX["meta"], fp.CATEGORY_MAX["ai_discovery"]), (0, 0))
        self.assertEqual(sum(v for v in fp.CATEGORY_MAX.values() if v), 85)

    def test_estimate_capped_at_100(self):
        view = {"ai_health": {"score": 90, "checks": [
            {"id": "bots", "pass": False}, {"id": "llms_txt", "pass": False},
            {"id": "freshness", "pass": False}, {"id": "semantic_html", "pass": False},
            {"id": "content_length", "pass": False}, {"id": "bluf", "pass": False}]}}
        fixes = [fp.FixItem(c, "d", "c", c + ".txt", "create")
                 for c in ("robots", "llms", "schema", "meta", "content", "ai_discovery")]
        est = fp.estimate(view, fixes)
        self.assertEqual(est["before"], 90)
        self.assertEqual(est["after"], 100)       # 90+40+15+15+15=175 → 封顶 100
        self.assertEqual(est["gain"], 10)         # 实际增量按封顶后计
        self.assertIn("robots:+40", est["breakdown"])

    def test_estimate_none_without_ai_health(self):
        self.assertIsNone(fp.estimate({"ai_health": None}, []))


class PreviewTests(unittest.TestCase):
    """dry-run 预览:前 30 行 + "... (N remaining lines)";≤30 行原样"""

    def test_preview_unit_truncation(self):
        content = "\n".join("line %d" % i for i in range(1, 46))     # 45 行
        out = fp.preview(content)
        self.assertIn("line 30", out)
        self.assertNotIn("line 31", out)
        self.assertTrue(out.endswith("... (15 remaining lines)"))
        self.assertEqual(len(out.splitlines()), 31)                   # 30 行 + 1 行标记
        self.assertEqual(fp.preview("a\nb\nc").splitlines(), ["a", "b", "c"])


class ContractTests(unittest.TestCase):
    """FixItem 形状/校验 + CATEGORY 输出契约 + --help"""

    def test_fixitem_shape_and_validation(self):
        fx = fp.FixItem("robots", "d", "c", "robots.txt", "append")
        self.assertEqual(set(fx), {"category", "description", "content", "file_name", "action"})
        with self.assertRaises(ValueError):
            fp.FixItem("nope", "d", "c", "x.txt", "create")           # 非法类别
        with self.assertRaises(ValueError):
            fp.FixItem("robots", "d", "c", "x.txt", "overwrite")      # 非法动作
        with self.assertRaises(ValueError):
            fp.FixItem("robots", "d", "c", "../site/robots.txt", "create")   # 禁止路径写隔离目录外

    def test_all_six_fixitems_shape(self):
        orig = sa.fetch
        sa.fetch = stub_fetch(BROKEN_PAGES)
        try:
            view = fp.view_from_live(ROOT + "/")
        finally:
            sa.fetch = orig
        fixes = fp.build_fixes(view) + fp.build_fixes(view, ("ai_discovery",))
        self.assertEqual(len(fixes), 6)
        for fx in fixes:
            self.assertEqual(set(fx), {"category", "description", "content", "file_name", "action"})
            self.assertIn(fx["action"], ("create", "append", "snippet"))
            self.assertEqual(fx["file_name"], os.path.basename(fx["file_name"]))

    def test_help_lists_flags_and_categories(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "fix_plan.py"), "--help"],
                           capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
        self.assertEqual(r.returncode, 0)
        for frag in ("--url", "--audit", "--only", "--apply", "--estimate", "--json",
                     "seo-fixes", "FAQPage", "30 行"):
            self.assertIn(frag, r.stdout)
        for cat in fp.CATEGORIES:
            self.assertIn(cat, r.stdout)
        self.assertIn(", ".join(fp.CATEGORIES), r.stdout)             # 合法值列表


# ---- CLI(--audit 文件模式:离线零网络;cwd 隔离验证 --apply 只写 ./seo-fixes/) ----

def audit_payload(verdict="fail", findings=(), meta=None, ai=None, url=ROOT + "/"):
    return {"audited": 1, "critical": 0,
            "results": {url: {"verdict": verdict, "findings": list(findings),
                              "meta": meta or {}, "ai_search_health": ai}}}


BROKEN_FINDINGS = [
    {"severity": "CRITICAL", "area": "title", "message": "缺失"},
    {"severity": "CRITICAL", "area": "description", "message": "缺失"},
    {"severity": "WARN", "area": "canonical", "message": "缺失"},
    {"severity": "WARN", "area": "og", "message": "og:title 缺失"},
    {"severity": "WARN", "area": "og", "message": "og:description 缺失"},
    {"severity": "WARN", "area": "og", "message": "og:image 缺失"},
    {"severity": "WARN", "area": "schema", "message": "无 JSON-LD"},
    {"severity": "WARN", "area": "content", "message": "词数 12 <200(soft-thin)"},
    {"severity": "INFO", "area": "robots", "message": "//robots.txt 不可达"},
    {"severity": "INFO", "area": "llms.txt", "message": "//llms.txt 不可达"},
]
BROKEN_META = {"title": "", "title_len": "0 chars/60", "desc_len": "0 chars/155",
               "words": 12, "h1": 0, "jsonld": 0, "links": 0}
BROKEN_AI = {"score": 30,                                   # 0(bots)+0(llms)+15(fresh)+0(sem)+15(content)
             "bots": {"allowed": ["ChatGPT-User", "OAI-SearchBot", "Googlebot", "Google-Extended",
                                  "Perplexity-User", "Claude-User", "Claude-SearchBot"],
                      "blocked": ["PerplexityBot"]},
             "checks": [{"id": "bots", "pass": False, "detail": "被禁: PerplexityBot"},
                        {"id": "llms_txt", "pass": False, "detail": "/llms.txt 缺失/404(notice)"},
                        {"id": "freshness", "pass": True, "detail": "无 Last-Modified"},
                        {"id": "semantic_html", "pass": False, "detail": "语义标签比值 0.0%"},
                        {"id": "content_length", "pass": True, "detail": "词数 12"},
                        {"id": "bluf", "pass": False, "detail": "score 0.00(纯文本过短)"}]}


def broken_audit():
    return audit_payload(findings=BROKEN_FINDINGS, meta=BROKEN_META, ai=BROKEN_AI)


class CliAuditModeTests(unittest.TestCase):
    """CLI --audit:--only 过滤与非法值/dry-run 截断与预估/--apply 隔离写盘/refused 退出 2"""

    def run_cli(self, payload, *flags, expect_files=()):
        d = tempfile.mkdtemp(prefix="fp-cli-")
        audit_path = os.path.join(d, "audit.json")
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "fix_plan.py"),
                            "--audit", audit_path, *flags],
                           capture_output=True, text=True, encoding="utf-8", env=env,
                           cwd=d, timeout=60)
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        return r, d

    def test_only_filter_and_invalid_value(self):
        r, _ = self.run_cli(broken_audit(), "--only", "robots,llms", "--json")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual([f["category"] for f in data["fixes"]], ["robots", "llms"])
        self.assertEqual(data["estimate"]["after"], 85)               # 30+40(robots)+15(llms)
        bad, _ = self.run_cli(broken_audit(), "--only", "robots,nope")
        self.assertEqual(bad.returncode, 2)
        self.assertIn("nope", bad.stderr)
        self.assertIn(", ".join(fp.CATEGORIES), bad.stderr)           # 报错并列出合法值
        noargs = subprocess.run([sys.executable, os.path.join(SCRIPTS, "fix_plan.py")],
                                capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(noargs.returncode, 2)                        # 缺输入

    def test_dry_run_preview_truncation_and_estimate(self):
        r, d = self.run_cli(broken_audit(), "--estimate")             # 默认 dry-run,markdown
        self.assertEqual(r.returncode, 0)
        self.assertIn("# SEO Fix Plan", r.stdout)
        self.assertIn("dry-run", r.stdout)
        self.assertIn("remaining lines)", r.stdout)                   # robots 模板 >30 行被截断
        self.assertIn("Bingbot", r.stdout)                            # 前 30 行内(search 第 6 个)
        self.assertNotIn("YouBot", r.stdout)                          # 第 30 行之后被截掉
        self.assertIn("修复前 30/100 → 修复后预估 100/100", r.stdout)  # 30+40+15+15(+meta·content 0)
        self.assertEqual(os.listdir(d), ["audit.json"])               # dry-run 绝不写盘

    def test_apply_writes_only_seo_fixes_dir(self):
        r, d = self.run_cli(broken_audit(), "--apply", "--json")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertFalse(data["dry_run"])
        fixes_dir = os.path.join(d, "seo-fixes")
        self.assertEqual(set(os.listdir(d)), {"audit.json", "seo-fixes"})   # 只写隔离目录
        written = {os.path.basename(p) for p in data["applied_files"]}
        self.assertEqual(written, {"robots.txt", "llms.txt", "schema-jsonld.html",
                                   "meta-tags.html", "content-rewrite.md"})
        self.assertEqual(set(os.listdir(fixes_dir)), written)
        with open(os.path.join(fixes_dir, "meta-tags.html"), encoding="utf-8") as f:
            meta_html = f.read()
        self.assertEqual(meta_html, data["fixes"][3]["content"])      # 落盘内容与 FixItem 一致
        self.assertIn('content="YOUR_DESCRIPTION"', meta_html)
        self.assertIn("<title>YOUR_TITLE</title>", meta_html)

    def test_audit_refused_no_fixes_exit_2(self):
        refused = audit_payload(verdict="refused", findings=[
            {"severity": "SKIP", "area": "fetch guard",
             "message": "response too small / likely challenge page (HTTP 403); refusing to audit"}])
        r, _ = self.run_cli(refused, "--json")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["fixes"], [])           # 不生成任何修复
        self.assertIn("fetch guard", r.stderr)
        r2, d2 = self.run_cli(refused, "--apply")
        self.assertEqual(r2.returncode, 2)
        self.assertEqual(os.listdir(d2), ["audit.json"])              # --apply 也不写盘


if __name__ == "__main__":
    unittest.main(verbosity=1)
