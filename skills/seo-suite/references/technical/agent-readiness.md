# Agent-Readiness 操作层(协议时代的站点准备)

> 建立于 2026-10-08。来源:英文区第一波深挖——[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-agentic/`(webmcp/lighthouse-agentic/vendor-matrix/access-policy/agent-friendly-pages 五件)、[jdevalk/specification.website](https://github.com/jdevalk/specification.website)(20+ 页 agent-readiness 规范,每页带出处)、[agenticresourcediscovery.org](https://agenticresourcediscovery.org)(ARD 官方)。证据约束:本层所有协议**均无 AI 引擎宣布消费**(ARD/OKF 属早期注册型投入)——定位是"低成本期权",不是已验证的引用杠杆;与 [AI 爬虫政策](ai-crawler-policy.md) 的 robots.txt 层互为补充。
> **分叉决策(本套件立场)**:英文目标站全开本层;其他语区只保留 llms.txt 类等价物(百度系/元宝/豆包不消费这些协议),分叉逻辑见 [多语言工作流](../overview/multilingual-workflow.md)。

## 一、三级发现链(ARD,Agentic Resource Discovery)

Google+Linux Foundation 工作组,2026-05 公布。三级递进,做到第二级即覆盖主流:

1. **robots.txt `Agentmap:` 指令**——声明 agent 目录位置:
   ```
   Agentmap: https://example.com/ai-catalog.json
   ```
2. **`<link rel="ai-catalog">` HTML 标签**——页面级指向目录;
3. **`/.well-known/ai-catalog.json`**——机器可读目录本体(工具清单/能力声明)。

**验证**:Lighthouse 13.5+ 新增 `AGENTIC_BROWSING` 类别(PSI API v5 可调 `category=AGENTIC_BROWSING`),其中 `ard-schema` 审计校验 ai-catalog.json 结构(warning 级,0.9 分)。

## 二、WebMCP(页面级工具注册)

W3C WebML CG 草案(编辑来自 Microsoft/Google),Chrome M149–M156 origin trial:

- 入口:`document.modelContext`(旧 `navigator.modelContext`),`registerTool()` 注册页面级工具(如"查库存""算报价");
- 表单声明式写法:`<form toolname="...">` + `SubmitEvent.agentInvoked` 区分 agent 提交与人类提交;
- 权限控制:`Permissions-Policy: tools=()`;
- **消费者现状:仅 ChatGPT 桌面版内置浏览器实证调用**(默认开启、仅顶层文档);WebKit 反对、Mozilla 中立——单一消费者,标注。

**"token 效率"类营销数字无可追溯基准,勿引用。**

## 三、身份与授权(Web Bot Auth)

- `draft-ietf-webbotauth-httpsig-protocol-00`(2026-09-01):`Signature-Agent` 字典形式——**ChatGPT-User 以此签名**,服务器可据此区分"真 bot"与伪装 UA;
- UA 行为表(决策用):`Google-Agent`(用户触发,通常无视 robots.txt)/`ClaudeBot`·`Claude-SearchBot`(遵守 robots)/`ChatGPT-User`(Web Bot Auth 签名);
- Content-Signal(Cloudflare CC0+IETF 个人草案已过期)、MCP Server Card(SEP-2127 未合并)——状态不稳,写事实库前复核。

## 四、Lighthouse AGENTIC_BROWSING 七审计(2026-09 上线)

首个把 agent 可读性纳入免费标准化工具链(PSI 免费可调):

| 审计 | 检查 | 备注 |
|---|---|---|
| agent-accessibility-tree | 33 条 axe 规则子集 | **与人类可访问性类别不同**(不含对比度/标题顺序) |
| webmcp-form-coverage | 表单可被 agent 识别的比例 | |
| webmcp-registered-tools | registerTool 覆盖 | |
| webmcp-schema-validity | 工具 schema 合法性 | |
| CLS | 布局稳定 | agent 抓取同样受害 |
| llms-txt | H1+至少一个 MD 链接+50 字符 | 与 [llms.txt 指南](../content/llms-txt-guide.md) 的规范一致 |
| ard-schema | ai-catalog.json 结构 | warning 0.9 |

## 五、语言中立层的多语言部署

协议层与语言无关——多语言站的正确做法:**每 locale 各发一份目录,bundle 内交叉链接按语言分目录**(ARD/OKF 均语言中立)。OKF(Open Knowledge Format,Google Cloud 2026-06):YAML frontmatter 交叉链接 markdown 概念包,`application/okf-bundle+gzip` 媒体类型提案中;当前唯一落地是付费企业 Knowledge Catalog——早期注册型投入,量力而行。

## 六、就绪决策表

| 站点情形 | 建议 |
|---|---|
| 英文 SaaS/文档站(客群重度用 ChatGPT/Claude) | 全开:ARD 二级+llms.txt+WebMCP 关键表单+Web Bot Auth 日志 |
| 其他语区站点 | llms.txt+robots 引用型 bot 放行即可;协议层等该语区引擎出现消费者再上 |
| 技术博客/文档 | markdown 双胞胎(dualmark 模式:每页配 .md 镜像)性价比高于全套协议 |
| 电商 | 优先 product schema/库存可见性,WebMCP 工具(查价/查库存)是唯一对 agent 有交互意义的层 |

## 七、未证实项

ARD/OKF 无任何 AI 引擎宣布消费;WebMCP 单一消费者(ChatGPT 桌面浏览器);无对照研究链接 accessibility-tree 质量×agent 任务成功率;MCP Server Card 与 Content-Signal 状态可能已变化。

## 完全装载:内容协商实现/端点家族/三层 AI 索引(百仓深扫)

**Markdown 内容协商**(nuxt-ai-ready 源码级):默认只看 Accept;开 botNegotiation 后 **botInfo.category==='ai' 才返回 markdown**(getBotInfo 按 headers 判);**启发式不得覆盖显式拒绝**——Accept 匹配组全部 q===0 则维持原偏好;显式 .md 请求在 early 段 defer(避开站点 auth);API/JSON 请求排除;缓存规则="Freshness 只进 max-age"(**Cloudflare 在有 s-maxage 时禁用 stale serving**)→`public, max-age=N, stale-while-revalidate=M`;Cloudflare 静态头规则上限 **100** 条。
**端点家族**(docs.page):`/{owner}/{repo}/llms.txt|llms-full.txt|mcp|robots.txt|sitemap.xml|search.json`+`.well-known/*`;单页加 .md 后缀取 raw;边缘缓存 ~5 分钟;大仓截断响应头 x-tree-truncated:1。
**三层 AI 索引**(beihaili):manifest(机器可读能力声明)→content-index(内容索引,双语按课显式 availability 字段)→llms.txt(发现入口);本地免费 MCP 政策字段化(free/readOnly/paymentEnforcement:false);x402 延后付费($0.25 检查类)标 future-hosted 不执行;`ai:index/ai:publish/ai:verify` 进 CI。
**llms.txt 消费端安全**(mcpdoc):远程 llms.txt 自动只放行其所在域;本地文件必须显式 --allowed-domains;**meta-refresh 重定向目标域也须过白名单**;官方两跳协议=list_doc_sources→fetch llms.txt→反思其中 URL→fetch 相关页。
**单一事实源+CI 漂移门**(sceneview):llms.txt 为唯一源,MCP/派生知识全由它生成;CI `--check` 比对派生物,漂移即 fail build;部署时 rm 旧副本防影射——"published surface cannot drift by construction"。
**电商 agent 接口**(aimeos):店铺自带 MCP 端点(搜索/增删产品/订单,OAuth)——AI 电商的 agent-readiness 实例。

## 协商决策状态机与 Link 头(nuxt-ai-ready 源码深读,2026-10-09)

补上节"完全装载"的实现层:`src/runtime/server/utils/negotiation-decision.ts` + `negotiation-response.ts` + `link-header.ts` + `markdown-request.ts`(协议行为细节见 [ai-crawler-policy.md](ai-crawler-policy.md) 同日节)。

**决策状态机五出口**(`resolveNegotiationDecision`,纯函数):`skip`(reason ∈ well-known/internal/artifact/not-a-page/deferred)/`not-acceptable`/`html`/`redirect`/`render`。入口短路序:`/.well-known/` 前缀→artifact 路径(agent skill 原样应答)→**内部头 `x-ai-ready-internal`**(模块自取 HTML 时绕过协商)→renderInfo 为 null(not-a-page:`.md` 以外的扩展名、JSON/event-stream Accept 的 API 请求、保留路径)。**两阶段执行**:`early`(在 Nitro 静态资源处理器之前)+`middleware`——**显式 `.md` 在 early 段必然 defer**(等静态预渲染文件先应答,且渲染要排在站点自注册的 auth 中间件之后,避免鉴权旁路);隐式 markdown 协商命中则 **307 重定向到 `.md` 双胞胎**——注释明示动机:"HTML 与 markdown 各占独立缓存键,对**忽略 Vary 的 CDN** 这才是安全的"。not-a-page 判定:Accept 含 `application/json` 或 `text/event-stream` 且不含 html/markdown/plain/`*/*` 的请求直接排除(不打扰 API)。

**决策缓存与去重**:同一请求的决策挂在 `event.context[Symbol('nuxt-ai-ready:negotiation')]`,键含 owner/path/policy/botNegotiation,**early 与 middleware 双跑只算一次**;协商头应用有 `APPLIED_KEY` 布尔守卫,防 `Vary` 被二次 append。

**Link 头模板**(`link-header.ts`):HTML 响应带 `<{path}.md>; rel="alternate"; type="text/markdown"`;markdown 响应带 `<{path}>; rel="alternate"; type="text/html"` + `<{path}>; rel="canonical"`(**md 的 canonical 指回 HTML 版**);两者都带 `<{llms.txt}>; rel="describedby"`(可关)。**RFC 9110 §5.5 头值 ASCII 限制**:非拉丁字符路径(中文/西里尔)必须 `encodeURI` 后进头,否则 Cloudflare 拒收整个响应——**中文站自研协商时的高频坑**。i18n 站点用 status-aware 变体(错误响应带精简 Link 集)。

**bot 启发式的三条护栏**(`markdown-request.ts`):预渲染(`x-nitro-prerender` 或 import.meta.prerender)一律 html;`sec-fetch-dest: document` 的浏览器导航跳过 bot 判定;Accept 中 text/markdown|text/*|*/* 匹配组全部 q=0 时维持原偏好(启发式不得覆盖显式拒绝)。

**路由规则互斥**(`content-negotiation.ts`):路由规则带 `isr` 或 `cache` 且 cache.varies 不含全部协商 Vary 维度时,协商自动 disabled(source: 'isr'|'route-cache')——**ISR/整页缓存与按 Accept 分表示天生冲突**,自研时同样要在 CDN 层禁或配 varies。
