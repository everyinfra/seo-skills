# Brand SERP 方法论：八面 AI Résumé 与 Algorithmic Trinity

> 建立于 2026-10-12，2026-10-18 对照原文复核。**框架来源：Kalicube《Brand SERP — Standalone Document》v1.0，2026-05-15，作者 Jason Barnard（术语 2012 年提出），[kalicube.pro/methodologies/brand-serp](https://kalicube.pro/methodologies/brand-serp)，许可 CC BY 4.0。本文转述并演绎其框架，须署名 Jason Barnard / Kalicube。** Kalicube 是第三方咨询公司：文中【Kalicube】标注的是它的方法论口径，不是搜索引擎的官方规则。工具接线表、与 brand.yaml 的映射、命令化流程是本套件口径。
> 引擎面行为按 3 个月、概念框架按 6 个月复查（本套件口径），随 intel-update 搭车核对。
> 关联方法论：[search-everywhere-optimization.md](../research/search-everywhere-optimization.md)（非品牌词的全平台层）、[community-seo-playbook.md](../content/community-seo-playbook.md)（第三方口碑面）。

## 一、概念：从 2012 的 Google 一页，到 2026 的 AI Résumé

Brand SERP 指用户**搜索品牌名**时返回的结果页或回答【Kalicube】。Kalicube 认为它是品牌可见性最重要的单一诊断面：潜在客户接触销售之前会先看它。2012 年的说法是「Google 对『世界对你的看法』的看法」；2026 年改为「AI 对『世界对你的看法』的看法」：AI 助手在做 Google 当年做的事，只是用合成文本替代了蓝色链接。这页「简历」出错，品牌在销售对话开始前就已经输了。

三种失败模式【Kalicube】，对应三类修法：

| 失败模式 | 表现 | 修法方向（本套件映射） |
|---|---|---|
| Confusion（混淆） | 算法不确定指哪个实体；同名品牌互抢；回答含糊 | 实体地基（第六节） |
| Negativity（负面） | 差评、争议、偏向竞品的对比占据首屏 | 第三方口碑面 + 事实一致性 |
| Invisibility（不可见） | 结果稀疏、没有知识图谱条目、AI 不敢描述你 | 跨平台印证 + 结构化数据 |

## 二、八面 AI Résumé 清单

Kalicube 的诊断步骤列出八个面：Google、Bing、ChatGPT、Claude、Gemini、Perplexity、Copilot、Google AI Mode；它的定义清单另外并列了 Grok 和知识图谱条目【Kalicube】。本套件把两份清单合并为下表：

| # | 面 | 查什么 |
|---|---|---|
| 1 | Google SERP（品牌词） | 首屏叙事：官网与子链占比、第三方内容性质、有无竞品入侵 |
| 2 | Bing SERP | 同上。Microsoft 文档说明 Copilot 把生成的搜索词发给 Bing 搜索服务来获取网页依据（[Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-365/copilot/manage-public-web-access)），所以单独看 |
| 3 | ChatGPT（「介绍一下 X」） | 叙事方向、是否含糊、引用了谁 |
| 4 | Claude | 同一问法；结论不能从别的面推出来 |
| 5 | Gemini | 同上 |
| 6 | Perplexity | 引用列表里品牌自有内容与第三方的比例 |
| 7 | Copilot / Grok | 同一问法 |
| 8 | 知识图谱条目 + Google AI Mode | 知识图谱条目有无、对错；AI Mode 对品牌词的综合回答 |

各面独立判定：Kalicube 原文举例，Google 上表现强的品牌在 ChatGPT 上仍可能含糊；知识图谱条目完美的品牌在 Perplexity 上仍可能不可见【Kalicube】。

## 三、Algorithmic Trinity：三套算法生态

Kalicube 把搜索引擎、大语言模型、知识图谱称为 Algorithmic Trinity（2024 年提出）【Kalicube】。下表「喂法」一列是本套件的映射：

| 生态 | 本套件映射 |
|---|---|
| 搜索引擎 | 既有 SEO 全套；SERP 面见 [serp-feature-taxonomy.md](../research/serp-feature-taxonomy.md) |
| 大语言模型（ChatGPT、Claude、Gemini 等） | 品牌事实一致地出现在官网、社区、评论、新闻等多个来源；引用行为观测见 [ai-citation-patterns.md](../content/ai-citation-patterns.md) |
| 知识图谱 | schema 与可见正文一致、`sameAs` 指向真实资料页、Wikidata 等开放知识库；操作见 [knowledge-graph-guide.md](knowledge-graph-guide.md) |

包含层级【Kalicube】：AAO（Assistive Agent Optimization，2025）⊃ AIEO（AI Assistive Engine Optimization，2024）⊃ AEO（Answer Engine Optimization，2017）⊃ SEO；三个缩写都由 Jason Barnard 提出。原文：做 SEO 不会让 AAO 自然发生，做 AAO 必然包含 SEO。

## 四、品牌词诊断流程（四步，逐面执行）

1. **八面搜索**：品牌名（加别名、常见错拼）在八个面各搜一次，记下每面的第一印象。
2. **UCD 三问打分**【Kalicube】：Understandability（这一面知道你是谁吗，对应 BOFU，实体地基）；Credibility（它信任到愿意推荐吗，对应 MOFU）；Deliverability（它按你期望的方式正面呈现吗，对应 TOFU）。必须自下而上修：U → C → D；信任信号要挂在已经存在的实体节点上。
3. **缺口识别**：不可见、含糊、负面的面各归一类缺陷：缺知识图谱条目、实体混淆、印证薄弱、内容陈旧、第三方负面报道【Kalicube】。
4. **按缺口逐个关闭**：从 U 开始；完成后复测同样的八面。

### 逐面核查表（每面三个固定检查位，本套件口径）

| 面 | ① 品牌词结果/回答占比 | ② 实体正确性 | ③ AI 回答叙事 |
|---|---|---|---|
| Google SERP | 前 10 中自有域占几位？子链有无？竞品或聚合站入侵？ | 知识面板有无、名称对不对、字段错没错 | —（AI Mode 单列） |
| Bing SERP | 同上口径，与 Google 差分记录 | Bing 实体卡 | — |
| ChatGPT / Claude / Gemini / Copilot / Grok | 回答是否含品牌与正确域名 | 指的是不是同一实体 | 定位句与 brand.yaml 差多少；含糊词（「可能」「据说」）多少 |
| Perplexity | 引用列表里自有域与第三方的条数 | 同上 | 叙事以谁的内容为底 |
| 知识图谱 + Google AI Mode | 知识图谱实体 ID（KG Search API 的 `kg:/m/…`）记录、`sameAs` 齐 | 字段逐项对照 brand.yaml | AI Mode 综合回答的倾向（正面/中性/负面） |

执行纪律（本套件口径）：同一 prompt 至少采样 3 次再下结论（引擎输出有随机性，见 citation_panel 口径）；逐面记录检查日期和条件（语言、地区）；跨期比较用配对分母。

## 五、与本套件工具的接线

| 工具/文档 | 覆盖哪块 | 用法（参数已对照 `--help` 核对） |
|---|---|---|
| `scripts/citation_panel.py` | 第 3–7 面的采样与打分 | `init --brand X --domain x.com --engines chatgpt,perplexity,gemini,copilot,claude,grok`（`--engines` 默认值即这六个）；`record` 记录一次采样；`report`；`diff RUN1 RUN2`；`decay`。每个格子分五种状态：`no_answer`、`failed`、`brand_absent`、`name_only_mention`、`cited_brand` |
| [brand-records.md](../content/brand-records.md) | U 层事实源 | brand.yaml 是所有面的对照基准；叙事与 brand.yaml 冲突即 U 或 C 缺口 |
| `scripts/oracle_check.py` | 第 3–7 面的叙事正确性 | `--facts brand.yaml --responses responses.json --out findings.json`：数字、日期、布尔冲突自动判；语义冲突（定位漂移）由人工复核 |
| [entity-signal-checklist.md](entity-signal-checklist.md) | 第 8 面的前置 | 站内基础 → 外部资料 → 呈现的核查顺序 |
| `scripts/grounding_page.py` | U 层实体事实页 | `--facts brand.yaml --type Organization --out entity.md` 生成；`--check 现有页面.md` 跑 11 条检查 |

## 六、实体三源（知识图谱一侧，本套件口径）

1. **自有一致性**：官网、文档、社媒资料、定价页对同一事实的表述完全一致（brand.yaml 是单一事实源，起草前必读）。不一致是混淆的第一来源。
2. **开放知识库**：符合收录标准才建条目、每条陈述带可靠来源、披露利益关联（规则见 [knowledge-graph-guide.md](knowledge-graph-guide.md)）；不符合 Wikipedia 收录标准时，以 Wikidata 和权威目录为主。
3. **结构化数据 + sameAs**：Organization 标记只写页面可见的事实；`sameAs` 只链自有或已认领的资料页。

校验顺序：先修自有一致性（全可控）→ 再补开放知识库与目录（部分可控）→ 最后观测八面呈现（不可控，只观测）。

## 七、诊断工作流（套件命令链）

```bash
# 1. 建面板：品牌词 + 品类词两组题，六个 AI 引擎（八面中的第 3–7 面）
python3 scripts/citation_panel.py init --brand Acme --domain acme.ai \
  --aliases "Acme CRM,艾克米" --engines chatgpt,perplexity,gemini,copilot,claude,grok --stage-mix
# 2. 采样录入后出报告（mention coverage / citation share / SoV）
python3 scripts/citation_panel.py report
# 3. AI 叙事正确性核查（第 3–7 面回答对照 brand.yaml）
python3 scripts/oracle_check.py --facts brand.yaml --responses responses.json --out findings.json
# 4. 第 8 面前置：按 entity-signal-checklist 顺序核站内基础与 sameAs
# 5. 缺口归因 → 按第六节顺序修 → 复测同八面，配对对比两期
python3 scripts/citation_panel.py diff RUN1 RUN2
```

Google 和 Bing 两个 SERP 面的人工检查结论记进项目工作区，与面板报告合并为八面快照；按月留档，看趋势而不是单点。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 八面都有记录 | 打开本月快照，逐面看日期、语言、地区三项 | 八面齐全且条件已记 → 通过 |
| AI 面采样足够 | `python3 scripts/citation_panel.py report` 看每个 prompt × 引擎的采样次数 | 每格 ≥3 次 → 通过（本套件口径） |
| 叙事正确 | `oracle_check.py` 的 findings 里未处理的冲突数 | 0 个未处理的数字、日期冲突 → 通过 |
| 实体地基 | 按 [entity-signal-checklist.md](entity-signal-checklist.md) 检查清单 | 站内名称一致、sameAs 有效 → 通过 |
| 趋势 | `citation_panel.py diff 上月RUN 本月RUN` | cited_brand 占比不下降 → 通过 |

## 八、证据边界与引用纪律

- 本文框架性表述转述 Kalicube canonical v1.0（CC BY 4.0）：对外输出物复用这些框架时，按 CC BY 4.0 署名 Jason Barnard / Kalicube 并链原文。原文提到的 Kalicube Pro 看板是其商业产品，本套件不背书、不依赖。
- 跨面不能互推是 Kalicube 的明确口径；第三方研究也指向同一方向：Profound 用自家平台跟踪 7 个 AI 搜索引擎上约 88.3 万个页面 12 个月，发现同一页面在不同引擎上的引用持续时间相关系数只有 0.03–0.09；只有 Google 的三个面（AI Overviews、AI Mode、Gemini）之间是 0.12–0.17（[Profound 博客](https://www.tryprofound.com/blog/the-half-life-of-an-ai-citation-is-11-days)，2026-09-30；转引见 borrow-specs.md）。分面独立判定是本套件的硬规则。
- 本文不承诺任何面的呈现结果（证据边界见 [geo-evidence.md](../content/geo-evidence.md)）。
