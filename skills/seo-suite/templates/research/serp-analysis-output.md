# {答案式标题,例:"'X pricing' 是交易+商业混合意图:购物/评分/广告三特征齐上,信息型长文无入场券;PAA+视频两条路径可争"}

_For: {决策人} · Date: {YYYY-MM-DD} · Market: {市场/语言/locale} · Query set: {N 个查询} · Data pulled: {日期+数据源,注明地域/设备/个性化关闭与否}_

> 多市场站点:逐市场各出一份本报告,不合并。市场差异规则见 references/overview/multilingual-workflow.md。
> 市场差异注记:该 locale 的引擎/SERP 特殊结构(如 Naver 垂直、Yandex 区域性、AIO 覆盖差异)按 references/markets/{市场}.md 换算。

## The answer

{一段独立成立:这组查询的意图判定 + 主导页面类型 + 哪些 SERP 特征改写了点击分配 + 我们能否入场/该用什么形式。置信度(高/中/低)+ 一句话依据。只读这段的人不会错。}

## Key numbers

| 指标 | 数值 | 对比/阈值 |
|---|---|---|
| 分析查询数 | {} | |
| SERP 特征平均出现数/查询 | {} | 特征越多,自然结果通常越靠下(时点观测,记录首屏截图);是否真的分流点击,用 GSC 效果报告的「搜索外观」筛选验证,不凭特征数推断 |
| 意图分布(信息/商业/交易/导航) | {}%/{}/{}/{} | 单一意图≥70% 才可按单一策略对待(本套件口径,阈值可调) |
| 广告位平均数 | {} | 记录首屏有几个广告位;广告多时自然结果下移(时点观测) |
| 我们已有排名的查询数 | {} | 进 top10 的:{} |

## Query

| Keyword | Locale/device | Intent(判定依据) | 月搜索量 | 特征计数 | 我们的排名 |
|---|---|---|---|---|---|
|  |  | {按 keyword-intent-taxonomy.md 分类,写旁证} |  |  | {无则写 "—"} |

## Feature Matrix(九特征 × 有无)

逐查询打 √/—;「占据者」填当前拿到该特征的 URL。FAQ/HowTo 富结果已停止展示,不计入、不当争取目标。

| 特征 | 出现时通常说明 | Q1 | Q2 | Q3 | 我们是否具备资格 | 可做的动作 |
|---|---|---|---|---|---|---|
| 精选摘要 | 要直接答案 |  |  |  |  | {标题下紧跟完整回答,真实列表/表格} |
| People Also Ask | 还有相关疑问链 |  |  |  |  | {问题当选题,正文里清楚回答} |
| AI 概览/AI 模式 | 需综合多来源 |  |  |  |  | {可被抓取+事实可核对;无专门标记} |
| 知识面板 | 查询指向实体 |  |  |  |  | {官网信息一致+Organization schema} |
| 附加链接 | 导航/品牌型 |  |  |  |  | {结构+标题唯一性,全自动无标记} |
| 图片结果 | 想看样子 |  |  |  |  | {原创图+alt+图片站点地图} |
| 视频结果 | 操作/评测需求 |  |  |  |  | {独立观看页+VideoObject} |
| 本地结果 | 本地需求 |  |  |  |  | {商家资料 NAP 一致} |
| 购物结果 | 明确购买意图 |  |  |  |  | {Product schema 与页面一致} |

占据者记录:{特征→当前占据 URL,谁反复出现}。各功能的官方说法、能做什么和不能保证什么,见 [serp-feature-taxonomy.md](../../references/research/serp-feature-taxonomy.md)(已核)。展示由系统自动决定:精选摘要、附加链接都没有标记或申请入口,AI 概览/AI 模式没有额外要求([AI 功能](https://developers.google.com/search/docs/appearance/ai-features))。

## Competitive Landscape(竞争格局卡)

每个反复出现的域名一张卡;按 SERP 选对手,不按业务选。

- **{domain1}**:类型 {媒体/社区/工具站/竞品官网} · 反复出现 {N}/{总} 查询 · 主力页面形式 {教程/对比表/落地页} · 强项 {凭什么赢:内容形态/深度/外链} · 弱项 {可切入的缝}
- **{domain2}**:…
- **{domain3}**:…

## What Wins Here

- {从 top10 归纳:内容形式、结构、深度、新鲜度、E-E-A-T 信号}
- {哪些非蓝色链接位置占据点击,占据者是谁}

## Gaps / Opportunities

- {谁都没做好的角度/SERP 功能资格缺口/形式缺口}
- {明确不做的事:如为 FAQ 富结果堆问答}

## Recommended Actions

1. {动作→预期(资格/形式),不承诺展示位}
2.
3.

## 检查清单(逐项:检查什么 → 怎么查 → 通过/失败)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 抓取条件已记录 | 无痕窗口,目标市场的 locale 与设备,保存截图和日期 | 通过:每个查询有 locale、设备、日期、截图。失败:缺任一项 |
| 2 | 意图判定有旁证 | 对照 [keyword-intent-taxonomy.md](../../references/research/keyword-intent-taxonomy.md),在 Query 表「Intent」列写前 10 条结果的页面形态 | 通过:每个查询有旁证。失败:只凭词面 |
| 3 | 特征矩阵逐查询逐项打 √/— | 在截图上逐项核对九个特征;FAQ/HowTo 富结果不计入(都已不再展示,[日期](../../references/overview/facts.md#rich-results)) | 通过:矩阵无空格。失败:有空格 |
| 4 | 竞争格局卡只收反复出现的域名 | 数每个域名在 N 个查询里出现几次;市场有 UGC、比价、投诉站占位时 `python3 scripts/serp_occupancy.py --market XX "域名1,域名2"` | 通过:每张卡有「出现 N/总」。失败:按业务而非 SERP 选对手 |
| 5 | 同簇查询合并前先看 SERP 重合 | `python3 scripts/serp_overlap.py input.csv`(CSV:`keyword,前 10 条 URL 以分号分隔`) | 通过:同簇词重合 ≥4 条(四档:7–10 同文 / 4–6 同簇 / 2–3 互链 / 0–1 分开)。失败:重合 0–1 → 分开分析 |
| 6 | 动作只承诺资格与可理解性 | 搜 Recommended Actions 里的「保证」「一定」「排名」 | 通过:零命中。失败:承诺展示位 |
| 7 | 点击影响用数据验证 | GSC 效果报告 → 搜索外观筛选 → 该查询点击变化 | 通过:有前后对照。失败:只靠特征出现推断 |

## What could change this conclusion

- {数据缺口:SERP 为时点快照,不同地域/设备/个性化下功能组合会变}
- {仅相关非因果:特征出现≠点击分流成立;能定案的验证:GSC 搜索外观筛选看该查询点击变化(窗口含[GSC 数据异常期](../../references/overview/facts.md#gsc-anomaly)时 CTR 不可信,只看点击)}
- {样本局限:仅 {} 查询×1 次抓取;小众查询波动大}
- {继承假设:意图分类基于 {} 规则;AIO 覆盖口径随 Google 界面调整}

## Method Notes

- 数据源与抓取时间:{工具+日期};记录地域、语言、设备、个性化状态,最好附截图。已知坑:{AI 概览和 AI 模式的点击计入 Search Console 效果报告的「网页」类型,拆不出来;Google 的生成式 AI 效果报告(已全球开放,[日期](../../references/overview/facts.md#gsc-genai))只报展示次数([帮助页](https://support.google.com/webmasters/answer/16984139))}。数字缺失写 [要追加: 数据源],禁编造。
- 符号:特征计数=该查询出现的功能种类数;意图按 keyword-intent-taxonomy.md 分类,FAQ/HowTo 不计入缺口(见 serp-feature-taxonomy.md)。
- 展示由搜索引擎自动决定:本报告的「可做的动作」只影响资格与可理解性,不保证出现。
