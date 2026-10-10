== 引用缺口报告(citation gaps): Nimbus Analytics ==
runs=6 cells=84 qualifying=18(有 cited_urls 且品牌未被引;cited_brand/failed/no_answer 不入)
自有域排除: nimbus-cdn.example,nimbus.example(qualifying cell 内自有域被引 1 次不计)
候选 URL=11 覆盖域名=8 高优先(竞品同场)=8

-- 域名分组(排序:竞品同场降序 → 总引用降序) --
| 域名 | 总引用 | 页面数 | 同场竞品 | 追踪 prompts | 引擎 | 优先级 |
|---|---|---|---|---|---|---|
| g2.com | 12 | 3 | devops.to,hubspot.com,rival.example,techcrunch.com,wikipedia.org | 3 | chatgpt,perplexity | High |
| devops.to | 4 | 1 | g2.com | 1 | chatgpt,perplexity | High |
| rival.example | 4 | 1 | g2.com,wikipedia.org | 1 | chatgpt,perplexity | High |
| wikipedia.org | 3 | 2 | g2.com,rival.example | 2 | chatgpt,perplexity | High |
| hubspot.com | 1 | 1 | g2.com | 1 | perplexity | High |
| techcrunch.com | 1 | 1 | g2.com | 1 | chatgpt | High |
| reddit.com | 3 | 1 | - | 1 | chatgpt,perplexity | Standard |
| kpiwiki.io | 1 | 1 | - | 1 | perplexity | Standard |

-- Top 页面(前 10,共 11;排序:竞品同场降序 → 引用次数降序) --
| URL | 引用 | prompts | 引擎 | 同场竞品 | 优先级 |
|---|---|---|---|---|---|
| https://www.g2.com/categories/product-analytics | 6 | 1 | chatgpt,perplexity | rival.example,techcrunch.com,wikipedia.org | High |
| https://handbook.devops.to/cheap-stack | 4 | 1 | chatgpt,perplexity | g2.com | High |
| https://rival.example/platform | 4 | 1 | chatgpt,perplexity | g2.com,wikipedia.org | High |
| https://www.g2.com/categories/cheap-analytics-tools | 4 | 1 | chatgpt,perplexity | devops.to | High |
| https://www.g2.com/best-crms-for-startups | 2 | 1 | perplexity | hubspot.com | High |
| https://en.wikipedia.org/wiki/Web_analytics | 1 | 1 | chatgpt | g2.com,rival.example | High |
| https://hubspot.com/crm/buyers-guide | 1 | 1 | perplexity | g2.com | High |
| https://techcrunch.com/2026/product-analytics-landscape | 1 | 1 | chatgpt | g2.com | High |
| https://www.reddit.com/r/productanalytics | 3 | 1 | chatgpt,perplexity | - | Standard |
| https://en.wikipedia.org/wiki/Business_intelligence | 2 | 1 | chatgpt,perplexity | - | Standard |

-- 外联提示(逐域名;口径照抄 borrow-specs B2) --
[High] g2.com:竞品 devops.to,hubspot.com,rival.example,techcrunch.com,wikipedia.org 在 g2.com 被引用——考虑贡献内容或争取列表位直接竞争
[High] devops.to:竞品 g2.com 在 devops.to 被引用——考虑贡献内容或争取列表位直接竞争
[High] rival.example:竞品 g2.com,wikipedia.org 在 rival.example 被引用——考虑贡献内容或争取列表位直接竞争
[High] wikipedia.org:竞品 g2.com,rival.example 在 wikipedia.org 被引用——考虑贡献内容或争取列表位直接竞争
[High] hubspot.com:竞品 g2.com 在 hubspot.com 被引用——考虑贡献内容或争取列表位直接竞争
[High] techcrunch.com:竞品 g2.com 在 techcrunch.com 被引用——考虑贡献内容或争取列表位直接竞争
[Standard] reddit.com:AI 模型在 1 个追踪 prompt 引用 reddit.com,获得收录可提升 AI 可见性
[Standard] kpiwiki.io:AI 模型在 1 个追踪 prompt 引用 kpiwiki.io,获得收录可提升 AI 可见性

-- 来源五分类(逐域名;Peec Source 五分类,启发式与默认均 [推断];--domain-class overrides.json 人工覆盖) --
| 域名 | 分类 | 判定依据 | 行动提示 |
|---|---|---|---|
| g2.com | UGC | override | 社区运营:官方账号真实参与讨论与答疑,不做硬广 |
| devops.to | Editorial | override | PR outreach:媒体投稿/新闻源/专家引言,争取编辑报道 |
| rival.example | Corporate | default:corporate[推断] | 合作目录:争取合作方目录、集成市场、对比页收录 |
| wikipedia.org | Reference | known:wikipedia.org | 更正词条:核对词条事实,补充自有可靠来源 |
| hubspot.com | Corporate | default:corporate[推断] | 合作目录:争取合作方目录、集成市场、对比页收录 |
| techcrunch.com | Editorial | known:techcrunch.com | PR outreach:媒体投稿/新闻源/专家引言,争取编辑报道 |
| reddit.com | UGC | known:reddit.com | 社区运营:官方账号真实参与讨论与答疑,不做硬广 |
| kpiwiki.io | Reference | token:wiki | 更正词条:核对词条事实,补充自有可靠来源 |

-- gapLabel 七叉(逐 prompt;niubigeo 口径;竞品代理=同 cell 非自有被引域[推断]) --
| Prompt | 标签 | 有效/提及/被引/竞品独现 | 动作 |
|---|---|---|---|
| ai agent security checklist | No completed AI answers | 0/0/0/0 | 数据不足:0 条有效回答——先修采集(重跑/换引擎),再谈缺口 |
| best webhook monitoring tools | No completed AI answers | 0/0/0/0 | 数据不足:0 条有效回答——先修采集(重跑/换引擎),再谈缺口 |
| cheap analytics alternatives list | Competitors own this AI answer space | 6/0/0/4 | 最高优先:对标竞品产出内容/对比页,争取进入该词的答案 |
| top product analytics platforms | Competitors own this AI answer space | 6/0/0/6 | 最高优先:对标竞品产出内容/对比页,争取进入该词的答案 |
| etl vs elt explained | Target absent from AI answers | 3/0/0/0 | 品类词缺席:补该主题的 grounding 页面与可引用事实 |
| how to build a data warehouse | Target absent from AI answers | 6/0/0/0 | 品类词缺席:补该主题的 grounding 页面与可引用事实 |
| cohort retention analysis guide | Owned content is not reflected | 6/2/0/0 | 自有内容没进答案:检查页面可引用性(结构化事实/数据密度) |
| product analytics benchmarks report | Owned content is not reflected | 6/2/0/0 | 自有内容没进答案:检查页面可引用性(结构化事实/数据密度) |
| open source product analytics options | Mentioned without official citation | 6/6/0/0 | 仅提及无引用:强化可引用资产(数据页/研究/文档) |
| self-hosted analytics comparison | Mentioned without official citation | 6/4/0/0 | 仅提及无引用:强化可引用资产(数据页/研究/文档) |
| best crm for startups | Competitors still appear without target | 6/4/4/2 | 偶发竞品独现:巩固既有覆盖,补竞品占位的子话题 |
| crm implementation mistakes | Competitors still appear without target | 6/5/5/1 | 偶发竞品独现:巩固既有覆盖,补竞品占位的子话题 |
| funnel analysis best practices | Covered in this audit | 6/6/6/0 | 已覆盖:保持监测,暂不动 |
| product analytics fundamentals tutorial | Covered in this audit | 6/6/6/0 | 已覆盖:保持监测,暂不动 |
[i] ownedRelevance 由 --owned-relevance 提供;分支 4 按输入判定。

-- 串联(先 gaps 找目标域 → 再 cite_domain.py 评级) --
  高优先域先评级再投入外联:python3 cite_domain.py --input answers.json(数据项人工采集);
  评级进入简报:templates/monitor/citation-outreach-brief.md。
