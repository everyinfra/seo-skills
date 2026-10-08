# llms.txt 指南：格式、校验与生成

> 建立于 2026-10-09。格式要点参考 [zubair-trzada/geo-seo-claude](https://github.com/zubair-trzada/geo-seo-claude)（开源）`skills/geo-llmstxt` 与 [jianruntech/geo-score](https://github.com/jianruntech/geo-score) 的判定规则，交叉 [AnswerEngines spec](https://llmstxt.org)。按本套件的证据约束改写。
> llms.txt 是给 AI 检索系统的内容地图，不是收录保证。没有任何引擎公开承诺"有 llms.txt 就优先引用"。

## 一、llms.txt 是什么、不是什么

- **是**：一个 Markdown 文件，放在站点根路径 `/llms.txt`，告诉来访的 AI 爬虫与检索系统"这个站有什么、去哪看"。提案出自 Jeremy Howard（2024-09），目前是事实上的社区约定。
- **不是**：收录开关。robots.txt 决定"能不能抓"，llms.txt 只是"抓到之后先看什么"的导览。引擎没有义务遵守它。
- **llms-full.txt**：同目录下的加长版（150–500+ 行、30–100+ 页、每页 30–100 词描述）。两者可共存，系统先查 llms.txt。

## 二、格式规范

```
# 站点名称                     ← H1，首行，官方业务名（必填）

> 一句话描述，事实性，无推销水分，200 字符以内（必填）

## Docs                        ← H2 分区（必填至少一个）
- [页面标题](https://example.com/absolute/url)：该页内容的描述，10–30 词
- [另一页](https://example.com/another)：按重要性排序

## Key Facts                   ← 推荐区：成立年 / 总部 / 客户数 / 关键产品
## Contact                     ← 推荐区
```

硬规则：

1. **仅绝对 URL**——相对路径是高频错误。
2. 条目描述 10–30 词；总量 10–30 条；区内按重要性降序。
3. llms.txt 整体 50–150 行、3–6 个分区。常用区名：Docs / Optional / API / Blog / Products / Services / About / Resources / Legal / Contact。
4. 描述要具体："含代码示例的 React Server Components 3000 字完整指南"好过"React 指南"。

## 三、校验严重度表

| 检查 | 严重度 |
|---|---|
| 缺 H1 或没有任何 H2 分区 | **Critical** |
| 条目 <5 条 / 相对 URL / 描述 >200 字符 | High |
| 缺 Key Facts / Markdown 语法破损 | Medium |
| >200 行 / 缺 Contact | Low |

状态码处理：200 → 校验；404 → 生成；403 → 标记配置错误（可能是权限问题不是没有）；301/302 → 跟随后注记。**判定"存在"只看状态码，绝不看响应体积**——定制 404 页也会返回 40–400 KB 的 HTML。

## 四、生成规则

**必收**：主页、About、Pricing、前 3–5 个产品页、Contact。
**跳过**：薄标签页、分页页、登录后页面、法律样板、重复页。
**频率**：活跃博客月更；静态站季更。强内容放前面。
**协调**：llms.txt 里列的页面**不得对 AI 爬虫禁抓**（与 robots.txt 冲突会让一半努力白费）。
**部署后复测**：确认无重定向、可直连。

## 五、判定（供审计用，0–5 分参考 geo-score 的分层）

- 0 = 无文件
- 2 = 存在且 >200 字符（有标题+链接）
- 4 = 有站点定义段落（H1+blockquote 完整）
- 5 = 有 ≥2 个主题分区且分区含链接
- Bonus：llms-full.txt 存在（+2）；llms.txt 内链接到非根路径的完整版也可接受

## 六、常见错误

1. 相对 URL（`/docs` 而非 `https://site.com/docs`）。
2. 描述写成营销口号（"业界领先的革命性平台"）——AI 要的是内容说明。
3. 与 robots.txt 矛盾（列了页又禁了 AI 爬虫）。
4. 一次生成永不更新——链接腐烂后比没有更糟。
5. 把 llms.txt 当 sitemap 复制品（500+ 行塞满每个 URL）——用 llms-full.txt 承载全量。

## 七、来源

- 格式与严重度：[zubair-trzada/geo-seo-claude](https://github.com/zubair-trzada/geo-seo-claude) `skills/geo-llmstxt/SKILL.md`
- 状态码判定与"不看体积"：[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `SKILL.md`
- 原始提案：[llmstxt.org](https://llmstxt.org)
