# 结构化数据验证

> 涉及 FAQPage 或 AI 引用的判断，先读 [geo-evidence.md](../content/geo-evidence.md)。

## 用途

新增或修改 schema 后做验收、审计别人的站点、排查「富结果不出现」时读。类型怎么选见 [schema-templates.md](schema-templates.md)。

## 一、三层验证，分开记录结论

| 层 | 要回答的问题 | 用什么查 |
|---|---|---|
| 1. 词汇 | JSON 能否解析；schema.org 类型和属性是否存在；值的类型对不对 | [Schema Markup Validator](https://validator.schema.org/) |
| 2. Google 支持与资格 | 该类型是否在 Google [类型库](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)里；Google 要求的属性齐不齐；是否违反[通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies) | [富媒体搜索结果测试](https://search.google.com/test/rich-results)、Search Console 的富结果报告和网址检查 |
| 3. 与可见内容一致 | 每个字段在渲染后的页面上能否找到对应的可见内容 | 浏览器渲染后的 DOM 加截图，逐字段对照 |

三层是三个结论，不合并成一个「通过」。例如 FAQPage 可以词汇合法，但 FAQ 富结果已停止展示，也不代表 AI 会优先引用。富媒体搜索结果测试只列出 Google 富结果支持的类型，没列出来不等于页面上没有其他 schema。三层都通过也不保证展示富结果，这不算验证失败。

## 二、不能只凭源码说「没有 schema」

JSON-LD 可能由前端框架、跟踪代码管理器或插件在渲染时注入，Google 能读取 JavaScript 注入的 JSON-LD（见[用 JavaScript 生成结构化数据](https://developers.google.com/search/docs/appearance/structured-data/generate-structured-data-with-javascript)）。所以 `curl` 或静态抓取看不到，不能作为「没有 schema」的证据。要下这个结论，至少要有下面一项：

- 浏览器渲染后 DOM 的检查结果；
- 富媒体搜索结果测试用 URL 模式的结果；
- Search Console 网址检查「测试实际网址」里 Google 看到的内容（需要该站点的 Search Console 权限）；
- 用户提供的渲染后 HTML 或截图。

还要查 microdata、RDFa 这类其他格式（`itemscope`、`typeof` 属性），以及 CDN 或服务端是否给爬虫和浏览器返回了不同内容。

在浏览器开发者工具控制台里列出所有 JSON-LD 并检查能否解析（自写示例）：

```js
[...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => {
  try { return JSON.parse(s.textContent); } catch (e) { return "解析失败：" + e.message; }
});
```

## 三、排查顺序

1. **页面本身**：能否抓取、有没有 noindex、状态码是否为 200。测试工具抓不到页面时，先解决这个问题。
2. **有没有标记**：渲染后 DOM 里有没有 JSON-LD 或 microdata；有几份，是否被几个插件重复输出。
3. **能否解析**：JSON 语法是否合法。
4. **词汇**：类型名、属性名拼写（区分大小写），值的类型和嵌套是否正确。
5. **Google 要求**：该类型是否受支持，必填属性是否齐全，是否符合政策。错误（error）会让该项失去资格；警告（warning）通常是缺少推荐属性，可以按需补。
6. **一致性**：价格、库存、评分、日期、作者、问答文本与页面逐条对照。
7. **上线后**：看 Search Console 对应的富结果报告；修复后用「验证修复」，并记下日期。
8. **仍不展示**：确认该功能当前是否还在展示（FAQ、HowTo 已不再展示），再检查人工处置和内容质量；不要为了「拿到展示」去改标记内容。

## 四、常见错误

- JSON 语法：末尾多余逗号、中文引号、未转义的双引号或换行。
- 属性名大小写写错，例如把 `datePublished` 写成 `datepublished`。
- 日期不是 ISO 8601 格式；URL 用了相对路径（绝对地址最稳妥）。
- 价格里带货币符号。按 [schema.org 的 price 说明](https://schema.org/price)，币种应写在 `priceCurrency` 里。
- 枚举值写成普通文字，例如库存状态应写 `https://schema.org/InStock`，而不是「有货」。
- 同一实体被多个插件各输出一份，且内容互相矛盾。
- 标记与页面不一致：价格过期、页面上没有的评价、隐藏的问答。

## 交付时给出

每个受检 URL 的验证记录：检查时间、设备或 User-Agent、所用工具、是否基于渲染后内容；三层各自的结论；错误和警告清单；截图或工具导出作为证据；修复建议和复查日期。

## 罕见判定法(seo-ops C 集,百仓扫描批 3;直接可落成检查规则)

- **C26 Accept-Language 跳转探测**:en-US 与 zh-CN 双语 fetch,对比 final_url——抓"自动语言跳转"导致的重复/错配;
- **C9 无 JS 完整性**:禁 JS 抓取≥90% 渲染版内容才算服务端完整(量化 SPA 判定);
- **C10 缓存个性化验证**:双匿名抓取 diff 为空=缓存非个性化;
- **C13 soft-404 双阈值**:长度+词数双低即判(不只看 200 状态);
- **C2 lastmod 验真**:覆盖率/离散度/单日聚簇——批量同日 lastmod=伪造信号;
- **C27 head 合法性**:head 内出现非法元素提前终止解析检查。
- **T 集反向映射**:内容团队须供给的输入(标题/H2 大纲/alt/YMYL 判断/OG 文案)反向映射到下游检查——审计前先收供给清单。
- **清单治理**:检查 ID 永久不回收;同优先级+同抓取动作则合并。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/schema-markup-generator/references/validation-guide.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/schema-markup-generator/references/validation-guide.md)（Apache-2.0）
- 一手资料：[结构化数据简介](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)、[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)、[结构化数据类型库](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)、[用 JavaScript 生成结构化数据](https://developers.google.com/search/docs/appearance/structured-data/generate-structured-data-with-javascript)、[富媒体搜索结果测试](https://search.google.com/test/rich-results)、[Schema Markup Validator](https://validator.schema.org/)、[schema.org price](https://schema.org/price)
