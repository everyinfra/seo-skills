# Changelog

以后内容或结构有变更时,提升版本号并增加一条带日期的记录。
Future content or structure changes must bump the version and add a dated entry.

## 0.5.0 - 2026-10-08

- **架构重构:市场成为一等维度(市场 × 能力双维度)**。SKILL.md:intake 市场先行(18 市场第一必答字段)、统一输出首行注市场、新增「市场维度」运行方式;capability-map 双维度结构+市场分层表(独立学科/ChatGPT 超强/方言分裂/合规驱动/基线);routing-rules 新增「第零步:先定市场」;统一各能力文件「市场差异」小节命名约定。
- **第一波长链路深挖(独立学科五市场,每市场单独 agent 母语挖掘)**:
  - **中文**:新增「生态内搜索速查」(搜一搜 Peoplerank/小红书 CES 互动分/抖音四因子/知乎引证与 2026-08"知乎修正"/豆包信源金字塔与 2–4 周验收窗/采样风控 ≤20 问);排行站免费申报通道(maigoo/CNPP 官方口径);新库:geo-book(一手实测)、AIGEOTOOLS(175★)、deepseek-geo(118★)、douyin-seo-playbook;
  - **英文**:协议层 agent-readiness(ARD 三级发现链/WebMCP/Web Bot Auth/Lighthouse AGENTIC_BROWSING);引用四级阶梯+recommended-against 暗级;ChatGPT 5.6 格式降权(listicle −50.5%);AIO 与 AI Mode 86% 引用不同源;Cloudflare 托管 robots 坑;fan-out 逆向;新库:marketingskills(53.7k★)、open-seo(22.7k★)、jdevalk/specification.website(874★)等 12 库;
  - **俄语区**:Telegram 公开镜像 SEO(t.me/s/ 被 Yandex 抓取,~90% 曝光来自 Yandex);Webmaster SoV 官方报告;Alisa RAG 五步+ЭПОС;商业透明层 6 类法定页;9 项官方违规+накрутка ПФ 红线;目录生态(Бизнес/2ГИС/Zoon/Flamp/Отзовик+TGStat);VK 群可排名;Horosheff 深读(行为代理 7 分制等 8 项新检查);
  - **韩语区**:`nosourceinfo`(全球唯一官方 AI 引用退出 meta);Yeti robots 语义四陷阱(5xx=全站封禁/host 隔离);연관채널 sameAs 实体图谱;AI 인용수 公开可侦察(메이트);웹문서/서비스内双通道;블로그 투트랙;官方 5 项引用标准+反模式;leopard627(707★)与 55 份官方文档蒸馏库深读;
  - **日语区**:全角阈值体系(title 32/desc 120/正文 300);「AI 臭」密度 lint(28 动词×14 构文);MEO 三因素×投稿週 1 回;2026-06 引用生态(note 第 2/新闻跌出/PR TIMES 特例/垂类>综合榜);卫星站终结论;業界ポータル NAP 一致;kseo/utsushi/seo-operator/hana652 深读([要追加]/[要確認] 占位符协议升为全区规范)。
- **主干新增「十八市场独到方法索引」**(第一波五行填实)+**跨区融合十原则**(封闭生态入口/SoV 计量观/断言半衰期/免费申报先行/行为代理审计/免责声明即 GEO 内容/密度检测/占位符协议/垂类媒体子表/互动分公式化)。
- monitoring/brand-mention 新增市场差异节(四级阶梯+各市场监控通道);backlink-directory 新增区域渠道节(中/俄/日+卫星站风险+链接红线);intake-checklists 四市场深化。
  Architecture: market becomes a first-class dimension (market × capability); Wave 1 deep-dives for the five independent-discipline markets (ZH/EN/RU/KR/JP), each with its own native-language agent.

## 0.4.1 - 2026-10-08

- **结构反馈落地:区域知识融入套件本体**。移除 0.4.0 的 `references/regions/` 独立专区(4 份指南),把内容并入五类能力文件——全球能力不再是一个模块,而是每个能力集合自带:
  - `overview/multilingual-workflow.md` 重写为**全球主干**:11 市场总表(格局/决定性事实/就绪闸门)、逐市场工具栈映射(俄/韩/日)、语言与内容规范(文字数按体裁、Sie/du、MSA/方言、baku/gaul、RTL、排版)、合规速查(152-ФЗ/erid、GDPR、LGPD、Bill 96、PIPA、ステマ規制);
  - `content/geo-platform-differences.md` 新增第六节**区域 AI 平台**(Alice/Neuro 取源规则、GigaChat 仅 App 内引用、Naver AI Briefing 只引自有生态、日语 AIO 76.9%、引用语言绑定 83–84%);
  - `technical/ai-crawler-policy.md` 新增第三节**区域引擎爬虫与收录**(YandexAdditional 唯一退出控制、Naver robots 收录、Bing 日本必做);
  - `technical/hreflang-validation.md` 修正规则五(**es-419 是 Google 接受的唯一 UN M.49 例外**)+ 新增 RTL 必检与常见市场码组合;
  - `research/keyword-intent-taxonomy.md` 新增**区域关键词研究差异**(Wordstat 算子、DataLab、ラッコ→Planner 管线、方言/语域/变体归组);
  - `overview/intake-checklists.md` 新增**目标市场 intake 闸门**(逐市场必答问题)。
- SKILL.md 路由改指向融入后的文件;README 双语同步("全球能力融在每个能力集合里")。
- **第二轮语区并入(18 市场全覆盖)**:印地(India,ChatGPT 第二大市场 ~1 亿周活;Hinglish 三种书写;hi-IN/en-IN 分开)、意大利(it-CH 独立 locale)、**土耳其(Yandex ~26%——俄语区之外第二个 Yandex 市场**,黏着语关键词形式)、越南(有调/无调变体+Coc Cốc ~6%)、泰国(无空格分词,密度工具失效)、波兰(变音符规范化)、荷兰(nl-NL/nl-BE 弗拉芒)——折入多语言工作流长尾市场表、爬虫政策(Yandex 土耳其/Coc Cốc)、hreflang 市场码组合、关键词区域表、intake 速查。
  Structural feedback: regional knowledge merged into the five capability files (regions/ section removed); multilingual-workflow rewritten as the global backbone; second round adds 7 more markets (18 total, incl. Turkish Yandex and Hindi/India).

## 0.4.0 - 2026-10-08

- **全球市场专区(regions/)**:新增 4 个区域指南,把套件从"中英双语"扩展为"全球 SEO/GEO 一把做,逐市场分开评分"——
  - **俄语区(Yandex 生态)**:平行工具栈映射(Webmaster/ИКС/Metrica/Wordstat/Business)、行为与商业排名因素、Королёв/Вега 算法、Alice AI 从自然 SERP 取源(经典 top-10 是引用前提)、YandexAdditional 唯一退出控制、llms.txt 在俄无消费证据、GigaChat 引用仅 App 内、152-ФЗ 与 ORD/erid 合规、15 项就绪清单;
  - **韩语区(Naver 生态)**:份额双口径(StatCounter 并列 vs 本土面板 63–64%)、Search Advisor 要点、C-Rank/D.I.A. 创作者排名、SERP 自有垂直主导、AI Briefing 几乎只引 Naver 生态(韩语 GEO=Naver 生态优先)、Coupang 商品搜索、Wrtn/ChatGPT 格局、14 项就绪清单;
  - **日语区**:Yahoo! Japan=Google 索引、Bing 在日 28–33%(喂 Copilot)、AIO 覆盖 76.9% 日语查询、LLMOチェキ >95% AI 证据来自第三方站、文字数按体裁分层(MEO 500–1,200/一般 1,500–3,500/支柱 7,000–12,000)、ステマ規制、Yahoo!プレイス 2027-03 EOL、14 项就绪清单;
  - **全球六市场(西·葡·阿·法·德·印尼)**:对照表(引擎份额/最大坑/hreflang)、es-419、pt-BR、RTL+MSA/方言分层(arXiv 同行评审:方言退化)、Bill 96、DACH Sie/du、baku/gaul 双轨、AI 引用语言绑定(西语 83–84%)、合规速查(GDPR/LGPD/Bill 96)。
  Four regional guides adding global market-by-market SEO/GEO in one pass: Russian (Yandex ecosystem), Korean (Naver ecosystem), Japanese, and a six-market comparative guide (Spanish/Portuguese/Arabic/French/German/Indonesian).
- **接线**:SKILL.md 新增「区域市场专区」路由与全球市场英文触发词(Yandex/Naver/MEO/es-419/pt-BR/RTL/Bill 96/Sie-du/baku-gaul 等);多语言工作流升级为全球市场路由表(九语区)+ 逐区可达性/es-419/逐引擎盲区;README 双语更新至 0.4.0 并新增全球市场数据表(均注明来源类型)。
- **修复**:消除 SKILL.md 中历史遗留的重复块(frontmatter/头部/整套路由规则各重复一次,475→260 行)。
- 所有事实按套件证据纪律标注来源类型(官方/行业/社区),未证实项在各文件末尾集中声明。

## 0.3.1 - 2026-10-09

- **多语言结构化**:SKILL.md 增加语言约定(输出随用户语言、多语言站逐版本评分)与英文触发词;新增《多语言工作流》参考(按市场路由、双语检查顺序、一套事实多种变体、中英阈值差异对照);README.en.md 更新至 v0.3 能力并加安装命令;README.md 同步。
  Multilingual structuring: language conventions in SKILL.md, new multilingual-workflow reference, EN README updated.
## 0.3.0 - 2026-10-09

- 第二轮新增 4 个参考资料:**中文 AI 搜索指南**(187,818 条引用实测:品牌官网仅占 1.37%、28 个排行站吃 9.1%、各引擎护城河、CJK 阈值、15 项就绪清单)、**程序化 SEO 闸门**(100/500 页硬闸、页型地板)、**SEO 漂移监控**(13 元素基线+17 规则)、**目录提交引擎**(九问闸门+13 层目录)。
  Round-2 additions: Chinese AI-search guide (measured citation economics from a 187,818-citation dataset), programmatic SEO gates, SEO drift monitoring, directory-submissions engine.
- 修复 0.2.0 中 SKILL.md 的 8 条死链;新增一行安装脚本 install.sh。
- 来源登记更新见 NOTICE。

## 0.2.0 - 2026-10-09

- 新增 8 个参考资料:外链画像分析(七段式框架+数据闸门)、外链渠道目录(分级+核验日期)、llms.txt 指南(格式+校验严重度)、AI 平台差异事实库(五引擎+爬虫分类)、可引用性打分(五维块级+就绪度分层)、AI 爬虫政策(引用型 vs 训练型 bot)、hreflang 八检、品牌提及监控(五平台加权+买家提示词集)。
  Eight new reference files: backlink profile analysis (7-section framework with a data-sufficiency gate), graded backlink directory with verification dates, llms.txt guide, AI platform differences fact base, citability scoring, AI crawler policy (citation vs training bots), hreflang 8-check validation, and brand-mention monitoring.
- 框架要点参考 AgriciDaniel/claude-seo、zubair-trzada/geo-seo-claude、jianruntech/geo-score、Auriti-Labs/geo-optimizer-skill、flaqai/backlink_skills、alvinunreal/awesome-submitlist、indie-hacking/Awesome-SEO-Backlinks、OranAi/orangeo(均在各文件末尾附来源)。借要点摘要与原文链接,见 NOTICE。
  Framework points borrowed (summary + link only, see NOTICE) from the repos above.

## 0.1.0 - 2026-09-29

首个公开版本 / Initial public release.

- 一个 Skill:`seo-suite`(SEO / GEO 统一工作台),含 overview、research、content、technical、monitoring 五类参考资料和 14 个输出模板。
  One Skill, `seo-suite` (SEO / GEO workbench), with reference notes for five capability sets and 14 output templates.
- 参考资料为 EveryInfra 自行编写;涉及第三方来源的文件只给要点摘要和原文链接,见 NOTICE。
  Reference notes are written by EveryInfra; where a third-party source is involved, only our summary and a link is given. See NOTICE.
