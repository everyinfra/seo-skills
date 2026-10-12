# examples/:真实脚本链产出的交付物样例

> 每个 examples/ 子目录是一次**可复现的脚本链运行**留下的完整交付物(报告+证据+原始数据),示范"这套件跑完之后,用户手里拿到什么"。规范(命名/结构/如何新增)见 [CONVENTIONS.md](CONVENTIONS.md);全库交付纪律见 [SKILL.md](../SKILL.md)。

## 索引

站型列=该示例对应的 [site-type-playbooks.md](../references/overview/site-type-playbooks.md) 打法卡(卡内「开局命令链」末行互引回本表);对不上具体站型的通用链标 —。

| 示例 | 站型 | 用的脚本链 | 主要交付物 |
|---|---|---|---|
| trend-gate-geo-survey-20261011 | ③ 媒体/内容 | trend_watch watch→gate | 真实热点的四问闸门 GO 决策件(⚠️ 首跑误用了 SEO 元领域话题,已更正为产品垂直——见目录内 CORRECTION.md 与 product-vertical-config.json) |
| [site-audit-chain-example.com-20261010/](site-audit-chain-example.com-20261010/REPORT.md) | —(通用) | `site_audit.py --json` → `health_score.py --input` → `fix_plan.py --audit --estimate`(真实抓取 https://example.com) | dev 模式审计报告(REPORT.md)+ 3 份编号证据(审计 JSON/健康分/修复计划 dry-run) |
| [citation-panel-demo-20261010/](citation-panel-demo-20261010/REPORT.md) | —(通用;AI 可见性) | `citation_panel.py init → record ×6 → report`(合成数据,显式声明) | AI 可见性面板报告(REPORT.md)+ 工具原样 report 输出(evidence/01)+ panel.json/runs/inputs 原始层 |
| [envelope-chain-example.com-20261011/](envelope-chain-example.com-20261011/REPORT.md) | —(通用) | `site_audit.py --json` → `health_score.py --json` → `prioritize.py --json` → `envelope.py`(三源聚合;真实抓取 https://example.com) | dev 模式 envelope 报告(REPORT.md)+ 4 步编号证据,含 envelope 落盘树(evidence/04:audit-data.json + REPORT.md + findings/*.md 3/3 类别,部分落盘契约形态) |
| [ai-views-example.com-20261011/](ai-views-example.com-20261011/REPORT.md) | ⑤ 文档/开发者 | `ai_views.py --html --apply --json`(真实抓取的 HTML 离线重放,零网络) | AI 视图层报告(REPORT.md;token 缩减 144→72/50.0%、Scrunch 对标未达标如实报、人审后部署边界)+ evidence 4 件(JSON/stats/视图/净化前后 diff) |
| [citation-decision-demo-20261011/](citation-decision-demo-20261011/REPORT.md) | ① SaaS(合成演示,比价词形) | `citation_panel.py init → record ×6` → `citation_gaps.py --owned-relevance --domain-class` → `cite_domain.py --input`(合成数据,显式声明) | 七叉决策演示报告(REPORT.md;14 prompt 覆盖全 7 分支×2)+ gaps 三形态证据(md/csv/json)+ g2.com 评级证据(90.0/A)+ panel/runs/inputs 原始层 |
| [gold-standard-keyword-research.md](gold-standard-keyword-research.md) | —(通用) | 无脚本(人工交付金标准,合成数据) | 关键词研究七段式单文件样例 |

## How to read an example(三层结构)

每个示例目录固定三层,自上而下读、自下而上溯源:

1. **REPORT.md(叙事层)**:verdict-first——第一行/前 30 行就能看到结论(主分与档位、或核心百分比),读者据此决定是否往下。正文每个数字都能在下层原样找到;结尾必有 Methodology(用了哪些脚本+精确命令行)。
2. **evidence/(证据层)**:工具产出的**原样落盘**,文件名按步骤编号对齐(`01-` 第一步、`02-` 第二步…);报告里的数字按编号回溯(如"evidence/02"即健康分输出)。证据文件永不手改。
3. **原始数据层**:示例自带的输入与中间产物(审计 JSON 的 pure 副本、panel.json、runs/、inputs/、fetch guard 原始输出等)——是"复跑一遍能对上"的底账。

读的纪律:**REPORT 里的数字 → evidence 编号 → 原始数据**,三层对不上就是报告写错了;示例若标明"合成数据",则只看形态、不引用数字。

## 快照免责声明

所有示例都是**单点时间快照**:审计对象的内容、robots/llms.txt/sitemap、AI 引擎的回答都会漂移,今天复跑大概率得到不同数字。示例展示的是**交付物形态**(结构、口径、可回溯纪律),不是目标站现状;不要把示例里的任何 finding 当作对 example.com 或任何品牌的现存判断。
