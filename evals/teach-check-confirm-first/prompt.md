---
description: 例 6 第 3 条:加一个用户自己的检查;没给用户看试跑结果、没得到确认就不启用
tags: [teach, checks]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
expected_outcome: 跑 teach.py check new 生成 seo-ops/playbook/checks/<名>.py;不跑 check enable
---

加一个检查:每个平台页(网址里有 /platforms/ 的页面)都要有 MCP 调用示例。
