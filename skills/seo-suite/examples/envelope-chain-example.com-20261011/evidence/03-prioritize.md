# 优先级引擎(Botify ActionBoard 口径)

- 输入: site_audit --json;1 URL 可评分(0 拒审未计入);全站样本
- 上下文: GSC 逐页流量 ✗ · PageRank 对比 ✗
- impact = 命中占比 × 严重度(CRITICAL=3/WARN=2/INFO=1) × 放大器(内链>10 次 → ×1.5)
- coverage: 基于样本,优先级不可外推到未爬取页面(Ryte/Botify 口径)

## 立即处理(impact>0,降序)
1. **desc_missing** [CRITICAL] impact 3.0 —— 命中 1/1(meta_tags)
   - 修复: 补 meta description(~155 字符)
   - URL(1): https://example.com
2. **h1_missing** [CRITICAL] impact 3.0 —— 命中 1/1(content)
   - 修复: 补唯一 H1(与 title 呼应但不重复)
   - URL(1): https://example.com
3. **thin_content** [WARN] impact 2.0 —— 命中 1/1(content)
   - 修复: thin content<100 词:增补实质内容(模板页除外)【Botify 官方阈值】
   - 条件(条件上下文): 模板页(联系/法务/登录)词数低是合理的——命中后先分型再修
   - URL(1): https://example.com
4. **title_short** [WARN] impact 2.0 —— 命中 1/1(meta_tags)
   - 修复: title<50 字符:扩到 50-60(保留主关键词,自然语句)【Botify 官方阈值】
   - URL(1): https://example.com

## 值得探索(Opportunity 类)
- (无)

未命中(本 segment 内 0 命中): canonical_invalid, desc_short, fetch_error, noindex_intent, staging_exposed, title_missing, url_long

## 降级声明(缺数据源的规则,未生效)
- depth_deep: 缺 depth 数据(输入 audit 无该页面级字段),规则未生效
- inlinks_low: 缺 inlinks 数据(输入 audit 无该页面级字段),规则未生效
- duplicate_body: 缺 similarity 数据(输入 audit 无该页面级字段),规则未生效
- canonical_mismatch: 缺 canonical_similarity 数据(输入 audit 无该页面级字段),规则未生效
- canonical_pagerank: 缺 canonical_other 数据(输入 audit 无该页面级字段),规则未生效
- redirect_canonical_conflict: 缺 redirect_and_canonical_other 数据(输入 audit 无该页面级字段),规则未生效
- not_indexed_with_traffic: 缺 not_indexed 数据(输入 audit 无该页面级字段),规则未生效
