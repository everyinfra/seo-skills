# 按站型的 SEO 打法手册(八卡)

用途:接单/开局先认站型,取对应打法卡定 KPI、渠道、防死清单与 pSEO 方向。
分工:本文管「打法层」;页面类型、URL 层级与各站型深读在 [site-type-templates.md](../technical/site-type-templates.md)(互为表里,不重复);通用打法流程见 [playbooks.md](../technical/playbooks.md);pSEO 上线闸门见 [programmatic-seo-gates.md](../technical/programmatic-seo-gates.md)。
基准数据均标注来源级别与日期(官方/报告/观察/共识);报告级数字用于对标,不用作对客承诺。

## ① SaaS / 软件营销站

**页面清单(必争 URL 集)**

- 核心转化面:`/`、`/features/<功能>`、`/solutions/<行业|角色>`、`/pricing`、`/customers/<案例>`。
- 比价拦截面:`/compare/<竞品>`(vs)、`/alternatives/<竞品>`、`/vs/` 集合页。
- 生态面:`/integrations/<app>`、`/templates/<用例>`、支柱指南 + 集群文(组织法见 [topic-cluster-templates.md](../research/topic-cluster-templates.md))。

**Schema 组合**

- SoftwareApplication(name/applicationCategory/operatingSystem)+ Organization;有真实用户评分才加 aggregateRating,禁止编造。
- pricing/vs/alternatives 页 FAQPage(打 PAA 与 AI 引用);博客 Article/BlogPosting 带作者。
- 全站 BreadcrumbList;完整映射见 [schema-templates.md](../technical/schema-templates.md)。

**核心 KPI**

- 非品牌词 demo/trial 注册占比——品牌词占比升高≠SEO 增长,常是品牌广告假象。
- trial 落地页转化率:2026 报告级中位 1.5-3%、头部四分位 5%+(Stackmatix 2026-09)。
- 自然渠道 close rate:报告级 ~14.6%,对比付费搜索 5.1%、付费社交 0.9%(Flighted 2026-05)——用渠道质量差为 SEO 争取预算。
- solution 页 vs feature 页流量结构:解决方案词落在 solution 页才算对位,错配即预警。
- AI 检索线索质量:demo show rate 报告级 14.2% vs 自然 2.8%(Authoricy 2026-06,单源,谨慎引用)。

**获取策略重点**

- vs/alternatives 矩阵截获竞品品牌词——SaaS 转化最高的词群,先打头三名竞品。
- 集成页三层结构:app 单页 → pair 页(A × B)→ workflow 页;量级来自 pair/workflow 层(Zapier 范式:5000 工具生成约 5 万页,salt.agency 案例)。
- 支柱内容 + 免费工具引流;G2/Capterra/目录外链垫权威底座。

**典型死法**

- 博客海量发文无支柱集群,权重散在孤儿文,主题权威建不起来。
- 功能页打解决方案词、解决方案页打功能词——意图错配两头不收。
- vs/alternatives 页 find-replace 模板,GSC 整组 "Discovered–currently not indexed"。
- 核心内容全门禁(gated)无 SEO 可见落点,可索引面太小。
- 把品牌词流量增长当 SEO 成果汇报,预算被砍时原形毕露。

**pSEO 机会**

- 集成对 `app1 × app2` 与 `app × 用例` workflow 页。
- `行业 × 角色` 解决方案矩阵(每格要有该行业真实痛点文案与案例)。
- 模板库 `/templates/<场景>`(带下载/复制价值,天然外链资产)。

## ② 电商(DTC)

**页面清单(必争 URL 集)**

- 类目面:多级类目/PLP(`/c/<类目>/<子类目>`)、品牌页、品牌×类目页。
- 商品面:PDP(`/p/<商品>`)、变体归一后的规范 URL。
- 内容面:导购(best-of/gift guide)、尺码/材质/兼容指南、评论 UGC 页。

**Schema 组合**

- Product + Offer(price/availability/currency 三项必填)+ BreadcrumbList,全站 PDP。
- AggregateRating/Review 仅挂页内真实评论;榜单页 ItemList;指南文 Article + FAQPage。
- Merchant Center 免费清单并行——结构化数据不替代 feed,两条腿都要。

**核心 KPI**

- 品类页 vs SKU 页流量结构:头部品类页应扛主要非品牌流量,SKU 页补长尾——倒挂说明类目词全输给了亚马逊/聚合站。
- 非品牌自然收入占比(报告口径先写进合同)。
- facet 索引泄漏量:被索引的 `?filter=`/`?color=` URL 数;2026 共识级——facet 是电商第一爬虫预算杀手(DigitalApplied 2026-01)。
- 缺货排名品保留率(保留+标 availability 的比例)。
- PDP 评论覆盖率(有评论文本的 PDP 占比,养长尾与富结果)。

**获取策略重点**

- 品类页内链 + 导购内容包抄:品类词 SERP 常被 informational 榜单占据,爬梯打法见 [ecommerce-geo-ladder.md](../content/ecommerce-geo-ladder.md)。
- 数字 PR:新品测评/unboxing/礼物清单植入换外链与联盟分发。
- Google 免费 listing(Merchant Center)+ 图片搜索流量(DTC 图片占比常被低估)。

**典型死法**

- facet 组合失控,百万近重复 URL 吞掉爬虫预算,真页面反而收录慢。
- 变体各留一 URL,30 个近重复 PDP 互相蚕食。
- 缺货即 404,排名资产清零(正解:保留+标 availability;真死 SKU 301 到类目/替代品)。
- 厂商样板描述全站复制,PDP 千篇一律零增量。
- 类目页无导语文本,纯商品网格排不上;迁平台整站换 URL 无重定向表。

**pSEO 机会**

- `品牌 × 类目` 页与 `礼物场景 × 人群 × 价格`(`gifts for <person> under <price>`)。
- 兼容性页(`fits <型号>`/`for iPhone 17`)——自带真实需求分布。
- 材质/尺寸组合页;全部过 [programmatic-seo-gates.md](../technical/programmatic-seo-gates.md) 闸门,无需求组合不生成。

## ③ 媒体 / 新闻 / 内容站

**页面清单(必争 URL 集)**

- 频道面:首页、channel/section 页、topic hub(专题支柱聚合页)。
- 内容面:文章(NewsArticle 或常青 Article 分开规划)、作者实体页。
- 机器面:news sitemap、普通 sitemap、RSS;订阅/落地转化页。

**Schema 组合**

- NewsArticle/Article + NewsMediaOrganization + Person(作者,带 sameAs 指向社媒/维基)。
- 时间戳精确到秒,`dateModified` 必须真实(假新鲜度是负信号)。
- 视频报道 VideoObject;全站 BreadcrumbList 可省但频道面包屑建议保留。

**核心 KPI**

- Discover / Top Stories / 经典搜索三源流量构成:2026 报告级 Discover 占出版商自然流量 30-50%(DigitalApplied 2026-02)——单源依赖度是风险指标。
- 新稿首小时索引率与首日 CTR(新闻窗口期价值)。
- 订阅/回访/单 UV 会话深度,替代裸 PV 考核。
- 作者实体页收录率与知识面板命中数。

**获取策略重点**

- Publisher Center 收录 + news sitemap:时效内容必争 Top Stories 位。
- Discover 优化:≥1200px 宽大图、实体清晰、标题克制——2026-02 Discover 更新后标题党流量掉 30-60%(报告级)。
- 平台联合分发(Apple News/MSN)+ 社交引用回流;细则见 [discover-news-seo.md](../content/discover-news-seo.md)。

**典型死法**

- 标题党——2026-02 Discover 更新的主罚对象,整站级别的展示量萎缩。
- tag 页海量薄页,抓取预算与权重被稀释。
- 作者匿名无实体,权威度无处累积(News sitemap 也要求可归因)。
- 改版换 URL 不逐条 301,历史外链全断。
- 只追 PV 无订阅漏斗,算法一抖收入归零;通讯社稿原样转载,重复内容不收。

**pSEO 机会**

- 数据新闻库:每年更新的 "State of X 2026" 报告页,天然年更外链磁铁。
- 事件 × 地区报道模板页(重大事件的本地化角度)。
- topic hub 持续聚合旧稿吃实体词与 AI 引用。

## ④ 本地服务

**页面清单(必争 URL 集)**

- `/`、`/services/<每项服务一页>`(本地自然排名 #1 因素,Whitespark 2026)、`/locations/<城市>`。
- `城市 × 服务` 页仅在能拿出真实本地证据时做;about/team(信任面)、评价与案例页。
- 六行业(餐饮/医疗/法律/家居/教育/汽车)的合规红线与 schema 正解全表在 [site-type-templates.md](../technical/site-type-templates.md),此处不重复。

**Schema 组合**

- LocalBusiness 精确子类(Plumber/Dentist/LegalService…,主类目选错是第一负面因素)。
- SAB(服务区域业务):areaServed、不展示 streetAddress;多门店页独立 `@id` 经 `branchOf` 归一到 Organization。
- Service + FAQPage + BreadcrumbList;医疗实体禁挂 aggregateRating(富结果受限)。

**核心 KPI**

- 本地包网格排名 ARP/ATRP/SoLV 三口径同报(公式与工具见 [local-grid-ranking.md](../monitoring/local-grid-ranking.md))。
- GBP 行为量:来电、问路、预约(GBP 信号权重占本地六维的 25%)。
- 评价速度:断档 18 天即见排名下滑的案例(观察级);10 条基准线、回复率 88% 消费者在意。
- 服务页 vs 位置页流量结构;`tel:` 点击与表单提交归因。

**获取策略重点**

- GBP 运营:主类目+最多 4 个次类目、帖子、Q&A 退场后常见问题写进商家描述。
- 评价引擎:完工短信征集、不门控(违反 Google 假互动政策与 FTC)、持续回复。
- 本地链接:"best of" 榜单 + 商会/赞助/行业目录;2026-03 核心更新后实体解析更看重真实本地提及(DigitalApplied 2026-03)。

**典型死法**

- 城市×服务 doorway 页:swap 测试(换城市名仍通顺)不过=整组去索引,HVAC 案例掉 80% 排名。
- SAB 业务乱展示街道地址(违反指南),或实体店硬藏地址。
- 30+ 位置页模板复制、唯一内容 <60%(50+ 强制停线说明)。
- 评价征集三天打鱼,速度断档。
- GBP 网站链接指到最强页面(有压制自然排名的案例风险)。

**pSEO 机会**

- `服务 × 城市` 页——唯一可行模式但必须过证据闸门:真实案例/本地照片/区域实据,无证据组合不生成(闸门见 [programmatic-seo-gates.md](../technical/programmatic-seo-gates.md))。
- 门店定位器 SSR/SSG 可爬,不留 CSR 黑洞。

## ⑤ 文档 / 开发者站

**页面清单(必争 URL 集)**

- 入门面:`/docs`、quickstart、guides(任务型教程)。
- 参考面:API reference(逐参数+可复制示例)、SDK 语言页、错误码/troubleshooting 页。
- 生态面:changelog、integrations、status 页。

**Schema 组合**

- TechArticle(教程)+ HowTo(步骤型)+ FAQPage + BreadcrumbList + Organization。
- 侧栏目录与 URL 层级一致;版本化时明确规范版本,旧版本 noindex 策略写死。

**核心 KPI**

- AI 引用份额:docs 是 LLM 编程答案的首选引用源;ChatGPT 占 AI 推荐流量 ~88%(2026 报告级)。
- AI 爬虫抓取量与 ChatGPT/Copilot referral 增速(站内 AI 流量占比 ~1% 是 2026 常态基线,涨速比绝对值重要)。
- quickstart 完成率(漏斗顶部质量)。
- 站内搜索零结果率(文档覆盖缺口最直接信号)。
- 旧版本页索引健康:该 noindex 的版本是否还在收录、是否蚕食最新版。

**获取策略重点**

- 对 AI 爬虫明确开放策略(GPTBot 等,见 [ai-crawler-policy.md](../technical/ai-crawler-policy.md))——封锁等于把 AI 答案位让给竞品文档。
- 开发者社区答疑:StackOverflow/Reddit/HN 带文档深链,答案即外链。
- 集成伙伴文档互链 + GitHub README/官网导流。

**典型死法**

- 纯客户端渲染,AI 爬虫与传统爬虫都读不到正文(<500 可见字符判 CSR 兜底)。
- 全版本页可索引,自我蚕食(v1/v2/v3 同关键词)。
- 把 llms.txt 当万能药:500M 事件分析显示 AI 爬虫几乎不抓它(观察级),Google 官方 2026 确认对排名无影响——正解是常规可爬性+清晰结构。
- 没有错误码页——开发者最高频的长尾词群(`<service> error 429`)拱手让人。
- API 重构后旧路径 404,生态外链与教程引用集体断裂。

**pSEO 机会**

- 错误码百科:`<service> error <code>` 每码一页(带成因与修复)。
- `语言 × 功能` SDK 示例页;`集成 × 平台` how-to。
- changelog 条目独立化吃 `<功能> release` 词。

## ⑥ 工具 / 免费计算器站

**页面清单(必争 URL 集)**

- 工具面:`/tools/<工具>`、`/calculators/<主题>`(页面即产品)。
- 内容面:每工具配套「怎么算/公式/结果解读」文;公式页单独可排名。
- 传播面:嵌入代码页(widget 换署名链接)、结果分享页。

**Schema 组合**

- WebApplication/SoftwareApplication + FAQPage(工具常见问题)。
- 配套文 HowTo(步骤)+ Article + BreadcrumbList。

**核心 KPI**

- 每工具页引用域获取速度:免费工具=最自然的 linkable asset(2026 共识级,Semrush 等)。
- 工具→注册/付费转化率(免费到付费的漏斗必须能归因)。
- 嵌入 widget 与分享链接带来的回链数。
- 品牌词月增长(工具被口碑传播的滞后指标)。
- 配套文 vs 工具页流量比:纯工具无文=信息词全丢。

**获取策略重点**

- 工具本身即链接磁铁:Reddit/论坛/newsletter 自发推荐——做「省时间/算得清」的工具,不做玩具。
- 配套内容打 "how to calculate X / X formula" 词群并双向内链工具页。
- Product Hunt/工具目录提交 + 提供嵌入 widget 换署名链接(seomatic 式 100+ 免工具矩阵可参考)。

**典型死法**

- 纯 JS 工具零可索引文本:公式、说明、示例输入全不进 HTML。
- 计算结果不生成可分享 URL——无独立落地页可排名、无传播钩子。
- 每个输入变体造一页,doorway 式膨胀。
- 工具与主营业务无关:流量不转化还稀释主题相关性。
- 工具包几 MB JS,CWV 崩掉拖累整站质量信号。

**pSEO 机会**

- 参数化结果 URL:固定输入的分享链接各成一页(结果数据真实唯一,非样板)。
- 单位/货币/进制换算矩阵(每页带换算表静态文本)。
- `行业 × 计算器` 变体页(每页配该行业口径与公式说明)。

## ⑦ Marketplace / 平台型

**页面清单(必争 URL 集)**

- 供给侧(SEO 库存):`/s/<商家|服务者>` 详情页、`/c/<类目>` 列表页、入驻招商页。
- 需求侧:`/<城市>/<类目>` 组合页、`/<类目>/<属性>` 页、best-of 榜单页。
- 信任面:如何运作/保障/退款政策页(平台型转化前置)。

**Schema 组合**

- Service/Product + 提供者实体(Person/Organization/LocalBusiness)+ 真实 AggregateRating。
- 榜单页 ItemList;全站 BreadcrumbList;同一商家多入口统一规范 URL。

**核心 KPI**

- 供给侧 vs 需求侧流量比:健康曲线是先供后需——倒挂=空货架在吃流量然后流失。
- 类目供需密度:每页可售条目数,密度达标才推需求词。
- 空/薄列表页索引占比(平台型经典暴雷指标,与 [programmatic-seo-gates.md](../technical/programmatic-seo-gates.md) 的 not-indexed 占比同源)。
- `城市×类目` 页与类目搜索页的蚕食监控。
- UGC 质量分:审核前后差值、重复/垃圾条目率。

**获取策略重点**

- 供给侧先行:批量收录商家/商品页做「SEO 库存」(Zapier/Booking 范式),库存密度达标才开需求侧词。
- 富结果军备:价格/评分/库存结构化数据拿 SERP 占位(平台 SERP 竞争即富结果竞争)。
- `品牌 × 城市`、`属性 × 类目` 长尾矩阵截流巨头(thebcms pSEO 案例集范式)。

**典型死法**

- 需求页先于供给上线,大量空类目页被批量去索引,再难翻身。
- 同一商家多入口多 URL 无归一(搜索页/类目页/标签页三个版本)。
- UGC 无质量门槛,整站质量信号被垃圾条目拖垮。
- 列表纯 AJAX 分页不可爬,第 2 页起的库存对引擎不存在。
- 冷启动只买付费流量填需求,SEO 库存始终为零,退出成本越滚越高。

**pSEO 机会**

- `城市 × 类目` 矩阵:每格库存 ≥ 阈值才生成(典型 5-10 条起)。
- 属性长尾:pet-friendly / 24h / open-now / accepts-insurance。
- best-of 榜单页(真实评分与评价摘要,非软文);比价/询价聚合页。

## ⑧ YMYL(医疗 / 金融 / 法律)

**页面清单(必争 URL 集)**

- 专业面:`/<条件|业务>` 每题一页(医疗 condition 页/法律 practice area 页/金融产品解读页)。
- 信任面:作者资质页(实名+执照+经历)、编辑政策与方法论页(how we review/test)、医审/法审署名机制。
- 工具面:计算器/自查评估页;免责与隐私页(合规面)。

**Schema 组合**

- Person + hasCredential + reviewedBy(医审/法审实体);Organization。
- Article + 作者署名;FAQPage 谨慎使用(医疗答案断章风险)。
- 医疗:MedicalWebPage;执业类:LegalService/Dentist 等分型;医疗实体禁 aggregateRating(合规红线详见 [site-type-templates.md](../technical/site-type-templates.md) 六行业表)。

**核心 KPI**

- 实名作者实体被知识面板/AI 答案引用数:2026-08 报告级——YMYL 匿名内容不承载权重(Sure Oak)。
- 医审/法审覆盖率与复核日期新鲜度(旧内容无复核=静默下滑)。
- 品牌词 vs 非品牌比:YMYL 转化重度依赖品牌信任,纯非品牌流量转化差。
- AI Overview/聊天引擎引用份额(见 [ai-citation-patterns.md](../content/ai-citation-patterns.md))。
- 合规分四项:署名/来源/引用/利益披露——起查用 [core_eeat.py](../../scripts/core_eeat.py)。

**获取策略重点**

- 资质署名 + 专业审阅制度:是排名前提,不是加分项。
- 权威外链:原创数据/研究做数字 PR,换学术机构与政府类引用(一条 .edu/.gov 级引用>百条目录)。
- 第三方声誉面:Reddit/权威论坛/百科的被动提及——AI 检索与 YMYL 质量评估都重,配品牌词防御页。

**典型死法**

- 匿名或假名作者,整站 YMYL 权重归零。
- 无编辑政策/方法论/复核日期页,E-E-A-T 无处验证。
- 医疗实体强加 aggregateRating 或征集患者评价(HIPAA+富结果双输;日本患者体验谈属医疗广告禁止项)。
- 旧医疗/费率内容断更无复核:利率、法案、指南一变即失准。
- AI 批量生成无审内容,一次质量更新整站清退。

**pSEO 机会**

- `费用 × 地区` 页:`cost of <procedure|case> in <state>`——医疗/法律通用强需求。
- 法条/资格 × 州页(法律);监管 × 产品页(金融)。
- 计算器矩阵(贷款 APR/赔偿金/税费/报销)——嫁接⑥号工具站打法;症状自查工具页(结果页必须带就诊指引与免责)。

## 来源

本文由 EveryInfra 综合编写,只保留要点与口径,未复制原文。

- 2026 转化基准(报告级,单源慎用):[Stackmatix(2026-09)](https://www.stackmatix.com/blog/website-conversion-rate-benchmarks)、[Flighted B2B SaaS(2026-05)](https://www.flighted.co/blog/b2b-saas-conversion-rate-benchmarks)、[Authoricy AI 搜索转化(2026-06)](https://authoricy.com/blog/ai-search-conversion-benchmarks)
- 电商/Discover/本地:[DigitalApplied 电商(2026-01)](https://www.digitalapplied.com/blog/ecommerce-seo-product-category-page-guide-2026)、[DigitalApplied Discover 更新(2026-02)](https://www.digitalapplied.com/blog/google-discover-core-update-february-2026-seo-guide)、[DigitalApplied 本地核心更新(2026-03)](https://www.digitalapplied.com/blog/local-seo-march-2026-core-update-gbp-optimization-guide)
- YMYL/文档与 AI 爬虫:[Sure Oak 金融 YMYL(2026-08)](https://sureoak.com/insights/ymyl-eeat-financial-services-seo-rules)、[Limy llms.txt 500M 事件分析(2026-05)](https://limy.ai/blog/llms-txt-in-2026-the-full-guide)、[Google AI 优化指南(官方)](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
- pSEO 范式:[Zapier 案例(salt.agency)](https://salt.agency/blog/how-zapier-quadrupled-organic-traffic/)、[pSEO 案例集(thebcms)](https://www.thebcms.com/blog/programmatic-seo-examples/)
- 本地六行业/网格排名/权重模型深读来源:见 [site-type-templates.md](../technical/site-type-templates.md) 文末及文内标注
