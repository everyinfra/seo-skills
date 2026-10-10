#!/usr/bin/env python3
"""统一审计数据封套 + findings 部分落盘契约(claude-seo 口径,borrow-specs.md E4;stdlib only)。
三源合一:site_audit.py --json(必需,发现来源)/ health_score.py --json(可选,主分与分档)/
prioritize.py --json(可选,impact 与修复文案)→ out-dir/ 统一 audit-data.json envelope
(供 monitor/notify/报告复用)+ REPORT.md(人读摘要)+ findings/<category>.md(逐类别人读表格)。

**findings 部分落盘契约**(核心,borrow-specs E4 原文口径):
每聚合完一个检查类别**立即**落盘 findings/<category>.md,全部分派完才写
audit-data.json 与 REPORT.md——设计意图:长审计/agent 编排被 maxTurns/超时掐断时,
已完成类别的结果不丢;--resume 重跑时 out-dir 已有 findings/*.md 的类别跳过重建,
类别明细自文末 envelope-category-v1 注释行无损回读(人读表格保持不动,计数随明细
一并回读)。--resume 只认当前输入出现的类别——旧 run 遗留的过期文件不混入 envelope
(留在盘上不删);无标记行/标记损坏的文件视为不可恢复,重建覆盖。

envelope(audit-data.json)结构:
  {schema_version:1, generated_at, source_urls[], inputs{health,priority 降级标记},
   summary{main_score,band,ai_search_health,top_findings[](severity×受影响面前三),
          quick_wins[](高 impact 且易修,≤3)},
   categories[{name,findings[{rule_id,title,severity,description,recommendation,
                              affected_urls(≤20),affected}]}],
   action_plan{phases[{name:"立即(本周)"|"短期(月内)"|"持续",items[]}]}}

phases 分派:CRITICAL→立即(本周);WARN 且 impact≥1.0→短期(月内);其余→持续。
impact 优先取 --priority(仅采信 hit_urls>0 的规则,prioritize 口径含放大器);
缺该输入按 severity×受影响面估算(受影响占比×权重,权重 CRITICAL=3/WARN=2/INFO=1
与 prioritize.py 同源)。--health/--priority 缺失 → 对应字段标 source_missing
(main_score/band 与 inputs 节)、impact 用估算,envelope 不因缺输入失败;
显式提供了但格式不符 → 退出码 2(不静默降级)。

类别=Lumar 六大类(映射与 health_score.MAPPING 第一列同源;envelope 保持 standalone
不 import 兄弟脚本,未知 area 归 other)。envelope 以 audit 发现为唯一发现源:
priority 仅供给 impact/修复文案,其特有规则(depth_deep/url_long 等无对应 audit
检查)不进 envelope——那部分信息保留在 prioritize.py 自己的输出里。

用法: python3 envelope.py --audit audit.json [--health health.json]
                          [--priority prioritize.json] [--out-dir ./audit-run/]
                          [--resume] [--json]
退出码: 0 正常 / 2 输入或参数错误。"""
import json
import os
import sys
from datetime import datetime, timezone

SCHEMA_VERSION = 1
DEFAULT_OUT_DIR = "./audit-run/"
SEVS = ("CRITICAL", "WARN", "INFO")
SEV_ORDER = {"CRITICAL": 0, "WARN": 1, "INFO": 2}
SEV_WEIGHT = {"CRITICAL": 3.0, "WARN": 2.0, "INFO": 1.0}  # 与 prioritize.py SEV_WEIGHT 同源
HIGH_IMPACT = 1.0     # 高 impact 阈值:受影响占比×严重度权重≥1(≈50% URL 命中 WARN 量级)
URL_CAP = 20          # affected_urls 封顶(与 prioritize.url_query 同款上限)
CATEGORY_ORDER = ("availability", "indexability", "uniqueness", "discoverability",
                  "rankability", "experience", "other")
PHASE_NAMES = ("立即(本周)", "短期(月内)", "持续")
MARKER = "envelope-category-v1"  # findings/*.md 文末机器回读标记(--resume 无损恢复用)

# 易修规则(quick_wins 候选):文案/模板/单文件级改动;rendering/robots/fetch 等架构或
# 策略级改动不算易修【自定口径,claude-seo 无官方易修清单】
EASY_FIX = frozenset(("title", "description", "h1", "headings", "og", "schema",
                      "images", "llms.txt", "sitemap", "a11y"))

# audit area → Lumar 类别(与 health_score.MAPPING 第一列同源的本地裁剪,两边映射漂移由
# test_envelope 钉死关键 area;duplicate_title 为 health_score 派生规则,仅当 audit 直接
# 输出该 area 时出现)。未知 area → other。
AREA_CATEGORY = {
    "fetch": "availability",
    "staging": "indexability", "robots": "indexability", "ai-bots": "indexability",
    "canonical": "indexability",
    "duplicate_title": "uniqueness",
    "links": "discoverability", "sitemap": "discoverability",
    "llms.txt": "discoverability", "a11y": "discoverability",
    "title": "rankability", "description": "rankability", "h1": "rankability",
    "headings": "rankability", "content": "rankability", "images": "rankability",
    "schema": "rankability", "og": "rankability", "rendering": "rankability",
    "semantic-html": "rankability", "bluf": "rankability", "freshness": "rankability",
}

# 人读标题 / 本地兜底修复文案(priority 命中该规则时用其 fix_instruction——那里带
# 条件依赖型语义;未命中才走这里的静态文案)
TITLES = {
    "fetch": "抓取失败", "staging": "staging 子域公开", "robots": "noindex/robots 屏蔽",
    "ai-bots": "AI 检索 bot 被禁", "canonical": "canonical 缺失/异常",
    "title": "title 缺失/越限", "description": "description 缺失/越限",
    "h1": "H1 缺失/多个", "headings": "标题层级跳级", "content": "内容词数异常",
    "images": "alt 缺失", "schema": "无 JSON-LD", "og": "og 标签缺失",
    "links": "页内链接过多", "sitemap": "sitemap 不可达", "llms.txt": "llms.txt 缺失",
    "a11y": "html 无 lang", "rendering": "渲染依赖过重",
    "semantic-html": "语义 HTML 比值低", "bluf": "BLUF 答案未前置",
    "freshness": "内容不新鲜", "duplicate_title": "批内 title 重复",
}
RECOS = {
    "fetch": "先恢复 200 可达再谈其他(HTTP 错误/超时排查)",
    "staging": "staging 子域加鉴权或整站屏蔽",
    "robots": "检查 noindex/nosnippet 是否误设;按页面意图决定保留或移除",
    "ai-bots": "robots.txt 放行 8 个 AI 检索 bot(Semrush 名单)",
    "canonical": "canonical 改绝对 URL 并自指(指他页需先对比权重)",
    "title": "补/改 title:每页唯一,50-60 字符",
    "description": "补/改 description:~155 字符,含利益点与 CTA",
    "h1": "每页唯一 H1(与 title 呼应但不重复)",
    "headings": "消除标题跳级(h1→h2→h3 逐级)",
    "content": "词数<200 增补实质内容;>15000 拆分长文",
    "images": "补 img alt(覆盖到 80% 以上)",
    "schema": "补 JSON-LD(按页型选 Organization/Article/Breadcrumb 等)",
    "og": "补 og:title/og:description/og:image(image 用绝对 URL)",
    "links": "页内链接>100 时精简导航或分页",
    "sitemap": "补 /sitemap.xml 并在 robots.txt 声明",
    "llms.txt": "补 /llms.txt(AI 发现层)",
    "a11y": "html 标签补 lang 属性",
    "rendering": "关键内容服务端渲染;压缩 JS;补 noscript 回退",
    "semantic-html": "模板改用语义标签(header/main/article/section)",
    "bluf": "答案前置(首屏直答短语+要点列表)",
    "freshness": "更新内容并回填 Last-Modified",
    "duplicate_title": "批内重复 title 差异化改写",
}

# prioritize 规则 id → audit area(impact/修复文案供给的桥);未列出的规则 id 若恰为
# audit area 名(health_score 摘要输入路径下原样透传的 og/schema/bluf 等)按恒等映射;
# 其余(depth_deep/url_long/redirect_canonical_conflict 等无对应 audit 检查)忽略。
RULE_TO_AREA = {
    "title_missing": "title", "title_short": "title",
    "desc_missing": "description", "desc_short": "description",
    "h1_missing": "h1", "fetch_error": "fetch", "staging_exposed": "staging",
    "canonical_invalid": "canonical", "canonical_mismatch": "canonical",
    "canonical_pagerank": "canonical",
    "noindex_intent": "robots", "not_indexed_with_traffic": "robots",
    "thin_content": "content", "duplicate_body": "duplicate_title",
    "inlinks_low": "links",
}

USAGE = """usage: envelope.py --audit audit.json [--health health.json] [--priority prioritize.json]
                    [--out-dir DIR] [--resume] [--json]
统一审计数据封套(claude-seo envelope 口径,borrow-specs E4):
  读 site_audit.py --json(必需,发现来源)+ health_score.py --json(可选,主分/分档)+
  prioritize.py --json(可选,impact/修复文案)→ out-dir/ 下:
    audit-data.json   统一 envelope(供 monitor/notify/报告复用)
    REPORT.md         人读摘要
    findings/<category>.md  逐类别人读表格(文末 envelope-category-v1 注释行为机器回读数据)
落盘契约(防中断丢结果):
  每聚合完一个类别立即写 findings/<category>.md;全部分派完才写 audit-data.json 与
  REPORT.md——长审计/agent 编排被掐断时已完成部分不丢;--resume 跳过已有 findings/*.md
  的类别(明细自落盘文件回读,人读表格不动;仅认当前输入出现的类别,旧 run 的过期
  文件不混入,亦不删除)。
envelope 结构:
  {schema_version:1, generated_at, source_urls[], inputs{health,priority 降级标记},
   summary{main_score,band,ai_search_health,top_findings[](前三),
          quick_wins[](高 impact 且易修,≤3)},
   categories[{name,findings[{rule_id,title,severity,description,recommendation,
                              affected_urls(≤20),affected}]}],
   action_plan{phases[{name:"立即(本周)"|"短期(月内)"|"持续",items[]}]} }
phases 分派: CRITICAL→立即(本周);WARN 且 impact≥1.0→短期(月内);其余→持续。
  impact 优先取 --priority(仅采信 hit_urls>0 的规则);缺输入按 severity×受影响面
  估算(受影响占比×权重 CRITICAL=3/WARN=2/INFO=1,与 prioritize.py 同源)。
降级: --health/--priority 缺失 → main_score/band 与 inputs 节标 source_missing、
  impact 用估算,envelope 不失败;显式提供但格式不符 → 退出码 2(不静默降级)。
选项:
  --audit audit.json          site_audit.py --json 输出(必填)
  --health health.json        health_score.py --json 输出(可选;main_score/band)
  --priority prioritize.json  prioritize.py --json 输出(可选;impact/修复文案)
  --out-dir DIR               输出目录(默认 ./audit-run/)
  --resume                    已有 findings/*.md 的类别跳过重建(自落盘文件回读)
  --json                      打印 envelope 到 stdout,不落盘(不写任何文件;
                              --resume 仍可从 out-dir 回读已有类别)
退出码: 0 正常 / 2 输入或参数错误。"""


def die(msg):
    """输入/参数错误 → stderr + 退出码 2。"""
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def check_audit(d):
    if not isinstance(d.get("results"), dict):
        return "缺 results 字典(应为 site_audit.py --json 输出)"
    return None


def check_health(d):
    ms = d.get("main_score")
    if isinstance(ms, bool) or not isinstance(ms, (int, float)):
        return "缺数值 main_score(应为 health_score.py --json 输出)"
    if not isinstance(d.get("band"), str):
        return "缺 band 字符串"
    return None


def check_priority(d):
    if not isinstance(d.get("fix_now"), list):
        return "缺 fix_now 列表(应为 prioritize.py --json 输出)"
    return None


def load_blob(path, what, check):
    """容错读 JSON(文件前部混有逐 URL 文本行时从每个 '{' 起点试解,末位候选胜出,
    与 health_score.load_audit 同法);check(data) 返回错误文案或 None;
    读不了/解析不出/check 不过 → 退出码 2。"""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        die("读不了 %s: %s" % (what, e))
    data = None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        for i, ch in enumerate(text):
            if ch != "{":
                continue
            try:
                cand = json.loads(text[i:])
            except json.JSONDecodeError:
                continue
            if isinstance(cand, dict):
                data = cand   # 不 break:末位的完整 blob 赢过早位的 meta 行片段
    if not isinstance(data, dict):
        die("无法从 %s 解析出 JSON: %s" % (what, path))
    err = check(data)
    if err:
        die("%s 格式不符: %s(%s)" % (what, err, path))
    return data


def aggregate(audit):
    """audit.results → (source_urls, 可评分 URL 列表, {area: {urls,sevs,msgs}})。
    拒审(verdict=refused 或含 SKIP)URL 进 source_urls 但不产生发现、不进分母
    (与 health_score 同口径:拒审≠失败)。"""
    results = audit["results"]
    source_urls, scored, rules = [], [], {}
    for url, rec in results.items():
        if not isinstance(rec, dict):
            continue
        findings = [f for f in (rec.get("findings") or []) if isinstance(f, dict)]
        source_urls.append(url)
        if rec.get("verdict") == "refused" or any(f.get("severity") == "SKIP" for f in findings):
            continue
        scored.append(url)
        for f in findings:
            sev, area = f.get("severity"), f.get("area")
            if sev not in SEVS or not isinstance(area, str) or not area:
                continue
            d = rules.setdefault(area, {"urls": [], "sevs": [], "msgs": {}})
            if url not in d["urls"]:
                d["urls"].append(url)
            d["sevs"].append(sev)
            msg = str(f.get("message", ""))
            d["msgs"][msg] = d["msgs"].get(msg, 0) + 1
    return source_urls, scored, rules


def index_priority(priority, known_areas):
    """prioritize 输出 → {area: [命中(hi_urls>0)的 item,...]}(impact/修复文案供给方)。
    规则 id 经 RULE_TO_AREA 桥接;未列出但恰为 audit area 名的按恒等映射(health_score
    摘要输入路径下 area 原样透传);无对应 audit 检查的规则忽略(envelope 以 audit
    发现为唯一发现源)。"""
    by_area = {}
    items = (priority.get("fix_now") or []) + (priority.get("explore") or [])
    for it in items:
        if not isinstance(it, dict):
            continue
        hits = it.get("hit_urls", 0)
        if isinstance(hits, bool) or not isinstance(hits, (int, float)) or hits <= 0:
            continue   # 只采信真正命中(hit_urls>0)的规则,0 命中不覆盖估算
        rid = it.get("rule")
        if rid in RULE_TO_AREA:
            area = RULE_TO_AREA[rid]
        elif rid in known_areas:
            area = rid
        else:
            continue
        by_area.setdefault(area, []).append(it)
    return by_area


def build_finding(area, agg, total, prio_items):
    """一个 area 聚合为一条 envelope finding;修复文案 priority 命中(impact 最高者)
    > 本地 RECO 兜底。"""
    sev = min(agg["sevs"], key=lambda s: SEV_ORDER[s])
    affected = len(agg["urls"])
    # 最常见表现:频次最高;并列取首见(dict 保插入序,max 先遇到者胜)
    top_msg = max(agg["msgs"], key=lambda m: agg["msgs"][m]) if agg["msgs"] else ""
    pct = round(affected / total * 100) if total else 0
    description = "命中 %d/%d URL(%d%%);最常见表现: %s" % (affected, total, pct, top_msg)
    reco = None
    if prio_items:
        reco = max(prio_items, key=lambda it: (it.get("impact") or 0)).get("fix_instruction")
    if not reco:
        reco = RECOS.get(area, "参照 site_audit.py 报告中 %s 检查的说明修复" % area)
    return {"rule_id": area, "title": TITLES.get(area, area), "severity": sev,
            "description": description, "recommendation": reco,
            "affected_urls": agg["urls"][:URL_CAP], "affected": affected}


def impact_of(area, sev, affected, total, prio_items):
    """(impact, 来源):priority 有命中规则 → 其最大 impact(prioritize 口径含放大器);
    否则估算 = 受影响占比 × 严重度权重(prioritize 同款权重,无放大器)。"""
    if prio_items:
        return round(max(it.get("impact") or 0 for it in prio_items), 4), "priority"
    est = round(affected / total * SEV_WEIGHT[sev], 4) if total else 0.0
    return est, "estimated"


def ai_health_mean(audit):
    """AI Search Health 子分样本均值(site_audit 每页 ai_search_health.score);
    一页都没有 → source_missing。"""
    vals = []
    for rec in audit["results"].values():
        ai = rec.get("ai_search_health") if isinstance(rec, dict) else None
        if isinstance(ai, dict):
            s = ai.get("score")
            if isinstance(s, (int, float)) and not isinstance(s, bool):
                vals.append(s)
    return round(sum(vals) / len(vals), 1) if vals else "source_missing"


def render_category_md(cat, findings, total):
    """findings/<category>.md:人读表格 + 明细 + 文末机器回读注释行(--resume 依赖)。"""
    L = ["# findings: %s" % cat, "",
         "%d 项发现;文末 %s 注释行为机器回读数据(--resume 依赖,勿删)" % (len(findings), MARKER),
         "",
         "| rule_id | severity | affected | title |", "|---|---|---|---|"]
    for f in findings:
        L.append("| %s | %s | %d/%d | %s |" % (f["rule_id"], f["severity"],
                                               f["affected"], total, f["title"]))
    L += ["", "## 明细"]
    for f in findings:
        L += ["", "### %s [%s] %d/%d URL" % (f["rule_id"], f["severity"], f["affected"], total),
              "- description: %s" % f["description"],
              "- recommendation: %s" % f["recommendation"],
              "- affected_urls(%d):" % len(f["affected_urls"])]
        L += ["  - %s" % u for u in f["affected_urls"]] or ["  - (无)"]
    payload = json.dumps({"name": cat, "findings": findings},
                         ensure_ascii=False, separators=(",", ":"))
    L += ["", "<!-- %s %s -->" % (MARKER, payload), ""]
    return "\n".join(L)


def parse_category_md(path):
    """从 findings/<category>.md 回读类别 payload(仅认 %s 注释行);
    无标记/解析失败 → None(调用方重建该类别)。"""
    prefix = "<!-- %s " % MARKER
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s.startswith(prefix) and s.endswith("-->"):
                    payload = json.loads(s[len(prefix):-3])
                    if isinstance(payload, dict) and isinstance(payload.get("findings"), list):
                        return payload
    except (OSError, json.JSONDecodeError):
        pass
    return None


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def render_report(env):
    """REPORT.md:envelope 的人读摘要(分数卡/Top findings/Quick wins/行动计划/类别索引)。"""
    s, inp = env["summary"], env["inputs"]
    ai = s["ai_search_health"]
    L = ["# SEO 审计 envelope 报告(audit-data.json 人读摘要)", "",
         "- 生成时间: %s" % env["generated_at"],
         "- 样本: %d URL(source_urls 见 audit-data.json;coverage: 基于样本,"
         "不可外推到未爬取页面)" % len(env["source_urls"]),
         "- 主分(health_score): %s" % ("%s(%s)" % (s["main_score"], s["band"])
                                        if inp["health"] == "ok"
                                        else "source_missing(未提供 --health)"),
         "- AI Search Health(site_audit 样本均值): %s" % (
             "%s/100" % ai if isinstance(ai, (int, float)) else "source_missing"),
         "- impact 口径: %s" % ("--priority 输入(未覆盖的规则按 severity×受影响面估算)"
                                if inp["priority"] == "ok"
                                else "估算(severity×受影响面;未提供 --priority)"),
         "",
         "## Top findings(前 3)"]
    if s["top_findings"]:
        L += ["%d. [%s] %s —— %d URL" % (i, f["severity"], f["title"], f["affected"])
              for i, f in enumerate(s["top_findings"], 1)]
    else:
        L.append("- (无发现)")
    L += ["", "## Quick wins(高 impact 且易修,至多 3)"]
    if s["quick_wins"]:
        src_label = {"priority": "priority 输入", "estimated": "估算"}
        L += ["%d. [%s] %s —— impact %s(%s): %s"
              % (i, f["severity"], f["title"], f["impact"],
                 src_label.get(f["impact_source"], f["impact_source"]), f["recommendation"])
              for i, f in enumerate(s["quick_wins"], 1)]
    else:
        L.append("- (无)")
    L += ["", "## 行动计划"]
    for ph in env["action_plan"]["phases"]:
        L += ["", "### %s(%d 项)" % (ph["name"], len(ph["items"]))]
        L += ["- [%s] %s: %s(impact %s)" % (it["severity"], it["title"], it["action"],
                                            it["impact"]) for it in ph["items"]] or ["- (无)"]
    L += ["", "## 类别明细(人读表格见 findings/<category>.md)"]
    L += ["- %s: %d 项发现" % (c["name"], len(c["findings"])) for c in env["categories"]] \
        or ["- (无发现)"]
    L.append("")
    return "\n".join(L)


def build_envelope(audit, health, priority, out_dir, resume, persist):
    """聚合三源 → (envelope, stats)。persist=True 时执行部分落盘契约:
    逐类别先落盘 findings/*.md,全部分派完才写 audit-data.json 与 REPORT.md;
    resume=True 时已有 findings/*.md 的类别跳过重建(自落盘文件回读)。"""
    source_urls, scored, rules = aggregate(audit)
    total = len(scored)
    prio_by_area = index_priority(priority, set(rules)) if priority else {}
    sev_of = {a: min(d["sevs"], key=lambda s: SEV_ORDER[s]) for a, d in rules.items()}
    # 当前输入将产出的类别集合(--resume 只认交集:旧 run 遗留的过期文件不混入)
    present = {}
    for area in rules:
        present.setdefault(AREA_CATEGORY.get(area, "other"), []).append(area)
    findings_dir = os.path.join(out_dir, "findings")
    if persist:
        os.makedirs(findings_dir, exist_ok=True)
    categories, skipped, written = [], [], []
    for cat in CATEGORY_ORDER:
        if cat not in present:
            continue
        md_path = os.path.join(findings_dir, "%s.md" % cat)
        payload = None
        if resume and os.path.isfile(md_path):
            payload = parse_category_md(md_path)   # 无标记/损坏 → None → 重建覆盖
            if payload is not None:
                skipped.append(cat)
        if payload is None:
            # 重建:类别内规则按 严重度 > 受影响数 > rule_id 排序(确定性输出)
            areas = sorted(present[cat],
                           key=lambda a: (SEV_ORDER[sev_of[a]], -len(rules[a]["urls"]), a))
            findings = [build_finding(a, rules[a], total, prio_by_area.get(a)) for a in areas]
            payload = {"name": cat, "findings": findings}
            if persist:
                # 部分落盘契约核心:此类别一聚合完立即写盘——本类别之后的流程被
                # 掐断(长审计/agent 编排超时)时,已完成部分不丢;--resume 可跳过
                write_text(md_path, render_category_md(cat, findings, total))
                written.append(cat)
        categories.append(payload)
    # ---- 全部分派完:汇总 summary 与 action_plan,再落盘 envelope 与 REPORT ----
    flat = [f for c in categories for f in c["findings"]]
    impacts = {f["rule_id"]: impact_of(f["rule_id"], f["severity"], f["affected"], total,
                                       prio_by_area.get(f["rule_id"])) for f in flat}
    top = sorted(flat, key=lambda f: (SEV_ORDER[f["severity"]], -f["affected"], f["rule_id"]))
    quick_wins = []
    for f in sorted(flat, key=lambda f: (-impacts[f["rule_id"]][0], f["rule_id"])):
        if len(quick_wins) >= 3:
            break
        imp, src = impacts[f["rule_id"]]
        if f["rule_id"] in EASY_FIX and imp >= HIGH_IMPACT:
            quick_wins.append({"rule_id": f["rule_id"], "title": f["title"],
                               "severity": f["severity"], "impact": imp,
                               "impact_source": src, "recommendation": f["recommendation"]})
    phases = [{"name": n, "items": []} for n in PHASE_NAMES]
    for f in top:
        imp, src = impacts[f["rule_id"]]
        item = {"rule_id": f["rule_id"], "title": f["title"], "severity": f["severity"],
                "impact": imp, "impact_source": src, "action": f["recommendation"]}
        if f["severity"] == "CRITICAL":
            phases[0]["items"].append(item)       # CRITICAL → 立即(本周)
        elif f["severity"] == "WARN" and imp >= HIGH_IMPACT:
            phases[1]["items"].append(item)       # WARN+高 impact → 短期(月内)
        else:
            phases[2]["items"].append(item)       # 其余(INFO/WARN 低 impact)→ 持续
    envelope = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_urls": source_urls,
        "inputs": {"audit": "ok",
                   "health": "ok" if health else "source_missing",
                   "priority": "ok" if priority else "source_missing"},
        "summary": {
            "main_score": health["main_score"] if health else "source_missing",
            "band": health["band"] if health else "source_missing",
            "ai_search_health": ai_health_mean(audit),
            "top_findings": [{"rule_id": f["rule_id"], "title": f["title"],
                              "severity": f["severity"], "affected": f["affected"]}
                             for f in top[:3]],
            "quick_wins": quick_wins,
        },
        "categories": categories,
        "action_plan": {"phases": phases},
    }
    if persist:
        write_text(os.path.join(out_dir, "audit-data.json"),
                   json.dumps(envelope, ensure_ascii=False, indent=1) + "\n")
        write_text(os.path.join(out_dir, "REPORT.md"), render_report(envelope))
    stats = {"scored": total, "source": len(source_urls),
             "refused": len(source_urls) - total,
             "skipped": skipped, "written": written}
    return envelope, stats


def main():
    argv = sys.argv[1:]
    if any(a in ("-h", "--help") for a in argv):
        print(USAGE)
        return
    val = {"--audit": None, "--health": None, "--priority": None, "--out-dir": DEFAULT_OUT_DIR}
    flag = {"--resume": False, "--json": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in val:
            if i + 1 >= len(argv):
                die("%s 需要一个值" % a)
            val[a] = argv[i + 1]; i += 2
        elif a in flag:
            flag[a] = True; i += 1
        else:
            sys.stderr.write(USAGE + "\n"); sys.exit(2)
    if not val["--audit"]:
        sys.stderr.write("缺少 --audit\n" + USAGE + "\n")
        sys.exit(2)
    audit = load_blob(val["--audit"], "--audit", check_audit)
    health = load_blob(val["--health"], "--health", check_health) if val["--health"] else None
    priority = (load_blob(val["--priority"], "--priority", check_priority)
                if val["--priority"] else None)
    env, stats = build_envelope(audit, health, priority, val["--out-dir"],
                                resume=flag["--resume"], persist=not flag["--json"])
    if flag["--json"]:
        # --json:envelope 只打到 stdout,不落盘(--resume 仍可从 out-dir 回读)
        print(json.dumps(env, ensure_ascii=False, indent=1))
        sys.exit(0)
    s = env["summary"]
    main_line = "%s(%s)" % (s["main_score"], s["band"]) if health else "source_missing"
    ai = s["ai_search_health"]
    ai_line = "%s/100" % ai if isinstance(ai, (int, float)) else "source_missing"
    tops = "; ".join("%s[%s] %d URL" % (f["title"], f["severity"], f["affected"])
                     for f in s["top_findings"]) or "(无)"
    print("envelope: %d URL 可评分(%d 来源,%d 拒审),%d 类别,%d 项发现 → %s"
          % (stats["scored"], stats["source"], stats["refused"], len(env["categories"]),
             sum(len(c["findings"]) for c in env["categories"]),
             os.path.abspath(val["--out-dir"])))
    print("  主分 %s | AI Search Health %s | Top: %s" % (main_line, ai_line, tops))
    if stats["skipped"]:
        print("  --resume: 跳过 %d 个已有 category(自落盘回读): %s"
              % (len(stats["skipped"]), ", ".join(stats["skipped"])))
    print("  已落盘: %s" % ", ".join(["findings/%s.md" % c for c in stats["written"]]
                                     + ["audit-data.json", "REPORT.md"]))
    sys.exit(0)


if __name__ == "__main__":
    main()
