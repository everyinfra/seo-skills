# LCP 诊断与优化要点

用途：页面的 Largest Contentful Paint（LCP）偏慢时，按固定顺序定位原因并给出修复建议。四指标全景、INP/CLS/TTFB 深度、第三方治理与优化优先级见 [cwv-playbook.md](cwv-playbook.md)。

## 定义与阈值

- LCP 衡量视口内最大的图片、文本块或视频从导航开始到渲染完成的时间。候选元素包括 `<img>`、`<svg>` 内的 `<image>`、`<video>`（封面图或首帧）、通过 `url()` 加载背景图的元素，以及包含文本的块级元素。
- 阈值（web.dev）：2.5 秒以内为良好，2.5–4 秒需要改进，超过 4 秒为差；按真实用户访问的第 75 百分位分别看移动端和桌面端。
- Google 搜索的 Core Web Vitals 报告使用真实用户数据（CrUX），实验室工具的一次测量不能代替它。

## 把 LCP 拆成四段

web.dev 把 LCP 拆为四个连续阶段，诊断时先看哪一段最长：

| 阶段 | 含义 | 常见原因 | 常见修法 |
|---|---|---|---|
| TTFB | 从导航到收到 HTML 首字节 | 服务端慢、没有缓存或 CDN、多次重定向 | 缓存 HTML、使用 CDN、减少重定向、优化后端查询 |
| 资源加载延迟 | 收到 HTML 到开始下载 LCP 资源 | 资源要等 JS 或 CSS 执行后才被发现、被懒加载、优先级低 | 让资源直接出现在 HTML 中；需要时 preload；加 `fetchpriority="high"`；LCP 图片不要懒加载 |
| 资源加载时间 | 下载 LCP 资源本身 | 图片过大、格式陈旧、没有响应式尺寸、跨域连接慢 | 压缩、现代格式、`srcset` / `sizes`、同源或提前建立连接 |
| 渲染延迟 | 资源到位后到真正绘制 | 渲染阻塞的 CSS / JS、客户端渲染才插入内容、字体、A/B 测试隐藏页面 | 精简关键 CSS、推迟非关键 JS、服务端输出主内容、避免整页隐藏 |

web.dev 给出的 TTFB 粗略参考是 0.8 秒以内；其余三段没有固定目标，按占比找最大的那段先处理。

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

用 web-vitals 库采集真实用户的 LCP，发送到你自己的分析端点：

```js
import { onLCP } from 'web-vitals/attribution';

onLCP((metric) => {
  // attribution 版本会给出目标元素和四段耗时，字段名以所用版本的文档为准
  navigator.sendBeacon('/your-rum-endpoint', JSON.stringify({
    name: metric.name, value: metric.value, rating: metric.rating
  }));
});
```

## 诊断顺序

1. 看真实用户数据：Search Console 的 Core Web Vitals 报告或 CrUX，确认是哪类页面、哪种设备的问题。
2. 在实验室复现：Chrome DevTools 性能面板或 Lighthouse，找出 LCP 元素和四段耗时。
3. 按上表处理占比最大的阶段，一次改一类，改完重新测量。
4. 上线后继续看真实用户数据；CrUX 是滚动窗口，改善需要一段时间才会完整体现。

需要批量测量时可以用 PageSpeed Insights API；自动化或较大量调用需要你自己的 API Key。

## 常见误区

- 给 LCP 图片加 `loading="lazy"`。
- 只看一次 Lighthouse 分数下结论，不看真实用户数据。
- 预加载太多资源，反而挤占 LCP 资源的带宽。
- 主内容完全由客户端渲染，HTML 里没有可发现的 LCP 资源。

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[addyosmani/web-quality-skills · skills/core-web-vitals/references/LCP.md](https://github.com/addyosmani/web-quality-skills/blob/main/skills/core-web-vitals/references/LCP.md)（MIT）
- 一手资料：[web.dev：LCP](https://web.dev/articles/lcp)、[web.dev：优化 LCP](https://web.dev/articles/optimize-lcp)、[web.dev：TTFB](https://web.dev/articles/ttfb)、[web.dev：INP](https://web.dev/articles/inp)、[web.dev：CLS](https://web.dev/articles/cls)、[Google：Core Web Vitals 与搜索](https://developers.google.com/search/docs/appearance/core-web-vitals)、[web-vitals 库](https://github.com/GoogleChrome/web-vitals)、[CrUX](https://developer.chrome.com/docs/crux)、[PageSpeed Insights API](https://developers.google.com/speed/docs/insights/v5/get-started)
