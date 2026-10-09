# 不同类型站点的信息架构要点

用途：规划或审计站点结构时，先按站点类型确定主要页面类型、层级和 URL 规则，再细化导航与内链。通用原则见 [link-architecture-patterns.md](link-architecture-patterns.md)、[navigation-patterns.md](navigation-patterns.md)，画图见 [mermaid-templates.md](mermaid-templates.md)。

## 通用规则

- URL 简短、可读、稳定，用连字符分词；层级只在确实反映内容关系时使用。
- 一个内容只有一个规范 URL；参数、排序、追踪参数产生的重复页用 canonical 或其他方式处理。
- 重要页面从首页出发几次点击内可达。
- 结构调整涉及 URL 变更时，提前准备逐条重定向表。

## SaaS 营销站

- 主要页面：首页、产品或功能页、解决方案页（按行业或角色）、定价、客户案例、集成、资源（博客、指南、模板）、对比页。
- URL 示例：`/features/<功能>`、`/solutions/<行业>`、`/integrations/<工具>`、`/compare/<竞品>`。
- 要点：功能页和解决方案页分别对应「能做什么」和「适合谁」两类搜索；集成页和对比页常是规模化页面的来源，注意每页要有独立价值（见 [playbooks.md](playbooks.md)）。

## 内容站 / 博客

- 主要页面：首页、专题（支柱）页、分类、文章、作者页、标签（谨慎使用）。
- URL 示例：`/topics/<专题>`、`/<分类>/<文章>` 或 `/blog/<文章>`。
- 要点：按专题集群组织（见 [topic-cluster-templates.md](../research/topic-cluster-templates.md)）；标签页过多且内容稀薄时考虑 noindex 或合并；作者页支撑署名与专业性。

## 电商

- 主要页面：首页、类目（多级）、商品详情、品牌页、筛选结果、导购内容。
- URL 示例：`/c/<类目>/<子类目>`、`/p/<商品>`。
- 要点：分面筛选会产生大量参数组合，只让有搜索需求的组合可索引，其余控制抓取（见 Google 分面导航文档）；缺货和下架商品的处理要事先定规则；商品页配合 Product 结构化数据。

## 文档站

- 主要页面：文档首页、快速开始、指南、API 参考、更新日志、常见问题。
- URL 示例：`/docs/<章节>/<页面>`，版本化时 `/docs/v2/...`。
- 要点：侧栏目录与 URL 层级一致；多版本并存时明确哪个版本是规范版本；API 参考页逐项写清参数与示例。

## 产品 + 内容混合站

- 要点：营销页和内容页分区清楚，但互相链接——文章链接到相关功能页，功能页链接到深入指南；避免博客成为与产品无关的孤岛。

## 本地业务

- 主要页面：首页、服务页（每项服务一页）、门店或服务区域页、关于、联系。
- 要点：多门店时每个门店一页，写真实地址、营业时间和本地信息，不做只换城市名的模板页；配合 LocalBusiness 结构化数据和地图商家资料。

### 本地 SEO 六行业速查(2026-10-09 并入;来源类型:官方/行业/观察)

| 行业 | 平台要点 | 评价边界(合规红线) | schema 正解 | 常见错误 |
|---|---|---|---|---|
| 餐饮 | 主类目 Restaurant+官方菜单编辑器/预订链接 | 美国 FTC 16 CFR 465(2024-10 生效):禁虚假/未披露激励/内部人评价,单条罚 ~$53,088(官方);日本 ステマ規制 | `Restaurant`+`hasMenu` | 泛 LocalBusiness;菜单不可见却标记 |
| 医疗/牙科 | 类目 Dentist/Medical clinic;**insurance accepted 属性**逐保司填(观察级) | 回复评价不得确认就诊关系/不透 PHI(HIPAA);**日本:患者体验谈属医疗广告禁止项**(MHLW 官方)——自站禁登,第三方自发评不论 | `Dentist`/`Physician`(单人)/`MedicalClinic`/`Hospital` 分清 | 医疗实体强加 aggregateRating(富结果受限) |
| 法律 | 类目 Lawyer/Legal services | ABA 7.1/7.2(不虚假/不付酬换评)+1.6 保密——回负评不透委托事实 | `LegalService`/`Attorney` | 州广告规则误判 |
| 家居服务 | **SAB 模式:隐藏地址+服务区**;完工后短信征集 | EU UCPD/Omnibus 禁未披露激励评价(官方) | `HomeAndConstructionBusiness` 子类(Plumber/Electrician/RoofingContractor) | 服务×城市页无真实本地证据→doorway 风险 |
| 教育 | 类目 School/Tutoring/Language/Driving school | 未成年人隐私与肖像授权 | `EducationalOrganization`/`School` | **`DrivingSchool` 在 schema.org 不存在(404 已验证)**——用 LocalBusiness+additionalType |
| 汽车 | Auto repair/New-Used car dealer+预约链接 | 售后/交车后征集 | `AutoRepair`/`AutoDealer`/`AutoWash`(AutomotiveBusiness 子类) | 品牌类目漏选 |

**评价生态第二平台(按市场)**:日=食べログ+EPARK(医疗)+Hot Pepper;韩=네이버 플레이스(리뷰 최근성·꾸준함>总数+**저장**;官方两度修订 리뷰 政策,伪造票据刷评→清零);俄=**Google 自 2022-03 停俄区用户发评**(媒体级)→Yandex Business+2GIS/Flamp/Отзовik;巴西=Reclame Aqui 双轨;德=ProvenExpert(本土印章文化)+Handwerkskammer 会员目录(手工业高权威免费外链,Meisterbetrieb 称号仅限持证者——合规红线)。

- 网格排名监控(ARP/ATRP/SoLV 源码级公式、网格参数与半径公式、5 层审计法、GBP 信号权重、API 盲区、审计输出模板):[local-grid-ranking.md](../monitoring/local-grid-ranking.md)

## 平台 / 市场型站点

- 主要页面：分类、列表、详情（商家、服务提供者、条目）、地点组合页。
- 要点：用户生成内容需要质量门槛；空列表页和极少条目的组合页不索引；详情页的重复内容（同一商家多个入口）统一规范 URL。

## 交付

- 页面类型清单与层级图。
- URL 规则与示例。
- 需要重定向的变更清单。
- 可索引与不可索引页面的规则。

### 本地网格排名三指标(实现口径,cablate/mcp-google-map 精读;百仓深扫)

- **ARP**(Average Rank Position)= 仅在"找到目标"的格点上求平均排名——找不到任何点则 null;
- **ATRP** = 全部格点平均,**未找到按 rank=21 计**(惩罚缺失)——两者口径差异必须同时报;
- **SoLV** = (进 top3 的格点数 ÷ 总格点) × 100,分母含未命中点;另报 found_in "x/y"。
- 网格参数:gridSize 3/5/7(9/25/49 点,默认 3)、间距 100–10000m(默认 1000m);纬度 111320 m/度,经度除以 111320×cos(纬度);每点 Text Search locationBias radius=间距/2,maxResultCount 20,并发 5。
- 5 层分析法:关键词版图→竞品深挖→缺口→区域密度(高密度+低评分=机会/低密度=蓝海/双高=红海)→月度快照;缺口阈值:评论数达头部竞品 80%、评分 ≥4.2、照片 ≥10;**search_nearby 不支持中文类目名须用英文 type**。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/site-architecture/references/site-type-templates.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/site-architecture/references/site-type-templates.md)（MIT）
- 一手资料：[Google：网址结构](https://developers.google.com/search/docs/crawling-indexing/url-structure)、[Google：分面导航](https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation)、[Google：电商网站](https://developers.google.com/search/docs/specialty/ecommerce)、[Google：规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)

## 内容流水线三段分工 + 机会五桶(notfair 深读 2026-10-09b)

来源:nowork-studio/notfair-plugin 的 keyword-research、content-planner、content-writer。

**三段互不越界**:keyword-research=从种子词发现词宇宙(seed 驱动);content-planner=从**本站 GSC 数据**挖掘机会并排期;content-writer=单题成文。

### content-planner(GSC→日历)

- 90 天三类拉取:Query×Page top 5000(**唯一能推理 intent 的笛卡尔视图**——页是答案面,词是需求)/Page-only top 1000(找高曝光低 CTR 页)/top 100 页的国家+设备;原始拉取缓存 7 天。
- **机会五桶**:A striking-distance(位 5-20、曝光 ≥100/90d、informational,最高优先——刷新或新文即可进 top5);B 未答 intent(全站无页排名且站在该领域经营);C CTR underperformer(位 1-10、曝光 ≥500、CTR<该位预期的 50%→出 **refresh 任务**而非新文,转标题/描述改写);D 相关词扩展(每 A/B 词派 2-4 变体聚为该文 H2,不单列日历);E 蚕食预警(同词多页各 >20 曝光→**排期阻断器**,先定 canonical 再排)。
- `clickPotential = projectedImpressions × (targetCtrAtPosition3 − currentCtr)`,targetCtr@3=0.10;按此降序,**日历封顶 12 题/3 月**(多了变货架货)。
- 状态机:planned→in-progress→**ready_to_publish(用户手动翻,系统永不自动晋升)**→published/failed;发布器只取 ready_to_publish 且有正文的条目。
- 质量闸:GSC 未连→停并走 OAuth;<50 行(query,page)→数据太少,明说是推测并停;裸关键词标题→重写;两题同 primaryKeyword→自造蚕食,合并或降一题。

### content-writer(编辑标准)

- 标题必须 **hook 驱动**(数字/反共识/点名受众/好奇缺口)+关键词前置+≤60 字符——裸关键词标题直接 fail。
- 博客硬性要求:≥1000 词地板、目录镜像全部 H2、featured 图+**≥3 内联图且每图有角色**(图表/截图/比较/数据可视化;装饰性库存图=fail)、FAQ 3-5 题(打 People Also Ask)、开头是钩子不是铺垫。
- **intent 定格式**:transactional→landing 不是博客,informational→博客不是销售页;反模式清单:关键词堆砌/填充段/"it depends"式 AI 骑墙/文字墙/与站内既有页意图重复。
- E-E-A-T 落地=只有亲历者才写得出的细节+原创分析+数据背书;**"Last Click 测试"**:读者读完还需再搜一次→没写完。
- 合规敏感话题(旅行规则/政府手续/健康安全/报销/管制产品/截止期)必须引官方规则源、写明时限与例外;计算器/清单要把同样的 caveat 编进去。
- 图片资产校验:扩展名=MIME/文件签名、尺寸、OG 元数据一致,发布前压到展示尺寸。
- 交付物:全文+SEO 元数据+JSON-LD(Article/BlogPosting 带 image,或 Service/Product/LocalBusiness)+**双向内链计划**+发布清单(含 canonical 指自身、移动渲染验证)。

### keyword-research(打分)

- `Opportunity = (Volume × IntentValue) / Difficulty`;IntentValue:informational/navigational=1、commercial=2、transactional=3;难度三档 70-100/40-69/1-39(大品牌+高 DA+广告霸屏=高)。
- **GEO 高潜词形**:问句("what/how/why")、定义("X meaning")、对比("A vs B")、榜单("best/top N")、how-to——可被 AI 简洁作答、话题网上有据、低商业意图。
- 输出必须逐条注明数据来源(工具拉取/用户提供/估算),pillar-cluster 结构给到每词的链接指向。

## 电商站审计五相 + 程序化 pSEO 闸门(notfair 深读 2026-10-09b)

来源:ecommerce-seo、programmatic-seo(能力部分源自开源 claude-seo,MIT;实现为 notfair 原创)。

### 电商(与上面"电商"节互补的操作化)

- **面导航是电商第一漏点**:先数清被索引的 `?color=`/`?orderby=`/`?filter_` URL;GSC Index coverage 里 "Crawled – currently not indexed" 聚集=典型信号。处理:有值组合 canonical 到净类目或 noindex,follow;纯排序/参数 URL 用 robots.txt 断爬;报告要**量化 crawl 泄漏(垃圾索引 URL 数)**。
- PLP:独特可索引+导语文案(不是纯商品网格);**分页 self-canonical,不 canonical 到第 1 页**;类目词进 title/H1;面包屑在场。
- PDP:标题/描述去厂商样板;薄页(无描述/单图)标记;**变体 canonical 归一**(不留 30 个近重复 URL);**缺货排名品保留+标 availability,不 404**;真死 SKU 301 到类目/替代品;页内评论 UGC 养长尾+富结果。
- schema 校验:Product+Offer(price/availability/currency)+AggregateRating/Review(仅真实页内评论)+BreadcrumbList。
- 模板会重复:抽代表性 PLP/PDP 深检即可推广。报告=电商 SEO 分+泄漏估计+影响×努力排序+30 天计划。

### 程序化 pSEO

- 唯一防线=**每页独特价值**:独特数据真实存在,不是变量 find-replace 的样板;"{city} 替换型"=doorway page,会被整组去索引——计划不过关就直说。
- 先验证 query 模式在变量维度上有**真实分布的需求**;不是每个组合都配一页;无数据的组合 noindex 或干脆不生成。
- 架构:hub 页+相关页模块保证可达与互链,不孤立;**分批上线→看索引率→再扩**;title/H1/meta 模板化但去重;内容必须在 HTML/可渲染,非纯客户端。
- 审计模式核心指标:set 中 "Crawled/Discovered – not indexed" 占比(pSEO 经典失败信号)。

## Schema 内容型映射 + 单页六维评分(notfair 深读 2026-10-09b)

来源:schema-markup-generator(CORE-EEAT O05 表)、seo-page。

### 内容型→schema 映射(O05)

| 内容型 | 必备 | 条件性 |
|---|---|---|
| 博客(指南) | Article、Breadcrumb | FAQ、HowTo |
| 博客(工具) | Article、Breadcrumb | FAQ、Review |
| Best-of 榜单 | ItemList、Breadcrumb、FAQ | 每工具 AggregateRating |
| 替代品对比 | Comparison*、Breadcrumb、FAQ | AggregateRating |
| FAQ 页 | FAQPage、Breadcrumb | — |
| SaaS landing | SoftwareApplication、Breadcrumb、FAQ | WebPage |

多类型同页=单个 `<script type="application/ld+json">` 内包 JSON 数组;校验底线:绝对 URL、ISO 8601 日期、**与页面可见内容一致**、无尾逗号。

### 单页评分(seo-page)

- 六维加权:**intent 对齐 20%/E-E-A-T 20%/内容质量深度 20%/On-page 15%/结构 UX 15%/技术 10%**;每分必须引用页面原文证据,修复给到可复制粘贴级。
- **Indexability 先行闸**:noindex/robots 拦截/canonical 指他/URL Inspection 未索引→**停止评分**,作为 Critical 置顶,其余分数标"学术性"。
- **反循环推理**:intent 以 SERP 为准,不是页面自我声明——top5 全是 listicle 而本页是 product page=mismatch;先搜词看 SERP 再评页。
- CTR 基准表(按位/意图):位 1 info 25-30%、trans 20-25%、brand 40-50%;位 3 info 9-12%;位 11-20 info 0.5-1.5%;**SERP 特性压有机 CTR 30-50%,有 featured snippet 时对预期打 ~7 折**;位稳 CTR 跌=SERP 变化不是内容退化。
- 竞品快查:WebFetch top 2-3 竞品**真实 HTML 数词数**,不从 ~160 字符的 snippet 估深度;1500 词在 800 词竞品里是厚,在 3000 词竞品里是薄。
- CSR 兜底:抓到的 body 可见文本 <500 字符→用无头浏览器渲染后再分析,否则产出垃圾分。
- 报告规则:单一最大解锁点置顶(如整页 intent 错位),即使别的问题更多。

## WordPress 连接器操作(notfair 深读 2026-10-09b)

来源:wordpress/(MCP 第一方连接器 `wordpress_` 工具)。

- **两套凭据不混用**:连接器是 NotFair MCP 的 WordPress 集成;本地 Application-Password/`.env.local`(setup-cms,面向 SEO 脚本,兼容 WordPress/Strapi/Contentful/Ghost)是另一条路;不从 Search Console 或本地配置推断连接器权限。
- 先用无害读确认站点清单,**只选连接器实际返回的站点**;记录站点 URL、site id、当前用户/角色、会话可否改内容/设计/设置/管理面(users/settings/design/plugins/themes/core/files/jobs 需 admin;插件管理自改被禁)。
- **写前读+乐观锁**:编辑前先读当前资源拿 `expectedVersion`;新 standalone HTML 文件的哨兵值是字面量 `absent`。
- 幂等纪律:`requestId` 重试同一逻辑动作时保持稳定,**输入变了绝不复用**;结果未知时 get-change+restore-change 优于盲重试。
- standalone HTML 发布:拒绝脚本、精确 URL、仅 admin;内容默认建 draft,**draft/brief/生成文件=ready_for_review,连接器确认后才叫 published**。
- 单点编辑优先用直接 update 工具而非 job。

## 本地业务站点结构与信号深读(claude-seo 深读 2026-10-09b)

- **业务形态三分法**(先判定再选检查项):Brick-and-Mortar(页面/页脚可见街道地址+地图嵌入)、SAB 服务区域业务(无可见地址,只有 "serving [city]" 或 schema `areaServed` 无 `streetAddress`)、Hybrid(两者兼有);SAB 跳过地图嵌入核验与实体地址一致性检查,实体店才做全量 NAP+地图。
- **六维权重模型**:GBP 信号 25% / 评价与声誉 20% / 本地 on-page 20% / NAP 一致性与引用 15% / 本地 schema 10% / 本地链接权威 10%。
- **多位置架构**:`domain.com/locations/city-name/` 子目录优于子域(整合链接权重,Bruce Clay 案例 50%+ 流量提升);门店定位器用**可爬 URL**(SSR/SSG 优先于 CSR);每位置页独立 LocalBusiness+唯一 `@id`,经 `branchOf` 连首页 Organization;位置页 **>60-70% 唯一内容**(行业共识,非 Google 确认阈值);**swap 测试**:换城市名后内容仍通顺=doorway 页(2024-03 核心更新后 HVAC 案例掉 80% 排名);**规模闸门:30+ 位置页 WARNING 强制 60%+ 唯一,50+ HARD STOP 需用户说明**。
- **页面要素清单**:title/H1 含城市+服务;页脚可见 NAP;**每项核心服务单独一页**(Whitespark 2026:本地自然排名 #1 因素兼 AI 可见性 #2);`tel:` 点击呼叫+首屏联系表单;地图嵌入 lazy-load(地理信号强化,非直接排名因素);2-5 条/千词上下文内链,关键页首页 3 次点击内可达。
- **GBP 要点**:主类目是单一最重要的本地包因素(选错主类目=第一负面因素);次类目最优再配 4 个;**GBP 网站链接别指向最强页面**(Sterling Sky:有压制自然排名风险);Q&A API 2025-11-03 停用且公开问答在退场→常见问题写进网站与商家描述;Verified badge(2025-10)取代 Guaranteed/Screened。
- **评价健康**:速度>总量(18 天断档即明显掉排名的案例);10 条基准线;31% 消费者只用 4.5+ 星(68% 只用 4+);74% 只看近 3 个月;88% 愿选回复评价的商家;**评价门控(先筛满意度再引流评价平台)违反 Google 假互动政策与 FTC 规定**。
- **引用与 AI 检索**:Google 2025-07 从 prominence 定义移除 "directories";引用对传统本地包降权但 **AI 可见性前 5 因素中 3 个是引用类**(Whitespark);**ChatGPT 不直接读 GBP**——源自 Bing 索引/Yelp/TripAdvisor/BBB/Reddit→Bing Places(供 ChatGPT/Copilot/Alexa)与 Apple Maps 要认领;三大数据聚合器 Data Axle/Foursquare/Neustar(TransUnion)做下游分发。
- **本地链接与 AI 转化**:"best of" 榜单=第一 AI 可见性引用因素;品牌提及与 AI 可见性相关性约为传统外链 3 倍(Ahrefs:0.664 vs 0.218);ChatGPT 本地转化率 15.9% vs Google 自然 1.76%(Seer Interactive,样本型数据);本地小站链接速度基准 5-10 条质量本地链/月(共识值)。
