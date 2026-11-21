---
description: 上线前清单(每项有负责人):在本地预览或预发站上跑 robots、sitemap、canonical、hreflang、结构化数据、分享卡片、速度。Pre-launch SEO checklist.
argument-hint: "<预览 URL> [--prod-host example.com]"
---

# /seo-suite:launch — 上线清单

参数:$ARGUMENTS(预览、预发或正式站地址;本机预览要 `--allow-local`)。

## 先读
- `${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/references/lifecycle/stage-1-prelaunch.md`(上线清单每一项的为什么和怎么修)。
- `seo-ops/playbook/` 的规则(用户说过上线必须检查的东西)。

## 跑
- `python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/launch_check.py" --url <预览 URL> [--allow-local] --prod-host <正式域名> --ws seo-ops --md`。
- 有已启用的自定义检查:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/teach.py" check run --url <页面> … [--allow-local]`,结果并进清单。
- 上线前存基线:`python3 "${CLAUDE_PLUGIN_ROOT}/skills/seo-suite/scripts/site_move.py" baseline --site <URL> --out seo-ops/baselines/<日期>.json`。

## 停下来问用户
- 清单里每个 block 项:给出证据和改法,问谁负责、什么时候改;不替用户提交 GSC / Bing 验证。
- 要改 robots、noindex、canonical、重定向:开分支、开草稿 PR,不推主干。
