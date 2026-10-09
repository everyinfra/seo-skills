# 批 02-04 提取档案

## aFarkas/lazysizes(17711★)
爬虫检测核心:`supportScroll = ('onscroll' in window) && !/(gle|ing)bot/.test(navigator.userAgent)`(UA 含 google/bing bot 即 unveil 全部图);expand 动态默认 `clientHeight>500&&clientWidth>500?500:370`(建议 300-1000);expFactor 1.5(1.5-4)/hFac 0.8(0.4-1)/minSize 40/throttleDelay 125(66-200)/loadMode 2;LQIP blur(5px)+400ms;防 CLS:data-sizes=auto+固有比例容器 padding-bottom;noscript 模式+1px GIF 占位;native-loading 插件检测 `'loading' in HTMLImageElement.prototype` 自动切原生;**AI 爬虫盲区**:正则只认 google/bing bot,不执行 JS 的 AI 爬虫拿到的是 SSR 里的 data-src。

## zubair-trabzada/geo-seo-claude(10972★)未吸收三模块
**GEO 复合分**:GEO=Citability×0.25+Brand×0.20+EEAT×0.20+Technical×0.15+Schema×0.10+Platform×0.10;档位 90/75/60/40/0。citability 内部:citability 35%+brand mention 30%+crawler access 25%+llms.txt 10%。**自包含最优区间**:134-167 词(10 分)/100-200(7)/80-250(4);代词密度<2%(8 分);≥3 专有名词(7 分);统计密度:百分比各 3 分上限 6/美元额各 3 上限 5/带单位数字各 2 上限 4。技术分:SSR 25/meta 15/crawlability 15/安全头 10/CWV 10/移动 10/URL 5/响应头 5/其他 5;安全头扣分:无 HTTPS -30/无 HSTS -10/无 CSP -10/无 XFO -5/无 X-Content-Type-Options -5/无 Referrer-Policy -5/无 Permissions-Policy -3。Schema 10 组件:Org/LocalBusiness 20(**3+ sameAs 满分**)/Article 15(含 dateModified 满分)/Person 15(jobTitle+knowsAbout 满分)/sameAs 15(**5+ 含 Wikipedia 满分**)/speakable 10/Breadcrumb 5/WebSite+SearchAction 5/无废弃 schema 5/全 JSON-LD 5/零错误 5;JS 注入 schema 对 AI 爬虫不可见标旗。**爬虫三层矩阵**:Tier1 必须 allow(GPTBot/OAI-SearchBot/ChatGPT-User/ClaudeBot/PerplexityBot)/Tier2 建议(Google-Extended/GoogleOther/Applebot-Extended/Amazonbot/FacebookBot)/Tier3 策略(CCBot/anthropic-ai/cohere-ai 仅训练;Bytespider 建议封);评分 Tier1 占 50%(每个 20 分)。**Cloudflare Managed robots.txt 检测**:live 响应含 `# BEGIN Cloudflare Managed content`=边缘注入封禁(站长文件里看不到),须关 Security→Bot traffic→block training。**Content-Signal 草案**:`Content-Signal: ai-train=no, search=yes, ai-retrieval=yes`(合法 key 仅 ai-train/search/ai-personalization/ai-retrieval)。**geo-prospect CRM**:5 态 lead→qualified→proposal→won→lost;审计分<55 自动建议 proposal;输出 Committed MRR/Pipeline Value。

## garmeeh/next-seo(8521★)
14 稀有 JSON-LD 字段(→已入 schema-templates 完整清单);Course 单体/列表双模式;CreativeWork 规则有 headline 不发 name,Article 缺 dateModified 用 datePublished 回填;EmployerAggregateRating ratingCount 与 reviewCount 至少一否则 throw;ImageObject contentUrl+creator/creditText/copyrightNotice/license 至少其一;MerchantReturnPolicy 独立顶层类型三组运费;ProfilePage 含 agentInteractionStatistic;Quiz Flashcard 结构;VacationRental containsPlace+8 图+geo。

## goenning/google-indexing-script(7711★)
(→已入 validation-guide 九态状态机全文)补充实现细节:缓存文件 .cache/<siteUrl 转名>.json,URL 转义 http://→http_、/→_;JWT scope=webmasters.readonly+indexing;密钥查找顺序 自定义路径→./service_account.json→~/.gis/;环境变量 GIS_CLIENT_EMAIL/GIS_PRIVATE_KEY/GIS_URLS/GIS_QUOTA_RPM_RETRY;fetchRetry 默认 5 次仅 status>=500;sitemap 先 GSC sites/{siteUrl}/sitemaps 列表再 sitemapper 解析 Set 去重。

## vercel/next-forge(7671★)
JSON-LD XSS 转义五字符(→已入 schema-templates);createMetadata 工厂 lodash.merge;OG 图固定 1200×630;metadataBase 取 VERCEL_PROJECT_URL 按 NODE_ENV 切协议;formatDetection.telephone:false;**反面教材:[locale] 目录下 sitemap 只产无语言后缀单一 URL 无 hreflang alternates**;middleware matcher `js(?!on)` 负向前瞻防误排 JSON。

## TheCraigHewitt/seomachine(7487★)
三分析器全文(→已入 scoring-rubric);补充:**search_intent_analyzer**:导航信号词权重 3(login/sign in/official/portal),信息/交易/商业各 +2;疑问句开头(what|why|how…)+3;`N+\s+(best|top)` 正则→商业 +3;SERP 特征映射(shopping→交易+3/local+2/ads+1/snippet·knowledge·PAA→信息+2/carousel→商业+1);**次意图判定=与主意图置信差<15 个百分点则输出混合意图**。**AI 引用 5 层+6 类 prompt**(→已入 brand-mention)。**context/ 12 文件客户上下文模板**(brand-voice/internal-links-map 8 段/writing-examples/ai-citation-targets/reddit-strategy)。**/priorities**:quick win=GSC 近 30 天排名 11-20 的词;潜在点击按"推到位置 5-7"估算;EXISTING UPDATE(审核前 5 竞文补 gap)vs NEW CONTENT(研前 10 竞文按竞品定词数)。

## Blazity/next-enterprise(7463★)
唯一可借=按页(扣全局共享后)的 raw/gzip JS 预算进 CI 回归(build-manifest 逐页计算写 __bundle_analysis.json 供 Actions 对比);K8s 健康检查别名模式(rewrites /healthz→/api/health)。

## GetPublii/Publii(7328★)
sitemap 生成=遍历渲染产物读 index.html 字符串包含 noindex 决定收录(静态导出站可复用);图片 sitemap 扩展 xmlns:image,每图 image:loc+image:title(alt 包 CDATA);**外链图片默认剔除**(sitemapAddExternalImages 开关);lastmod 格式 YYYY-MM-DDTHH:mm:ssZ;永久排除清单(assets/feed.xml/feed.json/_redirects/.htaccess/404/搜索页);三种编辑器各一套正文图片抽取正则;**分页页 noindex,follow**(三类粒度开关 homepage/tag/author);**noindex/nofollow 页不输出 canonical**(除非自定义);canonical 剥 index.html 补尾斜杠;json-ld 非文章页 Organization+8 平台 sameAs,文章页 Article(image 用 image-size 实测宽高;作者页禁用且无个人网站时省略 author url);输出前 `<`→`\\u003c`。

## chrisvfritz/prerender-spa-plugin(7262★)
已弃用;渲染触发三选一**禁止并用**(renderAfterDocumentEvent 官方推荐/renderAfterElementExists/renderAfterTime 标 NOT RECOMMENDED);渲染器选型:Puppeteer 适合几百页要准确/jsdom 适合成千上万页质量要求低;skipThirdPartyRequests 默认 false;maxConcurrentRoutes 默认 0 无上限;**任一路由失败则 compilation.errors 整体报错**(构建即红);postProcess 惯例 route=originalRoute 丢弃重定向;Vue2 需同 id 或 data-server-rendered 防双份渲染内容。

## tensorchord/Awesome-LLMOps(5955★)
仅两条思路:RagTune("检索层的 EXPLAIN ANALYZE")+semantic-coverage(UMAP 可视化 RAG 知识盲区)——AI 检索诊断的概念参照;NativePort 的"带日期 leaderboard+公开方法论"与证据保鲜同构。

## GoogleChrome/rendertron(5951★)/aimeos(5462★)/fusuma(5356★)/react-snap(5118★)/astro-paper(5101★)
(→已入 rendering-seo 三件套全文)补充:aimeos 的 SHOP_MULTILOCALE={locale}/ 路由前缀与 SHOP_MULTIROUTE 顶级 URL 形态开关(电商 hreflang 场景);**店铺自带 MCP 端点**(/admin/{site}/mcp,Sanctum/OAuth,供 Claude/ChatGPT 远程连接)——AI 电商的 agent-readiness 实例;管理端 AI 三键(OPENAI/DEEPL 翻译/REMOVEBG)。fusuma:og:image 生成以已配置 meta.url 为前提——跳过。react-snap anatomy 决策矩阵(renderToString/JSDOM/headless 三选)+路由发现三式(手列/程序/爬取,爬不到的须手补+ignore 列表)。
