# {答案式标题,例:"presence 34.2%(WoW +2.1pp)但增量全在 ChatGPT:Perplexity 连续两周走低、5 个消失提及全在 Perplexity——本周只做一件事,补 2 篇对比类内容"}

<!-- 数据纪律(与 ai-visibility-monthly.md 统一,违反任何一条即重写):
  1. 数据全部来自 scripts/citation_panel.py 的 report / diff 输出(内容侧可补 gsc_mining.py --decay);禁引入脚本输出之外的数字。
  2. 指标全平时(各引擎 |Δ|<5pp 且配对 n≥10)直接写 "stable, no action needed"——不制造紧迫感。5pp 与 n≥10 是 citation_panel.py diff 的 signals 节实现的本套件阈值(≥5pp 才报);借鉴 Scrunch Signals「只报有意义变化」的思路,厂商博客只说统计显著、没给这两个数。
  3. mention(Σmentioned,被提到)与 citation(brand_hits,被列为引用来源)是两个指标,分开呈现,禁合并成一个"曝光数"。
  4. 分引擎呈现,不合并成总计下结论:Profound 厂商研究(883,000 页、7 引擎)里,同一页面在不同引擎上的寿命相关仅 0.03-0.09(Google 三个面之间 0.12-0.17),单引擎涨跌不可外推其他引擎。
  5. 推算/人工归类的数字一律打 [est];数字缺失写 [要追加: 数据源],禁编造。
  6. 占位符约定:{{…}}=由 citation_panel.py 输出填充;{…}=人工填写。 -->

_For: {决策人} · Date: {YYYY-MM-DD} · Market: {目标市场/语言} · Period: {run1_id} vs {run2_id}(WoW) · Data pulled: citation_panel.py report+diff · Panel: {panel.json 路径,prompts N 条,engines M 个}_

> 多市场站点:逐市场各出一份本报告,不合并;引擎分列不合并总计。口径:presence=mention coverage=Σmentioned/成功 cell(cells−failed,no_answer 留分母计 0);citation 单指 share=brand_hits/domain_total(每答案每品牌至多 1 次,各品牌恒和 100%)。

## 1. Headline(The answer)

{两三句独立成立:总 presence {{visibility}}%(WoW {{delta_pp}}pp);最好平台 {{best_engine}}({{best_engine_visibility}}%)vs 最差平台 {{worst_engine}}({{worst_engine_visibility}}%),一句话点出差距来自哪。全平时整段写 "stable, no action needed"。只读这段的人不会错。}

WoW 口径:diff 配对分母(只比两期均成功=非 failed 的 cell),n={{paired_n}};n<10 时本段只当方向性观察并注明。`diff` 只比较同引擎、同探针指纹的两个 run;多引擎就每个引擎各跑一对。

## 2. 平台分解(Platform Breakdown)

行生成指令(每引擎一行,数据源:report 分引擎节 + 逐引擎 report --engine {engine} 与两期 per-engine diff):
{{per_engine_rows: engine|mentions|citations|visibility%|Δ}}

| 引擎 | mentions | citations | visibility% | Δ(pp,WoW) |
|---|---|---|---|---|
| {engine} | {该引擎 Σmentioned} | {该引擎 brand_hits} | {该引擎 coverage} | {本周−上周,配对分母} |

- mentions=被提到次数,name_only_mention+cited_brand 之和;citations=品牌域名进入引用来源的 answer 数——两列禁止相加或互换解读。
- 某引擎 failed 占比高时,该行 coverage 分母缩小,Δ 注明 "分母=成功 cell {n}"。

## 3. Sentiment 快照

{{sentiment_summary}}

口径:citation_panel.py 不产 sentiment,此项为人工标注(framing 四档:有利/中立/含糊/负面,见 references/monitoring/brand-mention-monitoring.md 第六节)。无标注时写 "N/A(本周无人工标注)",禁编造;标注样本 <10 条只当方向。

## 4. 竞争快照(SOV)

<!-- SOV 点名门槛(显式规则,不可省,本套件口径):|Δshare| ≥5pp 且配对 n≥10 才点名;<5pp 或 n<10 一律归"基本持平",不报数字细节、不制造紧迫感。 -->

| 品牌/域 | 本周 share% | 上周 share% | Δpp | 判定 |
|---|---|---|---|---|
| {我方 domain} |  |  |  | {点名/基本持平} |
| {同场竞品域,report co_cited top5} |  |  |  |  |

- 本周点名(≥5pp):{域+方向+pp 数;无人过门槛就写 "(无——全部基本持平)"}。
- 上周值由上期面板 run 重算;co_cited 域归入"竞品"为人工映射,打 [est]。

## 5. Top 5 变化 Prompt(涨跌都要,带平台)

{{changed_prompts}}

| 方向 | prompt | 平台(引擎) | 证据(run1→run2 状态) | 稳定性 |
|---|---|---|---|---|
| ↑ | {prompt} | {engine} | {如 brand_absent→name_only_mention} | {n≥3 且 CI95 不跨 0.5=stable;n<3=掷硬币,待确认} |
| ↓ | {prompt} | {engine} | {如 name_only_mention→brand_absent} |  |

选取规则:来自 diff 的新提及(↑)与消失提及(↓),按影响取前 5,涨跌都要有(单边不足时如实写少,不凑数);n<3 的 prompt 只标观察不下结论。

## 6. 本周动作(恰好一条)

{{single_action}}

格式:做什么 + 支撑数据点(哪条 Δ/哪个 prompt)+ 复查日 {YYYY-MM-DD}。全平台 |Δ|<5pp 且配对 n≥10 时,这里只写:"stable, no action needed——维持采样节奏,下次报告 {YYYY-MM-DD}"。禁止为"有产出"造动作。

## Slack 三行版(随报告推送)

> **AI 可见性周报 {YYYY-MM-DD}**:presence {{visibility}}%(WoW {{delta_pp}}pp)——{最显著发现一句,含平台名}
> **动作**:{{single_action}}
> 全文:{报告链接}

## 检查清单(出报告前逐项:检查什么 → 怎么查 → 通过/失败)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 面板规模够 | `python3 scripts/citation_panel.py report --panel panel.json`,读头部 `prompts=N runs=M cells=K` | 通过:prompts ≥10(脚本下限,低于 10 只当方向)。失败:<10 → 本期结论标「方向」 |
| 2 | 采样次数够下稳定结论 | 同一输出「每 prompt 稳定性」节 | 通过:下结论的 prompt 都有 ≥3 次有效采样,Wilson 95% CI 不跨 0.5。失败:「无 ≥3 次采样的 prompt」→ 不下结论 |
| 3 | WoW 对比可比 | `python3 scripts/citation_panel.py diff RUN1 RUN2 --panel panel.json`,读「可比」行与「配对 cell」 | 通过:同引擎、同探针指纹,配对 n ≥10。失败:不可比(换了引擎或探针)→ 不写 WoW |
| 4 | 点名只来自 signals 节 | 同一输出「signals」节 | 通过:只点名 `[signal]` 行(|Δ|≥5pp 且 n≥10);「stable 不报」的不写数字。失败:报告里出现 signals 节之外的 Δ |
| 5 | mention 与 citation 分列 | 对照报告「brand_visibility(被提)」与「source_visibility(被引)」 | 通过:两列分开写。失败:合并成一个「曝光数」 |
| 6 | 分引擎 | 读报告「分引擎」节 | 通过:每引擎一行,没有跨引擎总计下结论。失败:只给总计 |
| 7 | 人工项打标 | 搜报告里的 [est] 与 [要追加: 数据源] | 通过:竞品归类、sentiment 都带 [est] 或 N/A。失败:人工数字没标 |

## What could change this conclusion

- {数据缺口:sentiment 无脚本字段(人工标注,缺失即 N/A);citation share 依赖 --domain 已设;failed cell 多的引擎分母失真}
- {仅相关非因果:prompt 涨跌与同期内容/发布对齐是相关非因果;单引擎波动不外推其他引擎(跨引擎寿命相关 0.03-0.09,Profound 厂商研究)}
- {样本局限:prompts<10 或配对 cell<10 只当方向;单次引用检查=掷一次硬币(同一 prompt 重复采样结果会变,[Peec 2026-09-29](https://peec.ai/blog/the-key-to-prompt-tracking)),n<3 不下结论}
- {继承假设:品牌别名与 domain 沿用面板 init 口径;引擎清单与上期一致,新增引擎单独标注}

## Method Notes

- 数据源与抓取时间:{panel.json + 两次 run 的 run_id/日期 + report/diff 命令}。已知坑:{no_answer 计 0 留分母;failed 不入任何分母;cited=1 蕴含 mentioned=1}。数字缺失写 [要追加: 数据源],禁编造。
- 符号:presence=mention coverage;WoW Δ 为配对分母口径的百分点差(pp);SOV=citation share;五状态=no_answer/failed/brand_absent/name_only_mention/cited_brand;稳定判据=同一 prompt ≥3 次有效采样,Wilson 95% CI(z=1.96)跨 0.5 即 unstable。
