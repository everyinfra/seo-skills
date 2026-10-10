# 可引用性打分（内容能否被 AI 引用）

> 建立于 2026-10-09。框架参考 [zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) `geo-citability` 技能与 [jianruntech/geo-score](https://github.com/jianruntech/geo-score) rubric v1.1，按本套件证据约束改写。
> 打分衡量的是内容**形状**是否便于引用，不是引用结果本身——好分数不保证被引。

**用哪套(入口决策)**:快速评估用 **AIV**(第二节五支柱 100 分,读档即可打);深入研究用 **CORE-EEAT 80 项基准**(配 `scripts/core_eeat.py` 机械化,GEO/SEO 双分+veto 封顶 59);域名级评级用 **CITE 40 项**(配 `scripts/cite_domain.py --input json`,veto BLOCK)。三套可叠:域名 CITE → 站点 AIV → 内容 CORE-EEAT。

## 一、五维块级打分（0–100）

| 维度 | 权重 | 看什么 |
|---|---|---|
| 答案块质量 | 30% | 段落是否直接回答一个可提问的问题；先结论后展开 |
| 段落自含性 | 25% | 不依赖上文代词/省略也能独立成立（抽取后仍可读） |
| 结构可读性 | 20% | 标题层级、列表、定义先行；H2/H3 层级使引用概率 2.8x（AirOps 2025） |
| 统计密度 | 15% | 有源数字的密度；引用统计 +33% 可见性（KDD 2024） |
| 独特与原始数据 | 10% | 自有一手数据/图表/表格，别处没有 |

**最优被引段落形态**：134–167 词、自含、富事实、定义先行（"X 是……"）。低于 60 词的信息块建议重写或并入邻近段。

**覆盖度**：整页打分 = 得分 >70 的块占比。单块高分不够，要看页面整体的可抽取密度。

## 二、AI 就绪度分层审核（站点级，100 分参考 geo-score v1.1 结构）

**Reachable（15 分）**——进不来一切免谈：

- robots 对 10 个主流检索 UA 的政策（显式 allow 5 / 仅无禁 3 / 禁 0）
- 活体探测：发真实 bot UA 访问，403/429/5xx/挑战页 = 拦（robots 宽松但 WAF 拦截是常见暗坑）
- SSR/首屏可解析
- **任一门为 0 → 总分封顶 40%**（进不来就谈不上可引用）

**Understandable（22 分）**：sitemap+lastmod 4 / llms.txt 5 / Organization+WebSite schema 6 / BreadcrumbList 3 / 页型 schema 4

**Content Citability（35 分）**：自含答案段 9 / 标题匹配提问意图 7 / 新鲜度 6（dateModified 必须与可见日期一致，造假扣全分）/ 有源统计 7（最高档=可点击可核验）/ 具名可验证作者 6（署名解析到真实身份页）

**Brand Credibility（18 分）**：第三方目录 4 / 独立提及 4 / Knowledge Graph 实体 4 / sameAs 可解析 3 / 视频多模态 3

**Answer Fit（10 分）**：抽取型内容 4 / 覆盖 10 个真实买家问题 4 / 中文引擎就绪 2

分档：Leading 83+ / Solid 66+ / Growing 51+ / Early 31+ / Not started。

## 三、方法纪律（本套件强制）

1. **抽样协议**：恰好 8 个 URL——主页、2 个产品页、2 个文档页、3 个近期内容页。不多不少，保证跨站可比。
2. **三态标注**：每项 scored / unobservable / not_applicable。不可观测不等于 0 分。
3. **测量与整改分开报告**：就绪度分数与实测引用表现是两个数，不合并成一个"AI 可见度"。
4. **引用数据带不确定度**：报告实测引用时附 95% CI 和样本量 n。
5. 不承诺分数与被引的因果关系——分数是整改优先级工具。

## 四、作者信号（E-E-A-T 的可验证子集）

可机器验证的部分（区别于"内容质量"这种主观项）：

- 署名存在且解析到身份页（作者页有 sameAs 指向 LinkedIn/ORCID 等）
- dateModified 与页面可见日期一致
- 统计带可点击来源
- 组织 sameAs 全部可解析、无死链
- 有原始数据产物（表格/图/数据集）而非纯转述

## 五、来源

- 五维块级与 134–167 词最优段：[zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) `skills/geo-citability/SKILL.md`
- 站点级分层/闸门/三态/抽样协议：[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `rubric/v1.1.md`
- 47 方法库（9 个出自 KDD 2024）：[Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) `docs/geo-methods.md`

## 市场差异:单位换算与阈值(拉平轮;英文基线的"词"不是通用单位)

**134–167 词的最优引用段是英文衍生值**——其他语言按等价信息量换算:

| 市场 | 计量单位 | 可引用块阈值 |
|---|---|---|
| 中文 | 字 | 答案块 40–60 字;FAQ 答 80–200 字;句 15–25 字(>35 难解析) |
| 日语 | 全角字 | 答案块按体裁(MEO 500–1,200/一般 1,500–3,500/支柱 7,000–12,000);句 ≤25 词 |
| 泰语 | 字素+分词 | 先 `Intl.Segmenter("th")` 再谈密度;句 ≤25 词 |
| 俄语 | 词 | 答案首屏 40–60 词(Алиса 显 ~5 行) |
| 印尼 | 字 | 结论前置 40–60 字;对比表 ≥5 维 |
| 韩语 | 全角字 | description ≤80;疑问式 h2 ≥50%(t0mmy 规则,越区同) |

**跨市场通用**:有源数字+定义块+对比块优于纯问答格式(中文实测:纯问答 −5.7%);评分时剥离导航/页脚再算(法区规则,通用)。完整阈值表见 multilingual-workflow 第四节。

## 市场外增量:AIV 评分学(geo-score rubric v1.1 全量,百仓扫描批 4)

**双分制**:Readiness(100 分可改)与 Citation performance(只报告不进分)。
**三态分母**:scored / unobservable / not_applicable——后两者离开分母,不虚稀释。
**三个 gate**(robots/reachable/ssr):仅 tier 0 违例时把归一化分封顶 40%;中层只扣分不封顶(套件 Reachable gate 同构)。
**五支柱配分**:Reachable 15 / Understandable 22 / Content Citability 35 / Brand Credibility 18 / Answer Fit 10。
**Band 阈值**:83/66/51/31(Leading/Solid/Growing/Early);findings 按"可恢复分数÷工作量"排序。
**采样协议**:恰好 8 URL(首页 2/产品 2/文档 3?原文 2+2+3+1——按站型配比)。
**中文换算**:答案段 50–200 字(英文 25–120 词)。
**引用稳定性判定**:单次引用检查=掷硬币(arXiv:2604.07585)——**多次采样+Wilson 95% 置信区间**,区间跨判定界标 unstable(Auriti 4.18 同款)。

## CORE-EEAT 80 项基准(aaron-marketing-skills 精读,百仓深扫;与 AIV v1.1 并列的第二套评分学)

**结构**:CORE(C/O/R/E)管内容体=GEO;EEAT(Exp/Ept/A/T)管作者组织站=SEO;各 10 项×4 维。
- **C 清晰**:意图对齐/前 150 词直接答案/≥3 查询变体/术语首用即定义/显式范围与受众/段间连贯/A-vs-B 决策框架/结构化 FAQ/结论闭合;
- **O 组织**:单 H1 无跳级/TL;DR 框/对比用 HTML 表/~1-2 列表每 500 词/正确 JSON-LD/段落 3-5 句/TOC 锚点;
- **R 可引用**:≥5 带单位数据/≥1 引用每 500 词且 ≥3 源类型/一手源≥3/主张后紧跟证据/方法可复现/更新<1 年/实体全名/描述性内链锚/`<article><figure><time><cite>`/无内部矛盾;
- **E 独占**:一手数据/命名框架/原创研究/有据反共识/≥2 原创图/可下载工具/深度超竞品;
- **Exp**:第一人称+动作动词/≥10 感官词/带时间线过程/带时间戳原图/"用 X 个月后"/前后对比/承认局限;**Ept**:署名+头像+bio>30 词/资质/阈值可操作/"选 A 弃 B 因为";**A**:.edu/.gov 被引/奖项/Wikipedia·KG/全网一致;**T**:隐私条款/地址/VETO=利益披露/编辑政策/更正页/广告<30%。
**规则**:veto 3 项(T04 利益披露/C01/R10)封顶 59;9 内容型权重表(测评 Exp20/E20;落地页 A25/T25);引擎映射(AIO→C02/O03/O05;ChatGPT→C02/R01/R02/E01;Perplexity→E01/R03/R05);自造 aggregateRating=结构化数据垃圾可触发人工惩罚。

## 页级 agent 可操作性审计(claude-seo 深读,2026-10-09)

来源:[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-agentic/references/agent-friendly-pages.md`(2026-09-23 对照 Lighthouse 13.5.0 与 Chrome 文档核验)。可引用性的 agent 时代延伸:内容不仅要能被抽取,页面还要能被 agent **操作**(搜索/比价/填表/下单)。

**三通道阅读模型**(厂商共识,OpenAI publisher guidance/Lighthouse/WebKit 三方一致):①截图+视觉模型(慢、token 贵);②原始 HTML/DOM;③**浏览器无障碍树**——三者中最干净的信号,也是 WebKit 反对 WebMCP 时指名的替代层。原生元素优先于 ARIA(W3C 第一规则):ARIA 修 custom widget,不替代真 `<button>`。

八项页级检查(审计清单):
1. **真实交互元素**:`<button>` 做动作、`<a href>` 做导航、`<input>/<select>/<textarea>` 做输入;`<div onclick>` 是失败样例。实在做不到才补 `role`+`tabindex="0"`+可访问名+Enter/Space 键柄——custom div 常以无 role 进无障碍树,agent 直接跳过。
2. **可访问名称**:每个输入有 `<label for>`/`aria-label`/`aria-labelledby`;图标按钮必须有可访问名(对应 axe 规则 label/button-name/link-name/select-name)。
3. **交互目标尺寸**:视觉管线丢弃过小目标;WCAG 2.2 AA 24×24 CSS px(Apple HIG 44×44)同时清掉 agent 阈值。
4. **交互节点上无透明覆盖**:视觉模型丢弃被覆盖节点。惯犯:整卡点击处理器盖住子链接、授权后不消失的 cookie 层、关闭后仍 `pointer-events:auto` 的 modal、`position:absolute; inset:0` 的埋点层。
5. **布局稳定**:CLS ≤0.1(Lighthouse Agentic 分数计入);功能相同的动作在模板间位置一致——"加购"按钮在 /shoes 与 /bags 换位,截图 agent 每页都要重学。
6. **`cursor: pointer` 是信号**:视觉模型读它为"可操作"——真控件保留,非交互元素绝不加。
7. **稳定有意义的选择器**:DOM 型 agent 靠 landmark(`<nav>/<main>/<article>/<aside>`)、稳定 id、表意 `data-*`;哈希类名对 agent 零信息。
8. **失败模式清单**(从业者共识,非厂商实测):hover-only 菜单;无分页链接的无限滚动;无 ARIA 模式的 custom select/日期选择器;封闭 shadow DOM 与 canvas-only 界面;困住焦点或盖住控件的授权/弹窗;内容页上的 CAPTCHA/挑战;纯客户端渲染主内容;只闪一下或只在 toast 里的确认状态。

**证据边界**(照抄该仓立场):无受控公开研究把无障碍树质量与 agent 任务成功率挂钩——以上按"有理由的实践"呈现,不写成实测提升。

## 第二套站点级评分学:六类合成 + 确定性子分细则(geo-seo-claude 深读,2026-10-09)

来源:[zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) `docs/scoring-methodology.md` 全文 + `skills/geo-audit/SKILL.md`。与第二节 AIV 五支柱并列的第二套完整评分学;该文档自带三条 caveat(确定性/观点权重/诊断非保证),照录。

**六类合成权重**:Citability 25% / Brand 20% / E-E-A-T 20% / Technical 15% / Schema 10% / Platform 10%。分档:90+ Excellent / 75+ Good / 60+ Fair / 40+ Poor / <40 Critical。Citability 类内部再复合四组件:**Citability 35% / Brand Mention 30% / Crawler Access 25% / llms.txt 10%**。

**块级五维的确定性子分**(citability_scorer.py,同 HTML 必得同分;补足本文第一节只有维度权重的细粒度):
- 自含性:134–167 词 10 分、100–200 词 7 分、80–250 词 4 分;**代词密度 <2% 8 分**;≥3 个专名 7 分;
- 统计密度:百分比每个 3 分(上限 6)、金额每个 3 分(上限 5)、带单位数字每个 2 分(上限 4)、年份引用 2 分、具名来源 2 分;
- 独特性:原创研究措辞("our study found")5 分、案例/真实场景 3 分、具体工具/产品提及 2 分;
- **页面级得分 = 得分最高 5 个块的均值**(不足 5 块取全部)——top-5 均值而非全页均值,奖励"最优块密度"。

**Crawler Access 扣分表**(起 100):关键爬虫被封 −15/个、次要 −5/个、robots.txt 无 Sitemap 引用 −10,下限 0。⚠️ 该仓"关键爬虫"名单把 GPTBot/ClaudeBot(训练型)列入——与厂商文档矛盾,正确分层见平台差异文件第三节;扣分结构可借鉴,名单须用我们的引用型/训练型分层。

**llms.txt 组件五档(0–100 制)**:0 无文件 / 30 有但格式错 / 50 格式对但内容最少 / 70 覆盖主要内容区 / 90–100 完整且带 llms-full.txt。

**内容分复合**:E-E-A-T 四维各 25 分归一后占 60%;内容指标 15%(thin <300 词、deep-dive 3000+ 词、Flesch、段长、标题层级);AI 内容评估 10%(无 AI 腔泛化短语、有作者声音、有原创数据);主题权威 10%(相关页广度、内链深度、hub-cluster);新鲜度 5%。

**Technical 九组件**:SSR/JS 依赖 25%(最高权重,理由=GPTBot/ClaudeBot/PerplexityBot 一般不执行 JS——JS 渲染主内容的 SPA 对 AI 爬虫等于空页);meta/可索引 15%;robots+sitemap 15%;**安全头扣分表:无 HTTPS −30、无 HSTS −10、无 CSP −10、无 X-Frame-Options −5、无 X-Content-Type-Options −5、无 Referrer-Policy −5、无 Permissions-Policy −3**;CWV 风险 10%(静态分析只能标低/中/高风险,实测须 PSI/CrUX 字段数据);移动 10%;URL 结构 5%;响应头 5%;其他 5%。

**Schema 十组件分值**:Organization 20(存在 10,sameAs≥3 平台 20)/ Article 15(存在 8,作者为 Person 对象 12,带 dateModified 15)/ Person 15(jobTitle+knowsAbout 齐 15)/ sameAs 完整度 15(1–2 平台 5,3–4 平台 10,**5+ 平台含 Wikipedia 15**)/ speakable 10 / BreadcrumbList 5 / WebSite+SearchAction 5 / 无废弃 schema 5(HowTo 2023-09 移除;⚠️ 该仓称"FAQPage 2023-08 起限政府/健康站"**已过期**——现行口径是 2026-05-07 起富媒体全停,见 geo-evidence 第二节)/ 全 JSON-LD 5 / 校验无错 5。**JS 注入的 schema 一律降权**:AI 爬虫不执行 JS,初始 HTML 里没有就等于没有;校验是结构性的,不验值真伪。

**Platform 类子分**:AIO=内容结构 40/来源权威 30/技术 30;ChatGPT=实体识别 35(Wikipedia/Wikidata/sameAs)/内容偏好 40(可归因的事实陈述)/爬虫可达 25。Perplexity=社区验证(Reddit/Quora/SO)与来源直给分列。

**按站型加权的审计侧重**(geo-audit):SaaS=功能对比表(高可引)+集成页+文档质量;本地=NAP 一致性+GBP+本地 schema;电商=产品描述可引性+对比内容+购买指南;出版=文章质量+作者资质+引用惯例;B2B 服务=案例研究+专业展示+思想领导。

**方法论三纪律**(该仓自陈,采纳为套件评分器通用要求):①确定性脚本与 LLM 判分**分开标注**——后者同 URL 两次运行会有差异,报告须声明;②权重是作者判断、非受控研究产物,写"观点性权重";③分数是诊断工具,高分改善被引的结构条件、不保证被引。

## AIV rubric v1.1 全分档表与校准方法论(geo-score 深读,2026-10-09)

来源:[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `rubric/v1.1.md` 全文 + `rubric/calibration-v1.1.md` + `rubric/bands-analysis.md` + `rubric/evidence-v1.1.md` + `benchmark/PREREGISTRATION.md`(厂商文档 2026-10-04 复核)。此前只吸收了支柱骨架,以下是逐检查分档与全套校准方法论。

### 逐检查分档(21 个计分检查 + 4 bonus;tier 判据=证据实际满足的最高档)

**Reachable(15)**:`g.robots` 0/3/5(0=有适用 Disallow;3=无 Disallow 也无 Allow;5=显式 Allow)·`g.reachable` 0/3/5(0=多数检索 UA 被拒;3=部分被拒或内容与浏览器不符;5=10 个检索 UA 全 200 同内容)·`g.ssr` 0/3/5(**挑战页不算样本页,整站只回挑战=不评分,绝不读作 tier 0**)。
**Understandable(22)**:sitemap 0/2/4(+lastmod 覆盖)·llms.txt 0/2/4/5(2=200;4=有站点定义段;5=≥2 主题区含链接)·Organization+WebSite 0/3/5/6(6=logo 可解析+sameAs)·BreadcrumbList 0/2/3·页型 schema 0/2/4。
**Content Citability(35)**:自含答案段 0/4/7/9(按 8 页中出现的页数)·标题匹配问法 0/3/5/7(**问题/任务/解释都算,只排除关键词串与品牌标签——不是要带问号**)·新鲜度 0/3/6(schema 日期或可见日期等价,6=dateModified 与可见日期一致)·有源统计 0/3/5/7(7=来源可点击可核验)·具名作者 0/3/6(站内作者页或本人主页都算,不要求站内 bio)。
**Brand Credibility(18)**:第三方目录 0/2/3/4(2=1-2 家;4=5+家)·独立提及 0/2/3/4·KG 实体 0/4(全有全无;Wikidata/Wikipedia/百度百科任一)·sameAs 0/2/3(**不声明=0 分,不离分母**)·视频多模态 0/2/3(3=持续产出+站内 VideoObject)。
**Answer Fit(10)**:抽取形态 0/2/4·问题覆盖 0/2/3/4(10 个真实行业问题,0-2/3-5/6-8/9-10 覆盖;**缺口即编辑日历**)·中文引擎就绪 0/1/2(**2=可爬+ICP 备案+实体信息完整——唯一把备案写进评分的检查**)。
**Bonus(+6,不入分母,不做不罚)**:llms-full.txt 2(非根路径可,须从 llms.txt 或 robots 可发现)·ai.txt 2·GEO link tags 1·speakable 1。

**报告形态三件套**:findings 按"可恢复分数÷工作量"排序;**首屏只放三样**——分数+band、距下一 band 多少分、top 3 findings(全表进附录);每个 finding 三部分——为什么重要/哪里错了/到下一档值多少分。**范围纪律**:rubric 只发布判据(what/tier/why),修法/工作量/归属/顺序不进 rubric——"发布判据≠发布实现"。

### v1.0→v1.1 校准全过程(评分器维护的方法论范本)

- **翻车现场**:v1.0 给五个真实站(stripe 51%/nextjs 49%/svelte 40%/anthropic 36%/mingdao 34%)全打 Critical/Below——全 200+60KB SSR 文本的站被打 Critical,"这不是站的事实,是 rubric 的事实"。
- **四结构问题**:①13 分无人区(ai.txt/GEO link/speakable/HowTo/Breadcrumb/Product 五站全 0——Web Almanac:llms.txt 仅 2.13% 桌面站(2025 版);JSON-LD 中 BreadcrumbList 5.66%/Product 0.77%/FAQPage 0.34%(2024 版),这些分在惩罚所有人而非测量差异);②16 分无区分度(爬虫可达/SSR/目录五站全满——重要但作为二元检查不携带信息);③12 分站外不可观测(不同站掉不同检查→三个不同满分 82/85/88,互不可比);④二元判断压缩量程(五站挤在 17 分带内)。
- **七项改动**:判实质不判形式(标题三读法;答案段 40–90 词→25–120 词,svelte 核心句 39 词差一词被杀;新鲜度只认 dateModified→schema 或可见日期任一)·tier 取代 pass/fail(21 检查各 2–4 档,档位以 8 页中的页数计)·不可观测出分母(报为未计分块)·双分制·新兴约定转 bonus(9 分→+6)·gate 计分且封顶(**仅 tier 0 封顶 40%**)·五 band 用阶段名(删"Critical":CI 工具用红灯语言,给人看的诊断用阶段语言)。
- **回测教训**:投影(48–62%)vs 实测(69–87%)——**形式→实质的判据改动不能用比例折算**;投影量程 14 分/实测 18 分;同档五站测不了区分度(18 vs 17 无意义)。
- **gate 设计错误(重测抓出)**:初版"任何 gate 不满分即封顶"→stripe(robots 不点名 AI UA 但不封任何)+nextjs(40 字节 robots 全允许)都被显示为 40% Early——"这是 v1.0 错误的搬家:把'不理想'当'不工作'"。**由审计真实站发现,而非对 rubric 推理——这就是要发布审计的理由**。
- **与 aeo-lite 的分叉**:aeo-lite hard-fail(把人人过的检查移出分母)适合 CI fail-the-build;面向非技术读者的诊断保留 table-stakes 计分(移出会分子分母同降,测试中量程 17→12 被压缩)。

### 市场基线(四独立源,判断分数是否正常)

GeoReady 282 域均值 **56.4**(早前 750+ 样本均值 54.3/中位 56);GW Content"多数商业站 30–55";Foglift 2026Q1 行业中位 SaaS/B2B **62**/教育 58/医疗 55/代理 51/电商 48,上四分位 73–84;Seomator 2026-01~07 评分站 **54.6% 低于其 56 分就绪线**。引用表现基线(LumenGEO):SaaS 品牌 15–30,本地商家 0–10。**技术顶尖站 69–87 属正常——与 Foglift 上四分位吻合,不是校准错误**。

### band 切线的三准则检验(317 站 benchmark)

①可达性(CWV 元规则:阈值须 ≥10% 站已达到):Leading 83=10.1%(32/317)恰好达标,**84 就只剩 9%**——"再跑一次可能在规则两侧,所以 83 不能是设计出来的理由";②带宽>测量噪声:重测 SEM 3.09 → 单次分 95%CI **±6.1**;三个内带 20/15/17 分宽=6.5/4.9/5.5 倍 SEM,**但 53% 的站(168/317)落在切线 ±6.1 内=band 在噪声内**;重测 7.9% 换 band;等权重 12% 换 band 而排名几乎不动;③每带一种站:**不达标**——cap 值 40 落在 Early 内部,Early 88 站中 48 站(55%)是被 cap 的站("爬虫根本拿不到内容"≠"基础有清晰缺口");cap 前被 cap 的 83 站散布 1L/8S/18G/21E/35N。v1.2 方向:cap 值移出带内部或 band 标签注明 capped。

### 预注册验证计划(测工具,不测 GEO)

主问题:竞争同一批买家问题的站点中,readiness 更高者是否在 AI 答案中被引占比更大。设计:20 类×10 题×4 引擎(各开 web search)×8 次=6,400 答案/波,wave 0+12 周后 wave 1;**问题先冻结**(不看任何站分数就写完并提交,不点品牌名,`brand_in_query=false` 由匹配器保证);**选站按 predictor 不按 outcome**(候选=公开清单列出的厂商,绝不因被 AI 引用而加入);分层用 rubric 自己的 band 切线(低<51/中 51-65/高 66+),每层随机抽(记录种子);gate 封顶站保留(S1 剔除分析);次级 S1-S4 Holm 校正(去 gate 站/流行度残差化/吸收率/答案文本点名)。**明确不声称**:关联≠因果(因果需随机化改页,如 arXiv 2604.25707 附录 B 五臂设计);正相关可能有品牌混杂;null≠无关;API 答案≠消费级 App;不验证单检查与权重(任何改动走新版本);不测流量(单站实测:ChatGPT referral 原始增长大头是平台自身,arXiv 2606.04362)。单次运行 ±5 分;**预注册修正案机制**:改动只以带日期的 amendment 追加,注册日=含该文件的第一个 tag 版本发布日(git commit 日期不是证据)。

### 证据薄弱清单与文献分级(evidence-v1.1 自陈,引用时照抄限定)

- `p2.answer-passages`(9 分,最重)只靠两个 preprint(其一用模拟引擎),且 Google 明说内容无需为 AI 切块;`p2.question-intent`(7 分)无外部支持、Google 指反、另有三项研究未分离出问句格式;`p1.llms-txt`(5 分)=2.13% 采纳且 Google 明说忽略;`p1.page-type` 所列类型只有 Product 仍有 Google 特性;`p3.knowledge-graph`"最强单信号"声称无来源;`p4.question-coverage` 取决于审计者选题(最大不可复现源)。
- **ai.txt 是两个不相关提案共享的名字**(Spawning 2023 根路径文件 vs 2026 IETF 个人草案 well-known 路径),都无答案引擎文档读取;GEO link tags=llms.txt v2 建议的标准 link relations;**speakable=Google Assistant 智能音箱读新闻的 beta,无生成式引擎文档使用**。
- **文献分级注记**:Wu 2025(2510.11438)用小商业模型模拟引擎;Zhang 2026(2604.25707)观察性、自称不做因果声称;Kumar 2026(2606.20065)是 GEO 厂商测量研究;Zhen 2026(2607.15771)是 AI 搜索监测公司用自家工具采的观察研究;Watanabe 2026(2606.04362)单站自家研究、自称 suggestive;同行评议的:Aggarwal(KDD 2024)、Wan(ACL 2024)、Puerto(NeurIPS 2025 D&B)、Chen(WWW 2026,七个多为开源的 LLM 搜索产品)。
- **Cloudflare 2026-09-15 改 bot 默认值**——厂商文档高频变动,来源只与其 Verified 日期同新。

## 生产级 AI 质检门禁工程学(GEOFlow 深读,2026-10-09)

来源:[yaojingang/GEOFlow](https://github.com/yaojingang/GEOFlow) `docs/ai-quality-inspection-runbook.md`(343 行全文;仓库无 skills/georank,agent 技能在 `.agents/skills/geoflow/`)。这是内容工厂的 LLM 质检系统运行手册——评分学(上面两套)衡量内容,这一层**验证生产管线本身**;四维分(知识一致性/数据与引文/广告合规/内容完整性)+质量分+证据覆盖+置信度+门禁原因。

- **四态门禁**:`passed`(≥85 自动通过,且无 hard blocker/重要不确定项/无效证据引用)/`needs_review`(未达线或证据覆盖不足/重要不确定/输出截断)/`blocked`(已确认 hard blocker 或 <70 人工放行线)/`error`(模型/检索/队列/截止导致失败)。**证据缺失 ≠ 冲突**:缺失只形成 `unverified`+人工确认项;只有受管证据与主张在**主体/数值/时间/范围**上明确冲突才算已确认冲突。来源键用 `knowledge_base_id+chunk_id+content_hash`(页面短编号 K1/K2 仅展示用)。
- **预算不等式**(健康检查强制):`完整预算 180s + 抽样预算 45s + 持久化预留 10s < Job timeout 245s < Worker timeout 250s < retry_after 960s`;单请求全文 ≤160s、抽样 ≤35s;≤5000 字正文 P50 25s/P95 55s;单篇上限:12 条物质性主张、1 次文章级检索+6 次补检、12 条/6000 字符证据、输出 2048 token。
- **降级抽样五安全条件**:仅性能类失败(预算耗尽/超时/正文超 6 万字/截断/剩余预算不足分段)允许降级,配额/鉴权/限流/网关故障直接失败;抽样器确定性覆盖标题/摘要/开头/结论/高风险词/数字/日期/引用/承诺/重大主张+前中后三区(≤6000 字符/12 个不重叠范围/Unicode 原文偏移/同输入同范围);**抽样自动放行还须**:确定性风险扫描无阻断+重大主张完整覆盖+证据充分+后端结构与引用校验通过+无截断+达原通过线;系统级紧急开关+`incident` 冻结一键关闭。
- **灰度五阶**:0/10/25/50/100;`promote` 只许进下一阶且须 30 天内通过的在线端到端报告(**须同时覆盖全文与抽样路径+延迟闸门+同输入 5 次稳定性**);影子记录 `gate_applied=false` 不参与发布;重大风险漏检→incident 冻结全部灰度+关抽样,修复后凭新报告解冻。
- **熔断器**:连续 5 次可重试错误或 10 次窗口错误率 ≥50% →打开 60s;半开仅放单探测;候选模型仅同协议/主机/端口自动切换,跨供应商须管理员显式操作。
- **黄金集评测指标集**(LLM 评分器验收标配):decision 混淆矩阵、**安全样本误拦截率**、**重大风险召回率**、问题级 Macro F1、Cohen Kappa、延迟与输入/输出 token 分位数;生产门槛=120 篇校准+60 篇固定回归+60 篇盲测,两人独立标注+第三人裁决。
- **失败呈现纪律**:技术失败时总分与四维分统一显示"未评分",页面绝不渲染成功结论;页面兜底在 deadline+5s 内退出等待;API 失败载荷不返回正文/证据/API Key/供应商内部异常(只给脱敏错误码+建议+下一步)。
- **模型适配注记**:<think> 围栏与 JSON 代码围栏兼容解析;GLM 4.5+(bigmodel.cn/z.ai)关思考+`response_format.type=json_object`;MiniMax M 系用 `reasoning_split=true` 分离思考;结构化输出验证降级后 24h 不重试(防重复失败烧预算)。
- 对套件的含义:**任何用 LLM 给内容打分的流程,验收对象是"评分器"本身**——混淆矩阵/误拦截率/召回率/标注一致性/重测稳定性先于上线;门禁结论(过/不过)与质量分(多少分)表达不同风险信号,不互相替代。

## 落地页与转化层评分器源码级阈值(seomachine 深读,2026-10-09)

来源:[TheCraigHewitt/seomachine](https://github.com/TheCraigHewitt/seomachine) `data_sources/modules/` 逐模块读源码(readability_scorer/above_fold_analyzer/cro_checker/cta_analyzer/trust_signal_analyzer/opportunity_scorer/search_intent_analyzer/engagement_analyzer/competitor_gap_analyzer/keyword_analyzer 等;此前仅吸收 content_scorer 六维与 content_scrubber 水印)。这是"内容形状"判定的确定性实现层。

- **可读性扣分公式(readability_scorer,100 起扣)**:Flesch<30 扣 30/<50 扣 20/<60 扣 10/**>80 扣 5(太简单显得不专业——双向约束)**;FK 年级超目标+4 扣 25/+2 扣 15/超 1 扣 5/**低于目标 2 级也扣 10**;平均句长>30 词扣 20/>25 扣 10/>20 扣 5;超长句(>35 词)每句扣 3、上限 15;段均句数>6 扣 10/>4 扣 5;被动句占比>30% 扣 10/>20% 扣 5;**过渡词是唯一加分项**(>2 个/100 词 +5,<0.5 个扣 5)。目标默认 max_avg_sentence_length=20、段≤4 句。
- **首屏 5 秒测试(above_fold_analyzer)**:首屏=前 700 字符;四元素权重 headline 0.35 / value_prop 0.25 / CTA 0.25 / trust 0.15;≥70 过 5 秒测试。强标题 7 模式(数字开头/问号结尾/痛点移除/方案到达/动作动词/利益词)命中 ≥2 个 +30;弱标题 7 红旗(Welcome to/The best.../Everything you need/Introducing/We help/Our product/**"X is a..."**)。⚠️ **视角冲突须管理**:"X is a..." 在 CRO 层被判弱标题,却恰是 GEO 定义块的标准开式——落地页 H1 不用词典式定义(放到首屏下方定义块),GEO 判据见前文;两套判据按检查目的分开用。
- **CRO 清单(cro_checker)**:通过=≥70 且 0 个 critical;H1 最优 20–70 字符;CTA 数量最优 3–6(长页)/2–4(短页)。
- **CTA 三分(cta_analyzer)**:质量 0.4/分布 0.3/目标对齐 0.3;按转化目标(trial/demo/lead)各有 primary/secondary 按钮模式表;specificity 加分模式=天数(14-day)/百分比/$金额/免信用卡/"X 分钟内"。
- **信任信号四组模式与分值(trust_signal_analyzer)**:推荐语 35 分(≥3 条 25/2 条 20/1 条 10;带署名再 +10;引文 20–300 字符才算);社会证明 30 分(客户计数 15+具体结果 15:百分比增长/N 倍/金额/下载数/时间结果);**风险反转 25 分(3 类齐全才"强";2 类 20;任一 10)**;权威 10 分。
- **机会评分八维(opportunity_scorer)**:volume 25/position 20/intent 20/competition 15/cluster 10/ctr 5/freshness 5/trend 5;**期望 CTR 按位次内置表**(1=31.6%/2=15.7%/3=10.5%/5=5.9%/10=2.7%/20=0.7%);优先级分档 80/65/45。
- **意图分类的 SERP 特征映射(search_intent_analyzer)**:featured_snippet/knowledge_graph/PAA/video→informational;shopping_results/local_pack/ads→transactional;carousel→commercial;品牌+通用词→navigational;问句→informational、列表/对比→commercial;**无 SERP 数据时四意图各给 25%(显式承认不确定,不硬猜)**。
- **参与度节奏分(engagement_analyzer)**:按 H2 切节算词数;5 节滑动窗全在均值±5 词内=单调段;节长标准差 <5:40+σ×6;**σ 在 5–15:100−|10−σ|×2(理想 σ≈10)**;>15:80;单调罚分上限 20。**rhythm 及格线从 60 下调至 45,源码注释写明原因:"对比文天然表格重"——判据按体裁校准的实例**(与 geo-evidence 的体裁阈值同思路)。
- **竞品缺口四型(competitor_gap_analyzer)**:thin_section(**小节<75 词=HIGH**)/unsupported_claim(无来源主张)/outdated_info/structural_gap(整块主题缺失=HIGH);同时识别对方 strengths(要正面超越的)。关键词分析含多词变体计数(词序无关)与关键位置(H1/首段/H2)覆盖。

## 第三套站点评分器:Auriti v4 八类 100 分(geo-optimizer-skill 深读,2026-10-09)

来源:[Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) `src/geo_optimizer/models/config.py` SCORING 权重表 + `core/scoring.py` + `core/trust_stack.py` + `core/audit_negative.py`(源码级,每个权重带修订注释)。此前只吸收其 47 方法库,未吸收评分器本体。

**八类权重(源码原值,注释记录每次改动)**:robots 18 / llms 18 / schema 16 / meta 14 / content 12 / signals 6 / ai_discovery 6 / brand_entity 10;加负面罚分(不再加别处):severity high −5 / medium −3 / low −1;**X-Robots noindex 罚 −5**;总分钳位 [0,100],**>100 记 overflow warning 检测权重失配**。band:excellent 86+/good 68+/foundation 36+/critical <36(注释:从 91/71/41 下调过)。

- **robots 18**:found 5 + 引用 bot 显式 Allow 13;无显式 Allow 但通配符允许=10 分替代项(fix #332:替代而非叠加)。
- **llms 18(毕业化打分)**:found 5/H1 2/blockquote 1/sections 2/links 2/**词数 ≥1000 +2/≥5000 +2**/llms-full.txt +2——把"文件质量"做成分级而非二值。
- **schema 16**:任一有效 2/richness(**5+ 相关属性**)3/FAQ 3/Article 3/Organization 3/WebSite 2;**不完整的 schema 给 1 分不是 0**(鼓励起步);sameAs 迁去 brand 类留 0 兼容。
- **meta 14**:title 5/canonical 3/OG(title+description 齐)4/description 2。
- **content 12**:H1 2/数字 1/链接 1/**词数 ≥300** 2/H2+H3 正确层级 2/有列表或表格 2/**关键信息在前 30%** 2(前置加载密度阈值 0.05)。
- **signals 6**:html lang 3/RSS 2/新鲜度 1。
- **ai_discovery 6(geo-checklist.dev 标准)**:`/.well-known/ai.txt` 2/`/ai/summary.json`(须 valid)2/`/ai/faq.json` 1/`/ai/service.json` 1。
- **brand_entity 10**:实体一致性 3(名称跨 H1/title/og/schema 一致 2+schema 描述与 meta 一致 1)/KG readiness 3(**≥3 支柱满 3,2 支柱 2,1 支柱 1**;支柱=sameAs 指向 Wikipedia/Wikidata/LinkedIn/Crunchbase)/about 链接+联系信息 2/geo schema 或 hreflang 1/FAQ≥3 或近期文章 1。
- **负面信号判定(audit_negative)**:CTA >5 个或 >1% 词密度=过高;弹窗类名清单(modal/popup/overlay/interstitial/lightbox/cookie-banner)与 data-modal/data-popup/data-overlay 属性;薄内容;断链 >3;**关键词堆积阈值 2.5%**(KEYWORD_STUFFING_THRESHOLD=0.025);无作者信号。
- **Trust Stack 5 层 25 分**(独立于总分):Technical(HTTPS+2/HSTS/CSP/XFO)/Identity(署名+Organization+about/contact)/Social(sameAs 指向 8 大社交域)/Academic(**参考文献指向学术域名**(ncbi/pubmed/doi.org/scholar/arxiv/nature/science/jstor 等)+**统计语句正则**(百分比、N≥10 研究、"according to a study";最少 2 处匹配))/Consistency(品牌一致+无混合信号+日期);grade A≥22/B≥17/C≥11/D≥6。
- **可复现性细节**:Flesch-Kincaid 公式常量直接内置(0.39/11.8/−15.59,"published formula, not magic numbers");TTR 词汇丰富度用 200 词窗口、阈值 0.40。

## gtm-engineer 全管线:写作配方、六维先验与证据核验(gtm-engineer 深读 2026-10-09b)

来源:[onvoyage-ai/gtm-engineer-skills](https://github.com/onvoyage-ai/gtm-engineer-skills) 12 技能中余下 9 个全文(audit-content/build-backlinks/build-resource-pages/geo-content-planning/improve-aeo-geo/reddit-opportunity-research/research-brand/research-keywords/write-seo-geo-content)+ `audit-website-aeo/scripts/aeo-audit.mjs` 1,020 行逐读。前批已收 142 分 foundational 表(见 technical/scoring-rubric.md),本节只收可引用性/GEO 内容侧,覆盖"规划→写作→核验→提及"全管线。

**块级写作配方(write-seo-geo-content,第一节五维的操作化)**:Quick Answer 块=问句式 H2+1-3 句+≤60 词,可整段抽出;**Brand Mention 块(40-80 词)独立成段且自辩护**("Compared with [竞品], [品牌]……")——品牌提及机制必须在动笔前声明且可辩护,页面撑不起提及就先改角度再写;每页 ≥2 个可脱离上下文引用的段落;对比页必须有表+明确 verdict("best for X");**FAQ 是条件件不是标配**——仅当命中问句式搜索/用户有真实异议/能写出正文未答的 3-6 个非重复问题时才加,正文已答、短产品页、变相重复=跳过(与"每页必加 FAQ"类建议相反,也与本文中文实测纯问答 −5.7% 互证;FAQ 内容比 FAQPage schema 更重要,富结果已停但机器可读性仍在);段落 ≤2-3 句,每 ~200 词一个表格/列表/引用块;结论=前状态→后状态+1 个数据+单一 CTA;禁词表:revolutionary/game-changing/best ever/industry-leading;title 50-60 字符、meta description 恰 150-160、主关键词进前 100 词;2,500 词起步(对比/指南 3,000+);**装饰性图片 SEO/GEO 价值≈0**,视觉只在带数据/讲流程/证主张时加。

**增量统计(improve-aeo-geo 附研究表,本文件此前未收录,均已带一手出处)**:引语 +41%/统计 +33%/引用来源 +28%(KDD 2024 三 tactic 排序,引语为最强单手段;原排名 4-5 位站点加引用源最高 +115%)·**44.2% 的 ChatGPT 引用来自页面前 30%**(Kevin Indig 2026,1.2M 回答)·H2 之间 **120-180 词=引用 +70%**(SE Ranking 2025,2.3M 页;与第一节 134-167 词块长同源互证——节长与块长两个口径)·2,900+ 词 5.1 次引用 vs <800 词 3.2·FAQ 页 4.9 vs 4.4·3 个月内更新 6.0 vs 2 年+ 3.9·AI 引用比自然搜索结果**新 25.7%**(Ahrefs,17M 引用)·AIO 引用 85% 来自近两年(Seer)·ChatGPT 占 AI 推荐流量 87.4%(Conductor,3.3B 会话)。操作含义:每 150-200 词至少一个数据点;**alt 文本写结论不写形态**("柱状图"×,"GEO 优化页引用率高 41%(KDD 2024)"✓);图表必须配文本摘要+HTML 数据表——AI 引文本不引像素。

**六维智能分的确定性先验公式(aeo-audit.mjs 源码级,脚本半场可复用)**:脚本先出 heuristic prior,再由 agent 用 LLM 六维重评替换(两段式,同"确定性/LLM 分开标注"纪律):
- **answer-readiness** = 30×FAQ 式标题比 + 30×定义开头比 + 20×meta≥80 比 + 20×深度比;FAQ 式标题正则 `/\?|FAQ|how to|what is|guide/i`,定义开头=正文前 200 字符命中 `is/are/was/means/refers to/defined as`——"定义先行"的可执行判据;
- **quotability** = 30×标题富集比(≥4 个 H2/H3)+ 25×深度 + 25×层级清洁 + 20×**意图对齐**(title 与 meta description/H1 的 token 重叠率均值——标题-摘要-正文说同一件事的量化);
- **evidence-density** = 35×数字证据比 + 25×署名比 + 20×深度 + 20×内链密度(均值/12 封顶);数字证据=摘录含 `/\d/` 的页占比——**粗但确定性**,是"有源统计"的下界代理(不验源真伪);
- content-depth = 35×深度 + 25×模板多样性(覆盖页型数/5)+ 25×内链 + 15×标题富集;freshness = 30×日期信号 + 25×RSS + 20×sitemap 发现率 + 15×抓取成功率 + 10×可索引;structural-clarity = 30×层级 + 25×title≥20 字符 + 25×单 H1 + 20×标题富集;
- 实现细节:摘录剥离 nav/header/footer/form 后优先 `<main>/<article>`;LLM 复审页按 pageRichness 挑 5 页(摘要长+schema+作者+日期+标题数,blog/docs/product 页型加成);**robots 判定**:命名 bot 只读自己的组(`*` 组不继承,RFC 9309),仅 `Disallow: /` 且无 `Allow: /` 才算封——部分禁不算封,与 geo-platform-differences 的组选择暗坑一致。

**证据核验层(audit-content,发布前的质量门)**:主张五判 PASS/BROKEN/MISMATCH/UNVERIFIABLE/UNSOURCED——**错误≠不可验证**(付费墙≠编造,分开报告);幻觉模式清单:整数化的"合理"数字、挂知名机构却找不到原始出处的统计、数字漂移(文章写 52% 原文 48%)、未来日期的研究、貌似真实的不存在 URL;公司主张以 brand DNA 文件为唯一事实源(不在其中且外部不可证即标记);内部一致性(同一统计前后不一、年份矛盾);arXiv 按 ID 核、带年份的报告核实该年存在。

**规划与语言侧(geo-content-planning/research-keywords/reddit-opportunity-research)**:一页覆盖 1-3 关键词+3-6 相关 GEO prompt(**不做 prompt:页面 1:1 映射**);required_sections 枚举 direct_answer|comparison_table|who_this_is_for|how_it_works|use_cases|faqs|proof|objections,只选意图所需(对比页必 comparison_table,数据/money 页必 proof);prompt 分层 buy/solve/learn,优先 buy+solve。目标词**强制 1-3 词**(长句是博文题);KD 分档 easy_win 0-15/target 16-50/hard 50+;无付费数据时定性信号=自动补全存在+PAA+SERP 专页,ai_overview_present 单列为 GEO 信号。Reddit 研究把**用户原话**(非营销语言)喂给 H2/FAQ/异议措辞,讨论主题反推真实搜索与 AI prompt,只追反复出现的讨论模式(repeatability)。

**品牌提及面(build-backlinks/research-brand)**:GEO 外链论题=在 AI 训练与检索来源处出现——HN/Quora/Wikipedia/GitHub/SO 对 AI 引擎高可见;**高流量 HN/Quora 线程单次提及>10 个低权威目录**(第二节 Brand Credibility 18 分的"怎么做"侧);机会打分 GEO 影响 40%/工作量 30%/相关 30%;品牌描述用第三方语言而非官方营销语。

⚠️ **口径管理**:该仓 robots 建议放行全部 9 个 AI bot(含 GPTBot/ClaudeBot 训练型)——按套件分层,引用生死在检索型,全放是保守无害但非必要;meta description 三阈值并存(脚本及格线 ≥50/先验质量线 ≥80/编辑目标 150-160)是分层而非矛盾,引用时注明所在层。
- **项目自评 rubric 同仓并存**(SCORING_RUBRIC.md):给工具本身版本质量打分,六维 Robustness 25%/Code 20%/Doc 20%/Idea 15%/UX 10%/Growth 10%,0–10 制、按 0.05 舍入、**逐版本同 rubric 对比防目标漂移**("no moving goalposts")——工具产品质量与被测内容质量分开计量,值得套件维护借鉴。
