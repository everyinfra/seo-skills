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

## 来源

官方:Google JS SEO 基础/懒加载/动态渲染文档、Next.js SEO 教程、Naver Search Advisor JS 指南、Yandex Webmaster rendering。行业:Patrick Stox、Onely(9× 抓取预算)、SearchVIU 2025(AI 爬虫渲染)、dev.to 2026 综述。GitHub:garmeeh/next-seo(8.5k★)、prerender-node(921★,维护中)/Rendertron(已归档,信号)。未证实项:WRS 具体 Chromium 版本(官方只说 evergreen);百度渲染官方文档缺失;渲染队列实际延迟无固定值;AI 爬虫渲染能力半年即可能过期。
