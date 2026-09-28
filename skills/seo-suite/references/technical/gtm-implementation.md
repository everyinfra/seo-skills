# 用 Google 跟踪代码管理器部署 SEO 相关埋点

用途：用 GTM 落地 [event-library.md](event-library.md) 里的事件时的结构、命名和发布流程，以及不伤害性能和可抓取内容的注意事项。需要你自己的 GTM 容器权限。

## 结构

- **数据层**：页面把业务信息推入 `dataLayer`，GTM 只负责读取和发送。页面信息（页面类型、内容分组、模板、作者）在页面加载时推送；交互在发生时推送。
- **触发器**：优先用数据层自定义事件触发，少用依赖 CSS 类名或元素文字的点击触发，后者在改版时容易失效。
- **变量**：数据层变量读取参数；常量变量保存衡量 ID 等配置。
- **代码**：一个 Google 代码（GA4 配置）加若干事件代码。

自写的最小示例：

```js
// 页面加载时（由服务端模板输出）
window.dataLayer = window.dataLayer || [];
window.dataLayer.push({ page_type: 'article', content_group: 'technical-seo', author_id: 'a-102' });

// 用户点击主要 CTA 时
window.dataLayer.push({ event: 'cta_click', cta_id: 'hero-start', cta_position: 'hero' });
```

## 命名约定

- 代码：`平台 - 类型 - 事件`，如 `GA4 - Event - cta_click`。
- 触发器：`类型 - 条件`，如 `CE - cta_click`（自定义事件）。
- 变量：`类型 - 名称`，如 `DLV - cta_id`（数据层变量）。
- 同一约定写进团队文档，新代码按约定命名。

## 发布流程

1. 在单独的工作区修改。
2. 用预览模式（Tag Assistant）逐个触发事件，核对代码是否触发、参数是否正确，并在 GA4 DebugView 中确认收到。
3. 发布时写清版本说明：改了什么、为什么、谁验证。
4. 出问题时回滚到上一个版本，而不是在线上临时改代码。

## 同意管理

- 使用同意模式时，在任何代码触发前设置默认同意状态，用户选择后再更新。
- 同意相关的配置以所用同意管理平台和 Google 文档为准，并符合当地法规。

## 与 SEO 相关的注意事项

- 容器里代码越多，对 INP 和 LCP 的影响越大；定期清理不用的代码和第三方脚本，非必要脚本延后触发。
- 标题、canonical、robots、正文等 SEO 关键内容由服务端直接输出，不要依赖 GTM 注入。
- 结构化数据技术上可以用 JavaScript（包括 GTM）注入，Google 有专门文档；但更稳妥的是服务端输出。如果用 GTM 注入，必须用富媒体搜索结果测试检查渲染后的结果。
- 不要在 GTM 中改写链接或插入隐藏链接。

## 交付

- 代码、触发器、变量清单与命名。
- 数据层字段约定（给开发）。
- 预览验证记录和发布版本说明。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/analytics-tracking/references/gtm-implementation.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/analytics-tracking/references/gtm-implementation.md)（MIT）
- 一手资料：[Google 跟踪代码管理器帮助](https://support.google.com/tagmanager)、[用 JavaScript 生成结构化数据](https://developers.google.com/search/docs/appearance/structured-data/generate-structured-data-with-javascript)、[富媒体搜索结果测试](https://search.google.com/test/rich-results)、[web.dev：INP](https://web.dev/articles/inp)
