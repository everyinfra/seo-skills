# GA4 中与 SEO 相关的设置要点

用途：检查或设计 GA4，使它能回答「自然搜索带来了哪些访问、落在哪些页面、产生了什么结果」。需要你自己的 GA4 媒体资源访问权限；事件设计见 [event-library.md](event-library.md)。

## 必查设置

| 设置 | 为什么和 SEO 有关 | 检查什么 |
|---|---|---|
| 数据流与增强型衡量 | 页面浏览、滚动、外链点击、站内搜索、视频、文件下载、表单互动等事件 | 是否开启；站内搜索的查询参数是否在默认的 5 个（`q`、`s`、`search`、`query`、`keyword`）之内，不在就补上（[增强衡量事件](https://support.google.com/analytics/answer/9216061)） |
| 关键事件 | 衡量自然流量的业务价值 | 只标少数代表业务结果的事件（每个媒体资源最多 30 个，[配置上限](https://support.google.com/analytics/answer/12229528)）；价值和币种是否正确 |
| 自定义维度 | 按页面类型、内容分组、作者分析 | 事件参数要先注册为自定义维度才能在报告中使用；事件级上限 50 个，用户级 25 个（[创建事件级自定义维度](https://support.google.com/analytics/answer/14239696)） |
| 跨网域与引荐排除 | 支付页、第三方登录回跳会把自然流量错记为引荐 | 多域名是否配置跨网域衡量（各域名的标签用同一个 `G-` ID，通过 `_gl` 参数传递 cookie，[官方说明](https://support.google.com/analytics/answer/10071811)）；不需要的引荐来源是否加入「不需要的引荐」列表（[官方说明](https://support.google.com/analytics/answer/10327750)） |
| 内部流量过滤 | 员工访问会污染落地页数据 | 是否定义内部流量规则（给事件加 `traffic_type` 参数）并把对应数据过滤器从 Testing 切到 Active（[官方说明](https://support.google.com/analytics/answer/10104470)） |
| 数据保留期 | 同比分析需要较长的明细数据 | 标准媒体资源的事件级数据保留期只能选 2 个月或 14 个月，它只影响探索和漏斗报告，不影响标准聚合报告；当前值以 Admin 里显示为准，需要更长就手动选 14 个月（[数据保留](https://support.google.com/analytics/answer/7667196)） |
| 关联 Search Console | 在 GA4 中查看查询与自然搜索落地页 | 建立关联需要 GA4 媒体资源的编辑者角色，并且是 Search Console 资源的已验证所有者；Search Console 报告集合默认不发布，要在「库」里手动发布（[官方说明](https://support.google.com/analytics/answer/10737381)） |

## 常用分析视角

- 落地页报告，按「会话默认渠道分组 = Organic Search」筛选：每个落地页的会话、互动率、关键事件。
- 按内容分组或自定义维度汇总：比较专题集群、页面类型的贡献。
- Search Console 报告（关联后）：查询、展示、点击与落地页的对应关系；这部分数据来自 Search Console，口径与 GA4 会话不同。

## 口径陷阱

- GA4 的会话数与 Search Console 的点击数不会相等：同意拒绝、广告拦截、跨设备和统计定义都会造成差异（本套件口径；没有官方给出的固定差异比例）。
- 落地页显示 `(not set)`：官方说明是会话里没有 `page_view` 事件（[`(not set)` 说明](https://support.google.com/analytics/answer/13504892)）。同意模式配置错误是常见原因：同意后用 `default` 命令而不是 `update` 命令，会丢掉初始 `session_start`。占比高时先查同意模式实现。
- 默认渠道分组依赖来源 / 媒介规则；自定义 UTM 用错会把自然流量归到别处，站内链接不要加 UTM（本套件口径）。来自 ChatGPT、Gemini、Copilot、Grok 等的访问归入 AI Assistant 渠道；Google 的 AI Overviews 和 AI Mode 点击归入 Organic Search（[默认渠道分组](https://support.google.com/analytics/answer/9756891)）。
- 数据阈值：含人口统计或搜索查询信息的报告行，用户数不够时会被隐藏；阈值由系统设定，不能调整，拉长日期范围可以减少隐藏（[数据阈值](https://support.google.com/analytics/answer/9383630)）。探索报告每次查询超过 1,000 万事件会采样（[配置上限](https://support.google.com/analytics/answer/12229528)）。
- 高基数维度会把长尾折叠成 `(other)` 行（[官方说明](https://support.google.com/analytics/answer/10075209)）：明细行加总不等于总数时，在结论里写明。

## Measurement Protocol

服务端补发事件（例如线下成交回传）时使用。需要你自己的衡量 ID 和在 GA4 中创建的 API secret，示例中都是占位符：

```text
POST https://www.google-analytics.com/mp/collect?measurement_id=G-XXXXXXX&api_secret=YOUR_API_SECRET
```

请求体必须带 `client_id`（和前端同一个值）；一次请求最多 25 个事件；只支持 POST。事件名和参数与前端保持同一套命名；不要发送个人信息；`api_secret` 不要放进前端代码（[发送事件](https://developers.google.com/analytics/devguides/collection/protocol/ga4/sending-events)、[参考](https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference)，核对 2026-10-21）。请求格式错误时不返回 HTTP 错误码，先用 `/debug/mp/collect` 校验（[校验事件](https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events)）。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 事件和参数 | 用 DebugView 或 Tag Assistant 逐个触发事件（DebugView 要先开 `debug_mode`，[官方说明](https://support.google.com/analytics/answer/7201382)），核对名称和参数 | 通过：名称、参数与 [event-library.md](event-library.md) 清单一致。失败：缺事件或参数为空 |
| 自然搜索归类 | Reports → Acquisition → Traffic acquisition，主维度「Session default channel group」；从 Google 搜索结果点进站点一次，再看实时报告 | 通过：会话落 Organic Search。失败：落 Direct 或 Unassigned，查来源 / 媒介和跨网域设置 |
| `(not set)` 与异常引荐 | Engagement → Landing page 报告，筛 `(not set)`；Traffic acquisition 报告查来源 / 媒介里出现支付商、登录商域名 | 本套件口径：`(not set)` 落地页会话占比超过 5% 就排查（官方没有阈值）；异常引荐出现自家域名或支付商域名即失败 |
| Search Console 关联 | Admin → Product links → Search Console links；Library 里确认 Search Console 报告集合已发布 | 通过：有关联且报告集合在左侧导航可见。失败：只有关联、没发布报告集合 |
| 内部流量过滤 | Admin → Data filters，看状态；用内部 IP 访问后在 DebugView 看事件是否带 `traffic_type=internal`，再看过滤后实时报告 | 通过：过滤器为 Active，且内部访问不进报告。失败：仍为 Testing，或事件缺 `traffic_type` |
| 数据保留 | Admin → Data collection and modification → Data retention | 通过：事件数据保留为 14 个月。失败：仍是 2 个月，探索报告看不了更早日期 |
| 配额（用 Data API 拉数时） | 读 `runReport` 响应里的 `propertyQuota`（用 `returnPropertyQuota: true`）；标准媒体资源每天 200,000 tokens、每小时 40,000 tokens、并发 10（[Data API 配额](https://developers.google.com/analytics/devguides/reporting/data/v1/quotas)） | 通过：已用量低于上限的 80%（本套件口径）。失败：接近上限时缩小日期范围、少用高基数维度，或分批 |

## 市场差异:测量栈与合规(拉平轮)

| 市场 | 分析栈现实 |
|---|---|
| 俄语区 | 受 152-ФЗ 约束：俄罗斯联邦通信监督局（Roskomnadzor）2024-06-26 的答复 № 08-242780 写明，用 Google Analytics 处理个人数据属于跨境传输，运营者要先向它发出通知（[原文](https://www.garant.ru/products/ipo/prime/doc/409415443/)）；第 18 条第 5 款要求俄罗斯公民个人数据的首次记录和存储用位于俄罗斯境内的数据库（[条文](https://www.consultant.ru/document/cons_doc_LAW_61801/)）。因此俄语站常用 Yandex Metrica，它带 Вебвизор 会话回放、点击图、滚动图和表单分析（[点击图帮助](https://yandex.ru/support/metrica/ru/behavior/click-map)）。「免费」来自第三方介绍，未在官方页核到 |
| 德语区 | 不少站选 Matomo 或 Plausible（常见做法，本套件口径，无官方统计）。cookie 横幅判例：OLG Köln 2024-01-19（6 U 80/23）判决要求横幅提供与同意「同等价值」（gleichwertig）的拒绝选项（[判决原文](https://nrwe.justiz.nrw.de/olgs/koeln/j2024/6_U_80_23_Urteil_20240119.html)）；VG Hannover 2025-03-19（10 A 5385/22）审的是首层是否必须有「全部拒绝」按钮（[判决](https://voris.wolterskluwer-online.de/browse/document/230df5cf-d76c-4561-9499-e44445a96f11)；标题含「muss eine Alle-ablehnen-Schaltfläche enthalten」的解读见 [Beckmann & Norda](https://www.beckmannundnorda.de/serendipity/index.php?/archives/7228-VG-Hannover-Cookie-Banner-Cookie-Consent-Tool-fuer-technisch-nicht-notwendige-Cookies-muss-eine-Alles-ablehnen-Schaltflaeche-enthalten.html)，第三方）。横幅设计由合规驱动 |
| 法语区 | CNIL 2022-02-10 对一家使用 Google Analytics 的网站发出正式通知，认定向美国传输数据违法（当时的传输机制；[Lefebvre Dalloz，第三方](https://formation.lefebvre-dalloz.fr/actualite/un-gestionnaire-de-site-web-mis-en-demeure-par-la-cnil-utiliser-google-analytics-dans-les-conditions-actuelles-nest-pas)，CNIL 原页已下线）。之后欧盟委员会于 2023-07-10 通过欧美数据隐私框架充分性决定，欧盟普通法院 2025-09-03 驳回了对它的撤销诉讼（[EUR-Lex T-553/23](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:62023TJ0553)），所以 2022 年的结论不能直接套用到今天。Piano Analytics 2025-04 获得 Europrivacy 认证（[Piano 公告](https://www.piano.io/resources/first-in-digital-analytics-to-achieve-europrivacy-certification)）；「数据主权是采购决策词」是销售侧判断，未核 |
| 巴西 | 国家数据保护局（ANPD）的 Cookie 指南（2022-10 发布，2025-01 修订）把「在首层和次层横幅都提供易见的『拒绝全部非必要 cookie』按钮」列为良好实践，把「只突出接受按钮、让拒绝或设置按钮难以看到」列为应避免的做法；指南自称这些是非穷尽的良好实践，不是法律的逐条规定（[指南 PDF](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-orientativo-cookies-e-protecao-de-dados-pessoais.pdf)）。KPI 以 Search Console 为锚（本套件口径：它不依赖站点的 cookie 同意） |
| 通用 | 报表结构（本套件口径）：Search Console 数据为基准线，GA4 数据（含建模值）并列显示同意率。建模有官方资格门槛（见 [event-library.md](event-library.md)「同意模式下的降级方案」），流量低于门槛的站不要依赖建模。服务端 GTM 在欧盟站点很常见，但没有官方「标配」说法 |

## 来源

本文由 EveryInfra 自行编写，只保留要点，未复制原文。

- 思路参考：[coreyhaines31/marketingskills · skills/analytics-tracking/references/ga4-implementation.md](https://github.com/coreyhaines31/marketingskills/blob/v1.10.0/skills/analytics-tracking/references/ga4-implementation.md)（MIT）
- 一手资料：[GA4 事件](https://support.google.com/analytics/answer/9322688)、[GA4 推荐事件](https://support.google.com/analytics/answer/9267735)、[GA4 Measurement Protocol](https://developers.google.com/analytics/devguides/collection/protocol/ga4)、[Search Console 效果报告](https://support.google.com/webmasters/answer/7576553)

## GA4/GSC 连接器操作纪律(notfair 深读 2026-10-09b)

来源:nowork-studio/notfair-plugin 的 analytics/google-analytics、analytics/search-console 与 analytics/shared/operating-contract(MCP 连接器工作流,第三方仓库);下列带官方链接的条目已逐条对官方文档核对(2026-10-21),没有链接的是本套件口径。

### 资源定位(先于一切查询)

- **GA4 资源只能用连接器返回的 `properties/123456789` 资源名**(Data API 的 `property` 参数格式,示例 `properties/1234`,[runReport](https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport));`G-` 衡量 ID 标识的是数据流,不是媒体资源([Measurement Protocol](https://developers.google.com/analytics/devguides/collection/protocol/ga4/sending-events))。先列属性确认访问,再选资源。
- **GSC 属性用连接器返回的确切已验证形式**:`sc-domain:example.com`(域名属性)与 `https://example.com/`(网址前缀属性)是两个不同属性([Search Analytics API](https://developers.google.com/webmaster-tools/v1/searchanalytics/query));域名属性覆盖全部子域和协议,要按路径或协议限定数据时用网址前缀属性([添加属性](https://support.google.com/webmasters/answer/34592))。
- 平台未连或未授权→指引用户重连并**停止,不得声称拿到的是实时数据**。

### 取证纪律(GA4)

- 定义业务问题、主指标、转化/关键事件定义、**资源时区**、日期窗、对比窗,再拉数据;每个重要结论旁必须写明这些口径。
- **一次宽批量读优于多次窄读**;尊重连接器当前暴露的维度/指标/fan-out/配额限制,不照搬别平台的限制。
- 不熟的维度/指标组合先查元数据再猜(Data API 有 `getMetadata`,[文档](https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport));**检查响应元数据中的采样/阈值/配额告警**;出现 `(other)` 折叠行=数据因基数上限被合并,明细行加总不等于总数,必须声明([官方说明](https://support.google.com/analytics/answer/9756891))。Data API 标准媒体资源的配额:每天 200,000 tokens、每小时 40,000 tokens、并发请求 10([配额](https://developers.google.com/analytics/devguides/reporting/data/v1/quotas))。
- 当日/近期数据视为临时值并注明时区;**GA4 归因与广告平台归因分开报**,解释差异而不是混合不相容的数字;相关≠因果,无证据不得宣称渠道/页面变化导致了结果。
- 结论结构:什么变了→在哪变→有证据的可能驱动因素→置信度→下一个测量或业务动作;附上报告定义以便他人复现。

### 取证纪律(GSC)

- **对账资源级 clicks/impressions 时去掉 `query` 维度拉总数**——匿名化查询(只有少数用户搜过的词)不出现在 query 行里,按 query 加总会少于总数([官方深度解读](https://developers.google.com/search/blog/2022/10/performance-data-deep-dive))。
- API 的 `dataState` 设为 `all` 时包含未定稿的新数据,省略或设为 `final` 只返回定稿数据([query 文档](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)),`all` 的结果标临时;**不要对已聚合的 CTR/position 行做朴素平均**(本套件口径);API 不保证返回全部行,只返回靠前的行,`rowLimit` 取值 1–25,000,默认 1,000,所以结果要声明"top 行而非完整导出"。
- URL Inspection 配额比 Search Analytics 紧(两者数字见[配额表](../overview/facts.md#api-quotas))。**按需用**。它只返回 Google 索引里那个版本的索引状态,不能测试实时网址,**不会请求索引**([index.inspect](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect));排名波动是证据,不是某次算法更新的证明(本套件口径)。
- 结论以"最大实质性增/减→受影响词/页→有证据的假设→置信度→下一步 SEO 动作"开头。

### 测量配置变更安全(与上面必查设置互补)

- 改配置前展示:确切资源、当前状态、目标状态、对下游报表的影响、回滚方案,再请求批准。
- **可逆性矩阵**(本套件口径):关键事件创建/删除互为可逆;**自定义维度归档在 GA4 不可撤销**,归档后维度不能恢复,依赖它的受众条件要重建,但名称可以再用([归档说明](https://support.google.com/analytics/answer/12436143))——必须获得点名"资源+维度名"的明确批准。
- 写入后用返回的前后证据或新读确认;部分失败如实上报,**不盲重试**;连接器未明确支持并确认,不得声称"报告已保存/仪表板已发布"。
