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
- **数据延迟**：Search Console 效果数据有延迟，最近几天可能不完整；CrUX 字段数据是过去 28 天的滚动汇总，修复后要过一段时间才反映出来。不要用不完整的最新数据触发告警。

## 三、四种阈值方法

1. **波动带**：基线均值 ± k 倍标准差；有离群点时改用中位数 ± k 倍 MAD。k=2 记 P1、k=3 记 P0 是常用起点。
2. **相对变化**：适合量大的汇总指标，同时必须满足最小绝对量门槛。
3. **事件型**：出现即告警，不看波动。例如 robots.txt 内容变化、首页或核心模板返回非 200、核心页新出现 noindex 或 canonical 指向别处、sitemap 无法获取、人工处置通知。
4. **连续触发**：排名、流量这类噪声大的指标，要求连续 2–3 个观测周期越界才告警（经验起点）。事件型不加这个条件。

另外：同一根因引发的多条告警合并为一条；同一指标设冷却期；恢复正常后自动关闭，但保留记录。

## 四、各类告警的初始建议

下表数值都是**经验起点，需按站点数据校准**。

| 类别 | 看什么 | 起点 |
|---|---|---|
| 可访问与可索引 | 核心 URL 状态码、robots.txt 内容指纹、noindex / canonical 变化 | 事件型，P0 或 P1 |
| 流量 | Search Console 非品牌点击；GA4 自然搜索会话 | 7 日滚动值跌破波动带下沿，连续 2 个周期 |
| 排名 | 按词组看中位位置、进入前 10 的词数 | 核心词连续两次观测跌 3 位以上；长尾词只看组级 |
| 索引 | 页面索引报告的已编入数量、各类「未编入索引」原因的增量 | 按周看相对变化，逐项核对突增的原因 |
| 技术 | 5xx 比例、抓取统计里的请求数与响应时间、CWV | CWV 以 Google 公布的「良好 / 需要改进 / 较差」分档为准，跨档才告警 |
| 外链 | 引用域数量、重要外链丢失 | 按月看；重要链接丢失逐条核实原因 |
| AI 可见度 | 固定问题集的抽样观测：是否提及品牌、是否引用本站 URL | 按周比较多次采样的比例；单次缺失不告警 |

## 五、调校

- 每月复盘告警里有多少真正需要行动：噪音多就放宽 k 值或加连续触发条件，漏报就查哪条信号本该捕获。
- 改版、迁移、换统计代码后重建基线，期间先用更宽的阈值。
- Google 排名系统更新推出期间先记录、不急于改动，等 [Search Status Dashboard](https://status.search.google.com/) 标记推出完成后再做前后对比。

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

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · monitor/alert-manager/references/alert-threshold-guide.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/monitor/alert-manager/references/alert-threshold-guide.md)（Apache-2.0）
- 一手资料：[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)、[CrUX](https://developer.chrome.com/docs/crux)、[Web Vitals](https://web.dev/articles/vitals)、[排名系统指南](https://developers.google.com/search/docs/appearance/ranking-systems-guide)、[Google Search Status Dashboard](https://status.search.google.com/)、[搜索流量下降排查](https://developers.google.com/search/docs/monitor-debug/debugging-search-traffic-drops)
