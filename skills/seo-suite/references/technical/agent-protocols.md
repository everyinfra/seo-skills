# Agent 协议速查卡(14 协议一页对照)

> 建立于 2026-10-09。来源:[jdevalk/specification.website](https://github.com/jdevalk/specification.website) `src/content/spec/agent-readiness/` 22 页全文 + `src/content/considered/` 否决记录(2026-10 快照)。每卡:用途/规范位置/关键规则数字/验证命令/常见错误/状态(stable=已定稿规范;draft=标准流程中的草案;vendor=单厂商或单站提案)。
> 与既有内容的分工:策略层与部署决策见 [agent-readiness.md](agent-readiness.md)(ARD 三级链/WebMCP/OKF/分叉决策),robots.txt UA 表见 [ai-crawler-policy.md](ai-crawler-policy.md);本文件只做协议事实速查——写实施方案或事实库时从这里取规则数字与验证命令。

## 1. Content Signals(robots.txt 使用偏好声明)— draft

- **用途**:在 robots.txt 里声明内容可否被 search / ai-input(检索增强)/ ai-train(训练),把"bot 是谁"与"内容可做什么"分开。
- **规范**:IETF aipref WG([draft-ietf-aipref-vocab](https://datatracker.ietf.org/wg/aipref/documents/) rev 08,2026-09-14)+ IAB Tech Lab 平行规范([contentsignals.org](https://contentsignals.org/));两者词汇未收敛——**线上可部署写法用 IAB/验证器读的 `ai-train`/`ai-input`,不是 IETF 草案里的 `train-ai`/`ai-use`**。
- **关键规则**:`Content-Signal: search=yes, ai-input=yes, ai-train=no`——指令名单数 `Content-Signal`(不是 Content-Signals);只能 yes/no;必须放在 `User-agent:` 组内;与 `Disallow:` 语义矛盾(被封的 bot 根本读不到);是声明不是法律强制。
- **验证**:`curl -s https://example.com/robots.txt | grep -i content-signal`;isitagentready.com 的 `botAccessControl.contentSignals`。
- **常见错误**:写成复数;放组外被静默忽略;与 Disallow 冲突;自造第三种值。
- **注**:agent-readiness.md 旧注"个人草案已过期"已被本卡更正(attach 草案 2026-08-19 重发 rev 05,WG 活跃)。

## 2. ARD / AI Catalog(域级能力目录)— draft

- **用途**:一个 well-known 文件列全域的 agent 能力(MCP 服务器/A2A agent/Skill/子目录),一次抓取代替逐路径猜。
- **规范**:Linux Foundation([agenticresourcediscovery.org](https://agenticresourcediscovery.org/),Apache 2.0),基于 ai-catalog 标准。
- **关键规则**:本体 `/.well-known/ai-catalog.json`,条目=URN `identifier`+`displayName`+媒体类型+`url`/`data` 二选一;媒体类型 `application/mcp-server-card+json`/`a2a-agent-card+json`/`agentskill+zip`/`ai-catalog+json`;**两规范字段名分叉——`mediaType` 与 `type` 两个字段都发同值**+`representativeQueries`(2–5 条自然语言);三个指路机制:`<link rel="ai-catalog">`、robots.txt `Agentmap:`、DNS `_catalog._agents`;trustManifest 签名=JCS(RFC 8785)规范化后的 detached JWS,**只签 trustManifest 不签 entries**,且同源 JWKS 的签名与被签文件共命运(攻其一点即破)——无独立密钥锚点就不如 TLS+不签。
- **验证**:`curl -s …/.well-known/ai-catalog.json | jq .`(specVersion+entries);每条 url 以声明媒体类型可 200;Agentmap 行与 Link rel 在。
- **常见错误**:自造字段;列不存在的"愿望能力";同源签名当防篡改证据。

## 3. NLWeb(对话式站点问答)— draft

- **用途**:站点暴露 `/ask` 自然语言端点,答案扎根自家语料并强制引用来源 URL。
- **规范**:[nlweb-ai/NLWeb](https://github.com/nlweb-ai/NLWeb)(源自 Microsoft,现独立项目)+ [REST API 文档](https://github.com/nlweb-ai/NLWeb/blob/main/docs/nlweb-rest-api.md)。
- **关键规则**:发现=一行 `<link rel="nlweb" href="/ask">` + 同名 `Link` 头;GET `?query=` 或 POST JSON;**响应必须是 JSON(answer+sources),不是 HTML**;可同名包装成 MCP 工具(`ask_site`);每答必带站内来源 URL。
- **验证**:`curl -sI / | grep -i nlweb`;`curl '…/ask?query=…'` 返回 JSON 且 sources 内 URL 实存、内容相符。
- **常见错误**:答站外语料外的题;有聊天 UI 却没发现链接;索引过期不更新。

## 4. OKF bundle(整库 Markdown 打包)— vendor

- **用途**:整个知识库打成 Markdown 概念树一次摄取,免逐页抓取。Google Cloud 主导,当前唯一规模化落地是其付费 Knowledge Catalog。
- **规范**:[OKF SPEC v0.2](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)(2026-09)。
- **关键规则**:概念=frontmatter+正文,唯一硬字段非空 `type`;`okf_version` 只进根 `index.md`(其余 index.md 禁 frontmatter);0.1→0.2 断裂:`timestamp`→`generated.at`、正文 `# Citations`→frontmatter `sources`(消费方向要求回退兼容);`log.md` 新的在前;`references/` 镜像外部标准;**打包≠发现**——必须另配 ARD 条目/llms.txt;媒体类型过渡期用诚实的未注册 `application/okf-bundle+gzip`。
- **验证**:每个非 index/log 的 .md 可解析且 type 非空;声明的 okf_version 与实际字段形状一致;至少挂在一个发现面上。
- **常见错误**:手写第二份导致漂移(必须从同一源生成);index.md 带 frontmatter;宣称 0.2 却还发 0.1 字段;把 `recommended` 之类写进保留的 `status` 生命周期字段。

## 5. WebMCP(浏览器内工具注册)— draft

- **用途**:页面用 JS 注册工具,同浏览器内的 agent(侧边栏/内置 agent)直接调用,零服务端 MCP 铨路;跑在用户登录态里。
- **规范**:W3C WebML CG([webmachinelearning.github.io/webmcp](https://webmachinelearning.github.io/webmcp/));API 面 `document.modelContext`(旧 `navigator.modelContext`,**两个都要 feature-detect**)。
- **关键规则**:`registerTool({name, description, inputSchema, annotations, execute})`;`annotations.readOnlyHint`/`destructiveHint` 决定 agent 是否向用户确认;**检测必须在下载 bundle 之前**(几字节内联守卫,无 API 就不注入脚本,而非脚本内部 early return);工具定义小、语料首次调用时再取;单结果用 `mode:'summarize'`;与 HTTP MCP 服务器同名同 schema 互镜像。
- **验证**:支持浏览器控制台 `typeof navigator.modelContext?.registerTool === 'function'`;**不支持浏览器网络面板里完全不出现工具 bundle 请求**;测试 agent 调用返回 `{content:[…]}` MCP 形结果。
- **常见错误**:工具绕过站点自身鉴权(等同任意 JS 可调动作,服务端必须照常校验);注解说谎(readOnly 标在写操作上)。

## 6. Schemamap(逐页 JSON-LD 端点索引)— vendor

- **用途**:每页结构化数据另发 `.jsonld` 端点,`/schemamap.xml` 索引之——agent 免 HTML 抽取、免 JS 渲染,按 @type 定向抓取。
- **规范**:**本站单站提案,无外部标准、无第二实现者**([schemamap 页](https://github.com/jdevalk/specification.website)自述);底层靠 JSON-LD 1.1/RFC 8288/sitemaps。
- **关键规则**:端点=规范 URL 加 `.jsonld` 后缀,`Content-Type: application/ld+json` + `Access-Control-Allow-Origin: *` + 重缓存;索引 `<resource>` 带 loc/jsonld/@type/lastmod;逐页发现用**已注册**的 `rel="alternate" type="application/ld+json"`;站级 `rel="schemamap"` **未注册 IANA——只放 HTML head,不进全局 Link 头**,或按 RFC 8288 §2.1.1 用 URI 形 rel;索引只列资源级类型(Article/Product…),不列每页雷同的 WebSite 块;与 sitemap/llms.txt 答不同问题,三者并存。
- **验证**:`curl -sI …/foo.jsonld` 200+正确 Content-Type+CORS;`xmllint --noout` 校验索引;`.jsonld` 体与页面 `<script>` 内图谱排序后一致;validator.schema.org 过。
- **常见错误**:HTML 图谱与端点漂移;编造 @type;漏 CORS。

## 7. TDMRep(TDM 权利保留)— stable

- **用途**:机器可读声明"是否保留反对文本数据挖掘的权利"。**法律通知,不是拦截器**——robots 管"可否抓",TDMRep 管"抓了之后可否挖掘"。
- **规范**:W3C [TDMRep Final CG Report](https://www.w3.org/community/reports/tdmrep/CG-FINAL-tdmrep-20240202/)(2024-02 定稿);法律钩子=EU DSM 指令 2019/790 第 4 条(不声明=默认允许挖掘)。
- **关键规则**:值**只能是整数 `1`(保留)/`0`(不保留)**,true/yes/reserved 都等于未设;三载体优先级 **HTML `<meta>` > HTTP 头 > `/.well-known/tdmrep.json`**(well-known 是站点默认且最弱,用 robots 路径通配);设 `1` 必配 `tdm-policy` 指向许可政策;全站覆盖选 HTTP 头(PDF/图片无 head);与 robots/Content-Signal 口径必须一致;无追溯力。
- **验证**:`curl -sI https://example.com/ | grep -i tdm-`;抓一个非 HTML 资产确认头也在;well-known 文件是 JSON 数组且每条有 location+整数。
- **常见错误**:当拦截器用;`tdm-reservation:1` 配 `ai-train=yes` 自相矛盾;指望它挡抓取。

## 8. A2A agent cards(agent 互发现)— stable

- **用途**:一个 agent 发现并调用另一个 agent(整只 agent,非单个工具)——MCP 暴露工具,A2A 暴露可被委派的 agent 本体。
- **规范**:[A2A Protocol 1.0](https://a2a-protocol.org/latest/specification/)(2026-03 达 1.0,Linux Foundation;Google 2025 捐出)。
- **关键规则**:卡片在 **`/.well-known/agent-card.json`**(不是 agent.json);必填 `name`/`description`/`version`/`supportedInterfaces`(各含 url+protocolBinding+protocolVersion)/`capabilities`/`defaultInputModes`/`defaultOutputModes`/`skills`(各含 id/name/description/tags);camelCase;传输 JSON-RPC/gRPC/HTTP+JSON 任选;最小实现 `message/send` 其余回 method-not-found;`capabilities.streaming` 等如实填;skills id / 接口 url / capabilities 变更=破坏性,须 bump version;可加 JWS `signatures[]`。
- **验证**:`curl …/.well-known/agent-card.json` 200+`application/json`+过 schema;POST `message/send` 到 `supportedInterfaces[0].url` 返回 JSON-RPC 响应而非 HTML 错误页。
- **常见错误**:卡片指向 404 端点(比没有卡更糟);文件名写错;声称未实现的 streaming。

## 9. HTTP Link 头(HTML-free 发现)— stable

- **用途**:把 llms.txt/sitemap/api-catalog/RSS 等机器面广告在响应头里,不下载正文即可发现;JSON/PDF/304 等无 head 的响应也能带。
- **规范**:RFC 8288(Web Linking)+ RFC 9727(api-catalog)+ RFC 9264(linkset)+ [IANA rel 注册表](https://www.iana.org/assignments/link-relations/link-relations.xhtml)。
- **关键规则**:只准用注册 rel——内容站常用 `describedby`(llms.txt)/`alternate`(.md、RSS)/`api-catalog`/`sitemap`/`service-desc`/`security`/`author`/`license`;多条可逗号并一个头或多个 Link 头;URL 进 `<>` 不进引号;带 `type`+`title` 免二次抓取;至少首页发,最好全站;**在 CDN/反代层设**(Cloudflare `_headers` 一行 / nginx `add_header`),非 HTML 响应才覆盖得到;与 HTML `<link rel>` 保持一致。
- **验证**:`curl -sI https://example.com/ | grep -i ^link`;isitagentready.com `discoverability.linkHeaders`。
- **常见错误**:自造 rel;引号包 URL;漏逗号;只在 HTML 响应发。

## 10. Markdown 源端点(逐页 .md + 内容协商)— draft

- **用途**:agent 直接取作者写的 Markdown 源,免 DOM 抽取/JS 水合,体积小 5–20 倍;Anthropic/Stripe 文档已实装。
- **规范**:无正式标准,社区约定(见 [spec 页](https://github.com/jdevalk/specification.website) + [llmstxt.org](https://llmstxt.org/));协商语义=RFC 9110 §12 + `Vary`/`Content-Location`。
- **关键规则**:最低配 `.md` 后缀同源同内容;升级 `Accept: text/markdown` 协商,回 `Content-Type: text/markdown` + `Content-Location: /….md` + **`Vary: Accept`(HTML 侧也要带,否则缓存串表示)**;frontmatter 只放 title/url(规范 HTML URL)/updated/sources/licence;可加 `X-Markdown-Tokens`(cl100k_base 估数,内容变更时重算);HTML `<head>` 加 `rel="alternate" type="text/markdown"`;**.md 与 HTML 访问策略必须相同**(一边免费一边鉴权=破约)。
- **验证**:`curl -i …/getting-started.md` 200+text/markdown;`curl -i -H 'Accept: text/markdown' …/getting-started/` 带 Content-Location+Vary;.md 与 HTML 同构建生成、标题段落一致。
- **常见错误**:漏 Content-Type;协商不带 Vary;吐出未解析的模板 shortcode;.md 放鉴权后面。

## 11. Agent Skills 发现(SKILL.md 发布面)— draft

- **用途**:well-known 索引列出站点教 agent"怎么用我"的 SKILL.md,含 sha256 摘要供校验与变更检测。
- **规范**:Cloudflare 领衔 [discovery RFC draft v0.2.0](https://github.com/cloudflare/agent-skills-discovery-rfc) + [agentskills.io 规范](https://agentskills.io/specification) + RFC 8615。
- **关键规则**:索引 `/.well-known/agent-skills/index.json`,`$schema` 必须是 `https://schemas.agentskills.io/discovery/0.2.0/schema.json`(漏了客户端按 0.1 解析);条目=`name`/`type`(`skill-md`|`archive`)/`description`/`url`/`digest`(`sha256:<hex>` 对原始字节,文件变就重算);SKILL.md frontmatter:`name` 小写连字符 **1–64 字符**、`description` **≤1024 字符**且写给 agent 的"何时加载"判断;skill 挂 `/.well-known/agent-skills/<name>/SKILL.md` 以 `text/markdown` 服务;索引以 `rel="agent-skills"` Link 头广告;两文件都开 CORS `*`。
- **验证**:`curl -sI …/.well-known/agent-skills/index.json` 200+JSON;逐条 fetch url→hash→比对 digest;isitagentready.com `checks.discovery.agentSkills.status`。
- **常见错误**:digest 漂移(合规客户端直接拒收);description 写成营销文案;一个大杂烩 skill(拆成多个小 skill);Content-Type 给错。
- **防重注**:ai-crawler-policy.md 已收 Nuxt 侧"发布到 /.well-known/agent-skills/ 且协商器视为 artifact 原样应答"的实现细节,本卡只补协议本体。

## 12. DNS-AID(DNS 层 agent 服务发现)— draft

- **用途**:DNS 查询(建连必经路径)即返回 agent 服务入口,零 HTTP 往返;配 DNSSEC 得到认证答案。
- **规范**:[draft-mozleywilliams-dnsop-dnsaid](https://datatracker.ietf.org/doc/draft-mozleywilliams-dnsop-dnsaid/)(IETF 个人草案)+ RFC 9460(SVCB/HTTPS RR)。
- **关键规则**:保留 `_agents` 标签下 `_<service>._agents.<domain>`:`_index._agents`(必配,指规范站)、`_mcp._agents`(MCP 服务器)、`_a2a._agents`;**ServiceMode(priority≥1)非 AliasMode(0)**;至少带 `alpn`(如 h3,h2)+`port`(443),至少一条 `mandatory="alpn,port"`;zone 文件目标主机名**尾点不能省**;**必须 DNSSEC 签名且 DS 记录上到注册商**(否则验证器降级/失败);记录放真域不放 pages.dev/netlify.app。
- **验证**:`dig +short HTTPS _index._agents.example.com`(返回 `1 example.com.` 开头);`dig +dnssec +cd HTTPS …` 见 RRSIG;`dig +short DS example.com` 链不断;isitagentready.com `discoverability.dnsAid`。
- **常见错误**:AliasMode 发记录;自造字符串参数(未分配前用 `keyNNNNN` 数值形);Cloudflare 开了 DNSSEC 但注册商没贴 DS。

## 13. auth.md(agent 注册说明书)— vendor

- **用途**:根路径 Markdown 告诉 agent 如何注册并换取受限 API 访问。**文件只是文档,不创建账号不授予权限**——真权限由 OAuth 元数据+服务端执行。
- **规范**:WorkOS 提案([workos.com/auth-md](https://workos.com/auth-md/docs/auth-md) + [参考实现](https://github.com/workos/auth.md));OAuth 块本身是标准(RFC 9728 Protected Resource Metadata 等),`agent_auth` 扩展与 claim grant 是本协议私有。
- **关键规则**:HTTPS 公开可取、无登录墙;文件结构=发现 OAuth 元数据→选注册方式→注册→用户 claim→换 assertion→调 API→吊销;**端点 URL 一律从元数据取,不抄示例路径**;claim 仪式像 device flow 但用私有 grant,**通用 device-flow 客户端不保证兼容**;安全边界:权限在 API 侧强制(audience 受限 token+最小 scope);agent 报的 email 不是账号所有权证明;claim 码有过期与尝试次数限制;token 不进公开文件/URL/日志。
- **验证**:无凭证 fetch /auth.md 得到可读 Markdown;逐端点逐 scope 与线上元数据比对;测试环境:不受信签发者/错 audience/过期 claim 码/越界访问各自被拒;吊销后 API 与再签发都失败。
- **常见错误**:先发文后实现端点;把 WorkOS 扩展说成 OAuth RFC 要求;与 Web Bot Auth 混为一谈(那个验流量身份,这个管注册)。

## 14. Web Bot Auth(可验证 bot 身份)— draft

- **用途**:bot 用私钥逐请求签名证明身份,站点免 IP 白名单/UA 猜测做差异化策略;OpenAI/Anthropic/Perplexity 已发布密钥集,Cloudflare 边缘可验。
- **规范**:RFC 9421(HTTP Message Signatures)+ [draft-ietf-webbotauth-httpsig-protocol](https://datatracker.ietf.org/doc/draft-ietf-webbotauth-httpsig-protocol/)(**2026-09 IETF WG 接纳**,密钥目录草案已并入,pre-RFC)。
- **关键规则**:只许非对称算法,**HMAC 共享密钥被排除**;bot 侧发 `Signature-Agent: sig1="https://bot.example"`——值是 **origin 不是文件 URL**;默认目录=`origin + /.well-known/http-message-signatures-directory`(媒体类型 `application/http-message-signatures-directory+json`,IANA 注册申请中);直连 JWKS 用 `;type=jwks_uri` 变体;`Signature`/`Signature-Input`/`Signature-Agent` **同一标签**(如 sig1),`Signature-Input` 须含 `"signature-agent";key="sig1"`+目标组件;签名覆盖 `@authority` 或 `@target-uri`,带 `created`/`expires`/`keyid`/**`tag` 必须是 `web-bot-auth`**(区分同连接其他签名用途);站点侧:验签结果只经可信代理链接受、剥客户端伪造身份头;**签名=身份≠权限**;默认别拦未签名流量(浏览器不签)。
- **验证**:真签名请求→验证器报预期标识→改动任一被签组件→验证必须失败;RFC 9421 验证器比对签名基;日志里 signing 爬虫带 verified 标。
- **常见错误**:占位签名值测不出成功路径;漏 created/expires(被截获可永久重放);只验首页;以为签名覆盖了 User-Agent(只保护它覆盖的组件)。

## 否决记录(considered/,防止误收)

- **AGENTS.md — 拒收理由 `out-of-scope`(2026-09-12)**:仓库根目录给编码 agent 的说明文件(build/test 命令、约定),随源码走、给"已持有工作副本"的 agent 读;而本 spec 每个 agent-readiness 主题都是"origin 通过 HTTP 应答外来 agent"。**网站侧不存在可检查的 URL——这是判据**。采纳数据并不差(6 万+开源项目、20+工具、Linux Foundation 的 Agentic AI 基金会托管),拒的是方向不是热度。网站侧等价物是 Agent Skills 发现(见第 11 卡)。复核触发:出现"agents.md 由 origin 应答/经 HTTP 拉取"的服务形态。
- 其余六条均 `too-early` 拒,与 agent 协议层关系弱,记一行备查:Cache-Status 头(RFC 9211,等 CDN 默认开启)、DPP 发现(等公开页实证+独立消费者)、HTTP Cache Groups(RFC 9875,等主流缓存 honoring)、增量转发(RFC 10036,等 h2o/nginx 实装)、`<meta name="text-scale">`(等第二浏览器引擎)、419 Purpose Declined(等 IANA 注册+部署)。

## 状态一览(速判)

| 协议 | 状态 | 一句话定位 |
|---|---|---|
| Link 头(RFC 8288) | stable | 全部发现面的通用底座,先做 |
| TDMRep(W3C CG-FINAL) | stable | EU DSM Art.4 的机器可读保留声明 |
| A2A 1.0(LF) | stable | agent 调 agent;1.0 已发 |
| Content Signals(IETF aipref) | draft | robots.txt 用途级 yes/no;词汇未定稿 |
| ARD(LF) | draft | ai-catalog.json 域级能力清单 |
| NLWeb(独立项目) | draft | /ask 端点+rel 发现 |
| WebMCP(W3C CG) | draft | document.modelContext 页内工具 |
| Markdown 源端点(社区约定) | draft | .md 双胞胎+Accept 协商 |
| Agent Skills 发现(CF draft v0.2.0) | draft | well-known SKILL.md 索引 |
| DNS-AID(IETF draft) | draft | _agents SVCB/HTTPS 记录 |
| Web Bot Auth(IETF WG draft) | draft | RFC 9421 签名 bot 身份 |
| OKF bundle(Google v0.2) | vendor | 整库 Markdown 打包 |
| auth.md(WorkOS) | vendor | agent 注册流程文档 |
| Schemamap(单站提案) | vendor | .jsonld 端点+schemamap.xml |
