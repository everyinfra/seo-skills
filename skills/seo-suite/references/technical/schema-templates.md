# 结构化数据：类型选用与最小示例

> 涉及 FAQPage 或 AI 引用的判断，先读 [geo-evidence.md](../content/geo-evidence.md)。

## 用途

决定给哪类页面加哪种 schema、编写 JSON-LD 时读。一个页面组合多种类型的写法见 [schema-examples.md](schema-examples.md)，验证方法见 [validation-guide.md](validation-guide.md)。

## 一、基本规则

- 格式首选 JSON-LD，放在 head 或 body 里都可以，位置不影响权重。
- **标记必须与页面上可见的正文一致**：不标记用户看不到的内容，不写误导性的内容（见[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)）。
- 只标记页面的主要内容：页面讲的是什么，就用什么类型。
- **没有真实评分数据，不写 `aggregateRating` 或 `review`。** 评分必须来自页面上可见的真实评价；商家给自己打的评价不能用于 LocalBusiness 和 Organization 的评价富结果。
- 词汇合法、符合 Google 富结果资格、真的展示富结果是三件事；标记正确也不保证展示。
- 没有专门的「AI Schema」，加结构化数据不等于会被 AI 引用。
- 必填和推荐属性以 Google [类型库](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)中对应类型的文档和 [schema.org](https://schema.org/) 为准，每次动手前现查，不凭记忆写。

## 二、常用类型何时用

| 类型 | 放在哪里 | 何时用 | 注意 |
|---|---|---|---|
| Organization | 首页或「关于我们」页，一处即可 | 说明品牌或公司的名称、官网、logo、官方资料页 | `sameAs` 只放你控制或官方认证的资料页（见 [Organization](https://developers.google.com/search/docs/appearance/structured-data/organization)） |
| WebSite | 首页 | 声明站点名称（见[站点名称](https://developers.google.com/search/docs/appearance/site-names)） | 不要为站内搜索框富结果添加 SearchAction，Google 已[停止展示该功能](https://developers.google.com/search/blog/2024/10/sitelinks-search-box) |
| Article / BlogPosting / NewsArticle | 文章页 | 新闻、博客、指南 | 作者、发布时间、更新时间与页面显示一致；内容实质更新时才改 `dateModified`（见 [Article](https://developers.google.com/search/docs/appearance/structured-data/article)） |
| Product + Offer | 商品详情页 | 单个可购买的商品 | 价格、币种、库存与页面一致并同步更新；分类列表页不要标成单个 Product（见 [Product](https://developers.google.com/search/docs/appearance/structured-data/product)） |
| BreadcrumbList | 显示了面包屑的页面 | 面包屑可见时 | 与可见面包屑逐级一致（见 [Breadcrumb](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)） |
| SoftwareApplication | 软件或 App 介绍页 | 描述软件名称、运行平台、价格 | 按 Google 当前的[软件应用](https://developers.google.com/search/docs/appearance/structured-data/software-app)文档，该富结果要求有评分或评价；没有真实评分时可以只作词汇描述，不会获得该富结果，绝不编造 |
| LocalBusiness 及其子类型 | 门店页，一店一页 | 有实体门店或服务区域 | 名称、地址、电话、营业时间与页面及其他官方资料一致（见 [本地商家](https://developers.google.com/search/docs/appearance/structured-data/local-business)）；能用更具体的子类型就用子类型 |
| FAQPage | 页面上真实存在的问答区 | 只描述真实问答 | FAQ 富结果已停止展示，不把它当作获得富结果或 AI 优先引用的手段 |
| HowTo | — | — | HowTo 富结果 Google 已不再展示；步骤用清楚的有序列表写好即可 |

## 三、最小示例（自写）

以下每段放进一个 `<script type="application/ld+json">`，所有值都要替换成页面上真实可见的内容。

首页的 Organization：

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://example.com/#organization",
  "name": "示例品牌",
  "url": "https://example.com/",
  "logo": "https://example.com/assets/logo.png",
  "sameAs": ["https://social.example.net/example-brand"]
}
```

文章页的 BlogPosting：

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "如何核对 robots.txt 规则",
  "datePublished": "2026-03-02T09:00:00+08:00",
  "dateModified": "2026-06-18T10:30:00+08:00",
  "author": {
    "@type": "Person",
    "name": "张三",
    "url": "https://example.com/authors/zhang-san"
  },
  "image": "https://example.com/images/robots-check.png"
}
```

商品页的 Product（页面上没有展示评价，所以不写评分）：

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "示例品牌 保温杯 500ml",
  "image": "https://example.com/images/cup-500.jpg",
  "sku": "CUP-500",
  "brand": { "@type": "Brand", "name": "示例品牌" },
  "offers": {
    "@type": "Offer",
    "price": "129.00",
    "priceCurrency": "CNY",
    "availability": "https://schema.org/InStock",
    "url": "https://example.com/products/cup-500"
  }
}
```

## 四、实施与交付

- 可见内容和 JSON-LD 从同一份数据生成，避免两边内容漂移。
- 按模板实施、按模板检查：同一模板的页面一起抽查。
- 交付时给出：每种页面类型用哪些 schema 类型、字段映射表（schema 字段 ← 页面数据来源）、示例 JSON-LD、验证记录。

## 常见误区

- 为了拿富结果，标记页面上看不到的内容。
- 编造或复制别处的评分。
- 把分类列表页标成单个 Product。
- 每个页面都重复声明一整份 Organization，而不是用 `@id` 引用（见 [schema-examples.md](schema-examples.md)）。
- 以为加了 schema，AI 就会更多地引用本站。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/schema-markup-generator/references/schema-templates.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/schema-markup-generator/references/schema-templates.md)（Apache-2.0）
- 一手资料：[结构化数据简介](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)、[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)、[结构化数据类型库](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)、[schema.org](https://schema.org/)；各类型的 Google 文档见第二节表格中的链接。
