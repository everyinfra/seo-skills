# findings: indexability

1 项发现;文末 envelope-category-v1 注释行为机器回读数据(--resume 依赖,勿删)

| rule_id | severity | affected | title |
|---|---|---|---|
| canonical | WARN | 3/3 | canonical 缺失/异常 |

## 明细

### canonical [WARN] 3/3 URL
- description: 命中 3/3 URL(100%);最常见表现: 缺失
- recommendation: canonical 改绝对 URL 并自指(指他页需先对比权重)
- affected_urls(3):
  - https://github.com/everyinfra/seo-skills
  - https://github.com/everyinfra/seo-skills/blob/main/README.md
  - https://github.com/everyinfra/jev-radar

<!-- envelope-category-v1 {"name":"indexability","findings":[{"rule_id":"canonical","title":"canonical 缺失/异常","severity":"WARN","description":"命中 3/3 URL(100%);最常见表现: 缺失","recommendation":"canonical 改绝对 URL 并自指(指他页需先对比权重)","affected_urls":["https://github.com/everyinfra/seo-skills","https://github.com/everyinfra/seo-skills/blob/main/README.md","https://github.com/everyinfra/jev-radar"],"affected":3}]} -->
