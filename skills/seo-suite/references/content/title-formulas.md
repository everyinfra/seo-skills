# 标题写法

## 用途与何时读

给页面写 `<title>` 和 H1，或者页面有排名却没人点、想改标题时读。`<title>` 之外的 meta description、Open Graph 等标签见 [meta-tag-formulas.md](meta-tag-formulas.md)。

## 标题要同时完成两件事

1. **说清页面回答什么**：让搜索引擎和读者一眼看出这页对应哪类需求。意图判定见 [keyword-intent-taxonomy.md](../research/keyword-intent-taxonomy.md)。
2. **让对的人愿意点**：在一排结果里，让有这个需求的人看出这页比别的更合适。

两者冲突时准确优先。Google 的有用内容自查问题里就包括：标题是否对内容做了描述性的概括，是否避免夸大和耸动。

## 常用结构（示例均为自拟）

| 结构 | 适合 | 示例 |
|---|---|---|
| 主题 + 覆盖范围 | 概念解释、指南 | robots.txt 是什么：语法、示例和常见错误 |
| 怎么做 + 条件或结果 | 教程、操作步骤 | 如何在 Search Console 提交站点地图（附排错步骤） |
| 数量 + 对象 | 清单、盘点 | 8 个常见的 hreflang 配置错误及改法 |
| 对比对象 + 比较维度 | 对比页、选型 | 示例品牌与竞品 A 对比：价格、功能和迁移成本 |
| 用户原话式问题 | 排障、答疑 | 网站为什么没被收录？按顺序排查这 6 项 |
| 主题 + 人群或场景 | 细分受众 | 小型电商网站的结构化数据入门 |
| 主题 + 时间 | 确实按期更新的内容 | 2026 年搜索结果页功能变化汇总 |

用哪种结构看 SERP 前列在奖励什么形式，不按个人偏好选。

## 写法要点

- **主关键词自然出现**，放在前半部分更容易被扫到；不重复堆词。
- **数字要兑现**：写「8 个」，正文就是 8 条。
- **每页唯一**：模板生成的页面也要让标题体现各自差异，不能大批页面共用同一句。
- **品牌名要简短**，放在开头或末尾（内页通常放末尾），用一个分隔符隔开；站点名称在结果页里另有展示，见 Google 站点名称文档。
- **`<title>` 和 H1 意思一致**：写法可以不同，但不能讲两件事；页面上的主标题要清楚可辨，不要有多个同样醒目的大标题。
- **长度**：Google 对 `<title>` 没有字数上限，但结果页会按设备宽度截断。关键信息放前面，截断后仍能看懂。中文字符比拉丁字母宽，同样宽度放下的字更少；按实际显示效果检查，不死守字数。

## Google 可能改写标题链接

结果页里显示的标题链接不一定等于你的 `<title>`。标题缺失、过长、堆砌关键词、全站套同一句模板、与页面主标题不符或内容已过时，Google 都可能改用 H1、其他标题、锚文本等页面内外的文字。

发现被改写时，先检查上述问题并修正 `<title>` 和 H1，不要试图强行阻止改写。检查方法是在目标地域实际搜索并记录显示结果。

## 避免标题党

- 不承诺正文做不到的结果，不写没有依据的百分比。
- 「最全」「终极」「唯一」只在确实成立时用。
- 不制造虚假紧迫感，不全大写，不堆叹号。
- 年份只在内容真的按期更新时写，更新后同步修改。
- 对比类标题不预设胜负，把比较维度写出来。

## 改标题怎么验证

- 用 Search Console 效果报告按页面看点击率和平均排名，需要你自己的账号。
- 只在排名基本稳定时比较改动前后的点击率；同时排除季节、节假日和 SERP 功能变化的影响。
- 数据量太小不下结论。「点击率偏低」的判断以站点自己同类页面、同类排名的历史数据为参照，不套通用阈值。
- 一次只改标题，不同时改正文，否则无法判断原因。

## 交付时给出

每个页面：

1. 两三个候选标题，标明各自对应的意图和主关键词位置。
2. 推荐的一个，以及理由（SERP 前列的形式、截断后是否仍可读）。
3. 对应的 H1 建议。
4. 如为改写旧标题：改动原因和验证计划。

## 自查清单

- [ ] 读完标题就知道页面回答什么
- [ ] 主关键词自然出现，没有堆砌
- [ ] 与正文和 H1 一致，没有夸大
- [ ] 数字、年份和正文一致
- [ ] 截断后仍能看懂
- [ ] 站内没有另一页用同样或几乎相同的标题

## 市场差异:标题长度单位与惯例(2026-10-09 拉平轮;详见 multilingual-workflow 第四节)

公式跨市场通用,但**长度单位与截断行为按语言换**——英文基线(~60 字符/~580px)不可直接套:

| 市场 | title 惯例 | 单位注意 |
|---|---|---|
| 中文 | ~30 字以内 | 按字计;标题党禁(暴涨/封神) |
| 日语 | **全角 32 字**(desc 120 全角) | 用 visible_length(全角=1,半角=0.5 向上取整);英语圈 60/160 工具直接套会误判 |
| 韩语 | description ≤80 全角字(og:description 须一致) | |
| 德语 | 55–65 字符(~600px);**复合主词前置、不拆词** | 德语比英语长 25–35% |
| 西语 | 50–60;关键词前置比英语更关键(文本长 15–25%) | |
| 葡语(巴西) | 50–60(42–46 更稳,过长被重写);**禁 Title Case**(AI 味标志) | 句首大写 |
| 越南 | 45–65;**关键词进前 30 字符(防 Google 改写)** | 有调/无调并存时标题选带调形式 |
| 泰语 | 50–60,**按字素(grapheme)计非字符串长** | 无空格文字会词中截断 |
| 阿拉伯 | 文案比英文长 ~20%→按钮/标题预留空间;RTL 布局 | |
| 印尼 | title 50–60;EYD V 拼写 | |

## 标题审计:强弱模式与多候选制度(seomachine 深读 2026-10-09b)

**弱标题模式(命中即扣;共同点是自我视角而非读者收益开场)**:"Welcome to…"/"The best|ultimate|complete…"/"Everything|All you need…"/"Introducing…"/"We help|offer|provide…"/"Our product|service|solution…"。

**强标题模式(命中加分)**:数字开头;问句结尾;痛点去除("without…"/"no more…");解决方案到来(finally/at last);收益动词(save/grow/increase/boost)。落地页 H1/大标题 <70 字符。

**审计阈值**:meta title 50–60 字符、>65 截断风险;主关键词不在 title −10、不在 H1 −15(落地页)。与上文「Google 可能改写标题」一致:关键词缺失+过长正是触发改写的两类诱因。

**多候选制度**:文章规划期产出 title_options 多候选(与 meta description、slug、主/次关键词同批定),再按强弱模式与 SERP 前列形式挑选——与本文件「交付时给出两三个候选标题」互证。

**H2 分节标题分类词表(标题审计扩展到小标题)**:how-to(steps/guide/tutorial/process)、comparison(vs/versus/difference/best)、explanation(what is/why/overview)、list(top/best/tips/ways/methods)、FAQ(faq/questions)。FAQ 与 explanation 节是精选摘要目标位,FAQ 答案 40–60 词、直接答案先行——标题形式直接服务摘要抓取。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/seo-content-writer/references/title-formulas.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/seo-content-writer/references/title-formulas.md)（Apache-2.0）
- 深读补充：[TheCraigHewitt/seomachine · data_sources/modules](https://github.com/TheCraigHewitt/seomachine)(landing_page_scorer/article_planner/section_writer)
- 深读补充：[OpenClaudia/openclaudia-skills · skills](https://github.com/OpenClaudia/openclaudia-skills)(MIT;copywriting/email-subject-lines/write-landing/write-blog/seo-content-brief/thread-writer/newsletter/copy-editing/programmatic-seo/page-cro 十技能全文)
- 一手资料：[标题链接](https://developers.google.com/search/docs/appearance/title-link)、[站点名称](https://developers.google.com/search/docs/appearance/site-names)、[有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)

## 跨渠道标题公式库:四类场景与通用规则(openclaudia 深读 2026-10-09c)

同一套公式族(结果+痛点、数字清单、how-to、反共识、好奇缺口)在 SEO title、落地页 H1、邮件主题行、社交 hook 四个渠道反复出现;差异只在长度约束、禁用词和交付节奏。本节按渠道收录,公式骨架保留英文原式。

### SEO title 按意图选模板

| 意图 | 模板 | 示例骨架 |
|---|---|---|
| how-to | How to {动作}({限定语}) | How to Start a Blog (Step-by-Step Guide) |
| 清单 | {奇数} {形容词} {主题} for {年份/人群} | 15 Best SEO Tools for Small Business (2026) |
| 指南 | {主题}: The {形容词} Guide for {年份} | Email Marketing: The Complete Guide for 2026 |
| 对比 | {A} vs {B}: {决胜维度} | Notion vs Obsidian: Which Is Better for Teams? |
| 问答 | {问题}? {数据/承诺} | Is SEO Dead? What the Data Actually Shows |

配套规则:主关键词进前 30 字符;时敏话题带年份;清单用奇数;≤60 字符。与上文「常用结构」表互证,此表补充了意图→模板的显式映射。

### 落地页 H1 公式(5 秒测试)

- `{最终结果} without {痛点}` / `{动作动词} your {指标} by {数量}` / `The {形容词} way to {结果}` / `{结果} for {人群}` / `Stop {痛点}. Start {收益}.` / `{N} {人群} use {产品} to {结果}`
- 规则:最多 10 词(6–8 最佳);收益 > 功能;具体数 > 模糊形容;与带来流量的广告/链接做消息匹配(message match)。
- 副标题公式:`{产品} helps {人群} {达成结果} by {机制}. {证明或时限}.`
- H1 与 title tag 分开考虑:H1 可放宽到 <70 字符(与 seomachine 审计阈值一致),title 仍守 50–60。

### 邮件主题行:七族公式与预览文本配对

七族:好奇缺口、紧迫(须真实)、个性化、问句、数字清单、how-to、反共识。反共识族打开与退订同高,慎用。

- 甜点长度 30–50 字符(6–10 词);移动端预览宽 ~35–43 字符。
- **预览文本是主题行的延伸而非重复**(40–90 字符,永不留空):五种配对策略——续接(主题行断在半句)、背景、收益、反差、社会证明。
- 个性化(名字/行为)提升打开率 5–20%,但每封都 "{Name}," 会失效;行为个性化优于人口属性。
- 垃圾触发分级:高风险(FREE/Act now/Congratulations/Click here/Urgent 等)、中风险(Guarantee/Discount/双倍)、格式(全大写、多感叹号、伪造 Re:/Fwd:、1 个以上 emoji)。

### 社交 hook(thread/长文)

hook 公式:结果+时限、大胆断言、反共识、故事开场、清单、幕后、好奇、挑战问句。禁忌:hook 里不写 "Thread:"/"[1/N]" 前缀(降互动);链接永不放 hook,放末条或首评。一条一个观点,每条独立可读。

### 数字与特异性(多技能交叉出现,可信度最高)

- **奇数优于偶数**(7/9/11);**具体数优于整数**(247% 好过 ~250%);**用阿拉伯数字不用单词**。
- **特异性创造情绪**:"省时间"弱,"每周省 4 小时"强;原文对照案例:落地页写 "Save time" 转化 1.2%,改 "Save 4 hours every week" 后 4.7%。
- 数字必须兑现——与上文「数字要兑现」「避免标题党」互证。

### CTA 文案规则

动词开头、说清结果、禁 Submit/Click Here/Learn More;**第一人称常胜第二人称**("Start My Free Trial" > "Start Your Free Trial");按漏斗阶段配承诺等级(认知期低承诺,决策期高承诺);按钮旁配摩擦注释(无需信用卡/30 秒完成)。

### 用词:强力词与禁用词

- 强力词六类(每标题 1–2 个,轮换):紧迫(now/deadline)、独占(secret/insider)、信任(proven/tested)、价值(free/save)、情绪(breakthrough)、错失(before it's gone)。
- **与 seomachine 弱模式的冲突处理**:Ultimate/Complete/Definitive 类模板词在标题审计里是弱开场("The best|ultimate|complete…")——SEO title 少用;落地页与邮件可用,仍受「标题党」约束。
- 禁:weasel words(up to/as much as/potentially 无具体数)、clichés(best-in-class/world-class/cutting-edge/game-changer)。
- 自我视角检查:we/our 多于 you/your 时翻转比例——与 seomachine「弱标题共同点是自我视角」互证。

### 先测什么(A/B 优先级)

落地页影响排序第一是**标题角度**,其次 CTA 文案、社会证明位置、表单长度;邮件是主题行文案 > 个性化 > emoji > 预览文本 > 长度。一次只测一个变量,与上文「一次只改标题」互证。
