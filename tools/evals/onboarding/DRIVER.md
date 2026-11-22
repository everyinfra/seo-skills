# 开局多轮评测:驱动说明(给主会话照着跑)

被测会话是主会话用 Agent 工具起的子代理;每次它停下来问,主会话用 `grade.py next` 判环号、取模拟用户回话、写驱动日志,再用 SendMessage 把回话原样发回去续跑。跑完只跑 `grade.py`,不调模型判分。

场景和答案表是第 0 批出题人写定、记了 hash 的,**一个字不改**:

| 场景 | 场景文件 | 答案表目录 |
|---|---|---|
| onboard-idea / prelaunch / launched / mature / change | `tools/evals/onboarding/scenarios.json` | `tools/evals/onboarding/answers/` |
| onboard-everyinfra / -correct / -unknown / -skip | 私有目录 `<PRIVATE>/scenarios-everyinfra.json`(不在本仓,见 HASHES.txt 首行说明) | 同目录 `answers/` |

开跑前先核 hash:`cd tools && grep -v '^#' evals/onboarding/HASHES.txt | shasum -a 256 -c`;私有目录的 `answers/everyinfra.json` 对同目录 `HASHES-出题时.txt`。everyinfra 的结果文件含竞品名,只放私有目录,不进本仓。

## 1. 每个场景搭工作区、起测试站

下面 `RUN` 是这一次 run 的目录(建议 `~/Downloads/rq237-eval/<场景>-<arm>-<序号>/`),`PORT` 每个 run 一个(8810 起)。`L=tools/testsites/lifecycle_sites.py`。

| 场景 | 搭法(照 scenarios.json 的 setup) | 工作区 WS | `--site` |
|---|---|---|---|
| onboard-idea | `python3 $L build --product idea --out RUN/site`;`cp RUN/site/brief.md RUN/site/repo/` | `RUN/site/repo` | 不给 |
| onboard-prelaunch | `python3 $L build --product prelaunch --out RUN/site --base http://127.0.0.1:PORT`;后台 `python3 $L serve --dir RUN/site/site --port PORT` | `RUN/site/repo` | `http://127.0.0.1:PORT` |
| onboard-launched | build 同上(`--product launched`)、serve `RUN/site/site`;新建 `RUN/ws/`,写 `README.md`「Northfold Coffee 官网,站点在 http://127.0.0.1:PORT」,`cp -R RUN/site/gsc RUN/ws/data` | `RUN/ws` | 同上 |
| onboard-mature | 同 launched(`--product mature`,README 写「Trailmark Guides,站点在 …」) | `RUN/ws` | 同上 |
| onboard-change | `python3 $L build --product change --state before --out RUN/site --base http://127.0.0.1:PORT`;serve `--dir RUN/site/repo` | `RUN/site/repo` | 同上 |
| onboard-everyinfra* | 空目录 `RUN/ws`(没有 seo-ops/,不放任何仓库文件);站点是线上 | `RUN/ws` | `https://everyinfra.com` |

- 测试站用 `run_in_background` 起,记下 PID,跑完按 PID 停(不用 `pkill -f`)。
- 改版场景的例 10(site-move 前后对比)另跑,不在开局评测里。
- 工作区开跑前 `git init` 一下(idea / prelaunch / change 的 repo 已是目录,没有 .git 时补 `git init -q && git add -A && git commit -qm init`),被测会话要开分支时不会出错。

## 2. 三个 arm 的提示词

一律用脚本生成,不手写,保证三组只差「装没装、装哪版」:

```bash
G=tools/evals/onboarding/grade.py
python3 $G prompt onboard-prelaunch --arm skill    --ws WS --base http://127.0.0.1:PORT --skill-dir <本仓>/skills/seo-suite
python3 $G prompt onboard-prelaunch --arm baseline --ws WS --base http://127.0.0.1:PORT
python3 $G prompt onboard-prelaunch --arm v043     --ws WS --base http://127.0.0.1:PORT --skill-dir V043/skills/seo-suite
```

- **skill**:给当前分支的 `skills/seo-suite` 路径,让它先读 SKILL.md。
- **baseline**:不给 skill,明确不许用 Skill 工具、不许读任何 seo-suite 文件。判分时转录里出现 Skill 调用或 `skills/seo-suite` 路径,这个 run 记 void、不进汇总。
- **v043**:先把 0.43.0 整个 skill 导出到临时目录(脚本也要):
  `V043=$(mktemp -d) && git -C <本仓> archive v0.43.0 skills/seo-suite | tar -x -C "$V043"`
  (只要看 SKILL.md 时等价于 `git show v0.43.0:skills/seo-suite/SKILL.md`)。读了当前版本路径的 run 记 void。
- 三组共用同一段「评测产出位置」:档案写 `seo-ops/context/profile.json`(列了键名和阶段编号)、方案写 `seo-ops/plan/`。这是评测契约,三组拿到的完全一样;没有它,不装 skill 的组连档案放哪都不知道,「装 vs 不装」量到的就是文件格式,不是内容。
- 没有提问工具:提示词要求把问题按编号列出后结束回合(判分器按编号问题行认「停下」)。

## 3. 多轮驱动

```
1. Agent(subagent_type=general-purpose, model=sonnet, run_in_background=true, prompt=<上一步的提示词>)
   记下 agentId;转录在 ~/.claude/projects/<本会话目录>/subagents/agent-<agentId>.jsonl
2. 等它这一回合结束的通知(不要在它还在跑时调 next)
3. python3 $G next <场景> --ws WS --transcript <转录> --driver-log RUN/driver.jsonl [--scenarios <PRIVATE>/scenarios-everyinfra.json]
   - {"action":"reply","ring":N,"user_text":…} → SendMessage(to=agentId, message=user_text 原文,一个字不加)→ 回到 2
   - {"action":"end"} → 这个 run 结束(最后一回合没有编号问题、也不是以提问工具结束,而且文本里也没有问句;或到了 20 回合)
   - 回合以文本结束、有问句(含 ? / ？)却没按编号列出:`next` 照常按环号给回话(驱动日志带 `"unnumbered": true`),
     这一回合**不算停下**(R3、R4 不变),只是会话不在这里断掉;每段最多 3 次,连着两回合都这样就结束(R64)
   - {"action":"error"} → 看原因(同一回合已回过 / 转录为空),不要硬发
```

`next` 做的事(和 scenarios.json 的 driver 段一致,主会话不用自己判):

- **判环号**:最后一条 assistant 文本里找「第 N 环 / Ring N」;提到好几个不同环号时按 R32:档案顶层的 `ring` / `current_ring` 在其中就取它,否则取第一个问题行之前出现次数最多的那个(一样多取最近的)。文本里没有环号就读 `seo-ops/context/profile.json` 顶层的 `ring` / `current_ring`。都没有 → 发 `fallback_unknown_ring`,驱动日志 `ring: null`(这一次停下不计入任何环)。
- **取回话**:`simulated_user[环号]` 按顺序取下一条,取完了发 `fallback`。
- **问句没编号**:同上取回话,只在有 `simulated_user` 的段做(例 7 这类小任务段不回)。需求卡第 2 节例 1 和第 3 节「宿主适配」写的是
  「没有提问工具的宿主用编号问题后结束回合」,所以编号仍是停下的条件;但会话因此提前结束会让方案类结果断言一起挂,把流程分扣进结果分,
  和卡第 7 节红队致命 2「流程类单独判、不进差距」冲突,所以驱动照常回话(出题人 11-22 裁定)。
- **写驱动日志**:一行 `{"turn","ring","ring_from","user_text","source","at","profile_snapshot"}`;`profile_snapshot` 是这次停下时 `profile.json` 的副本(放在 `RUN/snapshots/`),判「第 1 环确认后的档案」用。
- SendMessage 的消息必须是 `user_text` 原文:判分器在下一回合的用户消息里按「去空白后包含」核对,对不上的那次停下不算数。

## 4. 判分和汇总

```bash
python3 $G onboard-prelaunch --ws WS --transcript <转录> --driver-log RUN/driver.jsonl \
        --site http://127.0.0.1:PORT --arm skill --out RESULTS/onboard-prelaunch-skill-1.json
# everyinfra:加 --scenarios <PRIVATE>/scenarios-everyinfra.json --answers-dir <PRIVATE>/answers,RESULTS 放私有目录
python3 $G report RESULTS
```

- 每条断言给 `pass`、`kind`(outcome / process)和证据(转录行号、文件路径、命中的词)。读法(criteria_defs 有歧义处怎么判)写在 `grade.py` 文件头 R1–R32、R63–R84。
- R65:认 onboard.py / plan.py 等脚本调用前,把同一条 Bash 命令里前面赋过值的 `$NAME` / `${NAME}`(整词或路径前缀)展开,跨调用不展开,展开后其余判定规则不变。R26 审计脚本、R42 执行、ops weekly 同一口径;纯赋值段和命令前缀赋值(`O=… python3 $O …`)里写的脚本不算调用。
- R66–R76(出题人 11-22 裁定试跑 3 的 12 个疑问,全文在 `grade.py` 文件头):包装命令 `check try <名>` 输出里有平台页判定就算执行(停用断言同口径,运营单内部跑了也算);启用按简单命令判、不认 `seo-ops/` 里的 ops;判定词英文 / 符号优先;启用确认看「停下问启用 + 回话是确认」;Reddit 否定看前 30 字、同分句后文和标签冒号后;价格表认紧邻上方的价格标题加货币金额,`vs` 独立成词、「月度对比」不算对比;开局脚本输出里原样带出 product-marketing.md 内容算读过;脚本写到默认位置的基线文件按 mtime 窗口归给那次调用;脚本输出里转印本地文件的行和报错行不算请求。R74、R75 要用到工作区文件的 mtime 和转录时间戳:**判分前不要复制或改动工作区**(要复制用 `cp -p` / `shutil.copy2`)。R76(疑问 12):档案里产品线用中文译名记算对,答案表别名组补了站点原词的标准译法(改的是 `answers/*.json`,hash 见 `HASHES.txt`)。
- R77–R80(出题人 11-22 裁定试跑 3b 例 5 的 8 个疑问,全文在 `grade.py` 文件头):threshold 的「连续 4 周」按 note 的算法,数据起始日前的日子按 0 算、下界过 1000 就算超过;gsc_series.py 的排名和点击改成和开局导出一致,spike 不改写开局导出已有的日子,threshold 加一条「新旧导出对不上」的回话(题目 hash 换了,见 `HASHES-第5批出题.txt`);回话外面那层「The coordinator sent a message…」是宿主加的,提示词照实说明,首条消息被改过记 `driver_deviations`;第一屏的阶段名要和「阶段 / stage」同一行;「提示进入增长期」另认「换成 / 切换到增长期」一类说法,否定和条件句里的不算。疑问 1、2、5、6、7 维持原读法。
- R81–R84(出题人第三轮裁定,11-22,第 5 批第 2 轮检查跑的疑问 A–D,全文在 `grade.py` 文件头):agent 文本里用「通过 / 没过」贴的试跑结果也算给用户看了结果(只用于「结果出现」,trial_matches 的判定词不变),确认停点于是落在试跑之后、启用之前;已写明排除 Reddit 的条目里解释来由的那处(分句里没有发帖、可以、建议一类动作词)不记违例;「brand vs non-brand / 品牌词 vs 非品牌词」是测量口径,不算对比条目;从命令取 `--quote` 等参数时双引号里的 `\$`、`` \` `` 按 bash 规则去掉反斜杠。题目改了一处:ex6 teach 段启用话题 `max_uses` 2 → 1(被测启用后报告里的「已启用」又触发一次「结果对,启用吧。」),hash 见 `HASHES-第5批出题.txt`。
- `report` 按产品 × arm 汇总:`outcome_pass_pct`、`outcome_gap_pp`(skill − baseline、v043 − baseline、skill − v043,单位百分点)只算 outcome 类;process 类在 `process` 下单列,不进差距(红队致命 2)。`maturity_exact` 是例 9 的 5 维完全一致数(null 只和「未知」对得上)。
- void 的 run 列在 `void`,不进任何汇总。
- 判分器改了要先过校准:`python3 -m unittest tools/evals/onboarding/test_grade.py`(发版门 `tools/evals/fast_checks.py` 也跑它)。

## 5. 省额度

- 被测子代理一律 `model: sonnet`;判分、驱动、汇总全是脚本,不调模型。
- 每个 run 的子代理只在这个 run 里续跑;跑完不再叫醒。
- 场景多时分批起(同时 3–4 个 run),每个 run 自己的端口和目录;测试站和长命令放后台。
- 先每个场景每组各跑 1 次看判分器证据是否合理,再补到每组 ≥2 次(规则评测要求每条例子跑两次以上)。

## 6. 第 5 批:真实站、扩展场景、盲比、宿主检查

第 5 批的题是另一位出题人写的,**一个字不改**,开跑前核 hash:公开的 `scenarios_ext.json`、`rubric_example3.json`、`hosts_static.json` 对本目录 `HASHES-第5批出题.txt`(`cd tools/evals/onboarding && grep -v '^#' HASHES-第5批出题.txt | awk '{print $1"  "$2}' | shasum -a 256 -c`);私有的 `<PRIVATE>/scenarios-real.json` 和它的答案表对私有目录里的 `HASHES-第5批出题.txt`。真实站的场景 id、产品名和结果文件都只放私有目录,不进本仓。

2026-11-22 出题人裁定试跑 3 后改了 `scenarios_ext.json` 两处(ex6 teach 段的话题回话、ex7-hreflang-broken 第 3 组正则),新旧 hash 和原因记在 `HASHES-第5批出题.txt` 末行;已经跑完的 run 判分时 run.json 里的 `scenarios_file` 指到哪份就用哪份,要按新题判,在内存里把 `R["scenarios_file"]` 换成本检出的文件再调 `grade_ext.grade_ext(R, …)` / `grade.grade(…)`,不改 run 目录。

2026-11-22 出题人裁定试跑 3b 后又改了 `scenarios_ext.json`(ex5 的 gsc_series.py 配方、threshold 一条话题回话、两个 note),新旧 hash 记在同一文件末行;已经跑完的 ex5 run 的 data/ 是旧配方生成的,重判时断言照旧配方的数据判(这些断言本身不随配方变),结果里标明。

第 5 批一律走 run 目录:`setup` 建站和工作区、写 `RUN/run.json`,之后的子命令只认 `--run RUN`(布局见 `grade_ext.py` 文件头)。读法在 `grade.py` 文件头 R33–R65。出题人更正过的回话记在场景的 `superseded_replies` 里:收到旧回话的 run,列出的断言记 voided、不进汇总(R63)。

### 6.1 真实站 3 个(场景 id 见 `<PRIVATE>/scenarios-real.json`,下面写成 `REAL_ID`)

```bash
P=<PRIVATE>; G=tools/evals/onboarding/grade.py
python3 $G setup REAL_ID --arm skill --run RUN --scenarios $P/scenarios-real.json --skill-dir <本仓>/skills/seo-suite
python3 $G mutate RUN main                     # 打印首条消息(= grade.py prompt 的同一份提示词),工作区做初始提交
# 起子代理 → 每回合结束:
python3 $G next REAL_ID --run RUN --session main --transcript <转录>
# 结束后:
python3 $G REAL_ID --run RUN --answers-dir $P/answers --out <PRIVATE>/results/REAL_ID-skill-1.json
```

- 真实站没有测试站、不起 serve;站点就是线上地址,主机名严格按 setup 原文(带不带 www 算两个主机,页面类型只数那一个)。
- 真实站不给 GSC:判分器把任何 GSC 数字都当编造(no_fabricated_metrics)。

### 6.2 扩展场景(例 5 / 6 / 7 / 11)

**先跑 base,打 W0**(有 `base` 的变体:ex5-*、ex7-title-warm)。同一轮评测里每个 base 每个 arm 只跑一次:

```bash
python3 $G setup onboard-launched --arm skill --run BASE_RUN --port 8810 --skill-dir <本仓>/skills/seo-suite
python3 $G mutate BASE_RUN main   # → 按第 3 节完整跑到第 6 环结束
python3 $G w0 BASE_RUN --out W0-launched-skill.tgz
```

**每个变体**:

```bash
python3 $G setup ex5-new-line --arm skill --run RUN --w0 W0-launched-skill.tgz [--port 8811 --rebase-port] --skill-dir …
# 有 serve 的后台起站(setup 输出的 serve 命令),记 PID
# 对 run.json 的 session_order 里每一段,按顺序:
python3 $G mutate RUN <段>        # 必调,mutate 为空也调:执行段间动作、git 提交、拍开始快照、打印这一段的首条消息
#   → 用打印的首条消息起一个新的被测子代理(每段一个新子代理,不续上一段的)
#   → 每回合结束:python3 $G next <场景> --run RUN --session <段> --transcript <这一段的转录>
#      reply → SendMessage 原文;end → 这一段结束(next 自己拍结束快照),进下一段的 mutate
python3 $G <场景> --run RUN --out RESULTS/<场景>-skill-1.json
```

- 同一个 W0 的变体默认沿用 W0 的端口,只能串行;要并行就各给 `--port` 并带 `--rebase-port`。
- **首条消息照 `mutate` 打印的原文发,一个字不加**(R78)。不要在末尾补「Harness note: … There is no coordinator …」之类的说明:回话经 SendMessage 续跑,宿主一定会包一层「The coordinator sent a message while you were working: … Address this before completing your current task.」,提示词里已经照实说明这层包装;驱动另加的说明和包装矛盾,被测会把回话当成第三方消息。判分器逐段拿转录首条用户消息和 `RUN/sessions/<段>/prompt.txt` 比,不一致记进结果的 `driver_deviations`,`report` 单列。
- 回话照旧用 SendMessage 发 `user_text` 原文;包装去不掉(这是宿主续跑子代理时加的固定格式;出题人能看到的工具里,续跑子代理只有 SendMessage 一条路,Agent 工具没有续跑参数),判分器 R1 认它。
- **ex5-threshold、ex5-spike-decoy 的 T 不早于 2026-11-15**(R77):数据从 10-19 起,T 再早 threshold 最早那个周检查点的窗口下界就不到 1000,「连续 4 周超过」不成立。
- `next` 的回话顺序:停下时先按 `simulated_user_by_topic` 回,没命中再发下一条 `user_turns`,再按环号取 `simulated_user`,最后 `fallback`;没停下时发下一条 `user_turns`,发完就结束这一段。
- **例 6**:setup 加 `--skill-src <旧版 skill 目录>`(装进 `RUN/skill/seo-suite`,被测会话用这份);第 4 段 `t1_compare_brief` 的 mutate 带 `--install-from <被测版本 skill 目录>`(reinstall_skill 只删 run 本地那份再装)。baseline 组没有 skill,reinstall 跳过;它拿不到 playbook 的路径提示,这部分差距里有一部分量的是「知不知道文件放哪」。
- **例 11**:判分要带 `--ref`,指向同 arm、同一轮 `onboard-launched` 的判分结果(第 1 环问题数的基线);不给判不过。
- **例 7 的 title 场景**:判分按 `git diff`,基准是 mutate 那次提交;被测会话自己 commit 不影响(比的是开始快照和结束快照)。
- 段跑砸了要重来:换一个新的 RUN 从 setup 重跑整个场景,不在旧 run 上补段。

### 6.3 例 3 盲比

同一产品、同一轮:新版(skill 组)和 0.43.0(v043 组)各跑一次开局到第 6 环结束(用 6.1 / 第 3 节的 run)。

```bash
python3 $G blind prepare --product launched --round R5-1 --new-run RUN_NEW --old-run RUN_OLD --out BLIND/launched \
        --new-skill-dir <本仓>/skills/seo-suite --old-skill-dir $V043/skills/seo-suite
```

1. 另起一个**独立**评判子代理(没看过任何被测转录),只给它 `BLIND/launched/judge_prompt.md` 和 `evidence_A.txt`、`evidence_B.txt`,不给 `record.json`;它输出 JSON 存成 `BLIND/launched/judge.json`。
2. 反事实:`BLIND/launched/cf/prompts.json` 里有两段首条消息。新版在 `cf/new_ws` 里新开会话跑一次,旧版在 `cf/old_ws` 里新开会话跑一次(停下来问时按 `if_it_asks` 回)。
3. 汇总:
   ```bash
   python3 $G blind tally --out BLIND/launched --judge BLIND/launched/judge.json \
           --cf-new-ws BLIND/launched/cf/new_ws --cf-old-ws BLIND/launched/cf/old_ws --cf-old-transcript <旧版反事实转录> \
           --result RESULTS/blind-launched.json
   ```
   归一化后肉眼仍能看出哪份是新版时加 `--blind-broken`(只作参考,不计入通过)。证据包是工具结果和文件原文去版本痕迹,结构上仍可能露出版本(新版有 seo-ops/ 文件、旧版没有),评判结论要连这一点一起看。

### 6.4 宿主静态检查(Codex、Cursor、Gemini CLI、VS Code Copilot)

```bash
python3 $G hosts --skill-dir <被测 skill 目录> --plugin-root <插件或仓库根> --label <版本> --out RESULTS/hosts-<版本>.json
```

不调模型、不联网;must 不过该宿主 fail,should 不过记 warn,可选项没有对应文件记 n/a。

### 6.5 汇总

`python3 $G report RESULTS`(递归读子目录):`products` 是第 0 批开局,`real` 是真实站,`ext` 按场景列;`outcome` 和 `outcome+process` 进差距,process 单列;`blind_example3` 是盲比(通过数 / 产品数,blind_broken 的单列),`hosts_static` 是宿主检查。

判分器改了先过校准:`python3 -m unittest tools/evals/onboarding/test_grade.py`(第 5 批的 31 条新断言各有标准答案、裸跑、反例三种 fixture,见 `fixtures/build_ext.py`、`fixtures/scenarios_real_calib.json`)。
