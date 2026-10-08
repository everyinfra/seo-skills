# 日语区 SEO/GEO 指南

> 建立于 2026-10-08。份额来自 [StatCounter 日本](https://gs.statcounter.com/search-engine-market-share/all/japan)(2025-08~2026-09);AI 使用率来自 [CyberAgent GEO Lab](https://note.com/amour_llmo)(21.3%→37.0%);引用行为来自 Ahrefs(经 [Nikkei xTREND](https://xtrend.nikkei.com))、[SiTest](https://sitest.jp/blog/?p=35347)、[LLMOチェキ 120 万引用分析](https://prtimes.jp/main/html/rd/p/000000069.000177930.html)。**引擎份额随测量方法剧烈波动(见下),任何场合禁止只引一个数**。
> 日语区两个决定性事实:**Yahoo! Japan 用 Google 索引**(排 Google=排 Yahoo! 有机),**Bing 在日份额 28–33%**(其最强大型市场,喂 Copilot)——因此日语 SEO 的引擎面比多数市场宽。

## 一、引擎与 AI 格局(2026)

| 口径 | 数字 | 来源 |
|---|---|---|
| StatCounter(2025-08~2026-09) | Google 59.08% / **Bing 31.63%** / Yahoo! 7.58% | 行业 |
| 其他追踪器 | Google 59.7–63%、Bing 28–33% | 行业 |
| 调查法 | Google 73–75%、Yahoo! Japan ~14% | 行业(方法论差异大) |

- **Yahoo! Japan 有机结果由 Google 索引授权供给**(2010 起),无独立自然算法;差异在 SERP 界面、自有垂直(ニュース/知恵袋/ショッピング/オークション)与 AI 功能。
- AI 助手:ChatGPT 第一(AI 搜索使用率 ~37%)、**Gemini ~30%(年增 ~2.8 倍)**、Copilot ~17%(职场偏);Claude/Perplexity 各<4%。
- **AI 搜索使用率 21.3%(2025-05)→ 37.0%(2026-02)**(CyberAgent GEO Lab);Google AIO 2024-08 在日 GA;AI Mode 2025-09-09 宣布入日;**Search Console 上线「生成AIパフォーマンス」报告**;Itera(2026-07,1,459 日语查询):**AIO 出现于 76.9% 日语查询**。

## 二、工具与生态映射

- **关键词管线(日本标准流程)**:[ラッコキーワード](https://rakkokeyword.com/)(免费,拉 Google/YouTube/Amazon/Rakuten/Bing 建议词)挖候选 → Google KW Planner JP(免费仅区间值)/パスカル 验量 → SEMrush。
- **CMS:WordPress 占日本 CMS 82.9–83.2%**(全球~60%);はてなブログ 0.9%(长尾引用底物)。
- **本地=「MEO」**(日式术语,即 GBP 优化+Map Pack):评价生态是 Google Maps 口コミ vs 食べログ/ぐるなび 双轨;**ステマ規制(隐性营销规制,2023-10 生效)约束评价征集**——任何日本本地手册必须先过这条。
- 时敏事实(交付前复核):Yahoo!ロコ/LINE PLACE 已分别于 2024-03/2024-06 终止;继任 **Yahoo!プレイス 将于 2027-03-31 关闭**(新注册 2026-11-30 截止)。

## 三、内容语言惯例(日语)

- **文字数字数按体裁分层**(实测共识,非官方规则):一般 SEO 文 1,500–3,500 字;支柱指南 7,000–12,000;**MEO/本地页 500–1,200**;快讯 300–800。原则:匹配意图与 top-10 字数分布,不设固定数。
- 语域:商务网页默认です/ます 体;だ/である 用于学术/技术专栏——全站一致,并把敬语策略写进 AI 可抽取答案的规范(风格指引,无量化源)。
- CJK 机制(领域知识,用于审计):无词空格→形态学分析切词;全角/半角重复(ＳＥＯ/SEO、カタカナ 变体)需规范化;片假名转写变体倍增关键词面;标题按字符计(实务 ~30–35 日文字)。

## 四、GEO / AI 搜索(日语)

1. **ChatGPT 对日语国内查询也把 Reddit 引用排第一**(Ahrefs 2025-05~09,经 Nikkei xTREND);Perplexity 偏 Yahoo!知恵袋,并转向 Wikipedia JP+note.com(SiTest 2026)。
2. **Perplexity 用 Google 索引**→ 已在 Google 排上的日站天然获引:日语 GEO 的第一杠杆仍是经典 SEO 强度+一方数据。
3. **LLMOチェキ 120 万引用分析:公司自有站被用作证据时,出现在 AI 答案的概率约 7 倍;但 >95% 的 AI 答案证据来自第三方站**——日语 GEO 本质是第三方引用工程。
4. **Bing 不可选**(28–33% 份额喂 Copilot):索引与可爬性单独验证。
5. llms.txt 在日:企业站 6.4–6.8%(~9,000 站,2026-09 测;全球基线 10.13%);John Mueller(2025-06)明示无 AI 系统当前使用 llms.txt——**低成本对冲,不承诺引用**。
6. ChatGPT(受 Bing 索引影响)与 Gemini(30% 使用)引用池不同——分开监控。

## 五、生态引用源(优先建设清单)

Wikipedia JP、note.com、Yahoo!知恵袋、Reddit(即使日语查询)、Yahoo!ニュース pickup;技术品牌:**Qiita 与 Zenn 双维护**(Zenn 存久文档,Qiita 触达大但内容泄入 AIO 引发迁移讨论)。

## 六、GitHub 现状(2026-10 检索)

日本原生 SEO/GEO skill 生态极小但新鲜(多为 0–2★):[tai1mo/QooQ-Dot-blogger-template](https://github.com/tai1mo/QooQ-Dot-blogger-template)(明示 GEO 优化)、[incognito-54/utsushi](https://github.com/incognito-54/utsushi)(自有品牌在日 AI 答案出现观测)、[hiroshi57/geo-audit-tool](https://github.com/hiroshi57/geo-audit-tool)(引用似然诊断)、[SEO-SKILL/multi-engine-seo-audit](https://github.com/SEO-SKILL/multi-engine-seo-audit)(442 规则含 Yahoo!JAPAN locale;其份额数字与 StatCounter 矛盾,已标记)。注:liangdabiao/GEO-Content-Optimizer-Skill(205★)README 中未发现日本相关内容,勿引用为日语先例。

## 七、日语 AI 搜索就绪清单(14 项)

1. Google JP 有机 top-3(同时喂 Yahoo! Japan 与 Perplexity),双引擎验证。
2. Search Console「生成AIパフォーマンス」+ GA4 AI 助手渠道,建立 AI 流量基线。
3. Wikipedia JP 词条/提及覆盖实体定义查询;为编辑者备好带引用的一方来源。
4. 第三方引用面(note.com、知恵袋向问答、Reddit、行业媒体)——>95% AI 证据是第三方。
5. 技术品牌:Qiita AND Zenn 双平台维护。
6. FAQ/Article/Organization schema + 可引用的统计与定义块(可抽取事实更易被引)。
7. 关键词走 ラッコ→Planner 管线;全/半角与片假名变体归组。
8. 文字数按体裁分层(MEO 500–1,200 / 一般 1,500–3,500 / 支柱 7,000–12,000),从 top-10 分布推导。
9. 本地:GBP 完整度+ステマ規制范围内的口コミ;食べログ/ぐるなび 当平行引用源;Yahoo!プレイス 计入 2027-03 EOL。
10. です/ます 语域全站一致;AI 抽取答案的敬语策略成文。
11. llms.txt 作为对冲发布(6–7% 日企采用),不声称驱动引用。
12. ChatGPT 与 Gemini 的日语提示可见性分开手工抽查。
13. Bing 索引/可爬验证(28–33% 份额经 Copilot,非可选)。
14. 金融/医疗:JFSA 披露式合规内容(单源标记,待核)。

## 未证实项(不得写成事实)

liangdabiao"日语文体"说法;AMIMOTO 的当前地位;敬语对排名的量化影响;任何单一引擎份额口径。
