# 结构化数据：类型选用与最小示例

> 涉及 FAQPage 或 AI 引用的判断，先读 [geo-evidence.md](../content/geo-evidence.md)。

> **schema.org v30.1（2026-09-16）**（[发布说明](https://schema.org/docs/releases.html)，核对 2026-10-18）：Product 新增 `consumerNotice`、`isOftenBoughtWith`、`specification`；Offer 新增 `itemPopularity`；ShippingRateSettings 新增 `minimumOrderValue`；PriceTypeEnumeration 新增 `MaximumRetailPrice`；PropertyValue 新增 `valueGroup`。欧盟数字产品护照：新类 `DigitalProductPassport` 和属性 `hasDigitalProductPassport`（Product/Offer）；`EnvironmentalProductDeclaration`、`DeclarationOfConformity` 是 Certification 的子类；Product 新增 `importer`、`recycledContentPercentage`、`substanceOfConcern`；Product/Organization 新增 `authorizedRepresentative`；MedicalSpecialty 新增 Ophthalmology、Audiology。以上新增词汇都在 schema.org 的 pending 区（[词汇表 JSON-LD](https://schema.org/version/latest/schemaorg-current-https.jsonld)）。Google 文档截至 2026-10-18 未提到它们：写进模板时标「词汇可用，富结果未承诺」。

## 用途

决定给哪类页面加哪种 schema、编写 JSON-LD 时读。一个页面组合多种类型的写法见 [schema-examples.md](schema-examples.md)；验证方法见 [validation-guide.md](validation-guide.md)；停用类型见 [deprecated-signals.md](deprecated-signals.md)。

## 一、基本规则

- 格式首选 JSON-LD。Google 能读 head 或 body 里的 JSON-LD，也能读 JS 动态插入的 JSON-LD（[结构化数据简介](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)）。Product 标记例外：Google 建议放进初始 HTML，JS 生成会让购物抓取更少、更不可靠（[用 JS 生成结构化数据](https://developers.google.com/search/docs/appearance/structured-data/generate-structured-data-with-javascript)）。
- **标记必须与页面可见内容一致**：不标记用户看不到的内容，不写误导性内容（[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)）。
- 只标记页面的主要内容。
- **没有真实评分，不写 `aggregateRating` 或 `review`。** 评分必须在页面上可见。实体自己控制的评价（直接写或用第三方小组件嵌入）让 LocalBusiness/Organization 页面失去评分星级资格；不得汇总其他网站的评价（[评价摘要](https://developers.google.com/search/docs/appearance/structured-data/review-snippet)）。
- 词汇合法、符合 Google 富结果资格、真的展示富结果是三件事。Google 不保证展示（通用指南原话）。
- 违规的后果是富结果资格：结构化数据人工处置只让页面失去富结果资格，不影响网页排名（通用指南，核对 2026-10-18）。
- Google 没有 AI 专用的 schema：在 AI 功能中出现，不需要特殊的 schema.org 标记（[AI 功能](https://developers.google.com/search/docs/appearance/ai-features)、[生成式 AI 优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)）。
- 必填和推荐属性以 Google [类型库](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)里对应文档为准，每次动手前现查。

## 二、常用类型何时用

状态列以 Google 类型库为准（页面最后更新 2026-10-16，核对 2026-10-18）。

| 类型 | 放在哪里 | Google 要求（核对 2026-10-18） | 注意 |
|---|---|---|---|
| Organization | 首页或「关于我们」等一个介绍页 | 无必填属性；`logo` 至少 112×112px；`name`/`alternateName` 与站点名称一致 | Google 建议放首页或单个介绍页，**不需要每页都放**（[Organization](https://developers.google.com/search/docs/appearance/structured-data/organization)）。`sameAs`：Google 定义为其他网站上介绍本组织的页面，例如社媒主页或点评页；本套件口径：只放能证明是同一实体的资料页 |
| WebSite | 首页 | 用于站点名称（[站点名称](https://developers.google.com/search/docs/appearance/site-names)） | 站点链接搜索框 2024-11-21 起停展（[公告](https://developers.google.com/search/blog/2024/10/sitelinks-search-box)），不再为它加 SearchAction |
| Article / BlogPosting / NewsArticle | 文章页 | 无必填属性；推荐 `author`（含 `name`、`url`）、`datePublished`、`dateModified`、`headline`、`image` | 日期用 ISO 8601 并带时区；图片建议多张，宽×高 ≥ 5 万像素，比例 16:9、4:3、1:1（[Article](https://developers.google.com/search/docs/appearance/structured-data/article)）。本套件口径：内容实质更新才改 `dateModified` |
| Product + Offer | 商品详情页 | 商品摘要：`name` + `review`/`aggregateRating`/`offers` 三选一；商家信息：`name`、`image`、`offers`（必须是 Offer，`price` > 0、`priceCurrency`） | Google 建议标在商品页，不标在列表页或分类页（[商品摘要](https://developers.google.com/search/docs/appearance/structured-data/product-snippet)、[商家信息](https://developers.google.com/search/docs/appearance/structured-data/merchant-listing)） |
| BreadcrumbList | 显示了面包屑的页面 | 至少 2 个 ListItem；每项 `name`、`position`、`item`（最后一项可省 `item`） | 2025-01-22 起只在桌面结果显示；Google 建议写典型用户路径，不必照搬 URL 层级（[Breadcrumb](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)） |
| SoftwareApplication | 软件或 App 介绍页 | `name`、`offers.price`（免费写 0）、`aggregateRating` 或 `review` 二选一 | 没有真实评分就拿不到该富结果；可以只作词汇描述，绝不编造（[软件应用](https://developers.google.com/search/docs/appearance/structured-data/software-app)） |
| LocalBusiness 及其子类型 | 门店页，一店一页 | `name`、`address` | 可影响知识面板里的营业时间等信息和商家轮播；用最具体的子类型（[本地商家](https://developers.google.com/search/docs/appearance/structured-data/local-business)） |
| FAQPage | 页面上真实存在的问答区 | 富结果 2026-05-07 起停展，文档 2026-06-15 删除（[更新记录](https://developers.google.com/search/updates)） | 不当作获得富结果或 AI 引用的手段；用户提交问答的页面用 QAPage |
| HowTo | — | 2023-09-13 起桌面也停展（[公告](https://developers.google.com/search/blog/2023/08/howto-faq-changes)） | 步骤用有序列表写清楚 |

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
  "image": [
    "https://example.com/images/robots-check-1x1.png",
    "https://example.com/images/robots-check-4x3.png",
    "https://example.com/images/robots-check-16x9.png"
  ]
}
```

商品页的 Product（页面上没有评价，所以不写评分；满足商家信息的必填项）：

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

- 可见内容和 JSON-LD 从同一份数据生成，避免漂移。
- 按模板实施、按模板检查：同一模板的页面一起抽查。
- 交付时给出：每种页面类型用哪些 schema 类型、字段映射表（schema 字段 ← 页面数据来源）、示例 JSON-LD、验证记录。

## 五、大规模验证（分层采样 + CI 门禁 + 部署后漂移对比）

单页用 Rich Results Test 点验只适合少量页面。千页以上的站按**模板**验证：页面由模板生成，错误也由模板生成。第三方研究：Digital Applied 2026-04 对 5,000 个站做分层抽样审计，71% 部署了至少一种 schema 类型，只有 22% 所有类型都能干净通过 Rich Results Test（[原文](https://www.digitalapplied.com/blog/schema-markup-adoption-5k-site-audit-2026)，核对 2026-10-18）。「部署了」和「验证通过」是两件事。

三步闭环（本套件口径）：

1. **按模板分层采样**：`python3 scripts/monitor.py sample-keypages --per-group 10`（读 sitemap 或 `--urls 清单文件`，按 URL 模板分组，每组随机抽 N 个；`--seed` 固定可复现；默认只打印，`--write` 才写入配置）。首轮或大改后可全量；首页和带来收入的模板直接全量。
2. **schema_lint 进 CI**：对抽样清单逐个跑 `python3 scripts/schema_lint.py URL`。它检查 @id 绝对性、引用悬空、同名实体分裂、占位符黑名单、aggregateRating 范围、FAQPage 空答案、JSON 解析失败。退出码：0 = 无 CRITICAL；1 = 有 CRITICAL 或页面没有 JSON-LD；2 = URL 非法。任一页非 0 即红灯。监控侧的 CI 输出用 `python3 scripts/monitor.py diff --ci --ci-format json|junit`（任一阈值失败退出码 10）。
3. **部署后漂移对比**：部署前后各抓一轮同一批采样页，对比 JSON-LD 指纹（@type 集合 + 必填字段值）。模板级字段消失或类型漂移就是回归：先查字段映射表（第四节），再查渲染层或边缘注入（[edge-seo.md](edge-seo.md) 第四节）。

方法边界：采样给的是模板级置信，不是全页保证。

## 常见误区

- 为了拿富结果，标记页面上看不到的内容。
- 编造评分，或汇总其他网站的评分。
- 把分类列表页标成单个 Product。
- 每个组件都输出一份 Organization，而不是用 `@id` 引用（见 [schema-examples.md](schema-examples.md)）。
- 以为加了 schema，AI 就会更多地引用本站。

## 完全装载：稀有类型的 Google 必填属性与安全序列化

**稀有类型速查**（逐个核对 Google 文档，2026-10-18）。「状态」指 Google 搜索是否还用它产生展示。

| 类型 | 状态 | Google 必填属性 | 易错点 |
|---|---|---|---|
| ClaimReview | Google 搜索逐步停用（2025-06-12 公告）；Fact Check Explorer 仍支持 | `claimReviewed`、`reviewRating`、`url` | `claimReviewed` 建议少于 75 个字符（[Fact check](https://developers.google.com/search/docs/appearance/structured-data/factcheck)）；旧版本文写的「≤140 字符」没有出处 |
| Dataset | 只用于 Dataset Search，不用于 Google 搜索（2025-11-05） | `name`、`description` | 文本属性只用前 5,000 字符（[Dataset](https://developers.google.com/search/docs/appearance/structured-data/dataset)） |
| DiscussionForumPosting | 支持 | `author`、`author.name`、`datePublished`，以及 `text`/`image`/`video` 三选一 | 只写 author + datePublished 不够（[Discussion forum](https://developers.google.com/search/docs/appearance/structured-data/discussion-forum)）；2026-03-24 新增评论线程属性 |
| EmployerAggregateRating | 支持（招聘体验） | `itemReviewed`（Organization）、`ratingValue`、`ratingCount` 或 `reviewCount` 至少一个 | （[Employer rating](https://developers.google.com/search/docs/appearance/structured-data/employer-rating)） |
| ImageObject（图片元数据） | 支持（Google 图片） | `contentUrl`，加 `creator`/`creditText`/`copyrightNotice`/`license` 四选一 | （[图片元数据](https://developers.google.com/search/docs/appearance/structured-data/image-license-metadata)） |
| JobPosting | 支持 | `datePosted`、`description`、`hiringOrganization`、`jobLocation`、`title` | 漏写 `jobLocation` 很常见；纯远程岗位用 `jobLocationType: "TELECOMMUTE"` + `applicantLocationRequirements`（[Job posting](https://developers.google.com/search/docs/appearance/structured-data/job-posting)） |
| MerchantReturnPolicy | 支持 | 方案 A：`applicableCountry` + `returnPolicyCategory`（有限期限再加 `merchantReturnDays`）；方案 B：`merchantReturnLink` | 店铺统一政策挂在 Organization 的 `hasMerchantReturnPolicy` 下；单品覆盖写在 Offer 下（[退货政策](https://developers.google.com/search/docs/appearance/structured-data/return-policy)）。它在 schema.org 是独立类型，但 Google 要求嵌套 |
| ProfilePage | 支持 | `mainEntity`（Person 或 Organization） | `agentInteractionStatistic` 是推荐属性，表示该实体自己的行为计数（如发帖数、关注数），不是什么 AEO 新字段（[Profile page](https://developers.google.com/search/docs/appearance/structured-data/profile-page)） |
| Quiz（教育问答） | 支持 | `hasPart`（每张闪卡一个 Question） | 每个 Question 的 `eduQuestionType` 必须是 `Flashcard`（[Education Q&A](https://developers.google.com/search/docs/appearance/structured-data/education-qa)）；Quiz 在 schema.org pending 区 |
| VacationRental | 支持，但需要先接入 Hotel Center / 技术客户经理 | `containsPlace`（含 `occupancy`）、`identifier`、`image`（至少 8 张）、`latitude`/`longitude`（至少 5 位小数）等 | （[Vacation rental](https://developers.google.com/search/docs/appearance/structured-data/vacation-rental)） |
| ItemList 轮播 | 支持 | `itemListElement`；必须配 Course list、Movie、Recipe、Restaurant 之一 | 两种页型：摘要页 + 详情页，或单页全量（[Carousel](https://developers.google.com/search/docs/appearance/structured-data/carousel)） |
| Course（课程列表） | 支持（英文） | 每门课 `name`、`description`；至少标 3 门课 | 单课详情（Course info）2025-09-09 已删除文档（[Course list](https://developers.google.com/search/docs/appearance/structured-data/course)） |
| Event | 支持 | `name`、`startDate`、`location`（含 `address`） | 只收公众可预订、在实体场地举办的活动；线上活动属性 2025-06-05 已移除（[Event](https://developers.google.com/search/docs/appearance/structured-data/event)） |

**JSON-LD 安全序列化**：

- 标准依据：W3C JSON-LD 1.1 第 7.2 节（非规范性）要求作者避免在 HTML 内嵌脚本里出现可能被当成 comment-open（`<!--`）、script-open（`<script`）、comment-close（`-->`）、script-close（`</script`）的字符序列（[W3C](https://www.w3.org/TR/json-ld11/#restrictions-for-contents-of-json-ld-script-elements)，核对 2026-10-18）。
- 最简做法（本套件口径）：序列化后把 JSON 字符串里的每个 `<` 写成 `<`。`<` 在 JSON 里就是 `<`，解析结果不变；四种序列都以 `<` 开头或依赖前面的 `<!--`，因此全部被避开。
- 第三方实现对照：next-seo 的 `stringify` 只替换 `</script>`、`<!--`、`-->` 三种，并刻意不转义 `&`、`<`、`>`、引号，同时剔除 null 值（[源码](https://github.com/garmeeh/next-seo/blob/main/src/utils/stringify.ts)，MIT）；next-forge 把 `<`、`>`、`&` 和 U+2028/U+2029 全部转义。两种都安全。
- 反例信号：页面 JSON-LD 里出现未转义的 `</script>`：脚本被提前截断，后半段 JSON 解析失败，也有注入风险。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 必填属性 | Rich Results Test 逐模板测代表页；对照本文第二节和「完全装载」表 | 无「严重」错误 → 通过；缺必填 → 失败 |
| 可见一致 | 对照页面可见文本逐项核对 name、价格、评分、日期 | 全部能在页面上看到 → 通过 |
| 实体规则 | `python3 scripts/schema_lint.py URL` | 退出码 0 → 通过；1 或 2 → 失败 |
| Product 位置 | `curl -s URL \| grep -c 'application/ld+json'` 与渲染后对比 | Product 标记在初始 HTML → 通过；只在渲染后出现 → 记风险 |
| 已停用类型 | 对照 [deprecated-signals.md](deprecated-signals.md) | 存量标记记 Info，不当作错误；不为它们新增标记 |
| 漂移 | 部署前后对同一批 `monitor.py sample-keypages` 采样页对比 @type 集合与必填字段 | 无字段消失 → 通过 |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/schema-markup-generator/references/schema-templates.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/schema-markup-generator/references/schema-templates.md)（Apache-2.0）
- 一手资料（核对 2026-10-18）：[结构化数据简介](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)、[通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)、[类型库](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)、[文档更新记录](https://developers.google.com/search/updates)、[schema.org 发布说明](https://schema.org/docs/releases.html)、[W3C JSON-LD 1.1](https://www.w3.org/TR/json-ld11/)；各类型 Google 文档见表内链接。
- 第三方：[Digital Applied 5,000 站审计](https://www.digitalapplied.com/blog/schema-markup-adoption-5k-site-audit-2026)（2026-04）；[garmeeh/next-seo](https://github.com/garmeeh/next-seo)（MIT）。
