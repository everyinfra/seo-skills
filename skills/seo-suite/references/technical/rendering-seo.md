# JS 渲染与 SPA SEO(2026 口径)

> 建立于 2026-10-09。以 Google/Naver/Yandex 官方文档为基准;行业实测标注。与 [中文 AI 搜索指南](../content/chinese-ai-search-guide.md) 的"SPA 空壳=P0"条目呼应,本文件是系统版。

## 一、Google 渲染管线(现行口径)

- **两波索引已死**:官方文档已删除 "two waves" 与 "5 秒超时" 表述。现行:抓取 → 渲染队列 → WRS(Web Rendering Service,evergreen Chromium)渲染 → 索引,无固定延迟。
- **队列行为**:HTTP 200 全部进渲染队列;官方措辞"排队 2–3 秒或更久";行业实测秒级至分钟级,**低权重/JS 重站点可拖到数小时甚至数周,JS 站消耗约 9 倍抓取预算**(Onely)。**"不在 rendered HTML 里的内容无法被索引"是官方原话**。
- **检测**:GSC URL Inspection(Live Test 看渲染后 HTML)、URL Inspection API、Rich Results Test;Mobile-Friendly Test 已退役(2023-12)。
- **懒加载红线(官方)**:内容须"进入视口即加载"(`loading=lazy`/IntersectionObserver),**不得依赖用户交互**(Google 不滚动不点击);无限滚动必须给每块持久唯一 URL 并顺序链接。

## 二、渲染策略决策表

| 站点类型 | 推荐 | SEO 后果 |
|---|---|---|
| 内容站/媒体 | SSG+ISR(on-demand) | 纯 CSR=Google 延迟索引、**Bing/AI 爬虫直接丢内容**(约 69% 主流爬虫不渲染 JS——SearchVIU 2025) |
| 电商 | 产品页 SSG/ISR;筛选 SSR 或规范化分页 | 价格/库存个性化部分客户端注水,主内容必须服务端 |
| SaaS | 营销站/docs SSR/SSG;app.* 子域整体 noindex | 混合渲染(Next.js per-page)是主流 |
| 文档 | SSG+ISR | 静态最优 |

**meta 注入红线**:title/OG/canonical/hreflang 必须在初始 HTML。Google 渲染后能读 JS 注入的 meta(官方:JS 注入 canonical 可读但须单标签且与响应头一致);**社交爬虫(Facebook/LinkedIn/微信)与多数 AI 爬虫不执行 JS——客户端注入 OG=分享卡片全挂**,且 Facebook 只解析前 ~60KB HTML。

## 三、市场差异:各引擎渲染能力

| 引擎 | 口径(来源类型) | 实操 |
|---|---|---|
| Google | WRS evergreen Chromium(官方) | 常规 |
| Bing | "一般能渲染 JS"但规模化受限,可靠性低于 Googlebot(官方 2018+行业实测) | **SPA 纯 CSR 连带伤 ChatGPT 可见性**(Bing 生态) |
| Naver Yeti | **官方确认解析 JS**,但资源消耗"数倍于 HTML",**官方明确建议 SSR**;两段式管线(先静态索引,JS 另行抓取渲染);JS/CSS 必须 robots 放行;fragment(#)URL 被剥离→SPA 必须用 History API(官方 JS 指南) | 韩语区 SPA 一律 SSR |
| Yandex | 站长侧 JS 渲染开关(β,官方);历史上不渲染 | 俄语区以开关+实测为准 |
| Baiduspider | "百度不执行 JS"为行业共识;有独立渲染 UA `Baiduspider-render`(行业实测,官方文档缺失)——**以百度站长平台"抓取诊断"实测为准** | 中文区 SSR/预渲染兜底 |

## 四、SPA SEO 审计清单(7 项)

1. `view-source`:主内容/title/meta/OG/canonical/hreflang/JSON-LD 是否在原始 HTML(空壳=P0)。
2. 单页 `curl -A "Mozilla/5.0 (compatible; Googlebot/2.1)"` 对比正常 UA(**只做诊断,不做差异化输出**)。
3. GSC Live Test 看渲染后 HTML;禁 JS 看退化内容。
4. robots.txt 放行 JS/CSS;JS/CSS 用指纹文件名(WRS 可能忽略缓存头)。
5. SPA 路由用 History API;JS 软 404 用 meta noindex 注入或真 404(官方)。
6. **cloaking 红线**:bot 与用户返回显著不同内容=违规;动态渲染"一般不算 cloaking"(输出一致前提下)但官方已降级为**临时变通,非长期方案**。
7. 预渲染:Google 自家 Rendertron 已归档(2022);Prerender.io 系仍在维护;2026 主流风险是**内容漂移**(bot 版与用户版不一致)而非惩罚——能 SSR 就别长期挂预渲染。

## 五、CWV 关联

- **INP(200ms)**:hydration backlog 与长任务是 React 系最大杀手;解法:RSC、岛屿/partial hydration、`scheduler.yield`。
- **LCP**:CSR 空壳天然差(等 JS bundle);SSR/流式渲染;勿对首屏 LCP 图 lazy-load;hydration 重写 DOM 可引发 CLS。

## 渲染工程三件套全文细节(百仓深扫完全装载)

**rendertron(官方弃用遗产,参数仍可引用)**:动态渲染 UA 白名单 16 个(Baiduspider/bingbot/Embedly/facebookexternalhit/LinkedInBot/pinterest/quora/Slackbot/Telegrambot/Twitterbot/vkShare/WhatsApp 等——**名单里没有 Googlebot**,Google 不需要);静态扩展名豁免 45 项(.js/.css/.svg/.xml… 命中不代理);渲染硬预算 **10 秒**;中间件超时 11000ms;缓存默认 24h、datastore 下 >1000 条性能劣化;`<meta name="render:status_code">` 可控代理返回码;代理失败 next() 回落原 SPA 不 5xx。
**react-snap 失败模式清单**:只支持 History 路由(hash 不可预渲染);snapSaveState 仅支持基本 JSON 类型(Date/Set/Map/NaN 会坏);Service Worker navigateFallback 须指 200.html 而非 index.html(否则他页闪首页);skipThirdPartyRequests 屏蔽 GA/Mapbox;爬取 UA 固定 "ReactSnap";JS 注入样式须关 speedy 才进 DOM;JSS 不支持 rehydration;决策三选——renderToString(锁库)/JSDOM(不支持 Blob,行为分叉)/headless(SSR 分叉 caveat)。
**astro-paper(静态主题 SEO 基线)**:OG 图 satori+sharp 1200×630 内嵌本地字体(不外链 Google Fonts);**文章自带 ogImage 时跳过自动生成(自定义优先)**;草稿不生成;robots-as-code 三行式指向 sitemap-index;GSC 验证走环境变量非硬编码;极简 BlogPosting JSON-LD(无 publisher,刻意)。
**CSR 落地(theninthsky)**:**Bing 不能渲染 JS→预渲染是 Bing/AI 可见性的实际前提**;Worker 按 UA 分流(bot 列表含 bingbot/yandex/twitterbot,**必须排除 googlebot**);Prerender.io 1000 次/月免费;"Vercel 组合过滤 65536(2^16) 种只能单文件"=SSG 反例;CSR 渲染即 JS 就绪、结构性免疫水合失焦。

## 源码级实现细节:rendertron 中间件/react-snap 管线/astro-paper 端点(rendertron·react-snap·astro-paper 源码深读,2026-10-09)

补上节"渲染工程三件套"的内部实现,审计遗留动态渲染栈或自建预渲染管线时直接引用。

**rendertron 中间件路由逻辑**(`middleware/src/middleware.ts`):UA 正则默认 `new RegExp(botUserAgents.join('|'), 'i')` 对 16 个 bot 名做**不区分大小写任意位置匹配**;命中后构造 `proxyUrl + encodeURIComponent(完整入站 URL)`——整 URL 二次编码是关键,防路径注入;`injectShadyDom` 选项追加 `?wc-inject-shadydom=true`(Web Components 站必须);`allowedForwardedHosts` + `X-Forwarded-Host`(默认头名可换)防 host 头伪造——**只有白名单内的 forwarded host 才被采用**,否则回落 `req.get('host')`;代理失败仅 console.error 后 `next()` 回落原 SPA(不 5xx)。服务端(`src/rendertron.ts` + `src/config.ts`):`restricted()` 三重防线——非 http(s) 协议拒、`*.internal` 内网域拒、配置了 `renderOnly` 前缀列表则非成员拒,全部 403(**SSRF 防护**);`x-renderer: rendertron` 响应头自曝身份;`/_ah/health` 健康检查;缓存三选(datastore/memory/filesystem)各带 `/invalidate/:url` 与 `/invalidate/` 全清端点;默认 viewport 1000×1000、超时 10000ms、`puppeteerArgs: ['--no-sandbox']`;`?mobile` 查询参数切移动渲染、`?timezoneId` 传时区。

**react-snap 内部管线**(`doc/behind-the-scenes.md` 14 步 + `index.js` 默认参数):复制 index.html→200.html → 起 express+serve-static+history-api-fallback 本地服务(默认端口 **45678**,源目录 `build/`)→ 从 `include:["/"]` 起爬同域链接入队(>1 页时追加 /404.html)→ puppeteer 渲染(**并发 4 tab**,`concurrency` 可调)→ **等待无活跃网络请求 0.5s** → CRA1/CRA2/Parcel chunk 修复(删 chunk script 换 `<link rel=preload as=script>`,按 package.json 里 react-scripts/parcel-bundler 版本自动判型)→ 删 blob 样式 → 重建 CSS-in-JS style 文本(`fixInsertRule`:空 style 从 `style.sheet.rules` 重生成 cssText)→ 可选 inlineCss(minimalcss 关键 CSS)→ 可选 http2PushManifest → 压缩 HTML 落盘(route 以 .html 结尾用原名,否则 route/index.html)。**表单状态固化**(`fixFormFields`):radio/checkbox 的 checked 与 option 的 selected 转成 HTML 属性,防止水合错位。**落盘告警**:404 页 title 不含 "404" 与普通页 title 含 "404" 都 console.warn(soft-404 语义自检)。**默认移动优先 viewport 480×850**、UA 固定 "ReactSnap"、`saveAs` ∈ html|png|jpeg。**anatomy 文档的预渲染器选型矩阵**:DOM 层三选——renderToString(锁框架、组件须支持 SSR、可缓存)/JSDOM(不支持 Blob 等新特性、SSR 分叉 caveat)/headless(react-snap 路线,真浏览器无特性缺口);路由发现三选——手列清单(会漏)/程序生成(gatsby createPages)/爬取(**react-snap 默认,爬不到的手动补**);数据层 agnostic(不做数据生成器)+ 水合靠 `window.snapSaveState` 序列化状态(Redux/loadable-components/Apollo 同一钩子)。**性能实测**(an-almost-static-stack,Moto G4/3G):inlineCss 使 Start Render -0.5s;Link 头(superstatic JSON 格式 `</static/js/main.df90a75f.js>;rel=preload;as=script`)使 First Interactive -0.6s;HTTP2 push 经 Cloudflare "几乎无变化";`removeScriptTags`(Netflix 式 server-only React)Load Time 3.6s→1.16s 但 PWA 分 91→45;换 Preact JS -35KB 但 React 16 特性不兼容。

**astro-paper 六文件细节**:`Layout.astro` 全站 head 模板——canonical 默认 `new URL(Astro.url.pathname, Astro.site)`;og:image 绝对化 `new URL(ogImage, Astro.site)`;**`<slot name="head">` 让子布局注入 JSON-LD/article meta**(分层注入模式);RSS 自动发现 `<link rel=alternate type=application/rss+xml>`;FOUC 防御用内联同步脚本读 localStorage+prefers-color-scheme 设 data-theme(**渲染前设,无闪烁,与 SSR 兼容**);`theme-color` 运行时填充。`PostLayout.astro`:BlogPosting 极简 JSON-LD(headline/image/author[Person]+条件 datePublished/dateModified 均toISOString);**og:type 覆盖模式**——Layout 默认 website,文章页用 slot 注入 `<meta property=og:type content=article>` **重复标签覆盖**(HTML 去重取第一个/最后因解析器而异,Astro 里靠注入顺序可控)——自研模板更稳的做法是 prop 传参;article:published_time/modified_time 与 JSON-LD 同源(props 直出)。`og.png.ts` + `posts/[...slug]/index.png.ts`:satori+sharp 生成 1200×630 PNG;**字体从 `astro:assets` 的 fontData 按权重(400/700)取本地文件**,不请求 Google Fonts(构建确定性+隐私);`embedFont:true` 字体内嵌进 SVG;视觉规范:双卡片边框(absolute 偏移 1px 阴影层 opacity .9)+标题 72px 粗体+站名/作者 28px、`overflow:hidden` 截断;文章 OG 的 `getStaticPaths()` **过滤 draft 与自带 ogImage 的文章**(自定义优先)+`config.features.dynamicOgImage` 总开关(关则 404)。`robots.txt.ts`:APIRoute 三行式输出 `User-agent: * / Allow: / / Sitemap: {site}/sitemap-index.xml`(robots-as-code,与构建产物同源)。`astro.config.ts`:`@astrojs/sitemap` 的 filter 回调按 `features.showArchives` 剔除 /archives/(**功能开关直接映射 sitemap 收录**);i18n `prefixDefaultLocale:false`(默认语言无前缀,canonical 干净);GSC 验证走 `envField.string({access:"public"})` 环境变量注入,不硬编码进模板;shiki 双主题(min-light/night-owl)+`defaultColor:false`(暗色模式不重排)。

## 来源

官方:Google JS SEO 基础/懒加载/动态渲染文档、Next.js SEO 教程、Naver Search Advisor JS 指南、Yandex Webmaster rendering。行业:Patrick Stox、Onely(9× 抓取预算)、SearchVIU 2025(AI 爬虫渲染)、dev.to 2026 综述。GitHub:garmeeh/next-seo(8.5k★)、prerender-node(921★,维护中)/Rendertron(已归档,信号)。未证实项:WRS 具体 Chromium 版本(官方只说 evergreen);百度渲染官方文档缺失;渲染队列实际延迟无固定值;AI 爬虫渲染能力半年即可能过期。
