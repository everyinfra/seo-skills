# AI 爬虫政策参考（robots.txt 决策）

> 建立于 2026-10-09。bot 分类与频率参考 [Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) `docs/ai-bots-reference.md`（27 bot 表）与 [jianruntech/geo-score](https://github.com/jianruntech/geo-score)。按本套件证据约束改写。
> 用途：回答"我该在 robots.txt 里允许/禁止哪些 AI 爬虫"这个具体问题。

## 一、先分清两类 bot（最常见错误在这里）

**引用型（影响搜索/答案系统）**：

| Bot | 归属 | 用途 | 频率 |
|---|---|---|---|
| `OAI-SearchBot` | OpenAI | ChatGPT 搜索索引 | 日频 |
| `ChatGPT-User` | OpenAI | 按用户请求抓取 | 按需 |
| `Claude-SearchBot` | Anthropic | Claude 搜索索引 | 按需 |
| `Claude-User` | Anthropic | 按用户请求抓取 | 按需 |
| `PerplexityBot` | Perplexity | 搜索/链接（不训练） | 每周数次 |
| `Perplexity-User` | Perplexity | 按用户请求 | 按需 |
| `Googlebot` | Google | 通用收录+AIO | 高频 |
| `Applebot` | Apple | Siri/Spotlight | 日频 |

**训练型（基础模型训练，不影响搜索答案）**：`GPTBot`、`ClaudeBot`、`CCBot`（Common Crawl）。

**关键事实**：**禁 `GPTBot` 不阻止 ChatGPT 引用你**——引用走 `OAI-SearchBot`。大量站点把两者搞混，想保留引用却把训练 bot 的规则套在搜索 bot 上，或反之。Copilot 无独立 bot，读 Bing 索引。

## 二、四种典型诉求的配置

### 1. 全开放（默认推荐）

```
User-agent: *
Allow: /
```

不写任何 AI 专属规则。想保留训练型抓取也开放。

### 2. 保留 AI 搜索引用、退出模型训练

```
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: CCBot
Disallow: /
```

引用型 bot 不动。注意 `ChatGPT-User` / `Perplexity-User` 官方声明"可能无视 robots"——按请求抓取类的 bot 多数厂商声明不受 robots 约束，这是行业现状而非配置错误。

### 3. 退出特定引擎的搜索答案

- **ChatGPT**：禁 `OAI-SearchBot`（官方：禁它 = 从搜索答案消失）
- **Google AIO**：用 Search Console → 设置 → Search generative AI 开关（**`Google-Extended` 不控制 AIO**，只管 Gemini 训练——第二个高频错误）
- **Perplexity**：禁 `PerplexityBot`

### 4. 完全退出所有 AI

逐家做 2+3；并接受 `*-User` 类 bot 可能继续按单用户请求访问。**没有一键全退**。

## 三、暗坑清单

1. **WAF/CDN 拦截**：robots 宽松但 Cloudflare 等按 UA 挑战 AI bot——活体探测（发真实 bot UA）才能发现。robots.txt 只说"允不允许"，不说"到没到得了"。
2. **`Google-Extended` 误解**：它不是 AIO 开关。
3. **`GPTBot` 误解**：它不是 ChatGPT 引用开关。
4. **ai.txt / GEO link tags**：尚无引擎公开承诺遵守；有则加分，无则不扣。
5. **robots 与 llms.txt 矛盾**：llms.txt 列出的页对 AI 爬虫禁抓——白做一半。

## 四、探测方法

对每个引用型 bot：用其真实 UA string `curl -A` 访问首页与一个深页，记录状态码。200 = 可达；403/429/5xx/挑战页重定向 = 被拦。对照 robots 声明，标注"声明允许但实际被拦"的项——这类项修复收益最高（WAF 白名单一行的事）。

## 五、来源

- 27 bot 引用/训练分类+频率：[Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) `docs/ai-bots-reference.md`
- 厂商官方行为声明（OAI-SearchBot/SearchBot/User 系）：[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `reference/platform-source-selection.md`（2026-10-04 复核一手文档）
