# examples/ 规范(详版见 [README.md](README.md))

1. 目录命名 `{脚本链}-{目标}-{YYYYMMDD}/`(如 `site-audit-chain-example.com-20261010`);合成演示可省目标段(`citation-panel-demo-20261010`)。
2. 三层结构:REPORT.md(verdict-first,数字全部可回溯)→ evidence/ 按步骤编号(01-、02-…,原样落盘永不手改)→ 原始数据层(panel.json/runs/inputs 等自带的输入与中间产物)。
3. REPORT.md 必带 Methodology 节(脚本+精确命令行)与快照免责声明;合成数据必须在首段显式声明。
4. 只展示真实产出:零发现的"全绿站点基线报告"也是有效示例;绝不虚构 finding,数字缺失写 [要追加: 数据源]。
5. 新增示例:真实跑一遍脚本链 → 原样落盘 evidence → 写 REPORT → 在 README.md 索引表加一行;跑 `python3 scripts/self_check.py` 确认不破坏检查。
