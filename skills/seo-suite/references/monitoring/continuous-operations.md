# 持续运营手册:从一次性审计到长期监控守护

> 建立于 2026-10-09。配套实装:`scripts/monitor.py`(init/run/diff/report)与 `scripts/notify.py`(分级路由)。
> 阈值方法论与基线纪律沿用 [alert-threshold-guide](alert-threshold-guide.md);页面级 13 元素对比走 [seo-drift-monitoring](seo-drift-monitoring.md)。

## 一、分层监控表:日检四问 → 周检趋势 → 月度校准

| 层 | 频率 | 查什么 | monitor.py |
|---|---|---|---|
| 日·可见性 | 每日 | 关键页 `site:` 抽查(可见页数);端点被拦=skipped 不告警 | run --checks daily |
| 日·流量异常 | 每日 | GSC 导出点击合计环比(gsc.csv 有才查,不猜数) | 同上 |
| 日·索引 | 每日 | robots.txt 哈希 + `* 组全站 Disallow` 误封检测 | 同上 |
| 日·存活 | 每日 | 首页+关键页状态码/时延/https 混合内容 | 同上 |
| 周·漂移 | 每周一 | title/meta/canonical 哈希、robots 变更、AI 爬虫放行矩阵翻转 | run --checks weekly |
| 周·趋势 | 每周一 | sitemap URL 数与 lastmod 对比、llms.txt 变更 | 同上 |
| 周·汇总 | 每周一 | 周报(趋势+告警汇总+建议 PR 列表)进 job summary/邮件 | report --days 7 |
| 月·校准 | 每月 | 阈值/冷却期复盘、noise 率、改版后重建基线 | 手动,见 alert-threshold-guide 第五节 |

日检四问的设计原则:**每问都能在 5 分钟预算内独立完成**(`--budget-minutes`,超时中止剩余检查,部分结果照常入库),任何一问的数据源缺失都显式记 skipped,绝不拿旧值顶替或猜数。

## 二、告警四级 × playbook

| 级别 | 触发(monitor.py code) | 查哪 | 何时升级 | 自动还是人审 |
|---|---|---|---|---|
| critical | `homepage_down`/`key_page_down`(状态码≥400)、`robots_sitewide_block`、`visibility_zero`(过最小样本地板) | 立即查发布记录与 CDN;robots 逐行 diff;GSC 网址检查+处罚通知 | 立即处理;1 小时未定位 → 按 [seo-drift-monitoring](seo-drift-monitoring.md) L1–L5 五层协议走 | auto 项可直接执行;其余人审当天 |
| warn | `visibility_drop`/`sitemap_urls_drop`/`gsc_clicks_drop`(百分比阈值×地板)、`mixed_content`、`fetch_error_confirmed`(连续两次) | GSC 分层(query/page/device);sitemap 生成管道;本机网络→DNS→WAF | 连续 2 个周期命中或恶化成 critical 形态 → 升 critical 处理节奏 | draft PR 项人审;1–2 个工作日 |
| info | `title_meta_drift`/`robots_changed`/`ai_posture_flip`/`llms_txt_*`/`latency_spike`/`gsc_clicks_spike` | diff 变更是否有意;发布日历对齐 | 无升级路径;周报汇总后决定是否处理 | 人审,排进本周计划 |
| low | `*_resolved`(自愈:上次告警本次消失) | 不查;进周报复核一眼即可 | — | 全自动,静默 |

升级的硬规则:**只有"影响面扩大 × 连续命中"才升级,单次越界不升级**;事件型(critical 类)不受连续命中约束,出现即告警。

**响应 SLA 与值守表**:

| 级别 | 首响 | 通知节奏(notify.py) | 谁接 |
|---|---|---|---|
| critical | 当天,小时级 | 即时,全渠道;冷却 12h 防重复轰炸 | 值守/站长本人 |
| warn | 1–2 个工作日 | 日批摘要(--flush warn) | SEO 负责人 |
| info | 本周 | 周批摘要(--flush info,随周报) | 周会过一遍 |
| low | 不响应 | 永不推送,只进 report | — |

## 三、防疲劳三律

1. **百分比阈值必须乘最小样本地板**:可见页 <3、sitemap <20 URL、GSC 点击 <5 的站,百分比没有意义([alert-threshold-guide](alert-threshold-guide.md) 第二节同款纪律)。地板未过 → 只记 info 基线,不告警。
2. **钱词实时、长尾周报**:关键页/钱词走日检通道(critical/warn 即时或日批);长尾与 info 级一律进周报批量消化,永不单独推送。
3. **调优期删噪**:每月复盘 noise 率(告警里多少不需要行动);`config.json` thresholds 放宽一档或加连续触发条件;改版/迁移期间显式接受"基线重建期",期间 info 一律降级静默。冷却期默认 critical 12h / warn 24h / info 168h,同指纹冷却期内重复告警标记 suppressed 不再通知。

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
| GitHub Actions(模板 `.github/workflows/seo-monitor.yml`) | 站点已在 GH,零运维 | actions/cache 或提交回库 | secrets 注入 webhook,notify.py 路由 |
| 本地 cron / launchd | 内网站、不想出门数据 | 本地 `.seo-monitor/` 天然持久 | cron 行内判断 diff 退出码再调 notify.py |
| `claude -p` 无头调 skill(Routines/Shortcuts 可同款定时) | 要"自动完善"闭环:告警→起草修复 | 本地 | agent 读 diff 输出,按本手册 playbook 起草 |

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

**本地 cron 参考行(diff 退出码 0=无/1=critical/2=warn/4=错误,只在前两者时通知)**:

```cron
17 3 * * *  cd /path/to/site && \
  python3 /path/to/seo-suite/scripts/monitor.py run --checks daily && \
  python3 /path/to/seo-suite/scripts/monitor.py diff --out .seo-monitor/alerts.json; \
  rc=$?; [ $rc -eq 1 -o $rc -eq 2 ] && \
  python3 /path/to/seo-suite/scripts/notify.py run --dir .seo-monitor \
    --alerts .seo-monitor/alerts.json --flush warn
23 4 * * 1  cd /path/to/site && python3 /path/to/seo-suite/scripts/monitor.py run --checks weekly && \
  python3 /path/to/seo-suite/scripts/monitor.py report --days 7 | mail -s "SEO 周报" you@example.com
```

**GSC 流量问的喂数方法**:monitor.py 不带任何 API key,GSC 数据靠导出文件。在 run 之前把你账号下的效果报告导出(全期或固定 28 天窗)存为 `.seo-monitor/gsc.csv`(列含 Query,Clicks,Impressions),cron 里可用你自己的凭据先拉取;文件缺失=流量问 skipped,不猜数。口径固定:同一数据源、同一窗口、同一过滤,口径一变基线作废。

**config.json 关键项(diff 与 notify 共读)**:

```json
{
  "site": "https://example.com", "market": "us", "key_pages": ["/", "/pricing"],
  "budget_minutes": 5,
  "cooldown_hours": {"critical": 12, "warn": 24, "info": 168},
  "thresholds": {"visibility_drop_pct": 30, "visibility_min_sample": 3,
                 "sitemap_urls_drop_pct": 15, "sitemap_min_sample": 20,
                 "gsc_clicks_drop_pct": 20, "gsc_min_clicks": 5,
                 "latency_increase_pct": 100, "latency_min_ms": 500,
                 "mixed_content_min": 3}
}
```

channels 里 webhook 留空时,notify.py 自动读 `SEO_MONITOR_SLACK_WEBHOOK` / `SEO_MONITOR_DISCORD_WEBHOOK` / `SEO_MONITOR_TG_TOKEN`+`SEO_MONITOR_TG_CHAT` / `SEO_MONITOR_SMTP_PASS` 环境变量(CI secrets 注入,明文不落盘)。

## 六、与套件现有监控件的分工

- 本手册+monitor.py = **站点级守护进程**:调度、快照存储(SQLite runs/snapshots/alerts 三表)、阈值判定、通知分级、周报。回答"今天有没有事"。
- [seo-drift-monitoring](seo-drift-monitoring.md) = **页面级漂移取证**:13 元素基线/17 规则对比、算法更新归因。monitor.py 报 `title_meta_drift` 或流量断崖后,转它做细粒度归因(diff 命中的项按其交叉路由走)。
- [alert-threshold-guide](alert-threshold-guide.md) = **阈值方法论**:分级定义、波动带/相对变化/事件型/连续触发四法、月度调校。monitor.py 的 thresholds/cooldown 参数就是它的工程化落地。
- [kpi-definitions](kpi-definitions.md) / [report-templates](report-templates.md) = 周报口径与对外模板;monitor.py report 的"趋势+告警汇总+建议 PR"是它们的机器底座,人写 stakeholder 报告时直接引用。
- 处罚/负面 SEO 处置在 [penalty-recovery](penalty-recovery.md)(monitor.py 只负责发现,不负责处置)。

## 来源

- 分层(日四问/周趋势)、四级告警、百分比阈值防疲劳、安全自动项 vs 人审边界:行业共识实践(crawlseo/iannuttall/claude-seo 等仓库深扫,详见 [seo-drift-monitoring](seo-drift-monitoring.md) 来源节),按本套件"不猜数/不炸渠道/人审不可逆动作"约束改写。
- budget/dry_run 参数形态参考本套件 geo-score 系脚本的预算纪律。

## 附:方法边界与第一周清单

**已知边界(不掩盖)**:
- 可见性抽查走 Bing HTML 端点,无 SLA、非官方索引数——它是"方向抽样"不是排名追踪;端点被拦/人机验证时该问记 blocked,不告警。要精确排名用自己的追踪工具数据。
- robots 姿态判定是近似(组内根路径 disallow 即视为 blocked),最终判断跑 `robots_posture.py` 全量。
- 网络层抓取失败单次只记 info,连续两次才升 warn——本机断网不该炸全站告警。
- sitemap 解析限 5000 loc/5 层 index,budget 耗尽时中止并记 budget_skipped,已解析部分照常入库。
- GSC 口径是"两次 run 之间导出文件的合计变化",不是严格的 7 日滚动;要严格口径请固定窗口导出。

**第一周上手清单**:
1. `monitor.py init --site URL --market XX`(关键页补进 config 的 key_pages);
2. 手动 `run --checks daily --dry-run` 看四问是否都能出数(gsc.csv 该喂就喂);
3. 正式 `run` 建基线,隔天再 `run` + `diff --format text` 验证零告警;
4. 配一个渠道的 webhook,用 `notify.py --dry-run` 演练路由;
5. 部署 cron/GH Actions,一周后拿 `report --days 7` 校准 thresholds 与 key_pages;
6. 每月按 [alert-threshold-guide](alert-threshold-guide.md) 第五节复盘 noise 率。
