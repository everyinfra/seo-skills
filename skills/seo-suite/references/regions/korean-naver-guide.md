# 韩语区(Naver 生态)SEO/GEO 指南

> 建立于 2026-10-08。份额双口径:[StatCounter 韩国](https://gs.statcounter.com/search-engine-market-share/all/south-korea) 与韩国本土面板 InternetTrend(via [InterAd](https://www.interad.com/en/insights/korean-search-engine-market-share));AI Briefing 行为来自 [Naver 官方 PR](https://www.navercorp.com/en/media/pressReleasesDetail?seq=10034442) 与行业分析([Andgentic](https://andgentic.com/insights/what-is-naver-ai-briefing)、[The Egg](https://www.theegg.com/seo/korea/naver-ai-search-guide-what-marketers-need-to-know))。AI Briefing ~20% 覆盖率为行业报告,非 Naver 官方——引用时标注。
> 韩语区的核心事实:**Naver SERP 被自有垂直主导,AI Briefing 的引用几乎全部来自 Naver 自有生态**——自有官网之外,必须在 Naver 生态内建立存在。

## 一、引擎与 AI 格局(2026)——先看双口径

| 口径 | Google | Naver | 说明 |
|---|---|---|---|
| StatCounter(2025-09~2026-09) | 47.97% | 43.05% | 统计并列,Bing 4.84% |
| 韩国本土面板(InterAd/InternetTrend) | ~28–30% | **~63–64%** | Naver 移动端领先,Google 桌面/B2B 领先 |

**永远双口径引用**——测量方法分歧本身就是韩语区第一知识点。Daum ~2.9% 已边缘化;**Coupang 是事实上的商品搜索**(2026Q1 ~3,325 万 App 用户,全年龄段第一商务 App)。

AI 助手:ChatGPT 64.3% / Gemini 29.35% / Perplexity 3.55%(StatCounter chatbot KR);国产 **Wrtn(뤽튼)>500 万 MAU**(2026-08 成为韩国首个消费 AI 独角兽);Kakao 独立 Kanana App **2026-10-15 停服**、转向 KakaoTalk 内嵌。

Naver AI 轨迹(官方):CUE:(2023 试点)→ **AI Briefing**(2025-03,带引用摘要)→ **AI Tab**(2026,主搜索框内的代理式对话搜索)。

## 二、工具栈映射(Google → Naver)

| Google 系 | Naver 系 | 关键差异 |
|---|---|---|
| Search Console | **Search Advisor**(searchadvisor.naver.com) | meta/HTML 文件验证;URL 须与 canonical 协议**精确一致**;sitemap 同域且<10MB;RSS 提交+robots 收录请求加速爬取 |
| GA4 | Naver Analytics | 免费但社区评价低于 GA4(无 IP 排除);主要用于 Naver 生态流量 |
| Business Profile | **Naver Place(플레이스)** | 店名/描述关键词、评价、照片 |
| 自然内容 | **Naver Blog / Cafe / 지식iN** | C-Rank/D.I.A. 排序;外部博客仅经 robot 收录出现在 Blog 标签(官方 Help) |
| Ads | Power Link / Smart Block | 搜索意图 CPC / AI 推荐块 |
| 关键词 | **Naver DataLab** + Naver Ads 关键词工具 | DataLab 按年龄/性别/设备出趋势;searchad 出 PC/移动月度量 |

## 三、排名差异(相对 Google)

1. **C-Rank(创作者排名)给作者/博客打分**,不是页面:31 个话题领域内单一话题持续发文积累权威(Content/Context/Chain)。
2. **D.I.A.** 在 Naver 自有行为日志(CTR、停留、回访)上跑 ML——参与度驱动。
3. **SERP 结构**:首页被自有垂直+付费块主导;独立网站主要在"웹문서"(网页文档)区竞争,空间有限。
4. 外国站能排,但需要:韩语内容+Search Advisor 注册+现实预期;**商业查询实质上必须有 Naver Blog 存在**。
5. 无付费"博客登记"一说;外部博客可见性是 robot 收录后的算法结果(官方)。

## 四、GEO / AI 搜索(韩语)

- **AI Briefing 引用几乎全部来自 Naver 自有生态**(Blog/Cafe/지식iN/Premium Content)(Andgentic 行业分析)。行动含义:**韩语 GEO = Naver 生态 GEO 优先,自有站 GEO 其次**。
- Naver 发布过官方 AI Briefing 内容指南;Google 2026-05 也发了 AI 搜索指南——两份可对照使用。
- 广告已内嵌进 AI Briefing 文本(带"AD"标,行业报告)。
- 监控工具:LLMPulse(AI Briefing 追踪)、Apify Naver AI Overview API;或 top-20 关键词手工周检。
- 韩国助手是否引用外国站:无研究——**未证实**;合理推断(标注为推断):Naver AI Briefing 只引韩语/Naver 生态源;ChatGPT/Gemini/Wrtn 对韩语提示偏好韩语内容。
- **ChatGPT/Gemini 是唯一不依赖 Naver 资产就能赢的 AI 通道**——韩语提示词直接测自有站可见性。

## 五、实操与合规

- PIPA(개인정보보호법):无 SEO 专门规定;分析/再营销 cookie 需同意提示,GA4 等跨境传输需披露。
- 关键词:DataLab(趋势)+ Naver Ads 工具(量);电商另做 Coupang/Smart Store 排名(独立学科)。

## 六、GitHub 现状(2026-10 检索)

关键先例:[leopard627/fire-your-seo-agency](https://github.com/leopard627/fire-your-seo-agency)(707★,KR 市场 Claude skill,含 NEO=Naver 维度);[gunheeaug/web-seo-aeo-geo-google-naver-skill](https://github.com/gunheeaug/web-seo-aeo-geo-google-naver-skill)(41★);若干 0★ 蒸馏项目(JaceProgramming/naver-searchadvisor-expert 基于 55 份官方文档)。`korean geo skill` 检索 0 结果——Naver 工具化供给稀疏,真实空白。

## 七、韩语 AI 搜索就绪清单(14 项)

1. Search Advisor 注册+所有权验证(canonical URL 精确一致)。
2. sitemap(同域<10MB)+ RSS 提交;robots 收录请求。
3. Naver Blog 存在:单一话题聚焦(C-Rank 话题权威)+稳定发文节奏。
4. 内容对准韩国用户真实输入的查询(DataLab 验证),不是英文关键词的翻译。
5. Naver Cafe 种草覆盖社区验证型查询(제품 후기/가격 类)。
6. 지식iN(知识问答)覆盖问句型查询。
7. 本地业务:Naver Place 认领与优化(店名关键词/评价/照片)。
8. AI Briefing 可引用格式:问题式小节标题、表格/列表、显式事实与数字(按 Naver 官方指南)。
9. Blog 帖配原创图(Naver 奖励媒体丰富度;结构化帖更易被 AI Briefing 引)。
10. 品牌实体一致:Blog/지식iN/Cafe/Place/官网同一品牌名。
11. 自有站 ko-KR 原生内容(非机翻);双语站 hreflang 正确。
12. top-20 核心词的 AI Briefing 声量监控(手工或 LLMPulse/Apify)。
13. ChatGPT/Gemini 韩语提示可见性单独测(不依赖 Naver 资产的通道)。
14. 电商:Coupang/Smart Store 列表优化(韩国第二大"搜索"行为)。

## 未证实项(不得写成事实)

Daum 出售给 Upstage;Kakao"Ari"现状;韩国助手的国内外引用比例;AI Briefing 20% 覆盖(Naver 未官方确认)。
