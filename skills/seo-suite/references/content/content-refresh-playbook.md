# Content Refresh Playbook

## 适用场景
- 旧内容排名下滑
- 流量连续下滑
- 年份、统计、截图、工具信息过时
- 竞品已覆盖新主题而你未覆盖
- 需要在保留 URL 已有积累的前提下恢复表现

信号怎么识别、怎么排除技术原因和季节性，见 [content-decay-signals.md](content-decay-signals.md)。

## 先判定是 refresh 还是 rewrite

### 优先 refresh
- URL 有外链或历史排名基础
- 搜索意图未变
- 原始结构尚可
- 预计改动不到一半（经验判断，不是硬线）

### 考虑 rewrite
- 内容基础质量差
- 搜索意图已变
- 预计要改动大半
- URL 几乎没有积累价值

## 常见 decay signals
- organic traffic 下滑
- 关键词平均排名下降
- CTR 下滑但 impressions 稳定
- 页面存在旧年份、旧统计、旧截图
- broken links 增加
- SERP 被新竞品内容替代
- AI Overviews / 富媒体结果改变了点击分布

## Refresh 工作流
1. 判断是否存在技术问题先于内容问题
2. 识别 decay signals 与严重度
3. 决定 refresh / rewrite / consolidate / retire
4. 列出需要更新的统计、段落、链接、截图、FAQ、schema 字段
5. 形成刷新计划与发布时间策略
6. 刷新后持续观察，常见观察窗口是 4–8 周（按页面流量和抓取频率调整）

## 刷新动作清单
- 更新 title / meta / H1 的时效信号（只在内容确实更新时）
- 替换旧统计并补来源和日期
- 增加竞品已覆盖而你缺失的新主题
- 扩写薄弱段落
- 更新内部链接
- 补充定义、可被准确摘取的结论句；FAQ 只写真实问答（见 [geo-evidence.md](geo-evidence.md)）
- 内容有实质更新时，同步 dateModified / sitemap lastmod；不要只改日期

## 输出要求
默认应输出：
1. Decay summary
2. Refresh vs rewrite decision
3. 具体更新项清单
4. 结构调整方案
5. 发布与再提交策略
6. 监控指标与复盘时间点

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/content-refresher](https://github.com/aaron-he-zhu/seo-geo-claude-skills/tree/v9.9.12/optimize/content-refresher)（Apache-2.0）
- 一手资料：[Google：有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[Google：站点地图](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)
