# Mercado Hispanohablante(西语市场:es-ES + es-419 深度参考)

> 建立于 2026-10-09(R6 语言专项轮)。
> 数据源:套件既有知识(`overview/multilingual-workflow.md` 西语区段)+ 2026-10 西语原生检索增量研究(SEO México 2026 / SEO España 2026 趋势、Mercado Libre 算法 2026、西班牙 AI 引用格局、WhatsApp 商务统计、西语外链价带报价)。
> 断言半衰期 6-12 个月,随复审更新。配套数据层:`scripts/markets.json` 的 `markets.es` 键(本文件不改 json)。

## 一、格局:一种语言,两个宏观市场(加一块 es-US)

### 1.1 引擎份额与市场结构

- **搜索引擎**:Google 88–94%(es-ES 与 es-419 一致),无本地引擎;Bing 残余份额喂 Copilot,不单独投入。
- 与日/韩/俄不同——西语**不是"独立学科"市场**:无自有引擎生态,差异全在**语言变体与渠道结构**。
- **市场切分**:
  - 西班牙 es-ES(~4,800 万人口,欧元区,高价带 B2B 成熟);
  - 拉美 es-419(~20 国,墨西哥最大 ~1.3 亿;阿根廷/智利高客单,哥伦比亚/秘鲁增长带);
  - es-US(4,000 万+ 西语人口,搜索行为见 1.3)。
- **hreflang 决策**:`es-419` 是 Google 接受的**唯一 UN 区域码**——拉美全域用 `es-419` 覆盖,国别码(es-MX/es-AR/es-CO…)按投入深度细化;裸 `es` 兜底 + `es-ES`/`es-419` 双主档是最小正确集。
- 全套建议码:`es` / `es-ES` / `es-MX` / `es-AR` / `es-419`(与 markets.json hreflang_codes 一致)。

### 1.2 支付即意图碎片化(payment_words 已入 json)

- 墨西哥:OXXO(现金便利店付款)、efectivo——现金偏好词即购买意图。
- 阿根廷:cuotas(分期)、dólar/financiamiento——通胀经济的分期词带。
- 哥伦比亚/秘鲁:contra entrega(货到付款)——信任缺失市场的转化闸门词。
- 通用层:envío gratis / envio gratis(免运费)。

### 1.3 es-US 集体代搜

- **81% 受托搜索**:西语用户常替家人/朋友搜索(集体代搜,deputized searching)。
- 含义:品牌词 SERP 常被代理商页面/目录页占据;品牌词审计必须做"代看视角"——搜的人不是用的人。
- 转化归因与文案都要按"帮别人买"场景重写(礼物、家人配单)。

### 1.4 墨西哥 2026 增量动态

- **本地 SEO 竞争激化**:PyME 大量涌入 Google Business Profile——照片与评价的**更新节奏**(而非仅在场)成为排位变量。
- E-E-A-T 2.0 强调**作者可验证经验**(verifiable experience)——作者履历实体化是内容层投入方向。
- 微意图(micro-intenciones)+ 内容聚类(content clustering)成为主流实操框架。
- 语音/多模态查询上升:移动端主导,Question-form 关键词层加权重叠(见三、倒问号)。

## 二、渠道:Mercado Libre、外链价带、WhatsApp+Facebook

### 2.1 Mercado Libre listing 五支柱(2026 算法口径)

排名按五支柱评分(来源:Base.com 2026 算法文 + Mercado Libre 官方卖家中心):

| # | 支柱 | 操作口径 |
|---|---|---|
| 1 | Reputación del vendedor | 卖家声誉等级(订单履行/投诉率;投诉率 <1% 是门槛带) |
| 2 | Conversión histórica | listing 历史转化率;新品无历史 → 用 MeLi Ads 注入初始转化 |
| 3 | Título + 关键词 | 60 字符标题模型:品牌+产品+关键属性,关键词前置 |
| 4 | Precio competitivo | 价格竞争力(含 vs catálogo 同款比价) |
| 5 | Envíos | 发货速度/成本;Flex 当日/次日权重最高 |

**ficha técnica(产品资料卡)是第六个隐形支柱**:

- 全字段填满 → 资格进 **catálogo**(平台级产品目录,类 buy-box)→ 赢得 catálogo 直接抬升排名与曝光。
- 字段缺失 = 连参赛资格都没有;漏填字段是 listing 审计里最廉价的修复项。
- **listing 审计顺序**:先 ficha técnica 完整性(全字段清单比对),再五支柱逐项打分。

### 2.2 西语外链价带(2026-10 报价刷新)

高度商品化市场,价带(欧元,ES/LATAM 混合池):

| 层级 | 价带 |
|---|---|
| 平台起步价(Publisuites/Getlinko/Linkatomic/Prensalink) | 12–20 €/链 |
| niche 博客 DR 10–30 | 15–60 €/链 |
| 中权威 DR 30–50 | 60–200 €/篇 |
| 优质单篇(ES/LATAM 通稿) | 80–200 €/篇 |
| 大媒体/大报 | >1,500 €(至 5,000 €) |
| 新闻稿分发 | 7 €/媒体起 |

参考锚:

- Dinorank 口径:"高质量 backlink 均价 ~361 $"。
- comprarenlaces.net 在售 ES+LATAM 域名 5,000+(供给体量的直接证据)。
- **含义**:低价带供给海量 → 竞品外链档案极易被 PBN/付费 niche 污染;审计按 DR 分档识破足迹(见六)。

### 2.3 拉美 WhatsApp + Facebook

- **WhatsApp 是事实转化按钮**:
  - 拉美对话式商务转化 **45–60%,vs 传统网站 2–4%**——十倍以上量差;
  - 落地页 CTA 审计:wa.me 深链是否在场、是否预填消息(wa.me/?text=)、响应时效承诺。
- **Facebook 本地页 = 事实店面**(尤其墨/哥中小企业):帖子节奏+评价+Messenger 响应速度,占品牌 SERP 与发现流量。
- **QR 到店 + WA 索评**:线下转化闭环标准动作——QR 落地索评页走 WhatsApp,不走邮件(邮件在拉美消费场景近缺席)。
- 2026 变量:
  - Meta **Business Agent**(WA 内 AI 导购,Conversations 2026 发布)——对话商务的 AI 层开始成型;
  - Meta 消息计费模式 2026-10-01 调整(巴西新客 2026-07 起 BRL 本币结算)——商务 WA 流量成本结构要重测。

## 三、语言机制:变体分流是本体

### 3.1 词汇三胞胎(不可互换)

- `coche`(西班牙)/ `carro`(墨/哥)/ `auto`(阿/智/乌)——核心高频词分裂最深的一组。
- 同类分流:ordenador/computadora(电脑)、móvil/celular(手机)、patata/papa(土豆)、zumo/jugo(果汁)、autobús/camión(墨"卡车"vs 哥"公交")。
- **关键词研究按变体组分开做**:一份词表通吃 = 拉美或半岛一侧的流量结构性丢失。
- 仲裁工具:Google Trends 按 es-ES / es-MX / es-AR 分域比量级(见七)。

### 3.2 vosotros–ustedes 二分(复数第二人称)

- 西班牙口语用 **vosotros**(动词变位 -áis/-éis);拉美不分正式与否一律 **ustedes**。
- 为西班牙写的文案在拉美读来"外国腔",反之亦然——CTA 文案(`Descubrid` vs `Descubran`)错层直接暴露外包/机翻。
- **单数层**再叠 tú/usted:
  - es-419 B2C 偏 tú;正式 B2B 用 usted;
  - 墨西哥客服/服务场景 usted 密度高于阿根廷(阿 tú 渗透最深);
  - markets.json 口径:tú/usted 按国别,正式 B2B usted。

### 3.3 ¿...? 倒问号与疑问式结构

- 疑问式 H2 是西语内容高频形态:`¿Cuánto cuesta...?` / `¿Cómo elegir...?` / `¿Qué es...?`。
- 倒问号 **¿** + 疑问词开头 = 与语音搜索及 AI 问答 Query 同构——可引性结构(特殊检查项已入 json)。
- 缺倒问号的疑问标题是机翻/外包信号(英文直译漏 ¿)。

### 3.4 数字与日期格式分裂

- `1.234,56`(es-ES 欧式)vs `1,234.56`(墨西哥及部分拉美随美制)。
- 同一站内混用 = 未本地化信号;货币同理(€ vs MXN/ARS/COP——阿根廷通胀下价格须带更新日期)。
- 日期 DD/MM/YYYY 为主(09/10/2026);墨西哥长格式 "9 de octubre de 2026"。

### 3.5 中性西语的边界

- `es neutral`(中性西语)只该用于 **UI 骨架与产品文案**,不用于关键词层与转化文案。
- 正确分层:关键词层按变体组 → 转化文案按目标国 → UI/法务中性层。

## 四、AI-GEO:半岛偏置与语言绑定

### 4.1 语言绑定 83–84%

- 西语查询的 AI 引用 **83–84% 指向西语源**(套件既有公理)。
- 翻译英文站有效的前提是**真西语内容**(非机翻骨架);源语言错配 = 直接退出引用池。

### 4.2 半岛偏置(peninsular bias)对抗

- AIO/ChatGPT 对拉美查询倾向引 **es-ES 源**——系统性偏置,要主动对抗:
  - es-419 独立测 SERP(勿用西班牙代理/VPN 数据代替);
  - 拉美本地托管或 CDN 前置——拉美站点常托管在欧洲,延迟即排名税;
  - 拉美本地作者/实体信号(作者所在地、本地引用、国别 TLD 外链占比)。

### 4.3 西班牙 2026 增量——AI 引用层碎片化

- **AI Information Map Spain**(journalismresearch.org, 2026):
  - 无任何西班牙媒体主导 AI 信息层;
  - 最可见的 El País 仅占引用 **4.9%**——引用池高度碎片化,长尾多样源被引。
- **Limon Publicidad**:AIO 引用源仅 **~15% 与自然 top-10 重合**。
  - 注意:与英文市场"92% AIO 引用来自 top-10"公理冲突——西语市场**经典排名仍是最佳预测因子(mjcachon 口径)但非充分条件**;
  - 操作含义:只盯 top-10 排名会漏掉一半引用机会,长尾权威页(指南/数据页/垂直媒体)单独做可引性优化。
- **覆盖面**:AIO 出现于 ~30–33% 信息型关键词(SE Ranking 33.2/10 万词;Laboratorio de Periodismo ~30% 媒体类查询;Clabe.org 43.6% SERP 无 AIO)。
- **ThinkEPI(学术侧)**:AI Overviews 对西班牙媒体流量造成显著下压——媒体类客户预期管理要用该口径。

### 4.4 测量基础设施

- **GSC"生成式 AI 性能报告"**(informes de rendimiento de la IA generativa,2026-06 起):AI 面板曝光/点击与经典搜索分离。
- 西语站测量基线必须切到该口径;第三方 AIO 抽样只做补充。

### 4.5 SESGO 研究(2026)

- 哥伦比亚研究者团队(WIRED 报道 + 论文 2509.03329):LLM 用西语回答时再现**不同于英语的偏见模式**。
- 含义:西语侧 AI 输出存在系统性评估缺口——品牌在西语 AI 答案中的呈现要单独抽检,不可沿用英语检测结果。

## 五、信息源(本圈在哪聊)

| 区域 | 源 | 用途 |
|---|---|---|
| 西班牙 | **SEOPLUS**(塞维利亚,年度大会) | 半岛算法更新第一手 |
| 西班牙 | **Campamento Web** 播客 | 半岛实操圈层闲聊+风向 |
| 西班牙 | Human Level(Fernando Macià) | 机构层方法论 |
| 西班牙 | Punto Rojo / Vilma Núñez | 年度趋势报告(西语全球视角) |
| 西班牙 | ThinkEPI | 学术侧(AI Overviews vs 媒体) |
| 拉美 | **Nubimetrics Academy** + Telegram 群 | ML 卖家生态风向 |
| 墨西哥 | Alan Quezada | AIO 触达与墨西哥实操 |

## 六、红旗(什么话一出口就判外行)

1. **"一份中性西语通吃"**——首错:auto/coche/carro 不可互换;vosotros/ustedes 变位错层直接暴露外包(见三)。
2. **"拉美=低竞争"**——假:墨城金融/电商词竞争激烈;GBP 拥挤度 2026 年再上一档(见 1.4)。
3. **PBN 泛滥**:
   - 外链市场从 12 € 起的商品化供给(2.2 价带)意味着:竞品档案里的 DR 20–40 单链密集、锚文本过度优化的 niche 群,大概率是租链/PBN;
   - 自家采购同层 = 与垃圾池同游;
   - 租链资产按月租摊销,勿按永久入账。
4. **es-US 集体代搜(81% 受托)被忽略**——品牌词 SERP 被代理商页面占据却不做代看视角优化(见 1.3)。
5. **拉美托管在欧洲不纠**——延迟+本地信号缺失;CDN 本地化是本地 SEO **前置**不是优化项(见 4.2)。
6. **半岛数据代替拉美实测**——用西班牙 SERP 工具口径汇报"西语排名",掩盖半岛偏置。
7. **机翻漏 ¿ 倒问号 / 数字格式混用**——低成本可检的未本地化信号(见 3.3/3.4)。

## 七、Herramientas(工具箱)

- **Nubimetrics**(首选,ML 生态):
  - Mercado Libre **官方合作伙伴**(Centro de Partners 在列);
  - Big Data+AI 分析 ML 全量 listing(供给/需求/价格带);
  - 品类探索器:找低竞争高增长 niche;
  - ML 账号登录即有免费档——低门槛起步。
- **GSC 生成 AI 性能报告**(2026-06+):西语站 AI 可见性测量第一数据源,替代第三方 AIO 抽样。
- **Google Trends 分域**(es-ES / es-MX / es-AR 独立会话):词汇分流(coche/carro/auto)的量级仲裁工具。
- **SERP 采样按国别代理**(MX/AR/CO 独立):半岛偏置对抗的实测层(4.2 的执行工具)。
- **外链交易平台**(Publisuites / Getlinko / Linkatomic / Prensalink / comprarenlaces.net):
  - **审计视角使用**——识别竞队付费层与价带锚点;
  - 不是采购建议(见六红旗 3)。
- **链接档案审计**:按 DR 分档(15–60/60–200/>1,500 € 价带对应)标注可疑租链层;配合 `scripts/link_check.py` 与 monitoring/link-quality-rubric.md。
- **GBP 节奏管理**(墨西哥重点):照片/评价更新频率进本地 SEO 检查表(见 1.4)。
