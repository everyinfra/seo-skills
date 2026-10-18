# 知识图谱与知识面板指南

用途：理解知识图谱如何影响品牌、组织和人物在搜索中的呈现，以及哪些事可以合规去做。配合 [entity-signal-checklist.md](entity-signal-checklist.md) 使用；GEO 相关结论先看 [geo-evidence.md](../content/geo-evidence.md)。

## 基本认识

以下依据 Google [知识面板帮助](https://support.google.com/knowledgepanel/answer/9163198)（核对 2026-10-18）：

- 知识面板是用户搜索知识图谱里的实体（人物、地点、组织、事物）时出现的信息框。
- 知识面板自动生成，信息来自网络上的多种来源；某些主题 Google 会与提供权威数据的合作方合作；被描述的实体本人或官方代表也可以提供反馈。具体采用哪些来源、怎样合并，由 Google 决定。
- 知识面板会随网络信息变化自动更新；Google 也会考虑实体本人的修改和普通用户的反馈。
- 没有「申请生成知识面板」的入口。已经出现的面板，实体本人或官方代表可以认领并提出修改；不是所有面板都能认领，不能认领时用面板右下角的「反馈」提交修改建议（[Get verified on Google](https://support.google.com/knowledgepanel/answer/7534902)）。
- 商家资料（Business Profile）看起来像知识面板，但面向有门店或服务区域的商家，在 Google 商家资料里认领或创建。

## 查询现状

1. 搜索品牌名、品牌名 + 行业词、创始人姓名，看是否有知识面板、内容是否正确。
2. 用 Knowledge Graph Search API 查询实体 ID、类型和描述。需要你自己的 Google Cloud 项目和 API Key（[API 文档](https://developers.google.com/knowledge-graph)，核对 2026-10-18）：

   ```text
   GET https://kgsearch.googleapis.com/v1/entities:search?query=示例品牌&limit=5&languages=zh&key=YOUR_API_KEY
   ```

   - 可用参数：`query`、`ids`（可重复）、`languages`、`types`（如 `Organization`）、`prefix`、`limit`（默认 20，最大 500）、`indent`（[参考文档](https://developers.google.com/knowledge-graph/reference/rest/v1)）。
   - 官方警告：该 API 只读，**不适合作为生产关键服务**；Google 正把它迁移到 Cloud Enterprise Knowledge Graph，新用户建议用新产品。
   - 结果是 JSON-LD，实体 ID 形如 `kg:/m/0dl567`（官方示例），附 `resultScore`。查不到不等于搜索中不存在相关信息，也不等同于知识面板的实际展示。
3. 记录实体 ID，之后用 `ids=` 参数追踪同一实体的变化。

## Wikidata

- 只为符合收录标准的实体建条目。标准是三选一：有有效的维基媒体站点链接；指向可用公开可靠资料描述的明确实体；满足结构需要（[Wikidata:Notability](https://www.wikidata.org/wiki/Wikidata:Notability)）。
- 每条陈述尽量附可靠来源；与官网事实一致；更名、搬迁、并购等变化及时更新并附来源。
- 遵守社区规则，不建无来源或宣传性质的条目。

## Wikipedia

- 关注度：主题获得独立于主题本身的可靠来源的显著报道（[Wikipedia:Notability](https://en.wikipedia.org/wiki/Wikipedia:Notability)）。
- 利益冲突：有利益冲突的编辑被强烈劝阻直接编辑相关条目，应披露关联，并在讨论页提出修改；有偿编辑必须披露（[Wikipedia:Conflict of interest](https://en.wikipedia.org/wiki/Wikipedia:Conflict_of_interest)，核对 2026-10-18）。
- 条目是否存在由社区决定。把精力放在获得真实的独立报道上，比「做一个 Wikipedia 条目」更可靠（本套件口径）。

## 站内实体标记

- Organization、Person、Product 等使用稳定的 `@id` 全站引用；`sameAs` 指向官方资料页和知识库条目（schema.org 定义：明确指明实体身份的参考网页）。
- 标记内容与可见正文、关于页一致；最小示例见 [schema-templates.md](schema-templates.md)，多类型组合见 [schema-examples.md](schema-examples.md)。

## 定期检查（本套件口径：每季度）

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 知识面板内容 | 无痕窗口搜品牌名，逐字段对照事实表 | 字段全部正确 → 通过；有错 → 走下面「出错时怎么处理」 |
| 实体 ID 稳定 | KG Search API 用 `ids=上次记录的ID` 查询 | 仍返回同一实体 → 通过；消失或变成别的实体 → 查同名混淆 |
| 知识库条目 | 打开 Wikidata 条目的「查看历史」 | 无未经来源的改动；引用链接仍有效 → 通过 |
| 站外事实一致 | 对照官网、社媒、目录 | 名称、地址、成立时间一致 → 通过 |
| AI 回答 | `python3 scripts/oracle_check.py --facts brand.yaml --responses responses.json` | 无冲突 → 通过 |

## 出错时怎么处理

| 问题 | 处理 |
|---|---|
| 知识面板信息错误 | 已认领的通过面板的修改建议流程提交，附可核实来源；不能认领的用「反馈」提交 |
| 与同名实体混淆 | 在所有资料中一致地写明区分信息（全称、地点、行业、官网）；在知识库中补充有来源的区分性陈述 |
| 信息过时 | 先更新一手来源（官网、官方资料页），再更新知识库 |
| 负面报道 | 更新你自己的一手信息；不要试图删除他人的合法报道 |

## 市场差异：各引擎的实体层

Google 知识图谱之外，各市场引擎有自己的实体来源（核对 2026-10-18）：

- **Naver**：「사이트 연관채널」让网站在根页面用 `sameAs` 声明关联的 Naver 服务与社媒频道（[Naver Search Advisor](https://searchadvisor.naver.com/guide/structured-data-channel)）。
- **Yandex**：Яндекс Бизнес 的公司卡片出现在 Яндекс Карты 和搜索中（[Яндекс Бизнес](https://yandex.ru/support/business-priority/ru/)）。
- **百度**：百度百科是常用的实体参照（未核百度官方说明）。
- 实操：实体审计按「该市场主导引擎的实体层」逐个检查，Google 知识图谱只是其一（本套件口径）。旧版本文的「Wikipedia JP 是多家 AI 共同高引实体源（意语区 48.67%）」「Нейро 答案取自自然 SERP」「百度百科是百度 AI 主要信源」没有一手出处，已删除。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · cross-cutting/entity-optimizer/references/knowledge-graph-guide.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/cross-cutting/entity-optimizer/references/knowledge-graph-guide.md)（Apache-2.0）
- 一手资料（核对 2026-10-18）：[Knowledge Graph Search API](https://developers.google.com/knowledge-graph)、[API 参考](https://developers.google.com/knowledge-graph/reference/rest/v1)、[About knowledge panels](https://support.google.com/knowledgepanel/answer/9163198)、[Get verified on Google](https://support.google.com/knowledgepanel/answer/7534902)、[Wikidata:Notability](https://www.wikidata.org/wiki/Wikidata:Notability)、[Wikipedia:Notability](https://en.wikipedia.org/wiki/Wikipedia:Notability)、[Wikipedia:Conflict of interest](https://en.wikipedia.org/wiki/Wikipedia:Conflict_of_interest)、[schema.org/sameAs](https://schema.org/sameAs)
