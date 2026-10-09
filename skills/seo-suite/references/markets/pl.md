# Rynek Polski(pl 专项)

> 语言市场文件:波兰语。断言半衰期 6-12 个月;2026-10-09 增量研究轮成文,波语一手检索为主(StatCounter PL/OBTK 银行 AI 研究/Gemius/Promptowy/WhitePress/vSprint/Vinseo 等)。基线见 overview/multilingual-workflow.md 波兰段与 scripts/markets.json `pl` 键;本文件为市场深潜层,三处互为引用。

## 〇、快速诊断入口(陌生项目 60 分钟路径)

1. `site:domena` 波语页抽查:变音字母完整(ą/ę/ł)?标题 sentence case?URL slug 是否 ASCII 转写?(→ 三)
2. 品牌词 SERP:wykop/dobreprogramy 占位 + Ceneo(电商类)是否在列;(→ 2.3)
3. ChatGPT 关浏览三态测试 + 问"najlepszy [kategoria] w Polsce" 看引用面,分引擎记录(ChatGPT vs Perplexity 结果不同);(→ 四)
4. 电商类:Allegro listing 参数完整度/标题意图式措辞/Smart! 参与状态;(→ 2.1)
5. Bing WMT 是否接入(桌面份额是移动外最大单块);(→ 一)
6. 基线记录:GSC 28 天 + Senuto 可见性快照 + Bing WMT 桌面。

## 一、格局:Google 主极 + Bing 桌面异常厚 + Przeglądy AI 已全量

### 1.1 关键数据(2026-10 复核)

| 指标 | 数值 | 来源/口径 |
|---|---|---|
| Google 搜索份额(全平台) | **89.56%**(Bing 7.38%、Yandex 1.44%) | StatCounter PL,2026-09 |
| Google 桌面份额 | **82.83%**;**Bing 桌面 13.94%** | StatCounter PL 桌面口径,2026-09——Bing 桌面约为全球桌面均值(14.65%)同级,但相对全平台 7.38% 是"桌面假象",必做 |
| Przegląd od AI(AI Overviews) | **2025-03-26 上线波兰语** | 波语版命名"Przegląd od AI";先于多数欧陆市场 |
| AI Mode(Tryb AI) | 2025-10-08 起波语可用,免费、手动切换 | Promptowy/Tabletowo |
| ChatGPT 采用 | **10.2M 月用户(34.4% 网民)** | 2025-10;1 月 3.6M→6 月 9.3M→10 月 10.2M,Gemius/press.pl。**2026-10-09 复核:Gemius《E-commerce w Polsce 2026》(2026-09-30)称 2026-06 AI 工具整体 16M real users、ChatGPT 仍居首**——采用曲线未走平 |
| Allegro 底座 | **~19M 月用户、日均 5.6M**;Temu 日活第二 | 2026-10-09 复核两源一致(nowymarketing 2026-10-01 引 Gemius + Gemius PDF 原文);Gemius 日活榜 Temu 升至第二——比价新势力进入实战名单 |
| AIO 出现频率(波兰本地) | **~每 4 个查询出现 1 次** | Senuto 基于 GSC 数据的分析(aiport 转引,2026)——波兰 Przegląd od AI 覆盖已远高于荷语(对照 nl.md 5.22%),信息类站必须按"AIO 常态"设计 |
| ChatGPT 用户画像 | ~60% ≤34 岁;39.6% 住农村 | Gemius——农村最大单块,勿当纯都市工具 |
| Zero-click | 54%→**72%**(AIO 出现的查询) | 全球口径(malyseo 引 Semrush 类研究),方向性适用 |
| AI 采用总量 | 34.4% 网民用 AI 工具 | O-M.pl 2026 |

### 1.2 解读与实操

- **Bing 桌面 13.94% 是"必做"不是"可选"**:波兰桌面办公场景(Edge/Copilot 预设)撑起份额,Bing WMT + IndexNow 10 分钟接入(GSC 可一键导入);Copilot/ChatGPT search 取材 Bing 索引——AEO 车道顺带受益。移动端策略仍以 Google 为绝对主轴。
- **Yandex 1.44% 不可忽略的存在**:波兰是 Yandex 在欧盟的可见据点之一,仅作监测项,不投入。
- **Przegląd od AI 已运行 18 个月**:GEO 不是"准备做"而是"已迟到";AI Mode 波语化(2025-10)意味着问答式会话流量开始实质分走信息类查询。
- **ChatGPT 增速陡峭**(一年 3.6M→10.2M):波兰是欧洲 ChatGPT 采用最猛的市场之一;GEO 验证协议以 ChatGPT 为主、Perplexity/Gemini 分列(引擎偏好差异见四)。
- 季节闸门:彩蛋季(Wielkanosc 前的 Śmigus-Dyngus/春季) < Back Friday PL(11 月,波兰全境已美式化)< 圣诞 Wigilia(12 月);TEXT 活动提前 60-90 天备货。Allegro 大促(Double 11/Black Week)前后 SERP 波动加大。

## 二、渠道:Allegro 一极 + 发布网络分层

### 2.1 Allegro Trafność 六信号

规模底座:**~19M 月用户、日均 5.6M**(2025-08 Real Users 口径 21.86M)——波兰 e-commerce 事实上的"第二搜索框",商品类查询先审 Allegro 占位再谈 Google 站内。

1. **参数(parametry)100% 填满且逐月更新**——进过滤器位的前提;Allegro 持续新增参数类目,卖家不跟进即从过滤结果消失(→ 六红旗);
2. **意图式标题 ~50-75 字符**——按买家搜索措辞(品牌+品名+型号+关键属性),标题与描述同查询匹配度是 Trafność 首因子;
3. **价格 + 运费总成本**——算法按"到手总价"排序,运费抬高等于自降位;
4. **评价数量与质量**——卖家信誉累计,投诉/取消历史被罚;
5. **CTR 与转化**——有曝光无点击/有点击无成交快速掉位;
6. **吸引力加分项**——图集质量、促销、**Smart!**(免费退货计划)参与、客服响应。

附加:产品图进 Google Shopping/图片搜索的 alt 完整度;m-commerce 占比 43%(2028 预测 53%),listing 移动端首屏决定论;Allegro Ads 竞价位与自然位分开审。

### 2.2 WhitePress 与 guest post 价带

- **WhitePress**:148,000+ 门户、28 国;平台按 SEO 指标/价格/行业筛选门户,含 **link insertion**(在已排名老文中插链,更便宜)——快速补量通道。
- **佣金真相(NETY.pl 分析)**:WhitePress 抽成约 **50%**——同 portal 直联编辑部通常便宜近半;平台价值=筛选+合规+发票,预算紧张时用平台发现、直联成交。
- **价带(2025-2026 波兰市场)**:

| 层 | 价格 | 说明 |
|---|---|---|
| 小博客/利基门户 | **300-800 zł** | WhitePress 上最低从 ~100 zł 起 |
| 中型门户(带客户链) | **1,200-2,500 zł** | 主力带 |
| 大型知名 serwis | **3,500-5,000+ zł** | Onet/Wyborcza 级另议 |

- **zielone linki(绿色链接,即不标 rel="sponsored" 的付费链)溢价明显但高风险**(→ 六)。

### 2.3 Ceneo 与社区层

- **Ceneo**(比价引擎):电商类品牌词 SERP 常客;入驻+价格竞争力(Allegro 报告自称便宜至 20%)影响 Ceneo 排序与 Google 占位,双审。
- **wykop.pl**(类 Reddit 投票社区)/ **dobreprogramy.pl**(软件垂类):品牌词审计必查 UGC 占位;wykop 热帖可进 Google News 类版位。

## 三、语言机制(变音字母 / URL 转写 / sierotki)

### 3.1 变音字母:内容层保留,URL 层转写

- **内容/标题/meta 一律保留 ą/ć/ę/ł/ń/ó/ś/ź/ż**——剥掉变音符是低端机器翻译标记,伤品牌与 AI 引用保真;关键词层勿"ASCII 化"收词。
- **URL slug 共识 = ASCII 转写**:Google 官方(John Mueller)确认能正确索引变音 URL、IDN 域名无惩罚也无加成;但百分号编码(`%C5%82`)可读性差、外链复制易出错——波兰从业者主流实践是 slug 转写 **ł→l、ą→a、ę→e、ó→o** 等。
- **ł 是特例**:与 ę→e 不同,ł 没有唯一显然的 ASCII 对应(ł→l 是约定俗成而非语音转写)——CMS 自动转写规则要显式配置,勿依赖英语系默认表。
- IDN 域名(含变音符域名)punycode 双写、邮件系统兼容差——新站不建,老站不动。

### 3.2 sierotki(孤字排版)

- 波兰排版规范(PN-P-55366:1983 + PWN 口径):**单双字母词(i、w、z、a、o、u、we、ze 等)不得悬在行尾**——用不换行空格(`&nbsp;`/`&#160;`)把短词与后词锁死;缩写与姓氏(dr、prof.、inisjały)同理。
- 这是**排版错误不是拼写错误**——但波兰读者对 sierotki 敏感,生成式内容批量产出时高频暴露;WordPress 有插件/`functions.php` 函数自动修,静态站需在构建层处理。
- title/meta 内不涉及换行,主要是正文与 H 标签层;交付验收清单项。

### 3.3 语域与格式

- **Pan/Pani 敬称**(商务默认)与 **ty**(熟络/消费向)二分—— Landing 页选边后全站一致;混用是失分项。
- 标题 sentence case(仅首词与专名大写),勿 Title Case;数字 **1 234,56**(空格千分位+逗号小数);货币 1 234,56 zł(符号后置);日期 **09.10.2026**;电话 +48。
- 波兰语屈折导致关键词变体多(7 格变化)——关键词研究必须收变格形态,Senuto 波兰本库是前提(→ 七),英语系工具从全球库估波兰量会失真。

## 四、AI-GEO 要点(引擎分列是铁律)

### 4.1 OBTK 银行研究(2026-06):分引擎引用偏好实证

**方法论**:225 个消费金融问题(房贷/消费贷/定存/信用卡/借记账户 5 类×45)× 4 模型(ChatGPT gpt-4.1-mini / Claude sonnet-4-0 / Gemini 2.5-flash / Perplexity sonar)= 900 回答、9,000 记录、每答案查 10 行品牌。

| 品牌 | 总提及 | 份额 | 引擎偏好 |
|---|---|---|---|
| PKO BP | **624** | 18.3% | 总榜第一;房贷/消费贷类霸主,最常被首个点名 |
| mBank | **616** | 18.0% | **ChatGPT 最爱**;借记账户(149/180)与信用卡(138/180)类第一 |
| ING | 562 | 16.4% | **Claude 最爱**;定存类第一 |
| Millennium | 473 | — | — |
| Alior | 385 | — | — |
| Pekao | — | — | **Perplexity 高位**(总榜外单引擎黑马) |

- 三强合计 52.7%(3,419 提及)——AI 回答集中度高于典型 SERP,"进清单"竞争更头部化。
- 模型平均点名 3-4 个品牌;~60% 描述正面或"值得关注",**零批评**——AI 口径天然偏中性正评,声誉管理战在"是否被提及"而非"被怎么说"。
- **Erste(原 Santander PL)改名后仅 101 提及**——2026 春 rebrand 后模型仍念旧牌:**品牌改名/合并的实体滞后是 GEO 专属风险**,需主动更新 Wikidata/Wikipedia/知识图谱层。

### 4.2 实操要点

- **分引擎分列测量**:ChatGPT / Claude / Gemini / Perplexity 各自跑品牌三态(不知道/知道但错/知道且对),勿合并平均——银行案证明单引擎冠军可互不相同。
- **引用面优先级**:Wikipedia(pl)+ Wikidata 实体一致 > wykop/社区讨论 > 本地垂直媒体(betheanswer"Banki w AI 2026"交叉口径:ING 65.5%/mBank 59.8%/PKO 50.5% 的在场率,与 OBTK 排序不完全一致——双报告对照再下结论)。
- 波兰语语料相对小:原创数据报告(本地一手统计)被 AI 引用的边际收益高于大语种市场——"数据生产商"策略在 pl 杠杆最大。
- GEO 检查单:①四引擎品牌三态季度重测;②Wikidata 实体字段(改名/合并即时更新);③段落级可引性(主体+数字+as-of 日期);④Ahrefs AI Overview Tracker(免费,有波语版)盯 Przegląd od AI 占位。

## 五、信息源

- **Planeta SEO**(planeta-seo.pl)——波兰 SEO 博客聚合器,单一入口看全圈月度动态( Spam Update 追踪等);新项目冷启动扫一遍即掌握本地博客版图。
- **Silesia SEM**(silesiasem.pl)——博客(625+ 篇)+ 线下 meetup + 会议;波兰 SEO 圈最老牌社群之一, Katowice 系从业者聚集地。
- **Promptowy**——月度《AI w Polsce》PDF 报告(波兰人问 AI 什么/模型测试),GEO 趋势一手数据。
- **Gemius《E-commerce w Polsce》**年度报告 + **Ceneo e-commerce 报告**——电商规模与行为基线。
- **Delante / Senuto / DevaGroup 博客**——实操向 GEO/AIO 波兰实测多;**seo-ai.pl《Pozycjonowanie AI w liczbach 2026》**(100+ 统计)做交叉验证;obtk.pl 的分引擎品牌研究(银行业模板可迁移到任意垂直)。

## 六、红旗(必拒/必修)

- **Allegro 参数过时即掉位**:Trafność 的过滤器依赖参数完整度;Allegro 逐月新增参数类目,**不跟进 = 直接从过滤结果消失**,且掉位后重新积累 momentum 慢——参数巡检是月度动作,非一次性任务。
- **zielone linki(不标 sponsored 的付费链)**:溢价购入 + Google link spam update/SpamBrain 惩罚风险——批量采买绿色链接是最常见的本地降权诱因;合规线 = rel="sponsored" + 广告披露("artykuł sponsorowany"/"we współpracy z"标注)。
- **WhitePress 整包采信**:~50% 佣金意味着平台价≠市场价;且 portal 质量方差大——逐门户分层审(流量来源/索引量/现有 OBL),勿按目录包购。
- **剥变音字母**:正文/标题/关键词任何一层 ASCII 化都是未本地化标记;反向错配同样成立——URL slug 反而不必强求变音符(见 3.1 双层规则,勿搞反)。
- **品牌词 AI 三态不测就交付**:改名/合并客户必须查 Wikidata 实体滞后(Erste 案例);旧牌残留引用是隐形流量漏损。
- **英语系工具直估波兰量**:屈折变体 + 本地搜索习惯(口语化、错拼)需 Senuto 本库校准(→ 七)。

### 常见误判(本地从业者视角)

| 误判 | 实际 |
|---|---|
| "Bing 只值 7%,可忽略" | 桌面 13.94%,B2B/办公客群桌上真实存在;WMT+IndexNow 成本 10 分钟 |
| "AI 排名 = Google 排名" | OBTK 案:总榜 PKO 第一,但 ChatGPT 榜 mBank 第一、Claude 榜 ING——分引擎测量 |
| "AI 会说品牌坏话,要舆情对冲" | 银行案 0% 批评——战场在"是否被点名",不在评价倾向 |
| "guest post 越贵越好" | 3,500+ zł 大 portal 多为品牌曝光价值;SEO 链值主力在 300-2,500 zł 带,直联可省近半 |
| "URL 保留变音符更本地化" | 共识相反:slug ASCII 转写;本地化体现在内容层变音保留 |
| "sierotki 是小题大做" | 波兰读者视之为排版硬伤,生成式内容高频暴露,验收清单项 |

## 七、Narzędzia

| 工具 | 用途 | 备注 |
|---|---|---|
| **Senuto** | 可见性分析(2015 年起积累)+ 波兰关键词库 + Rank Tracker 日更 + 关键词蚕食识别 | 波兰市场事实标准;数据自 2015,竞对域可见性历史曲线是冷启动最快路径;竞品 Semstorm |
| Ahrefs AI Overview Tracker | Przegląd od AI 占位监控 | 免费,波语界面版本可用 |
| WhitePress | 文章发布/门户发现/link insertion | 148k 门户;记住 ~50% 佣金结构,平台发现+直联成交 |
| Bing WMT + IndexNow | 桌面 13.94% 份额基建 | GSC 一键导入,10 分钟 |
| Google Trends PL | 季节曲线 + 屈折变体词量对比 | gl=PL |
| GSC | 基线 + AI 链接来源(2026 起含 AI 平台 referral 维度) | 28 天口径月检 |

---
**验证协议**:①四引擎(ChatGPT/Claude/Gemini/Perplexity)品牌三态季度重测,分列记录;②Allegro 参数完整度 + 新增参数月检;③Wikidata/Wikipedia 实体字段在改名/合并后即时更新并复测;④StatCounter PL 份额半年度复核;⑤Senuto 可见性基线月度快照。

## 八、Allegro Ads 联动(2026-10-09 增量:站内付费 × 自然位协同)

> pl 市场此前缺的 Allegro Ads 深潜。数据锚点:2026-10-09 复核(波语检索)。

### 8.1 2026 年 Allegro Ads 的地位变化

- **从"可选"变"必做"**:本地 2026 年指南口径(pryzmat.media / lepiejsprzedaj.pl)一致——Allegro 贡献波兰电商大盘 **60-70% 的平台流量盘子**,纯自然位维持头部 listing 的可见性已不现实;Ads 与 Trafność 六信号(2.1)是同一飞轮的两端:广告拉初期 CTR/销量 → 喂转化数据 → 自然位承接 → 降投放。
- **竞价模型=出价 × offer 质量**:排名不只看出价,还看 **CTR、描述完整度、与查询的匹配度**(raiseyoursales 口径)——即 2.1 的"参数 100%+意图式标题"直接降低广告 CPC:**先修 offer 质量再开广告,同预算多买 20-30% 流量**是本地代理的标准话术,方向可信。
- **Top Offer(Top oferta)徽章逻辑**:被有效推广+高转化+低投诉的 offer 更易获 Top 徽章,徽章再反哺 CTR——广告是拿徽章的路径之一,不是平行系统(vsprint 口径)。

### 8.2 与 Google 侧的联动纪律

- **词表分层(同 vi 的双层词表纪律)**:Allego 站内词(购买意图,短+属性)与 Google 词(信息/研究意图)分开建;Allegro Ads 的 wyszukiwania 报告(站内实搜)是 Google 侧品类词表的上游信源之一——站内热词反哺 Google 落地页选题。
- **预算联动公式(提案用)**:冷启动期 Ads:自然投入 ≈ 7:3,稳定期反转 ≈ 3:7——"以投养排"的波兰版;停投后自然位维持时长按类目 2-6 周不等(本地经验值,非官方披露)。
- **Allegro Ads × Przegląd od AI**:Google 侧 AIO 每 4 查询出现 1 次(一、1.1 新行)——商品类查询被 AIO 摘要截流的趋势下,Allegro 站内+Ads 是波兰电商的"确定性流量"仓位,提案里作为对冲 AIO 的论据。
- 红旗承接(→ 六):靠 Ads 灌量掩盖参数过时/差评积累是掉位定时炸弹——Ads 数据越好,算法对 offer 质量信号的权重越敏感。

## 十、本地实测(2026-10-09)

**实测站**:onet.pl(第一门户)、wykop.pl(最大 UGC 社区,markets.json entity_source 之首)。工具:`site_audit.py --market pl` / `llmstxt.py check` / `head_check.py`。

| 站 | site_audit 触发项 | head_check 汇总 | llms.txt |
|---|---|---|---|
| onet.pl | WARN:og 全缺(首页)/ alt 11/11 缺 / 根 /sitemap.xml 不可达;无 CRITICAL | 4 ERROR(apple-mobile-web-app-capable、x-ua-compatible、msapplication-config、mask-icon)+ og:image 缺;exit 1 | 无 |
| wykop.pl | WARN:desc 201 超限 / **2 个 H1** / 338 链接>100 | **0 ERROR,3 WARN(viewport 顺序、geo 缺、微信/QQ 误报)——8 站实测中唯一 head 全绿,exit 0** | 无 |

**工具盲区(如实记录)**:

1. **波兰变音符词被切碎**:`wc()` 的 Latin 正则 `[A-Za-z0-9']+` 不认 ą/ę/ł…——"przegląd" 计成 2 个 token,词数系统性虚高(粗估 +10-20%);"词数<200 soft-thin" 在 pl 站的判定阈值实际应下调。
2. **title 解析泄漏(同 vi/th 的 bug)**:onet 报 "title 70560 字符"(JSON-LD @graph 并入)、wykop 报 121901(内联 CSS 并入)——真实 title 分别 ~25/~75 字符;title 长度结论以 head_check 为准。
3. **`--market pl` 未接线**:sentence case/sierotki/变音保留等 markets.json `special_checks` 在 site_audit/head_check 均无实现——**sierotki 检查对 pl 不适配(工具缺口)**:孤字排版需在构建层(NBSP 处理)或 WordPress 插件层做,套件目前只能人工抽查。
4. **微信/QQ itemprop 检查对 pl 无意义**(误报,忽略)。
5. sitemap 检查只探根 /sitemap.xml,不读 robots.txt 的 Sitemap 声明——onet 的 sitemap 实际在别处,报"不可达"是**假阴性**(与 nl.md nos.nl 同一问题)。
6. wykop 的 2 个 H1 属真发现(多 H1 在门户/社区站常见,层级语义靠 H2 补偿)。

## 维护

- **复核周期**:90 天;**下次复核 2027-01-09**(取代原"验证协议"末行的 2027-04 全量复审——90 天节奏先跑,届时合并)。
- **信号源**:StatCounter 波兰国家页(gs.statcounter.com/search-engine-market-share/all/poland)、Gemius/PBI Mediapanel 月报(ChatGPT/AI 工具 real users;年度《E-commerce w Polsce》)、OBTK(obtk.pl 分引擎品牌研究后续)、Planeta SEO(planeta-seo.pl 月度聚合)、Promptowy《AI w Polsce》月报、Allegro 官方卖家公告(参数类目变更)。
- **上次核验**:2026-10-09(母语一手源重核:引擎份额 89,56/7,38/1,44 精确一致、AIO/AI Mode 双日期、ChatGPT 采用曲线+2026-06 AI 16M、Allegro 19M/5,6M 两源;本地实测 2 站×3 工具)。
