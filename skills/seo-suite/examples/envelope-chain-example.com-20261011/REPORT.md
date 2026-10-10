# example.com 三源聚合 envelope(dev 视图):主分 0.0/100(Weak)进封套,13 规则项分派 立即 2 / 短期 5 / 持续 6,findings/*.md 3/3 类别齐落盘

_For: 工程师 · 母报告口径: full-seo-audit(dev 渲染见 [report-modes.md](../../templates/audit/report-modes.md)) · 渲染模式: dev · 上次审计基线: [site-audit-chain-example.com-20261010](../site-audit-chain-example.com-20261010/REPORT.md)(同站前日快照,仅作对照,不计算 delta——单页样本噪声大于真实变化) · 分数来源: health_score.py(输入 evidence/01-site-audit.json) · 采样: 2026-10-11,1 URL(https://example.com)_

> **快照免责声明**:本报告是 2026-10-11 的单点时间快照,数据会漂移;示例展示的是**三源聚合 envelope 的交付物形态**,不代表目标站现状。

## The answer(先读这段)

四步链(site_audit → health_score → prioritize → envelope)真实抓取 https://example.com 跑通:16 条原始 finding(2 CRITICAL / 7 WARN / 7 INFO,evidence/01)聚合成 13 个规则项、3 个 Lumar 类别的统一封套(evidence/04-envelope/audit-data.json);主分 **0.0 → Weak**(0/1 URL 无 CRITICAL,evidence/02)与 AI Search Health 70.0 一并写入 summary;三源全部 `ok`(audit/health/priority,无降级标记)。行动计划按 phases 分派:**立即(本周) 2 项**(2 条 CRITICAL)/**短期(月内) 5 项**(WARN 且 impact≥1.0)/**持续 6 项**——"立即"两项即 Quick wins 前二(description/h1,impact 3.0 取自 priority 输入)。部分落盘契约得到体现:3 个类别文件 findings/{indexability,discoverability,rankability}.md 全部在盘,audit-data.json 与 REPORT.md 最后写。

## Key numbers(编号回溯)

| 数字 | 值 | 出处 |
|---|---|---|
| 原始 finding | 16 条(2 CRITICAL / 7 WARN / 7 INFO;og 一条规则 3 条 WARN) | evidence/01 |
| 主分 / 分档 | 0.0 / Weak(0/1 无 CRITICAL;WARN 子分 0.0、INFO 子分 0.0 单列) | evidence/02 |
| 合成分(Lumar 六类) | 94.3(availability 100 / indexability 98.8 / discoverability 99.5 / rankability 89.2;uniqueness/experience N/A 不计) | evidence/02 |
| AI Search Health | 70.0/100(8/8 bot 放行;llms.txt 缺失、语义比值 0.0% 两项未过) | evidence/01(封套 summary 同值) |
| prioritize 立即处理 | 4 条:desc_missing 3.0 / h1_missing 3.0 / thin_content 2.0 / title_short 2.0;7 规则零命中、7 规则降级(缺 depth/inlinks 等页面级字段) | evidence/03 |
| envelope 规则项 | 13 项 = rankability 9 + indexability 2 + discoverability 2 | evidence/04-envelope/audit-data.json |
| phases 分派 | 立即(本周) 2 / 短期(月内) 5 / 持续 6 | evidence/04-envelope/REPORT.md |
| Quick wins | description 3.0(priority)/ h1 3.0(priority)/ og 2.0(估算) | evidence/04-envelope/REPORT.md |
| inputs 三源状态 | audit: ok · health: ok · priority: ok(无 source_missing) | audit-data.json inputs 节 |

## Today's priorities(dev 清单前 5,严重级×受影响面×修复成本;对照前日基线无新增)

1. `description` 1/1(100%)· CRITICAL · 成本 S —— 补 meta description(~155 字符)
2. `h1` 1/1(100%)· CRITICAL · 成本 S —— 补唯一 H1(与 title 呼应但不重复)
3. `canonical` 1/1(100%)· WARN · 成本 S —— canonical 改绝对 URL 并自指
4. `content` 1/1(100%,词数 27)· WARN · 成本 M —— 按 Botify 官方阈值增补实质内容
5. `title` 1/1(100%,14 字符)· WARN · 成本 S —— 扩到 50-60 字符

杠杆:整类修完比单条分散修提分多——最大杠杆类 **rankability**(9 项;整组修完主分 0.0→100.0,反事实重算见 Methodology 第 6 步)。

## 三源各供了什么(读封套的钥匙)

| 源 | 进封套的字段 | 本例取值 | 未供时(envelope 降级行为) |
|---|---|---|---|
| site_audit.py --json(必需) | 发现本身:13 规则项 × severity × affected_urls(≤20);AI Search Health | 16 finding → 13 项;70.0 | 缺它 envelope 不成立 |
| health_score.py --json | summary.main_score / band | 0.0 / Weak | 标 source_missing,分数字段缺省 |
| prioritize.py --json | impact 与修复文案(仅采信 hit_urls>0 的规则) | desc/h1 3.0、thin/title 2.0(priority);og 等 2.0(估算) | impact 全部按 severity×受影响面估算 |

impact 来源可逐项核对:quick_wins 里 description/h1 标 `impact_source: priority`,og 标 `estimated`——同在一条 quick win 清单里,口径不同也不混淆(audit-data.json summary 节)。

## 部分落盘契约(本例要演示的形态)

envelope 的写盘顺序 = **每聚合完一个类别立即写 findings/<category>.md,全部完成才写 audit-data.json 与 REPORT.md**——长审计/agent 编排被掐断时已完成类别不丢;`--resume` 时已有 findings/*.md 的类别跳过重建。本例 out-dir(evidence/04-envelope/)最终在盘:

- `findings/indexability.md`(2 项)/ `findings/discoverability.md`(2 项)/ `findings/rankability.md`(9 项)——人读表格 + 文末 `envelope-category-v1` 机器回读标记行
- `audit-data.json`(统一封套,13 规则项 + summary + action_plan 三阶段)
- `REPORT.md`(人读摘要,本报告 evidence/04 的入口)

3/3 类别文件齐 = 本次运行未被中断的完整形态;每份 findings/*.md 文末的注释行是 `--resume` 无损回读的底账(不手改)。

## What could change this conclusion

- **分母=1 是最大噪声**:与 [前日基线](../site-audit-chain-example.com-20261010/REPORT.md) 同因——单页样本下任何 CRITICAL 都使主分 0/1;多页样本下 envelope 的 affected_urls(≤20 封顶)与 phases 分派才有梯度可言。
- 前日基线 16 条(2C/5W/6I)与本日 16 条(2C/7W/7I)raw 条数相同但 WARN/INFO 分布不同——单页快照的计数抖动,不足以判"站点变了";两次样本口径一致前不计算 delta(Ryte coverage 口径)。
- prioritize 有 7 条规则因缺 depth/inlinks/similarity 等页面级字段**降级未生效**(evidence/03 degradation_notes)——若换 crawl 源补齐这些字段,envelope 的 impact 估计面会变。
- robots.txt/llms.txt/sitemap "不可达/缺失"判定的是 2026-10-11 的响应;example.com 是 IANA 保留域,随时可能变化。

## Methodology(脚本链与精确命令行;均在 skill 根目录 skills/seo-suite/ 执行)

1. `python3 scripts/site_audit.py https://example.com --json > examples/envelope-chain-example.com-20261011/evidence/01-site-audit.json`(真实抓取;退出码 1=存在 CRITICAL,输出照常落盘)
2. `python3 scripts/health_score.py --input examples/envelope-chain-example.com-20261011/evidence/01-site-audit.json > examples/envelope-chain-example.com-20261011/evidence/02-health-score.md`(退出码 1=Weak 档)
3. `python3 scripts/health_score.py --input examples/envelope-chain-example.com-20261011/evidence/01-site-audit.json --json > examples/envelope-chain-example.com-20261011/evidence/02-health-score.json`(envelope 的 --health 输入)
4. `python3 scripts/prioritize.py --audit examples/envelope-chain-example.com-20261011/evidence/01-site-audit.json > examples/envelope-chain-example.com-20261011/evidence/03-prioritize.md` 与同参 `--json > .../evidence/03-prioritize.json`(后者为 envelope 的 --priority 输入;两脚本均容忍 01 文件前部的逐 URL 文本行)
5. `python3 scripts/envelope.py --audit .../evidence/01-site-audit.json --health .../evidence/02-health-score.json --priority .../evidence/03-prioritize.json --out-dir examples/envelope-chain-example.com-20261011/evidence/04-envelope`(退出码 0;产出 audit-data.json + REPORT.md + findings/*.md 三类别)
6. 杠杆行反事实重算:`python3 scripts/health_score.py --input .../evidence/01-site-audit.json --ignore description,h1,content,title,headings,rendering,semantic-html,schema,og --json` → main_score 100.0(Excellent)。

## Method Notes

- 三层结构:本 REPORT(叙事层)→ evidence/01-03(三源各自原样输出)+ evidence/04-envelope/(envelope 落盘树 = 第四步原样输出层)→ 无额外交接文件,01/02.json/03.json 即复跑底账。
- 口径:主分=(无 CRITICAL URL ÷ 内链 URL)×100【Ahrefs 官方】;impact=prioritize(命中占比×严重度权重×放大器,本例无内链数据放大器均 1.0)【Botify 官方】;phases 分派=CRITICAL→立即 / WARN 且 impact≥1.0→短期 / 其余→持续【claude-seo E4】。
- 16(原始 finding 条)vs 13(envelope 规则项):og 在 01 里是 3 条独立 WARN,入封套按规则归并为 1 项——两个数字口径不同,均已注明出处,不是矛盾。
- 偏差记录:① 单页样本未生成 bulk-exports/*.csv(与 [site-audit-chain 示例](../site-audit-chain-example.com-20261010/REPORT.md)同款偏差);② 修复成本 S/M 人工标注;③ 与前日基线不计算 delta(单页样本,噪声>变化)。
- 禁编造:全部数字可回溯 evidence/01(JSON)→02(分数)→03(impact)→04(封套);本报告未引入任何 evidence 外的数字。
