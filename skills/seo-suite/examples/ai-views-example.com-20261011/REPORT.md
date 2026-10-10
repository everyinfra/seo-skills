# example.com AI 视图层(离线重放):HTML 144→72 tokens(50.0% 缩减)、Markdown 视图 43 tokens——对标 Scrunch 98.9% **未达标,如实报**;产出只落本目录,**从不部署,人审后自行部署**

_For: 内容工程/前端 · 输入: inputs/example.com.html(2026-10-11 单次归档,sha256 25ddf2c8…,577 字节) · 工具: ai_views.py --html(离线重放,零网络) · 输出树: ai-views/example-com/(工具原样写盘) · 结构化输出: evidence/01_

> **快照免责声明**:输入 HTML 是 2026-10-11 的单点归档(example.com 内容可能变化);示例展示的是 AI 视图层的交付物形态,不代表目标站现状。

## The answer(先读这段)

对归档的 example.com HTML 跑 `ai_views.py --html --apply --json`(全程零网络):语义版 HTML **144 → 72 tokens(50.0% 缩减)**,另产 Markdown 视图 **43 tokens**(较原始 70.1%);净化只移除了 2 个块(内联 `<style>` 与 `<script src=/s.js>`)、丢弃 3 个 head meta/link 元素(charset/viewport/icon——骨架重发自带 charset),保留语义骨架与正文段(evidence/02)。**对标 Scrunch 官方实测 98.9% 未达标(`meets: false`,evidence/01)——原因是 example.com 本就几乎没有 chrome**(577 字节、单段正文),不是净化器失效;chrome 越重的页缩减空间越大。产出只写 `ai-views/` 隔离目录,**本工具从不部署**;部署由人审后自行完成(如挂 /ai/ 路径)。

## Key numbers(编号回溯)

| 数字 | 值 | 出处 |
|---|---|---|
| 原始 HTML tokens | 144(len(text)//4 口径,577 字节) | evidence/01 / 02 |
| ai-view HTML tokens / 缩减 | 72 / 50.0% | evidence/02 tokens.reduction_pct |
| Markdown 视图 tokens | 43(较原始 −70.1%,本行换算自 144/43) | evidence/02 |
| Scrunch 对标 | 98.9% vs 本例 50.0%,`meets: false` | evidence/01 benchmark 节 |
| blocks 净化计数 | 转换 0 / 移除 2 / 保留 1;属性剥离 0 项;head 元素移除 3 项 | evidence/02 blocks |
| meta 存留 | title "Example Domain";description/canonical/og 无(null/{}) | evidence/02 meta |
| 文件落点 | ai-views/example-com/{ai-view.html, ai-view.md, stats.json} | evidence/01 files |

## 净化前后对比(evidence/04,机器生成 diff)

原始页是"一行压平"的 HTML;净化后重排为缩进语义骨架——head 只剩 charset+title,style/script/icon/viewport 全部消失,正文 `<p>` 原样保留(evidence/04-before-after.diff 全文)。Markdown 视图两行:标题 + 正文一句(evidence/03)——语义内容零丢失,非内容字节全清。

值得注意的交叉印证:净化后 meta 只剩 title,**description 仍为 null、og 仍为空**——AI 视图层只能"减噪",不能"造门面";与 [envelope-chain 示例](../envelope-chain-example.com-20261011/REPORT.md)里 description/og 是 CRITICAL/WARN 发现互为印证:先修内容,再做视图层。

## "人审后部署"边界(本工具的定位纪律)

- **从不部署**:`--apply` 只写运行目录下的 `ai-views/` 隔离目录,不触碰站点文件;stats.json 与 --json 输出都带 `deploy: manual-only` 标记(evidence/01/02)。
- **人审后自行部署**:语义版 HTML/MD 交人审(核对净化是否误删业务内容),再自行挂载到如 `/ai/` 路径并决定 robots 对 AI bot 的放行策略——部署动作与责任在人,不在工具。
- **不承诺引用提升**:口径同全库——llms.txt 非可见性杠杆(Otterly 90 天 0.1% 请求率 / Ahrefs 13.7 万域 97% 整月零请求 / Google 官方"非必需",三份实证);AI 视图层同理,是"给 AI bot 的低噪版本",不是可见性保证。
- 本示例的 ai-views/ 输出树**永不部署**——它是交付物样例,不是站点变更。

## What could change this conclusion

- **50.0% 是"干净小页"的下界样本**:example.com 无导航/页脚/追踪脚本/内联事件,净化规则大部分没活干;同一工具对 chrome 重的真实页(数百 KB 模板)缩减会显著更高——不要把 50.0% 当作工具预期值,也不因此判定净化规则无效。
- token 口径是 len(text)//4 的估算,不是任何具体模型的 tokenizer 计数;不同模型真实 token 数会有偏移。
- 输入是单点归档;example.com 若改版(如补 description),meta 存留与 diff 形态都会变。
- `--diff`(版本间 section 变更清单)本例未演示——ai-views/ 无上一版本(`no-previous`);复跑第二次起可用。

## Methodology(脚本链与精确命令行;均在示例目录 examples/ai-views-example.com-20261011/ 下执行)

1. 归档输入(全链唯一一次网络):`curl -sS -o inputs/example.com.html https://example.com/`(200,577 字节;sha256 `25ddf2c883e0d1958ea971d279a7e4f0fd446724ee3db7db19dadabd4a62e484`;[envelope-chain 示例](../envelope-chain-example.com-20261011/REPORT.md)的 site_audit 不落盘原始 HTML,故单独归档一份供离线重放)
2. `python3 ../../scripts/ai_views.py --html inputs/example.com.html --apply --json > evidence/01-ai-views.json`(零网络;--apply 写 ai-views/example-com/ 三件套)
3. 原样复制工具落盘文件为编号证据:`cp ai-views/example-com/stats.json evidence/02-stats.json`、`cp ai-views/example-com/ai-view.md evidence/03-ai-view.md`
4. 机器生成净化前后对比:`diff -u inputs/example.com.html ai-views/example-com/ai-view.html > evidence/04-before-after.diff`(diff 退出码 1=有差异,即净化生效)

## Method Notes

- 三层结构:本 REPORT(叙事层)→ evidence/01-04(结构化输出/stats/视图/对比,原样落盘)→ inputs/example.com.html + ai-views/example-com/(原始输入与工具写盘树)。
- 口径:token=len(text)//4【工具自定,对标 Scrunch 官方实测 98.9%(123,916→1,355)】;净化规则(script/style/noscript/iframe/svg/注释/内联事件/data-*/表单交互全清,语义骨架保留)见 ai_views.py 模块 docstring。
- 禁编造:144/72/43/50.0%/meets:false/块计数全部出自 evidence/01-02;−70.1% 一行是 144→43 的换算,已注明。
