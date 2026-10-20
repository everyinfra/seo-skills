# SEO 归因事件清单

用途：为「自然搜索带来的访问最终产生了什么价值」设计埋点。本文件只覆盖 SEO 归因需要的事件，不是通用埋点手册。GA4 配置见 [ga4-implementation.md](ga4-implementation.md)，用 GTM 部署见 [gtm-implementation.md](gtm-implementation.md)。

## 设计原则

1. **先用官方推荐事件**：GA4 已有推荐事件（如 `sign_up`、`generate_lead`、`purchase`、`search`、`share`）时直接用，报告和集成支持更好；没有合适的再自定义。
2. **命名统一**：小写加下划线，「动作_对象」结构（如 `cta_click`、`demo_request`）；同一动作全站只用一个名字（本套件口径）。GA4 的硬规则（核对 2026-10-21）：事件名区分大小写，必须以字母开头，只用字母、数字、下划线（[命名规则](https://support.google.com/analytics/answer/13316687)）；事件名最多 40 个字符，每个事件最多 25 个参数，参数名最多 40 个字符，参数值最多 100 个字符（`page_title` 300、`page_referrer` 420、`page_location` 1,000）；Web 数据流不限事件名个数（[采集上限](https://support.google.com/analytics/answer/9267744)）。`click`、`scroll`、`file_download`、`form_start`、`form_submit`、`view_search_results`、`video_*`、`error` 等是保留名，不能当自定义事件名。
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

「关键事件」（GA4 中原来叫「转化」，现在「转化」只指用于衡量广告效果的重要动作；[官方说明](https://support.google.com/analytics/answer/13965727)）只选真正代表业务价值的少数几个。每个媒体资源最多 30 个关键事件（[配置上限](https://support.google.com/analytics/answer/12229528)）。

组合建议（本套件口径）：内容站用 `generate_lead`（或 `sign_up`）+ `cta_click` + `file_download`；电商用 `purchase`（关键）+ `add_to_cart` / `begin_checkout`（过程）；B2B 长漏斗加线索阶段事件（见下表）。同一动作不重复进关键事件，过程事件只作漏斗读数。

## 连接到 SEO 分析

- 以「落地页 + 会话默认渠道分组 = Organic Search」为主视角，看每个落地页带来的互动和关键事件。渠道归类有两条官方规则（[默认渠道分组](https://support.google.com/analytics/answer/9756891)，核对 2026-10-21）：Organic Search 含 Google 的 AI Overviews 和 AI Mode 带来的点击；来自 ChatGPT、Gemini、Deepseek、Copilot、Grok 等的访问归入单独的 AI Assistant 渠道（medium 为 `ai-assistant`）。看「AI 搜索带来的访问」要把 AI Assistant 渠道和 Organic Search 分开读。
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
| `page_view` | 每次页面加载或浏览器历史状态变化（自动，不能关闭） | `page_location`、`page_referrer`；自定义 `page_type`、`content_group` | 着陆页视角：Engagement → Landing page 报告加次要维度「Session default channel group」，筛 Organic Search；或 Traffic acquisition 报告，主维度选渠道，次要维度选「Landing page + query string」（[官方着陆页报告](https://support.google.com/analytics/answer/12931766)） |
| `view_search_results` | 站内搜索结果页展示（增强衡量「站内搜索」；URL 含 `q`、`s`、`search`、`query`、`keyword` 之一，或你配置的其他参数） | `search_term` | 站点搜索参数不在这 5 个里时，在数据流的增强衡量设置里补上，否则事件不触发（[增强衡量事件](https://support.google.com/analytics/answer/9216061)） |
| `search`（推荐事件，需自己发送） | 用户执行站内搜索 | `search_term`（必填） | Events 报告看高频词与空结果词，作内容缺口输入；与 `view_search_results` 同时存在时只选一个做主指标，避免重复计数 |
| `scroll` | 用户第一次滚到页面底部（90% 垂直深度可见） | — | 配 `page_type` 看内容页真实消费率 |
| `file_download` | 点击指向常见文件扩展名（pdf、docx、xlsx、zip、mp3 等）的链接 | `file_extension`、`file_name`、`link_url`、`link_text` | 内容资产消费证据 |

### 互动层

| 事件 | 触发时机 | 关键参数 | 说明 |
|---|---|---|---|
| `cta_click`（自定义） | 主 CTA 点击 | `cta_id`、`cta_position`、`destination` | 按落地页聚合即「内容→意向」漏斗第一级 |
| `click`（外链，增强衡量） | 点击通往其他域名的链接；已配置跨网域衡量的域名不触发 | `link_url`、`link_domain`、`link_id`、`link_classes`、`outbound` | 增强衡量的 Outbound clicks |
| `video_start` / `video_progress` / `video_complete` | 启用 JS API 的 YouTube 嵌入视频：开始、播放超过 10%/25%/50%/75%、结束 | `video_url`、`video_title`、`video_percent`、`video_current_time`、`video_duration`、`video_provider` | 视频内容完成率；视频检索面见 [video-geo-guide.md](../content/video-geo-guide.md) |
| `share`（推荐） | 分享动作 | `method`、`content_type`、`item_id` | 推荐事件，报告内置支持 |
| `copy_snippet`（自定义，如代码复制） | 复制代码 / 引用块 | `snippet_id`、`page_type` | 开发者内容常用；引用扩散与 AI 引用都相关 |
| `form_start` / `form_submit` | 一次会话里首次与表单互动 / 提交表单（增强衡量「表单互动」） | `form_id`、`form_name`、`form_destination`；`form_submit` 另有 `form_submit_text` | 这些参数要注册自定义维度才能在报告里用；增强衡量按表单提交动作触发，Ajax 表单要对照 DebugView 确认（[增强衡量事件](https://support.google.com/analytics/answer/9216061)） |

### 线索与交易层

| 事件 | 触发时机 | 关键参数 | GA4 对应 |
|---|---|---|---|
| `sign_up` | 注册完成 | `method`（如 Google / email） | 推荐事件 |
| `generate_lead` | 表单提交 / 订阅 / 演示请求 | `currency`、`value`、`lead_source` + 自定义 `form_id`、`lead_type` | 推荐事件；设了 `value` 就必须设 `currency`；标为关键事件时官方建议设 `value`（[事件参考](https://developers.google.com/analytics/devguides/collection/ga4/reference/events)） |
| `login` | 登录成功 | `method` | 推荐事件（回访信号） |
| `view_item` | 商品 / 方案详情页 | `currency`、`value`、`items` | 电商推荐 |
| `add_to_cart` / `remove_from_cart` | 加购 / 移除 | `currency`、`value`、`items` | 电商推荐 |
| `begin_checkout` | 发起结账 | `currency`、`value`、`items`、`coupon` | 电商推荐 |
| `purchase` | 支付完成（服务端回传最可靠） | `transaction_id`（必填）、`value`、`currency`、`tax`、`shipping`、`items`（必填） | 电商推荐；官方：`transaction_id` 用来避免重复的购买事件；`value` 是各商品 price × quantity 之和，不含运费和税 |
| `refund` | 退款发生 | `transaction_id`、`value`、`currency` | 电商推荐，服务端回传 |
| 线索阶段事件：`qualify_lead`、`disqualify_lead`、`working_lead`、`close_convert_lead`、`close_unconvert_lead` | 线索被判合格 / 不合格 / 已有销售联系 / 成交 / 丢单 | 都带 `currency`、`value`；另 `working_lead` 用 `lead_status`，`close_unconvert_lead` 用 `unconvert_lead_reason` | 官方推荐事件（“For lead generation”组），填充 Lead acquisition 报告；B2B 长漏斗用，线下成交靠 Measurement Protocol 回传（[推荐事件](https://support.google.com/analytics/answer/9267735)、[事件参考](https://developers.google.com/analytics/devguides/collection/ga4/reference/events)） |

### 体验问题层

| 事件 | 触发时机 | 关键参数 |
|---|---|---|
| `page_not_found`（自定义）或 `page_view` + `page_type=404` | 404 页渲染 | `page_path`、`referrer`；接 Search Console 覆盖率报告定位失效内链 |
| `search_zero_results`（自定义） | 站内搜索无结果页 | `search_term`；高频词即内容缺口清单 |
| `form_error`（自定义） | 表单校验失败 | `form_id`、`error_type`；落在高流量落地页上的报错优先修 |

### 报告查询示例

1. **内容集群价值**：Exploration（自由形式）→ 维度 `content_group` × `Landing page`，指标 Sessions（过滤 Organic Search）→ Key events → `event_count`（`generate_lead`）。
2. **单页漏斗**：Path Exploration 从某落地页 → `cta_click` → `generate_lead`。
3. **BigQuery 事件导出**：参数是 record，必须 UNNEST 展开，如 `SELECT (SELECT value.string_value FROM UNNEST(event_params) WHERE key='page_type') AS page_type, COUNT(*) FROM \`项目.数据集.events_*\` WHERE _TABLE_SUFFIX BETWEEN '20261001' AND '20261031' AND event_name='page_view' GROUP BY 1`；`event_params` 是可重复的 RECORD，值按类型分列在 `value.string_value`、`int_value`、`double_value`（[导出结构](https://support.google.com/analytics/answer/7029846)）。
4. 与 Search Console 按落地页对齐时口径不同不可相加（同上文原则）。
5. **参数注册**：自定义参数要先注册为自定义维度或指标，才能在标准报告与 Exploration 中选用。
   - 上限：每个媒体资源最多 50 个事件级自定义维度、25 个用户级自定义维度（[配置上限](https://support.google.com/analytics/answer/12229528)）。
   - 刚注册的参数，前 24 小时可能显示 `(not set)`（[官方说明](https://support.google.com/analytics/answer/13504892)）。
   - 归档自定义维度不能撤销，但名称可以再用（[归档说明](https://support.google.com/analytics/answer/12436143)）。
   - 未注册的参数只在 DebugView 与 BigQuery 里可见。
   - 上线前把「参数名 → 是否注册」写进交付清单。

### 服务器端 vs 客户端

| 维度 | 客户端（gtag / GTM Web） | 服务端（sGTM / Measurement Protocol） |
|---|---|---|
| 触发位置 | 浏览器 | 自有 tagging server 或后端直发（[Measurement Protocol 事件参考](https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference/events)） |
| 优点 | 真实用户行为信号全、自动采 client_id | 一方端点；PII 可在出站前脱敏；`purchase` / `refund` 等后端事实可补发（本套件口径；广告拦截是否受影响取决于部署域名，以实测为准） |
| 风险 | 拦截 / 隐私脚本丢失事件 | 双发重复计数（同一事件只留一条链路）；时间戳差异影响会话归属 |
| 归属 | client_id 自动 | Measurement Protocol 请求必须带 `client_id`，并回传前端同一个值，否则会话割裂、归因断裂；新的 `session_id` 会开启新会话（[发送事件](https://developers.google.com/analytics/devguides/collection/protocol/ga4/sending-events)） |
| 校验 | DebugView | Measurement Protocol 对格式错误的事件也不返回 HTTP 错误码，上线前必须用校验端点 `/debug/mp/collect` 测；校验端点不检查 `api_secret` 和 `measurement_id`（[校验事件](https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events)） |

### 同意模式下的降级方案

同意模式有 4 个同意类型：`ad_storage`、`analytics_storage`，以及 v2 新增的 `ad_user_data`、`ad_personalization`（[同意模式概览](https://developers.google.com/tag-platform/security/concepts/consent-mode)、[EEA 更新](https://support.google.com/google-ads/answer/13695607)，核对 2026-10-21）。

- **Advanced 模式 + `analytics_storage=denied`**：标签照常加载。拒绝期间，Google 标签发送不带 cookie 的测量 ping，用于基础测量和建模。行为与转化靠[行为建模](https://support.google.com/analytics/answer/11161109)补齐。建模资格（官方，核对 2026-10-21）有两条：
  1. 媒体资源每天至少有 1,000 个 `analytics_storage='denied'` 的事件，持续至少 7 天。
  2. 过去 28 天里，至少 7 天有 1,000 个每日用户发送 `analytics_storage='granted'` 的事件。
  满足条件也不保证启用。报告里的 modeled 数据要标注口径。
- **Basic 模式 + denied**：用户未同意时 Google 标签不加载，不向 Google 发送任何数据，连同意状态也不发——该人群在报告里是盲区，估算时注明「已知低估」（[同意模式概览](https://developers.google.com/tag-platform/security/concepts/consent-mode)）。
- **降级排序**（本套件口径）：完整事件 → cookieless ping + 建模 → 不发送；报告口径对应三档：全量 / modeled / 已知低估。
- **服务端 + 同意**：sGTM 可在出站前 redact 参数、强制执行 consent state（[服务端同意模式](https://developers.google.com/tag-platform/tag-manager/server-side/consent-mode)）。官方页面写明：服务 EEA 用户的 Google 标签必须收集同意并把同意信号传给 Google，否则不能继续用于广告个性化和再营销测量（[EEA 更新](https://support.google.com/google-ads/answer/13695607)）。强制执行从 2024-03 开始的说法，目前只在第三方来源找到（[Cookiebot，2024-01-24](https://www.cookiebot.com/en/googles-consent-mode-deadline-ads-privacy-compliance/)），官方页未写日期。
- **设计纪律**：事件名与参数不因同意状态改变，只改「发不发」；否则同意与拒绝人群的报告无法对齐比较。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 事件名与参数合规 | 把事件清单逐个对照命名规则：字母开头，只含字母、数字、下划线，名称 ≤40 字符，每事件参数 ≤25 个，参数值 ≤100 字符；不用保留名 | 通过：全部符合。失败：有超长名、保留名（如自定义的 `form_submit`、`click`、`error`）或超 25 个参数 |
| 事件真的发出且参数齐全 | 数据流开启调试：页面加 `debug_mode: true` 或用 Tag Assistant，打开 GA4 Admin → DebugView，逐个触发 | 通过：每个事件出现，参数名与值和清单一致。失败：事件缺失，或参数值为空 |
| 服务端事件格式 | `curl -s -X POST "https://www.google-analytics.com/debug/mp/collect?measurement_id=G-XXXX&api_secret=SECRET" -H "Content-Type: application/json" -d '{"client_id":"test.1","events":[{"name":"generate_lead","params":{"currency":"USD","value":10}}]}'` | 通过：返回 `"validationMessages": []`。失败：数组里有 `fieldPath` 和错误码。注意该端点不校验 `api_secret`，真发一条测试事件到 DebugView 再确认密钥 |
| 自定义参数已注册 | Admin → Custom definitions；对照清单里「是否注册」列 | 通过：要在报告里用的参数都已注册，注册后等 24 小时再看数据。失败：参数只在 DebugView 出现而报告里是 `(not set)` |
| 关键事件数量与币种 | Admin → Key events | 通过：数量远低于 30 的上限，带金额的事件有 `currency`。失败：同一动作重复标关键事件，或 `value` 有而 `currency` 缺 |
| 购买去重 | 在测试环境对同一 `transaction_id` 触发两次 `purchase`（客户端和服务端各一次），查 Monetization → Ecommerce purchases | 通过：只计一笔。失败：计两笔，说明客户端和服务端双发且没有统一 `transaction_id` |
| 自然流量归类 | Reports → Acquisition → Traffic acquisition，主维度 Session default channel group；用一个已知的 Google 自然搜索点击和一个 ChatGPT 点击各测一次；要自定义 AI 渠道正则时，`python3 scripts/ai_referral_log.py --attribution` 会输出 GA4 自定义渠道正则作对照 | 通过：前者落 Organic Search，后者落 AI Assistant。失败：落 Unassigned 或 Referral |
| 同意状态对齐 | 拒绝全部后在 DebugView 看事件 | 通过：与本节「同意模式下的降级方案」描述的模式一致（Basic 无事件；Advanced 只有无 cookie ping）。失败：拒绝后仍有带 cookie 的事件 |

### 来源补遗

[GA4 事件参考（developers）](https://developers.google.com/analytics/devguides/collection/ga4/reference/events)、[推荐事件（support）](https://support.google.com/analytics/answer/9267735)、[增强衡量事件](https://support.google.com/analytics/answer/9216061)、[事件命名规则](https://support.google.com/analytics/answer/13316687)、[事件采集上限](https://support.google.com/analytics/answer/9267744)、[配置上限](https://support.google.com/analytics/answer/12229528)、[Measurement Protocol 事件](https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference/events)、[GA4 着陆页报告](https://support.google.com/analytics/answer/12931766)、[默认渠道分组](https://support.google.com/analytics/answer/9756891)、[同意模式概览](https://developers.google.com/tag-platform/security/concepts/consent-mode)、[服务端同意模式](https://developers.google.com/tag-platform/tag-manager/server-side/consent-mode)、[行为建模](https://support.google.com/analytics/answer/11161109)
