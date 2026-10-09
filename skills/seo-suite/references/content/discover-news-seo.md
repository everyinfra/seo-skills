# Google Discover 与新闻 SEO

> 建立于 2026-10-09。来源:Google Search Central 官方文档为基准;Chartbeat/Press Gazette 为行业数据;市场锚:印度中型出版商 Discover 已超 Google Search(dpublish 2026)、日本新闻域名 2026-09 跌出 AI 引用总榜 Top10。

## 一、Discover 机制(官方口径)

- 资格=**已索引+符合 Discover 内容政策**,无特殊标签/schema;排名复用 Search 信号;
- 官方明确定位:Discover 流量 "less predictable"——**视为搜索的补充渠道,不作为业务基线**;波动源于用户兴趣/内容配比/Search 更新,与质量或频率无关;
- **2026-02 首个 Discover 专属核心更新**:①更多展示**用户所在国家网站的本地区内容**;②**打击标题党/煽情**——对跨境 Discover 流量的国际出版商冲击明显(官方博客,细节经转述);
- **Follow/关注(2025-09)**:Discover 内可直接关注发布者(半持久受众层);部分 Follow 入口依赖有效 RSS/Atom feed;Discover 开始混入 X/Instagram/YouTube Shorts 帖子;54 家出版商受邀控制增强版档案;
- 行业数据:Chartbeat 2,500+ 站 Discover 流量 2025 同比 **−16%**;印度地方语言站 Discover 可达 80–90% sessions(单一博客口径)。

## 二、Discover 优化要素

| 要素 | 规则(官方) |
|---|---|
| 大图 | **≥1200px 宽、>300,000 总像素(如 1280×720)、16:9**;必须 `max-image-preview:large` robots meta;schema.org/og:image 指定;避免 logo/文字密集图 |
| 标题红线 | 禁误导/夸张预览、禁隐瞒关键信息制造好奇缺口、禁煽情主义;违规可触发 GSC 人工处置 |
| 时效 vs 常青 | 偏好 timely,但匹配兴趣的旧文仍可浮现 |
| 地区 | 2026-02 后**国家属地相关性权重上升**——本地域名/本地存在感>语言本身 |
| 被过滤 | 求职/请愿/表单/代码仓库/无上下文讽刺/超 SafeSearch |

## 三、新闻 SEO 基础层(2026)

- **Publisher Center 已关闭新增(2024-04 停,2025-03 全量)**——新闻收录完全算法化,无申请入口;
- **News sitemap**:仅含**近 48 小时**文章、≤1,000 URL、必填 `news:publication`(名+语言)/`publication_date`/`title`;
- NewsArticle schema 推荐非必须(改善标题/图理解);Top Stories 五要素=相关性/prominence/权威/时效/可用性+原创报道优先系统;**Preferred Sources 已在美国/印度上线**(用户可选偏好源);
- AMP 已死(Cache 2024 底退役):现行技术要求=可抓取+移动友好+CWV;
- 标签:原创报道(原创优先于转载)、Fact Check(ClaimReview)。

## 四、新闻站 GEO(时效内容的 AI 引用)

- **日本对照(锚)**:2026-04 日本 AI 引用榜 news.yahoo.co.jp 总榜第 4(第一新闻源);**2026-09 总榜 Top10 已无任何新闻域名**(Wikipedia 日语/note/知恵袋/PR TIMES 占据)——**辞书/百科类正在压制新闻源**(Ahrefs Brand Radar,二手转述);
- 全球:AI 最常引 Reuters/AP/FT/BBC/Yahoo News/Forbes;仅 11% 域名同时被 ChatGPT 与 Perplexity 引用——分引擎监测;
- **付费墙与 AI 的杠杆反转**:First Click Free 已废→Flexible Sampling;`isAccessibleForFree`/`hasPart` schema;**Cloudflare 2025-07 起默认封 AI 训练爬虫并推 Pay-Per-Crawl→2026 Pay-Per-Use**;~79% 大型新闻站屏蔽 AI 训练爬虫;授权分成试点并行——新闻内容的 AI 可见性正在从"开放索引"转向"商业授权"。

## 五、监测

GSC Discover 报告:只有展示/点击/CTR、16 个月、含 Chrome 流量;**看不到查询词维度(设计如此)、排名位置、16 个月前数据**。对策=官方定位"补充渠道"→多元化(newsletter/App/直接流量;dark/direct 流量正在上升——Press Gazette)。

## 六、实操清单(合并)

1. 大图规范(1280×720/16:9/max-image-preview:large)进 CMS 模板;
2. 标题过"标题党红线"自查(不隐瞒关键信息/不夸张);
3. News sitemap 自动滚动 48h 窗口(WP 插件 10up/simple-google-news-itemap);
4. 原创报道信号(署名/独家标记)+ ClaimReview(如有事实核查);
5. 地区属性强化(2026-02 更新后):本地作者/本地实体/国别域名;
6. RSS/Atom feed 有效(Follow 入口依赖);
7. Discover 依赖度审计:单一渠道占比>40% 即触发多元化动作;
8. 新闻 GEO 立场决策:开放(索引+引用)vs Cloudflare 付费墙(商业授权)——按商业模式二选一,不骑墙。

## 来源

官方:Google Discover 文档/2026-02 更新博客/2025-09 Follow 公告/news sitemap/ranking systems/troubleshooting。行业:Press Gazette+Chartbeat、SEL(Publisher Center/Preferred Sources)、Fuel Online、dpublish.in(印度)、Web担当者Forum(日本榜,二手)。付费墙:Cloudflare Pay-Per-Crawl/Use。GitHub:10up news sitemap(15★)/php-sitemap(1,342★ 含 news 格式)——**Discover 优化专用库近乎空白**。未证实项:2026-02 更新完整正文未直读;Chartbeat/Raptive 口径不一;印度 80-90% 为单一博客。
