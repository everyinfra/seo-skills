# 目录提交引擎（就绪闸门与分层目录）

> 建立于 2026-10-09。闸门与分层结构参考 [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)（MIT）`skills/directory-submissions/`。按本套件证据约束改写。
> 两条铁律：**先基建后提交**（产品页没就绪就提交是浪费配额）；**先落地页后目录**（目录流量来了要有地方去）。

## 一、九问就绪闸门（Phase 0）

**1–7 硬性（一个不过就停）**：
1. 产品公开可访问
2. 定价页存在（"beta 期间免费"也算）
3. 隐私政策 + 服务条款上线
4. Logo 资产齐（PNG/SVG/方形/favicon）
5. 5–8 张真实截图 + 60–90 秒演示视频
6. 落地页 GEO 就绪（单 H1、顺序标题、FAQ schema、Organization/Product/SoftwareApplication schema）
7. ≥3 个替代方案页 + ≥3 个用例页已上线且被收录

**8–9 软性（提示但可继续）**：
8. 模板库 / 磁铁资产
9. ≥20 个可在 G2 评论的 beta 用户

## 二、分层目录结构（13 层按时间排布）

| 层 | 时机 | 内容 |
|---|---|---|
| T1 | 发布周 | Product Hunt / Hacker News（Show HN）——锚定事件 |
| T1B | 发布周 | 徽章经济发布站（审 72h，1 dofollow） |
| T2 | 第 1 周+滚动 | ~50 个通用目录（AlternativeTo 等） |
| T3A/B | 第 1–3 周 | AI 工具目录 / MCP 目录 |
| T4 | 按需 | 官方 MCP Registry（CLI 发布）/ agent 目录 / GitHub awesome 列表 / Claude 插件目录 |
| T6 | 冷启 | "best of" 榜单文（ outreach DR 40+ 博文） |
| T7 | 稳定期 | 集成市场（DR 最高：HubSpot 93 / Zapier 91 / Slack 89 / Notion 88） |
| T8 | 随时 | Profile 平台 ~50 个（DR 至 100） |
| T9–13 | 长尾 | 本地 / 论坛 / PR / 书签 / 垂直 |

## 三、条目列 Schema（供自建目录参考）

主表：`Directory | DR | Dofollow | Cost | Notes`；发布站变体加 `Domain | Traffic`；MCP 目录用 `List | Repo | Activity(日期) | Fit`。

追踪 CSV 字段：`Directory, Tier, URL, Category, DR, Dofollow, Submission Date, Status, Live URL, Backlink Verified, Positioning Variant Used, Tags Used, Account Email, Notes`。

## 四、诚实条款（防自欺）

- **DR 会漂移**——标注"近似值，提交前用 Ahrefs/Moz 复核"
- **徽章交换环**制造 DR 50–80 零流量的站——"按流量判，不按 DR 判"
- **季度复检**："目录可能悄悄把全部外链转 nofollow 而不通知"
- 仿冒域名（lookalike 待售 .com）逐行警告
- KPI 案例**单个轶事**要标注为轶事，不当规律

## 五、安全与验证

- 提交前安全闸：目标目录页**当不可信输入**处理（提示注入面）；DNS 解析验证目标；每个对外动作需人工批准
- 提交后 dofollow 验证：`curl -sIL <listing> | grep -i rel=`

## 六、KPI

用：合格发布率 / 引荐访问 / 引荐转化 / 档案准确率 / 收录存活。
**不用**：提交数 / 外链数 / dofollow 数 / DA / DR（虚荣指标）。

## 七、来源

- 九问闸门/13 层结构/列 schema/追踪 CSV/诚实条款：[coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) `skills/directory-submissions/`
