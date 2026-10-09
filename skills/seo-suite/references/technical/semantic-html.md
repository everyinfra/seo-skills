# 语义HTML技术参考

## 适用条件

技术SEO审查或相关模板修改时按需阅读本文。不要求每个任务都做全站改版，本文也不是新的强制检查层。只核受影响模板及代表页面。调整语义结构时，不顺带改动页面的视觉、事实内容和 URL。

语义HTML用带含义的元素标出文档分区，便于浏览器和辅助技术识别结构，也便于后续维护。CSS负责视觉。没有具体语义的布局可以继续使用 `div` 和 `span`，不要一律替换。

## 采用要点

- 按真实含义使用 `header`、`nav`、`main`、`article`、`section`、`aside`、`footer`，并检查嵌套是否合理。
- 一个文档不得同时存在多个未设置 `hidden` 的 `main`。用 `main` 标出主内容，并与全站重复导航区分；不要简化成「DOM 任意状态下只能有一个 `main`」。
- 标题层级应与可理解的阅读顺序一致。不要仅为了调整字号而选用 `h1` 到 `h6`。
- 页面存在多个导航时，为各导航提供可区分的名称。
- 可抓取导航使用真实的 `<a href>` 和描述性锚文本；操作使用 `<button>`。纯 `onclick` 不是可靠的可抓取链接。
- 参数和字段使用带表头的表格或定义列表。代码示例须保持可复制的文本。
- 图片和 3D 仅作辅助，不能独占核心正文。重要信息必须有文本形式。

## 避免误用

- 有营销文章和社交帖子（例如来源中列出的 Semrush 帖子与文章）用配图对比全 `div`/`span` 与 `header`/`nav`/`main`/`footer`，主张语义HTML有助AI搜索。它们没有提供因果实验，不能当作排名因素。
- 这类文章只说明话题的来由，技术判据不以它们为准。
- Google 文档仅覆盖 Google Search 的 AI Overviews 与 AI Mode：无额外技术要求；重要信息须能抓取、能索引、有文本，内部链接可发现，结构化数据与可见正文一致。不得外推到所有 AI 产品。
- 包一层 `section` 不会自动获得 AI 引用或排名。Schema 是另一层，与语义HTML分开核查。不得承诺引用率、排名或流量提升。

## 与 AI agent 的真实关系：可访问性树（2026-10-09 二波深化）

2026 年证据链给出的准确表述：浏览器 agent 主要消费**可访问性树**——它把 DOM 蒸馏为交互元素的角色（role）、名称（name）、状态（state），是「页面的语义摘要」（web.dev 2026-04 官方文章）。agent 以它为「高保真地图，忽略 CSS 视觉噪声、聚焦纯功能」。行业侧：SEJ 2026-06「可访问性树是 AI agent 阅读网站的方式（且正在失效）」；Sitebulb 2026-06 将其称为「agent 时代的 SEO surface」；merj 2026-09 的 agent 交互研究列出 agent 消费的四层：HTML、DOM、语义标记、可访问性树。

落到语义HTML的含义：
- **native 元素是可访问性树的地基**——真实 `<button>`/`<a href>` 自带 role 与 name；`<div onclick>` 在树中不出现为可交互节点。web.dev 明确建议用真实元素，不得已时才补 `role` + `tabindex`。
- `<label for>` 让 agent（与读屏用户）知道字段用途；「幽灵元素」（透明遮盖真实控件的叠层）会从树中隐藏交互目标，属反模式。
- 边界不变：这是 **agent 可用性层**，不是 Google 排名因素；与 [log-analysis](log-analysis.md) 的「agent 项」、[agent-readiness](agent-readiness.md) 同层衔接，审计时分开报告，不得混入排名承诺。

## heading 层级审计的自动化思路（2026-10-09 二波深化）

背景：AI 内容抽取按 heading 构建 outline 树（H1 为顶、H2 为枝、H3 为叶——Siteimprove 2026-05），heading 结构因此是机器可读性的核心指标之一。自动化两层对照：

1. **静态层**（curl 原始 HTML）：正则/解析器抽 `<h1>`–`<h6>` 序列，检查——h1 唯一且非空；无跳级（h2 直接跟 h4）；heading 不含嵌套交互元素。
2. **渲染层**（真实可访问性树）：Chrome DevTools 已提供全页可访问性树视图（developer.chrome.com 2021-12）；脚本化用 Playwright/Puppeteer 的 a11y snapshot 或 CDP `Accessibility.getFullAXTree`，比对 role=heading 节点的层级与静态层是否一致——CSR 补挂的 heading、`aria-level` 与视觉层级不符、`role="heading"` 无 `aria-level` 都只在此层暴露。Heading Inspector 扩展即按「Chrome 真实可访问性树」渲染 outline，在线工具（heading checker 类）可查跳级/空 heading/ARIA heading。
   渲染层抽取骨架（Playwright）：
   ```js
   const snap = await page.accessibility.snapshot();
   const out = [];
   (function walk(n) {
     if (n.role === 'heading') out.push({ level: n.level, name: n.name });
     (n.children || []).forEach(walk);
   })(snap);
   // out 即渲染层 outline，与静态层序列 diff
   ```
3. 判定以**渲染层为准**（与「相称验收」一致），静态层差异单列为渲染时机问题（见下节）。

## ARIA 角色最小集（2026-10-09 二波深化）

第一规则：**能原生就不 ARIA**（WAI-ARIA Authoring Practices）。审计只需要盯一个最小集，其余交给 native HTML：

| role | 该出现在什么上 | 高频错误 |
|---|---|---|
| `button` | 操作类元素 | `div role="button"` 无 tabindex/键盘事件——比不标更误导 |
| `link` | 导航类元素 | 用 button 语义做跳转（agent 不会当链接遍历） |
| `navigation`（landmark） | 每个导航区域，配 `aria-label` 区分「主导航/页脚」 | 多个 nav 全部无名 |
| `img` | 有含义的装饰性替代 | `alt` 与 `aria-label` 打架（name 计算顺序：`aria-labelledby` > `aria-label` > 内容） |
| `heading` + `aria-level` | 非原生 heading 的标题 | 缺 `aria-level` 则层级丢失 |

状态类只需两个：`aria-expanded`（可展开菜单）、`aria-current="page"`（导航当前位置）。ARIA 良构的完整核查归 [agent-readiness](agent-readiness.md)，本文只保底这个最小集。

## 语义模式速查表（2026-10-09 二波深化）

审计时的对照基准——右列的每一项都会在可访问性树里表现为「错误或缺失的 role/name」：

| 场景 | 正确做法 | 高频错误 |
|---|---|---|
| 页面主内容 | 一个 `main`（ landmarks 语义） | 多个未设 `hidden` 的 `main`；主内容仍用 `div id="content"` |
| 站点级导航 | `nav` + `aria-label` 区分（主导航/页脚/面包屑各一个） | 三个 `nav` 全无名；面包屑不标 `nav` |
| 独立成篇内容 | `article`；章节用 `section` 配 heading | 所有分区都是 `div`，靠 class 表义 |
| 侧栏相关内容 | `aside` | 与正文混在同一容器，树中无从区分 |
| 可点击跳转 | `<a href="真实 URL">` 描述性锚文本 | `div onclick`、`a` 无 href、`javascript:` 伪协议 |
| 页面内操作 | `<button type="button">` | `span` 加 click；用 `a` 做操作（agent 会当链接遍历） |
| 表单字段 | `<label for>` 关联；必填用 `required` | placeholder 代替 label（树中无名） |
| 数据表格 | `<th scope>` 表头 | 全 `td` + 视觉加粗 |
| 当前导航位置 | `aria-current="page"` | 只靠 CSS 高亮（视觉信息树中不可见） |
| 可展开菜单 | 触发器 `aria-expanded` 随状态切换 | 状态只存在于 JS 变量里 |
| 装饰图 | `alt=""`（空 alt，显式声明无义） | 无 alt 属性（name 缺失，agent 猜） |
| 图标按钮 | `aria-label` 给名称 | 纯图标无任何文本替代 |

速查表只覆盖审计高频项；完整语义判据仍以 MDN 元素参考与 [WAI 教程](https://www.w3.org/WAI/tutorials/page-structure/headings/)为准。

## React / Vue 的渲染时机陷阱（2026-10-09 二波深化）

共同根因：**语义结构在水合（hydration）之后才生成**——服务端 HTML 是空壳或骨架，语义标签与 heading 在客户端 JS 执行后才出现。

- **React**：水合不匹配（React 18「Hydration failed because the initial UI does not match」）会让整棵子树客户端重渲——语义结构出现更晚且闪变；纯 CSR 内容 Google 需二波渲染队列，不渲染的爬虫（多数 AI 爬虫）完全看不见（Google 论坛 CSR 收录案例；makersden 2025-11 SSR/Server Components 实操；guangsuan 2026-09 Vue/React 渲染陷阱对照）。
- **Vue**：默认输出 CSR 单页应用；vue-router 用 **hash 模式**（`#/path`）时 `#` 后部分不被当独立 URL——整站对搜索引擎只是一个 URL（nadiamohamed 2026-08 Vue SEO）；大站（10 万页级）纯 CSR 的抓取/收录问题复合（TechSEO 社区共识）；解法是 Nuxt 的 SSR/预渲染，降低对客户端 JS 的依赖（nuxtseo）。
- 检查法（对应「相称验收」）：对比 `curl` 原始 HTML 与渲染后 DOM 的 `main`/`nav`/heading 序列；两者不一致时先报渲染时机问题，再谈语义结构。


## 相称验收

- 以实际渲染的 DOM 和辅助技术可访问结构为准，并检查键盘与移动端阅读顺序。
- 核对可抓取 CTA 是否使用带有效 `href` 的链接，操作是否使用 `<button>`。
- 核对服务端渲染（SSR）输出与可索引内容是否一致。页面有多语言版本时，逐语言核对应文案。
- 只查受影响模板及代表页面，不新增机械标签数量测试。

## 来源与局限

一手依据检查时间为 2026-09-24。技术判据以 MDN 与 Google 文档为准。Semrush 材料只说明本参考的来由，不构成效果证据；社交帖子的展示日期与文章页面标注日期不同，不要混用。本文为 EveryInfra 自行编写，未复制下列资料的原文。相关证据边界见 [现有GEO证据边界](../content/geo-evidence.md)。

- [MDN Glossary: Semantics](https://developer.mozilla.org/en-US/docs/Glossary/Semantics)
- [MDN: The main element](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/main)
- [Google: AI features](https://developers.google.com/search/docs/appearance/ai-features)
- [Google: Crawlable links](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)
- [Semrush 帖子](https://x.com/semrush/status/2102748090071400757)（展示日期 2026-09-23）
- [Semrush: What Is Semantic HTML? And How to Use It Correctly](https://www.semrush.com/blog/semantic-html5-guide/)（页面标注 2025-02-07）

二波深化新增（检查时间 2026-10-09）：

- [web.dev: Build agent-friendly websites](https://web.dev/articles/ai-agent-site-ux)（2026-04-01）——可访问性树=role/name/state 摘要、native 元素优先、幽灵元素反模式
- [Search Engine Journal: The Accessibility Tree Is How AI Agents Read Your Site](https://www.searchenginejournal.com/the-accessibility-tree-is-how-ai-agents-read-your-site-its-breaking/578171/)（2026-06-24）；[Sitebulb 同题指南](https://sitebulb.com/resources/guides/what-ai-agents-see-the-accessibility-tree-is-an-seo-surface/)（2026-06-23）；[merj: agent 交互研究](https://merj.com/blog/agent-interaction-research)（2026-09-29）
- [Siteimprove: Headings and AI extraction](https://www.siteimprove.com/blog/heading-hierarchy-ai-extraction/)（2026-05-14）——AI 按 heading 建 outline 树
- [Chrome DevTools 全页可访问性树](https://developer.chrome.com/blog/full-accessibility-tree)（2021-12，官方）；[W3C WAI: Headings](https://www.w3.org/WAI/tutorials/page-structure/headings/)
- React：[makersden: SEO-friendly React SSR](https://makersden.io/blog/seo-friendly-react-leverage-server-components-server-ssr)（2025-11）、[React 18 水合不匹配](https://stackoverflow.com/questions/71706064/)；Vue：[Vue SEO 渲染与路由](https://nadiamohamed.me/insights/vue-seo/)（2026-08）、[nuxtseo: SPA vs SSR](https://nuxtseo.com/learn-seo/vue/spa)、[guangsuan: Vue/React 渲染陷阱](https://www.guangsuan.com/en/post/javascript-rendering-seo-traps-vue-react-site-crawler/)（2026-09-27）
