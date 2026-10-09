# Competitor Page Patterns

## 适用场景
- competitor alternative page
- alternatives list page
- you vs competitor
- competitor vs competitor
- 销售支持型 SEO 页面集规划

区块怎么写见 [competitor-section-templates.md](competitor-section-templates.md)，竞品数据怎么集中维护见 [competitor-content-architecture.md](competitor-content-architecture.md)。

## 四种核心格式

### 1. Singular alternative
- 搜索意图：用户已在寻找某个竞品的替代方案
- 常见关键词：`[Competitor] alternative`、`alternative to [Competitor]`
- 常见结构：痛点验证 → 你作为替代方案 → 详细对比 → 适合谁/不适合谁 → 迁移路径 → 证据 → CTA

### 2. Plural alternatives
- 搜索意图：用户处于方案调研期
- 常见关键词：`[Competitor] alternatives`、`best [Competitor] alternatives`
- 常见结构：为什么找替代方案 → 评估标准 → 替代方案列表 → 汇总对比 → 分场景推荐 → CTA
- 原则：列出多个真实可选的替代方案（常见做法是四到七个），而不是只写自己。

### 3. You vs competitor
- 搜索意图：用户直接比较两个品牌
- 常见关键词：`[You] vs [Competitor]`、`[Competitor] vs [You]`
- 常见结构：TL;DR → 对比表 → 维度展开 → 谁适合你 → 谁适合对手 → 迁移支持 → CTA

### 4. Competitor vs competitor
- 搜索意图：用户比较两个竞品，但你并非直接比较对象
- 常见结构：双方概述 → 分类对比 → 各自适合谁 → 第三选项引入你 → 三方对比 → CTA

## 页面级原则
- 诚实承认竞品优势，不要歪曲对方功能。
- 不要只堆 feature table；要解释差异为何重要。
- 明确每个方案适合的人群与不适合的人群。
- 价格、功能等事实注明核对日期和来源，过期就更新或删掉。
- comparison 内容要可模块化维护，避免每页手工重复更新。

## SEO 与信息架构要求
- 规划 alternatives hub 与 vs/comparison hub。
- 建立 competitor 数据单一事实源，统一维护定价、功能、优缺点、迁移信息。
- individual page 与 hub page 双向内链。
- 从 feature pages、solution pages、footer 向高优先级 comparison pages 分发内部链接。
- 页面上有真实问答时可以用 FAQPage 描述，但按 [geo-evidence.md](../content/geo-evidence.md) 的记录，Google 已停止展示 FAQ 富结果，不要把它当作流量手段。

## 输出要求
默认应输出：
1. 页面集范围与优先级
2. URL pattern 建议
3. 目标关键词与搜索意图
4. 每种页面模板骨架
5. 内链与 index page 方案
6. 需要集中维护的 competitor data 字段

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/competitor-alternatives](https://github.com/coreyhaines31/marketingskills/tree/v1.10.0/skills/competitor-alternatives)（MIT）

## 竞品页型逆向工作流（深读 2026-10-09）

四种核心格式是产出模板；本节是产生它们的方法：拿到一个竞品域，怎么系统拆出页型、标题公式、深度分布与 SERP 对照。骨架参考 [Semrush 竞品内容分析](https://www.semrush.com/blog/competitive-content-analysis)、[HubSpot 竞品 SEO 工作流](https://blog.hubspot.com/marketing/seo-competitor-analysis)、[The Blueprint Training 八步框架](https://theblueprint.training/seo-competitive-analysis)。

### 第 1 步：URL 聚类（URL 列表 → 页型）

1. **拿全 URL 清单**：竞品 sitemap.xml（含 sitemap index）、分页列表页、或排名工具的「竞品有排名的 URL」导出。工具不拘，数据到位即可。
2. **按 URL pattern 正则分桶**，典型桶：

| path 模式 | 通常对应页型 |
|---|---|
| `/alternatives/`、`/compare/`、`/vs/` | 对比 / 替代方案页（本文件四种格式的落点） |
| `/blog/`、`/resources/`、`/guides/` | 内容 / 教育页 |
| `/integrations/`、`/use-cases/`、`/solutions/` | 解决方案页 |
| `/pricing/`、`/features/`、`/product/` | 产品 / 商业页 |
| `/glossary/`、`/templates/`、`/tools/`（常为程序化） | 长尾资产页 |

3. **算每桶规模指标**：URL 数、目录深度分布、发布频率（sitemap lastmod 或页面日期）。URL 数最多的桶通常是竞品自然搜索的增长引擎。
4. **兜底**：URL 无规律（哈希、短 slug）时退回「按入口页聚类」：每桶抽样约 10 页人工标注页型，再按共享区块顺序归并。同类工具的做法是把竞品 URL 分成 product / tool / hub / comparison / commercial 等页型并看哪类带流量（[Manus](https://manus.im/solutions/seo/competitor-analysis)）。

### 第 2 步：标题公式提取

对每桶抓取 `<title>` 与 `<h1>`，做槽位化归纳：

- 可变部分换成变量：`Best {Category} Tools in {Year}: {N} Picks` → 变量 = Category / Year / N。
- 统计修饰符频率：best / top / free / alternative / vs / for {use case}；出现次数即竞品标题策略的权重。
- 记录长度分布（字符数与像素宽），取中位数而非平均值，避免单页极值带偏。
- 产出「标题公式卡」：每桶 1-3 个公式 + 使用频率 + 对应意图；写法接 [title-formulas.md](../content/title-formulas.md) 与 [meta-tag-formulas.md](../content/meta-tag-formulas.md)。

### 第 3 步：内容深度分布图

每桶抽样（大桶按流量或外链加权抽样，小桶全采），每页记录：字数、H2/H3 数、表格数、图片/视频数、FAQ 数、内链数。产出**分布**而非单点：

- 每指标给 min / P25 / 中位 / P75 / max，画分位数表或箱线图。
- 三方对齐比较：同一关键词 SERP 前十页的深度指标 vs 竞品桶分布 vs 我方对应页。通行做法即拉 SERP 前 10 页记录字数与标题结构、算竞品基准再对比自己（[The Blueprint Training](https://theblueprint.training/seo-competitive-analysis)、[Cited 指南](https://cited.so/blog/keyword-research-and)、[Traffic Torch](https://traffictorch.net/keyword-vs-tool)）。
- 解读纪律：字数是**覆盖度代理指标**，不是排名因子；深度显著低于竞品 P25 且话题覆盖缺项，才是补深度的理由；超过竞品 P75 仍无引用与结构，问题不在长度。

### 第 4 步：SERP 特征对照表（模板）

对目标查询集逐个记录，列定义：

| 列 | 内容 |
|---|---|
| query | 目标关键词 |
| intent | 信息 / 商业 / 交易 / 导航，见 [keyword-intent-taxonomy.md](keyword-intent-taxonomy.md) |
| features | 该 SERP 出现的功能（AIO / 精选摘要 / PAA / 本地包 / 购物 / 视频…见 [serp-feature-taxonomy.md](serp-feature-taxonomy.md)） |
| occupier_url（每功能一列） | 各功能由哪个 URL 占据 |
| occupier_page_type | 占据者属于第 1 步的哪个桶 |
| occupier_depth | 占据者的字数 / 结构指标（接第 3 步口径） |
| my_gap | 无对应页型 / 有页但深度或结构落后 / 可争夺 |
| 记录条件 | 日期、地域、语言、设备（功能组合随这些变化） |

### 第 5 步：输出格式（页型卡）

每桶一张「页型卡」，并入上文「输出要求」的交付物：

1. **URL pattern 建议**：路径模板 + slug 规则。
2. **标题公式卡**（第 2 步产出）。
3. **结构骨架**：区块顺序（接四种核心格式的结构）。
4. **深度目标**：各指标 P50-P75 区间，注明是「覆盖度目标」而非字数 KPI。
5. **内链规则**：入链来源桶与锚文本模式。
6. **优先级分**：机会（桶查询量 × 我方缺口）× 可行性（数据可维护性），方法见 [scoring-calibration.md](scoring-calibration.md)。
7. **数据字段**：竞品事实（定价 / 功能）接 [competitor-content-architecture.md](competitor-content-architecture.md) 的单一事实源；区块文案接 [competitor-section-templates.md](competitor-section-templates.md)。

### 常见坑

- 只看 URL 数最多的桶，忽略「URL 少但单页带量大流量」的高价值页型（结合流量或外链加权再看一遍）。
- 把标题公式当模板硬抄，丢掉自己的差异化定位；公式抄结构，不抄主张。
- 用平均值定深度目标：一个 8000 字 outliers 会把均值拉高一倍，用中位数与分位数。
- 逆向一次就固化：竞品改版后公式与深度基准过期，季度级重跑第 1-3 步（页面变迁取证可用 Wayback CDX，见 [serp-feature-taxonomy.md](serp-feature-taxonomy.md) 的方法）。
- 聚类只按 URL：同一 URL 模板下可能混着两种意图（如 /blog/ 里的对比文与教程文），抽样标注兜底。
- 输出只给页面清单不给「为什么」：每张页型卡必须附 SERP 证据（对照表行）与深度依据，否则无法排优先级。

### 最小可行版本（快速通道）

时间只够半天时：取竞品 sitemap → 正则分桶（第 1 步）→ 每桶抽 3 页抓 title/H1/字数（第 2-3 步缩水版）→ 对 10 个核心查询填 SERP 对照表 → 只输出 2 张最高优先级页型卡。宁可页型卡少而证据全，不要全覆盖而无证据。

### 工具映射（不绑定具体产品）

| 步骤 | 需要的能力 | 常见来源 |
|---|---|---|
| URL 清单 | sitemap 解析 / 已知 URL 列表 | sitemap.xml、排名工具导出、Screaming Frog 抓取 |
| 标题抓取 | 批量取 title/H1 | 爬虫导出、简单脚本 + 渲染 |
| 深度统计 | 字数 / 标题数 / 媒体数 | 爬虫导出列（如 Word Count）+ 自行统计分位数 |
| SERP 对照 | 特征与占据者记录 | 排名追踪工具导出、手工抽查（记录查看条件） |

### 来源补遗

[Semrush 竞品内容分析](https://www.semrush.com/blog/competitive-content-analysis)、[Semrush 内容差距分析](https://www.semrush.com/blog/content-gap-analysis)、[Ahrefs 内容差距模板](https://ahrefs.com/blog/content-gap-analysis)、[The Blueprint Training 八步框架](https://theblueprint.training/seo-competitive-analysis)、[Cited 关键词研究指南](https://cited.so/blog/keyword-research-and)、[Traffic Torch 深度对标](https://traffictorch.net/keyword-vs-tool)、[Manus 页型分类](https://manus.im/solutions/seo/competitor-analysis)、[HubSpot 竞品 SEO 工作流](https://blog.hubspot.com/marketing/seo-competitor-analysis)
