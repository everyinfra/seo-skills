# 瑞典市场专项(sv)

> **定位**:瑞典(sv-SE)市场的增量情报层。数值型规则(title/desc 60/155 字符、du 统一、复合词双形、Reklam 标注)在 `scripts/markets.json` 的 `markets.sv`;本文件只写:**StatCounter 份额口径、AI 使用率(2026-01 调查)、本地目录与比价层、瑞典语机制、营销法红旗**。
> 数据锚点 2026-11-21:数字回到原始页面或转引它的可核对页面读过;读不到的删除或降级。标注:=官方公告、帮助页或统计机构原始表;=写机构、时间;=博客转述,未核到一手;=本套件约定。断言半衰期 6–12 个月。
> 未写进来的:StatCounter 瑞典桌面/手机分设备份额——本轮没找到可核对的瑞典分设备表,只写全设备值与设备构成;Yandex 在瑞典 1.29%,无本地意义,不展开。

## 〇、关键数字速查

| 维度 | 值 | 来源与口径 |
|---|---|---|
| Google 份额(全设备) | **85.86%**(2026-10 单月);2026-07 为 87.08% | StatCounter 瑞典表,2026-11-20 取数;7 月值见 Statista 转引 |
| Bing / Yahoo! / DuckDuckGo | 8.63% / 1.79% / 1.88%(2026-10) | 同上 |
| 设备构成 | 手机 56.28% / 桌面 43.72%(2026-10) | StatCounter 瑞典设备构成 |
| AI Overviews 上线 | **2025-05-20**(40+ 语言扩展,含瑞典语) | Google I/O 扩展;Dagens PS 报道瑞典语在内 |
| AI Mode 上线 | 2025-10-08 起(瑞典语,瑞典) | Google 推出记录 |
| AI 服务使用率 | 62%;AI Overviews 71%;任一形式 AI 81% | Svenskarna och internet 2026(2026-01 调查,Novus,n=3,776) |
| ChatGPT 使用率 | **52%**(2025 年 34%);Copilot 18%、Gemini 13%、Claude 2% | 同上 |
| 生成式 AI(16+) | 37%(过去 3 个月,2025 年);2026 年口径 47% | SCB ICT 调查 |
| 网购 | 84%(16+ 过去一年网购,2026 年口径) | SCB ICT 调查 |
| 比价习惯 | 66% 经常比价;59% 近 3 个月购物时用过 AI | PostNord 2026 秋季调查 |
| AIO 触发率(电商词) | 32% 的词出现 AIO,覆盖 19% 自然流量 | Castro AI 2026-11(77 家零售商,约 120 万词) |
| 上网率 | 97% 上网,93% 每天上网 | Svenskarna och internet 2025 |
| title / desc | 60 / 155 字符(提示阈值) |:Google 对长度无固定上限 |

## 一、格局

### 1.1 引擎份额

- 数字以 StatCounter 瑞典表为准(`gs.statcounter.com/search-engine-market-share/all/sweden`),2026-10 单月:Google 85.86%、Bing 8.63%、Yahoo! 1.79%、Yandex 1.29%、DuckDuckGo 1.88%。StatCounter 量的是**搜索引荐流量**(到达站点的访问),不是搜索执行次数,别把它当「瑞典人搜索次数份额」。
- Google 在瑞典比欧洲均值(2026-10 为 88.80%)低约 3 个点,Bing 的 8.63% 是欧洲偏高的水平。Bing 的基本功(Bing Webmaster Tools 验证、IndexNow 提交)值得做,别只做 Google。
- 桌面/手机分设备份额本轮没找到瑞典表,不编数字。只记设备构成:手机 56.28% / 桌面 43.72%(2026-10),移动优先是默认值。

### 1.2 AI Overviews 与 AI Mode

- 2025-05-20:Google 把 AI Overviews 扩展到 40 多种语言,Dagens PS 报道瑞典语在内;2025-10-08 起 AI Mode 以瑞典语在瑞典推出。
- Castro AI 2026-11 测量(77 家瑞典电商,约 120 万桌面词):**32% 的词出现 AIO,覆盖这些店 19% 的自然流量**;14 家店过半关键词见 AI 答案;药房、健康、食品受冲击最大(Holistic 61%、Meds 52%、Fazer 50%)。
- Topdog 以 Ahrefs Brand Radar 测 50 家最大瑞典电商:2026-05 至 11 引用数总体 +44%,但 8 月见顶后到 11 月回落 17%,45 家下滑(Stadium -48%、Hemtex -33%、Prisjakt -29%)。AIO 引用不是单调上涨的资产,按月复测,别按 5 月的峰值做计划。

### 1.3 AI 使用率:瑞典是 AI 渗透最快的市场之一

- Svenskarna och internet 2026(Internetstiftelsen,2026-01 调查,Novus 面板 n=3,776,按人口加权):**62% 用 AI 服务,71% 用或读过 AI Overviews,81% 以任一形式用过 AI**;五分之一每天用 AI。ChatGPT 52%,一年前 34%;Copilot 18%、Gemini 13%、Claude 2%。
- SCB ICT 2025:37% 的 16 岁以上人口过去 3 个月用过生成式 AI 工具(约 320 万人);2026 年口径该数 47%。两个年份口径不同(3 个月窗口 vs 年度口径),别直接连成趋势线。
- 含义:瑞典用户先问 AI 再点链接的比例已经很高,标题与首段要能被 AI 直接引用(答案+数字+as-of 日期),而不是只写给排名。

## 二、渠道

### 2.1 本地目录与评价

- **Eniro(eniro.se)**:北欧目录与本地搜索,Eniro Group 2025 年报:约 45,000 家付费中小企业客户、300 万+收录企业。NAP(名称/地址/电话)先在这里对齐,再对 Google 商家资料。
- **Hitta.se**:瑞典人/企业查找与地图,本地搜索的第二层占位;**Reco.se**:瑞典评价平台,服务类本地词常出现;**allabolag.se**:企业信息(注册、营收),B2B 实体核查用。
- 做法:目录信息与官网 footer / Contact 页逐字一致;评价不买、不换,见第五节。

### 2.2 电商与比价

- **Blocket**:瑞典访问量最大的购物站之一(分类广告:车、房、二手大件);**Tradera**:拍卖与二手市场,360 万会员、每周 600 万访问、常年 300 万+在售 listing(2024 年),1999 年成立,2021 年起重新为瑞典公司。
- **Prisjakt**:瑞典比价站,2002 年起,购物站前五;**PriceRunner**:另一家主流比价平台。PostNord 2026 秋季调查:66% 的瑞典人经常比价,59% 近 3 个月购物时用过 AI(18–29 岁 76%,65–79 岁 32%)。
- **Amazon.se**:2020 年上线,亚马逊首个北欧站;**CDON**、**Apotea**(瑞典最大线上药房)是另外两层。产品页要过比价层:价格、运费、库存三项在 Prisjakt / PriceRunner 上可见,别只优化自家站内。

### 2.3 社交

- Svenskarna och internet 2025:覆盖前五是 YouTube、Facebook、Instagram、Snapchat、LinkedIn;按**每天使用**排则是 Snapchat、YouTube、Instagram、TikTok、Facebook。B2B 用 LinkedIn,年轻受众用 Snapchat / TikTok,别按覆盖排名倒推投放。
- 只有 45% 的瑞典人定期在社交媒体发帖(2025 年),以 Instagram、Facebook、Snapchat 为主,女性多于男性。UGC 征集别按「人人发帖」假设。

## 三、语言机制(本套件口径)

- **复合词(sammansatta ord)**:瑞典语把词连写成一个长词(例 `billigaste bilförsäkring` 里的 `bilförsäkring` 是 bil + försäkring)。关键词工具要**连写与分写双查**,标题里优先连写形;分写形出现在正文与问答里,别只查一种。
- **å / ä / ö 是三个独立字母**,排在 z 之后;别把它们剥离成 a / o 写标题,本地用户会觉得是机器翻译。搜索有时会归一化,但展示层(标题、品牌名、URL slug)保持原形。
- **称呼一律 du**:瑞典 1960 年代 du-reformen 之后 du 是通用称呼,B2B 也不例外;Ni 显得古板生硬,正文不用。语气直接、平实,不用德式敬语层级。
- **数字与日期**:`1 234,56`(空格千分位、逗号小数)、日期 `21 november 2026` 或 `2026-11-21`、电话 `+46`。价格写 `1 234 kr`,别写 $ 式 `1,234.56`。
- **标题/描述**:60 / 155 字符提示阈值(与 en 相同,拉丁字母口径);瑞典语复合词长,关键词前置,别把核心词埋在标题后半段。
- **hreflang**:`sv`、`sv-SE`;`sv-FI` 只用于 targeting 芬兰瑞典语区,别顺手加上。

## 四、AI 引用侦察

- Temso《Lost in Translation》(2026-04,700 万+引用样本,7 个语言商业类 prompt):瑞典语问题里,**Google AI Overviews 引用瑞典语页 85.1%,ChatGPT 57.4%**。瑞典语页是 AIO 的默认引用源,ChatGPT 回落英文源的比例高得多。
- 另一家 MaxAEO 的说法相反(荷兰与瑞典「80%+ 的情况回落英文源」)——两家方法不同,别采信单一结论。做法:用自己的 20–50 个核心商业问句抽样,每月记各引擎引用语种,不要抄任何一家的数当定论。
- B2B 软件类非厂商引用里本地信源占头:Computer Sweden / IDG、breakit.se、di.se、nyteknik.se(MaxAEO 数据)。B2B 想进引用池,先上这几家的报道与数据页,不是先堆外链。
- 测量注意:引用数是累计量,页面级不可拆;广告上线前后分段记基线(见 ko.md 第四节方法)。

## 五、红旗

- **广告必须一眼看出是广告**:《营销法》(Marknadsföringslagen)要求所有营销在呈现方式上就让人清楚这是营销。法院判过:「i samarbete med」「#samarbete」「sponsored post」这类说法**不够**(Patent and Market Court of Appeal 2019-12-05,Kissie 案)。用 **Reklam 或 Annons,放在开头**,再加平台自己的付费合作标签。
- **Konsumentverket 2026:3 报告**:2026 年初仍有大量网红与广告主无清晰标注;2026-04 监管信发给约 40 名网红与广告主,不改可罚款。责任在品牌与网红双方,实物/旅行等非金钱报酬同样触发标注义务。
- **品类禁区**:烟草与电子烟在数字平台禁投;酒精广告不得 targeting 25 岁以下人群。金融、赌博另有专项规则,上线前查条文,别凭感觉。
- **AI 生成内容须标 AI**:EU AI Act 2026-08-02 起,逼真的 AI 图片/视频须有可见 AI 标注,且须与广告标注分开、随内容一起传播。瑞典语标注写 `AI-genererad`,放在 caption 首行或画面上。
- **Cookie 横幅**:非必要 cookie 须事先同意(GDPR + 瑞典《电子通信法》),按 PTS 指引做;同意率要进测量设计,别只记 GSC 数。

## 六、工具

| 工具 | 用途 | 备注 |
|---|---|---|
| GSC + Bing Webmaster Tools | Google / Bing 口径 | Bing 份额 8.63%,值得单独验证站点 |
| StatCounter 瑞典表 | 份额月度复核 | 全设备引荐流量,非搜索次数 |
| Svenskarna och internet(年报) | AI 与平台使用率 | Internetstiftelsen,每年 9 月发布 |
| SCB ICT 调查 | 生成式 AI 与网购使用率 | Statistics Sweden,每年 10 月 |
| Eniro / Hitta.se / Reco.se | NAP 对齐与本地占位 | 目录信息与官网逐字一致 |
| Prisjakt / PriceRunner | 比价层可见性 | 价格、运费、库存三项先对齐 |
| `market_lint.py --market sv` | 文案机检 | title ≤60 字符、desc ≤155 字符、du 统一 |
| `site_audit.py URL --market sv` | 单页审计 | 同上阈值 |

## 七、检查清单

| # | 检查什么 | 怎么查 | 通过判据 |
|---|---|---|---|
| 1 | 份额口径 | StatCounter 瑞典表当月值 | 引用时写清月份、全设备、引荐流量口径 |
| 2 | 标题与描述宽度 | `python3 scripts/site_audit.py URL --market sv` | title ≤60 字符、description ≤155 字符(本套件阈值) |
| 3 | 文案机检 | `python3 scripts/market_lint.py --market sv page.html --report` | CRITICAL 0;du 统一;复合词双形在查 |
| 4 | å / ä / ö | 标题、品牌名、URL slug 目视 | 未剥离变音符;排序按瑞典字母表 |
| 5 | 广告标注 | 合作内容首行 | Reklam 或 Annons 在开头;无「i samarbete med」单独标注 |
| 6 | AI 标注 | AI 生成写实图/视频 | 可见 `AI-genererad`,与广告标注分开 |
| 7 | 目录一致性 | Eniro / Hitta.se / 官网 footer | 名称、地址、电话逐字一致 |
| 8 | 比价层 | Prisjakt / PriceRunner 查品牌词 | 价格、运费、库存与官网一致 |
| 9 | AI 引用台账 | 核心问句逐月抽样(`citation_panel.py`) | 同一问句、同一环境逐月可比;分段记广告上线前后 |

## 维护

- 复审周期 **90 天**,下一次 **2027-02-19**;signals 清单与 `scripts/markets.json` 的 `markets.sv.review_cycle` 保持一致,以 json 为准。
- 触发即复审:StatCounter 瑞典月度份额(Google 86% 上下波动时重读)、Svenskarna och internet 年报(每年 9 月)、SCB ICT 调查(每年 10 月)、AI Overviews / AI Mode 瑞典覆盖变化、Konsumentverket 营销法执法动态、Castro AI / Topdog 电商 AIO 引用季度测量。
- 下次复审补做:本地实测轮(2 个瑞典真实站 × `site_audit --market sv` / `head_check` / `llmstxt check`),本轮未做。
