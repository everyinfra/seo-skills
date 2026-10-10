# SEO 审计 envelope 报告(audit-data.json 人读摘要)

- 生成时间: 2026-10-10T20:19:35+00:00
- 样本: 1 URL(source_urls 见 audit-data.json;coverage: 基于样本,不可外推到未爬取页面)
- 主分(health_score): 0.0(Weak)
- AI Search Health(site_audit 样本均值): 70.0/100
- impact 口径: --priority 输入(未覆盖的规则按 severity×受影响面估算)

## Top findings(前 3)
1. [CRITICAL] description 缺失/越限 —— 1 URL
2. [CRITICAL] H1 缺失/多个 —— 1 URL
3. [WARN] canonical 缺失/异常 —— 1 URL

## Quick wins(高 impact 且易修,至多 3)
1. [CRITICAL] description 缺失/越限 —— impact 3.0(priority 输入): 补 meta description(~155 字符)
2. [CRITICAL] H1 缺失/多个 —— impact 3.0(priority 输入): 补唯一 H1(与 title 呼应但不重复)
3. [WARN] og 标签缺失 —— impact 2.0(估算): 补 og:title/og:description/og:image(image 用绝对 URL)

## 行动计划

### 立即(本周)(2 项)
- [CRITICAL] description 缺失/越限: 补 meta description(~155 字符)(impact 3.0)
- [CRITICAL] H1 缺失/多个: 补唯一 H1(与 title 呼应但不重复)(impact 3.0)

### 短期(月内)(5 项)
- [WARN] canonical 缺失/异常: canonical 改绝对 URL 并自指(指他页需先对比权重)(impact 2.0)
- [WARN] 内容词数异常: thin content<100 词:增补实质内容(模板页除外)【Botify 官方阈值】(impact 2.0)
- [WARN] og 标签缺失: 补 og:title/og:description/og:image(image 用绝对 URL)(impact 2.0)
- [WARN] 无 JSON-LD: 补 JSON-LD(按页型选 Organization/Article/Breadcrumb 等)(impact 2.0)
- [WARN] title 缺失/越限: title<50 字符:扩到 50-60(保留主关键词,自然语句)【Botify 官方阈值】(impact 2.0)

### 持续(6 项)
- [INFO] 标题层级跳级: 消除标题跳级(h1→h2→h3 逐级)(impact 1.0)
- [INFO] llms.txt 缺失: 补 /llms.txt(AI 发现层)(impact 1.0)
- [INFO] 渲染依赖过重: 关键内容服务端渲染;压缩 JS;补 noscript 回退(impact 1.0)
- [INFO] noindex/robots 屏蔽: 检查 noindex/nosnippet 是否误设;按页面意图决定保留或移除(impact 1.0)
- [INFO] 语义 HTML 比值低: 模板改用语义标签(header/main/article/section)(impact 1.0)
- [INFO] sitemap 不可达: 补 /sitemap.xml 并在 robots.txt 声明(impact 1.0)

## 类别明细(人读表格见 findings/<category>.md)
- indexability: 2 项发现
- discoverability: 2 项发现
- rankability: 9 项发现
