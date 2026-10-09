# 外链质量评估

## 用途

审计外链、评估新增或丢失的链接、做竞品外链差距分析、判断是否需要处理有害链接时读。结果填进 [backlink-report.md](../../templates/monitor/backlink-report.md)。

**数据来源**：你自己的外链工具账号导出（例如 Ahrefs、Semrush、Moz、Majestic），或 Search Console 的「链接」报告。后者只列出 Google 已知链接的一部分样本；各工具的抓取覆盖也不同，数量只能在同一来源内按时间比较。任何结论都要打开链接页抽样人工核实。

## 一、六个评估维度

| 维度 | 看什么 | 加分 | 减分 |
|---|---|---|---|
| 主题相关性 | 链接页和整站的主题是否与目标页有关 | 同一领域、链接页正在讨论相关问题 | 主题完全无关 |
| 来源站点质量 | 有无真实读者、原创内容、编辑标准、可识别的作者或机构 | 有持续更新的原创内容和明确的编辑责任人 | 大量无关出站链接、明显在卖链接、内容拼凑 |
| 位置与上下文 | 链接在正文、侧栏、页脚还是全站模板里；周围文字是否说明了为什么链接 | 正文中作为引用或推荐出现 | 页脚、全站模板、隐藏或堆砌的链接 |
| 锚文本 | 是否描述了目标页内容 | 品牌名、URL、描述性短语自然混合 | 大量完全匹配商业关键词的锚文本 |
| rel 属性 | 普通链接，或 `nofollow`、`sponsored`、`ugc` | 付费或赞助链接已正确标注 | 明显是付费链接却没有标注 |
| 真实流量 | 链接页是否有读者、能否带来引荐访问 | GA4 引荐报告里能看到来自该页的访问 | 链接页没有任何访问迹象 |

按 Google 的[出站链接 rel 说明](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links)，这几个 rel 值对 Google 是提示而不是指令；带 `nofollow` 的链接仍可能带来真实访问和品牌曝光，不等于没有价值。

## 二、打分方法

- 每个维度打 0–2 分（0 差、1 一般、2 好），按权重加总成 0–100 分。
- 默认权重是**可调的经验起点**：相关性 30、来源站点质量 25、位置与上下文 20、真实流量 10、锚文本 10、rel 5。站点类型不同就调整，并在报告里写明用的权重。
- 分数只用于排序和分层（重点维护 / 正常 / 待复核），不是 Google 的评分，也不能预测排名。
- **直接进待复核清单、不看总分**的情形：明显付费却没标注、链接农场或站群特征、被黑页面里注入的链接、与内容无关的全站链接。
- 每条打分都附证据：链接页 URL、链接所在位置的截图或页面摘录、锚文本原文、rel 值。

## 三、DR、DA 这类分数

DR、DA、Authority Score 等是各工具基于自己抓到的链接图算出来的，不是 Google 的指标，不同工具之间不可比。可以作为初筛排序的一个输入，但不能代替打开页面看相关性和上下文，也不要用「DR 低于某值就是垃圾」一刀切。

## 四、有害链接与 disavow

- Google [垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)的「链接垃圾」一节列出了哪些做法属于操纵排名，例如为排名买卖链接、过度交换链接、大规模发布带关键词锚文本的文章。先对照它判断，再谈处理。
- 大多数低质量链接不需要处理。只有当存在大量人为、付费或低质量的外链，并且已经收到人工处置、或很可能因此收到时，才考虑 [disavow](https://support.google.com/webmasters/answer/2648487)。
- 处理顺序：导出并人工核实 → 能联系对方删除的先联系 → 删不掉的才写进 disavow 文件 → 每条记录理由和日期，保留旧版本。
- 不要 disavow 权重低但内容真实的站点；用 `domain:` 整域屏蔽前，先确认该域没有正常链接。
- 怀疑有人恶意制造垃圾外链时，先记录和观察，不要急着批量 disavow。
- 你自己的站点放出的付费或赞助链接标 `sponsored`，用户生成内容里的链接标 `ugc`。

## 五、竞品外链差距

1. 用同一个工具导出本站和几个主要竞品的引用域。
2. 找出链接了多个竞品、却没有链接本站的域名。
3. 按相关性和来源站点质量筛选，不按数量排序。
4. 打开对方链接页，看它为什么链接竞品：资源推荐、引用数据、评测、新闻报道……
5. 判断本站有没有同等或更好的资源；有的话再按 [outreach-templates.md](outreach-templates.md) 起草外联，没有就先补内容。

不要追求复制竞品的每一条链接，也不要追求链接数量。

## 常见误区

- 用 DR 或 DA 阈值一刀切，判定链接好坏。
- 套用网上流传的「理想锚文本比例」「理想 nofollow 比例」。
- 为了让比例「看起来自然」而去制造链接。
- 看到工具标的「有害分数」就批量 disavow。

## 市场差异:本地链接红旗(拉平轮;与 backlink-directory 价带表配套)

| 市场 | 红旗信号 |
|---|---|
| 印尼 | "garansi halaman 1(保首页)"话术;Fastwork Rp15k 级外链;公开叫卖的 PBN;.ac.id 付费链接 |
| 印度 | 排 "SEO India" 词的机构;$99–149/月 PBN 目录层 |
| 越南 | backlink báo 规模化新闻站 sidebar 链(1,500 VND/条级) |
| 泰国 | "หลังบ้าน"灰链网(赌博站 hack);ThaiSEOBoard 交易区低价现货 |
| 德国 | 不标"Werbung"的赞助文——**Abmahnung 律师函风险大于 Google 惩罚**(采购方也担责) |
| 中文 | 假权重(权重词全是无人竞价冷僻长词);蜘蛛池(百度定性黑产) |
| 阿拉伯 | 新闻版面公开售卖(Youm7 级)——链接存在≠编辑认可 |
| 通用 | 价带偏离本地市场均价 ±3 倍即审;dofollow 保证是红旗 |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · monitor/backlink-analyzer/references/link-quality-rubric.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/monitor/backlink-analyzer/references/link-quality-rubric.md)（Apache-2.0）
- 一手资料：[垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)、[出站链接的 rel 属性](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links)、[可抓取链接与锚文本](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)、[拒绝外链（Search Console 帮助）](https://support.google.com/webmasters/answer/2648487)

## (irinabuht12 深读 2026-10-09c)审计增量：可达性战术层、AI 引用源与结构性外链

> 来源：Ryze 系 49 技能仓库 [irinabuht12-oss/marketing-skills](https://github.com/irinabuht12-oss/marketing-skills) 的 `e2e-seo-assistant`、`citation-source-gap-finder`、`ai-visibility-audit`、`programmatic-seo-playbook` 深读。承接上文第五节「竞品外链差距」：差距筛出目标域名之后怎么选战术，以及 AI 搜索时代外链审计要多看两件事。数字均为该仓库口径（2026-09 自报，Ahrefs/站点地图），沿用本目录核验纪律。

### 1. 机会类型 × 努力度（e2e-seo-assistant）

第五节差距分析的输出是一批「链了竞品没链本站」的域名；对每个域名按下表选战术，而不是一律发外联邮件：

| 机会类型 | 怎么找 | 努力度 |
|---|---|---|
| 资源页（resource pages） | 搜「[主题] + resources」 | 低 |
| 未链接的品牌提及 | 品牌监控 | 低 |
| 记者/专家引用（HARO 类） | 记者查询平台 | 低 |
| 失效链接替换（broken link building） | 竞品外链里的 404 页 | 中 |
| 客座发文 | 搜「[行业] + write for us」 | 中 |
| 复制竞品外链 | Ahrefs/Semrush 差集 | 中 |

### 2. AI 引用源可达性评分（citation-source-gap-finder / ai-visibility-audit）

AI 助手的回答只引用一小撮来源——评测平台、对比/listicle 文章、Reddit 帖、官方文档、维基。审计方法：

1. 对品类核心查询，收集 Perplexity / ChatGPT / Google AI Overviews 的回答及其引用 URL。
2. 按来源类型聚类（评测平台 / listicle / 社区 / 编辑内容 / 文档），统计每类的**引用份额**。该仓库案例：某品类 62% 引用集中在 9 个 URL——先看头部集中度再谈覆盖面。
3. 对每个聚类打**可达性分**并配一种战术：季度更新的 listicle → 直接投递更新；G2 类目录页 → 用评论量撬动；Reddit 帖 → 社区参与（有平台规则约束，不是发广告）。
4. 竞品引用地图（ai-visibility-audit）：把竞品被引追溯到具体来源页，逐个判断「本站能否进入同一来源」，比泛泛做外链精准。

判定链接价值时新增一问：**这条链接所在的页面/域名，是不是 AI 回答实际引用的那类来源**。同权重的两条外链，在被引来源上的那条溢出价值更高。

### 3. 结构性外链：产品放出的链（programmatic-seo-playbook Play 5）

审计外链组合时区分两类：内容挣来的链 vs **产品本身放出的链**（Mintlify 模式：产品渲染在客户域名上——文档、widget、托管页、徽章——每个实例默认带一条回链；2,506 个页面换来 19,800 个引用域、DR 90，该仓库 2026-09 口径）。审计自查问题：本站产品能否**默认**在客户站点留一条链？若能，这个杠杆优于任何内容外链；若不能，报告中注明这是组合缺口而非执行问题。

### 4. AI 引用前置条件（对上表「真实流量」维度的补充）

页面想被 AI 引用，除 Google 排名外还需：Bing 有索引（无 Bing 索引 → ChatGPT 不引）、至少一个第三方提及（listicle、Reddit 回答、伙伴文档）。审计高价值页时可把这两项列为检查项。

### 来源（irinabuht12 深读 2026-10-09c）

- [irinabuht12-oss/marketing-skills](https://github.com/irinabuht12-oss/marketing-skills)（49 个单文件技能）：`skills/e2e-seo-assistant/SKILL.md`（机会类型×努力度表）、`skills/citation-source-gap-finder/SKILL.md`（聚类+可达性评分流程与案例）、`skills/ai-visibility-audit/SKILL.md`（竞品引用地图）、`skills/programmatic-seo-playbook/SKILL.md`（Play 5 客户回链与 AI 引用检查，含 2026-09 Ahrefs/站点地图数字）。要点摘写，未复制原文。
