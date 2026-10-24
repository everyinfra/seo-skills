# 审计规则目录 · Structured Data

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### Structured Data(19 条,权重 5%)

没有 JSON-LD/microdata/RDFa=fail(只有 microdata 或 RDFa=warn;site_audit 只数 JSON-LD,缺则 `[WARN] schema`);JSON-LD 语法:部分坏 warn、全坏 fail;缺 @type:部分缺 warn、全缺 fail;必填字段缺=fail、推荐字段缺=warn;Article 必填 headline/author/datePublished,推荐 image/publisher/dateModified/description/mainEntityOfPage;BreadcrumbList(非首页,**≥2 个 itemListElement**)=warn;FAQPage 每个 Question 须 name+acceptedAnswer.text=fail;LocalBusiness 须 name/address/telephone/geo;Organization 须 name/logo/sameAs;Product 须 offers(price/priceCurrency/availability);Review 须 itemReviewed/author/reviewRating;VideoObject 须 name/thumbnailUrl/uploadDate(时长 ISO 8601 如 PT1M30S);WebSite SearchAction 含 `{search_term_string}`=warn。**实体图六查已吸收于 [entity-signal-checklist.md](../entity-signal-checklist.md) 与 [validation-guide.md](../validation-guide.md)**:entity-id(@id 绝对)/rating-scope(AggregateRating 不在 legal/account URL 且 ratingValue 可见)/entity-conflict(一 @id 两 logo/两电话)/entity-dangling(publisher/author/isPartOf 的 @id 须在爬取中声明)/entity-type-drift(同 @id 跨页同 @type)/entity-split(同名组织不挂两 @id)。

**解释层(8 条;ID 未公布原文的按家族命名法推得并标 [待核];第四批补实体图六查 3 条,细则深读见 [entity-signal-checklist.md](../entity-signal-checklist.md))**

#### sd-jsonld-missing
- 名称/类型: 缺 JSON-LD(源表 ID `schema-present`) —— warning · 优先级 low · 输出 WARN(site_audit 现行 `[WARN] schema: 无 JSON-LD`;原版源表:三种载体都没有=fail,只有 microdata/RDFa=warn)
**这意味(what)**: 页面没有任何 `<script type="application/ld+json">` 结构化数据。
**为什么(why)**: 结构化数据帮助 Google 理解页面并带来富结果资格;没有证据表明它独立提升 AI 引用(口径见 [geo-evidence.md](../../content/geo-evidence.md))。缺信号类:不惩罚,只放弃一层机器可读性,故 low。
**触发(trigger)**: 原版:无 JSON-LD、microdata、RDFa(`typeof`)任一即 fail;只有后两者 warn;Open Graph 不算。site_audit 只数 `ld+json` 节点,无则 warn。
**不修的条件(caveat)**: schema 不(直接)影响排名,然而决定富结果资格,所以一般建议至少配全站级 Organization+页面主类型。但登录墙内页/纯工具页可不配。
**修复(fix)**: 按页面类型配最小集(全站 Organization,文章 Article,产品 Product——各类型必填见 sd-required-fields 家族);模板化生成,勿手拼 JSON。
**关联(seealso)**: sd-json-syntax;[schema-templates.md](../schema-templates.md)、[validation-guide.md](../validation-guide.md)

#### sd-json-syntax
- 名称/类型: JSON-LD 语法坏/缺 @type(源表 ID `schema-valid`、`schema-type`) —— issue · 优先级 high · 输出 CRITICAL/WARN(源表现行:部分块坏或缺 @type=warn,全部坏或全缺=fail)
**这意味(what)**: ld+json 内容不是合法 JSON(尾逗号/单引号/未转义引号),或解析成功但缺 @type。
**为什么(why)**: 语法坏的块无法被解析,等于没写,且多数 CMS 不报错,坏块能潜伏数月;缺 @type 则引擎无法路由到任何类型校验,注解同样悬空。这是"坏信号"档:存在但残缺比没有更隐蔽,语法坏判 fail。
**触发(trigger)**: 1) 每个 ld+json 块做 JSON.parse:部分失败 warn、全部失败 fail;2) 解析成功但无 @type:部分缺 warn、全缺 fail。
**不修的条件(caveat)**: 语法错误不产生负面排名信号(只是白写),然而它是静默失效——没有任何报错渠道,所以一般建议 CI 里对全部 ld+json 做 JSON.parse 断言;修复本身无豁免。
**修复(fix)**: 用 JSON.stringify 生成而非手写模板拼接;补 @type;上线前过 Rich Results Test 类校验器。
**关联(seealso)**: sd-jsonld-missing、sd-required-fields;[validation-guide.md](../validation-guide.md)

#### sd-required-fields [待核 ID]
- 名称/类型: 类型必填字段家族(源表 ID `schema-required-fields`、`schema-article`、`schema-faq`、`schema-product` 等) —— issue/warning · 优先级 high(fail 档)/low(warn 档) · 输出 CRITICAL/WARN(源表现行:缺必填=fail,缺推荐=warn)
**这意味(what)**: 已部署的 schema 缺该类型的必填字段。源表口径照抄(工具约定,宽于 Google:Google 的 Article 与 Organization 没有必填属性,LocalBusiness 只要求 name 与 address,[Article](https://developers.google.com/search/docs/appearance/structured-data/article)、[Organization](https://developers.google.com/search/docs/appearance/structured-data/organization)、[LocalBusiness](https://developers.google.com/search/docs/appearance/structured-data/local-business)):Article 必填 headline/author/datePublished(缺则 fail),推荐 image/publisher/dateModified/description/mainEntityOfPage(缺则 warn);LocalBusiness 须 name/address/telephone/geo;Organization 须 name/logo/sameAs;Review 须 itemReviewed/author/reviewRating;VideoObject 须 name/thumbnailUrl/uploadDate(时长 ISO 8601 如 PT1M30S);Product 须 offers(price/priceCurrency/availability);FAQPage 每个 Question 须 name+acceptedAnswer.text(`schema-faq` 固定 fail)。
**为什么(why)**: 富结果与实体理解按"类型+必填"判资格:缺字段=该类型功能整体失效(Product 无 offers 则无价格类资格)。缺必填判 fail 是"半残标记比缺失更浪费"的取舍。**注意 FAQPage 在此仅是对既有标记的结构校验**——Google 的 FAQ 富结果自 2026-05-07 起不再展示,相应文档已于 2026-06-15 删除([更新日志](https://developers.google.com/search/updates),核对 2026-10-21);不要为 SERP 展示新增这类标记,真问答页用 QAPage(口径见 [deprecated-signals.md](../deprecated-signals.md) 第一节)。
**触发(trigger)**: 按类型逐字段断言(清单照抄源表);缺必填走 fail 档,缺推荐走 warn 档。
**不修的条件(caveat)**: 缺必填不惩罚,然而该类型的机器理解整体落空,所以一般建议补齐或删类型。但 Organization 的 sameAs 在社交资产确实少时可先上子集、后补字段。
**修复(fix)**: 对照 [schema-templates.md](../schema-templates.md) 每类型最小集补齐;数据源缺字段时模板应跳过该类型而非输出空壳。
**关联(seealso)**: sd-json-syntax;[schema-templates.md](../schema-templates.md)、[entity-signal-checklist.md](../entity-signal-checklist.md)

#### sd-breadcrumblist
- 名称/类型: BreadcrumbList(源表 ID `schema-breadcrumb`) —— opportunity · 优先级 low · 输出 WARN(源表现行 warn;非首页,≥2 个 itemListElement,JSON-LD、RDFa、microdata 均可)
**这意味(what)**: 非首页页面缺 BreadcrumbList,或已有但 itemListElement <2 个。
**为什么(why)**: 面包屑 schema 让桌面结果以层级路径替代裸 URL;2025-01-23 起移动结果不再显示面包屑,只显示域名,桌面仍支持该标记([公告](https://developers.google.com/search/blog/2025/01/simplifying-breadcrumbs))。它也是站内层级的机器可读声明。缺了不影响排名,本套件把它当 opportunity 排低优先级。
**触发(trigger)**: 1) 非首页无 BreadcrumbList 即 warn;2) 有但 itemListElement <2 即 warn;首页不需要面包屑。
**不修的条件(caveat)**: 面包屑 schema 不影响排名,然而影响 SERP 展示形态,所以一般建议有真实面包屑 UI 的页面配同源 schema。但扁平站(全站一层)没有层级可表达,硬造两级反而是错。
**修复(fix)**: 面包屑 UI 与 schema 用同一数据源生成;每级 name 与目标页 title 呼应;末级指当前页。
**关联(seealso)**: sd-required-fields;[schema-templates.md](../schema-templates.md)

#### sd-searchaction
- 名称/类型: WebSite SearchAction(源表 ID `schema-website-search`) —— opportunity · 优先级 insight · 输出 WARN(源表现行 warn、权重 8;target 须含 {search_term_string})
**这意味(what)**: 站点缺 WebSite+SearchAction 标记,或 potentialAction 的 target 模板没含字面 {search_term_string} 占位符。
**为什么(why)**: Google 自 2024-11-21 起在全球移除 sitelinks 搜索框;现存标记不报错、无需删除;WebSite 结构化数据仍用于站点名称([公告](https://developers.google.com/search/blog/2024/10/sitelinks-search-box),核对 2026-10-21)。本条只剩标记卫生意义,原版仍按 warn 计分,本套件排最低优先级。
**触发(trigger)**: WebSite 类型的 potentialAction target URL 模板须含字面 {search_term_string};缺失或占位符变形即 warn(原版)。
**不修的条件(caveat)**: 对 Google 已无展示收益,不必新增;存量标记可留。注意与 url-search-indexed 不矛盾:搜索功能要真实可用,搜索**结果页**要 noindex——一个对用户,一个对索引。
**修复(fix)**: WebSite schema 配 SearchAction,target 用真实搜索 URL+{search_term_string};搜索结果页模板加 noindex。
**关联(seealso)**: url-search-indexed;[schema-templates.md](../schema-templates.md)

#### sd-entity-reference [待核 ID](源表 ID `schema-entity-id` + `schema-entity-dangling`)
- 名称/类型: 实体引用完整性(@id 形态+悬空引用) —— issue/warning · 优先级 high · 输出 WARN(源表:entity-id @id 绝对;entity-dangling: publisher/author/isPartOf 的 @id 须在爬取中声明;档位未单列[待核])
**这意味(what)**: 实体的 @id 不是绝对 URL,或页面引用的实体 @id(publisher/author/isPartOf)在整站爬取中从未被任何页面声明——悬空引用。
**为什么(why)**: @id 是实体图的节点主键:绝对 URL 形态让它可跨页跨源稳定合并;悬空引用(指了没人声明的 @id)让 author/publisher 连不上具体 Person/Organization,实体消歧退回按名字猜——同名不同人就此混淆。六查的一号位:id 体系错,后面五查全部失真。
**触发(trigger)**: 1) @id 值非绝对 URL(含 scheme)即触发;2) 出向引用的 @id 在爬取全集中无对应声明节点即 dangling(两档分型[待核])。
**不修的条件(caveat)**: 单页审计只能判 @id 形态,dangling 需 crawl 全集;指向外部权威实体(Wikidata @id)是推荐做法,不算 dangling——"爬取中声明"应含已知外部实体源[口径待核]。
**修复(fix)**: @id 用站内稳定绝对 URL(https://site/#organization);声明与引用两侧用同一模板变量;人/组织实体挂 Wikidata sameAs 作外部锚。
**关联(seealso)**: sd-entity-consistency、eeat-author-expertise;[entity-signal-checklist.md](../entity-signal-checklist.md)

#### sd-entity-consistency [待核 ID](源表 ID `schema-entity-conflict` + `schema-entity-type-drift` + `schema-entity-split`)
- 名称/类型: 实体一致性(conflict/type-drift/split) —— issue/warning · 优先级 high · 输出 WARN/CRITICAL(源表:entity-conflict 一 @id 两 logo/两电话;entity-type-drift 同 @id 跨页同 @type;entity-split 同名组织不挂两 @id;分档未单列[待核];仅 crawl 模式)
**这意味(what)**: 同一实体在站内自相矛盾:一个 @id 挂两个 logo/两个电话(conflict);同 @id 在不同页面是不同 @type——组织页是 Organization、文章页变 Person(type-drift);同名组织拆成两个 @id(split)。
**为什么(why)**: 实体图的全部价值取决于一致性:引擎按 @id 合并属性,冲突值要么随机取一要么降低实体置信度;type 漂移让节点身份不稳;split 把同一组织的信任信号(外链/评价/资质)摊薄到两个幽灵实体。三条是同一病(模板各自为政)的三张化验单,与 eeat-nap-consistency 的可见层判定互为表里。
**触发(trigger)**: ⛏ crawl 聚合:1) 同 @id 的 logo/telephone 值 >1 即 conflict;2) 同 @id 的 @type 集合 >1 即 drift;3) 同名(name 归一化)组织的 @id >1 即 split。
**不修的条件(caveat)**: 合法多值场景除外:同组织多电话(总机+售后)是真数据——conflict 的属性白名单按源表 logo/电话口径[待核];多子品牌同名应加后缀区分而非共用 name。
**修复(fix)**: Organization/Person 属性单一数据源(CMS 站点信息表)全站注入;@type 与 @id 定死在模板常量;品牌子体用独立 name+独立 @id。
**关联(seealso)**: sd-entity-reference、eeat-nap-consistency、sd-rating-scope;[entity-signal-checklist.md](../entity-signal-checklist.md)

#### sd-rating-scope [待核 ID](源表 ID `schema-rating-scope`)
- 名称/类型: 评分作用域错配 —— issue · 优先级 high · 输出 CRITICAL/WARN(源表:AggregateRating 不在 legal/account URL 且 ratingValue 可见;分档未单列[待核])
**这意味(what)**: AggregateRating 挂错了地方:出现在法律页/账户页等无评分语境的 URL,或 schema 声明了 ratingValue 但页面渲染后看不见对应评分(暗评)。
**为什么(why)**: 评分是本地/电商富结果与实体信任的硬信号,也是结构化数据滥用重灾区:对"看不见的评分"(schema 有、页面无),Google 要求不标记页面上看不到的内容;结构化数据人工处置会让页面失去富结果资格,不影响该页在网页搜索里的排名([结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies),核对 2026-10-21);legal/account URL 上的评分则是全站 footer schema 带评分类的模板泄漏。两轴口径:主动错配(评分挂错页/暗评)是坏信号,排 high。
**触发(trigger)**: 1) URL 属 legal/account 类(路径词表[待核])却含 AggregateRating 即触发;2) 有 ratingValue 声明但渲染后页面无可见评分文本/星标即触发(可见性判定口径[待核])。
**不修的条件(caveat)**: 站点级 AggregateRating(组织整体评分)在首页/关于页展示可见即可;Review/AggregateRating 分层数据必须真实——刷出来的评分是负信号不是增益。
**修复(fix)**: 评分 schema 只挂在有可见评分的产品/店铺页;数据源接真实评价系统;legal/account 模板剥离评分块;资格用富结果测试类工具复验。
**关联(seealso)**: sd-entity-consistency、eeat-trust-signals;[validation-guide.md](../validation-guide.md)、[schema-examples.md](../schema-examples.md)
