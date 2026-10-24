# Rynek Polski(pl 专项)

> 波兰语市场文件。数据锚点 2026-10-21;断言半衰期 6–12 个月。基线见 overview/multilingual-workflow.md 波兰段与 scripts/markets.json `pl` 键。
> 来源标注:【官方】=Google/监管机构/StatCounter 原始表/平台官方页;【第三方研究】=写明样本和日期;【从业者说法】=博客或论坛转述,未核到一手;【本套件口径】=套件设计约定。

## 〇、快速诊断入口(陌生项目 60 分钟路径)

1. `site:domena` 抽查波语页:变音字母完整(ą/ę/ł)?标题 sentence case?URL slug 是否 ASCII?(→ 三)
2. 品牌词 SERP:wykop / dobreprogramy 占位 + Ceneo(电商类)是否在列。
3. ChatGPT 关浏览测试 + 问「najlepszy [kategoria] w Polsce」,分引擎记录引用面。(→ 四)
4. 电商:Allegro 参数完整度、标题措辞、Smart! 状态。(→ 2.1)
5. Bing Webmaster 是否接入(桌面份额是手机外最大的一块)。
6. 基线记录:GSC 28 天 + Bing WMT 桌面。

## 一、格局:Google 主极 + Bing 桌面厚 + AI 功能已上线

### 1.1 引擎份额(StatCounter PL,2026-10-21 读 CSV)

| 口径 | Google | Bing | Yandex |
|---|---|---|---|
| 全设备 2026-09 | 89.56% | 7.38% | 1.44% |
| 全设备 13 个月(2025-09~2026-09) | 88.07%–90.01% | 5.74%–8.02% | 1.34%–1.88% |
| 桌面 2026-09 | **82.83%** | **13.96%** | 1.02% |
| 手机 2026-09 | 95.84% | 1.27% | 1.81% |
| 平板 2026-09 | 90.74% | 5.06% | 2.47% |

- 旧稿的桌面 Bing「13.94%」是舍入或修订前的数;现值 13.96%。全球桌面 Bing 同月为 14.65%,所以波兰桌面与全球桌面同级。
- 全设备 7.38% 与桌面 13.96% 的差来自手机几乎只有 Google。结论:Bing Webmaster + IndexNow 要做(GSC 可导入站点);移动策略仍以 Google 为主。
- Yandex 1.44% 只作监测项,不投入。

### 1.2 Google AI 功能与 ChatGPT

| 事项 | 日期与数据 | 来源 |
|---|---|---|
| AI Overviews(Przegląd od AI) | **2025-03-25** 上线波兰(波兰语和英语),与意、德、奥、西、葡、瑞、比、爱同批 | Google 博客 Mar 25, 2025【官方】 |
| AI Mode(Tryb AI) | 2025-10-07 起全球扩张,波兰与波兰语在现行名单中 | Google 博客 + 支持页【官方】 |
| ChatGPT 用户 | 2025-01 3.6M → 2025-10 **10.2M**,触达 34.42%(7–75 岁互联网用户) | Mediapanel PBI/Gemius,press.pl 2025-11-22【第三方研究】 |

- 旧稿写「AIO 2025-03-26」「AI Mode 2025-10-08」:前者以 Google 博客日期为准(03-25);后者是欧洲本地发布日,美国博客为 10-07。
- 旧稿的「Senuto:AIO 每 4 个查询出现 1 次」「Zero-click 54%→72%」「ChatGPT 画像 60% ≤34 岁、39.6% 住农村」「2026-06 AI 工具整体 16M」找不到原文,已删。AIO 出现率用自己的 GSC 与抽样测。
- 季节:Black Friday(11 月)< 圣诞(12 月)。Allegro 大促前后 SERP 波动加大。【从业者说法】

## 二、渠道

### 2.1 Allegro

- 规模:Gemius《E-commerce w Polsce 2026》写明 Temu 与 Allegro 月访客「几乎相同,约 1900 万」(差 10 万);Mediapanel 2026-02 Temu 1933 万、2026-03 1910 万,Temu 在这些月份高于 Allegro(wiadomoscihandlowe.pl、PAP)。旧稿的「Allegro ~19M、日均 5.6M、Temu 日活第二」改写为:两者月用户同级。
- **Trafność(默认排序)的六信号**是第三方 SEO 博客归纳(vinseo.pl、qsell.pl、apilo.com 等),没有 Allegro 公开的权重公式,标【从业者说法】。能用的做法:参数填满、标题写清卖什么(Allegro 社区帖子也写标题要清楚说明所售商品)、价格含运费要有竞争力。参数巡检每月一次。
- **Smart!** 是买家付费订阅服务:不限次数的免费配送和免费退货(Allegro 帮助页);卖家的 offer 满足条件会得 Smart! 标识。旧稿「Smart!(免费退货计划)」改为此说法。
- 旧稿的「标题 50–75 字符」「m-commerce 43%」「Allegro 贡献大盘 60–70% 流量」找不到原文,已删。

### 2.2 WhitePress 与付费稿

- WhitePress 是发布、链接和 digital PR 的平台,官网自述覆盖搜索、ChatGPT 与 AI 系统可见性(`whitepress.com/pl/`)。旧稿的「148,000+ 门户、28 国」「抽成约 50%(NETY)」以及整张价带表(300–800 / 1,200–2,500 / 3,500–5,000+ zł)找不到稳定一手来源,按任务要求已删价格。
- Google 垃圾内容政策原文(link spam):为排名买卖链接属链接垃圾;同一段写明广告与赞助链接加 `rel="nofollow"` 或 `rel="sponsored"` 后不违规;带优化锚文本的付费文章、在其它站分发的新闻稿被列为示例(`developers.google.com/search/docs/essentials/spam-policies#link-spam`,核对 2026-10-21)。
- **zielone linki**(不标 sponsored 的付费链)违反上述政策;合规线=`rel="sponsored"` + 披露(「artykuł sponsorowany」「we współpracy z」)。
- 采购前逐门户核流量来源、索引量和现有出站链接,按门户而不是按套餐买。报价向平台索取当期书面价。

### 2.3 Ceneo 与社区

- Ceneo(比价)是电商品牌词 SERP 的常客。wykop.pl、dobreprogramy.pl 在品牌词审计里查 UGC 占位。这两条是【从业者说法】,用 `site:` 搜索自查。

## 三、语言机制

### 3.1 变音字母

- 内容、标题、meta 保留 ą ć ę ł ń ó ś ź ż。关键词表不 ASCII 化。
- URL:Google URL 文档要求链接里的非 ASCII 字符做百分号编码(`https://example.com/gem%C3%BCse` 为推荐写法,`gemüse` 为不推荐)(`developers.google.com/search/docs/crawling-indexing/url-structure`,核对 2026-10-21)。所以 slug 转写为 ASCII 更好读:ą→a、ę→e、ó→o、ś→s、ć→c、ń→n、ź/ż→z、ł→l。转写表是【本套件口径】。
- **ł 无分解形**:`unicodedata.normalize("NFD","ł")` 仍是 `ł`,所以「NFD 去组合符」的脚本剥不掉它:`łódź` 变 `łodz`,不等于无变音输入的 `lodz`(本机 Python 实测)。CMS 的转写规则要显式配置 ł→l。
- IDN 域名(含变音)不新建,老站不动。

### 3.2 sierotki(孤字)

- 波兰排版里的 sierotka 指行尾孤立的短词,尤其单字母词 a、i、o、u、w、z。它是排版问题,不是拼写错误(Wikipedia「Sierotka (typografia)」;波兰排版标准 PN-P-55366:1983 见该条目引述)。
- 规则强度:PWN《Wielki słownik ortograficzny》第 54.8.1 条写明单字母连词和前置词「可以留在连续正文的行尾」,但书名和章节标题里应移到下一行(eKorekta24 引述);实践中通常都移。所以验收项写「建议」,不写「违规」。
- 做法:在短词与后词之间放不换行空格(`&nbsp;` 或 U+00A0)。静态站在构建层处理。
- title / meta 不涉及换行,主要是正文与标题。

### 3.3 语域与格式

- Pan/Pani(商务默认)与 ty(熟络)二选一,全站一致。标题用 sentence case。【本套件口径】
- 数字 `1 234,56`,货币 `1 234,56 zł`,日期 `09.10.2026`,电话 +48。【格式约定】
- 波兰语有 7 个格,关键词有多个屈折形。关键词研究要收变格形态;用波兰语库的工具(例如 Senuto)估量比用全球库准。这条是方法建议,Senuto 的数据范围未逐项核。

## 四、AI-GEO

### 4.1 OBTK 银行研究(On Board Think Kong,2026-06-23 发布)

- 方法:ChatGPT、Claude、Gemini、Perplexity 四个模型回答 225 个消费金融问题(房贷、现金贷、存款、信用卡、个人账户 5 类各 45 题)= 900 个回答;10 家最大银行(按资产);指标=品牌在回答中出现至少一次。
- 结果:3419 次点名中,PKO BP 624(18.3%)、mBank 616(18.0%)、ING 562(16.4%),三家合计 52.7%;Millennium 473(13.8%)、Alior 385(11.3%)。ChatGPT 更常提 mBank,Claude 更常提 ING,Perplexity 里 Pekao 靠前。模型平均点名 3–4 家,约 60% 描述为正面或值得关注,其余中性。
- Santander Bank Polska 2026 春改名 Erste Bank Polska:资产第三,但只被点名 101 次,因为模型仍按旧名记忆。OBTK 自己写明方法的局限:模型一部分靠联网搜索,用户可选不同模型,结果会随时间和提问者变化。
- 本套件做法:分引擎测品牌三态(不知道 / 知道但错 / 知道且对);品牌改名或合并后更新 Wikidata 与 Wikipedia,并重测。

### 4.2 其它

- 引用面优先级、「原创数据报告在小语种边际收益更高」等推论没有一手来源,已删。GEO 证据以 `content/geo-evidence.md` 为准。

## 五、信息源(线索,逐项存在性未核)

Planeta SEO(planeta-seo.pl,博客聚合)、Silesia SEM、Promptowy《AI w Polsce》、Gemius《E-commerce w Polsce》、Ceneo 电商报告、Delante / Senuto / DevaGroup 博客、obtk.pl。引用其中数字前先读原文。

## 六、红旗

1. Allegro 参数过时:每月巡检参数,从筛选结果消失就是丢曝光。【从业者说法】
2. zielone linki:见 2.2。
3. 剥变音字母:内容层任何一层 ASCII 化都是未本地化;URL 层反而要 ASCII(见 3.1,别搞反)。
4. 品牌改名 / 合并不更新实体:见 4.1 Erste 案例。
5. 用全球库估波兰关键词量:屈折形和本地习惯需要本地库校准。
6. 把 OBTK 银行结果当所有行业的结论:样本是一个行业、2026 年上半年。

| 误判 | 实际 |
|---|---|
| 「Bing 只值 7%,可忽略」 | 桌面 13.96%;WMT + IndexNow 几分钟接入 |
| 「AI 排名=Google 排名」 | OBTK:总榜 PKO 第一,ChatGPT 榜 mBank、Claude 榜 ING;分引擎测量 |
| 「guest post 越贵越好」 | 价格与链接价值没有已核的对应关系;按门户质量审 |
| 「URL 保留变音符更本地化」 | 内容层保留变音;URL 用 ASCII slug |

## 七、工具

| 工具 | 用途 | 备注 |
|---|---|---|
| StatCounter PL(CSV) | 引擎份额 | 见 1.1 |
| Bing Webmaster + IndexNow | 桌面份额的基建 | `scripts/indexnow.py` |
| GSC | 基线与 AI 来源 | 28 天口径 |
| Google Trends(geo=PL) | 季节与屈折变体 | — |
| Senuto | 波兰关键词库、可见性 | 范围未逐项核 |
| WhitePress | 门户发现、发布 | 价格向平台询价 |

## 八、Allegro Ads(只留已核的结构)

- Allegro 站内词表(购买意图,短词 + 属性)与 Google 词表(信息 / 研究意图)分开建、分开考核。【本套件口径】
- 站内搜索数据可作为 Google 品类词表的线索来源,用来选落地页主题。
- 旧稿的「出价 × offer 质量模型」「Top oferta 徽章逻辑」「冷启动 Ads:自然 7:3」「停投后自然位维持 2–6 周」「先修 offer 质量同预算多买 20–30% 流量」找不到官方原文,已删。预算比例按自己的广告数据定。

## 九、法规适用范围(只写范围,不构成法律意见)

| 事项 | 适用范围与日期 | 来源 |
|---|---|---|
| Cookie 与追踪 | 《Prawo komunikacji elektronicznej》(PKE)2024-11-10 生效,替代《Prawo telekomunikacyjne》;cookie 规则在 PKE 第 399 条;同意标准同时受 RODO(GDPR)约束 | Grant Thornton 2024-12-02;Infor 2024-11 帖【第三方,未读到 Dz.U. 条文原文】 |

## 十、语言处理事实(影响计数、去重、小写比较)

| 事实 | 可查方式 | 脚本现状(2026-10-21 实测) |
|---|---|---|
| 变音词不能被 ASCII 正则切碎 | `site_audit.py` `wc()` | 已按 Unicode 字母段计词,`przegląd` 计 1 词 |
| `ł` 无 NFD 分解 | `python3 -c "import unicodedata as u;print(u.normalize('NFD','ł')=='ł')"` 得 True | `keyword_variants.py`:`łódź` 与 `lodz` **不同组**(`Łódź` 与 `łódź` 同组) |
| 提问对齐分词 | `question_align.py` `tokens()` | `łódź`、`kurier` 正常识别(字符集含 ą ć ę ł ń ó ś ź ż) |
| STE 检查 | `ste_lint.py --lang pl` | 变音词不是「纯 ASCII 词」;示例 18 词里 9 个纯 ASCII,刚好踩在 50% 门槛上通过;变音密集的段落会被整块跳过 |
| sierotki | `market_lint.py --market pl` | HTML 输入已折行,孤字检查失活(MANUAL);用 10 节命令自查 |

## 十一、本地实测(实测记录)

> 脚本口径 2026-10-21 已改:twitter:* 与 OG 重复只记 INFO;缺 H1 / 缺描述为 WARN。旧版 2026-10-09 的「onet.pl 报 ERROR」不再适用。

- `site_audit.py https://www.wykop.pl/ --market pl --json`(2026-10-21):title 76 字符(超 60 WARN)、description 201 字符(超 155 WARN)、2 个 H1(WARN)、跳级 h2→h4(WARN)、340 链接(INFO)、canonical 指向外域(INFO)。`head_check.py --market pl`:error=0,2 条 INFO。
- 旧版三个工具缺陷已修:title 解析吞脚本、`wc()` 切碎变音词、`--market pl` 不读阈值。
- 仍存在:sierotki 检查在 HTML 输入上失活;sitemap 只探根 `/sitemap.xml`(INFO 级,不再算 WARN)。

## 十二、上线检查清单

| # | 检查什么 | 怎么查 | 通过 / 失败判据 |
|---|---|---|---|
| 1 | title / description | `python3 scripts/site_audit.py URL --market pl` | title ≤60、description 77–155 字符(本套件口径) |
| 2 | head 元素 | `python3 scripts/head_check.py URL --market pl` | error=0 |
| 3 | hreflang | `python3 scripts/hreflang_cluster.py URL_pl URL_en` | 自引用、互指、语言码合法 |
| 4 | 变音字母 | `curl -s URL \| grep -c "ą\|ę\|ł"` | 波兰语正文命中数 >0;全站无「剥变音」文本 |
| 5 | slug | 人工看 URL | ASCII 小写 + 连字符;`ł` 已转写为 `l` |
| 6 | sierotki | `curl -s URL \| python3 -c "import re,sys,html;t=re.sub(r'<script.*?</script>\|<style.*?</style>',' ',sys.stdin.read(),flags=re.S);t=html.unescape(re.sub(r'<[^>]+>',' ',t));print(len(re.findall(r'(?<!\w)[aiouwzAIOUWZ] (?=\w)',t)))"` | 命中数写进台账;正文建议为 0(`html.unescape` 把 `&nbsp;` 变成 U+00A0,不会被计入) |
| 7 | Bing 接入 | Bing Webmaster 后台已验证站点;`python3 scripts/indexnow.py --help` 看提交参数 | 站点已验证,sitemap 已提交 |
| 8 | 关键词变体 | `cat words.txt \| python3 scripts/keyword_variants.py --json` | `ł` 的无变音形(`lodz`)人工并组 |
| 9 | 提问对齐 | `python3 scripts/question_align.py --gsc q.csv --pages p.csv --min-impressions 20 --max-position 10` | 波兰语字符集已覆盖,可直接用 |
| 10 | 付费链接 | `curl -s URL \| grep -io 'rel="[^"]*sponsored[^"]*"'` | 付费链接带 sponsored 或 nofollow |
| 11 | AI 爬虫姿态 | `python3 scripts/robots_posture.py https://site/robots.txt` | 搜索类、用户类 bot 无非预期 blocked |
| 12 | 品牌三态 | 四个引擎各问 10 个品牌问题,记不知道 / 知道但错 / 知道且对 | 季度重测;改名后立即重测 |
| 13 | Cookie 同意 | 浏览器无痕窗口,同意前查 Application → Cookies | 同意前只有必要 cookie(PKE 第 399 条 + RODO) |
