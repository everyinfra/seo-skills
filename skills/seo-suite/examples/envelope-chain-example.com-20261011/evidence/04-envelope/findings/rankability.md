# findings: rankability

9 项发现;文末 envelope-category-v1 注释行为机器回读数据(--resume 依赖,勿删)

| rule_id | severity | affected | title |
|---|---|---|---|
| description | CRITICAL | 1/1 | description 缺失/越限 |
| h1 | CRITICAL | 1/1 | H1 缺失/多个 |
| content | WARN | 1/1 | 内容词数异常 |
| og | WARN | 1/1 | og 标签缺失 |
| schema | WARN | 1/1 | 无 JSON-LD |
| title | WARN | 1/1 | title 缺失/越限 |
| headings | INFO | 1/1 | 标题层级跳级 |
| rendering | INFO | 1/1 | 渲染依赖过重 |
| semantic-html | INFO | 1/1 | 语义 HTML 比值低 |

## 明细

### description [CRITICAL] 1/1 URL
- description: 命中 1/1 URL(100%);最常见表现: 缺失
- recommendation: 补 meta description(~155 字符)
- affected_urls(1):
  - https://example.com

### h1 [CRITICAL] 1/1 URL
- description: 命中 1/1 URL(100%);最常见表现: 无 H1
- recommendation: 补唯一 H1(与 title 呼应但不重复)
- affected_urls(1):
  - https://example.com

### content [WARN] 1/1 URL
- description: 命中 1/1 URL(100%);最常见表现: 词数 27 <200(soft-thin)
- recommendation: thin content<100 词:增补实质内容(模板页除外)【Botify 官方阈值】
- affected_urls(1):
  - https://example.com

### og [WARN] 1/1 URL
- description: 命中 1/1 URL(100%);最常见表现: og:title 缺失
- recommendation: 补 og:title/og:description/og:image(image 用绝对 URL)
- affected_urls(1):
  - https://example.com

### schema [WARN] 1/1 URL
- description: 命中 1/1 URL(100%);最常见表现: 无 JSON-LD
- recommendation: 补 JSON-LD(按页型选 Organization/Article/Breadcrumb 等)
- affected_urls(1):
  - https://example.com

### title [WARN] 1/1 URL
- description: 命中 1/1 URL(100%);最常见表现: 14 chars <20
- recommendation: title<50 字符:扩到 50-60(保留主关键词,自然语句)【Botify 官方阈值】
- affected_urls(1):
  - https://example.com

### headings [INFO] 1/1 URL
- description: 命中 1/1 URL(100%);最常见表现: H2 仅 0 个(<2)——AI 分块依赖标题层级(H1==1 且 H2>=2)
- recommendation: 消除标题跳级(h1→h2→h3 逐级)
- affected_urls(1):
  - https://example.com

### rendering [INFO] 1/1 URL
- description: 命中 1/1 URL(100%);最常见表现: 无 noscript 回退(或去标签文本≤20 字)——无 JS 客户端拿到空页
- recommendation: 关键内容服务端渲染;压缩 JS;补 noscript 回退
- affected_urls(1):
  - https://example.com

### semantic-html [INFO] 1/1 URL
- description: 命中 1/1 URL(100%);最常见表现: 语义 HTML 比值 0.0% <10%(阈值自定,官方未公开)
- recommendation: 模板改用语义标签(header/main/article/section)
- affected_urls(1):
  - https://example.com

<!-- envelope-category-v1 {"name":"rankability","findings":[{"rule_id":"description","title":"description 缺失/越限","severity":"CRITICAL","description":"命中 1/1 URL(100%);最常见表现: 缺失","recommendation":"补 meta description(~155 字符)","affected_urls":["https://example.com"],"affected":1},{"rule_id":"h1","title":"H1 缺失/多个","severity":"CRITICAL","description":"命中 1/1 URL(100%);最常见表现: 无 H1","recommendation":"补唯一 H1(与 title 呼应但不重复)","affected_urls":["https://example.com"],"affected":1},{"rule_id":"content","title":"内容词数异常","severity":"WARN","description":"命中 1/1 URL(100%);最常见表现: 词数 27 <200(soft-thin)","recommendation":"thin content<100 词:增补实质内容(模板页除外)【Botify 官方阈值】","affected_urls":["https://example.com"],"affected":1},{"rule_id":"og","title":"og 标签缺失","severity":"WARN","description":"命中 1/1 URL(100%);最常见表现: og:title 缺失","recommendation":"补 og:title/og:description/og:image(image 用绝对 URL)","affected_urls":["https://example.com"],"affected":1},{"rule_id":"schema","title":"无 JSON-LD","severity":"WARN","description":"命中 1/1 URL(100%);最常见表现: 无 JSON-LD","recommendation":"补 JSON-LD(按页型选 Organization/Article/Breadcrumb 等)","affected_urls":["https://example.com"],"affected":1},{"rule_id":"title","title":"title 缺失/越限","severity":"WARN","description":"命中 1/1 URL(100%);最常见表现: 14 chars <20","recommendation":"title<50 字符:扩到 50-60(保留主关键词,自然语句)【Botify 官方阈值】","affected_urls":["https://example.com"],"affected":1},{"rule_id":"headings","title":"标题层级跳级","severity":"INFO","description":"命中 1/1 URL(100%);最常见表现: H2 仅 0 个(<2)——AI 分块依赖标题层级(H1==1 且 H2>=2)","recommendation":"消除标题跳级(h1→h2→h3 逐级)","affected_urls":["https://example.com"],"affected":1},{"rule_id":"rendering","title":"渲染依赖过重","severity":"INFO","description":"命中 1/1 URL(100%);最常见表现: 无 noscript 回退(或去标签文本≤20 字)——无 JS 客户端拿到空页","recommendation":"关键内容服务端渲染;压缩 JS;补 noscript 回退","affected_urls":["https://example.com"],"affected":1},{"rule_id":"semantic-html","title":"语义 HTML 比值低","severity":"INFO","description":"命中 1/1 URL(100%);最常见表现: 语义 HTML 比值 0.0% <10%(阈值自定,官方未公开)","recommendation":"模板改用语义标签(header/main/article/section)","affected_urls":["https://example.com"],"affected":1}]} -->
