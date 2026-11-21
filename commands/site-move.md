---
description: 改版、换域名、改 URL 结构前后对比:先存基线,改完对比出差异清单(漏 301、链式跳转、canonical 指旧址、hreflang 断簇)。Site migration protection.
argument-hint: "<旧站 URL> [新站 URL] [--map MIGRATION.md]"
---

# /seo-suite:site-move — 改版保护

参数:$ARGUMENTS。

## 先读
- `${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/references/lifecycle/loops-and-site-move.md`、`${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/references/technical/redirects-canonical.md`。
- 用户的映射表(`MIGRATION.md` 或 CSV);没有就问用户要,或先列出旧站全部 URL 让他补映射。

## 跑
1. 改动前:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/site_move.py" baseline --site <旧站> [--gsc-pages pages.csv] --out seo-ops/baselines/<日期>.json`。
2. 改完(本地预览加 `--allow-local`):`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/site_move.py" compare --baseline <基线> --new-site <新站> --map MIGRATION.md --md`。
3. 记进运营台账:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/onboard.py" event add migration --note "…"`。

## 停下来问用户
- 存基线之前确认是改动前的版本(不是已经改了一半)。
- compare 报 block 级问题时,逐条给证据和改法,问用户是否改完再上线;重定向改动开草稿 PR,不推主干。
