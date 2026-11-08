# 长期循环与改版保护(第二次打开以后)

开局 6 环做完以后,这套 Skill 不再从头问。每次打开先看一屏现状,再由循环决定要不要打扰用户。大多数轮次的结论是「查了,没事」:只记账,不提问。

相关:每周运营单见 [ops-agenda](../monitoring/ops-agenda.md);阶段怎么判见 [lifecycle-stages](../overview/lifecycle-stages.md);方案怎么出见 `plan.py`。

## 1. 第二次打开:一屏现状

```bash
python3 scripts/loops.py status --ws seo-ops
```

一屏写清:档案上次核对是哪天、现在是哪个阶段、方案进行到第几周、本周路线项(来自定稿的 `plan/roadmap.md`)、每个循环的状态(`quiet` 没事 / `ask` 要问 / `waiting` 问过、等回复)。

## 2. 六个循环

循环的定义在 `data/loops.json`,统一写七件事:什么时候查(trigger)、什么情况才打扰(act_if)、怎么自检(self_check)、什么时候不再问(stop_if)、怎么去重(dedup)、结果写哪(output)、回开局哪一环(ring)。

| 循环 | 什么时候查 | 什么情况才问 | 最多问 |
|---|---|---|---|
| weekly-ops 每周运营单 | 每 7 天 | 有硬告警、本周路线项或变差的问题 | 0(只出运营单) |
| profile-review 档案核对 | 档案上次核对满 30 天 | 重新读站后有事实和档案不一样;或满 30 天没核 | 3 |
| quarterly-review 季度复盘 | 方案定稿满 90 天 | 用这一季真实数据重跑 `plan.py`,和定稿方案比 | 2 |
| product-change 产品变了 | 重新读站(`--scan` / `--rescan`) | 新产品线、定价变了、sitemap 出现新页面类型;**只问变了的部分** | 3 |
| stage-threshold 到了下一阶段门槛 | 每次记指标 | 最近 4 次指标(跨度 ≥ 21 天)都判成同一个新阶段;一次冲高不算 | 1 |
| site-move 改版保护 | 档案里记了改版类事件 | 见第 4 节 | 1 |

```bash
python3 scripts/loops.py run --ws seo-ops [--scan new-scan.json | --rescan]   # 退出码 1 = 有问题要问
python3 scripts/loops.py resolve --ws seo-ops product-change --quote "<用户原话>" --set product.lines=发票,报销,差旅
```

规则:

- 问过的同一件事按指纹记在 `seo-ops/ledger/loops.jsonl`,`ask_again_days` 天内不再问;用户没回复时状态是 `waiting`,不重复问。
- 一轮所有循环加起来最多问 3 个问题。
- 用户的回答用 `resolve` 写回档案,带原话;改了产品线或阶段会提示重跑 `plan.py`。
- 用户在 `seo-ops/playbook/loops.json` 写 `{"loops": [...]}` 可以加自己的循环或改阈值,同 id 覆盖内置的。

## 3. 运营单里的优先级

方案定稿以后,每周运营单的「只做这一件」按这个顺序选:

1. 硬告警(首页打不开、整站 noindex、robots 全封这类);
2. 本周路线项(定稿方案里排在这一周的事);
3. 原来按 GSC 和体检挑的那一件。被路线项让位时写成「数据里另一个机会(排在路线项之后)」照样列出来,不丢。

运营单第 2.5 节「方案与循环」写本周路线项和各循环的状态。`ops weekly` 拿到 GSC 数据时会顺手把近 28 天点击、展示追加到 `context/metrics_history.jsonl`,阶段门槛循环用它判断。

## 4. 改版保护(换域名、改 URL、换建站系统、合并站点)

Google 对改 URL 的站点迁移的要求:旧 URL 一对一 301 到新 URL,新页 canonical、hreflang、sitemap、站内链接都换成新 URL,迁移后持续看抓取和收录([Site moves with URL changes](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes))。`site_move.py` 把这些要求变成改动前后的逐条对比。

**改动前**存基线(sitemap 加站内链接能到的页面,每页记状态码、title、H1、canonical、hreflang、结构化数据类型、noindex、站内链接;给了 GSC 网页导出就把每页近 28 天点击也记上):

```bash
python3 scripts/site_move.py baseline --site https://example.com --gsc-pages pages.csv \
        --out seo-ops/baselines/2026-11-20.json
```

**改动后**(预发或正式站都行)对比。映射表可以是 CSV(old,new),也可以直接用迁移文档里的 Markdown 表格:

```bash
python3 scripts/site_move.py compare --baseline seo-ops/baselines/2026-11-20.json \
        --new-site https://example.com --map MIGRATION.md --md
# 换域名时加 --old-origin https://old.example.com:旧 URL 去旧域名上请求
```

查的问题(block 级退出码 1):

| 问题 | 级别 | 怎么判 |
|---|---|---|
| 漏 301 | block | 旧 URL 在新站上直接 404 / 410 |
| 跳转终点不是 200 | block | 跳到的地址打不开;只差大小写时会点明 |
| 跳到首页 | block | 深层旧 URL 被跳到 `/`(Google 会当软 404) |
| 跳到映射表以外 | block | 终点和映射表不一致 |
| 旧地址没跳转 | block | 映射表说要改的旧 URL 还返回 200(新旧两份) |
| canonical 指向旧址 / 跳转 | block | 新页 canonical 指向旧域名、会跳转或打不开的地址 |
| hreflang 断簇 | block | hreflang 指向跳转 / 404,或 A 列了 B、B 没列 A |
| 新加了 noindex | block | 基线里能收录的页改后带 noindex |
| 链式跳转 | warn | 跳了不止一跳 |
| 临时跳转 | warn | 用了 302 / 303 / 307 |
| 结构化数据丢了 | warn | 基线里有的类型改后没了 |
| title / H1 丢了 | warn | 改后为空 |
| 站内链接指向跳转 | warn | 新页站内链接还指向会跳转的旧地址 |
| sitemap 里有旧地址 | warn | 新 sitemap 列了会跳转 / 404 的地址 |

给了 GSC 点击时,报告按点击排序,并写「有点击的旧页里没有 block 问题的点击占比」`[est]`。这是改动当天的结构检查,真实点击保留要等 GSC 数据回来:site-move 循环在改后 4 周点击保留率 ≥ 90% 且没有新错误时收口。

实测(测试站 Soilsense,30 页英德双语,预埋 10 个迁移问题):10 个全部找到,误报 0;没改动的站自己对比自己 0 条。真实站(everyinfra.com,基线 80 页、对比时查了 146 页)自己对比自己 0 条,约 6 分钟。站内链接只查指向基线旧地址和映射表地址的那些;sitemap 里的新增页最多多抓基线规模的 1.2 倍加 50 页。

## 5. 不做什么

- 不替用户改服务器跳转配置。找到的问题写成清单,修复走分支和草稿 PR。
- 不把一次冲高当成换阶段;不在用户没回复时重复问。
- 不在基线里存页面正文,只存对比要用的字段。
