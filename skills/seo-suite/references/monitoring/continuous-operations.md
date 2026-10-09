# 持续运营手册:从一次性审计到长期监控守护

> 建立于 2026-10-09,同日按 20 路外部审计(见文末"审计致谢")加固。配套实装:
> `scripts/monitor.py`(init/run/diff/report/quarantine/maintenance)与 `scripts/notify.py`(分级路由)。
> 阈值方法论与基线纪律沿用 [alert-threshold-guide](alert-threshold-guide.md);页面级 13 元素对比走 [seo-drift-monitoring](seo-drift-monitoring.md)。

## 一、分层监控表:日检四问 → 周检趋势 → 月度校准

| 层 | 频率 | 查什么 | monitor.py |
|---|---|---|---|
| 日·可见性 | 每日 | 关键页 `site:` 抽查(可见页数);端点被拦=skipped、DOM 改版=unparseable,均不告警 | run --checks daily |
| 日·流量异常 | 每日 | GSC 导出点击合计环比(gsc.csv 有才查,不猜数) | 同上 |
| 日·索引 | 每日 | robots.txt 哈希 + `* 组全站 Disallow` 误封检测 | 同上 |
| 日·存活 | 每日 | 首页+关键页状态码/时延/https 混合内容/expect_substring 断言 | 同上 |
| 周·漂移 | 每周一 | 关键页 title/meta/canonical/og/watch **分字段** diff、robots 变更、AI 爬虫放行矩阵翻转 | run --checks weekly |
| 周·趋势 | 每周一 | sitemap URL 数与 lastmod 对比、llms.txt 变更、**SSL 证书到期(30/14/7/0 梯度)** | 同上 |
| 周·汇总 | 每周一 | 周报(趋势+告警汇总+建议 PR 列表)进 job summary/邮件 | report --days 7 |
| 常态 | 每次调度 | dead man's switch:heartbeat ping(/ok、/fail)+ notify 端停摆检测(dead_man) | init --heartbeat-url |
| 月·校准 | 每月 | 阈值/冷却期复盘、noise 率、改版后重建基线 | 手动,见 alert-threshold-guide 第五节 |

日检四问的设计原则:**每问都能在 5 分钟预算内独立完成**(`--budget-minutes`,超时中止剩余检查),
budget 中止的 run 状态记 `partial`,照常入库但**不充当 diff 基线**(半截数据防污染);
任何一问的数据源缺失都显式记 skipped,绝不拿旧值顶替或猜数。

**维护窗口**(改版/迁站期防误报):`monitor.py maintenance --from T1 --to T2 --reason R`
登记窗口;窗口内 run 照常记快照,diff 只留档不产告警(uptime-kuma 惯例)。

**并发与基线卫生**(本地多 cron/挂死 run 安全):
- SQLite WAL + busy_timeout=30s,目录级 flock——两个 cron 撞车排队而非 `database is locked` 崩溃;
- run 先落 `status='running'` 再跑检查,终态 `ok/partial/failed`;卡死 >30min 的 run 由
  `sweep_stale_runs` 自动回收为 failed;
- diff 的对比基线只取 `status='ok'` 的 run;发现某次 run 数据被污染(WAF 返回 200 的维护页等)
  用 `monitor.py quarantine <run_id>` 隔离,`--undo` 解除——不用再手工改 SQLite;
- 历史按 PruneDB 纪律自动裁剪(保留最近 400 次 run,连带快照/告警/runs 文件)。

## 二、告警四级 × playbook

| 级别 | 触发(monitor.py code) | 查哪 | 何时升级 | 自动还是人审 |
|---|---|---|---|---|
| critical | `homepage_down`/`key_page_down`(状态码≥400)、`robots_sitewide_block`、`visibility_zero`(过最小样本地板)、`ssl_cert_expiry`(≤7 天)/`ssl_cert_expired` | 立即查发布记录与 CDN;robots 逐行 diff;GSC 网址检查+处罚通知;证书立即续期 | 立即处理;1 小时未定位 → 按 [seo-drift-monitoring](seo-drift-monitoring.md) L1–L5 五层协议走 | auto 项可直接执行;其余人审当天 |
| warn | `visibility_drop`/`sitemap_urls_drop`/`gsc_clicks_drop`(百分比阈值×地板)、`mixed_content`、`fetch_error_confirmed`(连续两次)、`content_regression`(expect_substring 断言失败)、`ssl_cert_expiry`(≤14 天)、`dead_man`(监控停摆) | GSC 分层(query/page/device);sitemap 生成管道;本机网络→DNS→WAF;cron/Actions 调度 | 连续 2 个周期命中或恶化成 critical 形态 → 升 critical 处理节奏 | draft PR 项人审;1–2 个工作日 |
| info | `title_meta_drift`(分字段)/`robots_changed`/`ai_posture_flip`/`llms_txt_*`/`latency_spike`/`gsc_clicks_spike`/`ssl_cert_expiry`(≤30 天) | diff 变更是否有意;发布日历对齐 | 无升级路径;周报汇总后决定是否处理 | 人审,排进本周计划 |
| low | `*_resolved`(自愈:上次告警本次消失) | 不查;进周报复核一眼即可 | — | 全自动,静默 |

升级的硬规则:**只有"影响面扩大 × 连续命中"才升级,单次越界不升级**;事件型(critical 类)不受
连续命中约束,出现即告警。**双窗口判定**:critical 需"昨日短窗触发 + 7 天基线同向确认"——
7 天基线同样异常(昨日才是抖动)时自动降 info 并在文案注明(SRE 多窗口 burn rate 的日检版);
库龄不足 7 天时保持原级别。

**告警抑制树**(Prometheus inhibition 纪律,替代"每 run Top-K 截断"):`homepage_down`
抑制所有 `key_page_down`/`content_regression`(站点已 down,页面级全是派生噪声);
`fetch_error_confirmed` 抑制同页内容派生判定(`title_meta_drift`/`mixed_content` 等——
抓都抓不到,内容层结论不可信)。被折叠的告警记录在 diff 输出的 `inhibited` 字段,只留痕不通知。

**响应 SLA 与值守表**:

| 级别 | 首响 | 通知节奏(notify.py) | 谁接 |
|---|---|---|---|
| critical | 当天,小时级 | 即时,全渠道;冷却 12h;suppressed 只进报告不进通知 | 值守/站长本人 |
| warn | 1–2 个工作日 | 日批摘要(--flush warn);渠道失败保留 pending 不丢 | SEO 负责人 |
| info | 本周 | 周批摘要(--flush info,随周报) | 周会过一遍 |
| low | 不响应 | 永不推送,只进 report | — |

## 三、防疲劳三律

1. **百分比阈值必须乘最小样本地板**:可见页 <3、sitemap <20 URL、GSC 点击 <5 的站,百分比没有意义([alert-threshold-guide](alert-threshold-guide.md) 第二节同款纪律)。地板未过 → 只记 info 基线,不告警。
2. **钱词实时、长尾周报**:关键页/钱词走日检通道(critical/warn 即时或日批);长尾与 info 级一律进周报批量消化,永不单独推送。
3. **调优期删噪**:每月复盘 noise 率(告警里多少不需要行动);`config.json` thresholds 放宽一档或加连续触发条件;改版/迁移期间登记维护窗口(不再是"显式接受误报")。冷却期默认 critical 12h / warn 24h / info 168h,同指纹冷却期内重复告警标记 **suppressed:只进报告,不进通知路径**(diff 的 counts/退出码同步排除,notify 路由前再剔除一次——双层保险);**陈旧 alerts.json 拒发**(notify `--max-age`,默认 30 分钟,防 run 失败时旧 critical 重播)。

## 四、安全边界表:自动安全项 vs 必须 draft PR

| 动作 | 边界 | 理由 |
|---|---|---|
| robots.txt 误封回滚(`Disallow: /` 删除) | **auto** | 几乎总是部署事故,分秒必争 |
| sitemap ping / 重新提交 | **auto** | 幂等、无副作用 |
| robots 校验报告、meta 长度修正建议 | **auto**(只产 patch 建议) | 纯只读分析 |
| meta/title 修正、混合内容批量替换 | **draft PR** | 改内容,须人审合并 |
| 301 重定向表、canonical 修正 | **draft PR** | 错误重定向=二次事故 |
| llms.txt 生成/更新(用 `llmstxt.py generate`) | **draft PR** | 内容资产,按 [llms-txt-guide](../content/llms-txt-guide.md) 人审 |
| 内容重写、删除页面、线上配置变更 | **human** | 不可逆或涉及业务判断 |

铁律:monitor.py 只读写本地 `.seo-monitor/`;对外动作(发 PR、改线上)永远是"起草+人确认",与套件"对外动作"约束一致。AI 爬虫放行翻转(`ai_posture_flip`)只告警不建议直接改——放行与否是 visibility/protect-ip 的取向决策([ai-crawler-policy](../technical/ai-crawler-policy.md))。

## 五、三种部署形态对照

| 形态 | 适合 | 状态持久化 | 告警链路 |
|---|---|---|---|
| GitHub Actions(模板 `.github/workflows/seo-monitor.yml`) | 站点已在 GH,零运维 | **commit-back**(monitor.db 提交回库,永不过期;cache 仅迁移期兜底) | secrets 注入 webhook,notify.py 路由;critical 自动开 label issue,归零自动关;workflow 失败有 if: failure() 兜底 |
| 本地 cron / launchd | 内网站、不想出门数据 | 本地 `.seo-monitor/` 天然持久(WAL+flock,多 cron 安全) | cron 行内判断 diff 退出码再调 notify.py(--max-age 防旧告警重播) |
| `claude -p` 无头调 skill(Routines/Shortcuts 可同款定时) | 要"自动完善"闭环:告警→起草修复 | 本地 | agent 读 diff 输出,按本手册 playbook 起草 |

多站点:仓库 Variable `SEO_SITES` 配 JSON 数组,workflow 自动 matrix 扇出(fail-fast 关闭,
一站慢/挂不连坐),每站独立监控目录 `.seo-monitor-<host>`/独立 concurrency 组/独立 issue。

**dead man's switch(监控器自身的监控)**:`init --heartbeat-url` 配 healthchecks.io 类
ping URL(或自建);run 成功 ping `/ok`、失败 ping `/fail`(立即告警不等超时,堵死
"run 失败只变红叉不发通知"的空窗);notify 端另有兜底——距上次成功 run 超 2×
`run_cadence_hours` 即发 `dead_man` 告警。grace 公式:**cron 间隔×2+典型运行时长**,
检查规模(页面数)增长后重估,别设一次不管。

**claude -p prompt 模板(成功标准必须写进 prompt,agent 才能自判收工)**:

```
claude -p "使用 seo-suite skill 的持续监控守护:
1) 运行 python3 scripts/monitor.py run --checks daily --dir .seo-monitor;
2) 运行 python3 scripts/monitor.py diff --dir .seo-monitor --format text --dry-run;
3) 若出现 critical/warn,按 references/monitoring/continuous-operations.md 对应级别
   playbook 起草修复(boundary=auto 的直接改;boundary=draft_pr 的只产 draft PR,
   禁止 merge,禁止改线上配置);
4) 输出:检查摘要+告警清单+已起草的修复。
成功标准:diff 完成且每条 critical/warn 都有对应 playbook 动作或 draft PR 链接;
失败标准:monitor.py 未解释的非零退出码,或存在无后续动作的 critical。"
```

部署后第一周只看不断电:首日建基线,第二日起 diff 才有意义;第一次 weekly report 之后把 thresholds 从"经验起点"校准成本站值。

**本地 cron 参考行(diff 退出码 0=无/1=critical/2=warn/3=run 未完成/4=错误,只在 1/2 时通知)**:

```cron
17 3 * * *  cd /path/to/site && \
  python3 /path/to/seo-suite/scripts/monitor.py run --checks daily && \
  python3 /path/to/seo-suite/scripts/monitor.py diff --out .seo-monitor/alerts.json; \
  rc=$?; [ $rc -eq 1 -o $rc -eq 2 ] && \
  python3 /path/to/seo-suite/scripts/notify.py run --dir .seo-monitor \
    --alerts .seo-monitor/alerts.json --flush warn --max-age 30
23 4 * * 1  cd /path/to/site && python3 /path/to/seo-suite/scripts/monitor.py run --checks weekly && \
  python3 /path/to/seo-suite/scripts/monitor.py report --days 7 | mail -s "SEO 周报" you@example.com
```

rc=3(run 未完成)不触发 notify——run 挂了不该把昨天的 alerts.json 重发一遍;
该路径的告警由 heartbeat `/fail` 与 notify 的 dead_man 检测兜底。

**GSC 流量问的喂数方法**:monitor.py 不带任何 API key,GSC 数据靠导出文件。在 run 之前把你账号下的效果报告导出(全期或固定 28 天窗)存为 `.seo-monitor/gsc.csv`(列含 Query,Clicks,Impressions),cron 里可用你自己的凭据先拉取;文件缺失=流量问 skipped,不猜数。口径固定:同一数据源、同一窗口、同一过滤,口径一变基线作废。

**config.json 关键项(diff 与 notify 共读)**:

```json
{
  "site": "https://example.com", "market": "us",
  "key_pages": ["/",
    {"path": "/pricing", "expect_substring": "Pricing", "selector": "h1"}],
  "budget_minutes": 5,
  "heartbeat_url": null, "run_cadence_hours": 24,
  "maintenance_windows": [{"from": "2026-10-11T02:00", "to": "2026-10-11T04:00",
                            "reason": "改版迁移"}],
  "cooldown_hours": {"critical": 12, "warn": 24, "info": 168},
  "thresholds": {"visibility_drop_pct": 30, "visibility_min_sample": 3,
                 "sitemap_urls_drop_pct": 15, "sitemap_min_sample": 20,
                 "gsc_clicks_drop_pct": 20, "gsc_min_clicks": 5,
                 "latency_increase_pct": 100, "latency_min_ms": 500,
                 "mixed_content_min": 3}
}
```

- **key_pages 两种形态**:字符串路径,或对象 `{path, expect_substring, selector}`——
  `expect_substring` 断言页面 200 但关键词消失(空白渲染/软 404/误改版,UptimeRobot
  keyword monitor 同款);`selector`(支持 `tag`/`#id`/`.class`/`re:<regex>`)圈定
  字段级 diff 的 watch 区,模板无关区块不进指纹(changedetection.io 思路)。
- **secret 只经环境变量**:channels 里只存 env 引用名(`SEO_MONITOR_SLACK_WEBHOOK` /
  `SEO_MONITOR_DISCORD_WEBHOOK` / `SEO_MONITOR_TG_TOKEN`+`SEO_MONITOR_TG_CHAT` /
  `SEO_MONITOR_SMTP_PASS` / `SEO_MONITOR_WEBHOOK_URL`);monitor 的 save_config 检出
  webhook/token 样式明文即拒写,`.gitignore` 整目录排除,commit-back 只显式 add
  monitor.db 与 runs/——secret 三层都不进 git。
- **通用 webhook**(Apprise 式):`SEO_MONITOR_WEBHOOK_URL` 支持 `json(s)://`/`form(s)://`/
  `text(s)://` scheme 决定载荷形态,裸 https 默认 JSON `{"text": ...}`——新渠道一行配置,
  渠道间故障隔离,失败 detail 自动脱敏(token 不进日志)。

## 六、与套件现有监控件的分工

- 本手册+monitor.py = **站点级守护进程**:调度、快照存储(SQLite runs/snapshots/alerts 三表)、阈值判定、通知分级、周报。回答"今天有没有事"。
- [seo-drift-monitoring](seo-drift-monitoring.md) = **页面级漂移取证**:13 元素基线/17 规则对比、算法更新归因。monitor.py 报 `title_meta_drift` 或流量断崖后,转它做细粒度归因(diff 命中的项按其交叉路由走)。
- [alert-threshold-guide](alert-threshold-guide.md) = **阈值方法论**:分级定义、波动带/相对变化/事件型/连续触发四法、月度调校。monitor.py 的 thresholds/cooldown 参数就是它的工程化落地。
- [kpi-definitions](kpi-definitions.md) / [report-templates](report-templates.md) = 周报口径与对外模板;monitor.py report 的"趋势+告警汇总+建议 PR"是它们的机器底座,人写 stakeholder 报告时直接引用。
- 处罚/负面 SEO 处置在 [penalty-recovery](penalty-recovery.md)(monitor.py 只负责发现,不负责处置)。

## 来源

- 分层(日四问/周趋势)、四级告警、百分比阈值防疲劳、安全自动项 vs 人审边界:行业共识实践(crawlseo/iannuttall/claude-seo 等仓库深扫,详见 [seo-drift-monitoring](seo-drift-monitoring.md) 来源节),按本套件"不猜数/不炸渠道/人审不可逆动作"约束改写。
- budget/dry_run 参数形态参考本套件 geo-score 系脚本的预算纪律。

## 审计致谢(2026-10-09,20 路外部审计全量融入)

本轮加固的实现全部来自以下审计的建议部分(报告存档于 seo-enrichment-notes/monitor-audit/):

- **红队自审(05)**:suppressed 不进通知路径与退出码(P0)、notify --max-age 陈旧拒发、
  SQLite WAL+busy_timeout+flock、基线 status='ok' 守卫+quarantine+budget 半截标 partial、
  重定向逐跳 SSRF 复查、channels 只存 env 引用+save 拒写明文+git 排除、Bing cites 空→unparseable。
- **常驻 server 形态(01,serposcope/searchmirror)**:run 状态机(running→ok/partial/failed)、
  sweep_stale_runs、PruneDB(keep=400)、channels secret 只存 env 引用。
- **GitHub Actions 生态(02,TrendWatch/lighthouse-check-action)**:基线 cache→commit-back
  (排除 config secret)、critical 开 label issue+归零自动关、if: failure() 兜底、
  SEO_SITES matrix 多站点、渠道故障隔离+URL 脱敏。
- **商业基准(04,Semrush/UptimeRobot/StatusCake)**:SSL 到期 30/14/7/0 梯度周检、
  关键页 expect_substring 断言(content_regression)。
- **垂直领域(06,uptime-kuma)**:维护窗口;**(10,Google SRE Workbook)**:双窗口判定
  (critical 需 7 天基线同向确认,单日抖动降 info)。
- **周边形态(17,changedetection.io)**:关键页字段级 diff(title/meta/canonical/og/watch)
  +selector 圈定;**(18,healthchecks.io)**:dead man's switch(heartbeat /ok、/fail);
  **(19,Alertmanager)**:告警抑制树(site_down 抑制 page_down,替 Top-K)。

## 附:方法边界与第一周清单

**已知边界(不掩盖)**:
- 可见性抽查走 Bing HTML 端点,无 SLA、非官方索引数——它是"方向抽样"不是排名追踪;端点被拦/人机验证记 blocked、**DOM 改版解析不出 cite 记 unparseable**,两者都不告警;告警文案自带"非官方方向抽样"标注。要精确排名用自己的追踪工具数据。
- 双窗口判定的长窗基线取"最接近 7 天前的 ok run";库龄不足 7 天时无法确认,保持原级别(宁报勿漏)。
- robots 姿态判定是近似(组内根路径 disallow 即视为 blocked),最终判断跑 `robots_posture.py` 全量。
- 网络层抓取失败单次只记 info,连续两次才升 warn——本机断网不该炸全站告警。
- sitemap 解析限 5000 loc/5 层 index,budget 耗尽时该 run 记 partial,已解析部分入库但不充当基线。
- GSC 口径是"两次 run 之间导出文件的合计变化",不是严格的 7 日滚动;要严格口径请固定窗口导出。
- SSRF 防护覆盖请求前与每一跳重定向;fake-IP 代理段(198.18.0.0/15)默认豁免,
  `SEO_MONITOR_STRICT_SSRF=1` 恢复全拒;guard 与连接间的 DNS rebinding TOCTOU 是已知取舍。
- 排名抓取是显式边界外的事(serposcope 之死证明开源养不活 SERP 军备竞赛)——本监控只盯自家可控面。

**第一周上手清单**:
1. `monitor.py init --site URL --market XX [--heartbeat-url U]`(关键页补进 config 的 key_pages,
   需要 expect_substring/selector 的用对象形态);
2. 手动 `run --checks daily --dry-run` 看四问是否都能出数(gsc.csv 该喂就喂);
3. 正式 `run` 建基线,隔天再 `run` + `diff --format text` 验证零告警;
4. 配一个渠道的 webhook(env 注入),用 `notify.py run --dry-run` 演练路由
   (suppressed/陈旧拒发/通用 webhook 都会打印出来);
5. 部署 cron/GH Actions(commit-back 基线+heartbeat+issue 兜底开箱即用),
   一周后拿 `report --days 7` 校准 thresholds 与 key_pages;
6. 每月按 [alert-threshold-guide](alert-threshold-guide.md) 第五节复盘 noise 率。
