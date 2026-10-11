# findings: rankability

7 项发现;文末 envelope-category-v1 注释行为机器回读数据(--resume 依赖,勿删)

| rule_id | severity | affected | title |
|---|---|---|---|
| description | WARN | 3/3 | description 缺失/越限 |
| schema | WARN | 3/3 | 无 JSON-LD |
| title | WARN | 3/3 | title 缺失/越限 |
| h1 | WARN | 1/3 | H1 缺失/多个 |
| headings | WARN | 1/3 | 标题层级跳级 |
| rendering | INFO | 3/3 | 渲染依赖过重 |
| semantic-html | INFO | 3/3 | 语义 HTML 比值低 |

## 明细

### description [WARN] 3/3 URL
- description: 命中 3/3 URL(100%);最常见表现: 247 chars 超上限 155
- recommendation: 补/改 description:~155 字符,含利益点与 CTA
- affected_urls(3):
  - https://github.com/everyinfra/seo-skills
  - https://github.com/everyinfra/seo-skills/blob/main/README.md
  - https://github.com/everyinfra/jev-radar

### schema [WARN] 3/3 URL
- description: 命中 3/3 URL(100%);最常见表现: 无 JSON-LD
- recommendation: 补 JSON-LD(按页型选 Organization/Article/Breadcrumb 等)
- affected_urls(3):
  - https://github.com/everyinfra/seo-skills
  - https://github.com/everyinfra/seo-skills/blob/main/README.md
  - https://github.com/everyinfra/jev-radar

### title [WARN] 3/3 URL
- description: 命中 3/3 URL(100%);最常见表现: 264 chars 超上限 60()
- recommendation: 补/改 title:每页唯一,50-60 字符
- affected_urls(3):
  - https://github.com/everyinfra/seo-skills
  - https://github.com/everyinfra/seo-skills/blob/main/README.md
  - https://github.com/everyinfra/jev-radar

### h1 [WARN] 1/3 URL
- description: 命中 1/3 URL(33%);最常见表现: 3 个 H1
- recommendation: 每页唯一 H1(与 title 呼应但不重复)
- affected_urls(1):
  - https://github.com/everyinfra/seo-skills/blob/main/README.md

### headings [WARN] 1/3 URL
- description: 命中 1/3 URL(33%);最常见表现: 跳级 h1→h3
- recommendation: 消除标题跳级(h1→h2→h3 逐级)
- affected_urls(1):
  - https://github.com/everyinfra/jev-radar

### rendering [INFO] 3/3 URL
- description: 命中 3/3 URL(100%);最常见表现: 无 noscript 回退(或去标签文本≤20 字)——无 JS 客户端拿到空页
- recommendation: 关键内容服务端渲染;压缩 JS;补 noscript 回退
- affected_urls(3):
  - https://github.com/everyinfra/seo-skills
  - https://github.com/everyinfra/seo-skills/blob/main/README.md
  - https://github.com/everyinfra/jev-radar

### semantic-html [INFO] 3/3 URL
- description: 命中 3/3 URL(100%);最常见表现: 语义 HTML 比值 2.5% <10%(阈值自定,官方未公开)
- recommendation: 模板改用语义标签(header/main/article/section)
- affected_urls(3):
  - https://github.com/everyinfra/seo-skills
  - https://github.com/everyinfra/seo-skills/blob/main/README.md
  - https://github.com/everyinfra/jev-radar

<!-- envelope-category-v1 {"name":"rankability","findings":[{"rule_id":"description","title":"description 缺失/越限","severity":"WARN","description":"命中 3/3 URL(100%);最常见表现: 247 chars 超上限 155","recommendation":"补/改 description:~155 字符,含利益点与 CTA","affected_urls":["https://github.com/everyinfra/seo-skills","https://github.com/everyinfra/seo-skills/blob/main/README.md","https://github.com/everyinfra/jev-radar"],"affected":3},{"rule_id":"schema","title":"无 JSON-LD","severity":"WARN","description":"命中 3/3 URL(100%);最常见表现: 无 JSON-LD","recommendation":"补 JSON-LD(按页型选 Organization/Article/Breadcrumb 等)","affected_urls":["https://github.com/everyinfra/seo-skills","https://github.com/everyinfra/seo-skills/blob/main/README.md","https://github.com/everyinfra/jev-radar"],"affected":3},{"rule_id":"title","title":"title 缺失/越限","severity":"WARN","description":"命中 3/3 URL(100%);最常见表现: 264 chars 超上限 60()","recommendation":"补/改 title:每页唯一,50-60 字符","affected_urls":["https://github.com/everyinfra/seo-skills","https://github.com/everyinfra/seo-skills/blob/main/README.md","https://github.com/everyinfra/jev-radar"],"affected":3},{"rule_id":"h1","title":"H1 缺失/多个","severity":"WARN","description":"命中 1/3 URL(33%);最常见表现: 3 个 H1","recommendation":"每页唯一 H1(与 title 呼应但不重复)","affected_urls":["https://github.com/everyinfra/seo-skills/blob/main/README.md"],"affected":1},{"rule_id":"headings","title":"标题层级跳级","severity":"WARN","description":"命中 1/3 URL(33%);最常见表现: 跳级 h1→h3","recommendation":"消除标题跳级(h1→h2→h3 逐级)","affected_urls":["https://github.com/everyinfra/jev-radar"],"affected":1},{"rule_id":"rendering","title":"渲染依赖过重","severity":"INFO","description":"命中 3/3 URL(100%);最常见表现: 无 noscript 回退(或去标签文本≤20 字)——无 JS 客户端拿到空页","recommendation":"关键内容服务端渲染;压缩 JS;补 noscript 回退","affected_urls":["https://github.com/everyinfra/seo-skills","https://github.com/everyinfra/seo-skills/blob/main/README.md","https://github.com/everyinfra/jev-radar"],"affected":3},{"rule_id":"semantic-html","title":"语义 HTML 比值低","severity":"INFO","description":"命中 3/3 URL(100%);最常见表现: 语义 HTML 比值 2.5% <10%(阈值自定,官方未公开)","recommendation":"模板改用语义标签(header/main/article/section)","affected_urls":["https://github.com/everyinfra/seo-skills","https://github.com/everyinfra/seo-skills/blob/main/README.md","https://github.com/everyinfra/jev-radar"],"affected":3}]} -->
