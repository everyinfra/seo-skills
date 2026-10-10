# 审计报告三模式规范(report-modes)

> **模板性质**:渲染规范,不是报告母版——母报告仍按 [full-seo-audit.md](full-seo-audit.md) / technical-audit.md / on-page-audit.md / entity-audit.md 产出,本规范只定义"同一份 Findings 按受众裁成 exec / dev / prospect 三种视图"的字段与纪律。三份视图讲的是同一组事实:任何模式下出现的数字,都必须能在母报告里找到出处。
> **数据来源**:Sitebulb(受众分层裁剪)/ Semrush Copilot(Today's priorities 优先行动流)/ Ryte(impact 双栏,borrow-specs A1)/ claude-seo(建议四字段,borrow-specs E4)。施工图见 [references/research/borrow-specs.md](../../references/research/borrow-specs.md) A1·A2·E4 节。标注纪律与全库一致:【官方】=一手口径,[推断]=本套件自定并注明。

_For: {报告作者} · 母报告: {所用的 audit 模板文件} · 渲染模式: {exec|dev|prospect} · 上次审计基线: {YYYY-MM-DD 或"无(首次)"} · 分数来源: health_score.py --json {文件名}_

> 占位符约定(双花括号=跨模式变量,实例化后不得残留):`{{delta}}`=与上次审计的主分差,仅两次样本口径一致时填写,否则写"样本口径不同,不可比"并附 coverage_note(Ryte 官方降级声明:样本<全站,两次分数不可比)· `{{new_since_last}}`="自上次审计新增"标注,首次审计标"首次"。

## The answer(怎么用本规范)

{一段独立成立:先按母模板出完整报告与 health_score.py --json,再按**读者是谁**选模式——exec 给 CMO/高管,只留分数、趋势、Top 3 损失与一句话结论;dev 给工程师,是按类分组的 rule-id 可勾选清单;prospect 给潜客,只讲发现量级与行业差距,不暴露内部阈值。三种模式都必带 Today's priorities 节与建议四字段(字段按模式裁剪,见第 4/5 节)。一表三裁的对照片段见第 6 节。只读这段的人不会错。}

## 1. exec 模式(给 CMO/高管)

只保留三块,再无其他:

1. **分数行**:主分+分档+趋势 {{delta}}(health_score.py 的 main_score+band;Weak/Fair/Good/Excellent 分档【Ahrefs 官方】)。
2. **Top 3 损失**:从 impacts[] 的"立即处理"栏(impact>0)按 impact 降序取前 3;每条=受影响面占比+一句"损失了什么",不给修法、不给 rule-id、不列表格。
3. **一句话结论**:母报告 The answer 压成一句(瓶颈+预期回收+时间窗)。

删除项:Findings 全表、Exclusions、Validation、Method Notes、建议四字段正文(四字段详情只进 dev 视图;exec 的结论句可保留预期数字)。

纪律:**"每多一个数字,被读的概率降一分"**——exec 全文独立数字 ≤8 组,超出即砍;砍掉的进 dev 视图,不是删事实,是换读者。

## 2. dev 模式(给工程师)

载体=rule-id 可勾选任务清单,每行固定五列:

```
- [ ] {rule-id} | {问题一句话} | {受影响面 hit/total(%)} | {fix 指令} | {bulk export 文件名}
```

- **rule-id**:health_score.py MAPPING 的规则 id(fetch/staging/robots/ai-bots/canonical/title/description/h1/headings/content/images/schema/og/links/sitemap/llms.txt/a11y/rendering/semantic-html/bluf/freshness/duplicate_title,以其当前全集为准)或 audit-rule-catalog.md 规则 ID——全清单统一用一套,不混。
- **受影响面**:照抄 impacts[] 的 hit_urls/total_urls,不四舍五入改口径。
- **fix 指令**:一句话可直接开工;细则链接 [audit-rule-catalog.md](../../references/technical/audit-rule-catalog.md) 对应条目。
- **bulk export 文件名**:每 rule-id 一个受影响 URL 清单文件,命名照 A2(SF 具名导出)`{类别} > {Issue 名}`,落盘形如 `bulk-exports/{category}/{rule}.csv`。
- **分组纪律【Semrush 官方杠杆规律】**:"修完一整类比分散修单条提分多"——按类别(Lumar 六大类,=impacts[] 的 category 字段)整组呈现;组头标**整组修完预期提分**,算法=反事实重算 `health_score.py --ignore {该组全部规则}` 前后 main_score 差,不重算时标 [est]。注意主分只数 CRITICAL【Ahrefs 口径】,纯 WARN/INFO 组对主分 +0,其预期提分写"主分 +0,WARN/INFO 子分 +X"。
- 组内按 impact 降序;ignored/SKIP 规则不进清单;impact=0 的零命中规则只进清单尾部"值得探索"组,不进正文(Ryte 双栏语义,与 health_score action 字段同口径)。

## 3. prospect 模式(给潜客)

结构=发现摘要+量级+行业差距:

- 每条发现:现象一句话+受影响 URL 数/占比(hit/total);排序按 impact 降序,取前 5-8 条。
- **不暴露内部阈值**:只说"X% 的页面缺 canonical",不说"我们的判定阈值是 Y%、扣分权重 Z"——阈值、权重、规则目录是交付后资产;给比例,不给判定线。
- 行业参考差距:只用公开基准;无公开基准标 [est] 或 [要追加: 数据源](E6 反编造守则),禁编造"行业中位数"。
- 不带 fix 指令与 bulk export 文件名(那是 dev 视图与交付后内容);Today's priorities 只留条目名+量级+{{new_since_last}} 标注。
- 语气=事实陈述,不制造紧迫感;指标全平时直接说 stable, no action needed(与 ai-visibility-weekly 周报纪律同源)。

## 4. Today's priorities 节规范(Copilot 口径)

三种模式的输出都必带此节(字段按模式裁剪),固定规则:

- **条数固定前 5-10 条**:不足 5 全列;超过 10 截断,尾行注明"另有 N 条见 dev 清单"。
- **排序 = 严重级 × 受影响面 × 修复成本**:严重级取 health_score 有效严重度,受影响面取 hit/total,修复成本人工标 S/M/L(成本越低越靠前);同分内 {{new_since_last}} 新增条目置前——新增即变化,变化优先暴露。
- **每条显式标注"自上次审计新增 {{new_since_last}}"**:与上次审计 findings 逐 rule-id 对比得出;首次审计全部标"首次"。
- **杠杆提示行**(节尾固定一行):"整类修完比单条分散修提分多——当前最大杠杆类:{category}(整组修完预期 +{n} 分)"【Semrush 官方杠杆规律】。
- 模式裁剪:exec=折叠进 Top 3 损失(每条只留现象+占比+新增标);dev=全字段(勾选框+fix 指令+export 文件名);prospect=条目+量级+新增标,无 fix。

## 5. 建议四字段(可证伪方法论,E4)

任何模式的建议条目(Action Plan / Priority Fixes / Today's priorities 条目)必附四字段:

1. **依据的第一性观察**:触发这条建议的原始观测(URL+数字+抓取日期),不是推论。
2. **依赖解锁关系**:它解锁什么(不修它,哪些后续动作无效)+ 它被什么解锁(前置是什么)。
3. **失败判定**:"怎么知道它失败了"——显式判据+观察窗(如"28 天后 X 未降即失败")。
4. **先行指标**:不重跑审计就能监控的信号(GSC/日志/SERP)+监控频率。

配套纪律(E4 全口径):审计末段点名"下次该看什么+本次测不了什么";失败判定触发过的建议进**停推清单**,下次审计显式排除,不复推。

**示例 1(修 canonical,Indexability)**

> 建议:修复 24 个页面的错误 canonical(改自指绝对 URL 并重提交)。
> - 第一性观察:2026-10-10 抓取,24/120 URL(20%)canonical 指向 staging.example.com;GSC 页面索引编制报告 12 页"已提交未编入",与命中集交集 9 页。
> - 依赖解锁关系:解锁内容层优化——这 24 页不回索引,title/正文改动无展示可言;无前置(索引层是第一层)。
> - 失败判定:修复+重提交后 28 天,GSC"已提交未编入"仍 ≥10 页(降幅 ≤2 页视同失败,小于采样噪声)。
> - 先行指标:GSC 页面索引编制报告计数,每 3 天看一次。

**示例 2(差异化 duplicate_title,Uniqueness)**

> 建议:26 个同模板页 title 逐页差异化。
> - 第一性观察:批内 26/120 URL(21.7%)title 两两相同,均出自 /blog/ 模板占位符未渲染(2026-10-10 抓取,4 组每组 ≥2 URL)。
> - 依赖解锁关系:前置=canonical 修复——先把"该索引谁"定下来,再谈"怎么区分";它解锁后续点击率优化(区分开的 title 才能各自抢 CTR)。
> - 失败判定:上线 28 天后,这 26 页的 GSC 展示仍集中在每组 1 页(其余展示=0),或复检 duplicate_title 命中 >5 页。
> - 先行指标:GSC 搜索分析按页过滤的展示数,每 7 天;SERP 快照抽 3 页核 title 生效。

## 6. 渲染规则:一表三裁片段示例

同一份母表(Findings 摘录,与 health_score.py --json 同源;示例数据):

```markdown
主分 71.7(Good;120 URL 样本,86 无 CRITICAL)| 上次 64.2(Fair)→ {{delta}} +7.5

| rule-id | 严重度 | 受影响面 | impact | 栏 |
|---|---|---|---|---|
| canonical | CRITICAL | 24/120(20%) | 1.80 | 立即处理 |
| title | CRITICAL | 18/120(15%) | 1.35 | 立即处理 |
| duplicate_title | WARN | 26/120(21.7%) | 0.87 | 立即处理 · {{new_since_last}} 本次新增 |
| robots | CRITICAL | 6/120(5%) | 0.45 | 立即处理 |
| llms.txt | INFO | 0/120(0%) | 0 | 值得探索 |
```

exec 片段(数字预算内,三块结构):

```markdown
# {site} SEO 健康:71.7 / 100(Good),较上次审计 +7.5 {{delta}}

**Top 3 损失**(按影响降序):
1. 24 页(20%)canonical 指向错误目标——页面在主动退出索引
2. 18 页(15%)title 缺失或超长——搜索结果门面缺位
3. 26 页(21.7%)title 完全重复——引擎无法区分页面(本次新增)

**一句话结论**:索引信号自相矛盾是唯一结构性损失,6 周内修复预计回收约 12% 展示量;其余层全部达标。
```

dev 片段(按类分组+五列清单+杠杆行):

```markdown
## Today's priorities(前 5 条,严重级×受影响面×修复成本)
1. `canonical` 24/120(20%)· 成本 M · {{new_since_last}} 否
2. `robots` 6/120(5%)· 成本 S · 否 —— 新增置前示例:若标"是"则进首位
3. `title` 18/120(15%)· 成本 M · 否
4. `duplicate_title` 26/120(21.7%)· 成本 L · {{new_since_last}} 本次新增
杠杆:整类修完比单条分散修提分多——最大杠杆类 Indexability(整组修完预期 +13.3 分)

## 修复清单(按类分组,组内 impact 降序)
### Indexability —— 整组修完预期主分 71.7→85.0(+13.3;重算 --ignore canonical,robots)
- [ ] `canonical` | canonical 指向 staging/外域 | 24/120(20%) | 逐页改自指绝对 URL 并重提交 GSC | bulk-exports/indexability/canonical.csv
- [ ] `robots` | 创收页误带 noindex | 6/120(5%) | 删 noindex 并重提交 | bulk-exports/indexability/robots.csv
### Rankability —— 整组修完预期主分 71.7→78.3(+6.6;重算 --ignore title)
- [ ] `title` | title 缺失/超长 | 18/120(15%) | 按市场口径补写(市场阈值换算见 multilingual-workflow) | bulk-exports/rankability/title.csv
### Uniqueness —— 主分 +0(WARN 不扣主分),WARN 子分 78.3→100
- [ ] `duplicate_title` | 批内 title 重复 | 26/120(21.7%) | 同模板页逐页差异化 | bulk-exports/uniqueness/duplicate-title.csv
### 值得探索(impact=0,零命中)
- `llms.txt`(INFO 0/120)——不进优先级,仅记录
```

prospect 片段(量级+行业差距,无阈值):

```markdown
# {site} 抽查发现(120 页样本,{YYYY-MM-DD})

- **20% 的页面在主动拒绝索引**(canonical 指向错误目标)——同类站点抽样常见水平约 5-8%[est]
- **21.7% 的页面标题完全重复**(上次抽查未见,属新增)
- **15% 的页面缺 title 或超长**

信号互相矛盾时,搜索引擎会自行选择收录哪个版本——通常不是你想让它收的那个。完整清单、判定口径与修复顺序见交付报告。
```

渲染纪律:三份视图的每个数字逐个对得上(71.7/24/20%/18/15%/26/21.7%/6/5% 只出现于母表已有的值);差异只在"讲多少",不在"数字不同";{{new_since_last}} 标注三份一致。

## What could change this conclusion

- {受众假设漂移:三模式画像(exec=CMO/dev=工程师/prospect=潜客)基于当前交付流程;受众复合时(如技术型创始人)允许混排,但数字预算仍按 exec 口径收紧。}
- {杠杆规律的边界:"整类修完比单条分散修提分多"是**分数口径**的规律——主分只数 CRITICAL URL 占比,纯 WARN/INFO 组对主分 +0;不得外推为流量规律。}
- {行业参考缺口:prospect 的差距表述依赖公开基准,缺失时只能 [est] 或 [要追加: 数据源],不得编造中位数。}
- {{{new_since_last}} 依赖样本一致:两次样本口径不同时,"新增"可能是采样差异而非站点变化,须与 coverage_note 同报。}

## Method Notes

- 数据源与口径:Sitebulb(受众分层)/ Semrush Copilot(Today's priorities 优先行动流)/ Ryte(impact=命中占比×严重度²,>0 降序"立即处理"、=0"值得探索"双栏,A1)/ claude-seo(建议四字段,E4);施工图见 [references/research/borrow-specs.md](../../references/research/borrow-specs.md)。组级预期提分的反事实重算法[推断]。
- 字段对齐:本规范所有排序与量级字段(rule/severity/hit_urls/total_urls/impact/action)与 health_score.py --json 的 impacts[] 逐字段同名;主分/分档取 main_score/band;{{delta}} 与 {{new_since_last}} 需保存上次审计的 --json 输出作基线。
- 禁编造:行业基准无公开来源一律 [est] 或 [要追加: 数据源];prospect 不暴露内部阈值;数字缺失写 [要追加: 数据源]。
- 符号:impact 双栏=立即处理/值得探索;修复成本 S/M/L;□(或 `- [ ]`)=未修/已修勾选;[est]=估算标注。
