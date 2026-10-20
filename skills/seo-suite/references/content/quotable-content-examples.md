# 可被准确摘取的写法：改写示例

> 先读 [geo-evidence.md](geo-evidence.md)。这里的目标是让一句话、一段话脱离上下文后仍然准确，
> 方便读者引用，也降低被摘录时断章取义的风险；它不保证被 AI 产品引用。
> 示例中方括号里的内容都是占位，必须换成你自己有出处的事实，不能照抄或编造。

## 可摘取内容的五个特征

1. **自足**：主语明确，不依赖「如上所述」「它」「这个方法」。
2. **有边界**：写清条件、适用范围和例外。
3. **可核实**：数字带口径、时间和出处；原创数据说明方法。
4. **具体**：多用名词和动词，少用形容词和最高级。
5. **一致**：同一个概念全篇用同一个叫法。

## 示例一：定义

- 改写前：「这其实是一个很重要的概念，很多站点都会用到它。」
- 改写后：「**canonical 标签**是放在页面 `<head>` 中的 `<link rel="canonical">`，用来告诉搜索引擎一组重复或近似页面中哪个网址是首选版本。它是强信号而不是强制指令，搜索引擎可能选用别的网址。」
- 为什么：第一句给出类别和作用，第二句给出边界。事实依据：Google 规范网址文档把 `rel="canonical"` 列为「strong signal」。

## 示例二：数据

- 改写前：「我们的方案能大幅提升效率。」
- 改写后：「在 [时间段] 对 [样本量] 个 [对象] 的内部测试中，[指标] 从 [基线值] 变为 [新值]；测试方法见 [方法说明链接]。」
- 为什么：说清是谁测的、测了什么、怎么测。没有真实数据就不写数字；自己的测试写「在我们的测试中」，不要写成「研究表明」。

## 示例三：步骤

- 改写前：「设置起来不复杂，按提示操作即可。」
- 改写后：「前提：[权限或版本要求]。1. 在 [位置] 打开 [设置项]；2. 在 [字段] 填入 [格式]；3. 保存后用 [验证方法] 确认生效。常见错误：[错误现象] 通常是因为 [原因]。」
- 为什么：每一步都能被单独执行和验证。

## 示例四：对比

- 改写前：「A 和 B 各有优劣，看你的需求。」
- 改写后：先给一张表，行是评价维度（如 [维度 1]、[维度 2]、价格区间、核对日期），列是 A 和 B；表后一句结论：「如果你需要 [场景 1]，[A] 更合适；如果你更看重 [场景 2]，[B] 更合适。」
- 为什么：结论可以单独引用，表格提供依据，核对日期说明时效。

## 示例五：观点与专家意见

- 改写前：「业内专家普遍认为这件事很关键。」
- 改写后：「[姓名]（[职务]，[机构]）在 [日期] 的 [出处名称] 中指出：[可核实的观点]。」
- 为什么：观点可以追溯。引语必须真实可查，不能编造专家或把转述写成原话。

## 示例六：趋势

- 改写前：「未来这个方向一定会爆发。」
- 改写后：「[数据来源] 显示，[指标] 在 [时间段] 从 [值] 变为 [值]。据此可以判断 [有限的推论]；这一判断在 [条件] 变化时可能不成立。」
- 为什么：区分事实和推论，并写出推论的前提。

## 快速自检

- 把这段单独复制出去，读者不看上下文能否理解且不误解？
- 每个数字能否指向具体来源和日期？
- 有没有无法核实的「最好」「第一」「唯一」？
- 有没有空话套话（见 [ai-writing-detection.md](ai-writing-detection.md)）？
- 同一事实在页面其他位置、结构化数据里是否说法一致？

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/geo-content-optimizer/references/quotable-content-examples.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/geo-content-optimizer/references/quotable-content-examples.md)（Apache-2.0）
- 一手资料：[Google：规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)、[Google：有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)

## 页面级可引用构件（参考 kostja94/marketing-skills，核对 2026-10-21）

> 前半讲"单段怎么写"，这里讲页面级构件。参考来源：[kostja94/marketing-skills](https://github.com/kostja94/marketing-skills) 的 featured-snippet、article、eeat-signals、content-optimization 等技能。该仓库的数字多数没有一手出处，下面只留能核对的，其余标明本套件口径或已删除。

### 精选摘要（featured snippet）

- Google 官方：不能手动标记页面成为精选摘要，由系统判断；不公布所需的最小长度，因为长度随信息、语言、平台变化（[精选摘要文档](https://developers.google.com/search/docs/appearance/featured-snippets)）。所以不设固定词数。
- 第三方参考：[Semrush](https://www.semrush.com/blog/featured-snippets/) 说精选摘要有段落、列表、表格、视频四类，段落最常见；建议段落答案写 40–50 词、放在小标题后第一二句、语气像词典条目；Google 也会把页面里的多个标题拼成列表摘要，所以 H2 本身要能当列表项读。
- 删除：「段落 70% / 列表 19% / 表格 6%」「45 词最常被摘」在 Semrush 该页和 Google 文档里都找不到；「AIO 出现在约 47% 的美国搜索、取代 83% 的精选摘要」与实测冲突（Semrush 2025-11 为 15.69%，见 [geo-evidence-bank.md](geo-evidence-bank.md) 第三节）。
- AI Overviews 不是精选摘要：精选摘要摘自单一页面，AIO 是多来源生成摘要（Semrush 同页）。

### 文章级构件（本套件口径，不是规则）

- **TL;DR 或要点列表二选一**，放导语后。证据很弱：2609.35077 里 TLDR/BLUF 块 β=+0.05，作者称效应很小。写它的理由是读者省时间，不是被引。
- **问句小标题 → 直接答案 → 证据**：答案放在小标题后的头两句。答案块长度按题目定；Google 写明没有理想页长，不设「100–200 词」这类下限。
- **信息增益**：写前先看现有结果的共识层，只写缺口——自有数据、新近数据、一线从业者的可核实引语、反共识但有证据的观点。依据：Google 生成式 AI 指南强调提供非同质化内容（non-commodity content）。
- **内容密度比字数重要**：每段至少一个可核实的事实、数字或例子。Google 没有偏好的字数（[有用内容指南](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)）。已删除按意图给词数区间（如「Explore 2000–3500」）：找不到出处。
- **关键词**：不设密度目标；只避免堆砌，Google 垃圾内容政策把关键词堆砌列为违规（[spam policies](https://developers.google.com/search/docs/essentials/spam-policies)）。已删除「0.5–1.5%」参考区间：找不到出处。

### E-E-A-T 可验证构件

- 体验信号：案例（挑战→方案→结果）、原创研究、第一手测试（"我们实测了 X"）、真实用户证言。
- 作者块：真名、头衔、与主题相关的资历、可验证链接（LinkedIn 或个人站，对齐 Person 的 `sameAs`）。多作者标 Written by / Reviewed by。资历不得夸大或虚构。依据：Google 的 Who/How/Why 自查（有用内容指南）。
- 引用：统计数字内联引用；引用多时文末列参考文献。
- 健康、财经、法律、安全类（YMYL）门槛更高：AI 辅助的内容发布前要人审、核实并加引用。

### 标题与简介

- Google 对标题和简介没有固定字符上限，按显示宽度截断；「≤60 字符」只是本套件的提示阈值（见 [title-formulas.md](title-formulas.md) 与 [meta-tag-formulas.md](meta-tag-formulas.md)）。已删除「数字加力量词使 CTR +36%」：找不到出处。
- LinkedIn 个人简介：把「About」前 40–60 词写成先给结论的块，便于被读者和工具摘引（本套件口径）。已删除「登录墙内的短帖对搜索与 AI 都不可见」：未找到官方说明。

## 检查清单

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 段落脱离上下文仍成立 | 把段落单独复制出来读一遍；中文用 `python3 scripts/ste_lint.py 页面.md --lang zh --json` 看长句和指代 | 通过：不依赖「如上所述」「它」；无 fail 级问题。失败：靠上文才懂 |
| 2 | 每个数字有来源、口径、日期 | 人工逐条点开来源 | 通过：数字与原文一致。失败：死链、数字漂移、只有「研究表明」 |
| 3 | 术语全篇一致 | `python3 scripts/ste_lint.py 页面.md --glossary 术语表.csv` | 通过：无同义混用。失败：同一概念多种叫法 |
| 4 | 标题、首段用买家的问法 | `python3 scripts/question_align.py --gsc 查询页面.csv --pages 页面.csv --json`，见 [question-alignment.md](question-alignment.md) | 通过：首段第一句含主要查询原词并直接作答。失败：先铺垫 |
| 5 | 可见正文与结构化数据一致 | `python3 scripts/schema_lint.py URL`；`python3 scripts/ai_views.py --url URL --json` 看去噪后正文 | 通过：事实在可见文本里，标记与正文同源。失败：事实只在标记里 |
| 6 | 空话套话 | `cat 页面.txt \| python3 scripts/text_metrics.py --market zh` | 通过：无成片 slop 词。失败：命中多处 |
