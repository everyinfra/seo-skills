# 审计规则全目录(SEOmator 373 规则,源码深读)

> 来源:seo-skills/seo-audit-skill v5.1.0 `docs/SEO-AUDIT-RULES.md` 全文(2026-10-09 深 clone 吸收)。
> 三态计分:Pass=100 / Warn=50 / Fail=0;总分=类别加权平均,**档位 90=A / 70=B / 50=C / <50=D-F**。
> **20 类权重表已吸收于 [scoring-rubric.md](scoring-rubric.md)「完全装载」节,不重抄**(Core 11%/Perf 10%/Links·Images·Security 各 8%/Tech·A11y 各 7%/Crawl·SD·Content·JS 各 5%/Social·E-E-A-T·URL·Redirects 各 3%/Mobile·i18n·HTMLval·AI-GEO 各 2%/Legal 1%)。
> 三类横切机制先记住,后面表格反复引用:
> - **crawl 模式专属**(`--crawl`):依赖多页爬取的跨页状态;单页审计时报 not measured(权重 0 不计分)。涉及 15 条 crawl-\* + 部分 links-inbound-\*/content-duplicate-\*/i18n 入向规则。
> - **渲染专属**(`--no-cwv` 时跳过):带"requires render"标记的 per-asset 规则,数据来自 Playwright 渲染。
> - **TOML 开关**:`[rules] disable=["core-*"]` 按前缀禁类;`enable=["core-*","perf-*"]+disable=["*"]` 只留指定类。

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

---

## 四、其余 17 类规则目录(浓缩表,保留全部数字阈值)

### Core SEO(24 条,权重 11%)

title 缺失=fail、长度 **30-60 字符**=warn;description 缺失=fail、**120-160 字符**=warn;canonical 缺失=fail、非绝对/不可达(须 200)=warn;viewport 缺失=fail;favicon 缺失=warn;H1 缺失=fail、多于 1 个=warn;`core-canonical-header`(HTML canonical 与 HTTP Link 头不一致=warn,Link 头应留给 PDF);`core-nosnippet`(nosnippet/max-snippet:0=warn);`core-robots-meta`(noindex/nofollow/noarchive/noimageindex/none=warn);`core-title-unique`(跨页重复 title,crawl,warn/fail);**canonical 家族 8 条**:conflicting(多信号不一致=fail)/to-homepage(深页指向首页=warn)/http-mismatch(协议不一致=warn)/loop(环=fail)/to-noindex(指向 noindex=fail)/outside-head(在 body 里=fail,引擎直接忽略)/attributes(带 hreflang/lang/media/type 属性改变语义=fail,其他多余属性=warn)/multiple(多条且不一致=fail,一致=warn);`core-robots-directive-mismatch`(meta 与 X-Robots-Tag 一方 index 一方 noindex=fail,多处声明 noindex=warn);`core-canonical-external`(指向外域=info,联合发布合法但让渡排名信号)。

### Performance(28 条,权重 10%)

**CWV 五指标阈值已吸收于 [LCP.md](LCP.md) 与 [scoring-rubric.md](scoring-rubric.md)**:LCP ≤2.5s/2.5-4/>4;CLS ≤0.1/0.1-0.25/>0.25;INP ≤200ms/200-500/>500;TTFB ≤800ms/800-1800/>1800;FCP ≤1.8s/1.8-3/>3。表内补静态项:DOM **<800 过/800-1500 警/>1500 败,深度>32 警**;`perf-asset-cache-policy`(静态资源 max-age ≥1 小时,渲染专属);`perf-asset-compression`(**>2KB** 文本资源须 gzip/Brotli,按 content-length,chunked 无长度不判);`perf-image-encoding`(图片传输 **>100KB=warn**,BMP/TIFF=fail);`perf-page-weight`(**<3MB** 建议);`perf-cache-policy`(带内容 hash 的静态资源 `max-age=31536000`);`perf-minify-css/js`(内联查空白比/块注释;外链 **>2KB** 且 URL 无 `.min.` 标记=启发式嫌疑,恒 ≤warn);`perf-response-time`、`perf-http2`(须 HTTP/2+)、`perf-render-blocking`(head 内脚本无 async/defer)、`perf-lazy-above-fold`(首屏图禁 lazy)、`perf-lcp-hints`(LCP 图须 preload+fetchpriority=high)、`perf-font-loading`(font-display:swap)、`perf-preconnect`、`perf-text-compression`、`perf-brotli`、`perf-video-for-animations`(GIF→video 省 90%)、`perf-legacy-javascript`、`perf-duplicate-js`(同库多 URL)、`perf-source-maps`(不得暴露 sourceMappingURL)。

### Links(27 条,权重 8%)

内链 4xx=fail;外链可达性=warn(结果缓存);无内链=warn;nofollow 滥用=warn;泛化锚文本("click here"/"read more"/"link")=warn;`links-depth`(**点击距离 ≤3**,crawl);死端页(无出链)=warn;HTTPS 页链 HTTP=warn;**外链 >100=warn**;空/javascript:/畸形 href=warn;tel:/mailto: 格式=warn;重定向链(**1-2 跳=warn,≥3=fail**);`links-localhost`(127.0.0.1=fail)/`links-local-file`(file://=fail);断锚点(#id 无匹配)=warn;`links-onclick`(onclick 导航替代 href=warn);href 首尾空白=warn;非 HTTP 协议(ftp:/intent:/chrome:)=warn;**crawl 专属入链族 8 条**:inbound-all-nofollow(全 nofollow=零权重流入,洞见级)/inbound-mixed-follow(有follow有nofollow=不一致)/inbound-low-quality(入链全 nofollow 或全来自被 canonical 走的页)/inbound-anchor-text(全部入链锚文本<2 字符或泛化)/nofollow-internal(同主机链接禁 nofollow)/weak-inbound(**非入口页须 >1 条 dofollow 入链**)/chrome-inbound(**至少 1 条入链在 nav/header/footer 之外**——正文链才算票)/orphan-pages(真孤儿由 crawl-sitemap-orphan-urls 配合判)。

### Images(14 条,权重 8%)

alt 缺失=fail;alt 泛化("image"/文件名)=warn;alt 长度 **5-125 字符**=warn;宽高属性缺失=warn(防 CLS);below-fold 须 `loading="lazy"`=warn;现代格式(WebP/AVIF 比 JPEG/PNG 小 30-50%)=warn;体积=warn;srcset 响应式=warn;图片 404=fail;figure 缺 figcaption=warn;文件名(IMG_001.jpg 坏/red-running-shoes.jpg 好)=warn;**内联 SVG >5KB 应外链**=warn;picture 缺 img 回退=fail;内容图用 CSS background(引擎读不到)=warn。

### Security(26 条,权重 8%)

非 HTTPS=fail;HTTP 不 301 到 HTTPS=warn;缺 HSTS(`max-age=31536000; includeSubDomains`)/CSP/X-Frame-Options(DENY/SAMEORIGIN)/nosniff/Permissions-Policy/Referrer-Policy(strict-origin-when-cross-origin)/COOP(`same-origin`,防 tabnabbing)=各 warn;`target=_blank` 缺 noopener/noreferrer=warn;表单 action 非 HTTPS=warn/fail;混合内容=warn/fail;`security-csp-xss`(CSP 是否真约束脚本:'unsafe-inline' 无 nonce=不设防;无 CSP 时按权重 0 报,避免与 security-csp 双重扣)/`security-info-disclosure`(Server 带版本号/X-Powered-By=warn,裸 `Server: nginx` 过)/`security-paste-blocking`(onpaste 阻止粘贴=fail,毁密码管理器)/`security-trusted-types`(仅已设 CSP 的站评,`require-trusted-types-for 'script'`)/`security-leaked-secrets`(AWS key/API token/私钥/数据库 URL=fail)/`security-password-http`(HTTP 页密码框=fail)/协议相对 URL `//`=warn;Cookie 三旗(Secure/HttpOnly/SameSite)=warn/fail;**Cookie 寿命 >400 天上限=warn**;SSL 到期=warn/fail;**TLS 须 1.2+**(1.0/1.1=warn/fail);SRI(跨域脚本/stylesheet 须 integrity hash)=warn;混淆脚本(长高熵内联脚本调 eval/Function/atob)=warn;品牌登录链指向品牌或本域=warn。

### Technical SEO(18 条,权重 7%)

robots.txt 存在/语法=warn;sitemap 存在/格式=warn;URL 结构(小写+连字符)=warn;尾斜杠一致性=warn;www 一致性 301=warn;自定义 404=warn;soft-404(200 但错误内容)=warn;5xx=fail;**非 404 的 4xx(403/410 等)=warn**;超时=fail;Content-Type 错=warn/fail;**200 空 HTML(fhead/body 皆空)=fail**;`technical-form-get-method`(GET 表单产生可抓取查询串 URL=warn);**多 GTM 容器/多 GA 属性(>1 个不同 ID)=warn**;`technical-consent-mode`(Google 标签须配 consent update)=warn。

### Structured Data(19 条,权重 5%)

缺 JSON-LD=warn;JSON 语法坏=fail;缺 @type=warn;类型必填字段=warn;Article 须 headline/author/datePublished/image;BreadcrumbList(非首页,**≥2 个 itemListElement**)=info;FAQPage 每个 Question 须 name+acceptedAnswer.text=fail;LocalBusiness 须 name/address/telephone/geo;Organization 须 name/logo/sameAs;Product 须 offers(price/priceCurrency/availability)=fail;Review 须 itemReviewed/author/reviewRating;VideoObject 须 name/thumbnailUrl/uploadDate(时长 ISO 8601 如 PT1M30S);WebSite SearchAction 含 `{search_term_string}`=info。**实体图六查已吸收于 [entity-signal-checklist.md](entity-signal-checklist.md) 与 [validation-guide.md](validation-guide.md)**:entity-id(@id 绝对)/rating-scope(AggregateRating 不在 legal/account URL 且 ratingValue 可见)/entity-conflict(一 @id 两 logo/两电话)/entity-dangling(publisher/author/isPartOf 的 @id 须在爬取中声明)/entity-type-drift(同 @id 跨页同 @type)/entity-split(同名组织不挂两 @id)。

### Content(27 条,权重 5%)

词数 **≥300 过/100-299 警/<100 败**(文章建议 500+,长文 1000+);Flesch-Kincaid **60-70** 最优;关键词堆砌=warn/fail;标题层级不跳(H1→H3=invalid);**标题 <3 字符或 >100 字符=警**;页内标题重复=warn;text/HTML 比=warn;title 与 H1 相同=warn;**title 像素宽 ≤~580px、description ≤~920px**(SERP 截断);title=description 全同=warn;meta 在 body 里=fail;MIME=warn/fail;**crawl 专属**:duplicate-description/duplicate-exact(=fail)/duplicate-near/duplicate-h1(跨页同 H1)/thin-vs-site(**<同类页中位词数一半=警**,需 ≥4 个同类页)/title-pattern(标题未带全站 ≥60% 使用的后缀=警);`content-mojibake`(UTF-8 被按 Latin-1/Windows-1252 解码,如 `â€™`=fail);`content-unrendered-markup`(code/pre 外的字面 Markdown `**bold**`=warn);`content-placeholder-text`(**`{{ }}`/`{% %}`/`<% %>`/`[object Object]`=fail;TODO:/FIXME:=warn**;`content-stale-copyright`(页脚版权年落后当年=warn,区间取末年);`content-date-agreement`(datePublished/time datetime//20xx/ 路径三年份不一致=warn,dateModified 不比);`content-hidden-text`(**≥80 字符**被内联样式隐藏(display:none/visibility:hidden/font-size:0/大负 text-indent/opacity:0)=warn,nav/对话框/sr-only 豁免,仅样式表隐藏不判);`content-broken-html`/`content-meta-in-body`。

### JavaScript Rendering(16 条,权重 5%)

**raw-vs-rendered 实现要点已吸收于 [rendering-seo.md](rendering-seo.md) 与 [validation-guide.md](validation-guide.md)**(HTTP 抓原始→$;Playwright 二抓→rendered$;web-vitals 库 goto 前注入;INP 合成标记 inpSynthetic 不计分)。规则粒度:title/description/H1/canonical 不在初始 HTML=fail/warn/warn/fail;canonical 或 noindex 在源码与渲染 DOM 间不一致=fail;JS 事后改写 title/description/H1=warn;主内容/内链依赖 JS=warn;JS/CSS 被 robots 挡=warn;SSR 检查=warn/fail;**console 未捕获异常与错误=warn/fail**;**子资源加载失败=warn/fail**;内联脚本用 `document.write()`=warn。

### Accessibility(36 条,权重 7%)

对比度 **≥4.5:1 正文/3:1 大字**;触控目标 **≥44×44 CSS px**(WCAG 2.5.8);交互元素须可访问名(aria-label/文本/title);focus 样式可见;表单 label(placeholder 不算);标题不跳级;landmark(main/nav/header/footer);描述性链接文本;skip-to-content 链接;表格 th+scope;视频字幕/文稿;viewport 禁缩放(user-scalable=no/maximum-scale=1)=fail;aria-hidden 包可聚焦元素=fail;**ARIA 角色/属性拼错浏览器静默丢弃(aria-lable→aria-label)=fail**;accesskey 唯一;**ID 重复致 aria-labelledby/label for 解析到第一个匹配=fail(svg 内 url(#id) 引用的 clipPath 豁免)**;空标题=fail;一控件一 label;同文本链接须同目的地;iframe/object 须 title/替代文本;`<input type=image>` 须 alt;**可访问名须含可见文本(语音用户"说所见")**;按钮有名;email/tel 输入配对 autocomplete token;lang 与 xml:lang 一致;html/body 禁 aria-hidden;ARIA widget 须有所需父子角色(tab 在 tablist 内/option 在 listbox 内);列表只含 li;**恰一个 main landmark**;role=none/presentation 不被 ARIA/可聚焦性反证;alt 不重复相邻链接/图注文本;img 角色 SVG 须可访问名;表格用 caption 不用跨列首行;**tabindex 禁正值**;元素级 lang 合法 BCP 47。

### Social(9 条,权重 3%)

og:title/description/image 各=warn;**og:image 推荐 1200×630(配 og:image:width/height meta)**;og:url=warn;**og:url 与 canonical 不一致=fail**;twitter:card(summary_large_image)=warn;分享按钮(**≥2 平台**)=warn;社交资料链接(**≥3 个**,入 Organization sameAs)=warn。

### URL Structure(14 条,权重 3%)

slug 含描述关键词(数字 ID/?p=123 坏)=fail/warn;URL 停用词=warn;大写=warn;下划线=warn(连字符才是词分隔);双斜杠=warn;**%20 编码空格=fail**;非 ASCII=warn;**路径 ≤75 字符**=warn;重复路径段(/shoes/shoes/)=warn;**查询参数 3-5 个=warn、>5=fail**,同名参数重复或多个 `?`=畸形=warn;**URL 会话 ID=fail**;UTM/追踪参数=warn;站内搜索 URL 被索引=warn;HTTP/HTTPS 双可达=warn。

### Redirects(11 条,权重 3%)

meta refresh=warn;JS 重定向=warn;HTTP Refresh 头=warn;环=fail;301(永久/传权重)vs 302(临时)用错=warn;目标 4xx/5xx=fail;**静态资源被重定向=warn**;大小写规范化重定向=warn;**渲染专属三条**:resource-broken(资源重定向终点 4xx/5xx=fail)/resource-loop(资源重定向环,浏览器 ERR_TOO_MANY_REDIRECTS=fail)/**resource-chain(资源 ≥2 跳=warn,单跳 http→https/尾斜杠视为良性)**。

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
