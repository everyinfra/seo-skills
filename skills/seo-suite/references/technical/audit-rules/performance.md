# 审计规则目录 · Performance

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### Performance(28 条,权重 10%)

**CWV 阈值**(web.dev,核对 2026-10-21):LCP ≤2.5s、>4s 为差([vitals](https://web.dev/articles/vitals)、[阈值研究](https://web.dev/articles/defining-core-web-vitals-thresholds));INP ≤200ms、>500ms 为差([INP](https://web.dev/articles/inp));CLS ≤0.1、>0.25 为差([CLS](https://web.dev/articles/cls));TTFB ≤0.8s、>1.8s 为差([TTFB](https://web.dev/articles/ttfb));FCP ≤1.8s、>3.0s 为差([FCP](https://web.dev/articles/fcp))。详见 [LCP.md](../LCP.md)、[scoring-rubric.md](../scoring-rubric.md)。SEOmator 的 `cwv-inp` 不计分(审计没有真实输入)。

**静态项**(SEOmator 现行 132d2384,均为工具约定):`perf-dom-size` 节点 >800 warn、>1500 fail,嵌套 >32 warn、>48 fail,单元素子节点 >60 warn(Lighthouse 是 body 节点 ~800 警、~1,400 错,[文档](https://developer.chrome.com/docs/lighthouse/performance/dom-size));`perf-css-file-size`(外链样式表 >3 warn、>6 fail;内联 CSS >50KB warn、>100KB fail);`perf-js-file-size`(内联 JS 合计 >50KB warn、>150KB fail,外链脚本不量);`perf-page-weight` 只量 HTML 文档本身(>100KB warn、>300KB fail);`perf-cache-policy` 查页面自身响应有没有缓存头(Cache-Control、ETag、Last-Modified、Expires 任一即过);`perf-asset-cache-policy`(渲染专属,静态资源 max-age ≥1 小时,Expires 不读);`perf-text-compression`(页面响应须 gzip/br/deflate/zstd)、`perf-brotli`;`perf-asset-compression`(渲染专属,>2KB 文本资源须压缩,按 content-length,chunked 无长度不判);`perf-image-encoding`(渲染专属,传输 >100KB warn,BMP/TIFF fail);`perf-minify-css/js`(内联超 500 字节后,空白占比 >15% 或 JS 块注释=warn;外链 >2KB 且 URL 无 `.min.` 为启发式,恒 ≤warn);`perf-http2` 只看有无 `alt-svc` 头,不读协商协议;`perf-video-for-animations` 任何 GIF 都 warn(分不出是否动画,「省 90%」是原版说法);`perf-response-time`、`perf-render-blocking`(head 内脚本无 async/defer)、`perf-lazy-above-fold`(首屏图禁 lazy)、`perf-lcp-hints`(LCP 图须 preload 与 fetchpriority=high)、`perf-font-loading`(font-display:swap)、`perf-preconnect`、`perf-legacy-javascript`、`perf-duplicate-js`(同库多 URL)、`perf-source-maps`(不得暴露 sourceMappingURL)。

**解释层(9 条;ID 未公布原文的按家族命名法推得并标 [待核];CWV 五指标本身见 [LCP.md](../LCP.md) 不重述)**

#### perf-page-weight
- 名称/类型: HTML 文档体积 —— warning · 优先级 medium · 输出 WARN/CRITICAL(源表现行 warn/fail:HTML 本身 >100KB warn、>300KB fail;图片、脚本、样式只在详情里计数,不参与判定;旧快照写的是「总重 <3MB」,已作废)
**这意味(what)**: HTML 文档本身(未含子资源)超过 100KB(工具约定)。
**为什么(why)**: Googlebot 抓取一个文件只取前 2MB,PDF 前 64MB,超出部分不参与索引,限制按解压后字节算([Googlebot 文档](https://developers.google.com/search/docs/crawling-indexing/googlebot),核对 2026-10-21)。100KB 与 300KB 远低于 2MB,标记的多是内联脚本、内联样式或嵌入数据(如整份 JSON 状态)撑大的文档。
**触发(trigger)**: HTML 响应体 >100KB warn,>300KB fail(未压缩字节)。
**不修的条件(caveat)**: 文档长度不直接影响排名;数据密集的长文档(手册、规格表)超线是内容属性。接近 2MB 才有索引截断风险。
**修复(fix)**: 内联脚本、样式、状态数据移到可缓存的外部文件;超长页拆页。图片、视频走 images-* 规则。
**关联(seealso)**: perf-asset-compression、images-modern-formats;[LCP.md](../LCP.md)

#### perf-asset-compression [待核 ID]
- 名称/类型: 文本资源未压缩(压缩家族) —— warning · 优先级 medium · 输出 WARN(源表 warn;渲染专属。perf-text-compression/perf-brotli 同构:载体与算法维度不同)
**这意味(what)**: content-length >2KB 的文本资源(HTML/CSS/JS/SVG/JSON)响应未带 gzip/Brotli 编码。
**为什么(why)**: 文本压缩是成本最低的传输优化之一;Brotli 静态预压又比 gzip 小一档。判定严格按 content-length:>2KB 才查,chunked 无长度不判——避免对流式响应误报,这是阈值纪律而非疏漏。
**触发(trigger)**: 1) 响应 content-length >2KB;2) 无 Content-Encoding: gzip/br 即 warn。家族其余规则同构:perf-text-compression(存在性)、perf-brotli(Brotli 特供)。
**不修的条件(caveat)**: 压缩不影响排名,然而 TTFB 之后的传输时间是 LCP 的直线组成,所以一般建议全站开启。但极小资源(<1KB)压缩收益趋零、CPU 反增的边缘场景可放过。
**修复(fix)**: 服务器/CDN 层开 gzip(底线)或 Brotli(静态资源构建期预压缩最优);验收看响应头。
**关联(seealso)**: perf-asset-cache-policy、perf-page-weight;[cwv-playbook.md](../cwv-playbook.md)

#### perf-asset-cache-policy
- 名称/类型: 缓存策略(缓存家族) —— warning · 优先级 medium · 输出 WARN(源表 warn;perf-asset-cache-policy 渲染专属:静态资源 max-age ≥1 小时,不读 Expires;perf-cache-policy 现行只查页面自身响应有无缓存头,「内容 hash 资源须 max-age=31536000」是旧快照写法,现行文档仅把「一年」列为带 hash URL 的修复建议)
**这意味(what)**: 静态资源 Cache-Control max-age 缺失或 <1 小时;页面自身响应没有任何缓存头。
**为什么(why)**: 缓存决定回访与深层爬取的成本:短 max-age 每次访问都重下全部资源;内容 hash 文件名(hash 变=新 URL)天然免疫过期,理应一年期 immutable。CWV 字段数据(CrUX)也依赖真实用户侧缓存生效。
**触发(trigger)**: 1) 静态资源(CSS/JS/图/字体)max-age 缺失或 <3600s 即 warn;2) 页面响应无 Cache-Control(含 max-age/no-cache/no-store)、ETag、Last-Modified、Expires 任一即 warn(perf-cache-policy)。
**不修的条件(caveat)**: 缓存头不影响排名,然而它决定重复访问的真实体验,所以一般建议分层:hash 资源一年+immutable、入口 HTML 短缓存。但无 hash 管道的 CSS 频繁热修时短缓存是运维取舍——先建 hash 管道再拉长缓存。
**修复(fix)**: 构建产物文件名带 hash,配 max-age=31536000, immutable;HTML 用 no-cache/短缓存;两者配合才安全。
**关联(seealso)**: perf-asset-compression;[cwv-playbook.md](../cwv-playbook.md)

#### perf-render-blocking [待核 ID]
- 名称/类型: 渲染阻塞脚本 —— warning · 优先级 medium · 输出 WARN(源表 warn;head 内脚本无 async/defer)
**这意味(what)**: head 内的 `<script src>` 无 async/defer,HTML 解析必须停下等它下载执行。
**为什么(why)**: 同步脚本阻塞解析器,FCP/LCP 直接被拖;多个同步脚本串行时每个都是链上的一环。async(下载完即执行)与 defer(解析完执行)都归还解析权,语义上 defer 保序、async 抢跑。
**触发(trigger)**: 1) head 内 `<script src>` 无 async/defer 即 warn;2) 内联脚本位于外链同步脚本之后被连带卡住的判定口径[待核]。
**不修的条件(caveat)**: async/defer 不改变脚本对 SEO 的作用,然而它决定首屏时间,所以一般建议非关键脚本全 defer。但强顺序依赖的第三方(统计/AB)要 defer 不要 async,别一刀切。
**修复(fix)**: 非关键脚本 defer 或挪 body 尾;head 只留精简关键样式与资源提示(见 perf-lcp-hints);验收用渲染瀑布图。
**关联(seealso)**: perf-lcp-hints、js-initial-html;[rendering-seo.md](../rendering-seo.md)

#### perf-lcp-hints [待核 ID]
- 名称/类型: LCP 图加载提示 —— warning · 优先级 high · 输出 WARN(源表 warn;LCP 图须 preload+fetchpriority=high)
**这意味(what)**: 页面 LCP 元素是图,却没有 `<link rel=preload as=image>` 且缺 fetchpriority="high"。
**为什么(why)**: fetchpriority="high" 告诉浏览器这张 LCP 图属于高 Fetch Priority 资源(这是资源加载提示,与 sitemap 的 priority 无关),让 LCP 更早发生;preload 让浏览器在发现前就开始加载([web.dev Fetch Priority](https://web.dev/articles/fetch-priority),核对 2026-10-21)。两者叠加是常见做法,「必须同时有」是 SEOmator 的工具约定。LCP Good 阈值 ≤2.5s(见 [LCP.md](../LCP.md))。
**触发(trigger)**: 1) 渲染判定 LCP 元素;2) 为图且无 preload 或无 fetchpriority=high 即 warn。
**不修的条件(caveat)**: 资源提示不影响排名,然而它们直接调度 LCP 资源的优先级,所以一般建议 LCP 图必配。但 LCP 元素是文字的页面不适用;preload 滥用(全页 preload)反而稀释优先级,只给这一张。
**修复(fix)**: `<link rel="preload" as="image" href="…hero.webp" fetchpriority="high">`,img 同步加 fetchpriority="high";LCP 图禁 lazy(见 images-lazy)。
**关联(seealso)**: images-lazy、perf-font-loading;[LCP.md](../LCP.md)

#### perf-font-loading [待核 ID]
- 名称/类型: 字体加载策略 —— warning · 优先级 medium · 输出 WARN(源表 warn;font-display:swap)
**这意味(what)**: @font-face 声明缺 font-display:swap(或等价的防隐形策略)。
**为什么(why)**: 浏览器对未到达字体的默认行为并不一致,常见是字体下载完前文字不可见(FOIT);`font-display` 让你指定行为,swap 先用后备字体渲染、字体到了再换([web.dev](https://web.dev/articles/optimize-webfont-loading),核对 2026-10-21)。
**触发(trigger)**: 渲染检查 @font-face 无 font-display:swap/optional 即 warn。
**不修的条件(caveat)**: swap 的双字 metrics 差异会小幅推高 CLS,然而换来的立即可见远大于抖动代价,所以一般建议 swap。但排版严苛页可选 optional(超时永用系统字);中文大字符集字体建议子集化后再 swap。
**修复(fix)**: @font-face 加 font-display:swap;关键字体 `<link rel=preload as=font crossorigin>`;中文字体按常用字切片。
**关联(seealso)**: perf-lcp-hints;[cwv-playbook.md](../cwv-playbook.md)

#### perf-dom-size
- 名称/类型: DOM 规模 —— warning · 优先级 medium · 输出 WARN(源表现行:节点 >800 warn、>1500 fail;嵌套 >32 warn、>48 fail;单元素子节点 >60 warn)
**这意味(what)**: 渲染后 DOM 节点数超 800(>1500 更重),或最大嵌套深度 >32,或某元素子节点 >60。
**为什么(why)**: DOM 过大会拖慢样式计算、布局和交互响应(web.dev 关于 DOM 大小与交互性的文章把 Lighthouse 的 ~800 节点警告、~1,400 节点错误当参考线,[文章](https://web.dev/articles/dom-size-and-interactivity),核对 2026-10-21);深度 >32 多是组件层层嵌套出的无语义容器。
**触发(trigger)**: 1) 渲染后元素节点数 >800 warn、>1500 fail;2) 最大嵌套深度 >32 warn、>48 fail;3) 单元素子节点 >60 warn。
**不修的条件(caveat)**: DOM 规模不(直接)影响 SEO,然而它给交互响应设上限,所以一般建议长列表分页/虚拟滚动。但数据密集页(财务表格)DOM 天然大,分页才是正解,不是硬删。
**修复(fix)**: 列表虚拟滚动或分页;拆装饰性嵌套容器;组件库治理"div 三明治"(每组件三层无语义 div)。
**关联(seealso)**: perf-page-weight;[cwv-playbook.md](../cwv-playbook.md)

#### perf-resource-hygiene [待核 ID]
- 名称/类型: 资源卫生家族(六小条) —— warning · 优先级 low · 输出 WARN(源表各=warn)
**这意味(what)**: 六项资源层卫生任一命中:响应没有 `alt-svc` 头(perf-http2 现行只看这个头,服务器已跑 HTTP/2 也会 warn);legacy polyfill 包(perf-legacy-javascript);同库多 URL 重复加载(perf-duplicate-js);暴露 sourceMappingURL(perf-source-maps 不得暴露);GIF 该换 video(perf-video-for-animations:任何 GIF 都 warn,分不出是否动画);css/js 压缩嫌疑(perf-minify 家族:内联超 500 字节后空白占比 >15% 或 JS 块注释;外链 >2KB 且 URL 无 .min. 标记=启发式嫌疑,恒 ≤warn)。
**为什么(why)**: 每项都是确定的字节/时间浪费:HTTP/1.1 队头阻塞限制同域并行;legacy JS 给现代浏览器发多余 polyfill;同库多 URL 既多下载又版本漂移;source map 公开暴露源码结构(偏安全面);GIF 做动画体积通常远大于等效视频(原版称最多省 90%,工具口径)。单项轻,叠加是可量化的无谓传输。
**触发(trigger)**: 无 `alt-svc` 头 → warn;脚本含 es5 时代 polyfill 特征 → warn;同库 ≥2 个不同 URL → warn;脚本带 sourceMappingURL → warn;任何 GIF → warn;外链 css/js >2KB 且无 .min. → 恒 ≤warn(启发式;图片传输侧另见 perf-image-encoding:>100KB=warn、BMP/TIFF=fail,与 Images 节 images-modern-formats 同一事实两面)。
**不修的条件(caveat)**: 家族单项都不影响排名,然而叠起来是可量化的浪费,所以一般建议一次清完。但 source map 若仅鉴权后可访问,暴露面已受控,可降优先级。
**修复(fix)**: 全站 HTTP/2+;构建 target 现代浏览器砍 polyfill;依赖收敛单版本;source map 仅上传错误平台、产物剥离 sourceMappingURL;GIF→MP4/WebM;构建开 css/js 压缩输出 .min. 产物。
**关联(seealso)**: perf-asset-compression、perf-asset-cache-policy;[cwv-playbook.md](../cwv-playbook.md)

#### perf-preconnect [待核 ID]
- 名称/类型: 关键源预连接 —— warning · 优先级 medium · 输出 WARN(源表 warn;perf-response-time 与 TTFB 同源阈值已吸收于 [LCP.md](../LCP.md) 不重述)
**这意味(what)**: 页面加载关键的跨源资源(字体 CDN/图床/第三方关键脚本)没有 `<link rel="preconnect">`(或 dns-prefetch 兜底)。
**为什么(why)**: 每个新源要付 DNS+TCP+TLS 三段握手,关键资源跨源时握手时间前置吃进 LCP;preconnect 提前完成握手,资源请求一发出即进传输段。只该给关键少数源——滥用会占满连接池,反而拖慢其余资源。
**触发(trigger)**: 渲染瀑布中首屏关键资源(字体/LCP 图/关键 CSS)的 host 与页面 host 不同,且 head 无对应 `<link rel="preconnect" href="https://…">`(字体类带 crossorigin)即 warn。
**不修的条件(caveat)**: 资源提示不(直接)影响排名,然而它削掉的是 LCP 里最机械的握手段,所以一般建议关键跨源必配。但资源已同源聚合或全站 HTTP/3 的站点收益趋零,按瀑布图实测决定再配。
**修复(fix)**: head 顶部对字体/CDN 源加 preconnect(字体带 crossorigin);次级源用 dns-prefetch;可配合 103 Early Hints 由源站下发(见 [cwv-playbook.md](../cwv-playbook.md))。
**关联(seealso)**: perf-lcp-hints、perf-font-loading;[cwv-playbook.md](../cwv-playbook.md)、[LCP.md](../LCP.md)
