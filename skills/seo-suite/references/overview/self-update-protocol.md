# Skill 自更新协议(信源变更→直接更新 skill)

> 建立于 2026-10-10;2026-10-15 按实际运行方式改写为「云端检测 + issue 工单 + 本地处理」。配合 intel_check.py 使用:当信源变更被检测到,本协议规定 agent 如何**直接更新 skill 文件**(不只是知识文档——规则/阈值/脚本/清单都改)。

## 两端分工

- **云端检测(自动)**:`.github/workflows/intel-update.yml` 每天 UTC 01:11 跑一次 intel_check;有变更就把本轮报告写进 label=`intel-update-pending` 的 issue(没有 open issue 就新开,已有就追加一条评论)。云端不改 skill 文件,也不自动关单。
- **本地处理(定时任务或人工)**:按下面的触发指令读工单、改文件、自检、提交、关单。频率自定(见文末「频率建议」);工单 open 超过 72 小时,云端会在 Actions 日志里报 warning。

## 触发指令模板(定时任务发这个)

`<REPO>` 换成本地克隆路径,`<OWNER/REPO>` 换成你的 GitHub 仓库。

```
检查 SEO skill 信源工单并更新:
1. cd <REPO> && git pull --rebase
2. 查工单:gh issue list -R <OWNER/REPO> -l intel-update-pending --state open
   有 open issue 就读正文和全部评论(每条是一轮报告:[CHANGED] 源 + 应更新文件)
3. 无工单(云端失败或没配 workflow):本地兜底跑 python3 skills/seo-suite/scripts/intel_check.py check
   退出码 0 = 无变更,1 = 有变更(报告格式同工单)
4. 有变更:按 self-update-protocol.md「更新流程」逐源处理
   (P0 规则级 / P1 事实级 / P2 事件级要改文件,P3 噪声跳过并记录;行为性变更标 [HUMAN-REVIEW])
5. python3 skills/seo-suite/scripts/self_check.py 必须全绿(测试数以仓库当前为准,不写死)
6. 只 add 本轮改过的文件(精确路径,不用 git add -A)
   git commit -m "intel-update <日期>: <变更源> <摘要>" && git push
7. 关单:gh issue close <N> -R <OWNER/REPO> -c "已处理: <摘要>"
8. 最终无变更:仓库根 .intel-cron.log 追加一行"<日期> 无变更",只 add 这个文件后 commit + push
9. 给一段简短中文总结:什么变了、改了什么(或"无变更")
绝不提交 API key/.env/.intel-state.json 和运行态产物(findings.json、crawl.json、briefs/ 已在 .gitignore)。
```

可选附加(按需写进同一个定时任务):

- **每周一**:有 citation 面板就跑 `python3 skills/seo-suite/scripts/citation_panel.py decay-summary --panel <panel.json> --json`,报告重写队列;`gh run list -R <OWNER/REPO> --limit 5` 看云端 workflow 是否全绿,红了只报告、不改 workflow。
- **每月 1 日**:数字巡检。实测脚本数(`ls skills/seo-suite/scripts/*.py | wc -l`)、测试数(`python3 skills/seo-suite/tests/run_tests.py` 的 `Ran` 行)、模板数(`find skills/seo-suite/templates -name '*.md' | wc -l`),对齐 README.md、README.en.md、manifest.json、`.claude-plugin/` 里的版本号与数字以及 CHANGELOG 最新版本;跑 `python3 skills/seo-suite/scripts/freshness.py skills/seo-suite/references` 列出过期断言(只报告,修复走正常工单)。

## 更新流程(收到变更报告后)

### 第一步:确认变更性质

intel_check.py 输出 `[CHANGED] <源名>: <详情>` + `→ 应更新: <文件列表>`。对每个变更:

1. **获取变更内容**:
   - RSS 源:读新条目标题+链接,fetch 原文确认;
   - hash 源:已过**二次拉取确认**(两次一致才算变更,报告里的就是稳定新内容),fetch 页面定位具体变了什么;
2. **判断影响级**:
   - **P0 规则级**:阈值/官方规则变了(如"CWV 阈值更新"→cwv-playbook 的数字要改)——必须改文件;
   - **P1 事实级**:数据/份额/统计变了(如 StatCounter 份额)——更新对应门户页+总览表;
   - **P2 事件级**:新功能/新公告(如"Search Console 新报告")——在对应模块加条目+来源;
   - **P3 噪声**:页面重构/无关变更——跳过,记录"确认无影响"。

> `unstable(连续N次)` 报告≠变更:intel_check 对 hash 源做了二次拉取确认,两次拉取结果不一致
> (JS渲染/动态页,如 StatCounter 图表页)自动按噪音跳过且不动基线——**无需任何处理**;
> 连续 3 次以上 unstable 的源只是"偶尔人工看一眼",不要据此更新文件。

### 第二步:按映射表更新文件

| 源 | 更新什么(不只加知识——改实际规则) |
|---|---|
| google-blog / google-updates | **改 validation-guide 的检查规则**/改 schema-examples 的状态表/改 llms-txt-guide 的规范描述 |
| gsc-announce | **改 intake-checklists 的闸门问题**/改 kpi-definitions 的口径 |
| status-dashboard | **改 seo-drift-monitoring 的归因规则**(新增事故加入时间线) |
| lighthouse | **改 agent-readiness 的 AGENTIC_BROWSING 审计解读**/改 agent-protocols 的卡片 |
| openai-bots / anthropic-crawl | **改 ai-crawler-policy 的 bot 表**(UA/robots 行为变了→规则改) |
| ard-spec / WebMCP | **改 agent-protocols 的速查卡+验证命令** |
| schema.org | **改 schema-templates 的字段清单**/改 audit-rule-catalog |
| crux | **改 cwv-playbook 的阈值表** |
| yandex-wm / naver-wm / baidu | **改对应市场门户页+markets.json 的引擎格局数字** |
| statcounter | **改 multilingual-workflow 的市场总表+对应门户页份额** |
| semrush-sensor / seroundtable | **改 seo-drift 的算法时间线**/改 penalty-recovery 的案例库 |
| bing-wm | **改 geo-platform-differences 的 Copilot 行** |

### 第三步:验证

```bash
python3 skills/seo-suite/scripts/self_check.py   # 必须 OK(全部金标测试通过)
python3 skills/seo-suite/scripts/freshness.py skills/seo-suite/references --lines 3  # 无过期
```

### 第四步:提交推送

```bash
git add <本轮改过的文件>   # 精确路径;git add -A 会把测试/脚本落在 CWD 的运行态产物一起带上
git commit -m "intel-update <日期>: <源名> — <一句话变更> | 改了 N 文件"
git push
gh issue close <N> -R <OWNER/REPO> -c "已处理: <摘要>"   # 有工单时
```

## 安全边界

- **自动可改**:份额数字/事实条目/来源链接/门户页数据——这些是"陈述性内容";
- **须人审后改**:评分权重/检查阈值/安全边界表——这些是"行为性内容"(改错会误导用户决策),标注 `[HUMAN-REVIEW]` 后 commit message 说明;
- **不改**:scripts/ 的核心逻辑(除非官方 API 变了导致脚本坏——那是 P0 修复);
- **每条新增带来源+日期**,不删旧条目(历史保留,用"已更新为"措辞)。

## 频率建议

| 检查 | 频率 | 原因 |
|---|---|---|
| 全量 intel_check(云端) | 每天 | workflow 自动跑,只检测、开/追加工单,不改文件 |
| 工单处理(本地) | 至少每周一次 | Google Blog 周更/Sensor 日更,按周处理能抓住主要变化;积压超 72 小时云端报 warning |
| StatCounter+Dashboard | 可加到 monitor.py 日检 | 份额漂移+事故检测 |
| freshness.py 扫 references | 月一次 | 兜底:防止漏检的过期声明 |
| 竞品仓扫描(GitHub API) | 双周 | 新趋势起点(见 intel-sources.md 检索式) |

## 来源

intel_check.py 源注册表与 references/overview/intel-sources.md 同步维护;本协议 2026-10-10 建立,2026-10-15 改为云端检测 + issue 工单 + 本地处理。
