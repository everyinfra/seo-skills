# 审计规则目录 · HTML Validation

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### HTML Validation(11 条,权重 2%)

缺 DOCTYPE=**fail**(任何 DOCTYPE 都过);缺 charset(utf-8 须 head 首位)=warn/fail;head 含非法元素=warn(白名单:meta/title/link/script/style/base/noscript;读的是served 源码,因为解析后的 DOM 已把它们挪进 body);head 内 noscript 仅当含 link/style/meta 以外元素时 warn;多 head=fail;**HTML 体积 >250KB 警、>500KB 败、~2MB 以上 Googlebot 可能只索引前段**;lorem ipsum=**fail**;多 title=**fail**;多 description=**fail**;title 在 head 外=fail;base 元素(href 空/畸形/非 HTTP(S)=fail,多条=warn,须 ≤1 条)。

**解释层(5 条,第三批;ID 未公布原文的按家族命名法推得并标 [待核])**

#### htmlval-document-structure [待核 ID]
- 名称/类型: 文档结构家族(源表 ID `htmlval-missing-doctype` fail、`htmlval-missing-charset` warn/fail、`htmlval-multiple-heads` fail) —— issue/warning · 优先级 medium · 输出 CRITICAL(缺 DOCTYPE、多 head,源表 fail)/WARN(charset 位置)
**这意味(what)**: 文档骨架错:没有 DOCTYPE、charset 声明不在 head 首位(utf-8 须 head 首位)、或文档解析出多个 head。
**为什么(why)**: DOCTYPE 决定浏览器用标准模式还是怪异模式,怪异模式下布局规则回退到旧行为;charset 不在 head 前部时浏览器可能先用错编码解码再重解析,正是 mojibake 的机制性来源(与 content-deploy-hygiene 的乱码判定同源);多 head 是模板拼接事故,解析器容错重组后的 DOM 与你写的不一致。
**触发(trigger)**: 1) 无 DOCTYPE 即 fail(源表现行);2) charset 声明非 head 内首位即 warn;3) 文档解析出 >1 个 head 即 fail。
**不修的条件(caveat)**: 结构家族不(直接)影响排名(引擎容错强),然而它决定浏览器与引擎各自"看到什么",所以一般建议骨架零错。但遗留系统改 DOCTYPE 会牵动整站盒模型的,先在影子环境回归再上。
**修复(fix)**: 模板统一 `<!DOCTYPE html>` 开头;`<meta charset="utf-8">` 紧随 head 开标签;排查双 head 的模板拼接/组件注入。
**关联(seealso)**: htmlval-duplicate-meta、htmlval-head-content、content-deploy-hygiene;[semantic-html.md](../semantic-html.md)、[head-elements.md](../head-elements.md)

#### htmlval-duplicate-meta [待核 ID]
- 名称/类型: 重复 title/description(源表 ID `htmlval-multiple-titles`、`htmlval-multiple-descriptions`、`htmlval-title-outside-head`) —— issue · 优先级 high · 输出 CRITICAL(源表:多 title=fail;多 description=fail;title 在 head 外=fail)
**这意味(what)**: 文档里不止一个 `<title>` 或不止一条 meta description,或 title 出现在 head 之外。
**为什么(why)**: 多条声明时引擎取哪条不可控(常见取第一条或最后一条,实现不一),SERP 展示与你的优化对象脱节;title 在 head 外按无效处理等于没写。与 core-canonical-multiple(多条 canonical)同构:重复声明的歧义性比缺失更糟——坏信号>缺信号的又一次体现。title/description 家族的其余形态(缺失/长度/跨页重复)分别见 core-title-present、core-description-present、core-title-unique、content-duplicate-description,本条收口"多条/错位"。
**触发(trigger)**: 1) `<title>` 计数 >1 即 fail;2) meta description 计数 >1 即 fail;3) title 元素祖先链不含 head 即 fail。
**不修的条件(caveat)**: 无豁免;双写几乎总是两套注入(框架默认+业务代码)各写一次,修复是找源头,不是删一条留一条。
**修复(fix)**: head 注入收敛单一出口(head 组件/helmet 类方案);CI 断言 title=1、description=1 且都在 head 内。
**关联(seealso)**: core-title-present、core-description-present、core-canonical-multiple、htmlval-document-structure;[head-elements.md](../head-elements.md)

#### htmlval-head-content [待核 ID]
- 名称/类型: head 非法元素家族(源表 ID `htmlval-invalid-head`、`htmlval-noscript-in-head`) —— warning · 优先级 low · 输出 WARN(源表 warn;head 白名单 meta/title/link/script/style/base/noscript;head 内 noscript 仅含 link/style/meta 以外元素时 warn)
**这意味(what)**: head 里出现白名单之外的元素(文本、div、img 等),或 head 内放了 noscript。
**为什么(why)**: HTML 规范限定 head 只容纳元数据元素;Google 说 head 里出现无效元素后,其后的元素会被忽略([valid-page-metadata](https://developers.google.com/search/docs/crawling-indexing/valid-page-metadata),核对 2026-10-21),连带造成 core-canonical-outside-head 一类问题。head 内 noscript 是特例:其内部只允许 link/style/meta,常被误用于塞内容或脚本。
**触发(trigger)**: 1) head 子元素标签名 ∉ {meta,title,link,script,style,base,noscript}(纯空白文本豁免)即 warn;2) head 内 noscript 含 link/style/meta 以外元素即 warn。
**不修的条件(caveat)**: 解析器会自愈重组,多数用户看不出异常,然而重组后的 DOM 与源码意图错位是隐患源,所以一般建议 head 纯净。但模板注释/条件注释残片命中属误报级,顺手清理即可。
**修复(fix)**: 内容元素全部移出 head;noscript 的降级样式放 style、跳转提示放 body;模板 lint 头部白名单。
**关联(seealso)**: htmlval-document-structure、core-canonical-outside-head;[head-elements.md](../head-elements.md)

#### htmlval-base [待核 ID](源表 ID `htmlval-base-url`)
- 名称/类型: base 元素误用 —— issue/warning · 优先级 medium · 输出 CRITICAL(href 空/畸形/非 HTTP(S),源表 fail)/WARN(多条,源表 warn;须 ≤1 条)
**这意味(what)**: `<base>` 的 href 为空、畸形或非 HTTP(S) 协议,或文档里有多条 base。
**为什么(why)**: base 重定义全页相对 URL 的解析基准:它一坏,页内所有相对链接/canonical/hreflang 的解析结果整体漂移——一条坏 base 能同时引爆相对 URL 类判罚,是单点故障放大器。规范限定每文档至多一条。
**触发(trigger)**: 1) base href 空/不可解析/协议非 http(s) 即 fail;2) base 计数 >1 即 warn。
**不修的条件(caveat)**: base 写对时不产生任何 SEO 问题,然而它的全局副作用让任何后续改动都隐含风险,所以一般建议现代项目直接用绝对/根相对 URL 弃用 base。但遗留系统深依赖 base 的,保持单条+合法绝对 href 即可。
**修复(fix)**: 优先移除 base、模板输出绝对 URL;必须保留时单条+合法绝对 href;上线检查清单加 base 计数断言。
**关联(seealso)**: i18n-hreflang-relative-url、core-canonical-present、htmlval-head-content;[head-elements.md](../head-elements.md)

#### htmlval-html-size [待核 ID]
- 名称/类型: HTML 体积与占位文本(源表 ID `htmlval-size-limit`、`htmlval-lorem-ipsum`) —— warning/issue · 优先级 medium · 输出 WARN(>250KB)/CRITICAL(>500KB、lorem ipsum)(源表:>250KB 警、>500KB 败;lorem ipsum=fail)
**这意味(what)**: 未压缩 HTML 超过 250KB(500KB 进败档,~2MB 以上 Googlebot 可能只索引前段),或页面含 lorem ipsum 占位文本。
**为什么(why)**: HTML 体积是解析与抓取预算的直接消耗:Googlebot 只抓文件前 2MB(解压后),之后的内容与链接不参与索引([Googlebot 文档](https://developers.google.com/search/docs/crawling-indexing/googlebot),核对 2026-10-21;与 perf-page-weight 同源);250/500KB 几乎总是内联数据 JSON/隐藏 DOM/注释未清的症状。lorem ipsum 则是模板没换真文案就上线的直接证据,对用户与引擎都是无意义内容(与 content-placeholder-text 的 {{ }} 占位符同族,此处并入陈述)。
**触发(trigger)**: 1) HTML 响应体 >250KB 即警;>500KB 即败;2) 文本命中 lorem/ipsum 词表即 fail(源表现行)。
**不修的条件(caveat)**: 体积阈值不是排名开关,然而它标记"尾部内容可能不被处理",所以一般建议压回 250KB 内并把关键内容与链接放前段。但合法的大文档(长表格/内联数据应用页)超线是形态属性,优先保证前段完整而非硬拆。
**修复(fix)**: 内联 JSON 改按需接口拉取;注释/调试属性剥离;长列表服务端分页;lorem 命中直接换真文案或下线页面。
**关联(seealso)**: perf-page-weight、perf-dom-size、content-deploy-hygiene;[cwv-playbook.md](../cwv-playbook.md)
