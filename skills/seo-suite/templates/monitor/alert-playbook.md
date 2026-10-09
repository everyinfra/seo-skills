# {答案式标题,例:"本次触发的是 warn 级 gsc_clicks_drop(-28%×地板 200):按 L1-L3 三步查,先排除季节性再查 5·08 发布"}

_For: {值班人/决策人} · Date: {YYYY-MM-DD} · Alert type: {ranking drop / traffic drop / indexing anomaly / backlink loss / schema issue} · Fired: {monitor.py code+首次触发时间} · Market: {目标市场/语言}_

> 多市场站点:逐市场各出一份本报告,不合并。告警阈值按市场基线,不跨市场套用。市场差异规则见 references/overview/multilingual-workflow.md。

## The answer

{一段独立成立:这是什么级别的什么告警+初步归因到 L 几+下一步动作与负责人+是否升级。只读这段的人不会错。}

## Key numbers

| 指标 | 数值 | 对比/阈值 |
|---|---|---|
| 告警级别 | {critical/warn/info/low} | 分级见下表 |
| 触发阈值 vs 实测 | {阈值} vs {} | {如 -20%×地板 100,实测 -28%} |
| 影响范围 | {} | {全站/单国/单页组/N 词} |
| 连续命中次数 | {} | 升级硬规则:影响面扩大×连续命中才升级 |

## Alert Tier Table(告警分级表)

对齐 continuous-operations.md 的四级 × playbook;列:症状/查哪/何时升级/自动 or 人审。

| 级别 | 症状(典型 code) | 查哪 | 何时升级 | 自动 or 人审 |
|---|---|---|---|---|
| critical | `homepage_down`/`key_page_down`(≥400)、`robots_sitewide_block`、`visibility_zero`、SSL 过期≤7 天 | 立即查发布记录与 CDN;robots 逐行 diff;GSC 网址检查+处罚通知 | 立即处理;1 小时未定位→按 L1–L5 协议走 | auto 项直接执行;其余人审当天 |
| warn | `visibility_drop`/`sitemap_urls_drop`/`gsc_clicks_drop`(百分比×地板)、`content_regression`、`dead_man` | GSC 分层(query/page/device);sitemap 管道;本机网络→DNS→WAF;cron 调度 | 连续 2 周期命中或恶化成 critical 形态 | draft PR 人审;1–2 个工作日 |
| info | `title_meta_drift`(分字段)、`robots_changed`、`ai_posture_flip`、`latency_spike` | diff 变更是否有意;对齐发布日历 | 无升级路径;周报汇总后决定 | 人审,排进本周 |
| low | `*_resolved`(自愈) | 不查;周报复核一眼 | — | 全自动,静默 |

升级硬规则:只有"影响面扩大×连续命中"才升级,单次越界不升级;事件型(critical 类)不受此约束。双窗口判定:critical 需昨日短窗+7 天基线同向确认,7 天基线同异常时降 info 并注明。

## Escalation Chain(升级链)

按 seo-drift-monitoring.md 五层根因顺序逐层推进,每层写"查什么/判据/通过则进下一层":

1. **L1 变化是否真实**:tracking 断档/bot/口径/季节性(要 YoY 不要 MoM;GSC clicks 与 sessions 同向 ±10–20%)
2. **L2 定位**:国家/设备/区块/品牌 vs 非品牌/落地页(单国跌=本地算法;仅移动跌=移动可用性;非品牌跌=算法…)
3. **L3 页面级**:位置跌+SERP 不变=质量;位置稳+CTR 跌=SERP 特性变化;同日 deploy+drop=强相关非证明
4. **L4 技术**:Recent deploys are the prime suspect(重定向 1 跳/4xx 5xx/sitemap/hreflang/抓取率)
5. **L5 外部**:算法/竞品/需求/处罚;归因到处罚分支转 penalty-recovery.md

升级时效:critical 立即→1h 未定位全链拉人;warn 2 个周期;本例当前停在 L{}。

## Worked Example(示例)

> 告警:`warn gsc_clicks_drop`(周一 run,非品牌点击 -28%,地板 200)
> L1:YoY 同期形态不一致(去年本周 +3%)→真实下降;GSC 与 GA4 organic 同向(-25%)→非 tracking。
> L2:仅 desktop 跌 {}%,mobile 持平;品牌词持平,非品牌跌 → 算法面而非品牌面。
> L3:掉的是 {cluster} 页组,排名 {稳/跌},CTR {}%→{}% → {判定}。
> L4:对照 deploy 日历:{日期发布} 与下降同日 → {拉回滚/继续取证}。
> 结论+动作:{...};下次复查:{YYYY-MM-DD}。

## Response Steps(本次执行记录)

1. {已做:查了什么,结果一行}
2. {待做:动作+owner+期限}
3.

## What could change this conclusion

- {数据缺口:GSC 2-3 天延迟,窗口可能仍不完整;bot 过滤不可用时 L1 判据弱化}
- {仅相关非因果:同日 deploy 是强相关非证明,要找到机制才定案}
- {样本局限:告警基于 {} 词/页的追踪集,长尾盲区}
- {继承假设:阈值与地板沿用 {日期} 校准的基线;改版后须重建}

## Method Notes

- 数据源与抓取时间:{monitor.py run id+GSC 导出+GA4+日期}。已知坑:{维护窗口内 diff 只留档不告警;quarantine 隔离污染 run;单次越界不升级}。数字缺失写 [要追加: 数据源],禁编造。
- 符号:四级=critical/warn/info/low;L1–L5=五层根因链(seo-drift-monitoring.md);本模板与 scripts/monitor.py 的 code 一一对应。
