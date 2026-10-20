# Thị Trường Việt Nam(越南语市场专项)

> **定位**:vi 市场的增量情报层。数值型规则(title 45–65 字符、desc 155、词进前 30 字符、hreflang vi / vi-VN 等)在 `scripts/markets.json` 的 `markets.vi`;跨市场流程见 [overview/multilingual-workflow](../overview/multilingual-workflow.md);内容模式见 [content/content-patterns](../content/content-patterns.md)。
> 数据锚点 2026-10-21;断言半衰期 6–12 个月。来源标注:【官方】=Google/监管机构/StatCounter 原始表/公司年报/平台官方页;【第三方研究】=写明样本和日期;【从业者说法】=博客或论坛转述,未核到一手;【本套件口径】=套件设计约定。

## 一、格局:Google 为主,Cốc Cốc 在桌面有 7–11%

### 1.1 搜索引擎份额(StatCounter VN,2026-10-21 读 CSV)

| 口径 | Google | Cốc Cốc | Bing |
|---|---|---|---|
| 全设备 2026-09 | 92.94% | 5.96% | 0.65% |
| 全设备 13 个月(2025-09~2026-09) | 92.07%–95.96% | 3.37%–5.98%(均值 4.86%) | 0.37%–1.07% |
| 桌面 2026-09 | 82.62% | **11.26%** | 3.94% |
| 手机 2026-09 | 94.79% | 5.01% | 0.06% |
| 平板 2026-09 | 92.53% | 6.85% | 0.41% |

- 旧稿把 92.94% 写成「2025-08~2026-09 窗口」。它是 2026-09 单月值。旧稿的「按 host google.com 90.66% / coccoc.com 4.47%」读不到,已删。
- StatCounter 统计的是「从搜索引擎点击进入其会员站点」的 referral,不是搜索次数(`gs.statcounter.com/faq`)。
- 浏览器份额(StatCounter 同月,全设备):Chrome 66.04%、Safari 20.52%、Cốc Cốc **5.50%**;桌面 Cốc Cốc 7.58%,手机 4.57%。
- Cốc Cốc 自报用户数随年份变化(新闻稿和广告页出现过 25 / 28 / 30 百万),属公司自报口径;旧稿的「VWAS 手机使用率 ~21%、NPS 66」找不到原文,已删。
- Cốc Cốc 官方帮助站(`help.coccoc.com/searchengine`)自称「越南第二大搜索引擎」「每月 574+ 百万次查询」。

### 1.2 操作结论

- 桌面占比高的品类(工具站、下载站、办公类)才值得做 Cốc Cốc 位次跟踪。手机用户为主的站,Google 之外的预算先给 Zalo 和 Facebook 群。【本套件口径】
- 收录:官方帮助站写明可「逐个提交 URL」到 Cốc Cốc 索引。爬虫 UA 为 `coccocbot-web`(`Mozilla/5.0 (compatible; coccocbot-web/1.0; +http://help.coccoc.com/searchengine)`,KnownAgents 记录)。
- 验证爬虫真伪:CrawlCheck 记录显示 Cốc Cốc 不公布 IP 段或 DNS 名,所以无法验证,日志里的 UA 只能当声明。旧稿的「可经 bot API 验证 IP」依据是第三方 SEO API 服务,不是官方,已删。控制抓取用 robots.txt 的 UA 规则,不按 IP 封。
- 旧稿的「官方偏好越南语内容和 .vn 域」「sitemap 指引」在官方页面里读不到,已删。
- Cốc Cốc 每年 12 月发布《Báo cáo xu hướng tìm kiếm và lướt web》。2025 版 2025-12-17 发布(VietnamPlus、Tuổi Trẻ 同日报道)。它是选题用的本地面板数据,代表大众和娱乐流量,B2B 选题不据此定调。
- 产品发现链路常是:Zalo / Facebook 群 → 站内搜索(Shopee 等)→ Google。这个三段说法是【从业者说法】;客户问「Google 流量涨但订单不涨」时,先查前两段是否掉量。

## 二、渠道

### 2.1 Shopee 站内搜索

- Shopee 排名看店铺运营指标,不是站外 SEO。指标在 Kênh Người Bán(卖家中心)的数据看板里读。官方阈值和权重没有逐页核到,下面是做法,不是平台规则:
  - 产品名:「品类 + 品牌 + 型号 + 关键参数」,主词前置。【从业者说法】
  - 聊天响应率、取消率、延迟率:先修指标再改词。【从业者说法】
  - 站内搜索栏的联想词是最贴近购买意图的免费词源;站内词表和 Google 词表分开建、分开考核。【本套件口径】
- 旧稿的 Momentum Works 平台份额(Shopee 58% / TikTok Shop 39% / Lazada 3%)是付费报告里的国家表,只核到总报告标题「东南亚 2025 年电商 GMV 1576 亿美元,三大平台占 98.8%」(Momentum Works 2026-04),国家份额未核,已删。

### 2.2 新闻站外链(backlink báo)与 Google 政策

- 越南存在把新闻站 sidebar 全站链接、textlink 租期包、PR 文章位打包出售的服务。旧稿列出的各套餐价格来自服务商报价页,按任务要求已全部删除。
- Google 垃圾内容政策原文(link spam):买卖链接以影响排名属链接垃圾;大量全站链接、带优化锚文本的付费文章同样列为示例。同一段也写明:出于广告或赞助的链接买卖是正常商业行为,只要用 `rel="nofollow"` 或 `rel="sponsored"` 标注就不违规(`developers.google.com/search/docs/essentials/spam-policies#link-spam`,核对 2026-10-21)。
- 做法:
  1. sidebar 全站链接和纯锚文本位:不做。
  2. 带真实编辑价值的 PR 稿:可以做,链接加 `rel="sponsored"`,稿件标注赞助。
  3. 替代方案:可引用的数据研究(数字 PR)、协会和官方引用。
- 「PA/DA 高保证上排名」是话术:Moz 官方页写明 Domain Authority「is not a Google ranking factor」(`moz.com/learn/seo/domain-authority`,核对 2026-10-21)。

### 2.3 t0mmy 99 条(业内规则集,不是官方算法)

- 提问式 H2 ≥50%、密度只设上限、句长方差检测、标题词进前 30 字符、nonce 双层质量门:都是 t0mmy / mona-seo-check-vi 一类业内规则或本套件设计。【本套件口径】
- Google 对 title 没有固定字符上限,按显示宽度截断(见第一批已核结论)。65 字符是提示阈值。
- 疑问词五型:`là gì?`(定义)/ `như thế nào? / ra sao?`(过程)/ `Có nên ...?`(决策)/ `bao nhiêu?`(价格)/ `ở đâu?`(本地)。写 H2 时对着买家的真实提问选型,不凑比例;提问对齐的做法见 [content/question-alignment](../content/question-alignment.md)。

## 三、语言机制

- **有调 / 无调**:移动端用户常省略声调直接输入(`điện thoại` → `dien thoai`)。归组时合并估量,排名跟踪时当两个词各记一行。Google 是否把两形归一,不同查询结果不同,须用 GSC 实查,不预设。
- **đ 是独立字母**:Unicode 里 `đ`(U+0111)没有分解形(NFD 后不变),所以「NFD 去组合符」的脚本剥不掉它:`đường` 变 `đuong`,仍不等于无调输入的 `duong`(本机 Python 实测)。
- **音节与词**:越南语按空格分音节,一个词常含 1–3 个音节;按空格计数得到的是音节数。句长「15–20 词」在 vi 里实际是 15–20 音节,信息量低于英语同词数。
- **长度估算**:一般越南语句平均每音节含空格约 4–5 字符(样本句 34 字符 / 7 音节 = 4.9),65 字符的 title 约 13–14 音节。【估算】
- **slug**:用无调小写加连字符。带调 URL 在链接里会被百分号编码(Google URL 文档要求非 ASCII 字符做百分号编码),可读性差。改 slug 必须 301。
- **代词语域**:bạn/tôi 常规、anh/chị 服务敬称、quý khách B2B/金融,同站统一。【本套件口径】
- hreflang:`vi` 或 `vi-VN` 合法。

## 四、AI-GEO

### 4.1 Google AI 功能的时间线

- 2024-10-28:Google 把 AI Overviews 扩到 100+ 国家,越南在名单内(Google 支持页 2024-11 快照列出 Vietnam 与 Thailand)。越南语支持:Lao Động、VTV 报道称随该批上线;Google 英文博客只点名 English、Hindi、Indonesian、Japanese、Portuguese、Spanish 等例子,所以「越南语 AIO 的起始日」未核到官方原文。
- 2025-05-20:Google 宣布 AI Overviews 扩到 200+ 国家和地区、40+ 语言。
- 2025-10-07:AI Mode 扩到 35+ 种新语言和 40+ 地区;Engadget 的语言名单含 Vietnamese。AI Mode 与 Vietnam / Vietnamese 在 Google 支持页的现行名单中。
- Google 支持页(2026-10-21 读取)另有「Gemini 4 Argon in AI Mode」名单:限登录的 Google AI Pro / Ultra 订阅者(18+),有每日用量限制。名单含 Vietnam 和 Thailand,不含意大利、波兰、荷兰、比利时、土耳其。

### 4.2 用户面数据

| 指标 | 读数 | 来源 |
|---|---|---|
| AI 使用率 | 2025 下半年 23.5%(上半年 21.2%),全球第 38 位;全球 16.3% | Microsoft AI Economy Institute《AI Diffusion Report 2025》,VnEconomy 2026-01-13 转引【第三方研究】 |
| AI 信任度 | 全球第 3(65.6 分);接受度第 5(71.6);综合 6/40(59.2) | WIN World AI Index 2025,Nhân Dân 2025-07-23 转引【第三方研究】 |
| 平台份额 ChatGPT/Gemini/Meta AI | 旧稿 81/51/36 与 66/50/24 两版,来自 Decision Lab 面板 | 面板原文未核,已删 |

- 解读:使用率不高、信任度高,说明用户愿意信 AI 答案但还没养成习惯。该说法只是对两个指数的并列解读。
- 旧稿的「本土 AI(AI Hay、Kiki Info)进 top 10」未核。Zalo 年报披露其 Kiki 系列 AI 功能被约 30% 月活用户使用(VNG 2025 年报,见 7.1)。

### 4.3 GEO 页面级清单(本套件口径)

1. 每页至少一个可直接摘录的定义段,含主词原样措辞。
2. 数据与结论段配机构来源引文。
3. 有调、无调形各在正文自然出现;无调形不进标题。
4. 句长有变化,避免句句等长(见检查清单)。

## 五、红旗

| 级别 | 项目 | 处理 |
|---|---|---|
| 禁止 | sidebar 千条包、租期 textlink、廉价群发「Entity」包 | 拒绝;客户坚持则书面披露 Google 链接垃圾政策风险 |
| 灰区 | 带真实编辑价值的 PR 稿 | 加 sponsored、标赞助 |
| 允许 | 数字 PR、协会和官方引用、社区自然提及 | 主动建议 |

- 「mua backlink báo = white hat」是市场话术,与 Google 政策原文不符(见 2.2)。
- Shopee 刷单、假评:平台违规,不做、不推荐。
- 未经质量门的 AI 量产内容:Google 垃圾内容政策的 scaled content abuse 条款适用。

## 六、工具

| 工具 | 用途 | 备注 |
|---|---|---|
| StatCounter(CSV) | 引擎与浏览器份额 | 见 1.1 |
| Cốc Cốc 官方帮助站 | 提交 URL、UA 说明 | `help.coccoc.com/searchengine` |
| Cốc Cốc 趋势报告(`qc.coccoc.com`、`blog.coccoc.com`) | 本地搜索面板 | 12 月年度版 + 季度版 |
| Google Trends(geo=VN, hl=vi) | 趋势 | 有调、无调各建一条 |
| Shopee 站内联想词 + 卖家中心 | 站内词表与店铺指标 | 官方入口 |
| GSC + 关键词工具 | Google 侧 | 无调形需手工补录;`keyword_variants.py` 不会把 `đ` 并到 `d` |
| IDVS(forum.idichvuseo.com) | SEO 行情论坛 | 行情线索,不作规则来源;旧稿的「唯一持牌」说法未核 |

## 七、Zalo

### 7.1 数据(VNG 2025 年报,`ar2025.vng.com.vn/vi/business-report/zalo-ai/`)

- 2025 年 Zalo 分部收入 **1,718 tỷ đồng,+38%**;日均消息超过 21 亿条(+9%);首次非广告收入超过广告收入(VNG 年报原文)。VTC News 报道该收入占 VNG 总营收近 16%。
- 约 30% 月活用户在 2025 年使用至少一个 AI 功能;企业方案含 Official Accounts、Mini Apps、Zalo Notification Service(ZNS)(年报原文)。
- 月活:CafeF 标题称「近 8000 万用户」;旧稿的「78,3 triệu」和「通讯类份额近 70%」「覆盖 ~76% 人口」未在年报页读到,降为约数。
- 旧稿的「OA 2026-06-01 起 4 档新服务包」「OA Ads 以涨粉结算」找不到官方原文,已删;引用 OA 价格时查 Zalo 官方现行页。

### 7.2 用法(本套件口径)

- 品牌审计加一行:在 Zalo 站内搜品牌名,查官方 OA 是否认证、是否有仿冒号。
- OA 消息是通知型渠道,不是搜索流量;落地页仍要能被 Google 收录。

## 八、法规适用范围(只写范围,不构成法律意见)

| 事项 | 适用范围与日期 | 一手来源 |
|---|---|---|
| 个人数据保护法 91/2025/QH15 | 2025-06-26 通过,**2026-01-01 生效**;适用于越南机构、组织、个人;在越南的外国机构、组织、个人;以及直接参与或涉及处理越南公民及已发身份证的无国籍越南裔人员个人数据的外国机构、组织、个人(第 1 条第 2 款) | 全文页 `luatvietnam.vn/dan-su/luat-bao-ve-du-lieu-ca-nhan-2025-so-91-2025-qh15-405135-d1.html` |
| 实施细则 356/2025/NĐ-CP | 2025-12-31 发布,2026-01-01 生效 | `thuvienphapluat.vn/van-ban/Quyen-dan-su/Nghi-dinh-356-2025-ND-CP-...-687428.aspx`;`hungyen.gov.vn` 转载 |
| Nghị định 13/2023/NĐ-CP | 2023-04-17 发布,2023-07-01 生效,是越南首个全面的个人数据保护规定(vojs.vn 引述)。它在 2026-01-01 之后是否被废止,未读到条文,按官方公报为准 | `vojs.vn` 页面 |

## 九、语言处理事实(影响计数、去重、小写比较)

| 事实 | 可查方式 | 脚本现状(2026-10-21 实测) |
|---|---|---|
| 词数按空格得到音节数 | `site_audit.py` 的 `wc()` 对 `Chúng tôi giao hàng trong hai ngày` 得 7 | 变音字母不再被切碎;结果是音节数,不是词数 |
| `đ` 无分解形 | `python3 -c "import unicodedata as u;print(u.normalize('NFD','đ')=='đ')"` 得 True | `keyword_variants.py`:`đường` 与 `duong` **不同组**(`đường` 归到 `đuong` 组) |
| 提问对齐分词 | `question_align.py` 的 `tokens()` 对 `làm thế nào đổi trả` | 得到 `làm, nào, th, tr`:`ế`、`ổ`、`ả` 不在 `LATIN_WORD_RE` 字符集内,词被截断,覆盖率不可信 |
| STE 检查 | `ste_lint.py --lang vi` 对一段越南语正文 | 整块被当「非正文」跳过,报 0 句(`is_prose` 要求半数以上词为纯 ASCII 字母) |
| 有调字符检测 | `market_lint.py --market vi page.html` | 无任何带调字符的页面报 AUTO-FAIL(疑似未本地化) |

## 十、本地实测(实测记录)

> 脚本口径 2026-10-21 已改:twitter:* 与 OG 重复只记 INFO;缺 H1 / 缺描述为 WARN。旧版 2026-10-09 的「vnexpress / tinhte 报 ERROR」不再适用。

- `site_audit.py https://tinhte.vn/ --market vi --json`(2026-10-21):title 52 字符(上限 65 已生效)、description 162 字符(WARN 超 155)、无 H1(WARN)、1,377KB 内联 JS(INFO)、/llms.txt 404(INFO)。
- `head_check.py https://tinhte.vn/ --market vi`:1 ERROR:`<meta charset>` 位于第 1911 字节,超出前 1024 字节。其余为 INFO(twitter:* 与 OG 重复、meta keywords)。
- 旧版三个工具缺陷已修:title 解析吞脚本、词数碎片化、`--market vi` 不读阈值。微信/QQ itemprop 检查现在只在 zh 市场报。

## 十一、上线检查清单

| # | 检查什么 | 怎么查 | 通过 / 失败判据 |
|---|---|---|---|
| 1 | title / description | `python3 scripts/site_audit.py URL --market vi` | title ≤65、description 77–155 字符(本套件口径) |
| 2 | charset 位置 | `python3 scripts/head_check.py URL --market vi` | `<meta charset>` 在前 1024 字节内;error=0 |
| 3 | hreflang | `python3 scripts/hreflang_cluster.py URL_vi URL_en` | 自引用、互指、语言码合法 |
| 4 | 有调正文 | `python3 scripts/market_lint.py --market vi page.html` | 无「无任何带调字符」AUTO-FAIL |
| 5 | 句长变化 | 同上的 vi 句长变异系数项 | 变异系数 ≥0.25(本套件口径) |
| 6 | 有调 / 无调双行跟踪 | GSC 导出两形查询,各一行 | 台账里两形都有位次 |
| 7 | slug | `curl -sI URL \| grep -i '^location'`;人工看 URL | 无调小写 + 连字符;无百分号编码 |
| 8 | 提问对齐 | `python3 scripts/question_align.py --gsc q.csv --pages p.csv --min-impressions 20 --max-position 10` | 越南语查询的覆盖率要人工复核(分词缺陷,见 9) |
| 9 | 爬虫规则 | `curl -s https://site/robots.txt \| grep -i coccoc` | 如不想被 Cốc Cốc 收录才写 `coccocbot-web` 规则 |
| 10 | 付费链接 | `curl -s URL \| grep -io 'rel="[^"]*sponsored[^"]*"'` | 每个付费链接带 sponsored 或 nofollow |
| 11 | Zalo 品牌占位 | 在 Zalo 站内搜品牌名,截图 | 官方认证 OA 在首位;仿冒号数量写台账 |
| 12 | AI 爬虫姿态 | `python3 scripts/robots_posture.py https://site/robots.txt` | 搜索类、用户类 bot 无非预期 blocked |
| 13 | 个人数据合规 | 人工:表单收集个人数据的页面有告知和同意 | 对照 91/2025/QH15 与 356/2025/NĐ-CP 条文 |
