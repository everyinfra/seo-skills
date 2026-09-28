# 内链架构模式

## 用途

重构站点结构、规划内链、排查孤立页和过深页、处理分面导航时读。导航组件的具体做法见 [navigation-patterns.md](navigation-patterns.md)；专题集群的内容规划见 [topic-cluster-templates.md](../research/topic-cluster-templates.md)。

## 一、前提：Google 靠链接发现页面

- Google 主要通过已抓取页面上的链接发现新页面。sitemap 帮助发现，但代替不了内链。
- 只有带 `href` 的 `<a>` 链接能被可靠抓取；只靠 JavaScript 点击事件跳转的元素不算（见[可抓取链接](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)）。
- JavaScript 生成的导航，要确认链接出现在渲染后的 DOM 里。

## 二、结构模式与适用场景

| 模式 | 形状 | 适合 | 要注意 |
|---|---|---|---|
| 层级 | 首页 → 分类 → 子分类 → 详情 | 电商、目录站、新闻栏目 | 分类页要有自己的说明内容；深层详情页需要横向链接补充入口 |
| 扁平 | 多数页面从首页一两次点击可达 | 页面不多的官网、作品集 | 页面一多，导航就会膨胀失控 |
| hub-and-spoke / 专题集群 | 支柱页概述主题并链到各子页，子页链回支柱页并相互链接 | 内容站、SaaS 博客、文档站 | 每个子页只挂一个主要支柱页；不要让几个页面争同一个搜索意图 |
| 网状 | 以正文里的上下文链接为主，按相关性互链 | 知识库、文档、Wiki | 定好规则：只在真正相关时链接 |
| 混合 | 分类做骨架，分类内做专题集群，跨分类用上下文链接桥接 | 大多数中大型站点 | 先定骨架，再补横向链接 |

## 三、面包屑与上下文链接

- **面包屑**反映页面在层级里的位置，而不是用户的浏览路径；每一级都是可点击的 `<a href>`。可以配 BreadcrumbList 结构化数据，但必须与页面上可见的面包屑一致（见 [schema-templates.md](schema-templates.md)、[Breadcrumb 文档](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)）。
- **上下文链接**是正文中指向真正相关页面的链接，是专题集群和网状结构的主要连接方式。放在读者需要进一步了解的地方。
- **相关推荐模块**按内容的真实相关性生成，不要全站挂同一批链接。

## 四、锚文本原则

- 描述目标页的内容，读者不看上下文也能大致知道点过去是什么。
- 简洁；避免「点击这里」「更多」这类泛称，也不要在全站反复堆同一个精确关键词。
- 同一目标页在不同上下文里，可以用不同的自然写法。
- 图片链接用图片的 alt 作为锚文本。

## 五、排查孤立页与过深页

1. 用你自选的爬虫工具（例如 Screaming Frog）从首页全站爬取，JavaScript 站点开启渲染；导出每个 URL 的点击深度和入链数。
2. 与 sitemap、Search Console 中已编入或已发现的 URL、GA4 落地页、服务器日志里的 URL 对比：这些来源里有、但从首页爬不到的，就是孤立页。
3. 过深页：重要页面的点击深度明显高于同类页面。「重要页面尽量在 3 次点击内可达」只是经验起点，要按站点规模校准。
4. 处理孤立页：有价值的，从相关页面、分类页或支柱页加链接；没价值的，合并、重定向或删除。
5. 处理过深页：在分类页加入口、补上下文链接、增加「热门 / 最新」入口、改进分页。
6. 分页：每一页有独立 URL，用 `<a href>` 依次链接；不要把所有分页的 canonical 都指向第一页（见[电商网站](https://developers.google.com/search/docs/specialty/ecommerce)文档中的分页说明）。

## 六、分面导航与参数页

以 Google [分面导航](https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation)文档为准，要点：

- 筛选、排序参数的组合会产生几乎无限的 URL，浪费抓取，还会产生大量重复页。
- 先确定哪些组合有独立的搜索需求（例如「品类 + 品牌」），把它们做成可索引的独立页面，纳入内链和 sitemap。
- 其余组合如果不需要被抓取，用 robots.txt 禁止相关参数，或者用 URL 片段（`#`）实现筛选。
- 需要被抓取的参数 URL：参数用标准的 `?key=value&key2=value2` 写法，顺序固定；没有结果的组合返回 404，而不是返回 200 的空页。
- canonical 和 nofollow 只是较弱的辅助手段，不能指望它们单独控制抓取量。大型站点再对照[抓取预算](https://developers.google.com/search/docs/crawling-indexing/large-site-managing-crawl-budget)文档。

## 七、交付时给出

- 现状：点击深度分布、孤立页清单、入链最多和最少的重要页面、分面 URL 的数量级。
- 目标结构图（可用 Mermaid，见 [mermaid-templates.md](mermaid-templates.md)）。
- 链接修改清单：来源页、目标页、锚文本、位置、优先级。
- 验证方式：上线后重新爬取对比；在 Search Console 看页面索引报告和抓取统计的变化。

## 常见误区

- 以为提交了 sitemap 就不需要内链。
- 在全站页脚堆大量关键词链接。
- 给内链加 nofollow 来「分配权重」。不想被编入索引用 noindex，不想被抓取用 robots.txt。
- 承诺调整内链会带来某个百分比的流量增长。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/internal-linking-optimizer/references/link-architecture-patterns.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/optimize/internal-linking-optimizer/references/link-architecture-patterns.md)（Apache-2.0）
- 一手资料：[可抓取链接与锚文本](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)、[分面导航](https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation)、[大型网站抓取预算](https://developers.google.com/search/docs/crawling-indexing/large-site-managing-crawl-budget)、[网址结构](https://developers.google.com/search/docs/crawling-indexing/url-structure)、[站点地图](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)、[Breadcrumb](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)、[电商网站](https://developers.google.com/search/docs/specialty/ecommerce)
