# 知识图谱与知识面板指南

用途：理解知识图谱如何影响品牌、组织和人物在搜索中的呈现，以及哪些事可以合规去做。配合 [entity-signal-checklist.md](entity-signal-checklist.md) 使用；GEO 相关结论先看 [geo-evidence.md](../content/geo-evidence.md)。

## 基本认识

- 知识图谱是搜索引擎维护的实体与关系数据库；知识面板是它在搜索结果中的一种呈现。
- 信息来源包括公开网页、开放知识库（如 Wikidata）、授权数据以及实体本人或机构的反馈。具体采用哪些来源、如何合并，由搜索引擎决定。
- 没有「申请生成知识面板」的入口。能做的是让真实信息一致、可核实、被独立来源记录。已经有知识面板的实体，可以按 Google 的流程认领并提交修改建议。

## 查询现状

1. 搜索品牌名、品牌名 + 行业词、创始人姓名，看是否有知识面板、内容是否正确。
2. 用 Knowledge Graph Search API 查询实体的 ID、类型和描述。需要你自己的 Google Cloud 项目和 API Key，示例中的 Key 是占位符：

   ```text
   GET https://kgsearch.googleapis.com/v1/entities:search?query=示例品牌&limit=5&key=YOUR_API_KEY
   ```

   这个 API 只返回有限字段，查不到不等于搜索中不存在任何相关信息，也不等同于知识面板的实际展示。
3. 记录实体 ID（形如 `/m/...` 或 `/g/...`），之后用它追踪同一实体的变化。

## Wikidata

- 只为符合收录标准的实体建条目；每条陈述尽量附可靠来源。
- 与官网事实保持一致；更名、搬迁、并购等变化及时更新并附来源。
- 遵守社区规则，披露利益关联；不要创建无来源或宣传性质的条目。

## Wikipedia

- 条目需要满足关注度要求：多个独立、可靠、有一定深度的来源报道。
- 利益冲突规则：与主题有关联的人不宜直接撰写或大幅编辑条目，应在讨论页提出修改建议并披露关联。
- 条目是否存在由社区决定。把精力放在获得真实的独立报道上，比「做一个 Wikipedia 条目」更可靠。

## 站内实体标记

- Organization、Person、Product 等使用稳定的 `@id` 全站复用；`sameAs` 指向官方资料页和知识库条目。
- 标记内容与可见正文、关于页一致；最小示例见 [schema-templates.md](schema-templates.md)，多类型组合见 [schema-examples.md](schema-examples.md)。

## 定期检查（建议每季度）

- 品牌词搜索结果与知识面板内容。
- 知识库条目是否被改动，引用的来源是否仍然有效。
- 官网、社媒、目录中的事实是否一致。
- AI 产品对品牌基本事实的回答是否正确（抽样记录）。

## 出错时怎么处理

| 问题 | 处理 |
|---|---|
| 知识面板信息错误 | 已认领的通过面板的修改建议流程提交，附可核实来源；未认领的提交反馈 |
| 与同名实体混淆 | 在所有资料中一致地写明区分信息（全称、地点、行业、官网）；在知识库中补充有来源的区分性陈述 |
| 信息过时 | 先更新一手来源（官网、官方资料页），再更新知识库 |
| 负面报道 | 更新你自己的一手信息；不要试图删除他人的合法报道 |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · cross-cutting/entity-optimizer/references/knowledge-graph-guide.md](https://github.com/aaron-he-zhu/seo-geo-claude-skills/blob/v9.9.12/cross-cutting/entity-optimizer/references/knowledge-graph-guide.md)（Apache-2.0）
- 一手资料：[Knowledge Graph Search API](https://developers.google.com/knowledge-graph)、[Google 知识面板帮助](https://support.google.com/knowledgepanel)、[Wikidata 简介](https://www.wikidata.org/wiki/Wikidata:Introduction)、[Wikidata 收录标准](https://www.wikidata.org/wiki/Wikidata:Notability)、[Wikipedia 关注度](https://en.wikipedia.org/wiki/Wikipedia:Notability)、[Wikipedia 利益冲突](https://en.wikipedia.org/wiki/Wikipedia:Conflict_of_interest)
