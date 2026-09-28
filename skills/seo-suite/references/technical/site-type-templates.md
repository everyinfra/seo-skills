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

## 平台 / 市场型站点

- 主要页面：分类、列表、详情（商家、服务提供者、条目）、地点组合页。
- 要点：用户生成内容需要质量门槛；空列表页和极少条目的组合页不索引；详情页的重复内容（同一商家多个入口）统一规范 URL。

## 交付

- 页面类型清单与层级图。
- URL 规则与示例。
- 需要重定向的变更清单。
- 可索引与不可索引页面的规则。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/site-architecture/references/site-type-templates.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/site-architecture/references/site-type-templates.md)（MIT）
- 一手资料：[Google：网址结构](https://developers.google.com/search/docs/crawling-indexing/url-structure)、[Google：分面导航](https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation)、[Google：电商网站](https://developers.google.com/search/docs/specialty/ecommerce)、[Google：规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
