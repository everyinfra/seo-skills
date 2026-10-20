# 外链画像分析框架

> 建立于 2026-10-09，2026-10-21 复核。框架要点参考 [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo)（MIT）的 `seo-backlinks` 技能和 [zubair-trabzada/dataforseo-claude](https://github.com/zubair-trabzada/dataforseo-claude) 的"按数据源层级选择"思路，按本套件的证据约束改写。
> 本文件是分析框架，不是数据服务：数据来自你自己的工具导出或 API 账号。不承诺外链数量、排名或流量提升。
> **口径说明**：下文所有阈值、权重和置信度数字，除注明出处的以外，都是**本套件口径**（经验提示，没有外部研究支撑）。DR、DA、AS 是 Ahrefs、Moz、Semrush 各自的评分，不是 Google 的信号（见 [backlink-directory](backlink-directory.md) 第二节）。

## 一、先探测可用数据源

| 层级 | 数据源 | 成本 | 能提供 | 本套件置信度（口径） |
|---|---|---|---|---|
| 3 | DataForSEO 等付费 API | 按调用计费 | 全量外链、锚文本、增减 | 1.00 |
| 2 | Moz Links API 免费档、Bing Webmaster Tools、Google Search Console 链接报告 | 免费 | Moz：DA/PA/Spam Score；Bing 与 GSC：已验证属性的链接 | 0.85 / 0.70 |
| 1 | Open PageRank（DomCop） | 免费注册 | 0–10 评分，由 PageRank 和按权威加权的来链域数合成 | 0.60 |
| 0 | Common Crawl 域名图 | 永远可用 | 域名级 PageRank 和谐波中心性 | 0.50 |
| 0 | 自建验证爬虫 | 永远可用 | 已知外链是否仍然存在、`rel` 是什么 | 0.95 |

已核事实（2026-10-21）：

- Moz 免费 API："每 10 秒一次请求，每月最多 50 行"（[Moz API 价格页](https://moz.com/products/api/pricing)）。50 行只够抽样，不够全站画像。
- Common Crawl 每季度发布主机级和域名级 Web Graph，含 harmonic centrality 与 PageRank（[Common Crawl 博客](https://commoncrawl.org/blog/host--and-domain-level-web-graphs-may-june-and-july-2026)）。图来自抓取快照，有滞后，不当速度数据用。
- Open PageRank 分数范围 0–10，对数刻度（[DomCop 说明](https://www.domcop.com/openpagerank/what-is-openpagerank)）。
- Google Search Console 的链接报告可导出，是你自己站唯一来自 Google 的链接数据；它不是全量。

规则（本套件口径）：

- 多源都有数据时，按置信度加权合成：`加权分 = Σ(源分 × 置信度 × 因子权重) / Σ(置信度 × 因子权重)`。
- 两个源冲突时相信更高层级，并把分歧写进报告，不悄悄择一。
- 免费源标注"仅时点快照"。
- 没有任何付费或注册源时，可基于 Common Crawl 出域名级报告，并建议配置 Moz 免费 API 与 GSC 导出以获得锚文本和页面级数据。

## 二、七段式分析

### 1. 画像总览

总量：外链总数、来链域数、follow 比、趋势。判读参考（本套件口径，非硬规则）：

- 来链域数：>100 良好 / 20–100 观察 / <20 薄弱。
- follow 比：>60% 正常 / 40–60% 观察 / <40% 偏低。
- 集中度：单一域贡献 >25% 来链域总数时标记集中风险。
- 趋势：季度降幅 >20% 视为快速流失，需查明原因。

### 2. 锚文本分布

Google 没有公布健康锚文本比例。下表是本套件的**审计提示**，只用于发现异常，不当目标：

| 锚类型 | 提示区间 | 异常信号 |
|---|---|---|
| 品牌词 / 品牌+URL | 30–50% | — |
| 裸 URL | 15–25% | — |
| 通用词（click here 等） | 10–20% | — |
| 精确匹配关键词 | 3–10% | >15% 看是否买链 |
| 部分匹配 | 5–15% | >25% 标记 |

上一版列的"各行业品牌词占比"（SaaS 40–55%、本地 45–60%、出版 30–40%）没有出处，已删除。单一域名内 100% 精确匹配锚按高危处理（该模式符合 Google 政策里"带优化锚文本的付费文章或客座文"一类）。

### 3. 来链域名质量

- TLD 分布：Google 说明 TLD 对排名几乎无直接影响（见 [domain-strategy](domain-strategy.md)）。上一版"`.edu`/`.gov` 高价值、`.xyz`/`.info` 低质"没有出处，已删。TLD 只作审计时的聚类维度。
- 国家分布：大部分来链来自与业务无关的国家时，人工抽查（本套件口径，不是判定规则）。
- 权威分层：按 DA、DR 或 AS（任选一家，注明是哪家）分桶，看分布形态，不看单个高值。
- 每域 follow/nofollow 比。

### 4. 疑似垃圾链检测

对照 Google [垃圾内容政策的 link spam 条目](https://developers.google.com/search/docs/essentials/spam-policies#link-spam)（核对 2026-10-21）：

**高危（发现即标记）**：来自 PBN；单域 100% 精确匹配锚；批量低质目录或书签站；页脚、侧栏或模板里广泛分发的链接；论坛签名或评论里的优化链接；明显的付费文章链接且无 `sponsored`。
**中危（组合出现时标记）**：无关主题；互链成对出现；薄内容站；单域 >50 条来链（本套件口径）。

完整的 30 模式清单见源仓库 `skills/seo/references/backlink-quality.md`；该清单的阈值是源仓库口径，未逐条核对。

### 5. 按外链排序的页面

- **链磁铁**：自然吸引链接的页面，内容策略的正面证据。
- **零外链重要页**：用内链传导（见 `scripts/link_graph.py`）。
- **有外链的 404 或重定向链**：修复或 301 到最相关页，收回既有链接。重定向写法见 Google [重定向文档](https://developers.google.com/search/docs/crawling-indexing/301-redirects)；用 `scripts/redirect_chain.py <URL>` 看链长。

### 6. 竞品差距

矩阵：链接到竞品但不链到目标站的域是机会；双向链接是关系验证；只链目标站是竞争优势。输出 Top 20 机会域并注明用哪家权威指标。

### 7. 新增与丢失

需要付费 API 或定期导出；免费源写"无法提供"。红旗（本套件口径）：一周内新增 10 倍于常态（排查负面 SEO 或买链）；一月丢失 50%+（排查站点变更或来源下线）；新增全部来自同一 TLD 或同一国家；连续 3 个月速度下滑。

## 三、外链健康分（0–100，本套件口径）

| 因子 | 权重 |
|---|---|
| 来链域数 | 20% |
| 域质量分布 | 20% |
| 锚自然度 | 15% |
| 疑似垃圾链占比 | 20% |
| 速度 | 10% |
| follow/nofollow | 5% |
| 地理相关性 | 10% |

权重是本套件的约定，没有外部研究。

**数据闸门（强制）**：7 个因子里至少 4 个有真实数据才允许输出数字分；否则输出 `外链健康分：数据不足（X/7 因子已评）`，列出缺失因子和补齐办法。禁止给未测量的因子赋默认值。

## 四、Disavow 决策

Google [Disavow 帮助](https://support.google.com/webmasters/answer/2648487?hl=en)（核对 2026-10-21）写明：多数站不需要这个工具。只有同时满足两条才建议使用：

1. 你有大量垃圾、人造或低质链接指向你；
2. 这些链接已经造成或很可能造成人工处置。

Google 还写：先尽量移除这些链接，移除不了再 disavow。该工具不支持域名属性（Domain property）。

**应该 disavow**：收到"非自然入站链接"人工处置；你或前任 SEO 买过链接、做过链接方案，且有大量证据。
**不该 disavow**：没有人工处置、只是看起来难看的低权威链接；nofollow 链接；合法的小站。上一版"毒链占比 >10% 就 disavow"没有 Google 依据，已删。
文件格式：纯文本，一行一个 URL 或 `domain:example.com`，`#` 开头为注释（见同一帮助页）。Disavow 是最后手段，不是日常清理。

## 五、检查清单

| 检查什么 | 怎么查 | 通过/失败 |
|---|---|---|
| 导出能统一导入 | `python3 scripts/backlink_import.py <导出.csv> --format auto --out unified.csv --json summary.json`（`--format` 可选 ahrefs/semrush/gsc/unified） | 输出行数等于导出行数（去表头）；嗅探不出格式退出码 2，不猜 |
| 锚文本是否过度精确 | `backlink_import.py ... --brand <品牌词>` 给出精确匹配占比 | 精确匹配 >15% 进人工抽查（本套件口径） |
| 外链是否还在、`rel` 是什么 | `curl -sL <来源页> \| grep -oE '<a [^>]*href="https?://你的域名[^"]*"[^>]*>'` | 找不到＝先判断是不是 JS 渲染页：JS 页标 `unverifiable_js`，不标"链接已删" |
| 重要页是否有内链承接 | `python3 scripts/site_crawl.py <站点> --out crawl.json` 后 `python3 scripts/link_graph.py --crawl crawl.json` | 零入链重要页清单为空；锚过度优化警告时退出码 1 |
| 有外链的旧 URL | GSC → 链接 → 导出"热门链接页"，逐个 `python3 scripts/redirect_chain.py <URL>` | 状态为 200，或单跳 301 到最相关页 |
| 数据闸门 | 数因子 | ≥4/7 才出数字分；否则写"数据不足" |
| 数据源标签 | 报告每个指标标来源和置信度 | 无来源的数字不写 |

## 六、数字禁令与交付前自查（claude-seo 深读，本套件口径）

- **Common Crawl 单源硬禁令**：CC 是唯一数据源时，任何数字分都不允许；每个本应是数字的位置写字面量 `Not Assessed`。
- **一致性校验**：出报告前核对两类错误——有数字分但无可计分源；标 `source: not-assessed` 的发现却带数字。出错就把违规数字换成 `Not Assessed` 重跑。
- **事实核查**：JSON-LD 缺 `@type` 先查是否 `@graph` 包裹；JS 渲染页的"链接消失"标 `unverifiable_js`；互链检测要把出链与已验证入链源比对。
- **"未找到"三分**：未爬取 / 低于阈值 / 错误。
- **Bing 双站对比**仅当两个属性都在同一 Bing API 账号下验证。
- Keywords Everywhere 的免费能力是否包含来链域数、能否替代 Moz，上一版有说法但没有一手来源（未核）；不依赖它。

## 七、来源

- 框架与阈值：[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-backlinks/SKILL.md`、`skills/seo/references/backlink-quality.md`（MIT）；阈值为源仓库口径
- 数据源层级思路：[zubair-trabzada/dataforseo-claude](https://github.com/zubair-trabzada/dataforseo-claude)
- Google：[垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)、[Disavow 帮助](https://support.google.com/webmasters/answer/2648487?hl=en)
- 数据源：[Moz API](https://moz.com/products/api/pricing)、[Common Crawl Web Graphs](https://commoncrawl.org/web-graphs)、[Open PageRank](https://www.domcop.com/openpagerank/what-is-openpagerank)
