# {答案式标题,例:"该页 6 项里 4 项在阈值内:真正压排名的是 H1 与搜索意图错位+零条上下文内链,改版预计 4 周见效"}

_For: {决策人} · Date: {YYYY-MM-DD} · Market: {目标市场/语言} · Render check: 浏览器渲染确认=是/否 · Data pulled: {日期+工具}_

> 多市场站点:逐市场各出一份本报告,不合并。市场差异规则见 references/overview/multilingual-workflow.md。
> 长度注记:Google 对 title 和 description 没有字符上限,只按设备宽度截断([title](https://developers.google.com/search/docs/appearance/title-link)、[snippet](https://developers.google.com/search/docs/appearance/snippet),核对 2026-10-21)。下面的数字是本套件提示阈值,单位随市场:en 等拉丁语 title 20–60、description 77–155 字符;zh 30/78 全角;ja 32/120 全角;ko 30/80 全角;de 65/150;ru 55/160;vi 65;th 按字素;id description 前 120 字符是安全区。真实值以 `site_audit.py --market XX --json` 顶层 `limits` 为准;完整表见 [title-formulas.md](../../references/content/title-formulas.md) 「市场差异」节。

## The answer

{一段独立成立:该页最关键的 1-2 个问题(按对排名/点击的影响排序)+ 量化(如 CTR 低于同位均值 x%)+ 置信度 + 建议先改什么。只读这段的人不会错。}

## Page

- URL:{} · Primary keyword:{} · Intent:{按 keyword-intent-taxonomy.md}
- 当前表现:排名 {} · 点击 {}/展示 {} · CTR {}%(GSC,近 28 天)

## Key numbers

| 指标 | 数值 | 对比/阈值 |
|---|---|---|
| 审计元素数 | {9} | |
| 达标项 / 越阈项 | {} / {} | 缺失类重于长度微调;长度越阈只复查截断后是否可读 |
| P0 修复项 | {} | 影响资格/理解 |
| CTR vs 同排名位基准 | {}% | 低 {} 个百分点则优先改 title/desc |

## Element Audit Table(逐元素审计)

每行:现状→阈值→Evidence→判定→Priority。Evidence 必须可复查(渲染后 DOM 摘录/截图/工具输出+抓取时间);**不得报告页面上不存在的信号**。

| Element | Current State(现状) | 阈值/规则 | Evidence | 判定 | Recommendation | Priority |
|---|---|---|---|---|---|---|
| Title | {原文} | 每页都有;描述本页、不堆词;长度见上方提示阈值;买家原词在内([question-alignment.md](../../references/content/question-alignment.md)) | {DOM 行+`site_audit.py` 的 `meta.title_len`} | 达标/缺失/越阈 |  | P0-P2 |
| Meta description | {原文或"缺失"} | 可选但建议写;每页不同,写本页独有信息;长度见上方(缺失在脚本里是 WARN,因为缺失时 Google 从正文取摘要) | {`meta.desc_len`} |  |  |  |
| H1 | {原文;是否含主词} | 本套件口径:一个最醒目的主标题,与 title 讲同一件事。Google 不要求单 H1([SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)),脚本把缺 H1 或多 H1 记 WARN | {`meta.h1` 数量} |  |  |  |
| Heading 结构 H2-H6 | {层级是否连续、问题式 H2} | 本套件口径:层级不跳号,方便读屏器和读者;Google 说标题的数量和顺序对搜索没有影响。H2 小标题覆盖买家真问的问题 | {`headings` 类发现} |  |  |  |
| 正文首屏 | {买家原词是否在首段、首段是否直接回答} | 意图匹配:SERP 主导形式对齐;首段直接回答([question_align.py](../../references/content/question-alignment.md)) | {`question_align.py` 覆盖率} |  |  |  |
| 内链(入/出) | {入 {} 条,上下文 {} 条} | 本套件口径:每页≥{} 条上下文内链;锚文本描述性。`site_audit.py` 只在总链接数 >100 时记 INFO(工具约定,非 Google 要求) | {GSC 链接报告+`site_crawl.py`+`link_graph.py`} |  |  |  |
| 图片 | {N 张,alt 缺 {} 张} | alt 描述内容;脚本在 alt 缺失 >20% 时记 WARN | {`images` 类发现} |  |  |  |
| Schema(JSON-LD) | {类型;与可见内容一致性} | 只标记页面上真实存在的内容([通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies));用 `schema_lint.py` 和 RRT 验证 | {`schema_lint.py` 输出行+RRT 输出行} |  |  |  |
| Canonical / indexability | {canonical 指向、robots、noindex} | 自指绝对 URL(相对路径 Google 支持但不建议,脚本记 WARN);`noindex` 在脚本里记 CRITICAL | {`canonical`、`robots` 类发现} |  |  |  |

## Priority Fixes

1. {P0:缺失类先补齐(缺 title/desc/H1 优先),再调长度}
2. {P1:意图错位/内链}
3. {P2:锦上添花项}

修复纪律:一次只改一组元素,留 14/28 天对比窗(本套件口径,否则归因不可分);同模板页面按本表批量套用前先抽 1 页试改。

## 检查清单(逐项:检查什么 → 怎么查 → 通过/失败)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 页面可抓取、渲染后元素齐全 | `python3 scripts/site_audit.py URL --market XX --json`;浏览器开渲染后 DOM 核对 title、H1、canonical | 通过:`verdict` 为 pass,无 CRITICAL,无 `[SKIP]`。失败:CRITICAL(缺 title、noindex 等)或被拒审 |
| 2 | title、description 长度(市场单位) | 读同一输出里的 `meta.title_len`、`meta.desc_len` 与顶层 `limits` | 通过:无 `title`、`description` 的 WARN。越阈:看截断后关键词是否仍在前部,不是排名规则 |
| 3 | 主查询词在 title、H1、首段 | GSC 导出该页的查询表,跑 `python3 scripts/question_align.py --gsc Queries.csv --page URL --fetch --json`,读 `queries[].cov_title`、`cov_h1`、`cov_lead` 与 `flags`([输出约定](../../references/content/question-alignment.md)) | 通过:无 `title_gap`、`lead_gap`(主查询在 title 与首段覆盖率均 ≥0.5);主查询展示 <3 或 `anonymized` 时不判。失败:任一标签出现 → 按 `missing_terms` 补买家原词 |
| 4 | 标题层级 | 同一输出 `headings` 类发现(跳级、H2 数量) | 通过:无「跳级」WARN。注意:这是可读性口径,不是 Google 规则 |
| 5 | CTR 对比同位基准 | 同一份 `question_align.py` 输出的 `site_ctr_by_position`(本站各排名段 CTR)和该页 `expected_clicks`;或 `python3 scripts/gsc_mining.py queries.csv --json` 的低 CTR 节 | 通过:该页点击不低于 `expected_clicks`,且 CTR 不比本站同排名段低 2 个百分点以上(`gsc_mining.py` 判据,本套件口径)。失败:低于 → 先改 title/description |
| 6 | 结构化数据与可见内容一致 | `python3 scripts/schema_lint.py URL`;RRT | 通过:无 WARN。失败:标记了页面上看不到的内容 |

## What could change this conclusion

- {数据缺口:GSC 28 天窗口含波动;个性化 SERP 与追踪工具位置可差 ±;窗口若含 2025-05-13 至 2026-04-27,展示、CTR、平均排名不可信,点击可用([官方记录](https://support.google.com/webmasters/answer/6211453))}
- {仅相关非因果:元素达标≠排名;能定案的验证:改版后 14/28 天同页 GSC 对比,一次只改一组元素}
- {样本局限:单页审计,模板级问题需抽同模板 {} 页复核}
- {继承假设:意图判定基于 {} 条 SERP 快照}

## Method Notes

- 数据源与抓取时间:{渲染后 DOM/Lighthouse/GSC/RRT+日期};移动端优先索引。已知坑:{JS 渲染站点须看渲染后 DOM;GSC 数据有延迟,近几天的数据是临时的;若见每个 meta 恰好两份,先查前端水合是否重复注入(本套件观察到的故障形态,不是通用规律)}。数字缺失写 [要追加: 数据源],禁编造。
- 符号:P0=2 周内修(影响资格/理解/收入);P1=本季度;P2=backlog(本套件口径)。阈值随市场换算,严重度对应见 [meta-tag-formulas.md](../../references/content/meta-tag-formulas.md) 审计扣分表。
