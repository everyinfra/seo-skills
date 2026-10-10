# Skill 自更新协议(信源变更→直接更新 skill)

> 建立于 2026-10-10。配合 intel_check.py 使用:当信源变更被检测到,本协议规定 agent 如何**直接更新 skill 文件**(不只是知识文档——规则/阈值/脚本/清单都改)。用户开定时任务(如每周一次)发送触发指令,agent 按本协议执行。

## 触发指令模板(用户的 cron 发这个)

```
检查信源并更新 SEO skill:
1. cd /path/to/seo-skills-work && python3 skills/seo-suite/scripts/intel_check.py check
2. 如有变更(退出码 1):按 self-update-protocol.md 逐个处理变更源
3. 更新受影响的 references/scripts 文件(按映射表)
4. python3 skills/seo-suite/scripts/self_check.py 必须全绿
5. git add -A && git commit -m "intel-update: <源名> <变更摘要>" && git push
6. 给一段简短中文总结:什么变了,改了什么
```

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
python3 skills/seo-suite/scripts/self_check.py   # 必须 OK(75 tests)
python3 skills/seo-suite/scripts/freshness.py skills/seo-suite/references --lines 3  # 无过期
```

### 第四步:提交推送

```bash
git add -A
git commit -m "intel-update <日期>: <源名> — <一句话变更> | 改了 N 文件"
git push
```

## 安全边界

- **自动可改**:份额数字/事实条目/来源链接/门户页数据——这些是"陈述性内容";
- **须人审后改**:评分权重/检查阈值/安全边界表——这些是"行为性内容"(改错会误导用户决策),标注 `[HUMAN-REVIEW]` 后 commit message 说明;
- **不改**:scripts/ 的核心逻辑(除非官方 API 变了导致脚本坏——那是 P0 修复);
- **每条新增带来源+日期**,不删旧条目(历史保留,用"已更新为"措辞)。

## 频率建议

| 检查 | 频率 | 原因 |
|---|---|---|
| 全量 intel_check | 周一次 | Google Blog 周更/Sensor 日更,周检能抓住主要变化 |
| StatCounter+Dashboard | 可加到 monitor.py 日检 | 份额漂移+事故检测 |
| freshness.py 扫 references | 月一次 | 兜底:防止漏检的过期声明 |
| 竞品仓扫描(GitHub API) | 双周 | 新趋势起点(见 intel-sources.md 检索式) |

## 来源

intel_check.py 源注册表与 references/overview/intel-sources.md 同步维护;本协议 2026-10-10 建立。
