# GEO 采样 prompt 库(prompt-bank)

> **模板性质**:常驻输入件库,不是一次性报告模板——表格行实例化后喂给 `citation_panel.py` 建立/扩充采样面板;结论产在第 7 节指向的周报/月报,本文件不产出任何数字。
> **数据来源**:Scrunch(stage 框架+初始集配方)/ Peec(品牌词独立分组警告、GSC top 词转问句公式)/ Otterly(fanout 六类型、引擎展开量基准、Citation Synthesis 第 5 步)三家**官方口径**;施工图见 [references/research/borrow-specs.md](../../references/research/borrow-specs.md) B3 节(来源清单在其文末)。标注纪律与全库一致:【官方】=一手口径,[推断]=本库自定并注明。

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

用法:前缀 + 空格 + 任一基础模板(主矩阵或 R 组)= 一条新 prompt,固定后缀照抄官方原文追加在句尾。前缀措辞[推断自定:persona 角色词必须出现,其余可改];后缀为官方逐字。

| Persona | 前缀[推断] | 固定后缀(官方原文) |
|---|---|---|
| CMO | As a CMO evaluating this quarter's tech spend, | Respond with sources and direct claims first. |
| Founder | As a founder scaling a small team, | Respond with sources and direct claims first. |
| SEO Lead | As an SEO lead reporting organic growth, | Respond with sources and direct claims first. |
| PMM | As a product marketing manager building a competitive battlecard, | Respond with sources and direct claims first. |

**限额提醒(硬规则)**:persona fan-out 后执行数 = 基础 prompt 数 × persona 数(4)翻倍计入采样限额——主矩阵 20 条 × 4 = 80 次/轮,再乘引擎数与采样次数;预算紧张时只对比较段(C 组)做 fan-out,认知/决策段保持基础形态。

## 4. Stage 配方(Scrunch 官方)

- stage 框架【官方】:awareness / consideration / conversion / loyalty;本库映射:认知=A、比较=C、决策=D(loyalty 暂留空,待扩)。
- **初始集配方【官方】**:5 awareness + 3 consideration + 2 decision,共 10 条起步——恰好满足 citation_panel.py 的 prompts≥10 下限;示例选法:A1/A3/A5/A7 + C2/C4/C5 + D1/D2(可替换同漏斗其他条)。
- **每 cluster 12-15 问【官方】**:一个 topic 组(簇)内问句数落在 12-15,不足先补簇内问法,不急着开新簇。
- **品牌词 prompt 必须独立分组【Peec 官方警告】**:句面含 {brand} 字面的 prompt,Visibility 恒 100%(答案必然提到被问的品牌),混入非品牌 prompt 会污染指标——品牌词组、R 组、persona 变体组各自单独统计、单独汇报。
- 扩量节奏【Peec 官方】:起步集稳定后,10-20 条 awareness + 20-30 条 consideration 连续跑 30 天再扩。

## 5. Fanout 六类型(Otterly 官方)

引擎不会只检索你问的原句——先展开成子查询群。写 prompt 与做内容都要按展开后的语义对齐:

| 类型 | 一句定义 | 示例 |
|---|---|---|
| reformulation | 引擎把原 prompt 改写成等价问法再检索 | "best crm 2026" → "top rated crm software this year" |
| related | 引擎自行补问原问的相邻子问题 | "best CRM for small business" → "how much does a CRM cost per seat" |
| implicit | 沉默内容缺口:决策必需但用户没问出口的信息,引擎替用户补查 | 问 "best CRM" 时引擎补查迁移成本、隐藏费用等没人明说的考量 |
| comparative | 引擎自动把被问实体放进对比集 | "Is {brand} any good?" → "{brand} vs {competitor} vs {competitor}" |
| entity expansion | 简称/实体被展开为完整实体+属性再检索 | "Acme" → Acme(AI CRM 厂商)的公司实体卡片与 sameAs 属性 |
| personalized | 同一 prompt 按用户画像/会话历史被改写 | 同一问法,初创创始人视角与企业 CMO 视角得到不同展开 |

- **引擎展开量基准【官方】**(单条 prompt 平均展开子查询数):Perplexity 12-15 · ChatGPT 6-10 · AI Mode 8-12 · AIO 4-8。
- **注记**:选源发生在第 5 步 Citation Synthesis——内容优化对象是展开后子查询能命中的语义覆盖,不是原始 prompt 的字面词匹配;展开行为分析走 `scripts/fanout_analysis.py`。

## 6. 统计纪律

1. **单 prompt 单次不可靠**:LLM 非确定性,同一问法两次回答可不同——任何单点数字不下结论(n<3 = 掷硬币,与 citation_panel.py 同口径)。
2. **按 topic 分组 + 周聚合**:先 cluster 级周聚合,再下钻 prompt 级;不逐 prompt 逐日比较。
3. **比较类 prompt(C 组)10 次采样即可估 visibility**;非比较类同样攒到 n≥10 再看趋势。
4. **3 次采样取多数**(majority 状态)并**标方差**;n≥3 才进报告(citation_panel.py 稳定判据:Wilson 95% CI 跨 0.5 = unstable)。

## 7. 使用说明(接线)

- **喂给面板**:`python3 scripts/citation_panel.py init --brand X --prompts-file 本文件`——脚本直接解析第 1/2 节表格的"模板"列(占位符须先实例化);旧版本无该参数时,把模板列实例化后另存单列 CSV(表头 `prompt`)走 `--prompts`。
- **GSC top 词 → 问句转换公式【Peec 官方】**:"What are the best [category] for [persona]?"——GSC 有展现/点击的 top 非品牌词逐条套此公式生成新 awareness prompt;品牌词路由到第 4 节独立组。
- **结果消费**:周报 [../monitor/ai-visibility-weekly.md](../monitor/ai-visibility-weekly.md)、月报 ai-visibility-monthly.md;引擎行为差异见 [references/content/geo-platform-differences.md](../../references/content/geo-platform-differences.md)。

## What could change this conclusion

- {时效:句内年份词("in 2026")每年需滚动更新,过期年份词测到的是引擎旧索引行为而非当前可见性}
- {口径漂移:引擎展开量基准为 Otterly 2026 口径,随引擎版本漂移,建议季度复核一次}
- {自定项:persona 前缀措辞、R 组第四后缀变体、A2/C7 补位条目为[推断]自定,非官方逐字——换措辞即换自变量}
- {措辞即自变量:source-seeking 后缀变体本身影响引用率,跨变体的历史数据不可直接对比}

## Method Notes

- 数据源与口径:Scrunch(stage 框架、5+3+2 初始集、每 cluster 12-15 问)/ Peec(品牌词独立分组警告、GSC 转问句公式、扩量节奏)/ Otterly(fanout 六类型、引擎展开量基准、Citation Synthesis 第 5 步)均为官方口径,施工图与全部来源见 [references/research/borrow-specs.md](../../references/research/borrow-specs.md) B3 节。
- 占位符:{brand}/{category}/{competitor}/{use_case}/{pain_point}/{segment};实例化后不得残留花括号进面板。
- 后缀体系:三变体 Include sources / According to experts / Cite your sources 可组合互换;风险组第四变体 According to reviews;D1 的 "based on trusted sources" 为竞品原文内嵌形式,视作等价变体。
- 禁编造:未见于官方文档的数字与"官方原文"不得标注【官方】;本库自定项一律标[推断]。数字缺失写 [要追加: 数据源]。
