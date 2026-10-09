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
