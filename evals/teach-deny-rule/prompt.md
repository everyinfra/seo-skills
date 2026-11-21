---
description: 例 6 第 2 条:用户说不做某类外链,写进 rules.md 和结构化禁用清单
tags: [teach]
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: 跑 teach.py rule add --deny reddit,seo-ops/playbook/rules.md 有原话,deny.json 有 reddit
---

以后别再建议我们去做 Reddit 外链了,我们不做。记下来,以后都按这个来。
