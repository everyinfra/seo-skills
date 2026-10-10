# llms.txt 指南：格式、校验与生成

> 建立于 2026-10-09。格式要点参考 [zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude)（开源）`skills/geo-llmstxt` 与 [jianruntech/geo-score](https://github.com/jianruntech/geo-score) 的判定规则，交叉 [AnswerEngines spec](https://llmstxt.org)。按本套件的证据约束改写。
> llms.txt 是给 AI 检索系统的内容地图，不是收录保证。没有任何引擎公开承诺"有 llms.txt 就优先引用"。

## 一、llms.txt 是什么、不是什么

- **是**：一个 Markdown 文件，放在站点根路径 `/llms.txt`，告诉来访的 AI 爬虫与检索系统"这个站有什么、去哪看"。提案出自 Jeremy Howard（2024-09），目前是事实上的社区约定。
- **不是**：收录开关。robots.txt 决定"能不能抓"，llms.txt 只是"抓到之后先看什么"的导览。引擎没有义务遵守它。
- **llms-full.txt**：同目录下的加长版（150–500+ 行、30–100+ 页、每页 30–100 词描述）。两者可共存，系统先查 llms.txt。

## 二、格式规范

```
# 站点名称                     ← H1，首行，官方业务名（必填）

> 一句话描述，事实性，无推销水分，200 字符以内（必填）

## Docs                        ← H2 分区（必填至少一个）
- [页面标题](https://example.com/absolute/url)：该页内容的描述，10–30 词
- [另一页](https://example.com/another)：按重要性排序

## Key Facts                   ← 推荐区：成立年 / 总部 / 客户数 / 关键产品
## Contact                     ← 推荐区
```

硬规则：

1. **仅绝对 URL**——相对路径是高频错误。
2. 条目描述 10–30 词；总量 10–30 条；区内按重要性降序。
3. llms.txt 整体 50–150 行、3–6 个分区。常用区名：Docs / Optional / API / Blog / Products / Services / About / Resources / Legal / Contact。
4. 描述要具体："含代码示例的 React Server Components 3000 字完整指南"好过"React 指南"。

## 三、校验严重度表

| 检查 | 严重度 |
|---|---|
| 缺 H1 或没有任何 H2 分区 | **Critical** |
| 条目 <5 条 / 相对 URL / 描述 >200 字符 | High |
| 缺 Key Facts / Markdown 语法破损 | Medium |
| >200 行 / 缺 Contact | Low |

状态码处理：200 → 校验；404 → 生成；403 → 标记配置错误（可能是权限问题不是没有）；301/302 → 跟随后注记。**判定"存在"只看状态码，绝不看响应体积**——定制 404 页也会返回 40–400 KB 的 HTML。

## 四、生成规则

**必收**：主页、About、Pricing、前 3–5 个产品页、Contact。
**跳过**：薄标签页、分页页、登录后页面、法律样板、重复页。
**频率**：活跃博客月更；静态站季更。强内容放前面。
**协调**：llms.txt 里列的页面**不得对 AI 爬虫禁抓**（与 robots.txt 冲突会让一半努力白费）。
**部署后复测**：确认无重定向、可直连。

## 五、判定（供审计用，0–5 分参考 geo-score 的分层）

- 0 = 无文件
- 2 = 存在且 >200 字符（有标题+链接）
- 4 = 有站点定义段落（H1+blockquote 完整）
- 5 = 有 ≥2 个主题分区且分区含链接
- Bonus：llms-full.txt 存在（+2）；llms.txt 内链接到非根路径的完整版也可接受

## 六、常见错误

1. 相对 URL（`/docs` 而非 `https://site.com/docs`）。
2. 描述写成营销口号（"业界领先的革命性平台"）——AI 要的是内容说明。
3. 与 robots.txt 矛盾（列了页又禁了 AI 爬虫）。
4. 一次生成永不更新——链接腐烂后比没有更糟。
5. 把 llms.txt 当 sitemap 复制品（500+ 行塞满每个 URL）——用 llms-full.txt 承载全量。

## 七、来源

- 格式与严重度：[zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) `skills/geo-llmstxt/SKILL.md`
- 状态码判定与"不看体积"：[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `SKILL.md`
- 原始提案：[llmstxt.org](https://llmstxt.org)

## llms.txt v2(2026-08 官方更新,百仓扫描批 2)

**v2 新机制**(AnswerDotAI/llms-txt 2026-08):
- **`.md` 孪生 URL**:page.html.md / page.md——每页的 markdown 版直接挂在 URL 上;
- **发现链**:HTML `<link rel="alternate" type="text/markdown">` + `rel="describedby"`(HTML link 或 HTTP Link 头);
- **子路径作用域**:/docs/llms.txt 覆盖 /docs/,多文件取最具体;
- **Optional 段约定**;与 sitemap/robots/well-known 的边界;
- 佐证:Lighthouse 已审计 llms.txt;OpenAI/Anthropic/Gemini 自发发布 llms.txt。
**edge case**(sceneview 案例):508KB 全量 API 参考 vs 精选链接的取舍——大站点用子路径分文件。
**验证命令**:`npx @vercel/agent-readability audit <url>`(nuxt-seo 生态)。
**Google 口径不变**:llms.txt 对 Google 排名既不帮助也不损害(qiaomu/seomachine 双源核对)——只作 OpenAI 系参考。

## 生态实证与生成规范(llms-txt-hub/docs.page 精读,百仓深扫)

**采用语料**(llms-txt-hub,1,515 条收录):developer-tools 610/ai-ml 573/data-analytics 202/infrastructure 67/security 63;跨度 2024-08→2026-09。**Google 侧证据**:SE Ranking 300k 域研究——AI 引用最多的 50 域中**仅 1 个有 /llms.txt**;OtterlyAI 日志——AI bot 仅 0.1% 请求 llms.txt(84/62,100);Mueller:"No AI system currently uses llms.txt"(2025),用例"a dead end"(2026);Google 官方文档 2026-06-15:"Google Search ignores them"。**但**开发者文档生态真消费(OpenAI/Anthropic/Gemini 自家文档都发布;Cursor/Cline 等 AI 编码 agent 确实读取);**翻案触发条件**:任一大厂确认消费/后续研究拐点/Mueller 收回——挂 source-registry 复查。
**大规模实证写法模式**(curl 实抓):Anthropic=多语言站只给主语言全文(其他语言标注 "Visit website");Cloudflare=**递归分片**(每产品一个自己的 llms.txt);Vercel=面向 agent 的行为指令段("Ask for approval before changing account resources")+?from=llms-txt 追踪;LangChain=按页数分层递归索引;Docker=MCP+llms-full 双通道声明。
**生成规范**(docs.page 路由级):`# {title}`→站描述→`## Docs`→每页 `- [{title}]({绝对URL}): {frontmatter description}`;Content-Type text/markdown;边缘缓存 ~5 分钟+SWR,浏览器 max-age=0 常取新;大仓截断时响应头 `x-tree-truncated: 1`。

## Markdown 交付与消费证据(claude-seo 深读,2026-10-09)

来源:[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-geo/references/llmstxt-evidence.md`、`skills/seo-agentic/references/discovery-and-markdown.md`(2026-09-23 核验,nginx:alpine 实测)。

1. **四巨头发布未消费声明**:Anthropic/Stripe/Cloudflare/NVIDIA 都发布了自家 llms.txt(2024–2025),**没有一家声明其爬虫消费第三方 llms.txt**。Mueller 2025"没有 AI 系统在用 llms.txt"(类比已废弃的 meta keywords)、2026 又称其发现/区分用例是"a dead end";Gary Illyes 2025-07 Search Central Live:Google 无支持计划。审计姿态:报告存在性与格式正确性,**不给引用权重**;用户要求生成时,产物必须带 banner("Google Search 忽略 llms.txt(官方 2026-06-15);无大厂确认消费;为非 Google 期权发布,不为引用")。
2. **Lighthouse `llms-txt` 审计判定**(13.5.0 源码级):4xx → N/A(不算失败);5xx 或抓取错误 → 0 分;否则要求 H1(正则 `^\s*#\s+.+`)+至少一个 Markdown 链接+50+ 字符。**软 404(HTML 返回 200)不是规则内的失败,但实际几乎不会含 `# ` 行,实践中过不了**。
3. **页面级 Markdown 交付两模式**(与 v2 的 .md 孪生互补):①alternate URL(`/pricing.md` + `<link rel="alternate" type="text/markdown">` 或 HTTP Link 头;OpenAI 开发者文档用此模式);②**内容协商**——同 URL 按 `Accept: text/markdown` 返回 markdown,**必须 `Vary: Accept`** 分开缓存;Cloudflare Markdown for Agents 即此模式,响应头族:`content-type: text/markdown; charset=utf-8`、`vary: accept`、`x-markdown-tokens`、`x-original-tokens`、`content-signal`。
4. **nginx 实测配置要点**(2026-09-23,nginx:alpine):`map $uri $md_path` 把 `/pricing` 与 `/pricing/` 都映射到 `/pricing.md`、根路径映射 `/index.md`;`map $http_accept $md_try` 仅在 Accept 含 text/markdown 时切换;`location` 内 `add_header Vary Accept always` + `try_files $md_try $uri $uri/ =404`。**坑**:Link 头若由 nginx 从 `$uri` 生成,内部重写后会指向错误文件——alternate 声明只在真有 .md 文件的页模板里输出。
5. **cloaking 与抓取负载防线**:没有任何确认的消费者 agent 发送 `Accept: text/markdown`(两个独立仓库都标注此缺口);**按 Accept(而非 UA)键控**避免 cloaking 争议与额外 URL;Mueller 质疑"服务没人看的页面",Bing 警告独立 markdown URL 增加抓取负载;markdown 内容必须与 HTML **内容等价**。
6. **AI 编码 agent 是当前真实消费面**:Cursor/Continue/Cline/Claude Code 加载每库文档时读 llms.txt;Mintlify 为数千开发者文档站自动生成 llms.txt+llms-full.txt。开发者工具站净收益明确;非开发者商业站纯防御性(零成本+未来期权)。

## 毕业化打分与 /ai/* 端点家族(geo-optimizer-skill 深读,2026-10-09)

来源:[Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) `src/geo_optimizer/models/config.py` SCORING 表 + `core/scoring.py`(源码级)。

1. **llms.txt 毕业化(graduated quality)打分**,18 分制替代二值判定:found 5 / H1 2 / **blockquote 描述段 1**(v2 新增,#39)/ sections 2 / links 2 / **词数 ≥1000 +2、≥5000 再 +2**(llms_depth/llms_depth_high 两档)/ llms-full.txt 存在 +2——"文件从有到厚"是阶梯不是开关。
2. **/ai/* 发现端点家族(geo-checklist.dev 标准,共 6 分)**:`/.well-known/ai.txt` 2 分;`/ai/summary.json` 2 分(**必须通过 validity 校验**,存在但无效=0);`/ai/faq.json` 1 分;`/ai/service.json` 1 分。与本文第五节 geo-score 的 0–5 判定、第二节格式规范互补——三个工具对 llms.txt 的分值不同但"毕业化"方向一致。

## v2 官方变更原文级与解析器实现(AnswerDotAI/llms-txt 深读,2026-10-09)

来源:[AnswerDotAI/llms-txt](https://github.com/AnswerDotAI/llms-txt)(提案官方仓)`nbs/changes.qmd` + `llms_txt/core.py`/`miniparse.py` + README v2(date-modified 2026-08-10)。

1. **v2 四项变更的原始措辞**(补足本文 v2 节):①最常见社区请求是**可发现性**——给定一个页面,agent 如何不靠猜找到它的 markdown 版/覆盖它的 llms.txt→标准 link relations;②v1 只规定 `.md` 追加式(`page.html.md`),有出版工具改成替换扩展名(`page.md`),**v2 追认两种都合法**;无文件名的 URL 追加 `index.html.md`/`index.md`;③子路径语义正式定义:文件覆盖其路径下全部页面、多文件适用时**取最具体者**——只控制一个路径的站(如 GitHub Pages 项目站)因此可完整参与;④**消费模型改写:agent 查看或搜索 llms.txt 找到所需,再跟随链接(链接应指向 LLM 友好内容、文件本身保持小到能进上下文、细节在链接后按需取)**;`llms_txt2ctx` 上下文展开工具退出提案,`Optional` 段的机械语义(告诉展开工具省略什么)随之取消——Optional 仍允许、仍是次级链接约定,但**不再携带机械语义**。
2. **官方解析器正则**(证明"精确格式可用经典解析器处理"):链接行 `-\s*\[(?P<title>[^\]]+)\]\((?P<url>[^\)]+)\)(?::\s*(?P<desc>.*))?`;头部 `^#\s*(?P<title>.+?$)\n+(?:^>\s*(?P<summary>.+?$)$)?\n+(?P<info>.*)`(MULTILINE|DOTALL);节切分=按 `^##\s*(.*?$)` split 后两两配对成 {节名: 链接列表}。
3. **采纳证据链(官方口径)**:数千站发布;Mintlify 自动生成;Chrome Lighthouse 以 agentic-browsing 审计之;**三大 AI 实验室为自家开发者文档发布 llms.txt**(OpenAI developers.openai.com/llms.txt、Anthropic docs.anthropic.com/llms.txt、Gemini ai.google.dev/gemini-api/docs/llms.txt);nbdev 项目默认为所有页面生成 .md 版本(Answer.AI/fast.ai 全系已重生成)。

## 生成器工程:多语言命名/页级排除/llms.json/注入防御(docmd 深读,2026-10-09)

来源:[docmd-io/docmd](https://github.com/docmd-io/docmd) `packages/plugins/llms/src/index.ts`(v0.9.7 全文源码)。

1. **i18n 文件命名规范**:默认只为默认 locale 写无后缀 `llms.txt`/`llms-full.txt`/`llms.json`(对既有消费者零破坏);开启 `plugins.llms.i18n: true` 后为每个非默认 locale 追加 `llms.<locale>.txt`/`llms-full.<locale>.txt`/`llms.<locale>.json`(如 llms.ja.txt)——多语言站的双 llms.txt 问题(见 multilingual-workflow)的落地命名法。
2. **页级排除**:frontmatter `noindex` 或 `llms: false` 的页面不进任何产物——与 sitemap 的 noindex 联动逻辑一致。
3. **第三产物 llms.json(机器可读清单)**:{title, description, pages:[{title, url, description, **priority**}]};priority 默认首页=high、其余=medium,可 frontmatter 覆盖——txt 给 agent、json 给管道。
4. **注入防御两威胁(T-Z10/T-Z11)**:标题经 `safeForMarkdownAndCsv` 净化——markdown 注入(`]`/`[`/反引号/反斜杠转义、换行折成空格、截断 200 字符)与 **CSV 公式注入(以 `=`/`+`/`-`/`@` 开头的标题加单引号前缀,防 Excel/LibreOffice/Sheets 打开时执行公式)**;llms-full.txt 正文视为信任的第一方内容,但注明"消费者不得不经消毒在 HTML 上下文渲染"。
5. 输出按 outputPath localeCompare 排序保证稳定(同输入同产物)。
