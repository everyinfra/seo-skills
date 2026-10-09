# GEO 的证据基础与实施边界

> 建立于 2026-08-29；一手来源复核于 **2026-09-04**。
> 目标是提高真实内容的可发现性、可理解性和可验证性，不把 HTML 形状、Schema、
> 域名后缀或自发转载次数包装成已知的 AI 排名公式。
> 本文件的证据约束优先于本包其他参考文件中的数字和字数建议。

## 一、先区分证据范围

- **产品官方说明**：可支持该产品的公开规则，不外推为所有 AI 搜索引擎的内部算法。
- **论文/可复现实验**：必须保留模型、任务、数据、时间、指标与对照条件；不能直接承诺某个站点的收益。
- **观察/相关性**：引用频率、爬虫访问、域名类别占比不等于因果加权。
- **营销转述**：找不到一手实验和方法时标「未证实」，不写进实施验收或预算收益。

Google 的[AI 功能技术说明](https://developers.google.com/search/docs/appearance/ai-features)
表示没有特殊的 AI Schema 要求。其[生成式搜索指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
进一步说明：无需为 AI 强行切碎内容、追逐不真实提及或专门改写；正常 SEO 与有价值的内容仍是基础。
**证据：一手产品文档；后者更新 2026-07-10，2026-09-04 读取；仅直接约束 Google Search。**

## 二、四条流行建议的取舍

### 1. 每段必须变成问题—答案并用 section/div 包裹？

**采用可读性，不采用强制格式或优先抽取保证。** 用户确实在问「怎么设置」「这个值是什么意思」时，
用清楚的问题标题、紧邻答案、稳定锚点和合理语义容器。说明须交代对象、适用范围、条件与例外；
定义列表、步骤、代码和真实比较表各有用途，不把每个段落都塞进 FAQ。

Google 上述指南明确不要求 chunking，建议语义 HTML 的理由包括帮助读者和辅助技术。
RAG 是检索增强生成方法，不自带「遇到 section/div 问答就优先引用」的统一排序规则。
**证据：Google 官方指导 + 工程判断；引用提升需另测，不能从 DOM 结构推断。**

### 2. FAQ Schema 铺满页面、放 head 就会优先引用？

**不采用。** 有真实 FAQ 时可保留与可见正文一致的一份语义声明，但不扩成隐藏答案库，
不把全部参数、促销语或段落标成 Question。schema.org 词汇存在与搜索产品支持是两件事。

- Google [2026-05-08 更新记录](https://developers.google.com/search/updates#faq-deprecation)：
  FAQ 富媒体结果自 **2026-05-07** 起停止展示；旧「仅医疗/政府站可展示」不再是当前规则。
- [FAQPage 词汇](https://schema.org/FAQPage)仍用于描述真实常见问答；不因此获得 AI 优先读取资格。
- [JSON-LD 说明](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)允许
  head 或 body 内的 script；位置不是权重开关。遵循框架当前实现与安全序列化规则。
- 验收：实际渲染的问答与 JSON-LD 逐条对应；无重复、虚构评分、不可见独家答案；
  用 Schema Markup Validator 查词汇合法性，用当前搜索文档查支持，不能把解析成功当作富结果资格。

**证据：一手产品文档/词汇规范，2026-09-04 读取。** 不沿用「Schema 抽取 16%→54%」这类数字作为通用实证：
能找到的只有二手转述，没有足够的一手实验方法。

### 3. .edu/.org 高 30%，.co/.io/.tech/.expert 更受 AI 青睐？

**不作为选域或迁站依据。** 这组固定增益缺少可核对的一手实验、引擎、样本与对照；
某类站点常被引用，不能排除内容、机构信誉与历史积累等混杂因素。

Google [关于新顶级域名的说明](https://developers.google.com/search/blog/2015/07/googles-handling-of-new-top-level)
指出新通用 TLD 与 .com/.org 同类处理，后缀中的关键词不带来排名优势。
这是一份 **2015 年的 Google 声明**，不是所有 AI 引擎或 .edu 的完整因果研究。
国家/地区域名的地域信号与「权威加权」也不能混为一谈。
**证据：范围明确的官方说明 + 数字未证实。** 保持现有品牌域名；迁站必须另有业务理由，并由站点负责人决定。

### 4. 同一信息在三个独立域名出现，引用权重翻倍？

**不采用固定阈值，也不把自发转载当独立验证。** 官网、品牌自己的 LinkedIn/Medium 文章即使域名不同，
仍可能是同一个发布者、同一个事实来源。真实的用户案例、独立测试和行业报道才增加不同的证据。

跨渠道发布应服务各自读者，标明作者、时间、原始来源、关联关系，增补该渠道需要的上下文；
错误事实要同步纠正，不能靠重复制造可信度。Google 上述指南明确反对追逐不真实 mentions。
**证据：Google 官方风险指导 + 来源独立性的工程判断；没有确认到「三域名翻倍」的通用规则。**
对外发布前由站点负责人确认；内容准备好不等于可以发布。

## 三、论文能说明什么，不能说明什么

[C-SEO Bench](https://arxiv.org/abs/2506.11097)（Puerto 等，v3 2025-10-20；
NeurIPS Datasets & Benchmarks 2025；有公开代码/数据）考察问答与商品推荐、每类三个领域，
并比较不同采纳率。在其设置中，多数受测内容优化方法无明显好处或出现负作用，
候选源在上下文中的排序更有效，采纳者增加时总体收益下降。

这是对泛化增益承诺的警示，**不是「所有 GEO 无效」「所有技巧收益必然归零」或「一手事实永远非零和」的证明**。
论文与其他实验结果不同时，先比较检索/生成阶段、模型、指标、基线和多参与者设置。
写得更清楚可以改善用户理解，但不要把这一工程价值冒充论文证明的排名提升。
**证据：一手同行评议研究；本轮核对摘要与版本，不宣称复现了作者实验。**

## 四、API 文档与多产品参考页的实施要求

逐产品、逐接口读取实际契约，不批量替换产品名来生成业务解释。公共渲染器与自动检查可以复用，
**产品事实与术语审查不能用模板代替**。每个展示的参数至少核：

1. 名称、必填/可选、具体对象；不同接口里同名的 keyword / id / url / sort 不假定同义。
2. 输入格式、对应产品的原生术语及对应关系；账号名、内部 ID、商品编号、地点标识等要分清。
3. 适用的接口或模式，默认值、单位、范围、允许值和兼容旧值；自由文本不得捏造枚举。
4. 参数影响什么、未开放什么；文档声明和实际行为冲突时先登记，不编造可用性。
5. 示例绑定具体产品和接口，格式示例标明不是成功样本；响应与统计不能伪造。
6. 返回字段的含义及空值/不完整边界，不能只解释通用参数、遗漏独有能力。

页面使用 heading + 紧邻说明、dt/dd、稳定的能力/参数锚点；从能力清单链接到准确参数，
同页不同接口的同名参数不得串链。FAQ 如保留，从同一份内容生成可见问答与 JSON-LD。
新增主题页必须有独立用户价值，不按关键词排列组合铺薄页；低重复率也不是 Google 垃圾内容政策的安全线。

验收分开记录：源码已核 → 生成物同步 → 实际 SSR/浏览器可读 → 在允许的测试环境中实际调用验证 → 上线后复核。
多语言版本逐语言由母语审校，不能把一种语言的数据就绪当作其他语言已完成。

## 五、发现与衡量

- 先核访问、索引指令、canonical、内链、正文与字段事实，再讨论 AI 引用。
- llms.txt 可服务确实消费它的开发者/工具；Google 上述指南明确 Search 不使用它。
  不为「AI 加权」默认增加 .well-known/ai.txt 或另一份 FAQ JSON，避免多份事实漂移。
- 搜索型、训练型、用户发起抓取型爬虫分开核策略；不为 SEO 擅自放开所有爬虫。
- 引用监测记录查询、语言/地域、产品/模型、时间、是否检索、引用 URL 与原始结果。
  回答提到品牌不等于引用来源；多条搜索链重合不等于多份独立证据。
- 固定问题集与取样协议，区分抓取、索引、展示、引用、点击和转化；使用重复观测、
  对照/分批发布减少混杂。改完本地 HTML 只能称工程验收，不能称排名或引用已提升。
- 外部监测失败、缺链、旧快照单独标明；不要把一次缺失解释为长期不可见。

## 六、维护规则

每条新增断言登记原始链接、日期、产品范围、证据类型及局限；无方法的百分比不进入实施要求。
官方文档过期时就地纠正旧建议，不能在尾部追加与前文冲突的规则。
吸收可核实的方法；不要把某个项目的运行快照（数据、截图、内部结论）复制进共享 Skill。

## 证据保鲜机制(qiaomu-seo 基建,百仓扫描批 4;解决"官方事实何时过期")

- **source-registry**:官方源 allowlist,每源标 `stability`(stable/mutable)与 `review_after_days`(365 或更短)——引用官方事实时先查登记;
- **知识四分类**:stable principle(稳定原理)/ current platform rule(现行平台规则,必须带源+复核日期)/ observed market state(观察到的市场态)/ hypothesis(假设)——套件所有断言按此四分归档;
- **覆盖台账八态**:discovered/selected/fetched/rendered/data-backed/failed/excluded/not checked——审计输出如实记态,不许"没查=通过";
- **Google 2026 指引事实**(双源核对):llms.txt 对 Google 排名既不帮助也不损害;无 AI 专用 schema;无理想 AI 页长;**规模化操纵 AI 回答违反 spam 政策**(2026-05-15 起 spam 政策适用于生成式 AI 回答);
- **算法更新台账**:`google-updates.json` 双区结构——`updates[]`(source 必须是 Google 自有域名)+ `unverified[]` 隔离区(第三方追踪器说法+primary_source_check;审计脚本不得编码未验证声明)+ last_verified。

## 完全装载:审计输出 schema/预注册标定/文件治理(百仓深扫)

**审计 JSON Schema**(qiaomu):顶层必填 7 项(schema_version/generated_at/scope/coverage/findings/action_plan/missing_evidence);scope.mode 7 枚举(advisory/page/template_sample/site_inventory/incident/migration/ai_search_extension);evidence_ref.kind 14 枚举(url/file/http/rendered_dom/search_console/server_log/crawl/serp/web_vitals_field/official_doc…)+observed_at;**finding 三轴:impact(5 档)/confidence(3 档)/effort(xs-xl)分立**;evidence_level=observed/inferred/missing 三分;**action 必须挂 finding_ids 且自带 verification**;source_review 必填 overdue_sources——过期来源显式暴露。
**预注册标定纪律**(respectaso):评分曲线必须实测拟合而非手调——327 官方值+90 负样本、30% holdout(按 crc32 哈希切分防泄漏)、Spearman/Pearson/MAE 三指标;**预注册闸门**(见数前固定:held-out Spearman≥0.25 且超旧模型);三版本号独立 bump 才触发历史重算;"NEVER hand-tune these: refit under pre-registered gates"。任何套件评分器的维护纪律。
**文件治理三法**(boraoztunc):①拒绝留痕——上游技能审计后拒绝理由全部写入 NOTICE("共享同一模板、描述不可区分→降低路由质量");②**一 trigger 一技能**(两个近同技能竞争同一 trigger 会降低路由);③采纳时纠错留痕(补 -webkit- 前缀/对齐参数,写明)。
