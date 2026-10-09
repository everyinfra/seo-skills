# 页面头部标签：作用与写法

## 用途与何时读

写或审查页面 `<head>` 里和搜索、分享相关的标签时读。`<title>` 的具体写法见 [title-formulas.md](title-formulas.md)，robots.txt 见 [robots-txt-reference.md](../technical/robots-txt-reference.md)。

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

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/meta-tags-optimizer/references/meta-tag-formulas.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/meta-tags-optimizer/references/meta-tag-formulas.md)（Apache-2.0）
- 一手资料：[标题链接](https://developers.google.com/search/docs/appearance/title-link)、[摘要与 meta description](https://developers.google.com/search/docs/appearance/snippet)、[Google 支持的 meta 标签](https://developers.google.com/search/docs/crawling-indexing/special-tags)、[robots meta / X-Robots-Tag](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)、[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)、[多语言与 hreflang](https://developers.google.com/search/docs/specialty/international/localized-versions)、[Open Graph 协议](https://ogp.me/)
