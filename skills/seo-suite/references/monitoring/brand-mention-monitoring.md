# 品牌提及监控（AI 搜索时代的"外链"）

> 建立于 2026-10-09。权重与平台分布参考 [zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) `geo-brand-mentions` 技能，按本套件证据约束改写。
> 背景事实（**第三方研究，相关不是因果**）:Ahrefs 2025-05-26 对 7.5 万个品牌的研究（[原文](https://ahrefs.com/blog/ai-overview-brand-correlation/)）里，网页品牌提及与 Google AI 概览中品牌出现的 Spearman 相关系数约 0.66，外链约 0.22，前者约为后者的 3 倍。2025-12-12 的续篇（[原文](https://ahrefs.com/blog/ai-brand-visibility-correlations/)）把范围扩到 ChatGPT 和 AI Mode：YouTube 提及相关性最高（约 0.737），品牌网页提及 0.66–0.71；ChatGPT 与 DR、品牌搜索量的相关性较弱（0.266、0.352）；网站页面数与 AI 可见度几乎无关（约 0.194）。作者自己写明相关不等于因果，这不是任何搜索引擎的官方算法声明。样本只含 DR > 40 且最高搜索量关键词月搜索量 ≥800 的域名，不代表所有站点。证据分级以 [geo-evidence](../content/geo-evidence.md) 为准。

## 一、五平台加权（0–100 品牌权威分）

| 平台 | 权重 | 看什么 |
|---|---|---|
| YouTube | 25% | 品牌提及量与情感（相关性最强的单一平台，~0.737） |
| Reddit | 25% | 子版块提及、正负情绪、是否被当权威答案引用 |
| Wikipedia / Wikidata | 20% | 词条存在性、实体完整性（sameAs、描述、类别） |
| LinkedIn | 15% | 公司页活跃度、员工提及 |
| 其他（新闻/博客/论坛） | 15% | 独立第三方提及（非自发） |

分档：Dominant 85+ / Strong 70–84 / Moderate 50–69 / Weak 30–49 / Minimal 0–29。**权重和分档是 geo-seo-claude 工具的自定义评分，本套件口径，不是行业标准**；表里「~0.737」是上面 Ahrefs 研究里 YouTube 提及的相关系数，不是权重依据。

## 二、监控什么（区别于社交聆听）

品牌提及监控在 SEO/GEO 语境下看三件事：

1. **实体一致性**：各平台的品牌名、描述、sameAs 是否一致——不一致会稀释 Knowledge Graph 实体信号。
2. **独立提及增速**：非自发、非付费的第三方提及趋势（AI 引擎的信任信号）。
3. **AI 答案中的出现**：定期用一组固定查询测五个引擎（见下），记录品牌是否出现在答案与引用里。

## 三、买家提示词集（测可见性用，参考 OranAi 分类法）

固定一组提示词、周期性重测，构成可比时间序列：

- **7 类类别提示词**（"最好的 X 工具"、行业对比、价格类、替代品、评测、教程、"X vs Y"）
- **5 个品牌提示词**（直接搜品牌名+品类词，测品牌答案准确性）
- **3 个竞品提示词**（测竞品语境下自己是否被提及）

记录：出现与否 / 位置（正文或引用）/ 情感 / 日期。**报告时附样本量与区间**（本套件纪律：测量数据带 n）。

## 四、实体建设清单（从监控推导的动作项）

- Wikidata 实体：存在、描述准确、sameAs 完整（官网+社交+GBD）
- Wikipedia：是否满足收录门槛。维基百科有[利益冲突（COI）政策](https://en.wikipedia.org/wiki/Wikipedia:Conflict_of_interest)，不鼓励为自己的组织直接编辑词条；自建词条有被删除的风险，被独立可靠来源收录才有价值
- Crunchbase / LinkedIn / GitHub 组织页：信息一致
- 各平台 sameAs 双向可解析、无死链
- YouTube：品牌频道有实质内容（Ahrefs 研究里 AI 概览和 AI Mode 引用 YouTube 最多，ChatGPT 中它是被引第六的域名；第三方数据，相关不是因果）

## 五、KPI 约束（沿用本套件的反虚荣原则）

用：独立提及数、实体一致性得分、固定提示词下的出现率与位置、AI 引用中的品牌出现。
**不用**：总提及数（含自发）、粉丝数、单次爆发帖。

## 六、市场差异：各市场的监控通道与指标

**度量升级（英文区的行业做法，本套件口径）**：引用四级阶梯 Retrieved → Cited → Mentioned → **Recommended**——推荐主要由站外共识（评论站、分析师、论坛）决定；监控输出用 framing（有利 / 中立 / 含糊 / 负面）而不只是计数。

**点击率**：Pew Research 2025-07-22 的研究（[原文](https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/)；900 名美国成年人，2025-03 的浏览数据，68,879 次 Google 搜索，其中 12,593 次出现 AI 摘要）显示：出现 AI 摘要时，用户点击普通结果链接的比例低于没有摘要时（报道数字约 8% 对 15%），点击摘要里引用链接的约 1%。样本只含美国用户和 Google。所以 KPI 用「AI 回答中的出现率」，不要把「AI 流量」当唯一指标。

**监测探针**：Perplexity 的 Sonar API 响应里带 `citations` 和 `search_results` 字段（[官方文档](https://docs.perplexity.ai/guides/chat-completions-guide)，核对 2026-10-21），可以读到真实引用 URL。注意:API 返回的内容不一定等于网页版用户看到的答案，不要把两者混在同一条时间序列里。

下表是各市场**可用的监控入口**。凡写「官方」的，见 [geo-evidence](../content/geo-evidence.md) 的核对；其余是从业者做法，未逐条核一手。

| 市场 | 增补监控通道 |
|---|---|
| 中文 | 对国产 AI 助手提问时留意平台的频率限制，错开时段，不要批量；指标可用:覆盖率、首屏推荐率、单篇被引次数、留存天数、同词竞品对比（行业说法，无统一标准）；知乎的「引证」标记纳入实体一致性检查 |
| 俄语区 | Yandex Webmaster 的「Видимость сайта в Алисе AI」报告（官方，见 geo-evidence）；Telegram 公开频道网页镜像（t.me/s/）是否被 Yandex 收录；红线:行为因素刷量会被惩罚 |
| 韩语区 | Naver Search Advisor 的 AI 브리핑 인용수（官方，见 geo-evidence）；`site:` 查询看收录数 |
| 日语区 | Search Console 的生成式 AI 效果报告（官方；已对全球网站开放，只报展示，[日期](../overview/facts.md#gsc-genai)）；分引擎分开跟，不同引擎偏好的来源不同（从业者观察） |
| 英文 | 自托管替代栈:elmo、oneglanse、limelit-open（第三方开源）；G2、Capterra、Crunchbase 的描述与 About 页保持一致 |

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 提示词面板固定 | 按第三节建 7 + 5 + 3 条提示词，写入文件并加版本号；每期同一面板 | 面板变了就标断点，不与上期直接比较 |
| 样本带 n | `python3 scripts/citation_panel.py init --brand 品牌名 --prompts prompts.csv --engines chatgpt,perplexity`，每次采样后 `record --engine chatgpt --file run.csv`，再 `report`；每条提示词每引擎重复采样几次，次数写进报告 | 报告里每个出现率都附分母和区间（脚本的 mention_rate 带 Wilson 区间） |
| 引用与提及分开 | 引用只算答案 sources 里的 URL；提及只算答案可见文本（第十一条纪律 2、3） | 把检索到但未被答案使用的结果算成引用 = 失败 |
| 有效无答案留在分母 | 采集失败单独报告，不算「可见度下降」 | 失败被算成 0 = 失败 |
| 实体一致性 | 官网、Wikidata、LinkedIn、Crunchbase 的名称与描述逐项比对 | 任一平台名称或描述不一致 = 列入修复 |
| 相关性数据标级别 | Ahrefs 一类相关系数只写「相关」，不写成「提升了 X%」 | 出现因果措辞 = 改写 |
| 官方报告优先 | Search Console 生成式 AI 报告、Bing Webmaster 的 AI Performance、Yandex、Naver 的官方报告先于自己抽样 | 有官方报告却只用抽样 = 补官方数据 |

## 七、来源

- 五平台权重与 0.737 相关性：[zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) `skills/geo-brand-mentions/SKILL.md`
- 7/5/3 提示词分类法：[OranAi-Ltd/orangeo-ai-visibility-skill](https://github.com/OranAi-Ltd/orangeo-ai-visibility-skill) `references/prompt-taxonomy.md`
- 品牌提及 3x 相关性主张：geo-seo-claude README 市场数据表
- 第六节：coreyhaines31/marketingskills（四级阶梯）；Pew Research（点击率，一手）；Perplexity 官方文档（Sonar 响应字段）；incognito-54/utsushi（Share of AI Voice 做法，第三方）；Yandex Webmaster、Naver Search Advisor（官方报告，见 geo-evidence）。2026-10-21 核对时，旧版引用的 Amsive、SimilarWeb、Reuters Institute、Comscore、Goodie 和 DeepSeek 风控数字没有找到一手出处，已删。

## 增量:AI 归因与 SEO×付费重叠(百仓扫描批 1/4)

- 品牌提及归一化=名称+别名+域名统一计数;原始引擎输出全存底供事后重算(elmo 模式);
- **SEO×Ads 四桶 join**(Ryze seo-vs-ads，第三方做法):GSC query 维度×Ads 搜索词报告 90 天——**double-paying**(自然≤3 位还付费,品牌词无竞价者时最浪费)/defensible(竞对在投)/paid-only winners(广告转化但无自然排名=被钱预验证的内容路线图)/organic-only;省额要用「自然点击保留率」估算，保留率没有外部基准，要用本站做小范围暂停广告的实验得出，在此之前不写具体比例;缺一侧账户时明说缺什么。

## 完全装载:AI 引用面五层/prompt 六类/品牌答案监控闭环(百仓深扫)

**AI 引用面 5 层模型**(seomachine ai-citation-targets，第三方做法，本套件口径，层级顺序不是引用概率排名):Tier1 软件评测目录(G2/Capterra/TrustRadius/Product Hunt/**AlternativeTo 对 "alternatives to" 类关键**/**Slant 对 "vs" 类关键**)/Tier2 行业目录/Tier3 "best X" listicle 外联(找作者,给更新数据换收录)/Tier4 Reddit(F5Bot 监控)+Medium/LinkedIn/Quora/YouTube/Tier5 声誉平台(GBP/Trustpilot/应用商店)。监控 5 组 prompt 簇:通用/功能/场景/迁移切换/价格,季度复审。
**6 类商业意图 prompt 生成法**(research-ai-citations):直接推荐/对比/功能/场景/价格/迁移——每类 15-20 条聚成 5-10 簇,实跑 10-15 条关键 prompt;记录品牌是否提及+位置/被引 URL/竞品/**主导来源类型分布(目录/listicle/官网/Reddit)**。
**citation-recipe 反推法**(Ryze):抓自己被引 top 2-3 页反推配方(答案靠前/统计定义/干净标题/schema),再让"有机强但零 AI 引荐"的页照方重构。
**品牌答案监控闭环**(irinabuht):固定品牌 prompt 面板(what is X/X pricing/X vs Y/is X good for Z/X alternatives)按计划跑,**周对周 diff**:新主张/消失提及/情绪漂移;每条错误主张溯源到具体页面;修正三层=出版商外联+自有 FAQ 明示+**changelog 式页面供 AI 爬虫拾取**。

## 测量口径源码级 + 纪律条款(elmohq/elmo、unifapi-agent/agents 源码深读,2026-10-09；第三方开源工具的做法，本套件口径)

### 波动率与稳定性(elmo visibility-stats.ts)

- **双口径刻意分开**:set volatility=相邻日引用域名集合的 Jaccard 距离均值;weighted volatility=逐日引用份额向量的 Bray–Curtis 距离均值。两者近正交——一个每天有单一主导源+嘈杂长尾的 prompt,按集合看动荡、按量看稳定;**「答案到底由谁承载」以 weighted 为准**,产品 Stability = round((1−weighted)×100)。dayTransitions(相邻日转换数)作可靠性闸门,<2 天返回 null 不硬算。
- **share 只存精确比率、显示层各自 round 一次**:预舍入会让表格/环形图/趋势互相差 1 个点。
- **LVCF 平滑**(per-prompt last-value-carried-forward):每个 prompt 的最近一次观察 carry 到它没跑的日期,再逐日求和——错开的 prompt 日程不再产生假 dip;carry 预置最早观察避免爬坡凹陷。排行榜用同一规则 carry 到末日求和:headline/环形图/表格与趋势线终点天然一致(不能用全窗聚合,否则与线对不上)。

### Query fanout 口径(elmo fanout-analysis.ts + README 方法论五步)

- 读时排除两类条目:与 prompt 逐字相同的查询(引擎确实会原样搜 prompt,但重复不说明「改写」,而本分析只看改写);`unavailable` 哨兵(搜索发生了但查询串不暴露的 provider)。因此从不暴露搜索的引擎贡献 0 行,而不是拉低均值。
- 产出指标:avgPerExecution(**分母只计发生 fanout 的 run**);topByPrompts(触达最多不同 prompt 的查询,跨 prompt 广度)与 topByRuns 分列;wordChanges(引擎 added/dropped/preserved 了 prompt 的哪些词,按次数加权)——回答「内容要赢的是引擎实际发出的搜索,不是你想优化的原句」。
- 方法论五步:prompt 按品牌定义(向导生成或手写,每个都是潜在客户会问 AI 的问题)→后台 worker 定时跑每引擎(抓真实消费面+模型 API 互补)→每个回答归一化解析(答案文本/引用 URL/fanout 搜索/模型版本;文本扫描品牌名+别名+域名,竞品同样)→**全量入 PostgreSQL 含原始引擎输出,任何指标可重算审计**→聚合出趋势(visibility=提及 run 占比;SoV=对竞品的提及对比;引用按 URL/域/类目上卷)。

### 十一条测量纪律(unifapi-agent geo-methodology.md,措辞照抄要点)

1. 每个测量绑定 surface+prompt+locale+search mode+样本+观察时间,与答案、request id 一起存。
2. **citation 只来自答案的 sources/references;检索到但未使用的搜索结果不是 citation**;citation 域名精确匹配、子域规则显式、URL 变体去重。
3. mention 来自可见答案文本+显式别名;**不得从链接目的地、无关子串、域名匹配推断**;文本匹配仍可能有歧义→保留答案供人工复核。
4. 每个采到的答案中,每个 tracked brand **至多计 1 次**(mention 与 citation 可同答案并存)。
5. **valid no-answer(有效无答案)留在 coverage 分母**;采集失败/unknown 无观察、单独报告;「更多失败不得显示为可见度丢失」。
6. coverage 与 share 是两个指标:coverage 分母=成功 cell 数(多品牌可同现,跨品牌求和可 >100%);share 分母=tracked brands 观察之和(=100%)。**「any tracked brand appeared」做分母的是 conditional coverage,不是 share**;空分母=N/A(null),不是 0。
7. 对比只用两轮**都成功采集的 cell(paired denominator)**并附各自完成率;冻结面板文本、品牌定义、引擎、locale、采样规则、权重后再比。
8. 需求加权口径可选,但必须与未加权并列展示;**weighted coverage 不许叫 share**。
9. 不混合:不同引擎之间、ChatGPT 自然 vs 强制搜索(force_web_search 两态是两个研究)、不同面板、索引语料检索与 live prompt 执行(Google AI Mode 的 result position 不是品牌推荐位)。
10. 单轮不构成排名或编辑效应的证据;多轮比较前先排查引擎/模型切换、答案本身变异、采集覆盖变化,再谈趋势。
11. 预算纪律(monitor.mjs runner):先 dry-run;跑前读实时价格表;max_credits 全局上限+每请求 Max-Credits 头(涨价不会静默超支);transport 超时/中断→unknown,**绝不自动重放**(按最大可能成本入账);同快照文件重跑只补 pending cell 不重采成功的。

与第三节(固定提示词集)的衔接:上述纪律即「报告时附样本量与区间」的可执行化——落地时把 6/7/10 写进监控脚本的输出 schema,把 2/3/4 写进解析器。
