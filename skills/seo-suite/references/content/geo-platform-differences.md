# AI 搜索平台差异事实库

> 建立于 2026-10-09。事实来源：[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `reference/platform-source-selection.md`（一手厂商文档级，2026-10-04 复核）与 [zubair-trzada/geo-seo-claude](https://github.com/zubair-trzada/geo-seo-claude) 平台优化技能。按证据约束改写：厂商文档级事实与社区观察分开标注；未证实处明写。
> 这些是各引擎的**公开行为差异**，不是排名公式。优化建议由此推导，但不应承诺引用结果。

## 一、厂商文档级事实（最可信层）

| 引擎 | 事实 | 级别 |
|---|---|---|
| ChatGPT | `OAI-SearchBot` 供搜索使用；**在 robots.txt 禁它 = 从搜索答案中消失**（导航链接仍可能） | 官方文档 |
| ChatGPT | `ChatGPT-User` 按用户请求抓取，官方声明"robots.txt 规则可能不适用" | 官方文档 |
| Perplexity | `PerplexityBot` 供搜索/链接，**不用于基础模型训练**；`Perplexity-User` "通常无视 robots.txt" | 官方文档 |
| Anthropic | `Claude-SearchBot` 为搜索索引、`Claude-User` 按需抓取；官方声明遵守 robots.txt | 官方文档 |
| Google AIO | 资格 = 已收录 + 可摘要；`nosnippet`/`noindex`/`max-snippet` 会限制 AI 特性 | 官方文档 |
| Google AIO | **`Google-Extended` 不控制 AIO**（只管 Gemini 训练/接地）；AIO 退出开关在 Search Console → 设置（2026-08-31 全量生效） | 官方文档 |
| Google AIO | 无特殊 AI Schema 要求；一次提问可能扇出多次搜索 | 官方文档 |
| Copilot | 与 Bing 共享抓取/收录/排名基础；官方声明"GEO 不保证 grounding 或引用"；IndexNow 可即时提交 | 官方文档 |

## 二、社区观察与相关性研究（次级证据，不外推为算法）

| 引擎 | 观察 | 来源性质 |
|---|---|---|
| Google AIO | 92% 引用来自自然搜索前 10；47% 来自第 5 位以下；~70% 与精选摘要优化重叠；偏好 40–60 词简洁答案块 | 行业研究 |
| ChatGPT | 基于 Bing 索引；引用域中 Wikipedia 47.9%、Reddit 11.3%、YouTube 居前；重实体识别（Wikidata/Crunchbase）；偏好 2000+ 词权威源；每次引 2–4 源 | 行业研究 |
| Perplexity | Reddit 46.7% 居首；社区验证权重最重；每答案 5–15 源（中权站机会多）；**新鲜度强信号** | 行业研究 |
| Gemini | Google 索引 + Google 系资产加权（YouTube 高于一切）；直接消费 Knowledge Graph 与 Schema.org；本地拉 GBP；多模态 | 行业研究 |
| Copilot | LinkedIn/GitHub/Microsoft Learn 加权；meta 描述与精确关键词权重高于 Google | 行业研究 |
| 跨平台 | 仅 11% 域同时被 ChatGPT 与 Google AIO 引用（同一查询） | 行业研究 |

## 三、爬虫分类（决策用）

**引用型 bot（影响搜索答案）**：`OAI-SearchBot`（日频）、`Claude-SearchBot`（按需）、`PerplexityBot`（每周数次）、`Googlebot`、`Applebot`。
**训练型 bot（不影响搜索答案）**：`GPTBot`、`ClaudeBot`、`CCBot`。
**关键推论：禁 `GPTBot` 不阻止 ChatGPT 引用你**——很多站长把两者混为一谈，禁错了对象。Copilot 无独立 bot，读 Bing 索引。

robots 决策速查：

- 想**保留** AI 搜索引用：允许全部引用型 bot；训练型 bot 按品牌偏好决定（不影响引用）。
- 想**退出**某引擎的搜索答案：ChatGPT 禁 `OAI-SearchBot`；Google AIO 用 Search Console 开关（不是 Google-Extended）；Perplexity 禁 `PerplexityBot` 但 `Perplexity-User` 可能无视。
- **没有**"一键全引擎退出"——逐家处理。

## 四、优化侧差异（由上述事实推导的侧重，非保证）

| 平台 | 侧重 |
|---|---|
| Google AIO | 自然排名前 10 是入场券；答案块 40–60 词、先给结论；结构化摘要友好 |
| ChatGPT | 实体建设（Wikidata/Crunchbase 一致性）；2000+ 词权威长文；Bing 收录是前提 |
| Perplexity | Reddit/社区存在感；内容新鲜度（dateModified 与可见日期一致）；中权站机会窗口 |
| Gemini | YouTube 存在感；Schema.org 完整；Knowledge Graph 实体对齐 |
| Copilot | IndexNow 提交；LinkedIn/GitHub 资料；精确关键词在 meta 的权重比 Google 高 |

## 五、引用行为统计（README 或报告可引，均带来源）

- KDD 2024（Princeton/GT/IITD，10K 查询）：GEO 优化可见性 +30–115%；加引号 +41% / 加统计 +33% / 标来源 +28%
- SE Ranking 2025（2.3M 页）：2900+ 词 vs <800 词 = 5.1 vs 3.2 次引用；标题间距 120–180 词 +70% ChatGPT 引用；FAQ 页 4.9 vs 4.4
- Ahrefs（17M 引用）：AI 引用的内容平均新 25.7%；Conductor（13.7K 域）：ChatGPT 占 AI 引荐流量 87.4%
- Kevin Indig（1.2M 答）：44.2% ChatGPT 引用来自页面前 30% 内容
- Seer Interactive：AIO 引用 85% 来自近两年内容
- AirOps 2025：H2/H3 层级 2.8x 引用
- BrightEdge（1M AI 答）：68% 引高权站；43% 引用来自 FAQ 标记页

## 六、区域 AI 搜索平台(2026-10-08 并入,来源类型标注)

Google 系之外的 AI 搜索入口,行为与上表五引擎不同,不能套用同一套 GEO 假设:

| 平台(市场) | 已证实行为 | 来源类型 | 实操含义 |
|---|---|---|---|
| **Alice AI / Нейро(Neuro)**(俄) | 答案来源**取自 Yandex 自然 SERP**,不单独爬取不单独排序;Webmaster 有"Alice 可见面板" | Yandex 官方文档 | 经典 Yandex top-10 即引用前提;退出控制仅 `YandexAdditional` |
| **GigaChat 2**(俄,Sber) | 联网检索+编号脚注引用,**仅聊天 App 内显示,API 不带引用** | 官方 FAQ | 品牌抽查须手工在 App 内做 |
| **Naver AI Briefing / AI Tab**(韩) | 引用**几乎全部来自 Naver 自有生态**(Blog/Cafe/지식iN/Premium);覆盖从 ~3% 升至 ~20%(2026) | 行业(Andgentic/The Egg;20% 非官方) | 韩语 GEO=Naver 生态 GEO 优先,自有站其次;ChatGPT/Gemini 是唯一不需 Naver 资产的通道 |
| **Google AIO(日)** | AIO 出现于 **76.9% 日语查询**(1,459 查询);日语 AI 搜索使用率 21.3%→37.0%(2025-05→2026-02) | 行业(Itera/CyberAgent GEO Lab) | 日语区的 AIO 覆盖比英文区更普遍 |
| **ChatGPT(日)** | 对日语国内查询也把 Reddit 引用排第一;Perplexity 偏知恵袋并转向 Wikipedia JP+note.com | 行业(Ahrefs 经 Nikkei;SiTest) | 日语第三方引用面=Reddit+日生态(note/知恵袋/Wikipedia JP) |
| **引用语言绑定(跨市场)** | 西语查询在 AIO/Copilot 得 83–84% 西语引用;西班牙西语查询 7% 引用去 .es 域 vs 英文查询 1.7% | 行业(Temso/Weglot) | **AI 引用审计必须用目标语言提示跑**;>95% 的日语 AI 答案证据来自第三方站(LLMOチェキ 120 万引用) |
| **Wrtn**(韩)/ **本地阿拉伯助手**(Jais/Fanar) | Wrtn >500 万 MAU;阿拉伯助手存在但 ChatGPT 主导使用 | 行业/未证实(份额) | 二线优先级;GPT-4 在阿拉伯方言上显著退化(arXiv:2305.14976)→ MSA 内容更可靠被引 |
| **ChatGPT(印度)** | ~1 亿周活,ChatGPT 第二大市场(Altman 官方口径);AIO 覆盖英语+印地语;罗马化印地文本使 AI 处理掉 5–12 F1(arXiv 2512.10780) | 官方/研究 | 印度 LLM 可见性优先级仅次于巴西;Hinglish 三种书写都要测 |
| **Coc Cốc AI(越南)** | 本地引擎 ~6%,浏览器自带 AI 聊天机器人 | 官方 Play 页 | 越南的小额但独占的本地 AI 面 |

## 七、来源

- 厂商事实与"禁 GPTBot 不阻止引用"：[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `reference/platform-source-selection.md`、[Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) `docs/ai-bots-reference.md`
- 平台侧重与统计：[zubair-trzada/geo-seo-claude](https://github.com/zubair-trzada/geo-seo-claude) `skills/geo-platform-optimizer/SKILL.md`、[onvoyage-ai/gtm-engineer-skills](https://github.com/onvoyage-ai/gtm-engineer-skills)
- 第六节（区域平台）：Yandex Webmaster 官方文档（Alice 取源、YandexAdditional）；giga.chat 官方 FAQ；Andgentic/The Egg（AI Briefing）；Itera、CyberAgent GEO Lab（日语 AIO）；Ahrefs 经 Nikkei xTREND、SiTest（日语引用行为）；LLMOチェキ（PR Times，120 万引用）；Temso、Weglot（引用语言绑定）；arXiv:2305.14976、arXiv:2510.27543（阿拉伯方言退化）；StatCounter/OpenAI/Chosun（Wrtn、巴西采用）
