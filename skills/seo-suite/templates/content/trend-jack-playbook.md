# {答案式标题,例:"判定 GO:37 分信号(Q1 相关 25/Q3 窗口 8h/Q4 独家视角=自有数据),News 型 24h 内发,必过 5 项发布闸+2 条红线"}

> **模板性质**:热点选题的**决策件+施工输入件**,不是结果报告——由 `scripts/trend_watch.py` 的 watch/gate 子命令预填判定字段,人补角度与观点清单;产出落在发布的页面本身与 monitor 的基线/复测,不在本文件。
> **填充方式**:信号与判定列由 trend_watch.py 落盘(`briefs/trend-{signal_id}-{YYYYMMDD}.md`),四问中 Q2/Q4 的人工半边由选题人填;**所有数字必须来自脚本输出或真实分析,不许编**;数字缺失写 [要追加: 数据源]。
> **字段出处**:四问闸门与判定矩阵、信号源登记表、48h 发布管线、放弃/转角度规则=本套件设计(依据 2026-10 定向调研,证据分级见 Method Notes);news sitemap 48h 三件套与验收命令=[discover-news-seo.md](../../references/content/discover-news-seo.md) 官方口径;IndexNow 消费方与边界=SKILL.md 技术节;刷新触发=fire-your-seo-agency 深读(已入 [content-refresh-playbook.md](../../references/content/content-refresh-playbook.md) 与 multilingual-workflow.md 第十二节)。
> **状态**:设计稿(2026-10-11),入仓动作见 Method Notes 登记清单。

_For: {选题人 · SME 复核人} · Date: {YYYY-MM-DD} · Market: {目标市场/语言} · Signal: {signal_id + 一句话事件} · 判定: {GO|PIVOT|WATCH|DROP} · Data pulled: {trend_watch.py watch 运行时刻 · 二次采样时刻}_

> 多市场站点:逐市场各出一份本决策件(trend_watch.py --market XX 决定热搜源与 wire 域名清单),不合并。市场差异规则见 [multilingual-workflow.md](../../references/overview/multilingual-workflow.md)。
> 占位符约定(实例化时全部替换,交付版不得残留花括号):`{{name}}`=命名占位符(取值必须能溯源到第 1 节信号登记表)· `{{x[]}}`=列表占位符(≥3 条,不足即证据不够)· `{}`=通用空位。

## The answer

{一段独立成立:信号是什么与来源、四问闸门逐问结果(过/不过+一句依据)、判定输出(GO=什么型+发布截止时刻 / PIVOT=转什么分析角度 / WATCH=何时重看 / DROP=为何放弃)、独家视角是什么(一句话)、红线自查结果(scaled-content-abuse 两条)、置信度(高/中/低+一句话依据)。只读这段的人不会错。判定规则:四问全过才 GO;Q4 无独家视角或 wire 源已 dominate 的硬新闻,一律 PIVOT 转"分析角度"而非硬新闻跟进;窗口 >72h 只 WATCH 挂既有页刷新队列。}

## 1. 信号登记表(固定第一节,脚本落盘)

此节固定为决策件正文第一节、不得省略或后移——设计动机:先摆信号原始事实再谈判定,倒逼真拉取而非凭印象选题(同 [content-brief.md](content-brief.md) 证据头的设计理由)。下表任一格为空,决策件不得进入第 2 节闸门。

| 信号项 | 数值 | 口径/阈值 |
|---|---|---|
| signal_id | {{signal_id}} | 源-主题词哈希;trend_watch 落盘,跨次运行幂等 |
| 信号源与链接 | {{sources[]}} | ≥2 个独立源才算"事件"(单源=传闻,只 WATCH);逐源记首次见到时刻 |
| first_seen / 采样时刻 | {} / {} | UTC+本地双记;时效窗口(Q3)从 first_seen 起算 |
| velocity | {{vel}} | 二次采样(间隔 ≥30min)条目数/热度增速;`rising` / `peaked` / `fading` 三态 |
| 垂直相关性分 | {{rel_score}} | trend_scout 同口径:HIGH 整词命中 +25 / MED 部分 +10;≥25 过 Q1 |
| 同事件 wire 占位 | {{wire_n}} | Google News RSS 查询 top 结果中 wire 域名条数;≥3 且 <24h = 硬新闻否决触发 |
| 我们既有覆盖 | {{existing}} | 站内已有相关页(GSC/内链检索);有=优先刷新既有页而非新开 |
| 数据源与抓取时间 | {} | trend_watch.py 运行参数+trend_scout.py 输出(若已跑);单源失败明说,不猜 |

## 2. 四问闸门(选题决策;一票否决制)

四问全过 → GO;任一问不过按该问的降级规则走。Q1/Q3/wire 否决由脚本机检,Q2/Q4 人机各半——机检列印在每问"机检"行,人工判断填"人工"行,当场判不了的写"待核"并阻塞发布,不得默认通过(同 [pre-publish-checklist.md](pre-publish-checklist.md) 纪律)。

### 2.1 Q1 相关性:这事件与我们站点的垂直/品牌主张有关吗?

- **机检**:垂直词打分 ≥25(HIGH)=过;10–24(MED)=降级 WATCH(相关性不足,涨了再看);<10=DROP。
- **人工**:一票否决补充——即使 HIGH 命中,若事件与 [brand-records.md](../../references/content/brand-records.md) 的 Audience/"不服务谁"错位(蹭到的是我们不服务的人群),填不过。
- 依据:检索是漏斗瓶颈,不相关热点的流量不进漏斗;引用行为发生在"引擎回答该垂直问题"的场景里。

### 2.2 Q2 信息增益可行性:48 小时内能做出 5–7 个净新观点吗?

- **机检**(gate 子命令):角度文件存在,且独家观点计数 ≥5(净新观点=与 top-10 竞品文集词重叠低于阈值的句段;IGS 近似口径,规格见第 0 节);<5=不过。
- **人工**:逐条列出净新观点清单(下表),写不满 5 条=信息增益不可行=不过。信息增益四源取材:反共识(须有证据支撑)/ 时效新鲜度(竞品内容与 LLM 截止之后的数据)/ 一线从业者(SME)引语 / 专有数据(自有调查、内部基准)——写前先审 SERP 列出"共识层",只写缺口(口径见 [quotable-content-examples.md](../../references/content/quotable-content-examples.md) 信息增益四源与 [content-strategy-framework.md](../../references/research/content-strategy-framework.md) 信息增益门槛)。

| # | 净新观点(一句话) | 增益来源(四源之一) | 证据/数据在哪 | 需要几小时 |
|---|---|---|---|---|
| 1 | {} | {} | {} | {} |

### 2.3 Q3 时效窗口:我们还在窗口里吗?(24–72h 判定)

- **机检**:first_seen 距今 **<24h 且 velocity=rising** → News 型候选(news sitemap 48h 窗口内还有完整生命周期);**24–72h** → Analysis 型候选(新闻位已被占,分析位还空);**>72h 或 velocity=peaked/fading** → 只 WATCH,挂既有页刷新队列(8–12 周分层节奏,见第 4.3)。
- 窗口与引用半衰期的关系:AI 引用半衰期约 4.5 周【调研 2026-10】(与 citation_panel.py decay 的 Profound 官方中位 11 天口径**并记两说**);热点单篇引用期望为正的窗口是天级,所以决策必须快,但**内容要按"发布后 4–5 周仍有引用价值"来设计**——写分析层与数据层,不写转述层。

### 2.4 Q4 独家视角:我们能不能加进对话里没有的东西?

- **机检**(gate 子命令):三选一自检——(a) 自有数据可算(内部数据/可复算的公开数据);(b) SME 可在窗口内给出具名引语;(c) 反共识且证据可溯源。全无=不过。
- **wire 硬新闻否决**(机检,优先级最高):Google News RSS 同事件 top 结果 wire 域名(路透/AP/法新/新华社/央媒,按 --market 从 markets 数据层取清单)≥3 条且事件 <24h → 判"硬新闻",**GO 强制降级 PIVOT**——我们赢不了 wire 源的首发与刷新速度,引擎引用会流向原始源。
- **人工**:一句话写下独家视角,写不出=不过(同信息增益门槛的"写不出这句话就不写")。

### 2.5 判定矩阵(脚本输出,人工复核)

| Q1 相关 | Q2 增益 | Q3 窗口 | Q4 独家 | wire 否决 | 判定 |
|---|---|---|---|---|---|
| ≥25 | ≥5 观点 | <24h rising | 三选一有 | 未触发 | **GO(News 型,24h 内发)** |
| ≥25 | ≥5 观点 | 24–72h | 三选一有 | 任意 | **GO(Analysis 型)** |
| ≥25 | ≥5 观点 | 任意 | 无 | 触发 | **PIVOT(转分析角度,见第 3 节)** |
| ≥25 | <5 或待核 | 任意 | 任意 | — | **WATCH(等 Q2 证据,deadline={{时刻}})** |
| 10–24 | — | — | — | — | **WATCH(相关性不足)** |
| <10 / 重复信号(与 backlog 词重叠 >70%) | — | — | — | — | **DROP(合并或放弃)** |

## 3. 放弃条件与转角度(PIVOT 的形态)

**直接放弃(DROP)的硬条件**:①Q1 <10;②与已判定信号词重叠 >70%(合并入既有决策件,不新开);③velocity=fading 且我们零起步——引用期望为负(新闻源仅占 AI 引用约 9% 且头部通吃【调研 2026-10】,下降段的残值不覆盖人写成本);④触发量产红线(见第 5 节)还想过闸。

**转"分析角度"(PIVOT)的形态**——硬新闻的时效位让给 wire,做引用位要的深度层:

| 形态 | 内容 | 被引逻辑 |
|---|---|---|
| 数据核对表 | 把事件数字逐条溯源、给出口径与基准 | 引擎沿"这个数字从哪来"溯源,分析层比转述层更常被引 |
| 时间线+影响分析 | 事件脉络 → 对 {{受众}} 意味着什么 | Q&A 结构+反例标注的深度表层特征 |
| 本地市场对照 | 事件在目标市场的对应物/差异 | 接 multilingual"一套事实,多种变体";小语种"唯一可用源"红利 |
| 操作层回答 | 受众因此该做什么(Decision 型) | 答案前置+next steps,常青引用 |

PIVOT 产出仍走本模板第 4 节发布闸,但 sitemap 退常规 sitemap(>48h 不进 news sitemap),时间戳与 dateModified 纪律不变。

## 4. 写作与发布动作(48h 管线)

### 4.1 写作(GO 后立刻,人写,不量产)

- 交稿走 [content-brief.md](content-brief.md)(News 型勾第 5 节 News 附加件:timeliness/事实核查/引语可归属/含意)或 Analysis 型勾 Guide/Comparison;首段三查与答案前置纪律不变(38–40% 的 AI 引用来自前 100 词)。
- 引用纪律按 [ai-citation-patterns.md](../../references/content/ai-citation-patterns.md):内联具名引用+带口径统计数字是被引的强形态【调研 2026-10:+30–40%;与 C-SEO Bench 未能重现通用增益的张力并记,见 geo-evidence.md 第三节】,转述他人数据会把引用输给原始源;**出站链接本身不是引用凭证**——链接给一手源是信任信号,被引靠信息增益。

### 4.2 发布动作清单(发布即执行,机器可验)

| # | 动作 | 通过标准 | 验收 |
|---|---|---|---|
| 1 | **news sitemap**(仅 News 型) | 只含近 48h 文章、≤1,000 URL、`news:publication`(名+语言)/`publication_date`(ISO 8601 精确到秒含时区)/`title` 三件套齐;Analysis 型退常规 sitemap | 验收命令照抄 discover-news-seo.md 第三节五查 |
| 2 | **IndexNow ping** | 发布流水线自动 ping(Bing/Naver/Yandex 消费;Google 不支持,靠 sitemap lastmod 准确度) | 部署后 curl 验 sitemap lastmod 已更新 |
| 3 | **显性时间戳** | 页面可见"发布于 {时刻}/更新于 {日期}"(市场格式以 market_lint 为准);`datePublished`/`dateModified` 与真实改动对齐——纯日期 bump 可被检测且反噬 | 人工+market_lint 日期格式检查 |
| 4 | **schema** | NewsArticle(headline/datePublished/dateModified/image)+Publisher,与可见正文逐字一致;不为富结果新增问答类标记 | schema_lint.py |
| 5 | **Discover 侧**(可选) | `max-image-preview:large` + ≥1200px 大图 | site_audit.py |
| 6 | **发布闸** | [pre-publish-checklist.md](pre-publish-checklist.md) 全过(机检脚本全绿+人工条目) | 逐条打勾落盘 |

### 4.3 分层刷新(发布不是终点;8–12 周节奏)

- **D+2**:勘误与数据回填(事件后续数字/口径修正);`dateModified` 只在内容真变时 bump。
- **W+2**:首批引用测量——目标问题 5–10 条进 citation_panel 采样,记基线,14 天复测(multilingual-workflow.md 第十二节四行报告制);AI 引用半衰期 4.5 周【调研 2026-10】/11 天(Profound 官方中位)两口径并记,复测日历按短口径排、刷新投入按长口径排。
- **W+8~12**:分层刷新接 [content-refresh-playbook.md](../../references/content/content-refresh-playbook.md) 与 [content-decay-signals.md](../../references/content/content-decay-signals.md)——decay 信号触发优先于固定日历;半衰期决定的不是"要不要刷新"而是"何时开始盯"。

## 5. 合规红线(起草前必读;两条都过才准写)

1. **量产蹭热点=scaled content abuse**:同一事件 >2 篇/日、模板化改写(换实体不换结构)、无人工实质参与的批量产出——AInvest 案的崩塌路径【调研 2026-10】;本模板强制人写(Q2 观点清单逐条有人名/数据归属),trend_watch.py 对同一信号只允许一个活跃 GO 决策件(重复否决)。
2. **真实性与署名**:热点场景的数字/引语高风险——每个数字有来源、引语可归属一手来源(News 型六考量);拿不准的事实宁可 [要追加: 待核] 阻塞发布,不抢先发错——错误热点页的信任损耗大于晚发 12 小时。

## 6. 运营与度量(接 monitor 守护)

- 监控节奏:热点信号扫描每 3 小时(cron/launchd,复用 monitor.py 部署模板);单篇期望为正但半衰期天级【调研 2026-10】——3 小时是"不漏 rising 段"的采样密度,不是发文频率。
- 判定输出路由:GO=critical 级走 notify.py 即时通知;WATCH=info 级日批;DROP 不通知只入库。trend_watch.py 退出码接 CI 与通知(见第 0 节)。
- 度量口径:发布记基线(曝光 0)→ 14 天复测;考核"被看见或被引的份额"(28 天曝光 >0 比例/AI 被引 O/X),不考核"N 篇/月"产出(multilingual-workflow.md 第十二节 12.2 度量口径)。

## 0. scripts/trend_watch.py 规格(实施规格,当前未实装;与本文档同轮入仓)

> 分工:**trend_scout.py 是雷达**(一次性拉 HN+Reddit 回答"现在有什么热点"),**trend_watch.py 是闸门**(多源信号+四问判定+决策件落盘,回答"这个热点我们该不该追、以什么形态追")。watch 不替代 scout——scout 的输出可作 watch 的输入源之一。

```text
名称:scripts/trend_watch.py(stdlib 零依赖,urllib+json+sqlite3,同 monitor.py 技术底座)
状态:规格稿(2026-10-11);实装时登记见 Method Notes。

子命令:
  watch   拉信号源 → 打分去重 → 机检四问(Q1/Q3/wire)→ 落盘信号库与决策件草稿
  gate    对单个 signal_id 补做 Q2/Q4 机检(角度文件存在性/观点计数/三选一自检),出终判
  backlog 查看信号库(open/go/pivot/watch/drop 各态,含 deadline 与到期升退级)

用法:
  python3 scripts/trend_watch.py watch  [--vertical "llm seo"] [--market XX]
        [--config trend_watch.json] [--panel panel.json] [--json] [--brief-dir briefs/]
  python3 scripts/trend_watch.py gate  --signal-id ID --angle-file 角度.md
  python3 scripts/trend_watch.py backlog [--status open|go|pivot|watch|drop] [--days 14]

输入:
  --vertical  垂直词(空格分隔 token;打分口径同 trend_scout:HIGH 整词 +25 / MED +10)
  --market    市场码(markets.json 18 市场数据层):决定热搜源、wire 域名清单、语言与 locale 参数
  --config    JSON:trend_watch.json{ signal_sources[](默认开:Google Trends 每日热搜 RSS/
              Google News RSS/Reddit rising/HN topstories;zh 市场默认加:微博热搜/百度热搜;
              X/Twitter 无 key 明说跳过,不猜——trend_scout 纪律),
              vertical_tokens[], wire_domains[](按市场), competitors[],
              thresholds{ relevance_min=25, velocity_resample_min=30, window_news_h=24,
              window_analysis_h=72, wire_dominate_n=3, ig_views_min=5, dedup_overlap_pct=70 } }
  --panel     可选 citation_panel 面板:读"该话题我们是否已被引"——已被引的信号优先刷新既有页
  --angle-file gate 用:选题人按第 2.2 节表格写的角度文档(净新观点清单)

信号源(纯 stdlib 可拉性,2026-10 核实):
  Google Trends 每日热搜 RSS   trends.google.com/trending/rss?geo={XX}      XML,免 key ✅
  Google News RSS 检索         news.google.com/rss/search?q=..&hl=..&gl=..  XML,免 key ✅(wire 检查用)
  Reddit rising                reddit.com/r/{sub}/rising.json               JSON,免 key ✅(hot 之外补 rising 段)
  HN topstories                hacker-news.firebaseio.com(同 trend_scout)   JSON,免 key ✅
  微博热搜                     weibo.com/ajax/side/hotSearch                 JSON,公开端点;被拦=skipped 明说
  百度热搜                     top.baidu.com/api/board?platform=wise         JSON;同上,失败明说不猜
  X/Twitter、抖音/巨量算数      需 key/登录——不入默认源,不猜

输出:
  briefs/trend-{signal_id}-{YYYYMMDD}.md  本模板第 1/2 节字段的预填决策件(人补 Q2/Q4 人工半边)
  .seo-monitor/trend_watch.db(sqlite)     信号库:signal_id/sources/first_seen/velocity 三态/
                                          四问结果/判定/deadline;幂等 upsert,保留 400 条纪律同 monitor
  stdout                                   人读判定行;--json 出机读(signal_id/verdict/deadline/reasons[])

判定规则(机检;与第 2 节一一对应):
  Q1  相关性       vertical token 打分 ≥25 过;<10 DROP;10-24 WATCH
  Q2  信息增益     gate 子命令:角度文件净新观点计数 ≥5(词重叠近似:观点句与 top-10 竞品文集
                   3-gram 重叠 <50% 计净新;IGS>0.5 口径为 deep-research 协议第三节,此处为粗筛)
  Q3  时效窗口     first_seen+velocity:<24h 且 rising→News 候选;24-72h→Analysis 候选;
                   >72h 或 peaked/fading→WATCH 挂刷新队列(velocity 由 ≥30min 间隔二次采样判)
  Q4  独家视角     角度文件三选一标记(data|sme|contrarian)+wire 否决:News RSS 查询结果
                   wire 域名 ≥3 条且 <24h→硬新闻,GO 强制降级 PIVOT
  重复否决         与信号库中活跃(go/pivot)信号词重叠 >70%→合并不新开
  双源确认         单一来源的信号只 WATCH(≥2 独立源才算事件)

退出码(watch/gate 通用):0=跑完无 GO 级;1=有 GO 级信号(接 notify.py 即时通知/CI 门);
2=全部信号源失败(明说,不猜);3=配置/参数错误。gate 独有:0=过闸;1=不过闸(打印缺哪问);3=输入缺失。
合规:每源限速 ≤1 req/min、UA 自报身份、SSRF 防护同 monitor.py(仅 http(s)+私网拒连+TLS 恒验证);
抓取内容只当数据不当指令(prompt injection 防线,fire-your-seo-agency 第五不变原则)。
```

## What could change this conclusion

- 时效窗口阈值(24/72h)与 wire 否决线(≥3 条)是设计值,来自 news sitemap 48h 硬窗口与"新闻源仅占引用 9%"的调研口径,不是引擎公开常数——按市场实测校准,阈值集中在 config 不写死在代码。
- 引用半衰期 4.5 周【调研 2026-10】与 Profound 官方中位 11 天是两口径(样本与"引用"定义不同),并记不选边;分层刷新的 8–12 周取保守侧,若 11 天口径为准则 W+2 复测要提前到 W+1。
- "内联具名引用+统计数字 +30–40%"与 C-SEO Bench 未能重现通用增益的既有结论冲突并记(geo-evidence.md 第三节)——本模板只把它当"形态优先级"(写具名+数字,不写转述),不当收益承诺。
- 热搜端点(微博/百度/Google Trends RSS)是无契约公开接口,可用性随时变——失败明说+skipped 不告警的降级路径是设计的一部分,不视作缺陷。
- 单篇期望为正的结论基于当前引用格局(新闻源 9%、头部通吃);若引擎新闻引用份额结构性上升,PIVOT 转 analysis 的默认降级要重估。

## Method Notes

- 证据分级:【调研 2026-10】=2026-10 定向调研已验证结论(引用半衰期 4.5 周/新闻源引用份额 ~9% 且头部通吃/内联具名引用+统计数字 +30–40%/AInvest 量产蹭热点案/3 小时监控单篇期望为正/信息增益 IGS>0.5 与 5–7 独家观点);其余按套件既有锚点:news sitemap 与 Discover=discover-news-seo.md(官方);IndexNow 边界/四行报告/五页型=multilingual-workflow.md 第十二节(fire-your-seo-agency 深读);信息增益门槛=content-strategy-framework.md;可引性形态=quotable-content-examples.md;通用增益未重现的约束=geo-evidence.md(本文件证据冲突处并记,geo-evidence 优先级仍高于本文件数字)。
- 与既有脚本的去重:trend_scout.py(HN+Reddit 雷达)保留不动,trend_watch.py 复用其打分口径;monitor.py 不改——watch 的 3 小时 cron 复用 monitor 部署模板与 notify.py 分级路由;citation_panel.py 只读不写(--panel 输入)。
- 入仓登记清单(实装轮执行,当前轮只入文档):①templates/content/trend-jack-playbook.md 入仓即被 self_check.py 七段式守护(须含本三节,已含);②trend_watch.py 实装时:data/capability-matrix.json 登记(templates/scripts 双向覆盖由 test_capability_matrix.py 守护,模板文件入仓时也要登记)+CAPABILITY_MATRIX.md 同步+tests/test_trend_watch.py 离线 fixture 金标+SKILL.md 脚本计数与命令行同步(SKILL.md 禁改范围的主会话裁决口径见 freshness-log-20261011.md 计数口径备注);③markets 数据层:wire_domains 逐市场清单进 markets.json 或 config 默认值,俄/中市场的"国家通讯社=被本土 AI 引用的高速通道"原则(multilingual-workflow.md 跨区原则 14)用于建名单。
- 已知坑:热搜快照无历史——first_seen 是"我们首次见到",不是事件真实起点,窗口判断偏保守是特性不是 bug;velocity 三态在低频源(Trends RSS 日更)上不可判,自动退化为"只看 first_seen";决策件 deadline 到期未处理由 backlog 升级为 info 告警(防"过期 GO 还在写")。
