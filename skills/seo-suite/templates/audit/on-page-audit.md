# {答案式标题,例:"该页 6 项里 4 项在阈值内:真正压排名的是 H1 与搜索意图错位+零条上下文内链,改版预计 4 周见效"}

_For: {决策人} · Date: {YYYY-MM-DD} · Market: {目标市场/语言} · Render check: 浏览器渲染确认=是/否 · Data pulled: {日期+工具}_

> 多市场站点:逐市场各出一份本报告,不合并。市场差异规则见 references/overview/multilingual-workflow.md。
> 市场阈值注记:长度以像素截断为准,字符数只是代理。日语文本用全角口径(title 32/desc 120);拉丁 50–60/120–160;德/西/意 desc 150–160;泰语按字素 desc 120–155;印尼 meta 前 120 字符为安全区;中文 title 25–35 字/desc 60–90 字——见 multilingual-workflow 第四节与 meta-tag-formulas.md。

## The answer

{一段独立成立:该页最关键的 1-2 个问题(按对排名/点击的影响排序)+ 量化(如 CTR 低于同位均值 x%)+ 置信度 + 建议先改什么。只读这段的人不会错。}

## Page

- URL:{} · Primary keyword:{} · Intent:{按 keyword-intent-taxonomy.md}
- 当前表现:排名 {} · 点击 {}/展示 {} · CTR {}%(GSC,近 28 天)

## Key numbers

| 指标 | 数值 | 对比/阈值 |
|---|---|---|
| 审计元素数 | {9} | |
| 达标项 / 越阈项 | {} / {} | 缺失类远重于长度微调 |
| P0 修复项 | {} | 影响资格/理解 |
| CTR vs 同排名位基准 | {}% | 低 {} 个百分点则优先改 title/desc |

## Element Audit Table(逐元素审计)

每行:现状→阈值→Evidence→判定→Priority。Evidence 必须可复查(渲染后 DOM 摘录/截图/工具输出+抓取时间);**不得报告页面上不存在的信号**。

| Element | Current State(现状) | 阈值/规则 | Evidence | 判定 | Recommendation | Priority |
|---|---|---|---|---|---|---|
| Title | {原文} | {按市场列上方注记;主词前置} | {DOM 行+截断预览} | 达标/缺失/越阈 |  | P0-P2 |
| Meta description | {原文或"缺失"} | {同上;缺失 −15 分级} |  |  |  |  |
| H1 | {原文;是否含主词} | 唯一、含主词、与 title 互补不重复 |  |  |  |  |
| Heading 结构 H2-H6 | {层级是否连续、问题式 H2} | 层级不跳号;覆盖 PAA 类疑问 |  |  |  |  |
| 正文首屏 | {主词是否在前 100 词} | 意图匹配:SERP 主导形式对齐 |  |  |  |  |
| 内链(入/出) | {入 {} 条,上下文 {} 条} | 每页≥{} 条上下文内链;锚文本描述性 | {GSC 链接报告+爬虫} |  |  |  |
| 图片 | {N 张,alt 缺 {} 张} | alt 描述内容;原创图近相关文字 |  |  |  |  |
| Schema(JSON-LD) | {类型;与可见内容一致性} | 只标记页面上真实存在的;RRT 验证 | {RRT 输出行} |  |  |  |
| Canonical / indexability | {canonical 指向、robots、noindex} | 唯一 canonical;可索引 |  |  |  |  |

## Priority Fixes

1. {P0:缺失类先补齐(缺 title/desc/H1 优先),再调长度}
2. {P1:意图错位/内链}
3. {P2:锦上添花项}

修复纪律:一次只改一组元素,留 14/28 天观察窗,否则归因不可分;同模板页面按本表批量套用前先抽 1 页试改。

## What could change this conclusion

- {数据缺口:GSC 28 天窗口含波动;个性化 SERP 与追踪工具位置可差 ±}
- {仅相关非因果:元素达标≠排名;能定案的验证:改版后 14/28 天同页 GSC 对比,一次只改一组元素}
- {样本局限:单页审计,模板级问题需抽同模板 {} 页复核}
- {继承假设:意图判定基于 {} 条 SERP 快照}

## Method Notes

- 数据源与抓取时间:{渲染后 DOM/Lighthouse/GSC/RRT+日期};移动端优先索引。已知坑:{JS 渲染站点须看渲染后 DOM;GSC 数据延迟 2-3 天;水合 bug 会导致 head 标签成对出现——每 meta 恰好两份即该病特征}。数字缺失写 [要追加: 数据源],禁编造。
- 符号:P0=2 周内修(影响资格/理解/收入);P1=本季度;P2=backlog。阈值随市场换算,扣分权重见 meta-tag-formulas.md 审计扣分表。
