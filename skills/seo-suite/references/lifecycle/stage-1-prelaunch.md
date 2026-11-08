# 阶段 1 打法卡:上线前(RQ-237 第 2 批)

有代码、有本地预览或预发环境,正式域名还没收录(或站点能打开但 robots 全封、首页 noindex)。这个阶段的目标是**上线当天不出低级错误、上线后能马上开始收录和测量**。上线后再发现 canonical 指向预发域名、robots 没撤,往往要几周才恢复。

`plan.py build` 在这个阶段只从 `stages` 含 1 的打法里选,不出「刷新旧文」「掉量排查」这类。

## 一、上线清单

```bash
python3 scripts/launch_check.py --url http://localhost:3000 --allow-local --prod-host example.com --md
```

- 清单在 `data/launch-checklist.json`,共 25 项:18 项脚本自动查,7 项手动(GSC / Bing 验证、转化埋点、301 映射、社媒一致、法律页、上线后 CWV)。
- 每项有级别:**block** 不过不能上线,**warn** 上线后两周内补,**info** 可选。
- **每项写负责人**:默认是角色(开发、内容、设计、站长、市场、产品负责人),把具体的人和截止日写进 `seo-ops/plan/launch-owners.json`:`{"gsc_verify": "张三", "gsc_verify@due": "2026-12-01"}`。没改的会在报告里标「默认角色,请改成具体的人」。
- `--prod-host` 一定要给:本地预览上最常见的错是 canonical、og:image 指向 `localhost` 或预发域名,不给正式域名就查不出来。
- 抽样:首页之外,从 sitemap 按第一段路径各取一页(每个模板都抽到),默认 8 页,`--sample` 调。
- 本地预览必须加 `--allow-local`(只放行本机回环地址,私网仍然拒绝,和 `site_crawl.py` 同一套守卫)。

几项判据的依据:

| 项 | 判据 | 依据 |
|---|---|---|
| robots | `User-agent: *` 下没有 `Disallow: /` | 预发环境常用全站封锁,上线时要撤 |
| noindex | 抽查页都没有 noindex | noindex 生效的前提是页面能被抓取;robots 封住的页面看不到 noindex,仍可能被收录([block-indexing](https://developers.google.com/search/docs/crawling-indexing/block-indexing)) |
| canonical | 绝对地址、指向正式域名 | [consolidate-duplicate-urls](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls) |
| hreflang | 列出自身、用完整地址;x-default 建议加 | 「每个语言版本必须列出自身和其他版本」,x-default 是建议([localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions)) |
| sitemap | 能读到、≥1 条、robots.txt 里声明 | [sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview) |
| 软 404 | 不存在的地址返回 404 | 返回 200 的错误页会被当成重复的空页 |
| favicon | 有 | 搜索结果里显示站点图标([favicon](https://developers.google.com/search/docs/appearance/favicon-in-search)) |
| 速度 | 首页 < 800 ms | 本地预览只作参考;上线 28 天后看 CWV 实测(手动项) |

清单的项目参考了 Google [SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)和公开的网站上线 SEO 清单([v9digital](https://www.v9digital.com/guides/website-launch-seo-checklist),核对 2026-11-08),按「脚本能不能查」拆成自动和手动两类。

## 二、本地预览体检

上线清单只抽查模板;全站问题用体检链跑一遍:

```bash
python3 scripts/site_crawl.py http://localhost:3000 --allow-local
python3 scripts/health_score.py …
```

CRITICAL 清零才上线。按产品线的页面类型分组看,一类模板的问题一次修完。

## 三、测量就绪

- GSC 用域名资源(DNS TXT 验证),上线当天提交 sitemap;Bing Webmaster 可以从 GSC 导入,顺手开 IndexNow([indexnow.org](https://www.indexnow.org/documentation))。
- 主转化事件在预览上触发一次,确认统计后台能记到。没有埋点就上线,第一个月的自然流量就没法归因。

## 四、AI 可见度

- 在 robots.txt 里对各 AI 爬虫做明确决定(放行或不放行都行,但要是有意的),见 [ai-crawler-policy](../technical/ai-crawler-policy.md)。
- llms.txt 是可选项(Google 搜索不需要),按产品线列核心页,见 [llms-txt-guide](../content/llms-txt-guide.md)。
- 首页 Organization(含 sameAs)、产品页 SoftwareApplication 或 Product 结构化数据,名称和价格与定价页一致。

## 五、上线当天

- 提交 sitemap、推 IndexNow;目录和产品上架平台的提交稿提前起草好(用户自己点提交)。
- 存一份基线(全部 URL、状态码、canonical、title),之后每周运营单和它比。
- 替换旧站的情况属于迁移,按阶段 5 做:先存旧站基线和 301 映射表。

## 六、什么时候进下一阶段

站点可访问、robots 和 noindex 撤了 → 阶段 2 刚上线。有 GSC 数据后,`onboard.py metric` 记下近 28 天展示和点击,阶段按真实数据判。
