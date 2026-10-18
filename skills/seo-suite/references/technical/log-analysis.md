# 服务器日志分析（爬虫行为的实测层）

> 2026-10-18 按 Google、Bing、Yandex、OpenAI、Anthropic、Perplexity 的官方文档和 nginx、Apache、Cloudflare 文档核对。日志记录真实请求，不是模拟。Google 自己也说客户端分析工具不能完整反映 Googlebot 和渲染服务的访问（[修复 JS 搜索问题](https://developers.google.com/search/docs/crawling-indexing/javascript/fix-search-javascript)）；不执行 JS 的爬虫在 GA4 里根本看不到，所以 AI 爬虫到访只能靠日志或 CDN 日志测量。

## 一、日志能回答的问题

- **真实爬虫频率与分布**：每个爬虫每天的请求数，按目录、深度的分布，最常被抓和从未被抓的 URL。
- **抓取浪费**：参数化或重复 URL、重定向链、被 robots.txt 屏蔽仍被请求的路径、低价值页占比。
- **AI 爬虫实际来访**：哪些 AI 爬虫真的来了，与 robots.txt 的决定对照。
- **5xx / 429 的影响**：Google 遇到 5xx 和 429 会暂时降低抓取速度；持续返回 5xx 的已收录 URL 最终移出索引；robots.txt 本身返回 5xx 时，前 12 小时停止抓取全站（见 [http-status-codes.md](http-status-codes.md)、[robots-txt-reference.md](robots-txt-reference.md)）。
- **发现延迟**：发布时间到首次被抓的时间差，可以直接从日志算。

抓取预算问题主要出现在大站：Google 的抓取预算指南面向 100 万以上页面且每周更新、或 1 万以上页面且每天更新的站点（[抓取预算](https://developers.google.com/crawling/docs/crawl-budget)）。小站先看 sitemap 和网页索引编制报告即可。

## 二、方法

1. **字段最低集**：时间、客户端 IP、方法、完整 URL（含查询串）、状态码、User-Agent；建议再加 referer、字节数、响应耗时。nginx 默认的 `combined` 格式不含响应耗时，SEO 用途要自定义 `log_format`（见二B）。
2. **先验证爬虫身份，再聚合**：User-Agent 可以伪造。验证方法见二C。
3. **聚合维度**：URL 目录层级 × 状态码 × 爬虫 × 日期；衍生指标见二D。
4. **日志源**：Apache / nginx 原始日志；用了 Cloudflare 的站点，用 Logpush 导出边缘日志。

## 二B、日志格式与解析

**nginx `combined`**（nginx 官方定义；Apache 的 combined 同构）：

```nginx
log_format combined '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent"';
```

- 按空白切分时 `$9` 是状态码、`$7` 是路径；但 User-Agent 含空格，按空白切分取不到它。稳妥做法是按双引号切分：`-F'"'` 后 `$2` 是请求行，`$3` 开头是状态码，`$6` 是 User-Agent。自定义格式要按自己的格式写解析。
- 解析正则（combined）：

```text
^(\S+) (\S+) (\S+) \[([^\]]+)\] "(\S+) (\S+)(?: (\S+))?" (\d{3}) (\S+) "([^"]*)" "([^"]*)"
  1=IP 2=ident 3=user 4=时间 5=方法 6=URL 7=协议 8=状态码 9=字节 10=referer 11=UA
```

- SEO 用的 nginx 格式（加响应耗时）：`$request_time` 是请求处理时间（秒，毫秒精度，从读到客户端第一个字节算起）；`$upstream_response_time` 是从上游收到响应的耗时（秒，毫秒精度，多个上游用逗号分隔）。

```nginx
log_format seo '$remote_addr [$time_local] "$request" $status $body_bytes_sent '
               '"$http_referer" "$http_user_agent" $request_time $upstream_response_time';
```

- Apache：`mod_log_config` 的 `%D` 是服务请求的耗时（微秒），`%T` 是秒。
- **Cloudflare 回源**：源站日志里的 `$remote_addr` 是 Cloudflare 边缘 IP。Cloudflare 用 `CF-Connecting-IP` 请求头把访客 IP 传给源站；nginx 要用 realip 模块（`set_real_ip_from` 填 Cloudflare 的 IP 段，`real_ip_header CF-Connecting-IP`）还原，否则所有按 IP 的爬虫验证都会错。
- **Cloudflare Logpush**（JSON 行，用 jq）：`http_requests` 数据集的字段包括 `ClientIP`、`ClientRequestUserAgent`、`ClientRequestURI`、`EdgeResponseStatus`（Cloudflare 返回给客户端的状态码）、`OriginResponseStatus`（源站状态码）、`EdgeStartTimestamp`、`VerifiedBotCategory`、`BotScore`。Logpush 任务可以设 `sample_rate`（0–1，默认 1 = 不采样）。

```bash
# AI 爬虫请求：边缘状态码、源站状态码、路径
jq -r 'select(.ClientRequestUserAgent|test("GPTBot|OAI-SearchBot|ClaudeBot|Claude-SearchBot|PerplexityBot";"i"))
       | "\(.EdgeResponseStatus) \(.OriginResponseStatus) \(.ClientRequestURI)"' logs.jsonl | sort | uniq -c | sort -rn
```

## 二C、爬虫身份验证

User-Agent 单独不可信。各家官方给的验证方法（核对 2026-10-18；IP 列表格式都是 `{"prefixes":[{"ipv4Prefix"|"ipv6Prefix": CIDR}]}`，2026-10-18 实测可下载）：

| 运营方 | 方法 | 反向 DNS 应落在 | 官方 IP 列表 |
|---|---|---|---|
| Google | 反向 + 正向 DNS，或匹配 IP 列表（[官方文档](https://developers.google.com/crawling/docs/crawlers-fetchers/verify-google-requests)） | 常见爬虫（含 Googlebot）：`googlebot.com`；特殊爬虫（如 AdsBot）：`google.com`；用户触发的抓取器：`googleusercontent.com` 或 `google.com` | [common-crawlers.json](https://developers.google.com/static/crawling/ipranges/common-crawlers.json)、[special-crawlers.json](https://developers.google.com/static/crawling/ipranges/special-crawlers.json)、[user-triggered-fetchers.json](https://developers.google.com/static/crawling/ipranges/user-triggered-fetchers.json)、[user-triggered-fetchers-google.json](https://developers.google.com/static/crawling/ipranges/user-triggered-fetchers-google.json) |
| Bing | 反向 + 正向 DNS；或匹配 IP 列表，列表要每天刷新（[官方文档](https://www.bing.com/webmasters/help/how-to-verify-bingbot-3905dc26)） | `search.msn.com` | [bingbot.json](https://www.bing.com/toolbox/bingbot.json) |
| Yandex | 反向 + 正向 DNS；IP 列表不公开（[官方文档](https://yandex.com/support/webmaster/en/robot-workings/check-yandex-robots)） | `yandex.ru`、`yandex.net`、`yandex.com` | 无 |
| OpenAI | 匹配 IP 列表（[官方文档](https://platform.openai.com/docs/bots)） | — | [gptbot.json](https://openai.com/gptbot.json)、[searchbot.json](https://openai.com/searchbot.json)、[chatgpt-user.json](https://openai.com/chatgpt-user.json) |
| Anthropic | 匹配 IP 列表（三个爬虫共用；[官方说明](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)） | — | [bots.json](https://claude.com/crawling/bots.json) |
| Perplexity | 匹配 IP 列表（[官方文档](https://docs.perplexity.ai/guides/bots)） | — | [perplexitybot.json](https://www.perplexity.com/perplexitybot.json)、[perplexity-user.json](https://www.perplexity.com/perplexity-user.json) |

判定规则（本套件口径）：UA 名称与官方验证同时成立才算真；UA 对、验证不过 = 伪装，按 IP 封。Google 的旧列表地址 `/static/search/apis/ipranges/googlebot.json` 2026-10-18 仍可访问且内容与 `common-crawlers.json` 相同，新脚本用新地址。

```bash
# 方法一：反向 + 正向 DNS（bash / zsh 通用；后缀前加点，正向解析要精确等于原 IP）
verify_rdns() {  # 用法：verify_rdns <IP> <允许的域名后缀...>
  ip=$1; shift
  name=$(host "$ip" | awk '/domain name pointer/ {print $NF}' | sed 's/\.$//' | head -1)
  [ -z "$name" ] && { echo "$ip FAIL 无反向解析记录"; return; }
  ok=no
  for d in "$@"; do case "$name" in *."$d") ok=yes ;; esac; done
  [ "$ok" = no ] && { echo "$ip FAIL $name 不在允许的域名内"; return; }
  if host "$name" | awk '/has (IPv6 )?address/ {print $NF}' | grep -qxF "$ip"; then
    echo "$ip VERIFIED $name"
  else
    echo "$ip FAIL $name 正向解析不回到原 IP"
  fi
}
verify_rdns 66.249.66.1 googlebot.com      # Googlebot
verify_rdns 157.55.39.1 search.msn.com     # bingbot

# 方法二：匹配官方 IP 列表（先下载需要的 JSON；日志 IP 一行一个从 stdin 读入）
curl -sO https://developers.google.com/static/crawling/ipranges/common-crawlers.json
curl -sO https://openai.com/gptbot.json
awk -F'"' '$6 ~ /Googlebot|GPTBot/ {split($1,f," "); print f[1]}' access.log | sort -u | python3 -I -c '
import ipaddress, json, sys
nets = [(ipaddress.ip_network(p.get("ipv4Prefix") or p.get("ipv6Prefix")), f)
        for f in ("common-crawlers.json", "gptbot.json") for p in json.load(open(f))["prefixes"]]
for ip in (l.strip() for l in sys.stdin if l.strip()):
    a = ipaddress.ip_address(ip)
    hit = next((f for n, f in nets if a.version == n.version and a in n), "")
    print(ip, "VERIFIED" if hit else "NOT-IN-LIST", hit)'
```

## 二D、聚合指标速查

| 指标 | 公式（只用已验证的爬虫请求） | 判读 |
|---|---|---|
| 日均请求数 | 总请求数 ÷ 天数 | 实测抓取量（案例 C） |
| 每日唯一 URL 数 | 去重 URL 数 | 有效抓取面；与总请求的差 = 重复抓取 |
| 重复抓取率 | 总请求 ÷ 唯一 URL | 无变化页面被高频重抓：检查 lastmod 和 304 支持 |
| 5xx 占比 | 5xx 请求 ÷ 总数 | Google 没有给出阈值；持续上升就查（案例 A） |
| 3xx 占比 | 3xx 请求 ÷ 总数 | 抓取花在跳转上；本套件口径：持续 >10% 进清理清单（见 [redirects-canonical](redirects-canonical.md) 6.1） |
| 目录占比 | 按一级目录求和 | 核心目录与参数、长尾目录的分配 |
| 抓取深度分布 | 按 URL 路径段数分桶 | 深层占比高：导航或 sitemap 层级有问题 |
| 发现延迟 | 首次被抓时间 − 发布时间 | 要与 CMS 发布时间关联 |

**跨源合并的五个坑**（本套件口径）：
1. **时区**：nginx `$time_local` 用服务器本地时区，Cloudflare 时间戳是 UTC；合并前统一，否则按日聚合会错位。
2. **CDN 边界**：命中边缘缓存的请求不回源，源站日志会低估热门页的到访；算爬虫到访用边缘日志，算源站压力用源站日志。
3. **采样**：Logpush 设了 `sample_rate` 时，小流量目录会失真；先看采样设置再下结论。
4. **WAF 质询**：边缘对爬虫返回 403/503 不是源站错误；排查 5xx 用 `OriginResponseStatus`，不要用 `EdgeResponseStatus`。
5. **轮转与缺口**：按天压缩的历史日志先 `zcat` 合并；缺天的时段在报告里写明，否则趋势会误读。

## 三、AI 爬虫

- 按 UA 名称过滤（如 GPTBot、OAI-SearchBot、ChatGPT-User、ClaudeBot、Claude-SearchBot、Claude-User、PerplexityBot、Perplexity-User），再用二C 的官方 IP 列表验证。各名称的用途与 robots.txt 规则见 [robots-txt-reference.md](robots-txt-reference.md) 第五节。
- 套件脚本：`python3 scripts/ai_referral_log.py access.log --bot-ua --classify` 输出 AI 爬虫分类、各爬虫的状态码矩阵和失败率。
- **Bytespider**：多份社区报告说它不遵守 robots.txt（例如 [F5 DevCentral 2024-02-01](https://community.f5.com/t/bytespider-webcrawler-unintentional-dos/73929)）；没有找到运营方公开的爬虫说明或 IP 列表。要拦就在 CDN/WAF 边缘按 UA 拦，再用日志确认拦截生效（第三方报告，未经官方证实）。
- 本套件口径：按 AI 爬虫建「到访量 × 状态码 × 目录」时间序列，作为内容被 AI 系统获取的前提信号；**到访不等于被引用**，要与品牌提及、引用监测一起看。

## 实战三案例（本套件口径）

**案例 A：5xx 导致抓取降频。** 信号：已验证的 Googlebot 请求里 5xx 占比逐周上升。Google 的机制：5xx 和 429 让抓取暂时降速，降幅与报错 URL 数成正比；恢复 2xx 后逐步回升。步骤：(1) 按日 × 状态码透视，先分清 5xx 是全流量都有，还是只出现在爬虫流量——只返回给爬虫的 5xx，用户和 JS 分析都看不到，日志是唯一证据；(2) 结合 `$upstream_response_time` 找慢端点；(3) 修好后按周看抓取曲线，抓取回升晚于服务器恢复，不要两三天就下结论。预防：优化服务器响应时间，支持 304（`If-Modified-Since` / `If-None-Match`）（Google 抓取预算与排查抓取错误文档）。

**案例 B：AI 爬虫封锁失效。** 已在 CDN/WAF 封了某个 AI 爬虫，日志里仍有它的 UA。两类根因：(1) 规则写成 UA「完全等于」，真实 UA 是带其他字段的长串——改成「包含」；(2) 伪装 UA：UA 写着 GPTBot，IP 却不在 OpenAI 公布的列表里。判定：UA 命中且 IP 在官方列表 = 规则真的没生效（查规则顺序和绕过）；UA 命中但 IP 不在列表 = 伪装，按 IP 封。

**案例 C：算实测抓取量，用日志驱动 sitemap。** 每日已验证 Googlebot 请求数 = 实测抓取量；再拆每日唯一 URL 数和各目录占比。闭环：
- 从没被抓的高价值 URL → 放进单独的 sitemap，写真实的 lastmod。
- 高频重抓但没变化的稳定 URL → 停止「每次构建都刷新 lastmod」。Google 只在 lastmod 一贯可核实地准确时才使用它（[构建 sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)）。
- 浪费大头（参数化、重复 URL）→ 用 robots.txt 或参数处理收口；14 天后按目录占比复测，看省下的抓取有没有回到核心目录。

三个案例的第一步都一样：先验证爬虫身份，再聚合；第二步都是按日看趋势，不只看总量。

## 四、a11y 与 SEO 的重叠（本套件口径）

| 类别 | 项目 | 归宿 |
|---|---|---|
| 与 SEO 重叠（机器可读性同源） | 语义化标题、有意义的 alt、描述性链接文本、表单 label 关联、文字转录、`lang` 属性 | 技术审计 |
| 主要服务人类 | 对比度、键盘焦点顺序、ARIA live、跳转链接、触控目标 | 合规审计 |
| 服务 AI 代理 | 按钮和链接的可访问名称、表单标签、ARIA 结构正确；布局位移导致误点 | 见 [agent-readiness.md](agent-readiness.md) |

## 五、工具

| 场景 | 工具 | 说明 |
|---|---|---|
| 临时体检 | [goaccess](https://github.com/allinurl/goaccess)、[rhit](https://github.com/Canop/rhit) | 终端里直接读 nginx 日志 |
| 找慢端点（案例 A） | [kataribe](https://github.com/matsuu/kataribe) | 按响应时间聚合（仓库最后更新 2022） |
| SEO 维度透视 | Screaming Frog Log File Analyser | 自动验证搜索引擎与 AI 爬虫；免费版限 1,000 行日志、1 个项目（[官方页面](https://www.screamingfrog.co.uk/log-file-analyser/)） |
| Googlebot 会话与陷阱 | `python3 scripts/log_session.py --log access.log --window 30m --json` | 按 IP + UA 拼会话，标出参数循环、过深抓取、超量会话 |
| AI 爬虫与 AI 引荐 | `python3 scripts/ai_referral_log.py access.log --bot-ua --classify` | 见第三节 |
| 持续监测 | Logpush → 对象存储 + jq 脚本 | 可回放、可自动化；口径可比性比工具本身重要 |

**从零开始采集**（本套件口径）：
1. 定 `log_format`（含 `$request_time`、`$upstream_response_time`）；改格式会打断历史可比性，从生效日开始积累。
2. 留存至少 90 天（压缩归档即可），发现延迟和季节对比需要长窗口。
3. Cloudflare 站点：Logpush 不采样全量推送，并记录采样设置。
4. 把时区和轮转策略写进审计报告（二D 坑 1、5）。
5. 首次分析前先抽样跑一天爬虫验证（二C），确认 IP 已正确还原（Cloudflare 站点尤其要查）。

## 检查清单

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 日志字段够用 | 看一行日志是否含 IP、时间、请求行、状态码、UA、耗时 | 失败：缺 UA 或缺查询串；没有耗时字段时只能做状态码分析 |
| 2 | 客户端 IP 是真实访客 IP | 抽查日志 IP 是否落在 Cloudflare 等 CDN 的 IP 段 | 失败：大量 CDN 边缘 IP（未配置 realip） |
| 3 | 爬虫身份已验证 | 对日志里自称 Googlebot/bingbot/GPTBot 等的 IP 跑二C 的两种方法 | 报告里写明验证通过率；伪装占比高时，后续指标只用已验证的请求 |
| 4 | 状态码分布 | 命令 1 | 关注：5xx 持续上升；3xx 占比持续高 |
| 5 | 每日抓取量趋势 | 命令 2 | 关注：突降（对照服务器事故、robots 改动、上线）或突增（分面、日历类 URL 陷阱） |
| 6 | 抓取流向 | 命令 3 | 关注：参数目录、搜索结果页占比高；核心目录占比低 |
| 7 | AI 爬虫到访与状态 | 命令 4，或 `ai_referral_log.py --bot-ua --classify` | 失败：用户决定放行的爬虫大量收到 403/5xx；决定封锁的爬虫仍拿到 200 |
| 8 | 与 Google 侧对照 | Search Console 抓取统计（按响应、按 Googlebot 类型） | 失败：日志与抓取统计的状态码结构差异大（多半是 CDN/WAF 按 UA 分叉） |

```bash
# 命令 1：Googlebot 状态码分布（combined；先粗看，验证身份后再精算）
awk -F'"' '$6 ~ /Googlebot/ {split($3, s, " "); print s[1]}' access.log | sort | uniq -c | sort -rn
# 命令 2：每日请求量
awk -F'"' '$6 ~ /Googlebot/ {split($1, f, " "); print substr(f[4], 2, 11)}' access.log | sort | uniq -c
# 命令 3：被抓最多的一级目录（去掉查询串）
awk -F'"' '$6 ~ /Googlebot/ {split($2, r, " "); split(r[2], q, "?"); split(q[1], a, "/"); print "/" a[2]}' access.log \
  | sort | uniq -c | sort -rn | head -20
# 命令 4：AI 爬虫的 IP 与状态码（再用二C 验证 IP）
awk -F'"' '$6 ~ /GPTBot|OAI-SearchBot|ChatGPT-User|ClaudeBot|Claude-SearchBot|Claude-User|PerplexityBot|Perplexity-User/ \
  {split($1, f, " "); split($3, s, " "); print f[1], s[1]}' access.log | sort | uniq -c | sort -rn | head -30
```

## 来源

- 爬虫验证：[Google](https://developers.google.com/crawling/docs/crawlers-fetchers/verify-google-requests)、[Bing](https://www.bing.com/webmasters/help/how-to-verify-bingbot-3905dc26)、[Yandex](https://yandex.com/support/webmaster/en/robot-workings/check-yandex-robots)、[OpenAI](https://platform.openai.com/docs/bots)、[Anthropic](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)、[Perplexity](https://docs.perplexity.ai/guides/bots)
- Google 抓取行为：[HTTP 状态码对抓取的影响](https://developers.google.com/crawling/docs/troubleshooting/http-status-codes)、[抓取预算](https://developers.google.com/crawling/docs/crawl-budget)、[排查抓取错误（304 与条件请求）](https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors)、[构建 sitemap（lastmod）](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)、[抓取统计报告](https://support.google.com/webmasters/answer/9679690)
- 日志格式：[nginx log 模块](https://nginx.org/en/docs/http/ngx_http_log_module.html)、[nginx core 变量](https://nginx.org/en/docs/http/ngx_http_core_module.html)、[nginx upstream 变量](https://nginx.org/en/docs/http/ngx_http_upstream_module.html)、[nginx realip](https://nginx.org/en/docs/http/ngx_http_realip_module.html)、[Apache mod_log_config](https://httpd.apache.org/docs/current/mod/mod_log_config.html)、[Cloudflare HTTP 请求头](https://developers.cloudflare.com/fundamentals/reference/http-headers/)、[Cloudflare http_requests 字段](https://developers.cloudflare.com/logs/logpush/logpush-job/datasets/zone/http_requests/)、[Logpush 采样](https://developers.cloudflare.com/logs/logpush/logpush-job/api-configuration/)
- 第三方：[F5 DevCentral 社区帖（Bytespider，2024-02-01）](https://community.f5.com/t/bytespider-webcrawler-unintentional-dos/73929)
- 命令与脚本均在样例日志上实测（2026-10-18）。
