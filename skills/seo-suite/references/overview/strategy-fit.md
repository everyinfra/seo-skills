# 策略适配层 strategy-fit:体检 × 站型 × 资源 → Top3 策略组合

> 建立 2026-10-12,落地 [pipeline-completeness.md](pipeline-completeness.md) R1-3。定位:审计链(site_crawl → site_audit → health_score → prioritize → envelope)的**下游决策层**——envelope 回答"哪里坏了",本文件回答"先做哪三件、为什么、多久见效、什么情况别做"。配套:站型判别用 [site-type-playbooks.md](site-type-playbooks.md) 各卡"识别信号"节;资源/风险/时间窗/目标四问见 [intake-checklists.md](intake-checklists.md) 通用节。

## 一、输入(三源,缺源降级、不缺答案)

| 输入 | 来源 | 关键字段 | 缺失时 |
|---|---|---|---|
| 审计封套 | `envelope.py` → audit-data.json | `summary{band,top_findings,quick_wins}`、`categories[]`(availability/indexability/uniqueness/discoverability/rankability/experience)、`action_plan.phases`(立即/短期/持续) | 未跑体检→先跑(SKILL.md 原则 0,先体检后内容);只有单页审计→信号标 `[est]` |
| 站型 | 八卡"识别信号"(site_crawl URL 型谱+schema 分布+页面构成) | 主卡+副卡(混合站) | 模糊→**列前二站型让用户确认**,不静默选一 |
| 资源字段 | intake 通用节"资源与约束四问" | 内容产能/开发资源/工具层级/外包预算;风险容忍三类;时间窗;量化目标 | 未答→资源可行性按 0.5 下限计,报告注明"资源未知按保守计" |

## 二、九条候选策略池

证据级别按 [geo-evidence-bank.md](../content/geo-evidence-bank.md) A-D 口径标注(2026-10-21 重核各条外部数字,已核的附链接,核不到的已删或降级);**收益区间是带证据级别的参照,不是承诺**——对客数字必须换成自家基线(GSC 实测+forecast `--actual` 校准)后再报。

**1 技术修复(先基座)**
- 匹配信号:`phases[立即]` 非空(任一 CRITICAL:不可达/noindex 误封/robots 误拒/canonical 断链);或 band=Weak。站型无关,一切策略的前置。
- 收益区间:无厂商案例数字可引(诚信口径);验证凭修复前后 `audit_compare.py` 复测+收录量回升,窗口 2-6 周。
- 反指标:无 CRITICAL 且 band≥Fair→降级为 `quick_wins` 清单,不占 Top3 席位;Core Update rollout 窗口内不动(intake 算法更新状态卡纪律)。

**2 内容刷新 refresh**
- 匹配信号:uniqueness 类 findings(duplicate_title/content_length 薄)+ GSC 衰退词(`gsc_mining --decay` 双期导出)+ 站型③⑥⑧内容面权重升;内容产能≥2 篇/月才可排期。
- 收益区间:恢复期 2-4 个月、恢复 60-80% 为**示意值非实测**(intake-checklists 内容衰减卡);观察窗 4-8 周([content-refresh-playbook.md](../content/content-refresh-playbook.md))。
- 反指标:URL 零外链零排名→rewrite/retire 而非 refresh;下跌源于技术问题→先策略 1;Core Update 窗口勿刷(归因污染)。

**3 pSEO 程序化页矩阵**
- 匹配信号:站型①②④⑦卡"pSEO 机会"节命中 + uniqueness 健康(无大面积近重复 findings)+ GSC 查询呈模式词群(vs/alternative/for/near/型号)+ 开发资源≥0.5 + pSEO 风险容忍≥中。
- 收益区间:Zapier 范式 5,000 工具→约 5 万页(**D 级厂商转述**,salt.agency);自家量级=可寻址组合×过闸率,自算不抄案例。
- 反指标:**content 质量差先修内容**——唯一度<40%/样板>60%/无真实数据源的组合不生成([programmatic-seo-gates.md](../technical/programmatic-seo-gates.md) 硬停线);风险容忍低→出局;未复核页 100+ 未审→WARNING 先行。

**4 多语言/多市场扩展**
- 匹配信号:GSC 国别流量分散(单一市场<80% 且他国有量)+ intake 目标市场清单 + hreflang 无 findings(有则先修)+ 有 transcreate 产能(非机翻)。
- 收益区间:Weglot 研究称有翻译版的网站在 AI Overviews 里的可见性最高高出 327%(**C 级:翻译服务商的赞助研究,样本是西班牙和墨西哥的 236 个西语站、130 万条引用,相关性非因果**,[Weglot](https://www.weglot.com/blog/multilingual-seo-ai-visibility)、[SEJ 赞助文章](https://www.searchenginejournal.com/translated-sites-boost-ai-visibility-weglot-spa/559900/));旧稿的"被引 3.83×"找不到出处,已删。Google 垃圾政策把用自动化(含翻译)批量生成对用户几乎没有价值的页面列入规模化内容滥用([垃圾政策](https://developers.google.com/search/docs/essentials/spam-policies#scaled-content))。
- 反指标:主市场流量在跌→先修本土;只有机翻产能→出局;市场决策先过 [multilingual-workflow.md](multilingual-workflow.md) 总表。

**5 GEO 可见性(AI 引用)**
- 匹配信号:`summary.ai_search_health` 低或缺失 + 站型⑤文档⑥工具⑧YMYL(AI 引用占比高的站型)+ citation_panel 基线已建(≥10 prompts)或用户目标即 AI 引用。
- 收益区间:GEO 论文摘要称最高可把生成引擎回答里的可见度提高约 40%([arXiv 2311.09735](https://arxiv.org/abs/2311.09735),**A 级带限定**:模拟引擎,非真实端到端流量);C-SEO Bench(NeurIPS 2025)报告会话式 SEO 总体几乎没有增益([arXiv 2506.11097](https://arxiv.org/abs/2506.11097))。两者**构成张力,两说并报**。Ramp 约 7× 是厂商案例(D 级,本次未核到原文),禁换算为客户预期。
- 反指标:站不可爬(AI 爬虫同样读不到)→回策略 1;llms.txt 非必做(Rankability 2026-09:前 1,000 个域名里 9.3% 有 llms.txt 或 llms-full.txt,[原文](https://www.rankability.com/blog/llms-txt-adoption/);Google 文档 2026-06-15 注明不需要、也不影响 Google 搜索的可见度或排名);无第一方数据(探针+GSC)不下结论。

**6 外链/数字 PR**
- 匹配信号:rankability findings + 引域画像弱(cite_domain 输入的 referring_domains 少/质量差)+ 有可链资产潜质(数据/工具/原创研究)+ 外包预算>0 或产能可支撑资产生产。
- 收益区间:引域↔排名为**共识级方向,无单条数字可承诺**;丢链要建找回流程(找回比新建便宜,本套件口径);旧稿的"丢链约 5%/月"和"一条 .edu/.gov 引用>百条目录"找不到出处,已删。
- 反指标:站本身不可链(内容薄无资产)→先做资产;购买外链默认禁(Google 垃圾政策把为排名买卖链接列为 link spam,[政策](https://developers.google.com/search/docs/essentials/spam-policies#link-spam);用户主动提出才按 site-networks 光谱评级);monitor 的引荐域月检(R2-4)未接上前不启动规模化外展。

**7 热点内容 trend**
- 匹配信号:站型③权重最高 + trend_scout 白名单门槛(HN+Reddit 相关≥15)+ 24-72h 时效窗内可产出(产能)。
- 收益区间:Kevin Indig 2026-01 的分析称,被 ChatGPT 引用的页面 70% 以上在 12 个月内更新过,建议 3 个月内更新([Growth Memo](https://www.growth-memo.com/p/state-of-ai-search-optimization-2026),B/C 级,旧稿的"3×"本次未核到);新闻源约占 AI 引用的 9%,且新闻引用集中在少数媒体([arXiv 2507.05301](https://arxiv.org/abs/2507.05301),单作者预印本)——普通站勿指望新闻面引用。
- 反指标:量产蹭热点属规模化内容滥用风险(Google 垃圾政策);旧稿的"AInvest 反例"本次未核到,已删;无人工审校产能→出局;YMYL 站型默认低配(时效与复核纪律冲突)。

**8 内链架构**
- 匹配信号:site_crawl crawl.json 的 edges/孤儿页清单非空 + 页面>500(小站收益有限)+ discoverability findings(sitemap/孤儿相关)。
- 收益区间:无第三方数字(权重流向修正类收益);验证凭两次 crawl 的 edges/孤儿 diff+收录变化;`link_graph.py`(R3-4,已实装)出 PageRank 排序、深度直方图和孤儿清单,`orphan_fix.py` 出"源→孤儿→建议锚文本"。
- 反指标:页面<100→工时不值;存在 CRITICAL→先策略 1;孤儿本身是薄内容→先并入 prune 三查(零点击×入链×外链)。

**9 E-E-A-T 强化**
- 匹配信号:站型⑧必查 + `core_eeat.py` 分低/veto 命中 + trust_signals 四维缺 + 作者实体页缺失。
- 收益区间:没有可引的数字。旧稿的"YMYL 匿名内容不承载权重(Sure Oak)"和"AI 流量 +2,300%(单案例)"本次未核到出处,已删。Google 在 SEO 起始指南里写明 E-E-A-T 不是排名因素([起始指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)),所以本策略的理由是可信度与用户判断,不是排名杠杆。
- 反指标:非 YMYL 且无作者面→收益系数按低计;堆 schema 不等于 E-E-A-T([arXiv 2609.35077](https://arxiv.org/abs/2609.35077):FAQ、结构化数据、CWV 在合并数据里的正效应,加入域名固定效应后反转或归零,见 geo-evidence-bank)——制度(真作者+真复核)先行,标记随行。

## 三、评分公式与决策表

`优先级分 = S(信号数)× B(收益系数)× R(资源可行性) ÷ K(风险系数)`

| 因子 | 取值 | 依据 |
|---|---|---|
| S | 0-5:命中该策略"匹配信号"的条数(封套/GSC/intake 各算一源) | 第二节逐条 |
| B | 1.5(A/B 级证据且区间大)/ 1.2(C 级或示意值)/ 1.0(D 级单案例或无数字) | 证据银行分级 |
| R | 1.0 四项齐 / 0.75 部分 / 0.5 缺或未答 | intake 四问 |
| K | 1.0 低 / 1.5 中(需过闸门+分批)/ 2.0 高(政策/惩罚风险面) | 风险容忍三类 |

**决策表(封套类别 × 站型 → 先查哪些候选)**

| 封套信号 | 任意站型必查 | 站型加权先查 |
|---|---|---|
| availability/indexability CRITICAL | 1 技术修复(锁定第一) | ②④facet/noindex 误封;⑤版本蚕食 |
| uniqueness(duplicate_title/薄/facet) | 1→2(先修因后刷新) | ②⑦facet/UGC;①vs 页 find-replace |
| discoverability(sitemap/孤儿) | 8 内链架构 | ③tag 薄页;⑤旧版本 noindex |
| rankability/schema 缺失 | quick_wins 清单 | ⑧E-E-A-T 制度先行;②PDP schema |
| band≥Fair 且无 CRITICAL | 2/3/6 按资源进 | ①③集成对/热点;②④礼物页/位置页 |
| ai_search_health 低/目标=AI 引用 | 5 GEO(可爬性先过) | ⑤⑥⑧权重最高 |
| GSC 国别分散+hreflang 健康 | 4 多语言 | 跨境②③优先 |
| GSC 衰退词+内容面大 | 2 内容刷新 | ③⑧年更数据页;①vs 页 |

- **反指标一票否决**:任一反指标命中→本轮出局,不进 Top3(不是靠低分挤掉),否决理由写进报告。
- **先基座约束**:策略 1 存在 CRITICAL 时永远列 Top3 第一,其余按分取二、三。
- 时间窗修正:硬 deadline 距今短于策略见效周期→该策略标注"窗口外"并降一位;见效周期来自各条收益区间,须与 intake 可接受周期对齐。
- 输出 Top3,每条六元组:`策略 / 依据信号(封套具体 finding+站型+intake 字段)/ 预期收益区间(带证据级别标)/ 优先级(分值)/ 反指标(触发即撤)/ 首条命令链`。

## 四、完整示例两则

> 两则示例的站点和数字是**虚构的演示**,用来展示评分与输出格式,不是真实案例,不能当基准。

**示例 A:SaaS 站(B2B 项目管理,约 1,200 页)**
输入:band=Fair;indexability 1 CRITICAL(noindex 命中 /vs/ 组 40 页);uniqueness WARN duplicate_title 同组;quick_wins 3(schema 缺)。站型①(URL 型谱 /vs//integrations/+SoftwareApplication)。intake:内容 2 篇/月、开发 0.5、Ahrefs 付费、外包 0;风险 pSEO 中/外链低/站群零;无硬 deadline,接受 1-2 季度;目标=非品牌 demo 注册 +50%(口径:GSC 非品牌点击→注册)。

| 序 | 策略 | 依据信号 | 预期收益区间 | 分 | 反指标 |
|---|---|---|---|---|---|
| 1 | 技术修复:撤 /vs/ noindex | phases[立即] 非空,40 页误封 | 无参照数字;2-6 周收录回升,audit_compare 复测 | 5×1.0×0.75÷1.0=3.75 | Update 窗口不动 |
| 2 | vs/alternatives 内容刷新 | uniqueness WARN+GSC 竞品词分布+产能 2/月 | 示意 60-80%、2-4 个月,观察 4-8 周 | 3×1.2×0.75÷1.0=2.7 | 零积累页→rewrite |
| 3 | 集成对 pSEO 试点 | 站型①pSEO 机会+模式词群+开发 0.5+风险中 | 组合量自算;Zapier 数字仅 D 级参照 | 4×1.0×0.75÷1.5=2.0 | 唯一度<40% 硬停;首批≤100 页过闸 |

落选说明:多语言(他国流量<5%)、GEO(先撤 noindex——被封页进不了引用池)、外链(预算 0+无可链资产)。triage 三件事:①撤 noindex→40 页 site_audit 复测;②刷新 6 张 vs 页→GSC 点击 8 周窗;③pSEO 首批 50-100 页→闸门 PASS+2-4 周索引率。

**示例 B:电商站(DTC 家居,约 8,000 URL)**
输入:band=Weak;uniqueness CRITICAL(facet 参数近重复 5,400 URL);availability WARN(缺货 404 月 +120);discoverability WARN(sitemap 超限)。站型②(/c//p/ 型谱+Product+Offer 覆盖 92%)。intake:内容 8 篇/月、开发 1、SF+Ahrefs、外包预算中;风险 pSEO 中高/外链中/站群零;Q4 旺季硬 deadline(10 周);目标=自然收入占比 12%→18%(口径:GA4 非品牌 organic 收入/总收入)。

| 序 | 策略 | 依据信号 | 预期收益区间 | 分 | 反指标 |
|---|---|---|---|---|---|
| 1 | 技术修复:facet 收敛+缺货保留 | uniqueness CRITICAL 5,400 URL+availability 404 | 爬虫预算回收,2-6 周真页面收录率回升 | 5×1.0×1.0÷1.0=5.0 | — |
| 2 | 导购内容包抄品类词 | 站型②品类词 SERP 被榜单占+产能 8/月 | 示意口径同策略 2;导购文观察 4-8 周 | 3×1.2×1.0÷1.0=3.6 | 意图错配先查 |
| 3 | pSEO 礼物矩阵 | 站型②礼物场景机会+uniqueness 修复后健康+风险中高 | 组合量自算;旺季词窗 10 周→首批须第 8 周前上线 | 4×1.0×1.0÷1.5=2.7 | 闸门硬停;无需求组合不生成 |

pSEO 排序注:分值低于导购,但旺季窗口硬过滤后首批仍可赶窗;若第 8 周前无法过闸→降出 Top3,补位策略=GEO(PDP schema 已 92%,补 FAQ/QA 面)。

## 五、与 project.py run triage 的衔接(R1-7)

strategy-fit 是 triage 的判定内核,链条:`site_crawl → 站型识别(project.py suggest_site_type,URL 型谱简化版;模糊=首位占比<30% 时列前二请确认,与八卡"识别信号"完整版互补)→ envelope → 本文评分 → triage 输出"站型+该做三件事+理由+验证方式"`。对齐现行实现口径:
- **事**=策略名+首条命令链(top_actions:envelope findings 优先、自带 recommendation;缺失时 audit-rule-catalog 严重度聚合兜底,CRITICAL>WARN>INFO、同档受影响面降序);
- **理由**=verdict.basis(来源标注)+本文六元组中的依据信号+落选说明(反指标否决的也要列,证明不是没考虑);
- **验证方式**=收益区间对应的复测命令与窗口(audit_compare / GSC 周期窗 / pSEO 闸门 PASS / citation_panel diff)。
- project.yaml 现行字段:`site / market / type(站型)/ created / history_dir / references`。**strategy-fit 建议扩展字段**(与 intake 四问一一对应,供 R1-1 后续吸收;未读到处时 triage 回退交互提问):`type_secondary`(混合站副卡)、`resources{content_capacity,dev,tool_tier,outsource_budget}`、`risk{pseo,links,networks}`、`window{deadline,patience}`、`goal{metric,definition}`。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败判据 |
|---|---|---|
| 三类输入已齐或已降级声明 | 有 envelope:`python3 scripts/envelope.py --audit audit.json`;资源字段看 [intake-checklists.md](intake-checklists.md) 四问 | 报告开头写明缺哪类输入以及按什么降级(资源未知按 0.5 计) |
| 站型已定或列前二 | `python3 scripts/project.py run triage`(内含站型建议,首位占比 <30% 时列前二) | 有主卡;模糊时已请用户确认 |
| 命令链里的脚本和参数真实存在 | 对每条首条命令链跑 `python3 scripts/<名>.py --help` | 参数都在 help 里;`link_graph.py`、`prune_gate.py` 等已实装,不再写"落地前" |
| 反指标一票否决已执行 | 对每个候选逐条对照"反指标" | 命中的候选不进 Top3,理由写进报告 |
| 外部数字有来源 | 每个收益区间旁有链接和证据级别 | 没有链接的数字删掉;D 级只作方向,不对客承诺 |
| 对客数字换成自家基线 | `python3 scripts/forecast.py --kws kws.csv --ctr gsc_ctr.csv --actual <月流量>` | 输出标 `[real]` 的自有曲线;只用内置曲线的结果标 `[est]` |
