# 审计规则目录 · Technical SEO

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### Technical SEO(18 条,权重 7%)

robots.txt 存在=fail、语法=warn/fail;sitemap 存在/格式=warn/fail;URL 结构(小写+连字符)=warn/fail;尾斜杠一致性(同一路径带与不带斜杠都被链接)=warn;www 一致性 301=warn/fail;自定义 404=warn/fail;soft-404(200 但错误内容)=**fail**;5xx=fail;**非 404 的 4xx:401/403/其他=fail,410 与 429=warn**;响应时间(`technical-timeout`):**≥3 秒 warn、>10 秒 fail**;Content-Type 错=warn/fail;**200 空响应体或 head/body 皆空=fail**;`technical-form-get-method`(GET 表单产生可抓取查询串 URL=warn);**多 GTM 容器/多 GA 属性(>1 个不同 ID)=warn**;`technical-consent-mode`(Google 标签须配 consent update)=warn。

**解释层(10 条,第三批;ID 未公布原文的按家族命名法推得并标 [待核])**

#### technical-5xx [待核 ID]
- 名称/类型: 服务器错误与超时(源表 ID `technical-server-error`、`technical-timeout`) —— issue · 优先级 critical · 输出 CRITICAL(源表:5xx=fail;响应时间 ≥3 秒 warn、>10 秒 fail)
**这意味(what)**: 该 URL 返回 5xx 状态码,或响应慢到 3 秒以上(>10 秒为失败)。
**为什么(why)**: 5xx 和 429 会让 Google 抓取器降低抓取速度,持续出现时已编入索引的 URL 会被移出索引([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors),核对 2026-10-21;处置表见 [http-status-codes.md](../http-status-codes.md))。慢响应的 3 秒/10 秒线是 SEOmator 工具约定。单页 5xx 指应用层,全站 5xx 指基础设施,修复路径不同。
**触发(trigger)**: 1) 响应状态 5xx 即 fail;2) 响应时间 ≥3 秒 warn、>10 秒 fail;3) 输出按影响面分型(单页/全站)。site_audit 对 HTTP 错误页只出 `[CRITICAL] fetch`(401/403/429/503 则按「疑似挑战页」`[SKIP]` 拒审),不量响应时间。
**不修的条件(caveat)**: 计划内维护应返回 503+Retry-After(告诉引擎稍后再来),用 200 返回维护页反而制造 soft-404;真故障无豁免,修的是稳定性本身。
**修复(fix)**: 全站 5xx 查基础设施(部署窗口/数据库连接池);单页 5xx 查应用日志;维护窗口统一 503+Retry-After;要降抓取速度短期用 429/503,不用 401/403。
**关联(seealso)**: technical-empty-html、technical-soft-404;[http-status-codes.md](../http-status-codes.md)、[log-analysis.md](../log-analysis.md)

#### technical-empty-html
- 名称/类型: 200 空 HTML —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;200 且响应体为空,或 head 与 body 皆空)
**这意味(what)**: URL 返回 200,响应体却是 head 与 body 都为空的 HTML 壳。
**为什么(why)**: 200+空壳是最高危的"假正常":索引流程收到"成功"却没有可索引内容,GSC 归入 soft 404 类目;客户端渲染失败(js-runtime-hygiene 的未捕获异常)也会呈现这个形态。引擎视角:页面存在但什么都没有,慢性退索引。
**触发(trigger)**: 1) 状态 200;2) 解析后 head 与 body 均无有效内容节点即 fail。
**不修的条件(caveat)**: 无豁免——200 必须配内容;确无内容的地址应给 404/410 或 301,而不是 200 空壳。
**修复(fix)**: 查渲染管道(SSR 失败回退空模板是常见肇因);模板兜底至少输出错误说明+正确状态码;CI 对发布产物做"空 HTML"断言。
**关联(seealso)**: technical-5xx、technical-soft-404、js-runtime-hygiene;[http-status-codes.md](../http-status-codes.md)

#### technical-soft-404
- 名称/类型: soft 404 —— issue · 优先级 high · 输出 CRITICAL(源表现行 fail,权重 10;200 但错误内容)
**这意味(what)**: URL 返回 200,页面内容却是"未找到/已下架"的错误态。
**为什么(why)**: 2xx 页面内容却是空页或错误信息时,Search Console 显示 soft 404([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors);[索引报告](https://support.google.com/webmasters/answer/7440203),核对 2026-10-21),Google 建议对真正不存在的页返回 404 码。它们在索引报告里混成噪音,真假问题难分。典型来源:下架商品页返回 200"商品不存在"。
**触发(trigger)**: 1) 状态 200;2) 内容命中错误态特征("未找到/已下架/page not found"文案、空分类、搜索无结果壳、渲染失败空壳)即 warn。
**不修的条件(caveat)**: 判定是内容启发不是状态码,误报存在(正文合法引用"not found"字样),所以一般建议命中后人工抽查再改状态码。但确要保留的"内容已移除"说明页(带后续指引)属正当形态,配 noindex 即可。
**修复(fix)**: 真没了→真 404/410;有替代→301 到最近亲内容页(不是首页);保留说明页→加 noindex。
**关联(seealso)**: technical-4xx-non404、technical-custom-404;[http-status-codes.md](../http-status-codes.md)

#### technical-4xx-non404
- 名称/类型: 非 404 的 4xx(源表 ID `technical-4xx-non-404`) —— warning · 优先级 medium · 输出 CRITICAL/WARN(源表现行:401、403 及其他 4xx=fail;410 与 429=warn;单页审计遇 4xx/5xx 会以退出码 2 中止,这两条规则只在 crawl 里出结果)
**这意味(what)**: 页面返回 403、410、451 等 404 之外的 4xx 状态。
**为什么(why)**: 各 4xx 语义不同,审计价值在分清"状态码用对了吗":401/403 是权限语义;Google 对除 429 外的 4xx 一律当作「内容不存在」,不要用 401/403 限制抓取速度([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors),核对 2026-10-21);要短期降速应返回 500/503/429([降速文档](https://developers.google.com/search/docs/crawling-indexing/reduce-crawl-rate))。410 是明确的永久下线声明。选错码主要污染你自己的监控分类。
**触发(trigger)**: 响应状态 ∈ 4xx 且 ≠404:401/403/其他 fail,410 与 429 warn(404 本身不算错误,由内链/sitemap 交叉规则管)。
**不修的条件(caveat)**: 4xx 状态不惩罚站点(404 是正常 web 形态),然而选错码会误导引擎与监控,所以一般建议按语义选码。但登录墙内容返回 401/403 是正当设计,别为审计绿灯改成 404。
**修复(fix)**: 永久下线→410;临时不可用→503+Retry-After;限流→429;无权访问→401/403 保持。
**关联(seealso)**: technical-soft-404、technical-5xx;[http-status-codes.md](../http-status-codes.md)

#### technical-custom-404
- 名称/类型: 自定义 404 页(源表 ID `technical-404-page`) —— warning · 优先级 low · 输出 WARN(源表 warn/fail)
**这意味(what)**: 站点 404 时返回服务器默认错误页,而非带导航与搜索的自定义 404 页。
**为什么(why)**: 404 本身不伤 SEO,伤的是 404 之后用户去留:默认错误页零出路,用户直接关站;自定义 404 给导航/搜索/热门内容,把撞错 URL 的流量接回站内。对引擎,自定义 404 也证明错误态是设计过的而非配置事故。
**触发(trigger)**: 请求不存在路径;返回 404 但响应体为服务器默认页(无站内导航特征/体积极小)即 warn;404 返回 200 另归 technical-soft-404。
**不修的条件(caveat)**: 404 状态码不(直接)影响排名,然而它决定错误流量的回收率,所以一般建议配自定义页。但纯 API/内部服务不需要人类可读 404。
**修复(fix)**: 404 模板带站点导航+站内搜索+热门链接;保持真 404 状态码;别自动跳首页(制造 soft-404)。
**关联(seealso)**: technical-soft-404、technical-4xx-non404;[http-status-codes.md](../http-status-codes.md)

#### technical-robots-txt
- 名称/类型: robots.txt 存在性与语法(源表 ID `technical-robots-txt-exists` fail、`technical-robots-txt-valid` warn/fail) —— warning · 优先级 high · 输出 CRITICAL/WARN
**这意味(what)**: 站点没有 robots.txt,或文件存在但含语法错误(非法指令/拼写错的键/未闭合组)。
**为什么(why)**: robots.txt 是抓取层第一道闸。Google 对 4xx(含 404)的 robots.txt 按「没有抓取限制」处理;5xx 则更糟:先暂停抓取全站约 12 小时,之后 30 天内沿用最后一份可用的版本([robots 规范](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec),核对 2026-10-21)。语法坏时你写的 Disallow 可能没按你以为的生效。它还是 crawl-* 交叉规则(crawl-sitemap-disallowed 等)的前置输入,坏语法会级联污染下游判定。
**触发(trigger)**: 1) /robots.txt 不可访问 → 存在性(源表 fail);2) RFC 9309 解析报语法错 → 语法档(warn/fail)。site_audit 对 robots.txt 404 视为全放行、不出 finding;其他不可达出 `[INFO] robots: /robots.txt 不可达`。
**不修的条件(caveat)**: 缺 robots.txt 不(直接)影响 SEO(全允许也是合法状态),然而失去声明面与审计输入,所以一般建议放显式文件。但确无任何屏蔽需求的小站,空文件与缺文件等价,可记豁免。
**修复(fix)**: 提交显式 robots.txt(至少含 Sitemap 行,见 crawl-sitemap-in-robotstxt);用 RFC 9309 校验器过一遍;模板生成禁手维护([ai-crawler-policy.md](../ai-crawler-policy.md) 口径)。
**关联(seealso)**: crawl-sitemap-disallowed、crawl-blocked-resources、crawl-crawl-delay;[robots-txt-reference.md](../robots-txt-reference.md)、[ai-crawler-policy.md](../ai-crawler-policy.md)

#### technical-sitemap-existence
- 名称/类型: sitemap 存在性与格式(源表 ID `technical-sitemap-exists`、`technical-sitemap-valid`) —— warning · 优先级 medium · 输出 WARN/CRITICAL(源表 warn/fail)
**这意味(what)**: 站点没有可发现的 sitemap,或 sitemap 格式坏(XML 不合法/编码错/非 sitemap 结构)。
**为什么(why)**: sitemap 是发现与再抓取的加速器:格式坏时 GSC 提交会报解析错误,该文件无法被处理。存在性按发现路径判:robots.txt Sitemap 行、/sitemap.xml 常规路径、GSC 声明。条数/体积/lastmod 质量/domain 一致性由 Crawlability 节 sitemap 家族分规则管,本条只立"有没有、能不能解析"。
**触发(trigger)**: 1) 无任何可发现 sitemap → 缺失档;2) XML 解析失败/缺 urlset 命名空间 → 格式档;均 warn/fail(上游按条目问题轻重分档)。site_audit 只探 `/sitemap.xml`,不可达出 `[INFO] sitemap`。
**不修的条件(caveat)**: sitemap 是推荐机制不是排名因素,内链完整的小站缺失损失有限,所以一般建议核心站必配、极小站可缓。但无 sitemap 时 GSC 的提交与覆盖率诊断面也少一半,通常仍值得配。
**修复(fix)**: 生成器输出标准 XML(可选 gzip);robots.txt 声明+GSC 提交;校验命名空间与转义(& 用 &amp;)。
**关联(seealso)**: crawl-sitemap-url-limit、crawl-sitemap-lastmod、crawl-sitemap-in-robotstxt;[validation-guide.md](../validation-guide.md)

#### technical-content-type
- 名称/类型: Content-Type 错误(源表 ID `technical-bad-content-type`) —— issue/warning · 优先级 medium · 输出 WARN/CRITICAL(源表 warn/fail;分型口径源表未公布[待核])
**这意味(what)**: 响应的 Content-Type 头与实际内容或用途不符:HTML 页声明成 text/plain、字体声明成 text/html、缺 charset 等。
**为什么(why)**: 引擎与浏览器按 Content-Type 决定解析路径:声明错时 HTML 被当纯文本(索引流程拿不到 DOM)、资源被按错误类型处理;缺 charset 触发编码猜测,与 mojibake(content-deploy-hygiene)同源;nosniff 生效时被误标的资源直接被拒执行。
**触发(trigger)**: 1) 主文档非 text/html(且非刻意的 data feed)即触发;2) 子资源 Content-Type 与扩展/内容嗅探不符即触发;warn/fail 按分型[待核:主文档误标取重档的常见分型]。
**不修的条件(caveat)**: 个别误标(注释类文件以 text/plain 服务)不影响 SEO 面,然而主文档误标等于把页面挡在解析之外,所以一般建议全站对齐。但刻意以非 HTML 类型服务的资源(JSON API/RSS)不属误报,注意剔除。
**修复(fix)**: 服务器 MIME 表对齐;HTML 显式 `text/html; charset=utf-8`;要上 nosniff 前先自查全部资源类型(见 security-headers)。
**关联(seealso)**: content-mime-broken、content-deploy-hygiene、security-headers;[http-status-codes.md](../http-status-codes.md)

#### technical-url-consistency [待核 ID]
- 名称/类型: URL 形态一致性家族(源表 ID `technical-url-structure`、`technical-trailing-slash`、`technical-www-redirect`) —— warning · 优先级 medium · 输出 WARN(源表 warn/fail:URL 结构小写+连字符;同一路径带与不带尾斜杠都被链接;www 一致性 301)
**这意味(what)**: 站点级 URL 形态不统一:大小写/分词符混用、同站尾斜杠两可、www 与非 www 双可达且不互 301。
**为什么(why)**: 三项都在制造"同内容多 URL":Google 的 URL 处理区分大小写,/APPLE 与 /apple 是两个 URL([URL 结构文档](https://developers.google.com/search/docs/crawling-indexing/url-structure),核对 2026-10-21);尾斜杠两可时引擎靠规范化猜;www 双可达是经典重复站点种子。它们是 url-shape(单页形态卫生)的站点级聚合面——[validation-guide.md](../validation-guide.md) C3 检查项(四变体 301 到唯一规范 host)就是本条的落地。
**触发(trigger)**: 1) 站内 URL 混用大小写/下划线与连字符即 warn;2) 同路径带/不带尾斜杠均 200 即 warn;3) www 与非 www 均可达且无单向 301 即 warn。
**不修的条件(caveat)**: 一致性家族不(直接)影响单页排名,然而每项都在给规范化添噪音,所以一般建议定一种形态+301 收口。但历史 URL 的大写形态已积累外链时,保持现状+canonical 比强改更稳。
**修复(fix)**: 定规范形态(小写+连字符+固定尾斜杠策略+单 host),其余变体 301 到规范形;CMS 输出层统一;新内容从源头合规。
**关联(seealso)**: url-shape、crawl-canonical-form-drift、redirects-case-normalization;[redirects-canonical.md](../redirects-canonical.md)、[validation-guide.md](../validation-guide.md)

#### technical-tagging [待核 ID]
- 名称/类型: 埋点与表单卫生家族(源表 ID `technical-duplicate-gtm`、`technical-duplicate-ga`、`technical-consent-mode`、`technical-form-get-method`) —— warning · 优先级 low · 输出 WARN(源表各=warn:多 GTM 容器/多 GA 属性(>1 个不同 ID);consent mode;GET 表单)
**这意味(what)**: 三项埋点/表单卫生任一命中:页面加载 >1 个不同 ID 的 GTM 容器或 GA 属性;Google 标签未配 consent mode update;GET 表单产生可抓取的查询串 URL。
**为什么(why)**: 双容器/双属性是"两拨人各埋一套"的事故:双计、页面变重、数据口径分裂——SEO 决策的数据底座被毁;consent mode 缺失在欧盟市场意味着同意前信号丢失与合规缺口;GET 表单把用户输入变成 URL,爬虫沿结果页发散(与 url-search-indexed 同源),敏感参数还可能进日志与外泄。
**触发(trigger)**: 1) 页面 GTM 容器 ID 去重后 >1 或 GA 属性 >1 即 warn;2) 有 gtag/GTM 但无 consent 默认态+update 调用即 warn;3) `<form method=get>`(缺省即 GET)且 action 产生站内查询 URL 即 warn。
**不修的条件(caveat)**: 埋点卫生不影响排名本身,然而双计毁掉流量归因的可信度,所以一般建议收敛单容器。但迁移期新旧属性并行的双属性是临时合理态,报告标注截止日期。
**修复(fix)**: 容器收敛为一个,历史属性经 GTM 转发;gtag 配 consent default+update(接 CMP,见 legal-cookie-consent);站内搜索表单结果页 noindex 或改 POST/前端路由。
**关联(seealso)**: url-search-indexed、legal-cookie-consent、sd-searchaction;[gtm-implementation.md](../gtm-implementation.md)、[ga4-implementation.md](../ga4-implementation.md)
