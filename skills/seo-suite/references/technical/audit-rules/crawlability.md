# 审计规则目录 · Crawlability

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

## 一、重点展开:Crawlability(38 条,我们此前覆盖最薄)

审计索引信号、sitemap 冲突、canonical 链与分页。**17 条跨页规则仅 crawl 模式测量**(表内标 ⛏)。严重度与要点按源表现行版(132d2384)。

| 规则 ID | 名称 | 严重度 | 判定阈值/要点(源表现行) |
|---|---|---|---|
| `crawl-schema-noindex-conflict` | Schema+Noindex 冲突 | fail | noindex 页上存在富结果 schema |
| `crawl-pagination-canonical` | 分页 canonical | warn/fail | 每个分页页须自引用 canonical;全指向第 1 页=错 |
| `crawl-sitemap-domain` | Sitemap 域名 | warn/fail | 经 index 读出的页面 URL 须在被审 host(www 与非 www 都算);>10% 在他 host=fail,更少=warn;找不到 sitemap=warn |
| `crawl-noindex-in-sitemap` | noindex 入 sitemap | warn/fail | noindex 页被列入=fail;取不到 sitemap=warn(只读 /sitemap.xml 或 robots 首条 Sitemap,index 只读前 3 个) |
| `crawl-indexability-conflict` | 索引性冲突 | warn | Googlebot 组(无则 `*` 组)Disallow 本页即 warn,有无 noindex 都报 |
| `crawl-canonical-redirect` | canonical 指向重定向 | warn/fail | 1-2 跳=warn,≥3 跳或目标 4xx/5xx=fail;无 canonical=warn |
| `crawl-sitemap-url-limit` | Sitemap 条数上限 | warn/fail | 逐文件:>40,000=warn,>50,000=fail |
| `crawl-sitemap-size-limit` | Sitemap 体积上限 | warn/fail | 逐文件按未压缩:>40MB=warn,>50MB=fail |
| `crawl-sitemap-duplicate-urls` | sitemap 内重复 URL | warn | 同一 URL 在全部已取 sitemap 中出现 >1 次 |
| `crawl-sitemap-orphan-urls` ⛏ | Sitemap 孤儿 URL | warn | sitemap 列出、已爬页面无一链向它 |
| `crawl-blocked-resources` | 屏蔽 CSS/JS | warn | robots.txt Disallow 挡住渲染资源 |
| `crawl-blocked-images` | 屏蔽图片 | fail | 同源图片 URL 被 Disallow(RFC 9309 匹配器);未取到 robots.txt=不测 |
| `crawl-crawl-delay` | crawl-delay | warn | `*`、Googlebot 或 Bingbot 组 Crawl-delay >10 秒 |
| `crawl-sitemap-in-robotstxt` | robots.txt 缺 Sitemap 行 | warn | 应加 `Sitemap: https://…/sitemap.xml` |
| `crawl-sitemap-lastmod` | lastmod 质量 | warn | 无任何 lastmod,或非法/未来日期/90% 落在同一天 |
| `crawl-pagination-broken` | 分页 href 不可解析 | fail | `rel="next/prev"` 的 href 解析不出 URL;不请求目标 |
| `crawl-pagination-loop` | 分页指回自身 | fail | `rel="next/prev"` 指向本页 |
| `crawl-pagination-sequence` | next/prev 相同 | fail | `rel="next"` 与 `rel="prev"` 指向同一 URL |
| `crawl-pagination-noindex` | 分页被 noindex | warn | 带 rel=next/prev 的页带 noindex |
| `crawl-pagination-orphaned` | 分页缺 rel 标记 | warn | URL 形如分页(?page=N、/page/N 等)却无 rel=next/prev |
| `crawl-pagination-isolated` ⛏ | 分页 URL 无入链 | fail | 分页形 URL 无普通 `<a>` 指向(抓"另径发现"的分页) |
| `crawl-sitemap-non-200` ⛏ | Sitemap 内非 200 | warn/fail | 与爬取状态码交叉:**4xx/5xx=fail,3xx 与超时=warn**;未爬到不判 |
| `crawl-sitemap-non-canonical` ⛏ | Sitemap 内非规范 URL | fail | sitemap 说"索引这个"、canonical 说"索引那个" |
| `crawl-sitemap-disallowed` ⛏ | Sitemap 内被 Disallow | fail | 与 robots.txt 矛盾;无 robots 内容且无 Disallow 时报 unmeasured |
| `crawl-sitemap-cross-duplicates` ⛏ | 一 URL 多 sitemap | warn | 跨 sitemap 文档重复声明;信息级 |
| `crawl-canonical-to-noindex` ⛏ | canonical→noindex | fail | 目标自身 noindex;自引用通过;未爬到报 unmeasured |
| `crawl-canonical-to-disallowed` ⛏ | canonical→Disallow | fail | 目标被 robots.txt 禁 |
| `crawl-canonical-chain` ⛏ | canonical 链 | warn | A→B→C;环由 loop 规则报 |
| `crawl-canonical-loop` ⛏ | canonical 环 | fail | 跟踪目标回到已访问 URL |
| `crawl-hreflang-to-noindex` ⛏ | hreflang→noindex | fail | 出向注解的已爬目标 noindex |
| `crawl-hreflang-to-disallowed` ⛏ | hreflang→Disallow | fail | 出向注解指向被禁页 |
| `crawl-hreflang-disallowed-target` ⛏ | 被禁页收 hreflang | fail | 本页被 Disallow 而他页指它 |
| `crawl-hreflang-incoming-conflict` ⛏ | 入向 hreflang 冲突 | fail | 他页对同一 URL 标不同码;本页自己的注解不计,x-default 不算冲突 |
| `crawl-hreflang-reciprocity` ⛏ | hreflang 回链 | warn | 已爬目标须反向标注本页;未爬到跳过 |
| `crawl-isolated-url` ⛏ | 孤立 URL | fail | 只经 canonical/重定向/sitemap/noindex,follow 页/其他孤立页发现,无锚点入链(一次传播);爬取入口必过 |
| `crawl-canonical-form-drift` ⛏ | canonical 形态漂移 | warn | 各页 canonical 在 www/协议/尾斜杠上不一致;需 ≥2 页 |
| `crawl-sitemap-date-drift` | 日期漂移 | warn | sitemap lastmod 与 schema dateModified 同日 |
| `crawl-pdf-size` | 链接 PDF 体积 | warn | Content-Length **>10MB** 警;HEAD 最多查 **8 个**;缺长度跳过 |

**为什么这 38 条值钱**:它们把孤立 URL 的一次传播、入向与出向 hreflang 分开判、sitemap×robots×canonical×noindex 两两交叉做成了独立规则。注意源表分页 5 条只看 `rel="next/prev"`;Google 已不用这对标记(见 crawl-pagination-canonical 条),对 Google 有意义的是 `<a href>` 翻页链接与 canonical。

**解释层(36 条;34 条第一波 P0/P1 用执行版六字段,其余见第三批)**

### crawl-canonical-to-noindex ⛏
- 源表:fail · 权重 8 · 需 `--crawl`。canonical 目标页自身 noindex。工具约定。建议优先级 critical。
**依据**: Google 要求核实 canonical 目标不带 noindex([2013 博文](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical));也不建议用 noindex 干预规范页选择([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。两信号冲突时 Google 选哪个未公开。核对 2026-10-18。
**判据**: 通过=canonical 自引用,或目标 200 且无 noindex/none。失败=目标的 meta robots/googlebot 或 X-Robots-Tag 含 noindex/none。目标未抓到=不判。
**执行**: site_audit 不跨页。对目标跑 `AUDIT 目标URL`,出现 `[CRITICAL] robots: noindex` 即失败(它不识别 none 与 googlebot meta,用 G6 补查);sitemap 内 URL 批量看 `SITEMAP` 桶3。
**修复**: 目标该索引就删 noindex;不该索引就把 canonical 改回自引用,或改指可索引页。
**关联**: core-canonical-to-noindex、crawl-hreflang-to-noindex;[redirects-canonical.md](../redirects-canonical.md)

### crawl-canonical-to-disallowed ⛏
- 源表:fail · 权重 8 · 需 `--crawl`。canonical 目标被 robots.txt Disallow。工具约定。建议优先级 critical。
**依据**: Google 读不到被 Disallow 页的内容,只可能凭外链收录 URL([robots 规范](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec));canonical 目标应是存在的正常页([2013 博文](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical))。合并结果未公开。核对 2026-10-18。
**判据**: 通过=目标对 Googlebot 可抓。失败=目标被 Googlebot 组(无则 `*` 组)Disallow。
**执行**: `AUDIT 目标URL` 出现 `[CRITICAL] ai-bots: Googlebot 被禁` 即失败。site_audit 按最长前缀匹配,不支持 `*`/`$` 通配,且路径按小写比;有通配规则时用 GSC 网址检查「是否允许抓取(Crawl allowed?)」复核。
**修复**: 要合并就从 robots.txt 放行该路径,索引控制改用 noindex;不要合并就把 canonical 改自引用。
**关联**: crawl-indexability-conflict、crawl-canonical-to-noindex;[robots-txt-reference.md](../robots-txt-reference.md)

### crawl-canonical-loop ⛏
- 源表:fail · 权重 8 · 需 `--crawl`。跟踪 canonical 回到已访问 URL。工具约定。建议优先级 high。
**依据**: Google 文档未专门谈 canonical 环;canonical 只是提示,Google 可另选规范页([规范化文档](https://developers.google.com/search/docs/crawling-indexing/canonicalization))。环让你的提示没有终点。核对 2026-10-18。
**判据**: 通过=链终止于自引用页。失败=链回到起点或任一途经 URL。
**执行**: `CRAWL` 后跑 J2,有输出即失败(只覆盖已爬页面);单页手工:G1 读出目标,再对目标跑 G1,看是否指回。
**修复**: 选定终点页让它自引用,其余页直指它;查模板是否把参数写进 canonical。
**关联**: core-canonical-loop、crawl-canonical-chain;[redirects-canonical.md](../redirects-canonical.md)

### crawl-canonical-chain ⛏
- 源表:warn · 权重 6 · 需 `--crawl`。canonical 目标自身又 canonical 到第三页(A→B→C)。工具约定。建议优先级 medium。
**依据**: Google 要求规范页本身带自引用 canonical([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls));链说明 B 不是规范页。"每跳衰减"无官方出处,不作理由。核对 2026-10-18。
**判据**: 通过=目标自引用或无 canonical。失败=目标 canonical 指向第三个 URL。
**执行**: `CRAWL` 后跑 J1,每行一条链。
**修复**: 前驱页全部直指链终点;确认终点 200 且自引用。
**关联**: crawl-canonical-redirect、crawl-canonical-loop;[redirects-canonical.md](../redirects-canonical.md)

### crawl-canonical-redirect
- 源表:warn/fail · 权重 15。canonical 目标重定向 1-2 跳=warn,≥3 跳或目标 4xx/5xx=fail;无 canonical=warn。工具约定。建议优先级 high。
**依据**: Google 要求 canonical 目标真实存在,不是错误页或 soft 404([2013 博文](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical))。"必须直指最终 URL"是工具约定,Google 文档无此句。核对 2026-10-18。
**判据**: 通过=目标直接返回 200。警告=目标 1-2 跳后 200。失败=≥3 跳或终点 4xx/5xx。
**执行**: `REDIR 目标URL`,看「链长」与「终态: HTTP」两行;已爬全站用 J3。
**修复**: canonical 改写为重定向链终点 URL,并确认它 200 且自引用。
**关联**: crawl-canonical-chain、links-redirect-chains;[redirects-canonical.md](../redirects-canonical.md)

### crawl-canonical-form-drift ⛏
- 源表:warn · 权重 6 · 需 `--crawl` 且 ≥2 页。各页 canonical 在 www/协议/尾斜杠上不一致。工具约定。建议优先级 low。
**依据**: Google 默认优先 HTTPS 页作规范页,HTTPS 页 canonical 指 HTTP 版会削弱这一偏好;Google 建议站内统一链向规范 URL([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。核对 2026-10-18。
**判据**: 通过=全站 canonical 只有一种协议+host+尾斜杠策略。失败=出现少数派形态(混用 http 最重)。
**执行**: `jq -r '.pages[].canonical // empty' crawl.json | sed -E 's#^(https?://[^/]+).*#\1#' | sort | uniq -c`;输出多于一行即漂移。尾斜杠另用 `grep -c '/$'` 比对。
**修复**: 定一种规范形态,模板统一输出;其余形态 301 到规范形。
**关联**: core-canonical-http-mismatch;[redirects-canonical.md](../redirects-canonical.md)

### crawl-hreflang-to-noindex ⛏
- 源表:fail · 权重 8 · 需 `--crawl`。出向 hreflang 的已爬目标 noindex。工具约定。建议优先级 high。
**依据**: Google 只处理互相指向的一对注解;没互指的那一对被忽略,其余互指的照常处理,不是整簇作废([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。noindex 页不会出现在结果里,这一格语言版等于空缺。核对 2026-10-18。
**判据**: 通过=全部目标可索引。失败=任一目标的 meta robots/googlebot 或 X-Robots-Tag 含 noindex/none。
**执行**: `HREFLANG 簇内全部URL` 列出目标;对每个目标跑 `AUDIT`,出现 `[CRITICAL] robots: noindex` 即失败。
**修复**: 要该语言版就删 noindex;不要就从 HTML/HTTP 头/sitemap 三种载体里一并删掉该成员。
**关联**: i18n-hreflang-to-noindex、crawl-canonical-to-noindex;[hreflang-validation.md](../hreflang-validation.md)

### crawl-hreflang-to-disallowed ⛏
- 源表:fail · 权重 7 · 需 `--crawl`。出向 hreflang 指向被 robots.txt 禁的页。工具约定。建议优先级 high。
**依据**: 推论:被 Disallow 的页 Google 读不到([robots 规范](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec)),也就看不到它的回链;没互指的那一对注解被忽略([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。核对 2026-10-18。
**判据**: 通过=全部目标对 Googlebot 可抓。失败=任一目标被 Disallow。
**执行**: 对每个 hreflang 目标跑 `AUDIT`,出现 `[CRITICAL] ai-bots: Googlebot 被禁` 即失败;通配规则用 GSC「是否允许抓取」复核。
**修复**: 放行该语言版,索引控制改用 noindex/canonical;或从注解集删掉该成员。
**关联**: crawl-canonical-to-disallowed、crawl-hreflang-disallowed-target;[robots-txt-reference.md](../robots-txt-reference.md)

### crawl-hreflang-disallowed-target ⛏
- 源表:fail · 权重 7 · 需 `--crawl`。本页被 Disallow,他页 hreflang 却指向本页。工具约定。建议优先级 high。
**依据**: 同上一条的镜像方向:本页的回链 Google 永远读不到,指向本页的那几对注解被忽略。核对 2026-10-18。
**判据**: 通过=本页可抓,或无人指向本页。失败=本页被 Disallow 且有入向 hreflang。
**执行**: `AUDIT 本页URL` 出现 `[CRITICAL] ai-bots: Googlebot 被禁`;再用 `HREFLANG` 跑引用方,看谁列了本页。
**修复**: 本页本就不该抓时,删掉引用方的注解(HTML/HTTP 头/sitemap);否则放行本页。
**关联**: crawl-hreflang-to-disallowed、crawl-hreflang-reciprocity;[hreflang-validation.md](../hreflang-validation.md)

### crawl-hreflang-incoming-conflict ⛏
- 源表:fail · 权重 7 · 需 `--crawl`。他页给本页标了不同语言码;本页自己的注解不计,x-default 不算冲突。工具约定。建议优先级 high。
**依据**: Google 要求每个语言版列出自己和对应的其他语言版,且互相指回;没互指的那一对被忽略([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。同一 URL 被不同页标成不同语言码,这几对注解互相矛盾;Google 如何裁决未公开。核对 2026-10-21。
**判据**: 通过=所有入向注解对本页用同一个码。失败=出现 ≥2 个不同码(x-default 除外)。
**执行**: `HREFLANG 簇内全部URL`,在矩阵里对比各行给本 URL 的码;站外引用方用 G7 逐页抓。
**修复**: 找到写错的引用方改码;双语页拆成两个 URL。
**关联**: i18n-hreflang-conflicting、i18n-hreflang-incoming-invalid;[hreflang-validation.md](../hreflang-validation.md)

### crawl-hreflang-reciprocity ⛏
- 源表:warn · 权重 6 · 需 `--crawl`。已爬目标没有反向标注本页;未爬到的目标跳过。工具约定。建议优先级 high。
**依据**: "If two pages don't both point to each other, the tags will be ignored";可以在部分页省略部分语言,互指的仍会处理([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。核对 2026-10-18。
**判据**: 通过=每个目标都含"指向本页且码对应"的条目。失败=任一目标缺该条目。
**执行**: `HREFLANG 簇内全部URL`,「双向回报」列出现 ✗ 即失败(脚本退出码 1)。
**修复**: 双向成对生成;页数多时用 sitemap 载体集中维护更省事(三载体对 Google 等价,这只是维护建议);修完重跑 `HREFLANG`。
**关联**: i18n-hreflang-return-links;[hreflang-validation.md](../hreflang-validation.md)

### crawl-isolated-url ⛏
- 源表:fail · 权重 8 · 需 `--crawl`。只经 canonical/重定向/sitemap 发现,无锚点入链;链接者全是 noindex,follow 或自身孤立也算(一次传播);爬取入口必过。工具约定。建议优先级 high。
**依据**: Google 主要靠已抓页面上的链接发现新页([SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide));"每个你在意的页面至少要有一个站内页面链向它"([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable))。核对 2026-10-18。
**判据**: 通过=至少一个可索引页用 `<a href>` 链向它。失败=零锚点入链(传播判定见上)。
**执行**: `CRAWL` 后看 `orphans`(0 入链且非首页),或 `GRAPH` 的入链 0/1 清单;一次传播与 noindex 链接者不在脚本内,需人工复核。`--max` 截断时入链偏少,先确认未截断。
**修复**: 从相关正文页加描述性锚文本内链;该删的页 301 到最近亲页。
**关联**: crawl-sitemap-orphan-urls、links-depth;[link-architecture-patterns.md](../link-architecture-patterns.md)

### crawl-schema-noindex-conflict
- 源表:fail · 权重 15。noindex 页上有富结果类 schema。工具约定。建议优先级 medium。
**依据**: noindex 的页不会出现在搜索结果中([robots meta 规范](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)),其上的富结果标记没有展示机会。这是浪费与治理问题,不是惩罚。核对 2026-10-18。
**判据**: 通过=页面可索引,或只含 Organization/WebSite 等全站标记。失败=noindex 页含 Product/Recipe/Review 等富结果类型。
**执行**: `AUDIT URL` 同时出现 `[CRITICAL] robots: noindex`,且 `curl -s URL | grep -o '"@type" *: *"[^"]*"'` 列出富结果类型。
**修复**: 页面要索引就删 noindex;不要就删该页富结果 schema。预发布页可暂留。
**关联**: crawl-noindex-in-sitemap;[validation-guide.md](../validation-guide.md)

### crawl-noindex-in-sitemap
- 源表:warn/fail · 权重 15。noindex 页被列入 sitemap=fail;取不到 sitemap=warn。工具约定。建议优先级 high。
**依据**: Google 要求 sitemap 只放你想出现在搜索结果里的规范 URL([sitemap 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap))。noindex 仍以 noindex 为准,矛盾不会被惩罚。核对 2026-10-18。
**判据**: 通过=sitemap 内 URL 无一 noindex。失败=任一 URL 的 meta robots 或 X-Robots-Tag 含 noindex。
**执行**: `SITEMAP`,桶3「noindex 页」命中即失败(脚本退出码 1)。
**修复**: 不该索引的从 sitemap 生成器过滤掉;该索引的删 noindex。修完在 GSC 重新提交 sitemap。
**关联**: crawl-sitemap-disallowed、crawl-sitemap-non-canonical、core-robots-meta

### crawl-blocked-images
- 源表:fail · 权重 7。同源图片 URL 被 robots.txt Disallow;未取到 robots.txt 不测。工具约定。建议优先级 high。
**依据**: robots.txt 可以阻止图片出现在 Google 搜索结果中([robots 入门](https://developers.google.com/search/docs/crawling-indexing/robots/intro));被禁的图片因此进不了图片搜索。核对 2026-10-18。
**判据**: 通过=页面内容图对 Googlebot(Googlebot-Image 无专组时同 `*` 组)可抓。失败=任一内容图被 Disallow。
**执行**: site_audit 不查资源。GSC 网址检查 → 测试实际网址 → 查看已测试的网页 → 更多信息,看加载失败的资源与原因;或把图片 URL 逐个对照 robots.txt 规则。
**修复**: 收窄 Disallow 或用 `Allow:` 放行图片目录。付费图库等刻意屏蔽的图不修。
**关联**: crawl-blocked-resources;[robots-txt-reference.md](../robots-txt-reference.md)

### crawl-blocked-resources
- 源表:warn · 权重 7。robots.txt Disallow 挡住 CSS/JS。工具约定。建议优先级 high。
**依据**: Google 2014-10-27 起要求放行 JS/CSS:"Disallowing crawling of Javascript or CSS files ... directly harms how well our algorithms render and index your content"([博文](https://developers.google.com/search/blog/2014/10/updating-our-technical-webmaster));现行 robots 入门也说缺了会让页面更难理解的资源不要屏蔽([robots 入门](https://developers.google.com/search/docs/crawling-indexing/robots/intro))。核对 2026-10-18。
**判据**: 通过=渲染所需 CSS/JS 均可抓。失败=任一渲染所需资源被 Disallow。纯计数类第三方脚本可豁免。
**执行**: 同 crawl-blocked-images 的 GSC 路径;`AUDIT` 不查资源。
**修复**: 放行 /assets/、/static/ 等资源路径;用 GSC 网址检查的实际测试复核渲染结果。
**关联**: crawl-blocked-images;[rendering-seo.md](../rendering-seo.md)

### crawl-pagination-broken
- 源表:fail · 权重 6。`rel="next/prev"` 的 href 解析不出 URL;不请求目标。工具约定。建议优先级 medium。
**依据**: Google 已不用 rel=prev/next([2013 博文图注 "deprecated rel-prev-next"](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical));Google 靠每页 `<a href>` 链到下一页来发现分页([分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading))。本套件因此加查翻页链接断链。核对 2026-10-18。
**判据**: 通过=rel 标记(若有)可解析,且翻页 `<a href>` 目标返回 200。失败=rel href 不可解析,或翻页链接目标 4xx/5xx(本套件口径)。
**执行**: `CRAWL` 后跑 `jq -r '.pages[] | select((.url|test("[?&](../page|p)=[0-9]+|/page/[0-9]+")) and (.status==null or .status>=400)) | "\(.status)\t\(.url)"' crawl.json`;rel 标记用 `curl -s URL | grep -oiE '<link[^>]+rel=.?(next|prev)[^>]*>'`。
**修复**: 恢复分页路由,或把序列截到真实末页;末页不再输出"下一页"。
**关联**: crawl-pagination-loop、crawl-pagination-canonical;[link-architecture-patterns.md](../link-architecture-patterns.md)

### crawl-pagination-loop
- 源表:fail · 权重 6。`rel="next/prev"` 指向本页。工具约定。建议优先级 medium。
**依据**: 同 crawl-pagination-broken:rel 标记只对仍读它的引擎有意义;对 Google 要看翻页 `<a href>` 是否把序列串起来。核对 2026-10-18。
**判据**: 通过=rel next/prev 都不指向本页,翻页链接页码单调递增。失败=rel 指回本页,或"下一页"回到已访问页。
**执行**: `curl -s URL | grep -oiE '<link[^>]+rel=.?(next|prev)[^>]*>'`,href 等于 URL 即失败;翻页环在 `CRAWL` 的 edges 里按页码手工追。
**修复**: 修页码计算(总页数 off-by-one、缓存串页);到末页停止输出 next。
**关联**: crawl-pagination-broken、crawl-pagination-sequence

### crawl-pagination-sequence
- 源表:fail · 权重 5。`rel="next"` 与 `rel="prev"` 指向同一 URL。工具约定。建议优先级 medium。
**依据**: 同上;本套件另查页码跳号与 `?page=`/`/page/` 两种形态混用(本套件口径),后者制造两套并行 URL。核对 2026-10-18。
**判据**: 通过=next≠prev,同系列只用一种分页形态,页码连续。失败=next=prev(源表),或跳号、形态混用(本套件 warn)。
**执行**: 同上 grep 取 next/prev 对比;跳号用 `jq -r '.pages[].url' crawl.json | grep -oE '[?&]page=[0-9]+' | sort -t= -k2 -n | uniq` 看缺口。
**修复**: 该恢复的恢复;已下架的重新连号;统一一种形态并 301 旧形态。
**关联**: crawl-pagination-broken、crawl-pagination-canonical

### crawl-pagination-isolated ⛏
- 源表:fail · 权重 5 · 需 `--crawl`。分页形 URL 没有普通 `<a>` 入链(只在 sitemap、canonical 或 rel 标记里出现)。工具约定。建议优先级 high。
**依据**: Google 建议每页用 `<a href>` 链到下一页,Google 一般只抓 `<a>` 的 href,不点按钮([分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading))。核对 2026-10-18。
**判据**: 通过=分页 URL 至少有一个 `<a href>` 入链。失败=入链为 0(爬取入口豁免)。
**执行**: `jq -r '.pages[] | select((.url|test("[?&](../page|p)=[0-9]+|/page/[0-9]+")) and .inlinks==0) | .url' crawl.json`,有输出即失败。
**修复**: 正文里补可跟随的翻页链接;筛选器泄漏的空壳分页用 noindex/301/canonical 收口。
**关联**: crawl-isolated-url;[link-architecture-patterns.md](../link-architecture-patterns.md)

### crawl-pagination-canonical
- 源表:warn/fail · 权重 10。分页页须自引用 canonical;全部指向第 1 页=错。工具约定(与 Google 一致)。建议优先级 high。
**依据**: "Don't use the first page of a paginated sequence as the canonical page. Instead, give each page its own canonical URL"([分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading));2..N 页 canonical 到第 1 页会让后续页内容不被索引([2013 博文](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical))。核对 2026-10-18。
**判据**: 通过=`?page=2` 的 canonical 就是 `?page=2` 自身。失败=指向第 1 页或其他 URL;全序列指第 1 页取 fail 档。
**执行**: `jq -r '.pages[] | select((.url|test("[?&]page=[0-9]+|/page/[0-9]+")) and .canonical and .canonical!=.url) | "\(.url) -> \(.canonical)"' crawl.json`;单页用 G1。
**修复**: 模板输出"含当前页码的绝对 URL";保留可抓取的翻页锚点链接。
**关联**: crawl-canonical-to-noindex;[redirects-canonical.md](../redirects-canonical.md) 分页深度节

### crawl-sitemap-non-canonical ⛏
- 源表:fail · 权重 7 · 需 `--crawl`。sitemap 内 URL 的 canonical 指向他址;未访问的跳过。工具约定。建议优先级 high。
**依据**: Google 建议 sitemap 只列规范 URL;sitemap 是弱规范化信号,rel=canonical 是强信号,两者给同一页不同答案是 Google 明确反对的做法([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。核对 2026-10-18。
**判据**: 通过=sitemap 内每个 URL 的 canonical 等于自身。失败=任一 URL canonical 指向他址(含参数差异)。
**执行**: `SITEMAP`,桶4「canonical 指向他址」命中即失败。
**修复**: 生成 sitemap 时按"canonical 自引用"过滤;排查 UTM/筛选参数混入。
**关联**: crawl-noindex-in-sitemap、i18n-hreflang-to-non-canonical;[redirects-canonical.md](../redirects-canonical.md)

### crawl-sitemap-disallowed ⛏
- 源表:fail · 权重 7 · 需 `--crawl`。sitemap 内 URL 被 robots.txt Disallow;无 robots 内容且无 Disallow 时报 unmeasured。工具约定。建议优先级 high。
**依据**: 被 Disallow 的页 Google 读不到内容,仍可能凭链接收录成无描述的结果([robots 入门](https://developers.google.com/search/docs/crawling-indexing/robots/intro));Page indexing 报告把它列为 "URL blocked by robots.txt",按 sitemap 筛选可看已提交网页([报告帮助](https://support.google.com/webmasters/answer/7440203))。核对 2026-10-18。
**判据**: 通过=sitemap 内 URL 对 Googlebot 全部可抓。失败=任一 URL 被 Disallow。
**执行**: `SITEMAP`,桶5「robots.txt 屏蔽 (Googlebot)」命中即失败。脚本用 urllib.robotparser(首条匹配、不支持通配),结果与 Google 的最长匹配可能不同,命中项在 GSC 复核。
**修复**: 从 sitemap 删掉该 URL,或收窄 Disallow;修完在 GSC 重交 sitemap。
**关联**: crawl-noindex-in-sitemap、crawl-canonical-to-disallowed;[robots-txt-reference.md](../robots-txt-reference.md)

### crawl-sitemap-non-200 ⛏
- 源表:warn/fail · 权重 10 · 需 `--crawl`。4xx/5xx=fail;3xx 与超时=warn;爬虫未到的 URL 不判。工具约定。建议优先级 high。
**依据**: Google 不索引返回 4xx 的 URL,已索引的会被移除;5xx 让抓取降速,持续则移除([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors));sitemap 应只列想进结果的规范 URL([sitemap 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap))。核对 2026-10-18。
**判据**: 通过=全部 200。警告=3xx 或超时。失败=4xx/5xx。
**执行**: `SITEMAP`,桶1(4xx/5xx/抓取失败)=失败,桶2(3xx)=警告。临时 5xx 先查服务器日志再动手。
**修复**: 4xx 从 sitemap 删除或恢复内容;3xx 改写为终点 URL;5xx 先修稳定性。
**关联**: crawl-sitemap-non-canonical、links-broken-internal;[http-status-codes.md](../http-status-codes.md)

### crawl-sitemap-domain
- 源表:warn/fail · 权重 15。经 index 读出的页面 URL 须在被审 host(www 与非 www 都算);>10% 在他 host=fail,更少=warn;找不到 sitemap=warn。工具约定。建议优先级 medium。
**依据**: sitemaps.org 规定一个 sitemap 内 URL 须与 sitemap 同 host、同协议,无效 URL 被丢弃(只丢那几条,不是整文件作废);跨 host 需在目标站 robots.txt 声明([协议](https://www.sitemaps.org/protocol.html));Google 另允许经 Search Console 验证全部站点后跨站提交([sitemap 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap))。核对 2026-10-18。
**判据**: 通过=全部 URL 同 host(或已按上述方式声明跨站)。失败=出现未声明的外 host URL。
**执行**: sitemap_audit 不查 host。`curl -s 站点/sitemap.xml | grep -oE '<loc>[^<]+' | sed 's#<loc>##' | awk -F/ '{print $3}' | sort | uniq -c`;index 文件对每个子 sitemap 重复一次(.gz 先 `gunzip -c`)。
**修复**: 删掉笔误的外域 URL;确需跨站就在目标站 robots.txt 加 `Sitemap:` 行。
**关联**: crawl-sitemap-in-robotstxt;[robots-txt-reference.md](../robots-txt-reference.md)

### crawl-sitemap-url-limit
- 源表:warn/fail · 权重 6。逐文件:>40,000 URL=warn,>50,000=fail;index 下每个文件单独判。工具约定。建议优先级 medium。
**依据**: "All formats limit a single sitemap to 50MB (uncompressed) or 50,000 URLs ... you must break your sitemap into multiple sitemaps"([sitemap 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap))。40,000 预警线是工具约定。核对 2026-10-18。
**判据**: 通过=每个文件 ≤50,000 条 `<loc>`。失败=任一文件 >50,000。
**执行**: 单文件计数 `curl -s 子sitemapURL | grep -c '<loc>'`(.gz 先 `gunzip -c`)。`SITEMAP` 的规模提示按去重后全部 loc 总数判,index 下多文件会误报,只作粗筛。
**修复**: 拆成多个 ≤50,000 条的文件,用 sitemap index 汇总提交;lastmod 留在各分片。
**关联**: crawl-sitemap-size-limit

### crawl-sitemap-size-limit
- 源表:warn/fail · 权重 5。逐文件按未压缩:>40MB=warn,>50MB=fail。工具约定。建议优先级 medium。
**依据**: 50MB 指解压后体积(52,428,800 字节),gzip 只省带宽不放宽上限([协议](https://www.sitemaps.org/protocol.html));Google 同口径([sitemap 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap))。核对 2026-10-18。
**判据**: 通过=每个文件解压后 ≤50MB。失败=任一文件 >50MB。
**执行**: `SITEMAP` 逐文件解压后判 50MB(规模提示行);单文件 `curl -s URL | gunzip -c | wc -c`(未压缩文件去掉 gunzip)。
**修复**: 先按条数拆分,再 gzip;同步更新 robots.txt 与 GSC 里的引用。
**关联**: crawl-sitemap-url-limit

### crawl-sitemap-duplicate-urls
- 源表:warn · 权重 6。同一 URL 在已取的全部 sitemap 文件里出现 >1 次。工具约定。建议优先级 low。
**依据**: 无搜索引擎专门规定;重复条目说明生成器没去重,还会出现同 URL 两个 lastmod 的矛盾。核对 2026-10-18。
**判据**: 通过=每个 URL 只出现一次。失败=任一 URL ≥2 次。
**执行**: `curl -s sitemapURL | grep -oE '<loc>[^<]+' | sort | uniq -d`;多文件先合并再跑。`SITEMAP` 会静默去重,不报此项。
**修复**: 生成管道加规范化去重;查大小写/尾斜杠变体。
**关联**: crawl-sitemap-cross-duplicates

### crawl-sitemap-cross-duplicates ⛏
- 源表:warn · 权重 2 · 需 `--crawl`。同一 URL 被 ≥2 个 sitemap 文档声明;信息级。工具约定。建议优先级 low。
**依据**: 同上;源表也注明爬虫会自行去重。核对 2026-10-18。
**判据**: 通过=各分片互斥。失败=同一 URL 属 ≥2 个文档。
**执行**: 对每个子 sitemap 取 loc 存成独立文件,`sort -u` 后合并 `sort | uniq -d`。
**修复**: 分片规则按唯一键切分;GSC 只提交 index。
**关联**: crawl-sitemap-duplicate-urls

### crawl-sitemap-orphan-urls ⛏
- 源表:warn · 权重 7 · 需 `--crawl`。sitemap 列出、已爬页面无一链向它。工具约定。建议优先级 medium。
**依据**: 同 crawl-isolated-url:Google 期望在意的页面至少有一个站内链接([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable))。本规则只比 sitemap 与链接集,不做传播判定。核对 2026-10-18。
**判据**: 通过=sitemap 内每个 URL 至少 1 条站内入链。失败=入链为 0。
**执行**: `CRAWL` 后跑 J4;或 `GRAPH --include-sitemap-only` 的入链 0 清单。
**修复**: 有价值的补进导航/相关推荐;无价值的 301 或 410;刻意存档的接受现状。
**关联**: crawl-isolated-url;[link-architecture-patterns.md](../link-architecture-patterns.md)

### crawl-sitemap-in-robotstxt
- 源表:warn · 权重 6。robots.txt 没有 `Sitemap:` 行。工具约定。建议优先级 low。
**依据**: Google、Bing 等主要引擎支持 robots.txt 的 sitemap 字段,可写多条、可跨 host([robots 规范](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec));有 index 时只列 index 即可([协议](https://www.sitemaps.org/protocol.html))。它是后台提交之外的自动发现方式。核对 2026-10-18。
**判据**: 通过=至少一条 `Sitemap: <绝对URL>`。失败=没有。全站确无 sitemap 时先解决有无。
**执行**: `ROBOTS`,`sitemaps` 为空数组即失败。
**修复**: robots.txt 加 `Sitemap: https://example.com/sitemap.xml`(列 index 或每个分片)。
**关联**: crawl-sitemap-url-limit;[robots-txt-reference.md](../robots-txt-reference.md)

### crawl-sitemap-lastmod
- 源表:warn · 权重 5。无任何 lastmod,或非法/未来日期/90% 落在同一天。工具约定。建议优先级 medium。
**依据**: Google 只在 lastmod "consistently and verifiably accurate" 时使用它;priority 与 changefreq 被忽略([sitemap 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap))。lastmod 应是页面最后修改日,不是 sitemap 生成时间([协议](https://www.sitemaps.org/protocol.html))。核对 2026-10-18。
**判据**: 通过=格式合法(W3C Datetime)、不晚于当前、日期有分布。失败=缺失、非法、未来,或集中在同一天(源表 90%)。
**执行**: `SITEMAP` 的「lastmod 三判定」:Coverage(期望 1.0)、Freshness(最新 ≤30 天)、Truthfulness(最大单日簇 >50% 且为今天=疑似构建期伪造);三条阈值均为本套件口径。
**修复**: lastmod 绑定内容真实修改时间(git 提交时间/CMS updated_at),别用构建时间。全量重建且确实同日变更的静态站不适用。
**关联**: crawl-sitemap-date-drift;[validation-guide.md](../validation-guide.md)

### crawl-sitemap-date-drift
- 源表:warn · 权重 4。sitemap lastmod 与页面 schema dateModified 同日。工具约定。建议优先级 low。
**依据**: 无搜索引擎规定;两处日期由同一构建时间戳灌入时,至少一处不真实,会抵消 lastmod 的可用性(见上条 Google 口径)。核对 2026-10-18。
**判据**: 通过=两处日期各自对应真实事件。失败=全站批量同日同步(小站样本少,先抽查)。
**执行**: 抽样对比 `curl -s URL | grep -o '"dateModified" *: *"[^"]*"'` 与 sitemap 中该 URL 的 lastmod。
**修复**: lastmod 与 dateModified 各自绑定真实事件;构建管道别用同一时间戳灌两处。
**关联**: crawl-sitemap-lastmod

### crawl-indexability-conflict
- 源表:warn · 权重 15。Googlebot 组(无则 `*` 组)Disallow 本页即 warn,有无 noindex 都报;读不到 robots.txt=通过。工具约定。建议优先级 high。
**依据**: 被 robots.txt 屏蔽的页上的 noindex Google 读不到,页面仍可能出现在结果里;此时网址检查的「是否允许编入索引」恒显示 Yes([网址检查帮助](https://support.google.com/webmasters/answer/9012289);[noindex 文档](https://developers.google.com/search/docs/crawling-indexing/block-indexing))。Google 不支持在 robots.txt 里写 noindex。核对 2026-10-18。
**判据**: 通过=想退索引的页可抓且带 noindex。失败=页面被 Disallow(带 noindex 时是最典型的双杀)。
**执行**: `AUDIT URL` 出现 `[CRITICAL] ai-bots: Googlebot 被禁`;同时出现 `[CRITICAL] robots: noindex` 即双杀。GSC 网址检查「是否允许抓取」=否可复核。
**修复**: 想退索引:删 Disallow、保留 noindex;想省抓取:等页面完全退索引后再评估 Disallow。
**关联**: crawl-canonical-to-disallowed、core-robots-directive-mismatch;[robots-txt-reference.md](../robots-txt-reference.md)

### crawl-pagination-noindex
- 名称/类型: 分页被 noindex —— warning · 优先级 medium · 输出 WARN(源表 warn;带 rel=next/prev 的页带 noindex)
**这意味(what)**: 分页序列中的某一页被 noindex。
**为什么(why)**: 中段页被 noindex 后,列表深处的商品/文章少了一条被发现的通道。Google 分页文档未要求分页可索引,只建议对筛选/排序变体用 noindex 或 robots.txt([分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading));"分页应可索引"是工具约定。
**触发(trigger)**: 1) 识别分页页;2) meta robots/X-Robots-Tag 含 noindex;3) 即 warn。
**不修的条件(caveat)**: 超长分页尾部 noindex 可作抓取取舍;内站搜索结果的分页本就该屏蔽。
**修复(fix)**: 列表分页移除 noindex;担心薄内容就让每页有独立价值(足够条数+唯一标题)。
**关联(seealso)**: crawl-pagination-canonical;[link-architecture-patterns.md](../link-architecture-patterns.md)

### crawl-pagination-orphaned
- 名称/类型: 分页缺 rel 标记 —— warning · 优先级 low · 输出 WARN(源表 warn;URL 形如 ?page=N、?p=N、/page/N 等却无 rel=next/prev)
**这意味(what)**: 页面 URL 像分页,却没有 rel=next/prev 标记。本套件另查分页系列是否从导航/分类页可达。
**为什么(why)**: Google 已不用 rel=prev/next,对 Google 无影响;源表此项只对仍读该标记的引擎有意义。对 Google 有意义的是系列第 1 页有稳定入口、各页有 `<a href>` 翻页链接([分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading))。
**触发(trigger)**: 1) URL 匹配分页模式;2) 无 rel=next/prev 即 warn(源表)。本套件:系列第 1 页不在导航/分类页可达范围即 warn。
**不修的条件(caveat)**: 只为 Google 优化的站点可不补 rel 标记;低价值存档列表不进导航是抓取取舍。
**修复(fix)**: 分类页/首页给系列第 1 页稳定入口;确认"下一页"是真实可跟随的 `<a href>`。
**关联(seealso)**: crawl-pagination-isolated、links-depth;[link-architecture-patterns.md](../link-architecture-patterns.md)

### crawl-pdf-size
- 名称/类型: 链接 PDF 体积 —— warning · 优先级 low · 输出 WARN(源表 warn;Content-Length **>10MB** 警;HEAD 最多查 **8 个** PDF)
**这意味(what)**: 页面链接的 PDF 传输体积超过 10MB(工具约定)。
**为什么(why)**: 大 PDF 对用户是下载等待;Google 抓 PDF 只取前 64MB([Googlebot 文档](https://developers.google.com/search/docs/crawling-indexing/googlebot)),10MB 线远低于此,它标记的多是未压缩的扫描件。
**触发(trigger)**: 1) 提取 PDF 链接;2) HEAD 取 Content-Length(最多 8 个);3) >10MB 即 warn;4) 无长度跳过;5) 无 PDF 链接通过。
**不修的条件(caveat)**: 需要原始分辨率的图纸/画册,可另出压缩版供在线阅读。
**修复(fix)**: 扫描件重压缩+OCR;降图片分辨率;超大的按章节拆分;正文改用 HTML 承载。
**关联(seealso)**: crawl-sitemap-non-200;[log-analysis.md](../log-analysis.md)

### crawl-crawl-delay
- 名称/类型: crawl-delay 指令 —— warning · 优先级 low · 输出 WARN(源表现行:`*`、Googlebot 或 Bingbot 组 Crawl-delay >10 秒=warn;旧快照为 info)
**这意味(what)**: robots.txt 用 Crawl-delay 限制抓取间隔。
**为什么(why)**: Google 不支持 crawl-delay([robots 规范](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec));Yandex 自 2018-02-22 起也不再理会,改用 Yandex Webmaster 的抓取速度设置([Yandex 帮助](https://yandex.com/support/webmaster/en/robot-workings/crawl-delay));Bing 支持,且 robots.txt 的值优先于 Bing Webmaster 的 Crawl Control([Bing 帮助](https://www.bing.com/webmasters/help/crawl-control-55a30303))。大值会压低 Bing 的日抓取量。
**触发(trigger)**: `ROBOTS` 的 `crawl_delay` 字段(取 `*` 组)非空即报;源表只对 >10 秒扣分。
**不修的条件(caveat)**: 被爬虫打挂的小站给 Bing 设 crawl-delay 是正当取舍;它对 Googlebot 无效。
**修复(fix)**: Google 侧降速用服务器短期返回 500/503/429(GSC 抓取频率工具已于 2024-01-08 下线,[公告](https://developers.google.com/search/blog/2023/11/sc-crawl-limiter-byebye)),见 [http-status-codes.md](../http-status-codes.md);保留 crawl-delay 时写明数值与目的。
**关联(seealso)**: crawl-sitemap-in-robotstxt;[robots-txt-reference.md](../robots-txt-reference.md)、[log-analysis.md](../log-analysis.md)
