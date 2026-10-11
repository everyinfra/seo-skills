# Capability Matrix(能力矩阵)

机器可读版:[data/capability-matrix.json](data/capability-matrix.json)(95 条 = 59 脚本 + 23 模板 + 13 references 主干;schema_version 1.0)。本文件是人读版,两者由 [tests/test_capability_matrix.py](tests/test_capability_matrix.py) 守护一致性。

治理出处:[references/research/niubigeo-deep-read.md](references/research/niubigeo-deep-read.md) N10(CAPABILITY_MATRIX 治理格式)。借用其核心思想「**能力=完成**三条件」并按本套件改写:

1. **真实代码存在**——脚本文件在 `scripts/` 落地(不是"计划中");
2. **测试守护存在**——专属测试文件或 `tests/run_tests.py` 内联用例(脚本存在≠能力完成);
3. **合同对勘入表**——数据来源与降级路径已写入 [references/overview/data-source-contract.md](references/overview/data-source-contract.md) 三列并逐一对勘。

与 niubigeo 原版的差异:它的矩阵映射「借来的五个开源项目→本版要求→owner」,本套件的矩阵映射「自有 59 脚本→数据/降级/测试→status」,同样公开承认口径来源(NOTICE 百仓深扫改写)。

## Status 图例

| status | 判据 | 当前数 |
|---|---|---|
| **stable** | 有测试守护(专属测试文件或 run_tests.py 内联用例),或本身即守护工具(self_check/link_check)被检查链每次消费 | 69(34 脚本+22 模板+13 主干) |
| **beta** | 已实装且已入 data-source-contract,但暂无测试守护 | 25(全部为脚本) |
| **draft** | 新增未对勘 | 1(templates/content/trend-jack-playbook.md,规格已定待实装) |

升级路径:新脚本入矩阵默认 **draft** → 合同对勘补行后升 **beta** → 补测试守护(golden 用例)后升 **stable**。

降级模式(与 data-source-contract 全局守则同口径):**①** 等价替代(标 `[est]`)/ **②** 部分执行(显式声明截断或 N/A)/ **③** 停止并指名缺什么 / **④** 静默跳过可选增强。多模式写法「③+②」= 主模式在前。

## 一、审计与页面质量(22)

| 脚本 | 输入 | 输出 | 数据源 | 降级 | 测试 | status |
|---|---|---|---|---|---|---|
| site_audit.py | URL [--market] | json | URL 实时抓取;markets.json 阈值 | ② | test_ai_search_health.py(+run_tests/test_scoring_contracts) | stable |
| health_score.py | audit.json | json | site_audit --json | ② | test_health_score.py | stable |
| traffic_funnel.py | --audit --gsc --cwv --urls | json | 审计 JSON+GSC 页面 CSV | ② | test_traffic_funnel.py | stable |
| quality_rater.py | 纯文本 FILE | markdown | 本地文本(首行=title) | ② | — | beta |
| above_fold.py | URL | markdown | 前 700 字符可见文本 | ③ | — | beta |
| trust_signals.py | URL | markdown | URL 实时抓取 | ③ | — | beta |
| core_eeat.py | FILE | markdown | 本地文本/Markdown | ② | — | beta |
| content_score.py | --draft --competitors --keyword | json | 草稿+≥3 竞品文件 | ③ | test_content_score.py | stable |
| fix_plan.py | --url/--audit | json | 审计 findings | ③ | test_fix_plan.py | stable |
| grounding_page.py | --facts brand.yaml | markdown | Brand Records 事实库 | ③+② | test_grounding_page.py | stable |
| audit_compare.py | --old --new | json | 两次审计 JSON | ③+② | test_audit_compare.py | stable |
| ci_format.py | audit/diff JSON --format | json | 本地 JSON | ③ | — | beta |
| sensor_volatility.py | --gsc/--positions | json | GSC 多日导出 | ③+② | test_sensor_volatility.py | stable |
| forecast.py | --kws [--ctr --actual] | markdown | 关键词 CSV+可选 GSC 曲线 | ② | test_forecast.py | stable |
| prioritize.py | --audit/health JSON | json | 审计 JSON+可选扩展键 | ② | test_prioritize.py | stable |
| changelog.py | --db/--snaps | json | monitor SQLite 或快照 JSON | ③+② | test_changelog.py | stable |
| doctor.py | (无)[--net] | json | 本地环境探测(键名不读值) | ② | test_doctor.py | stable |
| ai_views.py | --url/--html | markdown | URL 抓取或离线 HTML | ③ | test_ai_views.py | stable |
| envelope.py | --audit [--health --priority] | json | 审计 JSON 三源合一 | ② | test_envelope.py | stable |
| benchmark_report.py | --audits/--monitor-db/--scores | json | 多站审计/监控数据 | ③ | test_benchmark_report.py | stable |
| site_crawl.py | --domain(或 --urls 文件) | json | 目标站实时爬取(遵守 robots+crawl-delay,默认 1 req/s) | ① | test_site_crawl.py | beta |
| field_data.py | --url/--urls | json | Google PSI(无 key 低配额)+CrUX(需 key)真实 API | ② | test_field_data.py | beta |

## 二、技术 SEO(7)

| 脚本 | 输入 | 输出 | 数据源 | 降级 | 测试 | status |
|---|---|---|---|---|---|---|
| sitemap_audit.py | URL [--check-limit] | markdown | sitemap 实时抓取(递归 1 层) | ③+② | — | beta |
| hreflang_cluster.py | URL... | markdown | 多 URL 抓取(三载体) | ② | — | beta |
| redirect_chain.py | URL | markdown | 实时逐跳 GET | ③ | — | beta |
| robots_posture.py | URL [--fix-robots] | json | robots.txt+内置 27 bot 名单 | ③ | test_robots_posture.py(+run_tests) | stable |
| llmstxt.py | validate/check/generate | markdown | 本地文件/线上探测/sitemap | ③ | run_tests.py(内联) | stable |
| schema_lint.py | URL | markdown | 抓取页内 ld+json | ③ | — | beta |
| head_check.py | URL\|FILE [--market] | markdown | 抓取或本地 HTML | ③+④ | run_tests.py(内联) | stable |

## 三、关键词与 SERP(7)

| 脚本 | 输入 | 输出 | 数据源 | 降级 | 测试 | status |
|---|---|---|---|---|---|---|
| gsc_mining.py | 导出.csv [--mode --decay] | markdown | GSC 导出 CSV | ③+① | run_tests.py(内联) | stable |
| serp_overlap.py | 输入.csv | markdown | 用户提供 SERP 样 | ③ | run_tests.py(内联) | stable |
| keyword_variants.py | stdin 每行一词 | markdown | 本地归一链 | ④ | run_tests.py(内联) | stable |
| payment_intent.py | stdin 关键词 | markdown | markets.json 词表 | ④ | run_tests.py(内联) | stable |
| geo_difficulty.py | --kd --ur-median --targeting | markdown | 工具导出值(手工输入) | ③+② | — | beta |
| serp_occupancy.py | --market 域名列表 | markdown | 用户观测+内置占位表 | ③ | — | beta |
| grid_rank.py | rank_data.csv | json | 本地网格采集 CSV | ② | —(run_tests 只钉参考文档算例,未测脚本本体) | beta |

## 四、多语言实装(4,markets.json 数据层共读)

| 脚本 | 输入 | 输出 | 数据源 | 降级 | 测试 | status |
|---|---|---|---|---|---|---|
| market_lint.py | --market FILE | markdown | 本地文本+markets.json 64 条 | ③ | run_tests.py(内联) | stable |
| local_format.py | --market 文本 | markdown | 采样文本+markets.json | ③ | run_tests.py(内联) | stable |
| text_metrics.py | stdin 文本 | markdown | 本地文本 | ④ | run_tests.py(内联) | stable |
| text_units.py | <market> stdin | markdown | 本地文本 | ③ | — | beta |

## 五、AI/GEO 测量(6)

| 脚本 | 输入 | 输出 | 数据源 | 降级 | 测试 | status |
|---|---|---|---|---|---|---|
| citation_panel.py | init/record/report/diff/decay/score | json | 人工采样真实回答(绝不模拟) | ② | test_citation_decay.py(+niubigeo_panel/geo_writeback) | stable |
| fanout_analysis.py | 输入.csv | markdown | fan-out 采集导出 | ③ | — | beta |
| ai_referral_log.py | access.log [--bot-ua] | markdown | server access log | ③+②+④ | test_ai_referral_tiers.py | stable |
| citation_gaps.py | --panel --brand-domains | json | citation_panel panel.json | ② | test_citation_gaps.py | stable |
| oracle_check.py | --facts --responses | json | brand.yaml+真实采样回答 | ③ | test_oracle_check.py | stable |
| cite_domain.py | --input answers.json | markdown | 外链工具导出+人工观测 | ② | — | beta |

## 六、归因与管道(6)

| 脚本 | 输入 | 输出 | 数据源 | 降级 | 测试 | status |
|---|---|---|---|---|---|---|
| did_attribution.py | --pre --post | json | GSC 两期 CSV+分组 | ②+③ | — | beta |
| seo_vs_ads.py | --gsc [--ads --competitors] | markdown | GSC×Ads 导出 join | ② | — | beta |
| yt_outlier.py | videos.csv | markdown | YouTube 导出/采集 | ③ | — | beta |
| trend_scout.py | [--vertical] | markdown | HN+Reddit 免 key 抓取 | ④+②+③ | — | beta |
| freshness.py | [DIR] | markdown | *.md 头部日期标记 | ④ | — | beta |
| report_build.py | --findings --out | markdown | findings.json | ② | — | beta |

## 七、持续监控守护(2)

| 脚本 | 输入 | 输出 | 数据源 | 降级 | 测试 | status |
|---|---|---|---|---|---|---|
| monitor.py | init/run/diff/report --site | json | 实时探测+可选 gsc.csv+SQLite | ④ | test_monitor_noindex/p1/p2(+run_tests) | stable |
| notify.py | run --alerts | markdown | monitor 告警 JSON+config | ④ | test_notify_routing.py(+run_tests) | stable |

## 八、套件自维护(3)

| 脚本 | 输入 | 输出 | 数据源 | 降级 | 测试 | status |
|---|---|---|---|---|---|---|
| self_check.py | (无) | markdown | 本地 skill 文件 | ③ | 本身即守护(CI 每次消费) | stable |
| link_check.py | (无) | markdown | 本地 markdown 树 | ③ | 由 self_check 每次消费 | stable |
| intel_check.py | init/check | markdown | 18 信源+.intel-state.json | ③+② | run_tests.py(内联) | stable |

## 九、工作流(2)

| 脚本 | 输入 | 输出 | 数据源 | 降级 | 测试 | status |
|---|---|---|---|---|---|---|
| trend_watch.py | watch/gate(--topics 词表;gate 另需 --angle/--exclusive) | json | 六信号源实时拉取(Google News/Reddit rising/HN/微博/百度热搜;403 源整源跳过告警) | ② | test_trend_watch.py | beta |
| remediation.py | init/verify(envelope audit-data.json;两份 site_audit --json) | json | 上游脚本产出(工单不自带数据) | ③ | test_remediation.py | beta |

## 模板层(23;七段式结构由 self_check 守护)

| 目录 | 模板 |
|---|---|
| templates/audit(5) | full-seo-audit / on-page-audit / technical-audit / entity-audit / report-modes |
| templates/research(7) | keyword-research-output / serp-analysis-output / content-gap-output / competitor-analysis-output / competitor-pages-plan / content-strategy-plan / prompt-bank |
| templates/content(3) | content-brief / pre-publish-checklist / trend-jack-playbook(draft,规格已定待实装) |
| templates/monitor(8) | rank-report / backlink-report / performance-report / alert-playbook / ai-visibility-weekly / ai-visibility-monthly / citation-outreach-brief / forecast-report |

模板不自带数据(data-source-contract 全局守则同样适用):inputs 列写明各自消费的上游脚本产出,逐条见 JSON 的 template 条目。

## references 主干(13)

| 路径 | 角色 | 守护 |
|---|---|---|
| references/overview/capability-map.md | 能力地图(本矩阵姊妹篇) | — |
| references/overview/routing-rules.md | 分诊细则 | — |
| references/overview/intake-checklists.md | 统一 intake 清单 | — |
| references/overview/multilingual-workflow.md | 18 市场主干 | — |
| references/overview/data-source-contract.md | 数据源合同(本矩阵对勘源) | test_capability_matrix.py |
| references/overview/data-onboarding.md | 数据接入阶梯(目标→数据源矩阵+T0-T4) | — |
| references/overview/intel-sources.md | 信源注册表 | intel_check.py 同步维护 |
| references/overview/site-type-playbooks.md | 八站型卡 | — |
| references/content/geo-evidence.md | GEO 证据权威(冲突时以此为准) | — |
| references/technical/deprecated-signals.md | 过时信号看门表 | test_canonical_facts.py |
| references/research/niubigeo-deep-read.md | 本矩阵治理出处(N10) | — |
| references/monitoring/continuous-operations.md | 持续运营手册 | — |
| references/monitoring/ci-gates.md | CI 质量门手册 | — |

## 维护规则(强制)

1. **新增脚本必须同步更新矩阵**:SKILL.md 第 3 节(唯一事实来源)+ data-source-contract.md 补行 + 本文件与 data/capability-matrix.json 各加一条(status 从 draft 起步)。漏更即 `test_capability_matrix.py` ① 变红(双向文件覆盖)。
2. **新增模板必须同步更新矩阵**:templates/ 落盘 + 两处矩阵各加一条。漏更即 ⑤ 变红(22 个数量与磁盘集合校验)。
3. **删除/改名同理**:矩阵与文件系统双向对齐,任何一侧漂移都会红。
4. **status 只升不跳**:draft→beta 需合同对勘行;beta→stable 需测试守护;降级(发现 beta 级问题)须在 PR 里说明原因。
5. 守护链:`python3 tests/test_capability_matrix.py` 五检(①双向文件覆盖 ②tests_file 存在 ③枚举与计数 ④与 data-source-contract 抽查 10 条粗对齐 ⑤模板 23 个);`scripts/self_check.py` 的 `check_capability_matrix` 消费 ①②,矩阵漂移即 self_check FAIL。

## 已知口径备注

- **gsc_mining** 降级为「脚本侧 ③ + agent 层 ①」双写:脚本本身无 GSC 文件即 usage error,等价替代(serp_overlap 采样、标 `[est]`)是 agent 层策略(data-source-contract 差异第 3 条)。
- **grid_rank** 的 run_tests.py 用例钉的是 references/monitoring/local-grid-ranking.md 的 3×3 算例(ARP/ATRP/SoLV 口径),不 import 脚本本体,故 status 记 beta、tests_file 留空。
- **data-source-contract.md** 表头计数(52/54)落后于 SKILL.md 第 3 节的 59,系其文末"发现的差异"已自述的已知漂移;本矩阵以 SKILL.md + 文件系统为准(59)。
