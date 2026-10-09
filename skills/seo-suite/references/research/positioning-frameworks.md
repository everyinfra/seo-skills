# 定位思路与 SEO 落地

## 用途与何时读

做完竞品分析、要决定「我们在搜索结果里以什么身份出现」时读：为首页、产品页、对比页定主张，决定优先做哪些关键词簇，安排页面上的信息先后。竞品事实的整理见 [battlecard-template.md](battlecard-template.md)。

## 定位要回答的四件事

1. **给谁**：目标人群和具体场景。
2. **归在哪一类**：用户搜索和比较时用的品类名，不是内部叫法。
3. **比替代方案强在哪**：替代方案包括直接竞品、通用工具、外包，以及「手工做」「先不做」。
4. **凭什么信**：可展示、可核实的证据，例如演示、数据、案例、公开文档。

写成一句话备用：「面向〔人群与场景〕，〔产品〕是一种〔品类〕，能〔主要收益〕；和〔替代方案〕相比〔差异〕，依据是〔证据〕。」四个空里有一个填不出，定位就还没想清楚。

## 品类策略怎么选

| 策略 | 适合的情况 | 对 SEO 意味着什么 |
|---|---|---|
| 在现有品类里争 | 产品确实在主流品类里有优势 | 品类词需求现成但竞争激烈；先从「品类 + 人群 / 场景」的组合词切入 |
| 切出细分品类 | 差异点足以支撑一个更窄的标签 | 组合词需求较小但意图精准；细分品类名要有解释页，并链回大品类的内容 |
| 开创新品类 | 产品确实不属于任何现有品类 | 新品类名几乎没人搜；靠问题词和旧品类词带来访问，再解释新概念；见效慢，要配合品牌建设 |
| 改变比较标准 | 现有品类的比较方式对你不利 | 用户仍用旧品类词搜索；在旧词下提供按新标准比较的对比页和评测维度说明 |

选择时同时看三件事：差异点有多强、市场要花多少教育成本、现有搜索需求有多少。搜索需求用关键词工具和 Search Console 数据判断（需要你自己的账号），不凭感觉。

## 定位图：辅助找空白

- 两条轴都要是买家真正在乎的维度，并且彼此独立（例如上手难度和能力范围），不要选只对自己有利的轴。
- 按证据放点，包括自己；按「希望的样子」放点没有意义。
- 把替代方案也画上去，不只画直接竞品。
- 看到空白先验证：是真的没人做，还是没人需要。验证靠搜索需求、客户访谈和销售记录。
- 市场变化后重画，旧图不要一直沿用。

## 差异点检验

- **替换测试**：把句中的品牌名换成竞品名后仍然成立，它就不是差异点。
- **证据测试**：拿不出可以对外展示的证据，就只能当内部目标，不能写进页面。
- **耐久度**：单个功能容易被复制；数据积累、方法、对某类人群的长期专注更难复制，更值得作为主张。

竞品说法和用户实际评价之间的落差，可以当作选题线索（例如评价里反复出现的问题）；对外内容只陈述可核实的事实，不做影射。

## 落到 SEO 选题

| 定位要素 | 选题方向 |
|---|---|
| 品类和人群 | 核心关键词簇：品类词加人群、场景、行业修饰，意图判定见 [keyword-intent-taxonomy.md](keyword-intent-taxonomy.md) |
| 用户要解决的问题 | 问题型内容，从问题讲到解决思路，再引出产品 |
| 差异点和证据 | 证据型内容：方法说明、测试与基准、案例、公开数据 |
| 替代方案 | 对比页和替代方案页，做法见 [competitor-page-patterns.md](competitor-page-patterns.md) |

和定位矛盾的词不做，例如产品不免费就不去抢「免费」类查询。选题最终排成主题集群，见 [topic-cluster-templates.md](topic-cluster-templates.md)。

## 落到页面信息层级

1. **标题和 H1**：用用户搜索时用的品类词和场景说明页面是什么，不放内部口号。标题写法见 [title-formulas.md](../content/title-formulas.md)。
2. **首屏**：一句话讲清是什么、给谁、主要收益，紧接最有力的一条证据。
3. **中段**：逐条展开差异点，每条配证据；写清适合谁、不适合谁。
4. **后段**：和替代方案的比较、价格说明、真实的常见问题。
5. **全站一致**：首页、定价页、文档、对比页对同一件事的说法一致；结构化数据只描述页面上可见的内容。

## 交付物

1. 定位陈述，四个要素各附证据。
2. 品类策略的选择和理由，包括搜索需求依据。
3. 差异点清单：主张、证据、耐久度。
4. 定位到 SEO 的映射：定位要素 → 关键词簇 → 负责页面 → 页面上的信息层级。
5. 可选：定位图及放点依据。

## 常见误区

- 定位用内部术语，用户根本不这样搜。
- 把自造的新品类名当作主关键词。
- 差异点没有证据，或者竞品也能说同样的话。
- 标题里塞口号，看不出页面讲什么。
- 各页面对产品的描述互相矛盾。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · research/competitor-analysis/references/positioning-frameworks.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/research/competitor-analysis/references/positioning-frameworks.md)（Apache-2.0）
- 一手资料：[SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)、[标题链接](https://developers.google.com/search/docs/appearance/title-link)、[有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)

---

# (marketingskills 深读 2026-10-09b)

补充吸收 coreyhaines31/marketingskills 的 programmatic-seo、schema、seo-audit、competitor-profiling、competitors 五个技能。

## 程序化 SEO（programmatic-seo 2.1.0）

### 核心原则
- 每页提供**该页独有的价值**，不是模板换变量；100 个好页好过 10000 个薄页。
- 数据可防御性层级：自有原创 > 产品衍生（用户数据）> UGC > 独家授权 > 公共数据（最弱）。
- URL 用**子目录不用子域名**（子目录聚合域权重，子域名拆分它）。
- 12 个 playbook：模板、策展（best X）、换算、对比、案例集、本地（X in Y）、人群（X for Y）、集成（A B integration）、术语表、翻译、目录、实体档案页。可叠层（"best coworking spaces in San Diego" = 策展+本地）。

### 执行框架
关键词模式研究（重复结构、变量、组合总量、聚合量验证）→ 数据源（谁填页、怎么更新）→ 模板设计（含条件化区块保证每页独特性）→ 内链架构（hub-spoke、spoke 互链、防孤儿页）→ 收录策略（高量模式优先、极薄变体 noindex、分类型 sitemap、管理爬虫预算）→ 平台要能承载页数、刷新数据、SSR 渲染、按数据分支、按页控制收录；优先用现有 CMS，不行也挂在主域子路径。

### 质检与常见病
上线前：每页独特价值、标题 meta 唯一、schema 就位、无孤儿页、sitemap 收录。上线后盯收录率、排名、互动、转化，以及薄内容警告与手动操作。常见病：换城市名的薄页、同词蚕食、无需求硬生成页、数据过期、页面为 Google 而非用户做。

## 结构化数据（schema 2.0.2）

- 首选 JSON-LD（Google 推荐，head 或 body 末尾）；一页多类型用 `@graph` 组合。
- **schema.org 合法 ≠ Google 功能资格**：实现前查 Google 当前支持的富结果目录。按该库记载：FAQ 富结果 2026-05-07 起停展（6 月移除文档，政府/健康站例外通道也已关闭）；HowTo 富结果 2023-09 退役；sitelinks 搜索框 2024-11 退役（WebSite 类型仍支持站名）。已退役类型仍可做语义描述，但不要为获得已退役外观而实现，也不要把富结果测试测不出退役功能当作实现坏了。
- 常用类型速查：Organization（name/url）、Article（headline/image/datePublished/author）、Product（name/image/offers 含价格与库存）、SoftwareApplication、FAQPage（mainEntity 问答数组）、BreadcrumbList（itemListElement）、LocalBusiness、Event。
- 校验：Rich Results Test（测 Google 当前支持项，会渲染 JS）、validator.schema.org、Search Console 增强报告。日期 ISO 8601、URL 绝对地址、枚举值精确；schema 必须与页面可见内容一致——标记不存在的内容是作弊。

## SEO 审计（seo-audit 2.2.0）

### 优先级顺序
可爬可收 → 技术底座 → 页面优化 → 内容质量 → 权威与外链。基础打好后**最快收益在 8-20 位页面**（striking distance），推上首页比对新词从零做快。

### 工具陷阱：schema 检测
`web_fetch`/curl 抓不到 JS 注入的 JSON-LD（Yoast/RankMath 等常客户端注入，转换时 script 被剥掉）。判断有无 schema 要用：浏览器渲染后跑 `document.querySelectorAll('script[type="application/ld+json"]')`、Rich Results Test（渲染 JS）、或 Screaming Frog 导出。**只凭静态抓取报「无 schema」是假发现**。

### 技术检查要点
- CWV 阈值：LCP < 2.5s、INP < 200ms、CLS < 0.1。
- 收录病：误 noindex、canonical 指错方向、重定向链/环、软 404、无 canonical 的重复。
- hreflang（多语言）：每页含自引用、互为回链（单向则整对被弃）、代码 en-GB 不写 en-UK、有 x-default；10+ locale 优先 sitemap 方案。**canonical 与 hreflang 冲突时 canonical 赢**；跨语言 canonical（法语页 canonical 到英语页）会整站压制该语言收录。
- 多语言内容：只翻导航模板不翻正文=重复页；大量薄 locale 页拖累全站 helpful content 信号；做不了真正有用的 locale 页就不做。
- 分站点型常见病：SaaS（产品页太薄、缺对比/替代页、博客与产品页不联动）、电商（薄分类页、参数化导航重复、缺 product schema）、内容站（不刷新旧文、蚕食、无作者页）、本地（NAP 不一致、缺本地 schema、GBP 未优化）。

### 报告格式
每个发现：问题 → 影响（高/中/低）→ 证据 → 修法 → 优先级；结尾按「阻断收录的致命项 / 高影响改进 / 快赢 / 长期项」排序。

## 竞品建档（competitor-profiling 2.1.3）

### 证据三层与措辞纪律
- **Observed**（来源+日期）/ **Inferred**（标注推断及改变决策的置信度）/ **Implication**（以问题或选项呈现，不下结论）三层 visibly 分开。
- **没观察到 ≠ 没有**：写「在〔检查过的页面〕上未见，截至〔日期〕」，不写「他们没有」；用于对比页等公开场合前要在其文档或试用中确认。
- **不猜动机**：记「把 SSO 移到 Enterprise 档」，不写「因为要上探高端市场」。
- 快照思维：所有档案带生成日期；单次抓取支撑不了「他们多年没改价」这类主张，只有带日期的历史快照能。

### 流程
抓站（首页/定价/功能/关于/客户/集成/changelog 各提什么字段）→ SEO 数据（域名权重、反链与引荐域、收录词量与 top3/10、预估流量与价值、最高流量页、**域名级有机竞对**——会翻出你没考虑过的竞对）→ 评测挖掘（G2/Capterra 主题与代表引语）→ 交叉验证（站上称 1 万客户，流量反链撑不撑得起这个体量）。原始数据全部落盘存档（raw/日期/ 页），便于复跑与 diff。默认 quick scan（首页+定价+域名概览），除非点名深挖或竞对≤3。

### 输出
每竞对一份同构档案（可横比）+ `_summary.md`：格局综述、关键指标横比表、定位图（各竞对落点）、3-5 条战略观察、市场空白。更新顺序：定价页最先（最易变）、SEO 月度、changelog、生成日期与 Change Log。

## 竞品对比页（competitors 2.3.0）

### 四种格式
| 格式 | 意图 | URL 模式 |
|---|---|---|
| 〔竞品〕alternative（单数） | 铁了心要换 | /alternatives/[竞品] |
| 〔竞品〕alternatives（复数） | 早期调研 | /alternatives/[竞品]-alternatives |
| 你 vs 〔竞品〕 | 直接对比你 | /vs/[竞品] |
| 〔竞品A〕vs〔竞品B〕 | 比较两个对手，你是第三选项 | /compare/a-vs-b |

复数替代页要列 4-7 个**真实**替代品（你排第一但给真选项），诚实帮忙才排得好、转得动。

### 证据纪律（公开主张要经得起对方团队读）
- 「未列出」≠「没有」；写「截至 X 年 X 月其定价页未列」或删行；✗ 只有对方文档或试用确认缺失才能用。
- 竞品事实全部带 as-of 日期，重发布前复验；季度核定价与重大功能、年度全量刷新。
- 说变化不说动机；事实/解读/建议三层分开。

### AI 答案预期
自排榜单页常能赚到 AI 答案的**引用**，但 AI 是否**推荐**你取决于站外共识（评测、论坛、分析师）——新品牌自排第一，可能 AI 答案里出现的是竞品而你只拿到引用。仍为搜索意图和品类框架发布，但预期要设对。

### 内容架构
每竞对一份集中数据档案（定位/定价/强弱项/适合谁/常见抱怨/迁移备注）作为单一事实源，更新传导到所有对比页，避免多处改漏。存量资产审计：逐条列主张→带日期复验→标记 Current / Changed / Unverifiable（软化或删）/ Overclaimed（改写成证据能撑的表述）→ 公开页优先于话术再优先于内部文档修。

### 来源（marketingskills 深读 2026-10-09b）
- [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) `skills/programmatic-seo/SKILL.md`（v2.1.0）、`skills/schema/SKILL.md`（v2.0.2）、`skills/seo-audit/SKILL.md`（v2.2.0）、`skills/competitor-profiling/SKILL.md`（v2.1.3）、`skills/competitors/SKILL.md`（v2.3.0）（MIT）
- FAQ 富结果停展（2026-05-07）等 Google 功能状态为该库记载，实操前以 [Google 功能更新日志](https://developers.google.com/search/updates) 当日状态为准
