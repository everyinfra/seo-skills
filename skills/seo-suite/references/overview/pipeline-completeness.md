# 管线完备性地图与缺口登记簿(pipeline-completeness)

> 建立 2026-10-11,来自 10 视角并行审计(策略适配/管线断链/pSEO/内容生命周期/内链架构/国际化/外链 PR/监控完备性/数据集成层/管线形态对标)。**愿景基准**:拿到一个网站 → 诊断它适合哪些策略 → 每条策略有一条完整落地管线(数据→计划→执行→验证)→ 每条有长期监控。断言半衰期:状态列每月 intel-update 复盘搭车核对。

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
| # | 缺口 | 规格 |
|---|---|---|
| R0-1 | ~~周检从未自动执行~~ | ✅已修(2026-10-11:schedule 事件按 cron 显式判 weekly) |
| R0-2 | sensor_volatility --context 未接线 | monitor 的 gsc/visibility 告警前调用,high_volatility 时 message 附注 |
| R0-3 | field_data CWV 未进监控 | monitor 周检采 p75,跨档告警(notify 已预留 cwv_* 路由) |
| R0-4 | citation decay 不进告警链 | decay 状态变化注入 alerts(citation_drop warn) |
| R0-5 | remediation verify 无人排期 | envelope-report job 加一步 verify(每日新快照已在手边) |
| R0-6 | trend_watch 无 cron/workflow | 照 seo-monitor 加,退出码 1(有 GO)接 notify |
| R0-7 | trend-state 写进 skill 安装目录 | STATE_FILE 改 cwd/project 工作区 |
| R0-8 | monitor 告警不进工单 | critical 告警同步 remediation init 增补 |
| R0-9 | intel issue 无超时升级 | >72h 未关→notify |
| R0-10 | freshness 无 CI 守护 | capability-drift job 顺带 freshness --fail-stale |

### R1 管线骨架(把散珠串成链——最高结构性优先)
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
| R4-10 | 合同表重生成 | 修 trend_watch/benchmark 行粘连错位 |

## 四、建设顺序建议

R0(半天)→ R1(管线骨架,1-2 轮 agent 波)→ R2(数据接入)→ R3(生产线)→ R4(末端)。R1 是关键:没有 project 编排器,后面每个新工具都在加重"散珠"问题;有了它,59 个零件变成 10 条命名管线。
