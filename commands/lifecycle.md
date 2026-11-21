---
description: 产品在哪个阶段、5 维成熟度各几级、最该补哪一格、下一件事。Diagnose lifecycle stage and maturity.
argument-hint: "[--ws seo-ops]"
---

# /seo-suite:lifecycle — 阶段 × 成熟度诊断

## 先读
- `${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/references/overview/lifecycle-stages.md`(6 个阶段的判断依据、门槛、5 维 × 5 级判据)。
- `seo-ops/context/profile.json`(没有就先 `/seo-suite:start`)和 `seo-ops/playbook/` 里的规则。

## 跑
- `python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/lifecycle.py" diagnose --ws seo-ops`(有 GSC 数据包时加 `--metrics m.json`)。
- 一屏写:阶段(判断依据和证据)、5 维各几级(每级的依据,缺证据的写「未知」和缺什么)、最该补的一格、下一件事。
- 用户在 `seo-ops/playbook/lifecycle.json` 改过阈值就按他的;改阈值不改 skill 本体。

## 停下来问用户
- 阶段是脚本猜的(没 GSC、没确认)时,把判断依据给用户,问对不对,再按确认后的阶段出下一件事。
- 阶段变了(比如刚上线 → 增长期),问用户要不要换打法、重排路线(`onboard.py answer --ring 1 --correct stage=N`)。
