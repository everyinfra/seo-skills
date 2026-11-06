#!/usr/bin/env python3
"""source_map:线上 URL → 该改的源文件。

期望值来自 RQ-229 例 4 的盲标(labels_example4.json:没看过 source_map 的子代理读 everyinfra 源码逐条追到
title 所在文件,2026-11-05)。这里把那几类页面缩成最小样本:每条注释写对应的是哪条真实标注、真实踩过的坑。
"""
import os
import shutil
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
import source_map as S  # noqa: E402


def site(files):
    d = tempfile.mkdtemp(prefix="sm_test_")
    for path, text in files.items():
        p = os.path.join(d, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
    return d


class SourceMapTests(unittest.TestCase):
    def tearDown(self):
        for d in getattr(self, "_dirs", []):
            shutil.rmtree(d, ignore_errors=True)

    def repo(self, files):
        d = site(files)
        self._dirs = getattr(self, "_dirs", []) + [d]
        return S.Repo(d)

    def map1(self, repo, url, anchors):
        return S.map_urls(repo, [url], 0.7, lambda u: anchors)[0]

    def test_content_dir_named_build_is_not_skipped(self):
        # 标注 #10 /en/build/amazon-review-pipeline → web/content/en/build/articles.ts。
        # 旧代码按子串跳过「build/」,把 content/en/build/ 整个漏掉。
        r = self.repo({
            "web/app/en/build/[slug]/page.tsx": "import { A } from '@/content/en/build/articles';\n",
            "web/content/en/build/articles.ts": 'export const A = [{"slug": "amazon-review-pipeline", '
                                                '"title": "Amazon Review API: From Product Links to Issue Lists"}];\n',
            "web/tsconfig.json": "{}",
        })
        self.assertIn("web/content/en/build/articles.ts", r.files())
        res = self.map1(r, "https://x.com/en/build/amazon-review-pipeline",
                        {"title": "Amazon Review API: From Product Links to Issue Lists · Acme",
                         "h1": "Amazon Review API: From Product Links to Issue Lists"})
        self.assertEqual(res["best"], "web/content/en/build/articles.ts")
        self.assertTrue(res["actionable"])

    def test_site_suffix_template_does_not_win(self):
        # 标注 #2 /es/partners/power-bi → es.md。全站共用的 `${title} · 站名` 模板会套上任何页面,不能抢第一。
        r = self.repo({
            "web/app/es/partners/[slug]/page.tsx": "import { t } from '../../../../content/blog/locale';\n",
            "web/content/blog/locale.ts": "export const t = (x: string) => `${x} · Acme Engine`;\n",
            "web/content/partners/power-bi/es.md": "---\ntitle: Power BI y Acme: datos de redes sociales\n"
                                                   "description: Conecta Power BI con datos limpios de redes sociales.\n---\n",
        })
        res = self.map1(r, "https://x.com/es/partners/power-bi",
                        {"title": "Power BI y Acme: datos de redes sociales · Acme Engine",
                         "description": "Conecta Power BI con datos limpios de redes sociales."})
        self.assertEqual(res["best"], "web/content/partners/power-bi/es.md")

    def test_templated_chinese_title(self):
        # 标注 #3 /xiaohongshu-api → web/content/zh-CN/platform-seo.ts:标题由模板拼出,原文在仓库里搜不到。
        r = self.repo({
            "web/app/(zh)/[slug]/page.tsx": "import { zhTitle } from '@/content/zh-CN/platform-seo';\n",
            "web/content/zh-CN/platform-seo.ts": 'const ITEMS = { xiaohongshu: ["笔记", "评论", "用户"] };\n'
                                                 "export const zhTitle = (name: string, xs: string[]) => "
                                                 "`${name}爬虫 API:${xs.join('、')}数据采集`;\n",
        })
        res = self.map1(r, "https://x.com/xiaohongshu-api",
                        {"title": "小红书爬虫 API:笔记、评论、用户数据采集 · Acme 引擎"})
        self.assertEqual(res["best"], "web/content/zh-CN/platform-seo.ts")

    def test_locale_page_prefers_same_locale_file(self):
        # 标注 #6 /es/blog/... → web/content/es/blog/articles.ts,不是英文版或中文生成物。
        r = self.repo({
            "web/app/es/blog/[slug]/page.tsx": "import { ES } from '@/content/es/blog/articles';\n",
            "web/content/es/blog/articles.ts": 'export const ES = [{"slug": "place-id", '
                                              '"title": "Deduplicación de ubicaciones en Google Maps"}];\n',
            "web/content/en/blog/articles.ts": 'export const EN = [{"slug": "place-id", '
                                              '"note": "Deduplicación de ubicaciones en Google Maps (es)"}];\n',
        })
        res = self.map1(r, "https://x.com/es/blog/place-id",
                        {"title": "Deduplicación de ubicaciones en Google Maps · Acme"})
        self.assertEqual(res["best"], "web/content/es/blog/articles.ts")

    def test_entity_only_match_is_not_actionable(self):
        # 标注 #5 /en/similarweb-api/competitors:标题「SimilarWeb Competitors API」只由 URL 实体词拼成,
        # 另一个文件里恰好出现同名短语。这种证据不够动手,只能列候选。
        r = self.repo({
            "web/app/en/[slug]/[action]/page.tsx": "export default function P() {}\n",
            "web/content/en/capability-guides.ts": 'export const G = "SimilarWeb Competitors guide";\n',
        })
        res = self.map1(r, "https://x.com/en/similarweb-api/competitors",
                        {"title": "SimilarWeb Competitors API · Acme", "h1": "SimilarWeb Competitors API"})
        self.assertFalse(res["actionable"])

    # ---- RQ-229 例 4 留出集(h1–h4,独立代理标注)上错过的几类。文件内容是 everyinfra origin/main 的真实片段
    #      (2026-11-06,删去无关行),锚点是线上页面当天抓到的原文。----

    ZH_API_DOCS = (
        "const zhJoin = (platform: string, action: string) =>\n"
        "  `${platform}${/[A-Za-z0-9)）]$/.test(platform) && /^[\\u4e00-\\u9fff]/.test(action) ? \" \" : \"\"}${action}`;\n"
        "export const API_DOCS_ZH = {\n"
        "  metaTitle: (f) => ZH_CAPABILITY_META_TITLES[`${f.platformId}.${f.actionId}`] ?? "
        "`${zhJoin(f.platform, f.action)}爬虫 API`,\n"
        "  metaDescription: (f) => {\n"
        "    const shape = !f.list ? \"返回单个对象\" : f.pageSize ? `每次返回一页 ${f.pageSize} 条`\n"
        "      : f.maxLimit ? `返回列表，单次最多 ${f.maxLimit} 条` : \"返回列表\";\n"
        "    const what = note ?? `${shape}，含 ${f.fields.join(\"、\")}${f.fieldCount > f.fields.length ? "
        "` 等 ${f.fieldCount} 个字段` : \"\"}。`;\n"
        "    const text = `${zhJoin(f.platform, f.action)}爬虫 API：${what}${f.price ? `${f.price}，` : \"\"}失败与空结果不扣费。`;\n"
        "    return text;\n"
        "  },\n"
        "};\n")
    PLATFORMS_HEAD = ("/* 自动生成：python3 web/scripts/generate-platforms.py\n"
                      "   数据来自 gateway/public/social.py；展示元数据来自 web/lib/platform-metadata.json。手改会被覆盖。 */\n")

    def test_capability_title_name_in_guide_is_data_not_wording(self):
        # 留出 h3 /soundcloud-api/track → web/content/zh-CN/api-docs.ts。标题「SoundCloud 单曲详情爬虫 API」由
        # api-docs.ts 的模板拼出,「SoundCloud 单曲详情」是平台表里的名字;能力指南的正文恰好提到这个名字,
        # 旧代码把指南排第一还标了「可以动手」。
        r = self.repo({
            "web/app/(zh)/[slug]/[action]/page.tsx": 'import { CapabilityPage, capabilityMetadata } from "@/lib/api-docs/page";\n',
            "web/lib/api-docs/page.tsx": 'import { docsCopy } from "./copy";\n'
                                         'import { GUIDES } from "@/content/zh-CN/capability-guides";\n'
                                         'import { PLATFORMS } from "@/lib/platforms";\n',
            "web/lib/api-docs/copy.ts": 'import { API_DOCS_ZH } from "@/content/zh-CN/api-docs";\n',
            "web/content/zh-CN/api-docs.ts": self.ZH_API_DOCS,
            "web/content/zh-CN/capability-guides.ts":
                'export const GUIDES = {\n  "soundcloud.track": {\n    intro: "SoundCloud 单曲详情按曲目 `url` 读取一首曲目：'
                '标题、描述 `text`、流派 `genre`、标签 `tags`、时长、发布时间，以及播放量 `play_count`、点赞数、评论数、'
                '转发数、下载数 `download_count`。",\n    returns: "返回单个对象；主要字段见下表。",\n  },\n};\n',
            "web/lib/platforms.ts": self.PLATFORMS_HEAD + 'export const PLATFORMS = [{"id": "soundcloud", "name": "SoundCloud", '
                                    '"actions": [{"id": "track", "label": "单曲详情"}]}];\n',
            "web/scripts/generate-platforms.py": "# 生成 web/lib/platforms.ts\n",
        })
        res = self.map1(r, "https://everyinfra.com/soundcloud-api/track", {
            "title": "SoundCloud 单曲详情爬虫 API · EveryInfra 万有引擎",
            "description": "SoundCloud 单曲详情爬虫 API：返回单个对象，含 title、text、genre 等 22 个字段。"
                           "$1.39 / 千次，失败与空结果不扣费。",
            "og_title": "SoundCloud 单曲详情爬虫 API · EveryInfra 万有引擎",
            "h1": "SoundCloud 单曲详情 API",
            "p": "单曲详情：返回单个对象；主要字段 id、url、title、text、genre、tags。"})
        self.assertEqual(res["best"], "web/content/zh-CN/api-docs.ts")

    ES_API_DOCS = (
        "export const apiTitleHeadEs = (action: string, platform: string) => {\n"
        "  const a = action.toLowerCase(), p = platform.toLowerCase();\n"
        "  if (a.endsWith(` de ${p}`)) return `API de ${action}`;\n"
        "  if (p.startsWith(`${a} `)) return `API de ${lowerFirstSpanish(platform)}`;\n"
        "  return `API de ${action} de ${platform}`;\n"
        "};\n"
        "export const API_DOCS_ES = {\n"
        "  metaTitle: (f) => CAPABILITY_META_TITLE_ES[`${f.platformId}.${f.actionId}`]?.(f)\n"
        "    ?? apiTitleHeadEs(lowerFirstSpanish(f.action), SHORT_PLATFORM_ES[f.platformId] ?? f.platform),\n"
        "  metaDescription: (f) => {\n"
        "    const shape = !f.list ? \"un objeto\" : f.pageSize ? `hasta ${f.pageSize} filas por página`\n"
        "      : f.maxLimit ? `hasta ${f.maxLimit} filas por llamada` : \"una lista de filas\";\n"
        "    const tail = `${f.price ? `${f.price}; ` : \"\"}las llamadas fallidas o vacías no se cobran.`;\n"
        "    const head = apiTitleHeadEs(lowerFirstSpanish(f.action), SHORT_PLATFORM_ES[f.platformId] ?? f.platform);\n"
        "    return `${head}: ${shape}. ${tail}`;\n"
        "  },\n"
        "  pageTitle: (platform, action) => apiTitleHeadEs(action, platform),\n"
        "};\n")

    def test_spanish_capability_title_beats_blog_quoting_the_name(self):
        # 留出 h4 /es/linkedin-api/profile_search → web/content/es/api-docs.ts。标题是 apiTitleHeadEs 拼的;
        # 西语博客(不在这页的 import 链里)正文里写过「perfiles de LinkedIn」,旧代码让博客抢了第一。
        r = self.repo({
            "web/app/es/[slug]/[action]/page.tsx": 'import { CapabilityPage, capabilityMetadata } from "@/lib/api-docs/page";\n',
            "web/lib/api-docs/page.tsx": 'import { docsCopy } from "./copy";\nimport { PLATFORMS } from "@/lib/platforms";\n'
                                         'import { buildPlatformSpanish } from "@/content/es/platform";\n'
                                         'import { ROUTE_UI_ES } from "@/content/es/route-ui";\n'
                                         'import { captchaEs } from "@/content/es/captcha";\n'
                                         'import { mcpEs } from "@/content/es/mcp-server";\n',
            "web/lib/api-docs/copy.ts": 'import { API_DOCS_ES } from "@/content/es/api-docs";\n',
            "web/content/es/api-docs.ts": self.ES_API_DOCS,
            # 同一条 import 链里还有几份 `API de ${name}` 模板(真实行):旧代码的标题模板命中被它们摊薄
            "web/content/es/platform.ts": "export const buildPlatformSpanish = (name) => ({\n    title: `API de ${name}`,\n"
                                          "      title2: `Cómo usar la API de ${name}`,\n});\n",
            "web/content/es/route-ui.ts": "export const ROUTE_UI_ES = {\n  apiName: (name: string) => `API de ${name}`,\n};\n",
            "web/content/es/captcha.ts": "export const captchaEs = (name, type) => ({\n"
                                         "    breadcrumb: { home: \"Inicio\", captcha: \"API de CAPTCHA\", current: name }, "
                                         "title: `API de ${name}`,\n});\n",
            "web/content/es/mcp-server.ts": "export const mcpEs = (p, f) => [\n"
                                            "        { label: `API de ${p.name}`, href: `/${f.slug}-api` },\n];\n",
            "web/content/es/blog/articles.ts":
                'export const ARTICLES = [{"text": "La pregunta viene de un hilo de Reddit en r/apify. Quien preguntaba '
                'usaba un actor de perfiles de LinkedIn (4 USD por 1.000) y leía solo de 8 a 10 perfiles al día. '
                'Las llamadas fallidas o vacías no se cobran."}];\n',
            "web/lib/platforms.ts": self.PLATFORMS_HEAD + 'export const PLATFORMS = [{"id": "linkedin", "name": "LinkedIn", '
                                    '"actions": [{"id": "profile_search", "label_es": "Búsqueda de perfiles"}]}];\n',
            "web/scripts/generate-platforms.py": "# 生成 web/lib/platforms.ts\n",
        })
        res = self.map1(r, "https://everyinfra.com/es/linkedin-api/profile_search", {
            "title": "API de búsqueda de perfiles de LinkedIn · EveryInfra",
            "description": "API de búsqueda de perfiles de LinkedIn: hasta 100 filas por llamada. $0.56 por 1.000 "
                           "solicitudes; las llamadas fallidas o vacías no se cobran.",
            "og_title": "API de búsqueda de perfiles de LinkedIn · EveryInfra",
            "h1": "API de Búsqueda de perfiles de LinkedIn"})
        self.assertEqual(res["best"], "web/content/es/api-docs.ts")

    def test_generated_platform_table_is_data_template_is_the_source(self):
        # 留出 h2 /weibo-api → web/content/zh-CN/platform-seo.ts。「微博」「博文、用户、热搜」来自生成的平台表,
        # 旧代码把生成器排第一。该改标题措辞的是模板;生成器和数据真源配在 combo 里。
        r = self.repo({
            "web/app/(zh)/[slug]/page.tsx": 'import { zhPlatformTitle, zhPlatformDescription } from "@/content/zh-CN/platform-seo";\n'
                                           'import { PLATFORMS } from "@/lib/platforms";\n',
            "web/content/zh-CN/platform-seo.ts":
                "const spaced = (name: string) => (/[A-Za-z0-9)]$/.test(name) ? `${name} ` : name);\n"
                "export function zhPlatformTitle(name: string, items: readonly string[]): string {\n"
                "  const join = (xs: readonly string[]) => `${xs.join(\"、\")}${/[A-Za-z0-9]$/.test(xs[xs.length - 1] ?? \"\") ? \" \" : \"\"}`;\n"
                "  return firstThatFits([\n"
                "    ...shrinking(items).flatMap((xs) => [`${spaced(name)}爬虫 API：${join(xs)}数据采集`, "
                "`${spaced(name)}爬虫 API：${join(xs)}数据`]),\n"
                "    `${spaced(name)}爬虫 API`,\n  ], fitsZhTitle);\n}\n"
                "export function zhPlatformDescription(name, items, price, about) {\n"
                "  const lead = `${spaced(name)}${items.join(\"、\")}数据接口，${price ? `${price}，` : \"\"}失败不扣费。`;\n"
                "  return `${lead}${about ?? \"返回结构化 JSON，按调用计费。\"}`;\n}\n",
            "web/lib/platforms.ts": self.PLATFORMS_HEAD + 'export const PLATFORMS = [{"id": "weibo", "name": "微博", '
                                    '"tags": "博文、用户、热搜", "desc": "按关键词分别搜索微博与账号，按数字 UID 读取账号资料与'
                                    '账号发布的微博，按链接读取单条微博详情与评论，并读取热搜词条。"}];\n',
            "web/lib/platform-metadata.json": '{"weibo": {"tags": "博文、用户、热搜"}}\n',
            "web/scripts/generate-platforms.py": "# 生成 web/lib/platforms.ts\n",
            "gateway/public/social.py": 'SOCIAL = {"weibo": {"name": "微博", "desc": "按关键词分别搜索微博与账号，'
                                        '按数字 UID 读取账号资料与账号发布的微博，按链接读取单条微博详情与评论，并读取热搜词条。"}}\n',
        })
        res = self.map1(r, "https://everyinfra.com/weibo-api", {
            "title": "微博爬虫 API：博文、用户、热搜数据采集 · EveryInfra 万有引擎",
            "description": "微博博文、用户、热搜数据接口，每千次 $0.56 起，失败不扣费。按关键词分别搜索微博与账号，"
                           "按数字 UID 读取账号资料与账号发布的微博，按链接读取单条微博详情与评论，并读取热搜词条。",
            "og_title": "微博爬虫 API：博文、用户、热搜数据采集 · EveryInfra 万有引擎",
            "h1": "微博 API"})
        self.assertEqual(res["best"], "web/content/zh-CN/platform-seo.ts")
        self.assertIn("web/scripts/generate-platforms.py", res.get("combo", {}).get("data", []))

    def test_barrel_reexport_keeps_import_chain(self):
        # 留出 h4 /es/products/search/read → web/content/es/api-docs.ts(标题走 docsCopy("es").pageTitle)。
        # 路由 import 的 search-tool.tsx 只有一行 `export { … } from "@/lib/api-docs/line-page"`,旧代码不认
        # export-from,import 链在第一层就断了,第一名落到只管描述的 search-tool-seo.ts。
        r = self.repo({
            "web/app/es/products/search/[tool]/page.tsx":
                'import { SearchToolPage, searchToolMetadata, searchToolStaticParams } from "@/lib/i18n/native/search-tool";\n',
            "web/lib/i18n/native/search-tool.tsx":
                'export { SearchToolPage, searchToolMetadata, searchToolStaticParams } from "@/lib/api-docs/line-page";\n',
            "web/lib/api-docs/line-page.tsx": 'import { docsCopy } from "./copy";\n'
                                              'import { searchToolDescription } from "@/content/search-tool-seo";\n'
                                              '    title: docsCopy(locale).pageTitle("EverySearch", detail.label),\n',
            "web/lib/api-docs/copy.ts": 'import { API_DOCS_ES } from "@/content/es/api-docs";\n',
            "web/content/es/api-docs.ts": self.ES_API_DOCS,
            "web/content/search-tool-seo.ts":
                'export const ES = {\n  read: "API de lectura de URL: da una URL y obtén el título y el texto principal en '
                'Markdown, listo para un agente de IA; si un lector falla, prueba otro.",\n};\n',
        })
        res = self.map1(r, "https://everyinfra.com/es/products/search/read", {
            "title": "API de Lectura de páginas de EverySearch · EveryInfra",
            "description": "API de lectura de URL: da una URL y obtén el título y el texto principal en Markdown, listo "
                           "para un agente de IA; si un lector falla, prueba otro.",
            "og_title": "API de Lectura de páginas de EverySearch · EveryInfra",
            "h1": "API de Lectura de páginas de EverySearch"})
        self.assertEqual(res["best"], "web/content/es/api-docs.ts")

    def test_wording_inside_template_expression_beats_generator(self):
        # 留出 h2 /captcha/anubis → web/lib/captcha-page.ts。标题「Anubis 工作量证明网关（PoW）识别 API」:名字来自
        # 生成的 lib/captcha.ts,「识别 API」写在 captcha-page.ts 模板的 `${…}` 表达式里。旧代码把生成器排第一、标了动手。
        r = self.repo({
            "web/app/(zh)/captcha/[type]/page.tsx": 'import { pageTitle, CAPTCHA_PAGES } from "@/lib/captcha-page";\n',
            "web/lib/captcha-page.ts":
                'import { CAPTCHA } from "./captcha";\n'
                "const withSolving = (name: string) =>\n"
                "  `${name}${/[\\u2E80-\\uFFEF]$/.test(name) ? \"\" : \" \"}${name.includes(\"识别\") ? \"API\" : \"识别 API\"}`;\n"
                "export function pageTitle(p: CaptchaPage): string {\n"
                "  const base = plainText(withSolving(titleName(p)));\n"
                "  const withProxy = `${base}（需自带代理）`;\n"
                "  return p.required.includes(\"proxy\") && fitsTitle(withProxy) ? withProxy : base;\n}\n",
            "web/lib/captcha.ts": "/* 自动生成：python3 web/scripts/generate-captcha.py\n"
                                  "   数据来自 gateway/captcha/capabilities.py。手改会被覆盖。 */\n"
                                  'export const CAPTCHA = [{"type": "anubis", "entry": "Anubis 工作量证明网关（PoW）", '
                                  '"title": "Anubis 工作量证明网关（PoW）", "vendor": "Techaro — Anubis"}];\n',
            "web/scripts/generate-captcha.py": "# 生成 web/lib/captcha.ts\n",
            "gateway/captcha/capabilities.py": 'CAPS = {"anubis": {"title": "Anubis 工作量证明网关（PoW）"}}\n',
        })
        res = self.map1(r, "https://everyinfra.com/captcha/anubis", {
            "title": "Anubis 工作量证明网关（PoW）识别 API · EveryInfra 万有引擎",
            "og_title": "Anubis 工作量证明网关（PoW）识别 API · EveryInfra 万有引擎",
            "h1": "Anubis 工作量证明网关（PoW）识别 API"})
        self.assertEqual(res["best"], "web/lib/captcha-page.ts")

    def test_page_anchors_take_main_paragraph_not_consent_banner(self):
        # everyinfra 每页正文前都有一段 Cookie 说明,首段锚点不能取它。
        html = ("<html><head><title>T · Acme</title><meta name='description' content='D'></head><body>"
                "<div class='consent'><p>Our own visit statistics are always on. Analytics is enabled only with "
                "your permission.</p></div><main><h1>Heading</h1><p>List the sites a domain relates to, "
                "with category and rank for each one.</p></main></body></html>")
        a = S.page_anchors(html)
        self.assertEqual(a["title"], "T · Acme")
        self.assertTrue(a["p"].startswith("List the sites"))

    def test_static_route_and_text_agree(self):
        r = self.repo({"about/index.html": "<title>About Acme Static: who we are</title>",
                       "index.html": "<title>Acme Static home page title</title>"})
        res = self.map1(r, "http://127.0.0.1/about/", {"title": "About Acme Static: who we are"})
        self.assertEqual(res["best"], "about/index.html")
        self.assertGreaterEqual(res["confidence"], 0.9)


if __name__ == "__main__":
    unittest.main()
