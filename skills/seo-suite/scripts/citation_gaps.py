#!/usr/bin/env python3
"""引用缺口分析(citation gaps;geo-aeo-tracker 算法直译,输入为 citation_panel.py 的 panel.json)。stdlib-only。

qualifying cell = 有 cited_urls 且品牌未被引(state ∈ brand_absent/name_only_mention)的采样
cell;cited_brand=品牌已被引非缺口;failed/no_answer 不入(采集失败≠内容缺口)。
对每个被引 URL:registrable_domain 归域 → 排除自有域 → 累计
opp[url] = {count, prompts:set, providers:set, has_competitor_run:bool, competitors:set};
同一 cell 内重复 URL 去重(每答案每 URL 至多计 1 次,与 citation_panel 的 share 口径一致)。

竞品口径[推断]:panel.json 不记录竞品品牌清单,以"同 cell 共同被引的其他非自有域"代理
(geo-aeo-tracker 原版有显式竞品名单);has_competitor_run = 该 URL 所在 cell 有竞品
同场被引——唯一高优先判据。

排序:has_competitor_run 降序 → count 降序(URL 全局排序,CSV 同序);
域名分组聚合(总引用/页数/竞品数),同序。

输出:markdown 报告(域名分组表+Top 页面+外联提示)→ stdout;
--csv out.csv 列 Domain,URL,Citations,Prompts(|分隔),Providers,
                    Competitors Mentioned,Priority(High/Standard);
--json out.json 结构化(sets → 排序列表)。
外联提示口径(照抄 references/research/borrow-specs.md B2):
  竞品在场 → "竞品 {A,B} 在 {domain} 被引用——考虑贡献内容或争取列表位直接竞争"
  不在场   → "AI 模型在 {N} 个追踪 prompt 引用 {domain},获得收录可提升 AI 可见性"

来源五分类(Peec Source 五分类,规格 references/research/niubigeo-deep-read.md N3/B4):
  每个被引域名输出 Editorial/Corporate/UGC/Reference/Own website 五类之一 + 对应行动提示
  (Editorial→PR outreach / Corporate→合作目录 / UGC→社区运营 / Reference→更正词条 /
   Own→站内改造)。判定顺序:--domain-class overrides.json 人工覆盖 > 自有域 > 启发式
  (维基/词典→Reference;reddit/论坛/社区→UGC;媒体特征→Editorial;其余默认 Corporate)。
  启发式与默认均为 [推断] 规则,报告与 JSON 均附判定依据(basis);CSV 列保持七列不变。

gapLabel 七叉决策树(niubigeo keyword-metrics-engine 直译,deep-read N4;逐 prompt):
  0 条有效回答                                → "No completed AI answers"
  提及=0 且竞品独现>0                          → "Competitors own this AI answer space"(最高优先)
  提及=0                                      → "Target absent from AI answers"
  ownedRelevance≥0.6 且提及率<0.5              → "Owned content is not reflected"
  提及>0 且自有域被引=0                        → "Mentioned without official citation"
  竞品独现>0(偶发)                            → "Competitors still appear without target"
  其余                                        → "Covered in this audit"
  竞品口径[推断]:与 has_competitor_run 同代理(同 cell 非自有被引域),panel 无竞品名单。
  ownedRelevance 降级[注明]:该值为 niubigeo N7 词筛产出(站点证据对词相关度 0-1),
  panel.json 无此字段——用 --owned-relevance owned.json({prompt: 0-1}) 传入
  (或面板顶层 "owned_relevance" 对象);未提供时分支 4 不可判,如实落入后续分支。

与 cite_domain.py 串联:先用本脚本找目标域,再用 cite_domain.py 评级(先 gaps 后评级,
顺序不可倒——先评级后找域是浪费)。

用法:
  python3 citation_gaps.py --panel panel.json --brand-domains acme.ai,acme.com
  python3 citation_gaps.py --panel panel.json --csv gaps.csv --json gaps.json
  python3 citation_gaps.py --panel panel.json --domain-class overrides.json
  python3 citation_gaps.py --panel panel.json --owned-relevance owned.json
  python3 citation_gaps.py --self-test
"""
import argparse
import csv
import json
import os
import sys
import traceback

TOP_PAGES = 10
SL_TLD = {"co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au", "co.jp", "ne.jp",
          "or.jp", "com.cn", "net.cn", "org.cn", "com.br", "com.mx", "com.tr",
          "co.kr", "co.in", "co.za", "com.sg", "com.hk"}
CSV_HEADER = ["Domain", "URL", "Citations", "Prompts", "Providers",
              "Competitors Mentioned", "Priority"]

# ---------- 来源五分类(Peec Source 五分类;启发式与默认均 [推断],可 --domain-class 覆盖) ----------
SOURCE_CLASSES = ("Editorial", "Corporate", "UGC", "Reference", "Own")
SOURCE_CLASS_ACTIONS = {
    "Editorial": "PR outreach:媒体投稿/新闻源/专家引言,争取编辑报道",
    "Corporate": "合作目录:争取合作方目录、集成市场、对比页收录",
    "UGC": "社区运营:官方账号真实参与讨论与答疑,不做硬广",
    "Reference": "更正词条:核对词条事实,补充自有可靠来源",
    "Own": "站内改造:提升自有页可引用性(转 grounding_page.py / fix_plan.py)",
}
_CLASS_ALIASES = {"editorial": "Editorial", "corporate": "Corporate", "ugc": "UGC",
                  "reference": "Reference", "own": "Own", "own website": "Own"}
_REFERENCE_DOMAINS = {"wikipedia.org", "wikimedia.org", "wikidata.org", "wiktionary.org",
                      "britannica.com", "merriam-webster.com", "dictionary.com",
                      "oed.com", "zdic.net"}
_UGC_DOMAINS = {"reddit.com", "quora.com", "stackoverflow.com", "stackexchange.com",
                "superuser.com", "serverfault.com", "zhihu.com", "v2ex.com",
                "douban.com", "youtube.com"}
_EDITORIAL_DOMAINS = {"nytimes.com", "washingtonpost.com", "theguardian.com", "bbc.co.uk",
                      "bbc.com", "cnn.com", "reuters.com", "bloomberg.com", "forbes.com",
                      "wired.com", "theverge.com", "techcrunch.com", "arstechnica.com",
                      "zdnet.com", "mashable.com", "venturebeat.com", "engadget.com",
                      "economist.com", "techradar.com", "36kr.com"}
_REFERENCE_TOKENS = ("wiki", "dictionar", "encyclop")
_UGC_TOKENS = ("forum", "community", "bbs")
_EDITORIAL_TOKENS = ("news", "times", "daily", "weekly", "magazine", "herald",
                     "press", "journal", "gazette", "tribune", "chronicle")


def classify_domain(domain, brand_domains, overrides=None):
    """被引域名 → (五分类, 判定依据 basis)。判定顺序:人工覆盖 > 自有域 > 启发式[推断]。

    basis 形如 "override" / "own-domain" / "known:wikipedia.org" / "token:wiki" /
    "default:corporate[推断]",供报告与 JSON 暴露判定路径,不黑箱。
    """
    d = (domain or "").strip().lower()
    overrides = overrides or {}
    if d in overrides:
        return overrides[d], "override"
    if d in {b.lower() for b in brand_domains}:
        return "Own", "own-domain"
    if d in _REFERENCE_DOMAINS:
        return "Reference", "known:" + d
    if d in _UGC_DOMAINS:
        return "UGC", "known:" + d
    if d in _EDITORIAL_DOMAINS:
        return "Editorial", "known:" + d
    for tok in _REFERENCE_TOKENS:
        if tok in d:
            return "Reference", "token:" + tok
    for tok in _UGC_TOKENS:
        if tok in d:
            return "UGC", "token:" + tok
    for tok in _EDITORIAL_TOKENS:
        if tok in d:
            return "Editorial", "token:" + tok
    return "Corporate", "default:corporate[推断]"


def load_domain_overrides(path):
    """--domain-class overrides.json → {域名小写: 五分类};非法值抛 ValueError。"""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("应为 {\"域名\": \"分类\"} 对象,得到 %s" % type(raw).__name__)
    out = {}
    for dom, cls in raw.items():
        key = str(cls).strip().lower()
        if key not in _CLASS_ALIASES:
            raise ValueError("域名 %s 的分类 %r 无效(可用: %s)"
                             % (dom, cls, "/".join(SOURCE_CLASSES)))
        out[str(dom).strip().lower()] = _CLASS_ALIASES[key]
    return out


def ensure_classes(groups, brand_domains, overrides=None):
    """幂等:给域名分组补 source_class/class_action/class_basis 三键。"""
    for g in groups:
        if "source_class" not in g:
            cls, basis = classify_domain(g["domain"], brand_domains, overrides)
            g["source_class"], g["class_basis"] = cls, basis
            g["class_action"] = SOURCE_CLASS_ACTIONS[cls]
    return groups


# ---------- gapLabel 七叉决策树(niubigeo keyword-metrics-engine 直译,deep-read N4) ----------
GAP_LABELS = [
    ("no_valid", "No completed AI answers",
     "数据不足:0 条有效回答——先修采集(重跑/换引擎),再谈缺口"),
    ("competitor_owned", "Competitors own this AI answer space",
     "最高优先:对标竞品产出内容/对比页,争取进入该词的答案"),
    ("absent", "Target absent from AI answers",
     "品类词缺席:补该主题的 grounding 页面与可引用事实"),
    ("owned_not_reflected", "Owned content is not reflected",
     "自有内容没进答案:检查页面可引用性(结构化事实/数据密度)"),
    ("mention_no_citation", "Mentioned without official citation",
     "仅提及无引用:强化可引用资产(数据页/研究/文档)"),
    ("competitor_sporadic", "Competitors still appear without target",
     "偶发竞品独现:巩固既有覆盖,补竞品占位的子话题"),
    ("covered", "Covered in this audit", "已覆盖:保持监测,暂不动"),
]


def load_owned_relevance(path):
    """--owned-relevance owned.json → {prompt: 0-1};非法值抛 ValueError。"""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("应为 {\"prompt\": 0-1} 对象,得到 %s" % type(raw).__name__)
    out = {}
    for p, v in raw.items():
        try:
            x = float(v)
        except (TypeError, ValueError):
            raise ValueError("prompt %r 的 ownedRelevance %r 不是数字" % (p, v))
        if not 0.0 <= x <= 1.0:
            raise ValueError("prompt %r 的 ownedRelevance %s 超出 0-1" % (p, v))
        out[str(p)] = x
    return out


def _agg_gap_cells(panel, brand_domains):
    """逐 prompt 聚合:valid(有效回答)/mentioned(提及)/cited(自有域被引)/
    competitor_only(目标未提及且任一非自有域被引的 cell 数,竞品口径[推断])。"""
    per = {}
    for run in panel.get("runs", []):
        for prompt, res in (run.get("results") or {}).items():
            res = res or {}
            state = (res.get("state") or "").strip().lower()
            if state in ("failed", "no_answer"):
                continue                       # 无效回答不入分母
            a = per.setdefault(prompt, {"valid": 0, "mentioned": 0, "cited": 0,
                                        "competitor_only": 0})
            a["valid"] += 1
            mentioned = res.get("mentioned") in (1, True) or state == "cited_brand"
            if mentioned:
                a["mentioned"] += 1
            if res.get("cited") in (1, True) or state == "cited_brand":
                a["cited"] += 1
            doms = {registrable_domain(u) for u in (res.get("cited_urls") or [])}
            doms.discard("")
            if not mentioned and (doms - {b.lower() for b in brand_domains}):
                a["competitor_only"] += 1
    return per


def gap_label_of(agg, owned_rel):
    """七叉判定(顺序固定,自上而下首个命中):返回 GAP_LABELS 下标。"""
    if agg["valid"] == 0:
        return 0
    if agg["mentioned"] == 0:
        return 1 if agg["competitor_only"] > 0 else 2
    if owned_rel is not None and owned_rel >= 0.6 and agg["mentioned"] / agg["valid"] < 0.5:
        return 3
    if agg["cited"] == 0:
        return 4
    if agg["competitor_only"] > 0:
        return 5
    return 6


def compute_gap_labels(panel, brand_domains, owned_relevance=None):
    """逐 prompt 七叉标签;owned_relevance={prompt: 0-1} 或 None(分支 3 不可判,降级注明)。
    返回按标签严重度(下标)升序的行列表,同标签按 prompt 名排序。"""
    owned_relevance = owned_relevance or {}
    per = _agg_gap_cells(panel, brand_domains)
    prompts = list(panel.get("prompts") or [])
    prompts += sorted(p for p in per if p not in prompts)
    rows = []
    for p in prompts:
        a = per.get(p, {"valid": 0, "mentioned": 0, "cited": 0, "competitor_only": 0})
        idx = gap_label_of(a, owned_relevance.get(p))
        code, label, action = GAP_LABELS[idx]
        rows.append((idx, {"prompt": p, "code": code, "label": label, "action": action,
                           "valid_answers": a["valid"], "mentioned": a["mentioned"],
                           "own_cited": a["cited"],
                           "competitor_only_runs": a["competitor_only"],
                           "mention_rate": (a["mentioned"] / a["valid"]) if a["valid"] else None,
                           "owned_relevance": owned_relevance.get(p)}))
    rows.sort(key=lambda t: (t[0], t[1]["prompt"]))
    return [r for _, r in rows]


def registrable_domain(url):
    """URL → 可注册域(近似:取最后两段;co.uk/com.cn 等常见双段后缀取三段)。"""
    host = (url or "").strip().lower()
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    if "@" in host:
        host = host.split("@")[-1]
    if ":" in host:
        host = host.split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]
    parts = [p for p in host.split(".") if p]
    if not parts:
        return ""
    if len(parts) >= 3 and ".".join(parts[-2:]) in SL_TLD:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return parts[0]


def parse_brand_domains(arg, panel):
    """--brand-domains 逗号串 + 面板 domain → 小写自有域集合。"""
    doms = {d.strip().lower() for d in (arg or "").split(",") if d.strip()}
    pd = (panel.get("domain") or "").strip().lower()
    if pd:
        doms.add(pd)
    return doms


def compute_opps(panel, brand_domains):
    """返回 (urls_sorted, doms_sorted, stats);URL 全局排序 = 竞品同场降序 → count 降序 → url。"""
    opps = {}
    stats = {"runs": len(panel.get("runs", [])), "cells": 0, "qualifying": 0,
             "urls": 0, "domains": 0, "high_priority": 0, "own_cited": 0}
    for run in panel.get("runs", []):
        engine = run.get("engine") or "unknown"
        for prompt, res in (run.get("results") or {}).items():
            stats["cells"] += 1
            urls = list(dict.fromkeys(u.strip() for u in (res.get("cited_urls") or [])
                                      if u and u.strip()))
            if not urls:
                continue
            state = (res.get("state") or "").strip().lower()
            if state == "cited_brand" or res.get("cited") in (1, True):
                continue                     # 品牌已被引 → 不是缺口
            if state in ("failed", "no_answer"):
                continue                     # 采集失败≠内容缺口;无答案无引用
            stats["qualifying"] += 1
            doms = {registrable_domain(u) for u in urls}
            doms.discard("")
            foreign = doms - brand_domains
            for u in urls:
                d = registrable_domain(u)
                if not d or d in brand_domains:
                    stats["own_cited"] += 1 if d else 0
                    continue                 # 排除自有域
                o = opps.get(u)
                if o is None:
                    o = opps[u] = {"url": u, "domain": d, "count": 0,
                                   "prompts": set(), "providers": set(),
                                   "has_competitor_run": False, "competitors": set()}
                o["count"] += 1
                o["prompts"].add(prompt)
                o["providers"].add(engine)
                others = foreign - {d}
                if others:
                    o["has_competitor_run"] = True
                    o["competitors"] |= others
    groups = {}
    for o in opps.values():
        g = groups.setdefault(o["domain"], {
            "domain": o["domain"], "count": 0, "pages": set(), "prompts": set(),
            "providers": set(), "has_competitor_run": False, "competitors": set()})
        g["count"] += o["count"]
        g["pages"].add(o["url"])
        g["prompts"] |= o["prompts"]
        g["providers"] |= o["providers"]
        g["competitors"] |= o["competitors"]
        g["has_competitor_run"] |= o["has_competitor_run"]
    stats["urls"] = len(opps)
    stats["domains"] = len(groups)
    stats["high_priority"] = sum(1 for o in opps.values() if o["has_competitor_run"])
    urls_sorted = sorted(opps.values(),
                         key=lambda o: (not o["has_competitor_run"], -o["count"], o["url"]))
    doms_sorted = sorted(groups.values(),
                         key=lambda g: (not g["has_competitor_run"], -g["count"], g["domain"]))
    return urls_sorted, doms_sorted, stats


def priority_of(has_competitor_run):
    return "High" if has_competitor_run else "Standard"


def outreach_tip(g):
    """外联提示,口径照抄 borrow-specs B2;g 为域名分组。"""
    if g["has_competitor_run"]:
        return "竞品 %s 在 %s 被引用——考虑贡献内容或争取列表位直接竞争" % (
            ",".join(sorted(g["competitors"])), g["domain"])
    return "AI 模型在 %d 个追踪 prompt 引用 %s,获得收录可提升 AI 可见性" % (
        len(g["prompts"]), g["domain"])


def render_report(panel, urls_sorted, doms_sorted, stats, brand_domains,
                  owned_relevance=None, overrides=None):
    ensure_classes(doms_sorted, brand_domains, overrides)   # 幂等;直接调用亦安全
    L = []
    L.append("== 引用缺口报告(citation gaps): %s ==" % panel.get("brand", "?"))
    L.append("runs=%d cells=%d qualifying=%d(有 cited_urls 且品牌未被引;cited_brand/failed/no_answer 不入)"
             % (stats["runs"], stats["cells"], stats["qualifying"]))
    L.append("自有域排除: %s(qualifying cell 内自有域被引 %d 次不计)"
             % (",".join(sorted(brand_domains)) or "(无)", stats["own_cited"]))
    if not urls_sorted:
        L.append("无引用缺口:qualifying cell 中没有任何非自有域被引。")
        L.append("[i] qualifying=0 时先用 citation_panel.py report 检查采样覆盖,再回来跑本工具。")
        return "\n".join(L)
    L.append("候选 URL=%d 覆盖域名=%d 高优先(竞品同场)=%d"
             % (stats["urls"], stats["domains"], stats["high_priority"]))
    L.append("")
    L.append("-- 域名分组(排序:竞品同场降序 → 总引用降序) --")
    L.append("| 域名 | 总引用 | 页面数 | 同场竞品 | 追踪 prompts | 引擎 | 优先级 |")
    L.append("|---|---|---|---|---|---|---|")
    for g in doms_sorted:
        L.append("| %s | %d | %d | %s | %d | %s | %s |" % (
            g["domain"], g["count"], len(g["pages"]),
            ",".join(sorted(g["competitors"])) or "-", len(g["prompts"]),
            ",".join(sorted(g["providers"])), priority_of(g["has_competitor_run"])))
    L.append("")
    L.append("-- Top 页面(前 %d,共 %d;排序:竞品同场降序 → 引用次数降序) --"
             % (min(TOP_PAGES, len(urls_sorted)), len(urls_sorted)))
    L.append("| URL | 引用 | prompts | 引擎 | 同场竞品 | 优先级 |")
    L.append("|---|---|---|---|---|---|")
    for o in urls_sorted[:TOP_PAGES]:
        L.append("| %s | %d | %d | %s | %s | %s |" % (
            o["url"], o["count"], len(o["prompts"]),
            ",".join(sorted(o["providers"])),
            ",".join(sorted(o["competitors"])) or "-",
            priority_of(o["has_competitor_run"])))
    L.append("")
    L.append("-- 外联提示(逐域名;口径照抄 borrow-specs B2) --")
    for g in doms_sorted:
        L.append("[%s] %s:%s" % (priority_of(g["has_competitor_run"]),
                                 g["domain"], outreach_tip(g)))
    L.append("")
    L.append("-- 来源五分类(逐域名;Peec Source 五分类,启发式与默认均 [推断];"
             "--domain-class overrides.json 人工覆盖) --")
    L.append("| 域名 | 分类 | 判定依据 | 行动提示 |")
    L.append("|---|---|---|---|")
    for g in doms_sorted:
        L.append("| %s | %s | %s | %s |" % (
            g["domain"], g["source_class"], g["class_basis"], g["class_action"]))
    L.append("")
    gap_rows = compute_gap_labels(panel, brand_domains, owned_relevance)
    L.append("-- gapLabel 七叉(逐 prompt;niubigeo 口径;"
             "竞品代理=同 cell 非自有被引域[推断]) --")
    L.append("| Prompt | 标签 | 有效/提及/被引/竞品独现 | 动作 |")
    L.append("|---|---|---|---|")
    for r in gap_rows:
        L.append("| %s | %s | %d/%d/%d/%d | %s |" % (
            r["prompt"], r["label"], r["valid_answers"], r["mentioned"],
            r["own_cited"], r["competitor_only_runs"], r["action"]))
    if owned_relevance:
        L.append("[i] ownedRelevance 由 --owned-relevance 提供;分支 4 按输入判定。")
    else:
        L.append("[i] ownedRelevance 未提供(--owned-relevance owned.json):分支 "
                 "\"Owned content is not reflected\" 不可判[降级:该值为 niubigeo N7 词筛"
                 "产出,panel.json 无此字段],落入后续分支。")
    L.append("")
    L.append("-- 串联(先 gaps 找目标域 → 再 cite_domain.py 评级) --")
    L.append("  高优先域先评级再投入外联:python3 cite_domain.py --input answers.json(数据项人工采集);")
    L.append("  评级进入简报:templates/monitor/citation-outreach-brief.md。")
    if stats["qualifying"] < 10:
        L.append("[!] qualifying cells=%d <10:样本太小,结论只能当方向" % stats["qualifying"])
    return "\n".join(L)


def _url_row(o):
    return {"url": o["url"], "domain": o["domain"], "count": o["count"],
            "prompts": sorted(o["prompts"]), "providers": sorted(o["providers"]),
            "has_competitor_run": o["has_competitor_run"],
            "competitors": sorted(o["competitors"]),
            "priority": priority_of(o["has_competitor_run"])}


def _dom_row(g):
    return {"domain": g["domain"], "count": g["count"], "pages": sorted(g["pages"]),
            "prompts": sorted(g["prompts"]), "providers": sorted(g["providers"]),
            "has_competitor_run": g["has_competitor_run"],
            "competitors": sorted(g["competitors"]),
            "priority": priority_of(g["has_competitor_run"]),
            "source_class": g.get("source_class"),
            "class_basis": g.get("class_basis"),
            "class_action": g.get("class_action")}


def write_csv(path, urls_sorted):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)
        for o in urls_sorted:
            w.writerow([o["domain"], o["url"], o["count"],
                        "|".join(sorted(o["prompts"])),
                        ",".join(sorted(o["providers"])),
                        ",".join(sorted(o["competitors"])),
                        priority_of(o["has_competitor_run"])])


def write_json(path, panel_path, panel, urls_sorted, doms_sorted, stats, brand_domains,
               owned_relevance=None, overrides=None):
    ensure_classes(doms_sorted, brand_domains, overrides)
    counts = {}
    for g in doms_sorted:                       # 五分类域名计数(只增键,向后兼容)
        counts[g["source_class"]] = counts.get(g["source_class"], 0) + 1
    payload = {"tool": "citation_gaps.py", "panel": os.path.abspath(panel_path),
               "brand": panel.get("brand"), "brand_domains": sorted(brand_domains),
               "stats": stats,
               "domains": [_dom_row(g) for g in doms_sorted],
               "urls": [_url_row(o) for o in urls_sorted],
               "outreach_tips": {g["domain"]: outreach_tip(g) for g in doms_sorted},
               "source_class_counts": counts,
               "source_class_overrides": sorted((overrides or {}).keys()),
               "gap_labels": compute_gap_labels(panel, brand_domains, owned_relevance),
               "owned_relevance_available": bool(owned_relevance)}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# ---------- 自测(不联网) ----------

def _self_test():
    P = ["best crm", "crm pricing", "helpdesk tools"]
    panel = {"brand": "Acme", "domain": "acme.ai", "prompts": P,
             "engines": ["chatgpt", "perplexity"], "runs": [
        {"run_id": "r1", "engine": "chatgpt", "date": "2026-10-01", "brand": "Acme",
         "results": {
             P[0]: {"state": "brand_absent", "mentioned": 0, "cited": 0,
                    "cited_urls": ["https://www.g2.com/crm/best", "https://hubspot.com/crm"]},
             P[1]: {"state": "name_only_mention", "mentioned": 1, "cited": 0,
                    "cited_urls": ["https://www.g2.com/crm/best"]},
             P[2]: {"state": "cited_brand", "mentioned": 1, "cited": 1,
                    "cited_urls": ["https://acme.ai/x", "https://g2.com/helpdesk"]}}},
        {"run_id": "r2", "engine": "perplexity", "date": "2026-10-02", "brand": "Acme",
         "results": {
             P[0]: {"state": "brand_absent", "mentioned": 0, "cited": 0,
                    "cited_urls": ["https://blog.hubspot.co.uk/pricing"]}}}]
    }
    urls, doms, stats = compute_opps(panel, parse_brand_domains("acme-cdn.com", panel))
    assert stats["cells"] == 4 and stats["qualifying"] == 3
    by_url = {o["url"]: o for o in urls}
    g2 = by_url["https://www.g2.com/crm/best"]
    assert g2["count"] == 2 and g2["has_competitor_run"]
    assert g2["competitors"] == {"hubspot.com"}
    assert set(by_url) == {"https://www.g2.com/crm/best", "https://hubspot.com/crm",
                           "https://blog.hubspot.co.uk/pricing"}   # cited_brand cell 与自有域不入
    assert by_url["https://blog.hubspot.co.uk/pricing"]["domain"] == "hubspot.co.uk"
    assert not by_url["https://blog.hubspot.co.uk/pricing"]["has_competitor_run"]
    assert urls[0]["url"] == "https://www.g2.com/crm/best" and doms[0]["domain"] == "g2.com"
    rep = render_report(panel, urls, doms, stats, {"acme.ai", "acme-cdn.com"})
    assert "竞品 hubspot.com 在 g2.com 被引用——考虑贡献内容或争取列表位直接竞争" in rep
    assert "AI 模型在 1 个追踪 prompt 引用 hubspot.co.uk,获得收录可提升 AI 可见性" in rep
    # registrable_domain 双段后缀与清洗
    assert registrable_domain("https://www.acme.co.uk/a?b=1") == "acme.co.uk"
    assert registrable_domain("https://shop.example.com.cn/x#f") == "example.com.cn"
    assert registrable_domain("http://u:p@www.site.co.jp:8080/x") == "site.co.jp"
    assert registrable_domain("https://docs.other.org/x") == "other.org"
    # 来源五分类:覆盖优先 > 自有域 > 启发式[推断]
    assert classify_domain("g2.com", set(), {"g2.com": "UGC"}) == ("UGC", "override")
    assert classify_domain("acme.ai", {"acme.ai"}) == ("Own", "own-domain")
    assert classify_domain("en.wikipedia.org", set())[0] == "Reference"
    assert classify_domain("reddit.com", set())[0] == "UGC"
    assert classify_domain("techcrunch.com", set())[0] == "Editorial"
    assert classify_domain("hubspot.com", set()) == ("Corporate", "default:corporate[推断]")
    assert "合作目录" in SOURCE_CLASS_ACTIONS["Corporate"]
    # gapLabel 七叉:各分支单点触发
    G = {"valid": 2, "mentioned": 2, "cited": 2, "competitor_only": 0}
    assert gap_label_of({"valid": 0, "mentioned": 0, "cited": 0, "competitor_only": 0}, None) == 0
    assert gap_label_of({"valid": 2, "mentioned": 0, "cited": 0, "competitor_only": 1}, None) == 1
    assert gap_label_of({"valid": 2, "mentioned": 0, "cited": 0, "competitor_only": 0}, None) == 2
    assert gap_label_of(dict(G, cited=0), None) == 4
    assert gap_label_of(dict(G, competitor_only=1), None) == 5
    assert gap_label_of(G, None) == 6
    assert gap_label_of({"valid": 2, "mentioned": 0, "cited": 2, "competitor_only": 0},
                        0.8) == 2                    # 分支 2 先于分支 3(顺序固定)
    assert gap_label_of({"valid": 4, "mentioned": 1, "cited": 1, "competitor_only": 0},
                        0.7) == 3                    # 提及率 0.25<0.5 且 owned≥0.6
    assert gap_label_of({"valid": 4, "mentioned": 1, "cited": 1, "competitor_only": 0},
                        None) == 6                   # 无 owned 输入 → 分支 3 降级,已引=Covered
    rep2 = render_report(panel, urls, doms, stats, {"acme.ai", "acme-cdn.com"},
                         owned_relevance={"best crm": 0.9})
    assert "来源五分类" in rep2 and "gapLabel 七叉" in rep2
    assert "Competitors own this AI answer space" in rep2     # best crm:未提及+竞品独现
    assert "[i] ownedRelevance 由 --owned-relevance 提供" in rep2
    print("[self-test] PASS citation_gaps(qualifying 过滤/自有域排除/竞品同场高优先排序/双段后缀"
          "/来源五分类/gapLabel 七叉)")


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--panel", default="panel.json", help="citation_panel.py 的面板数据文件")
    ap.add_argument("--brand-domains", default="",
                    help="自有域,逗号分隔(排除;自动并入面板 --domain)")
    ap.add_argument("--csv", default="", help="输出 CSV 路径(列 %s)" % ",".join(CSV_HEADER))
    ap.add_argument("--json", default="", help="输出结构化 JSON 路径")
    ap.add_argument("--domain-class", default="",
                    help="来源五分类人工覆盖 JSON:{\"域名\": \"Editorial|Corporate|UGC"
                         "|Reference|Own\"}(优先于一切启发式)")
    ap.add_argument("--owned-relevance", default="",
                    help="gapLabel 分支 4 输入:{\"prompt\": 0-1} 站点证据对词相关度"
                         "(niubigeo N7 口径;缺省时该分支不可判,降级注明)")
    ap.add_argument("--self-test", action="store_true", help="冒烟自测(不联网)")
    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.self_test:
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL citation_gaps")
            return 1
    try:
        with open(args.panel, encoding="utf-8") as f:
            panel = json.load(f)
    except (OSError, ValueError) as e:
        print("错误: 无法读取面板 %s: %s" % (args.panel, e), file=sys.stderr)
        return 1
    panel.setdefault("runs", [])
    try:
        overrides = load_domain_overrides(args.domain_class) if args.domain_class else {}
    except (OSError, ValueError) as e:
        print("错误: --domain-class %s: %s" % (args.domain_class, e), file=sys.stderr)
        return 1
    owned = None
    if args.owned_relevance:
        try:
            owned = load_owned_relevance(args.owned_relevance)
        except (OSError, ValueError) as e:
            print("错误: --owned-relevance %s: %s" % (args.owned_relevance, e), file=sys.stderr)
            return 1
    if owned is None and isinstance(panel.get("owned_relevance"), dict):
        owned = {str(k): float(v) for k, v in panel["owned_relevance"].items()}
    brand_domains = parse_brand_domains(args.brand_domains, panel)
    urls_sorted, doms_sorted, stats = compute_opps(panel, brand_domains)
    ensure_classes(doms_sorted, brand_domains, overrides)
    print(render_report(panel, urls_sorted, doms_sorted, stats, brand_domains,
                        owned_relevance=owned, overrides=overrides))
    if args.csv:
        write_csv(args.csv, urls_sorted)
        print("[i] CSV → %s(%d 行)" % (args.csv, len(urls_sorted)), file=sys.stderr)
    if args.json:
        write_json(args.json, args.panel, panel, urls_sorted, doms_sorted, stats,
                   brand_domains, owned_relevance=owned, overrides=overrides)
        print("[i] JSON → %s" % args.json, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
