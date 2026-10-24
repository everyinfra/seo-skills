# 全仓新鲜度扫描与修正日志(2026-10-11)

> 用途:2026-10-11 一次新鲜度扫描的修正日志。**历史记录,不作现行依据**:里面的脚本数、测试数、文件行号都是当时的值,现行数字以 `data/capability-matrix.json` 和 `scripts/freshness.py` 的实时输出为准。

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
| research/competitive-landscape.md:53 | ipullrank AIO 零点击 80-83% | 原标待核→回填:Similarweb 2026-03,并纠正归属(见五.1) |
| research/competitive-landscape.md:54 | Semrush 转化 4.4 倍 | 补"(测量于 2025-06)"——semrush.com/blog/ai-search-seo-traffic-study,2025-06 发布,本轮 web 核实 |
| research/competitive-landscape.md:55 | Botify 75% top12 | 原标待核→回填:2024-12,Botify Q4 2024 报告(见五.2) |
| research/competitive-landscape.md:57 | Q&A +25.5% / 促销 −26.2% / 前 30%→55% / W+Y+R+A 占 AIO 引用 38% | 原标待核×4→回填:Semrush 2026-01 / CXL 2026-03 / thedigitalbloom 2025-03~08(见五.3-5) |
| content/discover-news-seo.md:123 | Google 零点击率 68% | 原标待核→回填:SparkToro 2026 年初测量、2026-06 发布(见五.6) |
| content/ai-citation-patterns.md:71-74 | 土耳其 75.3%/印尼 72.2%/西语 83-84%/意大利 48.67% | 原标待核×4→土耳其/印尼回填(seobaz 2026-08/pranas 2026-08);西语/意大利 wiki 升级 [未证实](见五.8-12) |
| research/serp-feature-taxonomy.md:68 | 意大利 AIO 覆盖 48-54% | 原标待核→升级 [未证实](见五.10) |
| markets/en.md:27 | AIO 67.66% vs AI Mode 32.39% 社媒链接 | 原标待核→回填:SE Ranking 研究 2026-10,SMT 2026-10-08 汇总(见五.7) |
| research/directory-submissions.md:131 | SE Ranking 129K 域研究(Wikipedia 7.8%/Reddit 1.8%) | 原标待核→回填:发布 2025-11-24(原记"约 2025-12"有误);"30 天 3.2x"纠正为"3 个月 ≈1.7x";W/R/F 占比改归 Profound(见五.13/15) |
| content/chinese-ai-search-guide.md:107 | 海外三平台漏斗表 | 补"(测量于 2026-04)"——由 arXiv:2604.25707 编号推得 |
| content/meta-tag-formulas.md:119 | "结构化数据 30–40% AI 可见度提升" | 原标待核→升级 [未证实](数字实出自 Princeton GEO 2023-11,非 schema;见五.13) |
| research/directory-submissions.md:123 | FAQPage schema 与 +40% AI 可见度 | 原标待核→升级 [未证实](二手口径混杂;见五.14) |

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

1. **日期类待核 → 已处置(2026-10-11 第二轮,见第五节)**:B 节 10 处 [待核:测量月] 全部处理——9 处回填带来源测量月,6 处升级 [未证实:引用时须注明二手来源](部分行两类并存,如 SE Ranking 行);日期类 [待核] 清零。`grep "\[待核"` 在 references/ 的剩余命中均为非日期类:data-source-contract.md(计数类,第 2 条)与 technical/audit-rule-catalog.md(规则 ID/阈值 caveat,非测量日期,不在本轮范围)。
2. **[待核] 计数类**:data-source-contract.md 缺 ai_views.py、envelope.py 两行(脚本已在但表未收);SKILL.md"52 个实装脚本"与 scripts/ 实际 54 个已提交 .py 的口径差,需主会话裁决(本文件与 SKILL.md 均禁改)。
3. **并行会话冲突(重要)**:本轮任务进行中,工作区出现未提交文件 scripts/benchmark_report.py、tests/test_benchmark_report.py、references/research/niubigeo-deep-read.md(另一会话 WIP)。其中 test_benchmark_report.py 当前 2 用例失败,导致 `scripts/self_check.py` 在工作区红;**stash 后在干净 HEAD 上复跑 self_check = 全绿**(frontmatter/22 模板七段式/死链/golden 全过),失败与本轮 references 修改无关,且 scripts//tests/ 为禁改范围,未处理。测试基线 523 亦为 HEAD 口径(工作区 WIP 会叠加)。
4. freshness.py 的 no_date=69:本轮按任务边界只做行内对齐,未补头部日期;下轮可考虑为 markets/de 等 11 个无日期市场页补"复核"行。

## 四、验证

- `python3 tests/test_canonical_facts.py`:4 tests OK(本日志写入前;写入后终验见下)。
- 终验(本日志落盘后重跑):见会话报告;若本日志自身命中正则为实现失误,应改本日志而非测试。

## 五、[待核:测量月] 回填轮(2026-10-11 第二轮)

方法:对 B 节全部日期类待核项逐条 web 检索一手来源(搜索词 + 读原文核对数字),可确证的回填"(测量于 YYYY-MM,来源:域名)",不可确证的升级 **[未证实:引用时须注明二手来源]**;未编造任何日期。原始仓库 aaron-he-zhu/seo-geo-claude-skills v9.9.12 对应文件不含这些统计(系本仓 2026-10-09 深挖轮自研添加),无内部来源可抄,全部以外部一手为准。

### 回填成功(9 项)

| # | 位置 | 回填口径 | 查证记录(搜索词 → 确认 URL) |
|---|---|---|---|
| 1 | competitive-landscape.md:53 | AIO 零点击 80-83% = Similarweb(中位 ~80/均值 ~83%),测量于 2026-03 | `Similarweb AI Overviews zero-click "80%" median average 83%` → aisearch.similarweb.com/blog/ai-search-optimization-best-practices/(2026-03-29)。**纠错**:原文记 ipullrank;其自研 Datos 研究(13B 事件,2024-10~2025-12,2026-07-30 发布)全量零点击为 46.96%,与本数字分属两源,已改归属并双注 |
| 2 | competitive-landscape.md:55 | Botify 75% top12,测量于 2024-12 | `Botify study 75% AI Overviews cited domains top 12 organic` → lp.botify.com/q4.2024-aio-report + searchengineland.com/google-ai-overview-links-top-12-organic-rankings-449216(2024-12-11);补注老化警示:2026 年 Ahrefs 86.3 万 SERP 口径 top10 重叠仅 ~38% |
| 3 | competitive-landscape.md:57 | Q&A +25.5% / 促销 −26.2%,测量于 2026-01 | `Semrush "337,785" cited URLs Q&A promotional` → semrush.com/blog/content-optimization-ai-search-study/(2026-01-14,337,785 URL/11,882 prompt) |
| 4 | competitive-landscape.md:57 | 前 30% 内容→55% 引用,测量于 2026-03 | `AI Overviews citations "first 30%" content "55%"` → cxl.com/blog/google-ai-overview-citation-sources/(2026-03-06,100 引用抽样) |
| 5 | competitive-landscape.md:57 | W+Y+R+A 占引用 38%,测量于 2025-03~08 | `"Wikipedia, YouTube, Reddit" Amazon "38%"` → thedigitalbloom.com/learn/google-ai-overviews-top-cited-domains-2025/(36M AIO/46M 引用;一手口径为含 Google 自有域**五组**合计 38%,已在正文注明) |
| 6 | discover-news-seo.md:123 | 零点击 68% = SparkToro,测量于 2026 年初、研究 2026-06 发布 | `zero-click searches "68%" up from 49% 2019` → searchengineland.com/google-zero-click-searches-2026-study-479717(2026-06-09);qz.com 原文(2026-10-08)自称转述 SEJ 系报道,底层即 SparkToro |
| 7 | markets/en.md:27 | 67.66% vs 32.39% 社媒链接 = SE Ranking 10 万词研究,测量于 2026-10 | `"67.66%" "32.39%" AI Mode` → socialmediatoday.com/news/ai-favors-brands-with-an-active-social-media-presence/832450/(2026-10-08 汇总;底层 SE Ranking,多源交叉确认) |
| 8 | ai-citation-patterns.md:71 | 土耳其 75.3% 与自然前 10 同页,测量于 2026-08 | `Turkey AI Overviews citations organic top 10 "75.3%"` → seobaz.com/en/blog/turkiye-ai-overview-study-2026(8,282 条土语移动搜索,快照 2026-08-16/文 2026-10-07;美国对照 37.1%/37.0% 一并坐实为 Ahrefs/TripleDart) |
| 9 | ai-citation-patterns.md:72 | 印尼官网出现率 72.2%/引用份额 18.9%,测量于 2026-08 | `Indonesia AI Overviews brand queries "72.2%"` → pranas.co/blog/most-cited-websites-google-ai-overviews-indonesia-2026(2026-08-20,20,839 prompt/225,094 引用;价格类官网份额 1.9% 补强"按意图分流"结论) |

### 未证实(升级 [未证实:引用时须注明二手来源],6 处)

| # | 位置 | 数字 | 失败原因(及最接近口径) |
|---|---|---|---|
| 10 | serp-feature-taxonomy.md:68 | 意大利 AIO 覆盖 48-54% | EN/IT 多轮检索(`AI Overviews Italia percentuale ricerche studio` 等)无一手;最接近:全球触发率 48%(2026-02,Otterly 系转述)与意语信息类查询 35-40%(lensky.it,无测量期)——疑为全球数误标为意处 |
| 11 | ai-citation-patterns.md:73 | 西语 83-84% 引西语源;.es 域 7% vs EN 1.7% | 无一手;最接近:西语本地化查询 96% 引西语源(inboundcycle.com 2026-09,另口径)、mencoro.com 2026-Q3 西班牙研究(无语言切分)——数字间不可互替 |
| 12 | ai-citation-patterns.md:74 | it.wikipedia 48.67% | 一手研究者已定位:Geosnap 意语研究(113,178 条 AI 回答,geo-platform-differences.md:92 已记名),但研究发布页与测量期经 geosnap.ai/blog 与多轮检索未能确证 → 标 [未证实:测量月] |
| 13 | meta-tag-formulas.md:121 | 结构化数据 30-40% AI 可见度 | 数字可溯源至 Princeton GEO(arXiv:2311.09735,2023-11/KDD 2024)但测量对象是"统计数据/引语/引用来源"因子而非 schema;二手(thesaaslibrary/frase/conbersa 等)普遍错套,schema 专属增益无一手 |
| 14 | directory-submissions.md:123 | FAQPage schema +40% AI 可见度 | 无一手;二手归属混杂:Princeton GEO +40% 系"引用来源"因子 / Semrush"被引页 40% 带结构化数据"系占比非增益 / Milestone 2023 系富结果曝光 |
| 15 | directory-submissions.md:131 | ①域信任分 91-96≈6/97-100≈8.4 ②官方域 +11.1pp | SE Ranking 原文(seranking.com/blog/how-to-optimize-for-chatgpt/,2025-11-24)与 SEJ 转述(2025-11-26)均无这两个子口径 → 标未证实。同行已纠错:研究发布日期回填 2025-11-24(原记"约 2025-12"有误);"30 天内 3.2x"原文实为"3 个月内 6.0 vs 3.6(≈1.7x)",已直接改正;Wikipedia 7.8%/Reddit 1.8%/Forbes 1.1% 经 tryprofound.com/blog/ai-platform-citation-patterns(测量 2024-08~2025-06,发布 2025-06-05)确证为 **Profound 的 ChatGPT 口径**,已改归 Profound——印证上轮"两源勿混"猜测,系误记而非同值巧合 |

### 终态(本轮落盘后)

- 日期类 [待核] = 0;`grep -rn "\[待核" references/` 剩余命中均为非日期类:data-source-contract.md:121 与本日志 A 节/三.2(计数类,留主会话裁决)、technical/audit-rule-catalog.md(规则 ID/阈值 caveat,不属测量日期,本轮不动)。
- 本轮改动文件(仅 references .md,禁改清单未触碰):research/competitive-landscape.md、research/directory-submissions.md、research/serp-feature-taxonomy.md、content/discover-news-seo.md、content/ai-citation-patterns.md、content/meta-tag-formulas.md、markets/en.md、overview/freshness-log-20261011.md。未 git commit。
