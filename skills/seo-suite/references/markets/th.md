# ตลาดไทย(泰语市场专项)

> **定位**:th 市场的增量情报层。数值型规则(title / desc 按字素 60 / 155、句 10–25 词、ครับ/ค่ะ 尾词一致、佛历年)在 `scripts/markets.json` 的 `markets.th`;总纲见 [multilingual-workflow](../overview/multilingual-workflow.md);电商见 [ecommerce-geo-ladder](../content/ecommerce-geo-ladder.md);链接市场见 [backlink-directory](../research/backlink-directory.md)。
> 数据锚点 2026-10-21;断言半衰期 6–12 个月。来源标注:【官方】=Google/监管机构/StatCounter 原始表/公司公告/平台官方页;【第三方研究】=写明样本和日期;【从业者说法】=博客或论坛转述,未核到一手;【本套件口径】=套件设计约定。

## 一、格局

### 1.1 引擎份额(StatCounter TH,2026-10-21 读 CSV)

| 口径 | Google | Bing | 其它 |
|---|---|---|---|
| 全设备 2026-09 | **99.37%** | 0.53% | DuckDuckGo 0.04%、Yandex 0.03% |
| 全设备 13 个月(2025-09~2026-09) | 98.86%–99.66% | 0.27%–0.91% | — |
| 桌面 2026-09 | 97.06% | 2.79% | — |
| 手机 2026-09 | 99.87% | 0.05% | — |

- 泰国没有本地通用搜索引擎。引擎面几乎只有 Google,竞争在语言机制和渠道上。
- 旧稿的「99.36% @ 2025-11」:2025-11 实际为 99.37%,2026-09 也是 99.37%,差异在四舍五入以内。

### 1.2 Google AI 功能时间线

- 2024-10-28:AI Overviews 扩到 100+ 国家,泰国在名单内(Google 博客 + 支持页 2024-11 快照)。泰语 AIO 的起始日未找到官方分语言公告;Google 支持页现行语言名单含 Thai。
- 2025-10-07/08:AI Mode 扩到 35+ 种新语言,Engadget 名单含 Thai。**Google 泰国博客 2025-10-08 写明「โหมด AI รองรับภาษาไทยแล้ว」**(`blog.google/intl/th-th/products/consumer-products/google-ai-plus-and-ai-mode/`)。旧稿「AI Mode 在泰国仅支持英文查询,泰语年内落地」已过时。
- Google 支持页另有「Gemini 4 Argon in AI Mode」名单(限登录的 Google AI Pro / Ultra 订阅者,18+,有每日用量限制),含 Thailand 与 Vietnam。
- 官方泰语文档(`developers.google.com/search/docs/appearance/ai-features?hl=th`)存在,这说明文档已本地化,不单独证明功能覆盖率。
- 泰语 AIO / AI Mode 出现率没有一手研究。引用任何出现率前,当天用 20 个核心词实测并记录日期。

### 1.3 搜索行为迁移

- 旧稿的「~40% 年轻人找餐厅不用 Google」来自 Google 副总裁 Prabhakar Raghavan 2022-07 的一次发言:「almost 40% of young people, when they're looking for a place for lunch, they don't go to Google Maps or Search」(TechCrunch 2022-07-12)。这是 Google 自己的研究,据其它报道对象为美国 18–24 岁,**不是泰国数据**。已改写为美国参照。
- 旧稿的「泰国 TikTok 日均 68 分钟」「TikTok 超过 Facebook 升至第 1」「Gen Z 品牌发现 TikTok 超过 Google」找不到原文,已删。判断发现型查询在哪个平台发生,用客户自己的 GSC 与各平台站内数据。

### 1.4 电商

- Momentum Works《Ecommerce in Southeast Asia 2026》总报告:东南亚 2025 年电商 GMV 1576 亿美元,Shopee、TikTok Shop、Lazada 三家占 98.8%(Momentum Works 2026-04 帖子与博客)。泰国国家表(旧稿的 50% / 32% / 18%、GMV 1.14 万亿泰铢 +52%)在付费报告里,未读到原文,已删。
- 旧稿的 PriceZa 口径(~1 万亿泰铢、卖家 >300 万)、Shopee 75% / Lazada 67% 使用率、ThaiPBS 78%、Milieu Insight 89% / 71%、佣金带 5–18%、「2026 三平台佣金普涨」:找不到原文,已删。佣金以各平台卖家中心现行费率表为准。

## 二、渠道

### 2.1 Pantip 与 seeding

- Pantip 的评测和「ซื้อไหม」类帖子常占搜索结果前列,这是【从业者说法】。品牌词审计查 Pantip 是否占位(`markets.json` 的 `serp_occupancy`、`complaint_lookalikes` 已收)。
- 旧稿列的 Fastwork / seeding2u / gorillaideas 服务页没有读到原文,按【从业者说法】处理:有代理公开售卖 Pantip 发帖和「删负面」服务。品牌方买这类服务有账号被识破、被社区反噬的风险;不买、不推荐。
- 正常路线:Pantip 官方认证账号答疑;真实体验活动并披露(สนับสนุนโดย / ร่วมรายการโดย)。【本套件口径】
- 旧稿的「โฆษณาแฝง 违反消费者保护委员会口径」没有读到条文,已删;法律判断请当地律师给。

### 2.2 平台特性(未核,只作线索)

- Lazada 偏内容完整度、Shopee 偏转化与服务指标、TikTok Shop 偏内容分发:这是从业者归纳,没有平台官方权重说明。做法:属性全填,看卖家中心数据。
- 站内搜索框的联想词是平台分词器切出的词组,可当免费泰语分词语料。【本套件口径】

### 2.3 LINE

- **LINE VOOM 已于 2026-09-28 在泰国终止服务**:LINE for Business 公告(2026-06-17)与 LINE 帮助中心均写明;帖子被删除;OA 主可在 2026-10-01 至 2026-12-31 通过 `voom-studio.line.biz` 下载自己发布的图片与视频;经 OA CMS 向 VOOM 发 Broadcast 的功能同日结束;LINE Ads 的 VOOM 版位将另行通知(`lineforbusiness.com/th/news/20260617`)。2026-09 之后的分发策略不得含 VOOM;外链清点把 VOOM 域链接按死链处理。
- LINE 泰国用户 **5600 万**(LINE 泰国发布会数字,relevantaudience、TECHMX 转述)。
- 品牌审计加一行:在 LINE 内搜品牌名,查官方 OA 是否在前、有无仿冒号。【本套件口径】

## 三、语言机制

### 3.1 分词

- 泰语词间无空格。`Intl.Segmenter("th", {granularity: "word"})` 是浏览器和 Node 内置的泰语分词接口(ICU 词典)。本机 Node v26.11.1 实测:`วิธีทำ SEO ให้ติดหน้าแรก Google สำหรับร้านค้าออนไลน์` 切成 `วิธี|ทำ|SEO|ให้|ติด|หน้า|แรก|Google|สำหรับ|ร้าน|ค้า|ออนไลน์`;`เราจัดส่งสินค้าภายในสองวันทำการ` 切成 8 词。
- 切分结果依赖 ICU 词典,不同运行环境可能略有差别。密度、精确匹配、关键词计数前先过它。
- GSC 导出的泰语查询,先分词再统计。站内联想词与 GSC 实查询对勘。

### 3.2 字素计数

- 泰语的组合元音和声调符号是独立码点,但与前一个辅音组成一个字素。Python `len()` 数码点会偏高。本机对 6 句泰语样本实测:码点数比 `Intl.Segmenter` 字素数高 21%–45%,合计高 29%。旧稿写「高估 30–50%」,按实测改为「约 20–45%」。
- `site_audit.py` 与 `market_lint.py` 的 `grapheme` 单位用「非组合符 + 非 Mn/Cf」近似:同样 6 句样本里比 Intl.Segmenter 每句多 1–2 个,偏差在约 4% 以内,可用于阈值判断。
- Google 对 title 与 description 没有固定字符上限,按显示宽度截断;60 / 155 字素是本套件提示阈值。meta 在词中间被截,逐页看搜索结果实际显示。

### 3.3 词数

- `site_audit.py` 的 `wc()` 对泰语按字素计数,**不是词数**:`เราจัดส่งสินค้าภายในสองวันทำการ` 在 `wc()` 得 26,而 `Intl.Segmenter` 得 8 词。所以 `markets.json` 里「句 10–25 词」不能用 `wc()` 结果判断。泰语句长用分词后的词数。
- 泰语句子之间用空格,不用句号。`market_lint.py` 的 `th` 用换行切句;`ste_lint.py` 按 `.!?` 切句,泰语正文被当作一整块(见第九节)。

### 3.4 书写与格式

- 佛历 = 公历 + 543:2026 年是 2569。Node 默认 `th-TH` 日历为佛历:`new Date("2026-10-21").toLocaleDateString("th-TH",{dateStyle:"long"})` 得 `21 ตุลาคม 2569`;`th-TH-u-ca-gregory` 得 `21 ตุลาคม ค.ศ. 2026`。商业页写明纪年。
- ครับ(男)/ค่ะ(女)礼貌尾词全站一致。【本套件口径】
- slug:Google URL 文档要求链接里的非 ASCII 字符做百分号编码;泰文 URL 编码后不可读,用音译或英文 slug。
- hreflang:`th` 或 `th-TH` 合法。

## 四、AI-GEO

- 通用 GEO 做法(段落级可引性、一手数据、实体一致)直接适用;泰语触发覆盖率没有一手研究(见 1.2)。
- 旧稿的「AIO CTR 冲击 −47%(泰语代理转引)」「ChatGPT 84.3% / Gemini 6.32%(Minimice)」没有读到原文,已删。
- 点击影响的外部参照都不是泰国数据(见 it.md 四);泰国站用自己的 GSC 分段 CTR。

## 五、红旗

1. 购买 หลังบ้าน(「后门」)链网或赌博站挂链:Google 垃圾内容政策把为排名买卖链接列为链接垃圾;被动收到赌场链接不自动中毒,按 disavow 台账处理。旧稿的「恢复以年计」没有原文,已删。
2. 付费链接不标 `rel="sponsored"`(政策原文:标注后的广告与赞助链接不违规,`developers.google.com/search/docs/essentials/spam-policies#link-spam`,核对 2026-10-21)。
3. 买 Pantip seeding 压负面帖。
4. 把 VOOM 写进 2026-09 之后的分发计划。
5. 用 `wc()` 的数字判泰语句长。
6. 引用美国的 40% 数字当泰国数据。

## 六、工具

| 工具 | 用途 | 备注 |
|---|---|---|
| StatCounter TH(CSV) | 引擎份额 | 见 1.1 |
| `Intl.Segmenter("th")` | 分词、字素计数 | Node / 浏览器内置 |
| GSC | 泰语实查询 | 导出后先分词 |
| Google Trends(geo=TH) | 趋势 | — |
| Shopee / Lazada / TikTok 联想词 | 分词语料 | 免费 |
| LINE OA Manager / LINE for Business 公告 | 私域分发与产品变动 | `lineforbusiness.com/th/news` |
| Pantip、ThaiSEOBoard | 舆情与行情线索 | 只读,不作采购渠道 |

## 七、法规适用范围(只写范围,不构成法律意见)

| 事项 | 适用范围与日期 | 一手来源 |
|---|---|---|
| 个人数据保护法(PDPA)B.E. 2562 | 2019-05-27 刊登政府公报;第 2 条:部分章节(第 II、III、V、VI、VII 章及第 95、96 条)延后一年生效;经多次皇家法令延期,**2022-06-01 全面生效**(law firm 通报,未读到最后一道皇家法令原文)。第 5 条:适用于在泰国的控制者或处理者;泰国以外的控制者或处理者,如向泰国境内的数据主体提供商品或服务,或监控其在泰国的行为,也适用。第 26 条:种族、政治观点、宗教、性行为、犯罪记录、**健康数据**、残障、工会、基因、生物特征等敏感数据,未经明示同意不得收集,另有法定例外 | 政府公报英译 PDF(DataGuidance 托管)逐条读到第 2、4、5、26 条;Nishimura、Hunton、DLA Piper 报告延期与 2022-06-01 |
| Cookie | 本套件未核到专门的 cookie 条文;按 PDPA 一般同意规则处理,是否需要同意由律师判断 | — |

## 八、本地实测(实测记录)

> 脚本口径 2026-10-21 已改:twitter:* 与 OG 重复只记 INFO;缺 H1 / 缺描述为 WARN。旧版 2026-10-09 的「thairath / pantip 报 ERROR / CRITICAL」不再适用。

- `site_audit.py https://pantip.com/ --market th --json`(2026-10-21):title 27 字素(上限 60 字素已生效)、description 129 字素、无 H1(WARN)、跳级 h2→h5(WARN)、无 JSON-LD(WARN)、272 链接(INFO);`words` 显示 2900 是字素数。`head_check.py --market th`:error=0。
- 旧版三个工具缺陷已修:title 解析吞脚本、`--market th` 不读阈值、微信/QQ itemprop 检查只在 zh 报。
- 仍存在:`wc()` 对泰语是字素计数(见 3.3);`ste_lint.py` 对泰语整块跳过。

## 九、语言处理事实(影响计数、去重、小写比较)

| 事实 | 可查方式 | 脚本现状(2026-10-21 实测) |
|---|---|---|
| 无词间空格 | `node -e` 调 `Intl.Segmenter("th")`(见 3.1) | `wc()` 返回字素数;`market_lint.py` 的 th 句长按空格短语近似,输出里自带 INFO 提示 |
| 码点 ≠ 字素 | 同上,`granularity:"grapheme"` | `site_audit.py` / `market_lint.py` 的 grapheme 与 Intl.Segmenter 偏差 ≤约 4%;`text_units.py th` 偏高:同一句 Intl 25、`text_units.py` 29(它只用 `unicodedata.combining()==0`,泰语元音符号 ccc=0 被计入) |
| 句子切分 | 泰语无句号 | `ste_lint.py --lang th` 对泰语正文报 0 句、跳过 1 块(`is_prose` 要求半数以上词为纯 ASCII 字母) |
| 提问对齐分词 | `question_align.py` 的 `tokens()` 对 `คืนสินค้าอย่างไร` | 得到空集合,覆盖率为 None:泰语查询不会被对齐 |
| 关键词归组 | `keyword_variants.py` | 无泰语规则,泰语词按原样分组 |

## 十、上线检查清单

| # | 检查什么 | 怎么查 | 通过 / 失败判据 |
|---|---|---|---|
| 1 | title / description 字素数 | `python3 scripts/site_audit.py URL --market th` | title ≤60、description 77–155 字素(本套件口径) |
| 2 | 字素与 Intl 对勘 | `python3 scripts/site_audit.py URL --market th --json` 的 title_len,再用 `node -e` 的 `Intl.Segmenter("th",{granularity:"grapheme"})` 分段数核一次 | 两者差 ≤2。不要用 `text_units.py th`:它只排除 combining≠0 的标记,把元音符号也计入,样本 25 个字素被报成 29 |
| 3 | meta 词中截断 | 在 Google 结果页(hl=th)搜该页,看 title 是否停在词中 | 无词中截断;有则把关键信息前置 |
| 4 | 句长 | 用 `Intl.Segmenter` word 分段数数句内词数 | 句 ≤25 词(markets.json th) |
| 5 | 礼貌尾词 | `python3 scripts/market_lint.py --market th page.html` | 无「ครับ 与 ค่ะ 混用」 |
| 6 | 佛历 | 同上 market_lint 的佛历检查;页面日期写 พ.ศ. | 商业页日期含 พ.ศ. 或明示 ค.ศ. |
| 7 | hreflang | `python3 scripts/hreflang_cluster.py URL_th URL_en` | 自引用、互指、语言码合法 |
| 8 | LINE VOOM 引用 | `curl -s URL \| grep -io "voom"` | 2026-09 后页面无 VOOM 链接或号召 |
| 9 | PDPA:健康数据表单 | 人工:收集健康数据的表单有明示同意勾选 | 第 26 条:明示同意,不预勾选 |
| 10 | 付费链接 | `curl -s URL \| grep -io 'rel="[^"]*sponsored[^"]*"'` | 付费链接带 sponsored 或 nofollow |
| 11 | AI 爬虫姿态 | `python3 scripts/robots_posture.py https://site/robots.txt` | 搜索类、用户类 bot 无非预期 blocked |
| 12 | 泰语 AIO 抽样 | 20 个核心词,hl=th,记日期、设备 | 报告写样本量和日期 |
