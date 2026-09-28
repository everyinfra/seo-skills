# 常见页面类型的结构要点

> 涉及 GEO / AI 引用的判断，先读 [geo-evidence.md](geo-evidence.md)。下面的结构是为了让读者更快找到答案，不承诺 AI 引用或排名提升。

## 用途与何时读

写内容简报、起草或改版教程、清单、对比、评测、术语页、落地页时读。先按 SERP 前列确定页面类型，再用下面的骨架检查有没有漏掉关键区块。标题写法见 [title-formulas.md](title-formulas.md)。

## 通用原则

- **篇幅由问题决定。** Google 明确表示没有偏好的字数，不为凑字数扩写，也不为压字数删掉必要的步骤和条件。
- **开头先回答。** 首屏讲清这页解决什么、结论是什么，再展开。
- **标题层级反映真实结构**：一个 H1；H2、H3 按内容分层，不为塞关键词加标题。
- **用真实的列表和表格元素**表达步骤和比较，不用图片或样式模拟。
- **写出信任信息**：作者和相关经验、发布与更新日期、测试或数据来源的方法说明。
- **链接**：内链指向上下游页面；外链优先指向一手来源。
- **FAQ 只收真实被问到的问题。** FAQPage 标记只描述页面上可见的问答；Google 已停止展示 FAQ 富结果，不为它加 FAQ 区块。
- **结构化数据按页面类型选**（例如 Article、Product、BreadcrumbList），内容必须与可见正文一致。

## 各类页面骨架

### 教程 / 操作指南

结果预览 → 前提条件（工具、权限、版本）→ 编号步骤 → 如何确认成功 → 常见报错与排查 → 下一步

- 每一步只做一个动作，写清预期结果，需要时配截图或代码。
- 注明适用的版本和测试日期，界面变化后及时更新。

### 清单 / 盘点（「最好的某类产品」）

选择标准与测试方法 → 速览表 → 逐项介绍（适合谁、优缺点、价格及日期）→ 怎么选 → 利益关系披露

- 每一项都要有实际使用或测试依据，而不是改写各家官网。
- 有联盟或合作关系必须披露。

### 对比（A vs B）

结论先行 → 对比表 → 分维度展开 → 各自适合谁 → 价格口径 → 真实常见问题

- 必须写出「选另一方更合适」的情形。
- 涉及自家产品和竞品时，区块写法见 [competitor-section-templates.md](../research/competitor-section-templates.md)。

### 评测（单个产品）

测评对象、版本和使用时长 → 测试方法 → 关键发现（附照片、数据、截图等证据）→ 优缺点 → 与替代品比较 → 适合与不适合的人 → 结论

- 用评分就说明评分方法。
- 按 Google 的评测写作建议，提供第一手证据，并说明与同类产品相比的差异。

### 术语 / 概念页

开头一两句定义 → 展开解释 → 具体例子 → 容易混淆的概念 → 相关术语链接

- 定义能单独读懂，不依赖上下文。
- 批量做术语页时，每页都要有例子和解释，避免只有一句话的薄页。

### 落地页 / 产品页

首屏价值主张（是什么、给谁、主要收益）→ 证据（客户、数据、演示）→ 按用户任务组织的功能 → 价格或获取方式 → 常见顾虑 → 行动按钮

- Product 结构化数据中的价格、库存必须和页面一致。
- 首屏不堆口号，读者要能直接看出这是否适合自己。

### 总览页（Pillar）

目录 → 各子主题的要点概述 → 链接到深入页 → 下一步阅读

- 每个子主题讲到够用，深入内容交给专门页面；规划方法见 [topic-cluster-templates.md](../research/topic-cluster-templates.md)。

### 排障 / 问答页

按问题分组 → 每个问题：现象 → 原因 → 解决 → 如何确认已解决

- 每个问题有稳定的锚点，便于从其他页面直接链到具体答案。
- 报错信息原文照录，方便读者用报错搜索时找到。

## 发布前自查

- [ ] 页面类型与 SERP 前列的主流形式一致
- [ ] 开头就回答了核心问题
- [ ] 标题层级真实，只有一个 H1
- [ ] 步骤、比较用了真实的列表和表格
- [ ] 作者、日期、方法或来源写清楚了
- [ ] 常见问题都是真实问题，答案与正文一致
- [ ] 结构化数据与可见内容一致
- [ ] 有指向上下游页面的内链

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/seo-content-writer/references/content-structure-templates.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/seo-content-writer/references/content-structure-templates.md)（Apache-2.0）
- 一手资料：[有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[撰写高质量评测](https://developers.google.com/search/docs/specialty/ecommerce/write-high-quality-reviews)、[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)、[Article](https://developers.google.com/search/docs/appearance/structured-data/article)、[Product](https://developers.google.com/search/docs/appearance/structured-data/product)、[Breadcrumb](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)
