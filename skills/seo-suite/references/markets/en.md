# 英文市场专项(基线层)

> 英文是基线,本页收英文区独有增量。建立于 2026-10-09,增量研究窗口 2026-09~10。
> 基线能力(协议层部署细节/爬虫分策/证据分级)在 [agent-readiness.md](../technical/agent-readiness.md)、[agent-protocols.md](../technical/agent-protocols.md)、[ai-crawler-policy.md](../technical/ai-crawler-policy.md)、[geo-evidence-bank.md](../content/geo-evidence-bank.md);本页只记 2026-10 复审发现的**新事实与口径修正**,不重复基线。冲突数字并记不择优。

## 一、引擎与 AI 格局

### 1. AIO 品牌词覆盖 9 月末骤增(2026 最大的英文区事件)

- DemandSphere 日频 SERP 追踪:品牌词 AIO 出现率 9 月大部分时间稳在 ~27%,**9 月 28-29 日跳至 80.23%/82.06%,日内峰值 90.5%**;另一次 100 品牌词手测出现 93 次。Google 无官方说明。
  - 来源:[demandsphere.com/blog/branded-ai-overviews-september-2026](https://www.demandsphere.com/blog/branded-ai-overviews-september-2026)、[Search Engine Land](https://searchengineland.com/google-ai-overviews-jump-branded-queries-september-492962),2026-10 读取。
- Ahrefs 交叉印证:截至 2026-09-29,美国桌面品牌词 AIO 出现率 **82.91%**——双追踪器同向,非单源噪声。
- 口径警示:这是**品牌词**口径,非全查询。全查询口径仍是各家并记(基线纪律不变):
  - Comscore 2026-06:美国桌面 39.4%(同比 +13pp),零点击率 68%;
  - SEMrush 13-14% / Terakeet 52% / SEL 峰值 25% 后回落——引用必须带追踪器名与查询集类型。
- 实操含义:
  1. 品牌词 SERP 审计从"季度"改"月度"——品牌词 AIO 由 Google 生成语义,负面/竞品内容混入的风险窗口随覆盖面放大;
  2. 品牌词承载页(about/定价/对比/评价汇总)逐页按可引性四要素(主体+数字+as-of 日期+方法学)过检;
  3. 品牌词负面出现的处置不再只是 PR 问题,是 GEO 一级工单。

### 2. AI 格局其他增量

- ChatGPT 周活 **12 亿**(2026-09-29 口径)——英文区 B2B 买家人工制品的第一入口假设成立。
- 爬虫构成反转:Q3 2026 **GPTBot 降至 AI-bot 流量 8.05%,OpenAI 搜索索引爬虫翻倍**:
  - 训练爬虫退潮、检索爬虫主导;robots"三类分策"基线不变,但**日志分析勿以 GPTBot 体积外推引用机会**;
  - 反向警示同样成立:封训练爬虫连带封引用爬虫的误杀仍是最常见错误。
- AIO 与 AI Mode 的社媒链接差:**67.66% AIO 响应带社媒链接 vs 32.39% AI Mode**(Social Media Today 汇总口径[待核:测量月])——社媒占位(Reddit/YouTube)对 AIO 的边际收益高于 AI Mode,分产品报告。

### 3. Google 2026-09 spam 更新与更新节奏

- 9/24 启动、**10/8 结束(13 天 16 小时,2025-08 以来最长)**,末段 10/4-7 波动峰值。
- **2026 年已 4 轮 spam 更新(3/6/8/9 月)**,多于 2025 全年;同期 manual actions 上升(PPC Land 报道)。
- Lily Ray 依节奏预测大 core update 临近——英文站监控以 [Google Search Status Dashboard](https://status.search.google.com/products/rGHU1u87FJnkP6W2GwMi/history) 官方时间戳对齐,勿以工具波动单方面定性。

## 二、协议层进展(ARD/WebMCP 采用)

基线(三级发现链/Web Bot Auth/Lighthouse AGENTIC_BROWSING 七审计)见 [agent-readiness.md](../technical/agent-readiness.md)。本轮增量是**采用现实的校准**:

- **ARD 联署扩容**:
  - SEJ 报道 ARD 于 2026-06-17 正式发布,Google 与 **Microsoft/Hugging Face/NVIDIA 等 11 厂商共同署名**,定位"运行时发现层,与 MCP 互补"(亦有"anti-MCP 联盟"的媒体解读);
  - 与套件既有"2026-05 工作组公布"并记——5 月工作组、6 月正式发布,两个里程碑。[searchenginejournal.com](https://www.searchenginejournal.com/the-web-is-growing-a-second-layer-almost-a-third-head/581147)。
- **WebMCP 采用现实核查**:
  - Chrome M149-M156 origin trial 持续 + Edge 平行 trial;
  - 2026-07 长读(Spronta《The State of WebMCP》)确认**规范仍在改、实际采用极低**——公开落地样本是"4 站点×3 个只读工具"级试点(nz365guy);
  - 企业侧卡在治理/权限/审计层未到位(humandelta 观察口径)。
  - 来源:[developer.chrome.com](https://developer.chrome.com/blog/ai-webmcp-origin-trial)、[nz365guy.com](https://nz365guy.com/blog/four-websites-agent-ready-webmcp)。
- 套件立场不变但表述升级:
  1. 协议层仍是"低成本期权",英文站全开的分叉决策不变;
  2. **向客户汇报时应引用本节采用数据**——防止把 ARD/WebMCP 部署当交付成果夸大;
  3. 唯一实证消费者仍是 ChatGPT 桌面浏览器(WebMCP)与零引擎(ARD)——写验收时不承诺引用收益。

## 三、内容规范(可引用块/slop 防御)

基线(段落四要素/句 15-20 词/hype 词 ≤3/页)见 multilingual-workflow.md 英文区专项。增量:

### 1. Reddit 在 ChatGPT 的引用份额塌陷——本页最重要修正

- **最新口径(2026-08,Semrush 数据/Search Engine Land 报道):ChatGPT 引用中 Reddit 份额已跌至 ~0.5%**——塌陷仍在加深,下列早期数字(~10%)是过程不是终点。
- 5WPR《State of AI Citations 2026》:ChatGPT 的 Reddit 引用份额**从 ~60% 跌至 ~10%**。
- Ahrefs Brand Radar 口径:ChatGPT 内 Reddit 引用**降 ~86%**。
- Strivelabs 六研究汇总:**YouTube 已取代 Reddit 成 ChatGPT 第一大被引域**(滚动追踪 YouTube ~26.47% / Reddit ~17.39%)。
- 与套件既有数字的关系:Profound"Reddit 占 Perplexity ~46.7%"**仍成立**——塌陷是 ChatGPT 引擎侧的,Gemini/Perplexity 的 Reddit 依赖未变。按引擎分列的纪律因此又多一条实证。

### 2. YouTube 是被低估的引用面

- Surfer《50 most-cited domains in Google AI Mode》:google.com ~662K / youtube.com ~324K / reddit.com ~151K / facebook 次之。
- Slate 引用研究:YouTube+Reddit 合占社媒引用 ~86%,**YouTube 在全部研究垂类进 top-10**。
- 英文区内容预算含义:视频转录页/YouTube 章节化描述是可引性资产,不只是品牌资产;转录文本按可引块规范(标题+结论句+数字口径)结构化。

### 3. Reddit 高引格式定量

- 万条 Reddit 引用分析(LinkedIn/Nicholas Dulait):被引最多的是**300-600 词长答评论、50+ 赞**——不是帖子本体。
- Reddit 运营按"长答评论"为交付单元设计,而非发帖数;评论区首答的优先级高于自答时间线。

### 4. 引用衰减是常态

- GreenFlag 金融垂类:2025-10 的 215 个顶引页面,**一年后 50%(107 页)零引用**。
- digitalapplied 口径:**57% 被引域不会再被引**。
- 与基线"发布 <3 月内容被引概率 3×"(Kevin Indig)合并成时间纪律:**新鲜度是持续供给,不是一次性刷新**——支柱页配月度增量段(新数字+新 as-of)而非季度大改。

### 5. slop 防御

- 2026 年 4 轮 spam 更新 + manual actions 上升(见一)——AI 生成低增量内容的清理在加强。
- AI 臭 lint(密度判据,方法同源见日区专项)英文站同样适用:英文判据本地化重标(对比构文 "not X but Y"、破折号密度、三段式排比),不直接搬日区阈值。

## 四、外链生态(数字 PR/寄生平台)

- **引用集中度按引擎分列**(Cloro《State of AI Search》):top-10 域名集中度——
  - AI Mode **57.8%**(最集中:Google 生态自引+大站)、Perplexity 27.3%、ChatGPT 25.1%、Copilot 18.3%、Gemini **17.3%**(最分散:长尾机会)。
  - [cloro.dev/research/state-of-ai-search](https://cloro.dev/research/state-of-ai-search)。
- **规模锚点(三套口径并记,引用带出处与月份)**:
  - Surfer 2026-09-01~28:**5.73M 条 ChatGPT 引用**(AI Search Analytics 口径);
  - Ahrefs 2026-07(ChatGPT 全量):Reddit 16.7% / Wikipedia 8.9% / Forbes 3.3%;
  - Resocial 加权(跨引擎):Wikipedia ~32% / Reddit ~21% / 一线编辑媒体 ~14%。
- **引擎间引用集几乎不重叠**:13,184 条引用跨 4 LLM 追踪,**ChatGPT 与 Perplexity 被引域仅重合 5-8%**——"一次优化全网生效"在英文区被证伪;每引擎独立问题集从建议升级为硬约束。
- **寄生平台格局(英文区)**:Reddit/YouTube/Wikipedia 三件套 + Quora/LinkedIn。
- **数字 PR 新出口**:被 AI 高引的垂直媒体榜单化——Surfer top-50 类榜单成为 PR 投放地图:**先查目标域在目标引擎的在场率再投**,不按传统域名权重(DR)投。
- **Reddit 代运营已成产业**(Posirank/Parse 2026 年度机构榜单)——商业化本身是风险信号,见六。

## 五、AI-GEO 测量(fan-out/四级阶梯)

基线(fan-out 三桶/四级阶梯+recommended-against 暗级/DevTools 提取)见 multilingual-workflow.md 与 [geo-platform-differences.md](../content/geo-platform-differences.md)。增量:

- **GA4 内置 AI Assistant 流量渠道**(2026 新):
  - AI 引荐不再混入 Referral,与既有"自定义 channel group"方案并存;
  - **先迁移到内置渠道再对账历史**,避免双口径混报。
- **归因漏损**:
  - TapClicks 口径**~70% AI 引荐被记为 Direct**——AI 流量报告必须先修通道(source regex 含 chatgpt.com/gemini.google.com/perplexity.ai/copilot.microsoft.com 等),否则基线被系统性低估;
  - ChatGPT 外链自带 `utm_source=chatgpt.com`(r/GoogleAnalytics 实证,非 bot);Perplexity/Gemini 无此待遇,勿假设对称。
- **可见度天花板基准**:SearchScore 冻结 2026-07 的 **102,873 域指数**可作英文区横排对照(厂商口径,只作参照不作验收)。
- **fan-out 的引擎侧新增观察**:AIO 品牌词骤增后,品牌词的 fan-out 更可能带修饰词(评测/价格/替代/缺点)——英文站做 fan-out 逆向时,品牌词问题集要单独建组,与品类词的增/删/留三桶分开统计;社媒链接差(一)提示 AIO 的 fan-out 更常落到社媒域,查"社媒占位是否被 fan-out 命中"加入诊断清单。
- 四级阶梯(retrieved→cited→mentioned→recommended)不变;新增**衰减复测节奏**:
  - 引用衰减数据(三)支持复测周期定为**月度**;
  - 顶引页面流失 ≥30%/季即触发内容供给管线检查;
  - 品牌词 AIO 覆盖(一)与引用份额(三)两指标每月随监控报告刷新。

## 六、红旗(买提及/llms.txt 迷思)

- **Reddit 引用代购 = inauthentic mentions 的具象化**:
  - Reddit 代运营机构产业化(四)+ Google 2026 年 manual actions 上升(一)+ Google 官方点名"追逐不真实提及"是 spam 风险——三线交汇;
  - **买赞/代发长答评论进红旗清单第一格**;Reddit 自身反 astroturfing 检测同向收紧,账号史与投放痕迹都是取证面。
- **单平台独大策略的塌陷风险**:Reddit 份额 ~60%→~10% 用一年走完——任何"押注单一被引平台"的方案(含全押 YouTube)都应写进这一条风险对称性。
- **llms.txt 迷思**(基线重申+升级):Google 官方三连(不需要新机器可读文件/无 AI 专用 schema/无独立资格门槛)未变;本页新增:WebMCP/ARD 采用极低(二)——**协议层交付物不得作为 KPI 或效果承诺出售**。
- **数字冲突纪律**:同一指标多套口径(Reddit 份额 10%/16.7%/21%/46.7% 因引擎与月份而异)——客户材料引用任一数字必须带引擎名+月份+来源,缺一即删。
- **品牌词 AIO 骤增的合规面**:品牌词 AI 概述中竞品/负面内容的管理只能走内容与实体信号,不存在"申诉删除 AIO"通道——承诺能删的供应商直接列黑。

## 七、工具表

| 工具 | 用途(英文区) | 口径备注 |
|---|---|---|
| DemandSphere 日频 SERP 追踪 | 品牌词 AIO 覆盖骤增监测 | 品牌词口径,月度重跑 |
| Ahrefs(AI Overviews 研究/Brand Radar) | AIO 出现率交叉印证;引用域份额与品牌关联 | 与 DemandSphere 并记 |
| Surfer AI Search Analytics | ChatGPT/AI Mode 被引域 top-50(5.73M 引用口径) | 厂商研究 |
| Cloro State of AI Search | 各引擎 top-10 集中度对照 | 引擎分列输入 |
| GA4 AI Assistant 渠道 + source regex | AI 引荐归因(先修 Direct 漏损 ~70%) | 与旧自定义组对账 |
| Lighthouse 13.5+ AGENTIC_BROWSING(PSI API) | ARD/WebMCP/llms.txt 技术验收 | 免费标准化 |
| Google Search Status Dashboard | spam/core 更新事件对齐(2026 已 4 轮 spam) | 官方时间戳 |
| SearchScore 可见度指数 | 102,873 域横排对照 | 厂商,仅参照 |
| r/SEO + Search Engine Roundtable | 英文圈一手讨论与更新风向 | 与 SEL/SEJ 交叉 |
| Keywords Everywhere AIO 追踪 | 日常低成本 AIO 出现率抽查 | 非验收口径 |

> 复审节奏:本页数字半衰期 6 个月内(引用份额类 3 个月)——AIO 覆盖率与 Reddit/YouTube 份额两指标建议每月随监控报告刷新;协议层采用状态(二)季度复核。

## 来源(2026-10-09 读取)

- DemandSphere:[branded-ai-overviews-september-2026](https://www.demandsphere.com/blog/branded-ai-overviews-september-2026);转述:[Search Engine Land](https://searchengineland.com/google-ai-overviews-jump-branded-queries-september-492962)、[Keywords Everywhere](https://keywordseverywhere.com/news/ai-overviews)、[Safari Digital](https://www.safaridigital.com.au/blog/ai-overview-aio-statistics)
- 2026-09 spam 更新:[Search Engine Land](https://searchengineland.com/google-september-2026-spam-update-done-rolling-out-493550)、[PPC Land(manual actions)](https://ppc.land/googles-september-spam-update-ends-after-13-days-as-manual-actions-rise/)、[Search Engine Roundtable](https://www.seroundtable.com/google-september-2026-spam-update-done-42235.html)
- 引用研究:Surfer [ChatGPT top-50](https://surferseo.com/blog/most-cited-domains-chatgpt) / [AI Mode top-50](https://surferseo.com/blog/most-cited-domains-ai-mode);Cloro [State of AI Search](https://cloro.dev/research/state-of-ai-search);GreenFlag [citation decay](https://greenflagdigital.com/chatgpt-citation-study);5WPR State of AI Citations 2026、Strivelabs 六研究汇总、Resocial(转述口径)
- Reddit 格式:LinkedIn/Nicholas Dulait [Reddit GEO 2026](https://www.linkedin.com/pulse/reddit-geo-2026-5-steps-get-cited-nicholas-dulait-f37pe);机构榜单:[Posirank](https://posirank.com/blog/top-10-reddit-marketing-agencies-for-aeo-geo-2026-guide)、[Parse](https://parse.gl/blog/best-reddit-marketing-agencies-for-ai-visibility-2026)
- 协议层:[Chrome WebMCP origin trial](https://developer.chrome.com/blog/ai-webmcp-origin-trial)、[SEJ/ARD 11 厂商](https://www.searchenginejournal.com/the-web-is-growing-a-second-layer-almost-a-third-head/581147)、[nz365guy 试点](https://nz365guy.com/blog/four-websites-agent-ready-webmcp)
- 测量:GA4 AI Assistant 渠道([WebFX](https://www.webfx.com/blog/ai/google-analytics-ai-assistant-traffic))、Direct 漏损 ~70%([TapClicks](https://www.tapclicks.com/blog/how-to-track-ai-referral-traffic-and-fix-your-marketing-attribution-in-2026))、[SearchScore](https://searchscore.io/research/ai-search-visibility-ceiling-2026)
- 格局:Comscore/零点击([Quartz](https://qz.com/google-zero-click-searches-rate))、社媒链接差(Social Media Today 转述)、GPTBot 8.05%([TechnologyChecker Q3](https://technologychecker.io/blog/chatgpt-statistics))

## 八、本地实测(2026-10-09)

**跑了什么**:en.wikipedia.org(内容站)+ www.craigslist.org(分类信息/交易站)× `site_audit --market en` / `llmstxt check` / `head_check`;ebay.com、etsy.com 主页对审计 UA 403(见盲区 1)。

**输出摘要**:

- **wikipedia**:desc 缺失 CRITICAL(首页确实无 meta description)、2 个 H1、669 链接>100、alt 缺 5/23;**四条 AI 检索爬虫全放行**——与"被引最多域名"地位自洽;llms.txt 404(判无,准确);head_check ERROR=`link rel=edituri` 弃用,og:image 绝对 URL 通过。
- **craigslist**:title 83 chars **真实超限 60**、2 H1、h1→h4 跳级、html 无 lang、458 链接;AI 爬虫放行;llms.txt 404。
- **etsy(403 站的例外)**:主页 403 挡掉 site_audit/head_check,但 **/llms.txt 200 且是真 llms.txt(首行"# Etsy: official reference for AI assistants")**——大型电商把 llms.txt 当一线实践;同一 UA 下静态文件可取、HTML 应用被墙,三工具中只有 llmstxt 探测穿透。
- head_check 跨站规律:twitter:* 全套弃用 ERROR 在 naver/tistory/note/yahoo 等站也全中——2026 口径判定合理,但头部大站普遍不清理,审计报告须按"行业现状噪音"降档解读。

**工具盲区(实测确认)**:

1. **bot 墙盲区**:ebay/etsy(及 ko 市场 coupang)主页对 stdlib UA 一律 403,site_audit/head_check 完全失效——大站审计需浏览器口径,报告必须标注"未穿透";
2. desc 下限 80 与 en 常规文案实践偏松紧不一(小 desc 常态 WARN),严重度需人工调档;
3. GA/AI 归因类(第五节)不在任何本地工具覆盖内,维持月度手工口径。

## 维护

- 复审周期 **90 天**,下一次 **2027-01-09**;signals 清单与 `scripts/markets.json` 的 `markets.en.review_cycle` 保持一致,以 json 为准。
- 触发即复审的信号:Google Search Status Dashboard(spam/core 更新时间戳)、DemandSphere/Ahrefs 品牌词 AIO 覆盖月度研究、Chrome WebMCP origin trial/ARD 采用进展、GA4 AI Assistant 渠道口径变化、ChatGPT/Perplexity 引用池份额季度研究。
- 断言半衰期 6 个月内(引用份额类 3 个月);etsy llms.txt 存在性与 403 墙组合属可变基础设施,每季抽查。
