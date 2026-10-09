# ตลาดไทย(泰语市场专项)

> **定位**:markets/th.md 是 th 市场的增量情报层。数值型规则(title/desc grapheme 阈值 60/155、句 10-25 词、ครับ/ค่ะ 尾词一致、佛历年、PDPA 医疗明示同意)在 `scripts/markets.json` 的 `markets.th`;总纲泰语区段见 [multilingual-workflow](../overview/multilingual-workflow.md),电商面见 [ecommerce-geo-ladder](../content/ecommerce-geo-ladder.md),链接市场见 [backlink-directory](../research/backlink-directory.md)。本文件只写三处不重叠的增量:**格局时间线(AI Mode 泰语化窗口)、渠道实战斗数(Pantip seeding 产业化/Shopee-Lazada-TikTok 份额再平衡)、红旗供应链**。断言半衰期 6-12 个月,引用前复查。

## 一、格局(ภาพรวม:一个 Google,三个站内搜索)

### 1.1 引擎

- **Google ~99.5%**(StatCounter 系,KB 既有口径),无本地通用搜索引擎;Bing/Yandex 不构成第二面——本市场竞争面全在**语言机制与渠道**,不在引擎分配。
- **AI Mode 已开放泰国**(官方名单,KB 既有)。增量:本地实测(2025-09 更新口径)AI Mode 在泰国**仅支持英文查询**,泰语查询当时未开;本地观察者普遍预期泰语支持"年内"落地。**泰语 AIO/AI Mode 全面化是 2026 泰国 SEO 最大变量——任何交付引用前必须当日实测当前泰语触发状态**。
- Google 官方已有泰语版 AI 功能文档(developers.google.com/search/docs/appearance/ai-features?hl=th)——文档本地化先行于功能本地化,勿把"有泰语文档"当"泰语已支持"。
- 移动为主;泰国社交App 使用时长全球前列,发现型查询大量发生在站内搜索而非 Google。

### 1.2 搜索行为迁移(TikTok 化,量级证据)

| 证据 | 读数 | 口径 |
|---|---|---|
| Google 内部研究(本地媒体转述) | **~40% 年轻人**找餐厅不用 Google Maps/Search,改用 TikTok/Instagram | techsauce 转引 Google 自研 |
| 泰国 TikTok 日均时长 | **68 分钟/日** | 本地流传口径,方向可信、精确值引用前复核 |
| 泰国人最喜爱 App | **TikTok 超过 Facebook 升至第 1** | Digital Thailand Report 2025 转述 |
| Gen Z 品牌发现渠道 | TikTok **超过** Google | marketeeronline 2026-09 |

- 战术含义:餐饮/美妆/生活方式的**发现型查询**主战场已偏移 TikTok 站内;Google 承担研究、比价、长尾信息意图——与印尼"先优化 Google 是错序"同构,但泰国 Google 份额本身不变,是**查询分流**而非**引擎更替**。

### 1.3 电商大盘(2026)

- 泰国电商盘子**~1 万亿泰铢级**;Shopee/Lazada/TikTok Shop 三平台卖家合计 **>300 万**(PriceZa 口径)。
- SEA 区域 GMV 2026:Shopee **~$83.2B(54%)**、TikTok Shop(含 Tokopedia)**~$45.6B(38%)**、Lazada **~$18.0B(7%)**——**Lazada 已是老三**,资源分配按此排。
- 泰国用户使用率(可并用,非零和):Shopee **~75%** / Lazada **~67%**(本地调研口径);ThaiPBS 2026-08:两大 App 合控网购 App 市场 **~78%**(8.8 千亿泰铢盘子)。
- 平台佣金带 **5-18%**(类目阶梯)。

## 二、渠道(ช่องทาง)

### 2.1 Pantip 双角色:排名占有者 + 声誉层

- KB 既有定论:รีวิว/ซื้อไหม(评测/值得买吗)类词常年霸榜——**排名占有者+声誉层双角色,不是外链来源**。
- **seeding 已产业化(2026 增量)**:
  - Fastwork 自由职业平台明码在架"Seeding&Review ลง Pantip",服务说明含配额机制(1 条真实评论折 3 条配额评论,2025 更新口径)——**按条计价、按配额交付的灰产供应链**;
  - seeding2u 类全案代理捆绑 Pantip/Facebook/Wongnai/TikTok,卖点明写"因为 Pantip SEO 排名高所以发 Pantip"——**平台的 SEO 优势正是灰产的卖点**;
  - gorillaideas 类代理公开售卖"ยึดคำค้นหา SEO/AEO + กำจัดข้อมูลเชิงลบ"(占据搜索词+清除负面信息)——ORM 灰产具名化。
- 帖子即页面:Pantip 帖题=title,首楼前 ~150 字符承担摘要;用户经 Google 进入落在具体楼层——**帖题写法按 title 公式对待**。
- 声誉层审计:品牌词 SERP 必查 Pantip 占位(`markets.json` serp_occupancy/complaint_lookalikes 已收);负面帖的对冲靠自然 UGC 与官方账号答疑,**买 seeding 压负是红旗**(见五)。
- 正常路线:Pantip 官方认证账号(ตรวจสอบแล้ว)答疑、真实体验活动+披露。

### 2.2 Lazada 内容分 vs Shopee 转化分

| 平台 | 权重倾向 | 实战要点 |
|---|---|---|
| Lazada | **内容分**:产品描述字段充实度、类目属性完整 | 长描述+属性全填;Lazada Sponsored Discovery 补量 |
| Shopee | **转化分**:销量速度、聊天响应、发货时效、退货率 | 上架初期用广告+促销拉转化数据喂算法;Shopee Ads 起量 |
| TikTok Shop | **分发分**:直播/短视频/达人内容挂车 | 佣金 5-18%;SEA 份额已 38%,泰国餐饮美妆尤甚 |

- 双/三平台并用是泰国卖家常态(75%/67% 使用率非零和);**官方学习渠道**:Shopee University TH / Lazada University 泰语版。
- **站内搜索联想词=天然泰语分词标注**:无空格文字在 Shopee/Lazada/TikTok 搜索框的联想词是平台分词器切好的词组——**关键词研究的免费分词语料**,比英文工具直接可靠。

### 2.3 TikTok:口播词被索引(量级补强)

- KB 既有:TikTok 口播词(spoken words)被 Google 索引。增量:68 分钟/日+Gen Z 发现第一(见 1.2)使该机制从"技巧"升为**主渠道**。
- 口播文案即关键词层:视频标题/首 3 秒口播/字幕文本进 Google 视频盒与 TikTok 站内搜索双索引——**同一段口播做两套关键词**。

### 2.4 LINE 与本地生活

- **LINE**:泰国用户 ~5,000 万+(仅次于日本的第二大市场,常用口径 ~54M,引用前复核)——OA(官方账号)+ VOOM + LINE TODAY 构成私域与内容分发层;SEO 之外的**默认分发基建**。
- **Wongnai**:餐饮/美容/SPA/酒店本地发现+评价目录(GEO 引用源,KB 既有)。增量:评价可信度**按账号历史分层**——老账号高权重,新注册账号自吹无效(Pantip 用户实证讨论);Wongnai for Business+POS(FoodStory)生态绑定商家运营。

## 三、语言机制(กลไกภาษา)

### 3.1 分词定论(无空格文字的第一问题)

- **`Intl.Segmenter("th")` 是唯一可信分词路径**——主流 SEO 工具栏在泰文站全错(KB 既有定论)。任何密度、精确匹配、关键词计数先过它再谈。
- 实操:
  - JS 一行:`[...new Intl.Segmenter('th',{granularity:'word'}).segment(s)]`;
  - 关键词研究双源对勘:平台站内联想词(切好的词组)+ GSC 实查询(用户真实切分习惯);
  - 泰文连写导致英文式头部词查询量被系统性低估——long-tail 以完整短语(自然语句)记。
- 泰调可读性公式:**句 ≤25 词 / 词均 ≤5 字符**(markets.json sentence_ideal 10-25 词);一句一信息。

### 3.2 grapheme 字素计数

- title 60 / desc 155 按 **grapheme**(字素)计:组合元音/声调符号不计独立字符——Python `len()` 码点计数会**高估 30-50%**,审计工具必须用 Intl.Segmenter granularity='grapheme' 或等价库。
- **meta 词中截断逐页检查**:泰文无空格,Google 截断可能落在词中间(乱码观感),关键信息前置。

### 3.3 书写、格式与查询习惯

- **ครับ(男)/ค่ะ(女)礼貌尾词全站一致**(markets.json 已收);语域:电商平台可เป็นกันเอง(亲近),金融/B2B 用正式敬语。
- **佛历年(พ.ศ.)**:2026 CE = 2569 BE,格式 `9 ตุลาคม 2569`;法律/政府场景双历并记;**勿在商业页漏标 BE**——西历在泰国非默认。
- **泰文 slug 陷阱**:泰文 URL 被 encode 成 `%E0%B8…` 完全不可读——用音译或英文 slug(本地实战共识);文件名/图片 alt 同理。
- **查询即口语**:泰国用户用自然语句+外来语(ทับศัพท์)混写搜索("วิธีทำ SEO ให้ติดหน้าแรก"/"รีวิว…ซื้อไหม")——**问答式 H2 与口语化标题**比关键词堆砌标题有效;รีวิว/วิธี/ซื้อไหม/ราคาเท่าไหร่ 是四大查询前缀。
- Keyword Planner 支持泰语但精度逊于英文(本地代理共识口径)——量级决策用 GSC 实数据校准。
- 泰文字体子集化省 **60-80%** 带宽(KB 既有;泰文字形大,LCP 前置优化项)。

## 四、AI-GEO(泰语 AIO 窗口期)

- **窗口期判断**:AI Mode 已开泰国但 2025-09 实测仅英文查询;泰语支持落地前后是**建基线的最后窗口**——泰语 AIO 引用源格局尚未被行业系统性研究,先建者得基线。
- 官方泰语文档已在(developers.google.com ai-features?hl=th);AIO 引用机制(段落级截取、nosnippet 退出、structured data 喂给)与全球一致——**通用 GEO 打法直接迁移**,不确定的只是泰语触发覆盖率。
- **泰国代理已开卖"AIO"服务**(ThaiSEOBoard 交易区在架)——市场教育先行于泰语 AIO 全面铺开;交付时区分"英文查询 AIO 占位"与"泰语查询 AIO 占位"两个产品。
- AIO CTR 冲击本地流传口径 **-47%**(泰语代理转引研究,作区间参考勿当泰国实测)。
- 预置占位审计清单(泰语 AIO 落地时首批被引候选):Pantip(UGC 评测)、Wongnai(本地目录)、Thairath/Khaosod/MgrOnline(新闻)、chula/mahidol 系(医疗学术)、wikipedia(th)。
- 段落级可引性四要素(主体+数字+as-of 日期+方法学)在泰语同样适用;**数字+佛历年双标**可同时服务人类信任与 AI 抽取。

## 五、红旗(ความเสี่ยง:灰产供应链成熟市场)

### 5.1 หลังบ้าน 灰链网

- KB 既有定论:**หลังบ้าน("后门")=灰黑帽链网**,赌博站 hack 排名手法,**被罚后恢复以年计**——低价外包安全是幻觉。
- 增量:**ThaiSEOBoard 交易区(board 60"ค้าๆขายๆ")公开在架**:ทำ SEO、**AIO**、ขายโดเมน、ขายเพจ、ขาย Backlink;服务自述"รับทั้งสายขาวและสายเทา"(白灰通吃)——**灰产已商品化到按 SKU 售卖**。
- 2026 泰语警示内容显著增多(代理案例文+个人踩坑贴)——本地受害者叙事成熟,客户教育成本低。
- 审计口径:被动被赌场链射击**不自动中毒**(disavow 台账化处理);**主动购链=Google 链接垃圾政策范围**,无论本地话术如何包装"คุณภาพสูง"(高质量)。

### 5.2 Seeding 产业化(本市场特有浓度)

- Fastwork 按条计价/seeding2u 捆绑包/gorillaideas"删负信息"具名服务(见 2.1)——供应链越成熟,**品牌方越容易无意识踩线**。
- 法律面:**โฆษณาแฝง(隐性广告)**违反泰国消费者保护委员会口径(未披露的商业推广);医疗类叠加 PDPA 明示同意。
- Google 面:批量假人评论/提及=inauthentic mentions 风险;Pantip seeding 翻车 drama 有多年历史(社区对 หน้าม้า/水军高度敏感)。
- 正面路线:真实体验+披露标注(สนับสนุนโดย/ร่วมรายการโดย)。

### 5.3 三级红线速查

| ระดับ | 项 | 处理 |
|---|---|---|
| ห้ามเด็ดขาด | 购买 หลังบ้าน 链网/赌博站挂链/假账号评论配额包 | 即拒(恢复以年计) |
| สีเทา(条件) | 体验型 seeding+完整披露/达人合作标注 | 合同披露条款+平台规则双检 |
| อนุญาต | 认证账号答疑/自然 UGC/真实评价邀请(无报酬条件) | 鼓励 |

## 六、เครื่องมือ(工具,免费优先)

| เครื่องมือ | 用途 | 备注 |
|---|---|---|
| Google Keyword Planner | 泰语月检索量 | 支持泰语但精度逊英文——GSC 校准 |
| Google Trends(Geo=TH) | 泰语词趋势/季节 | พ.ศ. 时区心态下旺季核对 |
| GSC | 泰语实查询+表现 | 导出后过 Intl.Segmenter 再统计 |
| Shopee/Lazada/TikTok 站内联想词 | **天然泰语分词语料**+品类词 | 免费关键词主源 |
| Pantip 站内搜索+热榜 | 评测词/舆情/声誉层监控 | 品牌词审计必查 |
| Wongnai(商家后台) | 本地生活评价+目录占位 | GEO 引用源预置 |
| ThaiSEOBoard | **情报与风险监控** | 只读情报,不作采购渠道 |
| Fastwork | 外包供应链审计对象 | 灰产浓度高,尽调必做 |
| LINE OA 后台 | 私域分发效果 | 泰国默认分发基建 |
| Ahrefs/Semrush | 外链与竞品(泰语分词谨慎) | 密度类功能在泰文站不可信 |

> **检索口径**:本文件 2026-10-09 以泰语 web 检索(ทำ SEO 2026 / Shopee Lazada อันดับ / Pantip SEO / AI Mode ไทย / ส่วนแบ่งตลาดอีคอมเมิร์ซ / จ้างโพสต์ seeding)。原文:contentshifu、impel-marketing、techsauce、marketeeronline、ThaiPBS Policy Watch、PriceZa/anchanto 电商报告、ThaiSEOBoard、Fastwork/seeding2u 服务页、Google 泰语官方文档。量级类数字(68 分钟/75%/67%/54M)为本地转述口径,引用前复核。
