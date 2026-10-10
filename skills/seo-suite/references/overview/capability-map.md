# SEO Suite Capability Map

能力地图:一页看清本套件有什么、按什么路由。深读吸收笔记(四段)与 v0.34.0 新子系统的设计依据速查表移至 [capability-appendix.md](capability-appendix.md),不占本文件。

## 总体结构(市场 × 能力 双维度)

```text
seo-suite
├── overview     总入口、分诊、优先级判断、健康分与修复闭环的编排层、商业提案、市场维度主干(multilingual-workflow)
├── research     关键词、SERP、内容缺口、竞品(含各市场工具链)
├── content      SEO/GEO 内容、标题描述、内容评分体系、品牌事实页(含区域 AI 平台、中文指南)
├── technical    技术 SEO、Schema、内链、架构、实体、Programmatic SEO(含区域爬虫/hreflang、修复物生成、CI 质量门)
└── monitoring   排名、外链、报告、告警、权威度、GEO 可见性闭环的测量面
```

**运行模型:每个任务 = 市场 × 能力。** 市场决定引擎格局、工具栈、语言规范与合规;能力决定方法论。市场差异知识不放在独立的区域文件里,而是作为各能力文件中带「市场差异」的小节存在;18 市场的索引与主干在 [multilingual-workflow.md](multilingual-workflow.md),每语区门户在 `references/markets/<代码>.md`。

## 能力映射

| 能力主题 | 集合 |
|---|---|
| 整体 SEO 诊断、SEO 方案、AI 搜索可见度的总体判断、审计编排与优先级、SEO 商业提案 | overview |
| 关键词研究、SERP 分析、内容缺口、竞品分析、竞品/替代方案页规划、内容策略、域名策略、目录提交 | research |
| SEO 内容写作、GEO 内容优化、标题与描述、内容质量（E-E-A-T）、内容评分与发布闸、内容刷新、竞品页文案、可引用性打分、品牌事实页与 AI 回答核查 | content |
| 单页审计、技术 SEO 检查、结构化数据、内链、站点架构、实体优化、Programmatic SEO、Core Web Vitals / 性能、审计工具输出解读、修复物生成、SEO 归因埋点 | technical |
| 排名追踪、外链分析、效果报告、告警、域名权威度评估、惩罚恢复、本地网格排名、引用面板与衰减、SERP 波动、页面变更审计 | monitoring |

## 可执行层(52 个 stdlib 脚本 + markets.json 数据层)

脚本清单以 SKILL.md 第 3 节为唯一事实来源;★ = v0.34.0 新增(38→52)。**对应任务先跑脚本拿事实,再按能力文件解读。**

| 脚本组 | 脚本 |
|---|---|
| 审计与页面质量(17) | site_audit / ★health_score / ★traffic_funnel / quality_rater / above_fold / trust_signals / core_eeat / ★content_score / ★fix_plan / ★grounding_page / ★audit_compare / ★ci_format / ★sensor_volatility / ★forecast / ★prioritize / ★changelog / ★doctor |
| 技术 SEO(7) | sitemap_audit / hreflang_cluster / redirect_chain / robots_posture(27 bot 两级评分) / llmstxt / schema_lint / head_check |
| 关键词与 SERP(7) | gsc_mining / serp_overlap / keyword_variants / payment_intent / geo_difficulty / serp_occupancy / grid_rank |
| 多语言实装(4) | market_lint / local_format / text_metrics / text_units(markets.json 18 市场数据层共读) |
| AI/GEO 测量(6) | citation_panel(decay/signals) / fanout_analysis / ai_referral_log(bot 四桶) / ★citation_gaps / ★oracle_check / cite_domain |
| 归因与管道(6) | did_attribution / seo_vs_ads / yt_outlier / trend_scout / freshness / report_build |
| 持续监控守护(2) | monitor(页面级 noindex/canonical/segments/CI 门) / notify(分级+按类型路由) |
| 套件自维护(3) | self_check / link_check / intel_check |

**新脚本归属**(v0.34.0,14 个):

| ★新脚本 | 主归属 | 所属子系统 |
|---|---|---|
| health_score / traffic_funnel / prioritize | technical(+overview 编排) | 健康分体系 |
| fix_plan | technical(+content 修复物) | 修复闭环 |
| audit_compare / ci_format | technical(+monitoring CI 面) | CI 门体系 |
| content_score | content | 内容评分体系 |
| grounding_page / oracle_check | content(GEO) | GEO 可见性闭环·品牌事实面 |
| citation_gaps | content(GEO)+ monitoring | GEO 可见性闭环·外联面 |
| sensor_volatility / changelog | monitoring | 监控增强 |
| forecast | overview(+monitoring 报告面) | 商业提案 |
| doctor | overview(环境自检) | 全链路前置 |

## 六个子系统能力(跨脚本闭环,v0.34.0 起)

1. **健康分体系(审计→分→漏斗→优先级)**:site_audit(原始 findings + AI Search Health 独立子分)→ health_score(Ahrefs 主分仅 CRITICAL 扣分/Lumar 六大类树缺源 N/A/Ryte impact 两栏排序)→ traffic_funnel(available⊃indexable⊃uniqueness⊃in_serps⊃with_clicks⊃good_ux 六阶段流失)→ prioritize(18 条声明式条件规则+segment 切换重算)。输入输出均为审计器 JSON 信封,外部爬虫导出经 audit-tool-output 字段映射后同链复用。
2. **修复闭环(audit→fix_plan)**:site_audit 或任意 audit JSON → fix_plan 生成 6 类 FixItem(robots/llms/schema/meta/ai_discovery/content);默认 dry-run,`--apply` 只写 `./seo-fixes/` 隔离目录,`--estimate` 出收益预估;人审部署后由 audit_compare 验证收敛。
3. **CI 门体系(compare→ci_format→action)**:site_audit 两次 → audit_compare `--baseline-gate`(新增/已修复/delta 三清单回归门)→ ci_format(SARIF/JUnit/github 注解三格式)→ 仓库根 action.yml 的 PR 门禁;定时侧 monitor `diff --ci` 同构输出。手册见 [ci-gates.md](../monitoring/ci-gates.md)。
4. **内容评分体系(草稿→竞品校准→发布闸)**:content_score(MarketMuse 话题公式+Surfer 双轨+意图系数,竞品<3 拒评并出术语表)配 content-brief 三段式模板;发布闸 above_fold(首屏 5 秒测试)/quality_rater(六维)/core_eeat(veto 封顶)挂进 pre-publish-checklist 27 条。
5. **GEO 可见性闭环(panel→decay→gaps→outreach)**:citation_panel init/record 采样(prompt-bank 供 prompts 对象)→ report/diff(SoV/win_rate/signals 阈值 |Δ|≥5pp 且 n≥10)→ decay(7 点平滑/4 道闸门/半衰期/重写队列)→ citation_gaps(竞品被引而己方未被引的 URL+外联简报)→ citation-outreach-brief 模板 → cite_domain 对目标域评级。旁路三件:ai_referral_log(AI 引荐流量下界+bot 四桶)、oracle_check(AI 回答 vs 品牌事实)、grounding_page(实体事实页生成/校验)。
6. **商业提案(forecast)**:gsc_mining 出词表 → forecast 六步(CTR 曲线→校准系数持久化→三 scenario→orders/value)→ forecast-report 模板(省钱+赚钱双结构,管理层五级漏斗)。

## 模板层(22 个;★ = v0.34.0 新增,14→22)

| 目录 | 模板 |
|---|---|
| templates/audit(5) | full-seo-audit / on-page-audit / technical-audit / entity-audit / ★report-modes(exec/dev/prospect 一表三裁) |
| templates/research(7) | keyword-research-output / serp-analysis-output / content-gap-output / competitor-analysis-output / competitor-pages-plan / content-strategy-plan / ★prompt-bank(采样 prompt 库) |
| templates/content(2) | ★content-brief(三段式简报) / ★pre-publish-checklist(27 条发布闸) |
| templates/monitor(8) | rank-report / backlink-report / performance-report / alert-playbook / ★ai-visibility-weekly / ★ai-visibility-monthly / ★citation-outreach-brief / ★forecast-report |

## 数据层(markets.json)

18 市场规则数据层(chars/fullwidth/grapheme 单位阈值、营销词表、格式规范),多语言脚本共读;`--market` 接线的脚本(site_audit/market_lint/head_check 等)按市场换阈值,多区域站点逐市场分开评分、不合并总分。市场清单与锚点见 [multilingual-workflow.md](multilingual-workflow.md)。

## 市场分层(策略侧重不同)

| 层 | 市场 | 策略侧重 |
|---|---|---|
| 独立学科(平行引擎生态) | 中文、俄语区、韩语区、日语区 | 换工具栈+换内容生态入口;GEO 的引用池与 Google 系完全不同 |
| ChatGPT 超强市场 | 葡语(巴西)、印地(印度) | Google 常规打法+LLM 可见性优先级全市场最高 |
| 方言/文字机制分裂 | 西语、阿拉伯、德语、印尼、越南、泰语、波兰、荷兰 | hreflang 结构+词表归组+文字方向/分词机制 |
| 合规驱动 | 法语(Bill 96)、俄语区(152-ФЗ/erid)、欧盟(GDPR)、日本(ステマ規制) | 合规先于内容 |
| 基线 | 英文 | 全球默认层,其他市场在此之上做差异 |

## 任务类型→脚本链(10 条典型链)

| # | 任务类型 | 能力组合 | 脚本链 |
|---|---|---|---|
| 1 | 整站审计与健康分路线图 | overview + technical | site_audit(--market)→ health_score → traffic_funnel → prioritize → fix_plan(修复物)→ full-seo-audit 模板交付 |
| 2 | 单页体检与修复闭环 | technical | site_audit → fix_plan(dry-run 人审 → --apply)→ 人工部署 → audit_compare 复验 |
| 3 | PR/CI 质量门 | technical | site_audit → audit_compare --baseline-gate → ci_format(sarif/junit/github)→ action.yml;定时侧 monitor diff --ci |
| 4 | 关键词研究 | research | gsc_mining → keyword_variants → serp_overlap 聚类 → payment_intent / geo_difficulty → keyword-research-output 模板 |
| 5 | 写一篇能排也能被引的页 | content(+research) | content_score(竞品校准+术语表)→ content-brief 模板起草 → above_fold / quality_rater / core_eeat → pre-publish-checklist(多市场叠 market_lint/local_format) |
| 6 | GEO 可见性测量与外联 | content(GEO)+ monitoring | prompt-bank → citation_panel init/record → report/diff → decay(重写队列)→ citation_gaps → citation-outreach-brief → cite_domain |
| 7 | 品牌在 AI 回答里说不说得对 | content(GEO) | brand-records 事实档案 → grounding_page(--check/--facts)→ oracle_check(Inaccuracy% 按引擎) |
| 8 | AI 流量归因与四桶画像 | monitoring(+technical) | ai_referral_log(access.log+--bot-ua)→ 归因正则/自报问卷 → seo_vs_ads / did_attribution 量化 |
| 9 | 排名/流量下滑根因 | monitoring + research + technical | monitor diff → sensor_volatility(z30 判疑似算法更新)→ changelog(下跌日页面变更)→ gsc_mining --decay → 定位到 content/technical |
| 10 | SEO 商业提案/预算答辩 | overview + monitoring | gsc_mining(词表)→ forecast 六步三 scenario → forecast-report 模板 |

分诊细则见 [routing-rules.md](routing-rules.md);开局先认站型见 [site-type-playbooks.md](site-type-playbooks.md);持续守护(monitor/notify 部署形态)见 [continuous-operations.md](../monitoring/continuous-operations.md)。

## 深读笔记

方法论级吸收笔记(rampstack 编排/open-seo 分诊与上下文/ai-marketing-claude 扇出/Awesome-LLMOps 检索版图)与 v0.34.0 新子系统设计依据速查表在 [capability-appendix.md](capability-appendix.md)——需要对应能力的操作细节或口径来源时再读。
