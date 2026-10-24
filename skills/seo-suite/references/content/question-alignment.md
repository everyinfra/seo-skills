# 提问对齐：title、H1、首段回答买家的原话

> 用途：给已有展示、点击少的页面改写 title、H1、首段和 meta description；给新页面定标题和首段。
> 前提：有 Search Console 或 Bing Webmaster Tools 的数据，或有工单原话。
> 边界：本方法管搜索结果页的点击和页面名实相符。它对 AI 引用有没有作用，按 [geo-evidence.md](geo-evidence.md) 的证据分级判断，本文件不承诺。
> 文中的阈值，除注明出处的以外，都是本套件口径。各站可以改，改了要写下来。

## 一、是什么

页面的四个位置用买家提问的原词。首段第一句直接回答。

| 位置 | 要求 |
|---|---|
| title | 含买家提问的核心词。读完就知道这页回答什么。 |
| H1 | 与 title 意思一致。是页面上最醒目的标题。 |
| 首段第一句 | 直接给答案：数字、是或否、定义、第一步、价格口径。第二句起写条件和例外。 |
| meta description | 一两句。概括答案和适用条件，含买家原词。 |

为什么这样做（一手来源，核对 2026-10-18）：

- Search Console 帮助说明：查询维度可以用来找「展示多、CTR 低」的查询，这是改进页面标题和描述的机会（[维度说明](https://support.google.com/webmasters/answer/17011259)）。低 CTR 可能说明用户看到了页面，但不认为它回答了查询；可以更新标题和描述，或调整内容去对齐这些查询（[常见任务](https://support.google.com/webmasters/answer/17010961)）。
- Google 标题链接文档说明：标题链接常常是用户决定点哪个结果的主要依据（[标题链接](https://developers.google.com/search/docs/appearance/title-link)）。
- Google 摘要文档说明：摘要主要从页面正文生成，突出与这次搜索最相关的内容；同一页对不同搜索可能显示不同摘要；meta description 比正文更准确时，才可能被采用（[摘要](https://developers.google.com/search/docs/appearance/snippet)）。
- Bing 网站管理员指南第 17、18 条：标题、标题层级和内容意图保持一致；关键信息放在页面靠前位置，不在进入主题前写长引言（[Bing 指南](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)）。

它不是什么：

- 不是为了让 Google「匹配上」。Google SEO 入门指南说明，它的语言匹配系统能理解页面和查询的关系，即使页面没有逐字使用查询词（[入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)「Expect your readers' search terms」，核对 2026-10-18）。提问对齐的目的是：买家在结果页认出自己的问题，点进来后第一句就拿到答案。
- 不是堆词。一个 title 只对齐一组同义提问。

## 二、提问从哪来

### 1. Search Console：查询 × 页面（主来源）

同一个窗口取两张表：页面级表（每页的总展示，含匿名查询）和查询 × 页面表（每页的可见查询）。三种取法任选一种。

**A. 网页界面**（每张表最多 1,000 行）

1. 打开 Performance → Search results。
2. 日期选 Last 28 days。搜索类型保持 Web。
3. 点 + Add filter → Page → Custom (regex)，填 `^https://example\.com/guide/export$` 锁定一页。正则用 RE2 语法，默认部分匹配、不区分大小写，所以用 `^` 和 `$` 锁住整条 URL。
4. 切到 Queries 标签，点 Impressions 列按降序排。
5. 点 Export → Download CSV。压缩包里每个维度一个 CSV。查询表是 `Queries.csv`，筛选条件记在 `Filters.csv`。
6. `Queries.csv` 的首列名是 `Top queries`，CTR 写成 `3.1%`，并且没有页面列。喂给脚本前，加一列 `Page`，填这一页的 URL。

出处：表格行数上限、匿名查询、RE2 正则见 [数据差异说明](https://support.google.com/webmasters/answer/17010575) 与 [过滤和对比](https://support.google.com/webmasters/answer/17011165)（官方，核对 2026-10-18）。压缩包文件名见 John Mueller 的个人博客[示例](https://johnmu.com/static-site-move-check/)（2021）；`Top queries` 列名来自第三方工具说明（例：[CTR Gap Estimator](https://www.ramkrshukla.com/seo-tools/ctr-gap-estimator/)），未见官方文档。非英文界面导出的表头可能是本地化文字（本套件未核），把界面语言切到英文再导出，或改用 API。

**B. API**（推荐，行数多）

```bash
python3 scripts/gsc_api.py query --site sc-domain:example.com \
  --start 2026-09-14 --end 2026-10-11 --dimensions page --out pages.csv
python3 scripts/gsc_api.py query --site sc-domain:example.com \
  --start 2026-09-14 --end 2026-10-11 --dimensions query,page --rows 100000 --out qp.csv
```

- 两条命令的窗口都是 28 天。输出列：`Query,Page,Clicks,Impressions,CTR,Position`，CTR 是小数。
- API 每次请求有行数上限（[配额表](../overview/facts.md#api-quotas)）；脚本用 startRow 分页，`--rows` 是总行数上限（默认取单次上限）。
- API 只返回排在前面的行，不保证全量；匿名查询不返回（[Search Analytics API](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)，核对 2026-10-18）。
- 结束日至少留 3 天：数据通常 2–3 天后可用。日期按太平洋时间计（[数据差异说明](https://support.google.com/webmasters/answer/17010575)）。

**C. BigQuery 批量导出**（行最全）

表 `searchdata_url_impression` 有 `query`、`url`、`impressions`、`clicks`、`sum_position` 等列。平均排名 = `SUM(sum_position) / SUM(impressions) + 1`（`sum_position` 从 0 起算）。`is_anonymized_query` 为真的行没有查询文字（[表结构](https://support.google.com/webmasters/answer/12917991)，核对 2026-10-18）。

```sql
SELECT query, url AS page, SUM(clicks) AS clicks, SUM(impressions) AS impressions,
       SUM(sum_position) / SUM(impressions) + 1 AS position
FROM `PROJECT.searchconsole.searchdata_url_impression`
WHERE data_date BETWEEN '2026-09-14' AND '2026-10-11'
  AND search_type = 'web' AND NOT is_anonymized_query
GROUP BY query, page
```

**拿到表后先跑现有脚本**

- 蚕食：`python3 scripts/gsc_mining.py qp.csv --mode matrix --json` 列出同一查询有 ≥ 2 个页面的组。先定这个查询归哪一页，再改写。不要让两页的 title 对齐同一个提问。
- 差一点进前排：`python3 scripts/gsc_mining.py queries.csv --brand 'examplebrand' --json`（单表：首列 `Query` 或 `Top queries`，加 Clicks,Impressions,CTR,Position）输出 striking distance（排名 5–20、展示 ≥ 20）和低 CTR（排名 1–10、展示 ≥ 50、低于脚本内置期望 CTR 曲线 2 个百分点以上）。`--brand` 命中的查询不参与挖掘。这些门槛和曲线是本套件口径，只用来排序；以 `--help` 为准。

### 2. Bing Webmaster Tools

- 界面：Search Performance → Pages → 点一个页面，看它的 Keywords；或 Keywords → 点一个词，看对应页面。Download 导出 CSV（[Bing 帮助](https://www.bing.com/webmasters/help/search-performance-c680da36)，核对 2026-10-18）。
- 数据从站点加入 Bing Webmaster Tools 那天开始累计，不回填。关键词和页面数据只含网页结果。历史最长 16 个月（[Bing 博客 2024-10-16](https://blogs.bing.com/webmaster/2024/10/Bing-Webmaster-Tools-Extends-Search-Performance-Data-to-16-Months/)）。
- 口径不同：Bing 一次搜索里同站多个页面各算一次展示；Google 的查询表按资源汇总。两家的数字不相加，只各看各的排序。
- 脚本：`python3 scripts/bing_wmt.py stats --site example.com --out bing-q.csv` 拉站点级查询（Date,Query,Clicks,Impressions,CTR,Position），没有页面列。页面级查询要用 API 方法 `GetPageQueryStats`（[Microsoft 文档](https://learn.microsoft.com/en-us/dotnet/api/microsoft.bing.webmaster.api.interfaces.iwebmasterapi.getpagequerystats?view=bing-webmaster-dotnet)：数据每周更新）。本套件脚本还没有实现它。

### 3. 工单和客服原话

1. 导出最近 90 天的工单标题和客户的第一条消息。
2. 删掉姓名、邮箱、电话、订单号等个人信息，再交给任何工具。
3. 只留客户的问句和要做的事。保留原词，包括口语、缩写和常见错拼。
4. 按「客户要完成什么」归类。每类记条数和 3 条原话。
5. 给每类找承接页。已有页面进改写清单；没有页面进选题清单。

不要改成内部术语。客户写「发票抬头怎么改」，页面就不要写「开票主体信息维护」。

### 4. 「其他人还问了」和论坛

- 「其他人还问了」：Google 文档称它为相关问题组（People Also Ask），精选摘要也会出现在里面（[精选摘要](https://developers.google.com/search/docs/appearance/featured-snippets)，核对 2026-10-18）。在目标市场、目标语言下用无痕窗口搜主查询。记下问题原文、日期、地区和设备。结果随时间、地点和设备变化，所以每条都带日期。
- 论坛：在目标市场的社区搜主题，例如 Reddit、Stack Overflow、知乎、Yahoo!知恵袋、Naver 知识iN。记下问题标题原文、日期和回复数。
- 用法：这两类来源没有展示数据。只用来起草新页面和补 H2，不进第三节的选页。
- **匿名查询多的页靠它补提问来源。** 页面被 `question_align.py` 标 `anonymized`（可见查询的展示不到页面展示的 20%）时，剩下的可见查询不能代表买家在问什么。用这一页的主题词搜索，记下结果页「相关搜索」和「其他人还问了」的原文、日期、地区和设备，再加上工单原话，作为改写依据。本套件实测（2026-10，一个真实的 API 站，不具名）：28 天展示 ≥ 20、点击为 0 的 27 页里，18 页的可见查询不到页面展示的 20%；Bing 的 `GetPageQueryStats` 对这些页返回空。

## 三、选页规则

| 参数 | 默认值 | 脚本参数 | 说明 |
|---|---|---|---|
| 窗口 | 28 天 | 导出时定 | 4 个完整周，前后两期的周几构成相同 |
| 页面展示下限 | 20 | `--min-impressions 20` | 只是候选门槛，不是结论 |
| 页面点击上限 | 0 | `--max-clicks 0` | 「展示多、点击 0」 |
| 平均排名 | ≤ 10 以标题为主 | `--max-position 10` | 超过的页标 `rank_first`：先查排名和内容 |
| 品牌词 | 排除 | `--brand 'examplebrand'` | 品牌导航词不代表买家提问；多个品牌写成一个正则 |
| 期望点击 | ≥ 3 | 看输出的 `expected_clicks`（脚本只报告，不过滤） | 见下 |
| 能读出提问 | 是 | 人工复核 | 见下 |

**期望点击复核**

- 期望点击 = 页面展示 × 本站同排名段的 CTR。按页面的平均排名选段。
- 本站分段 CTR：按排名分段（1–3、4–6、7–10、11–20、21+），每段的点击之和 ÷ 展示之和。`question_align.py` 用页面级表（`--pages`）算；给了 `--brand` 时，可见查询里品牌词展示 ≥ 50% 的页不进基线；各段 CTR 在报告头部 `site_ctr_by_position` 列出。网页界面也可以用 Query 过滤器里的 Non-branded（2025-03-11 起提供；低展示站点和子资源不可用，[常见任务](https://support.google.com/webmasters/answer/17010961)）。
- 期望点击 ≥ 3 而实际点击为 0，才算「展示多、点击 0」。理由：点击数近似泊松分布，期望为 λ 时零点击的概率是 e^−λ；λ = 3 时约 5%。λ < 3 时，零点击可能只是样本小。
- 不套第三方 CTR 曲线。各家差别很大，还随结果页的 AI 答案变化（第三方研究，核对 2026-10-18）：
  - [Backlinko](https://backlinko.com/google-ctr-stats) 2019 年发布（约 400 万条结果，1,312,881 个页面、12,166,560 个查询）：第 1 名平均 CTR 27.6%。
  - [First Page Sage](https://firstpagesage.com/reports/google-click-through-rates-ctrs-by-ranking-position/) 2026-09 版（供应商数据，1,184 个域名，2026-03 至 2026-08，按美国加权）：第 1 名混合 CTR 7.1%；有 AI 答案的结果页 3.6%，没有的 22.6%。该报告称其 2025 年版是 39.8%。

**能读出提问**

- 查询里能看出买家要的答案或要做的事。问句词：怎么、如何、为什么、多少钱、哪个、能不能；how、what、why、which、can、does。任务词：价格、对比、替代、教程、下载、API、报错原文。
- 在 Search Console 里先用正则筛：+ Add filter → Query → Custom (regex)。例如 `^(how|what|why|which|can|does|is)\b|\?`，或 `怎么|如何|为什么|多少钱|哪个|能不能|吗$`。
- 只有一个品类词、读不出意图的查询，不进改写清单。先做意图判定，见 [keyword-intent-taxonomy.md](../research/keyword-intent-taxonomy.md)。

**多语言**

- 每种语言单独取数、单独选页。按 URL 语言目录过滤（例如只取 `/es/` 下的页面），或按国家过滤。
- 每种语言用本语言的查询原词写。不把英文查询翻成别的语言来用：翻出来的词常常不是当地人搜的词。
- title 用页面正文的语言和文字。不一致时，Google 可能改用别的文字作标题链接（[标题链接](https://developers.google.com/search/docs/appearance/title-link)）。
- 脚本的词覆盖目前只切拉丁字母、西里尔字母和汉字（以 `--help` 为准）。日文假名、韩文、泰文、阿拉伯文、天城文的覆盖率不可信，改用人工核对。

**排序**：按「错过的点击」= 期望点击 − 实际点击，从大到小改。

## 四、改写规则

1. **用买家原词**。title 和 H1 含查询的核心词，原样或按自然语序。首段第一句复述他问的对象。
2. **回答他问的那件事**。首段第一句给答案，第二句起写条件和例外。不用背景、口号或自我介绍开头。
3. **名实相符**。产品或接口做不到的，不写进 title、H1 和首段。逐项对照产品文档或接口契约核对。
4. **只改文案，不改事实**。改写不新增未核实的数字、承诺和对比结论。
5. **守住 Google 标题链接文档的三条**（[标题链接](https://developers.google.com/search/docs/appearance/title-link)，核对 2026-10-18；完整写法见 [title-formulas.md](title-formulas.md)）：
   - 不堆词。几个描述词可以，同一个词或短语不重复。把查询的几种变体全塞进 title 就是堆砌。
   - 品牌名简短，放在开头或结尾，用连字符、冒号或竖线隔开。本套件口径：买家原词放在品牌名前面。
   - 预期会被改写。标题链接的来源还有主视觉标题、`<h1>`、`og:title`、醒目文字、正文和锚文本等；改动要等重新抓取，需要几天到几周。被改写时，先查文档列的常见问题（半空、过时、不准确、模板重复、没有清楚的主标题、语言不一致、重复站点名）。都没有，就看 Google 显示的标题是否更贴近查询。
6. **title、H1 和正文用同一种语言和文字**。不一致时，Google 可能改用别的文字作标题链接。
7. **一页只对齐一组同义提问**。意图不同的提问分页承接，不把几个问题塞进一个 title。
8. **meta description**：一两句，概括答案和条件，含原词。Google 主要从正文生成摘要，所以首段比 description 更关键。写法见 [meta-tag-formulas.md](meta-tag-formulas.md)。

**示例（虚构站点，事实取自该站的产品文档）**

| 位置 | 改前 | 改后 |
|---|---|---|
| 主查询 | `examplecrm export contacts csv`（28 天展示 640，点击 0，排名 6.8） | — |
| title | Data Portability \| ExampleCRM | Export Contacts to CSV \| ExampleCRM |
| H1 | Your data, your rules | Export contacts to a CSV file |
| 首段 | At ExampleCRM, we believe your data belongs to you. | Go to Contacts → Export, choose CSV, and click Download. The file has all contact fields except attachments. |

| 位置 | 改前 | 改后 |
|---|---|---|
| 主查询 | `发票抬头怎么改`（来自工单原话） | — |
| title | 账户设置 \| 示例云 | 发票抬头怎么改：在账户设置里修改 \| 示例云 |
| 首段 | 示例云致力于为企业提供一站式服务。 | 在「账户设置 → 发票信息」里修改发票抬头。修改只对之后开具的发票生效。 |

## 五、判据与测量

**动手前写下**（看到结果前定好，不事后改）：

1. 改写页清单和改写日期。
2. 每页基线：改前 28 天的展示、点击、CTR、平均排名（页面级表）。
3. 对照页：同类、同期不改的页，模板相同、排名段相近。
4. 通过标准。下面是模板，X、Y、Z 是业务阈值，由各站自己定，本套件不给默认数字：
   - 改写页合计 CTR ≥ 基线 × (1 + X)。
   - 改写页合计展示 ≥ 基线 × Y。防止换词后丢掉原来的查询。
   - 基线里期望点击 ≥ 3 的页，每页点击 ≥ 1。
   - 对照页同期 CTR 变化在 ±Z 以内。超出说明有季节或算法因素，改用差分比较，或判结论无效。

**改后怎么量**

1. 先查 Search Console 的[已知数据异常](https://support.google.com/webmasters/answer/6211453)。两期窗口都不能跨过异常期。例：[GSC 数据异常期](../overview/facts.md#gsc-anomaly)里展示、CTR 和平均排名受日志错误影响，点击不受影响。
2. 确认 Google 已显示新标题：搜目标查询看结果；或在网址检查里看 Last crawl 晚于改写日期（[网址检查](https://support.google.com/webmasters/answer/9012289)）。
3. 从新标题显示那天起，取同样长度的窗口（28 天）。Google 入门指南也建议等几周再评估（[入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)）。
4. 在效果报告的图表上加自定义注解，记改写日期。每个资源最多 200 条，每条最多 120 个字符；对比模式里不显示注解（[注解](https://support.google.com/webmasters/answer/16530728)，核对 2026-10-18）。
5. 比较两期：效果报告用 Compare 对比两个日期范围，可切到 Weekly 消除周几差异（[过滤和对比](https://support.google.com/webmasters/answer/17011165)）。或用 API 导出两期页面级表（`--dimensions page,date`），跑 `python3 scripts/did_attribution.py --treated-page <处理组 URL 前缀> --control-page <对照组 URL 前缀> --pre pre.csv --post post.csv`。
6. 做位置校正。排名变了，CTR 自然会变。比较「实际点击 ÷ 期望点击」（期望点击用改前的本站分段 CTR 算），比直接比 CTR 稳。
7. 同模板的页面多时，做页面级随机实验：`python3 scripts/split_test.py plan` 算样本量，`assign` 分组，`analyze` 判读。
8. 单页期望点击 < 3 时不单独下结论，按组合计。

**展示掉了，按这个顺序查**

1. 先看平均排名。排名掉了，问题不在标题，按排名下滑排查。
2. 再看查询构成。这一页的查询变少了，说明新标题丢了原来的词。
3. 最后看标题是否被改写。搜目标查询，对照结果里显示的标题链接。

## 六、检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 数据窗口 | 看导出的日期范围 | 通过：28 天，前后两期等长。失败：窗口不等长或含未完成的日期 |
| 数据异常 | 对照 Search Console「数据异常」页 | 通过：两期都不跨异常期。失败：跨了还比较展示、CTR 或排名 |
| 页面总展示来源 | 有没有页面级表 | 通过：用页面级表。失败：只用查询 × 页面表求和（漏掉匿名查询） |
| 零点击够不够样本 | `question_align.py` 的 `expected_clicks`（= 展示 × 本站分段 CTR） | 通过：≥ 3。失败：< 3 仍据此改写 |
| 匿名查询多的页 | `question_align.py` 的 `anonymized` 标签（可见查询展示 ÷ 页面展示 < 20%） | 通过：提问来源换成结果页「相关搜索」「其他人还问了」和工单原话，并注明日期。失败：拿剩下的可见查询判断覆盖 |
| 能读出提问 | 读主查询原文 | 通过：能说出买家要什么。失败：只有品类词或品牌词 |
| 蚕食 | `gsc_mining.py qp.csv --mode matrix --json` | 通过：这个查询只有一页去对齐。失败：两页 title 对齐同一提问 |
| title 含原词 | 对照主查询逐词看 | 通过：核心词都在。失败：只有同义改写或缺词 |
| H1 与 title 一致 | 浏览器看渲染后的第一个 `<h1>` | 通过：讲同一件事。失败：两件事，或页面上有两个同样醒目的标题 |
| 首段第一句是答案 | 读第一句 | 通过：含数字、是或否、定义、第一步或价格口径。失败：背景、口号、自我介绍 |
| meta description | 看渲染后的 `<head>` | 通过：一两句，含原词并概括答案。失败：缺失、全站同一句、堆词 |
| 名实相符 | 对照产品文档、接口契约 | 通过：每个承诺都能在产品里做到。失败：有做不到的承诺 |
| 不堆词 | 数 title 里每个词的出现次数 | 通过：除品牌名外每个词最多 1 次（本套件口径）。失败：重复 |
| 每页唯一 | `site_audit.py URL1 URL2 … --json > audit.json`，再 `health_score.py --input audit.json --json` | 通过：没有 `duplicate_title`。失败：有 |
| 语言 | 每个语言版本对照该语言的查询 | 通过：按本语言查询写。失败：从别的语言直译 |
| 新标题已生效 | 搜目标查询；看网址检查的 Last crawl | 通过：已显示或已重新抓取，才开始计窗口。失败：没生效就开始计 |
| 判据先写 | 看改写前的记录 | 通过：通过标准、对照页在改写前写好。失败：看到结果再定 |

## 七、和其他文件的关系

- [title-formulas.md](title-formulas.md)：title 的结构、长度和被改写的处理。本文件决定 title 里用哪些词。
- [meta-tag-formulas.md](meta-tag-formulas.md)：meta description 和 `<head>` 其他标签的写法。
- [geo-evidence.md](geo-evidence.md)：凡涉及 AI 引用的判断，以它为准。
- [content-structure-templates.md](content-structure-templates.md) 与 [content-patterns.md](content-patterns.md)：首段之后的页面结构和内容块。
- [keyword-intent-taxonomy.md](../research/keyword-intent-taxonomy.md)：读不出意图的查询先在这里判定。

## 八、脚本：question_align.py 的输入输出约定

已实现：`scripts/question_align.py`，测试 `tests/test_question_align.py`，已登记能力矩阵。参数以 `python3 scripts/question_align.py --help` 为准；本节与 `--help` 不一致时，以 `--help` 为准。

**输入**

- `--gsc FILE`（必填）：查询 × 页面 CSV。列名不区分大小写，接受三种来源：
  - `gsc_api.py` 的规范化输出：`Query,Page,Clicks,Impressions,CTR,Position`，CTR 是小数。
  - 网页导出：查询列 `Top queries`、页面列 `Top pages`，CTR 写成 `3.1%`。真实导出里这两列不在同一个文件；按页导出的 `Queries.csv` 要手工补一列 `Page`。
  - BigQuery：按第二节的 SQL 导出 `query,page,clicks,impressions,position`。
- `--pages FILE`（建议给）：页面级 CSV，来自 `gsc_api.py query --dimensions page`。查询 × 页面表不含匿名查询，只有页面级表有真实的页面总展示。
- `--page URL`：单页网页导出（`Queries.csv` 没有页面列）时，所有行记到这个 URL。既没给 `--page`、文件里又没有页面列时，报错退出，退出码 2。
- 选页参数：`--min-impressions N`（默认 20）、`--max-clicks N`（默认 0）、`--max-position P`（默认 10）、`--brand REGEX`、`--top-queries N`（每页列出的查询数，默认 5）。
- 页面内容：`--fetch` 抓线上页面，或 `--html-dir DIR` 读离线 HTML（文件名 = URL 的 sha1 前 16 位 + `.html`）。两者只能选一个。
- `--json`：结构化输出，`schema_version` 为 1。

**输出（每个候选页一条）**

- 数据：`page`、`impressions`、`clicks`、`ctr`、`position`、`visible_query_impressions`、`anonymized_share`（= 1 − 可见查询展示 ÷ 页面展示）、`expected_clicks`（= 页面展示 × 本站同排名段 CTR，供第三节复核）。
- 查询：`queries` 列出展示最多的 N 个查询，每个带 `impressions`、`clicks`、`position`。抓到页面时再带词覆盖率 `cov_title`、`cov_h1`、`cov_lead`（0–1；lead 指首段加 meta description），以及 `missing_terms`：title、h1、lead 各缺哪些查询词。这是改写素材；脚本不生成改写文案，文案由人按第四节写，避免编造事实。
- 页面文字：`title`、`h1`、`description`、`lead`。
- 标签 `flags`：`rank_first`（排名 > P）、`anonymized`（可见查询展示不到页面展示的 20%，或没有可见查询）、`title_gap`（主查询在 title 的覆盖率 < 0.5）、`lead_gap`（在首段加 description 的覆盖率 < 0.5）、`aligned`（两者都 ≥ 0.8 仍零点击，去看结果页）、`no_fetch`（没有页面内容）。主查询指展示最多的可见查询。
- 两条判定口径（本套件口径）：
  - `anonymized` 的页不打 `title_gap`、`lead_gap`、`aligned`：可见查询太少，覆盖率没有代表性。这类页的提问来源按第二节第 4 小节补。
  - 主查询展示 < 3 时不判覆盖：1–2 次展示没有代表性。
- 报告头部：`site_ctr_by_position`（各排名段的本站 CTR，段为 1–3、4–6、7–10、11–20、21+）和 `ctr_baseline_excluded_brand_pages`（因品牌词被剔出基线的页数）。
- 汇总 `summary`。退出码：0 正常，2 输入错误（文件缺失、列名不认识、参数不合法）。
- 测试的期望值来自去标识的真实 GSC 导出样例和本文件引用的官方定义，不来自读实现。

## 来源

本文由 EveryInfra 编写。一手资料均于 2026-10-18 打开核对，链接见正文。第三方资料已在正文标注：Backlinko 与 First Page Sage 的 CTR 研究、John Mueller 个人博客（导出文件名）、第三方工具说明（`Top queries` 列名，例：[CTR Gap Estimator](https://www.ramkrshukla.com/seo-tools/ctr-gap-estimator/)）。
