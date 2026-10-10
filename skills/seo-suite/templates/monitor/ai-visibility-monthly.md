# {答案式标题,例:"10 月 presence 稳在 33-35% 带内但 citation share 月降 4pp:引用正被两家评测站吃走——下月首务是把 Bottom5 中 3 个主题改成可引用格式"}

<!-- 数据纪律(与 ai-visibility-weekly.md 统一,违反任何一条即重写):
  1. 数据全部来自 scripts/citation_panel.py 的 report / diff 输出(Content Health 可补 gsc_mining.py --decay);禁引入脚本输出之外的数字。
  2. 指标全平时(各引擎 |Δ|≤5pp 且配对 n≥10)直接写 "stable, no action needed"——不制造紧迫感(Scrunch 官方原则)。
  3. mention(Σmentioned,被提到)与 citation(brand_hits,被列为引用来源)是两个指标,分开呈现,禁合并成一个"曝光数"。
  4. 分引擎呈现,不合并成总计下结论:跨引擎相关仅 0.03-0.09(Profound 官方),单引擎涨跌不可外推其他引擎。
  5. 推算/人工归类的数字一律打 [est];数字缺失写 [要追加: 数据源],禁编造。
  6. 占位符约定:{{…}}=由 citation_panel.py 输出填充;{…}=人工填写。 -->

_For: {决策人} · Date: {YYYY-MM-DD} · Market: {目标市场/语言} · Period: {YYYY-MM 月,含 runs N 次(月初 {run_first} → 月末 {run_last})} · Data pulled: citation_panel.py report(月内全部 runs)+diff(月初/月末){+gsc_mining.py --decay} · Panel: {panel.json 路径,prompts N 条}_

> 多市场站点:逐市场各出一份本报告,不合并;引擎分列不合并总计。口径:presence=mention coverage=Σmentioned/成功 cell(cells−failed);citation share=brand_hits/domain_total(各品牌恒和 100%)。

## 1. Executive Summary(The answer)

{恰好 3 句,一句一件事:① 总体健康——presence 月均 {{presence_avg}}%(MoM {{presence_mom_pp}}pp)、citation share 月均 {{share_avg}}%(MoM {{share_mom_pp}}pp),处于 {健康/观察/处置} 带内;② 本月最大赢——{{biggest_win}}(哪个引擎/主题,带数据点);③ 下月首务——{{top_priority}}。全平时①写 "stable, no action needed",②③如实写"无显著赢面/维持采样"。只读这段的人不会错。}

## 2. Visibility Performance

mention 与 citation 两条线分开(被提不被引=内容不被信任;被引不被提=品牌关联弱),分引擎不合并:

| 引擎 | mention coverage(月均) | MoM Δ(pp) | citation share(月均) | MoM Δ(pp) | 判定 |
|---|---|---|---|---|---|
| {engine,来自 report 分引擎节} |  |  |  |  | {点名/基本持平} |

周内趋势(月内各期 run,diff 链):

| run(日期) | 总 presence | 总 share | 配对 n(vs 前一期) |
|---|---|---|---|
| {run_id} |  |  |  |

五状态分布(月初 vs 月末,来自两期 report):

| 状态 | 月初 | 月末 | Δ |
|---|---|---|---|
| no_answer(留分母计 0) |  |  |  |
| failed(不入分母) |  |  |  |
| brand_absent |  |  |  |
| name_only_mention(被提不被引) |  |  |  |
| cited_brand |  |  |  |

## 3. Competitive Position(SOV)

<!-- SOV 点名门槛(显式规则,不可省):|Δshare| > 5pp 且配对 n≥10 才点名;≤5pp 或 n<10 一律归"基本持平",不报数字细节、不制造紧迫感。 -->

| 品牌/域 | 本月 share% | 上月 share% | Δpp | 判定 |
|---|---|---|---|---|
| {我方 domain} |  |  |  | {点名/基本持平} |
| {同场竞品域,report co_cited top5} |  |  |  |  |

- 月度点名(>5pp):{域+方向+pp 数;无人过门槛就写 "(无——全部基本持平)"}。
- 引用阵地:品牌被引集中在 {主题/引擎};竞品反超的主题 {列举} [est: 主题归类为人工映射]。
- 上月值由上期 runs 重算;co_cited 域归入"竞品"为人工映射,打 [est]。

## 4. Content Health

**Top5 主题保护**(coverage 高且采样 ≥3 次稳定的长处,守住不动):

| 主题 [est: 人工归类] | 代表 prompt | coverage | 稳定性(n≥3,CI95) | 保护动作 |
|---|---|---|---|---|
|  |  |  |  | {不改动/持续监测} |

**Bottom5 待修**(brand_absent 与 name_only_mention 集中的主题):

| 主题 [est] | 主要状态 | 缺口类型 | 修复入口 |
|---|---|---|---|
|  | {brand_absent / name_only_mention} | {有答案没我们=内容缺口;被提不被引=内容不被信任,改可引用格式} | {页面/新建/改写} |

内容侧补证:gsc_mining.py --decay 的衰退页与 Bottom5 主题交叉时优先修(来源标 decay,非 citation_panel 输出)。

**Citation health 三分**(本周期去重引用域名总数 domain_total={{domain_total}} 的构成):

| 类别 | 域名次数 | 占比 | 说明 |
|---|---|---|---|
| brand | {{brand_hits}} |  | 我方域名被引(brand_hits) |
| competitor |  |  | [est: co_cited 中人工映射为追踪竞品] |
| third-party |  |  | 其余评测站/媒体/UGC=domain_total−brand−competitor |

三分之和=domain_total;competitor 为人工归类,打 [est]。

## 5. Recommendations(恰好 3 个)

| # | 做什么 | 支撑数据点 | 成功标准 |
|---|---|---|---|
| 1 | {动作} | {report/diff 的哪个字段哪条 Δ,如 "ChatGPT coverage -6pp,配对 n=42"} | {可复测判据,如 "4 周内该主题 coverage ≥X% 且 Wilson CI95 不跨 0.5,配对 n≥10"} |
| 2 |  |  |  |
| 3 |  |  |  |

全月指标全平(各引擎 |Δ|≤5pp 且配对 n≥10)时,3 条全部为维持性动作(补采样至每 prompt n≥3、扩 prompts 至 ≥10、下月复查),禁造新动作。

## What could change this conclusion

- {数据缺口:sentiment 无脚本字段;citation share 依赖 --domain 已设;--decay 数据为 GSC 口径,与面板采样不可直接对表}
- {仅相关非因果:主题修复与 coverage 回升的对齐是相关非因果,须前后对照 run 定案;单引擎结论不外推(跨引擎相关 0.03-0.09)}
- {样本局限:prompts<10 或配对 cell<10 只当方向;单次引用检查=掷硬币,n<3 的 prompt 不进 Top5/Bottom5 判定}
- {继承假设:主题归类、竞品域清单、别名与 domain 沿用本月口径;下月变更须在头部说明并回算}

## Method Notes

- 数据源与抓取时间:{panel.json + 月内 runs 清单 + report/diff/--decay 命令与日期}。已知坑:{月均值按 cell 加权而非各周简单平均;no_answer 计 0 留分母;failed 不入分母}。数字缺失写 [要追加: 数据源],禁编造。
- 符号:presence=mention coverage;share=citation share;MoM Δ 为月初/月末 run 配对分母口径 pp 差;五状态=no_answer/failed/brand_absent/name_only_mention/cited_brand;稳定判据=同一 prompt ≥3 次有效采样,Wilson 95% CI(z=1.96)跨 0.5 即 unstable。
