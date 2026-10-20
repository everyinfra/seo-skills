# GEO 采样 prompt 库(prompt-bank)

> **模板性质**:常驻输入件库,不是一次性报告模板——表格行实例化后喂给 `citation_panel.py` 建立/扩充采样面板;结论产在第 7 节指向的周报/月报,本文件不产出任何数字。
> **数据来源与核对状态**(2026-10-21):①Scrunch 监测指南写明「每个主题簇 12–15 个问题」(`簇数 × 12–15 = 要追踪的 prompt 数`,[Scrunch](https://scrunch.com/guides/ai-search-guide/monitoring/),已核);②Peec 2026-09-29 的研究写明品牌词 prompt 的答案几乎每次都提到该品牌,非品牌 prompt 才不确定,建议分开看,并建议多加 prompt 而不是多跑几次([Peec](https://peec.ai/blog/the-key-to-prompt-tracking),已核);③fanout 六类型的名字见第三方转述(omnius.so),Otterly 原页打不开(403),**未核**,各引擎展开子查询数的具体数字找不到一手来源,已删;④5+3+2 起步集、persona 前缀与固定后缀、source-seeking 后缀三变体、GSC 词转问句公式、扩量节奏,均未找到厂商一手文档,一律按**本套件口径**使用。施工图见 [references/research/borrow-specs.md](../../references/research/borrow-specs.md) B3 节。[推断]=本库自定。

_For: {执行人} · Version: {YYYY-MM-DD 建库/复核日} · Scope: {brand}={品牌名}, {category}={品类}, 竞品集={competitor 候选清单} · Engines: {采样引擎清单}_

> 占位符约定(实例化时全部替换,采样面板中不得残留花括号):`{brand}` 品牌名 · `{category}` 品类 · `{competitor}` 竞品名 · `{use_case}` 具体用例 · `{pain_point}` 痛点 · `{segment}` 人群段。

## The answer(怎么用本库)

{一段独立成立:起步只取 10 条(5 认知+3 比较+2 决策,配方见第 4 节),从主矩阵按漏斗各选;凡句面含 {brand} 的条目、第 2 节风险条目、第 3 节 persona 变体,三组各自单独统计,不与非品牌主指标混算;单次采样非确定,一律按第 6 节纪律(topic 分组+周聚合,n≥3 才报)处理后进 [../monitor/ai-visibility-weekly.md](../monitor/ai-visibility-weekly.md)。只读这段的人不会错。}

## 1. 主矩阵 20 条(漏斗 × 视角)

构成:3 漏斗段 × 6 视角 = 18 条,品类视角在认知/比较各加 1 条(A2/C7)补满 20。**模板列为整句、可直接运行**,后缀已嵌入句尾;A1/C1/D1 三条照抄竞品原文起头(见 Method Notes)。source-seeking 后缀三变体(Include sources / According to experts / Cite your sources)**可组合或互换**(如句尾换 "Include sources. According to experts."),不加后缀也合法但会降低带引用回答的概率——换过变体的条目视为新 prompt,历史数据不连用。

| 编号 | 漏斗 | 视角 | 模板(整句) | source-seeking 后缀 |
|---|---|---|---|---|
| A1 | 认知 | 品类 | What are the best tools in {category} in 2026? Include sources. | Include sources |
| A2 | 认知 | 品类 | What {category} tools work well for {use_case}? Cite your sources. | Cite your sources |
| A3 | 认知 | 替代 | What are the main alternatives to {competitor}? Include sources. | Include sources |
| A4 | 认知 | 痛点 | How do teams commonly solve {pain_point}? According to experts. | According to experts |
| A5 | 认知 | 人群 | What are the best {category} for {segment}? Cite your sources. | Cite your sources |
| A6 | 认知 | 价格 | How much does {category} typically cost in 2026? According to experts. | According to experts |
| A7 | 认知 | 迁移 | What should a team check before switching {category} providers? Include sources. | Include sources |
| C1 | 比较 | 品类 | How visible is {brand} compared to its competitors? Include sources. | Include sources |
| C2 | 比较 | 替代 | What are the best alternatives to {brand}? Cite your sources. | Cite your sources |
| C3 | 比较 | 痛点 | Which {category} best addresses {pain_point}? According to experts. | According to experts |
| C4 | 比较 | 人群 | {brand} or {competitor}: which is the better fit for {segment}? Cite your sources. | Cite your sources |
| C5 | 比较 | 价格 | How does {brand} pricing compare to {competitor}? Include sources. | Include sources |
| C6 | 比较 | 迁移 | How hard is it to migrate from {competitor} to {brand}? According to experts. | According to experts |
| C7 | 比较 | 品类 | Compare the top 3 {category} for {use_case}. Cite your sources. | Cite your sources |
| D1 | 决策 | 品类 | What are the top 3 reasons to choose {brand} based on trusted sources? | (问句内嵌)based on trusted sources |
| D2 | 决策 | 替代 | Why do teams choose {brand} over {competitor}? Include sources. | Include sources |
| D3 | 决策 | 痛点 | Should we pick {brand} if our biggest problem is {pain_point}? Cite your sources. | Cite your sources |
| D4 | 决策 | 人群 | Would experts recommend {brand} for {segment}? According to experts. | According to experts |
| D5 | 决策 | 价格 | Is {brand} worth the price for {use_case}? Cite your sources. | Cite your sources |
| D6 | 决策 | 迁移 | What is the safest way to switch from {competitor} to {brand}? Include sources. | Include sources |

## 2. 风险/负面视角(2 条,测 sentiment 边界)

| 编号 | 类型 | 模板(整句) | source-seeking 后缀 |
|---|---|---|---|
| R1 | 投诉 | What are the biggest complaints about {brand}? Include sources. | Include sources |
| R2 | 迁出 | Why do teams switch away from {brand}? According to reviews. | According to reviews(风险组专用第四变体) |

纪律:R 组只用于测不利框架的占比与边界(sentiment 口径见 [references/monitoring/brand-mention-monitoring.md](../../references/monitoring/brand-mention-monitoring.md) 第六节),**不并入主 visibility 均值**;与品牌词一样按第 4 节规则独立分组。

## 3. Persona fan-out 前缀表

用法:前缀 + 空格 + 任一基础模板(主矩阵或 R 组)= 一条新 prompt,固定后缀原样追加在句尾。前缀措辞和后缀都是本套件口径[推断自定:persona 角色词必须出现,其余可改];persona 变换思路借鉴 Scrunch,未核厂商文档。

| Persona | 前缀[推断] | 固定后缀(本套件口径) |
|---|---|---|
| CMO | As a CMO evaluating this quarter's tech spend, | Respond with sources and direct claims first. |
| Founder | As a founder scaling a small team, | Respond with sources and direct claims first. |
| SEO Lead | As an SEO lead reporting organic growth, | Respond with sources and direct claims first. |
| PMM | As a product marketing manager building a competitive battlecard, | Respond with sources and direct claims first. |

**限额提醒(硬规则)**:persona fan-out 后执行数 = 基础 prompt 数 × persona 数(4)翻倍计入采样限额——主矩阵 20 条 × 4 = 80 次/轮,再乘引擎数与采样次数;预算紧张时只对比较段(C 组)做 fan-out,认知/决策段保持基础形态。

## 4. Stage 配方(本套件口径 + 已核的两条外部依据)

- stage 框架(本套件口径):awareness / consideration / conversion / loyalty 四段;本库映射:认知=A、比较=C、决策=D(loyalty 暂留空,待扩)。Scrunch 指南里的 funnel stage 示例分组是 Awareness、Advice、Evaluation、Comparison,与上面四段不同,各家分法不统一,本库只借「按漏斗分组」的思路。
- **起步集配方(本套件口径)**:5 awareness + 3 consideration + 2 decision,共 10 条起步——恰好满足 citation_panel.py 的 prompts≥10 下限(`citation_panel.py init --stage-mix` 会打印同一配方);示例选法:A1/A3/A5/A7 + C2/C4/C5 + D1/D2(可替换同漏斗其他条)。
- **每个主题簇 12–15 问**(Scrunch 指南的估算起点:簇数 × 12–15 = 追踪 prompt 数,指南说是起点而不是硬规则):簇内问句不足先补簇内问法,不急着开新簇。
- **品牌词 prompt 独立分组**:Peec 的研究说,品牌词 prompt(句面点名公司)里引擎几乎每次都会提到该公司,可见度很少变化;非品牌 prompt 才是优化影响最大、也最不确定的地方,所以两类要分开看。混入非品牌 prompt 会让总分失去信息量——品牌词组、R 组、persona 变体组各自单独统计、单独汇报(分组做法为本套件口径)。
- 扩量节奏(本套件口径,未找到厂商一手依据):起步集稳定后再扩;Peec 的结论是多加 prompt 比同一 prompt 多跑几次更能提高分数的准确度,时间越长越能确认可见度真的变了。

## 5. Fanout 六类型(第三方转述,未核 Otterly 原页)

引擎不会只检索你问的原句——先展开成子查询群。写 prompt 与做内容都要按展开后的语义对齐:

| 类型 | 一句定义 | 示例 |
|---|---|---|
| reformulation | 引擎把原 prompt 改写成等价问法再检索 | "best crm 2026" → "top rated crm software this year" |
| related | 引擎自行补问原问的相邻子问题 | "best CRM for small business" → "how much does a CRM cost per seat" |
| implicit | 沉默内容缺口:决策必需但用户没问出口的信息,引擎替用户补查 | 问 "best CRM" 时引擎补查迁移成本、隐藏费用等没人明说的考量 |
| comparative | 引擎自动把被问实体放进对比集 | "Is {brand} any good?" → "{brand} vs {competitor} vs {competitor}" |
| entity expansion | 简称/实体被展开为完整实体+属性再检索 | "Acme" → Acme(AI CRM 厂商)的公司实体卡片与 sameAs 属性 |
| personalized | 同一 prompt 按用户画像/会话历史被改写 | 同一问法,初创创始人视角与企业 CMO 视角得到不同展开 |

- **研究证据**:SSRN 预印本(Lee,2026-04-15;540 个母查询、1,323 条子查询、ChatGPT/Gemini/Perplexity)发现,子查询的字符串每次不同(同一提示重复采样的 Jaccard 相似度很低),但子查询的**类型**比较稳定(55–65% 的最常见类型一致),所以优化对象是类型层,不是某条具体子查询;意图对子查询构成有显著影响([SSRN 6652059](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6652059),核对 2026-10-21)。各引擎平均展开几条子查询,找不到一手数字,不写。
- **注记**:内容要覆盖的是展开后子查询能命中的语义,不是原始 prompt 的字面词匹配;展开行为分析走 `python3 scripts/fanout_analysis.py 文件.csv`(CSV 两列 `prompt,web_query`,`--top N` 控制每桶条数)。

## 6. 统计纪律

1. **单 prompt 单次不可靠**:LLM 非确定性,同一问法两次回答可不同——任何单点数字不下结论(n<3 = 掷硬币,与 citation_panel.py 同口径)。
2. **按 topic 分组 + 周聚合**:先 cluster 级周聚合,再下钻 prompt 级;不逐 prompt 逐日比较。
3. **攒够样本再看趋势**:非品牌 prompt 在 n≥10 之前只当方向(本套件口径;「比较类 10 次即可」无出处,已删)。
4. **3 次采样取多数**(majority 状态)并**标方差**;n≥3 才进报告(citation_panel.py 稳定判据:Wilson 95% CI 跨 0.5 = unstable;Wilson 区间是标准统计方法,阈值是本套件口径)。

## 7. 使用说明(接线)

- **喂给面板**:先把要用的行**复制到单独文件**(第 1/2 节表格的「模板」列,占位符实例化后),再 `python3 scripts/citation_panel.py init --brand X --prompts-file 你的文件.md --domain 站点`。也可以直接喂整份模板:解析器只收带「模板」列那张表的单元格(2026-10-21 起,整份模板得 22 条),但占位符要先实例化。或者另存单列 CSV(表头 `prompt`)走 `--prompts`。
- **GSC top 词 → 问句**(本套件口径):用 "What are the best [category] for [persona]?" 句式,GSC 有展现/点击的 top 非品牌词逐条套用,生成新 awareness prompt;更好的做法是直接用买家原话([question-alignment.md](../../references/content/question-alignment.md));品牌词路由到第 4 节独立组。
- **结果消费**:周报 [../monitor/ai-visibility-weekly.md](../monitor/ai-visibility-weekly.md)、月报 ai-visibility-monthly.md;引擎行为差异见 [references/content/geo-platform-differences.md](../../references/content/geo-platform-differences.md)。

## 检查清单(建库与复核时逐项:检查什么 → 怎么查 → 通过/失败)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 入面板的 prompt 是实例化后的整句 | `rg -n '\{(brand|category|competitor|use_case|pain_point|segment)\}' 你的文件.md` | 通过:零命中。失败:残留花括号 |
| 2 | 起步集 ≥10 条 | `python3 scripts/citation_panel.py init --brand X --prompts-file 你的文件.md --panel panel.json` 后看输出的 `prompts=N` | 通过:N ≥10 且等于你预期的条数。失败:N 与预期不符或 <10 |
| 3 | 品牌词、R 组、persona 变体单独统计 | `python3 scripts/citation_panel.py report --panel panel.json`,看「指标切片: prompt_targeting」里 `branded_or_direct` 与 `organic_unbranded` 分开 | 通过:两类分列。失败:混在一个分数里 |
| 4 | 每簇问题数 | 数每个 topic 的 prompt 数 | 通过:12–15(估算起点)。失败:差距大 → 补问法或合并簇 |
| 5 | 每个 prompt ≥3 次采样 | `report` 的「每 prompt 稳定性」节 | 通过:要下结论的 prompt 都有 ≥3 次有效采样。失败:不足不下结论 |
| 6 | 年份词不过期 | `rg -n '20[0-9]{2}' 你的文件.md` | 通过:年份为当前年。失败:过期年份词 → 测到的是旧索引行为 |
| 7 | 换过措辞的条目视为新 prompt | 对比版本记录 | 通过:新旧数据不连用。失败:跨版本连用 |

## What could change this conclusion

- {时效:句内年份词("in 2026")每年需滚动更新,过期年份词测到的是引擎旧索引行为而非当前可见性}
- {口径漂移:引擎的子查询行为随模型版本变;SSRN 研究里 ChatGPT 不同模型档的联网搜索触发率差别很大,换模型或档位要重新采样}
- {自定项:persona 前缀与后缀、source-seeking 后缀、R 组第四后缀变体、A2/C7 补位条目都是[推断]自定,没有厂商逐字依据——换措辞即换自变量}
- {措辞即自变量:source-seeking 后缀变体本身影响引用率,跨变体的历史数据不可直接对比}

## Method Notes

- 数据源与口径:已核=Scrunch 的 12–15 问/簇、Peec 的品牌词与非品牌词差异、SSRN 6652059 的子查询研究;未核或无出处=其余(见文件头)。施工图与来源清单见 [references/research/borrow-specs.md](../../references/research/borrow-specs.md) B3 节。
- 占位符:{brand}/{category}/{competitor}/{use_case}/{pain_point}/{segment};实例化后不得残留花括号进面板。
- 后缀体系:三变体 Include sources / According to experts / Cite your sources 可组合互换;风险组第四变体 According to reviews;D1 的 "based on trusted sources" 为竞品原文内嵌形式,视作等价变体。
- 禁编造:没有一手来源的数字不得写成官方口径;本库自定项一律标[推断]。数字缺失写 [要追加: 数据源]。
