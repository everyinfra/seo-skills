# 结构化数据：按页面类型组合

> 涉及 FAQPage 或 AI 引用的判断，先读 [geo-evidence.md](../content/geo-evidence.md)。

## 用途

一个页面需要同时描述多个实体时读，例如文章页既有文章本身，又有面包屑、作者和发布者。单个类型怎么选、查哪份属性文档，见 [schema-templates.md](schema-templates.md)；验证见 [validation-guide.md](validation-guide.md)。

## 一、组合原则

1. **用 `@graph` 放在同一个脚本里。** 同一页面的多个节点放进一个 `@graph` 数组，节点之间用 `{"@id": "…"}` 互相引用，不要把同一实体在多处嵌套重复写。
2. **一个实体在一个页面里只声明一次。** 多个插件、主题或前端组件各输出一份 Organization 很常见：先列出所有输出结构化数据的来源（CMS 插件、主题、跟踪代码管理器、前端组件），指定唯一负责方。
3. **`@id` 全站稳定。** 用规范 URL 加片段命名，例如 `https://example.com/#organization`、`https://example.com/guides/robots-check#article`；不带跟踪参数，与 canonical 一致，改版时也不要变。
4. **每个页面的数据要能独立成立。** `@id` 是标识符，不能指望搜索引擎跨页面去解析它（这是工程判断，不是 Google 的书面承诺）。站点级实体的完整信息放在首页；其他页面的 `@graph` 里保留一个用同一 `@id`、只含 name、url 等少量字段的精简节点，内容与首页一致。
5. **主实体只有一个。** 文章页的主角是文章，商品页的主角是商品；Organization、WebSite 只是被引用的配角。

## 二、按页面类型的常见组合

| 页面 | 主实体 | 常见组合 |
|---|---|---|
| 首页 | Organization、WebSite | WebSite 的 `publisher` 指向 Organization |
| 文章页 | Article / BlogPosting | + BreadcrumbList；`author` 指向作者 Person；`publisher` 指向 Organization |
| 作者页 | Person（可放在 ProfilePage 里） | Person 的 `@id` 供全站文章的 `author` 引用 |
| 商品详情页 | Product + Offer | + BreadcrumbList；`brand` 可指向品牌实体；评分只在页面上有真实评价时才加 |
| 分类 / 列表页 | 可用 CollectionPage 描述页面 | + BreadcrumbList；不要把列表页标成单个 Product |
| 门店页 | LocalBusiness 的具体子类型 | + BreadcrumbList；`parentOrganization` 指向总公司的 Organization |
| 软件 / SaaS 产品页 | SoftwareApplication 或 Product | 评分要求见 [schema-templates.md](schema-templates.md) |

WebPage 节点（`isPartOf`、`breadcrumb` 等关系）可以用来表达页面结构，但 Google 富结果不要求它；加不加按团队维护成本决定。

## 三、组合示例（自写，文章页）

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://example.com/#organization",
      "name": "示例品牌",
      "url": "https://example.com/"
    },
    {
      "@type": "WebSite",
      "@id": "https://example.com/#website",
      "name": "示例品牌",
      "url": "https://example.com/",
      "publisher": { "@id": "https://example.com/#organization" }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://example.com/guides/robots-check#breadcrumb",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "指南", "item": "https://example.com/guides/" },
        { "@type": "ListItem", "position": 2, "name": "如何核对 robots.txt 规则" }
      ]
    },
    {
      "@type": "BlogPosting",
      "@id": "https://example.com/guides/robots-check#article",
      "headline": "如何核对 robots.txt 规则",
      "datePublished": "2026-03-02T09:00:00+08:00",
      "mainEntityOfPage": "https://example.com/guides/robots-check",
      "isPartOf": { "@id": "https://example.com/#website" },
      "author": { "@id": "https://example.com/authors/zhang-san#person" },
      "publisher": { "@id": "https://example.com/#organization" }
    },
    {
      "@type": "Person",
      "@id": "https://example.com/authors/zhang-san#person",
      "name": "张三",
      "url": "https://example.com/authors/zhang-san"
    }
  ]
}
```

要点：Organization 和 WebSite 在这里是精简节点，完整信息在首页；面包屑最后一级是当前页，可以不写 `item`；所有值都必须能在页面上看到。

## 四、实施要点

- 可见内容和 JSON-LD 从同一份数据生成，避免漂移。
- 把 JSON 写进 `<script>` 时，按所用框架当前文档做安全序列化，至少把 `<` 转义为 `\u003c`，防止内容里的 `</script>` 截断脚本或造成注入。
- 同一实体不要同时用 microdata 和 JSON-LD 各写一份；确需并存时，内容必须一致。
- 验证时除了看有没有报错，还要看节点之间的引用是否都能对上（见 [validation-guide.md](validation-guide.md)）。

## 常见误区

- 每个组件各输出一份 Organization，`@id` 不同或内容互相矛盾。
- `@id` 用了带参数的 URL，或随改版变化。
- 以为 `@id` 引用能跨页面解析，于是单页数据残缺。
- 为了让「图谱更完整」，加入页面上没有的实体或属性。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/schema-markup/references/schema-examples.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/schema-markup/references/schema-examples.md)（MIT）
- 一手资料：[结构化数据简介](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)、[结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)、[Article](https://developers.google.com/search/docs/appearance/structured-data/article)、[Breadcrumb](https://developers.google.com/search/docs/appearance/structured-data/breadcrumb)、[Organization](https://developers.google.com/search/docs/appearance/structured-data/organization)、[JSON-LD 1.1（W3C）](https://www.w3.org/TR/json-ld11/)、[schema.org](https://schema.org/)
