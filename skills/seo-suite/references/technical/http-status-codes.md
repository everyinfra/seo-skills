# HTTP 状态码与抓取、索引

## 用途

技术审计、网站迁移、排查「页面不被编入索引 / 从结果里消失」时读。判断以 Google 的 [HTTP 状态码对抓取的影响](https://developers.google.com/crawling/docs/troubleshooting/http-status-codes)、[网络与 DNS 错误](https://developers.google.com/crawling/docs/troubleshooting/dns-network-errors) 和 [重定向](https://developers.google.com/search/docs/crawling-indexing/301-redirects) 文档为准（前两份于 2025-12-18 迁到 developers.google.com/crawling）。其他搜索引擎的处理可能不同。核对 2026-10-21。

> 本文管状态码语义与排查；重定向的全类型用法、canonical 场景、分页 / 分面治理与审计操作见 [redirects-canonical](redirects-canonical.md)。

## 一、Google 如何处理各类状态码

| 状态码 | Google 的处理 | 什么时候用 |
|---|---|---|
| 200 | 把收到的内容交给下一步（搜索是索引流程），不保证编入索引。内容像错误页或空页时，Search Console 报 soft 404 | 正常页面 |
| 202 | 等待有限时间，再把已收到的内容交出去 | 异步生成的内容，慎用 |
| 204 | 收不到内容，无法处理 | 不用于希望编入索引的页面 |
| 301、308 | 强信号：重定向目标应成为规范网址；搜索结果显示新 URL | 永久改址、合并页面、HTTP 转 HTTPS |
| 302、303、307 | Google 跟随重定向；重定向文档说它不作为规范化信号，状态码文档称它为「弱信号」；搜索结果通常显示原 URL | 临时活动、短期维护跳转 |
| 304 | 告知内容与上次抓取相同；索引可能重算信号，此外不影响索引 | 条件请求，节省抓取 |
| 4xx（429 除外，含 401、403、404、410） | 一律视为内容不存在：已编入的 URL 移出索引；新遇到的 404 不处理；抓取频率逐渐下降 | 删除且没有替代的内容 |
| 429 | 视为服务器过载，按服务器错误处理 | 临时限流 |
| 5xx | 暂时降低抓取速度，降幅与报错 URL 的数量成正比；已编入的 URL 先保留，持续报错最终移出；恢复 2xx 后抓取速度逐步回升 | 只应是短暂故障 |
| DNS 错误、超时、连接重置 | 与 5xx 类似，立即降速；无法访问的已编入 URL 几天内移出索引 | 查 DNS、CDN、防火墙 |

补充：

- Google 爬虫默认最多跟随 10 跳重定向；超过、循环、目标 URL 超长或为空，网页索引编制报告记为「重定向错误」。
- 状态码文档写 Google 检查工具不跟随重定向；网址检查帮助写实时测试会先跟随重定向、再测终点，且不显示终点 URL。两处说法不同，所以查跳转链用 `curl`，不要用网址检查。
- Googlebot 不带凭据访问。对它返回 403，页面不会被编入索引（网页索引编制报告说明）。

## 二、soft 404

返回 200，页面上却是「未找到」「商品已下架」、空的分类或站内搜索结果，或者渲染失败只剩空壳，都可能被判为 soft 404。Google 把这类页面排除出搜索结果，而且会继续抓取它们，浪费抓取预算。处理方法三选一（[排查抓取错误](https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors)）：

- 内容确实没了、也没有替代 → 返回 404 或 410。
- 有相关的替代页 → 301 到替代页。
- 页面本来有用 → 补足内容，修好渲染（常见原因：缺关键资源、渲染时报错）。

不要把大量旧 URL 重定向到一个不相关的页面（例如首页）。Google 的迁移文档说这可能被当作 soft 404。分面组合没有结果时，在原 URL 上直接返回 404，不要跳到统一的「未找到」页（[分面导航](https://developers.google.com/crawling/docs/faceted-navigation)）。

## 三、重定向

- 优先用服务端重定向。Google 对各种实现的识别把握从高到低是：服务端 3xx、meta refresh、JavaScript `location`。
- 0 秒的 meta refresh 按永久重定向处理；延迟的 meta refresh 按临时处理。
- 永久变更用 301 或 308，临时变更用 302 或 307。
- 链路直接指向最终 URL。迁移文档的建议是：做不到一跳时，链长最好不超过 3 跳，且少于 5 跳。
- 检查循环重定向（A → B → A）。
- 内链、sitemap、canonical、hreflang 都直接写最终 URL，这些 URL 本身应返回 200。

## 四、改址迁移

按 [网站迁移](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes) 文档：

1. 旧 URL 到新 URL 一对一映射；只有确实没有对应页的，才返回 404/410。不要把多个旧 URL 指到一个不相关的页面。
2. 上线前逐条测试映射表：每条都返回 301 或 308，并且一跳到达。
3. 同步更新内链、canonical（每个新 URL 自引用）、hreflang 和 sitemap。
4. 重定向尽量长期保留，一般至少一年。
5. 换域名或子域名时，在 Search Console 对旧站提交「地址更改」，网域的各个变体（含 www 与非 www）都要处理。HTTP 转 HTTPS、www 与非 www 互换、同域换路径不需要这个工具。
6. 上线后看网页索引编制报告、Sitemaps 报告和抓取统计。中型站点一般要几周，大部分页面才换成新 URL。
7. 301 等永久重定向不会造成 PageRank 损失（迁移文档原话）。

## 五、维护与限流

- 紧急降速（几小时到 1–2 天）：返回 500、503 或 429；503 和 429 可以带 `Retry-After`（秒数或绝对 UTC 时间）。Google 会降低整个主机名的抓取速度，错误减少后自动回升（[降低抓取速度](https://developers.google.com/crawling/docs/crawlers-fetchers/reduce-crawl-rate)）。
- 不要用 401、403、404 限速：除 429 外的 4xx 对抓取速度没有影响，反而会让 URL 被当作不存在并移出索引。
- 不能返回错误码时，用 Search Console 的特殊请求表单报告抓取过高；只能申请降低，不能申请提高。
- CDN 或 WAF 误拦 Googlebot 是常见事故。拦截前先核实爬虫真伪（反向 DNS 或官方 IP 列表，见 [log-analysis.md](log-analysis.md) 二C），不要按 User-Agent 字符串一刀切；防火墙要放行 Google 的 IP 和 DNS 查询（UDP 与 TCP）。

## 六、排查方法

- 看首个响应的状态码：浏览器开发者工具的「网络」面板，或命令行逐跳查看。
- 用 Search Console 的网址检查（需要该站点的权限）看 Google 抓到的版本；「Page fetch」「Crawled as」「Last crawl」三个字段最常用。
- 看网页索引编制报告的原因分类：服务器错误（5xx）、重定向错误、未找到（404）、soft 404、401、403、其他 4xx。
- 抓取统计报告（只对网域或根级网址前缀资源可用，设置 → 抓取统计）按「抓取响应」「文件类型」「抓取用途」「Googlebot 类型」分组，并显示主机状态。
- 服务器日志按状态码和爬虫统计。CDN 或 WAF 规则可能对不同 User-Agent、不同地区返回不同结果，要分别测试。

## 检查清单

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 首个响应与跳转链 | 命令 1 | 通过：页面 200，或一跳 301/308 到 200。失败：多于 1 跳、出现 302/307 做永久跳转、循环、终点不是 200 |
| 2 | 批量重定向链 | `python3 scripts/redirect_chain.py https://example.com/old --max 3` | 通过：无 CRITICAL。失败：超过 3 跳、循环、链中夹临时跳转 |
| 3 | 删除页返回真 404/410 | 命令 2：随机请求一个不存在的路径 | 通过：404 或 410。失败：200（soft 404 风险）或 3xx 到首页 |
| 4 | 爬虫与浏览器结果一致 | 命令 3：用浏览器 UA 和 Googlebot UA 各请求一次 | 失败：两者状态码不同（多半是 CDN/WAF 规则）。注意：伪造 UA 不能复现按 IP 判定的规则，最终以网址检查为准 |
| 5 | 维护期状态码正确 | 维护窗口内请求任意页面 | 通过：503（或 429）且带 `Retry-After`，持续不超过 1–2 天。失败：200 维护页、404、403 |
| 6 | Google 侧没有成片错误 | Search Console → 网页索引编制报告的服务器错误、重定向错误、soft 404；抓取统计 → 按响应分组 | 失败：重要模板出现成片 5xx、soft 404 或重定向错误 |
| 7 | DNS、连接与超时错误 | Search Console → 设置 → 抓取统计 → 主机状态（robots.txt 可用性、DNS 解析、服务器连接） | 通过：三项均为绿色。失败：红色：DNS 或连接错误会立即降低抓取速度，不可达的已编入 URL 几天内移出索引 |
| 8 | 日志里 Googlebot 的状态码分布 | 命令 4（combined 格式；先按 [log-analysis.md](log-analysis.md) 验证爬虫身份） | 关注：5xx 占比持续上升、3xx 占比高（抓取花在跳转上） |

```bash
# 命令 1：逐跳列出状态码和跳转目标（行数减 1 = 跳数）
curl -sIL --max-redirs 15 https://example.com/old-page | grep -iE '^(HTTP/|location:)'

# 命令 2：不存在的路径应返回 404/410
curl -s -o /dev/null -w '%{http_code}\n' "https://example.com/__no_such_page_$(date +%s)"

# 命令 3：同一 URL，浏览器 UA 与 Googlebot UA 的状态码对比
for ua in "Mozilla/5.0" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"; do
  curl -s -o /dev/null -A "$ua" -w "%{http_code}  $ua\n" https://example.com/page
done

# 命令 4：combined 日志里 Googlebot 请求的状态码分布（$9 是状态码，UA 在第 6 个引号字段）
awk -F'"' '$6 ~ /Googlebot/ {split($3, s, " "); print s[1]}' access.log | sort | uniq -c | sort -rn
```

## 常见误区

- 「410 比 404 快得多」：Google 文档说除 429 以外的 4xx 处理方式相同。
- 「302 完全不传递信号」：临时重定向也会被跟随；用 301/308 是为了把「永久」讲清楚。
- 「301 会损失百分之几的权重」：Google 迁移文档说永久重定向不会造成 PageRank 损失。
- 把所有删除页都 301 到首页：可能被当作 soft 404。
- 用 403 或 404 来限制抓取速度：会让页面移出索引。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。核对 2026-10-21。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/technical-seo-checker/references/http-status-codes.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/optimize/technical-seo-checker/references/http-status-codes.md)（Apache-2.0）
- 一手资料：[HTTP 状态码对 Google 抓取的影响](https://developers.google.com/crawling/docs/troubleshooting/http-status-codes)、[网络与 DNS 错误](https://developers.google.com/crawling/docs/troubleshooting/dns-network-errors)、[重定向](https://developers.google.com/search/docs/crawling-indexing/301-redirects)、[排查抓取错误（soft 404）](https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors)、[网站迁移](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)、[降低抓取速度](https://developers.google.com/crawling/docs/crawlers-fetchers/reduce-crawl-rate)、[抓取预算](https://developers.google.com/crawling/docs/crawl-budget)、[分面导航](https://developers.google.com/crawling/docs/faceted-navigation)、[网页索引编制报告](https://support.google.com/webmasters/answer/7440203)、[网址检查](https://support.google.com/webmasters/answer/9012289)、[抓取统计报告](https://support.google.com/webmasters/answer/9679690)、[MDN HTTP 状态码](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- 爬虫工具（如 siteone-crawler）的安全头、缓存、慢页严重度阈值不是 Google 规则，见 [ci-gates.md](../monitoring/ci-gates.md) 与 [alert-threshold-guide.md](../monitoring/alert-threshold-guide.md)。
