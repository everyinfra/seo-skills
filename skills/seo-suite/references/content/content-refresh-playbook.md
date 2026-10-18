# Content Refresh Playbook

> 复核于 2026-10-18：Google 文档逐条核对；第三方工具口径（seomachine）按源码核对后降级为参考；写法要求与 [asd-ste100-web-writing.md](asd-ste100-web-writing.md) 对齐。

## 适用场景

- 旧内容排名或点击下滑，且 [content-decay-signals.md](content-decay-signals.md) 已排除技术、测量和季节原因。
- 年份、统计、截图、工具信息过时。
- 竞品覆盖了新的子问题，你的页面没有。
- 需要保留 URL 已有的外链和排名积累。

信号怎么识别、衰退怎么用 GSC 导出计算，见 [content-decay-signals.md](content-decay-signals.md)。本文只管执行。

## 先判定是 refresh 还是 rewrite（本套件口径）

| 优先 refresh | 考虑 rewrite |
|---|---|
| URL 有外链或历史排名 | URL 几乎没有积累 |
| 搜索意图没变 | 搜索意图已变（SERP 前列的页面类型变了） |
| 原结构还能用 | 内容基础质量差 |
| 预计改动不到一半 | 预计要改动大半 |

「一半」是经验判断，不是硬线。

## Refresh 工作流

1. 确认技术问题已排除（decay-signals 第「先排除非内容原因」节）。
2. 记下衰退分型和数字（ΔC、ΔI、ΔP），决定 refresh／rewrite／consolidate／retire。
3. 列出要改的统计、段落、链接、截图、FAQ、结构化数据字段，每项写清旧值和新值的来源。
4. 一次只发一批改动。
5. 发布后按 decay-signals「更新之后」一节复查：先确认 Google 已重新抓取，再比较修改前后各 4 个整周。

## 刷新候选怎么来

用现有脚本出候选，不另起一套阈值。下表阈值都是脚本内置的**本套件口径**：

| 桶 | 判据 | 怎么跑 | 动作 |
|---|---|---|---|
| 衰退 | 上期点击 ≥10 且降幅 ≤ −25%（查询级） | `python3 scripts/content_queue.py collect --gsc cur.csv --gsc prev.csv` | 按 decay-signals 分型后再定 |
| 接近首页 | 排名 5–20 且展示 ≥20 | `python3 scripts/gsc_mining.py queries.csv --json`（`striking_distance`） | 补缺失的子问题、内链 |
| 低点击率 | 排名 11–20、展示 ≥50，且实际点击率比脚本内置期望曲线低 2 个百分点以上 | 同上（`low_ctr`） | 先改标题和描述 |
| 抢位 | 同一查询有 2 个以上页面 | `python3 scripts/gsc_mining.py matrix.csv --mode matrix` | 合并或调整内链 |

- 「低点击率」用的是脚本里写死的通用点击率曲线。decay-signals 把「用通用曲线判断自己页面」列为误区，所以这一桶只当候选。确认时用自己站点的数据：从 GSC 导出非品牌查询，按排名分档算点击率中位数，再比较。同一条自有曲线可以喂给 `python3 scripts/forecast.py --kws kws.csv --ctr own_ctr.csv` 估算收益。
- 错失点击估算（本套件口径）：展示 ×（自有曲线在该排名的点击率 − 实际点击率）。
- 先改标题和描述，是因为改动小、可以回滚（本套件口径），不是因为有证据证明它回报最高。Google 主要用页面正文生成摘要，只在 meta description 比正文更准确时才用它（[摘要文档](https://developers.google.com/search/docs/appearance/snippet)），所以改了描述也可能不显示。

## 刷新动作清单

- 只在内容确实更新时，才更新 title、H1 里的年份等时效词。
- 替换旧统计，同句写来源和日期。
- 补上竞品已覆盖、你缺失的子问题。只补读者需要的，不为凑字数扩写：Google 明确说没有偏好的字数（[有用内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)），生成式 AI 搜索也没有理想页长（[AI 功能优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)）。
- 更新内部链接。
- 补定义和能被单独摘出的结论句；FAQ 只写真实问答（见 [geo-evidence.md](geo-evidence.md)）。
- 有实质更新时同步 `dateModified` 和站点地图 `lastmod`；不要只改日期。Google 把「内容没有实质变化却改日期」和「为了显得新而大量增删内容」列为警示信号（[有用内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)）。

## 刷新时的写法要求

按 [asd-ste100-web-writing.md](asd-ste100-web-writing.md) 执行，替换旧版「刷新编辑八查」：

- 删空话和套话，见 [ai-writing-detection.md](ai-writing-detection.md)。
- 模糊词换成具体数据：many → 具体数量或百分比；often → 具体频率；various → 点名列举；significant → 具体幅度；good、bad → 具体收益或代价。
- 英文句长：程序句 ≤20 词，描述句 ≤25 词；描述段 ≤6 句，一段一个主题（STE 规则，出处见 STE 参考第二节）。
- 程序句全部用主动语态；描述句只在动作者未知时用被动。
- 接口文档和错误信息不用缩写形式（STE 4.2）；营销页可按品牌语气保留。
- 术语、产品名的写法和 [brand-records.md](brand-records.md) 的批准术语一致。

旧版八查来自 seomachine 的写作器源码（段落 ≤4 句、5–10 词短句配 15–25 词长句、补缩写形式、主动语态 ≥80%）。这些是该工具的设计，没有研究支持；其中「补缩写形式」和「主动语态 ≥80%」与 STE 冲突，本套件不再采用。

## 竞品字数只用来找缺口

seomachine 的字数对标器用前 10 名正文字数的中位数和 75 分位定「推荐字数」。本套件不把它当目标（Google 没有偏好字数，见上）。字数差距只提示「可能漏了子问题」：逐个比较竞品覆盖的子问题，缺的补上，多的不删。统计竞品字数时先定位正文（article、main、`[role=main]` 等），剥掉导航、页脚和侧栏，否则模板文字会污染统计。

## 质量门

- 事实核对：每个数字同句有来源和日期。`python3 scripts/market_lint.py --market en page.txt` 的「有源数字密度」一项：数字 ≥5 处且同句带来源线索的不到 30% 判 FAIL（本套件口径）。
- 内容评分：`python3 scripts/quality_rater.py page.md --market en`（六维）；有 3 个以上竞品正文时，再跑 `python3 scripts/content_score.py --draft page.md --competitors c1.md,c2.md,c3.md --keyword 主词`。分数只用来找问题，不当发布门槛的唯一依据。

## 输出要求

1. 衰退摘要（分型和数字）
2. refresh 或 rewrite 的决定与理由
3. 具体更新项清单（旧值、新值、来源）
4. 结构调整方案
5. 发布与重新抓取的确认方式
6. 复查起点和比较窗口

## 检查清单

1. **候选有数据** → `content_queue.py collect --gsc cur.csv --gsc prev.csv`、`gsc_mining.py queries.csv --json` → 通过：每个候选标明所在桶和数字；失败：凭感觉挑页面。
2. **低点击率已用自有曲线确认** → GSC 非品牌查询按排名分档算点击率中位数 → 通过：实际点击率低于自有曲线；失败：只看脚本内置曲线。
3. **每处修改有来源** → 更新项清单逐条核对 → 通过：每个新数字有来源 URL 和日期；失败：有无来源的数字。
4. **没有为字数扩写** → 对照竞品子问题清单 → 通过：新增段落都对应一个读者问题；失败：新增内容只为接近竞品字数。
5. **写法合规** → STE 参考第五节清单 → 通过：句长、段落、语态、术语四项无 FAIL；失败：有。
6. **日期与 `lastmod` 一致** → 页面可见日期、`dateModified`、站点地图 `lastmod` 对照修改记录 → 通过：三者等于这次实质修改的日期；失败：只改日期或三者不一致。
7. **复查起点正确** → 网址检查的抓取时间 → 通过：抓取时间晚于发布时间后才开始比较；失败：发布当天就比较。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。核对日期均为 2026-10-18。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/content-refresher](https://github.com/aaron-he-zhu/seo-geo-claude-skills/tree/v9.9.12/optimize/content-refresher)（Apache-2.0）
- 第三方工具源码（只作参考，不作规则）：[TheCraigHewitt/seomachine · data_sources/modules](https://github.com/TheCraigHewitt/seomachine/tree/main/data_sources/modules)（MIT；data_aggregator 的四桶、content_length_comparator 的中位数与 75 分位、content_scorer 的五维权重、section_writer 的写作规则）
- Google 一手资料：[有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[AI 功能优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)、[摘要](https://developers.google.com/search/docs/appearance/snippet)、[站点地图](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)
