# {答案式标题,例:"竞品 hubspot.com 同场被引 3 次而我们零被引:优先攻 g2.com(High,评级 B)争取列表位,capterra.com 只投一篇贡献内容"}

<!-- 数据纪律(违反任何一条即重写):
  1. 本简报数字全部来自 scripts/citation_gaps.py 的输出(输入为 citation_panel.py 的 panel.json);禁引入脚本输出之外的数字。
  2. 串联关系(顺序不可倒):先 citation_gaps.py 找目标域(哪里在被引、竞品是否同场)→ 再 cite_domain.py 对目标域评级(是否值得投入)→ 评级过关才写本简报并外联。先评级后找域是浪费。
  3. 优先级口径:has_competitor_run(竞品同场被引)= 唯一高优先判据;Standard 域仅当 cite_domain.py 评级 B 以上才排期。
  4. 同一 prompt ≥3 次采样才下稳定性结论(单次引用检查=掷硬币);qualifying cells<10 或 prompts<10 只当方向。
  5. 推算/人工判断的数字一律打 [est];数字缺失写 [要追加: 数据源],禁编造。
  6. 占位符约定:{{…}}=由 citation_gaps.py 输出填充(markdown/csv/json 同名字段);{…}=人工填写。 -->

_For: {决策人} · Date: {YYYY-MM-DD} · Market: {目标市场/语言} · Data pulled: `citation_gaps.py --panel {{panel}} --brand-domains {{brand_domains}} --csv gaps.csv --json gaps.json`(生成日期 {YYYY-MM-DD})· Panel: {{panel}},runs {{runs}} / qualifying cells {{qualifying}} · 目标域评级:cite_domain.py {{total}} → band {{band}}_

> 一个目标域一份简报,不合并;域间先后按 citation_gaps.py 域名排序(竞品同场降序 → 总引用降序)。竞品口径:panel.json 不记录竞品名单,"同场竞品"=同 cell 共同被引的其他非自有域[推断],外联前人工确认为真实竞品。

## The answer

{两三句独立成立:本域为什么值得外联(竞品 {{competitors}} 同场被引 / {{prompts_count}} 个追踪 prompt 引用本域共 {{count}} 次)、cite_domain.py 评级 {{band}}、建议动作(贡献内容/争取列表位/不动作)与预期收益表述。只读这段的人不会错。}

## 1. 目标域(Target Domain)

| 字段 | 值 | 来源 |
|---|---|---|
| 域名 | {{domain}} | citation_gaps.py 域名分组 |
| 优先级 | {{priority}}(High=竞品同场被引;Standard=仅我方缺席) | has_competitor_run |
| 总引用 / 页面数 | {{count}} 次 / {{pages}} 个被引页面 | 域名分组聚合 |
| cite_domain.py 评级 | {{total}} → band {{band}} | `python3 scripts/cite_domain.py --input answers.json`(数据项人工采集) |

评级不达 B 的 High 域:不发起外联,只做内容侧动作(见第 5 节),并注明 {评级不达标的原因}。

## 2. 竞品在场证据(Competitors Cited)

<!-- High 域必填本节;Standard 域写"无竞品同场被引",叙事改走收录线(第 6 节不在场口径)。 -->

- 同场被引竞品域:{{competitors}}(与 {{domain}} 同 cell 被引的非自有域)
- 外联口径(照抄脚本提示):{{outreach_tip}}

| 竞品域 | 同场 prompt 数 | 代表 prompt | 证据(run_id / 采样日期) |
|---|---|---|---|
| {competitor} | {{n}} [est] | {prompt} | {run_id, date, engine} |

## 3. 页面清单(Pages)

来自 citation_gaps.py CSV/JSON 中该域的行(逐页打开确认页面类型:listicle/评测/教程/文档——外联话术按类型选):

| URL | 被引次数 | 追踪 prompts(\|分隔) | 引擎 |
|---|---|---|---|
| {{url}} | {{count}} | {{prompts}} | {{providers}} |

## 4. AI 模型与 Prompt(AI Models + Prompts)

- 引用本域的引擎(providers):{{providers}}
- 追踪 prompt({{prompts_count}} 个):{{prompts}}
- 采样口径:qualifying cell=有 cited_urls 且品牌未被引(brand_absent/name_only_mention);cited_brand 的 cell 不算缺口;同一 prompt 采样 <3 次的计数只当方向。

## 5. 行动建议(Action)

1. {外联动作:贡献内容/争取列表位/提供可引用数据——按第 3 节页面类型选;High 域主打"列表位直接竞争",Standard 域主打"贡献可引用内容"}
2. {内容侧动作:补齐这些 prompt 主题下我方可被引资产(对照 Grounding Page checklist)}
3. 复查日:{YYYY-MM-DD}(重跑 citation_gaps.py,看该域 count/prompts 增量;increment 目标 {X} 次 [est])

## 6. 预期收益表述(Expected Benefit)

- 竞品在场(High):"竞品 {{competitors}} 在 {{domain}} 被引用——考虑贡献内容或争取列表位直接竞争。"
- 竞品不在场(Standard):"AI 模型在 {{prompts_count}} 个追踪 prompt 引用 {{domain}},获得收录可提升 AI 可见性。"
- 表述纪律:只承诺"争取同场/提升 AI 可见性",不承诺排名、流量或转化数字;收益复核以复查日 citation_gaps.py 的 count/prompts 增量为准,不凭单次采样下结论。

## What could change this conclusion

- {数据缺口:"竞品在场"以同 cell 共同被引的非自有域代理[推断],panel.json 无显式竞品名单;外联前须人工确认竞品关系}
- {仅相关非因果:域名被引频次与可争取性无因果;cite_domain.py 评级高≠对方会接受外联}
- {样本局限:qualifying cells<10、单 prompt 采样<3 次时,次数与同场判断只当方向}
- {继承假设:自有域清单=--brand-domains+面板 domain;引擎清单与 run 记录沿用 citation_panel.py 口径}

## Method Notes

- 数据源与抓取时间:{citation_gaps.py 完整命令行 + panel.json 路径 + 生成日期};评级来自 cite_domain.py(answers.json 人工采集 + 采集日期)。已知坑:{qualifying=品牌未被引的 cell;cited_brand 不算缺口;failed/no_answer 不入;自有域(含面板 domain)被引不计}。数字缺失写 [要追加: 数据源],禁编造。
- 符号:has_competitor_run=该 cell 有其他非自有域同场被引(唯一高优先判据);Priority=High/Standard;Prompts 列以 | 分隔;registrable domain=末两段(co.uk/com.cn 等双段后缀取三段);{{…}} 字段名与 citation_gaps.py --json 输出一一对应。
