# 全球市场 SEO/GEO 指南(西语·葡语·阿拉伯语·法语·德语·印尼语)

> 建立于 2026-10-08。份额来自 StatCounter(2025-09~2026-09 各国页面);AI 引用语言绑定来自 [Temso](https://temso.io) 与 [Weglot](https://www.weglot.com) 研究;阿拉伯语 LLM 方言落差为同行评审([arXiv:2305.14976](https://arxiv.org/2305.14976)、[arXiv:2510.27543](https://arxiv.org/2510.27543))。标注「未证实/从业者说法」的条目不得写入验收。
> 总判断:这六个市场**都没有 Naver/Yandex 级的本地引擎**——Google 优先战术全部通行;真正的差异在**方言分裂策略、同意法对测量的影响、语言绑定的 AI 引用**。中/俄/韩三区另见各自专区指南。

## 一、六市场对照表(先看这个)

| 市场 | Google 2026 | 本地引擎? | 最大坑 | hreflang |
|---|---|---|---|---|
| 西语 | 88–94%(西 93.8/墨 88.4) | 无 | 把"西语"当成一个市场 | es-ES, **es-419**, es-MX…, es |
| 葡语(巴西) | 88.4% | 无 | pt-PT 内容冒充 pt-BR | pt-BR, pt-PT |
| 阿拉伯 | 93–99% | 无 | 字面直译关键词;方言盲 | ar, ar-EG, ar-SA, ar-AE |
| 法语 | ~96%(法,移动) | Ecosia ~1–1.4% | 一个 fr 变体走天下;魁北克 Bill 96 | fr-FR, fr-CA, fr-BE |
| 德语(DACH) | **87.8%(六市场最低)** | Ecosia ~1%, Yandex 1.6% | Sie/du 称谓错配 | de-DE, de-AT, de-CH |
| 印尼语 | 92.3% | 无 | baku/gaul 语域错配;只按桌面规划 | id |

## 二、逐市场要点与迷你清单

### 西语(西班牙 + 拉美)
- `es-419`(拉美/加勒比)是 Google hreflang 接受的唯一 UN M.49 区域码;常用 `es-ES + es-419 + es/x-default`,国码可指同 URL。
- **AI 引用语言绑定(实测)**:西语查询在 Google AIO/Copilot 得 83–84% 西语引用(Temso);西班牙的西语查询 7% 引用去 .es 域、26% 去西语源,英文查询仅 1.7%(Weglot)。
- 清单:hreflang 默认 es-ES+es-419;ES-ES→拉美绝不机翻(vosotros/ustedes、coche/carro/auto);es-US(美国西语人群)是独立机会;按方言区做关键词;**AI 引用审计必须用西语提示跑**。

### 葡语(巴西)
- **巴西是 ChatGPT 最强采用市场:~5,000 万月用户、25.5% 人口用 App(全球最高;美国 ~15.6%);ChatGPT 占巴西 AI chatbot 流量 79.76%**;葡语是其第三常用语言;AIO 2024-08 入巴西。
- pt-BR vs pt-PT 词汇/语法差异(usuário/utilizador、"está falando"/"está a falar")足以让机翻 pt-PT 内容表现差(本地化共识,无单一研究)。
- 清单:pt-BR 专属关键词(绝不 pt-PT 进口);.com.br+GBP;口语/俚语词群纳入;**ChatGPT/LLM 可见性优先级全市场最高**;Bing ~9.6% 值得索引。

### 阿拉伯语(中东)
- Google 93–99%(埃及/伊拉克 99%+)。本地助手存在(Jais·MBZUAI 开源、Fanar·卡塔尔 QCRI、GoBLIN-8B)但 ChatGPT 主导使用(无硬份额)。
- **RTL 技术 SEO 不可谈判**:`dir="rtl"`、双向文本处理、镜像布局、逻辑 CSS 属性。
- **内容架构:MSA(现代标准阿拉伯语)骨架 + 方言层(埃及/海湾)进正文与口语文案**;不直译英文关键词;正字变体(hamza/ta-marbuta 不一致)需归组。
- 同行评审:ChatGPT/GPT-4 在 MSA 上好、**方言显著退化**(arXiv:2305.14976;19 模型基准确认)→ MSA 内容更可靠被 LLM 检索转述(推断,标注)。
- 清单:RTL 全链;MSA+方言分层;阿拉伯原生关键词+变体归组;hreflang `ar`(+国码或单 ar);GEO 面 MSA 优先;拉丁转写查询是真实细分(从业者说法,未证实)。

### 法语
- 唯一值得提的非 Google:Ecosia ~1–1.4%。**魁北克 Bill 96**:面向加拿大商务站有法语要求——合规先于内容。
- fr-FR/fr-CA/fr-BE/fr-CH 各需关键词集+hreflang;排版细节(`:;!?` 前不换行空格、数字格式)影响本地化质量。
- 清单:变体分离;Bill 96 检查;法语排版规范;法语提示跑 AI 审计(勿假设英文查询的引用面)。

### 德语(DACH)
- **Google 87.84%(六市场最低)**,Bing 6.49%+Yandex 1.56%+Ecosia ~1%。
- **Sie/du 称谓改变实际搜索查询词**:B2B 默认 Sie;德国 du 化快于奥/瑞(奥瑞更久守 Sie)——按目标国决定,不一次定 DACH。
- 复合名词→更长查询是常态;GDPR 执法严,同意横幅(Consent Mode v2)损分析完整性——**SEO 实验设计必须计入数据缺口**。
- 清单:Sie/du 按国别;匹配长复合词;同意模式纳入测量设计;DACH≠一个市场(AT/CH 词汇+正式度不同)。

### 印尼语
- Google 92.3%;**AIO 印尼语是 2024-10 首批六语言之一**;**移动 >82% 搜索流量**(全球 ~65%)——移动优先不是口号。
- 正式(baku)vs 口语(gaul)分裂;城市 GenZ 英印混码;**已发表口语词典 3,592 词→正式对应**(UAI 仓库),可直接用于关键词规范化;baku/gaul 搜索量对比是研究空白。
- EYD V(2022 拼写修订)影响关键词拼写。
- 清单:baku+gaul 双轨关键词;移动优先不可谈判;预期英印混码查询;拼写对齐 EYD V。

## 三、跨市场合规速查

- EU(西/德/法):GDPR+同意横幅损测量数据——A/B 与流量实验设计时声明。
- 巴西 LGPD(2020-09 生效):分析 cookie 需选择加入式同意。
- 加拿大魁北克 Bill 96:fr-CA 商务内容有法语义务。
- 六市场均无中俄式数据本地化障碍——SEO 测试可正常进行。

## 四、GitHub 供给空白(2026-10 检索)

非英 SEO skill 仓库近乎空:西语 top 1–5★(samuelurones28/seosindrama-skills 3★)、巴西(franklinbaldo/rossio 3★)、法语(david-corroy/skills-marketing-fr 1★)、印尼(alvinindra/bahasa-skills 4★)、阿拉伯(growthack88/growth-marketing-os 116★)。对照英文头部 2,343★——**印尼与巴西是"供给 vs 市场规模"落差最大的两个**,也是本套件全球覆盖的直接卖点。
