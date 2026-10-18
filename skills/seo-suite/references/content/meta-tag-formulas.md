# 页面头部标签：作用与写法

## 用途与何时读

写或审查页面 `<head>` 里和搜索、分享相关的标签时读。

- `<title>` 的写法见 [title-formulas.md](title-formulas.md)；title 和 description 里用哪些词见 [question-alignment.md](question-alignment.md)。
- robots.txt 见 [robots-txt-reference.md](../technical/robots-txt-reference.md)。
- head 全量元素（推荐顺序、OG 消费矩阵、中文浏览器 meta、geo、App Links、弃用清单）见 [head-elements.md](../technical/head-elements.md)。
- 结构化数据的必填字段见 [schema-templates.md](../technical/schema-templates.md)。

## 各标签的作用

| 标签 | 作用 | 写法原则 |
|---|---|---|
| `<title>` | 结果页标题链接的主要来源之一 | 每页唯一，准确描述本页。Google 可能改写。 |
| `meta description` | 结果页摘要的候选来源之一 | 概括本页独有的内容。Google 主要从正文生成摘要；description 比正文更准确时，才可能被采用。 |
| Open Graph | 社交平台和聊天工具里的分享卡片 | OGP 规定 4 个必需属性：`og:title`、`og:type`、`og:image`、`og:url`；`og:description` 可选。`og:title` 也是 Google 生成标题链接的来源之一。 |
| robots meta / `X-Robots-Tag` | 控制编入索引和摘要：`noindex`、`nofollow`、`nosnippet`、`max-snippet` 等 | 默认值是 `index, follow`，不用写。规则冲突时取更严格的一条。页面必须能被抓取，指令才会被读到。 |
| `link rel="canonical"` | 在重复或近似重复的网址中声明首选网址 | 强信号，不是强制指令。用绝对 URL。规范页自己也写自引用 canonical。与内链、站点地图、hreflang 一致。 |
| `link rel="alternate" hreflang` | 告诉搜索引擎同一内容的各语言、地区版本 | 每个版本列出全部版本（含自身），必须互相回链，否则被忽略。URL 写完整（含 https）。可加 `x-default`。 |
| `meta keywords` | Google 不使用，对索引和排名没有影响 | 不必写，也不要用来堆词。 |

出处（核对 2026-10-18）：[标题链接](https://developers.google.com/search/docs/appearance/title-link)、[摘要](https://developers.google.com/search/docs/appearance/snippet)、[Google 支持的 meta 标签](https://developers.google.com/search/docs/crawling-indexing/special-tags)、[noindex](https://developers.google.com/search/docs/crawling-indexing/block-indexing)、[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)、[hreflang](https://developers.google.com/search/docs/specialty/international/localized-versions)、[Open Graph 协议](https://ogp.me/)。

Open Graph 的补充（Facebook [分享指南](https://developers.facebook.com/docs/sharing/webmasters/)，核对 2026-10-18）：

- `og:title` 不带站点名等品牌字样。
- 图片按 URL 缓存。换图要换 URL。
- 写上 `og:image:width` 和 `og:image:height`，首次分享时图片才能正确加载。
- 用 Sharing Debugger 查看抓到的标签和报错。

## meta description 怎么写

- 写本页独有的具体信息：适用对象、步骤或条目数量、价格、规格、作者或发布日期。Google 的例子是一本书的作者、价格和页数。
- 用买家原词概括答案和条件，见 [question-alignment.md](question-alignment.md)。
- 每页不同。大型站点可以程序生成，Google 明确鼓励；把每页特有的数据填进去，做到人能读懂、彼此不同。
- 自然语言，不堆关键词。一长串关键词说明不了内容，也更不容易被选作摘要。
- 没时间每页写，先写首页和热门页。
- Google 主要从正文生成摘要，同一页对不同搜索可能显示不同摘要。所以正文开头把要点讲清楚，比 description 更关键。
- 控制摘要：`data-nosnippet` 标记某段不进摘要（用在 `div`、`span`、`section` 上）；`max-snippet` 限制长度；`nosnippet` 完全不显示摘要，与 `data-nosnippet` 同时出现时以 `nosnippet` 为准。

出处：[摘要](https://developers.google.com/search/docs/appearance/snippet)、[精选摘要](https://developers.google.com/search/docs/appearance/featured-snippets)、[Google 支持的 meta 标签](https://developers.google.com/search/docs/crawling-indexing/special-tags)（核对 2026-10-18）。Bing 指南第 10 条：`data-nosnippet` 和 `nosnippet` 会让 Bing 不显示摘要，也可能降低 Copilot 引用的质量（[Bing 指南](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)）。

## 长度：以像素截断为准

- Google 对 meta description 没有长度上限。摘要按需截断，通常按设备宽度截断（[摘要](https://developers.google.com/search/docs/appearance/snippet)，核对 2026-10-18）。title 同理。
- 下面是工具的提示阈值，不是搜索引擎的规定：
  - 本套件：各市场的 title 和 description 上限见 [title-formulas.md](title-formulas.md)「市场差异」节（数据在 `scripts/markets.json`）。`site_audit.py` 对 description 低于 80 个计数单位报 `description-too-short`。
  - Bing Site Scan：第三方截图显示，描述不在 25–160 个字符之间时报警告（[第三方](https://ottiliestudio.com/blog/fixing-website-issues-in-bing-webmaster-tools)）。
- 中日韩字符是全角，同样宽度放下的字更少，不能照搬英文字符数。
- 检查方式：在目标地域和设备上实际搜索，或用按像素计算的预览工具，确认最重要的信息出现在截断前。

## 多语言

- 每种语言单独写，不直译。description 用本语言的买家原词（见 question-alignment.md 第三节）。
- 标点和书写习惯跟随当地，例如中文用全角括号。
- 用 hreflang 时，canonical 指向同一语言的页面；没有同语言页面时，指向最接近的替代语言（[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)）。
- hreflang 的语言码用 ISO 639-1，可加 ISO 3166-1 Alpha-2 地区码（如 `en-GB`）。只写地区码无效。不在这两个标准里的代码（如 `es-419`）Google 不支持；`EU`、`UN`、`UK` 这类保留码不起作用（[hreflang](https://developers.google.com/search/docs/specialty/international/localized-versions)，核对 2026-10-18）。
- Google 不用 hreflang 或 HTML `lang` 属性判断页面语言，而是用算法判断。

## 最小示例

```html
<head>
  <title>如何提交站点地图：格式要求与常见报错 | 示例品牌</title>
  <meta name="description" content="分步说明站点地图的格式要求、提交入口和常见报错的处理方法，适合第一次配置的站长。">
  <link rel="canonical" href="https://example.com/zh/guides/sitemap">
  <link rel="alternate" hreflang="zh" href="https://example.com/zh/guides/sitemap">
  <link rel="alternate" hreflang="en" href="https://example.com/en/guides/sitemap">
  <link rel="alternate" hreflang="x-default" href="https://example.com/en/guides/sitemap">
  <meta property="og:title" content="如何提交站点地图">
  <meta property="og:description" content="格式要求、提交入口和常见报错处理。">
  <meta property="og:image" content="https://example.com/images/sitemap-guide.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:url" content="https://example.com/zh/guides/sitemap">
  <meta property="og:type" content="article">
</head>
```

英文版页面放同样一组 hreflang，canonical 指向英文版自身。

## 交付时给出

1. 每个页面的 title、description、canonical；需要时加 robots 指令、hreflang 组和 Open Graph 组。
2. 模板生成的页面：给出模板规则和填充字段，并抽样检查生成结果。
3. 验证方式：看渲染后的 `<head>`，不只看源码模板；用 Search Console 网址检查确认 Google 看到的标签、规范网址和索引状态（需要你自己的账号）；用各社交平台的分享预览检查卡片。

## 常见误区

- 以为写了 description 就一定显示，或者以为它能直接提升排名。
- 全站共用一句 description。
- canonical 指向另一种语言的版本，或者指向会重定向、`noindex` 的网址。
- 用不同方法给同一页指定不同的 canonical（例如站点地图写一个、`rel="canonical"` 写另一个）。
- hreflang 只单向声明，没有回链。
- 页面写了 `noindex`，又被 robots.txt 屏蔽抓取，导致指令读不到。
- `og:image` 用相对路径或尺寸太小，分享时不显示。

## 市场差异：本地格式与多语言一致性

- description 长度按语言：见 title-formulas.md「市场差异」节（本套件口径）。
- 本地格式（本套件口径，`market_lint.py` 会检查部分项）：法语在 `: ; ! ?` 前加窄不换行空格，用 « » 引号；德语数字写 `1.000,00`；中文日期写「2026年10月9日」；阿拉伯语从右到左排版，数字方向统一。
- 多语言一致性（本套件口径）：`og:description` 与 description 每页唯一、内容一致；JSON-LD 里的 description 与各语言的事实卡一致，防止品牌描述在不同语言里走样。

## 审计扣分表（本套件口径）

下表把 `site_audit.py` 的发现、严重度和外部依据对齐。`health_score.py` 的主分只扣 CRITICAL；类别树的权重是 CRITICAL = 3、WARN = 1、INFO = 0.25（见 `health_score.py --help`）。先补缺失项，再调长度。

| 发现（`--export-dir` 文件名） | 严重度 | 外部依据 |
|---|---|---|
| `title-missing` | CRITICAL | Google：每页都要有 title |
| `title-too-short`（< 20 单位）、`title-too-long`（超市场上限） | WARN | 本套件口径。Google 无长度上限；Bing 指出过短的 title 可能有害 |
| `description-missing` | CRITICAL | 本套件口径，严于 Google（Google 建议至少给首页和热门页写）；Bing 指出缺失可能有害 |
| `description-too-short`（< 80 单位）、`description-too-long` | WARN | 本套件口径 |
| `h1-missing` | CRITICAL | 本套件口径。Google 要求主标题清楚，没有规定必须有 h1 |
| `h1-multiple`、`headings-skip-level` | WARN | 本套件口径。Google：标题的数量和顺序对搜索没有影响；Bing 指南要求逻辑的标题层级 |
| `canonical-relative` | CRITICAL | 本套件口径，严于 Google（相对路径受支持，但不推荐） |
| `canonical-missing` | WARN | 本套件口径。Google：canonical 不是必需的 |
| `robots-noindex` | CRITICAL | 页面不会出现在 Google 搜索结果里 |
| `og-title-missing`、`og-image-missing`、`og-description-missing`、`og-image-not-absolute` | WARN | OGP：`og:title`、`og:image` 必需；`og:description` 可选 |

主查询词有没有进 title、H1 和首段：看 `question_align.py` 的覆盖率，见 question-alignment.md 第八节。

出处：Google 关于 h1 和标题顺序的说法见 [SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)「Number and order of headings」；Bing 见指南第 13 条（核对 2026-10-18）。

## 渲染态审计警告

- 只看源码会漏掉用 JavaScript 注入的 meta 和 JSON-LD。一些 CMS 插件用 JavaScript 注入 JSON-LD，只凭 `curl` 抓到的源码就报「无 schema」，可能是误报。
- Google 建议尽量不用 JavaScript 注入或修改 meta 标签；必须用时要充分测试（[Google 支持的 meta 标签](https://developers.google.com/search/docs/crawling-indexing/special-tags)）。canonical 最好写在 HTML 源码里，不让 JavaScript 改它（[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)）。
- 可靠做法：浏览器渲染后运行 `document.querySelectorAll('script[type="application/ld+json"]')`；或在 Search Console 网址检查里看 Google 拿到的页面。

## URL、slug 与模板页

- slug 用连字符分词，不用下划线。URL 区分大小写；服务器不区分大小写时，统一成一种大小写。用受众语言的词，非 ASCII 字符按百分号编码，不要把非拉丁文字一律删掉（[URL 结构](https://developers.google.com/search/docs/crawling-indexing/url-structure)，核对 2026-10-18）。
- 子目录还是子域：Google 入门指南说，从业务角度怎么好管理就怎么选，没有说哪种排名更好。本套件默认子目录，理由是统一管理，不是「权重集中」。
- 模板页的 title 和 description 逐页唯一，列入发布前检查清单。
- 对比页、替代方案页的 URL 和标题写法见 [competitor-page-patterns.md](../research/competitor-page-patterns.md)。

## Vue / Nuxt 栈的 meta 与 JSON-LD 注入机制

来源：[vue-meta 文档](https://vue-meta.nuxtjs.org/api/)（API、SSR、Caveats 三页）与 [escaping.js 源码](https://github.com/nuxt/vue-meta/blob/master/src/shared/escaping.js)，核对 2026-10-18。

- **适用范围**：vue-meta 用于 Vue 2 和 Nuxt 2。Nuxt 2 已于 2024-06-30 停止维护（[Nuxt 博客](https://nuxt.com/blog/nuxt2-eol)）。Nuxt 3 起用 Unhead（`useHead`、`useHeadSafe`、`useSeoMeta`，[Nuxt 文档](https://nuxt.com/docs/getting-started/seo-meta)）。审计前先确认版本。
- **JSON-LD 走 `script[].json`（v2.1+）**：键和值仍会被转义，防止 XSS。旧写法是 `innerHTML` 加 `__dangerouslyDisableSanitizersByTagID` 关掉转义；官方警告这会打开 SQL 注入和 XSS 攻击面。审计时看到 `__dangerouslyDisable*` 就列为发现项，优先迁到 `json` 属性。全局的 `__dangerouslyDisableSanitizers` 影响更大，官方建议能用 ByTagID 就不用全局。
- **转义规则**：服务端把 `& < > " '` 转成 `&amp; &lt; &gt; &quot; &#x27;`；客户端改用 `&` 这类 Unicode 转义。配置键和被 disable 列出的属性不转义。数组和对象递归转义，对象的键也转义。推论：渲染后的 JSON-LD 里出现 HTML 实体是正常现象；值里出现未转义的 `<script>`，说明有代码绕过了转义。
- **vmid 覆盖**：`tagIDKeyName` 默认是 `vmid`。两个同 vmid 的标签，深层组件的覆盖浅层的。没写 vmid 的同名 meta 两个都会渲染，常见的重复 description、canonical 就是这样来的。`titleTemplate` 用 `%s` 占位。
- **once、skip、body**：`once` 只在 SSR 下可靠，组件里要配合 `skip` 和组件外的状态。`skip`（v2.1+）让标签不渲染。`body`、`pbody`（v2.1+）要框架在 SSR 时支持，否则水合出错或丢标签。
- **SSR 注入**：服务端用 `$meta().inject()` 取各部分的 `text()`。模板里用三花括号 `{{{ }}}` 防止二次转义；与 `__dangerouslyDisableSanitizersByTagID` 同用时要极其谨慎。
- **已知坑**：① 模板函数里不能直接用响应式变量（issue #322），要先赋给局部变量；症状是 title 和 meta 不随语言切换。② SSR 水合后标签重复（issue #404）：`beforeCreate` 时组件树上没有任何 `metaInfo`，所有 metaInfo 会按 ssrAppId 和 appId `1` 各渲染一次。head 里每个 meta 和 JSON-LD 恰好两份，就是这个问题。修法：挂载前让树上有 metaInfo；或者（不推荐）把 ssrAppId 设成 `1`。审计时看 `vmid` 属性判断覆盖是否生效，看重复标签判断是否命中 #404。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| title、description、canonical、og 齐全 | `python3 scripts/site_audit.py URL --market XX --json` | 通过：无 CRITICAL。失败：有 `title-missing`、`description-missing`、`canonical-relative`、`robots-noindex` 等 |
| head 元素合规 | `python3 scripts/head_check.py URL --market XX` | 通过：退出码 0。失败：退出码 1（有严重违规） |
| description 每页唯一 | 抽样：`while read u; do curl -s "$u" \| grep -io '<meta name="description"[^>]*>'; done < urls.txt \| sort \| uniq -d`（只看静态 HTML；本套件暂无专用脚本） | 通过：无输出。失败：有重复行 |
| description 含买家原词并概括答案 | `question_align.py` 的 `cov_lead`；人工读 | 通过：主查询核心词在，且能读出答案。失败：缺词、口号式描述 |
| canonical | 看渲染后的 `<head>`；网址检查的「Google 选择的规范网址」 | 通过：绝对 URL、自引用或指向同语言的规范页，与站点地图一致。失败：相对路径、指向别的语言、指向重定向或 noindex 页 |
| hreflang 互链 | `python3 scripts/hreflang_cluster.py URL1 URL2 …`（传入全部语言版本） | 通过：簇内全部互指、含自身。失败：缺回链或语言码无效 |
| robots 指令可读 | 查 robots.txt 是否屏蔽该 URL；看 meta 或响应头 | 通过：未被屏蔽，指令可见。失败：屏蔽了还想靠 noindex |
| JavaScript 注入 | 浏览器渲染后查；网址检查看 Google 拿到的页面 | 通过：关键标签在 Google 看到的 HTML 里。失败：只在源码里有或只在渲染后有，且两者不一致 |
| 分享卡片 | Facebook Sharing Debugger；各平台预览 | 通过：标题、描述、图片正确。失败：缺图、旧图、相对路径 |
| JSON-LD | `python3 scripts/schema_lint.py URL` | 通过：无报错。失败：悬空引用、占位符、与可见内容不一致 |
| vue-meta 站 | 搜源码里的 `__dangerouslyDisable`；数 head 里重复的 meta | 通过：无 disable、无重复。失败：有，按上一节修 |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。一手资料均于 2026-10-18 打开核对，链接见正文。

- 一手资料：[标题链接](https://developers.google.com/search/docs/appearance/title-link)、[摘要与 meta description](https://developers.google.com/search/docs/appearance/snippet)、[Google 支持的 meta 标签](https://developers.google.com/search/docs/crawling-indexing/special-tags)、[noindex](https://developers.google.com/search/docs/crawling-indexing/block-indexing)、[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)、[多语言与 hreflang](https://developers.google.com/search/docs/specialty/international/localized-versions)、[URL 结构](https://developers.google.com/search/docs/crawling-indexing/url-structure)、[SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)、[Bing 网站管理员指南](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)、[Open Graph 协议](https://ogp.me/)、[Facebook 分享指南](https://developers.facebook.com/docs/sharing/webmasters/)、[vue-meta 文档](https://vue-meta.nuxtjs.org/api/)、[Nuxt SEO 文档](https://nuxt.com/docs/getting-started/seo-meta)
- 第三方工具口径：[TheCraigHewitt/seomachine](https://github.com/TheCraigHewitt/seomachine)（扣分表的早期来源，已改为对齐本套件 `site_audit.py`）；[LeoYeAI/openclaw-marketing-skills](https://github.com/LeoYeAI/openclaw-marketing-skills)（渲染态审计思路）
- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/meta-tags-optimizer/references/meta-tag-formulas.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/meta-tags-optimizer/references/meta-tag-formulas.md)（Apache-2.0）
