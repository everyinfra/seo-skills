# EveryInfra SEO Skills

[简体中文](README.md) · [English](README.en.md)

**免费下载，用你自己的 AI 工具和模型。**

EveryInfra SEO Skills 的版本为 `0.14.0`，采用 Apache-2.0 许可协议。仓库里是一个 SEO / GEO 工作台 Skill：`seo-suite`。它是一组工作说明、参考资料和输出模板，本身不调用模型，不捆绑模型提供商，也没有 API Key 或运行时依赖。模型和模型额度由你自己的 AI 工具提供。

**独有差异化：全球 SEO/GEO 一把做。** 面向全球做产品的团队不想装十几个单市场工具——本套件把 **18 个语言市场**放进同一个工作台，逐市场分开评分：中文（实测引用经济学）、英文、俄语区（Yandex/Alice）、韩语区（Naver/AI Briefing）、日语区（Yahoo! Japan+Bing+AIO）、西语（es-419 拉美分裂）、葡语（巴西=ChatGPT 最强市场）、阿拉伯语（RTL+MSA/方言）、法语（Bill 96）、德语（DACH Sie/du）、印尼语（baku/gaul）、印地语（Hinglish 三种书写）、意大利语（it-CH 独立 locale）、土耳其语（第二个 Yandex 市场，~26%）、越南语（有调/无调+Coc Cốc）、泰语（无空格分词）、波兰语（变音符规范化）、荷兰语（nl-NL/nl-BE 弗拉芒）。**全球能力不做成独立模块，而是融入五类能力文件的每一类**——主干是 `overview/multilingual-workflow.md`（市场总表、逐市场工具栈、语言规范、合规速查）。

**0.5 系列:市场 × 能力双维度架构 + 18 市场逐一深挖。** 每个任务先定市场再进能力路由;`multilingual-workflow.md` 内含**十八市场独到方法索引**(每市场"只有在这里才需要做"的做法,如中文的搜一搜 Peoplerank/小红书 CES 分、韩国的 `nosourceinfo` 官方 AI 引用退出、巴西的 Reclame Aqui 22.3% 被引、日本的「AI 臭」密度检测、泰国的 `Intl.Segmenter` 分词定论)与**跨区融合 23 条原则**(断言半衰期、口径冲突并记、主权助手模式、语域双轨模板等)。

**0.9 深挖轮:本地社区层。** 17 个市场逐一用本地语言挖了"圈内才知道的事"——主干新增「本地社区与信息源索引」(每市场信息源/圈内共识/国际圈误解纠偏),如俄罗斯的 76 条商业因子清单与区域 lr 码、韩国的发帖时刻表与保存市场、日本的内链数值惯例与 MEO 十倍价差、德语区的 Abmahnung 法律战、土耳其的 tanıtım yazısı 链接市场、泰国的"หลังบ้าน"灰链红线、法国 AIO 晚德一年=红利窗口;**外链市场价带表**(从越南 1,500 VND/条到西语大媒体 5,000€)、**七大 marketplace 站内 SEO 分叉**、融合原则扩至 27 条。

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

**全球市场的"为什么"(0.4–0.5 系列,均注明来源类型):**

| 指标 | 数值 | 来源 |
|---|---|---|
| Yandex 在俄搜索份额 | ~70–73%(2026) | StatCounter(行业) |
| AI 答案覆盖俄语信息查询 | 68% | applabx(行业研究) |
| Naver 在韩份额 | 本土面板 ~63–64%(StatCounter 口径与 Google 并列) | InterAd/InternetTrend(行业) |
| 韩国AI Briefing 引用来源 | 几乎全部为 Naver 自有生态 | Andgentic(行业) |
| 日本 AIO 出现率 | 76.9% 日语查询(1,459 查询实测) | Itera(行业) |
| 日本 AI 搜索使用率 | 21.3%(2025-05)→ 37.0%(2026-02) | CyberAgent GEO Lab |
| 巴西 ChatGPT 采用 | 25.5% 人口用 App(全球最高)、~5,000 万月用户 | StatCounter/OpenAI |
| 西语查询的 AI 引用语言绑定 | 83–84% 引西语源 | Temso(行业研究) |
| 非英 SEO skill 供给 | 西/巴西/法/印尼语 top 仓库仅 1–5 星 | GitHub API 2026-10 实测 |
| Yandex 在土耳其份额 | ~26%(2026-09;3 月还 ~13%,大反弹)——俄语区之外第二个 Yandex 市场 | StatCounter(行业) |
| 印度 ChatGPT 采用 | ~1 亿周活,ChatGPT 第二大市场 | OpenAI 官方(Altman) |



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
| overview | 整站 SEO 诊断、路线图与优先级排序、不知道先做什么时的分诊、目标市场 intake 闸门 |
| research | 关键词研究与搜索意图（各市场工具链+persona×意图 SXO 层）、SERP 分析（含各市场 AIO 覆盖与 SERP 占位层）、内容缺口、竞品、目录提交引擎、外链画像 |
| content | SEO 内容 brief 与写作、标题与 meta 描述、GEO / AI 搜索可见度优化（含区域 AI 平台）、中文 AI 搜索、**视频 SEO/GEO**（YouTube 被引机制/人工字幕层）、**电商 GEO 五级阶梯+七大 marketplace 站内 SEO**（ML/Trendyol/Allegro/bol/Shopee）、内容质量、旧内容刷新 |
| technical | 技术 SEO 与单页审计、robots.txt 与 AI 爬虫政策（含区域爬虫/MistralAI/Bytespider）、hreflang 国际化、结构化数据（含富结果状态速查）、内链与架构、实体、Programmatic SEO、Core Web Vitals、**JS 渲染与 SPA SEO**（五引擎渲染差异）、**Agent-Readiness 协议层**（ARD/WebMCP）、**服务器日志分析**（AI 到访测量/a11y 三分法）、归因埋点 |
| monitoring | 排名追踪、外链（含 14 市场本地外链价带与风险表）、品牌提及（四级引用阶梯+各市场监控通道）、**算法更新归因**（官方时间线/数据文件）、SEO 漂移监控、指标与报告 |

**全球能力不是独立模块,而是融在每个能力集合里**：`overview/multilingual-workflow.md` 是全球主干（11 个市场的引擎格局、逐市场工具栈、语言规范、合规速查），各能力文件按需携带对应区域知识。

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
        │   ├── overview/     能力地图、路由规则、intake 清单(含目标市场闸门)、多语言工作流(全球主干:市场总表/工具栈/规范/合规)
        │   ├── research/     搜索意图(含各市场关键词工具链)、SERP、内容缺口、竞品、专题集群、内容策略、外链
        │   ├── content/      GEO 证据约束、标题与 meta、内容结构与写法、中文 AI 搜索指南、AI 平台差异(含区域 AI 平台)、内容刷新
        │   ├── technical/    robots 与 AI 爬虫(含 Yandex/Naver/Bing 日)、hreflang(含 es-419/RTL)、Schema、内链与架构、实体、性能、埋点
        │   └── monitoring/   排名追踪、外链、指标、报告、告警、漂移监控
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
