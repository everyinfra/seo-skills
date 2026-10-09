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

## 大型下拉菜单与爬虫预算（2026-10-09 二波深化）

- **链接数量级问题**：实例口径——大型 mega menu 120 条 + 正文内链 15 条 + 页脚 10 条 = 单页 145 条内链（MagsTags 2026-03 测算）；社区经验值约 100 条之后的链接收益递减（r/TechSEO 讨论），千页级站点曾见单页 1500+ 内链的失控案例（webmasters.SE）。权重按链接数分摊，单页链接越多、每条分得越少。
- **全站复制放大**：mega menu 是全站模板——每页都背上全部链接。好处是二级类目全站可达（点击深度恒为 1），代价是核心正文内链被稀释、爬虫每页都要重新面对同一批 URL。
- **JS 展开陷阱**：下拉项只在 hover/click 后由 JS 注入 DOM 的写法，依赖渲染队列才可见（Google JavaScript SEO 基础）；正确做法是全部链接在服务端 HTML 中、仅用 CSS 控制显隐——CSS 隐藏的链接仍可被抓取。
- **收口方法**：(1) 分层——顶部只留一级类目，二级下沉到类目页与页脚精简区；(2) 用日志/点击数据验证菜单项真实被用（绝大多数点击集中在头部 10 项——Ideawrights 长期观察）；(3) 无数据支撑的「SEO 链接」直接删。

## 分面导航（faceted navigation）SEO 深度（2026-10-09 二波深化）

分面（筛选）导航按参数组合展开 URL 空间，是索引膨胀与抓取预算浪费的最大单一来源（Google 官方 faceted 文档，2025-12 更新版）。与 [redirects-canonical.md](redirects-canonical.md) 交叉——那里管规则层，这里只管导航层。官方二选一路径：

**路径一：筛选 URL 不需要索引（多数电商默认）→ robots.txt 阻断抓取**
```
User-agent: Googlebot
Disallow: /*?*color=
Disallow: /*?*size=
Allow: /*?products=all$      # 白名单例外：全量列表页
```
官方明示：筛选结果「通常没必要允许抓取，白白消耗服务器资源」。

**路径二：确有价值组合需要索引 → 官方细则**
- canonical 从筛选变体指向未筛选版（?color=green → ?products=fish）。
- 指向筛选页的锚点可加 `rel="nofollow"`——但**每个**指向该 URL 的锚点都要带才有效，且官方直言此法「长期普遍低效」。
- 无结果组合（重复筛选、无意义组合、不存在的分页号）**在原 URL 返回 404**，不要重定向到通用错误页（SPA 例外，按 SPA 最佳实践处理）。
- URL 工程规范：参数分隔符用标准 `&`（逗号/分号/方括号难被识别为分隔符）；路径式筛选（/products/fish/green/tiny/）保持筛选顺序恒定、不重复筛选。
- 另一官方选项：用 URL 片段（`#products=fish`）替代 query——Google 通常不支持片段抓取，因此片段方案对抓取无影响（双刃：也不会产生新 URL 空间）。

**哪些分面值得索引（决策表，行业共识口径）**：

| 分面类型 | 默认处置 | 依据 |
|---|---|---|
| 类目面（/shoes/） | 索引——它就是类目页本体 | 层级导航的一部分 |
| 品牌面 | 常可索引（有真实搜索量） | 「brand + 类目」查询真实存在 |
| 颜色/尺码/材质 | 不索引，robots.txt 收口 | 长尾组合爆炸，需求零散 |
| 价格区间 | 默认不索引，有搜索量证据再单独放行 | 同上 |
| 排序（sort=） | 一律不索引 | 内容重复，零增量 |
| 库存/评价筛选 | 不索引 | 时效性强，组合无索引价值 |
| 分页 | 单独按分页处理，不混入分面规则 | 见下 |

（决策口径综合 Builtvisible、Oncrawl 2025-11、resignal 2025-06 的行业实操；「可索引」的每一条都应有搜索量或转化数据支撑，不是拍脑袋放行。）

**分页交叉**：分面列表的分页别套用分面 robots.txt 规则——分页 URL 是发现列表后段内容的通道；`rel="prev"/"next"` Google 已不再使用（2019 官方确认弃用），现行做法是每页自指 canonical + 完整可抓取的分页链接，细节归 [redirects-canonical.md](redirects-canonical.md)。

**底层风险**：参数组合制造「无界 URL 空间」→ 过度抓取拖慢有用新页的发现（官方口径）。审计入口=日志按目录看筛选 URL 占比（见 [log-analysis.md](log-analysis.md)）；处置优先级：robots.txt 阻断 > canonical/nofollow（低效兜底）。


## 面包屑：视觉与 schema 的一致性（2026-10-09 二波深化）

- 路径与站点层级一致：首页 › 分类 › 子分类 › 当前页。
- **视觉面包屑与 BreadcrumbList 必须逐项一致**：用户看到的路径要精确匹配 JSON-LD 结构（名称、URL、层级顺序、条数——Glukhov 2025-12 实操口径）。不一致时搜索引擎可能忽略 schema 或标记为不符特征（QuickSEO 一致性检查器即专查此项）。
- Google 官方规范要点：当前页（最后一项）在官方示例中**不带 URL**；条目用 `position` 表序；缺 `position`/`name`/`item` 必填属性则失去富结果资格（Google breadcrumb 文档）。
- 常见错配：schema 写了视觉上不存在的中间层（通常是模板写死）；视觉有、schema 少；最后一项 schema 指向自身（同本文反模式「最后一项做成链接」的 schema 版）；多语言站 schema 未随语言切换（schema 是英文名、页面是中文面包屑）。
- 校验：Rich Results Test 只验语法，**不验与可见路径的一致性**——一致性要人工或脚本对拍（DOM 抽 `.breadcrumb` 文本序列 vs JSON-LD `name` 序列）。写法见 [schema-templates.md](schema-templates.md)。

## 移动导航与桌面差异检查（2026-10-09 二波深化）

- 前提：Google 用**智能手机 Googlebot 抓取并索引**（移动优先索引，官方文档）——移动端没有的链接，等于对索引器不存在。
- 检查法：同一 URL 分别用桌面 UA 与移动 UA 抓服务端 HTML，diff 导航链接集合；或用爬虫工具的设备仿真跑两遍对比（Screaming Frog/Sitebulb 均支持）。
  ```bash
  curl -s -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" URL | grep -oE 'href="[^"]+"' | sort -u > desktop.txt
  curl -s -A "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/W.X.Y.Z Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" URL | grep -oE 'href="[^"]+"' | sort -u > mobile.txt
  diff desktop.txt mobile.txt   # 差集=移动端缺失（或桌面缺失）的导航链接
  ```
- 高频差异：汉堡菜单为省屏幕删掉页脚整区或次级入口；移动模板与桌面模板分库维护后漂移；移动端把链接换成「点击展开后才请求」的懒加载接口。
- 移动端独有项：底部 tab 栏通常是移动专属导航——检查它与桌面主导航指向的重要页面集合是否等价，别让「移动才有的入口」变成桌面版永远给不出内链的孤儿。
- CSS 隐藏（`display:none` 的菜单项）仍会被抓取——可接受；**JS 点击后才注入 DOM** 依赖渲染，不可靠——不可接受。

## 内链权重流向的可视化审计（2026-10-09 二波深化）

目的：把「权重往哪流」从直觉变成图。方法链：

1. **爬取导出**：全站爬虫导出全部内链（Screaming Frog 的 inlinks/all inlinks 报告）。
2. **力导向图**：Screaming Frog 内置 Force-Directed Crawl Diagram——节点按入链聚合大小，直接暴露孤立簇与深度异常（官方教程）。
3. **Gephi 深分析**：内链 CSV 导入 Gephi，跑布局算法+入度/模块度指标——识别枢纽页集中度、切断的子图（Tahay Yelkenci / vmali 实操）。
4. **判读**：高价值页入链 <2（权重饥饿）；点击深度 >4 的成片区域（导航失效）；单页入链占比畸高（权重黑洞，常是首页自我引用或面包屑错误）。
5. **叠加日志**：把 [log-analysis.md](log-analysis.md) 的每目录抓取量叠到图上——权重流向与爬虫实际注意力不一致时，先修导航再谈内容。
6. **模板链接与正文链接分色**：可视化时把导航/页脚模板链接与正文上下文链接区分渲染——权重若几乎全走模板层，说明正文内链建设缺位，导航再优化也补不回来。

## 反模式

- 导航靠图片或图标，没有文字。
- 同一个页面在导航中出现多个不同名称。
- 用 `#` 或 `javascript:` 作为链接地址。
- 重要页面只能通过站内搜索到达。
- 为了「传递权重」在每页页脚放大量关键词链接。

## 检查方法

1. 查看服务端返回的 HTML（不执行 JS），确认导航链接存在且有 `href`。
2. 用爬虫工具导出内链数据，看重要页面的入链数量和点击深度。
3. 在手机视口下检查菜单中的链接是否与桌面一致；UA 分身抓两遍 diff 链接集合更严（见「移动导航与桌面差异检查」节）。
4. 面包屑：脚本对拍 DOM 可见文本序列与 JSON-LD `name` 序列（Rich Results Test 只验语法不验一致性）。
5. 分面导航：日志按目录算筛选 URL 抓取占比，决定 robots.txt 收口范围（见「分面导航」节）。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/site-architecture/references/navigation-patterns.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/site-architecture/references/navigation-patterns.md)（MIT）
- 一手资料：[Google：可抓取链接与锚文本](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)、[Google：Breadcrumb 结构化数据](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)、[Google：JavaScript SEO 基础](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)
- 二波深化新增（检查时间 2026-10-09）：
  - [Google：分面导航抓取管理](https://developers.google.com/crawling/docs/faceted-navigation)（2025-12 更新）——robots.txt 阻断/白名单、canonical、nofollow 全锚点要求、无结果组合返 404、`&` 分隔符、片段方案；2024-12 官方更新背景：[Boulder SEO Marketing 六步清单](https://boulderseomarketing.com/faceted-navigation-crawl-budget-fix/)（2026-03）
  - mega menu 链接量级与稀释：[MagsTags 测算](https://www.magstags.com/notes/mega-menus-seo/)（2026-03）、[r/TechSEO 讨论](https://www.reddit.com/r/TechSEO/comments/1hx8gye/can_mega_menus_negatively_affect_google_rankings/)、[webmasters.SE 1500 链接案例](https://webmasters.stackexchange.com/questions/81887/)、[Ideawrights 点击集中观察](https://ideawrights.com/mega-menus-and-seo/)、[Digital Applied 内链指南](https://www.digitalapplied.com/blog/internal-linking-strategy-2026-large-site-architecture-guide)（2026-05）
  - 分面索引决策口径：[Builtvisible 分面实操](https://builtvisible.com/faceted-navigation-seo-best-practices/)、[Oncrawl 规模化分面管理](https://www.oncrawl.com/technical-seo/managing-faceted-navigation-scale/)（2025-11）、[resignal 电商分面](https://resignal.com/blog/seo-friendly-faceted-navigation-to-avoid-crawl-efficiency-or-creating-index-bloat/)（2025-06）；`rel=prev/next` 弃用：Google 2019-03 官方公告
  - 面包屑一致性：[Glukhov 实操](https://www.glukhov.org/post/2025/12/breadcrumbs-for-seo/)（2025-12）、[QuickSEO 一致性检查器](https://quickseo.ai/tools/breadcrumb-consistency-checker)
  - 可视化审计：[Screaming Frog 官方 Force-Directed 教程](https://www.screamingfrog.co.uk/seo-spider/tutorials/site-architecture-crawl-visualisations/)、[SF+Gephi 实操](https://tahayelkenci.com/blog/site-architecture-with-screaming-frog-and-gephi/)、[vmali Gephi 内链分析](https://www.vmali.fr/visualizing-website-structure-analyzing-internal-links-with-gephi/)
  - 移动优先索引官方口径：[Google: Mobile-first indexing best practices](https://developers.google.com/search/docs/crawling-indexing/mobile-first-indexing)（双 UA diff 的方法基础）
