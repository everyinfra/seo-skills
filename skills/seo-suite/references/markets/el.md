# 希腊市场专项(el)

> **定位**:希腊(el-GR)市场的增量情报层。数值型规则(title/desc 60/155 字符、εσείς 正式称呼、希腊字母原形、διαφήμιση 标注)在 `scripts/markets.json` 的 `markets.el`;本文件只写:**StatCounter 份额口径、AI 使用率(Focus Bari 2026 调查 + Eurostat)、Skroutz/BestPrice 比价层、希腊语机制、广告披露红旗**。
> 数据锚点 2026-11-21:数字回到原始页面或转引它的可核对页面读过;读不到的删除或降级。标注:=官方公告、帮助页或统计机构原始表;=第三方研究或媒体(写机构、时间);=博客转述,未核到一手;=本套件约定。断言半衰期 6–12 个月。
> 未写进来的:StatCounter 希腊桌面/手机分设备搜索份额——本轮没找到可核对的希腊分设备表,只写全设备值;Temso 式希腊语 AI 引用语种测量——没找到已发表的希腊语版本,不编数字。

## 〇、关键数字速查

| 维度 | 值 | 来源与口径 |
|---|---|---|
| Google 份额(全设备) | **95.59%**(2026-10 单月) | StatCounter 希腊表,2026-11-21 取数 |
| Bing / Yahoo! / Yandex / DuckDuckGo | 3.03% / 0.52% / 0.25% / 0.39%(2026-10) | 同上 |
| AI 聊天份额(StatCounter) | ChatGPT 45.22%、Gemini 40.48%、Perplexity 7.87%、Claude 3.45%、Copilot 2.97%(2026-10) | 同上,AI 聊天机器人系列 |
| AI Overviews / AI Mode | AI Mode 希腊语 2025-10-08 上线;希腊在列 | Google 扩展公告,经第三方核对 |
| AI 工具使用率 | 90% 用过至少一种 AI 工具;ChatGPT 79%、Gemini 53% | Focus Bari 2026-09-29–10-05 调查,n=1,009 |
| 生成式 AI 使用率 | 44%(16–74 岁过去 3 个月),欧盟均值 32.7%;个人 41%、工作仅 16% | Eurostat 2025 参考年 |
| 企业 AI 采用 | 9%,欧盟均值约 20% | Eurostat Digitalisation in Europe 2026 |
| 上网率 | 8.64M 人,87.0%;社交媒体身份 7.40M(74.5%) | DataReportal Digital 2026 Greece(2025-10 数据) |
| 社交 | Facebook 72.3%、YouTube 69.5%、Instagram 59.8%、TikTok 35.3% | Datambar 2026-01 调查,n=600 |
| 网购 | 77.6% 经常/非常经常网购;一半人多数购买经比价站或集市 | GR.EC.A. + ELTRUN 希腊电商调查,经 Balkan eCommerce Summit 转引 |
| 比价层 | Skroutz 1,200 万+商品、约 9,000 商家、约 250 万活跃用户;2026-10 访问 2,538 万 | Skroutz(经转引);Semrush 2026-10 |
| title / desc | 60 / 155 字符(提示阈值) | 本套件口径,希腊字母按码点计 |

## 一、格局

### 1.1 引擎份额

- 数字以 StatCounter 希腊表为准(`gs.statcounter.com/search-engine-market-share/all/greece`),2026-10 单月:Google 95.59%、Bing 3.03%、Yahoo! 0.52%、Yandex 0.25%、DuckDuckGo 0.39%。StatCounter 量的是**搜索引荐流量**(到达站点的访问),不是搜索执行次数,别把它当「希腊人搜索次数份额」。数字读自 StatCounter CSV 的已发表转录表([searchengines.net 2026-11](https://www.searchengines.net/guides/search-engine-market-share-by-country/)、[venkatapagadala](https://venkatapagadala.com/search-engines-in-world/greece)),两处希腊值一致;StatCounter 称数据发布后 45 天内可修订。
- Google 在希腊比欧洲均值(2026-10 为 88.80%)高约 7 个点,Bing 只有 3.03%。Bing 的基本功(Bing Webmaster Tools 验证、IndexNow 提交)仍值得做,但优先级低于瑞典那种 Bing 占 8%+ 的市场。桌面/手机分设备份额本轮没找到希腊表,不编数字;移动优先仍是默认值(DataReportal:移动连接 1,370 万,相当于人口的 138%)。
- google.gr 2026-10 月访问 939 万,自然关键词头名是 `μεταφραση`(274 万量,Semrush google.gr 概览)——希腊人把 Google 当翻译器用是真实行为,翻译类、工具类内容有稳定需求。

### 1.2 AI Overviews 与 AI Mode

- 2025-10-07:Google 把 AI Mode 扩展到 40 多个国家和 35 种以上语言;**希腊语次日(2025-10-08)上线**,希腊在国家清单内([seoturtle](https://seoturtle.com/seo-insights/google-ai-mode-europe-what-cyprus-businesses-should-do)、[ghacks 2025-10-08](https://www.ghacks.net/2025/10/08/google-search-ai-mode-is-available-in-36-new-languages-and-45-regions/))。AI Overviews 2025-03 进入欧盟,Google 可用性页现列希腊与希腊语。
- 含义:希腊语问句的 AI 答案默认引用希腊语页,标题与首段要能被 AI 直接引用(答案+数字+as-of 日期),而不是只写给排名。

### 1.3 AI 使用率:消费者饱和,企业滞后

- Focus Bari 全国调查(2026-09-29–10-05,YouGov 面板,n=1,009 成年人):**90% 用过至少一种 AI 工具**,2024-11 是 50%,2025-07 是 60%;ChatGPT 79%、Gemini 53%、Copilot 20%、Claude 18%。ChatGPT 用户里 65% 每周至少用一次,87% 用免费版;Copilot 用户 52% 用于工作,ChatGPT 用户只有 33% 用于工作([Focus Bari](https://focusbari.gr/category/insights-trends/technology),经 [Windows Forum](https://windowsforum.com/news/greek-ai-survey-chatgpt-leads-in-reach-while-52-of-copilot-users-report-work-use.450540/) 转引)。
- Eurostat(2025 参考年):44% 的 16–74 岁希腊人在过去 3 个月用过生成式 AI 工具,欧盟均值 32.7%;**个人用 41%、工作用 16%**,25 个点的差距是欧盟最宽的一档;16–24 岁超八成。企业端反过来:希腊企业 AI 采用率 9%,欧盟均值约 20%([Eurostat](https://ec.europa.eu/eurostat),经 [Double Dot](https://wearedoubledot.com/greece-uses-ai-more-than-europe-does-greek-companies-use-it-less/) 转引)。
- StatCounter AI 聊天机器人系列(希腊,2026-10):ChatGPT 45.22%、Gemini 40.48%、Perplexity 7.87%、Claude 3.45%、Copilot 2.97%。聊天机器人份额与搜索引擎份额是两个不同口径,不能相加。
- ChatGPT 内广告 2026-08-24 起在希腊出现,属 31 国欧洲上线的一部分([Taxiarchis Vafeas 2026-09](https://www.taxiarchisvafeas.gr/en/insights/chatgpt-ads-greece-2026))。ChatGPT 答案内的广告位是独立的可见性层,别把它和自然引用混为一谈。

## 二、渠道

### 2.1 电商与比价:比价层就是发现层

- **Skroutz(skroutz.gr)**:希腊比价站兼集市,1,200 万+商品、约 9,000 商家、约 250 万活跃用户;Blackstone 2026-05 同意收购多数股权([Balkan eCommerce Summit](https://balkanecommerce.com/greece-ecommerce-trends-what-online-shoppers-really-want/))。Semrush:2026-10 月访问 2,538 万,希腊零售站第一;**BestPrice(bestprice.gr)** 567 万,是第二比价层。
- GR.EC.A. + ELTRUN 希腊电商调查:77.6% 的受访网购者经常或非常经常网购;**一半人多数购买经比价站或集市完成**;73.1% 通常用自提柜取货,高于送货上门的 52.5%;85% 多数购买来自希腊本土网店;最看重的是店名可信度(72.8%)。产品页要过比价层:价格、运费、库存三项在 Skroutz / BestPrice 上可见,别只优化自家站内。
- **Kotsovolos、Plaisio、Public.gr** 是本土零售大站;Trendyol、Temu、AliExpress 是跨境竞争层。TikTok Shop 2026-06 在希腊开店,目前主要还是发现入口,别按成熟销售渠道排计划。
- 支付:卡仍是主力;Apple Pay / Google Pay 是上升最快的支付方式,34.4% 的购物者通常使用(GR.EC.A. + ELTRUN 调查);货到付款仍常见(Shopify 希腊指南,25%)。结账页须明示货到付款与退货方式,别只写卡支付。

### 2.2 本地目录与评价

- **Vrisko(vrisko.gr)**:希腊本地目录,面向本土客户的近必备 listing;**in.gr**:希腊老牌门户与目录([Brainito 希腊目录清单](https://brainito.com/blog/top-greece-business-directories-citations-for-local-seo))。**xo.gr(Χρυσός Οδηγός)** 与 **11888.gr** 是电话目录时代留下的品牌目录(本套件口径,无数字主张)。
- 旅游业是希腊本地搜索的大头:GTP(greektravelpages)是旅游企业目录,酒店/民宿/租车类本地词先在这里对齐(本套件口径)。
- 做法:目录信息与官网 footer / Contact 页逐字一致;评价不买、不换,见第五节。

### 2.3 社交

- Datambar 2026-01-05–23 调查(n=600,18–64 岁,CAWI):Facebook 72.3%、YouTube 69.5%、Instagram 59.8%、TikTok 35.3%、X 20.5%。Facebook 在 45 岁以上人群的日活尤其高,Instagram 与 TikTok 在 18–24 岁最强。B2B 用 LinkedIn,年轻受众用 Instagram / TikTok,别按覆盖排名倒推投放。
- WhatsApp 是希腊最常用的聊天应用,家庭群与邻里群多语音消息(DataReportal 语境 + abcvv 希腊页)。客服与复购触达别只留邮箱。

## 三、语言机制(本套件口径,除非注明)

- **希腊字母是 24 个独立字母**,标题、品牌名、URL slug 保持希腊文原形,别剥离成拉丁字母。**Greeklish**(拉丁字母拼希腊语)在聊天与短信里常见,但正式场合评价偏负面(莱顿大学论文:Greeklish 在正式语境下被负面评价);专业内容一律用希腊文书写,Greeklish 只出现在用户原话引用里。
- **词尾 sigma**:词尾用 `ς`,词中用 `σ`(如 `όρος` / `ορος-`)。拼错词尾是机器翻译的明显信号,标题与品牌名逐字核对。
- **重音(tonos)**:单调正字法,一个词最多一个重音符号;但搜索者打字常省略重音。Semrush 的 google.gr 关键词表里 `μεταφραση`(无重音,274 万量)与拉丁转写 `τρανσλατε`(36.8 万量)都进了头部——关键词工具要**带重音与不带重音双查**,拉丁转写形也查,标题里用规范带重音形。
- **称呼一律 εσείς**:商务与正式场合用复数/敬称 εσείς,εσύ 只用于熟人与年轻受众;正文不用 εσύ。语气直接、平实。
- **数字与日期**:`1.234,56`(点千分位、逗号小数)、日期 `21 Νοεμβρίου 2026` 或 `21/11/2026`、电话 `+30`。价格写 `1.234 €`,别写 $ 式 `1,234.56`。标准增值税率 24%,欧盟最高(Shopify 希腊指南)。
- **标题/描述**:60 / 155 字符提示阈值(与 en 相同,希腊字母按码点计,本套件口径);希腊语词较长,关键词前置,别把核心词埋在标题后半段。
- **hreflang**:`el`、`el-GR`;`el-CY` 只用于 targeting 塞浦路斯希腊语区,别顺手加上。

## 四、AI 引用侦察

- 本轮没找到已发表的希腊语 AI 引用语种测量(Temso 式多语言引用样本未覆盖希腊语),不编数字。做法:用自己的 20–50 个核心商业问句抽样,每月记各引擎引用语种(希腊语页 vs 回落英文源),不要抄任何一家的数当定论。
- B2B 想进引用池,先上本地信源的报道与数据页,不是先堆外链(本套件口径,见 sv.md 第四节方法)。
- 测量注意:引用数是累计量,页面级不可拆;广告上线前后分段记基线(见 ko.md 第四节方法)。

## 五、红旗

- **广告必须一眼看出是广告**:希腊《消费者保护法》(Law 2251/1994,2024 年 Law 5111/2024 修订)与欧盟《不公平商业行为指令》要求商业传播一望即知是广告,广告主身份须标明;隐藏广告属误导性遗漏。欧盟网红大检查中 20 名希腊网红只有 25% 以清晰方式披露广告,50% 未清楚说明商业身份;发展部致函要求用 `#advertisement` / `#advertising` 标签(希腊语或英语均可)或平台自带的付费合作标签([Lexology 2024-11](https://www.lexblog.com/2024/11/13/greek-influencers-caught-on-regulators-radar/))。用 **διαφήμιση(广告)或 #advertisement,放在开头**,再加平台自己的付费合作标签;责任在品牌与网红双方,实物/旅行等非金钱报酬同样触发标注义务。
- **自律规则**:希腊广告自律委员会(SEE)执行《希腊广告传播实务守则》(HCACP),其网红营销附件要求社交媒体营销遵守广告的一般原则(合法、体面、诚实、真实)。
- **AI 生成内容须标 AI**:EU AI Act 2026-08-02 起,逼真的 AI 图片/视频须有可见 AI 标注,且须与广告标注分开、随内容一起传播。希腊语标注写 `Δημιουργήθηκε με AI`,放在 caption 首行或画面上。
- **Cookie 横幅**:非必要 cookie 须事先同意(GDPR + 希腊《电子通信法》下的数据保护局 ΑΠΔΠΧ 口径),同意率要进测量设计,别只记 GSC 数。
- **品类禁区**:烟草与电子烟在数字平台禁投;酒精广告有专项限制;金融、赌博另有专项规则,上线前查条文,别凭感觉。价格直降宣传须符合消费者保护法的降价标示规则。

## 六、工具

| 工具 | 用途 | 备注 |
|---|---|---|
| GSC + Bing Webmaster Tools | Google / Bing 口径 | Bing 份额 3.03%,仍值得单独验证站点 |
| StatCounter 希腊表 | 份额月度复核 | 全设备引荐流量,非搜索次数;45 天内可修订 |
| Focus Bari AI 调查 | AI 工具使用率 | 每年出,看 ChatGPT / Gemini 分项 |
| Eurostat 生成式 AI 使用 | 个人 vs 企业 AI 采用 | 2025 参考年,看 16–24 岁分项 |
| GR.EC.A. + ELTRUN 电商调查 | 网购习惯与支付 | 经 Balkan eCommerce Summit 转引 |
| Skroutz / BestPrice | 比价层可见性 | 价格、运费、库存三项先对齐 |
| Vrisko / xo.gr / in.gr | NAP 对齐与本地占位 | 目录信息与官网逐字一致 |
| `market_lint.py --market el` | 文案机检 | title ≤60 字符、desc ≤155 字符、εσείς 统一 |
| `site_audit.py URL --market el` | 单页审计 | 同上阈值 |

## 七、检查清单

| # | 检查什么 | 怎么查 | 通过判据 |
|---|---|---|---|
| 1 | 份额口径 | StatCounter 希腊表当月值 | 引用时写清月份、全设备、引荐流量口径 |
| 2 | 标题与描述宽度 | `python3 scripts/site_audit.py URL --market el` | title ≤60 字符、description ≤155 字符(本套件阈值) |
| 3 | 文案机检 | `python3 scripts/market_lint.py --market el page.html --report` | CRITICAL 0;εσείς 统一;带重音/不带重音双形在查 |
| 4 | 希腊字母原形 | 标题、品牌名、URL slug 目视 | 未剥离成拉丁字母;词尾 sigma 正确 |
| 5 | 广告标注 | 合作内容首行 | διαφήμιση 或 #advertisement 在开头;无隐藏广告 |
| 6 | AI 标注 | AI 生成写实图/视频 | 可见 `Δημιουργήθηκε με AI`,与广告标注分开 |
| 7 | 目录一致性 | Vrisko / xo.gr / 官网 footer | 名称、地址、电话逐字一致 |
| 8 | 比价层 | Skroutz / BestPrice 查品牌词 | 价格、运费、库存与官网一致 |
| 9 | AI 引用台账 | 核心问句逐月抽样(`citation_panel.py`) | 同一问句、同一环境逐月可比;分段记广告上线前后 |

## 维护

- 复审周期 **90 天**,下一次 **2027-02-19**;signals 清单与 `scripts/markets.json` 的 `markets.el.review_cycle` 保持一致,以 json 为准。
- 触发即复审:StatCounter 希腊月度份额(Google 95% 上下波动时重读)、Focus Bari AI 调查(每年)、Eurostat 生成式 AI 数据、AI Mode 希腊语覆盖变化、Skroutz 平台变化、发展部网红执法动态。
- 下次复审补做:本地实测轮(2 个希腊真实站 × `site_audit --market el` / `head_check` / `llmstxt check`),本轮未做。
