# SERP 功能：说明什么、能做什么、不能保证什么

> 涉及 AI 概览、AI 模式或 AI 引用的判断，先读 [geo-evidence.md](../content/geo-evidence.md)。

## 用途与何时读

做 SERP 分析、判断查询意图、决定页面形式和结构化数据时读。SERP 功能首先是**意图的旁证**，其次才是可争取的展示位置。意图判定见 [keyword-intent-taxonomy.md](keyword-intent-taxonomy.md)。

## 三条通用原则

1. **展示由搜索引擎自动决定。** 内容格式和结构化数据只影响是否「有资格」、能否被正确理解，不保证出现，也不保证排名或点击。
2. **功能会变。** 同一查询在不同时间、地域、语言、设备下的功能组合不同，Google 也会增删功能。记录查看条件；拿不准某功能当前是否还在展示，以当前 Google 文档为准。
3. **结构化数据必须与可见正文一致。** 支持哪些富结果以 Google 结构化数据类型库的当前列表为准；schema.org 里有某个类型，不等于 Google 会为它展示富结果。

## 常见功能

| 功能 | 出现时通常说明 | 页面能做什么 | 不能保证 / 注意 |
|---|---|---|---|
| 精选摘要 | 用户要一个直接答案：定义、步骤、列表或表格 | 在对应标题下紧跟简洁完整的回答，用真实的 `<ol>`、`<ul>`、`<table>` 组织 | 没有专门标记能申请；可用 `nosnippet`、`max-snippet` 限制摘录 |
| People Also Ask | 主题下还有一串相关疑问 | 把真实相关问题当选题线索，在正文里清楚回答 | FAQPage 标记不会让页面进入 PAA |
| AI 概览 / AI 模式 | 问题需要综合多个来源 | 页面可被抓取、已编入索引、能以摘要形式展示；事实清楚、来源可核对 | Google 说明没有额外要求或专门的 AI 标记；不承诺被引用 |
| 知识面板 | 查询指向一个实体（品牌、人物、机构） | 官网信息一致，Organization 结构化数据与可见信息一致，其他可信来源里有准确记录 | 不能直接申请或编辑；实体认领需走 Google 的验证流程 |
| 附加链接（sitelinks） | 导航型、品牌型查询 | 清楚的站点结构、唯一且描述准确的页面标题、合理内链 | 全自动生成，无标记可控制；附加链接里的站内搜索框已被 Google 取消，以当前 Google 文档为准 |
| 图片结果 | 用户想看样子、示意、设计 | 原创图片、描述性文件名和 alt、图片靠近相关文字、图片站点地图 | 图片搜索流量不一定转化 |
| 视频结果 | 操作演示、评测类需求 | 视频有独立可索引的观看页面，提供 VideoObject 和视频站点地图；可标记关键片段 | 视频平台的结果常占多数，自有页面不一定进得去 |
| 本地结果 | 显性或隐性的本地需求 | 维护商家资料（需要你自己的 Google 商家资料账号），各处名称、地址、电话一致 | 距离等因素不受网站控制 |
| 购物结果 | 明确的购买意图 | Product 结构化数据与页面价格、库存一致；商品数据经 Merchant Center 提交（需要你自己的账号） | 页面和数据源不一致会被拒 |
| 评分星级等富结果 | 用户在比较品质 | 只为 Google 支持的类型、真实存在的评分加标记 | 没有真实评分就不写 aggregateRating |
| FAQ / HowTo 富结果 | 均已停止展示 | FAQPage 只描述页面上真实存在的问答；步骤照常用有序列表写清楚 | FAQ 按 [geo-evidence.md](../content/geo-evidence.md) 的记录；HowTo 以当前 Google 文档为准；都不当争取目标 |
| 相关搜索 | 用户的后续探索方向 | 作为选题和内链线索 | 无优化位 |

## 读 SERP 组合

- 购物、广告、评分同时出现：交易或商业调研意图强，信息型长文很难排上去；广告多时自然结果整体下移。
- 本地结果加广告：本地服务需求，先看商家资料，再看落地页。
- 精选摘要、PAA、视频同时出现：信息需求多样，一篇指南配清楚的步骤或演示更容易覆盖。
- 几乎只有普通蓝色链接：功能少，可能是新话题或小众话题，SERP 前列的页面类型更值得参考。

## 监测怎么记

- 每个目标查询记录：日期、地域、语言、设备、出现的功能、各功能由哪个 URL 占据，最好附截图。数据来自你自有或自选的数据源（例如排名追踪工具导出、手工抽查）。
- Search Console 效果报告的「搜索外观」筛选可看部分富结果的表现；按 Google 的 AI 功能说明，AI 概览和 AI 模式带来的流量计入「网页」搜索类型的总数（能否单独拆分以当前 Google 文档为准）。需要你自己的 Search Console 权限。
- 功能出现、消失或易主时，先确认是否为功能本身调整，再判断是否与页面改动有关，不把相关性当因果。

## 交付物

1. 目标查询的 SERP 功能清单和查看条件。
2. 每个功能的推断意图，以及对页面形式的影响。
3. 可以做的页面调整和结构化数据（注明对应的 Google 文档），以及明确不做的事项。
4. 验证方式：富媒体搜索结果测试、Search Console 增强报告、定期抽查。

## 常见误区

- 把「加标记」当成「拿到展示」。
- 为了 FAQ 富结果把正文改成问答堆砌。
- 为精选摘要写固定字数的答案，不看问题本身需要多少信息。
- 以为 AI 概览需要专门的 Schema 或文件。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · research/serp-analysis/references/serp-feature-taxonomy.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/research/serp-analysis/references/serp-feature-taxonomy.md)（Apache-2.0）
- 一手资料：[精选摘要](https://developers.google.com/search/docs/appearance/featured-snippets)、[AI 功能与网站](https://developers.google.com/search/docs/appearance/ai-features)、[摘要与 meta description](https://developers.google.com/search/docs/appearance/snippet)、[结构化数据类型库](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)、[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)、[Organization](https://developers.google.com/search/docs/appearance/structured-data/organization)、[Product](https://developers.google.com/search/docs/appearance/structured-data/product)、[Google 图片 SEO](https://developers.google.com/search/docs/appearance/google-images)、[视频 SEO](https://developers.google.com/search/docs/appearance/video)、[电商网站](https://developers.google.com/search/docs/specialty/ecommerce)、[富媒体搜索结果测试](https://search.google.com/test/rich-results)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)

## 市场差异:各市场 AIO 覆盖与 SERP 占位层(2026-10-09 深挖轮)

**AIO 上线时间线(=市场红利窗口)**:印尼/巴西 2024-08 → 波兰 2025-03-26(Przeglądy od AI,~28.95% 单源)→ 德国 ~2025(覆盖 ~20%,Sistrix)→ **法国 2026-07-22(比德晚一年多——后上线市场多吃一年经典 SEO 窗口)**;巴西 AI Mode 2025-09-08 免 Search Labs 全量;荷兰触发率信息类仅 6.43%(2025-06,远低于美);意大利 48-54%(两家口径,标区间)。

**SERP 占位层(审计必查"谁占着本国 SERP")**:土耳其=UGC 五霸(Ekşi Sözlük/DonanımHaber/Technopat/Akakçe/Şikayetvar);泰国=Pantip(评测词霸榜,声誉+排名双角色);印度=聚合器层(JustDial 1000+ 城市/IndiaMART/Sulekha);越南=Kaskus 衰而未亡;韩国=Naver 自有垂直。

**声誉层通用模式**:品牌词 SERP 被本国投诉/UGC 平台占据(Şikayetvar/Pantip/Reclame Aqui/Отзовik/食べログ)——催生各国 ORM 产业;品牌词审计必查投诉站占位与情感。
