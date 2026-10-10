# 全仓新鲜度扫描与修正日志(2026-10-11)

> 建于 2026-10-11。范围:references/ 全量(禁改文件除外)。方法:`python3 scripts/freshness.py references` 基线 → 数字一致性 grep → 关键数字日期口径抽查 → 过时信号口径复查 → 裸路径检查。本日志只记录事实与处理,不承载新口径;口径权威仍为 [deprecated-signals.md](../technical/deprecated-signals.md) 与 [data-source-contract.md](data-source-contract.md)。

## 一、基线与终态

| 指标 | 基线(2026-10-11 扫描) | 终态(修正后复跑) |
|---|---|---|
| freshness.py 汇总 | fresh=45 / stale=0 / error=0 / invalid=0 / no_date=69(共 114 个 .md) | 同左(本轮未增删头部日期,只做行内数字/口径对齐) |
| 最旧带日期文件 | content/geo-evidence.md(2026-09-04,距今 37 天,<90 天阈值) | 同左 |

结论:无过期(stale)证据;本轮处理的是**行内数字陈旧与口径缺口**,不是头部日期陈旧。

## 二、发现与处理清单

### A. 数字一致性(现状描述与真实状态不符)

| 文件:行(修前行号) | 问题 | 处理 |
|---|---|---|
| research/competitive-landscape.md:76 | 现状描述"38 脚本纯 stdlib 零依赖、75 金标测试"——与现状(52 脚本/523 tests)不符 | 改为"52 脚本…523 金标测试",保留"(原 38/原 75)"注记 |
| research/competitive-landscape.md:80 | "现状列对照工作副本(38 脚本/107 文档/14 模板/75 测试/18 门户)"全组旧数 | 改为 52 脚本/114 文档/22 模板/523 测试/18 门户(2026-10-11 对勘),保留原记录括注 |
| overview/data-source-contract.md:5 | 括注"SKILL.md 第 3 节称 53,实为 52"已过期(SKILL.md 现写 52);且未反映 scripts/ 已增至 54 个已提交 .py | 更新括注:注明 SKILL.md 已改 52;2026-10-11 复核 ai_views.py/envelope.py(v0.34.1 新增)未入表 |
| overview/data-source-contract.md:117 | "发现的差异"第 1 条同样停在 2026-10-10 口径 | 改为带日期的沿革记录 + [待核:主会话补两行并同步 SKILL.md 计数口径] |

竞品叙事段(competitive-landscape.md:65 claude-seo"410 测试"、borrow-specs.md 等外部仓计数)为外部项目事实,未动。

**计数口径备注(供主会话裁决)**:`ls scripts/*.py` 现为 55——54 个已提交(52 合同表内 + ai_views + envelope)+ 1 个并行会话未提交 WIP(benchmark_report.py,出现于本轮任务进行中)。SKILL.md 第 3 节口径为 52(禁改),references 现状段按 52 对齐、差异已在 data-source-contract.md 显式记录。测试基线:`python3 tests/run_tests.py` = 523 全绿(HEAD 提交口径;见"剩余风险"第 3 条)。

### B. 关键数字日期口径抽查(12 处)

| 文件:行 | 数字 | 处理 |
|---|---|---|
| research/competitive-landscape.md:53 | ipullrank AIO 零点击 80-83% | 标 [待核:测量月](Pew/Ahrefs 两项原已带 2025-07/2026-02) |
| research/competitive-landscape.md:54 | Semrush 转化 4.4 倍 | 补"(测量于 2025-06)"——semrush.com/blog/ai-search-seo-traffic-study,2025-06 发布,本轮 web 核实 |
| research/competitive-landscape.md:55 | Botify 75% top12 | 标 [待核:测量月] |
| research/competitive-landscape.md:57 | Q&A +25.5% / 促销 −26.2% / 前 30%→55% / W+Y+R+A 占 AIO 引用 38% | 各标 [待核:测量月](KDD 2024 一项原已带日期) |
| content/discover-news-seo.md:123 | Google 零点击率 68% | 标 [待核:测量月,qz.com 同文口径](同句 AIO 39.4% 原已带 2026-06) |
| content/ai-citation-patterns.md:71-74 | 土耳其 75.3%/印尼 72.2%/西语 83-84%/意大利 48.67% | 各标 [待核:测量月](日本/韩国两条原已带日期) |
| research/serp-feature-taxonomy.md:68 | 意大利 AIO 覆盖 48-54% | 标 [待核:测量月] |
| markets/en.md:27 | AIO 67.66% vs AI Mode 32.39% 社媒链接 | 标 [待核:测量月] |
| research/directory-submissions.md:131 | SE Ranking 129K 域研究(Wikipedia 7.8%/Reddit 1.8%) | 补"研究发布约 2025-12"并注明头部占比与 Profound 2025-06 口径同值、两源勿混[待核] |
| content/chinese-ai-search-guide.md:107 | 海外三平台漏斗表 | 补"(测量于 2026-04)"——由 arXiv:2604.25707 编号推得 |
| content/meta-tag-formulas.md:119 | "结构化数据 30–40% AI 可见度提升" | 标 [待核:测量月] |
| research/directory-submissions.md:123 | FAQPage schema 与 +40% AI 可见度 | 标 [待核:测量月;系 AI 可见面主张,与 SERP 富结果退役无关] |

原则:日期可从一手来源/编号确证的补"(测量于 YYYY-MM)";不可确证的一律 [待核],未编造任何日期。

### C. 过时信号口径复查(对照 deprecated-signals.md)

| 文件:行 | 问题 | 处理 |
|---|---|---|
| overview/multilingual-workflow.md:353 | FAQ 富结果状态写成"2023-08 起限制于政府/健康权威站",缺 2026-05-07 全站退役——与看门表 FAQPage 行口径冲突 | 改为"2023-08 先收窄…2026-05-07 起全站退役;HowTo 富结果 2023-09 起停展",保留"FAQPage LD 照常挂"结论 |
| content/meta-tag-formulas.md:108-117 | schema 速查表列 FAQPage/HowTo 未注明对应 SERP 展示已停 | 表后加一行注:停展时间与"标记本身合法仅作语义描述"口径,链至 deprecated-signals.md |
| research/directory-submissions.md:123 | "+40% AI 可见度"易被误读为富结果主张 | 括注澄清(见 B 节) |

复查无冲突的命中(未动):discover-news-seo.md ClaimReview 节(2026-10-10 口径,退役+存续价值双写)、borrow-specs.md:126、positioning-frameworks.md:108/169、serp-feature-taxonomy.md:29、ugc-site-search.md:107、seo-drift-monitoring.md:144、validation-guide.md:47/137/212、cwv-playbook.md(FID 仅历史对照用法)、geo-evidence.md:40。FID/sitemap priority·changefreq/Indexing API/GBP chat 各命中处均与看门表一致。naver-searchadvisor.md 的 sitemap 字段与 HowTo 条目为 Naver 侧口径,不属 Google 看门表管辖。routing-rules.md:162 与 site-type-playbooks.md:182/224 推荐 HowTo 标记属"标记合法"范畴,非冲突,未动。

### D. 裸路径检查

- 剥离 markdown 链接后扫描全部 .md 的文件引用:指向**本套件**不存在文件的引用 = 0。命中 scripts/xxx.py 的 4 处(seo-drift-monitoring.md:81 drift_baseline.py、routing-rules.md:97 validate_skill.py、keyword-intent-taxonomy.md:170/180 content-quality-gate.py)均为外部仓库深读叙事(claude-seo/qiaomu-seo/ai-marketing-skills),非本仓路径,未动。
- 大量裸名 .md(markets/*.md → multilingual-workflow.md、zh.md → chinese-ai-search-guide.md 等)经存在性核对全部可解析到 references/ 子目录真实文件,未动。
- competitive-landscape.md:100 出现 data-source-adapter-matrix.md——为借鉴清单"落地"列的**规划中**文档(明示"新…"),非悬空引用,未动。
- 相对链接全量校验:3 个命中均为行文占位符(`({绝对URL})`/`(URL)`),非真实链接。

## 三、剩余风险 / 待核项

1. **[待核] 日期类**:B 节 12 处中 10 处标 [待核:测量月],建议下次自更新轮带回填(优先:Botify 75%、W+Y+R+A 38%、零点击 68%)。
2. **[待核] 计数类**:data-source-contract.md 缺 ai_views.py、envelope.py 两行(脚本已在但表未收);SKILL.md"52 个实装脚本"与 scripts/ 实际 54 个已提交 .py 的口径差,需主会话裁决(本文件与 SKILL.md 均禁改)。
3. **并行会话冲突(重要)**:本轮任务进行中,工作区出现未提交文件 scripts/benchmark_report.py、tests/test_benchmark_report.py、references/research/niubigeo-deep-read.md(另一会话 WIP)。其中 test_benchmark_report.py 当前 2 用例失败,导致 `scripts/self_check.py` 在工作区红;**stash 后在干净 HEAD 上复跑 self_check = 全绿**(frontmatter/22 模板七段式/死链/golden 全过),失败与本轮 references 修改无关,且 scripts//tests/ 为禁改范围,未处理。测试基线 523 亦为 HEAD 口径(工作区 WIP 会叠加)。
4. freshness.py 的 no_date=69:本轮按任务边界只做行内对齐,未补头部日期;下轮可考虑为 markets/de 等 11 个无日期市场页补"复核"行。

## 四、验证

- `python3 tests/test_canonical_facts.py`:4 tests OK(本日志写入前;写入后终验见下)。
- 终验(本日志落盘后重跑):见会话报告;若本日志自身命中正则为实现失误,应改本日志而非测试。
