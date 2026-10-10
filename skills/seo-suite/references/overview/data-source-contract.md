# 数据源合同表(全脚本)

> **Agent 调用任何脚本前,先查此表确认数据就绪。缺数据时走"降级"列的既定路径,绝不由模型编造数字或观测。**

本表覆盖 `scripts/` 全部 52 个实装脚本(2026-10-10 与源码逐一对勘;SKILL.md 第 3 节称 53,实为 52,见文末"发现的差异")。每行三列:

- **数据**:输入是什么、从哪来(GSC 导出 CSV / HTML 文件 / server log / URL 实时抓取 / 无输入纯本地)。
- **降级**:数据缺失时的既定动作,四种模式之一:
  - **① 等价替代**——换等价数据源或脚本重建同一问题域,输出必须标 `[est]`;
  - **② 部分执行**——继续跑,但截断/降级到有数据支撑的部分,并显式声明截断或 N/A;
  - **③ 停止并指名缺什么**——报错/警告并列出缺失数据,不产出误导性结果;
  - **④ 静默跳过可选增强**——该数据只影响可选项,核心功能照常。
- **反编造**:哪些数字绝不能估;真实数据 `[real]` vs 估算 `[est]` 的标注规则。

本套件不附带任何数据(见 SKILL.md 第 4 节):GSC/GA4/Ads 导出、排名追踪与外链工具导出、采样回答、server log 一律由用户自备;外部 API 需用户自己的 Key。跑任何吃数据的脚本前,可先跑 `doctor.py` 探测当前环境的数据凭证分层(T0 纯静态 → T3 GA4)。

---

## 一、审计与页面质量(14)

| 脚本 | 数据 | 降级 | 反编造 |
|---|---|---|---|
| `site_audit.py` | URL 实时抓取(HTML+HTTP 头);`--market` 阈值读本地 markets.json | ② 抓取异常→CRITICAL fetch 错误;WAF/挑战页→`[SKIP]` fetch guard 拒审,不算 CRITICAL、不进分母 | 只断言实际抓到的静态 HTML 证据;不测渲染,JS 注入内容缺失时不得推断"页面无内容" |
| `health_score.py` | 本地 JSON(site_audit `--json` 输出);`--config` 可选 | ② 缺数据源的类→N/A(`data_source_missing`)不计入合成分;refused/SKIP URL 不进分母、单列 | N/A 类绝不给分;恒带 coverage 注记:分数基于爬取样本,两次分数不可直接比 |
| `traffic_funnel.py` | `--audit`(site_audit JSON)+`--gsc`(GSC 页面导出 CSV)+`--cwv`(可选 CSV)+`--urls`(sitemap 清单) | ② 无 GSC→漏斗截断到 uniqueness 并输出截断声明(in_serps/with_clicks/good_ux=null);缺 CWV→good_ux N/A 不计入;仅 `--urls`→只做可达性抽测 | null 阶段绝不算比例;样本<全站时 coverage_ratio 必须显式输出 |
| `quality_rater.py` | 纯文本文件(本地;首行=title 约定);`--keyword`/`--market` 可选 | ② 无 `--keyword`→按词频自动推断主词(输出注明是推断) | 分数只基于给定文本;纯文本近似,不宣称覆盖视觉/渲染质量 |
| `above_fold.py` | URL 实时抓取(前 700 字符可见文本) | ③ 抓取失败→exit 2,不评分 | "首屏文本"是渲染首屏的保守近似(无布局引擎);输出不得宣称真实渲染布局结论 |
| `trust_signals.py` | URL 实时抓取 | ③ 抓取失败→exit 2 | 四维只认文本证据;静态未检出≠页面没有证言(可能在图片/JS 中),报告须注明口径 |
| `core_eeat.py` | 纯文本/Markdown 文件(本地) | ② 不可机判项(如"≥3 查询变体")固定记 na,离开分母 | na 不稀释分母;不把"未检出"当"不存在";veto 命中封顶 59 只对显式标记 |
| `content_score.py` | `--draft` 本地文件 + `--competitors` ≥3 个竞品文件 + `--keyword`;术语表从竞品正文提取 | ③ 竞品 <3 个不同来源(按内容哈希去重)→拒绝评分 exit 2(Surfer 官方规则) | 无竞品绝不出分;术语与重要度全部来自竞品语料共现,不引入外部臆测词表 |
| `fix_plan.py` | `--url`(内部跑 site_audit 实时抓取)或 `--audit` JSON | ③ 审计失败(fetch guard SKIP)→不生成任何修复物 exit 2 | 修复物只基于审计 findings;content 类只出提纲不自动重写;默认 dry-run,`--apply` 只写隔离目录 ./seo-fixes/ |
| `grounding_page.py` | brand.yaml(Brand Records 事实库,用户提供);`--check` 校验已有页 | ③ 无 facts 文件→无法生成;② facts 缺消歧记录→生成占位注释提示人工填 | 只重组 YAML 内的已验证事实,绝不新增/改写事实;FAQPage JSON-LD 不生成(2026-05 富结果退役) |
| `audit_compare.py` | 两次 site_audit `--json`(本地文件) | ③ 缺任一文件→exit 2;② canonical 等字段两侧皆缺→该字段跳过对比 | 两期 URL 样本不同时必须输出 coverage_ratio,不得直接断言"分数升降" |
| `prioritize.py` | `--audit`(site_audit JSON,逐页)或 health_score JSON(摘要);gsc_clicks/inlinks 等扩展键可选 | ② 摘要输入→条件依赖型规则降级;缺 GSC 上下文→未索引按中优先级并降级标注;canonical 缺 PageRank 数据→标"需人工判定" | 缺数据一律标"需人工判定",不给定论;两栏排序只基于命中的真实 finding |
| `changelog.py` | `--db`(monitor.py SQLite,读 snapshots 表)或 `--snaps` JSON,二选一 | ③ 两者皆缺→exit 2;② 仅 2xx 快照参与 diff(4xx/5xx 页字段不可信) | 只报白名单字段的真实 diff;事件流不含推测;与 gsc_mining `--decay` 联动定位衰退起点 |
| `forecast.py` | `--kws` 关键词 CSV(词+search_volume+position[+cpc]);`--ctr` 自有 GSC 曲线、`--actual` 校准流量均可选 | ② 无 `--ctr`→内置行业默认曲线,全输出标 `[est]`;无 cpc 列→acquisition_value/等效付费成本=N/A;>30 位的词不预测 | **Never invent search volumes**——kws.csv 无量不猜;CTR 模型默认是行业 benchmark `[est]`(官方建议换自有 GSC 90 天非品牌曲线 `[real]`);orders/value 是情景推演非承诺 |

## 二、技术 SEO(7)

| 脚本 | 数据 | 降级 | 反编造 |
|---|---|---|---|
| `sitemap_audit.py` | sitemap URL 实时抓取(sitemapindex 递归 1 层;逐 loc 抽查状态码/标签) | ③ 入口不可达→报错指名;② `--check-limit` 限定抽查数,结论只覆盖抽查样本 | 六坏桶只报实测状态码/标签;不推测未抽查 URL 的健康;lastmod 伪造只按三判定的显式证据 |
| `hreflang_cluster.py` | 多个 URL 实时抓取(HTML link 标签+HTTP Link 头+sitemap XML 三载体) | ② 未作为入参的 alternate 自动补抓(`--max-extra` 上限,超限标"未验证") | 只判实际抓到的声明;单条 return tag 断裂=整簇不生效(官方口径),不猜"部分生效" |
| `redirect_chain.py` | URL 实时逐跳 GET(手动跟随不自动重定向) | ③ 网络错误→exit 2 | 只报实测跳数/状态码/参数保留;301 建议来自规则映射,不虚构"权重损失数值" |
| `robots_posture.py` | robots.txt 实时抓取;27 bot 三层名单+RFC 9309 解析器内置本地 | ③ robots.txt 不可达→报错不判 posture | 四态判定只基于文件内容;通配符 Allow 只拿部分分(两级评分),不夸大为"已放行";`--fix-robots` 只打印不写盘 |
| `llmstxt.py` | validate=本地文件;check=线上 /llms.txt 等 4 路径探测;generate=--sitemap 实时抓取 | ③ check 探测不到→逐路径打 ✗ 与异常名(不猜"平台不支持");generate 抓取失败→exit 非 0 | 生成骨架只含 sitemap 实际 URL,不发明条目;check 发现返回 HTML 而非 Markdown 判 FAIL |
| `schema_lint.py` | URL 实时抓取(提取全部 ld+json 块) | ③ 抓取失败→exit 非 0 | 只对静态 HTML 内的 JSON-LD 断言(@id/悬空引用/占位符);静态未检出≠页面无 schema——渲染后可能注入,需渲染证据复核(SKILL.md 特别约束) |
| `head_check.py` | URL 实时抓取或本地 HTML 文件;`--market zh` 门控中文项 | ③ 抓取失败→exit 2;④ 非 zh 市场且页面无汉字→微信/QQ itemprop 检查跳过(消跨市场噪音) | charset>1024B/弃用 meta 命中只按文档口径断言;微信/QQ 读 itemprop 是平台文档行为,不虚构浏览器实测 |

## 三、关键词与 SERP(7)

| 脚本 | 数据 | 降级 | 反编造 |
|---|---|---|---|
| `gsc_mining.py` | GSC 导出 CSV(Query,Clicks,Impressions,CTR,Position;matrix 模式加 Page;`--decay` 需当前+前一期两文件) | ③ 脚本侧:无导出文件不可跑;**agent 层等价替代①**:无 GSC 时改用 `serp_overlap.py` 对 SERP 抓取样(逐词 top10 URL)做蚕食/同源判断,结论标 `[est]` | **Never invent search volumes**——clicks/impressions/position 全部来自 CSV,脚本不代查 GSC;期望 CTR 曲线是行业锚点(与 forecast DEFAULT_CTR 同源),低 CTR 判定基于该模型 `[est]`;列名宽容匹配、缺值按 0,调用前自查列齐全(见文末差异) |
| `serp_overlap.py` | 输入 CSV(keyword,top10 URL 分号分隔)——SERP 数据须用户提供(自抓取样或 rank tracker 导出) | ③ 无 CSV→exit 2 | Jaccard 只对给定 URL 集合计算,不虚构 SERP 结果;四档判据(7-10/4-6/2-3/0-1)是解读层,数据必须真实 |
| `keyword_variants.py` | stdin 每行一词(无输入纯本地归一) | ④ 无输入→空输出 | 归组=Unicode 归一链结果;越南有调/无调归组时显式提示"意图不同,排名当独立词跟踪",不合并了事 |
| `payment_intent.py` | stdin 关键词 + markets.json payment_words 词表(本地) | ④ 词未命中→无标签(不是"零商业意图") | 只标词表显式命中(OXXO/cuotas/Pix/COD…);不臆测未命中词的支付意图 |
| `geo_difficulty.py` | `--kd`/`--ur-median`/`--targeting` 手工输入——KD 来自第三方 SEO 工具导出,UR 来自竞品页审计 | ③ 缺必填参数→exit 2;② 无 `--position`/`--client-ur`→只出绝对难度分,不出客户三档 | KD/UR 必须来自真实工具导出,脚本不代查;分数公式透明,输入值须标注来源工具 |
| `serp_occupancy.py` | `--market` + 域名列表(argv/stdin,来自用户 SERP 观测);对照 markets.json 内置占位表(tr/th/in/kr/jp/vn/ru) | ③ 未知市场→exit 并列出可用市场 | 只对提供的域名计数;内置占位表是市场层知识(哪些平台通常霸位),不虚构"某域当前占位"的事实 |
| `grid_rank.py` | rank_data.csv(keyword,grid_point,rank)——本地网格排名采集结果(如 Text Search API 手工导出) | ② rank 留空/null→该格未找到;rank>20→视同未找到并告警(21 惩罚);全未命中→ARP=null 而 ATRP 永不 null;盲区=ATRP−ARP 必同报 | 只算采集到的格点,不补测不外推;复测须同网格同词表同半径,否则不比 |

## 四、多语言(4)

| 脚本 | 数据 | 降级 | 反编造 |
|---|---|---|---|
| `market_lint.py` | `--market` + 本地文本文件;64 条规则读 markets.json(本地) | ③ 未知市场→exit 并列出 18 个可用市场 | 机检三态 [AUTO-OK]/[AUTO-FAIL]/[MANUAL] 分明;不可机检项以 [MANUAL] 前缀列人工清单,绝不把 MANUAL 当 PASS |
| `local_format.py` | `--market` + 采样文本(argv/stdin);惯例表读 markets.json | ③ 缺 `--market`→exit 2 | 只对给定文本逐条 ✓/✗;电话前缀错配仅提示 ⚠ 不判错 |
| `text_metrics.py` | stdin 文本(本地) | ④ 无输入→空;`--scrub` 输出净化版到 stdout | 水印/slop/AI 节奏是**特征密度**检测,"检出"≠"AI 生成"结论;CJK 词数口径显式声明 |
| `text_units.py` | `<market>` + stdin 文本(本地;en/zh/ja/th/ko/ru/id) | ③ 未知 market→exit 2 | 换算是确定性计算;全角=1/半角=0.5、泰文按字素的口径在输出中显式 |

## 五、GEO 可见性(6)

| 脚本 | 数据 | 降级 | 反编造 |
|---|---|---|---|
| `citation_panel.py` | init 建 prompt 面板(本地);record 录入**人工采样的真实引擎回答**;report/diff/decay 基于累积 panel.json | ② prompts<10→"样本太小,结论只能当方向";单 prompt 采样 <3 次→不下结论(CI 跨 0.5→unstable);空分母→N/A;decay 观察窗不足→半衰期用官方中位 11 天作参照并标 `[est]` | **绝不生成"模拟引擎回答"**——面板里的每条回答必须真实采样粘贴;五状态边界分明(failed≠brand_absent:采集失败不是内容缺口);diff 报告 |Δ|≥5pp 且配对 n≥10 才下结论 |
| `fanout_analysis.py` | 输入 CSV(prompt,web_query)——来自 AI 平台 referral 查询或 fan-out 采集导出 | ③ 无 CSV→exit 2 | 三桶(added/dropped/preserved)只对给定查询对分词;不虚构 fan-out 序列 |
| `ai_referral_log.py` | server access log(apache/nginx combined 或 JSON 行,stdin/文件) | ③ 无日志→无法运行;② 日志缺 referrer→计入无 referrer 桶并声明;④ `--bot-ua` 先行指标可选 | **下界口径**:App 内打开常不带 referrer,测得值是下界,绝不表述为 AI 引流总量;failure_rate 只按日志内状态码计算 |
| `citation_gaps.py` | `--panel`(citation_panel 的 panel.json)+`--brand-domains` | ② panel 无竞品名单→以"同 cell 共同被引的其他非自有域"代理竞品并标 [推断];failed/no_answer 不入缺口 | 采集失败≠内容缺口;竞品判定是代理推断,报告必须注明;has_competitor_run 是唯一高优先判据 |
| `oracle_check.py` | `--facts` brand.yaml(已验证品牌事实)+`--responses` responses.json(真实采样回答) | ③ 已验证 facts<25 条→警告"样本不足,结论置信低"并继续(置信降级,报告必须带警告);responses 空→警告无可核查;语义级矛盾不由脚本判,交 agent 复核 | 只判显式数字/日期/布尔冲突(正则近似);possible sources 一律留空由 agent 调查后填——不臆造错误来源归因 |
| `cite_domain.py` | `--input` answers.json(referring_domains/DR 分布/锚文本等结构化观测,来自外链工具导出+人工观测) | ② 未观测字段=unknown 不计组内均值;某组全 unknown→该组权重按比例重分配到已知组 | unknown 绝不当 0 分(没观测≠零分);veto BLOCK 只对显式命中(manual_penalty 等) |

## 六、监控与 CI(5)

| 脚本 | 数据 | 降级 | 反编造 |
|---|---|---|---|
| `monitor.py` | `--site` URL 实时探测(robots/sitemap/状态码/site: 抽查)+ `.seo-monitor/gsc.csv`(GSC 导出,有才查)+ SQLite 本地快照 | ④ 无 gsc.csv→流量问 skipped 不告警、不猜数;site: 被拦/人机验证→blocked 不告警;DOM 改版解析失败→unparseable 不当真 0;canonical HEAD 失败→连续 3 次才告警;`--budget-minutes` 耗尽→budget_skipped | skipped/blocked 状态绝不转成数字进快照;prev 无数据→下降比例返回 None(不猜);low=自愈只进报告 |
| `notify.py` | monitor diff 的告警 JSON + config.json 渠道定义(secret 只经环境变量注入) | ④ 渠道未配置→跳过并报告;low 级静默只进报告;冷却期重复指纹→suppressed 只进报告;未知/过期 key→提示跳过不判错 | 不投递不存在的告警;明文 secret 被 monitor 拒写,绝不回显值 |
| `sensor_volatility.py` | `--gsc`(GSC 多日导出,列含 Date/Query/Position)或 `--positions` 三列 CSV | ③ 单日数据→exit 2(无法算波动);缺列→exit 2;② 基线 <2 天或 std=0→z30=null;GSC 缺日→与最近可用日比(标 [推断]) | 波动分只来自真实排名序列;公式是自研口径对齐 Semrush 分档(源码注释声明),不冒充官方公式;z30 null 时不标"异常日" |
| `ci_format.py` | 本地 JSON(site_audit `--json` 或 audit_compare `--json` diff) | ③ 输入错误→exit 2 | 格式化不判成败(门禁交给 min-score/baseline-gate);分数透传不重算;helpUri 只在有真实文档 URL 时加;github 注解每 URL 至多 10 行防刷屏 |
| `doctor.py` | 无外部数据——本地环境探测(Python 版本/文件/环境变量**键名**;`--net` 可选 HEAD 探测) | ② 无任何凭证→T0 纯静态审计可用,missing 列出"配置 X 可解锁 Y";网络探测失败只警告不影响 ready(exit 0=ready/3=需处理) | 只探键名**不读值**,全输出过 redact;报告按 tier 自动声明数据覆盖范围——T0 时绝不暗示能出 GSC/GA4 结论 |

## 七、工作流(9:归因·管道·套件自维护)

| 脚本 | 数据 | 降级 | 反编造 |
|---|---|---|---|
| `did_attribution.py` | GSC 页面级两期 CSV(`--pre`/`--post`:Page,Clicks[,Date])+ treated/control 页分组 | ② 控制页 <3 或控制组 pre 点击 <5→自动回退 site 级对照并注明;③ treated pre 点击 <5→exit 2"基线流量不足以归因";controlBefore≤0→结果 null | DiD 是**观测估计不是因果**——server-side A/B 才是真因果检验,报告必须声明;窗口与 GSC 断代期(2025-05-13~2026-04-30)重叠→impressions 不可靠警告 |
| `seo_vs_ads.py` | `--gsc`(GSC queries 导出)+ `--ads`(Google Ads search terms 导出,可选)+ `--competitors` 列表(可选) | ② 缺 Ads 侧→明确列出缺什么,只输出 GSC 侧概览,organic_only 桶不定义、不猜;defensible 桶无 `--competitors`→明说跳过 | 自己的 search terms 报告**看不到竞对竞价**——double_paying 判 HIGH 时注明需 auction insights 复核;省额是 50%~70% 保留率**估算区间**非实测 |
| `yt_outlier.py` | videos.csv(title,duration_s,views[,is_short][,channel])——YouTube 导出/采集 | ③ 文件/格式错误→exit 2 | 离群=组内均值 2×(频道×形态分基线,长短分开);只统计 CSV 内真实播放量,标题词频只对离群标题计算 |
| `trend_scout.py` | HN topstories API + Reddit 6 sub hot(免 key 实时抓取);X/Twitter 需 key | ④ X/Twitter 无 key→明说跳过不猜;② 单源失败→warn 明说;③ 全源失败/无数据→exit 2 | 白名单门槛:HN+Reddit 相关条目合计 ≥15 才建议立项;相关性分只对 `--vertical` 词命中,不硬凑 |
| `freshness.py` | 本地 *.md 头部日期标记(默认 references/) | ④ 文件无日期标记→按新鲜处理,不计 stale | 只读显式日期标记(Updated/verified_at/建于/复核于);不推测文件实际年龄;未来日期=error |
| `report_build.py` | findings.json(上游脚本产出或 agent 组装) | ② summary>2500 字符→截断并警告;findings>20 条→警告"失败报告"并截断到 20 | 只渲染输入 findings,不补写结论;禁 script/外部资源;数字同时印在文字里,不靠图形暗示 |
| `self_check.py` | 本地 skill 文件(frontmatter/模板七段式/死链/golden 测试) | ③ 任一项失败→exit 1 | 工具脚本,无外部数据 |
| `link_check.py` | 本地 markdown 文件树 | ③ 断链→exit 1 | 工具脚本,无外部数据 |
| `intel_check.py` | intel-sources.md 注册的 18 源实时拉取(RSS/hash)+ `.intel-state.json` 基线 | ③ 无基线→先 init;② hash 源二次确认:两次拉取不一致(动态页噪音)→按噪音跳过、不动基线;单源失败→明说 | 变更判定需两次拉取一致才算真变更;噪音不报变更;只输出"源变了→该更新哪些文件",不自动改 |

---

## 全局守则(四条,一切脚本与报告通用)

1. **真实数据优先于估算。** 凡能拿到站点自有数据(GSC 导出、server log、真实采样回答、工具导出),一律先用;行业默认曲线/官方参照常数只在自有数据缺席时顶位,且不覆盖、不冒充实测。
2. **估算必须打 `[est]` 标。** 一切非实测数字——内置 CTR 曲线、半衰期参照值、省额区间、代理竞品口径——在输出中逐个带 `[est]`;关键结论数字可用 `[real]` 明示为实测来源。混标或漏标即违规。
3. **Tool availability can vary;每个脚本声明了自己的 fallback。** 外部工具、导出文件、API 凭据的可用性因环境而异——缺什么看本表"降级列"按 ①②③④ 四模式处理,而不是换个数字继续算。
4. **不拿第三方估算冒充站点自有数据。** 行业基准 KD、默认 CTR、市场占位表、工具 DR 分布是第三方口径;报告里必须与站点实测分列并标注来源,绝不混写为"我们的数据"。

## 发现的差异(文档 vs 实现,以实现为准)

1. **SKILL.md 第 3 节标题写"53 个实装脚本",实际 `scripts/` 共 52 个 .py 文件**;SKILL.md 正文点名的脚本去重后恰为 52(与文件一一对应)。本表覆盖全部 52 个;主会话如修正 SKILL.md 计数请同步。
2. **gsc_mining.py 没有"缺列报错"路径**:列名按前缀+大小写宽容匹配,缺值按 0 参与计算——若 CSV 缺 Clicks/Position 列,脚本会静默跑完而非显式失败。调用前须人工确认列齐全(本表数据列已注明必需列)。
3. 任务口径中的"gsc_mining 无 GSC→serp_overlap 替代标 `[est]`"是 **agent 层等价替代策略**(模式①);gsc_mining 脚本本身无内建降级(无文件即 usage error exit 2)。本表按"脚本侧 ③ + agent 层 ①"双写。
4. **oracle_check.py 的 25 条 facts 门槛是"警告置信低并继续输出"**,并非硬停止——按实现写为模式 ③ 的警告变体(执行继续、置信降级、报告必须携带警告原文)。
5. 其余抽查脚本(traffic_funnel/forecast/health_score/prioritize/monitor/seo_vs_ads/sensor_volatility/did_attribution/trend_scout/content_score/grid_rank/citation_gaps/citation_panel/doctor/notify 共 15 个)的降级行为与 SKILL.md 第 3 节描述一致,未发现文档与实现不符。
