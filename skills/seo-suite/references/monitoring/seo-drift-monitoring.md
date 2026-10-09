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

## 五、算法更新归因层(2026-10-09 并入)

**数据源**:Google 官方 Search Status Dashboard 的 Ranking 历史是最强"官方传感器"(只报确认事件);Semrush Sensor(活跃;**2026-09-18 全市场重算波动基线,历史分不可直接比**)/MozCast(活跃,偏美)/Algoroo(存活)为旁证;**RankRanger 实质死亡**(2022 被收购后不独立销售,2025 清理历史数据)——勿依赖单一传感器,固定面板会漏(2026-06-08~12 社区观测波动未被捕捉)。

**归因流程(官方《Debugging drops》+行业实践)**:
1. 先排除数据假象(GSC data anomalies 页;clicks-only 还是 clicks+impressions 同降);
2. 下降形态:断崖全站→算法/spam/安全;逐年重复波形→季节性(拉 16 个月+Trends 验证);单页/单模板→技术;缓慢下滑→内容相关性;
3. 时间对齐:下降首日 vs 官方更新窗口,**同时对照自家发布日历**——区分技术事故最硬的信号;
4. 类目级传感器旁证;
5. GSC 分层(query/page/device/国家);**impressions 平+clicks 降→不是算法,是 SERP 特性/竞品截流(如 AIO)**;
6. **结论时点:rollout 完成后等 1–2 周**;2026 更新密集(8/9 月连续 spam),须先排除上一更新余波与更新重叠。

**2024–2026 官方时间线要点**(完整清单见 status.search.google.com):每年 3–4 次 core+1–3 次 spam;2024-01 后 **reviews 更新零次**(系统改持续迭代不再公告);2026 出现 **Discover update**(2/5)与超短 spam(19.5 小时,3/24);**2024-08-15 官方 ranking bug(4.5 天)证明技术事故与算法在同一官方流——归因必须能区分**。

**algorithm-updates 数据文件最小字段集**(漂移监控自动比对用):
```json
{"id":"2026-03-core","engine":"google","type":"core|spam|reviews|discover|bug_incident|unconfirmed_volatility","start_date":"2026-03-27","end_date":"2026-04-08","status":"complete|rolling_out","official_url":"…","source_tier":"official|vendor|community","scope":"global","impact_notes":"一句话","last_verified":"2026-10-09"}
```
**联动规则**:告警窗口 ∩ 更新窗口非空 → 打"疑似算法"标签而非直接升级;end_date 必填(归因窗口=end+7 天宽限);last_verified 驱动月度复核。**跨市场**:Yandex 官方博客会公告(ИКС 2026-02);Naver 无官方看板(统搜改革等仅博客转述,source_tier=community 降权);Bing 无算法公告流(只有 Webmaster 数据)。

## 五、与其他参考的联动

漂移规则命中的项直接路由：Schema 变更 → schema 校验参考；CWV 退步 → 性能参考；noindex 新增 → 索引审计；title/meta 变化 → 内容规范。

## 六、来源

- 13 元素/SQLite DDL/17 规则/归一化规则：[AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) `skills/seo-drift/SKILL.md`、`references/comparison-rules.md`、`scripts/drift_baseline.py`

## 增量:对照组归因与发布回归(百仓扫描批 2/4)

- **对照组归因**(seo-monster rank_attribution):改动页 vs 匹配对照组的前后对比+置信区间——比单纯前后对比强一档;
- **发布回归清单**(notfair seo-drift):基线快照→diff——**redeploy 覆盖了标题/元描述、canonical 或 noindex 翻转、schema 消失、索引页数下降**——每次发版后自动比对(与 13 元素基线互补:那个防漂移,这个防"改版踩坏")。
