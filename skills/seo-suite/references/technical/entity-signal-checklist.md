# 实体信号核查清单

用途：判断搜索引擎和 AI 产品能否把你的品牌、组织、人物或产品识别为一个清楚、一致的实体。用于实体审计（输出模板见 [entity-audit.md](../../templates/audit/entity-audit.md)）和 GEO 工作的前置检查。

先读 [geo-evidence.md](../content/geo-evidence.md)：实体信号帮助被正确识别，不保证知识面板、排名或 AI 引用。Google 没有公布「实体信号」的权重；本清单的顺序和优先级是本套件口径。

## 核查顺序（本套件口径）

1. **站内基础**：完全可控，先做。
2. **外部资料**：部分可控，只能核实和补全真实信息。
3. **搜索与 AI 中的呈现**：不可控，只观测。

## 一、站内基础

- **名称一致**：官方全称、简称、中英文名在标题、页脚、关于页、结构化数据中一致。Google 要求 Organization 的 `name`/`alternateName` 与站点名称一致（[Organization](https://developers.google.com/search/docs/appearance/structured-data/organization)，核对 2026-10-21）。
- **关于页**：成立时间、业务范围、所在地、负责人、联系方式等可核实的事实，与外部资料一致。
- **Organization 标记**（或更具体的子类型）：放在首页或一个介绍页即可，不需要每页都放；Google 没有必填属性，建议写 `name`、`alternateName`、`address`、`telephone`、`url`、`logo`（至少 112×112px）、`sameAs` 等真实存在的内容（同上）。用稳定的 `@id`（如 `https://example.com/#organization`）全站引用。
- **人物**：作者页或团队页；Person 标记与可见署名一致，`worksFor` 指向组织的 `@id`。Article 的 `author.url` 指向唯一标识作者的页面（[Article](https://developers.google.com/search/docs/appearance/structured-data/article)）。
- **产品**：名称、版本、价格等与产品页可见内容一致。
- **sameAs**：schema.org 定义为「明确指明该实体身份的参考网页的 URL」，例如维基百科页、Wikidata 条目或官网（[schema.org/sameAs](https://schema.org/sameAs)）；Google 的例子是社交媒体或点评网站上的组织主页。本套件口径：只放你拥有、已认领或确实描述同一实体的资料页。

## 二、外部资料

- **知识库**：Wikidata 条目要满足至少一条收录标准：有有效的维基媒体站点链接，或指向可用公开可靠资料描述的明确实体，或满足结构需要（[Wikidata:Notability](https://www.wikidata.org/wiki/Wikidata:Notability)）。Wikipedia 条目要求有独立可靠来源的显著报道；有利益冲突的人被强烈劝阻直接编辑，应披露关联并在讨论页提出修改（[关注度](https://en.wikipedia.org/wiki/Wikipedia:Notability)、[利益冲突](https://en.wikipedia.org/wiki/Wikipedia:Conflict_of_interest)，核对 2026-10-21）。详见 [knowledge-graph-guide.md](knowledge-graph-guide.md)。
- **目录与平台资料**：行业目录、应用商店、代码托管、地图商家资料等，信息与官网一致。
- **独立第三方证据**：媒体报道、独立评测、客户案例。自己在多个平台转载同一篇文章不算独立证据。
- **出现不一致**：先改自己可控的来源，再按各平台流程申请更正，保留证据。

## 三、搜索与 AI 中的呈现（观测）

- 品牌词搜索：官网是否排在前面、站点名称是否正确、是否有知识面板以及内容是否正确。
- 知识图谱：用 Knowledge Graph Search API 按名称查询，需要你自己的 Google Cloud API Key；官方提示该 API 不适合作为生产关键依赖（方法见 [knowledge-graph-guide.md](knowledge-graph-guide.md)）。
- AI 产品：用固定问题（「[品牌] 是做什么的」「[品牌] 的总部在哪里」等）抽样，记录回答是否正确、引用了哪些来源。工具与采样纪律见 [brand-serp-methodology.md](brand-serp-methodology.md)。

## 优先级判断（本套件口径）

| 情况 | 优先动作 |
|---|---|
| 站内名称或事实互相矛盾 | 先统一站内，再处理外部 |
| 站内一致，但外部官方资料缺失 | 补全你拥有的官方资料页；符合标准时再考虑知识库条目 |
| 外部资料有错误 | 走对应平台的更正流程，附可核实来源 |
| 全部一致但没有知识面板 | 继续积累真实的独立报道；知识面板由 Google 自动生成，不能申请生成 |

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 站内名称一致 | `curl -s https://example.com/ \| grep -o '<title>[^<]*'`；对照页脚、关于页、JSON-LD 的 `name`/`alternateName` | 各处写法一致 → 通过 |
| Organization 标记 | `python3 scripts/schema_lint.py https://example.com/`；Rich Results Test | 无 CRITICAL；`@id` 稳定；logo ≥112×112px → 通过 |
| sameAs 指向 | 逐个打开 `sameAs` 链接 | 每个都确实描述同一实体，且为自有、已认领或权威条目 → 通过 |
| 实体事实页 | `python3 scripts/grounding_page.py --facts brand.yaml --check 现有页面.md` | 11 条检查无 FAIL（MANUAL 项人工复核）→ 通过 |
| 知识图谱 ID | `curl -s "https://kgsearch.googleapis.com/v1/entities:search?query=示例品牌&limit=5&key=KEY"` | 记录返回的 `@id`（形如 `kg:/m/…`）与 `resultScore`；查不到不等于失败 |
| AI 回答正确性 | `python3 scripts/oracle_check.py --facts brand.yaml --responses responses.json` | 无数字、日期、布尔冲突 → 通过 |
| 法定身份信息（按市场） | 对照下表逐项看页脚或法律页 | 法定项齐全且与注册信息一致 → 通过 |

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

## 市场差异：可核实的身份信息与实体源

英文市场常用 Wikidata、Crunchbase 作实体参照。其他市场先补下表里有一手依据的项目（核对 2026-10-21）：

| 市场 | 可核实的身份信息 / 实体源 | 依据 |
|---|---|---|
| 韩国 | Naver「사이트 연관채널」：在网站根页面用 Person 或 Organization 标记写 `name`、`url`、`sameAs`（均必填），列出关联频道。当前识别的频道：네이버TV、블로그、스마트스토어、지식iN、치지직，以及 당근、Threads、Instagram、YouTube、카카오스토리、카카오톡 채널、Tistory、TikTok、Facebook、X。Naver 说明不保证展示，支持频道可能变动，以页面当前列表为准 | [Naver Search Advisor](https://searchadvisor.naver.com/guide/structured-data-channel) |
| 俄罗斯 | Яндекс Бизнес：免费添加公司信息，让公司出现在 Яндекс Карты 和搜索中 | [Яндекс Бизнес](https://yandex.ru/support/business-priority/ru/) |
| 德国 | Impressum：商业性数字服务须长期提供名称、地址、法律形式、代表人、电子邮件、商业登记及编号、受监管职业的所属行业协会、增值税号等 | [§5 DDG](https://www.gesetze-im-internet.de/ddg/__5.html) |
| 法国 | mentions légales：企业名称、法律形式、注册号（RCS/RNE）、增值税号、联系方式，以及托管商的名称、地址和电话 | [service-public.gouv.fr](https://entreprendre.service-public.gouv.fr/vosdroits/F37351) |
| 意大利 | 增值税号（partita IVA）须写在网站首页 | [DPR 633/1972 第 35 条](https://www.agenziaentrate.gov.it/portale/documents/20143/279316/Articol1+35++e+35+ter_Dpr+633_1972_articolo35_35ter.pdf) |
| 巴西 | 电商网站须醒目展示企业名称和 CPF/CNPJ 编号 | [Decreto 7.962/2013 第 2 条](https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2013/decreto/d7962.htm) |
| 荷兰 | KVK 编号须出现在信函、报价、发票、网站和商务邮件上 | [KVK](https://www.kvk.nl/over-het-handelsregister/kvk-nummer-alles-wat-je-moet-weten/) |
| 日本 | 法人番号：国税厅网站公开商号、所在地、法人番号三项，可用于核对 | [国税厅法人番号公表サイト](https://www.houjin-bangou.nta.go.jp/) |
| 中国 | 百度百科词条、百家号（未核百度官方规则；按百度百科编辑规则操作） | 未核 |
| 印度 | JustDial、IndiaMART 等商户目录（未核平台规则，按真实信息填写） | 未核 |

旧版本文的「40–60 词实体简介全平台逐字重复」「百度百科是百度 AI 引用前提」「ИНН/ОГРН 是 Vega 专家性信号」没有一手出处，已删除。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · cross-cutting/entity-optimizer/references/entity-signal-checklist.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/cross-cutting/entity-optimizer/references/entity-signal-checklist.md)（Apache-2.0）
- 一手资料（核对 2026-10-21）：[Google：Organization 结构化数据](https://developers.google.com/search/docs/appearance/structured-data/organization)、[Google：站点名称](https://developers.google.com/search/docs/appearance/site-names)、[schema.org sameAs](https://schema.org/sameAs)、[Knowledge Graph Search API](https://developers.google.com/knowledge-graph)、[Wikidata:Notability](https://www.wikidata.org/wiki/Wikidata:Notability)、[Wikipedia:Notability](https://en.wikipedia.org/wiki/Wikipedia:Notability)、[Wikipedia:Conflict of interest](https://en.wikipedia.org/wiki/Wikipedia:Conflict_of_interest)；各市场依据见表内链接。
