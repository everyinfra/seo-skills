# 竞品对照卡（SEO 视角）

## 用途与何时读

做竞品分析、准备对比页和替代方案页、或者要给内容团队一份统一的竞品事实时读。对照卡是**分析视图**：一张卡对应一个竞品，汇总对方怎么定位、在搜索里占了什么位置、强弱项和我们的差异点。

页面上实际展示的价格和功能，应来自竞品数据的单一事实源，见 [competitor-content-architecture.md](competitor-content-architecture.md)；对照卡里的结论再落到页面，见 [competitor-section-templates.md](competitor-section-templates.md) 和 [competitor-page-patterns.md](competitor-page-patterns.md)。

## 诚实原则

这些是硬要求，不满足的条目不能用于对外页面：

1. **每条事实有来源和核对日期。** 来源写到具体 URL（定价页、文档、更新日志、公开评价），日期写到天。
2. **标明证据类型**：对方自述、第三方评价、我们实测、推断。推断不能写成事实。
3. **价格和功能写清套餐、地区和版本**，对方没公开的写「未公开」，拿不准的写「待核实」，不要猜。
4. **承认对方的强项和它更适合的人群。** 只写对手缺点的对照卡，团队不会信，读者也不会信。
5. **弱项必须可核查**：来自公开评价、对方文档或可复现的实测；不引用截断或来源不明的评论。
6. **不贬损、不暗示。** 对外发布的比较性说法要真实、可证实；各地对比较广告有不同规定，对外使用前按所在市场的要求确认。

## 栏目

| 栏目 | 写什么 | 常见来源 |
|---|---|---|
| 基本信息 | 名称、官网、主要客户类型、定价模式 | 对方官网 |
| 自述定位 | 对方怎么介绍自己、反复强调哪几点 | 首页、定价页、广告落地页 |
| 搜索足迹 | 对方在哪些主题和查询上排在前列，主力页面类型，品牌词 SERP 上出现了哪些评价站和对比页 | Search Console 看不到对手数据，需用你自有或自选的工具（商业 SEO 工具需要你自己的账号），估算值要标注 |
| 强项 | 对方做得确实好的地方和证据 | 实测、公开评价、文档 |
| 弱项 | 有证据的限制和常见抱怨 | 公开评价、文档里的限制说明、实测 |
| 我们的差异点 | 我们更好的地方，以及能展示的证据（演示、数据、案例） | 我们的产品和客户资料 |
| 功能与价格对照 | 逐项对照，每格附来源和日期 | 双方官网、文档 |
| 用户常见顾虑 | 用户在两者之间犹豫时问什么，我们怎么如实回答 | 销售和客服记录、社区提问 |
| 适合谁 / 不适合谁 | 双方各自适合的场景 | 综合以上内容 |
| 内容机会 | 可以做的对比页、替代方案页，需要补的主题 | 搜索足迹和缺口分析 |

「用户常见顾虑」和「适合谁」两栏，是对比页 FAQ 和结论段最直接的素材。缺口怎么找见 [gap-analysis-frameworks.md](gap-analysis-frameworks.md)，定位怎么选见 [positioning-frameworks.md](positioning-frameworks.md)。

## 空白骨架

```markdown
## 竞品对照卡：竞品 A
核对日期：YYYY-MM-DD ｜ 维护人： ｜ 整体可信度：高 / 中 / 低

| 栏目 | 要点 | 来源 URL | 证据类型 | 核对日期 |
|---|---|---|---|---|
| 自述定位 |  |  |  |  |
| 搜索足迹 |  |  |  |  |
| 强项 |  |  |  |  |
| 弱项 |  |  |  |  |
| 我们的差异点 |  |  |  |  |
| 功能与价格 |  |  |  |  |
| 适合谁 / 不适合谁 |  |  |  |  |
| 内容机会 |  |  |  |  |
```

## 更新

- **触发更新**：对方改价、发布或下线功能、改定位；我们上线相关能力；对比页收到事实纠错。
- **定期复核**：周期由团队按竞品变化速度决定，复核时逐条更新核对日期。
- 过期或无法再核实的条目标记出来，移到历史记录，不直接删除。
- 对照卡更新后，同步检查引用这些事实的对外页面。

## 交付物

1. 每个主要竞品一张对照卡（按上面的骨架）。
2. 一张汇总表：各竞品的主要强项、弱项、我们的差异点和建议优先做的页面，格式可用 [competitor-analysis-output.md](../../templates/research/competitor-analysis-output.md)。
3. 待核实清单：还缺证据、不能对外使用的条目。

## 常见误区

- 把对方营销话术当成事实写进对照表。
- 价格截图没有日期，几个月后还在页面上用。
- 用「更强」「更好」这类结论，却没有对应的证据。
- 按销售话术写对照卡，把挖坑式提问、夸大对手缺点带进对外内容。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · research/competitor-analysis/references/battlecard-template.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/research/competitor-analysis/references/battlecard-template.md)（Apache-2.0）
- 一手资料：[撰写高质量评测](https://developers.google.com/search/docs/specialty/ecommerce/write-high-quality-reviews)、[有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)
