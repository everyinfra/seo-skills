# 程序化 SEO 作战手册(全生命周期)

> 建立 2026-10-09，核对 2026-10-18（第九章案例结构当日 curl 实测）。本文管从零到规模化：选词 → 数据 → URL → 模板 → 内链 → 索引 → 风险 → 测量。阈值、页型地板、Google 政策原文、竞品逆向与模式打分见 [programmatic-seo-gates.md](programmatic-seo-gates.md)；12 种页面模式见 [playbooks.md](playbooks.md)。未注明出处的阈值都是**本套件口径**。

## 一、选词与模式发现

先有可寻址查询，再建页。

**1. 查询模式正则**（跑在自己的词表上；`pseo_pattern_mining.py` 内置同类正则）：

| 查询正则 | 模式 | 意图 | 需求证据 |
|---|---|---|---|
| `(.+) vs (.+)` | 对比 | 高购买 | GSC 已有曝光 |
| `(.+) alternative(s)?` / `alternative to (.+)` | 替代 | 高购买 | 竞品数 × 相关度 |
| `(.+) for (.+)` | 垂直人群 | 中购买 | 行业/角色可枚举 |
| `(.+) near me` / `(.+) in (.+)` | 本地 | 高行动 | 仅限有真实本地存在 |
| `(.+) integrations` / `how to connect (.+) to (.+)` | 集成 | 高购买 | 工具对数量 |
| `(.+) to (.+)`（币种/单位换算） | 换算 | 信息 | 值域 × 值域 |
| `best (.+)` / `(.+) template` / `(.+) example` | 清单/模板 | 中 | 竞品 SERP 占位 |
| `what is (.+)` / `(.+) 是什么` | 术语 | 低购买 | 只作家底 |

**2. 数据源**（按证据强度）：① GSC 长尾：`gsc_mining.py queries.csv` 输出的 striking distance（位置 5–20 且曝光 ≥20）里含模式词的查询，说明页没建或没建好；② PAA：拆模式变体，问题可进模板 FAQ 块；③ Autocomplete：拿真实措辞，只覆盖头部，不当需求量证据；④ 竞品 URL 逆向：见 gates 第八节。

**3. 收口**：候选模式按 gates 第八节权重打分，≥50 才进第二章。需求最低门槛：GSC 或 SERP 上能看到 ≥3 个同模式真实查询变体；不足就是白空间，先手工做 5–10 页验证。`pseo_pattern_mining.py` 按同一规则输出 GO / WATCH / 白空间。

**4. SERP 意图匹配**（建页前，每模式抽 3 个变体词）：

| SERP 前排页型 | 判定 |
|---|---|
| 同模式生成页（竞品的 vs/、integrations/） | 格式已被认可，可切入 |
| 编辑长文/评测清单 | 纯生成页难排，慎入 |
| 强域名聚合页 | 只做它盖不住的长尾值 |
| 工具/计算器 | 页内必须有可用工具 |
| 本地包/地图 | near me 走 Business Profile，不靠 pSEO 页 |

格式不匹配，量再大也拿不到。

## 二、数据层(唯一数据是护城河)

| 层级 | 例子 | 价值 | 合规 |
|---|---|---|---|
| 自有 | 产品日志、用户行为、实测 | 最高，竞品无法复制 | 脱敏 |
| 许可 | API、付费源、官方数据（汇率、规格、名录） | 高 | 读 license 能否再展示和缓存；标来源与 as-of |
| 合成 | LLM 描述、推断标签 | 低，只能填充 | 必须由事实字段锚定 |

每页至少一块"只有这个站能给"的数据（Wise 的实时汇率、Zapier 的 trigger/action 列表），否则模式降级为拼装。

记录格式同 `pseo_batch_gate.py`：每行 `{key, axis_values, facts:[{value, source, as_of, quality_score}], title, desc, h1, body}`；另记 `proof_assets`（截图/图表）、`freshness`（价格日更、名录月更、规格季更）、`template_version`。必填字段缺失 → 不生成；可选字段缺失 → 区块级条件渲染，不留"待补充"。审计清单见 playbooks.md 实施步骤第 2 步。

**可寻址量**：可索引页数 = |值1域| × |值2域| × |locale 数| × 有查询证据的组合占比 × 过地板的记录占比。按需求证据裁剪组合，不靠事后 noindex 收尸：noindex 页仍要被抓取。

**更新管道**：按 freshness 排程拉取 → 与上次快照 diff → 只重渲染变化记录 → 更新 `<lastmod>` 并推 IndexNow → 停更数据源登记 discontinued，页面显示 as-of、去掉"最新"文案（见 playbooks.md rampstack Data Surface Integrity）。

## 三、URL 与信息架构

**1. URL**：一个模式一个目录，值按固定顺序拼 slug：`/{pattern}/{value1}[-{value2}]`。实测样例：`/{locale}/currency-converter/usd-to-eur-rate`（反向是另一页）、`/apps/{app1}/integrations/{app2}`（有序对）、`/city/san-jose--ca/`（`--` 分隔值）。细则见 gates 第五节。主内容页距首页 ≤3 次点击；层级（州 → 市 → 邻里）用内链表达，不用 URL 深度表达。

反模式：URL 带日期或版本号（数据一更新就换 URL）；同一对值两个方向随机出现（自我竞争）；query 承载 facet 且全部可索引（组合爆炸）；多模式混一个目录（无法按目录控索引）；slug 用 id 不用值。

子目录还是子域：默认子目录。Google 抓取预算按主机名计，子域单独计算（[crawl budget](https://developers.google.com/crawling/docs/crawl-budget)）。想用子域时，先问"该不该做这个模式"。

**2. sitemap 分片**：
- 单文件上限见[事实表](../overview/facts.md#sitemap-limits)，拆分规则见 gates 第五节。
- 按页型分片，不按序号分片：GSC Page indexing 报告能按单个 sitemap 筛选，分片后就能分页型看索引（[原文](https://support.google.com/webmasters/answer/7440203)）。
- 不必按优先级排序：Google 说 URL 顺序没有作用（[原文](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)）。
- `<lastmod>` 写数据更新时间；`sitemap_audit.py` 查"构建日单日簇"类伪造。

**3. facet**：筛选组合默认不生成可索引页。同时满足三条才可索引：① 有真实查询证据 ② 组合下实体 ≥3 ③ 内容差异过地板。其余按 Google [faceted navigation](https://developers.google.com/crawling/docs/faceted-navigation) 处理：robots.txt 屏蔽或改用 `#` 片段；无结果组合返回 404；路径内筛选顺序固定。总闸见 gates 第六节。

## 四、模板工程

**1. 变量覆盖矩阵**：TL;DR/首答、数据表、深度段落、截图/图表必须逐页不同；CTA 应不同；信任块和页脚可相同。变量区块占正文 ≥60%，对应 gates"样板 >60% = 风险页"；`pseo_batch_gate.py` 以全批共有 5-gram 占比 >60% 告警。两页的"必须不同"区块完全一致 → 退回数据层。每批抽高、中、低变体各一页，按 gates 第八节 7 维打分。

**2. 防 doorway**（gates 第三节"换城测试"的操作化）：每个"必须不同"区块至少由 3 个事实字段驱动（N≥3）；每页至少 1 个只属于该记录的元素。`pseo_batch_gate.py`：两页 title + H1 全同 → STOP；只 title 重复或 title + 首段近重复 → WARNING。差异不够的值域并进聚合页。

**3. 标题与描述**：3–5 个标题公式轮换（换句式，不只换同义词）；生成后查标题集唯一性。标题带值对和实时事实（汇率、日期）。长度按市场查：`market_lint.py --market ja`（日文 title 32 全角）。描述禁止"一句模板只换变量"全站套用。

**4. 版本与渲染**：每页记 `template_version`（第八章 cohort 分组键）。内容服务端可达、meta 不靠 JS 注入，见 [rendering-seo.md](rendering-seo.md)。

## 五、内部链接规模化

- **hub-spoke**：每个模式一个手写级 hub（全部值的入口 + 模式说明）；spoke 生成时自动回链 hub，hub 逐级向上（Nextdoor：找社区 → 州 → 市 → 邻里）。
- **相关页**：同轴邻近（USD-EUR 链 USD-GBP、USD-JPY，取前 3–5 条）；同 hub 共现值；交叉模式（对比页链集成页），只链已存在的页；不放"最新 N 篇"。
- **锚文本**：精确值锚 ~30%、值 + 修饰 ~40%、自然语或品牌 ~30%；清一色精确锚是操纵信号。密度 3–5 条/千词，做成生成器参数。
- **孤儿页**：发布前算"生成集 − 入链集"，补进 hub 后才发布；入链 <2 的页复查。

## 六、索引与抓取预算管理

**1. 分批节奏**（与 gates 第二节一致）：每批 50–100 页，观察 2–4 周，每批一个 cohort id；需求证据强的值先发。冷启动：第 0 周 hub + 首批最强值；第 1–2 周只补内链、不动模板；第 3–4 周判读首批、修模板、发第二批；第 5 周起有信号就放大到 100 页/批，零信号就停量修数据；之后每周一批，第八章淘汰机制同步启动。

**2. IndexNow**（[indexnow.org](https://www.indexnow.org/)，核对 2026-10-18）：
- 参与方：首页列 Microsoft Bing、Naver、Seznam.cz、Yandex、Yep；[FAQ](https://www.indexnow.org/faq) 的提交端点多一个 Amazon（`indexnow.amazonbot.amazon`），另有全局端点 `api.indexnow.org`；登记表 [searchengines.json](https://www.indexnow.org/searchengines.json) 还列 Internet Archive，但它设了 `unsubscribe: true`。
- Google 不在以上任何名单里，本套件按"Google 不支持"处理；Google 侧靠准确的 lastmod、内链和 GSC 提交 sitemap。
- 规则：key 8–128 个字符（字母、数字、连字符），放站根 `/{key}.txt`；单次 POST 的 URL 数有上限（[事实表](../overview/facts.md#indexnow-batch)）；提交新增、实质更新、删除（404/410）和重定向的 URL，不重复提交没变的 URL；提交计入抓取配额，不保证收录。
- 工具：`indexnow.py key --out public/`；`indexnow.py submit --host example.com --key KEY --urls changed.txt`（自动按 10,000 分批）。多市场站对 Naver、Yandex 市场尤其值得配。

**3. 抓取监控**（程序化页 >10k 的站，方法见 [log-analysis.md](log-analysis.md)）：按目录切 Googlebot 抓取量，对比流量占比；抓得多、流量少 = 低价值页烧预算。看重复抓取集中在哪些页；抓取后 noindex 比例高就改为不生成。GSC 的 Settings → Crawl stats 看请求数、响应码、主机状态（Google 说不足 1,000 页的站不必看）。

**4. 新站或新目录起量**：Google 说每个站从同一个保守的抓取容量起步，站点健康且有需求时自动上调（[crawl budget](https://developers.google.com/crawling/docs/crawl-budget)）；新页或新站开始被抓取和索引可能要一周左右（[Page indexing 帮助](https://support.google.com/webmasters/answer/7440203)）。"新目录先收几百页再放开"是社区说法，量级未核。应对：持续分批；首批做成最强 cohort；起量慢不批量 noindex；看 Page indexing 里 "Discovered – currently not indexed" 的变化。

## 七、质量与风险

闸门数字和 Google 政策原文以 [programmatic-seo-gates.md](programmatic-seo-gates.md) 为准，本节补三条边界。

**1. 站群与 doorway**：把同一模式复制到多个域（城市名、行业名域名互链导流），对上 doorway 原文例子"按城市定向的多个域名导向同一页"和 scaled content abuse 例子"建多个站掩盖规模化"。判别：拉出两个域（或两页）的差异字段，只剩域名和 logo 就是站群，砍掉。

**2. 站点声誉政策**（[原文](https://developers.google.com/search/docs/essentials/spam-policies#site-reputation)，核对 2026-10-18）：第三方内容主要因宿主站的排名信号而发布在宿主站上；只有第三方内容本身不违规。
- 2024-03-05 宣布（当时称 site reputation abuse），2024-05-05 执行。
- 2024-11-19 澄清：白标、授权、部分持股等第一方参与，不改变内容的第三方属性；把内容挪到同域子目录或子域可能被视为规避（[博客](https://developers.google.com/search/blog/2024/11/site-reputation-abuse)）。
- 2026-08-30 起：EEA 外照常人工处置；EEA 内不再受人工处置影响，违规部分可能被归为与主域分开、单独排名（[博客](https://developers.google.com/search/blog/2026/08/update-site-reputation-policy)）。
- 人工审核看四点：呈现是否与宿主站一致、质量是否低于主站、署名与责任是否明确、同样内容是否出现在多个站。
- pSEO 规避：第三方数据块标出处；保留宿主编辑审核记录；第三方页不占与主站语义无关的模式。

**3. 自证材料**：每批保留人审、数据源、更新三类记录，用于被误伤或人工审查时自证；它也是 gates"无正当理由页"里"正当理由"的证据。

## 八、测量(页面级 cohort,不看全站平均)

**1. cohort**：同一批发布、同一模板版本、同一数据快照的页面。全站平均会掩盖"一个模板 -90%、整体 -30%"的塌方（见 playbooks.md rampstack 层）。

**2. 每 cohort 每周追踪**（GSC 按 URL 过滤）：

| 指标 | 判读 |
|---|---|
| 索引率（已索引 / 已提交） | 4 周 <60% → 回查质量与内链 |
| 展示 | 起量慢但在涨 = 模式成立 |
| 点击、位置 | 均位 5–20 的值 → 优先补内容和内链 |
| 抓取量（日志） | 抓而不收 = 质量信号不足 |
| 转化 | 对比模板 CTA 变体 |

索引率精确值看 Page indexing 报告按 cohort sitemap 筛选；`pseo_cohort.py` 用"有展示 = 已索引"估算，输出带 `[est]`。改模板就开新 cohort 与旧 cohort 对照，不静默替换存量页。**判读规则预注册**：上线前写下成败标准，如"8 周索引率≥60% 且展示周环比两次为正"（`pseo_cohort.py init` 的默认标准，建档后冻结）。

**3. 零流量页 90 天处置阶梯**：
- 0–30 天：不动。
- 31–60 天：零展示 → 查索引与入链，补内链或并入 hub。
- 61–90 天：仍零展示 → 补事实字段或 proof 块，重渲染。
- 90 天：仍零展示 → 三选一：301 并入最近聚合页 / noindex 留功能 / 410 下线并移出 sitemap。
- 处置记进 cohort 日志。有外链或排名词的页不处置：`pseo_cohort.py prune` 与 `prune_gate.py` 都判 NO-GO；410 前人工确认无转化。

## 九、案例拆解(结构实测 2026-10-18)

方法：`curl -sL -A 'Mozilla/5.0'` 抓 robots.txt 和 sitemap 索引，逐个子 sitemap 数 `<loc>`。流量只有第三方估算或厂商自述，只作量级参考。

| 站 | URL 模式 | sitemap 实测 |
|---|---|---|
| Wise | `/{locale}/currency-converter/{from}-to-{to}-rate`，另有 `?amount=N`、`/history`、`/chart` | 索引 27 项：15 个按内容类型拆的子 sitemap（send-money、currency-converter、swift-codes、iban、routing-number、compare、cost-of-living、airport-in-city 等）+ 12 个帮助中心语言 sitemap。currency-converter 170 片：169 片各自填满单文件 URL 上限，末片 47,695，共 8,497,695 条 |
| Zapier | `/apps/{a}/integrations` → `/apps/{a}/integrations/{b}` → `/apps/{a}/integrations/{b}/{id}/{zap-slug}` | zap-templates 336 片（每片 1,000，共 335,260）；双应用页 58 片（每片 2,500，共 144,065）；单应用页 4 片（9,910）；`/templates/details/` 500 片（499,999） |
| Nextdoor | `/find-neighborhood/` → `/find-neighborhood/{州}/` → `/city/{市}--{州}/` → `/neighborhood/{社区}--{市}--{州}/` | robots.txt 不声明 sitemap；层级靠页内链接（找社区页链 51 个州级页，加州页链 1,155 个城市页） |
| Webflow | `/made-in-webflow/website/{slug}`、`/made-in-webflow/{tag}`、`/templates/html/{slug}` | `webflow.com/sitemap.xml` 302 到 CloudFront；6 个子 sitemap 按实体拆：showcase 2 片（50,000 + 45,160）、tags 8,739、profiles 14,226、apps 345、manual 8,568（含 1,178 个模板详情页） |

- **Wise**：护城河是自有实时汇率和费用对比，页内有换算器、走势图、汇率提醒。robots.txt 注释说明要避免爬虫在参数上浪费抓取预算，屏蔽 `*redirectUrl=*`、`*/send-money/?sourceCurrency=*` 等；但 `?amount=` 变体进了 sitemap（抽样一个满额分片，其中 37,772 条，约 76%）。流量估算差异大：[practicalprogrammatic](https://practicalprogrammatic.com/examples/wise) 6,050 万/月，[daydream](https://www.withdaydream.com/library/playbooks/wise)（引 Ahrefs）5,440 万/月，[OMNIUS](https://www.omnius.so/blog/wise-case-study) 1,600 万+/月，均未注明测量日期。"24 个月内索引页 7K→1.7M"出自 daydream，未见 Wise 一手出处。
- **Zapier**：护城河是平台真实的 trigger/action 数据和用户建的 zap 模板。分片远小于 50,000 上限；"便于增量更新"是本套件推断，Zapier 未说明。流量：[practicalprogrammatic](https://practicalprogrammatic.com/examples/zapier) 称 260 万/月（未注明日期）。
- **Nextdoor**：邻里页汇总会员帖子话题、公开活动、公共机构公告和人口普查数据；会员对话只对认证会员可见（[官方帮助](https://help.nextdoor.com/s/article/About-neighborhood-pages)）。标题按页型公式且随季节变，实测 `San Jose, CA | Trick or Treat Map and News, Crime, Lost Pets, Free Stuff`；描述由该城事实生成。Nextdoor 自述覆盖 35 万+ 社区（[2026-03-09 新闻稿](https://about.nextdoor.com/press-releases/nextdoor-publishes-2025-transparency-report)），这是网络覆盖数，不是可索引页数。
- **Webflow**：护城河是用户提交的作品和模板（创作者要曝光，站要内容）。模板页 title 自称 "7000+" 模板，sitemap 只列 1,178 个详情页。CMS 限额见 gates 第八节。[Kisi 案例](https://webflow.com/blog/kisi-and-webflow-seo)是 Webflow 博客上的客户自述：3 个月自然会话 12K→50K（标题称 +300%），图表为 2018 年数据；做法是按内容类型建模板、用 Collection 自动出相关链接。

四案共性（本套件归纳）：值域可枚举；数据来自自家产品或社区；sitemap 按页型或实体拆；页面里"活"的部分（换算器、trigger 列表、邻里汇总）才是独立价值。没有自有数据供给的模式，四案都没做。

## 十、检查清单(按生命周期)

批次质量闸门见 gates 第七节，这里不重复。

| 阶段 | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 选词 | 模式需求 | `python3 scripts/pseo_pattern_mining.py --gsc queries.csv --urls urls.txt --json` | GO（≥50 分且 ≥3 变体）才建；白空间先做 5–10 页 |
| 选词 | 长尾缺口 | `python3 scripts/gsc_mining.py queries.csv` | striking distance 里有该模式词 → 进首批 |
| 选词 | SERP 格式 | 每模式 3 个变体词手查 SERP | 前 10 有同类生成页或工具页 → 通过 |
| 内链 | 深度、孤儿、锚文本 | `python3 scripts/site_crawl.py example.com --urls batch_urls.txt --out crawl.json`（清单 = 首页 + hub + 本批页），再跑 `link_graph.py --crawl crawl.json --json`、`orphan_fix.py --crawl crawl.json` | >3 层占比 0、无不可达页、本批零入链 0 个；link_graph exit 0（域名锚 ≤60%）；30/40/30 锚配比按 JSON 里的目标页锚分布手工计 |
| 索引 | IndexNow 投递 | `python3 scripts/indexnow.py submit --host example.com --key KEY --urls changed.txt --json` | 全部 200/202（exit 0）；403 = key 无效；422 = key 未部署或 URL 不属该 host |
| 索引 | 抓取陷阱 | `python3 scripts/log_session.py --log access.log --json` | 无 param_loop（同路径参数请求 >10）、deep_crawl（深度 >8） |
| 测量 | cohort 判读 | `python3 scripts/pseo_cohort.py init --cohort_id b01 --template-version v1 --urls b01.txt`；每周 `ingest --cohort b01 --gsc pages.csv`；`report --cohort b01` | 到期 PASS；FAIL → 修数据或模板，开新 cohort |
| 淘汰 | 90 天处置 | `python3 scripts/pseo_cohort.py prune --cohort b01 --backlinks bl.csv` | 只处置非 NO-GO 页；410 前人工确认无转化 |

## 来源

- 实测 2026-10-18：四站的 robots.txt、sitemap 索引与相关子 sitemap（Wise currency-converter 170 片全数）；Nextdoor 找社区页、加州页、San Jose 城市页和一个邻里页；`webflow.com/templates` 页 title。
- 第三方与厂商链接见第九章；Google 原文与 IndexNow 链接见各节。
- 本套件：[programmatic-seo-gates.md](programmatic-seo-gates.md)、[playbooks.md](playbooks.md)、[log-analysis.md](log-analysis.md)、[link-architecture-patterns.md](link-architecture-patterns.md)。
