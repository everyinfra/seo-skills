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

### 资源与约束四问(2026-10-12 并入,R1-5;策略适配层 [strategy-fit](strategy-fit.md) 的输入)

- **资源投入**：内容产能（篇/月，自有写手还是外包）、开发资源（专职系数或每周可投入小时）、工具账号层级（T0 仅 GSC / 一套付费 SEO 工具 / 外链+排名追踪全配）、外包预算（月额度，无则 0）——喂给 strategy-fit 资源可行性系数 R 与 pSEO 分批上限（[programmatic-seo-gates](../technical/programmatic-seo-gates.md) 每批 50-100 页须产能可复核）；工具层级同时决定 [data-source-contract](data-source-contract.md) 的降级路径。
- **风险容忍（各标高中低，分三类）**：pSEO 规模化（是否接受分批上线+闸门硬停线）、激进外链（买卖链接、大量互换链接：Google 垃圾内容政策把「为排名买卖链接」和「过度互链」列为 link spam，见 [spam policies](https://developers.google.com/search/docs/essentials/spam-policies#link-spam)，核对 2026-10-21）、站群（卫星站/PBN 是否考虑）——喂给 strategy-fit 风险系数 K；**pSEO 类标"低"=闸门 STOP 即终审，不可被用户批准放行**；激进外链与站群默认不在白帽桌面，用户主动提出才按 [site-networks](../research/site-networks.md) 光谱评级并明示风险。
- **时间窗**：硬 deadline（融资/旺季/发布会，精确到周）、可接受见效周期（4-8 周 / 一个季度 / 6 个月+）——喂给 strategy-fit 排序（窗口短于策略见效周期→标"窗口外"降位）与 pSEO 批次排期（首批上线周）；见效周期也是 forecast 三档 scenario 的判读口径。
- **业务量化目标**：目标数字+口径（如"自然收入占比 12%→18%，口径=GA4 非品牌 organic 收入/总收入"、"非品牌 demo 注册/月 +50%"）——喂给 forecast `--actual` 校准（真实流量→calibration_factor）与 scenario 选型；strategy-fit 收益区间按此口径折算，禁用厂商案例数字直接对客承诺。

## 目标市场 intake(多语言/全球站必答,2026-10-08 并入,2026-10-21 重核)

按命中的市场逐个过。每行是要问的问题;数字和依据在对应的语区门户页,门户页已逐条核对一手来源。细则见[多语言工作流](multilingual-workflow.md)市场总表。

- **俄语区**([ru.md](../markets/ru.md)):Yandex.Webmaster 是否验证、区域是否已设?Metrica 是否安装(个人数据要按 152-ФЗ 评估,GA 的取舍见门户页)?robots 对 `YandexAdditional` 的决策(写 Disallow = 退出 Алиса AI 回答,2–14 天生效)?付费推广有没有 erid 标记(自有官网介绍自家商品不算广告,见门户页 FAS 函)?Telegram 公开频道与 VK 群是否运营?商业透明层(оферта/реквизиты 等法定页)齐吗?
- **韩语区**([ko.md](../markets/ko.md)、[naver-searchadvisor.md](../technical/naver-searchadvisor.md)):Search Advisor 是否注册并验证(按 host)?robots.txt 是否返回 200(5xx 会被 Yeti 按「全部不允许」处理,本套件判 P0)?IndexNow key 是否部署?연관채널 sameAs?title ≤30、description ≤80 全角字(本套件阈值),og:description 与之一致?Naver Blog/Cafe/지식iN 是否存在?AI 引用暴露敏感页时要不要 `nosourceinfo`(只表示 Naver 不提供 AI 出处说明,不等于 noindex)?电商是否做 Coupang?收录验证:수집요청 排队,需要 1 天到数周;`site:` 与 사이트 진단 口径不同。
- **日语区**([ja.md](../markets/ja.md)):Bing WMT 是否验证(Bing 在日本约占三成,月度区间见门户页)?审计是否用全角阈值(title 32、description 120 全角字,本套件阈值;勿套英文 60/155)?内容是否过「AI 臭」密度 lint?MEO/本地:GBP + ステマ規制下的口碑披露 + 投稿週 1 回?Qiita/Zenn 是否覆盖(技术品牌)?業界ポータル NAP 是否完全一致?
- **英文(协议层)**:agent-readiness 三件套是否要做——ARD(`ai-catalog.json`)/ llms.txt / WebMCP?Cloudflare 托管 robots 是否检测(抓线上响应)?Lighthouse 的 Agentic Browsing 类别跑过吗?
- **西语**([es.md](../markets/es.md)):hreflang 结构:`es` 兜底,需要时加国家码(`es-MX` 等);`es-419` 不是 Google 支持的 hreflang 值([Google 文档](https://developers.google.com/search/docs/specialty/international/localized-versions)),只能当内容层的「拉美通用西语」概念。方言本地化而非机翻?拉美内容有显式区域信号?支付词层(OXXO/cuotas)入表?es-US 当独立市场?
- **葡语(巴西)**([pt.md](../markets/pt.md)):pt-BR 原生词表?ChatGPT/LLM 可见性是否列入优先目标(依据见门户页)?Reclame Aqui 指数/响应率/TOP 抱怨话题映射 FAQ?WhatsApp OG 先行 + wa.me 归因?CNPJ 页脚?AO90 拼写核查?
- **阿拉伯**([ar.md](../markets/ar.md)):`dir="rtl"` 全链?MSA 骨架 + 方言层策略?品类×语域矩阵定了?文化日历闸门(Ramadan 弧/发布窗口)?合规词表预审(GAMR/TDRA)?GEO 测量协议(50 查询 × 14 天重测,本套件口径)。
- **法语**([fr.md](../markets/fr.md)):fr 变体分离(fr-FR/fr-CA/fr-BE)?魁北克 Bill 96 检查(等效可见性/OQLF)与魁北克词汇表?引用面板单独跑?
- **德语区**([de.md](../markets/de.md)):Sie/du 按国别定了?Ansprache/Tonalität 两字段 + 跨触点一致?分国别取数(禁合并 DACH)?GA4 在 Consent Mode v2 下使用时,GSC 基准与 consent rate 是否并列?瑞士 CHF + 子目录结构?
- **印尼**([id.md](../markets/id.md)):baku/gaul 双轨?移动优先:按本站 GSC 设备拆分判断(旧稿「移动 >82%」未核,已删)?视频/社媒资产优先于长文?品牌词 = sameAs + FAQ 实体页?slow-4G 基线测 LCP(`field_data.py`)?「hiruk pikuk」类 slop 禁用表?
- **印地/印度**([hi.md](../markets/hi.md)):GSC regex 跑过 Hinglish 快照缺口?目录(JustDial/IndiaMART)完整性?语音助词词库?超 App(JioHotstar)引用面?
- **意大利**([it.md](../markets/it.md)):P.IVA → 竞品链用过?Wikipedia 意语词条存在?评论策略按本地习惯做了吗?
- **土耳其**([tr.md](../markets/tr.md)):本地实测 Yandex 份额(口径冲突)?Yazeka 引用抽查?Zemberek 词干工作流?Trendyol 店铺?
- **越南**([vi.md](../markets/vi.md)):提问式 H2 ≥50%(本套件口径)?无调变体混入?Coc Cốc `site:` 收录?.vn 外链?
- **泰国**([th.md](../markets/th.md)):`Intl.Segmenter("th")` 分词 + grapheme 计数?Wongnai/Pantip 本地信号?PDPA(医疗)?
- **波兰**([pl.md](../markets/pl.md)):Bing WMT + IndexNow(Bing 桌面份额见门户页)?URL 转写?品牌引用按引擎分列?
- **荷兰**([nl.md](../markets/nl.md)):je/u tone 双轨?nl-BE 误标检测?[INVULLEN] 占位制?KvK 一致性?
- 逐市场分别评分还是只要一个总分?(本套件默认:逐市场分开)
- **外包/代理红旗**(只列红旗,不列价格:旧稿的各国单价没有一手来源,已删;「外链价带表」已从 backlink-directory.md 删除。各市场的本地目录与榜单见 [backlink-directory.md](../research/backlink-directory.md) 第四节「本地目录与榜单（按市场）」):印尼「garansi halaman 1」保首页话术、印度「排 'SEO India' 词的机构」、泰国低价灰链。买链接以换排名违反 Google link spam 政策(见上),报价单里出现「包发外链」就按风险项处理。

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

## EU AI Act Article 50 合规卡(面向 EU 的内容/营销任务必过;核对 2026-10-21)

来源:欧盟委员会 [Article 50 FAQ](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act)(页面日期 2026-07-24)。这是合规线索,不是法律意见。

- 适用日:Article 50 自 **2026-08-02** 起适用。仅对 2026-08-02 前已投放市场的 AI 系统,Article 50(2)「标记与可检测」义务有宽限,提供者须在 **2026-12-02** 起遵守。2026-08-02 前生成的内容不必追溯加标签,委员会鼓励尽量加。
- 罚款:最高 **1500 万欧元或上一财年全球营业额 3%**;SME 和小型中市值公司按比例处理。主要由各国市场监督机关执法。
- 谁承担什么:**提供者**(开发或以自有名义投放 AI 系统的一方)负责机器可读标记和可检测(50(2))。**使用者(deployer)**——内容团队多半是这一类——负责:公开发布的 deepfake 要清晰披露;为向公众说明「公共利益事项」而发布的 AI 生成或操纵文本要清晰标注(50(4))。
- deepfake 披露:最晚在第一次接触时,用看得见或听得见的标签,不需要特殊工具。使用者**不能**只靠提供者嵌入的机器可读标记来履行披露义务。明显属于艺术、创意、讽刺、虚构的作品,披露可以采用不妨碍作品展示的方式。
- 文本豁免:经人工审核或编辑控制的文本不必标注。人工审核 = 具备相关知识和专业判断的自然人对内容实质的认真检查;只做拼写、语法这类形式检查**不算**。编辑责任 = 有人对发布(含审核或编辑控制)承担最终法律责任。
- 自愿工具:《AI 生成内容透明度行为守则》(Code of Practice)可帮助证明遵守 50(2)、(4)、(5);不加入的一方要用别的方式证明,可能被索取更多信息。
- 旧稿里的「C2PA 为 presumption of compliance」「证书审批预留 2–4 周」「执法优先级」「高风险 3500 万/7%」找不到一手来源,已删(3500 万/7% 对应的是禁止类行为,不是 Article 50)。

## 审计与分析测量层增补(digital-marketing-pro 深读 2026-10-09b)

来源同 [agent-readiness](../technical/agent-readiness.md) 同日节的 164 技能仓库(digital-marketing-pro 深读)。**性质:第三方技能仓库的做法**——下面「快照漂移」「各审计门与阈值」两节里的阈值、权重、百分比是那个仓库的口径,不是搜索引擎规则,也没有逐项验证;采用前先做 [data-onboarding.md](data-onboarding.md) 的检查清单、用自己站点的数据校准。官方事实(GSC/Bing/GA4/Merchant Center)已在 2026-10-21 对官方页面重核,并附链接。

### AI 表面测量地图(监控/审计 intake 必问:每表面一列,单位各自报,禁混算)

| 表面 | 第一方可见性指标 | 点击/流量指标 | 不存在项 |
|---|---|---|---|
| Google AIO+AI Mode | GSC「生成式 AI 效果报告」:impressions 按 page/country/date/device([帮助页](https://support.google.com/webmasters/answer/16984139)) | **GA4 Organic Search 内,不可分** | AI 报告内的 clicks/CTR/queries(帮助页只列展示数) |
| Copilot/Bing 及伙伴 AI | Bing WMT AI Performance:citations、grounding queries([2026-02-10 公测](https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/));Intents/Topics/Citation Share/Compare([2026-06-16 起 preview](https://blogs.bing.com/search/2026/6/New-AI-Visibility-Insights-in-Bing-Webmaster-Tools-Intents-Topics-Citation-Share-Compare/)) | GA4 AI Assistant 通道 | 排名、权威、重要性(Bing 帮助页写明该报告只显示被引用次数,不衡量这些) |
| Google Shopping(AI Mode/Gemini app) | Merchant Center AI performance insights([帮助页](https://support.google.com/merchants/answer/17200695):目前只对澳大利亚、加拿大、印度、新西兰和美国的 Merchant Center 账户、英文查询开放,先在账户里确认) | MC/Ads 转化报表 | 逐查询引用明细 |
| ChatGPT/Claude/Perplexity/Gemini app | **无第一方引用报告**——只有合成探针,标注为探针 | GA4 AI Assistant 通道 | 一切官方引用/展示数 |

**三源对账纪律**:探针(引擎*可能*怎么说)/GSC(实际展示了什么)/GA4(实际点来了多少)——健康项目三者同涨;两两发散即诊断信号:GSC≫探针→查询集太窄要扩;探针有而 GSC 少→主题搜索量低,转移 AEO 精力。探针分与第一方数永远分列两列各自标源标日期,背离(如 Citation Share 降而探针分升)按 finding 上报,不许平均掉。

### GSC 生成式 AI 效果报告 事实卡(核对 2026-10-21)

来源:[Search Central 博文 2026-06-03](https://developers.google.com/search/blog)、[帮助页](https://support.google.com/webmasters/answer/16984139)、[multimodal 博文 2026-09-24](https://developers.google.com/search/blog/2026/09/web-multimodal-in-sc)。

- 2026-06-03 公布,先给一部分站点;**2026-08-31 起对全球所有站点开放**。Search 报告含 AI Overviews 和 AI Mode;Discover 另有一份独立报告。
- 默认只给**展示(impressions)**;维度:页面、国家、日期、设备;日期粒度含小时、天、周、月。帮助页只写了导出按钮(图表与表格),没写 API。**2026-10-21 在官方页面找不到 API 说明;自动化前先复核 Search Console API 更新记录。**
- 同一站点在一次生成式 AI 结果里出现多个链接,图表按属性只算一次展示;按页面分组时按页面聚合。和经典结果的展示口径不同,**不要一比一对比**(本套件口径)。
- **2026-09-24 起**,效果报告和这份报告都多了「Web: multimodal」搜索类型(Lens、Circle to Search、上传图片、Chrome 右键搜图)。官方没说明历史数据是否回填,所以 9 月前后做环比,先分别按「Web: text-based」和「Web: multimodal」导出再比(本套件口径)。
- 已知记录:2026-08-13 至 08-17 有日志错误,生成式 AI 报告的展示偏低([数据异常记录](https://support.google.com/webmasters/answer/6211453))。
- 属性看不到报告:记录原因和首次见到数据的日期,作为后续环比的真基线。
- 旧稿里的「数据回填自 2026-05-18」「UK 先行」「AIO 展示 = 被用作 grounding source」找不到一手来源,已删。

### GA4 "AI Assistant" 通道盲区(2026-05-13 新增默认通道;[发布说明](https://support.google.com/analytics/answer/9164320)、[默认通道定义](https://support.google.com/analytics/answer/9756891))

- 规则:`medium` 精确匹配 `ai-assistant`;覆盖 ChatGPT/Gemini/Claude/Deepseek/Copilot/Grok 等推荐流量;**明确排除 Google 自家 AIO 与 AI Mode(归 Organic Search,GA4 无任何维度可拆)**;
- 三禁令:**不得把 AI Assistant 报成"全部 AI 流量"**(仅非 Google 助手);**不得从 GA4 推算"AIO 占 organic 的份额"**(无第一方指标,估计当数据=编造);AIO 展示涨而 organic 点击跌时,两数并列+明说 GA4 无法归因该点击;
- onboarding 检查:老属性等 backfill;自定义报表加该通道为 AEO 项目主 KPI;禁并入 Organic/Direct 旧模板。

### 快照漂移对比纪律(seo-drift 类分析)

- 前置:**两快照必须同源**(GSC 配 Ahrefs=无效);每输入 ≥50 行;join 键(query/page/url)不得重复;noise 默认 5%,**YMYL 行业用 10%**(过滤质量评估员指南波动);
- 六分类:growth / decline / **reshuffle**(指标反向大动,如展示涨位置跌)/ stable / new / lost;**reshuffle 飙升=AI Mode 意图重加权的前导指标,下季度才会显化为涨跌,勿抢跑反应**;>40% decline→跑内容+技术侧诊断;>20% reshuffle→AEO 意图对齐;>30% growth→内容放大;
- position 特殊(低=好,方向自动反转);**position 噪声大于 impression/click**(8↔12 位摆动产生 ±30% 无意义摆动),诊断优先信展示/点击;GSC 数据滞后 ~3 天(取数窗口止于 3 天前);
- **Core Update 纪律:rollout 期间不跑**,等 dashboard 标"rollout complete"+7-14 天沉淀;triage 跑两次——day-after(冲击态)与 14 天后(沉淀态),两者常不一致,以 14 天为准;AI 报告无点击,只能做 impressions drift。

### 算法更新状态卡(2026-10-21 按 Status Dashboard 重核;下次约 2026-12 复核)

来源:[Google Search Status Dashboard · Ranking 历史](https://status.search.google.com/products/rGHU1u87FJnkP6W2GwMi/history)。

- 2026 年已列事件:Discover update 02-05(持续约 21 天);**spam update 03-24**;**core update 03-27**(约 12 天);**core update 05-21**(约 12 天);**spam update 06-24**(约 2 天);**spam update 08-18**(约 2 天 16 小时);**spam update 09-24**(约 13 天 16 小时,已完成)。
- 最近一次 core update 是 2026-05-21;**2026-09 和 2026-10 没有 core update**——有些 SEO 博客误报,只按 Dashboard 所列归因。
- core update 重新衡量质量和政策信号,不是技术信号变更:更新窗口会*暴露*既有技术债(抓取预算浪费、断 canonical 链、soft-404、JS 渲染孤儿路由),但技术修复是背景工作,不是解药。更新窗口内的排名波动,先分方向(全站 vs 单板块 vs 单模板;根因不同),不做反应式改动,内容和 E-E-A-T 侧同步审。

### 各审计门与阈值速查(对应通用/technical/monitoring intake 的量化依据)

- **全站 SEO 审计四门**:爬取覆盖 ≥90% sitemap URL;6 维度评分齐(technical/on-page/content/E-E-A-T/link/local-if-applicable);每条 high-impact 发现带 owner+工时估算;Core Update 窗口旗标+PLAN 内"等 7-14 天再动"提示;
- **>10K 页站点禁 URL 级审计**→按模板聚类每模板抽一代表页泛化;E-E-A-T 评分是判断非测量(资深审计者间差 ~1 分,按行业校准:作者信号 7/10 对 SaaS 优秀、对 YMYL 健康出版仅及格);
- **异常扫描**:灵敏度 strict 1.5σ / normal 2σ / relaxed 3σ;严重级 critical(追踪断裂/CPA 3×基线/超支 >20%/送达率 <80%)、warning(流量 -30%/CTR -40%,24 小时内查)、info;**诊断次序固定:先验数据(标签/consent/过滤器变更、平台故障)→再外因(算法/季节/竞对/平台政策)→后内因(部署/URL/内容/活动)**;近 14 天执行史交叉定位原因;
- **排名监控**(digital-marketing-pro 口径):告警默认 >5 位跌幅,分级 minor 3-5 / major 5-10 / critical >10 或 P1→P2;丢失 Featured Snippet 或 AIO 引用至少 major;**GSC 无 AIO 引用导出,feature 追踪里的 AIO 信号只是"出现+被引"二元观察**,评分化 AI 可见性与真实 impressions 分走探针/GSC 报告;50-150 个高价值词 > 2000 个噪声词;
- **内容衰减扫描**:默认阈值 3 个月流量 -15% / 主词掉 10+ 位 / 18 个月未实质更新 / 转化率 -20%;分层 Critical 前 10%(立即)→High 20%(2 周)→Medium 30%(1-2 月)→Monitor;按**可恢复收入**(峰值-现值×恢复概率)排序而非按流量损失排序;refresh 恢复期 2-4 个月(60-80% 为示意值非实测),30 天勿判成败;**refresh>delete**(带外链的衰减页价值大于 404+redirect);**AI 引用流失的修复=实体一致性刷新(schema/作者履历/知识图谱)而非内容重写**;Core Update 窗口内勿刷新(归因会被算法重排污染);
- **归因建模**:GA4 的归因模型只剩数据驱动和最后点击(first click、linear、time decay、position-based 自 2023-11 起不可用,[GA 帮助](https://support.google.com/analytics/answer/10596865),核对 2026-10-21),其他 credit 规则须在 warehouse/BI 层建模;lookback 1.5-2× 平均销售周期(click 与 view 窗口分开);渠道拆分必须含 AI Assistant 通道防 AI 来源误入 Referral/Direct;
- **SOV**:四维默认权重 organic 35 / paid 25 / social 25 / AI 15(B2B SaaS 可上调 organic+AI);organic 可见度按**本站自己的分段 CTR**(`gsc_mining.py`、`question_align.py` 报告头部列出各排名段 CTR)加权;旧稿的固定曲线(位 1=100%、位 2=65%……)没有一手来源,已删,第三方 CTR 基准从 7% 到 28% 都有,不当通用基准;社交情感加权 pos 1.5×/neu 1.0×/neg 0.5×,原始与情感加权双报(高量差情感=争议非强势);
- **关键词研究**:任何 provider 的搜索量都是估算,不同工具的数字不同,用区间不用点值并写明来源工具;KD 是启发式非测量(垂直权威小站可赢 KD-70);**intent 优先于 volume**("buy X" 200/mo > "what is X" 5000/mo);≥20 个原始词再交聚类;**勿直接聚类原始 GSC 导出**(同查询长尾变体会并成巨型簇);AI 搜索改写下真实点击查询可能与 seed 不同,以 GSC 实际查询为准;
- **聚类四门**:cannibalisation(无两簇同 pillar+intent)/ orphan(多词簇 ≥1 spoke)/ coverage(≥80% seed 入簇)/ anchor 多样性(每多词簇 ≥2 锚文本变体);SERP-overlap 聚类严格优于词法聚类;fragmentation(pillar-only >50%)是软信号→先降 overlap 阈值 0.4→0.3;
- **策略规划(4 支柱 dispatcher 模式)**:technical / content / topical / AI search 打分,**最弱支柱=下季度 lead theme**(强制聚焦,其余为支持工作);专家输出新鲜度窗口 30 天(高速行业缩至 14 天,慢行业放宽 60);缺的专家默认列为 Phase 0 工作而非自动补跑(防 API 花费);YMYL 手动加第 5 支柱 E-E-A-T;连续两季同支柱 lead=工作未奏效(升级处理)或评分错误(用当前数据重校)。

### 通用/technical intake 增补条目(并入上文各节提问)

- 品牌实体资产:Wikidata 条目存在?Knowledge Panel 认领?Wikipedia 词条?(决定实体一致性审计入口)
- GSC 属性是否见 AI Performance 报告?GA4 是否已认 AI Assistant 通道?
- AI 可见性探针的查询集(10-25 条,按 branded/category/comparison/best-of/problem-solution 分型)与 ≥2 竞对是否已定?——该审计最低输入=品牌名+域名
- 做漂移对比时:两快照是否同源同口径?窗口是否重叠?行数是否 ≥50?

## 检查清单(intake 完成前)

| 检查什么 | 怎么查 | 通过 / 失败判据 |
|---|---|---|
| 目标市场已定且在 18 个之内 | `python3 -c "import json; print(sorted(json.load(open('scripts/markets.json'))['markets']))"`(在 `skills/seo-suite/` 下跑) | 用户给的市场码在列表里;不在就按「基线」处理并告知 |
| 数据源与 tier 已声明 | `python3 scripts/doctor.py --wizard` | 报告开头写明 tier(T0–T3)与缺的数据源;缺数据走 [data-source-contract.md](data-source-contract.md) 的降级列 |
| 资源四问有答案 | 看上文「资源与约束四问」四项 | 四项都有数(产能、风险三类、时间窗、业务目标口径);缺项在报告里写「未提供」,不替用户假设 |
| GSC 报告可见性 | 问用户:属性里有没有「生成式 AI 效果报告」?首次见到数据日期? | 有答案并记录日期;没有就记原因 |
| 展示数据时间窗 | 对照 [Search Console 数据异常记录](https://support.google.com/webmasters/answer/6211453) | 对比期不跨 2025-05-13 至 2026-04-27;跨了只比点击 |
| 欧盟内容任务过合规卡 | 对照上文 EU AI Act 卡 | 写明自己是提供者还是使用者;AI 文本是否经人工审核/编辑控制;是否含 deepfake |
| 算法事件只按 Dashboard | 打开上文 Dashboard 链接 | 归因的更新名与日期都在 Dashboard 列表里 |
