# {答案式标题,例:"索引层是唯一 P0:38% 页面被错误 canonical 吸走,CWV 全绿非瓶颈——修 canonical 预计 6 周回收 12% 展示"}

_For: {决策人} · Date: {YYYY-MM-DD} · Domain/section: {} · Main issue category: {CWV/索引/爬取/安全/schema} · Render check: 浏览器渲染确认=是/否 · Data pulled: {日期+工具}_

> 多市场站点:逐市场各出一份本报告,不合并。市场差异规则见 references/overview/multilingual-workflow.md。
> 市场差异注记:市场决定要查哪些引擎的爬虫和站长后台——俄、土含 Yandex;韩查 Naver 的 Yeti(Search Advisor);日本桌面端 Bing 份额高,Search Console 不含 Bing 流量,要并接 Bing Webmaster Tools;越南查 Cốc Cốc(`coccocbot-web`)。份额和细节见 [references/markets/](../../references/markets/) 各市场文件(已核,份额随月波动,带月份引用)。

## The answer

{一段独立成立:五层里哪层是真瓶颈(量化:影响 URL 数/流量)+ 哪些"疑似问题"排除及依据 + 置信度 + 修复顺序。只读这段的人不会错。}

## Key numbers

| 指标 | 数值 | 基准/阈值 | 判定 |
|---|---|---|---|
| 抽查页数(占全站) | {} ({}%) | 首页+N 模板页+N 随机页 |  |
| 索引覆盖率(已编入/已提交) | {}% | ≥{}% |  |
| LCP p75 / INP p75 / CLS p75 | {}ms / {}ms / {} | 良好档(字段数据,[阈值表](../../references/overview/facts.md#cwv)) |  |
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

## 检查清单(逐项:检查什么 → 怎么查 → 通过/失败)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 爬虫能进站 | `python3 scripts/robots_posture.py https://站点/robots.txt --json`;再 `curl -sI -A "Googlebot" URL` 抽测 3 个重点页 | 通过:search 与 user 层爬虫无 Disallow(`citation_bots_ok` 为真),抽测 200。失败:检索型爬虫被禁或被 WAF 拦。封 training 型爬虫是授权决策,不算失败 |
| 2 | 页面可索引 | `python3 scripts/site_audit.py URL … --market XX --json`;Search Console 网址检查抽 {} 页 | 通过:无 `robots`(noindex)CRITICAL,网址检查「已编入」。失败:noindex、被 canonical 吸走或「已抓取 - 尚未编入」 |
| 3 | 重定向链 | `python3 scripts/redirect_chain.py URL` | 通过:无循环,≤1 跳(本套件口径;脚本默认超过 5 跳判 CRITICAL)。失败:循环或多跳 |
| 4 | sitemap | `python3 scripts/sitemap_audit.py https://站点` | 通过:六坏桶(非 200、3xx、noindex、canonical 他指、robots 屏蔽、参数重复)全空,退出码 0。失败:任一桶非空(退出码 1) |
| 5 | 字段 CWV | `python3 scripts/field_data.py --url URL --strategy both --json`(需 CrUX key;CrUX 为滑动窗口,[长度](../../references/overview/facts.md#crux-window)) | 通过:p75 的 LCP、INP、CLS 都在[良好档](../../references/overview/facts.md#cwv)。失败:任一项超阈。只有实验室数据时写「未验证字段」,不判通过 |
| 6 | 渲染一致 | 浏览器看渲染后 DOM;`curl -s URL` 看初始 HTML | 通过:title、canonical、正文要点一致。失败:关键信息只在 JS 渲染后出现 |
| 7 | 结构化数据 | `python3 scripts/schema_lint.py URL`;Rich Results Test | 通过:无 WARN,标记内容页面上看得到。失败:悬空 @id、占位符、标记不可见内容 |
| 8 | 爬取行为(有日志时) | `python3 scripts/log_session.py --log access.log --ua Googlebot --json` | 通过:无 `param_loop`(同路径参数请求 >10)、`deep_crawl`(深度 >8)。失败:出现陷阱特征 |

复查节点:
- [ ] P0 修复后 14 天:Search Console「页面索引编制」报告复查
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
- {数据坑:CrUX 是滑动窗口([长度](../../references/overview/facts.md#crux-window)),修复后数字要等几周才全部反映;Search Console 展示、CTR、平均排名在[GSC 数据异常期](../../references/overview/facts.md#gsc-anomaly)里记录有误,点击不受影响}

## Method Notes

- 工具与版本:{crawler/Lighthouse/CrUX/RRT+日期};移动端优先索引;字段数据(p75)为准,实验室数据只作诊断。已知坑:{Lighthouse 是实验室数据,分数不等于 CWV 字段数据;日志需按爬虫 UA 过滤并核验 IP,UA 可以伪造}。数字缺失写 [要追加: 数据源],禁编造。
- 符号:P0=2 周内修(影响索引/收入);P1=本季度;P2=backlog(本套件口径)。
