# 批 05-08 提取档案

## Ryze-AI-Adgent/open-seo-mcp-skills(4590★)
seo-vs-ads 四桶(→已入 brand-mention);补充八技能细则:**seo-audit**:衰减页=点击环比跌>30%;CTR 异常=位置≤5 但 CTR<2%;striking distance=位 8-20 高曝光;同 query 多页分食即蚕食;inspectUrl 抽查最差 3-5 页。**rank-tracking**:默认 28d vs 前 28d;"GSC 滞后~2 天永不包含今天";Winners/Losers=±2 位且真实曝光;**按损失点击排序不按名次差**("4→7 金钱词胜过 40→80 无关词");rowLimit 起 5000。**keyword-research**:种子扩~200,top~50 enrich;"Never invent volumes";CPC 必须输出(兼作否定词源);已有排名→optimize-not-create。**competitor-gap**:三桶 Gap(对方 top20 你零曝光)/Behind(差≥5 位)/Ahead;竞品品牌词默认剔除除非做 vs 页。**backlink-check**:红旗=精确匹配商业锚规模化/链接速度尖峰/低权域主导;第三方数字一律标 index estimates。**ai-visibility**:GA4 实测 AI referral 优先于 prompt 采样;fallback sessionSource 匹配 chatgpt.com/perplexity.ai/gemini.google.com/claude.ai/copilot.microsoft.com。**content-brief**:读 SERP top3,全覆盖=table stakes、无人覆盖=the opening;title/meta <60/155;内链 3-5 来源;长度=排名中位数。

## naxiaoduo/1000UserGuide(4082★)
国内渠道(→已入中文指南精选);补充海外面:网站~70(Betalist/MicroLaunch/PitchWall/OpenAlternative/StartupBase/LibHunt/SourceForge)/AI 导航~97-117/传统目录~58(Blogarama/Jayde/Viesearch)/社区 18(PH/Show HN/indiehackers/Uneed/dev.to)/Reddit 26 条(SideProject/IMadeThis/RoastMyStartup/Alphaandbetausers);**收录门槛四条**:必须免费/不在清单/有运营联系方式和隐私政策/有一定浏览量。

## irinabuht12-oss/marketing-skills(3968★)
同为 Ryze 出品;**Ads 侧竞价内耗 cannibalization**(非 SEO 同词多页):exact 在 A($28 CPC,4.2% CVR)vs broad 在 B($41,2.1%),broad 抢走 exact 35% 流量;时机=接手关键词蔓延账户/CPC 无故上涨/季度清理。**brand-answer-monitoring**(→已入 brand-mention)。

## nowork-studio/notfair-plugin(3911★)
sitemap 六坏桶+lastmod 造假+hreflang 簇矩阵(→已入 validation);补充:broken-link checker 实现——HEAD 优先被拒降 GET;timeout 10s;爬取前读 robots.txt;ThreadPoolExecutor 并发;默认 max-pages 50;内部 404 优先(完全可控);**priority/changefreq 明说 Google 基本忽略**;WP/Rank Math 默认 /sitemap_index.xml;48 技能分簇 SEO 15/paid 14/平台 8。

## yaojingang/GEOFlow(3774★)
85/70 门禁+四态(→已入 geo-evidence);补充完整预算链:**≤5000 字正文 P50≤25s/P95≤55s;全文预算 180s+抽样预留 45s+持久化 10s=硬截止 235s**;单篇最多 12 条物质性主张;1 次文章级检索+最多 6 次补检;注入≤12 条/6000 字符证据;输出上限 2048 token;**性能类超限才可降级抽样,配额/鉴权/限流/供应商故障直接失败不许抽样**;抽样器=≤6000 字符、≤12 个不重叠偏移、固定覆盖标题/摘要/开头/结论/高风险词/数字/日期/引用/承诺;灰度只许 0/10/25/50/100 五档,每次 promote 需 30 天内端到端报告,incident 冻结;熔断=连续 5 次可重试或 10 次内错误率≥50%→开 60s;金标准 starter 6 样本 production_gate_ready=false,**生产需 120 校准+60 固定回归+60 盲测,两人独立标注+第三人裁决**;自动优化上线需 240 基础+120 优化基准+30 对抗样本。

## iamvishnusankar/next-sitemap(3745★)
sitemapSize 默认 5000(非 5 万上限,保守拆分);v2 起默认索引 sitemap;robots 默认只列索引 sitemap 防双重提交;Host: 指令(Yandex 语义)+Crawl-delay 支持;additionalPaths 冲突原位合并;transform 返回 null=剔除;changefreq 默认 daily/priority 0.7/autoLastmod true;News/Image/Video sitemap 字段(news.title/publicationName/publicationLanguage/date);alternateRefs 生成 xhtml:link hreflang。

## ericosiu/ai-marketing-skills(3617★)
gsc_auth:scope 仅 webmasters.readonly;redirect localhost:8765 一次性 HTTPServer;access_type=offline&prompt=consent 强制 refresh_token;token 存 .gsc-token.json chmod 0600;拿到即 sites().list() 验证。**trend_scout 四源**:Google Trends RSS(geo=US 前 20 含 approx_traffic)/HN topstories(前 30,满 10 停)/Reddit 6 sub hot.json limit=5(**score>50 才收录**)/X 走 Brave Search API site:twitter.com OR site:x.com freshness=pd 无 key 跳过;相关性打分 HIGH+25/MED+10/LOW+5 封顶 100;白名单门槛 Trends≥20 其余≥15。**yt-competitive-analysis**:离群=播放>该频道该形态均值 2×;长短分开算基线(≤60s=Short);每频道 100 条近 30 天;标题模式提取=分词+60 词停用词+len>2+Counter 前 15;纯标准库实现。

## artesaos/seotools(3365★)
webmaster_tags 六家(google/bing/alexa/pinterest/**yandex/norton**);`add_notranslate_class`:title 加 class="notranslate" 防 Google 翻译改标题;generate() 顺序 title→description→keywords→自定义→canonical→amphtml→rel=prev/next→hreflang→robots;JsonLdMulti 一文多 schema;OG 垂直类型全字段表(article/book/profile/music/video/place);图片四种传法;og:locale:alternate 数组。

## xnx3/translate(3091★)
客户端翻译零 SEO 收益(源码/URL 始终单语)——反例;TCDN 分支=服务端改写 HTML 各语种可绑独立域("google 收英文站、NAVER 收韩文站")但**全篇未讨论机翻质量/重复内容风险**=scaled-content-abuse 实证反例。

## oxylabs/how-to-scrape-google-trends(2912★)
Trends 数据模型四分法:interest_over_time/breakdown_by_region/related_topics(含 mid/topic_type)/related_queries(rising/top);每类列表数据在 [0]["items"];related_topics 需展平(topic.mid/title/type+value+formatted_value+link);自然主键 iot=time/bbr=geo_code/rq=query/rt=title;多词比较 merge 规则(iot on time/bbr on geo_code/rt·rq inner)。

## aaron-he-zhu/aaron-marketing-skills(2888★)
CORE-EEAT 80 项(→已入 citability 完整);补充 CITE 40 项独有条目:C01 引域≥500(50-499 半<50 败)/C02 ≥20% 引域 DA/DR50+/C03 源站出链<1000(>10000 稀释)/C04 无月份>3×月均/C05 ≥2 AI 引擎≥10 利基查询被引/C06 ≥50% 引用为主/唯一来源/C07 ≥3 引擎/C08 ≥80% 正/中性/C09 ≥60% 编辑链/C10 ≥3 行业+≥5 地区;T03 VETO 链接流量相干性/T04 **VETO 单 C 段>5%(>20%=PBN)**/T09 VETO 人工处罚;E01 top100 词≥1000/E03 ≥3 种 SERP 特性/E04 AI 爬虫宽松+SSR+<3s/E07 长尾(4+ 词)深排名/E09 ≥10 国流量;6 域型权重表(机构 C=45%/产品工具 I=30%/电商 T=35%/社区 E=30%);**1 个 verified veto 封顶 59,2+ 直接 BLOCK**。

## zubair-trabzada/ai-marketing-claude(2723★)
六维加权+五档锚定(→已入 report-templates);补充:预抓取首页+至多 5 内页;业务预分类 6 类(SaaS/电商/Agency/本地/创作者/Marketplace);market-technical 子权重(Page 25/Crawl 20/Perf 15/Content Arch 20/Schema&Tracking 20);追踪检测表(GA4 gtag·gtm/Meta Pixel/LinkedIn Insight/Hotjar/cookie consent/UTM)+schema 七类;A/B 假设模板 "If we [change], then [metric] will [improve] because [reason]"。

## AnswerDotAI/llms-txt(2653★)与 docmd-io/docmd(2514★)
(→已入 llms-txt-guide 生态节);补充:Optional 段 v2 起**无机械语义**(v1 展开工具已移除);不用 well-known 的论证(仅 origin 根与路径描述需求冲突);写作指南 4 条含"仅以 llms.txt 为起点向 agent 提问来测试";目录站 3(llmstxt.site/directory.llmstxt.cloud/llmstxthub.com);docmd 多语言模式:每非默认 locale 写 llms.<locale>.txt,**默认 locale 永远占无后缀名**;页级双退出(frontmatter noindex 或 llms:false);CSV/Markdown 双注入防御(`=+-@` 开头加前导单引号防公式注入)。

## Sly777/ran(2204★)
跳过:grep 证实零 canonical/og/schema/sitemap;react-helmet 逐页 title+固定 robots index,follow 而已。
