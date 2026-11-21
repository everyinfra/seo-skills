---
description: 每周运营单:硬告警 > 方案本周路线项 > 只做一件;跑你启用的自定义检查,按你的规则过滤建议。Weekly SEO ops agenda.
argument-hint: "[--no-net]"
---

# /seo-suite:weekly — 每周运营单

## 先读
- `${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/references/monitoring/ops-agenda.md`。
- `seo-ops/`:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/loops.py" status --ws seo-ops`(档案上次核对日、阶段、方案第几周、到期循环)。
- `seo-ops/playbook/`:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/teach.py" show`(规则、禁用清单、自定义检查)。

## 跑
- `python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/project.py" ops weekly`(在站点仓根目录;离线时加 `--no-net`),读 `seo-ops/runs/<日期>/agenda.md`。
- 运营单「2.6 你的规则和检查」一节:禁用清单去掉了什么、每个已启用检查的结果、哪个检查脚本改过被自动停用。
- 只做运营单推荐的那一件;改代码开分支、开草稿 PR,不推主干;做完 `project.py ops ack`。

## 停下来问用户
- 运营单里有「要问用户的」(档案核对、产品变了、到了下一阶段门槛):用 AskUserQuestion 问,最多 3 个,只问变了的;答完 `loops.py resolve … --quote "<原话>"`。
- 有检查「脚本改过、已自动停用」:把改动给用户看,确认后 `teach.py check try` 再 `check enable --quote`,没确认前不跑。
- 推荐的那件事要动线上配置、外发(外联、提交收录)时,先给用户确认,只起草。
