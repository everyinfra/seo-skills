# Intake Checklists

## 通用 intake

- 目标域名 / 页面 URL
- 站点类型
- 目标国家 / 语言
- 核心目标关键词或主题
- 当前主要目标：排名 / 流量 / CTR / 转化 / AI 引用 / 监控
- 当前已知问题
- 近期是否改版、迁移、换模板、改 URL、改 CMS
- 有哪些数据：Search Console、GA4、排名工具、外链工具、日志、爬虫结果

## 目标市场 intake(多语言/全球站必答,2026-10-08 并入)

按命中的市场逐个过(细则见[多语言工作流](multilingual-workflow.md)市场总表):

- **俄语区**:Yandex.Webmaster 是否验证+区域已设?Metrica 是否安装(GA 因 152-ФЗ 不合规)?robots 对 `YandexAdditional` 的决策(允许=进 Neuro/Alice)?付费投放的 erid 标记?**Telegram 公开频道(镜像 SEO)与 VK 群是否运营?商业透明层(оферта/реквизиты 等 6 类法定页)齐吗?**
- **韩语区**:Search Advisor 是否注册+验证(canonical 精确;**robots.txt 无 5xx/HTML 陷阱——Yeti 5xx=全站封禁**)?og:image 三条件?IndexNow key 部署?연관채널 sameAs(치지직/당근 等韩域)?description ≤80 全角字且 og:description 一致?Naver Blog/Cafe/지식iN 存在吗(AI Briefing 只引 Naver 生态;**투트랙:生态内+自有域**)?有 AI 引用暴露敏感页要用 `nosourceinfo` 吗?电商是否做 Coupang?**收录验证窗口设 2–4 周(수집요청是优先级队列)**
- **日语区**:Bing WMT 是否验证(Bing 28–33% 份额)?**审计是否用全角阈值(title 32/desc 120/正文 300 全角字,勿套英文 60/160)?内容是否过「AI 臭」密度 lint?**MEO/本地:GBP+ステマ規制内口碑+投稿週 1 回?Qiita/Zenn 是否覆盖(技术品牌)?業界ポータル NAP 是否完全一致?
- **英文(协议层)**:agent-readiness 三件套是否要做——ARD(`ai-catalog.json`)/llms.txt/WebMCP?Cloudflare 托管 robots 是否检测(抓线上响应)?Lighthouse `AGENTIC_BROWSING` 跑过吗?
- **西语**:es-ES+es-419 结构决策?方言本地化(非机翻)?
- **葡语(巴西)**:pt-BR 原生词表?ChatGPT/LLM 可见性是否列入优先目标(全球最强采用市场)?
- **阿拉伯**:`dir="rtl"` 全链?MSA 骨架+方言层策略?
- **法语**:fr 变体分离(fr-FR/fr-CA/fr-BE)?魁北克 Bill 96 合规?
- **德语**:Sie/du 按国别定了?Consent Mode v2 是否影响测量计划?
- **印尼**:baku/gaul 双轨?移动优先(>82% 移动流量)?
- **长尾主流市场速查**(印地/意/土/越/泰/波兰/荷,详见多语言工作流长尾表):印地=Hinglish 三书写+hi-IN/en-IN 分开?意大利=it-CH 独立 locale?土耳其=Yandex 双引擎(~26%)?越南=有调/无调+Coc Cốc?泰国=分词验证?波兰=变音符保留?荷兰=nl-NL/nl-BE 分开?
- 逐市场分别评分还是只要一个总分?(本套件默认:逐市场分开)

## research intake

- 想抢哪些主题或词
- 是新市场还是已有市场扩展
- 主要竞争对手是谁
- 是做内容规划还是解释现有 SERP

## content intake

- 页面类型：博客、落地页、产品页、分类页、FAQ、比较页
- 主要 query / intent
- 是否已有初稿
- 目标是传统 SEO 还是 AI 引用，或两者都要

## technical intake

- 问题范围：单页、目录、整站
- 是否有 robots / sitemap / canonical / redirects / schema / CWV 证据
- 是否允许看代码、模板或渲染后 DOM
- 是否有近期技术改动

## monitoring intake

- 关注对象：关键词、页面、目录、整站、竞争对手
- 观察周期：日报、周报、月报
- 告警阈值：排名下降、流量下降、索引异常、外链流失等
- 是否需要 stakeholder-friendly 报告
