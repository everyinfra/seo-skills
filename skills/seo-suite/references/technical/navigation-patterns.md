# 导航模式与 SEO

用途：评估或设计页眉、页脚、侧栏、面包屑和移动端导航，让用户和爬虫都能顺利到达重要页面。语义标签写法见 [semantic-html.md](semantic-html.md)，整体链接结构见 [link-architecture-patterns.md](link-architecture-patterns.md)。

## 通用要求

- 导航链接必须是带有效 `href` 的 `<a>`；按钮只用于操作。纯脚本跳转、只在点击后才加载的菜单，爬虫可能发现不了。
- 导航内容出现在服务端输出的 HTML 中，不依赖用户交互才生成。
- 锚文本描述目标页内容，用用户熟悉的词，不用「点这里」。
- 页面上有多个导航区域时（主导航、页脚、侧栏），用 `nav` 并提供可区分的名称。
- 桌面和移动端给出同样的重要链接；Google 以移动版内容为主进行抓取和索引。

## 各区域的作用

| 区域 | 放什么 | 常见问题 |
|---|---|---|
| 页眉主导航 | 最重要的几类入口：产品或分类、定价、资源、关于 | 项目过多、用内部术语命名、下拉菜单只有 JS 才能展开 |
| 大型下拉菜单 | 分类多的电商或大型站点的二级入口 | 链接堆积、每页都重复几百个链接 |
| 页脚 | 次要但需要全站可达的页面：公司信息、法律条款、帮助、站点地图页 | 塞满关键词链接 |
| 侧栏 | 文档目录、博客分类、相关文章 | 目录过深、当前位置不清楚 |
| 面包屑 | 反映层级路径，帮助用户返回上级 | 与真实 URL 层级不一致、最后一项也做成链接指向自身 |
| 移动端菜单 | 与桌面一致的重要入口 | 移动端删减了重要链接 |

## 面包屑

- 路径与站点层级一致：首页 › 分类 › 子分类 › 当前页。
- 可配合 BreadcrumbList 结构化数据，标记内容与可见面包屑一致；写法见 [schema-templates.md](schema-templates.md)。

## 反模式

- 导航靠图片或图标，没有文字。
- 同一个页面在导航中出现多个不同名称。
- 用 `#` 或 `javascript:` 作为链接地址。
- 重要页面只能通过站内搜索到达。
- 为了「传递权重」在每页页脚放大量关键词链接。

## 检查方法

1. 查看服务端返回的 HTML（不执行 JS），确认导航链接存在且有 `href`。
2. 用爬虫工具导出内链数据，看重要页面的入链数量和点击深度。
3. 在手机视口下检查菜单中的链接是否与桌面一致。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/site-architecture/references/navigation-patterns.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/site-architecture/references/navigation-patterns.md)（MIT）
- 一手资料：[Google：可抓取链接与锚文本](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)、[Google：Breadcrumb 结构化数据](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)、[Google：JavaScript SEO 基础](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)
