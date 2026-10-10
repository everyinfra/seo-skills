# 信源监控体系(如何持续领先)

> 建立于 2026-10-10,来自三路 agent 深度调研(官方引擎/研究社区/竞品前沿)。目的:回答"要持续丰富完善本套件,应该重点监控和搜索哪些信源"。分四层:必盯官方→研究数据→社区本地→竞品前沿,各带频率与抓取方式。

## 一、必盯官方层(信号价值最高,变动=套件规则要改)

| 优先级 | 源 | 频率 | 方式 | 变了影响什么 |
|---|---|---|---|---|
| 1 | [Search Central Blog](https://developers.google.com/search/blog)(RSS: /blog/feed.xml) | 周 | RSS | 核心更新/新功能→全部模块 |
| 2 | [Search 文档 changelog](https://developers.google.com/search/updates) | 周 | 页面 diff | 文档级变更→技术审计规则 |
| 3 | GSC/Search 功能公告(旧 [support.google.com/webmasters/announcements](https://support.google.com/webmasters/announcements) **已 404 下线**,2026-10 确认)→ 改盯 [Search Blog RSS](https://developers.google.com/search/blog/feed.xml) | 月 | RSS | AI Reporting 等新功能→监控层 |
| 4 | [Status Dashboard](https://status.search.google.com/) | 事件 | 哈希 10min | 算法/事故时间线→算法归因 |
| 5 | [Lighthouse releases](https://github.com/googlechrome/lighthouse/releases) | 4 周 | GH RSS | AGENTIC_BROWSING 演进→agent-readiness |
| 6 | [Bing Webmaster Blog](https://blogs.bing.com/webmaster)(RSS) | 月 | RSS | Copilot 引用数据(2026-02 AI Performance)→测量层 |
| 7 | [OpenAI bots docs](https://developers.openai.com/api/docs/bots) | 不定期 | 哈希周 | UA/IP 段/robots 规则→爬虫政策 |
| 8 | [ARD spec](https://github.com/ards-project/ard-spec) | 活跃 | GH RSS | 发现协议→agent-protocols 模块 |
| 9 | WebMCP W3C/IETF 草案 | 月 | diff/commits | 页面工具协议→agent-readiness |
| 10 | [Anthropic 爬虫文档](https://privacy.claude.com/en/articles/8896518) | 不定期 | 哈希周 | Claude bot 行为→爬虫政策 |
| 11 | [Schema.org releases](https://schema.org/docs/releases.html) | 半年 | GH RSS | 词汇变更→schema 模块(v30.1=2026-09) |
| 12 | [CrUX release notes](https://developer.chrome.com/docs/crux/release-notes) | 月第二个周二 | RSS | CWV 口径→cwv-playbook |
| 13 | [Cloudflare Radar AI](https://radar.cloudflare.com/ai-insights) | 周 | API | AI bot 流量趋势→日志分析 |
| 14-15 | [StatCounter](https://gs.statcounter.com/search-engine-market-share) 全球搜索+AI chatbot 两页 | 日 | 抓取 | 份额数字→各市场门户 |
| 16-18 | Yandex Webmaster / Naver webmaster 博客 / Baidu ziyuan | 月 | diff/RSS | 三引擎生态→对应市场 |
| 19 | StatCounter 国家页×5(RU/KR/CN/JP/US) | 周 | 抓取 | 市场门户数字 |
| 20 | robots.txt RFC 9309+文档 | 年 | 哈希季 | 爬虫政策底层 |

注:旧"ranking updates history"页 2025 已下线,改盯 Blog+Dashboard。
注:StatCounter 图表页是 JS 渲染,服务端 HTML 每次拉取都在抖——intel_check 对 hash 源做
**二次拉取确认**(两次一致才算变更,抖动自动按噪音跳过);StatCounter 的 CSV 端点
(chart.php?csv=1)实测返回空数据,不可依赖,份额以页面变更触发人工核对为准。

## 二、研究与数据层

**学术(arXiv 周扫)**:`cat:cs.IR AND (all:"generative engine optimization" OR all:"answer engine optimization" OR abs:"LLM citation" OR abs:"visibility in AI search")`;已知脉络:Princeton GEO(arXiv:2311.09735)→E-GEO(2511.20867 电商测试床)→批判综述(2607.14035,2023-26 全谱系)→BRGEO-1 协议(SSRN 2026-09);排行榜 generative-engines.com。会议(SIGIR/WWW/WSDM/ACL)每年 5-7 月会后扫一次。

**数据研究团队**:
| 源 | 系列 | 频率 | 抓什么 |
|---|---|---|---|
| [Ahrefs](https://ahrefs.com/blog) | Data Studies | 2-4 月/篇 | AIO 点击率曲线(34.5→58%) |
| [Semrush](https://www.semrush.com/blog)+Sensor | 研究/日 | 月/日 | AIO 触发因子·SERP 波动 |
| [Sistrix](https://www.sistrix.com/blog) | AI Research | 1-2 月 | 德国 AIO CTR·citation drift |
| [Conductor](https://www.conductor.com/academy) | AI citations | 季 | 引用对流量影响 |
| [BrightEdge](https://www.brightedge.com/resources/research-reports) | 报告 | 月 | AI referral 趋势 |

## 三、社区与 18 市场本地层

**英文社区**:r/TSEO(周扫 top.json)/r/bigseo(月)/HN(hn.algolia.com API 关键词 "AI Overviews"/"llms.txt"/"Perplexity",周)。**三媒体分工不重叠**:Search Engine Land=官方公告解读(日 RSS)/SEJ=方法论长文(日 RSS)/**Search Engine Roundtable=论坛震荡·算法异常·GSC bug——异常信号最早出现(日 RSS,必订)**。

**中文圈**:知乎 SEO 话题周扫;tophead:Zac/昝辉(zaccode.com,RSS);chinaz.com/news(日,转载 AI 搜索报告);5118.com 博客;ziyuan.baidu.com(官方最重要)。

**18 市场本地信源(每市场至少 1 个,兜底=Google Blog 对应语言版 RSS)**:
| 市场 | 信源 | 市场 | 信源 |
|---|---|---|---|
| ja | suzukikenichi.com/blog/feed+webtan.impress.co.jp | fr | abondance.com(RSS) |
| ko | searchadvisor.naver.com+brunch「검색엔진 최적화」页 | it | giorgiotave.it 社区 |
| ru | searchengines.guru/ru/articles(RSS) | nl | frankwatching.com(RSS) |
| de | sistrix.com/blog 德区研究 | es | Google blog es+sistrix 西班牙研究 |
| 其余 | Google Search Central Blog 对应语言(RSS)+周扫该语种 site: 报道 | | |

## 四、竞品与前沿层(套件进化方向的风向标)

**GitHub 观察名单**(90 天 commits 确认的活跃度):
| 仓 | 信号 | 频率 |
|---|---|---|
| coreyhaines31/marketingskills(53.9k★,614 commits/90d,日更版本) | 功能最全对标 | 周 |
| every-app/open-seo(370 commits,issue 即 roadmap) | 商业化路径 | 周 |
| **Albert-Weasker/niubigeo(5 周 6,140★!9/3 创建)** | **增速最快黑马,AI 品牌可见性报告** | 周(必入) |
| jianruntech/geo-score(285 commits,v1.8.0 引文 spans) | 评分学演进 | 双周 |
| AgriciDaniel/claude-seo(183 commits,seo-cockpit) | 子技能扩张 | 双周 |
| zubair/geo-seo-claude(84,靠外部 PR) | 月 | |
| TheCraigHewitt/seomachine(5 commits,半休眠) | 季 | |

新仓扫描(双周):GitHub API `q=seo+claude+skill+created:>YYYY-MM-DD&sort=stars`+`q=geo|aeo|ai-visibility in:name,description created:>`+topics generative-engine-optimization/chatgpt-seo。Awesome 清单 commits.atom 订阅:amplifying-ai/bmpi-dev awesome-seo/DavidHuji/Awesome-GEO。

**商业产品风向标**:GSC Generative AI 报告(2026-06 上线,分 AIO/AI Mode/Discover)与 AI Mode ads=数据层最大变量;Profound MCP 化=工作流自动化方向;**竞品重心正从 SEO 审计转向 AI 可见性监测+MCP 化**。

**风险信号(防套件建议过时)**:spam 更新 2026 已 4 次(3/6/8/9 月);**6 月起 spam 政策明文覆盖"操纵生成式 AI 回答"**;8/28 站点声誉政策修订→内容模块合规边界;AI 内容检测进展→humanizer 类建议的失效风险(季)。

**跨行业(3-5 个泛信号)**:AI 浏览器普及(Atlas/Comet/Dia+Chrome 原生 agent 流量)/OS 级 agent/搜索入口变化(Google 智能搜索框)。

## 五、信源→套件模块映射(哪个信源变了改哪个文件)

| 信源变动 | 更新模块 |
|---|---|
| Google Blog/changelog/Schema | validation-guide/schema-*/audit-rule-catalog |
| OpenAI/Anthropic/Lighthouse/ARD/WebMCP | ai-crawler-policy/agent-readiness/agent-protocols |
| StatCounter 国家页/CrUX/Radar | markets/*.md 门户/cwv-playbook |
| Yandex/Naver/Baidu 官方 | 对应市场门户+naver-searchadvisor |
| Ahrefs/Semrush/Sistrix 研究 | geo-evidence-bank/geo-platform-differences |
| spam 政策执法案例 | penalty-recovery/continuous-operations 安全边界 |
| 竞品仓新版本 | 对应能力文件+scripts |
| arXiv 新论文 | geo-evidence-bank 证据银行 |

## 来源

三路 agent 调研(2026-10-10):官方引擎/研究社区/竞品前沿;全部 URL 经检索验证。
