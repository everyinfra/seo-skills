# Brand Records：品牌事实库与 Grounding Page

> 建立于 2026-10-10；复核于 2026-10-21（首轮 2026-10-18）：来源归属已更正；YAML 格式按 `scripts/oracle_check.py`、`scripts/grounding_page.py` 源码和实跑结果对齐，10-21 又用示例重跑一次，结果一致。
> 来源归属（核对 2026-10-21）：
> - 六类记录的思路来自 Profound 的 Context Manager：它的「knowledge records」覆盖公司、受众、竞品、产品、战略、执行，每条说法都能追到出处；缺信息时一次只问一个问题（[Profound 帮助中心](https://help.tryprofound.com/articles/5615587527-about-context-manager)，厂商文档）。本套件把「竞品」并进 Market 记录；每条 fact 的字段和 YAML 格式是**本套件约定**。
> - 「一条 fact 只断言一件事」参考 Profound FactCheck：它只核对事实性、可执行、原子化的说法，每条只断言一件能被事实库确认或否定的事（[FactCheck](https://help.tryprofound.com/articles/5793584301-about-factcheck)，厂商文档）。
> - Grounding Page 出自 [Grounding Page Standard](https://groundingpage.com/spec/)（独立开放项目，Hanns Kronenberg 提出；v1.7 于 2026-10-09 发布）。Rankscale 的 [/facts 页](https://rankscale.ai/facts) 是一个实现例子。旧版把「11 条」写成 Rankscale 官方规则，不准确。
> - `oracle_check.py` 在 fact 少于 25 条时报「样本不足」。25 条这个门槛出自 AthenaHQ：它的 Oracle 文档写明需要至少 25 条已验证 facts（[AthenaHQ Oracle 文档](https://docs.athenahq.ai/oracle)，厂商文档，核对 2026-10-21）。本套件借用这个数当「低样本警告线」，不是品牌库的质量标准。
>
> 本文件管「品牌自己说什么才是对的」。对外可引用性的证据边界见 [geo-evidence.md](geo-evidence.md)：照做不承诺被 AI 引用。

## 一、为什么需要 Brand Records

官网、文档、社媒、新闻稿各写各的，事实会漂移；agent 起草时没有单一事实源，只能靠记忆补洞。Profound 的 FactCheck 文档也说，AI 说错品牌信息，很多时候不是模型编造，而是品牌自己发布的内容过时了（厂商说法）。Brand Records 就是那份单一事实源：

- **起草前读它**：禁区与批准术语，见第五节；
- **发布后核查它**：`scripts/oracle_check.py` 拿它对照 AI 采样回答，找显式冲突；
- **生成实体页**：`scripts/grounding_page.py` 拿它生成 Grounding Page 草稿。

## 二、六类记录（本套件结构）

| 记录 | 回答的问题 | 必含要素 | 备注 |
|---|---|---|---|
| Company | 你是谁 | 法定名或别名、成立时间、总部、一句话定位、差异化 | 定位句要可验证，不写口号 |
| Market | 你在哪个战场 | 类目（用客户语言）、主要竞对、相对站位 | 不捏造排名；引第三方要给来源 |
| Offerings | 你卖什么 | 产品清单、**批准术语**（官方写法、大小写、已弃用旧名）、**能与不能宣称的**（白名单、黑名单） | 黑名单是合规红线，起草前必读 |
| Audience | 卖给谁 | 首要客户画像、重要细分、各自痛点；「不服务谁」 | 细分要有可验证的行为或规模依据 |
| Strategy | 现在优先做什么 | 当前优先级、即将发布、季度目标 | 变化最快；未公开的只放内部文件 |
| Execution | 怎么做事 | 发布节奏、内容格式和语气规范、审批链、**从不做的事**（never-do） | never-do 与 Offerings 黑名单同为起草禁区 |

## 三、brand.yaml 格式（两个脚本共用的受限子集）

**分两个文件放。** `brand.yaml` 只放可以公开的事实，交给 `grounding_page.py` 生成页面；`brand-internal.yaml` 放内部来源的事实、未公开的战略和禁区。`grounding_page.py` 不过滤内部来源：实测把 `source: internal/...` 的战略 fact 写进了页面的易变事实区、FAQ 和 Sources 列表（2026-10-18）。核查时把两份拼起来用：`cat brand.yaml brand-internal.yaml > all.yaml`，再交给 `oracle_check.py`（解析器支持这样拼接，实测通过）。

**字段**

| 键 | 必填 | 取值 | 谁读 |
|---|---|---|---|
| `fact` | 是 | 一句话，只断言一件事，含可判定的数字、日期或是否 | 两个脚本 |
| `record` | 建议 | `company`、`market`、`offerings`、`audience`、`strategy`、`execution`；其他值保留但告警 | 两个脚本；oracle_check 按它分组 |
| `source` | 建议 | 一手 URL；内部文档写 `internal/路径` | 两个脚本；grounding_page 列进 Sources，并从中抽 sameAs |
| `date` | 建议 | 核验日期，写成 YYYY-MM-DD（本套件约定） | oracle_check 在报告里显示；grounding_page 用易变事实里最新的日期写「Last reviewed」 |
| `confidence` | 建议 | `high`、`med`、`medium`、`low`、`高`、`中`、`低`；其他值当作空值，不告警 | 两个脚本只显示，不据此过滤 |
| `keywords` | 可选 | `[a, b]`，显式关键词组，覆盖自动抽取 | oracle_check |
| `disambiguation` | 可选 | `true`、`yes` 或 `1`：这条进 is-NOT 区块 | grounding_page |

**解析规则**（读源码并实测，2026-10-18）

1. 顶层写 `brand: 名称` 和 `facts:`。
2. 列表项**必须缩进**（至少 1 个空格）再写 `- fact:`。写在行首的 `- fact:` 不被识别，也不告警；它下面缩进的键会覆盖上一条 fact 的同名键。
3. 其余键缩进续行，值不能为空。未知键忽略。
4. 一个值只占一行。不支持多行块、锚点、嵌套。
5. 值首尾是同一种引号时才去掉引号；不处理转义。
6. 行内列表 `[a, b]` 的项里不能有逗号。
7. **不支持行尾注释。** `confidence: high  # 待复核` 会把整串当成值，confidence 变成空值，不告警；`record: company  # 公司` 会报「不在六记录内」。只用整行注释（`#` 开头）。

**让 grounding_page.py 抽到字段的句式**（源码里的正则）：

| 字段 | 中文句式 | 英文句式 |
|---|---|---|
| 首段定义 | 「是一家 X」；或「类目是 X」 | "is a(n) X"；或 "category is X" |
| 差异点 | 「差异化是 X」 | "differentiated by X" |
| 总部 | 「总部位于 X」「总部在 X」 | "headquartered in X"、"based in X" |
| 成立 | 「成立于 2015 年」「创办于 2015 年」 | "founded in 2015" |
| 创始人 | 「创始人是 X」 | "founded by X" |
| 竞对 | 「主要竞对是 X」 | "competitors are/include X" |
| 首要客户 | 「首要客户画像：X」 | "primary audience: X" |
| 产品线 | 「产品线……：X」 | "product lineup/plans include: X" |

中文 fact 的汉字数不少于拉丁词数时，页面用中文句式。含「从不、审批、可以宣称、不能宣称、白名单、黑名单」的 fact 被当作政策，不进页面的易变事实区。

**示例**（虚构品牌；`brand.yaml`，只含可公开事实）：

```yaml
brand: Acme
facts:
  # ---- Company ----
  - fact: "Acme 是一家客户关系管理(CRM)软件公司,总部在柏林"
    record: company
    source: https://acme.example/about
    date: 2026-08-12
    confidence: high
  - fact: "Acme 成立于 2015 年"
    record: company
    source: https://acme.example/about
    date: 2026-08-12
    confidence: high
  - fact: "Acme 的差异化是“部署 10 分钟上手”"
    record: company
    source: https://acme.example/positioning
    date: 2026-09-28
    confidence: high
  - fact: "消歧:Acme 不是 Acme Corp(美国保险集团)"
    record: company
    source: https://acme.example/about
    date: 2026-09-28
    confidence: high
    disambiguation: true
  - fact: "Acme 的领英公司主页"
    record: company
    source: https://www.linkedin.com/company/acme-example
    date: 2026-09-28
    confidence: high
  # ---- Market ----
  - fact: "Acme 所在类目是中小团队 CRM"
    record: market
    source: https://acme.example/positioning
    date: 2026-09-28
    confidence: high
  - fact: "Acme 的主要竞对是 HubSpot、Pipedrive 与 Zoho CRM"
    record: market
    source: https://acme.example/positioning
    date: 2026-09-28
    confidence: high
  # ---- Offerings ----
  - fact: "Acme 的产品线:Free 与 Pro"
    record: offerings
    source: https://acme.example/pricing
    date: 2026-10-01
    confidence: high
    keywords: [产品线, plans, product line]
  - fact: "Acme Pro 定价为 $49/月,按年计费为 $39/月"
    record: offerings
    source: https://acme.example/pricing
    date: 2026-10-01
    confidence: high
  - fact: "Acme Pro 计划提供 99.9% 月度可用性 SLA"
    record: offerings
    source: https://acme.example/legal/sla
    date: 2026-07-15
    confidence: high
  - fact: "Free 计划不含 SSO 登录"
    record: offerings
    source: https://docs.acme.example/sso
    date: 2026-07-20
    confidence: high
  # ---- Audience ----
  - fact: "首要客户画像:10-50 人的 B2B 销售团队"
    record: audience
    source: https://acme.example/positioning
    date: 2026-09-28
    confidence: high
  # ---- Strategy(只放已公开的)----
  - fact: "已公开的即将发布:Outlook 集成,2026 年 Q4 内上线"
    record: strategy
    source: https://acme.example/roadmap
    date: 2026-09-20
    confidence: med
```

`brand-internal.yaml` 的写法相同，例如：

```yaml
brand: Acme
facts:
  - fact: "不能宣称:已获得 SOC 2 认证——审计进行中,未发证"
    record: offerings
    source: https://docs.acme.example/security
    date: 2026-09-05
    confidence: high
    keywords: [SOC 2, SOC2]
  - fact: "从不宣称“永久免费”"
    record: execution
    source: internal/handbook
    date: 2026-08-30
    confidence: high
  - fact: "本季度优先级:邮件集成与移动端"
    record: strategy
    source: internal/okr-2026q4
    date: 2026-10-03
    confidence: med
```

批准术语（例如「写 Acme Pro，不写 ACME PRO」）不要写成 fact：`oracle_check.py` 匹配时不分大小写，这类规则会反复误报（实测）。把它写进 `ste_lint.py` 的术语表 CSV（`concept,preferred,forbidden`），用 `python3 scripts/ste_lint.py draft.md --glossary terms.csv` 查草稿；实测能报出 ACME PRO，放过 Acme Pro。

## 四、缺口协议

某条记录只有类目级描述、只有形容词没有出处，或者整库 fact 少于 25 条（`oracle_check.py` 的低样本警告线，本套件口径）时：

1. **一次只问一个问题**（Profound 的做法），并说明可以跳过（本套件约定）；不发问卷。
2. **答案回流**：写进对应记录，补 `source` 和 `date`；拿到一手来源前写 `confidence: low`。
3. 回流前，涉及这个缺口的内容只用于内部草稿，不进对外页面。

## 五、使用规则

- **起草任何对外内容前，先读两处禁区**：Offerings 的「不能宣称」和 Execution 的 never-do。正文里的数字、日期和是否判断，都要在 Brand Records 里找到对应 fact；找不到就先走缺口协议，不凭记忆写。
- **与 intake 衔接**：[intake 清单](../overview/intake-checklists.md)的问答直接沉淀为六类记录（公司→Company、市场与竞对→Market、产品与宣称边界→Offerings、受众→Audience、目标与排期→Strategy、流程与禁区→Execution）。新项目 intake 前先读现有文件，只问缺口。
- **核查 AI 回答**：

  ```bash
  jq --arg e chatgpt '[to_entries[] | {prompt: .key, engine: $e, text: .value}]' answers.json > responses.json
  python3 scripts/oracle_check.py --facts all.yaml --responses responses.json --out findings.json [--json]
  ```

  - `responses.json` 是数组 `[{prompt, engine, text, mentions?}]`：`text` 为空的条目跳过；`engine` 缺省记为 unknown；`mentions` 可以有，但不参与判定。
  - `citation_panel.py` 不导出这个格式。上面的 `jq` 把 `record --answer-file` 用的 `{prompt: 回答}` JSON 转成它；每个引擎转一次再合并。
  - 脚本只做正则近似：同类数字不同（货币按币种分桶）、日期或年份不同、同一关键词在事实和回答里肯定否定相反。涉及价格、安全、合规的 fact 判 critical，其余判 major。
  - 实测（虚构数据，2026-10-18）：报出了 $49 对 $59 的价格冲突、2015 对 2017 的成立年份冲突、SOC 2 和 Free 计划 SSO 的是否冲突；也有误报：回答里另一个上下文的年份撞上了含年份的 fact。给容易撞词的 fact 写 `keywords`，并保持一条 fact 一件事，可以减少误报。
  - `findings.json` 记每条 finding 的状态：`pending` → 人工改成 `acknowledged` 或 `ignored`；重跑时按指纹（引擎、prompt、回答序号、fact、AI 原句）保留状态。`ignored` 不计入 Inaccuracy%。
  - 指标：Inaccuracy% = 含有效 finding 的回答数 ÷ 回答总数；按引擎分列准确率；按记录分组统计出错主题。语义级矛盾（定位、受众、语气）由人判断，Possible sources 由人填。
- **维护**：每条 fact 的 `date` 是复核锚点。Grounding Page Standard 建议每 3–6 个月复核一次，最长不超过 12 个月（超过就不能再展示其 Human Verified 标记；[技术实施指南](https://groundingpage.com/spec/technical-implementation/)，核对 2026-10-21）；本套件的检查器用 183 天作为上限。

## 六、Grounding Page

**Standard v1.7 的 11 个构件与本套件检查器的对应**（Standard 原文见[技术实施指南](https://groundingpage.com/spec/technical-implementation/)，核对 2026-10-21；检查器指 `python3 scripts/grounding_page.py --check page.md --name "Acme"`）：

| Standard 构件 | Standard 的要求 | 检查器怎么查 | 差异 |
|---|---|---|---|
| 1 实体与页面主题 | 一页只讲一个主实体；子实体单独成页，只做链接 | 第 8 项 MANUAL | — |
| 2 页面标题 | H1 只写实体名，不写口号 | 第 1 项：唯一的 Markdown `# ` 标题等于 `--name` | 只认 Markdown 标题，HTML `<h1>` 判 FAIL |
| 3 首段定义 | 首段定义实体；整个导语 2–3 段：定义、定位、区分 | 第 2 项：H1 后第一段是一句含实体名的话，≤300 字符 | 只查第一段 |
| 4 独立成块的 H2 | 主要 H2 带实体名（必选） | 不查 | 人工核对 |
| 5 结构化事实 | 属性和值一一对应：`<dl>`、表格或资料卡都可以 | 第 3 项：要有 `<dt>`，出现 `<table>` 判 FAIL | 比 Standard 严 |
| 6 区分相似实体 | 推荐；自然写进导语、FAQ 或专节；生硬的「它不是什么」列表是常见错误 | 第 6 项：要求 is-NOT 区块 | 比 Standard 严，写法相反 |
| 7 来源与时效 | 易变值带「截至」日期；人工审核后才显示审核人和日期，并写入 `reviewedBy`、`lastReviewed` | 第 5 项：易变区块要有「Last reviewed:」行；第 10 项：「最后复核:」或「Last reviewed:」后的日期 ≤183 天 | Standard 的标签「Last reviewed by a human:」匹配不上；生成器自动把生成当天写成复核日期，Standard 禁止这样做 |
| 8 JSON-LD 镜像 | 必选；只镜像页面可见内容；可见 FAQ 可以镜像为 FAQPage | 第 7 项：有 JSON-LD、name 一致、字符串值都在可见文本里；出现 FAQPage 判 FAIL | FAQPage 一条比 Standard 严（本套件口径：Google FAQ 富结果已停展，见 [deprecated-signals.md](../technical/deprecated-signals.md)） |
| 9 内部链接 | 页脚链接、`/facts/` 总览页、正文里的上下文链接 | 第 9 项：页面里出现 isPartOf 和 hasPart 字样 | 生成器写进的注释就能让它通过，人工核对真实链接 |
| 10 品牌与页面设计 | 用站点自己的页头页脚，不做成技术附录 | 不查 | 人工核对 |
| 11 质量与维护 | 每 3–6 个月复核，最长 12 个月 | 第 10 项（同上） | — |

Standard 还要求：FAQ 是可选的；检查器第 4 项却要求 5–10 条 FAQ、每个答案含实体名（本套件口径，比 Standard 严）。URL 用独立页面，例如 `/facts/`；检查器第 11 项 MANUAL。

**生成与发布步骤**

1. `python3 scripts/grounding_page.py --facts brand.yaml --name "Acme" --out grounding-page.md`（`--type` 可选 Organization、SoftwareApplication、Person）。只用可公开的 `brand.yaml`。
2. `rg -n "internal/" grounding-page.md` 应该没有命中。
3. 人工补齐：sameAs 只填真实档案 URL；按 Standard 把导语写满定义、定位、区分；主要 H2 带实体名。
4. **复核日期改成人工审核的真实日期**，写上审核人，并在 JSON-LD 的 WebPage 节点写 `reviewedBy`、`lastReviewed`。不要保留生成器写的当天日期。
5. `python3 scripts/grounding_page.py --check grounding-page.md --name "Acme"`：FAIL 项改到通过；MANUAL 项和上表「差异」列逐项人工确认。

**生成器输出的骨架**（上面的示例实跑，2026-10-21，节选；`--check` 结果 PASS 9 / FAIL 0 / MANUAL 2）：

```markdown
# Acme

Acme 是一家客户关系管理(CRM)软件公司,以部署 10 分钟上手为差异化。

Entity type: Organization · Status: verified · Updated: 生成当天

## Core facts(稳定事实)

<dl>
  <dt>类目</dt><dd>中小团队 CRM</dd>
  <dt>成立</dt><dd>2015 年</dd>
  <dt>总部</dt><dd>柏林</dd>
</dl>

<section id="volatile">
<h2>易变事实(定价/客户数/平台与功能…)</h2>
<p>Last reviewed: 2026-10-01</p>
<dl>
  <dt>定价</dt><dd>Acme Pro 定价为 $49/月,按年计费为 $39/月(2026-10-01 复核)</dd>
</dl>
</section>

<section id="is-not">
<h2>Acme 不是</h2>
<ul>
  <li>Acme 不是 Acme Corp(美国保险集团)</li>
</ul>
</section>

最后复核:生成当天 · Status: verified · Entity type: Organization

<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "Organization", "name": "Acme", "foundingDate": "2015",
 "sameAs": ["https://www.linkedin.com/company/acme-example"]}
</script>
```

骨架里「最后复核」后的日期是生成器写的生成日期，按第 4 步换成人工审核日期。

## 检查清单

1. **两个脚本都能读全** → `python3 scripts/oracle_check.py --facts all.yaml --responses responses.json --out findings.json --json | jq .facts_count`；`python3 scripts/grounding_page.py --facts brand.yaml --json` → 通过：条数等于你写的 fact 条数，没有「不在六记录内」告警；失败：条数变少（多半是列表项没缩进），或出现该告警（多半是行尾注释）。
2. **一条 fact 一件事** → 人工逐条读 → 通过：每条只断言一件可判定的事；失败：一条里塞了产品线和术语规则这类两件事。
3. **公开文件不含内部事实** → `rg -n "internal/" brand.yaml grounding-page.md` → 通过：没有命中；失败：有。
4. **禁区已读** → 起草记录里列出引用过的「不能宣称」和 never-do 条目 → 通过：有；失败：没有。
5. **核查已跑并复核** → `findings.json` 里没有 `pending` → 通过：每条已改成 acknowledged 或 ignored，critical 先处理；失败：还有 pending。
6. **页面合规** → `grounding_page.py --check` → 通过：没有 FAIL，第六节表格「差异」列逐项人工确认；失败：有 FAIL，或复核日期仍是生成日期。
7. **复核不过期** → 页面可见复核日期 → 通过：≤183 天，且是人工审核日期；失败：超期，或日期由脚本自动写入。
8. **术语一致** → `ste_lint.py draft.md --glossary terms.csv` → 通过：没有 STE-TERM；失败：有。
