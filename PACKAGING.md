# seo-suite 的接入形态:Skill / Plugin / MCP 怎么选

> 建立 2026-10-10,基于 Claude 生态官方文档与 2026-10 市场实证(来源见 references/research/competitive-landscape.md 第五节)。一句话结论:**Skill 是内容,Plugin 是包装,MCP 是数据接口——我们三者都要,但各归其位。**

## 形态对比

| | 裸 Skill | Plugin(marketplace) | MCP server | CLI(pip/npm) | GH Action |
|---|---|---|---|---|---|
| 安装门槛 | clone+拷目录 | **一条命令** | 一条命令(或随 plugin 自动注册) | pip install | fork 仓库 |
| 能力边界 | 知识+流程+本地脚本 | skill 的一切+可捆绑 MCP/hooks/依赖 | 外部数据与动作接口(无工作流语义) | 全功能可脚本化 | 定时/CI 批跑 |
| 常驻 context | 极低(渐进式披露) | 同左(多组件叠加) | 工具定义常驻,多 server 时显著(Zilliz 实测 3 个 server 占 200K 窗口 72%) | 零 | 零 |
| 更新 | 手动 pull | `plugin update`/版本钉扎 | server 侧即时 | pip upgrade | git pull |
| 跨宿主 | **25+ 工具**(Agent Skills 开放标准,2025-12:Cursor/Codex/Gemini CLI/Copilot/Windsurf/Goose…) | Claude Code/Desktop/Cowork(ZCode 插件格式同构) | 一切 MCP 客户端(n8n/Cursor…) | 一切终端 | 一切 GitHub 用户 |
| 作者侧维护 | 最低 | 低(2 个 JSON) | 高(长驻进程/协议/鉴权) | 中 | 已有 |

## 为什么 Skill 是主形态

1. **本质匹配**:seo-suite = 知识(107 refs)+流程(模板)+本地纯 stdlib 计算(38 脚本)。MCP 的定义域是"连接 session 外部的数据/系统",而我们的脚本不需要长驻进程、不连付费 API。把 stdlib 脚本包进 MCP 反而丢掉最大优势——**脚本结果由 agent 自己的 LLM 判断和串联**(MCP 进程边界=智能边界,server 内无法复用外层 agent 的推理)。
2. **反例实证**:K-Dense-AI/claude-skills-mcp(把 skill 仓库包成 MCP 分发)已弃维护,弃维护理由即"Agent Skills 已被所有主流平台原生采纳"。Zilliz 先做 MCP 后补 CLI+Skills,公开复盘了 MCP 三条架构限制。
3. **市场现状**:现成 SEO MCP(Ahrefs/Semrush/SE Ranking/DataForSEO/GSC 社区版)全部是**付费数据 API 的封装**,没有一个提供审计方法论/工作流/报告模板——两个物种,不构成替代关系。

## 为什么加 Plugin 包装(本仓库已做)

`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` 两个文件把"clone+拷目录"升级为:

```bash
# Claude Code / ZCode(同构插件格式)
claude plugin marketplace add everyinfra/seo-skills   # 或 /plugin marketplace add everyinfra/seo-skills
claude plugin install seo-suite@everyinfra-seo-skills
# 更新
claude plugin update seo-suite@everyinfra-seo-skills
```

- 纯增量:skill/tests/workflows 原样复用,plugin 按 `skills/` 标准布局自动发现;
- 获得版本钉扎、依赖声明、`claude plugin validate --strict` CI 校验、未来捆绑 MCP/hooks 的能力;
- 流量实证:同类 claude-seo 以 plugin 形态 8 个月 18,626★;SE Ranking 官方 skills 仓库同构(插件内 `.mcp.json` 声明式捆绑官方 MCP,装完 OAuth 即用)。

## MCP 的正确用法:声明式接第三方,不自研 server

在 plugin 的 `.mcp.json`(未来按需加)声明接入**现成** SEO MCP(SE Ranking/Ahrefs/GSC 社区版),SKILL.md 写明"若用户配了数据源则优先取实时数据,否则走本地分析"。零 server 维护成本,补上实时数据短板,顺带覆盖 n8n/Cursor 等纯 MCP 客户端用户。只有当出现"必须由本套件自提供服务端计算"的需求时,才用纯 stdlib 手写薄 MCP(NDJSON+JSON-RPC,社区已有先例与教程),当前不存在此需求。

## 最终矩阵

| 用户 | 推荐入口 |
|---|---|
| Claude Code/ZCode 用户 | **Plugin 安装(首选)** 或裸 skill 拷贝 |
| Cursor/Codex/Gemini CLI 等其他 agent 用户 | 裸 skill(Agent Skills 开放标准,`~/.agents/skills/`) |
| 有 GSC/Ahrefs 等数据账号的用户 | Plugin + 第三方 MCP(数据层)+ 本套件(方法论层) |
| CI/定时审计 | 已有 `.github/workflows/seo-monitor.yml` |
| 非 agent 终端用户 | 不建 CLI——同类项目无一这么做且活得很好;`python3 scripts/*.py` 本身即 CLI |

## 维护注意

- 版本号与 CHANGELOG 同步更新 `plugin.json` 的 `version`;
- 每次 commit 前可跑 `claude plugin validate`(若本机有 Claude Code CLI)或依赖 CI;
- marketplace.json 的 plugins 列表新增 skill 时同步登记。
