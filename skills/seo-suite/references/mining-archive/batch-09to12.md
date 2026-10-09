# 批 09-12 提取档案

## oxylabs/how-to-scrape-google-scholar(2101★)
Scholar 字段模型:organic 条目 pos/title/url/result_type(book|pdf|html)/description/result_id;publication_info.summary 一行式+authors[]{name,author_id,url};**inline_links.cited_by{cites_id,total,url}+versions{cluster_id,total,url}(同 cluster=cites)**;resources[]{file_format:"PDF",title,url} 按 PDF 过滤;入参 geo_location(非 domain,已废)。

## AminForou/mcp-gsc(1880★)
21 工具面;**坑位清单**:mcp SDK 2.0 删 fastmcp→钉 <2.0.0;富媒体结果正确路径 richResultsResult.detectedItems[].items[].issues[](顶层 richResultsIssues 永远空);10-URL 批量须 asyncio.gather 并发(sc-domain 串行必超时);**compare_search_periods 方向:Period2=基线,正值=Period1 更好**;Search Analytics 忽略 orderBy 须客户端排序;GSC_DATA_STATE=all(仪表盘口径)/final(确认数据滞后 2-3 天);GSC_ALLOW_DESTRUCTIVE 默认禁;索引五桶 not_indexed/canonical_issues/robots_blocked/fetch_issues/indexed;content-opportunities=**位 11-20+高曝光+低 CTR**。

## ReScienceLab/opc-skills(1846★)
**requesthunt 平台×类目矩阵**:YouTube 消费/硬件(每 topic 10-29 条)/Reddit 开发/创作者(单 newsletter 176 条)/LinkedIn B2B(量低质高)/X 情绪(1-6)/GitHub 仅 OSS/Amazon 实体;选择规则"消费硬件→Amazon+YouTube,B2B→LinkedIn+X,开发者→Reddit+GitHub,一切加 X";信号类型表(Reddit=技术/YouTube=UX/LinkedIn=战略/X=情绪/GitHub=Bug·FR/Amazon=产品);Free 100 credits/月 10 req/min。domain-hunter:WHOIS grep "no match|not found";.ai 强制 2 年;续费价≠注册价必查。reddit:.json 后缀免鉴权限 100 req/min;producthunt GraphQL 限额 **6250 complexity points/15min**。

## sethblack/python-seo-analyzer(1485★)
13 点 SEL 路线图五链并行(entity/credibility=**N-E-E-A-T-T 六维**/conversation/platform/recommendations);传统项:title<10/>70、desc<140/>255、img 缺 alt 含 data-src 回退、泛词锚文本(click here/page/article);关键词阈值>4;content_hash 聚簇重复页;**AI 爬虫二分报告**:训练类(GPTBot/Google-Extended/ClaudeBot/anthropic-ai)vs 检索类(OAI-SearchBot/ChatGPT-User/PerplexityBot/Claude-User)分开+"屏蔽检索爬虫才是真正逐出 AI 答案且常是误伤";llms.txt 200 即 true。

## karust/openserp(1456★)
(→已入 validation 20 枚举);补充:Google AIO 提取 data-subtree='aimc'(mfc 可能占位);占位过滤=空文本/show more/CSS 泄漏(@keyframes)/本地化文案(含俄语);confidence AIO 0.75/PAA 0.8/related 0.6;Yandex AI 模块标题"Нейро",扁平化在 p/br/li 边界断行**刻意排除 div**(Google 流式 AI 每词一 div);**llms-full.txt 优先于 llms.txt;≥200 runes 且非 HTML 嗅探才接受(防 SPA 假阳性)**。

## harlan-zw/nuxt-seo(1448★)
(→已入 agent-readiness 协商节);补充:版本矩阵门禁;Content robots:'noindex' 仍留 sitemap,robots:false 才移除;skew-protection polling+cookie:false;MCP 六工具(debug_social_share/validate_schema/analyze_robots_txt/validate_sitemap/check_meta_tags/convert_html_to_markdown);自家 llms.txt=/llms.txt ~5K 索引+/llms-full.txt(200K+ 上下文才用)。

## sceneview/sceneview(1335★)
**约定反转**:llm.txt=507,951 字节全文(33 个 ## 节)而非短索引——URL 已被 sitemap/AGENTS.md/MCP/外部索引引用不能改,**在全文内补索引节**;派生防漂移:generate-gpt-knowledge 路由 4 桶,未匹配默认入 api 保证 --check 必报漂移,CI fail build;部署 rm 旧副本防影射;MCP 资源 sceneview://api=完整 llms.txt;5 工具(validate_code 30+ 规则+did-you-mean/get_node_reference 48 类型/list_samples 38 场景);known-issues 资源实时 GitHub 缓存 10min。

## onvoyage-ai/gtm-engineer-skills(1320★)
16 检查 142 分(→已入 scoring-rubric);补充:**引用率数字矩阵(带出处)**:答案在首段=4.8×;对比表 2.8×/FAQ 块+156%;in-text citations+115%/统计数字+40%;长文 2000+ 词 3×;干净标题层级 3.2×;ChatGPT 最常引页面 76% 在 30 天内更新、AI 引用内容比 organic 新 25.7%(Ahrefs 17M 引用);44.2% 引用来自内容前 30%(Kevin Indig 1.2M)。**prompts.csv 契约**:恰好 10 列最少 20 行;tier=buy|solve|learn(~20/40/40);priority 推导 buy/solve+high citability+none/low competition→easy_win;**AI 可引用图表四件套**:figcaption 文本层+语义 table(thead/th scope/caption)+Dataset JSON-LD(variableMeasured/temporalCoverage)+SVG 浏览器目检——"AI engines cite text, not pixels"。

## retlehs/quien(1286★)
(→已入 log-analysis);补充:HTTP body 512KB 上限/超时 10s/dial 5s;DKIM 15 selector(default/google/selector1-2/k1/mandrill/s1-s2/mail/dkim/sm1-2/sig1)。

## gooseworks-ai/goose-skills(1239★)
**pSEO 竞品 URL 模式正则表**:`/vs/|/compare/`、`/integrations?/`、`/for-.*|/solutions/`、`/alternatives?(-to)?/`——逆向竞品程序化页型+估算每模式页数;aeo skill:六引擎品牌可见性,**50 查询×3 供应商≈$2-5/次**;查询生成 --limit 10 --dry-run 人工过目再 --limit 50;配置 .goose-aeo.yml 直接编辑。

## LeoYeAI/openclaw-marketing-skills(1042★)
**平台取源差异表**:AIO 总结 top 排名页/ChatGPT 引用面更广/Perplexity 偏权威+新鲜+结构化/Claude 走 Brave Search;品牌经第三方被引概率是自有域 **6.5×**;schema 使 AI 可见性+30-40%;**引用份额按内容类型**:对比文~33%/权威指南~15%/原创研究~12%/榜单纯~10%/产品页~10%/how-to~8%;**12 个 pSEO playbook 全表**(Templates/Curation/Conversions/Comparisons/Examples/Locations/Personas/Integrations/Glossary/Translations/Directory/Profiles,每个含检索模式+URL 结构+组合公式);robots 中间方案=封 CCBot 放搜索 bot;监测 DIY=每月 20 查询×3 平台手工记录。

## langchain-ai/mcpdoc(1033★)
(→已入 agent-readiness 消费端安全);补充:fetch_docs 校验 startswith 前缀匹配;服务器 instructions 固定两跳引导协议。

## kostja94/marketing-skills(1022★)
parasite+Grokipedia(→已入 backlink/geo-platform);补充 Grokipedia 数据:ChatGPT 13.6M 提示中 ~263K 回复引用(~95K 页),Wikipedia 同期 2.9M;份额 0.01-0.02%/天自 2025-11 中旬上升;Suggest Edit 的 Summary 禁品牌名,URL 只放 Add another source 且**混 1-2 个权威源(Forbes/TechCrunch)**;审核~2 小时;Entity SEO:Organization schema 全局组件每页输出不要只放 About;@id 稳定 URL;首页 Organization↔WebSite 互链。

## Auriti-Labs/geo-optimizer-skill(1020★)
4.18.3 后无新版(2026-09-22 止);4.18.x 全量(→已入各文件);补充:--provider serpbase 直接观测 SERP+AIO 引用块(100 次免费后 $0.30/1k);标题分隔符补 en-dash 且按文本最早出现切;KNOWN_FORM_EMBED_HOSTS iframe 表单计入(Tally/Typeform/HubSpot/JotForm/Google Forms,匹配 src**与**data-*-src);About 锚点 #about 等价;ORGANIZATION_TYPES 子类匹配(LocalBusiness+25 子类)。

## Bhanunamikaze/Agentic-SEO-Skill(955★)
reference_freshness:正则 `<!--\s*Updated:\s*(\d{4}-\d{2}-\d{2})\s*-->`;四态 ok/stale/error(**未来日期=error**);默认 90 天;--fail-stale;indexability_matrix 五阻断(robots/HTTP≠200/meta noindex/x-robots-tag/**canonical 指他址**)+in_sitemap 交叉(单图 8MB 上限);GitHub 因子:topics≤20/README 三问/社区五件套+CITATION.cff;**GitHub 流量快照每 24-48h 归档**(平台保留期限制);反幻觉三规则(API 受限标 unknown 而非 failed)。

## rampstackco/claude-skills(941★)
五层诊断(→已入 drift);补充:重定向 1 hop 301;"A page can lose traffic without losing rank if SERP composition changed";9 失败模式全文(跳算法归因=懒惰/无基线一切皆警报/品牌非品牌不同团队/**四源并用禁单源**/不许提前安抚)。

## janreges/siteone-crawler(938★)
CI 门 15+参数(→已入 scoring);补充:分档 ≥9 Excellent/≥7 Good/≥5 Fair;**--ci-min-pages/assets/documents 防爬取不完整假绿**(0 页或全负状态码立即 fail);**baseline 缺失大声 WARNING 而非静默跳过**;ignore-code 与 fail-on-code 并存时 ignore=accepted wins;输出三形态(JUnit XML/GitHub ::error 注解/结构化 CiCheck);best_practice 检查码命名法(pages-without-h1/title-uniqueness/avif-support…);全站转单文件 Markdown("smart header/footer dedup——ideal for feeding to AI tools");WACZ 归档。

## thedaviddias/llms-txt-hub(911★)
1,515 条语料分布+校验反模式(`<meta|<!DOCTYPE|"informationation and resources"` 等即质量告警);**五种实证写法**(Anthropic 语言矩阵/Cloudflare 递归分片/Vercel 行为指令段+?from=llms-txt/LangChain 按页数分层递归/Docker 双通道;Stripe 反面)。

## callmesora/llmops-python-package(895★)
跳过(纯工程脚手架;仅 prompt/参数外置 YAML+追踪范式)。

## teles/awesome-seo(883★)
OSS 补条目:GSC Indexer(索引提交自动化)/geolint("ESLint for AI search" 四合一)/squirrelscan(295+ 规则 QA CLI)/ai-crawler-bots(CI 审计 Action)/ChatGPT Citation Checker/mesure-citations(法语隐私优先)/GEO-AEO Tracker(自托管看板)。
