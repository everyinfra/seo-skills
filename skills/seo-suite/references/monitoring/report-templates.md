# SEO 报告：按读者取舍，结论带证据

> 报告里含 AI 可见度或 AI 引用内容时，先读 [geo-evidence.md](../content/geo-evidence.md)。

## 用途

写周报、月报、季度复盘或给客户的 SEO 报告时读，数据来自你自己的 Search Console、GA4 等账号。整体表现填 [performance-report.md](../../templates/monitor/performance-report.md)，排名变化填 [rank-report.md](../../templates/monitor/rank-report.md)；指标口径见 [kpi-definitions.md](kpi-definitions.md)。

## 一、所有报告的共同规则

- **一条结论 = 数据 + 对比期 + 数据源 + 口径。** 缺任何一项，就只能写成「待核实」。
- **对比期**：环比用上一期同样长度的时间段，并对齐星期；有季节性时同时给同比。
- **数据截止**：写明截止日期。Search Console 最近几天的数据可能还不完整，不要拿来下结论。
- **口径不变**：筛选条件、品牌正则、渠道定义和上期一致；有变化时在开头说明，并尽量回算上期。
- **分清三种状态**：已上线（工程完成）、已观察到变化、原因已确认。不要把「已上线」写成「已见效」。
- **不做承诺**：不预测具体的排名、流量或 AI 引用涨幅；外部基准没有出处就不写。

## 二、不同读者写什么

| 读者 | 关心什么 | 放什么 | 不放什么 |
|---|---|---|---|
| 管理层 | 业务结果、风险、要不要投入 | 自然搜索带来的转化或收入（注明归因口径）、非品牌需求趋势、两三条主要变化及原因、风险、需要拍板的事 | 逐词排名、抓取细节 |
| 营销与内容 | 哪些主题和页面在涨、在跌 | 按主题簇和页面组的表现、上升与下降的页面、待刷新内容清单、AI 可见度抽样结果 | 服务器与部署细节 |
| 技术 | 能否抓取、能否索引、快不快、哪里报错 | 状态码分布、索引原因的变化、按模板拆分的 CWV 字段数据、错误清单与复现步骤、修复后的验证方法 | 营收数字 |
| 外部客户 | 做了什么、结果如何、下一步 | 管理层内容 + 本期完成事项 + 下期计划 | 内部成本、未核实的推测 |

管理层版控制在一页以内，细节放附录；技术版每个问题都给出受影响的 URL 样本。

## 三、异常怎么解释

按这个顺序写，每一步都附证据：

1. **现象**：哪个指标、变化多少、和哪个对比期比。
2. **范围**：全站，还是某个目录、模板、设备、国家或查询类型。
3. **时间线**：变化开始的日期，和发布记录、排名系统更新、季节因素逐一对齐。
4. **候选原因**：逐条列出，每条写支持或排除它的证据。
5. **置信度**：已确认 / 可能 / 待验证。
6. **下一步**：谁做、做什么、什么时候复查。

例：「8 月非品牌点击比 7 月少 12%，同比持平（Search Console，网页搜索类型，按网站聚合）。下降集中在 `/blog/`，从 8 月 5 日开始，与当日的模板改版对齐；抽查 20 个 URL，改版后 canonical 都指向了分页首页。置信度：可能。下一步：修复 canonical，两周后复查这批 URL 的索引状态和点击。」

## 四、月报骨架

```markdown
# 自然搜索月报：example.com（YYYY 年 M 月）
口径：数据源 / 筛选条件 / 品牌正则；对比期：上月、去年同月；数据截至：YYYY-MM-DD

## 本月结论（3 条以内，每条带数据和对比期）
## 关键指标（见 performance-report 模板）
## 变化与原因（现象 / 范围 / 证据 / 置信度）
## 排名与可见度（见 rank-report 模板）
## 风险与待决事项
## 下月行动（负责人 / 截止日期 / 验证方式）
## 附录：口径说明、事件日志、原始导出位置
```

## 五、常见误区

- 只报涨不报跌，或者没有对比期。
- 把 Search Console 的平均排名当主指标。
- 把相关写成因果，例如「加了结构化数据，所以 AI 引用涨了」。
- 把工具估算的流量价值当收入。
- 引用没有出处的行业基准。
- 行动项没有负责人、截止日期和验证方式。

## 完全装载:报告工程约束与锚定评分(百仓深扫)

**自包含 HTML 报告硬约束**(every-app seo-report):禁外部资源/禁 script;图必须内联 SVG/CSS bar 且**数字同时印在文字里**;目标 <80KB、硬上限 500,000 字节;**禁反引号和 `${`**(模板字面量语法);链接一律 target="_blank";summary <2,500 字符(给不打开页面的读者);finding 三段 Problem/Change/Expected effect;**"二十条 findings 的报告是失败报告"**;固定收尾节 "How this report was made"(Tools/Verified 分列)。
**六维营销评分+收入公式**(ai-marketing):Content 25%/Conversion 20%/SEO 20%/Competitive 15%/Brand 10%/Growth 10%;等级 85=A/70=B/55=C/40=D;审计前业务预分类 6 类(SaaS/电商/本地/创作者…);收入影响=月流量×转化率提升×客单价;影响分级 High>$5,000/mo 或>20%;每子维度 0-10 分带**五档锚定文案**(9-10="crystal clear"…0-2=无清晰标题)。
**30/60/90 方案模板**(GEORank):输出要求=先判优先级/含负责人+交付物+验收指标/覆盖页面结构·答案式内容·FAQ·Schema·权威引用·AI 可见性·长尾·转化路径/标信息缺口;输入 13 字段(goal/brand/url/industry/audience/stage/timeline/resources/market/competitors/constraints/context/focus),5 项必填。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · monitor/performance-reporter/references/report-templates.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/monitor/performance-reporter/references/report-templates.md)（Apache-2.0）
- 一手资料：[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)、[排名系统指南](https://developers.google.com/search/docs/appearance/ranking-systems-guide)、[Core Web Vitals 与 Google 搜索](https://developers.google.com/search/docs/appearance/core-web-vitals)

## 情报摘要类报告：骨架、信号类型学与样本量阶梯（goose-skills 深读 2026-10-09b）

来源仓库 monitoring / research / outreach 的周期性 digest 技能（kol-content-monitor、newsletter-signal-scanner、review-intelligence-digest、sequence-performance、industry-scanner 等）共享一套骨架，可作为常规 SEO 周 / 月报之外「竞争与内容情报流」报告的补充模板。

**通用骨架**：统计概要（N 个信源 / N 条命中 / 本期最热主题）→ 按信源或对象分节，每条带来源 + 日期 + 定长摘录 → 跨对象对比表 → 建议动作分「本周借势 / 下周抢跑」两层、各带角度建议 → 附录。

**信号类型学**（kol-content-monitor）：Convergence=3 个以上独立信源同期谈同一主题（最强信号）；Spike=环比翻倍；Underdog=单一信源先行（标注「尚早，持续观察」，不写成趋势）；Controversy=评论 / 反应比异常高。主题按总互动排序并标方向（新出现 / 增长 / 持平）；跟势内容在峰值后 3 天内发布。

**关键词战役式过滤**（newsletter-signal-scanner）：按四组建档——竞品名、ICP 痛点语言、市场迁移词、自有品牌词；命中只保留关键词前后约 50 字符的上下文，不整段复制；自有品牌词出现单独成节；条目按高 / 中 / 低相关过滤，低相关默认丢弃。**不强行给每条情报配策略**——多数只是「值得知道」，硬凑动作是噪音；只对真实可行动的聚簇出策略。

**样本量置信阶梯**（sequence-performance）：<50=数据不足、50-100=方向性、100-250=可能胜出、250+=统计显著。A/B 结论（标题、摘要、模板改版）照此措辞，不提前宣布赢家。分层基准给区间不给单值（客群不同基准不同），并看「边际贡献」——该变体在剩余未响应样本中的增量，不把累计值当增量。报告要读原始样本（实际回复、实际查询、实际 URL），不只看聚合指标；「已送达 ≠ 已见效」与上文三状态一致。

**节奏表**：周一晨=内容与社区情报、周五午后=趋势与 KOL 峰值、每月 1 日=定价 / 评价等慢变高影响项、季度=全量基线重跑并更新 watchlist；跨源去重时保留最丰富版本并注「多源出现」。

**评价 / 口碑月报**（review-intelligence-digest）：证明点库（带数字优先）、痛点原话频次表、异议对照表（异议 / 频次 / 原话 / 应对）、竞品抱怨=替代内容素材、用户高频词汇表=文案与关键词素材；月更即可。
