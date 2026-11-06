# Ahrefs Site Audit 121 项与本套件脚本的逐项对照

> 2026-11-06,RQ-229 例 3。清单来自 2026-11-05 独立评分的 `ahrefs-121.csv`(EveryInfra 仓 `_handoff/中枢/调研/2026-11-05-SEO-skill评分/复评/`),121 项原样照用。
> 「覆盖」= 脚本实际跑出来会点名这一项(不是只在文档里写了)。每项的命中夹具和不该命中的对照夹具在 `tests/test_ahrefs_coverage.py`。

## 覆盖率

| 口径 | 修前 | 修后 |
|---|---|---|
| 评分报告原口径:121 项,覆盖记 1、半记 0.5 | 59.9%(覆盖 63、半 19、缺 39) | 97.5%(覆盖 118、不适用 3) |
| 去掉 3 项不适用,分母 118 | 61.0%(覆盖 63、半 18) | **100%**(118/118) |
| 同上,再把 4 项本套件自定阈值的项记成没覆盖 | — | 96.6%(114/118) |

本轮补上 55 项(原来是「缺」或「半」),另修 2 项原有覆盖的错报(空 description 报成「太短」、JSON 坏不计 CRITICAL)。按类别:

| 类别 | 本轮补 |
|---|---|
| Internal pages | 2 |
| Indexability | 10 |
| Links | 7 |
| Redirects | 4 |
| Content | 1 |
| Duplicates | 3 |
| Social tags | 3 |
| Localization | 4 |
| Images | 5 |
| JavaScript | 4 |
| CSS | 5 |
| Usability and performance | 3 |
| AI Discoverability | 2 |
| External pages | 1 |
| Other | 1 |

## 不适用(不计入分母)

| 项 | 理由 |
|---|---|
| Tap targets too small | 要真实浏览器排版算出点按区域大小;离线 HTML 算不出(Lighthouse/PSI 的活) |
| Font too small | 要真实浏览器算出计算后的字号(CSS 层叠、视口缩放);离线 HTML 算不出 |
| Similar AI-generated content | 要 Ahrefs 自家的 AI 内容判定模型;没有公开判法和可复现的离线替代 |

## 本套件自定阈值的项

Ahrefs 没公布判法或数字,下面 4 项按本套件口径判,报出来的结果不能当成「Ahrefs 会报」:

- Slow page:HTML 下载完 >3000ms(`--slow-ms` 可调)。
- HTML file size too large:解压后 >300KB。Ahrefs 只在 2021-09 更新里说「250-300KB or more」通常伴随性能问题。
- Too slow/heavy for AI crawlers:HTML 下载 >`--slow-ms` 或 >2MB。AI 爬虫只取 HTML、不跑 JS,所以不看 script 个数。
- Inconsistent AI bot policies:robots.txt 根路径上,同一家的搜索/按需 bot 有放有封(WARN),训练放行而搜索封(WARN),各家搜索 bot 之间不一致(INFO)。

另有 2 个数字来自二手转录:Image file size too large 的 100KB(AWT 应用内说明),X (Twitter) card incomplete 的判法。

## Ahrefs 清单之外的补项(2026-11-06,RQ-229 例 7 规模站)

规模站(sitemap 300 多条)上实跑发现的缺口,都在 site_crawl 的 `site_issues` 里,夹具在 `tests/test_crawl_gaps_20261106.py`。

| 输出键 | 报什么 | 判法 | 出处 |
|---|---|---|---|
| `soft_404` | 返回 2xx、非 noindex,但页面是「找不到页面」 | title 或 H1 的某一段整段就是报错语;或正文 <300 词且有「页面找不到 / 不存在」句 | [Google soft 404](https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors#soft-404-errors);[Screaming Frog Soft 404 Pages](https://www.screamingfrog.co.uk/seo-spider/issues/content/soft-404-pages/) |
| `canonical_points_to_noindex` | canonical 目标是 noindex(meta robots/googlebot 或 X-Robots-Tag) | 目标页已抓或补抓一次 | [Screaming Frog Non-Indexable Canonical](https://www.screamingfrog.co.uk/seo-spider/issues/canonicals/non-indexable-canonical/) |
| `links_to_4xx_page` | 被站内链接引用的 4xx URL(除 429),按目标列,带来源页 | 经重定向落到 4xx 也算 | [Google HTTP 状态码](https://developers.google.com/search/docs/crawling-indexing/http-network-errors):「All 4xx errors, except 429, are treated the same」 |

另:sitemap ≥50 条时 site_crawl 原来只抓 sitemap、站内链接只进图不请求,链到 404 的链接、被链接引用的重定向链、只从分页页链出的页都查不到。现在 sitemap 优先,站内链接指向、sitemap 没列的 URL 排在后面请求(同受 `--max`;`--sitemap-only` 恢复旧口径)。

## 用法

- 单页:`python3 scripts/site_audit.py URL`。
- 跨页:`python3 scripts/site_crawl.py 站点 --max N --out crawl.json [--check-resources] [--check-external] [--slow-ms 3000]`,看 crawl.json 的 `site_issues`(每个键是一项,`counts` 是全量数,列表最多 100 行)。`--max` 截断时 `site_issues.partial` 写明哪几项不判。
- 重定向:`python3 scripts/redirect_chain.py URL`。
- AI bot 策略:`python3 scripts/robots_posture.py 站点/robots.txt --json`,看 `inconsistent_ai_policies`。
- 结构化数据:`python3 scripts/schema_lint.py URL`。退出码 0 没有 CRITICAL 和富结果错误,1 有,2 用法错或抓不到,3 页面没有 JSON-LD。
- 「…receives organic traffic」五项和 Core Web Vitals、TTFB 要外部数据:分别是 `ops.py` 的 GSC 数据包和 `field_data.py` 的 CrUX(要 API key)。

## 逐项表

「11-05 实跑」是评分时的判定;「现在」是本轮之后。

| 类别 | Ahrefs 项 | 11-05 实跑 | 现在 | 脚本与输出键 | 定义出处 |
|---|---|---|---|---|---|
| Internal pages | 404 page | 覆盖 | 覆盖(原有) | scripts/site_crawl.py:846 状态记录;sitemap_audit 桶1;site_audit fetch-http | — |
| Internal pages | 4XX page | 覆盖 | 覆盖(原有) | scripts/site_crawl.py:846 | — |
| Internal pages | 403 Forbidden page | 覆盖 | 覆盖(原有) | scripts/site_crawl.py:846;site_audit 把 403 当挑战页 SKIP | — |
| Internal pages | 500 page | 覆盖 | 覆盖(原有) | scripts/site_crawl.py:846;site_audit fetch-http | — |
| Internal pages | 5XX page | 覆盖 | 覆盖(原有) | scripts/site_crawl.py:846 | — |
| Internal pages | Timed out | 覆盖 | 覆盖(原有) | scripts/site_crawl.py:841 error;sitemap_audit 桶1 TimeoutError | — |
| Internal pages | HTTPS/HTTP mixed content | 覆盖 | 覆盖(原有) | scripts/monitor.py:930(只查首页和关键页) | — |
| Internal pages | Double slash in URL | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`double_slash_in_url`;`AUDIT` `url-double-slash` | [help 2596665](https://help.ahrefs.com/en/articles/2596665) |
| Internal pages | Oversized HTML (>2MB) | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`oversized_html`;`AUDIT` `size-html-too-large` | [Googlebot 文档](https://developers.google.com/search/docs/crawling-indexing/googlebot)「first 2MB」 |
| Indexability | Noindex page | 覆盖 | 覆盖(原有) | scripts/site_audit.py:173 robots-noindex | — |
| Indexability | Nofollow page | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`nofollow_page`;`AUDIT` `robots-nofollow` | [help 2478724](https://help.ahrefs.com/en/articles/2478724) |
| Indexability | Noindex follow page | 覆盖 | 覆盖(原有) | scripts/site_audit.py:173(列入 noindex) | — |
| Indexability | Noindex and nofollow page | 覆盖 | 覆盖(原有) | scripts/site_audit.py:173(列入 noindex) | — |
| Indexability | Noindex in HTML and HTTP header | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`noindex_in_html_and_header`;`AUDIT` `robots-noindex-html-and-header` | [help 2465780](https://help.ahrefs.com/en/articles/2465780)(nofollow 同篇同理) |
| Indexability | Nofollow in HTML and HTTP header | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`nofollow_in_html_and_header`;`AUDIT` `robots-nofollow-html-and-header` | [help 2465780](https://help.ahrefs.com/en/articles/2465780) |
| Indexability | Canonical points to 4XX | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`canonical_points_to_4xx`(canonical 目标没抓到时补抓) | [help 2427853](https://help.ahrefs.com/en/articles/2427853) |
| Indexability | Canonical points to 5XX | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`canonical_points_to_5xx` | [help 2491113](https://help.ahrefs.com/en/articles/2491113) |
| Indexability | Canonical points to redirect | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`canonical_points_to_redirect` | [help 2753767](https://help.ahrefs.com/en/articles/2753767) |
| Indexability | Canonical from HTTP to HTTPS | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`canonical_from_http_to_https`;`AUDIT` `canonical-http-to-https` | [help 2478867](https://help.ahrefs.com/en/articles/2478867) |
| Indexability | Canonical from HTTPS to HTTP | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`canonical_from_https_to_http`;`AUDIT` `canonical-https-to-http` | [help 2434581](https://help.ahrefs.com/en/articles/2434581) |
| Indexability | Non-canonical page specified as canonical | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`non_canonical_page_specified_as_canonical` | [help 2526305](https://help.ahrefs.com/en/articles/2526305) |
| Indexability | Duplicate pages without canonical | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`duplicate_pages_without_canonical`(noindex 页不算) | [help 2596742](https://help.ahrefs.com/en/articles/2596742);[Ahrefs 2021-09 更新](https://ahrefs.com/blog/site-audit-issues-update-september-2021/) |
| Indexability | Noindex page receives organic traffic | 覆盖 | 覆盖(原有) | scripts/ops.py:672 five_lists(要外部数据包 gsc_pages) | — |
| Indexability | 4xx page receives organic traffic | 覆盖 | 覆盖(原有) | scripts/ops.py:672 | — |
| Indexability | 403 page receives organic traffic | 覆盖 | 覆盖(原有) | scripts/ops.py:672 | — |
| Indexability | 3xx page receives organic traffic | 覆盖 | 覆盖(原有) | scripts/ops.py:672 | — |
| Indexability | Non-canonical page receives organic traffic | 覆盖 | 覆盖(原有) | scripts/ops.py:672 | — |
| Links | Orphan page | 覆盖 | 覆盖(原有) | scripts/site_crawl.py orphans;`link_graph.py` 零入链清单(11-06 起内链边完整时默认计入 sitemap 里 0 入链的页) | — |
| Links | Canonical URL has no incoming internal links | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`canonical_url_no_incoming_internal_links`(--max 截断时不判) | [help 2595174](https://help.ahrefs.com/en/articles/2595174);[Ahrefs 2021-09 更新](https://ahrefs.com/blog/site-audit-issues-update-september-2021/) |
| Links | Redirected page has no incoming internal links | 覆盖 | 覆盖(原有) | scripts/site_crawl.py:941 link_issues | — |
| Links | Page has nofollow incoming internal links only | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`nofollow_incoming_internal_links_only` | [help 2746992](https://help.ahrefs.com/en/articles/2746992) |
| Links | Page has nofollow and dofollow incoming internal links | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`nofollow_and_dofollow_incoming_internal_links` | [help 2734983](https://help.ahrefs.com/en/articles/2734983) |
| Links | Page has only one dofollow incoming internal link | 覆盖 | 覆盖(原有) | scripts/link_graph.py 单入链清单 | — |
| Links | Page has no outgoing links | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`no_outgoing_links` | [help 2734700](https://help.ahrefs.com/en/articles/2734700) |
| Links | Page has links to redirect | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`links_to_redirect`(外链部分 `external_links_to_redirect`) | [help 2724308](https://help.ahrefs.com/en/articles/2724308) |
| Links | Page has links to broken page | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`links_to_broken_page`(只算 404/410) | [help 2721106](https://help.ahrefs.com/en/articles/2721106);[Ahrefs 2021-09 更新](https://ahrefs.com/blog/site-audit-issues-update-september-2021/) |
| Links | HTTPS page has internal links to HTTP | 覆盖 | 覆盖(原有) | scripts/site_crawl.py:977 | — |
| Links | HTTP page has internal links to HTTPS | 覆盖 | 覆盖(原有) | scripts/site_crawl.py:975 | — |
| Links | Page has nofollow outgoing internal links | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`nofollow_outgoing_internal_links` | Ahrefs 问题清单(转录) |
| Redirects | 3XX redirect | 覆盖 | 覆盖(原有) | site_crawl 重定向计数;sitemap_audit 桶2;redirect_chain | — |
| Redirects | 302 redirect | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`redirect_302`;`REDIR` 302 跳 INFO | [help 2427783](https://help.ahrefs.com/en/articles/2427783) |
| Redirects | Broken redirect | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`broken_redirect`;`REDIR` 终点 4xx/5xx CRITICAL | [help 2456799](https://help.ahrefs.com/en/articles/2456799) |
| Redirects | Redirect loop | 覆盖 | 覆盖(原有) | scripts/redirect_chain.py:146 | — |
| Redirects | Redirect chain | 覆盖 | 覆盖(原有) | scripts/redirect_chain.py:11(单个 URL);`CRAWL` site_issues.`redirect_chain`(全站发现,带起点、逐跳和来源页,11-06 补) | [Ahrefs 2021-09 更新](https://ahrefs.com/blog/site-audit-issues-update-september-2021/) |
| Redirects | Redirect chain too long | 覆盖 | 覆盖(原有) | scripts/redirect_chain.py:128;`CRAWL` site_issues.`redirect_chain_too_long`(链上 URL >5) | 同上 |
| Redirects | Meta refresh redirect | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`meta_refresh_redirect`;`AUDIT` `redirect-meta-refresh`;`REDIR` 终点页 WARN | [help 2433739](https://help.ahrefs.com/en/articles/2433739) |
| Redirects | HTTPS to HTTP redirect | 覆盖 | 覆盖(原有) | scripts/site_crawl.py:984;redirect_chain WARN | — |
| Redirects | HTTP to HTTPS redirect | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`http_to_https_redirect`;`REDIR` INFO | Ahrefs 导出项 |
| Content | Title missing or empty | 覆盖 | 覆盖(原有) | site_audit title-missing | — |
| Content | Title too long | 覆盖 | 覆盖(原有) | site_audit title-too-long | — |
| Content | Title too short | 覆盖 | 覆盖(原有) | site_audit title-too-short | — |
| Content | Multiple title tags | 覆盖 | 覆盖(本轮修) | `CRAWL` site_issues.`multiple_title_tags`;`AUDIT` `title-multiple`(svg 里的 title 不算) | [help 2754360](https://help.ahrefs.com/en/articles/2754360) |
| Content | Meta description missing or empty | 覆盖 | 覆盖(本轮修) | `AUDIT` `description-missing`(空 content 现在报「缺失(content 为空)」,不再报太短) | — |
| Content | Meta description too long | 覆盖 | 覆盖(原有) | site_audit description-too-long | — |
| Content | Meta description too short | 覆盖 | 覆盖(原有) | site_audit description-too-short | — |
| Content | Multiple meta description tags | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`multiple_meta_description_tags`;`AUDIT` `description-multiple` | [help 2652405](https://help.ahrefs.com/en/articles/2652405) |
| Content | H1 missing or empty | 覆盖 | 覆盖(原有) | site_audit h1-missing | — |
| Content | Multiple H1 tags | 覆盖 | 覆盖(原有) | site_audit h1-multiple | — |
| Content | Low word count | 覆盖 | 覆盖(原有) | site_audit content-thin | — |
| Content | Page and SERP titles do not match | 覆盖 | 覆盖(原有) | site_audit --serp-titles title-serp-mismatch | — |
| Duplicates | Duplicate title tag | 覆盖 | 覆盖(原有) | `CRAWL` site_issues.`duplicate_title`(按组列 URL);health_score `duplicate_title_groups`(11-06 起列出撞在一起的页) | — |
| Duplicates | Duplicate meta description | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`duplicate_meta_description`(只算可索引页) | Ahrefs 问题清单 |
| Duplicates | Duplicate H1 | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`duplicate_h1`(只算可索引页) | Ahrefs 问题清单 |
| Duplicates | Duplicate content (bad duplicates) | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`duplicate_content_bad`(全文哈希 + 5 词 shingle 近似 Jaccard ≥0.9;canonical 同指一页或互为 hreflang 的算好重复) | [help 2115215](https://help.ahrefs.com/en/articles/2115215) |
| Social tags | Open Graph tags missing | 覆盖 | 覆盖(原有) | site_audit og-*-missing | — |
| Social tags | Open Graph tags incomplete | 覆盖 | 覆盖(原有) | site_audit og-*-missing | — |
| Social tags | Open Graph URL not matching canonical | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`og_url_not_matching_canonical`;`AUDIT` `og-url-canonical-mismatch` | [Ahrefs canonical 文第 10 条](https://ahrefs.com/blog/canonical-tags/) |
| Social tags | X (Twitter) card missing | 缺 | 覆盖(本轮补) | `AUDIT` `twitter-card-missing` | [X Cards 文档](https://developer.x.com/en/docs/x-for-websites/cards/overview/markup) |
| Social tags | X (Twitter) card incomplete | 缺 | 覆盖(本轮补) | `AUDIT` `twitter-card-incomplete`(缺 card/title/description/image 任一) | 同上;Patrick Stox(前 Ahrefs)「partial twitter:* metadata」,二手 |
| Localization | Self-referencing hreflang missing | 覆盖 | 覆盖(原有) | sitemap_audit --hreflang、hreflang_cluster | — |
| Localization | Missing reciprocal hreflang | 覆盖 | 覆盖(原有) | 同上 | — |
| Localization | Hreflang to broken page | 覆盖 | 覆盖(原有) | scripts/hreflang_cluster.py(alternate 不可达) | — |
| Localization | Hreflang to non-canonical | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`hreflang_to_non_canonical` | [help 2608450](https://help.ahrefs.com/en/articles/2608450) |
| Localization | Hreflang annotation invalid | 覆盖 | 覆盖(原有) | 语言码非法 | — |
| Localization | HTML lang attribute invalid | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`html_lang_invalid`;`AUDIT` `lang-invalid` | [help 2601025](https://help.ahrefs.com/en/articles/2601025) |
| Localization | Hreflang and HTML lang mismatch | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`hreflang_and_html_lang_mismatch`;`AUDIT` `hreflang-lang-mismatch` | [help 2598523](https://help.ahrefs.com/en/articles/2598523);非 canonical 页上的 hreflang 不看([Ahrefs 2021-09 更新](https://ahrefs.com/blog/site-audit-issues-update-september-2021/)) |
| Localization | More than one page for same language | 覆盖 | 覆盖(原有) | scripts/sitemap_audit.py:37 同码多址 | — |
| Localization | Page referenced for more than one language | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`page_referenced_for_more_than_one_language`;`AUDIT` `hreflang-multi-language` | [help 2747339](https://help.ahrefs.com/en/articles/2747339)(同语言不同地区不算) |
| Images | Image broken | 缺 | 覆盖(本轮补) | `CRAWL --check-resources` `image_broken` | [help 2628254](https://help.ahrefs.com/en/articles/2628254) |
| Images | Page has broken image | 缺 | 覆盖(本轮补) | `CRAWL --check-resources` `page_has_broken_image` | [help 2699397](https://help.ahrefs.com/en/articles/2699397) |
| Images | Missing alt text | 覆盖 | 覆盖(原有) | site_audit images-alt-missing | — |
| Images | Image file size too large | 缺 | 覆盖(本轮补) | `CRAWL --check-resources` `image_file_size_too_large`(>100KB) | AWT 应用内说明「superior a 100 KB」([sergiocanales 转录](https://sergiocanales.com/ahrefs-webmaster-tools/),二手) |
| Images | Image redirects / redirected image | 缺 | 覆盖(本轮补) | `CRAWL --check-resources` `image_redirects` | Ahrefs 问题清单 |
| Images | HTTPS page links to HTTP image | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`https_page_links_to_http_image`(全站,不用加 flag) | Ahrefs 问题清单 |
| JavaScript | JavaScript broken | 缺 | 覆盖(本轮补) | `CRAWL --check-resources` `javascript_broken` | [help 2750495](https://help.ahrefs.com/en/articles/2750495) |
| JavaScript | Page has broken JavaScript | 缺 | 覆盖(本轮补) | `CRAWL --check-resources` `page_has_broken_javascript` | [help 2720786](https://help.ahrefs.com/en/articles/2720786) |
| JavaScript | JavaScript redirects | 缺 | 覆盖(本轮补) | `CRAWL --check-resources` `javascript_redirects` | Ahrefs 问题清单 |
| JavaScript | HTTPS page links to HTTP JavaScript | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`https_page_links_to_http_javascript` | Ahrefs 问题清单 |
| CSS | CSS broken | 缺 | 覆盖(本轮补) | `CRAWL --check-resources` `css_broken` | [help 2759921](https://help.ahrefs.com/en/articles/2759921) |
| CSS | Page has broken CSS | 缺 | 覆盖(本轮补) | `CRAWL --check-resources` `page_has_broken_css` | 同上 |
| CSS | CSS file size too large | 缺 | 覆盖(本轮补) | `CRAWL --check-resources` `css_file_size_too_large`(>15KB) | [help 2760432](https://help.ahrefs.com/en/articles/2760432)「larger than 15 kB」 |
| CSS | CSS redirects | 缺 | 覆盖(本轮补) | `CRAWL --check-resources` `css_redirects` | Ahrefs 问题清单 |
| CSS | HTTPS page links to HTTP CSS | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`https_page_links_to_http_css` | Ahrefs 问题清单 |
| Sitemaps | Noindex page in sitemap | 覆盖 | 覆盖(原有) | sitemap_audit 桶3 | — |
| Sitemaps | Non-canonical page in sitemap | 覆盖 | 覆盖(原有) | sitemap_audit 桶4 | — |
| Sitemaps | 3xx redirect in sitemap | 覆盖 | 覆盖(原有) | sitemap_audit 桶2 | — |
| Sitemaps | 4xx page in sitemap | 覆盖 | 覆盖(原有) | sitemap_audit 桶1 | — |
| Sitemaps | 403 page in sitemap | 覆盖 | 覆盖(原有) | sitemap_audit 桶1 | — |
| Sitemaps | 5xx page in sitemap | 覆盖 | 覆盖(原有) | sitemap_audit 桶1 | — |
| Sitemaps | Page from sitemap timed out | 覆盖 | 覆盖(原有) | sitemap_audit 桶1 | — |
| Sitemaps | Format of sitemaps invalid | 覆盖 | 覆盖(原有) | scripts/sitemap_audit.py:245 | — |
| Usability and performance | Slow page | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`slow_page`(HTML 下载完 >3000ms,`--slow-ms` 可调) | Ahrefs 未公布阈值,[help 2570529](https://help.ahrefs.com/en/articles/2570529) 只讲测法;3000ms 是本套件口径 |
| Usability and performance | Time to first byte | 覆盖 | 覆盖(原有) | scripts/field_data.py:32(CrUX,要 API key) | — |
| Usability and performance | Not compressed | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`not_compressed`;`AUDIT` `compression-none`(只在请求真带了 Accept-Encoding 时判) | Ahrefs 问题清单 |
| Usability and performance | HTML file size too large | 缺 | 覆盖(本轮补) | `CRAWL` site_issues.`html_file_size_too_large`(解压后 >300KB) | Ahrefs 未给阈值;[Ahrefs 2021-09 更新](https://ahrefs.com/blog/site-audit-issues-update-september-2021/)「250-300KB or more」,取 300KB |
| Usability and performance | Poor LCP | 覆盖 | 覆盖(原有) | field_data(CrUX) | — |
| Usability and performance | Poor CLS | 覆盖 | 覆盖(原有) | field_data(CrUX) | — |
| Usability and performance | Poor INP/FID | 覆盖 | 覆盖(原有) | field_data(CrUX) | — |
| Usability and performance | Viewport not set | 覆盖 | 覆盖(原有) | scripts/head_check.py:275 | — |
| Usability and performance | Tap targets too small | 缺 | 不适用 | 要真实浏览器排版算出点按区域大小;离线 HTML 算不出(Lighthouse/PSI 的活) | — |
| Usability and performance | Font too small | 缺 | 不适用 | 要真实浏览器算出计算后的字号(CSS 层叠、视口缩放);离线 HTML 算不出 | — |
| Usability and performance | Document uses plugins | 覆盖 | 覆盖(原有) | site_audit rendering-plugins | — |
| AI Discoverability | Blocked from AI bots in robots.txt | 覆盖 | 覆盖(原有) | site_audit ai-bots-blocked;robots_posture | — |
| AI Discoverability | Too slow/heavy for AI crawlers | 半 | 覆盖(本轮补) | `CRAWL` site_issues.`too_slow_or_heavy_for_ai_crawlers`(HTML 下载 >--slow-ms 或 >2MB) | [Ahrefs 2026-09 新功能](https://ahrefs.com/blog/new-features-september-2026/)只公布名称;判法是本套件口径(AI 爬虫不跑 JS,不看 script 数) |
| AI Discoverability | Inconsistent AI bot policies | 半 | 覆盖(本轮补) | `ROBOTS` `inconsistent_ai_policies`(同厂商答案 bot 放封不一 WARN;训练放行而搜索封 WARN;各家搜索 bot 不一致 INFO) | 同上,只公布名称;判法本套件口径 |
| AI Discoverability | Similar AI-generated content | 半 | 不适用 | 要 Ahrefs 自家的 AI 内容判定模型;没有公开判法和可复现的离线替代 | — |
| AI Discoverability | Requires JavaScript rendering | 覆盖 | 覆盖(原有) | site_audit rendering-csr | — |
| External pages | External 4XX | 缺 | 覆盖(本轮补) | `CRAWL --check-external` `external_links_to_broken` | Ahrefs 问题清单 |
| External pages | External 3XX redirect | 覆盖 | 覆盖(原有) | scripts/site_crawl.py:994 | — |
| Other | Structured data schema.org validation error | 覆盖 | 覆盖(本轮修) | `schema_lint`(JSON 坏现在计入 CRITICAL、退出码 1;评分越界另报) | — |
| Other | Structured data Google rich results validation error | 缺 | 覆盖(本轮补) | `schema_lint` 富结果必填(Product/Offer/Review/AggregateRating/BreadcrumbList/Event/JobPosting/Recipe/LocalBusiness/VideoObject/SoftwareApplication/Dataset)+ 评分越界 | [help 8223239](https://help.ahrefs.com/en/articles/8223239);Google 各类型文档「Required properties」 |
