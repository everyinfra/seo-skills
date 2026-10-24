# {答案式标题,例:"目标分 77(竞品均值 62+15,封顶 85):1,800–2,200 词 Comparison 型,必答 8 问、补 5 个覆盖差距、2 条禁区红线"}

> **模板性质**:交给写手的施工输入件,不是结果报告——数字全部为"实现目标"(来自竞品分析与 SERP 现场研究),产出落在页面本身与交稿后的 content_score.py 复测,不在本文件。
> **填充方式**:由 agent 结合 `scripts/content_score.py` 竞品分析与 SERP 现场研究填充;**所有数字必须来自真实分析,不许编**。数字缺失写 [要追加: 数据源]。
> **字段出处**:9 种内容类型和每型的附加考量取自 MarketMuse 的[简报类型文档](https://docs.marketmuse.com/documents/content-brief-examples/)(核对 2026-10-21);证据头、六件套、≥3 个竞品域名门槛、分数目标是**本套件口径**,没有逐条核对 Frase、Surfer、Clearscope 的厂商文档;意图相关性数字取自 Surfer 的厂商研究(见 2.1)。施工图见 [borrow-specs.md](../../references/research/borrow-specs.md) C2 节。

_For: {写手 · SME 复核人} · Date: {YYYY-MM-DD} · Market: {目标市场/语言} · Page: {新建或改版的 URL} · 内容类型: {9 型选 1,默认 Article} · Data pulled: {content_score.py 运行日 · WebSearch SERP 抓取日}_

> 多市场站点:逐市场各出一份本简报,不合并。市场差异规则见 [multilingual-workflow.md](../../references/overview/multilingual-workflow.md)。
> 占位符约定(实例化时全部替换,交付版简报不得残留花括号):`{{name}}`=命名占位符(取值必须能溯源到第 1 节证据头)· `{{x[]}}`=列表占位符(≥3 条,不足即证据不够)· `{}`=通用空位。

## The answer

{一段独立成立:目标内容分与依据(竞品均值+15,下限 70、封顶 85)、建议词数区间、意图+相关性提示、内容类型、必答问题与覆盖差距各几条、一句话核心打法(靠什么赢过均值竞品)、置信度(高/中/低+一句话依据)。只读这段的人不会错。}

## 1. 证据头(固定第一节,Frase 口径)

此节固定为简报正文第一节、不得省略或后移——设计动机(本套件口径):先摆证据再写简报,**倒逼真做 SERP 对比而非凭记忆写**。下表任一格为空,简报不得进入执行摘要阶段。

| 证据项 | 数值 | 口径/阈值 |
|---|---|---|
| 分析竞品数 | {{n_competitors}} | **≥3 个不同来源**,不足则不设评分目标(`content_score.py` 少于 3 个来源拒评,退出码 2;本套件口径) |
| 共现标题 | Top {{x}} | 竞品 H2/H3 共现频次排序,直接喂第 3 节大纲子标题 |
| 抽取问题 | {{y}} 条 | SERP PAA+竞品小标题问句,去重后进必答问题池 |
| 覆盖差距 | {{z}} 项 | 竞品高频覆盖而本站缺失的话题/问题,按差距排序 |
| 数据源与抓取时间 | {} | content_score.py 运行参数+SERP 查询与日期;过期(>30 天,本套件口径)须重做 |

竞品清单(不同域名,含当前排名):{{competitors[]}}

## 2. 执行摘要(借鉴 MarketMuse 简报结构)

### 2.1 分数与词数

| 项 | 值 | 口径 |
|---|---|---|
| 目标内容分 | {{target_score}} | `content_score.py` 目标行:min(max(竞品均值 {{avg}} +15, 70), 85)(本套件口径,不是搜索引擎规则) |
| 建议词数 | {{wc_range}} | 竞品词数中位数 ×0.7–1.3 的区间(`structure` 维度口径),写区间不写点值。Google 没有偏好的字数([有用内容指南](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)),按读者问题写完为止 |
| 目标意图 | {{intent}} | `--intent` 取 comparison / consequence / definition / instructional 之一;只影响输出里的相关性提示行,不改分值 |
| Personas | {{personas[]}} | 取自 [brand-records.md](../../references/content/brand-records.md) Audience 记录(含"不服务谁"),不凭空造人设 |

意图相关性表(第三方厂商研究):Surfer 在 10,000 个查询、每个查询前 100 条结果(共 1,000,000 条 SERP 记录)上,算 **Surfer 自家 Content Score** 与排名位置的 Spearman 相关,整体 0.28;按意图拆分如下([Surfer 研究](https://surferseo.com/blog/surfer-content-score-study/),核对 2026-10-21)。这是相关性,不是因果;分数是 Surfer 的公式,不是本套件的 `content_score.py`,所以只当优先级参考:

| intent | Surfer Content Score 与排名的相关 |
|---|---|
| consequence(例:what happens if…) | 0.2961 |
| definition(例:what is…) | 0.2705 |
| comparison / reason / exploratory | 0.22–0.23 |
| instructional / short fact | 0.19 |

### 2.2 必答问题(竞品已覆盖的)

来自证据头 {{y}} 条,按意图系数与 persona 相关性筛入;草稿漏答=term_coverage 与 facts_coverage 双失分。

| # | 问题 | 来源(哪个竞品/PAA 覆盖) | 指派大纲节 |
|---|---|---|---|
| Q1 | {} | {} | 第 {} 节 |

### 2.3 标题建议

- 排名实例(逐字照抄当前 SERP 头部真实标题,不改写):{{ranking_titles[]}}
- 须含词:{{title_terms[]}}(标题高频词+术语表重要度 ≥8 者)
- 公式与长度口径见 [title-formulas.md](../../references/content/title-formulas.md)。

### 2.4 内链(高相关锚文本 → 站内)

| 锚文本(描述性,不用裸 "read more") | 目标页(站内) | 放置节 |
|---|---|---|

### 2.5 外链(一手来源,非竞品)

外链指向一手来源,方便读者核对([有用内容指南](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)把清楚的来源列为让人信任的表现,核对 2026-10-21);当前查询的竞品域名一律不列。不为多一条外链而稀释正文;出站链接本身不是被引凭证([geo-evidence.md](../../references/content/geo-evidence.md))。

| 锚文本(描述性) | 目标源(一手、非竞争) | 放置节 | 支撑哪条断言 |
|---|---|---|---|

## 3. 大纲(每节固定六件套)

节结构与 H2–H4 层级参照 [content-structure-templates.md](../../references/content/content-structure-templates.md)。词数占比 ×建议词数 ≈该节词数。话题提及次数**封顶 2 次计分**(term_coverage 公式取 min(提及,2)),堆mentions 超 2 次不加分。

| # | 建议子标题 | 词数占比 %≈{{words}} | 必答问题 | 须提及话题 ×建议次数 | 内链 | 外链 |
|---|---|---|---|---|---|---|
| H2-1 | {} | {}% ≈{} 词 | Q{} | {话题}×2 · {话题}×1 | {} | {} |

每节一行;问题与话题 ID 从第 2.2 节与证据头贯通,不得新造未溯源话题。

## 4. 优化要求

### 4.1 术语表(glossary)

重要度 ≥8 的术语强制计入。重要度 = ceil(命中竞品数 ÷ 竞品总数 × 10),范围 1-10(`content_score.py` 口径)。"典型用量区间"=竞品词频四分位[推断]。

| 术语 | 重要度 1-10 | 典型用量区间 | 实际用量(交稿时填) | 是否入标题 | 来源(serp/ai/nlp) |
|---|---|---|---|---|---|

### 引用与增益纪律

> 不占 4.x 序号(4.3 首段三查等节号被 deep-research-protocol.md 按号外部引用,既有编号冻结);研究过程全口径(五轮检索/IGS 自检/反例检索)见 [deep-research-protocol.md](../../references/content/deep-research-protocol.md),发布闸 28-32 条同口径验收。

1. **具名引用格式**:每个非显然主张配 1 条"机构+日期"式内联引用(观点=[姓名]([职务],[机构])在 [日期] 的 [出处] 指出),非匿名转述。这是写法要求,不是收益承诺:GEO 论文报告的增益没有在 C-SEO Bench 的更广设置里重现([geo-evidence.md](../../references/content/geo-evidence.md) 第三节)。
2. **数字带来源**:每个主张簇配 ≥1 个"数值+来源+年份"格式数字,出处同句或紧邻,测量值与估算值分标。
3. **净新观点≥5(起步阈值)**:对照 ≥3 个竞品页面,不复述共识;净新断言型观点(有主体+可验证锚点)至少 5 条,不为凑数注水。5 是本套件起步阈值,尚未在站点数据上校准([deep-research-protocol.md](../../references/content/deep-research-protocol.md))。
4. **反例块**:每 3-5 个断言配 ≥1 条"例外:{什么条件下不成立},证据:{出处}",核心结论标 高/中/低置信度;找不到反例也写明"未找到反例(检索了 {查询×N},截至 {日期})"。

### 4.2 AI 事实清单(按 AI 回答频次排序)

由 `scripts/content_score.py --facts 事实.md` 导入(每行一条事实;行首可加 `D:` 点名声明或 `K:` 中性观察前缀);频次=该事实在 top20 SERP 与采样 AI 回答中的出现次数。本清单是 AI 轨 `facts_coverage`(权重 0.60)的计分项。

| 事实(一句话、自包含) | AI 回答频次 | 是否覆盖(交稿时填) | 所在节 |
|---|---|---|---|

### 4.3 首段三查(前 100 词内)

1. 首句点名主题(本页讲什么,一句话说清);
2. 含事实锚点(可验证的数字/日期/布尔断言,取自事实清单或 brand.yaml);
3. 先答案后展开——本套件口径:读者先拿到答案。有第三方观察称 AI 引用偏向页面前部,数字和局限见 [geo-evidence-bank.md](../../references/content/geo-evidence-bank.md);那是相关性观察,不是引擎规则,Google 也说不需要为 AI 功能专门改写([AI 功能](https://developers.google.com/search/docs/appearance/ai-features))。

### 4.4 结构目标

- H2–H4 用买家原词的自然变体,不强塞精确匹配(`content_score.py` 的 `keyword_variations` 维度,权重 0.10,本套件口径);
- ≥{{n_images}} 张图,每张 alt 含术语表术语(images_alt 0.05);
- schema 只标记页面上真实存在的内容(Google 的结构化数据[通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies));`content_score.py` 的 `schema_focused` 维度(1 种相关类型满分、>3 种扣分)是本套件口径,不是 Google 规则。选型先过 [deprecated-signals.md](../../references/technical/deprecated-signals.md) 替换决策表——FAQ、HowTo 富结果都已停展([日期](../../references/overview/facts.md#rich-results)),不为展示位新增这类标记;
- **加粗关键术语**:只加粗术语表内术语,不整句整段加粗(`bolded` 维度,权重 0.05,本套件口径)。

### 4.5 检查清单与复审频率

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 证据头完整、大纲六件套齐 | 人读第 1、3 节:证据头 5 项都有值;大纲每行 7 列都不空 | 通过:无空格。失败:任一空 → 简报不进执行 |
| 2 | 交稿后分数达标 | `python3 scripts/content_score.py --draft 稿.md --competitors c1.md,c2.md,c3.md --keyword 主词 --facts 事实.md --json`,读总分、AI 轨、SEO 轨及各维度 | 通过:总分 ≥{{target_score}}。失败:低于 → 按术语表「实际用量」列和事实清单「是否覆盖」列补缺口,不整体重写 |
| 3 | 事实清单覆盖 | 同上输出的 `facts_coverage`(D/K 分报) | 通过:覆盖 ≥{{coverage_target}}%。失败:低于 |
| 4 | 首段三查 | 同上输出的 `upfront_intent` 维度 | 通过:三查都过。失败:缺项 → 重写首段 |
| 5 | 宣称与术语过禁区 | 稿中每个数字、产品名对照 `brand.yaml` 与批准术语 | 通过:每个数字有对应 fact。失败:找不到 fact → 走缺口协议,不凭记忆写 |
| 6 | 句子写法 | `python3 scripts/ste_lint.py 稿.md --fail-on fail` | 通过:退出码 0。失败:退出码 1 |
| 7 | 买家原词覆盖(改版页) | `python3 scripts/question_align.py --gsc Queries.csv --page URL --fetch --json` 看 `flags` | 通过:无 `title_gap`、`lead_gap`。失败:出现 → 补词 |

复审频率:发布后 {30–60} 天首审[推断],之后按 decay 信号驱动——见 [content-decay-signals.md](../../references/content/content-decay-signals.md) 与 [content-refresh-playbook.md](../../references/content/content-refresh-playbook.md),不按固定日历空转。

## 5. 内容类型变体(9 型;只填选中型,未选型整行删除)

9 型和各型的附加考量取自 MarketMuse 的[简报类型文档](https://docs.marketmuse.com/documents/content-brief-examples/)(核对 2026-10-21);「≥3 条」「必填位置」这类数量和打回规则是本套件口径。

### Article(兜底默认)
- 未指定类型时按此型执行:直接按第 3 节大纲写,无类型附加件。
- 唯一附加:结尾节须回应执行摘要的一句话核心打法(结论先行收束)。
- 其余 8 型的类型行全部删除、不生效。

### Comparison
- 必先指定**实体清单**(≥2 个对比对象;是否包含本品牌须明示;实体名按 brand-records 批准术语书写)。
- 每个 comparison point(对比维度)各配 1 个必答问题(进第 2.2 节与大纲六件套)。
- 必须给出 **recommendation 结论**:"哪种情况选哪个";只罗列不推荐=不合格。

### FAQ
- 问题按主题分组(H3 为组);可指定问题清单(用户提供或取证据头抽取问题)。
- 每个答案独立成句、可被单独摘出引用(块级引用粒度)。
- schema 选型遵守第 4.4 节:不为富结果新增问答类标记。

### Guide
- 主体按**顺序分节**(章节有先后但每节不是单个操作步骤,"是什么→怎么选→怎么开始"型)。
- 结论必须含 **next steps**:读者读完下一步做什么,≥3 条具体动作。
- 与 How-to 的分界:Guide 分节可整节调序不影响可用性,How-to 不行。

### How-to
- 大纲必须是**顺序步骤**:每步一个步骤级子标题,依序编号(Step 1/2/3 或等价)。
- 每步至少配 1 个必答问题+须提及话题(进六件套)。
- 步骤乱序或并步=不合格;前置条件单列首节[推断]。

### Listicle
- 每个条目各配 1 个问题与一句观点("为什么入选"),不得只报名单。
- 条目排序规则必须声明(按 {} 排序),并保持全文一致。
- 每条目可独立摘出(AI 引用粒度为块级)。

### Local
- **必填具体位置**(城市+服务区,粒度=目标查询中的地点词);"全国/各地"不算位置。
- 位置必须出现在标题、H1、首段与至少一个 H2。
- 位置缺失=整份简报打回,不允许默认值。

### News
- MarketMuse 的 News/Events 简报列六项考量:timeliness(时效)· fact checking(事实核查)· quotations and sources(引语与来源)· implications and analysis(含意与分析)· background information(背景)· geographic and cultural context(地域与文化语境)。
- timeliness:正文标注时间线与更新时间;quotations and sources:引语须可归属、可验证的一手来源。
- 新闻 sitemap 与 Discover 口径见 [discover-news-seo.md](../../references/content/discover-news-seo.md);复审频率高于其他型。

### Product Review
- MarketMuse 的 Product Review 简报列 13 项考量:产品/服务细节 · 评价标准 · 个人体验 · 优缺点 · 背景 · 对比 · 用户证言与反馈 · 评测者资历 · 价格与价值 · 外观与设计 · 技术规格与功能 · 保修与客服 · 无障碍与易用性。逐项在大纲里找到对应小节,没有就写「不适用」并说明原因。
- 亲测体验必须是一手经验(E-E-A-T),禁"我们认为"冒充"我们测试"。
- 证言、价格与价值数字全部受第 6 节禁区约束(brand.yaml 可溯源)。

## 6. 禁区声明(起草前必读)

- **起草前先读 [brand-records.md](../../references/content/brand-records.md) 第五节使用规则**,两条红线缺一不可:
  1. **Offerings 记录的"不能宣称"黑名单**(如未取得的认证、未上线的能力——即便竞品页面都在宣称);
  2. **Execution 记录的 never-do(从不做的事)**。
- 草稿中所有数字/日期/布尔断言必须在 `brand.yaml` 找到对应 fact;找不到→先走缺口协议补齐,**不凭记忆写**。
- 产品与公司名一律用批准术语写法(官方大小写、已弃用旧名不回潮);persona 表述不越"不服务谁"边界。

## What could change this conclusion

- {竞品样本局限:n_competitors 偏小/SERP 个性化;同一查询换时点重抓,竞品集可能变}
- {分数目标是口径不是承诺:竞品均值随 SERP 波动,+15 和 70–85 区间是本套件口径,不保证排名;Surfer 自己的研究里 Content Score 与排名的相关也只有 0.28}
- {意图相关性是厂商研究的相关性,不是因果:只用于话题优先级排序,不构成"写这类意图必排名"的依据}
- {AI 回答频次随引擎版本漂移;复审前须重新导入 --facts 清单}
- {继承假设:词数区间取竞品中位数的 0.7–1.3 倍[推断];Google 没有偏好字数,区间只是写作量级参考}

## Method Notes

- 数据源与抓取时间:竞品分析=`scripts/content_score.py`(运行参数记于证据头)+SERP 现场研究(查询+日期)。数字缺失写 [要追加: 数据源],禁编造;`content_score.py` 没有关键词密度维度。Google 把关键词堆砌列为垃圾内容做法([垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)),所以不为密度堆词。
- 评分口径(`content_score.py` 源码,本套件口径):term_coverage=50 话题×min(提及,2)=满分 100;总分=0.5×SEO 轨+0.5×AI 轨;分档 0-33 弱 / 34-66 中 / 67+ 强;目标 70-85。交稿复测未达标时,按术语表"实际用量"列与事实清单"是否覆盖"列定位缺口,不整体重写。
- 字段出处:9 内容类型与各型考量=MarketMuse 文档(已核);意图相关性=Surfer 厂商研究(已核,相关非因果);三段式、六件套、证据头、≥3 个来源门槛、用量区间四分位、复审频率、Article 收束条=本套件口径,未逐条核对厂商文档。施工图与来源清单见 [borrow-specs.md](../../references/research/borrow-specs.md) C1/C2 节。
- 占位符:`{{name}}`/`{{x[]}}`/`{}` 定义见文件头;交付版不得残留花括号。
- 已知坑:新页收录和排名需要时间(用 Search Console 网址检查看收录状态),复测分数与排名信号是两回事;FAQ/HowTo 富结果均已停止展示(第 4.4 节),schema 选型一律先过 deprecated-signals.md 替换决策表。
