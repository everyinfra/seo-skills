# EveryInfra SEO Skills

[简体中文](README.md) · [English](README.en.md)

**Free to download. Use your own AI tool and model.**

EveryInfra SEO Skills is version `0.13.0`, licensed under Apache-2.0. One SEO / GEO workbench Skill: `seo-suite` — instructions, reference notes and output templates. No model calls, no bundled provider, no API key, no runtime dependency.

**The differentiator: global SEO/GEO in one pass.** Teams shipping worldwide don't want a dozen single-market tools. This suite puts **18 language markets** in one workbench, scored market-by-market: Chinese, English, Russian (Yandex/Alice), Korean (Naver/AI Briefing), Japanese (Yahoo! Japan + Bing + AI Overviews), Spanish (es-419 LatAm splits), Portuguese (Brazil = ChatGPT's strongest market), Arabic (RTL + MSA vs dialects), French (Bill 96), German (DACH Sie/du), Indonesian (baku vs gaul), Hindi (Hinglish three-script reality), Italian (it-CH as its own locale), Turkish (a second Yandex market, ~26%), Vietnamese (diacritic variants + Coc Cốc), Thai (spaceless script segmentation), Polish (diacritic canonicalization), Dutch (Flemish nl-BE). Global capability is **woven into every capability set**, not a separate module — the spine is `overview/multilingual-workflow.md`.

**The 0.5 series: market × capability dual-dimension architecture + per-market deep-dives for all 18.** Every task picks its market first, then routes by capability. `multilingual-workflow.md` carries the **18-market unique-methods index** (what only works/matters in each market — e.g. WeChat Peoplerank & XHS CES score for Chinese, Korea's `nosourceinfo` official AI-citation opt-out, Brazil's Reclame Aqui cited by 22.3% of ChatGPT brand answers, Japan's "AI-flavor" density lint, Thailand's `Intl.Segmenter` word-segmentation settlement) and **23 cross-region fusion principles** (assertion half-life, conflict-noting discipline, sovereign-assistant pattern, register-duality template, etc.).

**The 0.9 local-community round: what only locals know.** All 17 non-English markets re-mined in their own languages — the spine gains a **local community & information-source index** (per market: where locals learn, insider consensus, international misconceptions corrected): Russia's 76-item commercial-factors checklist and region codes, Korea's posting timetable, Japan's internal-link conventions and the 10x SEO-vs-MEO price gap, Germany's Abmahnung legal risk, Turkey's tanıtım yazısı link market, Thailand's grey-hat red lines, France's one-year AIO head start; a **14-market link-price band table** (from 1,500 VND/link in Vietnam to €5,000 in Spanish top media), **seven marketplace in-store SEO forks**, fusion principles extended to 27.

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

Global-market why-now (0.4–0.5 series, source type noted):

| Metric | Value | Source |
|---|---|---|
| Yandex share of Russian search | ~70-73% (2026) | StatCounter (industry) |
| AI answers covering RU informational queries | 68% | applabx (industry study) |
| Naver share in Korea | ~63-64% on the domestic panel (statistical tie with Google on StatCounter) | InterAd/InternetTrend (industry) |
| Korean AI Briefing citation pool | almost exclusively Naver-owned properties | Andgentic (industry) |
| AI Overviews appearing on Japanese queries | 76.9% (1,459 queries measured) | Itera (industry) |
| Japan AI-search usage | 21.3% (May 2025) → 37.0% (Feb 2026) | CyberAgent GEO Lab |
| Brazil ChatGPT adoption | 25.5% of the population uses the app (highest globally), ~50M monthly users | StatCounter/OpenAI |
| Language-bound AI citations for Spanish queries | 83-84% Spanish-language sources | Temso (industry study) |
| Non-English SEO skill supply | top Spanish/Brazilian/French/Indonesian repos have 1-5 stars | GitHub API, Oct 2026 |
| Yandex share in Turkey | ~26% (Sept 2026, up from ~13% in March) — a second Yandex market | StatCounter (industry) |
| India ChatGPT adoption | ~100M weekly active users, ChatGPT's #2 market | OpenAI (Altman, official) |

## What it does

A single entry point: unified intake (site, market, goals, known issues, available data), then routing across overview / research / content / technical / monitoring, then structured output (Summary, Findings, Priority, Actions, Validation).

**Bilingual by design.** The skill answers in the user's language and scores each language version of a multilingual site separately. Unique capability: a [Chinese AI-search guide](skills/seo-suite/references/content/chinese-ai-search-guide.md) built on a measured 187,818-citation dataset — brand sites take only 1.37% of citations; 28 ranking sites take 9.1% at the earliest positions; engine moats for Baidu AI / Tencent Yuanbao / Doubao / Kimi / DeepSeek; CJK thresholds and a 15-item readiness checklist.

| Capability | Typical tasks |
|---|---|
| overview | Site-wide diagnosis, roadmap, triage, multilingual workflow (the global backbone: market table, per-market toolchains, compliance), target-market intake gates |
| research | Keywords & intent (with per-market toolchains: Wordstat, DataLab, ラッコ), SERP, content gaps, competitors, alternative/vs pages, backlink profile analysis (7-section framework), graded directory, directory-submission engine |
| content | Briefs, E-E-A-T, GEO citability scoring, llms.txt authoring/validation, AI platform differences (incl. regional AI platforms: Yandex Alice/Neuro, Naver AI Briefing, Japanese AIO), Chinese AI search |
| technical | Audits, schema, robots + AI crawler policy (incl. YandexAdditional, Naver collection, Bing Japan), hreflang 8-check (incl. es-419, RTL), programmatic SEO gates, sitemaps |
| monitoring | Rank tracking, KPIs, alerts, brand mention monitoring, SEO drift monitoring |

Global capability is **woven into every capability set**, not a separate module: `overview/multilingual-workflow.md` is the spine (engine landscape, per-market tool stacks, language conventions and compliance across markets), and each capability file carries the regional knowledge relevant to it.

Evidence-first: never reports signals that are not on the page; never promises ranking, traffic or AI citation gains. No bundled data — bring your own GSC/GA4 exports; optional free APIs are yours to configure.

## License & attribution

Apache-2.0. Framework points borrowed (summary + link, per NOTICE) from: AgriciDaniel/claude-seo, zubair-trzada/geo-seo-claude, jianruntech/geo-score, Auriti-Labs/geo-optimizer-skill, coreyhaines31/marketingskills, flaqai/backlink_skills, alvinunreal/awesome-submitlist, indie-hacking/Awesome-SEO-Backlinks, OranAi-Ltd/orangeo-ai-visibility-skill, liangdabiao/GEO-Content-Optimizer-Skill, Ryze-AI-Adgent/open-seo-mcp-skills.
