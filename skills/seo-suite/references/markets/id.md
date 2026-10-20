# Pasar Indonesia(印尼语市场专项)

> **定位**:markets/id.md 是 id 市场的增量情报层。数值型规则(title/desc 60/155、句 15-20 词、meta 前 120 字符安全区、1.234,56 数字格式、slow-4G 基线)在 `scripts/markets.json` 的 `markets.id`;总纲印尼语区段见 [multilingual-workflow](../overview/multilingual-workflow.md),电商面见 [ecommerce-geo-ladder](../content/ecommerce-geo-ladder.md),链接市场见 [backlink-directory](../research/backlink-directory.md)。写法约定见 [asd-ste100-web-writing](../content/asd-ste100-web-writing.md);标题与首段怎么对齐买家提问见 [question-alignment](../content/question-alignment.md)。
> 2026-10-21 逐条核对一手来源(StatCounter、Google 官方博客与 Search Central、IANA、Badan Bahasa、Shopee 与 Tokopedia 官方卖家教育页、BPK 法规库、Permenaker);二手研究标「第三方研究」。断言半衰期 6-12 个月。

## 一、格局(Pasar:一个 Google,AIO 触发率被报告为全球最高)

### 1.1 引擎与 AIO

StatCounter 印尼搜索引擎份额,2026-09 月值,取数 2026-10-21([页面](https://gs.statcounter.com/search-engine-market-share/all/indonesia)):

| 口径 | Google | 第二名 | 备注 |
|---|---|---|---|
| 全设备 | 92.30%(12 月区间 92.30–93.74) | Bing 3.04%、DuckDuckGo 2.19%、Yahoo 1.73% | |
| 桌面 | 89.43% | Bing 6.24%、Yahoo 3.89% | |
| 移动 | 94.31%(12 月区间 94.31–97.25) | DuckDuckGo 3.57%、Yandex 1.11%、Bing 0.76% | 移动端 DuckDuckGo 高于 Bing |

- 无本地通用搜索引擎。竞争面在渠道与语言,不在引擎分配。
- 旧稿「移动端口径更高 ~95%」与 2026-09 的 94.31% 同档;「Chrome ~85% 份额」未核,已删。
- **AIO 上线**:Google 2024-08-15 官方公告把 AIO 带到印尼(含本地语言支持),数周内逐步推送([Google 官方博客](https://blog.google/products/search/new-ways-to-connect-to-the-web-with-ai-overviews/));2024-10-28 扩 100+ 国并支持印尼语等([官方博客](https://blog.google/products-and-platforms/products/search/ai-overviews-search-october-2024/))。
- **AI Mode 印尼语**:2025-09-08 随印地语、日语、韩语、巴西葡语一起上线([Google 官方博客](https://blog.google/products-and-platforms/products/search/ai-mode-expands-more-languages/))。
- **AIO 触发率 37.2%**:Limadata 的一篇文章(2026-06-14)称印尼 37.2% 的关键词触发 AIO,为受测市场第一,对照美国 20.5%([Limadata](https://limadata.co.id/articles/how-ai-search-is-changing-online-visibility-in-2026))。本次抓取该页失败,无法核方法、样本和日期;而「美国 20.5%」与 Ahrefs 2025-09 桌面样本的全体 20.5% 数字相同,可能是转引。按「第三方、方法未核」使用。
- 旧稿「Arfadia:信息类 CTR 从 1.41% 跌至 0.64%」:1.41%→0.64% 是 Seer Interactive 对有 AIO 查询的美国客户数据(2025 年初),不是印尼数据([Seer](https://www.seerinteractive.com/insights/aio-impact-on-google-ctr-september-2025-update))。已改。
- Ahrefs(2026-02-04)称位置 1 的点击在有 AIO 时低 58%([Ahrefs](https://ahrefs.com/blog/ai-overviews-reduce-clicks-update/))。样本非印尼专属。
- 「~65% 搜索零点击」「68% 零点击、48% AIO 出现率」来自本地帖转引,无原文,已删。
- 做法(本套件口径):GEO 与排名同权交付;报价与 KPI 按「答案可见度」设计。用 Search Console 的生成式 AI 表现报告(2026-06-03 公布,2026-08-31 起全球开放;展示、页面、国家、设备、日期,无点击;[Search Central 博客](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports))看印尼展示。

### 1.2 AIO 引用格局

- 旧稿的「YouTube 12.7% 第一被引」「Tokopedia #6」「品牌官网价格查询仅 1.9%」「SE Ranking 全球 YouTube 4.43%」没有可核来源(未写研究名称和样本),已删。
- 巴西同类研究可作参照:SEONextbr 的巴西样本里 YouTube 65.4%、Instagram 37.0% 被 AIO 引用(见 [pt.md](pt.md))。**印尼没有公开的同类研究**,用自己的方法测:选 50 个高价值印尼语查询,逐个在 AI 模式与 AIO 里记被引域名。
- 本套件假设(待测):视频、marketplace、新闻门户占引用面;品牌官网在品牌词与深度研究词上有位置。

### 1.3 电商大盘

- cube.asia(2026-06-02)的东南亚六国(印尼、马来西亚、菲律宾、新加坡、泰国、越南)合并数据:2025 年 Shopee 占合并平台 GMV 59%,TikTok Shop 31%(2024 年 23%,2025 年增长 66%),Lazada 9%(2024 年 16%,2025 年下降 28%)([cube.asia](https://cube.asia/shopee-lazada-and-tiktok-shop-in-southeast-asia-what-the-data-shows-in-2026/))。这是**六国合并**口径,不是印尼单国口径。印尼是该数据里 GMV 最大的市场。
- 旧稿的印尼单国数字(TikTok Shop×Tokopedia 32%、Shopee 用户触达 47.5%、Lazada 6.2%、B2C 盘子 $43.4B、TikTok Shop 印尼 GMV $13.1B/全域 $45.6B)未找到来源,已删。印尼单国份额按 cube.asia 的印尼页面取数(第三方,付费细分)。

## 二、渠道(Saluran:站内搜索先于 Google)

### 2.1 Tokopedia

- **Analisis Pencarian**:Tokopedia University 有官方说明——卖家后台的搜索分析给出热词;对需要优化的商品点击「Perlu Optimasi」会跳到商品名编辑页并选择关键词([Tokopedia University](https://seller-id.tokopedia.com/university/essay?knowledge_id=2933138536302337&lang=id-ID),页面 2024-03-25)。2025-10 的另一页还有 Data Compass → Peringkat Kata Kunci。这是印尼语商品词研究的免费一手来源。
- 「算法明示价格是排名因子」没有读到官方原文,已删。
- 商品标题公式(本套件口径):核心词 + 属性 + 规格。

### 2.2 Shopee

- 官方卖家教育页写明:卖家须在收到聊天后 **12 小时内**回复,才计入「Persentase Chat Dibalas」([Shopee 卖家教育](https://seller.shopee.co.id/edu/article/1878),2026-03-17)。超过 12 小时的回复不计入。
- 这些是店铺表现指标。「直接影响店铺排名」官方页面未写权重,标为假设,用自己店铺的数据验证。
- 「聊天好的店转化高 ~34%」「理想转化 2–3%」出自 GineeHub 转述,无原文,已删。
- 官方学习渠道:Shopee University ID、Tokopedia University,均免费。

### 2.3 TikTok Shop

- 站内搜索联想词可作印尼语用户切分的语料(本套件口径)。佣金带「5–18%」未核,已删。
- 口播词被 Google 索引:TikTok 内容可能进入 Google 视频结果,需自己用 Search Console 视频报告核对(本套件口径)。

### 2.4 低价 SEO 套餐

- 旧稿列了各平台「Rp99.000–Rp500.000/月」低价包与 Rp6.000.000+ 代理价。价格来自在架页面,会变,已删。
- 判断依据不靠价格:Google 把以排名为目的的买卖链接、规模化自动生成内容列入垃圾政策([Spam policies](https://developers.google.com/search/docs/essentials/spam-policies),更新 2026-09-16)。审计低价包时,要求供应商给出每月交付物清单和链接来源,逐条查。

## 三、语言机制(Mekanisme Bahasa)

### 3.1 三区操作律:关键词跟手指,正文跟词典(本套件口径)

- 第一区(title/H2/slug/meta/alt)跟用户的写法:gaul 形式照收("gak""udh")。
- 第二区(正文)一律 baku,保可读性与可信度。
- 第三区(FAQ/评论区/UGC)再跟手指,收口语长尾。
- 落地为双轨关键词表:每个核心词出 baku 与 gaul 两行。
- 旧稿引的 Ivan Lanin《Dilema Kata Baku dan SEO》本次未读到原文,不再作为依据。

### 3.2 baku 与 gaul 分区(本套件口径)

| 内容域 | 语域 |
|---|---|
| 医疗/金融/法律 | 一律 baku |
| 实用/生活/电商 | gaul 优先 |
| B2B/企业站 | baku 半正式 |

### 3.3 五档 ragam 矩阵(本套件口径)

1. Ragam resmi(公文、法律、标书);
2. Baku lugas(企业官网、白皮书、新闻体);
3. Percakapan santai(博客正文、邮件、客服);
4. Gaul(社媒、电商详情页、口播);
5. Prokem/sandi(亚文化黑话,品牌内容禁用)。

- 每篇内容开工前指定档位,跨档混用视为缺陷。

### 3.4 EYD V 与宗教词

- 现行正字法 **EYD Edisi V**:Badan Bahasa 负责人决定 No. 0424/I/BS.00.01/2022,日期 **2022-08-16**([官方 PDF](https://badanbahasa.kemendikdasmen.go.id/resource/doc/files/SK_EYD_Edisi_V_16082022.pdf))。
- 词形:masjid(非 mesjid)、Ramadan(非 Ramadhan)按 KBBI 为标准写法(KBBI 条目经 [kbbi.web.id](https://kbbi.web.id/masjid-atau-mesjid) 与 [detik 2026-02-20](https://www.detik.com/sumbagsel/berita/d-8364094/cek-11-kata-baku-tentang-ramadan-sesuai-kbbi-awas-keliru) 转述,KBBI Daring 原页本次未直接打开)。musala 的标准写法同理(Balai Bahasa 材料)。
- "Ramadhan" 的双 h 写法在用户查询里仍大量存在:关键词层照收,正文层改正。

### 3.5 Ramadan 与 THR 季节律

- Ramadan 1448 的天文换算起点约 **2027-02-08**(乌姆库拉历,`hijridate`);印尼以政府宣布为准,可能差一天。
- THR(宗教节日津贴)法律规定:雇主须在宗教节日前**最迟 7 天**支付(Permenaker No. 6/2016,[Kemnaker 原文](https://jdih.kemnaker.go.id/asset/data_puu/permenaker_6_2016.pdf))。这意味着与薪资相关的搜索与消费在节前约一周前后集中。
- 内容排期(本套件口径):Ramadan 前 6–8 周发布,节中只做更新。旧稿「产品搜索 +30%」「食品查询 2.2×」找不到原文,已删。用 Google Trends(地区 ID)核对本年曲线。

## 四、AI-GEO

- 品牌词与价格词分工(本套件假设):品牌词做官网,价格词做 marketplace 占位。旧稿「品牌词 AIO 官网出现率 72.2%」「价格类仅 1.9%」无来源,已删。
- 移动端占比高:本套件把 slow-4G 作为测试基线(`markets.json`)。CrUX 是真实用户数据,可用 `field_data.py` 取(见检查清单)。旧稿「移动 >82% 搜索流量」未核,按本站 GSC 设备拆分。
- 引用面候选(审计首批假设,逐项用自己的查询验证):YouTube、Tokopedia/Shopee 商品页、新闻门户(detik、Kompas、Liputan6)、医疗(Halodoc、Alodokter)、Wikipedia(id)。

## 五、信息源

| 源 | 角色 | 用法 |
|---|---|---|
| cmlabs | 本地大型 SEO/GEO 内容厂,有免费电子书 | 监控其博客=监控本地共识;其数据按「第三方」引用 |
| DailySEO ID | 从业者社区与课程 | 实操风向 |
| Arfadia、RevoU、Glints | 教育厂与年度报告 | 交叉验证 |
| Shopee University、Tokopedia University | 平台官方教程 | 平台规则一手来源 |

- 旧稿的 ads.id 灰产交易区情报条目已删:是否列入这类站点不属于 SEO 方法。

## 六、红旗

### 6.1 买链与 PBN

- 主动购买 PBN 链接属于 Google 链接垃圾政策范围。政策原文:以排名为目的买卖链接、以及用自动化程序创建链接,均违反政策;标 `rel="sponsored"` 或 `nofollow` 的付费链接不违规([Spam policies](https://developers.google.com/search/docs/essentials/spam-policies),[qualify outbound links](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links))。
- 旧稿列出的具体平台、「$15/条」价格、「抗每次更新」话术已删(无公开来源,且属买链价格)。
- 收到垃圾链接不等于被处罚;只有收到人工操作通知时才考虑拒绝工具(本套件口径)。

### 6.2 盗版(nulled)主题与插件

- 盗版主题可能带后门,本套件把它当首要入侵向量(本套件口径,未找到印尼专项统计)。接手存量站先核主题与插件授权。
- 被黑站被改造成链接农场是常见攻击后果(Google 把此类站点归为被黑垃圾,见 Spam policies「Hacked content」一节)。

### 6.3 三级红线(本套件口径)

| 级别 | 项 | 处理 |
|---|---|---|
| 禁止 | 购 PBN 链、装盗版主题 | 即拒 |
| 灰色 | marketplace 刷单、达人合作无披露 | 合同写披露条款,按平台规则查 |
| 允许 | Shopee FAQ 自动应答、真实 UGC、官方账号答疑 | 鼓励 |

## 七、法规

- **UU PDP(Undang-Undang No. 27 Tahun 2022 tentang Pelindungan Data Pribadi)**:2022-10-17 公布;两年过渡期于 **2024-10-17** 结束([BPK 法规库](https://peraturan.bpk.go.id/Details/229798/uu-no-27-tahun-2022);过渡期日期见 [kres.id 时间线](https://www.kres.id/pp-33-2026-aturan-pelaksana-uu-pdp))。
- **PP 33/2026**(实施条例):2026-07-16 签署并公布(Lembaran Negara 2026 No. 88),**2027-01-16 生效**(Pasal 225)。据 kres.id 摘要,含 3×24 小时泄露通报、行政罚款上限 2% 年收入、AI 相关 DPIA 等([kres.id](https://www.kres.id/pp-33-2026-aturan-pelaksana-uu-pdp)、[Hukumonline](https://www.hukumonline.com/berita/a/pelindungan-data-pribadi-dalam-penegakan-hukum-dan-konfigurasi-beracara-di-bawah-pp-33-2026-lt6ac4acd9db1bd/))。条文细节以官方公报为准,摘要为律所或咨询公司文章。
- 适用范围提示:处理印尼境内个人数据的网站和 App 要对照。这是范围提示,不是法律意见。

## 八、Alat(工具)

| Alat | 用途 | 备注 |
|---|---|---|
| Google Keyword Planner | 印尼语月检索量 | 精度需用 GSC 校准 |
| Google Trends(地区 ID) | Ramadan/THR 季节曲线 | 年度排期基准 |
| Search Console 生成式 AI 报告 | 印尼展示 | 2026-08-31 起全球开放,只报展示 |
| Tokopedia Analisis Pencarian | 官方站内关键词工具 | 免费一手来源 |
| Shopee 卖家教育后台 | 聊天回复率等指标 | 店内指标主控台 |
| JNews(Jegtheme) | 印尼新闻站常见 WordPress 主题 | 接手存量站时先查授权;本次未核其功能列表 |

## 上线检查清单

| # | 检查什么 | 怎么查 | 通过/失败判据 |
|---|---|---|---|
| 1 | hreflang 码 | `python3 scripts/hreflang_cluster.py <id URL> <en URL>`;页面源码 `rg -n 'hreflang=' page.html` | 用 `id` 或 `id-ID`,**不用 `in`**。IANA 语言子标签表:`in` 自 1989-01-01 弃用,首选值 `id` |
| 2 | `<html lang>` | `rg -o '<html[^>]*lang="[^"]*"' page.html` | `lang="id"`(Google 不靠 lang 判语言,但辅助技术和浏览器翻译会用) |
| 3 | 头部元素 | `python3 scripts/head_check.py <URL> --market id --timeout 40` | 无 ERROR;印尼站从海外访问常慢,超时调大 |
| 4 | title/description | `python3 scripts/site_audit.py <URL> --market id --json` | 本套件口径:title ≤60、description 77–155 字符,关键信息在前 120 字符 |
| 5 | 市场 lint | `python3 scripts/market_lint.py --market id <html文件> --url <URL> --report` | CRITICAL=0;baku/gaul 项人工过 |
| 6 | 数字与电话 | `python3 scripts/local_format.py --market id "<页面样本文本>"` | `1.234,56`、`+62` 全部 ✓ |
| 7 | 真实用户 CWV | `python3 scripts/field_data.py --url <URL> --strategy mobile`(需 `PSI_API_KEY`) | LCP ≤2.5s、INP ≤200ms、CLS ≤0.1 为 good(官方阈值,脚本写死) |
| 8 | AI 检索爬虫放行 | `python3 scripts/robots_posture.py https://<域名>/robots.txt --signal visibility` | 搜索类与用户类 allowed |
| 9 | llms.txt(可选) | `python3 scripts/llmstxt.py check https://<域名>` | 看返回体是 markdown,不是 HTML 兜底页 |
| 10 | EYD V 词形 | 在内容里 `rg -n -i -e mesjid -e musholla -e ramadhan <文件>`(正文层) | 正文层命中为 0;关键词层保留属有意 |
| 11 | 盗版主题/插件 | 列出主题与插件清单,逐个核授权;在 wordpress.org 或供应商处核版本 | 全部有正版授权 |
| 12 | Marketplace 占位 | 手工搜 30 个核心词于 Tokopedia/Shopee,记录排名 | 每词记录位置;月度对比 |
| 13 | 低价 SEO 供应商审计 | 要求每月交付物清单与链接来源 | 每条链接可追溯来源;无 PBN |
| 14 | AI 报告 | Search Console 生成式 AI 表现报告(若已开放),国家=印尼 | 记录展示;未开放则手工抽查 |

## 本地实测(2026-10-09)

> 脚本口径 2026-10-21 已改:twitter:* 与 OG 重复只记 INFO;缺 H1/描述为 WARN。下面的 ERROR/CRITICAL 数是旧口径结果,复测会不同。

### 真实站验证(detik.com / kompas.com / tokopedia.com)

| 项 | detik.com | kompas.com | tokopedia.com |
|---|---|---|---|
| site_audit | 跳级 h1→h3 / 301 链接 / alt 缺失 85/111(77%) | 4 个 AI 检索爬虫全禁(OAI-SearchBot、ChatGPT-User、Claude-SearchBot、PerplexityBot);原始 HTML 无 H1 | 15s 超时(两跑两败) |
| head_check | charset 位于第 2364 字节(>1024)+ 弃用 meta 堆叠 | charset 1980 字节同类违规 | 未跑通 |
| llmstxt | `/index.html.md` 返回 200 但是 HTML 壳,假阳性 | 全无 | 未跑通 |

- kompas.com 当日封禁四个 AI 检索爬虫,detik 不封。两站对照只说明这一天这两家的立场不同,不推出市场格局(单次快照)。
- tokopedia.com 首页海外访问超时:审计印尼头部站要用本地出口或调大超时。
- detik alt 缺失 77%:新闻站图片多,alt 审计优先级较高。
- **工具盲区**:`head_check`/`site_audit` 没有 baku-gaul 或 EYD V 检查,`markets.json` 里的 EYD V 项是文档级标记。词形检查可用上面检查清单第 10 项的 `rg` 做初筛,只能查已知违拼词。
- llmstxt check 对 catch-all 服务器产生假阳性(不校验返回体):`.md` 孪生探测结果须人工看头 80 字符。

## 维护

- 复审周期 **90 天**,下一次 **2027-01-09**(以 `scripts/markets.json` 的 `markets.id.review_cycle` 为准)。
- 触发即复审:cube.asia 的印尼页面季度更新、PP 33/2026 生效(2027-01-16)前后的执行指引、kompas 类头部媒体 AI 爬虫立场、cmlabs 新 playbook、Search Console 生成式 AI 报告对印尼站点的开放度。
- 数字分诊:GMV 数字必带分母(六国合并、单国、单平台);AIO 触发率区分第三方方法与官方数据。

## 建议(需要别处配合,本文件不改)

| 键路径 | 现值 | 应改值 | 来源 |
|---|---|---|---|
| `scripts/markets.json` → `markets.id.notes` | 「AIO 触发率 37.2% 全球第一」 | 加口径「Limadata 文章,方法未核」 | Limadata 2026-06-14 |
| `markets.id.special_checks[5]` | 「Shopee 12h 回复率直接影响排名(聊天好转化+34%)」 | 改「Shopee 官方:12 小时内回复才计入 Persentase Chat Dibalas;对排名权重官方未写」,删 +34% | Shopee 卖家教育 |
| `markets.id.special_checks[6]` | 「低端 jasa SEO Rp99k-500k=结构性 PBN」 | 改「低价包要求交付物与链接来源清单」,删价带 | Google spam policies |
| `markets.id.special_checks[8]` | 「PBN×nulled 闭环($15/条 .id 域)」 | 删价格 | 无公开来源 |
| `markets.id.review_cycle.signals[0]` | 「cube.asia/Momentum Works 季度 GMV 更新(TikTok Shop×Tokopedia 31-39% 带…)」 | 改「cube.asia 印尼页面」,说明 31% 是东南亚六国合并口径 | cube.asia 2026-06-02 |
| `markets.id.review_cycle.signals[3]` | 「GSC AI Performance Report 印尼语数据开放度」 | 改名「Search Console 生成式 AI 表现报告」(2026-06-03 上线) | Search Central 博客 |
| `markets.id.hreflang_codes` | `["id","id-ID"]` | 保留 | IANA 子标签表 |
| `markets.id.engines` | `["google","chatgpt","tokopedia","shopee"]` | 保留;在 notes 说明「ChatGPT/TikTok Shop 的印尼份额未核」 | — |
