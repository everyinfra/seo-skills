# CI 质量门手册:siteone 阈值 × LHCI 断言 × unlighthouse 采样

> 建立于 2026-10-10。三家 CI 门设计(siteone-crawler `--ci` 阈值体系 / Lighthouse CI 断言
> schema / unlighthouse 智能采样)合并为可执行手册;规格与口径见
> [borrow-specs D1/D2](../research/borrow-specs.md),运维守护与三形态部署见
> [continuous-operations](continuous-operations.md),阈值方法论沿用
> [alert-threshold-guide](alert-threshold-guide.md)。PR 门答"这次改动有没有退步",运维门
> (monitor.py diff)答"站点今天有没有事",两种门并存。

## 一、三件套命令地图:审计 → 打分 → 回归门 → 格式化 → PR 集成

```
site_audit.py URL --json --market XX → audit.json(现场审计;fetch guard 拒审≠失败)
  ├─ health_score.py --input audit.json --json → 0-100 主分+类别分(Ahrefs/Lumar 口径)
  ├─ audit_compare.py --old base.json --new audit.json --baseline-gate 3 → 回归门(§二/§七)
  └─ ci_format.py audit.json --format github|sarif|junit|json → 注解/JUnit/SARIF/摘要
PR 集成:仓库根 action.yml(url+min-score+format 一站式)或 seo-monitor.yml 的 audit-pr-gate
运维门(另一条线):monitor.py run → diff(退出码 1/2 即告警,见 continuous-operations)
```

| 环节 | 脚本/载体 | 职责 | 退出码 |
|---|---|---|---|
| 审计 | `scripts/site_audit.py --json` | 逐 URL findings/meta/verdict/ai_search_health | 0 / 1=有 CRITICAL / 2=用法错 |
| 打分 | `scripts/health_score.py --input ... --json` | 主分+六类分+impact 排序 | 0 / 1=Weak 档 / 2=输入错 |
| 回归门 | `scripts/audit_compare.py --old/--new --baseline-gate N` | 新增/修复 issue+分数覆盖面对比+跌幅门 | 0 / 1=gate 触发 / 2=输入错 |
| 格式化 | `scripts/ci_format.py audit.json --format github` | `::error/::warning` 注解、JUnit、SARIF | 恒 0(门禁交给 min-score/--baseline-gate) |
| PR 集成 | 仓库根 `action.yml` / `seo-monitor.yml` 的 `audit-pr-gate` job | 组装上述步骤(§六配方 A) | min-score 门 ::error+exit 1;job 门 exit 10 |

action.yml 是三步的可复用封装(外部仓库 `uses:` 一行接入);audit-pr-gate job 是本仓库内的
显式等价物。两者都不因 site_audit 的 rc=1(CRITICAL)直接失败——那是审计结论,门禁交给阈值。

## 二、阈值体系表(siteone `--ci` 参数 → 本套件等价物)

siteone-crawler 的参数名和默认值取自它的[README](https://github.com/janreges/siteone-crawler)(核对 2026-10-21):`--ci` 开启质量门，门失败退出码 10；总分和类分是 0.0–10.0 分制，本套件是 0–100 分制。下表第三列只列**本套件真实存在的入口**——本套件的脚本没有名为 `--min-score`、`--max-criticals`、`--max-warnings`、`--fail-on-code` 的参数(这些门由 `action.yml` 输入和 `audit-pr-gate` 的门步骤实现)，不要照 siteone 的写法抄命令。

| siteone 参数(默认值) | 语义 | 本套件真实入口 | 起步默认(本套件口径) |
|---|---|---|---|
| `--ci-min-score`(5.0)及各类分(`--ci-min-seo` 等) | 总分或类分低于阈值即失败 | `action.yml` 的 `min-score` 输入(0 = 不启用);`audit-pr-gate` 的 `MIN_SCORE`;类分用 `health_score.py --json` 的 `category_scores` 自行比较 | 总分 80(Good 档 71+ 起步，先松后紧) |
| `--ci-max-criticals`(0) | CRITICAL 数上限 | `audit-pr-gate` 的门步骤检查 `critical == 0`(失败 exit 10);`site_audit.py` 有 CRITICAL 时本身退出码 1 | 0 |
| `--ci-max-warnings`(不检查) | WARN 数上限 | `health_score.py --json` 的 `warn_score` 单列，自行比较 | 站点自校，起步不设 |
| `--ci-min-pages`(10) | 样本地板:有效页数低于阈值即失败，防「只爬 1 页也绿灯」 | `audit-pr-gate` 的 `MIN_PAGES`(门步骤检查 scored ≥ MIN_PAGES，失败 exit 10);fetch guard 拒审的页不进分母(verdict=refused) | ≥5(单页门必须显式写 1) |
| `--ci-max-avg-response`(不检查) | 平均响应时间上限(秒) | `monitor.py` 阈值 `latency_increase_pct` 加 `latency_min_ms`(相对增幅加地板) | — |
| `--ci-baseline` + `--ci-max-score-drop`(0) | 与基线 JSON 对比，总分降幅超过阈值即失败;基线缺失只警告并跳过检查 | `audit_compare.py --old base.json --new audit.json --baseline-gate N`(主分跌幅 old−new > N 则退出码 1;N 的纪律见 §七) | 3–5 分 |
| `--ci-fail-on-code`(无) | 出现指定 finding code 即失败 | 无同名参数。从 `audit.json` 的 findings 里用 `jq` 自行检查;或用 `monitor.py diff --ci` 的告警检查 | — |
| `--ci-ignore-code`(无) | 已接受的 code 不计入 critical / warning 计数，同时压过 `--ci-fail-on-code` | `health_score.py --ignore r1,r2`、`--severity rule=sev`、`--config rules.json`;`monitor.py` 的 `accepted_codes` | — |

**ignore 优先于 fail**:siteone README 明说 `--ci-ignore-code` 同时压过 `--ci-fail-on-code`，本套件沿用:同一 code 两边都配时 ignore 赢，否则「接受」机制形同虚设。`health_score.py` 的 CLI `--ignore/--severity` 优先于 `--config` 里的同一条目。

**exit code 契约**:siteone 用 0 = 通过、10 = 门失败(1 保留给运行错误)。本套件脚本层是 POSIX 的 0/1/2(`site_audit` 1 = 有 CRITICAL、`audit_compare` 1 = gate 触发、`health_score` 1 = Weak 档、2 = 用法错),`monitor.py diff` 是 0/1/2/4(0 无告警、1 有 critical、2 有 warn、4 用法或数据错);**10 只用于** `monitor.py diff --ci`(输出 `{passed,exit_code,checks:[{metric,operator,threshold,actual,passed}]}`,`--ci-format junit` 出 JUnit XML)和 `audit-pr-gate` 的门步骤。CI 消费者只看通过 / 失败，运维守护看分级。

`monitor.py diff --ci` 的检查项(都是 `monitor.py` 自己的阈值，见 [continuous-operations](continuous-operations.md) 的阈值出处):`visibility_drop_pct`、`visibility_min_sample`、`sitemap_urls_drop_pct`、`sitemap_min_sample`、`gsc_clicks_drop_pct`、`gsc_min_clicks`、`latency_increase_pct`、`latency_min_ms`、`mixed_content_min`、`pages_left_segment_pct`(配了 segments 才有)、`critical_alerts`、`warn_alerts`。数据缺失时该项记通过，不猜。

## 三、LHCI 断言 schema(CI 门怎么「写断言」)

来源:[Lighthouse CI configuration.md](https://github.com/GoogleChrome/lighthouse-ci/blob/main/docs/configuration.md)(核对 2026-10-21)。`lhci assert` 读 `assert` 配置，按断言结果退出。

| key 形态 | 断言对象 | 例 |
|---|---|---|
| `<auditId>` | 单个 Lighthouse audit | `largest-contentful-paint` |
| `categories:<categoryId>` | 类别分(performance、accessibility、seo 等)。只影响类别分，不影响类内各 audit 的断言 | `categories:performance` |
| `user-timings:<kebab-cased-name>` | 你用 `performance.mark` / `performance.measure` 打的自定义时间点，只能用 `maxNumericValue`(毫秒) | `user-timings:my-custom-measure` |
| `resource-summary:<resourceType>:(size\|count)` | 预算:资源体积(字节)或数量;类型如 `script`、`font`、`document`、`third-party` | `resource-summary:script:size` |

**写法**:值是 `level` 或 `[level, options]`。`level` 三选一:`off`(不检查;没写进 `assertions` 的 audit 也按 off)、`warn`(检查并打印到 stderr，失败**不**产生非零退出码)、`error`(检查，失败产生非零退出码)。`options` 三个阈值,分别比较 audit 结果的三个属性:
- `minScore`:`score`(0–1);
- `maxLength`:`details.items.length`(条目数);
- `maxNumericValue`:`numericValue`(毫秒、字节或无量纲，随指标而定)。
没写 options 时，默认是 `{"aggregationMethod": "optimistic", "minScore": 1}`。注意:用 LHCI 断言写体积预算时 `maxNumericValue` 的单位是**字节**;用 `budgets.json` 文件(`budgetsFile`，不能与其他 assert 选项同用)时单位是 **KB**。

**多次运行的聚合**(`collect.numberOfRuns`，默认 3):`aggregationMethod` 四选一:`median`(取各次运行的中位数)、`optimistic`(取最可能通过的那次)、`pessimistic`(取最不可能通过的那次)、`median-run`(取按关键性能指标判定最有代表性的那一次运行，再用这次运行里的该 audit 值;和 `median` 不同，因为被断言的 audit 不一定是用来选 run 的那项指标)。默认是 **optimistic**。想做硬门，用 `pessimistic`。

**preset**(`assert.preset`):`lighthouse:all`、`lighthouse:recommended`、`lighthouse:no-pwa` 三选一;先选 preset，再逐条覆盖，例如 `lhci assert --preset=lighthouse:recommended --assertions.uses-webp-images=off`。没有名为 `lighthouse:default` 的 preset。

**多 URL**:`assertMatrix` 对不同 URL 模式配不同断言。本地跑用 `lhci autorun`(collect → assert → upload);autorun 里子命令参数必须用 `=` 写法，如 `--collect.numberOfRuns=5`。

**key_pages 的 CWV 断言 → monitor.py expect 机制对照**(/pricing 页为例)。
LHCI 写法(跑 lighthouse-ci,采 lab 数据):

```yaml
assertions:
  categories:performance: ["error", {minScore: 0.8}]
  largest-contentful-paint: ["error", {maxNumericValue: 2500, aggregationMethod: median}]
  cumulative-layout-shift: ["warn", {maxNumericValue: 0.1}]
  resource-summary:script:size: ["warn", {maxNumericValue: 1500000}]
  uses-webp-images: off
```

monitor.py 写法(config.json,零 headless 依赖):

```json
{"key_pages": [{"path": "/pricing", "expect_substring": "Pricing", "selector": "h1"}],
 "thresholds": {"latency_increase_pct": 100, "latency_min_ms": 500}}
```

| LHCI 概念 | monitor/audit 等价物 | 边界 |
|---|---|---|
| categories:minScore | `health_score.py` 类别分 + `action.yml` 的 `min-score` | 口径不同:LHCI 是 lab 单页,我们是站内样本 |
| auditId:minScore(内容通过率) | expect_substring 断言 → `content_regression` | 只断"在场",不断 CWV 数值 |
| maxNumericValue(LCP/CLS) | 无 lab CWV——接 PSI/CrUX 数据源或外跑 lighthouse-ci | 分层互补,不是替代 |
| aggregationMethod | 双窗口判定(7 天基线同向确认)+ diff prev 只取 status='ok' | 我们的"多 run"=多天快照 |
| level off/warn/error | info/warn/critical + accepted_codes(off≈接受,周报仍计数) | — |
| maxLength(`details.items.length` 上限) | 无直接等价物 | 本套件的「最小样本地板」是防小样本噪声，和 maxLength 不是一回事 |

## 四、unlighthouse 智能采样(大站门禁:审计多少页才有代表性)

来源:unlighthouse 文档的[动态采样](https://unlighthouse.dev/guide/guides/dynamic-sampling)、[URL 发现](https://unlighthouse.dev/guide/guides/url-discovery)、[配置](https://unlighthouse.dev/api-doc/config)(核对 2026-10-21)。官方事实:
- **动态采样**:按路径树前缀把相似页面分组(例如 `/blog/*`)，每组随机抽样。`scanner.dynamicSampling` 配每组样本数;配置示例注明默认 8，同页正文写「默认 5」，两处不一致，以实际运行配置为准;`false` 或 CLI `--disable-dynamic-sampling` 关闭。
- **路由上限**:`scanner.maxRoutes` 默认 200。
- **URL 来源**:手工 `urls`(给出后禁用 sitemap 和爬虫)、`robots.txt`(读 Sitemap 和 Disallow)、`sitemap.xml`、爬虫(内部链接)。官方原话:sitemap 有 **over 50 paths** 时会禁用爬虫。
- `scanner.samples`(默认 1)是**每个路由跑几次 Lighthouse**，不是每组抽几个页面，不要混。

**本套件的采样协议**(`site_crawl.py` 与 `monitor.py sample-keypages` 的实现，本套件口径):
1. URL 路径末段是 slug(数字、id、长串)的，换成占位符得路由模板(`/blog/<slug>`);
2. 按「站点 + 模板」分组;
3. 每组随机抽 ≤8 个，再并上手工清单(钱页永远进样本);
4. 全局上限 200 个路由，超出截断并标注 coverage;单组样本被截时警告。
**发现链**(`site_crawl.py`):手工 `--urls` 清单 → robots.txt 的 Sitemap 行 → sitemap(递归 sitemap index;≥50 条 loc 即关闭爬虫；unlighthouse 文档措辞是 over 50，其源码 `routes.ts` 是 `>= 50`，本套件按源码) → 爬虫兜底(BFS 内链)。传输层失败重试 2 次(带退避)，4xx / 5xx 不重试;仍失败记 error，不记 0(§五同律)。

落地前，门禁页清单 = `config.json` 的 `key_pages` 手工维护 + `sitemap_audit.py` 抽样。**样本纪律**:门禁跑分必须输出 coverage_ratio(样本 / 全站);两次 coverage 口径不同的分数不可比(Ryte 的说法;`health_score.py` 的 `coverage_note` 同口径)。

## 五、防假 0 纪律(排名 / 可见性类指标的 CI 语义，借自 serpbear 的做法，本套件口径)

- **半数请求失败 → 判 error,而非排名 0**:失败被当成"排名 100/消失"会制造假跌告警、污染
  基线。monitor 同口径:抓取失败单次记 info、连续两次才 `fetch_error_confirmed`(warn);
  可见性端点被拦记 blocked/unparseable,不告警、不进分母、不猜数。
- **丢失特判展示**:上次有、本次丢的关键词展示为 `prev-<rank> → lost`(serpbear 用
  prev-100),与"稳定在第 100 位"区分;`visibility_zero` 必须过最小样本地板才告警。
- **digest 头部计数**:摘要第一行给 `N improved / M declined`——先方向分布后明细;
  monitor report 趋势汇总同构,人先看总量再看条目。

## 六、部署配方(每条标注用哪个脚本)

**配方 A:PR 门禁**——`.github/workflows/seo-monitor.yml` 的 `audit-pr-gate` job(完整实装
在 workflow;脚本:site_audit + health_score + ci_format;骨架),或外部仓库直接用仓库根
action.yml(`uses: everyinfra/seo-skills@main with: {url:..., min-score: 80, format: github}`):

```yaml
audit-pr-gate:
  if: github.event_name == 'pull_request'   # 只在 PR 跑;monitor job 保持定时/手动
  permissions: {contents: read}             # 门禁只读,不 commit
  env: {SITE_URL: "https://example.com", MIN_SCORE: "80", MIN_PAGES: "1"}
  steps:
    - run: python3 .../site_audit.py "$SITE_URL" --json > audit.json || [ $? -eq 1 ]
    - run: python3 .../health_score.py --input audit.json --json > health.json || [ $? -eq 1 ]
    - run: python3 .../ci_format.py audit.json --format github
    - run: python3 .../audit_compare.py --old .seo-baseline/audit-main.json --new audit.json --baseline-gate 3
```

(`|| [ $? -eq 1 ]` 只放行"有 CRITICAL/Weak 档"退出码交给门判;exit 2 用法错直接红。)

**配方 B:定时+基线对比**——main 分支夜跑并刷新基线(脚本:site_audit + audit_compare):
nightly `site_audit --json > audit.json` → `audit_compare --old .seo-baseline/audit-main.json
--new audit.json --baseline-gate 3` → 通过后把 audit.json commit 回 `.seo-baseline/`(基线进
git,alerts/config 不进,commit-back 纪律同 monitor.db)。PR 门的 --old 即引用该产物。

**配方 C:本地 pre-push hook**——`.git/hooks/pre-push`(脚本:site_audit + health_score
+ audit_compare):

```sh
#!/bin/sh
# 推送前对预发跑门;基线存在才比对(缺失=响亮 WARNING 跳过,§七)
SITE_URL=${SITE_URL:-https://staging.example.com}
python3 skills/seo-suite/scripts/site_audit.py "$SITE_URL" --json > "$TMPDIR/audit.json" || [ $? -eq 1 ]
SCORE=$(python3 skills/seo-suite/scripts/health_score.py --input "$TMPDIR/audit.json" --json \
        | python3 -c 'import json,sys;print(json.load(sys.stdin)["main_score"])')
[ "${SCORE%.*}" -lt "${MIN_SCORE:-80}" ] && { echo "SEO 门失败: score=$SCORE < ${MIN_SCORE:-80}"; exit 10; }
```

## 七、基线纪律(照抄 siteone:缺失永不静默)

1. baseline 缺失/不可读/解析失败 → **响亮失败,绝不静默**:audit_compare 对读不了/解析不出
   results 的 --old 直接 exit 2(不是当通过);workflow/hook 层再补 `::warning` +
   `skipped(baseline_missing)` 标记,门对其余检查照常——**既不静默当通过,也不静默当失败**;
   payload 记 baseline_missing 供周报统计(monitor 库龄>7 天同款 WARNING)。
2. `--baseline-gate` 配了但旧审计无可评分 URL(如全部被 fetch guard 拒审)→ 无基线可守:
   gate 不触发并在报告 note 明示"旧审计无可评分 URL,无基线可守",不是默默放行。
3. 基线会陈旧:与当前样本 coverage 口径不同(页数/市场/检查集变了)→ audit_compare 输出
   coverage_ratio 并声明两次分数不可比;改版后按 [continuous-operations](continuous-operations.md)
   登记维护窗口并重建基线。
4. PR 门的基线来源=main 夜跑产物(配方 B commit-back);**不要拿 PR 分支自己的首轮跑分当
   基线**——自己跟自己比永远绿灯。
## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 脚本参数没抄错 | 在写进 CI 前跑 `python3 scripts/site_audit.py --help`、`health_score.py --help`、`audit_compare.py --help`、`ci_format.py --help`、`monitor.py diff --help` | 命令里没有 `--min-score`、`--max-criticals`、`--fail-on-code` 这类 siteone 参数 |
| 门有样本地板 | `audit-pr-gate` 里 `MIN_PAGES` 已设;`health_score --json` 的 `urls_refused` 不进分母 | 可评分页 < `MIN_PAGES` = 失败，不是通过 |
| 基线来源正确 | `.seo-baseline/audit-main.json` 由 main 夜跑生成，不是 PR 分支自己的首轮结果 | 基线缺失 / 不可读 → `audit_compare.py` 退出码 2;不是静默通过 |
| 门失败时能定位 | `python3 scripts/ci_format.py audit.json --format github` 出注解 | PR 里能看到 `::error` / `::warning` |
| LHCI 断言写法 | 对照 §三：key 形态、level、options 名；`lhci assert --config=lighthouserc.json` 本地先跑一次 | 断言名拼错时 `lhci` 会报错；退出码非 0 即未通过 |
| 采样有代表性 | `python3 scripts/site_crawl.py https://example.com --json` 看发现链与 URL 数；`monitor.py sample-keypages --per-group 8` 看分组 | 每种页面模板都有样本;coverage_ratio 已输出 |
| 门禁阈值有出处 | 每个数值标注:官方（LHCI 默认值、web.dev 阈值）、siteone 默认值或本套件口径 | 无出处的数值标「本套件口径」 |

## 来源

siteone-crawler(`--ci` 阈值体系、exit 10、ignore 优先)、lighthouse-ci(assertions schema/
聚合方法/preset,官方 configuration.md)、unlighthouse(smart sampling、discovery 链、
retry)、serpbear(防假 0、prev-100、digest 头)——深读结论与【官方】/[推断]标注见
[borrow-specs](../research/borrow-specs.md) D1/D2 及其来源节。门禁与运维守护分工、三形态
部署与防疲劳三律:[continuous-operations](continuous-operations.md);阈值四法与月度调校:
[alert-threshold-guide](alert-threshold-guide.md)。
