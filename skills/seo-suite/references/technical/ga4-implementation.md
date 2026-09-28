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

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/analytics-tracking/references/ga4-implementation.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/analytics-tracking/references/ga4-implementation.md)（MIT）
- 一手资料：[GA4 事件](https://support.google.com/analytics/answer/9322688)、[GA4 推荐事件](https://support.google.com/analytics/answer/9267735)、[GA4 Measurement Protocol](https://developers.google.com/analytics/devguides/collection/protocol/ga4)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)
