# Brand SERP 方法论:八面 AI Résumé 与 Algorithmic Trinity

> 建立于 2026-10-12(R6 新方法论入库)。**Canonical 来源:Kalicube《Brand SERP — Standalone
> Document》v1.0,2026-05-15,Jason Barnard(术语 2012 年提出),kalicube.pro/methodologies/brand-serp,
> 许可协议 CC BY 4.0——本文件转述/演绎其框架,须署名 Jason Barnard / Kalicube,商用口径以原文为准。**
> 本套件的工具接线表、与 brand.yaml 的映射、诊断流程的命令化为套件自有约定【推断】。
> **断言半衰期 3–6 个月**(引擎面行为 3 个月/概念与框架 6 个月),随 intel-update 复盘搭车核对。
> 关联方法论:[search-everywhere-optimization.md](../research/search-everywhere-optimization.md)(非品牌词的全平台层)、
> [community-seo-playbook.md](../content/community-seo-playbook.md)(第三方口碑面)。

## 一、概念:从 2012 的 Google 一页,到 2026 的 AI Résumé

Brand SERP = 用户**搜品牌名**时返回的那一页/那个回答【官方】。Kalicube 判定它是品牌可见性最重要的
单一诊断面:潜在客户在接触销售之前,一定先看它。2012 的口径是"Google 对'世界对你的看法'的看法";
2026 的口径升级为 **"AI 对'世界对你的看法'的看法"**——AI 助手在做 Google 当年做的事,
只是用合成文本替代了蓝色链接。这页"简历"决定点击、推荐与交易:**简历错了,销售对话开始前就已输**。

三种失败模式【官方】,对应三类修法:

| 失败模式 | 表现 | 修法方向 |
|---|---|---|
| Confusion(混淆) | 算法不确定指哪个实体;同名品牌互抢;回答在打太极 | 实体地基(第六节) |
| Negativity(负面) | 差评、争议、对竞品有利的对比占据首屏 | 第三方口碑面+事实一致性 |
| Invisibility(不可见) | 结果稀疏、无知识面板、AI 不敢描述你 | 跨平台印证+结构化数据 |

## 二、八面 AI Résumé 清单

2026 形态的 Brand SERP 不再只是 Google 一页【官方】。诊断面:

| # | 面 | 查什么 |
|---|---|---|
| 1 | Google SERP(品牌词) | 首屏叙事:官网/子链占比、第三方内容性质、有无竞品入侵 |
| 2 | Bing SERP | 同上;Bing 是 Copilot 的底座,单独看 |
| 3 | ChatGPT("介绍一下 X") | 叙事方向、是否 hedge、引用了谁 |
| 4 | Claude | 同问法;训练与检索机制不同,结论不可互推 |
| 5 | Gemini | 同上;与 Google/KG 数据亲缘最近 |
| 6 | Perplexity | 引用来源列表里品牌自有内容 vs 第三方的比例 |
| 7 | Copilot / Grok | 同问法(官方诊断协议的八面口径为 Google、Bing、ChatGPT、Claude、Gemini、Perplexity、Copilot、Google AI Mode;Grok 与 KG 条目在定义清单中并列,两表述并记) |
| 8 | 知识面板 + Google AI Mode | KG 条目有无/对错;AI Mode 对品牌词的综合回答 |

各面独立判定——"Google 强 ≠ ChatGPT 不 hedge;KG 完美 ≠ Perplexity 可见"【官方】。

## 三、Algorithmic Trinity:三套算法生态,各自喂什么

品牌在 2026 被三套算法生态共同理解,缺一即拖累另两套【官方】:

| 生态 | 它吃什么 | 喂法(套件映射) |
|---|---|---|
| 搜索引擎 | 可抓取、可索引、可排序的内容 | 既有 SEO 全套;SERP 面见 [serp-feature-taxonomy.md](../research/serp-feature-taxonomy.md) |
| LLM(ChatGPT/Claude/Gemini/…) | 跨平台**相互印证**的事实与语料;单点自述权重低 | 品牌事实一致地出现在官网/社区/评论/新闻多源;引用行为观测见 [ai-citation-patterns.md](../content/ai-citation-patterns.md) |
| 知识图谱(KG) | 一致、可核验的实体事实 | schema 与可见正文一致、sameAs 指真实档案、Wikidata 等开放库;操作见 [knowledge-graph-guide.md](knowledge-graph-guide.md) |

包含层级【官方】:AAO(Assistive Agent Optimization,2025)> AIEO(AI 引擎优化,2024)> AEO(答案引擎
优化,2017)> SEO。上层包含下层;只做 SEO 不等于 AAO 发生,做 AAO 必然包含 SEO。

## 四、品牌词诊断流程(四步,逐面执行)

1. **八面搜索**:品牌名(+ 别名/常见错拼)在八个面各搜一次,记下每面的第一印象。
2. **UCD 三问打分**【官方】:Understandability——这面知道你是谁吗(实体基础,BOFU 层);
   Credibility——它信任到愿意推荐吗(MOFU,信任积累);Deliverability——它按你期望的方式有利呈现吗
   (TOFU,主动推荐)。**必须自底向上修:U 先于 C 先于 D**——信任信号要挂在已存在的实体节点上,
   跳过地基直接刷 D 不产生结果。
3. **缺口识别**:不可见/hedge/负面的面各归因一类缺陷——缺 KG 条目、实体混淆、印证薄弱、
   内容陈旧、第三方负面覆盖。
4. **按缺口关单**:从 U 开始系统化关闭;复测同八面。

### 逐面核查表(每面三个固定检查位)

| 面 | ① 品牌词 SERP/回答占比 | ② 知识面板/实体正确性 | ③ AI 回答叙事 |
|---|---|---|---|
| Google SERP | 前 10 中自有域占几位?子链有无?竞品/聚合站入侵? | 知识面板有无/名称对不对/字段错没错 | ——(AI Mode 单列) |
| Bing SERP | 同上口径,与 Google 差分记录 | Bing 实体卡(Copilot 底座) | —— |
| ChatGPT | 回答是否含品牌与正确域名 | 指的是不是同一实体(同名混淆) | 定位句与 brand.yaml 差多少;hedge 词密度("可能""据说") |
| Claude | 同上 | 同上 | 同上 |
| Gemini | 同上 | 同上 | 同上 |
| Perplexity | 引用列表里自有域 vs 第三方条数 | 同上 | 叙事以谁的内容为底(差评站还是官网) |
| Copilot / Grok | 同上 | 同上 | 同上 |
| KG + Google AI Mode | KG 条目 MID 记录、sameAs 齐 | 字段逐项对照 brand.yaml | AI Mode 综合回答的整体倾向(正面/中性/负面) |

执行纪律:同一 prompt ≥3 次采样再下结论(引擎输出本身是掷硬币,见 citation_panel 口径);
逐面记录"检查日期+条件(语言/地区)",跨期比较用配对分母。

## 五、与本套件工具的接线

| 工具/文档 | 覆盖八面诊断的哪块 | 用法 |
|---|---|---|
| `scripts/citation_panel.py` | 第 3–7 面(AI 引擎)的采样与打分 | `init --brand X --engines chatgpt,perplexity,gemini,copilot,claude,grok`(即脚本六引擎默认);品牌词题进 prompt bank;五状态分类(brand_absent/name_only_mention/cited_brand)≈ 八面的 AI 叙事打分;`decay` 监控品牌词引用衰减 |
| [brand-records.md](../content/brand-records.md) | U 层事实源:品牌"希望算法相信什么" | 六记录 brand.yaml 是所有面的对照基准;品牌词叙事与 brand.yaml 冲突即 U/C 缺口 |
| `scripts/oracle_check.py` | 第 3–7 面的**叙事正确性**核查 | AI 采样回答(citation_panel 导出 responses.json)对照 brand.yaml:数字/日期/布尔冲突自动判;语义级冲突(定位漂移)由 agent 复核——即 Negativity/Confusion 的机检前置 |
| [entity-signal-checklist.md](entity-signal-checklist.md) | 第 8 面 KG/知识面板前置 | 站内基础→外部资料→呈现 的核查顺序 |
| `scripts/grounding_page.py` | U 层落地页生成骨架 | 实体页 11 条规范(brand-records.md 第六节)的工程化 |

## 六、实体三源(Algorithmic Trinity 的 KG 侧燃料)

1. **自有一致性**:官网、文档、社媒档案、定价页对同一事实的表述完全一致(brand.yaml 单一事实源,
   起草前必读);不一致是 Confusion 的第一来源。
2. **Wikipedia 类开放知识库**:符合收录标准才建条目、每条陈述带可靠来源、披露利益关联——
   规则见 [knowledge-graph-guide.md](knowledge-graph-guide.md);不符合收录标准时以 Wikidata/权威目录为主。
3. **结构化数据 + sameAs**:Organization schema 只镜像页面可见事实;sameAs 只链自有/已认领档案。

三源校验顺序:先修自有一致性(全可控)→ 再补开放库与目录(部分可控)→ 最后观测八面呈现(不可控,只观测)。

## 七、诊断工作流(套件命令链)

```bash
# 1. 起面板:品牌词+品类词两组题,六 AI 引擎(即八面中的 3-7 面)
python3 scripts/citation_panel.py init --brand Acme --domain acme.ai \
  --aliases "Acme CRM,艾克米" --engines chatgpt,perplexity,gemini,copilot,claude,grok --stage-mix
# 2. 采样录入后出报告(mention coverage / citation share / SoV)
python3 scripts/citation_panel.py report
# 3. AI 叙事正确性核查(第 3-7 面回答对照 brand.yaml;U 层缺口会以数字/日期冲突显形)
python3 scripts/oracle_check.py --facts brand.yaml --responses responses.json --out findings.json
# 4. KG/知识面板前置(第 8 面):按 entity-signal-checklist 顺序核站内基础与 sameAs
# 5. 缺口归因 → 按第六节三源顺序修 → 复测同八面(citation_panel diff 对比两期)
python3 scripts/citation_panel.py diff RUN1 RUN2
```

SERP 两面(Google/Bing)的人工检查结论记进项目工作区,与面板报告合并为八面快照;
Brand SERP 是过程量,快照按月留档,趋势比单点重要。

## 八、证据边界与引用纪律

- 本文件框架性表述转述 Kalicube canonical v1.0(CC BY 4.0):对外输出物复用这些框架时,
  按 CC BY 4.0 署名 Jason Barnard / Kalicube 并链原文;"Kalicube Pro 平台聚合八面看板"为其实体产品描述,
  本套件不背书、不依赖。
- 八面结论**跨面不可互推**是官方明确口径,与 citation_panel 的跨引擎相关仅 0.03–0.09
  (borrow-specs.md 官方常数)互证——分面独立判定是硬规则。
- 引擎面行为(哪面 hedge、哪面引用谁)按 3 个月半衰期复查;本文不承诺任何面的呈现结果
  (证据边界见 [geo-evidence.md](../content/geo-evidence.md))。
