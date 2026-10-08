# EveryInfra SEO Skills

[简体中文](README.md) · [English](README.en.md)

**Free to download. Use your own AI tool and model.**

EveryInfra SEO Skills is version `0.3.0`, licensed under Apache-2.0. One SEO / GEO workbench Skill: `seo-suite` — instructions, reference notes and output templates. No model calls, no bundled provider, no API key, no runtime dependency.

**Install (one command):**

```bash
curl -fsSL https://raw.githubusercontent.com/everyinfra/seo-skills/main/install.sh | bash
```

## Why now

> All figures sourced; source register lives in `skills/seo-suite/references/content/geo-platform-differences.md`.

| Metric | Value |
|---|---|
| GEO services market | $850M → $7.3B by 2031 |
| AI-referred traffic growth | +527% YoY |
| AI traffic conversion vs organic | 4.4x |
| Gartner: traditional search traffic by 2028 | -50% |
| Brand mentions vs backlinks correlation for AI ranking | ~3x |
| GEO-optimized content visibility gain (KDD 2024, 10K queries) | +30-115% |
| Marketers currently investing in GEO | only 23% |

## What it does

A single entry point: unified intake (site, market, goals, known issues, available data), then routing across overview / research / content / technical / monitoring, then structured output (Summary, Findings, Priority, Actions, Validation).

**Bilingual by design.** The skill answers in the user's language and scores each language version of a multilingual site separately. Unique capability: a [Chinese AI-search guide](skills/seo-suite/references/content/chinese-ai-search-guide.md) built on a measured 187,818-citation dataset — brand sites take only 1.37% of citations; 28 ranking sites take 9.1% at the earliest positions; engine moats for Baidu AI / Tencent Yuanbao / Doubao / Kimi / DeepSeek; CJK thresholds and a 15-item readiness checklist.

| Capability | Typical tasks |
|---|---|
| overview | Site-wide diagnosis, roadmap, triage, multilingual workflow |
| research | Keywords & intent, SERP, content gaps, competitors, alternative/vs pages, backlink profile analysis (7-section framework), graded directory, directory-submission engine |
| content | Briefs, E-E-A-T, GEO citability scoring, llms.txt authoring/validation, AI platform differences, Chinese AI search |
| technical | Audits, schema, robots + AI crawler policy, hreflang 8-check, programmatic SEO gates, sitemaps |
| monitoring | Rank tracking, KPIs, alerts, brand mention monitoring, SEO drift monitoring |

Evidence-first: never reports signals that are not on the page; never promises ranking, traffic or AI citation gains. No bundled data — bring your own GSC/GA4 exports; optional free APIs are yours to configure.

## License & attribution

Apache-2.0. Framework points borrowed (summary + link, per NOTICE) from: AgriciDaniel/claude-seo, zubair-trzada/geo-seo-claude, jianruntech/geo-score, Auriti-Labs/geo-optimizer-skill, coreyhaines31/marketingskills, flaqai/backlink_skills, alvinunreal/awesome-submitlist, indie-hacking/Awesome-SEO-Backlinks, OranAi-Ltd/orangeo-ai-visibility-skill, liangdabiao/GEO-Content-Optimizer-Skill, Ryze-AI-Adgent/open-seo-mcp-skills.
