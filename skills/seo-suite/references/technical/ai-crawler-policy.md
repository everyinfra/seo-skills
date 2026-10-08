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

## 三、区域引擎的爬虫与收录补充(2026-10-08 并入)

Google/OpenAI/Anthropic/Perplexity 之外,多个市场有独立的收录与 AI 答案通道:

| 市场 | Bot / 机制 | 行为(来源类型) | 决策 |
|---|---|---|---|
| 俄语区 | **`YandexAdditional`** | 供 Yandex 生成式答案(Нейро/Alice AI)取内容;是**唯一文档化的退出控制**——`User-agent: YandexAdditional / Disallow: /` 即退出;Forbes RU 等媒体已用此退出(Yandex 官方;案例 SEONews) | 想进俄语 AI 答案池=显式允许;与 GPTBot 等政策**分开决策** |
| 俄语区 | Yandex 主爬虫 | 经典收录走 YandexBot;**IndexNow**(Yandex 参与协议)可加速抓取(官方) | 俄语区把 IndexNow 纳入新鲜度策略 |
| **土耳其** | Yandex 系(同俄语区) | **Yandex 在土份额 ~26%(2026-09 StatCounter;3 月 ~13%,大反弹)**,YandexGPT SERP 答案同样存在 | 土耳其=第二个 Yandex 市场:Webmaster 注册与 YandexAdditional 决策同俄语区逻辑,且需 Google+Yandex 双引擎 |
| 韩语区 | Naver robot 收录 | 外部站需在 Search Advisor 发起 robots 收录请求;外部博客仅经收录后才出现在 Blog 标签(Naver 官方 Help) | 韩语流量前提是"被 Naver 收",不是"被爬" |
| 日语区 | bingbot | Bing 在日份额 28–33%(StatCounter),喂 Copilot 检索 | 日语区 Bing WMT 验证与可爬探测为必做项(多数市场可选项) |
| 越南 | Coc Cốc | 本地引擎 ~6% 份额,浏览器自带 AI 聊天机器人(官方 Play 页) | 越南向流量单独提交 Coc Cốc 收录 |
| 中文 | `Baiduspider` / `Bytespider` | 见中文 AI 搜索指南 | 中文站确认未被禁 |

**llms.txt 在区域市场的证据状态**:Yandex 无消费证据(俄社区视为仅策展);日本企业采用 6.4–6.8%(2026-09 测)但 John Mueller 明示无 AI 系统当前使用——**一切市场都只作低成本对冲,不承诺引用**。

## 四、暗坑清单

1. **WAF/CDN 拦截**：robots 宽松但 Cloudflare 等按 UA 挑战 AI bot——活体探测（发真实 bot UA）才能发现。robots.txt 只说"允不允许"，不说"到没到得了"。
2. **`Google-Extended` 误解**：它不是 AIO 开关。
3. **`GPTBot` 误解**：它不是 ChatGPT 引用开关。
4. **ai.txt / GEO link tags**：尚无引擎公开承诺遵守；有则加分，无则不扣。
5. **robots 与 llms.txt 矛盾**：llms.txt 列出的页对 AI 爬虫禁抓——白做一半。

## 五、探测方法

对每个引用型 bot：用其真实 UA string `curl -A` 访问首页与一个深页，记录状态码。200 = 可达；403/429/5xx/挑战页重定向 = 被拦。对照 robots 声明，标注"声明允许但实际被拦"的项——这类项修复收益最高（WAF 白名单一行的事）。

## 六、来源

- 27 bot 引用/训练分类+频率：[Auriti-Labs/geo-optimizer-skill](https://github.com/Auriti-Labs/geo-optimizer-skill) `docs/ai-bots-reference.md`
- 厂商官方行为声明（OAI-SearchBot/SearchBot/User 系）：[jianruntech/geo-score](https://github.com/jianruntech/geo-score) `reference/platform-source-selection.md`（2026-10-04 复核一手文档）
- 区域补充：Yandex Webmaster 官方文档（YandexAdditional）；SEONews（俄媒体退出案例）；Naver 官方 Help（robots 收录）；StatCounter（Bing 日本份额）；PR Times（llms.txt 日企采用率）
