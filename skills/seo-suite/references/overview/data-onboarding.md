# 数据接入指南(我想做 X 分析 → 需要什么数据)

> **本文是用户视角的"分析目标 → 数据源"对照:先想清楚要做什么分析,再对照备数据。
> 脚本视角的逐脚本合同(每脚本的数据/降级/反编造)见 [数据源合同表](data-source-contract.md),
> 两表口径一一衔接:本表"没有时降级成什么"列就是合同表降级列的用户侧摘要,
> 缺数据走既定降级路径,绝不由模型编造数字或观测。**
> 探测当前环境配了哪些凭证:`python3 scripts/doctor.py --wizard [--want seo-audit,rank,…]`
> ——非交互清单,逐项给出 数据源/是否已配/获取锚点/降级路径;零网络、只看键名存在性、绝不读值。建于 2026-10-11,2026-10-21 重核。

## 一、分析目标 → 数据源矩阵

| 分析目标 | 数据源(费用) | 获取方式(一句话,具体到页面/路径) | 没有时降级成什么(合同表口径) |
|---|---|---|---|
| <a id="want-seo-audit"></a>全站体检 | site_crawl+site_audit 实时抓取(免费·零数据门槛) | 无需备数据:`site_crawl.py example.com` → `site_audit.py` → `health_score.py` 现即可跑 | 本就是零门槛入口;WAF/挑战页按 [SKIP] 拒审,不算 CRITICAL、不进分母 |
| <a id="want-cwv"></a>CWV 现场数据 | CrUX API(免费,必须 key)与 PSI API(免费,key 可选);PSI 文档写明计划停止返回 CrUX 现场数据,长期以 CrUX API 为准 | Google Cloud 控制台 → 凭据 → API 密钥,启用 Chrome UX Report API(要用 PSI 实验数据再启用 PageSpeed Insights API);`export CRUX_API_KEY=…`、`export PSI_API_KEY=…`(约 5 分钟) | 无 key:`field_data.py` 只跑 PSI 并告警;或用 PSI 网页版逐页手查再导出;traffic_funnel 缺 CWV 时 good_ux=N/A 不计入漏斗 |
| <a id="want-rank"></a>排名与点击 | GSC(免费:导出 CSV 零门槛;API 用服务账号) | Search Console → 效果(Performance)→ 导出 CSV(查询/页面两表;搜索类型可选 Web 文本、Web multimodal、图片、视频、新闻);API 自动化:`gsc_api.py` + 服务账号 JSON,放 ~/.config/seo-suite/gsc.json,并把服务账号邮箱加为该属性的用户 | 蚕食/同源判断改用 serp_overlap 对 SERP 抓取样做,结论标 [est];monitor 无 gsc.csv 则流量问 skipped 不猜数 |
| 流量与转化 | GA4(免费) | GA4 报告导出 CSV。本套件**没有**脚本通过 GA4 Data API 拉数;gsc.json 里的 `ga4_property_id` 键只让 `doctor.py` 报 T3 徽章 | 转化侧只能声明 N/A;ai_referral_log `--attribution` 仍可产出 GA4 正则与归因纪律供手工配置 |
| <a id="want-keywords"></a>关键词搜索量 | Keyword Planner(需 Google Ads 账号,基础功能要先完成账号设置并填账单信息)或 Ahrefs/Semrush/DataForSEO(付费) | Google Ads → 工具 → 关键字规划师导出量级;付费工具导 kws.csv(词+search_volume+position[+cpc]) | Never invent search volumes:forecast 对无量词不预测(缺列 N/A);不同工具的量级不同,用区间不用点值,并注明来源工具 |
| <a id="want-backlinks"></a>外链画像 | Ahrefs/Semrush 导出(付费)或 GSC 链接报告(免费,覆盖不全) | 付费工具导 referring_domains/DR 分布/锚文本喂 cite_domain;GSC → 链接(Links)报告可出部分画像 | cite_domain 未观测字段=unknown 不当 0;竞品被引用 citation_gaps 同 cell 共同被引代理并标 [推断] |
| 竞品排名与 SERP | SERP API 如 serper.dev(付费,首个付费包 $50 买 50,000 credits,约 $1.00/1k 次查询,大包降到约 $0.30/1k) | 注册充值后逐词抓 top10,拼 `keyword,top10(分号分隔)` CSV 喂 serp_overlap | 无 API 时人工抽词查 SERP 手工录 top10;serp_overlap 无 CSV 即 exit 2,绝不虚构 SERP |
| <a id="want-geo"></a>AI 可见性(GEO) | citation_panel 人工采样(免费·零门槛)或厂商面板(付费) | `citation_panel init` 建 prompt 面板 → 各引擎真实提问 → `record` 粘贴真实回答(严禁生成模拟回答) | 采样 <3 次不下结论;面板 <10 prompts 只当方向性参考(本套件口径);GSC「生成式 AI 效果报告」(AI Overviews + AI Mode 的展示数,维度为页面/国家/日期/设备)和 Bing Webmaster Tools 的 AI Performance 可作第一方佐证 |
| <a id="want-logs"></a>日志分析(AI 到访) | server access log(自带导出) | 从主机/CDN(Nginx/Cloudflare/AWS)拉 access log(combined 或 JSON 行)喂 ai_referral_log | 无日志则 AI 到访只能靠探针+GSC AI 报告侧写;日志口径本就是下界(App 内打开常不带 referrer) |
| <a id="want-local"></a>本地商家 | Google Business Profile(免费,自带导出) | GBP 商家后台读绩效/导 CSV;网格排名用 Text Search API 手工采集 rank_data.csv(keyword,grid_point,rank) | grid_rank 无 CSV 不可跑(不补测不外推);GBP 无导出项则后台人工读数并在报告注明口径 |
| 排名波动与算法归因 | GSC 多日导出(免费) | GSC 效果报告按日期分段导出(列含 Date/Query/Position)喂 sensor_volatility | 单日数据 exit 2(无法算波动);z30 null 时不标"异常日";Core Update 滚动期不跑,沉淀 7-14 天再判 |
| 改版/投放归因(DiD) | GSC 页面级两期 CSV(免费) | 改版/投放前后各导一次页面级 CSV(Page,Clicks[,Date])喂 did_attribution | 控制页 <3 或控制组基线点击 <5 自动回退 site 级对照并注明;treated 基线不足 exit 2 |

## 二、凭证阶梯 T0 → T4

探测当前在哪一级:跑 `doctor.py`(或 `--wizard`)——tier 与能力徽章即时可见;升级判断只看键名存在性,不读值。

| 级别 | 门槛与成本 | 解锁什么(脚本级) | doctor 徽章 |
|---|---|---|---|
| T0 | 零凭证,零成本 | 全部静态/抓取/本地能力(七组,见下) | static-audit |
| T1 | 免费 key,约 5 分钟 | CWV 现场数据拉取 → traffic_funnel good_ux 段 | psi / crux |
| T2 | 免费:CSV 导出零门槛;API 走 OAuth | GSC 六件套(见下) | gsc |
| T3 | 免费:gsc.json 加 `ga4_property_id` 键(`doctor.py` 显示 T3 徽章;本套件暂无脚本调 GA4 Data API,GA4 数据用导出文件喂) | 流量与转化侧 + AI Assistant 通道归因 | ga4 |
| T4 | 按量计费(先报价) | 竞品 SERP / 搜索量 KD / 外链结构化观测 | (无徽章,自备导出) |

**决策顺序:先跑 T0 全站体检,再按体检结论决定配哪一级**——地基没过的站,先修基座再谈数据采买。
`doctor.py` 人读模式报 tier 与升级指引;`doctor.py --wizard` 另给逐分析目标的就绪清单(本文锚点)。

- **T0 零凭证(现在就能跑)**——纯静态/实时抓取/本地能力,分七组:
  - 全站体检链:site_crawl / site_audit / health_score / prioritize / envelope / audit_compare / benchmark_report
  - 单页与内容:above_fold / trust_signals / core_eeat / quality_rater / content_score(竞品文件自备)/ fix_plan(dry-run)
  - 技术七件:robots_posture / llmstxt / schema_lint / head_check / sitemap_audit / redirect_chain / hreflang_cluster
  - 多语言组:market_lint / local_format / text_metrics / text_units / keyword_variants / payment_intent / serp_occupancy
  - GEO 采样:citation_panel(人工采样零门槛)/ oracle_check / citation_gaps(面板与 brand.yaml 自备)
  - 监控:monitor(无 gsc.csv 则流量问 skipped)/ notify;trend_scout 的 HN+Reddit 段免 key
  - 工具:doctor / report_build / changelog(读 monitor.db)/ freshness / self_check
- **T1 PSI/CrUX key(免费,约 5 分钟)**
  - 在哪申请:Google Cloud 控制台 → API 和服务 → 凭据 → 创建凭据 → API 密钥。CrUX API 要求为「Chrome UX Report API」开通的 key([CrUX API 文档](https://developer.chrome.com/docs/crux/api),页面日期 2026-10-13,核对 2026-10-21);PSI API 可以不带 key 调用,频繁或自动化调用才建议加 key([PSI 入门](https://developers.google.com/speed/docs/insights/v5/get-started),页面日期 2025-08-28)。同一个 key 可同时启用两个 API。
  - 限额:CrUX API 每个 Google Cloud 项目 150 次/分钟,免费([CrUX API 文档](https://developer.chrome.com/docs/crux/api))。CrUX History API 与日常 API 用同一个 key;它每周一更新,保留最近 40 周数据,默认返回 25 个采集期([CrUX History API 文档](https://developer.chrome.com/docs/crux/history-api),页面日期 2025-04-11)。PSI 的限额以你 Cloud 控制台「配额」页显示为准。
  - 口径变化:PSI 文档写明「计划停止在该 API 中提供 CrUX 现场数据,建议改用 CrUX API 或 CrUX History API」([PSI 入门](https://developers.google.com/speed/docs/insights/v5/get-started))。所以现场数据(LCP/INP/CLS 的 p75)以 CrUX API 为主,PSI 只取 Lighthouse 实验数据。
  - 怎么配:`export PSI_API_KEY=…`(CrUX 用 `CRUX_API_KEY`;`field_data.py` 在没有 `CRUX_API_KEY` 时回退用 `PSI_API_KEY`),写进 shell profile 或密钥管理器,不进 git
  - 解锁什么:CWV 现场数据拉取 → `field_data.py --as-cwv-csv` 生成 CSV 喂 traffic_funnel `--cwv`(good_ux 段);doctor 徽章 psi/crux
- **T2 GSC(免费:导出 CSV 零门槛;API 走服务账号)**
  - 导出路径(零门槛):Search Console → 效果 → 导出;链接报告 → 链接(Links)。新的搜索类型过滤器含「Web: multimodal」(2026-09-24 起,[博文](https://developers.google.com/search/blog/2026/09/web-multimodal-in-sc))。
  - API 自动化:`gsc_api.py` 用**服务账号** JSON(RS256 签名),不是用户 OAuth 弹窗。凭证放 ~/.config/seo-suite/gsc.json(服务账号原生 JSON,或包一层 `credentials` 键),doctor 徽章 gsc。先 `python3 scripts/gsc_api.py auth`,再 `sites` 看有权限的属性,再 `query`。
  - API 限额(Search Analytics,[Usage Limits](https://developers.google.com/webmaster-tools/limits),页面日期 2025-08-28,核对 2026-10-21):每个站点 1,200 次/分钟,每个用户 1,200 次/分钟,每个项目 40,000 次/分钟、30,000,000 次/天;另有 10 分钟短期负载配额和 1 天长期负载配额(按页面或按查询分组、日期范围越长,单次越贵)。URL Inspection:每站点 2,000 次/天、600 次/分钟。
  - 解锁什么:gsc_mining(striking distance/低 CTR/蚕食/衰退)、traffic_funnel 完整六段漏斗、sensor_volatility、did_attribution、seo_vs_ads、monitor 流量问(.seo-monitor/gsc.csv)
- **T3 GA4(免费)**
  - 怎么配:GA4 报告导出 CSV 随时可用(零配置)。gsc.json 补 `ga4_property_id` 键只会让 `doctor.py` 报 T3 徽章,当前没有脚本调用 GA4 Data API。
  - 若你自己调 GA4 Data API:标准属性每天 200,000 个核心 token、每小时 40,000(Analytics 360 为 2,000,000 / 400,000);日配额太平洋时间午夜刷新([Data API 配额](https://developers.google.com/analytics/devguides/reporting/data/v1/quotas),页面日期 2026-10-13,核对 2026-10-21)。请求里加 `"returnPropertyQuota": true` 可读剩余 token。
  - 解锁什么:流量与转化侧分析;ai_referral_log `--attribution` 出 GA4 正则与 AI Assistant 通道归因纪律(测量层口径见 [intake 清单](intake-checklists.md))
- **T4 商业 API(按量计费)与 Bing 免费 key**
  - 典型单价:serper.dev 首个付费包 $50 / 50,000 credits(约 $1.00/1k 次查询),大包降到约 $0.30/1k([serper.dev](https://serper.dev/),核对 2026-10-21);Ahrefs/Semrush 按订阅;DataForSEO 按调用计费
  - Bing Webmaster Tools API key(免费):登录 Bing Webmaster Tools → 先添加并验证站点 → 右上角 Settings → API Access → 接受条款 → Generate API Key。每个用户只能生成一个 key,key 属于用户而不是站点,可用于该用户所有已验证站点。Microsoft 推荐 OAuth 2.0,API key 是第二种方式([Microsoft Learn](https://learn.microsoft.com/en-us/bingwebmaster/getting-access),页面日期 2022-10-13,核对 2026-10-21)。`bing_wmt.py` 读 `--key` 或环境变量 `BING_WMT_KEY`;子命令 `stats`(查询统计)、`pagequery`(单页的查询)、`urlstatus`、`submit`。
  - IndexNow(免费):`indexnow.py` 向 Bing、Yandex、Naver 等提交,Google 不在内([indexnow.org/faq](https://www.indexnow.org/faq))。
  - 解锁什么:竞品排名抓取(喂 serp_overlap)、搜索量与 KD(geo_difficulty `--kd` 输入)、外链结构化观测(cite_domain 输入)
  - 省钱口径四条:①免费层先顶(Keyword Planner 量级免费、GSC 全免费),商业 API 只补缺口;②词表 50-150 个高价值词优先,不买 2000 个噪声词;③先 10-50 词小批量试跑核对质量再放量;④一切第三方数字标 [est] 并注来源工具,不冒充站点自有数据

## 三、安全纪律

1. **key 只进两个地方**:环境变量,或 ~/.config/seo-suite/。建议权限:
   ```sh
   chmod 700 ~/.config/seo-suite && chmod 600 ~/.config/seo-suite/gsc.json
   ```
   gsc.json 是唯一凭证文件;任何凭证不进项目目录、不进聊天粘贴、不进报告附件。
2. **永不进 git/日志/报告**(套件已守,用户侧同样自查):doctor.py 全输出过 redact(home/email/token/secret 值打码、键名保留);monitor.py 拒写明文 webhook;notify.py 的 secret 只经环境变量注入。提交前 `git status` 自查不含 gsc.json/.env。
3. **外发与花钱须确认**:外联邮件/提交表单/发布内容/改线上配置一律先起草、用户本人确认后执行(SKILL.md 对外动作纪律);商业 API 按量计费,任何批量拉取先报预估费用再执行。

## 四、导出文件速查(列头清单)

| 喂给谁 | 文件/输入 | 必需列(缺列的后果) |
|---|---|---|
| gsc_mining / monitor | GSC 效果导出 CSV | Query,Clicks,Impressions,CTR,Position(matrix 模式加 Page;**缺列静默按 0,导出后自查列头**) |
| traffic_funnel | `--gsc` 页面级 CSV + `--cwv` 可选 | Page,Clicks(缺 CWV → good_ux=N/A) |
| forecast | kws.csv | 词,search_volume,position[,cpc](无量不预测;cpc 缺 → 等效付费成本 N/A) |
| serp_overlap | SERP 抓取样 CSV | keyword,top10(分号分隔 URL) |
| grid_rank | rank_data.csv | keyword,grid_point,rank(空/null=未找到;>20 视同未找到) |
| did_attribution | pre/post 两份 | Page,Clicks[,Date](treated 基线 <5 点击 exit 2) |
| sensor_volatility | GSC 多日导出 | Date,Query,Position(单日 exit 2) |
| ai_referral_log | access log(stdin/文件) | apache/nginx combined 或 JSON 行(缺 referrer 计入无 referrer 桶) |
| question_align | `--gsc` 查询×页面 CSV(`gsc_api.py query --dimensions query,page` 或网页导出),`--pages` 页面级 CSV | 查询列、页面列、Clicks、Impressions、Position(`--page URL` 可补单页导出缺的页面列) |
| market_fit | `--gsc-country` 国家维 CSV(`gsc_api.py query --dimensions country`) | Country,Clicks,Impressions,CTR,Position |
| citation_panel record | 面板答案 | 真实采样粘贴(严禁模拟回答;单 prompt ≥3 次采样才下结论) |

## 五、常见组合(目标栈速配)

- **只想知道站健不健康**:T0 就够——体检链(site_crawl → site_audit → health_score → envelope)跑完即出封套,不配任何 key。
- **想要"排名+点击+完整漏斗"**:T2 的 GSC CSV 导出(零门槛)即可上 gsc_mining+traffic_funnel;要日常自动化再加 OAuth 与 monitor。
- **做 GEO/AI 可见性周报**:GEO 采样(T0)+ T3 GA4(AI Assistant 通道引流)+ 可选 T4 厂商面板做对照;报告分列探针/第一方两口径。
- **竞品对标**:T4 serper.dev 小批量(10-50 词)抓 SERP → serp_overlap 聚类;竞品代表页用 site_audit+content_score 逐页审。

## 六、intake 提示语模板(agent 接新任务先问三问)

接新任务时**先问数据、再谈分析**——三问问完,数据边界与报告口径就定了:

1. **你有什么数据源?**(GSC 导出 / GA4 / 排名工具 / 外链工具 / server log / 厂商 AI 面板 / 都没有)
2. **愿意配哪些凭证?**(PSI key 免费 5 分钟 / GSC OAuth 免费 / 商业 API 按量——先报价)
3. **没有的部分按降级口径执行、报告按 tier 声明覆盖范围——可以吗?**

三问的答案直接落到执行路径:答"都没有" → T0 全站体检 + GEO 采样照跑,流量/排名结论声明缺席;答"有 GSC" → 至少 T2 六件套可跑;答"愿意配 key" → 按 T1→T3 顺序 5 分钟一级。

可直接粘贴的模板:

```text
本任务需要:{A(来源)}/{B(来源)}。当前环境探测 tier:T?({能力徽章})。
已有的:{…};缺的将按降级口径执行:{一句话降级},报告将声明覆盖范围。
愿意补配哪一个?①PSI key(免费,约 5 分钟)②GSC OAuth(免费)③商业 API(按量,预估 $…)
```

与报告纪律的衔接:报告**按 tier 声明数据覆盖范围**——T0 时绝不暗示能出 GSC/GA4 结论;
估算逐个标 [est]、实测标 [real](合同表全局守则);降级执行的部分在报告开头一句话声明截断/代理口径。

相关:[数据源合同表](data-source-contract.md)(逐脚本口径)· [intake 清单](intake-checklists.md)(市场与测量层闸门)· 本文末节「你需要自备什么」(原 SKILL.md 第 4 节)

复核说明:本文与合同表同周期复核(信源变更由 intel_check 提示);两表冲突时以合同表为准并回改本文。2026-10-21 按官方文档重核各数据源的接入条件与限额(GSC API Usage Limits、CrUX API / History API、PSI 入门页、GA4 Data API 配额、Bing Webmaster API 取 key 方式)。

## 检查清单(接入后逐项验)

| 检查什么 | 怎么查 | 通过 / 失败判据 |
|---|---|---|
| 当前 tier 与已配键 | `python3 scripts/doctor.py --wizard`;`python3 scripts/doctor.py --keys --check` | 向导列出每个分析目标的就绪状态,只显示键名;`--keys --check` 校验键存在,不读值。退出码 0 = ready |
| CrUX / PSI key 可用 | `python3 scripts/field_data.py --url https://example.com/ --strategy mobile --json` | JSON 里同时有 `field`(CrUX p75)和 `lab`;只有 `lab` 且告警「CrUX 无 key」→ 补 `CRUX_API_KEY`。退出码 3 = 两源全失败 |
| GSC 服务账号能登录 | `python3 scripts/gsc_api.py auth`,再 `python3 scripts/gsc_api.py sites` | `auth` 成功;`sites` 列出目标属性。列不出 → 服务账号邮箱没加进该属性 |
| GSC 拉取列齐全 | `python3 scripts/gsc_api.py query --site sc-domain:example.com --start 2026-09-01 --end 2026-09-28 --dimensions query,page --out gsc.csv`,再 `head -1 gsc.csv` | 表头含 `Query,Page,Clicks,Impressions,CTR,Position`;CTR 是小数(0.0317) |
| 展示数据不跨异常期 | 对比窗口与 2025-05-13 至 2026-04-27 比对([Search Console 数据异常记录](https://support.google.com/webmasters/answer/6211453)) | 两期对比不跨这个期间;跨了就只比点击,不比展示/CTR/位置 |
| Bing key 可用 | `python3 scripts/bing_wmt.py stats --site example.com --out bing.csv` | 返回 CSV(新验证站点历史不回填,空列表 ≠ 0 ≠ 错误);401/凭证错 → 重新生成 key |
| 限额未触顶 | GSC:Cloud 控制台「配额」页;GA4:请求里加 `returnPropertyQuota`;CrUX:控制台配额页 | 日用量低于上文列出的限额;429 时降频,不重试风暴 |

---

## 4. 你需要自备什么

> 2026-10-21 从 SKILL.md 第 4 节原样搬入。

- 本 Skill 不附带数据。需要数据的任务，使用你自己的数据源：Google Search Console、GA4、Bing Webmaster Tools 的导出，或你自己账号下的排名追踪、外链、爬虫工具的导出。
- 可选的外部 API（例如 PageSpeed Insights API、Knowledge Graph Search API）需要你自己的 Key，Skill 不提供任何 Key。
- 需要看渲染后页面时，使用你的 AI 工具自带的浏览器能力，或由你提供渲染后的 HTML / 截图。
