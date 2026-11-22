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
import re
import shlex
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lifecycle as LC  # noqa: E402
import playbook as PB  # noqa: E402

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


PERIOD_FILE_RE = re.compile(r"Pages_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.csv")
EXPORT_FILE_RE = re.compile(r"(Pages_\d{4}-\d{2}-\d{2}_\d{4}-\d{2}-\d{2}\.csv|gsc-pages\.csv)")
BACKFILL_TAG = "逐日回填"


def data_end_from_source(source):
    """来源写的是 Pages_起_止.csv(GSC 网页导出)时,指标的截止日就是第一个文件名里的「止」;认不出 → None。"""
    m = PERIOD_FILE_RE.search(str(source or ""))
    return m.group(2) if m else None


def append_metrics(ws, metrics, source, at=None):
    """指标按数据截止日记:--at 没给时,从来源里的 Pages_起_止.csv 取截止日,取不到才用今天。"""
    row = {"at": at or data_end_from_source(source) or dt.date.today().isoformat(), "metrics": metrics, "source": source}
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
    tamper = LC.check_seal(prof)
    if tamper and not tamper.get("legacy"):
        raise GateError(LC.tamper_message(tamper) + "。先跑 onboard.py status(会把受影响的环退回待确认)")
    for msg in LC.normalize_profile(prof):
        print("注意: 档案不合格:%s" % msg, file=sys.stderr)
    plan = read_json(os.path.join(ws, "plan", "plan.json"))
    return prof, plan


def save_profile(ws, prof):
    write_json(os.path.join(ws, "context", "profile.json"), LC.seal_profile(LC.profile_format(prof)))


def onboarding_done(prof):
    rings = prof.get("rings") or {}
    return all((rings.get(str(r)) or {}).get("status") in ("confirmed", "skipped") for r in range(1, 7))


def profile_checked_at(prof):
    """档案最后一次被用户核过的日期:profile_confirmed_at(旧档案叫 reviewed_at),否则各环确认日。"""
    cands = [day(prof.get("profile_confirmed_at")), day(prof.get("reviewed_at"))]
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
    recs = plan.get("items") if isinstance(plan.get("items"), list) else (plan.get("recommendations") or [])
    items = []
    for i, r in enumerate(x for x in recs if isinstance(x, dict)):
        w = LC.norm_weeks(r.get("weeks"))
        if w and w[0] <= wk <= w[1]:
            items.append(dict(r, weeks=list(w), rank=r.get("rank") if isinstance(r.get("rank"), int) else 1000 + i))
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
    if nf and nf.get("value") not in (None, "", []):
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


url_section = LC.url_section
section_counts = LC.section_counts


def section_baseline(ws):
    """开局时(或用户上次确认产品变化时)的一级栏目。→ ({栏目: 页数}, 出处);都没有 → (None, None)。
    顺序:context/site_sections.json(用户确认过的)> scan.json 的 site_scan.sections > 开局体检存的 history/*/urls.txt(最新一份)。"""
    got = read_json(os.path.join(ws, "context", "site_sections.json"))
    if isinstance(got, dict) and isinstance(got.get("sections"), dict):
        return got["sections"], "context/site_sections.json(%s)" % got.get("at", "?")
    sc = ((read_json(os.path.join(ws, "context", "scan.json")) or {}).get("site_scan") or {}).get("sections")
    if isinstance(sc, dict) and sc:
        return sc, "开局读站点时的栏目(context/scan.json)"
    hist = os.path.join(ws, "history")
    runs = sorted(d for d in os.listdir(hist) if os.path.isfile(os.path.join(hist, d, "urls.txt"))) if os.path.isdir(hist) else []
    if runs:
        with open(os.path.join(hist, runs[-1], "urls.txt"), encoding="utf-8") as f:
            urls = [x.strip() for x in f if x.strip()]
        if urls:
            return section_counts(urls), "开局体检的 URL 清单(history/%s/urls.txt)" % runs[-1]
    return None, None


def diff_sections(base, sections, base_src):
    """这周 sitemap 里新出现的一级栏目:基线里没有,且现在 ≥2 页或进了首页导航。"""
    cur = sections.get("current") or {}
    nav = set(sections.get("nav") or [])
    titles = sections.get("titles") or {}
    out = []
    for sec in sorted(cur):
        if sec in base or not (cur[sec] >= 2 or sec in nav):
            continue
        title = titles.get(sec)
        ev = "%d 页%s%s" % (cur[sec], ",在首页导航里" if sec in nav else "", (",标题「%s」" % title) if title else "")
        out.append({"key": "site.sections", "kind": "new_section", "old": sorted(base), "new": [sec],
                    "source": "这周 sitemap 对比 %s" % base_src, "evidence": ev,
                    "question": "站点多了一个栏目 /%s/(%s;开局时没有):这是新的产品线或新业务吗?卖给谁,和现有客户一样吗?" % (sec, ev),
                    "options": ["是新产品线(说一下叫什么、卖给谁)", "不是,只是普通页面,不用管"]})
    return out


def effective_at(row):
    """一条指标记录的数据截止日:window_end > 来源里 Pages_起_止.csv 的「止」> at。"""
    return day(row.get("window_end")) or day(data_end_from_source(row.get("source"))) or day(row.get("at"))


def _source_gone(ws, prof, row):
    """来源点名了 data/ 下的导出文件、而那个文件已经不在了(被新导出换掉)→ True:这条记录作废。"""
    m = EXPORT_FILE_RE.search(str(row.get("source") or ""))
    if not m or BACKFILL_TAG in str(row.get("source") or ""):
        return False
    dirs = LC.gsc_dirs(ws, prof)
    return bool(dirs) and not any(os.path.isfile(os.path.join(d, m.group(1))) for d in dirs)


def backfill_history(ws, prof, record=True, min_days=None):
    """指标历史 + 逐日 gsc-pages.csv 每周一个检查点(近 28 天点击、展示、上一期点击)。
    - 逐日导出盖到的日期,以导出现算的检查点为准:同一天的旧回填行换成新算的,别的来源截止日落在导出范围里的行作废;
    - 来源点名的导出文件已经不在的行作废;
    - 按数据截止日排序(不是写入日),旧导出记成今天的行不会排到最后把新数盖掉。
    record=True 时把新算出的、窗口盖满 28 天的检查点追加进 metrics_history.jsonl(不满 28 天的只参与这次判断,不落盘)。
    min_days:给了就让不满 28 天、但有 ≥min_days 天数据的检查点也参与(标 partial_days)。→ 按截止日排好的历史。"""
    hist = [h for h in read_jsonl(history_path(ws)) if not _source_gone(ws, prof, h)]
    path, rows = LC.find_daily_pages(ws, prof)
    if not rows:
        return sorted(hist, key=lambda h: effective_at(h) or dt.date.min)
    first, last = min(r[0] for r in rows), max(r[0] for r in rows)
    pts = [dict(pt, source="%s %s" % (os.path.basename(path), BACKFILL_TAG))
           for pt in LC.weekly_checkpoints(rows, min_days=min_days)]
    fresh = {pt["at"] for pt in pts}
    stored = {str(h.get("at"))[:10] for h in hist}
    if record:
        for pt in pts:
            if pt["at"] not in stored and "partial_days" not in pt:
                append_jsonl(history_path(ws), {k: v for k, v in pt.items() if k in ("at", "metrics", "source")})
    kept = []
    for h in hist:
        e = effective_at(h)
        if BACKFILL_TAG in str(h.get("source") or "") and str(h.get("at"))[:10] in fresh:
            continue                                   # 同一天以现算的为准
        if BACKFILL_TAG not in str(h.get("source") or "") and e and first <= e <= last:
            continue                                   # 截止日落在逐日导出范围里:导出更全,以导出为准
        kept.append(h)
    return sorted(kept + pts, key=lambda h: effective_at(h) or dt.date.min)


def _judge_point(rules, scan, prof, row, last):
    """一次指标记录判阶段。→ (阶段 或 None(判不了), 备注)。
    - 不满 28 天的窗口(partial_days):合计已经超过「刚上线」的展示上限 → 照常判(下界已超);没超 → 判不了,不算「没超」;
    - 超过上限全靠一两天(去掉展示最多的两天就不到上限)→ 一次性冲高,按去掉那两天的数判。"""
    th = rules["stage_thresholds"]["low_impressions_28d"]
    m = dict(row.get("metrics") or {})
    impr = m.get("gsc_impressions_28d")
    note = ""
    top2 = row.get("top2_impressions")
    if impr is not None and top2 is not None and impr >= th and impr - top2 < th:
        m["gsc_impressions_28d"] = impr - top2
        note = "冲高"
        if row.get("partial_days"):
            return None, note
    elif row.get("partial_days") and (impr is None or impr < th):
        return None, "不满 28 天、没过上限"
    ev, _ = LC.collect_evidence(scan, None, m, last)
    return LC.stage(rules, ev, {"events": prof.get("events") or []})["stage"], note


def stage_trend(ws, prof, loop, record=True):
    """最近 N 次指标记录逐次重判阶段;都判成同一个、和已确认阶段不同、跨度够长 → 返回目标阶段。
    逐日导出不满 28 天的窗口也算一次记录(至少 7 天数据),规则见 _judge_point;有判不了的就不提示。"""
    p = (loop.get("params") or {})
    n, span = int(p.get("points", 4)), int(p.get("min_span_days", 21))
    hist = backfill_history(ws, prof, record, min_days=int(p.get("partial_min_days", 7)))
    if len(hist) < n:
        return None, "指标记录 %d 次,不到 %d 次" % (len(hist), n)
    pts = hist[-n:]
    first, last = effective_at(pts[0]), effective_at(pts[-1])
    if not first or not last or (last - first).days < span:
        return None, "最近 %d 次指标跨度不到 %d 天" % (n, span)
    scan = read_json(os.path.join(ws, "context", "scan.json"))
    rules = LC.load_rules(ws)
    judged = [_judge_point(rules, scan, prof, row, last) for row in pts]
    stages = [j[0] for j in judged]
    cur = (prof.get("stage") or {}).get("value")
    partial = sum(1 for r in pts if r.get("partial_days"))
    spikes = sum(1 for j in judged if j[1] == "冲高")
    extra = []
    if partial:
        extra.append("其中 %d 次窗口不满 28 天(合计已过上限的按下界算,没过的判不了)" % partial)
    if spikes:
        extra.append("%d 次超过上限只靠一两天的冲高,按去掉那两天的数算" % spikes)
    tail = (";" + ",".join(extra)) if extra else ""
    if None in stages:
        return None, "最近 %d 次指标里 %d 次判不了%s;档案 %s,不提示换阶段" % (n, stages.count(None), tail, cur)
    if len(set(stages)) == 1 and stages[0] != cur:
        return stages[0], "最近 %d 次指标(%s~%s)按规则都判成阶段 %s,档案里是 %s%s" % (n, first, last, stages[0], cur, tail)
    return None, "最近 %d 次指标判出的阶段:%s(档案 %s)%s" % (n, stages, cur, tail)


# ---------------------------------------------------------------------------
# 求值
# ---------------------------------------------------------------------------

def _recent_asks(ws):
    out = {}
    for row in read_jsonl(os.path.join(ws, "ledger", "loops.jsonl")):
        if row.get("result") in ("ask", "resolved"):
            out[(row["loop"], row.get("fp"))] = row
    return out


def evaluate(ws, today=None, new_scan=None, record=True, sections=None):
    """sections:运营单轻检拿到的这一周的一级栏目({"current": {栏目: 页数}, "nav": [...], "titles": {...}});
    给了就拿它和开局时的栏目基线比(新栏目 → 产品变了循环问),不用重新读整站。"""
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
        qs = [q if isinstance(q, dict) else {"text": q} for q in qs]
        if status == "ask":
            prev = asks.get((lid, fingerprint))
            again = int(loop.get("ask_again_days", 30))
            if prev and prev.get("result") == "resolved":
                r.update(status="quiet", why=why + ";用户已经答过(%s)" % prev.get("at"))
            elif prev and day(prev.get("at")) and (today - day(prev["at"])).days < again:
                r.update(status="waiting", why=why + ";%s 已经问过,等用户回复,%d 天内不重复问" % (prev["at"], again),
                         asked_at=prev.get("at"), asked=prev.get("questions") or [q["text"] for q in qs])
            else:
                r["questions"] = [q["text"] for q in qs][:int(loop.get("max_questions", 3)) or 0]
        results.append(r)
        if record:
            row = {"at": today.isoformat(), "loop": lid, "result": r["status"], "fp": fingerprint, "why": r["why"]}
            if r["questions"]:
                row["questions"] = r["questions"]
            append_jsonl(os.path.join(ws, "ledger", "loops.jsonl"), row)
        byt = {q["text"]: q for q in qs}
        questions.extend({"loop": lid, "text": t, "options": (byt.get(t) or {}).get("options") or []}
                         for t in r["questions"])

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
                qs = [{"text": "档案 %s 以后没核过(%s 天)。下面这些有没有变:产品线、定价、主要客户、主转化?都没变回「都没变」就行。" % (chk, age),
                       "options": ["都没变", "有变化(说是哪一条、现在是什么)"]}]
            if unconfirmed:
                qs.append({"text": "还有 %d 条没确认的事实(%s),要现在确认吗?" % (len(unconfirmed), "、".join(unconfirmed[:5])),
                           "options": ["现在确认", "先不管"]})
            if qs:
                emit(lp, "ask", "档案超过 %d 天没核" % lp["trigger"]["cadence_days"], qs, fp(lp["id"], str(chk), [c["key"] for c in changes]))
            else:
                emit(lp, "quiet", "档案超过 %d 天没核,重新读了站点,没有变化" % lp["trigger"]["cadence_days"])
                if record:
                    prof["profile_confirmed_at"] = today.isoformat()
                    save_profile(ws, prof)

    # product-change:给了新扫描 → 比产品线、定价、页面类型;运营单给了这一周的一级栏目 → 和开局时的栏目基线比
    lp = loops.get("product-change")
    sec_changes = []
    if lp:
        sec_note = ""
        if sections is not None:
            base, base_src = section_baseline(ws)
            if base is None:
                sec_note = "没有开局时的栏目基线(旧工作区);这周的 %d 个一级栏目已存成基线,下周起能比" % len(sections.get("current") or {})
                if record:
                    write_json(os.path.join(ws, "context", "site_sections.json"),
                               {"at": today.isoformat(), "sections": sections.get("current") or {}, "source": "运营单轻检(首次存基线)"})
            else:
                sec_changes = diff_sections(base, sections, base_src)
                if sec_changes and record:
                    write_json(os.path.join(ws, "context", "sections-new.json"),
                               {"at": today.isoformat(), "sections": sections.get("current") or {}, "source": "运营单轻检"})
        allc = changes + sec_changes
        if new_scan is None and sections is None:
            emit(lp, "skip", "这次没有重新读站点(加 --rescan 或 --scan)")
        elif allc:
            emit(lp, "ask", "%s发现 %d 处变化" % ("重新读站点" if new_scan else "sitemap 一级栏目和基线比", len(allc)),
                 [{"text": c["question"], "options": c.get("options") or []} for c in allc],
                 fp(lp["id"], [(c["key"], c["new"]) for c in allc]), {"changes": allc})
        elif new_scan is None and sec_note:
            emit(lp, "skip", sec_note)
        elif new_scan is None:
            emit(lp, "quiet", "sitemap 一级栏目和基线(%s)比,没有新栏目" % base_src)
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
                     [{"text": "方案定稿满 %d 天了。我用这一季的数据重跑了 plan.py(见 plan/plan.json 的新草稿),路线要不要按新数据改?" % age,
                       "options": ["按新数据改", "不改,照原路线"]},
                      {"text": "这一季竞品有没有变化?有新的对手或不用管的站吗?", "options": ["没变", "有(说是谁)"]}], fp(lp["id"], q))

    # stage-threshold
    lp = loops.get("stage-threshold")
    if lp:
        to, why = stage_trend(ws, prof, lp, record)
        if to is None:
            emit(lp, "quiet", why)
        else:
            names = {s["id"]: s["name"] for s in LC.load_rules(ws)["stages"]}
            emit(lp, "ask", why, [{"text": "看起来进入「%s」了(%s)。要按「%s」换打法、重排路线吗?" % (names.get(to, to), why, names.get(to, to)),
                                   "options": ["换(按「%s」重排路线)" % names.get(to, to), "先不换,按现在的路线做"]}],
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
                     [{"text": "要改版(%s)了:改动前我先存一份基线(site_move.py baseline),可以吗?" % "、".join(ev),
                       "options": ["可以", "先不用"]}], fp(lp["id"], ev))
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
    return {"date": today.isoformat(), "loops": results, "questions": picked[:3], "changes": changes + sec_changes}


def status(ws, today=None):
    today = today or dt.date.today()
    prof, plan = load_state(ws)
    diag = read_json(os.path.join(ws, "context", "diagnosis.json")) or {}
    st = prof.get("stage") or {}
    names = {s["id"]: s["name"] for s in LC.load_rules(ws)["stages"]}
    wk, items = roadmap_this_week(plan, today)
    deny = PB.load_deny(ws, prof)
    items, _ = PB.apply_deny(items, deny, lambda r: "%s %s" % (r.get("title", ""), r.get("do", "")))
    chk = profile_checked_at(prof)
    return {"date": today.isoformat(), "ws": ws, "site": prof.get("site"), "profile_version": prof.get("version"),
            "profile_checked_at": chk.isoformat() if chk else None, "onboarding_done": onboarding_done(prof),
            "stage": {"id": st.get("value"), "name": names.get(st.get("value")), "confirmed": st.get("confirmed")},
            "weakest": [d for d in (diag.get("weakest") or [])][:2] if isinstance(diag.get("weakest"), list) else None,
            "plan": {"status": (plan or {}).get("status"), "approved_at": (plan or {}).get("approved_at"), "week": wk,
                     "this_week": [{"rank": r["rank"], "title": r.get("title") or r.get("id") or "—", "weeks": r["weeks"]}
                                   for r in items]},
            "deny": [d["item"] for d in deny]}


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
            L += [question_line(i, q) for i, q in enumerate(ev["questions"], 1)]
            L += ["", "停:等用户回复,再用 loops.py resolve 记下(要带用户原话 --quote)。"]
        ag = agent_lines(s.get("ws"), ev) if s.get("ws") else []
        if ag:
            L += [""] + ag
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


def is_loopback_site(site):
    h = (urllib.parse.urlsplit(site if "://" in str(site) else "http://%s" % site).hostname or "").lower()
    return h in ("localhost", "::1") or h.endswith(".localhost") or h.startswith("127.")


def allow_local(ws):
    """开局时带过 --allow-local(本机预览站)→ True。project.yaml 里有 allow_local: true 就算;
    旧工作区没记这一项时,看开局读站点的结果:本机站点读到了(site_live)说明开局就是带着 --allow-local 跑的。"""
    try:
        with open(os.path.join(ws, "project.yaml"), encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^allow_local:\s*(\S+)", line)
                if m:
                    return m.group(1).strip("'\"").lower() in ("true", "yes", "1")
    except OSError:
        pass
    scan = read_json(os.path.join(ws, "context", "scan.json")) or {}
    return bool((scan.get("signals") or {}).get("site_live")) and is_loopback_site(scan.get("site") or "")


def resolve_hint(loop_id):
    return {"profile-review": "都没变就只带 --quote;有变的加 --set <键>=<新值>(列表加一项用 --add <键>=<新项>)",
            "product-change": "是新产品线:加 --add product.lines=<产品线名>;不是:只带 --quote",
            "stage-threshold": "确认换阶段:加 --stage <阶段号>;不换:只带 --quote",
            "quarterly-review": "路线要改的,记完再 plan.py build --replan 出新草稿",
            "site-move": "同意存基线就只带 --quote,再跑 site_move.py baseline"}.get(loop_id, "")


def resolve_cmd(ws, loop_id):
    """用户答完循环问题后照抄的那条命令(--quote 里换成用户原话)。"""
    return "python3 %s resolve --ws %s %s --quote \"<用户原话>\"" % (
        shlex.quote(os.path.abspath(__file__)), shlex.quote(os.path.abspath(ws)), loop_id)


def question_line(i, q):
    opts = q.get("options") or []
    return "%d. %s%s" % (i, q["text"], ("　" + "　".join("%s. %s" % (chr(65 + k), o) for k, o in enumerate(opts))) if opts else "")


def agent_lines(ws, ev):
    """给 agent 的落档说明:每个要问的问题照抄哪条 resolve;上次问过、没记下回答的怎么补记。"""
    L = []
    qs = (ev or {}).get("questions") or []
    if qs:
        L.append("- 用户回答后先落档,再接着做(把 <用户原话> 换成用户这次回话的原文;一个问题一条):")
        for i, q in enumerate(qs, 1):
            h = resolve_hint(q["loop"])
            L.append("  %d. %s%s" % (i, resolve_cmd(ws, q["loop"]), ("  # " + h) if h else ""))
    for r in (ev or {}).get("loops") or []:
        if r["status"] == "waiting":
            asked = ";".join(r.get("asked") or []) or r["why"]
            L.append("- %s 问过「%s」,台账里没有记下回答:用户已经答了(包括「都没变」「carry on」)→ 照抄 %s%s;"
                     "还没答 → 不重复问,先做这周的事。" % (r.get("asked_at") or "之前", asked[:200], resolve_cmd(ws, r["id"]),
                                               ("(%s)" % resolve_hint(r["id"])) if resolve_hint(r["id"]) else ""))
    return L


def rescan(ws):
    prof, _ = load_state(ws)
    site = prof.get("site")
    if not site:
        raise UsageError("档案里没有 site,用 --scan 给一份新的 product_scan 输出")
    out = os.path.join(ws, "context", "scan-new.json")
    cmd = [sys.executable, os.path.join(HERE, "product_scan.py"), "--site", site, "--out", out]
    if is_loopback_site(site) and allow_local(ws):
        cmd.append("--allow-local")
    r = subprocess.run(cmd, capture_output=True, text=True)
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
    for kv in ns.add or []:
        if "=" not in kv:
            raise UsageError("--add 要写成 key=value(往列表里加一项,如 product.lines=批发)")
        k, v = kv.split("=", 1)
        if k not in LC.PROFILE_LIST_KEYS:
            raise UsageError("--add 只用于列表键:%s" % "、".join(LC.PROFILE_LIST_KEYS))
        have = _fact_value(prof, k)
        have = list(have) if isinstance(have, list) else [x.strip() for x in str(have or "").replace("、", ",").split(",") if x.strip()]
        new_items = [x.strip() for x in v.replace("、", ",").split(",") if x.strip() and x.strip().lower() not in _as_set(have)]
        ns.set = list(ns.set or []) + ["%s=%s" % (k, ",".join(have + new_items))]
    for kv in ns.set or []:
        if "=" not in kv:
            raise UsageError("--set 要写成 key=value")
        k, v = kv.split("=", 1)
        val = [x.strip() for x in v.replace("、", ",").split(",") if x.strip()] if k in LC.PROFILE_LIST_KEYS else v
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
        prof["profile_confirmed_at"] = today.isoformat()
        new = os.path.join(ws, "context", "scan-new.json")
        if os.path.isfile(new):
            os.replace(new, os.path.join(ws, "context", "scan.json"))
        new = os.path.join(ws, "context", "sections-new.json")
        if os.path.isfile(new):                     # 用户答过新栏目:这周的栏目成为新基线,同一个栏目不再问
            os.replace(new, os.path.join(ws, "context", "site_sections.json"))
    if ns.loop == "product-change" and "product.lines" in changed and "new_product_line" not in (prof.get("events") or []):
        prof.setdefault("events", []).append("new_product_line")
    prof["version"] = int(prof.get("version") or 0) + 1
    prof.setdefault("changelog", []).append({"version": prof["version"], "at": today.isoformat(),
                                             "change": "循环 %s:用户确认%s" % (ns.loop, (",改了 " + "、".join(changed)) if changed else "")})
    save_profile(ws, prof)
    append_jsonl(os.path.join(ws, "ledger", "loops.jsonl"),
                 {"at": today.isoformat(), "loop": ns.loop, "result": "resolved", "fp": fpr, "quote": ns.quote, "changed": changed})
    nxt = ""
    if "stage" in changed or ns.loop == "quarterly-review":
        nxt = "下一步:plan.py build --replan 重排路线,发给用户确认(开局第 6 环)。"
    elif "product.lines" in changed:
        nxt = ("产品线记进档案了。这周照原路线做,不用为它再停下;要把新产品线排进路线,季度复盘或用户提出时再跑 "
               "plan.py build --replan。")
    print("记下了:%s%s。%s" % (ns.loop, (",改了 " + "、".join(changed)) if changed else "", nxt))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="开局之后的长期循环")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("status", "run", "resolve"):
        s = sub.add_parser(name)
        s.add_argument("--ws", help="seo-ops 工作区(默认 ./seo-ops)")
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
            s.add_argument("--add", action="append", help="往列表键里加一项,不用整份重写(如 product.lines=批发)")
            s.add_argument("--stage", type=int)
    ns = ap.parse_args(argv)
    try:
        ns.ws = LC.resolve_ws(ns.ws, __file__, list(sys.argv[1:] if argv is None else argv))
        return {"status": cmd_status, "run": cmd_run, "resolve": cmd_resolve}[ns.cmd](ns)
    except GateError as e:
        print("停:%s" % e, file=sys.stderr)
        return 3
    except (UsageError, LC.UsageError) as e:
        print("错误:%s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
