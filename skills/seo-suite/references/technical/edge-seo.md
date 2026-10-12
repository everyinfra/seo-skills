# Edge SEO:CDN/worker 层的技术 SEO 变更(2026 口径)

> 建立于 2026-10-12。核心口径来自 Patrick Stox《Edge SEO》(2026-06-26 发布,页内证据核验 2026-07-14;本套件 2026-10-12 复核链接可达)。术语史:Dan Taylor(SALT.agency)2018 年 TechSEO Boost 提出。分工边界:重定向与 canonical 规则本体见 [redirects-canonical.md](redirects-canonical.md);动态渲染与 cloaking 红线见 [rendering-seo.md](rendering-seo.md);Cloudflare 层的 AI 爬虫封/放/收费是商业决策,见 [ai-crawler-policy.md](ai-crawler-policy.md) 第六节。

## 一、Edge SEO 是什么

**定义**:在 CDN/边缘 worker 层实施技术 SEO 变更——redirects、canonical、hreflang、robots.txt、X-Robots-Tag、meta 注入、JSON-LD 注入、页面级 A/B——拦截并改写响应,不碰源站或 CMS,不等发布周期。

**解决的两个真实痛点**:
- 开发队列滞后:SEO 建议落地平均拖延数月(Will Critchlow 2016 Moz 研究:多数 SEO 建议约 6 个月后才被实现,营销请求排在其他团队优先级之后);
- 锁定平台改不动:Shopify(历史上 robots.txt 硬编码)、Salesforce Commerce Cloud、冻结的遗留企业栈——要改的东西物理上没有编辑入口。

**关键架构事实**:Google 只看到 CDN 所服务的内容——它不知道也不关心有没有 worker 参与,**边缘响应就是页面状态的唯一真相**。这正是边缘层的威力,也是 cloaking 红线如此重要的原因:没有任何技术障碍阻止你对 bot 和用户返回不同内容,只有纪律。

**worker 三阶段模型**(以 Cloudflare Workers 为具体实现,非通用三段标准):
1. **改请求**:CDN 在源站之前收到请求;worker 可改写 URL、直接从边缘返回 3xx(源站不参与)、修改请求头或放行。
2. **改响应头**:源站响应后,worker 增改 `X-Robots-Tag`、`Link: rel=canonical`、缓存头、安全头。
3. **改响应体**:流式解析 HTML 并改写——注入 `<link rel="canonical">`、hreflang、title、meta robots/description、`<script type="application/ld+json">`,或删改内容。Cloudflare HTML Rewriter 是标准工具;SALT 早期发布的 RequestFilter/ResponseFilter/BodyFilter 三接口独立可组合。

**延迟代价**:SALT 实测 body 过滤平均增加约 10ms、极端约 50ms,生产延迟无统计显著变化;CDN 就近可抵消。多数站可忽略,但要计入 TTFB 预算(见 [cwv-playbook.md](cwv-playbook.md) 第四节)。

**与 GTM 的本质区别是时序**:边缘改写发生在用户/爬虫收到响应**之前**;GTM 要先加载再在客户端改——GTM 注入的 canonical/JSON-LD 对不执行 JS 的爬虫等于不存在(见 [rendering-seo.md](rendering-seo.md) 第二节 meta 注入红线)。"用 GTM 修 canonical"因此从来不是 edge SEO 的替代品。

Cloudflare Worker 最小骨架(三阶段各占一段,**全量流量、无任何 UA 判定**):

```js
export default {
  async fetch(request) {
    const url = new URL(request.url);

    // 阶段 1·改请求:边缘 301,源站不参与
    if (url.pathname === "/old-path") {
      return Response.redirect(new URL("/new-path", url), 301);
    }

    const response = await fetch(request);

    // 阶段 2·改响应头:参数页加 X-Robots-Tag
    const headers = new Headers(response.headers);
    if (url.searchParams.has("page")) {
      headers.set("X-Robots-Tag", "noindex, follow");
    }

    // 阶段 3·改响应体:HTML Rewriter 流式注入 JSON-LD
    return new HTMLRewriter()
      .on("head", {
        element(el) {
          el.append('<script type="application/ld+json">' +
            JSON.stringify({ "@context": "https://schema.org",
              "@type": "Organization", name: "示例品牌", url: url.origin }) +
            "</script>", { html: true });
        },
      })
      .transform(new Response(response.body, { ...response, headers }));
  },
};
```

注入的 JSON-LD 同样要过序列化安全(`</script>` 逃逸三序列)与实体规则,见 [schema-templates.md](schema-templates.md) 完全装载节;生产落地前过 `schema_lint.py` 点验。

## 二、平台对照表

| 平台 | 运行时/方法 | SEO 要点 |
|---|---|---|
| **Cloudflare Workers** | V8 isolate;JS/TS/WASM | 最成熟:HTML Rewriter 流式改写;KV 存重定向表;免费档 10 万请求/天。Snippets(付费计划可用)适合头改写与简单重定向,无持久存储/重计算 |
| **Akamai EdgeWorkers** | 边缘 JS | 企业级;EdgeKV 承载大规模重定向/SKU 表 |
| **Fastly Compute** | Rust/Go/JS 经 WASM | 流式 HTML 变换;支持 Surrogate-Control(边缘缓存控制) |
| **AWS Lambda@Edge** | CloudFront 上的 Node.js | 完整 Lambda 运行时;延迟高于纯边缘 worker |
| Vercel Routing Middleware(由 Edge Middleware 更名)/ Netlify Edge Functions | JS / Deno | 原生集成各自部署流;meta 注入与 geo 重定向常用载体 |

选型第一问不是"哪家强",而是"站现在就在哪个 CDN 上"——edge SEO 的全部收益都以"已在该 CDN"为前提;为 edge SEO 单独迁移 CDN 不成立。

**常见用例×阶段对照**(全部默认全量流量):

| 用例 | 阶段 | 要点 |
|---|---|---|
| 边缘重定向(清链、批量路径迁移、非规范域归一) | 1 | 映射表放 KV/EdgeKV/Bulk Redirects;上线后逐跳核验 |
| robots.txt 兜底(平台硬编码改不动) | 1/3 | 边缘直接应答 `/robots.txt`;注意与 CF 托管 robots 注入区分(ai-crawler-policy.md 第三节) |
| X-Robots-Tag 控索引(分页/参数页/打印版) | 2 | 头级控制不动 HTML;套件 monitor 的 noindex 检测覆盖响应头通道 |
| canonical/hreflang 批量修正 | 3 | HTML Rewriter 按 URL 规则注入/改写,先采样验证再放量 |
| 规模化纠错(误 noindex/nofollow、批量坏 title) | 3 | 大站把 Rewriter 指向全站,按规则扫描修复——Stox 给的典型场景 |
| JSON-LD 注入 | 3 | 序列化安全+`schema_lint.py` 点验(见第一节代码块后注) |
| 页面级 A/B(时敏实验) | 3 | 按实验分桶,见第五节铁律的 A/B 边界 |

## 三、决策表:什么改边缘,什么进源码

**默认答案:进源码。** 边缘是绕过约束的通道,不是新的正确架构。能改源码就改源码:源码是唯一有版本评审、测试、文档的地方;worker 改多了,页面真实状态散落源码与边缘两处,漂移只是时间问题。

边缘适合的三类场景:

| 场景 | 为什么边缘 | 退场条件 |
|---|---|---|
| 遗留 CMS/锁定平台改不动 | 源码路径物理不存在(见第一节痛点) | 平台迁移或解锁之日,把规则搬回源码 |
| 时敏实验(页面级 A/B、活动期 noindex/canonical 调整) | 等一个发布周期,实验窗口就过了 | 实验结论固化后回源码;实验结束即删 worker 规则 |
| 收购站过渡期 | 无权改对方代码库,但要先接管 canonical/重定向 | 完成技术栈整合 |

不构成边缘理由的:新站、有正常发布管线的团队、"想绕过开发部"的组织性诉求。最后一条尤其危险——绕过评审的改写层,长期必然产生没人知道的页面状态。

## 四、审计检查项

审计已部署 edge worker 的站,固定查四件:

1. **WAF/bot 规则在 worker 之前静默拦 Googlebot**:CDN 的 WAF、bot 管理规则排在 worker 前面——worker 写得再对,Googlebot 可能根本到不了它。核法:对照 Google 官方发布的 Googlebot IP 段与反向 DNS 验证真实 Googlebot 是否拿到 200;活体探测(UA 伪装探测)方法见 [ai-crawler-policy.md](ai-crawler-policy.md) 第五节——robots 说"允许"与请求"到得了"是两层。
2. **仅对 bot 的边缘预渲染=动态渲染,已废弃,踩线**:worker 按 UA 给爬虫喂预渲染版、给用户原版——这正是 Google 已降级为"临时变通、非长期方案"的动态渲染(口径见 [rendering-seo.md](rendering-seo.md) 第四节)。给 Googlebot 喂预渲染版还有 bot 版与用户版内容漂移的风险。套件认可的例外只有一个方向:对**不渲染 JS 的**社交/Bing 爬虫做补偿性预渲染且必须排除 Googlebot(rendering-seo.md CSR 深读节)——那是给能力缺口补偿,不是给 Googlebot 差异化内容。
3. **worker 是全站单点故障,必须可回滚**:worker 位于每个请求的路径上,一个异常就是全站 5xx。审计标准:版本化部署、作用域收窄(只挂需要的路由)、**保留一键回滚**;三者缺一即 P1 风险项。
4. **注入残留**:worker 回滚或改版后,页面 title/canonical/meta 是否残留旧注入值、与源站输出混在一起——用套件 monitor 的页面字段 diff 抓(见下节)。

## 五、铁律:全量流量生效,绝不按 bot 分流

**cloaking 是唯一不可协商的边界**:每一条边缘变更作用于全部流量;对 Googlebot 返回与用户显著不同的内容=违规。第一节说过"Google 只见 CDN 所服务的内容"——意味着这里没有技术护栏,只有这条纪律。

- 边缘层不存在合法的"按 bot 分流改内容";上节的社交/Bing 补偿性预渲染是唯一历史遗留方向,且必须排除 Googlebot。
- 页面级 A/B 的边界:按**用户/会话/实验分桶**,绝不按 bot 判定分桶——爬虫落进哪个桶就看到哪个桶,不给 bot 单开"最优桶"。
- 配套纪律:边缘改写要让团队可见——worker 代码入库、变更日志、与源码同级的评审。否则"这个页面为什么是这个 canonical"会变成考古题。

## 六、与套件工具接线

- **monitor 检测注入残留**:`monitor.py` 的页面字段 diff(title/meta_desc/canonical/og_title/og_desc)在相邻快照间对比——worker 注入的字段同样落进这些字段:注入上线=一次可解释的字段漂移;worker 回滚后的旧值残留=无法解释的漂移,按 content_regression/noindex_added 告警路由排查。其 noindex 双通道(meta robots + **X-Robots-Tag 响应头**)恰好覆盖边缘注入 X-Robots-Tag 的情形。
- **redirect_chain 逐跳核边缘重定向**:`redirect_chain.py URL` 实时逐跳 GET——边缘 3xx 与源站 3xx 在日志里难区分,逐跳响应头指纹(`server`/`cf-*` 等)能看出哪一跳来自边缘层;`--max N` 设链长阈值,边缘重定向接源站重定向拼出长链时按 CRITICAL 上报。
- **site_crawl 全站面 + schema_lint 点验**:批量核对全站 canonical/hreflang 是否被 worker 改对;采样页跑 `schema_lint.py` 核注入的 JSON-LD(@id 悬空/占位符在注入产物里同样常见)。

## 来源

本文由 EveryInfra 自行编写,只保留要点,未复制原文。

- 一手:Patrick Stox [Edge SEO](https://patrickstox.com/technical-seo/edge-seo/)(2026-06-26;页内证据核验 2026-07-14,含 [Cloudflare Workers 运行机制](https://developers.cloudflare.com/workers/reference/how-workers-works/)官方文档)。三阶段模型、平台对照表、SALT ~10ms 延迟实测、Critchlow 2016 研究均出自该页;本套件 2026-10-12 复核链接可达。
- 术语史:Dan Taylor / SALT.agency,TechSEO Boost Boston 2018(经 Stox 页转引)。
- 官方政策:Google cloaking 与动态渲染口径见 [rendering-seo.md](rendering-seo.md) 与 [deprecated-signals.md](deprecated-signals.md);重定向语义见 [redirects-canonical.md](redirects-canonical.md)。
