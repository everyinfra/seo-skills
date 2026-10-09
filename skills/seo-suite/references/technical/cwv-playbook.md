# Core Web Vitals 优化手册(2026-10 口径)

> 建立于 2026-10-09,关键事实经 2026-10 检索核实。本手册是 CWV 总纲:四指标全景、INP/CLS/TTFB 深度、第三方脚本治理、优化优先级。分工边界:LCP 的四段拆解与诊断顺序见 [LCP.md](LCP.md),本文只补 2026 新实践;JS 渲染策略见 [rendering-seo.md](rendering-seo.md);审计扣分规则见 [audit-rule-catalog.md](audit-rule-catalog.md)。

## 一、四指标全景

| 指标 | 衡量对象 | Good | 需改进 | Poor |
|---|---|---|---|---|
| LCP | 最大内容元素渲染完成(加载) | ≤2.5s | 2.5–4s | >4s |
| INP | 交互到下一帧绘制(响应性) | ≤200ms | 200–500ms | >500ms |
| CLS | 累积布局偏移(视觉稳定性) | ≤0.1 | 0.1–0.25 | >0.25 |
| TTFB | 首字节(诊断性辅助指标,非核心三项) | ≤0.8s | 0.8–1.8s | >1.8s |

- 阈值 2026-10 无变化:2024-03 INP 替代 FID 后 Google 未再动核心阈值;TTFB 的 0.8s/1.8s 只是 web.dev 诊断参考,不参与核心三项评估。
- 评估口径:真实用户(field)第 75 百分位,移动/桌面分开,CrUX 28 天滚动窗口,按页面组聚合。**组级评级规则:三项全 good 才算 good,任一 poor 即整组 poor**,其余为 needs improvement——只修最差的一项就能把组从 poor 拉回 NI,三项都过线才全绿。
- Field vs Lab:CrUX/GSC CWV 报告是 field,反映真实分布但无法归因;Lighthouse/DevTools 是 lab,可控可归因但受模拟环境(节流、设备档位)影响。正确顺序:field 定位"哪类页面、哪个指标差",lab 复现并归因,改完回看 field。
- CrUX vs RUM:CrUX 只覆盖被收录的流量(采样、以 Chrome 为主),低流量站可能查无数据;自建 RUM 用 web-vitals 库(attribution 版)补盲,可细到 URL 与交互元素。两者矛盾时信 RUM(自己的真实用户)。
- CrUX 已于 2024 年起收录 TTFB(API 与 BigQuery 可查),TTFB 不再只能靠 lab 估计。

数据源选型:

| 数据源 | 类型 | 粒度与归因 | 适用 |
|---|---|---|---|
| GSC CWV 报告 | field(CrUX) | 页面组级,无归因 | 定位哪类页面、哪个指标差 |
| CrUX API / BigQuery | field | origin/URL 级,含 TTFB | 竞品对比、改动前后验证 |
| PageSpeed Insights | field+lab 合一 | 单 URL | 单页快速诊断(lab 部分可归因) |
| web-vitals 自建 RUM | field(自采) | URL/元素/交互级归因 | 决定修什么、验证修没修好 |
| Lighthouse / DevTools | lab | 单次模拟 | 本地复现与 CI 回归 |

## 二、INP 深度(2024-03 替代 FID 后的优化)

定义要点(与 FID 的本质差异):

- FID 只测首次交互的输入延迟;INP 测页面全生命周期内每次交互的完整链路:**输入延迟 + 处理时长 + 呈现延迟**,直到下一帧绘制。
- 取值规则:交互 ≤50 次的页面取最差一次;>50 次取第 98 百分位(丢弃最极端 2%)。策略含义:不必修所有交互,用归因数据找最差的几类交互集中修。
- 触发器:click/tap/keypress、pointerdown;纯 hover 不计入。

三段归因与对应修法(先用 RUM 拿归因,再按下表对症):

| 最长段 | 典型原因 | 先修什么 |
|---|---|---|
| 输入延迟 | 主线程被长任务/第三方占用 | 让出主线程、延迟第三方 |
| 处理时长 | 事件处理器本身太重 | 拆任务、减计算、防抖 |
| 呈现延迟 | DOM 更新量过大/布局抖动/下一帧太晚 | 读写分离、减 DOM 更新、即时 loading 态 |

优化四板斧:

**1) 长任务拆分**

- 主线程任务 >50ms 即长任务;INP 差几乎总能追到主线程被长任务或大渲染更新占用。
- `scheduler.yield()`:Chrome 129+(2024-09)、Firefox 142+(2025-08)支持,**Safari 至 2026-10 仍未支持**(WebKit 对 API 设计有保留),未达 Baseline,必须带兜底:

```js
const yieldToMain = ('scheduler' in window && scheduler?.yield)
  ? scheduler.yield.bind(scheduler)
  : () => new Promise(r => setTimeout(r, 0));

// 长循环每处理一批就让出主线程
for (const batch of batches) {
  process(batch);
  await yieldToMain();
}
```

- 与 `setTimeout(0)` 的差别:yield 的续段带优先级续跑,不被新任务插队;setTimeout 让出后回到队列尾。
- 红线:兜底不能用"永不 resolve 的 Promise",await 会无报错永久挂起。Safari 上限方案:MessageChannel 让出、按块切片;React 18+ transition 自带让出式调度。

**2) Hydration backlog**

- SPA 典型 INP 杀手:hydration 期间主线程被注水任务占满,点击落在未注水的节点上无响应。
- 解法按成本递增:减 JS(代码分割/删依赖)→ 选择性注水(React selective hydration)/岛屿架构(Astro Islands)→ 可恢复性(Qwik,无注水)→ 纯 SSR+渐进增强(原生表单/`<details>` 承接交互)。
- 注水顺序按交互价值:首屏即需交互的组件先注水,其余 idle 后注水。

**3) 第三方脚本治理(详见第六节)**

- 广告/A-B/热图 tag 常年贡献最大头的主线程占用,且常在交互路径上抢执行。

**4) 交互优先(先给反馈)**

- INP 只算到下一帧:慢处理器先立刻置 loading 态再算,下一帧尽快绘制,不等计算完成。
- 搜索防抖;DOM 读写分离防 layout thrashing;动画用 transform/opacity,别动触发布局的属性。
- 用 web-vitals `onINP`(attribution)拿 interactionTarget 与三段耗时,只修最差交互:

```js
import { onINP } from 'web-vitals/attribution';

onINP((metric) => {
  const a = metric.attribution[0] || {};
  navigator.sendBeacon('/rum', JSON.stringify({
    url: location.pathname,
    value: metric.value, rating: metric.rating,
    target: a.interactionTarget,           // 慢交互的元素
    inputDelay: a.inputDelay,              // 三段归因,字段名以所用版本文档为准
    processingDuration: a.processingDuration,
    presentationDelay: a.presentationDelay,
  }));
});
```

**常见误区**

- 用 FID 数据判断响应性:FID 只测首次输入延迟,老站"FID 全绿、INP poor"是常态。
- 指望 lab 工具:Lighthouse 的模拟交互覆盖不了真实用户路径,INP 诊断只能靠 field/RUM。
- 只盯 load 后几秒:INP 观察页面全生命周期,晚发生的交互同样计入。
- 平铺资源修"所有点击":取第 98 百分位意味着集中修最差交互收益最高。

## 三、CLS 深度

口径:布局偏移按会话窗口累计(窗口 5s 封顶、单次偏移 1s 封顶),取最大会话得分;用户输入后 500ms 内的偏移不计入。**只在排版位置变化时算,内容追加不推挤现有内容则不计。**

按出现频率排查:

**1) 图片无尺寸**

- 所有 `<img>`/`<video>`/`<iframe>` 写 `width` + `height`,浏览器据此算 aspect-ratio 预留空间;CSS 布局下用 `aspect-ratio` 属性。
- 动态图尺寸未知:容器定宽 + `aspect-ratio` 上限预估 + `object-fit: cover` 兜底。

**2) Web 字体 swap**

- `font-display: swap` 必然 FOUT,回退字体与 Web 字体度量不一致 → 换字体瞬间整段文字重排。解法是给回退字体配平度量:

```css
@font-face {
  font-family: 'Adjusted Fallback';
  src: local('Arial');
  size-adjust: 104%;        /* 回退字形宽度调到与 Web 字体一致 */
  ascent-override: 92%;
  descent-override: 24%;
  line-gap-override: 0%;
}
body { font-family: 'BrandFont', 'Adjusted Fallback', sans-serif; }
```

- 度量值用工具按实际字体算(fontaine/capsize),不要手猜。`font-display: optional` 零偏移(要么首渲染就绪要么永远回退),品牌要求不高时是 CLS 最优解。

**3) 动态内容注入**

- toast/横幅插在现有内容上方 = 必然偏移。规则:**新内容追加到视口下方,或用 `position: fixed` 覆盖层,或用 transform 位移**。
- 列表懒加载用等高骨架屏占位,不留"加载后撑开"的空隙。

**4) 广告位与嵌入容器**

- 广告槽固定尺寸或 `min-height`,填充失败也保留空槽或同尺寸占位;广告库动态扩容是最常见的大额偏移源。

```html
<div id="ad-top" style="min-height:250px"></div>
```

- 视频/推文/地图 embed:容器按 `aspect-ratio` 预留,或直接上 facade(见第六节)。

诊断工具:

- Chrome DevTools → Rendering → **Layout Shift Regions**:偏移区域闪蓝紫色,直接看哪里在动。
- Performance 面板的 Layout Shift 事件:点开看 sources(引起偏移的节点)与前后位置。
- web-vitals `onCLS`(attribution):给出 `node`(偏移最大元素)与 `sources`(前几个来源)。

**常见误区**

- 以为一切位移都算:CLS 只统计视口内影响可见内容的位移,transform 动画不计入;内容追加不推挤现有内容也不计入。
- 占位高度靠猜:占位与真实渲染不一致照样偏移,按真实尺寸/比例预留。
- 修完不做回归:CLS 修复极适合写进 CI(Lighthouse 断言)防复发。

## 四、TTFB

拆解:重定向 + DNS/TCP/TLS + 源站思考时间。CDN 消掉的是前两类与缓存命中时的第三类;源站慢只能靠后端修。

分层修法(按见效排序):

1. **HTML 进 CDN 缓存**:最大杠杆是缓存 HTML 文档本身而不是只缓存静态资源;动态页用 stale-while-revalidate(旧内容秒回+后台刷新)。cache-key 纪律:只按必要头/cookie 变体,个性化片段拆成独立请求,否则一人一版本全站 miss。
2. **清重定向链**:HTTP→HTTPS→www 每跳一个完整 RTT,canonical 域直达。
3. **SSR 响应时间**:流式渲染早吐首字节;数据获取并行化(别串行 await);热点查询上对象缓存;数据库治 N+1、补索引。
4. **边缘渲染**:渲染搬到边缘节点,消掉单区域 SSR 的回源 RTT(行业口径 TTFB 可降 60–80%,当方向不当承诺)。载体:Next.js Edge/Cloudflare Workers 等;注意边缘运行时的 API 差异(Node API 不全)。
5. **103 Early Hints**:源站思考期间先发 preload/preconnect 提示,浏览器提前拉关键资源——不降 TTFB 本身,但把后续阶段整体提前:

```http
HTTP/1.1 103 Early Hints
Link: </css/main.css>; rel=preload; as=style
Link: </img/hero.webp>; rel=preload; as=image; fetchpriority=high
```

   常见载体:Cloudflare/CDN 自动注入、WordPress 6.x+ 原生支持。

测量:lab 看 DevTools Network 的 waiting/TTFB;field 用 CrUX API(2024 起含 TTFB)与 RUM(Navigation Timing `responseStart`);GSC CWV 报告间接反映在 LCP 的 TTFB 段。

## 五、LCP 增量(2026 新实践)

四段拆解、诊断顺序、`fetchpriority` 最小示例见 [LCP.md](LCP.md),以下只补增量,不重复。

- **fetchpriority 已 Baseline**:Chrome 101+/Safari 17.2+/Firefox 132+(Firefox 132 落地后达成),可放心裸用,不再是"仅 Chromium 提示"。
- **Speculation Rules 预取/预渲染**:对下一页 LCP 是数量级改善——预渲染页在导航时几乎已渲染完成。
  - 现状:仅 Chromium 支持(2026-10 Firefox/Safari 未支持),按渐进增强接入,不支持即静默跳过。
  - 文档规则(document rules)默认 `eagerness: conservative`(hover/pointerdown 才起);URL 列表规则默认 immediate。
  - 红线:document rules 配 immediate/eager 会过取几十上百条 URL 浪费流量;moderate/conservative 自带小 FIFO 上限(约 2–3 条)防过取。

```html
<script type="speculationrules">
{"prefetch":[{"source":"document","where":{"href_matches":"/*"},"eagerness":"moderate"}]}
</script>
```

- **响应式 LCP 图**:AVIF 为主力;`sizes` 写准——常见错配是 CSS 实际半宽却写 `sizes="100vw"`,导致下载过大。

## 六、第三方脚本治理

审计法:

1. 清点:Lighthouse "Third-party usage" 报告、DevTools Network 按域分组、Performance 面板按脚本归因主线程(第三方帧有标注)。
2. 三档分级:
   - **A 关键业务**(分析/支付/A-B):自托管或换轻量实现,`async`/`defer`,采集时机后移。
   - **B 可延迟**(热图/聊天/营销 pixel):idle 或首屏渲染完成后注入,或首个交互信号后再加载。
   - **C 仅视口内才有价值**(视频/地图/社交 embed):facade,点击才加载真组件。

   常见第三方与默认处置:

   | 类别 | 例子 | 默认处置 |
   |---|---|---|
   | 分析 | GA4/标签管理器 | 服务端采集(gtag 自托管/SSG 侧);事件批量上报 |
   | A/B 测试 | Optimizely/VWO | 反闪烁模板+限时卸载;实验结束立刻摘脚本 |
   | 热图/录屏 | Hotjar/Clarity | 首屏后加载、采样率调低 |
   | 客服聊天 | Intercom/Zendesk | 等交互意图(scroll/停留 N 秒)再挂 |
   | 视频/社交 embed | YouTube/推文/地图 | facade,点击才注入 iframe |
3. embed 治理:YouTube 换 lite-embed(缩略图+播放按钮,点击注入 iframe,省数百 KB);推文/IG 用截图+原文链接;聊天 widget 等首个交互意图再挂。
4. 进阶:Partytown 把第三方搬进 Web Worker,主线程零阻塞——兼容性有限,逐个脚本验证再上。
5. 制度化:设第三方 JS 预算(KB 上限)+ tag manager 审批流;没有闸门,治理完一个月就长回来。

## 七、CWV 与 SEO 的真实关系

- **官方口径**:page experience(含 CWV)自 2021-06 起是排名信号,但 Google 反复申明权重低、相关性优先——原话大意"页面体验不能替代好内容",工程师(Gary Illyes)称其为"某种意义上的 tie-breaker":同等相关时才分高下。**CWV 不是主排名杠杆,是资格线与负资产防线。**
- 报告侧变化:GSC 的 Page Experience 报告已于 2024-11-18 移除(它只是 CWV+HTTPS 两报告的汇总视图,两者均保留)——信号仍在,只是不再单独汇报。
- 实测数据:速度-营收关联最常被引的是 Deloitte《Milliseconds Make Millions》(2020):**0.1s 改善关联零售转化 +8.4%、AOV +9.2%**(关联非因果)。排名侧:大规模对照从未证明"修好 CWV → 排名上涨",SEO 案例里 CWV 全绿后的排名变化通常归于同期其他改动。
- 结论:向业务要预算时用转化/参与口径论证,CWV 的 SEO 价值是防御性的(大流量站全绿是常态,不绿是相对劣势)。

## 八、优化优先级决策树

第 0 步:GSC CWV 报告(无 field 数据先接 RUM)确认哪个指标、哪类页面组 poor。

按"影响 × 成本"的默认顺序(高影响低成本在前):

1. CLS poor → 图片补尺寸、容器 min-height:纯标记改动,半天级,零风险。
2. LCP poor 且 TTFB 段最长 → HTML 进 CDN 缓存+清重定向:架构外改动,风险低。
3. LCP poor 且加载延迟段最长 → LCP 图 preload+`fetchpriority="high"`+去掉懒加载:单点改动。
4. INP poor → 先测第三方主线程占比:延迟/facade 第三方往往比改自家代码便宜一个量级。
5. INP poor 且是自家代码 → 长任务拆分(yield 带兜底)+交互即时反馈:需要工程投入。
6. TTFB 源站慢 → 数据库/缓存/流式 SSR:后端工程,周期最长。
7. 全绿后 → Speculation Rules/预渲染抢体验上限。

文字版决策树:

```text
哪个指标 poor?
├─ CLS  → 按频率排查:图片尺寸?广告/embed 容器?字体 swap?
├─ LCP  → 按 LCP.md 四段表,先修占比最长的那段
└─ INP  → 第三方占比高(>40% 主线程)先治理第三方;否则拆长任务+查注水
三项均 NI → 修成本最低的一项把组级评级拉回 good(三项全过线才算 good)
```

纪律:一次只改一类;改完等 CrUX 28 天窗口滚动满再评估,不被单日波动带偏。

## 来源

本文由 EveryInfra 自行编写,只保留要点,未复制原文。官方口径优先,行业数字均标注。

- 一手:web.dev [INP](https://web.dev/articles/inp)、[优化 INP](https://web.dev/articles/optimize-inp)、[优化 CLS](https://web.dev/articles/optimize-cls)、[TTFB](https://web.dev/articles/ttfb)、[优化长任务](https://web.dev/articles/optimize-long-tasks)、Chrome [scheduler.yield 博文](https://developer.chrome.com/blog/use-scheduler-yield)、[Speculation Rules 改进](https://developer.chrome.com/blog/speculation-rules-improvements)、MDN [fetchpriority](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Attributes/fetchpriority)、[Speculation Rules API](https://developer.mozilla.org/en-US/docs/Web/API/Speculation_Rules_API)、Google Search Central [page experience](https://developers.google.com/search/docs/appearance/page-experience)
- 2026-10 检索核实:scheduler.yield Safari 未支持([caniuse](https://caniuse.com/mdn-api_scheduler_yield)、[Firefox 142](https://web.dev/blog/web-platform-08-2025));fetchpriority Baseline(Firefox 132+,[Calibre](https://calibreapp.com/blog/priority-hints));GSC Page Experience 报告 2024-11-18 移除([SEJ](https://www.searchenginejournal.com/google-retires-search-consoles-page-experience-report/532968));Illyes tie-breaker 表述([Seroundtable](https://www.seroundtable.com/google-page-experience-update-tiebreaker-31880.html));Deloitte 速度-营收研究;边缘渲染降 TTFB 60–80% 为行业口径([TotaliWeb](https://www.totaliweb.com/the-silent-website-killer-server-side-rendering-vs-edge-rendering-in-2026))
