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

## 二、阈值体系表(siteone `--ci` 参数语义 → 本套件等价物)

| 门参数 | siteone 语义(照抄) | 本套件等价物 | 起步默认 |
|---|---|---|---|
| min-score N | 总分/类分 <N 即失败,可按类分别设门 | health_score 主分+category_scores;门上 `--min-score 80`、按类 `--min-score category:experience=70` | 80(Good 档 71+,先松后紧) |
| max-criticals | CRITICAL 命中数上限,**默认 0** | site_audit --json 的 `critical` 计数(脚本本身 exit 1);门上 `--max-criticals 0` | 0 |
| max-warnings N | WARN 命中数上限 | health_score `warn_score` 单列;门上 `--max-warnings` | 站点自校,起步不设 |
| min-pages N | **样本地板:有效页 <N 直接失败**——防"只爬 1 页也绿灯" | fetch guard 拒审不进分母(verdict=refused)+ 门内检查 scored=audited−refused ≥N;监控侧同律=防疲劳三律"阈值×最小样本地板" | ≥5(单页门也必须显式写 1) |
| max-avg-response | 抓取平均响应时延上限 | monitor thresholds `latency_increase_pct`×`latency_min_ms`(相对+地板式,比绝对阈值抗机器差异[推断]) | — |
| baseline + max-score-drop | 与基线跑分对比,降幅 >N 分判失败 | `audit_compare.py --old base.json --new audit.json --baseline-gate 3`(主分跌幅 old−new>N → exit 1);纪律见 §七 | 3–5 分 |
| fail-on-code | 指定检查 code 出现即失败(加严白名单) | monitor 告警 code 直接对应;门上 `--fail-on-code robots_sitewide_block,duplicate_title` | — |
| ignore-code | **已接受**的失败项:不进退出码,报告保留 ignored 列表 | health_score `--ignore/--severity`(忽略=不进 findings 不进分);monitor accepted_codes(接受≠消失,周报仍计数) | — |

**ignore 优先于 fail**:同一 code 两边都配时 ignore 赢——"已接受"必须压倒"加严",否则接受
机制形同虚设。同构纪律:health_score 的 CLI `--ignore/--severity` 优先于 `--config` 同一条目。

**exit code 契约**:siteone 用 0=过 / 10=门失败;本套件脚本层沿用 POSIX 0/1/2(site_audit
1=有 CRITICAL、audit_compare 1=gate 触发、action.yml min-score 1),与 monitor diff 的
0/1/2/4(运维四态)一致——CI 消费者只看二态+注解,运维守护看分级。10 契约保留给
`monitor.py diff --ci`(borrow-specs D1 P1 规格:输出 `{passed,checks:[{metric,operator,
threshold,actual,passed}]}` + JUnit + `::error` 注解)与 audit-pr-gate job 的门步骤,作两条
门线的统一失败码。

## 三、LHCI 断言 schema(CI 门怎么"写断言")

assertions 的 key 语法(Lighthouse CI `assert.assertions`):

| key 形态 | 断言对象 | 例 |
|---|---|---|
| `<auditId>` | 单个 Lighthouse audit | `largest-contentful-paint` |
| `categories:<id>` | 类别分(performance/accessibility/seo…) | `categories:performance` |
| `user-timings` | 自定义 timing 条目数 | `["warn",{maxLength:20}]` |
| `resource-summary[:类型][:指标]` | 资源体积汇总条目 | `resource-summary:script:size` |

值为 `level` 或 `[level, options]`;**level = off|warn|error**——error 才影响退出码,warn 只
注解;off 用于继承 preset 后逐条关闭(比整包关安全)。options 四件:`minScore`(0-1,通过率)、
`maxLength`(条目数/字节)、`maxNumericValue`(metric 原值:ms/字节/无量纲)、
`aggregationMethod`;个别 audit 另有专属 option(如体积类的 maxWasteMs)。
聚合方法(默认 3 runs):**median**=各 run 指标取中位(默认)/ **optimistic**=取最好 run
(采集抖动大时)/ **pessimistic**=取最差 run(硬门,p95 思维)/ **median-run**=取 performance
分中位的那一次 run、全部指标用该 run 的(指标相关性重要时)。preset 三种:
`lighthouse:default`(全 off)/ `lighthouse:no-pwa` / `lighthouse:recommended`(成套常用
warn/error)——先选 preset 再逐条覆盖。

**key_pages 的 CWV 断言 → monitor.py expect 机制对照**(/pricing 页为例)。
LHCI 写法(跑 lighthouse-ci,采 lab 数据):

```yaml
assertions:
  categories:performance: ["error", {minScore: 0.8}]
  largest-contentful-paint: ["error", {maxNumericValue: 2500, aggregationMethod: median}]
  cumulative-layout-shift: ["warn", {maxNumericValue: 0.1}]
  resource-summary:script:size: ["warn", {maxNumericValue: 1500000}]
  user-timings: off
```

monitor.py 写法(config.json,零 headless 依赖):

```json
{"key_pages": [{"path": "/pricing", "expect_substring": "Pricing", "selector": "h1"}],
 "thresholds": {"latency_increase_pct": 100, "latency_min_ms": 500}}
```

| LHCI 概念 | monitor/audit 等价物 | 边界 |
|---|---|---|
| categories:minScore | health_score 类别分 + 门 --min-score | 口径不同:CWV 是 lab 单页,我们是站内样本 |
| auditId:minScore(内容通过率) | expect_substring 断言 → `content_regression` | 只断"在场",不断 CWV 数值 |
| maxNumericValue(LCP/CLS) | 无 lab CWV——接 PSI/CrUX 数据源或外跑 lighthouse-ci | 分层互补,不是替代 |
| aggregationMethod | 双窗口判定(7 天基线同向确认)+ diff prev 只取 status='ok' | 我们的"多 run"=多天快照 |
| level off/warn/error | info/warn/critical + accepted_codes(off≈接受,周报仍计数) | — |
| maxLength(条目上限) | 最小样本地板(阈值×地板) | 同构:防小样本噪声 |

## 四、unlighthouse 智能采样(大站门禁:审计多少页才有代表性)

**采样协议(路由模板归一)**:1) URL 路径末段是 slug(数字/id/长串)的替换为占位符,得路由
模板(`/blog/<slug>`);2) 按 站点+模板 groupBy 分组;3) 每组抽 ≤8 个样本 ∪ 手工清单(钱页
永远进样本);4) 全局上限 maxRoutes=200,超出截断并标注 coverage;单组 >8 警告"样本被截"。
**URL discovery 优先级链**(高→低,取到即止):手工清单 → robots.txt 的 Sitemap 行 →
sitemap.xml(**≥50 条即关闭爬虫**——代表性够,省时间)→ 爬虫兜底(链接发现)→ 前端路由
定义(Nuxt/Next router 抽取)。抓取失败重试 3 次、2s 退避;仍失败记 error 不记 0(§五同律)。

本套件等价物:`monitor.py sample-keypages`(D1 P1 规格,同算法:末段 slug 归一→groupBy→
每组随机抽 8 ∪ 手工 key_pages);落地前门禁页清单=config.json key_pages 手工维护 +
sitemap_audit.py 抽样。**样本纪律**:门禁跑分必须输出 coverage_ratio(样本/全站),两次
coverage 口径不同的分数不可比(Ryte 官方;health_score 的 coverage_note 同口径)。

## 五、serpbear 防假 0 纪律(排名/可见性类指标的 CI 语义)

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

## 来源

siteone-crawler(`--ci` 阈值体系、exit 10、ignore 优先)、lighthouse-ci(assertions schema/
聚合方法/preset,官方 configuration.md)、unlighthouse(smart sampling、discovery 链、
retry)、serpbear(防假 0、prev-100、digest 头)——深读结论与【官方】/[推断]标注见
[borrow-specs](../research/borrow-specs.md) D1/D2 及其来源节。门禁与运维守护分工、三形态
部署与防疲劳三律:[continuous-operations](continuous-operations.md);阈值四法与月度调校:
[alert-threshold-guide](alert-threshold-guide.md)。
