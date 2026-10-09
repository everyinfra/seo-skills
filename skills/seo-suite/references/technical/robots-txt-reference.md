# robots.txt 参考

> 涉及 AI 爬虫策略时，先读 [geo-evidence.md](../content/geo-evidence.md)。

## 用途

编写、审查 robots.txt，或排查 Search Console 里「被 robots.txt 屏蔽」「已编入索引，但被 robots.txt 屏蔽」时读。以 [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309) 和 [Google 如何解析 robots.txt](https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt) 为准，其他爬虫的实现可能不同。

## 一、它管什么，不管什么

- **管抓取，不管索引。** 被禁止抓取的 URL，仍可能因为外部链接出现在搜索结果里（通常没有摘要）。
- **不想被编入索引**：用 `noindex`（[meta robots 或 X-Robots-Tag](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)），而且不能同时用 robots.txt 禁止抓取，否则爬虫看不到 noindex。
- **不是访问控制**：它只是声明，不守规矩的爬虫可以无视。敏感内容和测试环境用登录或服务器端访问控制。

## 二、文件与位置

- 放在每个主机的根目录。协议、主机、端口不同就是不同的站点，子域名要有自己的文件。
- UTF-8 纯文本；Google 只处理前 500 KiB。
- 文件本身的状态码（Google 的处理）：2xx 正常解析；4xx（429 除外）视为没有任何限制；5xx 和 429 暂时视为整站禁止抓取；重定向只跟随有限次数。Google 一般会缓存 robots.txt 最多 24 小时，改动不会立刻生效。

## 三、语法与匹配

- **组**：一行或多行 `User-agent`，后面跟 `Allow` / `Disallow` 规则。爬虫只遵守与自己名称最匹配的那一组：一旦有了专门的 `Googlebot` 组，Googlebot 就不再看 `*` 组。
- **大小写**：字段名不区分大小写，路径区分大小写。
- **匹配**：路径按前缀匹配；`*` 匹配任意字符序列，`$` 表示 URL 结尾。
- **冲突**：匹配字符最长（最具体）的规则优先；一样长时，Google 采用限制较少的 `Allow`。`Allow` 已写进 RFC 9309。
- **Sitemap**：写绝对 URL，可以有多行，不属于任何组。
- **Google 不支持**：`crawl-delay`，以及写在 robots.txt 里的 `noindex`。

| 规则 | 会匹配 | 不会匹配 |
|---|---|---|
| `Disallow: /shop` | `/shop`、`/shop/a`、`/shopping` | `/Shop` |
| `Disallow: /shop/` | `/shop/`、`/shop/a` | `/shop`、`/shopping` |
| `Disallow: /*.pdf$` | `/files/a.pdf` | `/files/a.pdf?v=2` |

## 四、常见错误

- 屏蔽了渲染所需的 CSS、JS 或图片，Google 渲染出的页面不完整。
- 想「去索引」却用了 robots.txt。
- 以为 `Disallow: /admin` 只屏蔽目录，实际还会屏蔽 `/admin-guide` 这类前缀相同的路径。
- 测试环境的 `Disallow: /` 随上线一起带到了正式站。
- robots.txt 返回 5xx，相当于暂时整站禁止抓取。
- 为某个爬虫单独建组后，忘了它不再遵守 `*` 组的规则，需要的规则要在该组里重写。
- 没评估就把参数页、分面页全部屏蔽：屏蔽后，这些 URL 上的 canonical 和 noindex 也不会被看到。做法见[分面导航](https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation)文档。

## 五、AI 相关爬虫：分开决定

- 搜索 / 检索型、训练型、用户触发型爬虫的用途不同，分别决定，不要合并成一个开关。
- **Google**：`Google-Extended` 是只在 robots.txt 里使用的产品标记，用来控制 Google 抓取的内容能否用于 Gemini 模型的训练和 grounding 等用途（范围以 [Google 常见抓取工具](https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers)文档为准），不影响网站在 Google 搜索中的收录和排名。Google 搜索里的 AI 功能沿用普通搜索的控制方式（noindex、nosnippet 等），见 [AI 功能与网站](https://developers.google.com/search/docs/appearance/ai-features)。
- **OpenAI**：其[爬虫说明](https://platform.openai.com/docs/bots)列出了 `OAI-SearchBot`、`GPTBot`、`ChatGPT-User` 等，用途不同，可以分别设置；各自用途和是否遵守 robots.txt 以该文档为准。
- **其他 AI 服务**：user-agent 名称、用途、是否遵守 robots.txt，以各家官方文档为准，不要从第三方汇总列表里抄。
- 本 Skill 不替用户一刀切地放开或封禁。列出每类爬虫的用途，以及放开或屏蔽对可见度、内容使用和服务器负载的影响，由用户决定。需要强制执行时配合服务器端规则，并按各家公布的方式（反向 DNS 或 IP 列表）核实爬虫真伪。

## 六、最小示例（自写，仅示意）

```text
User-agent: *
Disallow: /cart/
Disallow: /search
Allow: /search/help

# 用户决定不允许 GPTBot 抓取；GPTBot 只看这一组
User-agent: GPTBot
Disallow: /

Sitemap: https://example.com/sitemap.xml
```

## 七、测试与上线

- 在 Search Console 的 robots.txt 报告里（需要该站点的权限）看 Google 抓到的版本、抓取时间和错误；用网址检查确认某个 URL 是否被屏蔽。
- 本地可以用遵循 RFC 9309 的解析库测试，例如 Google 开源的 [robotstxt](https://github.com/google/robotstxt)。
- 改动前后做 diff，列出新增屏蔽和新放开的路径；上线后监控文件内容和状态码（见 [alert-threshold-guide.md](../monitoring/alert-threshold-guide.md)）。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/technical-seo-checker/references/robots-txt-reference.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/optimize/technical-seo-checker/references/robots-txt-reference.md)（Apache-2.0）
- 一手资料：[robots.txt 入门](https://developers.google.com/search/docs/crawling-indexing/robots/intro)、[Google 如何解析 robots.txt](https://developers.google.com/search/docs/crawling-indexing/robots/robots_txt)、[RFC 9309](https://www.rfc-editor.org/rfc/rfc9309)、[robots meta / X-Robots-Tag](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)、[阻止编入索引](https://developers.google.com/search/docs/crawling-indexing/block-indexing)、[Google 常见抓取工具](https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers)、[OpenAI 爬虫说明](https://platform.openai.com/docs/bots)、[AI 功能与网站](https://developers.google.com/search/docs/appearance/ai-features)

## 抓取边界与连通层审计口径 (siteone-crawler 源码深读 2026-10-09b)

> 来源：[janreges/siteone-crawler](https://github.com/janreges/siteone-crawler)（Rust，MIT）`src/analysis/` 各分析器逐行深读。这是工具判定口径，不是 Google 官方规则；引用时标"爬虫审计工具阈值"。安全头/缓存/状态码分级见 [http-status-codes.md](http-status-codes.md) 同日节，性能与 HTML 质量阈值见 [validation-guide.md](validation-guide.md) 同日节。

### 被跳过 URL 的归因（SkippedUrlsAnalyzer）

- 跳过原因三分类：`Not allowed host`（外链域名）/ `Robots.txt` / `Max depth`；汇总表按"原因×域名"计数降序。
- 每条被跳过 URL 记录**来源属性**（发现它的位置）：5=初始 URL、10=`<a href>`、20/21=`<img src/srcset>`、22=`<input src>`、23/24/25=`<source/video/audio src>`、30=`<script src>`、40=内联 script、50=`<link href>`、60=CSS `url()`、70=JS url、80=重定向、90=sitemap。
- **排查"robots.txt 屏蔽了渲染资源"**（本文第四节第 1 条错误）的直接证据链：过滤 `reason=Robots.txt` 且 `sourceAttr` ∈ {50, 60, 30} 的行 → 这些正是 CSS/JS 被禁抓的页面级证据，比逐页猜测快得多。
- 站点级分级：0 条=OK / 1–2 / 3–9 / ≥10 逐级升档（仅计数提示，无 SEO 含义）。

### DNS（DnsAnalyzer）

- 解析链：先查 CNAME 链（去尾点去重），再查 A（IPv4）与 AAAA（IPv6）记录；**A 与 AAAA 全空才算解析失败（critical）**。
- 无 IPv4 或无 IPv6 各自只是 **notice**（"domain does not support IPv4/IPv6"）——单栈站点是合规状态，不要在报告里当缺陷；CNAME 链>1 条仅记 info。
- IP 字面量主机（`127.0.0.1`、`[::1]`）直接跳过 DNS 查询（等超时纯浪费）；系统 DNS 服务器取自 `/etc/resolv.conf` 首个 nameserver（Windows 上没有则省略该后缀）。

### 响应头清单（HeadersAnalyzer）

- 全站响应头按小写名聚合：出现次数、唯一值数（上限截断显示 `N+`）、值预览（120 字符）、min/max。
- 站点级分级：唯一响应头 ≤30 正常 / 31–40 正常 / **41–50 已标 "too many"** / ≥51 "too many"——头过多常暗示多层代理/框架堆叠各加自己的头。
- `content-length` 的 min/max 按字节格式化、`age` 按时长格式化——**age 的 min/max 漂移是 CDN 缓存命中不稳定的信号**；只统计允许抓取域名的响应。

### 外链发现（ExternalLinksAnalyzer）

- 外链=跳过原因为 `Not allowed host` 的 URL（即域名不在允许清单，而非"绝对不允许"）；按目标 URL 分组，计数去重的来源页，最多展示 5 个来源页（`(+N)` 折叠）。
- 输出按"引用页数降序→URL 升序"——排前面的外链是真实的权重出口，审计外链质量时优先看。

### 技术栈被动指纹（TechnologiesAnalyzer）

- 纯被动：只用爬取已下载的**响应头、Set-Cookie 名（不含值）、`<meta name>` content、`<script src>`、HTML 标记**（含注释，如 Yoast 的 SEO 注释）；不发任何额外请求。100+ 自维护签名（`technologies/signatures.json`），11 个类目：Server/CDN/WAF/Hosting/CMS/E-commerce/后端框架/前端框架/JS 库/分析与标签管理/字体 UI。
- 版本号取自签名正则的捕获组（如 `server: nginx/1.25.3` → 1.25.3；`meta generator` → WordPress 6.5.2）；同页多版本全部保留（`1.12.4, 3.7.1`），版本按数字分量排序（9.1.0 < 10.0.0）。
- 防误报细节：`Apache-Coyote` 判 Tomcat 不判 Apache HTTP Server；注释/`<textarea>` 文本/自定义元素（`<script-widget>`）里的标记不算；资产与 3xx 响应不计入"Pages"（只数本站 HTML 页）。
- 防泄密细节：**cookie 值与 script URL 查询串永不进证据列**（避免把 session/GTM 密钥写进报告）；空表文案刻意不断言"没有 WAF/CDN"——被动检测证明不了不存在。
- 审计用途：与 Server/X-Powered-By 暴露版本（安全 critical，见 http-status-codes.md）交叉——同一份数据既是指纹面也是攻击面。
