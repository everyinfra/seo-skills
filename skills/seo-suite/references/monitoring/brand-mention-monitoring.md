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

## 六、市场差异：各市场的监控通道与指标（2026-10-08 一波并入）

**度量升级（源自英文区，全区适用）**：引用四级阶梯 Retrieved → Cited → Mentioned → **Recommended**——推荐主要由站外共识（评论站/分析师/论坛）决定，且有 "recommended against" 暗级（模型点名排除产品）；监控输出用 framing（有利/中立/含糊/负面）而非只计数。观察性基准（单家研究，带机构名引用）：真推荐后一周 +182% 品牌搜索、约 2.5× 新访客（SimilarWeb）；**69% 的自荐型榜单即使被 AIO 引用也不把自己放进推荐**（Amsive，100 条 B2B 查询）。引用≠阅读：AI 答案点击率 ~4%（Reuters Institute）、AIO 引用点击 ~1%（Pew）——KPI 用「AI 回答中出现率」，勿用「AI 流量」单腿。免费 DIY：DevTools Network 面板提取 ChatGPT 真实 fan-out 搜索词；**Perplexity Sonar 返回真实引用 URL，是最可验证的监测探针**（utsushi 的 Share of AI Voice 模式）。

| 市场 | 增补监控通道 |
|---|---|
| 中文 | 采样频控：DeepSeek ~30 问触发风控，分时段 ≤20 问/时段（一手）；指标五项：覆盖率/首屏推荐率/单篇月均被引/90 天留存/同词竞品对比（行业）；微信指数做品牌词趋势；知乎「引证」标记纳入实体一致性检查；参考实现 [DeepSeekGEO/deepseek-geo](https://github.com/DeepSeekGEO/deepseek-geo)（118★）、lymefun-ux/geo-monitor-skill |
| 俄语区 | **Webmaster「Алиса AI 可见度」SoV 报告**（官方，3 个月数据/周更）——唯一官方 GEO 监测口径；Telegram：监控 t.me/s/ 镜像在 Yandex top-30（品牌+品类词）；VK：群名/状态/讨论页三处；红线：行为因素刷量（накрутка ПФ）自动罚 6–12 月 |
| 韩语区 | **AI 브리핑 인용수**：本人可见（채널 홈 프로필：누적/당월/전월）；**竞品若为메이트当选者则公开可查**——韩区竞品 AI 引用监测的唯一官方数据源；`site:도메인`（Naver 搜索栏）=색인 수 基准；주말 하락=평일性 주제 信号 |
| 日语区 | SC「生成AIパフォーマンス」报告（官方）；分引擎分开跟（ChatGPT→Reddit/PR TIMES、Perplexity→知恵袋、AIO→YouTube/note）；垂类词盯行业定番媒体 |
| 英文 | 自托管免费替代栈：elmo/oneglanse/limelit-open；共识档案同步（G2/Capterra/Gartner/Crunchbase 描述与 About 页同段位同类目）；Comscore 2026-06：35% 桌面用户访问 AI 助手；ChatGPT AI referral 份额 89%→63%（Goodie 2026-05，发现渠道碎片化进行中） |

## 七、来源

- 五平台权重与 0.737 相关性：[zubair-trzada/geo-seo-claude](https://github.com/zubair-trzada/geo-seo-claude) `skills/geo-brand-mentions/SKILL.md`
- 7/5/3 提示词分类法：[OranAi-Ltd/orangeo-ai-visibility-skill](https://github.com/OranAi-Ltd/orangeo-ai-visibility-skill) `references/prompt-taxonomy.md`
- 品牌提及 3x 相关性主张：geo-seo-claude README 市场数据表
- 第六节：coreyhaines31/marketingskills（四级阶梯/格式动荡）；Amsive、SimilarWeb、Scrunch（推荐基准，观察性）；Reuters Institute DNR 2026、Pew（点击率）；Comscore、Goodie（碎片化）；JingHao-Leon/geo-book（风控，一手）；incognito-54/utsushi（Share of AI Voice/Sonar 探针）；Yandex Webmaster 官方（SoV）；Naver 메이트 帮助页（인용수 公开）

## 增量:AI 归因与 SEO×付费重叠(百仓扫描批 1/4)

- 品牌提及归一化=名称+别名+域名统一计数;原始引擎输出全存底供事后重算(elmo 模式);
- **SEO×Ads 四桶 join**(Ryze seo-vs-ads):GSC query 维度×Ads 搜索词报告 90 天——**double-paying**(自然≤3 位还付费,品牌词无竞价者时最浪费)/defensible(竞对在投)/paid-only winners(广告转化但无自然排名=被钱预验证的内容路线图)/organic-only;省额=花费×自然点击保留率(保守 50-70%,明示估计);缺一侧账户时明说缺什么。

## 完全装载:AI 引用面五层/prompt 六类/品牌答案监控闭环(百仓深扫)

**AI 引用面 5 层模型**(seomachine ai-citation-targets):Tier1 软件评测目录(G2/Capterra/TrustRadius/Product Hunt/**AlternativeTo 对 "alternatives to" 类关键**/**Slant 对 "vs" 类关键**)/Tier2 行业目录/Tier3 "best X" listicle 外联(找作者,给更新数据换收录)/Tier4 Reddit(高赞老帖评论优于新帖,F5Bot 监控)+Medium/LinkedIn/Quora/YouTube(Perplexity 与 Gemini 交叉引视频)/Tier5 声誉平台(GBP/Trustpilot/应用商店)。监控 5 组 prompt 簇:通用/功能/场景/迁移切换/价格,季度复审。
**6 类商业意图 prompt 生成法**(research-ai-citations):直接推荐/对比/功能/场景/价格/迁移——每类 15-20 条聚成 5-10 簇,实跑 10-15 条关键 prompt;记录品牌是否提及+位置/被引 URL/竞品/**主导来源类型分布(目录/listicle/官网/Reddit)**。
**citation-recipe 反推法**(Ryze):抓自己被引 top 2-3 页反推配方(答案靠前/统计定义/干净标题/schema),再让"有机强但零 AI 引荐"的页照方重构。
**品牌答案监控闭环**(irinabuht):固定品牌 prompt 面板(what is X/X pricing/X vs Y/is X good for Z/X alternatives)按计划跑,**周对周 diff**:新主张/消失提及/情绪漂移;每条错误主张溯源到具体页面;修正三层=出版商外联+自有 FAQ 明示+**changelog 式页面供 AI 爬虫拾取**。
