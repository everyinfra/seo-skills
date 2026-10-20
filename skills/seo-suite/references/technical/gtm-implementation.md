# 用 Google 跟踪代码管理器部署 SEO 相关埋点

用途：用 GTM 落地 [event-library.md](event-library.md) 里的事件时的结构、命名和发布流程，以及不伤害性能和可抓取内容的注意事项。需要你自己的 GTM 容器权限。

## 结构

- **数据层**：页面把业务信息推入 `dataLayer`，GTM 只负责读取和发送。页面信息（页面类型、内容分组、模板、作者）在每次页面加载时推送，官方建议放在 GTM 容器代码上方，这样标签一开始就能读到；交互在发生时推送（[数据层](https://developers.google.com/tag-platform/tag-manager/datalayer)，核对 2026-10-21）。不要覆盖 `window.dataLayer` 变量，用 `window.dataLayer = window.dataLayer || []` 初始化；事件名和变量名区分大小写。
- **触发器**：优先用数据层自定义事件触发，少用依赖 CSS 类名或元素文字的点击触发，后者在改版时容易失效（本套件口径）。官方对表单和链接触发器的建议：先在预览模式里测，限定到测试过的页面，因为别的脚本返回 `false` 会让触发器失效（[触发器最佳实践](https://support.google.com/tagmanager/answer/7679102)）。
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
- 命名格式是本套件口径，GTM 没有官方命名规范；同一约定写进团队文档，新代码按约定命名。

## 发布流程

1. 在单独的工作区修改。
2. 用预览模式（点 Workspace 右上角 Preview 打开 Tag Assistant）逐个触发事件，核对代码是否触发、参数是否正确，并在 GA4 DebugView 中确认收到（[预览与调试](https://support.google.com/tagmanager/answer/6107056)）。
3. 发布时填版本名称和版本说明：改了什么、为什么、谁验证。每次发布都会自动记录一个版本（[发布与版本](https://support.google.com/tagmanager/answer/6107163)）。
4. 出问题时把工作区还原到上一个版本再发布，而不是在线上临时改代码。

## 同意管理

- 使用同意模式时，在任何代码触发前设置默认同意状态，用户选择后再更新。GTM 的做法：同意管理平台的标签（以及设置或更新同意状态的标签）用「Consent Initialization」触发器，它先于其他所有触发器，包括 Initialization；其他标签不要用它，改用 Initialization 触发器（[同意模式支持](https://support.google.com/tagmanager/answer/10718549)，核对 2026-10-21）。
- 同意相关的配置以所用同意管理平台和 Google 文档为准，并符合当地法规。

## 与 SEO 相关的注意事项

- web.dev 的说法（[标签最佳实践](https://web.dev/articles/tag-best-practices)，核对 2026-10-21）：标签管理器通过占用带宽和主线程间接影响 Core Web Vitals，LCP 受带宽争用影响，INP 受主线程争用影响，且观察到标签管理器体积与较差 INP 相关；单个标签影响可能很小，但几十上百个会累积。标签类型的影响由小到大大致是：图片像素、自定义模板、自定义 HTML。定期清理不用的代码和第三方脚本，非必要脚本延后触发。
- 不要用标签管理器加载立即影响体验的资源，如 cookie 提示、首屏大图和站点功能：它们会因此变晚，可能抬高 LCP 和 CLS，且有些用户会屏蔽标签管理器。
- 标题、canonical、robots、正文等 SEO 关键内容由服务端直接输出，不要依赖 GTM 注入（本套件口径）。
- 结构化数据可以用 GTM 的 Custom HTML 标签生成 JSON-LD，Google 有专门文档；但官方提醒，动态生成的 Product 标记会让 Shopping 抓取变得不那么频繁、不那么可靠，价格和库存这类变化快的内容尤其明显（[用 JavaScript 生成结构化数据](https://developers.google.com/search/docs/appearance/structured-data/generate-structured-data-with-javascript)）。如果用 GTM 注入，用富媒体搜索结果测试检查渲染后的结果。
- 不要在 GTM 中改写链接或插入隐藏链接（本套件口径；隐藏链接属于 Google 垃圾内容政策里的「隐藏文字和链接」）。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 数据层先于容器 | 查看页面源码，找 `dataLayer.push({page_type` 与 GTM 容器代码的先后；浏览器控制台运行 `window.dataLayer` | 通过：页面信息推送在容器代码之前，且 `window.dataLayer` 里有 `page_type`。失败：推送晚于容器，首个页面浏览事件缺参数 |
| 每个事件有触发器 | GTM 预览模式逐个触发，看 Tag Assistant 调试界面里标签是否触发、传了什么数据 | 通过：每个事件在对应动作后触发一次。失败：不触发或重复触发 |
| 同意触发器 | GTM → Triggers，看同意管理平台标签的触发器；预览里看它是否第一个触发 | 通过：用 Consent Initialization，且先于其他标签。失败：晚于分析标签触发 |
| 容器体积和自定义 HTML | GTM 工作区 → 标签列表按类型排序，数 Custom HTML 标签；用 [field_data.py](../../scripts/field_data.py)（`python3 scripts/field_data.py --help` 看参数）或 PageSpeed Insights 比较前后 INP/LCP | 通过：每个 Custom HTML 都有明确用途，且发布前后 INP/LCP 无变差。失败：无人认领的旧标签仍在，或发布后 INP 变差 |
| 渲染后结构化数据 | 把页面放进[富媒体搜索结果测试](https://search.google.com/test/rich-results)，看渲染后 HTML 是否有 JSON-LD | 通过：渲染后检出预期类型。失败：只有源码里有，渲染后没有，说明注入失败 |
| 发布记录 | GTM → Versions | 通过：最新发布版本有名称和说明，能还原到上一版。失败：版本说明为空 |

## 交付

- 代码、触发器、变量清单与命名。
- 数据层字段约定（给开发）。
- 预览验证记录和发布版本说明。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/analytics-tracking/references/gtm-implementation.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/analytics-tracking/references/gtm-implementation.md)（MIT）
- 一手资料：[Google 跟踪代码管理器帮助](https://support.google.com/tagmanager)、[数据层](https://developers.google.com/tag-platform/tag-manager/datalayer)、[用 JavaScript 生成结构化数据](https://developers.google.com/search/docs/appearance/structured-data/generate-structured-data-with-javascript)、[富媒体搜索结果测试](https://search.google.com/test/rich-results)、[web.dev：标签与标签管理器最佳实践](https://web.dev/articles/tag-best-practices)

## 连接器时代的变更纪律(notfair 深读 2026-10-09b)

来源:nowork-studio/notfair-plugin(第三方仓库)的 analytics/shared/operating-contract。以下条目是该仓库的工作纪律,属本套件口径,不是 Google 官方规则——衡量栈从"手改 GA4/GTM 后台"走向 MCP 连接器后,变更流程要补的纪律(与上面发布流程互补)。

- **读取靠批量**:一次宽的批量读优于反复窄读;配额与 fan-out 上限以连接器当前声明的为准,不照搬另一平台的限制。
- **事实/推断/建议三分**:观察到的数据、推断的原因、推荐的动作分开陈述;注明新鲜度、采样、阈值、行数上限、归因或跟踪局限。
- **归因不混源**:GA4、Search Console、广告平台的归因口径互不相同,先对齐定义再比较数值(同上"GSC 为基准线+GA4 建模值并列 consent rate"的报表结构)。
- **写前审批四件套**:确切资源、当前值、目标值、回滚路径,逐项展示并拿到明确批准后才动 sitemap 或测量配置类变更。
- **写后验证**:用返回的前后证据或一次新读确认;**"分析、建议或配置草稿"在没有连接器实时确认前一律不得称为已发布**——对应 GTM 语义:预览通过≠已上线,版本说明里区分"已验证/已发布"。
- **失败如实报**:部分成功按部分报,不盲目重试;重试同一逻辑动作时请求标识保持稳定,输入变了绝不复用旧标识(幂等纪律,来源同插件的 WordPress 连接器)。
