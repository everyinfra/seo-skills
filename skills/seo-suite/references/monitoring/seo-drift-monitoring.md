# SEO 漂移监控（基线 / 对比 / 历史）

> 建立于 2026-10-09。架构与规则参考 [AgriciDaniel/claude-seo](https://github.com/Agrici/claude-seo)（MIT）`skills/seo-drift/`。按本套件证据约束改写。
> 定位："SEO 的 Git"——先存基线，再定期对比，把静默劣化变成可归因事件。

## 一、三命令模型

| 命令 | 作用 |
|---|---|
| baseline | 抓取页面并存 13 元素快照 |
| compare | 当前页 vs 最近基线，跑 17 规则 |
| history | 同 URL 全部基线/对比的时间线 |

存储：本地 SQLite（单库，URL 归一化后哈希索引）。

## 二、13 个捕获元素

页面层：title / meta description / canonical / robots 指令 / H1 数组 / H2 数组 / H3 数组 / JSON-LD 数组 / Open Graph 字典（九项来自 HTML 解析）；性能：Core Web Vitals 字典；传输：HTTP 状态码；完整性：html_hash 与 schema_hash（**SHA-256**，分别对正文与 schema 内容）。

URL 归一化：scheme/host 小写、去默认端口 80/443、query 参数排序、去 UTM、去尾斜杠。

## 三、17 条对比规则

**CRITICAL（1–8，立即行动）**
1. JSON-LD/Schema 完全消失
2. Canonical URL 变更
3. Canonical 被移除
4. 新增 noindex 指令
5. H1 全部消失
6. H1 文本大改（相似度 <0.5）
7. Title 标签消失
8. 状态码 2xx → 4xx/5xx

**WARNING（9–14）**
9. Title 文本变化
10. Meta description 变化
11. CWV 指标退步 **>20%**（p75 LCP/INP/CLS）
12. Lighthouse 性能分掉 **10+**
13. OG 标签被移除
14. Schema 内容修改（schema_hash 变但 schema 仍在）

**INFO（15–17）**
15. 新增 Schema
16. H2 结构变化
17. 内容哈希变化（html_hash，兜底）

## 四、实施要点

- 4xx/5xx 页仍要捕获（状态码本身是被跟踪的漂移信号），不是跳过
- CWV 抓取失败存 null 并跳过 CWV 规则——**不猜数**
- 抓取走 SSRF 防护（只允许 http(s)、禁内网地址、TLS 恒验证）
- 适用节奏：每次发版后 compare；每周全站 compare；改版前先 baseline

## 五、与其他参考的联动

漂移规则命中的项直接路由：Schema 变更 → schema 校验参考；CWV 退步 → 性能参考；noindex 新增 → 索引审计；title/meta 变化 → 内容规范。

## 六、来源

- 13 元素/SQLite DDL/17 规则/归一化规则：[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-drift/SKILL.md`、`references/comparison-rules.md`、`scripts/drift_baseline.py`
