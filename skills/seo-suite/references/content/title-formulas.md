# 标题写法

## 用途与何时读

给页面写 `<title>` 和 H1，或者页面有排名却没人点、想改标题时读。

- title 里用哪些词，先看 [question-alignment.md](question-alignment.md)：用买家提问的原词，首段第一句直接回答。
- meta description、Open Graph 等其他标签见 [meta-tag-formulas.md](meta-tag-formulas.md)。
- 邮件主题行、社交帖开头、按钮文案不属于搜索场景，本文件不收。

## 标题要同时完成两件事

1. **说清页面回答什么**：读者和搜索引擎一眼看出这页对应哪类需求。意图判定见 [keyword-intent-taxonomy.md](../research/keyword-intent-taxonomy.md)。
2. **让对的人愿意点**：有这个需求的人在一排结果里看出这页更合适。

两者冲突时准确优先。Google 的有用内容自查问题包括：主标题或页面标题是否对内容做了描述性、有帮助的概括；是否避免夸大或耸动（[有用内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)，核对 2026-10-18）。

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

选哪种结构，看目标查询的原词和 SERP 前列的页面形式，不按个人偏好（本套件口径）。

## 写法要点

下面前七条出自 Google [标题链接文档](https://developers.google.com/search/docs/appearance/title-link)（核对 2026-10-18）：

- **每页都有 title**。描述性、简洁。不用「首页」「资料」这类空泛词，也不写冗长的句子。
- **不堆词**。几个描述词可以；同一个词或短语不重复。文档的反例是「Foobar, foo bar, foobars, foo bars」。
- **每页唯一**。不全站共用一句。长模板里只换一个词也不行。可以按页面实际内容动态生成：页面有视频才写「视频」。
- **品牌简短**。首页可以多写一句站点介绍。内页只在开头或结尾放站点名，用连字符、冒号或竖线隔开。站点名已在结果里显示时，Google 可能从标题链接里省掉重复的站点名。
- **主标题清楚**。放在页面第一个可见的 `<h1>` 里，字号最大。不要有多个同样醒目的标题。
- **语言和文字一致**。title 用正文的语言和文字。例：印地语页面不写英文 title，也不写拉丁字母转写。
- **航班价格不写进 title**。航班价格变得太快，Google 生成标题链接时多半不显示价格。

本套件口径：

- 主关键词放前半部分，截断后仍能看懂。
- 数字要兑现。写「8 个」，正文就是 8 条。
- `<title>` 和 H1 的写法可以不同，但讲同一件事。

**长度**：Google 对 `<title>` 没有长度上限。标题链接按需截断，通常按设备宽度截断（核对 2026-10-18）。字符数只是代理指标。中日韩字符是全角，同样宽度放下的字更少。按语言的提示阈值见本文「市场差异」节。

## Google 可能改写标题链接

结果页显示的标题链接不一定等于你的 `<title>`（[标题链接](https://developers.google.com/search/docs/appearance/title-link)，核对 2026-10-18）：

- **来源**：`<title>`、主视觉标题、`<h1>` 等标题元素、`og:title`、样式醒目的文字、正文、页内锚文本、指向本页的链接文字、`WebSite` 结构化数据。
- **官方列出的常见问题**：半空的 title（例如只有「| 站点名」）、过时的 title（年份没更新）、不准确的 title、小段模板重复（例如几季剧集共用一个 title）、没有清楚的主标题、语言或文字与正文不一致、重复站点名。
- **生效时间**：Google 要重新抓取和处理页面，可能需要几天到几周。可以请求重新抓取。
- **robots.txt**：被 robots.txt 屏蔽的页面仍可能被索引，这时 Google 只能用外部锚文本等生成标题链接。要阻止索引，用 `noindex`。

被改写时：先对照上面的常见问题修 `<title>` 和 H1。都没有，就看 Google 显示的标题是否更贴近查询。Google 不为单个站点手工改标题链接。检查方法：在目标地域实际搜索，记下显示的标题和日期。

## Bing 的要求

- Bing 网站管理员指南第 13 条：缺失、重复或过短的 title 和 meta description，可能降低索引可靠性、排名，以及被选作引用来源的资格。第 17 条：标题、标题层级和内容意图保持一致（[Bing 指南](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)，核对 2026-10-18）。
- Bing Webmaster Tools 的 Site Scan 会报「Title too long」「Title too short」。Bing 官方帮助没有公开阈值。第三方截图显示：标题超过 70 个字符报警告（[第三方](https://ottiliestudio.com/blog/fixing-website-issues-in-bing-webmaster-tools)）。这是工具提示阈值，不是排名规则。

## 避免标题党

- 不承诺正文做不到的结果，不写没有依据的百分比。
- 「最全」「终极」「唯一」只在确实成立时用。
- 不制造虚假紧迫感，不全大写，不堆叹号。
- 年份只在内容真的按期更新时写，更新后同步修改。Google 有用内容自查把「内容没有实质变化却改日期显得新鲜」列为警示信号。
- 对比类标题不预设胜负，写出比较维度。

## 改标题怎么验证

- 方法和通过标准见 [question-alignment.md](question-alignment.md) 第五节：28 天基线、对照页、先写判据、新标题生效后再计窗口、展示掉了先查排名。
- 一次只改标题和首段，不同时改正文结构，否则无法判断原因（本套件口径）。
- 判断「CTR 偏低」，用本站同排名段的 CTR 作参照，不套第三方曲线。第三方研究的曲线差别很大，例见 question-alignment.md 第三节。

## 交付时给出

每个页面：

1. 两三个候选标题，标明各自对齐的买家查询和主关键词位置。
2. 推荐的一个，以及理由：原词覆盖、SERP 前列的形式、截断后是否可读。
3. 对应的 H1 建议。
4. 如为改写旧标题：改动原因、基线数据和验证计划。

## 市场差异：长度提示阈值（本套件口径）

Google 和 Bing 都没有按语言规定 title 长度。下表是本套件的提示阈值。数据在 `scripts/markets.json`，由 `site_audit.py --market XX` 和 `market_lint.py --market XX` 读取。超限只提示复查截断效果，不是排名规则；`market_lint.py` 把超限记为 CRITICAL，严于搜索引擎。

| 市场 | title 上限 | description 上限 | 计数单位 | markets.json 记录的来源（本组未核） |
|---|---|---|---|---|
| zh | 30 | 78 | 字符 | 百度 PC 约 30 字截断；百度摘要约 76–78 字 |
| ja | 32 | 120 | 全角（全角 = 1，半角 = 0.5） | kseo 全角阈值 |
| ko | 30 | 80 | 全角 | Naver PC 约 30 全角；description ≤ 80 全角 |
| de | 65（低于 55 提示） | 150 | 字符 | Sistrix 口径 55–65 |
| ru | 55 | 160 | 字符 | Yandex 约 50–55 字符截断 |
| vi | 65（低于 45 提示；关键词进前 30 字符） | 155 | 字符 | t0mmy 规则集（业内规则，非官方） |
| th | 60 | 155 | 字素 | 泰文无词间空格，按字素计 |
| id | 60 | 155（前 120 字符是安全区） | 字符 | — |
| en、es、pt、fr、it、tr、hi、pl、nl、ar | 60 | 155 | 字符 | ar：阿拉伯文比英文长，留余量 |

量长度：`printf '%s' "标题文字" | python3 scripts/text_units.py ja`（市场可选 en、zh、ja、th、ko、ru、id）。拉丁语言看输出里的 `chars`，日韩看 `visible_fullwidth`。

第三方研究（相关性，不是因果）：Backlinko 2019 年发布的研究里，40–60 个字符的 title 平均 CTR 最高（[第三方研究](https://backlinko.com/google-ctr-stats)）。

## 标题审计：弱模式与多候选

- **自我视角开头信息量低**，审计时标出：Welcome to…、Introducing…、We help / offer / provide…、Our product / service…、Everything you need…。来源是 seomachine 评分器的弱标题词表（第三方开源工具，不是研究结论）。Google 文档也建议避免「Home」「Profile」这类空泛标题。
- **不按「问句结尾」「数字开头」加分**。Backlinko 2019 年研究里，问句标题与非问句标题的 CTR 差异不显著（15.5% 与 16.3%，第三方研究）。写不写成问句，看买家原话。
- **多候选**：规划期就产出 2–3 个候选 title，与 meta description、slug、主次关键词同批定，再按原词覆盖和 SERP 前列形式挑选。
- **小标题分类**（本套件口径，用于把审计扩展到 H2）：how-to、comparison、explanation、list、FAQ。FAQ 和 explanation 节下先给一两句直接答案。Google 不公布进入精选摘要的最短长度，也不能手动把页面标成精选摘要（[精选摘要](https://developers.google.com/search/docs/appearance/featured-snippets)，核对 2026-10-18），所以本套件不规定答案字数。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| title 存在 | `python3 scripts/site_audit.py URL --market XX --json`，看 title 类发现 | 通过：无 `title-missing`。失败：缺失（CRITICAL） |
| 长度 | 同上；或 `text_units.py` 量 | 通过：无 `title-too-long`、`title-too-short`。命中：复查截断后是否可读（WARN，不是排名规则） |
| 用了买家原词 | 按 [question-alignment.md](question-alignment.md) 第六节 | 通过：主查询核心词都在。失败：缺词或只有同义改写 |
| 不堆词 | 数 title 里每个词的出现次数 | 通过：除品牌名外每个词最多 1 次（本套件口径）。失败：重复 |
| 每页唯一 | `site_audit.py URL1 URL2 … --json > audit.json`，再 `python3 scripts/health_score.py --input audit.json --json` | 通过：没有 `duplicate_title`。失败：有 |
| 主标题 | 浏览器看渲染后的页面；site_audit 的 `h1-missing`、`h1-multiple` | 通过：一个最醒目的主标题，与 title 讲同一件事。失败：没有主标题，或几个同样醒目 |
| 语言和文字 | 对照正文 | 通过：同一语言、同一文字。失败：混用或转写 |
| 数字和年份 | 对照正文 | 通过：与正文一致。失败：数字不兑现、年份过时 |
| Google 显示的标题 | 在目标地域搜目标查询 | 通过：显示你的 title，或更贴近查询的版本。失败：显示半空、过时或错误的文字，按改写一节修 |
| 标题党 | 对照「避免标题党」 | 通过：每条都满足。失败：任何一条不满足 |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。一手资料均于 2026-10-18 打开核对。

- 一手资料：[标题链接](https://developers.google.com/search/docs/appearance/title-link)、[站点名称](https://developers.google.com/search/docs/appearance/site-names)、[有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[精选摘要](https://developers.google.com/search/docs/appearance/featured-snippets)、[Bing 网站管理员指南](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)
- 第三方研究：[Backlinko 自然点击率研究](https://backlinko.com/google-ctr-stats)（2019 年发布，约 400 万条结果）
- 第三方工具口径：[TheCraigHewitt/seomachine](https://github.com/TheCraigHewitt/seomachine)（弱标题词表、多候选流程）；`scripts/markets.json`（长度阈值）
- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · build/seo-content-writer/references/title-formulas.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/build/seo-content-writer/references/title-formulas.md)（Apache-2.0）
