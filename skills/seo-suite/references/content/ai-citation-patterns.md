# AI 搜索中的引用：机制、写法与观测

> 先读 [geo-evidence.md](geo-evidence.md)。本文是**描述性**的：说明 AI 搜索产品通常怎样找到、选用和展示来源，
> 以及哪些写法能让内容更容易被准确摘取。它不是「照做就会被引用」的因果清单，也不承诺引用率、排名或流量。
> 2026-10-21 复核（上一轮 2026-10-18）：每条「模式」都标明证据类型——官方说明、因果实验、描述性观察，或本套件口径。

## 1. 先分清三层

| 层 | 问题 | 你能控制多少 |
|---|---|---|
| 可发现 | 页面能否被抓取、渲染、索引；爬虫策略是否放行 | 基本可控 |
| 可理解 | 关键信息是否以文本存在；概念有无定义；结论有无条件、出处、日期 | 可控 |
| 被选用 | 产品的检索、排序、生成策略是否选中你的页面 | 不可控，只能观测 |

诊断时从上往下查。前两层有问题时，讨论「AI 偏好」没有意义。

## 2. 一手文档能支持的事实（核对 2026-10-21）

- **Google AI Overviews / AI Mode**：沿用 Google 搜索的基础要求——可抓取、已索引、可带摘要展示；重要内容以文本存在；内链可发现；结构化数据与可见文本一致。没有专门的 AI Schema，不需要为 AI 改写或切块。这些流量计入 Search Console「网页」类型（[AI features](https://developers.google.com/search/docs/appearance/ai-features)、[生成式 AI 优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)）。
- **Bing / Copilot**：指南要求事实和定义写明、关键陈述不依赖隐含内容、关键信息放在页面前部、每个网址聚焦一个主题、实体命名一致（[Bing Webmaster Guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a) 第 15–18 条）。这是官方写法要求，不是排名公式。
- **爬虫控制**：各家公布自己的 user-agent 和控制方式。Google-Extended 管 Gemini 训练与 grounding，不影响 Google 搜索收录和排名；OpenAI 区分搜索用、训练用和用户触发的访问（[Google 常见爬虫](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers)、[OpenAI bots](https://platform.openai.com/docs/bots)）。放行哪一类是业务决策，见 [geo-platform-differences.md](geo-platform-differences.md) 第三节与 [robots-txt-reference.md](../technical/robots-txt-reference.md)。
- 其他产品的检索来源、排序和引用展示，以各家当前公开文档为准；没有文档的部分当作假设，靠观测验证。

## 3. 引用模式：哪些是观察，哪些是实验

| 模式 | 证据类型 | 依据与限定 |
|---|---|---|
| 引用集中在页面前部 | 描述性观察 | Kevin Indig（SEL 二手转述，原文付费未核）：44.2% 的 ChatGPT 引用来自页面前 30%；2609.35077：作者算出的最佳匹配段中位深度 0.36。都不是「引擎读到某处就停」的测量 |
| 被引段落多用定义句、实体密、语气像分析师 | 描述性观察 | Kevin Indig：被引段落用「X 是」类定义的比例约为两倍，专有名词占比平均 20.6%（一般英文 5%–8%）（[SEL 报道](https://searchengineland.com/chatgpt-citations-content-study-469483)） |
| 新内容更常被引 | 描述性观察，两家结论不一致 | Ahrefs：ChatGPT 最偏好新内容；Seer：AIO 引用 85% 发布于 2023–2025。见 [geo-platform-differences.md](geo-platform-differences.md) 第二节 |
| 加统计、引语、来源能提高回答内可见度 | 因果实验，但条件窄且有反例 | GEO 论文在固定前 5 条结果的设定里 +30–40%；C-SEO Bench 发现多数此类改写无效（[geo-evidence.md](geo-evidence.md) 第三节） |
| 提示-内容对齐（页面用买家的问法） | 观察性研究，控制了域名 | 2609.35077 中最强的页面级变量（β=+0.37），跨期仍同号 |
| 加 Schema / FAQPage 提高引用 | 准实验否定 | Ahrefs 双重差分与 SSRN 6284518 都没有测出独立效应（[geo-evidence-bank.md](geo-evidence-bank.md) 第八节） |
| 读了不一定引 | 描述性观察 | Perplexity Sonar 每次约访问 10 个相关页、只引用 3–4 个（[arXiv 2508.00838](https://arxiv.org/abs/2508.00838)） |

描述性观察只说明「被引的页面长什么样」，不说明「改成这样就会被引」。

## 4. 有助于准确摘取的写法（本套件口径）

这些写法的理由是「读者更容易理解、被摘录时不容易被断章取义」；Bing 指南有同向要求。它们不是「AI 喜欢」：

- 先下定义再展开：第一句说清「是什么、属于哪一类、和相近概念有什么区别」。
- 一段一个结论：结论句带主语、条件、适用范围；避免「如上所述」「它」这类依赖上下文的指代。
- 标题、H1、首段用买家的原话，首段第一句直接回答（见 [question-alignment.md](question-alignment.md)）。
- 短句、一句一事、主动语态、术语一致（见 [asd-ste100-web-writing.md](asd-ste100-web-writing.md)）。
- 数字带口径：来源、时间、样本、统计方法；原创数据写清方法。
- 对比用真实表格：维度清楚，写核对日期，给出「适合谁」。
- 操作用有序步骤：前置条件、每一步的预期结果、常见错误。
- 署名与时间可见：作者、机构、发布与更新时间；专业领域写明审阅人。

具体块写法见 [content-patterns.md](content-patterns.md)，改写示例见 [quotable-content-examples.md](quotable-content-examples.md)。

## 5. 按查询类型的侧重（本套件口径）

| 查询类型 | 页面应先给出 | 常见缺口 |
|---|---|---|
| 是什么 / 为什么 | 一句话定义，再讲机制和例子 | 定义埋在第三段 |
| A 与 B 比较 / 哪个好 | 评价维度 + 对比表 + 适用场景 | 只写自家优点、无核对日期 |
| 怎么做 | 前置条件 + 编号步骤 + 验证方法 | 步骤跳跃、缺版本信息 |
| 多少 / 数据 | 数字 + 口径 + 时间 + 出处 | 无来源、过期数据 |

## 6. 不写进方案的说法

- 「某 AI 平台偏好某种格式或某类网站」的比例和排名，没有一手来源时一律不用。
- 「加统计、加引文可提升 N% 可见度」这类通用增益：C-SEO Bench 在其实验设置中发现多数此类方法无效，不能当优先级依据。
- 固定字数、TLD 加权、「多个域名转载后引用翻倍」。

## 7. 怎么观测 AI 引用（检查清单）

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 问题集固定且来自真实问法 | 按意图分组（定义、比较、操作、品牌事实），问法取自 GSC 查询或工单原话；`python3 scripts/citation_panel.py init --brand X --prompts-file 问题库.md --domain 站点 --stage-mix` | 通过：≥10 个 prompt，看结果前冻结。失败：看完结果再改问题 |
| 2 | 条件固定 | 记录语言、地域、登录状态、产品与模型版本、日期 | 通过：每次 run 都记全。失败：混用个人账号与干净环境 |
| 3 | 每次记录完整 | `record --engine chatgpt --file run.csv`（列：prompt,mentioned,cited,cited_urls[,state][,rank]）；有回答原文时加 `--answer-file` | 通过：失败采集记 failed，不当成缺席。失败：只记「有/没有」 |
| 4 | 三件事分开 | `python3 scripts/citation_panel.py report` 分列提及率与引用份额；`ai_referral_log.py` 看点击 | 通过：提及、引用、点击分别报告。失败：合成一个「可见度」 |
| 5 | 重复取样看趋势 | 同一 prompt ≥3 次；改动前后用 `citation_panel.py diff RUN1 RUN2`；尽量设对照页面 | 通过：只报配对样本的变化，并带区间。失败：单次缺失就下结论 |
| 6 | 辅助数据 | GSC 生成式 AI 效果报告（2026-06-03 起，只有展示；AI 功能的点击仍拆不出，包含在总体「网页」数据里）；Bing AI Performance；分析工具里的 AI 引荐（会漏掉不带 referrer 的访问） | 通过：标明是下界。失败：把引荐当全量 |

这些都是自己观测的抽样指标，不是平台官方数据；报告里写明取样方法。

## 8. 交付

- 可见度基线：问题集、取样条件、结果表。
- 影响可发现或可理解的问题清单，按页面列出证据。
- 按页面的修改建议（定义、结论句、数据出处、对比表、署名与日期）。
- 复测计划：时间点、问题集、对照页面。

## 市场差异：各市场引用模式（与 geo-platform-differences 第六节互补）

只列已核到原文的条目，均为第三方观察：

- **土耳其**：seobaz 2026-08 研究（8,282 个土耳其语移动端 Google 搜索，2026-08-16 采集，7,696 条 AIO 来源链接），AIO 引用的来源 75.3% 与同一搜索的自然前 10 结果为同一页面；有 AIO 的搜索里排第 1 的页面 53.4% 被引（[seobaz](https://seobaz.com/blog/turkiye-ai-overview-arastirmasi-2026-google-hangi-sayfalari-kaynak-gosteriyor)）。作者对比的两项美国研究约 37%（Ahrefs 37.1%、TripleDart 37.0%）。土耳其的 AI 可见度与传统 SEO 绑定更紧，美国的结论不能直接平移。
- **日本**：用日语提问时 26% 的被引来源在 .jp 域，用英语约 1%（Weglot，2026-09）；30 个领域 1,459 个日语查询中 76.9% 出现 AIO（Itera 自测，PR TIMES 新闻稿 2026-08-05，报告期 2026-07）。
- **韩国**：Naver 表示 AI 브리핑 被引内容约 70% 是其自有 UGC（博客、카페 等）（[Nasmedia 报道](https://blog.nasmedia.co.kr/entry/2606naspick)，2026-06）。
- **共同纪律**（本套件口径）：引用偏好的结论按引擎分列，不合并；6–12 个月内重测，过期的结论不沿用。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/geo-content-optimizer/references/ai-citation-patterns.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/geo-content-optimizer/references/ai-citation-patterns.md)（Apache-2.0）
- 一手资料：[Google：AI 功能与网站](https://developers.google.com/search/docs/appearance/ai-features)、[Google 常见抓取工具（含 Google-Extended）](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers)、[OpenAI 爬虫说明](https://platform.openai.com/docs/bots)、[Bing Webmaster Guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)、[C-SEO Bench](https://arxiv.org/abs/2506.11097)
