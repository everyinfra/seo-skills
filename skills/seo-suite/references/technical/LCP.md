# LCP 诊断与优化要点

用途：页面的 Largest Contentful Paint（LCP）偏慢时，按固定顺序定位原因并给出修复建议。四指标全景、INP/CLS/TTFB 深度、第三方治理与优化优先级见 [cwv-playbook.md](cwv-playbook.md)。

## 定义与阈值

- LCP 衡量视口内最大的图片、文本块或视频完成渲染的时间（从页面开始加载算起）。候选元素：`<img>`、`<svg>` 内的 `<image>`、`<video>`（取封面图加载和首帧呈现中较早的一个）、用 `url()` 加载背景图的元素、包含文本节点的块级元素（[web.dev：LCP](https://web.dev/articles/lcp)，核对 2026-10-18）。
- 阈值：≤2.5 秒为良好，2.5–4 秒需要改进，>4 秒为差；按真实用户第 75 百分位，移动端和桌面端分开看（同上）。
- Search Console 的 Core Web Vitals 报告数据来自 CrUX（真实 Chrome 用户），按最近 28 天的 p75 计算（[Search Console 帮助](https://support.google.com/webmasters/answer/9205520)）。实验室工具的一次测量不能代替它。

## 把 LCP 拆成四段

web.dev 把 LCP 拆为四个连续阶段，并给出各段的参考占比（[web.dev：优化 LCP](https://web.dev/articles/optimize-lcp)，核对 2026-10-18）：

| 阶段 | 含义 | 参考占比 | 常见原因 | 常见修法 |
|---|---|---|---|---|
| TTFB | 从导航开始到收到 HTML 首字节 | 约 40% | 服务端慢、没有缓存或 CDN、多次重定向 | 缓存 HTML、使用 CDN、减少重定向、优化后端查询 |
| 资源加载延迟 | 收到首字节到开始下载 LCP 资源 | <10% | 资源要等 JS 或 CSS 执行后才被发现、被懒加载、优先级低 | 让资源直接出现在 HTML 中；必要时 preload；加 `fetchpriority="high"`；LCP 图片永远不要懒加载 |
| 资源加载时长 | 下载 LCP 资源本身 | 约 40% | 图片过大、格式陈旧、没有响应式尺寸、跨域连接慢 | 压缩、AVIF/WebP、`srcset`/`sizes`、同源托管或提前建连、长缓存 |
| 渲染延迟 | 资源到位到真正绘制 | <10% | 渲染阻塞的 CSS/JS、客户端渲染才插入内容、主线程被长任务占用、A/B 测试隐藏页面 | 精简关键 CSS、推迟非关键 JS、服务端输出主内容、避免整页隐藏 |

web.dev 提醒：占比只用于段与段之间比较，不要换算成绝对毫秒目标。只压缩图片而渲染延迟不变时，节省的时间会转移到渲染延迟段，LCP 不变。TTFB 的粗略参考是 ≤0.8 秒（[web.dev：TTFB](https://web.dev/articles/ttfb)）。

## 最小示例

LCP 图片直接写在 HTML 中，并提高优先级：

```html
<img src="/img/cover-1200.webp"
     srcset="/img/cover-800.webp 800w, /img/cover-1200.webp 1200w"
     sizes="100vw" width="1200" height="600"
     fetchpriority="high" alt="产品主界面">
```

LCP 是 CSS 背景图时，浏览器要等样式解析后才发现它，可以预加载：

```html
<link rel="preload" as="image" href="/img/cover-bg.webp" fetchpriority="high">
```

用 web-vitals 库采集真实用户的 LCP 和四段耗时（attribution 构建；字段名按 [web-vitals README](https://github.com/GoogleChrome/web-vitals)，main 分支 6.2.3 核对 2026-10-18）：

```js
import { onLCP } from 'web-vitals/attribution';

onLCP(({ name, value, rating, attribution }) => {
  navigator.sendBeacon('/your-rum-endpoint', JSON.stringify({
    name, value, rating,
    target: attribution.target,                       // LCP 元素选择器
    ttfb: attribution.timeToFirstByte,
    loadDelay: attribution.resourceLoadDelay,
    loadDuration: attribution.resourceLoadDuration,
    renderDelay: attribution.elementRenderDelay,
  }));
});
```

## 诊断顺序

1. **看真实用户数据**：`python3 scripts/field_data.py --url URL --strategy both`（CrUX 28 天 p75 + Lighthouse 实验数据，按官方阈值判定；`--crux-scope origin` 看全站；批量用 `--urls 清单文件`）。退出码 1 表示 LCP/INP/CLS 任一现场值为差。也可看 Search Console 的 Core Web Vitals 报告，确认是哪类页面、哪种设备的问题。
2. **看现场的四段数据**：CrUX API 直接提供 LCP 分段指标 `largest_contentful_paint_image_time_to_first_byte`、`..._resource_load_delay`、`..._resource_load_duration`、`..._element_render_delay` 和 `largest_contentful_paint_resource_type`（[CrUX API](https://developer.chrome.com/docs/crux/api)）。
3. **在实验室复现**：Chrome DevTools 性能面板或 Lighthouse，找出 LCP 元素和四段耗时。
4. **按上表处理占比最大的阶段**，一次改一类，改完重新测量。
5. **上线后回看现场数据**：CrUX 是 28 天滚动平均、每天更新，改善要在窗口滚动后才完整体现。

PageSpeed Insights API 可以不带 key 调用；频繁的自动化调用建议用 API key（[PSI API](https://developers.google.com/speed/docs/insights/v5/get-started)）。CrUX API 必须带 key。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 现场 LCP | `python3 scripts/field_data.py --url URL --strategy both --json`，读 `field` 里 LCP 的 p75 | 两种设备 p75 ≤2.5s → 通过；>4s → 差 |
| 最长分段 | CrUX API 四个 `largest_contentful_paint_image_*` 分段，或 RUM 里 attribution 四段 | 找出超出参考占比最多的一段，作为第一修复项 |
| LCP 资源可发现 | `curl -s URL \| grep -io '<img[^>]*fetchpriority="high"[^>]*>'`；对照 DevTools 识别出的 LCP 元素 | LCP 图片出现在初始 HTML 且没有 `loading="lazy"` → 通过 |
| 懒加载误用 | DevTools Elements 选中 LCP 元素看属性 | 带 `loading="lazy"` → 失败 |
| 预加载过多 | DevTools Network 按 Priority 排序 | 高优先级请求里 LCP 资源排前 → 通过；被其他 preload 挤后 → 失败 |
| 修复生效 | 改动前后各跑一次 field_data；28 天后再跑 | 现场 p75 下降且评级不变差 → 通过 |

## 常见误区

- 给 LCP 图片加 `loading="lazy"`。web.dev 原话：永远不要懒加载 LCP 图片。
- 只看一次 Lighthouse 分数下结论，不看真实用户数据。
- 预加载太多资源，挤占 LCP 资源的带宽。
- 主内容完全由客户端渲染，HTML 里没有可发现的 LCP 资源。
- 只压缩图片，不看渲染延迟段：时间会从加载段转到渲染段。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[addyosmani/web-quality-skills · skills/core-web-vitals/references/LCP.md](https://github.com/addyosmani/web-quality-skills/blob/main/skills/core-web-vitals/references/LCP.md)（MIT）
- 一手资料（核对 2026-10-18）：[web.dev：LCP](https://web.dev/articles/lcp)、[web.dev：优化 LCP](https://web.dev/articles/optimize-lcp)、[web.dev：TTFB](https://web.dev/articles/ttfb)、[Search Console Core Web Vitals 报告](https://support.google.com/webmasters/answer/9205520)、[web-vitals 库](https://github.com/GoogleChrome/web-vitals)、[CrUX API](https://developer.chrome.com/docs/crux/api)、[PageSpeed Insights API](https://developers.google.com/speed/docs/insights/v5/get-started)
