# Routing Rules

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

## 不应误路由的情况

| 需求 | 不要误判为 |
|---|---|
| XML sitemap / crawl / indexing | 单纯的信息架构设计（它们属于 technical 的抓取与索引检查） |
| 页面 CRO 提升转化 | 必须由本 Skill 处理的 SEO 任务 |
| 纯广告投放文案 | content SEO |
| 纯产品分析埋点 | SEO 监控，除非明确与 SEO 归因相关 |

## 输出优先级规则

1. 先回答用户最直接的问题。
2. 再补充影响最大的相邻问题。
3. 不要一次把五个集合都展开，除非用户明确要整站路线图。

## 诊断管道、症状路由与决策闸门(qiaomu-seo 深读 2026-10-09b)

来源:[joeseesun/qiaomu-seo](https://github.com/joeseesun/qiaomu-seo) `references/{technical-seo,content-quality,keyword-content,international-commerce}.md` + `scripts/validate_skill.py`。核心工作模式:**按管道阶段路由技术问题,按症状形态路由事故问题,按决策台账路由内容问题,按闸门放行规模化动作**。

### 技术问题先定位管道阶段(七段,不得跨段推断)

`known`(URL 已被发现)→ `allowed to fetch`(robots/基础设施放行具名爬虫)→ `fetched`(HTTP 响应实际取回)→ `rendered`(JS 对具名渲染器执行充分)→ `index eligible`(响应/指令/内容/政策允许收录)→ `canonical selected`(平台聚类重复后选出代表 URL)→ `served`(该查询/市场/设备/时段实际展出)。一段失败不证明后段全败,一段通过不保证下段——**"收录了"和"排上了"是第 6 段和第 7 段,分开核**。

控制语义"不能证明"表(选工具时防越权结论):robots.txt 只管爬虫访问,不证明去索引/canonical/排名;robots meta/X-Robots-Tag 只在被抓取后生效,被禁爬虫读不到它;sitemap 只是发现与变更提示;IndexNow 只是通知(且不含 Google);canonical 是偏好表达非强制;redirect 不证明相关性等价(尤其批量重定向到首页);404/410 不保证立即从所有索引移除。迁移双闸:上线前(旧 URL 清单+新旧映射分类、重定向/状态码/canonical/hreflang/内链/sitemap/埋点/robots 全测、高价值页与度量连续性保留、DNS 容量与回滚就绪),上线后(新旧主机+日志+索引报告+重要模板复核、重定向保够久、把预期内重抓波动与映射故障分开)。抓取配额工作只对超大/高频变更/已有容量问题的站点先做日志取证;**不承诺"封锁低价值 URL 会把配额转给优选 URL"**。

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

五决策(页级或模板级):`keep`(有用/有战略必要)/`improve`(意图对但缺、旧、弱)/`consolidate`(多页同任务,需查询/页面或 SERP 重叠证据+重定向方案)/`reposition`(页型/意图错配机会)/`remove`(无用户价值/法务安全/过期无替代,需清单+依赖+内链+流量+替代决策)。**反保护条款:不得仅因近期零点击批量删页**——新页、季节页、小众页、导航页、支持/法务页、低量高价值页都可能是必要的;破坏性操作保留决策清单与回滚路径。程序化 SEO 七道闸门全过才放行:①重复用户任务真实存在(非关键词排列组合);②每个可收录页有超越变量替换的页级价值;③数据出处/许可/准确性/新鲜度/缺值行为已定义;④模板暴露可爬 URL、有用导航、正确状态/canonical、稳定渲染;⑤空/重复/不可能/低价值组合被预防或有意排除;⑥分阶段上线+holdout 抽查先于全量曝光;⑦监控覆盖收录/质量/参与/转化/爬取/政策风险。**程序化系统的强度在数据与交互的可辩护性,不在 URL 数量**。AI 辅助不是质量判词:人写与 AI 辅助同一 usefulness/原创性/事实审查/披露/维护责任标准;拒绝项——竞品摘要改写冒充专业、逐 fan-out 铺页、伪造经验/评论/作者/日期/引用、翻译页无本地审查、自动发布无抽样无回滚。

### 关键词方法的三条排序规则(keyword-content.md)

①聚类证据优先级:同市场/设备/日期的**排名 URL 重叠** > 共同意图与预期页型 > 语义相似——不为每个变体建页;②意图从实际 SERP 判读(信息/导航/商业/交易/本地五类映射到 guide/首页/对比/产品页/地点页),混合 SERP 可能需要多页型或刻意选择最佳拟合意图;③优先级输入显式标签:业务相关与转化价值、需求证据、差异化能力、现实竞争、内容/工程成本、现有页匹配与蚕食风险、依赖(产品/数据/法务/专家审查)——**量/难度缺失时定性排序,字段留 `unknown`,不编数**。国际内容**在目标市场重跑发现与意图分析**,翻译源语言词表不叫研究。

### 国际/电商的结构路由(international-commerce.md)

语言/地区版本用稳定可爬 URL(非 cookie/浏览器切换切换);hreflang 全集含自指+互指,x-default 仅在真有回退/选择器时加;本地化页通常 canonical 自指而非机械指向原文;不做强制 IP/语言重定向。分页/加载更多:每页稳定 URL+顺序 `<a href>`(爬虫不点交互控件),**内容不同不把分页页 canonical 到第一页**,过滤器组合防 URL 无限增生。变体是否独立 URL 由用户意图/可得性/内容/内链/运营定,变体选中态/URL/canonical/价格/库存/图/结构化数据保持一致。**五证据系统分离**:站点 HTML、Product 结构化数据、Merchant feed、自然搜索表现、免费列表/购物表面——feed 过审不证明自然收录,Product 标记不保证富结果,各系统间价格/库存/标识/URL 应一致。缺货/停产/换代决策:留 live+准确库存与替代 / 仅重定向到真等价替代 / 有持久价值留归档页 / 无替代 404 或 410——**不把停产品批量重定向到类目或首页**。

### 包契约与触发路由治理(validate_skill.py;技能工程层)

REQUIRED_FILES 硬契约(22 个必在文件,含 evals/trigger_cases.json、schemas、registry、scripts);**禁止嵌套 SKILL.md**(会破坏可发现性路由);frontmatter description 必须含 seo/audit/keyword/exclude 路由词(缺则警告);SKILL.md 内引用的 references/*.md 链接必须实际存在(悬空即 fail);触发评估三桶:`should_trigger` / `should_not_trigger` / **`near_neighbor`(近邻负例,专防误触发)**——本套件设计触发用例时照此三桶补齐。

## 24 个子代理的路由与 TOML 定义模式（codex-seo 深读 2026-10-09b）

来源:[AgriciDaniel/codex-seo](https://github.com/AgriciDaniel/codex-seo) `agents/*.toml`(24 个)+ `skills/seo/SKILL.md`(编排器)。它把路由拆成「自然语言触发(TOML agent)+ 能力探测加派(编排器)」两层,模式可移植。

**TOML 定义骨架。** 每个代理仅 4 字段:`name`、`description`(同时是触发文本,塞满关键词)、`nickname_candidates`(固定三件套:`seo-x` / `seo x` 带空格变体 / `x` 裸词)、`developer_instructions`(多行字符串即完整 system prompt)。description 写坏代理就路由不到——仓库里 `seo-ecommerce.toml` 的 description 是字面量 `">"`,是现成反例:路由文本与代理一体存放时,要有校验防字段损坏。

**指令模板的收敛结构。** 老代理(technical/content/schema/local/performance 等)遵循同一骨架:角色句 → 编号工作流步骤 → 领域参考表(CWV 阈值、E-E-A-T 权重 20/25/25/30、Local 六维权重 25/20/20/15/10/10)→ Cross-Skill Delegation 段 → Output Format 契约(0-100 分、表格、Critical>High>Medium>Low、必须标注数据来源如 "DataForSEO (live)" / "On-page analysis (static)")→ Error Handling 表。新代理(hreflang/images/programmatic/plan)改用紧凑的「Prioritization Logic」段直接定义四级严重度映射,省去重复输出格式——两种粒度按代理复杂度选。

**条件加派靠能力探测,不靠用户口供。** 编排器固定派 8 个常驻代理(technical/content/schema/sitemap/performance/visual/geo/sxo),其余按环境探测加派:`google_auth.py --check` 有凭据 → seo-google;首页检测到本地业务信号 → seo-local;再叠加 DataForSEO MCP 可用 → seo-maps;外链 API key → seo-backlinks;内容策略信号 → seo-cluster;电商信号 → seo-ecommerce;存在 drift 基线 → seo-drift。行业判定(SaaS/本地/电商/出版/代理)来自首页信号词,判定含糊时列前两名候选让用户确认,不硬猜。

**分层降级与配额纪律。** seo-google 分 Tier 0/1/2(API key → +service account → +GA4),每层列出可执行的具体命令;seo-maps 分 Tier 0/1(免费 Nominatim/Overpass vs DataForSEO),Tier 0 时把缺失的 geo-grid 维度权重 25% 重分配(+10 GBP/+10 评论/+5 跨平台),评分体系不因数据缺失而空转。付费调用前必须过 `dataforseo_costs.py check`(approved/needs_approval/blocked 三态,needs_approval 要上报编排器);image-gen 永不自动生成图片,只输出计划(成本控制)。

**防重复路由与代理间总线。** 每个代理写明「不做什么」:seo-maps 明确不重复 seo-local 的页面分析、不重复 seo-geo 的 AI 可见性,改推荐 `/seo local <url>` 交还给对应代理;seo-technical 把 hreflang 细查 defer 给子技能。代理间用 `.seo-cache/` 共享缓存传递上下文(site-meta.json 的 business_type 会影响 schema 分析结论、audit-scores.json、pages/{slug}/*.json),读取三态:找到则引用并注明日期 / 缺失或损坏则当不存在 / 用户说 refresh 则整体忽略——与上文 qiaomu 的闸门思路互补:一个管「放行」,一个管「复用与去重」。
