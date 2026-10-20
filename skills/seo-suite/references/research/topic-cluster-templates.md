# 主题集群（Pillar / Cluster）规划

## 用途与何时读

规划一个主题下的一组页面、梳理已有文章的归属、排查多个页面抢同一批查询时读。内容战略层面的主题选择见 [content-strategy-framework.md](content-strategy-framework.md)，意图判定见 [keyword-intent-taxonomy.md](keyword-intent-taxonomy.md)。

主题集群的价值在于：用户能顺着一个主题找全答案，搜索引擎能顺着链接发现并理解这些页面。它不是获得「主题权威」加分的固定公式，页面各自仍要有独立价值。

## 核心概念

- **Pillar（总览页）**：回答主题的全貌，每个子问题讲到够用，并把读者引向深入页。它本身要有实质内容，不能只是链接目录。
- **Cluster 页（深入页）**：只解决一个子问题，对准一组意图相同的查询，讲得比总览页深。
- **一页一意图**：两个查询的 SERP 前列结果大量重合、页面类型相同，通常归同一页；结果差异明显，就分页。重合多少算「大量」没有通用阈值，按市场自己判断并记录依据。

## 选组织维度

| 维度 | 适合的情况 | 例子（占位） |
|---|---|---|
| 按子问题 | 概念类主题，子问题之间相对独立 | 某概念的定义、原理、常见做法、工具、误区 |
| 按水平 | 有明显由浅入深路径的技术主题 | 入门配置 → 常见模式 → 高级调优 |
| 按人群或场景 | 产品和服务类主题，不同人群需求差异大 | 面向小团队、面向企业、面向某个行业 |
| 按步骤 | 流程长、每一步都值得单独展开 | 调研 → 计划 → 执行 → 衡量 |

维度可以组合，但一个集群内只用一个主维度，否则页面边界会互相重叠。

## 防止关键词互相抢位

**信号**：Search Console 效果报告里同一查询由多个 URL 轮流获得展示，排名在它们之间来回跳；或者两页标题和 H1 几乎一样。查看需要你自己的 Search Console 权限。

**处理**（按优先顺序考虑）：

1. **合并**：两页意图相同时，把有用内容并到更强的那页，旧 URL 做 301 到新页。
2. **重新分工**：两页意图其实不同时，调整标题、H1 和正文重点，让每页只回答自己那组查询。
3. **规范化**：只有内容确实重复或近似重复时（例如参数、打印版），才用 `rel="canonical"` 指向首选 URL。Google 把 301 重定向和 `rel="canonical"` 都列为「strong signal」，把 sitemap 收录列为弱信号（[规范网址文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)，核对 2026-10-21）；canonical 只表达偏好，不能替代合并两页的内容。
4. **内链统一**：站内提到这组查询时，锚文本一律指向负责它的那一页。

预防办法是维护一张**查询 → URL 映射表**，每个查询只归一个 URL，新建页面前先查表。

## 内链规则

- Pillar 链到每个 Cluster 页；每个 Cluster 页链回 Pillar。
- Cluster 页之间只在语境相关的地方互链，不为凑数量加链接。
- 链接放在正文里，使用可抓取的 `<a href>`；锚文本写清目标页讲什么，不用「点这里」「更多」。
- 新页上线时同步检查：有没有至少一个站内页面链接到它，避免孤儿页。
- 用面包屑和分类导航体现层级；站点级链接结构见 [link-architecture-patterns.md](../technical/link-architecture-patterns.md)。

不设固定的每页链接数，以读者此处是否需要这条链接为准。

## 规划步骤

1. **定主题**：和业务直接相关、你能提供一手经验或数据的主题优先。
2. **收查询**：从 Search Console、站内搜索、客服与销售问题、关键词工具（需要你自己的账号）收集候选查询。
3. **聚类**：按意图和 SERP 重合度把查询分组，每组对应一个 URL。
4. **盘点现有内容**：每篇已有文章标记为保留、改写、合并或下线，决定后再写新页。
5. **定 URL 与层级**：写出 Pillar 和各 Cluster 页的 URL、标题方向和目标查询组。
6. **设计内链**：按上面的规则画出链接矩阵。
7. **排发布顺序**：Pillar 先上线或与首批深入页同时上线；先做需求明确、你最有把握的子问题。
8. **定衡量口径**：按集群（URL 目录或自定义分组）看展示、点击、覆盖到的查询和转化；复盘节奏按内容更新频率定。

**新站版：先收词，再建站**（还没有 Search Console 数据、域名和首页都还没定的时候；社区经验，来源 X @qianshuixia2026 2026-10-17，2026-10-17 并入）。常见的错误顺序是先拍脑袋买域名、搭首页，再回头想要做哪些词。新站按下面的顺序倒推，让每个页面从第一天起就对着具体的搜索需求：

1. **多入口收词**：Google 搜索框下拉、结果页底部的相关搜索、Google Trends、Keyword Planner，以及 Similarweb / Semrush / Ahrefs 这类工具（需要你自己的账号）。工具型需求可用词根拓词，见 [keyword-intent-taxonomy.md](keyword-intent-taxonomy.md)「新站选词」一节。
2. **补全月搜索量和趋势**：量和趋势同一工具取数，标注口径和取数日期。
3. **剔除无关词，合并同义意图**：同一意图的不同说法归成一组，不按字面拆。
4. **按搜索意图分组**：对应上面第 3 步的聚类，每组对应一个 URL。
5. **定页面形态**：工具、教程、对比、列表……按意图和 SERP 实际形态选。
6. **生成第一批 URL 清单**：同上面第 5 步。
7. **人工剔除薄内容页**：撑不起独立内容的变体并入父页或直接放弃，不为凑数量开页。
8. **先上最有把握的 5–10 个核心页**：其余排队，上线后按第 8 步的口径看数据再扩。

和上面八步的差别：收查询不靠 Search Console；多了「人工剔除薄内容页」这道闸；首批只上 5–10 页。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 没有两个页面抢同一查询 | GSC 导出「查询 × 页面」，运行 `python3 scripts/gsc_mining.py matrix.csv --mode matrix`，看「蚕食」段 | 同一查询 ≥2 个页面且最大展示 ≥20 的条目已处理（合并或重新分工） |
| 两组查询该不该共用一页 | `python3 scripts/serp_overlap.py input.csv`（`keyword,url1;url2;…`） | 共享 ≥4 条前 10 URL：并页或同簇；≤1 条：分页。阈值为来源仓约定 |
| 没有孤儿页 | `python3 scripts/site_crawl.py <站点> --out crawl.json`，再 `python3 scripts/link_graph.py --crawl crawl.json` 看入链 0–1 清单 | 新建的 Pillar / Cluster 页都有至少一个站内入链 |
| 孤儿页的修复建议 | `python3 scripts/orphan_fix.py --crawl crawl.json` 输出「源页 → 孤儿页 → 建议锚文本」 | 每个孤儿都有源页，或标明需导航级入口 |
| 已有内容有处置结论 | `python3 scripts/content_inventory.py --crawl crawl.json --gsc <导出.csv>` 给 keep / update / consolidate / remove 四桶草稿 | 合并和下线的页面都有 301 目标 |
| 每个查询只归一个 URL | 查询 → URL 映射表按查询列去重 | 无重复查询行 |

## 交付物

1. 主题地图：Pillar 到各 Cluster 页的树状结构。
2. 查询 → URL 映射表：查询、意图、负责的 URL、状态（已有 / 待写 / 待合并）。
3. 现有内容处置表：保留、改写、合并（附 301 目标）、下线。
4. 内链矩阵：每页必须链到哪些页，用什么锚文本方向。
5. 发布顺序与负责人。
6. 衡量口径和复盘时间点。

汇总格式可参考 [content-strategy-plan.md](../../templates/research/content-strategy-plan.md)。

## 常见误区

- 把关键词的每个变体都做成一页。批量生产价值很低的页面，可能落入 Google 垃圾内容政策里 Doorway abuse（为排名相近查询而建的页面）或 Scaled content abuse 的范围（[垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)，核对 2026-10-21）。
- Pillar 只有一排链接，没有实质内容。
- 链接全堆在页脚或侧栏，正文里没有。
- 用 canonical 掩盖本该合并的重复页面。
- 只加新页、不回头更新 Pillar 和旧页的链接。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · research/keyword-research/references/topic-cluster-templates.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/research/keyword-research/references/topic-cluster-templates.md)（Apache-2.0）
- 一手资料：[可抓取链接与锚文本](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)、[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)、[重定向](https://developers.google.com/search/docs/crawling-indexing/301-redirects)、[垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)
- 新站版「先收词，再建站」：[X @qianshuixia2026 2026-10-17](https://x.com/qianshuixia2026/status/2111268767342997847)（整理哥飞公众号文章的二手笔记，社区经验；2026-10-17 并入）

---

# (Affitor 深读 2026-10-09c)

补充吸收 Affitor/affiliate-skills（52 技能，S1 研究 → S3 博客与 SEO 飞轮）中主题集群与内容规划的增量做法。此前已吸收其内容护城河公式（见 [keyword-intent-taxonomy.md](keyword-intent-taxonomy.md)），此处不重复。

**本节所有权重、阈值、比例都是来源仓的约定值（2026-10-21 抽查其 `seo-strategy.md`、`niche-opportunity-finder`、`content-angle-ranker`、`purple-cow-audit`、`case-studies.md`，数字与来源一致），不是 Google 规则，没有外部校准。** 按「本套件口径」使用，首次使用先在自己的数据上试跑，再决定是否沿用。

## 选题先于建簇：利基四道闸

建簇之前先过利基闸（monopoly-niche-finder / niche-opportunity-finder / purple-cow-audit）：

- **交集利基**：`领域 A × 领域 B`（如「房产中介 × AI 工具」），两条测试决定去留——具体到能成为该主题第一资源，又宽到有 ≥10K 月搜索可变现。
- **热情上限测试 = 集群规模可行性**：问自己能否围绕它写 50+ 篇而不倦。与护城河公式联用：护城河目标页数 > 热情上限 → 收窄利基再算，而不是硬扛。
- **利基评分权重**：搜索需求 30% × 联盟计划可得性 30% × 竞争 25% × 内容潜力 15%；7.5+ 高机会 / 5.5-7.4 值得试 / <5.5 放弃。候选分三层生成：趋势型 / 常青型 / 微利基（垂直 × 人群）。
- **产品闸（Purple Cow）**：进簇的变现产品先打分（独特性 20%/质量 20%/故事 15%/口碑 15%/设计 10%/问题契合 10%/信任 10%）：8-10 全力推、6-7 需要独特角度、4-5 只有佣金极佳才推、1-3 跳过。判官问题：「没有佣金我也愿意推荐给朋友吗？」——得分 <6 的产品不值得为它建簇。

## 建簇程序与簇卡片（keyword-cluster-architect）

- **种子四型**：产品型（"[product] review"、"best [category]"）、问题型（"how to [问题]"）、对比型（"A vs B"、"alternatives to A"）、教程型（"how to use [product]"）。
- **扩词检索式**：精确引号搜种子看 related searches 与 People Also Ask；`"[seed] guide" OR "[seed] tutorial"` 捞信息型变体；`"best [seed]" OR "[seed] review"` 捞商业型变体。按深度收 50-200+ 词。
- **意图分流**：I → 教程/博客、C → 对比/评测、T → 落地页、N（品牌导航词）→ 直接丢弃，不是你的流量。
- **簇卡片字段**：簇名 / 意图（I·C·T）/ Hub 词（簇内最高量词）/ 支撑词列表（各带估量）/ 内容型 / 优先级 1-5。
- **Hub 选择**：最宽、最高量的簇做 Hub，其余簇做 Spoke 链回。**Hub:Spoke = 1:5-15，攒够 5+ 个 spoke 再建 Hub 页**——与本文「Pillar 先上线」的调和：规划时 Pillar 先定（URL 与标题方向锁定），页面可等首批 spoke 就绪再上线或同期上线，避免只有一个空目录页挂着。
- **优先级公式**：`Priority = (Volume × Intent) ÷ Competition`。排产顺序：商业意图簇先行（收入），信息型簇殿后（流量与权威）。
- **两条质量规则**：词太多时激进合并——聚类质量 > 关键词数量；整个利基捞不到商业意图词 → 变现困难，明标记并评估相邻利基。
- **自检**：每个簇基于真实搜索数据而非臆测；总内容量与产能现实匹配（对照护城河分档）。

## 写前角度层：N 个来源 → N 个角度

每篇集群内容动笔前先过研究层（content-research-brief / content-angle-ranker / trending-content-scout）：

- **研究优先**：收 5-10 个真实来源（先抓 15-20 再筛）。反幻觉约束：每个数字可回溯到具体来源 URL；来源标注 fetch_status（full / snippet）；全文抓取成功 <3 篇即数据质量告警；全部来源同视角（全是好评）= 偏差告警，补 Reddit/批评视角。
- **角度规则**：N 个来源生成 N 个角度——每个角度以**不同主源**为基础、全部来源作背景、至少 1 个反向角度。
- **角度评分**：`angle_score = 平台契合×0.25 + 竞争度(越少越高)×0.30 + 互动预测×0.30 + 创作者契合×0.15`，生成 8-12 个候选。分数必须拉开（极差 <1 分即失败，重打）；呈报按 Quick Win（最快高分）/ Best Bet（最高分）/ Contrarian（最高分反向角度）三轨。
- **缺口六型**（找角度的入手处）：格式缺口 / 平台缺口 / 角度缺口（评论区高频疑问无人答）/ 受众缺口 / 时效缺口（头部内容 6 个月+ 旧）/ 诚实度缺口（全网皆吹 → 讲缺点即差异化）。
- **互动分统一公式**（跨平台可比）：`(likes×2 + comments×3 + shares×5) ÷ max(views,1) × 1000`；输出必须标注数据来源是 API 还是 web_search 估算。

## 一篇旗舰 → 15-30 个平台原生碎片

Pillar 写完后不是终点（content-pillar-atomizer）：抽出 5-8 个「原子单元」（可独立成立的洞见），改造成各平台原生碎片。分配**按互动潜力成比例**而非平均——某平台互动是另一平台 5 倍就按 5:1 产出。每件碎片独立成立、平台原生、只带一个洞见。

## 集群维护：衰减刷新与内链时效

- **刷新优先级** = 收入影响 × 衰减严重度 × 修复容易度（反向计分） × 竞品威胁。分级：P0 本周（排名掉 + 高流量页）、P1 本月（过期定价/功能、竞品发了更好版本）、P2 排期（缓慢下滑）、P3 观察 2 周。
- **刷新动作里含补内链**：上线后新增的相关页此时互链。月度节奏：第 1 周 P0、第 2 周 P1、第 3 周按衰减分析暴露的缺口写新内容、第 4 周内链复查。
- **内链时效规则**（来源仓约定；Google 文档没有给出入链时限或点击深度上限）：新页上线 48 小时内获得站内入链；每季度做孤儿页复查；反链最多的老页链到你最想排的新页；任何页距首页 ≤3 次点击。Google 对内链的要求见 [可抓取链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)。

## 飞轮闭环：规划是一次循环不是一张图

- `seo-audit` 的 ranking_gaps 回流建簇技能 → 加词、加页填缺口；`performance-report` 的实际表现回流更新角度评分权重与格式偏好。
- 工程做法：每步产出带 `chain_metadata.suggested_next`，且分析类技能的建议下一步必须指回研究类技能——保证闭环不断链。

## 案例自述（Affitor case-studies，不作基准）

来源仓 `case-studies.md` 的案例备注里写了：对比文（"Semrush vs Ahrefs"）转化约为单篇评测的 3 倍；5 篇文章约 $3,000/月；建议用实际转化率做基准，并称 1–5% 为典型值。这些是案例自述，没有样本量和方法，不能当通用基准，也不用来承诺排期。该案例还把精选摘要归因于 FAQ 加 schema：Google 文档写明精选摘要无法申请（见 [serp-feature-taxonomy.md](serp-feature-taxonomy.md)），FAQ 富结果也已在 2026-05-07 停止展示，这一条不采信。

### 来源（Affitor 深读 2026-10-09c）

- [Affitor/affiliate-skills](https://github.com/Affitor/affiliate-skills)（MIT）`skills/blog/keyword-cluster-architect/SKILL.md`、`skills/blog/content-decay-detector/SKILL.md`、`skills/blog/affiliate-blog-builder/SKILL.md`、`skills/content/content-research-brief/SKILL.md`、`skills/content/content-pillar-atomizer/SKILL.md`、`skills/research/content-angle-ranker/SKILL.md`、`skills/research/trending-content-scout/SKILL.md`、`skills/research/monopoly-niche-finder/SKILL.md`、`skills/research/niche-opportunity-finder/SKILL.md`、`skills/research/purple-cow-audit/SKILL.md`、`shared/references/seo-strategy.md`、`shared/references/flywheel-connections.md`、`shared/references/case-studies.md`
- 与本文既有规则的分工：SERP 重叠分档、蚕食严重度、执行记分卡见 [keyword-intent-taxonomy.md](keyword-intent-taxonomy.md)；内链架构见 [link-architecture-patterns.md](../technical/link-architecture-patterns.md)。
