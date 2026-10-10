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

> 结构与文案纪律来自 [borrow-specs.md](../research/borrow-specs.md) A2 节(Sitebulb 九节结构 + SF 320 条 issue 矩阵实证)。**各节表格仍是全量索引、永不删行**;解释层只覆盖 P0/P1(本版 79 条),其余规则见文末"未覆盖规则"。

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

**解释层(34 条 P0/P1;其余 pagination-sequence/pagination-orphaned/pdf-size/crawl-delay 留在上表)**

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

**解释层(13 条全部扩写)**

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

---

## 四、其余 17 类规则目录(浓缩表,保留全部数字阈值)

### Core SEO(24 条,权重 11%)

title 缺失=fail、长度 **30-60 字符**=warn;description 缺失=fail、**120-160 字符**=warn;canonical 缺失=fail、非绝对/不可达(须 200)=warn;viewport 缺失=fail;favicon 缺失=warn;H1 缺失=fail、多于 1 个=warn;`core-canonical-header`(HTML canonical 与 HTTP Link 头不一致=warn,Link 头应留给 PDF);`core-nosnippet`(nosnippet/max-snippet:0=warn);`core-robots-meta`(noindex/nofollow/noarchive/noimageindex/none=warn);`core-title-unique`(跨页重复 title,crawl,warn/fail);**canonical 家族 8 条**:conflicting(多信号不一致=fail)/to-homepage(深页指向首页=warn)/http-mismatch(协议不一致=warn)/loop(环=fail)/to-noindex(指向 noindex=fail)/outside-head(在 body 里=fail,引擎直接忽略)/attributes(带 hreflang/lang/media/type 属性改变语义=fail,其他多余属性=warn)/multiple(多条且不一致=fail,一致=warn);`core-robots-directive-mismatch`(meta 与 X-Robots-Tag 一方 index 一方 noindex=fail,多处声明 noindex=warn);`core-canonical-external`(指向外域=info,联合发布合法但让渡排名信号)。

**解释层(18 条;ID 未公布原文的按家族命名法推得并标 [待核])**

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

### Performance(28 条,权重 10%)

**CWV 五指标阈值已吸收于 [LCP.md](LCP.md) 与 [scoring-rubric.md](scoring-rubric.md)**:LCP ≤2.5s/2.5-4/>4;CLS ≤0.1/0.1-0.25/>0.25;INP ≤200ms/200-500/>500;TTFB ≤800ms/800-1800/>1800;FCP ≤1.8s/1.8-3/>3。表内补静态项:DOM **<800 过/800-1500 警/>1500 败,深度>32 警**;`perf-asset-cache-policy`(静态资源 max-age ≥1 小时,渲染专属);`perf-asset-compression`(**>2KB** 文本资源须 gzip/Brotli,按 content-length,chunked 无长度不判);`perf-image-encoding`(图片传输 **>100KB=warn**,BMP/TIFF=fail);`perf-page-weight`(**<3MB** 建议);`perf-cache-policy`(带内容 hash 的静态资源 `max-age=31536000`);`perf-minify-css/js`(内联查空白比/块注释;外链 **>2KB** 且 URL 无 `.min.` 标记=启发式嫌疑,恒 ≤warn);`perf-response-time`、`perf-http2`(须 HTTP/2+)、`perf-render-blocking`(head 内脚本无 async/defer)、`perf-lazy-above-fold`(首屏图禁 lazy)、`perf-lcp-hints`(LCP 图须 preload+fetchpriority=high)、`perf-font-loading`(font-display:swap)、`perf-preconnect`、`perf-text-compression`、`perf-brotli`、`perf-video-for-animations`(GIF→video 省 90%)、`perf-legacy-javascript`、`perf-duplicate-js`(同库多 URL)、`perf-source-maps`(不得暴露 sourceMappingURL)。

### Links(27 条,权重 8%)

内链 4xx=fail;外链可达性=warn(结果缓存);无内链=warn;nofollow 滥用=warn;泛化锚文本("click here"/"read more"/"link")=warn;`links-depth`(**点击距离 ≤3**,crawl);死端页(无出链)=warn;HTTPS 页链 HTTP=warn;**外链 >100=warn**;空/javascript:/畸形 href=warn;tel:/mailto: 格式=warn;重定向链(**1-2 跳=warn,≥3=fail**);`links-localhost`(127.0.0.1=fail)/`links-local-file`(file://=fail);断锚点(#id 无匹配)=warn;`links-onclick`(onclick 导航替代 href=warn);href 首尾空白=warn;非 HTTP 协议(ftp:/intent:/chrome:)=warn;**crawl 专属入链族 8 条**:inbound-all-nofollow(全 nofollow=零权重流入,洞见级)/inbound-mixed-follow(有follow有nofollow=不一致)/inbound-low-quality(入链全 nofollow 或全来自被 canonical 走的页)/inbound-anchor-text(全部入链锚文本<2 字符或泛化)/nofollow-internal(同主机链接禁 nofollow)/weak-inbound(**非入口页须 >1 条 dofollow 入链**)/chrome-inbound(**至少 1 条入链在 nav/header/footer 之外**——正文链才算票)/orphan-pages(真孤儿由 crawl-sitemap-orphan-urls 配合判)。

**解释层(4 条;ID 未公布原文的标 [待核])**

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

### Images(14 条,权重 8%)

alt 缺失=fail;alt 泛化("image"/文件名)=warn;alt 长度 **5-125 字符**=warn;宽高属性缺失=warn(防 CLS);below-fold 须 `loading="lazy"`=warn;现代格式(WebP/AVIF 比 JPEG/PNG 小 30-50%)=warn;体积=warn;srcset 响应式=warn;图片 404=fail;figure 缺 figcaption=warn;文件名(IMG_001.jpg 坏/red-running-shoes.jpg 好)=warn;**内联 SVG >5KB 应外链**=warn;picture 缺 img 回退=fail;内容图用 CSS background(引擎读不到)=warn。

**解释层(1 条;ID 未公布原文,标 [待核])**

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

### Security(26 条,权重 8%)

非 HTTPS=fail;HTTP 不 301 到 HTTPS=warn;缺 HSTS(`max-age=31536000; includeSubDomains`)/CSP/X-Frame-Options(DENY/SAMEORIGIN)/nosniff/Permissions-Policy/Referrer-Policy(strict-origin-when-cross-origin)/COOP(`same-origin`,防 tabnabbing)=各 warn;`target=_blank` 缺 noopener/noreferrer=warn;表单 action 非 HTTPS=warn/fail;混合内容=warn/fail;`security-csp-xss`(CSP 是否真约束脚本:'unsafe-inline' 无 nonce=不设防;无 CSP 时按权重 0 报,避免与 security-csp 双重扣)/`security-info-disclosure`(Server 带版本号/X-Powered-By=warn,裸 `Server: nginx` 过)/`security-paste-blocking`(onpaste 阻止粘贴=fail,毁密码管理器)/`security-trusted-types`(仅已设 CSP 的站评,`require-trusted-types-for 'script'`)/`security-leaked-secrets`(AWS key/API token/私钥/数据库 URL=fail)/`security-password-http`(HTTP 页密码框=fail)/协议相对 URL `//`=warn;Cookie 三旗(Secure/HttpOnly/SameSite)=warn/fail;**Cookie 寿命 >400 天上限=warn**;SSL 到期=warn/fail;**TLS 须 1.2+**(1.0/1.1=warn/fail);SRI(跨域脚本/stylesheet 须 integrity hash)=warn;混淆脚本(长高熵内联脚本调 eval/Function/atob)=warn;品牌登录链指向品牌或本域=warn。

### Technical SEO(18 条,权重 7%)

robots.txt 存在/语法=warn;sitemap 存在/格式=warn;URL 结构(小写+连字符)=warn;尾斜杠一致性=warn;www 一致性 301=warn;自定义 404=warn;soft-404(200 但错误内容)=warn;5xx=fail;**非 404 的 4xx(403/410 等)=warn**;超时=fail;Content-Type 错=warn/fail;**200 空 HTML(fhead/body 皆空)=fail**;`technical-form-get-method`(GET 表单产生可抓取查询串 URL=warn);**多 GTM 容器/多 GA 属性(>1 个不同 ID)=warn**;`technical-consent-mode`(Google 标签须配 consent update)=warn。

### Structured Data(19 条,权重 5%)

缺 JSON-LD=warn;JSON 语法坏=fail;缺 @type=warn;类型必填字段=warn;Article 须 headline/author/datePublished/image;BreadcrumbList(非首页,**≥2 个 itemListElement**)=info;FAQPage 每个 Question 须 name+acceptedAnswer.text=fail;LocalBusiness 须 name/address/telephone/geo;Organization 须 name/logo/sameAs;Product 须 offers(price/priceCurrency/availability)=fail;Review 须 itemReviewed/author/reviewRating;VideoObject 须 name/thumbnailUrl/uploadDate(时长 ISO 8601 如 PT1M30S);WebSite SearchAction 含 `{search_term_string}`=info。**实体图六查已吸收于 [entity-signal-checklist.md](entity-signal-checklist.md) 与 [validation-guide.md](validation-guide.md)**:entity-id(@id 绝对)/rating-scope(AggregateRating 不在 legal/account URL 且 ratingValue 可见)/entity-conflict(一 @id 两 logo/两电话)/entity-dangling(publisher/author/isPartOf 的 @id 须在爬取中声明)/entity-type-drift(同 @id 跨页同 @type)/entity-split(同名组织不挂两 @id)。

### Content(27 条,权重 5%)

词数 **≥300 过/100-299 警/<100 败**(文章建议 500+,长文 1000+);Flesch-Kincaid **60-70** 最优;关键词堆砌=warn/fail;标题层级不跳(H1→H3=invalid);**标题 <3 字符或 >100 字符=警**;页内标题重复=warn;text/HTML 比=warn;title 与 H1 相同=warn;**title 像素宽 ≤~580px、description ≤~920px**(SERP 截断);title=description 全同=warn;meta 在 body 里=fail;MIME=warn/fail;**crawl 专属**:duplicate-description/duplicate-exact(=fail)/duplicate-near/duplicate-h1(跨页同 H1)/thin-vs-site(**<同类页中位词数一半=警**,需 ≥4 个同类页)/title-pattern(标题未带全站 ≥60% 使用的后缀=警);`content-mojibake`(UTF-8 被按 Latin-1/Windows-1252 解码,如 `â€™`=fail);`content-unrendered-markup`(code/pre 外的字面 Markdown `**bold**`=warn);`content-placeholder-text`(**`{{ }}`/`{% %}`/`<% %>`/`[object Object]`=fail;TODO:/FIXME:=warn**;`content-stale-copyright`(页脚版权年落后当年=warn,区间取末年);`content-date-agreement`(datePublished/time datetime//20xx/ 路径三年份不一致=warn,dateModified 不比);`content-hidden-text`(**≥80 字符**被内联样式隐藏(display:none/visibility:hidden/font-size:0/大负 text-indent/opacity:0)=warn,nav/对话框/sr-only 豁免,仅样式表隐藏不判);`content-broken-html`/`content-meta-in-body`。

**解释层(重复内容家族 4 条;ID 未公布原文,标 [待核])**

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

### JavaScript Rendering(16 条,权重 5%)

**raw-vs-rendered 实现要点已吸收于 [rendering-seo.md](rendering-seo.md) 与 [validation-guide.md](validation-guide.md)**(HTTP 抓原始→$;Playwright 二抓→rendered$;web-vitals 库 goto 前注入;INP 合成标记 inpSynthetic 不计分)。规则粒度:title/description/H1/canonical 不在初始 HTML=fail/warn/warn/fail;canonical 或 noindex 在源码与渲染 DOM 间不一致=fail;JS 事后改写 title/description/H1=warn;主内容/内链依赖 JS=warn;JS/CSS 被 robots 挡=warn;SSR 检查=warn/fail;**console 未捕获异常与错误=warn/fail**;**子资源加载失败=warn/fail**;内联脚本用 `document.write()`=warn。

### Accessibility(36 条,权重 7%)

对比度 **≥4.5:1 正文/3:1 大字**;触控目标 **≥44×44 CSS px**(WCAG 2.5.8);交互元素须可访问名(aria-label/文本/title);focus 样式可见;表单 label(placeholder 不算);标题不跳级;landmark(main/nav/header/footer);描述性链接文本;skip-to-content 链接;表格 th+scope;视频字幕/文稿;viewport 禁缩放(user-scalable=no/maximum-scale=1)=fail;aria-hidden 包可聚焦元素=fail;**ARIA 角色/属性拼错浏览器静默丢弃(aria-lable→aria-label)=fail**;accesskey 唯一;**ID 重复致 aria-labelledby/label for 解析到第一个匹配=fail(svg 内 url(#id) 引用的 clipPath 豁免)**;空标题=fail;一控件一 label;同文本链接须同目的地;iframe/object 须 title/替代文本;`<input type=image>` 须 alt;**可访问名须含可见文本(语音用户"说所见")**;按钮有名;email/tel 输入配对 autocomplete token;lang 与 xml:lang 一致;html/body 禁 aria-hidden;ARIA widget 须有所需父子角色(tab 在 tablist 内/option 在 listbox 内);列表只含 li;**恰一个 main landmark**;role=none/presentation 不被 ARIA/可聚焦性反证;alt 不重复相邻链接/图注文本;img 角色 SVG 须可访问名;表格用 caption 不用跨列首行;**tabindex 禁正值**;元素级 lang 合法 BCP 47。

### Social(9 条,权重 3%)

og:title/description/image 各=warn;**og:image 推荐 1200×630(配 og:image:width/height meta)**;og:url=warn;**og:url 与 canonical 不一致=fail**;twitter:card(summary_large_image)=warn;分享按钮(**≥2 平台**)=warn;社交资料链接(**≥3 个**,入 Organization sameAs)=warn。

**解释层(1 条;ID 未公布原文,标 [待核])**

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

### URL Structure(14 条,权重 3%)

slug 含描述关键词(数字 ID/?p=123 坏)=fail/warn;URL 停用词=warn;大写=warn;下划线=warn(连字符才是词分隔);双斜杠=warn;**%20 编码空格=fail**;非 ASCII=warn;**路径 ≤75 字符**=warn;重复路径段(/shoes/shoes/)=warn;**查询参数 3-5 个=warn、>5=fail**,同名参数重复或多个 `?`=畸形=warn;**URL 会话 ID=fail**;UTM/追踪参数=warn;站内搜索 URL 被索引=warn;HTTP/HTTPS 双可达=warn。

### Redirects(11 条,权重 3%)

meta refresh=warn;JS 重定向=warn;HTTP Refresh 头=warn;环=fail;301(永久/传权重)vs 302(临时)用错=warn;目标 4xx/5xx=fail;**静态资源被重定向=warn**;大小写规范化重定向=warn;**渲染专属三条**:resource-broken(资源重定向终点 4xx/5xx=fail)/resource-loop(资源重定向环,浏览器 ERR_TOO_MANY_REDIRECTS=fail)/**resource-chain(资源 ≥2 跳=warn,单跳 http→https/尾斜杠视为良性)**。

**解释层(4 条;ID 未公布原文,标 [待核];JS/HTTP Refresh 头两条并入 meta-refresh 条目陈述)**

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

### Mobile(12 条,权重 2%)

正文字号 **≥16px 过,<12px 败**(rem/em 优);横向滚动=warn/fail;插页弹窗(跳过 cookie/GDPR/年龄验证/登录)=warn/fail;viewport 须 device-width=warn;多 viewport 标签=fail;**parity 五条(`--mobile` 双渲染对比,我们覆盖薄)**:content/title+description/canonical=warn/fail,structured-data=fail(JSON-LD 桌面有移动无),links(内链数量可比)=warn;image maps(`<map>`/`<area>` 客户端图像地图,固定像素坐标不适配触屏)=warn;viewport content 规范(width 存在+initial-scale=1+**不设 minimum-scale**)=warn。

### HTML Validation(11 条,权重 2%)

缺 DOCTYPE=warn;缺 charset(utf-8 须 head 首位)=warn;head 含非法元素=warn(白名单:meta/title/link/script/style/base/noscript);head 内 noscript=warn;多 head=fail;**HTML 体积 >250KB 警、>500KB 败、~2MB 以上 Googlebot 可能只索引前段**;lorem ipsum=warn;多 title=**fail**;多 description=**fail**;title 在 head 外=fail;base 元素(href 空/畸形/非 HTTP(S)=fail,多条=warn,须 ≤1 条)。

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

- 解释层本版覆盖 **79 条**(Crawlability 34/i18n 13/Core SEO 18/Links 4/Redirects 4/Content 重复族 4/Images alt 1/Social og:url 1),全部为 P0/P1(fail/critical 优先,聚焦 canonical·noindex·重复内容·断链·重定向·sitemap·hreflang·title/H1 结构家族)。
- **其余约 290 条仍以表格/浓缩表形式维护,是唯一事实来源**:阈值以表格为准,条目与表格冲突时改条目不改表。E-E-A-T 16 条、Performance 28 条、Security 26 条、Accessibility 36 条、Mobile parity、AI/GEO 13 条等未扩写类的判定阈值都在第四节浓缩表与被吸收的专项文档(LCP.md/validation-guide.md/ai-crawler-policy.md 等)里。
- 后续扩写按同规范增量进行:优先级次序建议为 Links 入链族 8 条 → Technical SEO 的 5xx/空 HTML/soft-404 → JS Rendering 双抓族 → Mobile parity 五条;每扩一批,更新本节数字。
- 新增条目必须照抄源表阈值并遵守〇节 ID 纪律与两轴哲学;来源变动的核对入口是 intel_check.py 的 google-updates 源(映射到本文)。


