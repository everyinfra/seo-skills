# भारतीय बाज़ार(印度/印地语市场)

> 建立于 2026-10-09;第一轮英/印双语增量研究(StatCounter/Statista/Google 官方博客/Google for India/TechCrunch/Bain 官方/IAMAI 口径转引/印度发行商与从业者 2026 指南)。断言半衰期 6–12 个月。配套:总纲见 [multilingual-workflow](../overview/multilingual-workflow.md),AI 平台差异见 [geo-platform-differences](../content/geo-platform-differences.md),阈值口径见 `scripts/markets.json` 的 `hi` 条目。

## 一、格局(एक Google、一个 ChatGPT、Discover 先于 Search)

### 1.1 引擎

- **Google ~96.7%**(StatCounter,2025-09→2026-09 窗口),移动端 **~99.2%**(Statista,2026-07)——比全球均值更极端的单引擎市场;Bing 1.9% 不构成第二面。
- 本市场的"第二引擎"不是 Bing,是 **ChatGPT**:印度 **1 亿周活**(Altman 2026-02-15 官宣),**全球第二大市场**,且是 OpenAI **API 前五市场**——AI 答案层的份额比多数市场提前到位。
- 搜索市场 **~75% 移动**;GEO 时间表按移动优先排。

### 1.2 Discover>Search(印度发行商市场的结构性事实)

- Google Discover 是**多数印度新闻站最大流量来源**(15–30% 流量;State of Indian Digital Publishing 2026)。
- **区域/vernacular 发行商 Discover 占全部会话 80–90%**(Praman masterclass 口径)——对中部发行商,Discover 不是 Search 的补充,是主渠道。
- 叠加 Search 自然流量普遍下滑(发行商自报 60–80% 区间)后,部分站 Discover 占有机引荐 **65–70%**。
- Google 官方口径 Discover"比 Search 更不可预测,应作补充流量对待"——印度场景下该口径与实际依赖度**倒挂**,风险见六。

### 1.3 语言人口面

- ~9.5 亿网民,农村占 55%;**~98% 用户消费 Indic 语言内容**(IAMAI 口径转引),57% 城市用户偏好区域语言内容。
- **Hindi 是最大单一语种但不是全部**:泰米尔/泰卢固/孟加拉/马拉地构成独立增量市场(见 2.3)。
- vernacular 内容市场 2026 年 **~$1.35B → 2031 ~$3.13B**(Ken Research,15% CAGR)。
- 品牌预算普遍仍按"区域语言≈30% 市场"配置——**预算结构与人口结构倒挂**是本市场最大的套利空间。

### 1.4 就绪闸门

- `hi-IN` 与 `en-IN` **分开评分**通过 + **Hinglish 三写决策记录**(见 3.1)落盘——未过不做增量投入。
- 英文版 90 分掩盖 Hinglish/印地语版 40 分,是本市场最常见失败模式(同阿语区)。

## 二、चैनल(渠道:聚合器守门人、vernacular、语音)

### 2.1 聚合器守门人(JustDial/IndiaMART/Sulekha)

- **JustDial**:印度最高 DA 目录站,程序化 **城市×品类页覆盖 1000+ 城市**(技术面=页/城/品类 playbook)——在"城市+服务"类查询上系统性压制 SMB 自有站。
- **IndiaMART** 垄断 B2B/工业品查询;**Sulekha** 覆盖本地服务;TradeIndia 次之。
- 动态:聚合器靠 DA+程序化页在 Google 上**排在小企业前面**,再把这些曝光卖回给小企业(付费收录/线索)——**守门人经济**:审计时区分"在聚合器上占位"(必要,作实体与引用信号)与"只靠聚合器获客"(租金依赖)。
- 实体一致性三件套:JustDial/IndiaMART/Sulekha 收录 + Wikipedia(en/hi)+ Google Business Profile;实体名、音译别名、印英双写统一计数。

### 2.2 语音:29 词问句市场

- 语音查询均长 **~29 词(约为打字的 7 倍)**;对照印度打字查询均长 **3–4 词**——两个关键词形态学完全不同,不可共用词表。
- 印度语音搜索增速 **~270% YoY**(Google 数据转引),语音用户 3 亿+;**~70% 新用户语音优先**(打字门槛高)。
- 60% 印度 AI 用户以语音交互、59% 用过区域语言(Northstar 口径)。
- 词形:**助词词库(kaise/kya/konsa/batao/karne/wala)× 产品词** 组态是语音层关键词的主形态(KB 继承,外部数据侧证)。

### 2.3 vernacular(泰米尔·泰卢固是独立市场)

- 泰米尔/泰卢固内容消费与 YouTube 语音搜索增速**快于英语**;印地语站不可代替泰米尔/泰卢固站——hreflang 分层 `ta-IN`/`te-IN` 独立决策。
- Vernacular 发行商是 Discover 依赖最深的群体(80–90% 会话)——技术 SEO 面弱 + 单渠道依赖,审计必查。

## 三、भाषा तंत्र(语言机制:Hinglish 三写是硬检查)

### 3.1 Hinglish 三写(本市场最重要的语言事实)

同一意图存在三种书写,查询量分布随人群/场景漂移:

| 书写 | 例(买笔记本) | 匹配页面语言 | 备注 |
|---|---|---|---|
| 罗马化 Hinglish | best laptop kharidna hai kaise | **英文页+Hinglish FAQ/标题** | 城市主力写法;Google 2021 起官方支持罗马化印地语 |
| 天城体印地语 | बेस्ट लैपटॉप कैसे खरीदें | 印地语页 | 农村/语音转写偏好 |
| 英语 | best laptop to buy | 英文页 | en-IN 站默认 |

- Google 官方确认:拉丁字母打的印地语查询会映射到印地语结果(2023 multilingual search 博客)——**引擎已做跨书写匹配,你的页面没做就是纯损失**。
- 战术:核心词按三写**归组追踪、分开落地**——罗马化 Hinglish 由英文页承接(标题/H2/FAQ 用 Hinglish),天城体由 hi 页承接;勿建三份镜像页。
- aap/tu 语域分层:B2B/金融用 aap 级正式体,社交/娱乐可口语体。

### 3.2 GSC regex 快照缺口诊断法(KB 方法,外部侧证)

1. GSC Performance→Queries→**正则过滤天城体区段** `[\u0900-\u097F]` 截一版快照;
2. 换罗马化 Hinglish 助词正则(`kaise|kya|konsa|hai|karo|batao`)再截一版;
3. 对照两版快照的**承接页语言**:天城体查询落在英文页、或 Hinglish 查询零展示=**语言错配缺口**;
4. 修复按 3.1 落地表执行(hreflang/独立段落/标题重写),**不做机翻镜像**(见六)。
- 该方法的产出是"排名尚可但语言错配"的页清单——这是印度站最常见的隐性损失。

### 3.3 数字与格式

- **lakh/crore 分组**:`1,23,456.78`(3-2-2 印度式),价格 ₹ + lakh/crore 口语单位;混用西式 `123,456` 在商业页是未本地化信号。
- 日期 `9 अक्टूबर 2026`;电话前缀 **+91**;`+91` 出现在页面是本地实体信号。

### 3.4 拼写漂移

- 音译漂移(color/colour、kya/kia、sasta/sasta≤变体)按 **IndicXlit 类音译规范化聚类**,当变体归组研究;呈现侧保留主流写法。

### 3.5 长度

- 印地语文案比英文**长约 10–15%**(KB 口径,弱于阿语 20%):title 60 字符/desc 155 字符留余量。

## 四、AI-GEO(印度是全球 AI 搜索的压力测试场)

### 4.1 时间线(官方)

| 事件 | 日期 | 来源 |
|---|---|---|
| AI Mode 进印度 Search Labs(**美国外首个市场**) | **2025-06-24** | Google |
| AI Mode 加印地语(同期+日/印尼等) | **2025-09-08** | Google |
| Search Live(印地语/英语)+ AI Mode 扩 9 种印度语言 | 2025-10 Google for India | Google 官方博客 |
| ChatGPT 印度 1 亿周活(第二市场) | **2026-02-15** | OpenAI/Altman |

### 4.2 依赖度基线

- **~80% 搜索用户至少 40% 的时间依赖 AI 摘要;~60% 搜索零点击**(Bain–Dynata,2024-12,n=1,117,全球口径;印度移动+AI 渗透高于均值,实际只高不低)。
- 印度"下一代搜索市场"2025 ~$1.54B;**60% 印度搜索者以 AI 辅助搜索开启每日查询**(行业口径)。
- 发行商侧:Google 传向 ~100 家出版商为 AI 答案付费(2026 报道)——引用经济学在印度提前进入"付费墙"阶段,watch 项。

### 4.3 印度专属 GEO 纪律

- AI 引用审计**必须双提示跑**:罗马化 Hinglish 与天城体提示的结果分布不同(引擎跨书写匹配≠生成引擎同样跨书写);只用英语提示测印度市场=白测。
- 语音层 GEO:29 词问句形态直接进 FAQ/schema(`Question` 文本用口语全句,不用关键词残片)。
- ChatGPT 作为事实上的第二引擎:**1 亿周活**意味着 Perplexity/Gemini 之前先测 ChatGPT 印地语+Hinglish 提示的引用。

### 4.4 本土模型 watch

- **Sarvam AI**(印度 AI Mission 主权栈,22 种印度语言,见七)有独立 API/爬虫生态;Krutrim 等次之——watch 项非必做项;ChatGPT/Gemini 仍主导实际使用。

## 五、आउटसोर्सिंग की सच्चाई(外包真相:三层价格)

印度是 SEO 外包最大输出国——"在印度做 SEO"的报价分三层,混层比较是外行信号:

| 层 | 价带(月) | 内容 | 风险 |
|---|---|---|---|
| **T1 商品层** | **₹6,000–15,000**(~$75–180) | 本地 SEO、目录提交、 GBP;按件计 | 目录群发/低质链接;iConnectDM ₹14,999 档等 |
| **T2 中层** | **₹15,000–40,000**(~$180–480) | 全案 on-page+内容+基础链 | 模板化;Hinglish 决策通常缺位 |
| **T3 全案层** | **₹75,000–2,00,000+**(~$900–2,400) | 含 AEO/GEO、技术债、编辑内容 | DigiStreet ₹75k–2L+GST 档等 |

- **白牌转包链**:西方 agency 以 **$300–1,000/月/客户**外包印度,再以 **$800–2,000** 收(WiseMonk/Reddit r/agency 口径)——审计客户供应链时按此价带识层。
- 总带宽参考:**₹8,000–1,50,000/月**(Media Sathi)。
- 判读规则:报价低于 T1 下限(~$75/月)≈ 链接农场;T2 报价但要 T3 交付(GEO/多语言)= 范围幻觉。

## 六、लाल झंडे(红旗)

- **单一英语市场误判**(最贵红旗):en-IN 单语策略覆盖不了 98% Indic 内容消费人群;品牌预算按"区域≈30%"配置与人口结构倒挂——审计第一问:query 三写分布测过吗?
- **聚合器租金依赖**:在 JustDial/IndiaMART 付费买线索≠渠道策略;自有实体面(GBP+官网+维基)缺席时,聚合器占位只是给守门人交租。
- **Discover 单点依赖**:区域发行商 80–90% 会话来自 Discover,且 Google 明示其不可预测——Discover 依赖度 >50% 即标红,需 Search/AI 引用/直接流量再平衡。
- **机翻镜像无 AI 引用**:机器翻译印地语镜像页被 AI 引擎低信任;逐句改写不足以修复——须原生 Hinglish/印地语写作(同阿语区纪律)。
- **三写当三市场**:为同一意图建三份镜像页(罗马化/天城体/英语)触发重复内容+索引膨胀;正确做法是归组追踪+按 3.1 分开落地。
- **lakh/crore 缺失**:商业页出现西式 `123,456` 分组=未本地化硬信号。
- **英语提示测印度 GEO**:跨书写提示分布不同,英语提示的引用审计结果不可外推。

## 七、औज़ार(工具栈)

| 功能 | 工具 | 注 |
|---|---|---|
| 印度语言 AI 栈 | **Sarvam AI API** | 主权栈 22 语言:Sarvam-M 24B(10 印度语言)/Saaras STT/Bulbul TTS/翻译;开发者免费层 |
| 音译归一 | **IndicXlit** | 拼写漂移/三写变体聚类研究侧 |
| 关键词 | Google KW Planner + suggest(印地语) | Ahrefs/Semrush 印地语数据薄;suggest 是免费 Hinglish 语料 |
| 快照诊断 | GSC Performance regex(天城体区段+助词正则) | 3.2 缺口修复法 |
| 语音词形 | 助词词库(kaise/konsa/batao)×产品词 | 29 词问句形态 |
| 聚合器占位 | JustDial/IndiaMART/Sulekha/TradeIndia | 实体+引用信号;守门人经济审计 |
| 本地实体 | GBP + Wikipedia(en/hi) | 实体一致性三件套 |
| AI 测量 | GSC 生成式 AI 报告 + GA4 AI referrer 正则 + ChatGPT 印地语/Hinglish 双提示 | 引用审计双提示纪律 |
| hreflang | `hi`+`hi-IN`+`en-IN`;vernacular 另挂 `ta-IN`/`te-IN` | 泰米尔/泰卢固独立决策 |

## 来源类型标注

- **官方**:Google 官方博客(Google for India:AI Mode 2025-06-24 首发/2025-09-08 印地语/Search Live;multilingual search 2023-09)、OpenAI/Altman(1 亿周活,2026-02-15)、StatCounter(96.69%)、Statista(移动 99.17%,2026-07)、Bain–Dynata(80%/60%,2024-12,n=1,117)。
- **研究/行业**:IAMAI 口径转引(98% Indic 消费/9.5 亿网民)、Ken Research(vernacular 市场 $1.35B→$3.13B)、State of Indian Digital Publishing 2026(Discover 15–30%)、Praman(区域发行商 80–90% 会话)、Lumenario(AIO 对印度中部发行商冲击)。
- **从业者共识/案例**:JustDial 1000 城程序化案例(LinkedIn 拆解)、BundledSEO(罗马化→英文页/天城体→印地语页)、Digital Applied(语音 29 词)、ET Travel×MakeMyTrip(打字 3–4 词)、WiseMonk/Media Sathi/DigiStreet/Kunal Dabi(三层外包价带)、Northstar(60% 语音 AI/59% 区域语言)。
- **KB 继承**:Hinglish 三写归组、GSC regex 快照缺口法、助词词库×产品词、IndicXlit、lakh/crore、聚合器占位审计——见 multilingual-workflow.md 印度段与 `scripts/markets.json` 的 `hi` 条目。
