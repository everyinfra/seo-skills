# 首次真实部署验证(2026-10-11)

> 完善度第 4 项"真实部署"的第一轮:套件对真实目标端到端跑通,**发现并修复了 2 个只有真实跑才能暴露的问题**。本文件是部署日志,后续每轮追加。

## ① 热点管线(trend_watch)——真实网络 ✅

- `watch --market en`(真实拉取):25 条真实信号;Google News 返回当日 GEO 热点(相关性最高 175 分 "8 Best GEO Tools"/75 分 "2026 GEO & AEO Survey");Reddit rising 403 按设计整源跳过告警;HN 无关项被 Q1 闸门正确 drop(Q1=0)
- `gate` 对最高相关信号跑四问闸门:Q1 75 分 PASS / Q2 七个净新观点 PASS / Q3 NEWS 窗口(0h)/ Q4 exclusive=data → **判定 GO(News 型):24h 内发,news sitemap 48h 窗口**;决策件见 `skills/seo-suite/examples/trend-gate-geo-survey-20261011/`
- **真实发现**:角度文件必须用 playbook 2.2 的编号行格式(`| 1 | …`),无编号表会被 Q2 计为 0——格式约定比直觉严格,已在示例中固化正确写法

## ② 自审计(site_audit 对 github.com/everyinfra/seo-skills)✅ 抓到真问题

- **AI Search Health 85/100**(bots ✓/llms.txt ✓/freshness ✓/BLUF ✓;semantic_html 2.6% 未过——GitHub 模板页固有)
- **真实发现:仓库 description 数字过期**("38 built-in scripts + 71 golden tests",实际 56/672)且 304 字符超限 → 已用 `gh repo edit` 更新为当前口径——**我们的工具审出了我们自己的营销元数据过期**
- title 304 字符/description 287/链接 201 条/schema 缺失均为 GitHub 页面模板固有,记录不修(非我们可控)

## ③ 监控闭环(monitor 对真实站点)✅ 抓到真实瞬态

- init+run#1(30.9s 基线)+run#2+diff+report 全链通过
- **真实事件被抓到**:run#1 时 `/blob/main/README.md` 返回 GitHub 故障页(h1="We're having a really bad day."、正文 37 词);run#2 恢复(3620 词)→ diff 正确产出 h1_changed/main_content_change(+9684%)/title_meta_drift 三条 INFO+draft_pr 处置建议,**没有误报 CRITICAL**——P2 的 removed/字数漂移机制在真实瞬态上表现正确
- latency_spike 2886→7272ms(+152%)同样被抓到
- 诚实降级:gsc 未配置→跳过不猜数;visibility 注明"非官方索引数,仅方向"

## ④ GitHub Actions 云端 ✅ 发现→修复→复跑绿

- **intel-update 定时任务已在云端真实运转**(2026-10-11 07:08 UTC 自动触发),且**真实检出了信源变更**(google-blog/ard-spec/seroundtable,10 个受影响文件,任务文件正确生成)
- **真实 bug**:提交步骤 `git add` 含被 .gitignore 忽略的 `.intel-state.json`,bash -e 下退出码 1 → job 失败。修复:只提交任务文件(状态本就由 actions/cache 持久化)。修复推送后 workflow_dispatch 复跑 → **success(1m3s)**
- capability-drift job 云端通过(能力矩阵 8 测试);seo-monitor 按预期 skip(未配 SITE_URL)

## ⑤ 品牌采样面板(citation_panel)✅ 建好待采样

- init:EveryInfra / github.com/everyinfra/seo-skills,10 条真实 prompt(5 觉醒+3 比较+2 决策),6 引擎;stage-mix 提示正确输出
- **边界(如实)**:AI 引擎的实际采样需要人在各引擎提问或配 API——脚本只提供面板与校验;下一步按 prompt-bank 纪律每 prompt 采样 3 次取多数

## 结论与下一步

- 端到端全链(热点→审计→监控→云端自更新)首次在真实环境闭环,**2 个真实缺陷被当场揪出并修复**(git add 忽略路径/workflow 失败;角度格式约定)
- **补录(同日)**:④已完成——设 SEO_SITES 仓库变量指向真实目标;monitor job 的模板守卫(排除本仓库)改为 vars.SEO_SITES 门控(模板用户未配置仍跳过),workflow_dispatch 复跑 **success(12s,云端基线建立)**;至此 intel-update/seo-monitor/capability-drift/envelope-report 四工作流全部云端在跑
- 下一步:①按 GO 判定的 brief 真实写发那篇 GEO survey 分析文(走 deep-research-protocol+pre-publish 32 条闸)②每 3 小时挂 trend_watch cron ③监控跑满 4 周后用 citation_panel decay 验证半衰期双口径
- 遗留小项:intel-update 任务文件头 "Generated: \${TIMESTAMP}" 未展开(heredoc 引号问题,纯装饰不影响功能)
