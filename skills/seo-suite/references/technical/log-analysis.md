# 服务器日志分析(SEO/GEO 的真实测量层)

> 建立于 2026-10-09。日志是爬虫行为的唯一真实记录(非模拟);GA4 等 JS 分析**看不见不执行 JS 的 AI 爬虫**——日志是 AI 到访的唯一可靠测量层。

## 一、日志能回答的问题

- **真实 bot 频率/分布**:每 UA 每日请求数、按目录/深度分布、最常与从未被抓的 URL。
- **抓取预算浪费**:参数化/重复 URL、重定向链、被 robots 屏蔽仍被请求的路径、低价值页占比。
- **AI 爬虫实际来访**:哪些 AI UA 真的来了(与 robots.txt 声明对照)。
- **5xx/429 影响**:官方明确会使爬虫临时降速,持续则停止抓取与掉收录。
- **发现延迟**:发布时间戳→首次抓取时间差,可直接从日志算。

## 二、方法

1. **字段最低集**:timestamp、client IP、method、完整 URL(含 query)、status、user-agent;建议加 referer/bytes/response_time。Nginx 默认 `combined` 缺 response time——SEO 用途应自定义 log_format。
2. **bot 验证(关键)**:UA 单独不可信。Google 官方=**反向+正向 DNS 双重验证**(`host <IP>` 必须属于 googlebot.com/google.com,再正向解析回指原 IP);Yandex 同法;Bing 提供已验证 IP 列表。
3. **聚合维度**:URL 目录层级 × 状态码 × UA × 日;衍生:日均请求、抓取深度、状态码占比、唯一 URL 数、每目录预算占比。
4. **日志源**:Apache/Nginx 原始日志;Cloudflare 走 Logpush/GraphQL 导出。

## 二B、三源日志的解析正则(Nginx / Apache / Cloudflare,2026-10-09 二波深化)

**Nginx combined(Apache combined 同格式,正则通用)**:
```
^(\S+) (\S+) (\S+) \[([^\]]+)\] "(\S+) (\S+)(?: (\S+))?" (\d{3}) (\S+) "([^"]*)" "([^"]*)"
  1=IP 2=ident 3=user 4=时间         5=方法 6=URL  7=协议   8=状态  9=字节 10=referer 11=UA
```
最小可用聚合(状态码分布,combined 格式下 $9 恰为状态码):
```bash
grep -i googlebot access.log | awk '{print $9}' | sort | uniq -c | sort -rn
```
注意:UA 含空格,awk 按空白切列在自定义格式下会错位——**只有 combined 恰好第 9 列是状态码**;自定义格式必须走正则解析(Python re / goaccess)。SEO 用途建议的 nginx log_format(补响应耗时):
```nginx
log_format seo '$remote_addr [$time_local] "$request" $status $body_bytes_sent '
               '"$http_referer" "$http_user_agent" $request_time $upstream_response_time';
```
Apache:combined + `%D`(微秒)加耗时(mod_log_config);Cloudflare 若回源,`CF-Connecting-IP` 头才真实来源,`$remote_addr` 是 CF 边缘 IP——nginx 需 `set_real_ip_from` + `real_ip_header` 还原,否则按 IP 的 bot 验证全错。

**Cloudflare Logpush(JSON 行,用 jq 不用正则)**:
```bash
jq -r 'select(.ClientRequestUserAgent|test("GPTBot|ClaudeBot|Bytespider";"i"))
       | (.EdgeResponseStatus|tostring) + " " + .ClientRequestURI' logs.jsonl | sort | uniq -c | sort -rn
```
字段名:`ClientRequestUserAgent`/`EdgeResponseStatus`/`ClientRequestURI`;GraphQL API 可按时间窗拉状态码分布(Cloudflare 官方 Logpush/GraphQL 文档)。

## 二C、机器人验证脚本逻辑(双重 DNS,2026-10-09 二波深化)

UA 单独不可信(伪装 Googlebot 大量存在)。官方算法=反向+正向两步:
1. 取日志行 client IP;
2. `host <IP>` 反解得主机名,必须落在 `*.googlebot.com` 或 `*.google.com`;
3. 该主机名再正向解析,**必须回到原 IP**——防 DNS 命名抢注(官方 verifying-googlebot 文档)。
```bash
ip=66.249.66.1
hn=$(host $ip | awk '{print $NF}' | sed 's/\.$//')
if [[ $hn == *googlebot.com || $hn == *google.com ]] && host "$hn" | grep -q "$ip"; then echo verified; fi
```
Yandex 同法(yandex.com/yandex.ru);Bing 用官方已验证 IP 列表(必应官方 bot 文档)。AI 爬虫:OpenAI 公布 GPTBot/OAI-SearchBot 的 CIDR 段(openai.com/gptbot-ranges.txt);Anthropic、Perplexity 各自公布——验证逻辑=**UA token 与 IP 段同时命中**;只中 UA 不中 IP=伪装(见实战案例 B)。

## 二D、聚合指标速查(公式与判读,2026-10-09 二波深化)

| 指标 | 公式(验证后 bot 行) | 判读 |
|---|---|---|
| 日均请求数 | 总请求数 ÷ 天数 | 站点抓取预算实测(案例 C) |
| 每日唯一 URL 数 | nunique(URL) | 有效抓取面;与总请求的差=重复抓 |
| 重复抓取率 | 总请求 ÷ 唯一 URL | 高频无变化重抓=lastmod/ETag 失效信号 |
| 5xx 占比 | count(status≥500) ÷ 总数 | 持续抬升触发官方降速机制(案例 A);无官方阈值,行业以 1–2% 为关注线 |
| 3xx 占比 | count(3xx) ÷ 总数 | 预算烧在跳转链;与 redirects-canonical 审计联动 |
| 目录预算占比 | groupby(一级目录) 求和 | 核心目录 vs 长尾/参数目录的分配实况 |
| 抓取深度分布 | URL path 段数分桶 | 深层占比高=导航或 sitemap 层级问题 |
| 发现延迟 | first_seen(URL) − 发布时间戳 | 需与 CMS/内容库 join,衡量新页可达性 |

**跨源合并的五个坑**:
1. **时区**:nginx `time_local` 默认服务器本地时区,Apache/Cloudflare 各异——合并前统一 UTC,否则"按日"聚合错位。
2. **CDN 边界**:命中边缘缓存的请求不回源,origin 日志**低估**热门页到访量;算 bot 到访以边缘日志为准,算源站压力以 origin 为准——两套口径别混用。
3. **采样**:Cloudflare Logpush 可配采样率,低采样下小流量目录全失真——先看采样字段再下结论。
4. **WAF 质询**:边缘质询页对 bot 返回 403/503,不是源站错误——Cloudflare 区分 `EdgeResponseStatus` 与 `OriginResponseStatus`,5xx 诊断(案例 A)必须用 Origin 值。
5. **轮转与缺口**:按天 gzip 的历史文件先 `zcat` 合并;日志缺天时段要在报告里显式标注,否则趋势误读。

## 三、AI 时代新价值(GEO 基线)

- 按 UA token(GPTBot/OAI-SearchBot/PerplexityBot/ClaudeBot/Bytespider)过滤+对照运营商公布 IP 段;grep/awk 即可入门。
- 行业基线(口径不一,仅参照):Cloudflare Radar 2026-05 GPTBot 占 AI bot 请求 11.48%、ClaudeBot 9.73%;HAProxy 实测其 AI 爬虫流量近 **90% 是 Bytespider**。
- **Bytespider 特例**:无视 robots.txt 且会伪装移动 UA(看 UA 尾部 token),只能靠 UA/IP 在边缘封锁——日志是验证封锁生效的证据。
- GEO 用法:按 AI UA 建"到访量×状态码×目录"时间序列,作为内容被 AI 系统纳入的先决信号基线;**到访≠引用**,与品牌提及监测互补。

## 实战三案例(2026-10-09 二波深化)

**案例 A:诊断 5xx 引起的抓取降频**
信号链:日志中 Googlebot 命中 5xx 的占比逐周抬升 → 官方机制:持续 5xx/429 会使 Googlebot **临时降速**,极端时停抓(官方 crawl-budget 文档)。步骤:(1) 按日×状态码透视,先分清 5xx 是全流量还是**只出现在 bot 流量**——"只给爬虫返回 5xx"对用户和 JS 分析完全不可见,日志是唯一证据(Digital Applied 2026-05 日志指南);(2) 关联 `$upstream_response_time` 定位慢端点(反代到哪层开始慢);(3) 修复后 14 天曲线回看——**抓取率恢复滞后于服务器恢复**,别在 2-3 天内下结论。预防基线:官方建议平均响应时间压在 300-400ms 以下、支持 304(Not Modified)缓存(官方 crawl-budget 文档)。

**案例 B:发现 AI 爬虫封锁失效**
场景:已在 Cloudflare/WAF 封了 Bytespider/GPTBot,日志仍见其 UA。两类根因(社区实录):(1) 规则用 UA "equals" 精确匹配,真实 UA 是带附加 token 的长串——改 "contains" 即命中(Cloudflare 社区 2024-08 实帖);(2) **伪装 UA**:UA 显示 GPTBot 但 IP 不在 OpenAI 公布段(Cloudflare 社区 2024-01 实帖:origin 日志见 GPTBot 但 CF 明明已封)。验证法:UA token 命中+IP 段命中=真封锁失效(查规则顺序/绕过);UA 命中但 IP 不命中=伪装,按 IP 段封。Bytespider 无视 robots.txt 且伪装移动 UA,只能边缘封——封锁是否生效,只有日志能证明(见本文件三节)。

**案例 C:算真实抓取预算,并用日志驱动 sitemap 优先级**
公式:`日均已验证 Googlebot 请求数` = 站点抓取预算实测;再拆**每日唯一 URL 数**与**每目录预算占比**。行业实录:索引膨胀拖慢新页收录,清掉 72% 低价值索引后会话反涨(bigseo 案例)——预算此前被浪费在低价值 URL。日志→sitemap 闭环:
- 从未被抓的高价值 URL → 移入独立 sitemap、真实更新 lastmod;
- 高频重抓且无变化的稳定 URL → 停止"每次全量刷 lastmod"——**假 lastmod 会让 Google 对整个 sitemap 失去信任**(官方 sitemap 文档口径:用 lastmod 主要因它影响抓取);
- 浪费大头(参数化/重复 URL)→ robots.txt/参数处理收口,省出的预算是否回灌核心目录,回到日志按目录占比验证(改后 14 天重测)。

**案例复盘的共性**:三个案例的第一步都是同一件事——**先验证 bot 身份再聚合**(二C),否则伪装 UA 的噪音流量足以让 5xx 占比与预算测算全部失真;第二步都是按日透视而非总量汇总,趋势拐点(降速起点、封锁失效日、预算回灌日)只在时间序列里可见。

**快速起步三命令**(拿到 access.log 当天可出基线):
```bash
# 1. Googlebot 状态码分布(先粗看,验证后再精算)
grep -i 'googlebot' access.log | awk '{print $9}' | sort | uniq -c | sort -rn
# 2. 每日请求量趋势(抓取预算曲线)
grep -i 'googlebot' access.log | awk '{print substr($4,2,11)}' | sort | uniq -c
# 3. 最常被抓的目录前 20(预算流向)
grep -i 'googlebot' access.log | awk -F'"' '{print $2}' | awk '{split($2,a,"/"); print a[2]}' | sort | uniq -c | sort -rn | head -20
```



## 四、a11y × SEO(三分法,与 [agent-readiness](agent-readiness.md) 呼应)

官方口径:Google 用 evergreen Chromium 渲染,**a11y 不是直接排名因素**(Mueller 2022 明确)。

| 类别 | 项目 | 归宿 |
|---|---|---|
| **a11y∩SEO**(机器可读性同源) | 语义化标题层级、有意义 alt、描述性链接文本(锚文本)、title/label 关联、文字转录、lang 属性 | 技术审计 |
| **纯人类项**(无排名影响) | 对比度、键盘焦点顺序、ARIA live、skip links、触控目标 | 合规 |
| **agent 项**(新维度) | agent-accessibility-tree 所依赖的按钮/链接名称、表单标签、ARIA 良构;CLS(元素位移致 agent 误点) | agent-readiness 层 |

**"SEO 无关"的 a11y 项并非无价值**——Lighthouse 13.5 Agentic Browsing 的 33 条 axe 规则子集说明 agent 像屏幕阅读器用户一样依赖可访问性树(官方 Chrome 文档)。

## 五、工具

- [goaccess](https://github.com/allinurl/goaccess)(21k★,C 实时终端分析)、rhit(1,008★,Rust nginx 切片)、kataribe(364★,按响应时间聚合)、tango(113★,SEO 工程师写的 CLI)
- [awslabs/Log-Analyzer-with-MCP](https://github.com/awslabs/Log-Analyzer-with-MCP)(169★):MCP 服务器让 LLM 查日志——agent 化方向
- Screaming Frog Log File Analyser(免费版含 bot 自动验证)

**选型对照(2026-10-09 二波深化)**:

| 场景 | 首选 | 理由 |
|---|---|---|
| 一次性体检、临时 SSH 进机器 | goaccess / rhit | 零配置读 nginx 格式,秒级出图 |
| 按响应时间找慢端点(案例 A) | kataribe | 专为 upstream 耗时聚合设计 |
| SEO 维度(目录×UA×状态码透视) | tango / Screaming Frog LFA | 面向爬虫分析预设维度;LFA 免费版自带验证 |
| 持续监测、并入 agent 工作流 | Logpush→S3+jq 脚本,或 MCP | 可回放、可自动化;MCP 让 LLM 直接查询 |
| 每月例行报告 | 任一 + 固定脚本 | 口径可比性比工具本身重要 |

**采集落地清单(没有日志源时从零开始)**:
1. 定 log_format(含 `$request_time`/`$upstream_response_time`,见二B)——改格式会断历史可比性,改天生效后才开始积累;
2. 留存 ≥90 天(gzip 归档即可)——发现延迟与季节性对比需要长窗;
3. Cloudflare 站:Logpush 全量推 S3,注意采样字段;
4. 记录时区与轮转策略到审计报告(二D 的坑 1/5);
5. 首次分析前先跑一天 bot 验证抽样(二C),确认 IP 还原正确(CF 站尤其)。

## 完全装载:邮件认证信任信号/CrUX 双 origin/AI 爬虫先行指标(百仓深扫)

**邮件认证=域名信任上游信号**(quien,SPF RFC 7208):SPF 查询预算 10 次(include 树展开)/void 2 次/深度 10;DKIM 15 个常用 selector 探测(default/google/selector1-2/k1/mandrill/s1-s2/sig1…);DMARC=\_dmarc. TXT;BIMI=default.\_bimi.(含 VMC 证书链)——AI 引用倾向的上游信任层。
**CrUX 双 origin 回退**:先试重定向后最终 origin,再试输入域名("CrUX may index data under either");五指标阈值 LCP 2500/4000、INP 200/500、CLS 0.1/0.25、FCP 1800/3000、TTFB 800/1800;history 取 p75 时序画趋势。
**AI 爬虫访问量=引用先行指标**(leopard):`grep -iE 'GPTBot|OAI-SearchBot|ChatGPT-User|ClaudeBot|PerplexityBot' access.log | awk '{print $1}' | wc -l`;无日志用 Cloudflare/Vercel 机器人分类;改后 14 天重测,比较时**剔除最近 2-3 天聚合延迟**;"旧数据能通过一切下限——监控值的日期而非值"。

## 来源

官方:Google 状态码对爬虫影响/反向 DNS 验证/Bing IP 列表/evergreen Googlebot/Chrome agentic-browsing 文档;[Google 抓取预算管理文档](https://developers.google.com/crawling/docs/crawl-budget)(300-400ms 响应时间/304 缓存/5xx 降速机制)。行业:Digital Applied 2026、Screaming Frog 22 法、Cloudflare Radar、HAProxy(Bytespider 90%)、F5(Bytespider 边缘封锁案例)、usegeon 实操。二波深化新增:Cloudflare 社区实录两帖([Bytespider 绕过封锁 2024-08](https://community.cloudflare.com/t/bytespider-bot-bypassing-cf-despite-blocking-rule/697576)、[伪装 GPTBot 2024-01](https://community.cloudflare.com/t/efficient-way-of-handling-fake-gptbot-requests/604235));[bigseo 清理 72% 索引实录](https://www.reddit.com/r/bigseo/comments/dqkwkj/case_study_how_we_optimized_our_crawl_budget_by/);Cloudflare Logpush/GraphQL 字段口径(官方文档);nginx combined 正则为通用工程事实(easyengine 日志解析教程)。未证实项:"GPTBot/ClaudeBot 消费 sitemaps"仅 Reddit 单源;各 AI 流量份额口径互相矛盾只作粗基线;a11y 经 CWV 间接影响排名是假说无官方确认。
