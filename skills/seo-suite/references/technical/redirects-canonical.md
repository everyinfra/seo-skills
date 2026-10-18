# 重定向与 Canonicalization 深度指南

> 2026-10-18 按 Google 现行文档逐条核对。分工（只引用不复述）：状态码语义、soft 404、迁移步骤见 [http-status-codes](http-status-codes.md)；C3 四变体 host、C8 canonical 双通道、C20 跳数等检查编号与 JS SEO 边界见 [validation-guide](validation-guide.md)；整站迁移清单见 [domain-strategy](../research/domain-strategy.md)；robots 屏蔽后 canonical / noindex 不可见的原理见 [robots-txt-reference](robots-txt-reference.md)；canonical 标签语法见 [head-elements](head-elements.md)；hreflang 细节见 [hreflang-validation](hreflang-validation.md)。

## 一、重定向全类型

### 1.1 五种 3xx 的用法边界

| 码 | HTTP 语义（RFC 9110） | Google 怎么用（[重定向文档](https://developers.google.com/search/docs/crawling-indexing/301-redirects)） | SEO 用途 |
|---|---|---|---|
| 301 | 永久移动；历史原因，客户端可能把 POST 改成 GET | 永久：目标应成为规范网址，结果显示新 URL | 永久改址、合并页面、http→https、www 统一 |
| 308 | 永久移动；不允许改请求方法 | 与 301 等同 | 同 301；表单 POST/PUT 端点迁移时才必需 |
| 302 | 临时；历史原因，客户端可能把 POST 改成 GET | 临时：不作为规范化信号，结果通常显示原 URL | 临时活动页、维护期临时指向 |
| 303 | 让客户端用 GET/HEAD 取另一个资源 | 按临时重定向处理 | POST 后跳到结果页；SEO 场景几乎不用 |
| 307 | 临时；不允许改请求方法 | 与 302 等同 | 临时跳转 API / 表单端点 |

判断口径（本套件）：意图讲清楚——永久用 301/308，临时用 302/307。「不确定就先 302 以后再改」是错的：302 期间结果里仍是原 URL。Bing 的口径更严：302 只用于很短期的变化（少于 2 天），永久改址用 301，并用重定向代替 canonical（[Bing Webmaster Guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)）。

### 1.2 HTTP / meta refresh / JS 三种实现

| 实现 | Google 的处理 | 定位 |
|---|---|---|
| HTTP 3xx + `Location` | 首次请求即见；Google 识别把握最高 | 首选 |
| meta refresh 或 `Refresh` 头 | 0 秒按永久，延迟按临时；需先下载 HTML | 无法改服务端时的兜底 |
| JS `window.location` | Google 按永久处理，但要在抓取完成后由渲染服务执行 | 最后手段；不是所有爬虫都执行 JS（[JS SEO 基础](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)） |

判定现状用哪种实现：curl 抓首个响应——3xx 是 HTTP 层；200 加 `http-equiv="refresh"` 是 meta；200、无标记、渲染后地址变化是 JS。报告里写明实现层：三层的修复位置不同（Nginx/CDN 规则、模板 head、前端代码）。

```bash
# 三层判定：状态码、meta refresh、JS 跳转特征
curl -sI https://example.com/old | head -5
curl -s https://example.com/old | grep -io 'http-equiv="refresh"[^>]*'
curl -s https://example.com/old | grep -ioE 'location\.(href|replace|assign)'
```

### 1.3 链式优化与循环检测

- **跳数分级**：Google 爬虫默认最多跟 10 跳，超过记「重定向错误」（[状态码文档](https://developers.google.com/crawling/docs/troubleshooting/http-status-codes)）。Google 迁移文档建议直达终点；做不到时链长最好不超过 3 跳，且少于 5 跳（[网站迁移](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)）。抓取预算文档说长链对抓取有负面影响。本套件内链口径 C20：≤1 跳。存量链目标：≤2 跳。
- 每多一跳：多一次往返延迟，多一次出错机会。
- **循环**：A→B→A、A→A 自指、跨 host 循环（https→http→https）。征兆：curl 跟到超时、Search Console「重定向错误」、日志里同一爬虫反复请求同一组 URL。
- 修复原则：改写**链首**直达终点，不要在链尾再补一跳；改完抽查历史高流量 URL 和 sitemap 里的全部 URL。

```bash
# 逐跳列出状态码与目标（HTTP 行数减 1 = 跳数）
curl -sIL --max-redirs 15 https://example.com/old | grep -iE '^(HTTP/|location:)'
# 套件脚本：链长、循环、301/302 混用、查询参数是否保留
python3 scripts/redirect_chain.py https://example.com/old --max 3
```

| 形态 | 例子 | 修法 |
|---|---|---|
| 历史叠加链 | A→B(2019)→C(2023)→D(2025) | 映射表把 A/B/C 全部直指 D |
| 协议串行 | http→https→www | 两条规则合并成一跳 |
| 链中夹 302 | 301→302→301 | 临时跳转替换为最终目标 |
| 尾斜杠 / 大小写链 | /Page→/page→/page/ | URL 规范化层一次输出最终形态 |

### 1.4 重定向映射表的维护（本套件口径）

- 字段至少：from URL、to URL（最终 200，不是中间跳）、状态码、上线日期、负责人或工单号、来源（迁移 / 合并 / 参数清理）。
- 新增映射走代码审核；不在映射表外临时加 301。
- 每季度用日志或脚本回放，确认每条 from 仍返回预期状态码。重定向一般至少保留一年（Google 迁移文档）。
- 同时维护 to→from 反向索引：页面再改版时，才知道哪些历史 URL 挂在它身上，避免链上加链。

```csv
from_url,to_url,code,shipped_at,owner,reason
/old-blog/post-1,/blog/post-1,301,2023-04-11,@infra,migration-v2
http://example.com/x,https://www.example.com/x,301,2021-08-02,@infra,host-unify
/products/discontinued,/products/category-a,301,2025-12-01,@ecom,sku-sunset
```

## 二、Canonicalization 六场景

Google 的规范化方法按影响力排序：重定向（强）、`rel="canonical"`（强）、sitemap 收录（弱）；几种方法叠加效果更好（[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)）。

### 2.1 www / 裸域

- 二选一定为规范 host，另一侧 301 过去，全站 canonical 对齐。两套都返回 200 = 外链分流、抓取分散。
- 上线前把 www/apex × http/https × 尾斜杠的变体全部一跳 301 到规范形态（[validation-guide](validation-guide.md) C3）。

### 2.2 http / https

- canonical、sitemap、hreflang 一律写 https；http→https 一跳直达规范 host。
- Google 默认优先 HTTPS 页做规范网址，但以下情况会改选 HTTP：证书无效；HTTPS 页含不安全依赖（图片除外）；HTTPS 跳到或经过 HTTP；HTTPS 页的 canonical 指向 HTTP。证书错误和 HTTPS→HTTP 跳转会让 Google 强烈偏向 HTTP，HSTS 也压不住（[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)）。
- 所以审计 HTTPS 页时要查混合内容（`http://` 的脚本、样式、iframe），证书要覆盖完整主机名或用通配证书。

### 2.3 参数 URL

- canonical 指向去参后的清洁版：跟踪参数（utm、gclid 等）、会话 ID、排序参数、打印视图。
- 例外：参数页本身有独立搜索需求（如 `?color=red`）→ 自引用 canonical。依据是 Search Console 的查询数据，不是直觉（本套件口径）。
- 同一页面不要用不同方法声明不同的 canonical（例如 sitemap 写一个，`rel="canonical"` 写另一个）；canonical 不要带片段（`#`）。

### 2.4 分页

- **每页自引用 canonical**：Google 分页文档写明「不要把第一页设为分页序列的 canonical，给每页自己的 canonical」（[分页最佳做法](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading)）。
- 每页用 `<a href>` 链到下一页；可以从各页链回第一页，提示第一页更适合当落地页。
- 每页一个唯一 URL（如 `?page=n`）；页码不要放在片段（`#`）里，Google 会忽略片段。
- 筛选、排序产生的同一列表变体：用 noindex，或用 robots.txt 阻止抓取这类 URL 模式。

### 2.5 分面组合页

结论先行（决策树见第五节）：不需要被索引的分面 URL → 阻止抓取；需要被索引的 → 按 Google 的分面 URL 规范实现。被 robots.txt 屏蔽的页上的 canonical 读不到，所以「屏蔽」和「用 canonical 收编」不能同时用在一个 URL 上。

### 2.6 跨域转载（syndication）

- Google 现行口径：**不推荐**用 canonical 防止转载伙伴造成重复，因为转载页往往差别很大；最有效的办法是让伙伴**阻止对转载内容编入索引**（noindex）（[规范化问题排查](https://developers.google.com/search/docs/crawling-indexing/canonicalization-troubleshooting)，同文链到 Google 新闻《避免文章重复》）。
- 内容源头：自引用 canonical，先发布，sitemap 及时更新。

| 角色 | 做法 |
|---|---|
| 内容源头（自己） | 自引用 canonical；先发布；sitemap 及时更新 |
| 可控的转载伙伴 | 在转载页加 noindex；保留指向原文的可见链接 |
| 不可控的抓取 / 洗稿站 | 加不了标记；原文被反超时按版权走 DMCA 投诉（Google 规范化排查文档提到此途径） |

- 多域同内容又没有 canonical 归属，是套件红线 R4（见 [validation-guide](validation-guide.md)）。

## 三、canonical 与 noindex / robots / hreflang 的交互（冲突矩阵）

| 组合 | 结果 | 判定与处理 | 依据 |
|---|---|---|---|
| canonical + noindex 同页 | 矛盾 | Google 不建议用 noindex 控制站内规范网址的选择，因为它会把页面整个挡出搜索。拆开用：canonical 收编重复，noindex 剔除垃圾页 | 官方 |
| noindex, follow | 短期可用 | Google 员工 2017 年说长期 noindex 最终等同 noindex, nofollow；不要当长期策略 | 第三方转述（[SER 2017-12-28](https://www.seroundtable.com/google-long-term-noindex-follow-24990.html)） |
| sitemap 写的 URL 与 `rel="canonical"` 不一致 | 信号矛盾 | sitemap 只放规范网址；Search Console 会出现「重复网页，Google 选择的规范网页与用户指定的不同」 | 官方 |
| canonical 指向被 robots 屏蔽的页 | 目标内容不可见 | 不要用 robots.txt 做规范化 | 官方原则 + 本套件推论 |
| canonical + hreflang 同页 | 需同语言 | 用 hreflang 时，canonical 要指向同语言页（没有同语言页时指向最接近的替代语言）；簇内每页自引用 canonical | 官方 |
| canonical 与 301 指向不同目标 | 两个强信号互相打架 | 以 301 终点为准对齐 canonical | 本套件口径 |
| canonical 指向 404/410 或重定向页 | 指向无效或中间页 | canonical 写最终返回 200 的 URL | 本套件口径 |
| `<link>` 与 `Link:` 响应头同时声明 | 更容易出错 | Google 建议二选一；两处值不同时信号矛盾（C8 双通道检查） | 官方 |
| 原始 HTML 与 JS 写的 canonical 不一致 | 规范化在渲染前后都会发生 | JS 不要把 canonical 改成别的值；HTML 里写不了时，HTML 里干脆不写，只用 JS 设置 | 官方（2025-12-17 更新） |

> 补记（本套件口径）：canonical 指向 noindex 页同样无效——目标页自己不在索引里，无法代表整组。

## 四、分页、无限滚动与 Search Console 观察

- **rel=prev/next**：Google 2011 年发布该标记的博客文章顶部现已注明「它不再是索引信号」。2019-03 Google 在官方社交账号公开此事（第三方报道：[Yoast 2019-03-22](https://yoast.com/google-doesnt-use-rel-prev-next-for-pagination/)）。已部署的保留无害，不再新增。
- **无限滚动**：每块内容要有持久、唯一的 URL（用绝对页码，如 `?page=12`，不用 `?date=yesterday`）；按顺序链接各 URL；新块成为主要可见内容时，用 History API 更新地址栏（[懒加载文档](https://developers.google.com/search/docs/crawling-indexing/javascript/lazy-loading)）。只靠「加载更多」按钮的内容，Google 发现不了：它不点击按钮。
- **sitemap 策略**（本套件口径）：sitemap 是「希望出现在结果里的页面清单」。第 1 页和高价值组合页进 sitemap；第 2 页以后可以只靠内链发现。
- **分页 URL 形态**：`?page=2` 与 `/page/2/` 只留一种做规范形态，另一种 301 过去。`page` 是参数白名单里最典型的合法成员，参数清理时别误伤。
- **搜索引擎侧的参数工具已没有**：Search Console 的 URL 参数工具 2022-03-28 宣布一个月后下线，Google 当时说只有约 1% 的配置对抓取有用（[公告](https://developers.google.com/search/blog/2022/03/url-parameters-tool-deprecated)）。参数治理只能在站内做（robots.txt、canonical、noindex、白名单）。
- **现行观察口径**：网页索引编制报告的「重复网页」类原因；网址检查里「用户声明的规范网址」与「Google 选择的规范网址」（API 字段 `userCanonical` / `googleCanonical`）。修正内容后，Google 可能把页面在重复簇里保留最多两周再重新评估（[规范化问题排查](https://developers.google.com/search/docs/crawling-indexing/canonicalization-troubleshooting)）。

## 五、参数与分面治理

### 5.1 组合爆炸的量级

10 个分面、每个分面 5 个取值、每个分面单选或不选，URL 空间就是 6^10 ≈ 6,000 万个组合；允许多选时是 (2^5)^10 ≈ 10^15。任何「全部留索引 / 全部自引用」的策略在这个量级前都失效，必须分层。

### 5.2 决策：阻止抓取、canonical 还是 noindex

Google 的分面导航文档给两条路（[分面导航](https://developers.google.com/crawling/docs/faceted-navigation)）：

| 情况 | Google 推荐的做法 | 补充 |
|---|---|---|
| 不需要分面 URL 被索引 | 用 robots.txt 禁止抓取分面参数；或者把筛选条件放进 URL 片段（`#`），片段对抓取没有影响 | 只开放单品页和一个不带筛选的完整列表页 |
| 需要分面 URL 被索引 | 参数分隔符用标准的 `&`；路径式分面保持固定顺序、不允许重复；没有结果的组合返回 404，不跳到统一的「未找到」页 | 程序化质量门槛见 [programmatic-seo-gates](programmatic-seo-gates.md) |
| 只能做弱处理时 | `rel="canonical"` 指向不带筛选的版本，或给指向筛选页的所有链接加 `rel="nofollow"` | 官方说这两种长期效果不如前两种；nofollow 要覆盖全部指向该 URL 的链接 |

noindex 的位置（本套件口径）：只用于「已进索引但确定不要」的存量页短期清理。noindex 要先被抓到才生效；页数很大时，用它反而先消耗抓取。

### 5.3 参数白名单（本套件口径）

- 维护一份**允许出现在可索引 URL 里的参数清单**。清单外的参数：内链不生成，canonical 去除，日志监控出现率。
- 模板层禁止拼接白名单外的查询串（与 C29 URL 卫生口径衔接，见 [validation-guide](validation-guide.md)）。

| 参数 | 类别 | 处理 |
|---|---|---|
| `page`、`p` | 分页 | 白名单；进规范 URL |
| `category`、`color`（有搜索需求） | 分面 | 白名单；按 5.2「需要被索引」实现 |
| `sort`、`order`、`dir` | 排序 | 不进规范 URL；可用 robots.txt 阻止抓取 |
| `utm_*`、`gclid`、`fbclid`、`ref` | 跟踪 | 输出前剥除；canonical 里永远不出现 |
| `sessionid`、`sid` | 会话 | 改用 cookie，不进 URL |
| `print=1`、`view=mobile` | 变体视图 | canonical 到标准版 |

- 分面交互的工程约束：每次点击只叠加一个分面；取值排序固定（同一组合只产生一个 URL）；面包屑只回链基页。

## 六、审计操作

### 6.1 重定向审计：日志法

1. 从服务器或 CDN 日志里筛出 Googlebot，并按反向 DNS 或官方 IP 列表核实真伪（[log-analysis](log-analysis.md) 二C）。
2. 统计 3xx 占已验证 Googlebot 请求的比例。本套件口径：持续高于 10% 就该清理跳转。
3. 对每条 3xx 跟到底，重建完整链（命令见 1.3）。
4. 用 Search Console 抓取统计的「按响应」分组核对；差异大时，多半是 CDN/WAF 按 UA 分叉。
5. 迁移后按日期切片，对比改址前后旧 URL 的 3xx 抓取量衰减与新 URL 的抓取增长。

```bash
# combined 日志：Googlebot 收到 3xx 的路径排行（UA 在第 6 个引号字段，状态码在第 3 个引号字段的开头）
awk -F'"' '$6 ~ /Googlebot/ {split($3, s, " "); if (s[1] ~ /^30/) {split($2, r, " "); print s[1], r[2]}}' access.log \
  | sort | uniq -c | sort -rn | head -30
```

### 6.2 canonical 一致性检查清单

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 每页有且只有一个 canonical，`<link>` 与 `Link:` 头一致 | 命令 A | 失败：0 个或多个；两处值不同 |
| 2 | canonical 是绝对 URL，协议和 host 与规范 host 一致 | 命令 A 的输出 | 失败：相对路径、http、非规范 host |
| 3 | canonical 目标返回 200，不重定向、不 404 | 命令 B | 失败：目标是 3xx/4xx/5xx |
| 4 | 每一处「canonical ≠ 自身」都能对应 2.2–2.6 的某个场景 | 爬虫导出（如 Screaming Frog 的 `Canonical Link Element 1` 列）逐行对照 | 失败：说不出理由的跨页 canonical |
| 5 | 分页每页自引用 | 抽查 `?page=2`、`?page=3` | 失败：指向第 1 页 |
| 6 | sitemap 里的 URL 全部自引用 | `python3 scripts/sitemap_audit.py https://example.com --check-limit 0` 后抽查；Search Console「Google 选择的规范网页与用户指定的不同」 | 失败：sitemap URL 的 canonical 指向别处 |
| 7 | 没有 noindex 与 canonical 同页叠加 | 命令 A 同时取 `robots` meta 和 `X-Robots-Tag` | 失败：同页两者并存 |
| 8 | hreflang 簇的 canonical 全部自引用 | `python3 scripts/hreflang_cluster.py <全部语言版 URL>` | 失败：某语言版 canonical 指向其他语言 |
| 9 | Google 采纳了声明的 canonical | 网址检查：「Google 选择的规范网址」=「用户声明的规范网址」 | 不一致：查内链、外链、sitemap、重定向四处是否各说各话 |

```bash
# 命令 A：取响应头和 HTML 里的 canonical 与 robots
u='https://example.com/page?page=2'
curl -sD /tmp/h.txt "$u" -o /tmp/body.html
grep -i '^link:.*rel="\?canonical' /tmp/h.txt; grep -i '^x-robots-tag' /tmp/h.txt
grep -ioE '<link[^>]+rel="?canonical"?[^>]*>' /tmp/body.html
grep -ioE '<meta[^>]+name="?robots"?[^>]*>' /tmp/body.html

# 命令 B：canonical 目标的状态码（应为 200，且无跳转）
c=$(grep -ioE '<link[^>]+rel="?canonical"?[^>]*>' /tmp/body.html | grep -oE 'href="[^"]+"' | head -1 | cut -d'"' -f2)
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' "$c"
```

### 6.3 修复优先级（本套件口径）

1. 循环重定向与 ≥3 跳的链。
2. canonical 指向 404、重定向页、被屏蔽页。
3. canonical + noindex 叠加；`<link>` 与 `Link:` 头不一致。
4. 分页 canonical 到第 1 页；参数页没有 canonical。
5. 2 跳链优化到 1 跳。

## 常见误区

- 「第 2 页以后 canonical 到第 1 页防重复」：Google 分页文档明确说不要这样做。
- 「robots.txt 屏蔽 + canonical 双保险」：屏蔽后 canonical 读不到，双保险变零保险。
- 「noindex 一下再 canonical 回来」：两种信号同页互相矛盾，Google 不建议。
- 「转载方加跨域 canonical 就够了」：Google 现行建议是让转载方 noindex。
- 「301 会损失权重」：Google 迁移文档说永久重定向不会造成 PageRank 损失。另一回事：买过期域名、再利用它操纵排名，属于 Google 垃圾内容政策的「过期域名滥用」（2024-03 新增）。
- 「等 Search Console 的参数工具」：该工具 2022 年已下线。
- 「meta refresh 0 秒等于 301」：Google 按永久处理，但要先下载 HTML；其他爬虫不一定跟。不能替代服务端 3xx。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。核对 2026-10-18。

- Google：[规范网址](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)、[规范化问题排查](https://developers.google.com/search/docs/crawling-indexing/canonicalization-troubleshooting)、[重定向](https://developers.google.com/search/docs/crawling-indexing/301-redirects)、[HTTP 状态码对抓取的影响](https://developers.google.com/crawling/docs/troubleshooting/http-status-codes)、[网站迁移](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)、[分面导航](https://developers.google.com/crawling/docs/faceted-navigation)、[分页最佳做法](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading)、[懒加载与无限滚动](https://developers.google.com/search/docs/crawling-indexing/javascript/lazy-loading)、[JS SEO 基础](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)、[文档更新记录](https://developers.google.com/search/updates)、[URL 参数工具下线](https://developers.google.com/search/blog/2022/03/url-parameters-tool-deprecated)、[rel=next/prev 原文（含注记）](https://developers.google.com/search/blog/2011/09/pagination-with-relnext-and-relprev)
- 标准与其他引擎：[RFC 9110 §15.4](https://www.rfc-editor.org/rfc/rfc9110.html#name-redirection-3xx)、[Bing Webmaster Guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)
- 第三方（只作转述）：[SER 2017-12-28（长期 noindex）](https://www.seroundtable.com/google-long-term-noindex-follow-24990.html)、[Yoast 2019-03-22（rel=prev/next）](https://yoast.com/google-doesnt-use-rel-prev-next-for-pagination/)
