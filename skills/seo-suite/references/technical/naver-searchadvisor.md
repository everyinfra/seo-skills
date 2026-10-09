# Naver Search Advisor 官方文档蒸馏

> **来源与口径**:本文件全部条目均为 Naver Search Advisor 官方 웹마스터 가이드蒸馏(来源仓 JaceProgramming/naver-searchadvisor-expert,55/55 篇官方文档全量,每篇带 `guid`+官方修订日期,采集时点 2026-07)。每节括注 `guid`,可在 searchadvisor.naver.com/guide/{guid} 对勘原文。官方指南未收录的概念(C-Rank、D.I.A.+、최적화 지수、저품질 등)不在本文件,不得当作官方口径引用。

## 用途

韩语区(네이버 搜索份额 63–64%)做收录诊断、robots/sitemap/RSS 提交、IndexNow、结构化数据、제휴(合作)API 评估时读。与 [ai-crawler-policy.md](ai-crawler-policy.md) 第三节(Naver 收录语义速览)配合;该文是摘要,本文件是完整规范层。

## 一、收录机制:수집요청 与优先级队列(官方文档蒸馏)

- **流水线**:네이버 搜索反映走「수집(抓取)→ 정제(清洗)→ 색인(索引)→ 랭킹(排名)」四段;抓到 ≠ 索引,索引 ≠ 曝光。`[guid: report-crawl-refine]`
- **优先级队列是核心机制**:검색로봇 对每个 URL 算「수집 우선순위」(抓取优先级),爬虫资源有限,算法只挑"重要"URL 抓;即使被抓取,索引规模也有物理上限,不保证索引与曝光——SPA 站不因此被判死刑,但同理不保证。`[guid: seo-advanced-javascript]`
- **웹페이지 수집요청**(Search Advisor 内网页抓取请求):只是把 URL 递给抓取系统的"助手",同样进优先级队列,**最短 1 天、最长数周**才访问;同一 URL 无需每天重复提交;抓取成功也不保证曝光。垃圾站的大批量请求会被算法限流。`[guid: request-crawl]`
- **검색 제외**(搜索排除):先删原文 → 确认 404 → 요청 > 웹 페이지 검색 제외 提交 URL → 经"再索引"生效(非实时)。`[guid: request-crawl]`
- **收录确认**:`site:域名` 查询;검색로봇 访问后最迟约 1 周内反映。索引量趋势看 사이트 진단 리포트(与 site: 快照数有口径差)。`[guid: seo-basic-intro, report-diagnosis]`
- **무료·无审核入场**:네이버 웹 검색无"提交收录"流程,全靠 Yeti 自动抓;Search Advisor 注册+소유확인(所有权验证)不是收录前提,只是解锁报表。站点注册以 host 为单位(路径级不支持)。`[guid: faq-start-register]`

## 二、Yeti 爬虫特性(官方文档蒸馏)

- **UA 两种形态**(版本随时无预警变更) `[guid: seo-basic-firewall]`:

```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko; compatible; Yeti/1.1; +https://naver.me/spd) Chrome/W.X.Y.Z Safari/537.36
Mozilla/5.0 (compatible; Yeti/1.1; +https://naver.me/spd)
```

- **专用爬虫**:Yeti=网页搜索主爬虫;`Ads-Naver`=广告主页面信息采集;`Blueno`=链接预览摘要采集。抓 JS/CSS 等资源时用浏览器 UA 追加 Yeti 串。`[guid: seo-basic-firewall, seo-advanced-javascript]`
- **真伪验证**:反向 DNS(IP → 域名须 `.naver.com` 结尾)+ 正向 DNS 复核;官方 IP 段(CIDR)JSON:`https://searchadvisor.naver.com/doc/naverbot.json`(随时变更)。**勿按 IP 封 Yeti**——IP 段会变,封 UA/robots 才是标准做法。`[guid: seo-basic-firewall]`
- **robots.txt 语义(与 Google 的关键差异)** `[guid: seo-basic-robots, 2025-10-14 修订]`:
  - 2xx:按规则解析;若返回 HTML,即使含有效规则也可能按"无 robots.txt=全部允许"处理(必须 text/plain);
  - 3xx:HTTP 重定向最多跟 5 跳,超限=全部允许;**HTML/JS 重定向不解释**;
  - 4xx:全部允许;
  - **5xx:全部不允许**(=整站禁抓;此前成功抓取的旧规则可临时续用)——Google 是"暂时全禁",Naver 语义更硬,SEO 审计里 robots 5xx 应列为最高优先级阻断项;
  - 规则只对**同 host+协议+端口**生效:`www.example.com/robots.txt` 管不到 `example.com` 与 `https://` 版本(apex↔www 分叉审计点);
  - Yeti 专组(`User-agent: Yeti`)一旦存在即走专组;favicon、JS/CSS 资源路径应与页面同权限放开,否则页面被不完整解读;`Sitemap:` 行可写进 robots.txt。
- **robots.txt 工具**:수집 및 검증(改完立即推送重抓+规则测试)、간단 생성(生成器)。`[guid: seo-basic-robots]`
- **渲染模型**(两波索引) `[guid: seo-advanced-javascript]`:先抓静态 HTML 入索引 → JS 资源存入渲染服务器 → 再访时带 JS 渲染、比对主内容变化后决定索引更新。JS URL 加 timestamp/hash 强刷缓存**不推荐**。SPA 官方建议 SSR。fragment(`#`)与 hashbang(`#!`)一律剥掉,独立内容必须 permalink 化。
- **抓取失败阈值**(수집 현황 错误类型) `[guid: report-crawl-refine]`:로봇 비허용/DNS 오류/연결 실패/서버 오류(4xx·5xx)/페이지 오류(404)/콘텐츠 오류(HTML 或关键资源不可解析)/URL 오류(非标准 URL)/单文档下载>1 分钟报错/HTML >4MB 报错。

## 三、Sitemap 规范(官方文档蒸馏) `[guid: request-feed]`

- 提交后被视为「콘텐츠 피드」,주기적 재방문;네이버 从中抽 URL 后按内部算法筛选、排优先级再抓——**不是提交即抓**。
- **硬校验**:全部 URL 域名须与소유확인 站点同域;单文件 ≤10MB;单 sitemap ≤50,000 URL;响应慢会被限制提交。
- 格式:sitemaps.org 0.9;`loc` 必填,`lastmod`/`changefreq`/`priority` 选填;量大用 sitemapindex(嵌套 sitemap 列表)。robots.txt `Sitemap:` 行是补充入口(사이트 상태 리포트 会识别)。`[guid: site-summary]`
- URL 尽量全量收录(只含 URL 不含正文,容量压力小);**官方明确:优先用 sitemap 而非 RSS 承载 URL 规模**。

## 四、RSS 规范(官方文档蒸馏) `[guid: request-feed, seo-basic-intro]`

- RSS 2.0,**최신글 본문 전체**(最新文全文)入 `<description>`——官方反复强调全文而非摘要。
- **硬校验**:同域;`<item>` ≥1(空 feed 拒收);≤10MB;响应慢限制提交。
- 定位:向爬虫"积极告知新内容 URL"的窗口;全文导致容量有限,URL 规模交给 sitemap。
- 迁移/新站场景:사이트맵+RSS 都提交是官方 10 步清单的标准动作。`[guid: seo-basic-intro]`

## 五、IndexNow(官方文档蒸馏) `[guid: indexnow-about/api-key/request/faq]`

- 端点:`https://searchadvisor.naver.com/indexnow`(搜索顾问自建端点,参与 IndexNow 协议联盟,变更一次多方共享)。
- **Key 规则**:UTF-8;字符集 `a-f A-F 0-9 -`;长度 8–128。key 文件 `{key}.txt` 放站点根目录(推荐),txt 内容=key 字符串本身;放其他目录须带 `keyLocation` 且**只对该目录下的页面生效**。多域名各自独立 key。
- **单 URL**:`GET /indexnow?url=...&key=...[&keyLocation=...]`(URL 须符合 RFC3986)。
- **批量**:`POST /indexnow`,JSON `{host, key, keyLocation?, urlList[]}`,**单次最多 10,000 URL**。
- 响应:200 成功 / 202 已接收待验 key / 400 格式错 / 403 key 无效 / 422 URL 与 key 不匹配 / 429 过频 / 500。总请求数无上限,只限突发。
- **边界(官方 FAQ)**:不保证索引;**不替代**수집요청/RSS/sitemap,按场景并用;404/301/302 变更也可推送;只推采用之后新增/变更的 URL,不回灌历史。

## 六、수집요청 API(제휴 联盟 API,官方文档蒸馏) `[guid: crawl-request-api, 2025-07-25 修订]`

- **前提三件**:①네이버 제휴제안(合作提案)获批;②Search Advisor 소유확인(url scheme/www/端口任一不同=不同站点,须严格一致);③目标 URL 对 Yeti 可抓(robots 允许)。
- 认证:도구 설정 页签发 accessToken,`Authorization: Bearer ...`;**TLS ≥1.2**(1.0/1.1 拒连)。
- 端点:`POST https://apis.naver.com/searchadvisor/crawl-request/submit.json`(提交)与 `verify.json`(payload 预检)。
- payload:`{"urls":[{"url":"...","type":"update|delete"}]}`;**单次 ≤1,000 URL、≤2MB**;update=Yeti 实访抓取,delete=从存储删 URL(不访问);同 URL 两类型并存时 delete 优先;只处理已제휴 站点 URL。
- 只能提交**最终落地页 URL**(请求 URL 与浏览器渲染 URL 须一致,重定向=업데이트 실패);同文多 URL 只提 canonical 那个。
- 配额:일별(每日)按 URL 数扣减;1005=当日额度耗尽,其后请求直接丢弃。关键错误码:1003 未소유확인 / 1004 未제휴 / 024 인증 실패。
- **제휴 API 提交的 URL 在全网抓取队列里优先级相对更高**;批量提交会瞬时抬升爬虫访问,建议分散;리포트 > 제휴 API 현황(24h 更新)监控 업데이트 실패 数。

## 七、结构化数据:제휴 依赖与类型矩阵(官方文档蒸馏)

- 基座:schema.org(W3C 2015 收编);**官方推荐 Microdata 或 JSON-LD**(RDFa 也支持);一页可组合多类型;验证用 validator.schema.org(+JSON 用 jsonformatter)。`[guid: structured-data-intro]`
- **总免责声明(官方原文级)**:结构化数据即使完全正确也不保证搜索结果反映,引擎可另行选择展示。`[guid: structured-data-intro]` 各类型页均重申"보조적으로 활용,노출 비보장"。

| 类型 (guid) | 必填属性 | 채용/동영상之外是否需제휴 |
|---|---|---|
| 연관채널 Person/Organization (structured-data-channel) | name / url / sameAs | 否;官方识别域名:네이버TV·블로그·스마트스토어·지식iN·치지직 + 당근·Threads·Instagram·YouTube·카카오스토리·카카오톡 채널·Tistory·TikTok·Facebook·X(清单可变,2026-04 修订) |
| 주소 PostalAddress (structured-data-address) | streetAddress(其余选填) | 否 |
| BreadcrumbList (structured-data-breadcrumb) | name | 否 |
| HowTo (structured-data-howto) | step[].text | 否 |
| 캐러셀 ItemList/ListItem (structured-data-carousel) | image(item 内时必填) | 否 |
| 평점 AggregateRating (structured-data-rating) | ratingValue + ratingCount/reviewCount 二选一(并存时 ratingCount 优先) | 否 |
| 레시피 Recipe (structured-data-recipe) | recipeInstructions | 否 |
| 리뷰 Review (structured-data-review) | reviewBody | 否 |
| 식당 Restaurant (structured-data-restaurant) | name / openingHours | 否 |
| TV 시리즈 TVSeries (structured-data-tvseries) | name / actor | 否 |
| 영화 Movie (structured-data-movie) | name / actor | 否 |
| 소프트웨어 SoftwareApplication (structured-data-software) | name / applicationCategory | 否 |
| **채용정보 JobPosting (structured-data-job)** | title/datePosted/validThrough/employmentType/experienceRequirements/jobLocation/description/hiringOrganization/identifier | **是**——제휴제안→JSON-LD 마크업→수집요청 API 연동→robots 허용,四步缺一不可(2025-04 修订) |
| **동영상 VideoObject + 频道 Person (structured-data-video)** | url/name/description/duration/thumbnailUrl/uploadDate/creator 等 | **是**——제휴(동영상콘텐츠 제휴)+ Push/Pull 采集;SERP URL=渲染 URL=含 markup 的 URL 三者必须同一;유료 영상须 offers,로그인 영상须事前协议(2026-03 修订) |

- JobPosting 细节(제휴 后):employmentType/experienceRequirements/workHours/educationRequirements 用官方**韩文枚举**(정규직/계약직/… ,경력/신입/…);薪资 Number 型+KRW;서치펌 공고加 `hiringtype:"headhunting"`;상시모집不写 validThrough。`[guid: structured-data-job]`

## 八、웹문서 vs 서비스内:双通道模型(官方文档蒸馏)

- **双通道**:自家站点内容经 Yeti 抓取进入 **웹문서 검색**(网页文档搜索,通用通道);통합검색(综合搜索)里另有各 **콘텐츠/서비스 영역**(채용정보、VIEW、블로그·카페、기업/학교/명소/게임 等),后者靠平台生态与제휴 供给。`[guid: report-expose-ctr, structured-data-job]`
- **同一内容可双通道重复曝光**:채용정보官方明示可同时出现在 웹 검색 与 통합검색 채용정보 영역;不想上网页通道→该页 noindex,**但제휴 영역对 noindex 的遵守按合作协议另行调整**(双通道策略不能只管一头)。`[guid: structured-data-job]`
- **报表只计 웹문서**:노출/클릭(曝光/点击)只统计"웹 검색과 연관된 영역"——VIEW·블로그 검색、各 콘텐츠 정보 영역、搜索广告**均不计入**;数据口径=更新基准日(约滞后 1 周)起回看 90 天,1/7/30/60/90 日窗,关键词与网页 TOP 30。`[guid: report-expose-ctr]`
- **서브링크**(子链接):引擎按结构与用户偏好自动分析,无法申请;退出开关:`<a rel="nosublink">` 单条、`<meta name="naver" content="nosublinks">` 全站。`[guid: faq-sublink]`
- **SERP 信息更新**:标题/说明/缩略图由引擎自动选定(title/description/OG/앵커 等候选中择优),네이버 不接受人工改 SERP;OG 与基础 meta 不一致时索引过程"选搜索最优值"。`[guid: faq-serpedit]`

## 九、标记层硬规范速查(官方文档蒸馏)

- **canonical**:绝对路径;主页用 HTTP redirect 优先于 canonical。`[guid: markup-structure]`
- **robots meta**:`noindex`/`nofollow` 标准语义之外,**`nosourceinfo`(네이버 独有)**=该站不提供 AI 自动生成的출처설명(AI 来源说明)——全球唯一官方 AI 引用退出 meta。`[guid: markup-structure]`
- **og:image 三条件+唯一性**:>150×150、≥5,000 字节、宽高比 ≤3:1、每文档唯一(重复 logo/横幅类会被弃用)。`[guid: markup-content]`
- **favicon**:方形 ≥16px(结果页按 15×15 缩放);ICO/PNG/GIF/JPEG/APNG/SVG 均可;href 绝对路径;rel 优先级 shortcut icon > icon > 默认 /favicon.ico > apple-touch-icon(-precomposed);URL 勿频繁改。`[guid: markup-favicon]`
- **title/description**:全站同 title、重复堆词、无关热词均扣分;**간단체크 工具口径:제목 40 자、설명 80 자(全角字符)以内**。`[guid: markup-content, diagnose-site]`
- **重定向**:301=永久(URL 变更保信号)、302=临时;JS 重定向禁用(meta refresh 可识别但不推荐);**连续重定向 ≤5 跳**、链条中每环都必须可抓;临时封爬用웹마스터도구 트래픽 제한(수집 설정)而非 robots.txt。`[guid: seo-basic-redirect]`
- **迁移**:旧站 301 1:1 到新站、新站全页 canonical、注册新站+提交 sitemap;**迁移完成前旧站禁止先设 robots 屏蔽或断网**(会挡住爬虫确认迁移)。`[guid: seo-basic-migration]`
- **소유확인 限制**:验证时不执行 JS,JS/meta refresh/cookie 跳转均不跟;验证 meta 必须在 head(非 frame/body)。`[guid: faq-start-register]`
- **移动**:官方推荐响应式;独立 m. 域名时移动页 canonical 指桌面页、双站都注册;UA 跳转用 HTTP redirect。`[guid: markup-mobile, seo-basic-create]`

## 十、官方工具清单(官方文档蒸馏,均在 searchadvisor.naver.com)

| 工具 | 位置 | 要点 (guid) |
|---|---|---|
| 사이트 간단 체크 | tools/sitecheck(免注册) | 实时访问主页出 SEO 报告;robot 접근/title·description(40/80 자) 길이/noindex/RSS·sitemap 提交等清单 `[diagnose-site]` |
| URL 검사 | 검증 | 색인/Meta/SEO 三表:状态码、수집·색인 여부、meta 提取、SEO 修复优先级;해킹(篡改注入)排查官方指定用此工具看"真实抓到的 HTML" `[url-inspection, content-abusing]` |
| 콘텐츠 노출 및 클릭 | 리포트 | 웹문서口径 90 天报(见第八节) `[report-expose-ctr]` |
| 사이트 진단 | 리포트 | 색인/수집제한/색인제외/SEO 四分类+일별 snapshot;明细 URL 最多下 2,000 条;近 90 天抓取页面;生效需 등록+≥1 条内容被抓+约 1 周 `[report-diagnosis]` |
| 사이트 최적화 | 리포트 | AI 评估算法打分=排名间接指标,**≠排名保证**;四轴:로봇 수집/콘텐츠 관리/사이트 구조/사이트 활성화 `[report-seo]` |
| 수집 현황 | 리포트 | 九类抓取错误(见第二节阈值) `[report-crawl-refine]` |
| 사이트 상태 | 리포트 | 보안 인증서/HTTPS 리다이렉션/사이트맵 三卡,1–2 日更新;HTTP·HTTPS 并存无重定向=重复抓取+安全隐患 `[site-summary]` |
| robots.txt 도구 | 수집 설정 | 수집 및 검증(推送重抓+规则测试)/간단 생성 `[seo-basic-robots]` |
| 웹 페이지 수집요청 / 검색 제외 | 요청 | 优先级队列语义(见第一节) `[request-crawl]` |
| 사이트맵·RSS 제출 | 요청 | 第 3·4 节校验 `[request-feed]` |
| 수집요청 API | 제휴(외부 API) | 第 6 节;리포트 > 제휴 API 현황 监控 `[crawl-request-api]` |
| IndexNow | api(indexnow) | 第 5 节 `[indexnow-*]` |
| 교육 자료 PDF | guide | 웹 검색 기초/웹마스터도구 활용两份官方 PDF `[education-basic, education-wmt-advanced]` |

## 十一、审计红旗(官方文档蒸馏,判 P0/P1 用)

- robots.txt 5xx = 整站禁抓(最高优先级);apex↔www robots 分叉;`User-agent :` 空格畸形致严格解析器丢组。`[guid: seo-basic-robots]`
- 页面允许但 JS/CSS/图片在 Disallow(渲染不完整);`href="javascript:..."` 断链发现;HTTPS 页引用同 host 的 http:// 资源。`[guid: resource-and-link]`
- 오류页返回 200(soft-404)/HTML 空壳 JS 站 → 불용문서 색인 제외。`[guid: seo-advanced-indexing]`
- 콘텐츠 스팸 유형(2026-07 修订,涉 AI 生成):클로킹(含 UA/Referer 差异化展示)、부적절 리다이렉트、링크 스팸、백링크 악용·만료 도메인 악용、매크로·조작、해킹 콘텐츠、숨겨진 텍스트、키워드 반복、낚시성、**저품질 대량 생성(模板微变多页,AI/自动化参与不单独定罪但同罚)**、스크래핑、유해/혼동 유발、유사 공공사이트、피싱。罚则=노출 제외或顺位下락;整改后可经 검색 노출 정상화 요청 申诉。`[guid: content-abusing]`
