# 多语言 GEO 更新条目清单(对照 multilingual-workflow.md;2026-10-11 设计稿,2026-10-21 逐条核对)

> 建立于 2026-10-11,2026-10-21 重新核对每条证据。**性质:增改条目清单,不改正文**——每条给出接入节(对照 [multilingual-workflow.md](../overview/multilingual-workflow.md) 现有结构)、类型(新增/扩充/修正)、可直接粘贴的条目草案、证据标签与关联文件。主文件结构与既有编号不动;条目按"能进哪节"最小编粒度设计,避免重排。
> 证据标签(2026-10-21 重定义,原来的"【调研 2026-10】"只是笼统说"已验证",没有来源,已全部替换):**【一手】**=官方文档或论文原文;**【第三方研究】**=厂商或机构研究,写样本与日期;**【小样本测试】**=个人手工测试,不外推;**【假设】**=本套件的推断,尚无证据,需要自己用 citation_panel 验证;**【本套件口径】**=设计约定。
> 深度入口规则遵十一A:**分市场杠杆类条目以门户页(markets/*.md)为主入口,本文件只留一行索引**。

## The answer

对照 multilingual-workflow.md 现有十二节结构,本轮有 **9 项增改**。核对后证据强弱分明:

- **有第三方数据支撑**:U1 的前半(ChatGPT 对非英语提问约 43% 的后台搜索用英语,[Peec 2026-02](https://peec.ai/blog/chatgpt-searches-in-english-even-when-you-don-t));各引擎引用本语言源的比例差异大([Temso 2026-04](https://www.temso.ai/data/-Lost-in-Translation-How-AI-Models-Handle-Local-Language-Sources));U6 新闻源约占 AI 引用 9%([arXiv 2507.05301](https://arxiv.org/abs/2507.05301));U7 的两个半衰期数字。
- **只有小样本测试**:U2——Glenn Gabe 2025-12 的手工测试里,ChatGPT、Perplexity、Claude 常返回英文版 URL,Copilot 和 Google 系返回本语言版;作者自己说不知道这些引擎是否支持 hreflang。
- **仍是假设**:U1 的后半("英文版吸走本语言版的引用位")、U4 的"机翻腔降权"、U5 的"唯一可用源红利"。这三条保留为待验证假设,不当事实。
- **杠杆位(U3)**:四格里只有 Tistory 在 Naver 连关渠道清单里有本套件文件的记录;其余三格的原数字核对后已更正。

## 一、条目总览(按优先级)

| # | 条目 | 接入节 | 类型 | 证据强度 |
|---|---|---|---|---|
| U1 | 非英语提问的引用语言:各引擎差异大,ChatGPT 后台搜索常用英语 | 五(第 6 步扩充)+ 十 英文行 + 十一B 英文区红旗 | 新增 | 前半有第三方数据,后半假设 |
| U2 | hreflang 对 AI 引擎:Google/Bing 系有效,其余引擎未证实 | 五(第 2 步后新增警示)+ 九 坑 5 扩充 | 新增+修正 | 小样本测试 |
| U3 | 分市场杠杆表:Tistory/引用源空置/豆包头条/Habr | 十(表尾新增"杠杆位"行)+ 门户 ko/ja/zh/ru | 新增 | 各格不同,见表 |
| U4 | 翻译有效但批量机翻有风险(独家层不可翻译获得) | 九 坑 1 扩充 + 六 变体表补注 | 扩充 | 一手(垃圾政策)+假设 |
| U5 | 小语种红利:唯一可用源 > 反链 | 十(跨区原则新增第 28 条) | 新增 | 假设 |
| U6 | 新闻源仅占 AI 引用 ~9%,且集中在少数媒体 | 六(补预期管理行) | 新增 | 论文原文 |
| U7 | AI 引用半衰期 4.5 周(SSRN 综合)与 11 天(Profound)并记 | 十二 12.1/12.2 + 原则 3 补注 | 扩充 | 两份来源均已核 |
| U8 | 新工作流接线点(trend-jack/deep-research) | 六(变体表后补一行) | 新增 | 本套件口径 |
| U9 | hreflang-validation.md 联动修正登记 | 另单(technical/) | 登记 | — |

## 二、逐条草案

### U1 非英语提问的引用语言:各引擎差异大,ChatGPT 后台搜索常用英语

**接入**:①五、检查顺序第 6 步"逐引擎可见性"末尾追加一句;②十、独到方法索引英文行"fan-out 修饰词逆向(DevTools 提取)"后补半句;③十一B 英文区专项"红旗"末尾补一条。

**条目草案**:

> (五第 6 步追加)**非英语提问时,各引擎引用本语言源的比例差异很大,多语言站必须按引擎×语言分别测**:Temso 对 700 万条引用、4 个引擎、12 个国家的分析([Temso 2026-04](https://www.temso.ai/data/-Lost-in-Translation-How-AI-Models-Handle-Local-Language-Sources),厂商研究)显示,非英语提问下引用来源与提问同语言的比例为 Google AI 概览 85.4%、Microsoft Copilot 76.7%、ChatGPT 70.2%、Grok 51.7%(英语占比分别为 8.7%、15.4%、23.7%、39.6%)。ChatGPT 的后台搜索也偏英语:Peec AI 分析 1,000 万条以上 ChatGPT 提示,发现非英语提示的后台搜索有 43% 用英语([Peec 2026-02-12](https://peec.ai/blog/chatgpt-searches-in-english-even-when-you-don-t),厂商遥测)。测法:把提示和后台搜索词按语言拆成多份 `prompt,web_query` CSV,各自运行 `python3 scripts/fanout_analysis.py <文件.csv>`;`citation_panel.py` 按引擎×语言分报,不合并统计(同第 1 节逐语言评分纪律)。
>
> (十 英文行补)"fan-out 修饰词逆向(DevTools 提取)"→ 补:非英语市场的 fan-out 里混有英文改写词,诊断时单列。
>
> (十一B 英文区红旗补)【假设,待验证】多语言站里"英文版引用份额上升"可能是在占用本语言版的引用位。现有研究没有直接测过同一站点两个语言版本互相争夺引用位;先用 citation_panel 在同一批提问下分语言对照,再下结论。

**证据**:【第三方研究】Temso、Peec(均为厂商,方法见原文);引擎侧 fan-out 机制锚点=[geo-platform-differences.md](../content/geo-platform-differences.md)。"本语言版被英文版吞引用位"为【假设】。

### U2 hreflang 对 AI 引擎:Google/Bing 系有效,其余引擎未证实

**接入**:①五、检查顺序第 2 步"hreflang 八检"后新增第 2bis 警示条目;②九、常见坑第 5 条"hreflang 与 canonical 打架"扩充后半句。

**条目草案**:

> (五 2bis 新增)**hreflang 是写给 Google 的;不要假设其他 AI 引擎读它**。【一手】Google 的 hreflang 文档描述的是 Google 搜索的行为([Google 文档](https://developers.google.com/search/docs/specialty/international/localized-versions));Bing 的 Fabrice Canel 在 2020 年说过 hreflang「是比 content-language 弱得多的信号」([SERoundtable 2020-09-11](https://www.seroundtable.com/bing-hreflang-weak-signal-30099.html))。【小样本测试】Glenn Gabe 2025-12 在 Google 文档、Cloudflare 博客等多语言站上手工测试([GSQi 2025-12-01](https://www.gsqi.com/marketing-blog/ai-search-hreflang-multilingual-queries/)):Google 蓝色链接、AI 模式、Bing、Copilot 多数返回本语言版;ChatGPT、Perplexity、Claude 常返回美国英文版;Gemini 要追问来源后才给链接,给出的多为本语言版。作者原文写"我们不知道其他 AI 搜索平台是否支持 hreflang",并猜测不支持。因此:每个语言 URL 仍应有自己的外链、内容量和语言匹配度;hreflang 照常做,但不要拿它当 AI 引擎语言路由的依据。测法:用目标语言向各引擎提同一批问题,记录被引 URL 的语言版本(citation_panel 按引擎×语言分报)。
>
> (九 坑 5 扩充)"hreflang 与 canonical 打架——八检第 1/6 条是最常见失败点"→ 补:即使八检全过,也不能默认其他 AI 引擎会因此引用本语言版(见五 2bis)。

**证据**:上述链接。结论范围:截至 2025-12 的小样本手工测试,AI 引擎会改,按原则 3 的 6–12 个月半衰期复审。hreflang 技术细则锚点=[hreflang-validation.md](../technical/hreflang-validation.md)(另需联动修正,见 U9)。

### U3 分市场杠杆表(Tistory/引用源空置/豆包头条/Habr)

**接入**:十、独到方法索引表尾新增一行"杠杆位汇总"(主入口在门户页,遵守十一A 规则);四项分别补进 markets/ko.md、ja.md、zh.md、ru.md 对应节(门户页修正单)。

**条目草案**:

> (十 表尾新增行)**杠杆位(leverage slot)= 该市场"存在但未被本地竞争者填满"的引用通道**。2026-10-21 核对后的四格:
>
> | 市场 | 杠杆位 | 打法与已核事实 | 主入口 |
> |---|---|---|---|
> | 韩语区 | **Tistory 外域半边** | Tistory 在本套件 [naver-searchadvisor.md](../technical/naver-searchadvisor.md) 记录的 Naver 连关渠道(연관채널)可识别域名清单里;博客双轨(Naver Blog / 外域)的外域半边可落 Tistory。"AI 브리핑引用内容约 70% 是 UGC"出自 Nasmedia 2026-06-16 的标题,方法未读,只作方向([ko.md](../markets/ko.md)) | [markets/ko.md](../markets/ko.md) |
> | 日语区 | **被引域名高度分散** | LIFE 公司自测(2026-02-27 至 03-29,37 个关键词,9,891 条引用):1,843 个被引域名里只有 81 个(4.4%)被 4 个引擎全部引用;AI 推荐第 1 位约 45% 在 SEO 圈外,数据限某一业种的地域检索([ja.md](../markets/ja.md) 4.1 节)。含义:各引擎引用源重叠低,不能只盯 Google 排名;"引用源空置位"的说法无数据,已删 | [markets/ja.md](../markets/ja.md) |
> | 中文 | **豆包头条通道** | 新榜智汇监测:10 个统计行业的豆包引用第一全是抖音;抖音权重 2026-05 为 10.79%、2026-08 为 31.8%([zh.md](../markets/zh.md) 引新榜 2026-09-10、2026-10-08)。原稿的"96.9–97.7%"在套件任何文件里都找不到出处,已删。头条号是字节生态图文半边的通道,属【假设】 | [markets/zh.md](../markets/zh.md) |
> | 俄语区 | **Habr 长文** | [ru.md](../markets/ru.md) 记录 Дзен、Habr、VK 用于分发与品牌提及,属【本套件口径】,无官方排名效果声明。原稿的"进 Yandex/AI 引用底物"没有证据,已删 | [markets/ru.md](../markets/ru.md) |
>
> 杠杆位判据(可迁移到其余市场,【本套件口径】):①平台在该市场 AI 引用池内 ②本地竞争密度低 ③官方图谱或生态承认该域名。每季复核——杠杆位随本地竞争者填满而失效(断言半衰期纪律,原则 3)。

**证据**:Tistory=连关渠道清单(naver-searchadvisor.md);其余见表内链接。杠杆位框架=【本套件口径】。

### U4 翻译有效但批量机翻有风险(独家层不可翻译获得)

**接入**:①九、常见坑第 1 条"机翻直接上线"扩充;②六、变体表上方补一句。

**条目草案**:

> (九 坑 1 扩充)"机翻直接上线无人工审校——scaled-content-abuse 风险+转化率双输"→ 补全两分法:【一手】Google 垃圾政策把"通过自动化转换(含翻译)批量生成页面且对用户几乎没有价值"列入 Scaled content abuse([垃圾政策](https://developers.google.com/search/docs/essentials/spam-policies));同时,Google 文档说本地化版本只有在"正文未翻译"时才算重复页([本地化版本文档](https://developers.google.com/search/docs/specialty/international/localized-versions))。所以:事实框架翻译 + 人审 + 本地实质(第四节第 4 步)是合法形态。【假设】"过了人审的机翻腔在 AI 引用竞争中仍被降权"没有证据,按"待验证"处理;更稳的做法是每语言版产出自己的净新层(本地数据/本地引语/本地反例),这也是引用竞争里"信息增益"的要求。变体≠翻译件,与六"一套事实,多种变体"衔接。
>
> (六 补句)"权威页(最长)"行前补:各语言权威页共享**核实事实层**,但信息增益层(净新观点)逐语言独立产出。

**证据**:【一手】Google 垃圾政策、本地化版本文档(核对 2026-10-21);"机翻腔降权"为【假设】。既有锚点=九 坑 1 原文、六 变体表、五 第 4 步。

### U5 小语种红利:唯一可用源 > 反链(【假设】)

**接入**:十、跨区融合原则新增第 28 条(接在第 27 条"AIO 上线时间红利"后)。

**条目草案**:

> 28. **小语种红利:成为"唯一可用源"可能比堆反链更有效**【假设,待验证】:小语种引用池小而浅,一个该语言的原创数据页或深度页可能成为整池唯一可用源——此时引用份额取决于"存在且唯一"。**这是推断,没有直接的实验数据**;原稿用来佐证的"荷兰区一条权威 .nl 链>数百条进口链""法国 Vibe 22.9% unique 推荐"未能在本次核对中找到一手来源。执行:选题优先"该语言没有好答案"的查询(GSC regex 快照缺口诊断法);原创数据首发 + 该语言独家层(同 U4);测量用该语言独立 citation_panel 基线(不与英文版合并,同第 1 节纪律),一个季度后看这条假设是否成立。

**证据**:无一手来源;引用前先在目标语言上自测。`scripts/market_fit.py` 的输出会引用本条(见页尾"建议")。

### U6 新闻源仅占 AI 引用 ~9%,且集中在少数媒体

**接入**:六、内容策略节首段后补一行"时效内容的预期管理"。

**条目草案**:

> (六 补行)**时效内容的预期管理**:AI Search Arena 的数据(2.4 万场对话、6.5 万条回答、36.6 万条引用,来自 OpenAI、Perplexity、Google 三家的模型)显示,新闻源约占引用的 9%,且新闻引用集中在少数媒体([arXiv 2507.05301](https://arxiv.org/abs/2507.05301),单作者预印本,2025-07)。"集中"指新闻引用内部的份额(例:OpenAI 模型的新闻引用里 reuters.com 22.8%,见 [geo-evidence-bank.md](../content/geo-evidence-bank.md)),不是占全部引用。所以新闻型内容不是 AI 引用的主通道;做时效选题时,新闻位让给通讯社,自己做分析层和数据层。Google Discover 不受此数约束,两个漏斗分开管。决策管线见 [trend-jack-playbook.md](../../templates/content/trend-jack-playbook.md) 的 PIVOT 规则。

**证据**:【一手论文】摘要原文:"Among the over 366,000 citations … 9% reference news sources";"News citations concentrate heavily among a small number of outlets"(核对 2026-10-21)。Discover 口径=[discover-news-seo.md](../content/discover-news-seo.md)。

### U7 AI 引用半衰期:4.5 周与 11 天并记

**接入**:①十二、12.1 度量闭环"复测日期是工作的一部分"段补数值锚点;②12.2 刷新触发段的"8–12 周"节奏补依据;③原则 3"断言半衰期纪律"补一句区分。

**条目草案**:

> (12.1 补)**AI 引用半衰期两个口径,不选边**:①SSRN 7344201(Tandeep Sangra,2026-08-20)综合 Scrunch/Stacker 等多家数据,给出跨平台中位 4.5 周(ChatGPT 3.4 周、Perplexity 5.8 周);它是二手综合([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7344201))。②Profound 用 88.3 万个页面、7 个引擎、12 个月的数据,给出"页面在峰值后失去一半引用份额"的中位数 11 天([Profound](https://www.tryprofound.com/blog/the-half-life-of-an-ai-citation-is-11-days))。样本与"半衰期"定义不同。复测日历按短口径排(11 天 → 峰值后 2 周复测),刷新投入按长口径排(4.5 周 → 8–12 周分层)。多语言站按语言分池各排各的;小语种池的半衰期是否更短没有数据,本地实测后校准。
>
> (原则 3 补)区分两种半衰期:原则 3 管**信源偏好结论**的 6–12 个月失效(本套件口径);AI 引用本身的半衰期(上面两口径)管**内容运营节奏**(12.1/12.2)。

**证据**:【一手】SSRN 摘要与 Profound 博客原文(核对 2026-10-21);`citation_panel.py` 里 `OFFICIAL_MEDIAN_HALF_LIFE = 11` 取 Profound 口径。

### U8 新工作流接线点(trend-jack / deep-research)

**接入**:六、变体表后补一行(本清单与两份新文档的同轮入仓动作)。

**条目草案**:

> (六 补行)两份新工作流的分工:**时效热点变体**走 [trend-jack-playbook.md](../../templates/content/trend-jack-playbook.md)(四问闸门→GO/PIVOT/WATCH/DROP→48h 发布管线,逐市场出决策件);**深度层写作**走 [deep-research-protocol.md](../content/deep-research-protocol.md)(五轮检索+IGS 自检+引用纪律+反例标注)——权威页变体的"信息增益层"按该协议逐语言独立产出(同 U4 分界线)。

### U9 联动修正登记(不在本文件处理)

| 文件 | 需要的联动 | 性质 |
|---|---|---|
| [hreflang-validation.md](../technical/hreflang-validation.md) | 补一节"AI 引擎边界":hreflang 八检合格只保证 Google/Bing 侧;其他 AI 引擎是否读它未证实(见 U2);检查项加"该语言 citation_panel 基线是否独立建档" | 另单修正(U2 的技术侧) |
| [markets/ko.md](../markets/ko.md) | Tistory 外域半边打法(U3 第 1 格)展开:连关渠道清单引用 + 外域位与 Naver Blog 位的分工 | 门户页修正单 |
| [markets/ja.md](../markets/ja.md) | 被引域名分散的数字已在 ja.md 4.1 节;补"目标查询集采样记无引用源答案份额"的测量法(假设验证用) | 门户页修正单 |
| [markets/zh.md](../markets/zh.md) | 豆包头条通道已有(杠杆位节);确认只引新榜数字 | 已完成 |
| [markets/ru.md](../markets/ru.md) | Habr 长文:保持"分发与品牌提及,本套件口径"的现有表述 | 已完成 |
| [freshness-log](../overview/freshness-log-20261011.md) | 本清单落地后按 self-update-protocol 记录一轮 | 流程登记 |

## What could change this conclusion

- U1 的 Temso、Peec 数字来自厂商样本,方法和提示词集会影响比例;各引擎会改,按原则 3 的 6–12 个月半衰期复审。
- U2 来自一个人的小样本手工测试;若 OpenAI、Perplexity、Anthropic 公开说明读取 hreflang,本条降级。
- U3 杠杆位全部有时效:本地竞争者填满即失效;日语区的 4.4%、45% 来自一家公司的自测,口径单薄。
- U5、U4 的"机翻腔降权"是推断,验证前不要写进任何收益承诺。
- U7 两口径样本定义不同,小语种池的半衰期是纯假设。

## 检查清单

| 检查什么 | 怎么查 | 通过 / 失败 |
|---|---|---|
| 本语言版是否被各引擎引用 | 用目标语言向各引擎提同一批问题:`python3 scripts/citation_panel.py init --brand <品牌> --prompts-file <题库> --stage-mix`,逐引擎 `record`,再 `report` | 按引擎×语言分别有 mention coverage 与 citation share;不合并统计 |
| 被引 URL 的语言版本 | 在 `record` 的 CSV 里记被引 URL,统计其中英文版与本语言版的比例 | 本语言提问下被引 URL 为本语言版的比例有基线可对照 |
| fan-out 是否偏英语 | 每个语言一份 `prompt,web_query` CSV,运行 `python3 scripts/fanout_analysis.py <文件.csv>`,看后台搜索词里英文词比例 | 每个语言各出一份报告,不合并 |
| hreflang 在 Google 侧是否正确 | `python3 scripts/hreflang_cluster.py <各语言版本 URL…>` 验证互指簇,再按 [hreflang-validation.md](../technical/hreflang-validation.md) 八检 | 八检全过;但不据此推断 AI 引擎行为 |
| 引用复测节奏 | `python3 scripts/citation_panel.py decay --engine <引擎>` | 复测日历写进计划;按两口径(11 天 / 4.5 周)排 |
| 杠杆位复核 | 每季度重查 U3 表四格对应的市场数字 | 过期数字更新或删除 |

## Method Notes

- 对照基线:multilingual-workflow.md 当前结构(一 语言约定/二 市场总表/三 工具栈/四 语言与内容规范/五 检查顺序六步/六 内容策略变体表/七 关键词研究/八 合规/九 常见坑六条/十 独到方法索引+跨区原则 1–27/十一 本地社区索引+迁移矩阵/十一A 门户页/十一B 专项分析/十二 韩区度量与流水线)。本清单所有"接入节"按此编号,落地时若主文件结构已变,按锚点文字定位。
- 2026-10-21 复核记录:U1(Temso、Peec)、U2(Gabe、SERoundtable)、U6(arXiv)、U7(SSRN、Profound)的原文已打开核对;U3 中 ja/zh 数字对照套件门户页更正;U4 对照 Google 垃圾政策与本地化版本文档;U5 无来源,降级为假设。
- 落地顺序建议:U2+U1(影响所有多语言审计)→ U3/U4(新增打法)→ U5–U8(原则与接线)→ U9(门户页与技术文件另单)。每条落地后主文件头部"建于"行加"2026-10-XX 更新"并过 freshness.py;门户页修正单各自过 market_lint 相关口径。
- 本清单本身不入 references/(它是变更工单);若需留档,建议按 freshness-log 模式存 overview/ 并在 self-update-protocol 记录,或直接消化进主文件后废弃。
