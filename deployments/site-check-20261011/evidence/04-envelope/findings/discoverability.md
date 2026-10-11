# findings: discoverability

2 项发现;文末 envelope-category-v1 注释行为机器回读数据(--resume 依赖,勿删)

| rule_id | severity | affected | title |
|---|---|---|---|
| links | WARN | 3/3 | 页内链接过多 |
| sitemap | INFO | 3/3 | sitemap 不可达 |

## 明细

### links [WARN] 3/3 URL
- description: 命中 3/3 URL(100%);最常见表现: 207 链接 >100
- recommendation: 页内链接>100 时精简导航或分页
- affected_urls(3):
  - https://github.com/everyinfra/seo-skills
  - https://github.com/everyinfra/seo-skills/blob/main/README.md
  - https://github.com/everyinfra/jev-radar

### sitemap [INFO] 3/3 URL
- description: 命中 3/3 URL(100%);最常见表现: //sitemap.xml 不可达
- recommendation: 补 /sitemap.xml 并在 robots.txt 声明
- affected_urls(3):
  - https://github.com/everyinfra/seo-skills
  - https://github.com/everyinfra/seo-skills/blob/main/README.md
  - https://github.com/everyinfra/jev-radar

<!-- envelope-category-v1 {"name":"discoverability","findings":[{"rule_id":"links","title":"页内链接过多","severity":"WARN","description":"命中 3/3 URL(100%);最常见表现: 207 链接 >100","recommendation":"页内链接>100 时精简导航或分页","affected_urls":["https://github.com/everyinfra/seo-skills","https://github.com/everyinfra/seo-skills/blob/main/README.md","https://github.com/everyinfra/jev-radar"],"affected":3},{"rule_id":"sitemap","title":"sitemap 不可达","severity":"INFO","description":"命中 3/3 URL(100%);最常见表现: //sitemap.xml 不可达","recommendation":"补 /sitemap.xml 并在 robots.txt 声明","affected_urls":["https://github.com/everyinfra/seo-skills","https://github.com/everyinfra/seo-skills/blob/main/README.md","https://github.com/everyinfra/jev-radar"],"affected":3}]} -->
