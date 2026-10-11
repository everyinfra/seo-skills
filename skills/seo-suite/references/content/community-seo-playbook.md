# 社区 SEO 操作手册(Community SEO Playbook)

> 建立于 2026-10-12(R6 新方法论入库)。**口径锚:Search Engine Land 2025-11-03《7 focus areas as AI
> transforms search》**(社区是 AI 时代全渠道叙事的组成部分)及 SEL Reddit 系列操作文
> (2025-07-24《A smarter Reddit strategy for organic and AI search visibility》、2026-02/03/05/08/09 系列)
> 【行业媒体】;引用占比数字另见套件引用银行。**断言半衰期 3–6 个月**(平台排名/引用占比 3 个月/
> 参与纪律 6 个月),引用数字前按半衰期复查,随 intel-update 搭车核对。
> 关联方法论:[search-everywhere-optimization.md](../research/search-everywhere-optimization.md)(社区是其中一平台面)、
> [brand-serp-methodology.md](../technical/brand-serp-methodology.md)(第三方口碑决定 Brand SERP 的 Negativity 面)。

## 一、为什么社区值得投入(证据链见引用银行)

- Reddit 在 Google SERP 的存在感 2024 年涨约 191%(Sistrix,SEL 转述);Reddit 自报每周 8000 万人用其站内搜索。
- AI 引用面:Reddit 是 ChatGPT 最常引用站点之一(SEL 转述研究口径:前二);Perplexity 引用中 Reddit 占比
  ~46.7% 居首;3000 万条 AI 回答的分析中 Reddit 为被引最多的域(SEL 2026-03)。全链数字与分级
  见 [geo-evidence-bank.md](geo-evidence-bank.md)——**厂商/媒体级证据,只作观察引用,不作收益承诺**。
- 对照口径并记(原则 23):另一分析(680 万 AI 引用)指多数 AI 回答实际来自品牌自有内容
  (SEL 2025-10)——社区是重要语料源,不是唯一战场;品牌地基仍走 brand-records 路线。

## 二、社区选择:匹配度评估

候选:subreddit、Quora(及知乎等中文对应)、Discord/Slack 私域、G2/垂直论坛。四维评分,两项不过即放弃:

| 维度 | 看什么 | 一票否决信号 |
|---|---|---|
| 主题重合 | 版块里有没有你的品类真实讨论(搜品牌/竞品/品类词) | 搜品类词零结果——没人在此研究你 |
| 规模与活跃 | 订阅量、日帖量、回复速度;小而活跃 > 大而死寂 | 热帖评论区零互动 |
| 规则与氛围 | 版规对品牌/外链/self-promo 的态度;版主执法强度 | 明文禁止商业参与 |
| 你的角色空间 | 有没有真实可答的问题(售前/故障/行业经验) | 只能硬贴内容才"出现" |

评估即参与的一部分:SEL 口径——先建透明档案、静观数周,摸清帖式、版规、版主执法,再开口。

评分示例(某 CRM 工具):r/smallbusiness(主题重合✓、活跃✓、规则友好△、角色空间✓→进入);
r/CRM(重合✓、死寂✗→放弃);Quora "best CRM" 问题簇(重合✓、有存量问题✓、规则中性✓→进入);
G2(重合✓、但属评论体系非社区→并入口碑面,不在本手册)。结论:两个平台做深,不铺第六个。

## 三、参与纪律(karma 文化与反 astroturf)

- **价值优先,不是销售**:社区一眼识破营销腔;成功的品牌带去有用回答而非广告(SEL 口径)。
  社区"把人当参与者、把 logo 当广告商"(SEL 2026-08)——让真实的员工(工程师/客服/销售)以
  透明命名档案(如 BrandName_Becky)参与,不以官方号刷帖。
- **crawl–walk–run**:crawl 期 2–3 个月只答与己无关的问题攒 karma 与版主信任;walk 期开始答品类问题、
  遵守各版 self-promo 比例惯例;run 期才可发起 AMA/资源帖。跳级=被识别,被识别即反噬
  (downvote、公开处刑帖、封禁——反噬帖本身会进搜索与 AI 语料,反噬 Brand SERP 的 Negativity 面)。
- **karma 是入场券不是 KPI**:karma 文化奖励"先给后取";考核应落在"真实解决问题的帖数",
  不落在曝光量。
- **节奏纪律**:每周固定参与窗口(如 2-3 次、每次 30 分钟答真实问题),好过集中爆发;
  版主与老用户对"突然高频出现然后消失"的账号模式同样敏感。热点日历交给工具
  (trend_watch 的 GO 信号),参与节奏保持人的连续性。

## 四、社区内容 → AI 引用的管道

路径:真实问答(社区)→ 平台投票排序(优质上浮)→ Google 收录(Discussions and forums 特性)→
AI 检索与训练引用。可观测、可复测;**不可直接购买或伪造**(见第六节)。三条操作含义:

1. **答案要"可摘取"**:具体经验+可核数字+先给结论——写法原则同 [ai-citation-patterns.md](ai-citation-patterns.md)。
2. **mentioned ≠ cited**:品牌在回答里被提及与被列为引用来源是两回事——观测用
   `scripts/citation_panel.py` 的五状态分类(brand_absent / name_only_mention / cited_brand),
   社区参与前后各采样一轮,同 prompt ≥3 次才报(Wilson 区间)。
3. **自有 UGC 站别幻想平替 Reddit**:四层机制差距(质量过滤/数据供给/规模/工程)见
   [ugc-site-search.md](ugc-site-search.md)。

前后对照示例:参与前基线(panel 首轮)品类题 20 条,mention coverage 15%、citation share 0;
crawl–walk 期 3 个月、每周 2-3 个真实答疑后复测——只比两期均成功的 cell(diff 配对分母),
`|Δ|≥5pp 且配对 n≥10` 才算信号(citation_panel diff 的 signals 节)。
涨幅不达标不追加发帖量,先回查:答的问题是不是决策链上的真问题(第二节匹配度)。

## 五、与本套件工具的接线

| 工具/文档 | 覆盖哪块 | 用法 |
|---|---|---|
| `scripts/trend_watch.py`(reddit_subs) | 社区雷达与选题闸门 | `watch --sources reddit-rising` 按版块 rising 帖发现热点;`--config trend_watch.json` 的 `reddit_subs` 配垂直版块(默认仅兜底 r/technology,真实部署必须配置);GO 信号接 [trend-jack-playbook.md](../../templates/content/trend-jack-playbook.md) |
| `scripts/trend_scout.py` | 一次性 HN+Reddit 扫描 | 社区选择期摸底:候选版块的讨论密度与帖式 |
| `scripts/citation_panel.py` | 引用面验收 | 上一节第 2 条;`diff` 看参与前后的 signals 节(\|Δ\|≥5pp 且配对 n≥10 才报) |
| [brand-records.md](brand-records.md) | 参与口径一致性 | 员工在社区里说的事实必须与 brand.yaml 同源;答价格/功能前先核 Offerings 黑名单 |

## 六、风险红线(镜鉴:2025 央视 3·15 口碑操纵曝光)

- **不自造问答**:3·15 曝光的口碑机构手法——批量注册账号在问答平台"自问自答"、操纵好评——
  一旦被识别,平台封号、媒体报道反噬,且虚假问答被收录后**进入 AI 引用语料,等于自我投毒**
  (AI 把捏造叙事当事实引用,纠错成本远高于初始收益)。本套件红线:只在真实问题下答,不开小号自问。
- **不买投票/水军**:买 upvote 可检测且适得其反(社区反 astroturf 机制+平台封禁)。
- **不越版规**:版规优先于任何增长目标;被封禁记录本身就是负面语料。
- **不做纯链接农夫**:社区链接多数 nofollow/ugc,直接 SEO 权重收益低——社区动作的验收指标是
  引用与口碑,不是外链数(外链体系另走 backlink 体系,见 [geo-evidence-bank.md](geo-evidence-bank.md) 的分级纪律)。
- **合规披露**:利益相关身份透明(受雇于品牌就说明);部分地区营销披露是法定义务。

## 七、什么站不该做社区参与(反指标)

- **品类在社区零讨论**(第二节主题重合一票否决):没人研究的品类,参与是成本不是杠杆。
- **法务/合规禁止公开答疑的品类**(受监管医疗、金融细节类):员工答错一句就是合规事件,
  风险>任何可见性收益。
- **没有真人可长期投入**:社区参与不能外包给内容农场或一次性 campaign——账号断档即前功尽弃,
  且半途账号是 astroturf 嫌疑信号。
- **目标只是外链**:社区链接权重收益低(第六节),要外链走 backlink 体系,别拿社区当目录站。

## 八、引用来源

- SEL 2025-11-03《7 focus areas as AI transforms search and the customer journey in 2026》
- SEL 2025-07-24《A smarter Reddit strategy for organic and AI search visibility》(crawl–walk–run、透明档案)
- SEL 系列 2026:Reddit 周搜索 8000 万(02-09)、3000 万 AI 回答引用分析(03-31)、
  Reddit 影响不止训练数据(05-21)、社区信号是 AI 最大第三方来源(08-12)
- 引用占比:Profound 等,经 [geo-evidence-bank.md](geo-evidence-bank.md) 转引(厂商研究分级)
- 3·15 镜鉴:央视 2025 年 3·15 晚会口碑操纵/虚假问答曝光报道【媒体报道 2025-03】
