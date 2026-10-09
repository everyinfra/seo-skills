# 可引用性打分（内容能否被 AI 引用）

> 建立于 2026-10-09。框架参考 [zubair-trzada/geo-seo-claude](https://github.com/zubair-trzada/geo-seo-claude) `geo-citability` 技能与 [jianruntech/geo-score](https://github.com/jianruntech/geo-score) rubric v1.1，按本套件证据约束改写。
> 打分衡量的是内容**形状**是否便于引用，不是引用结果本身——好分数不保证被引。

## 一、五维块级打分（0–100）

| 维度 | 权重 | 看什么 |
|---|---|---|
| 答案块质量 | 30% | 段落是否直接回答一个可提问的问题；先结论后展开 |
| 段落自含性 | 25% | 不依赖上文代词/省略也能独立成立（抽取后仍可读） |
| 结构可读性 | 20% | 标题层级、列表、定义先行；H2/H3 层级使引用概率 2.8x（AirOps 2025） |
| 统计密度 | 15% | 有源数字的密度；引用统计 +33% 可见性（KDD 2024） |
| 独特与原始数据 | 10% | 自有一手数据/图表/表格，别处没有 |

**最优被引段落形态**：134–167 词、自含、富事实、定义先行（"X 是……"）。低于 60 词的信息块建议重写或并入邻近段。

**覆盖度**：整页打分 = 得分 >70 的块占比。单块高分不够，要看页面整体的可抽取密度。

## 二、AI 就绪度分层审核（站点级，100 分参考 geo-score v1.1 结构）

**Reachable（15 分）**——进不来一切免谈：

- robots 对 10 个主流检索 UA 的政策（显式 allow 5 / 仅无禁 3 / 禁 0）
- 活体探测：发真实 bot UA 访问，403/429/5xx/挑战页 = 拦（robots 宽松但 WAF 拦截是常见暗坑）
- SSR/首屏可解析
- **任一门为 0 → 总分封顶 40%**（进不来就谈不上可引用）

**Understandable（22 分）**：sitemap+lastmod 4 / llms.txt 5 / Organization+WebSite schema 6 / BreadcrumbList 3 / 页型 schema 4

**Content Citability（35 分）**：自含答案段 9 / 标题匹配提问意图 7 / 新鲜度 6（dateModified 必须与可见日期一致，造假扣全分）/ 有源统计 7（最高档=可点击可核验）/ 具名可验证作者 6（署名解析到真实身份页）

**Brand Credibility（18 分）**：第三方目录 4 / 独立提及 4 / Knowledge Graph 实体 4 / sameAs 可解析 3 / 视频多模态 3

**Answer Fit（10 分）**：抽取型内容 4 / 覆盖 10 个真实买家问题 4 / 中文引擎就绪 2

分档：Leading 83+ / Solid 66+ / Growing 51+ / Early 31+ / Not started。

## 三、方法纪律（本套件强制）

1. **抽样协议**：恰好 8 个 URL——主页、2 个产品页、2 个文档页、3 个近期内容页。不多不少，保证跨站可比。
2. **三态标注**：每项 scored / unobservable / not_applicable。不可观测不等于 0 分。
3. **测量与整改分开报告**：就绪度分数与实测引用表现是两个数，不合并成一个"AI 可见度"。
4. **引用数据带不确定度**：报告实测引用时附 95% CI 和样本量 n。
5. 不承诺分数与被引的因果关系——分数是整改优先级工具。

## 四、作者信号（E-E-A-T 的可验证子集）

可机器验证的部分（区别于"内容质量"这种主观项）：

- 署名存在且解析到身份页（作者页有 sameAs 指向 LinkedIn/ORCID 等）
- dateModified 与页面可见日期一致
- 统计带可点击来源
- 组织 sameAs 全部可解析、无死链
- 有原始数据产物（表格/图/数据集）而非纯转述

## 五、来源

- 五维块级与 134–167 词最优段：[zubair-trzada/geo-seo-claude](https://github.com/zubair-trzada/geo-seo-claude) `skills/geo-citability/SKILL.md`
- 站点级分层/闸门/三态/抽样协议：[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `rubric/v1.1.md`
- 47 方法库（9 个出自 KDD 2024）：[Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) `docs/geo-methods.md`

## 市场差异:单位换算与阈值(拉平轮;英文基线的"词"不是通用单位)

**134–167 词的最优引用段是英文衍生值**——其他语言按等价信息量换算:

| 市场 | 计量单位 | 可引用块阈值 |
|---|---|---|
| 中文 | 字 | 答案块 40–60 字;FAQ 答 80–200 字;句 15–25 字(>35 难解析) |
| 日语 | 全角字 | 答案块按体裁(MEO 500–1,200/一般 1,500–3,500/支柱 7,000–12,000);句 ≤25 词 |
| 泰语 | 字素+分词 | 先 `Intl.Segmenter("th")` 再谈密度;句 ≤25 词 |
| 俄语 | 词 | 答案首屏 40–60 词(Алиса 显 ~5 行) |
| 印尼 | 字 | 结论前置 40–60 字;对比表 ≥5 维 |
| 韩语 | 全角字 | description ≤80;疑问式 h2 ≥50%(t0mmy 规则,越区同) |

**跨市场通用**:有源数字+定义块+对比块优于纯问答格式(中文实测:纯问答 −5.7%);评分时剥离导航/页脚再算(法区规则,通用)。完整阈值表见 multilingual-workflow 第四节。
