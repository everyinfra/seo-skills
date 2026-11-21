---
description: 例 6:禁了 Reddit 外链以后,每周运营单的推荐和本周路线项里不再出现 Reddit
tags: [weekly]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: 跑 project.py ops weekly --no-net --date 2030-01-07;agenda.md 的「本周只做这一件」和路线项里没有 Reddit
---

出这周的 SEO 运营单。离线跑就行(--no-net),日期用 2030-01-07。
