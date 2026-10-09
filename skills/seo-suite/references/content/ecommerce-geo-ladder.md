# 电商 GEO 阶梯(五级)与市场分叉

> 建立于 2026-10-09。来源:Google Merchant/结构化数据官方文档、[ucp.dev](https://ucp.dev)(UCP 官方,Apache-2.0)、[agentic-commerce-protocol](https://github.com/agentic-commerce-protocol/agentic-commerce-protocol)(ACP 官方 spec,OpenAI+Stripe)、[Shopify/ucp-cli](https://github.com/Shopify/ucp-cli)(79★)、市场数据见各条目标注。按证据纪律:UCP/AIO 内 free listings 属进行中状态,不承诺排名与转化。

## 一、五级阶梯(从基础到 agent 交互,逐级验收)

| 级 | 层 | 动作 | 验收 |
|---|---|---|---|
| **L1** | 产品数据 | 全 SKU 部署 Product+Offer(name/image/**price 纯数字**/priceCurrency ISO 4217/availability);接入 Merchant Center free listings,feed 与页面 schema 价格一致 | Rich Results Test 零 error;GSC「商家信息」有效;feed 价格差=0 |
| **L2** | 评价信号 | AggregateRating/Review 挂在 Product 上(挂 Organization 属 self-serving 不出富结果);官网评分与 marketplace 店铺同步(不一致是 AI 提取噪声) | 星级富结果展示;reviewCount 与平台一致 |
| **L3** | 内容层 | 比较页/选购指南/buying guide 覆盖 best/vs 类查询(AIO 最常引的产品推荐形态) | 目标查询 AIO 引用可见 |
| **L4** | marketplace 分工 | 交易型宽词让给 marketplace(域名权威压制官网,土/印尤甚);官网争品牌词/长尾/内容词/售后查询 | 品牌词官网第一;transactional 由 marketplace 承接 |
| **L5** | agent 交互 | 价格/库存对 AI 可读;发布 `/.well-known/ucp` 声明;AI 爬虫不恶意封锁 | UCP profile 可解析;AI Mode/Gemini 可取价 |

### 一点五、L1–L5 各级实操细节与验收命令(2026-10 深挖轮)

**L1(产品数据)——细节**:

- 全 SKU 含**停产/清仓 SKU**(带 `availability: OutOfStock`)——断货下架页保留是长尾+比价流量入口,整页删除=丢积累;
- `image` 数组:主图(白底)+辅图;主图 URL 与 GMC feed `image_link` **同 URL**;
- 价格同步机制:页面价(渲染后 DOM 里的价,非 JS 异步后到的价——Google 渲染等待有限)、schema 价、GMC feed 价三方一致;促销期用 `priceValidUntil` 标截止;
- 验收命令:

```bash
# schema 价格纯数字(应输出不带 $ 与逗号的数字)
curl -s https://shop.example.com/p/123 | grep -o '"price":\s*"[^"]*"'
# 页面可见价与 schema 价一致性(抽 20 SKU 人工比对;脚本抓 DOM 文本价)
# 富结果资格
# → Rich Results Test API: POST https://searchconsole.googleapis.com/v1/urlTesting/tools/richResults?   (GSC API,或手工 Rich Results Test)
# GMC 一致性 → Merchant Center「Diagnostics」零 Critical issue;feed vs 页面价差=0(抽检)
```

**L2(评价信号)——细节**:

- `aggregateRating` 挂在 `Product` 内(挂 `Organization` 属 self-serving,官方明确不出星);`reviewCount`/`ratingCount` 二选一与平台一致;
- 第三方平台评价同步策略:官网聚合页引用 marketplace 评论需注明来源(编造评论数是人工处置红线);
- 验收:GSC「商家信息」报告星标覆盖;Rich Results Test 显示 Rating;月度抽查 reviewCount 与 marketplace 店铺页一致。

**L3(内容层)——细节**:

- 页型矩阵:best(榜单)/vs(对比)/alternatives/-sizing/how-to-choose;每页**真实结构化信息**(参数表/评分维度),AI 引用偏好可抽取的表格与要点;
- 内链:内容页→产品页(锚文本带产品词);产品页→相关内容页(购买犹豫查询承接);
- 验收:目标 best/vs 查询在 AIO/Gemini 手工月检 20 词,记录引用域名;内容页 organic 进前 20。

**L4(marketplace 分工)——细节**:

- 官网保品牌词 SERP 第一(含 sitelinks);transactional 词让位 marketplace 的**验证方法**:搜核心 transactional 词,前 10 中 marketplace 占比>50% 即认清现实、预算转内容层;
- marketplace 店铺名与官网品牌词一致(品牌词 SERP 里官网+店铺双占位)。

**L5(agent 交互)——细节(2026-10 更新)**:

- **Merchant Center「UCP Integration Hub」已在美国先上线**(SEL/Seroundtable 2026 报道;官方文档 developers.google.com/merchant/ucp):商家可在 GMC 内连接 cart/checkout/identity,启用 AI Mode/Gemini/Search 的 agentic 动作——**L5 的入口从"手写 well-known 文件"升级为"GMC 后台向导+文件"双路径**;
- `/.well-known/ucp` 声明用 [Shopify/ucp-cli] 生成校验;AI 爬虫 UA(GPTBot 等)在 robots 里留白名单可读层(价格页不设登录墙);
- 验收命令:

```bash
# UCP profile 可解析
curl -s https://shop.example.com/.well-known/ucp | python3 -m json.tool
# ucp-cli 校验(Shopify 官方工具)
npx @shopify/ucp-cli validate --url https://shop.example.com
# AI 爬虫可达价格页(应 200)
curl -s -A "GPTBot" -o /dev/null -w "%{http_code}\n" https://shop.example.com/p/123
```

## 二、Product schema 实操清单(最常见错误即失败模式)

必填(merchant listing):`name`、`image`、`offers.price`、`offers.priceCurrency`;购物功能另需 `availability`。推荐:`gtin`/`sku`/`brand`/`mpn`、`Product.category`。
**七个高频错误**:①price 带货币符号/千分位(`$1,299.99` 非法→`1299.99`);②缺 priceCurrency;③缺 availability;④schema 与页面可见价/GMC feed 不一致(舍入差即报错);⑤缺 offers 节点;⑥单品误用 AggregateOffer;⑦主题/插件更新后 schema 过期。

**扩至 Top 10(2026-10 补,含 warning 级;Yoast/Rank Math/3wBiz/CommerceGurus/GSC 论坛汇总)**:

- ⑧**缺 `sku`/`gtin`/`brand`(warning)**:merchant listing 资格可保但商品匹配质量受损——GSC「商家信息」会列 "缺字段" 警告;GTIN 对了才进 Shopping Graph 的全球商品实体(官方 Product data 规范);
- ⑨**缺 `aggregateRating`/`review`(warning)**:"要么 offers 要么 review/aggregateRating" 的 GSC 提示——无评分=无星标富结果,商品 CTR 显著受损;但**为消 warning 造假评分**是人工处置直接原因,宁缺勿假;
- ⑩**`priceValidUntil` 处理不当(warning/错误两态)**:仅促销价有意义(=促销截止),常价商品缺失此字段属正常可忽略(Yoast 官方口径)——但促销过期未撤导致 `priceValidUntil` 已过=价格信号失效,GMC 同步报错;
- 补充两类隐性失败(不计入编号但常见):**图片不可抓**(schema `image` 指向 robots 屏蔽或带签名过期 URL 的 CDN);**Organization 上挂 AggregateRating**(见 L2,self-serving)。
- **排查入口**:GSC「商家信息」报告(错误按 SKU 列出)+ Rich Results Test(单 URL)+ GMC Diagnostics(feed 侧);三者交叉——**GSC 报 schema 侧、GMC 报 feed 侧,只看一边会漏**。

**最小可用 Product JSON-LD(L1 基线,零 warning 起步式)**:

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Example 3-Seat Sofa (Red Leather)",
  "image": ["https://cdn.example.com/img/sofa-red-main.webp",
            "https://cdn.example.com/img/sofa-red-side.webp"],
  "sku": "SOFA-RED-3S",
  "gtin13": "0123456789012",
  "brand": { "@type": "Brand", "name": "ExampleHome" },
  "aggregateRating": { "@type": "AggregateRating", "ratingValue": "4.6", "reviewCount": "812" },
  "offers": {
    "@type": "Offer",
    "url": "https://shop.example.com/p/sofa-red-3s",
    "priceCurrency": "USD",
    "price": "1299.99",
    "availability": "https://schema.org/InStock",
    "priceValidUntil": "2026-12-31"
  }
}
```

(price 纯数字/ISO 4217/availability 用完整 URL/reviewCount 与平台一致——四个高频错误一次规避。)
GMC 联动:free listings 默认覆盖 Shopping tab/Search/Images,**2025–26 正向 AIO 与 AI Mode 扩展**(query fan-out 取结构化 feed);已可不开 GMC 账户、仅凭页面结构化数据获 merchant listing 资格(官方)。

## 三、市场分叉表(主导方与官网策略)

| 市场 | marketplace 主导方 | 官网策略 |
|---|---|---|
| 美/英 | Amazon("best"查询部分被 Rufus 截流) | DTC 争品牌词/对比词/"best alternative to X";transactional 让 Amazon |
| 印度 | Amazon+Flipkart ~60–70% | 官网只做品牌词+内容;JustDial/IndiaMART 目录=GEO 引用源;AI 搜索已触及 ~22% 购买旅程 |
| 印尼 | Tokopedia(AIO 被引 #6)/Shopee/Lazada | AIO 直接引 marketplace 页→官网全力内容层+schema,做"被引第二通道" |
| 日本 | Amazon JP+楽天(双巨头 ~54% 价值份额) | 楽天店内 SEO≠Google SEO;海外品牌先进 marketplace 再建本地化官网 |
| 韩国 | Coupang(40%+)+Naver Shopping ~64% | 官网 Google 价值有限,重点在 Naver 生态(Smart Store/博客/카페) |
| 土耳其 | Trendyol(34–40%,月活 41.3M) | marketplace 页仅占 AIO 引用 2.5%→官网品牌词+内容层仍有空间 |
| 俄罗斯 | Ozon/Wildberries(WB ~52% 订单) | **低优先级**:2026 基础设施风险高(EU 制裁金融实体+仓库受损;Reuters/AP);Ozon AI 助手测试中 |

## 三点五、marketplace 站内 SEO 分叉(2026-10-09 深挖轮;各平台算法均为社区口径非官方)

| 平台(市场) | 站内排名清单(圈内版) |
|---|---|
| **Mercado Libre**(拉美) | 标题用满 60 字符(产品+品牌+型号+属性);ficha técnica 全字段喂过滤器;**问答响应速度/质量是排名因子**;转化率="女王指标";**投诉率<1% 保 Mercado Líder;Premium 曝光>Clássico**;工具 Nubimetrics(官方 partner) |
| **Trendyol**(土耳其) | 九信号:单量转化最强/评分与投诉时效/标题公式 Marka+Ürün+Model+Özellik/Hızlı Teslimat 徽章/**断货即时掉**/行为信号/新品窗口/广告间接/价格力;**content score 传 80-90+**(卖家口径);工具 pazarus.io+Trendyol Akademi |
| **Allegro**(波兰) | "Trafność"算法:标题匹配/**参数填满且逐月更新——常新增参数,过时即掉曝光**/缩略图+换算价/Allegro Analytics 迭代 |
| **bol.com**(荷兰) | 先做 zoekterm 研究再组标题(~100 字符);官方 Zoekalgoritme 页基准;zoektrends 数据库 |
| **Shopee**(越/泰/东南亚) | 关键词×**店铺指标**(回复率/粉丝/转化速度)+free ongkir;Lazada 给长描述更多内容分(分工) |
| **Tokopedia**(印尼) | 官方 Analisis Pencarian 工具;商品名+直播+短视频标题优先;TikTok Shop SEO 并入 University |
| **Salla/Zid**(沙特) | 平台级 SEO 偏弱需手动(sitemap/robots/抓取);App 生态 RankX;年费 SAR 990-2,990 |

### 三点六、两个市场分叉深挖:印度 Flipkart 与中东 Noon(2026-10)

**印度(Flipkart 主场确认+快商务变量)**:

- **份额口径分层(引用时注明)**:GMV 口径 Flipkart ~32% vs Amazon ~28%,Meesho 增长最快(~$6.2B GMV,Digital in Asia);MAU 口径 Flipkart+Myntra ~35%,Amazon 从 ~29% 跌至 ~18%(Goldman Sachs/Sensor Tower,CEO Review 转述);**Flipkart 自 2019 年起每年保持约 10pp GMV 领先**(Times of India)——印度是 Flipkart 主场,与美国镜像相反;
- **节庆脉冲**:Big Billion Days 期间 Flipkart 声称拿走全行业最高 ~70% 订单(峰值口径)——**印度电商预算要按节庆脉冲排班**(Q3/Q4),错峰=错季;
- **快商务(quick commerce)是 2026 真变量**:Flipkart 系日单 ~82 万 vs Amazon Now ~47 万(CNBC);快商务预计 2030 年占印度线上零售 ~40%(eMarketer)——**10 分钟达正在吃掉"次日达"的即时型购买**,对官网 DTC 的含义:印度市场的履约体验基线被快商务抬高,慢物流 DTC 在转化端先天劣势;
- **GEO 含义**:JustDial/IndiaMART 目录仍是 AI 引用源(见上表);Hinglish/地方语言内容是 Flipkart 生态外官网少数可竞争面(AI 搜索已触及 ~22% 购买旅程,套件已有数据)。

**中东(Noon+Amazon 分治,2026 新格局)**:

- **格局剧变:Amazon 入股 Noon**——沙特合并实体 ~31% 份额(Robusta Group 2026 报告);此前 Noon 完成新一轮 $500M 融资(LinkedIn/行业转述);**分治格局:Noon 主导沙特(其 52% 收入来自沙特,ECDB),Amazon 主导 UAE 尤其电子产品**——阿联酋与沙特要当两个市场做,不是一个"中东";
- **市场体量**:沙特电商 2026 达 **$20B**(提前两年达预测),2028 预计 $25–27B;UAE 2026 $12.30B、2031 预计 $21B(Cloud6/Market Data Forecast);
- **本地化要求(官网 DTC 进入门槛)**:阿拉伯语 RTL 站点(不是机翻)、COD(货到付款)与 Mada/Tabby(先买后付)支付、地址系统弱( landmarks 导向);`ar-SA` 内容+本地实体 schema;
- **建站生态**:Salla/Zid(沙特 SaaS 建站,见三点五)是本地 DTC 快速路径——但平台级 SEO 弱,**schema/sitemap/robots 需手动补**(与三点五行呼应);
- **GEO 含义**:中东 AI 引用生态尚浅(阿语语料质量参差)——**阿语内容层竞争低、先发优势大**;社交电商 $9.9B(2026,14.6% CAGR,Ken Research)与搜索并列入口。

## 四、AI 购物现状(2026-10 可证实口径)

- **Google**:AIO/AI Mode 集成 Merchant Center 与 Shopping Graph;AIO 内直接展示 free product listings 属测试中(官方确认路径,细节为行业观察)。
- **OpenAI**:ChatGPT Instant Checkout(2025-09 发布)**已于 2026-03 退役**——官方口径"迁移到 Apps,购买在商家自己网站完成";采用率低;底层 ACP 协议保留(媒体源,属实)。
- 格局共识:**"AI 管发现、商家管结算"**;ChatGPT 产品推荐日益依赖 merchant feed 而非开放网页。

### 四点五、AI 购物代理采用进度(2026-10 增量)

- **UCP 正式从 spec 走向产品化**:①**2026-03 大版本更新**(Semrush 口径)——agent 可浏览/比较/直接下单;②**Merchant Center「UCP Integration Hub」美国先上线**(SEL+Seroundtable;官方帮助页 support.google.com/merchants/answer/16837055)——GMC 内向导式连接 cart/checkout/identity,"Adopt UCP to enable agentic actions on AI Mode, Gemini and Search";③**Google I/O 2026 官宣 Universal Cart**(blog.google 一手,原"未证实"标记可升级):跨购物旅程的智能购物车,底层即 UCP 扩展;
- **采用现状的诚实口径**:Integration Hub 美国先行的"先行"= 其他市场商家当下无操作入口,只能预埋 `/.well-known/ucp`+补 schema(L1-L2 做扎实是 L5 的前置);**公开的商家采用率/转化数据仍缺失**(见未证实项)——对客户的表述应是"基建预备",不是"流量渠道";
- **ACP 侧**:Instant Checkout 退役后,ChatGPT 的商务路径=merchant feed(Apps/Directory 式);Stripe 同时支持 UCP/ACP 两协议是商家侧最稳的集成层;
- **判断框架**:AGI 购物代理的"发现→比价→下单"三段里,2026-10 只成熟了"发现"(AI 推荐),"下单"段在协议层就绪但消费者采用未验证——**把 L5 当期货,L1-L4 是现货**。

## 五、UCP 与 ACP(两大 agent 商务协议,2026-10)

| | UCP | ACP |
|---|---|---|
| 发起 | **Google 主导**,Shopify/Etsy/Wayfair/Target/Walmart 共同开发;~50 家背书(Amazon/Microsoft/Meta/Stripe/Visa/Mastercard/PayPal/Klarna/Flipkart/Shopee/Zalando) | OpenAI+Stripe 维护(GitHub 1,568★) |
| 机制 | `/.well-known/ucp` 声明 services/capabilities;transport=rest/mcp/a2a/embedded;覆盖 catalog→cart→checkout→identity→订单→支付;商家保持 Merchant of Record | ChatGPT 侧结算协议 |
| 状态 | spec 版本日期制,最新 2026-08-25;官方文档 developers.google.com/merchant/ucp;**GMC Integration Hub 美国上线(2026)**;垂直扩展 Lodging(草案)/Food(将上线) | Instant Checkout 退役但协议保留;Stripe 两者都支持 |
| 实操入口 | [ucp.dev](https://ucp.dev)、[Shopify/ucp-cli](https://github.com/Shopify/ucp-cli)(79★,L5 直接可用)、NVIDIA Retail-Agentic-Commerce 参考实现 | agentic-commerce-protocol spec |

**UCP 不影响 Google 排名(Google 未如此表述,勿写入客户材料)。**

## 六、未证实项

AIO 内 free listings 的触发条件与覆盖面(测试报告级);印尼 AIO 引用分布无独立研究;Ozon AI 助手效果;UCP→转化的案例数据;**GMC UCP Integration Hub 非美市场的开放时间表(官方未说)**;Amazon 入股 Noon 后 UAqar/UAE 合并实体的份额口径(Robusta 单源);Flipkart 70% 节庆订单份额为平台自述。

**已升级为证实(2026-10 深挖轮)**:原列 "Google I/O 2026 Universal Cart 细节(claude-seo 自标非一手)" ——现有一手来源 blog.google/products-and-platforms/products/shopping/google-shopping-cart,移出未证实;UCP Integration Hub 有 SEL+Seroundtable+官方帮助页三源。

### 来源增补(2026-10 深挖轮)

- 印度:Times of India(GMV 10pp 领先)/CNBC 2026-07(快商务日单)/eMarketer(2030 占比)/Digital in Asia(GMV 分层)/CEO Review(Goldman/Sensor Tower MAU 口径);
- 中东:Robusta Group(沙特 $20B/合并 31%)/ECDB(Noon 收入 52% 沙特)/Cloud6(UAE 体量)/Ken Research(社交电商)/Market Data Forecast;
- UCP/agent 商务:developers.google.com/merchant/ucp+support.google.com/merchants/answer/16837055(官方)/SEL+Seroundtable(Integration Hub)/Semrush(2026-03 更新)/blog.google(Universal Cart 一手)/Google Cloud(agentic commerce 叙事);
- schema 错误:Yoast(priceValidUntil 语义)/Rank Math(offers/review/aggregateRating 警告)/3wBiz(两个 missing field 修法)/CommerceGurus(星标缺失影响)/Google Webmasters 论坛真实工单。
