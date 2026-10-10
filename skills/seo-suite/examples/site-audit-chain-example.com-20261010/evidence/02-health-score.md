# 站点健康分(site_audit 样本 1 URL,0 拒审未计入)

## 分数卡
- 主分(Ahrefs 口径,无 CRITICAL URL 占比×100): **0.0 → Weak**(0/1 URL 无 CRITICAL)
- WARN 子分: 0.0 / INFO 子分: 0.0(WARN/INFO 不扣主分,单列)
- 合成分(Lumar 六类加权,类权重=类内负号检查权重和): 94.3
- coverage: 基于样本,分数不可与全站直接比较

## 类别树(Lumar 六大类,每类 100 起步,仅负号检查扣分)
availability 100.0(类权重 3.0)
  └─ server_errors: fetch 0/1 CRITICAL
indexability 98.8(类权重 7.25)
  ├─ non_indexable: robots 1/1 INFO; ai-bots 0/1 CRITICAL; staging 0/1 CRITICAL
  ├─ canonicalization: canonical 1/1 WARN
  └─ mobile_indexability: N/A(data_source_missing)
uniqueness: N/A(data_source_missing)——不计入合成分
discoverability 99.5(类权重 2.5)
  ├─ crawl_budget: N/A(data_source_missing)
  ├─ internal_linking: links 0/1 WARN
  ├─ redirection: N/A(data_source_missing)
  ├─ sitemaps: llms.txt 1/1 INFO; sitemap 1/1 INFO
  └─ internationalization: a11y 0/1 WARN
rankability 89.2(类权重 12.25)
  ├─ page_content: description 1/1 CRITICAL; h1 1/1 CRITICAL; content 1/1 WARN; title 1/1 WARN; headings 1/1 INFO; rendering 1/1 INFO; semantic-html 1/1 INFO; bluf 0/1 INFO; freshness 0/1 INFO; images 0/1 WARN
  ├─ structured_data: schema 1/1 WARN
  └─ social_tags: og 1/1 WARN
experience: N/A(data_source_missing)——不计入合成分

## Top impact(Ryte 口径:impact=命中占比×严重度²)
立即处理(impact>0,降序):
| 规则 | 类/子组 | 严重度 | 命中 | impact |
|---|---|---|---|---|
| description | rankability/page_content | CRITICAL | 1/1 | 9.0 |
| h1 | rankability/page_content | CRITICAL | 1/1 | 9.0 |
| canonical | indexability/canonicalization | WARN | 1/1 | 4.0 |
| content | rankability/page_content | WARN | 1/1 | 4.0 |
| og | rankability/social_tags | WARN | 1/1 | 4.0 |
| schema | rankability/structured_data | WARN | 1/1 | 4.0 |
| title | rankability/page_content | WARN | 1/1 | 4.0 |
| headings | rankability/page_content | INFO | 1/1 | 1.0 |
| llms.txt | discoverability/sitemaps | INFO | 1/1 | 1.0 |
| rendering | rankability/page_content | INFO | 1/1 | 1.0 |
| robots | indexability/non_indexable | INFO | 1/1 | 1.0 |
| semantic-html | rankability/page_content | INFO | 1/1 | 1.0 |
| sitemap | discoverability/sitemaps | INFO | 1/1 | 1.0 |

opportunity 值得探索(impact=0):
- a11y(discoverability/internationalization WARN 0/1)
- ai-bots(indexability/non_indexable CRITICAL 0/1)
- bluf(rankability/page_content INFO 0/1)
- fetch(availability/server_errors CRITICAL 0/1)
- freshness(rankability/page_content INFO 0/1)
- images(rankability/page_content WARN 0/1)
- links(discoverability/internal_linking WARN 0/1)
- staging(indexability/non_indexable CRITICAL 0/1)

## Ignored
- (无)
