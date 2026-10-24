# 告警阈值：分级、基线与排查顺序

> 涉及 AI 可见度或 AI 引用的告警，先读 [geo-evidence.md](../content/geo-evidence.md)。

## 用途

给站点设计流量、排名、索引、技术、外链和 AI 可见度告警时读，目标是不漏报、少噪音。数据来自你自己的 Search Console、GA4 和监测工具账号，本 Skill 不附带数据。落地时按 [alert-playbook.md](../../templates/monitor/alert-playbook.md) 写成告警手册。

## 一、分级

按「影响面 × 确定性 × 是否还在扩大」定级，不按指标种类定级。

| 级别 | 典型情形 | 响应 |
|---|---|---|
| P0 紧急 | 全站或核心目录无法访问；robots.txt 或 noindex 误封核心页；Search Console 出现人工处置或安全问题通知；证书即将过期 | 当天处理，立即通知负责人 |
| P1 高 | 核心页面或核心词组持续低于基线下沿；重要模板批量 5xx 或被错误重定向；已编入索引数量明显下滑 | 1–2 个工作日内定位 |
| P2 中 | 单页或次要词组异常；CWV 字段数据跨档变差；重要外链丢失 | 排进本周计划 |
| P3 观察 | 波动在基线范围内、长尾词变化、单次采样缺失 | 只进周报 |

## 二、先有基线，再谈阈值

- **窗口**：至少覆盖几个完整的周，抵消周内起伏；季节性强的业务要有上一年同期数据。
- **口径固定**：同一数据源、时区、国家、设备、品牌/非品牌过滤条件。口径一变，基线作废。
- **剔除已知事件**：大促、宕机、改版、统计代码故障记进事件日志，并从基线里剔除。
- **比较方式**：流量用 7 日滚动值，或「本周一对比前几周的周一」，不用日环比；有季节性时加同比。
- **样本量**：每天只有个位数点击的页面和长尾词，百分比阈值没有意义。设最小绝对量门槛，或合并到目录、模板、词组层级再看。
- **数据延迟**：Search Console 效果数据通常 2 到 3 天后才完整，最新数据可能是初步数据；日数据按太平洋时间（PT）（[官方](https://support.google.com/webmasters/answer/17010575)，核对 2026-10-21）。CrUX 字段数据是滚动窗口汇总（[窗口长度](../overview/facts.md#crux-window)），修复后要等窗口滚过才反映出来。不要用不完整的最新数据触发告警。
- **数据异常期**：Google 在[数据异常页](https://support.google.com/webmasters/answer/6211453)公布已知的数据问题（如[GSC 数据异常期](../overview/facts.md#gsc-anomaly)里的展示 / CTR / 排名记录错误）。基线窗口不要跨异常期；跨了就只用点击。

## 三、四种阈值方法

1. **波动带**：基线均值 ± k 倍标准差；有离群点时改用中位数和 MAD（中位数绝对偏差）。k=2 记 P1、k=3 记 P0 是**本套件口径的起点**，不是标准。两点要注意（来源:[NIST 工程统计手册 1.3.5.17](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm)，核对 2026-10-21）:
   - 用样本均值和标准差算的 Z 分数，最大值只有 (n−1)/√n。基线只有 7 个点时最大是 2.27，所以 k=3 永远不会触发；基线至少要几十个点，否则改用中位数 / MAD。
   - 稳健做法是修正 Z 分数 M = 0.6745 × (x − 中位数) ÷ MAD；Iglewicz 和 Hoaglin 建议 |M| > 3.5 标为潜在离群点。
2. **相对变化**：适合量大的汇总指标，同时必须满足最小绝对量门槛。
3. **事件型**：出现即告警，不看波动。例如 robots.txt 内容变化、首页或核心模板返回非 200、核心页新出现 noindex 或 canonical 指向别处、sitemap 无法获取、人工处置通知。
4. **连续触发**：排名、流量这类噪声大的指标，要求连续 2–3 个观测周期越界才告警（经验起点）。事件型不加这个条件。

另外：同一根因引发的多条告警合并为一条；同一指标设冷却期；恢复正常后自动关闭，但保留记录。

## 四、各类告警的初始建议

下表数值都是**本套件口径的经验起点，需按站点数据校准**，没有 Google 或行业标准出处（CWV 阈值除外）。

| 类别 | 看什么 | 起点 |
|---|---|---|
| 可访问与可索引 | 核心 URL 状态码、robots.txt 内容指纹、noindex / canonical 变化 | 事件型，P0 或 P1 |
| 流量 | Search Console 非品牌点击；GA4 自然搜索会话 | 7 日滚动值跌破波动带下沿，连续 2 个周期 |
| 排名 | 按词组看中位位置、进入前 10 的词数 | 核心词连续两次观测跌 3 位以上（本套件口径）；长尾词只看组级 |
| 索引 | 页面索引报告的已编入数量、各类「未编入索引」原因的增量 | 按周看相对变化，逐项核对突增的原因 |
| 技术 | 5xx 比例、抓取统计里的请求数与响应时间、CWV | CWV 以 web.dev 公布的分档为准（[阈值表](../overview/facts.md#cwv)，第 75 百分位），跨档才告警 |
| 外链 | 引用域数量、重要外链丢失 | 按月看；重要链接丢失逐条核实原因 |
| AI 可见度 | 固定问题集的抽样观测：是否提及品牌、是否引用本站 URL | 按周比较多次采样的比例；单次缺失不告警 |

## 五、调校

- 每月复盘告警里有多少真正需要行动：噪音多就放宽 k 值或加连续触发条件，漏报就查哪条信号本该捕获。
- 改版、迁移、换统计代码后重建基线，期间先用更宽的阈值。
- Google 排名系统更新推出期间先记录、不急于改动。官方建议:等 [Search Status Dashboard](https://status.search.google.com/) 标记推出完成后，**至少再等满一周**，再拿这一周与更新开始前一周比较（[核心更新说明](https://developers.google.com/search/updates/core-updates)）。

## 六、告警后的排查顺序

1. **数据本身**：统计代码、同意横幅、过滤器有没有变？数据是否还在延迟？GA4 与 Search Console 是否同向变化？
2. **可访问性**：站点和核心页能否访问、状态码是否正常；CDN、WAF 或防爬规则是否误拦搜索引擎爬虫（用 Search Console 网址检查核实）。
3. **抓取与索引指令**：robots.txt、noindex、canonical、hreflang、sitemap 最近是否被改。
4. **最近变更**：发布记录、CMS 与模板改动、URL 变更和重定向。
5. **Search Console 通知**：人工处置、安全问题。
6. **外部因素**：排名系统更新、SERP 版面变化（例如 AI 概览等功能分走点击）、季节性需求、竞品动作。
7. **圈定范围**：按目录、模板、设备、国家、查询类型切分，区分全站问题和局部问题。
8. **记录**：根因、证据、处理动作、复查时间。

可对照 Google 的[搜索流量下降排查说明](https://developers.google.com/search/docs/monitor-debug/debugging-search-traffic-drops)。

## 交付时给出

每条告警写明：指标、数据源、口径、阈值方法和数值、连续触发条件、级别、接收人、第一步排查动作，并注明阈值是「经验起点」还是「按本站基线算出」。

## 常见误区

- 用日环比做流量告警，周末和节假日必然误报。
- 用 Search Console 平均排名告警：新增一批靠后的长尾展示，就会让平均值变差。
- 看到垃圾外链激增就提交 disavow。先核实有没有人工处置通知（见 [link-quality-rubric.md](link-quality-rubric.md)）。
- 把某一次 AI 回答里没出现当成长期不可见。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 每条告警写明阈值出处 | 对照「交付时给出」一节；标注「官方」「第三方工具默认」或「本套件口径 / 按本站基线算出」 | 无出处的数值没有标注 = 补标注 |
| 基线窗口干净 | 窗口里没有数据异常期、大促、宕机；用[数据异常页](https://support.google.com/webmasters/answer/6211453)核对 | 含异常期 = 剔除或改只用点击 |
| 波动带用对统计量 | 基线点数 n：n < 30 用中位数 + MAD（|M| > 3.5），不用均值 ± 3σ | 用 n = 7 的 3σ 带 = 永远不触发，失败 |
| 有最小样本地板 | `config.json` 的 `thresholds`：`gsc_min_clicks`、`sitemap_min_sample`、`visibility_min_sample` 都不为 0 | 地板为 0 = 小站百分比噪声 |
| 冷却与合并生效 | `python3 scripts/monitor.py diff --format text` 连跑两次，同指纹第二次应为 suppressed | 重复推送 = 检查 `cooldown_hours` |
| 排查顺序可执行 | 随机挑一条历史告警，按第六节 8 步走一遍 | 任一步没有对应的数据入口 = 补入口 |
| 月度噪声复盘 | 统计上月告警中「无需行动」的占比，写进月报 | 占比超过团队事先写下的上限就放宽阈值（上限由你定） |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · monitor/alert-manager/references/alert-threshold-guide.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/monitor/alert-manager/references/alert-threshold-guide.md)（Apache-2.0）
- 一手资料：[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)、[CrUX](https://developer.chrome.com/docs/crux)、[Web Vitals](https://web.dev/articles/vitals)、[排名系统指南](https://developers.google.com/search/docs/appearance/ranking-systems-guide)、[Google Search Status Dashboard](https://status.search.google.com/)、[搜索流量下降排查](https://developers.google.com/search/docs/monitor-debug/debugging-search-traffic-drops)

## 告警矩阵默认值与 CI 门设计(crawlseo/siteone-crawler 源码深读,2026-10-09;数值是这两个第三方工具的默认值，不是 Google 规定，本套件口径)

### 四条默认告警(crawlseo evaluate.ts,双闸门设计)

| 类型 | 窗口 | 触发条件 | 默认值 |
|---|---|---|---|
| TRAFFIC_DROP | 7 天 vs 前 7 天 | 点击变化 ≤−20% **且当期点击 ≥5**(最小绝对量地板) | −20% |
| POSITION_CHANGE | 28 天 | 平均位置恶化 ≥2 位 | −2 位 |
| CRAWL_ISSUES | 最近一次完成爬取 | 健康分 <70(消息附 issuesFound) | 70 |
| VITALS_DEGRADED | 最近 5 份报告 | ≥2 份差;差 = LCP **或** CLS 超出[良好档](../overview/facts.md#cwv) **或** perfScore<50(连续 2 份,不是单份尖峰) | 2/5 |

新站点自动创建这四条(EMAIL 渠道);命中即写 lastFired(冷却的事实记录)。

### 健康分与计数口径(crawlseo engine.ts / issue-filter.ts)

- 健康分 = 100 − 8×CRITICAL − 3×WARNING − 1×INFO,clamp 0–100。
- **爬虫自用的内部行(details.kind=crawl_summary/content_score)不进用户可见计数**——SQL 细节:JSON 键缺失时比较得 NULL,`NOT (kind=…)` 仍为 NULL,必须显式「无 kind OR 非内部 kind」分支,否则把全部普通问题误过滤掉。
- 分页列表的 per-severity 计数走全量 groupBy,**不随列表 take 数变化**(列表只出 200 行,计数是全爬取的)。
- redirect 解析后的最终 URL 记入 visited,防同页双存导致 phantom DUPLICATE_TITLE;托管基础设施端点(managed infra)的 4xx 降为 INFO「expected, not a broken link」。
- **页级问题严重度映射**(可直接当爬虫告警分级表):HTTP≥400=BROKEN_LINK/CRITICAL;MISSING_TITLE=CRITICAL;MISSING_DESCRIPTION、MISSING_H1、MISSING_ALT、SLOW_PAGE(>3000ms)、LARGE_PAGE(>3MB)、DUPLICATE_TITLE、MIXED_CONTENT、MISSING_ROBOTS、孤儿页=WARNING;MULTIPLE_H1、MISSING_CANONICAL、MISSING_SCHEMA、DUPLICATE_DESCRIPTION、不在 sitemap=INFO。

### CI 质量门设计(siteone-crawler ci_gate.rs)

- **约定**（[siteone-crawler README](https://github.com/janreges/siteone-crawler) 核对 2026-10-21）:全过 exit 0,任一失败 exit 10;输出 JUnit XML(GitLab/Jenkins/GitHub 通用)+ GitHub `::error` workflow command(失败项直接显示在 PR checks 里)。
- **零成功响应立即失败**:0 页、或只有负状态码(−1 连接错误/−2 超时等,不算成功响应)→ 直接 fail,不进阈值判分——爬取失败不许产出假绿的门。
- 检查面(每项 metric/operator/threshold/actual 全部落盘):
  - **min 阈值**:overall 默认 ≥5.0(10 分制);分类可分别配:performance/SEO/security 默认 5.0、accessibility 3.0、best-practices 5.0;
  - **max 阈值**:404 默认 ≤0、5xx ≤0、criticals ≤0(排除 ignore_code);warnings 可选;
  - **forbidden finding codes**:指定 apl_code 只要出现非 OK 项即 fail——**Notice 级也能拦**(计数告警拦不住的用这个);同一 code 同时在 ignore 列表则 ignore 赢(「已接受」优先);
  - **baseline 回归门**:overall 相对基线掉分 ≤ max_score_drop(默认 0 = 一分不许掉);基线文件读不出→大声 WARNING 并跳过该项,**绝不静默绿**;只配 max_score_drop 没配 baseline 同样警告;
  - avg response time 可选;
  - **min pages/assets/documents**:内容类型计数下限,防「只爬到 3 页」的假绿(documents 为 0 时该项不出现)。
- 分类权重（README 的「Quality Scoring」表）:Performance 20% / SEO 20% / Security 25% / Accessibility 20% / Best Practices 15%。

### 爬虫侧 SEO 阈值与防误报(siteone-crawler seo_opengraph_analyzer.rs)

- **只对 indexable 页跑 on-page 检查**(noindex 与 robots.txt 拒抓的页移出分母),且要求 200+HTML。
- title 缺失=WARNING,长度出 10–60 字符=NOTICE;meta description 缺失与出 50–160=NOTICE（这些字符范围是 siteone 的提示阈值；Google 对 title 和 description 没有固定字符上限，截断按显示宽度）;canonical 缺失=NOTICE,**跨 host 指向=WARNING,但 www 与裸域视为等价**(www 规范化是常见故意模式,不等价会报大量噪音)。
- **sitewide noindex 检测的防误报设计**:总页数 ≥10 **且** noindex 占比 ≥80% 才升 CRITICAL(「possible accidental site-wide noindex」,几乎总是部署事故),否则只发 NOTICE——小规模/部分爬取、或分面导航大量故意 noindex 的站不会误触 P0。
- heading 结构:多 H1 标错并计入树;层级跳级(如 h3 直接跟 h1)按「实际应为的层级」标错（这是 siteone 的无障碍检查口径；Google 说标题的数量和顺序对搜索没有影响，不要把它当 SEO 规则）。
