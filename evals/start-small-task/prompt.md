---
description: 例 7 小任务:改一个页面标题直接做,不走 6 环开局
tags: [start, small-task]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: 直接给出改短后的 title(或改文件),不跑 onboard.py
---

pricing.html 的 title 太长了,帮我改短一点,控制在 60 个字符以内:「EveryWidget Pricing — Plans, Prices, Free Trial, Enterprise Options and Frequently Asked Questions About Billing」
