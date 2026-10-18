# 常见页面类型的结构要点

> 涉及 GEO / AI 引用的判断，先读 [geo-evidence.md](geo-evidence.md)。下面的结构是为了让读者更快找到答案，不承诺 AI 引用或排名提升。

## 用途与何时读

写内容简报、起草或改版教程、清单、对比、评测、术语页、落地页时读。先按 SERP 前列确定页面类型，再用下面的骨架查有没有漏掉关键区块。

- title、H1、首段用买家原词，首段第一句直接回答：见 [question-alignment.md](question-alignment.md)。
- 标题写法见 [title-formulas.md](title-formulas.md)。

## 通用要求

出处核对日期 2026-10-18。查法和通过标准见文末检查清单。

- **篇幅由问题决定，不凑字数。** Google 有用内容自查把「因为听说 Google 偏好某个字数而按字数写」列为警示信号，并注明没有偏好的字数（[有用内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)）；入门指南说内容长度本身不影响排名（[SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)）。
- **开头先回答。** Bing 指南第 18 条：关键信息放前面，不写长引言（[Bing 指南](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)）。首段写法见 question-alignment.md。
- **一个清楚的主标题。** Google 标题链接文档：主标题放在第一个可见的 `<h1>`，最醒目（[标题链接](https://developers.google.com/search/docs/appearance/title-link)）。入门指南：标题的数量和顺序对 Google 搜索没有影响。
- **标题层级反映内容结构。** Bing 指南第 13 条要求逻辑的标题层级；入门指南说语义顺序方便屏幕阅读器。不为塞关键词加标题。
- **步骤和比较用真实元素。** 用 `<ol>`、`<ul>`、`<table>`，不用图片或样式模拟。Bing 指南第 13 条要求语义 HTML 元素。
- **写出信任信息。** Google 有用内容的 Who / How / Why：署名、作者介绍、内容怎么做出来（评测写测了多少产品、怎么测、附证据）。
- **链接**（本套件口径）：内链指向上下游页面；外链优先指向一手来源。
- **FAQ 只收真实问题。** FAQ 富结果自 2026-05-07 起不再显示（[Search Console 数据异常页](https://support.google.com/webmasters/answer/6211453)）。问题来源见 question-alignment.md 第二节。
- **结构化数据与可见内容一致。** 不要标记读者看不到的内容；类型选最具体的（[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)）。

## 改版页：IST/SOLL 对比骨架

改版页先写 **IST**（现有区块树），再写 **SOLL**（目标骨架）。以下是本套件口径。

- SOLL 的三个输入：SERP 前列的主流页型、内容缺口、最弱的读者画像（画像方法见 [content-patterns.md](content-patterns.md) SXO 节）。
- 占位符要具体。不写「加 CTA」，写「hero 下加带年费节省徽章的定价按钮，链到 /pricing#enterprise」。
- FAQ 区填真实问题：「其他人还问了」原文、工单原话。
- 移动端 375px 宽的首屏放该页型最关键的元素：工具页放输入区，产品页放价格和购买按钮。
- SERP 前列以某一页型为主时，先做成那种页型，再优化内容。

## 各类页面的必备区块

### 教程 / 操作指南

结果预览 → 前提条件（工具、权限、版本）→ 编号步骤 → 如何确认成功 → 常见报错与排查 → 下一步

- 步骤用 `<ol>`。每个 `<li>` 只有一个动作，并写出预期结果。需要时配截图或代码。
- 写明适用版本和测试日期。界面变化后更新。
- 有「如何确认成功」一节。

### 清单 / 盘点（「最好的某类产品」）

选择标准与测试方法 → 速览表 → 逐项介绍（适合谁、优缺点、价格及核对日期）→ 怎么选 → 利益关系披露

- 每项都有实际使用或测试的证据，不是改写各家官网。
- 推荐某项为「最佳」时，写出理由和第一手证据（[Google 评测指南](https://developers.google.com/search/docs/specialty/ecommerce/write-high-quality-reviews)，核对 2026-10-18）。
- 清单本身内容足够，即使另有单品评测页，也能独立成立（同上）。
- 可以给多个购买渠道的链接（同上）。
- 有联盟链接时，按所在地法规披露；Google 对联盟页的立场见其垃圾内容政策中的 thin affiliate 一节。

### 对比（A vs B）

结论先行 → 对比表 → 分维度展开 → 各自适合谁 → 价格口径 → 真实常见问题

- 写出「选另一方更合适」的情形。
- 对比表写核对日期和价格口径。
- 自家产品和竞品同页时，区块写法见 [competitor-section-templates.md](../research/competitor-section-templates.md)。

### 评测（单个产品）

测评对象、版本和使用时长 → 测试方法 → 关键发现（附照片、数据、截图）→ 优缺点 → 与替代品比较 → 适合与不适合的人 → 结论

按 [Google 评测指南](https://developers.google.com/search/docs/specialty/ecommerce/write-high-quality-reviews)（核对 2026-10-18）逐项查：

- 有自己使用过的证据：图片、音频或其他链接。
- 有量化测量。
- 写出与竞品的差异，以及与上一代产品相比的变化。
- 优缺点基于自己的研究。
- 用评分时说明评分方法（本套件口径）。

### 术语 / 概念页

开头一两句定义 → 展开解释 → 具体例子 → 容易混淆的概念 → 相关术语链接

- 定义单独摘出来也能读懂，不依赖上下文。
- 每页都有例子和解释。批量做术语页时抽查，避免只有一句话的薄页。

### 落地页 / 产品页

首屏价值主张（是什么、给谁、主要收益）→ 证据（客户、数据、演示）→ 按用户任务组织的功能 → 价格或获取方式 → 常见顾虑 → 行动按钮

- `python3 scripts/above_fold.py URL`：首屏 700 个字符的四元素评分，≥ 70 通过（本套件口径）。
- Product 结构化数据中的价格、库存和页面一致。
- 首屏不堆口号。读者要能直接看出是否适合自己。

### 总览页（Pillar）

目录 → 各子主题的要点概述 → 链接到深入页 → 下一步阅读

- 每个子主题讲到够用，深入内容交给专门页面。规划方法见 [topic-cluster-templates.md](../research/topic-cluster-templates.md)。

### 排障 / 问答页

按问题分组 → 每个问题：现象 → 原因 → 解决 → 如何确认已解决

- 每个问题有稳定的锚点（`id`），方便从其他页面直接链到答案。
- 报错信息原文照录，方便读者用报错搜索时找到。
- 问题标题用用户原话，见 question-alignment.md。

## 检查清单（发布前）

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 页型 | 记录 SERP 前 10 名的页型（方法见 content-patterns.md SXO 节） | 通过：与主流页型一致，或写明差异的理由。失败：错页型 |
| 首段回答核心问题 | 读首段第一句；`above_fold.py URL` | 通过：第一句是答案，首屏评分 ≥ 70。失败：背景开头或评分 < 70 |
| 主标题和层级 | `site_audit.py URL --json` | 通过：无 `h1-missing`、`h1-multiple`、`headings-skip-level`。失败：有（WARN 或 CRITICAL，见 [meta-tag-formulas.md](meta-tag-formulas.md) 审计扣分表） |
| 必备区块 | 对照本页型的骨架逐项勾 | 通过：区块齐全。失败：缺区块且没有理由 |
| 篇幅 | 对照大纲，看每节是否回答一个问题 | 通过：每节都有用途。失败：为凑字数的重复段 |
| 列表和表格 | 浏览器检查元素 | 通过：真实 `<ol>`、`<ul>`、`<table>`。失败：图片或样式模拟 |
| 署名、日期、方法 | `trust_signals.py URL`；`core_eeat.py --url URL` | 通过：齐全。失败：缺 |
| FAQ 问题来源 | 对照来源记录 | 通过：每个问题都有来源。失败：有编造的问题 |
| 结构化数据 | `schema_lint.py URL`；Rich Results Test | 通过：无报错，字段都可见。失败：有报错或标记了不可见内容 |
| 内链 | `site_crawl.py example.com --json` | 通过：不是孤儿页，有上下游链接。失败：孤儿页 |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。一手资料均于 2026-10-18 打开核对。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/seo-content-writer/references/content-structure-templates.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/seo-content-writer/references/content-structure-templates.md)（Apache-2.0）
- 一手资料：[有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)、[标题链接](https://developers.google.com/search/docs/appearance/title-link)、[撰写高质量评测](https://developers.google.com/search/docs/specialty/ecommerce/write-high-quality-reviews)、[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)、[Search Console 数据异常](https://support.google.com/webmasters/answer/6211453)、[Bing 网站管理员指南](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)
