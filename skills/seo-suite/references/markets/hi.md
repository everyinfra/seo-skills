# भारतीय बाज़ार(印度/印地语市场)

> 建立于 2026-10-09;2026-10-21 逐条核对一手来源(StatCounter、Google 官方博客与 Search Central、Search Console 帮助、PIB、MeitY、IAMAI–Kantar、Bain)。二手研究标「第三方研究」。断言半衰期 6–12 个月。配套:总纲见 [multilingual-workflow](../overview/multilingual-workflow.md),AI 平台差异见 [geo-platform-differences](../content/geo-platform-differences.md),阈值口径见 `scripts/markets.json` 的 `hi` 条目。写法约定见 [asd-ste100-web-writing](../content/asd-ste100-web-writing.md);标题与首段怎么对齐买家提问见 [question-alignment](../content/question-alignment.md)。

## 一、格局(एक Google、一个 ChatGPT、Discover 要单独看)

### 1.1 引擎

StatCounter 印度搜索引擎份额,2026-09 月值,取数 2026-10-21([页面](https://gs.statcounter.com/search-engine-market-share/all/india)):

| 口径 | Google | 第二名 |
|---|---|---|
| 全设备 | 96.69%(12 月区间 96.38–97.85) | Bing 1.89%、DuckDuckGo 0.62%、Yahoo 0.56% |
| 桌面 | 88.29%(12 月区间 88.29–95.40) | Bing 8.57%、Yahoo 2.70% |
| 移动 | 98.67%(12 月区间 98.41–99.17) | DuckDuckGo 0.70%、Bing 0.31% |

- 旧稿的「移动 99.2%(Statista 2026-07)」本次未核;以 StatCounter 的 98.67% 为准。
- 本市场的第二个答案入口是 ChatGPT:OpenAI CEO Altman 在 2026-02-15(India AI Impact Summit 前)说印度有 **1 亿周活**,美国之外最大、全球第二([NDTV 2026-02-15](https://www.ndtv.com/india-news/india-ai-impact-summit-2026-india-has-potential-to-lead-in-ai-sam-altman-ahead-of-ai-impact-summit-11006719)、[TechCrunch 2026-02-22](https://techcrunch.com/2026/02/22/all-the-important-news-from-the-ongoing-india-ai-summit/))。旧稿「OpenAI API 前五市场」找不到来源,已删。
- 「搜索市场 ~75% 移动」未核,以本站 GSC 设备拆分为准。

### 1.2 Discover 要单独看

- Google 官方原文:「Traffic from Discover is less predictable or dependable when compared to keyword-driven search visits.」([Get on Discover](https://developers.google.com/search/docs/appearance/google-discover),更新 2026-03-09)。
- 旧稿的「Discover 占多数印度新闻站流量 15–30%」「区域发行商 Discover 占会话 80–90%」「Discover 占有机引荐 65–70%」出自行业报告和讲座转述,没有可核原文,已删。**用自己站的 GSC Discover 报告判断依赖度**(见检查清单)。
- 做法(本套件口径):Discover 占自然流量超过本套件设定的预警线(默认 50%)时,标红并平衡 Search、AI 引用和直接流量。

### 1.3 语言人口面

- IAMAI–Kantar《Internet in India 2024》原文:2024 年有 **8.7 亿**互联网用户(占互联网用户的 **98%**)访问过印度语言(Indic)内容;**57%** 的用户表示在印度城市地区偏好用印度语言获取互联网内容([IAMAI 报告 PDF](https://www.iamai.in/sites/default/files/research/Kantar_%20IAMAI%20report_2024_.pdf))。2025 年报告写互联网用户超过 9.5 亿(Scribd 上的报告页,未读原 PDF)。
- 旧稿「农村占 55%」「vernacular 内容市场 $1.35B→$3.13B(Ken Research)」「品牌预算按区域语言≈30%配置」未核,已删。
- 印地语是最大单一语种,但不是全部:Google 2025-10-08 的印度公告把 AI Mode 扩到孟加拉语、卡纳达语、马拉雅拉姆语、马拉地语、泰米尔语、泰卢固语、乌尔都语(见 4.1)。

### 1.4 就绪闸门

- `hi-IN` 与 `en-IN` 分开评分;Hinglish 三写决策记录落盘(见 3.1)。未过不做增量投入。
- 英文版 90 分会掩盖印地语或 Hinglish 版 40 分(本套件口径)。

## 二、渠道

### 2.1 聚合器(JustDial、IndiaMART、Sulekha)

- JustDial 是印度大型本地目录,有大量「城市 × 品类」页(行业拆解称覆盖千余城市,来源是 LinkedIn 帖,未核)。IndiaMART 覆盖 B2B 与工业品查询;Sulekha 覆盖本地服务。
- 聚合器在「城市+服务」类查询上常排在小企业前面,是本套件的观察(本套件口径)。审计时区分两件事:在聚合器上占位(实体与引用信号,必要);只靠聚合器获客(租金依赖)。
- 实体一致性:JustDial/IndiaMART/Sulekha 收录 + Wikipedia(en/hi)+ Google Business Profile;实体名、音译别名、印英双写统一。
- 大站对非浏览器 UA 常拦截(见本地实测)。

### 2.2 语音与长查询

- Google 官方(全球口径):AI Mode 用户提问长度约为传统搜索的近 3 倍([Google 印度博客 2025-10-08](https://blog.google/intl/en-in/products/supercharging-search-for-india-new-languages-in-ai-mode-search-live-debuts/))。
- 旧稿的「语音查询均长 29 词」「语音增速 270%」「语音用户 3 亿+」「70% 新用户语音优先」「Northstar 60%/59%」全部找不到原文,已删。
- 词形假设(本套件口径):助词词库(kaise、kya、konsa、batao、karne、wala)× 产品词,是口语化长查询的主形态。用自己 GSC 里的长查询验证。

### 2.3 区域语言

- 泰米尔语、泰卢固语是独立的内容市场。印地语站不能代替它们。hreflang 另挂 `ta-IN`、`te-IN`,分别决策。
- 旧稿中泰米尔纳德与泰卢固地区的人口数字(7,200 万、1.1 亿)和 YouTube 增速说法未核,已删。

## 三、语言机制

### 3.1 Hinglish 三写

同一意图有三种书写,查询量分布随人群与场景漂移:

| 书写 | 例(买笔记本) | 承接页 |
|---|---|---|
| 罗马化 Hinglish | best laptop kharidna hai kaise | 英文页 + Hinglish FAQ/标题 |
| 天城体印地语 | बेस्ट लैपटॉप कैसे खरीदें | 印地语页 |
| 英语 | best laptop to buy | 英文页 |

- **Google 官方**:Search Central 博客(2023-09,Sunny Nahar 等)写明:印度用户可能因键盘不便用拉丁字母搜印地语,Google 会给出两种书写的印地语结果,「want and receive Hindi results written either way」([How Google Search handles multilingual searches](https://developers.google.com/search/blog/2023/09/multilingual-searches))。更早的 2020-12-17 报道称 Google 搜索会对用英文字母键入的印度语言显示相应语言结果(Indian Express);旧稿「2021 年起」改为 2020-12。
- 本套件口径:核心词按三写归组追踪、分开落地。罗马化 Hinglish 由英文页承接(标题、H2、FAQ 用 Hinglish),天城体由印地语页承接。不建三份镜像页。
- hreflang:`hi`、`hi-IN`、`en-IN` 都是合法写法(ISO 639-1 + ISO 3166-1 Alpha-2,[Google 文档](https://developers.google.com/search/docs/specialty/international/localized-versions));Google 不靠 hreflang 或 lang 判断页面语言。`hi-Latn`(IANA 子标签表含 Latn 文字码)可用于 HTML `lang` 属性,Google 的 hreflang 文档没有列它,所以不把它写进 hreflang。
- aap/tu 语域:B2B、金融用 aap 级正式体,社交、娱乐可口语体(本套件口径)。

### 3.2 GSC 正则快照缺口诊断

1. Search Console → 效果 → 查询 → 筛选 → 自定义(正则),选「匹配」。
2. 第一版:天城体。**GSC 的正则用 RE2 语法**([Search Console 帮助](https://support.google.com/webmasters/answer/17011165))。RE2 不支持 `ऀ` 写法(用 google-re2 实测:`invalid escape sequence: \u`)。用 `\p{Devanagari}` 或 `[\x{0900}-\x{097F}]`(两者在 google-re2 中编译并匹配成功)。旧稿的 `[ऀ-ॿ]` 在 GSC 里会报错或不匹配。
3. 第二版:罗马化 Hinglish 助词正则,例如 `kaise|kya|konsa|hai|karo|batao`。
4. 对照两版的承接页语言。天城体查询落在英文页,或 Hinglish 查询零展示,就是语言错配缺口。
5. 修复按 3.1 落地,不做机翻镜像。

### 3.3 数字与格式

- 印度分组 `1,23,456.78`:Unicode CLDR 的 `hi` 与 `en-IN` 区域都用 `#,##,##0.###`(3-2-2 分组),货币格式 `¤#,##,##0.00`(cldr-json,取数 2026-10-21)。混用西式 `123,456` 在商业页是未本地化信号(本套件口径)。
- 日期 `9 अक्टूबर 2026`;电话前缀 +91。

### 3.4 拼写漂移

- 音译变体(color/colour、kya/kia)按音译规范化聚类。AI4Bharat 的 IndicXlit 是 21 种印度语言的音译模型(GitHub 仓库描述,最近一次提交 2023-10-13)。

### 3.5 长度

- 旧稿称印地语文案比英文长约 10–15%,无来源。title 60、description 155 是本套件口径。用 `parity_check.py` 对一页英印版实测。

## 四、AI-GEO

### 4.1 官方时间线

| 事件 | 日期 | 来源 |
|---|---|---|
| AI Mode 在印度以 Labs 实验推出(英语) | **2025-06-24** | [Google 印度博客](https://blog.google/intl/en-in/products/google-search-introducing-ai-mode-in-india/) |
| AI Mode 向印度所有人推出(英语,无需 Labs) | **2025-07-08** | [Google 印度博客](https://blog.google/intl/en-in/feed/ai-mode-in-google-search-rolling-out-in-india/) |
| AI Mode 新增印地语、印尼语、日语、韩语、巴西葡语 | **2025-09-08** | [Google 官方博客](https://blog.google/products-and-platforms/products/search/ai-mode-expands-more-languages/) |
| AI Mode 再增 7 种印度语言(孟加拉、卡纳达、马拉雅拉姆、马拉地、泰米尔、泰卢固、乌尔都)+ Search Live(英语、印地语);印度是美国以外首个获得 Search Live 的国家 | **2025-10-08** | [Google 印度博客](https://blog.google/intl/en-in/products/supercharging-search-for-india-new-languages-in-ai-mode-search-live-debuts/) |
| ChatGPT 印度 1 亿周活 | 2026-02-15 | Altman,NDTV 等转述 |

- 旧稿写「AI Mode 进印度 Search Labs=美国外首个市场」:官方印度博客写「We first introduced AI Mode as an experiment in the U.S.」后在印度以 Labs 推出,没有写「美国外首个」。该说法来自 Seroundtable 等媒体,本次未在 Google 原文读到,已改为不带「首个」。
- 旧稿「Search Live + AI Mode 扩 9 种印度语言」:官方写的是新增 7 种(加上已有的英语、印地语共 9 种)。

### 4.2 AI 摘要依赖度

- Bain 2025-02-19:约 80% 的消费者在至少 40% 的搜索里依赖「零点击」结果,自然网络流量因此下降约 15–25%(Bain 的估计)([Bain](https://www.bain.com/insights/goodbye-clicks-hello-ai-zero-click-search-redefines-marketing/))。调查样本是**美国消费者**,不是印度。用到印度要写明「美国样本,外推」。旧稿「60% 搜索零点击」同属 Bain 的美国样本。
- 「印度下一代搜索市场 2025 ~$1.54B」「60% 印度搜索者用 AI 开启每日查询」「Google 向约 100 家出版商为 AI 答案付费」未核,已删。

### 4.3 印度专属 GEO 纪律(本套件口径)

- AI 引用审计用双提示:罗马化 Hinglish 与天城体提示分别跑。Google 官方只说搜索会跨书写给结果;生成式回答是否同样跨书写,没有官方说明,所以分开测。
- FAQ 与 Question schema 用口语全句。
- ChatGPT 在印度有 1 亿周活,先测 ChatGPT 的印地语与 Hinglish 提示。

### 4.4 本土模型(观察项)

- Sarvam AI 自述是印度全栈主权 AI 平台,提供 22 种印度语言的语音转文字、文字转语音、翻译、对话代理([sarvam.ai](https://www.sarvam.ai/))。旧稿的具体型号(Sarvam-M 24B 等)已过时,不再列。它是观察项,不是必做项。

## 五、外包报价

- 旧稿列出了印度 SEO 外包的三层月费价带与白牌转包链价格,来源是代理商页面和论坛帖,价格会变且无统一口径,已删。
- 审计供应商的方法(本套件口径):要求每月交付物清单(页面、内容、链接来源),逐条核。外链类交付物对照 Google 垃圾政策(以排名为目的的买卖链接违规;付费链接标 `rel="sponsored"` 或 `nofollow`;[Spam policies](https://developers.google.com/search/docs/essentials/spam-policies),更新 2026-09-16)。

## 六、红旗

- **单一英语市场判断**:只做 en-IN 覆盖不了用印度语言上网的人群(IAMAI:98% 的用户用印度语言访问过互联网)。审计第一问:查询的三写分布测过吗?
- **聚合器租金依赖**:在聚合器付费买线索不等于渠道策略。
- **Discover 单点依赖**:Google 官方说 Discover 流量不如关键词搜索可预测。依赖度高时标红。
- **机翻镜像**:直接机器翻译的印地语镜像页不会因翻译而获得引用(本套件口径,无对照实验)。用原生 Hinglish 或印地语写作。
- **三写当三市场**:为同一意图建三份镜像页会造成重复内容和索引膨胀。
- **lakh/crore 缺失**:商业页用西式分组是未本地化信号。
- **只用英语提示测印度 GEO**:结果不能外推。

## 七、法规:DPDP

- **Digital Personal Data Protection Act, 2023**:2023-08-11 获总统批准([MeitY 页面](https://www.meity.gov.in/content/digital-personal-data-protection-act-2023)),按中央政府指定日期分阶段生效。
- **DPDP Rules, 2025**:2025-11 由 MeitY 公布(PIB 新闻稿 2025-11-14;媒体写公告日 11-13 或 11-14),PIB 称有 **18 个月分阶段合规时间表**,要求数据受托人发出独立、清晰、简明的同意通知,同意管理者须为印度公司([PIB](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2190014))。主要义务按 18 个月推算约在 2027-05,具体日期以规则条文为准(本套件推算)。
- 适用范围提示:处理印度境内个人数据的网站和应用要对照。这不是法律意见。

## 八、工具

| 功能 | 工具 | 注 |
|---|---|---|
| 印度语言 AI 栈 | Sarvam AI API | 观察项 |
| 音译归一 | IndicXlit(AI4Bharat) | 21 种语言 |
| 关键词 | Google Keyword Planner + 印地语 suggest | suggest 是免费 Hinglish 语料 |
| 快照诊断 | GSC 正则 | 见 3.2 |
| 聚合器占位 | JustDial、IndiaMART、Sulekha、TradeIndia | 实体与引用信号 |
| AI 测量 | GSC 生成式 AI 表现报告 + GA4 来源正则 + ChatGPT 印地语/Hinglish 双提示 | 报告 2026-06-03 公布,2026-08-31 起全球开放([帮助页](https://support.google.com/webmasters/answer/16984139))([Search Central 博客](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports)) |
| hreflang | `hi`、`hi-IN`、`en-IN`;`ta-IN`、`te-IN` | 泰米尔、泰卢固独立决策 |

## 上线检查清单

| # | 检查什么 | 怎么查 | 通过/失败判据 |
|---|---|---|---|
| 1 | hreflang 互指 | `python3 scripts/hreflang_cluster.py <hi-IN URL> <en-IN URL>`(有泰米尔/泰卢固版时一并传) | 互指完整;码合法 |
| 2 | lakh/crore 分组 | `python3 scripts/market_lint.py --market hi <html文件> --url <URL> --report` | lakh 分组项 AUTO-OK。脚本只识别 7 位及以上的西式分组(实测 `₹1,234,567` 报 WARN;6 位的 `₹123,456` 不报),6 位数人工看 |
| 3 | 天城体/罗马化检查 | 同上 | 天城体罗马化项无 AUTO-FAIL;语音助词项按提示处理 |
| 4 | 电话与数字 | `python3 scripts/local_format.py --market hi "<页面样本文本>"` | `+91` 前缀 ✓(该脚本不查 lakh 分组,分组靠第 2 项) |
| 5 | 头部元素 | `python3 scripts/head_check.py <URL> --market hi` | 无 ERROR |
| 6 | title/description | `python3 scripts/site_audit.py <URL> --market hi --json` | 本套件口径:title ≤60、description 77–155 字符;天城体词数是**逐字计**(见本地实测),不当词数用 |
| 7 | AI 检索爬虫放行 | `python3 scripts/robots_posture.py https://<域名>/robots.txt --signal visibility` | 搜索类与用户类 allowed |
| 8 | 三写缺口 | 在 GSC 查询里先过滤 `\p{Devanagari}`,再过滤罗马化助词正则(见 3.2 第 3 步),对照承接页语言 | 天城体查询落在英文页、或 Hinglish 查询零展示的页清单为空,或已排期处理 |
| 9 | Discover 依赖度 | GSC → 效果 → Discover 报告,对比 Search 点击 | Discover 占自然点击低于预警线(默认 50%,本套件口径) |
| 10 | 双提示 GEO 测试 | 罗马化 Hinglish 与天城体各 20 个提示,在 ChatGPT 与 AI Mode 跑 | 两组结果分开存档,被引域名分开记 |
| 11 | llms.txt(可选) | `python3 scripts/llmstxt.py check https://<域名>` | 看返回体是 markdown,不是 HTML 兜底页 |
| 12 | 聚合器占位 | 搜 20 个「城市+服务」词,记录聚合器与自有站排名 | 记录;月度对比 |

## 本地实测(2026-10-09)

> 脚本口径 2026-10-21 已改:twitter:* 与 OG 重复只记 INFO;缺 H1/描述为 WARN。下面的 ERROR 数是旧口径结果,复测会不同。

### 重核表(2026-10-09)

| 关键数字 | 当日结果 | 2026-10-21 复核 |
|---|---|---|
| Google ~96.7% | StatCounter 2026-09 96.63% | 现数据 96.69%(StatCounter 修订) |
| ChatGPT 1 亿周活 | 母语多源 | 英文多源(NDTV、TechCrunch)V |
| Bain 80%/60% | 样本为美国消费者,已修正 | 同 |
| IAMAI 98% Indic | 母语多源 + IAMAI–Kantar PDF | 2024 PDF V:870M 用户、98% |

### 真实站验证(amarujala.com / bhaskar.com)

- `site_audit --market hi`(旧口径):amarujala — title/desc 超限、跳级 h1→h3、262 链接;bhaskar — 同类,且 4 个 AI 检索爬虫(OAI-SearchBot、ChatGPT-User、Claude-SearchBot、PerplexityBot)被 robots.txt 全禁。`llmstxt check`:amarujala `/llms.txt` 200 在场;bhaskar 无。`head_check`(旧口径):两站均命中 twitter:* 全套、x-ua-compatible、fb:app_id 弃用 ERROR。
- 单次观察:Amar Ujala 放行 AI 爬虫并有 llms.txt;Dainik Bhaskar 四爬虫全禁。两站不能代表印度头部,「天城体 AI 引用池被头部收缩」的推论证据不足,已降为单次观察。
- 大站拦截:justdial.com 读超时、indiamart.com HTTP 429、hindi.news18.com 403。聚合器与大站对非浏览器 UA 激进拦截,先换浏览器 UA 重试再下结论。
- **工具盲区(2026-10-21 复核后更新)**:
  1. 旧结论「`site_audit.py` 对天城体词数计 0」**已过期**:当前 `wc()`(scripts/site_audit.py)对天城体**逐字(码点)计数**。实测 `wc("बेस्ट लैपटॉप कैसे खरीदें")` 返回 21,而人工词数是 4;`wc("best laptop kharidna hai")` 返回 4。所以天城体页的「词数」实为码点数,约为词数的 5 倍。薄内容判断(<200 词)对印地语页偏松,不当词数引用。
  2. `--market hi` 没有 hi 专属阈值分支(落通用阈值)。lakh/crore 的机检在 `market_lint.py`。
  3. 旧结论「title 解析把 head 内 CSS/JS 并入 title(amarujala 163,412 字符)」是旧数据,本次未复测。
  4. 微信/QQ itemprop 提示在非中文市场的噪声:本次未复测。
  5. 泰米尔、泰卢固字符的词数:`wc()` 对它们按「连续字母段」计,与印地语的逐字计不同,不能互比。

## 来源类型标注

- **官方**:Google 官方博客与 Search Central(AI Mode 时间线、multilingual search、Discover 文档)、PIB 与 MeitY(DPDP)、StatCounter、IAMAI–Kantar 报告、OpenAI CEO 公开讲话(经媒体转述)。
- **第三方研究**:Bain 零点击调查(美国样本)。
- **本套件口径**:Hinglish 三写归组、GSC 正则缺口法、助词词库、聚合器占位审计、预警线。

## 维护

- 复审周期 **90 天**,下一次 **2027-01-09**(以 `scripts/markets.json` 的 `markets.hi.review_cycle` 为准)。
- 触发即复审:StatCounter 印度月度份额;Google for India 年度发布(惯例 Q4);DPDP Rules 阶段生效日;IAMAI–Kantar 年报;Search Console 生成式 AI 报告的开放范围。
- 份额、周活类数字先于判断类断言过期。

## 建议(需要别处配合,本文件不改)

| 键路径 | 现值 | 应改值 | 来源 |
|---|---|---|---|
| `scripts/markets.json` → `markets.hi.special_checks[0]` | 「Hinglish 三写变体归组+GSC regex 快照缺口诊断」 | 保留;在 `references` 说明正则须用 RE2 的 `\p{Devanagari}` 而非 `ऀ` | Search Console 帮助、google-re2 实测 |
| `markets.hi.review_cycle.signals[3]` | 「IAMAI–Kantar 年报」 | 保留 | IAMAI 报告 |
| `markets.hi.review_cycle.signals[4]` | 「Discover 依赖度行业口径(State of Indian Digital Publishing/Praman)」 | 改「自家 GSC Discover 报告」(行业口径未核) | Google Discover 文档 |
| `markets.hi.review_cycle.note` | 「site_audit 天城文词数盲区已记录」 | 改「天城体词数已改为逐字计数(≈5×词数),不当词数用」 | scripts/site_audit.py wc() |
| `scripts/site_audit.py` → `wc()`(S2a 组) | 天城体逐码点计数 | 天城体改为按空格/词边界计词(或另列「字符数」),使 `soft-thin` 判断对印地语页有意义 | 实测 wc("बेस्ट लैपटॉप कैसे खरीदें")=21,词数=4 |
| `scripts/market_lint.py` → `hi_num`(约第 440–450 行) | 只对 7 位以上西式分组报 WARN | 加 6 位西式分组(如 `123,456`)的判定,或在输出里注明「6 位不判」 | 实测 `₹123,456` 无告警 |
| `markets.hi.notes` | 「hi-IN 与 en-IN 分开」 | 保留;补「hi-Latn 仅用于 HTML lang,Google hreflang 不用」 | Google 多语言文档 |
| `markets.hi.entity_sources` | `justdial.com, indiamart.com, sulekha.com` | 保留 | — |
