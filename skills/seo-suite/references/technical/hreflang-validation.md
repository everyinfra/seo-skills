# hreflang / 国际化校验（八检框架）

> 2026-10-18 按 Google [本地化版本文档](https://developers.google.com/search/docs/specialty/international/localized-versions)（2026-09-21 更新）和 Yandex [本地化页面文档](https://yandex.com/support/webmaster/en/yandex-indexing/locale-pages) 逐条核对。框架思路参考 [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo)（MIT）`skills/seo-hreflang/SKILL.md`。适用：多语言 / 多区域站。

## 一、八项校验

| # | 检查 | 规则（Google 原文口径） | 违例严重度（本套件口径） |
|---|---|---|---|
| 1 | 自引用 | 每个语言版必须列出自己**和**所有其他语言版；每个版本上的整组链接相同 | High |
| 2 | 双向返回 | A 指向 B，B 也要指回 A。两页没有互相指向时，这一对标注被忽略。只影响没互指的那一对，其余互指的照常处理 | Critical（对该对） |
| 3 | x-default | 推荐，不强制；为语言选择页设计，也可用于任何页。回退页本身的语言无关紧要。每组只写一个（本套件口径，官方未写数量） | High |
| 4 | 语言码 | ISO 639-1（`en`、`zh`、`ja`）；拒 `eng`、`jp`。文字可用 ISO 15924：`zh-Hant`、`zh-Hans`、`zh-Hans-US` 合法；`zh-TW` 这类按地区推导文字；`zh-CN` 合法 | High |
| 5 | 区域码 | ISO 3166-1 Alpha-2。只写区域码无效（`-US` 必须配语言）。`UK`、`EU`、`UN` 在 Google 搜索里无效果（英国写 `en-GB`）。不在这两个标准里的码不受支持，**`es-419` 明确不受支持**。`es-LA` 的 `LA` 是老挝，不是拉丁美洲 | High |
| 6 | 与 canonical 的关系 | 用 hreflang 时，canonical 要指向同语言页（没有同语言页时指向最接近的替代语言）。本套件要求：簇内每页自引用 canonical，hreflang 指向的 URL 返回 200 | High |
| 7 | URL 写法 | 必须是含协议的完整 URL（`https://example.com/foo`，不是 `//example.com/foo` 或 `/foo`）；不要在 hreflang 里写 HTTP 版本 | Medium |
| 8 | 跨域 | 允许，两边都要有返回链接 | High |

补充规则：

- 大小写不敏感：`en-gb` 与 `en-GB` 都被接受；区域码大写只是 ISO 惯例。
- Google 不用 hreflang 或 `<html lang>` 判断页面语言，语言由算法识别。
- 一个 `<link>` 标签只表达一种替代关系：不要把 `hreflang` 和 `media` 等属性合在同一个标签里。
- 同语言多地区时，加一个不带地区的兜底版本（如 `en`），它可以就是某个地区版。
- 只翻译模板、主体内容没翻译的页面，会被当作重复页；hreflang 帮 Google 理解它们是同一内容的本地化变体。

## 二、实现载体：HTML / HTTP Link / XML sitemap

Google 口径：三种载体等价，可以同时用，但在搜索中没有额外收益，同时维护三套更难。实际选一种用到底。

| 载体 | 适用 | 注意 |
|---|---|---|
| HTML `<link rel="alternate">` | 大多数站点；**Yandex 只认这一种** | 必须在格式正确的 `<head>` 里；模板改版容易无声丢组 |
| HTTP `Link` 头 | PDF 等非 HTML 文件 | CDN 可能剥头；只有 `curl -I` 看得到；Yandex 文档未提此载体 |
| XML sitemap `xhtml:link` | 变体多、跨域的大站 | 子元素不计入 sitemap 的 URL 数上限；sitemap 只能列它所在目录下的 URL（经 Search Console 提交或跨站提交时另算）；**Yandex 已不再支持用 sitemap 标注语言版本** |

- 选型判据（本套件口径）：QA 与维护成本。页面代码可能被不知情的人改掉，sitemap 集中生成更容易审计；面向 Yandex 的站点必须用 HTML。
- 迁移期确需两种载体并存时，两处的值必须逐个相同；值不同比只写一处更糟（本套件口径）。

## 三、x-default 的用法

Google 定义：保留值，用户的语言 / 地区设置不匹配任何声明版本时使用；推荐写，不强制。Yandex 同样支持 `x-default`，用于按 IP 或 `Accept-Language` 自动判断语言的页面。

1. **语言 / 国家选择页**：Google 说 x-default 为它设计，效果最好。
2. **自动重定向或按语言改内容的首页**：2013-04 Google 发布 x-default 时的原例（[博客](https://developers.google.com/search/blog/2013/04/x-default-hreflang-for-international-pages)）。
3. **复用某个语言版作回退**：x-default 可以和某个语言版指向同一 URL。
4. **不针对任何地区的全球页**：内容要真正中立，不能是某一语言的硬翻。
5. **sitemap 载体同样可写**：`<xhtml:link rel="alternate" hreflang="x-default" href="…"/>`，与其他行并列。
6. **不写也合法**：没有真实回退页时宁缺毋滥；指向 404 或不相关页会误导用户（本套件口径）。

## 四、常见 CMS 与框架的实现陷阱

**WordPress**
- Polylang 会自动输出 hreflang（[Polylang 官方说明](https://polylang.pro/hreflang-tag-attributes-and-polylang-everything-you-need-to-know/)）。WPML 等多语言插件同样会生成。
- 本套件口径：多语言插件与 SEO 插件（Yoast、Rank Math）只允许一个输出 hreflang；两个都输出时同页出现两组值。未翻译的标签页、作者归档混进组，以及缓存插件把不同语言变体缓存成同一份 HTML，都是常见事故。

**Shopify**（[Markets SEO 帮助](https://help.shopify.com/en/manual/markets/seo)）
- Markets 默认自动生成 hreflang，带一个指向主域名的 `x-default`；每个市场版本自引用 canonical。
- 只有拥有独立域名、子域或子目录的市场才会生成 hreflang。
- 用主题或 app 自己输出 hreflang 时，在 Online Store > Preferences 关掉「Automatic hreflang tags」，避免重复。
- 市场码要人工核对：英国写 `en-GB`（大小写都行，但 `UK` 无效）。

**Next.js**
- 框架不会凭空生成 hreflang。App Router 在 `metadata.alternates.languages` 里写，输出 `<link rel="alternate" hreflang>`；配合 `metadataBase` 得到完整 URL（[Next.js generateMetadata 文档](https://nextjs.org/docs/app/api-reference/functions/generate-metadata)）。用这个方法时，`x-default` 要自己加进 `languages`。
- next-intl 的中间件默认在响应头 `Link` 里输出各语言 alternate，并包含 `x-default`；基于域名的路由不输出 `x-default`；`localePrefix` 设为 `never` 时整个功能关闭（[next-intl 路由配置](https://next-intl.dev/docs/routing/configuration)）。
- 本套件口径：alternate 链接要走服务端 metadata，不要写在 Client Component 里；`trailingSlash` 配置要与 hreflang、canonical 的写法一致（`/en/` 与 `/en` 不能混用）。

**CMS 无关：用 GTM 或其他 JS 注入**（本套件口径）。Google 会渲染 JS，但不渲染的爬虫看不到；渲染失败或标记未发布时没有任何报错。hreflang 由服务端模板或 sitemap 输出。审计时先 `curl`（见第六节）：curl 看不到、浏览器看得到的，就是这类问题。

## 五、`rel="alternate" media`：移动分离 URL 注解

与 hreflang 同元素不同义：`hreflang` 注语言变体，`media` 注**设备变体**，用于 m. 子域式的分离移动站（[移动优先索引文档](https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing)）。

- 桌面页：自引用 canonical，加 `<link rel="alternate" media="only screen and (max-width: 640px)" href="https://m.example.com/page">`；移动页：canonical 指回桌面版。桌面 URL 永远是 canonical。
- 分离 URL 站点的 hreflang：移动版 hreflang 指向移动 URL，桌面版指向桌面 URL，分开写。
- 同一 URL 按 UA 输出不同 HTML（动态服务）时，响应带 `Vary: User-Agent`。
- Google 推荐响应式设计；分离 URL 只在存量站维护。审计存量站时，查 canonical 方向和 media 断点是否与实际 CSS 一致。
- 常见残留错误：桌面页漏写 media 注解；m. 站 canonical 自指（应指桌面版）；把 hreflang 和 media 写在同一个 `<link>` 里。

## 六、检测工具与命令行

```bash
# HTML 载体（看服务端输出，不执行 JS）
curl -s https://example.com/en/page | grep -oiE '<link[^>]+hreflang[^>]*>'

# HTTP Link 头载体（单头多值：按逗号拆开再取值）
curl -sI https://example.com/en/page | grep -i '^link:' | tr ',' '\n' | grep -oE 'hreflang="[^"]*"'

# sitemap 载体：xhtml:link 行数应 = 语言版本数 × 簇内 URL 数
curl -s https://example.com/sitemap.xml | grep -c 'xhtml:link'

# 套件脚本：传入簇内全部语言版本，输出互指矩阵
python3 scripts/hreflang_cluster.py https://example.com/en/page https://example.com/de/seite
```

Google 文档「调试」节列出两个第三方工具（Google 不维护）：Aleyda Solis 的 hreflang 生成器、Merkle 的 hreflang 测试器。Search Console 的「国际定位」报告已弃用（2022-09 移除，[帮助中心说明](https://support.google.com/webmasters/answer/12474899)），不能再用它查返回链接错误。

## 七、批量审计流程与失效信号

1. **抽样**：每语言 × 每模板（首页 / 类目 / 详情 / 博客）抽 5–10 个 URL；翻译不全的站，「只有部分语言存在」的页单独成层抽样——它们最容易缺返回链接（本套件口径）。
2. **抓取**：按载体分别抓——HTML 用 curl，Link 头用 `curl -sI`，sitemap 按 XML 逐个 `<url>` 解析。SPA 站的 hreflang 若在水合后才注入，先记为渲染时机问题（见 [semantic-html.md](semantic-html.md)）。
3. **建组**：按 hreflang 值建成员映射，跑第 1、2、4、5 检。没互指的那一对标为失效，其余互指的照常计入。
4. **对照 canonical**：组内每个成员的 canonical 指向自己（第 6 检），否则该成员视为重复页。

失效的外部信号（Search Console）：
- 网页索引编制报告出现「重复网页，Google 选择的规范网页与用户指定的不同」，且被选中的是别的语言版。
- 效果报告按国家筛选时，某国家的展示落到了错误的语言版 URL 上。
- 网址检查：某语言版的「Google 选择的规范网址」是另一个语言版。

修复回归（本套件口径）：改动后 7–14 天复查上述信号；hreflang 被重新采纳有滞后，当天正常不代表已生效。

## 八、标签之外（常被漏掉的国际化实质）

1. **内容平价**：各语言版主体内容要等价；某语言版字数明显偏少，常是截断或漏翻。长度比的合理区间因语言而异，套件没有可靠出处的统一数字，按市场文件和人工抽查判断。
2. **本地格式**：按 CLDR 本地化数字、日期、地址、电话。例：`1000` 加两位小数，在 `de-DE` 写作 `1.000,00`，`fr-FR` 写作 `1 000,00`（Node/ICU 实测）。法语通常在 `: ; ! ?` 前加不换行空格（排版惯例，未核一手）。
3. **过期翻译**：源语言改版后其他语言没跟上——对比各语言版的 `dateModified` 或最后修改时间。
4. **未复核机翻**：大量机翻页面、没有人工审校，落入 Google「规模化内容滥用」政策的范围；Google 2025-06 删除了「用 robots.txt 屏蔽自动翻译页」的旧建议，理由是与该政策对齐（[文档更新记录](https://developers.google.com/search/updates)）。
5. **文化适配**（软项）：示例、案例、货币、合规表述是否本地化，而不是字面翻译。
6. **RTL（阿拉伯语、希伯来语版必检）**：`<html dir="rtl">`；行内反向短语用带 `dir` 的标记包紧，方向未知时用 `dir="auto"` 或 `<bdi>`；`&rlm;`/`&lrm;` 只作旧浏览器兜底（[W3C 行内双向文本](https://www.w3.org/International/articles/inline-bidi-markup/)）。电话、验证码、卡号等字段显式 `dir="ltr"`。数字体系按市场定、全站统一：CLDR 默认 `ar-EG` 用阿拉伯-印度数字，`ar-AE` 用欧洲数字。播放、进度、时钟图标与 logo 不镜像。hreflang 写了 `ar`、页面仍是 LTR 布局，是高频的假国际化。
7. **常见市场码组合**：拉美西语用 `es` 兜底，需要时加国家码（`es-MX`、`es-AR` 等），不用 `es-419`；`pt-BR` / `pt-PT` 分开；`ar` 或 `ar-EG` / `ar-SA` / `ar-AE`；`fr-FR` / `fr-CA` / `fr-BE`；`de-DE` / `de-AT` / `de-CH`；`nl-NL` / `nl-BE`；`it-IT` / `it-CH`；`hi-IN` 与 `en-IN` 并存时两版都要真实存在；`id`、`tr`、`vi`、`th`、`pl` 通常单码即够。

## 九、审计输出格式

每项检查输出：页面 URL 对 / 检查项 / 违例描述 / 严重度 / 修复建议（含正确的标签写法）。按目录聚合修复批次（一个模板的问题 = 一批），不按单页零散报。

示例行：`/de/preise ↔ /en/pricing | #2 双向返回 | DE 版缺 en 回链，这一对被忽略 | Critical | 在 /de/preise 的 head 补 <link rel="alternate" hreflang="en" href="https://example.com/en/pricing">`。

## 九bis、AI 聊天产品的边界（本套件口径）

- hreflang 服务经典搜索引擎的版本互认。没有证据表明 ChatGPT、Perplexity 这类生成式引擎会按 hreflang 给某语言用户引用对应语言版；它们看的是该语言 URL 自身的证据（该语言的外链、被引用历史、内容量、语言与查询的匹配度）。结论与检查顺序见 [multilingual-workflow.md](../overview/multilingual-workflow.md)。
- 多语言站审计要单列「每语言 URL 自有权威」：该语言的专属外链；该语言单独建立的 citation_panel 基线；llms.txt 语言版与本地平台占位。
- hreflang 照常做；报告里「经典搜索互认」与「AI 引用」分开写。引擎若开始在引用决策中使用 hreflang，本节降级（6–12 个月复审）。

## 检查清单

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 互指与自引用 | `python3 scripts/hreflang_cluster.py <簇内全部 URL>` | 失败：任何一对没有互指；任何成员缺自引用 |
| 2 | 码合法 | 第六节命令取出全部值，逐个对照 ISO 639-1 / ISO 3166-1 Alpha-2 | 失败：`es-419`、`en-UK`、`EU`、`jp`、只有区域码、下划线（`en_US`） |
| 3 | URL 完整且返回 200 | 对每个 hreflang 目标跑 `curl -s -o /dev/null -w '%{http_code}\n' <URL>` | 失败：相对 URL、HTTP 版本、3xx/4xx/5xx |
| 4 | canonical 同语言且自引用 | 每个成员抓 `<link rel="canonical">`（命令见 [redirects-canonical.md](redirects-canonical.md) 6.2） | 失败：canonical 指向其他语言版 |
| 5 | 只有一个输出源 | 对比 HTML、`Link` 头、sitemap 三处是否都出现，值是否相同 | 失败：两处都有且值不同；同页两组 hreflang |
| 6 | x-default 合理 | 查 `x-default` 目标页 | 失败：多个 `x-default`；目标 404 或与站点无关 |
| 7 | Yandex 市场用 HTML 载体 | 目标含俄语区时检查是否只用了 sitemap | 失败：只靠 sitemap 标注语言版本 |
| 8 | 不依赖 JS 注入 | `curl` 抓服务端 HTML，与浏览器渲染后对比 | 失败：hreflang 只在渲染后出现 |
| 9 | Google 侧采纳 | 网址检查各语言版的「Google 选择的规范网址」 | 失败：选中的是其他语言版 |

## 十、来源

- Google：[本地化版本](https://developers.google.com/search/docs/specialty/international/localized-versions)（三载体等价、自引用、返回链接、码规则、es-419 不支持、大小写不敏感、x-default、调试工具）、[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)（canonical 指向同语言页、不在 hreflang 里写 HTTP 版本）、[移动优先索引](https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing)（media 注解、分离 URL 的 hreflang、Vary）、[x-default 发布博客（2013-04-10）](https://developers.google.com/search/blog/2013/04/x-default-hreflang-for-international-pages)、[国际定位报告弃用](https://support.google.com/webmasters/answer/12474899)、[文档更新记录](https://developers.google.com/search/updates)
- Yandex：[本地化页面](https://yandex.com/support/webmaster/en/yandex-indexing/locale-pages)（不再支持 sitemap 标注；ISO 639-1 + ISO 3166-1 Alpha-2 或 ISO 3166-2:RU；支持 x-default；支持的语言列表）
- 平台：[Shopify Markets SEO](https://help.shopify.com/en/manual/markets/seo)、[Next.js generateMetadata](https://nextjs.org/docs/app/api-reference/functions/generate-metadata)、[next-intl 路由配置](https://next-intl.dev/docs/routing/configuration)、[Polylang](https://polylang.pro/hreflang-tag-attributes-and-polylang-everything-you-need-to-know/)
- 标准：[W3C 行内双向文本](https://www.w3.org/International/articles/inline-bidi-markup/)；Unicode 隔离符 U+2066–U+2069（LRI/RLI/FSI/PDI）
- Bing：现行 [Webmaster Guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a) 未提 hreflang；第三方常说 Bing 主要看 `content-language`，未找到一手原文（未核），不要据此下结论。
- 框架思路：[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-hreflang/SKILL.md`
