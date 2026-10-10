#!/usr/bin/env python3
"""ai_views.py(AI 视图层生成器,Scrunch AXP 本地等价物)测试:standalone、--html 离线
fixture、零网络(tests/run_tests.py 自动发现本文件)。覆盖:净化规则逐项(噪音块移除/
语义骨架保留)、属性策略(data-*·onclick·class 剥离,aria-label 留)、meta 白名单、
img 占位、表单去交互、token 统计与 Scrunch 对标口径、markdown 层级映射、dry-run 不写盘、
--apply 隔离目录、--diff section 清单、fetch 守卫(过小/挑战页)。
用法: python3 tests/test_ai_views.py"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import ai_views as av      # noqa: E402  (需先入 SCRIPTS 路径)

# 离线 fixture:覆盖全部净化规则分支(噪音块/属性/占位/表单/meta/语义骨架)。
# style/script 内垫长注释保证 original tokens 足够大 → 缩减比为正且 < 98.9%(如实报口径)。
FIXTURE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>AI 搜索优化指南 - 示例站</title>
<meta name="description" content="如何让内容被 AI 搜索引用的完整指南,覆盖语义结构与事实密度。">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="https://unit.test/ai-seo-guide">
<link rel="stylesheet" href="/app.css">
<meta property="og:title" content="AI 搜索优化指南">
<meta property="og:description" content="让内容被 AI 引用的指南">
<meta property="og:image" content="https://unit.test/og.png">
<meta name="twitter:card" content="summary">
<script>console.log("tracking"); window.dataLayer=[];</script>
<script type="application/ld+json">{"@type":"Article"}</script>
<style>/* """ + "x" * 3000 + """ */</style>
</head>
<body>
<!-- header comment: analytics -->
<header class="site-header mega" aria-hidden="false">
<nav class="navbar" data-track="nav" aria-label="主导航">
<a class="nav-link" href="/pricing" onclick="track()">定价</a></nav></header>
<main>
<article class="post hentry" data-post-id="42">
<h1 class="title">AI 搜索优化指南</h1>
<p class="lead">这是导语段落,<strong>核心结论</strong>先行。<a href="/basics" data-track="link">基础概念</a>见另文。</p>
<img src="/chart.png" alt="AI 引用率变化图" class="lazy">
<img src="/spacer.gif">
<svg viewBox="0 0 10 10"><path d="M0 0"/></svg>
<iframe src="https://embed.unit.test/v"></iframe>
<h2 id="sec1">语义结构</h2>
<ul class="list" aria-hidden="true"><li data-item="1">语义标签保留</li><li>装饰 class 剥离</li></ul>
<h3>事实密度</h3>
<dl><dt>引用率</dt><dd>12.4%</dd></dl>
<h2 id="sec2">对比表</h2>
<table class="data"><thead><tr><th>方案</th><th>tokens</th></tr></thead>
<tbody><tr><td>原始页</td><td>123916</td></tr></tbody></table>
<form action="/subscribe" class="form"><input name="email" type="email">
<select><option>月度</option></select><textarea rows="2"></textarea>
<button type="submit" class="btn" onclick="submit()">订阅更新</button></form>
<noscript><p>请开启 JS</p></noscript>
</article>
</main>
<footer class="site-footer"><p>© 2026 示例站</p></footer>
<script src="/analytics.js"></script>
</body></html>"""


def build(fixture=FIXTURE):
    return av.build_views(fixture)


class PurifyRuleTests(unittest.TestCase):
    """净化规则逐项:script/svg/iframe/noscript/注释 移除;语义骨架保留;计数口径"""

    @classmethod
    def setUpClass(cls):
        cls.p, cls.ai_html, cls.ai_md = build()

    def test_noise_blocks_removed_semantic_kept(self):
        for gone in ("<script", "<style", "<svg", "<iframe", "<noscript", "<!--",
                     "console.log", "dataLayer", "analytics.js", "application/ld+json"):
            self.assertNotIn(gone, self.ai_html, gone)
        for kept in ("<header", "<nav", "<main", "<article", "<h1", "<h2", "<h3",
                     "<dl>", "<dt>", "<dd>", "<table", "<thead", "<th", "<td",
                     "<footer", "<ul", "<li"):
            self.assertIn(kept, self.ai_html, kept)
        # 移除计数:script×3 + style + noscript + svg + iframe + 注释 + input + select + textarea ≥ 11
        self.assertGreaterEqual(self.p.stats["removed"], 11)
        self.assertGreaterEqual(self.p.stats["kept"], 10)

    def test_attribute_policy(self):
        self.assertNotIn("class=", self.ai_html)                 # 装饰 class 全剥
        self.assertNotIn("onclick", self.ai_html)                # 内联事件删除
        self.assertNotIn("data-", self.ai_html)                  # 追踪属性 data-* 删除
        self.assertNotIn("aria-hidden", self.ai_html)            # aria-* 只留 aria-label
        self.assertIn('aria-label="主导航"', self.ai_html)
        self.assertIn('href="/pricing"', self.ai_html)           # href(链接语义)保留
        self.assertGreater(self.p.stats["attrs_stripped"], 0)

    def test_meta_whitelist(self):
        head = self.ai_html.split("</head>")[0]
        self.assertIn("<title>AI 搜索优化指南 - 示例站</title>", head)
        self.assertIn('name="description"', head)
        self.assertIn('rel="canonical"', head)
        for og in ("og:title", "og:description", "og:image"):
            self.assertIn('property="%s"' % og, head)
        self.assertNotIn("viewport", head)                       # 白名单外 meta 丢弃
        self.assertNotIn("twitter:card", head)
        self.assertNotIn("stylesheet", head)                     # 白名单外 link 丢弃
        self.assertGreater(self.p.stats["meta_dropped"], 0)

    def test_image_placeholder(self):
        self.assertIn("[image: AI 引用率变化图]", self.ai_html)   # 有 alt → 带说明占位
        self.assertIn("[image]", self.ai_html)                   # 无 alt → 裸占位
        self.assertNotIn("<img", self.ai_html)
        self.assertIn("[image: AI 引用率变化图]", self.ai_md)

    def test_forms_deinteractiveized(self):
        for gone in ("<form", "<input", "<select", "<textarea", "<button"):
            self.assertNotIn(gone, self.ai_html, gone)
        self.assertIn("订阅更新", self.ai_html)                   # 按钮文本保留
        self.assertIn("订阅更新", self.ai_md)
        self.assertNotIn("月度", self.ai_html)                   # select 内容随控件移除


class TokenAndMarkdownTests(unittest.TestCase):
    """token 统计(len//4)与 Scrunch 对标口径 / markdown 层级与元素映射"""

    @classmethod
    def setUpClass(cls):
        cls.p, cls.ai_html, cls.ai_md = build()

    def test_token_line_and_benchmark(self):
        self.assertEqual(av.estimate_tokens("a" * 40), 10)       # len//4 口径
        out = run_cli("--html", "page.html", cwd_fixture=FIXTURE)
        self.assertRegex(out.stdout, r"original: \d+ tokens → ai-view: \d+ tokens \(\d+(\.\d+)?% 缩减\)")
        self.assertIn("Scrunch", out.stdout)
        self.assertIn("98.9", out.stdout)                        # 官方实测常驻对标行
        self.assertIn("如实报", out.stdout)                      # 达不到 98.9% 时如实报
        self.assertIn("blocks: 转换 ", out.stdout)               # 转换/移除/保留计数
        self.assertIn("/ 移除 ", out.stdout)
        self.assertIn("/ 保留 ", out.stdout)

    def test_markdown_mapping(self):
        md = self.ai_md
        self.assertTrue(md.startswith("# AI 搜索优化指南 - 示例站"), md[:80])   # title→H1
        self.assertIn("## 语义结构", md)                          # h2→## 原级映射
        self.assertIn("### 事实密度", md)                         # h3→###
        self.assertIn("## AI 搜索优化指南", md)                   # 正文 h1 降为 h2(title 占 H1)
        self.assertIn("- 语义标签保留", md)                       # 列表转 md
        self.assertIn("- **引用率**: 12.4%", md)                  # dl → "dt: dd" 列表
        self.assertIn("| 方案 | tokens |", md)                    # 表格转 md
        self.assertIn("| --- |", md)
        self.assertIn("| 原始页 | 123916 |", md)
        self.assertIn("[定价](/pricing)", md)                     # 链接 [text](url)
        self.assertIn("[基础概念](/basics)", md)
        self.assertIn("**核心结论**", md)                         # strong → **


class UnitHelperTests(unittest.TestCase):
    """纯函数:slug 生成 / section 切分与 diff / h1 降级"""

    def test_make_slug(self):
        self.assertEqual(av.make_slug(url="https://x.test/blog/My-Post.html"), "my-post")
        self.assertEqual(av.make_slug(url="https://x.test/"), "x-test")     # 首页回退 host
        self.assertEqual(av.make_slug(html_path="/tmp/Page File.html"), "page-file")

    def test_heading_demote(self):
        self.assertEqual(av._heading_md("h1", True), 2)          # title 在场 → h1 降 h2
        self.assertEqual(av._heading_md("h2", True), 2)
        self.assertEqual(av._heading_md("h6", True), 6)
        self.assertEqual(av._heading_md("h1", False), 1)         # 无 title → h1 仍 H1

    def test_diff_sections_pure(self):
        old = "# T\n\n## A\na1\n\n## B\nb1\n"
        new = "# T\n\n## A\na2\n\n## C\nc1\n"
        d = av.diff_sections(old, new)
        self.assertEqual(d, {"added": ["C"], "removed": ["B"], "changed": ["A"]})


class CliFileModeTests(unittest.TestCase):
    """CLI --html 离线:dry-run 不写盘 / --apply 只写 ai-views/ 隔离目录 / --diff 清单"""

    def setUp(self):
        self.td = tempfile.mkdtemp(prefix="av-cli-")
        self.page = os.path.join(self.td, "page.html")
        with open(self.page, "w", encoding="utf-8") as f:
            f.write(FIXTURE)
        self.addCleanup(shutil.rmtree, self.td, ignore_errors=True)

    def run_cli(self, *flags):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, "ai_views.py"),
                               "--html", "page.html", *flags],
                              capture_output=True, text=True, encoding="utf-8",
                              env=env, cwd=self.td, timeout=60)

    def test_dry_run_writes_nothing(self):
        r = self.run_cli()
        self.assertEqual(r.returncode, 0)
        self.assertIn("dry-run", r.stdout)
        self.assertIn("从不部署", r.stdout)                        # 人审后部署边界常驻输出
        self.assertIn("不承诺引用提升", r.stdout)                  # llms.txt 三份实证口径
        self.assertEqual(os.listdir(self.td), ["page.html"])     # 绝不写盘

    def test_apply_writes_isolated_dir_only(self):
        r = self.run_cli("--apply")
        self.assertEqual(r.returncode, 0)
        self.assertEqual(set(os.listdir(self.td)), {"page.html", "ai-views"})   # 只写隔离目录
        vdir = os.path.join(self.td, "ai-views", "page")
        self.assertEqual(set(os.listdir(vdir)), {"ai-view.html", "ai-view.md", "stats.json"})
        with open(os.path.join(vdir, "ai-view.md"), encoding="utf-8") as f:
            md = f.read()
        self.assertTrue(md.startswith("# AI 搜索优化指南"))
        with open(os.path.join(vdir, "stats.json"), encoding="utf-8") as f:
            stats = json.load(f)
        self.assertEqual(stats["tool"], "ai_views")
        self.assertIn("manual-only", stats["deploy"])            # 从不部署写进落盘元数据
        self.assertIn("reduction_pct", stats["tokens"])
        self.assertIn("removed", stats["blocks"])

    def test_diff_added_removed_changed(self):
        self.assertEqual(self.run_cli("--apply").returncode, 0)  # v1 落盘
        v2 = FIXTURE.replace('<h2 id="sec2">对比表</h2>', "") \
                     .replace('<table class="data"><thead><tr><th>方案</th><th>tokens</th></tr></thead>'
                              '<tbody><tr><td>原始页</td><td>123916</td></tr></tbody></table>', "") \
                     .replace("<li>装饰 class 剥离</li>", "<li>装饰 class 全部剥离</li>") \
                     .replace("<h3>事实密度</h3>", '<h2 id="sec3">部署流程</h2><p>人审后部署。</p><h3>事实密度</h3>')
        with open(self.page, "w", encoding="utf-8") as f:
            f.write(v2)
        r = self.run_cli("--diff")                                # dry-run diff,不写盘
        self.assertEqual(r.returncode, 0)
        self.assertIn("+ 部署流程", r.stdout)                      # 新增 section
        self.assertIn("- 对比表", r.stdout)                        # 删除 section
        self.assertIn("~ 语义结构", r.stdout)                      # 内容变更 section
        self.assertEqual(set(os.listdir(os.path.join(self.td, "ai-views", "page"))),
                         {"ai-view.html", "ai-view.md", "stats.json"})   # diff 不覆盖旧版

    def test_diff_without_previous_version(self):
        r = self.run_cli("--diff")
        self.assertEqual(r.returncode, 0)
        self.assertIn("无上一版本", r.stdout)

    def test_json_output_shape(self):
        r = self.run_cli("--json")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["tool"], "ai_views")
        self.assertEqual(data["mode"], "dry-run")
        self.assertEqual(data["slug"], "page")
        self.assertEqual(data["deploy"], "manual-only")
        self.assertEqual(set(data["tokens"]), {"original", "ai_html", "ai_md", "reduction_pct"})
        self.assertEqual(set(data["benchmark"]), {"scrunch_pct", "ours_pct", "meets"})
        self.assertIn("meta", data)


class GuardAndUsageTests(unittest.TestCase):
    """fetch 守卫(响应过小/挑战页特征 → [SKIP] 拒产出,exit 2)+ --help 契约"""

    def _cli(self, content, *flags):
        td = tempfile.mkdtemp(prefix="av-guard-")
        self.addCleanup(shutil.rmtree, td, ignore_errors=True)
        p = os.path.join(td, "tiny.html")
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, "ai_views.py"),
                               "--html", p, *flags],
                              capture_output=True, text=True, encoding="utf-8",
                              env=env, timeout=60)

    def test_too_small_refused(self):
        r = self._cli("<html><body>tiny</body></html>")
        self.assertEqual(r.returncode, 2)
        self.assertIn("[SKIP] fetch guard", r.stdout)
        self.assertIn("too small", r.stdout)

    def test_challenge_page_refused(self):
        r = self._cli("<html><body>" + "Checking your browser before accessing. " * 20 + "</body></html>")
        self.assertEqual(r.returncode, 2)
        self.assertIn("challenge", r.stdout)

    def test_help_contract(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "ai_views.py"), "--help"],
                           capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
        self.assertEqual(r.returncode, 0)
        for frag in ("--url", "--html", "--apply", "--diff", "--json", "ai-views",
                     "人审", "从不部署", "不承诺引用提升", "98.9", "[image: alt]"):
            self.assertIn(frag, r.stdout, frag)
        # 互斥参数与缺参:exit 2
        r2 = subprocess.run([sys.executable, os.path.join(SCRIPTS, "ai_views.py")],
                            capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(r2.returncode, 2)


def run_cli(*args, cwd_fixture=None):
    """临时 cwd + fixture 文件(供 token 行断言;零网络)。"""
    td = tempfile.mkdtemp(prefix="av-tok-")
    try:
        with open(os.path.join(td, "page.html"), "w", encoding="utf-8") as f:
            f.write(cwd_fixture)
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, "ai_views.py"), *args],
                              capture_output=True, text=True, encoding="utf-8",
                              env=env, cwd=td, timeout=60)
    finally:
        shutil.rmtree(td, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
