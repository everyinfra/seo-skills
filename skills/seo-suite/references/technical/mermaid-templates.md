# 用 Mermaid 画站点结构与内链

用途：在方案里用 Mermaid 图说明站点层级、专题集群、内链流向和改版前后对比。Mermaid 能直接在很多 Markdown 渲染器中显示，也便于和文字方案一起版本管理。

## 写法约定

- 节点 ID 用简短英文（`home`、`blog`），显示文字放在方括号里；含特殊字符或中文等 Unicode 文本时加双引号：`home["首页 /"]`（[Mermaid 流程图语法](https://mermaid.js.org/syntax/flowchart.html)）。节点 ID 或文字里单独的小写 `end` 会破坏流程图语法，写成 `End` 或加引号。
- 需要展示 URL 时写在显示文字里：`pricing["定价 /pricing"]`。
- 用 `classDef` 标颜色，并在图下方写图例；不要只靠颜色区分含义。
- 一张图控制在二三十个节点以内，超过就拆成总览图和分区图。
- 实线表示导航或层级关系，虚线表示正文中的上下文链接。

## 示例一：站点层级

```mermaid
flowchart TD
  home["首页 /"] --> product["产品 /product"]
  home --> pricing["定价 /pricing"]
  home --> blog["博客 /blog"]
  home --> docs["文档 /docs"]
  product --> featA["功能 A /product/feature-a"]
  product --> featB["功能 B /product/feature-b"]
  blog --> catSeo["分类：SEO /blog/seo"]
  docs --> start["快速开始 /docs/start"]
```

## 示例二：专题集群与内链

```mermaid
flowchart LR
  pillar["支柱页：技术 SEO 指南"]
  c1["抓取与索引"]
  c2["结构化数据"]
  c3["页面性能"]
  pillar --> c1
  pillar --> c2
  pillar --> c3
  c1 --> pillar
  c2 --> pillar
  c3 --> pillar
  c1 -.-> c2
  c3 -.-> c1
  classDef hub fill:#dbeafe,stroke:#1d4ed8;
  class pillar hub;
```

图例：蓝色为支柱页；实线为支柱页与子页的双向链接，虚线为子页之间的上下文链接。

## 示例三：改版前后对比

```mermaid
flowchart TD
  subgraph before["改版前"]
    b_home["首页"] --> b_all["全部文章（单一列表）"]
  end
  subgraph after["改版后"]
    a_home["首页"] --> a_hub1["专题：技术 SEO"]
    a_home --> a_hub2["专题：内容策略"]
    a_hub1 --> a_post1["文章 ×N"]
    a_hub2 --> a_post2["文章 ×N"]
  end
```

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 语法可渲染 | 把代码块粘进 [Mermaid Live Editor](https://mermaid.live)；或在 Node 里用 `mermaid.parse()` 解析（本文三个示例 2026-10-21 用 mermaid 11.4.1 解析均通过，图类型为 flowchart-v2） | 无语法错误 → 通过 |
| 规模 | 数节点 | 一张图 ≤ 约 30 个节点（本套件口径） |
| 图例 | 图下方有文字图例，颜色以外还有线型或标签区分 | 有 → 通过 |
| URL 变更 | 图中出现的新旧 URL 在文字里有逐条重定向清单 | 有 → 通过 |

## 配套文字

每张图下面写清：图表达了什么、和现状的差异、涉及哪些 URL 变更（需要重定向的列表单独给出，做法见 [http-status-codes.md](http-status-codes.md)）。结构原则见 [link-architecture-patterns.md](link-architecture-patterns.md) 和 [site-type-templates.md](site-type-templates.md)。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/site-architecture/references/mermaid-templates.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/site-architecture/references/mermaid-templates.md)（MIT）
- 一手资料：[Mermaid 文档](https://mermaid.js.org/intro/)
