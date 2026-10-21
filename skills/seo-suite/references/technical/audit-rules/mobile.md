# 审计规则目录 · Mobile

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### Mobile(12 条,权重 2%)

正文字号 **<12px 败、内联 12-16px 警**(只读内联 `style` 与 `<style>` 块,外部样式表不读;em/rem/% 按 16px 换算;行高 <1.2 或 body/html 内联字号 <14px 也警);横向滚动=warn/fail;插页弹窗(跳过 cookie/GDPR/年龄验证/登录)=warn/fail;viewport 设固定像素宽度=**fail**(须 device-width);多 viewport 标签=fail;**parity 五条(`--mobile` 双渲染对比,我们覆盖薄)**:content、title+description=warn/fail,canonical=fail,structured-data=fail(JSON-LD 桌面有移动无),links(移动 `a[href]` 数至少为桌面一半)=warn;image maps(`<map>`/`<area>` 客户端图像地图,固定像素坐标不适配触屏)=warn;viewport content 规范(width 存在+initial-scale=1+**不设 minimum-scale**)=warn。

**解释层(6 条,第三批;ID 未公布原文的按家族命名法推得并标 [待核];移动优先索引与 m. 站背景见 [mobile-seo.md](../mobile-seo.md) 第一节)**

#### mobile-font-size
- 名称/类型: 正文字号 —— warning · 优先级 medium · 输出 WARN(中间档)/CRITICAL(<12px,源表败)(源表现行:只读内联 style 与 <style> 块;任何 <12px=fail;内联 12-16px、行高 <1.2、body/html 内联字号 <14px=warn)
**这意味(what)**: 移动视口下正文主体字号低于 16px 建议值,<12px 进败档。
**为什么(why)**: 小字号降低移动端可读性。Google 2016 年的博文把「文字无需缩放即可阅读」描述为移动友好标准之一([博文](https://developers.google.com/search/blog/2016/08/helping-users-easily-access-content-on),核对 2026-10-21);现行[页面体验文档](https://developers.google.com/search/docs/appearance/page-experience)仍把「内容在移动设备上是否显示良好」列为自评问题。字号阈值本身是工具约定。[mobile-seo.md](../mobile-seo.md) 审计口径:表单 input 字号 <16px 会触发 iOS Safari 聚焦自动放大(Safari 行为,本次未回读 Apple 文档),审计必报。rem/em 单位让用户的浏览器字号设置能生效。
**触发(trigger)**: 上游:扫内联 style 和 <style> 块里的 font-size(em/rem/% 按 16px 换算):<12px → fail;内联 12-16px → warn。外部样式表里的字号用浏览器 DevTools 的 computed 值复核;input 字号 <16px 本套件单列必报。
**不修的条件(caveat)**: 字号不(直接)影响排名,然而它影响移动可用性与移动优先索引下的页面评估,所以一般建议正文 ≥16px。但辅助信息(脚注/标签/法律小字)适度小一档是排版惯例,别一刀切拉平。
**修复(fix)**: 正文基准 16px(1rem)+行高 ≥1.4;input 全部 ≥16px 防 iOS 聚焦放大;对比度配套 ≥4.5:1。
**关联(seealso)**: mobile-viewport-config、mobile-overflow;[mobile-seo.md](../mobile-seo.md)

#### mobile-viewport-config [待核 ID]
- 名称/类型: viewport 配置家族(源表 ID `mobile-viewport-width`、`mobile-multiple-viewports`、`mobile-viewport-content`、`a11y-zoom-disabled`) —— issue/warning · 优先级 high · 输出 CRITICAL(固定宽度、多 viewport、禁缩放,源表 fail)/WARN(width/initial-scale/minimum-scale 不规范,源表 warn)
**这意味(what)**: viewport meta 存在但配置错:缺 width=device-width、content 不规范(width 缺失/initial-scale≠1/设了 minimum-scale)、文档里多条 viewport、或用 user-scalable=no/maximum-scale=1 禁用缩放。
**为什么(why)**: 移动优先索引下 viewport 是渲染的控制面:缺 device-width 按桌面宽渲染再缩放,字号与点击目标全错;禁缩放拿走弱视用户的最后手段(捏合放大)——无障碍硬红线;多 viewport 时浏览器取舍不一,行为不可控。与 core-viewport(缺失=fail)分工:那条管"有没有",本条管"对不对"。
**触发(trigger)**: 1) viewport meta 计数 >1 即 fail;2) content 含 user-scalable=no 或 maximum-scale=1 即 fail;3) 设固定像素宽度(无 device-width)即 fail(源表现行);4) width 缺失/initial-scale≠1/含 minimum-scale 即 warn。
**不修的条件(caveat)**: viewport 配置影响渲染形态与可用性,不改变内容相关度,所以一般建议按规范值整站统一。但全屏交互(地图/画布)确需局部禁缩放时,只在该视图动态设置并给替代操作。
**修复(fix)**: 单条 `<meta name="viewport" content="width=device-width, initial-scale=1">`;删 user-scalable/maximum-scale/minimum-scale;刘海屏加 viewport-fit=cover。
**关联(seealso)**: core-viewport、mobile-font-size;[mobile-seo.md](../mobile-seo.md)、[head-elements.md](../head-elements.md)

#### mobile-overflow
- 名称/类型: 横向滚动(源表 ID `mobile-horizontal-scroll`) —— issue/warning · 优先级 high · 输出 WARN/CRITICAL(源表 warn/fail;分型口径源表未公布[待核])
**这意味(what)**: 移动视口(常见 ~375px)下页面出现横向滚动——有元素超出视口宽度。
**为什么(why)**: 横向滚动是移动可用性的一票否决项:双轴滚动让用户极易迷失,"内容超出视口"长期是移动可用性评估的硬伤形态。常见肇因:固定宽度元素(表格/图/iframe 未 max-width)、绝对定位残片、长串不换行(裸 URL)。
**触发(trigger)**: 1) ~375px 视口渲染;2) scrollWidth > innerWidth 即触发;3) warn/fail 分型[待核:常见按超出幅度与是否整页双轴滚动分档]。
**不修的条件(caveat)**: 局部横向滚动区(轮播/代码块/宽表)是可用交互形态,本条针对整页级双轴滚动;命中后先定位溢出元素,别全局 overflow-x:hidden 掩盖——那只是把症状藏给用户。
**修复(fix)**: img/iframe/video 加 max-width:100%;宽表包横向滚动容器或改卡片式;fixed 宽度改响应式;pre/长 URL 强制换行。
**关联(seealso)**: mobile-font-size、mobile-interstitial;[mobile-seo.md](../mobile-seo.md)

#### mobile-interstitial
- 名称/类型: 侵扰性插页(源表 ID `mobile-interstitials`) —— issue/warning · 优先级 high · 输出 WARN/CRITICAL(源表 warn/fail;官方三形态+豁免清单)
**这意味(what)**: 用户从搜索进入后立即遭遇遮蔽主内容的弹窗/独立插页页,或 cookie/GDPR/年龄验证/登录类横幅采用违规形态(全屏、难关闭、进入即弹)。
**为什么(why)**: Google 2016-08-23 宣布,2017-01-10 之后从移动搜索结果进入后内容不易获取的页面「may not rank as highly」([博文](https://developers.google.com/search/blog/2016/08/helping-users-easily-access-content-on),核对 2026-10-21)。官方列举的三种形态:进入即弹遮主内容的弹窗、须关闭才能看内容的独立插页页、首屏伪内容横幅。豁免清单:法律必需的 cookie/GDPR 横幅(合规形态:非全屏、易关)、登录墙(公开内容有免费替代)、占合理比例且可关的横幅——政策全拆解见 [mobile-seo.md](../mobile-seo.md) 2.5 节。
**触发(trigger)**: 进入页面即检测遮罩(全屏 overlay/独立插页跳转);按"进入即弹/遮蔽比例/关闭难度"分型 warn/fail[分型口径源表未公布,待核]。
**不修的条件(caveat)**: 合规横幅不(必然)触发惩罚——判定看形态不看业务目的,所以一般建议 cookie/年龄类用非全屏、易关的形态。但"合规必需"不等于"任意形态免责",全屏 GDPR 墙同样在打击面内。
**修复(fix)**: 弹窗改用户交互后触发;横幅收紧为可关的顶部条;插页页移除;关闭目标(×)至少 24×24 CSS px(WCAG 2.5.8),最好 44×44。
**关联(seealso)**: mobile-overflow、legal-cookie-consent;[mobile-seo.md](../mobile-seo.md)

#### mobile-image-maps
- 名称/类型: 客户端图像地图 —— warning · 优先级 low · 输出 WARN(源表 warn)
**这意味(what)**: 页面用 `<map>`/`<area>` 客户端图像地图做导航或交互——固定像素坐标的热区不适配。
**为什么(why)**: image map 的热区是绝对像素坐标:响应式图片缩放后热区不再对位(点 A 命中 B),触屏精度下小热区几乎不可点;屏幕阅读器对 area 的支持参差。这是 90 年代遗产技术,现代替代(CSS 定位/SVG 热区/拆分图片)全面更优。
**触发(trigger)**: 页面含 `<map>`+`<img usemap>` 即 warn(热区数量的分级口径[待核])。
**不修的条件(caveat)**: image map 不(直接)影响排名(引擎能提取 area href),然而触屏交互失准是可用性实伤,所以一般建议重构。但按渲染尺寸动态换算坐标的实现(热区随图等比缩放)可用,命中后先确认是否自适应。
**修复(fix)**: 导航型改列表/按钮组;图形热点改 SVG 内嵌 `<a>`(可缩放+可访问名);必须保留时热区坐标按渲染尺寸动态计算。
**关联(seealso)**: mobile-overflow;[semantic-html.md](../semantic-html.md)

#### mobile-parity [待核 ID]
- 名称/类型: 移动-桌面内容平价(parity 五条;源表 ID `mobile-parity-content/-title/-canonical/-structured-data/-links`) —— issue/warning · 优先级 high · 输出 CRITICAL/WARN(源表现行:content、title+description=warn/fail,canonical=fail,structured-data=fail(JSON-LD 桌面有移动无),links(移动至少为桌面一半)=warn;`--mobile` 双渲染对比)
**这意味(what)**: 同一 URL 的移动与桌面渲染(或 m. 站双域)内容不对等:主内容/标题描述/canonical 出入、桌面有移动无的 JSON-LD、内链数量不可比。
**为什么(why)**: Google 用移动版内容做索引(2024-07-05 起只用 Googlebot Smartphone 抓取,[公告](https://developers.google.com/search/blog/2024/06/mobile-indexing-vlast-final-final.doc)),桌面专属内容不参与索引;m. 站遗留时瘦移动版被索引,www 的优化投入落空。JSON-LD 桌面有移动无是最隐蔽的形态:富结果资格随移动版消失。parity 检查法(双视口抓取 diff、GSC 按设备拆分、Live Test)见 [mobile-seo.md](../mobile-seo.md) 1.4 节(其 diff >20%/>50% 旗线是本套件口径)。
**触发(trigger)**: `--mobile` 双渲染(~375px 与 ~1280px)对比:1) 主内容文本量/title+description/canonical 不一致 → warn/fail[分型待核];2) 桌面 JSON-LD 移动缺失 → fail;3) 移动 `a[href]` 数不足桌面一半 → warn(源表现行)。
**不修的条件(caveat)**: parity 差异不(必然)是错——大屏增强内容(桌面才显示的对比图)被移动省略是响应式常态,移动优先索引按移动版算,损失的是增强加分而非硬伤。但结构性差异(schema 缺失/内容整段缺失)必须修平。
**修复(fix)**: 结构化数据与关键注解两端同源输出;m. 站遗留按 [mobile-seo.md](../mobile-seo.md) 1.3 风险清单收敛到响应式;双模板站点建 parity CI diff。
**关联(seealso)**: js-content-dependency、js-meta-drift、mobile-viewport-config;[mobile-seo.md](../mobile-seo.md)、[rendering-seo.md](../rendering-seo.md)
