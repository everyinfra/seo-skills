# HTTP 状态码与抓取、索引

## 用途

技术审计、网站迁移、排查「页面不被编入索引 / 从结果里消失」时读。判断以 Google 的[HTTP 状态码与网络错误](https://developers.google.com/search/docs/crawling-indexing/http-network-errors)和[重定向](https://developers.google.com/search/docs/crawling-indexing/301-redirects)文档为准；其他搜索引擎的处理可能不同。

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
