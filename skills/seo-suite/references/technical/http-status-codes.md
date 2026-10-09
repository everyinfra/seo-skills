# HTTP 状态码与抓取、索引

## 用途

技术审计、网站迁移、排查「页面不被编入索引 / 从结果里消失」时读。判断以 Google 的[HTTP 状态码与网络错误](https://developers.google.com/search/docs/crawling-indexing/http-network-errors)和[重定向](https://developers.google.com/search/docs/crawling-indexing/301-redirects)文档为准；其他搜索引擎的处理可能不同。

> 本文管状态码语义与分级；重定向的**全类型用法、canonicalization 六场景、分页/facet 治理与审计操作**深入指南见 [redirects-canonical](redirects-canonical.md)。

## 一、Google 如何处理各类状态码

| 状态码 | Google 的处理 | 什么时候用 |
|---|---|---|
| 200 等 2xx | 把内容交给索引流程，但不保证编入索引；内容看起来是错误页时会被判为 soft 404 | 正常页面 |
| 204 | 视为没有内容，Search Console 可能报 soft 404 | 不用于希望编入索引的页面 |
| 301、308 | 永久重定向：强信号，表示目标 URL 应成为规范网址 | 永久改址、合并页面、HTTP 转 HTTPS |
| 302、303、307 | 临时重定向：弱信号，搜索结果通常仍显示原 URL | 临时活动、短期维护跳转 |
| 304 | 内容自上次抓取后未变 | 条件请求，节省抓取 |
| 404、410 等 4xx（429 除外） | 同样处理：内容不存在；已编入的 URL 会被移出索引，抓取频率逐渐下降 | 删除且没有替代的内容 |
| 401、403 | 同上，视为不存在 | 需要登录的页面；不能拿来限制抓取速度 |
| 429 | 按服务器错误处理，是限速信号 | 临时限流 |
| 5xx | 暂时降低抓取速度；持续出现，已编入的 URL 会被移出索引 | 只应是短暂故障 |
| DNS、连接超时等网络错误 | 与 5xx 类似 | 查 DNS、CDN、防火墙 |

补充：Googlebot 最多跟随 10 次重定向，超过就在 Search Console 报重定向错误。

## 二、soft 404

返回 200，页面上却是「未找到」「商品已下架」、空的分类或站内搜索结果，或者渲染失败只剩空壳，都可能被判为 soft 404。处理方法三选一：

- 内容确实没了、也没有替代 → 返回 404 或 410。
- 有相关的替代页 → 301 到替代页。
- 页面本来有用 → 补足内容，修好渲染。

把大量删除页统一重定向到首页或无关页面，同样可能被当作 soft 404。

## 三、重定向

- 优先用服务端重定向；meta refresh 和 JavaScript 重定向只在无法做服务端重定向时使用。
- 永久变更用 301 或 308，临时变更用 302 或 307，表达清楚意图。
- 链路直接指向最终 URL。每多一跳，就多一次延迟和出错的机会。
- 检查循环重定向（A → B → A）。
- 内链、sitemap、canonical、hreflang 都直接写最终 URL，这些 URL 本身应返回 200，不要依赖重定向。

## 四、改址迁移

按[更改网址的网站迁移](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)文档：

1. 旧 URL 到新 URL 一对一映射；只有确实没有对应页的，才返回 404/410 或指向最相关的上级页。
2. 上线前逐条测试映射表：每条都返回 301 或 308，并且一跳到达。
3. 同步更新内链、canonical、hreflang 和 sitemap。
4. 重定向尽量长期保留，Google 的建议是一般至少一年。
5. 上线后在 Search Console 看页面索引报告和抓取统计；换域名时同时使用「地址更改」工具。

## 五、维护与限流

- 短时维护返回 503，可带 `Retry-After`；不要用 200 返回维护页，也不要返回 404。
- 需要降低 Google 抓取速度时，短期返回 429、500 或 503，不要用 401、403、404。
- CDN 或 WAF 规则误拦 Googlebot 是常见事故。拦截前先核实爬虫真伪（反向 DNS），不要按 User-Agent 字符串一刀切。

## 六、排查方法

- 看首个响应的状态码：浏览器开发者工具的「网络」面板，或命令行逐跳查看。
- 用 Search Console 的网址检查（需要该站点的权限），看 Google 实际抓到了什么。
- 看页面索引报告里的原因分类：未找到（404）、soft 404、服务器错误（5xx）、重定向错误等。
- 服务器日志按状态码和爬虫统计。CDN 或 WAF 规则可能对不同 User-Agent、不同地区返回不同结果，要分别测试。

自写示例，逐跳列出状态码和跳转目标：

```bash
curl -sIL https://example.com/old-page | grep -iE '^(HTTP/|location:)'
```

## 常见误区

- 「410 比 404 快得多」：按 Google 文档，除 429 以外的 4xx 处理方式相同。
- 「302 完全不传递信号」：临时重定向是规范化的弱信号；用 301/308 是为了把「永久」讲清楚。
- 「301 会损失百分之几的权重」：没有一手出处，不要写进方案。
- 把所有删除页都 301 到首页。
- 用 403 来限制抓取速度。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/technical-seo-checker/references/http-status-codes.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/optimize/technical-seo-checker/references/http-status-codes.md)（Apache-2.0）
- 一手资料：[HTTP 状态码与网络错误](https://developers.google.com/search/docs/crawling-indexing/http-network-errors)、[重定向](https://developers.google.com/search/docs/crawling-indexing/301-redirects)、[更改网址的网站迁移](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)、[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)、[MDN HTTP 状态码](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

## 安全头/缓存/状态码分级审计口径 (siteone-crawler 源码深读 2026-10-09b)

> 来源：[janreges/siteone-crawler](https://github.com/janreges/siteone-crawler)（Rust，MIT）`src/analysis/security_analyzer.rs`、`caching_analyzer.rs`、`redirects_analyzer.rs`、`page404_analyzer.rs`、`content_type_analyzer.rs` 逐行深读。四档严重度：critical/warning/notice/OK。这是工具判定口径，非 Google 官方规则；安全头本身不是排名因子，但混合内容与 HTTPS 直接影响抓取和页面体验信号。

### 安全响应头 16 项检查矩阵（SecurityAnalyzer，仅 HTML 响应）

| 头 | 缺失 | 命中其他情形 | OK |
|---|---|---|---|
| Strict-Transport-Security | **critical**（仅 HTTPS 页检查） | `max-age=0`=critical；**max-age < 31 天（2,678,400s）=warning** | max-age ≥ 31 天 |
| Content-Security-Policy | **critical** | 有但被削弱=warning：`'unsafe-inline'`（同指令内有 `'nonce-'`/`'sha256-'`/`'sha384-'`/`'sha512-'` 时浏览器忽略 unsafe-inline，不算弱点）、`'unsafe-eval'`、或 `default-src/script-src/object-src/style-src/frame-src/connect-src/worker-src/child-src/manifest-src` 里裸 `*` | 无上述弱点 |
| X-Frame-Options | warning | `SAMEORIGIN`/`ALLOW-FROM`=notice；其他任意值=warning | `DENY` |
| X-Content-Type-Options | warning | 非 `nosniff` 值=warning | `nosniff` |
| Referrer-Policy | warning | 非法值=notice | 8 个合法值（no-referrer / no-referrer-when-downgrade / origin / origin-when-cross-origin / same-origin / strict-origin / strict-origin-when-cross-origin / unsafe-url） |
| Permissions-Policy | warning | —（有值即 OK） | 有值 |
| Feature-Policy（旧） | warning（Permissions-Policy 已设则降为 notice"够了"） | — | 有值 |
| X-XSS-Protection（已弃用） | **不设=OK（现代正确行为）**；`0`=OK | 设了 `1`/`1; mode=block` 等=notice，建议改用 CSP | 不设或 `0` |
| Access-Control-Allow-Origin | 不检查 | `*`=warning；其他非 same-origin/none 值=notice | `same-origin`/`none` |
| COOP / COEP / CORP | notice（普及度低，不苛求） | — | 有值（如 `same-origin`/`require-corp`） |
| Server | 不设/空=**推荐（OK）** | **含数字（暴露版本）=critical**；含 Apache/nginx/Microsoft-IIS 名=warning；其他值=notice | 不设 |
| X-Powered-By | 不检查 | **含数字=critical**；无数字=warning | 不设 |

- **Set-Cookie 逐条评估**（多个 Set-Cookie 分行各查各的；单条 Expires 里的逗号不拆分）：缺 `SameSite`=notice；缺 `HttpOnly`=warning；**HTTPS 页缺 `Secure`=critical**。
- 判定只在 `is_allowed_for_crawling` 且 content-type=HTML 且 URL 不像静态文件的响应上跑——安全头审计口径应限定"页面"而非资产。

### 混合内容（HTTPS 页面上的 http:// 引用）

- **critical（主动混合内容，浏览器直接拦）**：`<form action=http://>`、`<iframe src=http://>`、`<script src=http://>`、`<link rel=stylesheet href=http://>`。
- **warning（被动混合内容）**：`<img|audio|video|source src=http://>`。
- `<link rel=canonical/alternate/preconnect/icon>` over http **不算**主动内容（不当 critical）——canonical 指 http 是规范化问题，不是混合内容。

### 重定向与 404 分级

- 重定向表收录 **301–308** 全量：重定向 URL + Location 目标 + 发现页（Found at URL）三列；站点级分级 0=OK / 1–2 / 3–9 / ≥10。对应本文"内链直指最终 URL"：3–9 条就该在迁移清单里处理。
- 404 表同样带发现页；**分级：0=OK / 1–2=notice / 3–5=warning / ≥6=critical**——与 Google"4xx 一律视为不存在"不同，这是站内链接卫生口径（内链打出 404 = 浪费抓取与链接权重，见 C6"只报不在 sitemap 内的死链"互补）。

### 缓存策略分级（CachingAnalyzer）

- 静态资产三分类（限 status 200、本站、静态文件，**排除 JSON/XML 动态端点**——它们 no-store 是正确的）：
  - **Uncacheable**（warning，"static-assets-uncacheable"）：`no-store` 或完全没有任何缓存头；
  - **ShortOrRevalidate**（notice，"<1 天"）：`no-cache`、max-age < **86,400s（1 天）**、或只有 ETag/Last-Modified 无寿命；
  - **LongLived**：max-age ≥ 1 天（指纹化静态资产的理想值）。
- 输出按 content-type × cache-type、domain × cache-type 两张表，各带 avg/min/max lifetime。缓存寿命着色：≤0 红 / <600s 品红 / ≤86,400s 黄 / >1 天 绿。
- 审计建议口径：HTML 主文档短缓存正常；**带指纹的 CSS/JS/图片应 LongLived（≥1 年 + immutable 更佳）**；未指纹资产用短 max-age + 协商缓存。

### 状态码分桶与页面重量（ContentTypeAnalyzer）

- 每类内容（HTML/Script/CSS/Image/Video/Audio/Font/Document/JSON/XML/Redirect/Other）统计 count/总字节/总耗时/**20x/30x/40x/42x(420–499)/50x/ERR 六桶**——按内容类型看 5xx 常只炸某一类（如 Image 全 503）。状态码着色：2xx 绿 / 3xx 黄 / 4xx 品红 / 5xx 与网络错误红。
- **页面重量预算**（按 HTTP Archive 移动端中位数取整）：直接子资源传输总量 > **2.5MB（2,500,000 字节）**=warning；请求数 > **75**=notice。只计直接子资源（img/script/link/css/font/media），`<a href>`/重定向/初始 URL/sitemap 条目不算其他页面的重量——是保守下界。
