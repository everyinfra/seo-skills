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

- **~80% 搜索用户至少 40% 的时间依赖 AI 摘要;~60% 搜索零点击**(Bain–Dynata,2024-12,n≈1,100;**2026-10-09 重核修正:样本为美国消费者,非全球口径**——印度依赖度未单独测量,"移动+AI 渗透高于均值故只高不低"是外推假设,引用时须注明)。
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

## 本地实测(2026-10-09,9.5 冲刺轮)

### 重核(一手源双源核实)

| 关键数字 | 重核结果(2026-10-09) | 判定 |
|---|---|---|
| Google ~96.7% | StatCounter 2026-09 印度 **96.63%**(Bing 1.92%) | ✓ 带内一致 |
| AI Mode 进印度 Search Labs=美国外首个(2025-06-24) | Seroundtable+Search Engine Land 双源确认;**增量:印度也是美国外首个 AI Mode 全量开放市场**(Moneycontrol) | ✓ |
| AI Mode 加印地语(2025-09-08) | Google 官方双帖:blog.google en-in 独立公告 + 2025-09-08 五语言扩展(Hema Budaraju 署名) | ✓ 官方 |
| ChatGPT 1 亿周活/全球第二 | 母语多源:Navbharat Times/Amar Ujala/ETV Bharat(口径:美国外第二、亚洲最大,总 WAU ~8 亿);官宣 02-15 vs 报道 02-16/02-21 | ✓ 母语多源;日期口径并记 |
| Bain 80%/60% | 数字双源确认(Bain 官方+Digiday),但**样本为美国消费者**(n≈1,100;另有 n≈3,000 转引);4.2 与来源标注已同步修正 | ⚠ 冲突已修正(全球口径→美国样本外推) |
| IAMAI 98% Indic/9.5 亿网民 | 母语双源(Jagran/Dainik Bhaskar)+IAMAI–Kantar 原 PDF 在线;农村 51–57%(原 55% 在带内) | ✓ |

### 真实站验证(amarujala.com / bhaskar.com × 3 工具)

- `site_audit --market hi`:amarujala — title/desc 超限+跳级 h1→h3+262 链接;bhaskar — 同类+**4 个 AI 检索爬虫(OAI-SearchBot/ChatGPT-User/Claude-SearchBot/PerplexityBot)全被 robots.txt 禁**,退出全部 AI 答案池。`llmstxt check`:**amarujala /llms.txt 200 在场**(印度头部印地语站少见);bhaskar 无。`head_check`:两站均命中 twitter:* 全套/x-ua-compatible/fb:app_id 弃用 ERROR。
- **结构性发现(印度头部双雄姿态两极)**:Amar Ujala=llms.txt 在场+AI 爬虫放行;Dainik Bhaskar=无 llms.txt+四爬虫全禁——天城体新闻的 AI 引用池正被头部主动收缩,做 hi 内容的品牌站 GEO 竞争反而小于英文市场。
- 大站拦截实录:justdial.com 读超时、indiamart.com HTTP 429、hindi.news18.com 403——聚合器/大站对非浏览器 UA 激进拦截,审计先换浏览器 UA 重试再下结论。
- **工具盲区(实测确认)**:
  1. `site_audit.py` 词数对天城体计 **0**(wc() 只数 CJK+拉丁;实测 `wc("बेस्ट लैपटॉप कैसे खरीदें…")=0`)→ 纯印地语页必误报 "词数 <200 soft-thin";罗马化 Hinglish 正常计数——**印地天城文检测未触发,hi 审计的词数结论一律不可信,须人工复核**;
  2. `--market hi` 无任何 hi 专属分支(market 仅 ja 特例 32/120;hi 落通用 60/160,lakh/crore/三写归组均无机检);
  3. title 解析把 `<title>` 后 head 内 CSS/JS 全并入 title(amarujala 报 163,412 字符、bhaskar 234,387)——解析器缺陷,非站方问题;
  4. head_check 微信/QQ itemprop WARN 在非中文市场同样触发(噪音);
  5. 泰米尔(U+0B80–0BFF)/泰卢固(U+0C00–0C7F)同不在 wc() 覆盖内——vernacular 站盲区与天城体相同。

### vernacular 深挖:泰米尔/泰卢固段落级展开(补 2.3 缺口)

**(1) 规模与结构**:泰米尔纳德 ~7,200 万人口、邦级互联网用户第一梯队;泰卢固带(安得拉+特伦甘纳)~1.1 亿人口、海得拉巴科技走廊。母语人口均超多数欧盟国家——"vernacular 区域语言"是误称,实为**两个独立千万级增量市场**。Google AI Mode 九种印度语言清单同时含 ta/te:基础设施已就位而内容供给未跟上,是印度 GEO 的最大套利面。

**(2) 文字与查询形态**:泰米尔正字浅层(音素一致),拼写漂移远低于印地;但英语借词用 Grantha 借音字母(ஸ/ஜ/ஷ)书写,同一借词存在"传统拼写 vs 简化音译"双写——关键词归组前先跑音译聚类(IndicXlit 支持 ta/te)。罗马化混码同样存在:Tanglish(epdi/enna/enga)、Telish(ela/emi/ekkadha)。三写纪律从 Hinglish 外推,**但词表必须按语言重建,不可翻译印地语助词词库**(kaise≠epdi≠ela)。

**(3) 语音问句后缀**:泰米尔口语疑问靠句尾 ஆ?(aa)/வா?(vaa)承载,语音查询常以口语助词收尾——FAQ/Question schema 用口语全句,同 2.2 纪律;泰卢固疑问后缀 -ఆ/-కదా 同理。

**(4) 数字与格式**:lakh/crore 同样适用(泰米尔 இலட்சம்/கோடி,泰卢固 లక్ష/కోటి);日期用本地月名(9 అక్టోబర్ 2026);电话 +91 不变。

**(5) 渠道与风险**:两语发行商 Discover 依赖最深(80–90% 会话,见 1.2)+ 技术面普遍弱(模板 CMS、无 hreflang 层)。审计入口:先查 Discover 单点依赖,再查 `ta-IN`/`te-IN` hreflang 是否独立挂载(勿挂 hi 机翻镜像)。YouTube 是两语第一大内容消费场(泰卢固内容含美国侨民全球消费)——视频词表与站内词表分开做。

**(6) 决策闸门**:泰米尔/泰卢固各自过就绪闸门(分开评分+音译决策记录落盘),任一未过则不做该语增量——与 hi/en 双评分同一纪律,不留"印地语覆盖南印"的幻觉。

## 来源类型标注

- **官方**:Google 官方博客(Google for India:AI Mode 2025-06-24 首发/2025-09-08 印地语/Search Live;multilingual search 2023-09)、OpenAI/Altman(1 亿周活,2026-02-15)、StatCounter(96.63%,2026-09 复核)、Statista(移动 99.17%,2026-07)、Bain–Dynata(80%/60%,2024-12,n≈1,100,**美国样本**)。
- **研究/行业**:IAMAI 口径转引(98% Indic 消费/9.5 亿网民)、Ken Research(vernacular 市场 $1.35B→$3.13B)、State of Indian Digital Publishing 2026(Discover 15–30%)、Praman(区域发行商 80–90% 会话)、Lumenario(AIO 对印度中部发行商冲击)。
- **从业者共识/案例**:JustDial 1000 城程序化案例(LinkedIn 拆解)、BundledSEO(罗马化→英文页/天城体→印地语页)、Digital Applied(语音 29 词)、ET Travel×MakeMyTrip(打字 3–4 词)、WiseMonk/Media Sathi/DigiStreet/Kunal Dabi(三层外包价带)、Northstar(60% 语音 AI/59% 区域语言)。
- **KB 继承**:Hinglish 三写归组、GSC regex 快照缺口法、助词词库×产品词、IndicXlit、lakh/crore、聚合器占位审计——见 multilingual-workflow.md 印度段与 `scripts/markets.json` 的 `hi` 条目。

## 维护

- 复审周期 **90 天**,下一次 **2027-01-09**;signals 清单与 `scripts/markets.json` 的 `markets.hi.review_cycle` 保持一致,以 json 为准。
- 触发即复审的信号:StatCounter 印度月度份额(连续 2 月 >1pp 漂移)、Google for India 年度发布(惯例 Q4)、ChatGPT 印度 WAU 官方口径更新、IAMAI–Kantar 年报、Discover 依赖度行业口径(State of Indian Digital Publishing/Praman)、Sarvam/Krutrim 主权栈动静。
- 断言半衰期 6–12 个月;份额/WAU/价带类数字先于判断类断言过期。
- 增量研究前先读「本地实测(2026-10-09)」的重核表——已修正口径(如 Bain 美国样本、tools 天城文盲区)勿当原始事实再引用。
