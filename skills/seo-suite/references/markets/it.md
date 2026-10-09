# Mercato Italiano(意大利市场专项参考)

> 适用圈:意大利(it-IT 主市场)+ 瑞士意大利语区(it-CH 提契诺,当独立 locale)+ 圣马力诺。
> 数据锚点:2026-10-09;断言半衰期 6–12 个月,随复审更新。
> 本轮增量信源:SEOZoom AI Overview 研究(2025-12)/mimir.bot 意大利实测(2026-09-08,DataForSEO live SERP,971 词)/ANSA-Teleborsa 电商报告(2026-01,Google 90.87%)/Statista 意大利桌面份额(2026-08)/The Guardian FIEG-AGCOM 之争(2025-10-16)/press-delivery.it 官方价目/Telelead·Eviblu·Italia Notizie 24·PMA 链接市场价带/veronicameriggi 文案价带/Truenumbers·Sarao Amazon 口径拆解/Leadverge(2026-08-28 AIO 自动扩张)/Kroma Studio(AIO 外链占比)。

## 〇、关键数字速查

| 维度 | 值 | 口径/日期 |
|---|---|---|
| Google 份额 | 全平台 **~90.87%** / 桌面 80.47% | ANSA 2026-01;Statista 2026-08 |
| 第二引擎 | Bing 全平台 4.83%(桌面双位数)/Yahoo 2.29% | ANSA 2026-01 |
| AIO 上线 | **2025-03-26 与 DACH 同批**;2025 Q3 扩至非 YMYL 信息类 | 总纲锚点/Esc Agency |
| AIO 覆盖率 | **54%(SEOZoom)vs ~48%(BrightEdge)两口径** | 2025-12 / 2026-02 |
| AI 主题词 AIO | 81.1%(971 词 live 实测;信息类 96.8%) | mimir.bot 2026-09-08 |
| AIO 引用集中度 | 仅 **~0.1% 网站**被引;均 7.9 源/条 | SEOZoom / mimir.bot |
| 新闻流量冲击 | Repubblica −30%;极端 −40–50%;Wikipedia 因果 −15% | FIEG 系 / Newslinet |
| 新闻稿底价 | **€6 One Shot**(自写)/ €180 Smart(记者执笔) | press-delivery.it/prezzi |
| 文章外包 | **25–80€/篇**均值;文案时薪 40–100€ | veronicameriggi 圈内 2026 |
| guest post 价带 | 博客层 15–50€;中档 50–250€;全国性媒体 1,500€+IVA 起 | Telelead/Eviblu 等 |
| title/desc/支柱 | 60 / 155 字符;支柱 ≥1,800 词 | markets.json |

## 一、格局

### 1.1 引擎份额(两口径并记)

| 口径 | 数值 | 来源/日期 |
|---|---|---|
| 全平台 | Google 90.87% / Bing 4.83% / Yahoo 2.29% | ANSA-Teleborsa 2026-01 |
| 桌面 | Google 80.47%(Bing 双位数) | Statista 2026-08 |

实操:移动一家独大;桌面 Bing 值得开 Webmaster+IndexNow,但投入量级远低于德/法桌面场景——报价按设备拆分口径写。

### 1.2 AI Overviews 时间线

- 2025-03-26 与 DACH 同批上线;2025 Q3 已覆盖全部非 YMYL 信息类查询(Esc Agency);**2026-08-28 起对部分查询自动扩张**(Leadverge)——覆盖曲线仍在爬坡,任何"覆盖率"数字必须带采样窗。
- 意图分层(mimir.bot live 实测):信息类 96.8% > 商业 92.9% > 导航 90.2%;**长尾不避险**(<50 搜索/月词 AIO 出现率 83.7%)——"躲长尾保点击"策略在意大利无效。

### 1.3 覆盖率两口径

- **SEOZoom(本土口径):54% 的意大利搜索触发 AIO**(2025-12)。
- **BrightEdge(美系监测):~48%**(2026-02);Conductor 更保守:25.11%(21.9M 查询,Q1 2026)。
- 三口径并记不选边;给客户的表述:"约一半搜索、信息类几乎全部"。本土口径高于美系工具口径——意大利语 AIO 监测优先用本土数据源。

### 1.4 新闻域名跌出 AI 引用

- FIEG(意大利出版商联合会)2025-10 向 **AGCOM** 递状:指 AI Overviews/AI Mode 违反 DSA、Google 是 "traffic killer";同期部分编辑方上诉欧盟委员会。
- Google 公开回应称这些研究"**不准确**"(方法学有缺陷,The Guardian 2025-10-16)——流量数字本身已成监管争议:引用任何一侧数字都必须带方法学附注(与 markets.json "测量值 vs 估算值声明降级"检查项联动)。
- 冲击样本:Repubblica −30%;HDblog 引述极端 −40%;美国对标(USA Today/Politico)12 个月 −50%;Wikipedia 暴露文章因果 −15%。
- 结果:新闻域名在 AI 引用面边缘化(见 4.2 引用集中度),意大利是欧洲"出版商 vs AIO"对抗最激烈的战场——新闻侧客户的内容策略要按"可被切分引用的原创数据"重排。

## 二、渠道

### 2.1 P.IVA→Registro Imprese 竞品链(意大利特有作业流)

- 意大利网站页脚**法定必须公示** P.IVA(增值税号)+ Registro Imprese 登记信息——每个竞品页脚即情报入口。
- 链路:竞品页脚 P.IVA → registroimprese.it/商会查询 → **ATECO 行业码 + 省份** → 同 ATECO 同省企业清单 = 真实竞品池 → 逐家核 SERP/外链/报价页。
- 同构:法 societe.com/Pappers、德 Handelsregister——竞品研究不靠猜,靠登记系统;B2B 报告第一步即跑此链。

### 2.2 新闻稿渠道:Press-Delivery 底价 €6

- **€6 One Shot**(自写自投发布)+ **€180 Smart**(平台记者执笔)——欧洲最低新闻稿门槛之一;SEO 结构化通稿进编辑部分发网络。
- 用法:初创低成本实体占位(品牌词 SERP+被索引的 NAP 一致信号);升级路径:全国性媒体署名文章 **1,500€+IVA 起**(Telelead 类代理)。
- 通稿仍须 publiredazionale(软文)披露——透明度义务先于 SEO 收益。

### 2.3 guest post 价带(2026-10 圈内)

| 层 | 价带 | 备注 |
|---|---|---|
| 低端博客/网络稿 | 15–50€/篇 | Telelead 起 15€;质量与邻域需逐条审 |
| 中档博客/门户 | 50–250€ | Eviblu 30–250€;Italia Notizie 24 列表价 150€/篇、5 篇 400€ |
| 软文写+发打包 | 60–140€ | PMA 类,3–5 天交付 |
| 全国性媒体署名 | 1,500€+IVA 起 | 含刊出保证 |

对比:德月租制(119€+/月)、法平台层(€3–10/条)——意大利呈**金字塔结构**,DA 15–30 约 100–150€ 起步按权威度爬坡;外链台账按"购链资产"与"内容资产"分列。

### 2.4 Connect.gt(圈内信息源)

- Giorgio Tave 系意大利 SEO 老牌社区(Forum GT 延续),衍生 copywriter.giorgiotave.it 等垂直站——意大利圈结论先过本地社区再引用(同构:法 Abondance)。

## 三、语言机制

### 3.1 意英双语双轨

- 意大利人高频直接用英语词:**SEO、digital marketing、machine learning、power bank** 常不翻译——"ottimizzazione per motori di ricerca"这类全直译形几乎无搜索。
- 关键词表双轨:**技术/潮流词用英语借词形 + 交易/生活词用意语形**(prezzo、spedizione、recensioni、come fare)。
- 英语借词页 ≠ en 内容:hreflang 仍按 it-IT 归档,勿因借词多就挂 en 页。

### 3.2 关键词池小于德法

- 同主题意语搜索量级系统性低于德/法语市场——量级预测**禁按 DE/FR 等比折算**。
- 补量策略:问题式长尾(come / quanto costa / migliore per)+ 英语借词层 + it-CH 微量增量;核心词在意语池做透优先于铺量。

### 3.3 内容外包 25–80€

- 文章均价 **25–80€/篇**,专业文案时薪 40–100€;低价平台 7.50–15€ 是红旗(翻译腔/AI 裸稿)。
- 1,800 词支柱预算走上沿 80€+,或拆"本地人写框架+草稿外包"两层;意大利语比英语长 ~10–15%,title 翻译留余量防截断。

### 3.4 语域与 locale

- Lei 商务默认 / tu 营销口语,全站一致;it-CH 独立 locale(.ch 域+CHF 定价+混德法语词),复制 it-IT 会被信号归并(markets.json 锚点)。

## 四、AI-GEO

### 4.1 引用面:Wikipedia 48.67% + Aranzulla 第三(锚点)+ 增量实测

- 既有研究锚点:Wikipedia 占比 **48.67%**,**Aranzulla 个人站第三**——个人专家站在国家级 AI 引用面权重全球罕见。
- 增量实测(mimir.bot 2026-09-08,971 意语 AI 主题词,457 条可见引用):均 **7.9 源/条、653 唯一域名**;**YouTube 68.5%** 单项第一;**aranzulla.it 12.3%**(56 词)意语第一域名,fastweb.it(41 词)第二梯队;厂商官网(OpenAI/Google/IBM/Microsoft)合计 51%;Wikipedia 双语合计 ~15%。
- 解读:垂直媒体不出头,**通用权威+教程型个人站**吃掉引用面;但 Aranzulla 本人自报 **−25% 流量**——"被引最多"与"保住流量"是两回事,报告分列。

### 4.2 引用集中度:0.1% 俱乐部

- SEOZoom:**仅 ~0.1% 的网站**被 AIO 引用——GEO 目标按"进入 0.1% 俱乐部"设计:Wikipedia/Wikidata 实体一致、可切分答案段、一手数据+方法学声明;新闻域名正跌出该俱乐部(见 1.4)。

### 4.3 测量方法学(意大利专属坑:缓存低估近半)

- **缓存/存档 SERP 把 AIO 低估近一半**:123 个头部词,缓存(中位 41 天)63 条 vs live 实测 113 条(mimir.bot)——意大利 AIO 监测必须用 live SERP API,用缓存数据得出的"覆盖低"结论作废。
- FIEG-Google 争议背景下,"测量值 vs 估算值声明降级"从建议升级为**合规级要求**;证据阶梯六级分开记(eligible→retrieved→cited→mentioned→recommended→converted)。

### 4.4 CTR 基准与窗口

- Pew(68,879 真实搜索):有 AI 摘要点击率 8% vs 无 15%;Ahrefs 位一 −34.5%;Seer 信息类 −61%——意大利提案按此区间给预期。
- **AIO 外链占比从 ~0% 升至 >25%**(Kroma Studio)——引用入口在增值,占位窗口仍开。

## 五、红旗

1. **直译关键词**:英意词典逐词映射("ottimizzazione motori di ricerca"式)不是意大利人真实查法——技术词用英语借词、交易词用意语,全部经 SEOZoom/Keyword Planner it-IT 验证。
2. **Amazon 份额传闻数**:"Amazon 占意大利电商 40%"——**40.4% 是美国口径**常被错安到意大利;本土估计 GMV 35–52%(Truenumbers 52%,EU Big Five 最高;西班牙 ~20%),换 62.3B€ B2c 全口径分母则远低于 52%;Amazon 不公布分国数据,audience 口径 36.1M 用户——引用必须标口径与分母。
3. **缓存测 AIO**:低估近半,禁用于覆盖率结论。
4. **争议数当定数**:FIEG −30/−40% 与 Google"不准确"针锋相对——两方并列+方法学附注,不选边。
5. **5 星迷信**:意大利 4 星>5 星信任校准(markets.json 锚点)。
6. **it-CH 复制 it-IT**:信号归并风险;**被引=有流量**:Aranzulla 被引第一梯队仍 −25%,GEO 报告分开记引用与推荐流量。

## 六、Strumenti(工具)

- **SEOZoom**:100% 意大利套件——keyword research(意图分层)/rank tracking/audit/竞品分析,已扩至"Google+AI 引擎可见性";本土 AIO 研究(54% 覆盖/0.1% 被引)与 zero-click 分析第一信源;价位低于 Semrush、意语 SERP 数据深于美系工具——意大利市场默认主力。
- **mimir.bot 方法论**(DataForSEO live SERP):意大利 AIO 实测采样协议可复制(live API+分层抽样+量级分层)。
- **Connect.gt / giorgiotave 系**:圈内共识第一道过滤。
- **StatCounter / Statista**:份额按设备拆分并记。
- **WhitePress**:意语 sponsor 文章 marketplace,价带询价基准。
- **Bing Webmaster + IndexNow**:桌面双位数份额下的第二索引通道。
- **AGCOM / FIEG 公告**:新闻侧政策风险追踪(相邻权/DSA 争议演化)。

## 复审钩子(下次更新先查)

1. SEOZoom 54% 是否发布新采样窗(2027-01);2026-08-28 自动扩张后的覆盖与 CTR 复测。
2. FIEG-AGCOM/欧盟投诉走向——新闻域名是否重返 AI 引用面。
3. Amazon 分国权威新估计(52% vs 35% 是否收敛)。
4. AIO 外链占比(>25%)继续上升趋势确认。
5. it-CH(提契诺)SERP 差异信号是否强化。

## 本地实测(2026-10-09)

### 一手源重核结论

- **StatCounter IT 直核(多源交叉)**:桌面 host 口径(2025-08~2026-08 窗口)Google.com **79.84%** / Bing.com 9.37%;移动口径 2026-07 **Google 97.04%**(DDG 0.63%/Bing 0.62%);全平台第三方汇编(alphametic,2026-04)**88.97%**/Bing 5.64%/Yahoo 3.55%。
- **裁决**:本文件关键数字自洽——ANSA 90.87%(2026-01)落在 StatCounter 系全平台 89-91% 带内;Statista 桌面 80.47% vs StatCounter 桌面 79.84% 差 <1pp。**多源一致,单源标注项:Repubblica −30% 系 FIEG 方单方口径(Google 称"不准确"),维持两方并记。**

### 真实站验证(repubblica.it / aranzulla.it)

| 项 | repubblica.it | aranzulla.it |
|---|---|---|
| site_audit CRITICAL | **PerplexityBot 被 robots 禁**——AI 答案被逐出 | meta description 缺失(首页) |
| site_audit WARN | 34 个 H1(首页聚合页常态)/641 链接 | 跳级 h1→h4 / 无 JSON-LD |
| llmstxt check | **/llms.txt 200(意语内容地图)** | 全部 ✗(无 llms.txt) |
| head_check | error=6(弃用 twitter:* 全套+fb:app_id) | error=0(仅顺序/geo WARN) |

- **解读 ①(FIEG 悖论的现场证据)**:repubblica 一边向 AGCOM 递状抗议 AIO,一边**已部署 /llms.txt 且只封 PerplexityBot、放行 OAI-SearchBot/Claude-SearchBot**——出版商的真实策略是"选择性 AI 分发"而非全面对抗;给新闻侧客户的建议从"对抗 AIO"修正为"分级放行+被引监测"。
- **解读 ②(Aranzulla 反直觉)**:头部 meta/description/JSON-LD 全缺、无 llms.txt,仍是意语 AIO 被引第一域名——**可切分内容 > 技术完备性**;技术审计权重在意市场应向"答案段落结构"倾斜。
- **工具盲区记录**:①site_audit.py 标题解析器吞脚本——`handle_endtag('title')` 不关闭累积,title 一路吸到 `<body>`,实测 23,050/25,270 字符假超标(6 站全触发);②`wc()` 词计数用 `[A-Za-z0-9']+`,意语重音词(à/è/ù/é)被切碎,词数虚高——与德法同病;③`--market it` 无专属阈值(仅 ja 特判),desc 上限用 160 而非本文件 155。

### Connect.gt 社区实时动向(2026-10 抽样)

- 社区体量复核:Giorgio Taverniti(GT 系创始人)公开口径 **13 万+注册**,2004 年 Forum GT 延续至今——意大利圈共识第一道过滤的地位未变。
- SEO 版块热帖样本:**站群迁移三问**(集团站→商业站拆分:交叉 canonical 必须拆除、301 一对一防链、GSC "Cambio di indirizzo" 工具用法)——社区共识与英文最佳实践一致,但**术语全意语化**(migrazione/canonical incrociato),检索本地案例用意语词。
- Taverniti 2026 年初公开课定调 **"SEO in 2026: The Year of Awareness"**(认知年):主线是 AI 时代从业者的定位重估——与 SEOZoom "0.1% 俱乐部"叙事同构:圈内共识已从"排名"转向"被引/可见性"计价。
- 实操含义:意语报告引用本地共识时,优先链 Connect.gt 帖+SEOZoom 研究,再补美系工具口径——本土口径系统性高于美系(见 1.3),引用顺序即立场。

## 维护

- **复审节奏**:随 markets.json `it.review_cycle`(interval_days 90,next 2027-01-09);触发信号:SEOZoom 新采样窗、FIEG-AGCOM/欧盟程序性进展、StatCounter IT 桌面份额跌破 78% 或 Bing 桌面破 11%、Connect.gt 年度大会议题单。
- **数字分诊**:引擎份额=StatCounter 直核+ANSA 并记;AIO 覆盖=SEOZoom/BrightEdge/Conductor 三口径;流量冲击=FIEG vs Google 两方并记+方法学附注;单源数字(如 Amazon 52%)标注后才可引用。
- **工具链提醒**:对本市场跑 site_audit 时,标题长度/词数两项读数先人工复核(标题吞脚本 bug+重音词碎片化);AIO 监测一律 live SERP(缓存低估近半,见 4.3)。
