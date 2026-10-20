# {答案式标题,例:"技术债不是主因:38 个索引页缺 canonical,但排名瓶颈在内容深度——修复 E-E-A-T 信号预计 60 天回收 15% 流量"}

_For: {决策人} · Date: {YYYY-MM-DD} · Scope: {域名/抽查页数/工具} · Render check: {浏览器渲染确认=是/否} · Market: {目标市场}_

> 多市场站点:逐市场各出一份本报告,不合并。

> 三模式渲染:按受众 exec/dev/prospect 裁剪,规范见 [report-modes.md](report-modes.md);输出必带 Today's priorities 节与建议四字段。

## Verdict

{fit for ranking growth / fixable blockers first / penalized-or-deindexed risk} — {一句话+三大结论规模数字。}

## The answer

{一段独立成立:最关键问题 + 量化影响 + 置信度 + 建议先做什么。}

## Key numbers

| 指标 | 当前 | 基准/阈值 | 判定 |
|---|---|---|---|
| 索引覆盖率(已编入/已提交) | {}% | ≥{}%(本站历史基线,不用行业平均) |  |
| LCP / INP / CLS(字段数据 p75) | {}ms / {}ms / {} | ≤2500ms / ≤200ms / ≤0.1([web.dev 官方阈值](https://web.dev/articles/vitals),核对 2026-10-21) |  |
| 修复项总数(P0/P1/P2) | {} |  |  |

## Findings

| Area | Issue | Evidence(怎么观测到) | Impact | Priority | Fix | Confidence |
|---|---|---|---|---|---|---|
|  |  | {URL+截图/工具输出+抓取时间} | {量化或"未知,需 GSC 验证"} | P0/P1/P2 |  | 高/中/低 |

每行 Evidence 必须可复查;**不得报告页面上不存在的信号**。长度类阈值是本套件提示值,不是 Google 限制:title 和 description 没有字符上限,只按设备宽度截断([title 文档](https://developers.google.com/search/docs/appearance/title-link)、[snippet 文档](https://developers.google.com/search/docs/appearance/snippet),核对 2026-10-21);市场单位以 `site_audit.py --json` 顶层 `limits` 为准(日全角/泰字素等),换算见 scoring-rubric 市场差异节。缺 description、缺 H1、相对 canonical 在脚本里记 WARN,因为 Google 把它们当可选或不建议,不当硬错误。

## Action Plan(选项表,选择权在 {owner})

| Option | Expected gain | Cost/effort | Confidence | Note |
|---|---|---|---|---|
|  | {流量/索引数+区间} | {人力/周} |  |  |

## What could change this conclusion

- {抽样局限:仅审计 {} 页,占全站 {}%}
- {渲染依赖:基于 JS 渲染后 DOM;需 GSC URL Inspection 复核}
- {因果模糊:排名下降与 {} 同期,无法排除算法更新/季节性;定案方式:{}(对照 seo-drift-monitoring 算法归因层)}
- {数据坑:Search Console 的展示、CTR、平均排名在 2025-05-13 至 2026-04-27 记录有误,点击不受影响;含这段时间的两期展示对比不可信([官方记录](https://support.google.com/webmasters/answer/6211453),核对 2026-10-21)}

## 检查清单(逐项:检查什么 → 怎么查 → 通过/失败)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 抽样页逐页审计 | `python3 scripts/site_audit.py URL1 URL2 … --market XX --json > audit.json`(stdout 只有一个 JSON 对象;顶层有 `market`、`limits`、`results`) | 通过:`results` 里每个 URL 有 `verdict`,无 `[SKIP]` 拒审页。失败:有 CRITICAL(退出码 1)或拒审页未补抓 |
| 2 | 健康分与影响排序 | `python3 scripts/health_score.py --input audit.json --json`,读 `main_score`、`band`、`impacts[]` | 通过:能列出 impact 降序的前 5 项。失败:`unmapped` 非空且未解释 |
| 3 | 索引覆盖 | Search Console →「页面索引编制」报告(原 Coverage)+ 网址检查抽 N 页 | 通过:抽查页都「已编入」。失败:有「已抓取 - 尚未编入」或错误 canonical |
| 4 | 字段 CWV | CrUX 或 Search Console「核心网页指标」报告,看 p75(28 天滑动窗口,[CrUX 文档](https://web.dev/articles/crux-and-rum-differences)) | 通过:LCP ≤2500ms、INP ≤200ms、CLS ≤0.1。失败:任一项在「需要改进」或「差」 |
| 5 | 渲染一致 | 浏览器看渲染后 DOM;`curl -s URL` 看初始 HTML,两者的 title、canonical、正文要点一致 | 通过:一致。失败:关键信息只在 JS 渲染后出现 |
| 6 | 结构化数据 | `python3 scripts/schema_lint.py URL` + [Rich Results Test](https://search.google.com/test/rich-results) | 通过:无 WARN,所标内容页面上看得到。失败:悬空 @id、占位符、标记不可见内容 |

复查节点(写进计划,不是定时任务):
- [ ] P0 修复后 14 天:页面索引编制报告复查 {} 页
- [ ] {} 排名复查日:{YYYY-MM-DD}

## Method Notes

- 工具与版本:{crawler/Lighthouse/RRT + 日期};移动端优先索引;抽样方法:{首页+N 模板页+N 随机页}。
- 符号:P0=2 周内修(影响索引/收入);P1=本季度;P2=backlog。
