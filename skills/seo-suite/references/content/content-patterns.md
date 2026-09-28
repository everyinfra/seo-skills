# 内容块写法模式（AEO / GEO）

> 先读 [geo-evidence.md](geo-evidence.md)。下面的模式帮助读者快速找到答案，也让搜索和 AI 产品更容易准确理解页面；
> 它们不保证获得精选摘要、AI 引用或排名。按真实用户问题选用，不要每页套全。

## 选哪个块

| 用户在问 | 用的块 | 写法要点 |
|---|---|---|
| 是什么 | 定义块 | 第一句给出类别和区别特征，再补例子与边界 |
| 怎么做 | 步骤块 | 前置条件、编号步骤、每步的可验证结果、常见错误 |
| 选哪个 | 对比表 | 维度清楚，写核对日期，结尾给「适合谁」 |
| 值不值 | 优缺点块 | 两边都写真实缺点，说明适用场景 |
| 常见疑问 | FAQ 块 | 只收真实问题（客服记录、搜索词、社区提问），答案先结论后解释 |
| 有哪些 | 清单块 | 每项写入选理由；排序依据公开透明 |
| 为什么 | 证据三明治 | 结论 → 证据（数据、来源、案例）→ 含义或下一步 |

## 通用写法

- 标题用用户的问法，答案紧跟标题，不绕弯。
- 自足回答：一个段落回答一个问题，单独摘出去仍然准确，示例见 [quotable-content-examples.md](quotable-content-examples.md)。
- 统计数字：写来源、时间、样本和口径；过期数据更新或标注。
- 专家引语：写清姓名、身份和出处，不编造。
- 权威主张：优先引用一手来源（标准、官方文档、论文），不引用转述的转述。
- 结构化数据只描述页面上可见的内容。FAQ 富结果的现状见 geo-evidence.md，不要为占位堆 FAQPage 标记。

## 高风险领域的额外要求

- **健康、金融、法律**：由有资质的人审阅并署名；写明更新时间；给一手来源；说明内容的适用边界，不做夸大承诺。
- **技术文档**：写清版本号和运行环境；代码示例可运行；标注已知限制。
- **商业与营销**：数据写口径；案例写清背景、时间和前提条件。

## 语音与对话式查询

- 语音助手和对话式搜索的答案仍然来自可抓取、可索引的页面。用自然问句做标题、答案先给一句话结论，就已覆盖大部分需求。
- 不需要为语音单独做一套页面；个别面向特定发布者的专用标记，以 Google 当前文档为准。

## 常见误区

- 为了「被 AI 摘取」把每段都改成问答。
- 在页面上堆 FAQ 和 FAQPage 标记来占位。
- 用虚构的统计、专家或案例填充证据块。
- 「最佳 N 个」清单只推自家产品，或排序理由不公开。
- 同一事实在正文、表格、结构化数据里说法不一致。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/ai-seo/references/content-patterns.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/ai-seo/references/content-patterns.md)（MIT）
- 一手资料：[Google：精选摘要](https://developers.google.com/search/docs/appearance/featured-snippets)、[Google：有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[Google：结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)
