# 竞品全景:SEO/GEO 工作台与产品(2026-10)

> 建立 2026-10-10。六个并行研究 agent 对五类形态(企业闭源平台/主流 SaaS/内容优化工作台/GEO 创业公司/开源产品)的实测调研,所有条目附一手来源。目的:找出 seo-suite 可借鉴的功能设计,以及我们在市场中的位置。断言半衰期:产品功能与定价 3-6 个月,行业数据 6-12 个月。

## 一、企业级闭源平台

| 平台 | 定位与现状 | 关键设计 |
|---|---|---|
| Conductor | 收购 ContentKing(2022)+Searchmetrics(2023),转型 AEO 平台 | Changelog 60 个月页面快照审计追踪;告警按敏感度×分区×责任人路由;"一核多形态"(平台/API+MCP/Turnkey Agents/LLM Apps) |
| BrightEdge | 老牌企业平台 | DataMind 规定性建议:百万变化收敛为**一条按优先级排序的行动 feed**;Workflow 自动触发任务+审批链+Jira 集成 |
| seoClarity(ArcAI) | 转型 AI 购物可见性 | SEO Forecasting 六步法:GSC CTR→搜索量→CPC→假设提升→ROI 预测,**无排名数据也能建模**(官方 FAQ 公开全流程) |
| Sistrix | 欧洲专业派 | Visibility Index 三步计算**完全公开**("只有理解数据的人才能采取正确措施");SERP 特性挤占的可见性记入"虚拟域名"归因 |
| Botify | 技术派转型 AI Readiness | ActionBoard:优先级=条件规则而非静态表("数千个 it depends 场景");日志级 AI 爬虫行为分析;内容层 HTML/Markdown <300ms 供 agent |
| Lumar(原 DeepCrawl) | 技术审计起家 | **Health Scores 六大类**从 100 扣分制+可调权重;**SEO Traffic Funnel 六阶段页面流失漏斗**;Protect 上线前回归拦截 |
| Ryte | WUX 单一 0-100 KPI | 双层报告:给管理层一个数,给执行者"立即处理/值得探索"两栏降序清单 |

## 二、主流 SaaS 与桌面爬虫(打分口径速查)

| 产品 | 公开口径(可直接引用) |
|---|---|
| Ahrefs | Health Score = **无 Error 的内链 URL 占比**×100(Warning/Notice 不扣分);170+ issue 可全局/项目级关掉并重设严重级;DR 是相对量表(别人涨你也可能跌) |
| Semrush | Site Health 按 error>warning>notice 加权,**与页数无关看 issue 频率**;杠杆规律:修完一整类比分散修单条提分多;**AI Search Health 独立子分**(8 大 AI 爬虫+llms.txt+语义 HTML+Last-Modified);Sensor 0-10 波动分 |
| Moz | On-Page Grader 27 因子,Hurting/Helping/All 三视图 |
| Screaming Frog | 300+ issue 三类型 **Issue/Warning/Opportunity**、22 分类;每条 issue 文档固定结构(去哪看/触发条件/怎么修)+**具名 bulk export**;Custom Extraction 100 提取器(XPath/CSS/regex);"issue 指引由职业 SEO 手写而非 AI" |
| Sitebulb | **两句话定律**:"句 1 这是什么,句 2 为什么可能带来麻烦";每条 Hint 带**受影响 URL 百分比**+反直觉提醒("这类问题不会伤害你的网站");PDF 报告按受众裁剪(高管/开发者/潜客) |
| SpyFu | 2026 最激进形态:审计→**AI 生成修复草稿→人审→一键发布**闭环 |

## 三、内容优化工作台

| 产品 | 机制要点 |
|---|---|
| Surfer | Content Score = SEO 分 + **AI Search Score**(仅两维:Facts Coverage + Upfront Intent Alignment);百万 SERP 研究:分与排名相关 0.28,**按意图分层**(definition 0.27-0.30 / instructional 仅 0.19);Auto-Optimize 一键补缺失术语 |
| Clearscope | 字母分级;术语 1-10 重要度 + **Typical uses 区间** + 已用对照;**AI Term Presence**(标出术语是否出现在 AI 回答里) |
| MarketMuse | **唯一完全公开的公式**:50 相关话题×每话题提及 1 分×单话题封顶 2 分=百分制;三段式 brief(执行摘要/大纲/优化要求)+ 9 种内容类型模板 |
| Frase | 新形态:整站逐页 Readiness 0-100,**Fix Pack 每条修复带预估收益**("answer is buried in paragraph 9, +12");夜间自动审计+起草进 Review queue |
| NeuronWriter | SEO Score(说什么词)+ **AI Score(怎么说:Topic Coverage/Structure/Clarity)**;AI Opportunities 二分:**Earn mention**(去第三方被引页获提及)vs **Optimize**(改自有页) |
| Jasper/Copy.ai | Optimization Agent 批量出 SEO/AEO/GEO brief;SEO/AEO/GEO Rewriter 是年度最受欢迎 agent |

**行业共识(2025-2026)**:内容分拆成 SEO 轨+AI 轨双轨;AI 轨收敛为"事实/实体覆盖 + 首屏意图对齐"两个可解释维度。

## 四、GEO/AI 可见性创业赛道(资本验证的真需求)

| 公司 | 融资/事件 | 指标体系要点 |
|---|---|---|
| Profound | 种子→**D 轮 $180M @ $1.8B(2026-09,首个 GEO 独角兽)**,累计 $334M | mention/citation/sentiment/Agent Analytics;AI Marketer 处理 **citation decay**(引用衰减→自动重写推 CMS);Brand Records 品牌实体档案 |
| Peec AI | A 轮 $21M(2025-11),累计 $29M | 最多 13 模型;提供 MCP+API |
| Scrunch | **被 Sitecore ~$225M 收购(2026-06)** | mention 与 domain link 分开;9 平台流量归因 |
| Semrush | **被 Adobe ~$1.9B 收购(2025-11)** | AI Visibility Score = 你 ÷ 竞品中位数;Prompt Research(AI 版关键词研究) |
| Ahrefs Brand Radar | — | **4 亿+ prompt 预跑存档**;AI SoV;Estimated Impressions 按真实搜索量加权;Claude 消耗 8 倍 checks |
| Otterly/Goodie/Athena/Rankscale/Bluefish($68M)/50+ 长尾 | — | 赛道进入洗牌期;价值从"监测面板"向"监测→归因→执行闭环"迁移 |

**关键行业数据(引用时附来源)**:
- AIO 对点击的影响:Pew 8% vs 15%(2025-07);Ahrefs 更新为 **-58%**(2026-02);ipullrank:AIO 查询零点击 80-83%
- Semrush:AI 搜索访客转化率是自然搜索的 **4.4 倍**(量小质高)
- 75% 被 AIO 引用的域同时位列自然结果 top12(Botify)——GEO 是 SEO 的延伸不是替代
- **llms.txt 裁决**(三份实证):Otterly 90 天实验 0.1% 请求率;Ahrefs 13.7 万域研究 97% 文件整月零请求(AI 消费者最大头是 GPTBot 和 **Claude-Code**);Google 官方"非必需"——**定位为编程 agent 基础设施而非可见性杠杆**
- 什么真提升引用:统计数据/引语/来源 +40%(KDD 2024);Q&A 格式 +25.5%;促销语气 **-26.2%**;前 30% 内容贡献 55% 的 AIO 引用;Wikipedia+YouTube+Reddit+Amazon 占 AIO 引用 38%

**指标通行做法**:mention(含未链接)与 citation 必须分开;ChatGPT=品牌提及渠道(少链接),Perplexity/AIO=引用流量渠道;visibility 只能比竞品(无行业绝对基准);prompt 库 15-50 条起步、跑 3 次取多数并标方差;**AI 流量归因**:GA4 原生只覆盖部分引擎,Claude/Perplexity 需自建 channel 正则,AIO 点击 referrer 是 google.com 无法区分,一切 AI referrer 数字当下限看。

## 五、开源/半开源产品(直接竞品)

| 项目 | Stars/活跃 | 关键设计 |
|---|---|---|
| **AgriciDaniel/claude-seo** | **18,626★**(2026-02 创建,8 个月,410 测试) | 26 sub-skill + 19 agent + 34 命令;**4 层凭证体系**(T0 免费 PSI key→T1 GSC→T2 GA4→T3 Ads);`/seo doctor` 自检;**可证伪方法论**(每条建议附"怎么知道它失败了"+先行指标);FAQ 式过时信号文档(INP 不提 FID、FAQPage 富结果 2026-05-07 停用) |
| Ryze-AI-Adgent/open-seo-mcp-skills | 4,665★(2026-08 创建) | 8 skill 全部标注数据源;主张"竞品是 DataForSEO 套壳,我用 GSC/GA4 真数据" |
| Auriti-Labs/geo-optimizer-skill | 1,026★,PyPI 月下载 1 万 | `uvx` 零配置;27 AI 爬虫检查;**`geo fix` 生成修复文件**(默认预览,`--apply` 才写盘);GitHub Action min-score 质量门+SARIF;发布 State of GEO 基准(1400 站中位 57/100) |
| danishashko/geo-aeo-tracker | 285★ | Prompt Hub({brand} 模板)、**Persona Fan-Out**(CMO/创始人视角变体)、**Citation Opportunities**(竞品被引你没被的 URL+外联简报)、Battlecards |
| oneglanse | 207★ | **在 AI 产品真实网页跑 prompt(浏览器自动化)而非调 API**——测真实用户所见 |
| towfiqi/serpbear | 2,107★ | SERP 抓取源适配层(README 附价格/限额/是否失效对照表) |
| janreges/siteone-crawler | 938★ | Rust 单二进制;三形态(向导/CLI/GUI);**`--ci` 质量门(exit code 10 阻断部署)**;五家包管理器分发 |
| seopanel/Seo-Panel | 155★,v6.0(2026-03) | 老牌 PHP 多站点面板:∞站点+cron 24/7 监控 |
| unlighthouse | 4,892★,npm 月下载 20 万 | **smart sampling**(按路由模板去重采样);官网自带 /llms.txt;免费小工具矩阵获客 |
| seranking/seo-skills | 161★ | 大厂官方 skill 仓库样板:插件内 `.mcp.json` 声明式捆绑官方 MCP,装完即用;26 skill 全部明示 API 调用 |

**赛道位置判断**:2025-2026 开源 SEO 重心从"PHP 面板"两极分化——**Claude skill/插件形态**(claude-seo 18.6k★)与 BYOK 自托管 GEO 追踪。seo-suite 的差异化资本:18 语言市场门户(无人做)、自更新信源循环、38 脚本纯 stdlib 零依赖、75 金标测试。最大短板:无 Plugin/Marketplace 包装(claude-seo 一条命令安装)、内容侧无 brief 模板与评分器。

## 六、借鉴清单(合并去重,按 价值×可行性 排序)

"现状"列对照工作副本真实状态(38 脚本/107 文档/14 模板/75 测试/18 门户),不是安装副本。

| # | 借鉴点 | 来源 | 现状 | 落地 |
|---|---|---|---|---|
| 1 | **Plugin/Marketplace 打包**(2 个 JSON,一条命令安装) | claude-seo/SE Ranking/Zilliz | ❌ 只有 install.sh | 已做:本仓库 `.claude-plugin/` + PACKAGING.md |
| 2 | **Sitebulb 两句话定律**:373 规则目录补 what/why/fix 解释层(先 P0/P1 约 80 条) | Sitebulb/Semrush kb | 部分(规则表有阈值无解释) | 扩 audit-rule-catalog.md |
| 3 | **AI Search Health 独立子分**:AI 爬虫 4→8 个,补 Last-Modified 新鲜度+语义 HTML 占比 | Semrush kb/1601 | 部分(site_audit 查 4 bot) | site_audit.py 扩 check+子分 |
| 4 | **分层 Health Score**:Lumar 六大类 100 扣分制+可调权重;Ahrefs 口径(无 CRITICAL URL 占比)并列输出 | Lumar/Ahrefs | ❌ 只有单页 findings | 新 health_score.py,读 --json 聚合 |
| 5 | **SEO Traffic Funnel 六阶段漏斗**(爬虫+GSC 免费数据可算) | Lumar | ❌ | 新 traffic_funnel.py+模板 |
| 6 | **content brief 模板套件**:三段式+9 内容类型+POV/Expertise/Proof 注入字段 | MarketMuse/Frase | ❌ templates 无 content/ | 新 templates/content/ |
| 7 | **透明内容评分器**:MarketMuse 公开口径(术语×2 分封顶)+ Surfer 双轨(SEO 分+AI 分两维) | MarketMuse/Surfer | ❌ | 新 content_score.py |
| 8 | **修复草稿 ready-to-review**:title/meta/h1/alt 附合市场限值的重写草稿;`--draft-fixes` | SpyFu/Frase/geo-optimizer | ❌ | site_audit.py 加参数+模板节 |
| 9 | **--compare 审计对比**:新增/已修复/分数 delta 三清单;staging vs prod 回归门 | Ahrefs/Lumar Protect | ❌(monitor.py 有页面级 diff) | site_audit.py 存快照+对比 |
| 10 | **具名 bulk export + 受影响面%**:每 rule-id 一个 URL 清单文件 | SF/Sitebulb | ❌ | site_audit.py --export-dir |
| 11 | **AI visibility 双指标**:mention/citation 分开+sentiment+facts_correct;prompt 矩阵(平台×persona×意图)跑 3 次取多数 | ZipTie/Profound/geo-aeo-tracker | 部分(citation_panel.py) | 扩 prompt 矩阵+persona fan-out |
| 12 | **AI 流量归因工具箱**:GA4 custom channel 正则+referrer 矩阵+retrieval/training bot 区分+"数字当下限"警告 | Terminus/Onely | 部分(ai_referral_log.py) | 扩正则输出+警告文案 |
| 13 | **过时信号看门表**:带时间戳的 deprecated 清单(FAQPage 富结果停用、INP 弃 FID 等),涉及 schema 先查表 | claude-seo | ❌ | 新 deprecated-signals.md |
| 14 | **凭证分层 doctor**:探测可用数据源→报告自动声明覆盖范围("无 GSC 数据,排名结论仅基于抓样") | claude-seo | 部分(intake 有问题) | 新 doctor 探测逻辑+报告声明节 |
| 15 | **条件优先级引擎**:"it depends" 规则库(未索引+有历史流量=紧急;未索引+零流量=低) | Botify ActionBoard | ❌ 严重度是静态 | 新 prioritize.py+声明式规则 |
| 16 | **SEO 商业提案六步法+forecast.py** | seoClarity | ❌ | 新脚本+模板 |
| 17 | **数据源适配矩阵**:GSC/GA4/PSI/CrUX/serper.dev/SerpApi 的凭证/成本/限额/边界声明表 | serpbear/SearXNG | ❌ | 新 data-source-adapter-matrix.md |
| 18 | **报告受众三模式**:exec(分数+趋势)/dev(可勾选任务)/prospect(摘要+量级)一表三裁 | Sitebulb | ❌ | 模板加三段渲染说明 |
| 19 | **Opportunity 升为一等类型**(不伤但可赚的项与惩罚叙事分开) | Screaming Frog | ❌ 只有 CRITICAL/WARN/INFO | findings schema 扩 OPP |
| 20 | **免费 checker 即获客**:一条命令出"你的品牌在 N prompt×4 引擎的可见性快照" | Ahrefs/SE Ranking 全员 | 天然具备 | README 首屏放一条命令 demo |

候补:Sensor 式自家波动带(alert-threshold-guide 扩)、DR 式"分数的边界"诚实文案(scoring-rubric 扩)、Wikipedia/Reddit/G2 外部证据缺口清单(Brand Radar 思路)、`geo fix` 式"先生成后写盘"安全约定。

## 七、分发形态结论(详见仓库根 PACKAGING.md)

- **Skill 是内容,Plugin 是包装,MCP 是数据接口**。seo-suite 本质=知识+流程+stdlib 计算,是 skill 的定义域;MCP 适合接外部付费数据(现成 SEO MCP 全是数据套壳),不适合包装我们的工作流。
- 最优组合:**Skill(已有)→ Plugin 打包(2 个 JSON,已做)→ 声明式接第三方 MCP(可选,.mcp.json)**;GH Action 保留。claude-seo 用 8 个月 18.6k★ 验证了这条路的流量。

## 来源(核心)

- Conductor: conductor.com/platform/monitoring · BrightEdge: brightedge.com/solutions/insights · seoClarity: seoclarity.net/seo-forecasting-tool · Sistrix: sistrix.com/visibility-index/calculation · Botify: botify.com/platform · Lumar: lumar.io/product-guides/general/lumar-health-scores + /seo-traffic-funnel · Ryte: en.ryte.com/platform/wux-overview
- Ahrefs: help.ahrefs.com/en/articles/1424673 · 1420169 · 1409408 · Brand Radar 11064852 · llms.txt 研究 ahrefs.com/blog/llmstxt-study/ · Semrush: semrush.com/kb/542 · kb/114 · kb/1601 · kb/1493 · kb/652 · SF: screamingfrog.co.uk/seo-spider/issues/ · Sitebulb: sitebulb.com/features/prioritized-hints/ · Moz: moz.com/help/research-tools/on-page-grader · SpyFu: spyfu.com
- Surfer: docs.surferseo.com/en/articles/5700317 · surferseo.com/blog/surfer-content-score-study/ · Clearscope: clearscope.io/support/how-does-clearscope-grade-your-content · MarketMuse: blog.marketmuse.com/marketmuse-vs-frase/ · Frase: frase.io · NeuronWriter: neuronwriter.com/features/ai-visibility/ · Jasper: jasper.ai/blog/optimize-search-at-scale
- Profound: tryprofound.com + TechCrunch 2026-09-15 · Peec: peec.ai + TechCrunch 2025-11-17 · Scrunch/Sitecore: Bloomberg 2026-06-03 · Semrush/Adobe: news.adobe.com 2025-11 · Otterly: otterly.ai/blog/the-llms-txt-experiment/ · SE Ranking: seranking.com/ai-visibility-tracker.html · ZipTie: ziptie.dev/blog/what-ive-learned-about-ai-search-tracking-tools-from-building-one/ · Onely: onely.com/blog/generative-engine-optimization-geo-checklist-optimize/ · Terminus: terminusapp.com/blog/tracking-ai-referral-traffic/
- 开源: github.com/AgriciDaniel/claude-seo(18,626★) · Ryze-AI-Adgent/open-seo-mcp-skills(4,665★) · Auriti-Labs/geo-optimizer-skill(1,026★) · towfiqi/serpbear · janreges/siteone-crawler · danishashko/geo-aeo-tracker · oneglanse/oneglanse · seopanel/Seo-Panel · harlan-zw/unlighthouse · seranking/seo-skills(161★) · searxng/searxng —— stars 数 2026-10-10 经 GitHub API 复核
