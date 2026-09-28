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
