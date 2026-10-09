# Thị Trường Việt Nam(越南语市场专项)

> **定位**:markets/vi.md 是 vi 市场的增量情报层。数值型规则(title 45-65 字符、desc 155、词进前 30 字符、密度上限 1/150、hreflang vi/vi-VN 等)在 `scripts/markets.json` 的 `markets.vi`;跨市场流程与越南行见 [overview/multilingual-workflow](../overview/multilingual-workflow.md) 越南行;内容模式总纲见 [content/content-patterns](../content/content-patterns.md)。本文件只写增量:**Cốc Cốc 的 A/B 双口径、Shopee 店内指标实战斗数、backlink báo 产业价格锚、AI 信任/使用剪刀差**。断言半衰期 6-12 个月,引用前复查。

## 一、格局:Google ~93% 独大,Cốc Cốc 的 A/B 面

### 1.1 双口径份额表

| 口径 | 最新读数 | 含义 |
|---|---|---|
| 搜索份额(StatCounter,2025-08~2026-09 窗口) | **Google 92.94% / Cốc Cốc 5.96% / Bing 0.65%**;按 host:google.com 90.66% vs coccoc.com 4.47% | 搜索行为面 Cốc Cốc 只有个位数——预算分配以 Google 为绝对主战场 |
| 浏览器装机/用户面 | **VWAS 2024:移动端 Cốc Cốc 浏览器使用率 ~21%**(与 Chrome 75%、Safari 30% 并存,合计>100% = 多浏览器并存口径);官方口径 **25+ triệu người dùng**(press.coccoc.com);桌面端稳居第 2(超 Edge/Safari/Firefox);移动端 **NPS 66 全场最高**(CafeF 引 VWAS) | "装机多、搜得少"——浏览器是壳,默认搜索仍被 Google 占据 |
| StatCounter 浏览器份额 | ~4.22%(2026 窗口;2023 快照曾 ~12%) | 与 VWAS 口径差异大,**并报双口径勿混用**:StatCounter 按页面浏览加权,VWAS 按用户使用率 |

### 1.2 A/B 面的操作结论

- **Cốc Cốc 的价值不在流量(6%),在数据面**:每年 12 月发布《Báo cáo xu hướng tìm kiếm và lướt web》(2025 版 2025-12-17 发布,Tuổi Trẻ/VietnamPlus 全量转引),另有季度趋势报告(qc.coccoc.com;Q1/2026 版口径"thứ hạng tìm kiếm ổn định so với cuối 2025")。年度报告是**越南唯一本地自有搜索面板**——做消费选题、品牌词热度、年度回顾内容时的独家源。
- 2025 年热搜词高度娱乐化(Ngân 98 / Shark Bình / Malisa 一类名人 scandal 词)——印证其面板代表的是**大众/娱乐流量层**,B2B 选题勿以此定调。
- CEO 曾设 2025 年 50 triệu 用户目标(CafeF 2022)——官方用户口径一贯偏宣传,引用时标注来源。
- **设备偏斜**:Cốc Cốc 流量集中在 **PC 端**(移动端 Google+google.com.vn 合计 ~97%);目标用户全移动时 Cốc Cốc 优化回报更低;PC 用户占比高的品类(工具站/下载站)才值得做位次跟踪。
- **收录通道**:独立爬虫 UA `coccocbot` / `coccocbot-web`,有自家 Search Console(URL 提交+sitemap 指引);官方偏好**越南语内容与 .vn 域**(单独提交收录,勿假设 Google 收录自动带入);爬虫 IP 真伪可经其 bot API 验证,禁按 IP 段封禁(与 Naver Yeti 同律——robots/UA 层控制才合规)。
- **优先级定位**(multilingual-workflow 口径):Cốc Cốc 是"低成本必做项"(提交+语言达标即止),优先级**低于 Facebook 群/Zalo**——越南社交封闭生态分流大量产品发现型查询,社媒侧投入先于第二搜索引擎。
- **产品发现链路是三段式**:Zalo/FB 群(熟人种草)→ Shopee 站内搜索(比价成交)→ Google(研究/长尾信息)——客户问"为什么 Google 流量涨但单不涨"时,先查前两段是否掉量。

## 二、渠道:Shopee 店内指标 × backlink báo × t0mmy 99 条

### 2.1 Shopee 店内 SEO(排名 = 店内运营指标,不是站外 SEO)

Shopee 是越南电商第一入口,产品发现型查询先在站内搜索发生——"SEO Shopee"是独立学科,指标全部在 Kênh Người Bán(卖家中心)→ Dữ liệu 看板内闭环。**平台份额锚(2026-10-09 复核)**:Momentum Works《Ecommerce in Southeast Asia 2026》越南 2025 GMV ฿0,66T(+~50% 档),平台列 **Shopee 58% / TikTok Shop 39% / Lazada 3%**——TikTok Shop 在越南的电商份额与印尼并列 SEA 最高档(高于泰国 32%),做店内 SEO 时把 TikTok Shop 当第二站而非可选项:

| 指标(chỉ số gian hàng) | 作用 | 实操口径 |
|---|---|---|
| Điểm sao(店铺评分) | 算法权重 + 转化双入口 | 4.5+ 为健康线;差评 24h 内响应(Shopee 评分不可编辑,只能靠增量稀释) |
| Tốc độ phản hồi chat | 店铺健康分 | 挂 Shopee App 常开;回复率是少数"可 24/7 达标"的硬指标,失分最冤 |
| Tỷ lệ hủy/trễ đơn(取消/延迟率) | 负向扣分 | 缺货即下架,勿硬接单 |
| Lượt mua thành công(成功购买次数) | 热度信号 | **近期销量加权**——吃老本无效(与 Naver 스마트스토어"최근 판매량"同构) |
| Vi phạm(违规记录) | 一票否决 | 假评/刷单属不可逆处罚区 |

- **产品名公式**(Salework 口径):`Loại sản phẩm + Thương hiệu + Model + Thông số kỹ thuật + Kích thước/Dung lượng`——主词前置,堆修饰词降权;禁用"rẻ nhất/100%"类绝对化词。
- **描述层**:hashtag 辅助站内抓取;信任短语 "cam kết chính hãng / bảo hành / đổi trả"(Shopee 官方博客口径)既是转化文案也是站内信任信号。
- **关键词研究**:站内搜索栏 suggest 下拉(免费、最贴近真实购买词,逐字母前缀试探)+ 第三方工具(Shopee Analytics 类按 Search Volume×竞争度筛);**站内词与 Google 词表不通用**——购买意图在站内更短、更口语、方言更多。
- **Shopee Ads 与 SEO 并行**:Ads 期间销售增量喂养热度指标,停投后自然位承接——"以投养排"是标准冷启动路径(选词集中 1-2 个主词,勿撒网)。
- **双层词表纪律**:Google 词表(信息/研究意图,长尾带疑问词)与 Shopee 词表(购买意图,短词+属性词)分开建、分开考核——同一品类两表的 top 词重合度通常很低,混表会导致 Google 页面优化去买词、Shopee 品名去堆研究词的双向错配。

**Quy trình hằng tuần(周节奏)**:站内 suggest 双轨采词(有调/无调)→ 对表类目 top 10 的产品名结构/评价数/得分 → 改品名+描述 hashtag → 追踪 7 日自然位变化 → 未动则检查店铺健康分(回 chat/取消率)再动内容。**先修指标再修词**——Shopee 排名天花板由店铺健康分决定。

### 2.2 backlink báo(新闻站外链产业)——价格锚与定性

越南特有规模化产业:省级/国家级新闻站(báo điện tử)出售 sidebar 全站链接与 PR 文章位,中间商公开挂单。2026-10 实测价锚:

| 套餐类型 | 价格区间 | 性质 |
|---|---|---|
| Sidebar 批量包(PRBaoChi 1K/3K Pro 类) | 1,000 条 ~2,6 triệu VND(~2.600đ/条);3,000 条 ~7,5 triệu(~2.500đ/条) | **规模化购买链接,Google 链接垃圾政策明文范围** |
| Textlink báo 时段包(Hapo Digital 类) | 3 个月 3.490.000đ / 6 个月 5.200.000đ | 同上,租期制,到期即失 |
| Bài PR(新闻稿式文章) | 按报按位;行业主流"白帽话术"包装 | 灰区:真实编辑位+付费披露可类比数字 PR;纯锚文本位不做 |
| "Entity" 包(SEOVIP 200-300 social/blog) | 3,6-4,9 triệu VND | 廉价社会书签/博客群发,基本无 SEO 价值 |
| "高 DA"噱头(Dichvubacklink 类 KENTOM/PA DA>90) | 低价 | PA/DA 是 Moz 第三方指标,与 Google 排名无因果——话术红旗 |

- 域名层级公开流通:**省级报**(baolaocai.vn / baoangiang.com.vn / baocantho.com.vn 等 22-30 个,Fame Media 类中间商挂单)< **国家级/头部电讯报**;层级决定单价,但 sidebar 位不论层级都是 sitewide 链接。
- **定性**:向客户报价"backlink báo = white hat"是市场默认话术,但 sidebar 千条包在 Google 政策下即 link spam;正确处置见"红旗"。
- Tinh tế(tinhte.vn)等大站社区有真实讨论位(含"mua backlink báo ở đâu"主题帖本身)——社区自然提及与付费板块勿混淆,前者是可争取的编辑链接。

### 2.3 t0mmy 99 条(内容产线规则,业内规则集非官方算法)

markets.json 已收 4 条硬参数;增量维度:

- **提问式 H2 ≥50%**:越南语疑问词体系天然适配——`... là gì? / ... như thế nào? / Có nên...? / ... bao nhiêu? / ... ở đâu?` 五型覆盖信息/决策/价格/本地四类意图,与 Google People-Also-Ask 及 AI 引用双双对齐;产线模板按"每两个陈述 H2 配一个疑问 H2"起步。
- **密度只设上限 1/150 且仅计正文**(thân bài):导航/侧栏/FAQ 折叠不计;超限即 lint 拦截,**不设下限**(防凑词——越南语音节复写词多,凑密度极易堆出机器味)。
- **nonce 双层质量门**:validator 达标 ∧ 独立评分 ≥85 才发布 + 状态目录只读——防 agent 产线自评篡改;这是越南区贡献给全区 agent 流水线的通用安全层(multilingual-workflow 第 21 条)。
- **句长方差检测**(mona-seo-check-vi 口径):反 AI 文风——越南语 AI 生成文常见"句句等长"病理,方差过低即回炉;vi 句长理想 15-20 词,但**方差比均值重要**。

## 三、语言机制:有调/无调双轨 + slug 无调

- **có dấu / không dấu(有调/无调)是两个查询世界**:移动端用户常不切 Telex/VNI 输入法直接打无调(`không`→`khong`,`điện thoại`→`dien thoai`)——**意图相近但 SERP 不同**;关键词研究时归组(合并估量),排名跟踪时当独立词各建一行(移动端特查无调形)。
- Google 对双轨做部分归一化但**不完全**——位次报告两形并列是 vi 区默认交付格式;品牌词含调字符(ơ/ư/đ)时,无调形 SERP 常被竞品/聚合页占据,品牌 ORM 必查。
- **đ 是独立字母**(不是 d 的变体)——排序/索引里 đ 与 d 分位;归一化脚本把 đ→d 会制造假词(如 "đến"→"den" 是另一个真词"颜色/到"歧义)。
- **slug 一律无调**:小写+连字符(`tin-tuc-cong-nghe`),去特殊字符;改 slug 必 301;带调 URL 被 percent-encode 成 `%E1%BA..` 串,可读性/分享/CTR 三输(全行业共识,slug 生成器基建成熟:WordPress 原生+本地工具)。
- **代词语域分层**:bạn/tôi 常规、anh/chị 服务敬称、quý khách B2B/金融——同站统一,混用即 lint 红旗(markets.json formality 口径);关键词层无名调动词("giá/báo giá/mua ở đâu"),正文层用语域——标题词表与正文语域分离是 vi 内容默认架构(与 ko 同构)。
- **分词机制**:越南语以空格分节、每音节即 token——15-20 词的理想句在 vi 实际承载信息量低于英语同词数;**超长复合名词组**(保险/金融词)优先拆破折或 bullet,否则 AI 摘要引用率下降。
- 字符预算先于词预算触顶:title 65 字符在 vi 约等于 10-12 个音节词——超限是 vi 站最高频 lint 违规,产线模板按字符截断。
- **疑问词五型与意图映射**(t0mmy H2 规则的落地词表):

| 疑问型 | 意图 | H2 模板示例 |
|---|---|---|
| `... là gì?` | 定义/科普(AIO 高触发) | Dịch vụ SEO là gì? |
| `... như thế nào? / ra sao?` | 过程/评价 | Chi phí SEO như thế nào? |
| `Có nên ...?` | 决策/比较 | Có nên mua backlink báo? |
| `... bao nhiêu?` | 价格/数量 | SEO website giá bao nhiêu? |
| `... ở đâu?` | 本地/渠道 | Đăng ký doanh nghiệp ở đâu? |

- 南北用词差异存在但比传闻小;全国型站点以标准书面语为准,本地服务页(địa điểm 类)可带地方口语变体做长尾。

## 四、AI-GEO:信任第 3 × 使用第 38 的剪刀差

### 4.1 数据面

| 指标 | 读数 | 来源口径 |
|---|---|---|
| AI 使用率 | **23.5%**(2025 下半年自 21.2% 升),**全球第 38 位**;全球均值 16.3% | VnEconomy 引全球指数 |
| AI 信任度 | **全球第 3(65,6 điểm)**;接受度第 5(71,6);综合 6/40 | World AI Index 2025(WIN),Bộ KH&CN 转发 |
| 互联网用户 AI 接触 | **78-80% 近 3 个月用过至少一个 AI 平台**;1/3 每日使用 | Decision Lab 2025-07 面板(n=600) |
| 平台格局 | **ChatGPT 81% / Gemini 51% / Meta AI 36%**;本土 AI(AI Hay 等)2 个进 top 10 | Decision Lab / VnExpress |
| 平台格局(2026-03 更新) | **ChatGPT 66% / Gemini 50% / Meta AI 24%**;Kiki Info 进 top 10 | VnExpress 2026-03-09 引 2026 版面板(vietnam.vn 转引一致)——ChatGPT 份额下移但 Gemini 持平,引用时两版并注年份 |

### 4.2 操作结论

- **剪刀差含义**:信任全球前 3、习惯性使用第 38 位、但 78-80% 已有接触——用户"信但不常查",GEO 内容量产窗口在早期;先占引用源的边际回报高于成熟市场,AIO/GEO 预算的辩护词就用这组数。
- **AI Overviews 已落地越南语**:2024-10 末随 100+ 国上线(tiếng Việt 支持,VTV/Lao Động 报道),**AI Mode 亦在越可用**——引用优化是现役战场非预备项。
- 本地媒体已报道 AIO 幻觉引用社媒源的翻车案例(Tuổi Trẻ/Saigon Times 口径)——**引用源权威性(E-E-A-T)是差异化机会**:产线给答案段落配官方/机构引文,比社媒源竞品更易被采信。
- **提问式内容双受益**(见 2.3):vi 疑问词体系与 AIO 触发查询高度重合,t0mmy H2 规则同时服务 SERP 与 AI 引用。
- 本土 AI(AI Hay 类)进 top 10 是信号:GEO 监测不只测 ChatGPT/Gemini——**越南语答案产品的引用面单列一行**跟踪。

**GEO 产出清单(vi 页面级,发布前过一遍)**:

1. 每页至少 1 个可直接摘录的"定义段"(30-50 词,含主词原样措辞);
2. 疑问 H2 覆盖率 ≥50%(疑问词五型对表);
3. 数据/结论段配**机构源引文**(官方/协会/权威媒体,优于社媒源);
4. 有调/无调双轨词在正文各自然出现(无调形只入正文不入标题,防品牌观感劣化);
5. 句长方差达标(句长方差检测过门)。

**Nhịp đo lường(测量节奏)**:

| Chu kỳ | Hành động | Sản phẩm |
|---|---|---|
| Tuần(周) | 有调/无调双轨位次 + AIO 出现率抽样(20 词面板) | rank tracker 双行制 |
| Tháng(月) | 品牌词无调形 SERP 占位审计(竞品/山寨) | ORM 台账 |
| Quý(季) | ChatGPT/Gemini/AI Hay 三面引用测试(同 10 问) | 引用面 diff |
| Năm(年) | Cốc Cốc 年度报告+Decision Lab 面板更新剪刀差数 | 客户汇报页 |

## 五、红旗(合规与封禁区)

| Cấp độ | Hạng mục | Xử lý |
|---|---|---|
| Cấm tuyệt đối | sidebar 千条包/租期 textlink báo(规模化购链)/ 廉价 Entity 群发包 | 即拒——Google 链接垃圾政策范围;客户坚持则**书面披露风险+降责条款** |
| Vùng xám | bài PR 新闻稿(真实编辑位+付费披露)/ 体验式评测 | 有编辑价值+披露可做;纯锚文本 sidebar 位不做 |
| Được phép | 原创数据研究引子(数字 PR)、行业协会/官方引用、IDVS 等社区自然提及、记者关系 | Chủ động khuyến nghị |

- **"mua backlink báo = white hat"是越南市场默认认知**——接越南客户第一课:把披露义务与替代方案(数字 PR、可引用数据研究)写进提案,勿顺着话术接单;话术红旗词:"PA DA >90 保证上排名"、"1,000 link 包月"。
- Shopee 刷单/假评(vi phạm)一票否决且不可逆;评论激励属站内违规——与 Google 侧评论伦理同罚,双平台客户一并写进合规章。
- AI 量产无质量门内容:靠 nonce 双层门+句长方差检测拦截(2.3),勿裸跑生成;越南语 AI 生成文的"等长句病理"在母语读者处极显眼,信任成本高于英语市场。

## 六、Công cụ(IDVS 论坛与工具面)

| Công cụ | Mục đích | Ghi chú |
|---|---|---|
| **IDVS**(forum.idichvuseo.com) | 越南 SEO/Digital Marketing 论坛 | **全国首个且唯一持 Bộ TT&TT(B信息传媒部)社交网络牌照的 SEO 论坛**;讨论质量高于规模;行情价/算法变动一手帖;另有招聘/接单板块可探人力行情 |
| Brands Vietnam / SEOMXH | 行业社区与行情 | IDVS 之外两个行情源;Brands Vietnam 偏品牌/研究向 |
| Cốc Cốc Search Console | coccocbot 收录/提交 | 越南语+.vn 偏好;与 GSC 分开核对 |
| StatCounter(gs.statcounter.com)/ VWAS | 双口径份额 | 引用时标注口径与时间窗(见 1.1) |
| Cốc Cốc 年度/季度趋势报告 | 本地搜索行为面板 | 12 月年度版+季度版(qc.coccoc.com);选题级数据 |
| Decision Lab 报告 | AI 使用/平台份额面板 | 年度追踪剪刀差(四) |
| Google Trends(geo=VN, hl=vi) | 免费趋势 | 有调/无调各建一条对比 |
| Shopee 站内 suggest + Kênh Người Bán → Dữ liệu | 站内词表+店内指标 | 2.1 全部指标官方入口 |
| GSC + Ahrefs/Semrush | Google 侧标准面 | 无调形关键词**手工补录**——工具自动归一化会吞掉双轨 |

## 七、Zalo 生态(2026-10-09 增量:越南第二战场)

> vi 市场此前缺的私域/发现层深潜。数据锚点:2026-10-09 复核(母语检索)。

### 7.1 盘子与变现(VNG 财报口径,两源一致)

- **Zalo ~78,3 triệu MAU**(VNG 披露,Zalo 官方账号口径;Nhân Dân 引 VNG Q3/2024 财报 77,6 triệu,趋势一致)——越南第一大通讯/社交平台,人口覆盖 ~76%;通讯类份额 "chiếm gần 70%"(Nhân Dân 口径)。
- **VNG 2026-04 首次拆分 Zalo 收入:2025 年 1.718 tỉ đồng,占 VNG 总营收 ~16%**(CafeF)——变现加深意味着 OA/广告位价格与竞价密度只会上升,早进场成本低。
- **Zalo OA 2026-06-01 起启用 4 档新服务包**(GaPiT 转官方公告)——套餐层重新定价,引用报价前查官方现行页。

### 7.2 Zalo 在发现链路里的真实位置(承接 1.2 三段式)

- 三段式 `Zalo/FB 群种草 → Shopee 比价成交 → Google 研究` 中,Zalo 承担的是**熟人信任层**:群聊转发是越南口碑传播的主通道,OA 是"品牌在 Zalo 里的官方门面"——种草后的第一步验证(这是不是正品/有没有官方)发生在 **Zalo 站内搜索**。
- **Zalo 站内搜索占位 = 越南版的品牌 SERP 审计**:用户搜品牌名,若 OA 认证号缺席而山寨号/仿号在场,转化在进入 Google 之前就漏掉了——ORM 台账在 vi 市场要加"Zalo 品牌词占位"一行(与 Google 品牌词 SERP、无调形 SERP 并列三查)。
- **OA 的私域广播 ≠ 社媒发帖**:消息触达(类 LINE OA Broadcast)是通知型渠道,打开率逻辑接近邮件营销——内容节奏按"服务通知 > 节日问候 > 促销"排,促销频率过高直接掉粉。
- **Zalo OA Ads(Official Account Ads)**:以涨粉(followers)为结算导向的付费位(CNV 2026-01 口径)——冷启动买粉再靠广播承接,是"以投养私域"的标准路径;与 Google Ads 词表完全不通用。
- Mini App(Zalo 小程序)承载轻交易/表单,跳过独立站开发——中小客户预算有限时,vi 市场的 MVP 顺序常是 **Zalo OA + Mini App 先于独立站 SEO**;SEO 从业者的定位是接住"研究段"的长尾,而非全链路。

### 7.3 操作清单(品牌进 vi 市场的 Zalo 三步)

1. 认证 OA + 品牌词占位审计(站内搜品牌名,查山寨仿号);
2. 客服话术接 OA(自动应答+人工兜底),响应速度是私域评分核心;
3. 广播内容日历与 Zalo Ads 涨粉计划分开考核(粉数/留存 vs 触达/转化)。

## 十、本地实测(2026-10-09)

**实测站**:vnexpress.net(头部新闻门户)、tinhte.vn(最大科技社区,markets.json entity_source 之一)。工具:`site_audit.py --market vi` / `llmstxt.py check` / `head_check.py`。

| 站 | site_audit 触发项 | head_check 汇总 | llms.txt |
|---|---|---|---|
| vnexpress.net | WARN:desc 192 超限 / 跳级 h2→h4 / 153 链接>100;无 CRITICAL | 9 ERROR(x-ua-compatible、fb:app_id、apple-mobile-web-app-capable、twitter:*×6)/2 WARN/geo 四件套齐,exit 1 | 无(/llms.txt 等 4 路径全 404) |
| tinhte.vn | **CRITICAL:无 H1**;WARN:desc 162 超限 / 183 链接>100 | 6 ERROR(twitter:*×4、fb:app_id、**charset 位于第 34763 字节**——前置 34KB 内联样式);文档 1.44MB,exit 1 | 无 |

**工具盲区(如实记录)**:

1. **title 解析泄漏(工具 bug,vi 两站全触发)**:`site_audit.py` 的 HTMLParser 把 `<head>` 内 title 之后出现的 JSON-LD/JS 全部并入 title 长度——vnexpress 报 "title 180485 字符"、tinhte 报 104794,均为假告警;真实 title 长度正常(head_check 读到的 50-55 字符)。vi 市场门户普遍把 JSON-LD 放 head,此 bug 在本市场高频命中,title 长度结论以 head_check 为准。
2. **`--market vi` 未接线**:market 参数只有 `ja` 有差异化阈值,markets.json 里 vi 的 65 字符 title 上限未生效(按 60 通用值判)——阈值偏差小,但属声明与实现不一致。
3. **词数统计对越南语失真**:`wc()` 的 Latin 正则 `[A-Za-z0-9']+` 把含变音符的越南语词按 ASCII 边界切碎("przegląd"式问题在 vi 同样存在),词数虚高;内容词数结论需 `text_metrics.py` 交叉。
4. **head_check 的微信/QQ itemprop 检查对 vi 无意义**:该检查是中文分享场景专用,在越南站上报 WARN 属误报,忽略即可。
5. 无站点提供 llms.txt——vi 头部站对 AI 爬虫协议层动作迟于 nl(见 nl.md 实测),GEO 引用面竞争仍靠内容质量。

> **检索口径**:本文件 2026-10-09 以越南语 web 检索执行(查询组:SEO website 2026 / Shopee SEO từ khóa / Cốc Cốc tìm kiếm + 追加)。原文:StatCounter Global Stats/Tuổi Trẻ/VietnamPlus/VietnamNet/VnExpress/VnEconomy/Báo Đầu Tư/CafeF/Bộ KH&CN(mst.gov.vn)/Cốc Cốc press & qc.coccoc.com/Decision Lab(经 Brands Vietnam 转发)/Shopee 官方博客/Mona Media/Salework/Nhanh.vn/Admatrix/SEOVIP/Hapo Digital/PRBaoChi/Fame Media/BacklinkAll/爬虫侧 Dark Visitors(coccocbot UA)。t0mmy 99 条为业内规则集(非官方算法披露);价格锚来自服务商 2026 公开报价页,引用前复核在营状态。
> **2026-10-09 复核增补**:StatCounter 92,94/5,96/0,65 两源一致(gs.statcounter 直读 + TopOnSeek/TapChiCongThuong 转引);AI 使用 23,5%/第 38 位与信任第 3(65,6)/接受第 5(71,6)/综合 6/40(59,2)多源一致(VnEconomy/Nhân Dân/baomoi 等);平台格局补 2026-03 版(66/50/24,VnExpress+vietnam.vn 两源);VWAS 移动浏览器 ~21% 仍(单源);Cốc Cốc 年度趋势报告 2025 版 2025-12-17 发布(VietnamPlus 确认);Zalo 78,3 triệu MAU(Zalo 官方 + Nhân Dân 引 VNG 财报,两源)。

## 维护

- **复核周期**:90 天;**下次复核 2027-01-09**。
- **信号源**:StatCounter 越南国家页(gs.statcounter.com/search-engine-market-share/all/viet-nam)、Cốc Cốc 官方报告(qc.coccoc.com 季度版 + 12 月年度版)、Decision Lab《The State of Consumer AI in Vietnam》(年度)、VNG 财报(Zalo MAU/收入拆分,季度)、Nhân Dân/Brands Vietnam(面板转引)。
- **上次核验**:2026-10-09(母语一手源重核:引擎份额/AI 使用与信任/平台格局两版口径/Zalo 盘子;本地实测 2 站×3 工具)。
