# example.com 站点审计(dev 视图):主分 0.0/100(Weak)——单页样本上 2 条 CRITICAL(description/h1 缺失),修复面小且全部可由 fix_plan.py 预生成

_For: 工程师 · 母报告口径: full-seo-audit(dev 渲染见 [report-modes.md](../../templates/audit/report-modes.md)) · 渲染模式: dev · 上次审计基线: 无(首次,全部标"首次") · 分数来源: health_score.py(输入 evidence/01-site-audit.json) · 采样: 2026-10-10,1 URL(https://example.com)_

> **快照免责声明**:本报告是 2026-10-10 的单点时间快照,数据会漂移;示例展示的是交付物形态,不代表目标站现状。

## The answer(先读这段)

单 URL 抽样审计:16 条 finding(2 CRITICAL / 5 WARN 规则 / 6 INFO 规则,evidence/01)。主分 **0.0 → Weak**——不是因为问题多,而是分母只有 1 个 URL,且该 URL 命中 2 条 CRITICAL(description 缺失、无 H1),Ahrefs 口径下"无 CRITICAL 的 URL 占比"即 0/1(evidence/02)。修复全部可由 `fix_plan.py` dry-run 预生成 5 类修复物,预估 AI Search Health 70→100(+30,evidence/03)。半小时内可清完 CRITICAL。

## Today's priorities(前 5 条,严重级×受影响面×修复成本;全部"首次")

1. `description` 1/1(100%)· CRITICAL · 成本 S · 首次
2. `h1` 1/1(100%)· CRITICAL · 成本 S · 首次
3. `canonical` 1/1(100%)· WARN · 成本 S · 首次
4. `content` 1/1(100%,词数 27)· WARN · 成本 M · 首次
5. `schema` 1/1(100%,无 JSON-LD)· WARN · 成本 S · 首次

杠杆:整类修完比单条分散修提分多——当前最大杠杆类 **Rankability**(整组修完预期主分 0.0→100.0,反事实重算见 Methodology 第 5 步)。

## 修复清单(按类分组,组内 impact 降序)

> 受影响面全部为 1/1:单页样本下每条规则要么 100% 命中要么 0%。**bulk export 偏差声明**:样本仅 1 URL,未生成 `bulk-exports/*.csv`(单条规则导出与正文重复);受影响 URL 即 https://example.com 本身,故清单第五列标注"(本页)"。多页样本时按规范落盘。

### Rankability —— 整组修完预期主分 0.0→100.0(反事实重算 `--ignore` 本组 12 规则;主分增益全部来自 2 条 CRITICAL)
- [ ] `description` | meta description 缺失(0/155) | 1/1(100%) | 补 120-155 字符描述,或贴 fix_plan 生成的 meta 片段(占位符填实) | (本页)
- [ ] `h1` | 无 H1 | 1/1(100%) | 页面加唯一 H1(即页面主标题) | (本页)
- [ ] `content` | 词数 27 <200(soft-thin) | 1/1(100%) | 按提纲扩写,首段 100 词内直答 | (本页)
- [ ] `title` | 14 字符 <20(偏短) | 1/1(100%) | 补足到 20-60 字符 | (本页)
- [ ] `schema` | 无 JSON-LD | 1/1(100%) | 贴 WebSite+Organization 片段(FAQPage 勿新增,已退役) | (本页)
- [ ] `og` | og:title/og:description/og:image 全缺 | 1/1(100%) | 补全 3 项 OG 标签 | (本页)
- [ ] `headings` / `rendering` / `semantic-html` | H2=0;服务端文本 171 字;语义比值 0.0% | 1/1(100%) | 扩写时用语义标签分块(H1==1 且 H2>=2) | (本页)

### Indexability —— WARN 修复对主分 +0(CRITICAL 项 ai-bots/staging 均 0 命中);canonical 修后降重复判定风险
- [ ] `canonical` | 缺失 | 1/1(100%) | 加自指 canonical `<link rel="canonical" href="https://example.com">` | (本页)

### Discoverability / AI 可发现性 —— 主分 +0;AI Search Health 子分相关(70/100,evidence/01)
- [ ] `robots` | robots.txt 不可达 | 1/1(100%) | 贴 27 bot 三层模板(evidence/03 已生成,引用层 5 bot 必留) | (本页)
- [ ] `llms.txt` | /llms.txt 不可达 | 1/1(100%) | 贴骨架后补真实页面条目,`llmstxt.py validate` 校验 | (本页)
- [ ] `sitemap` | sitemap.xml 不可达 | 1/1(100%) | 单页站可选;加后再跑 sitemap_audit | (本页)

### 值得探索(impact=0,零命中)
- `fetch` / `staging` / `ai-bots` / `bluf` / `freshness` / `images` / `links` / `a11y`(evidence/02 双栏之"opportunity")——不进优先级,仅记录。

## 建议四字段(可证伪;示例取首条)

> 建议:补 meta description 与唯一 H1(2 条 CRITICAL)。
> - 第一性观察:2026-10-10 抓取 https://example.com,description 0/155 字符、H1 计数 0(evidence/01 results.meta)。
> - 依赖解锁关系:无前置(页面层是第一层);解锁后续 title/CTR 与 AI 引用优化——门面缺失时其余优化无展示载体。
> - 失败判定:上线 28 天后复跑 site_audit,description/h1 仍非 PASS 即失败(单页判定,无采样噪声)。
> - 先行指标:GSC 该 URL 展示量每 7 天看一次(修复前基线:本样本未接 GSC,首期先建基线)。

下次该看什么:修复后复跑本链,重点看 `semantic-html` 与 `headings` 是否随扩写转为 PASS(AI 引用相关);本次测不了什么:外链/权威、CWV、GSC 表现(单页静态审计无这些数据源;health_score 相应类别 N/A 不计分,evidence/02)。

## What could change this conclusion

- **分母=1 是最大噪声**:主分对任何 CRITICAL 都是 0/1→100% 命中;多页样本下同样的 finding 面可能只影响部分 URL,分数语义完全不同(Ryte coverage 口径:样本分不可与全站比较)。
- example.com 是 IANA 保留示例域,内容几十年不变;"词数 27/soft-thin"等 finding 对真实内容站的外推有限。
- robots.txt/sitemap/llms.txt "不可达"判定的是 2026-10-10 的响应;目标站随时可能补上。
- `ai-bots`/`staging`/`fetch` 三条 CRITICAL 规则零命中属"未触发"而非"通过"(无 robots.txt 时按默认放行处理,evidence/01 checks.detail)。

## Methodology(脚本链与精确命令行;均在 skill 根目录 skills/seo-suite/ 执行)

1. `python3 scripts/site_audit.py https://example.com --json > examples/site-audit-chain-example.com-20261010/evidence/01-site-audit.json`(真实抓取;退出码 1=存在 CRITICAL)
2. `python3 scripts/health_score.py --input examples/site-audit-chain-example.com-20261010/evidence/01-site-audit.json > examples/site-audit-chain-example.com-20261010/evidence/02-health-score.md`(退出码 1=Weak 档)
3. fix_plan 只吃纯 JSON(health_score 才容忍文本前缀),故按 health_score 同款解析抽取 `evidence/01-site-audit.pure.json` 后:`python3 scripts/fix_plan.py --audit examples/site-audit-chain-example.com-20261010/evidence/01-site-audit.pure.json --estimate > examples/site-audit-chain-example.com-20261010/evidence/03-fix-plan.md`(dry-run,未 `--apply`,零写盘)
4. Today's priorities 排序与受影响面:取自 evidence/02 impacts[](hit/total 未取整)。
5. 杠杆行反事实重算:`python3 scripts/health_score.py --input examples/site-audit-chain-example.com-20261010/evidence/01-site-audit.json --ignore description,h1,content,title,headings,rendering,semantic-html,bluf,freshness,images,schema,og --json` → main_score 100.0(Excellent);对照组 `--ignore canonical,og,links,a11y,content,title,schema` → warn_score 100.0 而 main_score 仍 0.0(印证"WARN 不扣主分")。

## Method Notes

- 数据源:site_audit.py 单页静态抓取(2026-10-10);无 GSC/GA/外链数据源,health_score 的 uniqueness/experience 类 N/A 不计合成分(evidence/02)。
- 主分口径:(无 CRITICAL URL 数÷内链 URL 总数)×100【Ahrefs 官方】;impact=命中占比×严重度²【Ryte 官方】;渲染规范见 [report-modes.md](../../templates/audit/report-modes.md)。
- 偏差记录(相对 report-modes dev 规范):① 未生成 bulk-exports/*.csv(1 URL 样本,见上偏差声明);② 修复成本 S/M 为人工标注;③ `{{new_since_last}}` 全部标"首次"(无基线)。
- 禁编造:全部数字可回溯 evidence/01(JSON)→02(分数/impact)→03(修复物与收益预估);本报告未引入任何 evidence 外的数字。
