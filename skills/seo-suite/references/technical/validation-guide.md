# 结构化数据验证

> 涉及 FAQPage 或 AI 引用的判断，先读 [geo-evidence.md](../content/geo-evidence.md)。

## 用途

新增或修改 schema 后做验收、审计别人的站点、排查「富结果不出现」时读。类型怎么选见 [schema-templates.md](schema-templates.md)。

## 一、三层验证，分开记录结论

| 层 | 要回答的问题 | 用什么查 |
|---|---|---|
| 1. 词汇 | JSON 能否解析；schema.org 类型和属性是否存在；值的类型对不对 | [Schema Markup Validator](https://validator.schema.org/) |
| 2. Google 支持与资格 | 该类型是否在 Google [类型库](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)里；Google 要求的属性齐不齐；是否违反[通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies) | [富媒体搜索结果测试](https://search.google.com/test/rich-results)、Search Console 的富结果报告和网址检查 |
| 3. 与可见内容一致 | 每个字段在渲染后的页面上能否找到对应的可见内容 | 浏览器渲染后的 DOM 加截图，逐字段对照 |

三层是三个结论，不合并成一个「通过」。例如 FAQPage 可以词汇合法，但 FAQ 富结果已停止展示，也不代表 AI 会优先引用。富媒体搜索结果测试只列出 Google 富结果支持的类型，没列出来不等于页面上没有其他 schema。三层都通过也不保证展示富结果，这不算验证失败。

## 二、不能只凭源码说「没有 schema」

JSON-LD 可能由前端框架、跟踪代码管理器或插件在渲染时注入，Google 能读取 JavaScript 注入的 JSON-LD（见[用 JavaScript 生成结构化数据](https://developers.google.com/search/docs/appearance/structured-data/generate-structured-data-with-javascript)）。所以 `curl` 或静态抓取看不到，不能作为「没有 schema」的证据。要下这个结论，至少要有下面一项：

- 浏览器渲染后 DOM 的检查结果；
- 富媒体搜索结果测试用 URL 模式的结果；
- Search Console 网址检查「测试实际网址」里 Google 看到的内容（需要该站点的 Search Console 权限）；
- 用户提供的渲染后 HTML 或截图。

还要查 microdata、RDFa 这类其他格式（`itemscope`、`typeof` 属性），以及 CDN 或服务端是否给爬虫和浏览器返回了不同内容。

在浏览器开发者工具控制台里列出所有 JSON-LD 并检查能否解析（自写示例）：

```js
[...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => {
  try { return JSON.parse(s.textContent); } catch (e) { return "解析失败：" + e.message; }
});
```

## 三、排查顺序

1. **页面本身**：能否抓取、有没有 noindex、状态码是否为 200。测试工具抓不到页面时，先解决这个问题。
2. **有没有标记**：渲染后 DOM 里有没有 JSON-LD 或 microdata；有几份，是否被几个插件重复输出。
3. **能否解析**：JSON 语法是否合法。
4. **词汇**：类型名、属性名拼写（区分大小写），值的类型和嵌套是否正确。
5. **Google 要求**：该类型是否受支持，必填属性是否齐全，是否符合政策。错误（error）会让该项失去资格；警告（warning）通常是缺少推荐属性，可以按需补。
6. **一致性**：价格、库存、评分、日期、作者、问答文本与页面逐条对照。
7. **上线后**：看 Search Console 对应的富结果报告；修复后用「验证修复」，并记下日期。
8. **仍不展示**：确认该功能当前是否还在展示（FAQ、HowTo 已不再展示），再检查人工处置和内容质量；不要为了「拿到展示」去改标记内容。

## 四、常见错误

- JSON 语法：末尾多余逗号、中文引号、未转义的双引号或换行。
- 属性名大小写写错，例如把 `datePublished` 写成 `datepublished`。
- 日期不是 ISO 8601 格式；URL 用了相对路径（绝对地址最稳妥）。
- 价格里带货币符号。按 [schema.org 的 price 说明](https://schema.org/price)，币种应写在 `priceCurrency` 里。
- 枚举值写成普通文字，例如库存状态应写 `https://schema.org/InStock`，而不是「有货」。
- 同一实体被多个插件各输出一份，且内容互相矛盾。
- 标记与页面不一致：价格过期、页面上没有的评价、隐藏的问答。

## 交付时给出

每个受检 URL 的验证记录：检查时间、设备或 User-Agent、所用工具、是否基于渲染后内容；三层各自的结论；错误和警告清单；截图或工具导出作为证据；修复建议和复查日期。

## 罕见判定法(seo-ops C 集,百仓扫描批 3;直接可落成检查规则)

- **C26 Accept-Language 跳转探测**:en-US 与 zh-CN 双语 fetch,对比 final_url——抓"自动语言跳转"导致的重复/错配;
- **C9 无 JS 完整性**:禁 JS 抓取≥90% 渲染版内容才算服务端完整(量化 SPA 判定);
- **C10 缓存个性化验证**:双匿名抓取 diff 为空=缓存非个性化;
- **C13 soft-404 双阈值**:长度+词数双低即判(不只看 200 状态);
- **C2 lastmod 验真**:覆盖率/离散度/单日聚簇——批量同日 lastmod=伪造信号;
- **C27 head 合法性**:head 内出现非法元素提前终止解析检查。
- **T 集反向映射**:内容团队须供给的输入(标题/H2 大纲/alt/YMYL 判断/OG 文案)反向映射到下游检查——审计前先收供给清单。
- **清单治理**:检查 ID 永久不回收;同优先级+同抓取动作则合并。

## 审计阈值补充(seonaut 70 项/SEOmator 实体图/tigerless 全文细则,百仓深扫)

**seonaut 精确阈值表**(开源 Go 审计器实证):title <20/>60 字符;description <80/>160;单页链接 >100;词数 <200;**DOM >1500 节点**;TTFB >800ms;alt >100 字符;图片 >500KB;深度 >4 点击;跨页 14 项(body_hash 重复内容/hreflang 缺回链/canonical 指向不可索引页/孤儿页/重定向链与环)。
**head 八元素白名单(C27)**:head 仅 title/meta/link/script/style/base/noscript/template 合法——遇非法元素 Google 即认为 head 结束、其后全部失效;高频祸首=追踪像素 img、tag-manager iframe、内联 SVG favicon;GTM 官方即放 body 顶部;关键机读标签放最前。
**lastmod 三判定(C2 全文)**:Coverage=有 lastmod 条目占比应 1.0;Freshness=最新 ≤30 天;Truthfulness=最大单日簇占比且该日≠运行日(build 戳每天=今天必被抓);"假 lastmod 比没有更糟";储备判据=sitemap lastmod 与页 JSON-LD dateModified 打架;50k URL/50MB 超限**整文件作废**。
**语言跳转拆除顺序(C26 全文)**:Googlebot 不发 Accept-Language→他语言版本"对爬虫不存在"(P0);修复顺序=先各语言独立 URL 直 200→补 hreflang→最后删跳(反序会两版短暂 404);内容页禁自动跳,根路径 / 作选择器可。
**Disallow×noindex 不叠加**:不被爬则 noindex 读不到,仍可经外链无摘要索引;登录页应 200+noindex 而非 403。
**SEOmator 实体图六查**:`schema-entity-id`(@id 须绝对)/rating-scope(AggregateRating 须可见)/entity-conflict(一 @id 两 logo)/entity-dangling(publisher/author 的 @id 须在爬取中声明)/entity-type-drift(同 @id 跨页 @type 一致)/entity-split(同名组织不挂两 @id);AI/GEO 13 规则含 **geo-pay-per-crawl(HTTP 402 且无 Pay/Crawler-Price 头才警)**、geo-markdown-response、Content-Signal 矛盾检测(ai-train=yes 但训练 bot 全 Disallow=矛盾)。
**raw-vs-rendered 实现要点(SEOmator)**:HTTP 抓原始→$;Playwright 二抓→rendered$;UA 与 HTTP 爬虫一致;web-vitals 库在 goto 前注入(LCP/CLS 只在加载期发);INP 需交互故合成时标 inpSynthetic 不计分。

## 完全装载:Indexing API 状态机/hreflang 簇矩阵/staging 检查/SERP 类型(百仓深扫)

**Indexing API 提交器规格**(goenning,源码级):9 态状态机=Submitted and indexed/Duplicate without canonical/Crawled-not indexed/Discovered-not indexed/Page with redirect/URL unknown/RateLimited/Forbidden/Error;**可提交集合=后 6 态**;复查条件=状态在可提交集且上次检查 >14 天;幂等规则=先 GET urlNotifications/metadata,**404 才 POST publish**(每 URL 永不重复提交);批量 50/块并发块间串行;429 读请求线性退避 (3-n+1)×60s,写请求遇 429 直接退出;sitemap 经 GSC sites/{siteUrl}/sitemaps 列表再解析去重。
**hreflang 簇矩阵输出模板**(notfair):每簇输出矩阵(行=页面,列=自引用/return tag/代码合法/200 可索引/canonical)✅/❌ + 每错误的可直接粘贴 `<link>` 修复块;**单条 return tag 断裂→整簇被忽略(#1 错误,先查)**;经典错码:en-UK(应 en-GB)/下划线 en_US;三载体(head/Link 头/sitemap)只能用一种。
**staging 子域暴露检查**(JeffLi):test./staging./dev./preview./beta./uat. 公开可访问且镜像生产=fail。**llm_review_required 边界标志**:脚本判确定性项,LLM 只在边界时介入(H1 partial 匹配/title 关键词位置>30 字符/meta 有内容即评写作质量)——防幻觉的双层架构。
**统一 SERP ResultType 20 枚举**(openserp):organic/ad/featured_snippet/knowledge_panel/people_also_ask/video/image/news/shopping/local/answer_box/**ai_summary**/related_questions/related_searches/sitelinks/videos/images_inline/calculator/weather;非自然模块独立成 SerpFeature(带 confidence);**absolute 位次=跨页含广告的 1-based 绝对位**;domain_info 分类(gov/edu/news/forum/marketplace/social)。

## C1-C30 全集索引+T 集+红线(openserp·seo-ops·http-status-check·next-sitemap 源码深读,2026-10-09)

读 tigerless-labs/seo-ops `references/checklist/checklist.md`+全部 C1–C30 检查文件+`content/content-checklist.md`+`redlines.md`、karust/openserp `core/result.go`/`core/feature_selectors.go`/`google/features.go`/`extract/llmstxt.go`、spatie/http-status-check `src/ScanCommand.php`/`CrawlLogger.php`、iamvishnusankar/next-sitemap `src/builders/*.ts`。上文已有 C2/C9/C10/C13/C26/C27 深读与 openserp 枚举,此处补**全集与其余检查的判定细节**。

**C 集完整索引(P0/P1/P2,30 项)**:
- 站点级(每站一次):C1(P0)robots 放行全部 AI 爬虫 UA,**三分类清单(训练/检索/用户触发)以 ai-crawlers.yaml 为单一事实源,robots.txt 必须模板生成禁手维护**;C2(P0)sitemap;C3(P0)www/apex×http/https×尾斜杠四变体 301 到唯一规范 host(需真实域名,staging 记 N.A.);C26(P0)无 Accept-Language 跳转;C4(P1)CWV 走 CrUX 75 分位(上线约 28 天才有数据;CrUX API 免费无卡 150 请求/分钟,任意域名可查不需所有权);C5(P1)IndexNow key 文件:文件名=内容=key 串,`{key}.txt` 永久放根;C6(P1)内链无 4xx/5xx(**只报不在 sitemap 内的死链**——与 C2 数据源互补:查"页面实际存在的链接"而非"声明的清单");C7(P2)llms.txt;C28(P2)五安全头(HSTS/CSP/nosniff/X-Frame-Options/Referrer-Policy);C29(P2)URL 卫生(小写/连字符/无裸非 ASCII/无查询参数,扫 sitemap 零额外抓取)。
- 每索引页:C8(P0)自引用 canonical——**双通道查 `<link rel=canonical>` × `Link:` 响应头,不一致=失控**(头通道常见祸首=CDN 规则或给 PDF 配置的外溢);C23(P0)无 noindex(meta+X-Robots-Tag 双查);C27(P0)head 合法;C9(P0)无 JS 完整≥90%;C10(P0)双匿名抓取 diff 空;C11(P1)title≤60/desc≤150 且唯一;C12(P1)JSON-LD(**机器判:解析+基础组(Organization+WebSite)全页全字段+"声明即查"+负扫描;人判:与可见面一致**;AggregateRating 已移出禁用清单——Google 真消费它);C13(P1)soft-404;C14(P1)防闪烁脚本(VWO `hide_element='body'`/Optimize `.async-hide{opacity:0}` 模式扫描+渲染首屏非空;修复优先**服务端 A/B**);C16(P1)`max-snippet:-1, max-image-preview:large`;C24(P1)viewport 含 width=device-width;C17(P2)单 h1+层级不跳;C18(P2)img 显式宽高+alt(**判定是"alt 属性存在"而非"非空"——装饰图 `alt=""` 是正确写法**)+抽样图片字节预算;C19(P2)OG 全集+twitter:card(**og:type×JSON-LD article 类型交叉验证**:声明 Article/BlogPosting/NewsArticle 则 og:type 必须 article)+og 图 1200×630;C20(P2)重定向跳数≤1;C15(P2)SSR 须 CDN 缓存(s-maxage+SWR),SSG 天然过;C25(P2)无混合内容(主动混合内容浏览器直接拦;被动自动升级);C30(P2)每个 a 有文本/alt/aria-label,外链 `target=_blank` 带 rel=noopener。
- 条件触发:C21(P0,`ymyl=true`)YMYL 信任块;C22(P1,多语言)hreflang 互指——**机器部分:每个 hreflang 目标 URL 必须 200 直连**(3xx 即红:引擎静默丢弃非 200 条目);互指闭合+x-default 留人工。

**T 集(内容供给,反向映射到 C)**:T1 品牌拼写+官方社交号(→C12 sameAs);T2 关键页清单+一句话摘要(→C7 llms.txt 选页是内容团队决策);T4 **ymyl 判定(拿不准即标 true——漏标=C21 全禁用)**;T14 图片 alt **按文件名配对**(`images[].file`+alt,不按"图 1/图 2"编号——增删移图会错位);T8 双语成对交付;T9 OG 文案+分享图指定(默认正文首图,不适合作卡片时才指定);T10 date_modified 与实质变更同步(AI 答案偏爱新内容,尤其费率/政策/流程页)。**红线 R1–R8**:R1 agent 不直改生产(PR+人审);R2 YMYL 无专业审核不发布;R3 无真实数据的量产薄页;R4 多域同内容无 canonical 归属;R5 假结构化数据/买评论;R6 买链接/链接农场;R7 cloaking(**"缓存公共壳+客户端个性化"不算;按 UA 定向内容算**);R8 PII 不入店/harness/prompt/第三方 API。

**openserp 工程细节(自建 SERP 抓取时照抄)**:AI Overview 选择器组里 **`div[data-subtree='aimc']` 承载真实 AI Overview,`div[data-mcpr]` 可能只是占位壳**——所以文本选择器优先 aimc,容器命中后再做**占位过滤**:正文为空/"show more"/"show less"/含 "ai overview is not available"(含俄语本地化 "обзор от ии недоступен")/**looksLikeCSS 侦测**(`@keyframes`/`@media`/`} .`/`} #`/`{ `+冒号分号超 20 个=抓到的是内联样式不是内容)全部丢弃。**blockAwareText 的块级标签白名单**:p/br/li/tr/pre/h1-h6/blockquote 换行,**刻意排除 div/section——Google 流式 AI Overview 把每个词包一个 div,不排除则一词一行**。SerpFeatureSelector 带 `SingleMatch`(容器选择器会匹配嵌套子面板,不限制会把一个逻辑模块碎成多个 feature)与 confidence(AI 0.75/PAA 0.8/related 0.6)。**llms.txt 消费端实现**(extract/llmstxt.go):候选顺序 **/llms-full.txt 先于 /llms.txt**(富者优先);**只探站点根**(/blog/post 掝 llms.txt 只会拿到全站索引,不是调用方要的内容);最小 **200 runes** 阈值+HTML 嗅探(`<!doctype html`/`<html`/`<head>`/`<body` 前缀=SPA 壳顶回 200 的常见坑)双防线;失败静默回落正常抓取(**llms.txt 缺失是常态,绝不因此报错**);title 取首个 `# ` 行。

**http-status-check 工程参数**(spatie/php):默认**并发 10 连接**、超时 10s、`track_redirects: true`(Guzzle 开启后靠 **`X-Guzzle-Redirect-History` + `X-Guzzle-Redirect-Status-History` 两个合成响应头**重建完整重定向链,逐跳逐码记录——比只记 final 的爬虫多一倍信息);输出文件**只追加 error 级**(2xx info/3xx comment/其余 error 三色);去重键=statusCode+URL(重定向落到已有页不重复计);主机无响应记 `--- Host did not respond`;选项:`-x` 只爬内链(CrawlInternalUrls vs 默认 CrawlAllUrls)、`--ignore-robots`、basic auth、自定义 UA。

**next-sitemap 工程参数**:`sitemapSize` 默认 **5000**(不是协议上限 50000——工程默认取安全值,大站自动分片为 sitemap-0.xml…+sitemap-index.xml);**字段顺序规范化**:`normalizeSitemapField` 强制 loc→lastmod→changefreq→priority→其余——**对齐 sitemap XSD 的 sequence 顺序**(issue #345:乱序被严格校验器拒);urlset 一次声明**全部五个命名空间**(news/xhtml/mobile/image/video);`escapeHtml` 把**所有非字母数字空格字符**转数字字符引用(比最小转义激进但零漏网);视频条目 `rating.toFixed(1)` 且**逗号替换为点**(本地化陷阱);布尔渲染 yes/no;robots.txt 生成带 `Host:` 指令(Yandex 系)+分组注释头;`generateIndexSitemap` 开时 robots 默认只列 index、`includeNonIndexSitemaps: true` 才追加分片;`trailingSlash` 在 URL 生成层统一(末尾斜杠一致性从源头保证,呼应 C3)。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/schema-markup-generator/references/validation-guide.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/schema-markup-generator/references/validation-guide.md)（Apache-2.0）
- 一手资料：[结构化数据简介](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)、[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)、[结构化数据类型库](https://developers.google.com/search/docs/appearance/structured-data/search-gallery)、[用 JavaScript 生成结构化数据](https://developers.google.com/search/docs/appearance/structured-data/generate-structured-data-with-javascript)、[富媒体搜索结果测试](https://search.google.com/test/rich-results)、[Schema Markup Validator](https://validator.schema.org/)、[schema.org price](https://schema.org/price)
