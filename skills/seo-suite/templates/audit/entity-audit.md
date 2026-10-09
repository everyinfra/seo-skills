# {答案式标题,例:"品牌实体半缺席:官网 NAP 三处不一致+无 Organization schema,知识面板触发的 5 个查询全部无我们"}

_For: {决策人} · Date: {YYYY-MM-DD} · Brand/entity: {} · Market: {目标市场/语言} · Data pulled: {日期+各平台核对时间}_

> 多市场站点:逐市场各出一份本报告,不合并。实体一致性按各市场的联系格式/社交矩阵核,市场差异规则见 references/overview/multilingual-workflow.md。
> 市场差异注记:如荷兰 KvK(商会)号入 NAP;日语区 Wikipedia JP+法人番号+业界门户 NAP 一致——逐市场清单见 references/technical/entity-signal-checklist.md。

## The answer

{一段独立成立:实体在搜索引擎里的当前状态(有/半/无)+ 最伤的 1-2 个不一致 + 量化(不一致平台数、可触发的品牌查询)+ 置信度 + 先修什么。只读这段的人不会错。}

## Key numbers

| 指标 | 数值 | 对比/阈值 |
|---|---|---|
| 核对平台/信号数 | {} | 官网+schema+{} 个第三方 |
| NAP 一致平台数 | {} | 目标:全部一致 |
| 缺失/冲突信号数 | {} | P0:{影响知识面板/知识图谱资格} |
| 品牌词月搜索量 | {} | 实体强化的可及面 |

## Entity Matrix(实体矩阵:各平台 NAP/一致性)

NAP=Name/Address/Phone。每格填"该平台当前值+与主源一致?"。主源=官网 contact 页;列出核对日期。

| 平台/信号 | Name | Address | Phone | 其他(编号/社交/坐标) | 与主源一致? | 核对日期 | 缺口 |
|---|---|---|---|---|---|---|---|
| 官网 contact 页(主源) | — | — | — | — | 基准 |  |  |
| 官网 footer |  |  |  |  | ✓/✗/缺失 |  |  |
| Organization schema(JSON-LD) |  |  |  | {sameAs 列表} |  |  | {如缺 sameAs 指向社交} |
| Google 商家资料 |  |  |  | {类目/营业时间} |  |  | {需自己账号核} |
| {行业目录/门户} |  |  |  |  |  |  |  |
| {社交主页}×N |  |  |  | {bio 一致性} |  |  |  |
| {市场特有源:Wikipedia/KvK/法人番号} |  |  |  |  |  |  |  |

## Signals(信号层缺口)

| Signal | Current State | Gap | Evidence(怎么观测到) | Fix | Priority |
|---|---|---|---|---|---|
| Organization schema 完整性 | {有/无;缺 {} 属性} | {如缺 logo/sameAs} | {页面源码行+RRT} |  | P0-P2 |
| 官网↔社交 sameAs 互指 |  |  |  |  |  |
| 权威第三方收录 | {Wikipedia/行业库有无} |  | {搜索 site: 查询+日期} |  |  |
| 品牌词 SERP 现状 | {知识面板有无/谁占} |  | {SERP 快照} |  |  |

## Fix Priority(修复优先级)

| 优先级 | 动作 | 预期 | 所需 |
|---|---|---|---|
| P0 | {先统一官网内部 NAP+补 Organization schema} | 一致的主源是其他一切的前提 | {开发 0.5 天} |
| P1 | {修正 Google 商家资料/目录 NAP} | 本地包与图谱资格 | {逐平台人工} |
| P2 | {争取权威收录(Wikipedia 等)} | 知识面板概率提升,不保证 | {编辑流程,周期长} |

## Recommended Actions

1.
2.
3.

## What could change this conclusion

- {数据缺口:知识面板/图谱无公开 API,触发与否只能观测不能验证}
- {仅相关非因果:实体一致≠出现知识面板;能定案的验证:P0+P1 完成后 {} 天品牌词 SERP 复查}
- {样本局限:平台清单按 {} 市场选,长尾目录未穷尽}
- {继承假设:NAP 主源以官网 contact 页为准(若有多地址/多主体需先定主源)}

## Method Notes

- 数据源与抓取时间:{逐平台人工核对+页面源码+日期}。已知坑:{知识面板全自动不可申请,实体认领走 Google 验证流程;schema 标记不存在的信息即违规}。数字缺失写 [要追加: 数据源],禁编造。
- 符号:✓/✗/缺失 三态;P0=2 周内,P1=本季度,P2=backlog。逐市场信号清单见 entity-signal-checklist.md,图谱机制见 knowledge-graph-guide.md。
