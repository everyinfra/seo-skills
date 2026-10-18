# 内容块写法模式（AEO / GEO）

> 先读 [geo-evidence.md](geo-evidence.md)。下面的模式帮助读者快速找到答案，也让搜索和 AI 产品更容易准确理解页面；
> 它们不保证获得精选摘要、AI 引用或排名。按真实用户问题选用，不要每页套全。
> 标题和首段用买家原词，见 [question-alignment.md](question-alignment.md)。
> UGC 内容 SEO 与站内搜索优化（双模块）另见 [ugc-site-search.md](ugc-site-search.md)。

## 选哪个块

本套件口径：

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

- 标题用用户的问法，答案紧跟标题，不绕弯。问法的来源见 question-alignment.md 第二节。
- 自足回答：一个段落回答一个问题，单独摘出去仍然准确。示例见 [quotable-content-examples.md](quotable-content-examples.md)。
- 统计数字：写来源、时间、样本和口径；过期数据更新或标注。
- 专家引语：写清姓名、身份和出处，不编造。Google 把编造作者资料（AI 生成的头像、虚构的姓名、虚假的资历）列为欺骗（[有用内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)，核对 2026-10-18）。
- 权威主张：优先引用一手来源（标准、官方文档、论文），不引用转述的转述。
- 结构化数据只描述页面上可见的内容（[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)）。FAQ 富结果的现状见 geo-evidence.md 与 [deprecated-signals.md](../technical/deprecated-signals.md)，不要为占位堆 FAQPage 标记。

## 高风险领域的额外要求

- **健康、金融、法律**：由有资质的人审阅并署名；写明更新时间；给一手来源；说明内容的适用边界，不做夸大承诺。依据：对可能显著影响健康、财务稳定或安全的主题（YMYL），Google 的系统更看重体现强 E-E-A-T 的内容；这类内容必须高度准确，并与公认的专家共识一致（[有用内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)，核对 2026-10-18）。
- **技术文档**（本套件口径）：写清版本号和运行环境；代码示例可运行；标注已知限制。
- **商业与营销**（本套件口径）：数据写口径；案例写清背景、时间和前提条件。

## 语音与对话式查询

- Google 没有单独的「语音 SEO」规范。专用的只有 speakable 结构化数据：它是 Beta，只用于新闻内容，只面向美国、设备语言为英语的 Google Home 用户和英文发布者（[speakable](https://developers.google.com/search/docs/appearance/structured-data/speakable)，核对 2026-10-18）。
- 其他场景按普通页面做：用自然问句做标题，首句给一句话结论（本套件口径）。不为语音单独建页。

## 常见误区

- 为了「被 AI 摘取」把每段都改成问答。
- 在页面上堆 FAQ 和 FAQPage 标记来占位。
- 用虚构的统计、专家或案例填充证据块。
- 「最佳 N 个」清单只推自家产品，或排序理由不公开。
- 同一事实在正文、表格、结构化数据里说法不一致。

## 市场差异：结构惯例

- 各市场的结构惯例写在 [multilingual-workflow.md](../overview/multilingual-workflow.md) 和 `references/markets/<市场代码>.md`。例如：日语的見出し字数、越南的提问式 H2 规则（t0mmy 规则集，是业内规则，不是官方算法）、俄语商业页的法定信息页、阿拉伯语的标准语与方言分层。这些数字由对应文件核实，本文件不重复。
- 中文（本套件口径）：一套事实分三种写法（官网、公众号、社区）；营销词每页不超过 3 个，`market_lint.py --market zh FILE` 会检查。

## SXO：页型匹配与读者画像

本节是本套件口径，方法来自 claude-seo 的 SXO 模块（第三方工具），数字是该方法的约定，不是研究结论。

- **页型先于内容**：先把 SERP 前 10 的每条结果按页型分类，再谈页面本身。
- **8 类页型**，信号重叠时按顺序取：工具 / 交互 → 本地（地址 + 地图）→ 对比（vs + 矩阵表）→ 商品（价格 + 购买按钮）→ 落地页（CTA 重、导航精简）→ 服务页（流程 + 案例）→ 混合（教育 + CTA）→ 博客（默认）。
- **失配严重度**：博客打商品词 = CRITICAL（建商品页）；博客打对比词 = HIGH（改成对比矩阵）；商品页打信息词 = HIGH（加教育内容）；落地页打工具词 = HIGH（做交互组件）；服务页打本地结果 = MEDIUM（补本地信号和 schema）。
- **共识度**：某页型占比 > 60% 为强共识；40–60% 为混合；< 40% 为碎片化。碎片化是差异化机会，注明即可。
- **从 SERP 信号推导读者需要，不凭空编**：「其他人还问了」= 知识缺口；广告文案 = 商业触发点和顾虑；相关搜索 = 搜索路径（加限定词 = 收窄，alternatives = 不满意现有方案，vs = 正在比较，reviews = 先要信任）；精选摘要的格式 = 期望的答案结构（段落 = 定义，列表 = 步骤，表格 = 对比数据，视频 = 演示）。
- **故事模板**：As a [画像] / I want [目标] / because [动机] / but blocked by [障碍]。障碍分六类：信息缺口、信任缺口、比较疲劳、价格敏感、技术困惑、时间压力。
- **画像评分**：4–7 个画像，每个都要追溯到上面的信号。四维各 25 分：Relevance（解决这个画像的需求）、Clarity（10 秒内找到答案）、Trust（这个画像需要的信任信号）、Action（下一步匹配所处阶段）。总分分四档：80+、60–79、40–59、0–39；0–39 为严重失配，重构或另起页面。按估算搜索量加权，先修「最弱画像 × 最高权重」。
- **SXO 缺口分和 SEO 健康分分开报**：7 维，页型、内容深度、UX 信号、schema、媒体丰富度、权威信号各 15 分，新鲜度 10 分。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 块与问题匹配 | 对照「选哪个块」 | 通过：每个块回答一个真实问题。失败：每段都改成问答 |
| 标题用用户问法 | 对照查询、工单原话（question-alignment.md 第二节） | 通过：用原词。失败：内部术语 |
| 答案自足 | 把段落单独摘出来读 | 通过：单独读仍准确。失败：依赖上下文 |
| 统计数字 | 逐个查来源、时间、样本、口径 | 通过：四项齐。失败：缺任何一项或已过期未标注 |
| 引语 | 查姓名、身份、出处 | 通过：可查证。失败：查不到 |
| 事实一致 | 对照正文、表格和结构化数据；`python3 scripts/schema_lint.py URL` | 通过：三处说法一致。失败：不一致 |
| FAQ 问题来源 | 对照工单、搜索词、社区记录 | 通过：每个问题有来源。失败：编造 |
| H2 问句占比与营销词 | `python3 scripts/market_lint.py --market XX FILE --report` | 按该市场 markets 文件的口径判 |
| YMYL 内容 | 看署名、审阅者资质、更新时间 | 通过：三项齐。失败：缺 |
| 页型 | SXO 节的 8 类页型分类 SERP 前 10 | 通过：与主流页型一致或写明理由。失败：错页型 |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。一手资料均于 2026-10-18 打开核对。

- 思路参考：[coreyhaines31/marketingskills · skills/ai-seo/references/content-patterns.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/ai-seo/references/content-patterns.md)（MIT）
- 一手资料：[Google：精选摘要](https://developers.google.com/search/docs/appearance/featured-snippets)、[Google：有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[Google：结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)、[Google：speakable](https://developers.google.com/search/docs/appearance/structured-data/speakable)
- 方法来源（第三方工具）：claude-seo 的 SXO 模块（页型、画像评分）
