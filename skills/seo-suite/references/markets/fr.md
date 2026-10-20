# Marché Francophone(法语市场专项参考)

> 适用圈:法国(fr-FR 主市场)+ 魁北克(fr-CA)+ 比利时/瑞士(fr-BE/fr-CH)+ 非洲法语区(塞内加尔、科特迪瓦等)。
> 数据锚点:2026-10-21 逐条核对一手来源(StatCounter、Google 官方博客、Mistral 官方文档、OQLF、CNIL、Légifrance、Verian、Cision);二手研究标「第三方研究」。断言半衰期 6–12 个月。
> 写法约定见 [asd-ste100-web-writing](../content/asd-ste100-web-writing.md);标题与首段怎么对齐买家提问见 [question-alignment](../content/question-alignment.md)。

## 〇、关键数字速查

| 维度 | 值 | 口径/日期 |
|---|---|---|
| Google 份额(法国) | 全设备 88.14%(12 月区间 86.81–89.41);移动 96.63%;桌面 70.86% | [StatCounter FR](https://gs.statcounter.com/search-engine-market-share/all/france),2026-09 月值,取数 2026-10-21 |
| 桌面 Bing | 15.83%(2026-09);2026-06 至 08 为 10.98–11.79% | 同上;**2026-09 单月跳变约 9 个百分点,下月复核前不当趋势** |
| AIO + AI Mode 法国上线 | **2026-07-22** | Le Monde、Abondance 等媒体报道;未读到 Google 法国站的官方公告原文 |
| 法国 AIO 疑问类覆盖 | 51.7%–97.5%(按采样日期) | [Vincent Hégo 观察站](https://www.vincenthego.com/observatoire-seo/),作者自述是区间不是趋势 |
| AIO 对新闻站流量 | 33–38%(APIG 引 Arcom,针对**已上线的欧洲市场**) | 见 1.2 |
| title/desc | 60/155 字符;句长 15–20 词;支柱 ≥1,800 词 | `scripts/markets.json`(本套件口径;Google 无固定字符或字数要求) |
| Bill 96 罚款 | 3,000–30,000 加元(违反 OQLF 命令时,累犯加倍) | 见五 |

## 一、格局

### 1.1 引擎份额

StatCounter 2026-09 月值(取数 2026-10-21):

| 地区 | 全设备 Google / Bing | 桌面 Google / Bing | 移动 Google | 备注 |
|---|---|---|---|---|
| 法国 | 88.14% / 5.49% | 70.86% / 15.83% | 96.63% | 全设备 Yahoo 2.75%、Ecosia 1.34% |
| 比利时 | 87.86% / 8.62% | 76.06% / 18.81% | 97.35% | |
| 瑞士 | 80.21% / 12.11% | 68.91% / 22.11% | 93.08% | 多语种国家,法语区无单独数据 |
| 加拿大 | 85.28% / 10.08% | 74.82% / 18.87% | 96.16% | 全国口径,无魁北克单独数据 |
| 塞内加尔 | 95.68% / 3.68% | 86.07% / 12.57% | 99.14% | 桌面 Bing 12 月区间 6.68–20.76%,样本小、波动大 |

- 旧稿「Google ~96%」是移动端数字,不是全设备数字。
- 桌面 Bing 的份额高于「<5%」的印象。桌面客群大的业务要配 Bing Places 与 Bing Webmaster。
- Qwant 在法国桌面 2026-09 为 1.63%、全设备 0.86%。旧稿「Qwant 2025-08 起转 Bing 索引」与来源相反:Qwant 与 Ecosia 的合资公司 EUSP 在 2025-08 推出自有索引 Staan,**减少**对 Bing 的依赖([Qwant 2024-11 公告](https://betterweb.qwant.com/2024/11/08/ecosia-et-qwant-sassocient-pour-developper-un-index-de-recherche-europeen/)、[Objetconnecté 2026-09](https://www.objetconnecte.com/qwant-que-faut-il-savoir-de-ce-moteur-de-recherche/))。

### 1.2 AI Overviews:法国晚一年多

- **2026-07-22** 法国上线 AIO 与 AI Mode(Le Monde、[Abondance](https://www.abondance.com/20260722-2640402-lancement-officielle-ai-overviews-france.html)、BDM)。
- 邻国更早:Google 2025-03-25 官方公告把 AIO 带到德国、奥地利、瑞士(法、德、意语)、比利时(当时仅英语)、西班牙、意大利、波兰、葡萄牙、爱尔兰([Google 官方博客](https://blog.google/feed/were-bringing-the-helpfulness-of-ai-overviews-to-more-countries-in-europe/))。德国到法国相隔约 16 个月。瑞士法语用户自 2025-03 起就有 AIO。
- 延迟原因:邻接权纠纷。法国竞争管理局罚过 Google 两次:2021 年 5 亿欧元,**2024 年 2.5 亿欧元**(Abondance 与 Toute l'Europe)。旧稿写「上一年罚 2.5 亿」,应为 2024 年。
- 新闻出版商联盟 APIG(近 300 家日报)2026-08-11 向竞争管理局**提出申诉**(saisine),不是民事诉讼([Toute l'Europe](https://www.touteleurope.eu/societe/google-plus-de-300-medias-saisissent-l-autorite-de-la-concurrence-apres-l-arrivee-d-ia-overview-en-france/))。
- **33–38%** 是 APIG 引用 Arcom 的评估:在 AIO 已上线的欧洲市场,媒体流量下降 33–38%。它不是法国上线后的实测。
- 法国上线后的早期数据(第三方、弱):Alternatives Économiques 引 ACPM,通用新闻站 8 月访问量 −15%;Media Leader 引匿名来源称一个月 −17%([Media Leader](https://fr.themedialeader.com/google-overviews-une-baisse-de-17-de-trafic-en-un-mois-selon-lacpm/))。8 月本身是新闻淡季。旧稿「新闻站 2 个月 −22%」找不到出处,已删。
- Vincent Hégo 观察站(952 个法语查询,2026-05 至 09):含 AIO 的页面占全样本 32.4%;「职业+城市」类 95.3% 出本地地图、0.3% 出 AIO;SEO 与营销类查询 80.1% 出 AIO;疑问类 51.7%–97.5%,作者写明「差异可能来自日期、记录格式或刷新后的查询,按区间而非趋势发布」。旧稿「51.7%→97.5% 爬升」把区间读成了趋势。
- 做法(本套件口径):信息类内容按「有 AIO」设计,答案前置,首段自足。本地服务类先做 Google Business Profile。

### 1.3 本土助手 Vibe(原 Le Chat)与 AFP

- Mistral 官方帮助中心确认 [Le Chat 已更名为 Vibe](https://help.mistral.ai/en/articles/682992-le-chat-is-now-vibe)(页面日期 2026-08-12;the-decoder 报道 2026-05-28)。定位是通用工作代理。
- 法国「主权、隐私」叙事对 Vibe 有利(本套件口径)。欧洲议会 2026-06-04 起默认搜索引擎换成 Qwant(Objetconnecté 报道);未见其换用 Vibe 的来源,旧稿相关句已删。
- AFP 系媒体作为引用通道:没有一手研究支持,仅作假设(本套件口径)。检验方法见 4.2。

## 二、渠道

### 2.1 法国目录体系(本套件口径)

| 层 | 代表平台 | 作用 |
|---|---|---|
| ① 地图 | Google Business Profile、Bing Places、Apple Business Connect | NAP 一致性 |
| ② 黄页 | PagesJaunes、118712 | 本地词占位 |
| ③ 评价 | Trustpilot、Avis Vérifiés | 信任信号 |
| ④ 企业登记 | societe.com、Pappers、CCI | 实体验证 |
| ⑤ 行业垂类 | Doctolib(医疗)、Malt(自由职业) | 垂类入口 |
| ⑥ SaaS 目录 | Appvizer、Capterra FR | B2B 评测占位 |
| ⑦ 知识层 | LinkedIn、Crunchbase、Wikidata | 实体图谱 |

(旧稿「Bing 索引喂 ChatGPT」「Wikidata/GitHub 直接喂 AI 语料」没有一手来源,已删。OpenAI 官方只写 ChatGPT search 使用「第三方搜索服务商与合作方提供的内容」,没有点名 Bing:[OpenAI](https://openai.com/index/introducing-chatgpt-search/)。)

### 2.2 实体简介重复法

- 本套件口径:40–60 词的规范实体简介,在各平台逐字重复,NAP 逐字符一致。依据是实体一致性,不是官方规则。
- 简介写成可独立成句的事实陈述:谁、在哪、做什么、有数据支持的事实。少用营销词。
- 检验:季度 diff 各平台简介(见检查清单)。

### 2.3 数字 PR

- Cision《State of the Media 2026》(2026-06-02 发布,2,000 名记者、19 国与地区含法国)原文:79% 的记者**使用 AI**(去年 53%);公关人员仍是记者的第一信息来源,但记者会拉黑发送无关或过度推销内容的人([Cision 新闻稿](https://www.cision.fr/nous-connaitre/communiques-de-presse/rapport-state-of-the-media-2026-comment-les-journalistes-a-travers-le-monde-s-adaptent-ils-aux-mutations-de-l-information/))。旧稿「79% 记者依赖外部专家」「66% 以通稿为首要信源」与原文不符,已删。
- Verian 信任度调查(2026-01-15):65% 信电视新闻、63% 信地区报、58% 信全国报([Verian](https://www.veriangroup.com/fr/news-and-insights/barom%C3%A8tre-de-la-confiance-des-fran%C3%A7ais-dans-les-m%C3%A9dias))。可作「地区媒体值得投」的依据。
- Matris、SMART PR、Onclusive 是法语记者库,未逐一核功能。「Angie 2026 榜」无来源,已删。
- 买链:Google 垃圾政策把以排名为目的的买卖链接列为链接垃圾;付费位置标 `rel="sponsored"` 或 `nofollow` 不违规([Spam policies](https://developers.google.com/search/docs/essentials/spam-policies),更新 2026-09-16)。旧稿的「€3–10/条」价带无一手来源,已删。「降值优先于惩罚」是本地说法,无官方依据;审计时按 Google 政策判。
- 圈内信息源:Abondance(1998 年起)、WebRankInfo 论坛。

## 三、语言机制

### 3.1 排版

- 法语标点 `: ; ! ?` 前和 `»` 前用窄不换行空格 U+202F(或 U+00A0),`«` 后同理。这是法语排版惯例(Imprimerie nationale《Lexique》),本次未读到该手册原文。Unicode CLDR 的法语数字分组符号本身就是 U+202F(`fr` 区域,取数 2026-10-21)。
- 「普通空格会被识别为机器翻译站」没有来源,已删。
- 数字 `1 234,56`(分组符 U+202F,小数逗号);货币后置 `50 €`;日期 `JJ/MM/AAAA`。CLDR:`fr-CA` 分组符是 U+00A0,`fr-CH` 分组符是撇号 `'`(cldr-json,取数 2026-10-21)。
- 撇号用 U+2019;大写保留变音符;œ 连字在关键词归组时按 oe/cœur 双写兼收(本套件口径)。
- 法语比英语长约 15–25%:无来源,按本套件口径留余量。

### 3.2 敬称

- 默认 vous;tu 只用于亲密或生活方式品牌;一页内不混用(本套件口径)。
- 带变音符的关键词,归组研究用无重音形,展示用规范拼写。

### 3.3 魁北克与法国词汇

| 概念 | fr-CA(魁北克) | fr-FR |
|---|---|---|
| 邮件 | courriel | mail(口语)/ courriel(行政) |
| 播客 | balado | podcast |
| 购物 | magasinage | shopping |
| 周末 | fin de semaine | week-end |
| 垃圾邮件 | pourriel | spam |
| 聊天 | clavardage | chat / tchat |

- 词表来自魁北克常用法和 OQLF 术语库(Grand dictionnaire terminologique),本次未逐词在 OQLF 术语库核对,标「未核」。两地关键词映射分开建,量级用本地词工具分别验证。

### 3.4 比利时与瑞士

- fr-BE、fr-CH 用 septante(70)、nonante(90);瑞士部分州用 huitante(80)。这是语言常识(本套件口径)。价格类长尾词按区拆分。
- hreflang 用 `fr-FR`、`fr-CA`、`fr-BE`、`fr-CH`。Google 只认 ISO 639-1 语言码加可选 ISO 3166-1 Alpha-2 区域码,大小写不敏感([Google 文档](https://developers.google.com/search/docs/specialty/international/localized-versions))。**旧稿的 `fr-AF` 是错的**:AF 是阿富汗的国家码,非洲不是合法区域码。非洲法语区用具体国家码,如 `fr-SN`、`fr-CI`。

## 四、AI-GEO

### 4.1 Vibe 三个爬虫(Mistral 官方,[docs.mistral.ai/robots](https://docs.mistral.ai/robots),读取 2026-10-21)

| 爬虫 | 官方说明 | robots 策略(本套件口径) |
|---|---|---|
| `MistralAI-User/1.0` | 用户在 Vibe 里提问时取页,回答里附来源链接;不自动抓网,不用于训练 | 允许 |
| `MistralAI-Index/1.0` | 自动抓取,仅用于建 Mistral 搜索索引;内容不用于生成式 AI 训练 | 建议允许 |
| `MistralAI-Training/1.0` | 为训练数据集抓取;不用于搜索索引或实时回答 | 单独决策 |

- IP 清单公开:`https://mistral.ai/mistralai-user-ips.json` 与 `https://mistral.ai/mistralai-index-ips.json`(2026-10-21 实测 HTTP 200、application/json)。日志层可据此验证真伪。
- 一刀切封 `MistralAI-*` 会同时失去 Vibe 的引用和索引。三个令牌分开写。
- 旧稿「22.9% 的 Vibe 推荐不与美系助手重叠(内部研究)」没有可公开的来源,已删。Vibe 的 SERP 单独实测,不用 ChatGPT 结果替代。

### 4.2 AIO 法语侧与测量

- 证据阶梯(可见、被检索、被引用、被提及、被推荐、转化)分开记账(见 [geo-evidence](../content/geo-evidence.md))。
- 测量协议(本套件口径):50 条法语查询 × 预期标注 × 14 天重测;fr-FR 与 fr-CA 样本分开跑。
- Search Console 在 2026-06-03 上线「生成式 AI 表现报告」(2026-08-31 起全球开放;给展示、页面、国家、设备、日期,无点击)([Search Central 博客](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports))。法国 AIO 自 07-22 起,看该报告里的法国展示。
- 信源优先级(假设,待用自己的 50 条查询验证):官方机构(insee.fr、service-public.fr)、AFP 系与 Tier-1 法媒、国际泛源。

## 五、魁北克法律:Bill 96 与相关

适用范围以 OQLF 官方材料为准(OQLF《Charte de la langue française : mythes et réalité》;[OQLF 企业页](https://www.oqlf.gouv.qc.ca/francisation/entreprises/));以下为 Norton Rose Fulbright 对 Charte 条文的汇总,不是法律意见。

- **网站**:在魁北克有机构的企业,网站和社交媒体必须提供法语,可以同时有别的语言。**没有魁北克机构但向魁北克消费者销售**的企业,面向魁北克消费者的商业内容必须有法语版,内容不得少于、条件不得劣于其他语言版。OQLF 说明:一旦在魁北克提供产品或服务,相关信息就必须有法语版。
- **商业广告**:法语须「nettement prédominante」(显著占优)(Charte 第 58 条;2025-06-01 起新规取代旧的「显著占优」条例)。旧稿的「同等醒目」对应的是发票和合同类文件(第 57 条、第 89/91 条:法语至少同样明显、条件至少同样有利),广告类要求更高,两者别混。
- **企业法语化**:25 名及以上员工的企业须向 OQLF 登记并启动法语化流程,**自 2025-06-01 起**生效(此前门槛是 50 人)([OQLF 公告 2024-05-06](https://www.oqlf.gouv.qc.ca/office/communiques/2024/20240506_entreprises_25_49_personnes.aspx))。旧稿「2025-06-01 为电商合规大限」不准确:该日期针对员工人数门槛。
- **罚款**:OQLF 本身不罚款,也无权开罚单;由刑事与刑罚检察长决定是否起诉,法院判罚(OQLF《mythes et réalité》)。不遵守 OQLF 命令构成刑事违法,罚款 3,000–30,000 加元,累犯加倍或三倍,持续违法每日算一次(Charte 第 205 条,[Norton Rose Fulbright](https://www.nortonrosefulbright.com/fr-ca/centre-du-savoir/publications/38625c3d/legislation-en-matiere-de-langue))。
- 旧稿「公民私人诉权」未在上述来源中读到,标「未核」,已删。
- 商标例外、与 Law 25(魁北克隐私法)混淆的提醒保留:语言法与隐私法是两套义务,审计分开列。
- 合规闸门先于内容:查 OQLF 注册状态、网站法语版、合同与发票与客服的法语能力。

## 六、法国法律与隐私

- **Loi Toubon**(Loi n° 94-665 du 4 août 1994)第 2 条:商品、产品或服务的名称、要约、介绍、使用说明、保修范围与条件,以及发票和收据,必须使用法语;该规定同样适用于所有书面、口头或视听广告;外国原名的典型产品和特色商品名称例外;商标法不妨碍对随商标注册的说明与信息使用法语([Légifrance 第 2 条](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000006421210),版本自 1995-03-05 起有效)。面向法国消费者的英文页要有等效法语内容。
- **CNIL Cookie 规则**:在写入或读取终端上的追踪器之前,须告知并取得同意,严格必要的追踪器例外([CNIL 说明](https://www.cnil.fr/fr/cookies-et-autres-traceurs/regles/cookies/lignes-directrices-modificatives-et-recommandation);指南 2020-09-29)。拒绝要和接受一样容易(CNIL 2021-05 对约 20 家机构发出限期整改)。
- **受众测量可豁免同意**,条件(CNIL,2025-07-04 页面):目的严格限于本站受众测量;只产出匿名统计;不与其他处理交叉;不跨站跟踪。建议追踪器寿命不超过 13 个月,数据保留不超过 25 个月。CNIL 不认证具体产品,只提供厂商自评工具([CNIL](https://www.cnil.fr/fr/cookies-solutions-pour-les-outils-de-mesure-daudience))。
- **Google Analytics**:CNIL 2022-02-10 对一家网站运营者发出整改通知,认定其经 GA 向美国传输数据违反 GDPR 第 44 条及以下;2023 年欧盟-美国数据隐私框架(DPF)的充分性决定后,美国传输可在框架内进行(CNIL 页面「Transferts de données vers les États-Unis」)。结论:GA 不是「被禁」,合规取决于配置与传输依据。
- 测量:GSC(不依赖同意)做基准;GA4 或 Piano 的建模值并列 consent rate。Piano 在 2021-03 收购 AT Internet(TechCrunch 2021-03-02);「数据主权」是法国大企业采购用语(本套件口径)。

## 七、红旗

1. 泛欧盟方案通吃:法国 AIO 比德国晚约 16 个月;魁北克法规只适用魁北克;各国合规不同。
2. Qwant 迷思:Qwant 全设备 0.86%,价值主要在主权叙事。它与 Ecosia 在做自有索引 Staan,不再等于 Bing 的出口。
3. 份额口径单一引用:移动 96.63% 与全设备 88.14% 不是同一个数,按设备拆分并标月份。
4. 「GA 在法国被禁」是误解(见六)。
5. 「法语市场 = 法国」:魁北克、比利时、瑞士、非洲法语区各自有语言和法规差异。
6. 英语内容通吃:Loi Toubon 与 Charte 都要求法语。
7. Bill 96 与 Law 25 混淆。

## 八、工具

| 工具 | 用途 | 备注 |
|---|---|---|
| Piano Analytics | 法国企业常用分析栈 | 数据驻留与「数据主权」是采购词 |
| Matomo、Plausible | 自托管或轻量分析 | 受众测量豁免需按 CNIL 条件配置 |
| Vincent Hégo 观察站 | 法国 AIO 覆盖率本土追踪 | 样本 952 个查询,自述方法与局限 |
| Mistral IP JSON | 日志层验证 Vibe 爬虫 | 见 4.1 |
| OQLF Grand dictionnaire terminologique | fr-CA 术语查证 | 本次未逐词核 |
| Bing Webmaster + IndexNow | 桌面 Bing 的提交通道 | 桌面 Bing 11–16% |
| Yooda | 法国本土排名工具 | 未核功能 |

## 上线检查清单

| # | 检查什么 | 怎么查 | 通过/失败判据 |
|---|---|---|---|
| 1 | hreflang 互指与码合法 | `python3 scripts/hreflang_cluster.py <fr-FR URL> <fr-CA URL> <fr-BE URL> <fr-CH URL>` | 互指完整;无 `fr-AF` 一类非法区域码 |
| 2 | 标点前窄空格 | `python3 scripts/local_format.py --market fr "<页面样本文本>"` | 无「缺窄/不换行空格」✗(先做实体解码和文本抽取,见下方本地实测) |
| 3 | 头部元素 | `python3 scripts/head_check.py <URL> --market fr` | 无 ERROR |
| 4 | title/description | `python3 scripts/site_audit.py <URL> --market fr --json` | 本套件口径:title ≤60、description 77–155 字符;**审计法语页要带法语 Accept-Language**:`curl -sL -H 'Accept-Language: fr-FR' <URL> -o page.html`,再对本地文件跑脚本(`head_check.py` 支持本地文件) |
| 5 | 市场 lint | `python3 scripts/market_lint.py --market fr page.html --url <URL> --report` | CRITICAL=0;AUTO-FAIL=0;MANUAL 项人工过 |
| 6 | AI 检索爬虫放行 | `python3 scripts/robots_posture.py https://<域名>/robots.txt --signal visibility` | 搜索类与用户类 allowed |
| 7 | Mistral 爬虫三态 | 先 `curl -s https://<域名>/robots.txt -o robots.txt`,再 `rg -i mistral robots.txt` | `MistralAI-User` 与 `MistralAI-Index` 未被 Disallow;`MistralAI-Training` 的状态有决策记录(`robots_posture.py` 的 27 bot 矩阵不含 Mistral) |
| 8 | llms.txt(可选) | `python3 scripts/llmstxt.py check https://<域名>` | 看返回体是 markdown 而非 HTML 兜底页;200 不等于存在 |
| 9 | 日志层 Vibe 验证 | `python3 scripts/ai_referral_log.py <日志文件> --bot-ua --classify` | `MistralAI-User` 来源 IP 落在官方 JSON 内 |
| 10 | 魁北克法语版 | 打开 fr-CA 页,查商品页、结账、合同、发票是否有法语 | 全部有法语;法语不劣于英语(可见性、可达性) |
| 11 | 追踪器同意 | 无痕窗口打开页面,不点同意,看 Network 面板 | 非必要追踪器请求为 0;分析工具若走豁免,配置符合 CNIL 条件(13 个月/25 个月) |
| 12 | 实体简介一致性 | 抓各平台简介文本,`diff` 对比 | 逐字一致 |
| 13 | AIO 覆盖 | GSC 生成式 AI 表现报告(若已开放),国家=法国 | 记录展示数;季度对比 |

## 本地实测(2026-10-09)

> 脚本口径 2026-10-21 已改:twitter:* 与 OG 重复只记 INFO;缺 H1/描述为 WARN。下面的 ERROR 数是旧口径结果,复测会不同。

### 真实站验证(lemonde.fr / lefigaro.fr × site_audit + llmstxt check + head_check)

- `site_audit --market fr`:lemonde — title 53/60 ✓、desc 147/155 ✓、716 链接、**对非浏览器 UA 返回英文版**("Le Monde in English"),法语页审计须带法语 Accept-Language 重测;robots.txt 禁 Claude-SearchBot(1/4)。lefigaro — title 58/60 ✓、desc 119/155 ✓、8,807 词、robots.txt 禁 OAI-SearchBot、ChatGPT-User、Claude-SearchBot(3/4;PerplexityBot 放行)。
- `llmstxt check`:lemonde `/llms.txt` 返回 200,但四个路径都是同一张 HTML 兜底页(`<html lang="en">`),工具只看状态码,「200 不等于 llms.txt 在场」,需人工核 body;lefigaro 四路径真 404。
- `head_check`(旧口径):lemonde — 8 ERROR(twitter:*、apple-mobile-web-app-capable),title 落在第 12,947 字节(head 前有 17 个广告类 meta);lefigaro — 14 ERROR(mask-icon、smartbanner:* 17 条在 title 前)。
- **NBSP 检查对原始 HTML 有噪音**(market_lint.py):lefigaro 报 654 处,大量是撇号实体 `&#039;` 的分号被计入;lemonde 因返回英文版,18 处全是英文上下文。结论:先做实体解码、文本抽取、语言判定,再跑 NBSP 检查。在原始 HTML 上的计数是上界。
- 单次观察:lefigaro 3/4、spiegel.de 同日 3/4 封 AI 检索爬虫;lemonde 1/4。三站不足以说「欧陆付费墙大报默认封锁」。

## 维护

- 复审周期 **90 天**,下一次 **2027-01-09**(以 `scripts/markets.json` 的 `markets.fr.review_cycle` 为准)。
- 触发即复审:CNIL 与 Arcom 动态;StatCounter FR 月度份额(2026-09 桌面单月跳变是否持续);Vincent Hégo 观察站更新;Mistral robots 文档与 IP JSON;OQLF 执法公告;APIG 对竞争管理局申诉的进展;Google 法国站官方 AIO 公告。
- 断言半衰期 6–12 个月;AIO 时间线与流量数字最先过期,法规罚则次之。
- 头部站点 robots 姿态是当日快照,复审时重跑 `robots_posture.py`。

## 建议(需要别处配合,本文件不改)

| 键路径 | 现值 | 应改值 | 来源 |
|---|---|---|---|
| `scripts/markets.json` → `markets.fr.engines` | `["google","bing","vibe-ex-lechat"]` | `"vibe"`(Le Chat 已更名) | Mistral 帮助中心 |
| `markets.fr.notes` | 「Bill 96:…罚 ~3 万 CAD/日/项…」 | 「违反 OQLF 命令时罚 3,000–30,000 加元,累犯加倍,持续违法每日一次」 | Norton Rose / Charte 第 205 条 |
| `markets.fr.special_checks[5]` | 「非洲法语区桌面 Bing 9.2%→Bing Places 必配」 | 改「塞内加尔桌面 Bing 12.57%(2026-09,12 月区间 6.68–20.76%)」 | StatCounter SN |
| `markets.fr.special_checks[6]` | 「Vibe 三爬虫分态…」 | 保留;加注「`robots_posture.py` 27 bot 矩阵不含 Mistral,用 curl 查」 | robots_posture.py 源码 |
| `markets.fr.special_checks[7]` | 「AIO 疑问类覆盖 97.5%——月度跑疑问词面板」 | 改「疑问类 51.7%–97.5%(Hégo,按采样日期的区间)」 | Vincent Hégo 观察站 |
| `markets.fr.special_checks[8]` | 「Bill 96 罚 3,000-30,000 CAD/项+私人诉权」 | 去掉「私人诉权」(未在来源读到) | Norton Rose |
| `markets.fr.review_cycle.signals[0]` | 「Arcom 33-38% AIO 损失评估更新」 | 加「APIG 引用,已上线欧洲市场口径」 | Toute l'Europe |
| `markets.fr.review_cycle.signals[1]` | 「StatCounter FR 月度份额(桌面 Bing 10.92% 口径漂移)」 | 改「桌面 Bing 2026-06–08 为 10.98–11.79%,2026-09 为 15.83%」 | StatCounter FR |
| `markets.fr.hreflang_codes` | `["fr","fr-FR","fr-CA","fr-BE","fr-CH"]` | 保留;非洲法语区需要时加 `fr-SN`、`fr-CI` 等国家码,不得用 `fr-AF` | Google 多语言文档 |
