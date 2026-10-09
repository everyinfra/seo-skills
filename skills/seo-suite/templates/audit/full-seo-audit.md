# {答案式标题,例:"技术债不是主因:38 个索引页缺 canonical,但排名瓶颈在内容深度——修复 E-E-A-T 信号预计 60 天回收 15% 流量"}

_For: {决策人} · Date: {YYYY-MM-DD} · Scope: {域名/抽查页数/工具} · Render check: {浏览器渲染确认=是/否} · Market: {目标市场}_

> 多市场站点:逐市场各出一份本报告,不合并。

## Verdict

{fit for ranking growth / fixable blockers first / penalized-or-deindexed risk} — {一句话+三大结论规模数字。}

## The answer

{一段独立成立:最关键问题 + 量化影响 + 置信度 + 建议先做什么。}

## Key numbers

| 指标 | 当前 | 基准/阈值 | 判定 |
|---|---|---|---|
| 索引覆盖率 | {}% | ≥{}% |  |
| LCP p75 | {}ms | ≤2500ms |  |
| 修复项总数(P0/P1/P2) | {} |  |  |

## Findings

| Area | Issue | Evidence(怎么观测到) | Impact | Priority | Fix | Confidence |
|---|---|---|---|---|---|---|
|  |  | {URL+截图/工具输出+抓取时间} | {量化或"未知,需 GSC 验证"} | P0/P1/P2 |  | 高/中/低 |

每行 Evidence 必须可复查;**不得报告页面上不存在的信号**。市场阈值按 scoring-rubric 市场差异节换算(日全角/泰字素等)。

## Action Plan(选项表,选择权在 {owner})

| Option | Expected gain | Cost/effort | Confidence | Note |
|---|---|---|---|---|
|  | {流量/索引数+区间} | {人力/周} |  |  |

## What could change this conclusion

- {抽样局限:仅审计 {} 页,占全站 {}%}
- {渲染依赖:基于 JS 渲染后 DOM;需 GSC URL Inspection 复核}
- {因果模糊:排名下降与 {} 同期,无法排除算法更新/季节性;定案方式:{}(对照 seo-drift-monitoring 算法归因层)}
- {数据坑:GSC impressions 2025-05-13 至 2026-04-27 日志错误区间}

## Validation(下一步可验证)

- [ ] P0 修复后 14 天:GSC Coverage 复查 {} 页
- [ ] {} 排名复查日:{YYYY-MM-DD}
- [ ] Rich Results Test 复核:{URL}

## Method Notes

- 工具与版本:{crawler/Lighthouse/RRT + 日期};移动端优先索引;抽样方法:{首页+N 模板页+N 随机页}。
- 符号:P0=2 周内修(影响索引/收入);P1=本季度;P2=backlog。
