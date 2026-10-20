# Mercado Brasil(pt-BR 专项)

> 语言市场文件:巴西葡语。断言半衰期 6-12 个月。2026-10-21 逐条核对一手来源(StatCounter、Google 官方博客与 Search Central、Reclame Aqui 官方研究、Mercado Livre 官方帮助与 API、ANPD、Planalto);二手研究标「第三方研究」并写样本与日期。基线见 overview/multilingual-workflow.md 巴西段与 scripts/markets.json `pt` 键;本文件为市场深潜层,三处互为引用。写法约定见 [asd-ste100-web-writing](../content/asd-ste100-web-writing.md);标题与首段怎么对齐买家提问见 [question-alignment](../content/question-alignment.md)。

## 〇、快速诊断入口(陌生项目 60 分钟路径)

1. `site:dominio` 葡语页抽查:是否 Title Case?变音符号是否完整?是否混入 pt-PT 词汇?(→ 三)
2. 品牌词 SERP:Reclame Aqui 是否占位?评分与解决率是多少?(→ 2.1)
3. ChatGPT 关浏览三态测试;关浏览问「melhor [categoria] no Brasil」,看引用面。(→ 四)
4. 电商类:ML 信誉温度计、ficha técnica 完整度、标题结构。(→ 2.2)
5. robots 与 consent:同意前是否已加载广告类像素。(→ 六)
6. 基线记录:GSC 28 天、Bing WMT 桌面、RA 月检快照。

## 一、格局:Google 一极 + ChatGPT 单极 + AIO 已是常态

### 1.1 关键数据(2026-10-21 核对)

| 指标 | 数值 | 来源与口径 |
|---|---|---|
| Google 搜索份额 | **88.42%**(Bing 9.63%、Yahoo 1.54%),12 个月区间 85.88–91.68% | [StatCounter 巴西·搜索引擎·全设备](https://gs.statcounter.com/search-engine-market-share/all/brazil),2026-09 月值,取数 2026-10-21 |
| 桌面端 | Google 76.61%、Bing 19.86% | StatCounter BR 桌面,2026-09 月值 |
| 移动端 | Google 99.21%、Bing 0.25% | StatCounter BR 移动,2026-09 月值;12 个月区间 98.76–99.21% |
| ChatGPT 月活 | 约 5,400 万(超人口 25%) | 第三方研究:Atlantico《Latin America Digital Transformation Report 2025》(2025-07),经 [StartSe 2025-09-10](https://www.startse.com/artigos/o-proximo-vale-do-silicio-fala-portugues/) 转述,未读到报告原文;口径为 App 月活 |
| AI chatbot 站点访问份额 | ChatGPT 约 99%(2025-08 访问 3.1067 亿次) | 第三方研究:Cadastra×Similarweb,样本 100 个 AI chatbot 站点,经 [Meio & Mensagem 2025-11-13](https://www.meioemensagem.com.br/marketing/chatgpt-domina-mercado-de-inteligencia-artificial-no-brasil);口径是网站访问量,不是用户数 |
| AIO 出现率 | **86.8%**(按搜索量加权 90.2%) | 第三方研究:[SEONextbr](https://www.seonextbr.com.br/blog/estudo/estudo-ai-overviews-brasil/),2026-07,500 个关键词(5 行业各 100)、google.com.br、**桌面**、葡语 |
| 常用 AI 做购买研究 | 46.5%(日用 23%、周用 23.5%) | 第三方研究:Optimiza Marketing《Mapa da Busca no Brasil 2026》,n=1,000 消费者,经 [AdNews 2026-07-20](https://adnews.com.br/post/quase-metade-dos-brasileiros-usa-ia-para-pesquisar-e-decidir-compras-aponta-estudo) |
| AIO 上线 | 2024-08-15 宣布扩到巴西(含本地语言),数周内逐步推送 | [Google 官方博客](https://blog.google/products/search/new-ways-to-connect-to-the-web-with-ai-overviews/);2024-10-28 再扩 100+ 国并支持葡语等语言([官方博客](https://blog.google/products/search/ai-overviews-search-october-2024/)) |
| AI Mode 巴西葡语 | 2025-09-08(与印地语、印尼语、日语、韩语同批) | [Google 官方博客](https://blog.google/products-and-platforms/products/search/ai-mode-expands-more-languages/) |

### 1.2 解读与实操

- **无本地通用引擎**。解法是吃透 Google,再单独做 ChatGPT。
- **Bing 的份额几乎全在桌面**(19.86% 对 0.25%)。按桌面客群决定 Bing Webmaster 与 IndexNow 的投入;移动优先策略不受影响。
- **ChatGPT 访问量占 AI chatbot 站点的约 99%**。GEO 验证以 ChatGPT 为主,Gemini 与 Perplexity 为辅。Perplexity 在同一研究里排第二,2025-08 仅 201 万次访问。
- **AIO 在该样本里是常态**。样本是桌面端、5 个行业的 500 词,不能外推全站。SEONextbr 另有两条:第一名自然结果在 35.3% 的 AIO 里没被引用;AIO 平均引 9.7 个来源。报告必须分列「排名」与「被引用」。
- 同一研究里被引最多的域名是 youtube.com(65.4%)和 instagram.com(37.0%)。视频与社媒是引用面,不只是流量面。
- 季节:Black Friday、母亲节、13º salário(11–12 月)、IRPF(3–5 月)、Carnaval。内容提前 60–90 天备货(本套件口径)。

## 二、渠道:四条本地主干道

### 2.1 Reclame Aqui(RA)三重角色:AI 引用源 + 关键词语料 + 信任信号

**RA 自报规模**(RA 研究,经 [Veja 2026-07-27](https://veja.abril.com.br/economia/reputacao-passa-a-influenciar-ate-respostas-da-ia-e-muda-a-forma-como-brasileiros-escolhem-empresas/) 与 [RA 博客 2026-07-07](https://blog.reclameaqui.com.br/como-llms-decidem-confianca-marca-reclame-aqui/)):
- 2026 年上半年月均约 5.55 亿次 AI 引用;约 9.45 亿次 Google 曝光;2,200 万月独立用户;平均解决率 75%。
- 这是 RA 自己的统计,没有第三方审计。RA 博客写的口径略不同:曝光是「2025 年均值」,会话「4,000 万+」。引用时写「RA 自报」。
- RA 称 ChatGPT 与 Gemini 读取其公开历史(评分、解决指数、真实评价)。这是 RA 的说法,不是 OpenAI 或 Google 的说法。

**用户意图**(RA 研究,同上 Veja):64% 打算七天内买;86% 首次查这家公司;79% 说声誉直接影响决定;39% 来查是否骗局。

**第三方抽样**:Promptado 监测 30 个巴西品牌、32,369 段 AI 对话(2026-01-01 至 01-26)。ChatGPT 回答里 reclameaqui.com.br 出现 2,005 次、覆盖 21 个品牌,其中 22.3% 以显式引用形式出现([Promptado](https://blog.promptado.com/quais-sites-as-ias-mais-citam-ranking-de-fontes-janeiro-2026))。这个 22.3% 是「出现中被显式引用的比例」,不是「22.3% 的品牌回答引用 RA」。

**Black Friday 2026 研究**(RA 官网问卷,2026-08-21 至 08-26,n=2,161,95% 置信、误差 2%;[RA 博客 2026-10-08](https://blog.reclameaqui.com.br/ia-na-black-friday-pesquisa-2026/)):
- 购前查验入口:RA 与搜索引擎并列第一(各 55%),其后社媒 22%、朋友与网红 21%、AI 助手 19%。
- 87% 打算在 Black Friday 用 AI;任务是比规格型号(71%)和找优惠券与低价(44%)。
- 样本是 RA 站内访客,偏向本来就信 RA 的人。不要当全国代表性数据。

**SAC 即 GEO 的做法**:
1. 品牌词 SERP 审计查 RA 是否占位。
2. RA 企业页月检:响应速度、解决率、「voltaria a fazer negócio」指数。响应时限没有一手来源,按自己的 SLA 设。
3. 投诉语料反向挖关键词。
4. RA 称 2026 上半年被查最多的品牌含 Shopee、Mercado Livre、iFood、Caixa、Nubank、Amazon,可作竞品对照。

### 2.2 Mercado Livre(ML)信号

ML 官方文档能证实的:
1. **MercadoLíder 有搜索优先级**。[官方](https://vendedores.mercadolivre.com.br/nota/como-ser-um-mercadolider)写「anúncios vão ter prioridade e mais visibilidade nas buscas」。基础门槛(近三个月):有问题订单少于 1%、ML 介入调解的投诉少于 0.5%、取消少于 0.5%、发货错误少于 6%。
2. **ficha técnica 填全**。[官方](https://vendedores.mercadolivre.com.br/aprender/nota/dicas-avancadas-para-vender-no-mercado-livre)写填写准确的 ficha 能「aparecer mais nos filtros」并改善列表位置。
3. **标题上限 60 字符**。[ML 公开 API](https://api.mercadolibre.com/categories/MLB1055) 的类目 `settings.max_title_length` 为 60(取数 2026-10-21,以 MLB1055 为例)。
4. **标题结构**:官方写「produto + marca + modelo + 少量规格」。官方还写:不要把颜色、尺寸、免运费、分期、促销写进标题([官方](https://vendedores.mercadolivre.com.br/nota/como-criar-um-titulo-atrativo))。旧稿把颜色与规格塞标题的做法与此冲突。

本套件口径(ML 官方未给权重):Full 物流、库存健康、转化率会影响曝光。把它们当待测假设,用自己店铺的数据验证。「Perguntas 响应速度是排名因子」与「47% 消费者发现始于 marketplace」两条找不到一手来源,已删除。照抄竞品标题有重复内容风险(本套件口径)。

### 2.3 Instagram 与 Social SEO

- 个人资料姓名字段放关键词,命中 IG 站内搜索(从业者做法,Instagram 官方未给排名文档)。
- Instagram 与 YouTube 是 Google AIO 在巴西的高频引用源(见 1.2)。alt 文本、字幕、话题词要写完整。
- 「评论关键词自动发 DM」漏斗用第三方自动化或平台自带功能。旧稿说「Meta 已出免费原生版」,找不到官方公告,已删除。用任何自动化前先读 Meta 平台条款。

### 2.4 WhatsApp 发现层

- Meta 于 2025-06-16 宣布 Updates 页的 Status 广告、推广频道与频道订阅([about.fb.com](https://about.fb.com/news/2025/06/helping-you-find-more-channels-businesses-on-whatsapp/))。该公告没有按国家列出巴西上线时间,上线范围以 WhatsApp Business 后台为准。
- 链接预览用 OG 标签。先用 Meta 的分享调试工具确认卡片,再发链接(本套件口径;预览缓存时长没有官方数字)。
- 转化闭环常在 WhatsApp 或 IG DM 内完成。落地页的任务是给出可截图的信任凭证:价格、支付方式、CNPJ。

## 三、语言机制(AO90 / 标题大小写 / você)

### 3.1 AO90 正字法

- AO90 即 1990 年《葡萄牙语正字法协议》。巴西 2008-09-29 颁布(Decreto 6.583),过渡期 2009-01-01 至 2015-12-31,**2016-01-01 起强制**(Decreto 7.875,2012-12-27;[Migalhas 转载法令原文](https://www.migalhas.com.br/quentes/170196/decreto-altera-obrigatoriedade-do-acordo-ortografico-para-2016))。
- 变化举例:ação(旧 acção)、ótimo(旧 óptimo)、取消 trema(Base XIV,旧 freqüência)。
- **纠错**:旧稿写「fato←facto」。AO90 官方说明把 facto/fato、receção/recepção 列为**允许两种写法**的「dupla grafia」:葡萄牙写 facto,巴西写 fato([葡萄牙科学院《AO90 说明》第 4 节,原文举 facto/receção 对 fato/recepção](https://vocabulario.acad-ciencias.pt/index.php/ortografia/nota-explicativa-do-ao90))。所以 fato 与 facto 是国别差异,不是新旧拼法。
- 操作:面向巴西的页面用巴西写法。新旧拼法先用 Google Trends(地区 BR)比较再决定要不要在关键词层兼收;标题与正文只用现行拼法。

### 3.2 标题大小写

- 新闻标题惯例是**句首大写,专有名词大写**。例:[Estadão 手册](https://www.estadao.com.br/manualredacao/esclareca/t.php)规定标题用小写体(caixa-baixa)。
- 书名与作品名有另外的约定,可能用 Title Case(例:《Um Bonde Chamado Desejo》)。网页标题按新闻与网站惯例做句首大写。
- 英文式 Title Case 在葡语网页上读起来像翻译腔(本套件口径;有无「AI 痕迹」没有一手研究,不作为 AI 检测依据)。
- 全大写标题降低可读性(通用排版常识)。
- 专有名词照常大写:Google Ads、Black Friday、Reclame Aqui。

```
✅ Guia completo de SEO para o mercado brasileiro em 2026
❌ Guia Completo de SEO Para O Mercado Brasileiro Em 2026   ← Title Case
❌ GUIA COMPLETO DE SEO PARA O MERCADO BRASILEIRO           ← 全大写
✅ 5 formas de aumentar o tráfego orgânico (sem pagar anúncios)
❌ 5 Formas De Aumentar O Tráfego Orgânico
```

- 反 AI 文风(本套件口径):少用破折号(—)、少用「mergulhe no mundo de...」式开场、段尾不加总结句。用密度检测,不用单次出现判错。

### 3.3 人称与语域

- 全站统一 **você**(B2B 也一样)。不混 tu(tu 主要在部分南方口语区)。
- **a gente**(=nós)是高频口语,关键词层要收。
- pt-PT 用词不同:tu/você 分层;comboio(巴西 trem)、equipa(time)、telemóvel(celular)、bicha(fila)。不要把 pt-PT 站冒充 pt-BR。
- hreflang:巴西版标 **pt-BR**;同时有葡萄牙版时另标 **pt-PT**。Google 只认 ISO 639-1 语言码加可选 ISO 3166-1 Alpha-2 区域码,大小写不敏感([Google 多语言文档](https://developers.google.com/search/docs/specialty/international/localized-versions),核对 2026-10-21)。旧稿「裸 pt 会与 pt-PT 归并错杀」没有官方依据,已删除;裸 `pt` 是合法码,只表示语言。

### 3.4 格式与编码

- 变音符号写全(ã ç é ê)。charset 用 UTF-8。
- 数字、货币、日期、电话。[CLDR](https://github.com/unicode-org/cldr-json)(`pt` 区域,取数 2026-10-21):小数点为逗号,千分位为点,货币格式 `¤ #,##0.00`,所以写「R$ 1.234,56」。日期 dd/MM/aaaa,例 09/10/2026。电话 +55 加 DDD。
- 葡萄牙(`pt-PT`)的千分位是不换行空格,和巴西不同。
- 关键词不要直译。巴西用户搜口语、错拼、英葡混用。国际关键词工具对巴西的量估计不准,优先用本土数据源(见七)。

## 四、AI-GEO 要点

- **AI 是研究层,不是决策层**(RA 研究,2026-08):仅 15% 接受让 AI 选店,仅 4% 不核实就跟随。GEO 目标是进入对比清单,信任另建。
- **声誉一票否决**:64% 发现 RA 声誉差就放弃 AI 推荐。其他放弃理由:价格过低 43%、导向陌生站点 38%、**只收 PIX 或 boleto 31%**。Pix 本身是信任资产,「只能 Pix 或 boleto」才报警。多种支付并列更可信。
- **骗局恐惧**:88% 很怕 AI 生成的骗局,63% 自认分辨不了,32% 已遇到。页脚放 CNPJ、执业编号(OAB、CRM 等)可验证凭证。
- **Conversion《Tendências de SEO 2026》**:报告需注册下载([入口](https://www.conversion.com.br/estudos-e-pesquisas/tendencias-de-seo)),本次未读到全文,旧稿列出的「16 条」未核,已删。
- **引用面优先级**(本套件口径,依据 1.2 与 Promptado 抽样):YouTube/Instagram、Reclame Aqui、Wikipedia(pt)、gov.br、本地垂直媒体。外链权威优先在巴西本地生态里建。
- GEO 检查见「上线检查清单」。

## 五、信息源

- **Conversion《Guia de SEO》**:巴西 SEO 圈常引的年更指南;Tendências 报告免费下载但需注册。
- **SEO Happy Hour**(播客与博客)、**MestreCast**(营销科技)。
- **Reclame Aqui 官方博客**:消费者信任与 AI 行为的一手数据,Black Friday 年度研究每年追。
- **SEONextbr / Optimiza Marketing** 的巴西搜索报告。**Google 官方博客 pt-BR**。Veja、Meio & Mensagem 做交叉验证。

## 六、红旗(必拒/必修)

- **互惠链接**:Google 垃圾政策列的是「Fazer muitas trocas de links」,即**过量**互换([Spam policies,pt-BR,更新 2026-09-16](https://developers.google.com/search/docs/essentials/spam-policies?hl=pt-br))。政策没给数量阈值。本套件口径:审计时逐条查对端回链,环形互链按风险处理。
- **买链与 publieditorial**:同一页明文列出「Pagar por links ou postagens que contêm links」与「Publieditoriais ou publicidade nativa em que o pagamento é recebido por artigos com links aprovados」。页面同时写明:买卖链接是常见广告做法,链接标 `rel="nofollow"` 或 `rel="sponsored"` 时不违反政策([qualify outbound links,pt-BR,更新 2026-03-08](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links?hl=pt-br),写「o ideal é que seja usado sponsored」)。做法:付费位置一律标 `rel="sponsored"`,加明确广告披露,不做关键词锚文本堆砌。把「买门户包」当 link building 卖,等于买排名链接。旧稿的价带与「~10 天交付」类供应商宣传已删除。巴西广告合规另受 CONAR 约束(CONAR 守则,本次未逐条核)。
- **翻译不等于本地化**:直译关键词会全错(见 3.4)。
- **点击后信任差**:支付页没有 Pix/boleto/parcelamento、没有 CNPJ,转化会在可信度确认处流失。
- **LGPD(Lei 13.709/2018)**:适用范围见第 3 条:在巴西境内的处理、向巴西境内个人提供商品或服务、或数据在巴西境内收集,与企业所在国无关([Planalto 法条原文](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm))。法律于 2020-09 全面生效,罚则(第 52–54 条)自 2021-08-01 起生效(第 65 条)。**同意不是唯一合法依据**:ANPD《Cookies e Proteção de Dados Pessoais》(2022-10)写明各法律依据之间无优先级;非必要 cookie(如广告、画像)适合用同意;严格必要 cookie 不适合用同意;仅为聚合统计的受众测量 cookie,在限定条件下可以用合法利益(guide 示例 4,数据聚合、不共享、不与其他库交叉、告知并可反对)。**旧稿「分析类 cookie 一律需 opt-in」与 ANPD 不符**。做法:广告与跨站画像类像素在同意前不触发;分析类按你选的法律依据写进隐私政策并提供反对渠道。ANPD 指南原文:[PDF](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia-orientativo-cookies-e-protecao-de-dados-pessoais.pdf)。
- **虚构数据或锚文本比例是红线**:交付只给可验证的值。

### 常见误判

| 误判 | 实际 |
|---|---|
| 「Bing 9.6% 值得均衡投入」 | 移动端 99.21% 是 Google,Bing 份额在桌面(19.86%)。按客群设备结构决策 |
| 「ChatGPT 之外还要平摊 Gemini/Copilot」 | ChatGPT 占 AI chatbot 站点访问约 99%,单极验证优先 |
| 「Pix 是信任银弹」 | Pix 是信任资产,但「只收 Pix 或 boleto」被 31% 受访者当作放弃理由 |
| 「RA 只是售后问题」 | RA 与搜索引擎并列为购前首选查验入口(各 55%,RA 站内样本) |
| 「AIO 只影响信息类查询」 | SEONextbr 的 5 行业样本里电商/零售 88% 出 AIO |
| 「买一个门户包就是 link building」 | 付费位置须 `rel="sponsored"` 并披露;按 portal 逐个评估 |

## 七、ferramentas

| 工具 | 用途 | 备注 |
|---|---|---|
| SEONextbr | 巴西本土关键词、排名、技术审计、GEO | 国际工具对巴西量估计会失真;86.8% AIO 数据出处 |
| QMix Digital | 供应商宣传称有链接与 guest post 网络 | 不作为推荐。买链须按 `rel="sponsored"` 处理(见六);供应商宣传的门户数量与交付时间未核 |
| O2 Organic | Share of Search(免费) | 品牌搜索份额对比竞品 |
| Google Trends BR | 季节曲线、拼写新旧写法比较 | 关键词决策前置(地区 BR) |
| GSC + Bing WMT | 双引擎基线 | Bing 仅桌面有意义 |

(旧稿「Fastwork」一行已删:找不到稳定产品页。)

---
**验证协议**:①ChatGPT 关浏览问品牌三态,季度重测;②RA 品牌页月检;③ML 温度计与 ficha 完整度周检;④AIO 出现率按 SEONextbr 口径(桌面、同一词表)年度复测。

## 上线检查清单

| # | 检查什么 | 怎么查 | 通过/失败判据 |
|---|---|---|---|
| 1 | hreflang 互指 | `python3 scripts/hreflang_cluster.py <pt-BR URL> <pt-PT URL> <en URL>` | 每对页面互指;码合法(pt-BR、pt-PT);Google 规则:互指缺失则该对标注被忽略([Google 文档](https://developers.google.com/search/docs/specialty/international/localized-versions)) |
| 2 | 头部元素 | `python3 scripts/head_check.py <URL> --market pt` | 无 ERROR 级;twitter:* 与 OG 重复只记 INFO |
| 3 | title/description 长度 | `python3 scripts/site_audit.py <URL> --market pt --json` | 本套件口径:title ≤60、description 77–155 字符(Google 无固定上限,按显示宽度截断) |
| 4 | 市场 lint | `python3 scripts/market_lint.py --market pt <html文件> --url <URL> --report` | CRITICAL=0;AUTO-FAIL=0;MANUAL 项人工过一遍(CNPJ、PIX 文案、软文披露) |
| 5 | 数字、货币、电话 | `python3 scripts/local_format.py --market pt "<页面样本文本>"` | 全部 ✓(R$ 1.234,56;+55) |
| 6 | AI 检索爬虫放行 | `python3 scripts/robots_posture.py https://<域名>/robots.txt --signal visibility` | 搜索类与用户类爬虫 allowed;训练类封禁不扣分 |
| 7 | llms.txt | `python3 scripts/llmstxt.py check https://<域名>` | 有无都可;存在时 `validate` 通过(llms.txt 对排名无官方效果,见 content/geo-evidence.md) |
| 8 | 标题大小写 | 抽 20 个 title/H1/H2 人工看 | 无 Title Case、无全大写(专有名词除外) |
| 9 | 拼写 | Google Trends(地区 BR)比较新旧写法 | 记录兼收决策;页面只用现行拼法 |
| 10 | LGPD 同意前触发 | 浏览器无痕窗口打开页面,不点同意,看 Network 面板 | 广告与跨站像素请求为 0;分析类请求有对应隐私政策依据 |
| 11 | RA 占位 | 搜品牌名 + `reclame aqui`;打开 RA 企业页 | 记录评分、解决率、回复时长;每月一次 |
| 12 | ChatGPT 三态测试 | 关浏览问 5–10 个品牌问题 | 每问记「不知道/知道但错/知道且对」;季度对比 |
| 13 | ML listing | 标题 ≤60 字符、无颜色/尺寸/运费/促销词;ficha 全填 | 官方 API `max_title_length`=60;ficha 空字段=0 |

## 本地实测(2026-10-09)

### 真实站验证(g1.globo.com / uol.com.br × site_audit + llmstxt check + head_check)

> 脚本口径 2026-10-21 已改:twitter:* 与 OG 重复只记 INFO;缺 H1/描述为 WARN。下面的 ERROR/CRITICAL 数是旧口径结果,复测会不同。

- `site_audit --market pt`:g1 — title 34/60 ✓、**desc 195/155 超限 +40**、677 链接、跳级 h1→h3、robots.txt 四个 AI 检索爬虫全放行;uol — title 25/60 ✓、desc 153/155 ✓、448 链接、**robots.txt 禁 Claude-SearchBot 与 PerplexityBot(2/4;ChatGPT 系放行)**。
- `llmstxt check`:两站均无 llms.txt(四路径真 404)。
- `head_check`(旧口径):g1 — 5 ERROR(x-ua-compatible、fb:app_id、twitter:*);uol — 7 ERROR(skype_toolbar、x-ua-compatible、fb:app_id、twitter:* 四条)。charset 均达标,og:image 绝对 URL ✓。
- `market_lint --market pt`:desc 超限 CRITICAL 复现(195/155);句长拆分对门户跑马灯误报(最长「句」1,278 词,人工排除)。pt 的 special_checks 当日为 9/9 MANUAL;2026-10-21 复跑 `--report` 为 AUTO 2/9(「仅收 PIX/boleto」与「publieditorial 披露」两项已接线),其余 7 项仍须人工。
- **结构性观察(单次快照)**:g1 全放行、uol 禁 2/4。同日欧陆头部(lefigaro、spiegel)封 3/4,海湾 aljazeera 封 2/4。两站不足以推出「巴西头部最开放」,只能说这次抽到的两站没有封 ChatGPT 系。

## 维护

- 复审周期 **90 天**,下一次 **2027-01-09**(以 `scripts/markets.json` 的 `markets.pt.review_cycle` 为准)。
- 触发即复审:StatCounter BR 月度份额漂移、Conversion 年更报告、RA 官方研究与 Black Friday 年度报告、SEONextbr/Optimiza 报告、Google 官方博客 pt-BR、ANPD 动态。
- RA 研究数字随年度研究刷新,勿跨年沿用。
- 门户 robots 姿态是当日快照,复审时重跑 `robots_posture.py`。

## 建议(需要别处配合,本文件不改)

| 键路径 | 现值 | 应改值 | 来源 |
|---|---|---|---|
| `scripts/markets.json` → `markets.pt.notes` | 「ChatGPT 最强市场(25.5% 人口,~5,000 万月用户)」 | 「ChatGPT 约 5,400 万月活(Atlantico 2025-07,第三方转述)」 | StartSe 2025-09-10 转述 Atlantico |
| `markets.pt.special_checks[0]` | 「Reclame Aqui 品牌词占位必查(22.3% ChatGPT 被引)」 | 去掉括号数字,或改「Promptado 抽样:RA 出现中 22.3% 为显式引用」 | Promptado 2026-01 |
| `markets.pt.special_checks[3]` | 「troca de links 环形链检查(无安全阈值,改三角链)」 | 「互惠链接逐条查对端回链(Google 只列过量互换)」 | Google spam policies pt-BR |
| `markets.pt.special_checks[4]` | 「ML listing 60 字符标题+…投诉率<1% 门槛」 | 「标题≤60 字符(官方 API),不写颜色/运费/促销;MercadoLíder 有问题订单<1%」 | ML 官方帮助 |
| `markets.pt.special_checks[8]` | 「ML 六信号:Full/ficha100%/60字/断货即掉/投诉<1%/CVR」 | 官方可证的只有 ficha、标题 60 字符、信誉门槛;Full/库存/CVR 标「待测假设」 | ML 官方帮助 |
| `markets.pt.special_checks[5]` | 「AIO 86.8%:排名 vs 被引用分列」 | 加口径「桌面、500 词、2026-07」 | SEONextbr |
| `markets.pt.review_cycle.signals[3]` | 「SEONextbr/Optimiza 报告(AIO 86.8% 口径复测)」 | 保留,加「桌面口径」 | SEONextbr |
| `markets.pt.review_cycle.signals[4]` | 「LGPD/CNPCD 执法动态」 | 「LGPD/ANPD 执法与指南动态」 | ANPD 是监管机构 |
