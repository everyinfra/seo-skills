# 竞品页的数据与链接架构

## 用途与何时读

要做一批对比页、替代方案页，或者现有对比页之间事实对不上、难以维护时读。页面类型和结构见 [competitor-page-patterns.md](competitor-page-patterns.md)，各区块怎么写见 [competitor-section-templates.md](competitor-section-templates.md)。

## 为什么要单一事实源

同一个竞品的价格、功能、适用人群会同时出现在替代方案页、对比页、汇总页里。每页手工维护，迟早出现同一竞品在两页价格不同、或者半年前的价格还挂着的情况。

做法：**每个竞品一份结构化数据**（YAML、JSON 或 CMS 条目），**我们自己的产品也按同一结构写一份**，页面从数据渲染。改一处，所有引用页面一起更新，来源和核对日期也集中在一处。

## 字段

| 分组 | 字段 | 要求 |
|---|---|---|
| 身份 | 名称、官网、品类、主要客户 | 品类用用户搜索时的叫法 |
| 定位 | 主要用途、对方自述的主张 | 自述要附来源页 |
| 价格 | 计费模式、免费档及限制、各档价格、币种、计费周期、适用地区 | 附来源 URL 和核对日期；没公开就写「未公开」 |
| 功能 | 逐项状态：有 / 部分 / 无 / 未公开，加一句说明 | 每项附来源；不用没有评分方法的主观分数 |
| 强项、弱项 | 各几条，写清证据 | 弱项要可核查 |
| 适合谁、不适合谁 | 场景化描述 | 我们自己那份也要写「不适合谁」 |
| 迁移 | 导出格式、能迁移和不能迁移的内容、我们提供的迁移帮助 | 按实测写 |
| 元数据 | 来源 URL、核对日期、维护人、可信度 | 至少到字段组一级 |

最小示例（占位数据）：

```yaml
id: competitor-a
name: 竞品 A
website: https://competitor-a.example.com
category: 团队文档工具
pricing:
  model: per_seat
  currency: USD
  plans:
    - name: 基础版
      price: 未公开
  source: https://competitor-a.example.com/pricing
  checked_at: 2026-01-15
features:
  offline_mode:
    status: partial        # yes / partial / no / unknown
    note: 仅桌面端支持
    source: https://competitor-a.example.com/docs/offline
    checked_at: 2026-01-15
best_for: [需要高度自定义的小团队]
not_ideal_for: [对离线使用要求高的团队]
```

## 更新机制

- **有效期**：每个字段组有核对日期，超过团队设定的有效期自动标记为待复核。有效期没有通用标准，按竞品改价和发布的频率定。
- **触发更新**：对方定价页或更新日志变化、我们上线相关能力、读者或对方提出纠错。
- **走版本控制**：每次修改有记录、有审核人，能回看改了什么。
- **页面同步**：数据变更后重建所有引用页面；页面上显示的「最后核对日期」取自数据本身。
- **未知就写未知**：缺失字段在页面上显示「未公开」或「待核实」，不能省略成对我们有利的样子。
- 结构化数据只描述页面上可见的内容，不给竞品编造评分。

## 页面从数据取什么

| 页面类型 | 取自数据 | 仍需人工撰写 |
|---|---|---|
| 某竞品的替代方案 | 该竞品 + 我们 | 用户为什么离开它、迁移建议 |
| 某竞品的替代方案盘点 | 该竞品 + 我们 + 其他几个替代方案 | 评估标准、分场景推荐 |
| 我们 vs 某竞品 | 我们 + 该竞品 | 结论、各自适合谁 |
| 竞品 A vs 竞品 B | 两个竞品 + 我们 | 双方比较、何时考虑第三种选择 |

模板只负责排版和数据一致；每页的判断和解释必须针对这一对比较单独写。只替换竞品名批量生成、没有独立价值的页面，可能落入 Google 垃圾内容政策里「大规模滥用内容」的范围。

## 汇总页与单页的链接结构

- **两个汇总页**：替代方案汇总（例如 `https://example.com/alternatives/`）和对比汇总（例如 `https://example.com/compare/`）。每个竞品一行：一句话差异加链接；竞品多时按品类或场景分组，并显示最后更新日期。
- **单页链回汇总页**；同一竞品的替代方案页和对比页互链；同类竞品之间在语境相关时互链。
- **从业务页面引流**：功能页、解决方案页、定价页在相关段落链到对应对比页。
- **页脚和导航**：可以放两个汇总页和少数最重要的对比页，主要作用是方便发现和导航；不要把全部对比页塞进页脚。
- **URL 规则统一**：同一类页面用同一种路径模式，全部列入站点地图。
- 站点级内链方法见 [link-architecture-patterns.md](../technical/link-architecture-patterns.md)。

## 交付物

1. 数据模型：字段表和取值规则。
2. 每个竞品和我们自己的数据文件。
3. 更新流程：有效期、触发条件、维护人、审核方式。
4. 页面取数对应表，以及每页需要人工撰写的部分。
5. 汇总页、单页、业务页之间的内链方案和 URL 规则。

规划汇总可用 [competitor-pages-plan.md](../../templates/research/competitor-pages-plan.md)。

## 常见误区

- 价格直接写进页面正文，改价时漏改几页。
- 只给竞品建数据，我们自己的产品不按同一标准写。
- 数据里没有来源和日期，出了争议无从核对。
- 用模板批量铺页，每页只有竞品名不同。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/competitor-alternatives/references/content-architecture.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/competitor-alternatives/references/content-architecture.md)（MIT）
- 一手资料：[可抓取链接与锚文本](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)、[网址结构](https://developers.google.com/search/docs/crawling-indexing/url-structure)、[站点地图](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)、[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)、[垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)
