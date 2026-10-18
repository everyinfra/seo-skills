# HTML head 元素参考（2026 口径）

> 建立于 2026-10-09，2026-10-18 逐条核对一手来源。元素清单参考 joshbuchea/HEAD（第三方，CC0，commit `de1304e`，2026-05-02 UTC）及其 DEPRECATED.md；HEAD 的说法只当线索，结论以 WHATWG HTML 标准、Google Search Central 和各平台官方文档为准。`<title>`/description 的写法见 [meta-tag-formulas.md](../content/meta-tag-formulas.md)；JS 注入 meta 的风险见 [rendering-seo.md](rendering-seo.md)；结构化数据见 [schema-templates.md](schema-templates.md)。

## 用途与何时读

审计或编写页面 `<head>`、组装分享卡片、排查微信/QQ 分享问题、清理旧标签时读。先看第一节的硬约束：只有这几条会影响搜索引擎读取。其余多为风格或平台兼容问题，不要报成 SEO 错误。

## 一、会影响搜索引擎读取的硬约束

| 约束 | 一手依据 | 违反后果 |
|---|---|---|
| 字符编码声明（`<meta charset>`）必须完整落在文档前 1024 字节内 | [WHATWG：字符编码声明](https://html.spec.whatwg.org/multipage/semantics.html#charset)（核对 2026-10-18） | 浏览器和爬虫可能按错误编码解析，中文乱码 |
| `rel="canonical"` 只在 `<head>` 内才被 Google 接受；`<head>` 至少要是有效 HTML | [Google：规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)（核对 2026-10-18） | `<head>` 里先出现 `<img>`、`<iframe>`、`<div>` 等非元数据元素时，解析器会提前结束 head，之后的 canonical/hreflang 落进 body，Google 不采纳 |
| canonical 用绝对 URL | 同上（"Use absolute paths rather than relative paths"） | 相对路径易拼错 |
| `meta http-equiv="Content-Security-Policy"` 必须是 head 的子元素；它不保证拦住已经发起的请求 | [WHATWG：CSP pragma](https://html.spec.whatwg.org/multipage/semantics.html#attr-meta-http-equiv-content-security-policy)（核对 2026-10-18） | 放得太晚，前面的资源不受约束 |
| head 内的 metadata 元素只有 8 种：`base`、`link`、`meta`、`noscript`、`script`、`style`、`template`、`title` | [WHATWG：Metadata content](https://html.spec.whatwg.org/multipage/dom.html#metadata-content-2)（核对 2026-10-18；HEAD 写「7 个」漏了 `template`） | 其他元素会让 head 提前结束 |

Google 对 robots meta 不强制位置：放在 body 里也会遵守（[Google：robots meta](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)，核对 2026-10-18）。

## 二、推荐顺序（风格建议，无 SEO 影响）

HEAD 仓库建议的顺序如下。这是性能和可读性的风格建议。核对了 Google 的 meta 标签、robots meta、canonical 三份文档，没有任何一份说 head 内元素顺序会影响收录或排名（核对 2026-10-18）。审计时只把第一节的硬约束报成问题；顺序差异最多记 Info。

1. `<meta charset>`（硬约束：前 1024 字节内）
2. `<meta name="viewport">`
3. `<title>`
4. 其他 `<meta>`（description、robots 等）
5. Open Graph 等社交 meta
6. `<link rel="canonical">` 等 link（不含样式表与资源提示）
7. `<link rel="preconnect">` / `dns-prefetch`
8. `<link rel="stylesheet">`
9. `<link rel="icon">`
10. `<script>`（尽量 `defer` 或 `async`）

## 三、最小集

```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page Title</title>
```

Google 把 viewport 标签的存在视为页面适配移动端的信号（[Google 支持的 meta 标签](https://developers.google.com/search/docs/crawling-indexing/special-tags)，核对 2026-10-18）。

## 四、meta 速查

**Google 支持的 meta**（以 [Google 支持的 meta 标签](https://developers.google.com/search/docs/crawling-indexing/special-tags) 为准，核对 2026-10-18）：

| 标签 | Google 的用法 |
|---|---|
| `<meta name="description">` | 有时用于搜索结果摘要。Google 不限长度，按设备宽度截断（[摘要文档](https://developers.google.com/search/docs/appearance/snippet)）；写法见 meta-tag-formulas.md |
| `<meta name="robots">` / `googlebot` | 控制抓取与索引；`robots` 适用所有搜索引擎，`googlebot` 只对 Google；冲突时取更严的一条；默认 `index, follow`，不必写 |
| `<meta name="googlebot" content="notranslate">` | 不在搜索结果里提供翻译版标题与摘要。浏览器侧禁止翻译用 HTML 标准的 `translate="no"` 属性（[WHATWG](https://html.spec.whatwg.org/multipage/dom.html#attr-translate)） |
| `<meta name="google" content="nopagereadaloud">` | 禁止 Google 朗读服务读本页 |
| `<meta name="google-site-verification">` | Search Console 验证；值区分大小写 |
| `<meta charset>` / `http-equiv="Content-Type"` | 字符集；Google 建议 UTF-8 |
| `<meta http-equiv="refresh">` | Google 能处理，但建议改用服务端 301 |
| `<meta name="viewport">` | 移动端适配信号 |
| `<meta name="rating" content="adult">` | 标记成人内容供 SafeSearch 过滤；Google 只认 `adult` 和 RTA 标签值。HEAD 示例里的 `content="General"` 对 Google 无作用 |

**Google 明确不用**：`meta keywords`、`lang` 属性（Google 按正文判断语言）、`rel="next"/"prev"`、`<meta name="google" content="nositelinkssearchbox">`（站点链接搜索框 2024-11-21 起停展，该规则 2024-11-29 归档）。其他 Google 不支持的 meta 会被忽略。

**HTML 标准里的其他 metadata 名**（[WHATWG 标准 metadata 名](https://html.spec.whatwg.org/multipage/semantics.html#standard-metadata-names)）：`application-name`（仅 Web 应用使用）、`author`、`generator`、`referrer`、`theme-color`、`color-scheme`。`theme-color` 的浏览器支持：Safari 15+ 支持，Chrome 部分支持，Firefox 不支持（[MDN 兼容数据](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/name/theme-color) v8.1.6，核对 2026-10-18）。

**其他平台**：`msvalidate.01`（Bing 验证）、`yandex-verification`、`p:domain_verify`（Pinterest）按需写；`<meta name="format-detection" content="telephone=no">` 关闭 iOS Safari 的电话号码自动识别（[Apple Safari HTML 参考](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariHTMLRef/Articles/MetaTags.html)，存档文档）。`subject`、`rating=General` 等没有已知消费方，不写。

## 五、link 速查

| 关系 | 用途 | 依据与备注 |
|---|---|---|
| `canonical` | 声明首选网址 | Google：强信号，不是指令；绝对 URL；只在 head 内有效 |
| `alternate` + `hreflang` | 其他语言版本 | 每个语言版本单独一个 `<link>`，不能合并写在一个标签里（Google 2024-06-12 文档更新）；校验见 [hreflang-validation.md](hreflang-validation.md) |
| `manifest` | Web App Manifest | PWA 元数据首选这里 |
| `icon` / `apple-touch-icon` | 图标 | 见第七节 |
| `preload` | 预加载关键资源 | 要写 `as`；Chrome 50+、Safari 11.1+、Firefox 85+（MDN 兼容数据） |
| `preconnect` / `dns-prefetch` | 提前建连 | 只给真正要用的第三方源 |
| `alternate` type=rss/atom | 订阅源 | |
| `me` / `webmention` / `micropub` | IndieWeb 身份与端点 | 与 SEO 无关 |
| `search` | OpenSearch 描述文档 | `application/opensearchdescription+xml` |
| `next` / `prev` | 分页关系 | Google 不再使用；分页做法见 [link-architecture-patterns.md](link-architecture-patterns.md) |
| `amphtml` | 指向配对的 AMP 版本 | Google 仍索引 AMP，AMP 页与普通页按同一标准排名（[Google AMP 文档](https://developers.google.com/search/docs/crawling-indexing/amp)，2026-07-01 更新）；不是「已弃用」，见第十三节 |

## 六、script 加载语义

| 写法 | 行为（[WHATWG script](https://html.spec.whatwg.org/multipage/scripting.html#the-script-element)） |
|---|---|
| `<script src>` | 阻塞解析，取回并执行后才继续 |
| `<script async src>` | 并行取回，取回后立即执行 |
| `<script defer src>` | 并行取回，解析完成后按文档顺序执行 |
| `type="module"` | 默认按 defer 方式执行 |

第三方脚本可加 SRI：`integrity="sha384-…"` 加 `crossorigin`。

## 七、图标

```html
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="apple-touch-icon" href="/apple-touch-icon.png" sizes="180x180">
```

Google 搜索结果里的 favicon（[Google favicon 文档](https://developers.google.com/search/docs/appearance/favicon-in-search)，2026-08-28 更新，核对 2026-10-18）：

- 支持的 `rel`：`icon`、`shortcut icon`、`apple-touch-icon`、`apple-touch-icon-precomposed`。
- 正方形（1:1），至少 8×8px，建议大于 48×48px。
- 格式只支持 BMP、GIF、ICO、PNG、JPEG、PPM、TIFF。列表里没有 SVG 和 WebP：只放 SVG 图标的站要再给一个 PNG 或 ICO。
- 一个主机名只有一个 favicon；子目录不能单独设置。
- Googlebot-Image 要能抓图标，Googlebot 要能抓首页；图标 URL 保持稳定。

Apple 文档列出的 iPhone 高清图标尺寸是 180×180；页面没写 link 时，iOS 会去站点根目录找 `apple-touch-icon.png`（[Apple：Configuring Web Applications](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html)，存档文档）。

## 八、Open Graph 与分享卡片

Open Graph 协议规定每页四个必填属性：`og:title`、`og:type`、`og:image`、`og:url`；写了 `og:image` 就应同时写 `og:image:alt`（[ogp.me](https://ogp.me/)，核对 2026-10-18）。

```html
<meta property="og:title" content="Content Title">
<meta property="og:type" content="website">
<meta property="og:image" content="https://example.com/image.jpg">
<meta property="og:image:alt" content="A description of what is in the image (not a caption)">
<meta property="og:url" content="https://example.com/page.html">
<meta property="og:description" content="Description Here">
<meta property="og:site_name" content="Site Name">
<meta property="og:locale" content="en_US">
```

各平台怎么读（只列有官方出处的）：

| 平台 | 读法 | 依据 |
|---|---|---|
| Facebook | OG；`fb:app_id` 仍列在基础标签里，用 Facebook Insights 时必须加 | [Meta：Sharing for Webmasters](https://developers.facebook.com/docs/sharing/webmasters/)（2026-06-30 更新）；用 Sharing Debugger 验证 |
| X | 先读 `twitter:*`，没有就回落到对应 OG 属性（`og:title`/`og:description`/`og:image`/`og:image:alt`）；缺 `twitter:card` 但有 `og:type`、`og:title`、`og:description` 时可能渲染 summary 卡。`twitter:site`、`twitter:creator` 没有 OG 对应项 | X Cards markup 文档（原 URL 已跳转，读 [Wayback 2026-02-01 存档](http://web.archive.org/web/20260201012312/https://developer.x.com/en/docs/x-for-websites/cards/overview/markup)）。结论：有 OG 时 `twitter:title` 等可以省略，**不是弃用**；要大图卡写 `twitter:card=summary_large_image` |
| X 验证工具 | Card Validator 2022-08 起不再显示预览，只留日志；预览改在发帖框粘贴链接查看 | [X 开发者社区官方帖](https://devcommunity.x.com/t/card-validator-preview-removal/175006)（2022-08-02） |
| LinkedIn | 要求 `og:title`、`og:image`、`og:description`、`og:url` | [LinkedIn 帮助](https://www.linkedin.com/help/linkedin/answer/a521928)；用 Post Inspector 验证 |
| Mastodon | OG 决定预览；`fediverse:creator` 显示作者账号 | 见第十二节 |
| Google 搜索 | `og:title` 是标题链接的候选来源之一；`og:site_name` 是站点名称的参考来源；`og:image` 是搜索和 Discover 缩略图的参考来源 | [标题链接](https://developers.google.com/search/docs/appearance/title-link)、[站点名称](https://developers.google.com/search/docs/appearance/site-names)、[图片 SEO](https://developers.google.com/search/docs/appearance/google-images)（2026-03-02 更新） |

Pinterest 禁止收藏（[Pinterest 帮助](https://help.pinterest.com/en/business/article/prevent-saves-to-pinterest-from-your-site)）：

```html
<meta name="pinterest" content="nopin" description="Sorry, you can't save from my website!">
```

oEmbed 发现端点（[oembed.com](https://oembed.com/)）：

```html
<link rel="alternate" type="application/json+oembed" href="https://example.com/services/oembed?url=…" title="oEmbed Profile: JSON">
```

## 九、结构化数据

Google 推荐 JSON-LD；放在 head 或 body 都可以（[Google：结构化数据简介](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)）。写法与示例见 [schema-templates.md](schema-templates.md) 和 [schema-examples.md](schema-examples.md)。`@context` 用 `https://schema.org`。

## 十、中文浏览器与分享

**手机 QQ（官方）**：腾讯移动 Web 开发平台的手机 QQ API 文档写明，`setShareInfo` 可定制分享标题、摘要、图片；「使用 meta 同样可以达到该接口的作用」（[手机 QQ API · setShareInfo](https://open.mobile.qq.com/api/mqq/index)，核对 2026-10-18）。同页限制：分享 URL 必须与页面同域；标题最长 45 字节，摘要最长 60 字节；图片至少 200×200，否则分享到 QQ 空间时被过滤。

```html
<meta itemprop="name" content="分享标题">
<meta itemprop="image" content="https://example.com/share-200x200.png">
<meta name="description" itemprop="description" content="分享摘要">
```

**微信（官方路径是 JS-SDK）**：微信文档说明，微信内置浏览器通过 JS-SDK 等接口「设置分享内容」（[微信网页开发](https://developers.weixin.qq.com/doc/offiaccount/OA_Web_Apps/JS-SDK.html)）。JS-SDK 需要公众号和接口安全域名配置。微信不读 OG、改读上面 itemprop 三件套，是社区文章的观察，没有找到微信官方文档（**第三方观察**，核对 2026-10-18）；要稳定控制微信卡片，走 JS-SDK。

**360、QQ 浏览器（X5）、UC 的专有 meta**（`renderer`、`x5-*`、`screen-orientation`、`full-screen`、`browsermode` 等）只影响这些浏览器的显示，与搜索无关。来源是 HEAD 仓库的整理，未核对厂商当前文档；只在业务确实需要时加，并在目标浏览器里实测。

## 十一、geo meta（Google 不使用）

`ICBM`、`geo.position`、`geo.region`、`geo.placename` 不在 Google 支持的 meta 列表里；Google 忽略不支持的 meta（[Google 支持的 meta 标签](https://developers.google.com/search/docs/crawling-indexing/special-tags)，核对 2026-10-18）。缺失不是问题，不要报警告。本地业务用 LocalBusiness 结构化数据（见 [schema-templates.md](schema-templates.md)）和商家资料表达位置；geo meta 只算可选项。

## 十二、fediverse、App Links 与平台 meta

**Fediverse 作者归属**：Mastodon 读取 `fediverse:creator`，在链接预览里显示作者账号；作者要在 Mastodon 个人资料「Verification → Author attribution」里把网站域名加入允许列表（[Mastodon 官方博客](https://blog.joinmastodon.org/2024/07/highlighting-journalism-on-mastodon/)，2024-07）。

```html
<meta name="fediverse:creator" content="@handle@example.org">
```

**iOS Smart App Banner**：Apple 文档只列两个参数 `app-id` 和 `app-argument`（[Apple 文档](https://developer.apple.com/documentation/webkit/promoting-apps-with-smart-app-banners)，核对 2026-10-18）。

```html
<meta name="apple-itunes-app" content="app-id=APP_ID, app-argument=https://example.com/deep/link">
```

**App Links**（`al:ios:*`、`al:android:*`、`al:web:url`）是 Facebook 发起的深链规范；当前消费方未核，按需写。

**PWA**：应用名、独立显示模式、图标、主题色写进 `<link rel="manifest">`。`apple-touch-startup-image`、`apple-mobile-web-app-title`、`apple-mobile-web-app-status-bar-style` 是 Apple 旧机制，只作兜底。iOS 26 起，所有加到主屏幕的网站默认以 Web App 打开，不再看 meta 或 manifest（[WebKit：Safari 26.0](https://webkit.org/blog/17333/webkit-features-in-safari-26-0/)，2025-09-15）。

## 十三、可删除的旧标签（逐条核对 2026-10-18）

| 标签 | 核对结论 | 替代 |
|---|---|---|
| `<meta http-equiv="x-ua-compatible">` | IE 11 桌面应用 2022-06-15 起在部分 Windows 版本停止支持（[Microsoft](https://learn.microsoft.com/en-us/lifecycle/faq/internet-explorer-microsoft-edge)） | 删除 |
| `<meta name="msapplication-config">` + browserconfig.xml | Windows 11 不再提供动态磁贴（[Microsoft Win11 规格](https://www.microsoft.com/en-us/windows/windows-11-specifications)） | `<link rel="manifest">` |
| `<meta name="apple-mobile-web-app-capable">` | web.dev 把它列为弃用 meta，建议不用（[web.dev](https://web.dev/learn/pwa/enhancements)）；HEAD 所称「iOS 17.4 弃用」在 Safari 17.4 发布说明里查无 | manifest `display` |
| `<link rel="mask-icon">` | Safari 12 起固定标签页可用普通 favicon（第三方：[Evil Martians](https://evilmartians.com/chronicles/how-to-favicon-in-2021-six-files-that-fit-most-needs)）；HEAD 所称「Safari 17 移除 Pinned Tabs」在 Safari 17.0–17.2 发布说明里查无 | 普通 `<link rel="icon">` |
| `<link rel="prerender">` | MDN 标为弃用；Chrome 63 起只做无状态预取（MDN 兼容数据） | Speculation Rules（见 [cwv-playbook.md](cwv-playbook.md)） |
| `<link rel="chrome-webstore-item">` | 只服务于扩展内联安装；Chrome 71（2018-12）移除内联安装（[Chromium 博客](https://blog.chromium.org/2018/06/improving-extension-transparency-for.html)） | 链接到 Chrome 应用商店页面 |
| `<meta name="alexaVerifyID">` | Alexa.com 2022-05-01 关停（第三方媒体：[The Verge](https://www.theverge.com/2021/12/9/22825744/amazon-retiring-alexa-web-ranking-sevice)） | 删除 |
| `<meta name="google" content="nositelinkssearchbox">` | Google 已不再使用（见第四节） | 删除 |
| `<meta http-equiv="x-dns-prefetch-control">` | 非标准；MDN 兼容数据显示 Chrome、Firefox 支持该 HTTP 头，Safari 不支持。HEAD 所称「Chromium 从未实现」与 MDN 不符 | 需要时用 `<link rel="dns-prefetch">`；关闭预解析才用它 |
| `twitter:*` 卡片标签 | **不是弃用**：X 先读 `twitter:*`，缺失时回落 OG（见第八节） | 有 OG 时可省略重复项；`twitter:card`、`twitter:site` 按需保留 |
| `<meta property="fb:app_id">` | **不是弃用**：Meta 文档仍要求用 Facebook Insights 时添加 | 需要 Insights 就保留 |
| `<link rel="amphtml">` | **不是弃用**：Google 仍索引 AMP（见第五节） | 已有 AMP 配对就保留；新项目可不做 AMP |
| `skype_toolbar`、`twitter:dnt`、`Window-Target`、`EditURI`、`pingback`、`archives`、`index` | 未找到当前消费方的官方文档（未核） | 没有业务依赖就删除 |

## 十四、检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| charset 位置 | `curl -s URL \| head -c 1024 \| grep -io '<meta[^>]*charset'`；或 `python3 scripts/head_check.py URL` | 前 1024 字节内命中，或 HTTP 头 `Content-Type` 已带 charset → 通过；都没有 → 失败 |
| canonical 是否在 head 内被解析 | 浏览器打开页面，DevTools Console 运行 `document.querySelector('head link[rel=canonical]')`；或 Search Console 网址检查 →「查看已抓取的网页」看 HTML | 返回元素且 href 为绝对 URL → 通过；返回 `null`（被挤进 body）→ 失败，查 head 里 canonical 之前的非 metadata 元素 |
| 关键 meta 在初始 HTML | `curl -s URL \| grep -io '<title\|<meta name="description"\|<link rel="canonical"\|property="og:image"'` | 初始 HTML 里都有 → 通过；只在渲染后出现 → 失败（Google 建议尽量不用 JS 注入或修改 meta） |
| OG 必填项 | 同上 grep `og:title`、`og:type`、`og:image`、`og:url`；Facebook Sharing Debugger、LinkedIn Post Inspector 复核 | 四项齐全且 `og:image` 为可访问的绝对 URL → 通过 |
| X 卡片 | 在 X 发帖框粘贴链接，看预览 | 预览出现且标题、图片正确 → 通过；缺 `twitter:*` 但有 OG 不算失败 |
| favicon | `curl -sI 图标URL` 看状态码与 `Content-Type`；Search Console 网址检查首页 | 200、正方形、格式在 Google 支持列表内 → 通过；只有 SVG → 失败（补 PNG/ICO） |
| 旧标签 | `python3 scripts/head_check.py URL`，对照第十三节 | 命中可删项只记 Info；`twitter:*`、`fb:app_id`、`amphtml`、geo meta 缺失或存在都不算错误 |
| 中文分享 | 手机 QQ 内打开页面点分享；微信内打开看卡片 | QQ：三件套齐全且图片 ≥200×200 → 通过；微信：用 JS-SDK 时卡片按配置显示 → 通过 |

`head_check.py` 参数：`url`（也可传本地文件或 `-` 读 stdin）、`--market`、`--timeout`、`--max-bytes`；严重问题退出码 1。脚本判定与本文冲突时，以本文为准。

## 源

- 一手：[WHATWG HTML](https://html.spec.whatwg.org/multipage/)、[Google 支持的 meta 标签](https://developers.google.com/search/docs/crawling-indexing/special-tags)、[Google robots meta](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)、[Google 规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)、[Google 文档更新记录](https://developers.google.com/search/updates)、[Open Graph 协议](https://ogp.me/)、[MDN browser-compat-data](https://github.com/mdn/browser-compat-data) v8.1.6；各平台文档见正文链接。全部核对于 2026-10-18。
- 线索：[joshbuchea/HEAD](https://github.com/joshbuchea/HEAD) README.md 与 DEPRECATED.md（CC0）。
