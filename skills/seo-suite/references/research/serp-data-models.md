# Google Trends / Google Scholar 抓取数据模型(字段级参考)

## 用途与何时读

要写脚本拉 Google Trends 趋势数据或 Google Scholar 论文数据(选题时机、市场分层、实体簇种子、引用型内容的一手来源)时读。本文只管**数据模型**:字段、主键、合并与去重规则。什么时候该看趋势、趋势怎么判读,见 [keyword-intent-taxonomy.md](keyword-intent-taxonomy.md) 的趋势判读口径;意图判定与 SERP 功能含义见同目录其他文件。

模型基于两个 Oxylabs 教程仓(2026-10-09 克隆)与其官方文档输出示例,字段名全部对过一手样例;免费替代路径见文末。

## 获取入口

两条 Oxylabs 通道(均付费,有免费试用;凭证走 Basic Auth):

| 目标 | 教程用端点 | source | 关键参数 |
|---|---|---|---|
| Trends | `https://realtime.oxylabs.io/v1/queries` | `google_trends_explore` | `query`;上下文参数 `date_from`/`date_to`/`category_id`(老文档为 `context` 数组);该 source **始终返回结构化数据,无需 `parse`** |
| Scholar | 同上 | `google_scholar` | `query`、`start_page`(默认 1)、`pages`(默认 1)、`parse: true`、`geo_location`(`domain` 参数已废弃, localization 一律用它)、`render`、`callback_url` |

新统一端点 `/v1/scrape/google/trends/explore`(sync/async/batch)参数为 `query`、`category_id`、`date_from`、`date_to`、`search_type`。Trends 底层命中的是 `trends.google.com/trends/api/explore?...comparisonItem...`,即 pytrends 走的同一条内部 API——字段口径因此互通。

## Trends 四分法

响应:`results[0].content` 是**JSON 字符串**,先 `json.loads`。解析后四个顶层键,每个键的值是**块数组**,块内含 `keyword` 与 `items`。教程代码只取 `[0]` 块;稳妥做法是遍历全部块(按块内 `keyword` 分组)。

| 键 | 块级字段 | item 字段 | 说明 |
|---|---|---|---|
| `interest_over_time` | `keyword` | `time`(字符串,如 `"Jan 3 – 9, 2021"` 周区间或 `"Mar 15, 2023"` 日粒度)、`value`(0–100 整数) | 相对热度时序;粒度随时间窗自动变化 |
| `breakdown_by_region` | `keyword` | `geo_code`(如 `"SK"`)、`geo_name`(如 `"Slovakia"`)、`value`(0–100,最高地区=100) | 区域分布;value 是同一请求内归一的相对值 |
| `related_topics` | `keyword` | 嵌套 `topic` 对象:`mid`(Knowledge Graph 实体 ID,如 `"/m/07ngb7"`)、`title`(如 `"Jarritos"`)、`type`(实体类型,如 `"Corporation"`)、`value`、`formatted_value`、`link`(trends 站内相对链接) | **多层结构,须展平**:官方示例把每 item 拍成 `mid/title/type/value/formatted_value/link/keyword` 七列 |
| `related_queries` | `keyword` | `query`(如 `"nike pegasus 40"`)、`value`、`formatted_value`、`link` | 查询级相关词 |

**rising 与 top 的判别**:Oxylabs 展平输出里两类混在同一 `items`,**没有独立分榜键**;靠 `formatted_value` 的形态区分——`"+600%"`、`"+1,550%"` 这类**百分比增速是 Rising**(暴涨有时显示 Breakout),纯数字(0–100 制)是 **Top**。要严格分榜:按 `formatted_value` 是否匹配 `^\+?\d+%$` 过滤,或改走 pytrends(其 `related_topics()`/`related_queries()` 直接返回 `{'top', 'rising'}` 两个 DataFrame)。

**自然主键**:

| 键 | 主键 | 备注 |
|---|---|---|
| `interest_over_time` | `(keyword, time)` | `time` 是格式化字符串,不同时间窗粒度不同,不可跨粒度直接比 |
| `breakdown_by_region` | `(keyword, geo_code)` | `geo_name` 只做展示 |
| `related_topics` | `(keyword, mid)` | `mid` 全局唯一;`title` 有大小写/别名碰撞,只可作展示层代理 |
| `related_queries` | `(keyword, query)` | 原词保留写法,不做归一 |

**多词比较 merge 规则**(教程 `create_comparison`):逐词各自抓取、各自落四个 CSV(`csv/<keyword>/` 目录),再按块合并——

| 块 | merge 键 | how | 列后缀 |
|---|---|---|---|
| iot | `time` | `inner`(pandas 默认,未显式传) | 第一个词裸列,后续 `""`/`_1`/`_2`… |
| bbr | `geo_code` | `inner` | 同上 |
| rt | `title` | 显式 `inner` | 同上 |
| rq | `query` | 显式 `inner` | 同上 |

三个必须知道的坑:

- **归一化口径**:每个词是**独立请求独立归一**的 0–100,横向比绝对值是错的;分开抓再 merge 只适合比**形态/拐点/季节位相**。要真相对量级,用 Trends 原生比较(一次请求逗号分隔多词)。
- **inner join 丢行**:时间窗或地区集不重合的部分直接被丢;比形态前先对齐 `date_from`/`date_to`,或改 `how="outer"`。
- **rt 按 `title` merge 是有损代理**:实体消歧应该用 `mid`(展平后的 df 里就有);标题写法不同(别名、大小写)会假性不匹配。

## Scholar organic

响应:`results[]`(每页一个)→ `content`,含四个键:`organic`、`pagination`、`related_searches`、`search_information`。organic 单条结构(官方样例逐字段核对):

| 字段 | 类型/样例 | 说明 |
|---|---|---|
| `pos` | int,如 `5` | 该页有机位次(1 起) |
| `title` | str | 论文标题 |
| `url` | URL | 落地链接(常直指 PDF 或站点页) |
| `result_type` | `"pdf"` / `"html"` / `"book"` 等 | 结果资产形态;一个主题里 pdf 占比高=学术消费偏好 |
| `description` | str | 摘要式片段(带省略号) |
| `result_id` | 如 `"r_g8gsmjLJgJ"` | 本次 SERP 内的结果标识,出现在 `cite_url`/`related_pages_url` 里;**页内主键** |
| `publication_info.summary` | `"VG Ashok, S Feng, Y Choi - …, 2013 - aclanthology.org"` | 作者-会议-年份-域名一体的原始串,解析年份/venue 从它下手 |
| `publication_info.authors[]` | `{name, author_id, url}` | `author_id`=Scholar 作者档案 ID(如 `"Of8dNP0AAAAJ"`),`url` 为 profile 链接——外联名单直接用 |
| `resources[]` | `{file_format, title, url}` | 全文资源;`file_format == "PDF"` 的才是直链 PDF,**过滤式:`[r["url"] for r in resources if r.get("file_format")=="PDF"]`**;此处 `title` 是主机名不是论文名 |
| `inline_links.cite_url` | URL | 引用格式页( BibTeX/APA 导出入口) |
| `inline_links.cited_by` | `{cites_id, total, url}` | `total`=被引数,`url`=施引文献列表,`cites_id`=施引查询的簇 ID |
| `inline_links.related_pages_url` | URL | 相关论文(基于 `result_id`) |
| `inline_links.versions` | `{cluster_id, total, url}` | `cluster_id`=论文跨版本身份 ID;`total`=版本数;`url`=版本列表 |

**键与去重**:`result_id` 是 SERP 内键,跨页/跨查询不稳定;**跨查询去重与论文身份用 `versions.cluster_id`**。样例中 `cited_by.cites_id == versions.cluster_id`(同为 `10965319278609103023`)——施引集合与版本簇同源时二者相等,但**不要假定恒等**,建模时分开存。

教程的标准提取投影(`extract_articles`,可直接照抄):`position/title/url/result_type/description/authors(仅 name 列表)/publication_summary/cited_by_count(默认 0)/cited_by_url/cite_url/pdf_links(过滤后)`。

## 免费替代路径

不想付费时的等价数据源(Trends 无官方公开 API;Scholar 从无官方 API):

- **Trends → pytrends**(非官方库):`TrendReq().interest_over_time()` / `interest_by_region()` / `related_topics()` / `related_queries()` 与上面四分法**同名同口径**,且 related_* 直接分 `top`/`rising` 两个 DataFrame;`build_payload(kw_list, timeframe, geo, cat)` 对应 `date_from/date_to/category_id/geo`。无鉴权但易 429 限流:串行、加延时、多词一次请求(比较模式)省配额。库非官方,Google 改版会断,用前锁定版本。
- **Scholar → 学术开放 API**(结构化、可长期依赖,拿不到 Scholar 的 `pos` 排名,其余等价或更强):
  - **OpenAlex** `api.openalex.org/works?search=`:`cited_by_count`(≈`cited_by.total`)、`best_oa_location.pdf_url`(≈PDF 过滤)、`authorships`(含机构与 ORCID,比 `publication_info.authors` 更富)、`ids`(含 DOI,替代 cluster_id 做去重)。免 key,带 `mailto` 进 polite pool。
  - **Crossref** `api.crossref.org/works?query=`:`is-referenced-by-count` 被引数、`license`/`link` 找合规全文。免 key。
  - **Semantic Scholar** Graph API `paper/search`:`citationCount`、`openAccessPdf.url`、`externalIds`;匿名调用有限额。
  - **scholarly**(Python 库)直接刮 Scholar,可拿 `pos`/`versions`,但极易被限,只适合小批量并配代理——与付费 API 的差别就在稳定性,字段可对齐本文模型。

## SEO 用途映射

| 数据字段 | 信号 | SEO 动作 |
|---|---|---|
| `interest_over_time` | 上升/衰退/季节位相 | 选题时机与内容日历;衰退词降权刷新(28 天口径见 [keyword-intent-taxonomy.md](keyword-intent-taxonomy.md));配合 `scripts/trend_scout.py` |
| `breakdown_by_region` | 地理需求差 | 市场优先级排序、hreflang/market 取舍、本地化词表佐证 |
| `related_topics`(`mid`+`type`) | 实体层相关度 | 实体簇与 topic cluster 种子(`mid` 作实体去重键),见 [topic-cluster-templates.md](topic-cluster-templates.md) |
| `related_queries` rising(`formatted_value` 百分比) | 突增长尾 | 新兴内容先占位;PAA/相关搜索扩展;竞争小窗口期 |
| Scholar `cited_by.total` | 文献权威度 | statistics/数据型内容的一手来源挑选;数字断言带年份出处(E-E-A-T) |
| `versions.cluster_id` | 论文身份 | 跨查询去重建"可引用文献库";版本数=综述热度旁证 |
| `publication_info.authors`(`author_id`) | 作者档案 | digital PR 学者/作者外联名单 |
| `resources` PDF(`file_format` 过滤) | 全文可得性 | 白皮书/PDF 资产策略;引用前先取原文核对数字 |
| `result_type` 分布 | 资产形态 | 该主题做 pdf 还是 html 资产、能否做 linkable asset |

## 常见坑

- 只取 `[0]` 块:响应是块数组,多词/多块时漏数据;遍历并按 `keyword` 分组。
- 把 rising 的 `formatted_value`(`+600%`)当 Top 分数(0–100 制)直接混排。
- 跨词比绝对 value(各自归一);或 inner merge 丢掉不重合区间后误读"该地区无数据"。
- rt 按 `title` 合并碰撞;该用 `mid`。
- Scholar 把 `resources[].title`(主机名)当论文标题;把 `cites_id` 与 `cluster_id` 当恒等。
- 分页抓取不记 `pos` 所属页(`start_page`),跨页位次错乱。

## 来源

字段与结构核对自一手样例,未复制教程正文:

- [oxylabs/how-to-scrape-google-trends](https://github.com/oxylabs/how-to-scrape-google-trends)(`README.md` + `scraper.py`,2026-10-09 深度克隆精读)
- [oxylabs/how-to-scrape-google-scholar](https://github.com/oxylabs/how-to-scrape-google-scholar)(`README.md` + `main.py`,同上;organic 样例 JSON 为其官方输出示例)
- Oxylabs 官方文档:`google_trends_explore` 输出示例与 `context` 参数(Wayback 2025-01-02 存档)、`google_scholar` 参数表(README 内嵌)、新端点 `/v1/scrape/google/trends/explore` 参数(developers.oxylabs.io llms-full.txt,2026-10-09)
- 免费路径:pytrends、OpenAlex、Crossref、Semantic Scholar、scholarly 各自官方文档
