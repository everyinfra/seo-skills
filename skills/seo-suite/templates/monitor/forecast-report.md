# {答案式标题,例:"自然流量 12k→19k/月:三档情景收入区间 ¥18-31 万;建议先投等效付费成本的 10%"}

_For: {决策人} · Date: {YYYY-MM-DD} · Prepared by: {who} · Keywords: {N} 入榜 / {M} 排除(>30 位) · 工具: `scripts/forecast.py`(seoClarity 六步) · 校准: factor={x}({actual=GA 对比 | 未校准})_

> 数字口径:CTR 模型是估算 [est];位次情景是目标态假设而非承诺;>30 位的词不预测。

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

## Scenario 三档对照(官方枚举)

| 情景 | 规则(官方口径) | 流量/月 | Δ vs 当前 | 收入价值/月 | 等效付费成本/月 |
|---|---|---|---|---|---|
| pct10(保守默认) | 位次提升 10% | {} | {} | {} | {} |
| pos2(中档) | 每词升 2 位 | {} | {} | {} | {} |
| rank3(目标) | 全部词到第 3 位 | {} | {} | {} | {} |

>{} 位的词不预测(官方口径:"Google 认为相关但不权威"区间之外),共排除 {} 词,不在上表内。

## 商业提案(双结构)

**省钱结构(Traffic Potential × CPC = 等效付费成本)**:{选定情景} 预测流量 {}/月按自有 CPC 折算 = 等效付费成本 {}/月 [est];提案只投其 **10%({}/月)**——拿到同等自然流量即打平付费成本。

**赚钱结构(流量 × CVR × AOV)**:{流量}/月 × CVR {} × {AOV/lead-value} {} = {}/月收入价值;无电商转化时改用线索价值口径(--lead-value)。

## ROI 五法清单(各一行)

| 法 | 一行说明 |
|---|---|
| 实际转化 | 上线后真实 orders×AOV 对比投入(最硬口径,滞后一个周期) |
| Traffic Value | 流量 × 平均 CPC 的等效媒体价值(上表已列) |
| 相对付费省钱 | 同等点击若走付费的 Cost − SEO 投入(省钱结构兑现口径) |
| 付费 CVR 估算 | 无自有 CVR 时用付费搜索 CVR 作代理 |
| 按项目 tag 归因 | SEO 落地页打 campaign tag,GA 按项目归因收入 |

## Recommended Actions

1. {用 --actual {GA 月流量} 跑一次校准并保存 calibration.json——四家方法论中唯一明示的"模型自校准"环节,下次 --load-calibration 自动套用}
2. {用自有 GSC 90 天 非品牌 CTR 曲线(--ctr)替换行业默认 [est]}
3. {按 {选定情景} 排期内容/外链;月度复盘实际位次 vs 预测,偏差>{}% 重跑校准}

## Assumptions & 局限

- CTR 模型是估算 [est]:默认为行业 benchmark;官方建议用自有 GSC 90 天 移动/桌面 × 品牌/非品牌 曲线(预测只用非品牌)。
- >30 位的词不预测(官方口径:"Google 认为相关但不权威"区间之外)。
- 位次提升是目标态假设,不是承诺;AIO/广告位占据的 SERP 实际 CTR 会低于曲线。
- 校准系数只修正总量级,不修正词间分布;CVR/AOV 为全局常数,未按意图分段。

## What could change this conclusion

- {校准来源:factor={} 来自 {GA actual / 历史 calibration.json};GA 口径漂移(品牌流量混入)会直接改写全部数字}
- {搜索量为第三方估算 [est],季节性与趋势未建模;大促月不适用}
- {若 SERP 被 AI Overviews/广告重度占据,曲线 CTR 高估——换自有曲线后自动修正}
- {CVR 全局常数假设:高意图词实际 CVR 可数倍于均值,赚钱结构偏保守}

## Method Notes

- 数据源与取值:{kws.csv(词/量/位次/CPC)· CTR 曲线 {来源} · CVR {} · AOV/lead-value {} · 投入 {}};数字缺失写 [要追加: 数据源],禁编造。
- 方法:seoClarity 六步(CTR 曲线→估算→GA 校准→CPC 竞争→三情景→汇报);`scripts/forecast.py --json` 可复算每个数字;校准持久化 calibration.json。
- 符号:[est]=估算值;Δ=对当前位次基线;等效付费成本=流量×CPC(省钱结构),收入价值=流量×CVR×AOV(赚钱结构);ROI=(价值−投入)/投入。
