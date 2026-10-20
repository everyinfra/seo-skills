# Routing Rules

> 用途:一句话请求 → 走哪个能力集合、先跑哪个脚本。SKILL.md 的「常见请求如何路由」表是短版,本文是细则和负例。第三方仓库的阅读笔记在文末,只当设计参考,不是搜索引擎规则。

## 第零步:先定市场

任何任务先确认目标市场/语言(18 市场清单见 multilingual-workflow.md)。市场决定引擎格局与工具栈(如俄语区→Yandex、韩语区→Naver);未确认市场前,下面的能力路由结论可能整体不适用。

## 入口判断

### 走 research
当问题核心是“找什么机会做”或“为什么 SERP 长这样”。

关键词：
- keyword
- search intent
- SERP
- competitor
- competitor alternatives
- vs pages
- content gap
- topic cluster
- content pillars

### 走 content
当问题核心是“写什么”和“怎么把页面内容写得更能排名/更能被引用”。

关键词：
- article
- landing page copy
- content brief
- title tag
- meta description
- GEO content
- AI citation
- EEAT
- content refresh
- refresh strategy
- content decay

### 走 technical
当问题核心是“站点结构 / 页面结构 / 抓取索引 / schema / 内链 / 性能 / CWV / 实体信号 / programmatic SEO 实现”。

关键词：
- technical SEO
- indexing
- crawl
- robots.txt
- sitemap
- schema
- breadcrumb
- internal linking
- site architecture
- performance
- Core Web Vitals
- entity
- programmatic SEO

### 走 monitoring
当问题核心是“持续追踪、报告、告警、权威度、外链、排名变化”。

关键词：
- rankings
- keyword positions
- backlinks
- report
- alert
- authority
- domain trust
- trend

## 多路由规则

| 用户问题 | 路由 |
|---|---|
| 为什么这个页面 CTR 低 | content + technical |
| 为什么排名掉了 | monitoring + research + technical |
| 给我完整 SEO 审计 | overview + technical + content |
| 做 GEO 方案 | overview + content + technical + monitoring |
| 做竞争对手 SEO 拆解 | research + monitoring |
| 展示多、点击少,改标题和首段 | content(`question_align.py` + [question-alignment.md](../content/question-alignment.md)) |
| 英文文案按 ASD-STE100 检查 | content(`ste_lint.py` + [asd-ste100-web-writing.md](../content/asd-ste100-web-writing.md)) |
| 接入 GSC / Bing 数据、配 key | overview(`doctor.py --wizard` + [data-onboarding.md](data-onboarding.md)) |
| 把审计发现变成工单并跟进到关闭 | technical(`envelope.py` → `remediation.py`) |
| 评估要不要进新市场 | overview([intake-checklists.md](intake-checklists.md) 目标市场闸门 → [multilingual-workflow.md](multilingual-workflow.md)) |

## 不应误路由的情况

| 需求 | 不要误判为 |
|---|---|
| XML sitemap / crawl / indexing | 单纯的信息架构设计（它们属于 technical 的抓取与索引检查） |
| 页面 CRO 提升转化 | 必须由本 Skill 处理的 SEO 任务 |
| 纯广告投放文案 | content SEO |
| 纯产品分析埋点 | SEO 监控，除非明确与 SEO 归因相关 |

## 检查清单(路由前 30 秒)

| 检查什么 | 怎么查 | 通过 / 失败判据 |
|---|---|---|
| 市场已定 | 请求里有市场或语言;没有就问,单语言站按站点语言推断 | 有明确市场码(18 个之一)。没有就不往下路由 |
| 数据源已知 | `python3 scripts/doctor.py --wizard`(只看键名,不读值) | 报告写明当前 tier(T0–T3)。缺数据走合同表降级列,不编数 |
| 路由对应的脚本真实存在 | `python3 scripts/<名>.py --help` | help 能打开,文中写的参数都在 help 里 |
| 症状先分层 | 点击降/展示降/位置降/收录降/分析工具降,见下文「事故问题按症状形态路由」 | 每个症状只进一条先查的路径,不五个集合同时展开 |
| 日期口径 | GSC 展示数据涉及 2025-05-13 至 2026-04-27 时,两期对比不跨这个期间([Search Console 数据异常记录](https://support.google.com/webmasters/answer/6211453),核对 2026-10-21) | 对比期不跨异常期,或报告里注明展示不可比 |

## 输出优先级规则

1. 先回答用户最直接的问题。
2. 再补充影响最大的相邻问题。
3. 不要一次把五个集合都展开，除非用户明确要整站路线图。

## 诊断管道、症状路由与决策闸门(qiaomu-seo 深读 2026-10-09b)

> 性质:第三方仓库(MIT,2026-08-03 创建)的阅读笔记,不是搜索引擎规则。本节「不能证明」表与闸门是本套件采用的工作口径;其中有 Google 原文可对的句子,已在句内附链接。

来源:[joeseesun/qiaomu-seo](https://github.com/joeseesun/qiaomu-seo) `references/{technical-seo,content-quality,keyword-content,international-commerce}.md` + `scripts/validate_skill.py`。核心工作模式:**按管道阶段路由技术问题,按症状形态路由事故问题,按决策台账路由内容问题,按闸门放行规模化动作**。

### 技术问题先定位管道阶段(七段,不得跨段推断)

`known`(URL 已被发现)→ `allowed to fetch`(robots/基础设施放行具名爬虫)→ `fetched`(HTTP 响应实际取回)→ `rendered`(JS 对具名渲染器执行充分)→ `index eligible`(响应/指令/内容/政策允许收录)→ `canonical selected`(平台聚类重复后选出代表 URL)→ `served`(该查询/市场/设备/时段实际展出)。一段失败不证明后段全败,一段通过不保证下段——**"收录了"和"排上了"是第 6 段和第 7 段,分开核**。

控制语义"不能证明"表(选工具时防越权结论):robots.txt 只管爬虫访问,不证明去索引/canonical/排名;robots meta/X-Robots-Tag 在抓取时才被发现;页面被 robots.txt 禁抓,其中的索引与展示规则会被忽略([Google robots meta 文档](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag),核对 2026-10-21 页面日期 2026-03-24);sitemap 只是发现与变更提示;IndexNow 只是通知,IndexNow FAQ 列出的提交端点是 Amazon、Bing、Naver、Seznam、Yandex、Yep,没有 Google([indexnow.org/faq](https://www.indexnow.org/faq),核对 2026-10-21);canonical 是你对 Google 表达的偏好(Google 称 rel=canonical 是强信号,最终仍由它选定)([Google canonical 文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls),页面日期 2026-07-10);redirect 不证明相关性等价(尤其批量重定向到首页,本套件口径);Google 抓取器默认最多跟 10 跳重定向([Google HTTP 状态码文档](https://developers.google.com/crawling/docs/troubleshooting/http-status-codes),页面日期 2026-02-04)。迁移双闸:上线前(旧 URL 清单+新旧映射分类、重定向/状态码/canonical/hreflang/内链/sitemap/埋点/robots 全测、高价值页与度量连续性保留、DNS 容量与回滚就绪),上线后(新旧主机+日志+索引报告+重要模板复核、重定向保够久、把预期内重抓波动与映射故障分开)。抓取配额工作只对超大/高频变更/已有容量问题的站点先做日志取证;**不承诺"封锁低价值 URL 会把配额转给优选 URL"**——Google 原文:除非已达抓取容量上限,不会把省下的配额转给其它页面;永久删除的页返回 404 或 410([管理抓取预算](https://developers.google.com/search/docs/crawling-indexing/large-site-managing-crawl-budget),页面日期 2026-07-22)。

### 事故问题按症状形态路由(performance-measurement.md)

| 症状 | 先查 |
|---|---|
| 点击降、展示稳 | CTR、结果呈现、意图/SERP 变化、品牌需求、设备/市场结构 |
| 展示点击双降、位置稳 | 需求、季节性、查询组合、统计口径/范围 |
| 位置与展示双降 | 受影响模板/查询、内容与竞争、技术变更、政策与算法更新 |
| 收录量/爬取信号变化 | robots、noindex、canonical、重定向、渲染、宕机、安全、迁移、sitemap/feed |
| 分析工具降、SC 稳 | 埋点本身、同意机制、归因、落地页行为、转化代码 |

同比可比期+季节性+先分段再平均+保留发布时间线;证据淘汰前**多假设并存**。

### 内容问题走决策台账,清理走反保护条款(content-quality.md)

五决策(页级或模板级):`keep`(有用/有战略必要)/`improve`(意图对但缺、旧、弱)/`consolidate`(多页同任务,需查询/页面或 SERP 重叠证据+重定向方案)/`reposition`(页型/意图错配机会)/`remove`(无用户价值/法务安全/过期无替代,需清单+依赖+内链+流量+替代决策)。**反保护条款:不得仅因近期零点击批量删页**——新页、季节页、小众页、导航页、支持/法务页、低量高价值页都可能是必要的;破坏性操作保留决策清单与回滚路径。程序化 SEO 七道闸门全过才放行:①重复用户任务真实存在(非关键词排列组合);②每个可收录页有超越变量替换的页级价值;③数据出处/许可/准确性/新鲜度/缺值行为已定义;④模板暴露可爬 URL、有用导航、正确状态/canonical、稳定渲染;⑤空/重复/不可能/低价值组合被预防或有意排除;⑥分阶段上线+holdout 抽查先于全量曝光;⑦监控覆盖收录/质量/参与/转化/爬取/政策风险。**程序化系统的强度在数据与交互的可辩护性,不在 URL 数量**。AI 辅助不是质量判词:Google 的说法是,用生成式 AI 批量产出没有增加用户价值的页面,可能违反「规模化内容滥用」垃圾内容政策;AI 稿要人工核对事实([Google 生成式 AI 内容指南](https://developers.google.com/search/docs/fundamentals/using-gen-ai-content),页面日期 2026-10-01;[垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies#scaled-content));本套件口径:人写与 AI 辅助同一 usefulness/原创性/事实审查/披露/维护责任标准;拒绝项——竞品摘要改写冒充专业、逐 fan-out 铺页、伪造经验/评论/作者/日期/引用、翻译页无本地审查、自动发布无抽样无回滚。

### 关键词方法的三条排序规则(keyword-content.md)

①聚类证据优先级:同市场/设备/日期的**排名 URL 重叠** > 共同意图与预期页型 > 语义相似——不为每个变体建页;②意图从实际 SERP 判读(信息/导航/商业/交易/本地五类映射到 guide/首页/对比/产品页/地点页),混合 SERP 可能需要多页型或刻意选择最佳拟合意图;③优先级输入显式标签:业务相关与转化价值、需求证据、差异化能力、现实竞争、内容/工程成本、现有页匹配与蚕食风险、依赖(产品/数据/法务/专家审查)——**量/难度缺失时定性排序,字段留 `unknown`,不编数**。国际内容**在目标市场重跑发现与意图分析**,翻译源语言词表不叫研究。

### 国际/电商的结构路由(international-commerce.md)

语言/地区版本用稳定可爬 URL(非 cookie/浏览器切换切换);hreflang 每个版本都要列出自己和全部对应版本,互指缺失只让那一对被忽略,不是整簇作废;x-default 用于「没有匹配语言时的回退页」,常见于语言选择页或自动跳转的首页([Google 多语言文档](https://developers.google.com/search/docs/specialty/international/localized-versions),页面日期 2026-09-21);本地化页通常 canonical 自指而非机械指向原文;不按访客国家或语言自动改内容或跳转——Google 原文:按访客国家或语言返回不同内容的站点,Google 可能不抓取、不索引、不排名全部语区内容([locale-adaptive 文档](https://developers.google.com/search/docs/specialty/international/locale-adaptive-pages),页面日期 2025-12-10)。分页/加载更多:每页稳定 URL+顺序 `<a href>`(爬虫不点交互控件),**不要把分页序列的第一页当成所有分页的 canonical**([Google 分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading),页面日期 2025-12-10),过滤器组合防 URL 无限增生。变体是否独立 URL 由用户意图/可得性/内容/内链/运营定,变体选中态/URL/canonical/价格/库存/图/结构化数据保持一致。**五证据系统分离**:站点 HTML、Product 结构化数据、Merchant feed、自然搜索表现、免费列表/购物表面——feed 过审不证明自然收录,Product 标记不保证富结果,各系统间价格/库存/标识/URL 应一致。缺货/停产/换代决策:留 live+准确库存与替代 / 仅重定向到真等价替代 / 有持久价值留归档页 / 无替代 404 或 410——**不把停产品批量重定向到类目或首页**。

### 包契约与触发路由治理(validate_skill.py;技能工程层)

REQUIRED_FILES 硬契约(22 个必在文件,含 evals/trigger_cases.json、schemas、registry、scripts);**禁止嵌套 SKILL.md**(会破坏可发现性路由);frontmatter description 必须含 seo/audit/keyword/exclude 路由词(缺则警告);SKILL.md 内引用的 references/*.md 链接必须实际存在(悬空即 fail);触发评估三桶:`should_trigger` / `should_not_trigger` / **`near_neighbor`(近邻负例,专防误触发)**——本套件设计触发用例时照此三桶补齐。

## 子代理路由与 TOML 定义模式（codex-seo 深读 2026-10-09b,快照）

> 性质:第三方仓库快照笔记。核对 2026-10-21:该仓库已改名为 [AgriciDaniel/chatgpt-seo](https://github.com/AgriciDaniel/chatgpt-seo)(简介「Turn a page, draft, or SEO export into a sourced fix plan inside ChatGPT」),根目录已无 `agents/` 目录;下文的代理数量和文件结构是 2026-10-09 读到的旧版,**未能在现仓重核**,只当设计参考,不作为该仓现状的描述。

来源(旧版):`agents/*.toml` + `skills/seo/SKILL.md`(编排器)。它把路由拆成「自然语言触发(TOML agent)+ 能力探测加派(编排器)」两层,模式可移植。

**TOML 定义骨架。** 每个代理仅 4 字段:`name`、`description`(同时是触发文本,塞满关键词)、`nickname_candidates`(固定三件套:`seo-x` / `seo x` 带空格变体 / `x` 裸词)、`developer_instructions`(多行字符串即完整 system prompt)。description 写坏代理就路由不到:路由文本与代理一体存放时,要有校验防字段损坏(本套件口径:`self_check.py` 和 `link_check.py` 就是这类校验)。

**指令模板的收敛结构。** 老代理(technical/content/schema/local/performance 等)遵循同一骨架:角色句 → 编号工作流步骤 → 领域参考表(CWV 阈值、E-E-A-T 权重 20/25/25/30、Local 六维权重 25/20/20/15/10/10)→ Cross-Skill Delegation 段 → Output Format 契约(0-100 分、表格、Critical>High>Medium>Low、必须标注数据来源如 "DataForSEO (live)" / "On-page analysis (static)")→ Error Handling 表。新代理(hreflang/images/programmatic/plan)改用紧凑的「Prioritization Logic」段直接定义四级严重度映射,省去重复输出格式——两种粒度按代理复杂度选。

**条件加派靠能力探测,不靠用户口供。** 编排器固定派 8 个常驻代理(technical/content/schema/sitemap/performance/visual/geo/sxo),其余按环境探测加派:`google_auth.py --check` 有凭据 → seo-google;首页检测到本地业务信号 → seo-local;再叠加 DataForSEO MCP 可用 → seo-maps;外链 API key → seo-backlinks;内容策略信号 → seo-cluster;电商信号 → seo-ecommerce;存在 drift 基线 → seo-drift。行业判定(SaaS/本地/电商/出版/代理)来自首页信号词,判定含糊时列前两名候选让用户确认,不硬猜。

**分层降级与配额纪律。** seo-google 分 Tier 0/1/2(API key → +service account → +GA4),每层列出可执行的具体命令;seo-maps 分 Tier 0/1(免费 Nominatim/Overpass vs DataForSEO),Tier 0 时把缺失的 geo-grid 维度权重 25% 重分配(+10 GBP/+10 评论/+5 跨平台),评分体系不因数据缺失而空转。付费调用前必须过 `dataforseo_costs.py check`(approved/needs_approval/blocked 三态,needs_approval 要上报编排器);image-gen 永不自动生成图片,只输出计划(成本控制)。

**防重复路由与代理间总线。** 每个代理写明「不做什么」:seo-maps 明确不重复 seo-local 的页面分析、不重复 seo-geo 的 AI 可见性,改推荐 `/seo local <url>` 交还给对应代理;seo-technical 把 hreflang 细查 defer 给子技能。代理间用 `.seo-cache/` 共享缓存传递上下文(site-meta.json 的 business_type 会影响 schema 分析结论、audit-scores.json、pages/{slug}/*.json),读取三态:找到则引用并注明日期 / 缺失或损坏则当不存在 / 用户说 refresh 则整体忽略——与上文 qiaomu 的闸门思路互补:一个管「放行」,一个管「复用与去重」。

## 技术审计代理的标准作业程序(josstei/maestro-orchestrate 深读 2026-10-09d)

来源:[josstei/maestro-orchestrate](https://github.com/josstei/maestro-orchestrate) `src/agents/seo-specialist.md`(`src/agents/` 下共 40 个代理定义,核对 2026-10-21;该文件现 102 行,frontmatter 有 `max_turns: 20`,旧笔记写的 temperature 与超时设置已不在文件里,删除)。该代理是**只读+shell 跑审计工具**的定位(Lighthouse/结构化数据校验器;不修改代码只出报告);产出按下游分叉:coder 要可直接插入的 JSON-LD 片段+精确文件位置,copywriter 要内容级发现(薄内容/缺 alt/标题结构)。Handoff 契约分 Task Report(状态/文件/决策/验证)与 Downstream Context(接口/模式/假设/警告)两段。其三套决策框架可直接作为本套件技术审计的路由附件。

**可抓性审计五步(先验证"能被抓",再看内容质量——顺序即规则)**:①robots.txt 审查:按全部 user-agent 解析规则,标记封掉关键内容的过宽 Disallow;②sitemap 校验:存在性、XML 合法性、URL 数 vs 实际页面数、lastmod 准确性;③canonical 链分析:逐页追链,标记超过 1 跳的链、指向非 200 页的自指 canonical、冲突信号;④重定向审计:超过 2 跳的 301/302 链、循环、软 404;⑤渲染检查:识别无 JS 执行就不被索引的 JS 依赖内容(与 meta-tag-formulas 的"渲染态审计警告"同源)。**路由含义:请求落在①–⑤任一步的验证上 → 技术审计,不进内容/文案集合。**

**严重度三级(与上文的 H/M/L 不同粒度,审计报告用这级)**:**Critical**=页面完全无法索引(robots disallow、关键页 noindex、canonical 链断裂);**Major**=可索引但信号劣化(缺 canonical、重定向链、结构化数据不完整);**Minor**=优化机会(缺可选 meta、标题层级欠优)。排序铁律:按**实际搜索影响**排,不按理论最佳实践;依据现行引擎指南,不用过时 SEO 迷信。

**schema 选型矩阵(按页面主内容用途选型;必填列已按 Google 文档重写,核对 2026-10-21)**。maestro 原表的「必填」列和 Google 文档不一致:Article 在 Google 文档里没有必填属性;LocalBusiness 必填是 name 和 address,telephone 只是推荐;Event 必填是 name、startDate、location(含 location.name 和 location.address);Product 必填 name,另须 review、aggregateRating、offers 三者之一。FAQPage 和 HowTo 的富结果已不再展示。

| 页面类型 | 主 schema | Google 文档的必填 | 来源(页面日期) |
|---|---|---|---|
| 产品页 | `Product` | name + (review \| aggregateRating \| offers) 三选一 | [Product snippet](https://developers.google.com/search/docs/appearance/structured-data/product-snippet)(2026-09-08) |
| 文章/博客 | `Article` | 无必填;推荐 headline、image、datePublished、dateModified、author | [Article](https://developers.google.com/search/docs/appearance/structured-data/article)(2026-09-08) |
| FAQ 页 | `FAQPage` | Google 自 2026-05-07 起不再展示 FAQ 富结果,文档已移除;只在别的系统需要时保留 | [Search 文档更新记录](https://developers.google.com/search/updates) |
| 指南/教程 | `HowTo` | Google 已不展示 How-to 富结果,结构化数据文档已移除(2023-09 记录) | [Search 文档更新记录](https://developers.google.com/search/updates) |
| 组织 | `Organization` | 无必填 | [Organization](https://developers.google.com/search/docs/appearance/structured-data/organization)(2026-09-08) |
| 本地商家 | `LocalBusiness` | name、address | [Local business](https://developers.google.com/search/docs/appearance/structured-data/local-business)(2026-09-08) |
| 活动 | `Event` | name、startDate、location | [Event](https://developers.google.com/search/docs/appearance/structured-data/event)(2026-09-08) |

校验以 **Google Rich Results Test 要求**为准——schema.org 允许的属性多于 Google 实际用于富结果的范围。反模式清单(路由到"拒答/纠偏"而非执行):关键词堆砌或精确密度目标(现代引擎用语义理解)、报缺 meta keywords(Google 不用 keywords meta 标签,[2009 年博客](https://developers.google.com/search/blog/2009/09/google-does-not-use-keywords-meta-tag)页首注明至今如此,核对 2026-10-21)、schema 与页面实际内容不符、所有页等权对待(按业务价值排序)、任何损害用户体验的 SEO 手法(隐藏文本/堆砌标题/桥页)。
