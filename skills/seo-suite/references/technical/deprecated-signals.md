# 过时信号看门表(官方已停用/勿再推荐清单)

> 建立于 2026-10-10,逐行重核于 2026-10-21(每行都打开了一手来源,原先标"占位"的链接已全部回填)。**使用规则:凡要就 schema/rich result/CWV/GSC 报表/GBP 给建议,动笔前先查此表;发现套件内文档与此表冲突 → 以本表口径改该文档,并跑 `tests/test_canonical_facts.py`(已知错误陈述的回归看门;本表自身也在其扫描范围内,勿写出会命中的句子)。** 建议每季度重核一次,并刷新"最后核验"列。
> 分工:本表只管三类信号——**已停用(有退役时间戳)、已移除(工具/报表下线)、从未存在(第三方幻觉名目)**;活信号怎么用见专文:CWV 见 [cwv-playbook.md](cwv-playbook.md)、schema 替换细则与工具链深读见 [schema-examples.md](schema-examples.md)(其"弃用类型替换决策"节与本表互为镜像)、渲染与 AI 爬虫执行口径见 [rendering-seo.md](rendering-seo.md) 与 [ai-crawler-policy.md](ai-crawler-policy.md)。
> 时间戳来源:Google Search Central [文档更新记录](https://developers.google.com/search/updates)(下称"更新记录")、Search Central 博客、Search Console 帮助中心。"公告日"与"移除日"不同时,两个日期都写。

## 一、富结果 / schema 家族

| 信号 | 官方动作(时间戳) | 处置口径 | 验证命令 / 一手来源 | 最后核验 |
|---|---|---|---|---|
| FAQPage 富结果 | 先收窄到"知名的政府和健康权威站",**后来不再出现在 Google 搜索**,文档已删除(各日期见[事实表](../overview/facts.md#rich-results)) | 存量标记审计标 **Info、不标 Critical**;不建议删除(2023 公告原话:不用主动移除,没用到的结构化数据不会造成问题);不为 SERP 再加这类标记;真实用户提交问答的页面用 QAPage | [2023 年公告](https://developers.google.com/search/blog/2023/08/howto-faq-changes)、[更新记录](https://developers.google.com/search/updates)、[Search Console 数据异常页](https://support.google.com/webmasters/answer/6211453)(写明停展后 FAQ 展示下降会体现在效果报告) | 2026-10-21 |
| HowTo 富结果 | 先限定只在桌面显示,后来桌面和移动端都不再显示,文档已删除(日期见[事实表](../overview/facts.md#rich-results)) | 步骤照常用有序列表/清晰 H2 承载;HowTo schema 本身合法,只是 Google 不再给展示位 | [2023 年公告](https://developers.google.com/search/blog/2023/08/howto-faq-changes)、[更新记录](https://developers.google.com/search/updates) | 2026-10-21 |
| Course Info·Estimated Salary·Learning Video·Claim Review·Special Announcement·Vehicle Listing(及 Book Actions 公告) | **2025-06-12 公告停止支持**;**2025-09-09 起**从 Search Console 富结果报告、Rich Results Test 和搜索外观筛选中移除;Search Console API 保留到 2025-12;批量导出的对应字段 2025-10-01 起为 `NULL`。更新记录 2025-09-09 删除其中五类(不含 Claim Review)的文档 | 存量标 Info;不再为富结果投入;被问"那用什么"见下方替换决策表。**Book Actions 例外**:2025-11-05 官方撤掉了它的弃用横幅("仍有功能在用该标记") | [2025-06-12 公告及 2025-09-08 更新](https://developers.google.com/search/blog/2025/06/simplifying-search-results)、[更新记录](https://developers.google.com/search/updates) | 2026-10-21 |
| SpecialAnnouncement | 更新记录 2025-04-23:**2025-07-31 起弃用** | 不再使用;有时限的公告用 Event,常规公告用 Article | [更新记录](https://developers.google.com/search/updates) | 2026-10-21 |
| PracticeProblem | 更新记录 2025-11-05 弃用通知;2026-01 起 Search Console 富结果报告、Rich Results Test、搜索外观筛选移除;2026-01-06 删除文档(Search Console API 保留到 2026-01) | 不再使用;教育内容用正文分步 + VideoObject | [更新记录](https://developers.google.com/search/updates) | 2026-10-21 |
| **Dataset——未死,勿误杀** | 更新记录 2025-11-05 澄清:Dataset 结构化数据**只供 Dataset Search 使用,不用于 Google 搜索** | 数据门户/研究库继续标记——这与"Google 忽略某字段"是两回事 | [Dataset 文档](https://developers.google.com/search/docs/appearance/structured-data/dataset)、[Dataset Search](https://datasetsearch.research.google.com) 检索自家数据集验证收录 | 2026-10-21 |
| **QAPage——勿误伤** | 通道仍开放;更新记录 2026-03-24 为 Discussion Forum 与 QAPage 新增支持属性(评论线程结构) | 真实用户提交问答的页面用它,别套 FAQPage | [QAPage 文档](https://developers.google.com/search/docs/appearance/structured-data/qapage)、[更新记录](https://developers.google.com/search/updates) | 2026-10-21 |
| 验证工具口径 | Rich Results Test 与 Search Console 富结果报告 **2025-09-09** 起不再报告上述退役类型(Practice Problem 为 2026-01) | 工具里看不到 ≠ 标记非法;存废判断以本表时间戳为准,不以工具输出为准 | [2025-09-08 更新](https://developers.google.com/search/blog/2025/06/simplifying-search-results) | 2026-10-21 |

### 替换决策表(被问到弃用类型时给什么)

| 已退役 | 替代做法 |
|---|---|
| ClaimReview | 无 SERP 替代;新闻场景用 Article + dateline(datePublished/dateModified);Fact Check Explorer 仍在消费该标记,事实核查出版商可保留存量(本套件口径) |
| EstimatedSalary | JobPosting + baseSalary(单职位口径) |
| LearningVideo | VideoObject(视频富结果通道仍开放) |
| CourseInfo(单课详情) | Course List 轮播(Course + ItemList,仍支持) |
| VehicleListing | Product + Offer(带车辆属性;仅线上在售时) |
| SpecialAnnouncement | 有时限用 Event;否则 Article/WebPage |
| HowTo(为 SERP) | 无;文章结构 + 有序列表,H2 写清步骤 |
| FAQPage(为 SERP) | 无;真实用户提交问答页用 QAPage |

(与 [schema-examples.md](schema-examples.md)"弃用类型替换决策"节互为镜像,字段级细则以那边为准。)

## 二、CWV 家族

| 信号 | 官方动作(时间戳) | 处置口径 | 验证命令 / 一手来源 | 最后核验 |
|---|---|---|---|---|
| FID | **2024-03-12** 被 INP 正式替代为核心指标;CrUX 发布说明预告 **2024-09-09** 起从 Chrome 工具(含 CrUX)移除,2024-09-10 的发布说明确认已从 CrUX 移除(CrUX API 与 BigQuery 的 8 月数据为最后一批) | 任何现行建议不引用 FID;历史数据对照须注明"2024-03 前" | 命令(需自备 API key):`curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=<URL>&key=<KEY>" \| jq '.loadingExperience.metrics \| keys'` → 输出无 first-input-delay。来源:[web.dev INP 成为核心指标](https://web.dev/blog/inp-cwv-march-12)、[CrUX 发布说明](https://developer.chrome.com/docs/crux/release-notes) | 2026-10-21 |
| VSI(Visual Stability Index) | **从未存在**——第三方幻觉名目(无官方文档可引;不存在性无法用单页证明,以现行三指标页为准) | 勿引用;视觉稳定性看 CLS | [web.dev Web Vitals](https://web.dev/articles/vitals) 现行核心指标只有 LCP/INP/CLS | 2026-10-21 |
| CWV 2.0 | **从未存在**——官方从未宣布过 "Core Web Vitals 2.0" | 勿引用;现行口径 = LCP/INP/CLS(+TTFB 辅助),见 [cwv-playbook.md](cwv-playbook.md) 第一节 | [web.dev Web Vitals](https://web.dev/articles/vitals) | 2026-10-21 |
| Engagement Reliability | **从未存在**——幻觉名目 | 勿引用 | 同上 | 2026-10-21 |
| LCP 阈值 | Good 档官方口径没变,**未降 2.0s**("2 秒阈值"一说系第三方幻觉);现行阈值见[事实表](../overview/facts.md#cwv),按 p75 | 引用现行阈值表;跨年对比不换阈值 | [web.dev Web Vitals](https://web.dev/articles/vitals)(原文摘录见[事实表](../overview/facts.md#cwv)) | 2026-10-21 |
| Lighthouse PWA 类别 | Lighthouse 12 起移除 PWA 类别(不再计分) | PWA 审计不再引用 Lighthouse PWA 分;PWA 检查用专用工具 | [Lighthouse 12.0.0 发布说明](https://github.com/GoogleChrome/lighthouse/releases/tag/v12.0.0)("PWA Category Removal") | 2026-10-21 |
| 移动 lab CPU throttling | **2024-12-05** PageSpeed Insights 调整 CPU 节流系数,移动端 lab 的 TBT 通常升高;字段数据和桌面分数不受影响 | **TBT 等 lab 指标不可跨该日期前后直接比较**(趋势断点;要比先归一) | [PageSpeed Insights 发布说明](https://developers.google.com/speed/docs/insights/release_notes) | 2026-10-21 |

## 三、GSC / GA4

| 信号 | 官方动作(时间戳) | 处置口径 | 验证命令 / 一手来源 | 最后核验 |
|---|---|---|---|---|
| Page Experience 报告 | **2024-11-18** Search Central 官方账号宣布移除(它只汇总 CWV 与 HTTPS 两份报告,两份继续保留);具体下线日未查到官方原文 | 信号未死——改看 CWV 报告 + HTTPS 报告;审计与建议不再引用该报告名 | [Search Central LinkedIn 帖](https://www.linkedin.com/posts/googlesearchcentral_were-removing-the-page-experience-report-activity-7264284084145713152-rWCg)(帖子 ID 时间戳 2024-11-18 UTC)、[SER 报道 2024-11-19](https://www.seroundtable.com/google-search-console-page-experience-report-gone-38436.html)(第三方) | 2026-10-21 |
| impressions/CTR/position 记录错误 | [GSC 数据异常期](../overview/facts.md#gsc-anomaly)记录错误:展示、CTR、平均位置不准;**clicks 不受影响**;错误已修复,修复后展示数会下降 | 跨该窗口的趋势对比必须加注断代;窗口重叠的分析里 clicks 是唯一可信指标(与 [seo-drift-monitoring.md](../monitoring/seo-drift-monitoring.md) 的 data_regime_breaks 互认) | [Search Console 数据异常页](https://support.google.com/webmasters/answer/6211453) | 2026-10-21 |
| URL Inspection API `mobileUsabilityResult` | 字段标为 deprecated(Mobile Usability 报告与 Mobile-Friendly Test 已于 2023-12 退役) | API 消费方移除依赖;移动体验问题并入 CWV 与常规移动检查 | [UrlInspectionResult 参考](https://developers.google.com/webmaster-tools/v1/urlInspection.index/UrlInspectionResult)(原文:This item is deprecated) | 2026-10-21 |
| AI Mode 流量口径 | 2025-06 起 AI Mode 数据并入 Search Console 效果报告的 Web 搜索总数(更新记录)。已对全球开放([日期](../overview/facts.md#gsc-genai))的独立 Generative AI 效果报告(Search 与 Discover),只报**展示**(页面、国家、设备、日期),不报点击 | 点击/会话仍拆不出 AI Mode;展示可用 Generative AI 报告(没有该报告的站点看不到);AI 流量估算走 referrer 清单 + 渠道组正则 + 服务器日志三源法(见 [geo-platform-differences.md](../content/geo-platform-differences.md)) | [更新记录 2025-06](https://developers.google.com/search/updates)、[Generative AI 效果报告公告](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports) | 2026-10-21 |
| GA4 默认渠道组"AI Assistant" | 官方定义:来自 ChatGPT、Gemini、Deepseek、Copilot、Grok 等的访问,**不含** Google AI Overviews 与 AI Mode | 别只看该渠道报 AI 流量(漏掉 Google 的 AI 入口,且无 referrer 的访问会落入 Direct);referrer 正则与日志互证(同上三源法) | [GA4 默认渠道组](https://support.google.com/analytics/answer/9756891) | 2026-10-21 |

## 四、其他(GBP / sitemap / Indexing API)

| 信号 | 官方动作(时间戳) | 处置口径 | 验证命令 / 一手来源 | 最后核验 |
|---|---|---|---|---|
| GBP chat 与 call history | **2024-07-31** 下线(官方帮助:此日起这两项功能从商家资料中移除) | 客服入口收敛到网站自有渠道/电话直连;报告与审计不再检查 chat 指标 | [Google 商家资料帮助](https://support.google.com/business/answer/14919056) | 2026-10-21 |
| sitemap `<priority>` | Google 忽略 | 可不写;写了对排名与抓取调度无作用;lastmod(真实)才是被参考的字段 | [构建 sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)(原文:Google ignores `<priority>` and `<changefreq>` values) | 2026-10-21 |
| sitemap `<changefreq>` | 同上,Google 忽略 | 抓取调度看抓取历史 + lastmod + 内外链信号,不看该字段 | 同上 | 2026-10-21 |
| Indexing API 适用面 | 官方限 **JobPosting 与 BroadcastEvent**(嵌 VideoObject)两类 | 普通页面少量用 URL Inspection、批量靠 sitemap + 内链;给全站 URL 调 API 无效果且耗配额(默认每天 200 次发布请求) | [Indexing API 快速入门](https://developers.google.com/search/apis/indexing-api/v3/quickstart)、[配额](https://developers.google.com/search/apis/indexing-api/v3/quota-pricing) | 2026-10-21 |

## 四B、搜索功能与工具下线(2026-10-21 新增)

本节每行都有一手来源。表中"处置"列是本套件口径。

| 信号 | 官方动作(时间戳) | 处置口径 | 一手来源 | 最后核验 |
|---|---|---|---|---|
| Sitemap ping 端点 | **2023-06-26 宣布弃用**,约 6 个月后停止工作,请求返回 404 | 不再调用 ping;提交 sitemap 用 robots.txt 的 `Sitemap:` 行和 Search Console | [Search Central 博客 2023-06-26](https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping) | 2026-10-21 |
| URL 参数工具 | **2022-03-28 宣布一个月后下线**;官方称约 1% 的配置对抓取有用 | 参数治理只在站内做(见 [redirects-canonical.md](redirects-canonical.md) 第五节) | [Search Central 博客 2022-03-28](https://developers.google.com/search/blog/2022/03/url-parameters-tool-deprecated) | 2026-10-21 |
| Mobile-Friendly Test 与 Mobile Usability 报告 | 2023-12 退役 | 移动检查用 Lighthouse、PageSpeed Insights、CrUX 与网址检查(见 [mobile-seo.md](mobile-seo.md)) | [Search Central 博客注记](https://developers.google.com/search/blog/2016/05/a-new-mobile-friendly-testing-tool)(原文:As of December 2023, the Mobile Friendly Test has been retired) | 2026-10-21 |
| 国际定位报告(International Targeting) | 已弃用 | hreflang 返回链接错误改用爬虫工具或 [hreflang_cluster.py](../../scripts/hreflang_cluster.py) 查 | [Search Console 帮助](https://support.google.com/webmasters/answer/12474899) | 2026-10-21 |
| sitelinks 搜索框 | 更新记录 **2024-11-29** 删除文档,理由"该功能在 Google 搜索中不再可用" | 存量 WebSite + SearchAction 标记无害,不再为它投入 | [更新记录](https://developers.google.com/search/updates) | 2026-10-21 |
| 缓存链接与 `cache:` 运算符 | 更新记录 2024-09-24 删除 `cache:` 运算符文档("不再有效");2024-10-02 把 `noarchive` 移到历史参考("缓存链接不再可用") | 不必删 `noarchive`(其他搜索引擎和服务可能在用);审计不再把"缓存页"当检查项 | [更新记录](https://developers.google.com/search/updates) | 2026-10-21 |
| robots.txt 里的 `noindex` | 自 **2019-09-01** 不再生效 | 去索引用 meta robots 或 `X-Robots-Tag`(见 [robots-txt-reference.md](robots-txt-reference.md)) | [Google 公告 2019-07-02](https://developers.google.com/search/blog/2019/07/a-note-on-unsupported-rules-in-robotstxt) | 2026-10-21 |
| `rel=prev/next` | Google 不再使用;其他搜索引擎可能仍用 | 已部署的保留无害;每页自引用 canonical、唯一 URL(见 [redirects-canonical.md](redirects-canonical.md) 2.4) | [分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading) | 2026-10-21 |
| Discover 的 Follow 功能 | 更新记录 **2025-11-19** 删除相关指引,理由"该功能不再显示在 Discover" | 审计与建议不再包含 Follow 入口 | [更新记录](https://developers.google.com/search/updates) | 2026-10-21 |

## 五、与回归看门的联动

- 上表口径已固化为 `tests/test_canonical_facts.py` 的 `WRONG_STATEMENTS` 正则清单(FID-as-current、faqpage-for-serp、cwv-2.0、vsi-hallucination、engagement-reliability-hallucination、lcp-2.0s-threshold、sitemap-priority-ranking、changefreq-crawl-rate、ai-crawlers-no-js-absolute、gbp-chat-still-live、pagerank-next、pr-sculpting、indexing-api-any-url、page-experience-report-alive、schema-ai-citation-uplift(此项不属本表三类,口径见 [geo-evidence.md](../content/geo-evidence.md) 第二节第 2 条)等 ID):`python3 tests/test_canonical_facts.py` 单跑,或随 `python3 tests/run_tests.py` 全量。
- 第四B节的八行目前**没有**对应正则。需要机检时,按下一条流程补。
- 新增"官方已停用"条目的流程:本表加行(时间戳 + 一手来源链接 + 验证方式)→ 需要机检的补进 `WRONG_STATEMENTS`(正则必须同时通过其 bad/ok 自检样例)→ 两个测试都绿才算落账。

## 检查清单(使用本表前后)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 要写的建议涉及某个富结果、报表、工具或指标时,先在本表查到该行 | 在本文件里搜关键词 | 通过:查到,按"处置口径"写。失败:没有这一行——先去更新记录核实,再决定要不要加行 |
| 2 | 套件文档没有写出已知错误陈述 | `python3 tests/test_canonical_facts.py` | 通过:退出码 0。失败:按它打印的 文件:行号 改文档 |
| 3 | 新增行带一手来源 | 每行"一手来源"列有可打开的链接 | 失败:写"占位"或只有第三方链接(第三方只能作旁证,须标注) |
| 4 | 时间戳区分公告日与移除日 | 对照更新记录条目的"What / Why" | 失败:把公告日当移除日(或反过来) |
| 5 | 每季度重核 | 逐行打开来源,刷新"最后核验" | 失败:来源 404 或口径变了而本行没改 |

## 来源

- 一手:Google Search Central [文档更新记录](https://developers.google.com/search/updates)、[博客](https://developers.google.com/search/blog)(2019-07、2022-03、2023-06、2023-08、2025-06、2026-06 各篇,链接见各行)、Search Console 帮助([数据异常页](https://support.google.com/webmasters/answer/6211453)、[国际定位](https://support.google.com/webmasters/answer/12474899))、[web.dev Web Vitals](https://web.dev/articles/vitals) 与 [INP 公告](https://web.dev/blog/inp-cwv-march-12)、[CrUX 发布说明](https://developer.chrome.com/docs/crux/release-notes)、[PageSpeed Insights 发布说明](https://developers.google.com/speed/docs/insights/release_notes)、[Lighthouse 12.0.0 发布说明](https://github.com/GoogleChrome/lighthouse/releases/tag/v12.0.0)、[GA4 默认渠道组](https://support.google.com/analytics/answer/9756891)、[Google 商家资料帮助](https://support.google.com/business/answer/14919056)、[Indexing API 文档](https://developers.google.com/search/apis/indexing-api/v3/quickstart)。
- 第三方(只作旁证):[Search Engine Roundtable 2024-11-19](https://www.seroundtable.com/google-search-console-page-experience-report-gone-38436.html)。
- 套件内互认:替换决策与工具链时间线以 [schema-examples.md](schema-examples.md) 的深读记录为准;CWV 现行口径见 [cwv-playbook.md](cwv-playbook.md);GSC 断代窗口见 [validation-guide.md](validation-guide.md) 与 [seo-drift-monitoring.md](../monitoring/seo-drift-monitoring.md);FID→INP 的禁引口径见 [validation-guide.md](validation-guide.md)。
