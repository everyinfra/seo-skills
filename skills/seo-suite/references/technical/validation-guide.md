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

> SEOmator 373 规则/20 类的**完整规则目录**(各类规则 ID/阈值/严重度;Crawlability 38 条、E-E-A-T 16 条、i18n 13 条全展开)见 [audit-rule-catalog.md](audit-rule-catalog.md)。

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

## 技术 SEO 与 Google API 审计深读(claude-seo 深读 2026-10-09b)

### 抓取与索引边界

- **Googlebot 抓取上限**:HTML 只读前 **2MB**、PDF 前 **64MB**(未压缩)——内联 base64 图、超大内联 CSS/JS、膨胀导航可把关键内容/JSON-LD 推出上限;关键内容+结构化数据保持在 HTML 前 2MB。
- 抓取速率**自动调节**(5xx/慢响应即退避),无手动控制(旧 SC 设置 2024-01 已移除);官方爬虫文档 2025-11-20 迁至 developers.google.com/crawling,`googlebot.json` 更名 `common-crawlers.json`(引用旧路径的资料要更新)。
- **AMP**:无独立排名优势;2026-07-01 起 Search 直接把用户送发布商自托管 AMP URL——勿再建议维护 AMP Cache/Viewer/signed exchange;AMP 页按普通页同等内容/动作奇偶/质量要求审计。
- **返回按钮劫持**(`history.pushState/replaceState` 击退 Back,含第三方广告/库脚本注入):2026-04-13 入 spam policies,**2026-06-15 起执法**(手动处置+自动降权)——按 Critical 处理。
- canonical 修正后 Google 可在重复簇中保留**最多 2 周**再评估——修正后短期内 canonical 未变≠修复失败。
- 分页:rel=next/prev 2019 起不再使用;每页**自引用 canonical**;load-more/无限滚动背后必须有可分页 URL。
- **JS SEO 四条边界**(官方 2025-12 澄清):raw HTML 与 JS 注入的 canonical 不一致→Google 可能任选其一(两边必须一致);raw 带 noindex 而 JS 移除→可能仍按 raw 执行(noindex 必须在初始响应里就正确);**非 200 状态页 Google 不渲染 JS**(错误页上 JS 注入的内容/标记对爬虫不可见);JS 注入的时效型 schema(尤其 Product)处理延迟且 Shopping 抓取更不可靠。

### 移动与页面体验

- 移动优先索引 2024 完成;移动版**非硬性要求**,真正风险是**内容奇偶损失**——五项对齐:等价主内容/robots meta 一致/标题描述一致/等价结构化数据/资源可爬;避免需要用户交互才出现的主内容懒加载。
- 侵入式插屏(全页 interstitial、独立 consent 跳转页、持续阻断对话框)与过高广告密度是具名 page-experience 问题;可接受:小横幅、标准 CMS/法务对话框;"read more" 深链:关键内容**加载即可见**(手风琴/tab 后的内容更难入围),不劫持滚动、保留 URL hash。
- **page experience 是指南非单一排名系统**:只有 CWV 直接进排名,HTTPS 轻量信号;SC 独立 Page Experience 报告已下线(用 CWV+HTTPS 报告监控)。

### CWV/CrUX 验证口径

- 阈值(p75 真实用户):LCP≤2.5s / INP≤200ms / CLS≤0.1;辅助:FCP≤1.8s、TTFB≤800ms。**INP 2024-03-12 取代 FID(字段工具 2024-09-09 移除 FID)——任何输出中禁止再引用 FID**。
- CrUX 工程陷阱:**CLS p75 是字符串编码**(须 parseFloat);404=流量不足非鉴权错;直方图末桶无 `end`;日更 ~04:00 UTC、滞后约 2 天;History 周一更、每期=止于周日的 28 天滚动,不合格期密度为 `"NaN"`(字符串)、分位为 `null`——数值运算前先检查;`round_trip_time` 2025-02 取代 effectiveConnectionType;**LCP 子部件指标**(image TTFB/load delay/load duration/render delay,2025-01 新增)用于定位 LCP 瓶颈;字段数据正从 PSI 迁出→字段数据直接查 CrUX API,PSI 主要拿 Lighthouse 实验室数据;报告输出里的 `lighthouse_version` 而非假设最新。

### GSC/GA4 口径与陷阱

- **GSC 记录错误窗口 2025-05-13~2026-04-27**:impressions/CTR/均位不可靠(**clicks 不受影响**;仅向前修复、无回填)——跨该窗口的趋势必须加注,修复后预期出现"展示下降"假象。
- query 维度行会**省略匿名化低流量**,行加总≠全站总数——站点总数只认无维度聚合查询,且仅当 `totals_complete=true` 才可当权威;`discover`/`googleNews` 类型不支持 query 维度与 position 指标。
- **multimodal 筛选**(Lens/Circle to Search/图搜,2026-09-24 起全球铺开)仅 UI+导出,**无已验证的 API type 值——不要编造**;AI Mode 流量已并入标准 Web totals,无法从 totals 拆"经典 vs AI"——AI 可见性看 Generative AI 性能报告(2026-06-03,仅 impressions 无点击/CTR/位次)。
- **sitemap 报告的 submitted 数≠已索引**——逐 URL 的索引真相以 URL Inspection 为准;其 `pageFetchState` 有 11 态(SOFT_404/BLOCKED_ROBOTS_TXT/NOT_FOUND/SERVER_ERROR 等),`googleCanonical` vs `userCanonical` 分开看,`crawledAs` 看实际抓取设备;**`mobileUsabilityResult` 在 API 已弃用**,勿当移动可用性结论。
- 快赢探测口径:**位次 4-10 且高曝光**的 query=优化优先级;SC 数据滞后 2-3 天、保留约 16 个月;SC 可把 TikTok/Instagram/X/YouTube 账号验证为独立属性(只用于 Google Search 表现,不替代平台自有分析)。
- **GA4**:organic 过滤用 `sessionDefaultChannelGroup="Organic Search"`;**AI Assistants 渠道**(2026-05 起,`medium=ai-assistant`;认可源=ChatGPT/Gemini/Claude/Deepseek/Copilot/Grok;不含 Google AIO/AI Mode;Perplexity 未确认)——多数 AI 会话无 referrer 落 **Direct**,该渠道系统性低估,仅向前无回填。
- **DMA/Consent Mode v2**:2024-03-07 起欧盟 CTR 跨界对比不同口径;GA4 欧盟默认拒绝 consent 时计数保守(转化建模补差额);3P cookie 弃用 2024-07 已撤回——别再推"无 cookie 归因"为优先项;Privacy Sandbox 大批 API 2025-10-17 退役(CHIPS/FedCM/Private State Tokens 留存)。

### 配额与鉴权速查

- PSI 240 QPM/25K QPD(API key);CrUX+History **共享** 150 QPM;GSC Search Analytics 1,200 QPM/站、30M QPD/项目;URL Inspection 600 QPM、**2,000 QPD/站**;Indexing API **200 publish/天**(太平洋午夜重置;batch 逐条计数,100 条 batch=100 配额);GA4 令牌制:25K/天、5K/时、10 并发(`returnPropertyQuota:true` 监控;简单报表 ~1-10 token、复杂 ~100)。
- 429 处理:指数退避(1/2/4/8/16s)+随机抖动,最多 5 次;响应带 `Retry-After` 时优先用它。403=GSC/GA4 权限(SA 邮箱未加进属性;Indexing API 要求 SA 是 GSC **Owner**,只读分析 Full 即可);404 于 CrUX=流量不足非凭据问题。
- Indexing API 官方适用面:仅 **JobPosting** 与 **BroadcastEvent(嵌 VideoObject)**——普通 URL 少量用 URL Inspection、大量用 sitemap;`URL_DELETED` 仅限永久下线(404/410)。

### 打分纪律

- 审计分**只给测过的项**:各类目分=该类目通过检查占比(按严重度加权),未测量的类目报"未测量",**永不给数字**;每个分数背后列出对应检查项。

## 脚本级审计判定(Agentic-SEO-Skill 深读 2026-10-09b)

> 来源:[Bhanunamikaze/Agentic-SEO-Skill](https://github.com/Bhanunamikaze/Agentic-SEO-Skill)(16 子技能+89 脚本)逐脚本源码深读。本节收录其**硬编码阈值与判定公式**,吸收时注意:多数评分是启发式代理指标,不是 Google 已证实信号;引用时标注"脚本判定"而非"排名事实"。已另吸收的 reference_freshness.py / indexability_matrix.py 不在此重复。

### 全站审计权重与置信纪律

- 全站健康分权重:Technical 25% / Content 20% / On-Page 15% / Schema 15% / CWV 10% / Images 10% / AI Readiness 5%(其 SKILL.md 自称唯一来源,子文件为镜像——多文件同步是漂移风险点)。
- 置信标签纪律(值得沿用):脚本跑通=**Confirmed**;脚本失败仅靠 LLM 分析=**Likely**;token/API 环境故障是**环境限制,不是站点缺陷**。finding 一律带 severity+confidence+evidence+fix 四字段。
- 严重度换算分(其 github 侧脚本):`score = max(0, 100 − Critical×20 − Warning×8)`;评级带:≥90 Excellent / ≥70 Good / ≥50 Needs Improvement / ≥30 Poor / 其余 Critical。

### readability.py(纯 Python,无 NLP 依赖)

- Flesch=206.835−1.015×(词/句)−84.6×(音节/词);FKGL=0.39×(词/句)+11.8×(音节/词)−15.59;音节=元音组启发式(去尾 e);阅读速度 200 wpm。
- 分级带:FRE≥80 易(6 年级)/ 60–80 标准(7–8)/ 40–60 难(9–12)/ 20–40 很难(大学)/ <20 极难。
- 触发阈值:均句长>25 词警告(目标 15–20);FRE<40 警告、<60 仅提示;复杂词(≥3 音节)占比>20% 警告;均段>5 句警告;<300 词标薄内容。
- 长句改写器只取**前 5 条最长句**、输出前 3 条,且带导航噪声过滤器(nav 短语、≥2 换行、≥25 词且独特比>0.85 的关键词罗列)——防止把菜单/组件文本当改写对象。
- 诚实条款(其自注):Flesch **不是**排名因子(Mueller 确认;Yoast v19.3 降权);词数下限是**选题覆盖地板**非目标(首页 500 / 服务页 800 / 博文 1500 / 产品 300+(复杂 400+) / 本地页 500–600)。

### eeat_signal_checker.py

- 百分制拼分:作者/byline 信号 20 + 资质词命中 min(20, n×7) + 第一手经验词命中 min(20, n×7) + 编辑政策链接 15 + 信任链接(about/contact/privacy/terms)15 + 外部引用 min(10, n×2)。
- 正则即判定:资质词=phd/md/certified/licensed/reviewed by/fact-checked/award-winning…;经验词="we tested"/"hands-on"/"case study"/"we measured"/"original research"…。
- **局限要写进报告**:这是表层字符串信号,可被模板化堆砌,也识别不出真实资历;缺失时只能报"未见信号",不能报"无 E-E-A-T"。

### citation_readiness.py(AI 引用就绪)

- 事实声明识别正则:含百分比/\$金额/19xx–20xx 年份/或"study|research|according to|found that|largest|first|only|most"的句子。
- 拼分:声明覆盖率×35(覆盖率=min(1, 引用容量/声明数);引用容量=外链+`<cite>`/blockquote+脚注链接)+ 高信任外链 min(20, n×5)(仅 gov/edu/who.int/nih/cdc/worldbank/oecd/wikipedia)+ 作者信号 15 + sameAs 条目 min(20, n×5) + canonical 存在 10。
- 判定:声明数>引用容量=警告"声明多于可见引用";无高信任域=Info 而非 Warning。

### answer_block_scanner.py(精选摘要/AEO 格式)

- 直接答案块=问题式标题(以 what/why/how/… 开头或以?结尾)后的**下一个兄弟 p/div**,词数 **20–70**(子技能口径的目标带更窄:40–55 词;列表摘要 5–9 项、每项≤12 词;表摘要≤4 列)。
- 定义段=20–80 词且匹配"X is/are/refers to/means + 20–220 字符";列表≥3 项、表≥2 行才算结构信号。
- 分=min(100, 直接答案×20 + 定义×12 + 列表×10 + 表格×12)——纯计数打分,只能横向对比,不能当"摘要捕获概率"。

### content_decay_detector.py(GSC CSV)

- 衰减判定:前后期点击跌幅 ≥20%(可调 `--decline-threshold`),且**任一期曝光 ≥100**(过滤噪声);无 `--split-date` 时自动取日期中位数分期。
- 触手可及(striking-distance)关键词:加权均位=Σ(position×impressions)/Σimpressions 落在 **4–20** 且曝光≥100;输出按"位次升序→曝光降序"排,截前 200。
- 注意口径:GSC position 是 impressions 加权均值,不是最差/最好位次。

### llms_txt_checker.py

- 质量分:标题(# 开头)20 + 描述(> 引用)20(>50 字符再+5,<20 字符提示)+ `##` 分节 15(≥3 节+5)+ 链接(`- [标题](url): 描述`)20(≥5 条+5、≥10 条再+5)+ 内容>200 字符 5,封顶 100。
- 同时探测 `/llms-full.txt`(可选扩展版);404 与请求异常分开记录。

### 程序化/闸门类阈值(子技能文档口径)

- 地点页:≥30 页触发警告(要求 60%+ 独特内容)、≥50 页**硬停**(需人工论证);未审页 ≥100 警告、≥500 硬停;独特内容 <40% 标薄、建议 <30% 硬停;单页 <300 词复核。
- 发布节奏:50–100 页一批,观察 2–4 周再扩;>60% 内容为共享模板即罚则风险画像(对照 2024-03 Scaled Content Abuse 并入核心算法、2025 手动处置浪潮)。
- 图片分级阈值:缩略图目标<50KB/警>100/危>200;内容图<100/警>200/危>500;hero<200/警>300/危>700;alt 长度 10–125 字符;**首屏/LCP 图禁 lazy-load**,加 `fetchpriority="high"`。
- sitemap:单文件 <50k URL(协议限);`priority`/`changefreq` 已被 Google 忽略(Info 级);lastmod 全同=低信号;含 noindex/重定向 URL=High。
- 内链:孤儿=入链 ≤1;入链<3 的页面占爬取页 ≥10% 警告;单页出链>100 警告;内链 nofollow=Info(浪费权重);柱页目标入链 10+。
- schema 状态表(口径更新 2026-10-10):**FAQPage 富结果 2026-05-07 全站退役**(存量标 Info 不标 Critical,不建议删除或为 SERP 新增,真问答页用 QAPage);HowTo(2023-09 移除)、SpecialAnnouncement(2025-07 弃用)、CourseInfo/EstimatedSalary/LearningVideo/ClaimReview/VehicleListing(2025-06 退役)、PracticeProblem(2026-01 起 GSC 移除)一律**不再推荐**;**Dataset 未退役**(仅被 Dataset Search 消费,勿当被杀);Book Actions 弃用又回滚(仍可用,历史注记);详见 deprecated-signals.md。

### GEO 判定口径(引用时标"行业研究,非官方")

- 最优可引用段落 **134–167 词**;直接答案前置 40–60 词;AI 爬虫**不执行 JS**(SSR 是 GEO 前提);其引用的"品牌提及相关性≈外链 3 倍""YouTube 提及相关性 ~0.737 vs DR ~0.266"来自 Ahrefs 2025-12 7.5 万品牌研究——是单供应商相关性研究,写报告时须如此标注。

## 性能/安全与 SEO 交叉的爬虫审计阈值 (siteone-crawler 源码深读 2026-10-09b)

> 来源:[janreges/siteone-crawler](https://github.com/janreges/siteone-crawler)(Rust,MIT)`src/analysis/` 22 个分析器逐行深读的**性能与 HTML 质量部分**。工具判定口径,非 Google 官方信号;对照上文 seonaut 的 DOM>1500/TTFB>800ms 一套,两套阈值并存时取更严者并注明出处。安全头/缓存/DNS 阈值见 [robots-txt-reference.md](robots-txt-reference.md) 与 [http-status-codes.md](http-status-codes.md) 同日节。

### 响应速度分级(Slowest/FastestAnalyzer)

- 请求耗时着色(utils.rs 硬编码):**≥2s 红 / ≥1s 品红 / ≥0.5s 黄 / <0.5s 绿**——比 seonaut 的 TTFB>800ms 宽松,因为这是全文档下载耗时而非 TTFB。
- 慢页统计(仅 HTML 页):**默认 ≥3.0s 计为"slow"**(CLI 可调),分级 0=OK / 1–2=notice / 3–5=warning / **≥6=critical**;最慢 TOP 20 列表(下限 0.01s 过滤噪声)。快页 TOP 20 取 ≤1.0s 的 200 HTML 页,做前后对比基线用。
- 注意口径:这是服务端视角的爬虫下载时间,不含渲染;CWV 判定仍以 CrUX p75 为准(见上文 CWV 节),两套不可互换。

### HTML 质量与结构阈值(BestPracticeAnalyzer,200 HTML 页逐页跑)

- **DOM 深度**(从 `<body>` 起算):**≥30 层 warning / ≥50 层 critical**。比 seonaut 的"DOM>1500 节点"口径不同(深度 vs 广度),深层嵌套主要伤解析与样式计算。
- **内联 SVG**:单个 >**5KB(5120B)**=warning(建议外链);重复 >**5 次**且 >**1KB**=warning(用 MD5 去重);XML 解析失败=critical。跳过含 `&#x22;`/`&#x27;` 的(代码示例里的转义 SVG)。
- **标题/描述重复度**:**同一 `<title>` 占全站页面 >10% 且出现 >1 次**=warning(输出 TOP 10 重复表);meta description 同口径 **10%**,且**空描述也算一个值参与统计**——大规模空描述会直接触发。
- **H1 与标题层级**:无 `<h1>`=**critical**;多个 `<h1>`=**critical**;跳级(如 h1 后直接 h3,或无上级直接出现 h4)=warning;全页无任何 heading=notice。统计时**跳过 svg/script/style/template/noscript 内的 heading**(外来内容里的 h1 不算数)。
- 属性值未加引号(`href/src/content/alt/title`)=warning(数值、转义、`<astro` 开头跳过)。
- 电话号码非 `tel:` 链接(≥8 字符,剥掉 script/style 后匹配四种格式:国际带空格/国际无空格/US 括号/连字符)=warning——转化视角非 SEO。
- **压缩与图片格式**(站级):内部 HTML 页 `Content-Encoding` 不含 `br`(大小写不敏感,逗号分隔多编码)=warning;站内 200 图片无 `image/webp`=warning(**有 AVIF 则豁免**,文案明示"更现代格式");无 `image/avif`=warning(单独项)。

### 可访问性即 HTML 质量(AccessibilityAnalyzer,只查 200 HTML 页)

- `<img>` **缺 alt 属性**=warning;**`alt=""` 是合法装饰写法,不报**(用解析 DOM 判,不用正则——" alt=" 出现在别的属性值里是经典误报)。
- `<html>` 无 `lang` 或 `lang=""`=**critical**(该分析器唯一的 critical 级页面项之一)。
- 无 `<main>` 或 `role="main"`=warning(破坏 skip-to-content);**原生 `<nav>/<header>` 不补显式 role 不算错**(ARIA 第一原则:优先原生语义)。
- 表单控件无可访问名称=warning:认 `aria-label`/`aria-labelledby`/`title`/非空 `placeholder`(仅 input/textarea,select 不认)/`<label for>`(有文本)或包裹式 `<label>`;**hidden/aria-hidden/内联 display:none/visibility:hidden 的控件跳过**(inline style 按真实 CSS 语法解析:注释、引号、`!important`、转义、多关键字值都处理)。
- 图标式链接/按钮无可访问名称=warning:有可见文本、`aria-label`/`title`、嵌套 `img alt`、`svg <title>`、后代 aria-label 之一即通过——**有文字的普通链接不报**(防大规模误报)。
- **结构缺陷替代 W3C 全量校验**:重复 `id`、悬空 `aria-labelledby/-describedby/-controls/-owns`、`<label for>` 指向不存在 id=warning。其注释明说:这些是静态可查且真正破坏 a11y/脚本/锚点的缺陷,**"整页 W3C 是否有效"本身 Google 说过不是可靠信号**——与本文"三层验证"的务实立场一致。

### 渲染后才可见的缺陷(BrowserConsoleAnalyzer,仅 --browser 模式)

- 每页计数 console error/warning、未捕获 JS 异常、失败子请求、安全违规;**有任一类问题即计"问题页"**(warning-only 页不得被掩盖成 OK);分级 0=OK / 1–2=notice / 3–5=warning / ≥6=critical。
- 代表消息优先级:渲染失败 > console error > 未捕获异常 > console warning > 截图失败(截前 120 字符)。
- 审计意义:这是"raw 与 rendered 差异"的运行时证据源,配合 C9(禁 JS 完整性 ≥90%)一起用;纯 HTTP 爬取看不到这些,报告里要注明口径。
