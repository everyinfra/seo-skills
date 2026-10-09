# GEO 的证据基础与实施边界

> 建立于 2026-08-29；一手来源复核于 **2026-09-04**。
> 目标是提高真实内容的可发现性、可理解性和可验证性，不把 HTML 形状、Schema、
> 域名后缀或自发转载次数包装成已知的 AI 排名公式。
> 本文件的证据约束优先于本包其他参考文件中的数字和字数建议。
> 可引用的案例数字、行业研究与论文清单见 [geo-evidence-bank.md](geo-evidence-bank.md)（awesome-generative-engine-optimization 仓库吸收，2026-10-09）。

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

预注册标定的完整展开(官方数据锚点法/crc32 按 term 切分/保序回归 PAV/三版本号重算/twin-row 一致性/新评分器上线十项清单):见 [scoring-calibration.md](../research/scoring-calibration.md)。

## 官方指引与内容政策增量(claude-seo 深读,2026-10-09)

来源:[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-geo/references/google-ai-optimization-guide.md`、`skills/seo-agentic/references/vendor-matrix.md`(该仓自标"一手来源综合,2026-09-23 复核")。

1. **Google AI 优化指南五条"不需要做"**(2026-05-15 Search Central 博客公布,文档更新 2026-07-10):不需要创建 llms.txt 或 AI 专用标记文件;不需要为 AI 把内容切块(chunking);不需要用特定措辞/长尾变体改写;不需要追逐博客/论坛/视频里的不真实提及;不需要为 AI 功能过度投资结构化数据。Google 的定位原话:"优化生成式 AI 搜索就是优化搜索体验,因而**仍是 SEO**"——AEO/GEO 被视为同一工作的别名。与本文第二节四条取舍一致,可作官方出处引用。
2. **Google"第三方 SEO 工具"文档**(2026-06-05):任何工具都不能保证排名;第三方工具**无法访问 Google 内部排名数据**;Google 不背书厂商;Search Console 是权威一手源。套件评分器输出报告时照此声明"启发式,非引擎内部信号"。
3. **Who/How/Why 测试**(Google E-E-A-T 指南配套):Who——读者期望处有署名,YMYL 主题必须有作者背景页;How——尤其 AI 辅助内容,读者会问就披露过程;Why——为帮助人而非吸引点击。**YMYL 2025-09 QRG 扩展到政治/社会议题**。自警四信号:按目标字数写作(没有这种字数)、无专业知识只为流量进入领域、伪造发布日期新鲜度、为"新鲜度"批量翻新内容。
4. **Merchant Center 两条可执行 AI 内容要求**(有具体执法面):AI 生成产品图必须带 IPTC `DigitalSourceType: TrainedAlgorithmicMedia` 元数据;AI 生成的产品标题与描述须在 feed 中单独指定并标注为 AI 生成。QRG §4.6.5(规模化内容滥用)/§4.6.6(低努力主内容)是对应罚则面。
5. **厂商数字红旗**(vendor-matrix 明令不引用):Cloudflare 的 markdown token 削减数字为厂商来源;WebMCP"token 效率"百分比只追溯到营销帖、无可复核基准;WebArena 等 agent 基准测的是**模型**不是站点质量;无受控公开研究把 accessibility-tree 质量或 WebMCP 与 agent 任务成功率挂钩——全部按假设处理。
6. **agent 客户端事实的保鲜纪律**(可借鉴的方法):该仓 vendor-matrix 每行带来源分级 P(一手)/S(二手)/C(冲突),60 天以上行引用前必须重查;`CHECKED_ON` 常量与文档同次提交更新——快变事实"只在带日期的表里活,不散落正文"。

## 证据阶梯、测量纪律与知识治理执行面(qiaomu-seo 深读 2026-10-09b)

来源:[joeseesun/qiaomu-seo](https://github.com/joeseesun/qiaomu-seo) `references/{ai-search,performance-measurement,execution-sampling,knowledge-freshness}.md` + `scripts/validate_{audit,knowledge}.py`。

### AI 搜索证据六级阶梯(ai-search.md;替代笼统的"AI 可见性")

`eligible`(按平台文档条件可访问)→ `retrieved`(系统确实使用/呈现了来源)→ `cited`(显式引用带链接)→ `mentioned`(实体/品牌被点名)→ `recommended`(进入优选短名单)→ `converted`(可测的下游用户行为)。**任何阶段不得坍缩成"AI 可见性提升"一句话**——mention≠推荐、一次引用测试≠未来答案、检索爬虫≠引用爬虫。观察协议必记:查询集及选择理由、provider+产品 surface、日期/市场/语言/设备/登录态、答案+引用+被引 URL+提及措辞+推荐态;结论重要时重复观测或独立复核。手工 prompt 检查按"抽样观察"归档,不按"排名报告"归档。OpenAI 三 bot 显名分立:`OAI-SearchBot`(自动搜索发现)/`GPTBot`(训练)/`ChatGPT-User`(用户触发,不一定遵守同套 robots);Perplexity 以 `PerplexityBot` 为搜索爬虫,bot 身份影响结论时核已公布 IP 段。

### 知识分类修正:实为五类(knowledge-freshness.md)

前批记"四分类",实际该仓是五行表:stable principle / current platform rule / observed market state / **estimate(第三方指标:关键词量、流量、外链、难度——必须带具名 provider+方法+日期,永不作为 ground truth 呈现)** / hypothesis。套件引用任何工具数字时按 estimate 类处理。

### 官方文档冲突处理四则 + 特性生命周期

冲突时:①对具名 surface 取"更新且更具体"的产品文档;②两个都可能是真的时不抹掉更宽的旧陈述(例:生成式 AI 专属报告与"生成式 AI 流量计入 Web 总报告"可并存,先核当前 property 再断言);③显式写出 rollout/账号可用性/地区/报告范围的不确定性;④不把产品公告直接转成普适实施要求。生命周期六态:`experimental/limited/supported/unsupported/deprecated/removed`;**分层命名**——某搜索特性废弃后 Schema.org 类型可能仍合法、SC 维度可能过渡期仍在,声明时指明是哪一层变了。

### validate_knowledge.py 的执行面(比前批概念记录更硬)

- stability 实为三档:stable/**mutable/volatile**(volatile 是最快过期档);每源必填 `reviewed_at`+`review_after_days`(正整数),逾期默认 warning,**`--strict-stale` 才 fail**——CI 可分档执法;
- URL 强制**绝对 HTTPS**且域名必须在 `allowed_official_domains` 内;source id 与 URL 双重去重;
- **`deprecated_claim_patterns` 禁用词机制**:把"已知过期说法"写成字符串模式,对 SKILL.md + references/*.md 做 casefold 子串扫描,命中即 fail——过期知识的淘汰从"靠自觉"变成"可执行词表";
- 脚本自我声明边界:不抓网、不证明源内容未变,只查结构/域名政策/重复/逾期——validator 也诚实标注自己的证明力。

### validate_audit.py 的执行面(schema 之外的硬约束)

- `missing evidence` 级 finding 的 status 只能是 `warning/not_checked`,**不得是 pass 或 fail**——"没查"永远不能伪装成结论;
- `observed/inferred` 级 finding 必须附 `evidence_refs`(kind+ref),空引用即 fail;
- `template_sample` 模式缺 coverage.limitations → 警告;**六类 mutable 类目**(structured_data/commerce/image_search/video_search/ai_search/policy)存在 finding 而 `source_review` 缺失 → 警告——把"平台规则易变"编码进执法;
- action 悬空引用(指向不存在的 finding id)、重复 finding/action id、非 advisory 模式空 targets,全部 fail。

### 测量与取证的证据纪律(performance-measurement.md + execution-sampling.md)

- **CWV**:field 数据定级、lab 数据诊断,两套不可互证;Lighthouse 分数不证明 field CWV、排名或业务影响;当前阈值(LCP 2.5/4.0s、INP 200/500ms、CLS 0.1/0.25,P75)在长期标准里使用前须重开官方源;CrUX/SC/RUM/PSI/Lighthouse 覆盖的 URL、人群、时段、设备可能全不同。
- **Search Console 数据边界**(引用 SC 数字前的自查单):匿名查询进总量不进表;加维度会掉数据;API 返回的是内部限额下的 top 行而非穷举;页/媒体级聚合口径不同;average position 是聚合诊断量不是固定排名;**禁止用总量减过滤表,把差集当"完整隐藏关键词集"**。
- **采集五层,用最轻够用层**:repo/config(路由/元数据/sitemap 逻辑)→ HTTP 静态响应 → 渲染后 DOM → 一方工具(SC/日志/CrUX)→ 当前 SERP 观察;静态与渲染证据是**不同工件**,finding 必须注明由哪层支撑。重跑清单记日期时区/市场/语言/设备/登录态/工具版本/失败与限流/输出校验和;**不存凭据、原始 cookie、私有查询串**。
- **变更验证四里程碑**:`implemented`(源码改+测试过)→ `deployed and observable`(线上 HTTP/渲染输出已变)→ `processed by search platform`(抓取/索引/canonical/增强证据已反映)→ `outcome observed`(合格窗口后的效果数据)。**只有第四里程碑支持效果声明**;部署或重抓成功不是排名/流量/转化成功——本地改完 HTML 只能称工程验收。
- **SEO 实验七要素**(可逆且多页面可比时):一个可证伪假设+机制、防交叉污染的处理单元(页/模板组)、看结果前定好人群/排除/分配/基线窗、主指标+护栏+最小实用效应+观测窗+停止规则、避免模板/内链/内容/埋点同时改(除非整包即处理)、监控实现均等与重抓进度、**正/负/零/不定结果全部报告,不把噪声改成胜利**;无可信对照的 before/after 只是观察性证据,迁移/事故类用变点证据+竞争解释并降置信度。
