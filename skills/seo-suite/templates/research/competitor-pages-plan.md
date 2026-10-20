# {答案式标题,例:"6 张对比页按搜索量降序分三批发:'X vs Y' 先行(月搜 2.4k、KD 18),双竞对比页全部缓发"}

_For: {决策人} · Date: {YYYY-MM-DD} · Scope: {品牌/产品} · Market: {目标市场/语言} · Main competitors: {A、B、C} · Goal: SEO / sales enablement / both_

> 多市场站点:逐市场各出一份本报告,不合并。市场差异规则见 references/overview/multilingual-workflow.md。

## The answer

{一段独立成立:规划了多少页、按什么排序发布、预期流量/线索+区间、置信度、第一个里程碑(第 1 批上线后 N 天看什么)。只读这段的人不会错。}

## Key numbers

| 指标 | 数值 | 对比/阈值 |
|---|---|---|
| 规划页面总数 | {} | 分 {} 批发布 |
| 覆盖查询合计月搜索量 | {} | 区间 {low–high} |
| 预计 90 天可获取流量 | {} | 假设:进入前 10;CTR 用本站分段曲线,不用通用基准;只是区间,不承诺排名 |
| 需先补齐的竞品数据项 | {} | 缺项见 Competitor Data Requirements |

## Page Plan(页面规划表)

每页一行:目标词、意图、模板、预估。模板选型见 references/research/competitor-page-patterns.md 与 competitor-section-templates.md。

| # | Page Type | Target Query(模式或具体词) | Intent | 月搜索量 | KD | URL Pattern | 模板/结构 | 预估流量/线索 | 发布批次 | 依赖 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Alternatives | {competitor} alternatives | 商业调研 |  |  | /alternatives/{competitor}/ | 对比表+迁移指南 |  | 1 | 竞品定价数据 |
| 2 | You vs Competitor | {competitor} vs {us} | 商业调研 |  |  | /compare/{competitor}-vs-{us}/ | 逐项对照+适合谁 |  | 1 | 功能对照核实 |
| 3 | Competitor vs Competitor | {A} vs {B} | 商业调研 |  |  | /compare/{a}-vs-{b}/ | 中立对照+何时选我们 |  | 2 | — |
| 4 | Alternative(总览) | {category} alternatives | 商业调研 |  |  | /alternatives/ | 横评目录 |  | 1 | 1-3 页可链 |
| 5 | {迁移/切换型} | switch from {competitor} | 交易 |  |  | /migrate/from-{competitor}/ | 步骤+工具 |  | 3 | 工具支持 |
| 6 |  |  |  |  |  |  |  |  |  |  |

排序规则:先发搜索量×可赢性(KD、对手弱点)高的;双竞对比页在自有权威不足时缓发。

## Internal Link Map(内链图)

```
{Hub: /alternatives/ 总览页}
   ├── /alternatives/{competitor-a}/ ──┐
   ├── /alternatives/{competitor-b}/ ──┼── 互链:同类页交叉引用(仅真实相关时)
   ├── /compare/{a}-vs-{us}/           │
   └── /migrate/from-{a}/ ─────────────┘
        │
        └──→ {产品定价页/核心转化页}(每页恰好一条上下文 CTA)
```

- Hub pages:{...} · Supporting pages:{...} · Footer/nav links:{只放总览页,避免全站模板链}
- 内链锚文本规则:{描述性短语,禁全站同一商业锚文本}

## Publish Order(发布顺序与节奏)

| 批次 | 页面 | 上线窗口 | 前置条件 | 验证节点 |
|---|---|---|---|---|
| 1 | {#4、#1、#2} | 第 1–2 周 | 竞品数据核实完毕 | 上线 14 天:收录+排名基线 |
| 2 | {#3} | 第 4 周 | 批次 1 进前 30 或 GSC 有展示 | 30 天:CTR 复查 |
| 3 | {#5} | 第 6–8 周 | 工具/迁移支持就绪 | 60 天:线索归因 |

## Competitor Data Requirements

| Competitor | Positioning | Pricing(套餐/地区/日期) | Strengths | Weaknesses | Migration Notes |
|---|---|---|---|---|---|
|  |  | {未公开写"未公开"} |  |  |  |

数据是页面展示层的单一事实源,更新纪律见 references/research/competitor-content-architecture.md。

## Risks / Honesty Constraints

- 不歪曲竞品功能;每条对照事实可溯源(URL+日期)。
- 承认对方更适合谁;未核实的写"待核实",不猜。
- 双竞对比页在我们无一手评测时不写主观结论。

## 检查清单(逐项:检查什么 → 怎么查 → 通过/失败)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 目标词真有对比页形态的 SERP | 每个 Target Query 在目标市场搜索,截图前 10 条的页面类型 | 通过:前 10 里有对比页或替代方案页。失败:全是官网首页或评测站且无此形态 → 降级或删 |
| 2 | 同簇查询不拆成两页 | `python3 scripts/serp_overlap.py input.csv`(CSV:`keyword,前 10 条 URL 以分号分隔`) | 通过:重合 ≥4 的词合并成一页;0–1 的才分开。失败:重合高却各建一页 |
| 3 | 每条对照事实可溯源 | 打开竞品官网定价页、功能页、文档,记 URL 与核对日期 | 通过:有 URL + 日期,未核实写「待核实」。失败:凭印象 |
| 4 | 内链图可执行 | 上线后 `python3 scripts/site_crawl.py 站点 --max 500 --out crawl.json`,再 `python3 scripts/link_graph.py --crawl crawl.json` 看入链为 0–1 的页面 | 通过:计划页都有 ≥1 条正文内链,总览页链到各页。失败:新页是孤儿 |
| 5 | 每页恰好一条上下文 CTA | 逐页读 | 通过:一条。失败:没有或多条 |
| 6 | 批次门槛按数据判 | 批次 1 上线 14 天后 GSC 看收录与展示 | 通过:达到计划里写的前置条件才发下一批。失败:未达标仍发批次 2 |

## What could change this conclusion

- {数据缺口:搜索量/KD 为工具估算,各工具算法不同;双竞词的量常被工具合并}
- {仅相关非因果:排序基于对手弱点推断;能定案的验证:批次 1 上线 30 天的排名信号再决定批次 3}
- {样本局限:竞品数据截至 {日期},对方改版会失效}
- {继承假设:模板选型基于 {} 市场的 SERP 形态}

## Method Notes

- 数据源与抓取时间:{关键词工具+竞品官网+SERP 快照+日期}。已知坑:{竞品定价页随时变更,上线前再核一次并记日期(48h 是本套件口径)}。数字缺失写 [要追加: 数据源],禁编造。
- 符号:发布批次 1–3 对应 Publish Order;预估流量为进入前 10 假设下的区间值,不承诺排名。
- 对外比较性说法发布前按所在市场比较广告法规确认,法律事项由法务判断(同 battlecard-template.md 诚实原则)。
