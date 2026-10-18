# 内链架构模式

## 用途

重构站点结构、规划内链、排查孤立页和过深页、处理分面导航时读。导航组件的具体做法见 [navigation-patterns.md](navigation-patterns.md)；专题集群的内容规划见 [topic-cluster-templates.md](../research/topic-cluster-templates.md)。

## 一、前提：Google 靠链接发现页面

以下引自 Google [链接最佳实践](https://developers.google.com/search/docs/crawling-indexing/links-crawlable) 和 [JavaScript SEO 基础](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)（核对 2026-10-18）：

- Google 把链接用作判断相关性的信号，也用链接发现新页面。sitemap 帮助发现，但代替不了内链。
- 通常只有带 `href` 的 `<a>` 元素能被抓取。没有 `href` 的 `<a>`、靠脚本事件跳转的元素，Google 无法可靠提取。`href="javascript:…"` 不推荐。
- 用 JavaScript 插入的链接也能被抓取，前提是插入的是上面这种 `<a href>` 标记；Googlebot 会在渲染后的 HTML 里再解析一次链接。
- 你在意的每个页面，至少要有一个站内其他页面链向它。
- 一个页面放多少链接没有「理想数字」；Google 原话：如果你觉得太多，那多半就是太多。

## 二、结构模式与适用场景（本套件口径）

| 模式 | 形状 | 适合 | 要注意 |
|---|---|---|---|
| 层级 | 首页 → 分类 → 子分类 → 详情 | 电商、目录站、新闻栏目 | 分类页要有自己的说明内容；深层详情页需要横向链接补充入口 |
| 扁平 | 多数页面从首页一两次点击可达 | 页面不多的官网、作品集 | 页面一多，导航就会膨胀 |
| 专题集群（hub-and-spoke） | 支柱页概述主题并链到各子页，子页链回支柱页并相互链接 | 内容站、SaaS 博客、文档站 | 每个子页只挂一个主要支柱页；不要让几个页面争同一个搜索意图 |
| 网状 | 以正文里的上下文链接为主 | 知识库、文档、Wiki | 只在真正相关时链接 |
| 混合 | 分类做骨架，分类内做专题集群，跨分类用上下文链接桥接 | 多数中大型站点 | 先定骨架，再补横向链接 |

## 三、面包屑与上下文链接

- **面包屑**：每一级都是可点击的 `<a href>`。Google 建议面包屑写典型的用户访问路径，不必照搬 URL 层级；一个页面可以有多条面包屑路径（[Breadcrumb 文档](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)）。本套件口径：不要做成随用户浏览历史变化的路径。配 BreadcrumbList 结构化数据时必须与可见面包屑一致（见 [schema-templates.md](schema-templates.md)）；面包屑富结果 2025-01-22 起只在桌面结果显示。
- **上下文链接**：正文中指向真正相关页面的链接，是专题集群和网状结构的主要连接方式。Google 提示：链接前后的文字也有作用，不要把多个链接挨在一起。
- **相关推荐模块**：按内容的真实相关性生成，不要全站挂同一批链接（本套件口径）。

## 四、锚文本原则

依据 Google [链接最佳实践](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)（核对 2026-10-18）：

- 锚文本要描述目标页、简洁、与两端页面相关。自测方法：只读锚文本，脱离上下文也能大致知道目标页讲什么。
- 避免「点击这里」「阅读更多」这类泛称，也不要写得过长。
- 不要把相关关键词全塞进锚文本：关键词堆砌违反垃圾内容政策。
- 图片链接：Google 用 `img` 的 `alt` 作锚文本；`<a>` 为空时可用 `title` 属性兜底。用 JS 插入锚文本时，用网址检查工具确认它出现在渲染后的 HTML 里。
- 同一目标页在不同上下文里可以用不同的自然写法（本套件口径）。

## 五、排查孤立页与过深页

1. **全站爬取**：`python3 scripts/site_crawl.py example.com --max 5000 --out crawl.json`（robots、sitemap、爬虫三路发现，输出内外链图和孤儿页；`--strip-params` 丢弃查询参数；JS 渲染站另用支持渲染的爬虫交叉核对）。
2. **分析链接图**：`python3 scripts/link_graph.py --crawl crawl.json --json`，看深度直方图、零入链和单入链清单、锚文本审计（精确匹配锚占比超过 `--exact-threshold`，默认 0.60，退出码 1）。
3. **找孤立页**：把 sitemap（`python3 scripts/sitemap_audit.py https://example.com`）、Search Console 网页索引报告、GA4 落地页和服务器日志里出现、但爬虫从首页到不了的 URL 列出来，就是孤立页。
4. **过深页**：重要页面的点击深度明显高于同类页面。本套件口径：重要页面以 3 次点击内可达为起点，按站点规模校准；这不是 Google 的数字。
5. **处理孤立页**：`python3 scripts/orphan_fix.py --crawl crawl.json --max 50` 生成「源页 → 孤儿页 → 建议锚文本」清单。有价值的从分类页、支柱页或相关页加链接；没价值的合并、重定向或删除。
6. **处理过深页**：在分类页加入口、补上下文链接、增加「热门 / 最新」入口、改进分页。
7. **分页**（[Google 分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading)）：每页一个独立 URL（例如 `?page=n`），用 `<a href>` 链到下一页；可以从各页链回第一页；不要把第一页设为所有分页的 canonical，每页用自己的 canonical；页码不要用 `#` 片段；Google 不再使用 `rel="next"/"prev"`。

## 六、分面导航与参数页

以 Google [分面导航抓取管理](https://developers.google.com/crawling/docs/faceted-navigation) 为准（2024-12-17 成文，2025-12-18 迁到抓取基础设施站点，核对 2026-10-18）：

- 参数化的分面会产生近乎无限的 URL 空间：爬虫过度抓取，新的有用 URL 发现变慢。
- 不需要被索引的分面 URL：用 robots.txt 禁止抓取（只放行商品页和一个不带筛选的全量列表页），或用 URL 片段（`#`）实现筛选。
- 需要被索引的组合（例如有真实搜索需求的「品类 + 品牌」，本套件口径）：参数分隔符用标准的 `&`；路径式筛选保持顺序固定、不出现重复筛选；无结果、重复或无意义的组合在原 URL 返回 404，不要重定向到通用错误页。
- canonical 和 nofollow 只是辅助：长期效果通常不如 robots.txt 和片段方案；nofollow 要所有指向该 URL 的锚点都加才有效。大型站点再对照[抓取预算](https://developers.google.com/crawling/docs/crawl-budget)文档（适用于 100 万以上页面且每周变化，或 1 万以上页面且每天变化的站点）。

## 七、交付时给出

- 现状：点击深度分布、孤立页清单、入链最多和最少的重要页面、分面 URL 的数量级。
- 目标结构图（可用 Mermaid，见 [mermaid-templates.md](mermaid-templates.md)）。
- 链接修改清单：来源页、目标页、锚文本、位置、优先级。
- 验证方式：上线后重新爬取对比；在 Search Console 看网页索引报告和抓取统计的变化。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 链接可抓取 | `curl -s URL \| grep -o '<a [^>]*>' \| grep -vc 'href='` 统计无 href 的 `<a>`；网址检查工具看渲染后 HTML | 导航和正文链接都是 `<a href>` → 通过；靠 onclick 跳转 → 失败 |
| 孤立页 | `site_crawl.py` + `link_graph.py --json` 的零入链清单，对照 sitemap 与索引报告 | 重要页面零入链 = 失败 |
| 点击深度 | `link_graph.py` 深度直方图 | 重要页面深度明显高于同类 → 列入修复（阈值本套件口径） |
| 锚文本 | `link_graph.py` 锚文本审计 | 退出码 0 → 通过；1 → 精确匹配锚过度集中 |
| 分页 | 抽查第 2、3 页的 canonical 与链接 | 每页自指 canonical、有 `<a href>` 到下一页 → 通过 |
| 分面爬取 | `python3 scripts/log_session.py --log access.log --window 30m` 看 param_loop 陷阱；日志按目录统计筛选参数 URL 的 Googlebot 抓取占比 | 筛选 URL 占比持续上升或出现参数循环 → 收紧 robots.txt |
| 无结果组合 | `curl -s -o /dev/null -w '%{http_code}' 'https://example.com/c?color=不存在的值'` | 返回 404 → 通过；200 空页或重定向 → 失败 |

## 常见误区

- 以为提交了 sitemap 就不需要内链。
- 在全站页脚堆大量关键词链接。
- 给内链加 nofollow 来「分配权重」。不想被编入索引用 noindex，不想被抓取用 robots.txt。
- 承诺调整内链会带来某个百分比的流量增长。

## 市场差异：日本站点的内链惯例（本套件观察，未见官方数字）

- タグ页、作者归档页内容稀薄时设 noindex（日本站点常见做法，未核主题文档）。
- カテゴリ页文章数足够时保持 index，当作着陆页争排名。
- パンくず配 BreadcrumbList JSON-LD。
- 旧版本文写的「3 クリック以内」「1 見出し 1–2 本、3,000 字 4–8 本」「单页被内链 45 本以上点击下降」没有可核实出处，已删除；内链数量按 Google「没有理想数字」的口径判断。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/internal-linking-optimizer/references/link-architecture-patterns.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/optimize/internal-linking-optimizer/references/link-architecture-patterns.md)（Apache-2.0）
- 一手资料（核对 2026-10-18）：[链接最佳实践](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)、[JavaScript SEO 基础](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)、[分面导航](https://developers.google.com/crawling/docs/faceted-navigation)、[抓取预算](https://developers.google.com/crawling/docs/crawl-budget)、[网址结构](https://developers.google.com/search/docs/crawling-indexing/url-structure)、[站点地图](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)、[Breadcrumb](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)、[分页与增量加载](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading)、[文档更新记录](https://developers.google.com/search/updates)
