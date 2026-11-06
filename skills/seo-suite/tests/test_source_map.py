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

    # ---- 留出集 holdout5(40 条,独立代理只读 everyinfra origin/main 标注,2026-11-06)上错的几类:当天新上的
    #      ja/ko/ru 页面。路由 import 的 content/<loc>/*.ts 是翻译流水线产出(头部写「Generated … Do not edit by
    #      hand」),旧代码当生成物压到 0.3,第一名落到 import 链外的博客合集、消息包或路由文件。文件是真实片段。----

    LOCALIZED_HEAD = "// Generated from content/en by the bulk localization pipeline (locale: %s). Do not edit by hand.\n"
    NATIVE_ROUTE = ('import { nativeCoreMetadata } from "@/lib/i18n/native-copy";\n'
                    'export const metadata = nativeCoreMetadata("%s", "%s");\n')

    def test_translation_output_is_the_locale_source(self):
        # holdout5 /ru/docs → web/content/ru/docs.ts。旧代码第一名给路由文件,其次是链外的 ru/blog/articles.json。
        r = self.repo({
            "web/app/ru/docs/page.tsx": self.NATIVE_ROUTE % ("ru", "docs"),
            "web/lib/i18n/native-copy.ts": 'import { buildDocsEnglish } from "@/lib/i18n/generated-content";\n',
            "web/lib/i18n/generated-content.ts": 'import * as ru from "@/content/ru/docs";\n',
            "web/content/ru/docs.ts": self.LOCALIZED_HEAD % "ru" +
                'export function buildDocsEnglish() {\n  return {\n    metadata: {\n'
                '      title: "Документация по API и настройка MCP",\n'
                '      description: "Подключитесь к EveryInfra для сбора данных, поиска, решения капчи и работы с бесплатным '
                'OpenAI-совместимым API для ИИ. Здесь описаны API, MCP, аутентификация, восстановление после сбоев, оплата '
                'и обработка ошибок.",\n    },\n    hero: {\n      title: "Документация по API и MCP EveryInfra",\n'
                '      body: "Выберите задачу в публичном каталоге. Создайте API-ключ. Затем сделайте первый вызов. В этом '
                'руководстве есть примеры запросов, настройка MCP, аутентификация, оплата и обработка ошибок.",\n    },\n  };\n}\n',
            "web/content/ru/blog/articles.json":
                '[{"slug":"mcp-errors","title":"Ошибки MCP","text":"Создайте API-ключ. Затем сделайте первый вызов. '
                'Здесь описаны API, MCP, аутентификация, восстановление после сбоев, оплата и обработка ошибок."}]\n',
        })
        res = self.map1(r, "https://everyinfra.com/ru/docs", {
            "title": "Документация по API и настройка MCP · EveryInfra",
            "description": "Подключитесь к EveryInfra для сбора данных, поиска, решения капчи и работы с бесплатным "
                           "OpenAI-совместимым API для ИИ. Здесь описаны API, MCP, аутентификация, восстановление после "
                           "сбоев, оплата и обработка ошибок.",
            "og_title": "Документация по API и настройка MCP · EveryInfra",
            "h1": "Документация по API и MCP EveryInfra",
            "p": "Выберите задачу в публичном каталоге. Создайте API-ключ. Затем сделайте первый вызов. В этом руководстве "
                 "есть примеры запросов, настройка MCP, аутентификация, оплата и обработка ошибок."})
        self.assertEqual(res["best"], "web/content/ru/docs.ts")
        self.assertEqual(res["candidates"][0]["role"], "translation")

    def test_translation_store_names_english_source_not_a_generator(self):
        # holdout5 /ru/tools → web/content/tools.i18n.ts。头部「from the English entries in tools.ts」:tools.ts 是
        # 英文原文,不是生成器。旧代码把 tools.ts 当生成器排第一还标了动手(指错还敢动手)。
        r = self.repo({
            "web/app/ru/tools/page.tsx": 'import { toolsCopyFor } from "@/content/tools";\n',
            "web/content/tools.ts": 'import { localized, type Locale } from "@/lib/i18n/locales";\n'
                                    'import { COPY_I18N } from "./tools.i18n";\n'
                                    'const COPY = {\n  zh: {\n    metadata: { title: "配合 EveryInfra 好用的工具" },\n  },\n};\n',
            "web/lib/i18n/locales.ts": "export const localized = (x) => x;\n",
            "web/content/tools.i18n.ts":
                "// Generated by the bulk localization pipeline from the English entries in tools.ts. Do not edit by hand.\n"
                'import type { ToolsPageCopy } from "./tools";\n'
                'export const COPY_I18N = {\n  "ru": {\n  metadata: {\n'
                '    title: "Инструменты, которые хорошо работают с EveryInfra",\n'
                '    description: "Инструменты, которые можно использовать вместе с EveryInfra, по сценариям: парсинг и '
                'краулинг, прокси, поиск и SEO-данные, аналитика и BI. Для каждого есть ссылка на сайт.",\n  },\n'
                '  title: "Инструменты, которые хорошо работают с EveryInfra",\n  },\n};\n',
        })
        res = self.map1(r, "https://everyinfra.com/ru/tools", {
            "title": "Инструменты, которые хорошо работают с EveryInfra · EveryInfra",
            "description": "Инструменты, которые можно использовать вместе с EveryInfra, по сценариям: парсинг и краулинг, "
                           "прокси, поиск и SEO-данные, аналитика и BI. Для каждого есть ссылка на сайт.",
            "h1": "Инструменты, которые хорошо работают с EveryInfra"})
        self.assertEqual(res["best"], "web/content/tools.i18n.ts")
        self.assertNotIn(("web/content/tools.ts", "generator"),
                         [(c["file"], c["role"]) for c in res["candidates"]])

    def test_translated_action_name_fills_short_template(self):
        # holdout5 /ko/mastodon-api/trending → web/content/ko/api-docs.ts。`${platform} ${words} API` 的第二格是
        # 译好的能力名「인기 급상승」(ko/platform-names.ts),URL 里只有 trending;旧代码要求每格都含 URL 词,
        # 模板套不上,第一名落到链外的韩文博客合集。
        r = self.repo({
            "web/app/ko/[slug]/[action]/page.tsx": 'import { CapabilityPage, capabilityMetadata } from "@/lib/api-docs/page";\n',
            "web/lib/api-docs/page.tsx": 'import { docsCopy } from "./copy";\n'
                                         'import { PLATFORM_NAMES } from "@/content/ko/platform-names";\n',
            "web/lib/api-docs/copy.ts": 'import { API_DOCS_KO } from "@/content/ko/api-docs";\n'
                                        'import { API_DOCS_EN } from "@/content/en/api-docs";\n',
            "web/content/ko/api-docs.ts": self.LOCALIZED_HEAD % "ko" +
                "export const apiTitleHead = (platform: string, action: string) => {\n"
                "  const last = stem(platform.split(\" \").at(-1) ?? \"\");\n"
                "  const words = action.split(\" \");\n"
                "  while (words.length && stem(words[0]) === last) words.shift();\n"
                "  return words.length ? `${platform} ${words.join(\" \")} API` : `${platform} API`;\n};\n",
            "web/content/en/api-docs.ts":
                "export const apiTitleHead = (platform: string, action: string) => {\n"
                "  const words = action.split(\" \");\n"
                "  return words.length ? `${platform} ${words.join(\" \")} API` : `${platform} API`;\n};\n",
            "web/content/ko/platform-names.ts": self.LOCALIZED_HEAD % "ko" +
                'export const ACTION_NAMES = {\n  trending_posts: "인기 급상승 게시물",\n  trending: "인기 급상승",\n};\n',
            "web/content/ko/blog/articles.json":
                '[{"slug":"fediverse","text":"Mastodon 인스턴스에서 인기 급상승 중인 게시물을 가져옵니다. 호출당 최대 100행"}]\n',
        })
        res = self.map1(r, "https://everyinfra.com/ko/mastodon-api/trending", {
            "title": "Mastodon 인기 급상승 API · EveryInfra",
            "description": "Mastodon 인기 급상승 API: 호출당 최대 100행 (text, author_name 및 author_username 포함). "
                           "요청 1,000개당 $1.39; 실패하거나 결과가 없는 호출에는 과금하지 않습니다.",
            "og_title": "Mastodon 인기 급상승 API · EveryInfra",
            "h1": "Mastodon 인기 급상승 API",
            "p": "Mastodon 인스턴스에서 인기 급상승 중인 게시물을 가져옵니다. instance로 다른 인스턴스를 지정하지 않으면 "
                 "mastodon.social을 사용합니다."})
        self.assertEqual(res["best"], "web/content/ko/api-docs.ts")

    def test_corpus_outside_import_chain_does_not_win_title(self):
        # holdout5 /ja/mcp-server → web/content/ja/mcp-server.ts。日文博客合集(路由不 import)正文里写着
        # 「リモートMCPサーバー」,旧代码让它凭标题片段排第一。链外文件打折,也不许标动手。
        r = self.repo({
            "web/app/ja/mcp-server/page.tsx": self.NATIVE_ROUTE % ("ja", "mcpServer"),
            "web/lib/i18n/native-copy.ts": 'import * as ja from "@/content/ja/mcp-server";\n',
            "web/content/ja/mcp-server.ts": self.LOCALIZED_HEAD % "ja" +
                "export function buildMcpServerEnglish(f: McpServerFacts): McpServerCopy {\n  return {\n    metadata: {\n"
                "      title: `${f.platformCount}プラットフォームのデータを扱うリモートMCPサーバー`,\n"
                '      description: "Claude、Cursor、ChatGPTなどのMCPクライアントをEveryInfraに接続して、Xiaohongshu、'
                'TikTok、Amazonのデータ収集、Web検索、CAPTCHAの解決を行えます。ローカルへのインストールは不要で、呼び出しごとの'
                '従量課金です。",\n    },\n  };\n}\n',
            "web/content/ja/blog/articles.json":
                '[{"slug":"a","text":"同じデータをClaudeやCursorで使うには、[リモートMCPサーバー](/ja/mcp-server)に接続します。'
                'ClaudeやCursorなどのMCPクライアントをEveryInfraに接続して"},'
                '{"slug":"b","text":"APIキーを作成し、[90プラットフォームのデータを扱うリモートMCPサーバー](/ja/mcp-server)を追加"}]\n',
        })
        res = self.map1(r, "https://everyinfra.com/ja/mcp-server", {
            "title": "106プラットフォームのデータを扱うリモートMCPサーバー · EveryInfra",
            "description": "Claude、Cursor、ChatGPTなどのMCPクライアントをEveryInfraに接続して、Xiaohongshu、TikTok、"
                           "Amazonのデータ収集、Web検索、CAPTCHAの解決を行えます。ローカルへのインストールは不要で、"
                           "呼び出しごとの従量課金です。",
            "og_title": "106プラットフォームのデータを扱うリモートMCPサーバー · EveryInfra"})
        self.assertEqual(res["best"], "web/content/ja/mcp-server.ts")
        blog = [c for c in res["candidates"] if c["file"] == "web/content/ja/blog/articles.json"]
        self.assertTrue(all(c["confidence"] < 0.7 for c in blog))

    def test_two_names_side_by_side_pick_the_exact_template(self):
        # holdout5 /ja/products/search/map → web/content/ja/api-docs.ts。日文标题不空格:「EverySearch」+「サイトマップ」
        # +「API」,由 `${platform}${words}API` 拼出,两格正好是 line-page 写死的「EverySearch」和 ja/market.ts 的
        # 「サイトマップ」。旧代码:译文当生成物、`${x}API` 这类粗模板人人都套得上、「サイトマップ」紧挨拉丁字母被当成
        # 不在词边界上;第一名落到只管描述的 search-tool-seo(还当成生成器标了动手)。
        r = self.repo({
            "web/app/ja/products/search/[tool]/page.tsx":
                'import { SearchToolPage, searchToolMetadata } from "@/lib/api-docs/line-page";\n',
            "web/lib/api-docs/line-page.tsx": 'import { docsCopy } from "./copy";\n'
                                              'import { searchToolLabel } from "@/content/ja/market";\n'
                                              'import { searchToolDescription } from "@/content/search-tool-seo";\n'
                                              'import { routeUi } from "@/content/ja/route-ui";\n'
                                              '    title: docsCopy(locale).pageTitle("EverySearch", detail.label),\n',
            "web/lib/api-docs/copy.ts": 'import { API_DOCS_JA } from "@/content/ja/api-docs";\n',
            "web/content/ja/api-docs.ts": self.LOCALIZED_HEAD % "ja" +
                "export const apiTitleHead = (platform: string, action: string) => {\n"
                "  const last = stem(platform.split(\" \").at(-1) ?? \"\");\n"
                "  const words = action.split(\" \");\n"
                "  while (words.length && stem(words[0]) === last) words.shift();\n"
                "  return words.length ? `${platform}${words.join(\" \")}API` : `${platform}API`;\n};\n",
            "web/content/ja/market.ts": self.LOCALIZED_HEAD % "ja" +
                'export const searchTools = {\n    map: "サイトマップ", similar: "類似ページ", suggest: "検索候補",\n};\n',
            # 同一条链里别的 `${名字}API`:能套上整句,但把两个名字塞进了一格
            "web/content/ja/route-ui.ts": self.LOCALIZED_HEAD % "ja" +
                "export const routeUi = {\n  apiName: (name: string) => `${name}API`,\n};\n",
            "web/content/search-tool-seo.ts": 'import { SEARCH_TOOL_SEO_I18N } from "./search-tool-seo.i18n";\n',
            "web/content/search-tool-seo.i18n.ts":
                "// Generated by the bulk localization pipeline from the English entries in search-tool-seo.ts. "
                "Do not edit by hand.\n"
                'export const SEARCH_TOOL_SEO_I18N = {\n  "ja": {\n    map: "サイトマップAPI：テキストを取得せずにウェブ'
                'サイトのページURLを一覧化するため高速で、1回の呼び出しで最大200件返します。まずサイトの構造を把握したいときに'
                '使えます。",\n  },\n};\n',
        })
        res = self.map1(r, "https://everyinfra.com/ja/products/search/map", {
            "title": "EverySearchサイトマップAPI · EveryInfra",
            "description": "サイトマップAPI：テキストを取得せずにウェブサイトのページURLを一覧化するため高速で、1回の呼び出しで"
                           "最大200件返します。まずサイトの構造を把握したいときに使えます。料金は1,000リクエストあたり$0.69で、"
                           "失敗した呼び出しには課金されません。",
            "og_title": "EverySearchサイトマップAPI · EveryInfra",
            "h1": "EverySearchサイトマップAPI"})
        self.assertEqual(res["best"], "web/content/ja/api-docs.ts")

    def test_article_store_read_at_runtime_counts_as_chain(self):
        # holdout5 /ru/blog/gemini-deep-research-api-mcp-social-data → web/content/ru/blog/articles.json。路由不 import
        # 它:generated-articles.ts 运行时按 locale、栏目拼路径读「articles.json」。链外打折不能误伤它:链里写着它的
        # 文件名,它又装着这页的 slug,就算链里的。
        r = self.repo({
            "web/app/ru/blog/[slug]/page.tsx":
                'import { NativeBlogArticlePage, nativeBlogArticleMetadata } from "@/lib/i18n/native/blog-article";\n',
            "web/lib/i18n/native/blog-article.tsx": 'import { blogArticle } from "@/content/blog/locale";\n'
                                                    'import { GUIDES } from "@/content/ru/guides";\n',
            "web/content/blog/locale.ts": 'import { generatedArticles } from "@/content/build/generated-articles";\n'
                                          "export const blogArticle = (a) => ({ title: a.seoTitle ?? a.title });\n",
            "web/content/build/generated-articles.ts":
                'import { existsSync, readFileSync } from "node:fs";\nimport { join } from "node:path";\n'
                "export function generatedArticles(locale, collection) {\n"
                '  const file = join(process.cwd(), "content", locale, collection, "articles.json");\n'
                '  return existsSync(file) ? JSON.parse(readFileSync(file, "utf8")) : [];\n}\n',
            "web/content/ru/guides.ts": self.LOCALIZED_HEAD % "ru" +
                'export const GUIDES = [{ title: "Gemini Deep Research API с удалённым MCP-сервером: пошаговая настройка" },'
                ' { title: "Данные соцсетей, которые можно проверить: цитаты и источники" }];\n',
            "web/content/ru/blog/articles.json":
                '[{"slug":"gemini-deep-research-api-mcp-social-data","title":"Gemini Deep Research API с удалённым '
                'MCP-сервером: данные соцсетей, которые можно проверить","description":"Gemini Deep Research API принимает '
                'удалённые MCP-серверы, но не пользовательские функции. 7 реальных вызовов API социальных данных стоили '
                '$0,0046. Настройка, цены, проверка цитат.","seoTitle":"Gemini Deep Research API + удалённый MCP: данные, '
                'которые можно проверить"}]\n',
        })
        res = self.map1(r, "https://everyinfra.com/ru/blog/gemini-deep-research-api-mcp-social-data", {
            "title": "Gemini Deep Research API + удалённый MCP: данные, которые можно проверить · EveryInfra",
            "description": "Gemini Deep Research API принимает удалённые MCP-серверы, но не пользовательские функции. 7 реальных "
                           "вызовов API социальных данных стоили $0,0046. Настройка, цены, проверка цитат.",
            "og_title": "Gemini Deep Research API с удалённым MCP-сервером: данные соцсетей, которые можно проверить · EveryInfra",
            "h1": "Gemini Deep Research API с удалённым MCP-сервером: данные соцсетей, которые можно проверить"})
        self.assertEqual(res["best"], "web/content/ru/blog/articles.json")

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
