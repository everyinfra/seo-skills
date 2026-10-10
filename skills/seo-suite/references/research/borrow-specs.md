# 借鉴实施规格库(borrow-specs)

> 建立 2026-10-10。13 个研究 agent 对竞品源码/官方文档深读后的**可直接实施规格**汇总;与 competitive-landscape.md(全景)配套,本文是"怎么抄"的施工图。标注:【官方】=一手口径,[推断]=我们自定并注明,未公开=厂商不发布(勿编造)。每条含落点与来源。

## A. 审计与健康分(site_audit.py / health_score.py / 规则目录)

### A1. health_score.py(Lumar+Ahrefs+Ryte 三合一)
- **Lumar 六大类树**【官方】:Availability / Indexability(Non-Indexable·Canonicalization·Mobile Indexability)/ Uniqueness / Discoverability(Crawl Budget·Internal Linking·Redirection·Sitemaps·Internationalization)/ Rankability(Search Console·Authority·Page Content·Structured Data·Social Tags)/ Experience(Page Speed·Engagement·User Experience·Security·External Links)
- **扣分机制**【官方】:每类 100 起步,只有 sign=negative 的检查扣分(neutral/positive 不影响);类权重=类内负号检查的 weight 之和;缺数据源的类输出 N/A **不计入总分**(Engagement 缺 GA/Authority 缺外链数据即 N/A——直接抄此语义);权重→扣分数值映射未公开[推断:归一化封顶]
- **Ahrefs 主分公式**【官方】:`(无 Error 的内链 URL 数÷内链 URL 总数)×100`,Warning/Notice 完全不扣;分档 Weak 0-30/Fair 31-70/Good 71-90/Excellent 91-100 → 我们:仅 CRITICAL 扣主分,WARN/INFO 单列子分
- **Ryte impact 排序**【官方】:每检查项 impact=命中数×优先级非线性(如 priority²×URL 占比);impact=0 的标 Opportunity("值得探索"栏),>0 按降序("立即处理"栏);每项 impact=修复后总分提升量
- **--ignore/--severity 语义**【官方,Ahrefs】:忽略=既不进 findings 也不进分数,报告保留 ignored 列表;降级 CRITICAL→WARN 自动退出主分扣分项;配置存 `{"rules":{"<id>":{"enabled":bool,"severity":"..."}}}`
- **SEO 六阶段流量漏斗**(traffic_funnel.py)【官方判定】:available(200)⊃indexable(无 noindex/未屏蔽/自指 canonical)⊃unique(primary=唯一或重复集内 DeepRank 最高[相似度阈值未公开→Simhash 0.9 自定])⊃in-SERP(GSC impressions>0)⊃with-clicks(clicks>0)⊃good-UX(LCP≤2.5 且 CLS≤0.1 且 DCL≤1.5);每阶段输出 pages_in/through/dropped/drop_rate/cumulative;无 GSC 时漏斗截断到 uniqueness 并声明
- **降级声明**【官方,Ryte】:爬取样本<全站时"两次分数不可比"必须显式输出 coverage_ratio

### A2. 规则目录解释层(SF+Sitebulb 文案结构)
- **Sitebulb 九节结构**:意味句("该 URL…")/为什么(1-2 段,双理由 SEO+用户)/触发(编号判定+阈值+代码示例)/定性(issue|warning|opportunity)/反直觉提醒/分型修复/逐 URL 排查/导出/延伸
- **两句话定律公式**:"X 不(直接)影响 SEO,然而影响 Y,所以一般建议 Z。但在{某种页面/规模}下可合理不修"(例文 4 条已录 SKILL 报告)
- **类型×优先级两轴**(SF 320 条矩阵实测):Opportunity 永不给 High;"坏信号>缺信号"(canonical 冲突=High,canonical 缺失=Medium);Sitebulb 另有 Insight 级(观察项)与 Potential Issue 型(现在没坏将来可能坏)
- **SF 阈值表**【官方】:title >60 字符/561px 过长、<30/200px 过短;desc >155/985px、<70/400px;H1>70;URL>115=Opportunity;sitemap>50k URL/50MB;图片>100KB、alt>100 字符
- **具名 bulk export 命名**:`{类别} > {Issue 名}`+变体后缀(Inlinks/Summary);每 rule-id 一个受影响 URL 清单文件

### A3. AI Search Health 独立子分(Semrush)
- **8 bot 名单**【官方,检查这 8 个而非 27 个全量】:ChatGPT-User/OAI-SearchBot/Googlebot/Google-Extended/Perplexity-User/PerplexityBot/Claude-User/Claude-SearchBot;GPTBot/ClaudeBot(训练)**不在内**——"训练 bot 不影响搜索可见性";Google-Extended 非爬虫是 robots token 单列
- **检查项**【官方】:llms.txt 存在性+格式(细则未公开→按 llmstxt.org 规范[inferred]);内容过长(阈值未公开→自定 >100KB 或 >15k 词[inferred]);Last-Modified>**6 个月/183 天**(官方);语义 HTML 比值低(=语义标签÷其他标签,百分比阈值未公开→自定<10%[inferred]);content not optimized(标题层级/长段落/可读性,数值未公开)
- 独立 widget 与 Site Health 并列,底层检查共享;可选 UA=OpenAI-Search 视角抓取

### A4. GEO 技术审计补强
- **AEO rendering 5 检查**【geo-aeo-tracker 源码】:CSR 检测(空挂载点 #root/#app/#__next 且纯文本<200 字或 text/HTML<0.02;有 __NEXT_DATA__/data-reactroot 赦免);noscript 回退(存在且>20 字符);JS 重量(外部 script>15 或内联>100KB);服务端内容质量(>500 字符且有 article/main/section);H1==1 且 H2≥2
- **BLUF 密度**【源码公式】:first_chunk=前 max(20%·len,400) 字符;score=min(1,(直答短语+li>3+长度>100)/2);直答短语正则 `/in short|tl;dr|summary|key takeaways|bottom line|the answer is|here's what|here's how|here's why/i`;pass≥0.5
- **Otterly structured data 权重**【官方逐分值】:总分=Structure×0.30+Content×0.35+Metadata×0.25+Technical×0.10;Structure:H1 层级 30(单 H1=15/多=5/H2=10/H3=5)+语义 HTML 25(命中/7×25)+列表表格 20+段落 15(均长 50-200 字符满分)+nav 10;Metadata:title 30+desc 30(120-160 满分)+JSON-LD 25+OG 15;详见 agent 报告
- **Rankscale 六因**【官方】(前三 Access 后三 Parsing):crawler blocked/未被 Google 收录/JS 渲染内容/缺 JSON-LD/H1H2 层级断档/non-chunked content(段落脱离上下文无意义);**8 类页面逻辑门**先分类后差异化阈值(Local/YMYL/SaaS/E-com/News/Support/Entity Root/Other);branded prompt Detection Rate<90% ⇒ 先修结构再做内容
- **Grounding Page 11 条 checklist**【官方】:H1=实体名/首段一句事实定义/Core facts 用 `<dl>`/FAQ 5-10 条每答含实体名/**volatile facts 独立区块**+"is NOT"消歧/JSON-LD 与 HTML 镜像+sameAs/hub-and-spoke 拆分规则/交叉链接 @type 谓词/review date≤6 个月/URL 简短

## B. GEO/AI 可见性(citation_panel.py / ai_referral_log.py / 新脚本)

### B1. citation decay 协议(Profound 官方方法论,2026-09 88.3 万页研究)
- 序列:7 点滚动平均(官方 14 天,我们采样密度低用 7[推断])
- **资格闸门 4 道**【官方】:观察窗≥28 天;峰值窗内采样≥5;峰值>0;首采距窗起点>30 天剔除
- 判定:peak=平滑最高;**half-life=peak 后平滑值≤50% peak 且连续 14 天无反弹的天数**(未达成=holding 右删失);状态机 rising/peaked/decaying/decayed/holding
- **重写队列**【官方】:"过峰且 citation share 正跌向峰值一半"的 owned 页按距半衰剩余天数排序——decay 是触发器不是季度末发现
- 官方常数【可直接当默认阈值】:中位半衰期 11 天;首引→掉半中位 42 天;78% 页两周内掉半;**跨引擎相关仅 0.03-0.09(分引擎独立判定是硬规则)**;5+引擎被引页 8 周存活率 6.8%(单引擎 1.2%);内容家族半衰期 Choose 29/Explain 28/Sell 28/Report 27 天
- 落地:citation_panel.py 加 `decay` 子命令

### B2. citation_gaps.py(geo-aeo-tracker 算法直译)
- qualifying=有 sources 且(brand 未提及或 not-mentioned)的 run;对每个 cited URL:排除自有域,累计 count/prompts/providers;**hasCompetitorRun(竞品在该 run 被提及)=唯一高优先判据**
- 外联简报字段:Competitors cited/Pages(URL+次数)/AI models+prompts/Outreach tip(竞品在场→"贡献内容或争取列表位";不在场→"被引可提升 AI 可见性");CSV 列 Domain,URL,Citations,Prompts,Providers,Competitors,Priority
- 与 cite_domain.py 串联:先 gaps 找目标域,再评级

### B3. prompts 对象化+prompt 库
- panel prompts 从字符串升级 `{text, topic, tags[], stage, branded, region, lang}`;**stage 框架**(Scrunch 官方):awareness/consideration/conversion/loyalty;**初始集配方**:5 awareness+3 consideration+2 decision;每 cluster 12-15 问
- **Peec 三维覆盖**【官方】:旅程×人群上下文×地理;GSC top 词→问句转换公式("What are the best [category] for [persona]");品牌词 prompt 独立项目(混入会污染指标——Visibility 恒 100%);起步 10-20 awareness+20-30 consideration 跑 30 天
- **prompt-bank 20 条模板**(漏斗×视角矩阵+source-seeking 后缀变体)+persona 前缀变换(CMO/Founder/SEO Lead/PMM 前缀+固定后缀)→ templates/research/prompt-bank.md
- **fanout 六类型**【Otterly 官方】:reformulation/related/implicit(沉默内容缺口)/comparative/entity expansion/personalized;引擎展开量基准:Perplexity 12-15/ChatGPT 6-10/AI Mode 8-12/AIO 4-8;选源发生在第 5 步 Citation Synthesis

### B4. 评分与信号协议
- **五维 visibility 打分**(oneglanse 441 行打分 prompt 精髓):A 覆盖 25%+B 首现位置 25%+C 结构显著性 20%+D 频次 15%+E 语境角色 15%;**硬 cap**:仅 1 次提及→≤50;只出现在问题里→≤10;对比性负面→≤35;**反通胀**:平均列名不是 70+;echo-only(回声品牌名)/refusal 不算提及;竞品子产品合并到父品牌取最早位次
- **signals 化 diff**(Scrunch Signals API):|Δ|≥5pp 且配对 n≥10 才报;fingerprint=hash(metric+engine+topic) 跨夜去重;url_movers(每个 URL 对 delta 的贡献排序);三段叙事 what/why/to-do;基线=前 28 天
- **指标公式**【Peec 官方】:SoV=你的提及/(全部追踪品牌提及);win rate=排第一次数÷响应数;**citation rate=被检索时显式引用均次**(direct attribution vs background influence);Brand visibility vs Source visibility 分开(被引不被提=品牌关联弱;被提不被引=内容不被信任);Source 五分类 Editorial/Corporate/UGC/Reference/Own
- **Oracle 差异检测**(Athena):KB≥25 条已验证 facts 才能扫;finding 字段{AI claim, Known fact, Why flagged, Possible sources(调查线索非因果), Severity Critical/Major};状态机 Pending→Acknowledged/Ignored→Reopen;Inaccuracy%=有 confirmed finding 响应数÷扫描响应数;Model accuracy=无 finding 响应占比

### B5. bot 分类与归因
- **四桶**(Profound/Otterly/Peec 三家口径合并):citation/search index/on-demand fetcher/training;ai_referral_log.py 加 --classify;KPI 补 failure rate(4xx/5xx 占比);llms.txt 双基线(占总 AI bot 请求%;vs 站均页面)
- **归因正则**(锚定官方域名):referrer `(chat\.openai\.com|chatgpt\.com|perplexity\.ai|gemini\.google\.com|copilot\.microsoft\.com|claude\.ai|grok\.com)`;utm_source 同名;**AIO 点击 referrer=google.com 无法区分**;一切 AI referrer 数字当下限;**不给入站 AI 链接发明 UTM**;自报归因(注册表单问"从哪听说+用了什么 query")是首选补充
- **source_url 归一化**(Scrunch 官方):小写 host+path,去 scheme/www/端口/query/fragment/尾斜杠

### B6. GEO 周报模板(Scrunch 官方六段中文化)
周报:headline(总 presence%+WoW+最好最差平台)/平台分解/sentiment 快照/竞品 SOV(**>5pp 移动才点名**)/Top5 变化 prompt/**一条**建议动作;月报五节;QBR 8 页;"指标全平时直接说 stable, no action needed——不制造紧迫感"。→ templates/monitor/ai-visibility-weekly.md+monthly.md

## C. 内容(content_score.py / templates/content/ / fix_plan.py)

### C1. content_score.py 维度表(三家合成,权重[推断])
- SEO 轨:term_coverage 0.35(MarketMuse 公式:50 话题×min(提及,2)=满分 100【官方】)/term_importance 0.10(Clearscope:命中竞品数/竞品总数→1-10,8+ 强制计入)/true_density 0.10(竞品词频 P25-P75+位置加权,公式未公开[inferred])/structure 0.10/title_h1 0.05/images_alt 0.05/internal_links 0.05/keyword_variations 0.10(变体强于精确匹配)/bolded 0.05/schema_focused 0.05(1 种满分,>3 扣)
- AI 轨:facts_coverage 0.60(top20 SERP+AI 回答的事实清单,按 AI 回答频次加权)+upfront_intent 0.40(**前三查**【官方】:首句点名主题/含事实锚点/先答案后展开,前 100 词内;38-40% AI 引用来自前 100 词)
- 总分=0.5×SEO+0.5×AI[推断];分档 0-33/34-66/67+【官方】;目标=竞品+10~20 分,甜区 70-85【官方】;**竞品<3 个不同域名不评分**【Surfer 官方】;**关键词密度不计分**(两家官方明确)
- **意图系数**(100 万 SERP 研究【官方】):consequence 0.296/definition 0.271/comparison·reason·exploratory 0.22-0.23/instructional·short_fact 0.19——作优先级系数不改分值;top10 页均覆盖 74% 相关事实 vs 尾部 50%
- 术语表 schema:{term, importance 1-10, recommended_range(竞品四分位[inferred]), used, in_heading, source: serp|ai|nlp}

### C2. content-brief.md 三段式(MarketMuse 官方字段)
- 执行摘要:目标分(竞品均值+10~20 封顶 85)/建议词数/目标意图(附系数)/personas/必答问题/标题(排名实例+须含词)/内链(高相关锚文本→站内)外链(**低相关相邻话题**锚文本→高权威非竞争源——官方设计动机)
- 大纲(每节六件套):建议子标题+词数占比%+必答问题+topics(建议提及次数,封顶 2 次计分)+内链+外链
- 优化要求:术语表/AI 事实清单(按频次排序)/首段三查/结构目标/检查清单+复审频率
- **9 内容类型差异点**(Comparison 必指定实体清单+recommendation 结论;How-to 顺序步骤;Local 必填具体位置;Product Review 13 项考量;News 六项考量含 timeliness/fact-checking 等——全表在 agent 报告)
- 证据头:分析竞品数 N/共现标题 top X/抽取问题 Y/覆盖差距 Z(倒逼真做 SERP 对比)

### C3. fix_plan.py(geo-optimizer 源码级)
- 6 类 FixItem{category, description, content, file_name, action: create|append|snippet}:robots/llms/schema(WebSite·FAQPage·Organization)/meta/ai_discovery/content-rewrite
- **安全设计**:`--apply` 才写盘(默认 dry-run 预览前 30 行);写 `./seo-fixes/` 隔离目录从不覆盖站点文件;修复前先跑完整 audit,audit 失败不生成;目标站值过 html.escape;URL 过 anti-SSRF
- **robots 27 bot 模板**:三层 training(13)/search(10)/user(5);**CITATION_BOTS=5 个**(OAI-SearchBot/Claude-SearchBot/PerplexityBot/Googlebot/Applebot——刻意排除纯训练的 ClaudeBot);**两级评分**:5 个都 allowed=部分分,5 个都有专属规则(非通配符)=满分
- **收益预估**:score_before→after(该类别满分−当前得分封顶);robots_posture.py 同步扩 27 bot+answers/training 分层(封 training 不扣分,封 answers 才 fail)
- robots 解析:RFC 9309+BOM 剥离+500KB 截断+连续 User-agent 合并;classify 四态 allowed/blocked/partial/missing+via_wildcard

## D. 监控与 CI(monitor.py / notify.py / workflows)

### D1. monitor.py 缺口清单(对标 Conductor/Sensor/siteone,按优先级)
- **P0-1 页面级 noindex 检测**:meta robots+X-Robots-Tag 响应头(Conductor 头号触发器"Pages became non-indexable");规则 noindex_added(critical,进抑制树)/noindex_removed(info 自愈);http_get 需保留响应头
- **P0-2 canonical 目标健康度**:对 key_pages 的 canonical 目标 HEAD,存 status;规则 canonical_target_broken(warn)
- **P0-3 按告警类型路由**:channels 加 `route: {codes: ["robots_*","noindex_*"], channel: "slack:tech"}`
- **P0-4 波动上下文**:gsc.csv 有 Position 列时算自有词集日波动(每词|Δrank|/N 均值→0-10;档 0-2/2-5/5-8/8-10【官方】);下跌告警附 `serp_volatility:{score,z30}`;z≥2 降 info 改 message"疑似算法更新而非站点问题";deviation(d)=(score−30 天均值)/std
- P1:segments 模型(name+regex match+importance 来源)与受影响度=Σimportance;accepted_codes 白名单(code:key 指纹,接受≠消失,周报仍计数);`diff --ci` 输出 {passed,checks:[{metric,operator,threshold,actual,passed}]}+JUnit+`::error` 注解(exit 0/1,失败=10 参考siteone);sample-keypages 子命令(末段替换 slug 归一→groupBy→每组随机抽 8∪手工清单);baseline 缺失且库龄>7 天响亮 WARNING(payload 记 baseline_missing)
- P2:title/meta 区分 changed vs removed(值为空=removed warn);h1/hreflang 进 diff 指纹;GA 跟踪消失(expect must_contain "gtag(");非规范域名重定向失效 probe;多断言(expect 数组/latency 上限/selector 稳定);visibility 的 SERP 源适配层(id/name/website/price/quota/build_url/parse);**"半数请求失败→判 error 不判 0"**(serpbear 防假 0);digest 头部 N improved/M declined;丢失特判 prev-100
- **告警定义模型**【Conductor 官方 5 参数】:{triggers, scope, sensitivity: low|medium|high|always(segment 型 7 档 0/1/5/10/25/50/75%), recipients};敏感度=受影响页数×Importance 加权;incident 自动关闭=全部恢复(发 resolved)或 24h 无新增;Alerts(重要才推)与 Tracked Changes(全量留档 60 个月)分离
- **changelog.py 事件 schema**【官方】:{url, ts, change_type: changed|added|removed(4xx)|redirected(3xx)|other(5xx), property, old, new, snapshot};不追踪清单(仅当前值):入链/出链/PageSpeed;检索粒度 14 天内按日更早按周

### D2. LHCI 断言 schema(CI 门)
assertions: {"<auditId>": level|[level,{minScore|maxNumericValue}];"categories:<id>"};level=off|warn|error;聚合=median|optimistic|pessimistic;默认 3 runs

## E. 工作流与产品化(跨脚本)

### E1. forecast.py(seoClarity 六步【官方】)
1. GSC 90 天按 移动/桌面×品牌/非品牌 建 CTR 曲线(预测只用非品牌);2. est_traffic=Σ搜索量×CTR(当前位);3. **与 GA 真实对比校准**(校准系数持久化——四家唯一明示的自校准);4. CPC 评估竞争(traffic_value=visits×CPC);5. 三 scenario【官方枚举】:全部词到第 X 位/变化 X%(保守 10-15%)/变化 X 位(>30 位不预测);orders=traffic×CVR,value=orders×AOV;6. 汇报
- **省钱结构**:Traffic Potential×CPC=等效付费成本,提案只投 10%;**赚钱结构**:流量×CVR×AOV;ROI=(转化价值−投入)/投入;5 种 ROI 法(实际转化/Traffic Value/相对付费省钱/付费 CVR 估算/按项目 tag 归因)
- 无排名数据:搜索量+行业 CTR benchmark+CVR/AOV 建模【官方支持】

### E2. prioritize.py 条件规则(Botify 官方阈值示例)
depth≥6 clicks→上移;inlinks<4→增至≥5;title<50→50-60 字符;desc<100→~155;thin content<100 词(除模板);重复≥90% 相似度;canonical 配对相似度<75%→移除;**放大器**:内链指向问题页且被链>10 次;**条件依赖型**:"noindex 是否问题取决于意图"/"canonical 对错取决于 PageRank 对比";组合信号型(重定向×canonical 五种交叉);segment 切换触发优先级重算【官方行为】

### E3. 凭证分层+doctor(claude-seo 源码)
detect_tier 纯本地文件判断:T0 无凭证纯静态→T1 PSI/CrUX key→T2 GSC OAuth/SA→T3 GA4;输出 {tier, capabilities[], missing}进报告头部;**报告固定带 Data Sources & Methodology 页脚表**(Source/Description/Update Frequency);doctor 检查 Python 版本/markets.json 可解析/模板齐全/通知渠道配置(**只打渠道名不打值**,redact:home→<home>/email/token/password 正则)

### E4. 可证伪 4 字段+落盘契约(claude-seo)
- 每条建议必带:**依据的第一性观察/依赖解锁关系/显式失败判定("怎么知道它失败了")/先行指标(不重跑审计就能监控的)**;审计末段点名"下次该看什么+本次测不了什么";曾失败的建议不复推
- **findings 部分落盘契约**:每个检查类别首遍即写 findings/*.md,完成时覆盖(防 maxTurns 掐断丢结果);统一 audit-data.json envelope(summary{health_score,business_type,top_findings,quick_wins}+categories[].findings[]{title,severity,description,recommendation}+action_plan.phases)供 monitor/notify/报告复用

### E5. 过时信号看门(直接建 deprecated-signals.md,claude-seo 全表)
FAQPage 富结果 2026-05-07 全站退役(存量标 Info 不标 Critical,不建议删除/新增;真问答用 QAPage)/HowTo 2023-09/Course·EstimatedSalary 等 2025-06-12/SpecialAnnouncement 2025-07/PracticeProblem 2026-01;**INP 不提 FID**(2024-03 替代;无 VSI/无 CWV2.0/LCP 未降 2.0s——全是第三方幻觉)/Lighthouse12 删 PWA/GSC Page Experience 报告已移除/GSC 数据 2025-05-13~2026-04-27 不可靠/AI Mode 流量并入 Web totals/GBP chat 2024-07-31/sitemap priority·changefreq 弃用/Indexing API 仅限 JobPosting·BroadcastEvent;**配套 test_canonical_facts.py**:(regex,为何错,一手来源)三元组参数化扫描全部文档,匹配已知错误陈述即 fail

### E6. 数据源标注五段合同(open-seo-mcp-skills,与我们最同构)
每 skill/脚本声明:Requires(依赖什么数据)/Workflow(内联精确调用)/Output(verdict 先行+表格列定义)/**Fallback 四降级模式**(等价工具重建+附完整条件/供应商链降级/可选增强静默跳过/**停止并指名缺什么**)/反编造守则("Never invent volumes;真实数据优先,估算打 [est] 标")——落地:SKILL.md 的 52 脚本条目各加三行微标注(数据/降级/反编造)——✅ 已落地为 references/overview/data-source-contract.md

### E7. facts 实体页(Rankscale)与 Brand Records(Profound 六记录)
- facts 页结构:Status/Entity type/Updated 头部+一句话 lead definition(被 AI 逐字引用的目标句)+Core facts+**Volatile facts 独立区块**+is-NOT 消歧+FAQ(每答含实体名)+Sources
- Brand Records 六记录【官方】:Company/Market/Offerings(**批准术语+能与不能宣称**)/Audience/Strategy/Execution(**从不做的事**);每条 {fact, source, date, confidence};缺口协议:"够用但不够具体"时抛单个可跳过的问题,答案回流

### E8. 评分模型版本化与契约(geo-optimizer)
CATEGORY_MAX 常量+权重守恒断言(各类目和=100,改权重必炸测试);JSON 输出带 schema_version+冻结 fixture 契约测试;`--score-version` 双口径;校准测试(真实站点 fixture,v1→v2 跌幅≤15 除非有解释);**State of GEO 式基准可由 seo-monitor.yml 的 monitor.db 匿名聚合**,报告照抄其偏差自白("自选样本,方向性信号")

### E9. AI 视图层(Scrunch AXP 等价物)
对重点页产出去 chrome 语义 HTML/Markdown 进 ai-views/(人审后部署=stage);block 级 before/after diff;**Scrunch 官方实测 123,916→1,355 tokens(98.9% 缩减)**;其博客明确"Markdown endpoints/llms.txt 最可能是浪费"——与我们 geo-evidence 保守口径一致,保持"人审后部署"边界

## 来源(深读对象)

claude-seo(18,626★,clone 深读全部 26 skill/60 脚本/tests)· geo-optimizer-skill(1,026★,源码 fixer.py/config.py/mcp)· seranking/seo-skills(161★)· geo-aeo-tracker(285★,sovereign-dashboard 2296 行)· oneglanse(207★,441 行打分 prompt)· open-seo-mcp-skills(4,665★,8 skill 全读)· Lumar/Ryte(help 全文档)· Semrush(kb/1601·542·114·652·1493·1607)· Ahrefs(help 1424673·1420169·1409408·Brand Radar 15501968·16755865)· Moz(On-Page Grader/Spam Score 27 信号)· SF(320 issue 矩阵解析)+Sitebulb(hints 结构)· Surfer(docs+百万 SERP 研究)/Clearscope/MarketMuse(公式全公开)· Profound(citation decay 88.3 万页研究+Context Manager)/Scrunch(developers API+Signals)/Goodie(36×8 audit)· Peec/Athena(Oracle)/Otterly(fanout·Agent Analytics·llms.txt 90 天实验)/Rankscale(facts·page audit)· seoClarity(六步 FAQ)/BrightEdge/Conductor(告警 7 类)/Botify(Action Item Reference)· serpbear/siteone-crawler/unlighthouse/lighthouse-ci-action(源码)。全部 URL 见各 agent 报告原文(会话存档)。
