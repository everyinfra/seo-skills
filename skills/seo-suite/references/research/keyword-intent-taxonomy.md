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
- **品牌 + 具体对象**：品牌名单独出现，或品牌加功能、登录、文档、下载，以导航型为主。品牌词与域名的一致性是导航型排名的锚，选域/换域/域名历史风险见 [domain-strategy](domain-strategy.md)。
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

## 完全装载:GEO 难度公式/内容护城河/llm_mentions 决策(百仓深扫)

**GEO 绝对难度公式**(OpenClaudia):`0.35×KD + 0.40×median 竞品页 UR + 0.25×targeting%`——用页级 UR 不用域级 DR(McKinsey 泛文不虚增分);客户相对三档:WON(top-3 或被 AIO 引)/FOOTHOLD(4-10)/NOT RANKING(附差距)。
**llm_mentions 决策规则**:DataForSEO `ai_optimization/llm_mentions`(platform: google|chat_gpt;**Perplexity 不支持**);include_subdomains:true 否则裸域 0 结果;**返回 ≥20 条→跳过猜测直接差距分析;<20 作种子;0 才推测**;推测=gpt-4o-search-preview 实测(~$0.01/问,一次 $0.15-0.20,1-2s 串行)。
**内容护城河公式**(Affitor):目标=TOP5 竞品(排除 Wikipedia/Reddit)平均页数×1.5;分档 <20 页 GREEN/20-50 YELLOW/50-100 ORANGE(收窄利基)/100+ RED;竞品页数用 site: 计数;加速杠杆=独家数据/格式优势/更新速度。

## 深读补充:机会规则/聚类成本/难度评分(R3 组四仓深读,2026-10-09)

**AI 提问词的四类意图分组**(open-seo ai-prompt-research,关键词意图分类在 AI 问句上的等价物):Learning(原理/含义)/Choosing(best/comparison/alternatives/recommendations——**对商业最有价值,答案会点名产品**)/Doing(操作步骤)/Branded(点名品牌或竞品,**单列:测的是声誉不是发现量**)。头词取 1-3 词的短种子("crm" 优于 "best crm for small agencies",精确长短语返回少);跨调用结果按归一化文本(小写/去空白折叠)合并近重复;来源域按可注册域归并(www.semrush.com/semrush.com/sv.semrush.com 算一个);空 sources 的提问单独计数,不当"引无人"。

**SERP 重叠聚类的成本工程**(claude-seo serp-overlap-methodology,四档阈值见上文百仓深扫节,此处补执行优化):全两两对比 N(N-1)/2 次 SERP——40 词=780 次,必须预分组省成本:①先按意图分类(I/C/T/N,去 N)②同头词("CRM software" 变体族)归组③两两对比只在组内跑④各组最高量词跨组抽查。**跳检规则**:同头词+同意图→假定重叠 4-6 不查;不同意图→假定 0-2 除非同头词;被跳过的对抽 20% 验证假定。**3-4 分边界裁决**:同域不同页=更近/同意图=倾向同簇/一方量 10×+=各自成页/拿不准进同簇分页写(宁聚勿散)。**反模式**:绝不按文本相似聚类("dog training tips"vs"classes" 文似 SERP 异);SERP 特性不同(一个出本地包一个出精选摘要)即使 URL 重叠也要分内容型;**打分前滤掉全 SERP 常客域**(Wikipedia/Reddit 类,取全库前 5 常见域);单会话内缓存 SERP 结果复用(A-B 拉过的 A-C 不再拉)。

**簇结构与执行闸门**(claude-seo hub-spoke + execution-workflow):每 pillar 挂 2-5 簇×每簇 2-4 篇(pillar 2500-4000 词/spoke 1200-1800 词已入上节);模板按意图自动选:信息宽=ultimate-guide/信息 how=how-to/信息 list=listicle/信息概念=explainer/商业比较=comparison/商业评估=review/商业排名=best-of/交易=landing-page——多个匹配时看 SERP 实际内容形态(前列全是 listicle 就用 listicle)。锚文本多样性:**同一锚文本对同一页占比 ≤40%**。执行顺序=**pillar 先行→spoke 按量降序**;回链注入用占位符 `<!-- cluster-link:ID -->` 在写作时预埋,目标页上线后回填;中断恢复:产出 <50% 目标字数视为未写,重做。**交付记分卡**:内链密度 ≥3/篇、孤儿页 0、spoke→pillar 连通率 100%、pillar→spoke 100%、簇内互链实现率 ≥80%、同主词页数 0(蚕食)、实际/目标字数偏差 ≤10%——任一闸门失败不得静默通过。

**内容件优先级权重**(gooseworks topical-authority-mapper):搜索量 25%×竞争缺口 25%×意图匹配(ICP)20%×簇完整度 15%×制作成本 15%。**缺口分类四型**(seo-opportunity-finder):hard gap(对手有页我全无,高优)/soft gap(我有但薄<500 词或过时,中优)/positioning gap(对手占据的簇正对我 ICP 核心痛点,高优)/informational gap(高流量低商业意图,低优);商业意图 1-5 分(5=直指产品"best AI SDR tools"/4=问题意识无产品/3=相邻痛点/2=教育沾边/1=泛流量),**≥3 分才进排期**。

**竞品词差三桶**(Ryze competitor-gap,替代单一大 gap 概念):Gap(对手 top-20、我零曝光→新建内容)/Behind(双排但对手领先 ≥5 位→改现有页)/Ahead(我反超——简要报,这是护城河)。对手排名是估算、我方 GSC 是实测,**输出必须标注哪个数是哪个口径**;竞品品牌词默认丢,除非要做 vs/alternative 页——单列候选。

趋势判读要落到原始数据时,Google Trends 四分法与 Google Scholar organic 的字段级模型(主键/merge/去重/免费替代路径)见 [serp-data-models.md](serp-data-models.md)。

**Impact × Confidence 双轴评分**(ericosiu content_attack_brief,可直接代码化,已同步进 scripts/gsc_mining.py 头注):Impact(0-10)=量档(≥10k+3/≥2k+2/≥500+1)+CPC 档($15+3/$5+2/$1+1)+漏斗档(BOFU+2/MOFU+1)+趋势档(>50%+2/>20%+1);Confidence(0-10)=KD 档(≤10+4/≤20+3/≤35+2/≤50+1)+现有位次(≤10+3/≤30+2/≤50+1)+主题权威加成(该词落在本站内容指纹主题内且指纹计数>5,+2);优先级=Impact×Confidence。**趋势判读**:12 个月量史取首 3 月均值 vs 末 3 月均值,>50%=Surging/>20%=Rising/>5%=Growing/±5%=Stable/≥-20%=Declining/更低=Falling。**漏斗词表**:BOFU 触发词=agency/services/hire/pricing/tools/software/best/vs/alternative/platform/cost/price/company/firms/consultant/consultancy/outsource;MOFU=how to/guide/strategy/examples/case study/roi/tutorial/template/checklist/tips/framework/what is/explained/overview/comparison。**执行路径分派**:KD≤20 且无页→全自动新建;已有页且 KD≤50→全自动刷新;KD≤40→半自动(AI 起草人审);KD≤60→人写 AI 优化;更高→专家写+外链。**衰退检测 28d vs 90d 口径**:90 天点击×(28/90) 归一成日均再比,仅 c90>5 才判,c28<c90×0.7(即降 >30%)记衰退。**竞品 gap 硬阈值**:对手 best_position ≤20 且我 >50(或零曝光),过相关性词表+噪音黑名单双滤(login/coupon/what is/wikipedia 类不进 gap)。

## 需求发现:反查平台免费子域的「新出现自然点击」(2026-10-17 并入)

**思路**(社区经验,来源 X @aiRobertDaily 2026-10-16;工具界面与付费边界 2026-10-17 核验):不少人先用托管平台的免费子域(如 `*.vercel.app`)快速上线试水。某个子域开始拿到自然搜索点击,相当于别人替你试过一轮需求。反查「平台根域下新出现点击的子域落地页」,能拿到一份低成本的**选题种子**清单——只是线索,不是结论,后面必须过本文的意图判定和 SERP 核验。和 `scripts/trend_scout.py`(HN/Reddit 热度)互补:那边看讨论热度,这边看已经被搜索验证过的落地页。

**操作(Similarweb,菜单名以 2026-10 界面为准)**:
1. Keyword research → Website explorer → Landing pages,输入平台根域 `vercel.app`(输入类型显示为 Domain)。
2. 切到 Organic Pages,Clicks change 筛选选 **New Clicks**,时间选单月或最近 28 天。
3. 看哪些子域 URL 进了榜,点该行的 All keywords 展开驱动点击的关键词。
4. 先剔除子域自己的名字(导航词),剩下的词去 Google Trends 看形态和地区分布(字段口径见 [serp-data-models.md](serp-data-models.md)),再按上文「用实际 SERP 核验」判意图。

**已核实(2026-10-17)**:
- Landing Pages 工具在 Similarweb 官方知识库有说明:按 URL 列出估算点击、环比变化、排名词数和 Top Keyword,行内可展开驱动该 URL 的关键词;输入类型分 Domain / Exact URL / Prefix / Subdomain 四种。
- Clicks change 的官方口径:Trending=点击环比 >10% 且当月 >100;De-Trending=环比 <-10% 且当月 >100;Lost Clicks=当月 0、上月 >0;**New Clicks=当月 >0 且上月 =0**。这是**环比**口径:"新出现"只表示上月没有点击,不等于新建的站,季节性回流也会落进来。原帖说时间选最近 1–12 个月,截图里实际选的是单月;选多月区间时 New Clicks 怎么算,未核实。
- 输入平台根域后能列出子域 URL:原帖截图可见(vercel.app 以 Domain 类型输入,单月列出 1.7 万余个 URL)。官方文档没写明 Domain 输入是否涵盖子域;换平台用之前,先确认列表里出现的确实是子域 URL。

**付费边界(Similarweb 官网定价页,2026-10-17)**:
- Landing Pages(organic and paid)只在带 SEO Intelligence 的自助档里:Competitive Intel & SEO & AEO,年付折合 $333/月,按月付 $399/月(更高的含 Ads 档也有)。入门的 Competitive Intelligence 档(年付折合 $125/月)不含。
- 单独的 Subdomains 报告不在任何自助档里,只出现在企业定制套餐;自助用户只能走 Landing Pages 这条路。
- 免费部分:similarweb.com 的公开页面只给高层样本,不能下钻。官方博客(2024-06)写的是 7 天试用、需绑卡、每天限 15 次操作;试用期能不能打开 Landing Pages,未核实。

**局限**:
- 点击数是 Similarweb 的**估算值**(官方文档原词即 estimated),小子域误差更大。只拿来排序找线索,不当搜索量入账,不写进对外材料。
- 原帖截图里排在前面的子域,Top Keyword 多是子域自己的名字。这类导航词证明不了需求,要先剔除。
- 子域站本身质量参差,拿到的词必须过意图判定和 SERP 实看;Trends 是相对值,只用来看形态和拐点,不用来比绝对量。
- 只能看到已经拿到点击、且被 Similarweb 数据覆盖的子域;覆盖不到的地区和长尾小词看不见。

**同一思路可延伸到(未核实)**:netlify.app、pages.dev、github.io、replit.app、framer.website 等提供免费子域的平台。用之前先确认工具能把该根域下的子域 URL 列出来。

**其他工具里的相近能力(只列核实过的功能,没有在平台根域上实测过)**:
- Semrush Organic Research 的 Position Changes 报告可按 New / Improved / Declined / Lost 筛选(官方博客 2024-09)。同一来源写的免费账号额度是每天 10 次请求、每份报告 10 行、无历史数据——对平台根域这种量级基本不够用。
- Ahrefs Site Explorer(付费)有 Top pages、Top subdomains 报告(官方 Traffic Checker 页介绍)。免费 Traffic Checker 能不能列出平台根域下的子域,未核实。

## 新站选词:词根拓词、KGR 粗筛与「四找」研究循环(社区经验,2026-10-17 并入)

来源:X @qianshuixia2026 2026-10-17 长文(作者整理哥飞公众号文章的二手笔记);KGR 定义按提出者原文核对。本节都是社区经验法则,**不是 Google 指标**,只用于新站起步阶段的粗筛和练手;正式选词仍按本文前面的意图判定和 SERP 核验。

**需求词根拓长尾**:工具型需求常挂在固定的动作词根上,原文列出 generator / creator / maker / builder / checker / converter(原文称共 51 个,只列了这 6 个,其余不补猜)。做法:`[对象] + [词根]` 批量组合 → 进关键词工具补搜索量 → 用下面的 KGR 粗筛 → 判意图(要生成、要转换还是要看教程,页面形态完全不同)。工具页与配套说明文的打法见 [site-type-playbooks.md](../overview/site-type-playbooks.md) 的 ⑥ 工具站。

**KGR(Keyword Golden Ratio)**:由 Doug Cunnington(Niche Site Project)提出。KGR = 标题含该短语的 Google 结果数(搜 `allintitle:短语`)÷ 月搜索量,**只适用于月搜索量 <250 的词**(素材原文漏了这个上限)。提出者的判读:<0.25 收录后应进前 100;0.25–1 应较快进前 250;>1 说明量虽低但竞争已不小。使用边界:
- 依据是提出者自家站的案例,没有对照研究;筛出来的词仍要看 SERP 前十的页面类型和强弱。
- 各工具的搜索量口径不同,提出者建议固定用一个工具算,只比相对大小。
- `allintitle` 要人工查:提出者说明该运算符被 Google 限频;Google 垃圾政策把未经许可向 Google 发送自动查询(包括为查排名抓取结果)列为违规——不要写脚本批量跑。
- 同一对象的多个近似 KGR 词(加 review、加型号后缀之类),内容高度相似时合并成一页(提出者 FAQ),和上文「混合意图」的拆页判断一致。

**「四找」研究循环**:词找词(种子词扩相关词)→ 词找站(搜这些词,记 SERP 前十的站)→ 站找词(把站放进流量工具,看它的非品牌词和着陆页)→ 站找站(SERP 里冒出来的新站再放回工具)→ 回到词找词。原文转述的新手训练版:
1. 在 Similarweb 一类流量工具里打开一个靠自然搜索起量的标杆站,先看自然搜索流量占比;
2. 抽出非品牌核心词,记下每个词对应的着陆页 URL;
3. 逐个打开着陆页,记 Title、Description、H1 和页面字数(原文用 AITDK 浏览器插件);
4. 拿这些词去 Google 搜,记下第一页前十的全部竞争页;
5. 前十里冒出来的新站,再放回流量工具,循环。

流量工具的数字都是估算(口径与局限见上一节);按 SERP 选竞品的方法见 [gap-analysis-frameworks.md](gap-analysis-frameworks.md)。

**三个练手站(社区经验,逐级加难度)**:
1. **只练全流程**:起一个独一无二的站名,买便宜域名,跑通解析、部署、统计代码、Search Console 验证、等收录。验收=在 Google 搜这个站名排第一。
2. **练选词和基础外链**:挑一个每天几十次搜索、几乎没有竞争的长尾词做核心页,收录后补几条基础外链或目录提交(纪律见 [backlink-directory.md](backlink-directory.md)),观察排名从几百名外逐步进前三页、再到第一页。
3. **练内页矩阵和树形内链**:挑一个每天几百次搜索、有一定竞争的实用词,铺一批内页,按分类组织内链([link-architecture-patterns.md](../technical/link-architecture-patterns.md))。验收=内页开始拿长尾流量,首页核心词进第一页。

正式做站时「先收词,再建站」的流程见 [topic-cluster-templates.md](topic-cluster-templates.md)「规划步骤」的新站版。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 深读来源（R3 组，2026-10-09）：[every-app/open-seo](https://github.com/every-app/open-seo) `.agents/skills/ai-prompt-research/SKILL.md`（Apache-2.0）；[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-cluster/references/serp-overlap-methodology.md`、`hub-spoke-architecture.md`、`execution-workflow.md`（MIT）；[gooseworks-ai/goose-skills](https://github.com/gooseworks-ai/goose-skills) `skills/seo/composites/topical-authority-mapper/SKILL.md`、`seo-opportunity-finder/SKILL.md`（MIT）；[Ryze-AI-Adgent/open-seo-mcp-skills](https://github.com/Ryze-AI-Adgent/open-seo-mcp-skills) `skills/competitor-gap/SKILL.md`；[ericosiu/ai-marketing-skills](https://github.com/ericosiu/ai-marketing-skills) `seo-ops/content_attack_brief.py`
- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · research/keyword-research/references/keyword-intent-taxonomy.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/research/keyword-research/references/keyword-intent-taxonomy.md)（Apache-2.0）
- 一手资料：[SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)
- 区域段：Yandex Wordstat 官方文档（算子）；Naver DataLab/Ads 官方说明；ラッコキーワード；方言/语域分裂为本地化共识（西语 es-419 组合经 Google hreflang 文档核实；阿拉伯正字变体、印尼 baku/gaul、德语 Sie/du 为从业者共识，标注非量化研究）
- 需求发现段（2026-10-17 核验）：方法出处 [X @aiRobertDaily 2026-10-16](https://x.com/aiRobertDaily/status/2110993420424778028)（帖文与截图，社区经验）；[Similarweb Knowledge Center · Using Landing Pages](https://support.similarweb.com/hc/en-us/articles/17226212657693-Using-Landing-Pages)（输入类型、Clicks change 四档口径、估算点击）；[Similarweb Web Intelligence 定价页](https://www.similarweb.com/packages/web/)（Entrepreneurs 档功能表）；[Similarweb 博客 · 13 Things You Can Do With Similarweb for Free](https://www.similarweb.com/blog/marketing/marketing-strategy/similarweb-free/)（2024-06，试用条款）；[Semrush 博客 · competitor keyword analysis tools](https://www.semrush.com/blog/competitor-keyword-analysis-tool/)（2024-09，Position Changes 与免费额度）；[Ahrefs Traffic Checker](https://ahrefs.com/traffic-checker)（Site Explorer 报告名）
- 新站选词段（2026-10-17 核验）：素材 [X @qianshuixia2026 2026-10-17](https://x.com/qianshuixia2026/status/2111268767342997847)（整理哥飞公众号文章的二手笔记，社区经验）；KGR 定义、<250 上限、判读档位与近似词合并按提出者原文 [Niche Site Project · Keyword Golden Ratio](https://nichesiteproject.com/keyword-golden-ratio/) 及其 [FAQ](https://nichesiteproject.com/keyword-golden-ratio/faq/)；自动查询口径见 [Google 垃圾政策 · Machine-generated traffic](https://developers.google.com/search/docs/essentials/spam-policies#machine-generated-traffic)

## (ericosiu 深读 2026-10-09c)转化信号词表/异议分类/闭环回读/意图交付闸门

**交易意图的页面侧可机检词表**(conversion-ops `cro_audit.py`,946 行,纯 requests+BS4 无头浏览器外审计——反向用途:给交易/商业调研词的落地页做「意图满足度」静态打分):CTA 动词词表=get started/sign up/start free/try free/book a demo/schedule/download/buy now/add to cart/subscribe/join/register/request/claim/unlock/learn more/contact us/enroll/apply now/shop now(无任何命中即缺转化机制);社证词表=trusted by/used by/case stud/success stor/as seen in/logo+量化社证 `\d+\+?(users|customers|clients|companies)`;紧迫词表=limited time/only N/last chance/countdown/flash sale;信任词表=guarantee/money-back/refund/free trial/cancel anytime/GDPR/SOC 2/HIPAA/ISO/PCI/certified。**8 维权重**:CTA 可见性 0.20 最高,标题清晰/社证/表单摩擦各 0.15,信任/移动/速度各 0.10,**紧迫仅 0.05 且无紧迫时地板 35 分——紧迫非普适要素,按意图取舍**。表单摩擦分档:≤2 字段=90/3-4=75/5-6=55/7-10=35/>10=15,电话字段再 -10(弃填第一因),通用提交文案(submit/send)换利益导向文案。H1:无 H1 -30,词数<3 或>15 各 -10,多 H1 -10;首 CTA 位于页面前 30% HTML=above-fold 代理。行业基准(avg/上四分位):saas 62/78、ecommerce 58/74、agency 55/72、healthcare 52/68、b2b 56/73。

**异议五类=BOFU 商业调研细分**(revenue-intelligence `gong_insight_pipeline.py`):销售通话异议分类 pricing/timing/competition/authority/need——每类对应一族 BOFU 内容词(价格类 price/cost、时机类 when to switch、竞品类 vs/alternative、决策权类 who decides、需求类 do I need);购买信号四枚=budget confirmed/timeline mentioned/decision maker engaged/champion identified;竞品提及带情感(positive/negative/neutral)→vs 页选题与措辞来源。**通话异议挖掘是 GSC 词表之外的 BOFU 词源**(搜索措辞 vs 口头措辞互补)。内容→收入归因三模型 first-touch/linear/time-decay;**漏斗某阶段零归因=内容缺口**,替代纯流量 gap。

**闭环回读协议**(closed-loop-analytics-upgrade,SEO/AEO/GEO 层):追踪面=GSC clicks/impressions/CTR/位次/query×page 组合、GA4 sessions/engaged/conversions、Ahrefs 排名/外链/词移动、**AI 搜索可见度(AIO/ChatGPT 引用/Perplexity)**、**CMS 页面变更日志**(判定因果的锚)。每次晋升必填回读 12 字段:change/owner/baseline window/candidate window/source systems/primary metric/secondary metrics/winner/caveats/decision(promote|keep testing|rollback|unproven)/next patch/next readback date。晋升=候选赢**主指标**(先定主指标再看结果,否则 KPI 卡拉 OK)或暴露可复用信号且下行指标不显著变差;不晋升=量太低/归因太脏/季节性可解释/连接器失败/只有作者喜欢。只读拉数自由,外部写入(发布/CMS/广告/CRM)一律审批。

**SEO 实验晋升闸门**(growth-engine `experiment-engine.py`):胜出=**p<0.05 且 lift≥15%** 双条件;统计=bootstrap CI(1000 次)+Mann-Whitney U;**SEO 类低流量需 30 样本/变体**(content/email 仅 10);赢家自动进 playbook,写新内容前先查 playbook 应用已证规则。

**AI 写作检测=引用资格层**(x-longform-post 24 模式清单+content-ops `experts/humanizer.md`):第一红线=「不是 X,而是 Y」否定平行结构;禁词表(delve/leverage/seamless/robust/testament/pivotal/holistic/paradigm/tapestry/showcase…)在 **AEO/GEO 引用场景惩罚放大**——AI 概览倾向引用不像 AI 写的源;humanizer 专家在面板中权重 1.5x。发布闸门 CI 化(content-ops `scripts/content-quality-gate.py`):评分器先行→阈值过滤(默认 60,可调 75)→conservative 模式全部放行但带质量旗标→失败原因 top3 汇报;**0 篇通过不得静默**,必须提示降阈或改质量。

**意图页面的元素级变体优化**(autoresearch,Karpathy 式):每元素(H1/副标/CTA/痛点段/社证)10 变体×3 轮进化+跨元素杂交,5 专家**单次 API 批打全部变体**;止损=80 分或 3 轮;<70 不发布/70-79 攻最弱维/85+ 放心发;5 轮仍不到 80=定位问题非措辞问题。落地页五维=first_impression/clarity/trust/urgency/would_convert;广告五维含 **relevance=匹配受众意图**;邮件=would_open/would_read/would_click/would_reply/spam_risk。

**社媒分发打分**(podcast-ops+shortform-idea-grill):病毒分=**Novelty×0.4+Controversy×0.3+Utility×0.3**(80+优先发/60-79 填档/40-59 仅补空/<40 砍);短视频双轴独立打:virality(受众广度 25%/新颖 20%/赌注 20%/分享性 20%/证据 15%)、3 秒钩子(清晰 30%/具体 25%/张力 20%/可信 15%/回报对齐 10%),priority=0.4×virality+0.4×hook+0.2×payoff_confidence;**钩子必须可偿还**(3 秒前提成立、后续完整兑付)。竞品 outlier=>2× 频道均值;内容缺口优先「独特专长交集」或「独有数据」。播客→博客输出规范:主词+量/难度估、3-5 副词、meta 155 字符、H2 与 content atom 一一映射、1500-2500 词。

**数据呈现选型**(growth-signal-charts):单一百分比→大数字标注/跨类目量级→条形/两时点两组→斜率图/时间序列→折线/成分合计→瀑布;每图左下角引用(出版方+短题+日期)。

**组合增量**:①SEO 策略评审 10 专家面板(content-ops `experts/seo-strategy.md`)含 **AI/AEO 专家**(AI Overviews/ChatGPT 引用/Perplexity)与 4:1 ROI 闸门,评审判据=数据支撑/可执行具体性/ROI 估算质量/风险评估/可行性/优先级对齐;②视频资产组合脊柱公式 `[Viewer] should believe [verdict] because [proof], then use [framework] to reach [outcome]`——persona 层下游,质量闸 hook/clarity/proof/pacing/payoff 各 0-20;③内容生命周期状态机(content-os-portable-starter,fail-closed):SIGNAL→CANDIDATE→EVIDENCE_READY→DRAFT→REVIEW→APPROVED_FOR_DRAFT_WRITE→DRAFT_WRITTEN→APPROVED_FOR_PUBLISH→PUBLISHED→READBACK→LEARNING,每步持久化+可归因+幂等+缺审批即阻塞;④eval 基线回归模式:保存 score_pct 基线,后续运行比 Δ 即报警——关键词/CTR 监控同构可直接套用。

本节来源(均为深读,2026-10-09):[ericosiu/ai-marketing-skills](https://github.com/ericosiu/ai-marketing-skills) 16 个目录——conversion-ops(cro_audit.py 源码)、revenue-intelligence、closed-loop-analytics-upgrade、growth-engine、autoresearch、content-eval、content-ops(SKILL.md+experts/seo-strategy.md+experts/humanizer 摘要+scripts/content-quality-gate.py 源码)、x-longform-post、podcast-ops、shortform-idea-grill(references/scoring-rubric.md)、short-form-pipeline、growth-signal-charts、video-content-engine、leveling-up-content-engine、content-os-portable-starter、eval(run-eval.ts);基准分/阈值/权重均为该仓内置常量,非独立研究,引用时注明出处。
