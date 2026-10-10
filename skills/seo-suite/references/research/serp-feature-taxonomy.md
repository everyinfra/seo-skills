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

**AIO 上线时间线(=市场红利窗口)**:印尼/巴西 2024-08 → 波兰 2025-03-26(Przeglądy od AI,~28.95% 单源)→ 德国 ~2025(覆盖 ~20%,Sistrix)→ **法国 2026-07-22(比德晚一年多——后上线市场多吃一年经典 SEO 窗口)**;巴西 AI Mode 2025-09-08 免 Search Labs 全量;荷兰触发率信息类仅 6.43%(2025-06,远低于美);意大利 48-54%(两家口径,标区间[待核:测量月])。

**SERP 占位层(审计必查"谁占着本国 SERP")**:土耳其=UGC 五霸(Ekşi Sözlük/DonanımHaber/Technopat/Akakçe/Şikayetvar);泰国=Pantip(评测词霸榜,声誉+排名双角色);印度=聚合器层(JustDial 1000+ 城市/IndiaMART/Sulekha);越南=Kaskus 衰而未亡;韩国=Naver 自有垂直。

**声誉层通用模式**:品牌词 SERP 被本国投诉/UGC 平台占据(Şikayetvar/Pantip/Reclame Aqui/Отзовik/食べログ)——催生各国 ORM 产业;品牌词审计必查投诉站占位与情感。

## 垂直检索面、页面变迁取证与数字 PR 外联（goose-skills 深读 2026-10-09b）

来源仓库 research-tools / outreach 的通用技能，对本页有两点增量：SERP 之外另有一排「垂直检索面」值得观测；站外占位（评价站、对比页、第三方引用）靠外联流程争取，而不是靠标记。

**垂直检索面清单**（multi-platform-search 类工具）：购物=Amazon / Walmart / eBay 站内搜索（各有独立排序因子，是 Google 购物卡之外的第二战场）；视频=YouTube 搜索 + 频道 + 字幕（字幕文本即视频关键词与 FAQ 素材，评论区=PAA 式追问挖掘）；应用=Apple App Store 搜索；本地 / 出行=TripAdvisor（类别与坐标过滤）、Airbnb；社交=TikTok / Instagram 档案页。广告库（Meta / Reddit / LinkedIn / TikTok）免费可查，是竞品付费创意与落地信息的监测源。观测任一引擎都记录引擎 + 查询 + 日期 + 地域参数，与上文「记录查看条件」同规矩。

**页面变迁取证**（Wayback CDX，免费，约 15 请求/分钟）：prefix 匹配拉整域快照、按天去重、`id_` 后缀取原始 HTML。用途：核对竞品页面何时改版 / 改价、找回已下线的对比页与客户名单、为「变化开始的日期」提供独立证据，服务报告的时间线对齐。

**数字 PR 外联的序列规则**（cold-email-outreach / outbound-prospecting-engine，移植到链接、评测与专家引用请求）：触达节奏 Day 1 / 5 / 12，每次换角度换框架（Signal-Proof-Ask → PAS → 社证）；个性化三档——合并字段 / 按细分 / 逐人定制（超过 50 人不做逐人）；硬规则：首句谈对方不谈自己、每次触达给新理由（禁止 just checking in）、每封一个低门槛 CTA、主题 50 字符以内无感叹号；联系人去重并缓存，不重复触达；发出前人工审核样信；效果分层看（送达 → 打开 → 回复 → 正向回复），基准按客群给区间。注意边界：外联争取的是**第三方页面上的位置**，SERP 槽位本身仍由搜索引擎决定，与上文三条通用原则不冲突。

## 触发条件与优化动作对照表（深读 2026-10-09）

先重申三条通用原则：表中「触发条件」是**旁证归纳**（出现该特征通常说明什么），「优化动作」只提升资格与可理解性，不保证展示。

| 特征 | 常见触发条件（旁证） | 优化入口 | 主要不可控项 |
|---|---|---|---|
| AI 概览 | 问题型、需综合多源的信息查询 | 无专门标记：页面可抓取、已索引、事实清楚可核对、被可靠来源引用；深入做法见 [geo-evidence.md](../content/geo-evidence.md) 与 [ai-citation-patterns.md](../content/ai-citation-patterns.md)（[Google AI 功能文档](https://developers.google.com/search/docs/appearance/ai-features)） | 是否被引用及引用版式 |
| 精选摘要 | 定义 / 步骤 / 列表 / 表格型查询；页面通常已在前十，5-20 位常被引用为机会带（[Frase](https://www.frase.io/blog/how-to-optimize-for-featured-snippets-on-google)、[Moz](https://moz.com/blog/optimize-featured-snippets)） | 问题作 H2/H3，紧跟约 40-60 词直接回答；步骤用 `<ol>`、对比用 `<table>`；答案里不塞品牌名（[Moz](https://moz.com/blog/optimize-featured-snippets)、[Nightwatch](https://nightwatch.io/blog/optimize-for-featured-snippets)） | 无申请入口；`nosnippet` / `max-snippet` 只能主动限制 |
| PAA | 主题存在追问链 | 用 PAA 树工具（如 AlsoAsked）与相关搜索挖真实问题，正文自然回答（[Semrush PAA 研究](https://www.semrush.com/blog/how-to-maximize-people-also-ask-seo-opportunities-study)）；FAQPage 标记不进 PAA | 问题由 Google 生成且会变 |
| 本地包 | 显性 / 隐性地域意图 | Google 官方三因子：相关性、距离、知名度（[官方文档](https://support.google.com/business/answer/7091)）——资料完整、类目准确、各处 NAP 一致、真实评价积累；网格监测见 [local-grid-ranking.md](../monitoring/local-grid-ranking.md) | 距离权重不受网站控制 |
| 购物 | 明确购买意图 | Product 结构化数据与页面价格 / 库存一致，Merchant Center feed 与页面一致（[电商指南](https://developers.google.com/search/docs/specialty/ecommerce)） | 商品数据审核与排序机制 |
| 视频轮播 | 操作、评测、教程类查询 | 独立可索引观看页 + VideoObject；SeekToAction 让 Google 自动识别关键片段（[Google 官方博客](https://developers.google.com/search/blog/2021/07/new-way-key-moments)）；完整字幕 / 转录文本利于理解（[Search Engine Land](https://searchengineland.com/guide/how-to-win-video-driven-serps)） | 平台视频常占多数位 |
| 知识面板 | 查询指向实体 | Organization 结构化数据与可见信息一致；Wikidata 等外部实体源准确 | 面板内容自动生成 |
| 图片包 | 视觉型查询（样子 / 设计 / 示意） | 原创图、描述性文件名与 alt、图片靠近相关文字、图片站点地图（[Google 图片 SEO](https://developers.google.com/search/docs/appearance/google-images)） | 图片流量不一定转化 |
| 相关搜索 / 热门搜索 | 用户有后续探索方向 | 当选题与内链线索，无优化位 | 无 |

### 每特征的最小验证路径

| 特征 | 验证方式 |
|---|---|
| AIO / 精选摘要 / PAA | 手工抽查（记录查看条件）；无标记级验证工具 |
| 结构化数据类（Product / Organization / Video） | [富媒体搜索结果测试](https://search.google.com/test/rich-results) + Search Console 增强报告 |
| 本地包 | 商家资料后台的搜索表现 + [local-grid-ranking.md](../monitoring/local-grid-ranking.md) 的网格抽查 |
| 视频 | VideoObject 经富媒体测试；观看页 `site:` / 视频站点地图核查 |
| 购物 | Merchant Center 后台诊断 + 商品状态 |

### 读表补充

- **AIO 专项**：AIO 的「优化入口」之所以只有可抓取 + 可索引 + 事实清楚，是因为 Google 明确说明无额外要求、无专门标记（[AI 功能文档](https://developers.google.com/search/docs/appearance/ai-features)）；真正能做的是被引用面的经营：可核对的数据、明确的出处、独立站点的提及——方法与证据见 [geo-evidence.md](../content/geo-evidence.md)，勿把本表当作「AIO checklist」。
- **组合读法**：同一次 SERP 里多个特征同时出现时，先按上文「读 SERP 组合」判意图，再决定争哪个特征：意图不对，单特征优化是浪费。
- **特征优先级**：对同一查询不可能全都要；按「我方页型与该特征的占据者页型是否同型」决定——同型可争，异型先补页型。

### 快速参考：特征 → 主要控制面

| 特征 | 主要控制面 |
|---|---|
| AIO / 精选摘要 / PAA | 内容与结构（无标记入口） |
| 本地包 | 商家资料 + 实体信息一致性 |
| 购物 | Merchant Center 数据 + Product 标记一致性 |
| 视频 / 图片 | 媒体资产、元数据、站点地图 |
| 知识面板 / 附加链接 | 实体与站点结构（全自动生成） |

## SERP 波动测量

- **Semrush Sensor**：0-10 日度波动分，0-2 低 / 2-5 正常 / 5-8 高 / 8-10 极高；可按 20+ 类目与设备拆分，支持对自己的查询集算 personal score（[官方](https://www.semrush.com/sensor)、[KB](https://www.semrush.com/kb/652-sensor)、[档位解读](https://seo.co/blog/rankings-volatility)）。
- **MozCast**：固定约 1 万查询的「气温」隐喻指数，温度越高越动荡（[对比说明](https://seo.co/blog/rankings-volatility)）。
- **自建指数（不依赖第三方时）**：固定查询集每日快照前十，算「位置变动比例」= 发生排名变化的 URL 数 ÷（查询数 × 10）；更精细用 Spearman footrule 距离。特征变化另计一列：任一特征的占据者变化记 1。
- **自建快照的操作步骤**：①固定查询集（30-100 个，含品牌词 / 非品牌词 / 各意图）→ ②固定查看条件（地域、语言、设备、个性化关闭或一致）→ ③每日同一时段抓取前十与特征清单 → ④入库为长表 → ⑤每周算位置变动比例与特征变化数，画时间线。
- **判读纪律**（接上文「不把相关性当因果」）：全行业 Sensor 高企 + 本站波动 → 先怀疑算法更新，查 Google [搜索状态面板](https://status.search.google.com/products/rGHU1u87FJnkP6W2WywE/history) 是否有公告；Sensor 平静 + 单页暴跌 → 优先查自身改动（技术、内容、canonical）。波动期的策略是记录而非立即改页（[Nightwatch](https://nightwatch.io/blog/serp-volatility-tracking)）。
- **混杂因素**：地域与设备个性化会让不同观察者看到不同 SERP；快照条件不固定时，「波动」里混着观察误差。快照必须锁定地域、语言、设备与采集时段。
- **疑似更新期的报告写法**：只陈述「日期区间、受影响查询数、特征变化数、涨跌分布」，归因等 1-2 周窗口过后再下；窗口内结论标注「待确认」。
- **类目分层**：Sensor 支持按行业类目看波动（[官方](https://www.semrush.com/sensor)）；本站查询集的类目与 Sensor 类目对齐后，行业波动与个体波动才可比。

## Feature 占有率追踪

- **查询集选取**：30-100 个目标查询，覆盖品牌词、核心非品牌词、各意图各页面类型；查询集一旦固定就不要中途增删（口径漂移会让时间线失效），要换集时另起一条基线。
- **指标定义**：对查询集 Q 与特征 F，`占有率 = 我方占据该特征的查询数 ÷ 实际出现该特征的查询数`（分母只算该特征真实出现的查询）；逐特征分别报，不合成单一分。
- **数据结构**：`date × query × feature × occupier_url × rank` 长表；人工抽查或排名工具导出皆可，必须记录查看条件（同上文监测规矩）。示例：

| date | query | feature | occupier_url | rank |
|---|---|---|---|---|
| 2026-10-09 | crm for nonprofits | featured_snippet | competitor.example/crm-nonprofits | 1 |
| 2026-10-09 | crm for nonprofits | video | youtube.com/watch?v=… | 4 |
| 2026-10-09 | best crm | shopping | merchant.example/crm | 2 |

- **告警规则**：占据者易主；某特征对我方查询集整体消失（先排查是功能调整还是竞争失利，见上文监测条目）；精选摘要连续 N 日丢失。
- **与排名合并读法**：占有率时间线叠自然排名时间线看——排名稳但占有率掉，多为 SERP 版式变化（新特征挤占）而非页面问题；排名与占有率同掉，才回查页面与技术。
- **报告口径**：Share of Voice 类指标在 AccuRanker、Semrush 等工具中常见内置，AIO 追踪在近年工具中已普遍纳入（[工具对比](https://nathanojaokomo.com/blog/best-rank-tracking-tools)、[Semrush 排名追踪](https://www.semrush.com/features/rank-tracking/)、[cloro.dev 方法](https://cloro.dev/blog/serp-features-tracking)）；自建时写清分母定义，避免与工具口径混用。

### 深读轮补充误区

- 用「某特征出现次数」当 KPI：分母（该特征本来出现多少次）没记录，涨跌无从解释。
- 拿不同查看条件（地域/设备/日期）的两张快照对比，把正常波动当成易主。
- 把 AIO 占有率与传统 SoV 合成一个分数：两种位置的点击含义完全不同。

### 来源补遗

[Google 本地排名官方文档](https://support.google.com/business/answer/7091)、[SeekToAction 关键片段官方博客](https://developers.google.com/search/blog/2021/07/new-way-key-moments)、[Google AI 功能文档](https://developers.google.com/search/docs/appearance/ai-features)、[Semrush PAA 研究](https://www.semrush.com/blog/how-to-maximize-people-also-ask-seo-opportunities-study)、[Moz 精选摘要](https://moz.com/blog/optimize-featured-snippets)、[Frase 精选摘要](https://www.frase.io/blog/how-to-optimize-for-featured-snippets-on-google)、[Nightwatch 精选摘要](https://nightwatch.io/blog/optimize-for-featured-snippets)、[Search Engine Land 视频 SERP](https://searchengineland.com/guide/how-to-win-video-driven-serps)、[Semrush Sensor](https://www.semrush.com/sensor)、[Sensor KB](https://www.semrush.com/kb/652-sensor)、[SEO.co 波动档位](https://seo.co/blog/rankings-volatility)、[Nightwatch 波动应对](https://nightwatch.io/blog/serp-volatility-tracking)、[cloro.dev 特征追踪](https://cloro.dev/blog/serp-features-tracking)、[排名追踪工具对比](https://nathanojaokomo.com/blog/best-rank-tracking-tools)、[Semrush 排名追踪](https://www.semrush.com/features/rank-tracking/)、[Google 搜索状态面板](https://status.search.google.com/products/rGHU1u87FJnkP6W2WywE/history)
