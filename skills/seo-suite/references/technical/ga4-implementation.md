# GA4 中与 SEO 相关的设置要点

用途：检查或设计 GA4，使它能回答「自然搜索带来了哪些访问、落在哪些页面、产生了什么结果」。需要你自己的 GA4 媒体资源访问权限；事件设计见 [event-library.md](event-library.md)。

## 必查设置

| 设置 | 为什么和 SEO 有关 | 检查什么 |
|---|---|---|
| 数据流与增强型衡量 | 页面浏览、滚动、外链点击、站内搜索、文件下载等自动事件 | 是否开启；站内搜索的查询参数是否与站点一致 |
| 关键事件 | 衡量自然流量的业务价值 | 只标少数代表业务结果的事件，价值和币种是否正确 |
| 自定义维度 | 按页面类型、内容分组、作者分析 | 事件参数要先注册为自定义维度才能在报告中使用 |
| 跨网域与引荐排除 | 支付页、第三方登录回跳会把自然流量错记为引荐 | 多域名是否配置跨网域衡量；不需要的引荐来源是否排除 |
| 内部流量过滤 | 员工访问会污染落地页数据 | 是否定义并启用内部流量过滤 |
| 数据保留期 | 同比分析需要较长的明细数据 | 探索报告的数据保留期是否已按需要调长 |
| 关联 Search Console | 在 GA4 中查看查询与自然搜索落地页 | 是否已关联，相关报告是否已发布到报告库 |

## 常用分析视角

- 落地页报告，按「会话默认渠道分组 = Organic Search」筛选：每个落地页的会话、互动率、关键事件。
- 按内容分组或自定义维度汇总：比较专题集群、页面类型的贡献。
- Search Console 报告（关联后）：查询、展示、点击与落地页的对应关系；这部分数据来自 Search Console，口径与 GA4 会话不同。

## 口径陷阱

- GA4 的会话数与 Search Console 的点击数不会相等：同意拒绝、广告拦截、跨设备和统计定义都会造成差异。
- 「(not set)」落地页常见于会话超时、仅有非页面事件的会话或实现问题，占比高时要排查。
- 默认渠道分组依赖来源 / 媒介规则；自定义 UTM 用错会把自然流量归到别处，站内链接不要加 UTM。
- 数据阈值和采样会让小流量页面的数据不完整，结论要注明。

## Measurement Protocol

服务端补发事件（例如线下成交回传）时使用。需要你自己的衡量 ID 和在 GA4 中创建的 API secret，示例中都是占位符：

```text
POST https://www.google-analytics.com/mp/collect?measurement_id=G-XXXXXXX&api_secret=YOUR_API_SECRET
```

请求体中的事件名和参数与前端保持同一套命名；不要发送个人信息。

## 验收

1. 用 DebugView 或 Tag Assistant 逐个触发事件，核对名称和参数。
2. 在实时报告中确认自然搜索会话能被正确归类。
3. 上线一段时间后，抽查落地页报告中「(not set)」和异常引荐的占比。

## 市场差异:测量栈与合规(拉平轮)

| 市场 | 分析栈现实 |
|---|---|
| 俄语区 | **GA 因 152-ФЗ 实际不可用→Yandex Metrica**(免费含 Вебвизор 会话回放,ПФ 优化闭环:点击图/滚动图/表单分析) |
| 德语区 | Matomo(德服务器)/Plausible 为默认;**cookie 横幅判例**:OLG Köln 2024-01(拒绝键须同等醒目)/VG Hannover 2025-03(首层"全部拒绝")——横幅设计是合规驱动 |
| 法语区 | CNIL 2022 判 GA 转移违法;大企业默认 **Piano Analytics**(法企,Europrivacy 认证)+"数据主权"是采购决策词 |
| 巴西 | LGPD:欧式"接受突出"横幅不构成有效同意→对称 opt-in;KPI 锚 GSC(免 consent) |
| 通用 | **GSC(免 consent)为基准线+GA4 建模值并列 consent rate** 的报表结构;小流量站勿依赖 Advanced Consent Mode 建模;服务器端 GTM 为 EU 标配路径 |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/analytics-tracking/references/ga4-implementation.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/analytics-tracking/references/ga4-implementation.md)（MIT）
- 一手资料：[GA4 事件](https://support.google.com/analytics/answer/9322688)、[GA4 推荐事件](https://support.google.com/analytics/answer/9267735)、[GA4 Measurement Protocol](https://developers.google.com/analytics/devguides/collection/protocol/ga4)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)

## GA4/GSC 连接器操作纪律(notfair 深读 2026-10-09b)

来源:nowork-studio/notfair-plugin 的 analytics/google-analytics、analytics/search-console 与 analytics/shared/operating-contract(MCP 连接器工作流)。

### 资源定位(先于一切查询)

- **GA4 资源只能用连接器返回的 `properties/123456789` 资源名**;绝不用 `G-` 衡量 ID 或 Google 账号 ID 替代。先列属性确认访问,再选资源。
- **GSC 属性用连接器返回的确切已验证形式**:`sc-domain:example.com` 与 `https://example.com/` 是两个不同属性;优先域名属性(覆盖全部子域和协议)。
- 平台未连或未授权→指引用户重连并**停止,不得声称拿到的是实时数据**。

### 取证纪律(GA4)

- 定义业务问题、主指标、转化/关键事件定义、**资源时区**、日期窗、对比窗,再拉数据;每个重要结论旁必须写明这些口径。
- **一次宽批量读优于多次窄读**;尊重连接器当前暴露的维度/指标/fan-out/配额限制,不照搬别平台的限制。
- 不熟的维度/指标组合先查元数据再猜;**检查响应元数据中的采样/阈值/配额告警**;出现 `(other)` 折叠行=明细行加总不等于总数,必须声明。
- 当日/近期数据视为临时值并注明时区;**GA4 归因与广告平台归因分开报**,解释差异而不是混合不相容的数字;相关≠因果,无证据不得宣称渠道/页面变化导致了结果。
- 结论结构:什么变了→在哪变→有证据的可能驱动因素→置信度→下一个测量或业务动作;附上报告定义以便他人复现。

### 取证纪律(GSC)

- **对账资源级 clicks/impressions 时去掉 `query` 维度拉总数**——匿名化低量词使 query 行天然不完整。
- 近期 `all` 数据未定稿,标临时;**不要对已聚合的 CTR/position 行做朴素平均**;结果受行数上限约束时声明"top 行而非完整导出"。
- URL Inspection 配额远紧于 Search Analytics,**按需用**;检查报告只反映索引状态,**不会请求索引**;排名波动是证据,不是某次算法更新的证明。
- 结论以"最大实质性增/减→受影响词/页→有证据的假设→置信度→下一步 SEO 动作"开头。

### 测量配置变更安全(与上面必查设置互补)

- 改配置前展示:确切资源、当前状态、目标状态、对下游报表的影响、回滚方案,再请求批准。
- **可逆性矩阵**:关键事件创建/删除互为可逆;**自定义维度归档在 GA4 不可逆且参数名不可复用**——必须获得点名"资源+维度名"的明确批准。
- 写入后用返回的前后证据或新读确认;部分失败如实上报,**不盲重试**;连接器未明确支持并确认,不得声称"报告已保存/仪表板已发布"。
