# AI 搜索中的引用：机制、写法与观测

> 先读 [geo-evidence.md](geo-evidence.md)。本文是**描述性**的：说明 AI 搜索产品通常怎样找到、选用和展示来源，
> 以及哪些写法能让内容更容易被准确摘取。它不是「照做就会被引用」的因果清单，也不承诺引用率、排名或流量。

## 1. 先分清三层

| 层 | 问题 | 你能控制多少 |
|---|---|---|
| 可发现 | 页面能否被抓取、渲染、索引；爬虫策略是否放行 | 基本可控 |
| 可理解 | 关键信息是否以文本存在；概念有无定义；结论有无条件、出处、日期 | 可控 |
| 被选用 | 产品的检索、排序、生成策略是否选中你的页面 | 不可控，只能观测 |

诊断时从上往下查。前两层有问题时，讨论「AI 偏好」没有意义。

## 2. 一手文档能支持的事实

- **Google AI Overviews / AI Mode**：沿用 Google 搜索的基础要求——可抓取、可索引、有可见文本、内部链接可发现、结构化数据与正文一致；没有专门的 AI Schema，也不需要为 AI 改写或切块。出现在 AI 功能中的流量计入 Search Console 的网页搜索数据，具体口径以 Google 文档为准。
- **爬虫控制**：各家公布了自己的 user-agent 和控制方式。例如 Google 用 Google-Extended 让网站选择内容能否用于 Gemini 相关用途，Google 文档说明它不影响网站在 Google 搜索中的收录和排名；OpenAI 区分了搜索用爬虫、训练用爬虫和用户发起的抓取。放行哪一类是业务决策，见 [robots-txt-reference.md](../technical/robots-txt-reference.md)。
- 其他产品的检索来源、排序和引用展示方式，以各家当前公开文档为准；没有文档的部分当作假设，通过观测验证。

## 3. 有助于准确摘取的写法

这些写法的理由是「读者更容易理解、被摘录时不容易被断章取义」，不是「AI 喜欢」：

- 先下定义再展开：第一句说清「是什么、属于哪一类、和相近概念有什么区别」。
- 一段一个结论：结论句带主语、条件、适用范围；避免「如上所述」「它」这类依赖上下文的指代。
- 数字带口径：来源、时间、样本、统计方法；原创数据写清方法。
- 对比用真实表格：维度清楚，写核对日期，给出「适合谁」。
- 操作用有序步骤：前置条件、每一步的预期结果、常见错误。
- 署名与时间可见：作者、机构、发布与更新时间；专业领域写明审阅人。

具体块写法见 [content-patterns.md](content-patterns.md)，改写示例见 [quotable-content-examples.md](quotable-content-examples.md)。

## 4. 按查询类型的侧重

| 查询类型 | 页面应先给出 | 常见缺口 |
|---|---|---|
| 是什么 / 为什么 | 一句话定义，再讲机制和例子 | 定义埋在第三段 |
| A 与 B 比较 / 哪个好 | 评价维度 + 对比表 + 适用场景 | 只写自家优点、无核对日期 |
| 怎么做 | 前置条件 + 编号步骤 + 验证方法 | 步骤跳跃、缺版本信息 |
| 多少 / 数据 | 数字 + 口径 + 时间 + 出处 | 无来源、过期数据 |

## 5. 不写进方案的说法

- 「某 AI 平台偏好某种格式或某类网站」的比例和排名，没有一手来源时一律不用。
- 「加统计、加引文可提升 N% 可见度」这类通用增益：C-SEO Bench 在其实验设置中未能重现文献报告的效果（详见 geo-evidence.md 第三节），不能当作优先级依据。
- 固定字数、TLD 加权、「多个域名转载后引用翻倍」。

## 6. 怎么观测 AI 引用

1. 建固定问题集：按意图分组（定义、比较、操作、品牌事实），每组若干条真实用户问法。
2. 固定条件：语言、地域、登录状态、产品与模型版本，记录日期。
3. 每次记录：是否触发联网检索、回答原文、引用的 URL 及位置、是否提到品牌、是否附链接。
4. 区分三件事：品牌被提及、页面被引用、带来点击。三者互不等同。
5. 重复取样看趋势，单次缺失不下结论；改动前后分批对比，尽量设对照页面。
6. 辅助数据：Search Console 网页搜索数据、分析工具里来自 AI 产品的引荐流量（会漏掉不带引荐信息的访问）。

这些都是自己观测的抽样指标，不是平台官方数据；报告里要写明取样方法。

## 7. 交付

- 可见度基线：问题集、取样条件、结果表。
- 影响可发现或可理解的问题清单，按页面列出证据。
- 按页面的修改建议（定义、结论句、数据出处、对比表、署名与日期）。
- 复测计划：时间点、问题集、对照页面。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/geo-content-optimizer/references/ai-citation-patterns.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/geo-content-optimizer/references/ai-citation-patterns.md)（Apache-2.0）
- 一手资料：[Google：AI 功能与网站](https://developers.google.com/search/docs/appearance/ai-features)、[Google 常见抓取工具（含 Google-Extended）](https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers)、[OpenAI 爬虫说明](https://platform.openai.com/docs/bots)、[C-SEO Bench](https://arxiv.org/abs/2506.11097)
