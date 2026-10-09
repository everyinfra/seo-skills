# Google Discover 与新闻 SEO

> 建立于 2026-10-09。来源:Google Search Central 官方文档为基准;Chartbeat/Press Gazette 为行业数据;市场锚:印度中型出版商 Discover 已超 Google Search(dpublish 2026)、日本新闻域名 2026-09 跌出 AI 引用总榜 Top10。

## 一、Discover 机制(官方口径)

- 资格=**已索引+符合 Discover 内容政策**,无特殊标签/schema;排名复用 Search 信号;
- 官方明确定位:Discover 流量 "less predictable"——**视为搜索的补充渠道,不作为业务基线**;波动源于用户兴趣/内容配比/Search 更新,与质量或频率无关;
- **2026-02 首个 Discover 专属核心更新**:①更多展示**用户所在国家网站的本地区内容**;②**打击标题党/煽情**——对跨境 Discover 流量的国际出版商冲击明显(官方博客,细节经转述);
- **Follow/关注——已死(2026-10-09 更新核实)**:2025-08 随 Follow 按钮上线、54 家出版商受邀控制增强版档案(Search Engine Land/PPC Land);**2025-11 Google 从 Discover 文档移除 Follow 指引,官方口径 "The Follow feature is no longer shown in Google Discover"**(Search Engine Roundtable+Google 官方 changelog)——纯 UI 退役,无理由说明;**采用数据:档案控制与 Discover 流量无可测相关性**(PPC Land 对试点组的观察);Chrome 浏览器侧 Follow 功能仍存活(文档仍链接);2026-03 有新的"关注出版商/话题 widget"实验(Delante,实验级)。**教训:不要把渠道策略押在 Google 的社交化实验功能上,Feed/RSS 基建仍值得维护(Crawler 层依赖),但"半持久受众层"叙事已失效。**
- **Discover 流量占比(2026 实测,行业)**:①Chartbeat 网络(2,500+ 站,2026-02):Discover 占全球 pageviews **~14.9%**,Google Search 已跌至 **5.8%**(2024-07 Search 还占 ~9%)——**Discover 已是出版商最大的单一 Google 入口,约为 Search 的 2.6 倍**(SEJ/PPC Land 转述 Chartbeat);②出版商的 Google 引荐流量中 **~68–70% 来自 Discover 而非 Search**(Chartbeat 数据,Press Gazette/David Buttle 2025-08 转述);③新闻站口径:Google Search 占比从 **51% 跌至 27%**,Discover 全面反超(Stan Ventures 转述);④Chartbeat 2,500+ 站 Discover 流量 2025 同比 **−16%**(INMA:2024-12→2025-12 Search pageviews −34%、Discover −16%——**Discover 也在跌,只是跌得慢**);⑤印度地方语言站 Discover 可达 80–90% sessions(单一博客口径,未升级为共识);⑥小出版商 Search 流量最多损失 **60%**(PPC Land/Chartbeat)。

**Discover 生态补充(2026-10)**:①**社交内容混流仍在**:Discover 信息流继续混入 X/Instagram/YouTube Shorts 帖子(2025-09 起的形态,Follow 退役后未撤)——出版商在争的不是"新闻位"而是整个注意力流;②**Chrome 侧入口**:桌面 Chrome 新标签页的 Discover 卡片同样依赖 `max-image-preview:large` 与 feed 可抓取——被低估的桌面流量入口;③**多语言 feed 匹配**:Discover 按用户系统语言+兴趣双轴配流,`news:publication` 的 language 字段写错会让对应语言流"看不到你";④**本地实体信号**:官方否认 Discover 有独立质量分,但 2026-02 更新后"本地区内容优先"实质给了本地实体信号(地址/本地作者/About 页/国别域名)可操作权重——与 Search 的 E-E-A-T 实操殊途同归;⑤**流量结构变化**:Chartbeat"The Audience Trends in the Age of AI"结论——流量没有消失而是在**再分配**(direct/dark social/站内再循环上升),Discover 是 Google 侧最后的大入口但波动性设计如此,任何月的 −50% 都可能是正常的(官方 troubleshooting 口径)。

## 二、Discover 优化要素

| 要素 | 规则(官方) |
|---|---|
| 大图 | **≥1200px 宽、>300,000 总像素(如 1280×720)、16:9**;必须 `max-image-preview:large` robots meta;schema.org/og:image 指定;避免 logo/文字密集图 |
| 标题红线 | 禁误导/夸张预览、禁隐瞒关键信息制造好奇缺口、禁煽情主义;违规可触发 GSC 人工处置 |
| 时效 vs 常青 | 偏好 timely,但匹配兴趣的旧文仍可浮现 |
| 地区 | 2026-02 后**国家属地相关性权重上升**——本地域名/本地存在感>语言本身 |
| 被过滤 | 求职/请愿/表单/代码仓库/无上下文讽刺/超 SafeSearch |

**大图实证(官方案例+行业)**:Google 官方 Large Images 案例研究:启用大图(`max-image-preview:large`+≥1200px)后 Discover CTR **提升 ~50%(1.4x 量级)**、访问量同步上升(developers.google.com/search/case-studies/large-images-case-study,官方);SEL 案例"An Image Could Be Worth 1,000 Clicks":正确用图的出版商单图可带来千级点击(2020 案例但机制仍现行);Bring 案例研究:SEO+结构化数据整改后做到 **月 100 万+ Discover 展示**;wpspeedopt 案例:核心更新掉量后靠 **CWV 修复恢复 1k+/日 Discover 点击**——技术健康度是 Discover 恢复的现实路径;Adsterra 变现案例:Discover 流量周入 $1,000 级(流量质量=低 RPM 高量,广告模式依赖者的真实图景)。**原图摄影/定制题图持续跑赢图库图(多案例共识)。**

**标题党自查实操(对应官方红线,可执行版)**:①**信息完整性测试**——只看标题能否回答"发生了什么/谁/结果",需要点进去才能知道核心事实=踩线;②**情绪词扫描**——shocking/unbelievable/你绝对想不到/"惊呆了"类词出现即重写;③**数字与事实核对**——标题里的每个数字/引语必须正文可溯源;④**A/B 边界**——可以优化好奇心(留悬念在次要细节),不可隐瞒核心结论;⑤**GSC 处置信号**——Discover 手动处置(Manual Actions)会在 GSC 出现 "Discouraged features" 通知,月度检查一次;⑥**2026-02 更新后加严**:煽情主义打击是本轮核心,跨境出版商受损最重——面向他国用户的标题夸张度需要按目标市场文化重新校准(官方博客,细节经转述)。

**2026-02 Discover 专属核心更新的两层影响(细化)**:①**本地内容优先**=用户所在国的网站内容权重上升——对国际出版商意味着:即使语言匹配(英语),美国用户流会优先给美国域名;对策=目标市场本地化站点/本地合作发布/国别 TLD,而非只翻译内容;②**标题党/煽情打击**=CTR 导向的题文不符策略从"灰帽"变"明确负向"——Discover 的推荐系统对 clickbait 的识别在向 YouTube 的 Gemini 标题-内容一致性检测看齐(行业推断,标注)。

**Discover 选题工程(兴趣维度,官方机制的运营化)**:Discover 不按查询匹配而按**用户兴趣画像**推送,因此选题层的可操作面在"实体覆盖度"而非"关键词":①**题材簇连贯性**——算法给站点建兴趣画像,题材跳变(今天财经明天娱乐)会稀释画像纯度,垂直站天然占优;②**实体热度窗口**——突发实体(人物/事件)在热度期进 Discover 概率最高,发布时机=实体热度前 1/3 窗口(行业经验,标注);③**常青兴趣复活**——官方确认匹配兴趣的旧文仍可浮现:维护"可复推库存"(教程/解读类),dateModified 更新即有再分发机会;④**兴趣≠搜索量**——Discover 选题看的是"人群日常关心什么"(健康/理财/体育/本地),不是搜索框里的 query;用搜索词研究指导 Discover 选题是常见错配;⑤**频次无关**——官方明确发文频率不影响 Discover 表现,产能波动期不必恐慌性补稿。

## 三、新闻 SEO 基础层(2026)

- **Publisher Center 已关闭新增(2024-04 停,2025-03 全量)**——新闻收录完全算法化,无申请入口;
- **News sitemap**:仅含**近 48 小时**文章、≤1,000 URL、必填 `news:publication`(名+语言)/`publication_date`/`title`;

**News sitemap 实操常见错误清单(Yoast/AIOSEO/Google 支持论坛汇总,2026-10 核实)**:

1. **塞入 >48h 旧文**——最常见错误:旧文导致 sitemap 校验失败,Yoast 排障文档明确"must have been published within the past 48 hours";窗口滚动必须自动化(见第六节插件),手工维护必出错;
2. **noindex 页面混入**(含被 robots 屏蔽的分类/标签页)——GSC 报 "Submitted URL marked noindex";
3. **sitemap URL 自身重定向**(http→https 或加尾斜杠)——读取失败 "Sitemap could not be read",直接 200 返回 XML;
4. **把 news URL 写成相对路径**——`<loc>` 必须绝对 URL 含协议;
5. **`news:publication_date` 用日期而非完整时间戳**——新闻场景建议精确到秒(ISO 8601,含时区),Google 排序依赖;
6. **publication name 与 Google News 中站点展示名不一致**(历史遗留,Publisher Center 关停后靠算法识别,名称漂移会削弱关联);
7. **超 1,000 URL 不拆分**——单个 news sitemap 硬上限 50,000 URL/50MB(通用限制),但**新闻最佳实践按 48h 窗口自然远小于此**,异常大=窗口逻辑坏了;
8. **提交后 24–48h 内反复重新提交**——Google 重读周期 24–48h,"Last read" 未更新≠异常,先等再排查;
9. **新闻站只提交 news sitemap 不提交常规 sitemap**——两者互补,常规 sitemap 负责常青内容的索引面。

**News sitemap 验收命令(直接可用)**:

```bash
# 1) 窗口合规:输出的最大发布时间距今应 <48h
curl -s https://example.com/news-sitemap.xml | grep -o '<news:publication_date>[^<]*' | sort | tail -1
# 2) 条数上限
curl -s https://example.com/news-sitemap.xml | grep -c '<url>'
# 3) 必填三件套抽查(任一 URL 应同时命中三项)
curl -s https://example.com/news-sitemap.xml | grep -c -e 'news:publication' -e 'news:publication_date' -e 'news:title'
# 4) sitemap 本身 200 直返、无重定向
curl -sI https://example.com/news-sitemap.xml | head -1
# 5) 引用页未被 noindex(抽查)
curl -s https://example.com/news/article | grep -i 'noindex' || echo OK
```

**Fact Check 标签实操(ClaimReview,2026-10 现行路径)**:

- 触发机制:页面上的 schema.org **ClaimReview** JSON-LD → Google Search 显示 Fact Check 富结果、Google News 识别事实核查文章(官方文档+Google 官方博客);
- **两条实现路径**:①手写 JSON-LD(按官方 factcheck 文档,必填:被核查的声明 `claimReviewed`、结论 `reviewRating`、核查文 URL `url`);②**Fact Check Markup Tool**(toolbox.google.com/factcheck/markuptool)——表单式生成,**门槛=Search Console 验证站点所有权**,单个声明标记耗时 <30 秒(ClaimReview Project 用户指南口径);
- **批量/程序化路径:Fact Check Tools API**(Read/Write)可编程增删改 ClaimReview 标记——适合核查量大的新闻室;
- 最佳实践:**一页一 ClaimReview** 为主;一页多声明可用 `ItemList` 包多个 ClaimReview(官方支持);只核查可验证的具体声明(非观点);rating 建议用文字结论(如 "False")而非裸数字;
- 红线:ClaimReview 挂在**第三方声明**上(自己核查别人说的话),给自己的内容打核查标签=滥用。

**ClaimReview JSON-LD 最小可用示例(按官方 factcheck 文档)**:

```json
{
  "@context": "https://schema.org",
  "@type": "ClaimReview",
  "url": "https://example.com/factcheck/claim-123",      // 核查文自身 URL
  "claimReviewed": "某官员称该法案将提高税收 20%",          // 被核查的声明(具体、可验证)
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": "1",                                    // 1=False 尺度需在 ratingExplanation 说明
    "bestRating": "5",
    "worstRating": "1",
    "alternateName": "False",                              // 富结果里显示的文字结论
    "ratingExplanation": "官方预算办公室数据为 3%,非 20%"
  },
  "author": { "@type": "Organization", "url": "https://example.com" }
}
```

**Preferred Sources 现状(2026-10-09 更新)**:2025-08 美/印上线→2025 末日本→**2026-04-30 全球全语言上线**(Google 官方博客)→**2026-05-27 扩展进 AI Overviews 与 AI Mode**(官方博客"original, quality content"篇);用户在 google.com/preferences/source 管理;采用数据:2026-05 末 **~25.5 万**次来源选择,2026-08-20 增至 **60 万+**(PPC Land),并发布**可嵌入出版商站点的 Preferred Sources 按钮**;行业争议:Preferred Sources+算法推荐叠加会强化头部出版商的过滤器气泡(SEJ)。**对新闻站的含义:品牌词心智>纯内容匹配——用户"选你"是新的排名层。**
- NewsArticle schema 推荐非必须(改善标题/图理解);Top Stories 五要素=相关性/prominence/权威/时效/可用性+原创报道优先系统;**Preferred Sources 已在美国/印度上线**(用户可选偏好源);

**Top Stories 五要素的实操映射(官方要素→可执行信号)**:

| 要素 | 可执行信号 |
|---|---|
| 相关性 | 标题/正文/H1 与事件实体对齐;NewsArticle `headline` 与 `articleSection` 一致 |
| Prominence(显著性) | 原创报道/一手信源/署名记者(profile 页+`author` schema);转载与通稿难进 |
| 权威 | 站点级 E-E-A-T:About/编辑部页/作者实体在 Knowledge Graph 可识别 |
| 时效 | `datePublished` 精确到分钟;news sitemap 48h 窗口;突发事件的**首发速度**直接换 prominence |
| 可用性 | CWV(尤其 LCP——大图与速度的矛盾用 AVIF/WebP+响应式解决)、移动友好 |

**NewsArticle schema 字段要点(2026-10 现行)**:`headline`(≤110 字符,超长截断)、`image`(数组给多比例:1:1/4:3/16:9——覆盖 Discover/Top Stories/News tab 三种版位)、`datePublished`/`dateModified` 分开维护(改稿必须更新 dateModified)、`author.person` 带同作者页 URL;`isAccessibleForFree`+`hasPart` 处理付费墙(见第四节);**不要用 BlogPosting 冒充 NewsArticle**(类型错配削弱 News 流关联,行业共识)。
- AMP 已死(Cache 2024 底退役):现行技术要求=可抓取+移动友好+CWV;
- 标签:原创报道(原创优先于转载)、Fact Check(ClaimReview)。

## 四、新闻站 GEO(时效内容的 AI 引用)

- **日本对照(锚)**:2026-04 日本 AI 引用榜 news.yahoo.co.jp 总榜第 4(第一新闻源);**2026-09 总榜 Top10 已无任何新闻域名**(Wikipedia 日语/note/知恵袋/PR TIMES 占据)——**辞书/百科类正在压制新闻源**(Ahrefs Brand Radar,二手转述);
- 全球:AI 最常引 Reuters/AP/FT/BBC/Yahoo News/Forbes;仅 11% 域名同时被 ChatGPT 与 Perplexity 引用——分引擎监测;

**新闻内容提高 AI 引用面的实操(与上互补,2026-10)**:①**事实密度前置**——导语即给数字/结论/时间(AIO 摘要从首段抽取的权重最高,行业观察);②**原创数据是唯一护城河**——自有调查/独家信源类内容被 AI 引用且难以被摘要替代(SEL:突发+103% 的另一面);③**多引擎分别监测**——ChatGPT/Perplexity/Gemini 引用偏好不同(11% 重叠率意味着在一个引擎可见≠另一个也可见);④**结构化时间线**——事件长报道内嵌 timeline(更新流)让 AI 反复回访;⑤**署名实体化**——作者实体被 KG 识别的新闻室在 prominence 维度持续占优(Top Stories 要素同理);
- **付费墙与 AI 的杠杆反转**:First Click Free 已废→Flexible Sampling;`isAccessibleForFree`/`hasPart` schema;**Cloudflare 2025-07 起默认封 AI 训练爬虫并推 Pay-Per-Crawl→2026 Pay-Per-Use**;~79% 大型新闻站屏蔽 AI 训练爬虫;授权分成试点并行——新闻内容的 AI 可见性正在从"开放索引"转向"商业授权"。

**AI 摘要对新闻点击的侵蚀(2026 量化,引用需注明样本)**:

- **Ahrefs(2026-02)**:AIO 出现时首位页面 CTR **降 ~58%**(2025-04 同方法测得 34.5%——一年恶化近一倍;TNW/ppc.land 转述);
- **零点击**:Google 零点击率 **68%**;AIO 已覆盖 **39.4% 美国桌面查询**(2026-06,同比 +13pp;qz.com 转述 Comscore 类数据);
- **Search Engine Land 报告口径**:AIO 使整体搜索点击 **−42%**,但**突发新闻(breaking news)流量 +103%、Discover 点击上升**——AI 摘要吃掉的是"可摘要的常识查询",时效性/独家内容反而有窗口;
- **Press Gazette(头部站口径)**:美国 Top10 新闻站两年流量 **−1/3**;CNN 自然搜索访问 **−61%**(月 124.4M→48.4M);
- **Piano.io 基准(数百出版商站)**:搜索流量 **−36%** 但收入仅 **−16%**——**留下来的读者更忠诚更值钱**(订阅/直接转化占比上升);
- **Nieman Lab(2026-07)**:部分出版物 2025-06→2026 年中流量 **−40%+**,已有出版商认真评估**彻底退出 Google 索引**;
- **Discover 自身也在被侵蚀**:Google 开始在 Discover 内用 **AI 撰写的摘要替代出版商链接**(Press Gazette 2026 报道)——"Discover 是避风港"的假设有保质期;
- **策略含义(综合)**:①突发/独家>常青百科式内容(AIO 无法摘要"现在");②直接流量/newsletter/App 的单位价值上升;③评估"退出 Google"不再是边缘选项而是董事会级议题(Nieman)。

## 五、监测

GSC Discover 报告:只有展示/点击/CTR、16 个月、含 Chrome 流量;**看不到查询词维度(设计如此)、排名位置、16 个月前数据**。对策=官方定位"补充渠道"→多元化(newsletter/App/直接流量;dark/direct 流量正在上升——Press Gazette)。

**监测实操补充(2026-10)**:

- **GSC Discover 报告的三个隐藏用法**:①按页面维度排序找"意外爆款"——Discover 的选题风向标(无查询词,页面即最小分析单元);②「Appearance」确认大图资格——展示量高但 CTR 异常低的页面,九成是题图问题;③导出 16 个月历史做基线,**单日/单周波动不判死刑,月度滚动均值才作数**(与官方"不可预测"口径一致);
- **Discover 数据不在 GSC API 里**(官方确认 API 不返回 Discover 报告)——自动化监测只能手工导出或用 Chartbeat 类分析工具;
- **GA4 侧配 UTM 不可行**(Discover 引荐不带自定义参数),用 landing page+referrer 组合估算;dark social(WhatsApp/消息类分享)用短链+参数兜底;
- **头部参照系**:Chartbeat 网络基准(2026-02:Discover 14.9% pageviews、Search 5.8%)可作自家占比的健康对照——**显著高于 15% 即高依赖,提前触发第六节第 7 条动作**;
- **Nieman/Piano 口径补充**:监测"收入/流量比"而非只看流量(Piano:流量 −36% 收入仅 −16%)——订阅转化率、直接流量占比、newsletter 打开率是 AI 时代比 sessions 更早的预警指标。

## 六、实操清单(合并,含验收动作)

1. 大图规范(1280×720/16:9/max-image-preview:large)进 CMS 模板;**验收:随机抽 20 篇新文,`curl -s URL | grep max-image-preview` 全部命中 `large`,且题图 ≥1200px 宽**;
2. 标题过"标题党红线"自查(不隐瞒关键信息/不夸张);**验收:抽样标题去标题/留事实,信息损失<20% 即合格**;
3. News sitemap 自动滚动 48h 窗口(WP 插件 10up/simple-google-news-itemap);**验收:`curl -s sitemap.xml | grep -c "<url>"` ≤1000 且抽查首条文章发布时间 <48h;GSC「Sitemaps」Last read 24–48h 内有更新**;
4. 原创报道信号(署名/独家标记)+ ClaimReview(如有事实核查);**验收:Rich Results Test 对核查文显示 Fact Check 卡片;Fact Check Markup Tool 用 GSC 验证账号登录可用**;
5. 地区属性强化(2026-02 更新后):本地作者/本地实体/国别域名;
6. RSS/Atom feed 有效(Follow 已死但抓取层仍依赖 feed 发现——维护成本极低,保留);
7. Discover 依赖度审计:单一渠道占比>40% 即触发多元化动作;**验收:GA/Chartbeat 里 Discover/总流量比月度环比监控,>40% 告警**;
8. 新闻 GEO 立场决策:开放(索引+引用)vs Cloudflare 付费墙(商业授权)——按商业模式二选一,不骑墙;
9. **Preferred Sources 按钮嵌入**(2026-08 起可用):官网引导读者把自己设为偏好源,争夺"被选择"层(PPC Land);
10. **Follow 功能相关投入清零**(2025-11 已退役)——存量教程/插件如仍在配置 Following tab 属无效功。

## 七、Discover 掉量故障排查(决策树,综合官方 troubleshooting+行业案例)

1. **全站掉(基线级,持续 >2 周)** → 按序查:①GSC Manual Actions("Discouraged features"/标题党处置);②core update 时间线对照(AlgoTracking/SERP Metrics,同期全行业掉=环境);③技术回归——CMS 改版后 `max-image-preview:large` 丢失是最常见静默杀手(模板 diff 必查);④比例检查:如果 Search 同步在掉而 Discover 跟跌,是站点级质量信号问题;只有 Discover 掉而 Search 稳,多与兴趣配比/内容类型漂移有关(官方口径:波动≠惩罚);
2. **单类内容掉、其他稳** → 内容配比问题:近期选题密度变化(官方明确"内容类型变化会引起 Discover 流量变化,与质量无关")——恢复原有内容配比并观察 2-4 周;
3. **新站/新文完全无 Discover** → 正常:Discover 无提交通道、完全靠索引+兴趣匹配,新站冷启动 4-12 周常见;先确认 Search 索引正常(GSC Coverage)+大图合规;
4. **掉量后恢复案例参照**:wpspeedopt 案例——CWV(LCP/INP)修复后恢复 1k+/日;Bring 案例——结构化数据+SEO 整改后 100 万+月展示;共同点:**恢复路径都是技术债清理,不是"发更多"**;
5. **不要做的事**:为 Discover 改发稿频率(官方明确频率与 Discover 表现无关);删旧文"净化"(旧文仍可被兴趣匹配召回);把 Discover 数据当 KPI 承诺给客户(官方"less predictable"口径是免责条款也是真相)。

## 来源

官方:Google Discover 文档/2026-02 更新博客/news sitemap/ranking systems/troubleshooting;Large Images 官方案例(developers.google.com/search/case-study/large-images-case-study);Fact Check(ClaimReview)文档+Fact Check Markup Tool+Fact Check Tools API+Google 官方博客(Labeling fact-check articles);Preferred Sources 全球化公告(blog.google,2026-04-30)与 AIO/AI Mode 扩展(2026-05-27);Google 官方 changelog(Follow 移除)。行业:Press Gazette(Top10 新闻站/CNN −61%/Discover AI 摘要)+Chartbeat(SEJ 转述:Search −40.2% YoY、Discover 14.9% pageviews、小出版商 −60%;Buttle:Google 引荐 68–70% 来自 Discover)、INMA(Search −34%/Discover −16%)、Stan Ventures(51%→27%)、Ahrefs 2026-02(CTR −58%)、Piano.io(−36%/−16%)、Nieman Lab 2026-07、qz.com(零点击 68%/AIO 39.4%)、SEL(AIO 点击 −42%/突发 +103%)。Follow 退役:Search Engine Roundtable+PPC Land(54 家试点/无相关性)+Delante(2026-03 widget 实验)。sitemap 错误:Yoast/AIOSEO/Google 支持论坛。案例:SEL/Bring/wpspeedopt/Adsterra。市场:dpublish.in(印度)、Web担当者Forum(日本榜,二手)。付费墙:Cloudflare Pay-Per-Crawl/Use。GitHub:10up news sitemap(15★)/php-sitemap(1,342★ 含 news 格式)——**Discover 优化专用库近乎空白**。未证实项:2026-02 Discover 更新完整正文未直读;Chartbeat/Raptive 口径不一;印度 80-90% 为单一博客;Bring/wpspeedopt/Adsterra 案例为服务商自述无第三方审计;Discover 内 AI 摘要替代链接的覆盖面无量化数据。
