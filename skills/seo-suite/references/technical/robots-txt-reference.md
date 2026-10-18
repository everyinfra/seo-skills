# robots.txt 参考

> 涉及 AI 爬虫策略时，先读 [geo-evidence.md](../content/geo-evidence.md)。

## 用途

编写、审查 robots.txt，或排查 Search Console 里「被 robots.txt 屏蔽」「已编入索引，但被 robots.txt 屏蔽」时读。标准以 [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html) 为准，Google 的实现以 [Google 如何解析 robots.txt](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec) 为准（2025-11 起该文档迁到 developers.google.com/crawling）。其他爬虫的实现可能不同。核对 2026-10-18。

## 一、它管什么，不管什么

- **管抓取，不管索引。** 被禁止抓取的 URL 仍可能因为外部链接出现在搜索结果里，结果通常没有摘要（[robots.txt 入门](https://developers.google.com/search/docs/crawling-indexing/robots/intro)）。
- **不想被编入索引**：用 `noindex`（[meta robots 或 X-Robots-Tag](https://developers.google.com/search/docs/crawling-indexing/block-indexing)）。同一 URL 不能再用 robots.txt 禁止抓取，否则 Google 看不到 noindex。
- **不是访问控制。** RFC 9309 原文写明这些规则不是访问授权，还会把路径公开。敏感内容和测试环境用登录或服务器端访问控制。

## 二、文件与位置

- 文件放在每个主机的根目录，文件名全小写 `/robots.txt`。协议、主机、端口任一不同就是不同的站点；子域名要有自己的文件。
- 文件用 UTF-8 纯文本（`text/plain`）。Google 只处理前 500 KiB，超出部分忽略。
- 状态码的处理（Google）：

| 状态 | Google 怎么处理 |
|---|---|
| 2xx | 按文件内容解析。 |
| 3xx | 至少跟随 5 跳；仍拿不到文件就按 404 处理。不跟随 meta refresh、JavaScript 等逻辑重定向。 |
| 4xx（429 除外） | 视为没有 robots.txt，即没有抓取限制。 |
| 5xx、429、DNS 或网络错误 | 前 12 小时停止抓取全站，同时重试；之后最长 30 天沿用最后一次成功获取的版本；没有缓存版本就视为没有限制；30 天后仍失败，站点整体可用时按「没有 robots.txt」处理，整体不可用时停止抓取。 |

- 缓存：Google 一般缓存 robots.txt 最多 24 小时；拿不到新版本时会缓存更久；会参考 `Cache-Control: max-age`。改动不会立刻生效。

## 三、语法与匹配

- **组**：一行或多行 `User-agent`，后面跟 `Allow` / `Disallow` 规则。写在任何组之前的规则被忽略。
- **选组**：爬虫只遵守与自己名称最具体匹配的一组。有了专门的 `Googlebot` 组，Googlebot 就不再看 `*` 组。同一名称的多个组会合并成一组；专门组和 `*` 组不合并。组的先后顺序无关。
- **大小写**：字段名不区分大小写；`User-agent` 的值也不区分大小写；路径区分大小写。
- **匹配**：路径按前缀匹配；`*` 匹配任意字符序列，`$` 表示 URL 结尾。非 ASCII 字符按百分号编码比较，`/ツ` 与 `/%E3%83%84` 等价。
- **冲突**：路径最长（最具体）的规则优先。长度相同时，Google 用限制最少的规则；RFC 9309 规定此时应用 `Allow`。
- **Sitemap**：写完整 URL，可以有多行，不属于任何组，可以指向其他主机。
- **Google 只支持** `user-agent`、`allow`、`disallow`、`sitemap` 四个字段。Google 不支持 `crawl-delay`。写在 robots.txt 里的 `noindex` 自 2019-09-01 起不再生效（[Google 公告](https://developers.google.com/search/blog/2019/07/a-note-on-unsupported-rules-in-robotstxt)）。其他爬虫可能支持 `crawl-delay`，例如 Anthropic 官方说明支持。

| 规则 | 会匹配 | 不会匹配 |
|---|---|---|
| `Disallow: /shop` | `/shop`、`/shop/a`、`/shopping` | `/Shop` |
| `Disallow: /shop/` | `/shop/`、`/shop/a` | `/shop`、`/shopping` |
| `Disallow: /*.pdf$` | `/files/a.pdf` | `/files/a.pdf?v=2` |

## 四、常见错误

- 屏蔽了渲染所需的 CSS、JS 或图片，Google 渲染出的页面不完整。Google 不会渲染被屏蔽文件里的 JavaScript。
- 想「去索引」却用了 robots.txt。
- 以为 `Disallow: /admin` 只屏蔽目录，实际还会屏蔽 `/admin-guide` 这类前缀相同的路径。
- 测试环境的 `Disallow: /` 随上线一起带到了正式站。
- robots.txt 返回 5xx 或超时，前 12 小时全站停止抓取。
- 为某个爬虫单独建组后，忘了它不再遵守 `*` 组的规则，需要的规则要在该组里重写。
- 没评估就把参数页、分面页全部屏蔽：屏蔽后，这些 URL 上的 canonical 和 noindex 也不会被看到。做法见 [分面导航](https://developers.google.com/crawling/docs/faceted-navigation) 文档和 [redirects-canonical.md](redirects-canonical.md) 第五节。

## 五、AI 相关爬虫：分开决定

搜索 / 检索型、训练型、用户触发型爬虫的用途不同，分别决定，不要合并成一个开关。下表只列官方文档写明的内容（核对 2026-10-18）：

| 运营方 | robots.txt 名称 | 用途 | 官方说明的要点 | IP 列表 |
|---|---|---|---|---|
| Google | `Google-Extended` | 产品标记，没有单独的抓取 UA | 控制内容能否用于训练 Gemini 模型，以及 Gemini Apps 和 Vertex AI 的 grounding；不影响 Google 搜索收录和排名 | 无（沿用 Google 爬虫） |
| Google | `Googlebot` | 搜索抓取 | AI Overviews / AI Mode 的控制方式与普通搜索相同：robots.txt、`nosnippet`、`data-nosnippet`、`max-snippet`、`noindex` | [common-crawlers.json](https://developers.google.com/static/crawling/ipranges/common-crawlers.json) |
| OpenAI | `OAI-SearchBot` | ChatGPT 搜索 | 屏蔽后不出现在 ChatGPT 搜索答案中；robots.txt 改动约 24 小时生效 | [searchbot.json](https://openai.com/searchbot.json) |
| OpenAI | `GPTBot` | 训练 | 屏蔽表示内容不用于训练基础模型 | [gptbot.json](https://openai.com/gptbot.json) |
| OpenAI | `ChatGPT-User` | 用户触发的访问 | 由用户发起，robots.txt 规则可能不适用；不用于判断能否出现在搜索中 | [chatgpt-user.json](https://openai.com/chatgpt-user.json) |
| Anthropic | `ClaudeBot` / `Claude-SearchBot` / `Claude-User` | 训练 / 搜索 / 用户触发 | 三者分别控制；遵守 robots.txt，支持 `Crawl-delay`；靠封 IP 退出不可靠 | [bots.json](https://claude.com/crawling/bots.json)（三者共用） |
| Perplexity | `PerplexityBot` / `Perplexity-User` | 搜索 / 用户触发 | 各自独立设置，改动最长 24 小时生效 | [perplexitybot.json](https://www.perplexity.com/perplexitybot.json)、[perplexity-user.json](https://www.perplexity.com/perplexity-user.json) |

- 其他 AI 服务的名称、用途、是否遵守 robots.txt，以各家官方文档为准，不要从第三方汇总列表里抄。
- 本 Skill 不替用户一刀切地放开或封禁。列出每类爬虫的用途，以及放开或屏蔽对可见度、内容使用和服务器负载的影响，由用户决定。需要强制执行时配合服务器端规则，并按各家公布的方式（反向 DNS 或 IP 列表）核实爬虫真伪，方法见 [log-analysis.md](log-analysis.md) 二C。

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

- Search Console 的 [robots.txt 报告](https://support.google.com/webmasters/answer/6062598)只对网域级资源可用。它列出抓取量最高的 20 个主机的文件、抓取时间、解析问题和最近 30 天的版本，紧急时可以请求重新抓取。
- 单个 URL 是否被屏蔽：网址检查（URL Inspection）的「Crawl allowed?」。注意：被 robots.txt 屏蔽时，「Indexing allowed?」永远显示 Yes，因为 Google 看不到 noindex。
- 本地测试用 Google 开源的生产解析器 [google/robotstxt](https://github.com/google/robotstxt)。它不处理爬虫在解析之外的回退逻辑（例如 Googlebot-Image 在没有专门组时遵守 Googlebot 组）。
- 改动前后做 diff，列出新增屏蔽和新放开的路径；上线后监控文件内容和状态码（见 [alert-threshold-guide.md](../monitoring/alert-threshold-guide.md)）。

## 检查清单

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 文件可达 | 命令 1 | 通过：200、`text/plain`、小于 512000 字节；有意不设文件时 404 也通过。失败：5xx、429、超时，或超过 500 KiB |
| 2 | 重定向跳数 | 命令 2（输出行数减 1 = 跳数） | 通过：0–1 跳，终点 200。失败：超过 5 跳（Google 只保证跟 5 跳） |
| 3 | 每个主机和协议都有正确文件 | 对 `http`/`https` × apex/`www`/各子域逐个跑命令 1 | 失败：某个变体返回 5xx，或测试环境的规则出现在正式主机上 |
| 4 | 没有误伤的全站屏蔽 | 命令 3，列出含 `Disallow: /` 的组 | 通过：只列出用户明确决定屏蔽的爬虫。失败：出现 `*` 或 `Googlebot` |
| 5 | 关键 URL 与渲染资源可抓 | 命令 4（google/robotstxt），逐个测首页、主要模板页、CSS、JS、首屏图片 | 失败：任何一个返回 DISALLOWED |
| 6 | 没有用 robots.txt 去索引 | Search Console → 网页索引编制报告，看「已编入索引，但被 robots.txt 屏蔽」；抽样用网址检查看「Crawl allowed?」 | 失败：要去索引的页面同时被 robots.txt 屏蔽 |
| 7 | AI 爬虫姿态符合决定 | 命令 5，逐个对照用户的决定记录 | 失败：搜索型或用户触发型爬虫被误封，或训练型爬虫与用户决定不符 |
| 8 | 上线前后差异 | 命令 6 | 每一行差异都有对应的决定；没有遗留的 `Disallow: /` |

```bash
# 命令 1：状态码、类型、大小
curl -sS -o /tmp/robots.txt -w '%{http_code} %{content_type} %{size_download}\n' https://example.com/robots.txt

# 命令 2：重定向跳数
curl -sIL --max-redirs 10 https://example.com/robots.txt | grep -ciE '^HTTP/'

# 命令 3：列出含 Disallow: / 的组（同组多个 User-agent 用逗号连接；BSD/GNU awk 都能跑）
curl -s https://example.com/robots.txt | tr -d '\r' | awk '
  { l=$0; sub(/#.*/,"",l); gsub(/^[ \t]+|[ \t]+$/,"",l); if (l=="") next
    split(l,a,":"); k=tolower(a[1]); v=substr(l,index(l,":")+1); gsub(/^[ \t]+|[ \t]+$/,"",v) }
  k=="user-agent" { if (r) { u=""; r=0 }; u=u (u?",":"") v; next }
  k=="allow" || k=="disallow" { r=1; if (k=="disallow" && v=="/") print "全站屏蔽组: " u }'

# 命令 4：用 Google 生产解析器测单个 URL（先按 google/robotstxt 的 README 用 Bazel 或 CMake 编译）
robots_main /tmp/robots.txt Googlebot https://example.com/assets/app.js   # 退出码 0=ALLOWED，1=DISALLOWED

# 命令 5：AI 爬虫三层矩阵（训练 / 搜索 / 用户触发）
python3 scripts/robots_posture.py https://example.com/robots.txt --json

# 命令 6：测试环境与正式站对比
diff <(curl -s https://staging.example.com/robots.txt) <(curl -s https://example.com/robots.txt)
```

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。核对 2026-10-18。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/technical-seo-checker/references/robots-txt-reference.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/optimize/technical-seo-checker/references/robots-txt-reference.md)（Apache-2.0）
- 标准与 Google 实现：[RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html)、[Google 如何解析 robots.txt](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec)、[robots.txt 入门](https://developers.google.com/search/docs/crawling-indexing/robots/intro)、[用 noindex 阻止编入索引](https://developers.google.com/search/docs/crawling-indexing/block-indexing)、[robots.txt 不支持的规则（2019-07-02）](https://developers.google.com/search/blog/2019/07/a-note-on-unsupported-rules-in-robotstxt)、[robots.txt 报告](https://support.google.com/webmasters/answer/6062598)、[网址检查工具](https://support.google.com/webmasters/answer/9012289)、[google/robotstxt](https://github.com/google/robotstxt)
- AI 爬虫：[Google 常见抓取工具](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers)、[AI 功能与网站](https://developers.google.com/search/docs/appearance/ai-features)、[OpenAI 爬虫说明](https://platform.openai.com/docs/bots)、[Anthropic 爬虫说明](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)、[Perplexity 爬虫说明](https://docs.perplexity.ai/guides/bots)
- 爬虫导出里的「被 robots 屏蔽的资源」怎么读，见 [audit-tool-output.md](audit-tool-output.md)；爬虫工具的严重度阈值见 [ci-gates.md](../monitoring/ci-gates.md)。
