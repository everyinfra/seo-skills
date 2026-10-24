# 内容衰退：信号、诊断与处置决策

> 复核于 2026-10-21（首轮 2026-10-18）：Google 文档逐条对照原文，GSC 导出口径与 `gsc_mining.py`、`content_queue.py` 源码和实跑对齐。

## 用途与何时读

某个页面或一批页面的自然搜索表现下滑，要判断「是不是内容衰退、有多严重、该更新、重写、合并还是下线」时读。决定之后怎么执行，见 [content-refresh-playbook.md](content-refresh-playbook.md)。本文负责诊断和决策，那份负责执行。

## 需要的数据

| 数据 | 用来看什么 | 口径（官方文档，核对 2026-10-21） |
|---|---|---|
| Search Console 效果报告导出 | 按查询或页面看点击、展示、点击率、平均排名 | 表格最多显示 1,000 行；查询表不含匿名查询；数据通常 2–3 天后可用；按太平洋时间分日（[数据差异说明](https://support.google.com/webmasters/answer/17010575)）。导出时 "~" 和 "-" 变成 0（[报告概览](https://support.google.com/webmasters/answer/7576553)） |
| Search Console 网址检查 | 是否已编入索引、上次抓取时间、Google 选定的规范网址 | 显示的是最近编入索引的版本，不是实时版本（[网址检查](https://support.google.com/webmasters/answer/9012289)） |
| GA4 着陆页数据 | 自然搜索带来的访问和转化是否同步下降 | GA4 的互动率与跳出率互为反面；互动会话指持续 ≥10 秒、或有关键事件、或有 ≥2 次网页浏览的会话（[GA 帮助](https://support.google.com/analytics/answer/13682863)） |
| 爬虫导出 | 失效链接、重定向链、noindex、canonical 变化 | `scripts/site_crawl.py` 或你自选的工具 |
| 排名追踪（可选） | 固定查询的排名走势和 SERP 模块变化 | 你自有或自选的数据源 |

页面维度把点击记在 Google 选定的规范网址上（[维度说明](https://support.google.com/webmasters/answer/17011259)）。规范网址变了，点击会从一个 URL 挪到另一个 URL，看起来像衰退。Search Console 效果数据的保留期见[事实表](../overview/facts.md#gsc-retention)，同比最多回看一年。

## 先排除非内容原因

按顺序检查，任何一项成立，都先处理它，不要急着改内容：

1. **测量问题**：统计代码、同意横幅、GA4 配置、过滤条件最近有没有改动。
2. **技术问题**：页面是否仍被编入索引；有没有误加 `noindex`、canonical 被改、重定向变化、服务器错误、渲染失败、内链被删、站点改版或迁移。
3. **需求变化**：查询的展示整体下降，而排名没变，说明是需求下降或季节性。用同比，不只用环比。
4. **SERP 变化**：排名稳定、展示稳定、点击率下降，常见原因是 SERP 上新增了 AI 概览、视频、购物等模块，或者竞争页面的标题更吸引人。
5. **Google 更新**：下滑时间是否与[搜索状态面板](https://status.search.google.com/)公布的排名更新吻合。面板列出与站长相关的最新排名更新，历史记录保留 5 年（[面板说明](https://developers.google.com/search/help/status-dashboard)）。吻合只说明值得对照，不等于因果。

整站或整个目录同时下滑，通常是技术问题、测量问题或算法更新，不是单篇内容衰退。

## 衰退信号

**表现类**（来自 Search Console，判据见下节公式）：

- 点击持续下降，超出这个页面自己以往的正常波动范围。
- 平均排名变差，展示随之下降。
- 原先带来点击的主要查询消失，或者被站内另一个页面取代（互相抢位，见 [topic-cluster-templates.md](../research/topic-cluster-templates.md)）。
- 排名不变而点击率下降：先看 SERP 和标题，见 [title-formulas.md](title-formulas.md)。

**内容类**（人工或爬虫检查）：过时的年份、统计、价格、截图、界面描述；提到已下线的产品或功能；给出的做法已被官方文档推翻；外部链接失效。

**竞争类**：新的页面排到你前面，它们回答得更完整、更新或有一手证据；SERP 前列的页面类型变了（例如从教程变成工具页），说明意图漂移。

**辅助类**：自然搜索访问的转化或互动下降；重要外链丢失。单独出现不能确认衰退，只作佐证。

## 衰退判据：用 GSC 导出算

以下阈值都是**本套件口径**（`gsc_mining.py` 与 `content_queue.py` 用同一组数），不是 Google 的规则。站点有足够历史时，用第 3 步的自身波动替代固定阈值。

**1. 准备两份导出。** 同一维度（查询或页面）、同一搜索类型和国家／设备筛选、等长窗口。窗口用整周（Search Console 的周是周日到周六；Google 建议比较日期范围时用周或月粒度，抵消星期效应，见[筛选与比较](https://support.google.com/webmasters/answer/17011165)），结束日至少在 3 天前。常用：最近 28 天对前 28 天，再加去年同期 28 天做同比。

**2. 逐行计算。** 记本期点击、展示、点击率、排名为 C1、I1、CTR1、P1，上期为 C0、I0、CTR0、P0：

- 点击变化 ΔC = (C1 − C0) / C0，只算 C0 ≥ 10 的行；**ΔC ≤ −25% 进候选**。
- 展示变化 ΔI = I1 / I0 − 1；排名变化 ΔP = P1 − P0（正数表示变差）；点击率变化 ΔCTR = CTR1 / CTR0 − 1。
- 分型（本套件口径）：
  - **需求下降**：ΔI ≤ −25% 且 |ΔP| < 1。再看同比；去年同期也降，判季节性。
  - **SERP 或标题问题**：|ΔI| < 10%、|ΔP| < 1、ΔCTR ≤ −25%。
  - **排名下降**：ΔP ≥ 1 且 ΔI < 0。排除技术原因后，才算内容衰退候选。
  - **流失**：上期 C0 ≥ 10，本期导出里没有这一行。
  - **被替代**：同一查询改由站内另一个 URL 承接（用查询×页面导出查）。
- 比较模式导出里，罕见行可能显示 "~"，导出为 0。0 不一定是真的零，不要据此判「降到 0」。
- **数据异常期。** Search Console 公告过一次日志错误：一段时间内的展示、点击率和平均排名记录不准，点击不受影响，已修复（起止日期见[GSC 数据异常期](../overview/facts.md#gsc-anomaly)）。所以跨这个期间的 ΔI、ΔCTR、ΔP 不可比，只有 ΔC（点击）可信；要做同比，去年同期正好落在异常期内时，展示类分型改用点击和站内 GA4 自然会话交叉判断。

**3. 单页确认（自身波动）。** 在效果报告里按页面筛选，导出「日期」表，按周汇总点击。取下滑前 12 周的均值 μ 和标准差 σ；最近 4 周都低于 μ − 2σ，判为超出正常波动（本套件口径）。

**脚本现状**（读源码并用两份小 CSV 实跑，2026-10-21）：

- `python3 scripts/gsc_mining.py cur.csv prev.csv --decay [--json]`：只按查询比较点击，规则是上期 ≥10 次且降幅 ≤ −25%；本期消失的查询按 0 计，会列为 −100%；按流失点击取前 30 行；只认英文表头（Query／Top queries、Clicks）。本期有、上期没有的查询不进衰退表，也不再报错（10-21 实测）。
- `python3 scripts/content_queue.py collect --gsc cur.csv --gsc prev.csv`：同一衰退口径，但只统计两期都出现的查询，所以本期消失的查询不进队列；结果写进 `contentops.json` 的选题队列。要看流失查询，用上一条。
- `python3 scripts/gsc_mining.py matrix.csv --mode matrix`：查询×页面导出，列出同一查询有 2 个以上页面的组（抢位）。
- 页面级的 ΔI、ΔP、ΔCTR 分型和同比目前没有脚本，按上面公式在表格里算。

## 严重度

综合三个维度判断，阈值以站点自己的历史数据为准，不套行业平均数：

- **页面价值**：它带来的转化、在主题集群里的位置、外链数量。
- **偏离程度**：下降幅度相对于该页面正常波动的大小（上节第 3 步）。
- **范围和持续时间**：一个查询还是全部查询；一周还是持续数周。

| 等级 | 典型情况 | 处理 |
|---|---|---|
| 观察 | 价值一般的页面小幅下滑，或只持续了一两周 | 记入候选表，下个复查周期再算一次 |
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

- Google 把 301 当作「处理重定向目标」的强信号；除 429 外，所有 4xx 处理方式相同，已编入索引的 URL 返回 4xx 会被移出索引（[HTTP 状态码](https://developers.google.com/search/docs/crawling-indexing/http-network-errors)）。所以 404 和 410 对 Google 没有区别。
- 批量判桶用 `python3 scripts/content_inventory.py --crawl crawl.json --gsc pages.csv [--panel panel.json] [--backlinks links.csv]`：流量、外链、AI 引用、战略四轴，分 keep／update／consolidate／remove；被 AI 引用的页不进 remove 桶（本套件口径）。零点击页退役前再过 `python3 scripts/prune_gate.py --urls urls.txt --gsc queries.csv --crawl crawl.json --backlinks links.csv`：有外链或有排名 ≤20 的查询，判 NO-GO。
- 更新和重写的划分及执行清单见 [content-refresh-playbook.md](content-refresh-playbook.md)；状态码选择见 [http-status-codes.md](../technical/http-status-codes.md)。

## 更新之后

- **日期只在实质修改后更新。** Google 有用内容自查把「内容没有实质变化却改日期，让页面显得新」列为警示信号；同时说明，为了显得「新」而大量增删内容不会帮助排名（[有用内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)）。Google 新闻的规则更直接：没有新增重要信息或充分理由，人为刷新文章日期违反其指南（[新闻文章页最佳做法](https://support.google.com/news/publisher-center/answer/9607104)）。
- **可见日期与结构化数据一致。** 页面显示「发布于／最后更新」日期；用 `datePublished`、`dateModified` 标注；两者一致；不写未来日期（[署名日期](https://developers.google.com/search/docs/appearance/publication-dates)）。
- **`lastmod` 写真实的重大修改时间。** Google 只在 `lastmod` 一贯且可核实地准确时使用它（[构建站点地图](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)）。改了正文、结构化数据或链接要更新 `lastmod`；只改侧栏或页脚不用更新；长期乱写，Google 会不再相信这个站的 `lastmod`（[Search Central 博客 2023-06-26](https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping)）。
- **复查从重新抓取算起。** 用网址检查确认「抓取」一栏的时间晚于修改时间；再拿修改后的完整 4 周与修改前 4 周比较（本套件口径）。不承诺固定的恢复周期或恢复比例。
- 一次只发一批改动，等这批的结果算完再发下一批，否则无法判断哪一项起了作用。

## 检查清单

1. **非内容原因已排除** → 网址检查（编入索引、canonical、抓取时间）+ `scripts/site_crawl.py` 爬虫导出 + 状态面板历史页 → 通过：五项（测量、技术、需求、SERP、更新）逐条有结论；失败：有一项没查就改内容。
2. **衰退候选按公式算出** → `content_queue.py collect --gsc cur.csv --gsc prev.csv`（查询级），页面级按「衰退判据」公式 → 通过：每个候选有 C0、C1、ΔC、ΔI、ΔP 和分型；失败：只凭「流量掉了」下结论。
3. **季节性已排除** → 去年同期 28 天导出，同口径算 ΔI → 通过：有同比数字，且比较窗口没有跨[GSC 数据异常期](../overview/facts.md#gsc-anomaly)（展示类指标不可比）；失败：只有环比，或跨了异常期还在比展示。
4. **单页超出自身波动** → 按页面导出「日期」表，算 μ − 2σ → 通过：最近 4 周都低于下限；失败：仍在正常波动内。
5. **抢位已检查** → `gsc_mining.py matrix.csv --mode matrix` → 通过：候选查询没有被站内别的 URL 承接，或已列入合并计划；失败：没查。
6. **处置有依据** → `content_inventory.py`、`prune_gate.py` 的输出 + 上表 → 通过：每页一个决定和理由；下线页有重定向映射或 404/410；失败：有外链或有排名的页被直接下线。
7. **日期与 `lastmod` 合规** → 对照修改记录查页面可见日期、`dateModified`、站点地图 `lastmod` → 通过：三者都等于最近一次实质修改日期；失败：只改日期没改内容，或三者不一致。

## 交付物

每个候选页面一行：

| 页面 | 观察到的信号（含 ΔC/ΔI/ΔP） | 已排除的原因 | 严重度 | 决定 | 理由 | 复查起点 |
|---|---|---|---|---|---|---|

另附：需要先修的技术或测量问题清单，以及合并和下线页面的重定向映射表。

## 常见误区

- 一看到流量下降就改内容，没先排查技术、测量和季节因素。
- 只改日期不改内容。
- 用通用的「各排名位置点击率」表判断自己页面是否异常。
- 把 SERP 模块变化造成的点击下降，当成内容质量问题来重写。
- 把比较模式导出里的 0（原来是 "~"）当成真的零。
- 一次改动太多，无法判断哪一项起了作用。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。核对日期均为 2026-10-21。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/content-refresher/references/content-decay-signals.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/optimize/content-refresher/references/content-decay-signals.md)（Apache-2.0）
- Google 一手资料：[效果报告概览](https://support.google.com/webmasters/answer/7576553)、[维度与分组](https://support.google.com/webmasters/answer/17011259)、[筛选与比较](https://support.google.com/webmasters/answer/17011165)、[数据差异](https://support.google.com/webmasters/answer/17010575)、[网址检查](https://support.google.com/webmasters/answer/9012289)、[搜索状态面板说明](https://developers.google.com/search/help/status-dashboard)、[有用内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[署名日期](https://developers.google.com/search/docs/appearance/publication-dates)、[新闻文章页最佳做法](https://support.google.com/news/publisher-center/answer/9607104)、[构建站点地图](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)、[lastmod 说明](https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping)、[HTTP 状态码](https://developers.google.com/search/docs/crawling-indexing/http-network-errors)、[重定向](https://developers.google.com/search/docs/crawling-indexing/301-redirects)、[GA 中的 Search Console 报告](https://support.google.com/analytics/answer/13682863)
