# {答案式标题,例:"索引层是唯一 P0:38% 页面被错误 canonical 吸走,CWV 全绿非瓶颈——修 canonical 预计 6 周回收 12% 展示"}

_For: {决策人} · Date: {YYYY-MM-DD} · Domain/section: {} · Main issue category: {CWV/索引/爬取/安全/schema} · Render check: 浏览器渲染确认=是/否 · Data pulled: {日期+工具}_

> 多市场站点:逐市场各出一份本报告,不合并。市场差异规则见 references/overview/multilingual-workflow.md。
> 市场差异注记:市场决定爬虫面——俄/土=Yandex、韩=Yeti、日=Bing 必查、越=Cốc Cốc;robots/安全头按各引擎口径复核。

## The answer

{一段独立成立:五层里哪层是真瓶颈(量化:影响 URL 数/流量)+ 哪些"疑似问题"排除及依据 + 置信度 + 修复顺序。只读这段的人不会错。}

## Key numbers

| 指标 | 数值 | 基准/阈值 | 判定 |
|---|---|---|---|
| 抽查页数(占全站) | {} ({}%) | 首页+N 模板页+N 随机页 |  |
| 索引覆盖率(已编入/已提交) | {}% | ≥{}% |  |
| LCP p75 / INP p75 / CLS p75 | {}ms / {}ms / {} | ≤2500ms / ≤200ms / ≤0.1(字段数据) |  |
| 可索引性阻断页数 | {} | noindex/robots/canonical 吸走 |  |
| 修复项 P0/P1/P2 | {}/{}/{} |  |  |

## Findings by Layer(技术栈分层)

| 层 | Issue | Evidence(怎么观测到) | 影响 URL 数/流量 | Priority | Fix | Confidence |
|---|---|---|---|---|---|---|
| **CWV/渲染** | {如 LCP 4.1s:主图未预加载} | {CrUX/现场 Lighthouse+URL+日期;实验室 vs 字段区分} |  | P0-P2 |  | 高/中/低 |
| **索引** | {如 canonical 互指/软 404} | {GSC URL Inspection 逐条} |  |  |  |  |
| **爬取** | {如 robots 屏蔽 CSS/链路深} | {robots.txt 原文+日志分析} |  |  |  |  |
| **安全/规范** | {如 http 混链/缺 HTTPS 重定向} | {curl -I 输出} |  |  |  |  |
| **结构化数据** | {如 schema 与可见内容不符} | {RRT/validator 报错行} |  |  |  |  |

Evidence 必须可复查;不得报告页面上不存在的信号。爬取与状态码细节见 references/technical/audit-rule-catalog.md 与 http-status-codes.md;CWV 修法走 cwv-playbook.md。

## Exclusions(查过且排除的)

- {疑似项:为什么不是问题(证据一行)}——防"全都要修"式清单。
- {疑似项:如"重复 meta=索引膨胀"?实际 {} 页且均带参数,canonical 正确}——排除依据:{...}。
- {疑似项:如"Lighthouse 分数低"?字段数据 p75 全绿}——实验室 vs 字段以字段为准。
- {市场引擎特有:如 Yandex regional 因素?已在 {市场} 报告单独处理}——本报告不重复。

## Validation(验证 checklist)

- [ ] 爬取面:主引擎爬虫可达(Googlebot+{市场引擎}),robots.txt 无误封,CSS/JS 未屏蔽
- [ ] 可索引性:抽查 {} 页 URL Inspection=已编入;canonical/301 链≤1 跳
- [ ] 渲染/schema 方法合适:渲染后 DOM 与源码一致;JSON-LD 过 RRT+validator
- [ ] P0 修复后 14 天:GSC Coverage/增强报告复查
- [ ] 排名复查日:{YYYY-MM-DD}(对照 seo-drift-monitoring 归因)

## Recommended Actions

按层给出,只列有 Evidence 支撑的修复;每条附 owner 与复查日。

1. {P0:{层}修复:动作→预期(索引数/流量+区间)}
2. {P1:…}
3.

## What could change this conclusion

- {抽样局限:仅审计 {} 页,占全站 {}%,模板级外推需复核}
- {渲染依赖:基于 JS 渲染后 DOM;水合类 bug 需 GSC 复核}
- {因果模糊:流量下降与 {} 同期,无法排除算法/季节性;定案:L1-L5 归因链}
- {数据坑:CrUX 为 28 天滚动窗口;GSC impressions 有日志错误区间}

## Method Notes

- 工具与版本:{crawler/Lighthouse/CrUX/RRT+日期};移动端优先索引;字段数据(p75)为准,实验室数据只作诊断。已知坑:{Lighthouse 分数≠CWV;日志需按爬虫 UA 过滤}。数字缺失写 [要追加: 数据源],禁编造。
- 符号:P0=2 周内修(影响索引/收入);P1=本季度;P2=backlog。
