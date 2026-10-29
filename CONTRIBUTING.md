# Contributing: build this SEO / GEO Skill with us

[中文](CONTRIBUTING.zh-CN.md)

Search changes every month, and no single team knows all 18 markets from the inside. The people doing SEO in Seoul, São Paulo or Istanbul know things that never reach English blogs. If you know how search really works somewhere, put it here so others can use it. Your name stays on it.

You do not need to write code for most contributions.

## Ways to take part

| You have… | Do this |
|---|---|
| An idea, a question, or a market you know well | Start a thread in [Discussions → Ideas](https://github.com/everyinfra/seo-skills/discussions/categories/ideas), or open a **Propose a market, playbook or capability** issue |
| Advice in the Skill that is wrong or out of date | Open a **Wrong or outdated advice** issue with a dated source |
| A better step, check, template or example | Open an **Improve the Skill** issue, or send a pull request |
| A new market portal, playbook or script | Fork the repo and send a pull request |

Not sure where to start? Look at issues labelled [`help wanted`](https://github.com/everyinfra/seo-skills/labels/help%20wanted) or [`good first issue`](https://github.com/everyinfra/seo-skills/labels/good%20first%20issue).

## Where things live

```text
skills/seo-suite/SKILL.md                     # the entry point: intake, then routing
skills/seo-suite/references/markets/<lang>.md # one portal per language market (18 today)
skills/seo-suite/references/<area>/*.md       # overview / research / content / technical / monitoring
skills/seo-suite/scripts/*.py                 # standard-library-only Python tools
skills/seo-suite/tests/test_*.py              # tests; run_tests.py finds them automatically
```

- **New market:** copy the shape of an existing portal such as [ko.md](skills/seo-suite/references/markets/ko.md) and write what only applies in that market: engines, platforms, local channels, language conventions, local myths.
- **Facts need sources.** Every number, share, threshold or rule gets a source link and the date you checked it. Search changes fast; an undated claim cannot be maintained.
- **Scripts** use the Python standard library only and come with a test in `skills/seo-suite/tests/`.

## Ground rules

- **No secrets.** Never commit API keys, tokens, passwords or cookies. Use placeholders such as `YOUR_API_KEY`.
- **No client data.** Do not include real client sites' private data, Search Console exports or analytics.
- **Your own words.** Do not paste copyrighted text from books, courses or paid tools; summarise and link instead.
- **White-hat by default.** Grey-hat tactics may be described only to explain risks, as the existing references do.
- **License.** The Skill is [Apache-2.0](LICENSE). By sending a pull request you agree that your contribution is licensed under the same terms (Apache-2.0, section 5).

## Before you send a pull request

From the repository root (Python 3 only):

```bash
python3 .github/scripts/check_contribution.py
python3 skills/seo-suite/tests/run_tests.py
```

The first checks the manifest, front matter, links, JSON files and secrets in what you changed. The second runs the test suite (about a minute). Fix anything they list, then fill in the pull request template.

## How review works

- Maintainers review issues and pull requests by hand, regularly. Nothing is merged automatically.
- We may ask for a source, a change or a different shape. That is normal and is not a rejection.
- When your pull request is merged, you are added to [CONTRIBUTORS.md](CONTRIBUTORS.md). We are also adding a contributors section to [everyinfra.com](https://everyinfra.com).

Questions about contributing: ask in [Discussions](https://github.com/everyinfra/seo-skills/discussions).
