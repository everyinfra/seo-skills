# 内容衰退：信号、诊断与处置决策

## 用途与何时读

某个页面或一批页面的自然搜索表现下滑，要判断「是不是内容衰退、有多严重、该更新、重写、合并还是下线」时读。决定之后怎么执行，见 [content-refresh-playbook.md](content-refresh-playbook.md)。本文负责诊断和决策，那份负责执行。

## 需要的数据

| 数据 | 用来看什么 | 说明 |
|---|---|---|
| Search Console 效果报告 | 按页面、再按查询看点击、展示、点击率、平均排名的变化 | 需要你自己的账号；最近几天的数据可能还不完整 |
| Search Console 网址检查、页面索引报告 | 是否仍被编入索引，Google 选定的规范网址 | 同上 |
| GA4 着陆页数据 | 自然搜索带来的访问和转化是否同步下降 | 需要你自己的账号 |
| 爬虫工具导出 | 失效链接、重定向链、noindex、canonical 变化 | 例如 Screaming Frog，或你自选的工具 |
| 排名追踪（可选） | 固定查询的排名走势和 SERP 功能变化 | 你自有或自选的数据源 |

## 先排除非内容原因

按顺序检查，任何一项成立，都先处理它，不要急着改内容：

1. **测量问题**：统计代码、同意横幅、GA4 配置、过滤条件最近有没有改动。
2. **技术问题**：页面是否仍被编入索引；有没有误加 `noindex`、canonical 被改、重定向变化、服务器错误、渲染失败、内链被删、站点改版或迁移。
3. **需求变化**：查询的展示量整体下降，而你的排名没变，说明是需求下降或季节性。用同比而不只是环比来判断。
4. **SERP 变化**：排名稳定、展示稳定、点击率下降，常见原因是 SERP 上新增了 AI 概览、视频、购物等模块，或者竞争页面的标题更吸引人。
5. **Google 更新**：下滑时间是否与 Google 搜索状态面板公布的排名更新吻合。吻合只说明值得对照，不等于因果。

整站或整个目录同时下滑，通常是技术问题、测量问题或算法更新，而不是单篇内容衰退。

## 衰退信号

**表现类**（来自 Search Console）：

- 点击持续下降，且超出这个页面自己以往的正常波动范围。
- 平均排名下降，同时展示随之下降。
- 原先带来点击的主要查询消失，或者被站内另一个页面取代（可能是互相抢位，见 [topic-cluster-templates.md](../research/topic-cluster-templates.md)）。
- 排名不变而点击率下降：先看 SERP 和标题，见 [title-formulas.md](title-formulas.md)。

**内容类**（人工或爬虫检查）：

- 过时的年份、统计、价格、截图、界面描述。
- 提到已下线的产品或功能，给出的做法已被官方文档推翻。
- 外部链接失效。

**竞争类**：

- 新的页面排到你前面，它们回答得更完整、更新或有一手证据。
- SERP 前列的页面类型变了，例如从教程变成工具页，说明意图发生了漂移。

**辅助类**：自然搜索访问的转化或互动下降；重要外链丢失。单独出现不能确认衰退，只作佐证。

## 严重度

综合三个维度判断，阈值以站点自己的历史数据为准，不套行业平均数：

- **页面价值**：它带来的转化、在主题集群里的位置、外链数量。
- **偏离程度**：下降幅度相对于该页面正常波动的大小。
- **范围和持续时间**：一个查询还是全部查询；短期波动还是持续数周。

| 等级 | 典型情况 | 处理 |
|---|---|---|
| 观察 | 价值一般的页面小幅下滑，或者只持续了很短时间 | 加入监测，下个复查周期再看 |
| 处理 | 持续下滑，排除了非内容原因，内容确有过时之处 | 排进更新计划 |
| 优先 | 高价值页面持续下滑，或者主要查询已被别的页面取代 | 尽快诊断并处理 |

## 处置决策

| 情况 | 决定 |
|---|---|
| 意图没变，内容大体正确，只是有过时之处 | **更新**（保留 URL） |
| 意图已变，或者结构和深度明显跟不上 SERP 前列 | **重写**（通常保留 URL） |
| 多个页面对准同一组查询，各自都不强 | **合并**到最强的一页，其余 301 到它 |
| 与业务无关、没有流量和外链、也不值得更新 | **下线**：有相关替代页就 301；没有就返回 404 或 410 |
| 站内仍有用途，但不需要出现在搜索结果里 | 保留页面，加 `noindex` |

更新和重写之间的具体划分，以及执行清单，见 [content-refresh-playbook.md](content-refresh-playbook.md)；状态码的选择见 [http-status-codes.md](../technical/http-status-codes.md)。

## 更新之后

- 只有内容确实有实质修改时才更新可见日期和 `dateModified`；只改日期不改内容，本身就是 Google 有用内容自查里提到的问题做法。
- 站点地图的 `lastmod` 如实反映修改时间。
- 复查时间按这个页面以往的抓取和排名响应节奏定，不承诺固定的恢复周期或恢复比例。
- 一次集中改动后留出观察期，避免连续改动导致无法判断哪一项起了作用。

## 交付物

每个候选页面一行：

| 页面 | 观察到的信号 | 已排除的原因 | 严重度 | 决定 | 理由 | 复查时间 |
|---|---|---|---|---|---|---|

另附：需要先修的技术或测量问题清单，以及合并和下线页面的重定向映射表。

## 常见误区

- 一看到流量下降就改内容，没先排查技术、测量和季节因素。
- 只改日期不改内容。
- 用通用的「各排名位置点击率」表判断自己页面是否异常。
- 把 SERP 模块变化造成的点击下降，当成内容质量问题来重写。
- 一次改动太多，无法判断哪一项起了作用。

## 量化触发阈值与归因(seomachine 深读 2026-10-09b)

**候选触发(冷启动参照,按站点自身波动校准后替换)**:流量环比 −20% 入 declining 候选;关键词排名 11–20 视为「跌出首页」带(quick win,小改即可回收);展示量高而 CTR 偏低 → 判为 meta/标题衰退而非正文衰退,动作只改 title/description。降幅不足 20% 或仍在正常波动期内的页面先观察,不下结论。

**参与度基准带(仅冷启动参照;本套件原则仍是以站点自身历史为基线,不套行业平均)**:bounce rate 30/40/50/60%(优/良/中/差),页面平均停留 180/120/60/30 秒;转化率按目标分档:trial 15/10/5/2%、demo 10/5/3/1%、lead(下载/订阅)30/20/10/5%。高 bounce + 短停留组合指向首屏与价值主张问题,而非字数问题。

**五维归因(技术/季节排除后)**:对正文跑五维评分(humanity/specificity/structure/seo/readability),**加权亏分最多的维度即衰退主因**——specificity 崩=数据过时(刷新统计与事实);seo 维崩=meta/H1/字数不达标(见 [meta-tag-formulas.md](meta-tag-formulas.md));readability 崩=句长节奏与段落问题;humanity 崩=AI 味渗入。配合 SERP 字数对标(中位数/P75,见 [content-refresh-playbook.md](content-refresh-playbook.md))区分「深度被竞品超越」与「自身质量下滑」两种衰退。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/content-refresher/references/content-decay-signals.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/optimize/content-refresher/references/content-decay-signals.md)（Apache-2.0）
- 深读补充：[TheCraigHewitt/seomachine · data_sources/modules](https://github.com/TheCraigHewitt/seomachine)(data_aggregator/landing_performance/content_scorer)
- 一手资料：[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)、[有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[Google 搜索状态面板](https://status.search.google.com/)、[重定向](https://developers.google.com/search/docs/crawling-indexing/301-redirects)、[HTTP 状态码与网络错误](https://developers.google.com/search/docs/crawling-indexing/http-network-errors)、[站点地图](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)
