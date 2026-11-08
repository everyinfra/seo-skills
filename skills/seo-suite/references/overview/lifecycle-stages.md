# 产品阶段 × 成熟度:两条轴诊断(RQ-237)

同一个开局,产品在不同阶段该做的 SEO / GEO 完全不同:还没上线的产品去「提交 GSC」没意义,增长期的站再去「起名和定 URL 结构」也晚了。所以先定位,再选打法。定位用两条轴:

- **产品阶段**(6 档):产品走到了哪一步。
- **成熟度**(5 个方面 × 5 级):每个方面做到了什么程度。级别名借 [Moz SEO 客户成熟度](https://moz.com/blog/seo-client-maturity) 和 [Conductor AEO 成熟度](https://www.conductor.com/academy/aeo-maturity/) 的 5 级划分(核对 2026-11-08)。

两条轴都由 `lifecycle.py diagnose` 按 `data/lifecycle.json` 的条件算,不靠模型感觉。用户可以在 `seo-ops/playbook/lifecycle.json` 写同名键覆盖(比如改阈值)。

```bash
python3 scripts/lifecycle.py diagnose --scan seo-ops/context/scan.json --ws seo-ops [--metrics m.json]
```

`--metrics` 是扁平的指标 JSON,常用键:`gsc_impressions_28d`、`gsc_clicks_28d`、`gsc_clicks_prev_28d`、`referring_domains`、`pages_with_clicks`、`cwv_pass`、`ai_referrals_28d`、`ai_citation_weeks`。开局时也可以把这些写进 `profile.json` 的 `metrics`。

## 一、产品阶段

| 阶段 | 怎么判(按顺序,先命中先用) | 重点 |
|---|---|---|
| 5 改版 / 迁移 / 转型 | 档案里记了改版类事件:migration、domain_change、replatform、url_restructure、merge_sites、new_product_line、rebrand(`onboard.py event add`) | 改动前存基线;301 映射表;上线后对比;新产品线回开局第 1 环 |
| 0 想法 / 原型 | 站点不可访问,仓库里也没有公开路由 | 用搜索数据验证需求;起名和域名;按关键词版图定信息架构和 URL;技术选型的 SEO 约束;品牌实体统一 |
| 1 上线前 | 仓库有公开路由但站点不可访问;或站点可访问但 robots 全封 / 首页 noindex | 上线清单(每项写负责人);本地预览上跑体检(`site_crawl.py --allow-local`);GSC / Bing 验证和埋点;AI 爬虫策略和 llms.txt |
| 2 刚上线 | 近 28 天展示 < 1000,或站龄 < 90 天 | 收录(sitemap、IndexNow);冷启动外链;品牌实体档案;第一批核心页;llms.txt |
| 3 增长期 | 点击环比 ≥ +10%;或在 ±10% 内且站龄 < 2 年 | 关键词版图、内容生产线、对比页、程序化页(带闸门)、内链外链、AI 引用监控、归因、每周运营单 |
| 4 成熟期 | 点击环比 ≤ -10%;或在 ±10% 内且站龄 ≥ 2 年 | 内容刷新和退役、掉量排查和算法归因、多市场、实验 |

- 站龄来自 Wayback 最早快照(product_scan);拿不到就是未知。
- 没有 GSC 时 2 / 3 / 4 分不清:结果标「猜测」、列候选,在开局第 1 环让用户确认。用户确认的阶段优先,和规则不一致时写进 `conflicts`。
- 阶段 5 另报「底层阶段」(改版前在哪一档),改版做完后删掉事件,回到底层阶段。

各阶段的详细打法挂在已有专题参考上:上线和收录看 [validation-guide](../technical/validation-guide.md)、[redirects-canonical](../technical/redirects-canonical.md);增长看 [site-type-playbooks](site-type-playbooks.md)、[strategy-fit](strategy-fit.md);成熟看 [content-refresh-playbook](../content/content-refresh-playbook.md);监控看 [ops-agenda](../monitoring/ops-agenda.md)。想法阶段和上线前的打法卡在 RQ-237 第 2 批补。

## 二、成熟度

级别:0 还没开始 · 1 零散 · 2 能重复 · 3 有体系 · 4 可度量 · 5 持续优化。级别 = 从 1 级往上、条件全部满足的最高一级;某一级的条件缺证据,就停在下面一级并列出缺什么;一级都没证实且缺证据记「未知」。

| 方面 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| 技术 | 站点可访问 | robots / noindex 没封、有 sitemap | 体检 CRITICAL 清零 | 主分 ≥ 80 且 CWV 达标 | 每周运营单跑了 ≥ 4 期 |
| 内容 | ≥ 5 个 URL | 有产品 / 定价 / 文档类核心页 | 博客类 ≥ 10 篇 | 对比 / 集成 / 案例页 ≥ 3,且 ≥ 10 个页面有点击 | 近 90 天内容改动 ≥ 3 次 |
| 外链与品牌 | 有统一品牌名 | Organization sameAs ≥ 2 | 引用域 ≥ 20 | 引用域 ≥ 100 | 引用域 ≥ 500 且在跟踪未链提及 |
| AI 可见度 | 没全封爬虫 | 有 llms.txt | 有结构化数据且品牌名一致 | 在量 AI 引荐或引用 | AI 引用连续 ≥ 4 周有记录 |
| 团队与测量 | 开局第 1 环确认 | 装了统计埋点 | 接了 GSC 且写清转化 | 有业务目标数字和口径 | 每周运营单 ≥ 4 期、4 期里看过 3 期以上 |

**最该补的一格**:按阶段的补短顺序(`dim_priority_by_stage`)找级别最低的那一维;例如上线前先补技术,增长期先补内容。输出里的「下一件事」就是那一格升一级要做的事。

## 三、判据从哪来、什么时候改

- 阶段阈值(90 天、1000 展示、±10%、2 年)是经验口径,不是 Google 公布的数;改阈值写进 `seo-ops/playbook/lifecycle.json`,不改本仓库。
- 成熟度条件只用能核对的证据(scan、体检、GSC、运营单、档案);拿不到的维记「未知」,不猜。
- 业内只查到按「公司成熟度」分级的框架(Moz、Conductor),没查到按「产品阶段」划分的现成行业框架(核对 2026-11-08);本表的 6 个阶段是我们自己的划分,用 RQ-237 例 4 的 6 个产品验。
