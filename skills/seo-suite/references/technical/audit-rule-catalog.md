# 审计规则全目录(SEOmator 373 规则,源码深读)

> 来源:seo-skills/seo-audit-skill v5.1.0 `docs/SEO-AUDIT-RULES.md` 全文(2026-10-09 深 clone 吸收)。
> 三态计分:Pass=100 / Warn=50 / Fail=0;总分=类别加权平均,**档位 90=A / 70=B / 50=C / <50=D-F**。
> **20 类权重表已吸收于 [scoring-rubric.md](scoring-rubric.md)「完全装载」节,不重抄**(Core 11%/Perf 10%/Links·Images·Security 各 8%/Tech·A11y 各 7%/Crawl·SD·Content·JS 各 5%/Social·E-E-A-T·URL·Redirects 各 3%/Mobile·i18n·HTMLval·AI-GEO 各 2%/Legal 1%)。
> 三类横切机制先记住,后面表格反复引用:
> - **crawl 模式专属**(`--crawl`):依赖多页爬取的跨页状态;单页审计时报 not measured(权重 0 不计分)。涉及 15 条 crawl-\* + 部分 links-inbound-\*/content-duplicate-\*/i18n 入向规则。
> - **渲染专属**(`--no-cwv` 时跳过):带"requires render"标记的 per-asset 规则,数据来自 Playwright 渲染。
> - **TOML 开关**:`[rules] disable=["core-*"]` 按前缀禁类;`enable=["core-*","perf-*"]+disable=["*"]` 只留指定类。

---

## 〇、解释层规范(Sitebulb 式,2026-10-10 增补)

> 结构与文案纪律来自 [borrow-specs.md](../research/borrow-specs.md) A2 节(Sitebulb 九节结构 + SF 320 条 issue 矩阵实证)。**各节表格仍是全量索引、永不删行**;解释层第一波覆盖 P0/P1(79 条)、第二波增补 medium/low 高价值家族(44 条)、第三批收口可用性与卫生家族(47 条:Technical SEO 10/Security 6/Mobile 6/Links 6/HTML Validation 5/Content 5/Redirects 3/Core SEO 2/Crawlability 2/i18n 1/Performance 1),本版累计 **170 条**,其余规则见文末"未覆盖规则"。

- **字段固定**:每条目 = 规则 ID 标题 + 元信息行(名称/类型/优先级/输出)+ what/why/trigger/caveat/fix/export/seealso 八段。条目标题层级随所属节深一级(一/三节 `###`,四节 `####`)。
- **两轴哲学**:类型(issue|warning|opportunity)× 优先级(critical|high|medium|low|insight)独立打分。**Opportunity 永不给 critical**(SF 320 条矩阵实证);"坏信号>缺信号"——主动矛盾(信号冲突/指向坏目标)排 critical-high,单纯缺失排 medium-low。
- **输出级别与源表三态对齐**:CRITICAL=fail(计 0)/WARN=warn(计 50)/INFO=info(仅报告不计分)。优先级是建议层,个别"缺信号但源表 fail"的规则(如 canonical 缺失、title 缺失)输出 CRITICAL 而建议优先级降档,条目内注明——这是两轴哲学对源表的显式校准,不是抄写错误。
- **caveat 公式**:"X 不(直接)影响 SEO,然而影响 Y,所以一般建议 Z。但在{某种页面/规模}下可合理不修"。三个常驻样本:title 长度高度主观(Google 按像素截断且常自行改写);重复 title/description 若只涉几页可能无实质影响,数千页模板级重复才可能触发质量算法;缺 alt 不伤害页面只是错失描述,**装饰图空 alt 是正确做法**。
- **ID 纪律**:一/三节表格中的规则 ID 为源目录原文;第四节浓缩表内多数规则未公布 ID,条目 ID 按家族命名法推得并标 [待核]。阈值一律照抄源表,源表未公布的分型口径标 [待核],不发明新阈值。
- **横切机制沿用**:标 ⛏ 的条目仅 crawl 模式测量,单页审计报 not measured(权重 0);渲染专属条目 `--no-cwv` 时跳过。

---

## 一、重点展开:Crawlability(38 条,我们此前覆盖最薄)

审计索引信号、sitemap 冲突、canonical 链与分页。**15 条跨页规则仅 crawl 模式测量**(表内标 ⛏)。

| 规则 ID | 名称 | 严重度 | 判定阈值/要点 |
|---|---|---|---|
| `crawl-schema-noindex-conflict` | Schema+Noindex 冲突 | fail | noindex 页上存在富结果 schema |
| `crawl-pagination-canonical` | 分页 canonical | warn/fail | 每个分页页须自引用 canonical;全指向第 1 页=错 |
| `crawl-sitemap-domain` | Sitemap 域名 | warn/fail | 所有 URL 须匹配 sitemap 宿主域 |
| `crawl-noindex-in-sitemap` | noindex 入 sitemap | fail | 矛盾信号,二选一:出 sitemap 或删 noindex |
| `crawl-indexability-conflict` | 索引性冲突 | warn | robots.txt Disallow 与 noindex meta **同时用**——不被爬则 noindex 读不到 |
| `crawl-canonical-redirect` | canonical 指向重定向 | warn/fail | canonical 应直指最终 URL |
| `crawl-sitemap-url-limit` | Sitemap 条数上限 | warn | >50,000 URL 超限(超限整文件作废) |
| `crawl-sitemap-size-limit` | Sitemap 体积上限 | warn | >50MB 未压缩超限 |
| `crawl-sitemap-duplicate-urls` | 单文件内重复 URL | warn | 同一 sitemap 内重复条目 |
| `crawl-sitemap-orphan-urls` | Sitemap 孤儿 URL | warn | 仅在 sitemap、站内无链接指向 |
| `crawl-blocked-resources` | 屏蔽 CSS/JS | warn | robots.txt Disallow 挡住渲染资源 |
| `crawl-blocked-images` | 屏蔽图片 | fail | 图片 URL 被 Disallow(RFC 9309 匹配器)→ 无法进图片搜索 |
| `crawl-crawl-delay` | crawl-delay | info | 仅报告,不扣分 |
| `crawl-sitemap-in-robotstxt` | robots.txt 缺 Sitemap 行 | warn | 应加 `Sitemap: https://…/sitemap.xml` |
| `crawl-sitemap-lastmod` | lastmod 质量 | warn | 非法/未来日期/整文件同日 bulk 值(与 C2 lastmod 验真同源) |
| `crawl-pagination-broken` | 分页断链 | fail | 分页链接 404 |
| `crawl-pagination-loop` | 分页环 | fail | 分页链接成环 |
| `crawl-pagination-sequence` | 分页序号缺口 | warn | ?page=N 序列跳号/不一致 |
| `crawl-pagination-noindex` | 分页被 noindex | warn | 分页页应可索引 |
| `crawl-pagination-orphaned` | 分页孤儿 | warn | 分页系列未从主导航链接 |
| `crawl-pagination-isolated` ⛏ | 分页 URL 无入链 | fail | 形如 `?page=N`//`page/N`/rel=next-prev,但无普通 `<a>` 指向(爬虫靠锚点到的页必然有入链,此规则抓"另径发现"的分页) |
| `crawl-sitemap-non-200` ⛏ | Sitemap 内非 200 | warn/fail | 与爬取状态码交叉:**4xx/5xx=fail,3xx 与超时=warn**;爬虫未到的 URL 不判(orphan 规则管) |
| `crawl-sitemap-non-canonical` ⛏ | Sitemap 内非规范 URL | fail | sitemap 说"索引这个"、canonical 说"索引那个",canonical 赢 |
| `crawl-sitemap-disallowed` ⛏ | Sitemap 内被 Disallow | fail | 与 robots.txt 直接矛盾;robots.txt 无内容且无任何 Disallow 时报 unmeasured 而非空过 |
| `crawl-sitemap-cross-duplicates` ⛏ | 一 URL 多 sitemap | warn | 跨 sitemap 文档重复声明(区别于单文件内重复);信息级,爬虫侧会去重 |
| `crawl-canonical-to-noindex` ⛏ | canonical→noindex | fail | 目标自身 noindex;自引用通过;未爬到的目标报 unmeasured |
| `crawl-canonical-to-disallowed` ⛏ | canonical→Disallow | fail | 目标被 robots.txt 禁——委托了一个抓不到的 URL |
| `crawl-canonical-chain` ⛏ | canonical 链 | warn | A→B→C,每跳衰减信号;环由 loop 规则报 |
| `crawl-canonical-loop` ⛏ | canonical 环 | fail | 跟踪目标回到已访问 URL,无最终目的地 |
| `crawl-hreflang-to-noindex` ⛏ | hreflang→noindex | fail | 出向注解指向 noindex 页,语言簇断裂 |
| `crawl-hreflang-to-disallowed` ⛏ | hreflang→Disallow | fail | 出向注解指向被禁页 |
| `crawl-hreflang-disallowed-target` ⛏ | 被禁页收 hreflang | fail | 镜像方向:本页被 Disallow 而他人指它——回链永远无法确认 |
| `crawl-hreflang-incoming-conflict` ⛏ | 入向 hreflang 冲突 | fail | 他页对同一 URL 标了不同语言码;本页自己出的注解不计(i18n-hreflang-conflicting 管),x-default 永不冲突 |
| `crawl-hreflang-reciprocity` ⛏ | hreflang 回链 | warn | 本页的每个 hreflang 目标都须反向标注本页;warn 因缺回链多为模板遗漏;未爬到的目标跳过 |
| `crawl-isolated-url` ⛏ | 孤立 URL | fail | 只经 canonical/重定向/sitemap/noindex,follow 路径/其他孤立页发现,**无任何锚点入链**;链接者全为 noindex,follow 或自身孤立(一次传播)也 fail;爬取入口必过 |
| `crawl-canonical-form-drift` ⛏ | canonical 形态漂移 | warn | 各页 canonical 在 www/协议/尾斜杠上不一致 |
| `crawl-sitemap-date-drift` ⛏ | 日期漂移 | warn | sitemap lastmod 与页面 schema dateModified 同日(疑似 build 戳同步写) |
| `crawl-pdf-size` | 链接 PDF 体积 | warn | Content-Length **>10MB** 警;HEAD 最多查 **8 个** PDF;缺长度跳过;无 PDF 链接通过 |

**为什么这 38 条值钱**:把"孤立/孤立传播""入向 vs 出向 hreflang 分开判定""sitemap×robots×canonical×noindex 四信号两两交叉"做成了独立规则——多数工具只做其中三四条。孤立 URL 的"一次传播"判定(链接者也孤立→你也孤立)是图算法思维,单页工具做不到。

**解释层(36 条;第三批另补 pdf-size/crawl-delay 两条,38 条全量)**

### crawl-canonical-to-noindex ⛏
- 名称/类型: canonical 指向 noindex 页 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: 该 URL 把自己的规范版本委托给了一个自身声明 noindex 的页面——你对引擎说"去索引 B",B 自己说"别索引我"。
**为什么(why)**: canonical 是对索引目的地的投票,noindex 是对同一目的地的否决,两条指令互相取消:Google 通常两个都不听,回退到自行选择版本(常是当前 URL),信号合并失败的同时还暴露了模板失控。对用户无直接影响,但这类矛盾几乎总是模板 bug——今天丢的是信号,明天丢的可能是引擎对你全站 canonical 的信任度。
**触发(trigger)**: 1) 取本页 canonical 目标 URL;2) 抓取目标页,读其 meta robots / X-Robots-Tag;3) 目标含 noindex(或 none)即 fail;4) 自引用 canonical 通过;5) 目标未爬到报 unmeasured(既不算过也不算挂)。
```html
<!-- fail:页面 A -->
<link rel="canonical" href="https://example.com/b">
<!-- 页面 B(https://example.com/b)的 head -->
<meta name="robots" content="noindex">

<!-- pass:页面 A 自引用 -->
<link rel="canonical" href="https://example.com/a">
```
**不修的条件(caveat)**: canonical 是提示不是指令,此矛盾不会直接惩罚 SEO,然而它让整组重复页失去合并入口,所以一般建议二选一删信号。但在刻意用 noindex 页当 canonical 目标的少数场景(如 faceted search 的黑名单页)下,可视为已知取舍暂不修。
**修复(fix)**: 分两型。想让 B 当规范页 → 删掉 B 上的 noindex(或 X-Robots-Tag);B 不该当规范页 → 把 A 的 canonical 改回自引用或指向真正可索引的规范 URL;若 A 本身就不该索引 → 直接给 A noindex 并移出 sitemap,别用 canonical 间接表达。
**导出(export)**: Reports > Crawlability > Canonical to Noindex Page(附受影响 URL 清单)
**关联(seealso)**: core-canonical-to-noindex、crawl-hreflang-to-noindex、crawl-noindex-in-sitemap;[redirects-canonical.md](redirects-canonical.md) 第三节冲突矩阵、[robots-txt-reference.md](robots-txt-reference.md)

### crawl-canonical-to-disallowed ⛏
- 名称/类型: canonical 指向 robots.txt 禁止的 URL —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: 该 URL 把规范票投给了一个 robots.txt Disallow 的页面——委托了一个引擎永远无法抓取确认的 URL。
**为什么(why)**: Google 必须能抓取 canonical 目标才能完成信号合并;Disallow 让"确认合并"永远无法完成,重复版本各自为政,外链与内部权重分裂在不同 URL 上。用户侧无感,但投给非规范版本的外链票全部浪费——这是纯信号层损耗。
**触发(trigger)**: 1) 取 canonical 目标;2) 用 RFC 9309 匹配器对 robots.txt 判定;3) 目标被任何 User-agent 组 Disallow 即 fail;4) 未爬到目标不判。
```html
<!-- fail:robots.txt 有 Disallow: /print/ -->
<link rel="canonical" href="https://example.com/print/article">

<!-- pass:canonical 指向可抓取的规范 URL -->
<link rel="canonical" href="https://example.com/article">
```
**不修的条件(caveat)**: 引擎仍可能靠内容相似度自行合并,不构成惩罚,然而合并置信度大降,所以一般建议解除矛盾。但在目标确属内部页、你根本不想要合并的场景,把 canonical 改自引用即可,不必开 Disallow。
**修复(fix)**: 要合并 → 从 robots.txt 移除该路径(改用 noindex 或 meta 层控制索引);不要合并 → canonical 改自引用。永远不要 canonical 到 Disallow 路径。
**导出(export)**: Reports > Crawlability > Canonical to Disallowed URL
**关联(seealso)**: crawl-indexability-conflict、crawl-canonical-to-noindex;[redirects-canonical.md](redirects-canonical.md)、[robots-txt-reference.md](robots-txt-reference.md)

### crawl-canonical-loop ⛏
- 名称/类型: canonical 环 —— issue · 优先级 high · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: 该 URL 的 canonical 指向链绕回自身或途中任一 URL,整条链不存在最终规范页。
**为什么(why)**: 引擎发现环后丢弃整串 canonical,合并彻底失败;外链与内部权重在环上各页间分裂。环几乎总来自模板互相引用或迁移遗留,常成对成批出现在整站层面——找到一处就该 lint 全站。
**触发(trigger)**: 1) 从本页 canonical 出发,逐跳抓取目标页的 canonical;2) 目标集合出现重复(回到起点或任一途经 URL)即 fail;3) 单跳自引用通过。
```html
<!-- fail:A 页 --> <link rel="canonical" href="https://example.com/b">
<!--     B 页 --> <link rel="canonical" href="https://example.com/a">
<!-- pass:A 页 --> <link rel="canonical" href="https://example.com/a">
```
**不修的条件(caveat)**: 环不直接惩罚排名,然而整组重复页失去合并,所以一般建议立即打破。但若环只涉及两个已知低价值的存档页,可排期后修,不必当成事故。
**修复(fix)**: 找出本应最终规范的那一页让它自引用,其余全部直指它;检查模板变量是不是把排序/分页参数写进了 canonical。
**导出(export)**: Reports > Crawlability > Canonical Loop
**关联(seealso)**: core-canonical-loop、crawl-canonical-chain;[redirects-canonical.md](redirects-canonical.md)

### crawl-canonical-chain ⛏
- 名称/类型: canonical 链 —— warning · 优先级 medium · 输出 WARN(源表 warn;仅 crawl 模式)
**这意味(what)**: 该 URL 的 canonical 不是直指最终规范页,中间至少还隔一跳(A→B→C)。
**为什么(why)**: 每一跳都增加引擎放弃跟踪的概率,外链信号在链上逐跳衰减;Google 明确建议 canonical 直指最终 URL。对用户无感,是纯引擎效率问题。
**触发(trigger)**: 1) 跟踪本页 canonical 目标;2) 目标页的 canonical 又指向第三页即触发;3) 记录并输出全链,链长=跳数。
```html
<!-- fail:A → B → C(两跳) -->
A: <link rel="canonical" href="/b">   B: <link rel="canonical" href="/c">
<!-- pass:A → C 直连,C 自引用 -->
```
**不修的条件(caveat)**: 链是效率问题不是错误,引擎多数情况能跟到终点,然而每跳都衰减合并置信度,所以一般建议拉直。但迁移过渡期的一跳临时链可以接受,终点稳定后再收。
**修复(fix)**: 让所有前驱页直指链终点;顺带验证终点返回 200 且自引用。
**导出(export)**: Reports > Crawlability > Canonical Chain
**关联(seealso)**: crawl-canonical-redirect、crawl-canonical-loop;[redirects-canonical.md](redirects-canonical.md)

### crawl-canonical-redirect
- 名称/类型: canonical 指向重定向 —— warning · 优先级 high · 输出 WARN/CRITICAL(源表 warn/fail;基础判 3xx 目标=warn,升 fail 的分型条件源表未公布[待核])
**这意味(what)**: 该 URL 的 canonical 目标自身返回 3xx 重定向,不是最终 URL。
**为什么(why)**: 引擎要多跳一次才能确认规范页,每跳都有丢弃风险,与"canonical 直指最终 URL"的官方建议相悖。常与迁移遗留共存(HTTP→HTTPS、加尾斜杠批量重定向)。
**触发(trigger)**: 1) 请求 canonical 目标;2) 返回 3xx 即触发;3) 记录 Location 链的最终目标。
```html
<!-- fail:目标 /b 返回 301 → /c -->
<link rel="canonical" href="https://example.com/b">
<!-- pass:直指最终 200 的 /c -->
<link rel="canonical" href="https://example.com/c">
```
**不修的条件(caveat)**: 单跳重定向引擎能跟随,实际损耗有限,然而它总与 canonical-chain/sitemap 非最终 URL 同现,所以一般建议一次拉直全站。
**修复(fix)**: 把 canonical 改写为重定向链的最终 URL,并确认该 URL 返回 200 且自引用。
**导出(export)**: Reports > Crawlability > Canonical to Redirect
**关联(seealso)**: crawl-canonical-chain、links-redirect-chain;[redirects-canonical.md](redirects-canonical.md)

### crawl-canonical-form-drift ⛏
- 名称/类型: canonical 形态漂移 —— warning · 优先级 low · 输出 WARN(源表 warn;仅 crawl 模式)
**这意味(what)**: 该 URL 的 canonical 在 www/协议/尾斜杠形态上与站点主流形态不一致。
**为什么(why)**: 形态漂移制造"疑似不同 URL"的噪音,提高引擎误判规范版本的概率;极端时会诱发同一内容的多个形态都被索引。是站点级一致性问题,单页视角看不到。
**触发(trigger)**: 1) 对全站各页 canonical 提取形态四元组(www/协议/尾斜杠/host 大小写);2) 聚类;3) 少数派形态即触发。
```html
<!-- 漂移:多数页用 https://www. ,该页却是 -->
<link rel="canonical" href="http://example.com/page/">
```
**不修的条件(caveat)**: 漂移不直接影响单页 SEO,然而降低规范化一致性,所以一般建议统一。但纯尾斜杠漂移低优先,混合协议(http canonical on https 页)必须修。
**修复(fix)**: 定一种规范形态(建议 HTTPS+单 host+固定尾斜杠策略),模板统一输出;配合 301 把其余形态收紧到规范形。
**导出(export)**: Reports > Crawlability > Canonical Form Drift(Summary)
**关联(seealso)**: core-canonical-http-mismatch;[redirects-canonical.md](redirects-canonical.md)

### crawl-hreflang-to-noindex ⛏
- 名称/类型: hreflang 指向 noindex 页 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: 该 URL 的某条 hreflang 注解指向一个 noindex 页,语言簇在那一格断裂。
**为什么(why)**: hreflang 簇要求每个成员可索引;指向 noindex 页意味着该语言版本对引擎"存在但不可选",Google 的处理倾向是忽略整簇注解——为一页牺牲全簇的语言对应,各语言版在对应市场的排名连锁受损。用户侧:异地用户失去语言切换目标。
**触发(trigger)**: 1) 枚举本页全部 hreflang 目标;2) 逐个抓取,读 meta robots/X-Robots-Tag;3) 任一目标含 noindex 即 fail。
```html
<!-- fail:A(en)指 B(de),B 自身 noindex -->
<link rel="alternate" hreflang="de" href="https://example.com/de/">
<!-- B 的 head --><meta name="robots" content="noindex">
```
**不修的条件(caveat)**: hreflang 是提示,簇内单点 noindex 不会惩罚,然而整簇被忽略的代价远大于单页,所以一般建议先保簇完整。但在某语言版被策略性下线(临时停售市场)时,应把它从注解集里一并移除,而不是留一个 noindex 成员挂在簇里。
**修复(fix)**: 要该语言版 → 删其 noindex;不要 → 从所有页面的 hreflang 集移除该成员(HTML/HTTP 头/sitemap 三种载体都查),保持簇闭合。
**导出(export)**: Reports > Internationalization > Hreflang to Noindex
**关联(seealso)**: i18n-hreflang-to-noindex、crawl-canonical-to-noindex;[hreflang-validation.md](hreflang-validation.md)

### crawl-hreflang-to-disallowed ⛏
- 名称/类型: hreflang 指向 Disallow 页 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: 该 URL 的 hreflang 指向被 robots.txt Disallow 的页面——注解存在,但引擎抓不到目标,无法确认回链。
**为什么(why)**: hreflang 有效性依赖双向可抓取;Disallow 目标让注解变成死指针,Google 的口径是这类注解应整簇忽略。语言版在该市场失去互相支撑,用户也到不了被屏蔽的版本。
**触发(trigger)**: 1) 枚举 hreflang 目标;2) RFC 9309 匹配 robots.txt;3) 任一被 Disallow 即 fail。
**不修的条件(caveat)**: 与 canonical→Disallow 同理,矛盾不惩罚但合并失效;正确解几乎总是"别屏蔽语言版",极少有合理豁免。
**修复(fix)**: 移除该语言的 robots 屏蔽(索引控制改用 noindex/canonical 表达);或从注解集删掉该成员。
**导出(export)**: Reports > Internationalization > Hreflang to Disallowed
**关联(seealso)**: crawl-canonical-to-disallowed、crawl-hreflang-disallowed-target;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-hreflang-disallowed-target ⛏
- 名称/类型: 被禁页收 hreflang —— issue · 优先级 high · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: 该 URL 自身被 robots.txt Disallow,却仍被其他页面的 hreflang 指向——别人指你,而引擎永远读不到你来确认回链。
**为什么(why)**: 镜像方向的问题:即使你删掉自己出向的注解,入向注解仍在引用一个不可抓取页,簇依然不闭合。常见于"先用 robots 屏蔽了 staging/内部页,忘了摘掉全站模板里的 hreflang"。
**触发(trigger)**: 1) 本页 URL 被 robots.txt Disallow;2) 爬取中存在任一他页 hreflang 指向本页;3) 两者同时成立即 fail。
**不修的条件(caveat)**: 若该页本就该不可抓(内部工具页),正确解是让引用方移除注解,而不是给 Disallow 页开绿灯。
**修复(fix)**: 摘除全部指向本页的 hreflang(在引用页/HTTP 头/sitemap 三种载体里找);或本页恢复可抓取。
**导出(export)**: Reports > Internationalization > Disallowed Hreflang Target
**关联(seealso)**: crawl-hreflang-to-disallowed、crawl-hreflang-reciprocity;[hreflang-validation.md](hreflang-validation.md)

### crawl-hreflang-incoming-conflict ⛏
- 名称/类型: 入向 hreflang 冲突 —— issue · 优先级 high · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: 两个以上页面用**不同语言码**的 hreflang 指向本页,本页的语言身份被外部声明搞乱。
**为什么(why)**: 引擎按"每 URL 一个语言身份"建簇;入向声明冲突时矛盾注解可能被丢弃,本页丢失簇成员资格,失去各语言版互链加成。注意判定边界:本页自己出向的注解不计入(那归 i18n-hreflang-conflicting 管);x-default 永不冲突(回退不是冲突)。
**触发(trigger)**: 1) 汇总爬取中所有指向本页的 hreflang;2) 语言码去重;3) 出现 ≥2 个不同语言码即 fail;x-default 豁免。
```html
<!-- fail:A 页 hreflang="en" → /x ;B 页 hreflang="de" → /x -->
<!-- 除非 /x 真是双语页且自身声明与内容一致 -->
```
**不修的条件(caveat)**: 少数多语言单页(如加拿大英法双语页)天然会被两种码指向——若本页自身 lang 与内容确实双语,可在报告标注豁免。
**修复(fix)**: 找到错误声明方改码;双语内容页应拆分为独立 URL 或让自身注解与主语言一致。
**导出(export)**: Reports > Internationalization > Incoming Hreflang Conflict
**关联(seealso)**: i18n-hreflang-conflicting、i18n-hreflang-incoming-invalid;[hreflang-validation.md](hreflang-validation.md)

### crawl-hreflang-reciprocity ⛏
- 名称/类型: hreflang 回链缺失 —— warning · 优先级 high · 输出 WARN(源表 warn;仅 crawl 模式)
**这意味(what)**: 该 URL 的某个 hreflang 目标没有反向标注回来——A 指 B,B 不指 A。
**为什么(why)**: Google 官方要求注解双向(return link);缺回链的注解被忽略,该语言对应关系失效——德国 SERP 里看不到德语版,簇内信号也无法传递。源表给 warn 而非 fail,因为缺回链多为模板遗漏(某语言模板忘了循环变量),影响明确、修复成本低。未爬到的目标跳过不判。
**触发(trigger)**: 1) 枚举本页出向 hreflang(码,URL);2) 抓取各目标页注解集;3) 任一目标缺少"指向本页且码对应"的条目即触发。
**不修的条件(caveat)**: 回链缺失不惩罚,只是该对应关系被忽略;但既然部署了 hreflang,半套等于零套,建议一次修齐。
**修复(fix)**: 双向成对生成——优先在 sitemap 载体集中维护双向关系,模板化生成,杜绝手写单边;修完用 hreflang_cluster.py 复验。
**导出(export)**: Reports > Internationalization > Missing Return Links
**关联(seealso)**: i18n-hreflang-return-links;[hreflang-validation.md](hreflang-validation.md) 八检之一

### crawl-isolated-url ⛏
- 名称/类型: 孤立 URL —— issue · 优先级 high · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: 该 URL 只能经 canonical/重定向/sitemap/noindex 或其他孤立页被发现,站内没有任何一个可跟随锚点(`<a href>`)指向它。
**为什么(why)**: 无入链≈无 PageRank 流入、无发现路径;Google 明确"链接是发现页面的主要方式",sitemap 只是补充。孤岛页即使被索引也排名羸弱。**一次传播判定**:若链接者全部 noindex/nofollow、或链接者自身也是孤立页,本页仍判孤立——因为在链接图上权重传不到你。爬取入口(种子 URL)必过此判。
**触发(trigger)**: 1) 构建全站 follow 链接图(锚点入链,nofollow 不算边);2) 入链数=0 即 fail;3) 入链全来自 noindex 页/nofollow 链/自身孤立的页面 → 传播判定仍 fail;4) 爬取种子入口豁免。
**不修的条件(caveat)**: 孤立不等于不索引(sitemap 还能兜底),然而无链接投票的页面几乎不可能竞争排名,所以一般建议接入内链。但过渡页(法律存档)、仅靠外链引流的落地页可合理保持孤立。
**修复(fix)**: 从相关正文页加描述性锚文本内链;检查导航/分类页是否漏链;若页面本该删除,301 到最近亲页面而不是留着孤立。
**导出(export)**: Reports > Crawlability > Isolated URL(+Inlinks 变体)
**关联(seealso)**: crawl-sitemap-orphan-urls、links-depth;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-schema-noindex-conflict
- 名称/类型: Schema 与 noindex 冲突 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 自身 noindex,页面上却部署着富结果 schema(Product/Recipe/Review 等)。
**为什么(why)**: noindex 页不参与排名,富结果结构化数据在其上是纯负载:浪费维护成本,且若日后解除 noindex,过期 schema 可能产出不符预期的富结果。语义矛盾也说明模板治理混乱——索引意图与标记意图分属两拨人管。
**触发(trigger)**: 1) 本页 meta robots/X-Robots-Tag 含 noindex;2) 页面存在 Google 富结果类型 schema(按富结果目录判定);3) 两者同时成立即 fail。
```html
<!-- fail:noindex 页上挂 Product 富结果 -->
<meta name="robots" content="noindex">
<script type="application/ld+json">{"@type":"Product","name":"…"}</script>
```
**不修的条件(caveat)**: schema 不因 noindex 产生负面信号,然而零收益纯成本,所以一般建议移除或解除 noindex。但预发布页(暂 noindex 待上线)保留 schema 属合理过渡态。
**修复(fix)**: 页面要索引 → 删 noindex;不要 → 删该页富结果 schema(Organization/WebSite 这类全站级标记无妨保留)。
**导出(export)**: Reports > Structured Data > Schema on Noindex Page
**关联(seealso)**: crawl-noindex-in-sitemap;[validation-guide.md](validation-guide.md)

### crawl-noindex-in-sitemap
- 名称/类型: noindex 入 sitemap —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 声明 noindex,却被列在 sitemap 里——两套系统在索引问题上说了相反的话。
**为什么(why)**: sitemap 的语义是"请索引此 URL",noindex 的语义是"请别索引此 URL"。引擎会尊重 noindex,不会因矛盾惩罚,但重复矛盾会稀释 sitemap 整体质量信号、浪费抓取配额,也暴露 sitemap 生成器与 CMS 索引设置脱钩。
**触发(trigger)**: 1) 取 sitemap 全 URL 集;2) 逐页读 meta robots/X-Robots-Tag;3) 含 noindex(或 none)且在 sitemap 即 fail。
**不修的条件(caveat)**: 引擎以 noindex 为准,不惩罚,然而 sitemap 的"推荐配额"被浪费,所以一般建议二选一。但刚加 noindex 还没重新生成 sitemap 的过渡态可短暂存在,下个生成周期自愈。
**修复(fix)**: 不该索引 → sitemap 生成器加过滤把它移除;该索引 → 删 noindex。修完在 GSC 重新提交 sitemap。
**导出(export)**: Reports > Sitemaps > Noindex URLs in Sitemap
**关联(seealso)**: crawl-sitemap-disallowed、crawl-sitemap-non-canonical、core-robots-meta;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-blocked-images
- 名称/类型: 屏蔽图片 —— issue · 优先级 high · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 上的图片(或图片自身 URL)被 robots.txt Disallow,无法进入图片搜索。
**为什么(why)**: Google Images 靠 Googlebot-Image 抓取;图片路径被通用 Disallow 覆盖时,图片不被收录,页面在图片搜索的展现随之受损。电商/媒体站的这类损失常被低估——图片搜索是实打实的流量入口。
**触发(trigger)**: 1) 收集页面图片 URL(img src/srcset);2) 按 RFC 9309 匹配 robots.txt(通用组 `User-agent: *` 同样生效);3) 任一被 Disallow 即 fail。
```text
# fail:robots.txt
Disallow: /uploads/
# 修正:放行图片目录
Allow: /uploads/$
```
**不修的条件(caveat)**: 屏蔽图片不影响网页搜索排名,然而放弃整个图片渠道,所以一般建议放行。但版权敏感图(付费图库预览)被 Disallow 是刻意合规,勿修。
**修复(fix)**: robots.txt 加 `Allow:` 精确放行图片目录,或把 Disallow 范围收窄到真正敏感路径。
**导出(export)**: Reports > Crawlability > Blocked Images
**关联(seealso)**: crawl-blocked-resources;[robots-txt-reference.md](robots-txt-reference.md)、[log-analysis.md](log-analysis.md)

### crawl-blocked-resources
- 名称/类型: 屏蔽 CSS/JS —— warning · 优先级 high · 输出 WARN(源表 warn)
**这意味(what)**: 该 URL 引用的 CSS/JS 被 robots.txt Disallow,引擎渲染页面时"半盲"。
**为什么(why)**: Google 用与 Chrome 同源的渲染器理解页面;JS/CSS 被挡时引擎看到的是未渲染残页——内容由 JS 注入的部分等于不存在,布局信息也缺失(连带影响 CLS 等体验评估)。Google 自 2016 年起明确要求放行渲染资源。
**触发(trigger)**: 1) 提取页面外链 CSS/JS;2) RFC 9309 匹配 robots.txt;3) 被 Disallow 即 warn。
```text
# fail:robots.txt 挡住了渲染资源
Disallow: /assets/
Disallow: /*.js$
```
**不修的条件(caveat)**: 服务端渲染的静态页挡住 CSS 只损失体验评估精度、不丢内容,所以一般建议放行;但已知纯装饰、不参与渲染判定的第三方脚本(计数器)可保留屏蔽。
**修复(fix)**: robots.txt 放行 /assets/、/static/ 及常见 CDN 路径;用 GSC 网址检查的"测试实际抓取"验证渲染结果。
**导出(export)**: Reports > Crawlability > Blocked Resources
**关联(seealso)**: crawl-blocked-images;[rendering-seo.md](rendering-seo.md)

### crawl-pagination-broken
- 名称/类型: 分页断链 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的分页序列中存在 404 链接——翻到某页就断崖。
**为什么(why)**: 分页是系列内容的抓取主干;断链截断后续所有页的发现与权重流入(列表第 3 页 404,第 4-99 页成孤岛)。用户侧:翻页直接撞错误页,电商场景等于把货藏起来。
**触发(trigger)**: 1) 识别分页模式(?page=N、/page/N、页码锚文本);2) 逐页请求分页链接;3) 404 即 fail。
**不修的条件(caveat)**: 无豁免;末页之后的"下一页"链接若因总页数计算错误指向 404,是最常见形态。
**修复(fix)**: 恢复分页路由或把序列截短到真实末页;保证"下一页"链接始终指向 200,末页不再输出 next 链接。
**导出(export)**: Reports > Crawlability > Broken Pagination
**关联(seealso)**: crawl-pagination-loop、crawl-pagination-canonical;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-pagination-loop
- 名称/类型: 分页环 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的分页链接构成环——第 3 页的"下一页"指回第 2 页或第 1 页。
**为什么(why)**: 环让爬虫在有限深度内永远走不到末页,浪费抓取预算且系列内容抓取不完整;用户则在同几页里打转,直接损害可用性。
**触发(trigger)**: 跟踪分页"下一页"序列,出现任一已访问页即 fail。
**不修的条件(caveat)**: 环不惩罚排名,然而序列不可遍历,必须修;无明显豁免场景。
**修复(fix)**: 检查页码计算(总页数 off-by-one、缓存串页);保证页码单调递增、到末页后停止输出。
**导出(export)**: Reports > Crawlability > Pagination Loop
**关联(seealso)**: crawl-pagination-broken、crawl-pagination-sequence

### crawl-pagination-sequence
- 名称/类型: 分页序号缺口 —— warning · 优先级 medium · 输出 WARN(源表 warn;?page=N 序列跳号/不一致)
**这意味(what)**: 分页序列的页码不连续——`?page=1,2,4,7` 跳号,或同系列混用两种分页形态(`?page=` 与 `/page/` 并存)。
**为什么(why)**: 跳号有两种来源:中段页被 4xx/noindex 拿掉(序列真断,断链另归 crawl-pagination-broken),或生成器页码计算错(幽灵跳号);两种都让引擎对序列完整性失去信心,深处内容的发现链条存疑。形态混用则制造两套并行分页 URL,规范化负担翻倍。
**触发(trigger)**: 1) 按系列聚合分页 URL;2) 提取页码序列;3) 出现缺口或同系列两种形态即 warn。
**不修的条件(caveat)**: 跳号不(直接)影响单页排名,然而它标记序列完整性存疑,所以一般建议先查缺口页真实状态(404?noindex?)再决定补齐或重排。但运营刻意下架中段薄页后的缺口是真实业务状态,别硬造假页补号。
**修复(fix)**: 该恢复的恢复路由;已下架的把序列重新连号;统一一种分页形态并 301 旧形态。
**导出(export)**: Reports > Crawlability > Pagination Sequence Gaps
**关联(seealso)**: crawl-pagination-broken、crawl-pagination-canonical;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-pagination-isolated ⛏
- 名称/类型: 分页 URL 无入链 —— issue · 优先级 high · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: 该分页 URL 形如 `?page=N` 或 `/page/N`,在站内却没有任何普通 `<a>` 链接指向它——到达它的唯一途径是注解或参数本身。
**为什么(why)**: 爬虫靠锚点发现页面;只存在于注解/参数空间的分页页等于不可达,序列中段整段丢失。此规则抓的是"另径发现"的分页(只在 sitemap 或 canonical 里出现):爬虫能到的分页页必然有入链,所以命中的要么是生成器泄漏的幽灵分页 URL,要么是链接断档。
**触发(trigger)**: 1) 识别分页形态(?page=N、/page/N、rel=next/prev 残留);2) 检查普通锚点入链;3) 入链=0 即 fail(爬取入口豁免)。
**不修的条件(caveat)**: 若分页 URL 是参数工具(筛选器)泄漏的空壳页,正确处置是 noindex/301/canonical 收口,而不是补内链。
**修复(fix)**: 给真实分页序列补齐可跟随链接;对泄漏的幽灵分页 URL 做规范化收口。
**导出(export)**: Reports > Crawlability > Isolated Pagination URL
**关联(seealso)**: crawl-isolated-url、crawl-pagination-orphaned;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-pagination-canonical
- 名称/类型: 分页 canonical —— issue · 优先级 high · 输出 WARN/CRITICAL(源表 warn/fail:全序列指第 1 页=错,判 fail 档;个别指错=warn 档)
**这意味(what)**: 该分页页的 canonical 指向不正确——典型是第 2..N 页全部 canonical 到第 1 页。
**为什么(why)**: 把 2..N 页 canonical 到第 1 页是曾被滥用的老技巧:引擎对与内容明显不符的规范声明多数直接忽略,2..N 页仍被独立索引但失去明确规范,整组 URL 的去重化失控。**正确做法:每个分页页自引用 canonical**(含序号参数),让引擎自行决定如何处理分页。
**触发(trigger)**: 1) 本页为分页页(参数或路径形态);2) canonical 目标 ≠ 本页自身 URL 即触发;3) 全序列指向第 1 页为最重形态。
```html
<!-- fail:?page=2 的 canonical -->
<link rel="canonical" href="https://example.com/list">
<!-- pass:自引用含页码 -->
<link rel="canonical" href="https://example.com/list?page=2">
```
**不修的条件(caveat)**: Google 对分页 canonical 无强制口径[待核:官方仅明确不建议全指向第 1 页];自引用是社区共识形态,不是唯一合法解。
**修复(fix)**: 模板里 canonical 输出"含当前页码的绝对 URL";配合可抓取的分页锚点链接,不依赖注解。
**导出(export)**: Reports > Crawlability > Pagination Canonical
**关联(seealso)**: crawl-canonical-to-noindex;[redirects-canonical.md](redirects-canonical.md) 分页深度节

### crawl-sitemap-non-canonical ⛏
- 名称/类型: sitemap 内非规范 URL —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: sitemap 列了该 URL,但它不是自己的规范页——sitemap 说"索引这个",canonical 说"索引那个",canonical 赢。
**为什么(why)**: sitemap 应只含自引用 canonical 的 URL;列非规范 URL 浪费抓取配额并制造矛盾信号,引擎最终以 canonical 为准——你为一个不会进索引的 URL 花了预算。全站层面这是 sitemap 生成器与规范化策略脱钩的标志。
**触发(trigger)**: 1) URL 在 sitemap 中;2) 其 canonical ≠ 自身(含跨域/参数差异);3) 即 fail。
**不修的条件(caveat)**: canonical 是提示,引擎会自行仲裁,不惩罚,然而 sitemap 价值被稀释,所以一般建议过滤。但 A/B 测试变体页短暂入 sitemap 可接受。
**修复(fix)**: sitemap 生成时按"canonical 自引用"过滤;排查参数页(UTM/筛选参数)混入路径。
**导出(export)**: Reports > Sitemaps > Non-canonical URLs in Sitemap
**关联(seealso)**: crawl-noindex-in-sitemap、i18n-hreflang-to-non-canonical;[redirects-canonical.md](redirects-canonical.md)

### crawl-sitemap-disallowed ⛏
- 名称/类型: sitemap 内被 Disallow —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: 该 URL 被 robots.txt Disallow,却仍出现在 sitemap 里——你亲手把引擎引到一个它被禁止抓取的地址。
**为什么(why)**: sitemap 与 robots.txt 是同一引擎在读的两份指令,矛盾时引擎直接不抓,该 URL 的推荐额度作废;GSC 覆盖率报告还会出现"已提交但被 robots.txt 屏蔽"错误,持续污染报告的信号价值。
**触发(trigger)**: 1) URL 在 sitemap;2) RFC 9309 匹配 robots.txt 判定被 Disallow;3) 即 fail。**注意:robots.txt 无内容且无任何 Disallow 时报 unmeasured 而非空过**——没有规则可冲突时该规则不可判。
```text
# fail:robots.txt 与 sitemap 矛盾
Disallow: /private/
# sitemap.xml 里却有 https://example.com/private/page
```
**不修的条件(caveat)**: 矛盾不产生惩罚,然而双重浪费(抓取配额+报告噪音),所以一般建议对齐。但刚改 robots 还没重生成 sitemap 的窗口期可暂存。
**修复(fix)**: 二选一:从 sitemap 移除该 URL,或收窄 robots.txt Disallow 范围;修完 GSC 重交 sitemap,验证无"被屏蔽"项。
**导出(export)**: Reports > Sitemaps > Disallowed URLs in Sitemap
**关联(seealso)**: crawl-noindex-in-sitemap、crawl-canonical-to-disallowed;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-sitemap-non-200 ⛏
- 名称/类型: sitemap 内非 200 —— issue · 优先级 high · 输出 CRITICAL/WARN 分型(源表 warn/fail:4xx/5xx=fail,3xx 与超时=warn;仅 crawl 模式)
**这意味(what)**: sitemap 里声明的该 URL,实际爬取时返回的不是 200。
**为什么(why)**: sitemap 是"这些 URL 值得索引"的白名单;指向 4xx/5xx 的条目浪费配额且在 GSC 制造"已提交未编入索引/找不到"噪音。分型:4xx/5xx 是资源真没了(重),3xx 与超时是"sitemap 应直指最终 URL"或临时故障(轻)。爬虫未到达的 URL 不判——发现性归 orphan 规则管,本规则只管可达性。
**触发(trigger)**: 1) 交叉 sitemap URL 集与实际爬取状态码;2) 4xx/5xx → CRITICAL;3) 3xx 或超时 → WARN;4) 未爬到跳过。
**不修的条件(caveat)**: 临时 5xx(部署窗口)重跑即消,先核对服务器日志再动手;批量 404 才是生成器失控信号。
**修复(fix)**: 4xx → 从 sitemap 删除或恢复内容;3xx → sitemap 改写为最终目标 URL;5xx → 修稳定性后复验。
**导出(export)**: Reports > Sitemaps > Non-200 URLs in Sitemap
**关联(seealso)**: crawl-sitemap-non-canonical、links-internal-broken;[http-status-codes.md](http-status-codes.md)

### crawl-sitemap-domain
- 名称/类型: sitemap 域名不匹配 —— warning · 优先级 high · 输出 WARN/CRITICAL(源表 warn/fail;批量外域重、个别笔误轻[分型口径待核])
**这意味(what)**: sitemap 里出现了与 sitemap 宿主域不匹配的 URL。
**为什么(why)**: sitemap 协议要求所有 URL 与 sitemap 所在宿主域一致;混入外域 URL 会损害整个文件的可信度,部分引擎整文件拒收——一条坏行连累五万条好行。
**触发(trigger)**: 1) 解析 sitemap 每个 URL 的 host;2) 与 sitemap 自身 URL 的 host(含 www 形态)比对;3) 不一致即触发。
**不修的条件(caveat)**: 跨域 sitemap 本身合法(需在目标域 robots.txt 声明)——见到外域先查是否声明,别一律判死。
**修复(fix)**: 删除笔误外域 URL;确需跨域 → 在目标域 robots.txt 加 `Sitemap: …` 声明。
**导出(export)**: Reports > Sitemaps > Cross-domain URLs
**关联(seealso)**: crawl-sitemap-in-robotstxt;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-sitemap-url-limit
- 名称/类型: sitemap 条数超限 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 单个 sitemap 文件超过 50,000 条 URL,超出部分整文件可能作废。
**为什么(why)**: 50,000 URL/文件是 sitemap 协议硬上限;超限时引擎的处理不可预期(拒收或截断),且大文件失败重取成本高。分片后每片可独立重交、增量更新。
**触发(trigger)**: 解析 sitemap 条目数;>50,000 即 warn。
**不修的条件(caveat)**: 上限是协议值不是排名因素,然而超限=文件不可控,所以一般建议分片;逼近上限(4 万+)也建议提前拆,留增长余量。
**修复(fix)**: 拆成多个 ≤50,000 的文件(工程实践常按 ≤10,000 一片[待核:实践值非协议值])+ sitemap index;lastmod 保留在各分片。
**导出(export)**: Reports > Sitemaps > URL Limit Exceeded
**关联(seealso)**: crawl-sitemap-size-limit

### crawl-sitemap-size-limit
- 名称/类型: sitemap 体积超限 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 单个 sitemap 未压缩体积超过 50MB。
**为什么(why)**: 50MB 是协议硬上限;超限整文件可能被拒收。gzip 通常能压到 10% 以下,所以这条几乎总是"忘了开压缩"而非真的内容太大。
**触发(trigger)**: 取 sitemap 响应体大小(解压后口径[待核:Google 按 50MB 未压缩判定]);>50MB 即 warn。
**不修的条件(caveat)**: 无实质豁免;唯一提醒是先分片再压缩,别只压缩不拆条数。
**修复(fix)**: gzip(→ .xml.gz)并同步更新 robots.txt/GSC 里的引用;过大的先按 URL 条数上限一起拆。
**导出(export)**: Reports > Sitemaps > Size Limit Exceeded
**关联(seealso)**: crawl-sitemap-url-limit

### crawl-sitemap-duplicate-urls
- 名称/类型: 单文件内重复 URL —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: 同一 sitemap 文件内同一 URL 出现多次。
**为什么(why)**: 引擎侧会去重,不产生重复索引,但重复条目虚增文件体积、稀释 lastmod 语义(同 URL 两个不同 lastmod 以谁为准?),并暴露生成器没做 set 去重。
**触发(trigger)**: 文件内 URL 全量去重比对;出现 ≥2 次即 warn。
**不修的条件(caveat)**: 重复 URL 不影响 SEO(会去重),然而浪费配额与信任,所以一般建议去重。但含查询参数的"看似不同实为同页"URL 不归本规则——那是规范化问题。
**修复(fix)**: 生成管道加规范化去重(排序+unique);检查是否大小写/尾斜杠变体混入。
**导出(export)**: Reports > Sitemaps > Duplicate URLs in Sitemap
**关联(seealso)**: crawl-sitemap-cross-duplicates

### crawl-sitemap-cross-duplicates ⛏
- 名称/类型: 一 URL 多 sitemap —— warning · 优先级 low · 输出 WARN(源表 warn;仅 crawl 模式)
**这意味(what)**: 同一 URL 出现在多个 sitemap 文档里(区别于单文件内重复)。
**为什么(why)**: 引擎跨文件也会去重,属信息级;但多文件共同声明同一 URL 时 lastmod 冲突与维护成本上升,常见于分片逻辑重叠(按分类+按日期各生成一份)。
**触发(trigger)**: 合并全部 sitemap 文档的 URL 集合;同一 URL 属 ≥2 个文档即 warn。
**不修的条件(caveat)**: 跨文件重复会被去重,不影响 SEO,然而两套来源迟早打架,所以一般建议分片互斥。但 sitemap index 主从结构的合法重叠除外——先确认不是 index 自身被当子文件提交。
**修复(fix)**: 分片规则互斥(按唯一键切分);只把 sitemap index 提交给 GSC。
**导出(export)**: Reports > Sitemaps > Cross-Sitemap Duplicates(Summary)
**关联(seealso)**: crawl-sitemap-duplicate-urls

### crawl-sitemap-orphan-urls
- 名称/类型: sitemap 孤儿 URL —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 该 URL 只在 sitemap 里出现,站内没有任何链接指向它(Only in Sitemap)。
**为什么(why)**: sitemap-only 页是弱信号页:引擎可能索引它,但没有内链投票,排名天花板极低,同时占着抓取配额。与 crawl-isolated-url 的区别:本规则只对比 sitemap 与已提取链接集,不做"链接者质量"传播判定。
**触发(trigger)**: 1) 取 sitemap URL 集;2) 减去全站锚点入链非零的 URL;3) 余集即触发。
**不修的条件(caveat)**: 孤儿页不是错误——新页还没来得及加内链、刻意只走 sitemap 的存档页都合理;批量出现才说明信息架构有洞。
**修复(fix)**: 有价值的补入导航/相关推荐;无价值的 301 或 410;刻意存档的接受现状。
**导出(export)**: Reports > Sitemaps > Orphan URLs(Only in Sitemap)
**关联(seealso)**: crawl-isolated-url;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-sitemap-in-robotstxt
- 名称/类型: robots.txt 缺 Sitemap 行 —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: robots.txt 里没有 `Sitemap:` 行,sitemap 只能靠 GSC 手动提交或外部链接被发现。
**为什么(why)**: robots.txt 的 Sitemap 声明是全引擎通用的自动发现机制(不依赖 GSC);缺了它,Bing 及其他引擎可能根本不知道你的 sitemap 存在。一行成本,全引擎收益。
**触发(trigger)**: 解析 robots.txt;无任何 `Sitemap: <绝对URL>` 行即 warn(多分片场景应全部列出)。
**不修的条件(caveat)**: 该行不影响 Google 侧排名,然而堵死非 Google 引擎的发现路径,所以一般建议加。但全站确无 sitemap 时此规则不适用——先解决有没有。
**修复(fix)**: robots.txt 末尾加 `Sitemap: https://example.com/sitemap.xml`(只列 index,或每个分片各一行)。
**导出(export)**: Reports > Crawlability > Sitemap Not Declared in Robots.txt
**关联(seealso)**: crawl-sitemap-url-limit;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-sitemap-lastmod
- 名称/类型: lastmod 质量 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: sitemap 的 lastmod 值非法或是噪声——非法日期格式、未来日期、或整文件所有条目同一天(bulk 戳)。
**为什么(why)**: Google 2023 年起把合法 lastmod 用作抓取优先级信号;整文件同日的 bulk 值等于没有信息,未来日期/非法格式直接被忽略。核心纪律:输出真实变更日期,别输出构建时间。
**触发(trigger)**: 1) 格式合法(W3C Datetime);2) 值不晚于当前时间;3) 单文件内 lastmod 去重后的独立日期数,全同即 bulk 判 warn。
**不修的条件(caveat)**: lastmod 不影响已索引内容的排名,然而影响重抓频率,所以一般建议真实化。但静态站全量重建确实同日变更的场景,同日值是真实的,不适用 bulk 判。
**修复(fix)**: lastmod 绑定内容真实修改时间(git 提交时间/CMS updated_at);非法格式换 W3C Datetime。
**导出(export)**: Reports > Sitemaps > Lastmod Quality
**关联(seealso)**: crawl-sitemap-date-drift;[validation-guide.md](validation-guide.md)

### crawl-sitemap-date-drift ⛏
- 名称/类型: 日期漂移 —— warning · 优先级 low · 输出 WARN(源表 warn;仅 crawl 模式)
**这意味(what)**: 该 URL 的 sitemap lastmod 与页面内 schema dateModified 完全同日,疑似构建时同步写入而非独立维护。
**为什么(why)**: 两个本应独立的信号完全同步 = 至少一个是假的;引擎对全站同步噪声会降低 lastmod 权重。此规则是 sitemap-lastmod 的测谎仪:单看格式都对,交叉比对才露馅。
**触发(trigger)**: 1) 取 sitemap lastmod;2) 取页面 schema dateModified(或 `<time>` 元素);3) 全站批量同日同步即 warn。
**不修的条件(caveat)**: 同日本身合法(真同步更新的站),只有全站批量同日才构成漂移证据;小站样本少时误报率高,先人工抽查。
**修复(fix)**: lastmod 与 dateModified 各自绑定真实事件(抓取时间≠修改时间);构建管道别用同一时间戳灌两处。
**导出(export)**: Reports > Sitemaps > Lastmod Date Drift(Summary)
**关联(seealso)**: crawl-sitemap-lastmod

### crawl-indexability-conflict
- 名称/类型: 索引性冲突 —— warning · 优先级 high · 输出 WARN(源表 warn)
**这意味(what)**: 该 URL 同时被 robots.txt Disallow 和 meta noindex 覆盖——最经典的索引控制双杀误用。
**为什么(why)**: 引擎必须先抓取才能读到 noindex;Disallow 挡在前面时 noindex 永远读不到,URL 仍可能以"被屏蔽但被外链引用"的形态出现在索引里(无内容摘要)。想退索引用 noindex,想省抓取用 Disallow,**两个一起用=两个都不生效**。
**触发(trigger)**: 1) URL 被 robots.txt Disallow;2) 页面 meta robots/X-Robots-Tag 含 noindex;3) 同时成立即 warn。
```text
# fail:robots.txt            页面 head
Disallow: /search/      +     <meta name="robots" content="noindex">
```
**不修的条件(caveat)**: "双保险"直觉是错的——这不是保险是互锁。唯一过渡场景:先 Disallow 屏蔽再补 noindex 的迁移期,此时需 GSC 移除工具协助退索引。
**修复(fix)**: 保留 noindex、删 Disallow;确要省抓取,等页面完全退索引后再评估 Disallow。
**导出(export)**: Reports > Crawlability > Robots vs Noindex Conflict
**关联(seealso)**: crawl-canonical-to-disallowed、core-robots-directive-mismatch;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-pagination-noindex
- 名称/类型: 分页被 noindex —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 分页序列中的某一页被 noindex,而分页页应可索引。
**为什么(why)**: 系列中段被抽走会让引擎对序列完整性失去信心,后续页内容(列表深处的商品/文章)失去被索引的通道。若担心分页薄内容,正解是让每页有独立价值(足够条数+唯一标题),不是 noindex。
**触发(trigger)**: 1) 识别分页页;2) meta robots/X-Robots-Tag 含 noindex;3) 即 warn。
**不修的条件(caveat)**: 超长分页尾部(极深页码)noindex 是可接受的爬取预算取舍[待核:源表口径为整序列应可索引];内站搜索结果的分页另论——那类本就该屏蔽。
**修复(fix)**: 移除列表分页页的 noindex;若是内站搜索分页,canonical 到第 1 页或整体处理并移出 sitemap。
**导出(export)**: Reports > Crawlability > Noindexed Pagination
**关联(seealso)**: crawl-pagination-canonical;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-pagination-orphaned
- 名称/类型: 分页系列无主导航入口 —— warning · 优先级 medium · 输出 WARN(源表 warn;分页系列未从主导航链接)
**这意味(what)**: 分页系列存在,但没有从主导航/核心页面链接到系列——只靠深层页或注解可达。
**为什么(why)**: 分页是列表内容的抓取主干,主干入口埋得深,整组列表页的发现与权重流入都打折。与 crawl-pagination-isolated 的区别:isolated 判**单个**分页 URL 无任何入链(fail),本规则判**系列整体**缺权威入口(warn)——一个是断链级,一个是架构级。
**触发(trigger)**: 1) 识别分页系列;2) 检查系列第 1 页及系列内页是否从导航/分类页可达;3) 仅靠注解或深链发现即 warn。
**不修的条件(caveat)**: 入口深度不(直接)影响排名,然而它决定整组的抓取优先级,所以一般建议列表第 1 页挂进主导航或分类页。但低价值存档列表(历史公告)刻意不进导航是抓取预算取舍。
**修复(fix)**: 分类页/首页给分页第 1 页稳定入口;相关列表间互链;确认"下一页"锚点真实可跟随。
**导出(export)**: Reports > Crawlability > Orphaned Pagination
**关联(seealso)**: crawl-pagination-isolated、links-depth;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-pdf-size
- 名称/类型: 链接 PDF 体积 —— warning · 优先级 low · 输出 WARN(源表 warn;Content-Length **>10MB** 警;HEAD 最多查 **8 个** PDF)
**这意味(what)**: 页面链接的 PDF 文件传输体积超过 10MB。
**为什么(why)**: 大 PDF 对用户是下载等待,对引擎是抓取时间——超大文件可能只被抓取部分或放弃;10MB 线也几乎总是"扫描件没压缩"的症状(图片型 PDF 原始分辨率直接嵌入)。
**触发(trigger)**: 1) 提取页面 PDF 链接;2) HEAD 请求取 Content-Length(最多抽 8 个,超出不查);3) >10MB 即 warn;4) 响应无长度(chunked)跳过;5) 页面无 PDF 链接则通过。
**不修的条件(caveat)**: PDF 体积不(直接)影响所在页面排名,然而它决定 PDF 自身的可抓取性与用户获取成本,所以一般建议压回 10MB 内。但确实需要原始分辨率的图纸/画册类 PDF,可另出压缩版供在线阅读、原件放显式下载位。
**修复(fix)**: 扫描件重压缩+OCR 文本化;图文 PDF 降图片分辨率;超大的按章节拆分;正文内容改用 HTML 承载(还能吃到结构化标记)。
**导出(export)**: Reports > Crawlability > PDF Size
**关联(seealso)**: crawl-sitemap-non-200;[log-analysis.md](log-analysis.md)、[validation-guide.md](validation-guide.md)

### crawl-crawl-delay
- 名称/类型: crawl-delay 指令 —— opportunity · 优先级 insight · 输出 INFO(源表 info;仅报告不扣分)
**这意味(what)**: robots.txt 里使用了 Crawl-delay 指令限制抓取间隔。
**为什么(why)**: Google 从不支持 crawl-delay(直接忽略);Bing/Yandex 支持但把它当限速阀——大值会显著压低日抓取量,新内容收录与更新刷新随之变慢。info 级输出:它不是错误,而是"你在主动限制自己"的声明,审计要把它摆到桌面上让站主确认意图。
**触发(trigger)**: robots.txt 任一 User-agent 组含 `Crawl-delay: N` 即 info(记录 UA 与数值)。
**不修的条件(caveat)**: crawl-delay 不影响排名本身,然而它直接节流支持它的引擎的抓取量,所以一般建议想清楚再留。但被爬虫打挂的小站用 Bing/Yandex 的 crawl-delay 做保护是正当取舍;对 Google 侧它无效,别指望它降 Googlebot 频率。
**修复(fix)**: 限速需求改用 GSC 抓取频率设置与服务器层限流(429/503 短期返回,见 [http-status-codes.md](http-status-codes.md));确要保留 crawl-delay 时给出明确值并写进运维文档。
**导出(export)**: Reports > Crawlability > Crawl-delay Directive(Insight)
**关联(seealso)**: crawl-sitemap-in-robotstxt;[robots-txt-reference.md](robots-txt-reference.md)、[log-analysis.md](log-analysis.md)

---

## 二、重点展开:E-E-A-T(16 条)

| 规则 ID | 名称 | 严重度 | 判定要点 |
|---|---|---|---|
| `eeat-about-page` | About 页 | warn | 检测 About/About Us 页存在 |
| `eeat-affiliate-disclosure` | 联盟披露 | warn | 联盟内容须有 FTC 披露("This post contains affiliate links.") |
| `eeat-author-byline` | 作者署名 | warn | 页面有作者归属 |
| `eeat-author-expertise` | 作者资历 | warn | 作者凭证+简历+资历页 |
| `eeat-citations` | 引用来源 | warn | 链向权威源(.gov/.edu/论文/行业出版物) |
| `eeat-contact-page` | 联系页 | warn | email/电话/表单/地址至少其一 |
| `eeat-content-dates` | 内容日期 | warn | datePublished/dateModified(Article schema 或 `<time>`) |
| `eeat-disclaimers` | YMYL 免责声明 | warn | 医疗/财务/法律内容须有相应免责声明 |
| `eeat-editorial-policy` | 编辑政策 | warn | 编辑政策页(内容标准/事实核查流程) |
| `eeat-physical-address` | 实体地址 | warn | PostalAddress(Organization/LocalBusiness schema) |
| `eeat-privacy-policy` | 隐私政策 | warn | 页脚隐私政策链接 |
| `eeat-terms-of-service` | 服务条款 | warn | 页脚 ToS 链接 |
| `eeat-trust-signals` | 信任信号 | warn | 评论/认证/安全徽章/媒体报道 |
| `eeat-ymyl-detection` | YMYL 检测 | info | 仅识别 YMYL 内容(触发更高 E-E-A-T 标准),不扣分 |
| `eeat-geo-meta` | geo meta | warn | 有 local-business schema 的页也应设 geo meta 标签 |
| `eeat-nap-consistency` | NAP 一致性 ⛏ | warn | 同一组织名在整站爬取中只挂一个电话+地址;不同名=不同主体;需 crawl |

**结构拆法**:16 条 = 信任基建 5(about/contact/privacy/ToS/address)+ 作者维度 2(byline/expertise)+ 内容维度 3(dates/citations/disclaimers)+ 商业披露 1(affiliate)+ 治理 1(editorial-policy)+ 信号 1(trust-signals)+ 检测器 2(YMYL/geo-meta)+ 跨页一致性 1(NAP)。**eeat-ymyl-detection 是开关型 info 规则**——它给 YMYL 判定供数给 disclaimers 等,呼应我们 seo-ops T4"拿不准即标 true"。

---

## 三、重点展开:Internationalization(13 条)

> 我们的 [hreflang-validation.md](hreflang-validation.md) 八检框架覆盖了 return-links/noindex/非规范/断链/重定向/冲突/多载体/相对 URL 中的多数判定;此处按 SEOmator 规则粒度补全为 13 条,新增了**入向校验**与 **x-default 洞察**两个我们缺的维度。

| 规则 ID | 名称 | 严重度 | 判定阈值/要点 |
|---|---|---|---|
| `i18n-lang-attribute` | lang 属性 | fail | `<html>` 须带合法 BCP 47 码(en/en-US/zh-Hans) |
| `i18n-hreflang` | hreflang 存在 | warn/fail | 多语言站须有 `<link rel="alternate" hreflang=…>`,含 x-default |
| `i18n-hreflang-return-links` | 回链 | fail | A 指 B 则 B 必指 A(八检之一) |
| `i18n-hreflang-to-noindex` | 指向 noindex | fail | 目标被 noindex(八检之一) |
| `i18n-hreflang-to-non-canonical` | 指向非规范 | warn | 目标应为 canonical URL(八检之一) |
| `i18n-hreflang-to-broken` | 指向断链 | fail | 静态:空/仅锚点/javascript:/不可解析 href;crawl 模式追加:目标 **4xx/5xx=fail,超时=warn**;未爬到的跳过 |
| `i18n-hreflang-to-redirect` | 指向重定向 | warn | 静态启发:HTTPS 页上用 HTTP hreflang;crawl 模式追加:**3xx 目标=warn** |
| `i18n-hreflang-conflicting` | 冲突声明 | fail | 三形态:同码多 URL/同 URL 多码/本页被多码自引用;x-default 豁免(回退不是冲突) |
| `i18n-hreflang-lang-mismatch` | 语言不匹配 | warn | hreflang 码与目标页实际内容语言不符 |
| `i18n-hreflang-multiple-methods` | 多载体混用 | warn | head 标签/HTTP Link 头/sitemap **只能用一种**(八检之一) |
| `i18n-hreflang-relative-url` | 相对 URL | fail | href 必须含协议的绝对 URL;`/fr/`、`fr/page`、`//example.com/fr/` 全非法,可能废掉整个注解集 |
| `i18n-hreflang-x-default` | 语言码兼作 x-default | info | 同一 URL 既被语言码又被 x-default 指向——合法但值得确认意图(我们八检无此项) |
| `i18n-hreflang-incoming-invalid` | 入向无效码 ⛏ | fail | 他页指向本页的注解须用合法 `xx`/`xx-YY` 码(x-default 恒合法);非法码=本页丢失簇成员资格(我们八检无此项;经典错码 en-UK 应 en-GB、下划线 en_US) |

**解释层(14 条:13 条全目 + 第三批补 lang 一致性一条,吸收 Accessibility 节语言码两条同构)**

### i18n-lang-attribute
- 名称/类型: lang 属性非法 —— issue · 优先级 high · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的 `<html>` 缺少 lang 属性,或值不是合法 BCP 47 码(en/en-US/zh-Hans)。
**为什么(why)**: lang 是引擎语言识别与 hreflang 校验的锚点;对无障碍它同样关键——屏幕阅读器按 lang 切换语音合成引擎,缺失或错误时盲人用户听到的是用错误语音"念"的页面,几乎不可理解。拼错的码同时削弱翻译提示与 SERP 语言过滤。
**触发(trigger)**: 1) `<html lang>` 存在;2) 值匹配 BCP 47 子集 `xx` 或 `xx-YY`(zh-Hans 等脚本子tag 合法);3) 缺失或非法即 fail。
```html
<!-- pass --> <html lang="en">
<!-- fail --> <html>          <!-- 缺失 -->
<!-- fail --> <html lang="english">   <!-- 非法码 -->
```
**不修的条件(caveat)**: lang 不直接改变排名,然而它支撑一串下游机制(hreflang 校验/语言检测/语音合成),所以一般建议必设。但纯代码容器页/iframe 壳页可豁免。
**修复(fix)**: `<html lang="zh-Hans">` 按页面主语言设置;多语言混排页用主语言设 html 级、差异内容段用元素级 lang。
**导出(export)**: Reports > Internationalization > Invalid Lang Attribute
**关联(seealso)**: i18n-hreflang-lang-mismatch;[semantic-html.md](semantic-html.md)

### i18n-hreflang
- 名称/类型: hreflang 缺失 —— warning · 优先级 medium · 输出 WARN/CRITICAL(源表 warn/fail;多语言站缺注解为重档)
**这意味(what)**: 该 URL 是多语言站的一员,却没有任何 hreflang 注解(含 x-default)。
**为什么(why)**: 缺 hreflang 不丢索引,但引擎要靠内容相似度自行猜语言对应,正确语言版在正确市场的不确定性上升。典型缺信号类规则——按两轴哲学排 medium 而非 critical。
**触发(trigger)**: 1) 站点存在 ≥2 语言版本(crawl 判定);2) 本页无任何 `<link rel="alternate" hreflang>`;3) 触发。单页审计无法判定多语言性,不判。
**不修的条件(caveat)**: hreflang 是可选优化不是义务;两三种语言、URL 结构清晰(/en/ /de/)时引擎自行对应已足够好,可合理不部署。
**修复(fix)**: 三载体择一(HTML/HTTP Link/sitemap,只用一种),覆盖全簇+x-default;载体选择依据见 [hreflang-validation.md](hreflang-validation.md) 第二节。
**导出(export)**: Reports > Internationalization > Hreflang Missing
**关联(seealso)**: i18n-hreflang-multiple-methods、i18n-hreflang-x-default;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-return-links
- 名称/类型: hreflang 回链缺失 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;八检之一)
**这意味(what)**: 该 URL 的某条 hreflang 出去了,目标页却没有对应的反向注解指回来——A 指 B,B 不指 A。
**为什么(why)**: Google 官方明确注解必须双向才被采用;缺回链的注解被忽略,该语言对应关系失效——用户在对应语言的 SERP 里看不到正确语言版,引擎也无法在簇内传递信号。簇内一条断回链常意味着一整片模板漏变量。
**触发(trigger)**: 1) 枚举本页出向 hreflang(码,URL);2) 抓目标页注解集;3) 目标缺少"指向本页且码对应"的条目即 fail。
```html
<!-- fail:A(en) 指向 B(de),B 的注解集里没有 (en)→A 的条目 -->
<!-- pass:B 含 <link rel="alternate" hreflang="en" href="…/A"> -->
```
**不修的条件(caveat)**: 回链缺失不惩罚,只是该对应被忽略;但既然部署了 hreflang,半套等于零套,建议一次修齐。
**修复(fix)**: 双向成对生成(模板循环或 sitemap 统一维护);修完用 hreflang_cluster.py 复验簇闭合。
**导出(export)**: Reports > Internationalization > Missing Return Links
**关联(seealso)**: crawl-hreflang-reciprocity;[hreflang-validation.md](hreflang-validation.md) 八检之一

### i18n-hreflang-to-noindex
- 名称/类型: hreflang 指向 noindex —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;八检之一)
**这意味(what)**: 该 URL 的 hreflang 指向一个声明 noindex 的页面(单页版判定;crawl 版 crawl-hreflang-to-noindex 另做全站批量与未爬目标处理)。
**为什么(why)**: 簇内出现"存在但不可选"的成员,Google 的口径是这类注解应整簇忽略——为一页牺牲全簇语言对应,各语言版排名连锁受损;异地用户失去语言切换目标。
**触发(trigger)**: 1) 枚举 hreflang 目标;2) 读目标 meta robots/X-Robots-Tag;3) 任一含 noindex 即 fail。
**不修的条件(caveat)**: 同 crawl-hreflang-to-noindex:策略性下线的语言版应从注解集整体移除,而不是留 noindex 成员挂簇。
**修复(fix)**: 要该语言版 → 删 noindex;不要 → 从所有载体移除该成员,保持簇闭合。
**导出(export)**: Reports > Internationalization > Hreflang to Noindex
**关联(seealso)**: crawl-hreflang-to-noindex、i18n-hreflang-to-non-canonical;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-to-non-canonical
- 名称/类型: hreflang 指向非规范 URL —— warning · 优先级 high · 输出 WARN(源表 warn;八检之一)
**这意味(what)**: 该 URL 的 hreflang 指向的 URL 不是目标页的规范版本。
**为什么(why)**: 规范化之后,非规范 URL 的信号被合并走;指向非规范 URL 的注解要先经一次合并再进簇,多一跳就多一分被丢弃的风险。Google 文档要求 hreflang 指向各语言的规范 URL。
**触发(trigger)**: 1) 取注解目标 URL;2) 抓目标页 canonical;3) canonical ≠ 目标自身即触发。
**不修的条件(caveat)**: 引擎能解开多数"指向非规范"的注解,不构成惩罚,然而每跳折损,所以一般建议直指规范版;协议/尾斜杠级形态差异的修复价值低于参数级差异。
**修复(fix)**: hreflang 集统一输出各语言的 canonical 绝对 URL;生成器别复用带追踪参数的当前 URL。
**导出(export)**: Reports > Internationalization > Hreflang to Non-canonical
**关联(seealso)**: crawl-sitemap-non-canonical;[redirects-canonical.md](redirects-canonical.md)

### i18n-hreflang-to-broken
- 名称/类型: hreflang 指向断链 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;八检之一)
**这意味(what)**: 该 URL 的 hreflang href 是断的——静态判定:空/仅锚点/javascript:/不可解析;crawl 模式追加:目标 4xx/5xx。
**为什么(why)**: 死注解让该语言版本对引擎"不存在",簇出现空洞;空 href/javascript: 这类静态形态甚至可能废掉整个注解集的解析。crawl 模式分型:4xx/5xx=fail、超时=warn(临时性),未爬到的目标跳过。
**触发(trigger)**: 1) href 可解析且含协议(相对 URL 另归 i18n-hreflang-relative-url);2) 非 javascript:/纯锚点;3) crawl:目标 4xx/5xx→fail,超时→warn。
```html
<!-- fail --> <link rel="alternate" hreflang="de" href="">
<!-- pass --> <link rel="alternate" hreflang="de" href="https://example.com/de/">
```
**不修的条件(caveat)**: 无豁免;上线前把 hreflang 集过一遍 link_check 是最便宜的保险。
**修复(fix)**: 修好或删掉死注解;模板里对空语言版做条件渲染(没上线就别输出注解)。
**导出(export)**: Reports > Internationalization > Broken Hreflang
**关联(seealso)**: i18n-hreflang-relative-url、i18n-hreflang-to-redirect;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-to-redirect
- 名称/类型: hreflang 指向重定向 —— warning · 优先级 medium · 输出 WARN(源表 warn;八检之一)
**这意味(what)**: 该 URL 的 hreflang 指向 3xx 重定向目标(crawl 判定),或静态启发:HTTPS 页上用 http:// 的 hreflang。
**为什么(why)**: 引擎要多跳一跳确认语言版,重定向本身提示"该 URL 已非权威形态";静态启发抓的是迁移半拉子状态(全站 https 化后注解没跟着改)。
**触发(trigger)**: 1) crawl:目标 3xx 即 warn;2) 静态:页面 HTTPS 而 hreflang href 为 http:// 即 warn。
**不修的条件(caveat)**: 单跳语言重定向引擎能跟随,不影响排名本身,然而注解应直指最终页,所以一般建议拉直。但基于 Accept-Language 的动态语言选择器落地是合法形态,别误伤。
**修复(fix)**: hreflang 改指最终 200 目标;HTTPS 站全站注解统一 https 绝对 URL。
**导出(export)**: Reports > Internationalization > Hreflang to Redirect
**关联(seealso)**: crawl-canonical-redirect;[redirects-canonical.md](redirects-canonical.md)

### i18n-hreflang-conflicting
- 名称/类型: hreflang 冲突声明 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的注解集内部自相矛盾——三形态:同一语言码指向多个 URL;同一 URL 被标多个语言码;本页被多个码自引用。
**为什么(why)**: 引擎按注解建语言映射,矛盾时无法确定该信哪条,常见结果是丢弃矛盾部分甚至整簇降权处理。x-default 豁免:回退声明不是冲突。
**触发(trigger)**: 1) 集内"语言码→URL"映射须是单值函数;2) "URL→码"同样须单值;3) 违反任一即 fail;x-default 不参与冲突判定。
```html
<!-- fail:同码多 URL -->
<link rel="alternate" hreflang="en" href="/en-a/">
<link rel="alternate" hreflang="en" href="/en-b/">
<!-- fail:同 URL 多码 -->
<link rel="alternate" hreflang="en" href="/x/">
<link rel="alternate" hreflang="de" href="/x/">
```
**不修的条件(caveat)**: 同 URL 多码在"一页混排多语言"站点是物理现实,正确解是拆 URL;实在不拆时引擎按主语言近似处理,不构成惩罚。
**修复(fix)**: 保证映射单值;混排页拆分为 /en/ /de/ 各自持码,或以主语言为准只声明一码。
**导出(export)**: Reports > Internationalization > Conflicting Hreflang
**关联(seealso)**: crawl-hreflang-incoming-conflict、i18n-hreflang-lang-mismatch;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-lang-mismatch
- 名称/类型: hreflang 语言不匹配 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 该 URL 的某条 hreflang 声明的语言码与目标页实际内容语言不符(如 en 码指法语页)。
**为什么(why)**: 错配让该语言用户被送到读不懂的页面——引擎按注解分发语言版,错配直接砸该市场的相关度;无障碍侧屏幕阅读器也会被注解误导切错语音。
**触发(trigger)**: 1) 取注解码;2) 检测目标页实际语言(html lang+内容抽样);3) 主语言不符即 warn。
**不修的条件(caveat)**: 语言检测本身有误差(双语页/多语混杂),命中后先人工抽查再动模板——机器只判 warn 不判 fail 正因此。
**修复(fix)**: 改码或改目标;混排页以主语言为准。
**导出(export)**: Reports > Internationalization > Hreflang Language Mismatch
**关联(seealso)**: i18n-lang-attribute;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-multiple-methods
- 名称/类型: hreflang 多载体混用 —— warning · 优先级 medium · 输出 WARN(源表 warn;八检之一)
**这意味(what)**: 该 URL 同时用多种载体部署 hreflang——head 标签/HTTP Link 头/sitemap 只能用一种。
**为什么(why)**: 多载体并存的典型故障是两载体内容不一致,引擎以哪套为准不可控;且 sitemap 载体与页面载体混用时,单页审计看不到 sitemap,判定天然不完整。
**触发(trigger)**: 1) head 内 `<link rel=alternate hreflang>` 计数;2) 响应头 `Link: <...>; rel="alternate"; hreflang="..."` 计数;3) sitemap 内 xhtml:link 计数;4) ≥2 载体非空即 warn。
**不修的条件(caveat)**: 理论上"完全一致的多载体"也能被处理[待核:Google 文档建议单一来源],不一致才是硬伤;两套内容一致时可降优先级。
**修复(fix)**: 选一种载体(规模站推荐 sitemap——集中维护、免模板),清空其余载体。
**导出(export)**: Reports > Internationalization > Multiple Hreflang Methods
**关联(seealso)**: i18n-hreflang;[hreflang-validation.md](hreflang-validation.md) 第二节

### i18n-hreflang-relative-url
- 名称/类型: hreflang 相对 URL —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的 hreflang href 用了相对路径——`/fr/`、`fr/page`、`//example.com/fr/` 全非法。
**为什么(why)**: 规范要求 hreflang 用含协议的绝对 URL;相对引用在 sitemap 载体里直接非法,在 HTML 里解析结果取决于基准 URL,可能废掉整个注解集——一条相对 URL 连累全部语言对应。
**触发(trigger)**: 1) href 无 http/https scheme 即 fail;2) 协议相对 `//` 同样 fail。
```html
<!-- fail --> <link rel="alternate" hreflang="fr" href="/fr/page">
<!-- fail --> <link rel="alternate" hreflang="fr" href="//example.com/fr/">
<!-- pass --> <link rel="alternate" hreflang="fr" href="https://example.com/fr/page">
```
**不修的条件(caveat)**: 无豁免——规范硬性要求。
**修复(fix)**: 模板输出绝对 URL;CI 对 hreflang href 加 scheme 断言。
**导出(export)**: Reports > Internationalization > Relative Hreflang URL
**关联(seealso)**: i18n-hreflang-to-broken;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-x-default
- 名称/类型: 语言码兼作 x-default —— opportunity · 优先级 insight · 输出 INFO(源表 info)
**这意味(what)**: 该 URL 的某目标同时被一个语言码和 x-default 指向——合法,但值得确认意图。
**为什么(why)**: x-default 的语义是"无匹配语言时的兜底页",语言码是"该语言的指定页";两者指向同一 URL 意味着兜底=某语言专页。常见于 en 站把 x-default 也给 en 首页——能用,但若意图是"语言选择器页"则配错了。我们八检无此项,源目录作为洞察级补充。
**触发(trigger)**: 同一 URL 既出现在某 hreflang="xx" 又出现在 hreflang="x-default" 即报 info。
**不修的条件(caveat)**: 完全合法且常见(en 兜底),不必修;只在"本想用选择器兜底"时改目标。Opportunity/Insight 永不构成扣分项——两轴哲学的样板。
**修复(fix)**: 确认意图:语言专页兜底→保持;选择器兜底→x-default 改指选择器页。
**导出(export)**: Reports > Internationalization > X-default Overlap(Insight)
**关联(seealso)**: i18n-hreflang;[hreflang-validation.md](hreflang-validation.md) 第三节 x-default 六用法

### i18n-hreflang-incoming-invalid ⛏
- 名称/类型: 入向无效语言码 —— issue · 优先级 high · 输出 CRITICAL(源表 fail;仅 crawl 模式)
**这意味(what)**: 他页指向该 URL 的 hreflang 用了非法语言码(下划线 en_US、错码 en-UK),本页因此丢失簇成员资格。
**为什么(why)**: 非法码被引擎丢弃,注解等于没写——本页在其他语言版的簇里缺席。经典错码:en-UK(应 en-GB)、下划线分隔 en_US、大小写错乱;x-default 恒合法。判定的是"别人怎么标我",与 i18n-hreflang-conflicting("我怎么标别人")互补,我们八检此前无此维度。
**触发(trigger)**: 1) 汇总全部入向注解码;2) 逐一校验 `xx`/`xx-YY` 形态与已知码表;3) 任一非法即 fail(x-default 豁免)。
```html
<!-- fail:他页这样指向本页 /gb/ -->
<link rel="alternate" hreflang="en-UK" href="https://example.com/gb/">  <!-- 应 en-GB -->
<link rel="alternate" hreflang="en_US" href="https://example.com/gb/">  <!-- 应 en-US -->
```
**不修的条件(caveat)**: 修在引用方页面(或 sitemap),不在本页——本页无过错却被判,报告里要标注修复位置,避免改错文件。
**修复(fix)**: 改引用方:en_US→en-US、en-UK→en-GB;全站语言码表 lint 一次。
**导出(export)**: Reports > Internationalization > Invalid Incoming Hreflang Code
**关联(seealso)**: crawl-hreflang-incoming-conflict、i18n-hreflang;[hreflang-validation.md](hreflang-validation.md)

### i18n-lang-consistency [待核 ID]
- 名称/类型: 元素级 lang 与 xml:lang 一致性 —— warning · 优先级 low · 输出 WARN(严重度源表未单列[待核];Accessibility 节"lang 与 xml:lang 一致""元素级 lang 合法 BCP 47"两条并入本条,同构判定)
**这意味(what)**: 页面在 html 或元素级设置的 lang 与 xml:lang 值不一致,或元素级 lang 用了非法 BCP 47 码。
**为什么(why)**: XHTML 遗留属性 xml:lang 与 lang 并存时规范要求同值;不一致时解析器与辅助技术各取其一,语言判定行为分裂。元素级 lang 服务混排段落(引文/代码注释/翻译片段),错码让屏幕阅读器用错语音合成引擎读整段——与 i18n-lang-attribute(html 级判定)分工:那条管文档级,本条管元素级与双属性一致性。
**触发(trigger)**: 1) 同元素 lang 与 xml:lang 都存在且值不同即 warn;2) 元素级 lang 值不匹配 BCP 47 `xx`/`xx-YY` 子集(zh-Hans 等脚本子 tag 合法)即 warn。
**不修的条件(caveat)**: lang 一致性不(直接)影响 SEO,然而它同时支撑 hreflang 校验与语音合成,所以一般建议双属性同值、元素级用合法码。但纯 XHTML 遗留模板批量清理收益低时,可只修确有混排内容的模板。
**修复(fix)**: 输出层只写 lang(XHTML 需求才双写同值);混排段落元素级 lang 用精确码(zh-Hans/en-GB);CI 加 lang 值 BCP 47 lint。
**导出(export)**: Reports > Internationalization > Lang Attribute Consistency
**关联(seealso)**: i18n-lang-attribute、i18n-hreflang-lang-mismatch;[semantic-html.md](semantic-html.md)

---

## 四、其余 17 类规则目录(浓缩表,保留全部数字阈值)

### Core SEO(24 条,权重 11%)

title 缺失=fail、长度 **30-60 字符**=warn;description 缺失=fail、**120-160 字符**=warn;canonical 缺失=fail、非绝对/不可达(须 200)=warn;viewport 缺失=fail;favicon 缺失=warn;H1 缺失=fail、多于 1 个=warn;`core-canonical-header`(HTML canonical 与 HTTP Link 头不一致=warn,Link 头应留给 PDF);`core-nosnippet`(nosnippet/max-snippet:0=warn);`core-robots-meta`(noindex/nofollow/noarchive/noimageindex/none=warn);`core-title-unique`(跨页重复 title,crawl,warn/fail);**canonical 家族 8 条**:conflicting(多信号不一致=fail)/to-homepage(深页指向首页=warn)/http-mismatch(协议不一致=warn)/loop(环=fail)/to-noindex(指向 noindex=fail)/outside-head(在 body 里=fail,引擎直接忽略)/attributes(带 hreflang/lang/media/type 属性改变语义=fail,其他多余属性=warn)/multiple(多条且不一致=fail,一致=warn);`core-robots-directive-mismatch`(meta 与 X-Robots-Tag 一方 index 一方 noindex=fail,多处声明 noindex=warn);`core-canonical-external`(指向外域=info,联合发布合法但让渡排名信号)。

**解释层(20 条;ID 未公布原文的按家族命名法推得并标 [待核];第三批补 viewport/favicon 收口 Core SEO 全类)**

#### core-canonical-conflicting
- 名称/类型: canonical 多信号冲突 —— issue · 优先级 high · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的规范化多信号互相打架——meta canonical 与 HTTP Link 头指不同目标,或与其他规范化声明不一致。
**为什么(why)**: 引擎面对冲突信号时自行挑选(按内部启发式),结果不可控——你以为合并到 A,引擎选了 B,索引版本与外链信号双双漂移。这是两轴哲学的教科书案例:**坏信号(冲突)排 high,缺信号(没有 canonical)只排 medium**。
**触发(trigger)**: 1) 收集本页全部规范化声明:meta canonical、HTTP Link 头、全部 link 标签;2) 归一化比对(绝对化/去 fragment);3) 任两声明目标不同即 fail。
```html
<!-- fail:两个信号指不同目标 -->
<link rel="canonical" href="https://example.com/a">
<!-- 响应头 --> Link: <https://example.com/b>; rel="canonical"
```
**不修的条件(caveat)**: 冲突不会惩罚,然而失控的合并比没有合并更糟,所以一般建议统一到单一目标。但历史上"分渠道刻意不同"的变体页(如 AMP 遗留)要先确认再删。
**修复(fix)**: 全部信号指向同一目标(通常自引用);Link 头留给 PDF 等非 HTML 资源(见 core-canonical-header)。
**导出(export)**: Reports > Core SEO > Conflicting Canonical Signals
**关联(seealso)**: core-canonical-header、core-canonical-multiple;[redirects-canonical.md](redirects-canonical.md)

#### core-canonical-multiple
- 名称/类型: 多条 canonical —— issue/warning · 优先级 high(不一致)/low(一致) · 输出 CRITICAL/WARN(源表:不一致=fail,一致=warn)
**这意味(what)**: 该 URL 的 head 里有不止一条 rel=canonical。
**为什么(why)**: 规范要求每页至多一条;多条且不一致时引擎按未承诺的行为挑选(常取最宽松或最后一条),合并结果失控;多条完全一致属冗余,浪费但无害。几乎总是模板双写(框架默认+手写各注入一条)。
**触发(trigger)**: 1) head 内 `<link rel=canonical>` 计数;2) ≥2 且目标不一致 → fail 档;3) ≥2 且一致 → warn 档。
```html
<!-- fail:head 里两条不同目标 -->
<link rel="canonical" href="https://example.com/a">
<link rel="canonical" href="https://example.com/b">
```
**不修的条件(caveat)**: 一致的双写不影响结果,然而多一条就多一分未来不一致的隐患,所以一般建议去重。
**修复(fix)**: 找到双写来源(框架默认+业务手写)删其一;CI 断言每页 canonical 计数=1。
**导出(export)**: Reports > Core SEO > Multiple Canonical Tags
**关联(seealso)**: core-canonical-conflicting、core-canonical-outside-head;[head-elements.md](head-elements.md)

#### core-canonical-outside-head
- 名称/类型: canonical 在 body 里 —— issue · 优先级 high · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的 rel=canonical 出现在 body 里而不是 head 里,引擎直接忽略。
**为什么(why)**: HTML 规范把 link 元素限定在 head;body 里的 canonical 引擎不读——你以为设了规范,引擎根本没看见,规范化退回引擎自选。JS 误插与模板拼接错误是主因。
**触发(trigger)**: 解析 DOM,rel=canonical 元素的祖先链包含 body 即 fail。
```html
<!-- fail -->
<body> … <link rel="canonical" href="https://example.com/a"> … </body>
```
**不修的条件(caveat)**: 无豁免;修复通常只是一行模板位置调整,却决定整条规范化是否生效。
**修复(fix)**: 移进 head(服务端模板或渲染前注入);验证渲染后 DOM 里位置正确。
**导出(export)**: Reports > Core SEO > Canonical Outside Head
**关联(seealso)**: core-canonical-multiple;[head-elements.md](head-elements.md)、[rendering-seo.md](rendering-seo.md)

#### core-canonical-attributes
- 名称/类型: canonical 带语义属性 —— issue/warning · 优先级 high(语义属性)/low(其他) · 输出 CRITICAL/WARN(源表:带 hreflang/lang/media/type=fail,其他多余属性=warn)
**这意味(what)**: 该 URL 的 canonical link 带了改变语义的属性(hreflang/lang/media/type),或其他多余属性。
**为什么(why)**: link 元素的语义由 rel+属性组合决定:带 hreflang 的 canonical 被当作 alternate 族处理、带 media 的是设备变体声明——引擎按属性组合解释,它不再是纯规范化指令,合并行为随之改变。
**触发(trigger)**: 1) rel=canonical 元素上出现 hreflang|lang|media|type 任一 → fail 档;2) 其他非 href/rel 属性 → warn 档。
```html
<!-- fail:语义被属性改变 -->
<link rel="canonical" hreflang="en" href="https://example.com/a">
<!-- pass:只有 rel + href -->
<link rel="canonical" href="https://example.com/a">
```
**不修的条件(caveat)**: 无;清洗属性是无风险的机械修复。
**修复(fix)**: canonical 只留 rel+href 两个属性;语言/设备变体用独立的 link 元素表达。
**导出(export)**: Reports > Core SEO > Canonical with Extra Attributes
**关联(seealso)**: core-canonical-conflicting;[head-elements.md](head-elements.md) link 速查

#### core-canonical-loop
- 名称/类型: canonical 环(单页视角) —— issue · 优先级 high · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的 canonical 链绕回自身,不存在最终规范页(A→B→A 两页环是单页审计能抓到的形态)。
**为什么(why)**: 引擎发现环后丢弃环上全部 canonical,合并失败、信号分裂。单页版跟踪目标链(允许抓取目标页);全站多页环由 crawl 模式的 crawl-canonical-loop 用链接图抓。
**触发(trigger)**: 1) 跟踪 canonical 目标链;2) 回到任一途经 URL 即 fail;3) 自引用通过。
**不修的条件(caveat)**: 同 crawl-canonical-loop:不惩罚但合并作废;两页环通常一处模板错,修复成本极低。
**修复(fix)**: 确定最终规范页让它自引用,其余直指它。
**导出(export)**: Reports > Core SEO > Canonical Loop
**关联(seealso)**: crawl-canonical-loop;[redirects-canonical.md](redirects-canonical.md)

#### core-canonical-to-noindex
- 名称/类型: canonical 指向 noindex(单页视角) —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的 canonical 指向一个声明 noindex 的页面(单页判定;全站批量与未爬目标处理见 crawl-canonical-to-noindex)。
**为什么(why)**: 索引目的地被目的地自己否决:两条指令互相取消,合并回退到引擎自选,重复版本各自为政。
**触发(trigger)**: 1) 取 canonical 目标;2) 读目标 meta robots/X-Robots-Tag;3) 含 noindex 即 fail;自引用通过。
**不修的条件(caveat)**: 同 crawl-canonical-to-noindex 的取舍:刻意用 noindex 页当目标的场景可暂缓,但要记录在案。
**修复(fix)**: 二选一:删目标页 noindex,或 canonical 改自引用/指向可索引规范页。
**导出(export)**: Reports > Core SEO > Canonical to Noindex
**关联(seealso)**: crawl-canonical-to-noindex;[redirects-canonical.md](redirects-canonical.md) 第三节冲突矩阵

#### core-canonical-header
- 名称/类型: HTML canonical 与 Link 头不一致 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 该 URL 的 head 内 canonical 与 HTTP `Link: …; rel="canonical"` 响应头指不同目标。
**为什么(why)**: 双载体不一致时引擎选择不可控;Link 头的合理用途是 PDF 等非 HTML 资源的规范化,HTML 页应只用 meta。两载体同目标时属冗余不报。
**触发(trigger)**: 1) 读响应头 Link canonical;2) 与 head 内 meta canonical 归一化比对;3) 不同即 warn。
**不修的条件(caveat)**: 修 Link 头通常在 CDN/服务器层——应用层找不到别放弃,去网关配置里找。
**修复(fix)**: HTML 页删 Link 头版本;PDF/DOCX 等资源才用 Link 头做规范化。
**导出(export)**: Reports > Core SEO > Canonical Header Mismatch
**关联(seealso)**: core-canonical-conflicting;[head-elements.md](head-elements.md)、[http-status-codes.md](http-status-codes.md)

#### core-canonical-to-homepage
- 名称/类型: 深页 canonical 指向首页 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 该 URL 不是首页,canonical 却指向站点根。
**为什么(why)**: 深层页与首页内容几乎不可能重复:这种指向要么是模板兜底变量为空(首页成了 null 的落点),要么是刻意的"信号泵"——后者会被引擎当作用户导向的异常规范化忽略。深页的外链信号被错误引导到首页。
**触发(trigger)**: 1) 本页非首页;2) canonical 目标 = 站点根(/ 或首页形态)即 warn。
```html
<!-- fail:深页 /blog/post-1 上 -->
<link rel="canonical" href="https://example.com/">
```
**不修的条件(caveat)**: 极少数"深页确为首页的重复内容"(打印版/极薄镜像)成立时可保留;其余一律修。
**修复(fix)**: 模板兜底改成自引用;排查变量注入顺序(分类页为空时 canonical 别落到根)。
**导出(export)**: Reports > Core SEO > Canonical to Homepage
**关联(seealso)**: core-canonical(缺失);[redirects-canonical.md](redirects-canonical.md)

#### core-canonical-http-mismatch
- 名称/类型: canonical 协议不一致 —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: HTTPS 页面的 canonical 用 http:// 协议(或反向)。
**为什么(why)**: 协议不一致制造"似同实异"的 URL,引擎要先解一次重定向才到规范形态;与 form-drift 同族,单页即可判定,批量出现才有模板级价值。
**触发(trigger)**: 页面协议 vs canonical href 协议比对;不一致即 warn。
**不修的条件(caveat)**: 引擎会自行升级 http→https,实际风险低,所以一般建议顺手统一;批量出现才值得模板级修。
**修复(fix)**: canonical 输出与页面一致的协议(全站 https 化)。
**导出(export)**: Reports > Core SEO > Canonical Protocol Mismatch
**关联(seealso)**: crawl-canonical-form-drift;[redirects-canonical.md](redirects-canonical.md)

#### core-canonical [待核 ID]
- 名称/类型: canonical 缺失/非绝对/不可达 —— warning · 优先级 medium · 输出 CRITICAL(缺失,源表 fail)/WARN(非绝对·不可达,源表 warn)
**这意味(what)**: 该 URL 没有 canonical(缺),或值非绝对 URL,或目标不返回 200。
**为什么(why)**: **缺 canonical 本身无碍**——引擎默认页面自规范;只有当存在重复版本(参数/分页/打印版)时,缺失才把合并交给引擎自选。这正是"坏信号>缺信号"的校准点:冲突(坏)排 high,缺失只排 medium——虽然源表把缺失也判 fail(输出 CRITICAL),建议优先级显式降档。非绝对(相对/协议相对 URL)与不可达(目标非 200)是指令本身残缺,归 warn。
**触发(trigger)**: 1) 无 rel=canonical → 缺失档;2) href 相对或协议相对(`//`)→ 非绝对档;3) 目标状态 ≠200 → 不可达档。
**不修的条件(caveat)**: 无重复形态的单版本 URL 站点整体缺 canonical 是合理状态,不必补;规模化重复站(电商参数页/分页)才必补。
**修复(fix)**: 有重复形态的页补自引用绝对 canonical;参数页先定统一形态再显式声明。
**导出(export)**: Reports > Core SEO > Canonical Missing or Invalid
**关联(seealso)**: core-canonical-conflicting;[redirects-canonical.md](redirects-canonical.md) 六场景

#### core-canonical-external
- 名称/类型: canonical 指向外域 —— opportunity · 优先级 insight · 输出 INFO(源表 info)
**这意味(what)**: 该 URL 的 canonical 指向另一个域。
**为什么(why)**: 跨域 canonical 合法(联合发布/白标内容),但语义是"把本页的索引与排名信号让渡给目标域"——本页将退出索引,目标域收走全部权益。作为观察项输出:确认这是商务意图,而不是被黑或模板变量带了他域。
**触发(trigger)**: canonical href 的可注册域 ≠ 本页域即 info。
**不修的条件(caveat)**: 有意为之(供稿给出版伙伴)完全正确;无意的(模板错)是事故——先问意图再动手。Insight 级永不进扣分。
**修复(fix)**: 有意→保持并确保目标域知情;无意→改自引用。
**导出(export)**: Reports > Core SEO > External Canonical(Insight)
**关联(seealso)**: core-canonical-conflicting;[redirects-canonical.md](redirects-canonical.md)

#### core-robots-directive-mismatch
- 名称/类型: meta 与 X-Robots-Tag 索引指令冲突 —— issue/warning · 优先级 high/low · 输出 CRITICAL/WARN(源表:一方 index 一方 noindex=fail,多处声明 noindex=warn)
**这意味(what)**: 该 URL 的 meta robots 与 X-Robots-Tag 响应头,一方说 index 一方说 noindex;或同载体多处重复声明 noindex。
**为什么(why)**: 双载体冲突时引擎倾向取限制性更强的指令[待核:Google 口径为冲突时限制性生效]——你以为页面在索引里而它不在,是最隐蔽的流量消失原因之一。多处 noindex 只是冗余,归 warn。
**触发(trigger)**: 1) 解析 meta robots 与 X-Robots-Tag;2) 一方含 noindex、另一方显式 index → fail 档;3) 同为 noindex 的多处声明 → warn 档。
```html
<!-- fail -->
<meta name="robots" content="index,follow">
<!-- 响应头 --> X-Robots-Tag: noindex
```
**不修的条件(caveat)**: 无;这类冲突没有合法用例,只有没被发现的故障。
**修复(fix)**: 统一索引意图:要索引则两处都删 noindex;不要则保留一处(建议 X-Robots-Tag,服务器层统一管理)。
**导出(export)**: Reports > Core SEO > Robots Directive Mismatch
**关联(seealso)**: core-robots-meta、crawl-indexability-conflict;[head-elements.md](head-elements.md)

#### core-robots-meta
- 名称/类型: robots meta 指令存在 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 该 URL 带 noindex/nofollow/noarchive/noimageindex/none 等限制指令——不是错误,是必须被"知道"的状态。
**为什么(why)**: 这些指令改变页面的索引与链接行为:noindex 页退索引但出链仍被跟随、noimageindex 放弃图片流量、nofollow 改变链接权重语义。审计必须把带指令页从"可优化池"里分离,否则后续规则(内链建设/内容优化)会给出错误处方。输出 warn 语义是"需要注意"而非"有问题"。
**触发(trigger)**: meta robots 或 X-Robots-Tag 含上述任一指令即 warn(none = noindex+nofollow 简写)。
**不修的条件(caveat)**: 指令合法且常是刻意为之(后台/内部搜索/政策页);此规则的价值是清点意图,不是清除指令。
**修复(fix)**: 逐页确认意图:误加的删除,刻意的归档并把页面从审计分母剔除。
**导出(export)**: Reports > Core SEO > Robots Meta Directives
**关联(seealso)**: core-robots-directive-mismatch、crawl-noindex-in-sitemap;[robots-txt-reference.md](robots-txt-reference.md)

#### core-nosnippet
- 名称/类型: nosnippet 指令 —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: 该 URL 带 nosnippet 或 max-snippet:0——SERP 里不许显示摘要。
**为什么(why)**: 无摘要的结果 CTR 通常更低;在 AI 检索环境里,零摘要同时意味着 AI Overviews/助理无法引用该页——是"控制展示"与"放弃引用流量"的交换。作为状态清点输出 warn。
**触发(trigger)**: meta/X-Robots-Tag 含 nosnippet 或 max-snippet:0 即 warn。
**不修的条件(caveat)**: 法律/医疗隐私页刻意禁摘要是正当的;确认意图后记为豁免。
**修复(fix)**: 要摘要与 AI 引用→移除指令;刻意→记录在案,别让下次审计再报。
**导出(export)**: Reports > Core SEO > Nosnippet Directive
**关联(seealso)**: core-robots-meta;[head-elements.md](head-elements.md) meta 全表

#### core-title [待核 ID]
- 名称/类型: title 缺失/长度 —— issue(缺失)/warning(长度) · 优先级 high(缺失)/low(长度) · 输出 CRITICAL(缺失,源表 fail)/WARN(长度,源表 warn)
**这意味(what)**: 该 URL 没有 title,或长度在 30-60 字符建议区间之外。
**为什么(why)**: 缺失时 SERP 用 URL/锚文本充当标题,点击率与相关度双输——这是少数"缺了就肉眼可见"的缺失,故建议优先级高于一般缺信号类。长度是启发式:Google 按像素截断(title 约 ≤~580px,与 Content 节像素宽阈值同源)且常自行改写,**title 长度高度主观**——30-60 只是写作甜区不是硬规则。
**触发(trigger)**: 1) `<title>` 不存在或空白 → 缺失档 fail;2) 长度 <30 或 >60 字符 → 长度档 warn。
```html
<!-- fail --> <title></title>
<!-- warn  --> <title>Home</title>
<!-- pass --> <title>Trail Running Shoes 2026 Buyer's Guide | ExampleRun</title>
```
**不修的条件(caveat)**: title 长度不(直接)影响 SEO 排名,然而影响 SERP 展示完整度与点击,所以一般建议写进 30-60 字符。但在品牌极短标题("Apple")与长尾意图明确的长标题下,出区间完全合理。
**修复(fix)**: 缺失→每页唯一、前置关键词、附品牌的标题;过长→把限定词挪进 description;过短→补足意图修饰词。
**导出(export)**: Reports > Core SEO > Title Missing / Title Length
**关联(seealso)**: core-title-unique;[head-elements.md](head-elements.md)、[scoring-rubric.md](scoring-rubric.md) "不作为扣分依据"节

#### core-title-unique
- 名称/类型: 跨页重复 title —— warning · 优先级 high · 输出 WARN/CRITICAL(源表 warn/fail;crawl 模式)
**这意味(what)**: 站内多个页面用同一个 title。
**为什么(why)**: title 是引擎区分页面的第一信号;模板级重复(万页同题)让引擎只能靠 URL 区分,批量重复还会被质量算法视为低质模板信号——**重复 title 若只涉几页可能无实质影响,数千页模板级重复才可能触发质量算法**,这正是源表 warn/fail 两档的分型逻辑[分型阈值未公布,待核]。
**触发(trigger)**: 1) crawl 全站 title 集;2) 同 title 归组;3) 小组=warn,批量模板级=fail 档。
**不修的条件(caveat)**: 分页/参数变体页同 title 属预期(配合 canonical 处理);先确认重复页本身是否该合并,再谈改标题。
**修复(fix)**: 模板加页面级变量(分类名/页码/属性);真重复页直接合并(canonical/301)。
**导出(export)**: Reports > Core SEO > Duplicate Titles
**关联(seealso)**: content-duplicate-description、content-duplicate-h1;[scoring-rubric.md](scoring-rubric.md)

#### core-description [待核 ID]
- 名称/类型: description 缺失/长度 —— warning · 优先级 medium(缺失)/low(长度) · 输出 CRITICAL(缺失,源表 fail)/WARN(长度,源表 warn)
**这意味(what)**: 该 URL 缺 meta description,或长度在 120-160 字符之外。
**为什么(why)**: Google 只把 description 当候选摘要(查询相关时才用,否则抓页面文本),缺了不丢排名、丢的是摘要可控性——典型"缺信号 medium"。像素口径 ≤~920px(约 155-160 字符),与 Content 节同源。
**触发(trigger)**: 1) 无 meta description → 缺失档;2) <120 或 >160 字符 → 长度档。
**不修的条件(caveat)**: description 不(直接)影响排名,然而影响 CTR 与摘要质量,所以一般建议写满 120-160。但程序化海量页(评论分页/参数页)手写不现实,自动拼装或留空都是可接受取舍。
**修复(fix)**: 核心页手写(前置答案+行动点);模板页用真实字段拼装,别输出空串或全站同文案。
**导出(export)**: Reports > Core SEO > Description Missing / Length
**关联(seealso)**: core-title、content-duplicate-description;[head-elements.md](head-elements.md)

#### core-h1 [待核 ID]
- 名称/类型: H1 缺失/多 H1 —— issue(缺失)/warning(多 H1) · 优先级 medium(缺失)/low(多 H1) · 输出 CRITICAL(缺失,源表 fail)/WARN(多 H1,源表 warn)
**这意味(what)**: 该 URL 没有 H1,或有不止一个 H1。
**为什么(why)**: H1 帮引擎与屏幕阅读器定位页面主题(无障碍:SR 用户常以标题导航跳读);缺 H1 是错失结构信号而非错误指令,故建议优先级 medium。**"只能有一个 H1"不是排名规则**:HTML5 允许多 H1,[scoring-rubric.md](scoring-rubric.md) 的"不作为扣分依据"清单明确此项只作可读性建议,所以多 H1 仅 low。
**触发(trigger)**: 1) h1 计数=0 → fail 档;2) >1 → warn 档。
**不修的条件(caveat)**: 组件化页面常出现多 H1(每卡片一个)——视觉无碍但语义树变浅;真正要紧的是标题层级不跳级、主内容确有一个主题级 H1。
**修复(fix)**: 每页一个主题 H1(与 title 呼应但不雷同);卡片标题降为 H2/H3。
**导出(export)**: Reports > Core SEO > H1 Missing / Multiple
**关联(seealso)**: core-title、content-duplicate-h1;[semantic-html.md](semantic-html.md)

#### core-viewport [待核 ID]
- 名称/类型: viewport 缺失 —— issue · 优先级 high · 输出 CRITICAL(源表 fail)
**这意味(what)**: 页面 head 没有 `<meta name="viewport">`。
**为什么(why)**: 缺 viewport 时移动浏览器按 ~980px 桌面宽度渲染再整体缩放——移动优先索引时代引擎用智能手机爬虫抓取评级,"移动版不可用=不可索引"自 2024 抓取切换起就是事实口径(见 [mobile-seo.md](mobile-seo.md));字号、点击目标、布局全按桌面算,CWV 与可用性全部失真。规范值 `width=device-width, initial-scale=1`([head-elements.md](head-elements.md))。
**触发(trigger)**: head 内无 viewport meta 即 fail;存在但配置不合规(缺 device-width/多标签/禁缩放)另归 Mobile 节 mobile-viewport-config。
**不修的条件(caveat)**: viewport 不改变内容相关度,然而它决定移动渲染形态与索引评级基线,所以一般建议全站必设。但纯桌面工具页/仅登录后使用的后台系统可按内部系统豁免,不影响主站评估。
**修复(fix)**: 全站模板 head 注入 `<meta name="viewport" content="width=device-width, initial-scale=1">`;刘海屏加 viewport-fit=cover;禁 user-scalable=no(见 mobile-viewport-config)。
**导出(export)**: Reports > Core SEO > Missing Viewport
**关联(seealso)**: mobile-viewport-config、mobile-font-size;[head-elements.md](head-elements.md)、[mobile-seo.md](mobile-seo.md)

#### core-favicon [待核 ID]
- 名称/类型: favicon 缺失 —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: 站点没有 favicon:head 无 `<link rel="icon">` 且 /favicon.ico 不可达。
**为什么(why)**: favicon 自 2022 年起进移动 SERP 结果行,缺了结果行留白、品牌识别度下降;浏览器标签页/书签/历史列表全部显示占位图标。纯品牌资产项,与排名无关。
**触发(trigger)**: 1) head 无 rel=icon/shortcut icon/apple-touch-icon;2) 根路径 /favicon.ico 404;两者同时成立即 warn。
**不修的条件(caveat)**: favicon 不(直接)影响 SEO,然而它是 SERP 与浏览器界面的品牌露出位,所以一般建议配置。但内部系统/预发布环境不必配,记豁免即可。
**修复(fix)**: 出多尺寸 ICO 或 PNG+`<link rel="icon" type="image/png" sizes="...">`;apple-touch-icon 180px 单独配;别全站引用外域图标。
**导出(export)**: Reports > Core SEO > Missing Favicon
**关联(seealso)**: core-viewport;[head-elements.md](head-elements.md)

### Performance(28 条,权重 10%)

**CWV 五指标阈值已吸收于 [LCP.md](LCP.md) 与 [scoring-rubric.md](scoring-rubric.md)**:LCP ≤2.5s/2.5-4/>4;CLS ≤0.1/0.1-0.25/>0.25;INP ≤200ms/200-500/>500;TTFB ≤800ms/800-1800/>1800;FCP ≤1.8s/1.8-3/>3。表内补静态项:DOM **<800 过/800-1500 警/>1500 败,深度>32 警**;`perf-asset-cache-policy`(静态资源 max-age ≥1 小时,渲染专属);`perf-asset-compression`(**>2KB** 文本资源须 gzip/Brotli,按 content-length,chunked 无长度不判);`perf-image-encoding`(图片传输 **>100KB=warn**,BMP/TIFF=fail);`perf-page-weight`(**<3MB** 建议);`perf-cache-policy`(带内容 hash 的静态资源 `max-age=31536000`);`perf-minify-css/js`(内联查空白比/块注释;外链 **>2KB** 且 URL 无 `.min.` 标记=启发式嫌疑,恒 ≤warn);`perf-response-time`、`perf-http2`(须 HTTP/2+)、`perf-render-blocking`(head 内脚本无 async/defer)、`perf-lazy-above-fold`(首屏图禁 lazy)、`perf-lcp-hints`(LCP 图须 preload+fetchpriority=high)、`perf-font-loading`(font-display:swap)、`perf-preconnect`、`perf-text-compression`、`perf-brotli`、`perf-video-for-animations`(GIF→video 省 90%)、`perf-legacy-javascript`、`perf-duplicate-js`(同库多 URL)、`perf-source-maps`(不得暴露 sourceMappingURL)。

**解释层(9 条;ID 未公布原文的按家族命名法推得并标 [待核];CWV 五指标本身见 [LCP.md](LCP.md) 不重述)**

#### perf-page-weight [待核 ID]
- 名称/类型: 页面总重 —— warning · 优先级 medium · 输出 WARN(源表 warn;<3MB 建议)
**这意味(what)**: 页面传输总体积(HTML+全部子资源)超过 3MB 建议线。
**为什么(why)**: 总重是 CWV 的上游约束:移动网络下 3MB 意味着数十秒的下载窗口;抓取侧大页也消耗更多引擎时间。3MB 是建议线不是硬阈值——超得多(10MB+)几乎必然伴随未压缩图/未懒加载视频,那些才是要修的实体。
**触发(trigger)**: 1) 渲染后汇总 HTML+子资源传输字节(chunked 无长度资源的计入口径[待核]);2) >3MB 即 warn。
**不修的条件(caveat)**: 页重不(直接)影响排名,然而它给所有体验指标设了天花板,所以一般建议压回 3MB 内。但图库/作品集类页面在已做现代格式+lazy 的前提下适度超线是内容属性,不是技术债。
**修复(fix)**: 按子资源体积排序逐项处理:图片(格式/分辨率/lazy)、视频(poster+按需)、脚本(拆包);文本资源兜底走 perf-asset-compression。
**导出(export)**: Reports > Performance > Page Weight
**关联(seealso)**: perf-asset-compression、images-modern-formats;[LCP.md](LCP.md)

#### perf-asset-compression [待核 ID]
- 名称/类型: 文本资源未压缩(压缩家族) —— warning · 优先级 medium · 输出 WARN(源表 warn;渲染专属。perf-text-compression/perf-brotli 同构:载体与算法维度不同)
**这意味(what)**: content-length >2KB 的文本资源(HTML/CSS/JS/SVG/JSON)响应未带 gzip/Brotli 编码。
**为什么(why)**: 文本压缩比通常 70-90%,是性价比最高的性能修复;Brotli 静态预压又比 gzip 小一档。判定严格按 content-length:>2KB 才查,chunked 无长度不判——避免对流式响应误报,这是阈值纪律而非疏漏。
**触发(trigger)**: 1) 响应 content-length >2KB;2) 无 Content-Encoding: gzip/br 即 warn。家族其余规则同构:perf-text-compression(存在性)、perf-brotli(Brotli 特供)。
**不修的条件(caveat)**: 压缩不影响排名,然而 TTFB 之后的传输时间是 LCP 的直线组成,所以一般建议全站开启。但极小资源(<1KB)压缩收益趋零、CPU 反增的边缘场景可放过。
**修复(fix)**: 服务器/CDN 层开 gzip(底线)或 Brotli(静态资源构建期预压缩最优);验收看响应头。
**导出(export)**: Reports > Performance > Uncompressed Text Assets
**关联(seealso)**: perf-asset-cache-policy、perf-page-weight;[cwv-playbook.md](cwv-playbook.md)

#### perf-asset-cache-policy [待核 ID]
- 名称/类型: 缓存策略(缓存家族) —— warning · 优先级 medium · 输出 WARN(源表 warn;perf-asset-cache-policy 渲染专属:静态资源 max-age ≥1 小时;perf-cache-policy:带内容 hash 的资源 max-age=31536000)
**这意味(what)**: 静态资源 Cache-Control max-age <1 小时;或 URL 带内容 hash 的资源没设 max-age=31536000。
**为什么(why)**: 缓存决定回访与深层爬取的成本:短 max-age 每次访问都重下全部资源;内容 hash 文件名(hash 变=新 URL)天然免疫过期,理应一年期 immutable。CWV 字段数据(CrUX)也依赖真实用户侧缓存生效。
**触发(trigger)**: 1) 静态资源(CSS/JS/图/字体)max-age <3600s 即 warn;2) URL 含内容 hash(如 app.a3f9c2.js 形态)且 max-age ≠31536000 即 warn(perf-cache-policy)。
**不修的条件(caveat)**: 缓存头不影响排名,然而它决定重复访问的真实体验,所以一般建议分层:hash 资源一年+immutable、入口 HTML 短缓存。但无 hash 管道的 CSS 频繁热修时短缓存是运维取舍——先建 hash 管道再拉长缓存。
**修复(fix)**: 构建产物文件名带 hash,配 max-age=31536000, immutable;HTML 用 no-cache/短缓存;两者配合才安全。
**导出(export)**: Reports > Performance > Cache Policy
**关联(seealso)**: perf-asset-compression;[cwv-playbook.md](cwv-playbook.md)

#### perf-render-blocking [待核 ID]
- 名称/类型: 渲染阻塞脚本 —— warning · 优先级 medium · 输出 WARN(源表 warn;head 内脚本无 async/defer)
**这意味(what)**: head 内的 `<script src>` 无 async/defer,HTML 解析必须停下等它下载执行。
**为什么(why)**: 同步脚本阻塞解析器,FCP/LCP 直接被拖;多个同步脚本串行时每个都是链上的一环。async(下载完即执行)与 defer(解析完执行)都归还解析权,语义上 defer 保序、async 抢跑。
**触发(trigger)**: 1) head 内 `<script src>` 无 async/defer 即 warn;2) 内联脚本位于外链同步脚本之后被连带卡住的判定口径[待核]。
**不修的条件(caveat)**: async/defer 不改变脚本对 SEO 的作用,然而它决定首屏时间,所以一般建议非关键脚本全 defer。但强顺序依赖的第三方(统计/AB)要 defer 不要 async,别一刀切。
**修复(fix)**: 非关键脚本 defer 或挪 body 尾;head 只留精简关键样式与资源提示(见 perf-lcp-hints);验收用渲染瀑布图。
**导出(export)**: Reports > Performance > Render-Blocking Scripts
**关联(seealso)**: perf-lcp-hints、js-initial-html;[rendering-seo.md](rendering-seo.md)

#### perf-lcp-hints [待核 ID]
- 名称/类型: LCP 图加载提示 —— warning · 优先级 high · 输出 WARN(源表 warn;LCP 图须 preload+fetchpriority=high)
**这意味(what)**: 页面 LCP 元素是图,却没有 `<link rel=preload as=image>` 且缺 fetchpriority="high"。
**为什么(why)**: LCP 图常经 CSS/字体之后才被发现(CSS background 声明的图尤甚),preload 让它进解析早期队列;fetchpriority=high 在带宽竞争时优先喂它。两个提示叠加是 LCP 优化的标准组合拳——LCP Good 阈值 ≤2.5s(见 [LCP.md](LCP.md))。
**触发(trigger)**: 1) 渲染判定 LCP 元素;2) 为图且无 preload 或无 fetchpriority=high 即 warn。
**不修的条件(caveat)**: 资源提示不影响排名,然而它们直接调度 LCP 资源的优先级,所以一般建议 LCP 图必配。但 LCP 元素是文字的页面不适用;preload 滥用(全页 preload)反而稀释优先级,只给这一张。
**修复(fix)**: `<link rel="preload" as="image" href="…hero.webp" fetchpriority="high">`,img 同步加 fetchpriority="high";LCP 图禁 lazy(见 images-lazy)。
**导出(export)**: Reports > Performance > LCP Resource Hints
**关联(seealso)**: images-lazy、perf-font-loading;[LCP.md](LCP.md)

#### perf-font-loading [待核 ID]
- 名称/类型: 字体加载策略 —— warning · 优先级 medium · 输出 WARN(源表 warn;font-display:swap)
**这意味(what)**: @font-face 声明缺 font-display:swap(或等价的防隐形策略)。
**为什么(why)**: 默认字体行为是 FOIT——字体下载完前文字不可见,慢字体=隐形文字=FCP/LCP 双输;swap 先用系统字渲染、字体到了再换,把"不可见"降级为"闪换"。
**触发(trigger)**: 渲染检查 @font-face 无 font-display:swap/optional 即 warn。
**不修的条件(caveat)**: swap 的双字 metrics 差异会小幅推高 CLS,然而换来的立即可见远大于抖动代价,所以一般建议 swap。但排版严苛页可选 optional(超时永用系统字);中文大字符集字体建议子集化后再 swap。
**修复(fix)**: @font-face 加 font-display:swap;关键字体 `<link rel=preload as=font crossorigin>`;中文字体按常用字切片。
**导出(export)**: Reports > Performance > Font Loading
**关联(seealso)**: perf-lcp-hints;[cwv-playbook.md](cwv-playbook.md)

#### perf-dom-size [待核 ID]
- 名称/类型: DOM 规模 —— warning · 优先级 medium · 输出 WARN(源表:DOM <800 过/800-1500 警/>1500 败,深度>32 警)
**这意味(what)**: 渲染后 DOM 元素节点数超 800(>1500 更重),或最大嵌套深度 >32。
**为什么(why)**: DOM 规模是 INP 与 CLS 的放大器:节点越多,样式计算/布局/交互响应越慢;深度 >32 几乎总是组件套组件叠出来的无语义容器,对语义树零贡献。
**触发(trigger)**: 1) 统计渲染后元素节点数:<800 过、800-1500 警、>1500 败;2) 最大嵌套深度 >32 即警。
**不修的条件(caveat)**: DOM 规模不(直接)影响 SEO,然而它给交互响应设上限,所以一般建议长列表分页/虚拟滚动。但数据密集页(财务表格)DOM 天然大,分页才是正解,不是硬删。
**修复(fix)**: 列表虚拟滚动或分页;拆装饰性嵌套容器;组件库治理"div 三明治"(每组件三层无语义 div)。
**导出(export)**: Reports > Performance > DOM Size
**关联(seealso)**: perf-page-weight;[cwv-playbook.md](cwv-playbook.md)

#### perf-resource-hygiene [待核 ID]
- 名称/类型: 资源卫生家族(六小条) —— warning · 优先级 low · 输出 WARN(源表各=warn)
**这意味(what)**: 六项资源层卫生任一命中:非 HTTP/2+(perf-http2 须 HTTP/2+);legacy polyfill 包(perf-legacy-javascript);同库多 URL 重复加载(perf-duplicate-js);暴露 sourceMappingURL(perf-source-maps 不得暴露);动画 GIF 该换 video(perf-video-for-animations,GIF→video 省 90%);css/js 压缩嫌疑(perf-minify 家族:内联查空白比/块注释;外链 >2KB 且 URL 无 .min. 标记=启发式嫌疑,恒 ≤warn)。
**为什么(why)**: 每项都是确定的字节/时间浪费:HTTP/1.1 队头阻塞限制同域并行;legacy JS 给现代浏览器发多余 polyfill;同库多 URL 既多下载又版本漂移;source map 公开暴露源码结构(偏安全面);GIF 是编码效率最差的动画载体。单项轻,叠加是可量化的无谓传输。
**触发(trigger)**: 协议 <HTTP/2 → warn;脚本含 es5 时代 polyfill 特征 → warn;同库 ≥2 个不同 URL → warn;脚本带 sourceMappingURL → warn;动画 GIF[体积阈值源表未公布,待核] → warn;外链 css/js >2KB 且无 .min. → 恒 ≤warn(启发式;图片传输侧另见 perf-image-encoding:>100KB=warn、BMP/TIFF=fail,与 Images 节 images-modern-formats 同一事实两面)。
**不修的条件(caveat)**: 家族单项都不影响排名,然而叠起来是可量化的浪费,所以一般建议一次清完。但 source map 若仅鉴权后可访问,暴露面已受控,可降优先级。
**修复(fix)**: 全站 HTTP/2+;构建 target 现代浏览器砍 polyfill;依赖收敛单版本;source map 仅上传错误平台、产物剥离 sourceMappingURL;GIF→MP4/WebM;构建开 css/js 压缩输出 .min. 产物。
**导出(export)**: Reports > Performance > Resource Hygiene
**关联(seealso)**: perf-asset-compression、perf-asset-cache-policy;[cwv-playbook.md](cwv-playbook.md)

#### perf-preconnect [待核 ID]
- 名称/类型: 关键源预连接 —— warning · 优先级 medium · 输出 WARN(源表 warn;perf-response-time 与 TTFB 同源阈值已吸收于 [LCP.md](LCP.md) 不重述)
**这意味(what)**: 页面加载关键的跨源资源(字体 CDN/图床/第三方关键脚本)没有 `<link rel="preconnect">`(或 dns-prefetch 兜底)。
**为什么(why)**: 每个新源要付 DNS+TCP+TLS 三段握手,关键资源跨源时握手时间前置吃进 LCP;preconnect 提前完成握手,资源请求一发出即进传输段。只该给关键少数源——滥用会占满连接池,反而拖慢其余资源。
**触发(trigger)**: 渲染瀑布中首屏关键资源(字体/LCP 图/关键 CSS)的 host 与页面 host 不同,且 head 无对应 `<link rel="preconnect" href="https://…">`(字体类带 crossorigin)即 warn。
**不修的条件(caveat)**: 资源提示不(直接)影响排名,然而它削掉的是 LCP 里最机械的握手段,所以一般建议关键跨源必配。但资源已同源聚合或全站 HTTP/3 的站点收益趋零,按瀑布图实测决定再配。
**修复(fix)**: head 顶部对字体/CDN 源加 preconnect(字体带 crossorigin);次级源用 dns-prefetch;可配合 103 Early Hints 由源站下发(见 [cwv-playbook.md](cwv-playbook.md))。
**导出(export)**: Reports > Performance > Preconnect Hints
**关联(seealso)**: perf-lcp-hints、perf-font-loading;[cwv-playbook.md](cwv-playbook.md)、[LCP.md](LCP.md)

### Links(27 条,权重 8%)

内链 4xx=fail;外链可达性=warn(结果缓存);无内链=warn;nofollow 滥用=warn;泛化锚文本("click here"/"read more"/"link")=warn;`links-depth`(**点击距离 ≤3**,crawl);死端页(无出链)=warn;HTTPS 页链 HTTP=warn;**外链 >100=warn**;空/javascript:/畸形 href=warn;tel:/mailto: 格式=warn;重定向链(**1-2 跳=warn,≥3=fail**);`links-localhost`(127.0.0.1=fail)/`links-local-file`(file://=fail);断锚点(#id 无匹配)=warn;`links-onclick`(onclick 导航替代 href=warn);href 首尾空白=warn;非 HTTP 协议(ftp:/intent:/chrome:)=warn;**crawl 专属入链族 8 条**:inbound-all-nofollow(全 nofollow=零权重流入,洞见级)/inbound-mixed-follow(有follow有nofollow=不一致)/inbound-low-quality(入链全 nofollow 或全来自被 canonical 走的页)/inbound-anchor-text(全部入链锚文本<2 字符或泛化)/nofollow-internal(同主机链接禁 nofollow)/weak-inbound(**非入口页须 >1 条 dofollow 入链**)/chrome-inbound(**至少 1 条入链在 nav/header/footer 之外**——正文链才算票)/orphan-pages(真孤儿由 crawl-sitemap-orphan-urls 配合判)。

**解释层(16 条;ID 未公布原文的标 [待核];入链族 8 条的 5 条并入 links-weak-inbound/links-chrome-inbound 陈述)**

#### links-internal-broken [待核 ID]
- 名称/类型: 内链 4xx —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的站内链接指向返回 4xx 的页面。
**为什么(why)**: 每条死内链都是断的权重通道+断的用户路径:引擎沿链接爬行撞 404 会降低对该区域的抓取意愿,用户撞 404 直接流失。内链 4xx 是少数同时硬伤 SEO 与 UX 的问题,故 fail。
**触发(trigger)**: 1) 提取全部同域 `<a href>`;2) 请求目标(结果缓存);3) 4xx 即 fail。
**不修的条件(caveat)**: 刻意 410(Gone)的下线内容不算错——那是带语义的退场,告诉引擎"永久消失";404 与 410 在处置上要分开。
**修复(fix)**: 目标还在→修 href 拼写;目标没了→301 到最近亲页或删除链接;批量死链优先查迁移映射表。
**导出(export)**: Reports > Links > Broken Internal Links
**关联(seealso)**: crawl-pagination-broken、i18n-hreflang-to-broken;[link-architecture-patterns.md](link-architecture-patterns.md)、[http-status-codes.md](http-status-codes.md)

#### links-redirect-chain [待核 ID]
- 名称/类型: 重定向链 —— issue(≥3 跳)/warning(1-2 跳) · 优先级 high/medium · 输出 CRITICAL(≥3 跳)/WARN(1-2 跳;源表:1-2 跳=warn,≥3=fail)
**这意味(what)**: 该 URL 的链接要经过多跳重定向才到最终页。
**为什么(why)**: 每一跳都损耗:抓取预算×跳数、页面延迟叠加、部分爬虫限跳;≥3 跳意味着迁移叠迁移从没清理。内链理想态是零跳直指最终 URL。
**触发(trigger)**: 1) 跟踪目标 Location 链;2) 链长 1-2 → warn;3) ≥3 → fail。
**不修的条件(caveat)**: 单跳 http→https/加尾斜杠属良性规范化,不修也行;深链(3 跳+)才是技术债。
**修复(fix)**: 内链模板直指最终 URL;服务器层把链条整体改写为 A→Z 一步到位。
**导出(export)**: Reports > Links > Redirect Chains
**关联(seealso)**: redirects-loop、crawl-canonical-redirect;[redirects-canonical.md](redirects-canonical.md)

#### links-depth
- 名称/类型: 点击距离 —— warning · 优先级 medium · 输出 WARN(源表 warn;阈值 ≤3 过;crawl 模式)
**这意味(what)**: 该 URL 距首页的点击距离超过 3(点击距离 ≤3 过/超标警)。
**为什么(why)**: 点击距离是 PageRank 与抓取优先级的粗糙代理:埋得深的页面权重薄、发现慢,电商大类深页常因此"索引了但不排名"。仅 crawl 模式可测(需要全站链接图)。
**触发(trigger)**: 1) 以首页为源建 follow 内链图;2) BFS 计算点击距离;3) >3 即 warn。
**不修的条件(caveat)**: 距离不(直接)决定排名,然而它代理内链权重与可发现性,所以一般建议关键页 ≤3 跳。但存档/法律页天然可以深;把首页塞满链接去压深度才是错修。
**修复(fix)**: 重要页从导航/分类页/相关推荐多点接入;扁平化信息架构,而不是往首页堆链接。
**导出(export)**: Reports > Links > Click Depth
**关联(seealso)**: crawl-isolated-url、crawl-sitemap-orphan-urls;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-localhost
- 名称/类型: localhost/file 链接 —— issue · 优先级 high · 输出 CRITICAL(源表 fail;file:// 同族判)
**这意味(what)**: 该 URL 链向 127.0.0.1/localhost(或 file:// 本地路径)——开发环境地址漏进了生产。
**为什么(why)**: 对用户是死链,对爬虫是不可达地址,同时暴露部署管道把 dev 配置带上线;file:// 同性质。几乎总伴随"某环境下正常、上线即坏"的隐性故障。
**触发(trigger)**: href host ∈ {127.0.0.1, localhost, ::1} 或 scheme=file 即 fail。
```html
<!-- fail --> <a href="http://127.0.0.1:3000/dashboard">Dashboard</a>
<!-- fail --> <a href="file:///Users/dev/report.pdf">Report</a>
```
**不修的条件(caveat)**: 无;修的是配置与发布流程,不是这一个个链接。
**修复(fix)**: 排查环境变量注入(绝对 URL 拼装基准);上线检查清单加 localhost/file:// 扫描。
**导出(export)**: Reports > Links > Localhost or File Links
**关联(seealso)**: links-internal-broken

#### links-anchor-generic [待核 ID]
- 名称/类型: 泛化锚文本 —— warning · 优先级 medium · 输出 WARN(源表 warn;"click here"/"read more"/"link")
**这意味(what)**: 站内链接的锚文本是泛化词——click here/read more/link 一类,不含目标页主题信息。
**为什么(why)**: 锚文本是引擎理解目标页相关度的第一信号,泛化锚等于把票投给"一个叫 click here 的页面";无障碍侧,屏幕阅读器用户常脱离上下文按链接列表浏览,一列 "read more" 完全不可用。批量泛化锚几乎总是模板省事,不是文案选择。
**触发(trigger)**: 锚文本命中泛化词表(click here/read more/link/more/here 等[词表源表未公布,待核])且为普通文本链即 warn;图标链接的可访问名(alt/aria-label)即其锚文本,同口径计。
**不修的条件(caveat)**: 锚文本不(直接)决定目标页排名,然而它是零成本的相关度信号,所以一般建议锚含目标主题词。但 CTR 导向的行动按钮("免费试用")是转化文案,别为 SEO 破坏——链接补 aria-label 带上主题即可。
**修复(fix)**: 模板把目标页标题注入锚("阅读:SEO 审计入门");纯图标链接补 aria-label;全站泛化锚 lint 进 CI。
**导出(export)**: Reports > Links > Generic Anchor Text
**关联(seealso)**: links-weak-inbound;[link-architecture-patterns.md](link-architecture-patterns.md)、[semantic-html.md](semantic-html.md)

#### links-nofollow-internal [待核 ID]
- 名称/类型: 内链 nofollow —— warning · 优先级 medium · 输出 WARN(源表 warn;同主机链接禁 nofollow)
**这意味(what)**: 指向同主机的内链被加了 rel=nofollow。
**为什么(why)**: nofollow 的语义是"不为这个链接背书",用在自家内链上是自我否定;且自 2009 年起引擎对 nofollow 链接的权重处理是直接扣除而非导给同页其余链接——"用内链 nofollow 调节权重流向"的动机从起点就不成立(口径见 [deprecated-signals.md](deprecated-signals.md))。剩下的成因几乎只有误加:CMS 默认、UGC 模板全局套用。
**触发(trigger)**: 同域 `<a>` 带 rel=nofollow 即 warn。
**不修的条件(caveat)**: 内链 nofollow 不带来任何收益,然而删除它也无即时排名变化(权重会计在引擎内部),所以一般建议作为卫生项清理。但 UGC 区(论坛/评论)给用户发布的外链加 nofollow/ugc 是反 spam 标准做法,不属"内链"。
**修复(fix)**: 模板移除内链 nofollow;UGC 外链区保留 ugc/nofollow;抓取预算问题走 robots.txt,索引控制走 noindex/canonical。
**导出(export)**: Reports > Links > Nofollow Internal Links
**关联(seealso)**: links-external-many、url-search-indexed;[robots-txt-reference.md](robots-txt-reference.md)

#### links-external-many [待核 ID]
- 名称/类型: 外链过多 —— warning · 优先级 low · 输出 WARN(源表 warn;外链 >100)
**这意味(what)**: 单页指向外部的链接超过 100 条。
**为什么(why)**: 100 源自 Google 早年工程口径(单页链接数的解析上限),现代引擎不再硬卡;但外链爆炸仍是链接农场/资源页失控的形态信号,且链接权重按出链数稀释——100+ 出链时每条(含你想推的内链)分到的投票趋近于零。
**触发(trigger)**: 统计页内出站(跨域)`<a href>` 数;>100 即 warn(nofollow 是否计入的口径[待核])。
**不修的条件(caveat)**: 外链数量不影响本页排名,然而它稀释每条链接的相对价值,所以一般建议长资源页分栏分页。但学术引文页/目录站的百条外链是内容真实形态,分页反而伤可用性。
**修复(fix)**: 长资源页按主题分页;非核心外链区 nofollow/ugc 收口;付费与联盟位用 rel=sponsored。
**导出(export)**: Reports > Links > Excessive External Links
**关联(seealso)**: links-nofollow-internal;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-dead-end [待核 ID]
- 名称/类型: 死端页 —— warning · 优先级 medium · 输出 WARN(源表 warn;无出链)
**这意味(what)**: 页面没有任何 follow 出链——用户与爬虫到这里都走不动了。
**为什么(why)**: 死端页截断浏览路径(用户只能回退)与爬行路径(引擎无法从它继续发现);与孤立 URL(无入链)互为镜像——一个进不来,一个出不去。转化终点页(支付成功/退订确认)是唯一常见合理形态。
**触发(trigger)**: 页面 follow 出链计数=0 即 warn(爬取入口与纯工具页的豁免口径[待核])。
**不修的条件(caveat)**: 死端不(直接)影响本页排名,然而它浪费一次"带用户/引擎去别处"的机会,所以一般建议补相关推荐与返回路径。但流程终点页刻意零出链是转化设计,记豁免。
**修复(fix)**: 补相关内容推荐/面包屑/返回分类;结算页类模板确认其 noindex 与出链策略是刻意设计。
**导出(export)**: Reports > Links > Dead-End Pages
**关联(seealso)**: crawl-isolated-url、links-depth;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-weak-inbound [待核 ID]
- 名称/类型: 弱入链(入链族核心) —— warning · 优先级 medium · 输出 WARN(源表 warn;crawl 专属;非入口页须 >1 条 dofollow 入链)
**这意味(what)**: 非爬取入口的页面只有 ≤1 条 dofollow 入链——技术上可达,权重与健壮性上贫血。
**为什么(why)**: 单链页在链接图上是"叶子":首页一改版挪掉那条链接,它就掉成孤立页;权重流入也只有一条窄通道,排名天花板低。本规则是入链族 8 条的核心判定,同族同构维护:inbound-all-nofollow(全 nofollow=零权重流入,洞见级)/inbound-mixed-follow(follow·nofollow 混杂)/inbound-low-quality(入链全来自被 canonical 走的页)/inbound-anchor-text(全部入链锚 <2 字符或泛化)——四条都是对同一入链图不同切面的质量计数,阈值见本节表,不逐条扩写。
**触发(trigger)**: 1) crawl 构建 dofollow 入链图;2) 非入口页 dofollow 入链数 ≤1 即 warn。
**不修的条件(caveat)**: 入链数不(直接)决定排名(质量重于数量),然而 1 条链是脆弱性指标,所以一般建议关键页 ≥2-3 条来自不同区域。但刚发布未及内链的新页与法律页是过渡态/低需求态,可豁免。
**修复(fix)**: 分类页/相关推荐/正文上下文多点接入;重要页至少导航与正文各一条(见 links-chrome-inbound)。
**导出(export)**: Reports > Links > Weak Inbound Links
**关联(seealso)**: links-chrome-inbound、crawl-isolated-url;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-chrome-inbound [待核 ID]
- 名称/类型: 仅有导航区入链 —— warning · 优先级 medium · 输出 WARN(源表 warn;crawl 专属;至少 1 条入链在 nav/header/footer 之外)
**这意味(what)**: 页面的全部入链都来自导航 chrome(导航/页头/页脚),没有任何一条来自正文区。
**为什么(why)**: 导航链接全站同款,引擎对其的评估趋于"模板信号"而非"编辑性投票";正文内语境链接才是"该主题下值得推荐"的表达,也是相关度传递者。全 chrome 入链的页面=只被模板带到,没被任何内容论证过。
**触发(trigger)**: 1) 入链图标注每条入链来源区域(nav/header/footer vs 正文);2) 正文区入链=0 即 warn。
**不修的条件(caveat)**: 正文入链不影响排名本身,然而它是相关度信号的载体,所以一般建议核心页有语境内链。但政策/法务页(无需主题论证)全 chrome 入链是正常形态;相关推荐模块算不算正文区[待核:源表区域划分口径未公布]。
**修复(fix)**: 在相关正文里以描述性锚接入(锚文本规范见 links-anchor-generic);让内容作者而非仅模板产出内链。
**导出(export)**: Reports > Links > Chrome-only Inbound Links
**关联(seealso)**: links-weak-inbound、links-anchor-generic;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-no-internal [待核 ID]
- 名称/类型: 无内链 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 该 URL 的页面上没有任何指向本站其他页面的链接——出链全空或只剩外链。
**为什么(why)**: 爬虫沿内链爬行,无内链出边的页面是爬行路径终点,站内再深一层的内容失去一条发现通道;用户读完即"离开站点",相关推荐与转化路径全部缺席。与 links-dead-end 互补:那条判"零出链",本条把"有出链但无一是站内"也纳入——把流量送出门却不留后路。
**触发(trigger)**: 页面同域 follow `<a href>` 计数=0 即 warn。
**不修的条件(caveat)**: 内链数不(直接)影响本页排名,然而它决定爬行延续与用户动线,所以一般建议补相关内容入口。但纯外链引流的工具落地页/第三方托管的致谢页可合理保持。
**修复(fix)**: 补相关内容模块/面包屑/回到分类入口;模板保证每页有站内链接区块。
**导出(export)**: Reports > Links > No Internal Links
**关联(seealso)**: links-dead-end、links-depth;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-external-reachability [待核 ID]
- 名称/类型: 外链可达性(含 HTTPS 页链 HTTP) —— warning · 优先级 low · 输出 WARN(源表 warn;外链可达性结果缓存;HTTPS 页链 HTTP=warn 同族)
**这意味(what)**: 页面指向外部的链接目标不可达(4xx/5xx/超时),或 HTTPS 页面上仍用 http:// 外链。
**为什么(why)**: 死外链伤用户信任(点出去 404),也标记页面疏于维护;HTTPS 页混 http 外链本身不构成混合内容(仅子资源才算),但形态不一致在目标站完成 https 化后容易变成断链。外链判定带结果缓存,避免全站审计反复打同一目标。
**触发(trigger)**: 1) 请求全部跨域 href(缓存结果);4xx/5xx/超时即 warn;2) 页面 HTTPS 而 href 为 http:// 即 warn。
**不修的条件(caveat)**: 外链目标不受你控制——对方改版删页你这边全站误报,所以一般建议批量检测后只修高频引用的死外链。但支撑 E-E-A-T 的权威引用页(eeat-citations)值得保持零死链,优先级另计。
**修复(fix)**: 死外链换网页存档链接或替代来源;http 外链统一改 https(目标支持时);引用型内容的死链优先于资源页死链。
**导出(export)**: Reports > Links > Broken External Links
**关联(seealso)**: links-internal-broken、eeat-citations;[http-status-codes.md](http-status-codes.md)

#### links-malformed-href [待核 ID]
- 名称/类型: 畸形 href 家族 —— warning · 优先级 low · 输出 WARN(源表各=warn:空/javascript:/畸形 href;tel:/mailto: 格式;非 HTTP 协议 ftp:/intent:/chrome:;href 首尾空白)
**这意味(what)**: `<a>` 的 href 是空串、javascript: 伪协议或畸形值;tel:/mailto: 格式错;scheme 为 ftp:/intent:/chrome: 等非 HTTP(S) 协议;或首尾带空白字符。
**为什么(why)**: 空 href 与 javascript: 链接对引擎是不可跟随的假链接——权重与发现都不传递,键盘用户聚焦过去也无处可去;tel:/mailto: 格式错在移动端直接呼叫/发信失败;异形协议链接多数是模板变量泄漏。首尾空白则是"能工作但制造变体 URL"的卫生问题。
**触发(trigger)**: 1) href 空串或 javascript: 伪协议即 warn;2) tel: 不匹配 `tel:+数字` 形态、mailto: 无合法邮箱即 warn;3) scheme ∈ ftp:/intent:/chrome: 等非 HTTP(S) 即 warn;4) href 首尾含空白即 warn。
**不修的条件(caveat)**: 伪协议链接不(直接)影响排名,然而它把交互做成引擎与部分用户到不了的门,所以一般建议真导航一律用可跟随 href。但 mailto:/tel: 本身合法,只查格式;确需 JS 行为的元素正解是 `<button>`,不是豁免。
**修复(fix)**: 真导航用真实 URL;JS 行为改 button+事件;tel/mailto 按规范格式输出;模板输出 href 时 trim。
**导出(export)**: Reports > Links > Malformed Href Values
**关联(seealso)**: links-onclick、i18n-hreflang-to-broken;[semantic-html.md](semantic-html.md)

#### links-broken-anchor [待核 ID]
- 名称/类型: 断锚点 —— warning · 优先级 low · 输出 WARN(源表 warn;#id 无匹配)
**这意味(what)**: 链接的 fragment(#section)在目标页里找不到对应 id/命名锚点。
**为什么(why)**: 锚点链接是长页深链与 AI 引用定位的常用形态;目标页重构后 heading id 改名,来源页的 fragment 全部落空——用户被丢在页顶以为内容不存在。同页 fragment 直接查本页 DOM,跨页 fragment 要抓目标页才能判。
**触发(trigger)**: 1) 提取带 fragment 的 href;2) 在目标页(本页或已抓取缓存)DOM 查 id/`<a name>` 匹配;3) 无匹配即 warn。
**不修的条件(caveat)**: 断锚点不(直接)影响 SEO,然而它把"精确深链"降级为"页顶落点",所以一般建议高价值锚点链保持有效。但第三方页面的 fragment 你无法控制,只修站内互链与自有分发渠道。
**修复(fix)**: 目标页恢复旧 id(加别名)或改引用方 fragment;CMS 生成 heading 时输出稳定 slug id,别用序号。
**导出(export)**: Reports > Links > Broken Anchor Links
**关联(seealso)**: links-internal-broken、links-onclick;[semantic-html.md](semantic-html.md)

#### links-onclick [待核 ID]
- 名称/类型: onclick 导航 —— warning · 优先级 medium · 输出 WARN(源表 warn;onclick 导航替代 href)
**这意味(what)**: 用元素 onclick 事件做页面导航——`<a>` 无真实 href(或 href="#" 配 onclick 跳转)。
**为什么(why)**: 引擎与多数不执行 JS 的爬虫只认 href:onclick 导航对它们是死路,后续页面失去这条发现路径;中键/右键新开标签、悬停预览、状态栏 URL 全部失效,键盘与辅助技术同样受损。与 [rendering-seo.md](rendering-seo.md) 的口径一致:导航必须在初始 HTML 的可跟随 href 里。
**触发(trigger)**: `<a>` 无 href 或 href="#"/javascript: 且带 onclick 属性(含常见前端路由跳转特征)即 warn。
**不修的条件(caveat)**: onclick 导航不(直接)惩罚,然而它把不执行 JS 的访问者挡在门外,所以一般建议 href 写真实目标 URL、JS 只做增强。但 SPA 视图切换用真实 href+pushState 的渐进增强是正解形态,不是豁免。
**修复(fix)**: `<a href="/real/url">` 为主体,onclick preventDefault 仅做无刷新增强;纯动作元素(提交/展开)改 button。
**导出(export)**: Reports > Links > Onclick Navigation
**关联(seealso)**: links-malformed-href、js-content-dependency;[rendering-seo.md](rendering-seo.md)、[semantic-html.md](semantic-html.md)

#### links-nofollow-external [待核 ID]
- 名称/类型: 外链 nofollow 滥用 —— warning · 优先级 low · 输出 WARN(源表 warn;nofollow 滥用;与 links-nofollow-internal 互补)
**这意味(what)**: 站内出站链接被大面积加 rel=nofollow——包括自然引用的权威来源、合作伙伴等本应正常投票的链接。
**为什么(why)**: nofollow 的语义是"不为该链接背书":全站外链一刀切 nofollow 等于声明"我引用的一切都不算数"——E-E-A-T 的引用信号(eeat-citations)同时被自己关掉。正当用法只有三类:付费/赞助(rel=sponsored)、UGC(rel=ugc)、不信任目标。与 links-nofollow-internal 互补:一个错在自我否定,一个错在过度防御。
**触发(trigger)**: 跨域 `<a>` 带 rel=nofollow(不含 sponsored/ugc)占比超出自然水平(阈值源表未公布[待核]),或权威引用源(.gov/.edu/论文)被 nofollow 即 warn。
**不修的条件(caveat)**: nofollow 外链不影响本页排名,然而它同时放弃引用背书与链接语义准确性,所以一般建议只给三类正当用途。但法务要求全站外链免责的场景(金融合规)可整体保留,报告记豁免。
**修复(fix)**: 自然引用去 nofollow;付费位改 sponsored;UGC 区改 ugc;CMS 若默认全局加 nofollow,改模板开关。
**导出(export)**: Reports > Links > Nofollow External Links
**关联(seealso)**: links-nofollow-internal、eeat-citations;[robots-txt-reference.md](robots-txt-reference.md)、[deprecated-signals.md](deprecated-signals.md)

### Images(14 条,权重 8%)

alt 缺失=fail;alt 泛化("image"/文件名)=warn;alt 长度 **5-125 字符**=warn;宽高属性缺失=warn(防 CLS);below-fold 须 `loading="lazy"`=warn;现代格式(WebP/AVIF 比 JPEG/PNG 小 30-50%)=warn;体积=warn;srcset 响应式=warn;图片 404=fail;figure 缺 figcaption=warn;文件名(IMG_001.jpg 坏/red-running-shoes.jpg 好)=warn;**内联 SVG >5KB 应外链**=warn;picture 缺 img 回退=fail;内容图用 CSS background(引擎读不到)=warn。

**解释层(6 条;ID 未公布原文,标 [待核])**

#### images-alt [待核 ID]
- 名称/类型: alt 缺失/长度 —— issue(缺失)/warning(长度) · 优先级 high(缺失)/low(长度) · 输出 CRITICAL(缺失,源表 fail)/WARN(长度,源表 warn:5-125 字符区间)
**这意味(what)**: 该 URL 的内容图缺 alt 属性,或 alt 长度在 5-125 字符建议区间之外(泛化 alt"image"/文件名式另有条目)。
**为什么(why)**: alt 是无障碍的硬需求——屏幕阅读器用户完全依赖它"看"图;也是图片搜索理解图意的首要文本信号。**缺 alt 不伤害页面,只是错失描述**,所以长度问题仅 low、缺失因无障碍合规缺不得而建议 high。**装饰图空 alt(alt="")是正确做法**,不是缺失:它告诉 SR 跳过,别把噪声读给用户。
**触发(trigger)**: 1) `<img>` 无 alt 属性(注意:与 alt="" 是两回事!)→ fail;2) alt 长度 <5 或 >125 字符 → warn。
```html
<!-- pass --> <img src="shoe.jpg" alt="红色跑步鞋侧面图,鞋底加厚">
<!-- fail --> <img src="shoe.jpg">
<!-- pass(装饰图刻意留空)--> <img src="divider.png" alt="">
<!-- warn(超 125 字符的流水账描述)-->
```
**不修的条件(caveat)**: alt 不(直接)影响网页排名,然而影响图片搜索流量与无障碍合规,所以一般建议内容图全配。但纯装饰图应刻意留空——写满关键词反而是错。
**修复(fix)**: 内容图写"图里有什么"(不是文件名、不是关键词堆);装饰图用空 alt 或 role="presentation";复杂图表用 figcaption 做长描述。
**导出(export)**: Reports > Images > Alt Missing / Alt Length
**关联(seealso)**: core-title(同款"长度主观"哲学);[semantic-html.md](semantic-html.md)

#### images-alt-generic [待核 ID]
- 名称/类型: 泛化/文件名式 alt —— warning · 优先级 low · 输出 WARN(源表 warn;"image"/文件名)
**这意味(what)**: 内容图的 alt 是泛化词("image"/"photo"/"图片")或直接复述文件名(img001),没有描述图内内容。
**为什么(why)**: 泛化 alt 对图片搜索与屏幕阅读器约等于没有:图片搜索靠 alt 理解图意,SR 用户听到 "image" 毫无信息。与 images-alt(缺失/长度)同族互补:那条管"没写/写多长",本条管"写了但零信息量"。
**触发(trigger)**: 1) alt 值命中泛化词表(image/photo/picture 等[词表源表未公布,待核])即 warn;2) alt 与 src 文件名(去扩展名)相同即 warn;3) 装饰图空 alt 不判(正确做法)。
**不修的条件(caveat)**: alt 文案质量不(直接)影响网页排名,然而决定图片搜索的匹配面与无障碍信息量,所以一般建议写"图里有什么"。但 logo 类小图的短描述(alt="ExampleCorp 商标")属可接受形态。
**修复(fix)**: 按图内容写名词性描述(对象+动作+语境);别把关键词堆进 alt(那归 content-keyword-stuffing);模板无法自动生成时留空待人工补,也别输出文件名。
**导出(export)**: Reports > Images > Generic Alt Text
**关联(seealso)**: images-alt;[semantic-html.md](semantic-html.md)、[image-search-seo.md](../content/image-search-seo.md)

#### images-dimensions [待核 ID]
- 名称/类型: 宽高属性缺失(尺寸家族) —— warning · 优先级 medium · 输出 WARN(源表 warn;防 CLS)
**这意味(what)**: `<img>` 缺 width/height 属性(也无 aspect-ratio 兜底),浏览器无法预留占位。
**为什么(why)**: 缺宽高时图片到位后布局重排,直接推高 CLS(阈值见 [cwv-playbook.md](cwv-playbook.md));现代浏览器按属性计算宽高比,加载前就留好空间。本家族其余规则同构(缺信号 warn 档):srcset 响应式缺失=warn、figure 缺 figcaption=warn、文件名无描述性(IMG_001.jpg 坏/red-running-shoes.jpg 好)=warn、内联 SVG >5KB 应外链=warn;picture 缺 img 回退=**fail** 档(不支持环境整图消失);图片 404=**fail** 档(与 links-internal-broken 同构的断链家族)。
**触发(trigger)**: 1) `<img>` 无 width/height 且无 CSS aspect-ratio 即 warn;2) 家族各小条按上列阈值判。
**不修的条件(caveat)**: 宽高不(直接)影响 SEO,然而它是 CLS 的最大可控因子之一,所以一般建议模板全配。但已用 CSS aspect-ratio 或 srcset+sizes 覆盖同需求的场景,属性缺失可视为等价实现。
**修复(fix)**: CMS/构建管道存原始尺寸并输出 width/height;动态尺寸图用 aspect-ratio;响应式配 srcset+sizes;figure 配 figcaption。
**导出(export)**: Reports > Images > Missing Dimensions
**关联(seealso)**: images-modern-formats、perf-dom-size;[cwv-playbook.md](cwv-playbook.md)

#### images-modern-formats [待核 ID]
- 名称/类型: 老旧图片格式/传输体积 —— warning · 优先级 low · 输出 WARN(源表 warn;WebP/AVIF 比 JPEG/PNG 小 30-50%;与 Performance 节 perf-image-encoding 同一事实的两面)
**这意味(what)**: 页面图片仍是 JPEG/PNG 老格式且未提供 WebP/AVIF(协商或 picture 回退),或单图传输体积过大。
**为什么(why)**: WebP/AVIF 同画质小 30-50%(源表口径),省下的字节直接改善 LCP 与页面总重。perf 侧同源规则 perf-image-encoding(渲染专属)判**传输 >100KB=warn、BMP/TIFF=fail**——本条看"格式供给",那条看"实际传输",命中其一就该动手。
**触发(trigger)**: 1) img src 无 .webp/.avif 且响应无格式协商(Accept/Vary)即 warn;2) 渲染口径:单图传输 >100KB=warn、BMP/TIFF=fail。
**不修的条件(caveat)**: 格式不影响图片相关性判定,然而传输体积是 LCP 的一半战场,所以一般建议全站切现代格式。但图片本就 <30KB 且 CMS 无转换能力的场景,收益排序靠后。
**修复(fix)**: 构建/CDN 层自动转 WebP/AVIF+picture 回退;大图压到展示分辨率;截图类 PNG 走有损压缩;验收看单图传输量。
**导出(export)**: Reports > Images > Modern Formats / Reports > Performance > Image Encoding
**关联(seealso)**: perf-page-weight、images-lazy;[cwv-playbook.md](cwv-playbook.md)、[image-search-seo.md](../content/image-search-seo.md)

#### images-lazy [待核 ID]
- 名称/类型: loading="lazy" 家族 —— warning · 优先级 medium · 输出 WARN(源表 warn;below-fold 须 lazy;首屏图禁 lazy=perf-lazy-above-fold)
**这意味(what)**: 折叠线以下的图没加 loading="lazy",或首屏图(尤其 LCP 图)反而加了 lazy。
**为什么(why)**: 两个方向伤同一指标:下页图不 lazy=全部抢首屏带宽,LCP 被非关键图拖慢;首屏图 lazy=LCP 资源被延迟加载。native lazy 已全浏览器支持,零脚本成本,属于"一行属性换半个 LCP"的修复。
**触发(trigger)**: 1) below-fold 图无 loading="lazy" 即 warn;2) 首屏/LCP 图带 loading="lazy" 即 warn(Performance 侧 perf-lazy-above-fold)。
**不修的条件(caveat)**: lazy 属性不影响图片索引(仍会被抓取),然而它调度首屏带宽,所以一般建议 below-fold 全配。但首屏边缘图(是否在视口随设备变化)宁可不 lazy——误 lazy 的白屏代价大于误加载的带宽代价。
**修复(fix)**: 模板按位置分流:首屏/LCP 图 eager+fetchpriority=high(见 perf-lcp-hints),其余 lazy;首屏判定以常见移动视口为准。
**导出(export)**: Reports > Images > Lazy Loading
**关联(seealso)**: perf-lcp-hints、perf-page-weight;[cwv-playbook.md](cwv-playbook.md)

#### images-css-background [待核 ID]
- 名称/类型: 内容图用 CSS background —— warning · 优先级 medium · 输出 WARN(源表 warn;引擎读不到)
**这意味(what)**: 承载内容信息的图(产品图/文章配图/图表)用 CSS background-image 呈现,而非 `<img>`。
**为什么(why)**: 引擎把 background 归为样式,不作为内容图索引——图片搜索完全收不到,alt/宽高/srcset/lazy 一整套图片优化全部不可用。背景图的合理域是装饰;内容图的合理域是 img(或 picture/svg)。
**触发(trigger)**: 主内容区的信息图走 background-image(URL 提取自内联样式与样式表)且无对应 img 语义即 warn。
**不修的条件(caveat)**: 纯装饰背景(渐变/纹理/氛围图)用 background 是正确做法,不判;只有当图承载内容语义(用户需要"看懂"它)时才构成问题——判定依赖"信息图"识别,命中后建议人工复核再改。
**修复(fix)**: 内容图改 `<img>` 带 alt/宽高/现代格式;装饰保留 background;图表类用 svg+figcaption 或 img+长描述。
**导出(export)**: Reports > Images > Content Images in CSS
**关联(seealso)**: images-alt-generic;[semantic-html.md](semantic-html.md)

### Security(26 条,权重 8%)

非 HTTPS=fail;HTTP 不 301 到 HTTPS=warn;缺 HSTS(`max-age=31536000; includeSubDomains`)/CSP/X-Frame-Options(DENY/SAMEORIGIN)/nosniff/Permissions-Policy/Referrer-Policy(strict-origin-when-cross-origin)/COOP(`same-origin`,防 tabnabbing)=各 warn;`target=_blank` 缺 noopener/noreferrer=warn;表单 action 非 HTTPS=warn/fail;混合内容=warn/fail;`security-csp-xss`(CSP 是否真约束脚本:'unsafe-inline' 无 nonce=不设防;无 CSP 时按权重 0 报,避免与 security-csp 双重扣)/`security-info-disclosure`(Server 带版本号/X-Powered-By=warn,裸 `Server: nginx` 过)/`security-paste-blocking`(onpaste 阻止粘贴=fail,毁密码管理器)/`security-trusted-types`(仅已设 CSP 的站评,`require-trusted-types-for 'script'`)/`security-leaked-secrets`(AWS key/API token/私钥/数据库 URL=fail)/`security-password-http`(HTTP 页密码框=fail)/协议相对 URL `//`=warn;Cookie 三旗(Secure/HttpOnly/SameSite)=warn/fail;**Cookie 寿命 >400 天上限=warn**;SSL 到期=warn/fail;**TLS 须 1.2+**(1.0/1.1=warn/fail);SRI(跨域脚本/stylesheet 须 integrity hash)=warn;混淆脚本(长高熵内联脚本调 eval/Function/atob)=warn;品牌登录链指向品牌或本域=warn。

**解释层(6 条,第三批;ID 未公布原文的按家族命名法推得并标 [待核];安全头落地清单另见 [validation-guide.md](validation-guide.md) C28)**

#### security-https [待核 ID]
- 名称/类型: HTTPS 与混合内容 —— issue/warning · 优先级 critical · 输出 CRITICAL(非 HTTPS 与 fail 档)/WARN(不 301、warn 档)(源表:非 HTTPS=fail;HTTP 不 301 到 HTTPS=warn;表单 action 非 HTTPS=warn/fail;混合内容=warn/fail)
**这意味(what)**: 页面仍以 HTTP 服务(HTTP 版可直达不 301),或 HTTPS 页引用 HTTP 子资源、表单提交到 HTTP。
**为什么(why)**: HTTPS 是官方页面体验信号之一(现行观测入口:GSC 的 HTTPS 报告与 CWV 报告),也是浏览器信任基线——HTTP 页在地址栏被标"不安全",表单走 HTTP 等于明文送凭据。混合内容里被动型(图/音视频)被浏览器自动升级或降级处理,主动型(脚本/iframe)直接被拦——页面功能与评估双碎。
**触发(trigger)**: 1) 页面协议非 https 即 fail;2) http 版返回 200 不 301 即 warn;3) `<form action="http://…">` 即 warn/fail;4) HTTPS 页含 http:// 子资源即 warn/fail(主动型资源取重档)。
**不修的条件(caveat)**: HTTPS 对排名是小信号,然而缺失联动浏览器警告与表单明文,所以一般建议全站 https+301。但内网/预发环境的 http 是部署形态,不在本条评估面。
**修复(fix)**: 全站 301 到 https(单一 host 形态,见 technical-url-consistency);子资源/表单/canonical 全部 https 化;上 HSTS(见 security-headers)防回退。
**导出(export)**: Reports > Security > HTTPS & Mixed Content
**关联(seealso)**: security-headers、security-tls;[validation-guide.md](validation-guide.md)

#### security-headers [待核 ID]
- 名称/类型: 安全响应头家族 —— warning · 优先级 medium · 输出 WARN(源表各=warn:HSTS `max-age=31536000; includeSubDomains`/CSP/X-Frame-Options(DENY/SAMEORIGIN)/nosniff/Permissions-Policy/Referrer-Policy(strict-origin-when-cross-origin)/COOP(`same-origin`,防 tabnabbing))
**这意味(what)**: 七个安全响应头任一缺失:HSTS、CSP、X-Frame-Options、X-Content-Type-Options(nosniff)、Permissions-Policy、Referrer-Policy、COOP。
**为什么(why)**: 每个头各管一面:HSTS 防协议降级剥离(缺了首访 http 可被中间人劫持);CSP 约束脚本注入面;X-Frame-Options 防 clickjacking 嵌套;nosniff 防 MIME 嗅探错配执行;Permissions-Policy 收 API 权限;Referrer-Policy 控引荐信息外泄;COOP(same-origin)防 tabnabbing 类跨窗引用。SEO 侧关联是间接的:可被任意嵌套/注入的页面不是引擎信任的展示形态。CSP 的有效性另由 security-csp-xss 深化('unsafe-inline' 无 nonce=不设防;无 CSP 时按权重 0 报,避免与缺失双重扣),security-trusted-types 仅对已设 CSP 的站评 `require-trusted-types-for 'script'`。
**触发(trigger)**: 响应头逐一断言存在与推荐值(照抄源表:HSTS `max-age=31536000; includeSubDomains`;XFO DENY/SAMEORIGIN;RP strict-origin-when-cross-origin;COOP same-origin);缺失即 warn。
**不修的条件(caveat)**: 安全头不(直接)影响排名,然而它们是站点治理质量的可见面与真实攻击面的闸门,所以一般建议按 C28 清单补齐。但 CSP 要灰度上线(先 Report-Only 观察),一次性 enforce 打挂第三方脚本反成事故。
**修复(fix)**: 按 [validation-guide.md](validation-guide.md) C28 五头起步(HSTS/CSP/nosniff/XFO/RP);CSP 走 Report-Only 灰度;CDN/网关层统一注入。
**导出(export)**: Reports > Security > Security Headers
**关联(seealso)**: security-https、technical-content-type;[validation-guide.md](validation-guide.md)

#### security-tls [待核 ID]
- 名称/类型: TLS 版本与证书 —— warning/issue · 优先级 high · 输出 WARN/CRITICAL(源表:SSL 到期=warn/fail;TLS 须 1.2+,1.0/1.1=warn/fail)
**这意味(what)**: TLS 证书临期或已过期,或协议版本低于 1.2(1.0/1.1)。
**为什么(why)**: 过期证书让全部主流浏览器弹全页警告——流量断崖,引擎侧也随之抓取失败;TLS 1.0/1.1 已被 IETF 废弃且被主流浏览器禁用,老协议同时是降级攻击面。warn/fail 分型按临期程度与协议版本[待核:常见分型为临期=warn、已过期=fail]。
**触发(trigger)**: 1) 证书 notAfter 进入预警窗(窗口阈值源表未公布[待核])→ warn;已过期 → fail;2) 协商协议 <TLS1.2 → warn/fail。
**不修的条件(caveat)**: 证书与协议不(直接)影响内容排名,然而过期即全站不可达,是可用性事故级,所以一般建议自动续期+到期告警。但多证书/多边缘节点的站先盘点覆盖面再统一切 1.2+,避免漏节点造成部分用户不可达。
**修复(fix)**: ACME 自动续期(如 cert-manager);notAfter 双阈值告警(30/7 天);TLS 下限 1.2(逐步 1.3),关闭 1.0/1.1。
**导出(export)**: Reports > Security > TLS & Certificate
**关联(seealso)**: security-https;[validation-guide.md](validation-guide.md)

#### security-cookies [待核 ID]
- 名称/类型: Cookie 旗标与寿命 —— warning · 优先级 medium · 输出 WARN/CRITICAL(源表:三旗 Secure/HttpOnly/SameSite=warn/fail;寿命 >400 天=warn)
**这意味(what)**: Cookie 缺 Secure/HttpOnly/SameSite 旗标,或 Set-Cookie 的 max-age/expires 超过 400 天。
**为什么(why)**: 三旗各堵一类:Secure 限 https 传输(防明文截获)、HttpOnly 禁 JS 读取(防 XSS 窃会话)、SameSite 防跨站携带(CSRF);400 天是浏览器统一持久化上限,超限值被截断——声明与现实不符。warn/fail 分型按 cookie 用途[待核:常见分型为会话/鉴权类缺旗标取 fail 侧]。
**触发(trigger)**: 逐一解析 Set-Cookie:1) 缺任一旗标 → warn/fail;2) max-age/expires >400 天 → warn。
**不修的条件(caveat)**: Cookie 旗标不影响 SEO,然而会话安全缺口的后果(账号接管)会以最差方式登上 SERP,所以一般建议三旗全配。但第三方嵌入要求的宽松 SameSite 场景,用分区 cookie(CHIPS)替代裸放松。
**修复(fix)**: 会话 cookie `Secure; HttpOnly; SameSite=Lax`;持久 cookie ≤400 天并按业务再收;跨站场景评估 CHIPS/First-Party Sets。
**导出(export)**: Reports > Security > Cookie Flags
**关联(seealso)**: legal-cookie-consent、technical-tagging;[validation-guide.md](validation-guide.md)

#### security-link-integrity [待核 ID]
- 名称/类型: 链接与引用安全家族 —— warning · 优先级 medium · 输出 WARN(源表各=warn:target=_blank 缺 noopener/noreferrer;协议相对 URL `//`;跨域脚本/stylesheet 缺 SRI integrity;品牌登录链须指向品牌或本域)
**这意味(what)**: 四项链接/引用卫生任一:`target=_blank` 的链接缺 rel=noopener/noreferrer;URL 用协议相对 `//example.com` 形态;跨域脚本与样式表没有 integrity(SRI)hash;登录/支付类品牌入口链接指向非品牌域。
**为什么(why)**: noopener 防新窗口反向操纵 opener(tabnabbing 的页面侧防线);协议相对 URL 在 http 上下文解析成 http,与全站 https 化冲突且行为依赖上下文;SRI 缺失时第三方脚本被篡改即直接进你页面(供应链注入面);品牌登录链指向陌生域是钓鱼的教科书形态——引擎与用户都对"登录入口不在品牌域"高度敏感。
**触发(trigger)**: 1) `<a target="_blank">` 的 rel 不含 noopener 即 warn;2) href 以 `//` 开头即 warn;3) 跨域 `<script src>`/`<link rel="stylesheet">` 无 integrity 属性即 warn;4) 登录/账单类锚文本的 href 域 ∉ {本域,已知品牌域} 即 warn。
**不修的条件(caveat)**: 家族单项不(直接)影响排名,然而 SRI 与登录链两项是真实攻击/钓鱼面,所以一般建议一次配齐。但第三方面向无版本化 URL 的脚本(内容随构建变)无法静态钉 SRI,先换版本化 URL 再上。
**修复(fix)**: target=_blank 统一 `rel="noopener noreferrer"`;协议相对改 https 绝对 URL;第三方资源走版本化 URL+SRI(integrity+crossorigin);登录链收敛品牌域或已知 IdP 域并公示。
**导出(export)**: Reports > Security > Link & Reference Integrity
**关联(seealso)**: links-malformed-href、security-headers;[head-elements.md](head-elements.md)

#### security-content-danger [待核 ID]
- 名称/类型: 内容层危险信号家族 —— issue · 优先级 critical · 输出 CRITICAL(fail 档)/WARN(指纹与混淆档)(源表:泄露密钥 AWS key/API token/私钥/数据库 URL=fail;HTTP 页密码框=fail;onpaste 阻止粘贴=fail;Server 带版本号/X-Powered-By=warn,裸 `Server: nginx` 过;混淆脚本特征=warn)
**这意味(what)**: 页面/响应里出现五类危险信号:硬编码密钥、HTTP 明文密码表单、阻止粘贴的密码框、服务器版本指纹、混淆可疑脚本。
**为什么(why)**: 泄露密钥是最硬的事故(云端凭据被扫走即被刷账单/挂马);HTTP 密码框等于明文广播凭据;onpaste 阻断摧毁密码管理器(用户被迫手打,实际退回弱密码);Server/X-Powered-By 版本指纹给攻击者递漏洞清单;长高熵内联脚本调 eval/Function/atob 的混淆特征是被挂码后的常见形态(security-info-disclosure 与混淆脚本两条并入本条陈述)。
**触发(trigger)**: 1) 页面文本/脚本命中密钥形态(AWS key/API token/私钥头/数据库 URL)→ fail;2) http 页含 `type=password` → fail;3) 密码/确认框 onpaste 返回 false 或 preventDefault → fail;4) Server 头带版本号或存在 X-Powered-By → warn(裸 `Server: nginx` 通过);5) 内联脚本高熵长串+eval/Function/atob 组合 → warn。
**不修的条件(caveat)**: fail 档三项没有"可合理不修"——它们不是 SEO 取舍是安全事故;warn 档(版本指纹/混淆特征)有误报面(合法加固混淆的第三方组件),命中后先比对官方产物再定性。
**修复(fix)**: 密钥立即轮换+从源码与构建产物移除(历史提交要 purge);密码页强制 https;移除 onpaste 阻断;Server 头去版本、删 X-Powered-By;混淆脚本溯源验签,来源不明的直接下线。
**导出(export)**: Reports > Security > Content Danger Signals
**关联(seealso)**: security-https、security-link-integrity;[validation-guide.md](validation-guide.md)

### Technical SEO(18 条,权重 7%)

robots.txt 存在/语法=warn;sitemap 存在/格式=warn;URL 结构(小写+连字符)=warn;尾斜杠一致性=warn;www 一致性 301=warn;自定义 404=warn;soft-404(200 但错误内容)=warn;5xx=fail;**非 404 的 4xx(403/410 等)=warn**;超时=fail;Content-Type 错=warn/fail;**200 空 HTML(fhead/body 皆空)=fail**;`technical-form-get-method`(GET 表单产生可抓取查询串 URL=warn);**多 GTM 容器/多 GA 属性(>1 个不同 ID)=warn**;`technical-consent-mode`(Google 标签须配 consent update)=warn。

**解释层(10 条,第三批;ID 未公布原文的按家族命名法推得并标 [待核])**

#### technical-5xx [待核 ID]
- 名称/类型: 服务器错误与超时 —— issue · 优先级 critical · 输出 CRITICAL(源表:5xx=fail;超时=fail)
**这意味(what)**: 该 URL 返回 5xx 状态码,或连接/DNS 层直接超时。
**为什么(why)**: 5xx 告诉引擎"服务器出问题":短时出现会降低抓取速度,持续出现时已编入索引的 URL 会被移出索引——这是少数"放着不管就掉索引"的故障(处置表见 [http-status-codes.md](http-status-codes.md));DNS/连接超时等网络错误按同档处理。单页 5xx 指应用层,全站 5xx 指基础设施,修复路径不同。
**触发(trigger)**: 1) 响应状态 5xx 即 fail;2) 连接/DNS/TLS 握手超时即 fail;3) 输出按影响面分型(单页/全站)。
**不修的条件(caveat)**: 计划内维护应返回 503+Retry-After(告诉引擎稍后再来),用 200 返回维护页反而制造 soft-404;真故障无豁免,修的是稳定性本身。
**修复(fix)**: 全站 5xx 查基础设施(部署窗口/数据库连接池);单页 5xx 查应用日志;维护窗口统一 503+Retry-After;要降抓取速度短期用 429/503,不用 401/403。
**导出(export)**: Reports > Technical SEO > Server Errors & Timeouts
**关联(seealso)**: technical-empty-html、technical-soft-404;[http-status-codes.md](http-status-codes.md)、[log-analysis.md](log-analysis.md)

#### technical-empty-html [待核 ID]
- 名称/类型: 200 空 HTML —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;head/body 皆空)
**这意味(what)**: URL 返回 200,响应体却是 head 与 body 都为空的 HTML 壳。
**为什么(why)**: 200+空壳是最高危的"假正常":索引流程收到"成功"却没有可索引内容,GSC 归入 soft 404 类目;客户端渲染失败(js-runtime-hygiene 的未捕获异常)也会呈现这个形态。引擎视角:页面存在但什么都没有,慢性退索引。
**触发(trigger)**: 1) 状态 200;2) 解析后 head 与 body 均无有效内容节点即 fail。
**不修的条件(caveat)**: 无豁免——200 必须配内容;确无内容的地址应给 404/410 或 301,而不是 200 空壳。
**修复(fix)**: 查渲染管道(SSR 失败回退空模板是常见肇因);模板兜底至少输出错误说明+正确状态码;CI 对发布产物做"空 HTML"断言。
**导出(export)**: Reports > Technical SEO > Empty HTML
**关联(seealso)**: technical-5xx、technical-soft-404、js-runtime-hygiene;[http-status-codes.md](http-status-codes.md)

#### technical-soft-404 [待核 ID]
- 名称/类型: soft 404 —— issue · 优先级 high · 输出 WARN(源表 warn;200 但错误内容)
**这意味(what)**: URL 返回 200,页面内容却是"未找到/已下架"的错误态。
**为什么(why)**: 引擎对 200 页照常走索引流程,内容是错误信息时被判 soft 404——占着"正常响应"的抓取预算却没有可服务的内容;它们在 GSC 索引报告里混成噪音,真假问题难分。典型来源:下架商品页返回 200"商品不存在";把大量删除页统一 301 到首页/无关页同样可能被判 soft 404(官方口径见 [http-status-codes.md](http-status-codes.md) 第二节)。
**触发(trigger)**: 1) 状态 200;2) 内容命中错误态特征("未找到/已下架/page not found"文案、空分类、搜索无结果壳、渲染失败空壳)即 warn。
**不修的条件(caveat)**: 判定是内容启发不是状态码,误报存在(正文合法引用"not found"字样),所以一般建议命中后人工抽查再改状态码。但确要保留的"内容已移除"说明页(带后续指引)属正当形态,配 noindex 即可。
**修复(fix)**: 真没了→真 404/410;有替代→301 到最近亲内容页(不是首页);保留说明页→加 noindex。
**导出(export)**: Reports > Technical SEO > Soft 404
**关联(seealso)**: technical-4xx-non404、technical-custom-404;[http-status-codes.md](http-status-codes.md)

#### technical-4xx-non404 [待核 ID]
- 名称/类型: 非 404 的 4xx —— warning · 优先级 medium · 输出 WARN(源表 warn;403/410 等)
**这意味(what)**: 页面返回 403、410、451 等 404 之外的 4xx 状态。
**为什么(why)**: 各 4xx 语义不同,审计价值在分清"状态码用对了吗":401/403 是权限语义(引擎视为不存在,但官方明确不能拿来限制抓取速度——那是 429/503 的职责);410 是明确的永久下线声明;451 是法律移除。除 429 外引擎对 4xx 的处理方式相同,误用主要污染你自己的监控分类与维护诊断。
**触发(trigger)**: 响应状态 ∈ 4xx 且 ≠404 即 warn(404 本身不算错误,由内链/sitemap 交叉规则管)。
**不修的条件(caveat)**: 4xx 状态不惩罚站点(404 是正常 web 形态),然而选错码会误导引擎与监控,所以一般建议按语义选码。但登录墙内容返回 401/403 是正当设计,别为审计绿灯改成 404。
**修复(fix)**: 永久下线→410;临时不可用→503+Retry-After;限流→429;无权访问→401/403 保持。
**导出(export)**: Reports > Technical SEO > Non-404 Client Errors
**关联(seealso)**: technical-soft-404、technical-5xx;[http-status-codes.md](http-status-codes.md)

#### technical-custom-404 [待核 ID]
- 名称/类型: 自定义 404 页 —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: 站点 404 时返回服务器默认错误页,而非带导航与搜索的自定义 404 页。
**为什么(why)**: 404 本身不伤 SEO,伤的是 404 之后用户去留:默认错误页零出路,用户直接关站;自定义 404 给导航/搜索/热门内容,把撞错 URL 的流量接回站内。对引擎,自定义 404 也证明错误态是设计过的而非配置事故。
**触发(trigger)**: 请求不存在路径;返回 404 但响应体为服务器默认页(无站内导航特征/体积极小)即 warn;404 返回 200 另归 technical-soft-404。
**不修的条件(caveat)**: 404 状态码不(直接)影响排名,然而它决定错误流量的回收率,所以一般建议配自定义页。但纯 API/内部服务不需要人类可读 404。
**修复(fix)**: 404 模板带站点导航+站内搜索+热门链接;保持真 404 状态码;别自动跳首页(制造 soft-404)。
**导出(export)**: Reports > Technical SEO > Custom 404 Page
**关联(seealso)**: technical-soft-404、technical-4xx-non404;[http-status-codes.md](http-status-codes.md)

#### technical-robots-txt [待核 ID]
- 名称/类型: robots.txt 存在性与语法 —— warning · 优先级 high · 输出 WARN(源表 warn)
**这意味(what)**: 站点没有 robots.txt,或文件存在但含语法错误(非法指令/拼写错的键/未闭合组)。
**为什么(why)**: robots.txt 是抓取层第一道闸:不存在时按"全部允许"处理(失去 AI 爬虫策略等声明载体);存在但语法坏时引擎按容错解析——你写的 Disallow 可能没按你以为的生效。它还是 crawl-* 交叉规则(crawl-sitemap-disallowed 等)的前置输入,坏语法会级联污染下游判定。
**触发(trigger)**: 1) /robots.txt 404/5xx → 缺失档;2) RFC 9309 解析报语法错 → 语法档;均 warn。
**不修的条件(caveat)**: 缺 robots.txt 不(直接)影响 SEO(全允许也是合法状态),然而失去声明面与审计输入,所以一般建议放显式文件。但确无任何屏蔽需求的小站,空文件与缺文件等价,可记豁免。
**修复(fix)**: 提交显式 robots.txt(至少含 Sitemap 行,见 crawl-sitemap-in-robotstxt);用 RFC 9309 校验器过一遍;模板生成禁手维护([ai-crawler-policy.md](ai-crawler-policy.md) 口径)。
**导出(export)**: Reports > Technical SEO > Robots.txt Issues
**关联(seealso)**: crawl-sitemap-disallowed、crawl-blocked-resources、crawl-crawl-delay;[robots-txt-reference.md](robots-txt-reference.md)、[ai-crawler-policy.md](ai-crawler-policy.md)

#### technical-sitemap-existence [待核 ID]
- 名称/类型: sitemap 存在性与格式 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 站点没有可发现的 sitemap,或 sitemap 格式坏(XML 不合法/编码错/非 sitemap 结构)。
**为什么(why)**: sitemap 是发现与再抓取的加速器:格式坏时整文件被丢弃等于没有,GSC 提交也报解析错误。存在性按发现路径判:robots.txt Sitemap 行、/sitemap.xml 常规路径、GSC 声明。条数/体积/lastmod 质量/domain 一致性由 Crawlability 节 sitemap 家族分规则管,本条只立"有没有、能不能解析"。
**触发(trigger)**: 1) 无任何可发现 sitemap → 缺失档;2) XML 解析失败/缺 urlset 命名空间 → 格式档;均 warn。
**不修的条件(caveat)**: sitemap 是推荐机制不是排名因素,内链完整的小站缺失损失有限,所以一般建议核心站必配、极小站可缓。但无 sitemap 时 GSC 的提交与覆盖率诊断面也少一半,通常仍值得配。
**修复(fix)**: 生成器输出标准 XML(可选 gzip);robots.txt 声明+GSC 提交;校验命名空间与转义(& 用 &amp;)。
**导出(export)**: Reports > Technical SEO > Sitemap Issues
**关联(seealso)**: crawl-sitemap-url-limit、crawl-sitemap-lastmod、crawl-sitemap-in-robotstxt;[validation-guide.md](validation-guide.md)

#### technical-content-type [待核 ID]
- 名称/类型: Content-Type 错误 —— issue/warning · 优先级 medium · 输出 WARN/CRITICAL(源表 warn/fail;分型口径源表未公布[待核])
**这意味(what)**: 响应的 Content-Type 头与实际内容或用途不符:HTML 页声明成 text/plain、字体声明成 text/html、缺 charset 等。
**为什么(why)**: 引擎与浏览器按 Content-Type 决定解析路径:声明错时 HTML 被当纯文本(索引流程拿不到 DOM)、资源被按错误类型处理;缺 charset 触发编码猜测,与 mojibake(content-deploy-hygiene)同源;nosniff 生效时被误标的资源直接被拒执行。
**触发(trigger)**: 1) 主文档非 text/html(且非刻意的 data feed)即触发;2) 子资源 Content-Type 与扩展/内容嗅探不符即触发;warn/fail 按分型[待核:主文档误标取重档的常见分型]。
**不修的条件(caveat)**: 个别误标(注释类文件以 text/plain 服务)不影响 SEO 面,然而主文档误标等于把页面挡在解析之外,所以一般建议全站对齐。但刻意以非 HTML 类型服务的资源(JSON API/RSS)不属误报,注意剔除。
**修复(fix)**: 服务器 MIME 表对齐;HTML 显式 `text/html; charset=utf-8`;要上 nosniff 前先自查全部资源类型(见 security-headers)。
**导出(export)**: Reports > Technical SEO > Content-Type Mismatch
**关联(seealso)**: content-mime-broken、content-deploy-hygiene、security-headers;[http-status-codes.md](http-status-codes.md)

#### technical-url-consistency [待核 ID]
- 名称/类型: URL 形态一致性家族 —— warning · 优先级 medium · 输出 WARN(源表各=warn:URL 结构小写+连字符;尾斜杠一致性;www 一致性 301)
**这意味(what)**: 站点级 URL 形态不统一:大小写/分词符混用、同站尾斜杠两可、www 与非 www 双可达且不互 301。
**为什么(why)**: 三项都在制造"同内容多 URL":大小写敏感的服务器上 /About 与 /about 是两个 200;尾斜杠两可时引擎靠规范化猜;www 双可达是经典重复站点种子。它们是 url-shape(单页形态卫生)的站点级聚合面——[validation-guide.md](validation-guide.md) C3 检查项(四变体 301 到唯一规范 host)就是本条的落地。
**触发(trigger)**: 1) 站内 URL 混用大小写/下划线与连字符即 warn;2) 同路径带/不带尾斜杠均 200 即 warn;3) www 与非 www 均可达且无单向 301 即 warn。
**不修的条件(caveat)**: 一致性家族不(直接)影响单页排名,然而每项都在给规范化添噪音,所以一般建议定一种形态+301 收口。但历史 URL 的大写形态已积累外链时,保持现状+canonical 比强改更稳。
**修复(fix)**: 定规范形态(小写+连字符+固定尾斜杠策略+单 host),其余变体 301 到规范形;CMS 输出层统一;新内容从源头合规。
**导出(export)**: Reports > Technical SEO > URL Consistency
**关联(seealso)**: url-shape、crawl-canonical-form-drift、redirects-case-normalization;[redirects-canonical.md](redirects-canonical.md)、[validation-guide.md](validation-guide.md)

#### technical-tagging [待核 ID]
- 名称/类型: 埋点与表单卫生家族 —— warning · 优先级 low · 输出 WARN(源表各=warn:多 GTM 容器/多 GA 属性(>1 个不同 ID);consent mode;GET 表单)
**这意味(what)**: 三项埋点/表单卫生任一命中:页面加载 >1 个不同 ID 的 GTM 容器或 GA 属性;Google 标签未配 consent mode update;GET 表单产生可抓取的查询串 URL。
**为什么(why)**: 双容器/双属性是"两拨人各埋一套"的事故:双计、页面变重、数据口径分裂——SEO 决策的数据底座被毁;consent mode 缺失在欧盟市场意味着同意前信号丢失与合规缺口;GET 表单把用户输入变成 URL,爬虫沿结果页发散(与 url-search-indexed 同源),敏感参数还可能进日志与外泄。
**触发(trigger)**: 1) 页面 GTM 容器 ID 去重后 >1 或 GA 属性 >1 即 warn;2) 有 gtag/GTM 但无 consent 默认态+update 调用即 warn;3) `<form method=get>`(缺省即 GET)且 action 产生站内查询 URL 即 warn。
**不修的条件(caveat)**: 埋点卫生不影响排名本身,然而双计毁掉流量归因的可信度,所以一般建议收敛单容器。但迁移期新旧属性并行的双属性是临时合理态,报告标注截止日期。
**修复(fix)**: 容器收敛为一个,历史属性经 GTM 转发;gtag 配 consent default+update(接 CMP,见 legal-cookie-consent);站内搜索表单结果页 noindex 或改 POST/前端路由。
**导出(export)**: Reports > Technical SEO > Tagging Hygiene
**关联(seealso)**: url-search-indexed、legal-cookie-consent、sd-searchaction;[gtm-implementation.md](gtm-implementation.md)、[ga4-implementation.md](ga4-implementation.md)

### Structured Data(19 条,权重 5%)

缺 JSON-LD=warn;JSON 语法坏=fail;缺 @type=warn;类型必填字段=warn;Article 须 headline/author/datePublished/image;BreadcrumbList(非首页,**≥2 个 itemListElement**)=info;FAQPage 每个 Question 须 name+acceptedAnswer.text=fail;LocalBusiness 须 name/address/telephone/geo;Organization 须 name/logo/sameAs;Product 须 offers(price/priceCurrency/availability)=fail;Review 须 itemReviewed/author/reviewRating;VideoObject 须 name/thumbnailUrl/uploadDate(时长 ISO 8601 如 PT1M30S);WebSite SearchAction 含 `{search_term_string}`=info。**实体图六查已吸收于 [entity-signal-checklist.md](entity-signal-checklist.md) 与 [validation-guide.md](validation-guide.md)**:entity-id(@id 绝对)/rating-scope(AggregateRating 不在 legal/account URL 且 ratingValue 可见)/entity-conflict(一 @id 两 logo/两电话)/entity-dangling(publisher/author/isPartOf 的 @id 须在爬取中声明)/entity-type-drift(同 @id 跨页同 @type)/entity-split(同名组织不挂两 @id)。

**解释层(5 条;ID 未公布原文的按家族命名法推得并标 [待核])**

#### sd-jsonld-missing [待核 ID]
- 名称/类型: 缺 JSON-LD —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: 页面没有任何 `<script type="application/ld+json">` 结构化数据。
**为什么(why)**: 结构化数据是实体消歧与 AI 引用的锚(套件口径见 [validation-guide.md](validation-guide.md) 与 [ai-crawler-policy.md](ai-crawler-policy.md));缺 JSON-LD 意味着把"我是什么"完全交给引擎猜。缺信号类:不惩罚,只放弃一层机器可读性,故 low。
**触发(trigger)**: DOM 无 ld+json script 节点即 warn(microdata/RDFa 载体是否豁免[待核:源表按 JSON-LD 判])。
**不修的条件(caveat)**: schema 不(直接)影响排名,然而影响富结果资格与 AI 摘要引用,所以一般建议至少配全站级 Organization+页面主类型。但登录墙内页/纯工具页可不配。
**修复(fix)**: 按页面类型配最小集(全站 Organization,文章 Article,产品 Product——各类型必填见 sd-required-fields 家族);模板化生成,勿手拼 JSON。
**导出(export)**: Reports > Structured Data > Missing JSON-LD
**关联(seealso)**: sd-json-syntax;[schema-templates.md](schema-templates.md)、[validation-guide.md](validation-guide.md)

#### sd-json-syntax [待核 ID]
- 名称/类型: JSON-LD 语法坏/缺 @type —— issue · 优先级 high · 输出 CRITICAL(语法坏,源表 fail)/WARN(缺 @type,源表 warn)
**这意味(what)**: ld+json 内容不是合法 JSON(尾逗号/单引号/未转义引号),或解析成功但缺 @type。
**为什么(why)**: 语法坏时整块被静默丢弃——写了等于没写,且多数 CMS 不报错,坏块能潜伏数月;缺 @type 则引擎无法路由到任何类型校验,注解同样悬空。这是"坏信号"档:存在但残缺比没有更隐蔽,语法坏判 fail。
**触发(trigger)**: 1) JSON.parse 失败即 fail;2) 解析成功但顶层无 @type 即 warn。
**不修的条件(caveat)**: 语法错误不产生负面排名信号(只是白写),然而它是静默失效——没有任何报错渠道,所以一般建议 CI 里对全部 ld+json 做 JSON.parse 断言;修复本身无豁免。
**修复(fix)**: 用 JSON.stringify 生成而非手写模板拼接;补 @type;上线前过 Rich Results Test 类校验器。
**导出(export)**: Reports > Structured Data > Invalid JSON-LD
**关联(seealso)**: sd-jsonld-missing、sd-required-fields;[validation-guide.md](validation-guide.md)

#### sd-required-fields [待核 ID]
- 名称/类型: 类型必填字段家族 —— issue/warning · 优先级 high(fail 档)/low(warn 档) · 输出 CRITICAL/WARN(源表:通用=warn;Product 缺 offers 与 FAQPage 缺结构=fail)
**这意味(what)**: 已部署的 schema 缺该类型的必填字段。源表口径照抄:Article 须 headline/author/datePublished/image;LocalBusiness 须 name/address/telephone/geo;Organization 须 name/logo/sameAs;Review 须 itemReviewed/author/reviewRating;VideoObject 须 name/thumbnailUrl/uploadDate(时长 ISO 8601 如 PT1M30S);Product 须 offers(price/priceCurrency/availability)=**fail**;FAQPage 每个 Question 须 name+acceptedAnswer.text=**fail**。
**为什么(why)**: 富结果与实体理解按"类型+必填"判资格:缺字段=该类型功能整体失效(Product 无 offers 则无价格类资格)。Product/FAQPage 判 fail 是"半残标记比缺失更浪费"的取舍。**注意 FAQPage 在此仅是对既有标记的结构校验**——FAQPage 富结果 2026-05-07 起全站停展,不要为 SERP 展示新增这类标记,真问答页用 QAPage(口径见 [deprecated-signals.md](deprecated-signals.md) 第一节)。
**触发(trigger)**: 按类型逐字段断言(清单照抄源表);缺任一必填:Product/FAQPage 走 fail 档,其余 warn 档。
**不修的条件(caveat)**: 缺必填不惩罚,然而该类型的机器理解整体落空,所以一般建议补齐或删类型。但 Organization 的 sameAs 在社交资产确实少时可先上子集、后补字段。
**修复(fix)**: 对照 [schema-templates.md](schema-templates.md) 每类型最小集补齐;数据源缺字段时模板应跳过该类型而非输出空壳。
**导出(export)**: Reports > Structured Data > Missing Required Fields
**关联(seealso)**: sd-json-syntax;[schema-templates.md](schema-templates.md)、[entity-signal-checklist.md](entity-signal-checklist.md)

#### sd-breadcrumblist [待核 ID]
- 名称/类型: BreadcrumbList —— opportunity · 优先级 low · 输出 INFO(源表 info;非首页,≥2 个 itemListElement)
**这意味(what)**: 非首页页面缺 BreadcrumbList,或已有但 itemListElement <2 个。
**为什么(why)**: 面包屑 schema 让 SERP 以层级路径替代裸 URL 展示,提升结果行可读性;也是站内层级的机器可读声明。源表给 info:纯增益项,缺了不扣分——两轴哲学里典型的 opportunity。
**触发(trigger)**: 1) 非首页无 BreadcrumbList 即 info;2) 有但 itemListElement <2 即 info;首页不需要面包屑。
**不修的条件(caveat)**: 面包屑 schema 不影响排名,然而影响 SERP 展示形态,所以一般建议有真实面包屑 UI 的页面配同源 schema。但扁平站(全站一层)没有层级可表达,硬造两级反而是错。
**修复(fix)**: 面包屑 UI 与 schema 用同一数据源生成;每级 name 与目标页 title 呼应;末级指当前页。
**导出(export)**: Reports > Structured Data > BreadcrumbList
**关联(seealso)**: sd-required-fields;[schema-templates.md](schema-templates.md)

#### sd-searchaction [待核 ID]
- 名称/类型: WebSite SearchAction —— opportunity · 优先级 insight · 输出 INFO(源表 info;target 须含 {search_term_string})
**这意味(what)**: 站点缺 WebSite+SearchAction 标记,或 potentialAction 的 target 模板没含字面 {search_term_string} 占位符。
**为什么(why)**: SearchAction 是品牌词 sitelinks 搜索框的资格声明(前提是有真实站内搜索);占位符拼错(?q={searchterm} 之类)整条失效。info 级:展示位由引擎自主决定,缺了无损。
**触发(trigger)**: WebSite 类型的 potentialAction target URL 模板须含字面 {search_term_string};缺失或占位符变形即 info。
**不修的条件(caveat)**: 配置只是资格声明不保证展示,所以一般建议有站内搜索的站顺手配上。注意与 url-search-indexed 不矛盾:搜索功能要真实可用,搜索**结果页**要 noindex——一个对用户,一个对索引。
**修复(fix)**: WebSite schema 配 SearchAction,target 用真实搜索 URL+{search_term_string};搜索结果页模板加 noindex。
**导出(export)**: Reports > Structured Data > SearchAction
**关联(seealso)**: url-search-indexed;[schema-templates.md](schema-templates.md)

### Content(27 条,权重 5%)

词数 **≥300 过/100-299 警/<100 败**(文章建议 500+,长文 1000+);Flesch-Kincaid **60-70** 最优;关键词堆砌=warn/fail;标题层级不跳(H1→H3=invalid);**标题 <3 字符或 >100 字符=警**;页内标题重复=warn;text/HTML 比=warn;title 与 H1 相同=warn;**title 像素宽 ≤~580px、description ≤~920px**(SERP 截断);title=description 全同=warn;meta 在 body 里=fail;MIME=warn/fail;**crawl 专属**:duplicate-description/duplicate-exact(=fail)/duplicate-near/duplicate-h1(跨页同 H1)/thin-vs-site(**<同类页中位词数一半=警**,需 ≥4 个同类页)/title-pattern(标题未带全站 ≥60% 使用的后缀=警);`content-mojibake`(UTF-8 被按 Latin-1/Windows-1252 解码,如 `â€™`=fail);`content-unrendered-markup`(code/pre 外的字面 Markdown `**bold**`=warn);`content-placeholder-text`(**`{{ }}`/`{% %}`/`<% %>`/`[object Object]`=fail;TODO:/FIXME:=warn**;`content-stale-copyright`(页脚版权年落后当年=warn,区间取末年);`content-date-agreement`(datePublished/time datetime//20xx/ 路径三年份不一致=warn,dateModified 不比);`content-hidden-text`(**≥80 字符**被内联样式隐藏(display:none/visibility:hidden/font-size:0/大负 text-indent/opacity:0)=warn,nav/对话框/sr-only 豁免,仅样式表隐藏不判);`content-broken-html`/`content-meta-in-body`。

**解释层(15 条;ID 未公布原文,标 [待核])**

#### content-duplicate-exact [待核 ID]
- 名称/类型: 完全重复内容 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;crawl 模式)
**这意味(what)**: 站内另一个页面的主内容与该 URL 完全相同。
**为什么(why)**: 完全重复是最强的"坏信号":引擎被迫二选一(或自选),版本不可控、外链信号分裂;批量完全重复(打印版/参数变体/采集)会同时触发去重与质量算法的审视——**几页近似重复可能无实质影响,数千页完全重复是算法层面的模板质量问题**,故它是唯一判 fail 的内容重复档。
**触发(trigger)**: 1) crawl 全站主内容规范化后取指纹;2) 相同指纹归组;3) 组内 >1 即 fail。
**不修的条件(caveat)**: 联合发布/合法转载的完全重复,用 canonical 让渡权益即可化解;分页变体走分页规则,不在此列。
**修复(fix)**: 真重复→canonical/301 合并;打印版→加 canonical 或 noindex;采集页→重写或下线。
**导出(export)**: Reports > Content > Exact Duplicates
**关联(seealso)**: core-canonical-conflicting、content-duplicate-near;[scoring-rubric.md](scoring-rubric.md)

#### content-duplicate-near [待核 ID]
- 名称/类型: 近似重复内容 —— warning · 优先级 medium · 输出 WARN(源表 warn;crawl 模式)
**这意味(what)**: 站内页面主内容与该 URL 高度相似但不完全相同。
**为什么(why)**: 近似重复(同城不同区的服务页模板)是质量算法(薄内容/重复内容)的典型标的;但引擎有成熟的聚类去重,少量近似不致命——所以 warn 不 fail。源目录未公布相似度算法与阈值[待核:常见实现为 Simhash/余弦相似度 ≥0.9 量级,borrow-specs A1 的 0.9 口径可参考]。
**触发(trigger)**: 1) 全站内容相似度聚类;2) 组内 >1 即 warn。
**不修的条件(caveat)**: 地域页/参数页的适度模板化是行业常态,引擎也理解;"复制全文只换城市名"级别的零增量模板才是要修的。
**修复(fix)**: 增量本地化(本地数据/案例/评价);或合并为强页+canonical;程序化页面过 [programmatic-seo-gates.md](programmatic-seo-gates.md) 的门槛。
**导出(export)**: Reports > Content > Near Duplicates
**关联(seealso)**: content-duplicate-exact;[programmatic-seo-gates.md](programmatic-seo-gates.md)

#### content-duplicate-description [待核 ID]
- 名称/类型: 重复 description —— warning · 优先级 low · 输出 WARN(源表 warn;crawl 模式)
**这意味(what)**: 站内多页共用同一条 meta description。
**为什么(why)**: 重复 description 让 SERP 摘要失去区分度,引擎倾向改用页面文本抓摘要——可控性下降;但 description 本身非排名因素,故 low。
**触发(trigger)**: crawl 全站 description 集归组;组内 >1 即 warn。
**不修的条件(caveat)**: 规模论同 title:**几页重复可能无实质影响,数千页模板级重复才值得治理**;优先修有流量的页。
**修复(fix)**: 模板用真实字段变量拼装;无字段的页宁可删空 description 让引擎自抓,也别留假重复。
**导出(export)**: Reports > Content > Duplicate Descriptions
**关联(seealso)**: core-title-unique、core-description

#### content-duplicate-h1 [待核 ID]
- 名称/类型: 跨页重复 H1 —— warning · 优先级 low · 输出 WARN(源表 warn;crawl 模式)
**这意味(what)**: 站内多页共用同一 H1 文本。
**为什么(why)**: H1 重复=主题声明的重复,常与 title 重复、近似内容同现,是模板失控的症状指标;单独看影响弱(warn/low)。
**触发(trigger)**: crawl 全站 H1 集归组;组内 >1 即 warn。
**不修的条件(caveat)**: 分页序列共享 H1 属预期;先查同组页面是否本该合并,再改文案。
**修复(fix)**: H1 携带页面级变量;重复页合并。
**导出(export)**: Reports > Content > Duplicate H1
**关联(seealso)**: core-h1、content-duplicate-exact

#### content-word-count [待核 ID]
- 名称/类型: 词数 —— warning · 优先级 low · 输出 WARN(100-299)/CRITICAL(<100)(源表:≥300 过/100-299 警/<100 败;文章建议 500+,长文 1000+)
**这意味(what)**: 页面主内容词数不足:100-299 词 warn,<100 词 fail 档(文章类建议 500+、长文 1000+ 为参考线不扣分[待核])。
**为什么(why)**: 词数不是排名因素,是"页面有没有内容"的粗代理:<100 词几乎必然是空壳/占位/极薄页,才配 fail 档。质量口径见 [scoring-rubric.md](scoring-rubric.md) "不作为扣分依据"——**不要机械灌字数到 300**。
**触发(trigger)**: 主内容区(剥导航/页脚/广告)文本词数:<100 → fail 档;100-299 → warn;≥300 过。
**不修的条件(caveat)**: 词数不(直接)影响 SEO,然而它是薄内容检测的第一道症状指标,所以一般建议主内容 ≥300 词。但联系页/工具页/表单页天然短,按页面类型豁免。
**修复(fix)**: 薄页补实质内容(回答/示例/数据)或并入父页;程序化薄页过 [programmatic-seo-gates.md](programmatic-seo-gates.md) 门槛;别注水。
**导出(export)**: Reports > Content > Word Count
**关联(seealso)**: content-keyword-stuffing、content-duplicate-near;[scoring-rubric.md](scoring-rubric.md)

#### content-keyword-stuffing [待核 ID]
- 名称/类型: 关键词堆砌 —— issue · 优先级 high · 输出 CRITICAL/WARN 分型(源表 warn/fail;分型阈值源表未公布[待核])
**这意味(what)**: 页面文本/alt/meta 里同一关键词的密度与重复超出自然语言频率。
**为什么(why)**: 堆砌是最老的操纵手法,现代引擎将其归入质量层负信号;现代形态不再是裸重复,而是同义词轰炸与标签云式罗列。判 warn 还是 fail 按程度分型(阈值未公布)。
**触发(trigger)**: 主文本关键词密度+n-gram 不自然重复检测(密度阈值[待核]);meta/alt 内同词根堆叠另计。
**不修的条件(caveat)**: 没有公认的安全密度魔法数,机器判堆砌误报不低,所以一般建议命中后人工复查再动文案。但主题集中的专题页关键词命中率高是自然结果,别一见重复就删。
**修复(fix)**: 用同义词/实体变体分散表达;每段回答一个问题;alt/title 里的堆叠优先清。
**导出(export)**: Reports > Content > Keyword Stuffing
**关联(seealso)**: content-hidden-text、content-word-count;[scoring-rubric.md](scoring-rubric.md)

#### content-heading-family [待核 ID]
- 名称/类型: 标题结构家族 —— warning · 优先级 low · 输出 WARN(源表:层级跳级 H1→H3=invalid;标题 <3 字符或 >100 字符=警;页内标题重复=warn)
**这意味(what)**: 页内标题树有问题:层级跳级(H1 直接 H3)、标题过短(<3 字符)或过长(>100 字符)、同页重复标题文本。
**为什么(why)**: 标题树是引擎与屏幕阅读器共用的内容骨架:跳级让语义树断裂(SR 按级别导航会迷路),过长标题是段落伪装,页内重复让章节失去区分度。单项影响都轻,合并看是内容结构质量分。
**触发(trigger)**: 1) 相邻标题级别差 >1 即 invalid;2) 标题文本 <3 或 >100 字符即警;3) 同页两标题文本相同即 warn。
**不修的条件(caveat)**: 标题结构不(直接)影响排名,然而影响无障碍与 AI 摘要的章节切分,所以一般建议树形规范。但设计系统组件自带级别(卡片 H3 出现在 H1 区)造成的"跳级"是工程取舍,可按组件规则豁免。
**修复(fix)**: 模板按语义排 H1→H2→H3;标题写"这节说什么";组件标题级别参数化。
**导出(export)**: Reports > Content > Heading Structure
**关联(seealso)**: core-h1、content-agreement;[semantic-html.md](semantic-html.md)

#### content-agreement [待核 ID]
- 名称/类型: 元素一致性家族 —— warning · 优先级 low · 输出 WARN(源表:title 与 H1 相同=warn;title=description 全同=warn;content-date-agreement 三年份不一致=warn,dateModified 不比)
**这意味(what)**: 本该各司其职的信号互相雷同或矛盾:title 与 H1 完全相同;title 与 description 全同;页面三处年份(datePublished/`<time>` datetime/路径 /20xx/)互不一致。
**为什么(why)**: title 是 SERP 行、H1 是页内主题、description 是摘要候选——雷同等于放弃两层独立表达;年份不一致则对引擎发出矛盾的新鲜度信号。dateModified 不参与比对(更新时间晚于发布是常态)。均为轻档:单页雷同无实质影响,批量模板雷同才是病。
**触发(trigger)**: 1) 归一化后 title==H1 即 warn;2) title==description 即 warn;3) 三处年份取值 ≥2 个不同即 warn。
**不修的条件(caveat)**: 一致性家族不影响排名,然而各自放弃一层表达面,所以一般建议差异化:title 带品牌与意图、H1 是主题、description 是行动点。但品牌极简页(title=H1=品牌名)可豁免。
**修复(fix)**: 三字段分模板变量;日期单一来源(CMS updated_at)注入全部位置;像素口径(title ≤~580px/description ≤~920px)见本节表。
**导出(export)**: Reports > Content > Meta Content Agreement
**关联(seealso)**: core-title、core-h1、content-heading-family;[head-elements.md](head-elements.md)

#### content-hidden-text [待核 ID]
- 名称/类型: 隐藏文本 —— issue · 优先级 high · 输出 WARN(源表 warn;≥80 字符被内联样式隐藏)
**这意味(what)**: ≥80 字符的文本被**内联样式**隐藏(display:none/visibility:hidden/font-size:0/大负 text-indent/opacity:0)。
**为什么(why)**: 隐藏文本是 cloaking 的经典残余——给引擎看、不给用户看;单独出现很少直接惩罚(合法用例太多),但与关键词堆叠同现时是手动操作的典型标的。源表三个精准边界:只判内联样式(样式表隐藏可能是响应式规则,不判);≥80 字符(短文本隐藏多为 UI 状态);nav/对话框/sr-only 豁免(sr-only 是无障碍正确做法)。
**触发(trigger)**: 1) 元素内联样式含隐藏属性;2) 文本 ≥80 字符;3) 非豁免区即 warn。
**不修的条件(caveat)**: 隐藏本身不是罪(SR-only 文本、折叠 UI 都正当),然而"隐藏+长文本+关键词"的组合接近操纵形态,所以一般建议命中后人工判意图。但 A/B 测试的隐藏变体属实验基建,标注豁免。
**修复(fix)**: 该给用户看的就显示;折叠交互用 details/dialog 语义元素;sr-only 保留(豁免)。
**导出(export)**: Reports > Content > Hidden Text
**关联(seealso)**: content-keyword-stuffing;[semantic-html.md](semantic-html.md)

#### content-deploy-hygiene [待核 ID]
- 名称/类型: 部署卫生家族 —— issue · 优先级 high · 输出 CRITICAL/WARN(源表:占位符 {{ }}/{% %}/<% %>/[object Object]=fail,TODO:/FIXME:=warn;mojibake=fail;code/pre 外字面 Markdown=warn;页脚版权年落后=warn,区间取末年)
**这意味(what)**: 渲染管道事故漏进生产:未渲染占位符(fail 档)、TODO:/FIXME: 残留(warn)、乱码 mojibake——UTF-8 被按 Latin-1/Windows-1252 解码,如 `â€™`(fail 档)、code/pre 外的字面 Markdown `**bold**`(warn)、页脚版权年落后当年(warn,年份区间取末年)。
**为什么(why)**: 每项都是"管道坏了"的直接证据:占位符=模板引擎没跑或变量没注入;乱码=编码声明与实际字节不符;字面 Markdown=静态生成器漏处理。对用户是可见破损(信任度),对引擎是无意义文本;fail 档两项意味着页面实质坏死。
**触发(trigger)**: 正则扫主内容:占位符模式 → fail 档;TODO:/FIXME: → warn;mojibake 特征序列(â€™/Ã© 族)→ fail;code/pre 外 `**…**`/行首 # → warn;版权年 < 当年 → warn。
**不修的条件(caveat)**: 家族命中基本无豁免(生产页不该有模板残渣);唯一注意是展示模板语法的教程/文档页命中属误报,按白名单排除。
**修复(fix)**: CI 加渲染产物断言(无占位符/无 mojibake);charset 声明与实际编码统一为 UTF-8;版权年由服务器时间动态输出。
**导出(export)**: Reports > Content > Deployment Hygiene
**关联(seealso)**: content-word-count、sd-json-syntax(同为"静默失效"家族);[validation-guide.md](validation-guide.md)

#### content-text-html-ratio [待核 ID]
- 名称/类型: 文本/HTML 比 —— warning · 优先级 low · 输出 WARN(源表 warn;阈值源表未公布[待核])
**这意味(what)**: 页面可见文本量与 HTML 标记量的比值过低。
**为什么(why)**: 低比值是"标记-heavy"的粗代理:内联样式/深层嵌套容器/隐藏 DOM 把标记撑大,正文被稀释——引擎要剥壳取肉,移动端要为壳付流量。它从来不是排名因素,是内容密度的症状指标;真正的病(多余嵌套/内联属性)由它暴露。
**触发(trigger)**: 渲染后可见文本字符数 ÷ HTML 总字符数,低于阈值即 warn(具体比值[待核:源表未公布])。
**不修的条件(caveat)**: 比值不(直接)影响 SEO(代码展示页文本密集、应用页标记密集,天然波动),然而它是标记债的症状,所以一般建议命中后查嵌套与内联属性而非灌字。但 SPA 壳页低比值是形态属性,配 SSR 后再看。
**修复(fix)**: 内联样式剥离到样式表;组件嵌套扁平化;隐藏 DOM 按需挂载;SSR 输出真实内容。
**导出(export)**: Reports > Content > Text-to-HTML Ratio
**关联(seealso)**: perf-dom-size、content-word-count;[scoring-rubric.md](scoring-rubric.md)

#### content-readability [待核 ID]
- 名称/类型: 可读性 —— warning · 优先级 low · 输出 WARN(源表 warn;Flesch-Kincaid **60-70** 最优)
**这意味(what)**: 正文可读性得分偏离 60-70 建议区(Flesch-Kincaid 口径)。
**为什么(why)**: 60-70 对应 plain English 级:多数目标读者能顺读;分数过低(句长/词复杂)时读完率与停留下降,间接伤页面表现;过高则可能内容过于浅白、深度不足。中文场景 Flesch 公式不直接适用,按句长与常用字率近似[待核],得分作同类页横向对比而非绝对标尺。
**触发(trigger)**: 主内容文本计算 Flesch-Kincaid 读易分;<60 或 >70 即 warn(中文近似的口径[待核])。
**不修的条件(caveat)**: 可读性不是排名因素,然而它影响真实阅读完成率,所以一般建议向 60-70 靠拢。但学术/法律/技术文档天然低分是受众属性,别为得分把术语稀释成水文。
**修复(fix)**: 长句拆短(一句一个意思);术语首次出现给解释;段落 ≤4 行;中英混排统一标点口径。
**导出(export)**: Reports > Content > Readability
**关联(seealso)**: content-word-count、content-heading-family;[scoring-rubric.md](scoring-rubric.md)

#### content-thin-vs-site [待核 ID]
- 名称/类型: 相对站内同类过薄 —— warning · 优先级 medium · 输出 WARN(源表 warn;crawl 模式;**<同类页中位词数一半=警,需 ≥4 个同类页**)
**这意味(what)**: crawl 全站后,该页词数不足同模板/同类页面中位数的一半(同类页 ≥4 个才可判)。
**为什么(why)**: 绝对词数阈值(content-word-count)对工具页/长文页一刀切失真;相对口径按同类校准——同是产品详情页,别家中位 800 词你 200 词,薄就是同维度可比的薄。≥4 个同类页的门槛保证中位数有统计意义,不足则不判(缺数据不等于缺内容)。
**触发(trigger)**: 1) 按模板/类型聚合同类页;2) 组内 ≥4 页才启用;3) 页词数 < 组中位数 ÷2 即 warn。
**不修的条件(caveat)**: 相对薄不(直接)影响排名(词数不是排名因素),然而同模板下显著偏薄多为空字段/抓取失败/未完成页,所以一般建议补实质内容。但新品待充实、UGC 早期短评是真实生命周期状态,排期充实而非硬灌字。
**修复(fix)**: 查模板空字段(无描述的产品页);补齐结构化内容模块;确实无话可说的页并入父级或 410。
**导出(export)**: Reports > Content > Thin vs Site Median
**关联(seealso)**: content-word-count、content-duplicate-near;[programmatic-seo-gates.md](programmatic-seo-gates.md)

#### content-title-pattern [待核 ID]
- 名称/类型: 标题模式偏离 —— warning · 优先级 low · 输出 WARN(源表 warn;crawl 模式;标题未带全站 ≥60% 使用的后缀=警)
**这意味(what)**: crawl 全站后,该页 title 不带全站 ≥60% 页面都在用的标题后缀(品牌后缀/站名)。
**为什么(why)**: 品牌后缀一致性是模板健康与品牌 SERP 露出的双信号:多数页"| Brand"而个别页裸标题,几乎总是模板分支漏拼——SERP 里品牌词忽有忽无,同一站在结果页的视觉一致性碎掉。60% 是"主流模式"判定线:达到它,偏离者才算异常。
**触发(trigger)**: 1) 全站 title 提取公共后缀(分词对齐);2) 某后缀覆盖率 ≥60%;3) 不带该后缀的页即 warn。
**不修的条件(caveat)**: 后缀缺失不(直接)影响排名(title 长度哲学同 core-title),然而它是模板分支失控的症状,所以一般建议统一。但刻意区分的落地页组(广告着陆页不带品牌测 CTR)是实验设计,标注豁免。
**修复(fix)**: title 模板统一 `主题 | 品牌` 单一出口;超长页可程序化裁后缀保主题(像素口径见 content-agreement);实验页白名单。
**导出(export)**: Reports > Content > Title Pattern Deviation
**关联(seealso)**: core-title、content-agreement、core-title-unique;[scoring-rubric.md](scoring-rubric.md)

#### content-mime-broken [待核 ID]
- 名称/类型: MIME 与文档破损家族 —— issue/warning · 优先级 high(fail 档)/medium · 输出 CRITICAL/WARN(源表:MIME=warn/fail;meta 在 body 里=fail;content-broken-html)
**这意味(what)**: 文档级破损三型:页面 MIME 声明与实际不符(warn/fail 分型[待核]);meta 标签出现在 body 里(fail);HTML 结构破损(关键标签未闭合/非法嵌套)。
**为什么(why)**: MIME 错让引擎选错解析器(technical-content-type 的内容侧镜像);meta 出现在 body 时解析器容错重组,description/robots/canonical 可能全部失位——与 core-canonical-outside-head 同构的"声明不在有效位置"家族;结构性破损让 DOM 树与源码意图错位,内容提取随之漂移。三型叠加是"同一页面在不同工具里长得不一样"的根因。
**触发(trigger)**: 1) 响应 Content-Type 与文档实际形态(HTML/XML/文本)不符即 warn/fail;2) meta robots/description/charset 出现在 body 区即 fail;3) 关键标签未闭合/非法嵌套造成解析器重组即破损档。
**不修的条件(caveat)**: 破损判定依赖解析器口径,容错重组后多数用户无感,然而引擎提取的内容树已偏,所以一般建议 CI 过 HTML 校验器。但第三方组件注入的合法容错结构(微前端壳/遗留嵌入)命中属误报面,白名单处理。
**修复(fix)**: 模板过 W3C 类校验器零 error 再发;meta 全部收敛 head 单一出口;MIME 与内容对齐(见 technical-content-type);组件注入走规范插槽。
**导出(export)**: Reports > Content > MIME & Broken HTML
**关联(seealso)**: technical-content-type、htmlval-document-structure、core-canonical-outside-head;[semantic-html.md](semantic-html.md)

### JavaScript Rendering(16 条,权重 5%)

**raw-vs-rendered 实现要点已吸收于 [rendering-seo.md](rendering-seo.md) 与 [validation-guide.md](validation-guide.md)**(HTTP 抓原始→$;Playwright 二抓→rendered$;web-vitals 库 goto 前注入;INP 合成标记 inpSynthetic 不计分)。规则粒度:title/description/H1/canonical 不在初始 HTML=fail/warn/warn/fail;canonical 或 noindex 在源码与渲染 DOM 间不一致=fail;JS 事后改写 title/description/H1=warn;主内容/内链依赖 JS=warn;JS/CSS 被 robots 挡=warn;SSR 检查=warn/fail;**console 未捕获异常与错误=warn/fail**;**子资源加载失败=warn/fail**;内联脚本用 `document.write()`=warn。

**解释层(4 条;ID 未公布原文的按家族命名法推得并标 [待核];双抓实现见 [rendering-seo.md](rendering-seo.md))**

#### js-initial-html [待核 ID]
- 名称/类型: 关键注解不在初始 HTML —— issue · 优先级 critical · 输出 CRITICAL(title/canonical,源表 fail)/WARN(description/H1,源表 warn);SSR 检查=warn/fail(分型口径[待核])
**这意味(what)**: title/canonical 等关键注解不在服务端返回的初始 HTML,要等 JS 渲染才出现(源表分型:title 缺=fail、canonical 缺=fail、description=warn、H1=warn);SSR/SSG 检查同源。
**为什么(why)**: 初始 HTML 是所有抓取方的公共层:多数 AI 爬虫不执行 JS、社交爬虫不执行、Google 渲染排队有小时到天级延迟——注解只在渲染后 DOM 里,等于对一半消费者不存在。
**触发(trigger)**: 1) HTTP 抓 raw HTML;2) 检查 title/description/H1/canonical 存在性;3) 缺失再查渲染 DOM——仅渲染后存在即按上列分型触发。
**不修的条件(caveat)**: Google 终会渲染并读取 JS 注解,然而渲染延迟与非 Google 消费者的缺失是实打实的,所以一般建议 head 注解全部服务端输出。但客户端路由切换时的注解更新另归 js-meta-drift,不属本条。
**修复(fix)**: 框架切 SSR/SSG 或预渲染;至少 head 层(title/canonical/og)服务端输出;验收标准=raw HTML 即含全部关键注解。
**导出(export)**: Reports > JavaScript > Missing in Initial HTML
**关联(seealso)**: js-meta-drift、js-content-dependency;[rendering-seo.md](rendering-seo.md)、[ai-crawler-policy.md](ai-crawler-policy.md)

#### js-meta-drift [待核 ID]
- 名称/类型: 注解在源码与渲染间漂移 —— issue · 优先级 high · 输出 CRITICAL(canonical/noindex 不一致,源表 fail)/WARN(JS 改写 title/description/H1,源表 warn)
**这意味(what)**: 同一页的 canonical 或 noindex 在 raw HTML 与渲染 DOM 间不一致(如源码 noindex、渲染后被删),或 JS 事后改写 title/description/H1。
**为什么(why)**: 引擎两阶段抓取(先 raw 后渲染)各记一次注解,不一致时以哪次为准不可控——canonical/noindex 漂移意味着索引决策分裂,故 fail;title 类改写最终值仍会被读到,影响小一档 warn。典型肇因:客户端路由器接管 head 但没与 SSR 输出对齐。
**触发(trigger)**: 双抓对比:1) canonical/noindex raw ≠ rendered 即 fail;2) title/description/H1 文本被 JS 改写即 warn。
**不修的条件(caveat)**: 修漂移不改变最终渲染值,然而它消除两阶段解读分裂,所以一般建议注解只写一次且客户端不改。但单页应用路由切换时更新 og 标签属合法客户端更新——本条只看首屏注解的稳定性。
**修复(fix)**: head 管理收敛到框架 head 组件一处;禁 JS 改写 canonical/noindex;A/B 测试不落在 head 层。
**导出(export)**: Reports > JavaScript > Meta Drift (Raw vs Rendered)
**关联(seealso)**: js-initial-html;[rendering-seo.md](rendering-seo.md)、[head-elements.md](head-elements.md)

#### js-content-dependency [待核 ID]
- 名称/类型: 主内容/内链依赖 JS —— warning · 优先级 high · 输出 WARN(源表 warn)
**这意味(what)**: 页面主内容或内链只存在于渲染后 DOM,raw HTML 里没有。
**为什么(why)**: 与 js-initial-html 同因不同层:注解缺失伤元数据,主内容缺失伤实体——AI 引用与社交摘要都取 raw 层,内容不在就等于对它们不存在;内链不在则按 raw 层计算的链接图(发现/权重)漏掉它们(Google 渲染后会计入,多数 AI/社交爬虫不渲染)。JS/CSS 再被 robots 挡住时问题翻倍(见 crawl-blocked-resources)。
**触发(trigger)**: 1) raw HTML 主内容区为空壳(仅挂载点)即 warn;2) raw 内链数远小于渲染后内链数(比例阈值源表未公布[待核])即 warn。
**不修的条件(caveat)**: Google 渲染能力成熟,纯 Google 视野下 JS 内容可索引,然而渲染预算与延迟真实存在、AI/社交侧多不渲染,所以一般建议主内容与核心内链服务端输出。但交互后的次级内容(评论区/展开区)客户端加载是正当形态。
**修复(fix)**: 主内容 SSR;首屏内链进模板;评论区等增强层保留客户端。
**导出(export)**: Reports > JavaScript > Content Requires JS
**关联(seealso)**: js-initial-html、crawl-blocked-resources;[rendering-seo.md](rendering-seo.md)

#### js-runtime-hygiene [待核 ID]
- 名称/类型: 运行时卫生家族 —— issue/warning · 优先级 high(fail 分型)/medium · 输出 CRITICAL/WARN(源表:console 未捕获异常=warn/fail;子资源加载失败=warn/fail;document.write()=warn;分型口径未公布[待核])
**这意味(what)**: 渲染时 console 有未捕获异常/错误、子资源(脚本/样式/图)加载失败,或内联脚本用 document.write()。
**为什么(why)**: 未捕获异常常中断后续脚本——依赖它的注解注入/内容挂载全部静默失败,是"页面看起来正常但 SEO 层坏死"的头号原因;子资源 4xx/超时拖慢渲染且常是 CDN/版本漂移;document.write 阻塞解析,慢速网络下被 Chrome 直接干预弃用。
**触发(trigger)**: 渲染过程:1) console error/uncaught 非空按分型触发;2) 任一子资源网络失败按分型触发;3) 内联脚本调 document.write 即 warn。
**不修的条件(caveat)**: console 噪声本身不影响 SEO,然而它标记渲染链路断裂,所以一般建议零未捕获异常再上线。但第三方脚本(广告/统计)抛的错不在你掌控内,归类外部噪声跟踪,不必阻塞发布。
**修复(fix)**: 异常接错误监控;子资源 404 修路径/版本;document.write 全部换 DOM API 或异步注入。
**导出(export)**: Reports > JavaScript > Console Errors / Failed Subresources
**关联(seealso)**: js-initial-html;[rendering-seo.md](rendering-seo.md)

### Accessibility(36 条,权重 7%)

对比度 **≥4.5:1 正文/3:1 大字**;触控目标 **≥44×44 CSS px**(WCAG 2.5.8);交互元素须可访问名(aria-label/文本/title);focus 样式可见;表单 label(placeholder 不算);标题不跳级;landmark(main/nav/header/footer);描述性链接文本;skip-to-content 链接;表格 th+scope;视频字幕/文稿;viewport 禁缩放(user-scalable=no/maximum-scale=1)=fail;aria-hidden 包可聚焦元素=fail;**ARIA 角色/属性拼错浏览器静默丢弃(aria-lable→aria-label)=fail**;accesskey 唯一;**ID 重复致 aria-labelledby/label for 解析到第一个匹配=fail(svg 内 url(#id) 引用的 clipPath 豁免)**;空标题=fail;一控件一 label;同文本链接须同目的地;iframe/object 须 title/替代文本;`<input type=image>` 须 alt;**可访问名须含可见文本(语音用户"说所见")**;按钮有名;email/tel 输入配对 autocomplete token;lang 与 xml:lang 一致;html/body 禁 aria-hidden;ARIA widget 须有所需父子角色(tab 在 tablist 内/option 在 listbox 内);列表只含 li;**恰一个 main landmark**;role=none/presentation 不被 ARIA/可聚焦性反证;alt 不重复相邻链接/图注文本;img 角色 SVG 须可访问名;表格用 caption 不用跨列首行;**tabindex 禁正值**;元素级 lang 合法 BCP 47。

### Social(9 条,权重 3%)

og:title/description/image 各=warn;**og:image 推荐 1200×630(配 og:image:width/height meta)**;og:url=warn;**og:url 与 canonical 不一致=fail**;twitter:card(summary_large_image)=warn;分享按钮(**≥2 平台**)=warn;社交资料链接(**≥3 个**,入 Organization sameAs)=warn。

**解释层(4 条;ID 未公布原文,标 [待核])**

#### social-og-url-canonical [待核 ID]
- 名称/类型: og:url 与 canonical 不一致 —— issue · 优先级 high · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的 og:url 与 rel=canonical 指向不同的地址。
**为什么(why)**: og:url 是社交平台归并分享计数的规范声明;与 canonical 打架时,平台与搜索引擎对"本页权威 URL"的认定分裂——分享数据归并到 A、搜索信号归并到 B,两边都拿不齐。两套规范声明理应同值。
**触发(trigger)**: 1) 解析 og:url 与 rel=canonical;2) 归一化(绝对化/去 frag)比对;3) 不同即 fail。
```html
<!-- fail -->
<link rel="canonical" href="https://example.com/page">
<meta property="og:url" content="https://example.com/page?utm=social">
```
**不修的条件(caveat)**: 刻意分轨(社交专用落地页)罕见但存在;先确认不是"两个变量不同源注入"的模板错再谈豁免。
**修复(fix)**: og:url 直接复用 canonical 的同一模板变量输出,一改俱改。
**导出(export)**: Reports > Social > OG URL vs Canonical
**关联(seealso)**: core-canonical-conflicting;[head-elements.md](head-elements.md) OG 消费矩阵

#### social-og-basic [待核 ID]
- 名称/类型: og 标签家族缺失 —— warning · 优先级 low · 输出 WARN(源表各=warn;twitter:card 同构)
**这意味(what)**: 页面缺 og:title/og:description/og:image(og:url 缺失另计 warn,与 canonical 的冲突见 social-og-url-canonical);twitter:card 同构——缺=warn,推荐值 summary_large_image。
**为什么(why)**: og 标签是社交平台与主流聊天应用(WhatsApp/Slack/Discord)抓分享卡片的依据;缺了平台自行抓页面,卡片图文不可控——分享 CTR 的隐形漏斗。对搜索排名无影响,纯分享层缺信号,故 low。
**触发(trigger)**: 逐一断言 og:title/og:description/og:image/og:url 存在且非空;twitter:card 值应为 summary_large_image;任一缺失即 warn。本家族其余规则同构:字段不同、阈值同为存在性检查。
**不修的条件(caveat)**: og 标签不影响搜索排名,然而决定分享卡片完整度,所以一般建议核心模板页全配。但法律/结账流等不需要被分享的页面可豁免。
**修复(fix)**: 模板用与 title/description 同源变量输出 og:title/og:description;og:image 用固定比例专图(见 social-og-image-dimensions);twitter:card 配 summary_large_image。
**导出(export)**: Reports > Social > Missing OG Tags
**关联(seealso)**: social-og-url-canonical、social-og-image-dimensions;[head-elements.md](head-elements.md) OG 消费矩阵

#### social-og-image-dimensions [待核 ID]
- 名称/类型: og:image 尺寸 —— warning · 优先级 low · 输出 WARN(源表 warn;推荐 1200×630,配 og:image:width/height meta)
**这意味(what)**: og:image 分辨率明显偏离 1200×630(1.91:1),或未配 og:image:width/og:image:height meta。
**为什么(why)**: 各平台分享卡裁切比例不一,1.91:1 是最大公约数;尺寸离谱时平台裁掉关键内容或弃图。配 width/height meta 让平台免下整图即可算占位,加快卡片渲染。
**触发(trigger)**: 1) og:image 目标宽高比偏离 1.91:1(容差阈值源表未公布[待核]);2) 无 og:image:width/og:image:height 即 warn。
**不修的条件(caveat)**: 尺寸不影响 SEO,然而影响分享卡展示完整度,所以一般建议 1200×630 专图。但主投放平台明确(如以 X 的 1:1 为主)时可按主平台调优。
**修复(fix)**: 出 1200×630 专图;head 补 og:image:width/og:image:height;每页独立图,别全站一张。
**导出(export)**: Reports > Social > OG Image Dimensions
**关联(seealso)**: social-og-basic;[head-elements.md](head-elements.md)

#### social-engagement [待核 ID]
- 名称/类型: 分享按钮与社交资料链接 —— opportunity · 优先级 insight · 输出 WARN(源表 warn;分享按钮 ≥2 平台、社交资料链接 ≥3 个)
**这意味(what)**: 站点缺社交基建:分享按钮覆盖 <2 平台,或站内社交资料链接 <3 个。
**为什么(why)**: 分享按钮降低分发摩擦;资料链接的作用更大——它们是 Organization schema sameAs 的候补实体证据,帮引擎把站点与官方社交账号绑定为同一实体(见 [entity-signal-checklist.md](entity-signal-checklist.md))。典型缺信号/机会项,不构成错误。
**触发(trigger)**: 1) 分享按钮平台数 <2 即 warn;2) 页脚/联系页社交资料外链 <3 个即 warn(已入 sameAs 的链接计入)。
**不修的条件(caveat)**: 社交基建不影响排名,然而影响分发与实体确认,所以一般建议按受众补齐。但 B2B 内部系统/无社交属性的站点两项都可合理不修。
**修复(fix)**: 分享按钮接 2+ 主平台;页脚列官方资料并同步写入 Organization sameAs。
**导出(export)**: Reports > Social > Share Buttons / Social Profiles
**关联(seealso)**: sd-required-fields(Organization sameAs);[entity-signal-checklist.md](entity-signal-checklist.md)

### URL Structure(14 条,权重 3%)

slug 含描述关键词(数字 ID/?p=123 坏)=fail/warn;URL 停用词=warn;大写=warn;下划线=warn(连字符才是词分隔);双斜杠=warn;**%20 编码空格=fail**;非 ASCII=warn;**路径 ≤75 字符**=warn;重复路径段(/shoes/shoes/)=warn;**查询参数 3-5 个=warn、>5=fail**,同名参数重复或多个 `?`=畸形=warn;**URL 会话 ID=fail**;UTM/追踪参数=warn;站内搜索 URL 被索引=warn;HTTP/HTTPS 双可达=warn。

**解释层(5 条;ID 未公布原文的按家族命名法推得并标 [待核])**

#### url-slug-quality [待核 ID]
- 名称/类型: slug 质量 —— issue/warning · 优先级 high(数字 ID 形态)/low(停用词) · 输出 CRITICAL/WARN(源表:slug 含描述关键词,数字 ID/?p=123 坏=fail/warn 分型[口径待核];URL 停用词=warn)
**这意味(what)**: URL slug 不含描述性关键词:纯数字 ID 或 ?p=123 形态取内容(fail/warn 档),或 slug 塞满停用词(warn)。
**为什么(why)**: slug 是弱相关信号之一:外链 URL 展示、SERP 面包屑、引用复制里都会原样露出;?p=123 形态还与参数规范化纠缠。停用词只是稀释信息密度,故仅 warn。
**触发(trigger)**: 1) 路径段为纯数字/单字母 ID,或内容经查询串 ID 选取 → fail/warn 分型;2) slug 停用词(of/the/a/and 等)占比过高 → warn。
**不修的条件(caveat)**: 改 slug=改 URL=必须 301,老 URL 有外链与历史时改名收益常抵不过搬家风险,所以一般建议新页用好 slug、老页不为 SEO 单独改名。
**修复(fix)**: 新页 slug=主关键词短语(小写连字符);确需语义化的老 ID URL 用 301 迁移并同步更新内链与 sitemap。
**导出(export)**: Reports > URL Structure > Slug Quality
**关联(seealso)**: url-shape、url-length;[link-architecture-patterns.md](link-architecture-patterns.md)

#### url-shape [待核 ID]
- 名称/类型: URL 形态卫生家族 —— warning · 优先级 low · 输出 WARN/CRITICAL(源表:大写/下划线/双斜杠/非 ASCII/重复路径段/HTTP-HTTPS 双可达=warn;%20 编码空格=fail)
**这意味(what)**: URL 含形态瑕疵:大写字母、下划线分词、双斜杠、非 ASCII 字符、重复路径段(/shoes/shoes/)、HTTP 与 HTTPS 双可达不互跳(以上各 warn);最重的是 %20 编码空格(fail)。
**为什么(why)**: 形态决定"同一 URL 会有几种写法":大写混用制造大小写变体(部分服务器区分大小写);下划线不被当词分隔符;双斜杠/重复段制造规范化噪音;双协议可达是重复站点种子。%20 空格是硬伤——空格在 URL 中非法,编码形态在点击/引用/重写链条上最易断裂。
**触发(trigger)**: 逐项:含大写 → warn;含 _ → warn;含 // → warn;路径段重复 → warn;含非 ASCII → warn;http 与 https 版本均 200 不互跳 → warn;含 %20 → fail。
**不修的条件(caveat)**: 单项瑕疵不(直接)影响排名,然而每项都在增加变体重复的概率,所以一般建议全站 lint。但非 ASCII(中文/日文 slug)在相应语种市场是正当形态,warn 不等于要求转拼音。
**修复(fix)**: 新 URL 全小写+连字符;CMS 输出层统一规范化;老 URL 301 到规范形;http 单向 301 到 https。
**导出(export)**: Reports > URL Structure > URL Hygiene
**关联(seealso)**: url-slug-quality、crawl-canonical-form-drift;[redirects-canonical.md](redirects-canonical.md)

#### url-length [待核 ID]
- 名称/类型: URL 路径长度 —— warning · 优先级 low · 输出 WARN(源表 warn;路径 ≤75 字符)
**这意味(what)**: URL 路径部分超过 75 字符(不含协议与域名的口径[待核])。
**为什么(why)**: 长度本身不是排名因素,但超长路径几乎总意味着嵌套过深(点击距离超标,见 links-depth)、路径关键词堆砌、或筛选状态写进路径——这些才是问题,长度只是症状。75 字符也是 SERP 展示与外链复制的经验舒适线。
**触发(trigger)**: 解析 URL 取路径段;长度 >75 即 warn。
**不修的条件(caveat)**: URL 长度不(直接)影响 SEO,然而它是结构与堆砌的症状指标,所以一般建议控制。但多级分类的文档站(v2/api/auth/methods)超线是结构真实,不是错误。
**修复(fix)**: 压层级(去掉冗余中间层)、砍路径关键词堆砌;筛选状态移到参数并由规范化收口。
**导出(export)**: Reports > URL Structure > URL Length
**关联(seealso)**: links-depth、url-slug-quality;[link-architecture-patterns.md](link-architecture-patterns.md)

#### url-query-params [待核 ID]
- 名称/类型: 查询参数家族 —— issue/warning · 优先级 high(会话 ID=fail)/medium(计数与追踪) · 输出 CRITICAL/WARN(源表:参数 3-5 个=warn、>5=fail;同名参数重复或多个 ?=畸形 warn;URL 会话 ID=fail;UTM/追踪参数=warn)
**这意味(what)**: 查询串失控:参数 3-5 个 warn、>5 个 fail;同名参数重复/多个 ? 畸形 warn;URL 带会话 ID(PHPSESSID/jsessionid 形态)fail;站内链接带 UTM/追踪参数 warn。
**为什么(why)**: 参数爆炸是抓取预算头号杀手:每个参数组合都是潜在唯一 URL,爬虫在组合空间指数级发散,预算耗尽时真页面反而抓不到。会话 ID 更重:每访客一个 URL=无限重复页,是 2000 年代就被定性的反模式。UTM 入内链则是把追踪污染引进自己站内。
**触发(trigger)**: 解析查询串:参数计数 3-5 → warn、>5 → fail;同名键 ≥2 次或 ≥2 个 ? → warn;参数名匹配会话 ID 模式 → fail;内链 href 含 utm_/gclid 等追踪参数 → warn。
**不修的条件(caveat)**: 参数本身不(直接)影响排名,然而参数空间决定抓取预算的消耗方式,所以一般建议站内链接零追踪参数、筛选参数规范化收口。但合法功能参数(分页 ?page=、排序 ?sort=)不可删——要的是规范化,不是消灭。
**修复(fix)**: 内链剥 UTM(仅保留外链入口);筛选参数 canonical 收口或 robots.txt 屏蔽;会话状态改 cookie 承载;参数计数超标先审功能设计。
**导出(export)**: Reports > URL Structure > Query Parameters
**关联(seealso)**: crawl-sitemap-non-canonical、url-search-indexed;[robots-txt-reference.md](robots-txt-reference.md)

#### url-search-indexed [待核 ID]
- 名称/类型: 站内搜索结果被索引 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 站内搜索结果页(?s=/q=/search= 形态,键名口径[待核])可被索引——无 noindex、甚至进了 sitemap/内链。
**为什么(why)**: 搜索结果页是"关于查询的链接列表",无独立内容价值:引擎明确不喜欢索引一层"搜索结果套搜索结果"(用户从搜索引擎点进你的搜索页,看到的还是一堆链接);无限查询组合也是抓取预算黑洞。
**触发(trigger)**: 1) URL 匹配站内搜索参数形态;2) 页面可索引(无 noindex、被内链/sitemap 引用)即 warn。
**不修的条件(caveat)**: 搜索页索引不(直接)拖累其他页面排名,然而批量索引会稀释抓取预算,所以一般建议模板级 noindex。但确有搜索流量价值的长尾工具站,可把高价值查询做成内容化落地页保留索引——先看 GSC 流量再一刀切。
**修复(fix)**: 搜索结果模板加 noindex(整模板而非逐页);从 sitemap 与内链清除搜索 URL;站内搜索入口改 POST 或前端路由,不生成可爬 URL。
**导出(export)**: Reports > URL Structure > Indexed Search Results
**关联(seealso)**: sd-searchaction、url-query-params;[robots-txt-reference.md](robots-txt-reference.md)

### Redirects(11 条,权重 3%)

meta refresh=warn;JS 重定向=warn;HTTP Refresh 头=warn;环=fail;301(永久/传权重)vs 302(临时)用错=warn;目标 4xx/5xx=fail;**静态资源被重定向=warn**;大小写规范化重定向=warn;**渲染专属三条**:resource-broken(资源重定向终点 4xx/5xx=fail)/resource-loop(资源重定向环,浏览器 ERR_TOO_MANY_REDIRECTS=fail)/**resource-chain(资源 ≥2 跳=warn,单跳 http→https/尾斜杠视为良性)**。

**解释层(7 条;ID 未公布原文,标 [待核];JS/HTTP Refresh 头两条并入 meta-refresh 条目陈述)**

#### redirects-loop [待核 ID]
- 名称/类型: 重定向环 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 的重定向链绕回已访问 URL,不存在终点。
**为什么(why)**: 环让浏览器报 ERR_TOO_MANY_REDIRECTS、爬虫放弃——该 URL 形态对所有人完全不可达;常由多条 301 规则互相触发(强制 https+强制 www+尾斜杠规范化三者打架)。
**触发(trigger)**: 1) 跟踪 Location 链;2) 回到任一途经 URL 即 fail。
**不修的条件(caveat)**: 无豁免;这是运维事故级问题,立即修。
**修复(fix)**: 排查服务器层规则叠加顺序;统一终态(https+单一 host+固定尾斜杠)一步到位,别让三条规则接力。
**导出(export)**: Reports > Redirects > Redirect Loops
**关联(seealso)**: crawl-canonical-loop、links-redirect-chain;[redirects-canonical.md](redirects-canonical.md)

#### redirects-to-broken [待核 ID]
- 名称/类型: 重定向目标 4xx/5xx —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: 该 URL 重定向的最终目标是 4xx/5xx。
**为什么(why)**: 重定向的语义是"内容搬家了";终点 404 等于搬丢了——用户与引擎双输,旧 URL 的历史权重被导向死地址。这是迁移后"流量蒸发"的最常见原因。
**触发(trigger)**: 1) 跟踪重定向到链终点;2) 终点 4xx/5xx 即 fail。
**不修的条件(caveat)**: 无;对照迁移映射表逐行验证终态码是标准动作。
**修复(fix)**: 终点恢复内容,或改指最近亲存活页;批量修复后抽验全站终态。
**导出(export)**: Reports > Redirects > Redirect to Broken Target
**关联(seealso)**: links-internal-broken、crawl-sitemap-non-200;[http-status-codes.md](http-status-codes.md)

#### redirects-permanent-mismatch [待核 ID]
- 名称/类型: 301/302 用错 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 永久性变化用了 302 临时跳,或临时场景用了 301。
**为什么(why)**: 301 传权重且原 URL 退场、302 保留原 URL 待回归——用反了就是告诉引擎"别把信号搬过去"或"这页永久没了但其实会回来"。引擎会把长期稳定的 302 按 301 处理,但窗口期与不确定性由你承担。
**触发(trigger)**: 1) 判定变更性质(永久搬家 vs 临时);2) 与状态码(301/308 vs 302/307)比对;3) 不匹配即 warn。
**不修的条件(caveat)**: 302→301 引擎自纠概率高,不构成惩罚;临时活动页用 302 是**正确**的,别为心理安慰全站 301。
**修复(fix)**: 永久变更改 301/308;临时保持 302/307;HTTPS 强制跳用 301。
**导出(export)**: Reports > Redirects > Status Code Mismatch
**关联(seealso)**: redirects-loop;[redirects-canonical.md](redirects-canonical.md)

#### redirects-meta-refresh [待核 ID]
- 名称/类型: meta refresh/JS/HTTP Refresh 跳转 —— warning · 优先级 medium · 输出 WARN(源表 warn;同族三条:meta refresh/JS 重定向/HTTP Refresh 头)
**这意味(what)**: 该 URL 用 meta refresh(或 JS 跳转/HTTP Refresh 头)做重定向。
**为什么(why)**: meta refresh 是被滥用的古老跳转手法:引擎对 0 秒 refresh 近似按 301 处理、非 0 秒可能不跟,行为不受控;对用户是白屏闪烁与返回键破坏。HTTP 状态码重定向才是权威通道。
**触发(trigger)**: 1) `<meta http-equiv="refresh" content="0;url=…">` 存在;2) JS location 跳转;3) `Refresh:` 响应头;任一即 warn。
```html
<!-- fail -->
<meta http-equiv="refresh" content="0;url=https://example.com/new/">
```
**不修的条件(caveat)**: 延时刷新的内容轮播(5 秒切换幻灯)不是重定向语义,属误报,人工剔除;真正的跳转都应换成服务器层 301/302。
**修复(fix)**: 换服务器层 301/302;确需保留的引导页加 canonical 与 noindex 明确意图。
**导出(export)**: Reports > Redirects > Meta Refresh Redirect
**关联(seealso)**: redirects-permanent-mismatch;[redirects-canonical.md](redirects-canonical.md)

#### redirects-static-resource [待核 ID]
- 名称/类型: 静态资源被重定向 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 页面引用的静态资源(CSS/JS/图/字体)URL 自身返回 3xx,要再跳一次才拿到内容。
**为什么(why)**: 每条资源重定向都是渲染瀑布里多出的一跳:握手与请求白付两次,渲染阻塞资源(同步 CSS)的重定向直接串行拖慢 FCP/LCP;抓取侧同样双倍成本。典型来源:资源改版后旧 URL 301 保底、CDN 规则把 /assets/ 整体跳新路径、http 资源在 https 页被协议跳转。
**触发(trigger)**: 提取页面子资源 URL;任一返回 3xx 即 warn(终点 4xx/5xx 或成环另归 redirects-resource-chain 的 fail 档)。
**不修的条件(caveat)**: 单条资源重定向不影响排名,然而它在渲染关键路径上按毫秒计价,所以一般建议资源引用直指最终 URL。但迁移窗口期保留旧资源 URL 的 301 兜底是正当缓冲,发版后收直。
**修复(fix)**: 模板/构建产物里资源引用写最终 URL;http 资源引用改 https 直连;CDN 层把跳转规则改写为内部重写。
**导出(export)**: Reports > Redirects > Redirected Static Resources
**关联(seealso)**: redirects-resource-chain、perf-render-blocking;[redirects-canonical.md](redirects-canonical.md)

#### redirects-case-normalization [待核 ID]
- 名称/类型: 大小写规范化重定向 —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: URL 仅因大小写差异被重定向(/About → /about)——站点在用重定向兜 URL 大小写不一致。
**为什么(why)**: host 之后的路径大小写是否敏感取决于服务器/CDN,两种策略混用时唯一安全的收口是统一小写+301;但"每条内链先写成大写再靠 301 兜底"意味着每次点击都付一跳——这是把规范化成本从模板层转嫁到运行时。与 url-shape/technical-url-consistency 同源:根因是 URL 生成不规范。
**触发(trigger)**: 重定向的 source 与 target 仅大小写不同(其余成分一致)即 warn。
**不修的条件(caveat)**: 规范化重定向本身是正确收口(比双 200 好),然而它标记模板还在产大写 URL,所以一般建议源头改小写、301 只留兜底。但从大小写不敏感服务器迁到敏感服务器时,这批 301 是必要过渡,可长期保留。
**修复(fix)**: URL 生成层统一小写输出;内链/模板/sitemap 排查大写引用;301 规则保留作外链兜底。
**导出(export)**: Reports > Redirects > Case Normalization Redirects
**关联(seealso)**: technical-url-consistency、url-shape;[redirects-canonical.md](redirects-canonical.md)

#### redirects-resource-chain [待核 ID]
- 名称/类型: 资源重定向链家族(渲染专属三条) —— issue/warning · 优先级 high(fail 档)/medium · 输出 CRITICAL/WARN(源表:resource-broken 资源重定向终点 4xx/5xx=fail;resource-loop 资源重定向环,浏览器 ERR_TOO_MANY_REDIRECTS=fail;resource-chain 资源 ≥2 跳=warn,单跳 http→https/尾斜杠视为良性)
**这意味(what)**: 子资源重定向的三种深浅:链终点 4xx/5xx(资源实际丢失)、重定向成环(资源永不可得)、链长 ≥2 跳。
**为什么(why)**: 资源层与页面层(links-redirect-chain)同构但更苛:页面重定向用户还能多点一次,资源重定向直接决定渲染成败——CSS 链断则整页无样式,脚本链断则交互与注解注入全灭。单跳 http→https/尾斜杠被显式豁免为良性(规范化常态),≥2 跳才算链。
**触发(trigger)**: 渲染后逐资源跟踪 Location:1) 终点 4xx/5xx 即 fail;2) 回到途经任一 URL 即 fail;3) 跳数 ≥2 即 warn;4) 单跳且属 http→https/尾斜杠形态不报。
**不修的条件(caveat)**: 家族判定的是引用层的懒——资源本体搬家后引用没跟上,所以一般建议构建期校验全部资源 URL 直达 200。但第三方资源(外源字体/脚本)的重定向不在掌控内,先分类再处置:能换 URL 的换,不能换的评估自托管。
**修复(fix)**: 构建管道加资源 URL 终态断言(直达 200);版本化文件名+固定 CDN 路径消除跳转;外源资源锁定版本化 URL。
**导出(export)**: Reports > Redirects > Resource Redirect Chains
**关联(seealso)**: redirects-static-resource、js-runtime-hygiene、links-redirect-chain;[redirects-canonical.md](redirects-canonical.md)、[rendering-seo.md](rendering-seo.md)

### Mobile(12 条,权重 2%)

正文字号 **≥16px 过,<12px 败**(rem/em 优);横向滚动=warn/fail;插页弹窗(跳过 cookie/GDPR/年龄验证/登录)=warn/fail;viewport 须 device-width=warn;多 viewport 标签=fail;**parity 五条(`--mobile` 双渲染对比,我们覆盖薄)**:content/title+description/canonical=warn/fail,structured-data=fail(JSON-LD 桌面有移动无),links(内链数量可比)=warn;image maps(`<map>`/`<area>` 客户端图像地图,固定像素坐标不适配触屏)=warn;viewport content 规范(width 存在+initial-scale=1+**不设 minimum-scale**)=warn。

**解释层(6 条,第三批;ID 未公布原文的按家族命名法推得并标 [待核];移动优先索引与 m. 站背景见 [mobile-seo.md](mobile-seo.md) 第一节)**

#### mobile-font-size [待核 ID]
- 名称/类型: 正文字号 —— warning · 优先级 medium · 输出 WARN(中间档)/CRITICAL(<12px,源表败)(源表:≥16px 过,<12px 败;rem/em 优)
**这意味(what)**: 移动视口下正文主体字号低于 16px 建议值,<12px 进败档。
**为什么(why)**: 小字号在移动端直接降可读性(老年/弱视用户不可读),也是"视口没配对"的伴生症状——桌面排版塞进移动宽度时字号缩水。[mobile-seo.md](mobile-seo.md) 审计口径:表单 input 字号 <16px 会触发 iOS Safari 聚焦自动放大(强制缩放体验),审计必报。rem/em 单位让用户的浏览器字号设置能生效。
**触发(trigger)**: 渲染后计算正文主体(段落/列表)computed font-size:<12px → 败档;12-16px → 警;≥16px 过;input 字号 <16px 单列必报。
**不修的条件(caveat)**: 字号不(直接)影响排名,然而它影响移动可用性与移动优先索引下的页面评估,所以一般建议正文 ≥16px。但辅助信息(脚注/标签/法律小字)适度小一档是排版惯例,别一刀切拉平。
**修复(fix)**: 正文基准 16px(1rem)+行高 ≥1.4;input 全部 ≥16px 防 iOS 聚焦放大;对比度配套 ≥4.5:1。
**导出(export)**: Reports > Mobile > Font Size
**关联(seealso)**: mobile-viewport-config、mobile-overflow;[mobile-seo.md](mobile-seo.md)

#### mobile-viewport-config [待核 ID]
- 名称/类型: viewport 配置家族 —— issue/warning · 优先级 high · 输出 CRITICAL(多 viewport、禁缩放,源表 fail)/WARN(缺 device-width、content 规范,源表 warn)
**这意味(what)**: viewport meta 存在但配置错:缺 width=device-width、content 不规范(width 缺失/initial-scale≠1/设了 minimum-scale)、文档里多条 viewport、或用 user-scalable=no/maximum-scale=1 禁用缩放。
**为什么(why)**: 移动优先索引下 viewport 是渲染的控制面:缺 device-width 按桌面宽渲染再缩放,字号与点击目标全错;禁缩放拿走弱视用户的最后手段(捏合放大)——无障碍硬红线;多 viewport 时浏览器取舍不一,行为不可控。与 core-viewport(缺失=fail)分工:那条管"有没有",本条管"对不对"。
**触发(trigger)**: 1) viewport meta 计数 >1 即 fail;2) content 含 user-scalable=no 或 maximum-scale=1 即 fail;3) 无 width=device-width 即 warn;4) width 缺失/initial-scale≠1/含 minimum-scale 即 warn。
**不修的条件(caveat)**: viewport 配置影响渲染形态与可用性,不改变内容相关度,所以一般建议按规范值整站统一。但全屏交互(地图/画布)确需局部禁缩放时,只在该视图动态设置并给替代操作。
**修复(fix)**: 单条 `<meta name="viewport" content="width=device-width, initial-scale=1">`;删 user-scalable/maximum-scale/minimum-scale;刘海屏加 viewport-fit=cover。
**导出(export)**: Reports > Mobile > Viewport Configuration
**关联(seealso)**: core-viewport、mobile-font-size;[mobile-seo.md](mobile-seo.md)、[head-elements.md](head-elements.md)

#### mobile-overflow [待核 ID]
- 名称/类型: 横向滚动 —— issue/warning · 优先级 high · 输出 WARN/CRITICAL(源表 warn/fail;分型口径源表未公布[待核])
**这意味(what)**: 移动视口(常见 ~375px)下页面出现横向滚动——有元素超出视口宽度。
**为什么(why)**: 横向滚动是移动可用性的一票否决项:双轴滚动让用户极易迷失,"内容超出视口"长期是移动可用性评估的硬伤形态。常见肇因:固定宽度元素(表格/图/iframe 未 max-width)、绝对定位残片、长串不换行(裸 URL)。
**触发(trigger)**: 1) ~375px 视口渲染;2) scrollWidth > innerWidth 即触发;3) warn/fail 分型[待核:常见按超出幅度与是否整页双轴滚动分档]。
**不修的条件(caveat)**: 局部横向滚动区(轮播/代码块/宽表)是可用交互形态,本条针对整页级双轴滚动;命中后先定位溢出元素,别全局 overflow-x:hidden 掩盖——那只是把症状藏给用户。
**修复(fix)**: img/iframe/video 加 max-width:100%;宽表包横向滚动容器或改卡片式;fixed 宽度改响应式;pre/长 URL 强制换行。
**导出(export)**: Reports > Mobile > Horizontal Overflow
**关联(seealso)**: mobile-font-size、mobile-interstitial;[mobile-seo.md](mobile-seo.md)

#### mobile-interstitial [待核 ID]
- 名称/类型: 侵扰性插页 —— issue/warning · 优先级 high · 输出 WARN/CRITICAL(源表 warn/fail;官方三形态+豁免清单)
**这意味(what)**: 用户从搜索进入后立即遭遇遮蔽主内容的弹窗/独立插页页,或 cookie/GDPR/年龄验证/登录类横幅采用违规形态(全屏、难关闭、进入即弹)。
**为什么(why)**: Intrusive Interstitials 是 2017-01-10 生效的算法性排名调整(仅移动端,非手动动作)。官方三形态:进入即弹遮主内容的弹窗、须关闭才能看内容的独立插页页、首屏伪内容横幅。豁免清单:法律必需的 cookie/GDPR 横幅(合规形态:非全屏、易关)、登录墙(公开内容有免费替代)、占合理比例且可关的横幅——政策全拆解见 [mobile-seo.md](mobile-seo.md) 2.5 节。
**触发(trigger)**: 进入页面即检测遮罩(全屏 overlay/独立插页跳转);按"进入即弹/遮蔽比例/关闭难度"分型 warn/fail[分型口径源表未公布,待核]。
**不修的条件(caveat)**: 合规横幅不(必然)触发惩罚——判定看形态不看业务目的,所以一般建议 cookie/年龄类用非全屏、易关的形态。但"合规必需"不等于"任意形态免责",全屏 GDPR 墙同样在打击面内。
**修复(fix)**: 弹窗改用户交互后触发;横幅收紧为可关的顶部条;插页页移除;关闭目标(×)≥44px 触控目标。
**导出(export)**: Reports > Mobile > Intrusive Interstitials
**关联(seealso)**: mobile-overflow、legal-cookie-consent;[mobile-seo.md](mobile-seo.md)

#### mobile-image-maps [待核 ID]
- 名称/类型: 客户端图像地图 —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: 页面用 `<map>`/`<area>` 客户端图像地图做导航或交互——固定像素坐标的热区不适配。
**为什么(why)**: image map 的热区是绝对像素坐标:响应式图片缩放后热区不再对位(点 A 命中 B),触屏精度下小热区几乎不可点;屏幕阅读器对 area 的支持参差。这是 90 年代遗产技术,现代替代(CSS 定位/SVG 热区/拆分图片)全面更优。
**触发(trigger)**: 页面含 `<map>`+`<img usemap>` 即 warn(热区数量的分级口径[待核])。
**不修的条件(caveat)**: image map 不(直接)影响排名(引擎能提取 area href),然而触屏交互失准是可用性实伤,所以一般建议重构。但按渲染尺寸动态换算坐标的实现(热区随图等比缩放)可用,命中后先确认是否自适应。
**修复(fix)**: 导航型改列表/按钮组;图形热点改 SVG 内嵌 `<a>`(可缩放+可访问名);必须保留时热区坐标按渲染尺寸动态计算。
**导出(export)**: Reports > Mobile > Image Maps
**关联(seealso)**: mobile-overflow;[semantic-html.md](semantic-html.md)

#### mobile-parity [待核 ID]
- 名称/类型: 移动-桌面内容平价(parity 五条) —— issue/warning · 优先级 high · 输出 CRITICAL/WARN(源表:content/title+description/canonical=warn/fail,structured-data=fail(JSON-LD 桌面有移动无),links(内链数量可比)=warn;`--mobile` 双渲染对比)
**这意味(what)**: 同一 URL 的移动与桌面渲染(或 m. 站双域)内容不对等:主内容/标题描述/canonical 出入、桌面有移动无的 JSON-LD、内链数量不可比。
**为什么(why)**: 移动优先索引下引擎用移动版内容评级——桌面专属内容等于不存在;m. 站遗留时瘦移动版被索引,www 的优化投入落空。JSON-LD 桌面有移动无是最隐蔽的形态:富结果资格随移动版消失。parity 检查法(双视口抓取 diff、GSC 按设备拆分、Live Test)见 [mobile-seo.md](mobile-seo.md) 1.4 节:diff >20% 黄旗、>50% 红旗。
**触发(trigger)**: `--mobile` 双渲染(~375px 与 ~1280px)对比:1) 主内容文本量/title+description/canonical 不一致 → warn/fail[分型待核];2) 桌面 JSON-LD 移动缺失 → fail;3) 内链数量显著不可比 → warn。
**不修的条件(caveat)**: parity 差异不(必然)是错——大屏增强内容(桌面才显示的对比图)被移动省略是响应式常态,移动优先索引按移动版算,损失的是增强加分而非硬伤。但结构性差异(schema 缺失/内容整段缺失)必须修平。
**修复(fix)**: 结构化数据与关键注解两端同源输出;m. 站遗留按 [mobile-seo.md](mobile-seo.md) 1.3 风险清单收敛到响应式;双模板站点建 parity CI diff。
**导出(export)**: Reports > Mobile > Desktop vs Mobile Parity
**关联(seealso)**: js-content-dependency、js-meta-drift、mobile-viewport-config;[mobile-seo.md](mobile-seo.md)、[rendering-seo.md](rendering-seo.md)

### HTML Validation(11 条,权重 2%)

缺 DOCTYPE=warn;缺 charset(utf-8 须 head 首位)=warn;head 含非法元素=warn(白名单:meta/title/link/script/style/base/noscript);head 内 noscript=warn;多 head=fail;**HTML 体积 >250KB 警、>500KB 败、~2MB 以上 Googlebot 可能只索引前段**;lorem ipsum=warn;多 title=**fail**;多 description=**fail**;title 在 head 外=fail;base 元素(href 空/畸形/非 HTTP(S)=fail,多条=warn,须 ≤1 条)。

**解释层(5 条,第三批;ID 未公布原文的按家族命名法推得并标 [待核])**

#### htmlval-document-structure [待核 ID]
- 名称/类型: 文档结构家族 —— issue/warning · 优先级 medium · 输出 CRITICAL(多 head,源表 fail)/WARN(缺 DOCTYPE、charset 位置,源表 warn)
**这意味(what)**: 文档骨架错:没有 DOCTYPE、charset 声明不在 head 首位(utf-8 须 head 首位)、或文档解析出多个 head。
**为什么(why)**: DOCTYPE 决定标准模式还是怪异模式——怪异模式下盒模型与解析规则回退上古行为,布局不可预测;charset 不在 head 前部时浏览器可能先用错编码解码再重解析,正是 mojibake 的机制性来源(与 content-deploy-hygiene 的乱码判定同源);多 head 是模板拼接事故,解析器容错重组后的 DOM 与你写的不一致。
**触发(trigger)**: 1) 无 `<!DOCTYPE html>` 即 warn;2) charset 声明非 head 内首位即 warn;3) 文档解析出 >1 个 head 即 fail。
**不修的条件(caveat)**: 结构家族不(直接)影响排名(引擎容错强),然而它决定浏览器与引擎各自"看到什么",所以一般建议骨架零错。但遗留系统改 DOCTYPE 会牵动整站盒模型的,先在影子环境回归再上。
**修复(fix)**: 模板统一 `<!DOCTYPE html>` 开头;`<meta charset="utf-8">` 紧随 head 开标签;排查双 head 的模板拼接/组件注入。
**导出(export)**: Reports > HTML Validation > Document Structure
**关联(seealso)**: htmlval-duplicate-meta、htmlval-head-content、content-deploy-hygiene;[semantic-html.md](semantic-html.md)、[head-elements.md](head-elements.md)

#### htmlval-duplicate-meta [待核 ID]
- 名称/类型: 重复 title/description(title 家族与 description 家族收口) —— issue · 优先级 high · 输出 CRITICAL(源表:多 title=fail;多 description=fail;title 在 head 外=fail)
**这意味(what)**: 文档里不止一个 `<title>` 或不止一条 meta description,或 title 出现在 head 之外。
**为什么(why)**: 多条声明时引擎取哪条不可控(常见取第一条或最后一条,实现不一),SERP 展示与你的优化对象脱节;title 在 head 外按无效处理等于没写。与 core-canonical-multiple(多条 canonical)同构:重复声明的歧义性比缺失更糟——坏信号>缺信号的又一次体现。title/description 家族的其余形态(缺失/长度/跨页重复)分别见 core-title、core-description、core-title-unique、content-duplicate-description,本条收口"多条/错位"。
**触发(trigger)**: 1) `<title>` 计数 >1 即 fail;2) meta description 计数 >1 即 fail;3) title 元素祖先链不含 head 即 fail。
**不修的条件(caveat)**: 无豁免;双写几乎总是两套注入(框架默认+业务代码)各写一次,修复是找源头,不是删一条留一条。
**修复(fix)**: head 注入收敛单一出口(head 组件/helmet 类方案);CI 断言 title=1、description=1 且都在 head 内。
**导出(export)**: Reports > HTML Validation > Duplicate Title or Description
**关联(seealso)**: core-title、core-description、core-canonical-multiple、htmlval-document-structure;[head-elements.md](head-elements.md)

#### htmlval-head-content [待核 ID]
- 名称/类型: head 非法元素家族 —— warning · 优先级 low · 输出 WARN(源表 warn;head 白名单 meta/title/link/script/style/base/noscript;head 内 noscript=warn)
**这意味(what)**: head 里出现白名单之外的元素(文本、div、img 等),或 head 内放了 noscript。
**为什么(why)**: HTML 规范限定 head 只容纳元数据元素;非法内容触发解析器把 head 提前截断,把后续本该在 head 里的声明(meta/canonical)挤进 body——连带制造 core-canonical-outside-head 一类问题。head 内 noscript 是特例:其内部只允许 link/style/meta,常被误用于塞内容或脚本。
**触发(trigger)**: 1) head 子元素标签名 ∉ {meta,title,link,script,style,base,noscript}(纯空白文本豁免)即 warn;2) head 内存在 noscript 即 warn。
**不修的条件(caveat)**: 解析器会自愈重组,多数用户看不出异常,然而重组后的 DOM 与源码意图错位是隐患源,所以一般建议 head 纯净。但模板注释/条件注释残片命中属误报级,顺手清理即可。
**修复(fix)**: 内容元素全部移出 head;noscript 的降级样式放 style、跳转提示放 body;模板 lint 头部白名单。
**导出(export)**: Reports > HTML Validation > Illegal Head Content
**关联(seealso)**: htmlval-document-structure、core-canonical-outside-head;[head-elements.md](head-elements.md)

#### htmlval-base [待核 ID]
- 名称/类型: base 元素误用 —— issue/warning · 优先级 medium · 输出 CRITICAL(href 空/畸形/非 HTTP(S),源表 fail)/WARN(多条,源表 warn;须 ≤1 条)
**这意味(what)**: `<base>` 的 href 为空、畸形或非 HTTP(S) 协议,或文档里有多条 base。
**为什么(why)**: base 重定义全页相对 URL 的解析基准:它一坏,页内所有相对链接/canonical/hreflang 的解析结果整体漂移——一条坏 base 能同时引爆相对 URL 类判罚,是单点故障放大器。规范限定每文档至多一条。
**触发(trigger)**: 1) base href 空/不可解析/协议非 http(s) 即 fail;2) base 计数 >1 即 warn。
**不修的条件(caveat)**: base 写对时不产生任何 SEO 问题,然而它的全局副作用让任何后续改动都隐含风险,所以一般建议现代项目直接用绝对/根相对 URL 弃用 base。但遗留系统深依赖 base 的,保持单条+合法绝对 href 即可。
**修复(fix)**: 优先移除 base、模板输出绝对 URL;必须保留时单条+合法绝对 href;上线检查清单加 base 计数断言。
**导出(export)**: Reports > HTML Validation > Base Element
**关联(seealso)**: i18n-hreflang-relative-url、core-canonical、htmlval-head-content;[head-elements.md](head-elements.md)

#### htmlval-html-size [待核 ID]
- 名称/类型: HTML 体积与占位文本 —— warning/issue · 优先级 medium · 输出 WARN(>250KB 与 lorem ipsum)/CRITICAL(>500KB)(源表:>250KB 警、>500KB 败、~2MB 以上 Googlebot 可能只索引前段;lorem ipsum=warn)
**这意味(what)**: 未压缩 HTML 超过 250KB(500KB 进败档,~2MB 以上 Googlebot 可能只索引前段),或页面含 lorem ipsum 占位文本。
**为什么(why)**: HTML 体积是解析与抓取预算的直接消耗:超大文档可能只处理前段,尾部内容与链接被截断;250/500KB 几乎总是内联数据 JSON/隐藏 DOM/注释未清的症状。lorem ipsum 则是模板没换真文案就上线的直接证据,对用户与引擎都是无意义内容(与 content-placeholder-text 的 {{ }} 占位符同族,此处并入陈述)。
**触发(trigger)**: 1) HTML 响应体 >250KB 即警;>500KB 即败;2) 文本命中 lorem/ipsum 词表即 warn。
**不修的条件(caveat)**: 体积阈值不是排名开关,然而它标记"尾部内容可能不被处理",所以一般建议压回 250KB 内并把关键内容与链接放前段。但合法的大文档(长表格/内联数据应用页)超线是形态属性,优先保证前段完整而非硬拆。
**修复(fix)**: 内联 JSON 改按需接口拉取;注释/调试属性剥离;长列表服务端分页;lorem 命中直接换真文案或下线页面。
**导出(export)**: Reports > HTML Validation > HTML Size / Placeholder Text
**关联(seealso)**: perf-page-weight、perf-dom-size、content-deploy-hygiene;[cwv-playbook.md](cwv-playbook.md)

### AI/GEO Readiness(13 条,权重 2%)

**全部 13 条细则已吸收于 [validation-guide.md](validation-guide.md)「审计阈值补充」与 [ai-crawler-policy.md](ai-crawler-policy.md)**,此处仅存目:geo-semantic-html/geo-content-structure/geo-ai-bot-access(GPTBot/Claude-Web/Anthropic/Google-Extended 放行)/geo-llms-txt(info)/geo-schema-drift(schema 须与可见内容一致)/geo-content-signals(Content-Signal 语法+ai-train=yes 但训练 bot 全 Disallow=矛盾)/geo-noai-signals(恒 pass 不扣分)/geo-agents-md/geo-well-known(MCP/agent-card)/geo-rsl-license/geo-markdown-response(根路径出 Markdown)/geo-markdown-page(非根 URL 须有 .md 表示)/geo-pay-per-crawl(402 且无 Pay/Crawler-Price/X-Crawler-Price/payment Link 头才警)。

### Legal Compliance(1 条,权重 1%)

`legal-cookie-consent`:检测 CMP(CookieYes/OneTrust/Cookiebot/Termly/Quantcast);有 CMP 或无追踪脚本=pass,有追踪无 CMP=warn。

---

## 五、吸收备注(去重边界)

- CWV 五阈值/权重表/档位 → [LCP.md](LCP.md)、[scoring-rubric.md](scoring-rubric.md)。
- raw-vs-rendered 双抓实现 → [rendering-seo.md](rendering-seo.md)。
- AI/GEO 13 条 + 实体图六查 → [validation-guide.md](validation-guide.md)、[ai-crawler-policy.md](ai-crawler-policy.md)、[entity-signal-checklist.md](entity-signal-checklist.md)。
- 本文新增独有:Crawlability 38 条全目、E-E-A-T 16 条全目、i18n 13 条全目(含入向校验/x-default 洞察两维度)、Links 入链族 8 条、Content 跨页族、Mobile parity 五条、全类别数字阈值。

---

## 六、未覆盖规则(扩写边界与进度)

- 解释层本版覆盖 **170 条**:第一波 79 条 P0/P1(Crawlability 34/i18n 13/Core SEO 18/Links 4/Redirects 4/Content 重复族 4/Images alt 1/Social og:url 1,聚焦 canonical·noindex·重复内容·断链·重定向·sitemap·hreflang·title/H1 结构家族)+ 第二波 44 条 medium/low 高价值(Crawlability 分页 2/Links 6/Content 6/Images 5/Social 3/Performance 8/Structured Data 5/URL 5/JS Rendering 4)+ 第三批 47 条(Technical SEO 10:5xx·超时·空 HTML·soft-404·非 404 4xx·自定义 404·robots.txt·sitemap 存在性·Content-Type·URL 一致性·埋点卫生;Security 6:HTTPS/混合内容·安全头族·TLS/证书·Cookie·链接引用安全·内容危险信号;Mobile 6:字号·viewport 配置·横向滚动·插页·image maps·parity 五条;Links 6:无内链·外链可达·畸形 href 家族·断锚点·onclick·外链 nofollow;HTML Validation 5:文档结构·多 title/description·head 非法元素·base·体积与 lorem;Content 5:文本比·可读性·相对薄·标题模式·MIME 破损;Redirects 3:静态资源·大小写规范化·资源链;Core SEO 2:viewport/favicon;Crawlability 2:pdf-size/crawl-delay 收口 38 条全量;i18n 1:lang 一致性;Performance 1:preconnect)。
- **其余约 200 条仍以表格/浓缩表形式维护,是唯一事实来源**:阈值以表格为准,条目与表格冲突时改条目不改表。E-E-A-T 16 条、Accessibility 34 条(语言码两条已并入 i18n)、Images/Structured Data 表内剩余同构条、AI/GEO 13 条等未扩写类的判定阈值都在第四节浓缩表与被吸收的专项文档(LCP.md/validation-guide.md/ai-crawler-policy.md 等)里。
- 后续扩写按同规范增量进行:优先级次序建议为 E-E-A-T 16 条(信任基建+作者维度+YMYL 开关)→ Accessibility 剩余(对比度/触控目标/ARIA 族)→ Images/Structured Data 表内剩余同构条 → Legal 1 条;每扩一批,更新本节数字。
- 新增条目必须照抄源表阈值并遵守〇节 ID 纪律与两轴哲学;来源变动的核对入口是 intel_check.py 的 google-updates 源(映射到本文)。


