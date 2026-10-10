# 引用缺口七叉决策(演示数据):14 个合成 prompt 覆盖全部 7 个分支(每分支×2)——最高优先"竞品占领答案空间"2 词;先 citation_gaps 找域(g2.com 被 12 次引用、5 个同场竞品),再 cite_domain 评级 90.0/A

_For: SEO/Growth 负责 AI 可见性 · 面板: panel.json(brand=Nimbus Analytics,domain=nimbus.example,14 prompts × 2 引擎 × 3 天 = 84 cell) · 工具链: citation_panel.py(init/record)→ citation_gaps.py(--owned-relevance/--domain-class)→ cite_domain.py · 窗口(虚构): 2026-10-09 ~ 2026-10-11 · 引擎: chatgpt, perplexity_

> **演示数据声明**:本目录全部数据为**手工构造的合成数据,只演示交付物形态,非真实测量**——品牌、84 个 cell 的五状态、被引 URL、owned-relevance、来源分类覆盖、g2.com 评级输入的每一个数字都是虚构的。被引域名选用真实知名域(wikipedia/reddit/techcrunch 等)是为了让五分类启发式按真实判定路径走,不构成对这些站点的任何判断。任何数字不可对外引用。
> **快照免责声明**:即便是真实面板,报告也是采样窗口的单点快照,AI 引擎回答会漂移;示例展示的是交付物形态而非目标站现状。

## The answer(先读这段)

合成面板 84 cell(18 个 qualifying 缺口 cell,evidence/01)跑 citation_gaps:gapLabel 七叉**全部 7 个分支各有 2 个 prompt 命中**(设计目标达成,evidence/01 gapLabel 表)——最高优先是 **"Competitors own this AI answer space"**("top product analytics platforms" 竞品独现 6/6、"cheap analytics alternatives list" 4/6):品牌零提及且竞品稳定占位,动作=对标竞品产出对比页。缺口域侧:**g2.com 以 12 次引用、5 个同场竞品居首**(High),来源五分类 override 为 UGC——对它做外联前先 cite_domain 评级:**90.0 → band A**(E1/E2 两项 Partial,VETO 无,evidence/02)。顺序纪律:**先 gaps 找域、后 cite_domain 评级,不可倒**——先评级后找域是浪费。

## Key numbers(编号回溯)

| 数字 | 值 | 出处 |
|---|---|---|
| 面板规模 | runs=6 / cells=84 / qualifying=18(cited_brand/failed/no_answer 不入) | evidence/01 stats |
| gapLabel 覆盖 | 7 分支 × 各 2 prompt = 14/14 | evidence/01 gapLabel 表 |
| 缺口 URL / 域名 | 11 URL / 8 域名;URL 级高优先(竞品同场)8 | evidence/01 stats |
| 自有域排除 | nimbus.example + nimbus-cdn.example;qualifying cell 内自有域被引 1 次不计 | evidence/01 |
| 头号缺口域 | g2.com:12 次引用 / 3 页 / 同场竞品 5(devops.to,hubspot.com,rival.example,techcrunch.com,wikipedia.org) | evidence/01 域名分组表 |
| 来源五分类 | UGC 2 / Editorial 2 / Corporate 2 / Reference 2(override 2 个:g2.com→UGC,devops.to→Editorial) | evidence/01 JSON |
| cite_domain 评级 | 总分 90.0 → band A;C/I/T 三组 100,E 组 50(E1 被引查询 33、E2 评论 8 均 Partial);VETO 无 | evidence/02 |

## 七叉决策树:每种缺口该干什么(全分支覆盖,每分支 2 个演示 prompt)

判定顺序**固定自上而下,首个命中即停**(evidence/01 gapLabel 表;计数=有效/提及/被引/竞品独现):

| # | 分支(判据) | 本例 prompt(计数) | 该干什么 |
|---|---|---|---|
| 0 | No completed AI answers(0 条有效回答) | ai agent security checklist(0/0/0/0)· best webhook monitoring tools(0/0/0/0) | **先修采集再谈缺口**:重跑/换引擎/查配额——数据不足时任何内容结论都是空的 |
| 1 | Competitors own this AI answer space(提及=0 且竞品独现>0;**最高优先**) | top product analytics platforms(6/0/0/6)· cheap analytics alternatives list(6/0/0/4) | **对标竞品产出内容/对比页**,争取进入该词的答案——这是在丢阵地,不是没吃到 |
| 2 | Target absent from AI answers(提及=0 且无竞品独现) | how to build a data warehouse(6/0/0/0)· etl vs elt explained(3/0/0/0) | **补该主题的 grounding 页面与可引用事实**——品类词缺席=没有可被引用的资产 |
| 3 | Owned content is not reflected(owned≥0.6 且提及率<0.5) | cohort retention analysis guide(6/2/0/0,rate 0.33,owned 0.8)· product analytics benchmarks report(6/2/0/0,rate 0.33,owned 0.65) | **检查页面可引用性**(结构化事实/数据密度)——内容存在但引擎不采信,改格式而非补量 |
| 4 | Mentioned without official citation(提及>0 且被引=0) | open source product analytics options(6/6/0/0,owned 0.9)· self-hosted analytics comparison(6/4/0/0,owned 0.75) | **强化可引用资产**(数据页/研究/文档)——被提≠被引,缺的是"值得挂链接的硬资产" |
| 5 | Competitors still appear without target(偶发竞品独现) | best crm for startups(6/4/4/2)· crm implementation mistakes(6/5/5/1) | **巩固既有覆盖,补竞品占位的子话题**——基本盘在,防蚕食 |
| 6 | Covered in this audit(其余) | product analytics fundamentals tutorial(6/6/6/0)· funnel analysis best practices(6/6/6/0) | **保持监测,暂不动**——把外联预算让给上面六类 |

### 读树的三条纪律(本演示特意埋的对照)

- **分支 0 优先于一切**:"etl vs elt explained" 3 个 no_answer 把有效分母压到 3,但分支判定不受影响(3/0/0/0 仍落分支 2)——先看有没有效回答,再看缺口类型。
- **分支 3 需要 --owned-relevance 输入**:owned 值是站点证据对词相关度(niubigeo N7 词筛产出),panel.json 无此字段;不提供时分支 3 不可判、如实落入后续分支(本例提供了 4 个 prompt 的值)。对照:"open source…"(owned 0.9 但提及率 1.0)与"self-hosted…"(owned 0.75 但提及率 0.67)都因**提及率 ≥0.5 不满足分支 3 的严格 <**,落分支 4——owned 高≠自动触发。
- **分支 1 与 5 的差别是稳定性**:分支 1 = 品牌零提及下的系统性占位(竞品独现 4-6/6);分支 5 = 品牌已被引(4-5/6)背景下的偶发独现(1-2 cell)——前者是攻坚战,后者是防御战。

## 缺口域怎么排外联优先级(evidence/01 域名分组/五分类表)

- **High(竞品同场)= 直接竞争窗口**:g2.com(12)、devops.to(4)、rival.example(4)、wikipedia.org(3)、hubspot.com(1)、techcrunch.com(1)——外联提示口径:"竞品 {A,B} 在 {domain} 被引用——考虑贡献内容或争取列表位直接竞争"。
- **Standard(无竞品同场)= 蓝海收录**:reddit.com(3)、kpiwiki.io(1)——"获得收录可提升 AI 可见性"。
- **五分类给动作定渠道**:override(g2.com→UGC:社区运营;devops.to→Editorial:PR outreach)> 自有域 > 启发式[推断](known:wikipedia.org→Reference 更正词条;known:reddit.com→UGC;token:wiki→kpiwiki.io 归 Reference;default:corporate→rival.example/hubspot.com 归合作目录)。判定依据逐域暴露在表里,不黑箱。

## cite_domain 评级:外联投入前的最后一道闸(evidence/02)

对头号缺口域 g2.com 喂入手工采集形态的 answers-g2-com.json(数字全虚构):**总分 90.0 → band A(优)**——C 引用 100(950 引用域、DR50+ 份额 26.3%、出链 620、增速平滑、2 引擎 ≥10 查询、编辑链 68%)/ I 身份 100(品牌词行 7/8)/ T 信任 100(无 VETO)/ E 显赫 50(被引查询 33、评论量 8 均 Partial)。**证据核验清单**随评级输出:engines_cited 只按 provider_citation 口径计数,provider_search_result 与 answer_text_url 不充数(5 家 Provider 的原始 JSON 字段路径见 evidence/02 尾部)。结论形态:band A + High 同场 → 值得投入 UGC 渠道(评论/列表位),评级进 citation-outreach-brief 简报。

## What could change this conclusion

- **演示数据无结论可翻**;真实使用时的首要变数:qualifying cell 的口径依赖 cited_urls 记录完整——record 漏记 URL 会把缺口 cell 误判为"无引用"。
- **两工具间的形态约定**:本例 panel 用 `init --prompts`(字符串形态)构建;citation_gaps 的 gapLabel 聚合以 prompt 文本为键,`init --prompts-file` 的对象形态(prompts 为对象的列表)无法按键聚合——真实工作流若用对象形态,需先转换。
- 竞品口径是[推断]代理(同 cell 非自有被引域),panel 无显式竞品名单;rival.example 之外的"同场域"(wikipedia 等中性域)也被计入同场竞品,High 面积会比真实竞品口径宽。
- 分支 3 的 owned-relevance 是词筛产出的人工输入,0-1 主观刻度;同一面板换一套 owned 值,分支 3/4 的分界会移动。
- 14 prompts 满足 ≥10 的采样下限,但 3 天窗口仍不足以做 diff/decay(观察窗 ≥28 天、峰值窗采样 ≥5 的资格闸门不满足)。

## Methodology(合成数据构造 + 精确命令行;均在 skill 根目录 skills/seo-suite/ 执行,输出目录为本示例目录;构造法参照 [citation-panel-demo-20261010](../citation-panel-demo-20261010/REPORT.md))

1. 手工构造 14 prompts(七分支 × 各 2;文本无逗号)写入 `inputs/prompts.txt`(单列);按分支设计生成 6 个 run CSV `inputs/run-{chatgpt,perplexity}-202610{09,10,11}.csv`(列: prompt,mentioned,cited,cited_urls,state,rank;五状态在 84 cell 中各有覆盖,缺口 cell 的 cited_urls 埋入 8 个外域 + 自有域 1 次)。
2. `python3 scripts/citation_panel.py init --brand "Nimbus Analytics" --aliases Nimbus --domain nimbus.example --competitors rival.example --engines chatgpt,perplexity --prompts examples/citation-decision-demo-20261011/inputs/prompts.txt --panel examples/citation-decision-demo-20261011/panel.json`
3. 6 次 record(run 文件自动落 runs/):`python3 scripts/citation_panel.py record --engine chatgpt --file examples/citation-decision-demo-20261011/inputs/run-chatgpt-20261009.csv --date 2026-10-09 --panel examples/citation-decision-demo-20261011/panel.json`(其余 5 条同型,引擎/日期/文件名对应替换)
4. `python3 scripts/citation_gaps.py --panel examples/citation-decision-demo-20261011/panel.json --brand-domains nimbus-cdn.example --owned-relevance examples/citation-decision-demo-20261011/inputs/owned-relevance.json --domain-class examples/citation-decision-demo-20261011/inputs/domain-class.json --csv examples/citation-decision-demo-20261011/evidence/01-citation-gaps.csv --json examples/citation-decision-demo-20261011/evidence/01-citation-gaps.json > examples/citation-decision-demo-20261011/evidence/01-citation-gaps.md`
5. 手工构造 `inputs/answers-g2-com.json`(cite_domain 输入模板形态,数字全虚构)后:`python3 scripts/cite_domain.py --input examples/citation-decision-demo-20261011/inputs/answers-g2-com.json --json examples/citation-decision-demo-20261011/evidence/02-cite-domain.json > examples/citation-decision-demo-20261011/evidence/02-cite-domain.md`

## Method Notes

- 三层结构:本 REPORT(叙事层)→ evidence/01(md/csv/json 三形态)+ evidence/02(md/json)(工具原样输出层)→ panel.json + runs/*.json + inputs/*(原始数据层);七叉表每行的计数/动作与 evidence/01 逐字对应。
- 口径:qualifying cell=有 cited_urls 且品牌未被引;gapLabel 七叉=niubigeo keyword-metrics-engine 直译(分支 4 需 owned-relevance 外部输入,降级如实注明);来源五分类=Peec Source 五分类(override > 自有域 > 启发式[推断]);CITE 评级=Pass10/Partial5/Fail0,unknown 不计组内均值,VETO 触发封顶 59 或 BLOCK。
- 禁编造:本例数据为**显式声明的合成数据**(演示目录的合法形态);真实运行时禁用合成数据,采样失败如实记 failed,评级输入按证据核验清单人工采集。
