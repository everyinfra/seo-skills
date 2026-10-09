# 多语言工作流(全球 SEO/GEO 一把做)

> 建立于 2026-10-09;2026-10-08 并入全球区域知识(按结构反馈,原 regions/ 专区已融入套件各文件):区域 AI 平台事实见 [AI 平台差异事实库](../content/geo-platform-differences.md) 第六节,区域爬虫与收录见 [AI 爬虫政策](../technical/ai-crawler-policy.md),hreflang 区域码细则见 [hreflang 校验](../technical/hreflang-validation.md),各市场关键词工具链见 [关键词意图分类](../research/keyword-intent-taxonomy.md) 区域段,中文引擎细则见 [中文 AI 搜索指南](../content/chinese-ai-search-guide.md)。
> 本文件是全球主干:站点面向哪些市场 → 每个市场的引擎格局、必备工具、语言规范 → **逐市场分开评分,一个总分掩盖"英文版 90 分、俄语版 40 分"**。

## 一、语言约定(本 skill 的运行规则)

1. **面向用户的输出使用用户的语言**——用中文提问得中文报告,英文提问得英文报告。参考文件本身的语言不决定输出语言。
2. 参考文件的语言分工:**中文市场细则用中文写**(数据源是中文生态);**全球规则用中文写+英文术语括注**(主要给 agent 消费);输出模板的结构性标题保留双语(见各模板)。
3. 分析一个多语言站点时,**逐语言版本分开评分**——国际化失衡是最常见的失败模式。

## 二、市场总表(2026-10 数据,来源类型在各区域段标注)

| 市场 | 搜索格局(2026) | 决定性事实 | 进入该市场的就绪闸门 |
|---|---|---|---|
| 中文(大陆) | 百度+自有生态;8 大 AI 引擎各分护城河 | 品牌官网仅占引用 **1.37%**(187,818 条实测) | 百科/百家号/知道三件套+公众号 |
| 英文(全球) | Google AIO / ChatGPT / Perplexity / Gemini / Copilot | 92% AIO 引用来自自然 top-10 | Wikidata 实体一致+Bing 收录 |
| 俄语区 | Yandex ~70–73%,Google ~25–28%(StatCounter) | Alice AI 从自然 SERP 取源——**经典 top-10 即引用前提** | Webmaster 验证+Metrica(152-ФЗ 姿态) |
| 韩语区 | 双口径:StatCounter 并列 vs 本土面板 Naver 63–64% | AI Briefing 几乎只引 Naver 自有生态 | Search Advisor+Naver Blog(C-Rank) |
| 日语区 | Google 59–75%(口径差大)+Bing **28–33%** | Yahoo! Japan=Google 索引;>95% AI 证据来自第三方站 | SC 生成AIパフォーマンス报告+Bing 可爬验证 |
| 西语 | Google 88–94%,无本地引擎 | **es-419 是 Google 接受的唯一 UN 区域码**;西语查询 83–84% 引西语源 | es-ES+es-419 hreflang 决策 |
| 葡语(巴西) | Google 88.4%,无本地引擎 | **ChatGPT 最强市场**(25.5% 人口用 App,~5,000 万月用户) | pt-BR 原生关键词+LLM 可见性最优先 |
| 阿拉伯 | Google 93–99%,无本地引擎 | RTL 全链;MSA 内容 LLM 处理好、**方言显著退化**(同行评审) | `dir="rtl"`+MSA 骨架/方言层决策 |
| 法语 | Google ~96%,Ecosia ~1% | 魁北克 Bill 96 对 fr-CA 商务站有法语义务 | 变体分离+Bill 96 检查 |
| 德语(DACH) | Google **87.8%(主要市场最低)**+Bing 6.5% | Sie/du 称谓改变实际查询词;同意横幅损测量 | 按国别定称谓+Consent Mode v2 纳入测试设计 |
| 印尼语 | Google 92.3% | 移动 >82% 搜索流量;AIO 首批六语言之一 | baku/gaul 双轨关键词+移动优先 |

俄/韩/日三个"独立学科"市场的完整细则(排名信号、合规、就绪清单)已并入本文件第四至八节及对应能力文件;英文与中文见各自指南。

### 长尾主流市场(2026-10-08 第二轮并入;Google 主导,差异在语言机制)

| 市场 | 格局(2026) | 决定性事实 | 主要坑 |
|---|---|---|---|
| 印地/印度 | Google ~97% | **ChatGPT ~1 亿周活,其第二大市场**;AIO 覆盖英语+印地语;罗马化文本使 AI 处理掉 5–12 F1(arXiv 2512.10780) | 把英文词翻成"纯印地语"——真实查询量在 Hinglish/罗马化;语音查询占比高;`hi-IN` 与 `en-IN` 分开 |
| 意大利 | Google ~89% | it-CH(提契诺 ~35 万人)用 .ch 域+瑞郎价+混德法语词 | it-CH 复制 it-IT→信号被归并,瑞士版排不上;当独立 locale |
| 土耳其 | Google ~73%+**Yandex ~26%**(2026 反弹) | **第二个 Yandex 市场**——YandexGPT SERP 答案是本市场特有 GEO 面;双引擎优化+Yandex Webmaster 注册 | 黏着语后缀把格/数/领属折进一个长词→英文式头部词研究低估量,须研究屈折形式与词干 |
| 越南 | Google ~93%+**Coc Cốc ~6%** | Coc Cốc 浏览器自带 AI 机器人(本地 GEO 面) | 声调符号决定词义但移动端常不打入("khong/không")——有调/无调变体意图不同,当独立词跟踪 |
| 泰国 | Google ~99.5% | AI Mode 已开放泰国(官方名单) | **泰文无词间空格**→分词是核心:密度工具/标题截断/精确匹配计数全失效;meta 在词中间被截 |
| 波兰 | Google ~90%(Bing 7.4%,桌面高) | 9 个变音字母;Google 有调/无调都匹配 | 按过时建议剥变音符——伤品牌与 AI 保真;内容**带**正确变音符写 |
| 荷兰/弗拉芒 | Google ~90% | 比利时三语(nl-BE/fr-BE/de-BE);.nl 域在比利时表现差 | 一个"荷兰语"变体+单一 nl 码服务两国——弗拉芒词汇(auto's/wagen)与正式度不同,分开 |

七个市场的 GitHub 工具化几乎为零(仅越南有 4★ 工具;意/土没有)——供给空白与市场规模落差大。

## 三、工具栈映射(每市场的"必须用",不是可选)

| 功能 | 俄语区 | 韩语区 | 日语区 | 其他市场 |
|---|---|---|---|---|
| 站长平台 | Yandex.Webmaster(ИКС 站点质量;**自带 Alice AI 可见面板**;主机级索引) | Naver Search Advisor(canonical URL 须精确一致;sitemap 同域<10MB) | GSC(**生成AIパフォーマンス 报告**)+Bing WMT | GSC(+Bing WMT 当 Bing>6%) |
| 网站分析 | **Yandex.Metrica**(免费含会话回放;GA 因 152-ФЗ 实际不可用) | Naver Analytics(弱于 GA4,无 IP 排除;生态流量用) | GA4(AI 助手渠道) | GA4 |
| 关键词研究 | Yandex.Wordstat(`"短语"`精确、`!词`精确词形;预测曝光非搜索量;分区域+季节) | Naver DataLab(按年龄/性别/设备)+Naver Ads 关键词工具 | ラッコキーワード(挖候选)→KW Planner JP(验量) | 各语言独立做,不互译 |
| 本地/地图 | Yandex Business/Maps | Naver Place(플레이스) | GBP(=日式"MEO")+食べログ/ぐるなび 并行 | GBP |
| 内容生态 | Dzen(6,800 万 MAU;nofollow 经济,当品牌面) | **Blog/Cafe/지식iN 必做**(SERP 与 AI Briefing 双入口) | note.com/知恵袋/Qiita·Zenn(AI 引用底物) | Reddit/行业媒体 |
| 电商搜索 | Yandex Direct(付费需 erid 标记) | **Coupang**(3,325 万 App 用户,事实上的商品搜索) | — | 按品类 |

**土耳其是第二个 Yandex 市场**(Yandex ~26%,2026 反弹):上表俄语区列的 Webmaster/Wordstat/YandexGPT 逻辑同样适用,且需 Google+Yandex 双引擎优化。越南的 Coc Cốc(~6%)要单独提交收录。

## 四、语言与内容规范(阈值与惯例不可跨市场互套)

| 维度 | 各市场规范 |
|---|---|
| 句长 | 中文 15–25 字理想;英文 15–20 词;>35 字/词难解析 |
| 支柱页长度 | 中文 ≥1,500 字(头四分位 1,943);英文 2,000–2,900 词;**日语按体裁分层:MEO/本地 500–1,200、一般 1,500–3,500、支柱 7,000–12,000 字** |
| 营销词密度 | 中文创新领先/极致类 ≤3/页;英文 hype 词同理 |
| 称谓/语域 | **德语 Sie/du 按国别定**(B2B 默认 Sie;德国 du 化快于奥/瑞);**日语です/ます 全站一致**(学术栏可用だ/である);韩语敬语体系统一 |
| 语域分裂 | **阿拉伯=MSA 骨架+方言层**(埃及/海湾)进正文;**印尼=baku(正式)/gaul(口语)双轨**;**印地=Hinglish 混码**(罗马化/天城体/英语互换,真实量在 Hinglish 非纯印地语);越南=有调/无调双轨(移动端常不打入) |
| 文字方向 | 阿拉伯全链 RTL:`dir="rtl"`+双向文本+镜像布局+逻辑 CSS 属性 |
| 文字变体 | 日语全/半角(ＳＥＯ/SEO)与片假名转写变体归组;阿拉伯正字变体(hamza/ta-marbuta)归组;**波兰 9 个变音字母:内容带正确变音符写**(Google 有调/无调都匹配);**泰文无词间空格——密度工具与精确匹配计数失效**,须验证分词;土耳其黏着语长词干+屈折形式 |
| 排版细节 | 法语 `:;!?` 前有不换行空格;`1.000,00`(de)vs `1,000.00`(en/zh);中文日期 `2026年10月9日` |
| FAQ | 中文 ≥10 对、答 80–200 字;英文覆盖 10 个真实买家问题 |

## 五、多语言站点的检查顺序

1. **可达性(每区一套)**:robots 对引用型 bot 的政策([AI 爬虫政策](../technical/ai-crawler-policy.md));中文站确认 Baiduspider/Bytespider 未禁;**俄语区对 `YandexAdditional` 做显式决策**(允许=进 Neuro/Alice 引用池);**日语区单独验证 Bing 可爬**(28–33% 份额喂 Copilot);韩语区确认 Naver robot 收录请求已发。
2. **hreflang 八检**:自引用/双向返回/ISO 码([hreflang 校验](../technical/hreflang-validation.md))——中文简繁体用 ISO 15924 文字码;西语区用 `es-419`;阿拉伯 `ar`+国码。
3. **内容平价**:德语比英语长 25–35%、日语短 10–25%、中文比英文短 20–40%——大幅偏离提示截断或未本地化。
4. **本地实质**(不是字面翻译):示例、案例、货币、合规表述、联系方式本地化;未复核机翻标记为 scaled-content-abuse 风险。俄语区原生西里尔+7 号电话是 Vega 专家性信号。
5. **本地格式**:按目标区域(见第四节排版行)。
6. **逐引擎可见性**:中文引擎中文提示词(中文指南 7 组问句);全球引擎英文;俄/韩/日按第三节工具栈的引擎清单用当地语言提示——**同站各语言分开测,不合并**。

## 六、内容策略:一套事实,多种变体

实测结论(中文指南):跨渠道发同文无效;正确做法是**一套核实事实 → 每渠道一个变体**:

| 变体 | 语言/风格 | 去处(按市场) |
|---|---|---|
| 权威页(最长) | 目标市场的正式语域;schema+来源表 | 官网对应语言版 |
| 社交版 | 口语标题、结论先行、短段 | 公众号(中)/VK·Dzen(俄)/Naver Blog(韩)/note(日)/LinkedIn(英) |
| 社区版 | 当地主流问答社区体 | 知乎(中)/Reddit(英·日)/지식iN(韩)/知恵袋向(日) |

**JSON-LD 的 `description` 与每语言的事实卡逐字一致**——不一致是品牌描述在各引擎间漂移的第一成因。

## 七、多语言关键词研究

- 关键词**不互译**:各语言独立研究,再在战略层对齐主题。工具链按第三节选(Wordstat/DataLab/ラッコ)。
- **方言与变体归组**:西语 es-ES vs es-419 词汇(coche/carro/auto);阿拉伯 MSA+方言+正字变体;印尼 baku/gaul(3,592 词口语词典可参考);日语全/半角+片假名;德语复合长词是常态不是异常;印地 Hinglish 三种书写(罗马化/天城体/英语);越南有调/无调;意大利 it-CH 混德法词;荷兰 nl-NL/nl-BE 词汇分流。
- **转写查询是真实细分**:俄语区拉丁转写、印度罗马化印地(待补)——从业者共识,量级未证实,先小规模验证。
- SERP 特征按语言/区域分查;sitemap 按语言分组,`<lastmod>` 反映该语言版真实更新。

## 八、合规速查(按市场)

| 市场 | 要求 | 对 SEO 工作的影响 |
|---|---|---|
| 俄语区 | 152-ФЗ(俄公民数据须入库俄境);ORD/erid(付费广告标记,未标最高 50 万₽) | 俄向页面用 Metrica 非 GA;**自然 SEO 内容不算广告**;付费投放先解决 erid |
| 欧盟(西/德/法) | GDPR+同意横幅(Consent Mode v2) | 分析数据有缺口——A/B 与流量实验设计必须计入 |
| 巴西 | LGPD(2020-09 生效) | 分析 cookie 需选择加入式同意 |
| 加拿大(魁北克) | Bill 96 | fr-CA 商务站有法语义务,合规先于内容 |
| 韩国 | PIPA | cookie 同意提示+跨境传输(如 GA4)需披露 |
| 日本 | ステマ規制(2023-10) | **评价征集方式受限**——MEO/口碑策略先过这条 |
| 中国大陆 | ICP 备案等 | 见中文指南 |

六市场之外(英/中)无数据本地化障碍;俄/中是仅有的两个"分析工具也要换"的市场。

## 九、常见坑

1. **机翻直接上线**无人工审校——scaled-content-abuse 风险+转化率双输。
2. **英文阈值套其他语言页**(或反向)——第四节列出不可互套项。
3. **只测主语言可见性**——中文盲区元宝/豆包,英文盲区 AIO/Perplexity,俄语盲区 Alice/Neuro,韩语盲区 AI Briefing(只引 Naver 生态),日语盲区 Gemini(30% 使用)——每个命中市场都要测。
4. **同文跨渠道群发**——实测无效且稀释实体一致性。
5. **hreflang 与 canonical 打架**——八检第 1/6 条是最常见失败点。
6. **把一个语区当一个市场**——"西语"至少分 es-ES/es-419;DACH 的 Sie/du 按国别;pt-PT 冒充 pt-BR;阿拉伯 MSA/方言不分层;印尼 baku/gaul 不双轨。

## 十、十八市场独到方法索引(2026-10 第一波充实:独立学科五市场)

每个市场"只有在这里才需要做/才存在"的做法——这就是该市场的独到层:

| 市场 | 独到方法(能力锚点) |
|---|---|
| 中文 | 超级 App 站内搜索三件套(搜一搜 Peoplerank/小红书 CES 互动分/抖音四因子,中文指南§六);排行站**免费申报**(maigoo/CNPP);元宝=公众号护城河(内容);采样风控≤20 问/时段(监控) |
| 英文 | **协议层 agent-readiness**(ARD/ai-catalog.json/WebMCP/Web Bot Auth,英文站全开、其他语区只保留 llms.txt 类等价物——分叉逻辑);fan-out 修饰词逆向(DevTools 提取);引用四级阶梯(retrieved→cited→mentioned→recommended)+recommended-against 暗级;Cloudflare 托管 robots 检测;Lighthouse `AGENTIC_BROWSING` 审计 |
| 俄语区 | **Telegram 公开镜像 SEO**(t.me/s/ 镜像被 Yandex 抓取,~90% 曝光来自 Yandex;标题=关键词+品牌,前 150 字符即摘要);**Webmaster SoV 报告**(官方 GEO 计量);商业透明层(оферта/реквизиты 6 类法定页);9 项官方违规+накрутка ПФ 红线(6–12 月罚);目录=Yandex Бизнес/2ГИС/Zoon/Flamp/Отзовик+TGStat;VK 群讨论帖可如内页排名 |
| 韩语区 | **`nosourceinfo`**(全球唯一官方 AI 引用退出 meta);연관채널 sameAs 实体图谱(官方域名清单含 치지직/당근);Yeti robots 语义(5xx=全封/host 隔离);**AI 인용수 公开可侦察**(메이트当选者公开);웹문서/서비스内双通道;블로그 투트랙(生态内+自有域);description ≤80 全角字 |
| 日语区 | **全角阈值体系**(title 32/desc 120/正文 300 全角字,kseo);**「AI 臭」密度 lint**(28 转用动词×14 构文,人类上限 3–8 倍频率判 AI 文);MEO 三因素×投稿週 1 回;業界ポータル=引用+垄断双现实(食べログ/じゃらん;NAP 完全一致);卫星站终结论(SpamBrain 三层检测);垂类>综合榜;PR TIMES 特例 |
| 西语 | **审计报告翻译层**(技术发现→四段式商务话术+行业类比库,731 审计校准);GEO 五维评分带西语 NLP 特征(电话/地址正则、`¿...?` 疑问式 h2、information gain ≥3 自带数据点);**es-US 集体代搜**(81% 受托);支付即意图词层(OXXO/cuotas/contra entrega);半岛偏置对抗 |
| 葡语(巴西) | **Reclame Aqui 三重角色**(22.3% ChatGPT 品牌回答被引/关键词语料/信任信号→SAC 成为 GEO 手段);**WhatsApp 发现层**(官方 Status 广告+Canals;OG 先行因预览缓存极强;wa.me 归因链);E-E-A-T 巴西化(OAB/CRM 委员会注册号+CNPJ 页脚);pt-BR 反 AI 35 型;季节日历(Black Friday>母亲节>13º/IR/Carnaval,提前 60–90 天) |
| 阿拉伯 | **品类×语域矩阵**(金融/法律/B2B=MSA,电商/娱乐=方言,educated colloquial 兜底);**文化日历闸门**(Ramadan 内容弧 30 天/发布窗口 Iftar 后/Taraweeh 后/Suhoor;海湾峰值 10–3 月);GEO 测量=50 查询×预期标注×14 天重测协议;合规预审(GAMR/TDRA 词表);COD"الدفع عند الاستلام"信任资产;文案比英文长 ~20% 防换行 |
| 德语(DACH) | **Ansprache/Tonalität 两字段**+一致性优先;Sistrix 锚点(AIO 覆盖 20%/Pos.1 CTR 27%→11% **−59%**/月损 2.65 亿点击;1/3 德国人周用 AI——Bitkom 官方);GEO 引用源优先级=德国官方机构(BAFA/Fraunhofer/行业协会)>Tier-1 媒体>国际泛源;**测量:GSC(免 consent)为基准+GA4 建模值并列 consent rate**,小站勿依赖 Advanced CM 建模;瑞士=同 .ch 下语言子目录+CHF 原生定价 |
| 法语 | **Vibe(ex-Le Chat)单独优化**(三爬虫分工+AFP 通稿信源+22.9% unique 推荐);AIO 法国 2026-07-22 上线,新闻站 2 个月 −22%;**Bill 96 无规模豁免**(25+ 须注册 OQLF/等效可见性/商标例外须配法语通用描述/罚 ~3 万 CAD/日/项);魁北克"法语化"vs 法国收英语词的词汇表(courriel/balado/magasinage ↔ email/podcast/shopping——OQLF 官方术语库);非洲法语区(塞内加尔桌面 Bing 9.2% 必配 Bing Places);法国 9 层目录+**40–60 词规范实体简介全平台逐字重复** |
| 印尼语 | **AIO 触发率 37.2% 全球第一**;引用格局=视频/社媒 30.7%+电商平台被引+品牌词官网 72.2% 出现率;双雄+TikTok 分流(产品发现走 Tokopedia/Shopee/TikTok,Google 承担研究意图);**slow-4G 节流为测试基线**(全国中位 15–38 Mbps);meta 前 120 字符安全区;"hiruk pikuk"禁用 |
| 印地/印度 | **GSC regex 快照缺口修复法**(英文页在 Hinglish 查询排首页但 CTR 0.16%——顶部加原样措辞定义行);**超 App 内 ChatGPT**(JioHotstar×OpenAI 2026-02);目录=GEO 引用源(JustDial/IndiaMART/Sulekha);语音=助词词库(kaise/konsa/batao)×产品词;拼写漂移聚类(音译规范化);Sarvam MCP(Indic API 官方后端) |
| 意大利 | **P.IVA→Registro Imprese 竞品链**(增值税号→ATECO 码+省→真实竞品,公开 API 独有);"数据阶梯+声明降级"(测量值 vs 估算值标注);意语 AI 引用=Wikipedia 48.67%+个人专家站(Aranzulla 模式)第三;**4 星>5 星信任悖论**(意大利用户更信 4 星);AIO 2025-03-26 与 DACH 同批 |
| 土耳其 | **Yazeka**(土语专属 AI 答案品牌,非 YandexGPT);**AIO 引用 75.3% 绑定自然前 10**(美式"社媒核心"结论不可平移);Wordstat TR(2026-01)+webmaster 全土语界面;黏着语 Zemberek 工作流;Trendyol 电商主导但 marketplace 页仅占 AIO 引用 2.5%;**份额口径冲突并记**(StatCounter 26% vs 本地 3–5%) |
| 越南 | **t0mmy 99 条规则**(提问式 H2≥50%、密度只设上限 1/150 且仅计正文、nonce 双层质量门防 agent 自评篡改、标题词进前 30 字符防改写);Coc Cốc 官方偏好越南语+.vn;**句长方差检测**(反 AI 文风,mona-seo-check-vi) |
| 泰国 | **`Intl.Segmenter("th")` 分词定论**(主流 SEO 工具栏在泰文站全错);**grapheme 字素计数**;泰调可读性公式(句≤25 词/词均≤5 字符);Wongnai/Pantip 外链=本地信号;PDPA 明示同意(医疗);泰文字体子集省 60–80% |
| 波兰 | **Bing 桌面 ~13.3%**(全球 3 倍)必做 Bing WMT+IndexNow;**品牌引用按引擎分列**(ChatGPT PKO vs Gemini mBank);URL 转写六机构共识;Wykop/Dobreprogramy/Spider's Web 品牌渠道;sierotki 孤字排版规则 |
| 荷兰/弗拉芒 | **je/u tone 双轨**(nl-NL=je 连 B2B;nl-BE=u 句中小写);>60% 网民用 AI(欧洲最高档);**[INVULLEN] 占位制+拒绝虚构 norm**(锚文本不给比例);GBP 描述用满 750 字符+KvK 商会号;5 个垂直行业本地页模板模式 |

**跨区融合原则**(第一波提炼,全区通用):
1. **每个市场先识别封闭生态搜索入口**(搜一搜/抖音 ↔ Naver Blog/Cafe ↔ Dzen ↔ Telegram 镜像 ↔ VK 群)——同构模式,逐市场点名。
2. **SoV 取代位置**:AI 可见度的计量观是"份额"而非"排名"(Yandex 官方已如此设计,utsushi 的 Share of AI Voice 同构)。
3. **断言半衰期纪律**:信源偏好结论 6–12 个月失效,所有引用偏好表带测试日期;监控**值的日期**而非值("낡은 데이터는 모든 하한선을 통과한다")。
4. **免费申报先于付费**:榜单渠道先穷尽免费通道(maigoo 自主申报 ↔ G2/Capterra 免费 listing)。
5. **行为代理离线审计**:首屏清晰/低空锚率/模板文本占比(Horosheff 7 分制)——无数据时近似行为因素。
6. **免责声明即 GEO 内容**:安全边界文案可被当"安全答案片段"引用(医疗/金融/法律全区适用,俄区实证)。
7. **密度检测思路**:"AI 偏爱词频=人类上限 N 倍"可建各语言基线(日语六法则最完整)。
8. **[要追加]/[要確認] 占位符协议**:禁编造数字,全区规范。
9. **垂类定番媒体子表**:每语区建"行业必引媒体"清单(汽车案例实证)。
10. **互动分公式化**:CES(评4/转4/关8>赞藏1)反向指导社区内容设计(引导收藏回复)。
11. **每市场识别"Reclame Aqui 等价物"**:投诉/评价平台是被 AI 大量引用的信源(巴西 22.3%)——德/英 Trustpilot、美 PissedConsumer、俄 Отзовик 同构,纳入 GEO 审计。
12. **反 AI 文案的"本地化桥"**:每语种建自己的 slop 标记表(日语 28 转用动词×14 构文/pt-BR 35 型/印尼 hiruk pikuk+Title Case+em-dash)——检测"密度"而非"误用"。
13. **正字法改革关键词分裂**:巴西 AO90/德语 1996 改革/印尼 EYD V——改革市场通用检查项:新旧拼法 Trends 对比后决定兼收。
14. **主权助手模式**:每个大市场问两句——"本土助手用什么爬虫?"(法国 Vibe 三分工已是官方范例)"信源里有没有国家通讯社?"(AFP→新华社/韩联社=被本土 AI 引用的隐藏高速通道)。
15. **语域双轨通用模板**:"关键词跟手指、正文跟词典"迁移到所有口语-正式分裂语(土/阿/印地/他加禄/日);**AI 引用偏好正式语源**(印尼 AIO 引用的健康/政府站全为 baku)——GEO 内容层应比 SEO 内容层更偏正式语域。
16. **职业注册号=本地执业凭证字段**:巴西委员会号(OAB/CRM)、德国官方机构源——管制市场 E-E-A-T 的可验证信号。
17. **支付即意图维度**:OXXO/cuotas/contra entrega/Pix/COD——支付方式词层进意图分类(各市场通用模式)。
18. **本地引擎 watch 列表**:每区标配(法 Vibe/阿 Fanar·Jais/印尼 Sahabat-AI/韩 Wrtn)——本土助手不照搬美系排名,小语种原创内容的边际收益更高(Vibe 22.9% unique 推荐)。
19. **官方注册数据竞品链**:意 P.IVA→Registro Imprese(公开 API)>瑞 Zefix(免费)>德 Handelsregister(付费)——"官方注册竞品发现"三态适配。
20. **分词/字素基建**:无空格文字(泰/日/中)先 `Intl.Segmenter` 再谈密度;标题按 grapheme 计——**全球主流 SEO 工具栏在泰文站全错**是教训。
21. **质量门防自评篡改**:validator 达标 ∧ 独立评分 ≥85 才发布+状态目录只读+nonce(t0mmy 模式)——agent 产线的通用安全层。
22. **快照缺口诊断法**:GSC regex 找"排名好但语言错配"的零成本机会(印度 Hinglish 案例可移植所有混码市场)。
23. **口径冲突并记**:土耳其 Yandex(26% vs 3–5%)、日本引擎份额、韩国双口径——同一事实两源矛盾时**并记两说+建议本地实测**,不选边。

*(十八市场独到层全部填实:第一波 5 + 第二波 6 + 第三波 7。)

## 十一、本地社区与信息源索引(2026-10-09 深挖轮:本地圈才知道的事)

每市场的"圈内共识、信息源、国际圈最大误解"——这是套件区别于翻译型国际 SEO 内容的层:

| 市场 | 圈内信息源 | 本地圈独有共识 | 国际圈最大误解(纠偏) |
|---|---|---|---|
| 俄语区 | **searchengines.guru**(最大论坛)、habr、vc.ru、SEONews、Topvisor/Keys.so 工具圈 | 商业因子 76 条清单按 6 块过站;区域 lr 码(莫斯科 213≠莫斯科州 1,全俄 225),区域间位差可达 40 位;Яндекс Бизнес 卡片=区域主信号(审核可能要拍楼体视频);Вебвизор 三图(点击/滚动/表单)是 ПФ 优化闭环;**AI 直接流量极小(Алиса 0.02%/ChatGPT 0.25%)——损失发生在搜索内部**;站长情绪已转向"进 Нейро 答案+买量" | 用 GA4 替代 Metrica;"каталоги 死了"=不做本地目录(实际迁移到了 Бизнес 卡片);不知道 ПФ 是一线因子 |
| 韩语区 | 네이버 검색 공식블로그(官方)、brunch/tistory 实战圈、**아프니까 사장이다 카페**(43 万会员)、i-boss、Kmong、블랙키위 工具 | 发文时刻表(午夜=스마트블록/6 时=인기글,8-9 时反映;行业黄金时段各异);글자수 1,500-2,000;지수설(非官方指数段位);"최적화 기간"3-6 个月;**플레이스 저장有 30 元/单的付费市场,日 30-50 渐增"显自然"**;2025-05 起 GPS 实访 clip 리뷰 才信任展示;AI 인용 ~70% 来自博客/카페 UGC | Google SEO 可移植(Naver 是平台生态非外链生态);"Naver=搜索引擎"(实为 UGC 编排门户) |
| 日语区 | **海外SEO情報ブログ**(铃木谦一,日更)、検索エンジン情報ラウンジ、SEMリサーチ、Web担当者Forum、SEOラボ(京大联合) | 内链 1 見出し 1-2 本/3000 字 4-8 本/单页 45 本上限/3 クリック以内;タグ页·作者归档 noindex 国民级惯例;GBP 投稿週 1-2 回(每篇仅显示 ~7 天,月曜=推荐品/木金=周末预约);**口コミ:"星5つでお願い"本身构成要件(QR 王道/LINE 次日 follow);Ask Maps 2026-08-07 上线,AI 直接读口コミ本文选店**;SEO 月费 10-50 万円 vs **MEO 代行仅 1-5 万**(10 倍价差);民间 life-from2020 数据集(9,891 引):4 引擎域名重复率仅 ~10%,AI 推荐 No.1 有 45% 在 SEO 圈外 | 要单独做 Yahoo! Japan(=Google 索引);低估 MEO/口コミ 文化;直译=本地化(全半角/外来语归一) |
| 中文 | 站长圈(卢松松/白杨SEO)、5118/爱站/chinaz 工具圈、知乎实操帖 | **"快速收录"已死→"快速抓取"仅 VIP;现役=API 推送(配额有限)+sitemap**;5118 已出 MCP(36 API 接 Claude);假权重灰产识别(刷冷僻高指数词→爱站权重虚高→卖链);友链平台 2898(权4 站 30-50 元/月);公众号"入池"机制(初始池→点击率/完读率升级);**蜘蛛池只抓不录且会被盯上(百度官方定性黑产)** | 必须 .cn/备案才上百度(错);百度=中文 Google(JS 渲染更弱);meta keywords 有效(过时);最大盲区:忽视搜一搜/小红书 |
| 西语 | 西:**SEOPLUS 大会**/Campamento Web 播客/Human Level;拉美:Nubimetrics Academy/Telegram 群 | 外链高度商品化(niche 博客 50€→大媒体 1,500-5,000€,新闻稿 7€/媒体起);拉美 **Facebook 本地页+WhatsApp 是事实转化按钮**(QR 到店+WA 索评);拉美托管常在欧洲→CDN 是本地 SEO 前置 | "一份中性西语通吃"(auto/coche/carro 不可互换);"拉美=低竞争"(墨城金融电商词竞争激烈) |
| 葡语(巴西) | **Conversion《Guia de SEO》**(圈圣经)/SEO Happy Hour 播客/MestreCast | ML listing:60 字符标题+ficha técnica 全字段+**问答响应速度是排名因子**+投诉率<1% 保 Mercado Líder;troca de links 无安全阈值(改三角链);**IG"姓名字段放关键词"+"评论 X 发链接"DM 自动化(Meta 已出免费原生版,一个素材一个词)**;AIO 2024-08-15 上线且无需 Search Labs 全量 | 翻译≠本地化;hreflang 用 pt 而非 pt-BR;点击后信任差(Pix/boleto/本地徽章) |
| 德语区 | **ABAKUS 论坛**(4.5 万会员)、SISTRIX 博客、Seokratie;SEO Campixx/SEOkomm 大会 | 链接实为**月租制**(119€/月起);软文不标"Werbung"→**竞争对手 Abmahnung 律师函风险大于 Google 惩罚**;OLG Köln 2024 判例:拒绝键须与接受键同等醒目;Matomo/Plausible 为默认;DE AIO 覆盖 ~20% 且早法一年多 | "德国受监管没人买链"(租链常态化);"Ecosia 需单独优化"(=Google 索引) |
| 法语 | **Abondance**(1998 起)/WebRankInfo 论坛 | 链接平台市场成熟(€3-10/条起,降值优先于惩罚的共识);**AIO 2026-07-22 才上线(比德晚一年多)——法国多出一年经典 SEO 窗口期**;Qwant<1% 且 2025-08 起转 Bing 索引;Piano Analytics(法企)是大企业默认,"数据主权"是采购决策词 | 法国=泛欧盟口径;Qwant 重要;<1%;GA 在法被"禁"(DPF 后是配置问题) |
| 印尼 | **cmlabs**(风向标)/DailySEO ID/ads.id 论坛 | **jasa SEO murah 廉价圈真相:Rp50 万/月 vs 正规 Rp600 万,修复烂摊子成本常超服务费**;PBN 公开叫卖+".ac.id 付费链接"商品化;Tokopedia 官方 Analisis Pencarian 工具;JNews 主题(印尼团队)统治新闻站;nulled 主题文化是真实入侵向量 | "先优化 Google"(商品发现始于 marketplace/TikTok 站内);廉价 SEO 无害;Kaskus 已死(衰而未亡仍排 SERP) |
| 印地/印度 | Google **Search Central Live Bengaluru 2026**/SaaS SEO Alliance/Telegram SEOhindi 频道 | 外包三层($99 PBN 层/Clutch 白标层/$100-300 编辑链层);**中型出版商 Discover 流量已超 Google Search,WhatsApp 次之**;聚合器占位层(JustDial 1000+ 城市/IndiaMART/Sulekha)挤掉本地词页 1——实操是"入驻聚合器+GBP";泰米尔有文字圈,泰卢固几乎全是 YouTube(蓝海) | "印度 SEO=垃圾链"(分层是价格不是国籍);把印度当单一英语市场 |
| 意大利 | **Connect.gt 论坛**(14.6k 帖)/SERP Conf Rome/Search Tech 大会/SEOZoom | guest post 15-30€(走量)/40-100€(单篇),新闻稿 6€(Press-Delivery);**Amazon.it 份额无公开数(勿引用传闻)**;意语关键词池比德法小得多;内容外包 25-80€/篇(约英语圈一半) | 直译关键词;高估关键词体量;低估本土论坛话语权 |
| 土耳其 | **r10.net**(交易中枢)/İlyas Teker/Antalya Search 'n Stuff 大会 | 外链主形态=**tanıtım yazısı**(新闻站赞助文,90₺ 垃圾层→13,500₺ 全国媒体);Trendyol 九信号(单量转化最强/content score 传 80-90+/断货即掉/标题公式 Marka+Ürün+Model+Özellik);**土语 SERP 被 UGC 碾压(Ekşi Sözlük #1/DonanımHaber/Akakçe);品牌词被 Şikayetvar 占据催生 ORM 产业** | "Yandex 26% ⇒ 必须做"(本地实操几乎没人做,看客群);TR 链接=guest post(实为 tanıtım 市场) |
| 越南 | **IDVS 论坛**(持牌)/Brands Vietnam/卖家 FB 群 | **backlink báo 产业**:22-30 省级国家级新闻域 sidebar 链,1,500-3,500 VND/条(规模化购链,话术包装成 E-E-A-T——Google 链接垃圾政策范围);Cốc Cốc 搜索份额仅 ~6% 但浏览器 ~25%("装机多用得少",价值在数据面年度报告) | Cốc Cốc 是"必优化第二引擎"(优先级低于 FB 群/Zalo);买新闻外链=白帽 |
| 泰国 | **Pantip**(真活跃)/ThaiSEOBoard(交易区)/FB 群 | 本地黑话"**หลังบ้าน(后门)=灰黑帽链网**",赌博站 hack 排名手法,被罚后恢复以年计;Pantip 帖在"รีวิว/คววรซื้อไหม"类词常年霸榜(排名占有者+声誉层双角色);Lazada 给长描述内容分、Shopee 重转化速度;TikTok 口播词被索引 | Pantip=外链来源(实为声誉/UGC 占位);低价外包安全(被灰链把持) |
| 波兰 | Planeta SEO 聚合/Senuto/Silesia SEM 大会(十几年) | WhitePress/LinkHouse 中介常态(100-1,000 zł/篇);**Allegro"Trafność"算法:参数填满且逐月更新(常新增参数,过时即掉)**;AIO 波语名 Przeglądy od AI(2025-03-26,~28.95% 单源) | 波兰=便宜买链黑帽可行(本地已转向 E-E-A-T);"只做 Allegro 就够"(实为双轨) |
| 荷兰 | **Frankwatching**(第一本营)/Marketingfacts/Yoast | 外链 €150-350/条;**一条权威 .nl 链>数百条进口链(荷语 Google 拒收批量进口链)**;NL 的 AIO 触发率信息类仅 6.43%(2025-06,远低于美,交易词暂安全);发现层:LinkedIn 14M=第 2 渠道 | "荷兰人英语好→英文内容即可"(交易发生在荷语) |

**深挖轮跨区新原则**:
24. **每市场有"本地链接市场价"**:从 $1.5(越)到 5,000€(西大媒体)——报价审计先锚本地价带,防被当作"高价值链接"的进口溢价坑。
25. **投诉/UGC 平台的声誉层占位是新兴通用模式**:土耳其 Şikayetvar、泰国 Pantip、巴西 Reclame Aqui、俄 Отзовik、日食べログ——品牌词 SERP 审计必查"本国投诉站占位"。
26. **marketplace 站内 SEO 是独立学科**(ML/Trendyol/Allegro/bol/Shopee 各有算法+工具+官方学院)——"电商 SEO"在多数市场=marketplace 内优化×官网双轨。
27. **AIO 上线时间就是市场红利窗口**:法(2026-07)比德(2025)晚一年——后上线市场多吃一年经典 SEO 收益,发布日历按各国上线日重排。

### 跨区迁移矩阵(某市场验证过的方法 → 可迁移到哪些市场;迁移后必须本地实测)

| 源方法(起源市场) | 可迁移市场 | 迁移条件 |
|---|---|---|
| 搜一搜"生态内搜索"打法(中) | 韩(Naver Blog)/俄(Dzen/TG 镜像)/日(note)/印尼(TikTok) | 市场存在封闭生态搜索入口 |
| Reclame Aqui 投诉平台=GEO 引用源(巴西,22.3%) | 德/英(Trustpilot)、美(PissedConsumer)、俄(Отзовик)、日(食べログ) | 找到本国"RA 等价物"并实测被引率 |
| 「AI 臭」密度 lint(日,28 动词×14 构文) | 全区(每语种建 slop 表:pt-BR 35 型/印尼 hiruk pikuk/波兰 humanizer-pl) | 母语者标注触发词+人类上限频率基线 |
| 快照缺口诊断(GSC regex,印度 Hinglish) | 所有混码市场(阿拉伯 franco-arabe/菲 Taglish/印尼口语) | 语言错配且排名好的页 |
| 音译规范化聚类(印度 IndicXlit) | 阿拉伯(3arabizi)/越南(无调)/土耳其(黏着后缀) | 存在罗马化/口语变体双写 |
| 微信 OG 先行+WA 归因(巴西 WhatsApp) | 印度(WhatsApp)/印尼(WA+TikTok)/日(LINE) | 超级 App 分流发现的市场 |
| 官方注册竞品链(意 P.IVA→Registro) | 瑞士(Zefix 免费)/德国(Handelsregister 付费) | 有公开企业注册 API |
| 提问式 H2+nonce 质量门(越南 t0mmy) | 全区(语言无关) | agent 产线场景 |
| SoV 取代位置的计量观(俄,官方) | 全区(韩 인용수/日 Share of AI Voice 已同构) | 引擎提供份额类指标或可采样 |
| 主权助手单独优化(法 Vibe) | 印尼(Sahabat-AI)/阿拉伯(Fanar)/韩(Wrtn) | 本土助手有独立爬虫/索引 |
| 目录=GEO 引用源(印度 JustDial) | 巴西(Apontador)/波兰(Panorama Firm)/泰(Wongnai) | AI 引擎拉取本地目录的市场 |
