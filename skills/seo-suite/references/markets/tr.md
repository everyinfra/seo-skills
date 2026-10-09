# Türkiye Pazarı 土耳其语市场专项(Google 一极 + Trendyol 市场内搜索)

> 建立于 2026-10-09(增量研究轮:Trendyol Akademi / Seobaz AIO 研究 / AA / Marketing Türkiye / Technopat / r10.net)。断言半衰期 6-12 个月,随复审更新。
> 配套文件:`overview/multilingual-workflow.md` 土语区段、`scripts/markets.json` tr 键(结构化数据、lint 规则)。
> 来源标注约定:【官】=Trendyol Akademi / Yandex Türkiye 官方;【媒】=一手媒体(AA/Marketing Türkiye/Technopat/Webtekno);【圈】=从业者共识(r10.net/Seobaz/机构博客)。

## 一、引擎格局:份额口径冲突是本区第一事实

| 口径 | Google | Yandex | 说明 |
|---|---|---|---|
| StatCounter 全设备 12 个月(2025-08~2026-09) | ~73% | ~26% | 窗口均值;2025-09 曾出现 Yandex 49.79% 反超 Google 的病毒性数据点 |
| StatCounter 设备拆分(2025) | 桌面 ~63% / 移动 ~85% | 桌面 ~31% / 平板 ~49% / 移动 ~12% | Yandex 力量集中在桌面+平板,移动被 Google 压制 |
| 独立博客复核(cancankiran,2026-08) | — | ~16% | 用行为数据修正 StatCounter 面板偏差 |
| 本地机构实测(点击份额口径)【圈】 | ~94-97% | **3-5%** | 实询/点击侧几乎看不到 Yandex 流量 |

- **冲突必须并记,不得取单一口径**:
  - StatCounter 按"参与站点页面浏览"计量,受 Yandex 浏览器装机默认、后台刷新与疑似 bot 流量污染(btt.community 圈内公开质疑)【圈】;
  - 移动时代真实使用更接近机构实测的 3-5% 或独立复核的 ~16%,而非 26-50%;
  - 2025-09 "Yandex 反超 Google" 病毒新闻即此伪影的极端样本,据此做预算=战略错误(见第六节红旗)。
- Yandex 自报 2025 年用户与查询量 +75%(Marketing Türkiye/AA)【媒】——增长真实,但不等于"半壁江山"。
- 交付口径:**Google 是唯一主战场**;Yandex 仅对桌面/平板重度受众(工具站、导航、部分电商)作低成本次级审计,不设独立预算线。
- 报告引擎份额时必须双口径并记(StatCounter vs 点击实测),禁单口径——这是本区审计的硬规则。

### Yazeka:土语专属 AI 答案引擎【官】【媒】
- **yandex.com.tr/yazeka**,2024-12 上线,免费,全球唯一"为土耳其单独推出"的 AI 搜索入口。
- 支持文本/语音/照片输入(土/英双语);2025 年后新增 Akıl Yürütme(推理模式)+ AI 金融/旅行垂直答案(AA)。
- 答案带来源引用+视频/图片富媒体(egirisim)——形态对齐 Yandex Нейро,但语料与调优土语专属。
- 体量未知、无公开 SoV 工具(俄区 Алиса SoV 报告不覆盖土区)→ 列为**监测项而非优化对象**:品牌词 Yazeka 表现季度抽查即可。

## 二、渠道:市场内搜索(Trendyol)是土语 SEO 的半壁

### Trendyol 排名九信号(Akademi 官方课 + 卖家实测)【官】【圈】
1. **净销售/销售速度**——单量转化最强信号:有转化的商品滚动获得曝光,新卡冷启动最难;
2. **店铺评分(Mağaza Puanı)**:7-10 分制,9.0+ = Üstün Başarılı,直接关系 Buybox 资格【圈,Dopigo】;
3. **评价数量与星级**(含差评率与回复率);
4. **Content Score(内容分)**:卖家面板"İçerik Kalitesi"指标,行业目标 **80-90+**,低于阈值削减可见度【圈;官方未公布公式,以面板读数为准】;
5. **库存深度**:库存量直接影响排名(官方帮助页确认)——**断货即掉**,且补货不复位;
6. **履约表现**:发货/送达率、Tedarik edememme(缺货取消)率、退货率;
7. **价格竞争力 + Buybox**(同款多卖家竞价);
8. **点击率与点击后行为**(停留、加购、复访)——官方口径算法已从词匹配转向点击后行为数据【圈】;
9. **商品信息完整度**:类目属性全填、图集、结构化描述、GTIN/条码。

**Trendyol 操作要点**:
- **标题公式:Marka + Ürün Adı + Model + Özellik**,上限 ~100 字符——品牌前置、卖点词缀后、不堆砌【圈,r10】。
- **efors(权重积累)模型**:排名由历史销售"努力值"累积;断货或开新商品卡 = 权重清零重爬——换卡重启是下策,救老卡优于开新卡【圈】。
- Trendyol 有商品列表上限(限流结构),无限铺货策略受平台配额约束【官,Akademi】。
- 转化单量是飞轮起点:新品用站内广告/外部导流破零,再靠九信号自然滚动——"纯优化不动广告"在 Trendyol 不成立【圈】。

### 链路与内容交易生态
- **r10.net** = 土耳其最大站长交易论坛/市场:backlink、tanıtım yazısı、SEO 服务、 freelancer 人力明码标价——本区灰链与价格发现的**交易中枢**【圈】。
- **tanıtım yazısı(新闻赞助文 + dofollow 外链)**:本地外链主流形态,新闻站靠此变现,已成基础设施:
  - 价格带 **90₺(Seobaz 仓底价)至 13,500₺(全国性大报级)**【圈】;
  - 采购入口:Seobaz/tanitimpaketi/tanıtım yazısı 专业平台 + r10 freelancer 挂单;
  - 审计视角:这是"付费占位",须按赞助内容披露,勿当自然外链报量(第六节红旗联动)。
- Bionluk(土版 Fiverr)承载中小 SEO 外包;backlink ajansı 提供 r10.net 等域名 dofollow 挂单——灰链供应链完整。

## 三、语言机制:黏着语工程

### 黏着语(sondan eklemeli)与关键词方法
- 词根后串接 yapım eki(构词)与 çekim eki(屈折)——一个词根产出几十个表面形式(ölç→ölçe→ölçüm→ölçümü…)。
- 语义研究必须**先归词干、再扩屈折变体**;直接按表面形式建词表会碎片化且量级失真。
- Google 土语 NLU 归组能力尚可(变体常合并 SERP);但 **Trendyol 站内搜索偏字面匹配**——标题/属性按买家真实查询屈折形写,不吃归组红利【圈】。
- 词序灵活(SOV)、格位在词尾:正文里关键词自然屈折即可,勿强行重复原形;问答式长尾词用自然疑问屈折(-mu/-mi/-nasıl)。

### Zemberek-nlp 工程流水线【圈,工程实践】
- **Zemberek-nlp(Apache 开源)**:土语词干提取 + 完整形态分析(morphological analysis)事实标准。
- 关键词变体验证流水线:候选词表 → Zemberek 归干 → 变体聚类 → 逐变体验证搜索量与 SERP 一致性 → 屈折变体按聚类分配到页面组。

### İ/ı 双码点与 URL 转写
- 土语四态 I/i/İ/ı(İ=U+0130,ı=U+0131):
  - 默认 `toLowerCase()` 在 tr locale 下 "I"→"ı";非 tr locale 下 "İ"→"i"+残留;
  - 大小写不敏感比较、ID 匹配、hreflang/lang 校验全是雷区(经典 Turkish locale bug,曾搞挂 Kotlin 工具链)【媒/工程】。
- **URL slug 转写规则**:生成 slug 前先转写 ı→i、İ→i、ğ→g、ş→s、ç→c、ö→o、ü→u,再做 **locale 感知**小写化——否则 "ISTANBUL" 降成 "ıstanbul",与 "istanbul" 双轨并存制造重复页面【圈,工程】。
- 域名一律 ASCII 转写;正文/H 标签保留原生土语字符(_unicode 完整_)。

### 文案与格式基线
- title ~55-60 字符、desc ~150-160;数字/日期用土语惯例(1.234,56;09.10.2026)。
- 敬称正式语全站统一(siz);sen 仅限社媒非正式语境。
- superlative 惯例:营销文案可容纳 en iyi/№1,但 YMYL 页对齐 EU 谨慎口径——无证据最高级慎用(markets.json marketing_words 联动)。
- 季节性:电商词受bayram(宗教节日,日期随伊斯兰历漂移)与 Black Friday(11 月)双峰驱动——节日日历每年重排,勿复用去年投放窗口。

## 四、AI-GEO:top-10 绑定度全球最高之一,美式结论不可平移

- **Seobaz《Türkiye AI Overview Araştırması 2026》**【圈,一手研究】:
  - 样本:8,282 条有效土语移动搜索、7,696 条 AIO 来源链接;
  - 结论:**75.3% 的 AIO 引用与自然结果重叠**,且集中于自然 top-10。
- 对照美国:Ahrefs/SEJ 测得美区 AIO-引用与 top-10 重叠度已从 ~76% 降至 **~37-38%**(Originality.ai 口径 52%)【媒】。
- **推论:土语区 AIO 仍高度绑定经典排名;美区"绕过排名、直做 UGC 引用层"的 GEO 结论不可平移。**
- 交付次序:tr 的 GEO = **先进自然 top-10,再补 UGC 占位**;跳过排名直接经营"被 AI 引用"在土语区基本无效。
- 土语 AIO 引用形态:答案富媒体化(视频/论坛引用占比高)——视频 SEO 与论坛占位是土语 GEO 的两个放大器【圈,Seobaz】。
- UGC 五霸占位动作对照:
  - Ekşi Sözlük:建品牌词条(sözlük 体,非广告腔)+ 监测竞品词条;
  - DonanımHaber/Technopat:新品送测/种子用户帖(科技类目);
  - Akakçe:商品 feed 接入,价格历史页即天然长尾;
  - Şikayetvar:品牌页官方认领+48h 回复 SLA(联动第五节 ORM)。

### UGC 五霸(AIO/SERP 双占位)【圈,Seobaz/Stradiji】
| 平台 | 角色 |
|---|---|
| Ekşi Sözlük | 土版 Reddit;商业问题被引最多,AIO 常客 |
| DonanımHaber | 老牌科技论坛;硬件/电子词占位 |
| Technopat | 科技媒体+社区;评测词被引 |
| Akakçe | 比价站;商品词被引与 SERP 占位双强 |
| Şikayetvar | 投诉层;品牌词常驻(见第五节) |

- Yazeka 引用池与门槛未知(Alice 系基础设施)——不投入专项,品牌词季度抽查。

## 五、SERP 占位与 ORM(itibar yönetimi 产业)

- **Şikayetvar 的 SEO 权重使投诉页稳定占据品牌词首页**;"firma adı + şikayet" 是自动联想常态。
- 土语品牌审计第一步 = 查品牌词 SERP 的投诉占位率(列为常规交付指标)。

### Şikayetvar 官方删除三轨【官】【媒,律所口径】
1. **与投诉人解决**:解决 → 投诉人自行移除,唯一治本路径(站点自家指南亦如此推荐);
2. **违规举报**:侮辱/诽谤/隐私违规 → 站方审核删除;
3. **法律路径**:ihtarname(律师函)→ 内容删除/访问阻断诉讼 → Google 侧 delisting 申请。

- **itibar yönetimi(声誉管理)已是成熟付费产业**:律所+代理+平台三方生态;大中型土语公司普遍采购。
- 治理原则:站点删除只是隐藏;客诉源头解决率才是 ORM 的北极星指标。
- **品牌词 SERP 占位矩阵**:官网+子页面、Şikayetvar 品牌页(官方认领+回复)、Ekşi Sözlük 词条、Akakçe 商家页、LinkedIn/Instagram——五层占满即挤出投诉长尾。
- Akakçe 同时是商品词 SERP 常驻占位者:电商客户的"SERP 份额"审计必须把它算作竞品。

## 六、红旗(本地陷阱与从业者盲区)

- **"本地实操几乎没人做 Yandex"**:土语机构默认只做 Google——
  - Yandex 审计(Webmaster 提交、Yandex Browser 默认搜索可见性)是极便宜的差异化项;
  - 但鉴于份额口径混乱(第一节),只对桌面重度客户启用,勿过度投资【圈】。
- **灰链是本地默认**:r10.net 的 tanıtım yazısı/PBN 套餐是土语外链主渠道:
  - Google spam 风险 + 赞助披露合规双重问题;
  - 审计一律归类"付费占位",禁止计入自然外链增长【圈】。
- **StatCounter 病毒数据的战略误导**:2025-09 "Yandex 反超 Google" 源自测量伪影;据病毒数据重分配预算=真金白银的错误【媒/圈】。
- **Trendyol 断货惩罚与换卡清零**:库存归零是可预防的排名损失;新开商品卡重启是常见自杀式操作——运营 SOP 写死"救卡优先"【圈】。
- 刷单刷评(市场内):平台罚则直接(限流/封店),红线——不做、不推荐、不代运营。
- 交付纪律:
  1. 未验证 GSC(+ 桌面客户加 Yandex Webmaster)不得宣称 production-ready;
  2. 引擎份额报告必须双口径并记;
  3. 外链报告必须区分自然/付费(tanıtım yazısı)两类。

## 七、Araçlar(工具链)

| 工具 | 用途 | 备注 |
|---|---|---|
| Trendyol Akademi | 官方免费课:排名九信号/content score/店铺分/限流结构 | 唯一官方口径源,审计引用优先【官】 |
| pazarus.io | 市场内(marketplace)数据分析 | Trendyol 竞品与词表监测【圈】 |
| Seobaz 研究/blog | 土语 AIO 引用研究、tanıtım yazısı 价目 | 2026 AIO 研究=本文件第四节数据源 |
| Zemberek-nlp | 词干/形态分析 | 关键词变体验证流水线核心(开源) |
| Dopigo | Trendyol 店铺绩效分析 | 店铺分/履约指标【圈】 |
| Akakçe | 比价+商品词 SERP 占位监测 | 既是渠道也是竞品 |
| r10.net | 价格发现/供应链情报 | 只读监测,禁止直接采购灰链交付 |
| StatCounter TR + 本地点击数据 | 双口径引擎份额 | 并记呈现,禁单口径 |

**信息源**:r10.net(交易中枢)、Seobaz/turksem/机构博客、Marketing Türkiye、AA(Technology)、Technopat/Webtekno(份额月报)、Trendyol Akademi(官方)。

## 本地实测(2026-10-09)

### Yandex TR 三口径裁决(26 / 16 / 3-5%)

一手重核后**裁决如下,并修正本文件既有表述**:

| 口径 | 重核后的真实身份 | 裁决 |
|---|---|---|
| ~26% | StatCounter **12 个月滚动窗口均值**(2026-09 视图 25.19-25.53%)——窗口数学上被 2025-09~12 的伪影尖峰(病毒点 49.79%)抬高 | **退役**:作为"当前份额"引用=统计错误;单月已远低于此 |
| ~16% | **同为 StatCounter 源的单月读数**(2026-08 单月 15.98%;2026-03 单月 13.44%,serpsculpt 转引)。⚠ 原文件称 cancankiran "用行为数据修正面板偏差"——**重核原文后确认不实**:该博客明言"Aşağıdaki veriler StatCounter'ın Ağustos 2026 Türkiye ölçümüne dayanıyor",就是引用 StatCounter 单月截图 | 保留为"面板口径现状":单月 13-16% 带 |
| 3-5% | 本地机构点击侧实测(GSC/分析面板引荐流量) | **预算基准**:唯一与真实引流挂钩的口径 |

- **结论**:26 vs 16 是**同源窗口差**(12 个月均值 vs 单月),非独立方法学冲突——原文件"独立博客复核"表述已按上文修正;真正的冲突是 **StatCounter 面板口径(13-16%)vs 点击口径(3-5%)的 3-5 倍差**。Yandex/Google 均不发布 TR 分国份额,公开数据**无法终裁**此差;系列走势(尖峰 49.79%→13.44%→15.98%)与"Yandex 浏览器装机默认+后台刷新污染面板"假说一致。
- **实操判决(替代终裁)**:①预算按点击口径 3-5% 排;②面板单月 13-16% 只作"可见性上限"叙事;③26% 窗口值禁止进报告;④**终裁权限下放给客户自有数据**——交付前查其分析面板 Yandex 引荐占比,<3% 直接放弃 Yandex 专项(第六节红旗的量化补强)。
- 佐证带:Yandex 自报 2025 用户/查询 +75%(Habertürk/AA 复核确认,低基数高增速);生态噪音谱系—— Vimaj 称 1.5%、searchendurance 称 53.05%(2026-01,疑似复读旧尖峰)——TR 份额引用市场是重灾区,双口径并记纪律不放松。

### 真实站验证(trendyol.com / sikayetvar.com)

| 项 | trendyol.com | sikayetvar.com |
|---|---|---|
| site_audit | 原始 HTML **无 H1/0 链接/canonical 缺失**(JS 渲染盲区,实际首页数千链接);**/llms.txt 200(英语类目表)** | H1=1 / JSON-LD=2 / 252 链接,服务端渲染完整 |
| head_check | error=11(弃用 meta 堆叠:twitter:app:* 全套/x-ua-compatible) | error=6(twitter:* 冗余);title 含 Ş/İ 解析正确 |
| llmstxt | ✓ 在架 | ✗ 无 |

- **Trendyol 是 JS-SPA 审计盲区的标本**:无头抓取下"无 H1/0 链接"全是假阴性——Trendyol 类站必须用渲染引擎或 Search Console 数据审计,site_audit 类原始 HTML 工具仅作 robots/llms.txt 探测层。**Trendyol 已上 llms.txt(英语)**:marketplace 把 llms.txt 当 AI 分发入口的信号,与第四节"货架页=可被引实体"互证。
- **Şikayetvar 服务端渲染完整**+结构化数据在场——投诉页能稳定占品牌词首页(第五节)的技术底座;ORM 审计时它就是"竞品技术基准"。

### 工具盲区:İ 双码点实锤(单元级复现)

- `site_audit.py` 词计数 `[A-Za-z0-9']+` **不含 İ(U+0130)/ı(U+0131)/ğ/ş/ç/ö/ü**:实测 "İstanbul"→"stanbul"(İ 静默丢失)、"ıstanbul"→"stanbul"、"içerik kalitesi ölçümü"→ 5 词(实际 3 词,碎片化虚高 67%)——**经典 Turkish-I bug 的计数器变体**,土语页词数/密度读数全部失真,人工复核或先归一化。
- `--market tr` 无专属阈值(仅 ja 特判):desc 用 160 上限而非本文件/markets.json 的 155;title/desc 内 Ş/İ 解析在 head_check 下正常(其解析器独立且正确)。
- İ/ı 归组、slug 转写(第三节)在工具链均无实现——markets.json special_checks 为文档级标记,执行靠人工+Zemberek 流水线。

## 维护

- **复审节奏**:markets.json `tr.review_cycle`(interval_days 90,next 2027-01-09);触发信号:StatCounter TR 单月 Yandex 重上 25% 或跌破 8%、Yandex TR 官方份额/财报披露、Yazeka 引用池公开数据、Trendyol Akademi 算法口径更新。
- **份额纪律**:任何报告出现 Yandex TR 份额必须带口径标签(窗口均值/单月/点击侧),26% 窗口值已退役;新数字先进本文件第一节表格再对外引用。
- **工具链提醒**:土语站词数/密度读数失真(İ/ı/ğ/ş/ç 碎片化),引用前人工复核;SPA 站(trendyol 类)site_audit 仅采信 robots/llms.txt 探测结果。
