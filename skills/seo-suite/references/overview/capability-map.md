# SEO Suite Capability Map

## 总体结构

```text
seo-suite
├── overview     总入口、分诊、优先级判断
├── research     关键词、SERP、内容缺口、竞品
├── content      SEO/GEO 内容、标题描述、内容质量
├── technical    技术 SEO、Schema、内链、架构、实体、Programmatic SEO
└── monitoring   排名、外链、报告、告警、权威度
```

## 能力映射

| 能力主题 | 集合 |
|---|---|
| 整体 SEO 诊断、SEO 方案、AI 搜索可见度的总体判断 | overview |
| 关键词研究、SERP 分析、内容缺口、竞品分析、竞品/替代方案页规划、内容策略 | research |
| SEO 内容写作、GEO 内容优化、标题与描述、内容质量（E-E-A-T）、内容刷新、竞品页文案 | content |
| 单页审计、技术 SEO 检查、结构化数据、内链、站点架构、实体优化、Programmatic SEO、Core Web Vitals / 性能、审计工具输出解读、SEO 归因埋点 | technical |
| 排名追踪、外链分析、效果报告、告警、域名权威度评估 | monitoring |

## 组合调用建议

| 场景 | 推荐组合 |
|---|---|
| 新专题上线前 | research + content |
| 规划 competitor / alternatives 页面集 | research + content + technical |
| 做 content pillars / cluster map | research + content |
| 页面不排名 | research + technical |
| 旧内容掉量 refresh | monitoring + content + technical |
| 排名下滑 | monitoring + research + technical |
| AI 引用弱 | content + technical + monitoring |
| 做整站 SEO 路线图 | overview + research + technical + monitoring |
