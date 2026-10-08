# 品牌提及监控（AI 搜索时代的"外链"）

> 建立于 2026-10-09。权重与平台分布参考 [zubair-trzada/geo-seo-claude](https://github.com/zubair-trzada/geo-seo-claude) `geo-brand-mentions` 技能，按本套件证据约束改写。
> 背景事实：AI 引擎排名中品牌提及与结果的相关性约为外链的 3 倍（行业研究，非官方算法声明）。监控品牌提及因此成为 GEO 监控域的自然延伸。

## 一、五平台加权（0–100 品牌权威分）

| 平台 | 权重 | 看什么 |
|---|---|---|
| YouTube | 25% | 品牌提及量与情感（相关性最强的单一平台，~0.737） |
| Reddit | 25% | 子版块提及、正负情绪、是否被当权威答案引用 |
| Wikipedia / Wikidata | 20% | 词条存在性、实体完整性（sameAs、描述、类别） |
| LinkedIn | 15% | 公司页活跃度、员工提及 |
| 其他（新闻/博客/论坛） | 15% | 独立第三方提及（非自发） |

分档：Dominant 85+ / Strong 70–84 / Moderate 50–69 / Weak 30–49 / Minimal 0–29。

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
- Wikipedia：是否满足收录门槛（注意 COI 政策——自建词条有风险，被独立收录才有价值）
- Crunchbase / LinkedIn / GitHub 组织页：信息一致
- 各平台 sameAs 双向可解析、无死链
- YouTube：品牌频道有实质内容（Gemini/ChatGPT 偏好的引用源）

## 五、KPI 约束（沿用本套件的反虚荣原则）

用：独立提及数、实体一致性得分、固定提示词下的出现率与位置、AI 引用中的品牌出现。
**不用**：总提及数（含自发）、粉丝数、单次爆发帖。

## 六、来源

- 五平台权重与 0.737 相关性：[zubair-trzada/geo-seo-claude](https://github.com/zubair-trzada/geo-seo-claude) `skills/geo-brand-mentions/SKILL.md`
- 7/5/3 提示词分类法：[OranAi-Ltd/orangeo-ai-visibility-skill](https://github.com/OranAi-Ltd/orangeo-ai-visibility-skill) `references/prompt-taxonomy.md`
- 品牌提及 3x 相关性主张：geo-seo-claude README 市场数据表
