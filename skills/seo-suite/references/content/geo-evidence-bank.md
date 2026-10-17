# GEO 证据银行：可引用的案例数字、行业研究与论文

> 来源仓库：[amplifying-ai/awesome-generative-engine-optimization](https://github.com/amplifying-ai/awesome-generative-engine-optimization)（CC0），2026-10-09 读取。2026-10-11 增补：第六节调研批次（GEO 内容战略调研，交叉核查后口径）。2026-10-12 增补：第七节 2026-Q3 学术修正批次（20 视角学术调研登记，arXiv 摘要一手核读）。2026-10-17 增补：第七节第 1 条全文核读口径、第五节第 7 条（该研究的常见误读）、第八节 Schema/FAQ 对 AI 引用的独立效应（三条独立证据）。
> 证据约束遵循 [geo-evidence.md](geo-evidence.md)：本银行每条带链接与日期，但**证据分级决定用法**——
> 论文结论不能外推为站点收益承诺；厂商/代理商案例是营销转述，不进实施验收与预算预测；行业研究是观察/相关性，不是因果加权。
> 引用时保留口径（样本量、平台、时间、方法），数字冲突时并列呈现，不择优选边。

## 一、证据分级与引用规则

| 级别 | 类型 | 允许的用法 |
|---|---|---|
| A | 同行评议论文（arXiv/NeurIPS/ACM） | 引用其实验设定内的结论；注明模型、任务、指标与局限 |
| B | 平台规模化研究（Ahrefs/SEMrush/Conductor 等有方法说明的数据集） | 作为市场观察引用；注明样本量与时间窗 |
| C | 机构研究/媒体报道（Tow Center、Nieman Lab、Search Engine Land 转述） | 作为现象证据；注明一手出处 |
| D | 厂商案例/营销数字（Ramp、代理商案例） | 只作「有厂商报告了此结果」引用；标「未证实的营销转述」 |

## 二、案例数字库（D 级：厂商/代理商自报，引用时必须标注）

| 案例 | 数字 | 方法（自报） | 链接 | 日期 |
|---|---|---|---|---|
| Ramp（金融科技 SaaS） | 可见度 3.2% → 22.2%（约 7×） | Profound 平台追踪（厂商案例） | [tryprofound.com/case-studies/ramp](https://www.tryprofound.com/case-studies/ramp) | 来源未标注，2026-10-09 读取 |
| 制造业站点 | AI 流量 +2,300% | E-E-A-T 优化（Matt Diggity 案例） | [diggitymarketing.com/ai-overviews-seo-case-study](https://diggitymarketing.com/ai-overviews-seo-case-study/) | 来源未标注，2026-10-09 读取 |
| 汽车配件电商 | 月增长 +200% ⚠️2026-09 修正见第七节第 1 条 | Schema + llms.txt 实施 | [hedgescompany.com 案例集](https://hedgescompany.com/blog/2025/04/ai-search-optimization-case-studies/) | 2025-04 |
| Geneva Worldwide（翻译/口译） | AI Overviews 可见度 +115% | AI Overviews 优化（Boulder SEO Marketing 案例） | [boulderseomarketing.com](https://boulderseomarketing.com/seo-case-studies/how-this-translation-transcription-and-interpretation-company-dominated-ai-overviews/) | 来源未标注，2026-10-09 读取 |
| Go Fish Digital | 成功影响 ChatGPT 搜索结果 | 实时优化实验 | [gofishdigital.com](https://gofishdigital.com/blog/seo-case-study-how-we-influenced-the-chatgpt-search-results/) | 来源未标注，2026-10-09 读取 |
| AthenaHQ（厂商声明） | 70+ 客户、10× AI 流量 | 无公开方法 | [athenahq.ai](https://www.athenahq.ai/) | 厂商营销声明，勿引用为效果证据 |

**使用警示**：以上均为单一案例、无对照组、由利益相关方发布。写进方案时表述为「厂商报告的案例数字」，不得换算成客户预期。**2026-09 起另受 [arXiv 2609.35077](https://arxiv.org/abs/2609.35077) 约束**：页面级手段（FAQ 块/结构化数据/CWV）在合并数据中的正效应，加域名固定效应后**反转或归零**（辛普森悖论）——本表此类条目一律降权引用，见第七节第 1 条。

## 三、行业研究库（B/C 级：规模化观察）

> ⚠️2026-Q3 审计约束（统一适用于本节全部厂商追踪器数字，见第七节第 3 条，[arXiv 2609.06811](https://arxiv.org/abs/2609.06811)）：提示词集与权重共同定义各追踪器的「答案市场」，不必代表真实用户需求——跨追踪器数字禁止直接比较或合并，引用必须带厂商名+查询集口径+时间窗；LLM 判分的可见性分数连判分指令都是变量。

### 引用模式与平台差异

- **Conductor 2026 AEO/GEO Benchmarks**：13,770 域、21.9M 搜索、17M AI 响应（业界首个大规模分析）。ChatGPT 占 AI 引荐流量 87.4%；AI 引荐转化率为传统来源 2×。[conductor.com/academy/aeo-geo-benchmarks-report](https://www.conductor.com/academy/aeo-geo-benchmarks-report/)，2026 年报告，2026-10-09 读取。
- **Profound 引用模式分析**：Wikipedia 占 ChatGPT 顶部引用 47.9%；Reddit 在 Gemini/Perplexity 中高频出现。[tryprofound.com/blog/ai-platform-citation-patterns](https://www.tryprofound.com/blog/ai-platform-citation-patterns)，2026-10-09 读取（厂商研究，样本口径见原文）。
- **Perplexity 的 Reddit 依赖**：Reddit 占 Perplexity 引用约 46.7%。出处同上 + 仓库社区章节。

### AI Overviews 规模与波动（不同追踪器口径并列，勿合并成单一数字）

- SEMrush 2025 研究：2025-03 时 13.14% 查询触发 AIO（1 月为 6.49%），1,000 万关键词分析。[semrush.com/blog/semrush-ai-overviews-study](https://www.semrush.com/blog/semrush-ai-overviews-study/)
- Terakeet：2025-02 追踪到 AIO 覆盖 52% 查询。[terakeet.com](https://www.terakeet.com/)
- Ahrefs：2,500 万查询分析，AIO 出现率翻倍。[ahrefs.com/blog/ai-overview-growth](https://ahrefs.com/blog/ai-overview-growth/)
- Search Engine Land 汇总：AIO 峰值约 25%（2025-07），11 月回落至 <16%。[searchengineland.com](https://searchengineland.com/google-ai-overviews-surge-pullback-data-466314)
- **冲突提示**：52% vs 13.14% vs 25% 源于追踪面板与查询集差异；引用时必须带上追踪器名与月份。

### 点击、流量与引用行为

- Ahrefs：AIO 使首位点击下降 34.5%（2025-04 测量）；同方法 2026-02 复测为 ~58%——一年前后对照，勿单引旧值。[ahrefs.com/blog/ai-overviews-reduce-clicks](https://ahrefs.com/blog/ai-overviews-reduce-clicks/)，2026-10-09 读取；与 [discover-news-seo.md](discover-news-seo.md) 及 [intel-sources.md](../overview/intel-sources.md) 口径一致。
- Ahrefs：63% 网站收到 AI 流量（3,000 站研究）。[ahrefs.com/blog/ai-traffic-study](https://ahrefs.com/blog/ai-traffic-study/)
- Ahrefs 75K 品牌分析：传统流量指标只能解释约 5% 的 AI 引用行为（95% 未被解释——相关性研究，非因果）。[ahrefs.com/blog/ai-overview-brand-correlation](https://ahrefs.com/blog/ai-overview-brand-correlation/)
- Kevin Indig《State of AI Search Optimization 2026》：24% ChatGPT 响应未联网抓取；发布 <3 个月的内容被引用概率 3×。[growth-memo.com](https://www.growth-memo.com/p/state-of-ai-search-optimization-2026)，2026 年。
- SEMrush：ChatGPT Search 8,000 万点击流分析。[semrush.com/blog/chatgpt-search-insights](https://www.semrush.com/blog/chatgpt-search-insights/)
- Superprompt：2025 年 AI 引荐流量 +527%（400+ 站）。[superprompt.com](https://www.superprompt.com/blog/ai-traffic-up-527-percent-how-to-get-cited-by-chatgpt-claude-perplexity-2025)
- Seomator：4,100 万 AI 搜索结果分析（BrightonSEO 2025，覆盖 ChatGPT/AIO/Perplexity/Copilot）。[seomator.com](https://seomator.com/blog/ai-search-optimization-insights)

### 引用失败与信任（C 级）

- **Tow Center 研究**：AI 搜索引擎在超过 60% 的测试中未能产出准确引用。报道：[niemanlab.org（2025-03）](https://www.niemanlab.org/2025/03/ai-search-engines-fail-to-produce-accurate-citations-in-over-60-of-tests-according-to-new-tow-center-study/)。
- Pallas Advisory 逆向分析（2025-03-14）：ChatGPT/Perplexity 的来源选择与排序机制。[pallasadvisory.com](https://pallasadvisory.com/2025/03/14/inside-ai-search-decoding-how-chatgpt-perplexity-rank-your-content/)

### llms.txt 采用率

- **Rankability 采用追踪**：前 1,000 网站中 **9.3%** 已部署 llms.txt/llms-full.txt（2026-09 数据，按月更新；2025-06 基线为 0.3%/784+ 站）。[rankability.com/data/llms-txt-adoption](https://www.rankability.com/data/llms-txt-adoption/)
- 采用方：Zapier、Stripe、Cloudflare、Anthropic、Vercel、Supabase 等（[llms-txt.io 汇总](https://llms-txt.io/blog/companies-using-llms-txt-examples)）。
- 事件：Google 于 2025-12-03 将 llms.txt 加入 Search Central 文档又在同日移除（此前公开否定过该标准）。[omnius.so 报道](https://www.omnius.so/industry-updates/google-adds-llms-txt-to-docs-after-publicly-dismissing-it)
- 与 [geo-evidence.md](geo-evidence.md) 第五节一致：Google 已声明 Search 不使用 llms.txt；9.3% 采用率（2026-09，Rankability）仍属少数，说明它不是 GEO 必做项。

### 爬虫与基础设施

- Vercel：13 亿爬虫请求分析（AI 爬虫崛起）。[vercel.com/blog/the-rise-of-the-ai-crawler](https://vercel.com/blog/the-rise-of-the-ai-crawler)
- Prerender：AI 爬虫不执行 JavaScript（关键限制）。[prerender.io](https://prerender.io/blog/how-to-optimize-your-website-for-ai-crawlers/)
- **robots.txt 合规受控实验（本节首个 A 级实验）**：10 个带联网检索的 AI 助手 × 4 种 robots 条件 × 200 次实验——部分助手**不读取 robots.txt 即抓取受限内容**，或以**通用 UA** 抓取致无法归因；抓取行为与答案内容可背离。[arXiv 2607.14447](https://arxiv.org/abs/2607.14447)，2026-07；详见第七节第 4 条。

### 2025-2026 市场态快照（引用须带日期，过期即弃）

- Google 2025-12 核心更新：18 天滚动（12-11 至 12-29），AI 内容排序显著位移。[gsqi.com](https://www.gsqi.com/marketing-blog/google-december-2025-broad-core-update-analysis-findings/)
- Digital Third Coast（2026-01）：导航类 AIO 从 <1% 升至 >10%（2025 全年）；AIO 旁广告从 ~3% 升至 ~40%。[digitalthirdcoast.com](https://www.digitalthirdcoast.com/blog/ai-mode-use-trends)
- OpenAI 2026-01 宣布 ChatGPT 广告：广告与回答分离、不影响回答内容。[openai.com](https://openai.com/index/our-approach-to-advertising-and-expanding-access/)
- 仓库 Footnote 预测（转述级）：传统搜索量 2026 年 -25%、2028 年 -50%；LLM 流量 2027 年底超 Google。ChatGPT 占搜索流量 ~4.33%；用户 prompt 平均 23 词（传统搜索 4.2 词）。

## 四、论文库（A 级：每篇一行结论）

### 奠基与基准

| 论文 | 一行结论 | 链接 | 时间 |
|---|---|---|---|
| GEO: Generative Engine Optimization（Princeton/Georgia Tech/Allen Institute，KDD 2024） | 9 种优化 tactic（引用来源、统计数据、引文等）在其实验中带来最高约 40% 可见度提升——GEO 概念的原始出处 | [arXiv 2311.09735](https://arxiv.org/abs/2311.09735) / [ACM DL](https://dl.acm.org/doi/10.1145/3637528.3671900) | 2023-11 提交，2024 出版 |
| C-SEO Bench（NeurIPS 2025 D&B） | 跨任务/领域/采纳率基准发现**多数现行 GEO 内容方法基本无效**，传统 SEO 仍相关——与 GEO 原文 40% 增益构成直接张力，详见 [geo-evidence.md](geo-evidence.md) 第三节 | [OpenReview](https://openreview.net/forum?id=oTeixD3oZO&) | 2025（v3 2025-10-20） |

### 知识冲突与检索

| 论文 | 一行结论 | 链接 | 时间 |
|---|---|---|---|
| ConflictBank | 740 万「主张-证据」对数据集，刻画 LLM 何时信任外部检索内容而非训练记忆 | [arXiv 2408.12076](https://arxiv.org/abs/2408.12076) | 2024-08 |
| ConflictingQA | 面对矛盾信息时，LLM 倾向按**来源相关性**而非学术语气选择信息 | [arXiv 2402.11782](https://arxiv.org/abs/2402.11782) | 2024-02 |
| When Search Meets LLMs | Search4LLM 与 LLM4Search 管线综述，标出 AI 搜索架构中的可优化点 | [arXiv 2407.00128](https://arxiv.org/abs/2407.00128) | 2024-07 |

### 对抗与安全（引用时用于风险警示，不得作为操作手册）

| 论文 | 一行结论 | 链接 | 时间 |
|---|---|---|---|
| GASLITE | 仅 0.0001% 语料投毒即可实现密集检索 top-10 劫持——AI 检索系统的漏洞面 | [arXiv 2412.20953](https://arxiv.org/abs/2412.20953) | 2024-12 |
| Adversarial SEO for LLMs | 隐藏文本可使品牌在 AI 回答中的提及提升 2.5×——操纵手法的存在证明正当优化的必要性 | [arXiv 2406.18382](https://arxiv.org/abs/2406.18382) | 2024-06 |
| Dynamics of Adversarial Attacks on LLM-Based Search | 黑帽/白帽 GEO 竞争的博弈论模型 | [arXiv 2501.00745](https://arxiv.org/pdf/2501.00745) | 2025-01 |
| Ranking Manipulation for Conversational Search | 经文本结构化的页面内 prompt injection 可操纵对话式搜索排序 | [arXiv 2406.03589](https://arxiv.org/abs/2406.03589) | 2024-06 |
| Persistent Pre-Training Poisoning | 预训练期投毒具有长期持续性——训练数据更新时保持新鲜权威内容的另一理由 | [arXiv 2410.13722](https://arxiv.org/abs/2410.13722) | 2024-10 |

## 五、已知冲突与引用纪律

1. **GEO 40% vs C-SEO Bench 无效**：同为本银行收录的一手研究，结论相反。引用任一方必须同时提示另一方及其实验条件差异（检索/生成阶段、模型、指标、多采纳者设定）。**⚠️2026-Q3 第三方裁决（倾向怀疑侧）**：45 篇批判综述（[arXiv 2607.14035](https://arxiv.org/abs/2607.14035)，2026-07-15，见第七节第 2 条）判定——GEO 原文增益「在其实验设定内有效，但以来源已存在于固定上下文为前提」，既不证明自然可发现性也不证明持续流量效应；综述语料内**无任何已评技术显示稳定、纵向、跨平台的因果效应**。引用 GEO 40% 时按怀疑侧口径并读。
2. **AIO 覆盖率（52% / 25% / 13.14% / <16%）**：不同追踪器、不同月份、不同查询集；只允许带口径引用，禁止取最大值制造紧迫感。
3. **厂商案例 vs 同行评议**：Ramp 7× 与 C-SEO Bench「多数方法无效」并存——方案里两者都要出现，分别标注证据级别。
4. **llms.txt**：9.3% 采用率（2026-09，Rankability）+ Google 官方不使用 = 不作为实施必选项（与 geo-evidence.md 一致）。
5. 本银行条目读取于 2026-10-09（第六节批次为 2026-10-11 调研+交叉核查；第七节批次为 2026-10-12 调研+arXiv 摘要一手核读）；行业研究类数字的保鲜期按 [geo-evidence.md](geo-evidence.md)「证据保鲜机制」（快变事实 60 天内重查）执行。
6. **引用半衰期双口径**：SSRN 中位 4.5 周（第六节第 7 条）与 Profound 中位 11 天并记两说，样本与「引用」定义不同，禁止择一写成「AI 引用寿命」通值。
7. **arXiv 2609.35077 的常见误读（2026-10 中文社媒转述实例，2026-10-17 对照原文核出）**：①把「最佳匹配段中位深度 0.36」读成「AI 只读页面前 36%、读到答案就停」——0.36 是作者按相似度算出的最佳匹配段位置的中位数，不是引擎实际摘取的段落，一半页面比它更靠下；论文没有任何关于引擎「从顶部读、读到某处停下」的测量。②把「FAQ 段 β=+0.07」读成「停止写 FAQ 块」——FAQ 段是论文里最大的页面级清单信号，只是很小。③把 domain fixed effects（按网站域名控制）译成「控制领域深度」。④把转述者自报的「结论从第三段挪到第一段，两周后引用约 2.4 倍」当成研究结论——那是无对照、无数据的自述。引用该研究一律回 arXiv 原文，并带上「B2B SaaS、四引擎、只含被引页、观察性」四个限定（第七节第 1 条）。

---

## 六、2026-10-11 调研批次（GEO 内容战略调研，交叉核查后口径）

> 本批 14 条来自 2026-10-11 内容战略定向调研，经交叉核查后定级；**8 条相对初始口径降级使用**（逐条带降级标注，原因见本节末核查说明）。分级规则仍按第一节；落地条目对照 [multilingual-geo-evidence.md](../research/multilingual-geo-evidence.md)（其【调研 2026-10】标签即指本批）。

### A 级：同行评审（4 条）

1. **检索漏斗瓶颈——引用位是稀缺资源**：实测 Sonar 检索后仅读取约 10 页、最终引用 3–4 个；Gemini 92% 响应零外部链接。来源：[The Attribution Crisis in LLM Search Results（arXiv 2508.00838）](https://arxiv.org/abs/2508.00838)，期刊版 Data & Policy 2026；2025-08 提交，2026-10-11 核查。**使用注意**：结论限于论文测定的引擎快照（2025 上半年），证明的是「读了不一定引、多数回答根本不引」的机制，不可外推为各引擎现值——用于解释「被收录 ≠ 被引用」。
2. **引用行为优化增益 +30–40%（GEO 原始论文，附方法学限定）**：引用来源/统计数据/引语类改写在其实验中带来约 30–40% 引用指标提升（同第四节奠基条目）。来源：KDD 2024，[arXiv 2311.09735](https://arxiv.org/abs/2311.09735)；2026-10-11 复核加限定。**核查后降级标注**：测量基于 GPT-3.5 构建的**模拟生成引擎** + **固定文档上下文**，且**仅测引用阶段**指标——不是真实引擎端到端流量；外推到现役引擎须与第五节第 1 条（C-SEO Bench 张力）并读。
3. **被引源约 16% 带 AI 生成证据**：四家生成式搜索引擎审计（712 条真实人类查询 × 4 引擎）发现约 16% 被引来源检出 AI 生成痕迹。来源：[Synthetic Sources? Auditing Generative Search Engine Citations（arXiv 2605.23684）](https://arxiv.org/abs/2605.23684)；2026-05，2026-10-11 核查。**使用注意**：口径是「检出 AI 生成证据」非「内容全部为 AI 生成」；引用时保留 712×4 样本框。
4. **低资源语言 RAG 退化**：49 语言领土争议基准显示检索与生成质量随语言资源量下降显著退化——小语种引用池更浅、可用源更少。来源：[BordIRLines（ACL 2025 Findings）](https://aclanthology.org/2025.findings-acl.219/) / [arXiv 2410.01171](https://arxiv.org/abs/2410.01171)；2026-10-11 核查。**使用注意**：任务域是文化敏感事实问答，非商业查询；只支撑「低资源语言内容稀缺 = 唯一可用源机会」的方向判断（multilingual-geo-evidence.md U5）。

### B 级：大样本实测（5 条）

5. **AI 引用源比自然结果新鲜 25.7%**：AI 引用 URL 平均年龄 1,064 天 vs 自然结果 1,432 天（1,700 万 AI 引用，7 个 AI 助手汇总）。来源：[Ahrefs](https://ahrefs.com/blog/do-ai-assistants-prefer-to-cite-fresh-content/)，2025-07-28。**使用注意**：7 平台均值会掩盖引擎差异（Perplexity 新鲜度偏好更高，见 [geo-platform-differences.md](geo-platform-differences.md) 第二节）；与该文件第五节同一数字互链，勿拆成两处结论。
6. **新闻源仅占 AI 引用约 9%，头部通吃**：新闻域名仅占全部引用约 9%；OpenAI 模型新闻引用中 reuters.com 占 22.8%、apnews.com 12.2%（36.6 万条引用审计）。来源：[News Source Citing Patterns in AI Search Systems（arXiv 2507.05301）](https://arxiv.org/abs/2507.05301)；2025-07，2026-10-11 核查。**使用注意**：Reuters 22.8% 是「新闻引用内部份额」不是「全部引用份额」，两数勿混；时效选题预期管理见 multilingual-geo-evidence.md U6。
7. **AI 引用半衰期中位 4.5 周**（⚠️ 核查后降级：SSRN 单源预印本）：AI 引用活性中位 4.5 周减半，ChatGPT 最快（3.4 周）。来源：[SSRN 7344201](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7344201)，2026。**使用注意**：与 Profound 官方中位 11 天（[2026-09，88.3 万页研究](https://www.tryprofound.com/blog/the-half-life-of-an-ai-citation-is-11-days)）**并记两说不选边**——样本与「引用」定义不同（见第五节第 6 条与 multilingual-geo-evidence.md U7）。
8. **ChatGPT 非英语会话 43% 子检索用英语**（⚠️ 核查后降级：工具商遥测）：1,000 万+ ChatGPT 提示的 fan-out 分析——非英语提示的子检索 43% 以英语执行；78% 非英语会话至少含一次英语子检索。来源：[Peec AI](https://peec.ai/blog/chatgpt-searches-in-english-even-when-you-don-t)，2026-02-12；[SEJ 转述](https://www.searchenginejournal.com/chatgpt-search-often-switches-to-english-in-fan-out-queries-report/567811/)。**使用注意**：样本为工具商客户面板非全量流量；引用必须标「工具商遥测」。
9. **日文提问 26% 引用落 .jp 域，英文提问仅约 1%**（⚠️ 核查后降级：翻译厂商研究）：同一问题用日文提问时 26% 被引源在 .jp 域，英文提问时约 1%。来源：[Weglot](https://www.weglot.com/blog/ai-search-citations-language-country)，2026-09-08。**使用注意**：Weglot 为翻译服务商、研究服务其业务叙事；方向结论（提问语言切换引用池）与第 4/8 条一致故收 B 级，但具体百分比引用须带厂商名。

### C 级：机构/厂商（2 条）

10. **翻译有效但机翻降权（两分法）**：翻译有效 = Weglot 130 万引用分析：有目标语言版本的站在无该语言版本的查询中 AIO 可见性 +327%、被引 3.83×（⚠️ 核查后降级：Weglot 委托研究，非因果——自营样本只有相关性，不能写进效果承诺）；机翻降权 = Google 政策级：automated transformations 列入 scaled content abuse 打击范围（官方政策口径），但 **LLM 引擎侧对机翻的直接降权暂无一手证据**。来源：[Weglot](https://www.weglot.com/blog/multilingual-seo-ai-visibility)，2026-08-10。**使用注意**：+327%/3.83× 只能表述为「翻译商报告的相关性」；落地两分法见 multilingual-geo-evidence.md U4。
11. **量产蹭热点反例（AInvest）**（⚠️ 核查后降级：孤立个案、无对照、事后归因）：AI 量产财经新闻站约两个月从 27.5 万涨至 960 万月点击，遭 Google 垃圾更新（scaled content abuse）处置跌至约 90 万——量产蹭热点是「先吃流量后挨刀」的反例。来源：SEO 圈复盘（[Rise and Fall of AInvest](https://www.youtube.com/watch?v=RpgOKUO_SyI)，2025-09；[August spam update 复盘](https://www.youtube.com/watch?v=_n5_GiljJP0)）。**使用注意**：证明的是「不可持续」，不是「必然被罚」；不作为任何量产策略的可行性证据。

### 中文区（3 条）

12. **3·15 曝光「发布 2 小时被引用」= 黑产警示，非 GEO 功效**（核查后性质重释：功效叙事 → 风险警示）：2026-03-15 央视 3·15 晚会曝光：虚构「Apollo-9 智能手环」软文发布约 2 小时即进入主流大模型推荐榜——该数字证明的是**投毒漏洞与违规操作的存在**，不是「正规 GEO 两小时见效」。来源：[36 氪](https://m.36kr.com/p/3724411683895943)、[新华网追踪（2026-04-08）](https://www.news.cn/digital/20260408/c1ef4fac451c456f934fd97e333723fd/c.html)。**使用注意**：对外方案严禁引用为功效证据；与第四节 GASLITE 等对抗条目同属风险警示层。
13. **国内 GEO 团体标准 2026-04 立项，明确防范语料投毒**：《生成式引擎优化（GEO）可信信息传播与信息生态治理规范》2026-04-10 通过立项评审，为国内首部 GEO 团体标准，重点防范「语料投毒」等风险。来源：[立项报道（2026-04-28）](https://www.sohu.com/a/1015501700_122526825)、[新浪财经（2026-04-17）](https://finance.sina.com.cn/jjxw/2026-04-17/doc-inhuveqw2190232.shtml)。**使用注意**：立项 ≠ 发布，条款未定稿；引用写「已立项的团体标准」，勿写「已生效标准」。
14. **中文引擎平台归属只作定性：元宝 ≈ 腾讯系（公众号+腾讯新闻+企鹅号/ima），豆包 ≈ 字节系（抖音+头条号）**。来源：[chinese-ai-search-guide.md](chinese-ai-search-guide.md)、[markets/zh.md](../markets/zh.md)（2026-10-09 二轮核验）。**核查后降级标注**：引用池份额的量化拆分（如「头条 35.2%/知乎 21.8%」）为单源疑同源、已降级备考——**对外一律定性表述，不携带存疑百分比**。

### 本批核查说明

本批 14 条中 **8 条（第 2、7、8、9、10、11、12、14 条）在交叉核查后相对初始口径降级使用**——一句话原因：其一手来源为工具商遥测、翻译商委托研究、单一预印本、孤立个案或被误读性质（「功效证据」实为「黑产警示」），数字与允许用途按第一节分级规则收紧。未降级 6 条（1、3、4、5、6、13）为同行评审、方法透明的大样本数据或官方事实。本批读取于 2026-10-11，保鲜按 [geo-evidence.md](geo-evidence.md)「证据保鲜机制」执行。

---

## 七、2026-Q3 学术修正批次（20 视角学术调研，2026-10-12 入库）

> 本批 11 条来自 [pipeline-completeness.md](../overview/pipeline-completeness.md) R6「学术修正」登记（20 视角深扫 2026-10-11），论文摘要全部经 arXiv 一手核读（2026-10-12）。第 1–3 条为**修正条目**——银行既有条目已按其回改（第二/三/五节内 ⚠️ 指引回指本节）；修正不删除旧数字，**数字保留、口径收紧，引用时新旧并读**。分级规则仍按第一节。

### 修正条目（3 条，直接约束本银行旧口径）

1. **页面级 AEO 手段的「正效应」在域名固定效应下反转或消失（辛普森悖论）**：约 200 万条真实 LLM 引用（ChatGPT/Claude/Google AI/Gemini 四商业引擎 × 6 个月）× 1 万页（19 个 B2B SaaS 工作区），60+ 特征经九方法共识框架（混合效应回归+域名固定效应、双重机器学习、稳定性选择 Lasso、FDR 校正、GAM、时间外推复测）。FAQ 块、结构化数据（Schema）、Core Web Vitals 在合并数据中的正效应，加域名固定效应后**反转或归零**；主导变量是**提示-内容对齐**（工作区提示词集与页面 token 的 Jaccard 重叠，β=+0.37，95% CI [0.33, 0.41]）与**域名级 AI 权威**（平均绝对 SHAP ≈ 最强非对齐页面特征的 6 倍）。来源：[What Drives Citations in Production Large Language Models?（arXiv 2609.35077）](https://arxiv.org/abs/2609.35077)，2026-09-28 提交，2026-10-12 一手核读。**使用注意**：观察性研究（非实验）、样本限于 B2B SaaS 域、预印本——结论是「合并正效应可被域名级差异解释」，**不是**「Schema/CWV 有害」；正确读法是把投入排序从页面级标记转向提示对齐与域名权威。第二节 Schema+llms.txt 行与使用警示已按本条回改。
   **全文核读补充（2026-10-17，[HTML 全文 v1](https://arxiv.org/html/2609.35077v1)）**：
   - **样本只含被引 ≥2 次的 URL**（10,042 页），因变量是 log₂(1+引用次数)：研究的是「被引多少」，**回答不了「会不会被引」**。主模型限品牌自有页与竞品页（N=4,015 页 / 297 个域），第三方页面另算。
   - **摘要与正文口径不同**：摘要写清单类信号「反转或归零」，正文分项是 FAQ 段 β=+0.07、TLDR/BLUF +0.05、作者简介 +0.02（加内容深度控制后消失），三项都只在第三方页面上测得；Schema 无显著独立效应（品牌页 JSON-LD 抽取失败，Schema 结论只覆盖第三方页面）；真实用户 CWV 与 Lighthouse 分数加域名控制后不显著。页速在合并数据里其实是**负相关**（大品牌页面偏慢、被引又多），加域名固定效应后归零或翻转。准确读法：FAQ 段是「微小正值，低于 0.10 的小效应门槛」，Schema 和 CWV 是「无独立效应」，都不是「有害」。
   - **页面级可动空间有上限**：只放域名时 R²=0.320，全部特征 R²=0.450，页面级增量 ΔR²=0.13；扣除域名后剩余的页面级方差约占 14%。
   - **跨期预测不可迁移**：用 2026-04-01 前的引用训练、预测 4 月引用，样本外 r²=0.018。对齐系数跨期同号（+0.61 → +0.34），页龄系数跨期翻号（+0.323 → −0.136），作者判为不稳健。
   - **其他系数**：页面类型里定价页 +0.39、榜单测评页 −0.12；页长 +0.13；标题-提示相似度 +0.09（按被引提示计算，有循环成分，作者自称是上界）；对齐系数在自有品牌页 +0.77、竞品页 +0.31。
   - **位置**：作者按与被引提示的语义相似度找出每页的「最佳匹配段」，其位置中位深度 0.36（0=页顶，1=页底；对 0.5 均匀分布的 Wilcoxon 检验 p<10⁻²⁰）。这是**作者算出的最佳匹配段，不是引擎实际摘取的段落**，且有一半页面的最佳匹配段在 0.36 以下更深处。与 Kevin Indig「44.2% ChatGPT 引用来自页面前 30%」同向，见 [geo-platform-differences.md](geo-platform-differences.md) 第五节。
   - **口径边界**：Perplexity 因样本量小被排除；提示词由该公司分析师为 19 个 B2B SaaS 工作区手写（受本节第 3 条「提示词集定义答案市场」约束）；数据集不公开，只公开分析管线；作者是 AEO 代理商 Discovered Labs。该公司的研究摘要页（[discoveredlabs.com/research/what-drives-ai-citations](https://discoveredlabs.com/research/what-drives-ai-citations)）把清单类信号写成「measurable gains」，和论文摘要的「反转或归零」不一致——**引用以 arXiv 论文为准，不引摘要页**。常见误读见第五节第 7 条。
2. **GEO 原文 ~40% 增益仅在固定上下文设定内成立；无已评技术显示稳定纵向跨平台因果效应**：45 篇 GEO 研究（2023-11~2026-07 发表窗）批判综述：奠基论文增益在其实验设定内有效，但**以来源已存在于固定上下文为前提**——既不证明自然可发现性、也不证明持续流量效应；最可复现的杠杆是**主题相关性与上下文位置**，通用启发式跨平台迁移性差，竞争会侵蚀个体收益，面向引用的改写可能损害检索。综述语料内的总判定：**已被检索的内容可因果地改变其被引/被用，但没有任何已评技术显示对自然可发现性或下游行为的稳定、纵向、跨平台因果效应。**来源：[Optimizing Visibility in Generative Engines: A Critical Survey of GEO (2023-2026)（arXiv 2607.14035）](https://arxiv.org/abs/2607.14035)，2026-07-15 提交，2026-10-12 一手核读。**使用注意**：第五节冲突 #1 已按本条记第三方裁决（倾向 C-SEO Bench 怀疑侧）；引用 GEO 40%（第四节奠基行/第六节第 2 条）时必须并读本条——三家证据链现为「原文 40% ↔ C-SEO Bench 无效 ↔ 综述裁向怀疑侧」。
3. **提示词集与权重共同定义「答案市场」——厂商可见性分数不可比**：GEO 可见性分数聚合来源出现/引用/提及，而提示词语料选择被评估的情境、权重决定其相对重要性，两者共同定义一个**不必代表真实用户需求**的「答案市场」；提示措辞本身可改变检索、竞争源与生成答案；若用 LLM 判分，判分指令即可改变同一答案的得分。框架给出情境标注/提示表述/执行条件/权重/判分规则五要素，并要求在权重未知时报告「可容许分数集」（区分数据兼容值与权重惯例敏感值）。来源：[Measuring GEO Visibility: Prompt Corpora Define the Answer Market（arXiv 2609.06811）](https://arxiv.org/abs/2609.06811)，2026-09-06 提交，2026-10-12 一手核读。**使用注意**：方法论/批判论文、无新实验（作者自陈普适效度待评估）；对本银行第三节全部厂商追踪器数字与第六节工具商遥测条目（第 7/8/9/10 条）构成统一审计约束——第三节头部已加注；自家 citation_panel 采样协议同样受此约束（查询集先冻结、带口径、不跨面板比较）。

### 全新入库（6 条，A 级）

4. **部分 AI 助手不读 robots.txt 抓取受限内容/用通用 UA——爬虫基础设施首个 A 级受控实验**：10 个带联网检索的 AI 助手，先识别各自真正产生抓取行为的配置并记录抓取时暴露的 User-Agent，再跨 4 种 robots.txt 条件（全允许/全禁止/仅允许该助手专属 UA/仅禁止该专属 UA）做 200 次实验，以服务端日志+页内密钥区分「真实抓取」与「用户可见答案」。结果跨助手差异显著：部分按预期遵守允许/禁止模式，另一些**未请求 robots.txt 即访问受限资源**或**使用通用 UA 致无法归因**；抓取与答案可背离（抓了不展示、该抓没抓）。来源：[Do Generative AI Assistants Respect robots.txt?（arXiv 2607.14447）](https://arxiv.org/abs/2607.14447)，2026-07-16 提交（v2 07-19），2026-10-12 一手核读。**使用注意**：助手名单与版本是 2026-07 快照，合规状态随版本变化——支撑「robots.txt 不是 AI 抓取的可靠执行边界」的方向判断（敏感内容须用认证/服务端控制），不支撑对任一具名助手的永久指控；与第三节爬虫小节互链。
5. **agent-ready 设计使浏览器 agent 任务成功率 49.3% → 89.3%**：同一电商原型站（目录/价格/库存/购物流程全同）的「人导向基线」vs「agent-ready 版」受控对照：3 个浏览器 agent（GPT-4.1、Gemini-2.5 Flash、Grok-4 Fast）× 5 任务 × 300 次运行——严格成功率 **89.3% vs 49.3%**（PASS 134/150 vs 74/150），PARTIAL 结果 43 → 3，平均步数 9.31 → 6.49；增益最大的是商品详情抽取、比较、多约束选择。框架三维度：机器可读性/语义清晰（agent 可解释）、动作线索（agent 可执行）、证据与时效信号（决策可靠）。来源：[Designing Agent-Ready Websites for AI Web Agents（arXiv 2607.12056）](https://arxiv.org/abs/2607.12056)，2026-07-13 提交，2026-10-12 一手核读。**使用注意**：单一原型站+3 个 agent+电商任务的**初步证据**（作者自陈 preliminary），非现场 A/B——89.3% 是「同一站改版前后」不是「任意站可达水平」；用于论证 agentic 商务设计改版的优先级与预期量级。
6. **对话内引用捕获呈递增复利，10 轮内复利比可超 2×（理论）**：多轮人机信息寻求是闭环——agent 的回答改变用户信念、从而改变下一问、进而改变检索。早被引用的来源显著更可能再次被引用（机器侧：历史条件化检索；人侧：追问转向被捕获来源）。Pólya 罐过程证明：单轮评估下反馈项恒为零，GEO 累计收益随对话长度**超线性**增长；模型推演示例中反馈项可超过直接项、**10 轮内复利比 >2**，单轮与轨迹排序仅弱一致（Kendall τ=0.4）。来源：[Conversational Capture: A Trajectory-Level Framework for Evaluating GEO in Multi-turn Human-Agent Interaction（arXiv 2609.40069）](https://arxiv.org/abs/2609.40069)，2026-09-30 提交（调研口径：HAI'26 理论论文），2026-10-12 一手核读。**使用注意**：>2× 为**模型推导演示值**非实测——正确用法是「单轮可见性监测系统性低估早位引用的长期价值」，不能写成「早被引 = 收益翻倍」；对采样监测协议的含义是首答被引比单轮份额更值得跟踪。
7. **GEO 痕迹检测器 F1 0.944；真实检索结果中 GEO 优化页占比约 8.9%**：GEOFlagBench（3,200 条网页内容 × 400 查询 × 4 域 × 8 个 GEO 优化器家族）；Intervention-Paired Training 使 ModernBERT 检测器 F1 **0.862 → 0.944**、最差组准确率 0.725 → 0.883。全管线部署于 1,000 条真实用户查询的 Google Search 与 Gemini 接地检索结果（10,095 页）：整体 GEO 优化痕迹占比估计 **8.90%**，2026 年内修改过的页面中达 **16.36%**。来源：[GEO-Flag: Detecting and Measuring GEO-Optimized Web Content（arXiv 2608.16824）](https://arxiv.org/abs/2608.16824)，2026-08-17 提交（v2 08-20），2026-10-12 一手核读。**使用注意**：8.9%/16.36% 是「检出 GEO 痕迹」的估计，受检测器召回上限约束——正面读法是规范化 GEO 内容在真实语料中仍是少数，反面是检测面在快速上升（2026 修改页近两倍于整体）。
8. **CHASE：对 LLM 排序信号的反复优化会降解内容生态质量**：受控仿真框架（以排序作可见性代理，六域验证 rank-citation AUC 0.853±0.093）——创作者反复向固定 LLM 排序信号改写文档 20 轮后，**质量-排序对齐度在全部六个域下降**（Spearman ρ 变化 -0.107 ~ -0.018，均值 -0.068）：越贴近排序特征画像的文档与独立评审的文档质量越错配；随机目标对照证明这是「向排序激励适应」而非「反复改写」本身所致；生态动态强域依赖。来源：[CHASE: How Content Ecosystems Are Reshaped When Ranking Is the Only Target（arXiv 2608.30466）](https://arxiv.org/abs/2608.30466)，2026-08-31 提交，2026-10-12 一手核读。**使用注意**：仿真研究（20 轮/六域口径）——结论是种群层面的长期风险（全员向排序信号优化 → 系统性质量错配），不约束单站单轮优化的短期收益；与第六节第 11 条（AInvest 量产反例）同读，作「以排序信号为唯一目标」策略的反证。
9. **记录越薄的冲突主题，引擎幻觉越多——薄记录 = GEO 信息战结构暴露面**：28 场冲突 × 5 家头部答案引擎 × 5,460 个答案对照实证记录评分：可检索记录越薄，引擎越多发明事实、错记归属与计数；薄记录不只诱发幻觉，更构成**误/虚假信息的结构性暴露面**——最易被 GEO 扭曲以偏置引擎回答。对 1,048 个被引来源站的分析显示 GEO 来源优化已在发生，国家-党派数字捕获尚属初期但增长快。来源：[How AI LLM Engines Shape the Global Conflict Information Environment（arXiv 2607.14197）](https://arxiv.org/abs/2607.14197)，2026-07-15 提交（v2 2026-10-02），2026-10-12 一手核读。**使用注意**：任务域是冲突/和平议题（YMYL 极端区），具体幻觉率不可外推；方向结论（薄记录 → 高幻觉 → 高可操纵性）可迁移到「查询集稀疏的小众商业域」——小众域被引既是机会也是被操纵审查更弱的市场；与第四节对抗条目同属风险警示层。

### 回声补录（2 条，银行此前未收）

10. **「best-of」清单页吃掉约 21% 引用（⚠️ B 级：GEO 厂商测量研究）**：Ranqo 平台 100K+ 提示响应 × 100+ 品牌（2026-03~05）：引用给出时约 78% 落公司官网；非公司源中 YouTube 领先（Reddit、编辑媒体、Wikipedia 其后）；**被引最多的内容形态是排名型「best-of」清单，约占全部引用 21%**；首次可见性呈三级品牌阶梯（全球知名 73% / 中坚 44% / 长尾 11%，每级差约 30pp）；情感正负翻转频率是提及有无的 **6.7 倍**。来源：[Generative Engine Optimization at Scale: Measuring Brand Visibility Across AI Search Engines（arXiv 2606.20065）](https://arxiv.org/abs/2606.20065)，2026-06-18 提交，2026-10-12 一手核读。**使用注意**：数据来自 GEO 厂商（Ranqo）自家追踪面板，[citability-scoring.md](citability-scoring.md) 文献分级注记同此定性——引用必须带厂商名与样本框，不进实施验收；「best-of 清单是高杠杆形态」与第六节第 6 条（头部通吃）方向一致；三级阶梯与第七节第 1 条「域名级权威主导」互证。
11. **结构特征工程自称 +17.3% 引用率（回声条目，必须与第 1 条并读）**：GEO-SFE 把内容结构拆为宏观（文档架构）/中观（信息分块）/微观（视觉强调）三层，六家主流引擎实验：引用率 **+17.3%**、主观质量 +18.5%，自称「结构优化是 GEO 的基础组件」。来源：[Structural Feature Engineering for GEO: How Content Structure Shapes Citation Behavior（arXiv 2603.29979）](https://arxiv.org/abs/2603.29979)，2026-03-31 提交，2026-10-12 一手核读。**使用注意**：预印本；其「页面级结构特征 → 引用」正效应主张与本节第 1 条（2609.35077：结构清单类合并正效应在域名固定效应下消失/反转）构成直接张力——两者实验设定不同（受控实验页 vs 生产引用观测+域名固定效应），**引用 +17.3% 时必须并读第 1 条**，不得单独写成「结构调整提升引用」的通用结论。

### 本批核查说明

本批 11 条（修正 3 / 全新 6 / 回声 2）论文摘要均经 arXiv 一手核读（2026-10-12），入库依据为 pipeline-completeness.md R6「学术修正」登记与 20 视角学术调研；受影响旧条目（第二节 Schema+llms.txt 行与使用警示、第三节头部审计约束与爬虫小节、第五节冲突 #1 与 #5）已加 ⚠️ 指引回指本节。保鲜按 [geo-evidence.md](geo-evidence.md)「证据保鲜机制」执行——本批均为 2026 年提交的预印本/会议论文（最早 2026-03、最晚 2026-09），60 天内应复查版本号与 venue 变化。

---

## 八、2026-10-17 批次：Schema/FAQ 对 AI 引用的独立效应（生产证据补强）

> 起因：中文社媒转述 arXiv 2609.35077 时出现失真（第五节第 7 条），回一手原文全文核读（第七节第 1 条补充），并补齐两条独立证据。三条证据的设计不同（域名固定效应观测 / 匹配双重差分 / 按查询聚类的 GEE），结论同向：**通用 Schema 对 AI 引用没有可测的独立效应**。分级规则仍按第一节。

1. **（B 级）新加 JSON-LD 的页面，AI 引用没有可测提升**：Ahrefs 用自家爬虫的 HTML 历史找出 2025-08 至 2026-03 间新加 JSON-LD 的 1,885 个页面，每页配 3 个此前引用水平相近、从未加过 JSON-LD 的对照页（不同域，约 4,000 页），比较加标记前后各 30 天的引用。主分析为匹配双重差分：Google AI Overviews −4.6%（统计显著，但两组在加标记前已同步下滑，作者不归因于 Schema）、AI Mode +2.4%（不显著）、ChatGPT +2.2%（不显著）；另做 t 检验、事件研究、换窗口 DiD，方向一致。同一研究的 600 万 URL 合并观察里，被引页带 JSON-LD 的比例约为未被引页的 3 倍——这正是混杂相关。来源：[We Tracked 1,885 Pages Adding Schema. AI Citations Barely Moved.](https://ahrefs.com/blog/schema-ai-citations/)（Louise Linehan、Xibeijia Guan，2026-05-11 发布），2026-10-17 一手核读。**使用注意**：样本是 2025-02 已有 100+ 次 AIO 引用的页面，结论只覆盖「已经在候选集里的页面」，对尚未被抓取、被引的页面有没有帮助，这项研究回答不了；所有 Schema 类型合并估计，没有拆 FAQ、Product；观察窗 30 天；加 Schema 的页面常同时改了别的东西。
2. **（B 级，⚠️ 降级：单作者小样本预印本）通用 Schema 无效应，填了具体属性的 Product/Review Schema 是唯一例外**：ChatGPT（GPT-4o 联网）与 Gemini（1.5 Pro 接地）× 75 个商业查询，730 条引用、1,006 个页面（同查询的 Google 前 10 作对照）。合并分析得到 Schema 与被引显著**负**相关（OR=0.546），作者查明是对照组构造的伪影；改用按查询聚类的 GEE 后，Schema 存在与否（OR=0.678，p=.296）、实体丰富度、Schema 与查询的对齐度均不显著。最强预测项是 Google 自然排名（每降一位被引几率约 −24%，第 1 位 43% → 第 7 位 5%）。例外：填了价格、评分、规格等字段的 Product/Review Schema 页被引率 61.7%，通用类型 41.6%（p=.012），在 DR≤60 的域上更明显。来源：[Does Schema Markup Predict AI Citation?（SSRN 6284518，Kurt Fischman，2026-02-20 写成，Zenodo 预印本）](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6284518)，2026-10-17 摘要一手核读。**使用注意**：样本小、引擎版本旧；61.7% vs 41.6% 是观察相关，作者的解释（结构化事实弥补弱权威）未经实验。只支持「产品页把价格、规格写进 Product/Offer 字段值得做」，不支持「Schema 普遍提升引用」。
3. **（C 级）实时抓取阶段，主流 AI 助手只读可见 HTML**：searchVIU 建了一个测试页，把 8 个价格分别放在可见 HTML、JS 渲染、纯 JSON-LD、隐藏 Microdata/RDFa 等位置，2025-10-30 向 ChatGPT、Claude、Gemini、Perplexity、Google AI Mode 提问：没有一个系统读出只存在于 JSON-LD 或隐藏标记里的价格；Gemini 是唯一读出 JS 渲染价格的。来源：[Schema Markup and AI in 2025: What ChatGPT, Claude, Perplexity & Gemini Really See](https://www.searchviu.com/en/schema-markup-and-ai-in-2025-what-chatgpt-claude-perplexity-gemini-really-see/)，2026-10-17 一手核读。**使用注意**：单页、单日、厂商自测；只测「直接抓取」这一阶段，作者自己写明走搜索索引的产品（AIO、Copilot）仍可能在索引阶段用到 Schema。它支撑的是「关键事实必须写在可见正文里」，不是「Schema 对索引无用」。

**合并口径（本节三条 + 第七节第 1 条）**：

- 不为 AI 引用新增或扩写 Schema（含 FAQPage）。已有的、与可见正文同源的保留：它还服务知识图谱、语音、实体识别等消费者，删掉没有收益（处置同 [deprecated-signals.md](../technical/deprecated-signals.md) FAQPage 行）。
- 可见的 FAQ 段落可以写（2609.35077 里它是最大的页面级清单信号，但只有 +0.07），前提是回答真实问题，见 [citability-scoring.md](citability-scoring.md)「FAQ 是条件件不是标配」。
- 页面级投入顺序：提示-内容对齐（买家原话进标题、首段和小标题）→ 页面类型（定价页、对比页）→ 清单类信号。站外的域名权威排在所有页面级动作之前（第七节第 1 条：SHAP 约 6 倍）。
- 产品页例外：价格、规格、评分等事实写进 Product/Offer 字段，同时在正文可见；证据只有第 2 条一项小样本。
- 本批读取于 2026-10-17，保鲜按 [geo-evidence.md](geo-evidence.md)「证据保鲜机制」执行；第 2 条是预印本，60 天内复查有无正式发表版本。
