# 管线完备性地图与缺口登记簿(pipeline-completeness)

> 建立 2026-10-11,来自 10 视角并行审计(策略适配/管线断链/pSEO/内容生命周期/内链架构/国际化/外链 PR/监控完备性/数据集成层/管线形态对标)。**愿景基准**:拿到一个网站 → 诊断它适合哪些策略 → 每条策略有一条完整落地管线(数据→计划→执行→验证)→ 每条有长期监控。断言半衰期:状态列每月 intel-update 复盘搭车核对。
>
> **2026-10-12 收口**:R0-R4 各节头部已加状态行(✅=完成并指向实现物与 commit);R5 37 bug 修复波次与 R6 入库进度见第五节各组标注;50-agent 战役一句话总结见第五节末「战役总结」。

## 一、总判定

分析零件 59 个、知识文档 119 篇都是第一梯队;缺的是**管线感**的四个根因:
1. **无 project 实体与编排器**——链只存在于 SKILL.md 原则 0 的散文里;状态散落 6 处(.seo-monitor/、panel.json、remediations.json、.trend-state.json、.intel-state.json、seo-fixes/),agent 每次会话要重读 400 行自行拼链
2. **无诊断型路由**——现在的路由是"用户要什么给什么";缺"体检×站型×资源→推荐策略组合"的 strategy-fit 层;8 张站型卡无识别信号(靠用户自报)、几乎不含命令链
3. **数据线未打通**——GSC 同一份数据 4 种形态手工喂 6 个脚本;site_crawl 产的 edges 内链图零下游消费者;envelope 采用率 14/30;云/本地 sqlite 双份无同步
4. **"设计了没接线"与执行末端断裂**——sensor_volatility --context/field_data CWV/citation decay/cwv_* 路由全是设计了没接;outreach 简报生成后零跟踪;发布后验证只活在文字里

## 二、逐管线阶段图(✓工具+衔接 / △有零件无衔接 / ✗断)

| 管线 | 数据 | 计划 | 执行 | 验证 | 长期监控 |
|---|---|---|---|---|---|
| 技术审计(crawl→audit→score→prioritize→envelope→remediation) | ✓ | ✓ | △ | ✓ | ✓(verify 无人排期) |
| 热点内容(trend→gate→brief→写作→闸→发布) | △ | ✓ | ✗发布靠人(边界内) | ✗发布后 W+2 复测无实装 | △trend 无 cron |
| GEO 可见性(panel→采样→report→decay→gaps→outreach) | △人肉采样 | ✓ | ✗outreach 零跟踪 | ✓ | ✗decay 队列无消费者 |
| 信源自更新(intel→protocol→改文档→commit) | ✓ | ✓ | △ | ✓ | ✓(issue 无超时) |
| 监控(monitor→notify→remediation) | ✓ | ✓ | △ | ✓ | ✓(周检 bug 已修) |
| pSEO(模式→数据→架构→模板→生成→索引→cohort→退役) | △ | ✗ | ✗ | ✗ | ✗(九阶段零专用工具) |
| 内容生命周期(选题→brief→写作→闸→发布→刷新→退役) | △ | △无 calendar | △ | △无首月 cohort | △刷新无排期 |
| 内链架构(图分析→孤儿修复→facet 决策→持续) | △edges 无消费者 | ✗ | ✗ | ✗ | ✗ |
| 国际化(市场决策→架构→transcreate→上线→多市场监控) | △ | ✗市场进入纯知识 | △ | ✓hreflang_cluster | ✗无批量编排 |
| 外链/数字 PR(数据→健康→资产→外展→目录→PR) | ✗零解析器 | △ | △ | ✗ | ✗零监测 |

## 三、缺口登记簿(合并去重,按建设路线分组)

### R0 修复与接线(小改,立刻做)

> **状态:✅ 完成(2026-10-12)** — R0-1 于 241b531;R0-2 sensor 上下文/R0-3 CWV 周检/R0-4 decay 告警于 acd7100(tests/test_r0_wiring.py 守护);R0-5 verify 排期/R0-6 trend 3h cron/R0-9 issue 超时/R0-10 freshness CI 于 c9ba773;R0-7 新脚本状态文件一律落 cwd 工作区(trend_watch 保留 --state 可指);R0-8 未按原规格接线——critical 告警仍走 notify 路由,工单化由 project.py run/编排层承担(残项)。

| # | 缺口 | 规格 |
|---|---|---|
| R0-1 | ~~周检从未自动执行~~ | ✅已修(2026-10-11:schedule 事件按 cron 显式判 weekly,241b531) |
| R0-2 | ~~sensor_volatility --context 未接线~~ | ✅已修(acd7100:monitor gsc/visibility 告警前调用,high_volatility 附注) |
| R0-3 | ~~field_data CWV 未进监控~~ | ✅已修(acd7100:周检采 p75,跨档告警 cwv_*) |
| R0-4 | ~~citation decay 不进告警链~~ | ✅已修(acd7100:citation_decay warn 注入) |
| R0-5 | ~~remediation verify 无人排期~~ | ✅已修(c9ba773:workflows verify 排期) |
| R0-6 | ~~trend_watch 无 cron/workflow~~ | ✅已修(c9ba773:3h cron,退出码 1 接 notify) |
| R0-7 | ~~trend-state 写进 skill 安装目录~~ | ✅已修(新脚本状态一律 cwd;--state 可指工作区) |
| R0-8 | ~~monitor 告警不进工单~~ | ⚠️未按原规格接线(critical 走 notify 路由,工单化由 project 编排层承担) |
| R0-9 | ~~intel issue 无超时升级~~ | ✅已修(c9ba773:>72h 未关→notify) |
| R0-10 | ~~freshness 无 CI 守护~~ | ✅已修(c9ba773:capability-drift job 顺带 --fail-stale) |

### R1 管线骨架(把散珠串成链——最高结构性优先)

> **状态:✅ 完成(2026-10-12)** — R1-1/R1-2 project.py 编排器+`<slug>.seo/` 工作区、R1-3 strategy-fit、R1-4 站型识别、R1-5 intake 4 问、R1-7 run triage 30 分钟首答、R1-8 content_queue、R1-10 fix_plan --git-branch 均于 c9ba773(tests/test_project.py 等守护);R1-6 十卡开局命令链于 a605630(48 条逐条核对);R1-9 部分——refresh 排期未单独成器,由 content_queue 状态机+content_inventory update 桶+references/content/content-refresh-playbook.md 承载。

| # | 缺口 | 规格 |
|---|---|---|
| R1-1 | **project.py 编排器** | init/run/next/status:project.yaml(站点+市场+站型)为实体,next 按五阶段状态机输出下一条精确命令链 |
| R1-2 | **project 工作区归一** | `<slug>.seo/` 收敛 6 处状态;history/ 按日期存快照(对标 niubigeo Baseline 冻结语义) |
| R1-3 | **strategy-fit 决策层** | envelope×站型卡×intake 资源字段→Top3 策略组合(依据信号/收益区间/优先级/反指标) |
| R1-4 | 站型识别信号 | 8 卡各加识别信号(URL 型谱/schema/页面构成),site_crawl 输出→站型判别,模糊列前二确认 |
| R1-5 | intake 补 4 问 | 资源投入/风险容忍/时间窗/业务量化目标 |
| R1-6 | 8 张站型卡各补开局命令链 | 卡=recipe;examples 加站型标签 |
| R1-7 | 30 分钟首答 | project.py run triage:一条命令到"站型+该做三件事+理由+验证方式" |
| R1-8 | content_queue.py 选题合并队列 | trend backlog+gsc striking-distance+serp_overlap 缺口→周排期,复用 remediation 状态机 |
| R1-9 | refresh 排期器 | decay 双源(citation_panel/gsc_mining)→refresh 工单,content_score 复测核销 |
| R1-10 | 发布执行通道 | fix_plan --git-branch 模式:落分支+开 draft PR(CMS 走导出) |

### R2 数据接入与打通

> **状态:✅ 完成(2026-10-12)** — R2-1 gsc_api.py 纯 stdlib RSA 于 acd7100(313e0f1 修正矩阵枚举);R2-3 backlink_import/R2-5 indexnow+bing_wmt/R2-6 byo_import/R2-7 parity_check/R2-9 doctor --keys 于 fd464f0;R2-2 由 gsc_api 规范化 CSV 契约承载(一次拉取直喂 gsc_mining/traffic_funnel/monitor/sensor_volatility/did_attribution);R2-4 引荐域月检与 R2-8 schema_version×4 同波落地(fd464f0)。

| # | 缺口 | 规格 |
|---|---|---|
| R2-1 | **GSC API 客户端**(文档已承诺) | OAuth 读 gsc.json,RS256 JWT 纯 stdlib(手写 RSA 签名),一次拉取供 6 脚本复用 |
| R2-2 | **GSC 数据落地层** | data/ 规范区消灭 4 形态重复导出;monitor 的 gsc.csv 自动化 |
| R2-3 | backlink_import.py | Ahrefs/Semrush/GSC Links 三格式 CSV→统一 schema 喂 cite_domain |
| R2-4 | 引荐域变化监控 | monitor 月检吃外链导出,接四级告警(6.5x 杠杆零监测是最大反差) |
| R2-5 | Bing 两快赢 | indexnow.py 提交器(零 key)+Bing WMT API(免费) |
| R2-6 | BYO 解析器 pack | Screaming Frog 导出/SERP top10 分号 CSV/kws.csv 归一入口 |
| R2-7 | 双语 parity_check.py | 源/目标页对照:长度平价带(markets.json)/结构对照/JSON-LD 一致 |
| R2-8 | envelope 推广 | gsc_mining/traffic_funnel/monitor diff/citation_gaps 补 schema_version 与封套 |
| R2-9 | keys manifest | doctor 扩展 env 模板生成+校验 |

### R3 生产线(pSEO/内链/多市场)

> **状态:✅ 完成(2026-10-12,R3-7 残)** — R3-1 pseo_pattern_mining/R3-2 pseo_batch_gate/R3-3 pseo_cohort/R3-4 link_graph/R3-5 site_crawl 锚采集/R3-6 orphan_fix/R3-8 market_fit/R3-9 market_batch/R3-10 prune_gate(+content_inventory 四轴治理)于 ec4422c;R3-7 内链监控第 5 问未接 monitor 周检——现由 link_graph --crawl 编排重跑对照承载(残项)。

| # | 缺口 | 规格 |
|---|---|---|
| R3-1 | pseo_pattern_mining.py | GSC queries→模式聚类(vs/alternative/for…)→addressable 量+30/25/20/15/10 打分 |
| R3-2 | pseo_batch_gate.py | 批次 record→key 唯一/必填/爆炸预警/Simhash 唯一度/样板比→PASS/WARNING/STOP |
| R3-3 | pseo_cohort.py | cohort 索引率周喂+预注册判读+90 天零展示→301/noindex/410 工单 |
| R3-4 | link_graph.py | crawl.json edges→PageRank 排序/深度直方图/孤儿清单(deeprank 可移植) |
| R3-5 | 锚文本采集 | site_crawl parser 收 anchor 文本,edges 升级 {src,dst,anchor} |
| R3-6 | orphan_fix.py | 孤儿×同目录候选源页→"源→孤儿→建议锚文本"清单 |
| R3-7 | 内链监控第 5 问 | monitor 周检 diff 两次 crawl 的 edges/orphans |
| R3-8 | market_fit.py | GSC 国别流量×markets.json→市场组合优先级矩阵 |
| R3-9 | 多市场批量编排 | 一份声明→批量跑 monitor/serp_occupancy/market_lint→跨市场周报 |
| R3-10 | prune_gate.py | 零点击页×入链×外链三查→prune/merge/redirect 三判(外链>0 或有排名词 NO-GO) |

### R4 执行末端与体验

> **状态:部分完成(2026-10-12)** — R4-1 outreach_tracker/R4-2 directory_tracker 于 e8750d1;R4-6 多站 rollup 由 benchmark_report(--monitor-db 可重复传,一站一库)承载;R4-10 合同表重生成完成(2026-10-12,data-source-contract.md 已对齐 85);R4-3 PR 钩子判定/R4-4 linkable_assets.py/R4-5 通用 newpage 周检(pSEO 新页由 pseo_cohort 承载)/R4-7 收录覆盖周检/R4-8 algorithm-updates 数据文件(规格在 seo-drift-monitoring.md §五)/R4-9 disavow_check.py 未实装,留规格待后续波次。

| # | 缺口 | 规格 |
|---|---|---|
| R4-1 | outreach_tracker.py | 域级状态机+复查日接 notify |
| R4-2 | directory_tracker.py | 提交 CSV+dofollow 核验+季度复检 |
| R4-3 | PR 钩子判定 | trend GO 信号→数据/时效/反共识钩→press 骨架 |
| R4-4 | linkable_assets.py | gaps 高被引形态反推资产类型→选题卡 |
| R4-5 | 新页首月 cohort | monitor newpage 周检(7/14/30 天收录+表现) |
| R4-6 | 多站 rollup | report 跨 .seo-monitor-* 聚合 digest |
| R4-7 | 收录覆盖周检 | sitemap 抽样 URL 的 indexed/excluded 状态 |
| R4-8 | algorithm-updates 数据文件 | drift 文档 §五规格落地+告警联动 |
| R4-9 | disavow_check.py | 锚文本分布/集中度→disavow 草稿(默认 0 条) |
| R4-10 | ~~合同表重生成~~ | ✅已修(2026-10-12:data-source-contract.md 重生成——修 trend_watch/benchmark 行粘连+补 29 新脚本行+计数 85) |

## 五、20 视角深扫补录(2026-10-11 第二轮:内部错漏 + 知识边界)

### R5 错漏修复(P0 级,先于一切新功能)

> **状态:✅ 完成(2026-10-12)——37 个代码 bug 全修,五波落地:53bfb89(W1)→39db653(W2)→4a00867+90c9469(W2b)→c9ba773(W3);高危三件(假 Wilson/robots 假 CRITICAL/冷却失效)均有钉死测试。**

**代码 bug(37 个,均经复现验证)**
- 审计链 13:health_score 全拒审除零崩溃;site_audit robots RFC 9309 违背(专属组空时误回落通配组→假 CRITICAL);audit_compare 已修复清单污染(拒审≠修复);GBK 全量乱码;Last-Modified 时区混 8h;X-Robots-Tag 大小写漏检 ——✅ 53bfb89(R5-W1)
- GEO 家族 14:wilson_ci 实为 Wald 区间(k=0/n 时宽 0→误判 stable);oracle 指纹碰撞丢 findings+币种不分币($99=99元)+中文否定误判;grounding sameAs 子串误配;JSON 全族非原子写;trend 标题从首个" - "截断;跨源 velocity 不可比 ——✅ 39db653(Wilson/原子写/monitor 链)+4a00867 与 90c9469(oracle 币种词表/指纹采样序号)+c9ba773(grounding/trend 5 bug)
- 监控链 10:cooldown 只比最旧行(超一个冷却窗后冷却失效);weekly diff 的 prev 取到 daily 快照;单次抓取失败→全字段假漂移;抑制树把 inhibited 记自愈;remediation 无锁;critical 发送失败永久丢 ——✅ 39db653(冷却判龄/prev 同kind/漂移门/抑制不自愈/critical 暂存重发/remediation 原子写+锁)+241b531(周检恒空)
- 多语言 6:oracle 对 ko/ru/ar/th/hi 静默 0 findings;Simhash CJK 单 token;泰文句切假阳;market_lint 缺全角!? ——✅ c9ba773(分词断层 6 处 ko/ja/th)
- 安全 4:12 脚本零 SSRF(llmstxt/robots_posture/schema_lint/ai_views/core_eeat 等连 file:// 可读);hreflang_cluster 抓敌意 sitemap 任意 loc;core_eeat read 无上限;ai_views javascript: 链接(XSS 载体);workflow 模板注入面 ——✅ 53bfb89(SSRF 铲平 5 脚本:file:// 拒/2MB 帽/href 白名单)+c9ba773(workflow 注入面;tests/test_ssrf_guard.py)

**文档错漏**:一致性 12 处(manifest 停 0.31.0;插件 license 误标 MIT 实为 Apache-2.0;plugin.json description 旧数字;README 内部自相矛盾;CAPABILITY_MATRIX.md 人读版滞后;半衰期单口径×4 处;tr 份额单口径×3 处);事实抽查 60 条=52✅/7⚠️/1❌(SE Ranking 归属张冠李戴);SKILL 路由 3.5/8(高频任务缺行;deep-research-protocol 挂错区;路由表被脚本目录淹没);测试 8/10(币种/GBK/Wilson 三高危 bug 零捕获) ——✅ c9ba773(文档一致性 12+事实 6+SKILL 路由重排:表前置/5 高频行);测试缺口随各波补齐(现 1604 例回归,见 a605630);CAPABILITY_MATRIX.md 滞后项由 2026-10-12 收口波重刷清零

### R6 知识边界接入(50+ 项,外部 8 视角)

- 新方法论:Search Everywhere Optimization(Semrush/SEL/Adobe)/Kalicube Brand SERP 八面+Algorithmic Trinity v1.0/Community SEO/Zero-click 体系化 ——**已入库**(acd7100:search-everywhere-optimization.md/brand-serp-methodology.md/community-seo-playbook.md;Zero-click 并入 Search Everywhere 体系)
- GEO 新面:IAB 4P 测量标准(Presence/Prominence/Portrayal/Persuasion)/Google agentic commerce 四项/ChatGPT Ads 正式面+Perplexity 转订阅/AI Mode monitoring 全量/个人 agent 客户端×5(Muse·dots·Grok Bot·Instinct·Perplexity Computer)/negative GEO 纠错 playbook ——**已入库**(acd7100:geo-evidence-bank.md Q3 批次+ai-crawler-policy.md/agent-protocols.md)
- 学术修正(必须入库):arXiv 2609.35077(200 万引用:Schema/FAQ/CWV 正效应在域名固定效应下反转)/2607.14035(GEO 批判综述:无稳定跨平台因果)/2609.06811(提示集=答案市场)+6 篇全新(robots 合规实验/agent-ready 49→89/对话捕获/GEO 痕迹 8.9%/CHASE/冲突幻觉) ——**已入库**(acd7100:证据银行 Q3 学术批次 11 条,3 修正回改 7 处)
- 运营体系:算法更新变更冻结协议(Freeze→Pause→Review)/四层运营节奏/治理 RACI(≥3 贡献者)/PRD+证据库/RICE/领导层沟通 ——**已入库**(acd7100:program-management.md+seo-drift-monitoring.md 冻结协议+continuous-operations 四层节奏)
- 归因实验:split_test+功效计算(最足)/synthetic_control/geo_experiment(Meridian GeoX)/triangulate 三源 ——**已实装**(e8750d1:三脚本+triangulate 测试 42 例)
- 内容体系:ContentOps 状态机+遥测/ai-use-policy(AP 四象限)/人评刻度+IRR/content_inventory 四轴治理(keep·update·consolidate·remove+redirect map——此前未登记)/组件化 COPE ——**已实装/入库**(c9ba773 content_queue ContentOps+ai-use-policy 模板;ec4422c content_inventory 四轴)
- 技术新面:Edge SEO 体系/AI Crawl Control 三态商业框架/schema CI 分层采样/View Transitions/WRS 无状态/CF 日志源 ——**已入库**(11e3068:edge-seo.md+schemaCI 方法论)
- 垂直:local_audit 工具化/Job·房产扩展卡/news_sitemap_check/YouTube 站内章/GSC multimodal 采集/ASO 薄桥+ABM 小节(其余明示不建) ——**已实装/入库**(11e3068:local_audit+news_sitemap_check+multimodal_report 57 例+Job·房产卡+video-geo-guide 站内章;ASO/ABM 按登记边界未建)
- 监控对标:SLO+错误预算/flapping+ack 超时/postmortem 模板/Googlebot 会话追踪/incident 角色分工(owner_team) ——**已实装**(11e3068:SLO+flapping+ack 28 例/postmortem 模板+log_session+owner_team 22 例)
- 竞品:Ryze 一方数据 MCP 线(AI-referral 流量即可见性证据)/jev-seo 交付物层(PDF·XLSX·MD)/fire-your-seo-agency LLMO 车道+publish gate/geo-score rubric 版本化;已知三家:claude-seo cockpit/niubigeo 快照 diff/geo-optimizer rubric v2 ——**部分**(a605630:Ryze 一方数据桥 referral→panel 双轨 real/est 分列 18 例;其余三家登记在 borrow-specs 持续跟踪)

**建设顺序修订:R5(正确性)最优先 → R0 接线 → R1 编排器 → R6 高优入库(学术三修正+冻结协议+IAB 对齐+库存治理)→ R2/R3/R4。**

### 战役总结(50-agent 治理战役,2026-10-12 收口)

一句话每项(详细指向见上各组标注):

- **R5 正确性**:37 个复现 bug 五波全修(53bfb89/39db653/4a00867/90c9469/c9ba773),假 Wilson、robots 假 CRITICAL、冷却失效三高危均有钉死测试。
- **R0 全接线**:sensor 上下文/CWV 周检/decay 告警/verify 排期/trend cron/issue 超时/freshness CI 落地(test_r0_wiring 守护;R0-8 转由编排层承担)。
- **R1 骨架**:project.py 编排器+五阶段状态机+`<slug>.seo/` 工作区+strategy-fit+30 分钟首答,散珠成链(c9ba773;R1-9 部分)。
- **R2 数据接入**:gsc_api 纯 stdlib RSA 一次拉取喂 6 脚本,backlink/indexnow/bing_wmt/byo/parity 五件 BYO 归一(fd464f0/acd7100)。
- **R3 生产线**:pSEO 三件+link_graph/orphan_fix/market_fit/market_batch/prune_gate/content_inventory 九件,内链与内容生命周期成线(ec4422c;R3-7 残)。
- **R4 末端**:outreach/directory 双 tracker+split/synthetic/geo 三实验+log_session/SLO/flapping/postmortem(e8750d1/11e3068);六个小项留规格。
- **R6 知识边界**:学术三修正回改、冻结协议、IAB 4P、ContentOps、SLO、Edge SEO 等 50+ 项入库,垂直三工具落地(acd7100/11e3068)。
- **收尾治理**:85 脚本/25 模板/1604 例测试全绿;CAPABILITY_MATRIX.md 人读版从 JSON 全量重刷,data-source-contract.md 重生成对齐 85,本登记簿状态收口(2026-10-12 本波)。

## 四、建设顺序建议

R0(半天)→ R1(管线骨架,1-2 轮 agent 波)→ R2(数据接入)→ R3(生产线)→ R4(末端)。R1 是关键:没有 project 编排器,后面每个新工具都在加重"散珠"问题;有了它,59 个零件变成 10 条命名管线。
