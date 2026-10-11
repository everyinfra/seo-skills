# SEO 程序管理:大改 PRD、小改 ticket、证据库与治理 RACI

> 建立于 2026-10-12,来自 20 视角调研 R6"运营体系"(SEJ 2026-10 / decaseo / SearchPilot×Upwork 2026-02 /
> srnaseo 2026-04 等;调研摘要登记于 [pipeline-completeness](../overview/pipeline-completeness.md) 第五节)。
> 定位:SEO 一旦超过一个人、跨内容/前端/后端/法务多团队,就必须按产品管理(PM)纪律运作。本文件管
> **"改动怎么立项、审批、复盘"**;机器节奏(日/周/月监控)与人的节奏(四层 cadence/RICE)见
> [continuous-operations](continuous-operations.md);算法 rollout 期间的变更冻结与解冻后排期见
> [seo-drift-monitoring](seo-drift-monitoring.md) 第五节第 0 步;实验判定口径(DiD/split test/置信度纪律)
> 沿用该文件,不在此重复。

## 一、为什么 PM 化:三种失败模式

- **无 PRD**:大改(迁站/模板改版)只有口头共识,上线后无人能回答"当初为什么这么改、成功标准是什么";
- **无证据库**:每次测试的结论随会议纪要一起遗失,下个季度重做同样的测试(SearchPilot×Upwork 2026-02:
  企业 SEO 测试结果的内部复用率极低,证据库是对策);
- **无治理**:三个人同时改 title 模板、迁站没人签字、新成员上手靠口口相传——出了事查不到决策链。

**改动分级速查**:

| 触发 | 形态 | 审批 |
|---|---|---|
| 模板级 title/meta、迁站/换域名/换 CMS、URL/canonical 体系、pSEO 批次 | PRD | A 角色签字 + launch gate |
| 单页 title/meta、单页刷新、技术 bug | ticket | SEO 负责人 |
| 算法 rollout 冻结期积压的变更 | 冻结队列 | 解冻后按 RICE 重排,不按提交顺序 |

**升级触发**:ticket 的影响面从单页扩到页面族/模板(如同一 bug 在模板层)时,强制升 PRD;
PRD 判读窗口撞上算法 rollout 时冻结顺延(不做"边 rollout 边判读")。

## 二、大改走 PRD

**判断标准(任一命中即 PRD)**:全站或模板级 title/meta 变更;迁站/换域名/换 CMS;URL 结构或 canonical
体系变更;批量内容(pSEO 批次)上线;波及多个模板/页面族的代码改动。

### PRD 六件(模板)

1. **问题**:现状+量化证据(GSC/审计数据;不接受"感觉排名不行");
2. **假设**:单句 **"若 X 则 Y,因 Z"**——X=具体改动,Y=可测业务指标(clicks/注册,不是"SEO 变好"),
   Z=机制(为什么 X 能导致 Y)。写不出 Z 的假设退回重写;
3. **Why now**:为什么这个季度做(算法动向/竞品动作/资源窗口),过期作废;
4. **不可破坏项(non-negotiables)**:高流量承载页清单/合同义务页/法务合规页——PRD 的任何方案不得触碰,
   违者 launch gate 拦下(见第五节);
5. **时间线**:`baseline 采集 → 变更窗口 → 判读窗口`。判读窗口 ≥4 周;算法敏感改动的窗口还要避开更新
   rollout(撞上即冻结顺延,见 seo-drift-monitoring 第五节第 0 步);
6. **成功度量与判读口径**:主指标 + 对照构造(DiD 控制组或 split test)+ 提前中止条件(恶化到什么程度回滚)。

## 三、小改走 ticket

单页 title/meta、单页内容刷新、技术 bug 修复走 ticket,**三要素缺一不立**:改什么(精确到 URL/字段)、
为什么(证据链接或所属 PRD 编号)、验收标准(diff 后复测什么指标)。

与套件实装衔接:`remediation.py` 工单状态机(proposed→accepted→in_progress→implemented→verified,
verify 自动核销)就是 ticket 的本地形态;`fix_plan.py --apply --git-branch` 落分支+draft PR 即
"起草+人审"边界(见 continuous-operations 第五节安全边界表)。

## 四、证据库(evidence bank)

每次测试/大改结案时**强制**归档一条(不归档=该实验白做):

```yaml
id: 2026-10-title-rewrite-pdp
change: PDP title 模板 "{product} | {brand}" → "{product} {modifier} | {brand}"
prd: PRD-2026-07            # 无 PRD 的小测写 ticket 链接
window: 2026-08-01 ~ 2026-09-15   # 变更+判读全窗
design: DiD(section 对照,pre 56d / post 28d)
result: clicks +6.2%(CI +1.1~+11.3,likely_positive)
verdict: 保留;Confidence 更新为 1.0(自家数据)
```

**复用规则**:新 PRD 的假设若与历史条目同机制,直接引用该 id 并据此抬 Confidence(RICE 因子口径见
continuous-operations 第二节);同机制的反例存在时,PRD 必须写明"为何这次不同"。

**归档时机**:判读窗口关闭、verdict 出来的当周归档(月 review 的固定议程之一);回滚的实验同样归档——
反例与正例等价,都是下一份 PRD 的 Confidence 输入。条目只增不删,结论被推翻时追加新条目并互链,不覆盖旧的。
与 [geo-evidence-bank](../content/geo-evidence-bank.md) 的分工:那是**对外**证据(论文/行业研究),
本库是**自家**实验——Confidence=1.0 只能来自本库。

## 五、治理 RACI(≥3 贡献者即启用)

| 决策 | R(执行) | A(拍板/签字) | C(咨询) | I(知会) |
|---|---|---|---|---|
| title/meta 模板变更 | SEO | SEO 负责人 | 品牌/法务 | 前端 |
| 迁站/换域名/换 CMS | SEO+前端 | 站点 owner(业务签字) | 基建/法务 | 全员 |
| launch gate 前置检查 | SEO | 发布经理 | 前端 | — |
| 嵌入式培训(新贡献者上手) | SEO | — | — | 全体贡献者 |

**RACI 纪律**:每行恰好一个 A;"A 不知道自己是 A"=治理失败,先修表再动工。launch gate 的机器部分
自动跑([ci-gates](ci-gates.md) 回归门 + monitor 基线),人只签两件事:**不可破坏项未触碰**、
**判读窗口与 owner 已登记**。

**launch gate 前置检查清单(合入主干前)**:
1. ci-gates 回归门绿(audit_compare --baseline-gate);
2. robots/canonical 无意外翻转(drift compare 17 规则零 CRITICAL);
3. 不可破坏项清单上的页 200 且 expect_substring 断言通过;
4. 判读窗口、主指标、回滚条件已写进 PRD 第 6 件并指定 owner。

## 六、agency SOW 阶段结构(外包参考)

| 阶段 | 内容 | 客户签发门(不签字不进下一阶段) |
|---|---|---|
| M1 | 审计+策略:技术/内容/外链审计,策略文档与路线图 | 策略与优先级签字 |
| M2–M3 | 执行:按 PRD/ticket 落地,双周交付物+月 review | 执行验收+KPI 基线确认 |
| M4+ | 增长:内容/外链/转化优化,季度 OKR 对齐 | 季度 business review |

**SOW 纪律**:交付物写"物"(审计报告/PRD/落地页面数),不写"活动"(会议/调研次数);测试与实验的
数据/结论 IP 归客户——直接进客户自己的证据库,换 agency 不换证据;退出条款含交接包(账号/证据库/文档),
防"人走史失"。

## 七、来源

- PRD 模板(问题/假设"若 X 则 Y 因 Z"/why now/不可破坏项/时间线)、证据库复用、治理 RACI(≥3 贡献者)、
  agency SOW 阶段结构(M1 审计+策略→M2-3 执行→M4+ 增长+客户签发门):20 视角调研 R6"运营体系"——
  SearchPilot×Upwork 2026-02(测试复用缺口)、srnaseo 2026-04(RACI/SOW 结构)、decaseo(PRD 纪律);
  登记于 [pipeline-completeness](../overview/pipeline-completeness.md) 第五节。
- 变更冻结与解冻后排期:SEJ 2026-10,见 [seo-drift-monitoring](seo-drift-monitoring.md) 第五节第 0 步;
- 四层节奏/RICE/领导层沟通(本文件的运行环境):[continuous-operations](continuous-operations.md) 第二节;
- DiD 参数、判读窗口与置信度纪律:[seo-drift-monitoring](seo-drift-monitoring.md);
- 本地实装:`scripts/remediation.py`(ticket 状态机)、`scripts/fix_plan.py --git-branch`(draft PR 通道)。
