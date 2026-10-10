# 宿主适配指南(Host Adaptation Guide)

> 建立 2026-10-10,基于 9 个宿主官方文档 + 本机实证核对(来源见文末)。结论先行:**SKILL.md 本体零适配**(Agent Skills 开放标准),适配全部在"目录布局 + 分发通道"两层——本仓库已为每个宿主做了对应处理。

## 一张表看懂:哪个目录被谁读

```
~/.agents/skills/seo-suite/          ← 真源(install.sh 装在这里)
  ├── Codex / Cursor / Gemini CLI / Goose / Amp / VS Code Copilot / ZCode 直读
  ~/.claude/skills/seo-suite         ← symlink → 真源(Claude Code 专用目录)
  ~/.copilot/skills/seo-suite        ← symlink(Copilot 首选目录)
  ~/.codeium/windsurf/skills/…       ← symlink(Windsurf/Devin)
  ~/.config/agents/skills/…          ← symlink(Amp 最高优先级)
  ~/.kiro/skills/…                   ← symlink(Kiro)
  ~/.cursor/skills/…                 ← symlink(可选,Cursor 同步 Cloud Agents 需要)
  ~/.gemini/skills/…                 ← symlink(可选,~/.agents 别名已生效)
```

`install.sh` 自动探测已安装的宿主并为它们建入口;`--all` 装全部;`--agent claude,codex` 指定;`--uninstall` 清除。

## 逐宿主适配说明

| 宿主 | 安装后调用 | 验证 | 本仓库的适配 | 注意事项 |
|---|---|---|---|---|
| **Claude Code** | `/seo-suite` 或自动匹配;Plugin 形态 `/plugin install seo-suite@everyinfra-seo-skills` | 重启会话 → `/skills`;`/doctor` | `.claude-plugin/plugin.json` + `marketplace.json` | claude.ai 上传打包只允许 6 个 frontmatter 字段——我们 SKILL.md 的 `metadata` 是标准字段,安全 |
| **Codex** | `$seo-suite` 显式;`/skills` 选择器;隐式匹配 | `/skills` | 直读 `~/.agents/skills` | 技能列表有上下文预算(约 2%/8000 字符),描述超长会被截断甚至省略——我们 description 已控制在 1024 内且关键词前置 |
| **Cursor** | chat 输入 `/seo-suite`(挂单条消息);`Option/Alt+Enter` 挂整会话 | Customize → Skills 面板 | 直读 `~/.agents/skills`;`~/.cursor/skills` 可选链接(同步 Cloud Agents 需要) | 仓库内任意嵌套位置递归发现 skill |
| **VS Code / Copilot** | chat `/seo-suite`(可带参数) | chat 输入 `/skills` | 读 `~/.copilot` `~/.claude` `~/.agents` 三处 | name 非法字符会静默加载失败——`seo-suite` 纯小写连字符 |
| **Gemini CLI** | 自动匹配 → `activate_skill` | `/skills list` | 直读 `~/.agents/skills`(别名优先) | 首次激活弹目录授权确认,属正常流程 |
| **Windsurf** | `@seo-suite` | Cascade 面板 ⋯ → Skills | `~/.codeium/windsurf/skills` 链接 | 与 Devin CLI 共享目录 |
| **Goose** | 自然语言点名 / `/skills` | `goose skills list` | 直读 `~/.agents/skills` | 兼容读 `.goose/.claude` 目录 |
| **Amp** | 自然语言 | `amp skills list` | `~/.config/agents/skills` 链接(最高优先级) | 特色:skill 可带 `mcpServers` frontmatter 声明 skill 级 MCP |
| **Kiro** | `/seo-suite`(带参数;`$ARGUMENTS` 仅 CLI) | 面板 Agent Steering & Skills | `~/.kiro/skills` 链接 | 全局 skill 不上 Web/Mobile;custom agent 需 `skill://` 声明 |
| **ZCode** | Skill 工具按名调用;插件 skill `plugin:skill` 形式 | 新会话 skill 列表 | `.zcode-plugin/plugin.json` 薄清单;直读 `~/.agents/skills`;插件市场兼容 Claude 插件源 | 本机实证:ZCode 可直接挂载 `anthropics/claude-plugins-official` |

## SKILL.md 的跨宿主纪律

- **不加宿主专属 frontmatter 字段**:本地 Claude Code 会忽略未知字段,但 claude.ai 打包是硬错误;宿主专属元数据一律放 sidecar(OpenAI 用 `agents/openai.yaml`,ZCode 用 `.zcode-plugin/`,Claude 用 `.claude-plugin/`)。
- **标准 `metadata:` map 是唯一全宿主安全的自定义位**——我们在这里声明 `adapted-hosts`。
- **description ≤1024 且关键词前置**(Codex 预算/截断);**name 纯小写连字符且与目录同名**(VS Code 静默失败/Kiro 强校验)。
- 纯 stdlib 脚本在所有宿主都能由 agent 执行(权限模型不同,首次会请求确认)。

## 分发通道对照

| 通道 | 覆盖 | 状态 |
|---|---|---|
| Plugin/Marketplace(Claude Code) | Claude Code + ZCode(同构/直挂) | ✅ `.claude-plugin/` 已建 |
| `.zcode-plugin/` | ZCode 原生插件形态 | ✅ 薄清单已建 |
| 裸 skill + install.sh | 全部 10 宿主 | ✅ 多宿主安装器 |
| GitHub Actions | CI/定时审计人群 | ✅ `seo-monitor.yml`/`intel-update.yml` |
| MCP | 数据接口层(不自研 server) | 规划中:插件内 `.mcp.json` 声明式接第三方 |

## 来源

- Agent Skills 规范: agentskills.io/specification(name≤64/description≤1024/license/compatibility/metadata)
- Claude Code: code.claude.com/docs/en/skills · Codex: developers.openai.com/codex/build-skills · Cursor: cursor.com/docs/skills · VS Code: code.visualstudio.com/docs/agent-customization/agent-skills · GitHub: docs.github.com/en/copilot/concepts/agents/about-agent-skills · Gemini CLI: geminicli.com/docs/cli/skills · Windsurf: docs.windsurf.com/windsurf/cascade/skills · Goose: goose-docs.ai · Amp: ampcode.com/docs/customize/skills · Kiro: kiro.dev/docs/skills
- 本机实证:`~/.agents/skills/`(skills CLI 的 `.skill-lock.json` 管理,ZCode 实际加载源)、`~/.zcode/cli/plugins/`(known_marketplaces.json 含 GitHub 源)等
