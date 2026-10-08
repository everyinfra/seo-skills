# 俄语区(Yandex 生态)SEO/GEO 指南

> 建立于 2026-10-08。份额数据来自 [StatCounter](https://gs.statcounter.com/search-engine-market-share/all/russian-federation);GEO 统计来自 [applabx 2026 年俄罗斯 AI 搜索报告](https://blog.applabx.com/136-ai-search-geo-in-russia-statistics-data-trends-in-2026)(行业研究);工具规则以 [Yandex Webmaster 官方文档](https://yandex.ru/support/webmaster/ru/) 为准。按本套件证据约束:份额为第三方测量,非引擎官方;标注「社区估计」「未证实」的条目不得写入验收标准。
> 俄语区必须当作**独立学科**处理:Yandex 份额 ~70–73%(2026),工具栈、排名信号、合规要求与 Google 系几乎不重叠。

## 一、引擎与 AI 格局(2026)

| 事实 | 数字 | 来源类型 |
|---|---|---|
| Yandex 俄搜索份额 | ~70–73%(2026-09: 70.35%) | 行业(StatCounter) |
| Google 在俄份额 | ~25–28% | 行业(StatCounter) |
| Alice(Алиса)月触达 | ~6,600 万用户 | 行业(applabx) |
| Dzen MAU | 6,800 万(Mediascope 2026-08) | 行业 |
| AI 答案覆盖 | 68% 信息查询(Yandex)/ 43% 商业查询 | 行业(applabx) |

AI 产品:Нейро(Neuro,生成式搜索,2024-04 上线)、Alice AI(答案带"Источники"来源按钮)、GigaChat(Sber,15,000+ 企业客户)。2026 夏调查显示 Alisa AI/GigaChat 在俄使用超过 ChatGPT(调查法,谨慎引用)。

## 二、工具栈映射(Google → Yandex)

| Google 系 | Yandex 系 | 关键差异 |
|---|---|---|
| Search Console | **Yandex.Webmaster** | 按主机(非单页)索引、"主镜像"粘合;**ИКС 站点质量指标**(替代 тИЦ);Turbo 页面 2025-04 已停用勿再推荐;**自带"Видимость сайта в Алиса AI"面板**(官方) |
| GA4 | **Yandex.Metrica** | 免费含 Вебвизор 会话回放;GA 在俄因 152-ФЗ 实际不可用 |
| Keyword Planner | **Yandex.Wordstat** | 显示**预测曝光**非搜索量;算子:`"引号"`=精确短语、`!词`=精确词形;季节曲线+分区域 |
| Business Profile | Yandex Business/Maps | 免费商家卡,驱动本地包与导航 |
| Google Ads | Yandex.Direct | 拍卖 PPC;需 ORD 广告标记(见合规) |

## 三、排名信号差异(相对 Google)

- **行为因素权重远高**:摘要 CTR、停留、滚动深度、返回 SERP、跨页导航。~45% 权重是社区估计(Sostav 博客),非官方——用作方向,不作承诺。
- **商业因素**:价格、品类、配送、联系方式、支付、评价的准清单(Kokoc 等社区整理)。
- 链接因素存在但弱于行为;.ru/.рф 相关链接与原生西里尔内容占优。
- 过滤器:АГС(低价值站)、Переспам/Переоптимизация(关键词堆砌)。
- 区域排名:SERP = f(用户区域, 文档区域, 查询地理依赖)——Webmaster/Business 中设区域。
- 2025–26 算法:**Королёв**(2025-06,商业查询重构)、**Вега**(专家性/作者真实性,类 E-E-A-T)、Neuro 覆盖扩展。「Grad」这一算法名查无实据,勿引用。

## 四、GEO / AI 搜索(俄语)

1. **Alice AI 的来源取自 Yandex 自然 SERP**——不单独爬取、不单独排序(官方 Webmaster 文档)。行动含义:**经典 Yandex top-10 是 Alice 引用的前提**;每周看 Webmaster 的 Alice 可见面板并记录被引 URL。
2. **Neuro/Alice 的退出控制**:robots.txt `User-agent: YandexAdditional / Disallow: /` 是唯一文档化控制(Forbes RU 等媒体已用)。允许 = 进入 Neuro/Alice 引用池;与 GPTBot 等政策分开决策。
3. **llms.txt**:无证据 Yandex 消费;俄社区共识是仅策展性——不承诺效果(未证实为被忽略,但也无官方支持)。
4. **GigaChat 2**:联网检索+编号脚注引用,**仅聊天 App 内显示,API 不带引用**(官方 FAQ)→ 品牌抽查须手工在 App 内做。
5. applabx 实测:俄信息类发布商最高 **-60% 自然流量**;语音占 Yandex 搜索 20%(2024);行为信号+新鲜度+抓取速度是俄语 GEO 基础。

## 五、合规(外国站实际需要)

- **152-ФЗ(个人数据本地化)**:俄公民个人数据的初次收集/系统化/存储须在俄境内数据库;隐性传给境外服务(如 GA)被禁 → 俄向页面用 Metrica 是合规姿态而非偏好。
- **ORD/erid 广告标记**:面向俄受众的**付费**在线广告须在 ORD 登记、erid 令牌、ЕРИР 报告;未标最高 50 万₽罚。**自然 SEO 内容不属于广告**(除非付费投放)。
- 2026-03-01 起俄广告中外来语使用受限。

## 六、GitHub 现状(2026-10 检索)

俄语区原生 SEO/GEO skill 生态很薄:多为 MCP 封装([Yurich-ru/yandex-ads-mcp](https://github.com/Yurich-ru/yandex-ads-mcp) 43★、[stufently/yandex-mcp](https://github.com/stufently/yandex-mcp) 18★),唯一直接先例是 [Horosheff/google-yandex-seo-skill](https://github.com/Horosheff/google-yandex-seo-skill)(39★,双语审计)。`yandex geo` 等检索 0 结果——本套件此文件即填补该空白。

## 七、俄语 AI 搜索就绪清单(15 项)

1. Yandex.Webmaster 验证;区域设置;ИКС 基线记录。
2. Yandex.Metrica 安装并开 Вебвизор(替代 GA,兼 152-ФЗ 姿态)。
3. Wordstat 语义核(`!`+`"…"` 算子;分区域;季节曲线)。
4. 目标查询进入经典 Yandex top-10(Alice 引用前提)。
5. 周度跟踪 Webmaster"Видимость в Алиса AI",记录被引 URL。
6. robots 对 `YandexAdditional` 做显式决策(允许=进 Neuro/Alice 池)。
7. 答案形态内容:首屏 40–60 词直接答案(Alice 约显 5 行)+ FAQ/QL 标记。
8. 商业因素清单填满(价格/配送/支付/联系方式/评价)——Королёв 时代要求。
9. 新鲜度:更新时间戳+IndexNow(Yandex 参与)加速收录。
10. 行为 UX:面向 CTR 的标题/摘要(西里尔原生、无 emoji 堆砌)、内链提停留。
11. 原生西里尔文案(非机翻)、+7 电话、地址、юридические данные——Vega 专家性信号。
12. 本地查询:Yandex Business 卡认领+评价管理。
13. Dzen 作为品牌面(6,800 万 MAU;nofollow 经济,不当链接源)。
14. GigaChat 引用只能 App 内手工抽查(API 不带)。
15. 合规闸门:俄用户数据入库俄境;任何付费投放先解决 erid 标记。

## 未证实项(不得写成事实)

「Grad」算法名;Neuro 图/视频答案格式;行为因素 ~45% 权重;applabx 的 DeepSeek 俄份额;Королёв 2.0 细节。
