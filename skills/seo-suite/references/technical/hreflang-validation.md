# hreflang / 国际化校验（八检框架）

> 建立于 2026-10-09。校验规则参考 [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo)（MIT）`skills/seo-hreflang/SKILL.md`，按本套件证据约束改写。
> 适用场景：多语言/多区域站。本套件自身即双语（EN/中文），此文件同时服务内部。

## 一、八项校验（每项是真规则，不是清单口号）

| # | 检查 | 规则 | 违例严重度 |
|---|---|---|---|
| 1 | 自引用 | 每个语言版必须含指向自身的 hreflang，且与该页 canonical URL **全等**（含尾斜杠） | Critical——缺失则 Google 可能**忽略整组** |
| 2 | 双向返回 | A→B 则必须 B→A；全网格互指 | Critical |
| 3 | x-default | 仅当回退页真实存在；每组**至多一个** | High |
| 4 | 语言码 | ISO 639-1（`en`/`zh`/`ja`）；拒 `eng`/`jp`。文字用 ISO 15924：`zh-Hant`、`zh-Hans-US` 合法 | High |
| 5 | 区域码 | ISO 3166-1 Alpha-2 **大写**；拒 `en-uk`（应为 `en-GB`）、`EU`/`UN`（非国家）、`es-LA`（非单一国家）；`es-419`：**口径冲突待复核**——Google 官方文档列为支持值（UN M.49 例外），但有西语从业者报告解析器不认（2026-10）；稳妥写法=`es` 兜底 + `es-419` + 国码全簇双向回链（两说兼容）；**仅国家码无效**（`-US` 必须配语言） | High |
| 6 | 位置 | hreflang 仅在 canonical URL 上有效；与 canonical 精确匹配（含尾斜杠） | High |
| 7 | 协议 | 组内 https/http 一致 | Medium |
| 8 | 跨域 | 允许，但**两个域都要有返回标签** | High |

## 二、实现载体选择:HTML / HTTP Link / XML sitemap(2026-10-09 二波深化)

官方口径:三种载体**完全等价**,选一种用到底——同时用多种"没有额外好处,且比只用一种更难维护"(Google localized-versions 官方文档)。

| 载体 | 适用 | 优势 | 代价/陷阱 |
|---|---|---|---|
| HTML `<link rel="alternate">` | <50 个语言变体的小站 | 每页可见、调试直观;GSC 国际定位报告直接对应 | 模板改动即全站生效——主题升级/改版常无声丢组;HTML 头体积随语言数线性膨胀 |
| HTTP `Link` 头 | 非 HTML 资源(PDF/XLS 等) | 不动文档本身 | CDN/缓存层可能剥头;浏览器 devtools 不显眼,只有 curl 能看见 |
| XML sitemap `xhtml:link` | 50+ 变体、跨域、大站 | 集中生成与 QA,不污染页面;**xhtml:link 子元素不计入 sitemap 的 URL 数上限**(官方明文) | 页面翻页/下线时组内半边失效;sitemap 只能含自身目录下 URL |

载体选择的真实判据是 **QA 与维护成本**:on-page 代码可能在 SEO 不知情时被改掉,sitemap 集中一处更易审计(BrightEdge);大站普遍认为 sitemap "最易实现、测试与监控"(Bounteous 2021;Seer 2023 同口径)。行业统计:hreflang 实现 **约 75% 含错误**(缺 return tags、断链为主)——载体不是主因,组内不对称才是(Digital Applied 2026-01)。

混合警告:同一 URL 组在 HTML 与 sitemap 各写一份且值不一致时,冲突信号比只写一处更糟(GSC 帮助论坛多起案例);确需并存(迁移期)必须逐值全等。

## 三、x-default 的六种正确用法(2026-10-09 二波深化)

官方定义:保留值,用于**用户语言/区域不匹配任何已声明版本时**的回退;回退页的语言本身无关紧要;**推荐而非强制**,每组至多一个(localized-versions 官方文档)。

1. **语言/国家选择器页**——官方点名的最佳宿主:选择器无需先猜语言,x-default 直接指向它。
2. **自动重定向型首页**:example.com 按浏览器 Accept-Language 跳 /en/、/de/——x-default 发布时的官方原案例(2013-04 官方博客)。首页若不标 x-default,爬虫无法把根 URL 收进组,根域权重传递断裂。
3. **复用某个语言版作回退**:x-default 与 hreflang="en" 指向同一 URL 合法(该页既是英语版又是兜底);SEMrush 等工具对此报"冲突"属误报(webmasters.SE 2019 讨论)。
4. **不定向任何区域的全球页**:如 /worldwide/ 落地页,组内其余语言均不匹配时退到这里;页面内容需真实中立,不能是某一语的硬翻。
5. **sitemap 载体下同样可写**:`<xhtml:link rel="alternate" hreflang="x-default" href="…"/>` 与其他行并列,规则与 HTML 载体一致(官方 sitemap 示例)。
6. **不写也是合法选择**:没有真实回退页(如单区域多语言 B2B 站)时宁缺毋滥——指向 404 或不相干页会拖累整组可信度。

## 四、常见 CMS 实现陷阱:WordPress / Shopify / Next.js(2026-10-09 二波深化)

**WordPress**
- WPML:hreflang 组**按"当前已发布翻译"动态生成**——新增语言或某译稿转草稿后组内成员变化,出现 `en-EU` 缺失/错配 `en-NL` 这类不完整组(WPML 论坛 2025-02 实例);排查=逐 URL 对拍组内成员列表。
- Polylang:原生输出 hreflang,但与 SEO 插件(Yoast/Rank Math)**双写**时同页出现两组值打架——只允许一个发射源。
- 通用陷阱:两个 SEO 插件并存各写一份;tag/作者归档页未翻译却混入组;缓存插件把不同 query 参数的语言变体缓存成同一份 HTML(组在缓存命中时消失)。

**Shopify**
- Markets 自动生成 hreflang+canonical,但**主市场不能在主域名上用子目录**(官方社区:subfolder 仅对非主市场可用)——主市场想要 /us/ 得用第三方 app 或独立域,app 与 Markets 并存时 hreflang 双写是高频事故。
- 多域(每 market 绑独立域)时 hreflang 跨域自动输出,但**旧的手动 canonical 仍指主域**会与 Markets 新输出冲突——迁到 Markets 前清一遍 legacy 设置(Shopify 官方 Markets SEO 文档;社区 2026-02 案例)。
- 市场码大小写不稳(`en-uk`):需人工核对 ISO 3166-1 Alpha-2 大写(八检第 5 条)。

**Next.js**
- 框架**不自动输出** alternate links(vercel RFC #17078 明确拒绝自动生成)——必须 App Router 用 `metadata.alternates.languages` 手写,Pages Router 用 `next/head`。
- 陷阱一(渲染时机):alternate links 写进 Client Component 时,SSR 首屏 HTML 没有、水合后才补——不渲染的爬虫(多数 AI 爬虫不渲染 JS)完全看不见,Google 也有计入延迟。`<link>` 必须走服务端 metadata API。
- 陷阱二:`trailingSlash` 配置与 hreflang 值不一致(/en/ vs /en)导致与 canonical 不全等,整组作废——八检第 6 条在 Next 下最易踩。
- 陷阱三:next-intl 等库的 alternateLanguages 输出**不含 x-default**,需在 metadata 手动补(Weglot 2026-06 Next.js hreflang 实操)。

**CMS 无关的第四个陷阱:GTM 注入**。hreflang 用 Google Tag Manager 等 JS 方式注入的,不在服务端 HTML 里——Google 需渲染才可见,不渲染的爬虫(AI 爬虫多不渲染)完全看不见,且渲染失败/标记未发布时**无任何报错**。hreflang 必须由服务端模板/sitemap 输出;审计时先 `curl` 确认(见六),curl 看不到而浏览器看得到的即此类问题。

## 五、rel="alternate" media 属性:移动分离 URL 注解(2026-10-09 二波深化)

与 hreflang 同元素不同义:`hreflang` 注语言变体,`media` 注**设备变体**,服务于 m.example.com 式分离移动站。

- 桌面页:`<link rel="alternate" media="only screen and (max-width: 640px)" href="https://m.example.com/page">`;移动页用 `rel="canonical"` 回指桌面版(Google 2011-12 smartphone Googlebot 发布文,官方 separate-urls 文档沿用)。
- sitemap 载体同样可注 media 变体:`<xhtml:link rel="alternate" media="only screen and (max-width: 640px)"/>`(官方 separate-urls 文档示例)——与 hreflang 的 sitemap 写法同构。
- 服务器侧配套:按 UA 分发不同 HTML 时必须带 `Vary: User-Agent` 响应头(官方文档要求),否则中间缓存可能把桌面版发给移动爬虫。
- **现状(2026)**:功能机 Googlebot 已退役(2016-11 官方公告);响应式设计为官方首选,分离 URL 仅存量站维护。**新站不做移动分离**;审计存量站时八检不适用于此组,查的是 canonical 回指方向与 media 断点一致性。
- 常见残留错误:桌面页漏写 media 注解;m. 站 canonical 自指(应指桌面版);640px 断点声明与实际 CSS 断点不符。

## 六、检测工具与命令行(2026-10-09 二波深化)

HTML 载体(看服务端输出,不执行 JS):
```bash
curl -s https://example.com/en/page | grep -o '<link rel="alternate"[^>]*>'
```

HTTP Link 头载体(devtools 看不见,只有 curl 可见):
```bash
curl -sI https://example.com/en/page | grep -i '^link:'
# 单头多值解析:按逗号拆开后逐段取 hreflang 值
curl -sI https://example.com/en/page | grep -i '^link:' | tr ',' '\n' | grep -o 'hreflang="[^"]*"'
```

sitemap 载体组成员数核对:
```bash
curl -s https://example.com/sitemap.xml | grep -c 'xhtml:link'   # 应 = 语言数 × URL 数
```

浏览器侧工具:Google 官方"调试"节列出 Aleyda Solis hreflang 生成器与 Merkle hreflang 测试器(第三方,官方不维护);GSC 国际定位报告逐页暴露缺回链错误。

## 七、批量审计流程与失效信号(2026-10-09 二波深化)

全站审计流水线(三载体通用):
1. **抽样**:每语言×每模板类型抽 5–10 URL(首页/类目/详情/博客),翻译未全的站另抽"仅部分语言存在"的页。
2. **抓取**:按载体分别抓——HTML 用 curl grep(见六);Link 头用 `curl -sI`;sitemap 用 XML 解析。**注意抓服务端输出**:SPA 站 hreflang 在水合后注入的,先记为渲染时机问题(与 [semantic-html.md](semantic-html.md) 的 React/Vue 陷阱同根)。
3. **建组**:URL 组内成员按 hreflang 值建映射,跑八检 1/2/4/5(自引用、双向、码合法性)——组不完整即 Critical,其余检查在完整组上才有意义。
4. **对照 canonical**:组内每个成员的 canonical 必须指向自身(六检),否则该成员整行无效。

三载体各自的审计入口:

| 载体 | 抓取方式 | 组建来源 |
|---|---|---|
| HTML | `curl -s <url>` grep link 标签 | 每个成员页的头部 |
| Link 头 | `curl -sI <url>` | 同上 |
| sitemap | XML 解析逐 `<url>` 块 | 块内全部 `xhtml:link` 行天然成组 |

抽样规模:每语言×每模板 5–10 URL;翻译不全的站,「部分语言存在」的页单独成层抽样——它们最容易缺回链。

**组已失效的外部信号**(GSC 国际定位报告):
- "返回标签缺失/错误"按页列出——修复顺序按目录聚合,不按单页;一个模板的 bug 影响整目录。
- 错误语言版流量骤降但站点整体正常——常是某语言组整组被忽略(检查 1/2 违例的典型症状)。
- "未知错误"多为非法语言码(四检)或 x-default 多于一个(三检)。

**修复回归**:改动后 7–14 天复查 GSC 报错曲线;hreflang 信号被重新采纳有明显滞后,当天清零不代表生效。

## 八、标签之外（常被漏掉的国际化实质）

1. **内容平价字数比**：德语版通常比英语**长 25–35%**、日语**短 10–25%**——大幅偏离提示某语言版是截断/机器直译，不是对等翻译。
2. **本地格式**：`1,000.00` 在 de-DE 应为 `1.000,00`；日期、地址、电话同理；法语 `:;!?` 前有不换行空格。
3. **过期翻译**：EN 改版后其他语言未跟——检测各语言版 dateModified 差距。
4. **未复核机翻**：整站机翻无人工审校标记为 scaled-content-abuse 风险（Google 政策名目）。
5. **文化适配**（软项）：各语言版的示例、案例、货币、合规表述是否本地化，而非字面翻译。
6. **RTL 审计项（阿拉伯语版必检,2026-10 二波深化）**：`<html dir="rtl">` 全链、双向文本隔离（`<bdi>` 或 U+2066–2069,禁裸 RLM/LRM 补丁——W3C string-meta TR）；`<input dir="rtl">` 按类型自动方向,电话/验证码/卡号字段显式 `dir="ltr"`；数字：阿拉伯-印度数字(٠-٩) vs 欧洲数字全站统一,货币顺序按本地习惯；**镜像例外**：播放/进度/时钟图标与 logo 不镜像；字体：**preload 会绕过 unicode-range→只 preload 阿语子集单文件**（Tajawal 阿语子集仅 8.7KB）,用 size-adjust 回退字体控 CLS（阿语字形度量致 CLS 高于拉丁）；遗留 left/right 用 `[dir="rtl"]` 覆盖表——hreflang `ar` 正确但页面仍是 LTR 布局是高频假国际化。
7. **常见市场码组合**（2026-10-08 并入）：`es-ES`+`es-419`(+国码同 URL 可选)；`pt-BR`/`pt-PT` 分开（内容差异实质存在）；`ar`+`ar-EG`/`ar-SA`/`ar-AE`（或单一 `ar`）；`fr-FR`/`fr-CA`/`fr-BE` 分开；`de-DE`/`de-AT`/`de-CH` 分开（Sie/du 与词汇差异）；`id`（印尼通常单码即够）；`hi-IN`/`en-IN` 并存时必须两版都真实；`it-IT`/`it-CH` 分开（复制会被归并信号）；`nl-NL`/`nl-BE` 分开（弗拉芒词汇不同；比利时另有 `fr-BE`/`de-BE`）；`tr-TR`/`vi-VN`/`th-TH`/`pl-PL` 通常单国单码。

## 九、审计输出格式

每项检查输出：页面 URL 对 / 检查项 / 违例描述 / 严重度 / 修复建议（含正确的标签写法）。整组失效（检查 1/2 违例）时优先提示——单项修好也没用。
示例行：`/de/preise ↔ /en/pricing | #2 双向返回 | DE 版缺 en 回链,Critical | 在 /de/preise head 补 <link rel="alternate" hreflang="en" href="https://example.com/en/pricing">`。
输出按目录聚合修复批次(一个模板 bug=一批),不按单页零散报。

## 十、来源

- 八检规则与正反例、严重度表：[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-hreflang/SKILL.md`
- 字数比/本地格式/机翻风险：同上 SKILL.md 的内容平价段
- 三载体等价与"勿混用"、x-default 定义与选择器页推荐、sitemap 子元素不计上限、es-419 口径:[Google: Localized versions of your pages](https://developers.google.com/search/docs/specialty/international/localized-versions)
- x-default 自动重定向首页原案例:[Google 2013-04 x-default 发布博客](https://developers.google.com/search/blog/2013/04/x-default-hreflang-for-international-pages)
- en 与 x-default 同页合法(SEMrush 误报):[webmasters.SE 2019](https://webmasters.stackexchange.com/questions/126514/)
- sitemap 载体 QA/维护优势:[BrightEdge](https://amp.brightedge.com/blog/hreflang-xml-sitemaps-and-html-link-elements-and-international-site-management)、[Bounteous 2021](https://www.bounteous.com/insights/2021/15/10/hreflang-beginners-harnessing-global-seo/)、[Seer 2023](https://www.seerinteractive.com/insights/international-seo-hreflang-guide)
- 75% 实现含错误统计:[Digital Applied 2026-01](https://www.digitalapplied.com/blog/international-seo-hreflang-multilingual-guide)
- WPML 组动态生成错配:[WPML 论坛 2025-02](https://wpml.org/forums/topic/issue-with-hreflangs/);Polylang 原生 hreflang:[wpmarmite 2026-09](https://wpmarmite.com/en/compare/best-wordpress-multilingual-plugins/polylang/)
- Shopify Markets 规则与限制:[官方 SEO 文档](https://help.shopify.com/en/manual/markets/seo)、[社区 2026-02 案例](https://community.shopify.com/t/are-my-hreflang-tags-set-up-correctly-duplicate-content-issues/588258)
- Next.js 不自动生成 alternate links:[vercel RFC #17078](https://github.com/vercel/next.js/discussions/17078);App Router hreflang 实操:[Weglot 2026-06](https://www.weglot.com/blog/nextjs-internationalization)
- rel=alternate media 与 640px 断点:[Google 2011-12 博客](https://developers.google.com/search/blog/2011/12/introducing-smartphone-googlebot-mobile);功能机 Googlebot 退役:[2016-11 公告](https://developers.google.com/search/blog/2016/11/an-update-on-googles-feature-phone)
- 官方调试工具清单(Aleyda/Merkle):localized-versions 文档"调试"节
- GTM 注入 hreflang 的不可靠性:服务端输出原则由本文"可抓取性"基线推出(与 Google JavaScript SEO 基础一致)
