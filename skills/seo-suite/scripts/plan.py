#!/usr/bin/env python3
"""plan.py — 按产品阶段出方案、90 天路线和中英战略书(RQ-237 第 2 批;stdlib only)。

开局第 6 环用:先读开局档案(seo-ops/context/profile.json)和两条轴诊断,再从 data/playbooks.json 里
**只取本阶段的打法**(不跨阶段),按成熟度最弱的一格加权排序,每条建议都把档案里的产品事实(产品线、
客户、转化、竞品、市场)填进去,并写清动哪类页面、预期动哪个数、怎么量、第几周做。

过滤(都写进战略书,证明不是没考虑):
  - only_if 不成立 → 不适用(比如没有新产品线就不出「新产品线回第 1 环」)
  - done_if 全部成立 → 已经做完(比如已有 llms.txt)
  - veto 任一成立 → 本轮出局,附理由(比如页面不到 100 不做内链)
  - 禁用清单(profile.deny,开局第 5 环「明确不做」)→ 整条命中就去掉;只沾边的保留并注明「不含 X」
  - force_first_if 成立 → 排第一(体检有 CRITICAL 时先修技术,strategy-fit「先基座」)

用户在 seo-ops/playbook/plays.json 写 {"plays": [...]} 可以加自己的打法,同 id 覆盖内置的。

用法:
  python3 plan.py build --ws seo-ops [--metrics m.json] [--top 10] [--json]
  python3 plan.py show --ws seo-ops
产出:seo-ops/plan/plan.json、roadmap.md、strategy-book.zh.md、strategy-book.en.md
退出码:0 正常;2 输入错;3 开局第 1 环没确认或阶段未知(先回开局)。
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lifecycle as LC  # noqa: E402

PLAYBOOKS = os.path.join(os.path.dirname(HERE), "data", "playbooks.json")
WEEKS = 13
MAX_STARTS_PER_WEEK = 3
MISSING_VALUES = ("", "(用户不知道)", "(已答,存在 context/private/)", "没有", "无", "none", "n/a")

FALLBACK = {"product": ("产品", "the product"), "main_line": ("主产品线", "the main product line"),
            "lines": ("各产品线", "each product line"), "customers": ("目标客户", "target customers"),
            "conversion": ("主转化", "the primary conversion"), "competitor": ("主要竞品", "the main competitor"),
            "market": ("主市场", "the primary market"), "market_code": ("en", "en")}
FACT_SLOTS = ("product", "main_line", "lines", "customers", "conversion", "competitor", "market")


class UsageError(Exception):
    pass


class GateError(Exception):
    pass


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ---------------------------------------------------------------------------
# 档案 → 产品事实
# ---------------------------------------------------------------------------

def _answers(prof):
    out = {}
    for r in sorted((prof.get("rings") or {}), key=lambda x: int(x)):
        for k, v in ((prof["rings"][r].get("answers") or {}).items()):
            out[k] = (v, r)
    return out


def _fact(prof, key):
    best = None
    for f in prof.get("facts") or []:
        if f.get("key") == key:
            if best is None or f.get("status") in ("confirmed", "corrected"):
                best = f
    return best


def _ok(v):
    if v is None:
        return False
    if isinstance(v, (list, tuple)):
        return bool([x for x in v if _ok(x)])
    return str(v).strip().lower() not in MISSING_VALUES


def _split(v):
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if str(x).strip()]
    return [x.strip() for x in re.split(r"[,,、;;/]| vs | 和 ", str(v)) if x.strip()]


def product_facts(prof):
    """→ {slot: {"value", "source", "confirmed"}};取不到的槽不出现。"""
    ans = _answers(prof)
    out = {}

    def put(slot, value, source, confirmed):
        if _ok(value) and slot not in out:
            out[slot] = {"value": value, "source": source, "confirmed": confirmed}

    def from_fact(slot, key, fmt=lambda v: v):
        f = _fact(prof, key)
        if f and _ok(f.get("value")):
            put(slot, fmt(f["value"]), "fact:" + key, f.get("status") in ("confirmed", "corrected"))

    from_fact("product", "product.name")
    if "main_line" in ans:
        put("main_line", ans["main_line"][0], "ring%s.main_line" % ans["main_line"][1], True)
    lines_f = _fact(prof, "product.lines")
    if lines_f and _ok(lines_f.get("value")):
        lines = _split(lines_f["value"])[:4]
        put("lines", "、".join(lines), "fact:product.lines", lines_f.get("status") in ("confirmed", "corrected"))
        put("main_line", lines[0], "fact:product.lines", lines_f.get("status") in ("confirmed", "corrected"))
    for slot in ("customers", "conversion"):
        if slot in ans:
            put(slot, ans[slot][0], "ring%s.%s" % (ans[slot][1], slot), True)
    if "real_competitors" in ans and _ok(ans["real_competitors"][0]):
        put("competitor", _split(ans["real_competitors"][0])[0], "ring%s.real_competitors" % ans["real_competitors"][1], True)
    for key in ("competitors.business", "competitors.serp"):
        f = _fact(prof, key)
        if f and _ok(f.get("value")):
            put("competitor", _split(f["value"])[0], "fact:" + key, f.get("status") in ("confirmed", "corrected"))
    if "market_first" in ans:
        put("market", ans["market_first"][0], "ring%s.market_first" % ans["market_first"][1], True)
    if prof.get("market"):
        put("market", prof["market"], "profile.market", True)
    from_fact("market", "market.languages", lambda v: _split(v)[0])
    if "market" in out:
        code = str(out["market"]["value"]).strip().lower()[:2]
        out["market_code"] = {"value": code if code in LC_MARKETS else "en", "source": out["market"]["source"],
                              "confirmed": out["market"]["confirmed"]}
    return out


LC_MARKETS = ("zh", "en", "ru", "ko", "ja", "es", "pt", "ar", "fr", "de", "id", "hi", "it", "tr", "vi", "th", "pl", "nl")


def fill(template, facts, lang="zh"):
    """模板填事实;返回 (文本, 用到的事实槽, 缺的槽)。"""
    used, missing = [], []
    i = 0 if lang == "zh" else 1

    def rep(m):
        slot = m.group(1)
        if slot in facts:
            if slot in FACT_SLOTS and slot not in used:
                used.append(slot)
            return str(facts[slot]["value"])
        if slot in FACT_SLOTS and slot not in missing:
            missing.append(slot)
        return FALLBACK.get(slot, (slot, slot))[i]
    return re.sub(r"\{(\w+)\}", rep, template or ""), used, missing


# ---------------------------------------------------------------------------
# 打法库
# ---------------------------------------------------------------------------

def load_playbooks(ws=None):
    pb = read_json(PLAYBOOKS)
    if not pb:
        raise UsageError("读不到打法库 %s" % PLAYBOOKS)
    plays = {p["id"]: dict(p, origin="builtin") for p in pb["plays"]}
    user = read_json(os.path.join(ws, "playbook", "plays.json")) if ws else None
    if isinstance(user, dict):
        for p in user.get("plays") or []:
            if isinstance(p, dict) and p.get("id") and p.get("stages"):
                plays[p["id"]] = dict(plays.get(p["id"], {}), **p, origin="user")
    h = hashlib.sha256(json.dumps(pb, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
    return pb, list(plays.values()), h


def profile_evidence(prof):
    ans = _answers(prof)
    ev = {}
    comp = str((ans.get("compliance") or ("", 0))[0])
    ev["profile.compliance_no_naming"] = bool(re.search(r"不能点名|不点名|不提竞品|不能提|不写竞品|no naming|not name|don't name", comp, re.I))
    ev["profile.event_new_product_line"] = "new_product_line" in (prof.get("events") or [])
    f = _fact(prof, "site.replaces_old_site")
    ev["profile.replaces_old_site"] = bool(f and str(f.get("value")).lower() in ("true", "1", "是", "yes"))
    return ev


def _conds(conds, ev):
    return [(c, LC.check(c, ev)) for c in conds or []]


def deny_match(play, deny):
    """→ ("drop", item) 整条命中 / ("note", [items]) 沾边 / None。"""
    text = " ".join([play.get("title", ""), play.get("title_en", ""), " ".join(play.get("tags") or [])]).lower()
    tags = [t.lower() for t in play.get("tags") or []]
    notes = []
    for d in deny or []:
        item = str(d.get("item") if isinstance(d, dict) else d).strip()
        il = item.lower()
        if not il:
            continue
        if il in tags or il in text:
            return ("drop", item)
        if any(t in il for t in tags if len(t) >= 2):
            notes.append(item)
    return ("note", notes) if notes else None


def weak_order(diag, stage):
    rules = LC.load_rules()
    pri = (rules.get("dim_priority_by_stage") or {}).get(str(stage)) or list(LC.DIMS)
    mat = diag.get("maturity") or {}
    return sorted(pri, key=lambda d: ((mat.get(d) or {}).get("level", 0), pri.index(d)))


def select(plays, stage, ev, deny, weak):
    cand, skipped = [], {"done": [], "vetoed": [], "denied": [], "not_applicable": []}
    for p in plays:
        if stage not in (p.get("stages") or []):
            continue
        only = _conds(p.get("only_if"), ev)
        if only and not all(r is True for _, r in only):
            skipped["not_applicable"].append({"id": p["id"], "title": p["title"]})
            continue
        done = _conds(p.get("done_if"), ev)
        if done and all(r is True for _, r in done):
            skipped["done"].append({"id": p["id"], "title": p["title"],
                                    "why": ",".join("%s=%s" % (c["key"], ev.get(c["key"])) for c, _ in done)})
            continue
        vet = [(c, r) for c, r in _conds(p.get("veto"), ev) if r is True]
        if vet:
            skipped["vetoed"].append({"id": p["id"], "title": p["title"], "why": vet[0][0].get("why") or vet[0][0]["key"]})
            continue
        dm = deny_match(p, deny)
        if dm and dm[0] == "drop":
            skipped["denied"].append({"id": p["id"], "title": p["title"], "why": "禁用清单:%s" % dm[1]})
            continue
        score = float((p.get("base_by_stage") or {}).get(str(stage), p.get("base", 1)))
        bonus = 0
        for d in p.get("dims") or []:
            if weak and d == weak[0]:
                bonus = max(bonus, 2)
            elif len(weak) > 1 and d == weak[1]:
                bonus = max(bonus, 1)
        score += bonus
        forced = any(r is True for _, r in _conds(p.get("force_first_if"), ev))
        if forced:
            score += 100
        cand.append(dict(p, score=score, dim_bonus=bonus, forced=forced, deny_notes=dm[1] if dm else []))
    cand.sort(key=lambda p: (-p["score"], p.get("week", 1), p["id"]))
    return cand, skipped


def schedule(cand):
    end, starts, out, backlog = {}, {}, [], []
    ids = {p["id"] for p in cand}
    for p in cand:
        s = int(p.get("week", 1))
        for dep in p.get("after") or []:
            if dep in end:
                s = max(s, end[dep] + 1)
            elif dep in ids:
                s = max(s, s)  # 依赖排在后面:按自己的 week,不硬等
        while starts.get(s, 0) >= MAX_STARTS_PER_WEEK and s <= WEEKS:
            s += 1
        if s > WEEKS:
            backlog.append(dict(p, start=None, end=None))
            continue
        e = min(WEEKS, s + max(1, int(p.get("weeks", 1))) - 1)
        starts[s] = starts.get(s, 0) + 1
        end[p["id"]] = e
        out.append(dict(p, start=s, end=e))
    return out, backlog


def recommendation(p, facts, rank):
    title, u1, m1 = fill(p["title"], facts)
    do, u2, m2 = fill(p["do"], facts)
    metric, u3, _ = fill(p.get("metric", ""), facts)
    title_en, _, _ = fill(p.get("title_en", p["title"]), facts, "en")
    do_en, _, _ = fill(p.get("do_en", p["do"]), facts, "en")
    cmd, _, _ = fill(p.get("cmd", ""), facts)
    used = list(dict.fromkeys(u1 + u2 + u3))
    missing = [m for m in dict.fromkeys(m1 + m2) if m not in used]
    return {"rank": rank, "id": p["id"], "origin": p.get("origin", "builtin"), "theme": p["theme"],
            "title": title, "title_en": title_en, "do": do, "do_en": do_en,
            "page_types": p.get("page_types") or [], "metric": metric, "measure": p.get("measure", ""),
            "weeks": [p["start"], p["end"]] if p.get("start") else None, "score": p["score"], "forced": p["forced"],
            "dims": p.get("dims") or [], "dim_bonus": p["dim_bonus"],
            "facts_used": [{"slot": s, "value": facts[s]["value"], "source": facts[s]["source"],
                            "confirmed": facts[s]["confirmed"]} for s in used],
            "facts_missing": missing, "deny_notes": p.get("deny_notes") or [], "ref": p.get("ref", ""), "cmd": cmd}


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def build(ws, metrics=None, top=10, today=None):
    prof = read_json(os.path.join(ws, "context", "profile.json"))
    if not prof:
        raise GateError("还没有开局档案:先跑 onboard.py start")
    if (prof.get("rings") or {}).get("1", {}).get("status") != "confirmed":
        raise GateError("开局第 1 环还没确认,不出方案(onboard.py show --ring 1)")
    scan = read_json(os.path.join(ws, "context", "scan.json"))
    diag = LC.diagnose(scan, ws, metrics, today)
    st = prof.get("stage") or {}
    stage = st.get("value") if st.get("confirmed") and st.get("value") is not None else diag["stage"]["stage"]
    if stage is None:
        raise GateError("产品阶段未知,先在开局第 1 环让用户确认阶段(onboard.py answer --ring 1 --correct stage=N)")
    stage = int(stage)
    ev, _ = LC.collect_evidence(scan, ws, metrics, today)
    ev.update(profile_evidence(prof))
    pb, plays, pb_hash = load_playbooks(ws)
    weak = weak_order(diag, stage)
    cand, skipped = select(plays, stage, ev, prof.get("deny") or [], weak)
    sched, backlog = schedule(cand)
    sched.sort(key=lambda p: (-p["score"], p["start"], p["id"]))
    facts = product_facts(prof)
    recs = [recommendation(p, facts, i + 1) for i, p in enumerate(sched)]
    themes = {}
    for r in recs[:top]:
        themes.setdefault(r["theme"], []).append(r["score"])
    top_themes = sorted(themes, key=lambda t: (-sum(themes[t]), -max(themes[t])))[:3]
    stage_info = next((s for s in LC.load_rules(ws)["stages"] if s["id"] == stage), {})
    unconfirmed = [f["key"] for f in prof.get("facts") or [] if f.get("status") == "unconfirmed"]
    skipped_rings = [r for r, v in (prof.get("rings") or {}).items() if v.get("status") == "skipped"]
    plan = {"schema": 1, "generated_at": (today or dt.date.today()).isoformat(),
            "profile_version": prof.get("version"), "playbooks_sha": pb_hash,
            "site": prof.get("site"), "stage": {"id": stage, "name": stage_info.get("name"),
                                                 "confirmed": bool(st.get("confirmed")), "rule": diag["stage"]["stage"]},
            "maturity": {d: {"level": v["level"], "status": v["status"]} for d, v in (diag.get("maturity") or {}).items()},
            "weakest": weak[:2], "facts": facts,
            "strategies": [{"theme": t, "name": pb["themes"][t]["name"], "name_en": pb["themes"][t]["name_en"],
                            "plays": [r["id"] for r in recs[:top] if r["theme"] == t]} for t in top_themes],
            "recommendations": recs[:top], "more": recs[top:],
            "backlog": [{"id": p["id"], "title": p["title"]} for p in backlog], "skipped": skipped,
            "deny": [d.get("item") if isinstance(d, dict) else d for d in prof.get("deny") or []],
            "assumptions": {"unconfirmed_facts": unconfirmed, "skipped_rings": skipped_rings,
                            "missing_slots": sorted({m for r in recs[:top] for m in r["facts_missing"]})},
            "metrics_by_stage": pb["metrics_by_stage"].get(str(stage), []),
            "status": "draft"}
    return plan


DIM_NAMES = {"technical": ("技术", "Technical"), "content": ("内容", "Content"), "authority": ("外链与品牌", "Authority"),
             "geo": ("AI 可见度", "AI visibility"), "measurement": ("团队与测量", "Measurement")}
STAGE_EN = {0: "Idea / prototype", 1: "Pre-launch", 2: "Just launched", 3: "Growth", 4: "Mature", 5: "Change / migration"}


def _wk(r, lang="zh"):
    if not r["weeks"]:
        return "—"
    a, b = r["weeks"]
    if lang == "zh":
        return "第 %d 周" % a if a == b else "第 %d–%d 周" % (a, b)
    return "Week %d" % a if a == b else "Weeks %d-%d" % (a, b)


def by_week(recs):
    return sorted(recs, key=lambda r: ((r["weeks"] or [99])[0], r["rank"]))


def render_roadmap(plan):
    L = ["# 90 天路线(%s,%s)" % (plan.get("site") or "", plan["stage"]["name"]), "",
         "按开始周排;# 是优先级(1 最先)。", "", "| # | 周 | 做什么 | 动哪类页面 | 预期动哪个数 | 怎么量 | 用到的产品事实 |", "|---|---|---|---|---|---|---|"]
    for r in by_week(plan["recommendations"]):
        L.append("| %d | %s | **%s**:%s | %s | %s | %s | %s |" % (
            r["rank"], _wk(r), r["title"], r["do"] + ("(不含:%s)" % "、".join(r["deny_notes"]) if r["deny_notes"] else ""),
            "、".join(r["page_types"]), r["metric"], r["measure"],
            "、".join("%s=%s%s" % (f["slot"], f["value"], "" if f["confirmed"] else "(未确认)") for f in r["facts_used"]) or "—"))
    return "\n".join(L) + "\n"


def render_book(plan, lang="zh"):
    zh = lang == "zh"
    f = plan["facts"]
    g = lambda k: (f.get(k) or {}).get("value") or FALLBACK[k][0 if zh else 1]  # noqa: E731
    st = plan["stage"]
    L = []
    if zh:
        L += ["# %s 的 SEO / GEO 战略书" % g("product"), "",
              "> 生成于 %s,依据开局档案第 %s 版和打法库 %s。这是草稿:开局第 6 环由你确认后才算定稿。" % (
                  plan["generated_at"], plan["profile_version"], plan["playbooks_sha"]), "",
              "## 1. 产品", "",
              "- 产品线:%s;最先做:%s" % (g("lines"), g("main_line")),
              "- 主要客户:%s" % g("customers"), "- SEO 要带来的结果:%s" % g("conversion"),
              "- 主要竞品:%s;主市场:%s" % (g("competitor"), g("market")), "",
              "## 2. 现在在哪", "",
              "- 产品阶段:**%s**%s" % (st["name"], "(你已确认)" if st["confirmed"] else "(按规则判,待确认)"),
              "- 成熟度:" + ";".join("%s %s 级%s" % (DIM_NAMES[d][0], v["level"], "" if v["status"] == "ok" else "(证据不全)")
                                     for d, v in plan["maturity"].items()),
              "- 最该补的一格:" + "、".join(DIM_NAMES[d][0] for d in plan["weakest"]), "",
              "## 3. 三条策略", ""]
    else:
        L += ["# SEO / GEO strategy for %s" % g("product"), "",
              "> Generated %s from onboarding profile v%s and playbook %s. Draft until you approve it in onboarding ring 6." % (
                  plan["generated_at"], plan["profile_version"], plan["playbooks_sha"]), "",
              "## 1. Product", "",
              "- Product lines: %s; first: %s" % (g("lines"), g("main_line")),
              "- Customers: %s" % g("customers"), "- What SEO should drive: %s" % g("conversion"),
              "- Main competitor: %s; primary market: %s" % (g("competitor"), g("market")), "",
              "## 2. Where it stands", "",
              "- Stage: **%s**%s" % (STAGE_EN.get(st["id"], st["name"]), " (confirmed)" if st["confirmed"] else " (rule-based, to confirm)"),
              "- Maturity: " + "; ".join("%s L%s%s" % (DIM_NAMES[d][1], v["level"], "" if v["status"] == "ok" else " (partial evidence)")
                                         for d, v in plan["maturity"].items()),
              "- Weakest area: " + ", ".join(DIM_NAMES[d][1] for d in plan["weakest"]), "",
              "## 3. Three strategies", ""]
    recs = {r["id"]: r for r in plan["recommendations"]}
    for i, s in enumerate(plan["strategies"], 1):
        L.append("%d. **%s**:%s" % (i, s["name"] if zh else s["name_en"],
                                     ("、" if zh else ", ").join((recs[p]["title"] if zh else recs[p]["title_en"]) for p in s["plays"])))
    L += ["", "## 4. 90 天路线" if zh else "## 4. 90-day roadmap", ""]
    L += (["| # | 周 | 做什么 | 页面 | 看哪个数 | 怎么量 |"] if zh else ["| # | When | Action | Pages | Metric | How to measure |"])
    L.append("|---|---|---|---|---|---|")
    for r in by_week(plan["recommendations"]):
        note = ""
        if r["deny_notes"]:
            note = ("(不含:%s)" if zh else " (excluding: %s)") % ("、".join(r["deny_notes"]))
        L.append("| %d | %s | **%s**:%s%s | %s | %s | %s |" % (
            r["rank"], _wk(r, lang), r["title"] if zh else r["title_en"], r["do"] if zh else r["do_en"], note,
            "、".join(r["page_types"]), r["metric"], r["measure"]))
    L += ["", "## 5. 这个阶段看哪些数" if zh else "## 5. Metrics for this stage", ""]
    L += ["- %s:%s" % (a, b) for a, b in plan["metrics_by_stage"]]
    sk = plan["skipped"]
    L += ["", "## 6. 不做什么,为什么" if zh else "## 6. What we are not doing, and why", ""]
    if plan["deny"]:
        L.append(("- 你说过不做:" if zh else "- You ruled out: ") + "、".join(plan["deny"]))
    for k, label in (("denied", "禁用清单去掉"), ("vetoed", "本轮出局"), ("done", "已经做完")):
        for x in sk[k]:
            L.append("- %s:%s(%s)" % (label, x["title"], x["why"]))
    if plan["more"]:
        L.append(("- 排在前 %d 条之后:" if zh else "- Ranked after the top %d: ") % len(plan["recommendations"]) +
                 "、".join(r["title"] for r in plan["more"]))
    a = plan["assumptions"]
    L += ["", "## 7. 还没确认的假设" if zh else "## 7. Unconfirmed assumptions", ""]
    if a["skipped_rings"]:
        L.append(("- 跳过的开局环:第 %s 环,用的是猜测" if zh else "- Skipped onboarding rings: %s (guesses used)") % "、".join(a["skipped_rings"]))
    if a["unconfirmed_facts"]:
        L.append(("- 没确认的事实:" if zh else "- Unconfirmed facts: ") + "、".join(a["unconfirmed_facts"][:12]))
    if a["missing_slots"]:
        L.append(("- 档案里缺、方案里用了通用说法的:" if zh else "- Missing in the profile (generic wording used): ") + "、".join(a["missing_slots"]))
    if not any(a.values()):
        L.append("- 无" if zh else "- None")
    L += ["", "## 8. 怎么跟进" if zh else "## 8. Follow-up", "",
          "- 每周运营单:硬告警 > 本周路线项 > 只做这一件(`project.py ops weekly`)" if zh else
          "- Weekly ops sheet: hard alerts > this week's roadmap item > the single pick (`project.py ops weekly`)",
          "- 每月核一次档案,每季度重看竞品和策略;产品变了回到对应那一环" if zh else
          "- Review the profile monthly and competitors and strategy quarterly; when the product changes, revisit that ring"]
    return "\n".join(L) + "\n"


def cmd_build(ns):
    ws = ns.ws
    metrics = read_json(ns.metrics) if ns.metrics else None
    plan = build(ws, metrics, ns.top)
    d = os.path.join(ws, "plan")
    old = read_json(os.path.join(d, "plan.json"))
    if old and old.get("status") == "approved":
        plan["previous_approved"] = {"generated_at": old.get("generated_at"), "approved_quote": old.get("approved_quote")}
    write_text(os.path.join(d, "plan.json"), json.dumps(plan, ensure_ascii=False, indent=1))
    write_text(os.path.join(d, "roadmap.md"), render_roadmap(plan))
    write_text(os.path.join(d, "strategy-book.zh.md"), render_book(plan, "zh"))
    write_text(os.path.join(d, "strategy-book.en.md"), render_book(plan, "en"))
    if ns.json:
        print(json.dumps(plan, ensure_ascii=False, indent=1))
    else:
        print(render_roadmap(plan))
        print("写了:%s/{plan.json,roadmap.md,strategy-book.zh.md,strategy-book.en.md}" % d)
        print("下一步:把三条策略和路线发给用户(开局第 6 环),停下等确认。")
    return 0


def cmd_show(ns):
    plan = read_json(os.path.join(ns.ws, "plan", "plan.json"))
    if not plan:
        raise UsageError("还没有方案:先 plan.py build")
    print(render_roadmap(plan))
    print("状态:%s" % plan.get("status"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="按产品阶段出方案、90 天路线和战略书")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--ws", default="seo-ops")
    b.add_argument("--metrics")
    b.add_argument("--top", type=int, default=10)
    b.add_argument("--json", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("--ws", default="seo-ops")
    ns = ap.parse_args(argv)
    try:
        return {"build": cmd_build, "show": cmd_show}[ns.cmd](ns)
    except GateError as e:
        print("停:%s" % e, file=sys.stderr)
        return 3
    except (UsageError, LC.UsageError) as e:
        print("错误:%s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
