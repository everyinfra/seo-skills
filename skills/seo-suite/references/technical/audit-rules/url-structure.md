# 审计规则目录 · URL Structure

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### URL Structure(14 条,权重 3%)

slug 含描述关键词(数字 ID/?p=123 坏)=warn/fail;URL 停用词(占路径词数 >40%)=warn;大写=warn;下划线=warn(连字符才是词分隔);**双斜杠=fail**;**%20 编码空格=fail**;非 ASCII=warn;**完整 URL(含协议和主机)≤75 字符过、≤200 warn、>200 fail**;重复路径段(/blog/blog/)=**fail**;**查询参数 3-5 个=warn、>5=fail**,同名参数重复或多个 `?`=畸形=warn;**URL 会话 ID=fail**;UTM/追踪参数=warn;站内搜索 URL 被索引=warn;`url-http-https-duplicate`:绝对 canonical 的协议与页面不同=warn(不请求另一协议版本)。

**解释层(5 条;ID 未公布原文的按家族命名法推得并标 [待核])**

#### url-slug-quality [待核 ID]
- 名称/类型: slug 质量(源表 ID `url-slug-keywords`、`url-stop-words`) —— issue/warning · 优先级 high(数字 ID 形态)/low(停用词) · 输出 CRITICAL/WARN(源表:slug 含描述关键词,数字 ID/?p=123 坏=fail/warn 分型[口径待核];URL 停用词=warn)
**这意味(what)**: URL slug 不含描述性关键词:纯数字 ID 或 ?p=123 形态取内容(fail/warn 档),或 slug 塞满停用词(warn)。
**为什么(why)**: slug 是弱相关信号之一:外链 URL 展示、SERP 面包屑、引用复制里都会原样露出;?p=123 形态还与参数规范化纠缠。停用词只是稀释信息密度,故仅 warn。
**触发(trigger)**: 1) 路径段为纯数字/单字母 ID,或内容经查询串 ID 选取 → fail/warn 分型;2) 停用词(a、the、of 等)占路径词数 >40% → warn。
**不修的条件(caveat)**: 改 slug=改 URL=必须 301,老 URL 有外链与历史时改名收益常抵不过搬家风险,所以一般建议新页用好 slug、老页不为 SEO 单独改名。
**修复(fix)**: 新页 slug=主关键词短语(小写连字符);确需语义化的老 ID URL 用 301 迁移并同步更新内链与 sitemap。
**关联(seealso)**: url-shape、url-length;[link-architecture-patterns.md](../link-architecture-patterns.md)

#### url-shape [待核 ID]
- 名称/类型: URL 形态卫生家族(源表 ID `url-uppercase`、`url-underscores`、`url-double-slash`、`url-spaces`、`url-non-ascii`、`url-repetitive-path`、`url-http-https-duplicate`) —— warning · 优先级 low · 输出 WARN/CRITICAL(源表现行:大写/下划线/非 ASCII=warn;双斜杠、%20 编码空格、重复路径段=fail;canonical 与页面协议不同=warn)
**这意味(what)**: URL 含形态瑕疵:大写字母、下划线分词、双斜杠、非 ASCII 字符、重复路径段(/shoes/shoes/)、canonical 协议与页面不同(以上大写/下划线/非 ASCII/协议不符各 warn);双斜杠、重复路径段和 %20 编码空格为 fail。
**为什么(why)**: 形态决定"同一 URL 会有几种写法":大小写混用制造变体(Google 的 URL 处理区分大小写,见 technical-url-consistency);Google 建议用连字符分词、不建议下划线([URL 结构文档](https://developers.google.com/search/docs/crawling-indexing/url-structure),核对 2026-10-21);双斜杠/重复段制造规范化噪音。%20 空格是硬伤——空格在 URL 中非法,编码形态在点击/引用/重写链条上最易断裂。
**触发(trigger)**: 逐项:含大写 → warn;含 _ → warn;含 // → fail;路径段重复 → fail;含非 ASCII → warn;绝对 canonical 协议与页面不同 → warn;含 %20 → fail。http 与 https 双版本均 200 另用 `curl -sI http://域名/` 手工查。
**不修的条件(caveat)**: 单项瑕疵不(直接)影响排名,然而每项都在增加变体重复的概率,所以一般建议全站 lint。但非 ASCII(中文/日文 slug)在相应语种市场是正当形态,warn 不等于要求转拼音。
**修复(fix)**: 新 URL 全小写+连字符;CMS 输出层统一规范化;老 URL 301 到规范形;http 单向 301 到 https。
**关联(seealso)**: url-slug-quality、crawl-canonical-form-drift;[redirects-canonical.md](../redirects-canonical.md)

#### url-length
- 名称/类型: URL 长度 —— warning · 优先级 low · 输出 WARN/CRITICAL(源表现行:完整 URL 含协议与主机,≤75 字符过、≤200 warn、>200 fail;旧快照写「路径 ≤75」)
**这意味(what)**: 完整 URL 超过 75 字符。
**为什么(why)**: 长度本身不是排名因素,但超长路径几乎总意味着嵌套过深(点击距离超标,见 links-depth)、路径关键词堆砌、或筛选状态写进路径——这些才是问题,长度只是症状。75 与 200 是工具约定;Google 建议尽量缩短 URL、去掉不改变内容的参数([URL 结构文档](https://developers.google.com/search/docs/crawling-indexing/url-structure)),没有字符上限。
**触发(trigger)**: 完整 URL 长度 >75 warn,>200 fail。
**不修的条件(caveat)**: URL 长度不(直接)影响 SEO,然而它是结构与堆砌的症状指标,所以一般建议控制。但多级分类的文档站(v2/api/auth/methods)超线是结构真实,不是错误。
**修复(fix)**: 压层级(去掉冗余中间层)、砍路径关键词堆砌;筛选状态移到参数并由规范化收口。
**关联(seealso)**: links-depth、url-slug-quality;[link-architecture-patterns.md](../link-architecture-patterns.md)

#### url-query-params [待核 ID]
- 名称/类型: 查询参数家族(源表 ID `url-parameters`、`url-session-ids`、`url-tracking-params`) —— issue/warning · 优先级 high(会话 ID=fail)/medium(计数与追踪) · 输出 CRITICAL/WARN(源表:参数 3-5 个=warn、>5=fail;同名参数重复或多个 ?=畸形 warn;URL 会话 ID=fail;UTM/追踪参数=warn)
**这意味(what)**: 查询串失控:参数 3-5 个 warn、>5 个 fail;同名参数重复/多个 ? 畸形 warn;URL 带会话 ID(PHPSESSID/jsessionid 形态)fail;站内链接带 UTM/追踪参数 warn。
**为什么(why)**: 参数爆炸是抓取预算头号杀手:每个参数组合都是潜在唯一 URL,爬虫在组合空间指数级发散,预算耗尽时真页面反而抓不到。会话 ID 更重:每访客一个 URL=无限重复页,是 2000 年代就被定性的反模式。UTM 入内链则是把追踪污染引进自己站内。
**触发(trigger)**: 解析查询串:参数计数 3-5 → warn、>5 → fail;同名键 ≥2 次或 ≥2 个 ? → warn;参数名匹配会话 ID 模式 → fail;内链 href 含 utm_/gclid 等追踪参数 → warn。
**不修的条件(caveat)**: 参数本身不(直接)影响排名,然而参数空间决定抓取预算的消耗方式,所以一般建议站内链接零追踪参数、筛选参数规范化收口。但合法功能参数(分页 ?page=、排序 ?sort=)不可删——要的是规范化,不是消灭。
**修复(fix)**: 内链剥 UTM(仅保留外链入口);筛选参数 canonical 收口或 robots.txt 屏蔽;会话状态改 cookie 承载;参数计数超标先审功能设计。
**关联(seealso)**: crawl-sitemap-non-canonical、url-search-indexed;[robots-txt-reference.md](../robots-txt-reference.md)

#### url-search-indexed
- 名称/类型: 站内搜索结果被索引(源表 ID `url-internal-search`:只看 URL 形态,页面有 noindex 也照报) —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 站内搜索结果页(?s=/q=/search= 形态,键名口径[待核])可被索引——无 noindex、甚至进了 sitemap/内链。
**为什么(why)**: 搜索结果页是"关于查询的链接列表",无独立内容价值:无限查询组合也是抓取预算黑洞。Google 对「搜索结果页不该被索引」没有专页说法(其「自动生成内容」类垃圾政策不针对站内搜索),此处为工程判断。
**触发(trigger)**: 1) URL 匹配站内搜索参数形态;2) 页面可索引(无 noindex、被内链/sitemap 引用)即 warn。
**不修的条件(caveat)**: 搜索页索引不(直接)拖累其他页面排名,然而批量索引会稀释抓取预算,所以一般建议模板级 noindex。但确有搜索流量价值的长尾工具站,可把高价值查询做成内容化落地页保留索引——先看 GSC 流量再一刀切。
**修复(fix)**: 搜索结果模板加 noindex(整模板而非逐页);从 sitemap 与内链清除搜索 URL;站内搜索入口改 POST 或前端路由,不生成可爬 URL。
**关联(seealso)**: sd-searchaction、url-query-params;[robots-txt-reference.md](../robots-txt-reference.md)
