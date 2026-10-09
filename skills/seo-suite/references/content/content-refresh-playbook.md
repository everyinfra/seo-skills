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

## 刷新优先级队列与质量门(seomachine 深读 2026-10-09b)

**刷新候选四桶(GA4+GSC 聚合器自动分桶)**:

| 桶 | 触发条件 | 动作类型 | 优先级 |
|---|---|---|---|
| quick wins | 关键词排名 11–20(跌出首页带) | optimize:小改推回第 1 页 | high |
| declining | 页面流量环比降幅 ≥20% | update:刷新 | high |
| low CTR | 展示量高、点击率低 | optimize_meta:只改标题/描述 | medium |
| trending | 查询展示量上升 | create_new | medium |

low CTR 桶用「错失点击」估算说服力:按展示量 × 同类页面 CTR 差值折算每月少拿的点击数。**meta 修复是刷新中 ROI 最高、风险最低的动作,排在正文重写之前。**

**刷新后字数目标(SERP 对标而非拍脑袋)**:抓目标词前 10 结果,recommended_min=字数中位数,recommended_optimal=max(P75, 中位数×1.2),recommended_max=optimal×1.2。状态带:<80%×min=严重偏短必须扩;<min=偏短;<optimal=够用(补到 optimal 更稳);≤max=最优;>max=偏长,确认每段有增量价值再保留。竞品字数统计要先用 article/main/[role=main]/.content 等选择器定位主内容、剥离 nav/footer/header/aside,否则模板文字污染统计。

**五维质量门(刷新验收线)**:humanity 30% / specificity 25% / structure_balance 20% / seo 15% / readability 10%,复合分 ≥70 才算刷新完成。修复排序公式:**issue impact = 维度权重 ×(100 − 维度分)**,取 top-5 先修——权重高且亏分多的维度优先动手。

**刷新编辑八查(每节过一遍)**:①删 AI 套话(见 [ai-writing-detection.md](ai-writing-detection.md) 的词表与 Unicode 清理);②模糊词换具体数据;③段落 ≤4 句;④句长混排(5–10 词短句配 15–25 词长句);⑤加缩略语恢复口语感;⑥主动语态 ≥80%;⑦插入语/提问增加人味;⑧品牌语调一致。

**事实核查层(具体性打分)**:每千词中可验证事实信号 ≥2 处加分——百分比、金额、年份、「月份+日期」、带单位的计数(downloads/users/customers)、具名引语(Name said/noted)、≥10 字符引文;数字总密度 <3/千词扣分;模糊词(many/various/significant/often/…)密度 >15/千词开始扣、>25/千词重扣。刷新替换映射:many→具体数量或百分比;often→具体频率;various→点名列举;significant→具体幅度;things/stuff→具体条目;good/bad→具体收益/代价。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[aaron-he-zhu/seo-geo-claude-skills · optimize/content-refresher](https://github.com/aaron-he-zhu/seo-geo-claude-skills/tree/v9.9.12/optimize/content-refresher)（Apache-2.0）
- 深读补充：[TheCraigHewitt/seomachine · data_sources/modules](https://github.com/TheCraigHewitt/seomachine)(content_scorer/content_length_comparator/section_writer/data_aggregator)
- 一手资料：[Google：有用、可靠、以人为本的内容](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)、[Google：站点地图](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)
