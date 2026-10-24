# 移动 SEO 专项

> 2026-10-21 按 Google 官方文档与 W3C、web.dev、Lighthouse 原文核对。分工：JS 渲染诊断见 [rendering-seo.md](rendering-seo.md)；CWV 指标与阈值见 [cwv-playbook.md](cwv-playbook.md) 和 [LCP.md](LCP.md)；viewport 写法与 head 顺序见 [head-elements.md](head-elements.md)；各市场移动占比见 [markets/](../markets/id.md) 各文件。本文件只做移动专项，不重复。

## 一、移动优先索引的现状

### 1.1 时间线

| 时间 | 事件 | 出处 |
|---|---|---|
| 2016-11 | Google 开始移动优先抓取与索引 | [Google 博客 2023-10-31](https://developers.google.com/search/blog/2023/10/mobile-first-is-here) |
| 2023-10-31 | Google 宣布迁移完成；极少数移动端完全不可用的站点暂用桌面 Googlebot | 同上 |
| 2024-07-05 之后 | 剩余站点也只用 Googlebot Smartphone 抓取和索引；移动设备完全打不开的内容不再可索引 | [Google 博客 2024-06-03](https://developers.google.com/search/blog/2024/06/mobile-indexing-vlast-final-final.doc) |

- **核心含义**：Google 用智能手机 UA 抓取的移动版内容做索引和排名（[移动优先索引文档](https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing)）。文档同时写明：移动版内容比桌面版少时，Google 取不到这些信息，可能损失流量。桌面版有、移动版没有的文案、内链、图片 alt、结构化数据、标题，Google 看不到。
- 日志里仍可能看到桌面 Googlebot：商品信息、Google 招聘等少数功能有时用它抓取（2024-06-03 博客）。
- 不是必须有移动版，但官方「强烈建议」。响应式设计是 Google 推荐的做法；下面 1.2、1.3 的要求只针对动态服务和分离 URL 两种配置。
- 纠偏（本套件口径）：提案里写「做好移动适配以便进入移动优先索引」是过时说法；现在的正确表述是「移动版就是被索引的内容本体」。

### 1.2 移动版与桌面版要对齐的内容（官方清单）

| 项 | 官方要求 | 常见踩坑 |
|---|---|---|
| robots meta | 移动版与桌面版用相同的 robots meta；移动版上的 `noindex`/`nofollow` 可能让 Google 无法抓取或索引 | 移动模板单独加了 noindex |
| 主内容 | 内容等价；可以把内容放进折叠面板或标签页，只要内容等价 | 移动版删减段落 |
| 标题层级 | 使用相同、清楚的标题 | 移动版换了 H1 |
| 懒加载 | 不要让主内容依赖滑动、点击、输入才加载 | 「展开更多」按钮后才请求正文 |
| 结构化数据 | 两版相同；优先补 Breadcrumb、Product、VideoObject；移动版里的 URL 改成移动 URL | 移动版靠 JS 注入且失败 |
| title、meta description | 两版等价 | m. 站模板 title 与桌面不同步 |
| 图片 | 高质量、受支持的格式、不用每次加载都变的 URL、alt 文本与桌面相同 | 移动版换了裁剪图，alt 丢失 |
| 视频 | 稳定 URL、受支持的格式和标签、结构化数据相同、放在不用大量滚动就能看到的位置 | 移动版视频藏在页底 |
| 广告 | 遵守 Better Ads Standard；顶部广告不要占太大空间 | 首屏被广告占满 |

### 1.3 独立 m. 站（历史遗留）的要求

- 桌面 URL 永远是 canonical；移动页 canonical 指回桌面，桌面页用 `rel="alternate" media="only screen and (max-width: 640px)"` 指向移动页。
- 两版的错误状态要一致：桌面正常、移动返回错误页，这一页会从索引里消失。
- 移动 URL 不要带片段（`#`）；多数片段 URL 不可索引。
- 不同的桌面页要有各自对应的移动页；全部跳到移动首页，这些页面都会从索引里消失。
- hreflang 分开写：移动 URL 指向移动 URL，桌面 URL 指向桌面 URL。
- 两版都在 Search Console 验证；robots.txt 规则一般两版相同；移动站要扛得住抓取量上升。
- 新项目与重构一律响应式（本套件口径）。同一 URL 按 UA 输出不同 HTML 时必须带 `Vary: User-Agent`。

### 1.4 内容平价检查法

1. **双 UA / 双视口抓取对比**：同一 URL 分别用移动与桌面 UA（或约 375px 与 1280px 视口）取页面，对比主内容文本量、内链数、图片数、结构化数据条数（命令见检查清单）。本套件口径：差异 >20% 黄旗，>50% 红旗。
2. **Search Console 按设备拆分**：效果报告加「设备」维度；某页移动点击断崖而桌面正常，常是平价破裂（移动版渲染失败或内容缺失）。
3. **网址检查**：看 Googlebot Smartphone 抓到的渲染后 HTML 是否含关键内容（「Crawled as」字段显示抓取设备）。这是以 Google 视角确认的办法。
4. **爬虫工具**：Screaming Frog、Sitebulb 都能按 UA 分设备抓取，导出两份做对比。

| 症状 | 优先怀疑 | 验证 |
|---|---|---|
| 移动点击掉、桌面稳 | 移动版渲染失败或内容缺失 | 网址检查看渲染后 HTML |
| 移动版字数系统性少 | 移动模板裁剪（m. 站遗留） | 双 UA 对比 |
| 富结果消失 | 移动版 JSON-LD 缺失或 JS 注入失败 | 网址检查 + 富媒体搜索结果测试 |
| 图片搜索流量掉 | 移动版换图或丢 alt | 双 UA 对比 img 与 alt |

## 二、移动页面体验

### 2.1 viewport

- 写法：`<meta name="viewport" content="width=device-width, initial-scale=1">`（细节见 [head-elements.md](head-elements.md)）。
- 固定宽度（如 `width=980`）会让手机横向滚动，是 P0 级移动缺陷；不要禁止用户缩放（无障碍，本套件口径）。
- Lighthouse 12（2024-04）把 viewport 审计从 SEO 类移到最佳实践类；Lighthouse 13（2025-10）改为 `viewport-insight`（[Lighthouse 12 发布说明](https://github.com/GoogleChrome/lighthouse/releases/tag/v12.0.0)、[迁移到 insights](https://developer.chrome.com/blog/moving-lighthouse-to-insights)）。

### 2.2 触摸目标

- web.dev 建议：触摸目标约 48 个设备独立像素，目标之间横竖约留 8 像素（[web.dev](https://web.dev/articles/accessible-tap-targets)）。
- WCAG 2.2 SC 2.5.8（AA）：目标至少 24×24 CSS 像素；例外包括间距足够、页面上有等效控件、句子中的行内链接、浏览器默认控件、必要的呈现（[W3C](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)）。所以正文里的行内文字链不按这条判失败。
- 工具现状：Lighthouse 12 删除了 SEO 类的 `tap-targets` 审计，改由无障碍类的 `target-size` 审计检查。
- 审计报两条线（本套件口径）：48px 推荐线、24px WCAG 底线；重点看导航、分页器、表单控件、底部固定栏。

### 2.3 字体与对比度

- 正文基准 ≥16px（本套件口径）。Lighthouse 13 已删除 `font-size` 审计，需要用自己的检查。
- 表单输入框字号小于 16px 时，iOS Safari 聚焦会自动放大页面——这是前端社区的普遍经验，未找到 Apple 一手文档（未核），审计报 warn，不报 fail。
- 正文对比度至少 4.5:1，大字号至少 3:1（[WCAG 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)）。

### 2.4 阈值速查表

| 项 | 推荐值 | 底线 / 出处 | 审计判定（本套件口径） |
|---|---|---|---|
| viewport | `width=device-width, initial-scale=1` | 固定宽度导致横向滚动 | 固定宽 = fail；禁缩放 = warn |
| 触摸目标 | ≈48×48 px，间距 ≈8px（web.dev） | WCAG 2.5.8：24×24 CSS px（有例外） | 非例外目标 <24px = fail |
| 正文字号 | ≥16px | — | warn |
| 输入框字号 | ≥16px | iOS 聚焦放大（未核） | warn |
| 对比度 | 正文 ≥4.5:1 | WCAG 1.4.3 | fail |
| 插页 | 不遮住主内容、易关闭 | 见 2.5 | 违规形态 = fail |
| 横向滚动 | 360px 视口下没有 | 派生自 viewport | fail |

### 2.5 插页与弹窗

- **2017 年的移动信号**：Google 2016-08-23 宣布，自 2017-01-10 起，从移动搜索结果点进来后不能轻松看到内容的页面，排名可能下降。博客列了三种做法：进入后或浏览中弹出遮住主内容的弹窗；必须先关闭才能看主内容的独立插页；首屏看起来像独立插页、原内容压在折叠线下。不受影响的情况（负责任地使用时）：法律要求的 Cookie 或年龄验证；内容本来不公开时的登录框（如邮件、付费墙后的内容）；占用合理空间、容易关闭的横幅（[Google 博客 2016-08-23](https://developers.google.com/search/blog/2016/08/helping-users-easily-access-content-on)）。
- **现行文档**：侵扰性插页和弹窗让 Google 难以理解内容，可能导致搜索表现不佳。非法律要求的情况下不要遮住整页，也不要把用户跳到单独页面去同意或填写信息。法律强制的插页（如年龄门）不受此限，但建议覆盖在内容之上，不要把所有 URL 跳到同一个页面；成人内容年龄门可以在核实 Googlebot 后让它免过年龄门（[插页与弹窗文档](https://developers.google.com/search/docs/appearance/avoid-intrusive-interstitials)）。
- 官方没有「占屏幕超过 X% 即违规」的数字阈值。
- 检测工具现状：Search Console 移动可用性报告、Mobile-Friendly Test 工具与 API 已于 2023-12 退役（[Google 博客注记](https://developers.google.com/search/blog/2016/05/a-new-mobile-friendly-testing-tool)）。现在用 Lighthouse、PSI、CrUX 现场数据，加爬虫级 DOM 检查（弹窗类名、属性清单可参考 [audit-rules/mobile.md](audit-rules/mobile.md) 的 audit_negative 思路）。

## 三、AMP：已没有搜索特权

| 时间 | 事件 | 出处 |
|---|---|---|
| 2021-06 中旬起 | Top Stories 收录所有符合 Google 新闻政策的内容，不再要求 AMP；取消 AMP 徽标 | [Google 博客 2021-04-19](https://developers.google.com/search/blog/2021/04/more-details-page-experience) |
| 2026-07-01 | Google 搜索直接把用户送到发布商自己的 AMP 主机页，不再需要 AMP Cache 和 signed exchange；AMP 内容与其他网页一样参与排名 | [文档更新记录](https://developers.google.com/search/updates) |

- 留存与否（本套件口径）：唯一保留理由是遗留依赖；新项目不再引入 AMP。现在 AMP 只剩成本（双模板、受限组件、统计口径分裂），没有搜索收益。

迁出 AMP 的执行清单（本套件口径）：
1. **存量盘点**：从 Search Console、sitemap、内链列出全部 `/amp/` 与 `?amp` URL，按外链与流量排序，高价值页先迁。
2. 每个 AMP URL 301 到对应的规范 URL（不要批量跳首页）；从规范页删除 `<link rel="amphtml">`。
3. sitemap 与内链同步清理。
4. **性能先行**：下线前确认替代页的移动端 p75 CWV 不变差，逐模板对比 AMP 版与规范版的 LCP / INP / CLS。
5. Article / NewsArticle 的 JSON-LD 原样搬到规范页，逐字段校验。
6. 迁移后 2–4 周盯网页索引编制报告和 Discover 流量；短期波动正常，持续下跌再排查。

## 四、移动性能特殊性

- CWV 阈值与判定见 [cwv-playbook.md](cwv-playbook.md)。CrUX 按设备类型分开报告；审计看移动端 p75：`python3 scripts/field_data.py --url https://example.com/ --strategy both`。
- 报告永远拆设备：同一站点移动与桌面的 CWV 常有明显差距（本套件口径）。

| 环境 | 参数 | 用途 |
|---|---|---|
| Lighthouse 移动默认（与 PSI 一致） | 模拟节流：RTT 150ms、下行 1.6 Mbps / 上行 750 Kbps（约第 85 百分位的移动网络，Lighthouse 里叫「Slow 4G」）；CPU 4 倍降速，模拟中端手机 | 标准移动基线（[Lighthouse 节流文档](https://github.com/GoogleChrome/lighthouse/blob/main/docs/throttling.md)） |
| DevTools 网络节流预设 | 以当前 DevTools 面板显示的数值为准 | 复测、压力测试 |
| 中端安卓真机 | — | 校准模拟结果，发布前抽测 |

- 新兴市场：各市场的移动占比和测试基线见对应 markets 文件（如 [markets/id.md](../markets/id.md)、[markets/hi.md](../markets/hi.md)），本文件不重复数字。
- 移动特有的指标风险：首屏大图缺 `srcset`/`sizes`；LCP 图误加 `loading="lazy"`；图片缺 `width`/`height` 引起 CLS；字体交换位移；触屏交互密集、中端机 CPU 慢、第三方脚本让 INP 在移动上更差。

## 五、移动 SERP 与应用深度链接

### 5.1 移动 SERP

- 设备之间的 SERP 特性和排名会不同。排名追踪按设备拆分，记录维度与方法见 [serp-feature-taxonomy.md](../research/serp-feature-taxonomy.md)；CTR 曲线与 AI Overviews 对点击的影响见对应研究文件，本文件不重复第三方数字。
- Discover 机制见 [discover-news-seo.md](../content/discover-news-seo.md)；本地包见第六节。
- 对 KPI 的含义（本套件口径）：移动流量目标用移动端自己的 CTR 曲线校准，不要用桌面 CTR 外推。

### 5.2 应用深度链接

- **Google 现行口径**（[Google 博客 2025-05-02](https://developers.google.com/search/blog/2025/05/app-deep-links)）：网站上的深度链接把网页 URL 与 app 内页面关联起来，**不改变** Google 搜索展示内容的方式；索引和排名用的仍是网页内容。用户装了 app 时，从搜索结果直接进入 app 内对应页面。只在 app 页面与网页内容相同时才加深度链接，布局可以不同。
- 实现：Android 用 App Links（在 manifest 里关联网站，网站放 `/.well-known/assetlinks.json`）；iOS 用 Universal Links（网站放 `apple-app-site-association` 文件，并在 app 里配置）。
- 验证工具：Play 管理中心的深度链接页、Android Studio 的 App Links Assistant、Apple 技术说明 TN3155（调试 Universal Links）。Search Console 效果报告可用「Android 应用」搜索结果呈现筛选查看 Android 深度链接的展示。
- **已关停**：Firebase Dynamic Links 于 2025-08-25 关停，所有链接（含自定义域名和 page.link）返回 404（[Firebase FAQ](https://firebase.google.com/support/dynamic-links-faq)）。
- 商务含义（本套件口径）：深度链接是转化优化项，不是索引项；按 2016 年「app indexing」思路收费的提案是话术过期。

## 六、移动内容策略（本套件口径）

- **语音查询**：多发生在手机和智能助手上，查询更长、更口语、常带本地意图。不需要为语音单独建页（见 [content-patterns.md](../content/content-patterns.md)）；落点是自然问句做标题、首句给结论、段落短。FAQ 富结果已不再在 Google 搜索中显示（[日期](../overview/facts.md#rich-results)），不要为语音或富结果堆 FAQ 标记。
- **本地意图**：「附近」「营业中」类查询以移动为主；click-to-call、路线、营业时间放在移动版首屏可达的位置。网格化追踪见 [local-grid-ranking.md](../monitoring/local-grid-ranking.md)。移动版的地址、电话与商家资料保持一致。
- **移动先写**：既然索引看移动版，写作和排版以移动版为初稿：答案前置；折叠区可放补充内容，主结论放在展开区之上；横向滚动的表格在 360px 下改成卡片或定义列表。

## 七、检查清单

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | viewport 正确且唯一 | 命令 1 | 通过：每个模板恰好一个 `width=device-width, initial-scale=1`。失败：缺失、固定宽度、多个 |
| 2 | 360px 下无横向滚动 | Chrome DevTools 设备模式 360px 逐页型查看；或命令 2 截图人工看 | 失败：出现横向滚动条或内容被截断 |
| 3 | 移动版与桌面版内容平价 | 命令 3（双 UA 文本量、链接数、JSON-LD 数） | 本套件口径：任一项差异 >20% 黄旗，>50% 红旗 |
| 4 | robots meta 两版相同 | 命令 3 同时输出两版的 robots meta | 失败：移动版有 noindex/nofollow 而桌面没有 |
| 5 | Google 实际抓到的移动版 | 网址检查：「Crawled as」应为智能手机；查看渲染后 HTML 与截图 | 失败：主内容、结构化数据缺失 |
| 6 | 触摸目标 | Lighthouse 无障碍类 `target-size` 审计；人工量导航和底部栏 | 失败：非例外目标 <24×24 CSS px |
| 7 | 插页与弹窗 | 用手机 UA 从搜索结果进入主要落地页，记录弹出时机、遮挡面积、关闭难度 | 失败：进入即全屏遮挡；跳转到单独的同意页 |
| 8 | 移动端 CWV | `python3 scripts/field_data.py --url <URL> --strategy both` | 失败：移动端 p75 任一核心指标为 poor（脚本退出码 1） |
| 9 | m. 站接线（如有） | 抽样桌面页与对应 m. 页，查 canonical、alternate media、重定向目标 | 失败：m. 页 canonical 自指；移动 UA 被跳到首页 |
| 10 | AMP 遗留（如有） | `curl` 抽查 `/amp/` URL 是否 301 到规范页；规范页是否还有 `rel="amphtml"` | 失败：AMP URL 仍返回 200 且规范页仍链向它（迁移中除外） |
| 11 | 深度链接（有 app 时） | `curl -s https://example.com/.well-known/assetlinks.json`、`curl -s https://example.com/.well-known/apple-app-site-association` | 失败：文件 404、不是合法 JSON，或 app 页面内容与网页不同 |

```bash
# 命令 1：viewport 数量与内容
curl -s -A "Mozilla/5.0 (Linux; Android 10; Mobile)" https://example.com/page | grep -oiE '<meta[^>]+name="?viewport"?[^>]*>'

# 命令 2：360px 视口截图（macOS 路径；Linux 用 google-chrome）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --user-data-dir=/tmp/chrome-seo --window-size=360,800 --screenshot=/tmp/m360.png https://example.com/page

# 命令 3：移动 UA 与桌面 UA 的平价对比（可见文本字符数、<a href> 数、JSON-LD 块数、robots meta）
for ua in "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 Chrome/141.0 Mobile Safari/537.36" \
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/141.0 Safari/537.36"; do
  curl -s -A "$ua" https://example.com/page > /tmp/p.html
  python3 -I -c '
import re,sys
s=open("/tmp/p.html",encoding="utf-8",errors="replace").read()
ld=len(re.findall(r"application/ld\+json",s,re.I)); a=len(re.findall(r"<a\s[^>]*href=",s,re.I))
rb=re.findall(r"<meta[^>]+name=\"?robots\"?[^>]*>",s,re.I)
t=re.sub(r"(?is)<(script|style|noscript|template)[^>]*>.*?</\1>"," ",s); t=re.sub(r"(?s)<[^>]+>"," ",t)
print("text=%d links=%d jsonld=%d robots=%s" % (len(re.sub(r"\s+","",t)), a, ld, rb))'
done
```

## 来源

- Google：[移动优先索引最佳做法](https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing)、[Googlebot](https://developers.google.com/search/docs/crawling-indexing/googlebot)、[2023-10-31 移动优先完成](https://developers.google.com/search/blog/2023/10/mobile-first-is-here)、[2024-06-03 最后一步](https://developers.google.com/search/blog/2024/06/mobile-indexing-vlast-final-final.doc)、[插页与弹窗](https://developers.google.com/search/docs/appearance/avoid-intrusive-interstitials)、[2016-08-23 插页信号](https://developers.google.com/search/blog/2016/08/helping-users-easily-access-content-on)、[Mobile-Friendly Test 退役注记](https://developers.google.com/search/blog/2016/05/a-new-mobile-friendly-testing-tool)、[2021-04-19 页面体验更新细节](https://developers.google.com/search/blog/2021/04/more-details-page-experience)、[2025-05-02 应用深度链接](https://developers.google.com/search/blog/2025/05/app-deep-links)、[文档更新记录](https://developers.google.com/search/updates)
- 标准与工具：[WCAG 2.2 SC 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)、[WCAG 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)、[web.dev 触摸目标](https://web.dev/articles/accessible-tap-targets)、[Lighthouse 节流](https://github.com/GoogleChrome/lighthouse/blob/main/docs/throttling.md)、[Lighthouse 12.0.0 发布说明](https://github.com/GoogleChrome/lighthouse/releases/tag/v12.0.0)、[Lighthouse 迁移到 insights](https://developer.chrome.com/blog/moving-lighthouse-to-insights)、[Firebase Dynamic Links FAQ](https://firebase.google.com/support/dynamic-links-faq)
- 未核项：iOS 输入框 16px 聚焦放大（无 Apple 一手文档）；Apple HIG 触控尺寸未引用。
