# 图片 SEO 与视觉搜索(被 AI 看见的图片层)

> 建立于 2026-10-09。来源:Google Search Central 官方文档为基准;Backlinko 65,388 次 Lens 搜索研究为最大行业实证;Getty 判例为法律层。与 [视频 GEO 指南](video-geo-guide.md) 互补。

## 一、视觉搜索的量级与行为(2026)

- **Google Lens 月视觉搜索 ~200 亿次**(2025 Q3 财报 Pichai 口径,称"绝大部分是增量查询");2026-09-24 起 **Search Console Performance 报告新增 multimodal 过滤器**(Lens/Circle to Search/图片上传/右键搜图),并同步进生成式 AI 报告——测量层已就位(官方)。
- 行为差异:视觉搜索解决**"说不出口的查询"**(风格/外观/同款),~20% 带商业意图(行业转述官方);找对商品比文字快 5 倍(YouGov);与文字 organic 前 10 重叠仅 **15%**——独立优化面(Backlinko)。

**量级与"现实落差"(2026-10 核实)**:①Google Images 旧口径占全部搜索 ~26.79%(Moz/Jumpstatic 时代数据,常被误引为"流量占比")——**实际引荐流量通常仅占站点总流量 ~2%(seoClarity 多站实测)、CTR ~3%**(2026 统计汇编);引用查询份额与流量份额时必须分开,这是图片 SEO 报告最常见的夸大;②Define Media Group 案例:Google 图片搜索 UI 改版后 87 个域名图片引荐 **−63%**——UI 层一改,图片流量即蒸发,与 Discover 同属"不可作基线"渠道;③Lens 月 20 亿次中 **~40 亿次/月与购物相关**(Netguru 转述官方口径,注意与其他来源的口径差异);④优化案例:某电商图片 SEO 整改后点击 **+85.86%**(服务商案例,自述口径)——图搜流量"低基数+可翻倍"并存。

**图搜流量获取案例(分行业,2026-10)**:

| 行业 | 图搜定位与打法 |
|---|---|
| **电商/DTC** | 流量入口不在 Google Images 结果页而在 **Lens 镜头流与 AIO 商品轮播**:白底主图+多角度实拍+Product schema+GMC feed 四件套;Pinterest 80B+ 商品库承接"无品牌词"搜索(80% 无品牌)——图库化 listing 是被 Lens/AI 检索的前提 |
| **教程/手工艺/食谱站** | Google Images 传统主力(步骤图/成品图查询意图强):**每步一图+图注含步骤词**("how to bind a quilt 第 3 步")+教程页 schema(HowTo 退役但图文结构仍有效);Backlinko 实证 Lens 结果 ~1/3 图片位于页面上方 25%——**首屏放成品图** |
| **旅游/本地** | 实景图+GPS 无用(官方),靠**实体关联**:地标/店名入 alt+图注+页面实体;Google Maps 照片生态是第二图搜入口 |
| **媒体/出版** | Discover 大图逻辑(见 discover-news-seo.md)——图片层与 Discover 属同一入口家族 |
| **B2B/制造** | 参数图/图纸/白底产品图;工业品查询"part number+图"在 Lens 有增量(行业观察,标注) |

## 二、Lens 排名的实证(Backlinko 65,388 次搜索)

| 因子 | 实测 |
|---|---|
| 页面权威(Moz DA 均值) | **64.4**——页面主题与权威主导 |
| 移动友好 | 90.6% 结果 |
| 图片在页面上方 | ~1/3 在前 25% |
| alt 文本匹配 | **仅 11.4%**——alt 作用有限 |
| 文件名匹配 | 22.6% |

**结论:视觉搜索优化≈页面级 SEO(主题+权威+移动),不是元数据游戏。**

**由实证衍生的 Lens 优化优先级清单(按实测因子强度排序)**:

1. **页面主题与权威**(DA 64.4 均值):把图片放在**已有关联排名的页面**上——新图发在权威老页>新建页面挂图;站点级权重投资(内链/外链)先于图片层微调;
2. **移动友好**(90.6%):CLS 控制用 width/height 属性(图片加载跳动是移动友好硬伤);
3. **图放页面上方**(~1/3 在前 25%):目标进前 25%——首屏即图,教程类尤其(成品图先行);
4. **alt 仍要写但别指望**(11.4%):合规+无障碍价值>排名价值;写法=描述画面+上下文实体,不堆词;
5. **文件名**(22.6%):轻量线索,顺手做——`red-leather-sofa-3seat.webp` 式,一秒成本换两成结果占比;
6. **同款多图策略**:主图(白底)+场景图+细节图各承担不同查询面,Lens 对"视觉相似"的召回跨多图;
7. **验证方法**:自建 20 个目标查询(拍自家图/竞品图)月度人工跑 Lens 记录排名——Lens 无主流 rank tracker,人工面板最可靠;可由 Lens SERP 端点半自动化(DataForSEO,套件 DataForSEO 集成同源)。

## 三、AI 引擎怎么"看"图

- 官方口径:AIO/AI Mode 无额外图片技术要求;"高质量图片支撑文字内容"是官方最佳实践;Gemini 原生多模态;ChatGPT/Perplexity 已支持图搜并嵌出来源图(行业实测)。
- **AIO 引用图来自已索引页面的 `<img src>`——CSS 背景图永不索引**(AI Visible);首选图三信号:`primaryImageOfPage`、实体 `image`、`og:image`(最常用也最常失效);≥1200px,避免 logo/大字图/极端长宽比。
- 2025-11 起 Google 曾在 AIO 内测试 AI 生成配图(文字引用真实站点但配图 AI 生成),争议后暂停(行业)。
- **未证实**:图片视觉内容(非 alt)影响文字页被引率——无对照研究,仅从业者共识。

**首选图三信号的落地顺序与核对命令(AIO/Og 抓取实用层)**:

1. **信号一致性**:`og:image`、schema `image`、`primaryImageOfPage` 三处指向**同一 URL**(不一致时 AI 取图不确定);核对:

```bash
curl -s https://example.com/page | grep -o -e 'og:image" content="[^"]*' -e '"image":\s*"[^"]*' | sort -u
```

2. **og:image 绝对 URL** 带协议域名(相对路径是 OG 头号错误);尺寸写入 `og:image:width/height`(部分抓取器据此预筛);
3. **schema `image` 给数组**(多比例:1:1/4:3/16:9),首项=主图;
4. **别用 CSS 背景图承载关键视觉**(永不索引)——hero 区改 `<img>`+object-fit;
5. **robots 别拦图**:站点 robots 允许页面但 `Disallow: /uploads/` 是常见静默事故;`Googlebot-Image` 单独放行亦可;
6. **图片 URL 稳定**:同图换 URL=重置积累(Lens/AIO 的图片级缓存按 URL)。

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

**图片层技术债排查命令(月度/季度审计用)**:

```bash
# alt 缺失扫描(爬取后)
grep -rIo '<img[^>]*>' pages/ | grep -v 'alt=' | wc -l
# 超 1200px 大图占比(Discover/AIO 首选图资格)
find assets/ -name '*.webp' | xargs -I{} sh -c 'identify -format "%w %h\n" {}' | awk '$1>=1200' | wc -l
# AVIF/WebP 采用率
find assets/ \( -name '*.jpg' -o -name '*.png' \) | wc -l
# CDN 对图片 bot 的可达性
curl -s -A "Googlebot-Image/1.0" -o /dev/null -w "%{http_code}\n" "https://cdn.example.com/hero.webp"
```

**图片 sitemap 实操全流程(2026-10 官方文档口径,七步)**:

1. **判断是否需要**:图片被 JS 延迟加载/藏在深层页面/未被常规抓取覆盖时收益最大;静态 HTML 直出的图片通常不需要(官方:"help Google discover images you might not otherwise find");
2. **确认标签集**:2022 年后 Google **仅支持 `<image:image>`+`<image:loc>` 两个标签**——`image:caption`/`image:title`/`image:license` 等可选标签已废弃,生成器若还在输出属无效功(rankite/opt-img 核实);
3. **命名空间**:`xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"`;每个 `<url>` 条目**最多 1,000 张 `<image:image>`**(硬上限);
4. **CDN 跨域**:`<image:loc>` 可指向与页面不同的域(CDN)——前提:①CDN 域在 **GSC 验证**(或以 DNS 前缀方式可控);②CDN robots.txt 不拦 Googlebot;③CDN 不弹验证码/热链拦截(WAF 规则放行 `Googlebot-Image`);
5. **生成路径**:WP(Yoast/Rank Math 自动并入常规 sitemap 的 image 扩展)/Next.js(next-sitemap 的 image 选项)/自研(爬自家模板 DOM 取 `<img src>`+srcset 首项);
6. **提交与验收**:

```bash
# 结构校验(本地)
xmllint --noout sitemap-images.xml
# 跨域图片域可抓
curl -s -A "Googlebot-Image" -o /dev/null -w "%{http_code}\n" "https://cdn.example.com/img.jpg"
# 数量上限
grep -c '<image:image>' sitemap-images.xml
```

   GSC 提交后看「Sitemaps」读取状态;**图片索引量看 GSC「索引>页面」没有图片维度**——改用 `site:cdn域` 或 Image 内 `indexifembedded` 组合观察(官方无图片索引报告,这是长期缺口);
7. **维护**:新图随发布自动进 sitemap(模板层注入);季度审计一次死链图(`image:loc` 404 会被静默丢弃,无 GSC 报错)。

**Lens 购物意图优化(product feed 联动,2026-10)**:

- **图是 Lens 商务流的匹配键**:Lens 拍物→Shopping Graph 匹配→商品卡;匹配质量=**feed 图片质量×schema 一致性**;
- **Merchant Center 侧四动作**(官方 Help+2026 实践):①**图片 ≥1,500×1,500px**(2026 MC 最佳实践口径,白底主图+至少一张场景图);②开启 **"surfaces across Google"**(免费 listing 进搜索/图片/Lens 面);③**local inventory feed**(本地库存)接入后进"附近有货"类 Lens 结果;④feed 的 `image_link` 与页面 Product schema `image` **同图同 URL**(一致性即匹配信号);
- **页面侧三动作**:Product schema 给全(`image`/`price`/`availability`/`brand`);商品页多角度实拍(非只渲染图);**避免主图带促销文字/水印**(feed 政策+Lens 匹配双输);
- **意图分层**:Lens 购物查询 ~20% 带商业意图,但**转化率高于文字**(看过实物);教程/搭配类意图走内容页优化(见上表),商务类走 feed——同一张图可以同时服务两条路(页面内嵌+feed 引用同 URL);
- **Pinterest 侧**:商品 Pin+目录同步是第二视觉商务入口(80B+ listing、80% 无品牌词搜索)——跨境电商图搜不可只做 Google。

## 四点五、视觉搜索分析工具(2026-10)

- **GSC multimodal 过滤器(2026-09-24 起,官方)**:Performance 报告内直接看 Lens/Circle to Search/图片上传/右键搜图带来的展示点击,且并入生成式 AI 报告——**首个官方视觉搜索测量面**;局限:仍是"搜索外观"维度,无单独的 Lens 关键词;数据回溯期从上线日起算,历史不可补;
- **GSC「搜索效果>图片」维度的旧三招**:按页面看图片展示量;按国家看 Lens 热区(印度/印尼/巴西视觉搜索占比高——市场锚);CTR 异常页=图与意图错配的排查入口;
- **第三方**:`site:` 运算符+图片反搜(Google Lens 自测:拿自家产品图搜,看竞品是否抢占同款位);Semrush/SE Ranking 的图片 SEO 审计(alt 缺失/尺寸/格式扫描);DataForSEO 有 Lens SERP 端点(套件 DataForSEO 集成同源);
- **AIO 图片引用监测**:AI Visible 类工具查"AI 引用我的哪张图"(自评置信有限);Gumshoe/SE Ranking 的 GEO 报告部分覆盖图片引用;
- **自建最小方案**:GSC 导出 multimodal 过滤数据→按页聚合→对照 GA4 landing page 转化——**视觉搜索流量的价值要用转化而非流量衡量**(低 CTR 高转化是常态,行业共识)。

## 五、市场角度

- **中国**:淘宝拍立淘(2014 年,全球最早电商以图搜图)白底商品图+搜同款;百度识图偏通用——商品图是中文电商图片层主战场;
- **韩国**:Naver Smart Lens+쇼핑렌즈(拍商品→AI 简报→比价,已接 AI Tab)——识图+比价+AI 闭环;
- **电商视觉搜索**:Pinterest 80B+ 商品 listing、80% 搜索无品牌词;商品图+Product schema 是图片层 GEO 的最大商业入口(BrightEdge:AIO 商品轮播比重上升)。

**三大视觉商务体系对照(给跨境客户的分市场话术骨架)**:

| 维度 | Google Lens | 淘宝拍立淘 | Naver Smart Lens |
|---|---|---|---|
| 入口 | 系统级(Camera/Chrome/Circle to Search) | App 内(电商闭环) | Naver App+购物 Tab |
| 匹配层 | Shopping Graph(feed+schema) | 阿里商品库(白底主图为主) | Naver 商品目录+AI 简报 |
| 转化路径 | 搜索→商品卡→站(多跳) | 拍→同款→下单(一跳) | 拍→AI 简报→比价(信息层) |
| 官网机会 | feed+schema 可竞争 | 基本无(生态封闭),品牌号+天猫店 | Smart Store 承接 |
| 共同规律 | **白底主图是三体系通用的匹配锚**;多角度实拍加分;促销水印减分 | | |

## 六、版权与抓取生态

- AI 抓取控制:robots tokens(GPTBot/ClaudeBot/Google-Extended——只管 Gemini 训练不影响搜索);**TDMRep**(W3C)声明权利保留;Cloudflare 一键封 AI bot+付费抓取(2025-07 起)是摄影/图库主流执行层;
- **Getty v. Stability AI(英国高院 2025-11)**:训练数据版权诉败,但 AI 图复现 GETTY 水印的**商标索赔存活**——水印是事后维权证据,防抓取作用无证据;
- C2PA/Content Credentials 成来源证明标准,但**证明来源≠证明所有权**。

**C2PA 采用现状盘点(2026-10)**:

- **平台侧(已成主流)**:TikTok 2025-01 集成 Content Credentials 且已加入 **C2PA 指导委员会**(c2pa.org 官方公告)——三层检测并行;LinkedIn 支持 Content Credentials 展示(官方 Help 页,2025 起);Meta/Google 平台级 AI 标签并行;Adobe 全线(Photoshop/Firefly)自动附加,Microsoft 用于 Azure AI;
- **硬件侧**:消费手机与专业广播摄像机身开始内置签 名(SoftwareSeni 2026 盘点)——拍摄即签名是趋势,但存量图片无凭证;
- **法规推力**:**EU AI 透明度规则 2026-08-02 生效**——AI 生成内容需标识,C2PA 发布配套实施指南(AI labeling implementation guide);美国州法+平台政策并行推;
- **现实差距**:Media Provenance Summit 参会者观察**采用仍滞后于宣传**(行业活动口径);验证工具(Verify 工具)在浏览器端可剥(截图即失效)——**凭证链在转链平台间大量断裂**;
- **SEO 含义(务实版)**:C2PA 当前对排名无已证实影响(Google 未如此声明);价值在①新闻/纪实类内容的**信任差异化**(Discover/News 的 E-E-A-T 叙事补充);②电商图防盗用举证;③AI 训练数据授权谈判的技术底座(TDMRep/robots 之外的第二层权利声明)。把它当合规/信任投资,不是排名杠杆。

## 来源

官方:Google 图片 SEO/AI features 文档、SC multimodal 报告博客(2026-09-24)、图片 sitemap 文档(两标签现状)、Large Images 案例研究、Merchant Center Product data specification/优化建议。行业:Backlinko Lens 研究、seoClarity(实际引荐 ~2%)、Define Media Group(UI 改版 −63%)、Netguru(Lens 20B/购物 4B)、amraandelma 汇编(CTR ~3%)、85.86% 案例与服务商案例(自述)、rankite/opt-img(sitemap 标签废弃)、MBA 2026(1,500×1,500px)、AI Visible(AIO 图片,自评置信 74/100)、BrightEdge、YouGov、SSRN 电商视觉搜索。C2PA:c2pa.org(TikTok 委员会)、LinkedIn Help、SoftwareSeni 2026 盘点、EU AI 法规 2026-08-02 生效报道、Media Provenance Summit 观察。市场:拍立淘/Naver 官方新闻稿。法律:Guardian/Getty 判决报道。GitHub:alt 生成器生态(Nutlope 137★/accessibility-alt-text-bot 103★ GitHub 官方 Action)——**图片 SEO skill 是明确空白**。未证实项:B2B 工业品 Lens 增量为行业观察;视觉搜索"低 CTR 高转化"为共识非硬数据;Google Images 26.79% 为 Moz/Jumpshot 旧口径勿当现值引用。
