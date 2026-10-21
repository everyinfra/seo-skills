# 审计规则目录 · Legal Compliance

> 从 [audit-rule-catalog.md](../audit-rule-catalog.md) 拆出(2026-10-21),正文原样搬运,只改了相对链接路径。来源、计分口径、ID 纪律、执行速查(`AUDIT`/`CRAWL` 等简写与 J1–J8、G1–G7 片段)和扩写进度见索引页。

### Legal Compliance(1 条,权重 1%)

`legal-cookie-consent`:检测 CMP(CookieYes/OneTrust/Cookiebot/Termly/Quantcast);有 CMP 或无追踪脚本=pass,有追踪无 CMP=warn。

**解释层(1 条,第四批;ID 为源目录原文)**

#### legal-cookie-consent
- 名称/类型: 追踪脚本无 CMP —— warning · 优先级 medium · 输出 WARN(源表:有 CMP 或无追踪脚本=pass,有追踪无 CMP=warn)
**这意味(what)**: 页面加载了追踪脚本(GA/GTM/广告类)却没有检测到任何 CMP(consent management platform:CookieYes/OneTrust/Cookiebot/Termly/Quantcast)。
**为什么(why)**: 合规面:欧盟 ePrivacy/GDPR 对非必要追踪通常要求事先同意(以法务意见为准,本套件未回读法规原文);数据面:Google 标签的 consent mode 缺失会影响 EEA 流量的计量(本次未回读 Google 文档,见 technical-tagging)。判定按"追踪器脚本指纹+CMP 特征 DOM"双查,不读 Cookie 值。源表现行 warn、权重 15。
**触发(trigger)**: 1) 页面脚本命中追踪器指纹(GA/GTM/Meta Pixel 等[清单口径待核]);2) DOM/脚本无已知 CMP 特征(CookieYes/OneTrust/Cookiebot/Termly/Quantcast);两者同时成立即 warn;无追踪脚本则 pass。
**不修的条件(caveat)**: 无 cookie 同意强制要求的辖区,无 CMP 不构成当地合规问题,然而境外流量接入后即暴露;纯必要 Cookie(会话/安全)无 CMP 是合法形态,不判。
**修复(fix)**: 部署 CMP 并接 consent mode(gtag consent default+update,见 technical-tagging);追踪器一律经 CMP 门控加载;隐私政策同步(见 eeat-privacy-tos)。
**关联(seealso)**: technical-tagging、eeat-privacy-tos;[gtm-implementation.md](../gtm-implementation.md)、[validation-guide.md](../validation-guide.md)
