# llms.txt 指南：证据状态、格式、校验与生成

> 建立于 2026-10-09；2026-10-21 对照官方文档、提案原文、Lighthouse 源码和各研究原文重新核对。
> llms.txt 是给 AI 代理的内容地图，不是收录开关，也不是引用保证。没有任何搜索或回答引擎公开承诺「有 llms.txt 就优先引用」。
> 先读 [geo-evidence.md](geo-evidence.md)（仲裁）。格式部分以 [llmstxt.org](https://llmstxt.org/)（v2，2026-08）为准；校验严重度、行数和词数等是第三方仓库或本套件口径，已逐项标明。

## 一、谁读、谁不读（核对 2026-10-21）

| 对象 | 说法 | 来源 |
|---|---|---|
| Google Search | 不使用，既不帮助也不损害。原话：「Google Search itself doesn't use them」「as Google Search ignores them」 | [生成式 AI 优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)（2026-07-10 更新）；2026-06-15 文档更新记录 |
| Google 员工 | Mueller 在 Bluesky（2025-06-17）：「FWIW no AI system currently uses llms.txt」；在 Reddit（2025-04）称它「comparable to the keywords meta tag」；2026-05 又说它「not done for search」，是给 AI 编码工具省 token 的「temporary crutch」。Illyes 在 2025-07 Search Central Live 说 Google 不支持、没有计划（只有听众转述） | 引文转引自 [Ahrefs](https://ahrefs.com/blog/llmstxt-study/)、[arrivl.ai](https://arrivl.ai/blog/does-anything-fetch-your-llms-txt)、[SEL](https://searchengineland.com/google-says-normal-seo-works-for-ranking-in-ai-overviews-and-llms-txt-wont-be-used-459422)；原帖本组未直接打开 |
| Chrome Lighthouse | 实验性「Agentic Browsing」审计里有 llms.txt 检查：服务器出错时标记，404 记为 N/A，因为文件「optional at the moment」 | [Lighthouse 文档](https://developer.chrome.com/docs/lighthouse/agentic-browsing/llms-txt)（2026-05-05）；源码 `core/audits/agentic/llms-txt.js` |
| OpenAI、Anthropic、Perplexity、Apple、Amazon、Meta、Mistral、Bing | 各家爬虫文档和 Bing 指南都没有提 llms.txt 的读取（本组逐页搜过）。OpenAI、Anthropic、Gemini 为自家开发者文档发布了 llms.txt，这只说明它们发布，不说明它们的爬虫读别人的 | [OpenAI](https://platform.openai.com/docs/bots)、[Anthropic](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler)、[llmstxt.org](https://llmstxt.org/) 背景节 |
| AI 编码代理 | 有实际读取：Ahrefs 日志研究里，读 llms.txt 的命名 AI 工具中 GPTBot 第一、Claude-Code 第二；Vercel 与 ora.ai 的 1,033 次代理运行里，代理主要经页面链接到达 llms.txt（86%）。Cursor 在 2025-06 仍有「不支持 llms.txt」的功能请求，现状未核 | [Ahrefs](https://ahrefs.com/blog/llmstxt-study/)、[Vercel](https://vercel.com/kb/guide/make-your-site-readable-by-ai-agents)、[Cursor 论坛](https://forum.cursor.com/t/cursor-not-support-llms-txt-standard/108980) |

结论（本套件口径）：开发者文档站可以发布 llms.txt，服务读它的代理；其他商业站把它当零成本的期权，不写进 GEO 收益预测，不在报告里给它引用权重。

## 二、实测数据（第三方研究，写明样本）

| 研究 | 结果 | 样本与限定 |
|---|---|---|
| [Ahrefs](https://ahrefs.com/blog/llmstxt-study/)（2026-06-15） | 28% 的域发布 llms.txt；其中 97% 在 2026-05 零请求；到达的请求 96% 来自 bot，77% 的 bot 不是 AI 工具；不存在的文件从未被 AI bot 请求；Lighthouse 约占 1/1000 | 137,210 个 Ahrefs Web Analytics 域，用户偏技术和 SEO，28% 是上界 |
| [OtterlyAI](https://otterly.ai/blog/the-llms-txt-experiment/)（2026-02-05） | 90 天内 62,100+ 次 AI bot 访问，只有 84 次（0.1%）请求 llms.txt | 一个实验站点 |
| [SE Ranking](https://seranking.com/blog/llms-txt/) | 约 30 万个域，10.13% 有 llms.txt；统计和机器学习都没发现它与 AI 引用频率相关 | 观察数据 |
| [arrivl.ai](https://arrivl.ai/blog/does-anything-fetch-your-llms-txt)（2026-09） | 39 个中小商业站、46 天，具名 AI 代理共请求 100 次；Cloudflare 验证的请求里 GPTBot、OAI-SearchBot、ClaudeBot、Claude-User 为零 | 小样本，厂商自测 |
| [Vercel + ora.ai](https://vercel.com/kb/guide/make-your-site-readable-by-ai-agents)（2026-06~08） | 对照探针：llms.txt、JSON-LD、sitemap 都没有改变「答案已在服务端渲染 HTML 里」时的取回结果；运行里 14% 的有据答案追溯到 llms.txt | 25 个站、1,033 次运行，6 个站占 66.9% |
| [Rankability](https://www.rankability.com/data/llms-txt-adoption/)、[Web Almanac 2025](https://almanac.httparchive.org/en/2025/seo) | 采用率：前 1,000 域 9.3%；有效文件 2.1%（见 [geo-evidence-bank.md](geo-evidence-bank.md)） | 方法各异，不连续 |

## 三、格式规范

提案原文（[llmstxt.org](https://llmstxt.org/)）规定：

- 文件名 `llms.txt`，放根路径或任一子路径；文件覆盖其路径下的页面，多个文件适用时用最具体的那个。
- 按顺序：可选 BOM → **H1（唯一必需项）** → 可选 blockquote 摘要 → 可选正文段（除标题外） → 零个或多个以 H2 分节的文件列表。
- 文件列表是 Markdown 列表，每项必须有链接 `[名称](url)`，可加 `:` 和说明。
- 名为 `Optional` 的节是次要链接的约定；v2 起它不再有机械语义（原来告诉上下文展开工具省略什么）。
- v2 建议每页提供同 URL 的 Markdown 版（`page.html.md` 或 `page.md`；无文件名的 URL 用 `index.html.md` 或 `index.md`），并用 `<link rel="alternate" type="text/markdown">` 指向它、`<link rel="describedby">` 指向覆盖它的 llms.txt；也可以用 HTTP `Link:` 头。
- 官方解析器的链接行正则：`-\s*\[(?P<title>[^\]]+)\]\((?P<url>[^\)]+)\)(?::\s*(?P<desc>.*))?`（[AnswerDotAI/llms-txt](https://github.com/AnswerDotAI/llms-txt) `miniparse.py`）。

提案没有定义根路径的 `llms-full.txt`。它来自实践：Cloudflare、Anthropic、Perplexity 为自家文档发布了它。

**本套件的写法约定**（来自 [geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) `geo-llmstxt` 的建议，不是规范）：

```
# 站点名称                     ← H1，官方业务名

> 一句话描述，事实性，不带推销语，200 字符以内

## Docs
- [页面标题](https://example.com/absolute/url): 该页内容，10–30 词
## Key Facts                   ← 成立年 / 总部 / 关键产品
## Contact
```

1. 链接用绝对 URL。
2. 条目说明 10–30 词，具体（「含代码示例的 React Server Components 完整指南」好过「React 指南」）。
3. 总量 10–30 条，区内按重要性降序；整体 50–150 行、3–6 个分区。
4. 文件小到能放进上下文；细节放在链接后面（提案 v2 的消费模型）。

## 四、校验严重度（本套件口径）

| 检查 | 严重度 |
|---|---|
| 缺 H1 或没有任何 H2 分区 | Critical |
| 条目少于 5 条 / 相对 URL / 说明超过 200 字符 | High |
| 缺 Key Facts / Markdown 语法破损 | Medium |
| 超过 200 行 / 缺 Contact | Low |

- 提案只要求 H1。「必须有 blockquote 和 H2 分区」是本套件对商业站的要求，因为没有它们代理拿不到导览。
- 判定「存在」看状态码和内容类型，不看响应体积：定制 404 页也会返回几十 KB 的 HTML。`llmstxt.py check` 会把 HTML 响应标成 FAIL。
- 状态码处理：200 校验；404 生成；403 标配置错误（可能是权限问题）；301/302 跟随后注记。
- Lighthouse 源码（2026-10-21 读）：没有响应或状态 ≥500 或 429 记 0 分；其他 4xx 记 N/A；200 时要求匹配 `^\s*#\s+.+`（H1）、`\[.+\]\(.+\)`（至少一个链接）且内容至少 50 字符。

## 五、生成规则（本套件口径）

- 收：主页、About、Pricing、前 3–5 个产品页、Contact。
- 跳过：薄标签页、分页页、登录后页面、法律样板、重复页。
- 频率：活跃博客月更；静态站季更。
- 协调：llms.txt 里列的页面不得对 AI 爬虫禁抓，否则等于自相矛盾。
- 部署后复测：确认无重定向、可直连、返回 `text/markdown` 或 `text/plain`。
- 有多语言的站：默认语言用无后缀 `llms.txt`，其他语言用 `llms.<locale>.txt`（docmd 插件的命名法，见第八节），不要在一个文件里混多种语言。

## 六、评分器怎么算 llms.txt

| 评分器 | 规则 |
|---|---|
| geo-score rubric v1.1（[原文](https://github.com/jianruntech/geo-score/blob/main/rubric/v1.1.md)） | `p1.llms-txt` 满分 5：0 不存在；2 存在且返回 200；4 有站点定义段落；5 且有 2 个以上含链接的主题节。`b.llms-full` 另加 2 分（bonus，不进分母，整个 bonus 上限 +6）。作者在 [evidence-v1.1.md](https://github.com/jianruntech/geo-score/blob/main/rubric/evidence-v1.1.md) 里把它标为「convention」：奖励的是采用约定，不是可证明的效果 |
| geo-optimizer（[config.py](https://github.com/Auriti-Labs/geo-optimizer-skill/blob/main/src/geo_optimizer/models/config.py)） | 默认 rubric v2（v4.19）把 llms 类压到 6 分，源码注释：「llms.txt: ignorato da Google Search, utile ad altri agenti」；v1 的 18 分制仍可用 `--score-version 1`。另有 `/.well-known/ai.txt`、`/ai/summary.json` 等端点家族的加分，本组未核其来源标准 |
| Lighthouse | 见第四节：只检查存在和基本结构，不打质量分 |

这些分值是机器可读性卫生分，不是被引概率。

## 七、Markdown 交付（页面级）

1. **替代 URL**：`/pricing.md` 加 `<link rel="alternate" type="text/markdown">` 或 `Link:` 头。
2. **内容协商**：同一 URL 按 `Accept: text/markdown` 返回 Markdown，必须带 `Vary: Accept` 分开缓存。Cloudflare 的 [Markdown for Agents](https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/) 是这种模式，响应头含 `content-type: text/markdown; charset=utf-8`、`vary: accept`、`content-signal`，变更记录里还有 `x-markdown-tokens`。
3. 风险：内容必须与 HTML 等价，否则像 cloaking。arrivl.ai 的日志里，Markdown 孪生页的请求 8,179 次，其中一个搜索引擎在单站点占 7,993 次，其余四站合计 186 次；没有已确认的代理在发送 `Accept: text/markdown`（本组未找到官方说明）。
4. nginx 的做法：`map $http_accept $md_try` 仅在 Accept 含 `text/markdown` 时改写路径，`add_header Vary Accept always`；`Link` 头只在真有 `.md` 文件的页面输出（本套件口径，未在本组复测）。

## 八、生成器工程（参考 docmd 插件）

[docmd](https://github.com/docmd-io/docmd) `packages/plugins/llms/src/index.ts`（读取版本 v0.9.7，现为 v0.9.8）：

- 默认只为默认语言写 `llms.txt`、`llms-full.txt`、`llms.json`；`i18n: true` 后给每个非默认语言追加 `llms.<locale>.txt` 等。
- frontmatter 有 `noindex` 的页面不进产物。
- 标题经净化函数处理：换行折成空格、截断 200 字符，防 Markdown 注入；以 `=`、`+`、`-`、`@` 开头的标题加单引号前缀，防 CSV 公式注入。
- 输出按路径排序，保证同输入同产物。

## 九、常见错误

1. 相对 URL（`/docs` 而不是 `https://site.com/docs`）。`llmstxt.py validate` 会把以 `/`、`#` 开头的链接报为非绝对 URL（2026-10-21 起）。
2. 说明写成营销口号，代理要的是内容说明。
3. 与 robots.txt 矛盾（列了页又禁了 AI 爬虫）。
4. 一次生成永不更新：链接腐烂后比没有更糟。
5. 把 llms.txt 当 sitemap 复制品（几百行塞满每个 URL）：用 sitemap 承载全量。

## 十、检查清单

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 文件真的是 Markdown | `python3 scripts/llmstxt.py check https://站点` | 通过：`/llms.txt` 为 PASS。失败：HTML、403、5xx |
| 2 | 结构有效 | `curl -s https://站点/llms.txt > llms.txt && python3 scripts/llmstxt.py validate llms.txt` | 通过：退出码 0（有 H1、blockquote、至少 3 条链接）。失败：打印「[问题]」行 |
| 3 | 链接都是绝对 URL 且都能打开 | `grep -oE '\]\([^)]+\)' llms.txt \| head`；逐条 `curl -sI -o /dev/null -w '%{http_code}\n' URL` | 通过：全部 200 且为 `https://`。失败：相对路径、404、重定向链 |
| 4 | 不与 robots.txt 冲突 | `python3 scripts/robots_posture.py https://站点/robots.txt --json`，对照 llms.txt 里的重点页 | 通过：重点页对检索型和用户触发爬虫放行。失败：被禁 |
| 5 | 有人读吗（只看日志，不看引用） | `python3 scripts/ai_referral_log.py access.log --bot-ua --classify`（含 llms.txt 双基线） | 通过：能说出读它的 UA 和次数。失败：用「有文件」当「有效果」 |
| 6 | 报告措辞 | 读方案和报告 | 通过：写「服务读它的代理；Google Search 不用；无引用承诺」。失败：写进 GEO 收益预测 |
| 7 | 同步更新 | 页面增删时更新；月度检查链接 | 通过：无死链。失败：链接腐烂 |
