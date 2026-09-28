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
3. **规范化**：只有内容确实重复或近似重复时（例如参数、打印版），才用 `rel="canonical"` 指向首选 URL；它不能替代合并。
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

## 交付物

1. 主题地图：Pillar 到各 Cluster 页的树状结构。
2. 查询 → URL 映射表：查询、意图、负责的 URL、状态（已有 / 待写 / 待合并）。
3. 现有内容处置表：保留、改写、合并（附 301 目标）、下线。
4. 内链矩阵：每页必须链到哪些页，用什么锚文本方向。
5. 发布顺序与负责人。
6. 衡量口径和复盘时间点。

汇总格式可参考 [content-strategy-plan.md](../../templates/research/content-strategy-plan.md)。

## 常见误区

- 把关键词的每个变体都做成一页。批量生产价值很低的页面，可能落入 Google 垃圾内容政策里「门页」或「大规模滥用内容」的范围。
- Pillar 只有一排链接，没有实质内容。
- 链接全堆在页脚或侧栏，正文里没有。
- 用 canonical 掩盖本该合并的重复页面。
- 只加新页、不回头更新 Pillar 和旧页的链接。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · research/keyword-research/references/topic-cluster-templates.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/research/keyword-research/references/topic-cluster-templates.md)（Apache-2.0）
- 一手资料：[可抓取链接与锚文本](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)、[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)、[重定向](https://developers.google.com/search/docs/crawling-indexing/301-redirects)、[垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)
