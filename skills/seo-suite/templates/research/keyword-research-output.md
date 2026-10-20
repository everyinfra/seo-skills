# {答案式标题,例:"Transactional 'X alternatives' 集群是最大机会:4 个簇月搜索 12k+、KD≤25,30 天内可进前 20"}

_For: {决策人} · Date: {YYYY-MM-DD} · Market: {目标市场/语言} · Data pulled: {日期+数据源}_

> 多市场站点:逐市场各出一份本报告,不合并。市场差异规则见 references/overview/multilingual-workflow.md。

## The answer

{一段独立成立:核心结论 + 总可及搜索量/簇数 + 置信度(高/中/低+一句话依据) + 对业务意味着什么。只读这段的人不会错。}

## Key numbers

| 指标 | 数值 | 对比/阈值 |
|---|---|---|
| 候选关键词总数 | {} | |
| 优先簇数 | {} | 入选标准:KD≤{} 且 月搜索≥{} |
| 合计月搜索量 | {} | 区间 {low–high} |
| 预计 90 天可获取流量 | {} | 假设:进入前 10;CTR 用本站自己的分段曲线,不用通用基准([forecast-report.md](../monitor/forecast-report.md)) |

## Keyword Clusters

| Cluster | Primary Keyword | Intent | Volume/mo | KD | 当前排名 | Priority | Confidence |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  | 高/中/低 |

## Quick Wins

入选标准:{如 KD≤25、已有排名 11–30、月搜索≥500}。不满足任一条不入列。

| Keyword | Volume | KD | 当前排名 | 预计收益 | 动作 |
|---|---|---|---|---|---|

## Strategic Bets

入选标准:{高价值但 KD>60 或需新内容}。每条注明押注逻辑与所需资源。

## Recommendation(选项表,选择权在 {owner})

| Option | Expected gain | Cost/effort | Confidence | Note |
|---|---|---|---|---|
|  | {流量/线索数+区间} | {人力/周} |  |  |

## 检查清单(逐项:检查什么 → 怎么查 → 通过/失败)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 簇内关键词真的同一意图 | 每个簇取 3–5 个词,在目标市场搜索,把前 10 条 URL 写成 CSV(`keyword,url1;url2;…`),跑 `python3 scripts/serp_overlap.py input.csv` | 通过:同簇词两两重合 ≥4 条(脚本四档:7–10 同文 / 4–6 同簇 / 2–3 互链 / 0–1 分开)。失败:重合 0–1 → 拆簇,各出一页 |
| 2 | Intent 分类有旁证 | 按 [keyword-intent-taxonomy.md](../../references/research/keyword-intent-taxonomy.md) 分类,Query 表「Intent」列写看到的 SERP 形态 | 通过:每个主词有 SERP 旁证。失败:凭词面猜 |
| 3 | 买家原词没被改写 | 主词来自 GSC 查询、工单原话或 SERP 的「相关搜索」([question-alignment.md](../../references/content/question-alignment.md)) | 通过:能指出每个主词的来源。失败:来源是「我想的」 |
| 4 | Quick Wins 入选标准写明并执行 | GSC 导出跑 `python3 scripts/gsc_mining.py queries.csv --json`,取 striking distance 节(排名 5–20、展示 ≥20,本套件口径);与你的入选标准求交集 | 通过:每条满足全部标准。失败:有词不满足仍入列 |
| 5 | 数据来自同一工具、同一日期 | 看 Data pulled | 通过:是。失败:混用 → 只写方向 |
| 6 | 多语言/多市场分开 | 每个市场一份报告 | 通过:是。失败:合并 |

## What could change this conclusion

- {数据缺口:如 volume 为 point estimate,非个性化 SERP 采样}
- {仅相关非因果:基于竞对现状;能定案的验证:先发 1 簇内容,30 天看排名}
- {弱分段:长尾/多语言未覆盖}
- {继承假设:intent 分类基于 {} 规则}

## Method Notes

- 数据源与抓取时间:{GKP/第三方 API + 日期}。KD 是各工具自己的模型估计,算法不同,数值不可跨工具比较;搜索量同理是估算。
- 符号:KD=关键词难度(0–100);Intent 按 keyword-intent-taxonomy.md 分类。
- 已知坑:{如 GSC 近几天的数据是临时的;含 2025-05-13 至 2026-04-27 的窗口里展示、CTR、平均排名不可信,点击可用([官方记录](https://support.google.com/webmasters/answer/6211453));AI 引用类查询无公开量}。数字缺失写 [要追加: 数据源],禁编造。
