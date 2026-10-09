# 移动 SEO 专项(2026 口径)

> 建立于 2026-10-09。以 Google 官方文档为基准;行业数据标注来源。分工边界:JS 渲染诊断见 [rendering-seo.md](rendering-seo.md)(Mobile-Friendly Test 退役在其检测节),CWV 指标定义见 [LCP.md](LCP.md),viewport meta 写法见 [head-elements.md](head-elements.md),新兴市场移动占比见 [markets/id.md](../markets/id.md)——本文件只做移动专项,不重复。

## 一、移动优先索引 2026 现状(切换完成后)

### 1.1 时间线与现状

| 时间 | 事件(口径) |
|---|---|
| 2016 | 分批启动移动优先索引 |
| 2018-2023 | 渐进放量,GSC 逐站通知 |
| 2023-10 | 官方博客宣布最后一步 |
| **2024-07-05** | **Googlebot 只以 smartphone UA 抓取全部站点(官方)** |
| 2026 现状 | **切换早已完成,不存在"移动优先"与"桌面优先"之分——索引里只有移动版** |

- **核心含义**:Google 索引、排名、快照、结构化数据提取**全部基于移动版 HTML**。桌面版里"有而移动版没有"的内容(文案/内链/图片 alt/JSON-LD/标题)对 Google **等于不存在**——这是 2026 年最常见的静默损失,因为 GSC 不报、排名缓降、没人报警。
- 残留概念纠偏:客户提案里还写"做好移动适配以便进入移动优先索引"= 过时话术;2026 的正确表述是"**移动版就是你的索引内容本体**"。

### 1.2 桌面差异内容的处理(官方口径逐项)

| 内容类型 | 处理规则 | 常见踩坑 |
|---|---|---|
| 结构化数据 | 移动版必须完整携带;桌面独有 schema 不被读取 | 桌面注入 JSON-LD、移动版靠 JS 后注入且失败 → 富结果静默消失 |
| 图片 | 索引移动版实际展示的图(含 alt、文件名);桌面高清图不算数 | 移动版换裁剪图但 alt 丢失;懒加载图无占位 |
| 视频 | 元数据同样以移动版为准 | 桌面有 VideoObject 移动版没有 |
| 隐藏内容(折叠/tab/手风琴) | 移动版默认折叠但渲染后 DOM 存在的内容**可被索引**(官方:内容在渲染后 HTML 即可索引) | 把关键内容全塞进需要点击的 tab 且靠 JS 失败加载 |
| 标题/meta | 以移动版输出为准 | 响应式站同 URL 无此问题;m. 站模板 title 与 www 不同步 |
| 内链 | 移动版没有的链接 = 站点的这部分链接图不存在 | 桌面页脚塞满导航、移动版折叠菜单 JS 渲染失败 |

### 1.3 独立 m. 站(历史遗留)的风险清单

- m. 与 www 内容不对齐 = 索引到的是 m. 的瘦版(字数少/schema 缺/链接少),www 的优化投入全部落空。
- canonical/alternate 接线:www ↔ m. 双向(`rel=alternate media=` + m. 上 `rel=canonical` 回 www);接错 = 混合索引信号。
- UA 重定向:移动 UA 访问 www → 必须到**对应** m. 页;回首页式重定向 = 转化+抓取双输。
- robots.txt/抓取预算:两套站点双倍抓取成本。
- **2026 主流答案仍是响应式单 URL**——m. 站只该出现在历史遗留审计里;新项目与重构一律响应式,动态服务(同 URL 按 UA 出不同 HTML)因内容漂移风险同样不推荐(rendering-seo.md 的 cloaking 红线)。

### 1.4 parity(内容平价)检查法

1. **双视口抓取 diff**:同 URL 分别以 ~375px 与 ~1280px 视口渲染(Playwright 两次 goto;或 m. 站直接抓两个域),对比主内容文本量、内链数、图片数、结构化数据条数。diff >20% 即黄旗,>50% 红旗。
2. **GSC 按设备拆分**:效果报告加"设备"维度,某页移动点击断崖而桌面正常 ≈ 平价破裂的典型指纹(移动版渲染失败/内容缺失)。
3. **GSC URL Inspection(Live Test)**:看 smartphone Googlebot 实际抓到的渲染后 HTML 是否含关键内容——这是唯一"以 Google 视角"确认法。
4. 爬虫级:Sitebulb/Screaming Frog 均支持按视口或 UA 分设备爬取,产出一页两行的对比表。

4. 爬虫级:Sitebulb/Screaming Frog 均支持按视口或 UA 分设备爬取,产出一页两行的对比表。

**平价破裂诊断表**:

| 症状 | 优先怀疑 | 验证 |
|---|---|---|
| 移动点击掉、桌面稳 | 移动版渲染失败/内容缺失 | Live Test 看渲染后 HTML |
| 移动版字数系统性少 | CMS 移动模板裁剪(m. 遗留) | 双视口 diff |
| 富结果消失 | 移动版 JSON-LD 缺失或 JS 注入失败 | Live Test + Rich Results Test |
| 图片搜索流量掉 | 移动版换图/丢 alt | 双视口对比 img 与 alt |
| 索引量 > 移动流量应有权重 | m./www 混合索引 | site: 双域抽查 + canonical 接线 |

未证实项:部分低质来源宣称"2026-07 起无移动版站点被彻底逐出索引"——官方只承诺过 2024-07-05 的抓取切换,更激进的排除时间表**未获官方证实**;但"移动版不可用=不可索引"的事实从 2024 起就成立。

## 二、移动页面体验(官方口径与阈值)

### 2.1 viewport

- 唯一正确写法:`<meta name="viewport" content="width=device-width, initial-scale=1">`;刘海屏加 `viewport-fit=cover`。写法细节与 head 内顺序见 [head-elements.md](head-elements.md)。
- **红线**:`width=固定值`(如 980px)→ 手机上横向滚动 → **P0 级移动缺陷**;`user-scalable=no`/`maximum-scale=1` 禁缩放 → 无障碍与可用性双扣分(无直接排名惩罚,审计必报)。
- 审计方法:爬虫收 viewport meta 分布(全模板唯一正确值);Playwright 以 360px 宽截图抽查主要页型,`document.documentElement.scrollWidth > innerWidth` 即横向滚动。

### 2.2 触摸目标(tap targets)

- **推荐最小 48×48 CSS px**(Google/Lighthouse 口径),元素间距 ≥8px;连"尺寸达标但挤在一起"的导航同样判 fail——正文内密集文字链是最常见违规位。
- 法律级下限:WCAG 2.5.8 Target Size(Minimum)AA = **24×24 CSS px**(带间距豁免条款);Apple HIG 传统口径 44pt。审计报 48px 推荐 + 24px WCAG 双线。
- 检测:Lighthouse mobile 的 "Sizing tap targets appropriately" 审计逐元素给违规清单;重点位=正文行内链、分页器、表单控件、底部固定栏。

### 2.3 字体

- 正文基准 **≥16px**;**表单 input 字号 <16px 会触发 iOS Safari 聚焦自动放大**(强制缩放体验,审计必报);配套行高 ≥1.4、对比度 ≥4.5:1。
- 移动特有检查:正文避免高对比反转(暗底亮字大段文字)与 100% 宽长行(≤70 字符/行等效);标题层级在 360px 下不折行成三行。

### 2.4 移动体验阈值速查表

| 项 | 推荐值 | 底线/出处 | 审计判定 |
|---|---|---|---|
| viewport | `width=device-width, initial-scale=1` | 官方唯一推荐写法 | 其他任何值=warn,固定宽=fail |
| 触摸目标 | ≥48×48 CSS px,间距 ≥8px | WCAG 2.5.8 AA 24×24(底线) | <24px 或过挤=fail |
| 正文字号 | ≥16px | iOS input <16px 触发聚焦缩放 | input <16px=fail |
| 行高 | ≥1.4 | 可用性惯例 | warn |
| 对比度 | ≥4.5:1(正文) | WCAG AA | fail |
| 插页 | 非全屏、易关、非进入即弹 | 官方三形态+豁免清单 | 违规形态=fail |
| 横向滚动 | 360px 视口下无 | 派生自 viewport 正确性 | fail |

### 2.5 插页式广告(Interstitials)

- **政策名:Intrusive Interstitials(侵扰性插页)惩罚,2017-01-10 生效,仅作用于移动端,算法性排名调整**(非手动动作)。
- **官方定义的三种违规形态**:
  1. 用户从搜索结果进入后立即弹出、遮住主内容的弹窗;
  2. 须先关闭才能看内容的独立插页页(interstitial page);
  3. 首屏上方伪装成首屏的横幅(实际是广告)。
- **官方豁免清单(不算违规)**:Cookie/GDPR 同意提示、年龄验证、登录墙(付费墙内容)、**占用屏幕比例合理且易关闭的横幅**。新闻 App 深链弹订阅墙属于登录墙豁免范畴。
- **阈值口径**:官方**无数字阈值**(无"超过 X% 屏幕即罚")——判断点是"是否阻碍用户从搜索过渡到内容"。行业实操参考:非全屏、≤15-25% 屏高、即时可关、非进入即弹,基本安全。
- 检测工具现状:GSC **Mobile Usability 报告已于 2023-12-01 退役**(同批退役 Mobile-Friendly Test 工具与 API,公告见 2023-04 官方博客《The role of page experience in creating helpful content》);Page Experience 报告同轮弱化为指向官方指南的落地页。**现行检测 = Lighthouse(mobile)审计 + PSI + CrUX 字段数据 + 爬虫级 DOM 检查**(弹窗类名/属性清单可复用 [audit-rule-catalog.md](audit-rule-catalog.md) 的 audit_negative 思路:modal/popup/overlay/interstitial/lightbox 类名与 data-modal 属性)。

## 三、AMP 遗产(已死的 SEO 特殊性)

### 3.1 死亡时间线与 2026 定位

| 时间 | 事件(口径) |
|---|---|
| 2015-2016 | AMP 发布,Google News/Top Stories 给 AMP 专属入口 |
| 2021-06 | **Page Experience 更新:AMP 失去排名偏好;Top Stories 不再要求 AMP**(官方) |
| 2021+ | Discover、轮播、视觉特性对非 AMP 一视同仁 |
| 2025-08-25 | Firebase Dynamic Links 关停(AMP 生态外围件,见 5.2) |
| 2026 现状 | **未被正式废弃,但 SEO 零特殊性——无排名加分,无任何 SERP 特性门槛**;行业估计约 40% 用过 AMP 的站点已下线(转述估计) |

- **留存与否的决策**:唯一保留理由=遗留依赖(老 CMS 插件/分析埋线/AMP Cache 惯性);任何新项目**不应再引入 AMP**。CWV 好成绩完全可以裸站达成(优化路径见 [LCP.md](LCP.md) 与第四节)。
- 对客户的表述:AMP 不是"被惩罚",是"特权被收回"——现在它只剩成本(双模板维护/受限组件/统计口径分裂),没有收益。

### 3.2 迁移 off AMP 注意事项(审计执行清单)

1. **存量盘点**:GSC/sitemap/内链全量列出 `/amp/` 与 `?amp` URL;按外链与流量排序,高价值页优先迁。
2. 每个 AMP URL → 对应规范 URL **301**(不要批量回首页);`<link rel="amphtml">` 从规范页删除。
3. sitemap 与内链同步清理;AMP 专用结构化数据字段(如 `amphtml` 相关标记)清除。
4. **性能平价先行**:AMP 的真实遗产是"快",下线前先确认替代页 CWV(p75 移动)不劣化——否则 Top Stories/Discover 流量会先于排名掉。逐模板对拍:AMP 版 vs 规范版的 LCP/INP/CLS。
5. 结构化数据随迁:Article/NewsArticle 的 JSON-LD 不依赖 AMP 格式,原样搬到规范页(逐字校验,迁移最易丢字段)。
6. 迁移窗口盯 GSC 覆盖报告与 Discover 流量 2-4 周;AMP 版删除后 Google 需重新抓取规范 URL,短期索引波动属正常,跌势不止才回滚排查。
7. 未证实项:AMP Cache 的最终关停时间表以 amp.dev 当前公告为准,迁移前核对一次。

## 四、移动性能特殊性

### 4.1 阈值不变,网络与设备变

- CWV 阈值(LCP ≤2.5s / INP ≤200ms / CLS ≤0.1,p75)定义见 [LCP.md](LCP.md);**CrUX 字段数据按移动/桌面分开报告,审计以移动 p75 为准**——它是 PSI 与页面体验信号的取数口径。
- 同一站点移动与桌面 CWV 常差一倍以上(设备 CPU+网络),桌面过线移动不及格是常态而非例外——**报告永远拆设备**。

### 4.2 测试环境矩阵

| 环境 | 参数(约) | 用途 |
|---|---|---|
| Lighthouse mobile(默认) | 中端安卓 CPU 4× 降速 + slow 4G(≈150ms RTT、下行 ≈1.6Mbps) | **标准移动基线**,不是悲观设定 |
| DevTools Fast 4G | ≈1.6Mbps 下行 | 与 Lighthouse 口径对齐复测 |
| DevTools Slow 3G | ≈400kbps 下行、RTT 数百 ms | **压力测试**,新兴市场必跑 |
| 真机 DevTools | 中端安卓实体机 | 节流模拟器校准,发布前抽测 |

### 4.3 新兴市场基线(引 markets)

- 印尼:**移动 >82% 搜索流量,slow-4G 为测试基线**,CWV 全部按节流 4G 测([markets/id.md](../markets/id.md))——群岛网络现实使 LCP 每降 0.5s 都是实打实的转化杠杆。
- 印度:搜索市场 ~75% 移动,移动端 Google 份额 ~99.2%([markets/hi.md](../markets/hi.md))。
- 出海新兴市场时,"移动 p75 过线"是入场券而非优化项;东南亚/南亚目标站点以 slow-4G 达标为验收线。

### 4.4 移动特有的指标风险

- **LCP**:首屏 hero 图响应式缺 `srcset/sizes`(大图喂小屏,直接多花几百 KB);LCP 图误加 `loading=lazy`(红线,rendering-seo.md 已列);web 字体阻塞渲染未 `font-display: swap`;图片 CDN 未按视口裁剪。
- **CLS**:响应式图片**缺 width/height 属性**;广告位/嵌入物无占位;字体交换位移(度量不一致)。
- **INP**:触屏交互密集(每个 tap 都是 INP 计时点)、中端机 CPU 慢 3-4 倍、第三方脚本与长任务在移动上放大——桌面 INP 良好不代表移动过关。
- 移动网络常识杠杆:Brotli/gzip、关键 CSS 内联、预连接第三方域、`preload` LCP 资源——与桌面同理,但收益按移动网络成本放大。

## 五、移动 SERP 特性与应用深度链接

### 5.1 移动端 SERP 差异

- **更视觉化**:行业追踪(STAT)口径——smartphone SERP 视觉特性(图片/视频/轮播)密度显著高于桌面;图片结果在桌面 SERP 也已升至 ~27%(2026-01 对照 2024-01 的 17%)。特性跨设备会变,记录维度与追踪方法见 [serp-feature-taxonomy.md](../research/serp-feature-taxonomy.md)(其记录维度本来就含设备,不重复)。
- **CTR 更差**:移动零点击更高(Similarweb 2026:移动仅 **45.2%** 搜索产生外站点点击);行业面板显示 2025Q4→2026Q1 **桌面 CTR 回升而移动顶部位置 CTR 继续下滑**。AWR 2026:位置 1 平均 ~20% 有机 CTR,**有 AIO 时降到 ~9.7%**——移动上 AIO 抢点击更狠。
- **排名分歧**:移动与桌面排名差在拉大(定位/个性化/设备信号)——**排名追踪必须按设备拆分**,单一"平均位置"对本地型/语音型查询完全失真(nightwatch 行业口径)。
- **移动主导面**:Discover 基本是移动端面(官方机制与波动性见 [discover-news-seo.md](../content/discover-news-seo.md),不重复);本地包/near me 在移动首屏权重最高(见第六节)。
- **设备维度 SERP 差异速查**:

| 特性 | 移动 vs 桌面 | 审计动作 |
|---|---|---|
| 图片/视频/轮播 | 移动密度显著更高 | 视觉资产优化按移动优先 |
| AIO | 移动抢点击更狠(位置 1 CTR 20%→9.7%) | 引用优化按移动口径测 |
| Discover | 移动端面 | 见 discover-news-seo.md |
| 本地包 | 移动首屏权重最高 | 见 6.2 |
| App 包/深度链接 | Android 查询面 | 见 5.2 |
| 排名 | 设备分歧拉大 | 双设备追踪 |

- 对 KPI 的含义:移动流量目标要按"更低 CTR 曲线"校准——用桌面 CTR 外推移动流量会系统性高估。

### 5.2 应用深度链接(App Indexing 的 2026 现实)

- **已死件**:Firebase **Dynamic Links 于 2025-08-25 关停**(官方 FAQ,存量链接全失效);Firebase App Indexing 同步弃用——"把 app 内容喂给 Google 索引"这条老路线已不存在。
- **官方现行口径(2025-05 官方博客《App deep links: connecting your website and your app》)**:站点上的 deep link 把网页 URL 与 app 内页面**关联起来,但不改变 Google 搜索的展示方式**——Search 索引与排名的仍是**网页内容**;app 的收益是"用户已装 app 时,点搜索结果/浏览器链接直达 app 内页"的体验层。
- **该做的**:
  - Android:**App Links + `/.well-known/assetlinks.json` 数字资产链接验证**(intent 过滤器 + 签名指纹);
  - iOS:**Universal Links + `/.well-known/apple-app-site-association`**;
  - `rel=alternate` 指向 `android-app://` scheme 仍可用但非必需;
  - 验证方式:Android 的 App Links Assistant / `adb` 实测;iOS 用 OpenSDK 验证器或日志。
- 商务含义:有 app 的客户,深度链接是**转化优化项,不是索引项**——别再按 2016 年的"app indexing"提案收钱;审计发现此类提案=话术过期证据。

## 六、移动内容策略

### 6.1 语音查询=移动主场

- 语音搜索绝大多数发生在手机/助手设备上;查询更长、更口语、问句化,且与本地意图高度重叠("near me"式语音)。
- **不需要为语音单独建页**(该结论见 [content-patterns.md](../content/content-patterns.md) 语音节,不重复)——移动内容策略的落点是:自然问句做标题、答案首句给结论、段落短到能被念出来。
- 结构化 FAQ 仅在内容真实构成问答时使用;FAQ rich result 已大幅收缩(2023 起 Google 只对政府/卫生权威站展示),不要为语音堆 FAQ schema。

### 6.2 本地意图=移动主导

- "near me"/导航/"营业中"类查询以移动为绝对主力;移动 SERP 上本地包+地图坐首屏,标题/星级/距离决定点击。
- 本地排名的网格化移动追踪方法见 [local-grid-ranking.md](../monitoring/local-grid-ranking.md)(其口径本就按移动跟踪,不重复);配套硬指标:click-to-call、路线规划、营业时间在移动版**首屏可达**。
- 移动版地址/NAP 与 GBP 一致性是本地引用的基础层,审计纳入移动版专用检查。

### 6.3 移动内容优先(MFI 的内容面)

- 既然索引只认移动版,写作与排版直接以移动版为初稿:答案前置、首屏给出核心结论(桌面富内容可加,但**移动版先不能瘦**)。
- 折叠/手风琴收纳的补充内容可留(渲染后 DOM 在即可索引),但主结论必须在展开区域之上。
- 移动扫读形态:360px 下的可读性硬约束——横向滚动表格=移动缺陷(重排为卡片或定义列表);列表项不加 href 的纯文本 bullets 不传递权重;段落 2-3 句为宜。

## 七、移动专项审计清单(15 项)

1. viewport meta 全模板唯一且正确(`width=device-width, initial-scale=1`);无固定宽度、无禁缩放。
2. 360px 视口宽下逐页型抽查**无横向滚动**(`scrollWidth > innerWidth` 判定)。
3. 触摸目标 ≥48×48 CSS px 且间距 ≥8px(Lighthouse "tap targets" 审计);底线 WCAG 24px;重点位=正文行内链/分页器/底部固定栏。
4. 正文字号 ≥16px;**所有 input 字号 ≥16px**(防 iOS 聚焦放大);行高/对比度抽查。
5. **内容平价**:双视口(或 m. 域)抓取 diff 主内容/内链/结构化数据/图片 alt——桌面有移动无=P0(方法见 1.4)。
6. m. 遗留站:canonical/alternate 双向接线、逐 URL 对应重定向(无回首页式重定向)、混合索引检查。
7. 结构化数据在**移动版渲染后 HTML** 里完整(GSC Live Test 验证),桌面独有 schema 清零。
8. 插页式对照官方豁免清单逐项过:全屏弹窗/独立插页页/伪首屏横幅=违规;记录出现时机(进入即弹 vs 内容接触后)与关闭难度。
9. AMP 遗留:`/amp` URL 301 到规范页、`rel=amphtml` 已清、sitemap 干净、下线页 CWV 不劣化(见 3.2)。
10. CrUX/PSI **移动 p75** 三指标过线(LCP/INP/CLS);Lighthouse mobile 按标准节流跑。
11. 目标市场网络压力测试:slow-4G 基准,新兴市场加 slow 3G(引 [markets/id.md](../markets/id.md))。
12. LCP 资源三查:非 lazy、有 `srcset/sizes`、有 `width/height`;字体 `font-display: swap`。
13. 排名追踪**按设备拆分**;移动/桌面分歧大的词单列(本地/语音型重点);流量预测用移动 CTR 曲线。
14. 有 app 客户:`assetlinks.json`/AASA 有效、深度链接直达对应页(定位=转化,非索引;见 5.2)。
15. 本地业务:本地包移动首屏占位、GBP 信息完整、click-to-call/路线首屏可达(方法见 [local-grid-ranking.md](../monitoring/local-grid-ranking.md))。

## 来源

官方:Google Search Central(移动优先索引文档、smartphone-only 抓取公告 2023-10、app deep links 博客 2025-05、插页式政策页)、Firebase Dynamic Links 关停 FAQ(2025-08-25)、2023-04 page experience 博客(Mobile Usability 报告/MFT 退役)。行业:STAT(视觉 SERP)、Similarweb(移动 45.2% 外部点击,2026)、AWR(位置 1 CTR ~20%/AIO 9.7%,2026)、seosherpa(桌面升移动降,2025Q4-2026Q1)、nightwatch(设备排名分歧)、London Web Factory/WP Poland(AMP 2026 定位,~40% 已下线为转述估计)。未证实项:无移动版站点被"彻底逐出索引"的 2026 时间表(低质来源);AMP Cache 最终关停时间表(以 amp.dev 现行公告为准);Lighthouse/DevTools 节流参数随版本浮动,以当前版本为准。
