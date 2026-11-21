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
   - {"action":"end"} → 这个 run 结束(最后一回合没有编号问题、也不是以提问工具结束;或到了 20 回合)
   - {"action":"error"} → 看原因(同一回合已回过 / 转录为空),不要硬发
```

`next` 做的事(和 scenarios.json 的 driver 段一致,主会话不用自己判):

- **判环号**:最后一条 assistant 文本里找「第 N 环 / Ring N」;提到好几个不同环号时按 R32:档案顶层的 `ring` / `current_ring` 在其中就取它,否则取第一个问题行之前出现次数最多的那个(一样多取最近的)。文本里没有环号就读 `seo-ops/context/profile.json` 顶层的 `ring` / `current_ring`。都没有 → 发 `fallback_unknown_ring`,驱动日志 `ring: null`(这一次停下不计入任何环)。
- **取回话**:`simulated_user[环号]` 按顺序取下一条,取完了发 `fallback`。
- **写驱动日志**:一行 `{"turn","ring","ring_from","user_text","source","at","profile_snapshot"}`;`profile_snapshot` 是这次停下时 `profile.json` 的副本(放在 `RUN/snapshots/`),判「第 1 环确认后的档案」用。
- SendMessage 的消息必须是 `user_text` 原文:判分器在下一回合的用户消息里按「去空白后包含」核对,对不上的那次停下不算数。

## 4. 判分和汇总

```bash
python3 $G onboard-prelaunch --ws WS --transcript <转录> --driver-log RUN/driver.jsonl \
        --site http://127.0.0.1:PORT --arm skill --out RESULTS/onboard-prelaunch-skill-1.json
# everyinfra:加 --scenarios <PRIVATE>/scenarios-everyinfra.json --answers-dir <PRIVATE>/answers,RESULTS 放私有目录
python3 $G report RESULTS
```

- 每条断言给 `pass`、`kind`(outcome / process)和证据(转录行号、文件路径、命中的词)。读法(criteria_defs 有歧义处怎么判)写在 `grade.py` 文件头 R1–R31。
- `report` 按产品 × arm 汇总:`outcome_pass_pct`、`outcome_gap_pp`(skill − baseline、v043 − baseline、skill − v043,单位百分点)只算 outcome 类;process 类在 `process` 下单列,不进差距(红队致命 2)。`maturity_exact` 是例 9 的 5 维完全一致数(null 只和「未知」对得上)。
- void 的 run 列在 `void`,不进任何汇总。
- 判分器改了要先过校准:`python3 -m unittest tools/evals/onboarding/test_grade.py`(发版门 `tools/evals/fast_checks.py` 也跑它)。

## 5. 省额度

- 被测子代理一律 `model: sonnet`;判分、驱动、汇总全是脚本,不调模型。
- 每个 run 的子代理只在这个 run 里续跑;跑完不再叫醒。
- 场景多时分批起(同时 3–4 个 run),每个 run 自己的端口和目录;测试站和长命令放后台。
- 先每个场景每组各跑 1 次看判分器证据是否合理,再补到每组 ≥2 次(规则评测要求每条例子跑两次以上)。
