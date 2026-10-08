# SEO Suite Capability Map

## 总体结构(市场 × 能力 双维度)

```text
seo-suite
├── overview     总入口、分诊、优先级判断、市场维度主干(multilingual-workflow)
├── research     关键词、SERP、内容缺口、竞品(含各市场工具链)
├── content      SEO/GEO 内容、标题描述、内容质量(含区域 AI 平台、中文指南)
├── technical    技术 SEO、Schema、内链、架构、实体、Programmatic SEO(含区域爬虫/hreflang)
└── monitoring   排名、外链、报告、告警、权威度
```

**运行模型:每个任务 = 市场 × 能力。** 市场决定引擎格局、工具栈、语言规范与合规;能力决定方法论。市场差异知识不放在独立的区域文件里,而是作为各能力文件中带「市场差异」的小节存在;18 市场的索引与主干在 [multilingual-workflow.md](multilingual-workflow.md)。

## 能力映射

| 能力主题 | 集合 |
|---|---|
| 整体 SEO 诊断、SEO 方案、AI 搜索可见度的总体判断 | overview |
| 关键词研究、SERP 分析、内容缺口、竞品分析、竞品/替代方案页规划、内容策略 | research |
| SEO 内容写作、GEO 内容优化、标题与描述、内容质量（E-E-A-T）、内容刷新、竞品页文案 | content |
| 单页审计、技术 SEO 检查、结构化数据、内链、站点架构、实体优化、Programmatic SEO、Core Web Vitals / 性能、审计工具输出解读、SEO 归因埋点 | technical |
| 排名追踪、外链分析、效果报告、告警、域名权威度评估 | monitoring |

## 市场分层(策略侧重不同)

| 层 | 市场 | 策略侧重 |
|---|---|---|
| 独立学科(平行引擎生态) | 中文、俄语区、韩语区、日语区 | 换工具栈+换内容生态入口;GEO 的引用池与 Google 系完全不同 |
| ChatGPT 超强市场 | 葡语(巴西)、印地(印度) | Google 常规打法+LLM 可见性优先级全市场最高 |
| 方言/文字机制分裂 | 西语、阿拉伯、德语、印尼、越南、泰语、波兰、荷兰 | hreflang 结构+词表归组+文字方向/分词机制 |
| 合规驱动 | 法语(Bill 96)、俄语区(152-ФЗ/erid)、欧盟(GDPR)、日本(ステマ規制) | 合规先于内容 |
| 基线 | 英文 | 全球默认层,其他市场在此之上做差异 |

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
