# 社区 SEO 操作手册（Community SEO Playbook）

> 建立于 2026-10-12；2026-10-18 逐条核对来源（证据账本 C3）。参与方法主要依据 Search Engine Land 的 Reddit 系列文章【行业媒体】；引用占比数字全部是厂商或媒体研究，只作观察引用，不作收益承诺，分级见 [geo-evidence-bank.md](geo-evidence-bank.md)。「本套件口径」是本套件的做法约定。
> 断言半衰期 3 至 6 个月：平台排名和引用占比按 3 个月复查，参与纪律按 6 个月复查。
> 关联方法论：[search-everywhere-optimization.md](../research/search-everywhere-optimization.md)（社区是其中一个平台面）；[brand-serp-methodology.md](../technical/brand-serp-methodology.md)（第三方口碑决定 Brand SERP 的负面面）。

## 一、为什么社区值得投入（第三方数据）

- **Google 可见度**：Sistrix 美国数据，reddit.com 的可见度指数从 2024-01-01 的 667.79 升到 2024-12-30 的 1,942.29（升 190.85%），是 2024 年绝对增量最大的域名（[Sistrix IndexWatch 2024](https://www.sistrix.com/blog/indexwatch-seo-winners-in-google-us-search-2024/)）。
- **站内搜索**：Reddit 在 2025-Q4 财报电话会上说，每周有 8,000 万人使用 Reddit 搜索（[SEL 2026-02-09 转述](https://searchengineland.com/reddit-search-80-million-people-468598)）。
- **AI 引用面**（各研究的样本和口径不同，不能互相换算）：
  - Profound，6.8 亿条引用，2024-08 至 2025-06（[研究](https://www.tryprofound.com/blog/ai-platform-citation-patterns)）：在 Perplexity 引用最多的前 10 个来源内部，Reddit 占 46.7%；按全部引用算，Reddit 占 Perplexity 的 6.6%。ChatGPT 前 10 来源内 Reddit 排第 2（占 11.3%）。
  - Peec AI，3,000 万条来源（[SEL 2026-03-31 转述](https://searchengineland.com/ai-search-engines-cite-reddit-youtube-and-linkedin-most-study-473138)）：Reddit 是 ChatGPT、Google AI Mode、Gemini、Perplexity、AI Overviews 中被引最多的域名。
  - Kevin Indig，3.5 万条 ChatGPT 引用，美国，2025-12，SaaS 类提示（[SEL 2026-08-12](https://searchengineland.com/community-signals-ai-largest-third-party-source-484606)）：去掉厂商自有域名后，UGC 平台占被引域名的 17.1%，出版商占 4.0%。
- **对照口径并记**（总纲原则 23：口径冲突并记，见 [multilingual-workflow.md](../overview/multilingual-workflow.md)）：Yext 分析 680 万条引用（ChatGPT、Gemini、Perplexity，2025-07 至 08），86% 来自品牌自有或可管理的来源：官网 44%，商家信息类 42%，评价与社交 8%，论坛 2%（[SEL 2025-10-09](https://searchengineland.com/ai-search-citations-brand-controlled-sources-463166)）。结论：社区是重要语料源，不是唯一战场；品牌地基仍走 [brand-records.md](brand-records.md) 路线。
- **训练、授权接入、引用是三件事**：模型训练用过 Reddit，不等于答案会引用某个帖子；Google 与 OpenAI 的授权让它们持续拿到新帖；引用只说明检索系统当时认为该来源有用（[SEL 2026-05-21](https://searchengineland.com/reddits-ai-search-influence-goes-beyond-training-data-478235)）。

## 二、社区选择：匹配度评估

候选：subreddit、Quora（及知乎等中文对应）、Discord 或 Slack 私域、垂直论坛。四维评分，两项不过就放弃（本套件口径）：

| 维度 | 看什么 | 一票否决信号 |
|---|---|---|
| 主题重合 | 版块里有没有你的品类的真实讨论（搜品牌、竞品、品类词） | 搜品类词零结果 |
| 规模与活跃 | 订阅数、日帖量、回复速度；小而活跃好过大而沉寂 | 热帖评论区零互动 |
| 规则与氛围 | 版规对品牌、外链、自我推广的态度；版主执法强度 | 明文禁止商业参与 |
| 你的角色空间 | 有没有你能真实回答的问题（售前、故障、行业经验） | 只能硬贴内容才能「出现」 |

评估本身是参与的一部分。SEL 建议先建档案、观察讨论，摸清帖式、版规、版主执法强度和社区对品牌的态度，再开口（[SEL 2025-07-24](https://searchengineland.com/a-smarter-reddit-strategy-for-organic-and-ai-search-visibility-459369)）。

评分示例（某 CRM 工具）：r/smallbusiness（重合✓、活跃✓、规则△、角色空间✓ → 进入）；r/CRM（重合✓、沉寂✗ → 放弃）；Quora「best CRM」问题簇（重合✓、有存量问题✓、规则中性✓ → 进入）；G2（重合✓，但属于评论体系 → 并入口碑面，不在本手册）。结论：两个平台做深，不铺第六个。

## 三、参与纪律（karma 文化与反水军）

- **价值优先，不是销售**：社区很快识破营销腔。成功的品牌带去有用回答，不带广告。用透明的品牌命名账号参与，例如 BrandName_Official 或 BrandName_Becky；随时说明自己与品牌的关系（SEL 2025-07-24）。
- **让真人出面**：社区把一个人当参与者，把一个 logo 当广告主（SEL 2026-08-12）。让真实员工（工程师、客服、销售）用实名或透明档案参与。
- **crawl–walk–run（SEL 2025-07-24）**：
  - crawl（2 至 3 个月以上）：建档案、看讨论、点赞、评论、融入；暂不发任何品牌内容；积累 karma 和熟悉度。
  - walk（1 至 2 个月以上）：回答与产品相关的问题；提供专家见解；可以围绕高频问题开帖。
  - run：开设品牌自有 subreddit；沉淀流程；让客服团队参与。
  - 跳级会被识别。被识别就会反噬（downvote、公开批评帖、封禁）。反噬帖本身会进搜索和 AI 语料（本套件口径）。
- **karma 是入场券，不是 KPI**：考核「真实解决问题的帖数」，不考核曝光量（本套件口径）。
- **节奏纪律（本套件口径）**：每周固定参与窗口（例如 2 至 3 次、每次 30 分钟），好过集中爆发。版主和老用户对「突然高频出现然后消失」的账号同样敏感。热点日历交给工具（`trend_watch.py` 的 GO 信号），参与节奏保持真人连续。
- **纠正过时信息**：旧帖说你缺某功能而你已上线时，在原帖下回复一条带日期的更正和更新链接；删帖请求很少成功（SEL 2026-08-12）。

## 四、社区内容到 AI 引用的管道

路径（本套件口径）：真实问答（社区）→ 平台投票排序 → Google 收录（Discussions and forums 等特性）→ AI 检索和引用。可观测、可复测；不可购买或伪造（见第六节）。三条操作含义：

1. **答案要可摘取**：具体经验、可核数字、先给结论。写法原则同 [ai-citation-patterns.md](ai-citation-patterns.md)。
2. **提及不等于引用**：用 `scripts/citation_panel.py` 的五状态分类观测：`no_answer`（引擎没给答案）、`failed`（采集失败，不入分母）、`brand_absent`、`name_only_mention`（正文提到品牌但引用来源里没有品牌域名）、`cited_brand`。同一 prompt 至少采样 3 次才报 Wilson 区间。
3. **自有 UGC 站别幻想替代 Reddit**：四层机制差距（质量过滤、数据供给、规模、工程）见 [ugc-site-search.md](ugc-site-search.md)。

**前后对照示例（本套件口径）**：参与前基线（面板首轮）品类题 20 条，mention coverage 15%，citation share 0。crawl 到 walk 期 3 个月、每周 2 至 3 个真实答疑后复测。只比两期都成功的 cell（配对分母）。`|Δ|≥5pp 且配对 n≥10` 才算信号（`citation_panel.py diff` 的 signals 节）。涨幅不达标时不加发帖量，先回查答的问题是不是决策链上的真问题（第二节）。

## 五、与本套件工具的接线

| 工具或文档 | 覆盖哪块 | 用法（参数已核对 `--help`） |
|---|---|---|
| `scripts/trend_watch.py` | 社区雷达与选题闸门 | `python3 scripts/trend_watch.py watch --sources reddit-rising --config trend_watch.json`。`reddit_subs` 写在 config 里；不配时只兜底 r/technology，真实部署必须配置。GO 信号接 [trend-jack-playbook.md](../../templates/content/trend-jack-playbook.md) |
| `scripts/trend_scout.py` | 一次性 HN 与 Reddit 扫描 | `python3 scripts/trend_scout.py --vertical "crm small business"`。只扫 HN 首页和固定 6 个 subreddit（seo、bigseo、technology、startups、webdev、marketing）；候选版块摸底改用 trend_watch 的 `reddit_subs` |
| `scripts/citation_panel.py` | 引用面验收 | `init --brand X --prompts-file prompt-bank.md --domain example.com` 建面板 → `record --engine chatgpt --file run.csv` 记每轮 → `diff RUN1 RUN2` 看 signals 节 |
| [brand-records.md](brand-records.md) | 参与口径一致性 | 员工在社区说的事实必须与 brand.yaml 同源；答价格或功能前先核 Offerings 黑名单 |

## 六、风险红线

- **不制造虚假内容**（镜鉴：2026-03-15 央视 3·15 晚会曝光 AI 大模型「投毒」）：记者用「力擎 GEO 优化系统」虚构一款「Apollo-9」智能手环，编造卖点和用户评价，自动生成十几篇软文发到自媒体；两小时后就有 AI 大模型引用并推荐。三天后追加 11 篇虚构测评，两个 AI 模型把这款不存在的产品排在推荐前列（[证券时报 2026-03-16](https://stcn.com/article/detail/3678592.html)；节目页 [央视网](https://tv.cctv.com/2026/03/15/VIDEmX0VdYf9DeKI87GYEfqF260315.shtml)）。虚假内容进入 AI 语料后，纠错成本远高于初始收益。本套件红线：只在真实问题下回答，不开小号自问自答，不批量发虚构测评。
- **不买投票或水军**：买 upvote 会被平台识别并封禁，适得其反（本套件口径）。
- **不越版规**：版规优先于任何增长目标；封禁记录本身就是负面语料。
- **不做纯链接农夫**：Google 建议论坛和评论里的用户链接标 `rel="ugc"`（[链接属性文档](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links)），社区链接的直接 SEO 价值有限。社区动作的验收指标是引用与口碑，不是外链数。外链走 backlink 体系（分级纪律见 [geo-evidence-bank.md](geo-evidence-bank.md)）。
- **合规披露**：说明利益相关身份（受雇于品牌就写明）。部分地区的营销披露是法定义务。

## 七、什么站不该做社区参与（反指标）

- **品类在社区零讨论**（第二节主题重合一票否决）：没人研究的品类，参与是成本，不是杠杆。
- **法务或合规禁止公开答疑的品类**（受监管的医疗、金融细节）：员工答错一句就是合规事件。
- **没有真人可以长期投入**：社区参与不能外包给内容农场或一次性活动。账号断档就前功尽弃，半途弃号也像水军。
- **目标只是外链**：要外链走 backlink 体系，别拿社区当目录站。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 候选社区过四维评分 | 按第二节表格逐项打分，记录搜索品类词的结果截图或链接 | 四维至少三项通过，且无一票否决信号 |
| 账号透明 | 查看参与账号的主页简介与用户名 | 写明与品牌的关系为通过；匿名推广为失败 |
| crawl 期纪律 | 账号前 2 至 3 个月的发帖记录 | 无品牌推广帖为通过 |
| 版规合规 | 对照每个版块的自我推广规则逐帖核 | 零删帖、零封禁为通过 |
| 引用基线已建 | `python3 scripts/citation_panel.py init --brand X --prompts-file prompt-bank.md --domain example.com`，每个引擎 `record` 一轮 | 面板存在且每个 prompt 至少 3 次采样 |
| 参与效果 | `python3 scripts/citation_panel.py diff RUN1 RUN2` | signals 节出现 \|Δ\|≥5pp 且配对 n≥10 的正向信号为有效；只有 stable 不算效果 |
| 热点雷达已配置 | 查看 `trend_watch.json` 的 `reddit_subs` | 配了产品垂直版块为通过；只有默认 technology 为失败 |
| 过时说法已纠正 | 搜「品牌名 + 功能名 site:reddit.com」 | 过时帖下都有带日期的更正回复为通过 |
| 无虚假内容 | 内部审计：对外发布的测评和问答都能对应真实用户或真实员工 | 全部可对应为通过 |

## 引用来源

- [SEL 2025-07-24《A smarter Reddit strategy for organic and AI search visibility》](https://searchengineland.com/a-smarter-reddit-strategy-for-organic-and-ai-search-visibility-459369)（crawl–walk–run、透明档案）
- [SEL 2026-08-12《Community signals are AI's largest third-party source》](https://searchengineland.com/community-signals-ai-largest-third-party-source-484606)
- [SEL 2026-05-21《Reddit's AI search influence goes beyond training data》](https://searchengineland.com/reddits-ai-search-influence-goes-beyond-training-data-478235)
- [SEL 2026-02-09：Reddit 每周 8,000 万搜索用户](https://searchengineland.com/reddit-search-80-million-people-468598)；[SEL 2026-03-31：Peec AI 3,000 万来源](https://searchengineland.com/ai-search-engines-cite-reddit-youtube-and-linkedin-most-study-473138)；[SEL 2025-10-09：Yext 680 万引用](https://searchengineland.com/ai-search-citations-brand-controlled-sources-463166)
- [Sistrix IndexWatch 2024](https://www.sistrix.com/blog/indexwatch-seo-winners-in-google-us-search-2024/)；[Profound 引用模式研究](https://www.tryprofound.com/blog/ai-platform-citation-patterns)
- [SEL 2025-11-03《7 focus areas as AI transforms search and the customer journey in 2026》](https://searchengineland.com/7-focus-areas-as-ai-transforms-search-and-the-customer-journey-in-2026-464068)（全渠道背景）
- 2026 年 3·15：[证券时报](https://stcn.com/article/detail/3678592.html)、[央视网节目页](https://tv.cctv.com/2026/03/15/VIDEmX0VdYf9DeKI87GYEfqF260315.shtml)
- 2026-10-18 更正：旧版写的「2025 年 3·15 问答平台自问自答」与来源不符，已改为 2026 年 3·15 的 GEO 投毒案例；「Perplexity 引用中 Reddit 占 46.7%」改为「前 10 来源内部份额」（全部引用为 6.6%）。
