# Brand Records:六记录品牌事实库与 Grounding Page

> 建立于 2026-10-10;深读摘录见 [borrow-specs.md](../research/borrow-specs.md) E7/B4。
> 六记录结构与每条 fact 的 `{fact, source, date, confidence}` 字段、缺口协议为 Profound Brand Records【官方】;
> Grounding Page 11 条为 Rankscale【官方】;25 条已验证 facts 门槛、finding 字段与状态机为 Athena Oracle【官方】。
> YAML 落盘格式、oracle_check.py 消费契约与本文示例是本套件约定【推断】。
> 本文件管"品牌自己说什么才是对的";对外可引用性的证据边界见 [geo-evidence.md](geo-evidence.md)——
> 照做不承诺"必被 AI 引用"。

## 一、为什么需要 Brand Records

AI 引擎对品牌的表述近似全网证据的最小公倍数。没有一份单一、可验证、带出处的事实库,
官网、文档、社媒、新闻稿各自漂移,agent 起草内容时只能靠记忆补洞——错一个价格或成立年份,
就会被 Oracle 类核查直接抓为 finding。Brand Records 就是那份"单一事实源":

- **起草前读它**(禁区与批准术语,见第五节);
- **发布后核查它**:`scripts/oracle_check.py` 用这份事实库对照 AI 采样回答找冲突。

## 二、六记录(Profound 官方结构)

| 记录 | 回答的问题 | 必含要素 | 备注 |
|---|---|---|---|
| Company | 你是谁 | 法定名/别名、成立时间、总部、一句话定位、差异化声明 | 定位句要可验证,不写口号 |
| Market | 你在哪个战场 | 类目(用客户语言)、主要竞对名单、相对站位 | 站位不捏造排名;引第三方须给来源 |
| Offerings | 你卖什么 | 产品清单、**批准术语**(产品名官方写法/大小写/已弃用旧名)、**能与不能宣称的**(claims 白/黑名单) | 黑名单=合规红线,起草前必读 |
| Audience | 卖给谁 | 首要客户画像、重要细分、各自痛点;反向定义"不服务谁" | 细分要有可验证的行为或规模依据 |
| Strategy | 现在优先做什么 | 当前优先级、即将发布、季度目标 | 变化最快,confidence 常为 med/low |
| Execution | 怎么做事 | 发布节奏、内容格式/语气规范、审批链、**从不做的事**(never-do) | never-do 与 Offerings 黑名单同为起草禁区 |

## 三、数据文件格式(brand.yaml,受限 YAML 子集)

每条 fact 四字段【官方】:`fact`(一句话、自包含、含可判定的数字/日期/布尔断言)、
`source`(一手出处 URL 或内部文档路径)、`date`(该 fact 的核验/复核日期)、
`confidence: high|med|low`。本套件约定另加两键:

- `record`:归属六记录之一,取值 `company|market|offerings|audience|strategy|execution`(供核查结果按记录分组);
- `keywords`(可选):显式关键词组列表,覆盖脚本的自动抽取(跨语言场景建议手写)。

落盘为 YAML 的**受限子集**——`scripts/oracle_check.py` 的解析器只认这个形状
(顶层 `brand:` + `facts:` 列表;每条以 `- fact:` 起行,其余键缩进续行;不用锚点/多行块/嵌套;
行内列表用 `[a, b]`,项内不能含逗号):

```yaml
brand: Acme
facts:
  # ---- Company(3)----
  - fact: "Acme 是一家客户关系管理(CRM)软件公司,总部在柏林"
    record: company
    source: https://acme.ai/about
    date: 2026-08-12
    confidence: high
  - fact: "Acme 成立于 2015 年"
    record: company
    source: https://acme.ai/about
    date: 2026-08-12
    confidence: high
  - fact: "Acme 的差异化是“部署 10 分钟上手”,不是“企业套件大而全”"
    record: company
    source: https://acme.ai/positioning
    date: 2026-09-28
    confidence: high
  # ---- Market(3)----
  - fact: "Acme 所在类目是中小团队 CRM,不是企业级 CRM 套件"
    record: market
    source: https://acme.ai/positioning
    date: 2026-09-28
    confidence: high
  - fact: "Acme 的主要竞对是 HubSpot、Pipedrive 与 Zoho CRM"
    record: market
    source: https://acme.ai/positioning
    date: 2026-09-28
    confidence: high
  - fact: "在 G2 2026 年中小企业 CRM 网格中 Acme 位于 Leader 象限"
    record: market
    source: https://www.g2.com/report
    date: 2026-06-30
    confidence: med
  # ---- Offerings(5)----
  - fact: "产品线两条:Free 与 Pro;官方写法首字母大写,不写 ACME PRO"
    record: offerings
    source: https://acme.ai/pricing
    date: 2026-10-01
    confidence: high
  - fact: "Acme Pro 定价为 $49/月,按年计费为 $39/月"
    record: offerings
    source: https://acme.ai/pricing
    date: 2026-10-01
    confidence: high
  - fact: "可以宣称:Pro 计划提供 99.9% 月度可用性 SLA"
    record: offerings
    source: https://acme.ai/legal/sla
    date: 2026-07-15
    confidence: high
  - fact: "不能宣称:已获得 SOC 2 认证——审计进行中未发证(2026-09 口径)"
    record: offerings
    source: https://docs.acme.ai/security
    date: 2026-09-05
    confidence: high
  - fact: "Acme 支持 SSO 登录,仅 Pro 计划;Free 计划不含 SSO"
    record: offerings
    source: https://docs.acme.ai/sso
    date: 2026-07-20
    confidence: high
  # ---- Audience(3)----
  - fact: "首要客户画像:10-50 人的 B2B 销售团队"
    record: audience
    source: https://acme.ai/positioning
    date: 2026-09-28
    confidence: high
  - fact: "重要细分:跨境电商卖家的多币种销售管道"
    record: audience
    source: https://acme.ai/blog/segments
    date: 2026-08-02
    confidence: med
  - fact: "不服务对象:需要本地私有部署的大型金融机构"
    record: audience
    source: https://acme.ai/positioning
    date: 2026-09-28
    confidence: high
  # ---- Strategy(2)----
  - fact: "本季度优先级:邮件集成与移动端;AI 功能在探索阶段,无发布日期"
    record: strategy
    source: internal/okr-2026q4
    date: 2026-10-03
    confidence: med
  - fact: "已公开的即将发布:Outlook 集成,2026 年 Q4 内上线"
    record: strategy
    source: https://acme.ai/roadmap
    date: 2026-09-20
    confidence: med
  # ---- Execution(3)----
  - fact: "发布节奏:每两周一个功能更新,博客每周一篇"
    record: execution
    source: internal/handbook
    date: 2026-08-30
    confidence: high
  - fact: "从不做的事:从不宣称“永久免费”,从不发布无出处的对比图表,从不拿客户名单做广告"
    record: execution
    source: internal/handbook
    date: 2026-08-30
    confidence: high
  - fact: "内容审批:价格与合规相关表述经法务复核后才能发布"
    record: execution
    source: internal/handbook
    date: 2026-08-30
    confidence: high
```

(共 19 条,覆盖六记录;`internal/...` 表示内部文档路径,核查时人工溯源。)

## 四、缺口协议:"够用但不够具体"时【官方】

某记录 *enough to be helpful but not enough to be specific*(够用但不够具体)的信号:

- 只有类目级描述("我们是做 CRM 的"),没有任何可验证的具体 fact;
- 只有形容词没有出处("增长最快的……");
- 整库已验证 facts <25 条(Athena 核查门槛之下,见第五节)。

动作(一次一个、可跳过、答案回流):

1. **只抛一个问题**,且明确可跳过("不方便回答可直接跳过")——不做问卷轰炸;
2. **答案回流**:写进对应 record,补 `source`/`date`;拿不到一手来源前 `confidence: low`;
3. 回流前,涉及该缺口的内容按低置信处理:只用于内部草稿,不进对外页面。

## 五、使用规则

- **起草任何对外内容(页面/文章/FAQ/社媒/广告文案)前,必读两处禁区:Offerings 的"不能宣称"黑名单与 Execution 的 never-do。**
  所有数字/日期/布尔断言必须在 brand.yaml 中找到对应 fact;找不到→先走缺口协议补齐,不凭记忆写。
- **与 intake 的衔接**:项目的 [intake 清单](../overview/intake-checklists.md) 问答产出直接沉淀为六记录
  (问公司→Company、问市场与竞对→Market、问产品与宣称边界→Offerings、问受众→Audience、
  问目标与排期→Strategy、问流程与禁区→Execution)。intake 是一次性采集,Brand Records 是其持久化形态;
  新项目 intake 前先读现有 brand.yaml,只问缺口,不重复已答问题。
- **与核查的衔接**:

  ```
  python3 scripts/oracle_check.py --facts brand.yaml --responses responses.json --out findings.json
  ```

  `responses.json` 为采样回答 `[{prompt, engine, text, mentions}]`,由 `citation_panel.py` 采样导出或人工粘贴;
  facts <25 条时脚本输出低置信警告。finding 的语义级复核与 Possible sources 填写由 agent 结合脚本输出人工完成。
- **维护**:每条 fact 的 `date` 即复核锚点;超过 6 个月未复核的 fact,随下一次 Grounding Page 复审一并核
  (易变事实见下节独立区块)。

## 六、Grounding Page 11 条(Rankscale 官方,附节)

品牌实体页(brand facts 页)的落地规范——11 条 checklist:

1. **H1 = 实体名**(唯一,与外部知识源同名)。
2. **首段一句事实定义**(lead definition):被 AI 逐字引用的目标句;含实体名 + 类目 + 一个可验证差异点。
3. **Core facts 用 `<dl>`**:dt=属性名、dd=值;不写成营销段落。
4. **FAQ 每个答案都含实体名**:答案独立成句、可被单独摘出。
5. **Volatile facts 独立区块**:价格/版本/人员等易变事实与稳定事实分开,页面结构上可单独更新。
6. **is-NOT 消歧**:"Acme 不是 Acme Corp(美国保险集团)"——堵住常见混淆实体。
7. **JSON-LD 镜像页面事实 + sameAs**:结构化数据只镜像页面可见事实(不添加页面没有的);
   sameAs 指向权威档案(Wikidata/领英/官方社媒)。
8. **hub-and-spoke 拆分**:实体页是 hub,产品/主题页是 spoke;不把所有事实堆进一页。
9. **交叉链接用谓词**:锚文本说明关系("Acme 的定价页"、"Pro 计划文档"),不用裸 "read more"。
10. **复核日期 ≤6 个月**:页面可见的 review date;超期先复核再谈 AI 可见性。
11. **URL 简短**:实体名 slug,无参数、无深层级。

页面骨架(Status/Entity type/Updated 头部 + 上述结构)示例:

```html
<!-- /acme —— 实体 hub 页骨架(Rankscale 口径) -->
<h1>Acme</h1>
<p>Acme 是一家总部位于柏林的中小团队 CRM 软件公司,以部署 10 分钟上手为差异化。</p>
<dl>
  <dt>成立</dt><dd>2015 年</dd>
  <dt>总部</dt><dd>德国柏林</dd>
  <dt>类目</dt><dd>中小团队 CRM</dd>
</dl>
<section id="volatile">
  <h2>易变事实(价格与版本)</h2>
  <dl><dt>Pro 定价</dt><dd>$49/月;按年计费 $39/月(2026-10-01 复核)</dd></dl>
</section>
<section id="is-not">
  <h2>Acme 不是</h2>
  <ul><li>Acme Corp(美国保险集团)——同名不同实体</li></ul>
</section>
<section id="faq">
  <h2>常见问题</h2>
  <p><strong>Acme 支持 SSO 吗?</strong> 支持,Acme 的 SSO 登录仅 Pro 计划可用。</p>
</section>
<p>最后复核:2026-10-10 · Status: verified · Entity type: Organization</p>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Organization","name":"Acme",
 "foundingDate":"2015",
 "sameAs":["https://www.wikidata.org/wiki/EXAMPLE", "https://www.linkedin.com/company/acme"]}
</script>
```

注意:JSON-LD 只镜像页面已有事实(第 7 条),sameAs 必须用真实档案 URL——上面 EXAMPLE 是占位符;
hub 页之外的 spoke 页(定价/文档/FAQ)各自保持同一份 brand.yaml 事实,不从记忆复写。
