# SEO Suite Capability Map

## 总体结构(市场 × 能力 双维度)

```text
seo-suite
├── overview     总入口、分诊、优先级判断、市场维度主干(multilingual-workflow)
├── research     关键词、SERP、内容缺口、竞品(含各市场工具链)
├── content      SEO/GEO 内容、标题描述、内容质量(含区域 AI 平台、中文指南)
├── technical    技术 SEO、Schema、内链、架构、实体、Programmatic SEO(含区域爬虫/hreflang)
└── monitoring   排名、外链、报告、告警、权威度
```

**运行模型:每个任务 = 市场 × 能力。** 市场决定引擎格局、工具栈、语言规范与合规;能力决定方法论。市场差异知识不放在独立的区域文件里,而是作为各能力文件中带「市场差异」的小节存在;18 市场的索引与主干在 [multilingual-workflow.md](multilingual-workflow.md)。

## 能力映射

| 能力主题 | 集合 |
|---|---|
| 整体 SEO 诊断、SEO 方案、AI 搜索可见度的总体判断 | overview |
| 关键词研究、SERP 分析、内容缺口、竞品分析、竞品/替代方案页规划、内容策略 | research |
| SEO 内容写作、GEO 内容优化、标题与描述、内容质量（E-E-A-T）、内容刷新、竞品页文案 | content |
| 单页审计、技术 SEO 检查、结构化数据、内链、站点架构、实体优化、Programmatic SEO、Core Web Vitals / 性能、审计工具输出解读、SEO 归因埋点 | technical |
| 排名追踪、外链分析、效果报告、告警、域名权威度评估 | monitoring |

## 市场分层(策略侧重不同)

| 层 | 市场 | 策略侧重 |
|---|---|---|
| 独立学科(平行引擎生态) | 中文、俄语区、韩语区、日语区 | 换工具栈+换内容生态入口;GEO 的引用池与 Google 系完全不同 |
| ChatGPT 超强市场 | 葡语(巴西)、印地(印度) | Google 常规打法+LLM 可见性优先级全市场最高 |
| 方言/文字机制分裂 | 西语、阿拉伯、德语、印尼、越南、泰语、波兰、荷兰 | hreflang 结构+词表归组+文字方向/分词机制 |
| 合规驱动 | 法语(Bill 96)、俄语区(152-ФЗ/erid)、欧盟(GDPR)、日本(ステマ規制) | 合规先于内容 |
| 基线 | 英文 | 全球默认层,其他市场在此之上做差异 |

## 组合调用建议

| 场景 | 推荐组合 |
|---|---|
| 新专题上线前 | research + content |
| 规划 competitor / alternatives 页面集 | research + content + technical |
| 做 content pillars / cluster map | research + content |
| 页面不排名 | research + technical |
| 旧内容掉量 refresh | monitoring + content + technical |
| 排名下滑 | monitoring + research + technical |
| AI 引用弱 | content + technical + monitoring |
| 做整站 SEO 路线图 | overview + research + technical + monitoring |

---

# (rampstack 深读 2026-10-09b) rampstack 审计技能增量

来源：[rampstackco/claude-skills](https://github.com/rampstackco/claude-skills) 的 seo-\* 与 programmatic-seo 共 12 个 SKILL.md 深读（seo-traffic-diagnosis、seo-site-health-audit、seo-aeo-geo 已在先前批次吸收，不重复）。按本图五集合归位。

## research 增量

- **seo-keyword（4 阶段框架）**：发现（种子/竞品导出/GSC 第 1–2 页查询/PAA/客服语言/论坛，一轮 200–500 候选）→ 意图四分类（信息/导航/商业/交易；工具给量、SERP 定意图，混合意图取主导并记修饰词）→ 聚类（两法并用：SERP 前 10 重叠 ≥3 即同页 + 主题相关性；1 主词 + 5–15 副词共一页）→ 优先级（机会 + 战略契合 − 难度，前 20% 先做）。反模式：只追量、新站打头部词、忽视 GSC 已有排名词（最易的赢）、一词一页导致蚕食、忽视 SERP 特性挤占 CTR。
- **seo-keyword-gap-audit（四格差距矩阵）**：目标排 × 竞品排 → 共有领地（防守）/ 纯缺口（主攻）/ 独有领地（护城河，也要审其价值）/ 无人区（先验证意图再投）。机会分 = 量 20% + 业务相关 30% + 难度倒置 15% + 意图匹配 20% + 头部可达性 15%；80+ / 60–79 / 40–59 / <40 四个行动带。竞品集按 SERP 重叠选而非品牌知名度；KD 是启发式，SERP 被 Forbes/Wikipedia 占据时 KD 低得误导；多市场逐市场单独跑。
- **seo-competitor（5 角度）**：SERP 重叠 / 内容深度（看信息类型：数据表、原创研究、计算器，而非只看字数）/ 外链画像（他们的 linkable assets）/ 技术姿态（含 llms.txt 与 AI 就绪）/ 品牌与实体强度（品牌搜索量、知识图谱、提及）。选竞品：自家 Top10 优先词的 Top10 域名中出现最多的 3–5 个。Similarweb（相对规模/渠道）+ Ahrefs（外链/词重叠）+ Semrush（SERP 特性）三角互证，平台间不一致本身是信号。

## content 增量

- **seo-content-audit（5 动作决策树）**：keep / update / merge / redirect / delete（有意删除用 410，处理快于 404）。判据：90 天会话/自然点击/平均位置/展示/CTR/引域/停留/24 个月未更新/<300 词/零入链。决策树：有流量→近期衰减？→update : keep；无流量→有外链？→有合适目标页？→redirect :（重建）update；无外链→在蚕食另一页？→merge : delete。合并目标按信号强（老 URL、外链多、排名好）选而非内容多；删除前必查引域；蚕食先合并再更新；季节性页不按会话量批量删。
- **seo-content-gap-audit（4 类机会）**：缺主题（create）/ 覆盖过薄（deeper 或扩成簇）/ 过时（refresh 事实+例子+年份+截图，并重新分发求重爬）/ 衰减（先诊断：SERP 特性变化、竞品发布、意图迁移、内链稀释）。Ahrefs（词/主题缺口）+ Similarweb（页面级真实流量）+ Semrush（SERP 特性缺口）三源。反模式：只创建不更新（更新/合并常以更低成本跑起新建）、把发布日期当货币、季节性误判为衰减（同比不环比）、刷新不重新分发、路线图无工作量与流量预估（拿不到预算）。
- **seo-offpage（4 策略组合）**：赢得媒体（数据驱动的数字 PR/专家引语/播客）/ 自有可链资产（原创研究、工具、行业数据追踪器——复利）/ 伙伴关系（案例互链、联合营销）/ 引用与目录（GBP、Wikidata——实体合法性地基）。新站首年约 70/20/10/0（资产/引用/伙伴/赢得），成熟站可偏向赢得媒体。锚文本自然分布序：品牌 > 裸链 > 通用 > 部分匹配 > 精确匹配；每月约 5% 丢链率会复利，建找回流程；先让站值得被链再做外链。

## technical 增量

- **seo-onpage（8 维度打分）**：title（50–60 字符、主词前置、与 H1 不逐字相同）/ meta（150–160，当广告文案写、带软 CTA）/ 标题层级（唯一 H1、不跳级、可当目录导航）/ 正文（首段即答主意图、段落 3–5 行可扫、含相关实体）/ 内链（出入各 2–3 条、描述性锚文本、链规范 URL）/ 图片（alt、描述性文件名、WebP/AVIF、宽高属性防 CLS、懒加载）/ slug（小写连字符、<60 字符、无日期无参数）/ 页面 schema（类型对、必填全、可过富结果测试、不向爬虫撒谎）。推送反模式："加 5 次关键词"（密度不是信号）、给 noindex 页做优化、双页打同一查询（先走 content-audit 定 canonical）。
- **seo-technical（6 层栈）**：可爬取（robots 不挡 CSS/JS、无限空间）→ 可索引（canonical 自引用、无混合信号）→ 渲染（关键内容无 JS 可见、SPA 用 URL 检查验证、无 hydrate 丢内容）→ 架构（重要页 3 点击内、面包屑带 schema、无孤儿、重定向最多一跳）→ 结构化数据（JSON-LD 优先、Organization/BreadcrumbList、llms.txt）→ 页面体验与安全（HTTPS/HSTS、CWV、软 404）。下层坏则上层全坏。经典陷阱：过度 robots 屏蔽弄坏渲染；canonical 当指令用（内容真搬家用 301）；无重定向图的迁移是迁移后掉量第一大因。
- **programmatic-seo（12 条军规）**：先答"该不该做"——真底层数据（记录 10+ 字段，理想 20+）、长尾查询量真实存在、意图可被数据呈现、刷新节奏匹配查询波动、QC 有预算（1 万页 ≈ 0.5–1.0 FTE）；默认答案是不做，除非数据独特或一方专业让页面真有用。数据源即护城河（一方/授权/专家策划/合成；抓取+AI 改写不是）；schema 深度 15+ 字段起步、30+ 才有竞争力，计算字段（如每平方英尺均价）与跨记录字段（"最相似的 5 个"）驱动页面深度和兄弟链；模板首 200 词直答该页查询（AEO 引擎摘的就是它）；变量密度容纳稀疏/稠密记录；抽检每周期 50–200 页、分层抽样，>5% 失败即停生成先修模板/数据；hub-and-spoke + 每页 5–15 条兄弟链、锚文本按记录特征变化；sitemap 分段、薄页 noindex（不达标字段不给公开 URL）、X vs Y 与 Y vs X 规范化到一边；季度数据刷新 + 分批模板迁移（每批监控 30 天）；12–24 个月无流量页 noindex/410。AI 引擎对薄 pSEO 惩罚比传统搜索更快——pSEO 页走事实型查询车道（价格、统计、对比），不抢编辑内容的分析型查询。

## monitoring 增量

- **seo-rank-tracking（4 桶 + 阈值路由）**：品牌（10–30 词，任何变体掉出 #1 即警，即刻通知）/ 金钱（30–100 词，掉 5 位或出 Top10 即警，日摘要）/ 机会（11–30 名，50–200 词，进 Top10 为正向警、掉过 30 告警，季度重建此桶）/ 竞品基准（50–150 词，SOV 变动 10%+ 告警，月摘要）。全库 140–480 词、典型 200–500：太少失真、太多不可读；无分段 = 不可过滤的仪表盘。Day1 基线存位置 + SERP 构成 + CTR；附加标签（主题/漏斗阶段/页面映射/国家/设备/SERP 特性）前期打后期省。位置 ≠ 流量（#1 零点击不如 #5 稳定流量），叠 CTR 与点击数；汇报必须带上下文（"60 天从 11 到 4"）。高竞争领域放宽阈值防警报疲劳。
- **seo-backlink-audit（5 维画像）**：引域质量（DR 是相对指标，DR30 利基站可胜 DR80 综合站）/ 链接速度（尖峰 = 付费或负面 SEO，骤降 = 重定向错误或内容下线）/ 锚文本分布（品牌与裸链主导、精确匹配为极少数；品牌词≈关键词的利基站高精确匹配属正常，先查再动）/ 链接类型（编辑性 in-content dofollow 主导；关注 sponsored/UGC 标注与重定向链）/ 竞品差距（链 2+ 竞品但不链自己的域，差距应随时间收窄）。disavow 只在人工处罚或明确算法信号后用，例行化 disavow 反伤排名；丢链找回比新建便宜；Ahrefs 非地面真相，与 GSC 三角；活跃资产至少季度复审。

## overview 增量

- **seo-audit-orchestration（6 阶段编排）**：章程（1 页：范围/目标/干系人）→ 数据采集（Site Explorer/Site Audit/Keywords/Content Explorer/Rank Tracker + GSC/分析/日志，每笔记录新鲜度）→ 六个子审计（站点健康/外链/词缺口/内容缺口/单页/AI 搜索，各出 findings 文档）→ 主题化综合（200 条问题清单不是审计，短主题列表才是；每主题答：发生什么、为何重要、奖品多大、怎么修）→ 影响/努力矩阵（快赢做现在/战略项排资源/维护进 backlog/低影响高努力放弃）→ 交付（执行摘要 5 分钟可读 + 90 天路线图现场拿到承诺 + 排下次）。反模式：无目标审计产出 60 页没人读；跳过子审计到处都浅；各次审计结构漂移使趋势不可比；审计完无路线图 = 货架件。
- **数据可得性规则（全技能通用）**：任何技能在必需数据/工具不可得或不可验证时，合规产出 = 带声明缺口的交付（需要什么、实际拿到/验证了什么、哪些部分受影响）；编造、估算、内插必需数字永不合规。与运营层"诚实停止约定"同构，可移植进本 suite 全部审计模板的 done-when。

## 与本 suite 的对位

| rampstack 技能 | 本 suite 集合 |
|---|---|
| seo-keyword / seo-keyword-gap-audit / seo-competitor | research |
| seo-content-audit / seo-content-gap-audit / seo-offpage | content |
| seo-onpage / seo-technical / programmatic-seo | technical |
| seo-rank-tracking / seo-backlink-audit | monitoring |
| seo-audit-orchestration | overview |

---

# (open-seo 深读 2026-10-09b) coach 分诊 / 项目上下文 / 可观测性

来源：[every-app/open-seo](https://github.com/every-app/open-seo) `.agents/skills/seo-coach/SKILL.md`、`seo-project-setup/SKILL.md`、`observability-triage/SKILL.md`（Apache-2.0）。SEO 数据工作流部分已在前批吸收，此处只取 overview 集合相关的三个：交互分诊模式、跨会话共享上下文模型、数据管线自身的运维纪律。

## overview 增量

- **教练式分诊（seo-coach）**：教练回答与技能报告分两档——快速定向不花配额（读现状、平实解释、推荐一个下一步）；触发深度交接的信号 = 用户要报告/完整分析/"关于它的一切"/可分享交付物，或答案会超过一屏要点。回答规范：答案先行、要点优于段落、一条要点一个观点、数字首次出现带平实注释（"2,400/mo（每月搜它的人）"）、结尾**要么**一个问题**要么** 2–4 个编号选项，绝不两者都有。分诊五步：问清目标→盘点已有数据→**只选一个工作流**→解释会做什么→只要下一个必要输入。战略模式：先业务目标与定位再谈词、搜索对手≠业务对手、用 SERP 判意图不靠猜；本地市场用本地/Maps 证据，不靠全国性指标。
- **数据源分级（coach 工具课 = 本套件路由的取数优先级）**：SEO 数据 API=第三方估算（只作相对比较，花钱前查 30 天内研究日志）；**GSC=第一方实测**（免费，"什么已在排"与近排名机会首选起点）；网页搜索=市场语境与联系路径；页面抓取=正文/标题/作者/schema/联系链接（页面级断言的证据）；项目共享上下文=业务/目标/定位/写作偏好/对手/关键页/研究日志（免费，每个工作流先读；知识放这里不放本地文件）；本地文件=GSC CSV/爬虫/草稿；报告库=已完成交付物（**开新工作流前先查已有什么，不重买已付过的研究**）。

## 项目上下文模型（seo-project-setup，跨会话共享记忆）

- **分节存储**：business_overview（做什么/给谁/市场/站点阶段）、current_goal（指标+时限）、positioning（受众/痛点/差异化/要守住的主张）、writing_preferences（语气/禁用词/回避话题——内容工作流读它）+ 自定义节；补丁式写入：addCompetitors（域+一行"为何重要"）、addKeyPages（**精选 10–30 条短名单而非全站清点**，每条带角色 hub/spoke/money/other+主题）、研究日志追加（凡花配额必记）。**边访谈边分批写，不留到最后**；覆写=整节替换，已有内容并进新 prose 而非丢弃。
- **GSC 接入两级**：优先原生集成（agent 直接读，免维护文件）；退路 CSV 导出放 `gsc/`（查询+页面各取 3 个月与 16 个月两窗）。本地文件夹只建 gsc/drafts/reports 三件，不复制上下文内容到本地。
- **最小内联设置模式（open-seo 全部工作流通用，本套件同用）**：缺必需上下文时——从站点推断→一句话向用户确认→存→继续；**绝不前置完整访谈**，收尾才建议跑完整 setup；访谈后只推荐**一个**首个工作流；确认过的才写（推断以"约定答案"落盘，不是猜测）；GSC 未被工具返回确认就不断言已连接。

## monitoring 增量（observability-triage，面向数据管线/工具自身的运维面）

- **按结果计数，不按日志行数**：事件级过滤器（只取 worker-事件类）才让计数=调用数；分组结果不排序且约 10 行封顶，**缺组≠零**——要看错误面就显式加"结果≠ok"过滤，客户端自行排序。
- **扇出与碎片化**：一次隔离体死亡（OOM）同一瞬杀掉钉在其上的所有请求——先按时间戳聚类原始事件再读用户影响；带前缀的日志（时间戳开头）把一个错误拆成 N 个单行组，按消息分组会低估，取原始采样客户端合并。
- **修复了≠已部署**：先核对脚本版本/部署时间再下"修复无效"的结论（手动部署的环境里尤其如此）。
- **已知噪音清单纪律**：只有调查证明"无一方可修的发射点"（runtime 写的事件无应用调用点，按兄弟请求结果判定）才进清单；每条带识别标记（fingerprint）+ **唯一使它变回真信号的条件**；应用时不重新调查清单条目。
- **对 SEO 监控的映射**：告警/排名监控同理——按"结果"而非"日志"计数、单点故障先聚类再定影响、验证修复先确认已生效、长期维护一份带"重新激活条件"的已知噪音过滤表，防止每次巡检重查已定论的噪音。

## 意图→工作流路由表（seo-coach 目录，对位本套件集合）

| 用户意图 | open-seo 工作流 | 本套件集合 |
|---|---|---|
| 先建立项目上下文 | seo-project-setup | overview（intake-checklists） |
| 找该先做的一件事 | seo-audit | overview + technical |
| 为何 AI 推荐对手、如何被引用 | ai-visibility-audit / ai-prompt-research | content（GEO）+ monitoring |
| 从种子词找机会 | keyword-research | research |
| 把 GSC 查询聚成页面目标 | keyword-clustering | research |
| 选页前先看市场格局 | competitive-landscape | research |
| 深钻一个对手 | competitor-analysis | research |
| Google 商户档案与本地对手 | local-seo | research（本地） |
| 为可链资产找外链机会 | link-prospecting | monitoring（外链） |

---

# (ai-marketing-claude 深读 2026-10-09c) 技能编排 / 能力分域

来源：[zubair-trabzada/ai-marketing-claude](https://github.com/zubair-trabzada/ai-marketing-claude)（MIT）——1 个根路由技能 + 14 子技能 + 5 并行子代理 + 4 个 Python 脚本 + 6 模板。`/market audit` 的六维加权评分与锚定打分已在前批吸收，本条只取编排与分域；读完余下全部 13 个子技能与 5 个代理文件。

## 三层编排结构（根路由 → 审计编排器 → 专家子代理）

- **根路由（market/SKILL.md）**：单一 `/market <cmd>` 命令表路由 15 个命令；显式成本分档——旗舰 `audit` 才扇出 5 个并行子代理，`quick` 明写"Do NOT launch subagents"（单次 WebFetch + <30 行记分卡），其余命令一对一转给 `skills/market-<cmd>/SKILL.md`。路由前置**业务六型探测**（SaaS/电商/代理/本地/创作者/市场平台），每型一段"关注什么"，重塑所有下游分析焦点。
- **审计编排器（market-audit）的"集中预取再扇出"**：Phase 1 先由编排器抓首页+至多 5 个内页、分类业务型、建 page map；Phase 2 五个子代理**共享**这份预取内容+业务型+页面图（避免 5 个代理重复抓取、重复推断业务类型）；Phase 3 按固定格式聚合加权。子代理不各自取数是扇出编排的关键纪律。
- **子代理模板五件套**（agents/*.md 统一结构）：角色一句话→在审计中的位置→分步过程→**固定输出格式**（维度分表+Wins/Fixes/Missing+前后对照）→尾部 Important Rules（必须实际抓取不猜、引用原文、修复必须带具体替代文案、诚实打分、收入影响优先）。固定输出 schema 让聚合器无需解析变体；"每条修复带可粘贴的 before/after"与"数字锚定的维度分档"同为本套件审计模板可直抄的两条。

## 文件产物总线（跨技能集成的唯一机制）

- **固定大写文件名即接口**：每技能产出一个规范文件（MARKETING-AUDIT.md、SEO-AUDIT.md、LANDING-CRO.md、BRAND-VOICE.md、COMPETITOR-REPORT.md、FUNNEL-ANALYSIS.md、COPY-SUGGESTIONS.md、EMAIL-SEQUENCES.md、SOCIAL-CALENDAR.md、AD-CAMPAIGNS.md、LAUNCH-PLAYBOOK.md、CLIENT-PROPOSAL.md、MARKETING-REPORT.md），文件头固定 URL+日期+总分。
- **"If X.md exists, consume"优雅降级**：每个技能尾部有 Cross-Skill Integration 节，显式列出消费哪些上游文件；文件不存在则自行取数或询问，不阻断。生成型技能同样消费（copy←brand 声音档案；emails←funnel 阶段映射；ads←competitor 角度+social 日历；proposal←audit 发现）。与 open-seo 的共享上下文模型对照：这里知识以**交付物文件**为载体而非项目上下文——两种总线可并用（上下文存偏好、文件存发现）。
- **文档化推荐管线**：report-pdf 明写装配顺序 audit→competitors→seo→landing→report-pdf；proposal 的关键原则："数据支撑的提案成交率高 2–3 倍"——诊断产物的终点是被销售侧技能复用为证据。

## 能力分域三分（诊断 → 生成 → 编译交付）

- **诊断域**：audit（编排汇总）、seo（11 步）、landing（7 节 CRO+表单/移动/速度）、funnel（逐页 5 维+RPV 量化）、competitors（5 阶段+SWOT+偷师清单）、brand（4 维声音光谱+原型）。
- **生成域**：copy（5 维评分+PAS/AIDA/BAB/4U 公式+swipe file）、emails（7 类序列+发送节奏表+合规节）、social（5 支柱 40/20/15/15/10 配比+1→10 复用框架）、ads（多平台字符规格+三段再营销 40/35/25 预算+落地页信息匹配分）、launch（8 周逐日编排）。
- **编译交付域**：report（把所有上游文件汇编成另一套六类记分卡）、report-pdf（JSON schema 契约）、proposal（10 节提案+三层定价锚定+ROI 框架）。共同点：不产生新分析，只重组+补计算+换受众语言。
- **"检测→分支"表驱动模式贯穿全库**：业务六型、页面八型、漏斗八型、邮件序列七型、launch 七型、社交平台六选——每个技能先查表定型再套该型的专属打分权重/文案结构/基准值。上下文一次检测全程复用，与本套件"市场×能力"同构。

## 脚本与技能的分工

- **脚本找数据、技能做解释**（market-seo 原则原文："The script finds the data; the skill interprets what it means"）：analyze_page.py 抽 title/meta/标题层级/链接/图片/表单/schema/埋点等事实 JSON 作底，人工层再解读；脚本不可用时退路 = WebFetch 手动收集同等字段（能力不依赖脚本存在）。
- **report-pdf = JSON 契约渲染**：LLM 只负责按字段级装配指南填 JSON（含每个字段写什么、严重度写法、好坏示例），reportlab 确定性渲染成品牌 PDF；可选字段（competitors）缺省即跳节。这是"LLM 组数据、程序管排版"的干净分界，可移植到本套件任何报告产出。

## overview 增量（可移植点）

- **扇出编排三纪律**：集中预取+共享上下文传给每个子代理；子代理输出 schema 固定；编排器只做聚合加权不做新分析。多集合套件做综合审计时照此组织（research/content/technical/monitoring 并行出 findings，overview 只主题化+排优先级——与 rampstack 六阶段编排互补）。
- **双速命令**：重扇出命令与"不启动子代理"的快速档并存，路由层明写分档条件。
- **输出标准五条（根层对所有子技能强制）**：可执行优于理论、一律 H/M/L 排序、每条建议挂收入影响、示例驱动（before/after 而非建议）、客户可直接使用。

## 与本 suite 的对位

| ai-marketing-claude | 本 suite 集合 |
|---|---|
| market 根路由 + audit 编排 + proposal/report 编译 | overview |
| market-competitors | research |
| market-seo / market-landing | technical（单页审计） |
| market-copy / market-brand / market-emails / market-social / market-ads / market-launch | content（文案与内容生产） |
| market-funnel（转化路径+RPV） | monitoring（转化/归因面）+ overview |
| market-report / market-report-pdf（汇编+PDF 契约渲染） | monitoring（报告） |
