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

## 完全装载:14 个稀有 JSON-LD 字段清单+选型矩阵+转义规则(百仓深扫)

**稀有类型必填字段**(next-seo 组件库精读):ClaimReview(claimReviewed ≤140 字符+reviewRating+url)/Dataset(name+description)/DiscussionForumPosting(**author+datePublished**)/EmployerAggregateRating(itemReviewed+ratingValue,ratingCount 与 reviewCount 至少一)/ImageObject(**contentUrl+creator/creditText/copyrightNotice/license 至少其一**;多图用 @graph)/JobPosting(title/description/datePosted/hiringOrganization)/MerchantReturnPolicy(**独立顶层类型**;分场景运费三组 customerRemorse/itemDefect/seasonalOverride)/ProfilePage(mainEntity,含 **agentInteractionStatistic**——AEO 新字段)/Quiz(hasPart=Question[]{eduQuestionType:"Flashcard",text,acceptedAnswer})/VacationRental(**containsPlace+image 最低 8 张+经纬度**)/Carousel(ItemList,contentType∈Course|Movie|Recipe|Restaurant)。
**JSON-LD 转义五字符**(防 `</script>` 逃逸,next-forge):`<`→\u003c、`>`→\u003e、`&`→\u0026、\u2028/\u2029——任何自建模板必带;Publii 补:`JSON.stringify().replace(/</g,'\u003c')`。
**schema 选型矩阵**(maestro):Product(name/image/description/offers)/Article(headline/datePublished/author)/FAQPage(mainEntity)/Organization(name/url)/LocalBusiness(name/address/telephone)/Event(name/startDate/location);**meta keywords 2009 年起被忽略**——报告它=反模式。
**实体放置规则**(kostja94):Organization schema 最优放根布局组件每页输出(**不要只放 About 页**);@id 用稳定 URL(/#organization);首页 Organization↔WebSite 互链。

## 字段级细节:15 个稀有类型的必填/嵌套/默认值(next-seo 源码深读,2026-10-09)

读 garmeeh/next-seo 的 `src/components/*.tsx`(27 个组件)+ `src/types/*.types.ts` + `src/utils/processors.ts`,补上节摘要缺的字段级事实。**组件属性名即 schema 字段名**——用 React 组件库实现时 props 与 JSON-LD 一一对应,不用手拼 JSON。

**必填与运行时校验(组件里硬编码的行为)**:
- **ClaimReview**:必填 `claimReviewed`/`reviewRating`/`url`;`reviewRating` 是**扩展 Rating,必带 `alternateName`**(区别于普通 Rating);可选 `author`、`itemReviewed`(Claim 类型,内含 `firstAppearance`/`appearance`——字符串 URL 或 CreativeWork 对象,`firstAppearance` 单值、`appearance` 可数组)。
- **EmployerAggregateRating**:`ratingCount` 与 `reviewCount` **至少一个,否则组件直接 throw**(运行时异常,非静默);`itemReviewed` 必填且类型为 Organization(可传字符串自动包 `{@type:Organization,name}`;嵌套可带 logo/address/contactPoint/numberOfEmployees);`bestRating`/`worstRating` 可选。
- **ImageJsonLd(ImageObject)**:`contentUrl` + (creator|creditText|copyrightNotice|license)四选一,缺失时**仅 console.warn 不阻断**(与上节摘要一致的软校验);可选 `acquireLicensePage`;多图走 `images: []` → 输出 `@graph` 数组,单图平铺——两种输出结构不同,消费端解析要兼容。
- **ProfilePage**:`mainEntity` 必填(Person/Organization,字符串自动包 Person);`interactionStatistic` 与 **`agentInteractionStatistic`** 都会被规整为 InteractionCounter(后者是单值非数组);可选 `dateCreated`/`dateModified`。
- **Quiz**:三种子问题输入格式归一化为 `hasPart: Question[]`——纯字符串(问题即答案)、`{question,answer}` 对、`{text,acceptedAnswer}` 完整式;每个 Question 固定 `eduQuestionType:"Flashcard"`;可选 `about`(Thing)与 `educationalAlignment`(AlignmentObject:`alignmentType` ∈ educationalSubject|educationalLevel → `targetName`)。
- **VacationRental**:必填 `containsPlace`(Accommodation:bed/occupancy/amenityFeature/floorSize 嵌套 QuantitativeValue)、`image`(**数组处理,组件注释明示最低 8 张**)、`latitude`/`longitude`(或用 `geo:{latitude,longitude}`,两者取 geo 优先);可选 additionalType/address/aggregateRating/brand/checkinTime/checkoutTime/description/knowsLanguage(可数组)/review。
- **MerchantReturnPolicy**:两种模式互斥——**Option A 详细属性**(applicableCountry 数组化/returnPolicyCategory/merchantReturnDays/returnMethod 数组化/refundType 数组化/itemCondition 数组化/returnFees/returnShippingFeesAmount(MonetaryAmount)/restockingFee(number 或 MonetaryAmount)/returnLabelSource + customerRemorse 三件套 + itemDefect 三件套 + returnPolicySeasonalOverride 数组(startDate/endDate/returnPolicyCategory/merchantReturnDays))或 **Option B 仅 `merchantReturnLink`**(指向政策页链接)。
- **JobPosting**:必填 title/description/datePosted/hiringOrganization;**`jobLocationType` 类型系统只允许字面量 `"TELECOMMUTE"`**;`applicantLocationRequirements`(远程岗位用,可数组)、`baseSalary`(MonetaryAmount)、`directApply`(布尔)、`experienceInPlaceOfEducation`(布尔)、educationRequirements/experienceRequirements 可数组。
- **Course**:组件三态——单课(无 type 或 `type:"single"`,直接输出 Course:name+description 必填、url/provider 可选)或 `type:"list"`:urls 摘要页模式(ListItem 只含 position+url)或 courses 全量模式(ListItem.item 内嵌完整 Course)。
- **Carousel(ItemList)**:`urls`(摘要页,ListItem 只 position+url)或 `contentType`+`items`(全量页,content Type ∈ Course|Movie|Recipe|Restaurant);**Course/Movie 全量必填 name(+Movie 还必填 image)**;Restaurant 必填 name+address;position 默认 index+1 自动编号。
- **MovieCarousel**:同 Carousel 的两种模式,专用于 Movie(name+image 必填)。
- **Dataset**:必填仅 name+description;推荐 url/identifier/keywords/license/isAccessibleForFree/creator/funder/includedInDataCatalog(DataCatalog)/distribution(DataDownload)/temporalCoverage/spatialCoverage/measurementTechnique/variableMeasured/version/citation/alternateName/sameAs/hasPart/isPartOf。
- **DiscussionForumPosting**:`type` prop 默认 "DiscussionForumPosting"(可传 SocialMediaPosting 等父类);必填 **author + datePublished**;comment 数组逐条规整(Comment:author/text/datePublished);可选 creativeWorkStatus/interactionStatistic(InteractionCounter)/isPartOf/sharedContent。
- **CreativeWorkJsonLd(一族多型)**:`type` 可传 CreativeWork/Article/NewsArticle/BlogPosting/Comment/Course/Review;**headline 与 name 互斥(headline 优先)**;Article 系**缺 dateModified 时自动回落 datePublished**;Comment 专属 `text`、Course 专属 `provider`、Review 专属 `itemReviewed`+`reviewRating`(按 type 条件输出)。

**JSON-LD 安全序列化(纠正上节转义口径)**:next-seo 的 `utils/stringify.ts`(借自 google/react-schemaorg)按 W3C JSON-LD 11 规范只转义三种序列:`</script>`(不区分大小写)→`\u003C/script>`、`<!--`→`\u003C!--`、`-->`→`--\u003E`;**刻意不转义 `&`/`<`/`>`/引号**——它们在 script 内容里合法,且全量转义会破坏带查询参数的 URL;同时 replacer 会剔除 null 值。这与 next-forge 的"五字符全转义"是两种工程取舍:写自研模板时按 W3C 规范走三序列即可,`&`→`\u0026` 属于过度但无害。

**组件工程约定**:`scriptId`(script 标签 id)默认取 `scriptKey`(如 `"claimreview-jsonld"`);`nonce` 透传 CSP nonce;`data-testid` 同 id——测试与 DOM 定位都靠它。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/schema-markup-generator/references/schema-templates.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/schema-markup-generator/references/schema-templates.md)（Apache-2.0）
- 源码精读:garmeeh/next-seo `src/components/`(ClaimReview/Quiz/MerchantReturnPolicy/VacationRental/DiscussionForumPosting/Dataset/CreativeWork/Image/ProfilePage/Carousel/MovieCarousel/EmployerAggregateRating/Course/JobPosting 等 27 组件)、`src/types/common.types.ts`、`src/utils/processors.ts`、`src/utils/stringify.ts`、`src/core/JsonLdScript.tsx`(2026-10-09,MIT)
- 一手资料：[结构化数据简介](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)、[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)、[结构化数据类型库](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)、[schema.org](https://schema.org/)；各类型的 Google 文档见第二节表格中的链接。
