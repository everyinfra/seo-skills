# findings: discoverability

2 项发现;文末 envelope-category-v1 注释行为机器回读数据(--resume 依赖,勿删)

| rule_id | severity | affected | title |
|---|---|---|---|
| llms.txt | INFO | 1/1 | llms.txt 缺失 |
| sitemap | INFO | 1/1 | sitemap 不可达 |

## 明细

### llms.txt [INFO] 1/1 URL
- description: 命中 1/1 URL(100%);最常见表现: //llms.txt 不可达
- recommendation: 补 /llms.txt(AI 发现层)
- affected_urls(1):
  - https://example.com

### sitemap [INFO] 1/1 URL
- description: 命中 1/1 URL(100%);最常见表现: //sitemap.xml 不可达
- recommendation: 补 /sitemap.xml 并在 robots.txt 声明
- affected_urls(1):
  - https://example.com

<!-- envelope-category-v1 {"name":"discoverability","findings":[{"rule_id":"llms.txt","title":"llms.txt 缺失","severity":"INFO","description":"命中 1/1 URL(100%);最常见表现: //llms.txt 不可达","recommendation":"补 /llms.txt(AI 发现层)","affected_urls":["https://example.com"],"affected":1},{"rule_id":"sitemap","title":"sitemap 不可达","severity":"INFO","description":"命中 1/1 URL(100%);最常见表现: //sitemap.xml 不可达","recommendation":"补 /sitemap.xml 并在 robots.txt 声明","affected_urls":["https://example.com"],"affected":1}]} -->
