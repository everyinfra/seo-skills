# 发布前规则清单:{页面标题 / URL}

_For: {作者 / 审核人} · Date: {YYYY-MM-DD} · Market: {市场/语言} · 页面类型: {信息页|比较页|How-to|Local|YMYL} · 机检脚本已跑: 是/否_

> 用途:发布前最后一道闸。写完≠可发——逐条打勾,机检脚本全绿 + 人工条目过,才进发布队列。条目格式:`N. 条件 [机检|人工] — 通过标准;不通过时怎么办`。
> 机检条目对应脚本与命令行(在 skill 根目录执行;先跑机检,人工只判机器判不了的):

| 覆盖条目 | 脚本 | 命令行 |
|---|---|---|
| 1/3/4/5/7/8/17/20/22/23/27 | site_audit.py | `python3 scripts/site_audit.py URL --market XX --json` |
| 2/3(市场单位)/12/14/24/26 | market_lint.py | `python3 scripts/market_lint.py --market XX --url URL --report` |
| 21/23(JSON-LD 规则层) | schema_lint.py | `python3 scripts/schema_lint.py URL` |
| 5(og:image 绝对 URL) | head_check.py | `python3 scripts/head_check.py -`(stdin 喂渲染后 HTML) |
| 27(文档站) | llmstxt.py | `python3 scripts/llmstxt.py check https://站点` |
| 6/11/13/19/25 | content_score.py | `content_score.py --draft 文件 --competitors c1.md,c2.md,c3.md --keyword 主词 --facts 事实.md`(维度规格 borrow-specs C1;竞品<3 个不同域名时拒评,这 5 条转人工) |

> 人工条目判断指引:逐条问"一个不信你的人能否复查"——数字能点开来源、资历在页面上看得到、权威外链点得开且不是竞品。当场判不了的写"待核"并阻塞发布,不得默认通过。
> 与 market_lint.py 的分工:market_lint 管市场特检(语言/敬语/格式/市场长度单位),本清单管通用发布闸;口径重叠处(如 title/desc 长度)以 market_lint 市场单位为准,两者都过才发。

## The answer

{一句话结论:27 条中机检 {N} 条 / 人工 {M} 条;本次不通过 {X} 条(条目号 {..},集中在 {组名});按尾部门槛处置——0 条发布 / 1-2 条修复后发布 / 3 条以上回炉。}

## A. meta 组(1-6)

1. **Title 长度 30-60 字符且含主词** [机检:site_audit] — 通过:拉丁口径 30-60 字符且主词原文在场(ja 全角/th 字素等市场单位以 market_lint 判定为准);不通过:改写进区间,主词进 title,别堆变体。
2. **主词位置尽量靠前** [机检:market_lint v3 标题关键词位次] — 通过:主词落在 title 前 30 字符内;不通过:重排 title 把主词前移,品牌名后置。
3. **Description 120-160 字符** [机检:site_audit + market_lint] — 通过:拉丁口径 120-160(市场单位以 market_lint 为准)且含主词+一个具体事实;不通过:补齐/删减到区间,用事实句替代广告句。
4. **Canonical 自指** [机检:site_audit] — 通过:canonical 指向本页绝对 URL;不通过:改为自指绝对 URL(跨域联合发布的让渡决策须显式记录)。
5. **og 三件套齐全** [机检:site_audit;og:image 绝对 URL 判据同 head_check] — 通过:og:title / og:description / og:image 三者在场且 og:image 为 https 绝对 URL;不通过:补齐缺失项,og:image 换绝对地址。
6. **Title 与 H1 互补不重复** [机检:content_score.py title_h1 维度] — 通过:H1 含主词且与 title 表述不同(两者覆盖不同词组);不通过:改写其一,让另一组承接变体。

## B. 结构组(7-12)

7. **单 H1** [机检:site_audit rendering 检查 H1==1] — 通过:渲染后 DOM 恰 1 个 H1 且含主词;不通过:合并或把多余 H1 降为 H2。
8. **H2≥2 且含主词变体** [机检:site_audit 判 H2≥2;变体命中人工比对 keyword_variants 分组] — 通过:≥2 个 H2 且至少 1 个含主词变体(keyword_variants.py 同组词);不通过:补 H2 或把变体写进现有 H2。
9. **标题层级不跳级** [人工] — 通过:H1→H2→H3 逐级出现,无 H2 直跳 H4;不通过:把跳级标题改成相邻层级。
10. **段落≤150 词** [人工] — 通过:任一段落≤150 词(CJK ≤250 字),长内容用列表/表格拆;不通过:切分段落或转列表。
11. **首段三查** [机检:content_score.py AI 轨 upfront_intent] — 通过:首句点名主题、首段含≥1 个事实锚点(数字/日期/实体)、先答案后展开,三者都在前 100 词内(38-40% 的 AI 引用来自前 100 词);不通过:重写首段,结论句提到第一句。
12. **FAQ≥1 组** [机检:market_lint 问句密度辅助,块本身人工] — 通过:页面可见≥1 组真问答(问真有人搜的,答≤3 句);不通过:从 PAA/评论补 1 组。FAQPage JSON-LD 不新增(2026-05 已退役,口径见 references/technical/deprecated-signals.md)。

## C. 内容组(13-21)

13. **术语覆盖达目标分** [机检:content_score.py term_coverage] — 通过:总分≥竞品均值+10~20(甜区 70-85 封顶 85;竞品<3 个不同域名不评分);不通过:按术语表补 importance≥8 的缺口词,各提及 1-2 次(提及封顶 2 次计分)。
14. **每个数字有来源** [机检:market_lint 有源数字密度辅助 + 人工逐条] — 通过:数字≥5 处时同句来源线索≥30%,且关键数字逐条有可点开的来源;不通过:补来源句或删该数字,禁编造。
15. **作者署名+资历** [人工] — 通过:真实作者名+一行资历(职称/从业年限/认证),YMYL 页必须;不通过:补署名与资历,机构页补审阅人。
16. **更新日期可见** [人工] — 通过:页面上可见"更新于 {日期}"且用市场规范格式(market_lint 日期格式检查同口径);不通过:补可见日期,并与内容实际改动对齐。
17. **内链≥3** [机检:site_audit links 计数;锚文本上下文人工] — 通过:正文上下文内链≥3 条且锚文本描述性;不通过:从相关页补 3 条上下文内链,锚文本写目标页主题。
18. **外链权威非竞争** [人工] — 通过:外链指向一手权威源(官方/论文/标准)且非直接竞品;不通过:换成一手源,竞品链接删除。
19. **加粗关键术语** [机检:content_score.py bolded 维度;弱正信号] — 通过:importance≥8 术语在首次定义处加粗,全文≤10 处;不通过:加粗首现术语,删零散加粗。
20. **图片 alt 覆盖** [机检:site_audit img_noalt] — 通过:alt 缺失数为 0;不通过:逐张补描述性 alt(≤100 字符)。
21. **无占位符残留** [机检:schema_lint JSON-LD 占位符黑名单 + 人工全文] — 通过:全文与 JSON-LD 无 TODO/[占位]/示例域名/lorem 类残留;不通过:替换为真值,无真值先不发。

## D. AI 可引性组(22-27)

22. **BLUF 密度≥0.5** [机检:site_audit ai_search_health bluf] — 通过:首块(前 max(20% 篇幅, 400) 字符)score≥0.5——直答短语/列表>3/首块>100 字三取二;不通过:首屏加"要点 / key takeaways"直答块或列表。
23. **schema 1 种与内容匹配** [机检:site_audit JSON-LD 计数 + schema_lint 规则;与内容匹配人工] — 通过:恰 1 种主类型 JSON-LD 且只标记页面上真实存在的内容,schema_lint 无 FAIL;不通过:删到 1 种匹配类型,修悬空引用与空答案。
24. **无促销堆砌语气** [机检:market_lint 营销词≤3 + 句长 CV 代理 + 人工通读] — 通过:营销词≤3/页、句长 CV≥0.25、通读无"最好/第一/必买"式堆砌(促销堆砌为负面信号,转化 −26.2%,KDD 口径);不通过:营销句换事实句,删最高级与感叹号。
25. **事实清单覆盖** [机检:content_score.py --facts] — 通过:top20 SERP+AI 回答的事实清单按 AI 频次加权覆盖到位(缺口仅剩低频事实);不通过:补高频缺口事实各 1 句并标注来源。
26. **robots meta 无 AI 退出指令** [机检:market_lint v3 AI 退出 meta] — 通过:无 noai/noimageai/nosnippet/max-snippet:0(ko 的 nosourceinfo 走市场特检);不通过:删退出指令——确要退出 AI 引用的页面须显式记录决策,并移出本清单流程单独管理。
27. **llms.txt(仅文档站检查)** [机检:site_audit llms.txt 存在性 / llmstxt check] — 通过:文档站 /llms.txt 存在、结构通过 llmstxt validate 且含本页;非文档站跳过本条;不通过:`llmstxt.py generate --sitemap` 生成或更新后人工复核再部署。

## 门槛与处置

- **0 条不通过** → 发布。
- **1-2 条不通过** → 修复后发布;修复项按所属条目复跑对应机检脚本或人工复查一次。
- **3 条及以上不通过** → 回炉:回 content-brief 重写,不算"改版"。任一组大面积失守(如 meta 组 6 条挂 4 条)即使总数<3 也建议回炉。
- 机检脚本退出码非 0 → 对应条目直接计不通过,先清脚本项再数人工条目。
- 双闸都过才发:market_lint 无 CRITICAL(市场特检)+ 本清单过门槛(通用闸),缺一不可。

## What could change this conclusion

- 机检通过≠内容合格:脚本判在场性与结构,不判真假与是否值得发——13-19 条的人工部分才是质量闸,别用脚本绿代替通读。
- content_score.py 落地后,6/11/13/19/25 五条从人工转机检,条数与门槛不变,只换判定来源。
- 30-60 / 120-160 是拉丁字符代理口径,真实截断以像素为准;市场单位与像素口径见 references/overview/multilingual-workflow.md,冲突时以市场口径为准。
- 阈值随证据更新:本清单是既有 60-65 条规则体系(Letterdrop 口径)的简化版,砍掉的是机器已判或低杠杆项;若某条在实际发布中从未拦下问题,下次修订降级或删除。

## Method Notes

- 执行顺序:先跑头部表格的机检命令(全部退出码 0)→ 再逐条人工 → 数不通过条数按门槛处置;YMYL/Local 页在四组之外另跑对应市场 special_checks(market_lint --report 三态清单)。
- 证据纪律:每个"不通过"附一行可复查证据(脚本输出行/渲染后 DOM 摘录/来源 URL);数字缺失写 [要追加: 数据源],禁编造。
- 判定来源标注:[机检:X] = 脚本 X 已判(命令见头部表格);[人工] = 机器判不了(真实性/权威性/语气),判断指引见头部引用块。
- 维度与阈值出处:references/research/borrow-specs.md C1(content_score 维度表/首段三查/甜区 70-85)、A4(BLUF 公式)、E5(FAQPage 退役);清单与 market_lint.py 的分工见头部引用块。
