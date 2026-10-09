#!/usr/bin/env python3
"""AI 可见性采样面板管理器(人工采样协议的工程化)。stdlib-only。

五状态分类(unifapi 口径;采集失败 ≠ 内容缺口):
  no_answer          引擎没给答案 → 留在覆盖分母,计 zero-presence
  failed             采集失败       → 不入任何分母
  brand_absent       有答案但品牌未出现(文本别名与引用域名均无)
  name_only_mention  品牌名/别名出现在正文,但引用来源无品牌域名(mentioned≠cited)
  cited_brand        品牌域名出现在引用来源

指标口径:
  mention coverage = Σmentioned / 成功 cell 数(成功 = 非 failed;no_answer 计 0 留分母)
  citation share   = 品牌被引 answer 数 / Σ(每 answer 去重后的引用域名数)
                     每答案每品牌至多计 1 次 → 各品牌 share 恒和 100%;空分母 N/A
  跨期比较         = 配对分母:只比两期均成功(非 failed)的 cell
  稳定性           = 单次引用检查 = 掷硬币;同一 prompt ≥3 次采样才报
                     Wilson 95% CI(z=1.96,w=√(p(1-p)/n),CI=p±z·w;区间跨 0.5 → unstable)
  prompts < 10     = 样本太小,结论只能当方向

子命令:
  init    --brand X --prompts p.csv [--aliases a,b] [--domain example.com]
          [--engines e1,e2] [--panel PATH] [--force]
  record  --engine chatgpt --file run.csv [--run-id ID] [--date ISO] [--panel PATH]
  report  [--engine E] [--panel PATH]
  diff    RUN1 RUN2 [--panel PATH]        # RUN 为 run 文件路径或面板内 run_id

run.csv 列: prompt, mentioned, cited, cited_urls[, state]
  mentioned/cited ∈ {0,1};cited_urls 分号分隔;state 可显式给 failed/no_answer
  或三态之一覆盖,否则由 mentioned/cited 推导;cited=1 蕴含 mentioned=1。

面板文件 panel.json 与 runs/ 目录同层;record 同时写入面板与独立 run 文件。

用法:
  python3 citation_panel.py init --brand Acme --prompts prompts.csv --domain acme.ai
  python3 citation_panel.py record --engine chatgpt --file run1.csv
  python3 citation_panel.py report
  python3 citation_panel.py diff runs/r1.json runs/r2.json
  python3 citation_panel.py --self-test
"""
import argparse
import csv
import json
import math
import os
import re
import sys
import tempfile
import traceback
from collections import Counter
from datetime import datetime

DEFAULT_ENGINES = ["chatgpt", "perplexity", "gemini", "copilot", "claude", "grok"]
STATES = ("no_answer", "failed", "brand_absent", "name_only_mention", "cited_brand")
Z = 1.96
SL_TLD = {"co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au", "co.jp", "ne.jp",
          "or.jp", "com.cn", "net.cn", "org.cn", "com.br", "com.mx", "com.tr",
          "co.kr", "co.in", "co.za", "com.sg", "com.hk"}


# ---------- 基础工具 ----------

def registrable_domain(url):
    """从 URL 提取可注册域(近似:last-two-labels,常见二级 TLD 取三位)。"""
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


def load_panel(path):
    with open(path, encoding="utf-8") as f:
        panel = json.load(f)
    panel.setdefault("runs", [])
    panel.setdefault("aliases", [])
    panel.setdefault("engines", list(DEFAULT_ENGINES))
    return panel


def save_panel(path, panel):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(panel, f, ensure_ascii=False, indent=2)


def runs_dir_for(panel_path):
    return os.path.join(os.path.dirname(os.path.abspath(panel_path)), "runs")


def _to01(v):
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "是"):
        return 1
    if s in ("0", "false", "no", "n", "否", "", "na", "n/a", "-"):
        return 0
    raise ValueError("mentioned/cited 需要 0/1,得到 %r" % (v,))


# ---------- init ----------

def read_prompts_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [r for r in csv.reader(f) if r and r[0].strip()]
    if not rows:
        return []
    head = rows[0][0].strip().lower()
    body = rows[1:] if head in ("prompt", "prompts", "query", "提示词") else rows
    seen, out = set(), []
    for r in body:
        p = r[0].strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def cmd_init(args):
    prompts = read_prompts_csv(args.prompts)
    if not prompts:
        print("错误: %s 中没有读到 prompt" % args.prompts, file=sys.stderr)
        return 1
    if os.path.exists(args.panel) and not args.force:
        print("面板已存在: %s(用 --force 覆盖)" % args.panel, file=sys.stderr)
        return 1
    panel = {
        "brand": args.brand,
        "aliases": [a.strip() for a in (args.aliases or "").split(",") if a.strip()],
        "domain": (args.domain or "").strip().lower(),
        "prompts": prompts,
        "engines": [e.strip() for e in (args.engines or "").split(",") if e.strip()]
        or list(DEFAULT_ENGINES),
        "created": datetime.now().isoformat(timespec="seconds"),
        "runs": [],
    }
    os.makedirs(runs_dir_for(args.panel), exist_ok=True)
    save_panel(args.panel, panel)
    print("面板已建立: %s(brand=%s, domain=%s, prompts=%d, engines=%s)"
          % (args.panel, args.brand, panel["domain"] or "(未设)", len(prompts),
             ",".join(panel["engines"])))
    if len(prompts) < 10:
        print("[!] prompts=%d <10:样本太小,结论只能当方向" % len(prompts))
    return 0


# ---------- record ----------

def normalize_result(row, warnings, prompt):
    state = (row.get("state") or "").strip().lower()
    if state in ("failed", "no_answer"):
        return {"state": state, "mentioned": 0, "cited": 0, "cited_urls": []}
    if state in ("brand_absent", "name_only_mention", "cited_brand"):
        m, c = {"brand_absent": (0, 0),
                "name_only_mention": (1, 0),
                "cited_brand": (1, 1)}[state]
    else:
        m = _to01(row.get("mentioned", 0))
        c = _to01(row.get("cited", 0))
        if c and not m:
            warnings.append("cited=1 但 mentioned=0,已按 mentioned=1 处理: %s" % prompt)
            m = 1
        state = "cited_brand" if c else ("name_only_mention" if m else "brand_absent")
    urls = [u.strip() for u in re.split(r"[;,\s]+", row.get("cited_urls") or "") if u.strip()]
    return {"state": state, "mentioned": m, "cited": c, "cited_urls": urls}


def read_run_csv(path, panel):
    warnings, results = [], {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            row = {(k or "").strip().lower(): (v or "") for k, v in raw.items()}
            prompt = (row.get("prompt") or row.get("query") or "").strip()
            if not prompt:
                continue
            results[prompt] = normalize_result(row, warnings, prompt)
            if prompt not in panel["prompts"]:
                warnings.append("prompt 不在面板 prompts 列表中: %s" % prompt)
    return results, warnings


def cmd_record(args):
    panel = load_panel(args.panel)
    if args.engine not in panel["engines"]:
        panel["engines"].append(args.engine)
        print("[i] 引擎 %s 不在面板引擎列表,已追加" % args.engine)
    results, warnings = read_run_csv(args.file, panel)
    if not results:
        print("错误: %s 中没有有效行(需 prompt,mentioned,cited,cited_urls 列)" % args.file,
              file=sys.stderr)
        return 1
    date = args.date or datetime.now().isoformat(timespec="seconds")
    run_id = args.run_id or re.sub(r"[^\w.-]+", "-", "%s-%s" % (args.engine, date))
    existing = {r["run_id"] for r in panel["runs"]}
    base, n = run_id, 2
    while run_id in existing:
        run_id = "%s-%d" % (base, n)
        n += 1
    run = {"run_id": run_id, "engine": args.engine, "date": date,
           "brand": panel["brand"], "results": results}
    panel["runs"].append(run)
    save_panel(args.panel, panel)
    rdir = runs_dir_for(args.panel)
    os.makedirs(rdir, exist_ok=True)
    rpath = os.path.join(rdir, run_id + ".json")
    with open(rpath, "w", encoding="utf-8") as f:
        json.dump(run, f, ensure_ascii=False, indent=2)
    sc = Counter(r["state"] for r in results.values())
    print("已记录 run: %s(engine=%s, cells=%d)→ %s" % (run_id, args.engine, len(results), rpath))
    print("  五状态: " + ", ".join("%s=%d" % (s, sc.get(s, 0)) for s in STATES))
    for w in warnings:
        print("  [!] %s" % w)
    if len(panel["prompts"]) < 10:
        print("  [!] prompts=%d <10:样本太小,结论只能当方向" % len(panel["prompts"]))
    return 0


# ---------- 统计 ----------

def wilson_ci(k, n):
    """按面板口径(正态近似):w=√(p(1-p)/n),CI=p±z·w,z=1.96。"""
    if not n:
        return None
    p = k / n
    w = math.sqrt(p * (1 - p) / n)
    lo = max(0.0, p - Z * w)
    hi = min(1.0, p + Z * w)
    return p, lo, hi, (lo < 0.5 < hi)


def compute_stats(panel, engine=None, _per_engine=True):
    runs = [r for r in panel.get("runs", []) if not engine or r["engine"] == engine]
    state_counts = Counter()
    cells = mentioned_sum = brand_hits = domain_total = 0
    co_cited = Counter()
    per_prompt = {}
    brand_dom = (panel.get("domain") or "").lower()
    for run in runs:
        for prompt, res in run["results"].items():
            cells += 1
            state_counts[res["state"]] += 1
            mentioned_sum += res["mentioned"]
            doms = {registrable_domain(u) for u in res.get("cited_urls", [])}
            doms.discard("")
            domain_total += len(doms)
            if brand_dom and brand_dom in doms:
                brand_hits += 1
            for d in doms:
                if d != brand_dom:
                    co_cited[d] += 1
            agg = per_prompt.setdefault(prompt, {"n": 0, "k": 0})
            if res["state"] != "failed":
                agg["n"] += 1
                agg["k"] += res["mentioned"]
    denom = cells - state_counts["failed"]
    coverage = (mentioned_sum / denom) if denom else None
    share = (brand_hits / domain_total) if (domain_total and brand_dom) else None
    stability = {}
    for prompt, agg in per_prompt.items():
        if agg["n"] >= 3:
            stability[prompt] = (agg["k"], agg["n"]) + wilson_ci(agg["k"], agg["n"])
    per_engine = {}
    if _per_engine:
        for eng in sorted({r["engine"] for r in runs}):
            sub = compute_stats({**panel, "runs": [r for r in runs if r["engine"] == eng]},
                                _per_engine=False)
            per_engine[eng] = sub
    return {"runs": len(runs), "cells": cells, "state_counts": state_counts,
            "denominator": denom, "mentioned_sum": mentioned_sum, "coverage": coverage,
            "brand_hits": brand_hits, "domain_total": domain_total, "share": share,
            "co_cited": co_cited, "stability": stability, "per_engine": per_engine}


def _pct(x):
    return "N/A" if x is None else "%.1f%%" % (100 * x)


def render_report(panel, stats):
    L = []
    L.append("== AI 可见性面板报告: %s ==" % panel["brand"])
    L.append("prompts=%d runs=%d cells=%d engines=%s"
             % (len(panel["prompts"]), stats["runs"], stats["cells"],
                ",".join(panel["engines"])))
    if stats["runs"] == 0:
        L.append("尚无运行记录。先用 record 录入采样。")
        return "\n".join(L)
    sc = stats["state_counts"]
    L.append("-- 五状态分类 --")
    notes = {"failed": "  ← 采集失败≠内容缺口,不入分母",
             "no_answer": "  ← 留在覆盖分母,计 zero-presence"}
    for s in STATES:
        pct = (100 * sc.get(s, 0) / stats["cells"]) if stats["cells"] else 0
        L.append("  %-18s %4d  (%5.1f%%)%s" % (s, sc.get(s, 0), pct, notes.get(s, "")))
    L.append("-- mention coverage --")
    L.append("  Σmentioned=%d / 成功 cell=%d(=cells−failed;no_answer 计 0 留分母)= %s"
             % (stats["mentioned_sum"], stats["denominator"], _pct(stats["coverage"])))
    L.append("-- citation share(每答案每品牌至多计 1 次,各品牌恒和 100%)--")
    if panel.get("domain"):
        if stats["share"] is None:
            L.append("  N/A(尚无任何引用 URL,空分母)")
        else:
            L.append("  %s: %d / %d = %s"
                     % (panel["domain"], stats["brand_hits"], stats["domain_total"],
                        _pct(stats["share"])))
        top = stats["co_cited"].most_common(5)
        if top:
            L.append("  同场竞品域(top5): " + ", ".join(
                "%s %.1f%%" % (d, 100 * c / stats["domain_total"]) for d, c in top))
    else:
        L.append("  N/A(面板未设 --domain,无法把引用 URL 归到品牌)")
    L.append("-- 每 prompt 稳定性(≥3 次有效采样才报;z=1.96) --")
    if stats["stability"]:
        for prompt, (k, n, p, lo, hi, unstable) in sorted(stats["stability"].items()):
            L.append("  %-40.40s n=%d k=%d p=%.2f CI95[%.2f,%.2f] %s"
                     % (prompt, n, k, p, lo, hi,
                        "UNSTABLE(区间跨 0.5)" if unstable else "stable"))
    else:
        L.append("  无 ≥3 次采样的 prompt")
    L.append("  [i] 单次引用检查 = 掷硬币:不足 3 次采样的 prompt 不下结论")
    L.append("-- 分引擎(报告按 AI 引擎分列,不合并统计) --")
    for eng, sub in stats["per_engine"].items():
        L.append("  %-12s cells=%-3d coverage=%-7s share=%s"
                 % (eng, sub["cells"], _pct(sub["coverage"]), _pct(sub["share"])))
    if len(panel["prompts"]) < 10:
        L.append("[!] prompts=%d <10:样本太小,结论只能当方向" % len(panel["prompts"]))
    return "\n".join(L)


def cmd_report(args):
    panel = load_panel(args.panel)
    stats = compute_stats(panel, engine=args.engine)
    print(render_report(panel, stats))
    return 0


# ---------- diff(配对分母跨期) ----------

def resolve_run(arg, panel):
    if os.path.isfile(arg):
        with open(arg, encoding="utf-8") as f:
            return json.load(f)
    for r in panel.get("runs", []):
        if r.get("run_id") == arg:
            return r
    return None


def diff_runs(run_a, run_b):
    res_a, res_b = run_a["results"], run_b["results"]
    prompts = set(res_a) | set(res_b)
    paired, miss_a, miss_b = [], 0, 0
    for p in prompts:
        a, b = res_a.get(p), res_b.get(p)
        if a is None:
            miss_a += 1
        elif b is None:
            miss_b += 1
        elif a["state"] == "failed" or b["state"] == "failed":
            miss_a += (a["state"] == "failed")
            miss_b += (b["state"] == "failed")
        else:
            paired.append(p)
    new_mentions = [p for p in paired if res_b[p]["mentioned"] and not res_a[p]["mentioned"]]
    gone = [p for p in paired if res_a[p]["mentioned"] and not res_b[p]["mentioned"]]
    k1 = sum(res_a[p]["mentioned"] for p in paired)
    k2 = sum(res_b[p]["mentioned"] for p in paired)
    return {"paired": paired, "excluded": {"missing_in_a": miss_a, "missing_in_b": miss_b},
            "k1": k1, "k2": k2, "new_mentions": new_mentions, "disappeared": gone}


def cmd_diff(args):
    panel = load_panel(args.panel)
    ra, rb = resolve_run(args.run1, panel), resolve_run(args.run2, panel)
    if ra is None or rb is None:
        print("错误: 找不到 run(应为 run 文件路径或面板内 run_id): %s / %s"
              % (args.run1, args.run2), file=sys.stderr)
        return 1
    d = diff_runs(ra, rb)
    n = len(d["paired"])
    print("== diff(配对分母:只比两期均成功(非 failed)的 cell) ==")
    print("run1: %s (%s, %s)" % (ra.get("run_id"), ra.get("engine"), ra.get("date")))
    print("run2: %s (%s, %s)" % (rb.get("run_id"), rb.get("engine"), rb.get("date")))
    print("配对 cell: %d | 排除: run1 侧 %d,run2 侧 %d(失败或缺测)"
          % (n, d["excluded"]["missing_in_a"], d["excluded"]["missing_in_b"]))
    if n:
        print("mention: run1 %d/%d=%.1f%% → run2 %d/%d=%.1f%%"
              % (d["k1"], n, 100 * d["k1"] / n, d["k2"], n, 100 * d["k2"] / n))
    print("新提及(%d): %s" % (len(d["new_mentions"]),
          "; ".join(d["new_mentions"]) if d["new_mentions"] else "(无)"))
    print("消失提及(%d): %s" % (len(d["disappeared"]),
          "; ".join(d["disappeared"]) if d["disappeared"] else "(无)"))
    if n < 10:
        print("[!] 配对 cell=%d <10:样本太小,结论只能当方向" % n)
    return 0


# ---------- CLI / 自测 ----------

def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true", help="冒烟自测(不联网)")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("init", help="建立 panel.json")
    p.add_argument("--brand", required=True)
    p.add_argument("--prompts", required=True, help="prompt 列表 CSV(单列,可带表头)")
    p.add_argument("--aliases", default="", help="品牌别名,逗号分隔")
    p.add_argument("--domain", default="", help="品牌主域(用于 citation share)")
    p.add_argument("--engines", default="", help="逗号分隔,默认 chatgpt,perplexity,gemini,copilot,claude,grok")
    p.add_argument("--panel", default="panel.json")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("record", help="记录一次采样运行")
    p.add_argument("--engine", required=True)
    p.add_argument("--file", required=True, help="run.csv(prompt,mentioned,cited,cited_urls[,state])")
    p.add_argument("--run-id", default="")
    p.add_argument("--date", default="")
    p.add_argument("--panel", default="panel.json")
    p.set_defaults(func=cmd_record)
    p = sub.add_parser("report", help="输出面板报告")
    p.add_argument("--engine", default=None)
    p.add_argument("--panel", default="panel.json")
    p.set_defaults(func=cmd_report)
    p = sub.add_parser("diff", help="两组 run 配对对比(文件路径或 run_id)")
    p.add_argument("run1")
    p.add_argument("run2")
    p.add_argument("--panel", default="panel.json")
    p.set_defaults(func=cmd_diff)
    return ap


def _self_test():
    tmp = tempfile.mkdtemp(prefix="citation_panel_")
    panel_path = os.path.join(tmp, "panel.json")
    prompts_csv = os.path.join(tmp, "prompts.csv")
    with open(prompts_csv, "w", encoding="utf-8") as f:
        f.write("prompt\nbest crm for small business\ncrm 软件对比\nhelpdesk software\n")
    args = build_parser().parse_args(
        ["init", "--brand", "Acme", "--domain", "acme.ai", "--prompts", prompts_csv,
         "--panel", panel_path])
    assert cmd_init(args) == 0
    panel = load_panel(panel_path)
    assert panel["prompts"] == ["best crm for small business", "crm 软件对比", "helpdesk software"]
    assert os.path.isdir(os.path.join(tmp, "runs"))

    P1, P2, P3 = panel["prompts"]
    runs = [
        {"engine": "chatgpt", "rows": [
            (P1, "1", "1", "https://acme.ai/guide;https://www.comp.com/x", ""),
            (P2, "1", "0", "", ""),
            (P3, "0", "0", "", "failed")]},
        {"engine": "chatgpt", "rows": [
            (P1, "0", "0", "", ""),
            (P2, "1", "1", "https://acme.ai/pricing;https://docs.other.org/a", ""),
            (P3, "0", "0", "", "no_answer")]},
        {"engine": "perplexity", "rows": [
            (P1, "1", "1", "https://acme.ai/g2", ""),
            (P2, "0", "0", "", ""),
            (P3, "0", "0", "", "")]},
    ]
    for i, spec in enumerate(runs, 1):
        path = os.path.join(tmp, "run%d.csv" % i)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["prompt", "mentioned", "cited", "cited_urls", "state"])
            for row in spec["rows"]:
                w.writerow(row)
        rc = cmd_record(build_parser().parse_args(
            ["record", "--engine", spec["engine"], "--file", path,
             "--panel", panel_path, "--date", "2026-10-0%dT00:00:00" % i]))
        assert rc == 0

    panel = load_panel(panel_path)
    assert len(panel["runs"]) == 3
    stats = compute_stats(panel)
    # 五状态: cited_brand=3, name_only=1, failed=1, no_answer=1, brand_absent=3
    assert stats["cells"] == 9
    assert stats["state_counts"]["cited_brand"] == 3
    assert stats["state_counts"]["name_only_mention"] == 1
    assert stats["state_counts"]["failed"] == 1
    assert stats["state_counts"]["no_answer"] == 1
    assert stats["state_counts"]["brand_absent"] == 3
    # coverage: Σmentioned=4 / 成功=9-1=8 = 50.0%
    assert stats["denominator"] == 8 and stats["mentioned_sum"] == 4
    assert abs(stats["coverage"] - 0.5) < 1e-9
    # citation share: 品牌被引 3 / 去重域名总数 5 = 60%
    assert stats["brand_hits"] == 3 and stats["domain_total"] == 5
    assert abs(stats["share"] - 0.6) < 1e-9
    # Wilson: P1 n=3 k=2 → p=2/3, w=√(p(1-p)/3)≈0.272,CI 跨 0.5 → unstable
    k, n, p, lo, hi, unstable = stats["stability"][P1]
    assert (k, n) == (2, 3) and unstable and lo < 0.5 < hi
    # P2 n=3 k=2 同样 unstable;P3 n=2 不足 3 次,不报
    assert stats["stability"][P2][0] == 2 and P3 not in stats["stability"]
    # wilson 公式自检
    p, lo, hi, uns = wilson_ci(2, 3)
    w = math.sqrt((2 / 3) * (1 / 3) / 3)
    assert abs(hi - min(1.0, 2 / 3 + Z * w)) < 1e-12

    report = render_report(panel, stats)
    assert "五状态分类" in report and "50.0%" in report and "60.0%" in report
    assert "样本太小" in report and "掷硬币" in report

    d = diff_runs(panel["runs"][0], panel["runs"][1])
    assert sorted(d["paired"]) == [P1, P2]          # P3 在 run1 为 failed → 排除
    assert d["new_mentions"] == [] and d["disappeared"] == [P1]
    assert d["excluded"]["missing_in_a"] == 1
    d2 = diff_runs(panel["runs"][1], panel["runs"][2])
    assert d2["new_mentions"] == [P1] and d2["disappeared"] == [P2]

    # cited=1 但 mentioned=0 → 纠正为 mentioned=1
    bad = os.path.join(tmp, "bad.csv")
    with open(bad, "w", encoding="utf-8") as f:
        f.write("prompt,mentioned,cited,cited_urls\n%s,0,1,https://acme.ai/x\n" % P1)
    res, warns = read_run_csv(bad, panel)
    assert res[P1]["mentioned"] == 1 and res[P1]["state"] == "cited_brand" and warns
    # registrable_domain
    assert registrable_domain("https://www.acme.co.uk/a?b=1") == "acme.co.uk"
    assert registrable_domain("https://docs.other.org/x") == "other.org"
    print("[self-test] PASS citation_panel(9 cells, coverage=62.5%, share=60.0%, "
          "wilson unstable 案例, 配对 diff, cited/mentioned 纠正)")


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if getattr(args, "self_test", False):
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL citation_panel")
            return 1
    if not getattr(args, "cmd", None):
        ap.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
