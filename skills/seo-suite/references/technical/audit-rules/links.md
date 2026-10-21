# 审计规则目录 · Links

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### Links(27 条,权重 8%)

内链 404/410/5xx=fail(其他 4xx 通过);外链可达性=warn(只查前 20 条,不缓存);无内链=warn;nofollow 滥用=warn;泛化锚文本("click here"/"read more"/"link")=warn;`links-depth`(**点击距离 ≤3**,crawl);死端页(无出链)=warn;HTTPS 页链 HTTP=warn;**外链 >100=warn**(`links-external-count`);**页内链接总数 >100=warn、>300=fail**(`links-excessive`);空/javascript:/畸形 href=warn;tel:/mailto: 格式=warn;重定向链(**1-2 跳=warn,≥3=fail**);`links-localhost`(127.0.0.1=fail)/`links-local-file`(file://=fail);断锚点(#id 无匹配)=warn;`links-onclick`(onclick 导航替代 href=fail);href 首尾空白=warn;非 HTTP 协议(ftp:/intent:/chrome:)=warn;**crawl 专属入链族 8 条**:inbound-all-nofollow(全 nofollow=零权重流入,洞见级)/inbound-mixed-follow(有follow有nofollow=不一致)/inbound-low-quality(入链全 nofollow 或全来自被 canonical 走的页)/inbound-anchor-text(全部入链锚文本<2 字符或泛化)/nofollow-internal(同主机链接禁 nofollow)/weak-inbound(**非入口页须 >1 条 dofollow 入链**)/chrome-inbound(**至少 1 条入链在 nav/header/footer 之外**——正文链才算票)/orphan-pages(真孤儿由 crawl-sitemap-orphan-urls 配合判)。

**解释层(16 条;ID 未公布原文的标 [待核];入链族 8 条的 5 条并入 links-weak-inbound/links-chrome-inbound 陈述)**

#### links-broken-internal
- 源表:warn/fail · 权重 1。逐个内链目标 HEAD(失败再 GET):404、410、5xx=fail;无应答=warn;其他 4xx 通过。工具约定。建议优先级 high。
**依据**: 站内部分 URL 返回 404 本身不会让站点在 Google 搜索中受损([Google 2011 博文](https://developers.google.com/search/blog/2011/05/do-404s-hurt-my-site));Google 不索引返回 4xx 的 URL([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors))。修它是为了用户路径与内链指向有效页。"撞 404 会降低抓取意愿"无出处,已删。核对 2026-10-18。
**判据**: 通过=内链目标全部 2xx/3xx。失败=任一目标 404/410/5xx。刻意 410 的下线页不算错,但内链应删除。
**执行**: `CRAWL` 后跑 J6,每行"来源页 -> 死链";site_audit 不检查链接目标。
**修复**: 目标还在就修 href;目标没了就 301 到最近亲页或删链接;批量死链先查迁移映射表。
**关联**: crawl-pagination-broken、i18n-hreflang-to-broken;[link-architecture-patterns.md](../link-architecture-patterns.md)、[http-status-codes.md](../http-status-codes.md)

#### links-redirect-chains
- 源表:warn/fail · 权重 1。抽样至多 20 个内链目标:1-2 跳=warn,≥3 跳=fail。工具约定。建议优先级 medium。
**依据**: Googlebot 一般最多跟 10 跳,网址检查工具不跟随重定向([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors))。1-2/3 跳的分档是工具约定。内链零跳直指最终 URL 省掉每次访问的往返。核对 2026-10-18。
**判据**: 通过=内链直指 200 页。警告=1-2 跳。失败=≥3 跳(本套件 `REDIR`:>2 跳 WARN,>5 跳 CRITICAL)。
**执行**: `CRAWL` 后跑 J7 列出指向重定向的内链;单个目标用 `REDIR 目标URL` 看链长。
**修复**: 内链模板直指最终 URL;服务器层把链条改写为一步到位。单跳 http→https 或加尾斜杠可排后修。
**关联**: redirect-loop、crawl-canonical-redirect;[redirects-canonical.md](../redirects-canonical.md)

#### links-depth
- 源表:warn/fail · 权重 4 · 需 `--crawl`。真实点击距离(从爬取入口算);修复建议是重要页 3 击以内。工具约定。建议优先级 medium。
**依据**: 无搜索引擎公布的点击深度阈值;Google 只说链接是发现页面的主要方式,在意的页面至少要有一个站内链接([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable))。"≤3"是工具约定。核对 2026-10-18。
**判据**: 通过=重要页深度 ≤3。失败=重要页深度 >3(存档、法律页可深)。
**执行**: `CRAWL` 后跑 J5,或看 `GRAPH` 的深度直方图(>3 层占比);深度从种子 URL 按内链 BFS 计算。
**修复**: 重要页从导航/分类页/相关推荐多点接入;扁平化信息架构,而不是往首页堆链接。
**关联**: crawl-isolated-url、crawl-sitemap-orphan-urls;[link-architecture-patterns.md](../link-architecture-patterns.md)

#### links-localhost
- 源表:fail · 权重 8。链向 localhost、127.0.0.1、0.0.0.0 或常见开发端口(:3000、:8080、:5173 等);同族 `links-local-file`(fail · 权重 8)抓 file:// 与 /Users/、/home/、C:\ 开头的 href/src。工具约定。建议优先级 high。
**依据**: 这类地址在访客与爬虫端都不可达,属发布事故;无需搜索引擎规则佐证。核对 2026-10-18。
**判据**: 通过=无开发环境地址。失败=任一 href/src 指向上述地址。
**执行**: G5 有输出即失败;全站对 `CRAWL` 产出的 URL 清单循环跑 G5。
**修复**: 查环境变量与绝对 URL 拼装基准;上线检查清单加 localhost/file:// 扫描。
**关联**: links-broken-internal

#### links-anchor-generic
- 名称/类型: 泛化锚文本 —— warning · 优先级 medium · 输出 WARN(源表 ID `links-anchor-text`,warn;"click here"/"read more"/"link")
**这意味(what)**: 站内链接的锚文本是泛化词——click here/read more/link 一类,不含目标页主题信息。
**为什么(why)**: Google 说好的锚文本应具体、简短、与所在页相关,并举 "Click here" 为需要改得更具体的例子([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable),核对 2026-10-21);屏幕阅读器用户常按链接列表浏览,一列 "read more" 无法区分。批量泛化锚多半是模板省事,不是文案选择。
**触发(trigger)**: 锚文本命中泛化词表(click here/read more/link/more/here 等[词表源表未公布,待核])且为普通文本链即 warn;图标链接的可访问名(alt/aria-label)即其锚文本,同口径计。
**不修的条件(caveat)**: 锚文本不(直接)决定目标页排名,然而它是零成本的相关度信号,所以一般建议锚含目标主题词。但 CTR 导向的行动按钮("免费试用")是转化文案,别为 SEO 破坏——链接补 aria-label 带上主题即可。
**修复(fix)**: 模板把目标页标题注入锚("阅读:SEO 审计入门");纯图标链接补 aria-label;全站泛化锚 lint 进 CI。
**关联(seealso)**: links-weak-inbound;[link-architecture-patterns.md](../link-architecture-patterns.md)、[semantic-html.md](../semantic-html.md)

#### links-nofollow-internal
- 名称/类型: 内链 nofollow —— warning · 优先级 medium · 输出 WARN(源表 warn;同主机链接禁 nofollow)
**这意味(what)**: 指向同主机的内链被加了 rel=nofollow。
**为什么(why)**: nofollow 的语义是"不为这个链接背书",用在自家内链上是自我否定;且 Google 时任反垃圾负责人在 2009 年的博文里说,nofollow 链接分走的那份 PageRank 不再转给同页其余链接,改动早于该文一年多,并建议站内链接不要用 nofollow([博文](https://www.mattcutts.com/blog/pagerank-sculpting/),核对 2026-10-21;文中自称用「经典 PageRank」简化模型,是 2009 年的口径)——"用内链 nofollow 调节权重流向"的动机站不住(口径见 [deprecated-signals.md](../deprecated-signals.md))。剩下的成因几乎只有误加:CMS 默认、UGC 模板全局套用。
**触发(trigger)**: 同域 `<a>` 带 rel=nofollow 即 warn。
**不修的条件(caveat)**: 内链 nofollow 不带来任何收益,然而删除它也无即时排名变化(权重会计在引擎内部),所以一般建议作为卫生项清理。但 UGC 区(论坛/评论)给用户发布的外链加 nofollow/ugc 是反 spam 标准做法,不属"内链"。
**修复(fix)**: 模板移除内链 nofollow;UGC 外链区保留 ugc/nofollow;抓取预算问题走 robots.txt,索引控制走 noindex/canonical。
**关联(seealso)**: links-external-many、url-search-indexed;[robots-txt-reference.md](../robots-txt-reference.md)

#### links-external-many
- 名称/类型: 外链过多 —— warning · 优先级 low · 输出 WARN(源表 ID `links-external-count`,warn,外链 >100;同族 `links-excessive`:页内链接总数 >100 warn、>300 fail;site_audit 的 `[INFO] links: N 链接 >100` 对应后者,按 a 标签总数计)
**这意味(what)**: 单页指向外部的链接超过 100 条。
**为什么(why)**: 现行 Google 链接文档没有链接数量上限([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable),核对 2026-10-21),100 是工具约定。外链很多时,先查是不是链接列表或资源页失控;Google 没有说过「每页链接越多每条越弱」,本套件不把这当理由。
**触发(trigger)**: 统计页内出站(跨域)`<a href>` 数;>100 即 warn(nofollow 是否计入的口径[待核])。
**不修的条件(caveat)**: 外链数量不影响本页排名,然而它稀释每条链接的相对价值,所以一般建议长资源页分栏分页。但学术引文页/目录站的百条外链是内容真实形态,分页反而伤可用性。
**修复(fix)**: 长资源页按主题分页;非核心外链区 nofollow/ugc 收口;付费与联盟位用 rel=sponsored。
**关联(seealso)**: links-nofollow-internal;[link-architecture-patterns.md](../link-architecture-patterns.md)

#### links-dead-end
- 名称/类型: 死端页 —— warning · 优先级 medium · 输出 WARN(源表 ID `links-dead-end-pages`,warn;无出链)
**这意味(what)**: 页面没有任何 follow 出链——用户与爬虫到这里都走不动了。
**为什么(why)**: 死端页截断浏览路径(用户只能回退)与爬行路径(引擎无法从它继续发现);与孤立 URL(无入链)互为镜像——一个进不来,一个出不去。转化终点页(支付成功/退订确认)是唯一常见合理形态。
**触发(trigger)**: 页面 follow 出链计数=0 即 warn(爬取入口与纯工具页的豁免口径[待核])。
**不修的条件(caveat)**: 死端不(直接)影响本页排名,然而它浪费一次"带用户/引擎去别处"的机会,所以一般建议补相关推荐与返回路径。但流程终点页刻意零出链是转化设计,记豁免。
**修复(fix)**: 补相关内容推荐/面包屑/返回分类;结算页类模板确认其 noindex 与出链策略是刻意设计。
**关联(seealso)**: crawl-isolated-url、links-depth;[link-architecture-patterns.md](../link-architecture-patterns.md)

#### links-weak-inbound
- 名称/类型: 弱入链(入链族核心) —— warning · 优先级 medium · 输出 WARN(源表 warn;crawl 专属;非入口页须 >1 条 dofollow 入链)
**这意味(what)**: 非爬取入口的页面只有 ≤1 条 dofollow 入链——技术上可达,权重与健壮性上贫血。
**为什么(why)**: 单链页很脆弱:唯一那条入链被改版挪掉,它就成了孤立页(Google 发现页面主要靠链接,见 crawl-isolated-url)。「入链少排名天花板低」是工具约定,无搜索引擎文档。本规则是入链族 8 条的核心判定,同族同构维护:inbound-all-nofollow(全 nofollow=零权重流入,洞见级)/inbound-mixed-follow(follow·nofollow 混杂)/inbound-low-quality(入链全来自被 canonical 走的页)/inbound-anchor-text(全部入链锚 <2 字符或泛化)——四条都是对同一入链图不同切面的质量计数,阈值见本节表,不逐条扩写。
**触发(trigger)**: 1) crawl 构建 dofollow 入链图;2) 非入口页 dofollow 入链数 ≤1 即 warn。
**不修的条件(caveat)**: 入链数不(直接)决定排名(质量重于数量),然而 1 条链是脆弱性指标,所以一般建议关键页 ≥2-3 条来自不同区域。但刚发布未及内链的新页与法律页是过渡态/低需求态,可豁免。
**修复(fix)**: 分类页/相关推荐/正文上下文多点接入;重要页至少导航与正文各一条(见 links-chrome-inbound)。
**关联(seealso)**: links-chrome-inbound、crawl-isolated-url;[link-architecture-patterns.md](../link-architecture-patterns.md)

#### links-chrome-inbound
- 名称/类型: 仅有导航区入链 —— warning · 优先级 medium · 输出 WARN(源表 warn;crawl 专属;至少 1 条入链在 nav/header/footer 之外)
**这意味(what)**: 页面的全部入链都来自导航 chrome(导航/页头/页脚),没有任何一条来自正文区。
**为什么(why)**: 导航链接全站同款;正文里的上下文链接才说明「这个主题下值得读这页」,也给锚文本提供语境(Google 建议锚文本具体、相关,见 links-anchor-generic)。引擎是否区别对待导航链接没有官方说法,这是本套件的推断。
**触发(trigger)**: 1) 入链图标注每条入链来源区域(nav/header/footer vs 正文);2) 正文区入链=0 即 warn。
**不修的条件(caveat)**: 正文入链不影响排名本身,然而它是相关度信号的载体,所以一般建议核心页有语境内链。但政策/法务页(无需主题论证)全 chrome 入链是正常形态;相关推荐模块算不算正文区[待核:源表区域划分口径未公布]。
**修复(fix)**: 在相关正文里以描述性锚接入(锚文本规范见 links-anchor-generic);让内容作者而非仅模板产出内链。
**关联(seealso)**: links-weak-inbound、links-anchor-generic;[link-architecture-patterns.md](../link-architecture-patterns.md)

#### links-no-internal
- 名称/类型: 无内链 —— warning · 优先级 medium · 输出 WARN(源表 ID `links-internal-present`,warn)
**这意味(what)**: 该 URL 的页面上没有任何指向本站其他页面的链接——出链全空或只剩外链。
**为什么(why)**: 爬虫沿内链爬行,无内链出边的页面是爬行路径终点,站内再深一层的内容失去一条发现通道;用户读完即"离开站点",相关推荐与转化路径全部缺席。与 links-dead-end 互补:那条判"零出链",本条把"有出链但无一是站内"也纳入——把流量送出门却不留后路。
**触发(trigger)**: 页面同域 follow `<a href>` 计数=0 即 warn。
**不修的条件(caveat)**: 内链数不(直接)影响本页排名,然而它决定爬行延续与用户动线,所以一般建议补相关内容入口。但纯外链引流的工具落地页/第三方托管的致谢页可合理保持。
**修复(fix)**: 补相关内容模块/面包屑/回到分类入口;模板保证每页有站内链接区块。
**关联(seealso)**: links-dead-end、links-depth;[link-architecture-patterns.md](../link-architecture-patterns.md)

#### links-external-reachability
- 名称/类型: 外链可达性(含 HTTPS 页链 HTTP) —— warning · 优先级 low · 输出 WARN(源表 ID `links-external-valid`,warn:取页上前 20 条外链,先 HEAD、失败再 GET,4xx/5xx/无应答 warn,结果不跨审计缓存;HTTPS 页链 HTTP 是另一条 `links-https-downgrade`)
**这意味(what)**: 页面指向外部的链接目标不可达(4xx/5xx/超时),或 HTTPS 页面上仍用 http:// 外链。
**为什么(why)**: 死外链伤用户信任(点出去 404),也标记页面疏于维护;HTTPS 页混 http 外链本身不构成混合内容(仅子资源才算),但形态不一致在目标站完成 https 化后容易变成断链。
**触发(trigger)**: 1) 请求全部跨域 href(缓存结果);4xx/5xx/超时即 warn;2) 页面 HTTPS 而 href 为 http:// 即 warn。
**不修的条件(caveat)**: 外链目标不受你控制——对方改版删页你这边全站误报,所以一般建议批量检测后只修高频引用的死外链。但支撑 E-E-A-T 的权威引用页(eeat-citations)值得保持零死链,优先级另计。
**修复(fix)**: 死外链换网页存档链接或替代来源;http 外链统一改 https(目标支持时);引用型内容的死链优先于资源页死链。
**关联(seealso)**: links-broken-internal、eeat-citations;[http-status-codes.md](../http-status-codes.md)

#### links-malformed-href [待核 ID]
- 名称/类型: 畸形 href 家族(本套件合并名;源表 ID `links-invalid`、`links-tel-mailto`、`links-non-http-protocol`、`links-whitespace-href`) —— warning · 优先级 low · 输出 WARN(源表各=warn:空/javascript:/畸形 href;tel:/mailto: 格式;非 HTTP 协议 ftp:/intent:/chrome:;href 首尾空白)
**这意味(what)**: `<a>` 的 href 是空串、javascript: 伪协议或畸形值;tel:/mailto: 格式错;scheme 为 ftp:/intent:/chrome: 等非 HTTP(S) 协议;或首尾带空白字符。
**为什么(why)**: Google 只能可靠提取带 href、且能解析成真实地址的 `<a>`([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable),核对 2026-10-21);空 href 与 javascript: 链接没有可抓取的目标,键盘用户聚焦过去也无处可去;tel:/mailto: 格式错在移动端直接呼叫/发信失败;异形协议链接多数是模板变量泄漏。首尾空白则是"能工作但制造变体 URL"的卫生问题。
**触发(trigger)**: 1) href 空串或 javascript: 伪协议即 warn;2) tel: 不匹配 `tel:+数字` 形态、mailto: 无合法邮箱即 warn;3) scheme ∈ ftp:/intent:/chrome: 等非 HTTP(S) 即 warn;4) href 首尾含空白即 warn。
**不修的条件(caveat)**: 伪协议链接不(直接)影响排名,然而它把交互做成引擎与部分用户到不了的门,所以一般建议真导航一律用可跟随 href。但 mailto:/tel: 本身合法,只查格式;确需 JS 行为的元素正解是 `<button>`,不是豁免。
**修复(fix)**: 真导航用真实 URL;JS 行为改 button+事件;tel/mailto 按规范格式输出;模板输出 href 时 trim。
**关联(seealso)**: links-onclick、i18n-hreflang-to-broken;[semantic-html.md](../semantic-html.md)

#### links-broken-anchor
- 名称/类型: 断锚点 —— warning · 优先级 low · 输出 WARN(源表 ID `links-broken-fragment`,warn;#id 无匹配)
**这意味(what)**: 链接的 fragment(#section)在目标页里找不到对应 id/命名锚点。
**为什么(why)**: 锚点链接是长页深链与 AI 引用定位的常用形态;目标页重构后 heading id 改名,来源页的 fragment 全部落空——用户被丢在页顶以为内容不存在。同页 fragment 直接查本页 DOM,跨页 fragment 要抓目标页才能判。
**触发(trigger)**: 1) 提取带 fragment 的 href;2) 在目标页(本页或已抓取缓存)DOM 查 id/`<a name>` 匹配;3) 无匹配即 warn。
**不修的条件(caveat)**: 断锚点不(直接)影响 SEO,然而它把"精确深链"降级为"页顶落点",所以一般建议高价值锚点链保持有效。但第三方页面的 fragment 你无法控制,只修站内互链与自有分发渠道。
**修复(fix)**: 目标页恢复旧 id(加别名)或改引用方 fragment;CMS 生成 heading 时输出稳定 slug id,别用序号。
**关联(seealso)**: links-broken-internal、links-onclick;[semantic-html.md](../semantic-html.md)

#### links-onclick
- 名称/类型: onclick 导航 —— warning · 优先级 medium · 输出 CRITICAL(源表现行 fail · 权重 5;onclick 导航替代 href)
**这意味(what)**: 用元素 onclick 事件做页面导航——`<a>` 无真实 href(或 href="#" 配 onclick 跳转)。
**为什么(why)**: Google 说它无法可靠地从没有 href 的 `<a>` 或靠脚本事件起作用的元素里提取 URL,`<a onclick="goto(...)">` 属「不推荐」写法([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable),核对 2026-10-21);不执行 JS 的爬虫更是只认 href,后续页面失去这条发现路径;中键/右键新开标签、悬停预览、状态栏 URL 全部失效,键盘与辅助技术同样受损。与 [rendering-seo.md](../rendering-seo.md) 的口径一致:导航必须在初始 HTML 的可跟随 href 里。
**触发(trigger)**: `<a>` 无 href 或 href="#"/javascript: 且带 onclick 属性(含常见前端路由跳转特征)即 warn。
**不修的条件(caveat)**: onclick 导航不(直接)惩罚,然而它把不执行 JS 的访问者挡在门外,所以一般建议 href 写真实目标 URL、JS 只做增强。但 SPA 视图切换用真实 href+pushState 的渐进增强是正解形态,不是豁免。
**修复(fix)**: `<a href="/real/url">` 为主体,onclick preventDefault 仅做无刷新增强;纯动作元素(提交/展开)改 button。
**关联(seealso)**: links-malformed-href、js-content-dependency;[rendering-seo.md](../rendering-seo.md)、[semantic-html.md](../semantic-html.md)

#### links-nofollow-external
- 名称/类型: 外链 nofollow 滥用 —— warning · 优先级 low · 输出 WARN(源表 ID `links-nofollow-appropriate`,warn;nofollow 滥用;与 links-nofollow-internal 互补)
**这意味(what)**: 站内出站链接被大面积加 rel=nofollow——包括自然引用的权威来源、合作伙伴等本应正常投票的链接。
**为什么(why)**: Google 说 nofollow 只在不信任来源时用,不是每条外链都加;付费链接用 sponsored 或 nofollow,用户生成内容用 ugc 或 nofollow([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable),核对 2026-10-21)。引用来源本来有助建立可信度,全站外链一刀切 nofollow 等于自己关掉这个信号(eeat-citations)。与 links-nofollow-internal 互补:一个错在自我否定,一个错在过度防御。
**触发(trigger)**: 跨域 `<a>` 带 rel=nofollow(不含 sponsored/ugc)占比超出自然水平(阈值源表未公布[待核]),或权威引用源(.gov/.edu/论文)被 nofollow 即 warn。
**不修的条件(caveat)**: nofollow 外链不影响本页排名,然而它同时放弃引用背书与链接语义准确性,所以一般建议只给三类正当用途。但法务要求全站外链免责的场景(金融合规)可整体保留,报告记豁免。
**修复(fix)**: 自然引用去 nofollow;付费位改 sponsored;UGC 区改 ugc;CMS 若默认全局加 nofollow,改模板开关。
**关联(seealso)**: links-nofollow-internal、eeat-citations;[robots-txt-reference.md](../robots-txt-reference.md)、[deprecated-signals.md](../deprecated-signals.md)
