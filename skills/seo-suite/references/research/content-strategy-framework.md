# Content Strategy Framework

## 目标
用于做以 SEO 为核心的内容规划，包括：
- content pillars
- topic clusters
- buyer stage mapping
- searchable vs shareable content
- 内容优先级排序

集群怎么拆、内链怎么连，见 [topic-cluster-templates.md](topic-cluster-templates.md)；关键词意图判断见 [keyword-intent-taxonomy.md](keyword-intent-taxonomy.md)。

## 搜索型与传播型内容

### Searchable
- 捕获现有搜索需求
- 适合关键词、问题、教程、模板、比较、替代方案
- 重点：匹配搜索意图、结构清晰、覆盖完整、便于读者和搜索引擎理解

### Shareable
- 创造需求或放大品牌观点
- 适合洞察、数据、争议观点、案例、幕后内容
- 重点：新颖观点、可传播叙事、情绪触发、社会货币

默认优先级：先 searchable，再扩展 shareable。

## Content pillar 识别方法
- Product-led：产品解决什么问题
- Audience-led：目标客户（ICP）需要学习什么
- Search-led：哪些主题有稳定搜索需求
- Competitor-led：竞品已经覆盖但你还没系统布局的主题

## Topic cluster 结构
```text
Pillar Topic
├── Cluster A
│   ├── Article 1
│   ├── Article 2
│   └── Article 3
├── Cluster B
└── Cluster C
```

## Buyer stage 映射

### Awareness
- 修饰词：what is / how to / guide / introduction
- 目标：教育、定义、解释问题

### Consideration
- 修饰词：best / top / vs / alternatives / comparison
- 目标：帮助筛选与比较

### Decision
- 修饰词：pricing / reviews / demo / trial / buy
- 目标：降低购买阻力

### Implementation
- 修饰词：template / example / tutorial / setup / checklist
- 目标：帮助落地与激活

## 优先级评分
以下权重是可调整的起点，按业务目标改：
- Customer impact 40%
- Content-market fit 30%
- Search potential 20%
- Resource requirements 10%

## 输出要求
默认应输出：
1. 3-5 个 content pillars
2. 每个 pillar 的 cluster map
3. buyer stage 对应的主题机会
4. searchable/shareable 分类
5. 优先级排序与为什么先做

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/content-strategy](https://github.com/coreyhaines31/marketingskills/tree/v1.10.0/skills/content-strategy)（MIT）

---

# (marketingskills 深读 2026-10-09b)

补充吸收 coreyhaines31/marketingskills v2.x 的 content-strategy 增量与 copywriting / copy-editing / lead-magnets 三个技能。

## 内容策略 v2.x 增量（content-strategy 2.1.3）

### 信息增益门槛（information-gain gate）
写搜索型内容前先读当前 top 结果，写一句话说明「本文有什么是它们全都没有的」：原始数据、真实产品案例、可用的工具/模板、更清晰的答案、更强的观点。写不出这句话就不写——第 11 篇同质文章，Google 和 AI 助手都没有理由偏好它。

### 赚链接格式实证（Foundation Inc. 2026-03 B2B SaaS 单一厂商研究，方向性参考）
按「反链份额 / 页面份额」倍数排序：

| 格式 | 反链倍数 |
|---|---|
| 统计数据汇编页 | 4.25x |
| 术语/定义页 | 1.47x |
| 互动工具/计算器 | 1.38x |
| How-to 教程 | 1.36x |
| 原创研究报告 | 0.80x |
| 终极指南 | 0.77x |
| 思想领导力 | 0.74x |
| 模板/框架 | 0.68x |

反直觉结论：**策展统计页赚的链接约是原创研究的 5 倍**——作者引用的是让引用最省事的东西，且一行式数据正是 LLM 摘录的对象。做法：(1) 给自己品类做一个持续维护的 stats 页；(2) 做原创研究时配套自己的统计汇编页，把数据产出的链接留在自己手里。底部格式并非无用，只是不赚链接——按各格式承担的任务分别考核。

### 内容日历 60/30/10
- 60% 搜索型（基础盘，可预期捕获需求）
- 30% 传播型（思想领导力、原创数据、观点，赚链接和提及）
- 10% 实验（新格式/渠道的对冲）
起点比率而非规则：新博客可加大搜索型，成熟品牌抢品类话语权可加大传播型。

### Create Once, Distribute Twice + ORB
一篇旗舰内容改造分发到全渠道，胜过每平台现写平庸内容。**分发钩子在创作时就埋进正文**：小标题可独立成帖、章节可整段抽出、引语和数据预先留好做图。ORB = Owned（邮件列表/博客/社区，唯一可积累资产，一切向它汇流）/ Rented（社交平台，算法可一夜清零——Facebook 自然触达从约 20% 跌到 2% 以下）/ Borrowed（播客、客座文章、合作方受众，用于破圈）。失败模式：无旗舰无复用计划的乱撒、押注租来的地、把 90% 精力花在自己不控制的渠道上。

### 选题情报源
- 通话记录：客户提问→FAQ、异议→预防性内容、原话→voice of customer、竞品提及。
- 论坛：`site:reddit.com 主题`（高赞评论验证共鸣）、`site:quora.com 主题`、Indie Hackers / HN / 行业 Slack。
- 竞品：`site:competitor.com/blog` 找高互动文章、重复主题、未覆盖缺口。
- 每篇博客先写 10 个标题再动笔（标题承担大部分效果），计划约 5 轮编辑（结构/清晰/证据/行文/标题 SEO）。

## 文案写作（copywriting 2.1.0）

### AI 破绽黑名单（No AI Tells）
读者（尤其 B2B 买家）识别出 AI 腔后会连带怀疑周边主张。禁写：
1. **对比式揭示**：「It's not X, it's Y」「Not because X. Because Y.」→ 直接说 Y 加理由。
2. **否定清单**：「No X, no Y, no Z」→ 说会发生什么；真实缺失最多留一处近 CTA（No card required）。
3. **拖尾堆叠**：主张后接逗号再补一串从句 → 句子到主张为止。
4. **自问自答与冒号揭示**：「The result? 3x faster.」「The best part: it learns.」→ 正常陈述句（FAQ 和读者的真实疑问除外）。
5. **套话开场**：「In today's fast-paced world」「Whether you're X or Y」「Say goodbye to」「X, reimagined」「Unlock the power of」。
6. **短文案里的破折号**：标题/副标题/广告/主题行不用；长文每页最多 1-2 个。

限量：每区块（hero/一节/一条短帖）最多一个短句片段、一组三连排比。seamless/robust/powerful/unlock/streamline 是占位词——换成它们背后的事实；没有事实就标 `[NEED: ...]`，不编造。**替换测试**：一行字放到竞品官网也成立就重写。

### CTA 公式
[动作动词] + [得到什么] + [限定]：「Start My Free Trial」「Get the Complete Checklist」。避免 Submit / Sign Up / Learn More / Click Here。

### 页面骨架
首屏：标题（单一最重要信息，具体>通用）→ 副标题（加具体性，1-2 句）→ 主 CTA。正文段：社会证明 → 问题/痛点 → 方案/收益（3-5 条）→ 工作原理（3-4 步）→ 异议处理 → 终局 CTA（复述价值 + 风险反转）。清晰度数据（厂商引）：更清晰的定位与文案关联 +81% 转化、38% 更短销售周期、28% 更低 CAC、175% 更多转介绍。

## 文案编辑七遍法（copy-editing 2.1.1）

每遍只查一个维度，改完回查前几遍是否被破坏：
1. **Clarity**：读者能懂吗（拗口结构、指代不清、行话、埋没重点）。
2. **Voice/Tone**：语气是否前后一致（口头开头变公文体）。
3. **So What**：每个主张经得起「那又怎样」吗——缺「which means…」桥就补。
4. **Prove It**：每个主张有证据吗（具名证言、数据、案例；「trusted by thousands」算无证）。
5. **Specificity**：模糊词换数字和时限（save time→每周省 4 小时；many customers→2,847 teams）。
6. **Emotion**：读者有感觉吗（描绘 before 状态、感官语言、微故事）。
7. **Zero Risk**：CTA 旁的阻力全消了吗（保证、免费试用、no credit card、明确下一步）。

高危文案加**专家面板评分**：3-5 个专家人格各打 1-10 分并给具体批评，先修最低分，迭代到全部 7+、均分 8+。投放级文案必跑；博客可选。

快速词级清理：删 very/really/just/actually/in order to/things/stuff；utilize→use、leverage→use、implement→set up；动词名词化还原（make a decision→decide）；句长常≤25 词；段落 2-4 句。

**内容刷新**（content refresh）：页面会衰减（旧数据、旧案例、品牌漂移）。流量下滑/数据过期/产品变更时触发；做 SERP 差距分析（现排名 vs 当前 top 结果的缺口），按 refresh vs rewrite 矩阵决策。

## 磁铁内容（lead-magnets 2.1.0）

### 五原则
解决一个具体问题（不是宽泛主题）· 匹配买家阶段 · 高感知价值 + 低时间成本（30 分钟内可消费，最好 10 分钟）· 自然通往产品 · 单一格式易消费。

### 按阶段选格式
- Awareness：清单、cheat sheet、入门指南、测验。
- Consideration：比较表格模板、成熟度评估、案例集、选型 webinar。
- Decision：即用模板、免费试用、迁移清单、ROI 计算器。

### 门禁与表单
- 门禁四档：全门禁（漏斗底，高捕获低触达）/ 部分门禁（预览+完整版）/ 不门禁+可选（漏斗顶）/ 内容升级（博文+对应加餐，**转化率比通用侧栏 CTA 高 2-5 倍**）。
- 表单每多一个字段，转化降约 5-10%；只要「后续必需的最少字段」。
- 落地页基准：暖流量 20-40% 转化，冷流量 5-15%；交付后看邮件参与度、进试用率、退订率判断线索质量。
- Thank-you 页别浪费：确认送达 + 下一步（demo/试用）+ 预写分享文案。

### 来源（marketingskills 深读 2026-10-09b）
- [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) `skills/content-strategy/SKILL.md`（v2.1.3）、`skills/copywriting/SKILL.md`（v2.1.0）、`skills/copy-editing/SKILL.md`（v2.1.1）、`skills/lead-magnets/SKILL.md`（v2.1.0）（MIT）
- 反链格式数据为该库引述的 Foundation Inc. B2B Backlink Intelligence Report（2026-03），单一厂商研究，作方向性参考
