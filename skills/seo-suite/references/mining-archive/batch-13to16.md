# 批 13-16 提取档案

## jdevalk/specification.website(874★)
**agent-skills-discovery v0.2.0**:索引 /.well-known/agent-skills/index.json;字段 name/type(skill-md|archive)/description/url/digest;**SKILL.md frontmatter:name 1-64 字符小写连字符,description ≤1024 且前置何时用信号**;digest=sha256 原始字节,漂移则拒;Content-Type 必须 text/markdown;两文件均开 CORS *。**dns-aid**(draft-mozleywilliams-dnsop-dnsaid):_index._agents(必做)/_mcp._agents/_a2a._agents;ServiceMode(非 AliasMode)priority≥1+alpn="h3,h2"+port=443,建议 mandatory="alpn,port";示例 `_index._agents.example.com. 3600 IN HTTPS 1 example.com. alpn="h3,h2" port=443`;无 DNSSEC 仅 hint;**未分配自定义参数用 keyNNNNN 数字名**;勿指向 pages.dev 类平台域;验证 dig +dnssec 出 RSIG。**auth-md**(WorkOS 自创非 IETF):三种注册(身份断言/email 流/匿名);claim 类似 device flow 但私有 grant;Markdown 只是文档,权限在 API 端强制;**勿与 Web Bot Auth 混谈**。considered/ 否决记录(agents-md 被拒+理由)。

## indranilbanerjee/digital-marketing-pro(858★)
(→已入 intake 合规卡+agent-readiness);补充:no_js_render 检查 min-text=250 字符+app-shell 根(#root/#__next/#app)少文本+--expect 短语缺失即 fail;**HTML 必须按服务端原样保存(curl),不可用浏览器另存为**;merchant feed 必填 id/title/description/link/image_link/availability/price,availability 枚举 in_stock/out_of_stock/preorder/backorder;**native_commerce(checkout_eligibility)只认 TRUE/FALSE 限美加澳**;acp_feed=OpenAI JSONL 或 Google 兼容 CSV/TSV;退出码 0/1/2;**robots 4xx=全允许,5xx=全禁(RFC 9309)**。

## theninthsky/client-side-rendering(827★)
(→已入 rendering);补充:GSC View Crawled Page 失败请求标 Other error=Googlebot 主动中止(渲染预算);**Googlebot 用最新 Chromium 且数据慢时多数会等**;Vercel Guides 过滤组合 65536(2^16) 种只能单文件=SSG 反例;"no major e-commerce website uses SSG"(价格库存过期);CSR 水合失焦失效模式。

## StanGirard/seo-audits-toolkit(815★)
跳过:2021 年停更;安全审计=httpobs-cli 外包;Lighthouse 只存 5 类目分;shell=True 拼 URL 注入风险。

## StJudeWasHere/seonaut(805★)
(→已入 validation 阈值表);补充:56 页级+14 跨页全文;nosnippet 单列;**指向 localhost/127.0.0.1 的链接**检查;图片>500KB、alt>100 rune、depth>4;跨页:重复内容 body_hash GROUP BY/重定向链与环/孤儿页/nofollow 指向可索引页/hreflang 缺回链·指向非规范·指向 noindex/canonical 指向不可索引;**WACZ 归档+回放**;导出含锚文本内链/alt 图片清单。

## junruxiong/IncarnaMind(801★)
跳过(2023 栈 RAG 应用;仅 BASE_CHUNK=100/WINDOW=1800/RRF c=60 参数)。

## AgriciDaniel/codex-seo(796★)
TOML agent 四字段(name/description/nickname_candidates/developer_instructions);**置信度加权多源合并**:Tier 0-3(CC+verify/Moz/Bing/DataForSEO)=0.50/0.85/0.70/1.00;**Tier0 可用因子<4 时必须报 INSUFFICIENT DATA 不给数字分**;7 因子权重=引域 20/质量分布 20/锚文本 15/毒性 20/增速 10/follow 比 5/地理 10,缺数据按比例重分配;Moz 限速 1 req/10s;新鲜度 Moz~3 天/Bing 近实时/CC 季度;DataForSEO 与 Moz 冲突信前者并标注;drift 17 规则×3 级(CRITICAL=schema 删/canonical 改/noindex 加/H1 变>50%/4xx5xx;WARNING=title 改/CWV 退>20%/perf 掉 10+);SQLite+SHA-256;一切抓取走 fetch_page.py(SSRF)禁 raw curl;FLOW prompt 库 CC BY 4.0 须署名。

## JeffLi1993/seo-audit-skill(764★)
llm_review_required 边界(→已入 validation);补充:stdlib html.parser 单遍扫描;max_redirects=5;title 50-60(<10 直接 fail);meta 120-160;H1<5 字符(纯品牌疑)或>70 warn;**slug 段>60 字符 warn**;报告命名 reports/<hostname>[-<slug>]-full-audit.html;章节含 **Sitemap URL Inventory 独立表(Directory/URL Count/Page Type/Example)**;写作铁律 Pass 一句短语/Warn·Fail ≤2 bullet+1 fix;**E-E-A-T 双层 Exists+Reachable(footer/nav);无独立 /contact 不算 fail**(About/footer 有 mailto/社交即 pass);PageSpeed 默认 180s 超时标 error 非性能失败;**无 API key 必须停下来问,不许缺数据出报告**;staging 子域检查(→已入)。

## serpapi/google-search-results-python(756★)
已宣告弃用(迁 serpapi-python);14 引擎(google_scholar/baidu/yandex/naver/apple…);参数名各异(yandex text/yahoo p/ebay _nkw/youtube search_query);**Search Archive 按 search_id 免费重取**;分页 PAGE_SIZE=10/LIMIT=1000。

## aigclink/geolook(753★)
(→已入中文指南);补充:**12 平台采样协议**:API 10 个(智谱 GLM/ARK 豆包/DEEPSEEK/MOONSHOT Kimi/MINIMAX/GEMINI/OPENAI/ANTHROPIC/XAI/PERPLEXITY)+人工采样表+插件回灌(纳米 AI/百度 AI/豆包 App/ChatGPT web/Claude web/Google AIO);英文 README 称 17 engines(含 Metaso 秘塔);**千问 OpenAI 兼容端点不返回 search_info,须原生端点 /api/v1/services/aigc/text-generation/generation+forced_search;豆包 /chat/completions 不联网须 /responses 且控制台单独开通,联网后单次 ~100s vs 千问 ~9s,开关切换当期弃旧样本重设基线**;体检六维权重 访问 15/长度 15/结构 20/可抽取块 25/权威 15/对题 10;对题性 r=0.442 为最强单一预测因子>cosine 0.356>quality 0.292;引用广度 Perplexity 16.35/Google 12.06/ChatGPT 6.88 源每条,**但 ChatGPT 单引影响力 0.2567=Google 5.64 倍**;采样环境四档(personal 自动降 D 级);no-site 模式引用官网率显示"不适用"而非 0。

## OpenClaudia/openclaudia-skills(712★)
GEO 难度公式+llm_mentions 决策(→已入 keyword);补充:免费 API enception.ai/api/tools/geo-difficulty ≤10 词;ai-citations-report 免费层 10 报/月 20 req/h;location_code 2840=US/2826=UK/2124=CA;**报告诚实措辞**:说 "not yet cited" 不说 "not indexed";流量标 modelled estimates;gpt-4o-search-preview+web_search_options.search_context_size:"medium" max_tokens 1000 ~$0.01/问;1-2s 串行防限流;发布前 DetectAIWatermark 剥离 Unicode 水印。

## leopard627/fire-your-seo-agency(708★)
measure(→已入 log/drift);补充 content.md:**内容诊断三计数**(目标问题为空的文/90 天未更/曝光 0)——三数即诊断;frontmatter 单源(question/answer 40 字内直答/data_asof/sources/faq/status: draft|review|published|refresh-needed|merged);Brief 五行填不满=还不能写;**AI 稿三规则**(全部数字对原出处/人审+署名/禁批量自动发布);发布 gate 全过才发(curl 无 JS 含正文直答表/Article LD dateModified=实际/FAQ 可见文本=LD 逐字一致/断链 0/发布后验 sitemap lastmod/IndexNow 内置);刷新触发四条(底层数据变/**28 天曝光较 60 天前跌≥30%**/问法年号更替/发现事实错误);dateModified 只在真实变更时改;同题双文→强者留 301+canonical 弱者 merged;删除最后手段=410+移出 sitemap;**跨发顺序:自家域先被索引(1-3 天)再外发,否则副本被当原版;NAVER 博客编辑器不渲染 markdown**。

## Affitor/affiliate-skills(700★)
moat 公式(→已入 keyword);补充:registry.json 顶层 version/generated_at/stages/skills,52 条各含 stage/version/agent_compatible/chain_metadata.suggested_next[];Quality Gate 5 问(愿发个人社媒?有惊人细节?尊重读者智力?Purple Cow 值得转?可执行?任一 NO 重写);trending scout 输出范式=格式占比+参与度基准(中位 18K views,top 10% 需 85K+)——**格式选择由数据定**。

## tigerless-labs/seo-ops(700★)
C 集(→已入 validation);补充:T 集供给清单:ymyl 拿不准即标 true(漏标=全灭)/图片 alt 按文件名键控禁"图 1"/装饰图标 alt=""/产品 JSON-LD 值取自人类可读字段/页型条件 2026-08-25 废弃(Google 不消费 WebPage 子类型);R 红线 8 条(R1 代理永不直改生产/R2 YMYL 专业审/R5 假结构化·买评论/R7 防爬异供:缓存公壳+客户端个性化不算,UA 定向算/R8 PII 禁入 prompt);N.A. 码 8 种(throttled→N.A. 非红,"**假红比慢更危险**");SQLite checks 表跨次累积可 diff;271 页站点约 7 分钟。

## fulls1z3/universal(700★)
跳过:Angular 旧栈停更近 4 年;'**' 通配 redirectTo ''=整站软 404 反例。

## invertase/docs.page(676★)
(→已入 llms-txt/agent-readiness);补充:标题回退链 docs.json name→owner/repo;链接 label 去方括号;分支/PR 预览 ~{ref} 段。

## crawlseo/crawlseo(625★)
16 类问题+机会公式+CTR 曲线(→已入 scoring/keyword);补充:健康分=100−8×CRITICAL−3×WARNING−1×INFO;爬虫参数 BATCH_SIZE=15 批间 100ms/maxPages 200 上限 2000;**CSV 注入防护(OWASP)**:=+-@\\t\\r 开头前缀 ';陷阱=重定向目标已 visited 造成幻影 DUPLICATE_TITLE,内部行必须从用户可见计数排除。

## jianruntech/geo-score(621★)
v1.1 后无 v1.2(明确结论);CLI 采样:run(base, sample=8);discover 按"检索爬虫视角"选真叶子页(robots Sitemap 行前 3 候选/子图前 2/loc 前 600 条+8 个 section 索引 /blog//news//posts//articles//insights//resources//docs//learn);配额 blog 类 3/docs 2/product 2;**--urls 钉住 ≤8 页重评消除 run-to-run 方差;--urls-from 上轮 REPORT.json 复用**;抓取工程:永不重试超时;FETCH_BUDGET=30s;RUN_DEADLINE=300s;_TimedReader 逐读限时防 tarpit(一字节慢滴曾挂住 CI 数小时);Retry-After 封顶 5s;**10 个检索爬 UA 全串+9 训练 token 只进证据不计分**;校准:阈值铁律"at least 10% of real sites already meet";外部基准(GeoReady 均值 54-56/282 域;行业分位 SaaS 62/教育 58/医疗 55/电商 48;324 站 Leading 仅 10%;"a quarter unreadable to AI crawlers")。

## beihaili/Get-Started-with-Web3(614★)
(→已入 agent-readiness 三层索引);补充:artifactContract v1.0.0 语义化(加字段不改版本);content-index 结构 11 modules/124 lessons/63 glossary,双语按课 availability 字段;x402 付费工具($0.25/$0.1)标 future-hosted 本地不执行;ai:index/publish/verify 进 CI。

## spatie/http-status-check(600★)
默认并发 10/超时 10s/遵 robots/track_redirects 记录链;非 2xx/3xx 写输出文件(覆盖前交互确认);--auth/--user-agent/任意 Guzzle opt。
