# EveryInfra SEO Skills

[简体中文](README.md) · [English](README.en.md)

**Free to download. Use your own AI tool and model.**

EveryInfra SEO Skills is version `0.1.0`, licensed under Apache-2.0. The repository ships one SEO / GEO workbench Skill: `seo-suite`. It is a set of instructions, reference notes and output templates. It does not call a model, does not bundle a model provider, and has no API key or runtime dependency. Your own AI tool supplies the model and the model quota.

The Skill's instructions and reference notes are written in Simplified Chinese. Compatible AI tools can read them and answer in the user's language.

## What it is

`seo-suite` is a single entry point for SEO work. It starts with a shared intake (site, market, goals, known issues, available data), routes the task to one or more of five capability sets — overview, research, content, technical, monitoring — and returns findings, priorities and validation steps in a fixed structure.

It is evidence-first: it does not report signals that are not on the page, and it does not promise ranking, traffic or AI-citation gains. Advice on GEO (visibility in AI search) follows the evidence constraints in `references/content/geo-evidence.md`.

## SEO tasks it covers

| Capability set | Typical tasks |
|---|---|
| overview | Site-wide SEO diagnosis, roadmap and prioritization, triage when you do not know where to start |
| research | Keyword research and search intent, SERP analysis, content gaps, competitor analysis, alternative / vs page planning, topic clusters and content strategy |
| content | SEO content briefs and writing, titles and meta descriptions, GEO / AI search visibility, content quality review, refreshing decayed content |
| technical | Technical and on-page SEO audits, robots.txt and status codes, structured data (Schema), internal linking and site architecture, entities and knowledge graph, programmatic SEO, Core Web Vitals (LCP), reading audit-tool exports, SEO attribution tracking (GA4 / GTM) |
| monitoring | Rank tracking setup, backlink quality review and outreach drafts, SEO / GEO metrics, alert thresholds, performance reports |

## What you bring

- An AI tool that supports Skills, with a model you configure yourself.
- For data-driven tasks, your own data sources: exports from Google Search Console, GA4 or Bing Webmaster Tools, or from rank-tracking, backlink or crawler tools under your own accounts.
- Optional external APIs (for example PageSpeed Insights API or Knowledge Graph Search API) need your own key. This repository contains no keys and does not provide any.
- For outreach emails, publishing or other external actions, the Skill only drafts; you confirm and carry them out yourself.

## Install

Get the repository first: on the GitHub page use **Code → Download ZIP** and unpack it, or clone it:

```bash
git clone https://github.com/everyinfra/seo-skills.git
```

The commands below assume the folder is named `seo-skills`. A ZIP download may unpack as `seo-skills-main`; use the actual folder name.

### Codex (CLI / IDE)

Copy the whole `skills/seo-suite` folder into `~/.agents/skills/`:

```bash
mkdir -p ~/.agents/skills
cp -R seo-skills/skills/seo-suite ~/.agents/skills/
```

In Codex, invoke it with `$seo-suite`, or describe an SEO task and let Codex pick the Skill from its description. If it is not detected, restart Codex.

### Claude Code

Copy the whole `skills/seo-suite` folder into `~/.claude/skills/` (all projects) or into a project's `.claude/skills/` (that project only):

```bash
mkdir -p ~/.claude/skills
cp -R seo-skills/skills/seo-suite ~/.claude/skills/
```

In Claude Code, invoke it with `/seo-suite`, or describe an SEO task and let Claude Code pick the Skill from its description.

Other tools that support Skills can use the same folder in their documented Skill directory. See [Build skills — Codex](https://developers.openai.com/codex/build-skills) · [Extend Claude with skills](https://code.claude.com/docs/en/skills)

## Repository layout

```text
seo-skills/
├── README.md              Chinese README
├── README.en.md           English README
├── LICENSE                Apache-2.0 full text
├── NOTICE                 Attribution and third-party materials
├── CHANGELOG.md           Release notes
├── manifest.json          Package metadata
└── skills/
    └── seo-suite/
        ├── SKILL.md       Entry point: intake, routing rules, output structure
        ├── references/
        │   ├── overview/     Capability map, routing rules, intake checklists
        │   ├── research/     Search intent, SERP, content gaps, competitors, topic clusters, content strategy
        │   ├── content/      GEO evidence constraints, titles and meta, content structure, refresh
        │   ├── technical/    robots, status codes, Schema, linking and architecture, entities, performance, tracking
        │   └── monitoring/   Rank tracking, backlinks, metrics, reports, alerts
        └── templates/
            ├── research/     Research output templates
            ├── audit/        Audit output templates
            └── monitor/      Monitoring output templates
```

## Third-party materials

The notes in `references/` were written by EveryInfra. For some topics, the way the material is organized was informed by open-source projects and public documentation. This repository does not contain their text; it gives only our own summaries plus links to the originals, listed in the "来源" (Sources) section at the end of each file. See [NOTICE](NOTICE).

## Feedback

Please open [GitHub Issues](https://github.com/everyinfra/seo-skills/issues) for problems and suggestions. Do not post API keys, credentials, customer data or other confidential information.

## License

Apache-2.0. See [LICENSE](LICENSE).
