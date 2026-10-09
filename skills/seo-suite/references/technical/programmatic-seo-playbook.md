# 程序化 SEO 作战手册(全生命周期)

> 建立于 2026-10-09。案例与 sitemap 结构当日实测核实(方法见第九章来源)。本文管"从零到规模化怎么打":选词→数据→URL→模板→内链→索引→风险→测量。**质量阈值、页型地板、100/500 闸门、goose 八模式逆向/7 维打分/vs 蓝图不在本文重复**,见 [programmatic-seo-gates.md](programmatic-seo-gates.md);**12 种页面模式清单**见 [playbooks.md](playbooks.md)。三层关系:playbooks 选模式 → 本文跑生命周期 → gates 卡质量红线。

## 一、选词与模式发现

先有可寻址查询,再谈建页。模式没验证需求就生成 = 最大的浪费。

**1. 查询模式挖掘(正则表,跑在自己的词表上)**:

| 查询正则 | 模式 | 意图 | 需求证据看什么 |
|---|---|---|---|
| `(.+) vs (.+)` | 对比 | 高购买 | GSC 是否已有 impressions |
| `(.+) alternative(s)?` / `alternative to (.+)` | 替代 | 高购买 | 竞品名数量×自家相关度 |
| `(.+) for (.+)`(for dentists/for startups) | 垂直人群 | 中购买 | 行业/角色词有限列举 |
| `(.+) near me` / `(.+) in (.+)` | 本地 | 高行动 | 仅当有真实本地存在(见 playbooks 地点行) |
| `(.+) integrations` / `how to connect (.+) to (.+)` / `(.+) (.+) integration` | 集成 | 高购买 | 工具对数量=笛卡尔积上限 |
| `(.+) to (.+)`(币种/单位换算) | 换算 | 信息 | 值域×值域组合量 |
| `best (.+)` / `(.+) template` / `(.+) example` | 清单/模板 | 中 | 竞品 SERP 占位 |
| `what is (.+)` / `(.+) 是什么` | 术语 | 低购买 | 仅作家底,不作主力 |

**2. 四个数据源(按证据强度排序)**:

- **GSC 长尾(最强)**:自家已有 impressions 8–30 位、 queries 含模式词的,是"页面还没建/没建好"的直接证据。导出走 `gsc_mining.py`(striking distance 模式);词按上面正则归类后聚合出"每模式可寻址量"。
- **PAA(People Also Ask)**:对种子词抓 PAA,拆出模式变体;PAA 问题可直接进模板 FAQ 块。
- **Autocomplete/suggest**:种子词逐字母扩展(`a`、`b`…后缀),拿真实用户措辞;成本低但只覆盖头部,不能当需求量证据。
- **竞品 URL 逆向(最系统的模式来源)**:拉竞品 sitemap 按 URL 正则聚类,完整正则表与四分类/缺口分析法见 [programmatic-seo-gates.md](programmatic-seo-gates.md) 第八节,不重复。

**3. 收口**:候选模式过 gates 第八节的评分权重(需求 30/意图 25/模板可行性 20/数据可得 15/竞争缺口 10),≥50 才进第二章。需求侧最低证据门槛:GSC 或 SERP 上能看到 ≥3 个同模式真实查询变体,否则视为白空间,先用 5–10 页手工验证。

**4. SERP 意图匹配检查(评分后、建页前)**:每个模式抽 3 个变体词看 SERP 排的是什么:

| SERP 上排名的页型 | 对 pSEO 模式页的判定 |
|---|---|
| 同模式生成页(竞品的 vs//integrations/) | 格式已被认可,正面或缺口切入 |
| 编辑长文/评测清单 | SERP 要综述——纯生成页难排,慎入 |
| 强域名聚合页(百科/大平台) | 只做该聚合页盖不住的长尾值 |
| 工具/计算器 | 生成页需内嵌可用工具,纯文字出局 |
| 本地包/地图结果 | near me 模式转 Google Business 路线,pSEO 页非主解 |

格式不匹配=搜索量大也拿不到,这一步淘汰掉"有量无格"的模式。

## 二、数据层(唯一数据是护城河)

模板可以抄,数据不能。三层层级与合规:

| 层级 | 定义 | pSEO 价值 | 合规要点 |
|---|---|---|---|
| **自有数据** | 产品日志、用户行为、自有调研、实测 | 最高——竞品无法复制 | 脱敏;不泄用户隐私 |
| **许可数据** | API、付费数据源、公开但可核实的官方数据(汇率/规格/名录) | 高——拼覆盖与更新速度 | 读 license 是否允许再展示/缓存;标注来源与 as-of 日期 |
| **合成数据** | LLM 生成描述、推断标签、拼装文案 | 低——只能当填充,不能当独立价值 | 永远需要事实字段锚定;纯合成=薄内容 |

纪律:**每页至少一块"只有这个站能给"的数据块**(Wise 的实时汇率、Zapier 的真实 trigger/action 列表),否则模式降级为拼装。

**数据 schema 设计**(生成前定死,字段即页面的变量):

```
record = {
  key:            唯一键(决定 URL slug,生成时强制唯一)
  axis_values:    模式轴上的值(币种对/工具对/城市…)
  facts:          事实字段(结构化,来自自有/许可层,带 source+as_of)
  proof_assets:   截图/图表/实测数据(防"纯文字页")
  derived:        派生文案字段(由 facts 生成,LLM 仅做语言润色)
  quality_score:  逐记录质量分(字段完整度),低于阈值→不生成或 noindex
  freshness:      数据更新周期(价格类=日,规格类=季);过期→自动重跑或下线
}
```

缺字段策略写在 schema 里:必填字段缺失→**不生成**(宁可少页);可选缺失→模板区块级条件渲染,不留"Lorem/待补充"。数据审计清单见 playbooks.md 实施步骤第 2 步。

**可寻址量估算**(进第三章前必算):`|值1域| × |值2域| × |locale数|` 是理论上限,**可索引页数 = 理论上限 × 有查询证据的组合占比 × 过质量地板的记录占比**。对上限做"哪些组合值得做"的裁剪(裁剪依据回第一章的需求证据),而不是生成后靠 noindex 收尸——noindex 的页仍会耗抓取预算。

**数据更新管道**(上线即运转,不是上线后补):

```
数据源(按 schema 的 freshness 字段排程)
  → 拉取/清洗 → 与上次快照 diff → 只对变化记录重渲染
  → 变更页 bump sitemap lastmod + 推 IndexNow
  → 停更数据源登记 discontinued(页头降级显示 as-of,抑制"最新"文案)
```

价格/汇率类日更,规格类季更,名录类月更——节奏写进 schema,不靠人记。停更序列静默陈旧比不更新更糟(见 playbooks.md rampstack Data Surface Integrity)。

## 三、URL 与信息架构

**1. 模式×值的 URL 设计**:一个模式一个目录,值按固定顺序拼 slug:`/{pattern}/{value1}[-{value2}]`。实例(Wise/Zapier/Nextdoor 实测):

- 币种对:`/{locale}/currency-converter/usd-to-eur-rate`(值序固定,usd-eur 与 eur-usd 是两页不同意图)
- 工具对:`/apps/{app1}/integrations/{app2}`(有序对,反向是另一页)
- 城市:`/city/{san-jose--ca}/`(双连字符分隔值内空格)

规则:小写、连字符、`<100` 字符、不带 query 承载主内容(Wise 的 `?amount=` 变体只作辅助变体)、尾斜杠一致——细则已在 gates 第五节,不重复。

**2. 目录深度**:主内容页距首页 ≤3 点击;层级镜像信息架构(state→city→neighborhood),不在 URL 里堆层级(hub 用内链表达,不用 URL 深度表达)。

**URL 设计反模式**(评审时按此拉清单):

| 反模式 | 为什么错 |
|---|---|
| URL 里带日期/版本号 | 数据更新即换 URL,权重断代 |
| 值序不固定(同一对两个方向随机) | 自我竞争;有序对,反向另立页 |
| query 参数承载 facet 并全部可索引 | 组合爆炸烧预算(见下 facet 阈值) |
| 模式混目录(`/tools/x-vs-y/`) | 后台无法按目录控索引/分析 |
| slug 用 id 不用值 | 值可读=锚文本可读=相关性信号丢失 |

子域 vs 子目录:pSEO 页默认子目录(权重共享);只有当模式与主站语义完全不同、且会稀释主爬取预算时才考虑子域——那通常是"该不该做这个模式"的问题,不是 URL 问题。

**3. sitemap 分片**:

- 硬限 **50,000 URL / 50MB**(gates 第五节),先到先拆
- **按页型分片优于按序号分片**:Wise 的 sitemap 索引按页型拆(send-money / currency-converter / swift-codes / iban / routing-number / compare…各一个子索引),单页型出问题可单独重提交
- 片内顺序=优先级:头部放最该被抓的批次
- `<lastmod>` 用**数据更新时间**而非生成时间(伪造检测见 `sitemap_audit.py`)
- noindex 页不入 sitemap

**4. facet 控制阈值**:筛选组合(类目×价格×标签…)默认**不生成可索引页**;仅当组合同时满足:① GSC/SERP 有真实查询证据 ② 该组合下实体数 ≥3 ③ 与已有页内容差异过地板——才升级为可索引。其余 facet 保持动态参数 + robots 屏蔽。防索引膨胀的总闸见 gates 第六节。

## 四、模板工程

**1. 模板结构 = 固定区块 + 变量区块,先画变量覆盖矩阵**:

| 模板区块 | 消费的变量 | 该区块是否逐页不同 |
|---|---|---|
| TL;DR/首答 | axis_values + facts 摘要 | 必须不同 |
| 对比表/数据表 | facts(逐记录) | 必须不同 |
| 深度段落 | derived(facts 锚定) | 必须不同 |
| 截图/图表 | proof_assets | 必须不同 |
| CTA | 场景化变量 | 应不同 |
| 通用信任块/页脚 | 无 | 允许相同 |

**覆盖度检查**:变量区块占正文比例 ≥60%(与 gates "模板样板 >60% = 惩罚候选"对齐);**任一"必须不同"区块在两页间完全一致 → 该记录退回数据层**。模板质量的 7 维打分(内容深度/独有价值/数据丰富度/新鲜度/内链/CTA 融合/schema)沿用 gates 第八节,发布前对每批抽高/中/低变体各一页打分。

**2. 防 doorway 的最低差异化要求**(gates 第三节"换城测试"的操作化):每个"必须不同"区块至少 N 个事实字段驱动(N≥3);页面至少包含 1 个**只属于该记录**的元素(独有截图/独有数据点/该值特有的 FAQ);两页标题+H1+首段任一完全相同即阻断发布。差异不够的值域宁可合并进聚合页。

**3. 标题/描述生成的防重复**:

- 准备 **3–5 个标题公式**按记录轮换(句式/词序不同,不是同义词替换),全批次生成后跑标题集合唯一性检查——重复即换公式重生成
- 标题含值对(`USD to EUR`)与当年/实时事实(汇率、日期)提升区分度;长度按市场(日文 32 字符等,走 `market_lint.py`)
- meta description 同法;描述公式数可少于标题,但禁止"一句模板+只换变量值"全域套用

**4. 模板版本与渲染**:模板打版本号,每页记录 `template_version`(它是第八章 cohort 的分组键;模板一改=新 cohort,禁止静默热替换存量页)。渲染选型(SSR/SSG/CSR)按 [rendering-seo.md](rendering-seo.md) 决策表——pSEO 页内容必须服务端可达,meta 不依赖 JS 注入;静态生成器(Next.js/Astro)批量输出是最稳路径(与 gates 第八节 CMS 可行性三问一致)。

## 五、内部链接规模化

**1. hub-spoke 自动化**:每个模式一个 hub(hub 定义=该模式的聚合页:全部值的可浏览入口+模式级说明), spokes(值页)生成时**自动回链 hub**;上层 hub 逐级向上(neighborhood→city→state→find-neighborhood,Nextdoor 实测即此四级)。hub 页本身是手写级质量,不是生成页。

**2. 相关页算法(同模式内自动出链)**:

- 同轴邻近:同值 1 的其他值 2(USD-EUR 页链 USD-GBP/USD-JPY)——取流量/转化 top,固定 3–5 条(gates 第五节)
- 共现:同一 hub 下高频共同出现值
- 交叉模式:该值的对比页链它的集成页、换算页(只链真实存在的,禁止预生成死链)
- 禁止"全站最新 N 篇"式无关节点入相关位

**3. 锚文本多样性**:三档配比控制——精确值锚(`USD to EUR converter`)~30%、值+修饰(~40%)、自然语/品牌混入(~30%)。全站同一模式清一色精确锚=规模化操纵信号。落地页内链密度 3–5 条/千词(gates 第五节),生成器里做成参数不是手活。

**4. 孤儿页零容忍**:每批发布前跑"生成集−入链集"差集,孤儿页补进 hub 或相关位后才发布;入链少于 2 的页标记复查。

## 六、索引与抓取预算管理

**1. 分批发布节奏**:50–100 页/批,观察 2–4 周(与 gates 第二节一致);每批一个可追踪的 cohort id(供第八章)。发布顺序=需求证据强的值先发,不是字典序。节奏样例(单模式冷启动):

| 周 | 动作 |
|---|---|
| 0 | hub 页 + 首批 50–100 页(最强值),过闸门+抽检后发布 |
| 1–2 | 观察索引/抓取;补内链修正;不动模板 |
| 3–4 | GSC 判读首批 cohort;模板修一批 → 第二批发布 |
| 5+ | 首批出流量信号 → 放大批次至 100;零信号 → 停量先修数据 |
| 常态 | 每周一批,cohort 看板滚动;淘汰机制(第八章)同步启动 |

**2. IndexNow**:批量提交新/更新 URL,**注意 Google 不支持 IndexNow**——支持方为 Bing、Yandex、Naver、Seznam、Yep(官方 indexnow.org,核实于 2026-10-09)。Google 侧靠 sitemap lastmod + 高质量内链 + GSC 提交;多市场站对 Naver/Yandex 市场尤其值得配。实施要点:站根放 key 文件;单次 POST 上限 10,000 URL,分批提交与发布节奏对齐;只提交"可索引且内容实际变更"的 URL(拿它当日更心跳=自毁信用)。

**3. 爬取预算监控(日志法)**:>10k 程序化页的站必须做(gates 第六节),方法走 [log-analysis.md](log-analysis.md):

- Googlebot 每日抓取量、按目录切片:程序化目录占比 vs 该目录流量贡献,抓取多流量少=低价值页在烧预算
- 唯一 URL 抓取率、重复抓取集中在哪几页(该合并/该缓存)
- 抓取但 noindex 的比例高 → 信号传递浪费,收 robots

**4. 新站/新目录的"探测期"应对**(社区观察,非官方文档,方向性):新域名或新目录常先被索引一小部分(数百页量级)再逐步放开。应对:保持节奏持续分批(探测期停滞不发更糟);把首批打造成最强 cohort(数据最全、内链最多);不要探测期没流量就批量 noindex——那是把未来的索引资格也关掉;用 GSC 页级数据确认"已发现未索引"的量,发现量在涨=正常推进。

## 七、质量与风险

**闸门数字全部引用 [programmatic-seo-gates.md](programmatic-seo-gates.md)**:100 页 WARNING / 500 页硬停 / 唯一度 40%·30% / 分批纪律 / 页型地板——本文不另设阈值,执行以 gates 为准。本节补三条 gates 未展开的边界:

**1. 站群与 doorway 的界线**:同一模式复制到 N 个域(城名/行业名域名互链导流)= Google doorway 定义的多站点形态,手工惩罚高危;单域内同模式页有真实差异化数据=可规模化(gates 第四节安全清单)。判别法:把两个域(或两页)的差异字段拉出来,若只剩域名和 logo——是站群,砍。

**2. site reputation abuse(站点声誉滥用)规避**:政策(2024-03 发布,2024-11 扩展到"租用站点排名信号"的更多形态)针对借强势域发布第三方内容蹭排名。pSEO 场景的红线:接受第三方付费内容进自己高权目录、合作方内容无站点所有者实质监督就上线路径。规避:第三方数据块标注出处、编辑监督留痕(review 记录)、不让第三方页面占据与主站语义无关的模式。EEA 侧 2026 出现"违规部分独立降权"的执行动向(方向性,见来源),别赌区域差异。

**3. scaled content abuse 的自证**:保留每批次的"人审记录+数据源记录+更新记录",被算法误伤或人工审查时可自证流程;这同时是 gates"无正当理由页"里"正当理由"的实体证据。

## 八、测量(页面级 cohort,不看全站平均)

**1. cohort 定义**:一批发布、同一模板版本、同一数据快照的页面集合为一个 cohort。全站平均会掩盖"一个模板 -90%、整体 -30%"的塌方(反模式见 playbooks.md rampstack 层)。

**2. 每 cohort 追踪**(GSC 按 URL 过滤,按周):

| 指标 | 判读 |
|---|---|
| 索引率(已索引/已提交) | <60% 于 4 周→回查质量与内链 |
| 展示 | 起量慢但增长=模式成立 |
| 点击、位置分布 | 均位 8–20 的 striking distance 值→优先加内容/内链 |
| 抓取量(日志) | 抓而不收=质量信号不足 |
| 转化(按 cohort) | 模板 CTA 变体对比 |

cohort 间对比(批次 A vs B)是模板迭代的依据:改模板→新 cohort→与旧 cohort 对照,禁止改完就推广到全部存量(先增量验证)。**判读规则预注册**:cohort 上线前先写下"什么算成/什么算败"(如:8 周索引率≥60% 且展示周环比两次为正=模式成立),避免看完数据再挑标准;与 playbooks.md rampstack 层的预注册纪律同源。

**3. 淘汰机制——零流量页 90 天处置阶梯**:

- 0–30 天:不动(索引爬坡期)
- 31–60 天:零展示 → 检查索引状态与入链,补内链/并入 hub
- 61–90 天:仍零展示 → 数据增强一次(补事实字段/加 proof 块)重渲染
- 90 天:仍零展示 → 三选一:**并入最近的聚合页**(301)/ **noindex 留功能** / **410 下线**并从 sitemap 移除
- 处置动作记录进 cohort 日志;批量 410 前确认无外链与转化,防止误杀长尾

## 九、案例拆解(2026-10-09 实测核实)

**核实方法声明**:四案的 URL 结构/sitemap 均当日直接抓取各站 sitemap 与 robots 核实(非转述博客);流量数字为第三方估算,各家口径差异大,只作量级参考。

**1. Wise(货币页,~60M 月访问的第三方估算)**:
- URL:`/{locale}/currency-converter/{from}-to-{to}-rate`(值序固定),辅以 `?amount=` 变体;换算、send-money、SWIFT、IBAN、routing-number、cost-of-living、机场换汇等多模式并行
- sitemap 索引按**页型**分片;仅 currency-converter 即 13+ 个子片×每片顶满 50,000 URL;help center 再按 12+ 语言分片(合计百万级 URL,第三方称 24 个月 7K→1.7M 索引)
- 护城河=自有实时汇率+费用对比数据;页内是活的换算器+走势图+费率提醒订阅(功能性内容,非文字拼装)
- robots 对参数化换算视图 `Disallow: /*/*/currency-converter/`——facet 收敛的现场示范
- 可借鉴:页型分片、locale×值对的矩阵扩张、"数据块即内容"

**2. Zapier(integrations,~2.6M 月访问估算)**:
- 三层 URL:`/apps/{app}/integrations`(应用主页)→ `/apps/{a}/integrations/{b}`(有序工具对)→ `/apps/{a}/integrations/{b}/{id}/{zap-slug}`(具体自动化模板页)
- zap-templates 子索引 **336 片×1,000 URL**(~33.6 万模板页),apps 索引每片 2,500——**片刻意做小**(远小于 50K 上限),重提交与增量抓取更快
- 护城河=自家平台真实的 trigger/action 元数据+用户建好的 zap;页面内容即产品功能清单,无法被外站复制
- 可借鉴:小片策略、三层漏斗(头部应用→工具对→具体模板)逐层收窄意图

**3. Nextdoor(邻里页,~35 万个 neighborhood)**:
- URL:四级信息架构 `/find-neighborhood/`(州入口)→ 州页 → `/city/{city}--{state}/` → `/neighborhood/{slug}--{city}--{state}/`;值内空格用**双连字符**
- 城市/邻里页标题按页型公式("San Jose, CA | News, Crime, Lost Pets, Free Stuff"),描述由该城事实生成(本地安全/友好度/公园等)——同模板但数据块逐城不同
- 护城河=UGC 本身:每页的真实邻里动态、本地帖流,模板只是容器
- 注:此案在常见 pSEO 案例 roundup 中少被引用(搜"Nextdoor programmatic"命中的多为其广告产品),结构为本手册当日实测;它演示的是"社区数据喂模板"路线
- 可借鉴:层级式 hub(州→市→邻里)内链自动化、`--` 值分隔约定

**4. Webflow(模板页+showcase)**:
- 模板市场:`/templates/{type}/{slug}` 详情页+类目页,市场 1,000+ 模板(第三方口径);更大的 pSEO 面是 **Made in Webflow showcase**:`/made-in-webflow/website/{slug}` 用户作品页 ~10 万(2 片×50,000),`/made-in-webflow/{tag}` 标签聚合页 8,732 个
- sitemap 索引按**实体类型**分片(profiles/tags/showcase/apps/manual)且由 CloudFront CDN 分发——大规模静态分发的工程参考
- 护城河=用户提交的模板与作品(UGC 双飞轮:创作者要曝光→站要内容);Webflow CMS 单集合 10K 条上限(gates 第八节)决定了它的 pSEO 主要靠 showcase 而非 CMS 硬堆
- 可借鉴:UGC 供给的规模化内容+按实体分片 sitemap;同模式见 Kisi 用 Webflow 快速落地页+内链做到 +300% 流量(Webflow 官方案例)

**四案共性**:① 值域确定且可枚举(币种对/工具对/地理/模板);② 数据来自自家产品或社区,外人拿不到;③ sitemap 按页型/实体分片;④ 模板中的"活"部分(换算器/trigger 列表/本地帖流)就是独立价值,文字只是包装。反向推论:**没有自有数据供给的模式,四案一个都没做**。

## 来源

- 实测(2026-10-09):`wise.com/sitemap` 及其子索引、`wise.com/robots.txt`、`zapier.com/robots.txt` 与其 sitemap 子索引、`nextdoor.com/city/san-jose--ca/`、`webflow.com/sitemap.xml`(重定向至 CloudFront)与 showcase/tags 子索引
- [practicalprogrammatic.com Wise 案例](https://practicalprogrammatic.com/examples/wise)、[Zapier 案例](https://practicalprogrammatic.com/examples/zapier)(页内数据点与流量估算)
- [withdaydream Wise 拆解](https://www.withdaydream.com/library/playbooks/wise)(7K→1.7M 索引,24 个月)、[OMNIUS Wise 案例](https://www.omnius.so/blog/wise-case-study)
- [Nextdoor neighborhood pages 官方说明](https://help.nextdoor.com/s/article/About-neighborhood-pages)、[about.nextdoor.com](https://about.nextdoor.com/)(350K neighborhoods)
- [Webflow 官方 pSEO 文章](https://webflow.com/blog/programmatic-seo)、[Kisi 案例](https://webflow.com/blog/kisi-and-webflow-seo)
- [IndexNow 官网](https://www.indexnow.org/)(支持引擎列表)、[Google: site reputation abuse 政策更新 2024-11](https://developers.google.com/search/blog/2024/11/site-reputation-abuse)、[2024-03 政策公告](https://blog.google/products-and-platforms/products/search/google-search-update-march-2024/)
- 生命周期框架与闸门衔接:本套件 [programmatic-seo-gates.md](programmatic-seo-gates.md)、[playbooks.md](playbooks.md)、[log-analysis.md](log-analysis.md)、[link-architecture-patterns.md](link-architecture-patterns.md)
