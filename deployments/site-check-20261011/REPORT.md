# EveryInfra 站点完整体检(2026-10-11)——"先体检,后内容"原则的首次执行

**判定(The answer):技术地基 PASS(主分 100.0/Excellent,零 CRITICAL)——内容策略可以启动。** 全部 WARN 均为 GitHub 模板页平台固有限制(我们不可控),记录不修;AI Search Health 85/100。

## 体检范围与链路

目标:github.com/everyinfra/seo-skills(3 关键页)+ everyinfra/jev-radar(1 页)。
链路:`site_audit 多页 → health_score → prioritize → envelope`(全部真实网络,证据在 evidence/)。

## 结果

| 指标 | 值 | 说明 |
|---|---|---|
| 主分(Ahrefs 口径) | **100.0 Excellent** | 仅 CRITICAL 扣分;4 页零 CRITICAL |
| AI Search Health | 85/100 | bots/llms.txt/freshness/BLUF 全过;semantic_html 2.5% 未过(GitHub 模板页固有) |
| Top 影响项 | canonical 缺失×4 / description 越限×4 / 链接>100×4 | **GitHub 平台固有,不可控,记录不修** |
| 可控修复(本轮已做) | 仓库 description 数字过期 38/71→56/672 | 上一轮 site_audit 揪出,gh 已修(title 304→264 字符) |

## 处置决定

1. **内容闸:开**——在 GitHub 平台约束内,内容策略(热点选题/深度文)可以启动,不需要等待技术修复
2. WARN 项设为 accepted(接受≠消失,周报仍计数):canonical/title/description/链接数均由 GitHub 模板决定
3. **真正可控的优化目标在未来**:自建站(GitHub Pages 或独立域)上线当天重跑本链作为基线——届时 canonical/schema/描述全部可控,主分与 AI 子分才是"我们的"数字
4. envelope 封套(evidence/04-envelope/)作为下次体检的 --baseline 对比物(audit_compare 回归门)

## What could change this conclusion

- GitHub 若调整仓库页模板(如加 canonical),accepted 清单需重评
- jev-radar 仅审了 1 页;其 README 渲染页与未来 Pages 站需补审
- "零 CRITICAL"的口径基于单页抽样;自建站上线后应跑 sitemap 全采样(traffic_funnel 六阶段)

## Method Notes

命令:evidence/ 内编号文件对应;health_score 输入=site_audit 末段合并 JSON;envelope 三源聚合。体检原则:SKILL.md 使用原则第 0 条(先体检后内容)。快照声明:单时点数据,变更后重跑。
