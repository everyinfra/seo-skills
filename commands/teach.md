---
description: 教它你的规则:「以后都这样做」「别再建议 X」「加一个检查」,写进 seo-ops/playbook/,升级不覆盖;通用的整理成开源仓 PR 草稿。Teach seo-suite your own rules and checks.
argument-hint: "<你的原话>"
---

# /seo-suite:teach — 按你的想法教它

参数:$ARGUMENTS(用户原话,原样用)。

## 先读
- `${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/references/overview/playbook.md`(规则、禁用清单、自定义检查、自定义打法、数据源怎么写)。
- 现有的:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/teach.py" show`,避免记重复。

## 跑(按原话属于哪一类)
- **以后都这样做**:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/teach.py" rule add --quote "<原话>" --no-deny`。
- **别再建议 X / 我们不做 X**:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/teach.py" rule add --quote "<原话>" --deny <X 的关键词>`(关键词写推荐里会出现的词,比如 reddit);之后 plan、每周运营单、link_intel、prioritize、fix_plan、content_queue 都按它直接过滤。
- **加一个检查**:
  1. `teach.py check new <名> --desc "<用用户的话写>" --match "<页面网址正则>"`,按原话改 `seo-ops/playbook/checks/<名>.py`(零依赖,stdin 读页面 JSON,stdout 打印 {"pass", "findings"});
  2. `teach.py check try <名> --url U1 --url U2 --url U3`,把 3 个页面的结果原样给用户看,编号问「1. 这样判对不对?对的话我就启用。」,停下等回复;
  3. 用户说可以:`teach.py check enable <名> --quote "<原话>"`(记 sha256;脚本一改就自动停用)。
- **自定义打法**:写进 `seo-ops/playbook/plays.json`(格式同 `${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/data/playbooks.json`,必须带 stages),再 `plan.py build`。
- **提给开源仓**:`teach.py export <检查名>`,把换掉的站点专属内容和 PR 草稿给用户看。

## 停下来问用户
- `--quote` 照抄用户这一句,不改写,标点、全角半角也不改。记完把这一条(适用范围、禁用关键词)念给用户,不用专门问「对吗」,用户下一句没纠正就算确认;「不做 X」的 X 拿不准时先编号问、停下等回复,不替用户猜。
- 试跑完问「这样判对不对、要不要启用」是要用户拍板的事:编号问、停下等回复,不写成陈述句。
- 检查启用前一定先 try、给用户看结果;用户写的脚本当不可信代码,只在确认后跑。
- export 只生成文件:不提交、不推送;用户确认后他自己跑屏幕上给的 `gh pr create --draft …`。

## 做完
- 记完规则、启用完检查就汇报一次、收尾:顺带要补的现有页面(规则碰到的、试跑没过的)写成一句陈述的待办(「/a/、/b/ 两页还没有这一项,要补时说一声」),不编号、不问要不要补;用户只回「对」「好」「先这样」就是收尾,不把问题再列一遍。
- 原话里有 `$`(价格)时 `--quote` 整段用单引号(原话本身带单引号就用双引号,把每个 `$` 写成 `\$`);脚本看出金额被 shell 吃掉会退出码 2,什么都不写。
