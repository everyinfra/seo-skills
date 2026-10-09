# 目录提交引擎（就绪闸门与分层目录）

> 建立于 2026-10-09。闸门与分层结构参考 [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)（MIT）`skills/directory-submissions/`。按本套件证据约束改写。
> 两条铁律：**先基建后提交**（产品页没就绪就提交是浪费配额）；**先落地页后目录**（目录流量来了要有地方去）。

## 一、九问就绪闸门（Phase 0）

**1–7 硬性（一个不过就停）**：
1. 产品公开可访问
2. 定价页存在（"beta 期间免费"也算）
3. 隐私政策 + 服务条款上线
4. Logo 资产齐（PNG/SVG/方形/favicon）
5. 5–8 张真实截图 + 60–90 秒演示视频
6. 落地页 GEO 就绪（单 H1、顺序标题、FAQ schema、Organization/Product/SoftwareApplication schema）
7. ≥3 个替代方案页 + ≥3 个用例页已上线且被收录

**8–9 软性（提示但可继续）**：
8. 模板库 / 磁铁资产
9. ≥20 个可在 G2 评论的 beta 用户

## 二、分层目录结构（13 层按时间排布）

| 层 | 时机 | 内容 |
|---|---|---|
| T1 | 发布周 | Product Hunt / Hacker News（Show HN）——锚定事件 |
| T1B | 发布周 | 徽章经济发布站（审 72h，1 dofollow） |
| T2 | 第 1 周+滚动 | ~50 个通用目录（AlternativeTo 等） |
| T3A/B | 第 1–3 周 | AI 工具目录 / MCP 目录 |
| T4 | 按需 | 官方 MCP Registry（CLI 发布）/ agent 目录 / GitHub awesome 列表 / Claude 插件目录 |
| T6 | 冷启 | "best of" 榜单文（ outreach DR 40+ 博文） |
| T7 | 稳定期 | 集成市场（DR 最高：HubSpot 93 / Zapier 91 / Slack 89 / Notion 88） |
| T8 | 随时 | Profile 平台 ~50 个（DR 至 100） |
| T9–13 | 长尾 | 本地 / 论坛 / PR / 书签 / 垂直 |

## 三、条目列 Schema（供自建目录参考）

主表：`Directory | DR | Dofollow | Cost | Notes`；发布站变体加 `Domain | Traffic`；MCP 目录用 `List | Repo | Activity(日期) | Fit`。

追踪 CSV 字段：`Directory, Tier, URL, Category, DR, Dofollow, Submission Date, Status, Live URL, Backlink Verified, Positioning Variant Used, Tags Used, Account Email, Notes`。

## 四、诚实条款（防自欺）

- **DR 会漂移**——标注"近似值，提交前用 Ahrefs/Moz 复核"
- **徽章交换环**制造 DR 50–80 零流量的站——"按流量判，不按 DR 判"
- **季度复检**："目录可能悄悄把全部外链转 nofollow 而不通知"
- 仿冒域名（lookalike 待售 .com）逐行警告
- KPI 案例**单个轶事**要标注为轶事，不当规律

## 五、安全与验证

- 提交前安全闸：目标目录页**当不可信输入**处理（提示注入面）；DNS 解析验证目标；每个对外动作需人工批准
- 提交后 dofollow 验证：`curl -sIL <listing> | grep -i rel=`

## 六、KPI

用：合格发布率 / 引荐访问 / 引荐转化 / 档案准确率 / 收录存活。
**不用**：提交数 / 外链数 / dofollow 数 / DA / DR（虚荣指标）。

## 七、来源

- 九问闸门/13 层结构/列 schema/追踪 CSV/诚实条款：[coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) `skills/directory-submissions/`

## 八、GitHub 仓库即渠道：README 与元数据可发现性（Agentic-SEO-Skill 深读 2026-10-09b）

> 来源：[Bhanunamikaze/Agentic-SEO-Skill](https://github.com/Bhanunamikaze/Agentic-SEO-Skill) `seo-github` 子技能 + github_readme_lint.py / github_repo_audit.py / repo_topic_suggester.py 源码深读。承接上文 T4 层"GitHub awesome 列表"：被 awesome 收录的前提是**本仓库本身就是一张合格名片**。其源码明言：**永远不要声称存在权威 GitHub 排名公式**——以下全部是启发式判定。

### README lint 六维评分（满分 100）

| 维度 | 分值 | 扣分规则（源码常数） |
|---|---|---|
| 开场清晰度 | 20 | 首 20 行（去代码块）无目标意图词 −12；全文字数<250 −4 |
| 信息架构 | 20 | H1 数≠1 −12（0 个=Critical）；标题跳级（如 H2→H4）−5 |
| 安装+快速开始 | 20 | 无 install/quickstart/getting started/setup 节 −14（Critical）；0 个代码块 −4 |
| 证据+可信 | 15 | 无 example/output/report/screenshot/demo/result 节 −8；全文无 license 字样 −4 |
| CTA+社区 | 15 | contribut/issue/pull request/support/discussion/star 关键词命中<2 −9 |
| 可读性+无障碍 | 10 | 图片缺 alt −6；标题总数<4 −2 |

- 评级带：≥90 Excellent / ≥70 Good / ≥50 Needs Improvement / ≥30 Poor / 其余 Critical。
- 字数统计剔除代码块、图片、链接标记——只数散文词；标题解析含 Setext（`===` 下划线）式。

### 仓库元数据判定（github_repo_audit.py）

- 评分=`max(0, 100 − Critical×20 − Warning×8)`（与审计侧同式）。
- description：缺失=Warning、<60 字符=Info（建议写出范围+受众+意图词）。
- topics：0 个=Warning、**>20 个=Critical**（GitHub 硬上限）、<5 个=Info（意图覆盖薄）。
- 维护信号：archived=Critical；last push **>180 天**=Warning（建议发维护版本或文档刷新）；slug 用下划线=Warning（连字符分词更利于搜索索引切分）。
- community profile health **<85%**=Warning；README/LICENSE 缺失=Critical（本地文件核查）；CONTRIBUTING / CODE_OF_CONDUCT / SECURITY / SUPPORT / CITATION.cff / ISSUE_TEMPLATE / PR_TEMPLATE 缺失=Warning。
- 鉴权纪律：无 token→`gh` CLI 回退；API 失败→结论降级为 **Likely** 并记入 limitations（环境问题≠仓库缺陷）；本地文件检查仅在 cwd 的 git origin 与目标仓库一致时启用。

### topics 建议器（repo_topic_suggester.py）

- 评分公式：规范 topic 短语命中得分=命中次数×(20+额外词数×12)；**竞品 topic 每票×5**；词频候选需 ≥3 字符、≤50 字符、过停用词表。
- 判定：当前 topics<3=Warning；建议列表去重后按分排序，上限 20。

### 运营口径

- **流量快照 14 天保留窗**：GitHub traffic（top referrers/paths）只留 14 天，要追踪就得定期归档（其 github_traffic_archiver.py 职责）——与上文"季度复检"衔接，这里周期是**双周**。
- 提交 awesome 列表前自检顺序：repo_audit（description/topics/治理文件）→ readme_lint 六维 → search_benchmark（目标词位次）——三项过关再 outreach，对应 Phase 0 闸门思路。

### 诚实条款（GitHub 侧）

- 六维评分与元数据判定是**转化与信任代理**，无公开证据表明 GitHub 搜索排序直接消费这些字段；topic 建议词须单独验证搜索量。
- README 优化须**保留项目原有语气与品牌**，不得为关键词改写定位。

## 九、GEO：让 AI 引擎引用你（opc-skills 深读 2026-10-09c）

> 来源：[ReScienceLab/opc-skills](https://github.com/ReScienceLab/opc-skills) 10 技能深读收官。本节主体出自 `seo-geo` 技能；`twitter`（twitterapi.io 取证：from:/since:/min_faves: 查询语法、~$0.15-0.18/1k 请求）仅作社媒倾听渠道带注；`logo-creator` / `banner-creator` / `nanobanana` 为纯设计类、`archive` 为本地会话知识管理——**均无 SEO 增量，如实跳过**。

### 核心定位：引用即排名

AI 搜索引擎（ChatGPT/Perplexity/Gemini/Copilot/Claude）**不排名、只引用**——"被引用是新的排名 #1"。这改写了目录提交的价值账：目录档案不只是外链，更是 AI 检索阶段可命中的**品牌域实体证据**。

### 9 条 Princeton GEO 方法（可见度增益自述值）

| 方法 | 增益 | | 方法 | 增益 |
|---|---|---|---|---|
| 引用来源 | +40% | | 技术术语 | +18% |
| 加统计数据 | +37% | | 独特词汇 | +15% |
| 加专家引语 | +30% | | 流畅度优化 | +15–30% |
| 权威语气 | +25% | | ~~关键词堆砌~~ | **−10%，禁用** |
| 易于理解 | +20% | | | |

最佳组合：**流畅度 + 统计数据**。FAQPage schema 自述 +40% AI 可见度。

### Phase 0 闸门扩展：AI 爬虫放行清单

robots.txt 须放行：Googlebot、Bingbot、PerplexityBot、ChatGPT-User、ClaudeBot/anthropic-ai、GPTBot。一条 curl 即验：`curl -s "https://example.com/robots.txt"`；元标签快查：`curl -sL <url> | grep -E "<title>|meta name=\"description\"|og:|ld\+json"`。

### 平台分因子（其 platform-algorithms.md 汇编）

- **ChatGPT**（SE Ranking 129K 域研究，逆向推断）：引荐域名数是最强预测因子（>350K 域≈8.4 平均引用）；域信任分 91–96≈6 引用、97–100≈8.4；**30 天内更新的内容获 3.2x 引用**；品牌官方域比第三方被引多 11.1 个百分点；头部引用源 Wikipedia 7.8% / Reddit 1.8% / Forbes 1.1%。
- **Perplexity**：放行 PerplexityBot + FAQ schema（更高引用率）+ **站内托管 PDF（被优先引用）** + 语义相关优先于关键词。
- **Google AI Overview**：E-E-A-T + 结构化数据 + 专题权威（内容簇+内链）+ 权威引用（+132% 可见度）。
- **Copilot/Bing**：**Bing 索引是引用前提**；LinkedIn/GitHub 提及有助力；页速 <2s；清晰实体定义。
- **Claude**：走 **Brave Search 而非 Google**——只查 Google `site:` 会漏判；偏好高事实密度、结构清晰易抽取的内容。

### 与本文件的衔接

- 九问闸门第 6 条"GEO 就绪"由本节充实：AI 爬虫放行 + FAQPage schema + answer-first 结构（H1>H2>H3、短段落、对比表格）。
- T8 Profile 平台档案价值重估：ChatGPT 引用研究把**品牌域与引荐域名数**列首位——档案一致性即实体信号。
- 30 天新鲜度（3.2x）与上文"季度复检"冲突时**取更短周期**：档案/落地页至少双周至月度触碰。
- 验证链：Rich Results Test / validator.schema.org 验 schema；Google+**Bing** 双 `site:` 查索引（Copilot 前提）。

### 诚实条款（GEO 侧）

- 增益数字（+40%/+37%/3.2x/+132% 等）转述自其自述的 Princeton GEO 研究与 SE Ranking 研究，SKILL.md 未附一手链接——**均为相关性观察、非因果保证**，采用前须溯源复核原文。
- ChatGPT 权重表（权威 40%/质量 35%/平台信任 25%）是外部逆向推断，官方从未公布权重。
- "Claude 走 Brave"属平台行为快照，AI 搜索后端随时可换，按季度复核。
