# 语义HTML技术参考

## 适用条件

技术SEO审查或相关模板修改时按需阅读本文。不要求每个任务都做全站改版，本文也不是新的强制检查层。只核受影响模板及代表页面。调整语义结构时，不顺带改动页面的视觉、事实内容和 URL。

语义HTML用带含义的元素标出文档分区，便于浏览器和辅助技术识别结构，也便于后续维护。CSS负责视觉。没有具体语义的布局可以继续使用 `div` 和 `span`，不要一律替换。

**Google 的口径**（[生成式 AI 优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)，2026-07-10 更新，核对 2026-10-21）：语义 HTML 不要求完美，网络上多数页面本来就不是有效 HTML，Google 也能理解；但尽量使用语义 HTML 仍是好主意，它帮助读屏软件等其他用户解析和浏览页面。

## 采用要点

- 按真实含义使用 `header`、`nav`、`main`、`article`、`section`、`aside`、`footer`，并检查嵌套是否合理。
- 一个文档不得同时存在多个未设置 `hidden` 的 `main`（[WHATWG](https://html.spec.whatwg.org/multipage/grouping-content.html#the-main-element)）。用 `main` 标出主内容，并与全站重复导航区分；不要简化成「DOM 任意状态下只能有一个 `main`」。
- 标题层级应与可理解的阅读顺序一致。不要仅为了调整字号而选用 `h1` 到 `h6`。Google 的 SEO 起始指南说标题数量和顺序对搜索没有影响；「单 H1、不跳级」来自可访问性（WCAG、屏幕阅读器导航）和 Bing 的习惯，不是 Google 规则。
- 页面存在多个导航时，为各导航提供可区分的名称（W3C WAI：每个导航菜单都用标签标识）。
- 可抓取导航使用真实的 `<a href>` 和描述性锚文本；操作使用 `<button>`。Google 通常只抓取带 `href` 的 `<a>`，纯 `onclick` 不是可靠的可抓取链接（[Google 链接最佳实践](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)）。
- 参数和字段使用带表头的表格或定义列表。代码示例须保持可复制的文本。
- 图片和 3D 仅作辅助，不能独占核心正文。Google AI 功能文档的原话是「Making sure that important content is available in textual form」和「Supporting your textual content with high-quality images and videos」（核对 2026-10-21）。

## 避免误用

- 营销文章和社交帖子（例如来源中列出的 Semrush 帖子与文章）用配图对比全 `div`/`span` 与 `header`/`nav`/`main`/`footer`，主张语义HTML有助AI搜索。它们没有提供因果实验，不能当作排名因素。
- Google 文档只覆盖 Google 搜索的 AI Overviews 与 AI Mode：没有额外技术要求；重要信息须能抓取、能索引、有文本，结构化数据与可见正文一致（[Google：AI 功能](https://developers.google.com/search/docs/appearance/ai-features)）。不得外推到所有 AI 产品。
- 包一层 `section` 不会自动获得 AI 引用或排名。Schema 是另一层，与语义HTML分开核查。不得承诺引用率、排名或流量提升。

## 与 AI agent 的关系：可访问性树

- web.dev（2026-04-01）：可访问性树是浏览器原生 API，把 DOM 提炼为交互元素的角色（role）、名称（name）、状态（state），是页面的语义摘要；对 AI agent 来说，它是一张忽略 CSS 视觉噪声、只看功能的地图（[web.dev：Build agent-friendly websites](https://web.dev/articles/ai-agent-site-ux)，页面最后更新 2026-04-01，核对 2026-10-21）。
- 同一篇文章的建议：用 `<button>`、`<a>` 而不是改造过的 `<div>`/`<span>`；做不到时给元素合适的 `role` 和 `tabindex`（如 `<div role="button">`）；`<label for>` 关联输入框；避免透明覆盖层遮住可交互元素（「幽灵元素」）；可交互元素保持可见且大于 8 平方像素；布局保持稳定。
- 第三方研究方向一致：MERJ（2026-09-29）观察到 agent 读取 HTML、DOM、语义标记和可访问性树，按钮做成 `<div>` 时可访问性树只报 generic，agent 认为没有可点的东西（[MERJ](https://merj.com/blog/agent-interaction-research)）；另见 Sitebulb 同题文章（SEJ 同题文章 2026-10-21 打不开，未核）。
- 边界：这是 **agent 可用性层**，不是 Google 排名因素；与 [log-analysis](log-analysis.md) 的 agent 项、[agent-readiness](agent-readiness.md) 衔接，审计时分开报告，不混入排名承诺。

## heading 层级审计的自动化思路

背景：Siteimprove（第三方，页面标注 2026-05-14 更新，核对 2026-10-21）声称 AI 搜索按标题构建大纲树来切分和引用内容；它没有给出实验证据，只当作检查动机，不当作事实。Google 的口径见本文开头：不要求完美的语义 HTML。

1. **静态层**（curl 原始 HTML）：抽 `<h1>`–`<h6>` 序列，检查 h1 是否存在且非空、是否跳级（h2 后直接 h4）、heading 内是否嵌套交互元素。
2. **渲染层**（真实可访问性树）：Chrome DevTools 提供全页可访问性树视图（[Chrome 博客](https://developer.chrome.com/blog/full-accessibility-tree)）；脚本化用 Playwright 的 `page.ariaSnapshot()`，或 CDP 的 `Accessibility.getFullAXTree`（实验性域）。CSR 补挂的 heading、`aria-level` 与视觉层级不符、`role="heading"` 没写 `aria-level`，只在这一层暴露。注意：Playwright 1.57 已移除 `page.accessibility`（[发布说明](https://github.com/microsoft/playwright/blob/main/docs/src/release-notes-js.md)），旧的 `page.accessibility.snapshot()` 代码要改写：

   ```js
   // Playwright：从 aria 快照（YAML 文本）里抽出 heading 序列
   const yaml = await page.ariaSnapshot();
   const out = [...yaml.matchAll(/- heading "([^"]*)" \[level=(\d)\]/g)]
     .map(m => ({ name: m[1], level: Number(m[2]) }));
   // out 即渲染层大纲，与静态层序列做 diff
   ```

   快照格式见 [Playwright aria snapshots](https://playwright.dev/docs/aria-snapshots)（heading 写作 `- heading "标题" [level=1]`）。快照格式随 Playwright 版本增删附加标记（如 `ref`、`box`），先在目标版本上打印一次，再改正则。
3. 判定以**渲染层为准**；静态层与渲染层不一致时，单列为渲染时机问题（见下节）。

## ARIA 角色最小集

第一规则：能用原生 HTML 元素或属性实现语义和行为，就用原生的，不要改造元素再加 ARIA（[W3C：Using ARIA 第一规则](https://www.w3.org/TR/using-aria/#rule1)）。审计只盯一个最小集：

| role | 用在哪里 | 高频错误 |
|---|---|---|
| `button` | 操作类元素 | `div role="button"` 没有 `tabindex` 和键盘事件 |
| `link` | 导航类元素 | 用 button 做跳转（agent 不会当链接遍历） |
| `navigation`（landmark） | 每个导航区域，配 `aria-label` 区分 | 多个 nav 都没有名称 |
| `img` | 把多个元素组成的图像（如内联 SVG）当作一张图，并给可访问名称（[WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/#img)） | `alt` 与 `aria-label` 冲突；名称计算顺序是 `aria-labelledby` > `aria-label` > 原生属性（如 `alt`）> 内容（[AccName 1.2](https://www.w3.org/TR/accname-1.2/)） |
| `heading` + `aria-level` | 非原生 heading 的标题 | WAI-ARIA 1.2 规定 `role="heading"` 必须写 `aria-level` |

状态类只需两个：`aria-expanded`（可展开菜单）、`aria-current="page"`（导航当前位置）。ARIA 的完整核查归 [agent-readiness](agent-readiness.md)。

## 语义模式速查表

审计时的对照基准，右列每一项都会在可访问性树里表现为错误或缺失的 role/name：

| 场景 | 正确做法 | 高频错误 |
|---|---|---|
| 页面主内容 | 一个 `main` | 多个未设 `hidden` 的 `main`；主内容仍用 `div id="content"` |
| 站点级导航 | `nav` + `aria-label` 区分（主导航/页脚/面包屑） | 多个 `nav` 都没有名称；面包屑不标 `nav` |
| 独立成篇内容 | `article`；章节用 `section` 配 heading | 所有分区都是 `div`，靠 class 表义 |
| 侧栏相关内容 | `aside` | 与正文混在同一容器 |
| 可点击跳转 | `<a href="真实 URL">` + 描述性锚文本 | `div onclick`、`a` 无 href、`javascript:` 伪协议 |
| 页面内操作 | `<button type="button">` | `span` 加 click；用 `a` 做操作 |
| 表单字段 | `<label for>` 关联；必填用 `required` | 用 placeholder 代替 label（可访问性树里没有名称） |
| 数据表格 | `<th scope>` 表头 | 全 `td` + 视觉加粗 |
| 当前导航位置 | `aria-current="page"` | 只靠 CSS 高亮 |
| 可展开菜单 | 触发器的 `aria-expanded` 随状态切换 | 状态只存在于 JS 变量 |
| 装饰图 | `alt=""`（显式声明无意义） | 没有 alt 属性 |
| 图标按钮 | `aria-label` 给名称 | 纯图标没有任何文本替代 |

完整判据以 MDN 元素参考与 [W3C WAI 教程](https://www.w3.org/WAI/tutorials/page-structure/headings/)为准。

## React / Vue 的渲染时机陷阱

共同根因：语义结构在水合（hydration）或客户端渲染之后才出现，服务端 HTML 只是空壳或骨架。

- **React**：`hydrateRoot()` 要求客户端渲染结果与服务端 HTML 完全一致，官方要求把不一致当 bug 修；React 能从部分水合错误中恢复，但最好情况是变慢，最坏情况是事件处理器挂到错误的元素上（[react.dev：hydrateRoot](https://react.dev/reference/react-dom/client/hydrateRoot)）。纯客户端渲染的内容，Googlebot 要等渲染队列处理；不执行 JS 的爬虫看不到（[Google JavaScript SEO 基础](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)：不是所有爬虫都能运行 JavaScript）。
- **Vue**：vue-router 的 hash 模式（`#/path`）里 `#` 之后的部分不会发给服务器，官方文档写明它对 SEO 有不良影响，建议改用 HTML5 history 模式（[Vue Router](https://router.vuejs.org/guide/essentials/history-mode.html)）；Google 说明一般不支持 URL 片段，不要用片段改变页面内容，改用 History API（[Google：URL 结构](https://developers.google.com/search/docs/crawling-indexing/url-structure)，核对 2026-10-21）。解法是 Nuxt 的 SSR 或预渲染。
- 检查法：对比 `curl` 原始 HTML 与渲染后 DOM 的 `main`、`nav`、heading 序列；两者不一致时，先报渲染时机问题，再谈语义结构。

## 检查清单

只查受影响模板及代表页面，不新增机械的标签数量测试。

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| `main` 唯一 | 浏览器 Console：`document.querySelectorAll('main:not([hidden])').length` | 等于 1 → 通过 |
| 静态层 heading | `curl -s URL \| grep -oE '<h[1-6][^>]*>' ` 看序列 | 有 h1、无跳级 → 通过（本套件口径，按可访问性惯例；Google 不要求） |
| 渲染层 heading | 上文 Playwright `page.ariaSnapshot()` 脚本，与静态层 diff | 两层序列一致 → 通过；不一致 → 记渲染时机问题 |
| 可抓取 CTA | `curl -s URL \| grep -oE '<a [^>]*>' \| grep -vc 'href='` | 主要 CTA 都是带有效 `href` 的 `<a>` → 通过 |
| 操作元素 | DevTools → Elements → Accessibility 面板，逐个看按钮的 role 和 name | 都是 `button` 且有名称 → 通过；显示 generic → 失败 |
| 多个导航有名称 | Console：`[...document.querySelectorAll('nav')].map(n=>n.getAttribute('aria-label'))` | 每个都有可区分名称 → 通过 |
| 语义比值（参考项） | `python3 scripts/site_audit.py URL --json`，读 `ai_search_health.semantic_ratio` 与 rendering 检查项 | 比值 = 语义标签数 ÷ 非语义标签数；<10% 只记提示（阈值是套件自定，官方未公开）；CSR 空挂载点 → 优先修 |
| 多语言 | 每个语言版本各抽一页重复以上检查 | 各语言结构一致 → 通过 |

## 来源与局限

技术判据以 MDN、WHATWG、W3C 与 Google 文档为准（核对 2026-10-21）。Semrush、SEJ、Sitebulb、MERJ、Siteimprove 材料是第三方观察，只说明话题来由，不构成效果证据。本文为 EveryInfra 自行编写，未复制下列资料的原文。相关证据边界见 [现有GEO证据边界](../content/geo-evidence.md)。

- 一手：[WHATWG：main 元素](https://html.spec.whatwg.org/multipage/grouping-content.html#the-main-element)、[MDN Glossary: Semantics](https://developer.mozilla.org/en-US/docs/Glossary/Semantics)、[MDN: The main element](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/main)、[Google：AI 功能](https://developers.google.com/search/docs/appearance/ai-features)、[Google：生成式 AI 优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)、[Google：链接最佳实践](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)、[Google：JavaScript SEO 基础](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)、[web.dev：Build agent-friendly websites](https://web.dev/articles/ai-agent-site-ux)（2026-04-01）、[Chrome DevTools 全页可访问性树](https://developer.chrome.com/blog/full-accessibility-tree)、[W3C：Using ARIA](https://www.w3.org/TR/using-aria/)、[WAI-ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/)、[AccName 1.2](https://www.w3.org/TR/accname-1.2/)、[W3C WAI: Headings](https://www.w3.org/WAI/tutorials/page-structure/headings/)、[react.dev：hydrateRoot](https://react.dev/reference/react-dom/client/hydrateRoot)、[Vue Router：历史模式](https://router.vuejs.org/guide/essentials/history-mode.html)、[Playwright aria snapshots](https://playwright.dev/docs/aria-snapshots)、[Playwright 发布说明](https://github.com/microsoft/playwright/blob/main/docs/src/release-notes-js.md)、[CDP Accessibility 域](https://chromedevtools.github.io/devtools-protocol/tot/Accessibility/)
- 第三方：[Semrush 帖子](https://x.com/semrush/status/2102748090071400757)（展示日期 2026-09-23）、[Semrush: What Is Semantic HTML?](https://www.semrush.com/blog/semantic-html5-guide/)（页面标注 2025-02-07）、[SEJ](https://www.searchenginejournal.com/the-accessibility-tree-is-how-ai-agents-read-your-site-its-breaking/578171/)（2026-06-24）、[Sitebulb](https://sitebulb.com/resources/guides/what-ai-agents-see-the-accessibility-tree-is-an-seo-surface/)、[MERJ](https://merj.com/blog/agent-interaction-research)（2026-09-29）、[Siteimprove](https://www.siteimprove.com/blog/heading-hierarchy-ai-extraction/)
