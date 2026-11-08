#!/usr/bin/env python3
"""lifecycle.py — 两条轴诊断:产品在哪个阶段 × 每个方面成熟到几级(RQ-237;stdlib only)。

规则全在 data/lifecycle.json(阶段阈值、6 个阶段、5 维 × 5 级成熟度条件、按阶段的补短顺序);
用户在 seo-ops/playbook/lifecycle.json 里写同名键可以覆盖(顶层键整体替换)。本脚本只做
「收证据 → 套条件」,不靠模型感觉:证据缺失的条件判「未知」,该维停在已证实的级别,并列出要补什么。

证据从哪来(都可缺):
  --scan      product_scan.py 的输出(signals、page_types、facts)
  --ws        seo-ops 工作区:context/profile.json(开局答案、metrics)、history/*/health.json
              (最近一次体检)、runs/*/agenda.json(每周运营单期数)、ledger/acks.jsonl(已读)、
              ledger/changes.jsonl(内容改动)
  --metrics   额外的指标 JSON(扁平键,如 {"gsc_clicks_28d": 1200, "referring_domains": 35});
              同名键覆盖 profile.json 里的 metrics

阶段判定(顺序执行,先命中先用):
  1. 档案里声明了改版类事件(change_events)→ 5 改版;另报底层阶段
  2. 站点不可访问:仓库有公开路由 → 1 上线前;否则 → 0 想法(只给了仓库、没给站点时同样判,标「猜测」)
  3. 站点可访问但 robots 全封或首页 noindex → 1 上线前
  4. 有 GSC:近 28 天展示 < 阈值,或站龄 < 90 天 → 2 刚上线;点击环比 ≥ +10% → 3;≤ -10% → 4;
     其余站龄 ≥ 2 年 → 4(平台期),否则 → 3
  5. 没有 GSC:站龄 < 90 天 → 2;否则是猜测(URL 数少 → 2,否则 → 3),confidence=guess,
     列候选、要用户确认
用户在开局第 1 环确认过的阶段(profile.stage.confirmed)优先于规则,但规则结果照样输出,两者不一致时写进 conflicts。

用法:
  python3 lifecycle.py diagnose [--scan product_scan.json] [--ws seo-ops] [--metrics m.json] [--json]
退出码:0 正常;2 输入错。
"""
import argparse
import datetime as dt
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(os.path.dirname(HERE), "data", "lifecycle.json")
DIMS = ("technical", "content", "authority", "geo", "measurement")


class UsageError(Exception):
    pass


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def load_rules(ws=None):
    rules = read_json(RULES_PATH)
    if not rules:
        raise UsageError("读不到规则表 %s" % RULES_PATH)
    if ws:
        over = read_json(os.path.join(ws, "playbook", "lifecycle.json"))
        if isinstance(over, dict):
            for k, v in over.items():
                if k != "about":
                    rules[k] = v
    return rules


# ---------------------------------------------------------------------------
# 收证据
# ---------------------------------------------------------------------------

def _fact(scan, key):
    for f in (scan or {}).get("facts") or []:
        if f.get("key") == key:
            return f.get("value")
    return None


def _age_days(first_seen, today=None):
    if not first_seen:
        return None
    try:
        d = dt.date.fromisoformat(str(first_seen)[:10])
    except ValueError:
        return None
    return ((today or dt.date.today()) - d).days


def collect_evidence(scan=None, ws=None, metrics=None, today=None):
    """把 scan / 工作区 / 指标拍平成 {点分键: 值};缺的键不出现(条件判未知)。"""
    ev = {}
    sig = (scan or {}).get("signals") or {}
    for k, v in sig.items():
        if v is not None:
            ev["signals." + k] = v
    if scan is not None:
        name = _fact(scan, "product.name")
        ev["signals.brand_name"] = name if isinstance(name, str) else ""
        same = sig.get("same_as") or []
        ev["signals.same_as_count"] = len(same) if isinstance(same, list) else 0
        site_scan = scan.get("site_scan") or {}
        pt = site_scan.get("page_types") if isinstance(site_scan, dict) else None
        if isinstance(pt, dict):
            g = lambda *ks: sum(int(pt.get(k) or 0) for k in ks)  # noqa: E731
            ev["page_types.core"] = g("pricing", "product", "docs")
            ev["page_types.editorial"] = g("blog")
            ev["page_types.intent"] = g("compare", "integrations", "customers")
        age = _age_days(sig.get("first_seen"), today)
        if age is not None:
            ev["signals.age_days"] = age
    prof = {}
    if ws:
        prof = read_json(os.path.join(ws, "context", "profile.json"), {}) or {}
        rings = prof.get("rings") or {}
        r1 = rings.get("1") or {}
        ev["profile.ring1_confirmed"] = r1.get("status") == "confirmed"
        answers = {}
        for r in rings.values():
            answers.update(r.get("answers") or {})
        if "conversion" in answers:
            ev["profile.conversion_defined"] = bool(str(answers["conversion"]).strip())
        if "kpi_target" in answers:
            ev["profile.kpi_defined"] = bool(str(answers["kpi_target"]).strip())
        # 最近一次体检
        runs = sorted(glob.glob(os.path.join(ws, "history", "*", "health.json")))
        if runs:
            h = read_json(runs[-1], {}) or {}
            if h.get("main_score") is not None:
                ev["health.score"] = h["main_score"]
            if h.get("urls_total") is not None and h.get("urls_clean") is not None:
                ev["health.critical"] = int(h["urls_total"]) - int(h["urls_clean"])
        agendas = sorted(glob.glob(os.path.join(ws, "runs", "*", "agenda.json")))
        ev["ops.weekly_runs"] = len(agendas)
        acks = set()
        try:
            with open(os.path.join(ws, "ledger", "acks.jsonl"), encoding="utf-8") as f:
                for line in f:
                    try:
                        acks.add(json.loads(line).get("run"))
                    except ValueError:
                        pass
        except OSError:
            pass
        last4 = [os.path.basename(os.path.dirname(p)) for p in agendas[-4:]]
        if last4:
            ev["ops.agenda_read_rate"] = round(sum(1 for r in last4 if r in acks) / len(last4), 2)
        cutoff = (today or dt.date.today()) - dt.timedelta(days=90)
        n_content = 0
        try:
            with open(os.path.join(ws, "ledger", "changes.jsonl"), encoding="utf-8") as f:
                for line in f:
                    try:
                        c = json.loads(line)
                    except ValueError:
                        continue
                    at = str(c.get("at") or "")[:10]
                    if at and at >= cutoff.isoformat() and c.get("kind", "content") == "content":
                        n_content += 1
        except OSError:
            pass
        if os.path.isfile(os.path.join(ws, "ledger", "changes.jsonl")):
            ev["ops.content_changes_90d"] = n_content
    m = dict(prof.get("metrics") or {})
    m.update(metrics or {})
    for k, v in m.items():
        if v is not None:
            ev["metrics." + k] = v
    if "metrics.gsc_clicks_28d" in ev or "metrics.gsc_impressions_28d" in ev:
        ev.setdefault("metrics.gsc_connected", True)
    if "metrics.ai_referrals_28d" in ev or "metrics.ai_citation_weeks" in ev:
        ev.setdefault("metrics.ai_visibility_measured", True)
    return ev, prof


# ---------------------------------------------------------------------------
# 条件求值
# ---------------------------------------------------------------------------

def check(cond, ev):
    """→ True / False / None(证据缺失)。"""
    key, op = cond["key"], cond["op"]
    if key not in ev:
        return None
    v = ev[key]
    want = cond.get("value")
    try:
        if op == "true":
            return bool(v) is True
        if op == "false":
            return bool(v) is False
        if op == "nonempty":
            return bool(v)
        if op == "==":
            return v == want
        if op == ">=":
            return float(v) >= float(want)
        if op == "<=":
            return float(v) <= float(want)
        if op == ">":
            return float(v) > float(want)
        if op == "<":
            return float(v) < float(want)
        if op == "in":
            return v in (want or [])
    except (TypeError, ValueError):
        return None
    raise UsageError("规则表里有不认识的条件 op: %r" % op)


def maturity(rules, ev):
    out = {}
    for d in rules["maturity"]:
        level, missing, nxt, cmd, basis = 0, [], None, None, []
        for lv in d["levels"]:
            res = [(c, check(c, ev)) for c in lv["all"]]
            if all(r is True for _, r in res):
                level = lv["level"]
                basis.append("L%d:%s" % (lv["level"], ",".join(
                    "%s=%s" % (c["key"], ev.get(c["key"])) for c, _ in res)))
                continue
            missing = [c["key"] for c, r in res if r is None]
            nxt, cmd = lv["next"], lv.get("cmd") or ""
            break
        out[d["dim"]] = {"name": d["name"], "level": level,
                         "status": "unknown" if (missing and level == 0) else ("partial" if missing else "ok"),
                         "missing": missing, "next": nxt, "cmd": cmd, "basis": basis}
    return out


def stage(rules, ev, prof=None):
    th = rules["stage_thresholds"]
    names = {s["id"]: s["name"] for s in rules["stages"]}
    why, cands, conf, sid = [], [], "rule", None
    events = [e for e in ((prof or {}).get("events") or []) if e in rules.get("change_events", [])]
    live = ev.get("signals.site_live")
    routes = ev.get("signals.repo_public_routes") or 0
    age = ev.get("signals.age_days")
    impr = ev.get("metrics.gsc_impressions_28d")
    clicks = ev.get("metrics.gsc_clicks_28d")
    prev = ev.get("metrics.gsc_clicks_prev_28d")
    base = None
    if "signals.site_live" not in ev and "signals.repo_public_routes" in ev:
        # 只给了仓库、没给站点:空仓库多半是想法阶段,有公开路由多半是上线前;是猜测,第 1 环让用户确认
        sid = 1 if routes > 0 else 0
        return {"stage": sid, "name": names[sid], "base_stage": None, "base_name": None, "confidence": "guess",
                "why": ["没给站点地址,只读了仓库:" + ("有 %d 条公开路由" % routes if routes else "没有公开路由")
                        + ";站点已经上线的话补 --site 重跑"],
                "candidates": [0, 1, 2], "missing": ["signals.site_live"], "conflicts": []}
    if "signals.site_live" not in ev:
        return {"stage": None, "name": "未知", "base_stage": None, "base_name": None, "confidence": "unknown",
                "why": ["没有站点和仓库的证据,先跑 product_scan.py"], "candidates": [],
                "missing": ["signals.site_live"], "conflicts": []}
    if not live:
        base = 1 if routes > 0 else 0
        why.append("站点不可访问" + ("(仓库有 %d 条公开路由)" % routes if routes else ",仓库里也没有公开路由"))
    elif ev.get("signals.robots_block_all") or ev.get("signals.homepage_noindex"):
        base = 1
        why.append("站点可访问但 robots 全封或首页 noindex")
    elif impr is not None or clicks is not None:
        if (impr is not None and impr < th["low_impressions_28d"]) or (age is not None and age < th["new_site_age_days"]):
            base = 2
            why.append("近 28 天展示 %s(门槛 %d),站龄 %s(门槛 %d 天)" % (impr, th["low_impressions_28d"], ("%d 天" % age) if age is not None else "未知", th["new_site_age_days"]))
        elif clicks is not None and prev:
            delta = (float(clicks) - float(prev)) / float(prev)
            if delta >= th["growth_clicks_delta"]:
                base = 3
            elif delta <= th["decline_clicks_delta"]:
                base = 4
            elif age is not None and age >= th["mature_age_days"]:
                base = 4
            else:
                base = 3
            why.append("点击环比 %+.0f%%(%s → %s)%s" % (delta * 100, prev, clicks, (",站龄 %d 天" % age) if age is not None else ",站龄未知"))
        else:
            base = 3
            conf = "guess"
            why.append("有展示数但缺上一期点击,按增长期猜")
            cands = [3, 4]
    else:
        if age is not None and age < th["new_site_age_days"]:
            base = 2
            why.append("站龄 %d 天(<%d),没有 GSC" % (age, th["new_site_age_days"]))
        else:
            conf = "guess"
            n = ev.get("signals.url_count")
            base = 2 if (n is not None and n < th["guess_small_site_urls"]) else 3
            why.append("没有 GSC 数据,按 URL 数 %s%s猜;请用户确认" % (n, (",站龄 %d 天" % age) if age is not None else ",站龄未知"))
            cands = [2, 3, 4]
    sid = base
    if events:
        sid = 5
        why.insert(0, "档案声明了改版类事件:%s" % ",".join(events))
    res = {"stage": sid, "name": names.get(sid), "base_stage": base, "base_name": names.get(base),
           "confidence": conf, "why": why, "candidates": [{"id": c, "name": names[c]} for c in cands],
           "missing": [] if (impr is not None or clicks is not None or not live) else ["metrics.gsc_impressions_28d", "metrics.gsc_clicks_28d", "metrics.gsc_clicks_prev_28d"],
           "conflicts": []}
    confirmed = ((prof or {}).get("stage") or {})
    if confirmed.get("confirmed") and confirmed.get("value") is not None:
        cv = int(confirmed["value"])
        if cv != sid:
            res["conflicts"].append("用户确认的阶段是 %s,规则判的是 %s" % (names.get(cv), names.get(sid)))
        res.update({"stage": cv, "name": names.get(cv), "confidence": "confirmed"})
    return res


def diagnose(scan=None, ws=None, metrics=None, today=None):
    rules = load_rules(ws)
    ev, prof = collect_evidence(scan, ws, metrics, today)
    st = stage(rules, ev, prof)
    mat = maturity(rules, ev)
    order = rules["dim_priority_by_stage"].get(str(st["stage"]), list(DIMS)) if st["stage"] is not None else list(DIMS)
    known = [d for d in order if mat[d]["status"] != "unknown" and mat[d]["level"] < 5]
    weakest = None
    if known:
        low = min(mat[d]["level"] for d in known)
        weakest = next(d for d in order if d in known and mat[d]["level"] == low)
    focus = next((s["focus"] for s in rules["stages"] if s["id"] == st["stage"]), [])
    return {"schema": 1, "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stage": st, "maturity": mat, "weakest": weakest,
            "next": ({"dim": weakest, "level_to": mat[weakest]["level"] + 1,
                      "action": mat[weakest]["next"], "cmd": mat[weakest]["cmd"]} if weakest else None),
            "stage_focus": focus,
            "unknown_dims": [d for d in DIMS if mat[d]["status"] == "unknown"],
            "evidence_keys": sorted(ev)}


def render(diag):
    st, mat = diag["stage"], diag["maturity"]
    L = ["## 产品阶段:%s%s" % (st["name"], {"guess": "(猜测,请确认)", "unknown": "(证据不够)"}.get(st["confidence"], "")),
         "依据:" + ";".join(st["why"])]
    if st["stage"] == 5 and st.get("base_name"):
        L.append("底层阶段:%s" % st["base_name"])
    if st["candidates"]:
        L.append("候选:" + "、".join(c["name"] for c in st["candidates"]))
    for c in st["conflicts"]:
        L.append("冲突:" + c)
    L += ["", "## 成熟度(1 零散 · 2 能重复 · 3 有体系 · 4 可度量 · 5 持续优化)", "",
          "| 方面 | 级别 | 下一级要做 | 缺的证据 |", "|---|---|---|---|"]
    for d in DIMS:
        m = mat[d]
        lv = "未知" if m["status"] == "unknown" else str(m["level"])
        L.append("| %s | %s | %s | %s |" % (m["name"], lv, m["next"] or "—", "、".join(m["missing"]) or "—"))
    if diag["next"]:
        n = diag["next"]
        L += ["", "## 最该补的一格:%s → %d 级" % (mat[n["dim"]]["name"], n["level_to"]),
              "下一件事:%s%s" % (n["action"], ("(%s)" % n["cmd"]) if n["cmd"] else "")]
    if diag["stage_focus"]:
        L += ["", "## 这个阶段的重点"] + ["- " + x for x in diag["stage_focus"]]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="两条轴诊断:产品阶段 × 5 维成熟度")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("diagnose")
    p.add_argument("--scan")
    p.add_argument("--ws")
    p.add_argument("--metrics")
    p.add_argument("--today", help="YYYY-MM-DD(测试用)")
    p.add_argument("--json", action="store_true")
    ns = ap.parse_args(argv)
    try:
        scan = read_json(ns.scan) if ns.scan else None
        if ns.scan and scan is None:
            raise UsageError("读不到 --scan %s" % ns.scan)
        metrics = read_json(ns.metrics) if ns.metrics else None
        today = dt.date.fromisoformat(ns.today) if ns.today else None
        if ns.ws and not os.path.isdir(ns.ws):
            raise UsageError("--ws 不是目录: %s" % ns.ws)
        d = diagnose(scan, ns.ws, metrics, today)
    except UsageError as e:
        print("错误: %s" % e, file=sys.stderr)
        return 2
    print(json.dumps(d, ensure_ascii=False, indent=1) if ns.json else render(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
