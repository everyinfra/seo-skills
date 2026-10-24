# 审计规则目录 · Accessibility

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### Accessibility(36 条,权重 7%)

对比度 **≥4.5:1 正文/3:1 大字**;触控目标 **≥44×44 CSS px**(源表;出自 WCAG 2.5.5 AAA,AA 级 2.5.8 为 24×24 或留足间距);交互元素须可访问名(aria-label/文本/title);focus 样式可见;表单 label(placeholder 不算);标题不跳级;landmark(main/nav/header/footer);描述性链接文本;skip-to-content 链接;表格 th+scope;视频字幕/文稿;viewport 禁缩放(user-scalable=no/maximum-scale=1)=fail;aria-hidden 包可聚焦元素=fail;**ARIA 角色/属性拼错浏览器静默丢弃(aria-lable→aria-label)=fail**;accesskey 唯一;**ID 重复致 aria-labelledby/label for 解析到第一个匹配=fail(svg 内 url(#id) 引用的 clipPath 豁免)**;空标题=fail;一控件一 label;同文本链接须同目的地;iframe/object 须 title/替代文本;`<input type=image>` 须 alt;**可访问名须含可见文本(语音用户"说所见")**;按钮有名;email/tel 输入配对 autocomplete token;lang 与 xml:lang 一致;html/body 禁 aria-hidden;ARIA widget 须有所需父子角色(tab 在 tablist 内/option 在 listbox 内);列表只含 li;**恰一个 main landmark**;role=none/presentation 不被 ARIA/可聚焦性反证;alt 不重复相邻链接/图注文本;img 角色 SVG 须可访问名;表格用 caption 不用跨列首行;**tabindex 禁正值**;元素级 lang 合法 BCP 47。

**SEOmator 原版现行 ID 与档位(132d2384,核对 2026-10-21)**:fail=`a11y-zoom-disabled`、`a11y-aria-hidden-focusable`、`a11y-aria-valid`、`a11y-empty-heading`、`a11y-iframe-title`、`a11y-input-image-alt`、`a11y-aria-hidden-body`、`a11y-list-structure`、`a11y-object-alt`、`a11y-svg-img-alt`;warn/fail=`a11y-aria-labels`、`a11y-focus-visible`、`a11y-form-labels`、`a11y-heading-order`、`a11y-link-text`、`a11y-table-headers`、`a11y-video-captions`、`a11y-duplicate-id`、`a11y-main-landmark`;warn=其余(`a11y-color-contrast`、`a11y-landmark-regions`、`a11y-skip-link`、`a11y-touch-targets`、`a11y-tabindex-positive`、`a11y-autocomplete` 等)。**`a11y-color-contrast` 现行只是对内联样式颜色的启发式检查,页面没有内联颜色时不测量**,下文 a11y-contrast 的「渲染后算 computed 对比度」是本套件对完整做法的描述,不是 SEOmator 原版行为。家族名与原版 ID 的对应:tabindex↔tabindex-positive、aria-hidden↔aria-hidden-focusable、aria-hidden-root↔aria-hidden-body、aria-typo↔aria-valid、accessible-name↔aria-labels、form-label↔form-labels、one-label-per-control↔form-multiple-labels、autocomplete-token↔autocomplete、accesskey↔accesskey-unique、name-contains-visible↔label-name-mismatch、heading-hierarchy↔heading-order、single-main↔main-landmark、landmarks↔landmark-regions、link-consistency↔identical-links-purpose、media-transcripts↔video-captions、svg-name↔svg-img-alt、alt-duplicate↔redundant-alt、aria-parent-child↔aria-required、role-presentation↔presentation-role-conflict、touch-target↔touch-targets、contrast↔color-contrast。

**解释层(32 条,第四批;ID 未公布原文,按家族命名法推得并标 [待核]。归并边界:alt 家族已归 Images 节 images-alt-present 三条、语言码两条已并入 i18n-lang-consistency、viewport 禁缩放已并入 mobile-viewport-config,不重复。why 只写无障碍理由;原"SEO 面"推断(引擎读无障碍树、aria-hidden 影响索引等)无一手出处,已删,仅保留有 Google 文档支持的几句)**

#### a11y-contrast [待核 ID]
- 名称/类型: 文本对比度不足 —— warning · 优先级 medium · 输出 WARN(源表:≥4.5:1 正文/3:1 大字;档位见节首对照行)
**这意味(what)**: 文本与背景的前景/背景对比度低于阈值:正文 <4.5:1,大字(约 ≥18pt/14pt 粗体) <3:1。
**为什么(why)**: 无障碍:低对比对低视力/老年/强光环境用户直接不可读;WCAG 1.4.3 要求文本对比度至少 4.5:1,大号文本至少 3:1([W3C](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html),核对 2026-10-21)。
**触发(trigger)**: 渲染后计算文本节点 computed 前景/背景对比度(图片背景的采样口径[待核]):正文 <4.5:1、大字 <3:1 即 warn。
**不修的条件(caveat)**: 对比度不(直接)影响排名,然而 4.5:1 是可读性工程下限,所以一般建议正文全站达标。但 disabled 态/水印等非必要信息文本豁免;改版走设计系统调 token,别逐页打补丁。
**修复(fix)**: 设计 token 化色对并预检 ≥4.5:1;灰阶层压进合规区间;CI 对主题色组合跑对比度断言。
**关联(seealso)**: mobile-font-size、content-readability;[semantic-html.md](../semantic-html.md)、[validation-guide.md](../validation-guide.md)

#### a11y-touch-target [待核 ID]
- 名称/类型: 触控目标过小 —— warning · 优先级 medium · 输出 WARN(源表:44×44 CSS px,出自 WCAG 2.5.5 AAA;AA 级 2.5.8 为 24×24;档位未单列)
**这意味(what)**: 可点击/可触摸元素(按钮/链接/表单控件)的触达区域小于 44×44 CSS 像素。
**为什么(why)**: 无障碍:小目标难倒运动障碍与触屏用户。WCAG 2.5.8(AA)要求目标至少 24×24 CSS px 或留足间距,44×44 是 2.5.5(AAA)([W3C](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html))。
**触发(trigger)**: 渲染后测量交互元素的可触达盒(含 padding/伪元素扩展):<44×44 即 warn(源表口径;按 WCAG 2.5.8 只有 <24×24 且间距不足才算不达标,行内文字链豁免)。
**不修的条件(caveat)**: 触控尺寸不影响桌面排名,然而移动端它是可用性硬阈值,所以一般建议交互件全站达标。但正文行内文字链的密排形态天然豁免——本条管的是按钮/控件/导航项等关键交互件。
**修复(fix)**: 按钮/控件最小热区 44×44(padding 或伪元素扩展,视觉尺寸可小);间距 ≥8px 防误触;图标按钮扩热区而非放大图标。
**关联(seealso)**: mobile-interstitial、mobile-font-size;[mobile-seo.md](../mobile-seo.md)

#### a11y-accessible-name [待核 ID]
- 名称/类型: 交互元素无可访问名 —— warning · 优先级 high · 输出 WARN(源表:aria-label/文本/title;档位见节首对照行)
**这意味(what)**: 链接/按钮/输入等交互元素没有可访问名(accessible name)——无文本内容、无 aria-label、无 title。
**为什么(why)**: 无障碍:屏幕阅读器按可访问名朗读控件,无名控件只念"按钮",用户不知道会发生什么;语音控制用户更是无法下指令("点'提交'按钮"落空)。SEO 面唯一有出处的一点:空 `<a>` 时 Google 可用 title 作锚文本,图片链接用 img 的 alt 作锚文本([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable))。
**触发(trigger)**: 交互元素(a/button/input/select/textarea)按 accname 算法计算(优先级:aria-labelledby → aria-label → label/alt 等原生标签 → 内容文本 → title,[accname 1.2](https://www.w3.org/TR/accname-1.2/)):结果为空即 warn。
**不修的条件(caveat)**: 可访问名不影响排名本身,然而它是无障碍合规与语义完整性的交叉点,所以一般建议全配。但 aria-hidden 标记的装饰性冗余控件不判——那是 a11y-aria-hidden 家族的辖区。
**修复(fix)**: 图标按钮加 aria-label("打开菜单");文本按钮靠内容文本;title 只作兜底(触屏不可见);配合 a11y-name-contains-visible 的"名含可见文本"要求。
**关联(seealso)**: a11y-button-name、a11y-svg-name、images-alt-present;[semantic-html.md](../semantic-html.md)

#### a11y-button-name [待核 ID]
- 名称/类型: 按钮无名 —— warning · 优先级 medium · 输出 WARN(源表:按钮有名;与 a11y-accessible-name 同族,按钮为最高频命中面)
**这意味(what)**: `<button>` 元素没有任何可访问名(空文本且无 aria-label)。
**为什么(why)**: 无障碍:无名按钮在 SR 里是一列"按钮、按钮",播放器/弹窗/表单里的图形按钮全部不可用。
**触发(trigger)**: `<button>`(含 role=button)accessible name 计算为空即 warn。
**不修的条件(caveat)**: 单个命中可能是刻意的装饰冗余(双重关闭按钮),所以一般建议模板级批量治理而非逐个补。但 aria-hidden 标记的冗余控件不判。
**修复(fix)**: 组件库给图标按钮内置 aria-label 槽位;文案缺失(空 i18n key)构建期报错;验收用 SR 模式抽查关键流程。
**关联(seealso)**: a11y-accessible-name、a11y-form-label;[semantic-html.md](../semantic-html.md)

#### a11y-name-contains-visible [待核 ID]
- 名称/类型: 可访问名不含可见文本 —— warning · 优先级 low · 输出 WARN(源表:可访问名须含可见文本,语音用户"说所见";档位见节首对照行)
**这意味(what)**: 元素的可访问名(aria-label/aria-labelledby)与其可见文本不一致——可见写"购买",可访问名却是"加入购物车 submit"。
**为什么(why)**: 无障碍:语音控制用户"说所见"——对着屏幕念"点击购买"命中不了名为"加入购物车"的按钮;SR 用户听到的与看到的也不同,两套词两套认知。
**触发(trigger)**: 1) 元素同时有可见文本与 aria-label/aria-labelledby;2) 可访问名归一化后不包含可见文本字符串即 warn(源表"须含"口径,即扩写方向合法、替换方向违例)。
**不修的条件(caveat)**: 合法的扩写场景:可见文本是缩写/短词,aria-label 给完整表述("菜单"→"主导航菜单")——名 ⊃ 可见文本合法;名与可见文本无关才是问题。
**修复(fix)**: 默认不覆写——有可见文本就不加 aria-label;确需扩写时保留原词;关键词堆砌进 aria-label 的全部清除。
**关联(seealso)**: a11y-accessible-name、links-anchor-generic;[semantic-html.md](../semantic-html.md)

#### a11y-focus-visible [待核 ID]
- 名称/类型: 焦点样式不可见 —— warning · 优先级 medium · 输出 WARN(源表:focus 样式可见;档位见节首对照行)
**这意味(what)**: 可聚焦元素被聚焦时没有任何可见指示——`outline:none` 且无替代 focus 样式。
**为什么(why)**: 无障碍:键盘用户(运动障碍/高级用户/部分 AT)靠焦点环知道"现在在哪",全局删 outline 等于蒙眼操作。
**触发(trigger)**: 1) 样式表出现 :focus{outline:none/0} 且无 :focus-visible 替代即触发;2) 渲染后聚焦元素无可感知的指示变化(判定口径[待核])即 warn。
**不修的条件(caveat)**: 焦点样式不影响排名,然而全局删焦点环是"看起来更干净"的经典反模式,所以一般建议 :focus-visible 替代而非删除。但鼠标点击态的 :focus 抑制(focus-visible 分流)是正当精细化,不判。
**修复(fix)**: :focus-visible 给 ≥2px 对比指示(outline/box-shadow);别全局 outline:none;验收标准=纯键盘走通主流程(登录→下单)。
**关联(seealso)**: a11y-tabindex、links-onclick;[semantic-html.md](../semantic-html.md)

#### a11y-tabindex [待核 ID]
- 名称/类型: 正值 tabindex —— warning · 优先级 medium · 输出 WARN(源表:tabindex 禁正值;档位见节首对照行)
**这意味(what)**: 元素带正整数 tabindex(tabindex="1"/"3"),覆盖文档流的自然 Tab 顺序。
**为什么(why)**: 无障碍:正 tabindex 把焦点顺序钉死在作者想象的顺序上,DOM 变化(插组件/异步内容)后跳转顺序错乱,键盘用户在页面里"瞬移"。
**触发(trigger)**: 任一元素 tabindex 属性值为正整数即 warn(tabindex=0/-1 合法:0 加入自然序、-1 可编程聚焦)。
**不修的条件(caveat)**: 正 tabindex 不影响排名,然而它几乎没有正当用例(模态框焦点管理用 -1+focus()),所以一般建议全站清零。但遗留 widget 库依赖正值的,先建组件焦点管理再清。
**修复(fix)**: 删正值——自然顺序靠 DOM 顺序表达;自定义组件用 tabindex=-1 + element.focus();模态框做 focus trap。
**关联(seealso)**: a11y-focus-visible、a11y-aria-parent-child;[semantic-html.md](../semantic-html.md)

#### a11y-skip-link [待核 ID]
- 名称/类型: 缺 skip-to-content 链接 —— warning · 优先级 low · 输出 WARN(源表:skip-to-content 链接;档位见节首对照行)
**这意味(what)**: 页面没有"跳到主内容"链接——键盘/SR 用户每页都要 Tab 过整条导航才能到正文。
**为什么(why)**: 无障碍:键盘用户每次换页从页头 Tab 二十几个导航链接,skip 链是满足 WCAG 2.4.1 Bypass Blocks 的常见手段([W3C](https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks.html),核对 2026-10-21)。
**触发(trigger)**: 页面首部(body 前几个焦点元素)无指向主内容锚点的跳转链接(href="#main"/#content 形态[待核])即 warn。
**不修的条件(caveat)**: 短导航页(≤5 个链接)的 skip 链价值低,所以一般建议导航项多的模板配。但配了就别 display:none 隐藏——要"聚焦时可见"。
**修复(fix)**: body 首元素加 `<a href="#main" class="skip-link">跳到主内容</a>`;CSS 默认移出视口、:focus 时归位;与 main landmark 同步(见 a11y-landmarks)。
**关联(seealso)**: a11y-landmarks、a11y-single-main;[semantic-html.md](../semantic-html.md)

#### a11y-accesskey [待核 ID]
- 名称/类型: accesskey 重复 —— warning · 优先级 low · 输出 WARN(源表:accesskey 唯一;档位见节首对照行)
**这意味(what)**: 多个元素绑定了同一个 accesskey 快捷键。
**为什么(why)**: 无障碍:重复 accesskey 只有浏览器选中的那个生效,用户记住的快捷键在半数页面失灵;accesskey 还与浏览器/AT 自身快捷键冲突(Alt+字母多被占用),现代最佳实践已弱化它。
**触发(trigger)**: 全页收集 accesskey 属性值;同一字符出现 ≥2 次即 warn。
**不修的条件(caveat)**: accesskey 不影响 SEO 且现代站点多数已弃用,所以一般建议直接清理而非修复映射。但确要保留(工具型内网应用)时保证全站唯一并公示键位表。
**修复(fix)**: 优先删除 accesskey(改可见快捷键说明);保留时全站唯一并避开浏览器保留组合。
**关联(seealso)**: a11y-duplicate-id、a11y-focus-visible;[semantic-html.md](../semantic-html.md)

#### a11y-form-label [待核 ID]
- 名称/类型: 表单控件无 label —— warning · 优先级 high · 输出 WARN(源表:表单 label,placeholder 不算;档位见节首对照行)
**这意味(what)**: 表单控件(input/select/textarea)没有关联 label——无 `<label for>`、无 aria-label(ledBy);placeholder 占位文本不算 label。
**为什么(why)**: 无障碍:SR 对 placeholder 的支持参差,且输入后 placeholder 消失——用户回改时字段名没了;label 的点击命中区同时扩大触控目标。
**触发(trigger)**: 每个 input(除 hidden/button/submit 等自带语义型[豁免清单待核])/select/textarea 计算 label 关联(for=id 匹配/aria-label/aria-labelledby):结果为空即 warn;placeholder 存在不豁免。
**不修的条件(caveat)**: 极简搜索框(放大镜图标+placeholder)是广被接受的形态,可用 aria-label 补名;但任何收集关键信息(地址/支付)的表单没有 label 都是硬伤。
**修复(fix)**: `<label for>` 绑定;图标-only 控件用 aria-label;placeholder 只作示例提示;一控件一 label(见 a11y-one-label-per-control)。
**关联(seealso)**: a11y-one-label-per-control、a11y-autocomplete-token、a11y-accessible-name;[semantic-html.md](../semantic-html.md)

#### a11y-one-label-per-control [待核 ID]
- 名称/类型: 一控件多 label —— warning · 优先级 low · 输出 WARN(源表:一控件一 label;档位见节首对照行)
**这意味(what)**: 同一表单控件被多个 label 关联(多个 for 指向同一 id,或嵌套 label 与显式 for 并存)。
**为什么(why)**: 无障碍:多 label 时 AT 读取行为不一(读首个/拼接),用户听到的字段名不可预期。
**触发(trigger)**: 按 for=id 聚合:任一控件的关联 label 计数 >1 即 warn(嵌套+显式并存的计数口径[待核])。
**不修的条件(caveat)**: 多 label 极少有正当用例,所以一般建议收敛为一。但控件用 aria-labelledby 引用多个 id 是合法的多源命名(如"账单 地址"),不属本条。
**修复(fix)**: 每控件一个 label for;辅助说明文字改 aria-describedby(描述而非命名);CI 断言 for 值与控件 id 一一对应。
**关联(seealso)**: a11y-form-label、a11y-duplicate-id;[semantic-html.md](../semantic-html.md)

#### a11y-autocomplete-token [待核 ID]
- 名称/类型: email/tel 输入缺 autocomplete token —— warning · 优先级 low · 输出 WARN(源表:email/tel 输入配对 autocomplete token;档位见节首对照行)
**这意味(what)**: type=email 的输入框没配 autocomplete="email",type=tel 没配 autocomplete="tel"。
**为什么(why)**: 无障碍:autocomplete token 是 AT 与密码管理器/浏览器自动填充的对接协议——正确 token 让运动障碍用户一次完成表单,自编 token(autocomplete="email-address")静默失效。
**触发(trigger)**: type=email 的 autocomplete 不含 "email"、type=tel 不含 "tel"(精确 token 按 HTML 规范词表[待核:源表按这两个 token 判])即 warn。
**不修的条件(caveat)**: token 配错与没配等效,所以一般建议整表按 HTML autocomplete 词表配全(name/street-address 等同族)。但一次性验证码输入配 autocomplete="one-time-code" 或禁填充属安全设计。
**修复(fix)**: email→autocomplete="email";tel→autocomplete="tel"(区号分体用 tel-national 系);整表按词表补全并做密码管理器回归。
**关联(seealso)**: a11y-form-label;[semantic-html.md](../semantic-html.md)

#### a11y-landmarks [待核 ID]
- 名称/类型: landmark 角色缺失 —— warning · 优先级 medium · 输出 WARN(源表:landmark main/nav/header/footer;档位见节首对照行)
**这意味(what)**: 页面缺 HTML5 landmark 语义:无 `<main>`/`<nav>`/`<header>`/`<footer>`(或对应 role),整页是 div 沙漠。
**为什么(why)**: 无障碍:SR 用户靠 landmark 区跳转(到导航/到主内容),无 landmark 只能逐元素线性听。
**触发(trigger)**: 渲染后解析 landmark 元素(main/nav/header/footer/aside 及对应 role):main 或 nav 计数为 0 即 warn(header/footer 缺失是否同判[待核:footer 常并入分组判定])。
**不修的条件(caveat)**: landmark 不(直接)影响排名,然而它是语义 HTML 骨架层,所以一般建议模板级配齐。但组件化页面滥用 header/footer(每卡片一个)会稀释语义——main 的唯一性另由下条管。
**修复(fix)**: 模板用原生 landmark 元素(role 兜底仅限 div 不可避免时);导航区用 aria-label 区分(主导航/面包屑/页脚导航);main 恰一个(见 a11y-single-main)。
**关联(seealso)**: a11y-single-main、a11y-skip-link、links-chrome-inbound;[semantic-html.md](../semantic-html.md)

#### a11y-single-main [待核 ID]
- 名称/类型: main landmark 数量错误 —— warning · 优先级 medium · 输出 WARN(源表:恰一个 main landmark;档位见节首对照行)
**这意味(what)**: 页面的 main landmark 数量 ≠1:零个(缺失面与 a11y-landmarks 重叠)或多个(组件化误用)。
**为什么(why)**: 无障碍:HTML 规范规定一个文档不得有多于一个未带 hidden 的 main([WHATWG](https://html.spec.whatwg.org/multipage/grouping-content.html));多个 main 时"跳到主内容"的落点不可预期。
**触发(trigger)**: 渲染后 `<main>`/role=main 计数 0 或 >1 即 warn(0 个已由 a11y-landmarks 报缺失,本条侧重 >1 与计数口径)。
**不修的条件(caveat)**: 合法例外是切换式视图(同一时刻只有一个 main 可见)——SPA 若 DOM 同时存在多个视图,用 hidden 属性保证只一个对 AT 与爬虫暴露。
**修复(fix)**: 模板级恰一个 `<main>`;SPA 路由切换时旧视图加 hidden 或移除;组件不私自包 main(插槽组件用 div)。
**关联(seealso)**: a11y-landmarks、a11y-skip-link;[semantic-html.md](../semantic-html.md)

#### a11y-heading-hierarchy [待核 ID]
- 名称/类型: 标题跳级(无障碍视角) —— warning · 优先级 low · 输出 WARN(源表:标题不跳级;Content 节同构条已写 content-heading-family,本条为 Accessibility 类计分视角,阈值同源不重抄)
**这意味(what)**: 标题层级跳跃(H1 直接 H3、H2 掉到 H5),语义树断档。
**为什么(why)**: 无障碍:SR 用户按标题级别导航(按 2 级跳/按 3 级跳),跳级让导航树缺枝——H1 后直接 H3,按 2 级导航的用户整节内容不可达。SEO:标题顺序对 Google 搜索无所谓,只对屏幕阅读器重要([SEO 入门指南](https://developers.google.com/search/docs/fundamentals/seo-starter-guide))。
**触发(trigger)**: 相邻标题级别差 >1 即触发(阈值与 content-heading-family 同源照抄,不另立)。
**不修的条件(caveat)**: 设计系统组件自带级别造成的技术性跳级,豁免口径见 content-heading-family;修复优先级低于空标题(下条)。
**修复(fix)**: 见 content-heading-family(模板按语义排级、组件级别参数化)。
**关联(seealso)**: content-heading-family、a11y-empty-heading;[semantic-html.md](../semantic-html.md)

#### a11y-empty-heading [待核 ID]
- 名称/类型: 空标题 —— issue · 优先级 medium · 输出 CRITICAL(源表 fail;两轴校准:输出随源表 fail,建议优先级按卫生级降 medium——存在但残缺的坏信号,非主动矛盾)
**这意味(what)**: 标题元素(h1-h6)存在但内容为空——无文本、无可访问名(aria-label)。
**为什么(why)**: 无障碍:空标题在 SR 标题列表里显示为空行,按标题速览的用户遇到"无名节",导航价值归零还制造噪音。
**触发(trigger)**: 任一 h1-h6 的文本(含 img alt 贡献与 aria-label)归一化后为空即 fail 档。
**不修的条件(caveat)**: 刻意的纯图标节标题可用 aria-label 补名后豁免;真无内容的标题应条件渲染跳过,而不是渲染空壳。
**修复(fix)**: 空字段时整个标题元素不渲染(v-if/条件模板);图标节标题加 aria-label;CI 对渲染产物断言无空标题。
**关联(seealso)**: a11y-heading-hierarchy、content-deploy-hygiene、content-heading-family;[semantic-html.md](../semantic-html.md)

#### a11y-link-text [待核 ID]
- 名称/类型: 链接文本无信息量 —— warning · 优先级 medium · 输出 WARN(源表:描述性链接文本;Links 节 links-anchor-generic 同源,本条从 Accessibility 类计分补判)
**这意味(what)**: 链接的可访问名不含目标信息——泛化词(click here/read more)、裸 URL 或无意义图标。
**为什么(why)**: 无障碍:SR 用户常调出"链接列表"脱离上下文浏览,一列 "read more" 完全不可用——链接文本就是它的全部语境。SEO:Google 用锚文本理解目标页,click here/read more 一类泛化锚文本不好([链接文档](https://developers.google.com/search/docs/crawling-indexing/links-crawlable))。
**触发(trigger)**: 链接可访问名命中泛化词表或为纯 URL 字符串即 warn(词表与 links-anchor-generic 共用[待核])。
**不修的条件(caveat)**: 转化文案锚("免费试用")的取舍豁免见 links-anchor-generic;本条不重复修复细则,修复一次两规则双绿。
**修复(fix)**: 见 links-anchor-generic(锚含目标主题、图标链补 aria-label);裸 URL 换描述性锚或页面标题。
**关联(seealso)**: links-anchor-generic、a11y-name-contains-visible;[semantic-html.md](../semantic-html.md)

#### a11y-link-consistency [待核 ID]
- 名称/类型: 同文本链接不同目的地 —— issue/warning · 优先级 medium · 输出 WARN(源表:同文本链接须同目的地;档位见节首对照行)
**这意味(what)**: 页面里两处链接的可访问名完全相同,href 却指向不同地址。
**为什么(why)**: 无障碍:SR/语音用户按链接名操作,同名不同目的地让指令二义——念"产品页"命中哪个全凭 Tab 位置。
**触发(trigger)**: 全页按可访问名归一化聚合链接;同名的 href 集合去重后 >1 即 warn(大小写/空白归一化口径[待核])。
**不修的条件(caveat)**: 同目的地的同名重复链接(面包屑末级与正文链)不判;"阅读更多"指向不同文章的形态该修锚文本而非删链接——与 links-anchor-generic 联手覆盖。
**修复(fix)**: 同目的地保持一致;不同目的地的链接文本差异化(带目标主题);模板循环变量注入锚文本。
**关联(seealso)**: a11y-link-text、links-anchor-generic;[semantic-html.md](../semantic-html.md)

#### a11y-table-headers [待核 ID]
- 名称/类型: 数据表缺表头关联 —— warning · 优先级 medium · 输出 WARN(源表:表格 th+scope;档位见节首对照行)
**这意味(what)**: 数据表(对比表/报价表/规格表)的单元格没有表头关联:无 `<th>`,或有 th 但缺 scope 属性/headers-id 映射。
**为什么(why)**: 无障碍:SR 按表头+单元格报坐标("价格 第3列 ¥299"),无 scope 的表读出来是一串无上下文的数字,复杂数据表等于不可用。
**触发(trigger)**: `<table>` 含 ≥2 列数据(简单双列键值表豁免口径[待核])但表头单元格无 scope(或无 headers/id 映射)即 warn。
**不修的条件(caveat)**: 布局用表(邮件模板遗留)与数据表要分开——布局表该删不该补 scope;双列键值表(`<th>键</th><td>值</td>`)天然可读,缺 scope 影响小。
**修复(fix)**: 表头单元格 `<th scope="col"/"row">`;复杂表加 id/headers 映射;布局表改 CSS grid;配 caption(见 a11y-table-caption)。
**关联(seealso)**: a11y-table-caption、a11y-landmarks;[semantic-html.md](../semantic-html.md)

#### a11y-table-caption [待核 ID]
- 名称/类型: 表格标题用跨列首行替代 —— warning · 优先级 low · 输出 WARN(源表:表格用 caption 不用跨列首行;档位见节首对照行)
**这意味(what)**: 表格标题被写成第一行的跨列单元格(`<td colspan=全表宽>`),而不是 `<caption>` 元素。
**为什么(why)**: 无障碍:SR 进入表格前先播报 caption——用首行单元格冒充标题时,用户进了表还不知道表是什么,跨列首行在导航模式里只是普通数据格。
**触发(trigger)**: 表格首行为跨全部列的单单元格文本(疑似标题)且无 `<caption>` 即 warn(疑似标题的判定口径[待核])。
**不修的条件(caveat)**: 首行若是真实数据(日期行/首条记录)不判;存量表格批量改造收益有限时,优先保证新表用 caption。
**修复(fix)**: 跨列首行改 `<caption>`(可 CSS 定位到任意位置);新表模板默认开 caption 槽位。
**关联(seealso)**: a11y-table-headers;[semantic-html.md](../semantic-html.md)

#### a11y-media-transcripts [待核 ID]
- 名称/类型: 视频缺字幕/文稿 —— warning · 优先级 medium · 输出 WARN(源表:视频字幕/文稿;档位见节首对照行)
**这意味(what)**: 页面内嵌视频(`<video>`/iframe 播放器)没有字幕轨道(track)或页内文稿(transcript)。
**为什么(why)**: 无障碍:聋哑/重听用户与静音自动播放场景(社交分发常态)完全依赖字幕——无字幕的视频内容对这部分用户不存在。
**触发(trigger)**: 1) `<video>` 无 `<track kind="captions|subtitles">` 即 warn;2) iframe 嵌入按页内有无 transcript 文本判(判定口径[待核])。
**不修的条件(caveat)**: 第三方平台 iframe 的字幕你控制不了,能做的是页内文稿与描述;自动生成字幕质量差时,重要视频补人工校对版。
**修复(fix)**: `<track kind="captions" srclang label>` 本地字幕;页内 transcript 与 VideoObject 同源;视频分发全案见 [video-geo-guide.md](../../content/video-geo-guide.md)。
**关联(seealso)**: sd-required-fields(VideoObject);[video-geo-guide.md](../../content/video-geo-guide.md)

#### a11y-iframe-title [待核 ID]
- 名称/类型: iframe/object 缺 title —— warning · 优先级 medium · 输出 WARN(源表:iframe/object 须 title/替代文本;档位见节首对照行)
**这意味(what)**: `<iframe>`(或 `<object>`)没有 title 属性(或等价替代文本)。
**为什么(why)**: 无障碍:SR 把 iframe 当独立浏览区,进入前读 title——无名框架只报"框架",用户不知道里面是广告、表单还是地图,键盘焦点进入无名框架时尤其迷失。
**触发(trigger)**: 任一 `<iframe>`/`<object>` 无 title 或 title 空白即 warn(装饰性隐藏框架的豁免口径[待核])。
**不修的条件(caveat)**: 技术 iframe(埋点/支付回调)用 title="(hidden)" 或 aria-hidden+height=0 处理,不影响判定;视觉无框嵌入(无缝地图)更需要 title 说明身份。
**修复(fix)**: `<iframe title="Google 地图:公司位置">`——每处嵌入给具体身份而非"iframe";装饰性技术框架加 hidden 语义。
**关联(seealso)**: a11y-accessible-name、sd-required-fields(VideoObject);[semantic-html.md](../semantic-html.md)

#### a11y-svg-name [待核 ID]
- 名称/类型: img 角色 SVG 缺可访问名 —— warning · 优先级 medium · 输出 WARN(源表:img 角色 SVG 须可访问名;档位见节首对照行)
**这意味(what)**: 承载信息的内联 SVG(role=img 或视觉等价于内容图)没有可访问名——无 `<title>`/`<desc>`、无 aria-label。
**为什么(why)**: 无障碍:SR 默认跳过纯图形,role=img 后会尝试播报但无名则读不出内容——信息图形对盲用户完全不存在。SEO:Google 图片文档建议内联 svg 用 `<title>` 提供替代文本([图片 SEO 文档](https://developers.google.com/search/docs/appearance/google-images))。
**触发(trigger)**: 内联 svg 带 role="img"(或被判为信息图形[判定口径待核])且 accessible name(svg>title 或 aria-label)为空即 warn。
**不修的条件(caveat)**: 装饰性 SVG 的正确做法是 aria-hidden="true"(跳过)而非补名——补名反而制造噪音;判定标准是"这图形承载信息吗"。
**修复(fix)**: 信息 SVG:`<svg role="img" aria-label="描述">` 或内嵌 `<title>`;装饰 SVG:aria-hidden="true";可交互 SVG 图标按 a11y-accessible-name 给名。
**关联(seealso)**: a11y-accessible-name、images-alt-present;[semantic-html.md](../semantic-html.md)

#### a11y-alt-duplicate [待核 ID]
- 名称/类型: alt 复读相邻文本 —— warning · 优先级 low · 输出 WARN(源表:alt 不重复相邻链接/图注文本;档位见节首对照行)
**这意味(what)**: 图片的 alt 与紧邻的链接文本或 figcaption 图注完全相同——SR 用户同一句话听两遍。
**为什么(why)**: 无障碍:图文卡片(图+标题链)是最常见布局,alt=标题文本时 SR 逐卡片读两遍标题,信息零增量、耐心双倍消耗。W3C 建议:相邻文本已描述图意时用空 alt([W3C](https://www.w3.org/WAI/tutorials/images/decorative/))。
**触发(trigger)**: img 的 alt 与同容器内链接文本或 figcaption 归一化后相同即 warn(相邻范围的判定口径[待核])。
**不修的条件(caveat)**: 图注已完整描述图意时,alt 可刻意留空(alt="")——图注就是描述,不判缺失(images-alt-present 的口径);本条抓的是"复读"而非"缺失"。
**修复(fix)**: alt 写图内信息(与文字标题互补);图注完整时 alt="";卡片组件模板化——标题进链接、图片描述进 alt,两变量分工。
**关联(seealso)**: images-alt-present、images-alt-generic;[semantic-html.md](../semantic-html.md)

#### a11y-aria-typo [待核 ID]
- 名称/类型: ARIA 属性/角色拼错 —— issue · 优先级 high · 输出 CRITICAL(源表 fail;浏览器静默丢弃)
**这意味(what)**: aria-* 属性名或 role 值拼错:aria-lable(丢 e)、aria-labeledby(应为 labelledby)、role="buton"——浏览器静默丢弃,不报任何错。
**为什么(why)**: 无障碍:拼错的 ARIA 等于没写,且零报错渠道——开发者以为配了无障碍,用户端什么都没发生,是"最自信的失效"。
**触发(trigger)**: 1) aria-* 属性名不在 WAI-ARIA 已知属性表;2) role 值不在 ARIA 角色表;3) 属性-角色搭配非法(role=img 上用 aria-expanded)——命中任一即 fail 档(校验表口径[待核])。
**不修的条件(caveat)**: 属性名对但引用值错(aria-labelledby 指向不存在的 id)归 a11y-duplicate-id 关联家族;本条只管词法层。data-* 自定义属性不判。
**修复(fix)**: IDE 装 ARIA 校验(eslint-plugin-jsx-a11y 类);CI 加 ARIA 词法 lint(属性表+角色表白名单);评审对 aria-* 一律查表。
**关联(seealso)**: a11y-aria-parent-child、a11y-accessible-name;[semantic-html.md](../semantic-html.md)

#### a11y-aria-hidden [待核 ID]
- 名称/类型: aria-hidden 包裹可聚焦元素 —— issue · 优先级 critical · 输出 CRITICAL(源表 fail)
**这意味(what)**: aria-hidden="true" 的容器里有可聚焦元素(链接/按钮/输入)——视觉可见、可 Tab 到,但 SR 完全不播报。
**为什么(why)**: 无障碍:键盘用户 Tab 进"不存在"的元素——焦点静默消失、所见与所听分裂,是 ARIA 的头号误用。
**触发(trigger)**: aria-hidden=true 的元素子树内含可聚焦元素(无 disabled/tabindex=-1 豁免)即 fail。
**不修的条件(caveat)**: 合法做法是先禁再隐:元素 disabled 或 tabindex=-1 后再 aria-hidden(折叠菜单收起态);纯装饰容器(无交互)aria-hidden 永远合法。
**修复(fix)**: 隐藏前先移出 Tab 序(tabindex=-1/disabled/条件渲染);折叠类组件用 hidden 属性(视觉+语义双收)替代 aria-hidden;根级禁令见 a11y-aria-hidden-root。
**关联(seealso)**: a11y-aria-hidden-root、a11y-tabindex;[semantic-html.md](../semantic-html.md)

#### a11y-aria-hidden-root [待核 ID]
- 名称/类型: html/body 级 aria-hidden —— issue · 优先级 critical · 输出 CRITICAL(源表:html/body 禁 aria-hidden;档位见节首对照行,按 aria-hidden 家族 fail 档从重,两轴校准注明)
**这意味(what)**: `<html>` 或 `<body>` 元素上出现 aria-hidden 属性(常见 true——SPA 加载态/新手引导插件的遗产)。
**为什么(why)**: 无障碍:根级隐藏让整页对 AT 消失——浏览器里正常显示,SR 用户听到的却是空页面,是能写出的最重无障碍事故之一。
**触发(trigger)**: `<html>` 或 `<body>` 元素带 aria-hidden 属性即触发(无论值)。
**不修的条件(caveat)**: 无豁免——任何"暂时隐藏全页"的实现都该用视觉遮罩(overlay)而不是根级语义隐藏;命中即最高优先级修。
**修复(fix)**: 排查加载态/引导(tour)组件对 body 的属性操作,改视觉层(opacity/overlay);CI 断言 html/body 永不带 aria-hidden。
**关联(seealso)**: a11y-aria-hidden、js-runtime-hygiene;[semantic-html.md](../semantic-html.md)

#### a11y-aria-parent-child [待核 ID]
- 名称/类型: ARIA widget 父子角色缺失 —— warning · 优先级 medium · 输出 WARN(源表:ARIA widget 须有所需父子角色,tab 在 tablist 内/option 在 listbox 内;档位见节首对照行)
**这意味(what)**: ARIA 复合控件的角色结构不完整:role=tab 不在 role=tablist 内、role=option 不在 role=listbox 内、menuitem 不在 menu 内。
**为什么(why)**: 无障碍:复合控件的 AT 行为(方向键导航/选中播报)由完整角色树驱动——孤儿 tab 退化为普通元素,键盘用户按方向键没反应。
**触发(trigger)**: 需容器角色清单(tab/option/menuitem/menuitemcheckbox 等[清单待核])中的角色,其祖先链内无对应 required parent 角色即 warn。
**不修的条件(caveat)**: 原生元素优先(`<select><option>` 天生完整)——能用原生就不要手搓 ARIA;本条命中常提示该换原生组件。
**修复(fix)**: 补容器角色(tab→tablist、option→listbox、menuitem→menu)或换原生元素;复合控件优先用角色树内置的成熟组件库。
**关联(seealso)**: a11y-aria-typo、a11y-list-structure;[semantic-html.md](../semantic-html.md)

#### a11y-list-structure [待核 ID]
- 名称/类型: 列表子元素非法 —— warning · 优先级 low · 输出 WARN(源表:列表只含 li;档位见节首对照行)
**这意味(what)**: `<ul>`/`<ol>` 的直接子元素不是 `<li>`——塞了 div/p/文本节点,或 `<li>` 裸奔在列表容器外。
**为什么(why)**: 无障碍:SR 播报列表先报"列表,共 N 项"再逐项读——非法子元素打断计数,项数与实际不符,用户对内容量失去预期。
**触发(trigger)**: `<ul>`/`<ol>` 的 Element 直接子节点标签 ∉ {li, script, template}(HTML 规范豁免口径[待核])即 warn。
**不修的条件(caveat)**: 历史模板里 ul 套 div 分组的布局用法,视觉无碍低风险,可排期修;display:list-item 的 div 不算——语义看 DOM 不看样式。
**修复(fix)**: 分组需求用嵌套 li(ul>li>ul>li);包裹层移到 ul 外;模板 lint 列表子元素白名单。
**关联(seealso)**: a11y-aria-parent-child、sd-breadcrumblist;[semantic-html.md](../semantic-html.md)

#### a11y-role-presentation [待核 ID]
- 名称/类型: role=none/presentation 被反证 —— warning · 优先级 low · 输出 WARN(源表:role=none/presentation 不被 ARIA/可聚焦性反证;档位见节首对照行)
**这意味(what)**: 元素声明 role="none"/"presentation"(意图:从无障碍树抹掉),但它带全局 ARIA 属性(aria-label 等)或含可聚焦子元素——声明与实态互相反驳。
**为什么(why)**: 无障碍:presentation 说"我是装饰",aria-label 说"我有名字"——AT 按规范丢弃矛盾的角色声明回退隐式语义,行为不可预期;可聚焦子元素更让"隐藏"名存实亡(与 a11y-aria-hidden 同族矛盾)。
**触发(trigger)**: 1) role=none/presentation 元素带全局 aria-* 属性或含可聚焦子元素即 warn;2) `<table role=presentation>` 内含 th/scope(表头是内容信号,布局表不该有)同类触发[表格分型待核]。
**不修的条件(caveat)**: role=presentation 的正确用法(装饰图/布局表抹除)不受影响——本条只抓"声明与实态矛盾";命中多半该删 role 而非删属性。
**修复(fix)**: 真装饰:去掉矛盾属性、聚焦子元素先移出;真内容:删 role=恢复语义;布局表抹 presentation 时确保内部无 th。
**关联(seealso)**: a11y-aria-hidden、a11y-aria-typo;[semantic-html.md](../semantic-html.md)

#### a11y-input-image-alt [待核 ID]
- 名称/类型: 图像提交按钮缺 alt —— warning · 优先级 medium · 输出 WARN(源表:`<input type=image>` 须 alt;档位见节首对照行)
**这意味(what)**: `<input type="image">`(图像形式的提交按钮)没有 alt 属性。
**为什么(why)**: 无障碍:图像按钮的可访问名只能来自 alt——无名时 SR 只读"提交按钮 图像"或文件名,用户不知道点了会提交什么。
**触发(trigger)**: `<input type="image">` 无 alt 或 alt 空白即 warn。
**不修的条件(caveat)**: 注意与装饰 img 相反:此处空 alt(alt="")不合规——提交按钮必须有名字;遗留表单至少补 alt="搜索" 类动作名。
**修复(fix)**: 首选换 `<button type="submit">`(内嵌图标+文本);遗留表单补动作名 alt。
**关联(seealso)**: a11y-accessible-name、images-alt-present、a11y-form-label;[semantic-html.md](../semantic-html.md)

#### a11y-duplicate-id [待核 ID]
- 名称/类型: ID 重复 —— issue · 优先级 high · 输出 CRITICAL(源表 fail;svg 内 url(#id) 引用的 clipPath 豁免)
**这意味(what)**: 同一文档里 id 属性值出现多次——aria-labelledby/label for/fragment 锚点全部解析到第一个匹配,其余静默失效。
**为什么(why)**: 无障碍:aria-labelledby 与 `<label for>` 按 id 查找,重复 id 让第二个以后的元素失去命名/标签关联——SR 读到的是别人的名字。
**触发(trigger)**: 1) 全文档 id 值去重后仍 >1 即 fail 档;2) svg defs 族的 url(#id) 引用豁免。
**不修的条件(caveat)**: 豁免仅限 SVG defs 族;HTML 层的重复 id 没有正当形态——第三方组件注入的重复 id 也该报给组件方修。
**修复(fix)**: 组件 id 加实例后缀(useId() 类工具);label/aria 引用与 fragment 统一走 id 注册表;CI 断言全文档 id 唯一。
**关联(seealso)**: a11y-form-label、links-broken-anchor、a11y-one-label-per-control;[semantic-html.md](../semantic-html.md)
