# SEO 归因事件清单

用途：为「自然搜索带来的访问最终产生了什么价值」设计埋点。本文件只覆盖 SEO 归因需要的事件，不是通用埋点手册。GA4 配置见 [ga4-implementation.md](ga4-implementation.md)，用 GTM 部署见 [gtm-implementation.md](gtm-implementation.md)。

## 设计原则

1. **先用官方推荐事件**：GA4 已有推荐事件（如 `sign_up`、`generate_lead`、`purchase`、`search`、`share`）时直接用，报告和集成支持更好；没有合适的再自定义。
2. **命名统一**：小写加下划线，「动作_对象」结构（如 `cta_click`、`demo_request`）；同一动作全站只用一个名字。GA4 对事件名、参数名、参数值的长度和数量有上限，以官方文档为准。
3. **参数说明页面，而不是个人**：页面类型、内容分组、模板、作者、发布日期等参数用于把转化归到内容上；不采集姓名、邮箱、电话等个人信息。
4. **同意优先**：按所在地区的法规和同意管理方案决定是否、何时发送事件。

## 事件分层

| 层级 | 目的 | 示例事件 | 关键参数 |
|---|---|---|---|
| 访问与内容 | 知道用户看了哪类内容 | `page_view`（自动）、滚动、站内搜索 `search` / `view_search_results` | `page_type`、`content_group`、`template` |
| 互动 | 判断内容是否被真正使用 | `cta_click`、`file_download`、外链点击、视频播放、代码复制 | `cta_id`、`cta_position`、`link_url` |
| 线索与注册 | 连接内容与业务结果 | `generate_lead`、`sign_up`、`demo_request` | `form_id`、`lead_type` |
| 交易 | 电商或付费转化 | `view_item`、`add_to_cart`、`begin_checkout`、`purchase` | `value`、`currency`、`items` |
| 体验问题 | 发现 SEO 流量落到坏页面 | 404 页面浏览（`page_type=404`）、表单报错 | `page_path`、`referrer` |

「关键事件」（GA4 中原来叫「转化」）只选真正代表业务价值的少数几个。

深读轮补充：内容站建议组合 `generate_lead`（或 `sign_up`）+ `cta_click` + `file_download`；电商建议 `purchase`（关键）+ `add_to_cart` / `begin_checkout`（过程）；B2B 长漏斗加 `working_lead`。同一动作不重复进关键事件，过程事件只作漏斗读数。

## 连接到 SEO 分析

- 以「落地页 + 默认渠道分组 = Organic Search」为主视角，看每个落地页带来的互动和关键事件。
- 用 `content_group` 或自定义维度把页面归到专题集群、页面类型、作者，按集群评估内容价值。
- 与 Search Console 数据按落地页对齐：查询和展示来自 Search Console，行为和转化来自分析工具，两者口径不同，不要直接相加。
- 多次访问后才转化的情况，看分析工具的归因报告和转化路径，不要只看最后一次点击。

## 交付

- 事件清单：事件名、触发条件、参数、是否关键事件、负责实现的一方。
- 数据层字段约定（给开发）。
- 验收清单：在调试工具里逐个触发并核对参数。

## 常见误区

- 每个按钮一个事件名，导致报告无法汇总。
- 把邮箱、用户名写进事件参数或页面 URL。
- 关键事件选得过多，稀释真正的业务目标。
- 只埋点不验证，上线后才发现参数为空。
- 同一事件客户端与服务端双发且不去重，转化被计两次。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/analytics-tracking/references/event-library.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/analytics-tracking/references/event-library.md)（MIT）
- 一手资料：[GA4 事件](https://support.google.com/analytics/answer/9322688)、[GA4 推荐事件](https://support.google.com/analytics/answer/9267735)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)

## SEO 归因事件字典（深读 2026-10-09）

把上文分层展开为逐事件字典。参数以 [GA4 事件参考（developers）](https://developers.google.com/analytics/devguides/collection/ga4/reference/events)与[推荐事件（support）](https://support.google.com/analytics/answer/9267735)当前文档为准；GA4 对事件与参数的数量、长度有上限。

### 访问与内容层

| 事件 | 触发时机 | 关键参数 | 报告查询 |
|---|---|---|---|
| `page_view` | 页面加载 / 历史记录变更（增强衡量自动） | `page_location`、`page_referrer`；自定义 `page_type`、`content_group` | 着陆页视角：维度 `Landing page + query string`，过滤 `Session default channel group = Organic Search`（[官方着陆页报告](https://support.google.com/analytics/answer/12931766)、[OptimizeSmart 教程](https://optimizesmart.com/blog/tracking-organic-traffic-in-ga4-complete-guide)） |
| `search` | 站内搜索提交 | `search_term`（必填） | Events 报告看高频词与空结果词，作内容缺口输入 |
| `view_search_results` | 站内结果页展示 | `search_term` | 与 `search` 对比看「提交→到达结果页」流失 |
| `scroll` | 滚动至 90%（增强衡量） | — | 配 `page_type` 看内容页真实消费率 |
| `file_download` | 点击文件下载（增强衡量） | `file_extension`、`file_name` | 内容资产消费证据 |

### 互动层

| 事件 | 触发时机 | 关键参数 | 说明 |
|---|---|---|---|
| `cta_click`（自定义） | 主 CTA 点击 | `cta_id`、`cta_position`、`destination` | 按落地页聚合即「内容→意向」漏斗第一级 |
| `click`（外链，增强衡量） | 点击出站链接 | `link_url`、`link_domain`、`outbound` | 增强衡量的 Outbound clicks；出站方向是引用关系的反向证据 |
| `video_start` / `video_progress` / `video_complete` | YouTube 等嵌入播放（增强衡量） | `video_url`、`video_percent` | 视频内容完成率；视频检索面见 [video-geo-guide.md](../content/video-geo-guide.md) |
| `share`（推荐） | 分享动作 | `method`、`content_type`、`item_id` | 推荐事件，报告内置支持 |
| `copy_snippet`（自定义，如代码复制） | 复制代码 / 引用块 | `snippet_id`、`page_type` | 开发者内容常用；引用扩散与 AI 引用都相关 |
| `form_start` / `form_submit` | 表单首字段聚焦 / 提交（增强衡量「表单互动」） | `form_id`、`form_name`、`form_destination`、`form_origin` | `form_submit` 失败重提不重复算完成；比自定义表单事件省维护 |

### 线索与交易层

| 事件 | 触发时机 | 关键参数 | GA4 对应 |
|---|---|---|---|
| `sign_up` | 注册完成 | `method`（如 Google / email） | 推荐事件 |
| `generate_lead` | 表单提交 / 订阅 / 演示请求 | `currency`、`value` + 自定义 `form_id`、`lead_type` | 推荐事件；SEO 线索主指标 |
| `login` | 登录成功 | `method` | 推荐事件（回访信号） |
| `view_item` | 商品 / 方案详情页 | `currency`、`value`、`items` | 电商推荐 |
| `add_to_cart` / `remove_from_cart` | 加购 / 移除 | `currency`、`value`、`items` | 电商推荐 |
| `begin_checkout` | 发起结账 | `currency`、`value`、`items`、`coupon` | 电商推荐 |
| `purchase` | 支付完成（服务端回传最可靠） | `transaction_id`（去重键）、`value`、`currency`、`tax`、`shipping`、`items` | 电商推荐；`transaction_id` 幂等防重复计数 |
| `refund` | 退款发生 | `transaction_id`、`value`、`currency` | 电商推荐，服务端回传 |
| `working_lead` / `close_unconvert_lead` | 长周期线索的中间态（推进 / 判负） | `lead_id`、`currency`、`value` | 较新的线索型推荐事件，B2B 长漏斗用得上（[Stape 解读](https://stape.io/news/ga4-new-recommended-events-lead-generation)）；是否采用以当前官方推荐列表为准 |

### 体验问题层

| 事件 | 触发时机 | 关键参数 |
|---|---|---|
| `page_not_found`（自定义）或 `page_view` + `page_type=404` | 404 页渲染 | `page_path`、`referrer`；接 Search Console 覆盖率报告定位失效内链 |
| `search_zero_results`（自定义） | 站内搜索无结果页 | `search_term`；高频词即内容缺口清单 |
| `form_error`（自定义） | 表单校验失败 | `form_id`、`error_type`；落在高流量落地页上的报错优先修 |

### 报告查询示例

1. **内容集群价值**：Exploration（自由形式）→ 维度 `content_group` × `Landing page`，指标 Sessions（过滤 Organic Search）→ Key events → `event_count`（`generate_lead`）。
2. **单页漏斗**：Path Exploration 从某落地页 → `cta_click` → `generate_lead`。
3. **BigQuery 事件导出**：参数是 record，必须 UNNEST 展开，如 `SELECT (SELECT value.string_value FROM UNNEST(event_params) WHERE key='page_type') AS page_type, COUNT(*) FROM events_* WHERE event_name='page_view' GROUP BY 1`。
4. 与 Search Console 按落地页对齐时口径不同不可相加（同上文原则）。
5. **参数注册**：自定义参数要在 GA4 里注册为自定义维度 / 指标后才能在标准报告与 Exploration 中选用（数量有上限，以当前文档为准）；未注册的参数只在调试与 BigQuery 里可见。上线前把「参数名 → 是否注册」写进交付清单。

### 服务器端 vs 客户端

| 维度 | 客户端（gtag / GTM Web） | 服务端（sGTM / Measurement Protocol） |
|---|---|---|
| 触发位置 | 浏览器 | 自有 tagging server 或后端直发（[Measurement Protocol 事件参考](https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference/events)） |
| 优点 | 真实用户行为信号全、自动采 client_id | 一方端点；PII 可在出站前脱敏；广告拦截影响小；`purchase` / `refund` 等后端事实可补发 |
| 风险 | 拦截 / 隐私脚本丢失事件 | 双发重复计数（同一事件只留一条链路）；时间戳差异影响会话归属 |
| 归属 | client_id 自动 | 需回传或生成一致的 client_id，否则会话割裂、归因断裂 |

### 同意模式下的降级方案

同意模式 v2 四状态：`ad_storage`、`analytics_storage`、`ad_user_data`、`ad_personalization`（[服务端同意模式文档](https://developers.google.com/tag-platform/tag-manager/server-side/consent-mode)）。

- **Advanced 模式 + `analytics_storage=denied`**：仍发无 cookie ping（IP 截断），行为与转化靠[行为建模](https://support.google.com/analytics/answer/11161109)补齐；建模有资格门槛（连续天数与每日 denied 事件量，以当前文档为准）。报告里 modeled 数据要标注口径。
- **Basic 模式 + denied**：不发分析事件——该人群在报告里是盲区，估算时注明「已知低估」。
- **降级排序**：完整事件 → cookieless ping + 建模 → 不发送；报告口径对应三档：全量 / modeled / 已知低估。
- **服务端 + 同意**：sGTM 可在出站前 redact 参数、强制执行 consent state；EEA 流量自 2024-03 起必须实现 v2 信号，否则广告功能受限（[iubenda 解读](https://www.iubenda.com/en/blog/what-is-google-consent-mode)、[IIH Nordic 技术指南](https://iihnordic.com/news/consent-mode-v2-a-comprehensive-technical-guide)）。
- **设计纪律**：事件名与参数不因同意状态改变，只改「发不发」；否则同意与拒绝人群的报告无法对齐比较。

### 来源补遗

[GA4 事件参考（developers）](https://developers.google.com/analytics/devguides/collection/ga4/reference/events)、[推荐事件（support）](https://support.google.com/analytics/answer/9267735)、[Measurement Protocol 事件](https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference/events)、[GA4 着陆页报告](https://support.google.com/analytics/answer/12931766)、[服务端同意模式](https://developers.google.com/tag-platform/tag-manager/server-side/consent-mode)、[行为建模](https://support.google.com/analytics/answer/11161109)、[OptimizeSmart 自然流量报告教程](https://optimizesmart.com/blog/tracking-organic-traffic-in-ga4-complete-guide)
