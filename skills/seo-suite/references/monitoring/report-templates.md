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

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · monitor/performance-reporter/references/report-templates.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/monitor/performance-reporter/references/report-templates.md)（Apache-2.0）
- 一手资料：[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)、[排名系统指南](https://developers.google.com/search/docs/appearance/ranking-systems-guide)、[Core Web Vitals 与 Google 搜索](https://developers.google.com/search/docs/appearance/core-web-vitals)
