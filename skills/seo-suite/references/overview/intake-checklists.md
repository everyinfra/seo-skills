# Intake Checklists

## 通用 intake

- 目标域名 / 页面 URL
- 站点类型
- 目标国家 / 语言
- 核心目标关键词或主题
- 当前主要目标：排名 / 流量 / CTR / 转化 / AI 引用 / 监控
- 当前已知问题
- 近期是否改版、迁移、换模板、改 URL、改 CMS
- 有哪些数据：Search Console、GA4、排名工具、外链工具、日志、爬虫结果

## 目标市场 intake(多语言/全球站必答,2026-10-08 并入)

按命中的市场逐个过(细则见[多语言工作流](multilingual-workflow.md)市场总表):

- **俄语区**:Yandex.Webmaster 是否验证+区域已设?Metrica 是否安装(GA 因 152-ФЗ 不合规)?robots 对 `YandexAdditional` 的决策(允许=进 Neuro/Alice)?付费投放的 erid 标记?**Telegram 公开频道(镜像 SEO)与 VK 群是否运营?商业透明层(оферта/реквизиты 等 6 类法定页)齐吗?**
- **韩语区**:Search Advisor 是否注册+验证(canonical 精确;**robots.txt 无 5xx/HTML 陷阱——Yeti 5xx=全站封禁**)?og:image 三条件?IndexNow key 部署?연관채널 sameAs(치지직/당근 等韩域)?description ≤80 全角字且 og:description 一致?Naver Blog/Cafe/지식iN 存在吗(AI Briefing 只引 Naver 生态;**투트랙:生态内+自有域**)?有 AI 引用暴露敏感页要用 `nosourceinfo` 吗?电商是否做 Coupang?**收录验证窗口设 2–4 周(수집요청是优先级队列)**
- **日语区**:Bing WMT 是否验证(Bing 28–33% 份额)?**审计是否用全角阈值(title 32/desc 120/正文 300 全角字,勿套英文 60/160)?内容是否过「AI 臭」密度 lint?**MEO/本地:GBP+ステマ規制内口碑+投稿週 1 回?Qiita/Zenn 是否覆盖(技术品牌)?業界ポータル NAP 是否完全一致?
- **英文(协议层)**:agent-readiness 三件套是否要做——ARD(`ai-catalog.json`)/llms.txt/WebMCP?Cloudflare 托管 robots 是否检测(抓线上响应)?Lighthouse `AGENTIC_BROWSING` 跑过吗?
- **西语**:es-ES+es-419 结构决策?方言本地化(非机翻)?
- **葡语(巴西)**:pt-BR 原生词表?ChatGPT/LLM 可见性是否列入优先目标(全球最强采用市场)?
- **阿拉伯**:`dir="rtl"` 全链?MSA 骨架+方言层策略?
- **法语**:fr 变体分离(fr-FR/fr-CA/fr-BE)?魁北克 Bill 96 合规?
- **德语**:Sie/du 按国别定了?Consent Mode v2 是否影响测量计划?
- **印尼**:baku/gaul 双轨?移动优先(>82% 移动流量)?
- **西语**:es 兜底+es-419+国码全簇回链(两说兼容)?拉美内容有显式区域信号?支付词层(OXXO/cuotas)入表?es-US 当独立市场?
- **葡语(巴西)**:Reclame Aqui 指数/响应率/TOP 抱怨话题映射 FAQ?WhatsApp OG 先行+wa.me 归因?委员会注册号+CNPJ 页脚?AO90 拼写核查?
- **阿拉伯**:品类×语域矩阵定了?文化日历闸门(Ramadan 弧/发布窗口)?合规词表预审(GAMR/TDRA)?GEO 测量用 50 查询×14 天重测?
- **德语区**:Ansprache/Tonalität 两字段+跨触点一致性?分国别取数(禁合并 DACH)?GSC 基准+consent rate 并列?瑞士 CHF+子目录结构?
- **法语**:Vibe 引用面板单独跑?Bill 96 检查(等效可见性/OQLF)?魁北克词汇表应用?塞内加尔等 Bing Places?
- **印尼**:视频/社媒资产优先于长文?品牌词=sameAs+FAQ 实体页?slow-4G 基线测 LCP?"hiruk pikuk"类 slop 禁用表?
- **印地/印度**:GSC regex 跑过 Hinglish 快照缺口?目录(JustDial/IndiaMART)完整性?语音助词词库?超 App(JioHotstar)引用面?
- **意大利**:P.IVA→竞品链用过?Wikipedia 意语词条存在?评论策略按"4 星>5 星"本地化?
- **土耳其**:本地实测 Yandex 份额(口径冲突)?Yazeka 引用抽查?Zemberek 词干工作流?Trendyol 店铺?
- **越南**:提问式 H2≥50%?无调变体混入?Coc Cốc site: 收录?.vn 外链?
- **泰国**:`Intl.Segmenter("th")` 分词+grapheme 计数?Wongnai/Pantip 本地信号?PDPA(医疗)?
- **波兰**:Bing WMT+IndexNow(桌面 13.3%)?URL 转写?品牌引用按引擎分列?
- **荷兰**:je/u tone 双轨?nl-BE 误标检测?[INVULLEN] 占位制?KvK 一致性?
- 逐市场分别评分还是只要一个总分?(本套件默认:逐市场分开)
- **外包/代理价格锚(深挖轮,防进口溢价)**:内容写作——意 25-80€/篇(约英语圈一半)/西 0.02-0.10€/词/墨 0.6 MXN/词;SEO 月费——日 10-50 万円(SEO)vs 1-5 万円(MEO)/波 1,490-5,250 zł/月;外链单条见 backlink-directory 市场价带表;**廉价服务红旗:印尼"garansi halaman 1 保首页"话术、印度"排 'SEO India' 词的机构"、泰国低价灰链**

## research intake

- 想抢哪些主题或词
- 是新市场还是已有市场扩展
- 主要竞争对手是谁
- 是做内容规划还是解释现有 SERP

## content intake
- 目标受众 persona 是否已有证据(访谈/评论/工单)？没有则先做 persona 推导再写内容(方法见关键词文件的 persona 层)
- 多市场站:persona 是否按市场分开(各市场的本地信任信号与词汇不同;信号源按市场替换)

- 页面类型：博客、落地页、产品页、分类页、FAQ、比较页
- 主要 query / intent
- 是否已有初稿
- 目标是传统 SEO 还是 AI 引用，或两者都要

## technical intake

- 问题范围：单页、目录、整站
- 是否有 robots / sitemap / canonical / redirects / schema / CWV 证据
- 是否允许看代码、模板或渲染后 DOM
- 是否有近期技术改动

## monitoring intake

- 关注对象：关键词、页面、目录、整站、竞争对手
- 观察周期：日报、周报、月报
- 告警阈值：排名下降、流量下降、索引异常、外链流失等
- 是否需要 stakeholder-friendly 报告

## EU AI Act Article 50 合规卡(indranilbanerjee 精读,百仓深扫;面向 EU 的内容/营销任务必过)

- 透明义务适用 **2026-08-02**(GPAI 2025-08-02;高风险 2027-08-02);无最低投放门槛,广告不豁免;
- 罚 **EUR 1500 万或全球营业额 3%**(高风险 3500 万/7%);
- AI 生成内容须机器可读标记,**C2PA 为"presumption of compliance"路径**(证书审批预留 2-4 周,四家认可机构);
- deepfake 须可见披露(角落小字明确不足);执法优先级:deepfake>政治/健康>无溯源 AI 内容;
- "实质性 AI 操纵"=改变意义/身份/事实主张(常规调色不算);编辑责任豁免需有否决权的署名人类+留痕评审。

## 审计与分析测量层增补(digital-marketing-pro 深读 2026-10-09b)

来源同 [agent-readiness](../technical/agent-readiness.md) 同日节的 164 技能仓库(aeo-audit/gsc-ai-performance/analytics-insights/seo-drift/seo-audit/anomaly-scan/rank-monitor/content-decay-scan/keyword-cluster/seo-plan 等);EU AI Act 卡与 merchant feed 前批已收,不重复。

### AI 表面测量地图(监控/审计 intake 必问:每表面一列,单位各自报,禁混算)

| 表面 | 第一方可见性指标 | 点击/流量指标 | 不存在项 |
|---|---|---|---|
| Google AIO+AI Mode | GSC generative AI 报告:impressions 按 page/country/date/device | **GA4 Organic Search 内,不可分** | AI 报告内的 clicks/CTR/queries |
| Copilot/Bing 及伙伴 AI | Bing WMT AI Performance:citations、grounding queries、Intents/Topics/Citation Share/Compare(2026-06-16 起 preview) | GA4 AI Assistant 通道 | 竞对域名、流量份额(Bing 明说不提供) |
| Google Shopping(AI Mode/Gemini app) | Merchant Center AI performance insights(品牌 share of voice,US/CA/AU/IN/NZ 滚出中,先账户确认) | MC/Ads 转化报表 | 逐查询引用明细 |
| ChatGPT/Claude/Perplexity/Gemini app | **无第一方引用报告**——只有合成探针,标注为探针 | GA4 AI Assistant 通道 | 一切官方引用/展示数 |

**三源对账纪律**:探针(引擎*可能*怎么说)/GSC(实际展示了什么)/GA4(实际点来了多少)——健康项目三者同涨;两两发散即诊断信号:GSC≫探针→查询集太窄要扩;探针有而 GSC 少→主题搜索量低,转移 AEO 精力。探针分与第一方数永远分列两列各自标源标日期,背离(如 Citation Share 降而探针分升)按 finding 上报,不许平均掉。

### GSC AI Performance Report 事实卡(2026-06-03 上线)

- 合并 AIO+AI Mode 单一报告;数据回填自 **2026-05-18**;**2026-08-31 起全球所有站**;UK 先行;
- **只有 impressions,无 clicks/CTR/queries**;维度 Pages/Countries/Dates/Devices;**无 API(截至 2026-07 检查,UI+CSV 导出为主,自动化前先复核 release notes)**;
- **2026-09 multimodal 过滤器(Lens/Circle to Search/图片上传)= 统计口径断点**:这些 impressions 是新开始计数的,报告 9 月环比跳升前先排除 multimodal 重跑对比——口径变化≠可见性增长;
- AIO 的"impression"=被用作 grounding source,比 10 蓝链出现门槛更严,**禁与经典 SERP impressions 一比一对比**;
- 属性看不到报告=发现而非回归:记录原因(AI 展示过少/被排除出 generative features);
- intake 新问:GSC 属性是否见该报告?首次见数据的日期(做后续环比的真基线)。

### GA4 "AI Assistant" 通道盲区(2026-05-13 新增默认通道组)

- 规则:`medium` 精确匹配 `ai-assistant`;覆盖 ChatGPT/Gemini/Claude/Deepseek/Copilot/Grok 等推荐流量;**明确排除 Google 自家 AIO 与 AI Mode(归 Organic Search,GA4 无任何维度可拆)**;
- 三禁令:**不得把 AI Assistant 报成"全部 AI 流量"**(仅非 Google 助手);**不得从 GA4 推算"AIO 占 organic 的份额"**(无第一方指标,估计当数据=编造);AIO 展示涨而 organic 点击跌时,两数并列+明说 GA4 无法归因该点击;
- onboarding 检查:老属性等 backfill;自定义报表加该通道为 AEO 项目主 KPI;禁并入 Organic/Direct 旧模板。

### 快照漂移对比纪律(seo-drift 类分析)

- 前置:**两快照必须同源**(GSC 配 Ahrefs=无效);每输入 ≥50 行;join 键(query/page/url)不得重复;noise 默认 5%,**YMYL 行业用 10%**(过滤质量评估员指南波动);
- 六分类:growth / decline / **reshuffle**(指标反向大动,如展示涨位置跌)/ stable / new / lost;**reshuffle 飙升=AI Mode 意图重加权的前导指标,下季度才会显化为涨跌,勿抢跑反应**;>40% decline→跑内容+技术侧诊断;>20% reshuffle→AEO 意图对齐;>30% growth→内容放大;
- position 特殊(低=好,方向自动反转);**position 噪声大于 impression/click**(8↔12 位摆动产生 ±30% 无意义摆动),诊断优先信展示/点击;GSC 数据滞后 ~3 天(取数窗口止于 3 天前);
- **Core Update 纪律:rollout 期间不跑**,等 dashboard 标"rollout complete"+7-14 天沉淀;triage 跑两次——day-after(冲击态)与 14 天后(沉淀态),两者常不一致,以 14 天为准;AI 报告无点击,只能做 impressions drift。

### 算法更新状态卡(2026-10-04 时效,约 2026-12 复核)

- 最近 core:**2026-05-21 开始(~12 天完成)**;此后仅 spam 更新:2026-08(18-21)、2026-09(24 起,当时未标完成);
- **2026-09 无 core update——多家 SEO 博客误报;只按 Google Search Status Dashboard 所列归因**;
- core=质量/政策再加权而非技术信号变更:更新窗口会*暴露*既有技术债(爬虫预算浪费/断 canonical 链/soft-404/JS 渲染孤儿路由放大伤害),但技术修复是背景工作不是解药——更新窗口内的排名波动诊断先分方向(site-wide vs 单板块 vs 单模板,root cause 完全不同),不做反应式改动,内容/E-E-A-T 侧同步审。

### 各审计门与阈值速查(对应通用/technical/monitoring intake 的量化依据)

- **全站 SEO 审计四门**:爬取覆盖 ≥90% sitemap URL;6 维度评分齐(technical/on-page/content/E-E-A-T/link/local-if-applicable);每条 high-impact 发现带 owner+工时估算;Core Update 窗口旗标+PLAN 内"等 7-14 天再动"提示;
- **>10K 页站点禁 URL 级审计**→按模板聚类每模板抽一代表页泛化;E-E-A-T 评分是判断非测量(资深审计者间差 ~1 分,按行业校准:作者信号 7/10 对 SaaS 优秀、对 YMYL 健康出版仅及格);
- **异常扫描**:灵敏度 strict 1.5σ / normal 2σ / relaxed 3σ;严重级 critical(追踪断裂/CPA 3×基线/超支 >20%/送达率 <80%)、warning(流量 -30%/CTR -40%,24 小时内查)、info;**诊断次序固定:先验数据(标签/consent/过滤器变更、平台故障)→再外因(算法/季节/竞对/平台政策)→后内因(部署/URL/内容/活动)**;近 14 天执行史交叉定位原因;
- **排名监控**:告警默认 >5 位跌幅,分级 minor 3-5 / major 5-10 / critical >10 或 P1→P2;丢失 Featured Snippet 或 AIO 引用至少 major;**GSC 无 AIO 引用导出,feature 追踪里的 AIO 信号只是"出现+被引"二元观察**,评分化 AI 可见性与真实 impressions 分走探针/GSC 报告;50-150 个高价值词 > 2000 个噪声词;
- **内容衰减扫描**:默认阈值 3 个月流量 -15% / 主词掉 10+ 位 / 18 个月未实质更新 / 转化率 -20%;分层 Critical 前 10%(立即)→High 20%(2 周)→Medium 30%(1-2 月)→Monitor;按**可恢复收入**(峰值-现值×恢复概率)排序而非按流量损失排序;refresh 恢复期 2-4 个月(60-80% 为示意值非实测),30 天勿判成败;**refresh>delete**(带外链的衰减页价值大于 404+redirect);**AI 引用流失的修复=实体一致性刷新(schema/作者履历/知识图谱)而非内容重写**;Core Update 窗口内勿刷新(归因会被算法重排污染);
- **归因建模**:GA4 仅 data-driven 与 last-click 可配(linear/time-decay/position 菜单 2023 已删),其他 credit 规则须在 warehouse/BI 层建模;lookback 1.5-2× 平均销售周期(click 与 view 窗口分开);渠道拆分必须含 AI Assistant 通道防 AI 来源误入 Referral/Direct;
- **SOV**:四维默认权重 organic 35 / paid 25 / social 25 / AI 15(B2B SaaS 可上调 organic+AI);organic 可见度按 CTR 模型:位 1=100%/2=65%/3=45%/4=30%/5=22%/10=10%/**P2+=0%**,按搜索量加权;社交情感加权 pos 1.5×/neu 1.0×/neg 0.5×,原始与情感加权双报(高量差情感=争议非强势);
- **关键词研究**:任何 provider 的搜索量是估算,互相差 20-50%,用区间不用点值;KD 是启发式非测量(垂直权威小站可赢 KD-70);**intent 优先于 volume**("buy X" 200/mo > "what is X" 5000/mo);≥20 个原始词再交聚类;**勿直接聚类原始 GSC 导出**(同查询长尾变体会并成巨型簇);AI 搜索改写下真实点击查询可能与 seed 不同,以 GSC 实际查询为准;
- **聚类四门**:cannibalisation(无两簇同 pillar+intent)/ orphan(多词簇 ≥1 spoke)/ coverage(≥80% seed 入簇)/ anchor 多样性(每多词簇 ≥2 锚文本变体);SERP-overlap 聚类严格优于词法聚类;fragmentation(pillar-only >50%)是软信号→先降 overlap 阈值 0.4→0.3;
- **策略规划(4 支柱 dispatcher 模式)**:technical / content / topical / AI search 打分,**最弱支柱=下季度 lead theme**(强制聚焦,其余为支持工作);专家输出新鲜度窗口 30 天(高速行业缩至 14 天,慢行业放宽 60);缺的专家默认列为 Phase 0 工作而非自动补跑(防 API 花费);YMYL 手动加第 5 支柱 E-E-A-T;连续两季同支柱 lead=工作未奏效(升级处理)或评分错误(用当前数据重校)。

### 通用/technical intake 增补条目(并入上文各节提问)

- 品牌实体资产:Wikidata 条目存在?Knowledge Panel 认领?Wikipedia 词条?(决定实体一致性审计入口)
- GSC 属性是否见 AI Performance 报告?GA4 是否已认 AI Assistant 通道?
- AI 可见性探针的查询集(10-25 条,按 branded/category/comparison/best-of/problem-solution 分型)与 ≥2 竞对是否已定?——该审计最低输入=品牌名+域名
- 做漂移对比时:两快照是否同源同口径?窗口是否重叠?行数是否 ≥50?
