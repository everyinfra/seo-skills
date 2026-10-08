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

## 二、Product schema 实操清单(最常见错误即失败模式)

必填(merchant listing):`name`、`image`、`offers.price`、`offers.priceCurrency`;购物功能另需 `availability`。推荐:`gtin`/`sku`/`brand`/`mpn`、`Product.category`。
**七个高频错误**:①price 带货币符号/千分位(`$1,299.99` 非法→`1299.99`);②缺 priceCurrency;③缺 availability;④schema 与页面可见价/GMC feed 不一致(舍入差即报错);⑤缺 offers 节点;⑥单品误用 AggregateOffer;⑦主题/插件更新后 schema 过期。
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

## 四、AI 购物现状(2026-10 可证实口径)

- **Google**:AIO/AI Mode 集成 Merchant Center 与 Shopping Graph;AIO 内直接展示 free product listings 属测试中(官方确认路径,细节为行业观察)。
- **OpenAI**:ChatGPT Instant Checkout(2025-09 发布)**已于 2026-03 退役**——官方口径"迁移到 Apps,购买在商家自己网站完成";采用率低;底层 ACP 协议保留(媒体源,属实)。
- 格局共识:**"AI 管发现、商家管结算"**;ChatGPT 产品推荐日益依赖 merchant feed 而非开放网页。

## 五、UCP 与 ACP(两大 agent 商务协议,2026-10)

| | UCP | ACP |
|---|---|---|
| 发起 | **Google 主导**,Shopify/Etsy/Wayfair/Target/Walmart 共同开发;~50 家背书(Amazon/Microsoft/Meta/Stripe/Visa/Mastercard/PayPal/Klarna/Flipkart/Shopee/Zalando) | OpenAI+Stripe 维护(GitHub 1,568★) |
| 机制 | `/.well-known/ucp` 声明 services/capabilities;transport=rest/mcp/a2a/embedded;覆盖 catalog→cart→checkout→identity→订单→支付;商家保持 Merchant of Record | ChatGPT 侧结算协议 |
| 状态 | spec 版本日期制,最新 2026-08-25;Google 商家指南已有;waitlist 中;垂直扩展 Lodging(草案)/Food(将上线) | Instant Checkout 退役但协议保留;Stripe 两者都支持 |
| 实操入口 | [ucp.dev](https://ucp.dev)、[Shopify/ucp-cli](https://github.com/Shopify/ucp-cli)(79★,L5 直接可用)、NVIDIA Retail-Agentic-Commerce 参考实现 | agentic-commerce-protocol spec |

**UCP 不影响 Google 排名(Google 未如此表述,勿写入客户材料)。**

## 六、未证实项

AIO 内 free listings 的触发条件与覆盖面(测试报告级);"Google I/O 2026 Universal Cart"细节(claude-seo 自标非一手);印尼 AIO 引用分布无独立研究;Ozon AI 助手效果;UCP→转化的案例数据。
