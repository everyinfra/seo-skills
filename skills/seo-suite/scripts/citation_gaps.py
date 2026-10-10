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

与 cite_domain.py 串联:先用本脚本找目标域,再用 cite_domain.py 评级(先 gaps 后评级,
顺序不可倒——先评级后找域是浪费)。

用法:
  python3 citation_gaps.py --panel panel.json --brand-domains acme.ai,acme.com
  python3 citation_gaps.py --panel panel.json --csv gaps.csv --json gaps.json
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


def render_report(panel, urls_sorted, doms_sorted, stats, brand_domains):
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
            "priority": priority_of(g["has_competitor_run"])}


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


def write_json(path, panel_path, panel, urls_sorted, doms_sorted, stats, brand_domains):
    payload = {"tool": "citation_gaps.py", "panel": os.path.abspath(panel_path),
               "brand": panel.get("brand"), "brand_domains": sorted(brand_domains),
               "stats": stats,
               "domains": [_dom_row(g) for g in doms_sorted],
               "urls": [_url_row(o) for o in urls_sorted],
               "outreach_tips": {g["domain"]: outreach_tip(g) for g in doms_sorted}}
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
    print("[self-test] PASS citation_gaps(qualifying 过滤/自有域排除/竞品同场高优先排序/双段后缀)")


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--panel", default="panel.json", help="citation_panel.py 的面板数据文件")
    ap.add_argument("--brand-domains", default="",
                    help="自有域,逗号分隔(排除;自动并入面板 --domain)")
    ap.add_argument("--csv", default="", help="输出 CSV 路径(列 %s)" % ",".join(CSV_HEADER))
    ap.add_argument("--json", default="", help="输出结构化 JSON 路径")
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
    brand_domains = parse_brand_domains(args.brand_domains, panel)
    urls_sorted, doms_sorted, stats = compute_opps(panel, brand_domains)
    print(render_report(panel, urls_sorted, doms_sorted, stats, brand_domains))
    if args.csv:
        write_csv(args.csv, urls_sorted)
        print("[i] CSV → %s(%d 行)" % (args.csv, len(urls_sorted)), file=sys.stderr)
    if args.json:
        write_json(args.json, args.panel, panel, urls_sorted, doms_sorted, stats, brand_domains)
        print("[i] JSON → %s" % args.json, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
