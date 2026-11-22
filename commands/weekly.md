---
description: 每周运营单:硬告警 > 方案本周路线项 > 只做一件;跑你启用的自定义检查,按你的规则过滤建议。Weekly SEO ops agenda.
argument-hint: "[--no-net]"
---

# /seo-suite:weekly — 每周运营单

## 跑
- 开局做完的站只跑一条:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/project.py" ops weekly`(在站点仓根目录;离线时加 `--no-net`)。
- 把输出最前面两行等号之间「原样发给用户」那一块原样贴出(档案上次核对日、阶段、方案第几周、这周做哪件、要问的问题),再照紧跟着的「给 agent」那段做。现状以这条命令现算的为准,不读 `seo-ops/runs/*/agenda.md` 旧运营单,不自己另写摘要。
- 运营单「2.6 你的规则和检查」一节:禁用清单去掉了什么、每个已启用检查的结果、哪个检查脚本改过被自动停用。
- 只做运营单推荐的那一件;改代码开分支、开草稿 PR,不推主干;做完 `project.py ops ack`。
- 要细看规则和检查:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/teach.py" show`。参考:`${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/references/monitoring/ops-agenda.md`。

## 停下来问用户
- 首屏那一块里有问题才停下等回复,没有就不停。用户答了,照抄「给 agent」里印的 `loops.py resolve … --quote "<用户原话>"` 落档(「都没变 / carry on」只带 `--quote`;加了产品线用 `--add product.lines=<名字>`;换阶段用 `--stage <阶段号>`)。
- 缺的材料(平台主页链接、源码位置、正式域名)写成陈述句的「待你补的材料」,不编号、不带问号、不为它停下。
- 有检查「脚本改过、已自动停用」:把改动给用户看,确认后 `teach.py check try` 再 `check enable --quote`,没确认前不跑。
- 推荐的那件事要动线上配置、外发(外联、提交收录)时,先给用户确认,只起草。
- 路线要重排(换了阶段、季度复盘):`plan.py build --replan`,新方案发给用户确认后才算数。
