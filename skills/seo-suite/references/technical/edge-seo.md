# Edge SEO：CDN/worker 层的技术 SEO 变更（2026 口径）

> 主要参考 Patrick Stox《[Edge SEO](https://patrickstox.com/technical-seo/edge-seo/)》（第三方从业者文章，发布 2026-06-26，更新 2026-07-22；本套件 2026-10-18 复读）。平台能力与 Google 政策另按官方文档核对，核对日 2026-10-18。
> 分工：重定向与 canonical 规则见 [redirects-canonical.md](redirects-canonical.md)；渲染与 cloaking 见 [rendering-seo.md](rendering-seo.md)；Cloudflare 层的 AI 爬虫封/放/收费是商业决策，见 [ai-crawler-policy.md](ai-crawler-policy.md) 第六节。

## 一、Edge SEO 是什么

**定义**：在 CDN 或边缘 worker 层做技术 SEO 变更，包括重定向、canonical、hreflang、robots.txt、X-Robots-Tag、meta 注入、JSON-LD 注入和页面级 A/B。worker 拦截并改写响应，不改源站或 CMS。「edge SEO」一词由 SALT.agency 的 Dan Taylor 在 2018 年 TechSEO Boost 上提出（据 Stox）。

**它解决两个问题**：
- **开发队列慢**：Will Critchlow 2016 年调查了约二十多位大公司 SEO。他们最想做的技术改动平均已等了 6 个月以上，42% 等了一年以上；首要原因是营销需求排在其他团队之后（53%）（[Moz 2016-05-16](https://moz.com/blog/how-long-are-seos-waiting-for-their-most-important-changes)，样本小，第三方调查）。
- **平台锁死**：遗留企业栈或封闭平台上，要改的东西没有编辑入口。注意平台会变：Shopify 现在可以用 `robots.txt.liquid` 改 robots.txt，官方还要求先撤掉 Cloudflare 等第三方变通（[Shopify 帮助](https://help.shopify.com/en/manual/promoting-marketing/seo/editing-robots-txt)）。上边缘前先查平台当前能力。

**关键事实**：爬虫只看到 CDN 返回的响应，看不到中间有没有 worker（Stox）。边缘响应就是页面的真实状态。这是边缘层的威力，也是 cloaking 风险的来源：技术上没有任何东西阻止你给 bot 和用户返回不同内容，只有纪律。

**worker 三阶段**（以 Cloudflare Workers 为例，不是通用标准）：
1. **改请求**：worker 在源站之前收到请求。它可以改写 URL、直接在边缘返回 3xx，或放行。
2. **改响应头**：源站响应后，worker 增改 `X-Robots-Tag`、`Link: rel=canonical`、缓存头、安全头。
3. **改响应体**：流式解析 HTML 并改写，例如注入 canonical、hreflang、title、meta robots、JSON-LD。Cloudflare 的工具是 HTMLRewriter。

**延迟**：SALT 测试 body 过滤平均增加约 10 ms，极端约 50 ms（第三方，经 Stox 转引，未核原始数据）。上线前把它计入 TTFB 预算（见 [cwv-playbook.md](cwv-playbook.md) 第四节）。

**与 GTM 的区别是时序**：边缘改写发生在爬虫收到响应之前；GTM 要等页面加载后在客户端改。不执行 JS 的爬虫看不到 GTM 注入的 canonical 或 JSON-LD（见 [rendering-seo.md](rendering-seo.md)「meta 注入红线」）。所以「用 GTM 修 canonical」不能替代 edge SEO。

Cloudflare Worker 最小骨架（三阶段各一段；**对全部流量生效，不判断 UA**）：

```js
export default {
  async fetch(request) {
    const url = new URL(request.url);

    // 阶段 1·改请求：边缘 301，源站不参与
    if (url.pathname === "/old-path") {
      return Response.redirect(new URL("/new-path", url), 301);
    }

    const origin = await fetch(request);
    // 复制响应：保留源站的状态码和响应头，否则 404 会被改成 200（软 404）
    const response = new Response(origin.body, origin);

    // 阶段 2·改响应头：参数页加 X-Robots-Tag
    if (url.searchParams.has("page")) {
      response.headers.set("X-Robots-Tag", "noindex, follow");
    }

    // 阶段 3·改响应体：只改 HTML，用 HTMLRewriter 流式注入 JSON-LD
    if (!(response.headers.get("content-type") || "").includes("text/html")) {
      return response;
    }
    return new HTMLRewriter()
      .on("head", {
        element(el) {
          el.append('<script type="application/ld+json">' +
            JSON.stringify({ "@context": "https://schema.org",
              "@type": "Organization", name: "示例品牌", url: url.origin }) +
            "</script>", { html: true });
        },
      })
      .transform(response);
  },
};
```

注入的 JSON-LD 要过序列化安全（`</script>` 逃逸）与实体规则，见 [schema-templates.md](schema-templates.md)「完全装载」节；上线前用 `schema_lint.py` 点验。

## 二、平台对照表

| 平台 | 运行时 | SEO 要点（官方，核对 2026-10-18） |
|---|---|---|
| **Cloudflare Workers** | V8 isolates；JS/TS/Wasm | HTMLRewriter 流式改写；KV 存重定向表。免费套餐每天 100,000 次请求、每次 CPU 10 ms（[限额](https://developers.cloudflare.com/workers/platform/limits/)） |
| **Cloudflare Snippets** | 轻量 JS | 只在 Pro/Business/Enterprise 可用；每次执行 5 ms、内存 2 MB、包 32 KB；适合改头和简单重定向；Version Management 不支持 Snippets（[文档](https://developers.cloudflare.com/rules/snippets/)） |
| **Akamai EdgeWorkers** | 边缘 JS | EdgeKV 是配套的分布式键值库，适合大规模重定向表（[EdgeKV](https://techdocs.akamai.com/edgekv/docs/welcome-to-edgekv)） |
| **Fastly Compute** | 任意 Wasm；官方 SDK 为 Rust、JS、Go、C++，Python 为 beta（[SDK](https://www.fastly.com/documentation/reference/compute/sdks/)） | `Surrogate-Control` 头单独控制 Fastly 缓存，与 `Cache-Control` 同时存在时优先（[文档](https://www.fastly.com/documentation/reference/http/http-headers/Surrogate-Control/)） |
| **AWS Lambda@Edge** | CloudFront 上的 Node.js 与 Python | 函数须建在 us-east-1；viewer response 事件不能改状态码（[限制](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-at-edge-function-restrictions.html)）。Stox 称其延迟高于纯边缘 worker（第三方） |
| **Vercel Routing Middleware** | 默认 Node.js，可选 Bun | 在缓存之前运行；可重写、重定向、加头（[文档](https://vercel.com/docs/routing-middleware)） |
| **Netlify Edge Functions** | Deno；TS/JS | 随站点一起版本化部署，支持 Deploy Preview 与回滚（[文档](https://docs.netlify.com/build/edge-functions/overview/)） |

选型第一问不是「哪家强」，而是「站点现在在哪个 CDN 上」。edge SEO 的收益以「已经在该 CDN」为前提；为 edge SEO 单独迁移 CDN 不成立（本套件口径）。

**常见用例 × 阶段**（全部对全量流量生效；本套件口径）：

| 用例 | 阶段 | 要点 |
|---|---|---|
| 边缘重定向（清链、批量迁移、非规范域归一） | 1 | 映射表放 KV / EdgeKV / Bulk Redirects；上线后逐跳核验 |
| robots.txt 兜底（平台改不动时） | 1/3 | 边缘直接应答 `/robots.txt`；先确认平台是否已开放编辑（如 Shopify）；与 Cloudflare 托管 robots.txt 区分（[ai-crawler-policy.md](ai-crawler-policy.md) 第四节） |
| X-Robots-Tag 控索引（分页、参数页、PDF） | 2 | 头级控制不动 HTML；非 HTML 文件只能用这个通道 |
| canonical / hreflang 批量修正 | 3 | HTMLRewriter 按 URL 规则改写；先采样验证再放量 |
| 规模化纠错（误 noindex、批量坏 title） | 3 | Stox 给的典型场景：对全站扫描并按规则修 |
| JSON-LD 注入 | 3 | 序列化安全 + `schema_lint.py` 点验 |
| 页面级 A/B | 3 | 按页面分组，见第五节 |

## 三、决策表：什么改边缘，什么进源码

**默认答案：进源码**（本套件口径）。边缘是绕过约束的通道，不是新的正确架构。源码有版本评审、测试和文档。worker 改多了，页面真实状态散在源码和边缘两处，迟早漂移。

边缘适合的三类场景：

| 场景 | 为什么用边缘 | 退场条件 |
|---|---|---|
| 遗留 CMS / 锁死平台改不动 | 源码路径不存在（第一节） | 平台迁移或解锁后，把规则搬回源码 |
| 时敏实验（页面级 A/B、活动期 noindex / canonical 调整） | 等一个发布周期，窗口就过了 | 实验结论固化后回源码；实验结束即删 worker 规则 |
| 收购站过渡期 | 无权改对方代码，但要先接管 canonical / 重定向 | 技术栈整合完成 |

不构成边缘理由的：新站、有正常发布管线的团队、「想绕过开发部」。最后一条最危险：绕过评审的改写层，迟早产生没人知道的页面状态。

## 四、审计检查项

审计已部署 edge worker 的站，固定查四件：

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 1. WAF / bot 规则在 worker 之前拦了 Googlebot | Search Console 网址检查看渲染截图；从日志取 Googlebot IP，用 `host <IP>` 反查须为 `googlebot.com` / `google.com` 并正向复核，或比对 [common-crawlers.json](https://developers.google.com/static/crawling/ipranges/common-crawlers.json)（[Google 验证文档](https://developers.google.com/crawling/docs/crawlers-fetchers/verify-google-requests)）；UA 探测法见 [ai-crawler-policy.md](ai-crawler-policy.md) 第五节 | 真 Googlebot 拿到 200、截图是页面 → 通过。临时拦截必须返回 503 或 429；验证页对爬虫也要改回 503；返回 200 的错误页或网络超时 → 失败（[Google 2024-12-24](https://developers.google.com/search/blog/2024/12/crawling-december-cdns)） |
| 2. 只对 bot 做边缘预渲染 | 读 worker 代码找 UA 分支；用浏览器 UA 和 Googlebot UA 各抓一次，比对正文 | 无 UA 分支 → 通过。有 UA 分支就是动态渲染：Google 称其为变通办法、不推荐；内容相近时一般不算 cloaking，内容不同就是 cloaking（[Google](https://developers.google.com/search/docs/crawling-indexing/javascript/dynamic-rendering)）。本套件只接受一个例外：给不渲染 JS 的社交/Bing 爬虫补预渲染，且排除 Googlebot（rendering-seo.md CSR 深读节） |
| 3. worker 是全站单点故障 | 查部署记录：是否版本化、路由是否收窄、能否一键回滚 | 三项都有 → 通过；缺一项记 P1（本套件口径）。Cloudflare Snippets 不受 Version Management 管，回滚要靠代码仓库 |
| 4. 注入残留 | worker 回滚或改版后跑 `monitor.py diff`，看 title / meta_desc / canonical / og_title / og_desc 是否出现无法解释的漂移（见第六节） | 漂移都能对上一次已知变更 → 通过 |

## 五、铁律：对全量流量生效，绝不按 bot 分流

**cloaking 是不可协商的边界。** Google 的定义：为操纵排名、误导用户，给用户和搜索引擎呈现不同内容；例子包括只在请求方是搜索引擎时插入文字或关键词（[Google 垃圾政策](https://developers.google.com/search/docs/essentials/spam-policies#cloaking)）。Bing 也把给爬虫和用户展示不同内容列为操纵行为（[Bing 指南](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)）。

- 每一条边缘变更作用于全部流量。边缘层没有合法的「按 bot 分流改内容」。
- 页面级 A/B 按 Google 的测试规则做（[A/B 测试最佳实践](https://developers.google.com/search/docs/crawling-indexing/website-testing)）：不给 Googlebot 单独一组 URL；多 URL 测试时变体页 `rel="canonical"` 指回原页；跳转用 302 不用 301；实验结束尽快撤掉。Googlebot 一般不带 cookie，只会看到无 cookie 用户的版本。
- 本套件口径：按页面分组（每页只有一个版本，bot 和用户看到同一版）比按用户分组更安全。
- 配套纪律：worker 代码入库、写变更日志、与源码同级评审。否则「这页为什么是这个 canonical」会变成考古题。

## 六、与套件工具接线（检查清单）

| 检查什么 | 怎么查（参数已用 `--help` 核对） | 通过 / 失败 |
|---|---|---|
| 注入字段漂移 | `python3 scripts/monitor.py init --site https://example.com --key-pages /,/pricing`，之后每次发布跑 `python3 scripts/monitor.py run` 和 `python3 scripts/monitor.py diff --format text` | diff 里 title / meta_desc / canonical / og_title / og_desc 的变化都能对上已知发布 → 通过；出现 `noindex_added`（meta robots 或 X-Robots-Tag 任一通道）→ 失败，先查最近的 worker 变更 |
| 边缘重定向链 | `python3 scripts/redirect_chain.py https://example.com/old-path --max 3` 看跳数、状态码、终态；脚本不输出响应头，判断哪一跳来自边缘另跑 `curl -sIL https://example.com/old-path`，看每跳的 `server`、`cf-ray` 等头 | 一跳到位、终点 200 → 通过；超过 `--max`（默认 5）判 CRITICAL → 失败 |
| 全站 canonical / hreflang | `python3 scripts/site_crawl.py example.com --max 500 --json` 抓全站面，再抽样核对 worker 改写结果 | 抽样页 canonical / hreflang 与规则一致 → 通过 |
| 注入的 JSON-LD | `python3 scripts/schema_lint.py https://example.com/page` | 无悬空 `@id`、无占位符 → 通过 |
| 只改 HTML、保留状态码 | `curl -sI https://example.com/不存在的页`，看状态码和 `content-type` | 源站 404 经过 worker 仍是 404 → 通过；变成 200 → 失败（软 404） |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 第三方：Patrick Stox《[Edge SEO](https://patrickstox.com/technical-seo/edge-seo/)》（三阶段模型、平台对照、SALT 延迟数据、Dan Taylor 术语史）；Will Critchlow，Moz 2016-05-16（开发队列调查）。
- 官方：正文各处链接（Cloudflare、Akamai、Fastly、AWS、Vercel、Netlify、Shopify、Google、Bing），全部 2026-10-18 打开核对。
