# 外链渠道目录（分级+核验日期）

> 站群、卫星站、PBN 的定级与审计见 [site-networks](site-networks.md)。本文件只管"哪些渠道值得做、先核什么"。
> 建立于 2026-10-09，2026-10-21 全文复核：目录逐个重新打开，费用和链接属性只写读到的内容，读不到的写"未核"。
> 渠道收录与格式参考三个公开清单：[flaqai/backlink_skills](https://github.com/flaqai/backlink_skills)（`Free-backlink-list.md` 列 743 个入口）、[alvinunreal/awesome-submitlist](https://github.com/alvinunreal/awesome-submitlist)（README 徽章 2026-10-21 显示 1,915 个 destinations，分类计数：目录 120、通讯 37、Subreddit 44）、[indie-hacking/Awesome-SEO-Backlinks](https://github.com/indie-hacking/Awesome-SEO-Backlinks)（最后提交 2024-02-29，数据已冻结）。星数会变，不写。
> 提交纪律：不群发。执行前重访该站核对当前条款。不承诺收录、dofollow 或排名。

## 一、先读 Google 政策边界

以下全部来自 [Google 垃圾内容政策 · Link spam](https://developers.google.com/search/docs/essentials/spam-policies#link-spam)（核对 2026-10-21，页面更新日 2026-08-28）。

| 做法 | 政策原文要点 | 本套件处理 |
|---|---|---|
| 为排名买卖链接 | 列为 link spam：用钱、商品或服务换链接，或寄送产品换带链接的文章 | 不做 |
| 付费链接加属性 | 原文：只要用 `rel="nofollow"` 或 `rel="sponsored"` 限定，买卖链接"不违反我们的政策" | 允许。付费目录、广告、赞助一律要求带这两个属性之一 |
| 软文、客座文、新闻稿里的传权重链接 | 付费文章中带传递排名权重的链接，或带优化锚文本的链接，列为 link spam | 只做带 `sponsored` 的版本 |
| 低质量目录或书签站链接 | 原文列为 link spam | 不批量提交；只做有真实编辑审核或真实访客的目录 |
| 自动程序造链 | 列为 link spam | 不做 |
| 全站页脚、模板里广泛分发的链接，论坛签名里的优化链接 | 列为 link spam | 不做 |
| 过度互链、仅为互链而建的伙伴页 | 列为 link spam | 不做 |
| 买来的过期域名 | 买过期域名并转作低价值内容以操纵排名，属 Expired domain abuse | 不做；见 [domain-strategy](domain-strategy.md) |
| PBN（私有博客网络） | 政策没有出现"PBN"一词；PBN 的目的是制造排名链接，落在上面几条之内 | 违反 Google 政策，不做 |
| 在他人高权重站发第三方内容以借其排名信号 | 属 Site reputation abuse（政策页称 site reputation policy） | 违反 Google 政策，不做；见 [site-networks](site-networks.md) |

Google 在 [2022-12 link spam update 公告](https://developers.google.com/search/blog/2022/12/december-22-link-spam-update)里写：系统用 SpamBrain 识别买链的站点和为传链而建的站点；"我们的算法和人工处理旨在大规模抵消这些非自然链接"（核对 2026-10-21）。

Bing 的 [Webmaster Guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a) 在 "Link Schemes and Artificial Promotion" 一节写：操纵入站链接以抬高权威违反准则，包括 link buying、link spamming、private networks 和模拟人气的人为社交推广；链接应"通过高质量、有用的内容自然获得"（核对 2026-10-21）。

**买链市场不再列价带表。** 上一版按市场列了 PBN、租链、付费新闻稿的价格和中介名。这些服务的卖点是传权重，多数违反上表。价格没有一手来源，已删除。需要付费曝光时，按 [qualify-links](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links) 要求对方加 `rel="sponsored"`，并按引荐流量而不是链接属性计价。

## 二、条目格式与指标口径

| 字段 | 说明 |
|---|---|
| 渠道名+入口 | 直达提交页 |
| 类型 | AI 工具目录 / 通用目录 / 发布社区 / 开发平台 / 本地目录 |
| 成本 | 只写读到的价格和日期；读不到写"未核" |
| 链接属性 | dofollow / nofollow / ugc / sponsored / 未核。用第八节的 curl 命令看 `rel` |
| 第三方指标 | DR（Ahrefs）、AS（Semrush）、DA（Moz）。写成"工具厂商指标"，注明取数日期 |
| 最后核验 | 打开页面的日期 |

三个指标都是工具厂商自己的评分，不是 Google 的信号。Google 2024-03-05 公告里有一句原话："有些第三方服务提供站点的“信誉”或“权威”评分。这些评分与 Google 自己的任何信号都不对应，也不来自 Google。"（[公告](https://developers.google.com/search/blog/2024/03/core-update-spam-policies)，核对 2026-10-21）各家定义：

- Ahrefs 的 DR 描述为"网站反向链接档案相对于其数据库中其他站的强度"，是相对量表，用来挑选建链对象（[Ahrefs 帮助](https://help.ahrefs.com/en/articles/1409408-what-is-domain-rating-dr)，核对 2026-10-21）。
- Moz 的 DA 页写明"与 Google 的排名算法不同，Domain Authority 不是直接排名因素"（[Moz](https://moz.com/learn/seo/domain-authority)，核对 2026-10-21）。
- 目录站自报的 DR 会漂移。2026-10-21 抽样：mcp.so 提交页同一页面正文写 DR 72，数据块写 74；mcpservers.org 此前写 71，现写 72。

## 三、基础渠道

核验方式：`curl -sIL -A "Mozilla/5.0" <入口>` 看状态码；返回 403 的站被 Cloudflare 拦，改用 search MCP 的 `read` 读正文。成本栏只记提交页上读到的内容。

| 渠道 | 类型 | 状态（2026-10-21） | 成本 | 链接属性 |
|---|---|---|---|---|
| [Product Hunt](https://www.producthunt.com) | 发布社区 | 在线（curl 200） | 免费发布；其他套餐未核 | 未核 |
| [Hacker News · Show HN](https://news.ycombinator.com/showhn.html) | 发布社区 | 在线，页面为 Show HN 规则 | 免费 | 未核 |
| [AlternativeTo](https://alternativeto.net) | 通用目录 | 在线（curl 403，search MCP 读到） | 官方 [FAQ](https://alternativeto.net/faq/) 写明用 "Suggest new application" 添加，免费；需账号 | 未核；第三方 Submitator 称抽样 54 条中混有 follow 和 nofollow |
| [Slant](https://www.slant.co) | 通用目录 | 在线（search MCP 读到） | 未核 | 未核 |
| [G2](https://www.g2.com) | 评测目录 | 在线（search MCP 读到），首页有认领档案入口 | 认领入口 `g2.com/add_product_requests/new`；是否收费未核 | 未核 |
| [Capterra](https://www.capterra.com) | 评测目录 | 在线（search MCP 读到） | 未核 | 未核 |
| [There's An AI For That](https://theresanaiforthat.com) | AI 目录 | 在线（search MCP 读到） | **付费**：提交页 2026-10-21 列 $49 一次性审核费（基础）和 $437 一次性费用（含通讯位）；免费名额只来自每月一次的 X 帖 | 未核 |
| [Futurepedia](https://www.futurepedia.io) | AI 目录 | 在线 | **付费**：提交页列 Basic $247（标 Sold Out）、Verified $497，一次性 | 未核 |
| [Toolify](https://www.toolify.ai) | AI 目录 | 在线（search MCP 读到） | **付费**：提交页写 $99，一次性，无免费档（搜索摘要读到 toolify.ai/submit 的 "Total: $99"） | 未核 |
| [AI 工具集](https://ai-bot.cn) | AI 目录（中文） | 在线（curl 200）；其提交页 `ai-bot.cn/submit-sites/` 本次读不到 | 未核 | 未核 |

上一版把 There's An AI For That、Futurepedia、Toolify 的成本写成"Free"，与各站提交页不符，已改。这几家是付费收录。按第一节，付费链接应带 `sponsored`，且这类 AI 工具目录的收录价值要看引荐流量，不看链接属性。三家的"保证流量"数字（如 700–10,000+ 访客）是站方自述，不采信。

## 四、本地目录与榜单（按市场）

**用途**：本地商户和 SaaS 的品牌信息一致性（名称、地址、电话、官网写法一致），以及可能带来的引荐流量。不为传权重批量提交。

**通用做法**（本套件口径）：先穷尽免费通道；每个市场只做该市场主流的 3–5 个目录；名称、地址、电话、官网 URL 逐字符一致；提交后用第八节命令验链接属性。

状态列均为 2026-10-21 打开首页的结果（"search MCP"表示 curl 被拦、改用 search MCP 读到）。

| 市场 | 渠道（状态） | 备注 |
|---|---|---|
| 中文 | [买购网 maigoo](https://www.maigoo.com)、[十大品牌网 CNPP](https://cn.cnpp.cn)：均在线 | 两站是不同网站。两站的"品牌申报"是否免费未核；榜单是商业榜单，名次不可承诺 |
| 俄语区 | [Яндекс Бизнес](https://business.yandex.ru/sprav/index)（在线，`yandex.ru/sprav/` 已跳转到 business.yandex.ru）、[2ГИС](https://2gis.ru)、[Zoon](https://zoon.ru)、[Flamp](https://flamp.ru)、[Yell.ru](https://www.yell.ru)、[Отзовик](https://otzovik.com)：均在线 | Яндекс Бизнес 的说明页写"创建公司档案"，是否收费未核 |
| 俄语区 | [TGStat](https://tgstat.ru)、[Telemetr](https://telemetr.io)：在线（search MCP） | Telegram 频道目录与统计；Telemetr 页面主推 Telegram Ads 工具 |
| 日语区 | [食べログ](https://tabelog.com)、[ホットペッパー](https://www.hotpepper.jp)、[じゃらん](https://www.jalan.net)、[楽天トラベル](https://travel.rakuten.co.jp)、[一休.com](https://www.ikyu.com)、[iタウンページ](https://itp.ne.jp)：均在线（后两者 search MCP） | 这些是平台，不是通用目录；是否适用取决于行业 |
| 日语区 | [note](https://note.com)、[アメブロ](https://ameblo.jp)、[PR TIMES](https://prtimes.jp)：均在线 | PR TIMES 是新闻稿分发服务，发稿费用未核；新闻稿里的传权重链接按第一节处理 |
| 西语区 | [Páginas Amarillas ES](https://www.paginasamarillas.es)（在线，要求先开 cookie）、[Sección Amarilla MX](https://www.seccionamarilla.com.mx)（在线，首页写"免费注册你的商户"） | |
| 巴西 | [Apontador](https://www.apontador.com.br)、[GuiaMais](https://www.guiamais.com.br)、[Solutudo](https://www.solutudo.com.br)、[Doctoralia BR](https://www.doctoralia.com.br)、[Jusbrasil](https://www.jusbrasil.com.br)、[GetNinjas](https://www.getninjas.com.br)：均在线 | [Telelistas](https://www.telelistas.net) 现已跳转到 buscja.com 页面，提交前先确认归属；iFood 是外卖平台，不当目录用 |
| 德语区 | [Gelbe Seiten](https://www.gelbeseiten.de)、[11880](https://www.11880.com)（首页写 440 万条目）、[Das Örtliche](https://www.dasoertliche.de)、[Cylex DE](https://www.cylex.de)、[local.ch](https://www.local.ch)、[search.ch](https://search.ch)、[pr-gateway.de](https://www.pr-gateway.de)：均在线 | Cylex 首页写批量上传"每条每年 1.00 欧元（不含增值税）"；pr-gateway 首页写分发到 250+ 新闻门户，属付费分发，链接属性按第一节处理 |
| 法语区 | [PagesJaunes](https://www.pagesjaunes.fr)、[118712](https://www.118712.fr)、[Avis Vérifiés](https://www.avis-verifies.com)、[societe.com](https://www.societe.com)、[Pappers](https://www.pappers.fr)、[Appvizer](https://www.appvizer.fr)、[Capterra FR](https://www.capterra.fr)、[Malt](https://www.malt.fr)、[Doctolib](https://www.doctolib.fr)：均在线 | societe.com 和 Pappers 是公开企业登记信息库，不接受"提交"，只可核对自己公司信息是否准确 |
| 印度 | [JustDial](https://www.justdial.com)（首页写 5.6 Crore+ 商户，即 5,600 万以上；有 Free Listing 入口）、[IndiaMART](https://www.indiamart.com)、[Sulekha](https://www.sulekha.com)、[TradeIndia](https://www.tradeindia.com)：均在线 | |
| 意大利 | [Pagine Gialle](https://www.paginegialle.it)：在线（search MCP） | |
| 泰国 | [Wongnai](https://www.wongnai.com)、[Yellowpages.co.th](https://www.yellowpages.co.th)：在线 | **ThaiSME 已删除**：thaisme.com 返回 523 且搜索查无，无法确认是否存在 |
| 波兰 | [Panorama Firm](https://panoramafirm.pl)、[Oferteo](https://www.oferteo.pl)：均在线 | |
| 荷兰 | [Telefoonboek.nl](https://www.telefoonboek.nl)、[Openingstijden.nl](https://www.openingstijden.nl)：均在线 | |

本节已删除的内容：各市场"AI 引用占比""均引位""商户数""佣金比例""DA 数值""提交几个目录最佳""某国曾因售链被整站处罚"等数字和断言，上一版都没有一手出处，2026-10-21 也查不到可信来源。

## 五、MCP 目录（产品有 MCP server 才做；2026-10-21 复核）

适用对象：已有可安装或可远程连接的 MCP server 的产品。没有的不要为外链去造。分层见 [directory-submissions](directory-submissions.md) 的 T3B/T4 层。

| 渠道 | 入口与材料 | 成本 | 链接属性 | 核验 |
|---|---|---|---|---|
| [mcp.so](https://mcp.so/submit) | 填 Repository URL 和 Name | 提交页只显示付费档 $39 一次性（免审即发、Verified 徽章、精选位、dofollow 项目链接）；是否有免费档未核 | 2026-10-17 抽样：免费条目项目链接 `rel="nofollow ugc noopener noreferrer"`，Verified 条目 `rel="noopener noreferrer"`。2026-10-21 条目页为前端渲染，curl 抓不到外链，**本次未复核** | 页面 2026-10-21；rel 2026-10-17 |
| [mcpservers.org](https://mcpservers.org/submit) | 名称、分类、简述、仓库或网址、可选 Official Registry 名、是否远程、邮箱 | 免费（页面写 2 周内审核）；$39 Premium（24 小时审核、Official 徽章、搜索优先、"Dofollow link (DR 72)"） | 付费档写 dofollow；免费档属性页面未写，条目页对脚本请求 403，未核 | 2026-10-21 |
| [Smithery](https://smithery.ai/docs) | 登录后在 smithery.ai/new 发布 | 免费 | 2026-10-21 抽 2 个条目页（/servers/brave、/servers/onesignal/onesignal）：外链均为 `rel="noopener noreferrer"`，即 dofollow | 2026-10-21 |
| [Glama](https://glama.ai/mcp/servers) | 目录页有 Add Server 入口 | 免费 | 2026-10-21 抽 1 个条目页：仓库链接无 rel；README 内链接和网站链接是 `rel="ugc nofollow"` | 2026-10-21 |
| [PulseMCP](https://www.pulsemcp.com/submit) | **暂停新提交，也不改已有条目**（页面更新日 2026-09-03）；官方建议先发 Official MCP Registry，恢复后会自动收录 | — | — | 2026-10-21（search MCP） |
| [Official MCP Registry](https://modelcontextprotocol.io/registry/quickstart) | 官方 `mcp-publisher` CLI：写 `server.json`、login（GitHub 或 DNS）、publish；npm 包需在 `package.json` 写 `mcpName` 且与 `server.json` 的 name 一致 | 免费 | API 型注册表，本身不产生 HTML 外链 | 2026-10-17，未复核 |

怎么用这张表：

- 免费条目基本拿不到 dofollow。免费上架的价值是开发者可发现性和引荐流量，按第九节 KPI 度量。
- 为 dofollow 付费前先看第一节：付费链接合规做法是 `nofollow` 或 `sponsored`。$39 档的审核提速、徽章和精选位，按引荐流量值不值单独算。
- 自述 DR 写"站方自述＋日期"，不当决策依据。
- 先发 Official Registry，再投别的目录；`server.json` 先定稿再发布，已发布版本的元数据不可改（Registry FAQ，2026-10-17 核）。

## 六、开发与内容平台（有实质内容才做）

- **GitHub**：README、Profile、Docs 里的链接是普通外链。GitHub 官方文档写明一个仓库最多 20 个 topics，名称限 50 字符（[GitHub 文档](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)，核对 2026-10-21）。这些元数据对 GitHub 站内搜索的影响没有官方公式；README 与元数据的检查见 [directory-submissions](directory-submissions.md) 第八节。
- **npm、PyPI**：包页主页链接。属性未核。
- **Medium、Dev.to、知乎专栏、微信公众号**：内容分发和个人页链接。UGC 平台上的外链通常带 `ugc` 或 `nofollow`，以实测为准。
- **Product Hunt、Hacker News、Reddit**：当发布与社区渠道，不当外链渠道。各自规则以站内社区准则为准，发布前读。

**寄生 SEO（barnacle SEO）**：指借大站权重让内容快速上首页。若做法是在他人站点发第三方内容以利用其排名信号，Google 的 site reputation policy 明确针对这种做法（[2024-11-19 公告](https://developers.google.com/search/blog/2024/11/site-reputation-abuse)：不管有没有宿主站参与，只要目的是借宿主排名信号就违规；[2026-08-28 公告](https://developers.google.com/search/blog/2026/08/update-site-reputation-policy)：自 8 月 30 日起，EEA 内受影响板块可能被单独排序，EEA 外照旧）。本套件不把它当策略。在 Reddit、Medium、Quora 上发内容的正当理由只有一个：回答真实问题、服务读者。

**Grokipedia 等 AI 百科**：上一版有一整节"诱导 Grok 引用"的话术（隐去品牌、混入权威来源等）和 6 个引用数字。数字没有一手来源，话术本质是伪装的自我推广，已删除。如果产品有真实、可核实的事实需要纠正或补充，用平台的建议编辑通道，写中性事实并附真实来源；不隐藏利益关系。

## 七、外链方法论（编辑性链接）

| 策略 | 做法 |
|---|---|
| 内容营销 | 造可链资产：研究、工具、指南、数据 |
| 客座发文 | 相关刊物投稿；付费版本带 `sponsored` |
| 断链建设 | 找他人站死链，荐自家内容补位 |
| 未链接品牌提及 | 监听提及，礼貌请求加链接 |
| 记者请求 | 回应记者，提供引语或数据 |
| 目录与精选清单 | 见第三至五节；"Best X"清单作者可 outreach |
| 数字 PR | 新闻或专家引语赚取编辑性链接 |
| 伙伴关系 | 联合发布；互换链接过量属 link spam |

Google 的口径：链接应是别人因内容有价值而自然给出的（见 [SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide) 推广一节）。外链画像的评估见 [backlink-profile-analysis](backlink-profile-analysis.md)。

**目录提交文案**：每个目录备三版长度（一句话、短、长），按站点读者换角度，产品名、定位、NAP 全程一致。

## 八、检查清单

| 检查什么 | 怎么查 | 通过/失败 |
|---|---|---|
| 渠道还在 | `curl -sIL -m 20 -A "Mozilla/5.0" <入口> -o /dev/null -w "%{http_code} %{url_effective}\n"`；403 用 search MCP 的 `read` | 200 且落在原域＝在线；跳转到别的域＝先核归属；超时且搜索查无＝删除 |
| 是否收费 | 读提交页，记价格和日期 | 有价格＝付费收录；对付费链接要求 `sponsored`；读不到＝写"未核" |
| 提交后链接属性 | `curl -sL <条目页> \| grep -oE '<a [^>]*href="https?://你的域名[^"]*"[^>]*>'` | 看 `rel`：含 nofollow、sponsored、ugc 任一＝不传权重；前端渲染页 curl 拿不到链接，用浏览器开发者工具看渲染后 DOM |
| 批量复检 | `python3 scripts/directory_tracker.py verify --entry DIR-001 --target https://你的域名`；`directory_tracker.py quarterly`（命令真实存在，见其 `--help`） | `verify` 只检查 rel 是否含 nofollow，不识别 sponsored 和 ugc；这两类要人工看。`quarterly` 队列非空时退出码 1 |
| 外链总体画像 | `python3 scripts/backlink_import.py <导出.csv> --format auto --out unified.csv`，再按 [backlink-profile-analysis](backlink-profile-analysis.md) 读 | 导入后字段齐全；格式嗅探失败退出码 2，不猜 |
| 季度抽样 | 每季度抽 10% 渠道重走前三行 | 死站移入归档并注明日期（本套件口径） |
| 反群发 | 单批不超过 10 个渠道，按类型分层，逐渠道记结果（本套件口径） | 一批里出现 2 个以上被拒或被删＝停批，查原因 |

## 九、提交结果度量（反虚荣 KPI）

用：合格发布率、引荐访问、引荐转化、档案准确率、收录存活率。
不用：提交数、外链数、dofollow 数、DA 或 DR 的涨幅。理由：这些指标衡量的是"做了多少"，不是"带来了什么"；DR 与 DA 是工具厂商指标（第二节）。

## 十、来源

- Google：[垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)、[限定外链属性](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links)、[2022-12 link spam update](https://developers.google.com/search/blog/2022/12/december-22-link-spam-update)、[2024-11 site reputation abuse 更新](https://developers.google.com/search/blog/2024/11/site-reputation-abuse)、[2026-08 site reputation policy 更新](https://developers.google.com/search/blog/2026/08/update-site-reputation-policy)（以上核对 2026-10-21）
- 渠道清单：flaqai、alvinunreal、indie-hacking 三个公开仓库（链接见文首）
- 各目录提交页与首页：2026-10-21 打开所得，见第三至五节
- MCP 目录：mcp.so/submit、mcpservers.org/submit、pulsemcp.com/submit、smithery.ai、glama.ai 页面；[MCP Registry Quickstart](https://modelcontextprotocol.io/registry/quickstart) 与 [FAQ](https://modelcontextprotocol.io/registry/faq)
