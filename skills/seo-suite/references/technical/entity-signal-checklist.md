# 实体信号核查清单

用途：判断搜索引擎和 AI 产品能否把你的品牌、组织、人物或产品识别为一个清楚、一致的实体。用于实体审计（输出模板见 [entity-audit.md](../../templates/audit/entity-audit.md)）和 GEO 工作的前置检查。

先读 [geo-evidence.md](../content/geo-evidence.md)：实体信号帮助被正确识别，不保证知识面板、排名或 AI 引用。

## 核查顺序

1. **站内基础**：完全可控，先做。
2. **外部资料**：部分可控，只能核实和补全真实信息。
3. **搜索与 AI 中的呈现**：不可控，只观测。

## 一、站内基础

- **名称一致**：官方全称、简称、中英文名在标题、页脚、关于页、结构化数据中一致。
- **关于页**：成立时间、业务范围、所在地、负责人、联系方式等可核实的事实，并与外部资料一致。
- **Organization 标记**（或更具体的子类型）：name、url、logo、sameAs、联系方式等，只写真实存在的内容。用稳定的 `@id`（如 `https://example.com/#organization`）全站复用，避免每页声明互相矛盾的版本。
- **人物**：作者页或团队页；Person 标记与可见署名一致，`worksFor` 指向组织的 `@id`。
- **产品**：名称、版本、价格等与产品页可见内容一致。
- **sameAs**：只链接你拥有或已官方认领的资料页（官方社媒账号、知识库条目、官方目录页），不要链接无关或未核实的页面。

## 二、外部资料

- **知识库**：符合收录标准时可以有 Wikidata 条目；Wikipedia 条目需要多个独立可靠来源证明关注度，且有利益冲突规则，关联方直接撰写或推广通常不被接受。详见 [knowledge-graph-guide.md](knowledge-graph-guide.md)。
- **目录与平台资料**：行业目录、应用商店、代码托管、地图商家资料等，信息与官网一致。
- **独立第三方证据**：媒体报道、独立评测、客户案例。自己在多个平台转载同一篇文章不算独立证据。
- **出现不一致**：先改自己可控的来源，再按各平台流程申请更正，保留证据。

## 三、搜索与 AI 中的呈现（观测）

- 品牌词搜索：官网是否排在前面、站点名称是否正确、是否有知识面板以及内容是否正确。
- 知识图谱：可用 Knowledge Graph Search API 按名称查询（需要你自己的 Google Cloud API Key），方法见 knowledge-graph-guide.md。
- AI 产品：用固定问题（「[品牌] 是做什么的」「[品牌] 的总部在哪里」等）抽样，记录回答是否正确、引用了哪些来源。只作观测记录。

## 优先级判断

| 情况 | 优先动作 |
|---|---|
| 站内名称或事实互相矛盾 | 先统一站内，再处理外部 |
| 站内一致，但外部官方资料缺失 | 补全你拥有的官方资料页；符合标准时再考虑知识库条目 |
| 外部资料有错误 | 走对应平台的更正流程，附可核实来源 |
| 全部一致但没有知识面板 | 继续积累真实的独立报道；知识面板不能申请生成 |

## 交付

- 实体事实表：名称、别名、官网、成立时间、总部、负责人、官方资料页，每项注明来源与核对日期。
- 不一致清单和修正建议，按可控程度排序。
- 结构化数据修改建议，附最小 JSON-LD（写法见 [schema-templates.md](schema-templates.md)）。
- 观测记录和复查时间。

## 常见误区

- 为了「实体信号」编造奖项、媒体报道或评分。
- sameAs 链到未认领的第三方页面甚至竞品页面。
- 以为加了 Organization 标记就会出现知识面板。
- 批量注册低质量目录。

## 市场差异:实体源按市场换(拉平轮;Wikidata/Crunchbase 是英文基线)

| 市场 | 实体权威源(替代/补充 Wikidata) |
|---|---|
| 韩语区 | **연관채널 sameAs 实体图谱**(官方域名清单:네이버TV/블로그/스마트스토어/지식iN/치지직+당근/Threads/Instagram/YouTube/Tistory/TikTok/Facebook/X)——Naver 官方机制,Google 无对应 |
| 俄语区 | Яндекс Бизнес 卡片+Справочник;юридические данные(ИНН/ОГРН)是实体信任层(Vega 专家性信号) |
| 中文 | 百度百科词条+百家号(百度 AI 引用前提);各 AI 引擎信源池见中文指南 |
| 日语区 | Wikipedia JP+法人番号/会社概況页;業界ポータル NAP 一致(食べログ等) |
| 德语区 | Impressum(§5 DDG)+Handwerkskammer 登记(手工业)——法定页=实体信任基件 |
| 法语区 | mentions légales(LCEN 强制,含托管商)+societe.com/Pappers 注册数据 |
| 意大利 | **P.IVA→Registro Imprese**(ATECO 码+省,公开 API 可查) |
| 巴西 | CNPJ 页脚+职业委员会注册号(OAB/CRM) |
| 印度 | JustDial/IndiaMART 商户条目(聚合器=实体层) |
| 荷兰 | KvK(商会)号入 NAP |

**通用**:40–60 词规范实体简介全平台逐字重复(法区规则,反向于长描述应变化);JSON-LD description 与事实卡逐字一致。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · cross-cutting/entity-optimizer/references/entity-signal-checklist.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/cross-cutting/entity-optimizer/references/entity-signal-checklist.md)（Apache-2.0）
- 一手资料：[Google：Organization 结构化数据](https://developers.google.com/search/docs/appearance/structured-data/organization)、[Google：站点名称](https://developers.google.com/search/docs/appearance/site-names)、[schema.org sameAs](https://schema.org/sameAs)、[Knowledge Graph Search API](https://developers.google.com/knowledge-graph)
