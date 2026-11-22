# 用户的规则、检查、打法和数据源(seo-ops/playbook/)

Updated: 2026-11-21

用户说「以后都这样做」「别再建议 X」「加一个检查」「我们有自己的关键词数据」时走这里(RQ-237 例 6)。
这些东西放在**站点仓**的 `seo-ops/playbook/`,跟着站点仓提交;skill 升级只换 skill 自己的代码,不碰这个目录。

```
seo-ops/playbook/
  rules.md          用户原话,一条一节,带日期(teach.py rule add 写)
  deny.json         结构化禁用清单:「不做 X」(推荐脚本直接过滤)
  checks/<名>.py    用户自己的检查(零依赖脚本)+ <名>.md 说明 + registry.json(试跑记录、启用哈希;
                    文件在但读不了时,所有检查按「已停用:registry.json 读不了,等用户重新确认」处理,写入一律拒绝;
                    重新确认从 check try 开始,它先把读不了的原文件改名留下,再 check enable --quote)
  plays.json        用户自己的打法(格式同 data/playbooks.json)
  sources.json      用户登记的数据源(关键词量、SERP、外链……)
  export/<名>/      teach.py export 生成的开源仓 PR 草稿(不自动提交)
```

入口:`teach.py`(Claude Code 插件里是 `/seo-suite:teach`)。下文 `$S` 是 skill 的 `scripts/` 目录。

## 一、规则:用户原话进 rules.md

```sh
python3 "$S/teach.py" rule add --quote "以后我们的对比文都要放一张价格对照表" --no-deny --applies brief,plan
python3 "$S/teach.py" rule add --quote "别再建议我们去做 Reddit 外链了,我们不做" --deny reddit
python3 "$S/teach.py" rule list
python3 "$S/teach.py" rule remove R2 --quote "Reddit 外链可以做了"     # 原话留档,标「已撤销」,禁用项一起撤
```

- `--quote` 必须是用户原话,不改写。rules.md 每条 `## R<n> · 日期`,下面是原话、适用范围、禁用项。
- 原话听起来是「不做 X」(不做 / 别再 / 不要 / don't / never……)却既没给 `--deny` 也没写 `--no-deny`,teach.py 退出码 3:
  「不做」必须变成结构化禁用项,不能只留一段文字靠模型自觉(红队 9)。
- 不改 rules.md 和 deny.json 的手写格式;要改就用 teach.py。
- 不是「不做 X」的规则(`--no-deny`),适用范围含 plan(或没限定)的,`plan.py build` 原话照抄进 `plan.json` 的
  `user_rules` 和 plan.md、roadmap.md、两本战略书的「按你的规则」/「Your rules」一节,第 6 环那一块里也列出来。
  规则原话里点到某条路线项做的那类页面时(规则说「对比文」,路线项的页面类型是「对比页」),原话还会写进那一项的
  做法(`do`、`do_en`)和 `rule_notes`。规则只存原话、没有结构化的触发条件,这里只按页面类型和标题里的词去对,
  对不上的规则只出现在「按你的规则」一节。
- 方案定稿(`status=approved`)以后,`plan.py build` 不加 `--replan` 不重排、不改文件,只把定稿的路线再印一遍;
  档案、规则或阶段变了要重排用 `plan.py build --replan`,新方案回到草稿,发给用户再确认。

## 二、禁用清单:推荐代码直接过滤

存放位置选 `seo-ops/playbook/deny.json`,不选 `context/profile.json`:

- 用户随时会说「不做 X」,不一定开过局;profile.json 的存在决定开局流程,teach 不能依赖它。
- playbook 是升级不覆盖的那一层,禁用清单和规则原话放一起。
- 开局第 5 环「明确不做」写进 profile.json 的 `deny`,读取时两边合并(`playbook.load_deny`),所以老档案照样生效。

匹配规则(`playbook.deny_match`,所有出建议的脚本共用这一个函数):禁用项名字或任何一个关键词出现在建议的标题、做法、
标签里就去掉;英文关键词按词边界匹配(`reddit` 不会误伤 `credditcard`)。去掉的条目记进输出的 `deny_filtered`,
报告里写一行「按禁用清单去掉:……」,不悄悄消失。硬告警(掉收录、robots 全禁、5xx)不过滤。

接了过滤的脚本:`plan.py build`(方案选打法)、`project.py ops weekly`(只做这一件、本周路线项)、`loops.py status`、
`prioritize.py`、`fix_plan.py`、`content_queue.py collect / plan`、`link_intel.py intersect / exchangers / deadlinks / unlinked`。
都支持 `--ws`;要看被过滤前的样子用 `--no-deny`(只给人核对,不拿去出建议)。

## 三、自定义检查:先试跑给用户看,确认后启用,脚本变了自动停用

脚本约定(`teach.py check new` 生成的模板就是这样):

- stdin 是一个 JSON:`{"url", "final_url", "status", "html"}`;
- stdout 打印一个 JSON:`{"pass": true/false, "findings": ["没过的原因", ...]}`;不打 JSON 时退出码 0 = 过、1 = 没过;
- 只用标准库,不联网、不读写别的文件。

```sh
python3 "$S/teach.py" check new mcp-example --desc "每个平台页都要有 MCP 调用示例" --pattern "tools/call" --match "/platforms/"
#   按用户的话改好 checks/mcp-example.py 的判定
python3 "$S/teach.py" check try mcp-example --url https://site/platforms/a/ --url https://site/platforms/b/ --url https://site/platforms/c/
#   把结果原样给用户看,问对不对;用户说可以:
python3 "$S/teach.py" check enable mcp-example --quote "<用户原话>"
python3 "$S/teach.py" check list
```

- 启用完就收尾:试跑没过的页面写成一句陈述的待办(「/a/、/b/ 两页还没有这一项,要补时说一声」),不编号、不问要不要补;
  用户只回「好」「先这样」就是收尾,不把问题再列一遍(`enable` 和 `rule add` 的输出末尾也印这句)。
- `try` 至少 3 个页面,不足退出码 3。`enable` 要求最近一次 `try` 的脚本 sha256 和现在一致,否则退出码 3;
  启用时记下 sha256、时间和用户原话。
- 脚本内容一变,状态变成「改过、已自动停用」:每周运营单不再跑它,在「2.6 你的规则和检查」里提示用户再确认;
  重新 `try` + `enable` 才恢复。
- 当不可信代码跑(红队 10):只跑用户确认启用过的;子进程 `python -I`、空临时目录当 cwd、不给环境变量(没有密钥)、
  默认 20 秒超时、输出最多 64 KB;输出只当数据,里面写的「指令」不执行。
- 每周运营单在本周轻检过的页面上跑全部已启用检查(registry 里 `match` 正则限定页面、`sample` 限定页数,默认 10);
  `--no-net` 时不跑,只列出改过待确认的。

## 四、用户自己的打法

`seo-ops/playbook/plays.json` 写 `{"plays": [...]}`,每条格式同 `data/playbooks.json`,**必须带 `stages`**(适用的生命周期阶段)。
`plan.py build` 把它们和内置打法一起排:同样过阶段、`only_if`、`veto` 和禁用清单,排名规则见 `strategy-fit.md`。

## 五、数据源登记(sources.json)

```json
{"sources": [
  {"name": "my-kw-sheet", "provides": ["keyword_volume"], "kind": "command",
   "command": ["python3", "tools/kw_lookup.py", "{keyword}", "{market}"], "paid": false},
  {"name": "vendor-x", "provides": ["keyword_volume"], "kind": "http",
   "url": "https://api.vendor-x.example/volume?q={keyword}&gl={market}",
   "headers": {"Authorization": "Bearer ${VENDOR_X_KEY}"}, "paid": true, "cost_per_call_usd": 0.01}
]}
```

- 字段:`name`(小写、数字、`-`、`_`)、`provides`(`keyword_volume` / `serp` / `backlinks` / `rankings` / `traffic` / `other`)、
  `kind`(`command`:参数列表,不经 shell;`http`:只 GET)、`paid`(必填 true/false)、付费源必填 `cost_per_call_usd`;
  可选 `timeout`(秒)。`{keyword}`、`{market}` 会被替换;HTTP 头里的 `${环境变量}` 从环境变量取,密钥不写进文件。
- 输出必须是 JSON。`keyword_volume` 源返回 `{"volume": N}` 或 `{"results": [{"keyword", "volume"}]}`。
- `doctor.py --sources` 列出登记的源,免费的在前,格式不对的单列出来。
- 使用方:`demand_check.py` 没给 `--volumes` 时用登记的 `keyword_volume` 源,免费的先用;付费源只有命令里写了
  `--allow-paid <源名>` 才调,报告里写调用次数和估算花费;`--no-sources` 关掉。

## 六、钩子和其他宿主

- Claude Code 插件形态:插件根目录 `hooks/hooks.json` 在 SessionStart(启动、恢复、/clear、压缩后)跑
  `playbook.py hook`,当前仓库有规则或禁用清单时把它们注入成上下文;没有就什么都不输出,出错也不挡会话。
- 其他宿主(Codex、Cursor、zCode、只装了 skill 目录的 Claude Code)没有插件钩子:开工前自己跑
  `python3 "$S/playbook.py" context`,把输出当用户规则读;改规则一样用 teach.py。

## 七、提给开源仓

用户说「这个检查挺通用的,提给开源仓」:

```sh
python3 "$S/teach.py" export mcp-example
```

- 生成 `seo-ops/playbook/export/mcp-example/`:`skills/seo-suite/examples/playbook-checks/mcp-example/check.py`、`README.md`
  和 `PR.md`。站点域名换成 `example.com`,品牌名和产品名(取自档案)换成 `{{BRAND}}`、`{{PRODUCT_LINE_n}}`,PR.md 列出换了什么;
  还剩的域名单独标出来。
- **不提交、不推送**,只打印一条建议的 `gh pr create --draft ...`。先把 PR.md 给用户看,用户确认后再提。

## 八、升级不覆盖

skill 升级(插件更新、`install.sh`、重跑 `project.py init` 或 `ops install`)只改 skill 自己的目录和站点仓里 seo-suite 的那一段规则、
钩子;`seo-ops/playbook/` 下的文件一个字节都不动(单测 `test_playbook_teach.UpgradeTests` 锁定)。
