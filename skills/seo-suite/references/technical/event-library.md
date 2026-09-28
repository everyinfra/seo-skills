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

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/analytics-tracking/references/event-library.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/analytics-tracking/references/event-library.md)（MIT）
- 一手资料：[GA4 事件](https://support.google.com/analytics/answer/9322688)、[GA4 推荐事件](https://support.google.com/analytics/answer/9267735)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)
