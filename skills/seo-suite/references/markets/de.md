# DACH-Markt(德语市场专项参考)

> 适用圈:德国(de-DE 主市场)+ 奥地利(de-AT)+ 瑞士德语区(de-CH)+ 列支敦士登/卢森堡/南蒂罗尔(顺带,不建独立站)。
> 数据锚点:2026-10-21 逐条核对一手来源(StatCounter、Google 官方博客、Sistrix、Seer、Pew、gesetze-im-internet.de、法院判决库、heise);二手研究标「第三方研究」。断言半衰期 6–12 个月。
> 写法约定见 [asd-ste100-web-writing](../content/asd-ste100-web-writing.md);标题与首段怎么对齐买家提问见 [question-alignment](../content/question-alignment.md)。

## 〇、关键数字速查

| 维度 | 值 | 口径/日期 |
|---|---|---|
| Google 份额(德国) | 全设备 87.84%;桌面 69.99%;移动 96.21% | [StatCounter DE](https://gs.statcounter.com/search-engine-market-share/all/germany),2026-09 月值,取数 2026-10-21 |
| 份额波动 | 全设备 12 月区间 80.05–90.18%;桌面 Bing 2026-05 至 09 为 16.56 / 16.31 / 14.48 / 12.81 / 19.44% | 同上;**月间波动大,不引用单月为常数** |
| AIO 上线 | **2025-03-25** 官方公告(德、奥、瑞士等) | [Google 官方博客](https://blog.google/feed/were-bringing-the-helpfulness-of-ai-overviews-to-more-countries-in-europe/) |
| AIO 覆盖 | 约 20% 德国关键词 | [Sistrix](https://www.sistrix.de/news/ai-overviews-in-deutschland-so-stark-sinken-die-klickraten-wirklich/),>1 亿关键词,2026-02 发布、2026-10-13 更新 |
| 位置 1 点击率 | 27% → 11%(约 −60%);有 AIO 的搜索中 33% 有自然点击,平均搜索 57% | 同上 |
| 点击损失 | 约 2.65 亿次自然点击**每月**;全关键词平均 −6.6% | 同上 |
| title/desc | 65(55–65 为佳)/150 字符;支柱 ≥2,000 词 | `scripts/markets.json`(本套件口径;Sistrix 出处的 55–65 未在其公开页读到;Google 无固定字符或字数要求) |
| 德语比英语长 | +25–35% | 本套件口径,无一手来源;用 `parity_check.py` 实测 |

## 一、格局

### 1.1 引擎份额

StatCounter 2026-09 月值(取数 2026-10-21):

| 地区 | 全设备 Google / Bing | 桌面 Google / Bing | 移动 Google |
|---|---|---|---|
| 德国 | 87.84% / 6.50% | 69.99% / 19.44% | 96.21% |
| 奥地利 | 80.88% / 10.93% | 69.19% / 20.64% | 93.09% |
| 瑞士 | 80.21% / 12.11% | 68.91% / 22.11% | 93.08% |

- 旧稿的「Google 87.8%(内部锚点)」就是 StatCounter 2026-09 全设备值 87.84%,不是独立口径。「SE Ranking 92.3%」本次未核,已删。
- 德国全设备 Google 2026-05 至 09 为 80.63 / 81.43 / 85.68 / 88.41 / 87.84%,变化大。引用时写月份。
- 桌面 Bing 15–20% 是行动级数字:桌面采购与 B2B 场景要配 Bing Webmaster 与 IndexNow。旧稿「Bing 索引喂 ChatGPT」无官方点名(OpenAI 只写「第三方搜索服务商」,[OpenAI](https://openai.com/index/introducing-chatgpt-search/)),已删。
- 移动 96.21% 一家独大。Yandex(全设备 1.56%)、DuckDuckGo、Yahoo 是噪声级(本套件口径)。

### 1.2 AIO:德国已在「冲击后」阶段

- Google 2025-03-25 官方公告把 AIO 带到奥地利(德、英)、德国(德、英)、瑞士(法、德、意、英)等九国。Sistrix 的文章写「2025-05 起」,与官方公告不同;时间点以官方公告为准。法国 2026-07-22 才上线(见 [fr.md](fr.md)),相差约 16 个月。
- Sistrix(>1 亿关键词):AIO 出现在约 20% 的德国关键词;长尾约 30%;78.6% 的 AIO 在自然结果之上。位置 1 点击率 27% → 11%;每月损失约 2.65 亿次自然点击;平均损失 6.6%;各行业从 1% 到 24%+;最大的绝对损失者是 Wikipedia(每月 3,160 万次点击),最大的比例损失者是专业健康门户(30%+)。
- 国际对照:
  - Pew(2025-07-22 发布,2025-03 的美国数据):有 AI 摘要时 8% 的访问含点击传统链接,无摘要时 15%([Pew](https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/))。
  - Seer Interactive:有 AIO 的查询自然 CTR 在 2025 年持续下降;**2025-12 约 1.3%,2026-02 回升到约 2.4%**([Seer 2026-04 更新](https://www.seerinteractive.com/insights/aio-impact-on-google-ctr-2026-update))。旧稿把这个回升归给 Ahrefs,应为 Seer。
  - Ahrefs(2026-02-04):位置 1 的点击在有 AIO 时低 58%([Ahrefs](https://ahrefs.com/blog/ai-overviews-reduce-clicks-update/))。
- 「全球信息类查询 AIO 覆盖 >50%」来自一家营销公司,无一手来源,已删。
- 做法(本套件口径):德国是「GEO 已跑一年半、引用面竞争成熟」的市场。交易词做经典 SEO,信息词做 AIO 引用占位。信息词自然流量按折价入预算。

### 1.3 Ecosia 与 Qwant 的自有索引

- Ecosia 全设备约 1.0%(2026-09 为 1.03%,移动 0.86%)。流量层面没有单独优化的价值。
- Ecosia 与 Qwant 的合资公司 EUSP 在 2025-08 启用自有索引 Staan;**德国索引 2026-07 才投入运行**,约 10 亿网页(Ecosia 总经理 Oels 对 heise 的说法),Ecosia 逐步提高自有索引的结果占比([heise,2026-07-30](https://www.heise.de/news/Ecosia-und-Qwant-starten-deutschen-Webindex-11383500.html))。旧稿「2025 年起共建德语索引」应为 2026-07 德国索引上线。
- 结论(本套件口径):优化 Ecosia 约等于优化 Google 与 Bing;自有索引成为默认结果源后再评估。

## 二、渠道

### 2.1 德国目录体系(本套件口径)

| 层 | 德国代表 | 作用 |
|---|---|---|
| ① 地图 | Google Business Profile、Bing Places、Apple Business Connect | NAP 一致性 |
| ② 黄页 | Gelbe Seiten、Das Örtliche、11880 | 本地词占位 |
| ③ 评价 | Trustpilot、ProvenExpert、eKomi | 信任信号 |
| ④ 商会登记 | Handwerkskammer、IHK、North Data | 实体验证 |
| ⑤ 行业垂类 | Jameda(医疗)、ImmoScout24(地产)、wlw.de(B2B 采购) | 垂类入口 |
| ⑥ B2B SaaS | OMR Reviews、Capterra DE | B2B 评测占位 |
| ⑦ 比价 | idealo、Check24 | 高购买意图词 |
| ⑧ 知识层 | Wikipedia(de)、Wikidata、LinkedIn | 实体图谱 |

- 手工业企业须登记入 Handwerksrolle(Handwerksordnung),所以商会目录是官方背书的实体来源(法律常识;本次未逐条核 HwO)。NAP 以登记数据为准,逐字符对齐。

### 2.2 付费链接:Google 政策与 UWG

- 旧稿的「月租 119€ 起」来自内部锚点,无公开来源,已删;「停租即摘链」是逻辑推论,保留为本套件口径:租来的链接按运营费用入账,不入资产。
- Google 立场:以排名为目的的买卖链接属链接垃圾;标 `rel="sponsored"` 或 `nofollow` 不违规([Spam policies](https://developers.google.com/search/docs/essentials/spam-policies),更新 2026-09-16;[qualify outbound links](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links),更新 2026-03-08)。
- 德国法律侧:UWG § 5a 第 4 款——商业目的不能直接从情境看出时,不标明商业目的属不正当竞争,且足以影响消费者或其他市场参与者的交易决定([gesetze-im-internet.de](https://www.gesetze-im-internet.de/uwg_2004/__5a.html))。有律所解读:LG München 2015-07-31(4 HK O 21172/14)认为,只写「Sponsored」不足以标明广告性质(来源:[律所文章](https://www.ra-plutte.de/schleichwerbung-sponsored-hinweis-reicht-nicht-aus/),判决原文本次未读)。
- 做法:付费或赞助内容同时做两件事:链接标 `rel="sponsored"`;页面上可见地标「Werbung」或「Anzeige」。审计顺序:先查法律暴露面,再查 Google 暴露面(本套件口径)。
- 旧稿「单函成本常见四位数欧元」无来源,已删。

### 2.3 数字 PR

- 德国常见路径是专家客座文(Gastbeitrag)与行业协会(Verband)数据。这是行业做法,无一手研究,标本套件口径。
- 新闻分发可用 Presseportal;不要在免费通稿站堆垃圾稿。

## 三、语言机制

### 3.1 Ansprache 与 Tonalität

- Ansprache(Sie/du)与 Tonalität(seriös/freundlich/locker)是两个字段,内容契约里分开声明。
- 默认:B2B 全场 Sie。de-DE 的 B2C du 化快,de-AT、de-CH 更保守(本套件口径)。一页内混用 Sie 与 du 是红旗。
- 问候语:Grüß Gott/Servus(南德与奥地利)、Grüezi(瑞士)、Guten Tag(通用)。

### 3.2 复合词

- 德语用户输入整词复合(Rechtsschutzversicherung)。关键词库按整词建,不按词素拆;拆写形只作 FAQ 长尾兼收。
- Google 对德语复合词的匹配强弱没有官方说明。本套件口径:title 和 H1 含完整目标复合词。

### 3.3 数字、日期、货币、正字法

| 项 | de-DE | de-AT | de-CH |
|---|---|---|---|
| 数字(CLDR) | 1.000,00 | 1 000,00(分组为不换行空格) | 1'000.00 |
| 货币 | 50 € | € 50 | CHF 50 |
| ß | 保留 | 保留 | 通常写 ss(Strasse) |
| 电话 | +49 | +43 | +41 |

- 数字与货币来自 Unicode CLDR 的 `de`、`de-AT`、`de-CH` 区域数据(cldr-json,取数 2026-10-21):`de` 分组点、小数逗号,货币 `#,##0.00 ¤`;`de-AT` 分组为 U+00A0、货币 `¤ #,##0.00`;`de-CH` 分组为撇号、小数点。旧稿把 de-AT 数字写成「1.000,00」,与 CLDR 不同;奥地利实际文本两种写法都有,页面内保持统一并与本站既有写法一致。
- 日期三国都用 DD.MM.YYYY(例 09.10.2026)。
- 瑞士标准德语不用 ß,统一写 ss(语言常识,本次未引用权威页)。
- de-CH 独立建语言-国家对:同域 /de/ 子目录加 CHF 定价;de-AT 不冒充 de-DE。hreflang 用 `de`、`de-DE`、`de-AT`、`de-CH`,大小写不敏感([Google 文档](https://developers.google.com/search/docs/specialty/international/localized-versions))。
- 词汇分流(关键词层按品类建表):Jänner/Januar、Paradeiser/Tomate、Karfiol/Blumenkohl、Fleischhauer/Metzger、Velo/Fahrrad、Natel/Handy。

### 3.4 长度与排版

- 德语比英语长 25–35% 无一手来源。title 65、description 150 是本套件口径;用 `parity_check.py` 对一页英德版实测本站的比值。
- 句长 15–20 词;营销词(revolutionär/führend/bahnbrechend)≤3/页。
- 正文用 ä/ö/ü/ß 规范拼法;主域避免 IDN。

## 四、AI-GEO

### 4.1 AIO 与 AI Mode

- 覆盖与损失见 1.2。AI Mode 德语:2025-10-07 官方博客宣布 35+ 新语言、40+ 新国家(含德语,见 [CNET 报道语言列表](https://www.cnet.com/tech/services-and-software/google-search-ai-mode-now-available-in-35-more-languages-and-40-more-countries/)),[官方博客](https://blog.google/products-and-platforms/products/search/ai-mode-expands-languages-locations/)。
- 证据阶梯(可见、被检索、被引用、被提及、被推荐、转化)分开记账(见 [geo-evidence](../content/geo-evidence.md))。
- Search Console 自 2026-06-03 提供「生成式 AI 表现报告」(2026-08-31 起全球开放;展示、页面、国家、设备、日期,无点击)([Search Central 博客](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports))。

### 4.2 引用源假设

- 本套件假设:德语 AI 引用偏向官方机构(BAFA、Fraunhofer、Destatis、行业协会)与德国 Tier-1 媒体。**未找到德语 AI 引用源的公开研究**,按假设处理,用自己的 50 条德语查询验证。
- 做法:数据引用与官方口径对齐(命名、单位、as-of 日期)。Wikipedia(de)与 Wikidata 实体保持一致。

### 4.3 测量

- GSC 做基准,GA4 或 Matomo 的建模值并列同意率。拒绝率高时,GA4 原始值偏低(本套件口径),不直接当真实流量汇报。

## 五、合规

### 5.1 Impressum:§ 5 DDG

- 德国 Digitale-Dienste-Gesetz(DDG)自 2024-05-14 起取代 Telemediengesetz(TMG),Impressum 义务现在是 **§ 5 DDG**(IHK Nord Westfalen:TMG 2024-05-14 失效)。
- § 5 DDG(原文):对「商业性质、通常有偿提供的数字服务」,服务提供者必须让以下信息易于识别、直接可达、持续可用——名称与住所地址(法人另有法律形式、代表人、已披露资本时的资本信息);能快速电子联系和直接沟通的信息(含电子邮件);须许可的活动的主管监管机构;商业登记簿与登记号;受监管职业的相关信息等([gesetze-im-internet.de](https://www.gesetze-im-internet.de/ddg/__5.html))。完整字段以条文为准。
- 缺失会被竞争者或消费者协会警告(Abmahnung)。同时削弱可信度信号(本套件口径)。

### 5.2 Cookie 与 TDDDG

- 德国《电信与数字服务数据保护法》**TDDDG** 由原 TTDSG 更名而来,2024-05-14 随 DDG 一起生效(来源:[transformation-gastgewerbe.nrw](https://transformation-gastgewerbe.nrw/aktuelles/ttdsg-heisst-jetzt-tdddg-was-aendert-sich));现行文本见 [gesetze-im-internet.de/ttdsg](https://www.gesetze-im-internet.de/ttdsg/)。终端设备上存取信息的同意义务在其 § 25。
- **OLG Köln,2024-01-19,6 U 80/23**(判决要旨):第一层不提供拒绝选项、第二层引导同意的 banner,不构成自愿且充分知情的同意;右上角「Akzeptieren und schließen X」按钮的设计违反透明和自愿原则,同意无效([MIR 2024, Dok. 025](https://medien-internet-und-recht.de/volltext.php?mir_dok_id=3354))。判决理由中提到同意与拒绝按钮要「gleichwertig」(dejure.org 摘录 Rn. 47)。旧稿写成「必须同等醒目且位于第一层」,与要旨大体一致,但「banner 第一层」的措辞以要旨为准。
- 其他判例:VG Hannover 2025 年有一份关于「全部拒绝」按钮的判决,不同律所解读相反(一说要求第一层有「Alles ablehnen」,另一说法院并未强制),因此旧稿「VG Hannover 跟进确认」不采用。旧稿的「OLG Frankfurt 2024-06-27」本次未核,已删。
- OLG Köln 2024-07-04,15 U 60/23:涉及搜索引擎运营者的案件,判决全文见 [justiz.nrw.de](https://www.justiz.nrw.de/nrwe/olgs/koeln/j2024/15_U_60_23_Urteil_20240704.html);具体结论本次未逐条核。
- 以上是适用范围提示,不是法律意见。

### 5.3 分析工具

- DACH 采购常要求隐私优先:Matomo(可自托管)、Plausible。GA4 要在 Consent Mode v2 与同意率披露下使用。这是行业做法(本套件口径)。

## 六、红旗

1. Ecosia 单独优化:约 1% 份额;优化 Google 加桌面 Bing 即可(见 1.3)。
2. 租链接记资产:租来的链接按运营费用入账(见 2.2)。
3. 泛欧盟方案:德、法、荷的 AIO 时间线不同(德 2025-03、法 2026-07-22),合规不同。
4. Sie/du 一刀切或混用:de-DE 的 B2C 模板复制到 de-CH 会出品牌语域事故。
5. 「德国人英语好,所以英文站能成交」:报价、AGB、客服、发票都要德语(本套件口径;未找到公开研究)。
6. 复合词拆分处理。
7. 合规当软建议:缺 Impressum、banner 无第一层拒绝、付费内容未标 Werbung,都是 Abmahnung 的靶子。
8. 份额口径单一引用:德国月间波动大,写月份。

## 七、工具

- **Sistrix**:可见度指数(Sichtbarkeitsindex)是德国提案常用货币;AIO-DE 研究出处。
- **Searchmetrics、XOVI**:德国可见度工具。
- **ABAKUS 论坛**:德国老牌 SEO 社区。
- **IT-Recht-Kanzlei**:Abmahnung、Werbung 标注、Cookie 判例的法律更新来源。
- **heise**:搜索基础设施新闻。
- **StatCounter**:份额;德国月间波动大,配 GSC 自查。

## 复审钩子

1. Sistrix AIO-DE 覆盖率是否破 40%;Seer 的 CTR 回升是否持续。
2. EUSP 德国索引是否成为 Ecosia 默认结果源。
3. Cookie banner 判例是否上行(BGH、欧盟层)。
4. de-AT、de-CH 的 Sie→du 演化。

## 上线检查清单

| # | 检查什么 | 怎么查 | 通过/失败判据 |
|---|---|---|---|
| 1 | hreflang 互指 | `python3 scripts/hreflang_cluster.py <de URL> <de-AT URL> <de-CH URL> <en URL>` | 互指完整;码合法 |
| 2 | 数字格式 | `python3 scripts/local_format.py --market de "<页面样本文本>"` | 德式 `1.234,56`,无英式 `1,234.56` ✗ |
| 3 | title/description 长度 | `python3 scripts/site_audit.py <URL> --market de --json` | 本套件口径:title ≤65(<55 提示浪费)、description 75–150 字符 |
| 4 | 头部元素 | `python3 scripts/head_check.py <URL> --market de` | 无 ERROR;charset 在前 1024 字节内 |
| 5 | 市场 lint | `python3 scripts/market_lint.py --market de <html文件> --url <URL> --report` | CRITICAL=0;Sie/du 混用 WARN=0;Werbung 标注项已处理;Impressum 项通过 |
| 6 | 中德长度比 | `python3 scripts/parity_check.py --source en.html --target de.html --market de` | 比值落在 markets.json 的带内;实测记入本站基线 |
| 7 | Impressum | 打开 `<域名>/impressum`;对照 § 5 DDG 字段清单 | 名称、地址、电子联系方式、登记号等齐全;页脚每页可达 |
| 8 | Cookie banner 第一层 | 无痕窗口打开页面,截图第一层 | 有与「同意」同等明显的「拒绝」入口(OLG Köln 6 U 80/23 要旨);无「X 即同意」设计 |
| 9 | 追踪器同意前触发 | 不点同意,看 Network 面板 | 非必要追踪器请求为 0 |
| 10 | AI 检索爬虫放行 | `python3 scripts/robots_posture.py https://<域名>/robots.txt --signal visibility` | 搜索类与用户类 allowed |
| 11 | llms.txt(可选) | `python3 scripts/llmstxt.py check https://<域名>` | 看返回体是 markdown 而非 HTML 兜底页 |
| 12 | 付费内容标注 | 列出所有付费链接与赞助稿 | 链接带 `rel="sponsored"`;页面有「Werbung」或「Anzeige」 |
| 13 | AIO 覆盖 | GSC 生成式 AI 表现报告(若已开放),国家=德国 | 记录展示数,季度对比 |

## 本地实测(2026-10-09)

> 脚本口径 2026-10-21 已改:twitter:* 与 OG 重复只记 INFO;缺 H1/描述为 WARN。下面的 ERROR/CRITICAL 数是旧口径结果,复测会不同。

### 真实站验证(spiegel.de / heise.de × site_audit + llmstxt check + head_check;zeit.de 403 换站)

- **zeit.de 对非浏览器 UA 整站 403**,拒审;换 heise.de 补位。德国头部站的 UA 过滤先于一切结论,先换浏览器 UA 重试。
- `site_audit --market de`:spiegel — robots.txt 禁 OAI-SearchBot、ChatGPT-User、Claude-SearchBot(3/4;PerplexityBot 放行)、首页无 H1、alt 缺失 575/649、title 32/65;heise — **title 67/65 超限 +2**、**charset 落在第 7,182 字节(>1024)**、66 块 JSON-LD、390 链接。
- `llmstxt check`:两站均无 llms.txt。
- `head_check`(旧口径):spiegel — 5 ERROR(twitter:* 全套)且 charset/viewport 在 title 后;heise — 5 ERROR(charset 超限、twitter:* 四条)。
- **德式数字检查(market_lint.py)**:`--market de --url` 直跑,德式数字识别 ✓;title 55–65 带双向触发(spiegel 32 报低于下限 INFO、heise 67 报超限 CRITICAL);Sie/du 混用 WARN(spiegel 50/2)触发。
- 单次观察:spiegel 3/4 封 AI 检索爬虫,lefigaro 同日 3/4,heise 未测 robots。三站不足以说「欧陆付费墙大报默认封锁」。

## 维护

- 复审周期 **90 天**,下一次 **2027-01-09**(以 `scripts/markets.json` 的 `markets.de.review_cycle` 为准)。
- 触发即复审:Sistrix 博客、StatCounter DE 月度份额(2026-09 桌面 Bing 单月跳至 19.44%)、heise/Ecosia 博客、IT-Recht-Kanzlei/ABAKUS、法院 Cookie banner 判例。
- 断言半衰期 6–12 个月;CTR 与份额类数字最先过期,法定义务(DDG § 5)最稳。

## 建议(需要别处配合,本文件不改)

| 键路径 | 现值 | 应改值 | 来源 |
|---|---|---|---|
| `scripts/markets.json` → `markets.de.notes` | 「Google 87.8%(主要市场最低)+Bing 6.5%」 | 加月份「StatCounter 2026-09」,并注「月间波动大(12 月区间 80.05–90.18%)」 | StatCounter DE |
| `markets.de.title_limit.note` | 「Sistrix 口径 55-65 字符」 | 改「本套件口径;Sistrix 公开页未读到该口径」 | Sistrix 页面 |
| `markets.de.pillar_note` | 「德语版比英语长 25-35%」 | 同上,改「本套件口径,未核」 | 无一手来源 |
| `markets.de.entity_sources[0]` | 「impressum(§5 DDG 法定页义务)」 | 保留 | gesetze-im-internet.de |
| `markets.de.special_checks[2]` | 「软文 Werbung 标注(Abmahnung…);OLG Köln 2024 拒绝键同等醒目」 | 保留;加「UWG § 5a(4);OLG Köln 6 U 80/23 要旨:第一层须有拒绝选项」 | gesetze-im-internet.de、MIR 2024 Dok. 025 |
| `markets.de.special_checks[3]` | 「租链(月租制)资产台账勿按永久入账」 | 保留(本套件口径),去掉「119€」类内部价带 | 无公开来源 |
| `markets.de.special_checks[5]` | 「AIO CTR 恢复信号(1.3%→2.4%)」 | 加「Seer,2025-12 至 2026-02」 | Seer 2026-04 更新 |
| `markets.de.special_checks[6]` | 「Ecosia 已混自有索引(非纯 Google)」 | 改「Ecosia/Qwant 德国自有索引 2026-07 上线,逐步提高占比」 | heise 2026-07-30 |
| `markets.de.special_checks[7]` | 「桌面 Bing 12.81% 泛口径低估」 | 改「桌面 Bing 2026-05 至 09 为 12.81–19.44%」 | StatCounter DE |
| `markets.de.special_checks[8]` | 「OLG Köln 判例:拒绝键同层同等醒目」 | 保留,措辞对齐判决要旨 | MIR 2024 Dok. 025 |
| `markets.de.review_cycle.signals[1]` | 「桌面 Bing 12.81% 口径漂移」 | 改「桌面 Bing 月间 12.81–19.44%」 | StatCounter DE |
| `markets.de.formats` | 只配 `de-DE` 风格数字 | 若需分国,补 de-AT(分组 U+00A0)、de-CH(撇号+小数点) | cldr-json |
