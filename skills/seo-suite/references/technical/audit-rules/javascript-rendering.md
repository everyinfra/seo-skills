# 审计规则目录 · JavaScript Rendering

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### JavaScript Rendering(16 条,权重 5%)

**raw-vs-rendered 实现要点已吸收于 [rendering-seo.md](../rendering-seo.md) 与 [validation-guide.md](../validation-guide.md)**(HTTP 抓原始→$;Playwright 二抓→rendered$;web-vitals 库 goto 前注入;INP 合成标记 inpSynthetic 不计分)。规则粒度(SEOmator 原版现行,多数需渲染):渲染后 DOM 里 title/description/H1/canonical 缺失或为空=fail(**JS 注入的元素算通过**);canonical 或 meta robots 的 noindex/nofollow 在源码与渲染 DOM 间不一致=fail(不比较 X-Robots-Tag);JS 事后改写 title/description/H1=warn;`js-rendered-content`(源码正文 <100 字符而渲染后 >500 字符=fail;渲染后文本多于源码 3 倍=warn);`js-rendered-links`(渲染后 `a[href]` 数超过源码 2 倍且多 10 个以上=warn);`js-blocked-resources`(只查同主机 script 是否被 `*` 组 Disallow,不查样式表、不读 Allow)=warn;SSR 检查=warn/fail;**console 未捕获异常=fail、console 错误=warn**;**子资源加载失败=warn/fail**(script/stylesheet/document/fetch/XHR 失败=fail);内联脚本用 `document.write()`=warn。site_audit 无渲染,只有 `rendering` 五项近似检查(CSR 空挂载点、noscript、JS 重量、服务端内容、H1/H2)。

**解释层(4 条;ID 未公布原文的按家族命名法推得并标 [待核];双抓实现见 [rendering-seo.md](../rendering-seo.md))**

#### js-initial-html [待核 ID]
- 名称/类型: 关键注解不在初始 HTML(本套件要求;原版对应 `js-rendered-title/description/h1/canonical`、`js-ssr-check`) —— issue · 优先级 critical · 输出 CRITICAL(title/canonical)/WARN(description/H1)
**这意味(what)**: title/canonical 等关键注解不在服务端返回的初始 HTML,要等 JS 渲染才出现。注意原版 `js-rendered-*` 查的是渲染后 DOM,JS 注入也算通过;「必须在初始 HTML」是本套件更严的口径(原稿把它写成源表分型,已更正)。
**为什么(why)**: 初始 HTML 是所有抓取方的公共层。Google 的渲染队列"may stay on this queue for a few seconds, but it can take longer"([JS SEO 文档](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics),核对 2026-10-21)。第三方研究(Vercel 与 MERJ,2024-12,样本为 nextjs.org 与两个招聘站的服务器日志):OpenAI、Anthropic、Meta、ByteDance、Perplexity 的爬虫会下载 JS 文件但不执行([文章](https://vercel.com/blog/the-rise-of-the-ai-crawler));该结论是 2024 年底的数据,需定期复测。社交预览抓取器是否执行 JS 本次未核,按「通常不执行」作工程假设。
**触发(trigger)**: 1) HTTP 抓 raw HTML;2) 检查 title/description/H1/canonical 存在性;3) 缺失再查渲染 DOM——仅渲染后存在即按上列分型触发。
**不修的条件(caveat)**: Google 终会渲染并读取 JS 注解,然而渲染延迟与非 Google 消费者的缺失是实打实的,所以一般建议 head 注解全部服务端输出。但客户端路由切换时的注解更新另归 js-meta-drift,不属本条。
**修复(fix)**: 框架切 SSR/SSG 或预渲染;至少 head 层(title/canonical/og)服务端输出;验收标准=raw HTML 即含全部关键注解。
**关联(seealso)**: js-meta-drift、js-content-dependency;[rendering-seo.md](../rendering-seo.md)、[ai-crawler-policy.md](../ai-crawler-policy.md)

#### js-meta-drift [待核 ID]
- 名称/类型: 注解在源码与渲染间漂移(源表 ID `js-canonical-mismatch`、`js-noindex-mismatch`、`js-title-modified`、`js-description-modified`、`js-h1-modified`) —— issue · 优先级 high · 输出 CRITICAL(canonical/noindex 不一致,源表 fail)/WARN(JS 改写 title/description/H1,源表 warn)
**这意味(what)**: 同一页的 canonical 或 noindex 在 raw HTML 与渲染 DOM 间不一致(如源码 noindex、渲染后被删),或 JS 事后改写 title/description/H1。
**为什么(why)**: Google 先抓原始 HTML、再排队渲染([JS SEO 文档](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics));两次读到的 canonical/noindex 不一致时以哪次为准,Google 没有公布,所以按 fail 处理;title 类改写最终值仍会被读到,影响小一档 warn。典型肇因:客户端路由器接管 head 但没与 SSR 输出对齐。
**触发(trigger)**: 双抓对比:1) canonical/noindex raw ≠ rendered 即 fail;2) title/description/H1 文本被 JS 改写即 warn。
**不修的条件(caveat)**: 修漂移不改变最终渲染值,然而它消除两阶段解读分裂,所以一般建议注解只写一次且客户端不改。但单页应用路由切换时更新 og 标签属合法客户端更新——本条只看首屏注解的稳定性。
**修复(fix)**: head 管理收敛到框架 head 组件一处;禁 JS 改写 canonical/noindex;A/B 测试不落在 head 层。
**关联(seealso)**: js-initial-html;[rendering-seo.md](../rendering-seo.md)、[head-elements.md](../head-elements.md)

#### js-content-dependency [待核 ID]
- 名称/类型: 主内容/内链依赖 JS(源表 ID `js-rendered-content`、`js-rendered-links`) —— warning · 优先级 high · 输出 WARN/CRITICAL(源表 warn/fail)
**这意味(what)**: 页面主内容或内链只存在于渲染后 DOM,raw HTML 里没有。
**为什么(why)**: 与 js-initial-html 同因不同层:注解缺失伤元数据,主内容缺失伤实体——AI 引用与社交摘要都取 raw 层,内容不在就等于对它们不存在;内链不在则按 raw 层计算的链接图(发现/权重)漏掉它们(Google 渲染后会计入,多数 AI/社交爬虫不渲染)。JS/CSS 再被 robots 挡住时问题翻倍(见 crawl-blocked-resources)。
**触发(trigger)**: 1) 源码可见文本 <100 字符而渲染后 >500 字符=fail;渲染后文本多于源码 3 倍=warn;2) 渲染后 `a[href]` 数超过源码 2 倍且多 10 个以上=warn。site_audit 近似项:`[WARN] rendering: CSR 疑似…`(空挂载点且纯文本 <200 字或文本/HTML <0.02)。
**不修的条件(caveat)**: Google 渲染能力成熟,纯 Google 视野下 JS 内容可索引,然而渲染预算与延迟真实存在、AI/社交侧多不渲染,所以一般建议主内容与核心内链服务端输出。但交互后的次级内容(评论区/展开区)客户端加载是正当形态。
**修复(fix)**: 主内容 SSR;首屏内链进模板;评论区等增强层保留客户端。
**关联(seealso)**: js-initial-html、crawl-blocked-resources;[rendering-seo.md](../rendering-seo.md)

#### js-runtime-hygiene [待核 ID]
- 名称/类型: 运行时卫生家族(源表 ID `js-console-errors`、`js-failed-requests`、`js-document-write`) —— issue/warning · 优先级 high(fail 分型)/medium · 输出 CRITICAL/WARN(源表现行:未捕获异常=fail、console 错误=warn;script/stylesheet/document/fetch/XHR 加载失败=fail;document.write()=warn)
**这意味(what)**: 渲染时 console 有未捕获异常/错误、子资源(脚本/样式/图)加载失败,或内联脚本用 document.write()。
**为什么(why)**: 未捕获异常常中断后续脚本——依赖它的注解注入/内容挂载全部静默失败,是"页面看起来正常但 SEO 层坏死"的头号原因;子资源 4xx/超时拖慢渲染且常是 CDN/版本漂移;document.write 注入的外部脚本在 2G 等慢连接上可能把主内容显示拖慢数十秒,Chrome 为此对其做过拦截干预([Chrome](https://developer.chrome.com/blog/removing-document-write),核对 2026-10-21)。
**触发(trigger)**: 渲染过程:1) console error/uncaught 非空按分型触发;2) 任一子资源网络失败按分型触发;3) 内联脚本调 document.write 即 warn。
**不修的条件(caveat)**: console 噪声本身不影响 SEO,然而它标记渲染链路断裂,所以一般建议零未捕获异常再上线。但第三方脚本(广告/统计)抛的错不在你掌控内,归类外部噪声跟踪,不必阻塞发布。
**修复(fix)**: 异常接错误监控;子资源 404 修路径/版本;document.write 全部换 DOM API 或异步注入。
**关联(seealso)**: js-initial-html;[rendering-seo.md](../rendering-seo.md)
