# 程序化 SEO 质量闸门

> 建立 2026-10-09，核对 2026-10-18。阈值全部是**本套件口径**：第一至六节出自第三方 skill 仓 [claude-seo](https://github.com/AgriciDaniel/claude-seo)（MIT，v2.4.2），第八节出自 [goose-skills](https://github.com/gooseworks-ai/goose-skills)，都不是 Google 规则。`pseo_batch_gate.py`、`pseo_pattern_mining.py`、`pseo_cohort.py` 硬编码了其中部分数字。
> 分工：[playbooks.md](playbooks.md) 选模式 → [programmatic-seo-playbook.md](programmatic-seo-playbook.md) 跑生命周期 → 本文件卡红线。

## Google 原文（核对 2026-10-18）

- [Scaled content abuse](https://developers.google.com/search/docs/essentials/spam-policies#scaled-content)：为操纵排名、不为帮助用户而批量生成很多页面；内容原创性低、对用户几乎没有价值，不论怎么生成。例子含：用生成式 AI 批量产页而不增加价值；抓取或拼接他站内容（含同义替换、翻译）；建多个站掩盖规模化。2024-03-05 发布，人工产出同样适用（[博客](https://developers.google.com/search/blog/2024/03/core-update-spam-policies)）。
- [Doorway abuse](https://developers.google.com/search/docs/essentials/spam-policies#doorways)：为一组相近查询建站或建页，把用户引到不如目的地有用的中间页。例子含：按地区或城市定向的多个域名或页面，把用户导向同一页。
- [Helpful content 自检](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)（转述）：是否靠大量自动化覆盖很多主题？是否批量外包或分散到大量站点，单页得不到照看？读完是否还要再搜？Google 没有偏好字数。
- [生成式 AI 指南](https://developers.google.com/search/docs/fundamentals/using-gen-ai-content)（2026-10-01 更新）：发布前人工核查 AI 内容，核查覆盖 title、meta description、结构化数据和图片 alt。自检参照[评分员指南](https://static.googleusercontent.com/media/guidelines.raterhub.com/en//searchqualityevaluatorguidelines.pdf)（2025-09-11 版）4.6.5 Scaled Content Abuse 和 4.6.6 低投入、低原创、低附加值的主内容；评分不直接影响排名。电商：AI 图片带 IPTC `DigitalSourceType=TrainedAlgorithmicMedia`，AI 标题和描述用 Merchant Center 的 `structured_title`、`structured_description`（[政策](https://support.google.com/merchants/answer/14743464)）。
- 独立价值测试（本套件口径，claude-seo）：假如没有其他同类页，这页还值得发布吗？答"否"就不进批次。

## 一、核心闸门（本套件口径）

| 指标 | 阈值 | 动作 |
|---|---|---|
| 未复核页 | **100+** | WARNING：发布前做内容审计 |
| 无正当理由页 | **500+** | **硬停**：用户明确批准 + 薄内容审计 |
| 页间唯一内容 | **<40%** | 标记薄内容 |
| 页间唯一内容 | **<30%** | 硬停（增强规则） |
| 单页字数 | <300 | 标记复核 |
| 近重复记录 | 字段重合 >80% | 标记 |

唯一度 = 该页独有词 ÷ 该页总词 × 100，对照集内其他全部页；排除公共页头、页脚、导航，计入模板样板。`pseo_batch_gate.py` 按拉丁词 + CJK 双字 token 求批次均值；它把 100/500 套在**警告条数**上；近重复用 title + 首段 Simhash（汉明 ≤3）近似；不查 <300 词。

## 二、发布纪律（本套件口径）

- 发布前人工抽检 **≥5–10%** 样本。
- 分批上线：每批 **50–100 页**，观察 **2–4 周**再发下一批。
- 不一次发布 **500+** 未审页。

## 三、页型地板（字数/唯一度）

本套件口径（claude-seo `quality-gates.md`），只是复核触发线，不是排名门槛。

| 页型 | 字数下限 | 唯一度下限 |
|---|---|---|
| 主页 | 500 | 100% |
| 服务页 | 800 | 100% |
| 位置页（主） | 600 | 60% |
| 位置页（次） | 500 | 40% |
| 博客 | 1,500 | 100% |
| 产品页 | 400 | 80% |
| 分类页 | 400 | 100% |
| About / 落地页 | 400–600 | 100% |

脚本默认只有 product=400、article=800；记录写 `page_type`，用 `--floor blog=1500,location=600` 补其他页型。

位置页：**30+** 页 WARNING（每页唯一度 ≥60%）；**50+** 页硬停（需书面正当理由）。**换城测试**：换掉城市名后内容仍成立的页，对上 doorway 原文例子。

## 四、安全 vs 风险页型（本套件口径）

**安全**：集成页（真实设置文档 + API 细节 + 截图）、模板/工具页（可下载）、词表（200+ 词定义）、产品页（独有规格/评论/对比）、数据页（独有统计/图表）。
**风险**：只换城市名的地点页；无行业价值的 "Best [tool] for [industry]"；无对比数据的 "[竞品] alternative"；未经人工核查的 AI 内容；**模板样板 >60%** 的页。

## 五、URL 与内链规则

- URL（本套件口径）：小写连字符 slug，生成时强制唯一，**<100 字符**，主内容 URL 不带 query 参数，尾斜杠一致。反例：Wise 把 `?amount=` 变体放进了 sitemap（playbook 第九章）。
- 内链（本套件口径）：3–5 条/千词；每页自动关联 3–5 个相关页；hub/spoke 配 BreadcrumbList。
- Sitemap：单文件有 URL 数和体积两个上限（[事实表](../overview/facts.md#sitemap-limits)），超了必须拆分。Google 只采用一贯且可验证的 `<lastmod>`。Google 忽略 `<priority>` 和 `<changefreq>`。URL 排列顺序对 Google 没有作用。noindex 页不入 sitemap。

## 六、索引膨胀控制

- 未过闸门的页先不生成，确需保留功能才 noindex。noindex 要等页面被抓取才生效（[原文](https://developers.google.com/search/docs/crawling-indexing/block-indexing)）。
- 筛选视图（[faceted navigation](https://developers.google.com/crawling/docs/faceted-navigation)）：不需要索引的筛选 URL 用 robots.txt 屏蔽；无结果的组合返回 404。只对真重复或低价值视图做 noindex/canonical 合并。
- 程序化页 **>10k** 的站监控抓取统计（本套件口径）。Google [抓取预算指南](https://developers.google.com/crawling/docs/crawl-budget)主要面向 100 万+ 页周更、1 万+ 页日更、或大量 URL 处于 "Discovered – currently not indexed" 的站。
- 每月审计"已索引 vs 应索引"；薄记录并进聚合页。

## 七、检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 唯一度、样板比、title+H1 重复、地板、事实来源 | `python3 scripts/pseo_batch_gate.py --records batch.jsonl --rendered dist/ --json` | exit 0（PASS）才发布；exit 1 退回数据层 |
| 人工抽检 | 随机抽 ≥5–10%，逐页答上方自检问题和独立价值测试 | 任一页答出警示答案 → 该模式退回 |
| AI 元数据 | 抽检页对照数据源核 title、description、结构化数据、alt | 有事实错误 → 整批停 |
| 标题长度按市场 | `python3 scripts/market_lint.py --market ja page.html` | 无 CRITICAL（exit 0） |
| sitemap | `python3 scripts/sitemap_audit.py https://example.com --max-child 200` | exit 0；单文件不超 [URL 数上限](../overview/facts.md#sitemap-limits)；lastmod 不报伪造 |
| 位置页数量 | 按 URL 模式计数 | <30 通过；30–49 唯一度 ≥60%；≥50 需正当理由 |
| 发布后：已索引 vs 应索引 | GSC Page indexing 报告，按该批 sitemap 筛选 | 8 周内已编入索引 ÷ 已提交 ≥60%（本套件口径，同 `pseo_cohort.py` 默认） |

## 八、goose pSEO 模式:竞品逆向与模式闸门(gooseworks 深读,2026-10-09)

本节管"选什么模式值得做"，全部是本套件口径，出自 goose-skills `programmatic-seo-spy` 与 `programmatic-seo-planner`（核对 2026-10-18）。

**第一步：URL 模式正则分类表**（爬竞品 sitemap 后聚类）：

| 正则 | 页型 | 数据轴 |
|---|---|---|
| `/vs/.*`、`/compare/.*` | 对比 | 竞品名 |
| `/integrations?/.*` | 集成 | 工具/App 名 |
| `/for-.*`、`/solutions/.*` | 垂直行业 | 行业名 |
| `/use-cases?/.*` | 用例 | 任务场景 |
| `/alternatives?(-to)?/.*` | 替代 | 竞品名 |
| `/templates?/`、`/examples?/` | 模板 | 模板类型 |
| `/glossary/`、`/what-is/` | 词汇 | 术语 |
| `/tools?/`、`/calculat(or\|e)/` | 工具 | 工具功能 |
| `/blog/.*` | 编辑内容（**排除出 pSEO 分析**） | — |

每模式记：页数、数据轴、URL 一致性、**覆盖完整度**。

**四分类**：Programmatic（URL 一致 + 标题同构 + 页数多）/ Semi（模板 + 大量手工）/ Editorial（单篇手写）/ Auto-generated thin（标签页、归档页）。只分析前两类；thin 类直接记风险。

**模板质量 7 维打分**（每维 1–5；每模式抽 3–5 页，高、低、中变体各一）：内容深度 / 每页独有价值 / 数据丰富度 / 新鲜度信号 / 内链 / CTA 融合 / schema（FAQ 富结果已停展，[日期](../overview/facts.md#rich-results)，此维只评标记是否正确）。均分 4–5 = 难撼动；3–4 = 可用更好模板打赢；1–3 = 薄，易超越。

**缺口四型**：① 白空间（没有竞品做，先验证需求）② 变体缺口（竞品没做满，快赢）③ 质量缺口（竞品页 <500 词、无独有数据、过时、无 schema）④ 正面强攻（硬撼 4–5 分模板，成本高）。

**模式评分权重**：搜索需求 30% / 意图质量 25%（vs/ 高，glossary 低）/ 模板可行性 20% / 数据可得性 15% / 竞争缺口 10%。**评分 ≥50 的模式过可行性三问**：① 数据源在哪（竞品名单手工、集成名录走 API、行业用标准列表）② 怎么差异化（vs/ 要真实功能对比，集成页要真设置指南，垂直页要行业痛点）③ CMS 能否规模化：静态生成器（Next.js、Astro）最好，WordPress 自定义文章类型可行，纯手工不是 pSEO。Webflow 的 CMS item 上限按站点套餐计、不按集合：Premium 与 Team 每站 20,000 条，Enterprise 定制（[webflow.com/pricing](https://webflow.com/pricing)，核对 2026-10-18；goose 原文"每集合 10K"已过时）。

**vs/ 模板蓝图八段**：① TL;DR 三句话 ② 快速对比表 ③ 详细对比 4–6 维 ④ 价格逐档对比 ⑤ 谁该选我们 ⑥ 谁该选对方 ⑦ 双边用户评价 ⑧ CTA。数据：竞品功能、价格、评论（G2/Capterra）、差异点。硬要求：≥1,500 词、≥1 条独有洞察、能用截图就用、**每季度更新**。

**流量归因两模式**：增强模式按 URL 包含 `/vs/` 等过滤 ranked_keywords，得每模式排名词数、估算流量、均位；基线模式每模式抽 3–5 页查是否进前 10，再用 `site:domain/vs/` 看收录，结果**明标方向性估算**。优先级：P0 = 白空间 + 质量缺口，P1 = 变体缺口，P2 = 正面强攻。

## 九、来源

- 第一至六节阈值：claude-seo `skills/seo-programmatic/SKILL.md`、`skills/seo/references/quality-gates.md`。第八节：goose-skills `skills/seo/composites/programmatic-seo-spy/SKILL.md`、`programmatic-seo-planner/SKILL.md`。均核对 2026-10-18。
- Google 原文链接见各节，均核对 2026-10-18。
