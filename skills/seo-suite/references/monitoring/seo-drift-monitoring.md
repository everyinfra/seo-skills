# SEO 漂移监控（基线 / 对比 / 历史）

> 建立于 2026-10-09。架构与规则参考 [AgriciDaniel/claude-seo](https://github.com/Agrici/claude-seo)（MIT）`skills/seo-drift/`。按本套件证据约束改写。
> 定位："SEO 的 Git"——先存基线，再定期对比，把静默劣化变成可归因事件。
> 惩罚处置（手动动作类型学 / reconsideration 流程 / 负面 SEO 防御 / 恢复期策略）见 [penalty-recovery](penalty-recovery.md)——归因到 L5"处罚"分支后转该文件。

## 一、三命令模型

| 命令 | 作用 |
|---|---|
| baseline | 抓取页面并存 13 元素快照 |
| compare | 当前页 vs 最近基线，跑 17 规则 |
| history | 同 URL 全部基线/对比的时间线 |

存储：本地 SQLite（单库，URL 归一化后哈希索引）。

## 二、13 个捕获元素

页面层：title / meta description / canonical / robots 指令 / H1 数组 / H2 数组 / H3 数组 / JSON-LD 数组 / Open Graph 字典（九项来自 HTML 解析）；性能：Core Web Vitals 字典；传输：HTTP 状态码；完整性：html_hash 与 schema_hash（**SHA-256**，分别对正文与 schema 内容）。

URL 归一化：scheme/host 小写、去默认端口 80/443、query 参数排序、去 UTM、去尾斜杠。

## 三、17 条对比规则

**CRITICAL（1–8，立即行动）**
1. JSON-LD/Schema 完全消失
2. Canonical URL 变更
3. Canonical 被移除
4. 新增 noindex 指令
5. H1 全部消失
6. H1 文本大改（相似度 <0.5）
7. Title 标签消失
8. 状态码 2xx → 4xx/5xx

**WARNING（9–14）**
9. Title 文本变化
10. Meta description 变化
11. CWV 指标退步 **>20%**（p75 LCP/INP/CLS）
12. Lighthouse 性能分掉 **10+**
13. OG 标签被移除
14. Schema 内容修改（schema_hash 变但 schema 仍在）

**INFO（15–17）**
15. 新增 Schema
16. H2 结构变化
17. 内容哈希变化（html_hash，兜底）

## 四、实施要点

- 4xx/5xx 页仍要捕获（状态码本身是被跟踪的漂移信号），不是跳过
- CWV 抓取失败存 null 并跳过 CWV 规则——**不猜数**
- 抓取走 SSRF 防护（只允许 http(s)、禁内网地址、TLS 恒验证）
- 适用节奏：每次发版后 compare；每周全站 compare；改版前先 baseline

## 五、算法更新归因层(2026-10-09 并入)

**数据源**:Google 官方 Search Status Dashboard 的 Ranking 历史是最强"官方传感器"(只报确认事件);Semrush Sensor(活跃;**2026-09-18 全市场重算波动基线,历史分不可直接比**)/MozCast(活跃,偏美)/Algoroo(存活)为旁证;**RankRanger 实质死亡**(2022 被收购后不独立销售,2025 清理历史数据)——勿依赖单一传感器,固定面板会漏(2026-06-08~12 社区观测波动未被捕捉)。

**归因流程(官方《Debugging drops》+行业实践)**:
1. 先排除数据假象(GSC data anomalies 页;clicks-only 还是 clicks+impressions 同降);
2. 下降形态:断崖全站→算法/spam/安全;逐年重复波形→季节性(拉 16 个月+Trends 验证);单页/单模板→技术;缓慢下滑→内容相关性;
3. 时间对齐:下降首日 vs 官方更新窗口,**同时对照自家发布日历**——区分技术事故最硬的信号;
4. 类目级传感器旁证;
5. GSC 分层(query/page/device/国家);**impressions 平+clicks 降→不是算法,是 SERP 特性/竞品截流(如 AIO)**;
6. **结论时点:rollout 完成后等 1–2 周**;2026 更新密集(8/9 月连续 spam),须先排除上一更新余波与更新重叠。

**2024–2026 官方时间线要点**(完整清单见 status.search.google.com):每年 3–4 次 core+1–3 次 spam;2024-01 后 **reviews 更新零次**(系统改持续迭代不再公告);2026 出现 **Discover update**(2/5)与超短 spam(19.5 小时,3/24);**2024-08-15 官方 ranking bug(4.5 天)证明技术事故与算法在同一官方流——归因必须能区分**。

**algorithm-updates 数据文件最小字段集**(漂移监控自动比对用):
```json
{"id":"2026-03-core","engine":"google","type":"core|spam|reviews|discover|bug_incident|unconfirmed_volatility","start_date":"2026-03-27","end_date":"2026-04-08","status":"complete|rolling_out","official_url":"…","source_tier":"official|vendor|community","scope":"global","impact_notes":"一句话","last_verified":"2026-10-09"}
```
**联动规则**:告警窗口 ∩ 更新窗口非空 → 打"疑似算法"标签而非直接升级;end_date 必填(归因窗口=end+7 天宽限);last_verified 驱动月度复核。**跨市场**:Yandex 官方博客会公告(ИКС 2026-02);Naver 无官方看板(统搜改革等仅博客转述,source_tier=community 降权);Bing 无算法公告流(只有 Webmaster 数据)。

## 五、与其他参考的联动

漂移规则命中的项直接路由：Schema 变更 → schema 校验参考；CWV 退步 → 性能参考；noindex 新增 → 索引审计；title/meta 变化 → 内容规范。

## 六、来源

- 13 元素/SQLite DDL/17 规则/归一化规则：[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-drift/SKILL.md`、`references/comparison-rules.md`、`scripts/drift_baseline.py`

## 增量:对照组归因与发布回归(百仓扫描批 2/4)

- **对照组归因**(seo-monster rank_attribution):改动页 vs 匹配对照组的前后对比+置信区间——比单纯前后对比强一档;
- **发布回归清单**(notfair seo-drift):基线快照→diff——**redeploy 覆盖了标题/元描述、canonical 或 noindex 翻转、schema 消失、索引页数下降**——每次发版后自动比对(与 13 元素基线互补:那个防漂移,这个防"改版踩坏")。

## 流量诊断五层协议 + DiD 参数(rampstack/seo-monster 精读,百仓深扫)

**五层根因顺序**:L1 确认变化真实(tracking 断档/bot/口径/季节性,**要 YoY 不要 MoM**;GSC clicks 与 analytics sessions 同向波动 within 10-20%,显著背离=tracking 问题)→ L2 定位(国家/设备/区块/品牌 vs 非品牌/落地页)→ L3 页面级 → L4 技术(**"Recent deploys are the prime suspect"**)→ L5 外部(算法/竞品/需求/处罚)。
**L2 模式表**:单国跌=本地算法或 hreflang;仅移动跌=移动可用性;品牌词跌=品牌级问题(宕机/声誉/处罚);非品牌跌=算法;单页跌=页面级;全站跌=惩罚/技术/迁移/算法。
**L3 判读**:位置跌+SERP 不变=质量/新鲜度;**位置稳+CTR 跌=SERP 特性变化(AIO/广告)——页面可以不掉排名而掉流量**;去索引=技术;同日 deploy+drop=强相关非证明,要找机制。
**九条失败模式**(照抄要点):跳到算法归因是懒惰答案;无正常基线则一切波动皆警报;**品牌 vs 非品牌由不同团队负责**;四源并用(GSC+Ahrefs+analytics+日志)单源诊断禁止;不许提前安抚"算法会恢复"。
**假设单句模板**:"[Property] lost [magnitude] starting [date] because [cause], evidenced by [data], recovery requires [actions], timeline [duration]"。
**DiD 对照参数**(seo-monster):pre=56 天(≥2× post)/post=28/gap=7 天 washout;闸门=控制页≥3、treated pre 点击≥5、控制页 pre 点击≥5;lift CI(±1.96 SE)三态判定;GSC 断代检测(impression bug 2025-05-13~2026-04-27;num=100 弃用 2025-09-11)窗口重叠时 clicks 为唯一可信指标;**"server-side page-level split test 是唯一真因果检验"**。
**告警矩阵默认值**(crawlseo):TRAFFIC_DROP 7 天点击 ≤−20%(当期≥5);POSITION_CHANGE 28 天均位恶化 ≥2 位;CRAWL_ISSUES 健康分 <70;VITALS 最近 5 份报告 ≥2 份 LCP>2.5s 或 CLS>0.1;健康分=100−8×CRITICAL−3×WARNING−1×INFO。

## 诊断清单细化 + 回归四件套 + DiD 实现细节(rampstack/iannuttall/seo-monster 源码深读,2026-10-09)

### 五层协议的 checklist 级细化(rampstack seo-traffic-diagnosis/references/diagnosis-checklist.md)

**L1 拉动清单**:GSC clicks 与 impressions(近 90 天逐日)+analytics 同窗 organic sessions+YoY 同期+可过滤时的 bot 流量。校验项:日期口径对齐;窗口内无 analytics 停摆;**窗口内无 tag manager 发布**;GSC clicks 与 sessions 同向(±10–20% 内);YoY 同形态→季节性而非异常;无节假日/行业事件解释。

**L4 技术回归症状表**(症状→可能原因):

| 症状 | 可能原因 |
|---|---|
| 部署后全站骤降 | robots.txt 全封 / 误加 sitewide noindex / 路由断裂 |
| 页面 404/410 | URL 结构变更、缺重定向 |
| 页面 5xx | 服务器/托管故障,可能 CDN 配错 |
| Render mismatch | JS 渲染对爬虫失效(框架升级后高发) |
| hreflang 断裂 | 跨国流量掉但其他市场位移 |
| 批量 canonical 变更 | 改版后 canonical 指向错误 URL |

L4 校验项补:重定向须 1 跳且 301;受影响 URL 无 4xx/5xx 尖峰;sitemap 含受影响 URL 且新鲜;hreflang 互指且指向活 URL;Googlebot 抓取率正常(服务器日志);**逐条比对 deploy 日期与流量下降日期**。

**L5 三判读**(L1–L4 全净时):下降落在已知更新日→大概率算法性,审计内容质量与 E-E-A-T,恢复常需等下一个更新周期;掉位且有新强势域名进 SERP→竞争位移,审计对方内容并更新自己;全行业搜索需求下滑→非己方问题,管理预期。

**诊断不清时的 4 步**(不强行下结论):列 top 2 假设各附证据→推荐对两者都有效的最低风险动作→指出能区分两个假设的数据→提出采集该数据的监控计划。"Stakeholders prefer honest uncertainty to confident-but-wrong."

**交付模板**:What happened 1 句 / Why 1 句 / What we're doing 3–5 条 / When to expect recovery+置信度 / What to watch for(恢复或恶化的前导指标)。诊断正文 7 段:Summary、Symptom、逐层发现、根因假设、行动计划、恢复预期、监控计划;4–10 页。

### 回归四件套(iannuttall/seo technical-watch 源码,一次编排并行跑)

| 组件 | 口径 |
|---|---|
| crawl-diff | BFS 抓取→与上一 run 快照 diff,**7 字段**:status/title/meta_description/canonical/h1/indexable/contentHash;变更分 added/changed/removed 三类;**newErrors=after≥400 且 before<200**;indexabilityFlips 单列;快照入库供下次对比 |
| index-watch | URL Inspection 逐 URL:单次 ≤100 个、dailyLimit ≤2000;每 URL 保留最近 20 次尝试(拿到成功后修剪);**quota 被限或属性错误后,剩余 URL 全部标 deferred、不再发请求**;产出 changed/regressions/recoveries/alerts 四分类 |
| index-monitor | sitemap 驱动的同能力(有 sitemap 时替代逐 URL) |
| link-recover | 找有搜索价值(点击/展示下限可配)的可恢复 URL |

**编排纪律**:findingCount = crawl 高优先建议 + index currentIssues + recovery high/medium;failed+quotaBlocked+deferred 计为「未完成检查」而**不算缺陷**——"Do not treat incomplete checks as SEO defects"。index-watch 固定四条 caveats:URL Inspection 报的是 Google 已索引快照非 live 测试;PASS/NEUTRAL/FAIL ↔ indexed/excluded/invalid;excluded 或 canonical 差异可能是有意的(复核而非默认缺陷);本地配额账本(保守 UTC 日上限)看不到其他机器/客户端对 URL Inspection 的调用。

### DiD 实现细节(seo-monster rank_attribution + iannuttall measure-change 互补)

- **控制组构造**:默认 section(URL 首路径段)池;section 池 <3 页自动回退 site-wide 并注记;控制页 pre 点击 ≥5 才入池。
- **公式**:peer_trend_ratio = mean(各控制页 post/pre 点击比);counterfactual = treated_pre × ratio;lift = treated_post − counterfactual;CI 由 ratio 的 ±1.96 SE 推出 lift_lo/lift_hi。
- **判定五态**:lift_lo>0→likely_positive;lift_hi<0→likely_negative;跨零→inconclusive;**treated pre<5→insufficient_data;控制页<3→insufficient_control——数据不足本身就是一种 verdict,不许硬给方向**。
- **confounders 块**(每次必返):data_regime_breaks(GSC impression bug 2025-05-13~2026-04-27、num=100 弃用 2025-09-11,窗口重叠即检出)→position_reliable 标志;parallel_trends_assumption;algo_update_note——"查 Search Status Dashboard change_date 前后 ~2 周的 core/spam 更新;DiD 经控制组吸收全站性更新,吸收不了页面类型特定的更新"。
- **iannuttall 变体**(equal-finalized-calendar-windows-v1):前后等长 finalized 日历窗(GSC America/Los_Angeles 时区),可选 controlScope/controlTarget;adjusted delta = control-ratio counterfactual;**置信度纪律:GSC 证据 partial→confidence 降一档;每窗 finalized 天 <7 或 after 窗被截→verdict=not-enough-data,不给方向**;caveats:position 是 impression-weighted;query 匿名化缺行≠零流量。

## 操作参数与规则边界增量(claude-seo 深读 2026-10-09b)

- **Rule 1 的弃用类型豁免**:schema 全消失时,仍受支持的类型(Product/Review/LocalBusiness 等)按"富结果将快速掉出 SERP"处理;**已停展类型(FAQ/HowTo 等)的消失不算富结果损失**,降级记录——避免把清理死标记误报成 CRITICAL。
- **操作参数集**:baseline 可 `--skip-cwv`(无 API key 场景);compare 可 `--baseline-id N` 指定历史基线,**默认取最近一条**;history 支持 `--limit`;compare 完成后可把 JSON 结果喂报告器生成 HTML 漂移报告(人读交付物)。
- **错误路径纪律**:无基线→提示先跑 baseline,不硬比;URL 不可达→报 fetch 错误,**不猜页面状态**;SSRF 拦截(私网 IP)→绝不绕过;SQLite 库不存在→首次使用自动建库(非错误);存储层查询一律参数化占位符,不做字符串拼接。
- **交叉路由补全**(在现有四条之外):canonical 变更/移除→索引与规范化审计;状态码 2xx→4xx/5xx→技术诊断;OG 标签移除→社交分享分析;H1 结构变化→内容与 E-E-A-T 复核。
- **CWV 采集失败的处理**:CWV 字段存 null 且比较时跳过 CWV 规则——缺数据跳过规则,而不是拿旧值顶替。
