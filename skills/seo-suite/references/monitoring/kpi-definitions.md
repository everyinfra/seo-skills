# SEO / GEO 指标口径

> 涉及 AI 可见度的指标，先读 [geo-evidence.md](../content/geo-evidence.md)。

## 用途

写报告、设告警、定目标之前，先把每个指标「怎么算、从哪来、容易被怎么误读」说清楚。本文不给行业基准数字：行业、站点和查询组合差别太大，目标用本站历史基线和同期对比来定。Search Console、GA4 和第三方工具的数据都需要你自己的账号和权限，本 Skill 不附带数据。

报告里每个指标都要写明：公式、数据源、日期范围与时区、筛选条件（国家、设备、搜索类型、品牌 / 非品牌）、聚合方式、数据延迟。

## 一、Search Console（只覆盖 Google 搜索）

| 指标 | 含义 | 容易误读的地方 |
|---|---|---|
| 点击 | 从 Google 搜索结果点进本站的次数 | 不等于 GA4 会话数 |
| 展示 | 本站链接出现在用户看到的结果里的次数 | 部分结果类型要滚动到或展开后才计数 |
| CTR | 点击 ÷ 展示 | 新增大量靠后的展示会拉低 CTR，不一定是标题的问题 |
| 平均排名 | 每次展示中本站最靠前那条结果的位置，再取平均 | 数值变大不一定是排名下降，可能是新增了靠后的长尾展示 |

口径要点：

- 「按网站」和「按网页」聚合得到的数字不同；查询表各行相加小于总计，因为部分罕见查询出于隐私原因不显示。
- 网页、图片、视频、新闻是不同的搜索类型；Discover 和 Google 新闻有单独的报告。
- 按 Google 的 [AI 功能说明](https://developers.google.com/search/docs/appearance/ai-features)，AI 功能里的展示和点击计入「网页」搜索类型的总数；能否单独拆分，以 Search Console 当前界面为准。
- 品牌 / 非品牌用查询正则筛选，正则写进报告附录，保证每期一致。
- 界面导出有行数上限，大站用 [Search Console API](https://developers.google.com/webmaster-tools) 或批量导出。

## 二、GA4（站内行为与转化）

- **自然搜索会话**：会话级默认渠道组为「自然搜索」的会话。它包括所有搜索引擎，不只 Google。
- **归因范围**：会话级渠道、首次用户渠道、转化归因报告的口径各不相同，同一个「自然搜索带来的转化」会得到不同的数。报告里写明用的是哪一种。
- **关键事件率**：关键事件数 ÷ 会话数，或 ÷ 用户数，写明分母。
- **和 Search Console 对不上是常态**：点击和会话的定义不同；用户拒绝统计或拦截脚本；referrer 丢失会记为直接流量；中间跳转、时区和数据延迟也会造成差异。看两边趋势是否同向，不追求数字相等。
- **来自 AI 助手的访问**：默认渠道分组里通常归为「引荐」，没有 referrer 时记为「直接」。需要时建自定义渠道组，用来源正则单独列出。

## 三、索引、抓取与性能

- **已编入索引页数**：看页面索引报告，可按 sitemap 筛选，对比「已提交」和「已编入」。未编入的原因逐项看，不只看总数。
- **抓取**：抓取统计报告给出请求数、平均响应时间，以及按状态码和抓取用途的分布；服务器日志能看到所有爬虫，更完整。
- **Core Web Vitals**：按 [web.dev](https://web.dev/articles/vitals) 的定义，用字段数据的第 75 百分位评估，LCP ≤ 2.5 秒、INP ≤ 200 毫秒、CLS ≤ 0.1 为良好。Lighthouse 这类实验室数据用来诊断，不能代替字段数据；[CrUX](https://developer.chrome.com/docs/crux) 字段数据是 28 天滚动窗口。

## 四、外链与竞争指标（第三方工具的估算）

- **引用域**：链接到本站的不同域名数。各工具抓取覆盖不同，只能在同一工具内按时间比较。
- **DR、DA、Authority Score 等**：各工具自定义的评分，不是 Google 的指标，也不是排名因素的读数。
- **可见度 / Share of Voice**：基于你自选的关键词集和工具假设的点击率曲线估算。换词集或换工具就不可比。
- **流量价值**：估算点击数 × 广告单价，意思是「买同样的流量要花多少」。它不是收入，不能直接当 ROI。

## 五、AI 可见度（自行观测的抽样指标）

这些不是任何平台提供的官方指标，而是你按固定协议自己采样得到的数：

- **样本**：固定问题集 × 产品或模型 × 语言与地域 × 重复采样次数。每条记录时间、是否联网检索、引用的 URL 和原始回答。
- **提及率**：提到品牌的回答数 ÷ 有效回答数。
- **引用率**：引用本站 URL 的回答数 ÷ 有效回答数。提到品牌不等于引用本站。
- **表述准确率**：回答里关于品牌或产品的事实，有多少是对的。
- 同一问题重复问，结果会变；不同监测工具的数字不可比；和内容改动同时出现的变化只是相关，不能写成因果。

## 六、业务结果

- 自然搜索转化和收入：写明归因模型和时间窗口。
- SEO ROI：写明成本包含哪些、收益按哪种归因、是否扣除了品牌的自然需求；给区间和假设，不给单一数字。

## 常见误读

- 平均排名变差，就说「排名掉了」。
- 拿网上流传的「各位置 CTR 表」判断标题好坏。有效参照是本站同一查询、相近位置的历史 CTR。
- 用工具的 DR 涨跌解释流量变化。
- 凭某一次 AI 回答里有没有本站就下结论。

## 完全装载:营销归因模型表+AI 流量盲区(百仓深扫)

**归因模型表**(marketingskills attribution):first/last/last non-direct/linear/time-decay/position-based(40%首+40%末+20%中)/data-driven(Shapley);**Google Ads/GA4 已于 2023 弃用中间模型**只剩 DDA+last-click;DDA 门槛=200 转化+2,000 交互/30 天(低于此塌缩向 last-click);三范式:MTA(用户级)/MMM(需 2-3 年周度数据+真实预算波动)/Incrementality(geo holdout——"两个渠道争同一转化时的终审")。
**对账五步**:单一真相源(CRM/backend)→**永不跨平台求和**("一次转化两个索赔人")→只读方向一致性→自报做 tiebreaker、**禁止乘数规则**(Meta 2× GA≠翻倍)→预算化 gap。
**盲区四项**:direct(垃圾抽屉)/branded search(挪用上层功劳)/dark social/**AI 流量(经 branded search 或 direct 进入,AI touch 不可见)**——AI 归因只能靠 referrer 清单+日志三源下界估计。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · monitor/performance-reporter/references/kpi-definitions.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/monitor/performance-reporter/references/kpi-definitions.md)（Apache-2.0）
- 一手资料：[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)、[Search Console API](https://developers.google.com/webmaster-tools)、[AI 功能与网站](https://developers.google.com/search/docs/appearance/ai-features)、[GA4 事件](https://support.google.com/analytics/answer/9322688)、[Web Vitals](https://web.dev/articles/vitals)、[CrUX](https://developer.chrome.com/docs/crux)

## 机会挖掘与变更测量的口径细则(crawlseo/seo-monster/iannuttall/elmo/unifapi 源码深读,2026-10-09)

### 四类机会口径(crawlseo seo-opportunities.ts)

expectedCtr 参考曲线(粗略行业均值,**只用于 gap 排序,不用于判断标题好坏**;更稳的做法是 seo-monster 式用本站各位置历史 CTR 自校准曲线):pos≤1=28%、≤2=15%、≤3=11%、≤4–5=7%、≤6–10=3%、≤11–20=1%、>20=0.5%。

| 机会 | 入池条件 | 口径要点 |
|---|---|---|
| striking distance | 位置 4–20 且 28 天展示 ≥20 | 按展示排序;**potential=impressions×expectedCtr(max(1, pos−3))**,即「推进 3 位」的估算 |
| low CTR | 展示 ≥50 且位置 ≤15 | gap=expectedCtr−实际 CTR,须 >2pp;排序按 **展示×gap**(绝对量×差距,不是百分比优先) |
| content decay | 前 28 天点击 ≥10 | 28 天 vs 前 28 天,变化 ≤−25% 才报;小基数页不入池 |
| cannibalization | 同 query ≥2 个落地页且 top 页展示 ≥20 | 页面位置=Σ(pos×imp)/Σimp **展示加权位置**,不是简单平均 |

### GSC 对比与异常(seo-monster 工具目录)

`gsc_compare_periods` 支持按 delta 排序、min_delta_clicks/impressions/position 门槛、**anomalies_only + sigma_threshold(σ 阈值离群检测)**——一次调用出 movers/losers/outliers 报表;decaying/trending pages = 按 delta_impressions 降/升序的页面级包装器(rescue 清单)。多资产场景先看 portfolio_summary(每属性一行的多站 rollup)。

### 变更测量口径(iannuttall measure-change)

- **equal-finalized-calendar-windows**:前后等长、只用 finalized 日历日,按 GSC 的 America/Los_Angeles 时区切日;after 窗被截或每窗 finalized 天 <7 → 指标标 provisional、**不给方向性判定**。
- GSC position 一律是 impression-weighted 平均位置;query 级数据因隐私匿名化缺行≠零流量(retained-query-date-aggregates 口径要在报告里注明)。
- GA4 交叉读用落地页过滤器,且注意 GA4 属性时区与 GSC 太平洋日的边界差异。

### AI 可见度指标公式版(elmo/unifapi)

- visibility = 提及品牌的 run 数 ÷ 总 run 数;share of voice = brand ÷ (brand+Σcompetitors)(提及单位须一致,如「提及该实体的 run 数」)。
- citation coverage = Σ C(b,i) ÷ 成功 cell 数(多品牌可同现,**跨品牌求和可 >100%**);citation share = Σ C(b,i) ÷ Σ_b Σ C(b,i)(非空时恒 =100%);加权版分母带 w_i,**不叫 share**;空分母=N/A 不是 0;valid no-answer 留在 coverage 分母。
- stability = round((1−Bray–Curtis weighted volatility)×100),输入是逐日引用份额向量;fanout 的 avgPerExecution 分母只计发生 fanout 的 run。

### 页内内容分参考公式(crawlseo parseHtml)

base 40 + title 在 15–65 字符 +15(有但不在区间 +5)+ description 在 50–160 +15(否则 +5)+ 恰好 1 个 H1 +15(多个 +5)+ 词数 ≥300 +15(≥100 得 +8)+ 有 schema +5 + 有 canonical +5,clamp 0–100。定位是**页内质量粗筛信号**,不是排名预测;配合 health score(100−8×CRITICAL−3×WARNING−1×INFO)分别看「这页写得如何」与「这站技术上如何」。
