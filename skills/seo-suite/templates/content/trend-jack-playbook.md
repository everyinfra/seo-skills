# {答案式标题,例:"判定 GO:37 分信号(Q1 相关 25/Q3 窗口 8h/Q4 独家视角=自有数据),News 型 24h 内发,必过 5 项发布闸+2 条红线"}

> **模板性质**:热点选题的**决策件+施工输入件**,不是结果报告——由 `scripts/trend_watch.py` 的 `watch`/`gate` 子命令预填判定字段,人补角度与观点清单;产出落在发布的页面本身与 monitor 的基线/复测,不在本文件。
> **填充方式**:信号与判定列由 trend_watch.py 落盘(`briefs/trend-{signal_id}-{YYYYMMDD}.md`),四问中 Q2/Q4 的人工半边由选题人填;**所有数字必须来自脚本输出或真实分析,不许编**;数字缺失写 [要追加: 数据源]。
> **字段出处**:四问闸门、判定矩阵、信号源登记表、48h 发布管线、放弃/转角度规则是**本套件设计**(没有对应的外部标准)。外部依据只用于下列事实:news sitemap 规则(Google 文档,见 [discover-news-seo.md](../../references/content/discover-news-seo.md));IndexNow 参与引擎(indexnow.org);AI 引用半衰期(Profound 与 SSRN 预印本,见 4.3);新闻源引用份额(arXiv 2507.05301);规模化内容滥用(Google 垃圾内容政策)。
> **垂直配置纪律**:热点监控的是**目标网站/产品所在行业**的趋势,不是 SEO/GEO 本身。`--config` 的 `vertical_tokens` 用三层词表(品类词+自家品牌词+竞品词;配竞品词后竞品动态自动成为高相关信号);`reddit_subs` 按垂直选版块(如 devops、LocalLLaMA),不要用默认值。Q1 匹配:词组全命中 +25;token 的词干级全命中 +10;显著单词(≥3 字符、非停用词)各 +10,且 ≥2 个不同垂类词时升为 HIGH(25);单复数互通。示例配置:`examples/trend-gate-geo-survey-20261011/product-vertical-config.json`。
> **状态**:`scripts/trend_watch.py` 已实装(用法见第 0 节)。

_For: {选题人 · SME 复核人} · Date: {YYYY-MM-DD} · Market: {目标市场/语言} · Signal: {signal_id + 一句话事件} · 判定: {GO|PIVOT|WATCH|DROP} · Data pulled: {trend_watch.py watch 运行时刻 · 二次采样时刻}_

> 多市场站点:逐市场各出一份本决策件(`trend_watch.py watch --market XX` 决定热搜源、wire 域名清单和 locale),不合并。市场差异规则见 [multilingual-workflow.md](../../references/overview/multilingual-workflow.md)。
> 占位符约定(实例化时全部替换,交付版不得残留花括号):`{{name}}`=命名占位符(取值必须能溯源到第 1 节信号登记表)· `{{x[]}}`=列表占位符(≥3 条,不足即证据不够)· `{}`=通用空位。

## The answer

{一段独立成立:信号是什么与来源、四问闸门逐问结果(过/不过+一句依据)、判定输出(GO=什么型+发布截止时刻 / PIVOT=转什么分析角度 / WATCH=何时重看 / DROP=为何放弃)、独家视角是什么(一句话)、红线自查结果(规模化内容滥用两条)、置信度(高/中/低+一句话依据)。只读这段的人不会错。判定规则:四问全过才 GO;Q4 无独家视角或 wire 源已占位的硬新闻,一律 PIVOT 转"分析角度"而非硬新闻跟进;窗口 >72h 只 WATCH 挂既有页刷新队列。}

## 1. 信号登记表(固定第一节,脚本落盘)

此节固定为决策件正文第一节、不得省略或后移——设计动机:先摆信号原始事实再谈判定,倒逼真拉取而非凭印象选题(同 [content-brief.md](content-brief.md) 证据头的设计理由)。下表任一格为空,决策件不得进入第 2 节闸门。

| 信号项 | 数值 | 口径/阈值 |
|---|---|---|
| signal_id | {{signal_id}} | 源-主题词哈希;trend_watch 落盘,跨次运行幂等 |
| 信号源与链接 | {{sources[]}} | ≥2 个独立源才算"事件"(单源=传闻,只 WATCH);逐源记首次见到时刻 |
| first_seen / 采样时刻 | {} / {} | UTC+本地双记;时效窗口(Q3)从 first_seen 起算 |
| velocity | {{vel}} | 同一信号源内,与 ≥30min 前的采样比排位(位置小=更热):`rising` / `peaked`(排位不变)/ `fading`;同源样本不足时为「不可判」,Q3 退化为只看 first_seen |
| 垂直相关性分 | {{rel_score}} | 见文件头 Q1 匹配规则;≥25 过 Q1,10–24 WATCH,<10 DROP |
| 同事件 wire 占位 | {{wire_n}} | 以信号标题查 Google News RSS,取前 10 条结果,数来源域名属于 wire 清单的条数;≥3 且 <24h = 硬新闻否决;`watch` 每次最多检 1 条候选(Q1 过线且窗口为 NEWS),其余在 `gate` 时补检 |
| 我们既有覆盖 | {{existing}} | 站内已有相关页(GSC/内链检索;`--panel` 可读 citation_panel 面板);有=优先刷新既有页而非新开 |
| 数据源与抓取时间 | {} | trend_watch.py 运行参数(`--sources`、`--market`、`--vertical`);单源失败明说,不猜 |

## 2. 四问闸门(选题决策;一票否决制)

四问全过 → GO;任一问不过按该问的降级规则走。Q1/Q3/wire 否决由脚本机检,Q2/Q4 人机各半——机检结果在每问"机检"行,人工判断填"人工"行,当场判不了的写"待核"并阻塞发布,不得默认通过(同 [pre-publish-checklist.md](pre-publish-checklist.md) 纪律)。

### 2.1 Q1 相关性:这事件与我们站点的垂直/品牌主张有关吗?

- **机检**:垂直词打分 ≥25(HIGH)=过;10–24(MED)=降级 WATCH(相关性不足,涨了再看);<10=DROP。
- **人工**:一票否决补充——即使 HIGH 命中,若事件与 [brand-records.md](../../references/content/brand-records.md) 的 Audience/"不服务谁"错位,填不过。
- 依据(工程判断):不相关热点的流量不进漏斗。

### 2.2 Q2 信息增益可行性:48 小时内能做出 5 个净新观点吗?

- **机检**(`gate --angle 角度.md`):脚本数角度文件里的观点条数——优先数表格行(`| 1 |`),没有表格就数列表项;≥5 条记 PASS,<5 条记 FAIL(判定 WATCH)。**脚本只计数,不判净新**:净新性靠人工,对照 top 竞品文本逐条确认(可用 `content_score.py` 的缺失术语补集辅助)。5 条是本套件起步阈值,尚未在站点数据上校准([deep-research-protocol.md](../../references/content/deep-research-protocol.md))。
- **人工**:逐条列出净新观点清单(下表),写不满 5 条=信息增益不可行=不过。取材四源:反共识(须有证据支撑)/ 时效新鲜度(竞品内容与模型训练截止之后的数据)/ 一线从业者(SME)引语 / 专有数据(自有调查、内部基准)——写前先审 SERP 列出"共识层",只写缺口(口径见 [quotable-content-examples.md](../../references/content/quotable-content-examples.md) 与 [content-strategy-framework.md](../../references/research/content-strategy-framework.md))。

| # | 净新观点(一句话) | 增益来源(四源之一) | 证据/数据在哪 | 需要几小时 |
|---|---|---|---|---|
| 1 | {} | {} | {} | {} |

### 2.3 Q3 时效窗口:我们还在窗口里吗?(24–72h 判定)

- **机检**:first_seen 距今 **<24h 且 velocity 不是 peaked/fading** → News 型候选(velocity 不可判时也按 News 候选,人工复核);**24–72h** → Analysis 型候选(新闻位已被占,分析位还空);**>72h,或 velocity=peaked/fading** → 只 WATCH,挂既有页刷新队列(8–12 周分层节奏,见 4.3)。24h、72h 是本套件设计值,写在 `thresholds`(`window_news_h`、`window_analysis_h`)里可调。
- **窗口与引用寿命**:AI 引用衰减很快,有两个定义不同的第三方数字,并记不选边——Profound 厂商研究(883,000 个页面、7 个 AI 引擎、12 个月):页面达到峰值后,中位 11 天跌到峰值一半,78% 的页面两周内减半([Profound](https://www.tryprofound.com/blog/the-half-life-of-an-ai-citation-is-11-days),核对 2026-10-21);SSRN 预印本(汇总多家厂商数据集):中位半衰期 4.5 周([SSRN 7344201](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7344201),核对 2026-10-21)。热点单篇的引用寿命以天计,所以决策要快;内容按"发布后 4–5 周仍有价值"设计,写分析层与数据层,不写转述层。

### 2.4 Q4 独家视角:我们能不能加进对话里没有的东西?

- **机检**(`gate --exclusive data|quote|access`):三选一——`data`=自有数据(内部数据或可复算的公开数据)/ `quote`=SME 可在窗口内给出具名引语 / `access`=一手访问(独家采访、实测、一手文件)。没有传 `--exclusive`=不过。**反共识角度没有对应参数**:它靠人工判断并写进角度文件;不传 `--exclusive` 时脚本按「无独家视角」判 PIVOT。
- **wire 硬新闻否决**(机检,优先级最高):Google News RSS 同事件前 10 条里,wire 域名 ≥3 条且事件 <24h → 判"硬新闻",**无论 Q4 如何,GO 强制降级 PIVOT**——我们很难赢 wire 源的首发与刷新速度。wire 清单按 `--market` 取默认值(国际:reuters.com、apnews.com、afp.com 等;zh、ru、ko、ja 另有本国通讯社/央媒清单),可在 `--config` 的 `wire_domains` 覆盖。
- **人工**:一句话写下独家视角,写不出=不过。

### 2.5 判定矩阵(脚本 `gate` 输出,人工复核)

脚本按下面的顺序判,先命中先出:

| 顺序 | 条件 | 判定 |
|---|---|---|
| 1 | Q1 <10 | **DROP**(垂直无关) |
| 2 | Q1 10–24 | **WATCH**(相关性不足) |
| 3 | 与库内活跃 go/pivot 信号词重叠 >70% | **DROP**(合并入既有决策件,不新开) |
| 4 | 没提供 `--angle`,或观点数 <5 | **WATCH**(等 Q2 证据,deadline 到时再看) |
| 5 | wire ≥3 条且 <24h | **PIVOT**(转分析角度,见第 3 节) |
| 6 | 没传 `--exclusive` | **PIVOT**(无独家视角) |
| 7 | Q3=NEWS(<24h,velocity 非 peaked/fading) | **GO(News 型,24h 内发)** |
| 8 | Q3=ANALYSIS(24–72h) | **GO(Analysis 型)** |
| 9 | Q3=LATE(>72h 或 peaked/fading) | **WATCH**(挂既有页刷新队列) |

`watch` 阶段另有:单源信号一律 WATCH(≥2 独立源才算事件)。

## 3. 放弃条件与转角度(PIVOT 的形态)

**直接放弃(DROP)的硬条件**:①Q1 <10;②与已判定信号词重叠 >70%(合并入既有决策件);③velocity=fading 且我们零起步——引用期望为负(新闻源在 AI 引用里占比不高且集中在少数媒体:AI Search Arena 的 24,000 多段对话、366,000 多条引用中,9% 指向新闻源,新闻引用高度集中在少数媒体,[arXiv 2507.05301](https://arxiv.org/abs/2507.05301),单作者预印本,核对 2026-10-21;下降段的残值不覆盖人写成本是本套件判断);④触发量产红线(见第 5 节)还想过闸。

**转"分析角度"(PIVOT)的形态**——硬新闻的时效位让给 wire,做深度层:

| 形态 | 内容 | 为什么这样做(工程判断) |
|---|---|---|
| 数据核对表 | 把事件数字逐条溯源、给出口径与基准 | 读者会问"这个数字从哪来",转述层答不了 |
| 时间线+影响分析 | 事件脉络 → 对 {{受众}} 意味着什么 | 提供 wire 稿没有的解释 |
| 本地市场对照 | 事件在目标市场的对应物/差异 | 接 multilingual"一套事实,多种变体" |
| 操作层回答 | 受众因此该做什么(Decision 型) | 答案前置+next steps,事件过后仍有用 |

PIVOT 产出仍走本模板第 4 节发布闸,但 sitemap 退常规 sitemap(>2 天不进 news sitemap),时间戳纪律不变。

## 4. 写作与发布动作(48h 管线)

### 4.1 写作(GO 后立刻,人写,不量产)

- 交稿走 [content-brief.md](content-brief.md)(News 型勾第 5 节 News 附加件:时效、事实核查、引语与来源、含意与分析、背景、地域语境六项;Analysis 型勾 Guide/Comparison);首段先给答案(读者口径)。
- 引用纪律按 [ai-citation-patterns.md](../../references/content/ai-citation-patterns.md):内联具名引用和带口径的统计数字是**写法要求,不是收益承诺**——GEO 论文报告的位置加权词数提升只在单一模型、固定上下文里出现,C-SEO Bench 在更广设置里没有重现([geo-evidence.md](../../references/content/geo-evidence.md) 第三节);转述他人数据会把引用留给原始源。

### 4.2 发布动作清单(发布即执行,机器可验)

| # | 动作 | 通过标准 | 验收 |
|---|---|---|---|
| 1 | **news sitemap**(仅 News 型,且站点属于 Google News 范围) | 只含最近两天内创建的文章;每个 sitemap ≤1,000 个 `<news:news>`;必填 `<news:publication>`(`name`、`language`)、`<news:publication_date>`(W3C 格式,可只写日期,建议写到时分秒带时区)、`<news:title>`([Google 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps/news-sitemap),核对 2026-10-21);Analysis 型退常规 sitemap | `python3 scripts/news_sitemap_check.py --url SITEMAP --pub-name "站名" --sample 3 --json`,退出码 0 |
| 2 | **IndexNow 通知** | 发布流水线提交新 URL。IndexNow 官方 FAQ 列出的接收端点是 Bing、Naver、Seznam、Yandex、Yep、Amazon,没有 Google([indexnow.org](https://www.indexnow.org/faq),核对 2026-10-21);Google 侧靠 sitemap `lastmod` 准确和内链 | `python3 scripts/indexnow.py submit --host 域名 --key KEY --url URL --json`,退出码 0(200/202);并 `curl -s sitemap.xml` 看 `lastmod` 已更新 |
| 3 | **显性时间戳** | 页面可见「发布于/更新于」带标签;`datePublished`、`dateModified` 与可见日期一致,给时区([日期指南](https://developers.google.com/search/docs/appearance/publication-dates));只在内容实质变化时改日期(Google 自查问题明确问是否改日期装作新鲜,[有用内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)) | 人工 + `market_lint.py` 日期格式检查 |
| 4 | **schema** | `NewsArticle`:Google 文档没有必需属性,推荐 `headline`、`image`、`datePublished`、`dateModified`、`author`([Article 文档](https://developers.google.com/search/docs/appearance/structured-data/article),核对 2026-10-21);与可见正文一致;不为展示位新增问答类标记 | `python3 scripts/schema_lint.py URL` 无 WARN |
| 5 | **Discover 侧**(可选) | 大图宽度 ≥1200px,总像素 >300,000,用 `max-image-preview:large` 启用;无需特殊标签或结构化数据([Discover 文档](https://developers.google.com/search/docs/appearance/google-discover),核对 2026-10-21) | 读页面 `<meta name="robots">`;`site_audit.py` 的 `nosnippet` 类发现为空 |
| 6 | **发布闸** | [pre-publish-checklist.md](pre-publish-checklist.md) 全过(机检脚本全绿+人工条目) | 逐条打勾落盘 |

### 4.3 分层刷新(发布不是终点;8–12 周节奏)

- **D+2**:勘误与数据回填(事件后续数字/口径修正);`dateModified` 只在内容真变时更新。
- **W+2**:首批引用测量——目标问题 5–10 条进 `citation_panel.py` 采样并记基线,14 天复测([multilingual-workflow.md](../../references/overview/multilingual-workflow.md) 第十二节四行报告制)。复测日历按短口径(11 天)排,刷新投入按长口径(4.5 周)排。
- **W+8~12**:分层刷新接 [content-refresh-playbook.md](../../references/content/content-refresh-playbook.md) 与 [content-decay-signals.md](../../references/content/content-decay-signals.md)——decay 信号触发优先于固定日历。

## 5. 合规红线(起草前必读;两条都过才准写)

1. **量产蹭热点=规模化内容滥用**:Google 垃圾内容政策把"为操纵排名、而不是帮用户而批量生成的页面"列为规模化内容滥用,「无论内容如何生成」都适用([垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies),核对 2026-10-21)。本模板的做法(本套件口径):同一事件 ≤2 篇/日、不做换实体不换结构的模板改写、强制人写(Q2 观点清单逐条有人名/数据归属);`trend_watch.py gate` 对词重叠 >70% 的信号判重复否决。
2. **真实性与署名**:热点场景的数字/引语高风险——每个数字有来源、引语可归属一手来源;拿不准的事实宁可 [要追加: 待核] 阻塞发布,不抢先发错。

## 6. 运营与度量(接 monitor 守护)

- 监控节奏(本套件设计):热点信号扫描每 3 小时(cron/launchd,可复用 `monitor.py` 的部署模板);3 小时是"不漏 rising 段"的采样密度,不是发文频率。
- 判定输出路由:`trend_watch.py watch` 在库里有活跃 GO 时退出码 1,接 `notify.py` 即时通知或 CI 门;WATCH 日批;DROP 只入库。
- 度量口径:发布记基线(曝光 0)→ 14 天复测;考核"被看见或被引的份额"(28 天曝光 >0 比例/AI 被引 O/X),不考核"N 篇/月"产出(multilingual-workflow.md 第十二节 12.2)。

## 检查清单(决策件自检:检查什么 → 怎么查 → 通过/失败)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 事件是真的(≥2 个独立源) | `python3 scripts/trend_watch.py backlog --status all --json`,读该信号的 `sources` | 通过:≥2 个源。失败:单源(标「单源」)→ 只 WATCH |
| 2 | Q1 相关 | 同上输出的 `rel_score` | 通过:≥25。10–24 WATCH,<10 DROP |
| 3 | Q2 观点 ≥5 且净新 | `python3 scripts/trend_watch.py gate --signal-id ID --angle 角度.md --exclusive data`,读 `q.q2`;再人工对照竞品文本确认净新 | 通过:PASS 且人工确认。失败:FAIL 或净新性存疑 |
| 4 | Q3 窗口 | 同上输出 `q.q3` | 通过:NEWS 或 ANALYSIS。LATE → WATCH |
| 5 | wire 否决 | 同上输出 `q.wire`;在 news.google.com 手搜标题核对 | 通过:未触发。触发 → PIVOT |
| 6 | 独家视角一句话 | 读决策件 Q4 人工行 | 通过:一句话写得出。写不出 → 不过 |
| 7 | 判定与终态一致 | `gate` 退出码:0=GO,1=其他;`--json` 的 `verdict`、`reasons` | 通过:决策件头部判定=`verdict`。失败:人工改了判定却没记理由 |
| 8 | 发布动作 | 第 4.2 节 6 项逐项验收 | 通过:全部验收命令退出码 0 |

## 0. scripts/trend_watch.py 用法(已实装)

> 分工:**trend_scout.py 是雷达**(一次性拉 HN + Reddit,回答"现在有什么热点"),**trend_watch.py 是闸门**(多源信号+四问判定+决策件落盘,回答"这个热点我们该不该追、以什么形态追")。scout 的输出可作 watch 的输入线索。

```text
python3 scripts/trend_watch.py watch  [--sources google-trends,google-news,reddit-rising,hn,weibo,baidu]
      [--market XX] [--vertical "llm agents"] [--topics 词表.txt] [--config trend_watch.json]
      [--panel panel.json] [--brief-dir briefs/] [--state .trend-state.json] [--json]
python3 scripts/trend_watch.py gate   --signal-id ID [--angle 角度.md] [--exclusive data|quote|access]
      [--market XX] [--config trend_watch.json] [--brief-dir briefs/] [--state ...] [--json]
python3 scripts/trend_watch.py backlog [--status open|go|pivot|watch|drop|all] [--days 14] [--state ...] [--json]
```

- `--market` 默认 `en`;必须是 `markets.json` 的 18 个市场码之一。默认信号源:所有市场 `google-news`+`reddit-rising`+`hn`;`zh` 另加 `weibo`+`baidu`。`google-trends` 可用但不在默认里。`google-news` 源需要垂直词(`--vertical`、`--topics` 或 config 的 `vertical_tokens`)。
- `--config` JSON 键:`vertical_tokens[]`、`reddit_subs[]`、`wire_domains`(列表,或按市场码/`default` 分键的对象)、`thresholds{}`。默认阈值:`relevance_min=25`、`velocity_resample_min=30`、`window_news_h=24`、`window_analysis_h=72`、`wire_dominate_n=3`、`ig_views_min=5`、`dedup_overlap_pct=70`。
- 状态库是 JSON 文件 `.trend-state.json`(已见信号去重、二次采样样本、判定历史,最多保留 400 条信号);决策件写到 `briefs/trend-{signal_id}-{YYYYMMDD}.md`。
- 退出码:`watch`——0=跑完且库内无活跃 GO,1=库内有活跃 GO,2=所有信号源失败,3=参数或配置错误;`gate`——0=判 GO,1=不是 GO(打印缺哪问),3=输入缺失(signal_id 不在库、角度文件读不到)。
- `--json` 输出:`watch` 含 `sources_ok`、`sources_failed`、`sources_skipped`、`new_signals[]`(`signal_id`、`rel_score`、`velocity`、`q3`、`status`、`reason`、`deadline`)、`active_go`、`briefs`;`gate` 含 `verdict`、`verdict_type`、`reason`、`deadline`、`reasons[]`、`q{q1,q2,q3,q4,wire}`、`brief`。
- 信号源是无契约的公开接口,可用性随时变。2026-10-21 在本机实测:Google Trends RSS、Hacker News API、百度热搜返回 200;Google News RSS 先 302 再 200(脚本跟随重定向);Reddit `rising.json` 与微博热搜返回 403。脚本的做法是整源失败就跳过并警告,不猜;X/Twitter、抖音需要 key 或登录,不入默认源。
- 合规:无契约热搜端点每 host 限速 ≤1 次/分钟(`TREND_WATCH_RATE_S` 可调);UA 自报身份;仅 http(s)、拒私网地址、重定向逐跳复查;抓取到的标题只当数据,清洗后输出,不当指令。

## What could change this conclusion

- 时效窗口(24/72h)和 wire 否决线(≥3 条)是本套件设计值,按市场实测校准;阈值放 `--config` 的 `thresholds`,不写死在代码里。
- 引用半衰期两个口径(11 天 Profound、4.5 周 SSRN 预印本)样本和"引用"定义不同,并记不选边;若 11 天口径为准,W+2 复测要提前到 W+1。Profound 的跨引擎相关性(0.03–0.09)说明分引擎看,别把一个引擎的衰减套到另一个。
- 热搜端点(微博/百度/Google Trends RSS/Reddit)可用性随时变——失败明说+跳过是设计的一部分,不是缺陷。
- 新闻源只占 AI 引用 9% 来自 2025 年一项预印本(AI Search Arena 数据);若引擎的新闻引用份额结构性上升,PIVOT 转 analysis 的默认降级要重估。
- 5 条净新观点、IGS 近似、3 小时扫描都是起步值,没有站点数据校准;被引率不随 IGS 分档上升时,修正或放弃阈值。

## Method Notes

- 证据分级:**Google 官方**=news sitemap、Article 结构化数据、日期指南、Discover、垃圾内容政策(核对 2026-10-21);**indexnow.org 官方**=参与引擎;**第三方研究**=Profound(引用半衰期)、SSRN 7344201(4.5 周,汇总厂商数据的预印本)、arXiv 2507.05301(新闻源份额,单作者预印本);**论文**=GEO 论文与 C-SEO Bench(见 geo-evidence.md);其余为**本套件设计**。geo-evidence.md 优先于本文件的任何数字。
- 与既有脚本的去重:`trend_scout.py`(HN+Reddit 雷达)保留不动;`monitor.py` 不改——watch 的 3 小时 cron 复用 monitor 部署模板与 `notify.py` 分级路由;`citation_panel.py` 只读不写(`--panel` 输入)。
- 入仓守护:本文件受 self_check 七段式守护(含 The answer、What could change this conclusion、Method Notes);`trend_watch.py` 已登记在能力矩阵,离线测试见 `tests/test_trend_watch.py`。
- 已知坑:热搜快照无历史——first_seen 是"我们首次见到",不是事件真实起点,窗口判断偏保守;velocity 在低频源(如日更的 Trends RSS)上不可判,自动退化为只看 first_seen;`backlog` 会标出 deadline 到期未处理的信号(GO 过期建议降级 WATCH 并停止写作)。
