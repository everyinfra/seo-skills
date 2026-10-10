# AI 可见性面板报告(演示数据):Nimbus Analytics 覆盖 60.0%、引用份额 44.4%——**本目录全部数据为手工构造的合成数据,只演示交付物形态,不来自任何真实采样**

_For: 品牌/Growth 负责人 · 面板: panel.json(brand=Nimbus Analytics,domain=nimbus.example,竞品 rival.example) · 渲染口径: citation_panel.py report 原样输出存 evidence/01-report.md · 采样窗口(虚构): 2026-10-07 ~ 2026-10-09 · 引擎: chatgpt, perplexity_

> **演示数据声明**:本例是 citation_panel 工作流的**合成演示**——品牌、域名、竞品、36 个 cell(6 prompts × 2 引擎 × 3 天)全部虚构,五状态(no_answer/failed/brand_absent/name_only_mention/cited_brand)各有覆盖。目的是展示"panel.json 怎么建、report 长什么样、数字怎么读";任何数字都不可对外引用,也不构成对任何真实品牌的判断。
> **快照免责声明**:即便是真实面板,报告也是采样窗口的单点时间快照,AI 引擎的回答会漂移;示例展示的是交付物形态而非目标站现状。

## The answer(先读这段)

36 个 cell 的演示面板:mention coverage 60.0%(21/35 成功 cell),citation share 44.4%(16/36 引用域命中,同场最大对手 rival.example 19.4%),SoV 69.6%,win_rate 18.8%(3/16),被提(60.0%)与被引(48.5%)差 11.5pp——差距<20pp 未触发"被提≠被引"警报(evidence/01)。两条 prompt 的置信区间跨 0.5 判 UNSTABLE,不下结论;`prompts=6 <10`,整套数字只能当方向(脚本自身告警,见 evidence/01 末行)。

## Key numbers(全部出自 evidence/01-report.md,编号回溯)

| 指标 | 数值 | 口径 |
|---|---|---|
| cells / runs / prompts | 36 / 6 / 6 | 2 引擎 × 3 天 × 6 prompts |
| 五状态分布 | cited_brand 16(44.4%)· brand_absent 12(33.3%)· name_only 5(13.9%)· no_answer 2(5.6%)· failed 1(2.8%) | failed 不入分母,no_answer 计 0 留分母 |
| mention coverage | 60.0% | Σmentioned 21 / 成功 cell 35 |
| citation share | 44.4%(16/36) | 每答案每品牌至多计 1 次,各品牌恒和 100% |
| SoV | 69.6%(16/23) | 提及以引用域命中为代理 |
| win_rate / citation_rate | 18.8%(3/16)· 1.09 次/响应 | 有 rank 列才报 win_rate |
| brand vs source visibility | 60.0% vs 48.5%(差 11.5pp) | 差距>20pp 才告警 |
| 分引擎 | chatgpt coverage 58.8%/share 44.4%;perplexity 61.1%/44.4% | 按引擎分列,不合并统计 |

## 怎么读这张面板(演示要教的读法)

- **五状态先于一切百分比**:1 个 failed cell 是采集失败,不是内容缺口——它已从分母剔除;2 个 no_answer 留在分母计 0。忽略这一步会把"引擎没给答案"误读成"品牌不够好"。
- **稳定性闸门**:同一 prompt ≥3 次采样才报 Wilson CI;"cheapest alternative..."(p=0.33,CI 跨 0.5)与"how to reduce churn..."(p=0.33)判 UNSTABLE——单次引用检查=掷硬币,这两条不进任何结论。
- **结构性缺口看 brand_absent 与 name_only 的分布**:12 个 brand_absent 集中在"open source"(6/6 全零,p=1.00 CI[0,0] 稳定的零)——这是稳定的内容缺口信号;"churn"类 name_only 偏多=被提不被引,改可引用格式(列表/定义块)。
- **同场竞品域**是外联与内容对标清单(rival.example 19.4% 之外,dataschool.io 16.7% 等中性域也占引用池——份额争夺不只在竞品)。

## What could change this conclusion

- 演示数据本身无结论可翻——真实使用时,首要变数是采样密度:3 天窗口不足以做 diff(配对分母)与 decay(资格闸门要求观察窗 ≥28 天、峰值窗内采样 ≥5,本面板不满足,故未演示 `diff`/`decay` 子命令)。
- prompts=6 <10 是脚本硬告警:真实面板应按 Scrunch 5+3+2 配方起步 10+ 条(见 `citation_panel.py init --stage-mix`)。
- SoV 用"引用域命中"代理文本提及(record 未存竞品文本提及)——文本提及口径的 SoV 会与本表不同。

## Methodology(合成数据构造 + 精确命令行;均在 skill 根目录 skills/seo-suite/ 执行,输出目录为本示例目录)

1. 手工编写 `inputs/prompts.csv`(6 条非品牌 prompt,stage 列 awareness/consideration/decision)与 6 个 run CSV(`inputs/run-{chatgpt,perplexity}-2026100{7,8,9}.csv`,列: prompt,mentioned,cited,cited_urls,state,rank;五状态在 36 cell 中各有覆盖)。
2. `python3 scripts/citation_panel.py init --brand "Nimbus Analytics" --aliases Nimbus --domain nimbus.example --competitors rival.example --engines chatgpt,perplexity --prompts-file examples/citation-panel-demo-20261010/inputs/prompts.csv --panel examples/citation-panel-demo-20261010/panel.json`
3. 6 次 record(每天每引擎一条;run 文件自动落 `runs/`):`python3 scripts/citation_panel.py record --engine chatgpt --file examples/citation-panel-demo-20261010/inputs/run-chatgpt-20261007.csv --date 2026-10-07 --panel examples/citation-panel-demo-20261010/panel.json`(其余 5 条同型,引擎/日期/文件名对应替换)
4. `python3 scripts/citation_panel.py report --panel examples/citation-panel-demo-20261010/panel.json > examples/citation-panel-demo-20261010/evidence/01-report.md`

## Method Notes

- 三层结构:本 REPORT(叙事层)→ evidence/01-report.md(工具原样输出层)→ panel.json + runs/*.json + inputs/*.csv(原始数据层);叙事层每个数字可在下层原样找到。
- 指标口径:coverage/share/CI/SoV/win_rate/citation_rate/brand vs source visibility 公式见 citation_panel.py 模块 docstring(Peec/unifapi/Scrunch 官方口径,标注纪律同全库)。
- 禁编造:本例数据为**显式声明的合成数据**(这是演示目录的合法形态);真实运行时禁用合成数据,采样失败如实记 failed。
