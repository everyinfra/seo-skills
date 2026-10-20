# 导航模式与 SEO

用途：评估或设计页眉、页脚、侧栏、面包屑和移动端导航，让用户和爬虫都能到达重要页面。语义标签写法见 [semantic-html.md](semantic-html.md)，整体链接结构见 [link-architecture-patterns.md](link-architecture-patterns.md)。

## 通用要求

- 导航链接必须是带有效 `href` 的 `<a>`；按钮只用于操作。Google 通常只抓取带 `href` 的 `<a>`，靠脚本事件跳转的元素无法可靠提取（[Google 链接最佳实践](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)，核对 2026-10-21）。
- 导航链接最好直接出现在服务端返回的 HTML 中。用 JS 插入也可以，但要等渲染队列处理后才被发现（[JavaScript SEO 基础](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)）；不渲染 JS 的爬虫看不到。
- 锚文本描述目标页内容，用用户熟悉的词，不用「点这里」。
- 页面上有多个导航区域时（主导航、页脚、侧栏），每个用 `nav` 并给出可区分的名称（`aria-label`；见 [W3C WAI 页面区域教程](https://www.w3.org/WAI/tutorials/page-structure/regions/)）。
- 桌面和移动端给出同样的重要链接：Google 用智能手机版 Googlebot 抓取的移动版内容做索引（[移动优先索引](https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing)）。

## 各区域的作用

| 区域 | 放什么 | 常见问题 |
|---|---|---|
| 页眉主导航 | 最重要的几类入口：产品或分类、定价、资源、关于 | 项目过多、用内部术语命名、下拉菜单只有 JS 才能展开 |
| 大型下拉菜单 | 分类多的电商或大型站点的二级入口 | 链接堆积、每页都重复几百个链接 |
| 页脚 | 次要但需要全站可达的页面：公司信息、法律条款、帮助、站点地图页 | 塞满关键词链接 |
| 侧栏 | 文档目录、博客分类、相关文章 | 目录过深、当前位置不清楚 |
| 面包屑 | 典型的上级路径，帮助用户返回 | 视觉与结构化数据不一致；最后一项做成指向自身的链接 |
| 移动端菜单 | 与桌面一致的重要入口 | 移动端删减了重要链接 |

## 大型下拉菜单（mega menu）

- **链接数量**：Google 说一个页面放多少链接没有「理想数字」，「如果你觉得太多，那多半就是太多」（[链接最佳实践](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)）。旧版本文引用的「约 100 条后收益递减」「单页 145 条」等数字来自论坛和博客，没有方法说明，不作为阈值。
- **全站复制**：mega menu 在每页重复全部链接。好处是二级类目全站一次点击可达；代价是正文链接占比被稀释。经典 PageRank 模型把一个页面的分值按出链数平分（[Brin & Page 1998](http://infolab.stanford.edu/~backrub/google.html)）；Google 现行算法未公开，这只是推理依据，不是可量化的规则。
- **JS 展开**：下拉项只在悬停或点击后才由 JS 注入 DOM 时，要等渲染后才能被发现。做法：链接全部写进服务端 HTML，只用 CSS 控制显隐。Googlebot 解析 HTML 响应里的 `href`（官方）；CSS 隐藏的菜单链接仍在 HTML 里，同样会被解析（推论）。
- **收口方法**（本套件口径）：顶部只留一级类目，二级下沉到类目页和页脚精简区；用点击数据和日志验证菜单项是否真的被用；没有数据支撑的「SEO 链接」直接删。

## 分面导航（faceted navigation）

分面导航按参数组合展开 URL 空间，会导致过度抓取并拖慢新页面的发现（[Google 分面导航抓取管理](https://developers.google.com/crawling/docs/faceted-navigation)，页面最后更新 2025-12-18，已迁到抓取基础设施站点，核对 2026-10-21）。规则层见 [redirects-canonical.md](redirects-canonical.md)，这里只管导航层。官方给两条路：

**路径一：分面 URL 不需要被索引 → robots.txt 禁止抓取**（官方示例改写）

```
User-agent: Googlebot
Disallow: /*?*color=
Disallow: /*?*size=
Allow: /*?products=all$
```

官方原意：抓取筛选结果通常没有必要，只消耗服务器资源；只放行商品页和一个不带筛选的全量列表页。也可以用 URL 片段（`#products=fish`）实现筛选：Google 一般不支持抓取片段，对抓取没有影响，也不会产生新 URL。

**路径二：部分组合需要被索引 → 官方细则**

- 参数分隔符用标准 `&`；逗号、分号、方括号很难被识别为分隔符。
- 路径式筛选（`/products/fish/green/tiny/`）保持筛选顺序固定、不出现重复筛选。
- 无结果、重复或无意义的组合，以及不存在的分页号，在原 URL 返回 404；不要重定向到通用错误页（SPA 可能做不到）。
- canonical 指向不带筛选的版本、指向筛选页的锚点加 `rel="nofollow"`：长期效果通常不如前两种方法；nofollow 要所有指向该 URL 的锚点都加才有效。

**哪些分面值得索引**（本套件口径：每一条「可索引」都要有搜索量或转化数据支撑；官方文档没有逐分面类型的处置表）：

| 分面类型 | 默认处置 | 理由 |
|---|---|---|
| 类目面（/shoes/） | 索引，它就是类目页本体 | 层级导航的一部分 |
| 品牌面 | 有真实搜索量时索引 | 「品牌 + 类目」查询真实存在 |
| 颜色、尺码、材质 | 不索引，robots.txt 收口 | 组合爆炸，需求零散 |
| 价格区间 | 默认不索引，有搜索量证据再放行 | 同上 |
| 排序（sort=） | 不索引 | 内容重复 |
| 库存、评价筛选 | 不索引 | 时效性强 |
| 分页 | 单独按分页处理，不套分面规则 | 见下 |

**分页交叉**：分页 URL 是发现列表后段内容的通道，不要套用分面的 robots.txt 规则。Google 不再使用 `rel="prev"/"next"`；每页自指 canonical，并用 `<a href>` 链到下一页（[Google 分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading)）。

**审计入口**：服务器日志按目录统计筛选 URL 的抓取占比（见 [log-analysis.md](log-analysis.md)）；处置优先级：robots.txt 禁抓 > canonical/nofollow。

## 面包屑：视觉与 schema 的一致性

- Google 建议面包屑写典型的用户访问路径，不必照搬 URL 层级；一个页面可以有多条路径；不必包含顶级域名一项和当前页一项（[Breadcrumb 文档](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)，核对 2026-10-21）。
- BreadcrumbList 至少 2 个 ListItem；每项必填 `name`、`position`、`item`，最后一项可以省略 `item`（Google 用当前页 URL）。面包屑富结果 2025-01-22 起只在桌面显示。
- 视觉面包屑与 BreadcrumbList 必须一致：结构化数据要与可见内容一致是 Google 的通用要求（[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)）。常见错配：schema 写了视觉上没有的中间层（模板写死）；视觉有、schema 少；多语言站 schema 没有随语言切换。
- Rich Results Test 检查的是标记能否产生富结果，不比对可见面包屑；一致性要用脚本对拍（见检查清单）。写法见 [schema-templates.md](schema-templates.md)。

## 移动导航与桌面差异检查

- Google 用智能手机版 Googlebot 抓取并索引；移动版没有的链接，Google 可能发现不了。大型站点移动版和桌面版 HTML 不同时，移动版缺少的链接会让新页面发现变慢（Google 2024-11-01 在抓取预算文档加入的最佳实践，见[文档更新记录](https://developers.google.com/search/updates)）。
- 检查法：同一 URL 分别用桌面 UA 和移动 UA 抓服务端 HTML，比较导航链接集合（UA 字符串取自 [Google 常见抓取工具](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers)）：

  ```bash
  curl -s -A "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/W.X.Y.Z Safari/537.36" URL | grep -oE 'href="[^"]+"' | sort -u > desktop.txt
  curl -s -A "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/W.X.Y.Z Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" URL | grep -oE 'href="[^"]+"' | sort -u > mobile.txt
  diff desktop.txt mobile.txt   # 差集 = 只在一端出现的链接
  ```

  有的站会拦截伪装 Googlebot 的请求，结果为空时改用普通浏览器 UA 复测。
- 高频差异：汉堡菜单删掉页脚整区或次级入口；移动模板与桌面模板分开维护后内容漂移；移动端把链接换成点击后才请求的接口。
- 移动端底部标签栏是移动专属导航：检查它与桌面主导航覆盖的重要页面是否等价。

## 内链流向的可视化审计

1. **爬取导出**：`python3 scripts/site_crawl.py example.com --out crawl.json`，再 `python3 scripts/link_graph.py --crawl crawl.json`（PageRank 近似排序、深度直方图、零入链和单入链清单）。
2. **力导向图**：Screaming Frog 的 Force-Directed Crawl Diagram 用边表示链接（按最短路径），节点随抓取深度变小变浅，可识别不可索引页占比（[官方教程](https://www.screamingfrog.co.uk/seo-spider/tutorials/site-architecture-crawl-visualisations/)，核对 2026-10-21）。
3. **Gephi 深分析**（第三方做法）：内链 CSV 导入 Gephi，看入度和模块度，找枢纽页集中度和断开的子图。
4. **判读**（本套件口径）：高价值页入链很少（权重饥饿）；成片页面深度明显偏大（导航失效）；单页入链占比畸高（常是模板或面包屑错误）。
5. **叠加日志**：把 [log-analysis.md](log-analysis.md) 的每目录抓取量叠到图上；链接流向与爬虫实际抓取不一致时，先修导航。
6. **模板链接与正文链接分开看**：如果链接几乎都来自导航和页脚模板，说明正文内链建设缺位。

## 反模式

- 导航靠图片或图标，没有文字（图片链接至少要有描述性 `alt`）。
- 同一个页面在导航中出现多个不同名称。
- 用 `#` 或 `javascript:` 作为链接地址。
- 重要页面只能通过站内搜索到达。
- 为了「传递权重」在每页页脚放大量关键词链接。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 导航在服务端 HTML 里 | `curl -s URL \| grep -o '<nav[^>]*>.*</nav>' \| grep -c 'href='`，与浏览器里看到的菜单项数对比 | 数量一致 → 通过；明显少 → 菜单靠 JS 注入，失败 |
| 链接写法 | `curl -s URL \| grep -oE '<a [^>]*href="(#\|javascript:)[^"]*"'` | 导航里无此类链接 → 通过 |
| 多个导航有名称 | 浏览器 Console：`[...document.querySelectorAll('nav')].map(n=>n.getAttribute('aria-label'))` | 每个 nav 都有可区分的名称 → 通过 |
| 移动与桌面一致 | 上文双 UA diff | 移动端不缺重要链接 → 通过 |
| 面包屑一致 | Console：比较 `[...document.querySelectorAll('nav[aria-label*=readcrumb] a, .breadcrumb a')].map(a=>a.textContent.trim())` 与 JSON-LD 里 BreadcrumbList 的 `name` 序列（选择器按站点调整） | 序列一致 → 通过 |
| 重要页入链与深度 | `link_graph.py --crawl crawl.json --json` | 重要页面不在零入链清单、深度不异常 → 通过 |
| 分面抓取 | 日志统计筛选参数 URL 的 Googlebot 抓取占比；`python3 scripts/log_session.py --log access.log --window 30m` 看参数循环 | 占比稳定且无参数循环 → 通过 |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/site-architecture/references/navigation-patterns.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/site-architecture/references/navigation-patterns.md)（MIT）
- 一手资料（核对 2026-10-21）：[Google：链接最佳实践](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)、[JavaScript SEO 基础](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)、[分面导航抓取管理](https://developers.google.com/crawling/docs/faceted-navigation)、[分页与增量加载](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading)、[Breadcrumb 结构化数据](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)、[移动优先索引](https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing)、[Google 常见抓取工具](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers)、[文档更新记录](https://developers.google.com/search/updates)；[W3C WAI 页面区域](https://www.w3.org/WAI/tutorials/page-structure/regions/)；[Brin & Page 1998](http://infolab.stanford.edu/~backrub/google.html)。
- 工具文档：[Screaming Frog 可视化教程](https://www.screamingfrog.co.uk/seo-spider/tutorials/site-architecture-crawl-visualisations/)。
