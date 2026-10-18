# Google Discover 与新闻 SEO

> 建立于 2026-10-09；2026-10-18 逐条核对一手来源（证据账本 C3）。规则以 Google Search Central 文档、Search Status Dashboard 和 Publisher Center 帮助为准。第三方数字标「第三方」，并写样本和时间。「本套件口径」是本套件的做法约定，不是 Google 规则。GEO 证据的仲裁见 [geo-evidence.md](geo-evidence.md)。

## 一、Discover 机制（官方口径）

- **资格**：内容被 Google 索引，并且符合 Discover 内容政策，就自动有资格。不需要特殊标签或结构化数据。有资格不等于一定出现。来源：[Get on Discover](https://developers.google.com/search/docs/appearance/google-discover)，核对 2026-10-18。
- **排序**：Discover 复用 Search 的许多信号和系统。旧内容只要对用户有帮助、与兴趣相关，也可能出现。
- **流量定位**：官方原话是 "less predictable or dependable"，并建议把 Discover 视为关键词搜索流量的补充。官方列出三类波动原因：用户兴趣变化、Discover 调整内容类型、Search 更新。官方没有说波动「与质量或发文频率无关」。
- **2026-02 Discover 核心更新**：
  - Status Dashboard 事件名 "February 2026 Discover update"，起止 2026-02-05 09:00 至 2026-02-27 02:00（US/Pacific）。来源：[事件页](https://status.search.google.com/incidents/mYbNTqV1ytDc2fA8hUz4)。
  - 博客标题 "Google's February 2026 Discover Core Update"，正文称 "February 2026 Discover core update"。来源：[Search Central 博客 2026-02-05](https://developers.google.com/search/blog/2026/02/discover-core-update)。
  - 三项目标：多展示用户所在国家网站的本地相关内容；减少煽情内容和标题党；多展示有专长网站的深度、原创、及时内容。
  - 专长按话题逐个判断。综合站与垂直站有同等机会。例如本地新闻站的园艺版块可以在园艺话题上有专长。
  - 先对美国英语用户发布，"in the months ahead" 扩展到所有国家和语言。扩展进度以 Status Dashboard 为准。
  - Search Engine Roundtable 称它是首个只针对 Discover 的核心更新（第三方）。
- **关注层（订阅）现状**：
  - 2025-09-17：用户可以在 Discover 里关注出版商和创作者。Discover 开始混入 X、Instagram 帖子和 YouTube Shorts。来源：[blog.google](https://blog.google/products-and-platforms/products/search/discover-updates-september-2025/)。
  - 2025-11-19：Google 从 Discover 文档删除旧版 Follow 功能（基于 feed 的 Chrome 实验）的指引，原因是 "The Follow feature is no longer shown in Google Discover"。来源：[文档更新日志](https://developers.google.com/search/updates)。
  - 2026-09-16：Search profile 文档上线。读者关注你的 Search profile 后，你在 Instagram、TikTok、YouTube、X、Facebook 和网站上的内容更可能出现在 Discover。主页地址格式 `https://profile.google.com/@handle`。来源：[Search profile 徽章文档](https://developers.google.com/search/docs/appearance/search-profiles)。
  - 2026-08-20：Google 宣布用户可在 Discover 卡片的三点菜单里用自己的话调整想看和不想看的内容。来源：[blog.google](https://blog.google/products-and-platforms/products/search/personalize-search-discover-news/)。
  - 结论：旧版 Follow 已退役，但「关注」以 Search profile 和 Preferred Sources 的形式继续存在。
- **Discover 里的 AI 摘要**：2025-07 Google 在美国 Discover 推出热门话题 AI 摘要（[TechCrunch 2025-07-15](https://techcrunch.com/2025/07/15/google-discover-adds-ai-summaries-threatening-publishers-with-further-traffic-declines/)，第三方）。2026-06 英国出现把多家出版商归组在 AI 摘要下的形态；Google 回应称用户可点开归组看到全部链接（[Press Gazette 2026-06-29](https://pressgazette.co.uk/platforms/google-ai-changes-could-deal-further-blow-to-publisher-discover-traffic/)，第三方）。同文引 NewzDash 数据：社交帖约占 Discover 信息流的四分之一。
- **行业流量数据（第三方，样本偏新闻站）**：
  - Chartbeat 数据（[Axios 2026-03-17](https://www.axios.com/2026/03/17/chartbeat-search-traffic-ai-chatbots)）：Google Search 占全球 pageviews 的周份额在 2024-11 达峰 10.6%，2026-02-02 降到 5.84%；同期 Discover 在 13.13% 至 17.04% 之间，始终高于 Search。2024-12 至 2025-12，Search 带来的 pageviews 降 34%，Discover 降 15%。两年内小出版商（日 PV 1,000 至 10,000）的搜索引荐降 60%，中型降 47%，大型降 22%。
  - Chartbeat《2026 Publisher Playbook》（[SEJ 2026-09-24](https://www.searchenginejournal.com/google-search-decline-publishers-chartbeat/590681/)）：2025-07 至 2026-07，Google Search 同比降 40.2%，Discover 同比降 34.3%。Search 占全网 pageviews 从 2024-07 的约 9% 降到 2026-07 的约 5%。报告未给站点数。
  - 本套件口径：Discover 目前是新闻站最大的 Google 入口之一，但它也在下滑。不要把它当业务基线。

## 二、Discover 优化要素（官方）

| 要素 | 官方规则（[Get on Discover](https://developers.google.com/search/docs/appearance/google-discover)） |
|---|---|
| 大图 | 宽度至少 1200px；总像素超过 300,000（例：1280×720）；16:9；用 `max-image-preview:large` 或 AMP 启用 |
| 首选图 | 用 schema.org 标记或 `og:image` 指定有代表性的大图。2026-03-02 起文档写明 Google 两种来源都用。不要用站点 logo；避免文字很多的图 |
| 标题与预览 | 不用误导或夸张的预览（标题、摘要、图片）制造点击；不隐瞒理解内容所需的关键信息；不用煽情手法；标题要概括内容本质 |
| 内容 | 契合当下兴趣、讲好故事或提供独特见解 |
| 页面体验 | 整体页面体验良好 |
| 会被过滤 | 求职申请、请愿、表单、代码仓库、无上下文的讽刺内容；SafeSearch 之外还会过滤令人震惊的内容 |

- **大图官方案例**（[Large Images 案例 2021-08-11](https://developers.google.com/search/case-studies/large-images-case-study)）：Kirbie's Cravings 启用 `max-image-preview:large` 后 Discover CTR 升 79%；Istoé CTR 升 30%，6 个月点击升 332%。这是两家出版商的自报结果，不是对照实验。
- **违规后果**：人工处置报告里有 "News and Discover policy violations" 一类。其中 "Misleading content (News and Discover)" 指用内容里没有的细节诱导点击。申请复审时要提供编辑流程已改正的证据。来源：[人工处置报告帮助](https://support.google.com/webmasters/answer/9044175)。
- **标题自查（本套件口径，对应官方红线）**：
  1. 只看标题，能说清发生了什么、涉及谁、结果是什么。必须点进去才知道核心事实，就是隐瞒关键信息。
  2. 去掉夸张情绪词（「震惊」「你绝对想不到」类）。
  3. 标题里的每个数字和引语，正文都能找到出处。
  4. 题图与正文主题一致，不用无关的刺激性图片。

## 三、新闻 SEO 基础层

- **Publisher Center 已无申请入口**：2024-04-25 起不能在 Publisher Center 新建 Google News publication。2025-03 下旬起，所有 publication 页面改为自动生成；Google News 不再使用 Publisher Center 提交的 RSS 或网址；logo 取站点 favicon，名称取 site name。符合内容政策的内容自动有资格。来源：[Publisher Center 公告](https://support.google.com/news/publisher-center/announcements/10146168)、[自动生成页面说明](https://support.google.com/news/publisher-center/answer/15898024)。
- **Google News 排名因素**：内容相关性、显著性（Prominence）、权威性、时效、可用性、地点与语言。来源：[Ranking within Google News](https://support.google.com/news/publisher-center/answer/9606702)。这是 Google News 的因素清单，不是「Top Stories 五要素」。
- **原创报道**：Google 有原创内容系统，让原创报道排在只引用它的内容前面。来源：[排名系统指南](https://developers.google.com/search/docs/appearance/ranking-systems-guide)。
- **Article 结构化数据**：没有必填属性。推荐 `author`、`datePublished`、`dateModified`、`headline`、`image`。图片建议给多张高分辨率图（宽×高至少 50K 像素），比例 16:9、4:3、1:1。`Article`、`NewsArticle`、`BlogPosting` 都受支持；现行文档没有 110 字符标题上限。来源：[Article 文档](https://developers.google.com/search/docs/appearance/structured-data/article)。
- **付费墙**：官方建议用 Flexible Sampling（metering 计量或 lead-in 导语试读）。付费内容用 `isAccessibleForFree: false` 加 `hasPart`（`WebPageElement` + `cssSelector`）标出，帮 Google 区分付费墙和 cloaking。来源：[Flexible Sampling](https://developers.google.com/search/docs/appearance/flexible-sampling)、[付费内容结构化数据](https://developers.google.com/search/docs/appearance/structured-data/paywalled-content)。
- **AMP 现状**：2026-07-01 起，Google Search 直接把用户带到出版商自己托管的 AMP 页面，不再经 AMP viewer、AMP Cache 或 signed exchange。AMP 内容像其他网页一样参与排名。来源：[文档更新日志 2026-07-01](https://developers.google.com/search/updates)。
- **Preferred Sources（偏好来源）**：
  - 时间线：2025-08-12 美国和印度上线（[blog.google](https://blog.google/products-and-platforms/products/search/preferred-sources/)）；2025-12-10 开始向全球英语用户推出（[blog.google](https://blog.google/products-and-platforms/products/search/tools-partnerships-web-ecosystem/)）；2026-04-30 覆盖所有 Google Search 支持的语言（[blog.google](https://blog.google/products-and-platforms/products/search/preferred-sources-language-expansion/)）；2026-05-27 文档加入 AI Overviews 与 AI Mode；2026-08-20 推出可嵌入的交互按钮。
  - 官方采用数据：约 9 万个不同来源被选（2025-12）；超过 20 万（2026-04-30）；超过 60 万（2026-08-20）。用户把站点设为偏好来源后，点击该站的概率约为两倍。
  - 资格：只有域名级和子域名级站点能出现在[来源偏好工具](https://www.google.com/preferences/source)里，子目录不行。要在 AI Mode 和 AI Overviews 里显示偏好标记，站点必须在 Search Console 里纳入 Search 生成式 AI 功能。来源：[Preferred sources 文档](https://developers.google.com/search/docs/appearance/preferred-sources)。
  - 接入方式：标准 JavaScript 按钮（推荐）、带自定义素材的高级 JavaScript、深链 `https://www.google.com/preferences/source?q=example.com`。

### News sitemap 规范（官方）

来源：[Create a News Sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/news-sitemap)，核对 2026-10-18。

- 只放最近两天内创建的文章。文章超过两天后，删掉该 URL，或删掉它的 `<news:news>` 标签。sitemap 因此变空时，Search Console 会给 Empty Sitemap 警告；官方说这不会造成问题。
- 每个 news sitemap 最多 1,000 个 `<news:news>`。超过就拆成多个 sitemap。
- 必填标签：`<news:news>`、`<news:publication>`（含 `<news:name>`、`<news:language>`）、`<news:publication_date>`、`<news:title>`。
- `<news:name>` 必须与文章在 news.google.com 上显示的名称完全一致（去掉括号内容）。Google News 现在用 site name 作 publication 名称。
- `<news:language>` 用 ISO 639 代码；简体中文写 `zh-cn`，繁体写 `zh-tw`。
- `<news:publication_date>` 用 W3C 格式。只写日期（`YYYY-MM-DD`）或写到时分秒带时区都可以。填文章首次发布时间，不填加入 sitemap 的时间。
- 更新现有 sitemap，不要每次新建。Google News 抓 news sitemap 的频率与抓站点其他部分相同。
- 通用 sitemap 规则同样适用：用绝对 URL；单文件不超过 50MB（未压缩）或 50,000 个 URL。来源：[Sitemaps 报告帮助](https://support.google.com/webmasters/answer/7451001)。
- 新闻站还需要常规 sitemap：news sitemap 只装两天内的文章，旧文靠常规 sitemap 被发现（本套件口径）。

**常见错误对照**：

| 错误 | 官方依据 | 怎么查 |
|---|---|---|
| 放入超过两天的旧文 | 只放最近两天的文章 | 脚本 `[curl1]` 列出超龄条目 |
| 混入 noindex 页面 | 页面索引报告原因 "URL marked 'noindex'"（[帮助](https://support.google.com/webmasters/answer/7440203)） | 脚本 `--sample N` 抽查 |
| 相对 URL | Sitemaps 报告提示改用绝对 URL | 脚本检查 `<loc>` |
| `news:name` 与 Google News 显示名不一致 | 必须完全一致 | 脚本 `--pub-name` 比对 |
| 超过 1,000 条不拆分 | 上限 1,000 个 `<news:news>` | 脚本 `[curl2]` |
| sitemap 读取失败 | Sitemaps 报告状态 "Couldn't fetch"，详情页 "Sitemap could not be read" | GSC「Sitemaps」报告 |

### News sitemap 验收命令

首选套件脚本（stdlib，零依赖）：

```bash
python3 scripts/news_sitemap_check.py --url https://example.com/news-sitemap.xml \
  --pub-name "Example Times" --sample 3 --json
# 退出码 0=无 FAIL，1=有 FAIL，2=sitemap 不可达或不可解析（要传具体文件，不传 index）
```

无法跑脚本时，用五条 curl 手查：

```bash
SM=https://example.com/news-sitemap.xml
# 1) 两天窗口：最新与最旧的发布时间都应在两天内
curl -s $SM | grep -o '<news:publication_date>[^<]*' | sort | sed -n '1p;$p'
# 2) 条数上限：<news:news> 应 ≤1000
curl -s $SM | grep -o '<news:news>' | wc -l
# 3) 必填项：三个数字应相等（每条都有 publication_date、title、name）
for t in news:publication_date news:title news:name; do curl -s $SM | grep -o "<$t>" | wc -l; done
# 4) sitemap 本身直接返回 200（本套件口径：不经重定向）
curl -s -o /dev/null -w '%{http_code}\n' $SM
# 5) 抽查文章页没有 noindex（meta 和 X-Robots-Tag 都看）
curl -sI https://example.com/news/article | grep -i 'x-robots-tag'; curl -s https://example.com/news/article | grep -io '<meta[^>]*noindex[^>]*>' || echo OK
```

### Fact Check（ClaimReview）现状

- 2025-06-12，Google 宣布在搜索结果里逐步停止支持 ClaimReview 等七类结构化数据（[博客](https://developers.google.com/search/blog/2025/06/simplifying-search-results)）。2025-09-09 起，这些类型从 Search Console 增强报告、Rich Results Test 和搜索外观筛选器中移除；Search Console API 支持到 2025-12。
- 文档横幅原话："We're phasing out support for ClaimReview markup in Google Search. However, this markup remains supported by the Factcheck Explorer Tool."（[Fact check 文档](https://developers.google.com/search/docs/appearance/structured-data/factcheck)，2026-09-08 更新）
- 本套件口径：不要为了 Google 搜索展示去写 ClaimReview。事实核查机构如需被 Fact Check Explorer 收录，按文档规范写：
  - 只核查他人提出的、可追溯来源的具体声明；不给自己的内容打核查标签。
  - 一页只放一个 `ClaimReview`；同一核查只放在一个页面。
  - 页面要有更正政策或报错渠道；政党、竞选团队、民选官员的网站不适用。
  - `claimReviewed` 尽量少于 75 个字符；`reviewRating` 的文字结论（`alternateName`）是展示用的值；数字评分要配文字对照表。
  - 工具：Fact Check Markup Tool 和 ClaimReview Read/Write API 可以增改删标记，要求操作者是该站 Search Console 的受限或完整用户；Claim Search API 查询与 Fact Check Explorer 相同的结果集（[Fact Check Tools API](https://developers.google.com/fact-check/tools/api)）。
  - 误用会触发人工处置，例如 "ClaimReview lacks reference, or reference does not match verdict"。
  - 官方说这次精简不影响网页排名。存量标记可以保留（套件看门表口径见 [deprecated-signals.md](../technical/deprecated-signals.md)）。

```json
{
  "@context": "https://schema.org",
  "@type": "ClaimReview",
  "url": "https://example.com/factcheck/claim-123",
  "claimReviewed": "某官员称该法案将把税收提高 20%",
  "itemReviewed": {
    "@type": "Claim",
    "author": { "@type": "Person", "name": "某官员" },
    "datePublished": "2026-10-01"
  },
  "author": { "@type": "Organization", "name": "Example Fact Check", "url": "https://example.com" },
  "reviewRating": {
    "@type": "Rating",
    "ratingValue": 1, "bestRating": 5, "worstRating": 1,
    "alternateName": "False"
  }
}
```

## 四、新闻站 GEO 与 AI 摘要的影响

**AI 摘要与零点击（第三方研究，引用时带样本）**：

- Ahrefs（[2026-02-04](https://ahrefs.com/blog/ai-overviews-reduce-clicks-update/)）：30 万关键词，GSC 汇总的桌面 CTR，2023-12 对比 2025-12。有 AI Overview 时，第一名页面的 CTR 低约 58%。2025-04 同方法测得 34.5%。
- SparkToro（[SEL 2026-06-09 转述](https://searchengineland.com/google-zero-click-searches-2026-study-479717)）：Similarweb 美国面板，2026-01 至 2026-04，68.01% 的 Google 搜索没有点击；AI Overviews 出现在 20% 以上的搜索中。不同年份数据源不同，不宜直接比较。
- Define Media Group（[SEL 2026-03-12 转述](https://searchengineland.com/google-ai-overviews-cut-search-clicks-report-471497)）：64 个站的 GSC 数据。到 2025-Q4，自然搜索点击比 AI Overviews 上线前的基线低 42%；同期突发新闻流量升 103%，Discover 升 30%。报告引 Ahrefs 数据：AI Overviews 只出现在约 15% 的新闻查询上。
- Press Gazette（[2026-08-21](https://pressgazette.co.uk/media-audience-and-business-data/media_metrics/traffic-to-10-biggest-us-news-websites-down-a-third-in-two-years/)）：美国前十新闻站两年流量降约三分之一；CNN 来自自然搜索的月访问从 1.244 亿降到 4,840 万（降 61%，2024-07 至 2026-07）。
- Piano（[基准更新 2026-04](https://www.piano.io/resources/benchmark-update-what-happened-to-search-traffic-in-2025)）：数百个出版商站，2025 年搜索流量降 36%，收入降 16%，总受众降 9%。
- Nieman Lab（[2026-07-22](https://www.niemanlab.org/2026/07/search-traffic-has-declined-so-much-that-some-publishers-are-considering-opting-out-of-google-entirely/)）：据 Semrush 数据，部分刊物 2025-06 至 2026-06 流量降 40% 以上；有出版商在评估完全退出 Google。
- 日本（[Web担当者Forum 2026-10-08](https://webtan.impress.co.jp/n/2026/10/08/53402)，Ahrefs 品牌雷达，2026-09-29 至 30 采样）：AI 引用总榜前十中有 3 个辞书或百科域名（Wikipedia 日语版第 1、weblio 第 9、コトバンク第 10）。

**AI 爬虫与授权**：

- BuzzStream（[研究](https://www.buzzstream.com/blog/publishers-block-ai-study/)，美英各 50 家头部新闻站）：79% 至少屏蔽一个训练爬虫；71% 至少屏蔽一个检索爬虫。
- Cloudflare：2025-07-01 推出一键屏蔽 AI 爬虫和 Pay Per Crawl（私测）（[博客](https://blog.cloudflare.com/introducing-pay-per-crawl/)）。2026-07-01 改为按 Search、Agent、Training 三类管理；2026-09-15 起新接入域名在有广告的页面默认屏蔽 Training 和 Agent，Search 默认放行（[博客](https://blog.cloudflare.com/content-independence-day-ai-options)）。
- Google 2025-12-10 宣布与多家新闻出版商试点新的商业合作，在 Google News 测试 AI 文章概览（[blog.google](https://blog.google/products-and-platforms/products/search/tools-partnerships-web-ecosystem/)）。
- 各 AI 爬虫的放行决策见 [ai-crawler-policy.md](../technical/ai-crawler-policy.md)。

**本套件口径（不是因果结论）**：

1. 先定立场：开放索引和引用，还是走授权。两条路不要混用。
2. 原创报道、独家数据、可核对的时间线，比可被摘要的常识内容更难被 AI 摘要替代（依据：上文 DMG 突发新闻数据与 Google 原创内容系统）。
3. 分引擎监测引用，不用一个引擎的结果代表全部（采样纪律见 [ai-citation-patterns.md](ai-citation-patterns.md)）。
4. 新闻站同时盯「收入/流量比」：Piano 数据显示收入降幅小于流量降幅。

## 五、监测

- **GSC Discover 效果报告**（[帮助](https://support.google.com/webmasters/answer/9216516)）：指标只有展示、点击、CTR；可按页面、国家、Discover 外观、日期分组；没有查询词和排名位置。数据覆盖近 16 个月；达到最低展示量才显示报告；包含 Chrome 上的 Discover 流量。表格最多 1,000 行；日期按太平洋时间；数据一般延迟 2 至 3 天；指标记在 canonical URL 上。
- **API**：Search Analytics API 的 `type` 参数支持 `discover` 和 `googleNews`（news.google.com 与 Google News App）；`news` 指 Search 的「新闻」标签。`discover` 和 `googleNews` 不支持 `aggregationType=byProperty`。来源：[searchanalytics.query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)。套件的 `gsc_api.py query` 目前没有 `--type` 参数，Discover 数据要直接调 API 或在 GSC 导出：

```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "https://www.googleapis.com/webmasters/v3/sites/sc-domain%3Aexample.com/searchAnalytics/query" \
  -d '{"startDate":"2026-07-01","endDate":"2026-09-30","type":"discover","dimensions":["page","date"],"rowLimit":25000}'
```

- **GA4**：GA4 没有单独的 Discover 渠道。Discover 的点击和展示以 GSC 为准（本套件口径）。
- **依赖度**：Discover 点击占全站自然流量超过 40% 就触发多渠道动作（本套件口径阈值）。

## 六、检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 文章模板有大图授权 | 随机抽 20 篇新文：`curl -s URL \| grep -io 'max-image-preview:[a-z]*'` | 20 篇都输出 `max-image-preview:large` 为通过；任一缺失为失败 |
| 首选图规格 | `curl -s URL \| grep -o 'og:image" content="[^"]*'` 取图，再用 `sips -g pixelWidth -g pixelHeight 图片`（macOS）或 ImageMagick `identify` 量尺寸 | 宽 ≥1200px 且宽×高 >300,000 为通过；用 logo 或文字图为失败 |
| og:image 是绝对 URL | `python3 scripts/head_check.py URL` 第 4 项 | 输出 ok 为通过；warn 为失败 |
| 标题不越红线 | 按第二节「标题自查」4 条逐篇过 | 4 条全过为通过 |
| News sitemap 合规 | `python3 scripts/news_sitemap_check.py --url SITEMAP --pub-name "站名" --sample 3` | 退出码 0 为通过；1 或 2 为失败 |
| Sitemap 读取正常 | GSC「Sitemaps」报告 | 状态 Success 为通过；"Couldn't fetch" 为失败 |
| 新闻 URL 未被 noindex | GSC「网页」索引报告筛 news 目录 | 无 "URL marked 'noindex'" 为通过 |
| 无 News/Discover 人工处置 | GSC「人工处置」报告 | 显示无问题为通过；出现 "News and Discover policy violations" 为失败 |
| Discover 依赖度 | GSC Discover 报告与 Search 报告点击对比（或上面 API 命令） | Discover 占比 ≤40% 为通过（本套件口径） |
| 偏好来源入口 | 在[来源偏好工具](https://www.google.com/preferences/source)搜自己的域名；页面上有按钮或深链 | 能搜到且站内有入口为通过 |
| 付费墙标记 | `curl -s URL \| grep -o '"isAccessibleForFree":[^,}]*'` | 付费文章输出 `false` 且有 `hasPart` 为通过 |
| AI 爬虫立场与 robots 一致 | `python3 scripts/robots_posture.py https://example.com/robots.txt --json` | 实际放行或屏蔽与第四节所定立场一致为通过 |

## 七、Discover 掉量排查

1. **先看是不是更新**：在 [Status Dashboard 排名历史](https://status.search.google.com/products/rGHU1u87FJnkP6W2GwMi/history) 找同期的 Discover 更新或核心更新。官方说更新期间流量可能波动；核心更新的通用建议见 [core updates 文档](https://developers.google.com/search/docs/appearance/core-updates)。
2. **再看人工处置**：GSC「人工处置」里有没有 "News and Discover policy violations"。
3. **查模板回归**：改版后 `max-image-preview:large` 或 `og:image` 丢失，会让大图资格消失（用第六节前三条命令查）。
4. **对比 Search 与 Discover**：两者同跌，先按站点质量排查；只有 Discover 跌，先看兴趣变化和内容类型调整，这两项都是官方列出的波动原因。
5. **新站或新文完全不出现**：Discover 没有提交入口。先确认页面已被索引、图片合规。
6. **不要做的事（本套件口径）**：不为 Discover 删旧文（旧内容仍可被推荐）；不向客户承诺 Discover 流量（官方定位是补充渠道）。

## 来源

- 官方：[Get on Discover](https://developers.google.com/search/docs/appearance/google-discover)；[2026-02 Discover 核心更新博客](https://developers.google.com/search/blog/2026/02/discover-core-update)；[Status Dashboard 事件](https://status.search.google.com/incidents/mYbNTqV1ytDc2fA8hUz4)；[文档更新日志](https://developers.google.com/search/updates)；[Search profile 文档](https://developers.google.com/search/docs/appearance/search-profiles)；[Preferred sources 文档](https://developers.google.com/search/docs/appearance/preferred-sources)；[Large Images 案例](https://developers.google.com/search/case-studies/large-images-case-study)；[robots meta 规范](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)；[News sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/news-sitemap)；[Article](https://developers.google.com/search/docs/appearance/structured-data/article)；[Fact check](https://developers.google.com/search/docs/appearance/structured-data/factcheck)；[简化搜索结果博客](https://developers.google.com/search/blog/2025/06/simplifying-search-results)；[Flexible Sampling](https://developers.google.com/search/docs/appearance/flexible-sampling)；[付费内容](https://developers.google.com/search/docs/appearance/structured-data/paywalled-content)；[排名系统指南](https://developers.google.com/search/docs/appearance/ranking-systems-guide)；[Ranking within Google News](https://support.google.com/news/publisher-center/answer/9606702)；[Publisher Center 公告](https://support.google.com/news/publisher-center/announcements/10146168)；[Discover 效果报告](https://support.google.com/webmasters/answer/9216516)；[人工处置报告](https://support.google.com/webmasters/answer/9044175)；[searchanalytics.query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)；blog.google（Discover 2025-09、Preferred Sources 三篇、个性化 2026-08-20）。
- 第三方：Axios/Chartbeat、SEJ/Chartbeat Playbook、Ahrefs、SparkToro（SEL）、Define Media Group（SEL）、Press Gazette、Piano、Nieman Lab、BuzzStream、Cloudflare、TechCrunch、Web担当者Forum/Ahrefs（链接见正文）。WordPress 插件参考：[10up Simple Google News Sitemap](https://github.com/10up/simple-google-news-sitemap)（只生成两天内文章）。
- 2026-10-18 删除的旧说法（无一手来源或与来源不符）见证据账本 C3：Discover 流量占比 68–70%、51%→27%、印度 80–90%、Follow 试点 54 家、Bring/wpspeedopt/Adsterra 服务商案例、「发文频率不影响 Discover」「GSC API 不返回 Discover」「Top Stories 五要素」等。
