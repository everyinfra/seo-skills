# 批 17-20 提取档案

## unifapi-agent/agents(589★)
五状态差距+no-answer 分母+配对协议(→已入 geo-platform);补充:mentioned≠cited 分开返回;**/geo/serp 的 is_target 匹配链接宽于 references 不能证明 citation;best_rank 是结果位置非品牌推荐名次**;"Retrieved but unused search results are not citations";计价 /geo/answers 每次 30 credits($0.03)含 no-answer,20 prompts×2 engines×2 samples ≤2,400 credits($2.40);Panel 冻结项(prompt 原文/品牌别名/引用域名/子域是否计入/引擎/locale/样本数/权重)初始 10-30 条;force_web_search true/false 永不混合(Gemini 不支持该参数);每答案每品牌至多计 1 次,coverage 各品牌之和可>100%,share 恒和 100% 空分母返 N/A;快照存全部响应+billing+request id;timeout 记 unknown 并预算最大成本不自动重放;**"Do not call weighted coverage 'share'"**;"JSON-LD/llms.txt/adding quotations cannot guarantee a citation or transferable percentage lift"。

## iannuttall/seo(565★)
MCP 78 工具;发现协议三段(seo_list_reports→describe→run);**回归四件套**(technical-watch/crawl-diff/index-watch/measure-change);index-watch MAX_DIRECT_INSPECTIONS=100/ATTEMPT_RETENTION=20,每 URL 存 verdict/coverageState/indexingState/robotsTxtState/pageFetchState/googleCanonical/userCanonical/lastCrawlTime 快照;**measure-change 反事实公式**:expectedAfter=treatmentBefore×(controlAfter/controlBefore),delta=treatmentAfter−expectedAfter;**"A fix contains an instruction. A review contains change conditions"**(fix 枚举 fixed/deferred/not-needed;review 枚举 changed/no-change/deferred,均需证据);"Partial data is never reported as zero";"Grouped Search Console totals can undercount";noindex/canonical/robots 是 observations until 用户确认;**Never promise clicks/rankings/indexing/traffic/AI citations**;报表元数据 readOrder/doNotClaim/related;首命令 --actions-only --json "Do not pipe through head";行数须对上 findings.counts.returned;**客户报告 HTML 必须 noindex,nofollow 无远程脚本**。

## artiebits/svelte-seo(563★)
两条细节:JSON-LD 注入 `JSON.stringify(data)+"<"+"/script>"` 拆开防 Svelte 解析中断;robots+googlebot 双标签始终输出默认 index,follow。

## argusdusty/Ferret(545★)
跳过(Go 子串搜索引擎,主题错配;仅 Levenshtein-1 容错概念)。

## Yuzzyuk/marketing-os(538★)
五杠杆+slop 全文(→已入 citability/ai-writing-detection);补充 geo.md 独有条目:**"If a page contains no fact a model could not have invented, it will not be cited, no matter how well it ranks"**;基线=每问题至少查 3 次(引用非确定性),复测日期+30;"GEO without a repeat query is astrology";**anti-citation 反信号 8 条**:CTA 密度读作漏斗/弹窗 cookie 墙盖内容/薄页复述/无作者无来源身份/时间敏感却无日期/关键词堆砌("credibility tell")/主内容客户端渲染/无证据最高级;robots 放行 AI 爬虫="business decision, not a technical default";binding constraint 诊断(通常一杆独大,其余四杆不动它之前修了没用)。

## firecrawl/llmstxt-generator(538★)
跳过(薄封装):免费层 10 URL/BYOK 100/300s 超时;API key 经 URL query 会进日志(安全隐患)。

## avansaber/seo-monster(532★)
DiD+Content-Signals(→已入 drift);补充:ai_citation_readiness——**GPTBot/ClaudeBot/PerplexityBot fetch 不执行 JS,SPA 不可见;schema.org/FAQ/llms.txt 仅 informational 不计分("2026 evidence does not support them as AI-citation drivers")**;ai_referral_overview=GA4 原生 ai-assistant 频道+host 正则,~70% dark-traffic 低估,AIO 点击归 Organic 需单列;ai_citation_track 默认 7 samples/prompt+95% CI+run-to-run 波动率,"NOT an AI rank";gsc_keyword_expand:"GSC hides ~75% of impressions";indexnow_bulk_submit 单 host 上限 10,000;gsc_batch_inspect 上限 25。

## prakharsr/audiobook-creator(530★)
跳过(领域外)。

## amplifying-ai/awesome-generative-engine-optimization(517★)
**案例库**:2,300% AI 流量(制造业 E-E-A-T)/200% 月增长(汽配 schema+llms.txt)/115% visibility(Geneva)/Ramp 7×(3.2%→22.2%)。**论文清单**:GEO 原始(arxiv 2311.09735)/C-SEO Bench(NeurIPS 2025 "most current GEO methods largely ineffective")/ConflictBank 7.4M 对/ConflictingQA(LLM 重 source relevance 轻学术语气)/GASLITE(0.0001% corpus poisoning 即 top-10 劫持)/Adversarial SEO(隐藏文本 AI 提及×2.5)/Ranking Manipulation/Persistent Pre-Training Poisoning。**行业数据**:Wikipedia 47.9% ChatGPT/Reddit 46.7% Perplexity;Conductor 13,770 域 17M AI 回答;24% ChatGPT 回答不联网;<3 月新内容被引 3×;Ahrefs AIO 降点击 34.5%;AI 流量 2025 +527%;Tow Center AI 引用>60% 失败率;**llms.txt 784+ 站=top1000 的 0.3%**(Rankability 跟踪;2025-12-03 Google 加入又当天撤下);ChatGPT 提示词均值 23 词 vs 搜索 4.2 词;AIO 旁广告 ~3%→~40%。

## respectlytics/respectaso(517★)
预注册标定(→已入 geo-evidence);补充:POP_TO_SEARCHES 曲线锚点=(1,1)(20,35)(40,70)(50,280)(60,1150)(70,4600)(80,19000)(90,76000)(100,300000)——**pop 40=Apple 官方数据地板(≥500 周搜)是首个硬绝对锚点**;40-100 段 log-linear ~15%/点;非美 storefront 乘 countries.market 系数;权重照抄(intercept 3.6672/f_result 1.0404/f_leader −1.9714/f_title 0.6129/f_depth 2.9001/f_spec 0.8644/f_exact −0.338/x_top1_exact 2.1709/x_leader_mag 8.1524);六信号分值(结果数 0-25/领导者强度 0-30/标题匹配 0-20/市场深度 0-10/具体性 −5~−30/精确短语 0-15);难度分层 Very Easy<16…Extreme 91+;机会分标尺 1 下载/日=50 分每十倍 20 分;**twin-row 一致性**:同词同店同日共享同一读数。

## yaojingang/GEORank(492★)
(→已入 report-templates 30/60/90+keyword 拓词);补充:诊断权重 DEFAULT={schema:0.3, content:0.3, meta:0.2, citation:0.2};内容评分 100 分制:单 H1+20/H2≥2+20/**首段>80 字符+20**/字符>800+20/alt 覆盖≥60%+10/FAQ≥1 或列表≥2+10;阅读时长=字符/450;引用评分:外链≥3+40/权威链≥2+40/外链≥10 或内链≥12+20;权威域名表(arxiv/scholar/pubmed/doi/ieee/acm/nature/science/wikipedia/gov/edu);Schema 评分=min(100, max(类型数×16, 覆盖率)),推荐 5 类型 WebSite/Organization/FAQPage/Article/BreadcrumbList;LLM 输出契约 urgent/recommended/optional 各≤3 条。

## cablate/mcp-google-map(469★)
(→已入 local 三指标);补充:每点返回 rank+top3 竞品名;支持≤3 关键词批量;GBP 信号权重表(主类目/评论数/评分/评论关键词=High;照片/完整性/菜单/回复率/NAP=Medium;Posts=Low);**API 盲区**(搜索印象/3-Pack 出现率/Direct vs Discovery 比例);反模式 7 条(商家名堆关键词/创意菜单名/照片荒漠 0-3 张/夏冬数据直接对比)。

## quantumproxies/quantumproxies.io(469★)
跳过(营销仓):仅 uule 本地化 SERP 线索一句(用户名语法 country-us-session-ab12-lifetime-10 粘滞 10 分钟)。

## josstei/maestro-orchestrate(465★)
schema 选型矩阵+两级阈值(→已入 schema/validation);补充:canonical>1 跳标记/重定向>2 跳/软 404;严重度三级定义(Critical=整页不可索引);Handoff Report 固定字段;一源多运行时打包(同 src→四运行时)。

## seo-skills/seo-audit-skill(457★)
(→已入 validation);补充:canonical 家族 9 条(指向 noindex=fail/head 外=fail/带 hreflang·media 属性=fail/指向外域=info"联合发布合法但让渡权重");CWV 阈值 LCP 2.5/CLS 0.1/INP 200/TTFB 800/FCP 1.8;DOM<800 过/800-1500 警/>1500 fail;静态资源 max-age≥1h、文本>2KB 须压缩、图片>100KB 警 BMP·TIFF fail;**i18n 13 条独立类目**;E-E-A-T 16 条含 NAP 一致性+local-business 页须配 geo meta。

## ai-search-guru/getcito(448★)
跳过:**README License 明文"GetCito v9 is a fork of Elmo"**(MIT 合规换牌);代码级验证 fanout-analysis.ts 与 elmo 近乎逐行相同;数字以 elmo 为准。

## joeseesun/qiaomu-seo(441★)
(→已入 geo-evidence schema);补充 engine-matrix:**IndexNow 200/202=received/accepted, not indexed**;UA 可伪造——身份验证须官方 IP 段或正反 DNS+日志,**禁止仅凭 UA 给 allow/block 建议**;**改 robots 前必须建"平台控制矩阵"表**(provider/UA/自动爬 vs 用户触发/业务政策/当前指令+来源+复查日期/预期效果与失控项)——防一条 User-agent:* 意外耦合搜索发现·模型训练·用户访问;33 个官方源登记;validate_knowledge.py --strict-stale 强制。

## AgriciDaniel/claude-youtube(436★)
(→已入 video);补充:tags 500 字符上限只值 30 秒;章节 0:00 起≥3 章≥10 秒;hashtags>15 全忽略,前 3 显示在标题上方;**VideoObject schema +30% CTR,2023 末起视频须为页面主内容**;视频词 how to/tutorial/review/vs/explained;满意度信号完整排序;**2 小时内回复 50+ 评论=+15-20% 触达;24h 通知上限 3 次**;<500 订阅获算法扶持;Shorts ~28-30 天失新鲜;设备加权 TV>Mobile。

## elmohq/elmo(419★)
(→已入 geo-platform 测量口径);补充:README 竞品对照表(Profound 企业定价/Ahrefs Brand Radar $129 起/Semrush $139.95 起;承认对方有 prompt 量估算/情感分析,elmo 无);coverageRate 发布为 0..1 比率;上限 topQueries 25/terms 60/wordChanges 60/perModelTop 8/variations 10/breadth 20;**跨 prompt 广度双榜**(按 distinct prompts vs 按 runs)。

## boraoztunc/skills(397★)
(→已入 geo-evidence 治理三法);补充:拒绝理由实例——19 个 palette-dump 技能拒绝("共享同一生成模板…降低 skill 路由质量");tailwindcss 拒绝(纯 v3 零提 v4,"agent 照做会写出被静默忽略的配置");gooey-blob-system 拒绝(规定阈值却省略 feColorMatrix 数值——"唯一难的部分");demo/ 76 个 index.html 塌缩成少数字节级相同文件;采纳纠错实例(progressive-blur 补 16 条 -webkit-mask;100vw→100% 滚动条错位);rules-with-exact-values vs taste-and-philosophy 分区原则("回答不同问题、刻意共存");付费非 OSS 标 ⚠️。
