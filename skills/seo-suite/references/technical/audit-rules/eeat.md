# 审计规则目录 · E-E-A-T

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

## 二、重点展开:E-E-A-T(16 条)

| 规则 ID | 名称 | 严重度 | 判定要点 |
|---|---|---|---|
| `eeat-about-page` | About 页 | warn | 检测 About/About Us 页存在 |
| `eeat-affiliate-disclosure` | 联盟披露 | warn | 联盟内容须有 FTC 披露("This post contains affiliate links.") |
| `eeat-author-byline` | 作者署名 | warn | 页面有作者归属 |
| `eeat-author-expertise` | 作者资历 | warn | 作者凭证+简历+资历页 |
| `eeat-citations` | 引用来源 | warn | 链向权威源(.gov/.edu/论文/行业出版物) |
| `eeat-contact-page` | 联系页 | warn | email/电话/表单/地址至少其一 |
| `eeat-content-dates` | 内容日期 | warn | datePublished/dateModified(Article schema 或 `<time>`) |
| `eeat-disclaimers` | YMYL 免责声明 | warn | 医疗/财务/法律内容须有相应免责声明 |
| `eeat-editorial-policy` | 编辑政策 | warn | 编辑政策页(内容标准/事实核查流程) |
| `eeat-physical-address` | 实体地址 | warn | PostalAddress(Organization/LocalBusiness schema) |
| `eeat-privacy-policy` | 隐私政策 | warn | 页脚隐私政策链接 |
| `eeat-terms-of-service` | 服务条款 | warn | 页脚 ToS 链接 |
| `eeat-trust-signals` | 信任信号 | warn | 评论/认证/安全徽章/媒体报道 |
| `eeat-ymyl-detection` | YMYL 检测 | info | 仅识别 YMYL 内容(触发更高 E-E-A-T 标准),不扣分 |
| `eeat-geo-meta` | geo meta | warn | 有 local-business schema 的页也应设 geo meta 标签 |
| `eeat-nap-consistency` | NAP 一致性 ⛏ | warn | 同一组织名在整站爬取中只挂一个电话+地址;不同名=不同主体;需 crawl |

**结构拆法**:16 条 = 信任基建 5(about/contact/privacy/ToS/address)+ 作者维度 2(byline/expertise)+ 内容维度 3(dates/citations/disclaimers)+ 商业披露 1(affiliate)+ 治理 1(editorial-policy)+ 信号 1(trust-signals)+ 检测器 2(YMYL/geo-meta)+ 跨页一致性 1(NAP)。**eeat-ymyl-detection 是开关型 info 规则**——它给 YMYL 判定供数给 disclaimers 等,呼应我们 seo-ops T4"拿不准即标 true"。

**解释层(14 条,第四批;ID 为源目录原文;privacy+ToS、physical-address+geo-meta 各并一条家族条)**

### eeat-author-byline
- 名称/类型: 作者署名缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 内容页(文章/指南/评测)没有可见的作者归属——无 byline,也无链接到作者档案的署名元素。
**为什么(why)**: Google 在有用内容文档里写「We strongly encourage」在读者期待的地方加准确的作者信息(byline),并让 byline 链到作者背景;伪造作者信息不可取。E-E-A-T 本身不是具体排名因素([有用内容文档](https://developers.google.com/search/docs/fundamentals/creating-helpful-content))。署名也是 Article author 字段的可见依据:结构化数据描述的内容须在页面可见([结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies))。
**触发(trigger)**: 1) 页面属内容模板(文章/博客/新闻形态,判定口径源表未公布[待核]);2) 无作者名文本或指向作者档案的署名链接即 warn。
**不修的条件(caveat)**: 署名不是直接排名因素,然而它是整条 E-E-A-T 评估链的入口,所以一般建议内容页必配。但公司公告/产品页/工具页以组织身份发布是正当形态,author 用 Organization 代替 Person 即可。
**修复(fix)**: 内容模板加可见 byline 并链接到作者档案页;与 Article schema 的 author 字段同源输出;匿名编辑部的站至少给"编辑团队"一个实体页。
**关联(seealso)**: eeat-author-expertise、sd-required-fields;[content-patterns.md](../../content/content-patterns.md)、[geo-evidence.md](../../content/geo-evidence.md)

### eeat-author-expertise
- 名称/类型: 作者资历标记缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn;作者凭证+简历+资历页)
**这意味(what)**: 有作者署名,但作者资历不可验证——无 bio、无凭证(头衔/资质/从业背景)、无独立作者页。
**为什么(why)**: 署名回答"谁写的",资历回答"凭什么信"。Google 的自评问题包括:byline 是否链到作者背景与所写领域([有用内容文档](https://developers.google.com/search/docs/fundamentals/creating-helpful-content))。Person schema 的 jobTitle/knowsAbout 把资历机器可读化;作者页是 author 实体 @id 的落点,缺它署名实体悬空(联动 sd-entity-reference 的 dangling 判定)。
**触发(trigger)**: 1) 页面存在署名;2) 站内无对应作者档案页,或 bio 缺凭证要素(要素清单口径[待核])即 warn。
**不修的条件(caveat)**: 资历呈现对非 YMYL 内容的常规排名影响有限,所以一般建议按内容风险分级:YMYL 全配,普通内容至少 bio+头衔。但个人品牌站(域名即作者本人)可弱化独立作者页。
**修复(fix)**: 建作者档案页(bio/凭证/同主题其他文章);Article 的 author 指向该页 Person 的 @id;补 jobTitle/knowsAbout 字段。
**关联(seealso)**: eeat-author-byline、sd-entity-reference;[entity-signal-checklist.md](../entity-signal-checklist.md)、[knowledge-graph-guide.md](../knowledge-graph-guide.md)

### eeat-content-dates
- 名称/类型: 内容日期缺失/更新机制缺位 —— warning · 优先级 medium · 输出 WARN(源表 warn;datePublished/dateModified,Article schema 或 `<time>`)
**这意味(what)**: 内容页没有发布/更新日期,或日期只有视觉层没有机器可读载体(Article schema 的 datePublished/dateModified 或 `<time datetime>`)。
**为什么(why)**: Google 有"query deserves freshness"系统,对需要新内容的查询展示更新的内容([排名系统指南](https://developers.google.com/search/docs/appearance/ranking-systems-guide))。可见日期与机器可读日期要一致,三处年份打架另归 content-agreement。正解是真实更新加真实 dateModified,而不是机械刷新时间戳(会被 crawl-sitemap-date-drift 的交叉比对识破)。
**触发(trigger)**: 1) 内容模板页无 datePublished(或等价 `<time>`)即 warn;2) 有发布无更新日期是否单判[待核:源表按 Article 必填口径]。
**不修的条件(caveat)**: 日期不是全场景排名因素(常青内容挂显眼旧日期反而降 CTR),所以一般建议信息敏感内容配全、常青内容可只留发布年月。但把构建时间当修改时间写入是必须清掉的造假形态。
**修复(fix)**: CMS 把真实 updated_at 输出到 Article schema 的 datePublished/dateModified 与 `<time>`;内容保鲜流程见 [content-refresh-playbook.md](../../content/content-refresh-playbook.md)。
**关联(seealso)**: eeat-author-byline、content-agreement、crawl-sitemap-lastmod;[content-refresh-playbook.md](../../content/content-refresh-playbook.md)、[content-decay-signals.md](../../content/content-decay-signals.md)

### eeat-citations
- 名称/类型: 权威引用缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn;链向权威源 .gov/.edu/论文/行业出版物)
**这意味(what)**: 内容页的论断没有外部权威来源支撑——无出站引用,或引用全指向低可信源。
**为什么(why)**: Google 说链出引用来源有助于建立可信度,nofollow 只用于不信任的来源([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable))。把引用链接全 nofollow 等于亲手关掉这个信号(见 links-nofollow-external)。.gov/.edu 等"权威域清单"是工具约定,不是 Google 规则。
**触发(trigger)**: 源表现行:正文里(导航、页头、页脚、侧栏及指向本站域名的链接不算)有出站链接,却没有一条指向权威主机(政府、教育、研究、主流新闻等清单)才 warn;完全没有出站链接=通过。
**不修的条件(caveat)**: 引用密度不是排名公式(不是每页都得挂 .gov),所以一般建议论断型内容配引用、叙事型内容不强求。但为凑权威链接硬引不相关来源,反而稀释主题相关度。
**修复(fix)**: 数据/论断处补一手来源链接(正常 follow);证据分级规范见 [geo-evidence.md](../../content/geo-evidence.md);死引用按 links-external-reachability 定期清理。
**关联(seealso)**: links-nofollow-external、eeat-disclaimers;[geo-evidence.md](../../content/geo-evidence.md)、[geo-evidence-bank.md](../../content/geo-evidence-bank.md)

### eeat-about-page
- 名称/类型: About 页缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn)
**这意味(what)**: 站点没有 About/About Us 页,或有但无实质组织信息。
**为什么(why)**: About 页告诉读者这个站是谁、凭什么可信。Google 的自评问题包括访客能否一眼看出内容由谁制作([有用内容文档](https://developers.google.com/search/docs/fundamentals/creating-helpful-content))。它也是 Organization 实体叙事(使命/团队/历史)的载体,与 Organization schema 互为表里。
**触发(trigger)**: 站内导航/页脚无可达的 About 页(URL 形态 /about、/about-us 等[路径词表待核])即 warn;crawl 模式全站判,单页审计按页脚链接判。
**不修的条件(caveat)**: About 页不是排名因素本身,然而它是信任链地基,所以一般建议全站必配。但纯内部工具无所谓;个人博客可用"关于我"页等价满足。
**修复(fix)**: 建 About 页:组织是谁/做什么/凭什么可信(团队/历史/认证);页脚全局链接;与 Organization schema 同源输出。
**关联(seealso)**: eeat-contact-page、eeat-editorial-policy;[knowledge-graph-guide.md](../knowledge-graph-guide.md)

### eeat-contact-page
- 名称/类型: 联系页缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn;email/电话/表单/地址至少其一)
**这意味(what)**: 站点没有联系页,或联系页没有任何可用通道(源表口径:email/电话/表单/地址至少其一)。
**为什么(why)**: 联系信息是读者判断站点是否真实存在的基本证据,电商/服务类尤甚。是否有法定披露义务因辖区而异,以法务意见为准(本套件无统一来源)。通道的真实可用性比数量重要,一个真实表单胜过四个死邮箱。
**触发(trigger)**: 站内无可达联系页,或联系页四类通道(email/电话/表单/地址)计数=0 即 warn。
**不修的条件(caveat)**: 联系页不影响常规排名,然而缺失在 YMYL/电商场景是信任硬伤,所以一般建议必配。但开源项目站用 GitHub issue 等单一通道替代是可接受形态。
**修复(fix)**: 建联系页(≥1 真实通道);页脚全局链接;电话/地址与 LocalBusiness/PostalAddress schema 同源(见 eeat-physical-address)。
**关联(seealso)**: eeat-about-page、eeat-physical-address;[knowledge-graph-guide.md](../knowledge-graph-guide.md)

### eeat-privacy-tos(家族条:privacy-policy+terms-of-service)
- 名称/类型: 隐私政策/服务条款链接缺失 —— warning · 优先级 low · 输出 WARN(源表各=warn:页脚隐私政策链接、页脚 ToS 链接)
**这意味(what)**: 页脚缺隐私政策或服务条款链接(两条同构:均为页脚法定页存在性检查,并作一条)。
**为什么(why)**: 两页是商业信任与合规的基建:收集个人数据或加载追踪脚本时,不少辖区要求公开隐私政策(因辖区而异,以法务意见为准;本套件无统一来源);ToS 划定内容与交易权责。对搜索引擎无已知直接作用。缺失还联动 legal-cookie-consent。
**触发(trigger)**: 页脚(或全站级导航)无 Privacy Policy / Terms of Service 链接即各 warn。
**不修的条件(caveat)**: 法定页本身不是排名因素,然而隐私政策缺失在多数辖区是合规缺口,所以一般建议全站配。但无 cookie 无收集的纯静态个人站可从简——从简不等于没有。
**修复(fix)**: 页脚模板级补两链接(勿逐页手写);隐私政策覆盖实际收集行为并与 CMP 配置一致(见 legal-cookie-consent)。
**关联(seealso)**: legal-cookie-consent、eeat-contact-page;[validation-guide.md](../validation-guide.md)

### eeat-physical-address(吸收 eeat-geo-meta)
- 名称/类型: 实体地址标记缺失 —— warning · 优先级 low · 输出 WARN(源表:physical-address warn,PostalAddress(Organization/LocalBusiness schema);geo-meta warn,有 local-business schema 的页也应设 geo meta 标签)
**这意味(what)**: Organization/LocalBusiness schema 没有 PostalAddress,或 LocalBusiness 页面缺 geo meta(geo.region/geo.position/ICBM)标签——源表把 geo meta 作为 local-business schema 的伴生要求。
**为什么(why)**: 地址是线下可信实体与本地相关度的双重信号:LocalBusiness 富结果与本地意图查询都吃地址数据;LocalBusiness 结构化数据里 Google 必填的是 name 与 address([文档](https://developers.google.com/search/docs/appearance/structured-data/local-business));geo meta 标签没有搜索引擎文档支持,是工具约定。单点标记不等于有效——NAP 跨载体一致才有价值(见 eeat-nap-consistency)。
**触发(trigger)**: 1) 页面有 Organization/LocalBusiness schema 但无 PostalAddress 即 warn;2) 页面有 LocalBusiness schema 但无 geo meta 标签即 warn(geo-meta 条)。
**不修的条件(caveat)**: 纯线上业务无实体地址是正当形态,PostalAddress 可只到城市/国家级;家庭办公地址公开与否是隐私取舍,可用 areaServed(服务区域)替代。但本地商户缺地址标记等于放弃本地搜索资格。
**修复(fix)**: Organization/LocalBusiness 挂 PostalAddress(streetAddress/postalCode/addressLocality/addressCountry);LocalBusiness 页补 geo.position(与 schema 的 geo 同源);模板见 [schema-templates.md](../schema-templates.md)。
**关联(seealso)**: eeat-nap-consistency、eeat-contact-page;[schema-templates.md](../schema-templates.md)、[knowledge-graph-guide.md](../knowledge-graph-guide.md)

### eeat-affiliate-disclosure
- 名称/类型: 联盟披露缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn;FTC 口径 "This post contains affiliate links.")
**这意味(what)**: 含联盟/付费推广链接的页面没有披露声明(FTC 要求的显式披露,如 "This post contains affiliate links.")。
**为什么(why)**: 链接层面,Google 要求付费链接用 rel=sponsored 或 nofollow([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable));法律层面,美国 FTC 的网红披露指南(针对社交媒体,原则同样适用于博客)要求披露实质性关联,披露要与推荐信息放在一起、难以错过;只放在关于页、帖子末尾或要点开才看到的位置容易被忽略([FTC](https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers),核对 2026-10-21)。
**触发(trigger)**: 1) 页面含联盟链接特征(amazon.*/tag=、/aff/、?aff_id= 等形态[特征表待核]);2) 无披露文本即 warn。
**不修的条件(caveat)**: 披露不影响链接本身的排名语义(那是 rel=sponsored 的职责),然而它是合规义务,所以一般建议凡有佣金链接必配。但自然外链与联盟链接要分清——无商业关系的推荐不需要披露。
**修复(fix)**: 联盟链接统一 rel="sponsored";页首/链接前置披露声明;模板级注入勿逐页手写。
**关联(seealso)**: links-nofollow-internal、eeat-disclaimers;[deprecated-signals.md](../deprecated-signals.md)

### eeat-disclaimers
- 名称/类型: YMYL 免责声明缺失 —— warning · 优先级 medium · 输出 WARN(源表 warn;医疗/财务/法律内容须有相应免责声明)
**这意味(what)**: YMYL 内容(医疗/财务/法律等)没有对应免责声明("本内容不构成医嘱/投资建议/法律意见")。
**为什么(why)**: 对健康、财务、安全等 YMYL 主题,Google 系统更重视体现强 E-E-A-T 的内容([有用内容文档](https://developers.google.com/search/docs/fundamentals/creating-helpful-content));判定开关见 eeat-ymyl-detection。免责声明框定内容的专业责任范围,本身不是排名因素。
**触发(trigger)**: 1) 页面被 YMYL 检测判为医疗/财务/法律类;2) 无对应免责声明文本即 warn(声明匹配词表[待核])。
**不修的条件(caveat)**: 免责声明不是免责金牌(内容质量仍是主体),所以一般建议声明+引用+作者资历三件套同配,单挂声明救不了薄内容。但非 YMYL 内容不需要泛化免责——全站挂"仅供参考"反而稀释。
**修复(fix)**: 按主题配医疗/财务/法律三类声明;放内容首屏或结论前;与 eeat-citations、eeat-author-expertise 构成 E-E-A-T 三角。
**关联(seealso)**: eeat-ymyl-detection、eeat-citations;[scoring-rubric.md](../scoring-rubric.md)

### eeat-editorial-policy
- 名称/类型: 编辑政策页缺失 —— warning · 优先级 low · 输出 WARN(源表 warn;内容标准/事实核查流程)
**这意味(what)**: 站点没有编辑政策页——内容来源标准、事实核查流程、更正机制的公开声明。
**为什么(why)**: "谁核查、怎么更正"让读者判断可信度,更正机制也让 dateModified 的更新可信。无搜索引擎直接依据,是加分项不是底线项,故 low。
**触发(trigger)**: 站内无编辑政策/内容标准/事实核查类页面(URL 与标题词表[待核])即 warn。
**不修的条件(caveat)**: 编辑政策对单人小站不是必需(署名+资历已覆盖信任链),所以一般建议内容团队 ≥2 人或新闻类站配。但为配而配的空政策页(无真实流程)不产生信任价值。
**修复(fix)**: 建编辑政策页:来源标准/核查流程/更正机制/作者资历要求;页脚或 About 页链接;与作者档案页互链。
**关联(seealso)**: eeat-about-page、eeat-content-dates;[content-patterns.md](../../content/content-patterns.md)

### eeat-trust-signals
- 名称/类型: 信任信号清单 —— opportunity · 优先级 insight · 输出 PASS(源表现行 pass only:只列出信号,永不扣分;少于 3 类时建议补充)
**这意味(what)**: 站点没有任何可验证的信任信号:用户评论、第三方认证、安全徽章、媒体报道引用。
**为什么(why)**: 第三方背书是信任的社会化证据;认证与媒体报道可写进 Organization schema(award/subjectOf)。信号要可验证:无链接的 logo 墙没有价值;虚假评论违反 Google 结构化数据指南([结构化数据通用指南](https://developers.google.com/search/docs/appearance/structured-data/sd-policies))。源表现行为 pass only:只列出信号,不扣分。
**触发(trigger)**: 源表现行永远通过,只列出已发现的信号类型(评论 schema、认证、安全徽章、媒体报道等);本套件口径:全站一类都没有时,人工提示补充,不记失败。
**不修的条件(caveat)**: 信任信号是加法不是底线,所以一般建议按业务形态选配(电商重评论,B2B 重认证与报道)。但伪造信号(假评论/未授权徽章)比没有更糟,是信任硬伤。
**修复(fix)**: 接真实评论系统(schema 配页面可见评分,可见性判定见 sd-rating-scope);认证挂权威来源链接;媒体报道用 subjectOf/citation 进 schema。
**关联(seealso)**: sd-rating-scope、eeat-author-expertise;[entity-signal-checklist.md](../entity-signal-checklist.md)

### eeat-ymyl-detection
- 名称/类型: YMYL 检测器 —— opportunity · 优先级 insight · 输出 INFO(源表 info;仅识别不扣分)
**这意味(what)**: 页面被识别为 YMYL(Your Money or Your Life)内容——健康/财务/安全/法律等直接影响读者重大利益的题材。
**为什么(why)**: 开关型规则:它不评价页面,只给 eeat-disclaimers 等下游规则供数。Google 对 YMYL 主题更重视强 E-E-A-T 内容([有用内容文档](https://developers.google.com/search/docs/fundamentals/creating-helpful-content))。输出它让站主知道哪些页面要按更严标准加固;拿不准即标 true。源表现行为 pass only,永不扣分。
**触发(trigger)**: 页面内容/主题命中 YMYL 题材词表(医疗/金融/法律/重大新闻等类目[词表口径待核])即 info,不扣分。
**不修的条件(caveat)**: YMYL 没有官方机器可读清单,词表判定必有边缘误差(健身食谱算不算健康类),所以 info 不扣分、人工复核定类。但漏判的代价(按普通标准处理 YMYL)大于误判,方向上从严。
**修复(fix)**: 无需修复——把 YMYL 页面清单交给 E-E-A-T 加固流程:作者资历/免责声明/权威引用三件套(见 eeat-disclaimers)。
**关联(seealso)**: eeat-disclaimers、eeat-author-expertise;[scoring-rubric.md](../scoring-rubric.md)

### eeat-nap-consistency ⛏
- 名称/类型: NAP 一致性 —— warning · 优先级 medium · 输出 WARN(源表 warn;仅 crawl 模式;同一组织名在整站爬取中只挂一个电话+地址,不同名=不同主体)
**这意味(what)**: 同一组织的名称/地址/电话(NAP)在整站爬取中不一致——同名组织出现多个电话/地址组合。
**为什么(why)**: 同一门店的名称、地址、电话在各处一致,是本地 SEO 的通行做法(行业经验,非 Google 文档条文);不一致会让同一门店像两家。源表判定边界照抄:同一组织名只挂一个电话+地址;不同名=不同主体。可见层与 schema 的 PostalAddress/telephone 要同源。
**触发(trigger)**: ⛏ 1) crawl 全站提取 NAP 三元组;2) 同名组织的电话或地址组合 >1 即 warn;3) 不同名不做归并判定。
**不修的条件(caveat)**: 合法场景:连锁多店(同名组织每店独立地址电话是真实业务形态[分型口径待核:命中后需人工确认是否连锁])、品牌更名过渡期新旧名并存。所以一般建议命中后人工核对再改。
**修复(fix)**: NAP 单一数据源(CMS 站点信息表)注入页脚/联系页/schema 三处;连锁站每店独立页+独立 NAP;先改可见层再同步 schema。
**关联(seealso)**: eeat-physical-address、sd-entity-consistency;[knowledge-graph-guide.md](../knowledge-graph-guide.md)、[entity-signal-checklist.md](../entity-signal-checklist.md)
