#!/usr/bin/env python3
"""loops.py — 开局做完以后跟着产品走:统一格式的长期循环(RQ-237 第 3 批;stdlib only)。

循环定义在 data/loops.json(触发、动手条件、自检、停止条件、去重、产出、回哪一环),用户在
seo-ops/playbook/loops.json 可以加或覆盖。大多数轮次的结论是「查了,没事」:只记账(ledger/loops.jsonl),
不打扰用户;要问时只问变了的部分,同一件事问过就在 ask_again_days 天内不再问。

内置循环:
  profile-review    档案超过 30 天没核 → 只列可能变了的条目,问 1–3 个问题
  quarterly-review  方案定稿满 90 天 → 用真实数据重跑 plan.py,和定稿方案比,问路线要不要改
  product-change    重新读站点(--scan / --rescan)后出现新产品线、定价变了、新页面类型 → 回第 1 环只问变了的
  stage-threshold   最近 4 次指标记录都判成同一个新阶段(跨度 ≥21 天)→ 提示换阶段,用户确认后重排路线
  site-move         档案里有改版类事件 → 提醒存基线、改后对比(site_move.py)
  weekly-ops        每周运营单本身(ops.py),这里只报到期

用法:
  python3 loops.py status --ws seo-ops                         # 第二次打开时的一屏:档案、阶段、方案第几周、本周路线项、到期循环
  python3 loops.py run --ws seo-ops [--scan new_scan.json | --rescan] [--today 2026-12-01] [--json]
  python3 loops.py resolve --ws seo-ops <循环 id> --quote "<用户原话>" [--set product.lines=a,b] [--stage N]
退出码:0 正常(没有要问的);1 有要问用户的问题;2 输入错;3 开局没做完。
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lifecycle as LC  # noqa: E402

LOOPS = os.path.join(os.path.dirname(HERE), "data", "loops.json")


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


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def read_jsonl(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except ValueError:
                        pass
    except OSError:
        pass
    return out


def append_jsonl(path, row):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def day(s):
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except (TypeError, ValueError):
        return None


def fp(*parts):
    return hashlib.sha1(json.dumps(parts, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def load_loops(ws=None):
    base = read_json(LOOPS)
    if not base:
        raise UsageError("读不到循环定义 %s" % LOOPS)
    loops = {x["id"]: x for x in base["loops"]}
    user = read_json(os.path.join(ws, "playbook", "loops.json")) if ws else None
    if isinstance(user, dict):
        for x in user.get("loops") or []:
            if isinstance(x, dict) and x.get("id"):
                loops[x["id"]] = dict(loops.get(x["id"], {}), **x, origin="user")
    return loops


# ---------------------------------------------------------------------------
# 指标历史(onboard.py metric 和 ops.py 每周都往里追加)
# ---------------------------------------------------------------------------

def history_path(ws):
    return os.path.join(ws, "context", "metrics_history.jsonl")


def append_metrics(ws, metrics, source, at=None):
    row = {"at": at or dt.date.today().isoformat(), "metrics": metrics, "source": source}
    hist = read_jsonl(history_path(ws))
    if hist and hist[-1].get("at") == row["at"] and hist[-1].get("metrics") == metrics:
        return
    append_jsonl(history_path(ws), row)


def metrics_from_external(ext):
    """外部数据包的 gsc_totals 逐日行 → 近两个 28 天的点击和展示。"""
    rows = (((ext or {}).get("sources") or {}).get("gsc_totals") or {}).get("rows") or []
    if not rows:
        return None
    last = day(rows[-1]["date"])
    if not last:
        return None

    def tot(a, b, k):
        lo, hi = last - dt.timedelta(days=a), last - dt.timedelta(days=b)
        return sum(float(r.get(k) or 0) for r in rows if lo <= (day(r["date"]) or lo - dt.timedelta(1)) <= hi)
    cur_days = sum(1 for r in rows if day(r["date"]) and day(r["date"]) > last - dt.timedelta(days=28))
    if cur_days < 28:
        return None
    m = {"gsc_clicks_28d": int(tot(27, 0, "clicks")), "gsc_impressions_28d": int(tot(27, 0, "impressions"))}
    prev_days = sum(1 for r in rows if day(r["date"]) and last - dt.timedelta(days=56) < day(r["date"]) <= last - dt.timedelta(days=28))
    if prev_days >= 28:
        m["gsc_clicks_prev_28d"] = int(tot(55, 28, "clicks"))
    return m, last.isoformat()


# ---------------------------------------------------------------------------
# 档案与方案
# ---------------------------------------------------------------------------

def load_state(ws):
    prof = read_json(os.path.join(ws, "context", "profile.json"))
    if not prof:
        raise GateError("还没有开局档案:先跑 onboard.py start")
    plan = read_json(os.path.join(ws, "plan", "plan.json"))
    return prof, plan


def onboarding_done(prof):
    rings = prof.get("rings") or {}
    return all((rings.get(str(r)) or {}).get("status") in ("confirmed", "skipped") for r in range(1, 7))


def profile_checked_at(prof):
    """档案最后一次被用户核过的日期:reviewed_at,否则第 1 环确认日。"""
    cands = [day(prof.get("reviewed_at"))]
    for r in (prof.get("rings") or {}).values():
        cands.append(day(r.get("confirmed_at")))
    cands = [c for c in cands if c]
    return max(cands) if cands else None


def plan_week(plan, today):
    if not plan or plan.get("status") != "approved":
        return None
    start = day(plan.get("approved_at"))
    if not start:
        return None
    return (today - start).days // 7 + 1


def roadmap_this_week(plan, today):
    wk = plan_week(plan, today)
    if not wk:
        return wk, []
    items = [r for r in plan.get("recommendations") or [] if r.get("weeks") and r["weeks"][0] <= wk <= r["weeks"][1]]
    items.sort(key=lambda r: r["rank"])
    return wk, items


# ---------------------------------------------------------------------------
# 变化检测
# ---------------------------------------------------------------------------

def _fact_value(prof, key):
    best = None
    for f in prof.get("facts") or []:
        if f.get("key") == key and (best is None or f.get("status") in ("confirmed", "corrected")):
            best = f
    return best.get("value") if best else None


def _as_set(v):
    if v is None:
        return set()
    if isinstance(v, (list, tuple)):
        return {str(x).strip().lower() for x in v if str(x).strip()}
    return {x.strip().lower() for x in str(v).replace("、", ",").split(",") if x.strip()}


def _scan_fact(scan, key):
    for f in (scan or {}).get("facts") or []:
        if f.get("key") == key:
            return f
    return None


def diff_scan(prof, old_scan, new_scan):
    """新读的站点 和 档案(已确认值优先)比:新产品线、定价变了、新页面类型。"""
    changes = []
    nf = _scan_fact(new_scan, "product.lines")
    if nf:
        have = _as_set(_fact_value(prof, "product.lines"))
        add = [x for x in (nf["value"] if isinstance(nf["value"], list) else [nf["value"]])
               if str(x).strip().lower() not in have]
        if have and add:
            changes.append({"key": "product.lines", "kind": "new_product_line", "old": sorted(have), "new": add,
                            "source": nf.get("source"),
                            "question": "站点上多了产品线「%s」:要加进档案吗?它卖给谁、转化算什么,和现有客户一样吗?" % "、".join(map(str, add))})
    nf = _scan_fact(new_scan, "pricing.prices")
    if nf:
        old = _as_set(_fact_value(prof, "pricing.prices"))
        new = _as_set(nf["value"])
        if old and new and old != new:
            changes.append({"key": "pricing.prices", "kind": "pricing_changed", "old": sorted(old), "new": sorted(new),
                            "source": nf.get("source"),
                            "question": "定价页变了(%s → %s):是改价了吗?目标客户或主转化要跟着改吗?" % (
                                "、".join(sorted(old)), "、".join(sorted(new)))})
    opt = ((old_scan or {}).get("site_scan") or {}).get("page_types") or {}
    npt = ((new_scan or {}).get("site_scan") or {}).get("page_types") or {}
    added = sorted(k for k, v in npt.items() if (v or 0) > 0 and not (opt.get(k) or 0) and k not in ("other",))
    if opt and added:
        changes.append({"key": "site.page_types", "kind": "new_page_type", "old": sorted(k for k, v in opt.items() if v),
                        "new": added, "source": "sitemap",
                        "question": "sitemap 里出现了新的页面类型「%s」:这是新产品线或新内容方向吗?" % "、".join(added)})
    return changes


def stage_trend(ws, prof, loop):
    """最近 N 次指标记录逐次重判阶段;都判成同一个、和已确认阶段不同、跨度够长 → 返回目标阶段。"""
    p = (loop.get("params") or {})
    n, span = int(p.get("points", 4)), int(p.get("min_span_days", 21))
    hist = read_jsonl(history_path(ws))
    if len(hist) < n:
        return None, "指标记录 %d 次,不到 %d 次" % (len(hist), n)
    pts = hist[-n:]
    first, last = day(pts[0]["at"]), day(pts[-1]["at"])
    if not first or not last or (last - first).days < span:
        return None, "最近 %d 次指标跨度不到 %d 天" % (n, span)
    scan = read_json(os.path.join(ws, "context", "scan.json"))
    rules = LC.load_rules(ws)
    stages = []
    for row in pts:
        ev, _ = LC.collect_evidence(scan, None, row.get("metrics") or {}, last)
        stages.append(LC.stage(rules, ev, {"events": prof.get("events") or []})["stage"])
    cur = (prof.get("stage") or {}).get("value")
    if len(set(stages)) == 1 and stages[0] is not None and stages[0] != cur:
        return stages[0], "最近 %d 次指标(%s~%s)按规则都判成阶段 %s,档案里是 %s" % (n, first, last, stages[0], cur)
    return None, "最近 %d 次指标判出的阶段:%s(档案 %s)" % (n, stages, cur)


# ---------------------------------------------------------------------------
# 求值
# ---------------------------------------------------------------------------

def _recent_asks(ws):
    out = {}
    for row in read_jsonl(os.path.join(ws, "ledger", "loops.jsonl")):
        if row.get("result") in ("ask", "resolved"):
            out[(row["loop"], row.get("fp"))] = row
    return out


def evaluate(ws, today=None, new_scan=None, record=True):
    today = today or dt.date.today()
    prof, plan = load_state(ws)
    loops = load_loops(ws)
    asks = _recent_asks(ws)
    results, questions = [], []

    def emit(loop, status, why, qs=(), fingerprint=None, extra=None):
        lid = loop["id"]
        r = {"id": lid, "name": loop.get("name", lid), "status": status, "why": why, "ring": loop.get("ring"),
             "questions": [], "fp": fingerprint}
        if extra:
            r.update(extra)
        if status == "ask":
            prev = asks.get((lid, fingerprint))
            again = int(loop.get("ask_again_days", 30))
            if prev and prev.get("result") == "resolved":
                r.update(status="quiet", why=why + ";用户已经答过(%s)" % prev.get("at"))
            elif prev and day(prev.get("at")) and (today - day(prev["at"])).days < again:
                r.update(status="waiting", why=why + ";%s 已经问过,等用户回复,%d 天内不重复问" % (prev["at"], again))
            else:
                r["questions"] = list(qs)[:int(loop.get("max_questions", 3)) or 0]
        results.append(r)
        if record:
            append_jsonl(os.path.join(ws, "ledger", "loops.jsonl"),
                         {"at": today.isoformat(), "loop": lid, "result": r["status"], "fp": fingerprint, "why": r["why"]})
        questions.extend({"loop": lid, "text": q} for q in r["questions"])

    # 开局没做完:循环都不跑,先接着开局
    if not onboarding_done(prof):
        raise GateError("开局还没做完(onboard.py status / show),循环不跑")

    # profile-review
    lp = loops.get("profile-review")
    old_scan = read_json(os.path.join(ws, "context", "scan.json"))
    changes = diff_scan(prof, old_scan, new_scan) if new_scan else []
    if lp:
        chk = profile_checked_at(prof)
        age = (today - chk).days if chk else None
        due = age is None or age >= int(lp["trigger"].get("cadence_days", 30))
        if not due:
            emit(lp, "quiet", "档案 %s 核过,%d 天,没到 %d 天" % (chk, age, lp["trigger"]["cadence_days"]))
        else:
            unconfirmed = [f["key"] for f in prof.get("facts") or [] if f.get("status") == "unconfirmed"]
            qs = []
            if changes:
                qs = [c["question"] for c in changes]
            elif new_scan is None:
                qs = ["档案 %s 以后没核过(%s 天)。下面这些有没有变:产品线、定价、主要客户、主转化?都没变回「都没变」就行。" % (chk, age)]
            if unconfirmed:
                qs.append("还有 %d 条没确认的事实(%s),要现在确认吗?" % (len(unconfirmed), "、".join(unconfirmed[:5])))
            if qs:
                emit(lp, "ask", "档案超过 %d 天没核" % lp["trigger"]["cadence_days"], qs, fp(lp["id"], str(chk), [c["key"] for c in changes]))
            else:
                emit(lp, "quiet", "档案超过 %d 天没核,重新读了站点,没有变化" % lp["trigger"]["cadence_days"])
                if record:
                    prof["reviewed_at"] = today.isoformat()
                    write_json(os.path.join(ws, "context", "profile.json"), prof)

    # product-change(只在给了新扫描时)
    lp = loops.get("product-change")
    if lp:
        if new_scan is None:
            emit(lp, "skip", "这次没有重新读站点(加 --rescan 或 --scan)")
        elif changes:
            emit(lp, "ask", "重新读站点发现 %d 处变化" % len(changes), [c["question"] for c in changes],
                 fp(lp["id"], [(c["key"], c["new"]) for c in changes]), {"changes": changes})
        else:
            emit(lp, "quiet", "重新读了站点,产品线、定价、页面类型都没变")

    # quarterly-review
    lp = loops.get("quarterly-review")
    if lp:
        ap = day((plan or {}).get("approved_at"))
        if not ap:
            emit(lp, "skip", "方案还没定稿")
        else:
            age = (today - ap).days
            n = int(lp["trigger"].get("cadence_days", 90))
            if age < n:
                emit(lp, "quiet", "方案 %s 定稿,%d 天,没到 %d 天" % (ap, age, n))
            else:
                q = int(age // n)
                emit(lp, "ask", "方案定稿 %d 天,到季度复盘" % age,
                     ["方案定稿满 %d 天了。我用这一季的数据重跑了 plan.py(见 plan/plan.json 的新草稿),路线要不要按新数据改?" % age,
                      "这一季竞品有没有变化(第 3 环)?有新的对手或不用管的站吗?"], fp(lp["id"], q))

    # stage-threshold
    lp = loops.get("stage-threshold")
    if lp:
        to, why = stage_trend(ws, prof, lp)
        if to is None:
            emit(lp, "quiet", why)
        else:
            names = {s["id"]: s["name"] for s in LC.load_rules(ws)["stages"]}
            emit(lp, "ask", why, ["看起来进入「%s」了(%s)。确认的话我换这个阶段的打法、重排路线。" % (names.get(to, to), why)],
                 fp(lp["id"], to), {"to_stage": to})

    # site-move
    lp = loops.get("site-move")
    if lp:
        ev = [e for e in prof.get("events") or [] if e in ("migration", "domain_change", "replatform", "url_restructure", "merge_sites")]
        if not ev:
            emit(lp, "quiet", "档案里没有改版类事件")
        else:
            base = sorted(f for f in os.listdir(os.path.join(ws, "baselines")) if f.endswith(".json")) \
                if os.path.isdir(os.path.join(ws, "baselines")) else []
            if not base:
                emit(lp, "ask", "档案里有改版事件(%s),还没存基线" % "、".join(ev),
                     ["要改版(%s)了:改动前我先存一份基线(site_move.py baseline),可以吗?" % "、".join(ev)], fp(lp["id"], ev))
            else:
                emit(lp, "due", "已有基线 %s;改完跑 site_move.py compare" % base[-1])

    # weekly-ops
    lp = loops.get("weekly-ops")
    if lp:
        runs = sorted(d for d in os.listdir(os.path.join(ws, "runs")) if day(d)) if os.path.isdir(os.path.join(ws, "runs")) else []
        last = day(runs[-1]) if runs else None
        if last and (today - last).days < int(lp["trigger"]["cadence_days"]):
            emit(lp, "quiet", "上次运营单 %s" % last)
        else:
            emit(lp, "due", "上次运营单 %s,到期" % (last or "没跑过"))

    # 合计最多 3 个问题:阶段门槛 > 产品变了 > 档案核对 > 季度 > 改版
    order = ["stage-threshold", "product-change", "profile-review", "quarterly-review", "site-move"]
    seen, picked = set(), []
    for q in sorted(questions, key=lambda q: order.index(q["loop"]) if q["loop"] in order else 99):
        if q["text"] not in seen:
            seen.add(q["text"])
            picked.append(q)
    return {"date": today.isoformat(), "loops": results, "questions": picked[:3], "changes": changes}


def status(ws, today=None):
    today = today or dt.date.today()
    prof, plan = load_state(ws)
    diag = read_json(os.path.join(ws, "context", "diagnosis.json")) or {}
    st = prof.get("stage") or {}
    names = {s["id"]: s["name"] for s in LC.load_rules(ws)["stages"]}
    wk, items = roadmap_this_week(plan, today)
    chk = profile_checked_at(prof)
    return {"date": today.isoformat(), "site": prof.get("site"), "profile_version": prof.get("version"),
            "profile_checked_at": chk.isoformat() if chk else None, "onboarding_done": onboarding_done(prof),
            "stage": {"id": st.get("value"), "name": names.get(st.get("value")), "confirmed": st.get("confirmed")},
            "weakest": [d for d in (diag.get("weakest") or [])][:2] if isinstance(diag.get("weakest"), list) else None,
            "plan": {"status": (plan or {}).get("status"), "approved_at": (plan or {}).get("approved_at"), "week": wk,
                     "this_week": [{"rank": r["rank"], "title": r["title"], "weeks": r["weeks"]} for r in items]},
            "deny": [d.get("item") if isinstance(d, dict) else d for d in prof.get("deny") or []]}


def render_status(s, ev=None):
    L = ["# %s · %s" % (s["site"] or "seo-ops", s["date"]), ""]
    L.append("- 档案:第 %s 版,上次和你核对是 %s" % (s["profile_version"], s["profile_checked_at"] or "—"))
    L.append("- 阶段:%s%s" % (s["stage"]["name"] or "未知", "(已确认)" if s["stage"]["confirmed"] else "(待确认)"))
    p = s["plan"]
    if p["status"] == "approved":
        L.append("- 方案:%s 定稿,现在是第 %s 周" % (p["approved_at"][:10], p["week"]))
        if p["this_week"]:
            L.append("- 本周路线项:" + ";".join("#%d %s" % (r["rank"], r["title"]) for r in p["this_week"]))
        else:
            L.append("- 本周没有路线项(%s)" % ("90 天路线已走完,到季度复盘" if (p["week"] or 0) > 13 else "按运营单推进"))
    else:
        L.append("- 方案:%s" % ("草稿,等你在开局第 6 环确认" if p["status"] == "draft" else "还没出(开局第 6 环跑 plan.py build)"))
    if s["deny"]:
        L.append("- 你说过不做:" + "、".join(s["deny"]))
    if ev:
        L += ["", "## 循环", ""]
        for r in ev["loops"]:
            mark = {"quiet": "查了,没事", "skip": "没查", "due": "到期", "ask": "要问你", "waiting": "等你回复"}.get(r["status"], r["status"])
            L.append("- %s:%s — %s" % (r["name"], mark, r["why"]))
        if ev["questions"]:
            L += ["", "## 要问你的(最多 3 个)", ""]
            L += ["%d. %s" % (i, q["text"]) for i, q in enumerate(ev["questions"], 1)]
            L += ["", "停:等用户回复,再用 loops.py resolve 记下(要带用户原话 --quote)。"]
    return "\n".join(L) + "\n"


def cmd_status(ns):
    s = status(ns.ws, day(ns.today))
    ev = None
    if s["onboarding_done"]:
        ev = evaluate(ns.ws, day(ns.today), None, record=False)
    if ns.json:
        print(json.dumps({"status": s, "loops": ev}, ensure_ascii=False, indent=1))
    else:
        print(render_status(s, ev))
    return 0


def rescan(ws):
    prof, _ = load_state(ws)
    site = prof.get("site")
    if not site:
        raise UsageError("档案里没有 site,用 --scan 给一份新的 product_scan 输出")
    out = os.path.join(ws, "context", "scan-new.json")
    r = subprocess.run([sys.executable, os.path.join(HERE, "product_scan.py"), "--site", site, "--out", out],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(out):
        raise UsageError("重新读站点失败:%s" % (r.stderr or r.stdout)[-300:])
    return read_json(out)


def cmd_run(ns):
    new_scan = None
    if ns.scan:
        new_scan = read_json(ns.scan)
        if new_scan is None:
            raise UsageError("读不到 %s" % ns.scan)
        write_json(os.path.join(ns.ws, "context", "scan-new.json"), new_scan)
    elif ns.rescan:
        new_scan = rescan(ns.ws)
    ev = evaluate(ns.ws, day(ns.today), new_scan)
    d = os.path.join(ns.ws, "runs", ev["date"])
    write_json(os.path.join(d, "loops.json"), ev)
    if ns.json:
        print(json.dumps(ev, ensure_ascii=False, indent=1))
    else:
        print(render_status(status(ns.ws, day(ns.today)), ev))
    return 1 if ev["questions"] else 0


def cmd_resolve(ns):
    if not (ns.quote or "").strip():
        raise GateError("必须用 --quote 带上用户原话")
    ws = ns.ws
    prof, _ = load_state(ws)
    today = day(ns.today) or dt.date.today()
    loops = load_loops(ws)
    if ns.loop not in loops:
        raise UsageError("没有循环 %s;有:%s" % (ns.loop, ", ".join(loops)))
    rows = [r for r in read_jsonl(os.path.join(ws, "ledger", "loops.jsonl")) if r["loop"] == ns.loop and r.get("result") == "ask"]
    fpr = rows[-1]["fp"] if rows else None
    changed = []
    for kv in ns.set or []:
        if "=" not in kv:
            raise UsageError("--set 要写成 key=value")
        k, v = kv.split("=", 1)
        val = [x.strip() for x in v.replace("、", ",").split(",") if x.strip()] if k == "product.lines" else v
        hit = False
        for f in prof.get("facts") or []:
            if f.get("key") == k:
                f.update({"value": val, "status": "corrected", "quote": ns.quote, "at": today.isoformat(), "source": "用户确认(%s)" % ns.loop})
                hit = True
        if not hit:
            prof.setdefault("facts", []).append({"key": k, "value": val, "status": "corrected", "quote": ns.quote,
                                                 "at": today.isoformat(), "source": "用户确认(%s)" % ns.loop, "kind": "fact"})
        changed.append(k)
    if ns.stage is not None:
        prof.setdefault("stage", {}).update({"value": int(ns.stage), "confirmed": True, "confirmed_at": today.isoformat()})
        changed.append("stage")
    if ns.loop in ("profile-review", "product-change"):
        prof["reviewed_at"] = today.isoformat()
        new = os.path.join(ws, "context", "scan-new.json")
        if os.path.isfile(new):
            os.replace(new, os.path.join(ws, "context", "scan.json"))
    if ns.loop == "product-change" and "product.lines" in changed and "new_product_line" not in (prof.get("events") or []):
        prof.setdefault("events", []).append("new_product_line")
    prof["version"] = int(prof.get("version") or 0) + 1
    prof.setdefault("changelog", []).append({"version": prof["version"], "at": today.isoformat(),
                                             "change": "循环 %s:用户确认%s" % (ns.loop, (",改了 " + "、".join(changed)) if changed else "")})
    write_json(os.path.join(ws, "context", "profile.json"), prof)
    append_jsonl(os.path.join(ws, "ledger", "loops.jsonl"),
                 {"at": today.isoformat(), "loop": ns.loop, "result": "resolved", "fp": fpr, "quote": ns.quote, "changed": changed})
    nxt = ""
    if "stage" in changed or ns.loop == "quarterly-review" or "product.lines" in changed:
        nxt = "下一步:plan.py build 重排路线,发给用户确认(开局第 6 环)。"
    print("记下了:%s%s。%s" % (ns.loop, (",改了 " + "、".join(changed)) if changed else "", nxt))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="开局之后的长期循环")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("status", "run", "resolve"):
        s = sub.add_parser(name)
        s.add_argument("--ws", default="seo-ops")
        s.add_argument("--today", help="YYYY-MM-DD(测试和回放用)")
        if name != "resolve":
            s.add_argument("--json", action="store_true")
        if name == "run":
            s.add_argument("--scan", help="新的 product_scan 输出")
            s.add_argument("--rescan", action="store_true", help="现在重新读站点(联网)")
        if name == "resolve":
            s.add_argument("loop")
            s.add_argument("--quote", required=True)
            s.add_argument("--set", action="append")
            s.add_argument("--stage", type=int)
    ns = ap.parse_args(argv)
    try:
        return {"status": cmd_status, "run": cmd_run, "resolve": cmd_resolve}[ns.cmd](ns)
    except GateError as e:
        print("停:%s" % e, file=sys.stderr)
        return 3
    except (UsageError, LC.UsageError) as e:
        print("错误:%s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
