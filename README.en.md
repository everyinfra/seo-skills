# EveryInfra SEO Skills

[简体中文](README.md) · [English](README.en.md)

**Free to download. Use your own AI tool and model.**

> Maintained by [EveryInfra](https://everyinfra.com/en). When a task needs live data, EveryInfra offers a [web search API](https://everyinfra.com/en/products/search) (17 tools) and [data APIs for 90 platforms](https://everyinfra.com/en/market); this Skill does not depend on them.

EveryInfra SEO Skills is version `0.35.0`, licensed under Apache-2.0. One SEO / GEO workbench Skill: `seo-suite` — instructions, reference notes and output templates. No model calls, no bundled provider, no API key, no runtime dependency. The model and its quota are whatever AI tool you already use.

**The differentiator: global SEO/GEO in one pass.** Teams shipping worldwide don't want a dozen single-market tools. This suite puts **18 language markets** in one workbench, scored market-by-market: Chinese, English, Russian (Yandex/Alice), Korean (Naver/AI Briefing), Japanese (Yahoo! Japan + Bing + AI Overviews), Spanish (es-419 LatAm splits), Portuguese (Brazil = ChatGPT's strongest market), Arabic (RTL + MSA vs dialects), French (Bill 96), German (DACH Sie/du), Indonesian (baku vs gaul), Hindi (Hinglish three-script reality), Italian (it-CH as its own locale), Turkish (a second Yandex market, ~26%), Vietnamese (diacritic variants + Coc Cốc), Thai (spaceless script segmentation), Polish (diacritic canonicalization), Dutch (Flemish nl-BE). Global capability is **woven into every capability set**, not a separate module — the spine is `overview/multilingual-workflow.md`.

## What only this suite ships

- **18 market portals.** `references/markets/` holds one portal per language market (zh, en, ru, ko, ja, es, pt, ar, fr, de, id, hi, it, tr, vi, th, pl, nl), each written from native-language research in October 2026: engine landscape, local tool stack, community intel, compliance notes.
- **Wikipedia-grade evidence discipline.** Claims carry source types and assertion half-lives; the skill never reports a signal that is not on the page and never promises ranking, traffic or AI-citation gains. GEO advice is bounded by an evidence-constraint file (`references/content/geo-evidence.md`); every Why-now number below has a registered source.
- **A self-updating intel loop.** `intel_check.py` monitors 18 upstream sources (engine blogs, robots and AI-crawler policies, agent specs, market-share trackers), re-pulls hash changes to confirm them, maps each real change to the affected reference files, and grades the required update P0–P3 under a written self-update protocol — the skill's facts are engineered to decay slower than the market's.
- **A monitoring daemon, not one-shot audits.** `monitor.py` runs daily four-question checks and weekly drift, keeps SQLite snapshots, and raises four-tier alerts with cooldown and anti-fatigue rules (plus SSRF and secret guards); `notify.py` fans notifications out across four channels by severity; GitHub Actions deployment templates are included.
- **CI gates for SEO.** A composite action at the repo root (`action.yml`) audits on every pull request, fails the build below a `min-score` threshold, and emits SARIF / JUnit / GitHub PR annotations via `ci_format.py` — SEO regressions surface like test failures.
- **A pipeline orchestrator.** `project.py` gives each site a workspace and a five-stage state machine (audit → prioritize → fix → verify → monitor): `run triage` chains crawl → audit → health score → priorities in one command, `next` prints the exact command to paste next, `status` shows the score trend. It orchestrates the other scripts as subprocesses and never reimplements them.

## How it got here (0.5 → 0.34)

One arc, compressed: the 0.5 series introduced the **market × capability dual-dimension architecture** — every task picks its market first, then routes by capability — with per-market deep-dives for all 18 markets and 23 cross-region fusion principles; 0.9 re-mined the 17 non-English markets in their own languages (a local community & information-source index, 14-market link-price bands, fusion principles grown to 27); 0.16–0.23 turned rules into code — stdlib-only scripts, the `markets.json` 18-market rule layer with dynamic `market_lint.py` checks, golden tests, the specialist modules and the 18 market portals; 0.24–0.30 added the monitoring daemon and the self-update loop; since 0.31 the executable layer has grown to **85 scripts and 1,604 golden tests** (self_check runs them all on every pass), plus the CI gates and the `project.py` orchestrator. Full history: [CHANGELOG.md](CHANGELOG.md).

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
| Yandex share in Turkey | ~26% (Sept 2026, up from ~13% in March; vs 3-5% in local measurement — conflicting calibers, both noted) — a second Yandex market | StatCounter (industry) |
| India ChatGPT adoption | ~100M weekly active users, ChatGPT's #2 market | OpenAI (Altman, official) |

## What it does

A single entry point: unified intake (site, market, goals, known issues, available data), then routing across five capability sets — overview / research / content / technical / monitoring — then structured output: conclusions, priorities, and how to validate each one. The target market is the first mandatory intake field, because it decides which engines, toolchains, thresholds and language conventions apply.

| Capability | Typical tasks |
|---|---|
| overview | Site-wide SEO diagnosis, roadmap and prioritization, triage when you don't know where to start, target-market intake gates |
| research | Keyword research and search intent (per-market toolchains + persona × intent SXO layer), SERP analysis (incl. per-market AI-Overview coverage and SERP occupancy), content gaps, competitors, directory-submission engine, backlink profile |
| content | SEO content briefs and drafting, titles and meta descriptions, GEO / AI-search visibility (incl. regional AI platforms), Chinese AI search, video SEO/GEO (YouTube citation mechanics, manual-caption layer), the five-rung ecommerce GEO ladder + on-site SEO for seven marketplaces (incl. MercadoLibre, Trendyol, Allegro, bol, Shopee), content quality, content refresh |
| technical | Technical SEO and single-page audits, robots.txt and AI-crawler policy (incl. regional crawlers, MistralAI, Bytespider), hreflang internationalization, structured data (incl. rich-result status), internal linking and site architecture, entity signals, programmatic SEO, Core Web Vitals, JS rendering and SPA SEO (five-engine rendering differences), Agent-Readiness protocol layer (ARD / WebMCP), server-log analysis (AI-visit measurement, a11y triage), attribution instrumentation |
| monitoring | Rank tracking, backlinks (incl. 14-market local link-price bands and risk table), brand mentions (four-tier citation ladder + per-market monitoring channels), algorithm-update attribution (official timelines and data files), SEO drift monitoring, metrics and reporting |
| **Specialist modules** | Domain strategy (selection, expired-domain due diligence, migration checklist, AI-citation inheritance), site-network spectrum and white-hat equivalents, 9-stage programmatic-SEO playbook, site-type playbooks (SaaS / ecommerce / media / local / docs / tools / marketplace / YMYL), CWV four metrics, mobile SEO, penalty recovery, redirects and canonicalization, UGC and site search |
| **Executable layer** | 85 stdlib scripts + the `markets.json` 18-market data layer (150 special checks) + 1,604 golden tests — the AI runs the scripts to get facts first, then interprets them per the capability files |

Global capability is **woven into every capability set**, not a separate module: [multilingual-workflow.md](skills/seo-suite/references/overview/multilingual-workflow.md) is the spine (market table, per-market tool stacks, language conventions, compliance), and each capability file carries the regional knowledge relevant to it.

**Bilingual by design.** The skill answers in the user's language and scores each language version of a multilingual site separately. One flagship: the [Chinese AI-search guide](skills/seo-suite/references/content/chinese-ai-search-guide.md), built on a measured 187,818-citation dataset — brand sites take only 1.37% of citations, 28 ranking sites take 9.1% of earliest positions; engine moats for Baidu AI / Tencent Yuanbao / Doubao / Kimi / DeepSeek; CJK thresholds and a 15-item readiness checklist.

Evidence-first: it never reports signals that are not on the page, and never promises ranking, traffic or AI-citation gains. No bundled data — bring your own GSC/GA4 exports; optional free APIs are yours to configure.

## What you bring

- An AI tool that supports Skills, with your own model configured.
- For data-dependent tasks, your own exports: Google Search Console, GA4, Bing Webmaster Tools, or rank-tracker / backlink / crawler exports from tools on your own accounts.
- Optional external APIs (e.g. PageSpeed Insights, Knowledge Graph Search) need your own keys — this repo ships none.
- Outbound actions (outreach email, publishing) are drafted by the skill and executed only after you confirm.

## 60-second taste

Zero dependencies, zero API keys — every script runs on the Python standard library alone. After cloning or unzipping, no install is needed: one command chain takes `example.com` through the minimal loop **audit → layered health score → fix plan**:

```bash
cd seo-skills/skills/seo-suite
python3 scripts/site_audit.py https://example.com --json > /tmp/audit.json
python3 scripts/health_score.py --input /tmp/audit.json
python3 scripts/fix_plan.py --audit /tmp/audit.json --estimate
```

Expected output, one line (measured): `main score 0.0 → Weak (example.com really lacks meta description/H1) · Lumar six-category composite 94.3 · AI Search Health 70/100 · fix_plan dry-run previews per-category fix artifacts + benefit estimate (writes nothing by default)`.

## Install

**Claude Code / ZCode (one line, recommended)** — this repo ships plugin manifests (`.claude-plugin/`, `.zcode-plugin/`):

```bash
claude plugin marketplace add everyinfra/seo-skills
claude plugin install seo-suite@everyinfra-seo-skills
```

**Any Agent Skills host (Codex, Cursor, Gemini CLI, Copilot, Windsurf, Goose, Amp, …):** the `install.sh` one-liner above auto-detects installed hosts and adapts to each, or copy `skills/seo-suite` into the tool's skills directory, e.g. `~/.agents/skills/`. Per-host directories and invocation cheat sheet: [HOSTS.md](HOSTS.md). Form-factor analysis: [PACKAGING.md](PACKAGING.md).

## Repo layout

```text
seo-skills/
├── README.md / README.en.md   Chinese original + this file
├── LICENSE / NOTICE / CHANGELOG.md
├── action.yml                 CI composite action (PR SEO gate)
├── install.sh                 One-command installer
└── skills/seo-suite/
    ├── SKILL.md               Entry point: intake, routing, script map
    ├── scripts/               85 stdlib scripts + markets.json (18-market rule layer)
    ├── tests/                 1,604 golden tests (self_check runs all)
    ├── examples/              Golden-sample outputs
    ├── references/
    │   ├── overview/          Capability map, routing, intake, multilingual spine
    │   ├── research/ content/ technical/ monitoring/
    │   └── markets/           18 language-market portals
    └── templates/             Research / audit / monitor output templates
```

## License & attribution

Apache-2.0. Framework points borrowed (summary + link, per NOTICE) from: AgriciDaniel/claude-seo, zubair-trabzada/geo-seo-claude, jianruntech/geo-score, Auriti-Labs/geo-optimizer-skill, coreyhaines31/marketingskills, flaqai/backlink_skills, alvinunreal/awesome-submitlist, indie-hacking/Awesome-SEO-Backlinks, OranAi-Ltd/orangeo-ai-visibility-skill, liangdabiao/GEO-Content-Optimizer-Skill, Ryze-AI-Adgent/open-seo-mcp-skills.
