---
description: 例 1 第一屏:站点级任务先开局,读完产品后停下来问第 1 环,不先给建议
tags: [start, onboarding]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
expected_outcome: 跑 onboard.py start,列出带出处的产品草稿和第 1 环 ≤4 个问题,用 AskUserQuestion 停下;没有方案和优先级
---

用 seo-suite 帮我做 https://example.com 的 SEO。
