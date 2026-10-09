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

## 三、AI 时代新价值(GEO 基线)

- 按 UA token(GPTBot/OAI-SearchBot/PerplexityBot/ClaudeBot/Bytespider)过滤+对照运营商公布 IP 段;grep/awk 即可入门。
- 行业基线(口径不一,仅参照):Cloudflare Radar 2026-05 GPTBot 占 AI bot 请求 11.48%、ClaudeBot 9.73%;HAProxy 实测其 AI 爬虫流量近 **90% 是 Bytespider**。
- **Bytespider 特例**:无视 robots.txt 且会伪装移动 UA(看 UA 尾部 token),只能靠 UA/IP 在边缘封锁——日志是验证封锁生效的证据。
- GEO 用法:按 AI UA 建"到访量×状态码×目录"时间序列,作为内容被 AI 系统纳入的先决信号基线;**到访≠引用**,与品牌提及监测互补。

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

## 完全装载:邮件认证信任信号/CrUX 双 origin/AI 爬虫先行指标(百仓深扫)

**邮件认证=域名信任上游信号**(quien,SPF RFC 7208):SPF 查询预算 10 次(include 树展开)/void 2 次/深度 10;DKIM 15 个常用 selector 探测(default/google/selector1-2/k1/mandrill/s1-s2/sig1…);DMARC=\_dmarc. TXT;BIMI=default.\_bimi.(含 VMC 证书链)——AI 引用倾向的上游信任层。
**CrUX 双 origin 回退**:先试重定向后最终 origin,再试输入域名("CrUX may index data under either");五指标阈值 LCP 2500/4000、INP 200/500、CLS 0.1/0.25、FCP 1800/3000、TTFB 800/1800;history 取 p75 时序画趋势。
**AI 爬虫访问量=引用先行指标**(leopard):`grep -iE 'GPTBot|OAI-SearchBot|ChatGPT-User|ClaudeBot|PerplexityBot' access.log | awk '{print $1}' | wc -l`;无日志用 Cloudflare/Vercel 机器人分类;改后 14 天重测,比较时**剔除最近 2-3 天聚合延迟**;"旧数据能通过一切下限——监控值的日期而非值"。

## 来源

官方:Google 状态码对爬虫影响/反向 DNS 验证/Bing IP 列表/evergreen Googlebot/Chrome agentic-browsing 文档。行业:Digital Applied 2026、Screaming Frog 22 法、Cloudflare Radar、HAProxy(Bytespider 90%)、F5(Bytespider 边缘封锁案例)、usegeon 实操。未证实项:"GPTBot/ClaudeBot 消费 sitemaps"仅 Reddit 单源;各 AI 流量份额口径互相矛盾只作粗基线;a11y 经 CWV 间接影响排名是假说无官方确认。
