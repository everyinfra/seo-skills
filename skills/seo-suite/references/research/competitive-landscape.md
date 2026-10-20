# 竞品全景：SEO/GEO 工作台与产品

> 建立 2026-10-10，**2026-10-21 全文复核**：功能、价格、融资和仓库数字逐条回到厂商页面或原始报道；打不开或找不到的，数字已删，不写成事实。目的：找出 seo-suite 可借鉴的功能设计，以及我们在市场里的位置。
> 取数口径：厂商功能写"厂商自述"；仓库数字取 GitHub API 或 README（2026-10-21）；融资和收购写公司公告或报道来源。产品功能和定价半衰期 3–6 个月，行业数据 6–12 个月。

## 一、企业级闭源平台

| 平台 | 厂商页面能核对的内容（2026-10-21） | 值得借鉴的设计 |
|---|---|---|
| Conductor | 2022-02 收购 ContentKing（[Search Engine Land](https://searchengineland.com/conductor-acquires-contentking-380357)），2023-02 收购 Searchmetrics（[SEJ](https://www.searchenginejournal.com/from-competitors-to-partners-conductor-acquires-searchmetrics/478767/)）；[监控页](https://www.conductor.com/platform/monitoring/)写"最多 60 个月的变更历史"，告警"按合适的敏感级别路由给合适的人" | 变更日志留档；告警按敏感度和责任人路由 |
| BrightEdge | [Insights 页](https://www.brightedge.com/solutions/insights)：把所有行动"排进一个简单的信息流，最关键的放最上面" | 把成百上千个变化收敛成一条按优先级排序的行动流 |
| seoClarity | [预测页](https://www.seoclarity.net/seo-forecasting-tool)：写"六步"建立 SEO 商业方案；"即使没有排名数据"也能用历史数据、站点分析和搜索分析预测流量潜力；用 GSC 的 CTR、站点分析的 CVR 和 AOV | 无排名数据也能建模；见 [forecast.py](../../scripts/forecast.py) |
| Sistrix | [可见度指数计算页](https://www.sistrix.com/visibility-index/calculation/)：计算公开，三步——收集约一百万个有代表性的关键词的搜索结果，按搜索量和该自然位置的预期点击率加权，把域名所有排名的加权值相加 | 公式公开，用户能复算 |
| Botify | [AI Readiness 页](https://www.botify.com/platform)：把内容以 agent 偏好的 HTML 或 Markdown 交付；JS 重页面"在 300 毫秒以内"直接提供给 bot | 面向 agent 的内容层（厂商自述） |
| Lumar | [Health Scores 页](https://www.lumar.io/product-guides/general/lumar-health-scores/)：技术 SEO 健康分按 6 个大类（Availability、Indexability、Uniqueness、Discoverability、Rankability、Experience）各给 0–100 分，下分子类；[SEO Traffic Funnel](https://www.lumar.io/product-guides/general/seo-traffic-funnel/) 同样 6 个阶段（Availability→Experience），需连接 GSC | 分类打分加页面流失漏斗 |
| Ryte | [WUX 页](https://en.ryte.com/platform/wux-overview)：WUX Score 是 0–100 的单一指标；总览区分"需立即处理的问题"和"值得探索的机会" | 管理层看一个数，执行者看两栏清单 |

上一版写的 Conductor"一核多形态"、BrightEdge"DataMind 与 Jira 集成"、Sistrix"虚拟域名归因"、Botify"ActionBoard 数千 it depends 场景"、Lumar"Protect 上线前回归拦截"在本次读到的页面里没有对应文字，已删。

## 二、主流 SaaS 与桌面爬虫（打分口径速查）

| 产品 | 公开口径（2026-10-21 读到） |
|---|---|
| Ahrefs | [Health Score](https://help.ahrefs.com/en/articles/1424673-what-is-the-health-score-in-site-audit)：没有 Error 的内部 URL 数除以内部 URL 总数乘 100；"只有 Error 会拉低分，Warning 和 Notice 完全不影响"；分档 Weak 0–30、Fair 31–70、Good 71–90、Excellent 91–100；预设 170+ 个问题，可对项目关闭。DR 在 [DR 说明页](https://help.ahrefs.com/en/articles/1409408-what-is-domain-rating-dr)里是相对量表 |
| Semrush | [Site Health](https://www.semrush.com/kb/114)：得分"不取决于抓取页数，取决于每个错误出现的频率"；[AI Search Health](https://www.semrush.com/kb/1601)是独立得分，检查 8 个主要 AI 爬虫是否被 robots.txt 挡；[问题清单](https://www.semrush.com/kb/542)含 llms.txt 缺失或格式问题、内容过长、Last-Modified 头显示内容"超过六个月未更新"、语义 HTML 占比低、"内容未优化"（标题层级差、段落过长、可读性低）；[Sensor](https://www.semrush.com/kb/652) 波动分 0–10 |
| Moz | [On-Page Grader](https://moz.com/help/research-tools/on-page-grader)：分析 27 个页面内因素，给 0–100 分；因素分"拖累、帮助、全部"三个视图 |
| Screaming Frog | [Issues 页](https://www.screamingfrog.co.uk/seo-spider/issues/)："300 多个 SEO 问题、警告和机会"，分 Issue、Warning、Opportunity 三类；页面写明"问题指引由职业 SEO 手写" |
| Sitebulb | [Hints 页](https://sitebulb.com/features/prioritized-hints/)：300 多条检查；每条标 Critical、High、Medium、Low；说明按"第 1 句：这是什么问题；第 2 句：为什么可能出问题"的固定写法；带"Learn more"链接 |
| SpyFu | [首页](https://www.spyfu.com)：AI 站点审计"把问题变成可审阅、可立即发布的修复"，连接站点一次、逐条批准后上线 |

## 三、内容优化工作台

| 产品 | 机制要点（2026-10-21 读到） |
|---|---|
| Surfer | [Content Score 文档](https://docs.surferseo.com/en/articles/5700317-what-is-content-score)：总分之外有 SEO Score 和 AI Search Score；AI Search Score 0–100，"基于两个"维度。[百万 SERP 研究](https://surferseo.com/blog/surfer-content-score-study/)：10,000 个查询、1,000,000 个 SERP 条目，Content Score 与排名的 Spearman 相关为 0.28；按意图分：consequence 0.296、definition 0.271、comparison/reason/exploratory 0.22–0.23、instructional/short fact 0.19；建议目标分 70–85。**这是 Surfer 自家产品指标的自家研究**，不是 Google 信号 |
| Clearscope | [评分说明](https://www.clearscope.io/support/how-does-clearscope-grade-your-content)：按排名靠前内容里术语出现的情况算重要度，满分 10 为"必含"；"典型使用次数"是范围指引；AI Term Presence 标出某术语是否出现在 Gemini 或 GPT 的回答里 |
| MarketMuse | [对比文章](https://blog.marketmuse.com/marketmuse-vs-frase/)：Optimize 为一个主题给出 50 个相关话题；每个话题被提到一次得 1 分，每个话题最多 2 分，理论满分 100 |
| Frase | [首页](https://www.frase.io/)演示：审计完成后给出 "Fix Pack"，按影响排序，另有起草环节（厂商自述） |
| NeuronWriter | [AI Visibility 页](https://neuronwriter.com/features/ai-visibility/)：对你输入的问题在多个 AI 引擎里监测品牌提及，给出 0–100 的可见度分，并列出"机会" |

上一版写的 Jasper/Copy.ai"Optimization Agent 批量出 brief"、NeuronWriter"Earn mention 与 Optimize 二分"、Frase"Readiness 0–100"本次没有读到对应页面文字，已删。

**行业共识**（本套件观察，非统计）：内容工具把评分分成 SEO 轨和 AI 轨；AI 轨偏向事实或实体覆盖和首屏意图对齐。

## 四、GEO/AI 可见性赛道

| 公司 | 事件或指标（2026-10-21 核对） |
|---|---|
| Profound | 2026-09-15 宣布 D 轮 1.8 亿美元，估值 18 亿美元，Sequoia 与 Kleiner Perkins 联合领投；新闻稿称服务 1,000+ 企业品牌（[公司新闻稿](https://www.tryprofound.com/newsroom/profound-raises-usd180m-series-d-at-usd1-8b-valuation-to-build-the-ai-platform-for-marketing-teams)）。上一版"累计 3.34 亿""首个 GEO 独角兽"新闻稿里没有，已删 |
| Peec AI | 2025-11-17 宣布 A 轮 2,100 万美元，Singular 领投（[TechCrunch](https://techcrunch.com/2025/11/17/as-consumers-ditch-google-for-chatgpt-peec-ai-raises-21m-to-help-brands-adapt/)）。上一版"累计 2,900 万""最多 13 模型""MCP+API"没有读到原文，已删 |
| Scrunch | Sitecore 2026-06-03 宣布收购（[Sitecore 新闻稿](https://www.sitecore.com/company/newsroom/press-releases/2026/06/sitecore-acquires-scrunch-to-help-brands-influence-discovery--and-buying-decisions)）；约 2.25 亿美元的金额来自 Bloomberg 报道（[Bloomberg](https://www.bloomberg.com/news/articles/2026-06-03/sitecore-said-to-acquire-scrunch-for-225-million)），新闻稿未写价格 |
| Semrush | 2025-11-19 Adobe 宣布收购，每股 12.00 美元，股权总价值约 19 亿美元（[Adobe 新闻稿](https://news.adobe.com/news/2025/11/adobe-to-acquire-semrush)） |
| Ahrefs Brand Radar | [产品页](https://ahrefs.com/brand-radar)写"跨 4.93 亿个 prompt 看任意品牌的 AI 可见度"（2026-10-21；该数字随版本变化，第三方文章引用过 2–2.5 亿）。上一版"Claude 消耗 8 倍 checks"未核，已删 |

Otterly、Goodie、Athena、Rankscale、Bluefish 的融资和"赛道洗牌"没有读到一手来源，已删。

**关键行业数据**（引用时附来源和口径）：

- AI 摘要对点击的影响：Pew Research 对 900 名美国成年人浏览数据的分析（2025-03 数据）——出现 AI 摘要的访问里，用户点击传统搜索结果链接的比例为 8%，没有 AI 摘要时为 15%（[Pew](https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/)）。Ahrefs 复测：有 AI Overview 时排名第一页面的平均点击率比无时低 58%，数据为 2025-12，发布 2026-02-04（[Ahrefs](https://ahrefs.com/blog/ai-overviews-reduce-clicks-update/)）。
- AIO 引用来源与自然排名：Botify 2024-12 的分析称 75% 的 AI Overview 链接来自自然排名前 12（[Search Engine Land 报道](https://searchengineland.com/google-ai-overview-links-top-12-organic-rankings-449216)）；Ahrefs 在 863K 个关键词 SERP、400 万个 AI Overview URL 上的更新研究发现只有 38% 的引用页面也在自然前 10，一年前为 76%（[Ahrefs](https://ahrefs.com/blog/ai-overview-citations-top-10/)）。两项研究样本、时间和定义不同，不要混用。
- AI 搜索访客：Semrush 称平均 AI 搜索访客按转化率计，价值是传统自然搜索访客的 4.4 倍（[Semrush](https://www.semrush.com/blog/ai-search-seo-traffic-study/)，发布 2025-07-21；样本为 Semrush 自己的数据，量小）。
- **llms.txt**：Ahrefs 在 137K 个域名上发现 28% 发布了 llms.txt，其中 97% 在 2026-05 当月没有收到任何请求（[Ahrefs](https://ahrefs.com/blog/llmstxt-study/)）；SE Ranking 对约 30 万个域名的分析没发现 llms.txt 与 AI 引用频率有关系（[SE Ranking](https://seranking.com/blog/llms-txt/)）；OtterlyAI 在一个实验站点上 90 天内记录了 62,100+ 次 AI bot 访问，其中 84 次请求 `/llms.txt`，约 0.1%（[Otterly](https://otterly.ai/blog/the-llms-txt-experiment/)）。Google 一侧：Search Central 文档更新日志 2026-06-15 条目 "Clarifying guidance on llms.txt files" 写明，这些文件不是 Google 搜索所需，"不会对可见度或排名产生正面或负面影响"，想为其他服务保留也可以（[更新日志](https://developers.google.com/search/updates)，核对 2026-10-21）。结论：llms.txt 不当可见性杠杆，口径见 [llms-txt-guide](../content/llms-txt-guide.md)。
- 内容特征与 AI 引用：KDD 2024 的 GEO 论文，引语、统计、引用来源三类方法在其基准上相对基线提升约 27–41%（[arXiv 2311.09735](https://arxiv.org/abs/2311.09735)，见 [directory-submissions](directory-submissions.md) 第八节）。Semrush 的 337,785 个唯一 URL 研究（11,882 个 prompt，覆盖 ChatGPT Search、Google AI Mode、Perplexity）：Q&A 格式与引用的关联为 +25.45%；"非促销语气"这一项与引用呈**负**关联（−26.19%），Semrush 自己提醒这不等于模型偏爱促销语，可能是专业写手的文章本身更常被引用（[Semrush](https://www.semrush.com/blog/content-optimization-ai-search-study/)，发布 2026-01-14）。上一版把它写成"促销语气 −26.2%"，方向相反，已改。CXL 对 100 条 AI Overview 引用的分析：55% 的被引段落位于来源页前 30% 内（[CXL](https://cxl.com/blog/google-ai-overview-citation-sources/)，2026-03；抽样小）。
- 删除：Similarweb 口径的"AIO 查询零点击 80–83%"和 ipullrank 的 46.96%（本次未找到原文，且样本口径冲突）；"Wikipedia+YouTube+Reddit+Amazon 占 AIO 引用 38%"（二手来源，未核）。

**指标通行做法**（行业做法，非标准）：mention（含未链接）与 citation 分开；visibility 只能与竞品比较；prompt 库跑多次取多数并标方差；GA4 默认渠道只覆盖部分 AI 来源，AI 来源数字当下限看。本套件的实现见 [citation_panel.py](../../scripts/citation_panel.py) 与 [ai_referral_log.py](../../scripts/ai_referral_log.py)。

## 五、开源与半开源产品

星数、fork 数取 GitHub API（2026-10-21）；功能写法取 README。

| 项目 | 数据 | README 自述的关键设计 |
|---|---|---|
| [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) | 19,460★；2026-02-07 创建；MIT | 26 个 sub-skill、19 个专家 agent；410 个测试（README 徽章）；4 级凭证体系（Tier 0 仅 API key，向上逐级加 GSC、GA4 等）；`/seo doctor`；"可证伪"：每条建议带"怎么知道它失败了"检查 |
| [Ryze-AI-Adgent/open-seo-mcp-skills](https://github.com/Ryze-AI-Adgent/open-seo-mcp-skills) | 6,252★；2026-08-29 创建 | README 主张多数"开源 SEO 工具"只是 DataForSEO API 的壳，自己用 GSC 与 GA4 的真实数据 |
| [Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) | 1,135★ | `uvx` 零配置；检查 27 个 AI 爬虫；`geo fix` 生成修复文件，默认预览、`--apply` 才写盘；CI 里可设 min-score 并输出 SARIF；README 称在 1,800+ 个站点上的自选样本中位 GEO 分为 59/100（样本自选，方向性） |
| [danishashko/geo-aeo-tracker](https://github.com/danishashko/geo-aeo-tracker) | 300★ | Prompt Hub（`{brand}` 注入）、Persona Fan-Out（CMO、SEO Lead、Founder 等变体）、Citation Opportunities（竞品被引你没被引的 URL 与外联简报）、Competitor Battlecards |
| [oneglanse/oneglanse](https://github.com/oneglanse/oneglanse) | 223★ | 在 AI 产品的真实网页上跑 prompt，而不是调 API；README 引 Surfer 的 2026 研究说明两者答案不同 |
| [towfiqi/serpbear](https://github.com/towfiqi/serpbear) | 2,114★ | 开源排名追踪；README 有各 SERP 抓取服务的价格与限额对照表（含 serper.dev 的 $1.00/1000 次） |
| [janreges/siteone-crawler](https://github.com/janreges/siteone-crawler) | 965★ | 已重写为 Rust；质量评分 0.0–10.0；`--ci` 质量门，失败时退出码 10 |
| [seopanel/Seo-Panel](https://github.com/seopanel/Seo-Panel) | 155★ | 老牌 PHP 多站点 SEO 控制面板（需 PHP、MySQL） |
| [harlan-zw/unlighthouse](https://github.com/harlan-zw/unlighthouse) | 4,902★ | 用 Lighthouse 扫整站，带"smart sampling" |
| [seranking/seo-skills](https://github.com/seranking/seo-skills) | 178★ | 厂商官方 skill 仓库；插件内 `mcp.json` 声明托管的 SE Ranking MCP；26 个 skill |

**赛道位置判断**（本套件观察）：开源 SEO 工具的重心从"PHP 面板"转向 Claude skill/插件形态（claude-seo）和自托管的 GEO 追踪。星数是关注度，不是方法质量，见 [niubigeo-deep-read](niubigeo-deep-read.md) 第五节。seo-suite 的差异化：18 个语言市场门户、证据分级与自更新信源循环、纯标准库脚本。短板见仓库 README 与 CAPABILITY_MATRIX，不在此重复数字。

## 六、借鉴清单（合并去重，按价值×可行性排序）

"现状"列对照工作副本（2026-10-21 逐个文件复核存在）。图例：✅＝已实现；✅经 X 覆盖＝未按原案做，由更优形态承接；部分＝注明剩余。每项在 [borrow-specs](borrow-specs.md) 有对应规格。

| # | 借鉴点 | 来源 | 现状 | 落点 |
|---|---|---|---|---|
| 1 | Plugin/Marketplace 打包 | claude-seo、SE Ranking | ✅ | `.claude-plugin/`、PACKAGING.md |
| 2 | Sitebulb 两句话定律，规则目录补解释层 | Sitebulb | ✅ | [audit-rule-catalog](../technical/audit-rule-catalog.md) 解释层 |
| 3 | AI Search Health 独立子分 | Semrush | ✅ | `site_audit.py --json` 的 ai_search_health 节 |
| 4 | 分层 Health Score（Lumar 六类 + Ahrefs 口径并列） | Lumar、Ahrefs | ✅ | `health_score.py` |
| 5 | SEO Traffic Funnel 六阶段 | Lumar | ✅ | `traffic_funnel.py` |
| 6 | content brief 模板套件 | MarketMuse、Frase | ✅ | `templates/content/` |
| 7 | 透明内容评分器 | MarketMuse、Surfer | ✅ | `content_score.py` |
| 8 | 修复草稿 ready-to-review | SpyFu、Frase、geo-optimizer | ✅经 `fix_plan.py` 覆盖 | `fix_plan.py`（默认 dry-run，`--apply` 隔离写盘） |
| 9 | `--compare` 审计对比 | Ahrefs、Lumar | ✅ | `audit_compare.py` |
| 10 | 具名 bulk export 与受影响面% | Screaming Frog、Sitebulb | ✅ | `site_audit.py --export-dir`（每条规则一份清单加 summary.json） |
| 11 | AI visibility 双指标 | Profound、geo-aeo-tracker | ✅ | `citation_panel.py`、`templates/research/prompt-bank.md` |
| 12 | AI 流量归因工具箱 | 行业通行做法 | ✅ | `ai_referral_log.py --classify --attribution` |
| 13 | 过时信号看门表 | claude-seo | ✅ | [deprecated-signals](../technical/deprecated-signals.md) 加 `tests/test_canonical_facts.py` |
| 14 | 凭证分层 doctor | claude-seo | ✅ | `doctor.py` |
| 15 | 条件优先级引擎 | Botify | ✅ | `prioritize.py` |
| 16 | SEO 商业提案六步法 | seoClarity | ✅ | `forecast.py` 加 `templates/monitor/forecast-report.md` |
| 17 | 数据源适配矩阵 | serpbear | ✅ | [data-onboarding](../overview/data-onboarding.md)、[data-source-contract](../overview/data-source-contract.md) |
| 18 | 报告受众三模式 | Sitebulb | ✅ | `templates/audit/report-modes.md` |
| 19 | Opportunity 升为一等类型 | Screaming Frog | 部分 | 已落优先级与规则目录层；`site_audit` findings 仍三态（下游契约） |
| 20 | 免费 checker 即获客 | Ahrefs、SE Ranking | ✅ | README 首屏"60 秒体验" |

候补：Sensor 式自家波动带（[alert-threshold-guide](../monitoring/alert-threshold-guide.md) 扩）、"分数的边界"诚实文案、Wikipedia/Reddit/G2 外部证据缺口清单、`geo fix` 式"先生成后写盘"的安全约定。

## 七、分发形态结论（详见仓库根 PACKAGING.md）

- Skill 是内容，Plugin 是包装，MCP 是数据接口。seo-suite 的本质是知识、流程和标准库计算，属于 skill；MCP 适合接外部付费数据，不适合包装本套件的工作流（本套件判断）。
- 最优组合：Skill（已有）→ Plugin 打包（已做）→ 可选声明式接第三方 MCP。

## 八、检查清单（引用本文件的竞品事实前）

| 检查什么 | 怎么查 | 通过/失败 |
|---|---|---|
| 厂商功能或价格 | 打开厂商页面，记录 URL 和日期；403 的页面用 search MCP 的 `read` | 读到对应文字＝写入并标日期；读不到＝不写 |
| 融资或收购 | 找公司公告或一线报道；价格只有报道的，写"报道称" | 公告和报道不一致时以公告为准并注明差异 |
| 仓库数字 | `gh api repos/<owner>/<repo> --jq '[.stargazers_count,.forks_count,.pushed_at]'` | 数字写取数日期 |
| 行业研究数字 | 打开原文，记录样本量、时间、口径 | 样本或口径对不上＝不并列比较 |
| 借鉴清单的"现状"列 | `ls scripts/<名>.py`、`python3 scripts/<名>.py --help` | 文件存在且参数对得上＝✅ |

## 来源

- 平台：见各表格内链接，2026-10-21 打开。
- 仓库：GitHub API `repos/<owner>/<repo>` 与各仓 README，2026-10-21。
- 研究：Pew、Ahrefs、Botify（经 Search Engine Land）、Semrush、SE Ranking、OtterlyAI、Surfer、CXL、arXiv 2311.09735，链接见正文。
