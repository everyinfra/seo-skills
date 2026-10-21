# 审计规则目录 · Redirects

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### Redirects(11 条,权重 3%)

meta refresh=warn;JS 重定向=warn;HTTP Refresh 头=warn;环=fail;301(永久/传权重)vs 302(临时)用错=warn;目标 4xx/5xx=fail;**静态资源被重定向=warn**;大小写规范化重定向=warn;**渲染专属三条**:resource-broken(资源重定向终点 4xx/5xx=fail)/resource-loop(资源重定向环,浏览器 ERR_TOO_MANY_REDIRECTS=fail)/**resource-chain(资源 ≥2 跳=warn,单跳 http→https/尾斜杠视为良性)**。

**解释层(7 条;ID 未公布原文,标 [待核];JS/HTTP Refresh 头两条并入 meta-refresh 条目陈述)**

#### redirect-loop
- 源表:fail · 权重 15。重定向链回到已访问 URL。工具约定。建议优先级 critical。
**依据**: Googlebot 最多跟约 10 跳,环永远到不了内容;Search Console 对重定向失败报错([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors))。核对 2026-10-18。
**判据**: 通过=链在有限跳内到达非 3xx。失败=回到途经 URL。
**执行**: `REDIR URL` 出现 `[CRITICAL] 检测到循环`(退出码 1)。
**修复**: 排查强制 https、强制 www、尾斜杠三类规则的叠加顺序,合并为一步到位。
**关联**: crawl-canonical-loop、links-redirect-chains;[redirects-canonical.md](../redirects-canonical.md)

#### redirect-broken
- 源表:fail · 权重 15。页面重定向链的最终状态是 4xx/5xx(爬取中无重定向直达 4xx/5xx 的页也算)。工具约定。建议优先级 critical。
**依据**: Google 不索引返回 4xx 的 URL,已索引的会被移除;5xx 持续则移除([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors))。旧 URL 的去向因此丢失。核对 2026-10-18。
**判据**: 通过=终点 2xx。失败=终点 4xx/5xx。
**执行**: `REDIR URL` 看「终态: HTTP」行,4xx/5xx 即失败(脚本只打印不判定)。迁移后按映射表逐行跑。
**修复**: 终点恢复内容,或改指最近亲的存活页;不要统一跳首页(内容不对应时,首页不是合适的替代)。
**关联**: links-broken-internal、crawl-sitemap-non-200;[http-status-codes.md](../http-status-codes.md)

#### redirect-type
- 源表:warn · 权重 12。链中某跳是临时码(302/303/307)而不是 301/308。工具约定。建议优先级 medium。
**依据**: 要改变页面在结果中显示的 URL,Google 推荐尽量用服务端永久重定向(301/308);301 是"目标应被处理"的强信号,302 是弱信号;临时重定向保留源页在结果中([重定向文档](https://developers.google.com/search/docs/crawling-indexing/301-redirects);[HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors))。核对 2026-10-18。
**判据**: 通过=永久搬迁用 301/308,临时活动用 302/307。失败=永久变化用了临时码。
**执行**: `REDIR URL` 出现 `[WARN] 第 N 跳是…临时重定向,建议改 301`(脚本只对 http→https、加去 www、尾斜杠三类永久变化报警,其他场景人工判)。
**修复**: 永久变更改 301/308;临时场景保持 302/307。
**关联**: redirect-loop;[redirects-canonical.md](../redirects-canonical.md)

#### redirect-meta-refresh
- 源表:`redirect-meta-refresh` warn/fail · 权重 15;同族 `redirect-http-refresh`(Refresh 响应头,fail · 权重 10)、`redirect-javascript`(warn · 权重 12)。工具约定。建议优先级 medium。
**依据**: Google 把 0 秒 meta refresh 与 0 秒 HTTP Refresh 当永久重定向,延时的当临时重定向;服务端重定向最可靠,做不到时才用 meta refresh,JS 跳转更靠后([重定向文档](https://developers.google.com/search/docs/crawling-indexing/301-redirects))。"非 0 秒可能不跟"不成立。核对 2026-10-18。
**判据**: 通过=跳转用服务端 3xx。失败=用 meta refresh、Refresh 头或 JS 实现跳转。5 秒轮播一类非跳转语义不算。
**执行**: `curl -s URL | grep -oiE '<meta[^>]+http-equiv=.?refresh[^>]*>'`;`curl -sI URL | grep -i '^refresh:'`;JS 跳转人工查 `location` 赋值。
**修复**: 换成服务端 301/302;确需保留的引导页写清 canonical。
**关联**: redirect-type;[redirects-canonical.md](../redirects-canonical.md)

#### redirects-static-resource [待核 ID]
- 名称/类型: 静态资源被重定向(源表 ID `redirect-resource`) —— warning · 优先级 medium · 输出 WARN(源表现行:HTTPS 页的样式表、脚本、图片 URL 以 `http://` 开头即 warn,不发请求,这类 URL 通常会跳转到 HTTPS)
**这意味(what)**: 页面引用的静态资源(CSS/JS/图)用了 `http://` 地址(上游判据);或其 URL 自身返回 3xx(本套件另查,需渲染)。
**为什么(why)**: 每条资源重定向都是渲染瀑布里多出的一跳:握手与请求白付两次,渲染阻塞资源(同步 CSS)的重定向直接串行拖慢 FCP/LCP;抓取侧同样双倍成本。典型来源:资源改版后旧 URL 301 保底、CDN 规则把 /assets/ 整体跳新路径、http 资源在 https 页被协议跳转。
**触发(trigger)**: 上游:HTTPS 页的子资源 URL 以 http:// 开头即 warn。本套件另查:子资源返回 3xx 即 warn(终点 4xx/5xx 或成环另归 redirects-resource-chain 的 fail 档)。
**不修的条件(caveat)**: 单条资源重定向不影响排名,然而它在渲染关键路径上按毫秒计价,所以一般建议资源引用直指最终 URL。但迁移窗口期保留旧资源 URL 的 301 兜底是正当缓冲,发版后收直。
**修复(fix)**: 模板/构建产物里资源引用写最终 URL;http 资源引用改 https 直连;CDN 层把跳转规则改写为内部重写。
**关联(seealso)**: redirects-resource-chain、perf-render-blocking;[redirects-canonical.md](../redirects-canonical.md)

#### redirects-case-normalization
- 名称/类型: URL 大小写规范化(源表 ID `redirect-case-normalization`) —— warning · 优先级 low · 输出 WARN(源表现行:最终服务的 URL 与页面 canonical 仅大小写不同才 warn;请求大小写变体后被 301 到规范形式=通过)
**这意味(what)**: 页面最终服务的 URL 与 canonical 仅大小写不同——大小写变体没有被收口到规范形式。(原稿把「大小写重定向本身」当问题,与上游现行相反,已更正:重定向到规范形式是正确做法。)
**为什么(why)**: host 之后的路径大小写是否敏感取决于服务器/CDN,两种策略混用时唯一安全的收口是统一小写+301;但"每条内链先写成大写再靠 301 兜底"意味着每次点击都付一跳——这是把规范化成本从模板层转嫁到运行时。与 url-shape/technical-url-consistency 同源:根因是 URL 生成不规范。
**触发(trigger)**: 最终服务的 URL 与 canonical 仅大小写不同即 warn;大小写变体 301 到规范形式则通过。
**不修的条件(caveat)**: 规范化重定向本身是正确收口(比双 200 好),然而它标记模板还在产大写 URL,所以一般建议源头改小写、301 只留兜底。但从大小写不敏感服务器迁到敏感服务器时,这批 301 是必要过渡,可长期保留。
**修复(fix)**: URL 生成层统一小写输出;内链/模板/sitemap 排查大写引用;301 规则保留作外链兜底。
**关联(seealso)**: technical-url-consistency、url-shape;[redirects-canonical.md](../redirects-canonical.md)

#### redirects-resource-chain [待核 ID]
- 名称/类型: 资源重定向链家族(渲染专属三条;源表 ID `redirect-resource-broken`、`redirect-resource-loop`、`redirect-resource-chain`) —— issue/warning · 优先级 high(fail 档)/medium · 输出 CRITICAL/WARN(源表:resource-broken 资源重定向终点 4xx/5xx=fail;resource-loop 资源重定向环,浏览器 ERR_TOO_MANY_REDIRECTS=fail;resource-chain 资源 ≥2 跳=warn,单跳 http→https/尾斜杠视为良性)
**这意味(what)**: 子资源重定向的三种深浅:链终点 4xx/5xx(资源实际丢失)、重定向成环(资源永不可得)、链长 ≥2 跳。
**为什么(why)**: 资源层与页面层(links-redirect-chains)同构但更苛:页面重定向用户还能多点一次,资源重定向直接决定渲染成败——CSS 链断则整页无样式,脚本链断则交互与注解注入全灭。单跳 http→https/尾斜杠被显式豁免为良性(规范化常态),≥2 跳才算链。
**触发(trigger)**: 渲染后逐资源跟踪 Location:1) 终点 4xx/5xx 即 fail;2) 回到途经任一 URL 即 fail;3) 跳数 ≥2 即 warn;4) 单跳且属 http→https/尾斜杠形态不报。
**不修的条件(caveat)**: 家族判定的是引用层的懒——资源本体搬家后引用没跟上,所以一般建议构建期校验全部资源 URL 直达 200。但第三方资源(外源字体/脚本)的重定向不在掌控内,先分类再处置:能换 URL 的换,不能换的评估自托管。
**修复(fix)**: 构建管道加资源 URL 终态断言(直达 200);版本化文件名+固定 CDN 路径消除跳转;外源资源锁定版本化 URL。
**关联(seealso)**: redirects-static-resource、js-runtime-hygiene、links-redirect-chains;[redirects-canonical.md](../redirects-canonical.md)、[rendering-seo.md](../rendering-seo.md)
