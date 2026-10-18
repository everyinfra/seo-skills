# 审计规则全目录(SEOmator 373 规则,源码深读)

> 来源:SEOmator 开源审计器 [seo-skills/seo-audit-skill](https://github.com/seo-skills/seo-audit-skill) 的 `docs/SEO-AUDIT-RULES.md`。2026-10-09 吸收的是 e047a5e2(2026-09-22)快照。上游 2026-10-15 在 132d2384 按代码重写了该文档,多条规则的语义与严重度变了。**第一波 P0/P1 的 79 条已按 132d2384 复核(核对 2026-10-18);其余表格与条目仍是 09-22 快照,与现行版冲突时以现行版为准。**
> 三态计分:Pass=100 / Warn=50 / Fail=0;总分=类别加权平均。现行档位 **90-100=A / 80-89=B / 70-79=C / 50-69=D / <50=F**;单页审计另有封顶(noindex 或 robots.txt 屏蔽封 20,无 title 封 69 等)。
> **20 类权重表已吸收于 [scoring-rubric.md](scoring-rubric.md)「完全装载」节,不重抄**(Core 11%/Perf 10%/Links·Images·Security 各 8%/Tech·A11y 各 7%/Crawl·SD·Content·JS 各 5%/Social·E-E-A-T·URL·Redirects 各 3%/Mobile·i18n·HTMLval·AI-GEO 各 2%/Legal 1%)。
> **严重度与阈值是 SEOmator 的工具约定,不是搜索引擎规则。** 搜索引擎的一手说法写在各条「依据」里;没有官方出处的写"无官方出处"。
> 三类横切机制先记住,后面表格反复引用:
> - **crawl 模式专属**(`--crawl`):依赖多页爬取的跨页状态;单页审计时报 not measured(权重 0 不计分)。现行 17 条,表内标 ⛏。
> - **渲染专属**(`--no-cwv` 时跳过):带"requires render"标记的 per-asset 规则,数据来自 Playwright 渲染。
> - **TOML 开关**:`[rules] disable=["core-*"]` 按前缀禁类;`enable=["core-*","perf-*"]+disable=["*"]` 只留指定类。

---

## 〇、解释层规范与执行速查

> 结构与文案纪律来自 [borrow-specs.md](../research/borrow-specs.md) A2 节。**各节表格仍是全量索引,永不删行**。解释层覆盖 220 条,分批见文末第六节。

- **P0/P1 执行版(第一波 79 条)**:规则 ID 标题 + 「源表」行(现行严重度·权重·判定;工具约定;建议优先级)+ 依据 / 判据 / 执行 / 修复 / 关联 五段。依据只写一手来源并附链接;判据写通过/失败;执行写 site_audit 对应的输出行或替代命令。
- **其余条目(八段式)**:what/why/trigger/caveat/fix/seealso。原「导出(export)」字段的 `Reports > …` 路径在 SEOmator 文档中不存在,本套件也无法执行,已全部删除。
- **两轴哲学**:类型(issue|warning|opportunity)× 优先级(critical|high|medium|low|insight)独立打分。Opportunity 永不给 critical;"坏信号>缺信号":主动矛盾排 critical-high,单纯缺失排 medium-low。个别"缺信号但源表 fail"的规则(canonical 缺失、title 缺失)输出 CRITICAL、建议优先级降档,条目内注明。
- **ID 纪律**:第一波条目标题用源表现行 ID。第四节其余标 [待核 ID] 的是本套件按家族起的名字,不是源表 ID。阈值照抄源表,源表未公布的写"未公布",不发明新阈值。
- **caveat 常驻样本**:title 长度高度主观(Google 无上限,按设备宽度截断,且常自行改写 title link);站内重复内容不违反 Google 垃圾政策,影响在规范页选择与抓取效率;缺 alt 只是错失描述,**装饰图空 alt 是正确做法**。

**执行速查**(在 skill 根目录运行;`URL`、`站点` 换成实际值):

| 简写 | 命令 | 用途与限制 |
|---|---|---|
| `AUDIT` | `python3 scripts/site_audit.py URL [--market xx] [--json] [--export-dir DIR]` | 单页;输出 `[级别] area: 消息`;有 CRITICAL 退出码 1。不跨页、不渲染、只读第一个/最后一个 meta robots,不识别 `none` 与 googlebot meta |
| `SITEMAP` | `python3 scripts/sitemap_audit.py 站点 --check-limit 0` | 六坏桶:1 非200/2 3xx/3 noindex/4 canonical 他指/5 robots 屏蔽/6 参数重复 + lastmod 三判定;默认只逐条查前 50 条 |
| `HREFLANG` | `python3 scripts/hreflang_cluster.py URL1 URL2 …` | 簇矩阵:自引用/语言码/绝对URL/HTTP200/双向回报 + 三载体冲突;跟随重定向 |
| `REDIR` | `python3 scripts/redirect_chain.py URL [--max N]` | 逐跳;>2 跳 WARN,>5 跳或环 CRITICAL;临时码用于永久变化 WARN;打印「终态: HTTP」 |
| `CRAWL` | `python3 scripts/site_crawl.py 站点 --max N --out crawl.json` | `pages[]` 含 url/status/final_url/canonical/depth/inlinks/source,另有 `edges`、`orphans`;N 要覆盖全站,截断时入链偏少 |
| `GRAPH` | `python3 scripts/link_graph.py --crawl crawl.json` | 深度直方图(>3 层占比)、入链 0/1 清单、锚文本审计 |
| `ROBOTS` | `python3 scripts/robots_posture.py 站点/robots.txt --json` | 含 `crawl_delay`(`*` 组)与 `sitemaps` 字段 |
| `GSC 网址检查` | Search Console → 网址检查 | 「是否允许抓取 / 是否允许编入索引 / 用户声明与 Google 选择的规范网址」;「查看已抓取的网页 → 更多信息」列出资源 |

jq/grep 片段(`crawl.json` 来自 `CRAWL`;已用样例数据实测):
- **J1 canonical 链**:`jq -r '(.pages|map({(.url):.canonical})|add) as $c | .pages[] | select(.canonical and .canonical!=.url) | select($c[.canonical] and $c[.canonical]!=.canonical and $c[.canonical]!=.url) | "\(.url) -> \(.canonical) -> \($c[.canonical])"' crawl.json`
- **J2 canonical 环**:`jq -r '(.pages|map({(.url):.canonical})|add) as $c | .pages[] | select(.canonical and .canonical!=.url and $c[.canonical]==.url) | "\(.url) <-> \(.canonical)"' crawl.json`
- **J3 canonical 目标非 200 或重定向**:`jq -r '(.pages|map({(.url):.})|add) as $p | .pages[] | select(.canonical and .canonical!=.url and $p[.canonical]) | $p[.canonical] as $t | select($t.status!=200 or $t.final_url) | "\(.url) -> \(.canonical) status=\($t.status) final=\($t.final_url)"' crawl.json`
- **J4 sitemap 孤儿**:`jq -r '.pages[] | select(.source=="sitemap" and .inlinks==0) | .url' crawl.json`
- **J5 深度 >3**:`jq -r '.pages[] | select(.depth != null and .depth > 3) | "\(.depth)\t\(.url)"' crawl.json`
- **J6 死内链来源**:`jq -r '(.pages|map(select(.status==null or .status>=400)|.url)) as $bad | .edges[] | select(.dst as $d | $bad|index($d)) | "\(.src) -> \(.dst)"' crawl.json`
- **J7 内链指向重定向**:`jq -r '(.pages|map(select(.final_url)|{(.url):.final_url})|add // {}) as $r | .edges[] | select($r[.dst]) | "\(.src) -> \(.dst) => \($r[.dst])"' crawl.json`
- **J8 重复 title**:`jq -r '.pages[] | .title // empty | ascii_downcase | gsub("^\\s+|\\s+$";"")' crawl.json | sort | uniq -c | awk '$1>1'`
- **G1 canonical 标签**:`curl -s URL | grep -oiE '<link[^>]+rel=.?canonical[^>]*>'`(加 `| wc -l` 计数)
- **G2 head 外的 canonical**:`curl -s URL | tr -d '\n' | grep -oiE '</head>.*' | grep -oiE '<link[^>]+rel=.?canonical[^>]*>'`
- **G3 Link 头 canonical**:`curl -sI URL | grep -i '^link:.*canonical'`
- **G4 相对 hreflang**:`curl -s URL | grep -oiE '<link[^>]+hreflang=[^>]*>' | grep -ivE 'href=.?https?://'`
- **G5 开发环境链接**:`curl -s URL | grep -oiE 'href=.?(https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)|file:)[^ >]*'`
- **G6 索引指令**:`curl -s URL | grep -oiE '<meta[^>]+name=.?(robots|googlebot)[^>]*>'; curl -sI URL | grep -i '^x-robots-tag'`
- **G7 hreflang 清单**:`curl -s URL | grep -oiE '<link[^>]+hreflang=[^>]*>'`

---

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
**关联**: core-canonical-to-noindex、crawl-hreflang-to-noindex;[redirects-canonical.md](redirects-canonical.md)

### crawl-canonical-to-disallowed ⛏
- 源表:fail · 权重 8 · 需 `--crawl`。canonical 目标被 robots.txt Disallow。工具约定。建议优先级 critical。
**依据**: Google 读不到被 Disallow 页的内容,只可能凭外链收录 URL([robots 规范](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec));canonical 目标应是存在的正常页([2013 博文](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical))。合并结果未公开。核对 2026-10-18。
**判据**: 通过=目标对 Googlebot 可抓。失败=目标被 Googlebot 组(无则 `*` 组)Disallow。
**执行**: `AUDIT 目标URL` 出现 `[CRITICAL] ai-bots: Googlebot 被禁` 即失败。site_audit 按最长前缀匹配,不支持 `*`/`$` 通配,且路径按小写比;有通配规则时用 GSC 网址检查「是否允许抓取(Crawl allowed?)」复核。
**修复**: 要合并就从 robots.txt 放行该路径,索引控制改用 noindex;不要合并就把 canonical 改自引用。
**关联**: crawl-indexability-conflict、crawl-canonical-to-noindex;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-canonical-loop ⛏
- 源表:fail · 权重 8 · 需 `--crawl`。跟踪 canonical 回到已访问 URL。工具约定。建议优先级 high。
**依据**: Google 文档未专门谈 canonical 环;canonical 只是提示,Google 可另选规范页([规范化文档](https://developers.google.com/search/docs/crawling-indexing/canonicalization))。环让你的提示没有终点。核对 2026-10-18。
**判据**: 通过=链终止于自引用页。失败=链回到起点或任一途经 URL。
**执行**: `CRAWL` 后跑 J2,有输出即失败(只覆盖已爬页面);单页手工:G1 读出目标,再对目标跑 G1,看是否指回。
**修复**: 选定终点页让它自引用,其余页直指它;查模板是否把参数写进 canonical。
**关联**: core-canonical-loop、crawl-canonical-chain;[redirects-canonical.md](redirects-canonical.md)

### crawl-canonical-chain ⛏
- 源表:warn · 权重 6 · 需 `--crawl`。canonical 目标自身又 canonical 到第三页(A→B→C)。工具约定。建议优先级 medium。
**依据**: Google 要求规范页本身带自引用 canonical([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls));链说明 B 不是规范页。"每跳衰减"无官方出处,不作理由。核对 2026-10-18。
**判据**: 通过=目标自引用或无 canonical。失败=目标 canonical 指向第三个 URL。
**执行**: `CRAWL` 后跑 J1,每行一条链。
**修复**: 前驱页全部直指链终点;确认终点 200 且自引用。
**关联**: crawl-canonical-redirect、crawl-canonical-loop;[redirects-canonical.md](redirects-canonical.md)

### crawl-canonical-redirect
- 源表:warn/fail · 权重 15。canonical 目标重定向 1-2 跳=warn,≥3 跳或目标 4xx/5xx=fail;无 canonical=warn。工具约定。建议优先级 high。
**依据**: Google 要求 canonical 目标真实存在,不是错误页或 soft 404([2013 博文](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical))。"必须直指最终 URL"是工具约定,Google 文档无此句。核对 2026-10-18。
**判据**: 通过=目标直接返回 200。警告=目标 1-2 跳后 200。失败=≥3 跳或终点 4xx/5xx。
**执行**: `REDIR 目标URL`,看「链长」与「终态: HTTP」两行;已爬全站用 J3。
**修复**: canonical 改写为重定向链终点 URL,并确认它 200 且自引用。
**关联**: crawl-canonical-chain、links-redirect-chains;[redirects-canonical.md](redirects-canonical.md)

### crawl-canonical-form-drift ⛏
- 源表:warn · 权重 6 · 需 `--crawl` 且 ≥2 页。各页 canonical 在 www/协议/尾斜杠上不一致。工具约定。建议优先级 low。
**依据**: Google 默认优先 HTTPS 页作规范页,HTTPS 页 canonical 指 HTTP 版会削弱这一偏好;Google 建议站内统一链向规范 URL([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。核对 2026-10-18。
**判据**: 通过=全站 canonical 只有一种协议+host+尾斜杠策略。失败=出现少数派形态(混用 http 最重)。
**执行**: `jq -r '.pages[].canonical // empty' crawl.json | sed -E 's#^(https?://[^/]+).*#\1#' | sort | uniq -c`;输出多于一行即漂移。尾斜杠另用 `grep -c '/$'` 比对。
**修复**: 定一种规范形态,模板统一输出;其余形态 301 到规范形。
**关联**: core-canonical-http-mismatch;[redirects-canonical.md](redirects-canonical.md)

### crawl-hreflang-to-noindex ⛏
- 源表:fail · 权重 8 · 需 `--crawl`。出向 hreflang 的已爬目标 noindex。工具约定。建议优先级 high。
**依据**: Google 只处理互相指向的一对注解;没互指的那一对被忽略,其余互指的照常处理,不是整簇作废([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。noindex 页不会出现在结果里,这一格语言版等于空缺。核对 2026-10-18。
**判据**: 通过=全部目标可索引。失败=任一目标的 meta robots/googlebot 或 X-Robots-Tag 含 noindex/none。
**执行**: `HREFLANG 簇内全部URL` 列出目标;对每个目标跑 `AUDIT`,出现 `[CRITICAL] robots: noindex` 即失败。
**修复**: 要该语言版就删 noindex;不要就从 HTML/HTTP 头/sitemap 三种载体里一并删掉该成员。
**关联**: i18n-hreflang-to-noindex、crawl-canonical-to-noindex;[hreflang-validation.md](hreflang-validation.md)

### crawl-hreflang-to-disallowed ⛏
- 源表:fail · 权重 7 · 需 `--crawl`。出向 hreflang 指向被 robots.txt 禁的页。工具约定。建议优先级 high。
**依据**: 推论:被 Disallow 的页 Google 读不到([robots 规范](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec)),也就看不到它的回链;没互指的那一对注解被忽略([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。核对 2026-10-18。
**判据**: 通过=全部目标对 Googlebot 可抓。失败=任一目标被 Disallow。
**执行**: 对每个 hreflang 目标跑 `AUDIT`,出现 `[CRITICAL] ai-bots: Googlebot 被禁` 即失败;通配规则用 GSC「是否允许抓取」复核。
**修复**: 放行该语言版,索引控制改用 noindex/canonical;或从注解集删掉该成员。
**关联**: crawl-canonical-to-disallowed、crawl-hreflang-disallowed-target;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-hreflang-disallowed-target ⛏
- 源表:fail · 权重 7 · 需 `--crawl`。本页被 Disallow,他页 hreflang 却指向本页。工具约定。建议优先级 high。
**依据**: 同上一条的镜像方向:本页的回链 Google 永远读不到,指向本页的那几对注解被忽略。核对 2026-10-18。
**判据**: 通过=本页可抓,或无人指向本页。失败=本页被 Disallow 且有入向 hreflang。
**执行**: `AUDIT 本页URL` 出现 `[CRITICAL] ai-bots: Googlebot 被禁`;再用 `HREFLANG` 跑引用方,看谁列了本页。
**修复**: 本页本就不该抓时,删掉引用方的注解(HTML/HTTP 头/sitemap);否则放行本页。
**关联**: crawl-hreflang-to-disallowed、crawl-hreflang-reciprocity;[hreflang-validation.md](hreflang-validation.md)

### crawl-hreflang-incoming-conflict ⛏
- 源表:fail · 权重 7 · 需 `--crawl`。他页给本页标了不同语言码;本页自己的注解不计,x-default 不算冲突。工具约定。建议优先级 high。
**依据**: Google 要求每个语言版列出同一套链接(含自己),各版本的集合一致([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。同一 URL 被标两种码,说明各页集合不一致。核对 2026-10-18。
**判据**: 通过=所有入向注解对本页用同一个码。失败=出现 ≥2 个不同码(x-default 除外)。
**执行**: `HREFLANG 簇内全部URL`,在矩阵里对比各行给本 URL 的码;站外引用方用 G7 逐页抓。
**修复**: 找到写错的引用方改码;双语页拆成两个 URL。
**关联**: i18n-hreflang-conflicting、i18n-hreflang-incoming-invalid;[hreflang-validation.md](hreflang-validation.md)

### crawl-hreflang-reciprocity ⛏
- 源表:warn · 权重 6 · 需 `--crawl`。已爬目标没有反向标注本页;未爬到的目标跳过。工具约定。建议优先级 high。
**依据**: "If two pages don't both point to each other, the tags will be ignored";可以在部分页省略部分语言,互指的仍会处理([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。核对 2026-10-18。
**判据**: 通过=每个目标都含"指向本页且码对应"的条目。失败=任一目标缺该条目。
**执行**: `HREFLANG 簇内全部URL`,「双向回报」列出现 ✗ 即失败(脚本退出码 1)。
**修复**: 双向成对生成,优先在 sitemap 载体集中维护;修完重跑 `HREFLANG`。
**关联**: i18n-hreflang-return-links;[hreflang-validation.md](hreflang-validation.md)

### crawl-isolated-url ⛏
- 源表:fail · 权重 8 · 需 `--crawl`。只经 canonical/重定向/sitemap 发现,无锚点入链;链接者全是 noindex,follow 或自身孤立也算(一次传播);爬取入口必过。工具约定。建议优先级 high。
**依据**: Google 主要靠已抓页面上的链接发现新页([SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide));"每个你在意的页面至少要有一个站内页面链向它"([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable))。核对 2026-10-18。
**判据**: 通过=至少一个可索引页用 `<a href>` 链向它。失败=零锚点入链(传播判定见上)。
**执行**: `CRAWL` 后看 `orphans`(0 入链且非首页),或 `GRAPH` 的入链 0/1 清单;一次传播与 noindex 链接者不在脚本内,需人工复核。`--max` 截断时入链偏少,先确认未截断。
**修复**: 从相关正文页加描述性锚文本内链;该删的页 301 到最近亲页。
**关联**: crawl-sitemap-orphan-urls、links-depth;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-schema-noindex-conflict
- 源表:fail · 权重 15。noindex 页上有富结果类 schema。工具约定。建议优先级 medium。
**依据**: noindex 的页不会出现在搜索结果中([robots meta 规范](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)),其上的富结果标记没有展示机会。这是浪费与治理问题,不是惩罚。核对 2026-10-18。
**判据**: 通过=页面可索引,或只含 Organization/WebSite 等全站标记。失败=noindex 页含 Product/Recipe/Review 等富结果类型。
**执行**: `AUDIT URL` 同时出现 `[CRITICAL] robots: noindex`,且 `curl -s URL | grep -o '"@type" *: *"[^"]*"'` 列出富结果类型。
**修复**: 页面要索引就删 noindex;不要就删该页富结果 schema。预发布页可暂留。
**关联**: crawl-noindex-in-sitemap;[validation-guide.md](validation-guide.md)

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
**关联**: crawl-blocked-resources;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-blocked-resources
- 源表:warn · 权重 7。robots.txt Disallow 挡住 CSS/JS。工具约定。建议优先级 high。
**依据**: Google 2014-10-27 起要求放行 JS/CSS:"Disallowing crawling of Javascript or CSS files ... directly harms how well our algorithms render and index your content"([博文](https://developers.google.com/search/blog/2014/10/updating-our-technical-webmaster));现行 robots 入门也说缺了会让页面更难理解的资源不要屏蔽([robots 入门](https://developers.google.com/search/docs/crawling-indexing/robots/intro))。核对 2026-10-18。
**判据**: 通过=渲染所需 CSS/JS 均可抓。失败=任一渲染所需资源被 Disallow。纯计数类第三方脚本可豁免。
**执行**: 同 crawl-blocked-images 的 GSC 路径;`AUDIT` 不查资源。
**修复**: 放行 /assets/、/static/ 等资源路径;用 GSC 网址检查的实际测试复核渲染结果。
**关联**: crawl-blocked-images;[rendering-seo.md](rendering-seo.md)

### crawl-pagination-broken
- 源表:fail · 权重 6。`rel="next/prev"` 的 href 解析不出 URL;不请求目标。工具约定。建议优先级 medium。
**依据**: Google 已不用 rel=prev/next([2013 博文图注 "deprecated rel-prev-next"](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical));Google 靠每页 `<a href>` 链到下一页来发现分页([分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading))。本套件因此加查翻页链接断链。核对 2026-10-18。
**判据**: 通过=rel 标记(若有)可解析,且翻页 `<a href>` 目标返回 200。失败=rel href 不可解析,或翻页链接目标 4xx/5xx(本套件口径)。
**执行**: `CRAWL` 后跑 `jq -r '.pages[] | select((.url|test("[?&](page|p)=[0-9]+|/page/[0-9]+")) and (.status==null or .status>=400)) | "\(.status)\t\(.url)"' crawl.json`;rel 标记用 `curl -s URL | grep -oiE '<link[^>]+rel=.?(next|prev)[^>]*>'`。
**修复**: 恢复分页路由,或把序列截到真实末页;末页不再输出"下一页"。
**关联**: crawl-pagination-loop、crawl-pagination-canonical;[link-architecture-patterns.md](link-architecture-patterns.md)

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
**执行**: `jq -r '.pages[] | select((.url|test("[?&](page|p)=[0-9]+|/page/[0-9]+")) and .inlinks==0) | .url' crawl.json`,有输出即失败。
**修复**: 正文里补可跟随的翻页链接;筛选器泄漏的空壳分页用 noindex/301/canonical 收口。
**关联**: crawl-isolated-url;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-pagination-canonical
- 源表:warn/fail · 权重 10。分页页须自引用 canonical;全部指向第 1 页=错。工具约定(与 Google 一致)。建议优先级 high。
**依据**: "Don't use the first page of a paginated sequence as the canonical page. Instead, give each page its own canonical URL"([分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading));2..N 页 canonical 到第 1 页会让后续页内容不被索引([2013 博文](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical))。核对 2026-10-18。
**判据**: 通过=`?page=2` 的 canonical 就是 `?page=2` 自身。失败=指向第 1 页或其他 URL;全序列指第 1 页取 fail 档。
**执行**: `jq -r '.pages[] | select((.url|test("[?&]page=[0-9]+|/page/[0-9]+")) and .canonical and .canonical!=.url) | "\(.url) -> \(.canonical)"' crawl.json`;单页用 G1。
**修复**: 模板输出"含当前页码的绝对 URL";保留可抓取的翻页锚点链接。
**关联**: crawl-canonical-to-noindex;[redirects-canonical.md](redirects-canonical.md) 分页深度节

### crawl-sitemap-non-canonical ⛏
- 源表:fail · 权重 7 · 需 `--crawl`。sitemap 内 URL 的 canonical 指向他址;未访问的跳过。工具约定。建议优先级 high。
**依据**: Google 建议 sitemap 只列规范 URL;sitemap 是弱规范化信号,rel=canonical 是强信号,两者给同一页不同答案是 Google 明确反对的做法([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。核对 2026-10-18。
**判据**: 通过=sitemap 内每个 URL 的 canonical 等于自身。失败=任一 URL canonical 指向他址(含参数差异)。
**执行**: `SITEMAP`,桶4「canonical 指向他址」命中即失败。
**修复**: 生成 sitemap 时按"canonical 自引用"过滤;排查 UTM/筛选参数混入。
**关联**: crawl-noindex-in-sitemap、i18n-hreflang-to-non-canonical;[redirects-canonical.md](redirects-canonical.md)

### crawl-sitemap-disallowed ⛏
- 源表:fail · 权重 7 · 需 `--crawl`。sitemap 内 URL 被 robots.txt Disallow;无 robots 内容且无 Disallow 时报 unmeasured。工具约定。建议优先级 high。
**依据**: 被 Disallow 的页 Google 读不到内容,仍可能凭链接收录成无描述的结果([robots 入门](https://developers.google.com/search/docs/crawling-indexing/robots/intro));Page indexing 报告把它列为 "URL blocked by robots.txt",按 sitemap 筛选可看已提交网页([报告帮助](https://support.google.com/webmasters/answer/7440203))。核对 2026-10-18。
**判据**: 通过=sitemap 内 URL 对 Googlebot 全部可抓。失败=任一 URL 被 Disallow。
**执行**: `SITEMAP`,桶5「robots.txt 屏蔽 (Googlebot)」命中即失败。脚本用 urllib.robotparser(首条匹配、不支持通配),结果与 Google 的最长匹配可能不同,命中项在 GSC 复核。
**修复**: 从 sitemap 删掉该 URL,或收窄 Disallow;修完在 GSC 重交 sitemap。
**关联**: crawl-noindex-in-sitemap、crawl-canonical-to-disallowed;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-sitemap-non-200 ⛏
- 源表:warn/fail · 权重 10 · 需 `--crawl`。4xx/5xx=fail;3xx 与超时=warn;爬虫未到的 URL 不判。工具约定。建议优先级 high。
**依据**: Google 不索引返回 4xx 的 URL,已索引的会被移除;5xx 让抓取降速,持续则移除([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors));sitemap 应只列想进结果的规范 URL([sitemap 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap))。核对 2026-10-18。
**判据**: 通过=全部 200。警告=3xx 或超时。失败=4xx/5xx。
**执行**: `SITEMAP`,桶1(4xx/5xx/抓取失败)=失败,桶2(3xx)=警告。临时 5xx 先查服务器日志再动手。
**修复**: 4xx 从 sitemap 删除或恢复内容;3xx 改写为终点 URL;5xx 先修稳定性。
**关联**: crawl-sitemap-non-canonical、links-broken-internal;[http-status-codes.md](http-status-codes.md)

### crawl-sitemap-domain
- 源表:warn/fail · 权重 15。经 index 读出的页面 URL 须在被审 host(www 与非 www 都算);>10% 在他 host=fail,更少=warn;找不到 sitemap=warn。工具约定。建议优先级 medium。
**依据**: sitemaps.org 规定一个 sitemap 内 URL 须与 sitemap 同 host、同协议,无效 URL 被丢弃(只丢那几条,不是整文件作废);跨 host 需在目标站 robots.txt 声明([协议](https://www.sitemaps.org/protocol.html));Google 另允许经 Search Console 验证全部站点后跨站提交([sitemap 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap))。核对 2026-10-18。
**判据**: 通过=全部 URL 同 host(或已按上述方式声明跨站)。失败=出现未声明的外 host URL。
**执行**: sitemap_audit 不查 host。`curl -s 站点/sitemap.xml | grep -oE '<loc>[^<]+' | sed 's#<loc>##' | awk -F/ '{print $3}' | sort | uniq -c`;index 文件对每个子 sitemap 重复一次(.gz 先 `gunzip -c`)。
**修复**: 删掉笔误的外域 URL;确需跨站就在目标站 robots.txt 加 `Sitemap:` 行。
**关联**: crawl-sitemap-in-robotstxt;[robots-txt-reference.md](robots-txt-reference.md)

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
**关联**: crawl-isolated-url;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-sitemap-in-robotstxt
- 源表:warn · 权重 6。robots.txt 没有 `Sitemap:` 行。工具约定。建议优先级 low。
**依据**: Google、Bing 等主要引擎支持 robots.txt 的 sitemap 字段,可写多条、可跨 host([robots 规范](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec));有 index 时只列 index 即可([协议](https://www.sitemaps.org/protocol.html))。它是后台提交之外的自动发现方式。核对 2026-10-18。
**判据**: 通过=至少一条 `Sitemap: <绝对URL>`。失败=没有。全站确无 sitemap 时先解决有无。
**执行**: `ROBOTS`,`sitemaps` 为空数组即失败。
**修复**: robots.txt 加 `Sitemap: https://example.com/sitemap.xml`(列 index 或每个分片)。
**关联**: crawl-sitemap-url-limit;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-sitemap-lastmod
- 源表:warn · 权重 5。无任何 lastmod,或非法/未来日期/90% 落在同一天。工具约定。建议优先级 medium。
**依据**: Google 只在 lastmod "consistently and verifiably accurate" 时使用它;priority 与 changefreq 被忽略([sitemap 文档](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap))。lastmod 应是页面最后修改日,不是 sitemap 生成时间([协议](https://www.sitemaps.org/protocol.html))。核对 2026-10-18。
**判据**: 通过=格式合法(W3C Datetime)、不晚于当前、日期有分布。失败=缺失、非法、未来,或集中在同一天(源表 90%)。
**执行**: `SITEMAP` 的「lastmod 三判定」:Coverage(期望 1.0)、Freshness(最新 ≤30 天)、Truthfulness(最大单日簇 >50% 且为今天=疑似构建期伪造);三条阈值均为本套件口径。
**修复**: lastmod 绑定内容真实修改时间(git 提交时间/CMS updated_at),别用构建时间。全量重建且确实同日变更的静态站不适用。
**关联**: crawl-sitemap-date-drift;[validation-guide.md](validation-guide.md)

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
**关联**: crawl-canonical-to-disallowed、core-robots-directive-mismatch;[robots-txt-reference.md](robots-txt-reference.md)

### crawl-pagination-noindex
- 名称/类型: 分页被 noindex —— warning · 优先级 medium · 输出 WARN(源表 warn;带 rel=next/prev 的页带 noindex)
**这意味(what)**: 分页序列中的某一页被 noindex。
**为什么(why)**: 中段页被 noindex 后,列表深处的商品/文章少了一条被发现的通道。Google 分页文档未要求分页可索引,只建议对筛选/排序变体用 noindex 或 robots.txt([分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading));"分页应可索引"是工具约定。
**触发(trigger)**: 1) 识别分页页;2) meta robots/X-Robots-Tag 含 noindex;3) 即 warn。
**不修的条件(caveat)**: 超长分页尾部 noindex 可作抓取取舍;内站搜索结果的分页本就该屏蔽。
**修复(fix)**: 列表分页移除 noindex;担心薄内容就让每页有独立价值(足够条数+唯一标题)。
**关联(seealso)**: crawl-pagination-canonical;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-pagination-orphaned
- 名称/类型: 分页缺 rel 标记 —— warning · 优先级 low · 输出 WARN(源表 warn;URL 形如 ?page=N、?p=N、/page/N 等却无 rel=next/prev)
**这意味(what)**: 页面 URL 像分页,却没有 rel=next/prev 标记。本套件另查分页系列是否从导航/分类页可达。
**为什么(why)**: Google 已不用 rel=prev/next,对 Google 无影响;源表此项只对仍读该标记的引擎有意义。对 Google 有意义的是系列第 1 页有稳定入口、各页有 `<a href>` 翻页链接([分页文档](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading))。
**触发(trigger)**: 1) URL 匹配分页模式;2) 无 rel=next/prev 即 warn(源表)。本套件:系列第 1 页不在导航/分类页可达范围即 warn。
**不修的条件(caveat)**: 只为 Google 优化的站点可不补 rel 标记;低价值存档列表不进导航是抓取取舍。
**修复(fix)**: 分类页/首页给系列第 1 页稳定入口;确认"下一页"是真实可跟随的 `<a href>`。
**关联(seealso)**: crawl-pagination-isolated、links-depth;[link-architecture-patterns.md](link-architecture-patterns.md)

### crawl-pdf-size
- 名称/类型: 链接 PDF 体积 —— warning · 优先级 low · 输出 WARN(源表 warn;Content-Length **>10MB** 警;HEAD 最多查 **8 个** PDF)
**这意味(what)**: 页面链接的 PDF 传输体积超过 10MB(工具约定)。
**为什么(why)**: 大 PDF 对用户是下载等待;Google 抓 PDF 只取前 64MB([Googlebot 文档](https://developers.google.com/search/docs/crawling-indexing/googlebot)),10MB 线远低于此,它标记的多是未压缩的扫描件。
**触发(trigger)**: 1) 提取 PDF 链接;2) HEAD 取 Content-Length(最多 8 个);3) >10MB 即 warn;4) 无长度跳过;5) 无 PDF 链接通过。
**不修的条件(caveat)**: 需要原始分辨率的图纸/画册,可另出压缩版供在线阅读。
**修复(fix)**: 扫描件重压缩+OCR;降图片分辨率;超大的按章节拆分;正文改用 HTML 承载。
**关联(seealso)**: crawl-sitemap-non-200;[log-analysis.md](log-analysis.md)

### crawl-crawl-delay
- 名称/类型: crawl-delay 指令 —— warning · 优先级 low · 输出 WARN(源表现行:`*`、Googlebot 或 Bingbot 组 Crawl-delay >10 秒=warn;旧快照为 info)
**这意味(what)**: robots.txt 用 Crawl-delay 限制抓取间隔。
**为什么(why)**: Google 不支持 crawl-delay([robots 规范](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec));Yandex 自 2018-02-22 起也不再理会,改用 Yandex Webmaster 的抓取速度设置([Yandex 帮助](https://yandex.com/support/webmaster/en/robot-workings/crawl-delay));Bing 支持,且 robots.txt 的值优先于 Bing Webmaster 的 Crawl Control([Bing 帮助](https://www.bing.com/webmasters/help/crawl-control-55a30303))。大值会压低 Bing 的日抓取量。
**触发(trigger)**: `ROBOTS` 的 `crawl_delay` 字段(取 `*` 组)非空即报;源表只对 >10 秒扣分。
**不修的条件(caveat)**: 被爬虫打挂的小站给 Bing 设 crawl-delay 是正当取舍;它对 Googlebot 无效。
**修复(fix)**: Google 侧降速用服务器短期返回 500/503/429(GSC 抓取频率工具已于 2024-01-08 下线,[公告](https://developers.google.com/search/blog/2023/11/sc-crawl-limiter-byebye)),见 [http-status-codes.md](http-status-codes.md);保留 crawl-delay 时写明数值与目的。
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

**解释层(14 条,第四批;ID 为源目录原文;privacy+ToS、physical-address+geo-meta 各并一条家族条)**

### eeat-author-byline
- 名称/类型: 作者署名缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 内容页(文章/指南/评测)没有可见的作者归属——无 byline,也无链接到作者档案的署名元素。
**为什么(why)**: Google 强烈建议在读者期待的地方加准确的作者信息(byline),并让 byline 链到作者背景;伪造作者信息不可取。E-E-A-T 本身不是具体排名因素([有用内容文档](https://developers.google.com/search/docs/fundamentals/creating-helpful-content))。署名也是 Article author 字段的可见依据:结构化数据描述的内容须在页面可见([结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies))。
**触发(trigger)**: 1) 页面属内容模板(文章/博客/新闻形态,判定口径源表未公布[待核]);2) 无作者名文本或指向作者档案的署名链接即 warn。
**不修的条件(caveat)**: 署名不是直接排名因素,然而它是整条 E-E-A-T 评估链的入口,所以一般建议内容页必配。但公司公告/产品页/工具页以组织身份发布是正当形态,author 用 Organization 代替 Person 即可。
**修复(fix)**: 内容模板加可见 byline 并链接到作者档案页;与 Article schema 的 author 字段同源输出;匿名编辑部的站至少给"编辑团队"一个实体页。
**关联(seealso)**: eeat-author-expertise、sd-required-fields;[content-patterns.md](../content/content-patterns.md)、[geo-evidence.md](../content/geo-evidence.md)

### eeat-author-expertise
- 名称/类型: 作者资历标记缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn;作者凭证+简历+资历页)
**这意味(what)**: 有作者署名,但作者资历不可验证——无 bio、无凭证(头衔/资质/从业背景)、无独立作者页。
**为什么(why)**: 署名回答"谁写的",资历回答"凭什么信"。Google 的自评问题包括:byline 是否链到作者背景与所写领域([有用内容文档](https://developers.google.com/search/docs/fundamentals/creating-helpful-content))。Person schema 的 jobTitle/knowsAbout 把资历机器可读化;作者页是 author 实体 @id 的落点,缺它署名实体悬空(联动 sd-entity-reference 的 dangling 判定)。
**触发(trigger)**: 1) 页面存在署名;2) 站内无对应作者档案页,或 bio 缺凭证要素(要素清单口径[待核])即 warn。
**不修的条件(caveat)**: 资历呈现对非 YMYL 内容的常规排名影响有限,所以一般建议按内容风险分级:YMYL 全配,普通内容至少 bio+头衔。但个人品牌站(域名即作者本人)可弱化独立作者页。
**修复(fix)**: 建作者档案页(bio/凭证/同主题其他文章);Article 的 author 指向该页 Person 的 @id;补 jobTitle/knowsAbout 字段。
**关联(seealso)**: eeat-author-byline、sd-entity-reference;[entity-signal-checklist.md](entity-signal-checklist.md)、[knowledge-graph-guide.md](knowledge-graph-guide.md)

### eeat-content-dates
- 名称/类型: 内容日期缺失/更新机制缺位 —— warning · 优先级 medium · 输出 WARN(源表 warn;datePublished/dateModified,Article schema 或 `<time>`)
**这意味(what)**: 内容页没有发布/更新日期,或日期只有视觉层没有机器可读载体(Article schema 的 datePublished/dateModified 或 `<time datetime>`)。
**为什么(why)**: Google 有"query deserves freshness"系统,对需要新内容的查询展示更新的内容([排名系统指南](https://developers.google.com/search/docs/appearance/ranking-systems-guide))。可见日期与机器可读日期要一致,三处年份打架另归 content-agreement。正解是真实更新加真实 dateModified,而不是机械刷新时间戳(会被 crawl-sitemap-date-drift 的交叉比对识破)。
**触发(trigger)**: 1) 内容模板页无 datePublished(或等价 `<time>`)即 warn;2) 有发布无更新日期是否单判[待核:源表按 Article 必填口径]。
**不修的条件(caveat)**: 日期不是全场景排名因素(常青内容挂显眼旧日期反而降 CTR),所以一般建议信息敏感内容配全、常青内容可只留发布年月。但把构建时间当修改时间写入是必须清掉的造假形态。
**修复(fix)**: CMS 把真实 updated_at 输出到 Article schema 的 datePublished/dateModified 与 `<time>`;内容保鲜流程见 [content-refresh-playbook.md](../content/content-refresh-playbook.md)。
**关联(seealso)**: eeat-author-byline、content-agreement、crawl-sitemap-lastmod;[content-refresh-playbook.md](../content/content-refresh-playbook.md)、[content-decay-signals.md](../content/content-decay-signals.md)

### eeat-citations
- 名称/类型: 权威引用缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn;链向权威源 .gov/.edu/论文/行业出版物)
**这意味(what)**: 内容页的论断没有外部权威来源支撑——无出站引用,或引用全指向低可信源。
**为什么(why)**: Google 说链出引用来源有助于建立可信度,nofollow 只用于不信任的来源([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable))。把引用链接全 nofollow 等于亲手关掉这个信号(见 links-nofollow-external)。.gov/.edu 等"权威域清单"是工具约定,不是 Google 规则。
**触发(trigger)**: 内容页出站引用中权威源(.gov/.edu/论文域名/行业出版物清单[清单口径待核])计数=0 即 warn。
**不修的条件(caveat)**: 引用密度不是排名公式(不是每页都得挂 .gov),所以一般建议论断型内容配引用、叙事型内容不强求。但为凑权威链接硬引不相关来源,反而稀释主题相关度。
**修复(fix)**: 数据/论断处补一手来源链接(正常 follow);证据分级规范见 [geo-evidence.md](../content/geo-evidence.md);死引用按 links-external-reachability 定期清理。
**关联(seealso)**: links-nofollow-external、eeat-disclaimers;[geo-evidence.md](../content/geo-evidence.md)、[geo-evidence-bank.md](../content/geo-evidence-bank.md)

### eeat-about-page
- 名称/类型: About 页缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 站点没有 About/About Us 页,或有但无实质组织信息。
**为什么(why)**: About 页告诉读者这个站是谁、凭什么可信。Google 的自评问题包括访客能否一眼看出内容由谁制作([有用内容文档](https://developers.google.com/search/docs/fundamentals/creating-helpful-content))。它也是 Organization 实体叙事(使命/团队/历史)的载体,与 Organization schema 互为表里。
**触发(trigger)**: 站内导航/页脚无可达的 About 页(URL 形态 /about、/about-us 等[路径词表待核])即 warn;crawl 模式全站判,单页审计按页脚链接判。
**不修的条件(caveat)**: About 页不是排名因素本身,然而它是信任链地基,所以一般建议全站必配。但纯内部工具无所谓;个人博客可用"关于我"页等价满足。
**修复(fix)**: 建 About 页:组织是谁/做什么/凭什么可信(团队/历史/认证);页脚全局链接;与 Organization schema 同源输出。
**关联(seealso)**: eeat-contact-page、eeat-editorial-policy;[knowledge-graph-guide.md](knowledge-graph-guide.md)

### eeat-contact-page
- 名称/类型: 联系页缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn;email/电话/表单/地址至少其一)
**这意味(what)**: 站点没有联系页,或联系页没有任何可用通道(源表口径:email/电话/表单/地址至少其一)。
**为什么(why)**: 联系信息是信任的底线证据,电商/服务类尤甚。多地法律要求电商标明经营者与联系方式,以当地法务意见为准。通道的真实可用性比数量重要,一个真实表单胜过四个死邮箱。
**触发(trigger)**: 站内无可达联系页,或联系页四类通道(email/电话/表单/地址)计数=0 即 warn。
**不修的条件(caveat)**: 联系页不影响常规排名,然而缺失在 YMYL/电商场景是信任硬伤,所以一般建议必配。但开源项目站用 GitHub issue 等单一通道替代是可接受形态。
**修复(fix)**: 建联系页(≥1 真实通道);页脚全局链接;电话/地址与 LocalBusiness/PostalAddress schema 同源(见 eeat-physical-address)。
**关联(seealso)**: eeat-about-page、eeat-physical-address;[knowledge-graph-guide.md](knowledge-graph-guide.md)

### eeat-privacy-tos(家族条:privacy-policy+terms-of-service)
- 名称/类型: 隐私政策/服务条款链接缺失 —— warning · 优先级 low · 输出 WARN(源表各=warn:页脚隐私政策链接、页脚 ToS 链接)
**这意味(what)**: 页脚缺隐私政策或服务条款链接(两条同构:均为页脚法定页存在性检查,并作一条)。
**为什么(why)**: 两页是商业信任与合规的基建:收集个人数据或加载追踪脚本时,多数辖区要求公开隐私政策(以法务意见为准);ToS 划定内容与交易权责。对搜索引擎无已知直接作用。缺失还联动 legal-cookie-consent。
**触发(trigger)**: 页脚(或全站级导航)无 Privacy Policy / Terms of Service 链接即各 warn。
**不修的条件(caveat)**: 法定页本身不是排名因素,然而隐私政策缺失在多数辖区是合规缺口,所以一般建议全站配。但无 cookie 无收集的纯静态个人站可从简——从简不等于没有。
**修复(fix)**: 页脚模板级补两链接(勿逐页手写);隐私政策覆盖实际收集行为并与 CMP 配置一致(见 legal-cookie-consent)。
**关联(seealso)**: legal-cookie-consent、eeat-contact-page;[validation-guide.md](validation-guide.md)

### eeat-physical-address(吸收 eeat-geo-meta)
- 名称/类型: 实体地址标记缺失 —— warning · 优先级 low · 输出 WARN(源表:physical-address warn,PostalAddress(Organization/LocalBusiness schema);geo-meta warn,有 local-business schema 的页也应设 geo meta 标签)
**这意味(what)**: Organization/LocalBusiness schema 没有 PostalAddress,或 LocalBusiness 页面缺 geo meta(geo.region/geo.position/ICBM)标签——源表把 geo meta 作为 local-business schema 的伴生要求。
**为什么(why)**: 地址是线下可信实体与本地相关度的双重信号:LocalBusiness 富结果与本地意图查询都吃地址数据;LocalBusiness 结构化数据里 Google 必填的是 name 与 address([文档](https://developers.google.com/search/docs/appearance/structured-data/local-business));geo meta 标签没有搜索引擎文档支持,是工具约定。单点标记不等于有效——NAP 跨载体一致才有价值(见 eeat-nap-consistency)。
**触发(trigger)**: 1) 页面有 Organization/LocalBusiness schema 但无 PostalAddress 即 warn;2) 页面有 LocalBusiness schema 但无 geo meta 标签即 warn(geo-meta 条)。
**不修的条件(caveat)**: 纯线上业务无实体地址是正当形态,PostalAddress 可只到城市/国家级;家庭办公地址公开与否是隐私取舍,可用 areaServed(服务区域)替代。但本地商户缺地址标记等于放弃本地搜索资格。
**修复(fix)**: Organization/LocalBusiness 挂 PostalAddress(streetAddress/postalCode/addressLocality/addressCountry);LocalBusiness 页补 geo.position(与 schema 的 geo 同源);模板见 [schema-templates.md](schema-templates.md)。
**关联(seealso)**: eeat-nap-consistency、eeat-contact-page;[schema-templates.md](schema-templates.md)、[knowledge-graph-guide.md](knowledge-graph-guide.md)

### eeat-affiliate-disclosure
- 名称/类型: 联盟披露缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn;FTC 口径 "This post contains affiliate links.")
**这意味(what)**: 含联盟/付费推广链接的页面没有披露声明(FTC 要求的显式披露,如 "This post contains affiliate links.")。
**为什么(why)**: 链接层面,Google 要求付费链接用 rel=sponsored 或 nofollow([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable));法律层面,美国 FTC 要求披露实质性关联,披露要放在推荐信息旁、难以错过,只放页尾或要点开才看到的位置容易被忽略([FTC](https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers))。
**触发(trigger)**: 1) 页面含联盟链接特征(amazon.*/tag=、/aff/、?aff_id= 等形态[特征表待核]);2) 无披露文本即 warn。
**不修的条件(caveat)**: 披露不影响链接本身的排名语义(那是 rel=sponsored 的职责),然而它是合规义务,所以一般建议凡有佣金链接必配。但自然外链与联盟链接要分清——无商业关系的推荐不需要披露。
**修复(fix)**: 联盟链接统一 rel="sponsored";页首/链接前置披露声明;模板级注入勿逐页手写。
**关联(seealso)**: links-nofollow-internal、eeat-disclaimers;[deprecated-signals.md](deprecated-signals.md)

### eeat-disclaimers
- 名称/类型: YMYL 免责声明缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn;医疗/财务/法律内容须有相应免责声明)
**这意味(what)**: YMYL 内容(医疗/财务/法律等)没有对应免责声明("本内容不构成医嘱/投资建议/法律意见")。
**为什么(why)**: 对健康、财务、安全等 YMYL 主题,Google 系统更重视体现强 E-E-A-T 的内容([有用内容文档](https://developers.google.com/search/docs/fundamentals/creating-helpful-content));判定开关见 eeat-ymyl-detection。免责声明框定内容的专业责任范围,本身不是排名因素。
**触发(trigger)**: 1) 页面被 YMYL 检测判为医疗/财务/法律类;2) 无对应免责声明文本即 warn(声明匹配词表[待核])。
**不修的条件(caveat)**: 免责声明不是免责金牌(内容质量仍是主体),所以一般建议声明+引用+作者资历三件套同配,单挂声明救不了薄内容。但非 YMYL 内容不需要泛化免责——全站挂"仅供参考"反而稀释。
**修复(fix)**: 按主题配医疗/财务/法律三类声明;放内容首屏或结论前;与 eeat-citations、eeat-author-expertise 构成 E-E-A-T 三角。
**关联(seealso)**: eeat-ymyl-detection、eeat-citations;[scoring-rubric.md](scoring-rubric.md)

### eeat-editorial-policy
- 名称/类型: 编辑政策页缺失 —— warning · 优先级 low · 输出 WARN(源表 warn;内容标准/事实核查流程)
**这意味(what)**: 站点没有编辑政策页——内容来源标准、事实核查流程、更正机制的公开声明。
**为什么(why)**: "谁核查、怎么更正"让读者判断可信度,更正机制也让 dateModified 的更新可信。无搜索引擎直接依据,是加分项不是底线项,故 low。
**触发(trigger)**: 站内无编辑政策/内容标准/事实核查类页面(URL 与标题词表[待核])即 warn。
**不修的条件(caveat)**: 编辑政策对单人小站不是必需(署名+资历已覆盖信任链),所以一般建议内容团队 ≥2 人或新闻类站配。但为配而配的空政策页(无真实流程)不产生信任价值。
**修复(fix)**: 建编辑政策页:来源标准/核查流程/更正机制/作者资历要求;页脚或 About 页链接;与作者档案页互链。
**关联(seealso)**: eeat-about-page、eeat-content-dates;[content-patterns.md](../content/content-patterns.md)

### eeat-trust-signals
- 名称/类型: 信任信号缺失 —— warning · 优先级 low · 输出 WARN(源表 warn;评论/认证/安全徽章/媒体报道)
**这意味(what)**: 站点没有任何可验证的信任信号:用户评论、第三方认证、安全徽章、媒体报道引用。
**为什么(why)**: 第三方背书是信任的社会化证据;认证与媒体报道可写进 Organization schema(award/subjectOf)。信号要可验证:无链接的 logo 墙没有价值;虚假评论违反 Google 结构化数据指南([结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies))。源表现行改为 pass only:只列出信号,不扣分。
**触发(trigger)**: 全站(或关键模板)评论/认证/徽章/媒体报道四类信号计数=0 即 warn(计入粒度口径[待核])。
**不修的条件(caveat)**: 信任信号是加法不是底线,所以一般建议按业务形态选配(电商重评论,B2B 重认证与报道)。但伪造信号(假评论/未授权徽章)比没有更糟,是信任硬伤。
**修复(fix)**: 接真实评论系统(schema 配页面可见评分,可见性判定见 sd-rating-scope);认证挂权威来源链接;媒体报道用 subjectOf/citation 进 schema。
**关联(seealso)**: sd-rating-scope、eeat-author-expertise;[entity-signal-checklist.md](entity-signal-checklist.md)

### eeat-ymyl-detection
- 名称/类型: YMYL 检测器 —— opportunity · 优先级 insight · 输出 INFO(源表 info;仅识别不扣分)
**这意味(what)**: 页面被识别为 YMYL(Your Money or Your Life)内容——健康/财务/安全/法律等直接影响读者重大利益的题材。
**为什么(why)**: 开关型规则:它不评价页面,只给 eeat-disclaimers 等下游规则供数。Google 对 YMYL 主题更重视强 E-E-A-T 内容([有用内容文档](https://developers.google.com/search/docs/fundamentals/creating-helpful-content))。输出它让站主知道哪些页面要按更严标准加固;拿不准即标 true。源表现行为 pass only,永不扣分。
**触发(trigger)**: 页面内容/主题命中 YMYL 题材词表(医疗/金融/法律/重大新闻等类目[词表口径待核])即 info,不扣分。
**不修的条件(caveat)**: YMYL 没有官方机器可读清单,词表判定必有边缘误差(健身食谱算不算健康类),所以 info 不扣分、人工复核定类。但漏判的代价(按普通标准处理 YMYL)大于误判,方向上从严。
**修复(fix)**: 无需修复——把 YMYL 页面清单交给 E-E-A-T 加固流程:作者资历/免责声明/权威引用三件套(见 eeat-disclaimers)。
**关联(seealso)**: eeat-disclaimers、eeat-author-expertise;[scoring-rubric.md](scoring-rubric.md)

### eeat-nap-consistency ⛏
- 名称/类型: NAP 一致性 —— warning · 优先级 medium · 输出 WARN(源表 warn;仅 crawl 模式;同一组织名在整站爬取中只挂一个电话+地址,不同名=不同主体)
**这意味(what)**: 同一组织的名称/地址/电话(NAP)在整站爬取中不一致——同名组织出现多个电话/地址组合。
**为什么(why)**: 同一门店的名称、地址、电话在各处一致,是本地 SEO 的通行做法(行业经验,非 Google 文档条文);不一致会让同一门店像两家。源表判定边界照抄:同一组织名只挂一个电话+地址;不同名=不同主体。可见层与 schema 的 PostalAddress/telephone 要同源。
**触发(trigger)**: ⛏ 1) crawl 全站提取 NAP 三元组;2) 同名组织的电话或地址组合 >1 即 warn;3) 不同名不做归并判定。
**不修的条件(caveat)**: 合法场景:连锁多店(同名组织每店独立地址电话是真实业务形态[分型口径待核:命中后需人工确认是否连锁])、品牌更名过渡期新旧名并存。所以一般建议命中后人工核对再改。
**修复(fix)**: NAP 单一数据源(CMS 站点信息表)注入页脚/联系页/schema 三处;连锁站每店独立页+独立 NAP;先改可见层再同步 schema。
**关联(seealso)**: eeat-physical-address、sd-entity-consistency;[knowledge-graph-guide.md](knowledge-graph-guide.md)、[entity-signal-checklist.md](entity-signal-checklist.md)

---

## 三、重点展开:Internationalization(13 条)

> 我们的 [hreflang-validation.md](hreflang-validation.md) 八检框架覆盖了 return-links/noindex/非规范/断链/重定向/冲突/多载体/相对 URL 中的多数判定;此处按 SEOmator 规则粒度补全为 13 条,新增了**入向校验**与 **x-default 洞察**两个我们缺的维度。
> Google 口径先记三条([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions),核对 2026-10-18):① 没互指的那一对注解被忽略,其余互指的照常处理,不是整簇作废;② HTML、HTTP 头、sitemap 三载体等价,同时用"no benefit in Search",是维护问题不是错误;③ Google 不用 hreflang 或 html lang 判定页面语言。码值:ISO 639-1 语言 + 可选 ISO 3166-1 Alpha-2 区域或 ISO 15924 文字(zh-Hans、zh-Hant、zh-Hans-US 合法),大小写不敏感;es-419 这类非 Alpha-2 区域码不支持;只写区域不合法;UK/EU 等保留码只忽略区域部分。

| 规则 ID | 名称 | 严重度 | 判定阈值/要点(源表现行) |
|---|---|---|---|
| `i18n-lang-attribute` | lang 属性 | warn/fail | `<html>` 须带合法 BCP 47 码(en/en-US/zh-Hans) |
| `i18n-hreflang` | hreflang 校验 | warn/fail | 空值、非 `xx`/`xx-YY`(语言小写区域大写)、重复码=fail;相对 href、无自引用、≥2 条却无 x-default=warn;无注解只在链向他 locale 同路径时 warn;不读 sitemap |
| `i18n-hreflang-return-links` | 自引用 | warn | 本页 hreflang 集里没有指向本页的条目;不抓目标(互指由 crawl-hreflang-reciprocity 判) |
| `i18n-hreflang-to-noindex` | 带 hreflang 又 noindex | fail | 本页声明 hreflang 且本页 noindex;目标 noindex 由 crawl 版判 |
| `i18n-hreflang-to-non-canonical` | 自引用非规范 | warn | 本页的自引用 hreflang 指向的 URL ≠ 本页 canonical |
| `i18n-hreflang-to-broken` | 指向断链 | warn/fail | 静态:空/仅锚点/javascript:/不可解析/非 HTTP(S) href;crawl 模式追加:目标 **4xx/5xx=fail,超时=warn** |
| `i18n-hreflang-to-redirect` | 指向重定向 | warn | 静态启发:HTTPS 页上用 HTTP hreflang;crawl 模式追加:**3xx 目标=warn** |
| `i18n-hreflang-conflicting` | 冲突声明 | fail | 同码多 URL/同 URL 多码/本页被多码自引用;x-default 豁免 |
| `i18n-hreflang-lang-mismatch` | 语言不匹配 | warn | `<html lang>` 主语言子标签 ≠ 本页自引用 hreflang 码的主语言;不分析正文 |
| `i18n-hreflang-multiple-methods` | 多载体混用 | warn | 同页 HTML link 与 HTTP Link 头都声明;不读 sitemap |
| `i18n-hreflang-relative-url` | 相对 URL | fail | href 须为含协议的绝对 URL;`/fr/`、`fr/page`、`//example.com/fr/` 均不合格 |
| `i18n-hreflang-x-default` | 语言码兼作 x-default | pass only | 同一 URL 既被语言码又被 x-default 指向;合法,报出供确认 |
| `i18n-hreflang-incoming-invalid` ⛏ | 入向无效码 | fail | 他页指向本页的注解须用合法码(x-default 恒合法) |

**解释层(14 条:13 条第一波 P0/P1 + 第三批 lang 一致性一条)**

### i18n-lang-attribute
- 源表:warn/fail · 权重 10。`<html>` 缺 lang 或值不是合法 BCP 47 码。工具约定。建议优先级:无障碍 high,SEO low。
**依据**: Google 不用 html lang 判定页面语言,而用算法识别([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。lang 的作用在无障碍:WCAG 3.1.1(A 级)要求页面默认语言可被程序判定,屏幕阅读器据此加载发音规则([W3C](https://www.w3.org/WAI/WCAG22/Understanding/language-of-page.html))。核对 2026-10-18。
**判据**: 通过=`<html lang>` 存在且是合法 BCP 47 码(`xx`、`xx-YY`、`zh-Hans`)。失败=缺失或非法(如 `english`)。
**执行**: `AUDIT URL` 出现 `[WARN] a11y: html 无 lang` 即缺失;值是否合法用 `curl -s URL | grep -oiE '<html[^>]*lang=[^ >]+'` 人工判。
**修复**: 按页面主语言设 `<html lang="zh-Hans">`;混排段落用元素级 lang。
**关联**: i18n-hreflang-lang-mismatch、i18n-lang-consistency;[semantic-html.md](semantic-html.md)

### i18n-hreflang
- 源表:warn/fail · 权重 10。见上表;码格式要求"语言小写区域大写",比 Google 严。工具约定。建议优先级 medium。
**依据**: hreflang 是可选做法,不加 Google 也可能自己找到其他语言版,但最好显式声明;码值规则与 x-default 见本节开头([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。核对 2026-10-18。
**判据**: 通过=多语言页的注解集码值合法、含自引用,≥2 条时有 x-default(源表 warn 项)。失败=空值、重复码、非法码。大小写不同不算错(Google 不敏感)。
**执行**: `HREFLANG 簇内全部URL`,看「条目」「自引用」「语言码」三列。注意脚本要求区域码大写、拒收 zh-Hans、放行 es-419,三点都与 Google 口径相反,命中后按本节开头人工复判。
**修复**: 三载体任选一种,覆盖全簇加 x-default;载体选择见 [hreflang-validation.md](hreflang-validation.md) 第二节。
**关联**: i18n-hreflang-multiple-methods、i18n-hreflang-x-default;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-return-links
- 源表:warn · 权重 12。本页的 hreflang 集里没有指向本页的条目(自引用);不抓目标。工具约定。建议优先级 high。
**依据**: "Each language version must list itself as well as all other language versions"([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。互相回链另由 crawl-hreflang-reciprocity 判。核对 2026-10-18。
**判据**: 通过=集内有一条 href 等于本页(同 host 同路径)。失败=没有。
**执行**: `HREFLANG URL`,「自引用」列为 ✗ 即失败;单页用 G7 看有无本页 URL。
**修复**: 模板循环输出全簇时包含当前页;sitemap 载体每个 `<url>` 列出包括自己在内的全部版本。
**关联**: crawl-hreflang-reciprocity;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-to-noindex
- 源表:fail · 权重 10。本页声明了 hreflang,本页又带 noindex(meta robots/googlebot 或 X-Robots-Tag)。工具约定。建议优先级 high。
**依据**: noindex 的页不会出现在结果里([robots meta 规范](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)),它作为语言版的那几对注解没有可展示的对象;按 Google 口径只影响含它的那几对,不是整簇。核对 2026-10-18。
**判据**: 通过=带 hreflang 的页可索引。失败=带 hreflang 且 noindex。
**执行**: G7 有输出,同时 `AUDIT URL` 出现 `[CRITICAL] robots: noindex`。
**修复**: 要该语言版就删 noindex;不要就从所有载体删掉它的注解,也删掉本页的注解。
**关联**: crawl-hreflang-to-noindex;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-to-non-canonical
- 源表:warn · 权重 10。本页的自引用 hreflang 指向的 URL ≠ 本页 canonical。工具约定。建议优先级 high。
**依据**: 用 hreflang 时 canonical 应指向同语言页;Google 规范化时优先选 hreflang 簇里的 URL;不要把 HTTP 版本放进 hreflang([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。注解与 canonical 指向不同 URL 时,两个信号互相打架。核对 2026-10-18。
**判据**: 通过=自引用 hreflang 的 href 与 canonical 完全相同(协议、host、路径、参数)。失败=不同。
**执行**: G7 取本页自引用条目,G1 取 canonical,逐字比对。
**修复**: hreflang 集统一输出各语言的 canonical 绝对 URL;生成器别复用带追踪参数的当前 URL。
**关联**: crawl-sitemap-non-canonical;[redirects-canonical.md](redirects-canonical.md)

### i18n-hreflang-to-broken
- 源表:warn/fail · 权重 10。静态:空/仅锚点/javascript:/不可解析/非 HTTP(S) href;crawl:目标 4xx/5xx=fail,超时=warn。工具约定。建议优先级 high。
**依据**: Google 不索引返回 4xx 的 URL([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors)),坏注解指向的语言版无法提供;alternate URL 必须是完整 URL([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。核对 2026-10-18。
**判据**: 通过=href 是可解析的 http(s) 绝对 URL 且目标 200。失败=静态坏 href 或目标 4xx/5xx;超时=警告。
**执行**: `HREFLANG 簇内全部URL`,「HTTP200」列 ✗ 即失败(脚本跟随重定向,只看终态);静态坏值用 G7 人工看。
**修复**: 修好或删掉坏注解;未上线的语言版别输出注解。
**关联**: i18n-hreflang-relative-url、i18n-hreflang-to-redirect;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-to-redirect
- 源表:warn · 权重 8(静态:HTTPS 页用 http:// hreflang;crawl:3xx 目标)。工具约定。建议优先级 medium。
**依据**: Google 要求 hreflang 里放 HTTPS 版本,不放 HTTP 版本([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。"每跳都损耗"无官方出处。核对 2026-10-18。
**判据**: 通过=每个目标直接 200 且与页面同协议。失败=目标 3xx,或 HTTPS 页出现 http:// 目标。
**执行**: 对每个目标跑 `REDIR 目标URL`,链长 >0 即失败;静态启发用 G7 找 `href="http://`。
**修复**: hreflang 改指终点 200 URL;全站注解统一 https 绝对 URL。按 Accept-Language 动态落地的选择页属正常形态。
**关联**: crawl-canonical-redirect;[redirects-canonical.md](redirects-canonical.md)

### i18n-hreflang-conflicting
- 源表:fail · 权重 10。同码多 URL、同 URL 多码、本页被多码自引用;x-default 豁免。工具约定。建议优先级 high。
**依据**: Google 要求每个语言版列出同一套链接,集合在各版本间一致([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions));一码对多 URL 时无法判断该给哪一个。Google 对冲突注解的处理未公开。核对 2026-10-18。
**判据**: 通过="码→URL"与"URL→码"都是一对一(x-default 不计)。失败=任一方向一对多。
**执行**: `curl -s URL | grep -oiE '<link[^>]+hreflang=[^>]*>' | grep -oiE 'hreflang=.?[a-zA-Z-]+' | sort | uniq -d` 有输出=同码重复;同 URL 多码从 G7 输出人工看。
**修复**: 保证映射一对一;混排页拆成各语言独立 URL。
**关联**: crawl-hreflang-incoming-conflict、i18n-hreflang-lang-mismatch;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-lang-mismatch
- 源表:warn · 权重 8。`<html lang>` 主语言子标签 ≠ 本页自引用 hreflang 码的主语言(en-US 算 en);不分析正文。工具约定。建议优先级 low。
**依据**: Google 不用 html lang 判定语言([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions)),这项不直接影响 Google;它暴露模板配置不一致。注解码与实际内容语言不符才伤用户,需人工抽查。核对 2026-10-18。
**判据**: 通过=两处主语言一致。失败=不一致,或注解码与正文语言明显不符(人工)。
**执行**: G7 取自引用码,`curl -s URL | grep -oiE '<html[^>]*lang=[^ >]+'` 取 lang,比对主子标签。
**修复**: 改码或改 lang;混排页以主语言为准。
**关联**: i18n-lang-attribute;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-multiple-methods
- 源表:warn · 权重 6。同页 HTML link 与 HTTP Link 头都声明;不读 sitemap。工具约定。建议优先级 low(维护建议)。
**依据**: 三种方法在 Google 看来等价;可以同时用,但"there's no benefit in Search",还更难维护([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。不是错误。核对 2026-10-18。
**判据**: 通过=只用一种载体,或多载体内容完全一致(降为提示)。失败=多载体且内容不一致。
**执行**: `HREFLANG URL`,看「三载体冲突」段;单页 G7 加 `curl -sI URL | grep -i '^link:.*hreflang'`。
**修复**: 选一种载体(规模站多用 sitemap,集中维护),清空其余载体。
**关联**: i18n-hreflang;[hreflang-validation.md](hreflang-validation.md) 第二节

### i18n-hreflang-relative-url
- 源表:fail · 权重 6。href 是 `/fr/`、`fr/page` 或协议相对 `//example.com/fr/`。工具约定(与 Google 一致)。建议优先级 high。
**依据**: "Alternate URLs must be fully-qualified, including the transport method (http/https)",`//example.com/foo` 与 `/foo` 均不行([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。核对 2026-10-18。
**判据**: 通过=每个 href 以 `http://` 或 `https://` 开头。失败=任一相对或协议相对。
**执行**: G4 有输出即失败;或 `HREFLANG` 的「绝对URL」列 ✗。
**修复**: 模板输出绝对 URL;CI 对 hreflang href 加 scheme 断言。
**关联**: i18n-hreflang-to-broken;[hreflang-validation.md](hreflang-validation.md)

### i18n-hreflang-x-default
- 源表:pass only · 权重 1。同一 URL 既被语言码又被 x-default 指向;永远通过,只报出供确认。工具约定。建议优先级 insight。
**依据**: x-default 为语言选择页设计,但可用于任何页;通用兜底页"可以是某个特定语言页"([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。核对 2026-10-18。
**判据**: 不判对错。确认意图:语言专页兜底=保持;本想用选择页兜底=改 x-default 目标。
**执行**: G7 输出里找同时带语言码与 `x-default` 的同一 href。
**修复**: 按意图调整;无需为扣分修改。
**关联**: i18n-hreflang;[hreflang-validation.md](hreflang-validation.md) 第三节 x-default 六用法

### i18n-hreflang-incoming-invalid ⛏
- 源表:fail · 权重 8 · 需 `--crawl`。他页指向本页的注解用了无效码(x-default 恒合法)。工具约定。建议优先级 high。
**依据**: Google 只支持 ISO 639-1 语言码加可选 ISO 3166-1 Alpha-2 区域码(或 ISO 15924 文字);es-419 不支持;UK、EU 这类保留码只是区域部分被忽略,不是整条作废;只写区域不合法([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。下划线写法(en_US)不符合规定格式,Google 是否容错未公开。核对 2026-10-18。
**判据**: 通过=入向注解全用合法码。失败=出现非法语言码、只有区域、下划线分隔;保留区域码(en-UK)按"区域无效"报警告。
**执行**: 对引用方跑 `HREFLANG 引用方URL…`,「语言码」列 ✗ 的条目即问题(注意该列对 zh-Hans 与大小写误报,见 i18n-hreflang)。
**修复**: 改引用方:en_US→en-US、en-UK→en-GB;全站语言码表 lint 一次。修在引用方,不在本页。
**关联**: crawl-hreflang-incoming-conflict、i18n-hreflang;[hreflang-validation.md](hreflang-validation.md)

### i18n-lang-consistency [待核 ID]
- 名称/类型: 元素级 lang 与 xml:lang 一致性 —— warning · 优先级 low · 输出 WARN(严重度源表未单列[待核];Accessibility 节"lang 与 xml:lang 一致""元素级 lang 合法 BCP 47"两条并入本条,同构判定)
**这意味(what)**: 页面在 html 或元素级设置的 lang 与 xml:lang 值不一致,或元素级 lang 用了非法 BCP 47 码。
**为什么(why)**: XHTML 遗留属性 xml:lang 与 lang 并存时应同值;不一致时解析器与辅助技术各取其一。元素级 lang 服务混排段落,错码让屏幕阅读器用错发音规则(WCAG 3.1.2 Language of Parts)。本条管元素级与双属性一致性,文档级见 i18n-lang-attribute。Google 不用 lang 判语言,本条是无障碍项。
**触发(trigger)**: 1) 同元素 lang 与 xml:lang 都存在且值不同即 warn;2) 元素级 lang 值不匹配 BCP 47 `xx`/`xx-YY` 子集(zh-Hans 等文字子标签合法)即 warn。
**不修的条件(caveat)**: 纯 XHTML 遗留模板批量清理收益低时,可只修确有混排内容的模板。
**修复(fix)**: 输出层只写 lang(XHTML 需求才双写同值);混排段落元素级 lang 用精确码;CI 加 lang 值 BCP 47 lint。
**关联(seealso)**: i18n-lang-attribute、i18n-hreflang-lang-mismatch;[semantic-html.md](semantic-html.md)

---

## 四、其余 17 类规则目录(浓缩表,保留全部数字阈值)

### Core SEO(24 条,权重 11%)

源表现行(132d2384):`core-title-present` 缺失=fail;`core-title-length` **30-60 字符**=warn/fail;`core-description-present` 缺失=fail;`core-description-length` **120-160 字符**=warn;`core-canonical-present` 缺失=fail;`core-canonical-valid` 非绝对 http(s)=warn/fail(不请求目标);`core-viewport-present` 缺失=fail;`core-favicon-present` 缺失=fail;`core-h1-present` 缺失=fail、`core-h1-single` 多于 1 个=warn/fail;`core-canonical-header`(HTML canonical 与 HTTP Link 头不一致=warn);`core-nosnippet`(nosnippet/max-snippet:0=warn);`core-robots-meta`(noindex/nofollow/noarchive/noimageindex/none=warn);`core-title-unique`(跨页重复 title=warn,无 title=fail,crawl);**canonical 家族 8 条**:conflicting(HTML 与 Link 头不一致=fail)/to-homepage(深页指向首页=fail)/http-mismatch(协议不一致=fail)/loop(指向他页即 warn,不抓目标)/to-noindex(本页 noindex 且 canonical 指他页=warn)/outside-head(在 body 里=fail)/attributes(带 hreflang/lang/media/type=fail,其他多余属性=warn)/multiple(多条且不一致=fail,一致=warn);`core-robots-directive-mismatch`(meta 与 X-Robots-Tag 一方 index 一方 noindex=fail,多处声明 noindex=warn);`core-canonical-external`(指向外域,pass only)。长度阈值都是工具约定。

**解释层(20 条:18 条第一波 P0/P1 + 第三批 viewport/favicon)**

#### core-canonical-conflicting
- 源表:fail · 权重 8。HTML canonical 与 HTTP Link 头 canonical 指向不同 URL(小写、去尾斜杠后比);只有一处则通过;sitemap 不参与。建议优先级 high。
**依据**: 不要用不同方法为同一页指定不同 canonical;HTML 元素与 HTTP 头二选一,同时用更易出错([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。冲突时 Google 自行挑选。核对 2026-10-18。
**判据**: 通过=只有一处声明,或两处同值。失败=两处不同。
**执行**: G1 与 G3 的 URL 比对;site_audit 只读 HTML canonical,不查 Link 头。
**修复**: 全部信号指同一目标(通常自引用);只保留一种载体。
**关联**: core-canonical-header、core-canonical-multiple;[redirects-canonical.md](redirects-canonical.md)

#### core-canonical-multiple
- 源表:warn/fail · 权重 6。同一文档有多条 rel=canonical:不一致=fail,一致=warn。建议优先级 high(不一致)/low(一致)。
**依据**: "When more than one is specified, all rel=canonical links will be ignored"([Google 2013 博文](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical));常见原因是 SEO 插件默认再插一条。核对 2026-10-18。
**判据**: 通过=恰好 1 条。失败=≥2 条且目标不同;警告=≥2 条但相同。
**执行**: `G1 | wc -l` 大于 1 即命中;site_audit 只保留最后一条,不报多条。
**修复**: 找到双写来源(框架默认+插件/手写)删掉一处;CI 断言每页 canonical 计数=1。
**关联**: core-canonical-conflicting、core-canonical-outside-head;[head-elements.md](head-elements.md)

#### core-canonical-outside-head
- 源表:fail · 权重 8。rel=canonical 出现在 `<head>` 之外。建议优先级 high。
**依据**: canonical 元素"only accepted if it appears in the `<head>` section";body 里的会被忽略([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls);[2013 博文](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical))。head 里出现非法元素时,Google 忽略其后的全部元素([valid-page-metadata](https://developers.google.com/search/docs/crawling-indexing/valid-page-metadata))。核对 2026-10-18。
**判据**: 通过=canonical 在 head 内,且之前没有非法元素。失败=在 body 里,或排在 head 内的非法元素(img、iframe 等)之后。
**执行**: G2 有输出即失败;渲染后位置用 GSC 网址检查的已抓取 HTML 复核。
**修复**: 移进 head 并尽量靠前;清除 head 内的非法元素。
**关联**: core-canonical-multiple、htmlval-head-content;[head-elements.md](head-elements.md)、[rendering-seo.md](rendering-seo.md)

#### core-canonical-attributes
- 源表:warn/fail · 权重 7。canonical 元素带 hreflang/lang/media/type=fail,带其他多余属性=warn。建议优先级 high/low。
**依据**: 带 hreflang、lang、media、type 的 rel=canonical "are not used for canonicalization"([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。核对 2026-10-18。
**判据**: 通过=只有 rel 与 href。失败=带上述四种属性之一。
**执行**: `G1 | grep -iE ' (hreflang|lang|media|type)='` 有输出即失败。
**修复**: canonical 只留 rel+href;语言与设备变体用独立的 alternate 元素。
**关联**: core-canonical-conflicting;[head-elements.md](head-elements.md) link 速查

#### core-canonical-loop
- 源表:warn · 权重 7。canonical 指向他页即 warn(可能回指);不抓目标。真环由 crawl-canonical-loop 判。建议优先级 medium。
**依据**: Google 文档无专门说法;规范页本身应自引用([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。核对 2026-10-18。
**判据**: 通过=自引用。警告=指向他页(需确认目标自引用)。失败=目标指回本页(两页环)。
**执行**: G1 读目标;对目标再跑 G1,指回本页即失败;全站用 J2。
**修复**: 确定终点页让它自引用,其余直指它。
**关联**: crawl-canonical-loop;[redirects-canonical.md](redirects-canonical.md)

#### core-canonical-to-noindex
- 源表:warn · 权重 7。本页带 noindex(robots/googlebot meta 或 X-Robots-Tag),canonical 又指向他页;自引用通过;不抓目标。建议优先级 medium。
**依据**: Google 不建议用 noindex 阻止单站内规范页的选择,推荐只用 rel=canonical([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。目标 noindex 的情形见 crawl-canonical-to-noindex。核对 2026-10-18。
**判据**: 通过=noindex 与"canonical 指他页"不同时出现。失败=同时出现。
**执行**: `AUDIT URL` 出现 `[CRITICAL] robots: noindex`,且 G1 的 href 不是本页。
**修复**: 要合并到他页:删 noindex,保留 canonical;要退出索引:删 canonical,保留 noindex。
**关联**: crawl-canonical-to-noindex;[redirects-canonical.md](redirects-canonical.md) 第三节冲突矩阵

#### core-canonical-header
- 源表:warn · 权重 7。HTML canonical 与 HTTP Link 头 canonical 不一致;SEOmator 建议 HTML 页只用 HTML 元素,Link 头留给 PDF 等非 HTML 资源(工具建议)。建议优先级 medium。
**依据**: Google 两种方式都支持,建议选一种;Link 头的优势是可用于 PDF 等非 HTML 文件([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。核对 2026-10-18。
**判据**: 通过=只用一种,或两者同值。失败=两者不同(与 conflicting 同源,本条侧重载体选择)。
**执行**: G3 有输出时与 G1 比对。Link 头常由 CDN/网关注入,应用代码里找不到就查网关配置。
**修复**: HTML 页删掉 Link 头版本;PDF/DOCX 用 Link 头。
**关联**: core-canonical-conflicting;[head-elements.md](head-elements.md)、[http-status-codes.md](http-status-codes.md)

#### core-canonical-to-homepage
- 源表:fail · 权重 6。非首页的 canonical 指向首页。建议优先级 medium。
**依据**: canonical 表示"这页是那页的重复";Google 举过分类页 canonical 到精选文章的反例,后果是分类页从结果里消失([2013 博文 Mistake 4](https://developers.google.com/search/blog/2013/04/5-common-mistakes-with-relcanonical))。深页与首页几乎不可能重复,多为模板兜底变量为空。核对 2026-10-18。
**判据**: 通过=深页 canonical 不是站点根。失败=路径不是 `/` 的页 canonical 等于首页。
**执行**: G1 的 href 等于 `https://域名/` 而本页路径不是 `/` 即失败。
**修复**: 模板兜底改为自引用;排查变量注入顺序。打印版等真重复页可保留。
**关联**: core-canonical-present;[redirects-canonical.md](redirects-canonical.md)

#### core-canonical-http-mismatch
- 源表:fail · 权重 7。页面与 canonical 协议不一致(HTTPS 页指 HTTP 或反之)。建议优先级 medium。
**依据**: Google 默认优先 HTTPS 作规范页,但 HTTPS 页 canonical 指向 HTTP 页是让它改选 HTTP 的冲突信号之一([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。"引擎会自动升级、风险低"的说法不成立。核对 2026-10-18。
**判据**: 通过=协议一致(应为 https)。失败=不一致。
**执行**: G1 的 href 协议与页面 URL 协议比对。
**修复**: canonical 输出 https 绝对 URL,全站统一。
**关联**: crawl-canonical-form-drift;[redirects-canonical.md](redirects-canonical.md)

#### core-canonical-present
- 源表:`core-canonical-present` fail · 权重 10(缺失);`core-canonical-valid` warn/fail · 权重 1(href 不是绝对 http(s) URL;空或相对=fail,缺失=warn;不请求目标)。建议优先级 medium(缺失是缺信号)。
**依据**: 指定 canonical 不是必需,不指定时 Google 自行选择;规范页上加自引用 canonical 是建议做法([规范化文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls))。相对路径 Google 支持但不推荐,建议用绝对 URL(同上)。核对 2026-10-18。
**判据**: 通过=有一条绝对 https canonical。警告=缺失(单版本页可接受)或根相对路径。失败=空值或相对路径(源表)。
**执行**: `AUDIT URL`:`[WARN] canonical: 缺失`;`[CRITICAL] canonical: 相对 URL`(只对不以 http 或 / 开头的值报,比 Google 严;`/path` 与 `//host` 不报)。
**修复**: 有参数、分页、打印版等重复形态的页补自引用绝对 canonical。
**关联**: core-canonical-conflicting;[redirects-canonical.md](redirects-canonical.md) 六场景

#### core-canonical-external
- 源表:pass only · 权重 1。canonical 指向他 host;永远通过,只报出供确认。建议优先级 insight。
**依据**: Google 不建议用 canonical 处理与联合发布伙伴的重复,最有效的做法是伙伴屏蔽索引;攻击者也会插入跨域 canonical 劫持页面([规范化排障](https://developers.google.com/search/docs/crawling-indexing/canonicalization-troubleshooting))。核对 2026-10-18。
**判据**: 不判对错。确认:自有多域合并=保持;供稿伙伴场景=改用伙伴侧 noindex;非预期=按被黑或模板错处理。
**执行**: `AUDIT URL` 出现 `[INFO] canonical: 指向外域`(已按 host 小写、去默认端口比较)。
**修复**: 非预期的改回自引用,并检查是否被注入。
**关联**: core-canonical-conflicting;[redirects-canonical.md](redirects-canonical.md)

#### core-robots-directive-mismatch
- 源表:warn/fail · 权重 5。meta robots 与 X-Robots-Tag 一方 index/follow、一方 noindex/nofollow=fail;多处重复声明 noindex/nofollow=warn。建议优先级 high/low。
**依据**: 多条规则冲突时,Google 取全部否定规则之和,即限制更严的生效("use the sum of the negative rules",[robots meta 规范](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag))。核对 2026-10-18。
**判据**: 通过=所有载体意图一致且只声明一次。失败=一处 index、一处 noindex(结果按 noindex 处理)。
**执行**: G6 同时列出 meta 与响应头,人工比对;site_audit 把两处合并后只报 noindex。
**修复**: 统一索引意图;只在一处声明(服务器层 X-Robots-Tag 便于统一管理)。
**关联**: core-robots-meta、crawl-indexability-conflict;[head-elements.md](head-elements.md)

#### core-robots-meta
- 源表:warn · 权重 5。meta robots 或 X-Robots-Tag 含 noindex/nofollow/noarchive/noimageindex/none。这是清点项,不等于有错。建议优先级 medium。
**依据**: noindex=不在结果中显示;nofollow=不跟随本页链接;none=noindex+nofollow;noimageindex=不索引本页图片;noarchive 已不被 Google 使用(缓存链接功能已不存在)([robots meta 规范](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag))。核对 2026-10-18。
**判据**: 通过=指令都是刻意的。失败=误加在本该索引的页上。
**执行**: `AUDIT URL` 只报 `[CRITICAL] robots: noindex` 与 nosnippet;nofollow、none、noimageindex 与 googlebot meta 用 G6 补查。
**修复**: 误加的删除;刻意的归档,并把页面从审计分母剔除。
**关联**: core-robots-directive-mismatch、crawl-noindex-in-sitemap;[robots-txt-reference.md](robots-txt-reference.md)

#### core-nosnippet
- 源表:warn · 权重 7。meta 或 X-Robots-Tag 含 nosnippet 或 max-snippet:0。建议优先级 low。
**依据**: nosnippet 对网页、图片、Discover、AI Overviews、AI Mode 全部生效,并阻止内容作为 AI Overviews 与 AI Mode 的直接输入;max-snippet:0 等同 nosnippet([robots meta 规范](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag))。这是 Google 的口径,其他 AI 助手是否遵守各看其文档。核对 2026-10-18。
**判据**: 通过=无该指令,或刻意为之且已登记。失败=非刻意的 nosnippet。
**执行**: `AUDIT URL` 出现 `[WARN] robots: nosnippet(会限制 AI 特性)`;max-snippet:0 用 G6 查。只想隐藏片段时改用 `data-nosnippet`。
**修复**: 需要摘要与 AI 引用就删除;刻意的记录在案。
**关联**: core-robots-meta;[head-elements.md](head-elements.md) meta 全表

#### core-title-present
- 源表:`core-title-present` fail · 权重 25(无非空 `<title>`;内联 SVG 里的 title 不算);`core-title-length` warn/fail · 权重 1(30-60 字符)。长度是工具约定。建议优先级 high(缺失)/low(长度)。
**依据**: 每个页面都要有 `<title>`;"there's no limit on how long a `<title>` element can be",title link 按需截断以适配设备宽度,Google 还会从 h1、og:title、锚文本等来源自行生成([title link 文档](https://developers.google.com/search/docs/appearance/title-link))。**Google 无固定上限;本套件 site_audit 用 markets.json 的阈值作提示(en 为 <20 或 >60 字符)。** 像素宽度(~580px 一类)是工具约定。核对 2026-10-18。
**判据**: 通过=非空且描述本页。失败=缺失或空白。长度超出提示阈值只算提示。
**执行**: `AUDIT URL [--market xx]`:`[CRITICAL] title: 缺失`;`[WARN] title: N chars <20`;`[WARN] title: N chars 超上限 60`(其他市场按 markets.json 单位与上限,如 ja 32 全角)。
**修复**: 缺失就补每页唯一、描述性的标题;过长就把限定词挪进 description;避免堆砌与全站同模板标题。
**关联**: core-title-unique;[head-elements.md](head-elements.md)、[scoring-rubric.md](scoring-rubric.md) "不作为扣分依据"节

#### core-title-unique ⛏
- 源表:warn/fail · 权重 5 · 需 `--crawl`。不分大小写与多余空白比较;首个通过,其后同 title 的页 warn;无 title 的页 fail。建议优先级 high(模板级)/low(零星)。
**依据**: Google 要求避免重复或模板化的 `<title>`,每页要有区分本页内容的文字([title link 文档](https://developers.google.com/search/docs/appearance/title-link))。"数千页重复才触发质量算法"无官方出处,已删。核对 2026-10-18。
**判据**: 通过=每个可索引页 title 唯一。失败=同一 title 出现在 ≥2 个可索引页(分页、参数变体先按 canonical 处理)。
**执行**: `CRAWL` 后跑 J8,每行一个重复 title 及次数。
**修复**: 模板加页面级变量(分类名/页码/属性);真重复页用 canonical 或 301 合并。
**关联**: content-duplicate-description、content-duplicate-h1;[scoring-rubric.md](scoring-rubric.md)

#### core-description-present
- 源表:`core-description-present` fail · 权重 15(缺 meta description);`core-description-length` warn · 权重 1(120-160 字符)。长度是工具约定。建议优先级 medium(缺失)/low(长度)。
**依据**: Google 主要用页面内容生成摘要,只在 meta description 更准确时采用;"there's no limit on how long a meta description can be",按设备宽度截断;大站可程序化生成([snippet 文档](https://developers.google.com/search/docs/appearance/snippet))。**Google 无固定上限;本套件用 markets.json 的阈值作提示(en 为 <80 或 >155 字符)。** 核对 2026-10-18。
**判据**: 通过=有且描述本页。失败=缺失(源表 fail;建议优先级只到 medium)。长度只算提示。
**执行**: `AUDIT URL [--market xx]`:`[CRITICAL] description: 缺失`;`[WARN] description: N chars <80`;`[WARN] description: N chars 超上限 155`。
**修复**: 核心页手写(先给答案和行动点);模板页用真实字段拼装,别输出空串或全站同文案。
**关联**: core-title-present、content-duplicate-description;[head-elements.md](head-elements.md)

#### core-h1-present
- 源表:`core-h1-present` fail · 权重 15(无 h1);`core-h1-single` warn/fail · 权重 1(多于 1 个)。工具约定。建议优先级 medium(缺失)/low(多个)。
**依据**: 标题的数量与顺序对 Google 搜索无所谓,对屏幕阅读器有用([SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide));把主标题放进第一个可见 h1 有助 Google 选 title link([title link 文档](https://developers.google.com/search/docs/appearance/title-link))。"只能有一个 H1"不是 Google 规则。核对 2026-10-18。
**判据**: 通过=有一个描述主题的 h1。警告=缺失或多个(组件卡片各一个 h1 时)。
**执行**: `AUDIT URL`:`[CRITICAL] h1: 无 H1`(源表 fail,按建议优先级降档处理);`[WARN] h1: N 个 H1`。
**修复**: 每页一个主题 h1,与 title 呼应但不雷同;卡片标题降为 h2/h3。
**关联**: core-title-present、content-duplicate-h1;[semantic-html.md](semantic-html.md)

#### core-viewport [待核 ID]
- 名称/类型: viewport 缺失 —— issue · 优先级 high · 输出 CRITICAL(源表 `core-viewport-present` fail)
**这意味(what)**: 页面 head 没有 `<meta name="viewport">`。
**为什么(why)**: 缺 viewport 时移动浏览器按约 980px 桌面宽度渲染再缩放,字号、点击目标与布局都按桌面算。Google 自 2024-07-05 起只用智能手机版 Googlebot 抓取,"在移动设备上完全无法访问"的内容不再可索引([公告](https://developers.google.com/search/blog/2024/06/mobile-indexing-vlast-final-final.doc));缺 viewport 不等于无法访问,但移动体验与评估全部失真。规范值 `width=device-width, initial-scale=1`([head-elements.md](head-elements.md))。
**触发(trigger)**: head 内无 viewport meta 即 fail;配置不合规另归 mobile-viewport-config。
**不修的条件(caveat)**: 纯桌面工具页、仅登录后使用的后台可按内部系统豁免。
**修复(fix)**: 全站模板 head 注入 `<meta name="viewport" content="width=device-width, initial-scale=1">`;别用 user-scalable=no。
**关联(seealso)**: mobile-viewport-config、mobile-font-size;[head-elements.md](head-elements.md)、[mobile-seo.md](mobile-seo.md)

#### core-favicon [待核 ID]
- 名称/类型: favicon 缺失 —— warning · 优先级 low · 输出 CRITICAL(源表现行 `core-favicon-present` fail,权重 1;旧快照为 warn)
**这意味(what)**: head 无 `<link rel="icon">` 或 `rel="shortcut icon"`(源表:只有 apple-touch-icon 不算)。
**为什么(why)**: Google 自 2019-05 移动结果改版起在结果卡顶部显示网站图标与名称([公告](https://blog.google/products-and-platforms/products/search/new-design-google-search/));缺了只剩占位图标,浏览器标签页与书签同样。纯品牌露出项,与排名无关。
**触发(trigger)**: head 无 rel=icon/shortcut icon 即触发(源表);本套件另查根路径 /favicon.ico 是否 404。
**不修的条件(caveat)**: 内部系统/预发布环境可豁免。
**修复(fix)**: 出多尺寸 ICO 或 PNG/SVG + `<link rel="icon" sizes="…">`;apple-touch-icon 180px 另配;别引用外域图标。
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
**关联(seealso)**: perf-asset-compression、images-modern-formats;[LCP.md](LCP.md)

#### perf-asset-compression [待核 ID]
- 名称/类型: 文本资源未压缩(压缩家族) —— warning · 优先级 medium · 输出 WARN(源表 warn;渲染专属。perf-text-compression/perf-brotli 同构:载体与算法维度不同)
**这意味(what)**: content-length >2KB 的文本资源(HTML/CSS/JS/SVG/JSON)响应未带 gzip/Brotli 编码。
**为什么(why)**: 文本压缩是成本最低的传输优化之一;Brotli 静态预压又比 gzip 小一档。判定严格按 content-length:>2KB 才查,chunked 无长度不判——避免对流式响应误报,这是阈值纪律而非疏漏。
**触发(trigger)**: 1) 响应 content-length >2KB;2) 无 Content-Encoding: gzip/br 即 warn。家族其余规则同构:perf-text-compression(存在性)、perf-brotli(Brotli 特供)。
**不修的条件(caveat)**: 压缩不影响排名,然而 TTFB 之后的传输时间是 LCP 的直线组成,所以一般建议全站开启。但极小资源(<1KB)压缩收益趋零、CPU 反增的边缘场景可放过。
**修复(fix)**: 服务器/CDN 层开 gzip(底线)或 Brotli(静态资源构建期预压缩最优);验收看响应头。
**关联(seealso)**: perf-asset-cache-policy、perf-page-weight;[cwv-playbook.md](cwv-playbook.md)

#### perf-asset-cache-policy [待核 ID]
- 名称/类型: 缓存策略(缓存家族) —— warning · 优先级 medium · 输出 WARN(源表 warn;perf-asset-cache-policy 渲染专属:静态资源 max-age ≥1 小时;perf-cache-policy:带内容 hash 的资源 max-age=31536000)
**这意味(what)**: 静态资源 Cache-Control max-age <1 小时;或 URL 带内容 hash 的资源没设 max-age=31536000。
**为什么(why)**: 缓存决定回访与深层爬取的成本:短 max-age 每次访问都重下全部资源;内容 hash 文件名(hash 变=新 URL)天然免疫过期,理应一年期 immutable。CWV 字段数据(CrUX)也依赖真实用户侧缓存生效。
**触发(trigger)**: 1) 静态资源(CSS/JS/图/字体)max-age <3600s 即 warn;2) URL 含内容 hash(如 app.a3f9c2.js 形态)且 max-age ≠31536000 即 warn(perf-cache-policy)。
**不修的条件(caveat)**: 缓存头不影响排名,然而它决定重复访问的真实体验,所以一般建议分层:hash 资源一年+immutable、入口 HTML 短缓存。但无 hash 管道的 CSS 频繁热修时短缓存是运维取舍——先建 hash 管道再拉长缓存。
**修复(fix)**: 构建产物文件名带 hash,配 max-age=31536000, immutable;HTML 用 no-cache/短缓存;两者配合才安全。
**关联(seealso)**: perf-asset-compression;[cwv-playbook.md](cwv-playbook.md)

#### perf-render-blocking [待核 ID]
- 名称/类型: 渲染阻塞脚本 —— warning · 优先级 medium · 输出 WARN(源表 warn;head 内脚本无 async/defer)
**这意味(what)**: head 内的 `<script src>` 无 async/defer,HTML 解析必须停下等它下载执行。
**为什么(why)**: 同步脚本阻塞解析器,FCP/LCP 直接被拖;多个同步脚本串行时每个都是链上的一环。async(下载完即执行)与 defer(解析完执行)都归还解析权,语义上 defer 保序、async 抢跑。
**触发(trigger)**: 1) head 内 `<script src>` 无 async/defer 即 warn;2) 内联脚本位于外链同步脚本之后被连带卡住的判定口径[待核]。
**不修的条件(caveat)**: async/defer 不改变脚本对 SEO 的作用,然而它决定首屏时间,所以一般建议非关键脚本全 defer。但强顺序依赖的第三方(统计/AB)要 defer 不要 async,别一刀切。
**修复(fix)**: 非关键脚本 defer 或挪 body 尾;head 只留精简关键样式与资源提示(见 perf-lcp-hints);验收用渲染瀑布图。
**关联(seealso)**: perf-lcp-hints、js-initial-html;[rendering-seo.md](rendering-seo.md)

#### perf-lcp-hints [待核 ID]
- 名称/类型: LCP 图加载提示 —— warning · 优先级 high · 输出 WARN(源表 warn;LCP 图须 preload+fetchpriority=high)
**这意味(what)**: 页面 LCP 元素是图,却没有 `<link rel=preload as=image>` 且缺 fetchpriority="high"。
**为什么(why)**: LCP 图常经 CSS/字体之后才被发现(CSS background 声明的图尤甚),preload 让它进解析早期队列;fetchpriority=high 在带宽竞争时优先喂它。两个提示叠加是 LCP 优化的标准组合拳——LCP Good 阈值 ≤2.5s(见 [LCP.md](LCP.md))。
**触发(trigger)**: 1) 渲染判定 LCP 元素;2) 为图且无 preload 或无 fetchpriority=high 即 warn。
**不修的条件(caveat)**: 资源提示不影响排名,然而它们直接调度 LCP 资源的优先级,所以一般建议 LCP 图必配。但 LCP 元素是文字的页面不适用;preload 滥用(全页 preload)反而稀释优先级,只给这一张。
**修复(fix)**: `<link rel="preload" as="image" href="…hero.webp" fetchpriority="high">`,img 同步加 fetchpriority="high";LCP 图禁 lazy(见 images-lazy)。
**关联(seealso)**: images-lazy、perf-font-loading;[LCP.md](LCP.md)

#### perf-font-loading [待核 ID]
- 名称/类型: 字体加载策略 —— warning · 优先级 medium · 输出 WARN(源表 warn;font-display:swap)
**这意味(what)**: @font-face 声明缺 font-display:swap(或等价的防隐形策略)。
**为什么(why)**: 默认字体行为是 FOIT——字体下载完前文字不可见,慢字体=隐形文字=FCP/LCP 双输;swap 先用系统字渲染、字体到了再换,把"不可见"降级为"闪换"。
**触发(trigger)**: 渲染检查 @font-face 无 font-display:swap/optional 即 warn。
**不修的条件(caveat)**: swap 的双字 metrics 差异会小幅推高 CLS,然而换来的立即可见远大于抖动代价,所以一般建议 swap。但排版严苛页可选 optional(超时永用系统字);中文大字符集字体建议子集化后再 swap。
**修复(fix)**: @font-face 加 font-display:swap;关键字体 `<link rel=preload as=font crossorigin>`;中文字体按常用字切片。
**关联(seealso)**: perf-lcp-hints;[cwv-playbook.md](cwv-playbook.md)

#### perf-dom-size [待核 ID]
- 名称/类型: DOM 规模 —— warning · 优先级 medium · 输出 WARN(源表:DOM <800 过/800-1500 警/>1500 败,深度>32 警)
**这意味(what)**: 渲染后 DOM 元素节点数超 800(>1500 更重),或最大嵌套深度 >32。
**为什么(why)**: DOM 规模是 INP 与 CLS 的放大器:节点越多,样式计算/布局/交互响应越慢;深度 >32 几乎总是组件套组件叠出来的无语义容器,对语义树零贡献。
**触发(trigger)**: 1) 统计渲染后元素节点数:<800 过、800-1500 警、>1500 败;2) 最大嵌套深度 >32 即警。
**不修的条件(caveat)**: DOM 规模不(直接)影响 SEO,然而它给交互响应设上限,所以一般建议长列表分页/虚拟滚动。但数据密集页(财务表格)DOM 天然大,分页才是正解,不是硬删。
**修复(fix)**: 列表虚拟滚动或分页;拆装饰性嵌套容器;组件库治理"div 三明治"(每组件三层无语义 div)。
**关联(seealso)**: perf-page-weight;[cwv-playbook.md](cwv-playbook.md)

#### perf-resource-hygiene [待核 ID]
- 名称/类型: 资源卫生家族(六小条) —— warning · 优先级 low · 输出 WARN(源表各=warn)
**这意味(what)**: 六项资源层卫生任一命中:非 HTTP/2+(perf-http2 须 HTTP/2+);legacy polyfill 包(perf-legacy-javascript);同库多 URL 重复加载(perf-duplicate-js);暴露 sourceMappingURL(perf-source-maps 不得暴露);动画 GIF 该换 video(perf-video-for-animations,GIF→video 省 90%);css/js 压缩嫌疑(perf-minify 家族:内联查空白比/块注释;外链 >2KB 且 URL 无 .min. 标记=启发式嫌疑,恒 ≤warn)。
**为什么(why)**: 每项都是确定的字节/时间浪费:HTTP/1.1 队头阻塞限制同域并行;legacy JS 给现代浏览器发多余 polyfill;同库多 URL 既多下载又版本漂移;source map 公开暴露源码结构(偏安全面);GIF 做动画体积远大于等效视频(源表称 GIF→video 省 90%,工具口径)。单项轻,叠加是可量化的无谓传输。
**触发(trigger)**: 协议 <HTTP/2 → warn;脚本含 es5 时代 polyfill 特征 → warn;同库 ≥2 个不同 URL → warn;脚本带 sourceMappingURL → warn;动画 GIF[体积阈值源表未公布,待核] → warn;外链 css/js >2KB 且无 .min. → 恒 ≤warn(启发式;图片传输侧另见 perf-image-encoding:>100KB=warn、BMP/TIFF=fail,与 Images 节 images-modern-formats 同一事实两面)。
**不修的条件(caveat)**: 家族单项都不影响排名,然而叠起来是可量化的浪费,所以一般建议一次清完。但 source map 若仅鉴权后可访问,暴露面已受控,可降优先级。
**修复(fix)**: 全站 HTTP/2+;构建 target 现代浏览器砍 polyfill;依赖收敛单版本;source map 仅上传错误平台、产物剥离 sourceMappingURL;GIF→MP4/WebM;构建开 css/js 压缩输出 .min. 产物。
**关联(seealso)**: perf-asset-compression、perf-asset-cache-policy;[cwv-playbook.md](cwv-playbook.md)

#### perf-preconnect [待核 ID]
- 名称/类型: 关键源预连接 —— warning · 优先级 medium · 输出 WARN(源表 warn;perf-response-time 与 TTFB 同源阈值已吸收于 [LCP.md](LCP.md) 不重述)
**这意味(what)**: 页面加载关键的跨源资源(字体 CDN/图床/第三方关键脚本)没有 `<link rel="preconnect">`(或 dns-prefetch 兜底)。
**为什么(why)**: 每个新源要付 DNS+TCP+TLS 三段握手,关键资源跨源时握手时间前置吃进 LCP;preconnect 提前完成握手,资源请求一发出即进传输段。只该给关键少数源——滥用会占满连接池,反而拖慢其余资源。
**触发(trigger)**: 渲染瀑布中首屏关键资源(字体/LCP 图/关键 CSS)的 host 与页面 host 不同,且 head 无对应 `<link rel="preconnect" href="https://…">`(字体类带 crossorigin)即 warn。
**不修的条件(caveat)**: 资源提示不(直接)影响排名,然而它削掉的是 LCP 里最机械的握手段,所以一般建议关键跨源必配。但资源已同源聚合或全站 HTTP/3 的站点收益趋零,按瀑布图实测决定再配。
**修复(fix)**: head 顶部对字体/CDN 源加 preconnect(字体带 crossorigin);次级源用 dns-prefetch;可配合 103 Early Hints 由源站下发(见 [cwv-playbook.md](cwv-playbook.md))。
**关联(seealso)**: perf-lcp-hints、perf-font-loading;[cwv-playbook.md](cwv-playbook.md)、[LCP.md](LCP.md)

### Links(27 条,权重 8%)

内链 4xx=fail;外链可达性=warn(结果缓存);无内链=warn;nofollow 滥用=warn;泛化锚文本("click here"/"read more"/"link")=warn;`links-depth`(**点击距离 ≤3**,crawl);死端页(无出链)=warn;HTTPS 页链 HTTP=warn;**外链 >100=warn**;空/javascript:/畸形 href=warn;tel:/mailto: 格式=warn;重定向链(**1-2 跳=warn,≥3=fail**);`links-localhost`(127.0.0.1=fail)/`links-local-file`(file://=fail);断锚点(#id 无匹配)=warn;`links-onclick`(onclick 导航替代 href=warn);href 首尾空白=warn;非 HTTP 协议(ftp:/intent:/chrome:)=warn;**crawl 专属入链族 8 条**:inbound-all-nofollow(全 nofollow=零权重流入,洞见级)/inbound-mixed-follow(有follow有nofollow=不一致)/inbound-low-quality(入链全 nofollow 或全来自被 canonical 走的页)/inbound-anchor-text(全部入链锚文本<2 字符或泛化)/nofollow-internal(同主机链接禁 nofollow)/weak-inbound(**非入口页须 >1 条 dofollow 入链**)/chrome-inbound(**至少 1 条入链在 nav/header/footer 之外**——正文链才算票)/orphan-pages(真孤儿由 crawl-sitemap-orphan-urls 配合判)。

**解释层(16 条;ID 未公布原文的标 [待核];入链族 8 条的 5 条并入 links-weak-inbound/links-chrome-inbound 陈述)**

#### links-broken-internal
- 源表:warn/fail · 权重 1。逐个内链目标 HEAD(失败再 GET):404、410、5xx=fail;无应答=warn;其他 4xx 通过。工具约定。建议优先级 high。
**依据**: 站内部分 URL 返回 404 本身不会让站点在 Google 搜索中受损([Google 2011 博文](https://developers.google.com/search/blog/2011/05/do-404s-hurt-my-site));Google 不索引返回 4xx 的 URL([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors))。修它是为了用户路径与内链指向有效页。"撞 404 会降低抓取意愿"无出处,已删。核对 2026-10-18。
**判据**: 通过=内链目标全部 2xx/3xx。失败=任一目标 404/410/5xx。刻意 410 的下线页不算错,但内链应删除。
**执行**: `CRAWL` 后跑 J6,每行"来源页 -> 死链";site_audit 不检查链接目标。
**修复**: 目标还在就修 href;目标没了就 301 到最近亲页或删链接;批量死链先查迁移映射表。
**关联**: crawl-pagination-broken、i18n-hreflang-to-broken;[link-architecture-patterns.md](link-architecture-patterns.md)、[http-status-codes.md](http-status-codes.md)

#### links-redirect-chains
- 源表:warn/fail · 权重 1。抽样至多 20 个内链目标:1-2 跳=warn,≥3 跳=fail。工具约定。建议优先级 medium。
**依据**: Googlebot 一般最多跟 10 跳,网址检查工具不跟随重定向([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors))。1-2/3 跳的分档是工具约定。内链零跳直指最终 URL 省掉每次访问的往返。核对 2026-10-18。
**判据**: 通过=内链直指 200 页。警告=1-2 跳。失败=≥3 跳(本套件 `REDIR`:>2 跳 WARN,>5 跳 CRITICAL)。
**执行**: `CRAWL` 后跑 J7 列出指向重定向的内链;单个目标用 `REDIR 目标URL` 看链长。
**修复**: 内链模板直指最终 URL;服务器层把链条改写为一步到位。单跳 http→https 或加尾斜杠可排后修。
**关联**: redirect-loop、crawl-canonical-redirect;[redirects-canonical.md](redirects-canonical.md)

#### links-depth
- 源表:warn/fail · 权重 4 · 需 `--crawl`。真实点击距离(从爬取入口算);修复建议是重要页 3 击以内。工具约定。建议优先级 medium。
**依据**: 无搜索引擎公布的点击深度阈值;Google 只说链接是发现页面的主要方式,在意的页面至少要有一个站内链接([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable))。"≤3"是工具约定。核对 2026-10-18。
**判据**: 通过=重要页深度 ≤3。失败=重要页深度 >3(存档、法律页可深)。
**执行**: `CRAWL` 后跑 J5,或看 `GRAPH` 的深度直方图(>3 层占比);深度从种子 URL 按内链 BFS 计算。
**修复**: 重要页从导航/分类页/相关推荐多点接入;扁平化信息架构,而不是往首页堆链接。
**关联**: crawl-isolated-url、crawl-sitemap-orphan-urls;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-localhost
- 源表:fail · 权重 8。链向 localhost、127.0.0.1、0.0.0.0 或常见开发端口(:3000、:8080、:5173 等);同族 `links-local-file`(fail · 权重 8)抓 file:// 与 /Users/、/home/、C:\ 开头的 href/src。工具约定。建议优先级 high。
**依据**: 这类地址在访客与爬虫端都不可达,属发布事故;无需搜索引擎规则佐证。核对 2026-10-18。
**判据**: 通过=无开发环境地址。失败=任一 href/src 指向上述地址。
**执行**: G5 有输出即失败;全站对 `CRAWL` 产出的 URL 清单循环跑 G5。
**修复**: 查环境变量与绝对 URL 拼装基准;上线检查清单加 localhost/file:// 扫描。
**关联**: links-broken-internal

#### links-anchor-generic [待核 ID]
- 名称/类型: 泛化锚文本 —— warning · 优先级 medium · 输出 WARN(源表 warn;"click here"/"read more"/"link")
**这意味(what)**: 站内链接的锚文本是泛化词——click here/read more/link 一类,不含目标页主题信息。
**为什么(why)**: 锚文本是引擎理解目标页相关度的第一信号,泛化锚等于把票投给"一个叫 click here 的页面";无障碍侧,屏幕阅读器用户常脱离上下文按链接列表浏览,一列 "read more" 完全不可用。批量泛化锚几乎总是模板省事,不是文案选择。
**触发(trigger)**: 锚文本命中泛化词表(click here/read more/link/more/here 等[词表源表未公布,待核])且为普通文本链即 warn;图标链接的可访问名(alt/aria-label)即其锚文本,同口径计。
**不修的条件(caveat)**: 锚文本不(直接)决定目标页排名,然而它是零成本的相关度信号,所以一般建议锚含目标主题词。但 CTR 导向的行动按钮("免费试用")是转化文案,别为 SEO 破坏——链接补 aria-label 带上主题即可。
**修复(fix)**: 模板把目标页标题注入锚("阅读:SEO 审计入门");纯图标链接补 aria-label;全站泛化锚 lint 进 CI。
**关联(seealso)**: links-weak-inbound;[link-architecture-patterns.md](link-architecture-patterns.md)、[semantic-html.md](semantic-html.md)

#### links-nofollow-internal [待核 ID]
- 名称/类型: 内链 nofollow —— warning · 优先级 medium · 输出 WARN(源表 warn;同主机链接禁 nofollow)
**这意味(what)**: 指向同主机的内链被加了 rel=nofollow。
**为什么(why)**: nofollow 的语义是"不为这个链接背书",用在自家内链上是自我否定;且 Google 2009 年公开说明,nofollow 链接分走的那份 PageRank 直接蒸发,不再转给同页其余链接([Matt Cutts 博文](https://www.mattcutts.com/blog/pagerank-sculpting/),时任 Google 反垃圾负责人;改动早于该文一年多)——"用内链 nofollow 调节权重流向"的动机从起点就不成立(口径见 [deprecated-signals.md](deprecated-signals.md))。剩下的成因几乎只有误加:CMS 默认、UGC 模板全局套用。
**触发(trigger)**: 同域 `<a>` 带 rel=nofollow 即 warn。
**不修的条件(caveat)**: 内链 nofollow 不带来任何收益,然而删除它也无即时排名变化(权重会计在引擎内部),所以一般建议作为卫生项清理。但 UGC 区(论坛/评论)给用户发布的外链加 nofollow/ugc 是反 spam 标准做法,不属"内链"。
**修复(fix)**: 模板移除内链 nofollow;UGC 外链区保留 ugc/nofollow;抓取预算问题走 robots.txt,索引控制走 noindex/canonical。
**关联(seealso)**: links-external-many、url-search-indexed;[robots-txt-reference.md](robots-txt-reference.md)

#### links-external-many [待核 ID]
- 名称/类型: 外链过多 —— warning · 优先级 low · 输出 WARN(源表 warn;外链 >100)
**这意味(what)**: 单页指向外部的链接超过 100 条。
**为什么(why)**: 100 是早年 Google 指南里的经验数,现行 Google 链接文档没有数量上限([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable));但外链爆炸仍是链接农场/资源页失控的形态信号,且链接权重按出链数稀释——100+ 出链时每条(含你想推的内链)分到的投票趋近于零。
**触发(trigger)**: 统计页内出站(跨域)`<a href>` 数;>100 即 warn(nofollow 是否计入的口径[待核])。
**不修的条件(caveat)**: 外链数量不影响本页排名,然而它稀释每条链接的相对价值,所以一般建议长资源页分栏分页。但学术引文页/目录站的百条外链是内容真实形态,分页反而伤可用性。
**修复(fix)**: 长资源页按主题分页;非核心外链区 nofollow/ugc 收口;付费与联盟位用 rel=sponsored。
**关联(seealso)**: links-nofollow-internal;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-dead-end [待核 ID]
- 名称/类型: 死端页 —— warning · 优先级 medium · 输出 WARN(源表 warn;无出链)
**这意味(what)**: 页面没有任何 follow 出链——用户与爬虫到这里都走不动了。
**为什么(why)**: 死端页截断浏览路径(用户只能回退)与爬行路径(引擎无法从它继续发现);与孤立 URL(无入链)互为镜像——一个进不来,一个出不去。转化终点页(支付成功/退订确认)是唯一常见合理形态。
**触发(trigger)**: 页面 follow 出链计数=0 即 warn(爬取入口与纯工具页的豁免口径[待核])。
**不修的条件(caveat)**: 死端不(直接)影响本页排名,然而它浪费一次"带用户/引擎去别处"的机会,所以一般建议补相关推荐与返回路径。但流程终点页刻意零出链是转化设计,记豁免。
**修复(fix)**: 补相关内容推荐/面包屑/返回分类;结算页类模板确认其 noindex 与出链策略是刻意设计。
**关联(seealso)**: crawl-isolated-url、links-depth;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-weak-inbound [待核 ID]
- 名称/类型: 弱入链(入链族核心) —— warning · 优先级 medium · 输出 WARN(源表 warn;crawl 专属;非入口页须 >1 条 dofollow 入链)
**这意味(what)**: 非爬取入口的页面只有 ≤1 条 dofollow 入链——技术上可达,权重与健壮性上贫血。
**为什么(why)**: 单链页在链接图上是"叶子":首页一改版挪掉那条链接,它就掉成孤立页;权重流入也只有一条窄通道,排名天花板低。本规则是入链族 8 条的核心判定,同族同构维护:inbound-all-nofollow(全 nofollow=零权重流入,洞见级)/inbound-mixed-follow(follow·nofollow 混杂)/inbound-low-quality(入链全来自被 canonical 走的页)/inbound-anchor-text(全部入链锚 <2 字符或泛化)——四条都是对同一入链图不同切面的质量计数,阈值见本节表,不逐条扩写。
**触发(trigger)**: 1) crawl 构建 dofollow 入链图;2) 非入口页 dofollow 入链数 ≤1 即 warn。
**不修的条件(caveat)**: 入链数不(直接)决定排名(质量重于数量),然而 1 条链是脆弱性指标,所以一般建议关键页 ≥2-3 条来自不同区域。但刚发布未及内链的新页与法律页是过渡态/低需求态,可豁免。
**修复(fix)**: 分类页/相关推荐/正文上下文多点接入;重要页至少导航与正文各一条(见 links-chrome-inbound)。
**关联(seealso)**: links-chrome-inbound、crawl-isolated-url;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-chrome-inbound [待核 ID]
- 名称/类型: 仅有导航区入链 —— warning · 优先级 medium · 输出 WARN(源表 warn;crawl 专属;至少 1 条入链在 nav/header/footer 之外)
**这意味(what)**: 页面的全部入链都来自导航 chrome(导航/页头/页脚),没有任何一条来自正文区。
**为什么(why)**: 导航链接全站同款,引擎对其的评估趋于"模板信号"而非"编辑性投票";正文内语境链接才是"该主题下值得推荐"的表达,也是相关度传递者。全 chrome 入链的页面=只被模板带到,没被任何内容论证过。
**触发(trigger)**: 1) 入链图标注每条入链来源区域(nav/header/footer vs 正文);2) 正文区入链=0 即 warn。
**不修的条件(caveat)**: 正文入链不影响排名本身,然而它是相关度信号的载体,所以一般建议核心页有语境内链。但政策/法务页(无需主题论证)全 chrome 入链是正常形态;相关推荐模块算不算正文区[待核:源表区域划分口径未公布]。
**修复(fix)**: 在相关正文里以描述性锚接入(锚文本规范见 links-anchor-generic);让内容作者而非仅模板产出内链。
**关联(seealso)**: links-weak-inbound、links-anchor-generic;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-no-internal [待核 ID]
- 名称/类型: 无内链 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 该 URL 的页面上没有任何指向本站其他页面的链接——出链全空或只剩外链。
**为什么(why)**: 爬虫沿内链爬行,无内链出边的页面是爬行路径终点,站内再深一层的内容失去一条发现通道;用户读完即"离开站点",相关推荐与转化路径全部缺席。与 links-dead-end 互补:那条判"零出链",本条把"有出链但无一是站内"也纳入——把流量送出门却不留后路。
**触发(trigger)**: 页面同域 follow `<a href>` 计数=0 即 warn。
**不修的条件(caveat)**: 内链数不(直接)影响本页排名,然而它决定爬行延续与用户动线,所以一般建议补相关内容入口。但纯外链引流的工具落地页/第三方托管的致谢页可合理保持。
**修复(fix)**: 补相关内容模块/面包屑/回到分类入口;模板保证每页有站内链接区块。
**关联(seealso)**: links-dead-end、links-depth;[link-architecture-patterns.md](link-architecture-patterns.md)

#### links-external-reachability [待核 ID]
- 名称/类型: 外链可达性(含 HTTPS 页链 HTTP) —— warning · 优先级 low · 输出 WARN(源表 warn;外链可达性结果缓存;HTTPS 页链 HTTP=warn 同族)
**这意味(what)**: 页面指向外部的链接目标不可达(4xx/5xx/超时),或 HTTPS 页面上仍用 http:// 外链。
**为什么(why)**: 死外链伤用户信任(点出去 404),也标记页面疏于维护;HTTPS 页混 http 外链本身不构成混合内容(仅子资源才算),但形态不一致在目标站完成 https 化后容易变成断链。外链判定带结果缓存,避免全站审计反复打同一目标。
**触发(trigger)**: 1) 请求全部跨域 href(缓存结果);4xx/5xx/超时即 warn;2) 页面 HTTPS 而 href 为 http:// 即 warn。
**不修的条件(caveat)**: 外链目标不受你控制——对方改版删页你这边全站误报,所以一般建议批量检测后只修高频引用的死外链。但支撑 E-E-A-T 的权威引用页(eeat-citations)值得保持零死链,优先级另计。
**修复(fix)**: 死外链换网页存档链接或替代来源;http 外链统一改 https(目标支持时);引用型内容的死链优先于资源页死链。
**关联(seealso)**: links-broken-internal、eeat-citations;[http-status-codes.md](http-status-codes.md)

#### links-malformed-href [待核 ID]
- 名称/类型: 畸形 href 家族 —— warning · 优先级 low · 输出 WARN(源表各=warn:空/javascript:/畸形 href;tel:/mailto: 格式;非 HTTP 协议 ftp:/intent:/chrome:;href 首尾空白)
**这意味(what)**: `<a>` 的 href 是空串、javascript: 伪协议或畸形值;tel:/mailto: 格式错;scheme 为 ftp:/intent:/chrome: 等非 HTTP(S) 协议;或首尾带空白字符。
**为什么(why)**: 空 href 与 javascript: 链接对引擎是不可跟随的假链接——权重与发现都不传递,键盘用户聚焦过去也无处可去;tel:/mailto: 格式错在移动端直接呼叫/发信失败;异形协议链接多数是模板变量泄漏。首尾空白则是"能工作但制造变体 URL"的卫生问题。
**触发(trigger)**: 1) href 空串或 javascript: 伪协议即 warn;2) tel: 不匹配 `tel:+数字` 形态、mailto: 无合法邮箱即 warn;3) scheme ∈ ftp:/intent:/chrome: 等非 HTTP(S) 即 warn;4) href 首尾含空白即 warn。
**不修的条件(caveat)**: 伪协议链接不(直接)影响排名,然而它把交互做成引擎与部分用户到不了的门,所以一般建议真导航一律用可跟随 href。但 mailto:/tel: 本身合法,只查格式;确需 JS 行为的元素正解是 `<button>`,不是豁免。
**修复(fix)**: 真导航用真实 URL;JS 行为改 button+事件;tel/mailto 按规范格式输出;模板输出 href 时 trim。
**关联(seealso)**: links-onclick、i18n-hreflang-to-broken;[semantic-html.md](semantic-html.md)

#### links-broken-anchor [待核 ID]
- 名称/类型: 断锚点 —— warning · 优先级 low · 输出 WARN(源表 warn;#id 无匹配)
**这意味(what)**: 链接的 fragment(#section)在目标页里找不到对应 id/命名锚点。
**为什么(why)**: 锚点链接是长页深链与 AI 引用定位的常用形态;目标页重构后 heading id 改名,来源页的 fragment 全部落空——用户被丢在页顶以为内容不存在。同页 fragment 直接查本页 DOM,跨页 fragment 要抓目标页才能判。
**触发(trigger)**: 1) 提取带 fragment 的 href;2) 在目标页(本页或已抓取缓存)DOM 查 id/`<a name>` 匹配;3) 无匹配即 warn。
**不修的条件(caveat)**: 断锚点不(直接)影响 SEO,然而它把"精确深链"降级为"页顶落点",所以一般建议高价值锚点链保持有效。但第三方页面的 fragment 你无法控制,只修站内互链与自有分发渠道。
**修复(fix)**: 目标页恢复旧 id(加别名)或改引用方 fragment;CMS 生成 heading 时输出稳定 slug id,别用序号。
**关联(seealso)**: links-broken-internal、links-onclick;[semantic-html.md](semantic-html.md)

#### links-onclick [待核 ID]
- 名称/类型: onclick 导航 —— warning · 优先级 medium · 输出 WARN(源表 warn;onclick 导航替代 href)
**这意味(what)**: 用元素 onclick 事件做页面导航——`<a>` 无真实 href(或 href="#" 配 onclick 跳转)。
**为什么(why)**: 引擎与多数不执行 JS 的爬虫只认 href:onclick 导航对它们是死路,后续页面失去这条发现路径;中键/右键新开标签、悬停预览、状态栏 URL 全部失效,键盘与辅助技术同样受损。与 [rendering-seo.md](rendering-seo.md) 的口径一致:导航必须在初始 HTML 的可跟随 href 里。
**触发(trigger)**: `<a>` 无 href 或 href="#"/javascript: 且带 onclick 属性(含常见前端路由跳转特征)即 warn。
**不修的条件(caveat)**: onclick 导航不(直接)惩罚,然而它把不执行 JS 的访问者挡在门外,所以一般建议 href 写真实目标 URL、JS 只做增强。但 SPA 视图切换用真实 href+pushState 的渐进增强是正解形态,不是豁免。
**修复(fix)**: `<a href="/real/url">` 为主体,onclick preventDefault 仅做无刷新增强;纯动作元素(提交/展开)改 button。
**关联(seealso)**: links-malformed-href、js-content-dependency;[rendering-seo.md](rendering-seo.md)、[semantic-html.md](semantic-html.md)

#### links-nofollow-external [待核 ID]
- 名称/类型: 外链 nofollow 滥用 —— warning · 优先级 low · 输出 WARN(源表 warn;nofollow 滥用;与 links-nofollow-internal 互补)
**这意味(what)**: 站内出站链接被大面积加 rel=nofollow——包括自然引用的权威来源、合作伙伴等本应正常投票的链接。
**为什么(why)**: nofollow 的语义是"不为该链接背书":全站外链一刀切 nofollow 等于声明"我引用的一切都不算数"——E-E-A-T 的引用信号(eeat-citations)同时被自己关掉。正当用法只有三类:付费/赞助(rel=sponsored)、UGC(rel=ugc)、不信任目标。与 links-nofollow-internal 互补:一个错在自我否定,一个错在过度防御。
**触发(trigger)**: 跨域 `<a>` 带 rel=nofollow(不含 sponsored/ugc)占比超出自然水平(阈值源表未公布[待核]),或权威引用源(.gov/.edu/论文)被 nofollow 即 warn。
**不修的条件(caveat)**: nofollow 外链不影响本页排名,然而它同时放弃引用背书与链接语义准确性,所以一般建议只给三类正当用途。但法务要求全站外链免责的场景(金融合规)可整体保留,报告记豁免。
**修复(fix)**: 自然引用去 nofollow;付费位改 sponsored;UGC 区改 ugc;CMS 若默认全局加 nofollow,改模板开关。
**关联(seealso)**: links-nofollow-internal、eeat-citations;[robots-txt-reference.md](robots-txt-reference.md)、[deprecated-signals.md](deprecated-signals.md)

### Images(14 条,权重 8%)

alt 缺失=fail;alt 泛化("image"/文件名)=warn;alt 长度 **5-125 字符**=warn;宽高属性缺失=warn(防 CLS);below-fold 须 `loading="lazy"`=warn;现代格式(WebP/AVIF 比 JPEG/PNG 小 30-50%)=warn;体积=warn;srcset 响应式=warn;图片 404=fail;figure 缺 figcaption=warn;文件名(IMG_001.jpg 坏/red-running-shoes.jpg 好)=warn;**内联 SVG >5KB 应外链**=warn;picture 缺 img 回退=fail;内容图用 CSS background(引擎读不到)=warn。

**解释层(6 条;ID 未公布原文,标 [待核])**

#### images-alt-present
- 源表:`images-alt-present` fail · 权重 20(img 无 alt 属性);`images-alt-length` warn/fail · 权重 6(>125 字符 warn,>250 fail,无下限);泛化 alt 归 `images-alt-quality`。长度是工具约定。建议优先级 high(缺失)/low(长度)。
**依据**: Google 结合 alt、计算机视觉和页面内容理解图片,alt 是最重要的图片元数据,也服务屏幕阅读器;不要往 alt 堆关键词([图片 SEO 文档](https://developers.google.com/search/docs/appearance/google-images))。Google 没有 alt 长度规则。装饰图用空 alt 是 W3C 推荐做法,不是缺失。核对 2026-10-18。
**判据**: 通过=内容图有描述性 alt,装饰图 alt=""。失败=内容图无 alt 属性。长度超 125 只算提示。
**执行**: `AUDIT URL` 出现 `[WARN] images: alt 缺失 N/M`(超过 20% 才报,且把 alt="" 也算缺失,需人工剔除装饰图);精确查无 alt 属性的图:`curl -s URL | grep -oiE '<img[^>]*>' | grep -viE ' alt='`。
**修复**: 内容图写"图里有什么";装饰图用空 alt;复杂图表用 figcaption 写长描述。
**关联**: images-alt-generic;[semantic-html.md](semantic-html.md)

#### images-alt-generic [待核 ID]
- 名称/类型: 泛化/文件名式 alt —— warning · 优先级 low · 输出 WARN(源表 warn;"image"/文件名)
**这意味(what)**: 内容图的 alt 是泛化词("image"/"photo"/"图片")或直接复述文件名(img001),没有描述图内内容。
**为什么(why)**: 泛化 alt 对图片搜索与屏幕阅读器约等于没有:图片搜索靠 alt 理解图意,SR 用户听到 "image" 毫无信息。与 images-alt-present(缺失/长度)同族互补:那条管"没写/写多长",本条管"写了但零信息量"。
**触发(trigger)**: 1) alt 值命中泛化词表(image/photo/picture 等[词表源表未公布,待核])即 warn;2) alt 与 src 文件名(去扩展名)相同即 warn;3) 装饰图空 alt 不判(正确做法)。
**不修的条件(caveat)**: alt 文案质量不(直接)影响网页排名,然而决定图片搜索的匹配面与无障碍信息量,所以一般建议写"图里有什么"。但 logo 类小图的短描述(alt="ExampleCorp 商标")属可接受形态。
**修复(fix)**: 按图内容写名词性描述(对象+动作+语境);别把关键词堆进 alt(那归 content-keyword-stuffing);模板无法自动生成时留空待人工补,也别输出文件名。
**关联(seealso)**: images-alt-present;[semantic-html.md](semantic-html.md)、[image-search-seo.md](../content/image-search-seo.md)

#### images-dimensions [待核 ID]
- 名称/类型: 宽高属性缺失(尺寸家族) —— warning · 优先级 medium · 输出 WARN(源表 warn;防 CLS)
**这意味(what)**: `<img>` 缺 width/height 属性(也无 aspect-ratio 兜底),浏览器无法预留占位。
**为什么(why)**: 缺宽高时图片到位后布局重排,直接推高 CLS(阈值见 [cwv-playbook.md](cwv-playbook.md));现代浏览器按属性计算宽高比,加载前就留好空间。本家族其余规则同构(缺信号 warn 档):srcset 响应式缺失=warn、figure 缺 figcaption=warn、文件名无描述性(IMG_001.jpg 坏/red-running-shoes.jpg 好)=warn、内联 SVG >5KB 应外链=warn;picture 缺 img 回退=**fail** 档(不支持环境整图消失);图片 404=**fail** 档(与 links-broken-internal 同构的断链家族)。
**触发(trigger)**: 1) `<img>` 无 width/height 且无 CSS aspect-ratio 即 warn;2) 家族各小条按上列阈值判。
**不修的条件(caveat)**: 宽高不(直接)影响 SEO,然而它是 CLS 的最大可控因子之一,所以一般建议模板全配。但已用 CSS aspect-ratio 或 srcset+sizes 覆盖同需求的场景,属性缺失可视为等价实现。
**修复(fix)**: CMS/构建管道存原始尺寸并输出 width/height;动态尺寸图用 aspect-ratio;响应式配 srcset+sizes;figure 配 figcaption。
**关联(seealso)**: images-modern-formats、perf-dom-size;[cwv-playbook.md](cwv-playbook.md)

#### images-modern-formats [待核 ID]
- 名称/类型: 老旧图片格式/传输体积 —— warning · 优先级 low · 输出 WARN(源表 warn;WebP/AVIF 比 JPEG/PNG 小 30-50%;与 Performance 节 perf-image-encoding 同一事实的两面)
**这意味(what)**: 页面图片仍是 JPEG/PNG 老格式且未提供 WebP/AVIF(协商或 picture 回退),或单图传输体积过大。
**为什么(why)**: WebP/AVIF 同画质小 30-50%(源表口径),省下的字节直接改善 LCP 与页面总重。perf 侧同源规则 perf-image-encoding(渲染专属)判**传输 >100KB=warn、BMP/TIFF=fail**——本条看"格式供给",那条看"实际传输",命中其一就该动手。
**触发(trigger)**: 1) img src 无 .webp/.avif 且响应无格式协商(Accept/Vary)即 warn;2) 渲染口径:单图传输 >100KB=warn、BMP/TIFF=fail。
**不修的条件(caveat)**: 格式不影响图片相关性判定,然而传输体积是 LCP 的一半战场,所以一般建议全站切现代格式。但图片本就 <30KB 且 CMS 无转换能力的场景,收益排序靠后。
**修复(fix)**: 构建/CDN 层自动转 WebP/AVIF+picture 回退;大图压到展示分辨率;截图类 PNG 走有损压缩;验收看单图传输量。
**关联(seealso)**: perf-page-weight、images-lazy;[cwv-playbook.md](cwv-playbook.md)、[image-search-seo.md](../content/image-search-seo.md)

#### images-lazy [待核 ID]
- 名称/类型: loading="lazy" 家族 —— warning · 优先级 medium · 输出 WARN(源表 warn;below-fold 须 lazy;首屏图禁 lazy=perf-lazy-above-fold)
**这意味(what)**: 折叠线以下的图没加 loading="lazy",或首屏图(尤其 LCP 图)反而加了 lazy。
**为什么(why)**: 两个方向伤同一指标:下页图不 lazy=全部抢首屏带宽,LCP 被非关键图拖慢;首屏图 lazy=LCP 资源被延迟加载。原生 loading="lazy" 主流浏览器均支持,零脚本成本,属于"一行属性换半个 LCP"的修复。
**触发(trigger)**: 1) below-fold 图无 loading="lazy" 即 warn;2) 首屏/LCP 图带 loading="lazy" 即 warn(Performance 侧 perf-lazy-above-fold)。
**不修的条件(caveat)**: lazy 属性不影响图片索引(仍会被抓取),然而它调度首屏带宽,所以一般建议 below-fold 全配。但首屏边缘图(是否在视口随设备变化)宁可不 lazy——误 lazy 的白屏代价大于误加载的带宽代价。
**修复(fix)**: 模板按位置分流:首屏/LCP 图 eager+fetchpriority=high(见 perf-lcp-hints),其余 lazy;首屏判定以常见移动视口为准。
**关联(seealso)**: perf-lcp-hints、perf-page-weight;[cwv-playbook.md](cwv-playbook.md)

#### images-css-background [待核 ID]
- 名称/类型: 内容图用 CSS background —— warning · 优先级 medium · 输出 WARN(源表 warn;引擎读不到)
**这意味(what)**: 承载内容信息的图(产品图/文章配图/图表)用 CSS background-image 呈现,而非 `<img>`。
**为什么(why)**: 引擎把 background 归为样式,不作为内容图索引——图片搜索完全收不到,alt/宽高/srcset/lazy 一整套图片优化全部不可用。背景图的合理域是装饰;内容图的合理域是 img(或 picture/svg)。
**触发(trigger)**: 主内容区的信息图走 background-image(URL 提取自内联样式与样式表)且无对应 img 语义即 warn。
**不修的条件(caveat)**: 纯装饰背景(渐变/纹理/氛围图)用 background 是正确做法,不判;只有当图承载内容语义(用户需要"看懂"它)时才构成问题——判定依赖"信息图"识别,命中后建议人工复核再改。
**修复(fix)**: 内容图改 `<img>` 带 alt/宽高/现代格式;装饰保留 background;图表类用 svg+figcaption 或 img+长描述。
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
**关联(seealso)**: security-headers、security-tls;[validation-guide.md](validation-guide.md)

#### security-headers [待核 ID]
- 名称/类型: 安全响应头家族 —— warning · 优先级 medium · 输出 WARN(源表各=warn:HSTS `max-age=31536000; includeSubDomains`/CSP/X-Frame-Options(DENY/SAMEORIGIN)/nosniff/Permissions-Policy/Referrer-Policy(strict-origin-when-cross-origin)/COOP(`same-origin`,防 tabnabbing))
**这意味(what)**: 七个安全响应头任一缺失:HSTS、CSP、X-Frame-Options、X-Content-Type-Options(nosniff)、Permissions-Policy、Referrer-Policy、COOP。
**为什么(why)**: 每个头各管一面:HSTS 防协议降级剥离(缺了首访 http 可被中间人劫持);CSP 约束脚本注入面;X-Frame-Options 防 clickjacking 嵌套;nosniff 防 MIME 嗅探错配执行;Permissions-Policy 收 API 权限;Referrer-Policy 控引荐信息外泄;COOP(same-origin)防 tabnabbing 类跨窗引用。SEO 侧关联是间接的:可被任意嵌套/注入的页面不是引擎信任的展示形态。CSP 的有效性另由 security-csp-xss 深化('unsafe-inline' 无 nonce=不设防;无 CSP 时按权重 0 报,避免与缺失双重扣),security-trusted-types 仅对已设 CSP 的站评 `require-trusted-types-for 'script'`。
**触发(trigger)**: 响应头逐一断言存在与推荐值(照抄源表:HSTS `max-age=31536000; includeSubDomains`;XFO DENY/SAMEORIGIN;RP strict-origin-when-cross-origin;COOP same-origin);缺失即 warn。
**不修的条件(caveat)**: 安全头不(直接)影响排名,然而它们是站点治理质量的可见面与真实攻击面的闸门,所以一般建议按 C28 清单补齐。但 CSP 要灰度上线(先 Report-Only 观察),一次性 enforce 打挂第三方脚本反成事故。
**修复(fix)**: 按 [validation-guide.md](validation-guide.md) C28 五头起步(HSTS/CSP/nosniff/XFO/RP);CSP 走 Report-Only 灰度;CDN/网关层统一注入。
**关联(seealso)**: security-https、technical-content-type;[validation-guide.md](validation-guide.md)

#### security-tls [待核 ID]
- 名称/类型: TLS 版本与证书 —— warning/issue · 优先级 high · 输出 WARN/CRITICAL(源表:SSL 到期=warn/fail;TLS 须 1.2+,1.0/1.1=warn/fail)
**这意味(what)**: TLS 证书临期或已过期,或协议版本低于 1.2(1.0/1.1)。
**为什么(why)**: 过期证书让全部主流浏览器弹全页警告——流量断崖,引擎侧也随之抓取失败;TLS 1.0/1.1 已被 IETF 废弃且被主流浏览器禁用,老协议同时是降级攻击面。warn/fail 分型按临期程度与协议版本[待核:常见分型为临期=warn、已过期=fail]。
**触发(trigger)**: 1) 证书 notAfter 进入预警窗(窗口阈值源表未公布[待核])→ warn;已过期 → fail;2) 协商协议 <TLS1.2 → warn/fail。
**不修的条件(caveat)**: 证书与协议不(直接)影响内容排名,然而过期即全站不可达,是可用性事故级,所以一般建议自动续期+到期告警。但多证书/多边缘节点的站先盘点覆盖面再统一切 1.2+,避免漏节点造成部分用户不可达。
**修复(fix)**: ACME 自动续期(如 cert-manager);notAfter 双阈值告警(30/7 天);TLS 下限 1.2(逐步 1.3),关闭 1.0/1.1。
**关联(seealso)**: security-https;[validation-guide.md](validation-guide.md)

#### security-cookies [待核 ID]
- 名称/类型: Cookie 旗标与寿命 —— warning · 优先级 medium · 输出 WARN/CRITICAL(源表:三旗 Secure/HttpOnly/SameSite=warn/fail;寿命 >400 天=warn)
**这意味(what)**: Cookie 缺 Secure/HttpOnly/SameSite 旗标,或 Set-Cookie 的 max-age/expires 超过 400 天。
**为什么(why)**: 三旗各堵一类:Secure 限 https 传输(防明文截获)、HttpOnly 禁 JS 读取(防 XSS 窃会话)、SameSite 防跨站携带(CSRF);Chrome M104(2022-08)起把超过 400 天的过期时间截到 400 天,RFC 6265bis 草案建议同一上限([Chrome](https://developer.chrome.com/blog/cookie-max-age-expires));声明更长只是自欺。warn/fail 分型按 cookie 用途[待核:常见分型为会话/鉴权类缺旗标取 fail 侧]。
**触发(trigger)**: 逐一解析 Set-Cookie:1) 缺任一旗标 → warn/fail;2) max-age/expires >400 天 → warn。
**不修的条件(caveat)**: Cookie 旗标不影响 SEO,然而会话安全缺口的后果(账号接管)会以最差方式登上 SERP,所以一般建议三旗全配。但第三方嵌入要求的宽松 SameSite 场景,用分区 cookie(CHIPS)替代裸放松。
**修复(fix)**: 会话 cookie `Secure; HttpOnly; SameSite=Lax`;持久 cookie ≤400 天并按业务再收;跨站场景评估 CHIPS/First-Party Sets。
**关联(seealso)**: legal-cookie-consent、technical-tagging;[validation-guide.md](validation-guide.md)

#### security-link-integrity [待核 ID]
- 名称/类型: 链接与引用安全家族 —— warning · 优先级 medium · 输出 WARN(源表各=warn:target=_blank 缺 noopener/noreferrer;协议相对 URL `//`;跨域脚本/stylesheet 缺 SRI integrity;品牌登录链须指向品牌或本域)
**这意味(what)**: 四项链接/引用卫生任一:`target=_blank` 的链接缺 rel=noopener/noreferrer;URL 用协议相对 `//example.com` 形态;跨域脚本与样式表没有 integrity(SRI)hash;登录/支付类品牌入口链接指向非品牌域。
**为什么(why)**: noopener 防新窗口反向操纵 opener(tabnabbing 的页面侧防线);协议相对 URL 在 http 上下文解析成 http,与全站 https 化冲突且行为依赖上下文;SRI 缺失时第三方脚本被篡改即直接进你页面(供应链注入面);品牌登录链指向陌生域是钓鱼的教科书形态——引擎与用户都对"登录入口不在品牌域"高度敏感。
**触发(trigger)**: 1) `<a target="_blank">` 的 rel 不含 noopener 即 warn;2) href 以 `//` 开头即 warn;3) 跨域 `<script src>`/`<link rel="stylesheet">` 无 integrity 属性即 warn;4) 登录/账单类锚文本的 href 域 ∉ {本域,已知品牌域} 即 warn。
**不修的条件(caveat)**: 家族单项不(直接)影响排名,然而 SRI 与登录链两项是真实攻击/钓鱼面,所以一般建议一次配齐。但第三方面向无版本化 URL 的脚本(内容随构建变)无法静态钉 SRI,先换版本化 URL 再上。
**修复(fix)**: target=_blank 统一 `rel="noopener noreferrer"`;协议相对改 https 绝对 URL;第三方资源走版本化 URL+SRI(integrity+crossorigin);登录链收敛品牌域或已知 IdP 域并公示。
**关联(seealso)**: links-malformed-href、security-headers;[head-elements.md](head-elements.md)

#### security-content-danger [待核 ID]
- 名称/类型: 内容层危险信号家族 —— issue · 优先级 critical · 输出 CRITICAL(fail 档)/WARN(指纹与混淆档)(源表:泄露密钥 AWS key/API token/私钥/数据库 URL=fail;HTTP 页密码框=fail;onpaste 阻止粘贴=fail;Server 带版本号/X-Powered-By=warn,裸 `Server: nginx` 过;混淆脚本特征=warn)
**这意味(what)**: 页面/响应里出现五类危险信号:硬编码密钥、HTTP 明文密码表单、阻止粘贴的密码框、服务器版本指纹、混淆可疑脚本。
**为什么(why)**: 泄露密钥是最硬的事故(云端凭据被扫走即被刷账单/挂马);HTTP 密码框等于明文广播凭据;onpaste 阻断摧毁密码管理器(用户被迫手打,实际退回弱密码);Server/X-Powered-By 版本指纹给攻击者递漏洞清单;长高熵内联脚本调 eval/Function/atob 的混淆特征是被挂码后的常见形态(security-info-disclosure 与混淆脚本两条并入本条陈述)。
**触发(trigger)**: 1) 页面文本/脚本命中密钥形态(AWS key/API token/私钥头/数据库 URL)→ fail;2) http 页含 `type=password` → fail;3) 密码/确认框 onpaste 返回 false 或 preventDefault → fail;4) Server 头带版本号或存在 X-Powered-By → warn(裸 `Server: nginx` 通过);5) 内联脚本高熵长串+eval/Function/atob 组合 → warn。
**不修的条件(caveat)**: fail 档三项没有"可合理不修"——它们不是 SEO 取舍是安全事故;warn 档(版本指纹/混淆特征)有误报面(合法加固混淆的第三方组件),命中后先比对官方产物再定性。
**修复(fix)**: 密钥立即轮换+从源码与构建产物移除(历史提交要 purge);密码页强制 https;移除 onpaste 阻断;Server 头去版本、删 X-Powered-By;混淆脚本溯源验签,来源不明的直接下线。
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
**关联(seealso)**: technical-empty-html、technical-soft-404;[http-status-codes.md](http-status-codes.md)、[log-analysis.md](log-analysis.md)

#### technical-empty-html [待核 ID]
- 名称/类型: 200 空 HTML —— issue · 优先级 critical · 输出 CRITICAL(源表 fail;head/body 皆空)
**这意味(what)**: URL 返回 200,响应体却是 head 与 body 都为空的 HTML 壳。
**为什么(why)**: 200+空壳是最高危的"假正常":索引流程收到"成功"却没有可索引内容,GSC 归入 soft 404 类目;客户端渲染失败(js-runtime-hygiene 的未捕获异常)也会呈现这个形态。引擎视角:页面存在但什么都没有,慢性退索引。
**触发(trigger)**: 1) 状态 200;2) 解析后 head 与 body 均无有效内容节点即 fail。
**不修的条件(caveat)**: 无豁免——200 必须配内容;确无内容的地址应给 404/410 或 301,而不是 200 空壳。
**修复(fix)**: 查渲染管道(SSR 失败回退空模板是常见肇因);模板兜底至少输出错误说明+正确状态码;CI 对发布产物做"空 HTML"断言。
**关联(seealso)**: technical-5xx、technical-soft-404、js-runtime-hygiene;[http-status-codes.md](http-status-codes.md)

#### technical-soft-404 [待核 ID]
- 名称/类型: soft 404 —— issue · 优先级 high · 输出 WARN(源表 warn;200 但错误内容)
**这意味(what)**: URL 返回 200,页面内容却是"未找到/已下架"的错误态。
**为什么(why)**: 引擎对 200 页照常走索引流程,内容是错误信息时被判 soft 404——占着"正常响应"的抓取预算却没有可服务的内容;它们在 GSC 索引报告里混成噪音,真假问题难分。典型来源:下架商品页返回 200"商品不存在";把大量删除页统一 301 到首页/无关页同样可能被判 soft 404(官方口径见 [http-status-codes.md](http-status-codes.md) 第二节)。
**触发(trigger)**: 1) 状态 200;2) 内容命中错误态特征("未找到/已下架/page not found"文案、空分类、搜索无结果壳、渲染失败空壳)即 warn。
**不修的条件(caveat)**: 判定是内容启发不是状态码,误报存在(正文合法引用"not found"字样),所以一般建议命中后人工抽查再改状态码。但确要保留的"内容已移除"说明页(带后续指引)属正当形态,配 noindex 即可。
**修复(fix)**: 真没了→真 404/410;有替代→301 到最近亲内容页(不是首页);保留说明页→加 noindex。
**关联(seealso)**: technical-4xx-non404、technical-custom-404;[http-status-codes.md](http-status-codes.md)

#### technical-4xx-non404 [待核 ID]
- 名称/类型: 非 404 的 4xx —— warning · 优先级 medium · 输出 WARN(源表 warn;403/410 等)
**这意味(what)**: 页面返回 403、410、451 等 404 之外的 4xx 状态。
**为什么(why)**: 各 4xx 语义不同,审计价值在分清"状态码用对了吗":401/403 是权限语义(Google 当作内容不存在;要短期降抓取速度应返回 500/503/429,[降速文档](https://developers.google.com/search/docs/crawling-indexing/reduce-crawl-rate));410 是明确的永久下线声明;451 是法律移除。除 429 外 Google 对所有 4xx 处理相同([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors)),选错码主要污染你自己的监控分类。
**触发(trigger)**: 响应状态 ∈ 4xx 且 ≠404 即 warn(404 本身不算错误,由内链/sitemap 交叉规则管)。
**不修的条件(caveat)**: 4xx 状态不惩罚站点(404 是正常 web 形态),然而选错码会误导引擎与监控,所以一般建议按语义选码。但登录墙内容返回 401/403 是正当设计,别为审计绿灯改成 404。
**修复(fix)**: 永久下线→410;临时不可用→503+Retry-After;限流→429;无权访问→401/403 保持。
**关联(seealso)**: technical-soft-404、technical-5xx;[http-status-codes.md](http-status-codes.md)

#### technical-custom-404 [待核 ID]
- 名称/类型: 自定义 404 页 —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: 站点 404 时返回服务器默认错误页,而非带导航与搜索的自定义 404 页。
**为什么(why)**: 404 本身不伤 SEO,伤的是 404 之后用户去留:默认错误页零出路,用户直接关站;自定义 404 给导航/搜索/热门内容,把撞错 URL 的流量接回站内。对引擎,自定义 404 也证明错误态是设计过的而非配置事故。
**触发(trigger)**: 请求不存在路径;返回 404 但响应体为服务器默认页(无站内导航特征/体积极小)即 warn;404 返回 200 另归 technical-soft-404。
**不修的条件(caveat)**: 404 状态码不(直接)影响排名,然而它决定错误流量的回收率,所以一般建议配自定义页。但纯 API/内部服务不需要人类可读 404。
**修复(fix)**: 404 模板带站点导航+站内搜索+热门链接;保持真 404 状态码;别自动跳首页(制造 soft-404)。
**关联(seealso)**: technical-soft-404、technical-4xx-non404;[http-status-codes.md](http-status-codes.md)

#### technical-robots-txt [待核 ID]
- 名称/类型: robots.txt 存在性与语法 —— warning · 优先级 high · 输出 WARN(源表 warn)
**这意味(what)**: 站点没有 robots.txt,或文件存在但含语法错误(非法指令/拼写错的键/未闭合组)。
**为什么(why)**: robots.txt 是抓取层第一道闸:不存在时按"全部允许"处理(失去 AI 爬虫策略等声明载体);存在但语法坏时引擎按容错解析——你写的 Disallow 可能没按你以为的生效。它还是 crawl-* 交叉规则(crawl-sitemap-disallowed 等)的前置输入,坏语法会级联污染下游判定。
**触发(trigger)**: 1) /robots.txt 404/5xx → 缺失档;2) RFC 9309 解析报语法错 → 语法档;均 warn。
**不修的条件(caveat)**: 缺 robots.txt 不(直接)影响 SEO(全允许也是合法状态),然而失去声明面与审计输入,所以一般建议放显式文件。但确无任何屏蔽需求的小站,空文件与缺文件等价,可记豁免。
**修复(fix)**: 提交显式 robots.txt(至少含 Sitemap 行,见 crawl-sitemap-in-robotstxt);用 RFC 9309 校验器过一遍;模板生成禁手维护([ai-crawler-policy.md](ai-crawler-policy.md) 口径)。
**关联(seealso)**: crawl-sitemap-disallowed、crawl-blocked-resources、crawl-crawl-delay;[robots-txt-reference.md](robots-txt-reference.md)、[ai-crawler-policy.md](ai-crawler-policy.md)

#### technical-sitemap-existence [待核 ID]
- 名称/类型: sitemap 存在性与格式 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 站点没有可发现的 sitemap,或 sitemap 格式坏(XML 不合法/编码错/非 sitemap 结构)。
**为什么(why)**: sitemap 是发现与再抓取的加速器:格式坏时整文件被丢弃等于没有,GSC 提交也报解析错误。存在性按发现路径判:robots.txt Sitemap 行、/sitemap.xml 常规路径、GSC 声明。条数/体积/lastmod 质量/domain 一致性由 Crawlability 节 sitemap 家族分规则管,本条只立"有没有、能不能解析"。
**触发(trigger)**: 1) 无任何可发现 sitemap → 缺失档;2) XML 解析失败/缺 urlset 命名空间 → 格式档;均 warn。
**不修的条件(caveat)**: sitemap 是推荐机制不是排名因素,内链完整的小站缺失损失有限,所以一般建议核心站必配、极小站可缓。但无 sitemap 时 GSC 的提交与覆盖率诊断面也少一半,通常仍值得配。
**修复(fix)**: 生成器输出标准 XML(可选 gzip);robots.txt 声明+GSC 提交;校验命名空间与转义(& 用 &amp;)。
**关联(seealso)**: crawl-sitemap-url-limit、crawl-sitemap-lastmod、crawl-sitemap-in-robotstxt;[validation-guide.md](validation-guide.md)

#### technical-content-type [待核 ID]
- 名称/类型: Content-Type 错误 —— issue/warning · 优先级 medium · 输出 WARN/CRITICAL(源表 warn/fail;分型口径源表未公布[待核])
**这意味(what)**: 响应的 Content-Type 头与实际内容或用途不符:HTML 页声明成 text/plain、字体声明成 text/html、缺 charset 等。
**为什么(why)**: 引擎与浏览器按 Content-Type 决定解析路径:声明错时 HTML 被当纯文本(索引流程拿不到 DOM)、资源被按错误类型处理;缺 charset 触发编码猜测,与 mojibake(content-deploy-hygiene)同源;nosniff 生效时被误标的资源直接被拒执行。
**触发(trigger)**: 1) 主文档非 text/html(且非刻意的 data feed)即触发;2) 子资源 Content-Type 与扩展/内容嗅探不符即触发;warn/fail 按分型[待核:主文档误标取重档的常见分型]。
**不修的条件(caveat)**: 个别误标(注释类文件以 text/plain 服务)不影响 SEO 面,然而主文档误标等于把页面挡在解析之外,所以一般建议全站对齐。但刻意以非 HTML 类型服务的资源(JSON API/RSS)不属误报,注意剔除。
**修复(fix)**: 服务器 MIME 表对齐;HTML 显式 `text/html; charset=utf-8`;要上 nosniff 前先自查全部资源类型(见 security-headers)。
**关联(seealso)**: content-mime-broken、content-deploy-hygiene、security-headers;[http-status-codes.md](http-status-codes.md)

#### technical-url-consistency [待核 ID]
- 名称/类型: URL 形态一致性家族 —— warning · 优先级 medium · 输出 WARN(源表各=warn:URL 结构小写+连字符;尾斜杠一致性;www 一致性 301)
**这意味(what)**: 站点级 URL 形态不统一:大小写/分词符混用、同站尾斜杠两可、www 与非 www 双可达且不互 301。
**为什么(why)**: 三项都在制造"同内容多 URL":大小写敏感的服务器上 /About 与 /about 是两个 200;尾斜杠两可时引擎靠规范化猜;www 双可达是经典重复站点种子。它们是 url-shape(单页形态卫生)的站点级聚合面——[validation-guide.md](validation-guide.md) C3 检查项(四变体 301 到唯一规范 host)就是本条的落地。
**触发(trigger)**: 1) 站内 URL 混用大小写/下划线与连字符即 warn;2) 同路径带/不带尾斜杠均 200 即 warn;3) www 与非 www 均可达且无单向 301 即 warn。
**不修的条件(caveat)**: 一致性家族不(直接)影响单页排名,然而每项都在给规范化添噪音,所以一般建议定一种形态+301 收口。但历史 URL 的大写形态已积累外链时,保持现状+canonical 比强改更稳。
**修复(fix)**: 定规范形态(小写+连字符+固定尾斜杠策略+单 host),其余变体 301 到规范形;CMS 输出层统一;新内容从源头合规。
**关联(seealso)**: url-shape、crawl-canonical-form-drift、redirects-case-normalization;[redirects-canonical.md](redirects-canonical.md)、[validation-guide.md](validation-guide.md)

#### technical-tagging [待核 ID]
- 名称/类型: 埋点与表单卫生家族 —— warning · 优先级 low · 输出 WARN(源表各=warn:多 GTM 容器/多 GA 属性(>1 个不同 ID);consent mode;GET 表单)
**这意味(what)**: 三项埋点/表单卫生任一命中:页面加载 >1 个不同 ID 的 GTM 容器或 GA 属性;Google 标签未配 consent mode update;GET 表单产生可抓取的查询串 URL。
**为什么(why)**: 双容器/双属性是"两拨人各埋一套"的事故:双计、页面变重、数据口径分裂——SEO 决策的数据底座被毁;consent mode 缺失在欧盟市场意味着同意前信号丢失与合规缺口;GET 表单把用户输入变成 URL,爬虫沿结果页发散(与 url-search-indexed 同源),敏感参数还可能进日志与外泄。
**触发(trigger)**: 1) 页面 GTM 容器 ID 去重后 >1 或 GA 属性 >1 即 warn;2) 有 gtag/GTM 但无 consent 默认态+update 调用即 warn;3) `<form method=get>`(缺省即 GET)且 action 产生站内查询 URL 即 warn。
**不修的条件(caveat)**: 埋点卫生不影响排名本身,然而双计毁掉流量归因的可信度,所以一般建议收敛单容器。但迁移期新旧属性并行的双属性是临时合理态,报告标注截止日期。
**修复(fix)**: 容器收敛为一个,历史属性经 GTM 转发;gtag 配 consent default+update(接 CMP,见 legal-cookie-consent);站内搜索表单结果页 noindex 或改 POST/前端路由。
**关联(seealso)**: url-search-indexed、legal-cookie-consent、sd-searchaction;[gtm-implementation.md](gtm-implementation.md)、[ga4-implementation.md](ga4-implementation.md)

### Structured Data(19 条,权重 5%)

缺 JSON-LD=warn;JSON 语法坏=fail;缺 @type=warn;类型必填字段=warn;Article 须 headline/author/datePublished/image;BreadcrumbList(非首页,**≥2 个 itemListElement**)=info;FAQPage 每个 Question 须 name+acceptedAnswer.text=fail;LocalBusiness 须 name/address/telephone/geo;Organization 须 name/logo/sameAs;Product 须 offers(price/priceCurrency/availability)=fail;Review 须 itemReviewed/author/reviewRating;VideoObject 须 name/thumbnailUrl/uploadDate(时长 ISO 8601 如 PT1M30S);WebSite SearchAction 含 `{search_term_string}`=info。**实体图六查已吸收于 [entity-signal-checklist.md](entity-signal-checklist.md) 与 [validation-guide.md](validation-guide.md)**:entity-id(@id 绝对)/rating-scope(AggregateRating 不在 legal/account URL 且 ratingValue 可见)/entity-conflict(一 @id 两 logo/两电话)/entity-dangling(publisher/author/isPartOf 的 @id 须在爬取中声明)/entity-type-drift(同 @id 跨页同 @type)/entity-split(同名组织不挂两 @id)。

**解释层(8 条;ID 未公布原文的按家族命名法推得并标 [待核];第四批补实体图六查 3 条,细则深读见 [entity-signal-checklist.md](entity-signal-checklist.md))**

#### sd-jsonld-missing [待核 ID]
- 名称/类型: 缺 JSON-LD —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: 页面没有任何 `<script type="application/ld+json">` 结构化数据。
**为什么(why)**: 结构化数据帮助 Google 理解页面并带来富结果资格;没有证据表明它独立提升 AI 引用(口径见 [geo-evidence.md](../content/geo-evidence.md))。缺信号类:不惩罚,只放弃一层机器可读性,故 low。
**触发(trigger)**: DOM 无 ld+json script 节点即 warn(microdata/RDFa 载体是否豁免[待核:源表按 JSON-LD 判])。
**不修的条件(caveat)**: schema 不(直接)影响排名,然而决定富结果资格,所以一般建议至少配全站级 Organization+页面主类型。但登录墙内页/纯工具页可不配。
**修复(fix)**: 按页面类型配最小集(全站 Organization,文章 Article,产品 Product——各类型必填见 sd-required-fields 家族);模板化生成,勿手拼 JSON。
**关联(seealso)**: sd-json-syntax;[schema-templates.md](schema-templates.md)、[validation-guide.md](validation-guide.md)

#### sd-json-syntax [待核 ID]
- 名称/类型: JSON-LD 语法坏/缺 @type —— issue · 优先级 high · 输出 CRITICAL(语法坏,源表 fail)/WARN(缺 @type,源表 warn)
**这意味(what)**: ld+json 内容不是合法 JSON(尾逗号/单引号/未转义引号),或解析成功但缺 @type。
**为什么(why)**: 语法坏时整块被静默丢弃——写了等于没写,且多数 CMS 不报错,坏块能潜伏数月;缺 @type 则引擎无法路由到任何类型校验,注解同样悬空。这是"坏信号"档:存在但残缺比没有更隐蔽,语法坏判 fail。
**触发(trigger)**: 1) JSON.parse 失败即 fail;2) 解析成功但顶层无 @type 即 warn。
**不修的条件(caveat)**: 语法错误不产生负面排名信号(只是白写),然而它是静默失效——没有任何报错渠道,所以一般建议 CI 里对全部 ld+json 做 JSON.parse 断言;修复本身无豁免。
**修复(fix)**: 用 JSON.stringify 生成而非手写模板拼接;补 @type;上线前过 Rich Results Test 类校验器。
**关联(seealso)**: sd-jsonld-missing、sd-required-fields;[validation-guide.md](validation-guide.md)

#### sd-required-fields [待核 ID]
- 名称/类型: 类型必填字段家族 —— issue/warning · 优先级 high(fail 档)/low(warn 档) · 输出 CRITICAL/WARN(源表:通用=warn;Product 缺 offers 与 FAQPage 缺结构=fail)
**这意味(what)**: 已部署的 schema 缺该类型的必填字段。源表口径照抄(工具约定,宽于 Google:Google 的 Article 与 Organization 没有必填属性,LocalBusiness 只要求 name 与 address,[Article](https://developers.google.com/search/docs/appearance/structured-data/article)、[Organization](https://developers.google.com/search/docs/appearance/structured-data/organization)、[LocalBusiness](https://developers.google.com/search/docs/appearance/structured-data/local-business)):Article 须 headline/author/datePublished/image;LocalBusiness 须 name/address/telephone/geo;Organization 须 name/logo/sameAs;Review 须 itemReviewed/author/reviewRating;VideoObject 须 name/thumbnailUrl/uploadDate(时长 ISO 8601 如 PT1M30S);Product 须 offers(price/priceCurrency/availability)=**fail**;FAQPage 每个 Question 须 name+acceptedAnswer.text=**fail**。
**为什么(why)**: 富结果与实体理解按"类型+必填"判资格:缺字段=该类型功能整体失效(Product 无 offers 则无价格类资格)。Product/FAQPage 判 fail 是"半残标记比缺失更浪费"的取舍。**注意 FAQPage 在此仅是对既有标记的结构校验**——FAQPage 富结果 2026-05-07 起全站停展,不要为 SERP 展示新增这类标记,真问答页用 QAPage(口径见 [deprecated-signals.md](deprecated-signals.md) 第一节)。
**触发(trigger)**: 按类型逐字段断言(清单照抄源表);缺任一必填:Product/FAQPage 走 fail 档,其余 warn 档。
**不修的条件(caveat)**: 缺必填不惩罚,然而该类型的机器理解整体落空,所以一般建议补齐或删类型。但 Organization 的 sameAs 在社交资产确实少时可先上子集、后补字段。
**修复(fix)**: 对照 [schema-templates.md](schema-templates.md) 每类型最小集补齐;数据源缺字段时模板应跳过该类型而非输出空壳。
**关联(seealso)**: sd-json-syntax;[schema-templates.md](schema-templates.md)、[entity-signal-checklist.md](entity-signal-checklist.md)

#### sd-breadcrumblist [待核 ID]
- 名称/类型: BreadcrumbList —— opportunity · 优先级 low · 输出 INFO(源表 info;非首页,≥2 个 itemListElement)
**这意味(what)**: 非首页页面缺 BreadcrumbList,或已有但 itemListElement <2 个。
**为什么(why)**: 面包屑 schema 让桌面结果以层级路径替代裸 URL;2025-01-23 起移动结果不再显示面包屑,只显示域名,标记仍受支持([公告](https://developers.google.com/search/blog/2025/01/simplifying-breadcrumbs))。它也是站内层级的机器可读声明。源表给 info:纯增益项,缺了不扣分——两轴哲学里典型的 opportunity。
**触发(trigger)**: 1) 非首页无 BreadcrumbList 即 info;2) 有但 itemListElement <2 即 info;首页不需要面包屑。
**不修的条件(caveat)**: 面包屑 schema 不影响排名,然而影响 SERP 展示形态,所以一般建议有真实面包屑 UI 的页面配同源 schema。但扁平站(全站一层)没有层级可表达,硬造两级反而是错。
**修复(fix)**: 面包屑 UI 与 schema 用同一数据源生成;每级 name 与目标页 title 呼应;末级指当前页。
**关联(seealso)**: sd-required-fields;[schema-templates.md](schema-templates.md)

#### sd-searchaction [待核 ID]
- 名称/类型: WebSite SearchAction —— opportunity · 优先级 insight · 输出 INFO(源表 info;target 须含 {search_term_string})
**这意味(what)**: 站点缺 WebSite+SearchAction 标记,或 potentialAction 的 target 模板没含字面 {search_term_string} 占位符。
**为什么(why)**: Google 已于 2024-11-21 起在全球移除 sitelinks 搜索框;现存标记不报错、无需删除;WebSite 结构化数据仍用于站点名称([公告](https://developers.google.com/search/blog/2024/10/sitelinks-search-box))。本条只剩标记卫生意义,源表现行仍按 warn 计分。
**触发(trigger)**: WebSite 类型的 potentialAction target URL 模板须含字面 {search_term_string};缺失或占位符变形即 info。
**不修的条件(caveat)**: 对 Google 已无展示收益,不必新增;存量标记可留。注意与 url-search-indexed 不矛盾:搜索功能要真实可用,搜索**结果页**要 noindex——一个对用户,一个对索引。
**修复(fix)**: WebSite schema 配 SearchAction,target 用真实搜索 URL+{search_term_string};搜索结果页模板加 noindex。
**关联(seealso)**: url-search-indexed;[schema-templates.md](schema-templates.md)

#### sd-entity-reference [待核 ID](entity-id + entity-dangling)
- 名称/类型: 实体引用完整性(@id 形态+悬空引用) —— issue/warning · 优先级 high · 输出 WARN(源表:entity-id @id 绝对;entity-dangling: publisher/author/isPartOf 的 @id 须在爬取中声明;档位未单列[待核])
**这意味(what)**: 实体的 @id 不是绝对 URL,或页面引用的实体 @id(publisher/author/isPartOf)在整站爬取中从未被任何页面声明——悬空引用。
**为什么(why)**: @id 是实体图的节点主键:绝对 URL 形态让它可跨页跨源稳定合并;悬空引用(指了没人声明的 @id)让 author/publisher 连不上具体 Person/Organization,实体消歧退回按名字猜——同名不同人就此混淆。六查的一号位:id 体系错,后面五查全部失真。
**触发(trigger)**: 1) @id 值非绝对 URL(含 scheme)即触发;2) 出向引用的 @id 在爬取全集中无对应声明节点即 dangling(两档分型[待核])。
**不修的条件(caveat)**: 单页审计只能判 @id 形态,dangling 需 crawl 全集;指向外部权威实体(Wikidata @id)是推荐做法,不算 dangling——"爬取中声明"应含已知外部实体源[口径待核]。
**修复(fix)**: @id 用站内稳定绝对 URL(https://site/#organization);声明与引用两侧用同一模板变量;人/组织实体挂 Wikidata sameAs 作外部锚。
**关联(seealso)**: sd-entity-consistency、eeat-author-expertise;[entity-signal-checklist.md](entity-signal-checklist.md)

#### sd-entity-consistency [待核 ID](entity-conflict + entity-type-drift + entity-split)
- 名称/类型: 实体一致性(conflict/type-drift/split) —— issue/warning · 优先级 high · 输出 WARN/CRITICAL(源表:entity-conflict 一 @id 两 logo/两电话;entity-type-drift 同 @id 跨页同 @type;entity-split 同名组织不挂两 @id;分档未单列[待核];仅 crawl 模式)
**这意味(what)**: 同一实体在站内自相矛盾:一个 @id 挂两个 logo/两个电话(conflict);同 @id 在不同页面是不同 @type——组织页是 Organization、文章页变 Person(type-drift);同名组织拆成两个 @id(split)。
**为什么(why)**: 实体图的全部价值取决于一致性:引擎按 @id 合并属性,冲突值要么随机取一要么降低实体置信度;type 漂移让节点身份不稳;split 把同一组织的信任信号(外链/评价/资质)摊薄到两个幽灵实体。三条是同一病(模板各自为政)的三张化验单,与 eeat-nap-consistency 的可见层判定互为表里。
**触发(trigger)**: ⛏ crawl 聚合:1) 同 @id 的 logo/telephone 值 >1 即 conflict;2) 同 @id 的 @type 集合 >1 即 drift;3) 同名(name 归一化)组织的 @id >1 即 split。
**不修的条件(caveat)**: 合法多值场景除外:同组织多电话(总机+售后)是真数据——conflict 的属性白名单按源表 logo/电话口径[待核];多子品牌同名应加后缀区分而非共用 name。
**修复(fix)**: Organization/Person 属性单一数据源(CMS 站点信息表)全站注入;@type 与 @id 定死在模板常量;品牌子体用独立 name+独立 @id。
**关联(seealso)**: sd-entity-reference、eeat-nap-consistency、sd-rating-scope;[entity-signal-checklist.md](entity-signal-checklist.md)

#### sd-rating-scope [待核 ID](rating-scope)
- 名称/类型: 评分作用域错配 —— issue · 优先级 high · 输出 CRITICAL/WARN(源表:AggregateRating 不在 legal/account URL 且 ratingValue 可见;分档未单列[待核])
**这意味(what)**: AggregateRating 挂错了地方:出现在法律页/账户页等无评分语境的 URL,或 schema 声明了 ratingValue 但页面渲染后看不见对应评分(暗评)。
**为什么(why)**: 评分是本地/电商富结果与实体信任的硬信号,也是结构化数据滥用重灾区:对"看不见的评分"(schema 有、页面无),Google 要求不标记页面上看不到的内容;结构化数据人工处置会让页面失去富结果资格,但不影响网页排名([结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies));legal/account URL 上的评分则是全站 footer schema 带评分类的模板泄漏。两轴口径:主动错配(评分挂错页/暗评)是坏信号,排 high。
**触发(trigger)**: 1) URL 属 legal/account 类(路径词表[待核])却含 AggregateRating 即触发;2) 有 ratingValue 声明但渲染后页面无可见评分文本/星标即触发(可见性判定口径[待核])。
**不修的条件(caveat)**: 站点级 AggregateRating(组织整体评分)在首页/关于页展示可见即可;Review/AggregateRating 分层数据必须真实——刷出来的评分是负信号不是增益。
**修复(fix)**: 评分 schema 只挂在有可见评分的产品/店铺页;数据源接真实评价系统;legal/account 模板剥离评分块;资格用富结果测试类工具复验。
**关联(seealso)**: sd-entity-consistency、eeat-trust-signals;[validation-guide.md](validation-guide.md)、[schema-examples.md](schema-examples.md)

### Content(27 条,权重 5%)

词数 **≥300 过/100-299 警/<100 败**(文章建议 500+,长文 1000+);Flesch-Kincaid **60-70** 最优(源表说法);关键词堆砌=warn/fail;标题层级不跳(H1→H3=invalid);**标题 <3 字符或 >100 字符=警**;页内标题重复=warn;text/HTML 比=warn;title 与 H1 相同=warn;**title 像素宽 ≤~580px、description ≤~920px**(工具约定;Google 无固定上限,按设备宽度截断);title=description 全同=warn;meta 在 body 里=fail;MIME=warn/fail;**crawl 专属**:duplicate-description/duplicate-exact(=fail)/duplicate-near/duplicate-h1(跨页同 H1)/thin-vs-site(**<同类页中位词数一半=警**,需 ≥4 个同类页)/title-pattern(标题未带全站 ≥60% 使用的后缀=警);`content-mojibake`(UTF-8 被按 Latin-1/Windows-1252 解码,如 `â€™`=fail);`content-unrendered-markup`(code/pre 外的字面 Markdown `**bold**`=warn);`content-placeholder-text`(**`{{ }}`/`{% %}`/`<% %>`/`[object Object]`=fail;TODO:/FIXME:=warn**;`content-stale-copyright`(页脚版权年落后当年=warn,区间取末年);`content-date-agreement`(datePublished/time datetime//20xx/ 路径三年份不一致=warn,dateModified 不比);`content-hidden-text`(**≥80 字符**被内联样式隐藏(display:none/visibility:hidden/font-size:0/大负 text-indent/opacity:0)=warn,nav/对话框/sr-only 豁免,仅样式表隐藏不判);`content-broken-html`/`content-meta-in-body`。

**解释层(15 条;ID 未公布原文,标 [待核])**

#### content-duplicate-exact ⛏
- 源表:fail · 权重 8 · 需 `--crawl`。另一已爬页的可见文本与本页完全相同。工具约定。建议优先级 high。
**依据**: 站内重复内容"not a violation of our spam policies",也不会招致人工处置;代价是体验差、浪费抓取,Google 会自行聚类并选规范页([SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide);[规范化文档](https://developers.google.com/search/docs/crawling-indexing/canonicalization))。"数千页触发质量算法"无出处,已删。核对 2026-10-18。
**判据**: 通过=无可见文本完全相同的可索引页对。失败=存在(联合发布、合法转载用伙伴侧 noindex 处理)。
**执行**: site_audit 不跨页;套件里 `traffic_funnel.py --audit audit.json` 只按 title+description 的 Simhash 聚类,不比正文。正文完全重复手工查:`while read u; do echo "$(curl -s "$u" | sed 's/<[^>]*>/ /g' | tr -s '[:space:]' ' ' | shasum | cut -c1-12) $u"; done < urls.txt | sort | awk '{n[$1]++; l[$1]=l[$1]" "$2} END{for(k in n) if(n[k]>1) print k":"l[k]}'`。
**修复**: 真重复用 canonical 或 301 合并;打印版加 canonical;采集页重写或下线。
**关联**: core-canonical-conflicting、content-duplicate-near;[scoring-rubric.md](scoring-rubric.md)

#### content-duplicate-near ⛏
- 源表:warn/fail · 权重 7 · 需 `--crawl`。主内容高度相似;相似度算法与阈值源表未公布。工具约定。建议优先级 medium。
**依据**: 同上:Google 会把主内容相似的页聚类,只选一个作规范页,重复页抓取频率降低([规范化文档](https://developers.google.com/search/docs/crawling-indexing/canonicalization))。真正的风险在规模化零增量模板,那属于"规模化内容滥用"的审查范围([垃圾政策](https://developers.google.com/search/docs/essentials/spam-policies))。核对 2026-10-18。
**判据**: 通过=同类页各有实质差异(本地数据、案例、评价)。失败=只换城市名/型号的模板页成批出现。
**执行**: 无现成正文相似度脚本。先用上条命令排除完全重复,再人工抽样对比同模板页;程序化页过 [programmatic-seo-gates.md](programmatic-seo-gates.md) 的门槛。
**修复**: 增量本地化;或合并为强页加 canonical。
**关联**: content-duplicate-exact;[programmatic-seo-gates.md](programmatic-seo-gates.md)

#### content-duplicate-description ⛏
- 源表:warn/fail · 权重 5。重复或不足 50 字符的 description=warn(需 `--crawl`);缺失=fail(任何审计)。工具约定。建议优先级 low。
**依据**: 全站相同或相似的 description 对用户没有帮助;无暇逐页写时先保核心页,大站可程序化生成([snippet 文档](https://developers.google.com/search/docs/appearance/snippet))。description 不是排名因素。核对 2026-10-18。
**判据**: 通过=可索引页 description 各不相同。失败=模板级重复(零星几页可排后)。
**执行**: `while read u; do curl -s "$u" | grep -oiE '<meta[^>]+name=.?description[^>]*>'; done < urls.txt | sort | uniq -c | sort -rn | awk '$1>1'`。
**修复**: 模板用真实字段变量拼装;无字段的页宁可不写,让 Google 从正文取摘要。
**关联**: core-title-unique、core-description-present

#### content-duplicate-h1 ⛏
- 源表:warn · 权重 5 · 需 `--crawl`。本页 h1 与另一已爬页完全相同;无 h1 报 not measured。工具约定。建议优先级 low。
**依据**: 无搜索引擎专门规定;Google 会参考 h1 生成 title link([title link 文档](https://developers.google.com/search/docs/appearance/title-link)),h1 重复常与 title 重复、近似内容同时出现,是模板失控的症状。核对 2026-10-18。
**判据**: 通过=可索引页 h1 各不相同(分页序列共享 h1 属预期)。失败=不同主题页用同一 h1。
**执行**: `while read u; do curl -s "$u" | grep -oiE '<h1[^>]*>[^<]*' | sed -E 's/<h1[^>]*>//'; done < urls.txt | sort | uniq -c | awk '$1>1'`。
**修复**: h1 带页面级变量;真重复页合并。
**关联**: core-h1-present、content-duplicate-exact

#### content-word-count [待核 ID]
- 名称/类型: 词数 —— warning · 优先级 low · 输出 WARN(100-299)/CRITICAL(<100)(源表:≥300 过/100-299 警/<100 败;文章建议 500+,长文 1000+)
**这意味(what)**: 页面主内容词数不足:100-299 词 warn,<100 词 fail 档(文章类建议 500+、长文 1000+ 为参考线不扣分[待核])。
**为什么(why)**: 词数不是排名因素,是"页面有没有内容"的粗代理:<100 词几乎必然是空壳/占位/极薄页,才配 fail 档。质量口径见 [scoring-rubric.md](scoring-rubric.md) "不作为扣分依据"——**不要机械灌字数到 300**。
**触发(trigger)**: 主内容区(剥导航/页脚/广告)文本词数:<100 → fail 档;100-299 → warn;≥300 过。
**不修的条件(caveat)**: 词数不(直接)影响 SEO,然而它是薄内容检测的第一道症状指标,所以一般建议主内容 ≥300 词。但联系页/工具页/表单页天然短,按页面类型豁免。
**修复(fix)**: 薄页补实质内容(回答/示例/数据)或并入父页;程序化薄页过 [programmatic-seo-gates.md](programmatic-seo-gates.md) 门槛;别注水。
**关联(seealso)**: content-keyword-stuffing、content-duplicate-near;[scoring-rubric.md](scoring-rubric.md)

#### content-keyword-stuffing [待核 ID]
- 名称/类型: 关键词堆砌 —— issue · 优先级 high · 输出 CRITICAL/WARN 分型(源表 warn/fail;分型阈值源表未公布[待核])
**这意味(what)**: 页面文本/alt/meta 里同一关键词的密度与重复超出自然语言频率。
**为什么(why)**: 关键词堆砌违反 Google 垃圾政策,例子包括罗列城市名、不自然地重复同一词组([垃圾政策](https://developers.google.com/search/docs/essentials/spam-policies))。判 warn 还是 fail 按程度分型(阈值未公布)。
**触发(trigger)**: 主文本关键词密度+n-gram 不自然重复检测(密度阈值[待核]);meta/alt 内同词根堆叠另计。
**不修的条件(caveat)**: 没有公认的安全密度魔法数,机器判堆砌误报不低,所以一般建议命中后人工复查再动文案。但主题集中的专题页关键词命中率高是自然结果,别一见重复就删。
**修复(fix)**: 用同义词/实体变体分散表达;每段回答一个问题;alt/title 里的堆叠优先清。
**关联(seealso)**: content-hidden-text、content-word-count;[scoring-rubric.md](scoring-rubric.md)

#### content-heading-family [待核 ID]
- 名称/类型: 标题结构家族 —— warning · 优先级 low · 输出 WARN(源表:层级跳级 H1→H3=invalid;标题 <3 字符或 >100 字符=警;页内标题重复=warn)
**这意味(what)**: 页内标题树有问题:层级跳级(H1 直接 H3)、标题过短(<3 字符)或过长(>100 字符)、同页重复标题文本。
**为什么(why)**: 标题树是引擎与屏幕阅读器共用的内容骨架:跳级让语义树断裂(SR 按级别导航会迷路),过长标题是段落伪装,页内重复让章节失去区分度。单项影响都轻,合并看是内容结构质量分。
**触发(trigger)**: 1) 相邻标题级别差 >1 即 invalid;2) 标题文本 <3 或 >100 字符即警;3) 同页两标题文本相同即 warn。
**不修的条件(caveat)**: 标题结构不(直接)影响排名,然而影响无障碍与 AI 摘要的章节切分,所以一般建议树形规范。但设计系统组件自带级别(卡片 H3 出现在 H1 区)造成的"跳级"是工程取舍,可按组件规则豁免。
**修复(fix)**: 模板按语义排 H1→H2→H3;标题写"这节说什么";组件标题级别参数化。
**关联(seealso)**: core-h1-present、content-agreement;[semantic-html.md](semantic-html.md)

#### content-agreement [待核 ID]
- 名称/类型: 元素一致性家族 —— warning · 优先级 low · 输出 WARN(源表:title 与 H1 相同=warn;title=description 全同=warn;content-date-agreement 三年份不一致=warn,dateModified 不比)
**这意味(what)**: 本该各司其职的信号互相雷同或矛盾:title 与 H1 完全相同;title 与 description 全同;页面三处年份(datePublished/`<time>` datetime/路径 /20xx/)互不一致。
**为什么(why)**: title 是 SERP 行、H1 是页内主题、description 是摘要候选——雷同等于放弃两层独立表达;年份不一致则对引擎发出矛盾的新鲜度信号。dateModified 不参与比对(更新时间晚于发布是常态)。均为轻档:单页雷同无实质影响,批量模板雷同才是病。
**触发(trigger)**: 1) 归一化后 title==H1 即 warn;2) title==description 即 warn;3) 三处年份取值 ≥2 个不同即 warn。
**不修的条件(caveat)**: 一致性家族不影响排名,然而各自放弃一层表达面,所以一般建议差异化:title 带品牌与意图、H1 是主题、description 是行动点。但品牌极简页(title=H1=品牌名)可豁免。
**修复(fix)**: 三字段分模板变量;日期单一来源(CMS updated_at)注入全部位置;像素口径(title ≤~580px/description ≤~920px)见本节表。
**关联(seealso)**: core-title-present、core-h1-present、content-heading-family;[head-elements.md](head-elements.md)

#### content-hidden-text [待核 ID]
- 名称/类型: 隐藏文本 —— issue · 优先级 high · 输出 WARN(源表 warn;≥80 字符被内联样式隐藏)
**这意味(what)**: ≥80 字符的文本被**内联样式**隐藏(display:none/visibility:hidden/font-size:0/大负 text-indent/opacity:0)。
**为什么(why)**: 为操纵排名而隐藏文本违反 Google 垃圾政策(字号或透明度设 0、移出屏幕等);折叠、选项卡等动态显示内容不违规([垃圾政策](https://developers.google.com/search/docs/essentials/spam-policies))。源表三个精准边界:只判内联样式(样式表隐藏可能是响应式规则,不判);≥80 字符(短文本隐藏多为 UI 状态);nav/对话框/sr-only 豁免(sr-only 是无障碍正确做法)。
**触发(trigger)**: 1) 元素内联样式含隐藏属性;2) 文本 ≥80 字符;3) 非豁免区即 warn。
**不修的条件(caveat)**: 隐藏本身不是罪(SR-only 文本、折叠 UI 都正当),然而"隐藏+长文本+关键词"的组合接近操纵形态,所以一般建议命中后人工判意图。但 A/B 测试的隐藏变体属实验基建,标注豁免。
**修复(fix)**: 该给用户看的就显示;折叠交互用 details/dialog 语义元素;sr-only 保留(豁免)。
**关联(seealso)**: content-keyword-stuffing;[semantic-html.md](semantic-html.md)

#### content-deploy-hygiene [待核 ID]
- 名称/类型: 部署卫生家族 —— issue · 优先级 high · 输出 CRITICAL/WARN(源表:占位符 {{ }}/{% %}/<% %>/[object Object]=fail,TODO:/FIXME:=warn;mojibake=fail;code/pre 外字面 Markdown=warn;页脚版权年落后=warn,区间取末年)
**这意味(what)**: 渲染管道事故漏进生产:未渲染占位符(fail 档)、TODO:/FIXME: 残留(warn)、乱码 mojibake——UTF-8 被按 Latin-1/Windows-1252 解码,如 `â€™`(fail 档)、code/pre 外的字面 Markdown `**bold**`(warn)、页脚版权年落后当年(warn,年份区间取末年)。
**为什么(why)**: 每项都是"管道坏了"的直接证据:占位符=模板引擎没跑或变量没注入;乱码=编码声明与实际字节不符;字面 Markdown=静态生成器漏处理。对用户是可见破损(信任度),对引擎是无意义文本;fail 档两项意味着页面实质坏死。
**触发(trigger)**: 正则扫主内容:占位符模式 → fail 档;TODO:/FIXME: → warn;mojibake 特征序列(â€™/Ã© 族)→ fail;code/pre 外 `**…**`/行首 # → warn;版权年 < 当年 → warn。
**不修的条件(caveat)**: 家族命中基本无豁免(生产页不该有模板残渣);唯一注意是展示模板语法的教程/文档页命中属误报,按白名单排除。
**修复(fix)**: CI 加渲染产物断言(无占位符/无 mojibake);charset 声明与实际编码统一为 UTF-8;版权年由服务器时间动态输出。
**关联(seealso)**: content-word-count、sd-json-syntax(同为"静默失效"家族);[validation-guide.md](validation-guide.md)

#### content-text-html-ratio [待核 ID]
- 名称/类型: 文本/HTML 比 —— warning · 优先级 low · 输出 WARN(源表 warn;阈值源表未公布[待核])
**这意味(what)**: 页面可见文本量与 HTML 标记量的比值过低。
**为什么(why)**: 低比值是"标记-heavy"的粗代理:内联样式/深层嵌套容器/隐藏 DOM 把标记撑大,正文被稀释——引擎要剥壳取肉,移动端要为壳付流量。它从来不是排名因素,是内容密度的症状指标;真正的病(多余嵌套/内联属性)由它暴露。
**触发(trigger)**: 渲染后可见文本字符数 ÷ HTML 总字符数,低于阈值即 warn(具体比值[待核:源表未公布])。
**不修的条件(caveat)**: 比值不(直接)影响 SEO(代码展示页文本密集、应用页标记密集,天然波动),然而它是标记债的症状,所以一般建议命中后查嵌套与内联属性而非灌字。但 SPA 壳页低比值是形态属性,配 SSR 后再看。
**修复(fix)**: 内联样式剥离到样式表;组件嵌套扁平化;隐藏 DOM 按需挂载;SSR 输出真实内容。
**关联(seealso)**: perf-dom-size、content-word-count;[scoring-rubric.md](scoring-rubric.md)

#### content-readability [待核 ID]
- 名称/类型: 可读性 —— warning · 优先级 low · 输出 WARN(源表 warn;Flesch-Kincaid **60-70** 最优)
**这意味(what)**: 正文可读性得分偏离 60-70 建议区(Flesch-Kincaid 口径)。
**为什么(why)**: 60-70 是源表给的最优区间(工具约定);可读性不是 Google 排名因素。英文公式不适用于中文,得分只作同类页横向对比。
**触发(trigger)**: 主内容文本计算 Flesch-Kincaid 读易分;<60 或 >70 即 warn(中文近似的口径[待核])。
**不修的条件(caveat)**: 可读性不是排名因素,然而它影响真实阅读完成率,所以一般建议向 60-70 靠拢。但学术/法律/技术文档天然低分是受众属性,别为得分把术语稀释成水文。
**修复(fix)**: 长句拆短(一句一个意思);术语首次出现给解释;段落 ≤4 行;中英混排统一标点口径。
**关联(seealso)**: content-word-count、content-heading-family;[scoring-rubric.md](scoring-rubric.md)

#### content-thin-vs-site [待核 ID]
- 名称/类型: 相对站内同类过薄 —— warning · 优先级 medium · 输出 WARN(源表 warn;crawl 模式;**<同类页中位词数一半=警,需 ≥4 个同类页**)
**这意味(what)**: crawl 全站后,该页词数不足同模板/同类页面中位数的一半(同类页 ≥4 个才可判)。
**为什么(why)**: 绝对词数阈值(content-word-count)对工具页/长文页一刀切失真;相对口径按同类校准——同是产品详情页,别家中位 800 词你 200 词,薄就是同维度可比的薄。≥4 个同类页的门槛保证中位数有统计意义,不足则不判(缺数据不等于缺内容)。
**触发(trigger)**: 1) 按模板/类型聚合同类页;2) 组内 ≥4 页才启用;3) 页词数 < 组中位数 ÷2 即 warn。
**不修的条件(caveat)**: 相对薄不(直接)影响排名(词数不是排名因素),然而同模板下显著偏薄多为空字段/抓取失败/未完成页,所以一般建议补实质内容。但新品待充实、UGC 早期短评是真实生命周期状态,排期充实而非硬灌字。
**修复(fix)**: 查模板空字段(无描述的产品页);补齐结构化内容模块;确实无话可说的页并入父级或 410。
**关联(seealso)**: content-word-count、content-duplicate-near;[programmatic-seo-gates.md](programmatic-seo-gates.md)

#### content-title-pattern [待核 ID]
- 名称/类型: 标题模式偏离 —— warning · 优先级 low · 输出 WARN(源表 warn;crawl 模式;标题未带全站 ≥60% 使用的后缀=警)
**这意味(what)**: crawl 全站后,该页 title 不带全站 ≥60% 页面都在用的标题后缀(品牌后缀/站名)。
**为什么(why)**: 品牌后缀一致性是模板健康与品牌 SERP 露出的双信号:多数页"| Brand"而个别页裸标题,几乎总是模板分支漏拼——SERP 里品牌词忽有忽无,同一站在结果页的视觉一致性碎掉。60% 是"主流模式"判定线:达到它,偏离者才算异常。
**触发(trigger)**: 1) 全站 title 提取公共后缀(分词对齐);2) 某后缀覆盖率 ≥60%;3) 不带该后缀的页即 warn。
**不修的条件(caveat)**: 后缀缺失不(直接)影响排名(title 长度哲学同 core-title-present),然而它是模板分支失控的症状,所以一般建议统一。但刻意区分的落地页组(广告着陆页不带品牌测 CTR)是实验设计,标注豁免。
**修复(fix)**: title 模板统一 `主题 | 品牌` 单一出口;超长页可程序化裁后缀保主题(像素口径见 content-agreement);实验页白名单。
**关联(seealso)**: core-title-present、content-agreement、core-title-unique;[scoring-rubric.md](scoring-rubric.md)

#### content-mime-broken [待核 ID]
- 名称/类型: MIME 与文档破损家族 —— issue/warning · 优先级 high(fail 档)/medium · 输出 CRITICAL/WARN(源表:MIME=warn/fail;meta 在 body 里=fail;content-broken-html)
**这意味(what)**: 文档级破损三型:页面 MIME 声明与实际不符(warn/fail 分型[待核]);meta 标签出现在 body 里(fail);HTML 结构破损(关键标签未闭合/非法嵌套)。
**为什么(why)**: MIME 错让引擎选错解析器(technical-content-type 的内容侧镜像);meta 出现在 body 时解析器容错重组,description/robots/canonical 可能全部失位——与 core-canonical-outside-head 同构的"声明不在有效位置"家族;结构性破损让 DOM 树与源码意图错位,内容提取随之漂移。三型叠加是"同一页面在不同工具里长得不一样"的根因。
**触发(trigger)**: 1) 响应 Content-Type 与文档实际形态(HTML/XML/文本)不符即 warn/fail;2) meta robots/description/charset 出现在 body 区即 fail;3) 关键标签未闭合/非法嵌套造成解析器重组即破损档。
**不修的条件(caveat)**: 破损判定依赖解析器口径,容错重组后多数用户无感,然而引擎提取的内容树已偏,所以一般建议 CI 过 HTML 校验器。但第三方组件注入的合法容错结构(微前端壳/遗留嵌入)命中属误报面,白名单处理。
**修复(fix)**: 模板过 W3C 类校验器零 error 再发;meta 全部收敛 head 单一出口;MIME 与内容对齐(见 technical-content-type);组件注入走规范插槽。
**关联(seealso)**: technical-content-type、htmlval-document-structure、core-canonical-outside-head;[semantic-html.md](semantic-html.md)

### JavaScript Rendering(16 条,权重 5%)

**raw-vs-rendered 实现要点已吸收于 [rendering-seo.md](rendering-seo.md) 与 [validation-guide.md](validation-guide.md)**(HTTP 抓原始→$;Playwright 二抓→rendered$;web-vitals 库 goto 前注入;INP 合成标记 inpSynthetic 不计分)。规则粒度:title/description/H1/canonical 不在初始 HTML=fail/warn/warn/fail;canonical 或 noindex 在源码与渲染 DOM 间不一致=fail;JS 事后改写 title/description/H1=warn;主内容/内链依赖 JS=warn;JS/CSS 被 robots 挡=warn;SSR 检查=warn/fail;**console 未捕获异常与错误=warn/fail**;**子资源加载失败=warn/fail**;内联脚本用 `document.write()`=warn。

**解释层(4 条;ID 未公布原文的按家族命名法推得并标 [待核];双抓实现见 [rendering-seo.md](rendering-seo.md))**

#### js-initial-html [待核 ID]
- 名称/类型: 关键注解不在初始 HTML —— issue · 优先级 critical · 输出 CRITICAL(title/canonical,源表 fail)/WARN(description/H1,源表 warn);SSR 检查=warn/fail(分型口径[待核])
**这意味(what)**: title/canonical 等关键注解不在服务端返回的初始 HTML,要等 JS 渲染才出现(源表分型:title 缺=fail、canonical 缺=fail、description=warn、H1=warn);SSR/SSG 检查同源。
**为什么(why)**: 初始 HTML 是所有抓取方的公共层:多数 AI 爬虫不执行 JS、社交爬虫不执行、Google 的渲染队列"may stay on this queue for a few seconds, but it can take longer"([JS SEO 文档](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics))——注解只在渲染后 DOM 里,对不渲染的消费者等于不存在。
**触发(trigger)**: 1) HTTP 抓 raw HTML;2) 检查 title/description/H1/canonical 存在性;3) 缺失再查渲染 DOM——仅渲染后存在即按上列分型触发。
**不修的条件(caveat)**: Google 终会渲染并读取 JS 注解,然而渲染延迟与非 Google 消费者的缺失是实打实的,所以一般建议 head 注解全部服务端输出。但客户端路由切换时的注解更新另归 js-meta-drift,不属本条。
**修复(fix)**: 框架切 SSR/SSG 或预渲染;至少 head 层(title/canonical/og)服务端输出;验收标准=raw HTML 即含全部关键注解。
**关联(seealso)**: js-meta-drift、js-content-dependency;[rendering-seo.md](rendering-seo.md)、[ai-crawler-policy.md](ai-crawler-policy.md)

#### js-meta-drift [待核 ID]
- 名称/类型: 注解在源码与渲染间漂移 —— issue · 优先级 high · 输出 CRITICAL(canonical/noindex 不一致,源表 fail)/WARN(JS 改写 title/description/H1,源表 warn)
**这意味(what)**: 同一页的 canonical 或 noindex 在 raw HTML 与渲染 DOM 间不一致(如源码 noindex、渲染后被删),或 JS 事后改写 title/description/H1。
**为什么(why)**: 引擎两阶段抓取(先 raw 后渲染)各记一次注解,不一致时以哪次为准不可控——canonical/noindex 漂移意味着索引决策分裂,故 fail;title 类改写最终值仍会被读到,影响小一档 warn。典型肇因:客户端路由器接管 head 但没与 SSR 输出对齐。
**触发(trigger)**: 双抓对比:1) canonical/noindex raw ≠ rendered 即 fail;2) title/description/H1 文本被 JS 改写即 warn。
**不修的条件(caveat)**: 修漂移不改变最终渲染值,然而它消除两阶段解读分裂,所以一般建议注解只写一次且客户端不改。但单页应用路由切换时更新 og 标签属合法客户端更新——本条只看首屏注解的稳定性。
**修复(fix)**: head 管理收敛到框架 head 组件一处;禁 JS 改写 canonical/noindex;A/B 测试不落在 head 层。
**关联(seealso)**: js-initial-html;[rendering-seo.md](rendering-seo.md)、[head-elements.md](head-elements.md)

#### js-content-dependency [待核 ID]
- 名称/类型: 主内容/内链依赖 JS —— warning · 优先级 high · 输出 WARN(源表 warn)
**这意味(what)**: 页面主内容或内链只存在于渲染后 DOM,raw HTML 里没有。
**为什么(why)**: 与 js-initial-html 同因不同层:注解缺失伤元数据,主内容缺失伤实体——AI 引用与社交摘要都取 raw 层,内容不在就等于对它们不存在;内链不在则按 raw 层计算的链接图(发现/权重)漏掉它们(Google 渲染后会计入,多数 AI/社交爬虫不渲染)。JS/CSS 再被 robots 挡住时问题翻倍(见 crawl-blocked-resources)。
**触发(trigger)**: 1) raw HTML 主内容区为空壳(仅挂载点)即 warn;2) raw 内链数远小于渲染后内链数(比例阈值源表未公布[待核])即 warn。
**不修的条件(caveat)**: Google 渲染能力成熟,纯 Google 视野下 JS 内容可索引,然而渲染预算与延迟真实存在、AI/社交侧多不渲染,所以一般建议主内容与核心内链服务端输出。但交互后的次级内容(评论区/展开区)客户端加载是正当形态。
**修复(fix)**: 主内容 SSR;首屏内链进模板;评论区等增强层保留客户端。
**关联(seealso)**: js-initial-html、crawl-blocked-resources;[rendering-seo.md](rendering-seo.md)

#### js-runtime-hygiene [待核 ID]
- 名称/类型: 运行时卫生家族 —— issue/warning · 优先级 high(fail 分型)/medium · 输出 CRITICAL/WARN(源表:console 未捕获异常=warn/fail;子资源加载失败=warn/fail;document.write()=warn;分型口径未公布[待核])
**这意味(what)**: 渲染时 console 有未捕获异常/错误、子资源(脚本/样式/图)加载失败,或内联脚本用 document.write()。
**为什么(why)**: 未捕获异常常中断后续脚本——依赖它的注解注入/内容挂载全部静默失败,是"页面看起来正常但 SEO 层坏死"的头号原因;子资源 4xx/超时拖慢渲染且常是 CDN/版本漂移;document.write 插入的跨站阻塞脚本在 2G 等慢网络下可能被 Chrome 拦截([Chrome](https://developer.chrome.com/blog/removing-document-write))。
**触发(trigger)**: 渲染过程:1) console error/uncaught 非空按分型触发;2) 任一子资源网络失败按分型触发;3) 内联脚本调 document.write 即 warn。
**不修的条件(caveat)**: console 噪声本身不影响 SEO,然而它标记渲染链路断裂,所以一般建议零未捕获异常再上线。但第三方脚本(广告/统计)抛的错不在你掌控内,归类外部噪声跟踪,不必阻塞发布。
**修复(fix)**: 异常接错误监控;子资源 404 修路径/版本;document.write 全部换 DOM API 或异步注入。
**关联(seealso)**: js-initial-html;[rendering-seo.md](rendering-seo.md)

### Accessibility(36 条,权重 7%)

对比度 **≥4.5:1 正文/3:1 大字**;触控目标 **≥44×44 CSS px**(源表;出自 WCAG 2.5.5 AAA,AA 级 2.5.8 为 24×24 或留足间距);交互元素须可访问名(aria-label/文本/title);focus 样式可见;表单 label(placeholder 不算);标题不跳级;landmark(main/nav/header/footer);描述性链接文本;skip-to-content 链接;表格 th+scope;视频字幕/文稿;viewport 禁缩放(user-scalable=no/maximum-scale=1)=fail;aria-hidden 包可聚焦元素=fail;**ARIA 角色/属性拼错浏览器静默丢弃(aria-lable→aria-label)=fail**;accesskey 唯一;**ID 重复致 aria-labelledby/label for 解析到第一个匹配=fail(svg 内 url(#id) 引用的 clipPath 豁免)**;空标题=fail;一控件一 label;同文本链接须同目的地;iframe/object 须 title/替代文本;`<input type=image>` 须 alt;**可访问名须含可见文本(语音用户"说所见")**;按钮有名;email/tel 输入配对 autocomplete token;lang 与 xml:lang 一致;html/body 禁 aria-hidden;ARIA widget 须有所需父子角色(tab 在 tablist 内/option 在 listbox 内);列表只含 li;**恰一个 main landmark**;role=none/presentation 不被 ARIA/可聚焦性反证;alt 不重复相邻链接/图注文本;img 角色 SVG 须可访问名;表格用 caption 不用跨列首行;**tabindex 禁正值**;元素级 lang 合法 BCP 47。

**解释层(32 条,第四批;ID 未公布原文,按家族命名法推得并标 [待核]。归并边界:alt 家族已归 Images 节 images-alt-present 三条、语言码两条已并入 i18n-lang-consistency、viewport 禁缩放已并入 mobile-viewport-config,不重复。why 只写无障碍理由;原"SEO 面"推断(引擎读无障碍树、aria-hidden 影响索引等)无一手出处,已删,仅保留有 Google 文档支持的几句)**

#### a11y-contrast [待核 ID]
- 名称/类型: 文本对比度不足 —— warning · 优先级 medium · 输出 WARN(源表:≥4.5:1 正文/3:1 大字;档位未单列[待核])
**这意味(what)**: 文本与背景的前景/背景对比度低于阈值:正文 <4.5:1,大字(约 ≥18pt/14pt 粗体) <3:1。
**为什么(why)**: 无障碍:低对比对低视力/老年/强光环境用户直接不可读,4.5:1 是 WCAG 2.1 AA(1.4.3)硬阈值。
**触发(trigger)**: 渲染后计算文本节点 computed 前景/背景对比度(图片背景的采样口径[待核]):正文 <4.5:1、大字 <3:1 即 warn。
**不修的条件(caveat)**: 对比度不(直接)影响排名,然而 4.5:1 是可读性工程下限,所以一般建议正文全站达标。但 disabled 态/水印等非必要信息文本豁免;改版走设计系统调 token,别逐页打补丁。
**修复(fix)**: 设计 token 化色对并预检 ≥4.5:1;灰阶层压进合规区间;CI 对主题色组合跑对比度断言。
**关联(seealso)**: mobile-font-size、content-readability;[semantic-html.md](semantic-html.md)、[validation-guide.md](validation-guide.md)

#### a11y-touch-target [待核 ID]
- 名称/类型: 触控目标过小 —— warning · 优先级 medium · 输出 WARN(源表:44×44 CSS px,出自 WCAG 2.5.5 AAA;AA 级 2.5.8 为 24×24;档位未单列)
**这意味(what)**: 可点击/可触摸元素(按钮/链接/表单控件)的触达区域小于 44×44 CSS 像素。
**为什么(why)**: 无障碍:小目标难倒运动障碍与触屏用户。WCAG 2.5.8(AA)要求目标至少 24×24 CSS px 或留足间距,44×44 是 2.5.5(AAA)([W3C](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html))。
**触发(trigger)**: 渲染后测量交互元素的可触达盒(含 padding/伪元素扩展):<44×44 即 warn(源表口径;按 WCAG 2.5.8 只有 <24×24 且间距不足才算不达标,行内文字链豁免)。
**不修的条件(caveat)**: 触控尺寸不影响桌面排名,然而移动端它是可用性硬阈值,所以一般建议交互件全站达标。但正文行内文字链的密排形态天然豁免——本条管的是按钮/控件/导航项等关键交互件。
**修复(fix)**: 按钮/控件最小热区 44×44(padding 或伪元素扩展,视觉尺寸可小);间距 ≥8px 防误触;图标按钮扩热区而非放大图标。
**关联(seealso)**: mobile-interstitial、mobile-font-size;[mobile-seo.md](mobile-seo.md)

#### a11y-accessible-name [待核 ID]
- 名称/类型: 交互元素无可访问名 —— warning · 优先级 high · 输出 WARN(源表:aria-label/文本/title;档位未单列[待核])
**这意味(what)**: 链接/按钮/输入等交互元素没有可访问名(accessible name)——无文本内容、无 aria-label、无 title。
**为什么(why)**: 无障碍:屏幕阅读器按可访问名朗读控件,无名控件只念"按钮",用户不知道会发生什么;语音控制用户更是无法下指令("点'提交'按钮"落空)。SEO 面唯一有出处的一点:空 `<a>` 时 Google 可用 title 作锚文本,图片链接用 img 的 alt 作锚文本([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable))。
**触发(trigger)**: 交互元素(a/button/input/select/textarea)按 accname 算法计算(优先级:aria-labelledby → aria-label → label/alt 等原生标签 → 内容文本 → title,[accname 1.2](https://www.w3.org/TR/accname-1.2/)):结果为空即 warn。
**不修的条件(caveat)**: 可访问名不影响排名本身,然而它是无障碍合规与语义完整性的交叉点,所以一般建议全配。但 aria-hidden 标记的装饰性冗余控件不判——那是 a11y-aria-hidden 家族的辖区。
**修复(fix)**: 图标按钮加 aria-label("打开菜单");文本按钮靠内容文本;title 只作兜底(触屏不可见);配合 a11y-name-contains-visible 的"名含可见文本"要求。
**关联(seealso)**: a11y-button-name、a11y-svg-name、images-alt-present;[semantic-html.md](semantic-html.md)

#### a11y-button-name [待核 ID]
- 名称/类型: 按钮无名 —— warning · 优先级 medium · 输出 WARN(源表:按钮有名;与 a11y-accessible-name 同族,按钮为最高频命中面)
**这意味(what)**: `<button>` 元素没有任何可访问名(空文本且无 aria-label)。
**为什么(why)**: 无障碍:无名按钮在 SR 里是一列"按钮、按钮",播放器/弹窗/表单里的图形按钮全部不可用。
**触发(trigger)**: `<button>`(含 role=button)accessible name 计算为空即 warn。
**不修的条件(caveat)**: 单个命中可能是刻意的装饰冗余(双重关闭按钮),所以一般建议模板级批量治理而非逐个补。但 aria-hidden 标记的冗余控件不判。
**修复(fix)**: 组件库给图标按钮内置 aria-label 槽位;文案缺失(空 i18n key)构建期报错;验收用 SR 模式抽查关键流程。
**关联(seealso)**: a11y-accessible-name、a11y-form-label;[semantic-html.md](semantic-html.md)

#### a11y-name-contains-visible [待核 ID]
- 名称/类型: 可访问名不含可见文本 —— warning · 优先级 low · 输出 WARN(源表:可访问名须含可见文本,语音用户"说所见";档位未单列[待核])
**这意味(what)**: 元素的可访问名(aria-label/aria-labelledby)与其可见文本不一致——可见写"购买",可访问名却是"加入购物车 submit"。
**为什么(why)**: 无障碍:语音控制用户"说所见"——对着屏幕念"点击购买"命中不了名为"加入购物车"的按钮;SR 用户听到的与看到的也不同,两套词两套认知。
**触发(trigger)**: 1) 元素同时有可见文本与 aria-label/aria-labelledby;2) 可访问名归一化后不包含可见文本字符串即 warn(源表"须含"口径,即扩写方向合法、替换方向违例)。
**不修的条件(caveat)**: 合法的扩写场景:可见文本是缩写/短词,aria-label 给完整表述("菜单"→"主导航菜单")——名 ⊃ 可见文本合法;名与可见文本无关才是问题。
**修复(fix)**: 默认不覆写——有可见文本就不加 aria-label;确需扩写时保留原词;关键词堆砌进 aria-label 的全部清除。
**关联(seealso)**: a11y-accessible-name、links-anchor-generic;[semantic-html.md](semantic-html.md)

#### a11y-focus-visible [待核 ID]
- 名称/类型: 焦点样式不可见 —— warning · 优先级 medium · 输出 WARN(源表:focus 样式可见;档位未单列[待核])
**这意味(what)**: 可聚焦元素被聚焦时没有任何可见指示——`outline:none` 且无替代 focus 样式。
**为什么(why)**: 无障碍:键盘用户(运动障碍/高级用户/部分 AT)靠焦点环知道"现在在哪",全局删 outline 等于蒙眼操作。
**触发(trigger)**: 1) 样式表出现 :focus{outline:none/0} 且无 :focus-visible 替代即触发;2) 渲染后聚焦元素无可感知的指示变化(判定口径[待核])即 warn。
**不修的条件(caveat)**: 焦点样式不影响排名,然而全局删焦点环是"看起来更干净"的经典反模式,所以一般建议 :focus-visible 替代而非删除。但鼠标点击态的 :focus 抑制(focus-visible 分流)是正当精细化,不判。
**修复(fix)**: :focus-visible 给 ≥2px 对比指示(outline/box-shadow);别全局 outline:none;验收标准=纯键盘走通主流程(登录→下单)。
**关联(seealso)**: a11y-tabindex、links-onclick;[semantic-html.md](semantic-html.md)

#### a11y-tabindex [待核 ID]
- 名称/类型: 正值 tabindex —— warning · 优先级 medium · 输出 WARN(源表:tabindex 禁正值;档位未单列[待核])
**这意味(what)**: 元素带正整数 tabindex(tabindex="1"/"3"),覆盖文档流的自然 Tab 顺序。
**为什么(why)**: 无障碍:正 tabindex 把焦点顺序钉死在作者想象的顺序上,DOM 变化(插组件/异步内容)后跳转顺序错乱,键盘用户在页面里"瞬移"。
**触发(trigger)**: 任一元素 tabindex 属性值为正整数即 warn(tabindex=0/-1 合法:0 加入自然序、-1 可编程聚焦)。
**不修的条件(caveat)**: 正 tabindex 不影响排名,然而它几乎没有正当用例(模态框焦点管理用 -1+focus()),所以一般建议全站清零。但遗留 widget 库依赖正值的,先建组件焦点管理再清。
**修复(fix)**: 删正值——自然顺序靠 DOM 顺序表达;自定义组件用 tabindex=-1 + element.focus();模态框做 focus trap。
**关联(seealso)**: a11y-focus-visible、a11y-aria-parent-child;[semantic-html.md](semantic-html.md)

#### a11y-skip-link [待核 ID]
- 名称/类型: 缺 skip-to-content 链接 —— warning · 优先级 low · 输出 WARN(源表:skip-to-content 链接;档位未单列[待核])
**这意味(what)**: 页面没有"跳到主内容"链接——键盘/SR 用户每页都要 Tab 过整条导航才能到正文。
**为什么(why)**: 无障碍:键盘用户每次换页从页头 Tab 二十几个导航链接,skip 链是 WCAG 2.4.1 的经典达标手段。
**触发(trigger)**: 页面首部(body 前几个焦点元素)无指向主内容锚点的跳转链接(href="#main"/#content 形态[待核])即 warn。
**不修的条件(caveat)**: 短导航页(≤5 个链接)的 skip 链价值低,所以一般建议导航项多的模板配。但配了就别 display:none 隐藏——要"聚焦时可见"。
**修复(fix)**: body 首元素加 `<a href="#main" class="skip-link">跳到主内容</a>`;CSS 默认移出视口、:focus 时归位;与 main landmark 同步(见 a11y-landmarks)。
**关联(seealso)**: a11y-landmarks、a11y-single-main;[semantic-html.md](semantic-html.md)

#### a11y-accesskey [待核 ID]
- 名称/类型: accesskey 重复 —— warning · 优先级 low · 输出 WARN(源表:accesskey 唯一;档位未单列[待核])
**这意味(what)**: 多个元素绑定了同一个 accesskey 快捷键。
**为什么(why)**: 无障碍:重复 accesskey 只有浏览器选中的那个生效,用户记住的快捷键在半数页面失灵;accesskey 还与浏览器/AT 自身快捷键冲突(Alt+字母多被占用),现代最佳实践已弱化它。
**触发(trigger)**: 全页收集 accesskey 属性值;同一字符出现 ≥2 次即 warn。
**不修的条件(caveat)**: accesskey 不影响 SEO 且现代站点多数已弃用,所以一般建议直接清理而非修复映射。但确要保留(工具型内网应用)时保证全站唯一并公示键位表。
**修复(fix)**: 优先删除 accesskey(改可见快捷键说明);保留时全站唯一并避开浏览器保留组合。
**关联(seealso)**: a11y-duplicate-id、a11y-focus-visible;[semantic-html.md](semantic-html.md)

#### a11y-form-label [待核 ID]
- 名称/类型: 表单控件无 label —— warning · 优先级 high · 输出 WARN(源表:表单 label,placeholder 不算;档位未单列[待核])
**这意味(what)**: 表单控件(input/select/textarea)没有关联 label——无 `<label for>`、无 aria-label(ledBy);placeholder 占位文本不算 label。
**为什么(why)**: 无障碍:SR 对 placeholder 的支持参差,且输入后 placeholder 消失——用户回改时字段名没了;label 的点击命中区同时扩大触控目标。
**触发(trigger)**: 每个 input(除 hidden/button/submit 等自带语义型[豁免清单待核])/select/textarea 计算 label 关联(for=id 匹配/aria-label/aria-labelledby):结果为空即 warn;placeholder 存在不豁免。
**不修的条件(caveat)**: 极简搜索框(放大镜图标+placeholder)是广被接受的形态,可用 aria-label 补名;但任何收集关键信息(地址/支付)的表单没有 label 都是硬伤。
**修复(fix)**: `<label for>` 绑定;图标-only 控件用 aria-label;placeholder 只作示例提示;一控件一 label(见 a11y-one-label-per-control)。
**关联(seealso)**: a11y-one-label-per-control、a11y-autocomplete-token、a11y-accessible-name;[semantic-html.md](semantic-html.md)

#### a11y-one-label-per-control [待核 ID]
- 名称/类型: 一控件多 label —— warning · 优先级 low · 输出 WARN(源表:一控件一 label;档位未单列[待核])
**这意味(what)**: 同一表单控件被多个 label 关联(多个 for 指向同一 id,或嵌套 label 与显式 for 并存)。
**为什么(why)**: 无障碍:多 label 时 AT 读取行为不一(读首个/拼接),用户听到的字段名不可预期。
**触发(trigger)**: 按 for=id 聚合:任一控件的关联 label 计数 >1 即 warn(嵌套+显式并存的计数口径[待核])。
**不修的条件(caveat)**: 多 label 极少有正当用例,所以一般建议收敛为一。但控件用 aria-labelledby 引用多个 id 是合法的多源命名(如"账单 地址"),不属本条。
**修复(fix)**: 每控件一个 label for;辅助说明文字改 aria-describedby(描述而非命名);CI 断言 for 值与控件 id 一一对应。
**关联(seealso)**: a11y-form-label、a11y-duplicate-id;[semantic-html.md](semantic-html.md)

#### a11y-autocomplete-token [待核 ID]
- 名称/类型: email/tel 输入缺 autocomplete token —— warning · 优先级 low · 输出 WARN(源表:email/tel 输入配对 autocomplete token;档位未单列[待核])
**这意味(what)**: type=email 的输入框没配 autocomplete="email",type=tel 没配 autocomplete="tel"。
**为什么(why)**: 无障碍:autocomplete token 是 AT 与密码管理器/浏览器自动填充的对接协议——正确 token 让运动障碍用户一次完成表单,自编 token(autocomplete="email-address")静默失效。
**触发(trigger)**: type=email 的 autocomplete 不含 "email"、type=tel 不含 "tel"(精确 token 按 HTML 规范词表[待核:源表按这两个 token 判])即 warn。
**不修的条件(caveat)**: token 配错与没配等效,所以一般建议整表按 HTML autocomplete 词表配全(name/street-address 等同族)。但一次性验证码输入配 autocomplete="one-time-code" 或禁填充属安全设计。
**修复(fix)**: email→autocomplete="email";tel→autocomplete="tel"(区号分体用 tel-national 系);整表按词表补全并做密码管理器回归。
**关联(seealso)**: a11y-form-label;[semantic-html.md](semantic-html.md)

#### a11y-landmarks [待核 ID]
- 名称/类型: landmark 角色缺失 —— warning · 优先级 medium · 输出 WARN(源表:landmark main/nav/header/footer;档位未单列[待核])
**这意味(what)**: 页面缺 HTML5 landmark 语义:无 `<main>`/`<nav>`/`<header>`/`<footer>`(或对应 role),整页是 div 沙漠。
**为什么(why)**: 无障碍:SR 用户靠 landmark 区跳转(到导航/到主内容),无 landmark 只能逐元素线性听。
**触发(trigger)**: 渲染后解析 landmark 元素(main/nav/header/footer/aside 及对应 role):main 或 nav 计数为 0 即 warn(header/footer 缺失是否同判[待核:footer 常并入分组判定])。
**不修的条件(caveat)**: landmark 不(直接)影响排名,然而它是语义 HTML 骨架层,所以一般建议模板级配齐。但组件化页面滥用 header/footer(每卡片一个)会稀释语义——main 的唯一性另由下条管。
**修复(fix)**: 模板用原生 landmark 元素(role 兜底仅限 div 不可避免时);导航区用 aria-label 区分(主导航/面包屑/页脚导航);main 恰一个(见 a11y-single-main)。
**关联(seealso)**: a11y-single-main、a11y-skip-link、links-chrome-inbound;[semantic-html.md](semantic-html.md)

#### a11y-single-main [待核 ID]
- 名称/类型: main landmark 数量错误 —— warning · 优先级 medium · 输出 WARN(源表:恰一个 main landmark;档位未单列[待核])
**这意味(what)**: 页面的 main landmark 数量 ≠1:零个(缺失面与 a11y-landmarks 重叠)或多个(组件化误用)。
**为什么(why)**: 无障碍:HTML 规范规定一个文档不得有多于一个未带 hidden 的 main([WHATWG](https://html.spec.whatwg.org/multipage/grouping-content.html));多个 main 时"跳到主内容"的落点不可预期。
**触发(trigger)**: 渲染后 `<main>`/role=main 计数 0 或 >1 即 warn(0 个已由 a11y-landmarks 报缺失,本条侧重 >1 与计数口径)。
**不修的条件(caveat)**: 合法例外是切换式视图(同一时刻只有一个 main 可见)——SPA 若 DOM 同时存在多个视图,用 hidden 属性保证只一个对 AT 与爬虫暴露。
**修复(fix)**: 模板级恰一个 `<main>`;SPA 路由切换时旧视图加 hidden 或移除;组件不私自包 main(插槽组件用 div)。
**关联(seealso)**: a11y-landmarks、a11y-skip-link;[semantic-html.md](semantic-html.md)

#### a11y-heading-hierarchy [待核 ID]
- 名称/类型: 标题跳级(无障碍视角) —— warning · 优先级 low · 输出 WARN(源表:标题不跳级;Content 节同构条已写 content-heading-family,本条为 Accessibility 类计分视角,阈值同源不重抄)
**这意味(what)**: 标题层级跳跃(H1 直接 H3、H2 掉到 H5),语义树断档。
**为什么(why)**: 无障碍:SR 用户按标题级别导航(按 2 级跳/按 3 级跳),跳级让导航树缺枝——H1 后直接 H3,按 2 级导航的用户整节内容不可达。SEO:标题顺序对 Google 搜索无所谓,只对屏幕阅读器重要([SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide))。
**触发(trigger)**: 相邻标题级别差 >1 即触发(阈值与 content-heading-family 同源照抄,不另立)。
**不修的条件(caveat)**: 设计系统组件自带级别造成的技术性跳级,豁免口径见 content-heading-family;修复优先级低于空标题(下条)。
**修复(fix)**: 见 content-heading-family(模板按语义排级、组件级别参数化)。
**关联(seealso)**: content-heading-family、a11y-empty-heading;[semantic-html.md](semantic-html.md)

#### a11y-empty-heading [待核 ID]
- 名称/类型: 空标题 —— issue · 优先级 medium · 输出 CRITICAL(源表 fail;两轴校准:输出随源表 fail,建议优先级按卫生级降 medium——存在但残缺的坏信号,非主动矛盾)
**这意味(what)**: 标题元素(h1-h6)存在但内容为空——无文本、无可访问名(aria-label)。
**为什么(why)**: 无障碍:空标题在 SR 标题列表里显示为空行,按标题速览的用户遇到"无名节",导航价值归零还制造噪音。
**触发(trigger)**: 任一 h1-h6 的文本(含 img alt 贡献与 aria-label)归一化后为空即 fail 档。
**不修的条件(caveat)**: 刻意的纯图标节标题可用 aria-label 补名后豁免;真无内容的标题应条件渲染跳过,而不是渲染空壳。
**修复(fix)**: 空字段时整个标题元素不渲染(v-if/条件模板);图标节标题加 aria-label;CI 对渲染产物断言无空标题。
**关联(seealso)**: a11y-heading-hierarchy、content-deploy-hygiene、content-heading-family;[semantic-html.md](semantic-html.md)

#### a11y-link-text [待核 ID]
- 名称/类型: 链接文本无信息量 —— warning · 优先级 medium · 输出 WARN(源表:描述性链接文本;Links 节 links-anchor-generic 同源,本条从 Accessibility 类计分补判)
**这意味(what)**: 链接的可访问名不含目标信息——泛化词(click here/read more)、裸 URL 或无意义图标。
**为什么(why)**: 无障碍:SR 用户常调出"链接列表"脱离上下文浏览,一列 "read more" 完全不可用——链接文本就是它的全部语境。SEO:Google 用锚文本理解目标页,click here/read more 一类泛化锚文本不好([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable))。
**触发(trigger)**: 链接可访问名命中泛化词表或为纯 URL 字符串即 warn(词表与 links-anchor-generic 共用[待核])。
**不修的条件(caveat)**: 转化文案锚("免费试用")的取舍豁免见 links-anchor-generic;本条不重复修复细则,修复一次两规则双绿。
**修复(fix)**: 见 links-anchor-generic(锚含目标主题、图标链补 aria-label);裸 URL 换描述性锚或页面标题。
**关联(seealso)**: links-anchor-generic、a11y-name-contains-visible;[semantic-html.md](semantic-html.md)

#### a11y-link-consistency [待核 ID]
- 名称/类型: 同文本链接不同目的地 —— issue/warning · 优先级 medium · 输出 WARN(源表:同文本链接须同目的地;档位未单列[待核])
**这意味(what)**: 页面里两处链接的可访问名完全相同,href 却指向不同地址。
**为什么(why)**: 无障碍:SR/语音用户按链接名操作,同名不同目的地让指令二义——念"产品页"命中哪个全凭 Tab 位置。
**触发(trigger)**: 全页按可访问名归一化聚合链接;同名的 href 集合去重后 >1 即 warn(大小写/空白归一化口径[待核])。
**不修的条件(caveat)**: 同目的地的同名重复链接(面包屑末级与正文链)不判;"阅读更多"指向不同文章的形态该修锚文本而非删链接——与 links-anchor-generic 联手覆盖。
**修复(fix)**: 同目的地保持一致;不同目的地的链接文本差异化(带目标主题);模板循环变量注入锚文本。
**关联(seealso)**: a11y-link-text、links-anchor-generic;[semantic-html.md](semantic-html.md)

#### a11y-table-headers [待核 ID]
- 名称/类型: 数据表缺表头关联 —— warning · 优先级 medium · 输出 WARN(源表:表格 th+scope;档位未单列[待核])
**这意味(what)**: 数据表(对比表/报价表/规格表)的单元格没有表头关联:无 `<th>`,或有 th 但缺 scope 属性/headers-id 映射。
**为什么(why)**: 无障碍:SR 按表头+单元格报坐标("价格 第3列 ¥299"),无 scope 的表读出来是一串无上下文的数字,复杂数据表等于不可用。
**触发(trigger)**: `<table>` 含 ≥2 列数据(简单双列键值表豁免口径[待核])但表头单元格无 scope(或无 headers/id 映射)即 warn。
**不修的条件(caveat)**: 布局用表(邮件模板遗留)与数据表要分开——布局表该删不该补 scope;双列键值表(`<th>键</th><td>值</td>`)天然可读,缺 scope 影响小。
**修复(fix)**: 表头单元格 `<th scope="col"/"row">`;复杂表加 id/headers 映射;布局表改 CSS grid;配 caption(见 a11y-table-caption)。
**关联(seealso)**: a11y-table-caption、a11y-landmarks;[semantic-html.md](semantic-html.md)

#### a11y-table-caption [待核 ID]
- 名称/类型: 表格标题用跨列首行替代 —— warning · 优先级 low · 输出 WARN(源表:表格用 caption 不用跨列首行;档位未单列[待核])
**这意味(what)**: 表格标题被写成第一行的跨列单元格(`<td colspan=全表宽>`),而不是 `<caption>` 元素。
**为什么(why)**: 无障碍:SR 进入表格前先播报 caption——用首行单元格冒充标题时,用户进了表还不知道表是什么,跨列首行在导航模式里只是普通数据格。
**触发(trigger)**: 表格首行为跨全部列的单单元格文本(疑似标题)且无 `<caption>` 即 warn(疑似标题的判定口径[待核])。
**不修的条件(caveat)**: 首行若是真实数据(日期行/首条记录)不判;存量表格批量改造收益有限时,优先保证新表用 caption。
**修复(fix)**: 跨列首行改 `<caption>`(可 CSS 定位到任意位置);新表模板默认开 caption 槽位。
**关联(seealso)**: a11y-table-headers;[semantic-html.md](semantic-html.md)

#### a11y-media-transcripts [待核 ID]
- 名称/类型: 视频缺字幕/文稿 —— warning · 优先级 medium · 输出 WARN(源表:视频字幕/文稿;档位未单列[待核])
**这意味(what)**: 页面内嵌视频(`<video>`/iframe 播放器)没有字幕轨道(track)或页内文稿(transcript)。
**为什么(why)**: 无障碍:聋哑/重听用户与静音自动播放场景(社交分发常态)完全依赖字幕——无字幕的视频内容对这部分用户不存在。
**触发(trigger)**: 1) `<video>` 无 `<track kind="captions|subtitles">` 即 warn;2) iframe 嵌入按页内有无 transcript 文本判(判定口径[待核])。
**不修的条件(caveat)**: 第三方平台 iframe 的字幕你控制不了,能做的是页内文稿与描述;自动生成字幕质量差时,重要视频补人工校对版。
**修复(fix)**: `<track kind="captions" srclang label>` 本地字幕;页内 transcript 与 VideoObject 同源;视频分发全案见 [video-geo-guide.md](../content/video-geo-guide.md)。
**关联(seealso)**: sd-required-fields(VideoObject);[video-geo-guide.md](../content/video-geo-guide.md)

#### a11y-iframe-title [待核 ID]
- 名称/类型: iframe/object 缺 title —— warning · 优先级 medium · 输出 WARN(源表:iframe/object 须 title/替代文本;档位未单列[待核])
**这意味(what)**: `<iframe>`(或 `<object>`)没有 title 属性(或等价替代文本)。
**为什么(why)**: 无障碍:SR 把 iframe 当独立浏览区,进入前读 title——无名框架只报"框架",用户不知道里面是广告、表单还是地图,键盘焦点进入无名框架时尤其迷失。
**触发(trigger)**: 任一 `<iframe>`/`<object>` 无 title 或 title 空白即 warn(装饰性隐藏框架的豁免口径[待核])。
**不修的条件(caveat)**: 技术 iframe(埋点/支付回调)用 title="(hidden)" 或 aria-hidden+height=0 处理,不影响判定;视觉无框嵌入(无缝地图)更需要 title 说明身份。
**修复(fix)**: `<iframe title="Google 地图:公司位置">`——每处嵌入给具体身份而非"iframe";装饰性技术框架加 hidden 语义。
**关联(seealso)**: a11y-accessible-name、sd-required-fields(VideoObject);[semantic-html.md](semantic-html.md)

#### a11y-svg-name [待核 ID]
- 名称/类型: img 角色 SVG 缺可访问名 —— warning · 优先级 medium · 输出 WARN(源表:img 角色 SVG 须可访问名;档位未单列[待核])
**这意味(what)**: 承载信息的内联 SVG(role=img 或视觉等价于内容图)没有可访问名——无 `<title>`/`<desc>`、无 aria-label。
**为什么(why)**: 无障碍:SR 默认跳过纯图形,role=img 后会尝试播报但无名则读不出内容——信息图形对盲用户完全不存在。SEO:Google 图片文档建议内联 svg 用 `<title>` 提供替代文本([图片 SEO 文档](https://developers.google.com/search/docs/appearance/google-images))。
**触发(trigger)**: 内联 svg 带 role="img"(或被判为信息图形[判定口径待核])且 accessible name(svg>title 或 aria-label)为空即 warn。
**不修的条件(caveat)**: 装饰性 SVG 的正确做法是 aria-hidden="true"(跳过)而非补名——补名反而制造噪音;判定标准是"这图形承载信息吗"。
**修复(fix)**: 信息 SVG:`<svg role="img" aria-label="描述">` 或内嵌 `<title>`;装饰 SVG:aria-hidden="true";可交互 SVG 图标按 a11y-accessible-name 给名。
**关联(seealso)**: a11y-accessible-name、images-alt-present;[semantic-html.md](semantic-html.md)

#### a11y-alt-duplicate [待核 ID]
- 名称/类型: alt 复读相邻文本 —— warning · 优先级 low · 输出 WARN(源表:alt 不重复相邻链接/图注文本;档位未单列[待核])
**这意味(what)**: 图片的 alt 与紧邻的链接文本或 figcaption 图注完全相同——SR 用户同一句话听两遍。
**为什么(why)**: 无障碍:图文卡片(图+标题链)是最常见布局,alt=标题文本时 SR 逐卡片读两遍标题,信息零增量、耐心双倍消耗。W3C 建议:相邻文本已描述图意时用空 alt([W3C](https://www.w3.org/WAI/tutorials/images/decorative/))。
**触发(trigger)**: img 的 alt 与同容器内链接文本或 figcaption 归一化后相同即 warn(相邻范围的判定口径[待核])。
**不修的条件(caveat)**: 图注已完整描述图意时,alt 可刻意留空(alt="")——图注就是描述,不判缺失(images-alt-present 的口径);本条抓的是"复读"而非"缺失"。
**修复(fix)**: alt 写图内信息(与文字标题互补);图注完整时 alt="";卡片组件模板化——标题进链接、图片描述进 alt,两变量分工。
**关联(seealso)**: images-alt-present、images-alt-generic;[semantic-html.md](semantic-html.md)

#### a11y-aria-typo [待核 ID]
- 名称/类型: ARIA 属性/角色拼错 —— issue · 优先级 high · 输出 CRITICAL(源表 fail;浏览器静默丢弃)
**这意味(what)**: aria-* 属性名或 role 值拼错:aria-lable(丢 e)、aria-labeledby(应为 labelledby)、role="buton"——浏览器静默丢弃,不报任何错。
**为什么(why)**: 无障碍:拼错的 ARIA 等于没写,且零报错渠道——开发者以为配了无障碍,用户端什么都没发生,是"最自信的失效"。
**触发(trigger)**: 1) aria-* 属性名不在 WAI-ARIA 已知属性表;2) role 值不在 ARIA 角色表;3) 属性-角色搭配非法(role=img 上用 aria-expanded)——命中任一即 fail 档(校验表口径[待核])。
**不修的条件(caveat)**: 属性名对但引用值错(aria-labelledby 指向不存在的 id)归 a11y-duplicate-id 关联家族;本条只管词法层。data-* 自定义属性不判。
**修复(fix)**: IDE 装 ARIA 校验(eslint-plugin-jsx-a11y 类);CI 加 ARIA 词法 lint(属性表+角色表白名单);评审对 aria-* 一律查表。
**关联(seealso)**: a11y-aria-parent-child、a11y-accessible-name;[semantic-html.md](semantic-html.md)

#### a11y-aria-hidden [待核 ID]
- 名称/类型: aria-hidden 包裹可聚焦元素 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: aria-hidden="true" 的容器里有可聚焦元素(链接/按钮/输入)——视觉可见、可 Tab 到,但 SR 完全不播报。
**为什么(why)**: 无障碍:键盘用户 Tab 进"不存在"的元素——焦点静默消失、所见与所听分裂,是 ARIA 的头号误用。
**触发(trigger)**: aria-hidden=true 的元素子树内含可聚焦元素(无 disabled/tabindex=-1 豁免)即 fail。
**不修的条件(caveat)**: 合法做法是先禁再隐:元素 disabled 或 tabindex=-1 后再 aria-hidden(折叠菜单收起态);纯装饰容器(无交互)aria-hidden 永远合法。
**修复(fix)**: 隐藏前先移出 Tab 序(tabindex=-1/disabled/条件渲染);折叠类组件用 hidden 属性(视觉+语义双收)替代 aria-hidden;根级禁令见 a11y-aria-hidden-root。
**关联(seealso)**: a11y-aria-hidden-root、a11y-tabindex;[semantic-html.md](semantic-html.md)

#### a11y-aria-hidden-root [待核 ID]
- 名称/类型: html/body 级 aria-hidden —— issue · 优先级 critical · 输出 CRITICAL(源表:html/body 禁 aria-hidden;档位未单列[待核],按 aria-hidden 家族 fail 档从重,两轴校准注明)
**这意味(what)**: `<html>` 或 `<body>` 元素上出现 aria-hidden 属性(常见 true——SPA 加载态/新手引导插件的遗产)。
**为什么(why)**: 无障碍:根级隐藏让整页对 AT 消失——浏览器里正常显示,SR 用户听到的却是空页面,是能写出的最重无障碍事故之一。
**触发(trigger)**: `<html>` 或 `<body>` 元素带 aria-hidden 属性即触发(无论值)。
**不修的条件(caveat)**: 无豁免——任何"暂时隐藏全页"的实现都该用视觉遮罩(overlay)而不是根级语义隐藏;命中即最高优先级修。
**修复(fix)**: 排查加载态/引导(tour)组件对 body 的属性操作,改视觉层(opacity/overlay);CI 断言 html/body 永不带 aria-hidden。
**关联(seealso)**: a11y-aria-hidden、js-runtime-hygiene;[semantic-html.md](semantic-html.md)

#### a11y-aria-parent-child [待核 ID]
- 名称/类型: ARIA widget 父子角色缺失 —— warning · 优先级 medium · 输出 WARN(源表:ARIA widget 须有所需父子角色,tab 在 tablist 内/option 在 listbox 内;档位未单列[待核])
**这意味(what)**: ARIA 复合控件的角色结构不完整:role=tab 不在 role=tablist 内、role=option 不在 role=listbox 内、menuitem 不在 menu 内。
**为什么(why)**: 无障碍:复合控件的 AT 行为(方向键导航/选中播报)由完整角色树驱动——孤儿 tab 退化为普通元素,键盘用户按方向键没反应。
**触发(trigger)**: 需容器角色清单(tab/option/menuitem/menuitemcheckbox 等[清单待核])中的角色,其祖先链内无对应 required parent 角色即 warn。
**不修的条件(caveat)**: 原生元素优先(`<select><option>` 天生完整)——能用原生就不要手搓 ARIA;本条命中常提示该换原生组件。
**修复(fix)**: 补容器角色(tab→tablist、option→listbox、menuitem→menu)或换原生元素;复合控件优先用角色树内置的成熟组件库。
**关联(seealso)**: a11y-aria-typo、a11y-list-structure;[semantic-html.md](semantic-html.md)

#### a11y-list-structure [待核 ID]
- 名称/类型: 列表子元素非法 —— warning · 优先级 low · 输出 WARN(源表:列表只含 li;档位未单列[待核])
**这意味(what)**: `<ul>`/`<ol>` 的直接子元素不是 `<li>`——塞了 div/p/文本节点,或 `<li>` 裸奔在列表容器外。
**为什么(why)**: 无障碍:SR 播报列表先报"列表,共 N 项"再逐项读——非法子元素打断计数,项数与实际不符,用户对内容量失去预期。
**触发(trigger)**: `<ul>`/`<ol>` 的 Element 直接子节点标签 ∉ {li, script, template}(HTML 规范豁免口径[待核])即 warn。
**不修的条件(caveat)**: 历史模板里 ul 套 div 分组的布局用法,视觉无碍低风险,可排期修;display:list-item 的 div 不算——语义看 DOM 不看样式。
**修复(fix)**: 分组需求用嵌套 li(ul>li>ul>li);包裹层移到 ul 外;模板 lint 列表子元素白名单。
**关联(seealso)**: a11y-aria-parent-child、sd-breadcrumblist;[semantic-html.md](semantic-html.md)

#### a11y-role-presentation [待核 ID]
- 名称/类型: role=none/presentation 被反证 —— warning · 优先级 low · 输出 WARN(源表:role=none/presentation 不被 ARIA/可聚焦性反证;档位未单列[待核])
**这意味(what)**: 元素声明 role="none"/"presentation"(意图:从无障碍树抹掉),但它带全局 ARIA 属性(aria-label 等)或含可聚焦子元素——声明与实态互相反驳。
**为什么(why)**: 无障碍:presentation 说"我是装饰",aria-label 说"我有名字"——AT 按规范丢弃矛盾的角色声明回退隐式语义,行为不可预期;可聚焦子元素更让"隐藏"名存实亡(与 a11y-aria-hidden 同族矛盾)。
**触发(trigger)**: 1) role=none/presentation 元素带全局 aria-* 属性或含可聚焦子元素即 warn;2) `<table role=presentation>` 内含 th/scope(表头是内容信号,布局表不该有)同类触发[表格分型待核]。
**不修的条件(caveat)**: role=presentation 的正确用法(装饰图/布局表抹除)不受影响——本条只抓"声明与实态矛盾";命中多半该删 role 而非删属性。
**修复(fix)**: 真装饰:去掉矛盾属性、聚焦子元素先移出;真内容:删 role=恢复语义;布局表抹 presentation 时确保内部无 th。
**关联(seealso)**: a11y-aria-hidden、a11y-aria-typo;[semantic-html.md](semantic-html.md)

#### a11y-input-image-alt [待核 ID]
- 名称/类型: 图像提交按钮缺 alt —— warning · 优先级 medium · 输出 WARN(源表:`<input type=image>` 须 alt;档位未单列[待核])
**这意味(what)**: `<input type="image">`(图像形式的提交按钮)没有 alt 属性。
**为什么(why)**: 无障碍:图像按钮的可访问名只能来自 alt——无名时 SR 只读"提交按钮 图像"或文件名,用户不知道点了会提交什么。
**触发(trigger)**: `<input type="image">` 无 alt 或 alt 空白即 warn。
**不修的条件(caveat)**: 注意与装饰 img 相反:此处空 alt(alt="")不合规——提交按钮必须有名字;遗留表单至少补 alt="搜索" 类动作名。
**修复(fix)**: 首选换 `<button type="submit">`(内嵌图标+文本);遗留表单补动作名 alt。
**关联(seealso)**: a11y-accessible-name、images-alt-present、a11y-form-label;[semantic-html.md](semantic-html.md)

#### a11y-duplicate-id [待核 ID]
- 名称/类型: ID 重复 —— issue · 优先级 high · 输出 CRITICAL(源表 fail;svg 内 url(#id) 引用的 clipPath 豁免)
**这意味(what)**: 同一文档里 id 属性值出现多次——aria-labelledby/label for/fragment 锚点全部解析到第一个匹配,其余静默失效。
**为什么(why)**: 无障碍:aria-labelledby 与 `<label for>` 按 id 查找,重复 id 让第二个以后的元素失去命名/标签关联——SR 读到的是别人的名字。
**触发(trigger)**: 1) 全文档 id 值去重后仍 >1 即 fail 档;2) svg defs 族的 url(#id) 引用豁免。
**不修的条件(caveat)**: 豁免仅限 SVG defs 族;HTML 层的重复 id 没有正当形态——第三方组件注入的重复 id 也该报给组件方修。
**修复(fix)**: 组件 id 加实例后缀(useId() 类工具);label/aria 引用与 fragment 统一走 id 注册表;CI 断言全文档 id 唯一。
**关联(seealso)**: a11y-form-label、links-broken-anchor、a11y-one-label-per-control;[semantic-html.md](semantic-html.md)

### Social(9 条,权重 3%)

og:title/description/image 各=warn;**og:image 推荐 1200×630(配 og:image:width/height meta)**;og:url=warn;**og:url 与 canonical 不一致=fail**;twitter:card(summary_large_image)=warn;分享按钮(**≥2 平台**)=warn;社交资料链接(**≥3 个**,入 Organization sameAs)=warn。

**解释层(4 条;ID 未公布原文,标 [待核])**

#### social-og-url-canonical
- 源表:warn/fail · 权重 1。比较 og:url 与 canonical(host 小写、去尾斜杠):不一致或有 canonical 无 og:url=fail;只有 og:url 或两者都无=warn。工具约定。建议优先级 medium。
**依据**: Open Graph 协议把 og:url 定义为"The canonical URL of your object that will be used as its permanent ID in the graph"([ogp.me](https://ogp.me/))。og:url 与 canonical 不同,社交平台归并分享计数的 URL 与搜索引擎的规范 URL 就分裂。核对 2026-10-18。
**判据**: 通过=og:url 与 canonical 同值。失败=不同(常见是 og:url 带 utm 参数)。
**执行**: `curl -s URL | grep -oiE '<meta[^>]+property=.?og:url[^>]*>'` 与 G1 比对;site_audit 只查 og:title/description/image,不查 og:url。
**修复**: og:url 复用 canonical 的同一模板变量。
**关联**: core-canonical-conflicting;[head-elements.md](head-elements.md) OG 消费矩阵

#### social-og-basic [待核 ID]
- 名称/类型: og 标签家族缺失 —— warning · 优先级 low · 输出 WARN(源表各=warn;twitter:card 同构)
**这意味(what)**: 页面缺 og:title/og:description/og:image(og:url 缺失另计 warn,与 canonical 的冲突见 social-og-url-canonical);twitter:card 同构——缺=warn,推荐值 summary_large_image。
**为什么(why)**: og 标签是社交平台与主流聊天应用(WhatsApp/Slack/Discord)抓分享卡片的依据;缺了平台自行抓页面,卡片图文不可控——分享 CTR 的隐形漏斗。对搜索排名无影响,纯分享层缺信号,故 low。
**触发(trigger)**: 逐一断言 og:title/og:description/og:image/og:url 存在且非空;twitter:card 值应为 summary_large_image;任一缺失即 warn。本家族其余规则同构:字段不同、阈值同为存在性检查。
**不修的条件(caveat)**: og 标签不影响搜索排名,然而决定分享卡片完整度,所以一般建议核心模板页全配。但法律/结账流等不需要被分享的页面可豁免。
**修复(fix)**: 模板用与 title/description 同源变量输出 og:title/og:description;og:image 用固定比例专图(见 social-og-image-dimensions);twitter:card 配 summary_large_image。
**关联(seealso)**: social-og-url-canonical、social-og-image-dimensions;[head-elements.md](head-elements.md) OG 消费矩阵

#### social-og-image-dimensions [待核 ID]
- 名称/类型: og:image 尺寸 —— warning · 优先级 low · 输出 WARN(源表 warn;推荐 1200×630,配 og:image:width/height meta)
**这意味(what)**: og:image 分辨率明显偏离 1200×630(1.91:1),或未配 og:image:width/og:image:height meta。
**为什么(why)**: 各平台分享卡裁切比例不一,1.91:1 是最大公约数;尺寸离谱时平台裁掉关键内容或弃图。配 width/height meta 让平台免下整图即可算占位,加快卡片渲染。
**触发(trigger)**: 1) og:image 目标宽高比偏离 1.91:1(容差阈值源表未公布[待核]);2) 无 og:image:width/og:image:height 即 warn。
**不修的条件(caveat)**: 尺寸不影响 SEO,然而影响分享卡展示完整度,所以一般建议 1200×630 专图。但主投放平台明确(如以 X 的 1:1 为主)时可按主平台调优。
**修复(fix)**: 出 1200×630 专图;head 补 og:image:width/og:image:height;每页独立图,别全站一张。
**关联(seealso)**: social-og-basic;[head-elements.md](head-elements.md)

#### social-engagement [待核 ID]
- 名称/类型: 分享按钮与社交资料链接 —— opportunity · 优先级 insight · 输出 WARN(源表 warn;分享按钮 ≥2 平台、社交资料链接 ≥3 个)
**这意味(what)**: 站点缺社交基建:分享按钮覆盖 <2 平台,或站内社交资料链接 <3 个。
**为什么(why)**: 分享按钮降低分发摩擦;资料链接的作用更大——它们是 Organization schema sameAs 的候补实体证据,帮引擎把站点与官方社交账号绑定为同一实体(见 [entity-signal-checklist.md](entity-signal-checklist.md))。典型缺信号/机会项,不构成错误。
**触发(trigger)**: 1) 分享按钮平台数 <2 即 warn;2) 页脚/联系页社交资料外链 <3 个即 warn(已入 sameAs 的链接计入)。
**不修的条件(caveat)**: 社交基建不影响排名,然而影响分发与实体确认,所以一般建议按受众补齐。但 B2B 内部系统/无社交属性的站点两项都可合理不修。
**修复(fix)**: 分享按钮接 2+ 主平台;页脚列官方资料并同步写入 Organization sameAs。
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
**关联(seealso)**: url-shape、url-length;[link-architecture-patterns.md](link-architecture-patterns.md)

#### url-shape [待核 ID]
- 名称/类型: URL 形态卫生家族 —— warning · 优先级 low · 输出 WARN/CRITICAL(源表:大写/下划线/双斜杠/非 ASCII/重复路径段/HTTP-HTTPS 双可达=warn;%20 编码空格=fail)
**这意味(what)**: URL 含形态瑕疵:大写字母、下划线分词、双斜杠、非 ASCII 字符、重复路径段(/shoes/shoes/)、HTTP 与 HTTPS 双可达不互跳(以上各 warn);最重的是 %20 编码空格(fail)。
**为什么(why)**: 形态决定"同一 URL 会有几种写法":大写混用制造大小写变体(部分服务器区分大小写);下划线不被当词分隔符;双斜杠/重复段制造规范化噪音;双协议可达是重复站点种子。%20 空格是硬伤——空格在 URL 中非法,编码形态在点击/引用/重写链条上最易断裂。
**触发(trigger)**: 逐项:含大写 → warn;含 _ → warn;含 // → warn;路径段重复 → warn;含非 ASCII → warn;http 与 https 版本均 200 不互跳 → warn;含 %20 → fail。
**不修的条件(caveat)**: 单项瑕疵不(直接)影响排名,然而每项都在增加变体重复的概率,所以一般建议全站 lint。但非 ASCII(中文/日文 slug)在相应语种市场是正当形态,warn 不等于要求转拼音。
**修复(fix)**: 新 URL 全小写+连字符;CMS 输出层统一规范化;老 URL 301 到规范形;http 单向 301 到 https。
**关联(seealso)**: url-slug-quality、crawl-canonical-form-drift;[redirects-canonical.md](redirects-canonical.md)

#### url-length [待核 ID]
- 名称/类型: URL 路径长度 —— warning · 优先级 low · 输出 WARN(源表 warn;路径 ≤75 字符)
**这意味(what)**: URL 路径部分超过 75 字符(不含协议与域名的口径[待核])。
**为什么(why)**: 长度本身不是排名因素,但超长路径几乎总意味着嵌套过深(点击距离超标,见 links-depth)、路径关键词堆砌、或筛选状态写进路径——这些才是问题,长度只是症状。75 字符也是 SERP 展示与外链复制的经验舒适线。
**触发(trigger)**: 解析 URL 取路径段;长度 >75 即 warn。
**不修的条件(caveat)**: URL 长度不(直接)影响 SEO,然而它是结构与堆砌的症状指标,所以一般建议控制。但多级分类的文档站(v2/api/auth/methods)超线是结构真实,不是错误。
**修复(fix)**: 压层级(去掉冗余中间层)、砍路径关键词堆砌;筛选状态移到参数并由规范化收口。
**关联(seealso)**: links-depth、url-slug-quality;[link-architecture-patterns.md](link-architecture-patterns.md)

#### url-query-params [待核 ID]
- 名称/类型: 查询参数家族 —— issue/warning · 优先级 high(会话 ID=fail)/medium(计数与追踪) · 输出 CRITICAL/WARN(源表:参数 3-5 个=warn、>5=fail;同名参数重复或多个 ?=畸形 warn;URL 会话 ID=fail;UTM/追踪参数=warn)
**这意味(what)**: 查询串失控:参数 3-5 个 warn、>5 个 fail;同名参数重复/多个 ? 畸形 warn;URL 带会话 ID(PHPSESSID/jsessionid 形态)fail;站内链接带 UTM/追踪参数 warn。
**为什么(why)**: 参数爆炸是抓取预算头号杀手:每个参数组合都是潜在唯一 URL,爬虫在组合空间指数级发散,预算耗尽时真页面反而抓不到。会话 ID 更重:每访客一个 URL=无限重复页,是 2000 年代就被定性的反模式。UTM 入内链则是把追踪污染引进自己站内。
**触发(trigger)**: 解析查询串:参数计数 3-5 → warn、>5 → fail;同名键 ≥2 次或 ≥2 个 ? → warn;参数名匹配会话 ID 模式 → fail;内链 href 含 utm_/gclid 等追踪参数 → warn。
**不修的条件(caveat)**: 参数本身不(直接)影响排名,然而参数空间决定抓取预算的消耗方式,所以一般建议站内链接零追踪参数、筛选参数规范化收口。但合法功能参数(分页 ?page=、排序 ?sort=)不可删——要的是规范化,不是消灭。
**修复(fix)**: 内链剥 UTM(仅保留外链入口);筛选参数 canonical 收口或 robots.txt 屏蔽;会话状态改 cookie 承载;参数计数超标先审功能设计。
**关联(seealso)**: crawl-sitemap-non-canonical、url-search-indexed;[robots-txt-reference.md](robots-txt-reference.md)

#### url-search-indexed [待核 ID]
- 名称/类型: 站内搜索结果被索引 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 站内搜索结果页(?s=/q=/search= 形态,键名口径[待核])可被索引——无 noindex、甚至进了 sitemap/内链。
**为什么(why)**: 搜索结果页是"关于查询的链接列表",无独立内容价值:引擎明确不喜欢索引一层"搜索结果套搜索结果"(用户从搜索引擎点进你的搜索页,看到的还是一堆链接);无限查询组合也是抓取预算黑洞。
**触发(trigger)**: 1) URL 匹配站内搜索参数形态;2) 页面可索引(无 noindex、被内链/sitemap 引用)即 warn。
**不修的条件(caveat)**: 搜索页索引不(直接)拖累其他页面排名,然而批量索引会稀释抓取预算,所以一般建议模板级 noindex。但确有搜索流量价值的长尾工具站,可把高价值查询做成内容化落地页保留索引——先看 GSC 流量再一刀切。
**修复(fix)**: 搜索结果模板加 noindex(整模板而非逐页);从 sitemap 与内链清除搜索 URL;站内搜索入口改 POST 或前端路由,不生成可爬 URL。
**关联(seealso)**: sd-searchaction、url-query-params;[robots-txt-reference.md](robots-txt-reference.md)

### Redirects(11 条,权重 3%)

meta refresh=warn;JS 重定向=warn;HTTP Refresh 头=warn;环=fail;301(永久/传权重)vs 302(临时)用错=warn;目标 4xx/5xx=fail;**静态资源被重定向=warn**;大小写规范化重定向=warn;**渲染专属三条**:resource-broken(资源重定向终点 4xx/5xx=fail)/resource-loop(资源重定向环,浏览器 ERR_TOO_MANY_REDIRECTS=fail)/**resource-chain(资源 ≥2 跳=warn,单跳 http→https/尾斜杠视为良性)**。

**解释层(7 条;ID 未公布原文,标 [待核];JS/HTTP Refresh 头两条并入 meta-refresh 条目陈述)**

#### redirect-loop
- 源表:fail · 权重 15。重定向链回到已访问 URL。工具约定。建议优先级 critical。
**依据**: Googlebot 最多跟约 10 跳,环永远到不了内容;Search Console 对重定向失败报错([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors))。核对 2026-10-18。
**判据**: 通过=链在有限跳内到达非 3xx。失败=回到途经 URL。
**执行**: `REDIR URL` 出现 `[CRITICAL] 检测到循环`(退出码 1)。
**修复**: 排查强制 https、强制 www、尾斜杠三类规则的叠加顺序,合并为一步到位。
**关联**: crawl-canonical-loop、links-redirect-chains;[redirects-canonical.md](redirects-canonical.md)

#### redirect-broken
- 源表:fail · 权重 15。页面重定向链的最终状态是 4xx/5xx(爬取中无重定向直达 4xx/5xx 的页也算)。工具约定。建议优先级 critical。
**依据**: Google 不索引返回 4xx 的 URL,已索引的会被移除;5xx 持续则移除([HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors))。旧 URL 的去向因此丢失。核对 2026-10-18。
**判据**: 通过=终点 2xx。失败=终点 4xx/5xx。
**执行**: `REDIR URL` 看「终态: HTTP」行,4xx/5xx 即失败(脚本只打印不判定)。迁移后按映射表逐行跑。
**修复**: 终点恢复内容,或改指最近亲的存活页;不要统一跳首页(Google 可能当 soft 404)。
**关联**: links-broken-internal、crawl-sitemap-non-200;[http-status-codes.md](http-status-codes.md)

#### redirect-type
- 源表:warn · 权重 12。链中某跳是临时码(302/303/307)而不是 301/308。工具约定。建议优先级 medium。
**依据**: 要改变页面在结果中显示的 URL,Google 推荐尽量用服务端永久重定向(301/308);301 是"目标应被处理"的强信号,302 是弱信号;临时重定向保留源页在结果中([重定向文档](https://developers.google.com/search/docs/crawling-indexing/301-redirects);[HTTP 状态码文档](https://developers.google.com/search/docs/crawling-indexing/http-network-errors))。核对 2026-10-18。
**判据**: 通过=永久搬迁用 301/308,临时活动用 302/307。失败=永久变化用了临时码。
**执行**: `REDIR URL` 出现 `[WARN] 第 N 跳是…临时重定向,建议改 301`(脚本只对 http→https、加去 www、尾斜杠三类永久变化报警,其他场景人工判)。
**修复**: 永久变更改 301/308;临时场景保持 302/307。
**关联**: redirect-loop;[redirects-canonical.md](redirects-canonical.md)

#### redirect-meta-refresh
- 源表:`redirect-meta-refresh` warn/fail · 权重 15;同族 `redirect-http-refresh`(Refresh 响应头,fail · 权重 10)、`redirect-javascript`(warn · 权重 12)。工具约定。建议优先级 medium。
**依据**: Google 把 0 秒 meta refresh 与 0 秒 HTTP Refresh 当永久重定向,延时的当临时重定向;服务端重定向最可靠,做不到时才用 meta refresh,JS 跳转更靠后([重定向文档](https://developers.google.com/search/docs/crawling-indexing/301-redirects))。"非 0 秒可能不跟"不成立。核对 2026-10-18。
**判据**: 通过=跳转用服务端 3xx。失败=用 meta refresh、Refresh 头或 JS 实现跳转。5 秒轮播一类非跳转语义不算。
**执行**: `curl -s URL | grep -oiE '<meta[^>]+http-equiv=.?refresh[^>]*>'`;`curl -sI URL | grep -i '^refresh:'`;JS 跳转人工查 `location` 赋值。
**修复**: 换成服务端 301/302;确需保留的引导页写清 canonical。
**关联**: redirect-type;[redirects-canonical.md](redirects-canonical.md)

#### redirects-static-resource [待核 ID]
- 名称/类型: 静态资源被重定向 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 页面引用的静态资源(CSS/JS/图/字体)URL 自身返回 3xx,要再跳一次才拿到内容。
**为什么(why)**: 每条资源重定向都是渲染瀑布里多出的一跳:握手与请求白付两次,渲染阻塞资源(同步 CSS)的重定向直接串行拖慢 FCP/LCP;抓取侧同样双倍成本。典型来源:资源改版后旧 URL 301 保底、CDN 规则把 /assets/ 整体跳新路径、http 资源在 https 页被协议跳转。
**触发(trigger)**: 提取页面子资源 URL;任一返回 3xx 即 warn(终点 4xx/5xx 或成环另归 redirects-resource-chain 的 fail 档)。
**不修的条件(caveat)**: 单条资源重定向不影响排名,然而它在渲染关键路径上按毫秒计价,所以一般建议资源引用直指最终 URL。但迁移窗口期保留旧资源 URL 的 301 兜底是正当缓冲,发版后收直。
**修复(fix)**: 模板/构建产物里资源引用写最终 URL;http 资源引用改 https 直连;CDN 层把跳转规则改写为内部重写。
**关联(seealso)**: redirects-resource-chain、perf-render-blocking;[redirects-canonical.md](redirects-canonical.md)

#### redirects-case-normalization [待核 ID]
- 名称/类型: 大小写规范化重定向 —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: URL 仅因大小写差异被重定向(/About → /about)——站点在用重定向兜 URL 大小写不一致。
**为什么(why)**: host 之后的路径大小写是否敏感取决于服务器/CDN,两种策略混用时唯一安全的收口是统一小写+301;但"每条内链先写成大写再靠 301 兜底"意味着每次点击都付一跳——这是把规范化成本从模板层转嫁到运行时。与 url-shape/technical-url-consistency 同源:根因是 URL 生成不规范。
**触发(trigger)**: 重定向的 source 与 target 仅大小写不同(其余成分一致)即 warn。
**不修的条件(caveat)**: 规范化重定向本身是正确收口(比双 200 好),然而它标记模板还在产大写 URL,所以一般建议源头改小写、301 只留兜底。但从大小写不敏感服务器迁到敏感服务器时,这批 301 是必要过渡,可长期保留。
**修复(fix)**: URL 生成层统一小写输出;内链/模板/sitemap 排查大写引用;301 规则保留作外链兜底。
**关联(seealso)**: technical-url-consistency、url-shape;[redirects-canonical.md](redirects-canonical.md)

#### redirects-resource-chain [待核 ID]
- 名称/类型: 资源重定向链家族(渲染专属三条) —— issue/warning · 优先级 high(fail 档)/medium · 输出 CRITICAL/WARN(源表:resource-broken 资源重定向终点 4xx/5xx=fail;resource-loop 资源重定向环,浏览器 ERR_TOO_MANY_REDIRECTS=fail;resource-chain 资源 ≥2 跳=warn,单跳 http→https/尾斜杠视为良性)
**这意味(what)**: 子资源重定向的三种深浅:链终点 4xx/5xx(资源实际丢失)、重定向成环(资源永不可得)、链长 ≥2 跳。
**为什么(why)**: 资源层与页面层(links-redirect-chains)同构但更苛:页面重定向用户还能多点一次,资源重定向直接决定渲染成败——CSS 链断则整页无样式,脚本链断则交互与注解注入全灭。单跳 http→https/尾斜杠被显式豁免为良性(规范化常态),≥2 跳才算链。
**触发(trigger)**: 渲染后逐资源跟踪 Location:1) 终点 4xx/5xx 即 fail;2) 回到途经任一 URL 即 fail;3) 跳数 ≥2 即 warn;4) 单跳且属 http→https/尾斜杠形态不报。
**不修的条件(caveat)**: 家族判定的是引用层的懒——资源本体搬家后引用没跟上,所以一般建议构建期校验全部资源 URL 直达 200。但第三方资源(外源字体/脚本)的重定向不在掌控内,先分类再处置:能换 URL 的换,不能换的评估自托管。
**修复(fix)**: 构建管道加资源 URL 终态断言(直达 200);版本化文件名+固定 CDN 路径消除跳转;外源资源锁定版本化 URL。
**关联(seealso)**: redirects-static-resource、js-runtime-hygiene、links-redirect-chains;[redirects-canonical.md](redirects-canonical.md)、[rendering-seo.md](rendering-seo.md)

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
**关联(seealso)**: mobile-viewport-config、mobile-overflow;[mobile-seo.md](mobile-seo.md)

#### mobile-viewport-config [待核 ID]
- 名称/类型: viewport 配置家族 —— issue/warning · 优先级 high · 输出 CRITICAL(多 viewport、禁缩放,源表 fail)/WARN(缺 device-width、content 规范,源表 warn)
**这意味(what)**: viewport meta 存在但配置错:缺 width=device-width、content 不规范(width 缺失/initial-scale≠1/设了 minimum-scale)、文档里多条 viewport、或用 user-scalable=no/maximum-scale=1 禁用缩放。
**为什么(why)**: 移动优先索引下 viewport 是渲染的控制面:缺 device-width 按桌面宽渲染再缩放,字号与点击目标全错;禁缩放拿走弱视用户的最后手段(捏合放大)——无障碍硬红线;多 viewport 时浏览器取舍不一,行为不可控。与 core-viewport(缺失=fail)分工:那条管"有没有",本条管"对不对"。
**触发(trigger)**: 1) viewport meta 计数 >1 即 fail;2) content 含 user-scalable=no 或 maximum-scale=1 即 fail;3) 无 width=device-width 即 warn;4) width 缺失/initial-scale≠1/含 minimum-scale 即 warn。
**不修的条件(caveat)**: viewport 配置影响渲染形态与可用性,不改变内容相关度,所以一般建议按规范值整站统一。但全屏交互(地图/画布)确需局部禁缩放时,只在该视图动态设置并给替代操作。
**修复(fix)**: 单条 `<meta name="viewport" content="width=device-width, initial-scale=1">`;删 user-scalable/maximum-scale/minimum-scale;刘海屏加 viewport-fit=cover。
**关联(seealso)**: core-viewport、mobile-font-size;[mobile-seo.md](mobile-seo.md)、[head-elements.md](head-elements.md)

#### mobile-overflow [待核 ID]
- 名称/类型: 横向滚动 —— issue/warning · 优先级 high · 输出 WARN/CRITICAL(源表 warn/fail;分型口径源表未公布[待核])
**这意味(what)**: 移动视口(常见 ~375px)下页面出现横向滚动——有元素超出视口宽度。
**为什么(why)**: 横向滚动是移动可用性的一票否决项:双轴滚动让用户极易迷失,"内容超出视口"长期是移动可用性评估的硬伤形态。常见肇因:固定宽度元素(表格/图/iframe 未 max-width)、绝对定位残片、长串不换行(裸 URL)。
**触发(trigger)**: 1) ~375px 视口渲染;2) scrollWidth > innerWidth 即触发;3) warn/fail 分型[待核:常见按超出幅度与是否整页双轴滚动分档]。
**不修的条件(caveat)**: 局部横向滚动区(轮播/代码块/宽表)是可用交互形态,本条针对整页级双轴滚动;命中后先定位溢出元素,别全局 overflow-x:hidden 掩盖——那只是把症状藏给用户。
**修复(fix)**: img/iframe/video 加 max-width:100%;宽表包横向滚动容器或改卡片式;fixed 宽度改响应式;pre/长 URL 强制换行。
**关联(seealso)**: mobile-font-size、mobile-interstitial;[mobile-seo.md](mobile-seo.md)

#### mobile-interstitial [待核 ID]
- 名称/类型: 侵扰性插页 —— issue/warning · 优先级 high · 输出 WARN/CRITICAL(源表 warn/fail;官方三形态+豁免清单)
**这意味(what)**: 用户从搜索进入后立即遭遇遮蔽主内容的弹窗/独立插页页,或 cookie/GDPR/年龄验证/登录类横幅采用违规形态(全屏、难关闭、进入即弹)。
**为什么(why)**: Intrusive Interstitials 是 2017-01-10 生效的算法性排名调整(仅移动端,非手动动作)。官方三形态:进入即弹遮主内容的弹窗、须关闭才能看内容的独立插页页、首屏伪内容横幅。豁免清单:法律必需的 cookie/GDPR 横幅(合规形态:非全屏、易关)、登录墙(公开内容有免费替代)、占合理比例且可关的横幅——政策全拆解见 [mobile-seo.md](mobile-seo.md) 2.5 节。
**触发(trigger)**: 进入页面即检测遮罩(全屏 overlay/独立插页跳转);按"进入即弹/遮蔽比例/关闭难度"分型 warn/fail[分型口径源表未公布,待核]。
**不修的条件(caveat)**: 合规横幅不(必然)触发惩罚——判定看形态不看业务目的,所以一般建议 cookie/年龄类用非全屏、易关的形态。但"合规必需"不等于"任意形态免责",全屏 GDPR 墙同样在打击面内。
**修复(fix)**: 弹窗改用户交互后触发;横幅收紧为可关的顶部条;插页页移除;关闭目标(×)至少 24×24 CSS px(WCAG 2.5.8),最好 44×44。
**关联(seealso)**: mobile-overflow、legal-cookie-consent;[mobile-seo.md](mobile-seo.md)

#### mobile-image-maps [待核 ID]
- 名称/类型: 客户端图像地图 —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: 页面用 `<map>`/`<area>` 客户端图像地图做导航或交互——固定像素坐标的热区不适配。
**为什么(why)**: image map 的热区是绝对像素坐标:响应式图片缩放后热区不再对位(点 A 命中 B),触屏精度下小热区几乎不可点;屏幕阅读器对 area 的支持参差。这是 90 年代遗产技术,现代替代(CSS 定位/SVG 热区/拆分图片)全面更优。
**触发(trigger)**: 页面含 `<map>`+`<img usemap>` 即 warn(热区数量的分级口径[待核])。
**不修的条件(caveat)**: image map 不(直接)影响排名(引擎能提取 area href),然而触屏交互失准是可用性实伤,所以一般建议重构。但按渲染尺寸动态换算坐标的实现(热区随图等比缩放)可用,命中后先确认是否自适应。
**修复(fix)**: 导航型改列表/按钮组;图形热点改 SVG 内嵌 `<a>`(可缩放+可访问名);必须保留时热区坐标按渲染尺寸动态计算。
**关联(seealso)**: mobile-overflow;[semantic-html.md](semantic-html.md)

#### mobile-parity [待核 ID]
- 名称/类型: 移动-桌面内容平价(parity 五条) —— issue/warning · 优先级 high · 输出 CRITICAL/WARN(源表:content/title+description/canonical=warn/fail,structured-data=fail(JSON-LD 桌面有移动无),links(内链数量可比)=warn;`--mobile` 双渲染对比)
**这意味(what)**: 同一 URL 的移动与桌面渲染(或 m. 站双域)内容不对等:主内容/标题描述/canonical 出入、桌面有移动无的 JSON-LD、内链数量不可比。
**为什么(why)**: 移动优先索引下引擎用移动版内容评级——桌面专属内容等于不存在;m. 站遗留时瘦移动版被索引,www 的优化投入落空。JSON-LD 桌面有移动无是最隐蔽的形态:富结果资格随移动版消失。parity 检查法(双视口抓取 diff、GSC 按设备拆分、Live Test)见 [mobile-seo.md](mobile-seo.md) 1.4 节:diff >20% 黄旗、>50% 红旗。
**触发(trigger)**: `--mobile` 双渲染(~375px 与 ~1280px)对比:1) 主内容文本量/title+description/canonical 不一致 → warn/fail[分型待核];2) 桌面 JSON-LD 移动缺失 → fail;3) 内链数量显著不可比 → warn。
**不修的条件(caveat)**: parity 差异不(必然)是错——大屏增强内容(桌面才显示的对比图)被移动省略是响应式常态,移动优先索引按移动版算,损失的是增强加分而非硬伤。但结构性差异(schema 缺失/内容整段缺失)必须修平。
**修复(fix)**: 结构化数据与关键注解两端同源输出;m. 站遗留按 [mobile-seo.md](mobile-seo.md) 1.3 风险清单收敛到响应式;双模板站点建 parity CI diff。
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
**关联(seealso)**: htmlval-duplicate-meta、htmlval-head-content、content-deploy-hygiene;[semantic-html.md](semantic-html.md)、[head-elements.md](head-elements.md)

#### htmlval-duplicate-meta [待核 ID]
- 名称/类型: 重复 title/description(title 家族与 description 家族收口) —— issue · 优先级 high · 输出 CRITICAL(源表:多 title=fail;多 description=fail;title 在 head 外=fail)
**这意味(what)**: 文档里不止一个 `<title>` 或不止一条 meta description,或 title 出现在 head 之外。
**为什么(why)**: 多条声明时引擎取哪条不可控(常见取第一条或最后一条,实现不一),SERP 展示与你的优化对象脱节;title 在 head 外按无效处理等于没写。与 core-canonical-multiple(多条 canonical)同构:重复声明的歧义性比缺失更糟——坏信号>缺信号的又一次体现。title/description 家族的其余形态(缺失/长度/跨页重复)分别见 core-title-present、core-description-present、core-title-unique、content-duplicate-description,本条收口"多条/错位"。
**触发(trigger)**: 1) `<title>` 计数 >1 即 fail;2) meta description 计数 >1 即 fail;3) title 元素祖先链不含 head 即 fail。
**不修的条件(caveat)**: 无豁免;双写几乎总是两套注入(框架默认+业务代码)各写一次,修复是找源头,不是删一条留一条。
**修复(fix)**: head 注入收敛单一出口(head 组件/helmet 类方案);CI 断言 title=1、description=1 且都在 head 内。
**关联(seealso)**: core-title-present、core-description-present、core-canonical-multiple、htmlval-document-structure;[head-elements.md](head-elements.md)

#### htmlval-head-content [待核 ID]
- 名称/类型: head 非法元素家族 —— warning · 优先级 low · 输出 WARN(源表 warn;head 白名单 meta/title/link/script/style/base/noscript;head 内 noscript=warn)
**这意味(what)**: head 里出现白名单之外的元素(文本、div、img 等),或 head 内放了 noscript。
**为什么(why)**: HTML 规范限定 head 只容纳元数据元素;非法内容触发解析器把 head 提前截断,把后续本该在 head 里的声明(meta/canonical)挤进 body——连带制造 core-canonical-outside-head 一类问题。head 内 noscript 是特例:其内部只允许 link/style/meta,常被误用于塞内容或脚本。
**触发(trigger)**: 1) head 子元素标签名 ∉ {meta,title,link,script,style,base,noscript}(纯空白文本豁免)即 warn;2) head 内存在 noscript 即 warn。
**不修的条件(caveat)**: 解析器会自愈重组,多数用户看不出异常,然而重组后的 DOM 与源码意图错位是隐患源,所以一般建议 head 纯净。但模板注释/条件注释残片命中属误报级,顺手清理即可。
**修复(fix)**: 内容元素全部移出 head;noscript 的降级样式放 style、跳转提示放 body;模板 lint 头部白名单。
**关联(seealso)**: htmlval-document-structure、core-canonical-outside-head;[head-elements.md](head-elements.md)

#### htmlval-base [待核 ID]
- 名称/类型: base 元素误用 —— issue/warning · 优先级 medium · 输出 CRITICAL(href 空/畸形/非 HTTP(S),源表 fail)/WARN(多条,源表 warn;须 ≤1 条)
**这意味(what)**: `<base>` 的 href 为空、畸形或非 HTTP(S) 协议,或文档里有多条 base。
**为什么(why)**: base 重定义全页相对 URL 的解析基准:它一坏,页内所有相对链接/canonical/hreflang 的解析结果整体漂移——一条坏 base 能同时引爆相对 URL 类判罚,是单点故障放大器。规范限定每文档至多一条。
**触发(trigger)**: 1) base href 空/不可解析/协议非 http(s) 即 fail;2) base 计数 >1 即 warn。
**不修的条件(caveat)**: base 写对时不产生任何 SEO 问题,然而它的全局副作用让任何后续改动都隐含风险,所以一般建议现代项目直接用绝对/根相对 URL 弃用 base。但遗留系统深依赖 base 的,保持单条+合法绝对 href 即可。
**修复(fix)**: 优先移除 base、模板输出绝对 URL;必须保留时单条+合法绝对 href;上线检查清单加 base 计数断言。
**关联(seealso)**: i18n-hreflang-relative-url、core-canonical-present、htmlval-head-content;[head-elements.md](head-elements.md)

#### htmlval-html-size [待核 ID]
- 名称/类型: HTML 体积与占位文本 —— warning/issue · 优先级 medium · 输出 WARN(>250KB 与 lorem ipsum)/CRITICAL(>500KB)(源表:>250KB 警、>500KB 败、~2MB 以上 Googlebot 可能只索引前段;lorem ipsum=warn)
**这意味(what)**: 未压缩 HTML 超过 250KB(500KB 进败档,~2MB 以上 Googlebot 可能只索引前段),或页面含 lorem ipsum 占位文本。
**为什么(why)**: HTML 体积是解析与抓取预算的直接消耗:超大文档可能只处理前段,尾部内容与链接被截断;250/500KB 几乎总是内联数据 JSON/隐藏 DOM/注释未清的症状。lorem ipsum 则是模板没换真文案就上线的直接证据,对用户与引擎都是无意义内容(与 content-placeholder-text 的 {{ }} 占位符同族,此处并入陈述)。
**触发(trigger)**: 1) HTML 响应体 >250KB 即警;>500KB 即败;2) 文本命中 lorem/ipsum 词表即 warn。
**不修的条件(caveat)**: 体积阈值不是排名开关,然而它标记"尾部内容可能不被处理",所以一般建议压回 250KB 内并把关键内容与链接放前段。但合法的大文档(长表格/内联数据应用页)超线是形态属性,优先保证前段完整而非硬拆。
**修复(fix)**: 内联 JSON 改按需接口拉取;注释/调试属性剥离;长列表服务端分页;lorem 命中直接换真文案或下线页面。
**关联(seealso)**: perf-page-weight、perf-dom-size、content-deploy-hygiene;[cwv-playbook.md](cwv-playbook.md)

### AI/GEO Readiness(13 条,权重 2%)

**全部 13 条细则已吸收于 [validation-guide.md](validation-guide.md)「审计阈值补充」与 [ai-crawler-policy.md](ai-crawler-policy.md)**,此处仅存目:geo-semantic-html/geo-content-structure/geo-ai-bot-access(GPTBot/Claude-Web/Anthropic/Google-Extended 放行)/geo-llms-txt(info)/geo-schema-drift(schema 须与可见内容一致)/geo-content-signals(Content-Signal 语法+ai-train=yes 但训练 bot 全 Disallow=矛盾)/geo-noai-signals(恒 pass 不扣分)/geo-agents-md/geo-well-known(MCP/agent-card)/geo-rsl-license/geo-markdown-response(根路径出 Markdown)/geo-markdown-page(非根 URL 须有 .md 表示)/geo-pay-per-crawl(402 且无 Pay/Crawler-Price/X-Crawler-Price/payment Link 头才警)。

### Legal Compliance(1 条,权重 1%)

`legal-cookie-consent`:检测 CMP(CookieYes/OneTrust/Cookiebot/Termly/Quantcast);有 CMP 或无追踪脚本=pass,有追踪无 CMP=warn。

**解释层(1 条,第四批;ID 为源目录原文)**

#### legal-cookie-consent
- 名称/类型: 追踪脚本无 CMP —— warning · 优先级 medium · 输出 WARN(源表:有 CMP 或无追踪脚本=pass,有追踪无 CMP=warn)
**这意味(what)**: 页面加载了追踪脚本(GA/GTM/广告类)却没有检测到任何 CMP(consent management platform:CookieYes/OneTrust/Cookiebot/Termly/Quantcast)。
**为什么(why)**: 双重后果:合规面,欧盟 GDPR/ePrivacy 系要求追踪前取得同意,无 CMP 的追踪直接踩监管红线(罚款案例常态化);数据面,无同意框架时 Google 标签在 EEA 按未同意降级处理——consent mode 缺失(见 technical-tagging)连带信号缺失,SEO 决策依赖的流量数据也失真。判定按"追踪器脚本指纹+CMP 特征 DOM"双查,不读 Cookie 值。
**触发(trigger)**: 1) 页面脚本命中追踪器指纹(GA/GTM/Meta Pixel 等[清单口径待核]);2) DOM/脚本无已知 CMP 特征(CookieYes/OneTrust/Cookiebot/Termly/Quantcast);两者同时成立即 warn;无追踪脚本则 pass。
**不修的条件(caveat)**: 无 cookie 同意强制要求的辖区,无 CMP 不构成当地合规问题,然而境外流量接入后即暴露;纯必要 Cookie(会话/安全)无 CMP 是合法形态,不判。
**修复(fix)**: 部署 CMP 并接 consent mode(gtag consent default+update,见 technical-tagging);追踪器一律经 CMP 门控加载;隐私政策同步(见 eeat-privacy-tos)。
**关联(seealso)**: technical-tagging、eeat-privacy-tos;[gtm-implementation.md](gtm-implementation.md)、[validation-guide.md](validation-guide.md)

---

## 五、吸收备注(去重边界)

- CWV 五阈值/权重表/档位 → [LCP.md](LCP.md)、[scoring-rubric.md](scoring-rubric.md)。
- raw-vs-rendered 双抓实现 → [rendering-seo.md](rendering-seo.md)。
- AI/GEO 13 条 + 实体图六查 → [validation-guide.md](validation-guide.md)、[ai-crawler-policy.md](ai-crawler-policy.md)、[entity-signal-checklist.md](entity-signal-checklist.md)。
- 本文新增独有:Crawlability 38 条全目、E-E-A-T 16 条全目、i18n 13 条全目(含入向校验/x-default 洞察两维度)、Links 入链族 8 条、Content 跨页族、Mobile parity 五条、全类别数字阈值。

---

## 六、未覆盖规则(扩写边界与进度)

- 解释层本版覆盖 **220 条**:第一波 79 条 P0/P1(Crawlability 34/i18n 13/Core SEO 18/Links 4/Redirects 4/Content 重复族 4/Images alt 1/Social og:url 1,聚焦 canonical·noindex·重复内容·断链·重定向·sitemap·hreflang·title/H1 结构家族)+ 第二波 44 条 medium/low 高价值(Crawlability 分页 2/Links 6/Content 6/Images 5/Social 3/Performance 8/Structured Data 5/URL 5/JS Rendering 4)+ 第三批 47 条(Technical SEO 10:5xx·超时·空 HTML·soft-404·非 404 4xx·自定义 404·robots.txt·sitemap 存在性·Content-Type·URL 一致性·埋点卫生;Security 6:HTTPS/混合内容·安全头族·TLS/证书·Cookie·链接引用安全·内容危险信号;Mobile 6:字号·viewport 配置·横向滚动·插页·image maps·parity 五条;Links 6:无内链·外链可达·畸形 href 家族·断锚点·onclick·外链 nofollow;HTML Validation 5:文档结构·多 title/description·head 非法元素·base·体积与 lorem;Content 5:文本比·可读性·相对薄·标题模式·MIME 破损;Redirects 3:静态资源·大小写规范化·资源链;Core SEO 2:viewport/favicon;Crawlability 2:pdf-size/crawl-delay 收口 38 条全量;i18n 1:lang 一致性;Performance 1:preconnect)+ 第四批 50 条(E-E-A-T 14:byline·资历·日期/更新机制·引用·about·contact·隐私+ToS·地址+geo meta·联盟披露·免责·编辑政策·信任信号·YMYL 检测器·NAP,16 条全量;Accessibility 32:对比度·触控目标·可访问名·按钮名·名含可见文本·焦点·tabindex·skip 链·accesskey·表单 label·一控件一 label·autocomplete token·landmark·恰一 main·标题跳级·空标题·链接文本·同链同的·表格 th+scope·caption·字幕文稿·iframe title·SVG 名·alt 复读·ARIA 拼错·aria-hidden 聚焦·根级 aria-hidden·widget 父子角色·列表结构·role 反证·input image alt·重复 ID,34 条规则全量[alt 归 Images、语言码归 i18n、禁缩放归 mobile];Structured Data 3:实体引用·实体一致性·评分作用域,六查全量;Legal 1:cookie consent 收口 20 类全覆盖)。
- **其余约 150 条仍以表格/浓缩表形式维护,是唯一事实来源**:阈值以表格为准,条目与表格冲突时改条目不改表。AI/GEO 13 条(细则已吸收于 [validation-guide.md](validation-guide.md) 与 [ai-crawler-policy.md](ai-crawler-policy.md),仅存目)与各节表内剩余同构细分条(Performance minify 子项、Mobile parity 子项、Links 入链族切面等)的判定阈值都在第四节浓缩表与被吸收的专项文档(LCP.md/validation-guide.md/ai-crawler-policy.md 等)里。
- 后续扩写按同规范增量进行:第四批后 20 类主要规则均有解释层覆盖,剩余为 AI/GEO 13 条(细则在专项文档,存目即可)与各节同构细分条(逐条单列的扩写价值低);后续批次以源目录变动核对、[待核] 阈值复核与新增规则补录为主——每扩一批,更新本节数字。
- 新增条目必须照抄源表阈值并遵守〇节 ID 纪律与两轴哲学;来源变动的核对入口是 intel_check.py 的 google-updates 源(映射到本文)。


