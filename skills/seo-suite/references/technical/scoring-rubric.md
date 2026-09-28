# 单页 SEO 审计评分

## 用途

对单个页面（或同一模板的一批页面）做 on-page 审计、需要给出可比较的分数和修复优先级时读。结果填进 [on-page-audit.md](../../templates/audit/on-page-audit.md)。

**分数只是内部排序工具**：用来比较页面、跟踪修复进度，不是 Google 的指标，也不能预测排名。

## 一、先过门槛，再打分

以下任何一项不通过，先列为最高优先级问题，不急着算总分：

- 返回 200，没有被重定向到别处（见 [http-status-codes.md](http-status-codes.md)）。
- 没有被 robots.txt 屏蔽，也没有 noindex（见 [robots-txt-reference.md](robots-txt-reference.md)）。
- canonical 指向自身，或指向一个合理的规范版本。
- 渲染后的主内容可见：JavaScript 渲染的页面，要看渲染后的 DOM，不能只看源码。

## 二、评分维度与默认权重

默认权重是**可调的经验起点**。按页面类型调整（例如商品页提高图片和页面体验的权重，长文指南提高内容的权重），并在报告里写明用了哪套权重。

| 维度 | 权重 | 检查什么 |
|---|---|---|
| 意图匹配与内容 | 30 | 是否直接满足目标查询的意图；有没有原创的信息、经验或数据；事实准确，注明出处和更新日期；作者或负责主体清楚（对照 Google 的[有用内容自评问题](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)） |
| 标题与描述 | 15 | `<title>` 准确、独特，并写明页面主题；meta description 准确概括本页、不与其他页重复（见[标题链接](https://developers.google.com/search/docs/appearance/title-link)、[摘要](https://developers.google.com/search/docs/appearance/snippet)） |
| 链接 | 15 | 内链用可抓取的 `<a href>`，锚文本描述目标页；指向相关页面；没有失效链接；出站链接指向可靠来源，rel 使用正确 |
| 页面体验 | 15 | 有 CrUX 字段数据时看 Core Web Vitals，没有时用实验室数据诊断并注明；HTTPS；移动端内容与桌面端一致；没有遮挡主内容的弹窗 |
| 结构与可读性 | 10 | 标题层级能反映内容结构；段落、列表、表格用得合适；语义 HTML（见 [semantic-html.md](semantic-html.md)） |
| 结构化数据 | 10 | 类型合适，与可见内容一致，能通过验证（见 [validation-guide.md](validation-guide.md)）；没有标记本身不扣光这一项，只在该页类型确有合适的 Google 支持类型时提出建议 |
| 图片与媒体 | 5 | alt 描述图片内容；尺寸与显示尺寸相称；首屏主图不懒加载 |

## 三、打分方法

1. 每个维度拆成若干检查项，每项记为「通过 / 部分 / 未通过 / 无法验证」，分别按 1、0.5、0 计分。
2. 「无法验证」（例如没有字段数据、拿不到渲染后页面）不计入分母，并在报告里单列，不能猜。
3. 维度得分 = 得分 ÷ 可验证项数 × 权重；总分为各维度之和，满分 100。
4. **每个扣分项都附证据**：URL、检查时间、设备或 User-Agent，加上渲染后 DOM 片段、截图或工具导出（例如 Lighthouse 报告、Search Console 网址检查结果（需要该站点的权限）、爬虫导出）之一。
5. 修复优先级按「影响 × 修复成本」排，不按扣分多少排；门槛问题永远排第一。

## 四、评分纪律

- 各维度独立打分，不要因为标题写得好，就给内容也打高分。
- 对照检查项打分，不对照竞品打分；和竞品比较是另一项分析。
- 同一模板的页面放在一起评，模板问题只记一次，并注明影响的页面数。
- 两次评分（或两个人）结果差距大的检查项，把判定标准写得更具体。

## 五、不要作为扣分依据

以下说法没有 Google 一手依据，或与 Google 的说明相反（见 [SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)里「不必关注」的部分），不作为扣分项：

- 固定的字数目标、关键词密度。堆砌关键词本身违反[垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)。
- 「只能有一个 H1」「标题层级不能跳级」。层级清楚有助于读者和辅助技术，可以作为可读性建议，但不作为排名问题扣分。
- `<title>` 或 meta description 的固定字符数。Google 按设备宽度截断，并可能改写标题；只有在真实结果里被截断、影响理解时才提出。
- URL 里必须含关键词。
- 为了富结果加 FAQPage。FAQ 富结果已停止展示，FAQPage 只用于页面上真实存在的问答（见 [geo-evidence.md](../content/geo-evidence.md)）。

## 交付时给出

总分和各维度得分、所用权重、门槛检查结果、「无法验证」清单、按优先级排列的问题表（问题、证据、影响、建议、验证方法）。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/on-page-seo-auditor/references/scoring-rubric.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/optimize/on-page-seo-auditor/references/scoring-rubric.md)（Apache-2.0）
- 一手资料：[SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)、[有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[标题链接](https://developers.google.com/search/docs/appearance/title-link)、[摘要与 meta description](https://developers.google.com/search/docs/appearance/snippet)、[可抓取链接与锚文本](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)、[Core Web Vitals 与 Google 搜索](https://developers.google.com/search/docs/appearance/core-web-vitals)、[优化 LCP](https://web.dev/articles/optimize-lcp)、[垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)
