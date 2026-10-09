# 图片 SEO 与视觉搜索(被 AI 看见的图片层)

> 建立于 2026-10-09。来源:Google Search Central 官方文档为基准;Backlinko 65,388 次 Lens 搜索研究为最大行业实证;Getty 判例为法律层。与 [视频 GEO 指南](video-geo-guide.md) 互补。

## 一、视觉搜索的量级与行为(2026)

- **Google Lens 月视觉搜索 ~200 亿次**(2025 Q3 财报 Pichai 口径,称"绝大部分是增量查询");2026-09-24 起 **Search Console Performance 报告新增 multimodal 过滤器**(Lens/Circle to Search/图片上传/右键搜图),并同步进生成式 AI 报告——测量层已就位(官方)。
- 行为差异:视觉搜索解决**"说不出口的查询"**(风格/外观/同款),~20% 带商业意图(行业转述官方);找对商品比文字快 5 倍(YouGov);与文字 organic 前 10 重叠仅 **15%**——独立优化面(Backlinko)。

## 二、Lens 排名的实证(Backlinko 65,388 次搜索)

| 因子 | 实测 |
|---|---|
| 页面权威(Moz DA 均值) | **64.4**——页面主题与权威主导 |
| 移动友好 | 90.6% 结果 |
| 图片在页面上方 | ~1/3 在前 25% |
| alt 文本匹配 | **仅 11.4%**——alt 作用有限 |
| 文件名匹配 | 22.6% |

**结论:视觉搜索优化≈页面级 SEO(主题+权威+移动),不是元数据游戏。**

## 三、AI 引擎怎么"看"图

- 官方口径:AIO/AI Mode 无额外图片技术要求;"高质量图片支撑文字内容"是官方最佳实践;Gemini 原生多模态;ChatGPT/Perplexity 已支持图搜并嵌出来源图(行业实测)。
- **AIO 引用图来自已索引页面的 `<img src>`——CSS 背景图永不索引**(AI Visible);首选图三信号:`primaryImageOfPage`、实体 `image`、`og:image`(最常用也最常失效);≥1200px,避免 logo/大字图/极端长宽比。
- 2025-11 起 Google 曾在 AIO 内测试 AI 生成配图(文字引用真实站点但配图 AI 生成),争议后暂停(行业)。
- **未证实**:图片视觉内容(非 alt)影响文字页被引率——无对照研究,仅从业者共识。

## 四、图片 SEO 要素清单(官方)

1. **alt**:最重要元数据;描述性+上下文相关,禁堆砌;图片作链接时兼作锚文本;inline SVG 用 `<title>`;
2. **文件名**:"非常轻量线索";短、描述性、本地化翻译;
3. **页面上下文**:主题来自页面内容+图注+图片标题——**图文近置**;
4. **结构化数据**:`image` 属性;首选图三信号(见上);
5. **图片 sitemap**:可发现未链接图片;`<image:loc>` 允许跨域(CDN 需 GSC 验证);
6. **格式**:索引 BMP/GIF/JPEG/PNG/WebP/SVG/**AVIF**;CSS 图不索引;srcset 需 src 回退;**同图同 URL** 利缓存;
7. **EXIF/GPS:官方明确不用**(Mueller/Splitt 口径)——geotag for SEO 是过时建议;
8. **性能**:AVIF/WebP 比 JPEG 省 25–35%;LCP 图忌 lazy-load;
9. **退出**:204/空 200 内联链接,非 cloaking 无处罚风险。

## 五、市场角度

- **中国**:淘宝拍立淘(2014 年,全球最早电商以图搜图)白底商品图+搜同款;百度识图偏通用——商品图是中文电商图片层主战场;
- **韩国**:Naver Smart Lens+쇼핑렌즈(拍商品→AI 简报→比价,已接 AI Tab)——识图+比价+AI 闭环;
- **电商视觉搜索**:Pinterest 80B+ 商品 listing、80% 搜索无品牌词;商品图+Product schema 是图片层 GEO 的最大商业入口(BrightEdge:AIO 商品轮播比重上升)。

## 六、版权与抓取生态

- AI 抓取控制:robots tokens(GPTBot/ClaudeBot/Google-Extended——只管 Gemini 训练不影响搜索);**TDMRep**(W3C)声明权利保留;Cloudflare 一键封 AI bot+付费抓取(2025-07 起)是摄影/图库主流执行层;
- **Getty v. Stability AI(英国高院 2025-11)**:训练数据版权诉败,但 AI 图复现 GETTY 水印的**商标索赔存活**——水印是事后维权证据,防抓取作用无证据;
- C2PA/Content Credentials 成来源证明标准,但**证明来源≠证明所有权**。

## 来源

官方:Google 图片 SEO/AI features 文档、SC multimodal 报告博客、Chrome 图片交付。行业:Backlinko Lens 研究、AI Visible(AIO 图片,自评置信 74/100)、BrightEdge、YouGov、SSRN 电商视觉搜索。市场:拍立淘/Naver 官方新闻稿。法律:Guardian/Getty 判决报道。GitHub:alt 生成器生态(Nutlope 137★/accessibility-alt-text-bot 103★ GitHub 官方 Action)——**图片 SEO skill 是明确空白**。未证实项见文中标注。
