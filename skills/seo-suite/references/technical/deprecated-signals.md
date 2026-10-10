# 过时信号看门表(官方已停用/勿再推荐清单)

> 建立于 2026-10-10,每条含官方动作时间戳、处置口径、验证方式与最后核验日期。**使用规则:凡要就 schema/rich result/CWV/GSC 报表/GBP 给建议,动笔前先查此表;发现套件内文档与此表冲突 → 以本表口径改该文档,并跑 `tests/test_canonical_facts.py`(已知错误陈述的回归看门;本表自身也在其扫描范围内,勿写出会命中的句子)。** 标注"占位"的 URL 在下次核验(建议每季度)回填,并刷新"最后核验"列。
> 分工:本表只管三类信号——**已停用(有退役时间戳)、已移除(工具/报表下线)、从未存在(第三方幻觉名目)**;活信号怎么用见专文:CWV 见 [cwv-playbook.md](cwv-playbook.md)、schema 替换细则与工具链深读见 [schema-examples.md](schema-examples.md)(其"弃用类型替换决策"节与本表互为镜像)、渲染与 AI 爬虫执行口径见 [rendering-seo.md](rendering-seo.md) 与 [ai-crawler-policy.md](ai-crawler-policy.md)。

## 一、富结果 / schema 家族

| 信号 | 官方动作(时间戳) | 处置口径 | 验证命令 / 一手来源 | 最后核验 |
|---|---|---|---|---|
| FAQPage 富结果 | SERP 富结果 **2026-05-07 起全站退役**(2023-08 先收窄到政府/健康权威站,2026-05 归零) | 存量标记审计标 **Info、不标 Critical**;不建议删除(对其他消费者无害);不为 SERP 再加这类标记;真实用户提交问答的页面用 QAPage | Rich Results Test 输入存量页已不报告该类型;[官方 faqpage 文档](https://developers.google.com/search/docs/appearance/structured-data/faqpage)(一手) | 2026-10-10 |
| HowTo 富结果 | 2023-08 官方公告,2023-09 起 SERP 停展 | 步骤照常用有序列表/清晰 H2 承载;HowTo schema 本身合法,只是 Google 不再给展示位 | [官方变更公告](https://developers.google.com/search/blog)(URL 占位,2023-08"FAQ 与 HowTo rich results"篇) | 2026-10-10 |
| Course(CourseInfo)·EstimatedSalary·LearningVideo·ClaimReview·VehicleListing | **2025-06-12** 起不再产生富结果;2025-09-09 起从 GSC 富结果报告与 Rich Results Test 移除(SC API 拖到 2025-12) | 存量标 Info;不再为富结果投入;被问"那用什么"见下方替换决策表 | 官方 retiring 公告(URL 占位)+ GSC 增强报告类型清单 | 2026-10-10 |
| SpecialAnnouncement | 2025-07 退役(疫情期专用类型) | 不再使用;有时限的公告用 Event,常规公告用 Article | 同上(占位) | 2026-10-10 |
| PracticeProblem | 2025-11-05 弃用通知;2026-01 起工具支持移除、2026-01-06 文档删除 | 不再使用;教育内容用正文分步 + VideoObject | 同上(占位) | 2026-10-10 |
| **Dataset——未死,勿误杀** | 未退役(常规 SERP 本无此富结果) | **Dataset Search 仍在消费**:数据门户/研究库继续标记——这与"Google 忽略某字段"是两回事 | [datasetsearch.research.google.com](https://datasetsearch.research.google.com) 检索自家数据集验证收录 | 2026-10-10 |
| **QAPage——勿误伤** | 通道仍开放(2026-03-24 还扩展了评论线程属性) | 真实用户提交问答的页面用它,别套 FAQPage | 官方 qapage 文档(一手,URL 见 [schema-examples.md](schema-examples.md) 来源节) | 2026-10-10 |
| 验证工具口径 | Rich Results Test 与 GSC 富结果报告 **2025-09-09** 起不再报告上述退役类型 | 工具里看不到 ≠ 标记非法;存废判断以本表时间戳为准,不以工具输出为准 | GSC 增强报告类型清单(占位) | 2026-10-10 |

### 替换决策表(被问到弃用类型时给什么)

| 已退役 | 替代做法 |
|---|---|
| ClaimReview | 无 SERP 替代;新闻场景用 Article + dateline(datePublished/dateModified);Fact Check Explorer 仍在消费该标记,事实核查出版商可保留存量 |
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
| FID | **2024-03-12** 被 INP 正式替代为核心指标;**2024-09-09** 起从 CrUX/PSI 字段数据移除 | 任何现行建议不引用 FID;历史数据对照须注明"2024-03 前" | `curl -s "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=<URL>&key=<KEY>" \| jq '.loadingExperience.metrics \| keys'` → 输出无 first-input-delay;[web.dev/articles/inp](https://web.dev/articles/inp)(一手) | 2026-10-10 |
| VSI(Visual Stability Index) | **从未存在**——第三方幻觉名目 | 勿引用;视觉稳定性看 CLS | [web.dev/articles/cls](https://web.dev/articles/cls) 通篇无此名(占位核验) | 2026-10-10 |
| CWV 2.0 | **从未存在**——官方从未宣布过 "Core Web Vitals 2.0" | 勿引用;现行口径 = LCP/INP/CLS(+TTFB 辅助),见 [cwv-playbook.md](cwv-playbook.md) 第一节 | [web.dev/articles/vitals](https://web.dev/articles/vitals)(一手) | 2026-10-10 |
| Engagement Reliability | **从未存在**——幻觉名目 | 勿引用 | 同上 | 2026-10-10 |
| LCP 阈值 | Good 档官方口径仍为 ≤2.5s,**未降 2.0s**("2 秒阈值"一说系第三方幻觉) | 引用现行阈值表;跨年对比不换阈值 | [web.dev/articles/lcp](https://web.dev/articles/lcp)(一手) | 2026-10-10 |
| Lighthouse PWA 类别 | Lighthouse 12 起移除 PWA 类别(不再计分) | PWA 审计不再引用 Lighthouse PWA 分;PWA 检查用专用工具 | [github.com/GoogleChrome/lighthouse release notes](https://github.com/GoogleChrome/lighthouse/releases)(占位) | 2026-10-10 |
| 移动 lab CPU throttling | 2024-12-05 PSI/Lighthouse 移动 lab CPU 节流档位调整 | **TBT 等 lab 指标不可跨该日期前后直接比较**(趋势断点;要比先归一) | Lighthouse/PSI changelog(占位) | 2026-10-10 |

## 三、GSC / GA4

| 信号 | 官方动作(时间戳) | 处置口径 | 验证命令 / 一手来源 | 最后核验 |
|---|---|---|---|---|
| Page Experience 报告 | **2024-11-18** 从 GSC 移除(它只是 CWV+HTTPS 两报告的汇总视图) | 信号未死——改看 CWV 报告 + HTTPS 报告;审计与建议不再引用该报告名 | GSC 左栏报告清单(占位) | 2026-10-10 |
| impressions/CTR/position 记录错误 | **2025-05-13 ~ 2026-04-27** GSC 日志错误,三者不可靠(仅向前修复、无回填;**clicks 不受影响**) | 跨该窗口的趋势对比必须加注断代;窗口重叠的分析里 clicks 是唯一可信指标(与 [seo-drift-monitoring.md](../monitoring/seo-drift-monitoring.md) 的 data_regime_breaks 互认) | 官方公告(占位:developers.google.com/search/blog/2025/) | 2026-10-10 |
| URL Inspection API `mobileUsabilityResult` | 字段弃用(GSC 移动可用性报告先已下线) | API 消费方移除依赖;移动体验问题并入 CWV 与常规移动检查 | Search Console API v3 字段文档(占位) | 2026-10-10 |
| AI Mode 流量口径 | 并入 Web 搜索 totals,官方不提供拆分 | GSC 里拆不出单独的 AI Mode 会话/点击;AI 流量估算走 referrer 清单 + 渠道组正则 + 服务器日志三源法(见 [geo-platform-differences.md](../content/geo-platform-differences.md)) | GSC 效果报告维度说明(占位) | 2026-10-10 |
| GA4 "AI Assistants" 渠道 | 系统性低估——渠道定义不含 Google AIO/AI Mode | 别只看该渠道报 AI 流量;referrer 正则与日志互证(同上三源法) | GA4 渠道定义文档(占位) | 2026-10-10 |

## 四、其他(GBP / sitemap / Indexing API)

| 信号 | 官方动作(时间戳) | 处置口径 | 验证命令 / 一手来源 | 最后核验 |
|---|---|---|---|---|
| GBP chat 与 call history | **2024-07-31** 下线 | 客服入口收敛到网站自有渠道/电话直连;报告与审计不再检查 chat 指标 | [help.google.com/business](https://help.google.com/business)(占位) | 2026-10-10 |
| sitemap `<priority>` | Google 长期忽略(官方明示) | 可不写;写了对排名与抓取调度无作用;lastmod(真实)才是被参考的字段 | [官方 sitemap 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps)(一手) | 2026-10-10 |
| sitemap `<changefreq>` | 同上,Google 忽略 | 抓取调度看抓取历史 + lastmod + 内外链信号,不看该字段 | 同上 | 2026-10-10 |
| Indexing API 适用面 | 官方限 **JobPosting 与 BroadcastEvent**(嵌 VideoObject)两类 | 普通页面少量用 URL Inspection、批量靠 sitemap + 内链;给全站 URL 调 API 无效果且耗配额(200 publish/天) | [官方 Indexing API 文档](https://developers.google.com/search/apis/indexing-api)(一手) | 2026-10-10 |

## 五、与回归看门的联动

- 上表口径已固化为 `tests/test_canonical_facts.py` 的 `WRONG_STATEMENTS` 正则清单(FID-as-current、faqpage-for-serp、cwv-2.0、vsi-hallucination、engagement-reliability-hallucination、lcp-2.0s-threshold、sitemap-priority-ranking、changefreq-crawl-rate、ai-crawlers-no-js-absolute、gbp-chat-still-live、pagerank-next、pr-sculpting、indexing-api-any-url、page-experience-report-alive 等 ID):`python3 tests/test_canonical_facts.py` 单跑,或随 `python3 tests/run_tests.py` 全量。
- 新增"官方已停用"条目的流程:本表加行(时间戳 + 验证方式)→ 需要机检的补进 `WRONG_STATEMENTS`(正则必须同时通过其 bad/ok 自检样例)→ 两个测试都绿才算落账。

## 来源

- 一手:Google Search Central 文档与博客(faqpage / howto 变更公告 / sitemap / indexing-api 各页,URL 见上行)、[web.dev](https://web.dev/articles/vitals) vitals 系列(INP/CLS/LCP/vitals)、CrUX release notes、GSC 公告与 API 文档、GA4 渠道定义、Lighthouse release notes、GBP Help。
- 套件内互认:替换决策与工具链时间线以 [schema-examples.md](schema-examples.md) 的深读记录为准;CWV 现行口径见 [cwv-playbook.md](cwv-playbook.md);GSC 断代窗口见 [validation-guide.md](validation-guide.md) 与 [seo-drift-monitoring.md](../monitoring/seo-drift-monitoring.md);FID→INP 的禁引口径见 [validation-guide.md](validation-guide.md)。
