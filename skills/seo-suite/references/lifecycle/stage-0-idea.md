# 阶段 0 打法卡:想法 / 原型(RQ-237 第 2 批)

产品还没有站点,或只有一份产品说明和空仓库。这时没有东西可以体检,SEO / GEO 能做的是**在写代码之前把几件以后很难改的事定对**:有没有人搜、叫什么名字、页面和 URL 怎么排、技术栈能不能被搜索引擎和 AI 读到、品牌事实从第一天起一致。

`plan.py build` 在这个阶段只从下面这些打法里选(`data/playbooks.json` 里 `stages` 含 0 的条目),不出「提交 GSC」「刷新旧文」「修体检问题」这类上线后的事。

| 顺序 | 打法 | 产出 | 命令 |
|---|---|---|---|
| 1 | 用真实搜索数据验证需求 | 一页需求验证报告 | `demand_check.py` |
| 2 | 看清搜索结果里赢的是哪类页 | SERP 页型表 | `serp_occupancy.py`(有导出时)或人工看前 10 |
| 3 | 起名和域名过一遍搜索可见度 | 命名对照表 | `demand_check.py --names` |
| 4 | 按关键词版图定信息架构和 URL | 页面类型表 + URL 规则 | `keyword_variants.py` |
| 5 | 技术选型先过 SEO 约束 | 技术选型表(8 项) | — |
| 6 | 定上线时的前 10 张页 | 页面清单 | — |
| 7 | 问一遍 AI:客户的问题现在谁被引用 | AI 引用基线 | `citation_panel.py` |
| 8 | 品牌实体从第一天起统一 | 品牌事实卡 | `grounding_page.py` |
| 9 | 先定转化怎么记 | 埋点方案 | — |
| 10 | 看竞品靠哪类页拿流量和外链 | 竞品空档表 | `link_intel.py` |
| 11 | 先放一张可收录的落地页 | 落地页 | — |

## 一、需求验证

目的:回答「有没有人搜、搜什么词、结果里已经是谁」。不需要任何 key:

```bash
python3 scripts/demand_check.py --seeds seeds.txt --market en --md
```

- **种子词怎么写**:用客户自己的话写 10–30 个(开局第 2 环问过「客户怎么称呼你们解决的问题」),不要用内部产品名。每条产品线至少 3 个:问题词(how to …)、品类词(… software / … app)、场景词(… for freelancers)。
- **脚本做什么**:对每个种子词,从 Google、Bing、DuckDuckGo 的公开联想接口取联想词,再加问题词、比较词、价格词各查一轮,汇总成:
  - **信号**:两家以上引擎各返回 ≥3 条、合计 ≥10 条不重复联想 → 强;≥3 条 → 弱;否则没有。
  - **意图分布**:问题 / 比较 / 价格各几条。比较词和价格词多,说明已经有人在挑产品(商业意图),适合先做对比页和定价页;问题词多,适合先做指南。
  - **跑题率**:联想里同时含种子词全部实词的比例。低于 40% 时报告会提示「这个叫法可能被理解成别的东西」——例如「pet expense tracker」的联想大多偏到 GPS 定位器,说明「tracker」在这个品类里被理解成定位器,要换叫法再验。
  - **反复出现的词**:联想里种子没有、出现 ≥2 次的词,多半是品牌名或品类名,就是「结果里已经是谁」的线索。
- **口径**:联想词数量是「有人在搜」的信号,**不是搜索量**,报告标 `[est]`。有关键词工具(任何一家)的导出,`--volumes keyword,volume` 补上月搜索量,标 `[real]`。
- **判据**:核心产品线至少有 3 个种子词信号强,才值得按 SEO 获客来规划;都弱或没有时,结论写「搜索需求还没形成,先靠其他渠道,SEO 只做品牌词和基础页」,不硬排内容计划。

## 二、起名和域名

```bash
python3 scripts/demand_check.py --names name-a,name-b --tlds com,io,ai,app,dev --md
```

- 域名用 RDAP(注册数据查询协议,[about.rdap.org](https://about.rdap.org/))查:200 = 已注册;404 = 没查到注册记录,多半可注册,以注册商为准。
- 搜名字时的联想:没有联想最好占;已有 5 条以上以这个名字开头的联想,说明已经有东西叫这个名字,品牌词会和它抢第一页。
- 再人工看三件事:名字和竞品读音或拼写是否接近;在目标市场的语言里有没有不好的意思;社媒同名账号是否还在(第 8 条一起占)。
- 站点名在搜索结果里怎么显示,见 Google 的[站点名称](https://developers.google.com/search/docs/appearance/site-names)文档(首页加 WebSite 结构化数据)。

## 三、信息架构和 URL

- 先把需求验证出来的词用 `keyword_variants.py` 去掉变体、按意图归成主题簇;**一簇对应一类页面**(产品页、对比页、集成页、场景页、指南、文档)。
- URL 规则写成一张表:层级(一般不超过 2 层)、语言前缀(`/en/`、`/es/` 这类子目录最省事,见 Google 的[多地区和多语言网站](https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites))、对比页和集成页放哪。Google 建议 URL 简单、可读、用连字符分词([URL 结构](https://developers.google.com/search/docs/crawling-indexing/url-structure))。
- **为什么现在做**:URL 上线后再改就要做 301 和迁移(阶段 5),代价大得多。

## 四、技术选型的 SEO 约束

选框架和托管之前,8 项都要有答案:

1. 关键页面(首页、产品页、定价、对比页、文档)能服务端渲染或静态生成。Google 能渲染 JavaScript,但它自己也写明服务端渲染或预渲染仍然更好,因为更快,而且不是所有爬虫都能跑 JavaScript([JavaScript SEO 基础](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics));AI 爬虫大多不跑 JavaScript。
2. 每页能单独设 title、meta description、canonical、Open Graph。
3. 能自动生成 sitemap,新页面自动进 sitemap。
4. 多语言:能输出 hreflang(每个语言版本列出自身和其他版本,用完整地址,见 [localized-versions](https://developers.google.com/search/docs/specialty/international/localized-versions))。
5. 改 URL 时能配 301(服务器或框架层)。
6. 预发环境能整站 noindex,正式环境能撤(上线清单会查)。
7. 能加 JSON-LD 结构化数据。
8. 404 页面返回真的 404 状态码。

## 五、品牌实体和测量

- 品牌事实卡:正式名、一句话简介、产品线、目标客户、官网、各平台账号。之后官网、社媒、目录站、llms.txt 都照这一份写,AI 和搜索引擎看到的事实才一致。
- 转化:把开局第 1 环定的那个转化写成唯一主转化,定事件名和触发点,上线前就埋好。

## 六、什么时候进下一阶段

仓库里有了公开页面路由、有了本地预览 → 阶段 1 上线前(`lifecycle.py diagnose` 会自动判)。
