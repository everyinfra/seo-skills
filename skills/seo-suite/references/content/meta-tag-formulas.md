# 页面头部标签：作用与写法

## 用途与何时读

写或审查页面 `<head>` 里和搜索、分享相关的标签时读。`<title>` 的具体写法见 [title-formulas.md](title-formulas.md)，robots.txt 见 [robots-txt-reference.md](../technical/robots-txt-reference.md)；head 全量元素（推荐顺序、OG 消费矩阵、中文浏览器 meta、geo、App Links、弃用清单）见 [head-elements.md](../technical/head-elements.md)。

## 各标签的作用

| 标签 | 作用 | 写法原则 |
|---|---|---|
| `<title>` | 结果页标题链接的主要来源 | 每页唯一，准确描述本页；Google 可能改写 |
| `meta description` | 结果页摘要的候选来源之一 | 概括本页独有的内容；是否采用由 Google 按查询决定 |
| Open Graph（`og:title`、`og:description`、`og:image`、`og:url`、`og:type`） | 社交平台和聊天工具里的分享卡片 | 图片用绝对 URL 和合适尺寸；`og:title` 也是 Google 生成标题链接时可能参考的来源之一 |
| robots meta / `X-Robots-Tag` | 控制编入索引和摘要：`noindex`、`nofollow`、`nosnippet`、`max-snippet` 等 | 只在需要改变默认行为时写；页面必须能被抓取，指令才会被读到 |
| `link rel="canonical"` | 在重复或近似重复的网址中声明首选网址 | 是强信号而非强制指令；用绝对 URL；与内链、站点地图、hreflang 保持一致 |
| `link rel="alternate" hreflang` | 告诉搜索引擎同一内容的各语言、地区版本 | 每个版本列出全部版本（含自身），并且互相回链；可加 `x-default` |
| `meta keywords` | Google 不使用 | 不必写，也不要用来堆词 |

## meta description 怎么写

- 写本页独有的具体信息：适用对象、步骤或条目数量、价格区间、规格、作者或更新日期。
- 每页不同。大型站点可以用模板生成，但要把每页特有的数据填进去，而不是全站一句话。
- 自然语言，不堆关键词，不写正文里没有的承诺。
- 不必为每个页面强求：Google 经常直接从正文中选取与查询最相关的片段作摘要，所以**正文开头把要点讲清楚**同样重要。
- 不想让某段文字出现在摘要里，可用 `data-nosnippet` 标记该段；整体限制摘要长度用 `max-snippet`。

## 长度：以像素截断为准

Google 对 title 和 meta description 都没有规定字数上限，结果页按设备宽度截断，桌面和移动端不同，前面出现日期等信息时可用宽度还会变小。

下面只作经验起点，不是 Google 的规定，需要按实际显示和站点自己的数据校准：

| 文字 | title | meta description |
|---|---|---|
| 英文等拉丁字母 | 约 50–60 个字符 | 约 120–160 个字符 |
| 中文、日文、韩文 | 约 25–35 个字 | 约 60–100 个字 |

中日韩字符是全角，单字比拉丁字母宽，同样宽度能放下的字数明显更少，不能照搬英文的字符数建议。检查方式：在目标地域和设备上实际搜索，或用按像素宽度计算的预览工具，确认最重要的信息在截断前出现。

## 多语言

- 每种语言单独写，不直译；关键词按当地搜索习惯重新研究。
- 标点和书写习惯跟随当地，例如中文用全角括号。
- 每个语言版本的 canonical 指向它自己，不指向另一种语言的版本。
- hreflang 使用 ISO 639-1 语言代码，可加 ISO 3166-1 地区代码（如 `en-GB`）；只写地区不写语言是无效的。

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
  <meta property="og:url" content="https://example.com/zh/guides/sitemap">
  <meta property="og:type" content="article">
</head>
```

英文版页面放同样一组 hreflang，canonical 指向英文版自身。

## 交付时给出

1. 每个页面的 title、description、canonical；需要时加 robots 指令、hreflang 组和 Open Graph 组。
2. 模板生成的页面：给出模板规则和填充字段，并抽样检查生成结果。
3. 验证方式：查看渲染后的 `<head>`（不只看源码模板）；用 Search Console 网址检查确认 Google 看到的规范网址和索引状态，需要你自己的账号；用各社交平台的分享预览检查卡片。

## 常见误区

- 以为写了 description 就一定会显示，或者以为它能直接提升排名。
- 全站共用一句 description。
- canonical 指向另一种语言的版本，或者指向会重定向、`noindex` 的网址。
- hreflang 只单向声明，没有回链。
- 页面写了 `noindex`，却又被 robots.txt 屏蔽抓取，导致指令读不到。
- `og:image` 用相对路径或尺寸太小，分享时不显示。

## 市场差异:meta 长度与本地格式(拉平轮)

- **description 长度按语言**:日 全角 120;泰 120–155;德/西/意 150–160;印尼 **meta 前 120 字符为安全区**(移动为主);中文 60–90 字。
- **本地格式**:法语 `:;!?` 前不换行空格(U+202F 窄式标准)、« » 引号;德 `1.000,00`;中文日期 `2026年10月9日`;阿拉伯 RTL+数字方向统一。
- **多语言一致性**:og:description 与 description 每页唯一且一致(韩区硬规则);JSON-LD description 与每语言事实卡逐字一致(品牌漂移第一成因)。

## meta/内链审计扣分制与 CMS 写回(seomachine 深读 2026-10-09b)

**审计扣分表(两个评分器合并,可当 checklist 用)**:meta title 缺失 −15(落地页评分器 −35,为最高权重单项);<50 或 >60–65 字符各 −5~−10(>65 有截断风险);meta description 缺失 −15(落地页 −35);<150 或 >160–165 各 −5~−10;主关键词不在 title −10、不在 H1 −10(落地页 −15)、不在前 100 词 −10。**缺失类远重于长度微调——先补齐再调长度;字符数只是代理指标,截断判断仍以上文像素原则为准。**

**内链预算按页面类型分**:SEO 落地页 ≥2 条内链(不足 −15);**PPC 落地页内链预算为 0**(流量是付费买的,减少跳出路径);文章类在规划期就把内链分配进每节的 internal_links 清单,而不是发布后回补。

**slug 规则**:小写;去非词字符;空格/下划线→连字符;解析 URL Slug 字段时剥掉 /blog/ 前缀只留末段。

**发布写回(WordPress/Yoast 路径)**:文章 markdown 头部字段块(**Meta Title**/**Meta Description**/**Target Keyword**/**Secondary Keywords**/**URL Slug**/**Category**/**Tags**)发布时剥离正文,经 REST 写回 Yoast 三字段:seo_title、meta_description、focus_keyphrase;description 兼作 excerpt。**注意:该仓库没有独立 schema 校验模块**——结构化数据审计不在其覆盖范围,结构化方面仅有 dateModified/sitemap lastmod 随实质更新同步的原则(见 [content-refresh-playbook.md](content-refresh-playbook.md))。

## meta 改写优先级、渲染态审计与 schema 速查(openclaw 深读 2026-10-09c)

**先用 CTR 数据决定改哪页的 meta,不要全站平铺**(search-console-connect):给每个候选页查"排名位置 × 实际 CTR",对照基准——位置 1 预期 28–35%、位置 2 15–20%、位置 3 10–13%、位置 4–5 6–8%、位置 6–10 2–4%。诊断规则:**位置 1–5 但 CTR 显著低于基准 → title/description 重写是第一优先级**(查询已匹配、输在点击);位置 4–20 且月曝光 >100 → meta 对齐搜索意图后排名还有空间;每个修复给出"预估 +XX 点击/月"再排全局优先级。流量下跌诊断顺序:先定位下跌日期 → 对照算法更新时间线 → 按页、按查询对比前后 → 判断全站性(技术)还是主题性(内容)。

**on-page 检查细则**(seo-audit,与上文扣分制互补):title 逐页唯一、主关键词尽量靠前;description = 主关键词 + 明确价值主张 + 行动号召,三要素齐;常见失败是重复 title、CMS 自动生成的垃圾 description。标题结构:单 H1 且含主关键词、不跳级(H1→H3)、标题描述内容而非仅作样式。**三对齐**:title、H1、URL 指向同一主关键词;多页竞争同词(蚕食)时合并或差异化。图片:全部有 alt 且描述图片内容、描述性文件名。

**渲染态审计警告**(seo-audit 独有):`web_fetch`/`curl` 抓不到客户端注入的内容——Yoast/RankMath/AIOSEO 等插件常把 JSON-LD(有时连同 meta)用 JS 注入,静态源码里看不到,**基于源码报"无 schema"是误报**。可靠做法:浏览器渲染后跑 `document.querySelectorAll('script[type="application/ld+json"]')`,或 Rich Results Test(渲染 JS),或 Screaming Frog 导出。上文"查看渲染后的 head"同理覆盖 JS 注入的 meta。

**schema 必填字段速查**(schema-markup,补上轮"无 schema 校验模块"的缺口):

| 类型 | 必填 | 常用推荐 |
|---|---|---|
| Organization | name, url | logo, sameAs, contactPoint |
| Article/BlogPosting | headline, image, datePublished, author | dateModified, publisher, description |
| Product | name, image, offers(价格+库存) | sku, brand, aggregateRating, review |
| SoftwareApplication | name, offers | — |
| FAQPage | mainEntity(Q&A 数组) | — |
| HowTo | name, step | — |
| BreadcrumbList | itemListElement(position/name/item) | — |
| LocalBusiness / Event | name+address / name+startDate+location | — |

JSON-LD 优先,放 head 或 body 末;多类型用 `@graph` 合并为一块。格式硬规则:日期 ISO 8601、URL 全限定、枚举值精确;**schema 必须与页面可见内容一致,标记不存在的内容即违规**。验证:Rich Results Test + validator.schema.org + Search Console 增强报告。AI 面:结构化数据带来 30–40% AI 可见度提升,关键词堆砌反而 −10%(评分细节见 [citability-scoring.md](citability-scoring.md))。

**页面级 URL/模板补充**:pSEO 用子目录不用子域(权重集中);模板页 title/meta 逐页唯一要进发布前 checklist(与上文"模板生成的页面抽样检查"呼应)。对比页 URL 惯例四式:单数替代 `/alternatives/[竞品]`、复数 `/alternatives/[竞品]-alternatives`、对打 `/vs/[竞品]` 或 `/compare/`、竞品互殴 `/compare/[A]-vs-[B]`;title 直接用对应目标关键词(如"[竞品] alternative(s)"、"[你] vs [竞品]")。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/meta-tags-optimizer/references/meta-tag-formulas.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/meta-tags-optimizer/references/meta-tag-formulas.md)（Apache-2.0）
- 深读补充：[TheCraigHewitt/seomachine · data_sources/modules](https://github.com/TheCraigHewitt/seomachine)(content_scorer/landing_page_scorer/article_planner/wordpress_publisher)
- 深读补充：[LeoYeAI/openclaw-marketing-skills · skills](https://github.com/LeoYeAI/openclaw-marketing-skills)(seo-audit/search-console-connect/schema-markup/programmatic-seo/competitor-alternatives;全仓 38 技能中 14 个 SEO/内容/CRO 深读,本文件只取 meta/页面级相关)
- 一手资料：[标题链接](https://developers.google.com/search/docs/appearance/title-link)、[摘要与 meta description](https://developers.google.com/search/docs/appearance/snippet)、[Google 支持的 meta 标签](https://developers.google.com/search/docs/crawling-indexing/special-tags)、[robots meta / X-Robots-Tag](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)、[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)、[多语言与 hreflang](https://developers.google.com/search/docs/specialty/international/localized-versions)、[Open Graph 协议](https://ogp.me/)
