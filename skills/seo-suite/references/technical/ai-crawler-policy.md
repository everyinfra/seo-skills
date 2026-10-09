# AI 爬虫政策参考（robots.txt 决策）

> 建立于 2026-10-09。bot 分类与频率参考 [Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) `docs/ai-bots-reference.md`（27 bot 表）与 [jianruntech/geo-score](https://github.com/jianruntech/geo-score)。按本套件证据约束改写。
> 用途：回答"我该在 robots.txt 里允许/禁止哪些 AI 爬虫"这个具体问题。

## 一、先分清两类 bot（最常见错误在这里）

**引用型（影响搜索/答案系统）**：

| Bot | 归属 | 用途 | 频率 |
|---|---|---|---|
| `OAI-SearchBot` | OpenAI | ChatGPT 搜索索引 | 日频 |
| `ChatGPT-User` | OpenAI | 按用户请求抓取 | 按需 |
| `Claude-SearchBot` | Anthropic | Claude 搜索索引 | 按需 |
| `Claude-User` | Anthropic | 按用户请求抓取 | 按需 |
| `PerplexityBot` | Perplexity | 搜索/链接（不训练） | 每周数次 |
| `Perplexity-User` | Perplexity | 按用户请求 | 按需 |
| `Googlebot` | Google | 通用收录+AIO | 高频 |
| `Applebot` | Apple | Siri/Spotlight | 日频 |

**训练型（基础模型训练，不影响搜索答案）**：`GPTBot`、`ClaudeBot`、`CCBot`（Common Crawl）。

**关键事实**：**禁 `GPTBot` 不阻止 ChatGPT 引用你**——引用走 `OAI-SearchBot`。大量站点把两者搞混，想保留引用却把训练 bot 的规则套在搜索 bot 上，或反之。Copilot 无独立 bot，读 Bing 索引。

## 二、四种典型诉求的配置

### 1. 全开放（默认推荐）

```
User-agent: *
Allow: /
```

不写任何 AI 专属规则。想保留训练型抓取也开放。

### 2. 保留 AI 搜索引用、退出模型训练

```
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: CCBot
Disallow: /
```

引用型 bot 不动。注意 `ChatGPT-User` / `Perplexity-User` 官方声明"可能无视 robots"——按请求抓取类的 bot 多数厂商声明不受 robots 约束，这是行业现状而非配置错误。

### 3. 退出特定引擎的搜索答案

- **ChatGPT**：禁 `OAI-SearchBot`（官方：禁它 = 从搜索答案消失）
- **Google AIO**：用 Search Console → 设置 → Search generative AI 开关（**`Google-Extended` 不控制 AIO**，只管 Gemini 训练——第二个高频错误）
- **Perplexity**：禁 `PerplexityBot`

### 4. 完全退出所有 AI

逐家做 2+3；并接受 `*-User` 类 bot 可能继续按单用户请求访问。**没有一键全退**。

## 三、市场差异:区域引擎的爬虫与收录

Google/OpenAI/Anthropic/Perplexity 之外,多个市场有独立的收录与 AI 答案通道:

| 市场 | Bot / 机制 | 行为(来源类型) | 决策 |
|---|---|---|---|
| 俄语区 | **`YandexAdditional`** | 供 Yandex 生成式答案(Нейро/Alice AI)取内容;是**唯一文档化的退出控制**——`User-agent: YandexAdditional / Disallow: /` 即退出;Forbes RU 等媒体已用此退出(Yandex 官方;案例 SEONews) | 想进俄语 AI 答案池=显式允许;与 GPTBot 等政策**分开决策** |
| 俄语区 | Yandex 主爬虫 | 经典收录走 YandexBot;**IndexNow**(Yandex 参与协议)可加速抓取(官方) | 俄语区把 IndexNow 纳入新鲜度策略 |
| **土耳其** | Yandex 系(同俄语区) | **Yandex 在土份额 ~26%(2026-09 StatCounter;3 月 ~13%,大反弹)**,YandexGPT SERP 答案同样存在 | 土耳其=第二个 Yandex 市场:Webmaster 注册与 YandexAdditional 决策同俄语区逻辑,且需 Google+Yandex 双引擎 |
| 韩语区 | Naver robot 收录 | 外部站需在 Search Advisor 发起 robots 收录请求;外部博客仅经收录后才出现在 Blog 标签(Naver 官方 Help) | 韩语流量前提是"被 Naver 收",不是"被爬" |
| 日语区 | bingbot | Bing 在日份额 28–33%(StatCounter),喂 Copilot 检索 | 日语区 Bing WMT 验证与可爬探测为必做项(多数市场可选项) |
| 越南 | Coc Cốc | 本地引擎 ~6% 份额,浏览器自带 AI 聊天机器人(官方 Play 页) | 越南向流量单独提交 Coc Cốc 收录 |
| 中文 | `Baiduspider` / `Bytespider` | 见中文 AI 搜索指南 | 中文站确认未被禁 |
| 法语区 | **MistralAI 三爬虫** | `MistralAI-User`(实时检索)/`MistralAI-Index`(索引)须放行;`MistralAI-Training` 仅训练、可封(Mistral 官方文档) | Vibe 引用面=GEO 目标;训练/检索分工模式的官方范例 |
| (全) | 过时 token | `anthropic-ai`、`Claude-Web`、`ChatGPT-Plugins` 已失效勿写;`Google-Extended` 不影响搜索排名(官方) | robots 审计先查死 token;**User/Index/Training 三分工**正在成为各家标配 |

**llms.txt 在区域市场的证据状态**:Yandex 无消费证据(俄社区视为仅策展);日本企业采用 6.4–6.8%(2026-09 测)但 John Mueller 明示无 AI 系统当前使用——**一切市场都只作低成本对冲,不承诺引用**。

**Yeti(Naver 爬虫)的 robots.txt 语义陷阱**(官方文档级,2026-10 深化)——四条与 Google 不同:
1. robots.txt 返回 **5xx → 全站封禁**(Google 用缓存兜底);返回 HTML → 可能被当作"无规则";
2. 规则按 **host/协议/端口隔离**——www 的规则救不了 apex 域;
3. `User-agent : Yeti`(冒号前空格)RFC 9309 合法,但 grep 检查会漏;
4. Yeti-only 白名单:`User-agent: * Disallow: /` + `User-agent: Yeti Allow: /`。
另:**`nosourceinfo` meta(全球唯一)**——Naver 独有的 robots meta 值,把页面排除出 AI 출처설명(AI 来源说明):有 AI 引用暴露策略(如隐藏 R&D 页)时的官方开关。og:image 三条件:>150×150、≥5,000B、长宽比≤3:1、每页唯一。IndexNow(Naver 端点)批量上限 10,000 URL;JobPosting/VideoObject **仅标记不收录,须제휴(合作)+Push 收集**。

**英文协议层(agent-readiness,2026-10 新增,语言中立)**:
- **ARD**(Agentic Resource Discovery,Google+Linux Foundation 2026-05):robots `Agentmap:` → `<link rel="ai-catalog">` → `/.well-known/ai-catalog.json` 三级发现链;Lighthouse 13.5+ `AGENTIC_BROWSING` 类别可校验。
- **WebMCP**(W3C WebML CG 草案,Chrome M149–156 origin trial):`document.modelContext.registerTool()` 页面级工具;目前仅 ChatGPT 桌面浏览器实证调用(单一消费者,标注)。
- **Web Bot Auth**:`draft-ietf-webbotauth-httpsig-protocol-00`(2026-09),`Signature-Agent` 字典——ChatGPT-User 以此签名。
- **Cloudflare 托管 robots.txt 坑**:Cloudflare 在响应端注入托管 Disallow(GPTBot/ClaudeBot 等),只存在于线上响应——**审计必须抓线上响应,不能只看源文件**。
- **Google 官方口径(2026-05-15)**:llms.txt/AI 专用标记/分块不被 Google 特殊对待;**`nosnippet` 一举把内容排除出 AIO/AI Mode 输入**(对照 `Google-Extended` 只管 Gemini 训练)。

## 四、暗坑清单

1. **WAF/CDN 拦截**：robots 宽松但 Cloudflare 等按 UA 挑战 AI bot——活体探测（发真实 bot UA）才能发现。robots.txt 只说"允不允许"，不说"到没到得了"。
2. **`Google-Extended` 误解**：它不是 AIO 开关。
3. **`GPTBot` 误解**：它不是 ChatGPT 引用开关。
4. **ai.txt / GEO link tags**：尚无引擎公开承诺遵守；有则加分，无则不扣。
5. **robots 与 llms.txt 矛盾**：llms.txt 列出的页对 AI 爬虫禁抓——白做一半。

## 五、探测方法

对每个引用型 bot：用其真实 UA string `curl -A` 访问首页与一个深页，记录状态码。200 = 可达；403/429/5xx/挑战页重定向 = 被拦。对照 robots 声明，标注"声明允许但实际被拦"的项——这类项修复收益最高（WAF 白名单一行的事）。

## 协商与放行的服务端实现(nuxt-ai-ready 源码深读,2026-10-09)

读 harlan-zw/nuxt-ai-ready `src/runtime/server/utils/`(markdown-request/negotiation-decision/negotiation-response/content-negotiation/link-header)+ `src/runtime/cache-control.ts` + skills/nuxt-ai-ready/SKILL.md + nuxt-seo docs llms-txt 篇。agent-readiness.md"完全装载"节已有决策摘要,这里补**可直接照抄的协议行为**。

**Content-Signal 的 robots.txt 实际格式**(SKILL.md 官方示例):`aiReady: { contentSignal: { search: true } }` 输出 `Content-Signal: ai-train=no, search=yes, ai-input=no`——**字段未配置即渲染为 no**(显式 opt-in 语义,与 robots Allow/Disallow 的默认开放相反,写政策时别搞反默认值)。

**协商失败的正确响应**:Accept 无法匹配时返回 **406 + `statusMessage: 'Not Acceptable'` + body 提示 `Supported types: text/html, text/markdown, text/plain`**,并 `appendHeader vary` + 设不可缓存头。协商成功的 HTML 直通响应也会 `Vary: Accept`(botNegotiation 开启时扩为 `Accept, Sec-Fetch-Dest, User-Agent`——**Sec-Fetch-Dest=document 视为浏览器导航,绕过 bot 启发式**)。

**缓存头的 Cloudflare 特化**(`cache-control.ts` 注释原文):"Freshness 只进 max-age——**Cloudflare 在有 s-maxage 时禁用 stale serving**,stale-while-revalidate 在边缘永不生效",故模板固定 `public, max-age=N, stale-while-revalidate=M` 不写 s-maxage。`mergeVaryHeader` 去重合并 Vary token,**遇 `*` 直接整体降级为 `*`**。markdown 响应的隐私防线:cookie/authorization/set-cookie 任一存在、或 cache-control 族头含 private|no-store|no-cache → 强制 `private, no-store` + `cdn-cache-control: no-store`(**表示切换不得把私有内容变公开**——缓存个性化检查的供给侧实现,呼应 seo-ops C10)。

**llms.txt 与双文档的工程参数**(nuxt-seo docs):`/llms.txt` 控制在 **~5K tokens**(结构化索引,先读这个);`/llms-full.txt` 是全量 markdown(**仅预渲染页进静态文件**,运行时访问不索引任何东西——`nuxi generate` 或 `nitro.prerender.routes` 是收录前提);Cursor/Windsurf 用 `@https://site/llms.txt` 引用(**@ 必须手敲,粘贴破坏上下文识别**)。`.md` 双胞胎映射:`/about`→`/about.md`、`/`→`/index.md`;**`/api` 与 `/_` 前缀路径不生成**。每个生成页尾部自动带 `## Sitemap` 段+独立 `/sitemap.md`(关闭项 `sitemapMd: false`)。**Nuxt Content v3 站点 `.md` 路由直接回源 markdown 源文件而非转换 HTML**(`contentSource: false` 才转)——CMS 站做双胞胎时先确认语义。**Agent Skills 发布面**:`skills/<name>/SKILL.md` 发布到 `/.well-known/agent-skills/` + `/skills/<name>/SKILL.md` + llms.txt 内,单 skill 站点额外挂 `/SKILL.md`;这些路径被协商器视为 artifact **原样应答、永不渲染**。**MCP 工具面**:`list_pages`/`search_pages`/`get_page_markdown` 三工具挂 `/mcp`(需运行中的服务器,静态导出无法承载);运行时索引带 **contentHash 变更检测**(hash 不变则跳过重索引)与 TTL。

## 六、来源

- 27 bot 引用/训练分类+频率：[Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) `docs/ai-bots-reference.md`
- 厂商官方行为声明（OAI-SearchBot/SearchBot/User 系）：[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `reference/platform-source-selection.md`（2026-10-04 复核一手文档）
- 区域补充：Yandex Webmaster 官方文档（YandexAdditional）；SEONews（俄媒体退出案例）；Naver 官方 Help（robots 收录）；StatCounter（Bing 日本份额）；PR Times（llms.txt 日企采用率）
