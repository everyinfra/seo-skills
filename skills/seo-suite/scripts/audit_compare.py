#!/usr/bin/env python3
"""两次 site_audit --json 审计对比器(Ahrefs Crawl Comparison 口径,stdlib only)。
三张清单:
  新增 issue     新审计有、旧审计无的 finding,按 URL+rule 认定;同 key 严重度升级
                 (如 WARN→CRITICAL)也计入新增并标 escalated=True。
  已修复 issue   旧审计有、新审计无的 finding(同 URL+rule 口径)。
  分数与覆盖面   主分(Ahrefs:(无 CRITICAL URL÷可评分 URL)×100,refused 不进分母)/
                 AI Search Health 均值/受影响 URL 面(≥1 条 finding)/逐 URL verdict
                 与 ai_search_health 变化/URL 覆盖增删与 coverage_ratio(Ryte 口径:
                 样本两次分数不可比,必须显式输出交集占比)。
  页级 changed   两审计都在场的 URL 的 title/status(verdict)/word_count/h1/canonical
                 字段变化(canonical 两侧皆缺时自动跳过,site_audit meta 补字段即纳入)。
--baseline-gate N(Lumar Protect 语义):主分跌幅(old−new)>N → 退出码 1;默认不启用。
用法: python3 audit_compare.py --old old.json --new new.json [--baseline-gate N] [--json]
退出码: 0 正常(或 gate 未触发)/ 1 baseline gate 触发 / 2 输入或参数错误。"""
import sys, os, json

SCHEMA_VERSION = "1.0"
SEV_ORDER = {"CRITICAL": 0, "WARN": 1, "INFO": 2}
# 页级对比字段:(取值键, 展示名)。verdict 取自页对象,其余取自 meta;
# canonical site_audit meta 暂无 → 两侧都缺时不报,未来补字段自动生效。
PAGE_FIELDS = (("title", "title"), ("verdict", "status"), ("words", "word_count"),
               ("h1", "h1"), ("canonical", "canonical"))

USAGE = """usage: audit_compare.py --old old.json --new new.json [--baseline-gate N] [--json]
两次 site_audit.py --json 输出的对比(Ahrefs Crawl Comparison 口径):
  新增 issue     新审计有、旧审计无的 finding(按 URL+rule);同 key 严重度升级
                 (WARN→CRITICAL)计入新增并标 escalated。
  已修复 issue   旧审计有、新审计无的 finding(同 URL+rule 口径)。
  分数与覆盖面   主分(Ahrefs:(无 CRITICAL URL÷可评分 URL)×100,refused 不进分母)/
                 AI Search Health 均值/受影响 URL 面/逐 URL verdict 与 ai_search_health
                 变化/URL 覆盖增删 + coverage_ratio(Ryte:样本分数不可比须显式声明)。
  页级 changed   交集 URL 的 title/status(verdict)/word_count/h1/canonical 字段变化。
选项:
  --old F / --new F      两次 site_audit --json 输出文件(均必填)
  --baseline-gate N      Lumar Protect 语义:主分跌幅(old−new)>N → 退出码 1;默认不启用
                         (旧审计无可评分 URL 时无基线,gate 不触发)
  --json                 结构化输出(默认输出 markdown 人读报告)
退出码: 0 正常 / 1 baseline gate 触发 / 2 输入或参数错误。"""


def _die(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def load_audit(path):
    """读 site_audit --json 输出。--json 模式文件前部混有逐 URL 文本行(meta: {...}
    行可解析但不完整),故从每个 '{' 起点试解并取含 results 字典的候选;
    无候选则退出码 2。(与 health_score.load_audit 同思路,套件约定脚本自包含。)"""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        _die("读不了 %s: %s" % (path, e))
    cands = []
    try:
        cands.append(json.loads(text))
    except json.JSONDecodeError:
        pass
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                cands.append(json.loads(text[i:]))
            except json.JSONDecodeError:
                continue
    for cand in cands:
        if isinstance(cand, dict) and isinstance(cand.get("results"), dict):
            return cand
    _die("无法从 %s 解析出含 results 的 JSON(应为 site_audit.py --json 的输出)" % path)


def main_score(audit):
    """主分【Ahrefs 官方】:(无 CRITICAL 的 URL 数÷可评分 URL 数)×100。
    verdict=refused(fetch guard 拒审)不进分母;无可评分 URL → None。"""
    scored = [r for r in audit["results"].values() if r.get("verdict") != "refused"]
    if not scored:
        return None
    crit = sum(1 for r in scored if r.get("verdict") == "fail")
    return round((len(scored) - crit) / len(scored) * 100, 1)


def ai_health_mean(audit):
    """AI Search Health 均值(0-100):有 ai_search_health.score 的页才计入;无 → None。"""
    vals = [r["ai_search_health"]["score"] for r in audit["results"].values()
            if isinstance(r.get("ai_search_health"), dict)
            and r["ai_search_health"].get("score") is not None]
    return round(sum(vals) / len(vals), 1) if vals else None


def _affected(audit):
    """受影响 URL 面:≥1 条非 SKIP finding 的 URL 数。"""
    return sum(1 for r in audit["results"].values()
               if any(f.get("severity") in SEV_ORDER for f in r.get("findings", [])))


def _issue_index(audit):
    """(url, rule) → (最高严重度, 代表消息)。SKIP(fetch guard 拒审)不是 issue,不入索引。"""
    idx = {}
    for url, r in audit["results"].items():
        for f in r.get("findings", []):
            sev, area = f.get("severity"), f.get("area")
            if sev not in SEV_ORDER or not area:
                continue
            key = (url, area)
            cur = idx.get(key)
            if cur is None or SEV_ORDER[sev] < SEV_ORDER[cur[0]]:
                idx[key] = (sev, f.get("message", ""))
    return idx


def _fmt(v):
    return "N/A" if v is None else v


def compare(old, new, baseline_gate=None):
    """纯对比:两次已解析的 site_audit --json dict → 报告 dict(+退出码)。"""
    ro, rn = old["results"], new["results"]
    io, inew = _issue_index(old), _issue_index(new)
    new_issues, fixed_issues = [], []
    for (url, rule) in sorted(inew, key=lambda k: (SEV_ORDER[inew[k][0]], k[0], k[1])):
        sev, msg = inew[(url, rule)]
        if (url, rule) not in io:
            new_issues.append({"url": url, "rule": rule, "severity": sev,
                               "message": msg, "escalated": False})
        elif SEV_ORDER[sev] < SEV_ORDER[io[(url, rule)][0]]:   # 同 key 严重度升级 → 计入新增
            new_issues.append({"url": url, "rule": rule, "severity": sev, "message": msg,
                               "escalated": True, "severity_before": io[(url, rule)][0]})
    for (url, rule) in sorted(io, key=lambda k: (SEV_ORDER[io[k][0]], k[0], k[1])):
        if (url, rule) not in inew:
            sev, msg = io[(url, rule)]
            fixed_issues.append({"url": url, "rule": rule, "severity": sev, "message": msg})

    ms_o, ms_n = main_score(old), main_score(new)
    ai_o, ai_n = ai_health_mean(old), ai_health_mean(new)
    aff_o, aff_n = _affected(old), _affected(new)
    common = sorted(set(ro) & set(rn))
    verdict_changes = [{"url": u, "old": ro[u].get("verdict"), "new": rn[u].get("verdict")}
                       for u in common if ro[u].get("verdict") != rn[u].get("verdict")]
    ai_changes = []
    for u in common:
        so = (ro[u].get("ai_search_health") or {}).get("score")
        sn = (rn[u].get("ai_search_health") or {}).get("score")
        if so is not None and sn is not None and so != sn:
            ai_changes.append({"url": u, "old": so, "new": sn, "delta": round(sn - so, 1)})
    urls_added = sorted(set(rn) - set(ro))
    urls_removed = sorted(set(ro) - set(rn))
    denom = max(len(ro), len(rn))
    coverage_ratio = round(len(common) / denom, 3) if denom else 1.0

    pages_changed = []
    for u in common:
        changes = []
        for key, label in PAGE_FIELDS:
            if key == "verdict":
                ov, nv = ro[u].get("verdict"), rn[u].get("verdict")
            else:
                ov = (ro[u].get("meta") or {}).get(key)
                nv = (rn[u].get("meta") or {}).get(key)
            if ov != nv and not (ov is None and nv is None):
                changes.append({"field": label, "old": ov, "new": nv})
        if changes:
            pages_changed.append({"url": u, "changes": changes})

    gate = None
    if baseline_gate is not None:
        if ms_o is None:
            gate = {"threshold": baseline_gate, "drop": None, "tripped": False,
                    "note": "旧审计无可评分 URL,无基线可守"}
        else:
            eff_n = 0.0 if ms_n is None else ms_n   # 新审计全拒审 → 按健康 0 计跌幅
            drop = round(ms_o - eff_n, 1)
            gate = {"threshold": baseline_gate, "drop": drop, "tripped": drop > baseline_gate}

    rep = {
        "schema_version": SCHEMA_VERSION,
        "old": {"main_score": ms_o, "ai_search_health_mean": ai_o,
                "audited": len(ro), "affected_urls": aff_o},
        "new": {"main_score": ms_n, "ai_search_health_mean": ai_n,
                "audited": len(rn), "affected_urls": aff_n},
        "delta": {"main_score": (round(ms_n - ms_o, 1)
                                 if ms_o is not None and ms_n is not None else None),
                  "ai_search_health_mean": (round(ai_n - ai_o, 1)
                                            if ai_o is not None and ai_n is not None else None),
                  "affected_urls": aff_n - aff_o,
                  "urls_added": urls_added, "urls_removed": urls_removed,
                  "coverage_ratio": coverage_ratio},
        "new_issues": new_issues,
        "fixed_issues": fixed_issues,
        "verdict_changes": verdict_changes,
        "ai_health_changes": ai_changes,
        "pages_changed": pages_changed,
        "baseline_gate": gate,
    }
    return rep, (1 if gate and gate.get("tripped") else 0)


def _issue_lines(issues):
    out = []
    for it in issues:
        esc = "↑(%s→%s)" % (it.get("severity_before"), it["severity"]) if it.get("escalated") else ""
        out.append("- [%s%s] %s — %s: %s" % (it["severity"], esc, it["url"], it["rule"], it["message"]))
    return out or ["- (无)"]


def render(rep):
    """人读 markdown:三张清单 + 页级 changed + gate。"""
    o, n, d = rep["old"], rep["new"], rep["delta"]
    L = ["# 审计对比(Ahrefs Crawl Comparison 口径)",
         "",
         "## 新增 issue(%d)" % len(rep["new_issues"])]
    L += _issue_lines(rep["new_issues"])
    L += ["", "## 已修复 issue(%d)" % len(rep["fixed_issues"])]
    L += _issue_lines(rep["fixed_issues"])
    L += ["", "## 分数与覆盖面 delta",
          "- 主分(Ahrefs,无 CRITICAL URL 占比×100): %s → %s(Δ %s)"
          % (_fmt(o["main_score"]), _fmt(n["main_score"]), _fmt(d["main_score"])),
          "- AI Search Health 均值: %s → %s(Δ %s)"
          % (_fmt(o["ai_search_health_mean"]), _fmt(n["ai_search_health_mean"]),
             _fmt(d["ai_search_health_mean"])),
          "- 受影响 URL 面(≥1 条 finding): %d → %d(Δ %+d)"
          % (o["affected_urls"], n["affected_urls"], d["affected_urls"]),
          "- URL 覆盖: %d → %d(交集 %d,coverage_ratio %s;新增 %d/移除 %d)"
          % (o["audited"], n["audited"], o["audited"] - len(d["urls_removed"]),
             d["coverage_ratio"], len(d["urls_added"]), len(d["urls_removed"])),
          "- coverage: 基于爬取样本,两次分数仅在交集 URL 语义下可比(Ryte 官方口径)"]
    if d["urls_added"]:
        L.append("  - 新增: %s" % ", ".join(d["urls_added"]))
    if d["urls_removed"]:
        L.append("  - 移除: %s" % ", ".join(d["urls_removed"]))
    L.append("- verdict 变化(%d):" % len(rep["verdict_changes"]))
    L += ["  - %s: %s → %s" % (v["url"], v["old"], v["new"]) for v in rep["verdict_changes"]] \
        or ["  - (无)"]
    L.append("- ai_search_health 变化(%d):" % len(rep["ai_health_changes"]))
    L += ["  - %s: %s → %s(%+s)" % (a["url"], a["old"], a["new"], a["delta"])
          for a in rep["ai_health_changes"]] or ["  - (无)"]
    L += ["", "## 页级 changed(%d)" % len(rep["pages_changed"])]
    if rep["pages_changed"]:
        for p in rep["pages_changed"]:
            L.append("- %s: %s" % (p["url"], "; ".join(
                "%s %r→%r" % (c["field"], c["old"], c["new"]) for c in p["changes"])))
    else:
        L.append("- (无)")
    g = rep["baseline_gate"]
    if g is not None:
        note = "(%s)" % g["note"] if g.get("note") else ""
        L += ["", "## baseline gate(Lumar Protect 语义)",
              "- 阈值 %s,实际跌幅 %s%s → %s" % (g["threshold"], _fmt(g["drop"]), note,
                                                 "触发(退出码 1)" if g["tripped"] else "未触发")]
    return "\n".join(L)


def main():
    argv = sys.argv[1:]
    if any(a in ("-h", "--help") for a in argv):
        print(USAGE)
        return
    old_path = new_path = gate = None
    as_json = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--old" and i + 1 < len(argv):
            old_path = argv[i + 1]; i += 2
        elif a == "--new" and i + 1 < len(argv):
            new_path = argv[i + 1]; i += 2
        elif a == "--baseline-gate" and i + 1 < len(argv):
            try:
                gate = float(argv[i + 1])
            except ValueError:
                _die("--baseline-gate 需要数字阈值,得到 %r" % argv[i + 1])
            i += 2
        elif a == "--json":
            as_json = True; i += 1
        else:
            _die("未知参数 %r\n%s" % (a, USAGE))
    if not old_path or not new_path:
        _die("缺少 --old 或 --new\n" + USAGE)
    rep, rc = compare(load_audit(old_path), load_audit(new_path), baseline_gate=gate)
    if as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(render(rep))
    sys.exit(rc)


if __name__ == "__main__":
    main()
