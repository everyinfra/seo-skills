# 关键词意图分类与判定

## 用途与何时读

做关键词研究、给关键词分簇、为页面选内容形式，或排查「内容不差却排不上」时读。目标是给每个查询定出**主意图**（必要时加次意图），再据此决定做哪类页面、放在漏斗哪一段、配什么下一步动作。

判定意图的最终依据是**目标市场当前的真实 SERP**；字面信号只用来初判。

## 四种主意图

| 主意图 | 用户想做什么 | 常见细分 | 通常承接的页面 |
|---|---|---|---|
| 信息型 | 弄懂概念、学会操作、解决故障、了解有哪些做法 | 概念、操作、排障、盘点 | 指南、教程、术语页、排障文章 |
| 导航型 | 去一个已知的网站或页面 | 品牌或产品名、账户入口、文档与支持 | 首页、功能页、登录页、帮助中心 |
| 商业调研型 | 付钱之前比较、筛选、看评价 | 两两对比、榜单与推荐、评测口碑、按场景选型 | 对比页、替代方案页、评测、选购指南 |
| 交易型 | 马上完成一个动作 | 购买或订阅、注册试用、下载、预约或询价 | 产品页、定价页、注册落地页、服务页 |

细分比主意图更能决定页面形式：同是信息型，「是什么」要定义加例子，「怎么做」要编号步骤和截图，「为什么报错」要按「现象 → 原因 → 解决」组织。

## 字面信号（只作初判）

按信号类别判断，不依赖固定词表：

- **疑问结构**：是什么、怎么、为什么、有哪些，多为信息型；但「多少钱」「值不值得」「哪个好」这类问句常属商业调研或交易。
- **比较与筛选**：vs、对比、区别、推荐、排行、替代、「适合某类人的」，以商业调研型为主。
- **品牌 + 具体对象**：品牌名单独出现，或品牌加功能、登录、文档、下载，以导航型为主。
- **动作动词**：买、订阅、下载、注册、预约、报价，以交易型为主。
- **地点修饰**：「附近」、城市名，表示本地意图，常和交易型叠加。
- **时间修饰**：年份、「最新」，说明用户要时效内容，页面必须能按期更新。

不同语言和市场的信号不能互相照搬，同一概念在不同市场的意图分布可能不同，要分别看 SERP。

## 用实际 SERP 核验

1. 在目标地域、语言和设备下查看结果（无痕窗口，或你自有、自选的排名数据源），记下查看日期。
2. 看前十条的**页面类型**（首页、产品页、文章、榜单、论坛、视频）和**内容形式**（教程、清单、对比、工具）。占多数的类型，就是搜索引擎当前对主意图的判断。
3. 把 SERP 功能当旁证：购物结果、本地结果、视频、「用户还问了」、AI 概览等，含义见 [serp-feature-taxonomy.md](serp-feature-taxonomy.md)。
4. 结果类型高度混杂，说明意图分裂或还不稳定，按下一节处理。
5. 已上线的页面，用 Search Console 效果报告看它实际拿到哪些查询的展示。实际触发的查询和设想的目标词对不上，往往就是意图错配。这一步需要你自己的 Search Console 权限。

## 混合意图

- **先分主次**：主意图决定页面类型和首屏内容，次意图放到后续段落或相邻页面。
- **SERP 同时排着两类页面**（例如文章和产品页）时二选一：一页先满足主意图，再用一段内容加链接接住次意图；或者拆成两页各对准一个意图，互相链接。判断标准是两种需求放在同一页里是否读得顺。
- 同一主题下「是什么」「怎么选」「多少钱」通常是不同意图，硬塞进一页会互相稀释；拆页时别让两页抢同一组查询，见 [topic-cluster-templates.md](topic-cluster-templates.md)。
- 意图会随新产品、季节和事件变化，重点词定期复查 SERP。

## 意图、漏斗阶段与下一步动作

| 漏斗阶段 | 典型意图 | 页面要做到 | 合适的下一步 |
|---|---|---|---|
| 认知 | 信息型（概念、盘点） | 把问题讲清楚，建立信任 | 相关教程、订阅、资料下载 |
| 考虑 | 信息型（操作）、商业调研型（榜单、对比） | 帮用户缩小选择范围 | 对比表、案例、试用 |
| 决策 | 商业调研型（评测、价格）、交易型 | 消除顾虑，让动作顺利完成 | 注册、购买、联系销售 |
| 使用与留存 | 导航型（文档、登录、支持） | 让已有用户快速到达 | 文档目录、帮助中心 |

不要给纯信息型页面硬塞购买按钮，也不要用长篇教程去抢交易型查询。各阶段的转化预期以站点自己的历史数据为准，不套行业平均数。

## 意图 × persona 映射(SXO 层,2026-10-09 并入)

意图回答"这词要什么页",persona 回答"这词背后是谁、页面是否服务好他"——意图层的下游:

- **persona 推导(从 SERP 证据,无证据不立 persona)**:PAA 问题簇→知识缺口人群;广告文案分众→商业人群(Budget/Enterprise);相关搜索→旅程阶段;SERP 结果类型→消费偏好。4–7 个,每卡:目标/旅程阶段/2–3 关键问题/信号证据。
- **页面 4 维打分(×25=100/persona)**:Relevance(解决该 persona 具体需求)/Clarity(10 秒首屏找到答案)/Trust(信任信号对该 persona)/Action(CTA 匹配阶段:awareness="learn more"、decision="buy now")。80+/60+/40+/39− 四档;优先级=最弱 persona×意图份额;全 persona 最低维=系统性问题。
- **证据面扩展**:SERP 之外用客服工单/评论挖掘(G2/Reddit;中文=知乎/小红书,韩=카페,日=知恵袋——**信号源必须按市场替换**)、一手访谈;置信度 High=3+ 独立来源非引导提及;每段 ≥5 数据点才立 persona,季度复审。
- **persona 卡加 locale 字段**:市场/语言/本地信任偏好(德区 Sie/du、巴西 Reclame Aqui、日区ステマ規制;Trust 维判据 SOC2 偏美式 SaaS,YMYL 换资质/法定页)。
- **用户故事桥**:`As a [persona], I want [goal], because [emotional driver], but I'm blocked by [barrier]`——每条引用具体 SERP 信号。

## 交付字段

每个关键词或关键词簇至少给出：

| 字段 | 内容 |
|---|---|
| 查询 | 原词，保留语言和写法 |
| 主意图 / 细分 | 例如「商业调研 / 两两对比」 |
| 次意图 | 没有就写「无」 |
| SERP 证据 | 主导页面类型、关键 SERP 功能、查看日期、地域、设备 |
| 建议页面 | 新建还是复用，对应哪个 URL |
| 漏斗阶段 | 认知 / 考虑 / 决策 / 使用 |
| 置信度 | 高（SERP 一致）/ 中（结果混杂）/ 低（没看 SERP，只按字面） |

汇总表格式见 [keyword-research-output.md](../../templates/research/keyword-research-output.md)。

## 常见误区

- 只看字面判意图，不看 SERP。
- 把所有问句都当信息型：「某产品多少钱」「值不值得买」多半在做购买判断。
- 把「最好的某类产品」当信息型：用户其实在挑产品。
- 忽略本地意图：服务类词在很多市场默认返回本地结果。
- 把别人的品牌词当泛词做内容，和对方官网正面竞争。
- 一个页面同时对准几种互相冲突的意图。

## 市场差异:关键词研究(各市场工具链与词形处理)

意图分类跨市场通用,但**工具链和词形处理按市场换**:

| 市场 | 工具链 | 词形处理要点 |
|---|---|---|
| 英文 | Google KW Planner + 自有 SERP 数据 | 词而非字;长尾靠修饰词扩展。**两个新轴**(2026-10):①fan-out 修饰词轴——vs/comparison/top/best/reviews(引用权重下行)vs site:/official(上行);②**共识治理型查询**——"best X"类推荐位由站外共识(G2/Reddit/分析师)决定,标注 citation-winnable / recommendation-gated,后者内容型优化收益封顶(行业,marketingskills) |
| 中文 | 百度指数 + **微信指数**(搜一搜选题,7/30/90 天,官方)+ **巨量算数**(抖音,官方)+ 千瓜(小红书,第三方);各 AI 引擎采样见中文指南 | 15–25 字问句口语措辞;简繁分开;**超级 App(微信/抖音/小红书)站内搜索词与开放网页词分开建表**;知乎当"实体存在"做,不当必然引用渠道(2026-08 实测修正) |
| 俄语区 | **Yandex.Wordstat**(`"短语"`=精确短语、`!词`=精确词形、`+/-`;精确频率公式 `"[!слово1 !слово2]"`;`(вариант1\|вариант2)` 变体合并) | 显示**预测曝光**非搜索量;右侧列≠精确频率;История/季节页**不支持运算符**;俄语形态丰富→"基础频率虚高"比英语严重,**聚类前双频过滤(基础/精确两档)**;按区域+设备分层 |
| 韩语区 | **Naver DataLab**(趋势)+ Naver Ads 关键词工具(量)+ **연관검색어/자동완성 흡수도法**:目标词的自动完成词逐个检查正文覆盖(先做全员覆盖词,再做无人覆盖词=先占机会) | 韩国用户真实输入,非英译;**통합검색 콜렉션 结构**:查询词决定 블로그/카페/지식iN/웹문서/지역 哪类集合展示——关键词研究按"集合"分层(官方文档级) |
| 日语区 | **ラッコキーワード**(候选挖掘)→ Google KW Planner JP(验量) | **全角/半角(ＳＥＯ/SEO)与片假名转写变体归组**;汉字/假名同词多写法;**MEO/SEO 词分工**:MEO=「地域名+業種」「〇〇近く」(今から行く意图)→GBP,SEO=比较/情报类→网页(行业共识);ChatGPT 日语查询可能被内部英译(Ahrefs 假说,未证实)→重要词备英文对照页 |
| 西语 | KW Planner 按区域 | **按方言区分套**:es-ES 与拉美词汇不同(coche/carro/auto);es-US 单独机会(70.2M 人口/45.5M 母语者,全球第二;**81% 受亲友之托代搜**的"集体搜索"特征——Pew);人称分层:tú=消费默认/usted=法律金融医疗/vos=rioplatense/vosotros=仅西班牙;**支付即意图词层**:MX=OXXO/efectivo、AR=cuotas/dólar(通胀语境,比较词带 precio/cuota 前缀,2025 电商 +55% 跑赢通胀 28 点——CACE 官方)、CO/PE=contra entrega |
| 葡语(巴西) | KW Planner(br)+ **Reclame Aqui 当关键词语料**(真实用户抱怨语言) | 只做 pt-BR;**AO90 正字法唯一标准**(idéia→ideia,老拼法仅存量长尾,Trends 对比后决定兼收);标题禁 Title Case(英文 AI 味标志);实体全称句式("A X, agência de Y em São Paulo") |
| 阿拉伯 | KW Planner(阿语最可靠工具之一)+ Google/YouTube 阿语 suggest + Ajebhom/TenKeyword;正字归一参考 Tanqeeh/tnkeeh 类库 | **打字=MSA、语音=方言**(从业者共识);埃及方言词跨区域触达最广;每核心词收录 MSA+方言(EG/SA/LV)+阿拉伯-印度/欧洲数字双写+正字变体(أ/ا/إ、ي/ى、ة/ه);Ahrefs/Semrush 阿语数据薄须交叉验证 |
| 德语(DACH) | KW Planner(**分国别取数,禁合并 DACH 搜索量**——合并产生没人搜的虚高数) | **Ansprache(称谓)与 Tonalität(语气)拆两个字段**:传统 B2B 默认 Sie+locker Ton、B2C/SaaS 默认 du,混合仅允许按渠道或按阶段且写进 styleguide,**全触点一致性>单点选择**;词汇映射每国一份(Jänner/Januar、Metzger/Fleischhauer、Marille/Aprrikose);奥地利 44% 电商跨境流向德国——德国站可被动覆盖 |
| 印尼 | KW Planner(id)+ 免费三源词研(客服对话/竞品评论区/社媒评论)+ Autocomplete a–z 验证 | **"关键词跟手指、正文跟词典"(kata kunci mengikuti jari pengguna, prosa mengikuti KBBI)**:gaul 词 Autocomplete 验证主导后可进 title/H2,正文保持 baku;五档 ragam 矩阵(beku/resmi/konsultatif/santai/akrar)比二元更细;gaul 区=实用/定义类,YMYL/健康/政府=baku 区(AIO 引用的健康/政府站全为规范语);宗教词用 KBBI 拼写(salat/Jumat);Ramadan/THR 季节内容刚需;**"hiruk pikuk"是印尼第一 ChatGPT 文风标记,绝对禁用**;±100 对 baku/salah 拼写(silakan≠silahkan) |
| 印地/印度 | KW Planner(en-IN/hi-IN 分开)+ **GSC regex(RE2)隔离罗马化 Hinglish 查询** | **Hinglish 三书写+拼写漂移聚类**(kya hota hai/h、kaunsa/konsa——音译规范化后聚类,IndicXlit 思路);**两大形态分开建**:英文词+meaning in hindi(电商信息)vs 英文词+印地语法包装(oily skin ke liye best foundation);语音=助词词库(kaise/konsa/batao/chahiye,泰米尔 enna/epdi/yaar)×产品词模板;**"排名好但快照语言错配"缺口**:英文页在 Hinglish 查询排首页但 CTR 0.16% 纚——修法=排名页顶部加用户原样措辞的 Hinglish 定义行(案例实测) |
| 意大利 | KW Planner(it-IT/it-CH) | **双语双轨**:科技/数字主题意英同搜("crm per pmi"/"crm tool");**P.IVA→Registro Imprese 竞品链**:页脚增值税号→ATECO 行业码+省→同码同省注册公司=真实竞品(公开 API,意语区独有);Lei 仅机构/高龄/奢侈,现代趋势全面 tu |
| 土耳其 | KW Planner + **Wordstat TR(2026-01 上线,wordstat.yandex.com.tr,土语分词联想)** | **黏着语工作流:Zemberek-nlp(1.4k★)词干+形态分析→保留高频屈折变体→Wordstat 验证后缀族**;URL 一律转写(ı→i/ğ→g/ş→s,禁 percent-encode);**份额口径冲突并记**:StatCounter Yandex ~26% vs 本地机构 3–5%(俄语旅游带 5–7%)——投放前本地实测 |
| 越南 | KW Planner(vi-VN;GKP/Ahrefs 有调无调是独立词条分别查量) | **内容用带调形式(Google 语义评估更优)+混入无调输入变体+slug 无调小写**;Coc Cốc 官方偏好越南语页与 .vn 域(文档化收录因素);**提问式 H2 ≥50% 用真实搜索措辞**(对 SEO/GEO 双高价值);标题 45–65 字符、词进前 30 字符(防 Google 改写) |
| 泰国 | KW Planner(th-TH) | **分词定论:`Intl.Segmenter("th")`(word 粒度)正确切词零依赖——全球主流 SEO 工具栏在泰文站全部错误**;标题按 **grapheme(字素)** 计非字符串长;泰调可读性:句 ≤25 词(>30 罚)、词均 ≤5 字符;`Intl.Segmenter("vi")` 同解越南 |
| 波兰 | KW Planner(pl-PL) | 内容带变音符+**URL/slug 转写(ą→a/ł→l)是六家波兰 SEO 机构一致共识**(转义 %C4%85 体验差);**Bing 桌面 ~13.3%**(全球均值 3 倍)→必做 Bing WMT+IndexNow,B2B 桌面词单独追;**品牌引用按引擎分列**(ChatGPT 偏 PKO/Gemini 偏 mBank——Basta Digital) |
| 荷兰/弗拉芒 | KW Planner(nl-NL/nl-BE) | 词汇分流(wagen/auto's、sloebers/gymschoenen)+**tone 双轨:nl-NL=je(连 B2B)/nl-BE=u(句中小写,商务政务),gij 仅乡土品牌**——同一内容无法靠词汇表通吃;hreflang 高频错误=nl-BE 页误标 nl-NL;**锚文本拒绝虚构比例 norm**(Google 不公布),自然顺序 brand>descriptive>naked>exact |

**跨市场共同纪律**:关键词不互译(各语言独立研究,战略层对齐主题);SERP 证据记录地域与语言;变体归组后再估量,不把变体当独立词;**信源/词量断言带日期**(偏好结论半衰期 6–12 个月);屈折语系(俄/土)一律双频过滤。

**[要追加]/[要確認] 占位符协议**(全语区,源自 indiabiyori/seo-operator):关键词数据缺失或未验证时,输出写 `[要追加: 数据源]` / `[要確認: 来源]` 占位符,**禁止编造搜索量**——LLM 只写建议文,数字必须有可回溯出处。

## 聚类判据与机会公式(百仓深扫:claude-seo 四档/crawlseo 曲线/every-app 阈值)

- **SERP 重叠四档判据**(top-10 有机结果共享 URL 数):**7-10=同一篇文章、4-6=同簇、2-3=互链、0-1=分开**;种子扩 30-50 变体;pillar 2500-4000 词、spoke 1200-1800;每 spoke ≥3 入链且与 pillar 双向。
- **期望 CTR 曲线**(可直接照抄用于潜力估算):pos1=0.28/pos2=0.15/pos3=0.11/pos4-5=0.07/pos6-10=0.03/pos11-20=0.01/>20=0.005;潜力=曝光×expectedCtr(max(1, 位次−3))。
- **机会四分法**(各家口径归并):striking distance=位 4-20 且曝光≥20(或 11-20+高曝光+低 CTR);low_ctr=曝光≥50 且位次≤15 且期望−实际 CTR>2pp;content_decay=28 天 vs 前 28 天点击降幅 ≤−25%(<−50% 记 high);cannibalization=同 query≥2 落地页,加权位次=Σ(位次×曝光)/曝光。
- **蚕食严重度公式**(claude-blog):severity = overlap_count × avg_search_volume × (1/position_gap),gap 最小取 1;四级聚类优先序 exact>stem>语义>subset。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · research/keyword-research/references/keyword-intent-taxonomy.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/research/keyword-research/references/keyword-intent-taxonomy.md)（Apache-2.0）
- 一手资料：[SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)
- 区域段：Yandex Wordstat 官方文档（算子）；Naver DataLab/Ads 官方说明；ラッコキーワード；方言/语域分裂为本地化共识（西语 es-419 组合经 Google hreflang 文档核实；阿拉伯正字变体、印尼 baku/gaul、德语 Sie/du 为从业者共识，标注非量化研究）
