---
description: 周报 / 月报 / 给老板或客户的 SEO 报告:结论带数据、对比期、数据源和口径。SEO/GEO report from your own data.
argument-hint: "[周报|月报|季度] [读者]"
---

# /seo-suite:report — 报告

参数:$ARGUMENTS(报告类型和读者;没给就问)。

## 先读
- `${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/references/monitoring/report-templates.md`(按读者取舍、共同规则)和 `${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/references/monitoring/kpi-definitions.md`。
- 报告里有 AI 可见度时先读 `${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/references/content/geo-evidence.md`。
- `seo-ops/`:方案(`plan/plan.json`)、近几期运营单(`runs/*/agenda.json`)、变更台账;`seo-ops/playbook/` 的规则(用户说过报告里必须有的东西)。

## 跑
- 月报:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/project.py" ops monthly`,再按 `${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/templates/monitor/performance-report.md` 填。
- 要 HTML:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/report_build.py" --findings findings.json --out report.html`。
- 每条结论写数据 + 对比期 + 数据源 + 口径;缺一项写「待核实」。

## 停下来问用户
- 读者是谁、要多长、要不要对外发:先问清楚。
- 报告要以用户名义发给客户或老板时,只出稿,由用户自己发。
