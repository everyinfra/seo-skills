# 发布前规则清单:{页面标题 / URL}

_For: {作者 / 审核人} · Date: {YYYY-MM-DD} · Market: {市场/语言} · 页面类型: {信息页|比较页|How-to|Local|YMYL} · 机检脚本已跑: 是/否_

> 用途:发布前最后一道闸(本套件口径,不是搜索引擎的规则)。写完≠可发——逐条打勾,机检脚本全绿 + 人工条目过,才进发布队列。条目格式:`N. 检查什么 [机检|人工|机检+人工] — 怎么查:… 通过:… 失败:…`。
> 阈值来源分三类:**Google 官方说法**(附链接)、**本套件提示阈值**(可调,不是搜索引擎规则)、**工具约定**。长度类阈值全部是第二类:Google 对 title 和 description 没有字符上限,只按设备宽度截断([title](https://developers.google.com/search/docs/appearance/title-link)、[snippet](https://developers.google.com/search/docs/appearance/snippet),核对 2026-10-21)。
> 机检脚本与命令行(在 skill 根目录执行;先跑机检,人工只判机器判不了的)。`site_audit.py`、`schema_lint.py` 要能从公网访问的 URL(预览站点也要公网可达;私网地址会被拒);草稿文件用 `market_lint.py` 和 `content_score.py`:

| 覆盖条目 | 脚本 | 命令行 |
|---|---|---|
| 1/3/4/5/7/8/9/20/22/23/27/32 | site_audit.py | `python3 scripts/site_audit.py URL --market XX --json`(stdout 只有一个 JSON 对象;顶层 `market`、`limits`,每页 `verdict`、`findings[]`、`meta`、`ai_search_health`) |
| 1/2/3/12/14/21/24/26 | market_lint.py | `python3 scripts/market_lint.py --market XX --url URL --report`(线上页)或 `python3 scripts/market_lint.py --market XX 稿件.html`(草稿);超市场长度记 CRITICAL、退出码 1 |
| 21/23(JSON-LD 规则层) | schema_lint.py | `python3 scripts/schema_lint.py URL` |
| 5(og:image 绝对 URL) | head_check.py | `python3 scripts/head_check.py URL`,或 `python3 scripts/head_check.py -`(stdin 喂渲染后 HTML) |
| 27(llms.txt) | llmstxt.py | `python3 scripts/llmstxt.py check https://站点`;`python3 scripts/llmstxt.py validate FILE` |
| 6/11/13/17/19/25 | content_score.py | `python3 scripts/content_score.py --draft 稿件.md --competitors c1.md,c2.md,c3.md --keyword 主词 --facts 事实.md --json`(竞品少于 3 个来源拒评,退出码 2,这几条转人工) |
| 33 的句子写法 | ste_lint.py | `python3 scripts/ste_lint.py 稿件.md --fail-on fail` |

> 人工条目判断指引:逐条问"一个不信你的人能否复查"——数字能点开来源、资历在页面上看得到、权威外链点得开且不是竞品。当场判不了的写"待核"并阻塞发布,不得默认通过。
> 与 market_lint.py 的分工:market_lint 管市场特检(语言/敬语/格式/市场长度单位),本清单管通用发布闸;口径重叠处(如 title/desc 长度)以 market_lint 市场单位为准,两者都过才发。

## The answer

{一句话结论:33 条中机检 {N} 条 / 机检+人工 {K} 条 / 人工 {M} 条;本次不通过 {X} 条(条目号 {..},集中在 {组名});按尾部门槛处置——0 条发布 / 1-2 条修复后发布 / 3 条以上回炉。}

## A. meta 组(1-6)

1. **Title 在市场长度内且含主词** [机检+人工] — 怎么查:读 `site_audit.py --json` 的 `meta.title_len` 与顶层 `limits.title`(en 20–60 字符;zh、ko 30 全角;ja 32 全角;de 65;ru 55;th 按字素,值以 `limits` 为准);`market_lint.py` 同判。通过:`title_len` 在 `limits.title` 区间内,主词原文在场。失败:改写进区间,主词进 title,别堆变体。超长只说明可能被截断,不是排名规则:改写前先看截断位之后是否还有关键词。
2. **主词位置靠前** [机检] — 怎么查:`market_lint.py` v3「标题关键词位次」(脚本取正文高频词作主词代理;主词与高频词不同时人工核)。通过:该词落在 title 前 30 字符内(vi 市场 t0mmy 口径,本套件取作通用提示)。失败:重排 title 把主词前移,品牌名后置。
3. **Description 在市场长度内、写本页独有信息** [机检+人工] — 怎么查:`meta.desc_len` 与 `limits.description`(en 77–155 字符;下限是上限的一半,本套件口径);缺失在脚本里记 WARN。通过:在区间内,且含一个本页独有的具体事实(数字、规格、适用对象)。失败:补齐或删减,用事实句替代广告句。Google 说它主要从正文生成摘要,description 只在更准确时才被采用,所以首段比 description 更关键。
4. **Canonical 自指绝对 URL** [机检] — 怎么查:`site_audit.py` 的 `canonical` 类发现。通过:无发现(canonical 指向本页绝对 URL)。失败:缺失(WARN)、相对 URL(WARN,Google 支持但建议改绝对)、指向外域(INFO,跨域联合发布须显式记录让渡决策)。
5. **og 三件套齐全、og:image 为绝对 URL** [机检] — 怎么查:`site_audit.py` 的 `og` 类发现;`head_check.py URL`。通过:`og:title`、`og:description`、`og:image` 都在,`og:image` 以 http(s) 开头。失败:补齐缺失项,换绝对地址。
6. **Title 与 H1 互补不重复** [机检+人工] — 怎么查:`content_score.py` 的 `title_h1` 维度只判主词或变体是否在 title/H1 里;互补与否人工读两行文字。通过:主词在场,且 H1 与 title 不是同一句话的复制。失败:改写其一,让另一组承接变体。

## B. 结构组(7-12)

7. **有且只有一个最醒目的主标题(单 H1)** [机检] — 怎么查:`site_audit.py` 的 `h1` 类发现(`meta.h1` 数量)。通过:恰 1 个 H1 且含主词。失败:无 H1 或多个 H1(都是 WARN)。注意:Google 不要求单 H1,标题的数量和顺序对搜索没有影响([SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide));这条是读者与读屏器口径。
8. **H2≥2,且至少 1 个含买家原词的变体** [机检+人工] — 怎么查:`site_audit.py` 的 `headings` 类发现(H2 少于 2 个记 INFO);变体命中:把 H2 逐行放进 words.txt,`cat words.txt | python3 scripts/keyword_variants.py --json` 看哪些词归同一组,再人工比对。通过:无 H2 数量发现,且至少 1 个 H2 含主词变体。失败:补 H2 或把变体写进现有 H2。
9. **标题层级不跳级** [机检] — 怎么查:`site_audit.py` 的 `headings` 类「跳级」发现。通过:无跳级 WARN。失败:把跳级标题改成相邻层级。这是可读性和无障碍口径,Google 说标题顺序对搜索没有影响。
10. **段落不过长** [人工] — 怎么查:拉丁文 `awk 'BEGIN{RS=""} {n=split($0,w," "); if(n>150) print "段"NR": "n"词"}' 稿件.md`;CJK 用 `cat 稿件.txt | python3 scripts/text_metrics.py --market zh` 看句长节奏后目测段落。通过:每段 ≤150 词(CJK ≤250 字,本套件提示阈值)。失败:切分段落或转列表。
11. **首段三查** [机检] — 怎么查:`content_score.py` 的 `upfront_intent` 维度(三查:首句点名主题;前 100 词含数字或具体事实;先答案后展开)。通过:三查都过。失败:重写首段,结论句提到第一句。这是读者口径;Google 说不需要为 AI 功能专门改写([AI 功能](https://developers.google.com/search/docs/appearance/ai-features))。
12. **有一组真问答** [人工,market_lint 问句密度仅供参考] — 怎么查:读页面,问题来自 PAA、评论或工单原话,答案可单独读懂。通过:页面可见 ≥1 组真问答(答 ≤3 句)。失败:从 PAA/评论/工单补 1 组。FAQ 富结果自 2026-05-07 起不再展示([更新记录](https://developers.google.com/search/updates#faq-deprecation)),不为展示位新增问答类标记。

## C. 内容组(13-21)

13. **术语覆盖达目标分** [机检] — 怎么查:`content_score.py` 总分对比目标行(目标 = min(max(竞品均值+15, 70), 85),本套件口径)。通过:总分 ≥ 目标。失败:按术语表补 importance≥8 的缺口词,各提及 1-2 次(脚本提及封顶 2 次计分)。竞品少于 3 个来源不评分,本条转人工。
14. **每个数字有来源** [机检+人工] — 怎么查:`market_lint.py` 的「有源数字密度」;再抽 5 个数字点开来源读原句。通过:数字 ≥5 处时同句来源线索 ≥30%(脚本判据),且抽查的数字都能在来源页读到。失败:补来源句或删该数字,禁编造。
15. **作者署名与资历** [人工] — 怎么查:读页面作者行与作者页。通过:真实作者名 + 一行资历(职称/从业年限/认证),YMYL 页必须。失败:补署名与资历,机构页补审阅人。依据:Google「Who」自查——署名能否链到作者背景([有用内容指南](https://developers.google.com/search/docs/fundamentals/creating-helpful-content))。
16. **更新日期可见且真实** [人工] — 怎么查:读页面可见日期,对比 JSON-LD 的 `datePublished`/`dateModified` 与实际改动记录。通过:可见日期带「发布/更新」标签,与结构化数据一致,时间与时区尽量给全([Google 日期指南](https://developers.google.com/search/docs/appearance/publication-dates));只在内容实质变化时才改日期。失败:补日期或对齐;Google 的自查问题明确问「是否改页面日期装作新鲜」。
17. **上下文内链 ≥3** [机检+人工] — 怎么查:`rg -o '\]\((/|\.\./|https?://你的域名)[^)]*\)' 稿件.md | wc -l`;`content_score.py` 的 `internal_links` 维度(相对链接 ≥2 满分)。`site_audit.py` 不数内链条数。通过:正文上下文内链 ≥3(本套件阈值),锚文本描述性。失败:从相关页补内链,锚文本写目标页主题。
18. **外链指向一手来源、非竞品** [人工] — 怎么查:逐条点开外链。通过:指向官方、论文、标准等一手源,且能打开,不是直接竞品。失败:换成一手源,删竞品链接。
19. **术语加粗克制** [机检] — 怎么查:`content_score.py` 的 `bolded` 维度。通过:术语表内术语至少 2 处加粗(脚本满分条件),不整句整段加粗。失败:加粗首现术语,删零散加粗。弱信号,本套件口径。
20. **图片 alt 覆盖** [机检+人工] — 怎么查:`site_audit.py` 的 `images` 类发现(alt 缺失超过 20% 才记 WARN);缺失张数用 `curl -s URL | rg -o '<img[^>]*>' | rg -v 'alt="[^"]+"' | wc -l`。通过:每张有意义的图都有描述性 alt。失败:逐张补(≤100 字符为本套件提示阈值)。脚本只在缺失 >20% 时报,本清单要求补齐。
21. **无占位符残留** [机检+人工] — 怎么查:`schema_lint.py` 的占位符黑名单(JSON-LD 内);全文 `rg -n 'TODO|lorem|example\.com|\[占位|\{\{|\[要追加' 稿件.md`。通过:零命中。失败:替换为真值,无真值先不发。

## D. AI 可引性组(22-33)

22. **首块直答(BLUF)** [机检] — 怎么查:`site_audit.py` 的 `ai_search_health.checks` 里 `bluf` 项。通过:`pass` 为真(score ≥0.5;首块=前 max(20% 篇幅, 400) 字符,三项里满足两项:直答短语、列表 >3、首块 >100 字)。失败:首屏加「要点」直答块或列表。公式取自开源 geo-aeo-tracker 的做法,是本套件工具约定。
23. **schema 与可见内容一致** [机检+人工] — 怎么查:`site_audit.py` 的 `schema` 类发现与 `meta.jsonld`;`schema_lint.py URL`。通过:有需要的 JSON-LD,只标记页面上真实存在的内容([通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)),`schema_lint.py` 无 WARN。失败:删除不可见内容的标记,修悬空引用与空答案。「只用 1 种类型」是 `content_score.py` 的评分口径,不是 Google 规则。
24. **语气以事实为主** [机检+人工] — 怎么查:`market_lint.py` 的「营销词密度」与「句长 CV」。通过:营销词 ≤3/页(`markets.json` 词表)、句长 CV ≥0.25(脚本的「AI 均匀签名」阈值,本套件口径),通读无「最好/第一/必买」式堆砌。失败:营销句换事实句,删最高级与感叹号。理由是可信度与可核对,不是 AI 引用:Semrush 2026-01 的研究里「非促销语气」与被引呈负相关(被引页反而更偏商业语气),Semrush 自己的解释是专业撰写的文章常带商业语气,不能据此推出模型偏爱促销([Semrush](https://www.semrush.com/blog/content-optimization-ai-search-study/),核对 2026-10-21)。
25. **事实清单覆盖** [机检] — 怎么查:`content_score.py --facts 事实.md` 的 `facts_coverage`(D/K 分报)。通过:覆盖达到简报里的 {{coverage_target}}%。失败:补高频缺口事实各 1 句并标注来源。
26. **robots meta 无 AI 退出指令** [机检] — 怎么查:`market_lint.py` v3「页面级 noai/noimageai/nosnippet」检查。通过:无 `noai`、`noimageai`、`nosnippet`、`max-snippet:0`(ko 的 nosourceinfo 走市场特检)。失败:删除,或显式记录决策并移出本流程单独管理。`noai`/`noimageai` 不在 Google 的 robots meta 规范里(Google 不识别,[规范](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag),核对 2026-10-21),其他爬虫是否尊重各看其文档;`nosnippet`、`max-snippet` 会限制 Google AI 概览与 AI 模式使用摘要。
27. **llms.txt(仅文档站或面向编码 agent 的站点检查)** [机检] — 怎么查:`llmstxt.py check https://站点`;有文件时 `llmstxt.py validate FILE`。通过:没有文件,或文件结构有效(H1 + 链接)。失败:文件存在但无效或指向已删页。Google Search 不使用 llms.txt([Google 更新记录 2026-06-15](https://developers.google.com/search/updates)),不要把它写进 AI 引用收益;要生成骨架用 `llmstxt.py generate --sitemap URL`,人工复核后再部署。
28. **内联具名引用** [人工] — 怎么查:逐个非显然主张看有没有「机构 + 日期」式引用,引语格式 [姓名]([职务],[机构])在 [日期] 的 [出处] 指出,点开原始出处核对。通过:每个非显然主张配 1 条可点开的具名引用。失败:补引用,或把该主张降级为带源事实句,禁编造引语。这是写法要求,不是收益承诺:GEO 论文报告的 30–40% 位置加权词数提升只在固定上下文、单一模型的设置里出现,C-SEO Bench 在更广设置里没有重现([geo-evidence.md](../../references/content/geo-evidence.md) 第三节)。第 18 条管外链选源,本条管引用形态。
29. **统计数字带来源与年份** [人工;market_lint 有源数字密度辅助] — 怎么查:每个主张簇(支撑同一结论的断言组)找 ≥1 个「数值 + 来源 + 年份」。通过:出处同句或紧邻,测量值与估算值分标,数字四件套(来源、时间、样本、方法)齐全,缺项的降级为估算并标注。失败:补带源数字或删该数字,禁编造。第 14 条管关键数字逐条可点开,本条管每簇密度与格式。
30. **信息增益:净新观点 ≥5(起步阈值)** [人工] — 怎么查:对照 top 竞品文本,用 `content_score.py` 的缺失术语清单做补集:竞品全有而草稿独缺是共识缺口,草稿有而竞品全无是净新候选,再人工确认不是注水。通过:有 ≥5 条断言型观点(有主体 + 可验证锚点:数字、日期、引语、可复算方法)。失败:回炉补独家层;补不出净新观点的选题放弃发布。5 条是本套件起步阈值,尚未在站点数据上校准([deep-research-protocol.md](../../references/content/deep-research-protocol.md))。
31. **反例与不确定性标注** [人工] — 怎么查:数断言与反例块。通过:每 3-5 个断言配 ≥1 条「例外:{什么条件下不成立},证据:{出处}」,核心结论逐条标高/中/低置信度 + 一句依据;找不到反例的写「未找到反例(检索了 {查询×N},截至 {日期})」。失败:补反例块与置信度标尺,删绝对化表述。
32. **答案前置与可见时间戳** [机检+人工] — 怎么查:`site_audit.py` 的 `bluf` 项与 `ai_search_health.last_modified_days`(Last-Modified 头);人读每节开头。通过:页面可见发布/更新日期,`Last-Modified` 有值(超过 183 天记 INFO,是工具约定),每节开头 60 词内直接回答本节问题(本套件口径)。失败:补可见日期并与实际改动对齐,节首加直答句。第 16 条管日期可见与真实,第 22 条管首块,本条扩到节级。
33. **AI 参与等级与人审记录** [人工] — 怎么查:读内容台账;按 [ai-use-policy.md](ai-use-policy.md) 四象限定级,句子写法跑 `ste_lint.py`。通过:每篇有等级与处置,可辅助级附人审记录,须披露级三件套完整。失败:禁用级任务回人,须披露级补标注。机检脚本不判 AI 参与等级,本条永远人工。

## 门槛与处置

- **0 条不通过** → 发布。
- **1-2 条不通过** → 修复后发布;修复项按所属条目复跑对应机检脚本或人工复查一次。
- **3 条及以上不通过** → 回炉:回 content-brief 重写,不算"改版"。任一组大面积失守(如 meta 组 6 条挂 4 条)即使总数<3 也建议回炉。
- 机检脚本退出码非 0 → 对应条目直接计不通过,先清脚本项再数人工条目。
- 双闸都过才发:market_lint 无 CRITICAL(市场特检)+ 本清单过门槛(通用闸),缺一不可。
- 门槛的 0 / 1-2 / 3 档位是本套件口径。

## What could change this conclusion

- 机检通过≠内容合格:脚本判在场性与结构,不判真假与是否值得发——13-19 条的人工部分才是质量闸,别用脚本绿代替通读。
- 没有竞品语料时 `content_score.py` 拒评,6/11/13/17/19/25 这几条转人工,条数与门槛不变,只换判定来源。
- 长度阈值是字符代理,真实截断按设备宽度;市场单位见 `scripts/markets.json` 与 [title-formulas.md](../../references/content/title-formulas.md) 「市场差异」节,冲突时以市场口径为准。
- 阈值随证据更新:若某条在实际发布中从未拦下问题,下次修订降级或删除;条目来自本套件的简化发布闸,没有对应外部清单。
- 引擎规则会变:Google 的 FAQ 富结果、日期指南、AI 功能说明都在更新,条目 12、16、26、27 每季度对照一次官方文档。

## Method Notes

- 执行顺序:先跑头部表格的机检命令(全部退出码 0)→ 再逐条人工 → 数不通过条数按门槛处置;YMYL/Local 页在四组之外另跑对应市场 special_checks(`market_lint.py --report` 三态清单)。
- 证据纪律:每个"不通过"附一行可复查证据(脚本输出行/渲染后 DOM 摘录/来源 URL);数字缺失写 [要追加: 数据源],禁编造。
- 判定来源标注:[机检] = 脚本已判(命令见头部表格);[人工] = 机器判不了(真实性/权威性/语气);[机检+人工] = 脚本给出在场性,人工判内容。
- 维度与阈值出处:`content_score.py` 的维度与权重在脚本头注;BLUF 公式见 `site_audit.py` 的 `bluf_score`;FAQ 富结果状态见 [deprecated-signals.md](../../references/technical/deprecated-signals.md);28-32 条(引用纪律)口径见 [deep-research-protocol.md](../../references/content/deep-research-protocol.md);清单与 market_lint.py 的分工见头部引用块。
