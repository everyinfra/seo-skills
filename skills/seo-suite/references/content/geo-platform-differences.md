# AI 搜索平台差异事实库

> 建立于 2026-10-09。事实来源：[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `reference/platform-source-selection.md`（一手厂商文档级，2026-10-04 复核）与 [zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) 平台优化技能。按证据约束改写：厂商文档级事实与社区观察分开标注；未证实处明写。
> 这些是各引擎的**公开行为差异**，不是排名公式。优化建议由此推导，但不应承诺引用结果。

## 一、厂商文档级事实（最可信层）

| 引擎 | 事实 | 级别 |
|---|---|---|
| ChatGPT | `OAI-SearchBot` 供搜索使用；**在 robots.txt 禁它 = 从搜索答案中消失**（导航链接仍可能） | 官方文档 |
| ChatGPT | `ChatGPT-User` 按用户请求抓取，官方声明"robots.txt 规则可能不适用" | 官方文档 |
| Perplexity | `PerplexityBot` 供搜索/链接，**不用于基础模型训练**；`Perplexity-User` "通常无视 robots.txt" | 官方文档 |
| Anthropic | `Claude-SearchBot` 为搜索索引、`Claude-User` 按需抓取；官方声明遵守 robots.txt | 官方文档 |
| Google AIO | 资格 = 已收录 + 可摘要；`nosnippet`/`noindex`/`max-snippet` 会限制 AI 特性 | 官方文档 |
| Google AIO | **`Google-Extended` 不控制 AIO**（只管 Gemini 训练/接地）；AIO 退出开关在 Search Console → 设置（2026-08-31 全量生效） | 官方文档 |
| Google AIO | 无特殊 AI Schema 要求；一次提问可能扇出多次搜索 | 官方文档 |
| Copilot | 与 Bing 共享抓取/收录/排名基础；官方声明"GEO 不保证 grounding 或引用"；IndexNow 可即时提交 | 官方文档 |

## 二、社区观察与相关性研究（次级证据，不外推为算法）

| 引擎 | 观察 | 来源性质 |
|---|---|---|
| Google AIO | 92% 引用来自自然搜索前 10；47% 来自第 5 位以下；~70% 与精选摘要优化重叠；偏好 40–60 词简洁答案块 | 行业研究 |
| ChatGPT | 基于 Bing 索引；引用域中 Wikipedia 47.9%、Reddit 11.3%、YouTube 居前；重实体识别（Wikidata/Crunchbase）；偏好 2000+ 词权威源；每次引 2–4 源 | 行业研究 |
| Perplexity | Reddit 46.7% 居首；社区验证权重最重；每答案 5–15 源（中权站机会多）；**新鲜度强信号** | 行业研究 |
| Gemini | Google 索引 + Google 系资产加权（YouTube 高于一切）；直接消费 Knowledge Graph 与 Schema.org；本地拉 GBP；多模态 | 行业研究 |
| Copilot | LinkedIn/GitHub/Microsoft Learn 加权；meta 描述与精确关键词权重高于 Google | 行业研究 |
| 跨平台 | 仅 11% 域同时被 ChatGPT 与 Google AIO 引用（同一查询） | 行业研究 |

## 三、爬虫分类（决策用）

**引用型 bot（影响搜索答案）**：`OAI-SearchBot`（日频）、`Claude-SearchBot`（按需）、`PerplexityBot`（每周数次）、`Googlebot`、`Applebot`。
**训练型 bot（不影响搜索答案）**：`GPTBot`、`ClaudeBot`、`CCBot`。
**关键推论：禁 `GPTBot` 不阻止 ChatGPT 引用你**——很多站长把两者混为一谈，禁错了对象。Copilot 无独立 bot，读 Bing 索引。

robots 决策速查：

- 想**保留** AI 搜索引用：允许全部引用型 bot；训练型 bot 按品牌偏好决定（不影响引用）。
- 想**退出**某引擎的搜索答案：ChatGPT 禁 `OAI-SearchBot`；Google AIO 用 Search Console 开关（不是 Google-Extended）；Perplexity 禁 `PerplexityBot` 但 `Perplexity-User` 可能无视。
- **没有**"一键全引擎退出"——逐家处理。

## 四、优化侧差异（由上述事实推导的侧重，非保证）

| 平台 | 侧重 |
|---|---|
| Google AIO | 自然排名前 10 是入场券；答案块 40–60 词、先给结论；结构化摘要友好 |
| ChatGPT | 实体建设（Wikidata/Crunchbase 一致性）；2000+ 词权威长文；Bing 收录是前提 |
| Perplexity | Reddit/社区存在感；内容新鲜度（dateModified 与可见日期一致）；中权站机会窗口 |
| Gemini | YouTube 存在感；Schema.org 完整；Knowledge Graph 实体对齐 |
| Copilot | IndexNow 提交；LinkedIn/GitHub 资料；精确关键词在 meta 的权重比 Google 高 |

## 五、引用行为统计（README 或报告可引，均带来源）

- KDD 2024（Princeton/GT/IITD，10K 查询）：GEO 优化可见性 +30–115%；加引号 +41% / 加统计 +33% / 标来源 +28%
- SE Ranking 2025（2.3M 页）：2900+ 词 vs <800 词 = 5.1 vs 3.2 次引用；标题间距 120–180 词 +70% ChatGPT 引用；FAQ 页 4.9 vs 4.4
- Ahrefs（17M 引用）：AI 引用的内容平均新 25.7%；Conductor（13.7K 域）：ChatGPT 占 AI 引荐流量 87.4%
- Kevin Indig（1.2M 答）：44.2% ChatGPT 引用来自页面前 30% 内容
- Seer Interactive：AIO 引用 85% 来自近两年内容
- AirOps 2025：H2/H3 层级 2.8x 引用
- BrightEdge（1M AI 答）：68% 引高权站；43% 引用来自 FAQ 标记页

## 六、市场差异:区域 AI 搜索平台

Google 系之外的 AI 搜索入口,行为与上表五引擎不同,不能套用同一套 GEO 假设:

| 平台(市场) | 已证实行为 | 来源类型 | 实操含义 |
|---|---|---|---|
| **Alice AI / Нейро(Neuro)**(俄) | 答案来源**取自 Yandex 自然 SERP**,不单独爬取不单独排序;Webmaster 有"Alice 可见面板" | Yandex 官方文档 | 经典 Yandex top-10 即引用前提;退出控制仅 `YandexAdditional` |
| **GigaChat 2**(俄,Sber) | 联网检索+编号脚注引用,**仅聊天 App 内显示,API 不带引用** | 官方 FAQ | 品牌抽查须手工在 App 内做 |
| **Naver AI Briefing / AI Tab**(韩) | 引用**几乎全部来自 Naver 自有生态**(Blog/Cafe/지식iN/Premium);覆盖从 ~3% 升至 ~20%(2026) | 行业(Andgentic/The Egg;20% 非官方) | 韩语 GEO=Naver 生态 GEO 优先,自有站其次;ChatGPT/Gemini 是唯一不需 Naver 资产的通道 |
| **Google AIO(日)** | AIO 出现于 **76.9% 日语查询**(1,459 查询);日语 AI 搜索使用率 21.3%→37.0%(2025-05→2026-02) | 行业(Itera/CyberAgent GEO Lab) | 日语区的 AIO 覆盖比英文区更普遍 |
| **ChatGPT(日)** | 对日语国内查询也把 Reddit 引用排第一;Perplexity 偏知恵袋并转向 Wikipedia JP+note.com | 行业(Ahrefs 经 Nikkei;SiTest) | 日语第三方引用面=Reddit+日生态(note/知恵袋/Wikipedia JP) |
| **引用语言绑定(跨市场)** | 西语查询在 AIO/Copilot 得 83–84% 西语引用;西班牙西语查询 7% 引用去 .es 域 vs 英文查询 1.7% | 行业(Temso/Weglot) | **AI 引用审计必须用目标语言提示跑**;>95% 的日语 AI 答案证据来自第三方站(LLMOチェキ 120 万引用) |
| **Wrtn**(韩)/ **本地阿拉伯助手**(Jais/Fanar) | Wrtn >500 万 MAU;阿拉伯助手存在但 ChatGPT 主导使用 | 行业/未证实(份额) | 二线优先级;GPT-4 在阿拉伯方言上显著退化(arXiv:2305.14976)→ MSA 内容更可靠被引 |
| **ChatGPT(印度)** | ~1 亿周活,ChatGPT 第二大市场(Altman 官方口径);AIO 覆盖英语+印地语;罗马化印地文本使 AI 处理掉 5–12 F1(arXiv 2512.10780) | 官方/研究 | 印度 LLM 可见性优先级仅次于巴西;Hinglish 三种书写都要测 |
| **Coc Cốc AI(越南)** | 本地引擎 ~6%,浏览器自带 AI 聊天机器人 | 官方 Play 页 | 越南的小额但独占的本地 AI 面 |
| **Alice AI(俄,2026-10 深化)** | RAG 五步:意图分析→级联子查询→经典索引检索→passage 级神经评估→合成;答案为改写非原文;**官方 Webmaster「SoV 可见度」报告**(3 个月/周更,2026-04 上线);覆盖 42% 查询、4,950 万 MAU;质量框架 ЭПОС;底座 AliceAI-T5-35B 开源 | Yandex 官方 | SoV(非位置)是官方 GEO 计量口径;引用前提仍是经典 SERP 排名 |
| **Naver AI Briefing(官方标准)** | 官方 5 项引用基准:전문성·경험/주제 일관성/진정성·투명성/가독성/활동성·최신성;反模式:无关关键词/**내돈내산·협찬 须明示**/无关图片;图内核心信息必须文本化;机械批量生成被滤;**2026-06 起引用数货币化(메이트,Top10 月 1,000 万韩元)且当选者公开→竞品引用量可侦察** | Naver 官方博客/帮助 | 韩区 GEO 验收用「인용수」做可查基准 |
| **日本引用生态(2026-06)** | 综合 Top:YouTube、**note 第 2**、Wikipedia JP、アメブロ、知恵袋、PR TIMES、Reddit、mybest、楽天——**新闻系全部跌出**;ChatGPT→Reddit/PR TIMES/アメブロ(英文 Wikipedia 排日文之上);Perplexity→知恵袋第 3;垂类(汽车)过半引行业专业媒体 | 行业(Ahrefs 定点) | 盯"行业定番媒体"优于综合榜;PR TIMES=日本特有高引新闻稿渠道 |
| **ChatGPT 5.6 格式动荡(2026-08)** | listicle 引用份额 15.77%→7.80%(−50.5%)、comparison −32.1%、site:/official 检索激增;Gemini/Perplexity 未见同等降权 | 行业(Peec AI) | 被工业化滥用的格式遭检索层降权——格式策略按引擎分平台制定 |
| **AIO vs AI Mode(英)** | 730k 回答研究:两者 **86% 时候引用不同来源**;会话深度 21 秒 vs 49 秒(品牌对比 77 秒) | 行业(Machine Relations 2026-07) | Google 的两个 AI 面分开优化分开验收 |
| **微信搜一搜 AI 问答(中)** | 元宝嵌入搜一搜多触点,公众号被引比例显著高于其他信源;搜一搜排序=Peoplerank,首页公众号获该领域近八成流量(2023 公开课口径) | 官方(公开课)/行业 | 公众号=元宝唯一可运营信源;搜一搜排名是引用前置层 |
| **豆包信源金字塔(中)** | 字节系权重高(头条 ~35.2%+抖音 ~13.5%,行业横评);9/12 题引抖音视频(geo-book 2026-08 实测);高权媒体收录 48h、被引 2–4 周 | 行业/一手实测 | 头条号+抖音图文双发;验收窗口按 2–4 周 |
| **知乎「引证」(中)** | 官方功能:绿色标记有可靠来源、红色标记不可信;但 2026-08 实测知乎几乎未被六引擎引用("知乎修正") | 官方功能/一手实测 | 带来源的机构号回答优先;知乎当"实体存在"做,勿当必然引用渠道 |
| **Reclame Aqui(巴西)** | 巴西投诉平台被 **22.3% 的 ChatGPT 关于巴西品牌的回答引用**(Encontrabilidade);46.5% 消费者用 AI 研究购买而仅 9% 品牌有 AI 策略(Optimiza×AB Pesquisas 2026-02) | 行业研究/商业调查 | SAC 客服响应率正式成为 AI 引用优化手段;RA 也是关键词语料与信任信号——**每市场识别本国"RA 等价物"** |
| **Vibe/ex-Le Chat(法,Mistral)** | 法国本土助手:自建索引+**三爬虫**(`MistralAI-User` 实时/`MistralAI-Index` 索引/`MistralAI-Training` 训练可封);接入 **AFP 通稿(2,300 条/日)**为信源;法国 ChatGPT 46%/Gemini 28%(2026-05);本地商家查询 22.9% 推荐 unique(最独立助手) | 官方文档+行业 | 法语原创内容有被引溢价;**通稿通讯社是被本土 AI 引用的隐藏通道**;主权助手模式会在每个大市场重演 |
| **AIO(印尼)** | 触发率 **37.2% 全球第一**(1.08 亿查询研究,厂商级);引用格局(32k 问答实测):YouTube 12.7% 第一、社交视频占 30.7%、**电商平台被大量引用**(Tokopedia #6/Shopee #9)、品牌官网总份额仅 3.5% 但品牌词查询出现率 72.2% | 厂商研究(标注) | 印尼 GEO=视频资产优先;价格意图让给 marketplace;品牌词是官网唯一主场;`.go.id`/`.ac.id` 是信任引用源 |
| **西语 AI 引用层** | ChatGPT 西语回答存在"半岛偏置"(默认伊比利亚用语,误读拉美缩写)——催生 LatamGPT 等区域模型;西语是 ChatGPT 第一大非英语言(官方) | 智库(Brookings)/行业 | 拉美引用需内容显式区域信号(词汇+实体+本地数据) |
| **阿拉伯内容鸿沟** | 阿拉伯语仅占已知语言网站 **0.6%**(W3Techs)而用户占全球网民 ~5.2%——约 9–10 倍代表性缺口;流传的"3%"无原始出处禁用 | 官方统计+一手仓库核验 | 结构化阿语内容在 AI 引用竞争中近乎空场——阿拉伯 GEO 的量化论据;Fanar(伊斯兰主题强引用)/Jais 为 watch 项 |
| **Yazeka(土耳其)** | 土耳其 Yandex 的 SERP AI 答案**不叫 YandexGPT,叫 Yazeka**(2024-12 上线,仅土耳其市场,土语+英语本地数据集调优,带引用);**土语 AIO 引用 75.3% 来自自然前 10 同页**(美国仅 ~37%,绑定强 2 倍);#1 位 53.4% 被引;社媒/论坛被低引(8.9% vs 份额 13.8%) | 官方新闻稿/本地实测(seobaz 8,282 次移动搜索) | 土语的"社媒= GEO 核心"美式结论**不可平移**——每市场独立测引用转化率;Wordstat TR 2026-01 开放 |
| **ChatGPT(印度,深化)** | **JioHotstar×OpenAI(2026-02)在超 App 内分发 ChatGPT 对话式搜索**(首个大规模超 App 内 ChatGPT);Bain 官方:80% 印度搜索用户 ≥40% 场合依赖 AI 摘要、60% 零点击;GEO 引用拉取 JustDial/IndiaMART/Sulekha 目录 | 官方/行业 | 印度 GEO=目录完整性(JustDial 5,610 万商户)+GBP+平台级引用监测(不只 web) |
| **意大利 AI 引用偏好** | it.wikipedia **48.67% 断层第一**;ilsole24ore 4.48%;**aranzulla.it(个人专家博客)3.24% 第三**;repubblica/corriere/ansa 随后——Reddit/Quora 未进意语前列(Geosnap,113,178 条 AI 回答) | 行业研究 | 意语 AI 引用偏"专家站+财经媒体"而非 UGC;个人专家站可突围;automotive/agroalimentare 是 AI 可见度洼地 |
| **AI 引用按引擎分化(波兰例)** | 同一行业查询 ChatGPT 偏引 PKO Bank、Gemini 偏引 mBank(Basta Digital);ChatGPT 波兰 930 万真实用户(约 1/3 网民) | 行业研究 | **GEO 报告按 AI 引擎分列,不合并统计**(全区通用纪律) |

## 七、来源

- 厂商事实与"禁 GPTBot 不阻止引用"：[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `reference/platform-source-selection.md`、[Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) `docs/ai-bots-reference.md`
- 平台侧重与统计：[zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) `skills/geo-platform-optimizer/SKILL.md`、[onvoyage-ai/gtm-engineer-skills](https://github.com/onvoyage-ai/gtm-engineer-skills)
- 第六节（区域平台）：Yandex Webmaster 官方文档（Alice 取源、YandexAdditional、SoV）；giga.chat 官方 FAQ；Andgentic/The Egg（AI Briefing）；Itera、CyberAgent GEO Lab（日语 AIO）；Ahrefs 经 Nikkei xTREND、SiTest、lizck.com 定点综述（日语引用行为）；LLMOチェキ（PR Times，120 万引用）；Temso、Weglot（引用语言绑定）；arXiv:2305.14976、arXiv:2510.27543（阿拉伯方言退化）；StatCounter/OpenAI/Chosun（Wrtn、巴西采用）；Naver 官方博客 224296857688 与 help.naver.com/service/30056（AI Briefing 标准与메이트）；Peec AI（ChatGPT 5.6 格式）；Machine Relations（AIO/AI Mode）；微信公开课 PRO 2023、卢松松博客（Peoplerank）、极搜AI（元宝）、CSDN 2026-07 横评与 [geo-book](https://github.com/JingHao-Leon/geo-book)（豆包/知乎修正，一手）

## 测量定义层(elmo/seo-monster/indranilbanerjee,百仓扫描批 3-4)

- **query fan-out 分析**:引擎回答前跑了哪些搜索、改写了哪些词(增/删/留三桶)——AI 可见性诊断的第一层数据;
- **引用 URL 五分类**:自有域/竞品域/社媒/Google 资产/机构源——share of voice 按此分层;
- **品牌提及归一化**:名称+别名+域名统一计数;
- **11 个 AI 爬虫 token 角色**(逐条带厂商出处):必须放行=OAI-SearchBot/ChatGPT-User/Claude-SearchBot/Claude-User/PerplexityBot;训练政策项=GPTBot/ClaudeBot/Google-Extended/Applebot-Extended;Perplexity-User 通常忽略 robots;
- **测量注记(防误读)**:GSC AI 报告只有 impressions 无 clicks/CTR/queries;**GA4 AI Assistant 渠道不含 AI Overviews/AI Mode 流量**——AI 流量估算用 AI 引擎 referrer 清单(chatgpt.com/perplexity.ai/gemini.google.com/copilot.microsoft.com)+GA4 渠道组正则+服务器日志三源;"App 内打开常不带 referrer,测得的是下界";
- **Content-Signals 三杠杆姿势顾问**:robots.txt 的 search/ai-input/ai-train 权衡→商业目标→姿势推荐,每次输出强制携带"Googlebot 不遵守、非排名因素"caveat。

## 测量实现口径与 Grokipedia(elmo/kostja94 精读,百仓深扫)

- **query fan-out 三桶判定**(elmo 实现):查询 token 不在 prompt→added;prompt token 不在查询→dropped;都在→preserved;排除两类=与 prompt 完全相同的查询+"unavailable" 哨兵;停用词表**刻意不含** best/top/review/vs/年份(它们是 fan-out 信号本体)。
- **SOV 纪律**:share 只在展示层 round 一次;时序用 **per-prompt LVCF(末值前推)** 消除错峰排期的假 dip;引用波动双指标=set volatility(逐日域名集 Jaccard)+weighted volatility(逐日份额向量 **Bray–Curtis**);Stability=(1−clamp01(wv))×100,<2 天返回 null。
- **五状态差距分类**(unifapi):no answer/采集失败/brand absent/name-only mention/cited brand——**采集失败≠内容缺口**;no-answer 留在覆盖分母作 zero-presence;跨期比较只用两期均成功的 cell(配对分母);mentioned≠cited(文本别名 vs sources 域名)。
- **Grokipedia**(xAI 百科,2025-10 上线,~6M 文章):ChatGPT 13.6M 提示中 ~263K 回复引用(2026-01);场景=小众具体事实查询常列首批来源;**Suggest Article 绝不放 URL**——把自家文章概念改写成中性"aspects to cover"让 Grok 自然发现(反推广红线:严格拒绝推广内容);审核 ~2 小时,状态流 Pending→In Progress→Processing→Created。

## Agent 客户端行为矩阵(claude-seo 深读,2026-10-09)

来源:[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-agentic/references/vendor-matrix.md`(2026-09-23 复核,逐行标 P=一手/S=二手/C=冲突)。这是"引擎"层之外的**agent 客户端**层——它们不检索排名,而是直接读页面替用户行动:

| 客户端 | 读什么 | WebMCP | 身份/robots |
|---|---|---|---|
| ChatGPT 桌面版内置浏览器(site tools) | ARIA/无障碍树(官方 publisher FAQ) | **是,仅命令式**;默认开、仅顶层文档、无 Enterprise/Edu | ChatGPT-User,Web Bot Auth 签名(P) |
| Google: Gemini in Chrome / Chrome auto browse | 页面元素+屏幕坐标 | 无消费公开证据(Google 共同编辑 spec) | Google-Agent(用户触发,通常无视 robots);试验 `agent.bot.goog` 签名(P/S) |
| Microsoft Edge / Copilot Mode | 未文档化 | Edge 支持测试;无 Copilot 消费证据 | 未研究(P/S) |
| Anthropic: Claude for Chrome / computer use | 页面文本、DOM、控制台、网络、截图 | 无(公开 issue 报发现缺失) | ClaudeBot/Claude-SearchBot/Claude-User 全遵守 robots;IP 表在 claude.com/crawling/bots.json(P) |
| Perplexity Comet | 无障碍树+截图 | 无公开信号 | PerplexityBot 遵守;Perplexity-User 通常无视(P) |
| Brave Leo | 未文档化 | 实验性,Nightly flag | 未验证(S) |
| Apple Safari/WebKit | n/a | **反对**(agent 更接近辅助技术,站点不应检测) | n/a(P) |
| Mozilla Firefox | n/a | 中立,不实现 | n/a(P) |

**产品状态注记**(S 级,写报告前重查):ChatGPT Atlas 浏览器 2026-08-09 报道停止;Project Mariner 2026-05-04 报道关闭;Chrome WebMCP origin trial M149–M156、**无 ship 里程碑**;Lighthouse 13.5.0(PSI 同版);Web Bot Auth `draft-ietf-webbotauth-httpsig-protocol-00`(2026-09-01),`Signature-Agent` 已改字典形式 `sig1="https://signer.example"`。

**robots.txt 组选择的三个暗坑**(RFC 9309;access-policy.md):
1. 爬虫只遵守**点名它的最具体组**——存在 `User-agent: GPTBot` 组时,`*` 组对该爬虫整组失效。Cloudflare 托管 robots 把 `Content-Signal:` 放 `*` 组,而规范没有说它能逃逸组选择——**站点有命名组时必须在每组内重复该行**。
2. 5xx robots → 合规爬虫按全站禁用处理;4xx → 视为无限制(与 ai-crawler-policy 一致,此处为 claude-seo 独立复核)。
3. **不要用 IP 封禁 Anthropic 爬虫**——被封的爬虫连 robots.txt 都读不到,等于静默全禁;要区分"真 bot 与伪装 UA"用 Web Bot Auth 签名验证,不封 IP。
4. 两个未证缺口须在报告中明说:无一手来源显示任何消费者 agent 发送 `Accept: text/markdown`;Dia/Opera/Comet 的 agent 动作 robots 行为未验证。

## 爬虫访问层补充与角色混淆警示(geo-seo-claude 深读,2026-10-09)

来源:[zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) `skills/geo-crawlers/SKILL.md`(387 行,三层爬虫参考)。

1. **封锁率基线**(Originality.ai 2025):top-1000 网站中 **35%+ 封至少一个主要 AI 爬虫,5–10% 全封**——多为继承自旧 SEO 配置的激进 robots;封锁 AI 爬虫是"从 AI 答案消失"的最快单一途径。审计时把"意外封锁"当默认怀疑项。
2. **⚠️ 角色混淆警示(方法论样本)**:该仓(高星流行仓库)的爬虫角色表与厂商文档存在三处硬冲突——把 GPTBot 说成"ChatGPT 搜索的动力,封它则 ChatGPT 搜索不收录"(实际搜索是 OAI-SearchBot;禁 GPTBot 不阻止 ChatGPT 引用);把 ClaudeBot 说成"live search/citation"(实际是 Claude-SearchBot;ClaudeBot 是训练);把 Google-Extended 说成"控制 AI Overviews"(实际不管 AIO)。**爬虫角色事实只从厂商 bots 文档取**,流行技能仓库的角色表须逐条对照我们的第三节。
3. **补充爬虫名单**(三层中我们此前未列全的 Tier2/3):GoogleOther(Google 非排名用途/研究抓取)/ Amazonbot(Alexa 与 Amazon AI)/ FacebookBot(Meta AI;链接预览是另一个爬虫,不受影响)/ cohere-ai / anthropic-ai(Anthropic 安全研究+训练的旧 token,与 ClaudeBot 分立)/ Bytespider(字节系;西方市场站点常封,中文市场目标站**必须放行**——见中文指南)。
4. **页级与头级 AI 指令**(新兴非标准,报告须带"草案"标):`<meta name="robots" content="noai">`/`noimageai`(Cloudflare Content Signals 语境的页级退出)、bot 特异 meta(`<meta name="GPTBot" content="noindex">`)、`X-Robots-Tag: noai`/`X-Robots-Tag: GPTBot: noindex`(HTTP 头优先于 meta,且覆盖非 HTML 资源)。
5. **爬虫访问评分结构**(可借鉴):Tier1 放行 50%(每爬虫 20 分)/ Tier2 放行 25% / 无一键全封(`*` Disallow 全站+noai meta)15% / llms.txt+sitemap 对 AI 可达 10%。

## 爬虫三分类与 2026-10 厂商文档更新(geo-score 深读,2026-10-09)

来源:[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `reference/ai-crawlers.md`(三分类框架,逐条厂商出处,2026-10-04 复核)。

1. **三分类取代二分**(robots.txt 里混这三类是 AI 可见性建议最常见错误):**检索爬虫**(真爬虫,为回答用户问题抓页——封它丢的是引用)、**训练爬虫**(为训练语料抓页)、**退出 token**(**不是爬虫、不发请求**——只是声明"其他爬虫抓到的内容可否这样用";长得像 UA 才总被误当爬虫)。`Disallow: Google-Extended` 不会阻止 Googlebot 抓取;`Disallow: Applebot-Extended` 不会把站移出 Spotlight/Siri/Safari 结果。
2. **10 个检索 UA 完整名单**(g.reachable 实测对象):OAI-SearchBot / ChatGPT-User / Claude-SearchBot / Claude-User / PerplexityBot / Perplexity-User / Googlebot(AIO grounding 也用它)/ **Bingbot(喂 Copilot)** / Applebot(Siri+Spotlight 含 AI 答案)/ **Amazonbot(Alexa+Rufus)**——比本文第三节 5 个的名单多出 Bingbot/Amazonbot 两个必测项;用户触发型(ChatGPT-User 等)也算:封它仍是封。
3. **Apple 新事实**(官方 2026-09-04):Applebot-Extended 只管训练 Apple 基础模型;**退出 Apple 的 AI 答案(Siri/Spotlight)用 `nosnippet`**,不是 Applebot-Extended。
4. **Google-Extended 控制全集**:训练未来 Gemini(Gemini Apps+Vertex API 背后的模型)**+ Gemini Apps 与 Vertex AI Grounding 的接地**;Search Console 帮助页也把它列为 AIO/AI Mode 生成模型的训练控制。不影响 Google Search 收录与排名(官方)。
5. **Meta 新爬虫**(官方文档):`Meta-WebIndexer`(改善 Meta AI 搜索结果,Meta 称其帮助 Meta AI 引用并链接站点内容)/`Meta-ExternalFetcher`(按用户请求抓链接、**可能绕过 robots.txt**);`Meta-ExternalAgent` 非纯训练(官方写"训练或通过直接索引内容改进产品")。
6. **Amazon 分类待审**:官方新列 `Amzn-SearchBot`(搜索含 Alexa)与 `Amzn-User`(代用户抓取),并称 Amazonbot 的抓取可能用于训练 Amazon 模型——Amazonbot 仍在检索表但标注待复审。
7. **活体探测的解释限定**:探测从审计者自己的 IP 发厂商 UA 串(非厂商 IP 段);Claude-SearchBot/Claude-User 官方只发布 token,UA 串由 token 构造。**做 IP 段/rDNS 验证的防火墙会拒绝这些探测但服务真爬虫——拒绝只能读作"该服务器拒绝未验证爬虫 UA",不是厂商爬虫被封的证据**。
8. **评分立场**(可借鉴):只对检索爬虫评分——封全部训练爬虫+退出 token**不扣一分**;"允许检索+拒绝训练"是合法姿势。但"不扣分"≠"无代价":封 Google-Extended 同时退出 Gemini Apps/Vertex grounding(见第 4 条),其余(cohere-ai/Bytespider/anthropic-ai/CCBot 下游)代价未知——报告如实分开写。
