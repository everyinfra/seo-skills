# {答案式标题,例:"自然流量 12k→19k/月:三档情景收入区间 ¥18-31 万;建议先投等效付费成本的 10%"}

_For: {决策人} · Date: {YYYY-MM-DD} · Prepared by: {who} · Keywords: {N} 入榜 / {M} 排除(>30 位) · 工具: `scripts/forecast.py`(按 seoClarity 公开的六步流程实现) · 校准: factor={x}({actual=GA 对比 | 未校准})_

> 数字口径:CTR 模型是估算 [est];位次情景是目标态假设而非承诺;>30 位的词不预测。内置默认 CTR 曲线(1 位 28%、2 位 15%、3 位 11%、5 位 7%、10 位 3%、20 位 1%)是 `forecast.py` 里的估算锚点,不是 Google 数据,也不是公认的行业基准:第三方研究给出的第 1 位 CTR 从 7% 到 28% 都有。报告里的收入数字要换成自己的 GSC 曲线再信。

## The answer

{一段独立成立:推荐以哪档做规划基线(pct10 保守默认),预测流量与收入区间,建议投入(等效付费成本的 10%),回本口径与置信度。只读这段的人不会错。}

## Key numbers

| 指标 | Current(当前位次) | pct10(保守) | pos2(中档) | rank3(目标) |
|---|---|---|---|---|
| 预测自然流量/月 | {} | {} | {} | {} |
| 订单(或线索)/月 | {} | {} | {} | {} |
| 自然收入价值/月 | {} | {} | {} | {} |
| 等效付费成本/月(CPC 折算) | {} | {} | {} | {} |
| ROI(对投入 {}) | - | {} | {} | {} |

## Funnel(五级:rank → visibility → traffic → conversions → revenue)

| 漏斗级 | Current | Forecast({选定情景}) | 口径 |
|---|---|---|---|
| Rank(位次) | {中位/加权位次} | {情景规则,如"位次提升 10%"} | 目标态假设,非承诺 |
| Visibility(CTR 加权可见度) | {Σ vol×CTR ÷ Σ vol} | {} | CTR 曲线:{内置行业默认 [est] / 自有 GSC 曲线} |
| Traffic(自然流量/月) | {} | {} | Σ 量×CTR(位次) × 校准系数 {} |
| Conversions(转化/月) | {} | {} | traffic × CVR {} |
| Revenue(收入价值/月) | {} | {} | conversions × {AOV / lead-value} {} |

## Scenario 三档对照(本套件口径)

| 情景 | 规则(`forecast.py` 内置,可用 `--scenario rankN/pctN/posN` 改) | 流量/月 | Δ vs 当前 | 收入价值/月 | 等效付费成本/月 |
|---|---|---|---|---|---|
| pct10(保守默认) | 位次提升 10% | {} | {} | {} | {} |
| pos2(中档) | 每词升 2 位 | {} | {} | {} | {} |
| rank3(目标) | 全部词到第 3 位 | {} | {} | {} | {} |

>30 位的词不预测(seoClarity 的示例把 11–30 位当「相关但不权威」区间,并说 30 位以外不投入大量资源很难进前列;[seoClarity 博客](https://www.seoclarity.net/blog/seo-forecasting-business-case),2023-10-11,核对 2026-10-21),共排除 {} 词,不在上表内。

## 商业提案(双结构)

**省钱结构(Traffic Potential × CPC = 等效付费成本)**:{选定情景} 预测流量 {}/月按自有 CPC 折算 = 等效付费成本 {}/月 [est];提案只投其 **10%({}/月)**——拿到同等自然流量即打平付费成本。

**赚钱结构(流量 × CVR × AOV)**:{流量}/月 × CVR {} × {AOV/lead-value} {} = {}/月收入价值;无电商转化时改用线索价值口径(--lead-value)。

## ROI 五法清单(各一行,本套件口径)

| 法 | 一行说明 |
|---|---|
| 实际转化 | 上线后真实 orders×AOV 对比投入(最硬口径,滞后一个周期) |
| Traffic Value | 流量 × 平均 CPC 的等效媒体价值(上表已列) |
| 相对付费省钱 | 同等点击若走付费的 Cost − SEO 投入(省钱结构兑现口径) |
| 付费 CVR 估算 | 无自有 CVR 时用付费搜索 CVR 作代理 |
| 按项目 tag 归因 | SEO 落地页打 campaign tag,GA 按项目归因收入 |

## Recommended Actions

1. {用 --actual {GA 月流量} 跑一次校准并保存 calibration.json(校准步骤对应 seoClarity 的「与实际 analytics 对比后调整 CTR 模型」),下次 --load-calibration 自动套用}
2. {用自有 GSC 近 90 天([GSC 数据异常期](../../references/overview/facts.md#gsc-anomaly)结束之后)非品牌 CTR 曲线(--ctr)替换内置默认 [est]}
3. {按 {选定情景} 排期内容/外链;月度复盘实际位次 vs 预测,偏差>{}% 重跑校准}

## Assumptions & 局限

- CTR 模型是估算 [est]:默认曲线是脚本内置的估算锚点。seoClarity 建议分移动/桌面、品牌/非品牌各建 CTR 曲线;本套件口径是用自有 GSC 近 90 天的非品牌曲线(预测只用非品牌)。窗口必须在异常期结束之后:Search Console 的展示、CTR、平均排名在[GSC 数据异常期](../../references/overview/facts.md#gsc-anomaly)里记录有误,这段时间的 CTR 曲线不可信。
- >30 位的词不预测(见上)。
- 位次提升是目标态假设,不是承诺;AI 概览/广告位占据的 SERP,实际 CTR 可能低于曲线。
- 校准系数只修正总量级,不修正词间分布;CVR/AOV 为全局常数,未按意图分段。

## 检查清单(跑预测前逐项:检查什么 → 怎么查 → 通过/失败)

| # | 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|---|
| 1 | 输入表合格 | `kws.csv` 列为 keyword, search_volume, current_position[, cpc];`ctr.csv` 列为 position, ctr | 通过:脚本退出码 0。失败:退出码 2(文件、格式或参数错)。无 cpc 列时「等效付费成本」为 N/A,省钱结构不能写 |
| 2 | CTR 曲线来源 | 看输出「步1 CTR 曲线」行 | 通过:`--ctr` 给了自有 GSC 非品牌曲线,窗口在[GSC 数据异常期](../../references/overview/facts.md#gsc-anomaly)结束之后。失败:仍是内置默认 [est] → 报告所有金额标 [est] |
| 3 | 已校准 | `python3 scripts/forecast.py --kws kws.csv --ctr gsc_ctr.csv --actual GA月流量 --save-calibration calibration.json`;之后用 `--load-calibration` | 通过:「步3 校准」行有 factor 且来源是 GA 自然渠道月流量。失败:「未校准(factor=1.00)」 → 数字只当量级 |
| 4 | >30 位的词已排除并列出 | 输出「入榜 N 词(>30 位不预测,排除 M 词)」 | 通过:M 与你数的一致。失败:对不上 |
| 5 | 数字可复算 | `python3 scripts/forecast.py … --json`,读 `baseline`、`scenarios`、`primary`、`proposal`、`calibration` | 通过:报告里每个数字都在 JSON 里。失败:手算或手改的数字 |
| 6 | ROI 有投入口径 | 加 `--invest 月投入` | 通过:ROI 列有值。失败:「-」 → 不写 ROI |
| 7 | 实际 vs 预测月度复盘 | 每月比较实际位次、流量与预测(GSC + GA) | 通过:偏差在你定的阈值内。失败:超阈值 → 重跑校准 |

## What could change this conclusion

- {校准来源:factor={} 来自 {GA actual / 历史 calibration.json};GA 口径漂移(品牌流量混入)会直接改写全部数字}
- {搜索量为第三方估算 [est],季节性与趋势未建模;大促月不适用}
- {若 SERP 被 AI 概览/广告重度占据,曲线 CTR 可能高估;换自有曲线会部分反映,但曲线本身是历史数据}
- {CVR 全局常数假设:高意图词实际 CVR 可数倍于均值,赚钱结构偏保守}

## Method Notes

- 数据源与取值:{kws.csv(词/量/位次/CPC)· CTR 曲线 {来源} · CVR {} · AOV/lead-value {} · 投入 {}};数字缺失写 [要追加: 数据源],禁编造。
- 方法:seoClarity 公开的六步(取 CTR→套用到现有数据估算→与 analytics 实际对比校准→用 CPC 看竞争度→按位次增长重新套 CTR 预测→向管理层汇报;[原文](https://www.seoclarity.net/blog/seo-forecasting-business-case)已核);三档情景的名字和规则(rank3/pct10/pos2)是脚本的本套件口径,原文没有这三档。`scripts/forecast.py --json` 可复算每个数字;校准持久化 calibration.json。
- 符号:[est]=估算值;Δ=对当前位次基线;等效付费成本=流量×CPC(省钱结构),收入价值=流量×CVR×AOV(赚钱结构);ROI=(价值−投入)/投入。
