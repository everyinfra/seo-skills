# SEO 审计 envelope 报告(audit-data.json 人读摘要)

- 生成时间: 2026-10-11T09:21:06+00:00
- 样本: 3 URL(source_urls 见 audit-data.json;coverage: 基于样本,不可外推到未爬取页面)
- 主分(health_score): 100.0(Excellent)
- AI Search Health(site_audit 样本均值): 85.0/100
- impact 口径: --priority 输入(未覆盖的规则按 severity×受影响面估算)

## Top findings(前 3)
1. [WARN] canonical 缺失/异常 —— 3 URL
2. [WARN] description 缺失/越限 —— 3 URL
3. [WARN] 页内链接过多 —— 3 URL

## Quick wins(高 impact 且易修,至多 3)
1. [WARN] description 缺失/越限 —— impact 2.0(估算): 补/改 description:~155 字符,含利益点与 CTA
2. [WARN] 无 JSON-LD —— impact 2.0(估算): 补 JSON-LD(按页型选 Organization/Article/Breadcrumb 等)
3. [WARN] title 缺失/越限 —— impact 2.0(估算): 补/改 title:每页唯一,50-60 字符

## 行动计划

### 立即(本周)(0 项)
- (无)

### 短期(月内)(5 项)
- [WARN] canonical 缺失/异常: canonical 改绝对 URL 并自指(指他页需先对比权重)(impact 2.0)
- [WARN] description 缺失/越限: 补/改 description:~155 字符,含利益点与 CTA(impact 2.0)
- [WARN] 页内链接过多: 页内链接>100 时精简导航或分页(impact 2.0)
- [WARN] 无 JSON-LD: 补 JSON-LD(按页型选 Organization/Article/Breadcrumb 等)(impact 2.0)
- [WARN] title 缺失/越限: 补/改 title:每页唯一,50-60 字符(impact 2.0)

### 持续(5 项)
- [WARN] H1 缺失/多个: 每页唯一 H1(与 title 呼应但不重复)(impact 0.6667)
- [WARN] 标题层级跳级: 消除标题跳级(h1→h2→h3 逐级)(impact 0.6667)
- [INFO] 渲染依赖过重: 关键内容服务端渲染;压缩 JS;补 noscript 回退(impact 1.0)
- [INFO] 语义 HTML 比值低: 模板改用语义标签(header/main/article/section)(impact 1.0)
- [INFO] sitemap 不可达: 补 /sitemap.xml 并在 robots.txt 声明(impact 1.0)

## 类别明细(人读表格见 findings/<category>.md)
- indexability: 1 项发现
- discoverability: 2 项发现
- rankability: 7 项发现
