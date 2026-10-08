# EveryInfra SEO Skills

[简体中文](README.md) · [English](README.en.md)

**免费下载，用你自己的 AI 工具和模型。**

EveryInfra SEO Skills 的版本为 `0.3.0`，采用 Apache-2.0 许可协议。仓库里是一个 SEO / GEO 工作台 Skill：`seo-suite`。它是一组工作说明、参考资料和输出模板，本身不调用模型，不捆绑模型提供商，也没有 API Key 或运行时依赖。模型和模型额度由你自己的 AI 工具提供。

## 为什么是现在 / Why now

> 数字均来自公开研究或厂商文档;来源登记于 `skills/seo-suite/references/content/geo-platform-differences.md` 第五节。

| 指标 | 数值 |
|---|---|
| GEO 服务市场 | 8.5 亿美元 → 2031 年预计 73 亿 |
| AI 引荐流量年增速 | +527% |
| AI 流量转化率 vs 自然搜索 | 4.4 倍 |
| Gartner:传统搜索流量(到 2028) | -50% |
| 品牌提及 vs 外链对 AI 排名的相关性 | 约 3 倍 |
| GEO 优化内容的可见性提升(KDD 2024,10K 查询) | +30–115% |
| 目前投入 GEO 的营销者 | 仅 23% |



**一行安装:**

```bash
curl -fsSL https://raw.githubusercontent.com/everyinfra/seo-skills/main/install.sh | bash
```

## 它是什么



`seo-suite` 是一个统一的 SEO 入口：先做统一 intake（站点、市场、目标、已知问题、可用数据），再把任务路由到 overview、research、content、technical、monitoring 五类能力，最后按固定结构给出结论、优先级和验证方法。

它强调证据：不报告页面上不存在的信号，不承诺排名、流量或 AI 引用的提升。GEO（AI 搜索可见度）相关建议以 `references/content/geo-evidence.md` 的证据约束为准。

## 能做哪些 SEO 任务

| 能力集合 | 典型任务 |
|---|---|
| overview | 整站 SEO 诊断、路线图与优先级排序、不知道先做什么时的分诊 |
| research | 关键词研究与搜索意图、SERP 分析、内容缺口、竞品分析、替代方案 / vs 页面规划、专题集群与内容策略 |
| content | SEO 内容 brief 与写作、标题与 meta 描述、GEO / AI 搜索可见度优化、内容质量检查、旧内容刷新 |
| technical | 技术 SEO 与单页审计、robots.txt 与状态码、结构化数据（Schema）、内链与站点架构、实体与知识图谱、Programmatic SEO、Core Web Vitals（LCP）、审计工具输出解读、SEO 归因埋点（GA4 / GTM） |
| monitoring | 排名追踪设置、外链质量评估与外联起草、SEO / GEO 指标、告警阈值、效果报告 |

## 你需要自备什么

- 一个支持 Skill 的 AI 工具，以及你自己配置的模型。
- 需要数据的任务，使用你自己的数据源：Google Search Console、GA4、Bing Webmaster Tools 的导出，或你自己账号下的排名追踪、外链、爬虫工具的导出。
- 可选的外部 API（例如 PageSpeed Insights API、Knowledge Graph Search API）需要你自己的 Key。本仓库不包含、也不提供任何 Key。
- 外联邮件、发布内容等对外动作，Skill 只负责起草，由你本人确认后执行。

## 安装

先获取本仓库：在 GitHub 仓库页面用 **Code → Download ZIP** 下载并解压，或者克隆：

```bash
git clone https://github.com/everyinfra/seo-skills.git
```

下面的命令假设仓库目录名是 `seo-skills`；用 ZIP 解压时目录名可能是 `seo-skills-main`，替换成实际目录即可。

### Codex（CLI / IDE）

把 `skills/seo-suite` 整个文件夹复制到 `~/.agents/skills/`：

```bash
mkdir -p ~/.agents/skills
cp -R seo-skills/skills/seo-suite ~/.agents/skills/
```

在 Codex 中用 `$seo-suite` 调用，或直接描述 SEO 任务，由 Codex 按 Skill 描述选用。没有识别到时，重启 Codex 再试。

### Claude Code

把 `skills/seo-suite` 整个文件夹复制到 `~/.claude/skills/`（对所有项目生效），或项目内的 `.claude/skills/`（只对该项目生效）：

```bash
mkdir -p ~/.claude/skills
cp -R seo-skills/skills/seo-suite ~/.claude/skills/
```

在 Claude Code 中用 `/seo-suite` 调用，或直接描述 SEO 任务，由 Claude Code 按 Skill 描述选用。

其他兼容 Skill 的工具，把同一个文件夹放到该工具文档说明的 Skill 目录即可。参考：[Build skills — Codex](https://developers.openai.com/codex/build-skills) · [Extend Claude with skills](https://code.claude.com/docs/en/skills)

## 目录结构

```text
seo-skills/
├── README.md              中文说明
├── README.en.md           English README
├── LICENSE                Apache-2.0 全文
├── NOTICE                 署名与第三方资料说明
├── CHANGELOG.md           版本记录
├── manifest.json          包信息
└── skills/
    └── seo-suite/
        ├── SKILL.md       入口：intake、路由规则、输出结构
        ├── references/
        │   ├── overview/     能力地图、路由规则、intake 清单
        │   ├── research/     搜索意图、SERP、内容缺口、竞品、专题集群、内容策略
        │   ├── content/      GEO 证据约束、标题与 meta、内容结构与写法、内容刷新
        │   ├── technical/    robots、状态码、Schema、内链与架构、实体、性能、埋点
        │   └── monitoring/   排名追踪、外链、指标、报告、告警
        └── templates/
            ├── research/     研究类输出模板
            ├── audit/        审计类输出模板
            └── monitor/      监控类输出模板
```

## 第三方资料

`references/` 中的资料由 EveryInfra 自行编写。部分主题的组织思路参考了开源项目和公开文档；本仓库不包含这些资料的原文，只提供我们自己的要点摘要和原文链接，每个文件末尾的「来源」一节列出对应链接。详见 [NOTICE](NOTICE)。

## 反馈

问题和建议请提交到 [GitHub Issues](https://github.com/everyinfra/seo-skills/issues)。请勿在 Issue 中粘贴 API Key、凭据、客户数据或其他机密信息。

## 许可证

Apache-2.0，见 [LICENSE](LICENSE)。
