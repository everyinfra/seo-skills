# HTML head 元素完整参考(2026 口径)

> 建立于 2026-10-09。主体吸收自 joshbuchea/HEAD(30k★,CC0,commit `de1304e`,2026-05-01)+ 其 DEPRECATED.md,按 SEO 审计场景重组。`<title>`/description 的写法与长度见 [meta-tag-formulas.md](../content/meta-tag-formulas.md);JS 注入 meta 的红线(社交/AI 爬虫不执行 JS)见 [rendering-seo.md](rendering-seo.md);结构化数据见 [schema-templates.md](schema-templates.md)。

## 用途与何时读

审计或编写页面 `<head>`、组装分享卡片、排查中文浏览器/微信分享问题、核对弃用标签时读。合法的 head 元素共 7 个:`meta`、`link`、`title`、`style`、`script`、`noscript`、`base`。

## 一、推荐顺序(10 步)

性能与正确渲染的推荐顺序(HEAD 仓库口径):

1. `<meta charset>` — 必须出现在文档**前 1024 字节**内
2. `<meta name="viewport">` — 尽早声明,确保响应式渲染正确
3. `<title>` — 放在编码/viewport 之后,避免潜在的重渲染
4. 其他 `<meta>`(description、robots 等)
5. Open Graph / 社交 meta
6. `<link rel="canonical">` 及其他 `<link>`(**不含**样式表与资源提示)
7. `<link rel="preconnect">` / `<link rel="dns-prefetch">` — 资源提示,越早价值越大
8. `<link rel="stylesheet">` — 样式表在脚本之前
9. `<link rel="icon">` — favicon
10. `<script>` — 尽量 `defer` 或 `async`,避免阻塞渲染

```html
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <title>Page Title</title>

  <meta name="description" content="Page description">

  <meta property="og:title" content="Page Title">

  <link rel="canonical" href="https://example.com/page.html">

  <link rel="preconnect" href="https://example.com">
  <link rel="dns-prefetch" href="https://example.com">

  <link rel="stylesheet" href="styles.css">
  <link rel="icon" href="favicon.ico">

  <script defer src="script.js"></script>
</head>
```

## 二、最小集

任何网页/应用的地板配置,两个 meta 越早越好,其余元素排在它们之后:

```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page Title</title>
```

## 三、meta 全表

| 标签 | 作用 | 备注 |
|---|---|---|
| `<meta charset="utf-8">` | 字符编码 | UTF-8 是标准;前 1024 字节内 |
| `<meta name="viewport">` | 移动端视口 | `width=device-width, initial-scale=1`;刘海屏加 `viewport-fit=cover` |
| `<meta http-equiv="Content-Security-Policy">` | 控制资源加载来源 | **只对其后声明的资源生效,必须尽量早放** |
| `<meta name="application-name">` | 应用名 | 仅站点作为应用使用时写 |
| `<meta name="theme-color">` | 主题色 | Chrome/Firefox OS/Opera;manifest `theme_color` 更可移植,此标签做兜底 |
| `<meta name="color-scheme" content="light dark">` | 支持的配色方案 | light / dark / both |
| `<meta name="description">` | 页面简述 | 限 150 字符内;可能用于搜索结果摘要 |
| `<meta name="robots">` / `googlebot` | 抓取与索引控制 | 值:`index,follow` 等;后者 Google 专属 |
| `<meta name="google" content="nositelinkssearchbox">` | 关闭站点链接搜索框 | Google |
| `<meta name="google" content="notranslate">` | 禁止翻译本页 | Chrome 也消费 |
| `<meta name="google-site-verification">` | 站点验证 | Google Search Console |
| `<meta name="yandex-verification">` | 站点验证 | Yandex |
| `<meta name="msvalidate.01">` | 站点验证 | Bing |
| `<meta name="p:domain_verify">` | 站点验证 | Pinterest |
| `<meta name="norton-safeweb-site-verification">` | 站点验证 | Norton Safe Web |
| `<meta name="generator">` | 建站软件标识 | WordPress 等 |
| `<meta name="subject">` | 文档主题简述 | |
| `<meta name="rating" content="General">` | 内容年龄分级 | |
| `<meta name="referrer" content="no-referrer">` | Referrer 传递策略 | |
| `<meta name="format-detection" content="telephone=no">` | 禁止自动识别电话号码 | iOS 等 |
| geo 四件套 | 地理定位 | 见第十节 |
| `<meta name="monetization">` | Web Monetization | `$paymentpointer.example` |

参考:[Google 理解的 meta 标签](https://developers.google.com/search/docs/crawling-indexing/special-tags)、[WHATWG MetaExtensions](https://wiki.whatwg.org/wiki/MetaExtensions)。

## 四、link 速查

| 关系 | 用途 | 备注 |
|---|---|---|
| `stylesheet` | 外部样式表 | 顺序见第一节 |
| `canonical` | 声明首选网址,防重复内容 | 绝对 URL;强信号非指令 |
| `manifest` | Web App Manifest | PWA 元数据(name/icons/theme_color/display)的推荐跨平台方式 |
| `author` / `license` | 作者信息 / 版权声明 | 常指 humans.txt / copyright 页 |
| `alternate` + `hreflang` | 其他语言版本 | 校验见 [hreflang-validation.md](hreflang-validation.md) |
| `me` | RelMeAuth 分布式身份验证 | 可指 profile/mailto/sms |
| `self` | 自引用 | 文档有多引用可能时 |
| `prev` / `next` | 系列文档分页 | |
| `webmention` / `micropub` | IndieWeb 端点 | |
| `token_endpoint` / `authorization_endpoint` | IndieAuth 端点 | |
| `search` | OpenSearch 描述文档 | `application/opensearchdescription+xml` |
| `alternate` type=rss/atom | 订阅源 | |
| `dns-prefetch` / `preconnect` / `prefetch` / `preload` | 资源提示 | `preload` 须带 `as` |
| `amphtml` | AMP 版本 | **已弃用**,见第十三节 |

## 五、script 加载语义

| 写法 | 行为 |
|---|---|
| `<script src>` | 阻塞 HTML 解析与渲染,直到取回并执行 |
| `<script async src>` | 并行抓取,就绪即执行(解析完成前) |
| `<script defer src>` | 并行抓取,解析完成后按序执行 |
| `<script async defer src>` | async 优先,defer 作旧浏览器兜底 |

- 能放 `</body>` 前就放 `</body>` 前。
- SRI:`integrity="sha384-…"` 校验第三方脚本未被篡改。

## 六、图标

```html
<link rel="icon" sizes="192x192" href="/path/to/icon.png">
<link rel="apple-touch-icon" href="/path/to/apple-touch-icon.png">
```

IE10 及更早:favicon.ico 放根目录即可,无需标签。Apple Touch Icon 至少 180×180px,可直接复用 192px 图。

## 七、Open Graph 与社交平台消费矩阵

OG 标签全集:

```html
<meta property="og:url" content="https://example.com/page.html">
<meta property="og:type" content="website">
<meta property="og:title" content="Content Title">
<meta property="og:image" content="https://example.com/image.jpg">
<meta property="og:image:alt" content="A description of what is in the image (not a caption)">
<meta property="og:description" content="Description Here">
<meta property="og:site_name" content="Site Name">
<meta property="og:locale" content="en_US">
<meta property="article:author" content="">
```

OG 是分享卡片的事实标准(Facebook 原创),当前消费矩阵:

| 平台 | 消费口径 | 备注 |
|---|---|---|
| Facebook/Meta | OG 原生 | Sharing Debugger 验证 |
| X(原 Twitter) | `twitter:*` 优先,**缺省回落 OG** | 独立标签已冗余(见第十三节);仅需要 `summary_large_image` 等差异时才写 |
| LinkedIn | OG | Post Inspector 验证 |
| Discord / Slack / iMessage / WhatsApp | OG | |
| Mastodon / Bluesky | OG + `fediverse:creator` | 见第十一节 |
| Pinterest | OG | 可加 `nopin` 禁止收藏(见下) |
| 微信 / QQ | **不消费 OG**,读 itemprop 微数据 | 见第九节 |
| Google | `og:title` 是标题链接候选来源之一 | 结构化数据优先走 JSON-LD |

Pinterest 禁止收藏:

```html
<meta name="pinterest" content="nopin" description="Sorry, you can't save from my website!">
```

oEmbed(供消费方发现嵌入端点):

```html
<link rel="alternate" type="application/json+oembed" href="https://example.com/services/oembed?url=…" title="oEmbed Profile: JSON">
```

## 八、Schema.org 微数据与 JSON-LD

微数据写法——**必须在 `<html>` 上加 `itemscope itemtype`**(微信/QQ 分享依赖的正是这组):

```html
<html lang="" itemscope itemtype="https://schema.org/Article">
  <head>
    <meta itemprop="name" content="Content Title">
    <meta itemprop="description" content="Content description less than 200 characters">
    <meta itemprop="image" content="https://example.com/image.jpg">
```

JSON-LD(知识面板,Google 品牌面板):

```html
<script type="application/ld+json">
{
  "@context": "http://schema.org",
  "@type": "Organization",
  "name": "yourbrand.com",
  "url": "https://www.yourbrand.com/",
  "logo": "https://www.yourbrand.com/logo.png",
  "sameAs": ["https://www.facebook.com/yourbrand", "https://twitter.com/yourbrand"]
}
</script>
```

完整模板见 [schema-templates.md](schema-templates.md),示例见 [schema-examples.md](schema-examples.md)。

## 九、中文浏览器与分享 meta

**微信/QQ 分享三件套**(QQ 官方 API `setShareInfo` 口径;分享到微信/QQ 时展示为格式化消息;更可靠的卡片控制走微信 JS-SDK,HEAD 仓库未覆盖):

```html
<meta itemprop="name" content="share title">
<meta itemprop="image" content="http://imgcache.qq.com/qqshow/ac/v4/global/logo.png">
<meta name="description" itemprop="description" content="share content">
```

**360 浏览器**:

```html
<meta name="renderer" content="webkit|ie-comp|ie-stand"><!-- 选择渲染引擎 -->
```

**QQ 移动浏览器(X5 内核)**:

```html
<meta name="x5-orientation" content="landscape/portrait"><!-- 锁定屏幕方向 -->
<meta name="x5-fullscreen" content="true"><!-- 全屏 -->
<meta name="x5-page-mode" content="app"><!-- 应用模式(全屏等) -->
```

**UC 移动浏览器**:

```html
<meta name="screen-orientation" content="landscape/portrait">
<meta name="full-screen" content="yes">
<meta name="imagemode" content="force"><!-- 文字模式下仍显示图片 -->
<meta name="browsermode" content="application"><!-- 应用模式(全屏、禁手势等) -->
<meta name="nightmode" content="disable"><!-- 禁用夜间模式 -->
<meta name="layoutmode" content="fitscreen"><!-- 精简文档省流量 -->
<meta name="wap-font-scale" content="no"><!-- 禁止字多时自动放大字号 -->
```

## 十、geo meta 四件套

```html
<meta name="ICBM" content="48.8566, 2.3522"><!-- 十进制度,逗号分隔 -->
<meta name="geo.position" content="48.8566;2.3522"><!-- 同坐标,分号分隔 -->
<meta name="geo.region" content="US-NY"><!-- ISO 3166-1 国家码必填,ISO 3166-2 州/省可选 -->
<meta name="geo.placename" content="New York City"><!-- 人类可读地名 -->
```

要点:**浏览器不直接消费**这组标签——它们面向搜索引擎、爬虫和位置类服务表达页面的地理相关性。ICBM 与 geo.position 表达同一坐标、仅分隔符不同(逗号 vs 分号)。本地商家 SEO 优先用结构化 LocalBusiness schema(见 [schema-examples.md](schema-examples.md)),geo meta 作辅助。

## 十一、fediverse 与 App Links

**Fediverse 作者归属**(Mastodon 等在嵌入卡片里显示联邦宇宙 handle;Mastodon 还需在 Settings → Public profile → Verification → Author attribution 里把域名加入允许列表):

```html
<meta name="fediverse:creator" content="@handle@example.org">
```

**App Links**(Facebook 规范,原生 App 深链):

```html
<meta property="al:ios:url" content="applinks://docs">
<meta property="al:ios:app_store_id" content="12345">
<meta property="al:ios:app_name" content="App Links">

<meta property="al:android:url" content="applinks://docs">
<meta property="al:android:app_name" content="App Links">
<meta property="al:android:package" content="org.applinks">

<meta property="al:web:url" content="https://applinks.org/documentation"><!-- Web 兜底 -->
```

## 十二、平台 meta(iOS / Android / Chrome)

```html
<!-- iOS Smart App Banner 与深链 -->
<meta name="apple-itunes-app" content="app-id=APP_ID,affiliate-data=AFFILIATE_ID,app-argument=SOME_TEXT">
<link rel="alternate" href="ios-app://APP-ID/http/url-sample.com">

<!-- iOS 启动画面与标题 -->
<link rel="apple-touch-startup-image" href="/path/to/launch.png">
<meta name="apple-mobile-web-app-title" content="App Title">

<!-- 独立(全屏)模式——标准化写法;apple- 前缀旧版已弃用 -->
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black"><!-- 仅独立模式生效 -->

<!-- Android 深链与主题色 -->
<meta name="theme-color" content="#E64545">
<meta name="google-play-app" content="app-id=package-name">
<link rel="alternate" href="android-app://package-name/http/url-sample.com">

<!-- Chrome 应用商店 / 禁翻译提示 -->
<link rel="chrome-webstore-item" href="https://chrome.google.com/webstore/detail/APP_ID">
<meta name="google" content="notranslate">
```

**PWA 首选 manifest**:应用名、独立模式、图标、主题色等属性用 `<link rel="manifest">` 声明更可靠、更可移植;上述平台特定 meta 作旧版本兜底。

## 十三、弃用清单(带替代)

来自 HEAD 仓库 DEPRECATED.md,**不要在新项目使用**:

| 弃用项 | 原因 | 替代 |
|---|---|---|
| `<meta http-equiv="x-ua-compatible" content="ie=edge">` | IE 已于 2022-06-15 退役 | 无需替代 |
| `<meta name="skype_toolbar">` | Skype 工具栏扩展已消亡 | 无 |
| `<meta name="msapplication-config">` + browserconfig.xml | Live Tiles 已从 Win11 移除,Edge 不再渲染 | `<link rel="manifest">` |
| `<link rel="mask-icon">` | Safari 17(2023)移除 Pinned Tabs | 标准 `<link rel="icon">` |
| `<meta name="apple-mobile-web-app-capable">` | iOS 17.4 弃用 | `mobile-web-app-capable`;更推荐 manifest `display` |
| `<link rel="prerender">` | Chrome 已移除 | Speculation Rules API |
| `<meta http-equiv="x-dns-prefetch-control">` | Firefox/IE 时代扩展,Chromium 从未实现 | `<link rel="dns-prefetch">` |
| `<link rel="amphtml">` | Google 2021 年移除 Top Stories AMP 要求,AMP 项目停滞 | 无 |
| `<link rel="EditURI">` / `<link rel="pingback">` | XML-RPC 编辑器消亡;pingback 因 DDoS 放大被默认禁用 | Webmention |
| `<link rel="archives">` / `<link rel="index">` | 已从 HTML Living Standard 与 IANA 注册表移除 | 无 |
| `<meta name="alexaVerifyID">` | Alexa Internet 2022-05-01 关停 | 无 |
| `twitter:*` 卡片全套 | X 在缺失时回落 OG,独立维护冗余;Validator 已退役 | Open Graph(仅卡片类型有差异时保留 `twitter:card`) |
| `<meta name="twitter:dnt">` | X 不再实际遵守 | 无 |
| `<meta property="fb:app_id">` | Facebook 分享不再需要,多数 OG 解析器忽略 | OG 标签本身 |
| `<meta http-equiv="Window-Target">` | IE 时代非标准,现代浏览器不支持 | 无 |

另:`meta keywords` Google 不使用(见 [meta-tag-formulas.md](../content/meta-tag-formulas.md)),不必写。

## 十四、审计要点(SEO 视角)

1. `charset` 是否在前 1024 字节;CSP 是否足够早(只管其后资源)。
2. title/description/OG/canonical 是否在**初始 HTML** 而非 JS 注入——社交爬虫与多数 AI 爬虫不执行 JS,客户端注入 OG = 分享卡片全挂(详见 [rendering-seo.md](rendering-seo.md))。
3. 中文站:微信/QQ 分享是否带 itemprop 三件套;X5/UC 场景按需加浏览器 meta。
4. 逐项对照第十三节清掉弃用标签(尤其 `x-ua-compatible`、`amphtml`、`prerender`)。
5. PWA 属性收敛到 manifest,平台 meta 只留兜底。

## 源

- joshbuchea/HEAD README.md + DEPRECATED.md(CC0,commit `de1304e`,2026-05-01,克隆于 /tmp/wb08/)。
