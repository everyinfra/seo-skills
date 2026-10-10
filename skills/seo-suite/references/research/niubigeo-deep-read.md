# niubigeo 深读(Albert-Weasker/niubigeo)

> 建立 2026-10-11。竞品监控(intel-sources.md "5 周 6,140★ 黑马")命中后的**逐文件源码深读**;与 [borrow-specs.md](borrow-specs.md)(SaaS 竞品施工图)、[competitive-landscape.md](competitive-landscape.md)(全景)配套,本文是开源仓 niubigeo 的施工图。标注:【仓库】=该仓自己的文档/源码主张(一手),[推断]=我们自定并注明。深读基线:clone @ commit 014c649(v0.3.0 后,2026-10-10 push)。

## 1. 身份档案

| 项 | 值 | 来源 |
| --- | --- | --- |
| 全名 | `Albert-Weasker/niubigeo`(监控记录无 org 名,作者个人名下) | GitHub API |
| 定位 | 开源 GEO 研究工具:AI 品牌可见性+竞品报告+可复测+证据回溯;口号 "Refuse black-box GEO scores" | README.md |
| Stars | **6,848**(监控时约 6,140 → 5 天后再看 +708;fork 684,watcher 120,open issues 91) | GitHub API 2026-10-11 |
| 创建 | 2026-09-03;最近 push 2026-10-10。**约 5.5 周 6.8k 星** | GitHub API |
| 发布节奏 | v0.1.0-alpha 9/3 → v0.2.0 9/8 → v0.2.1 9/28 → v0.3.0 10/8(三周一版,机械稳定) | releases API |
| 作者 | GitHub `Albert-Weasker`(账面:2024-10 建,27 公开仓,238 followers,无姓名/公司/地点;git 邮箱 herchejane@gmail.com)。贡献者 4 人:38/2/1/1 commits;另有 commit 作者署名 "An AI tool" | GitHub API + git log |
| 商业闭环 | Apache-2.0 开源 + 官网 niubigeo.ai 付费服务(真人 AI 测试/GEO 优化/内容代发);赞助商 NiubiStar(niubistar.com)——同时是案例 R01 的被测域名(case.json 里 `sponsorDisclosure: true`) | README.md + examples/cases/R01 |
| 形态 | **自托管 Web 应用**(Node 22+TypeScript,product-server :8787 + schedule-worker,文件存储无数据库,BYOK 走 OpenRouter/直连),不是 skill/CLI 库 | README.md + docs/ARCHITECTURE.md |
| 曝光 | Product Hunt(post 1256676)+ Trendshift 每日榜(repo 212064)徽章;存在第三方镜像仓 ShijiuWei/niubigeo-mirror-479 | README.md + search API |

## 2. 架构深读

580 文件:`src/`(~150 个 TS 模块)、`docs/`(30+ 方法论文档)、`examples/`(20 个真实域名的全证据案例包)、`test/`(40 个)+ e2e Playwright、`scripts/`(发布门禁/验证器)。核心数据链【仓库】:

```text
ProductProject → Baseline(不可变配置快照) → RecognitionRun(D:域名认知)
  → RecognitionReport(冻结快照) → WatchSet(待测对象/词) → MeasurementRun(K:持续测量)
  → MeasurementMetricPoint(指标点,可从存档重算)
MonitoringTask → ScheduledOccurrence(cron) → BudgetLedgerEntry(费用预约账本)
```

核心主张:一切指标**可从存储证据重算**;每个结论能沿 `指标点 → samples → ProbeRun → Attempt → rawProviderResponse` 回到原文;失败样本永久保留。它有两条我们确实没有的东西:

1. **BYOK 多模型实测执行器**:真的打模型 API(attempt/retry/probe 三层,temperature=0,JSON Schema 结构化输出),带费用账本——串行预约费用、`unknown_cost` 即停新调用、HTTP attempts=1(案例实测 204 次调用 $1.00 全程封顶 $2)。我们按 skill 原则不打 API,这是形态差异;但**预算账本纪律**(见 N6 下文)可进 monitor.py。
2. **20 个公开全证据案例包**:每案例 case.json/evidence-index.json/public-evidence.json/result-summary.json+中英双语原文+失败记录+7 项已知冲突逐条挂链。是"研究证据出版"范式,我们没有案例库。

它**没有**(差异化确认,见 §4):传统 SEO 任何一侧(技术审计/GSC/SERP/内容评分/修复物)、多市场规则层、归因、decay 建模、事实核查。README 自认 "Traditional search-engine rank tracking is not included";v0.3 也没有独立竞品检测 dashboard。

## 3. 值得抄 Top 10(按 价值×stdlib+现有 52 脚本可行性 排序)

### N1. 提及检测算法:URL 掩码 + 实体词表(src/analyzer/response-analyzer.ts)
我们 citation_panel.py 的 record 靠人/agent 填 mentioned;它把这一步机械化【仓库源码】:
- **实体词表** `entityTerms = {品牌名, 完整域名, 域名根(拆 "." 取首段且长度≥3), github repo 名, 全部别名}`,trim 后去重
- **URL 掩码**:先把正文中所有 URL 的字符替换成空格再子串匹配——引用链接里的域名**不算**正文提及(防假阳性核心)
- 首次命中位置 → 全部实体按 first index 排序 → `rankPosition`(1 起);`count`=出现次数;`context`=命中点前 240/后 520 字符;句子边界集合含 CJK 标点 `.。!?!?\n`
- `sentiment` 恒返回 neutral——宁缺勿猜,情感判定留给上层语义评审(与我们五维打分卡的 agent 语义层互补)
- 落地:citation_panel.py `record` 增加 `--answer-file`(纯文本回答)时自动跑该检测填 mentioned/position;ai_views.py 同用。零依赖(urllib.parse + 正则掩码即可)

### N2. 指标切片:显式分子分母 + branded/unbranded 分报 + 交叉错配对(src/metrics/metrics-engine.ts)
【仓库源码】每指标 `{numerator, denominator, value|null}`,**denominator=0 → null 永不报 0%**(与我们 Wilson CI 面板同路数,但更狠):
- 指标族:mentionRate / citationRate / recommendationRate / firstPositionRate / **shareOfVoice=目标提及 run 数 ÷ 全部实体提及覆盖数**(分母是"所有实体的提及总覆盖",不是 run 数——与我们 SoV=目标提及/全部追踪品牌提及等价,但它把分母写死成代码常量)
- **交叉错配对**:`mentionedWithoutOfficialCitation`(被提及但无自有域引用=品牌有关联、内容不被信任)× `citedWithoutProseMention`(被引用但正文没提=内容被信任、品牌关联弱)——borrow-specs B4 里 Peec 的 Brand vs Source visibility 双指标,这里有一份免费源码实现
- 切片维度:provider / model / provider×model / prompt_type / **prompt_targeting(organic_unbranded vs branded_or_direct)**——品牌词与中性词**永不混进同一个分**;`winner`=该回答中 rankPosition 最小的被提及实体,累计 wins
- 落地:citation_panel.py `compute_stats`/`report`:prompts 对象已有 branded 字段,补"分 targeting 两栏各出全套指标+两交叉错配计数"

### N3. 三类来源分离协议 + 5 家引用字段路径(docs/evidence-model.md + src/providers/citation-extractors.ts)
【仓库】引用必须三分类,集合名不能替代 provenance:
| 类 | citation.source | 能证明什么 |
| --- | --- | --- |
| Provider 引用 | provider_annotation / provider_citation_array / provider_grounding_chunk | Provider 本次响应确实返回了该引用(附 `providerPayloadPath`=原始 JSON 里的定位路径) |
| 检索结果 | provider_search_result | URL 出现在搜索工具返回里,**不证明被答案引用** |
| 回答中的链接 | answer_text_url | 正文出现 URL,不证明检索或引用 |

- 5 家 payload 字段路径(直接抄):OpenAI Chat=`choices[0].message.annotations[].url` 或 `.url_citation.url`;OpenAI Responses=`output[i].content[j].annotations[]`;Anthropic=`content[i].citations[].url`;Perplexity=`citations[]`+`search_results[].url`;Gemini=`candidates[0].groundingMetadata.groundingChunks[].web.uri`
- 同 source+URL 去重后重编 citationIndex;**无 Provider 引用时报告写"本次未返回 Provider 引用"**,不从普通链接补造
- 落地:citation_panel.py record 的 citation 记录加 `source_class`(三值)+`payload_path` 字段;report 三栏分开计数;写进 [geo-platform-differences.md](../content/geo-platform-differences.md) 引用口径节

### N4. gapLabel 七叉决策树(src/metrics/keyword-metrics-engine.ts)
【仓库源码】每关键词自动出诊断标签,纯静态判定(0 依赖):
```text
0 条有效回答           → "No completed AI answers"
提及=0 且竞品独现>0     → "Competitors own this AI answer space"(最高优先缺口)
提及=0                → "Target absent from AI answers"
ownedRelevance≥0.6 且提及率<0.5 → "Owned content is not reflected"(自有内容没进答案)
提及>0 且官方引用=0     → "Mentioned without official citation"
竞品独现>0(偶发)       → "Competitors still appear without target"
其余                  → "Covered in this audit"
```
- 配套:`competitorOnlyRun` = !target.isMentioned && 任一竞品 isMentioned;`ownedRelevance` 是站点证据对词的相关度 0-1(N7 词筛出)
- 落地:citation_gaps.py 报告尾部加逐词 gap 标签列;或并入 citation_panel.py report 的 keyword 节。与现有 has_competitor_run 高优先判据互补(它按"词"出,我们按"URL"出)

### N5. 意图先定分母:PromptIntentProfile 冻结进基线(docs/BRAND_QUESTION_TAXONOMY.md)
【仓库】12 意图多标签(product_understanding / brand_evaluation / recommendation / comparison / alternative / pricing / product_fit / product_usage / purchase_decision / risk_evaluation / adoption / source_analysis),关键三分边界:`product_fit`=谁适合 / `brand_evaluation`=值不值得 / `purchase_decision`=选不选——可共存,不许只挑最近邻。**核心机制**:每条启用的问句在基线运行前生成 `{intents[], candidateApplicable, recommendationApplicable}` 并**冻结为不可变基线的一部分**;之后的答案分析无权改变该问句进不进候选/推荐分母——"监测指标的分母不能由每次会变的答案决定"。
- 落地:templates/research/prompt-bank.md 每条 prompt 模板加 `intents` + `candidate_applicable`/`recommendation_applicable` 字段(带 12 意图边界表);citation_panel.py init 校验非空。防的是我们 diff 里最隐蔽的漂移:改一句 prompt 措辞导致它从"推荐类"变"候选类",分母悄悄变了

### N6. 配对差分门 + 指纹 + 预算账本(docs/measurement-methodology.md + examples/lib/budget.mjs)
【仓库】三件可独立抄的纪律:
- **配对差**:目标 vs 竞品推荐率之差,仅当 runId/modelId/搜索配置/keywordId 相同、两侧分母相等且>0、样本数相同且**逐数组位置 probeRunId 相同**才计算,否则 null——不许拿两个独立百分比相减。落地:citation_panel.py `diff` 从"面板级对比"升级为"逐 prompt 配对对比"(我们已有 |Δ|≥5pp 且 n≥10 闸门,加同 prompt_id+同 engine+同 fingerprint 配对门)
- **探针指纹**:provider/model+搜索模式+协议版本+语言+scenario+subject+repetitions+temperature/maxTokens+匹配规则版本;K 另加 keywordSetHash;同指纹≠范围一致(它诚实声明指纹不含别名/实际上游模型版本)。落地:panel 每条 record 存 fingerprint hash,diff 跨指纹时强制标注"不可比"
- **费用账本**:串行预约(先记账再调用)、`unknown_cost` 立即停止新增调用、HTTP 重试 attempts=1。落地:monitor.py `--budget-minutes` 旁加 `--budget-usd` 预约语义说明(我们有时间预算,缺费用纪律文档)

### N7. observed-consensus/v1 监测词筛选(examples/lib/study.mjs)
【仓库】从已归档回答里机械选监测词(无语义改写):保留**可在原文精确定位证据**的词 + **≥2 个不同模型同词关联** + 排除命中目标/竞品身份子串的词;按独立模型数降序取前 N。四种排除码全留档:`contains_observed_identity` / `no_exact_answer_evidence` / `insufficient_independent_association` / 非 neutralEligible——候选与落选原因都保存,不黑箱。
- 落地:prompt-bank.md 生成纪律加一节"多模型共识确认"(GSC 词→prompt→至少 2 模型关联→才入固定监测集);citation_panel.py init 支持 `--from-archive` 从历史 record 里筛

### N8. D/K 协议分离与诚实统计纪律(docs/measurement-methodology.md)
【仓库】这是全仓最值钱的方法论文档(133 行,含公式级分母定义):
- **D(点名域名)≠ K(中性词不点名)**:D 测认知与关键词关联,K 测自然发现,**指标永不混算**;"复述已点名的域名不能叫自然发现率"。我们 prompt-bank 已有 branded 标记,N2 的 targeting 分报是同一思想;把这句话写死进 [kpi-definitions.md](../monitoring/kpi-definitions.md)
- failed ≠ 品牌未出现;有效分母下的 0% 是真未命中;null=不能计算;`pointState` = complete / partial / no_data 三态;**不同模型点各留分母,不平均成综合分**("不发明一个未经定义的混合分"——反黑盒的代码化)
- `executionMode` 四值:native / sdk / unverified / provider_always_on——**请求联网 ≠ 实际原生执行**,SDK 路径不得写成"模型内建搜索"。落地:[geo-platform-differences.md](../content/geo-platform-differences.md) 加 executionMode 口径;citation_panel record 加可选 `execution_mode` 字段
- 落地(文档):monitoring/kpi-definitions.md + geo-scoring-rubric.md 措辞对齐

### N9. 证据定位核验:UTF-16 偏移 + recordHash(docs/evidence-model.md)
【仓库】`AnswerEvidenceLocation.start/end` 为 **UTF-16 code unit**(非 UTF-8 字节),核验条件 `rawAnswer.slice(start,end) === quote`;定位失败 evidence=null,**不虚构偏移**;同文多次出现取首次精确匹配。recordHash=`sha256(JSON.stringify(value))` 无缩进无末尾换行——不是文件字节 hash,公开证据包另算文件 SHA-256。
- 落地:oracle_check.py / quality_rater.py 引用 AI 原文片段时加同款核验步骤(Python `str` 切片恰是 UTF-16 近似[推断:Python 按 code point,CJK BMP 内等同,增补平面需注意]);report_build.py 的 findings JSON 加 record_hash 字段

### N10. CAPABILITY_MATRIX 治理格式(docs/CAPABILITY_MATRIX.md)
【仓库】"能力=完成"三条件:真实 provider 代码存在 + 自检存在 + 用户报告用平实语言暴露证据;外加 Reference Capability Mapping 表:`源项目 → 核心思想 → 本版要求 → 代码 owner`,公开承认借自 Elmo / Aperture / OneGlanse / AiCMO / Citatra 五个开源项目(它自己也是"百仓聚合"范式,和我们 NOTICE 声明同路数)。
- 落地:[capability-map.md](../overview/capability-map.md) 加"完成判据"三条件列(脚本存在≠能力完成,还要 self_check/golden 覆盖+报告平实语言暴露证据)

## 4. 我们已有的它没有(差异化确认)

- **传统 SEO 全链**:技术审计(site_audit/schema_lint/robots_posture 27 bot/llmstxt/hreflang/sitemap/redirect_chain)、GSC 挖矿、SERP 分析、内容评分与优化(content_score/quality_rater/above_fold/core_eeat)、grounding_page 生成、fix_plan 修复物——它对网站本身只抓 meta/heading/JSON-LD 做词种子(src/keywords/site-evidence.ts),不做任何技术侧
- **18 市场多语言规则层**(markets.json 64 检查)——它 UI 仅 en/zh/pt-BR,协议有 language 字段但无市场规则
- **归因侧**:ai_referral_log(access log 下界+bot 四桶)/did_attribution/seo_vs_ads——它只打模型 API,无自有站数据
- **citation decay 半衰期协议**——它只有快照 Diff View,无 decay 建模(我们 decay 子命令独有的官方常数体系)
- **oracle_check 事实核查**(brand facts KB vs AI 回答)——它存证据但无 KB 比对
- **内容生产侧**:它诊断完的修复是付费服务(真人测试/内容代发),开源版不给修复物;我们 grounding_page/fix_plan/内容模板全开源
- **零依赖 stdlib skill 形态** vs 它 Node 22+npm(linkify-it/cron-parser/zod 等)+Docker——不同交付物,我们的每条借鉴都必须保持纯 stdlib 可实现(N1-N10 全部满足)

## 5. 风险信号

- **星速与工程规模不匹配(未确认推广手段)**:5.5 周 6,848★、fork 684,但贡献者仅 4 人(38/2/1/1 commits)、watcher 120(fork:watch≈5.7)、commit 署名含 "An AI tool";Product Hunt+Trendshift 双徽章+赞助商即案例 R01(sponsorDisclosure:true)+官网付费漏斗。高度像**营销驱动的 AI 生成代码仓**。星数 ≠ 方法论质量,方法论文档本身质量高(见下),但"6.8k 星社区"叙事不成立【未确认是否存在 star campaign,如实标注】
- **方法诚实度反而高(加分项)**:known-issues.md 公开 7 项 unique-first 结构化标签冲突(同一回答把 3-10 个对象都标"唯一第一");limitations.md 公开 L01-L20(统计可能混用首次与重试结果;检索结果可能被误读为已验证引用;UI 尚非完整双语)。**抄它规格时必须避开这些已声明的坑**:别抄它 provider_citation 资格判断(两入口不一致,L08);别信模型自报的 recommendation/first 标签(L06 未强制证据核验)——所以 N1(机械提及检测)+N9(偏移核验)才是安全底座
- **它自己也是聚合仓**:CAPABILITY_MATRIX 自认核心思想借自 Elmo/Aperture/OneGlanse/AiCMO/Citatra——引用其规格时可顺手把这五个名字当线索,但溯源到源头再定【官方口径】
- **许可证**:Apache-2.0 宽松,借规格无障碍;assets/providers/* 是各 AI 厂商商标 logo(另有 LICENSE),不要搬;我们只借思想+公式,不搬代码(与 NOTICE"百仓深扫改写"一致)
- **宣传略超前**:README "Refuse black-box scores" 但 v0.3 才有关词监测,竞品检测 dashboard 未做(自认);20 案例中 10 个 partial、失败保留在案——案例是真实研究材料,不是成功案例展示(这点反而可信)

## 6. 来源(实际读到的文件,clone @ /tmp/niubigeo,commit 014c649)

- 元数据:GitHub API `repos/Albert-Weasker/niubigeo`、`search/repositories?q=niubigeo`、`contributors`、`releases`、`users/Albert-Weasker`(2026-10-11)
- 定位与商业:README.md(全 354 行)、CHANGELOG.md(全)、docs/ARCHITECTURE.md(前 80 行)、examples/cases/R01/case.json + result-summary.json
- 方法论:docs/measurement-methodology.md(全 133 行)、docs/evidence-model.md(全 142 行)、docs/BRAND_QUESTION_TAXONOMY.md(全 73 行)、docs/INTENT_RESULT_LAYER.md(全 99 行)
- 风险:docs/known-issues.md(冲突表)、docs/limitations.md(全 76 行)、docs/CAPABILITY_MATRIX.md(前 30 行)
- 源码:src/analyzer/response-analyzer.ts(全 159 行)、src/providers/citation-extractors.ts(全 201 行)、src/metrics/metrics-engine.ts(全 326 行)、src/metrics/keyword-metrics-engine.ts(全)、src/keywords/keyword-analyzer.ts(全 301 行)、src/prompts/audit-category.ts(全)、src/prompts/brand-question.ts(结构)、src/prompts/monitoring-prompt-intent-classifier.ts(前 60 行)、src/monitoring/schedule-calculator.ts(前 100 行)、src/product/keyword-monitor-schema.ts(全)、examples/lib/study.mjs(共识筛选段)
