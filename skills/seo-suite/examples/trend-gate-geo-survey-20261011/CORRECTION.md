# 修正:热点必须监控"产品垂直",不是"SEO/GEO 元领域"

> 2026-10-11 用户指正后修正。本示例目录最初的 topics.txt 用了 SEO/GEO 关键词——
> 那是本套件自己的元领域,示范了"做 SEO 的人蹭 SEO 的热点",不是目标场景。
> 正确场景:**监控与目标网站/产品所在行业相关的热点**,蹭的是产品垂直的趋势。

## 正确配置(product-vertical-config.json)

- `vertical_tokens`:**三层词表**——品类词(infrastructure/agents/MCP/devtools)+品牌词(自家产品名)+竞品词(对手产品名);配竞品词后竞品动态(发版/融资/事故)自动成为高相关信号
- `reddit_subs`:按垂直选版块(devops/LocalLLaMA/selfhosted),不是默认的 technology
- `wire_domains`:垂直权威媒体,用于硬新闻否决

## 顺带修掉的真实缺陷

词组全匹配把 "Claude Agent SDK vs LangGraph vs CrewAI" 漏成 Q1=0(每个含 agent
的 token 都是双词组,"AI agents" 要求 ai+agent 同时出现)。已加**词干级三档匹配**:
词组全命中 25 / token 全词命中 10 / 显著单词命中各 10 且≥2 个不同垂类词升 HIGH——
该信号现为 25(HIGH)。
