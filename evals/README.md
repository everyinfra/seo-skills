# seo-suite 插件评测(`claude plugin eval`)

格式按 Claude Code 官方文档 [Test plugins with evals](https://code.claude.com/docs/en/plugin-evals):每个用例一个目录,
`prompt.md`(frontmatter 是运行参数,正文是用户的话)+ `graders/*.md`(一个文件一个判分器),要预置工作区的另带
`case.yaml` 和 `scaffold.sh`。

| 用例 | 入口 | 判什么(期望值来自需求卡 RQ-237) |
|---|---|---|
| start-first-screen | start | 例 1:先跑 onboard.py start、用提问工具停下来问,第一屏之前不出方案(不跑 plan.py) |
| start-small-task | start | 例 7:小任务直接做,不弹 6 环(不跑 onboard.py) |
| teach-deny-rule | teach | 例 6 第 2 条:「别再建议 Reddit 外链」写进 rules.md(带原话)和结构化禁用清单 deny.json |
| teach-check-confirm-first | teach | 例 6 第 3 条:生成检查脚本;用户没看过试跑结果就不启用 |
| weekly-respects-deny | weekly | 例 6:禁了 Reddit 以后,运营单的「只做这一件」和本周路线项里不再出现 Reddit |

跑法(本机要有 Claude Code ≥ v2.1.269;脚本要 Bash,预置工作区要 `--scaffold`):

```sh
claude plugin eval . --scaffold --allow-tools Bash,Write,Edit --runs 3
```

发版门(`tools/release_check.py`)只做这份套件的静态校验(`tools/evals/plugin_suite_check.py`:结构、字段、引用的文件都在),
不调模型;真跑由维护者在有 Claude Code 的机器上手动跑。`results/` 不进 git。
