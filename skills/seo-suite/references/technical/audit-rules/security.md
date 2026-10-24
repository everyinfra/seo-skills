# 审计规则目录 · Security

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### Security(26 条,权重 8%)

非 HTTPS=fail;HTTP 不 301 到 HTTPS=warn/fail;缺 HSTS(`max-age=31536000; includeSubDomains`)=warn/fail;XFO(DENY/SAMEORIGIN)=warn/fail;nosniff=**fail**;CSP/Permissions-Policy/Referrer-Policy(strict-origin-when-cross-origin)/COOP(`same-origin`,防 tabnabbing)=各 warn;`target=_blank` 缺 noopener/noreferrer=warn;表单 action 非 HTTPS=warn/fail;混合内容=warn/fail;`security-csp-xss`(CSP 是否真约束脚本:'unsafe-inline' 无 nonce=不设防;无 CSP 时按权重 0 报,避免与 security-csp 双重扣)/`security-info-disclosure`(Server 带版本号/X-Powered-By=warn,裸 `Server: nginx` 过)/`security-paste-blocking`(onpaste 阻止粘贴=fail,毁密码管理器)/`security-trusted-types`(仅已设 CSP 的站评,`require-trusted-types-for 'script'`)/`security-leaked-secrets`(AWS key/API token/私钥/数据库 URL=fail)/`security-password-http`(HTTP 页密码框=fail)/协议相对 URL `//`=warn;Cookie 三旗(Secure/HttpOnly/SameSite)=warn/fail;**Cookie 寿命 >400 天上限=warn**;`security-ssl-expiry`/`security-ssl-protocol`(**现行并不读证书、不测 TLS 版本**,只拿 HSTS 当代理,见 security-tls 条);SRI(跨域脚本/stylesheet 须 integrity hash)=warn;混淆脚本(长高熵内联脚本调 eval/Function/atob)=warn;品牌登录链指向品牌或本域=warn。

**解释层(6 条,第三批;ID 未公布原文的按家族命名法推得并标 [待核];安全头落地清单另见 [validation-guide.md](../validation-guide.md) C28)**

#### security-https [待核 ID]
- 名称/类型: HTTPS 与混合内容 —— issue/warning · 优先级 critical · 输出 CRITICAL(非 HTTPS 与 fail 档)/WARN(不 301、warn 档)(源表:非 HTTPS=fail;HTTP 不 301 到 HTTPS=warn;表单 action 非 HTTPS=warn/fail;混合内容=warn/fail)
**这意味(what)**: 页面仍以 HTTP 服务(HTTP 版可直达不 301),或 HTTPS 页引用 HTTP 子资源、表单提交到 HTTP。
**为什么(why)**: HTTPS 是官方页面体验信号之一(现行观测入口:GSC 的 HTTPS 报告与 CWV 报告),也是浏览器信任基线——HTTP 页在地址栏被标"不安全",表单走 HTTP 等于明文送凭据。混合内容里被动型(图/音视频)被浏览器自动升级或降级处理,主动型(脚本/iframe)直接被拦——页面功能与评估双碎。
**触发(trigger)**: 1) 页面协议非 https 即 fail;2) http 版返回 200 不 301 即 warn;3) `<form action="http://…">` 即 warn/fail;4) HTTPS 页含 http:// 子资源即 warn/fail(主动型资源取重档)。
**不修的条件(caveat)**: HTTPS 对排名是小信号,然而缺失联动浏览器警告与表单明文,所以一般建议全站 https+301。但内网/预发环境的 http 是部署形态,不在本条评估面。
**修复(fix)**: 全站 301 到 https(单一 host 形态,见 technical-url-consistency);子资源/表单/canonical 全部 https 化;上 HSTS(见 security-headers)防回退。
**关联(seealso)**: security-headers、security-tls;[validation-guide.md](../validation-guide.md)

#### security-headers [待核 ID]
- 名称/类型: 安全响应头家族 —— warning · 优先级 medium · 输出 WARN(源表各=warn:HSTS `max-age=31536000; includeSubDomains`/CSP/X-Frame-Options(DENY/SAMEORIGIN)/nosniff/Permissions-Policy/Referrer-Policy(strict-origin-when-cross-origin)/COOP(`same-origin`,防 tabnabbing))
**这意味(what)**: 七个安全响应头任一缺失:HSTS、CSP、X-Frame-Options、X-Content-Type-Options(nosniff)、Permissions-Policy、Referrer-Policy、COOP。
**为什么(why)**: 每个头各管一面:HSTS 防协议降级剥离(缺了首访 http 可被中间人劫持);CSP 约束脚本注入面;X-Frame-Options 防 clickjacking 嵌套;nosniff 防 MIME 嗅探错配执行;Permissions-Policy 收 API 权限;Referrer-Policy 控引荐信息外泄;COOP(same-origin)防 tabnabbing 类跨窗引用。SEO 侧关联是间接的:可被任意嵌套/注入的页面不是引擎信任的展示形态。CSP 的有效性另由 security-csp-xss 深化('unsafe-inline' 无 nonce=不设防;无 CSP 时按权重 0 报,避免与缺失双重扣),security-trusted-types 仅对已设 CSP 的站评 `require-trusted-types-for 'script'`。
**触发(trigger)**: 响应头逐一断言存在与推荐值(照抄源表:HSTS `max-age=31536000; includeSubDomains`;XFO DENY/SAMEORIGIN;RP strict-origin-when-cross-origin;COOP same-origin);缺失即 warn(原版里 HSTS、XFO 可到 fail,nosniff 缺失直接 fail;CSP 只发 Report-Only 也按缺失 warn)。
**不修的条件(caveat)**: 安全头不(直接)影响排名,然而它们是站点治理质量的可见面与真实攻击面的闸门,所以一般建议按 C28 清单补齐。但 CSP 要灰度上线(先 Report-Only 观察),一次性 enforce 打挂第三方脚本反成事故。
**修复(fix)**: 按 [validation-guide.md](../validation-guide.md) C28 五头起步(HSTS/CSP/nosniff/XFO/RP);CSP 走 Report-Only 灰度;CDN/网关层统一注入。
**关联(seealso)**: security-https、technical-content-type;[validation-guide.md](../validation-guide.md)

#### security-tls
- 名称/类型: TLS 版本与证书(HSTS 代理) —— warning/issue · 优先级 high · 输出 WARN/CRITICAL(源表现行 `security-ssl-expiry`、`security-ssl-protocol`:都不读证书、不测协商的 TLS 版本;HTTP 页=fail;HTTPS 页无 HSTS 头:expiry 条 warn、protocol 条 fail;HSTS max-age <1 年 warn;缺 includeSubDomains 或 preload warn。旧快照写的「证书临期、TLS 须 1.2+」并非现行行为)
**这意味(what)**: 站点没有用 HSTS 声明长期只走 HTTPS;证书与协议版本本身需另查。
**为什么(why)**: 过期证书让主流浏览器弹全页警告;TLS 1.0/1.1 已被 IETF 在 RFC 8996 正式废弃([RFC 8996](https://www.rfc-editor.org/rfc/rfc8996.html),核对 2026-10-21)。HSTS 让浏览器此后只用 HTTPS 访问,但它不证明证书有效。
**触发(trigger)**: 源表现行:1) HTTP 页 fail;2) HTTPS 无 Strict-Transport-Security → warn/fail;3) max-age <31536000 → warn;4) 缺 includeSubDomains 与 preload → warn。证书到期和 TLS 版本手工查:`echo | openssl s_client -connect 域名:443 -servername 域名 2>/dev/null | openssl x509 -noout -enddate`;`openssl s_client -tls1_1 -connect 域名:443`(握手失败即已关闭 1.1)。
**不修的条件(caveat)**: 证书与协议不(直接)影响内容排名,然而过期即全站不可达,是可用性事故级,所以一般建议自动续期+到期告警。但多证书/多边缘节点的站先盘点覆盖面再统一切 1.2+,避免漏节点造成部分用户不可达。
**修复(fix)**: ACME 自动续期(如 cert-manager);notAfter 双阈值告警(30/7 天);TLS 下限 1.2(逐步 1.3),关闭 1.0/1.1。
**关联(seealso)**: security-https;[validation-guide.md](../validation-guide.md)

#### security-cookies [待核 ID]
- 名称/类型: Cookie 旗标与寿命 —— warning · 优先级 medium · 输出 WARN/CRITICAL(源表:三旗 Secure/HttpOnly/SameSite=warn/fail;寿命 >400 天=warn)
**这意味(what)**: Cookie 缺 Secure/HttpOnly/SameSite 旗标,或 Set-Cookie 的 max-age/expires 超过 400 天。
**为什么(why)**: 三旗各堵一类:Secure 限 https 传输(防明文截获)、HttpOnly 禁 JS 读取(防 XSS 窃会话)、SameSite 防跨站携带(CSRF);Chrome M104(2022-08)起把超过 400 天的过期时间截到 400 天,不拒绝该 cookie([Chrome](https://developer.chrome.com/blog/cookie-max-age-expires),核对 2026-10-21);声明更长没有效果。warn/fail 分型按 cookie 用途[待核:常见分型为会话/鉴权类缺旗标取 fail 侧]。
**触发(trigger)**: 逐一解析 Set-Cookie:1) 缺任一旗标 → warn/fail;2) max-age/expires >400 天 → warn。
**不修的条件(caveat)**: Cookie 旗标不影响 SEO,然而会话安全缺口的后果(账号接管)会以最差方式登上 SERP,所以一般建议三旗全配。但第三方嵌入要求的宽松 SameSite 场景,用分区 cookie(CHIPS)替代裸放松。
**修复(fix)**: 会话 cookie `Secure; HttpOnly; SameSite=Lax`;持久 cookie ≤400 天并按业务再收;跨站场景评估 CHIPS/First-Party Sets。
**关联(seealso)**: legal-cookie-consent、technical-tagging;[validation-guide.md](../validation-guide.md)

#### security-link-integrity [待核 ID]
- 名称/类型: 链接与引用安全家族 —— warning · 优先级 medium · 输出 WARN(源表各=warn:target=_blank 缺 noopener/noreferrer;协议相对 URL `//`;跨域脚本/stylesheet 缺 SRI integrity;品牌登录链须指向品牌或本域)
**这意味(what)**: 四项链接/引用卫生任一:`target=_blank` 的链接缺 rel=noopener/noreferrer;URL 用协议相对 `//example.com` 形态;跨域脚本与样式表没有 integrity(SRI)hash;登录/支付类品牌入口链接指向非品牌域。
**为什么(why)**: noopener 防新窗口反向操纵 opener(tabnabbing 的页面侧防线);协议相对 URL 在 http 上下文解析成 http,与全站 https 化冲突且行为依赖上下文;SRI 缺失时第三方脚本被篡改即直接进你页面(供应链注入面);品牌登录链指向陌生域是常见钓鱼形态(本条是原版的安全启发式,非搜索引擎规则)。
**触发(trigger)**: 1) `<a target="_blank">` 的 rel 不含 noopener 即 warn;2) href 以 `//` 开头即 warn;3) 跨域 `<script src>`/`<link rel="stylesheet">` 无 integrity 属性即 warn;4) 登录/账单类锚文本的 href 域 ∉ {本域,已知品牌域} 即 warn。
**不修的条件(caveat)**: 家族单项不(直接)影响排名,然而 SRI 与登录链两项是真实攻击/钓鱼面,所以一般建议一次配齐。但第三方面向无版本化 URL 的脚本(内容随构建变)无法静态钉 SRI,先换版本化 URL 再上。
**修复(fix)**: target=_blank 统一 `rel="noopener noreferrer"`;协议相对改 https 绝对 URL;第三方资源走版本化 URL+SRI(integrity+crossorigin);登录链收敛品牌域或已知 IdP 域并公示。
**关联(seealso)**: links-malformed-href、security-headers;[head-elements.md](../head-elements.md)

#### security-content-danger [待核 ID]
- 名称/类型: 内容层危险信号家族 —— issue · 优先级 critical · 输出 CRITICAL(fail 档)/WARN(指纹与混淆档)(源表:泄露密钥 AWS key/API token/私钥/数据库 URL=fail;HTTP 页密码框=fail;onpaste 阻止粘贴=fail;Server 带版本号/X-Powered-By=warn,裸 `Server: nginx` 过;混淆脚本特征=warn)
**这意味(what)**: 页面/响应里出现五类危险信号:硬编码密钥、HTTP 明文密码表单、阻止粘贴的密码框、服务器版本指纹、混淆可疑脚本。
**为什么(why)**: 泄露密钥是最硬的事故(云端凭据被扫走即被刷账单/挂马);HTTP 密码框等于明文广播凭据;onpaste 阻断摧毁密码管理器(用户被迫手打,实际退回弱密码);Server/X-Powered-By 版本指纹给攻击者递漏洞清单;长高熵内联脚本调 eval/Function/atob 的混淆特征是被挂码后的常见形态(security-info-disclosure 与混淆脚本两条并入本条陈述)。
**触发(trigger)**: 1) 页面文本/脚本命中密钥形态(AWS key/API token/私钥头/数据库 URL)→ fail;2) http 页含 `type=password` → fail;3) 密码/确认框 onpaste 返回 false 或 preventDefault → fail;4) Server 头带版本号或存在 X-Powered-By → warn(裸 `Server: nginx` 通过);5) 内联脚本高熵长串+eval/Function/atob 组合 → warn。
**不修的条件(caveat)**: fail 档三项没有"可合理不修"——它们不是 SEO 取舍是安全事故;warn 档(版本指纹/混淆特征)有误报面(合法加固混淆的第三方组件),命中后先比对官方产物再定性。
**修复(fix)**: 密钥立即轮换+从源码与构建产物移除(历史提交要 purge);密码页强制 https;移除 onpaste 阻断;Server 头去版本、删 X-Powered-By;混淆脚本溯源验签,来源不明的直接下线。
**关联(seealso)**: security-https、security-link-integrity;[validation-guide.md](../validation-guide.md)
