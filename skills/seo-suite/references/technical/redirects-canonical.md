# 重定向与 Canonicalization 深度指南

> 建立于 2026-10-09,口径经 2026-10 检索核实。与既有文件**分工(只引用不复述)**:状态码语义表、Google 10 跳上限、soft 404、curl 逐跳命令、siteone-crawler 跳数分级见 [http-status-codes](http-status-codes.md);C8 canonical 双通道检查、C20 跳数 ≤1、C3 四变体 host、JS SEO 四边界、GSC `googleCanonical`/`userCanonical` 字段见 [validation-guide](validation-guide.md);301 权重传递数据(~90-99%)、Renew-Forever 规则、整站迁移 checklist 与 www/裸域双活事故见 [domain-strategy](../research/domain-strategy.md);robots 屏蔽后 canonical/noindex 不可见的原理见 [robots-txt-reference](robots-txt-reference.md);canonical 标签语法见 [head-elements](head-elements.md);hreflang 交互细节见 [hreflang-validation](hreflang-validation.md)。

## 一、重定向全类型

### 1.1 五种 3xx 的用法边界

| 码 | 语义 | 方法与 body | SEO 用途 | 边界 |
|---|---|---|---|---|
| 301 | 永久移动 | 转为 GET、丢 body | 永久改址、合并页面、http→https、www 统一 | 强规范化信号,目标 URL 成为规范网址 |
| 308 | 永久移动 | **保留方法与 body** | 同 301,但表单 POST/PUT 端点迁移时才必需 | 对普通 GET 页面与 301 无 SEO 差异 |
| 302 | 临时移动 | 转为 GET、丢 body | 临时活动页、短期 A/B 跳转、维护期临时指向 | 弱规范化信号,搜索结果通常保留原 URL |
| 303 | See Other | 强制 GET | POST 后跳转到结果页(Web 开发语义) | SEO 场景几乎不用;对 GET 请求与 302 实际等价 |
| 307 | 临时移动 | **保留方法与 body** | 同 302 的保留方法版 | 临时跳转 API/表单端点;普通页面用 302 即可 |

判断口径:**意图讲清楚**——永久用 301/308,临时用 302/307;"不确定就先 302 以后再改"是错的,302 期间原 URL 仍占索引与信号。语义细节与 Google 对各码的处理以 [http-status-codes](http-status-codes.md) 第一节表为准。

### 1.2 HTTP / meta refresh / JS 三种实现的可爬性差异

| 实现 | 爬虫看见的时机 | 可靠性 | 定位 |
|---|---|---|---|
| HTTP 服务端(3xx + Location) | **首次请求即见**,不耗渲染队列 | 全部爬虫一致 | 首选,永远优先 |
| meta refresh(尤其 0s) | 需先下载 HTML;Google 把 0s 视作重定向,部分爬虫/工具不跟或延迟跟 | 低,且给用户闪跳体验 | 仅当无法改服务端配置时的兜底 |
| JS `location`/`history` 跳转 | 需进**二级渲染系统**(WRS),晚数小时至数天;raw HTML 上一切规范化标记此时才被读 | AI 爬虫与多数社交爬虫**不执行** | 最后手段;迁移期用 JS 跳转=把改址信号延迟一整个渲染周期 |

JS 实现的边界与"raw HTML 与 JS 注入不一致时 Google 任选其一"的口径,见 [validation-guide](validation-guide.md) 的 JS SEO 四条边界。

**判定现状用哪种实现**:curl 抓首个响应——3xx 状态码即 HTTP 层;200 + `<meta http-equiv="refresh">` 即 meta;200 + 无标记但渲染后 `location.href` 变化即 JS。审计报告里必须写明实现层,因为三层对应的修复工位完全不同(Nginx/CDN 规则 vs 模板 head vs 前端代码)。

```bash
# 三层判定一次完成:状态码、meta refresh、JS 跳转特征
curl -sI https://example.com/old | head -5
curl -s https://example.com/old | grep -io 'http-equiv="refresh"[^>]*'
curl -s https://example.com/old | grep -ioE 'location\.(href|replace|assign)\s*\('
```

### 1.3 链式优化与循环检测

- **跳数分级**(自内向外收紧):Googlebot 官方上限 **10 跳**,超过在 Search Console 报"重定向错误"([http-status-codes](http-status-codes.md) 补充);Mueller 对高频抓取 URL 的建议是 **<5 跳**(2020 公开口径,仍是 2026 各审计工具的引用基线);套件内链口径 C20 **≤1 跳**;本指南对**存量重定向链的目标是 ≤2 跳**——超过即应改写映射直达最终 URL。
- 每多一跳 = 多一次往返延迟 + 多一次出错机会 + 中间页内容漂移带来的信号漏损(链中夹 302 漏损显著放大,数据见 [domain-strategy](../research/domain-strategy.md) §2.4)。
- **循环检测**:A→B→A、A→A 自指、跨 host 循环(https→http→https)。征兆:curl 跟随到超时、GSC"重定向错误"、日志里同一 Googlebot 会话反复请求同簇 URL。自检命令(逐跳列出状态码与目标,数 HTTP 行即跳数):

```bash
curl -sIL --max-redirs 15 https://example.com/old | grep -iE '^(HTTP/|location:)'
```

- 修复原则:改写**链首**直达终点,而不是在链尾再补一跳;改完抽查历史 Top 流量 URL 与 sitemap 内全部 URL。

常见链式形态与修法:

| 形态 | 例子 | 修法 |
|---|---|---|
| 历史叠加链 | A→B(2019)→C(2023)→D(2025) | 地图合并 A/B/C 全部直指 D |
| 协议串行 | http→https→www | 两条规则合并成一跳(2.2 同款) |
| 链中夹 302 | 301→302→301 | 临时跳转替换为最终目标,消除弱信号夹层 |
| 尾斜杠/大小写链 | /Page→/page→/page/ | 规范化层(C29 URL 卫生)统一输出,一次成型 |

### 1.4 重定向地图(映射表)的维护

- 字段至少:from URL、to URL(最终 200,非中间跳)、状态码、上线日期、负责人/工单号、来源(迁移/合并/参数清理)。
- 变更管理:新增映射走 PR 审核(套件红线 R1 同源逻辑);**禁止**在地图外临时加 301。
- 存量治理:每季度用服务器日志回放验证每条 from 仍返回预期码;整站迁移后的保留纪律(Renew-Forever:至少一年、实务上无限续费)与 T+180 地址变更窗口见 [domain-strategy](../research/domain-strategy.md) 迁移 checklist。
- 反向索引:地图同时维护 to→from,页面再改版时才知道哪些历史 URL 挂在它身上,避免"链上加链"。

示例结构(实际以工单系统或 CSV 台账承载,进版本库):

```csv
from_url,to_url,code,shipped_at,owner,reason
/old-blog/post-1,/blog/post-1,301,2023-04-11,@infra,migration-v2
/http://example.com/x,https://www.example.com/x,301,2021-08-02,@infra,host-unify
/products/discontinued,/products/category-a,301,2025-12-01,@ecom,sku-sunset
```

## 二、Canonicalization 六场景

### 2.1 www / 裸域

- 二选一定为 canonical host,**另一侧 301 过去 + 全站 canonical 对齐**。两套都 200 = 外链分流、抓取预算分裂、规范化信号互搏(唯一会出 SEO 事故的形态,修复顺序:先统一 canonical 再上 301,反了会短期震荡——[domain-strategy](../research/domain-strategy.md) §www 既有口径)。
- 上线前用 C3 口径把 www/apex × http/https × 尾斜杠的**变体全 301 一跳到规范形态**([validation-guide](validation-guide.md) C3)。

### 2.2 http / https

- canonical 与 sitemap 一律写 https;http→https 必须**一跳直达**规范 host(不要 http→www 再→https 的两跳串行)。
- HSTS(max-age ≥ 31 天,分级口径见 [http-status-codes](http-status-codes.md) 附录)把 http 请求在浏览器侧直接升级;证书 SAN 需覆盖遗留变体让握手先成功、再 301。

### 2.3 参数 URL

- canonical 指向**去参后的清洁版**,适用于:跟踪参数(utm 等)、会话 ID、排序参数(sort=)、打印视图。
- **例外**:该参数页自身有独立搜索需求与流量(如 `?color=red`)→ 自引用 canonical,让它独立参与排序;判断依据是 GSC 查询数据而非直觉。

### 2.4 分页:canonical 到自己还是第一页?

- **2026 共识:每页自引用 canonical**(页 2 指向页 2,不指向页 1)。依据链:Search Engine Land 2025-11 指南、seoClarity 2025-01、Yoast 2025-11、Boomcycle 2025-05(直接点名"canonical 到页 1"是过时教条)。
- 理由:页 2+ 携带独特商品/内容,canonical 到页 1 = 主动告诉 Google"我的后半库存不存在",深层商品失去索引入口;也阻断页 2+ 自身的排名能力。
- **唯一例外**:存在加载快的 view-all 页且选择它做规范版时,全部页 canonical 到 view-all(2026 年已少见于大站,分页深度太大时不适用)。

### 2.5 facet 组合页

- 结论先行(完整决策树见第五节):无搜索需求的纯浏览组合 → robots 屏蔽省抓取;接近重复但有部分价值 → canonical 到干净基页或自引用;有真实搜索需求(颜色×品类这类) → 留索引 + 自引用。
- 关键约束:**被 robots 屏蔽的页上的 canonical 不会被读到**,所以"屏蔽"与"用 canonical 收编"是互斥策略,不能同时用在一个 URL 上([robots-txt-reference](robots-txt-reference.md) 既有原理)。

### 2.6 跨域 syndication(内容联合发布)

- 内容源头方:canonical **自引用**;转载方:canonical 指回源头。
- Google 明确 canonical 可跨域使用;但它是 hint——若转载版内容更完整、加载更快、内链更强,Google 仍可能选转载版。源头方护城河:首发 + 更完整的页面 + 站内与 sitemap 的自引用一致性。
- 无法给转载方加 canonical 时(平台限制):转载页保留指向源头的**可见超链接**与原文出处声明,降低被选为规范版的概率。
- 三种角色定位:

| 角色 | canonical | 补充动作 |
|---|---|---|
| 内容源头(自己) | 自引用 | 先发、GSC 提交、sitemap 即时更新 |
| 友好转载方(可控) | 指回源头 | 保留出处链接;延迟发布让源头先被收录 |
| 不可控转载(抓取/洗稿) | 加不了 | 不追着加 noindex(对方页面你管不着);靠源头自身信号强度压制,被反超时走 DMCA |

- 多域同内容**无 canonical 归属**是套件红线 R4(量产薄页判定的一部分,见 [validation-guide](validation-guide.md))。

## 三、canonical 与 noindex / robots / hreflang 的交互(冲突矩阵)

| 组合 | 结果 | 判定与处理 |
|---|---|---|
| canonical + noindex 同页 | **矛盾**,Google 官方明示"不建议用 noindex 控制规范化选择" | noindex 会让页面出局,canonical 失去汇聚意义。拆开:canonical 收编重复簇,noindex 剔除垃圾页,**不要同页叠加** |
| noindex, follow | 合法组合 | follow 保留该页外链权重传递;但 Mueller 口径:长期 noindex 的页最终会被当 noindex,nofollow 处理,别当长期策略 |
| sitemap 里的 URL canonical 指向别处 | 浪费抓取 + 信号混乱 | **sitemap 只放自引用 canonical 的 URL**;GSC 会以 "Duplicate, Google chose different canonical" 收编这类页 |
| canonical 指向被 robots 屏蔽的页 | 目标不可见,规范化失效 | 屏蔽与 canonical 互斥(2.5 同理) |
| canonical + hreflang 同页 | hreflang **仅在 canonical URL 上有效** | 簇内每页 canonical 与自身 hreflang 自引用全等,否则整组可能被忽略(规则 1/6,见 [hreflang-validation](hreflang-validation.md)) |
| canonical 与 301 同时存在 | 301 是更强信号 | Google 通常跟 301;迁移期两信号打架会产生震荡,以 301 目标为 canonical 终点对齐 |
| canonical 指向 404/410 | 指向不存在的目标,被忽略 | canonical 必须指向返回 200 的最终 URL |
| canonical 指向重定向页 | 信号打折 | 应写重定向链的最终 200 URL |
| `<link>` 与 `Link:` 响应头两个 canonical 不一致 | 失控,Google 任选其一 | C8 双通道检查,常见祸首是 CDN 规则外溢([validation-guide](validation-guide.md) C8) |
| raw HTML 与 JS 注入的 canonical 不一致 | 同上,任选其一 | 两边必须一致(JS SEO 边界第 1 条) |

> 补记:用 noindex 页做 canonical 目标同样无效——目标页自己都不在索引里,无法成为簇的代表页(seonaut 14 项跨页检查里的"canonical 指向不可索引页"即此,[validation-guide](validation-guide.md))。

## 四、分页 SEO 深度(页 2+ 的处理)

- **canonical**:每页自引用(2.4 共识),包括 `?page=2` 与 `/page/2/` 两种形态——两种形态**只能留一种**做规范 URL,另一种 301。
- **rel=prev/next 遗产**:Google 2019-03 起不再将其用作索引信号;已部署的保留无害(对部分非 Google 爬虫仍可读),但**不新增**、不为它投入工程量。套件口径见 [validation-guide](validation-guide.md) 分页条目。
- **无限滚动的服务端化**:滚动容器背后必须有**真实可抓的分页 URL**(`/page/2/`),"加载更多"按钮之外用 `<a href>` 承载入口;仅靠 History API pushState 改地址栏对爬虫不可见。这是 Google 官方 infinite scroll 文档的硬要求,也是 2026 年电商审计的高频失败项。
- **sitemap 策略**:分页页 2+ 一般**不进 sitemap**(seoClarity 口径)——sitemap 是"值得索引的页面清单"而非"全部存在的页面清单";页 1 与高价值组合页进,页 2+ 靠内链发现。
- **抓取预算**:分页是深层商品的发现通道;页 2+ 深度过大(>4 点击,seonaut 阈值)时用分类再分层,而不是无限加页。
- **GSC 遗产**:围绕分页/参数的旧工具已全部退役——URL Parameters 工具 2022-04 退役(官方自述仅约 1% 配置真实有效,且误配会**阻止 Google 抓取**),更早的 HTML Improvements 报告 2019 退役。含义:参数与分页治理**只能站内自管**(robots/canonical/noindex/白名单),不能再托付搜索引擎侧工具。现行观察窗口是"页面索引"报告的重复类目与 URL Inspection 的 `googleCanonical` vs `userCanonical`([validation-guide](validation-guide.md) 既有字段口径)。
- **分页 URL 形态**:`?page=2` 与 `/page/2/` 选一种做规范形态,另一种 301 过去;混合形态是分页 canonical 混乱的第一来源。页码参数(page)是参数白名单里最典型的合法成员(第五节),别在参数清理时误伤。
- **"查看全部"与分页的取舍**:商品数 <~30 且 DOM 可控时 view-all 单页是最优解(无页 2+ 问题);大分类用真分页 + 自引用,两者别混用同一分类。

## 五、参数与 facet 治理

### 5.1 组合爆炸的量级

10 个 facet 各 5 个取值,理论 URL 空间 = 每 facet 取或不取的乘积(≈3^10 量级)——任何"全部留索引/全部自引用"的策略在这个量级前都失效,必须分层。

### 5.2 决策树:robots vs canonical vs noindex

按"该组 URL 有没有搜索需求 + 接近重复程度"分四层(Google 官方 faceted navigation 文档框架 + 2026 实务口径):

| 层 | 判定 | 策略 | 理由 |
|---|---|---|---|
| 1. 纯浏览组合(如排序、价格区间细切) | 无搜索需求、与基页近重复 | **robots.txt 屏蔽** + 内链不再输出该类 URL | 最省抓取预算;屏蔽后无需 canonical(反正读不到) |
| 2. 弱需求组合(单一 facet,偶有长尾) | 有少量流量、内容与基页差异薄 | 可爬 + **自引用 canonical 或 canonical 到干净基页**,交给 Google 选 | 保留被选中的可能,不硬塞结论 |
| 3. 有明确需求的组合(品类×颜色这类被搜索的搭配) | 有查询量的组合页 | **留索引**:自引用 canonical + 进 sitemap + 程序化质量门槛 | 这是程序化 SEO 的正面资产(门槛见 [programmatic-seo-gates](programmatic-seo-gates.md)) |
| 4. 会话/跟踪参数 | 生成即污染 | 服务端不输出、canonical 指清洁版 | 从生成端消灭,而非靠规范化兜底 |

**noindex 在此树中的位置**:只用于"已进索引但确定不要"的存量页短期清理;长期靠 robots(层 1)或根本不生成(层 4)。noindex 需要先**爬到**才生效,量级大的层 1 页群用它反而先烧抓取预算。

### 5.3 参数白名单

- 维护一份**允许出现在可索引 URL 里的参数清单**(典型:`page`、分类 ID、必要的筛选 slug),清单外参数:内链不生成、canonical 去除、日志监控出现率。
- 白名单落在 CI:模板层禁止拼接非白名单查询串(与 C29 URL 卫生口径衔接,[validation-guide](validation-guide.md))。

| 参数 | 类别 | 处理 |
|---|---|---|
| `page`、`p` | 分页 | 白名单;进规范 URL |
| `category`、`color`(有搜索需求) | facet | 白名单;组合页走第五节层 3 |
| `sort`、`order`、`dir` | 排序 | 不进规范 URL;canonical 去除;层 1 可 robots 屏蔽 |
| `utm_*`、`gclid`、`fbclid`、`ref` | 跟踪 | 服务端输出前剥除;canonical 去除;rel=canonical 上**永远不出现** |
| `sessionid`、`sid` | 会话 | 从 URL 生成端消灭(cookie 化) |
| `print=1`、`view=mobile` | 变体视图 | canonical 到标准版 |
- facet 交互层面的工程约束:每次点击只叠加一个 facet 的链接输出、值排序固定(同一组合只产一个 URL)、面包屑只回链基页——从源头压 URL 空间,比事后规范化便宜一个量级。

## 六、审计操作

### 6.1 重定向审计:日志法

1. 从服务器/CDN 日志过滤 Googlebot(按反向 DNS 核实真伪,口径见 [http-status-codes](http-status-codes.md) §五)。
2. 统计 3xx 占总抓取请求的比例——**持续 >10% 即抓取预算在为重定向买单**,是清理信号。
3. 对每条 3xx 跟随到底,重建完整链(Guzzle 系工具用 `X-Guzzle-Redirect-History` 两个合成头,工程参数见 [validation-guide](validation-guide.md) http-status-check 条目)。
4. 站点级跳数分布对照 siteone 分级:0=OK / 1–2 / 3–9 / ≥10(3–9 就该进迁移清理清单,分级出处 [http-status-codes](http-status-codes.md) 附录)。
5. GSC 抓取统计"按响应"核对服务端口径;差异大通常是 CDN/WAF 按 UA 分叉。
6. 迁移后窗口叠加维度:**日期切片**对比改址前后的 3xx 抓取量衰减与新旧 URL 的 Googlebot 点击占比切换进度(整站迁移的观察节奏与 T+180 窗口见 [domain-strategy](../research/domain-strategy.md))。

```bash
# 日志里 3xx 的目标分布(按出现次数排序)
awk '$7 ~ /Googlebot/ && $9 ~ /^30/ {print $9, $6}' access.log | sort | uniq -c | sort -rn | head -30
```

### 6.2 canonical 一致性:爬取检查清单

对全站 200 页逐项过(可并入 seonaut 14 项跨页检查与 C 系列跑批):

- [ ] 每页**有且仅有一个** canonical;`<link>` 与 `Link:` 头双通道一致(C8)。
- [ ] canonical 是**绝对 URL**,协议/host 与规范 host 完全一致(C3 四变体的反面验证)。
- [ ] canonical 目标返回 **200**——不重定向、不 404(矩阵第三、七、八行)。
- [ ] 自引用为主;每一处 canonical≠自身都能对应到 2.2–2.6 的某个场景,否则视为事故。
- [ ] 分页页 2+ 全部自引用;页 2+ 不在 sitemap 里。
- [ ] sitemap 内 URL 100% 自引用 canonical(与 GSC "Duplicate, Google chose different canonical" 类目交叉验证)。
- [ ] 无 noindex 与 canonical 同页叠加;noindex 目标不在任何 canonical 指向里。
- [ ] hreflang 簇的 canonical 与自引用全等(整簇校验见 [hreflang-validation](hreflang-validation.md))。
- [ ] GSC URL Inspection 抽查:googleCanonical = userCanonical;不一致的页排查信号冲突(内链、外链、sitemap、redirect 四处是否各说各话)。

单页快检命令(meta 与 Link 头双通道一次取回):

```bash
u=https://example.com/page?page=2
curl -sD - "$u" -o /tmp/body.html | grep -i '^link:.*rel="canonical"'
grep -io '<link rel="canonical"[^>]*>' /tmp/body.html
curl -sIL --max-redirs 15 "$u" | grep -cE '^HTTP/'   # 跳数=输出行数-1
```

### 6.3 修复的优先级

1. 循环重定向与 ≥3 跳链(直接报错/超限类)。
2. canonical 指向 404/重定向页/被屏蔽页(规范化失效类)。
3. canonical + noindex 叠加、双通道不一致(信号矛盾类)。
4. 分页 canonical 到页 1、参数页无 canonical(策略错误类)。
5. 链式 2 跳优化到 1 跳(体验与预算优化类)。

## 常见误区

- 「页 2+ canonical 到页 1 防重复」——2026 年已明确为过时教条,自引用才是共识(Boomcycle 2025-05 直接点名)。
- 「robots.txt 屏蔽 + canonical 双保险」——屏蔽后 canonical 读不到,双保险变零保险。
- 「noindex 一下再 canonical 回来」——两信号同页互斥,Google 官方不建议。
- 「302 不传权重所以永远用 301」——301 的 ~90-99% 传递是相关内容页对页前提下的实测口径([domain-strategy](../research/domain-strategy.md) §2.4),不是免死金牌;过期域 301 借权是政策红线。
- 「等 GSC 的参数工具调 crawl 率」——该工具 2022-04 已退役,参数治理只剩站内手段。
- 「meta refresh 0 秒等于 301」——Google 当重定向处理,但时机慢一层、其他爬虫不保证跟,不能替代服务端 3xx。

## 来源

本文由 EveryInfra 自行编写,只保留要点,未复制原文。一手资料:

- [规范网址(rel=canonical)官方文档](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)(含"不建议用 noindex 控制规范化""canonical 页自身要自引用")
- [重定向官方文档](https://developers.google.com/search/docs/crawling-indexing/301-redirects)、[分面导航官方文档](https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation)、[无限滚动与分页官方文档](https://developers.google.com/search/docs/crawling-indexing/javascript-infinite-scroll)
- [URL Parameters 工具退役公告(2022-03)](https://developers.google.com/search/blog/2022/03/url-parameters-tool-deprecated)
- Search Engine Land [Canonicalization and SEO: A guide for 2026](https://searchengineland.com/canonicalization-seo-448161)(2025-11)、seoClarity [SEO Pagination Best Practices](https://www.seoclarity.net/blog/pagination-seo)(2025-01)、Yoast [rel=canonical 指南](https://yoast.com/rel-canonical/)(2025-11)、Boomcycle [The Truth About Pagination Canonicalization](https://boomcycle.com/blog/the-truth-about-pagination-canonicalization-why-seo-conventional-wisdom-is-wrong/)(2025-05)
- SEJ [Mueller: <5 hops per redirect chain](https://www.searchenginejournal.com/googles-john-mueller-recommends-less-than-5-hops-per-redirect-chain/344664/)(2020 口径,2026 仍被各审计工具引用)、Conductor/Siteimprove 2026 重定向链综述

数值型断言与"共识"表述引用前按断言半衰期复查;套件内交叉引用以正文链接为准。
