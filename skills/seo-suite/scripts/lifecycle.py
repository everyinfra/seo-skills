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
import shlex
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
RULES_PATH = os.path.join(SKILL_ROOT, "data", "lifecycle.json")
DIMS = ("technical", "content", "authority", "geo", "measurement")
OPS_DIR = "seo-ops"


class UsageError(Exception):
    pass


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


# ---------------------------------------------------------------------------
# 工作区定位(onboard / plan / loops / project / site_move / teach 共用)
# ---------------------------------------------------------------------------

def inside_skill(path):
    """path 落在 seo-suite 安装目录(scripts/ 的上一级)里面 → True。工作区不许建在这里。"""
    root = os.path.realpath(SKILL_ROOT)
    p = os.path.realpath(os.path.abspath(path))
    return p == root or p.startswith(root + os.sep)


def drop_ws_args(argv, names=("--ws", "--dir")):
    """命令行里去掉 --ws / --dir 和它的值(给出改过的照抄命令用)。"""
    out, skip = [], False
    for a in argv or []:
        if skip:
            skip = False
            continue
        if a in names:
            skip = True
            continue
        if any(a.startswith(n + "=") for n in names):
            continue
        out.append(a)
    return out


def shell_cmd(script, argv):
    return "python3 " + " ".join(shlex.quote(x) for x in [os.path.abspath(script)] + list(argv))


def find_ws_up(start=None):
    """从 start(默认当前目录)往上找开过局的 seo-ops/(只用来给提示,不改变用哪个工作区)。"""
    cur = os.path.abspath(start or os.getcwd())
    home = os.path.expanduser("~")
    while True:
        cand = os.path.join(cur, OPS_DIR)
        if not inside_skill(cand) and (os.path.isfile(os.path.join(cand, "context", "profile.json"))
                                       or os.path.isfile(os.path.join(cand, "project.yaml"))):
            return cand
        parent = os.path.dirname(cur)
        if parent == cur or cur == home:
            return None
        cur = parent


def ws_fix_hint(script, argv, flag="--ws", repo=None):
    """两条照抄就能跑的命令:cd 到站点仓库再跑,或者加 --ws <站点仓库>/seo-ops。"""
    base = drop_ws_args(argv)
    r = repo or "<站点仓库>"
    cmd = shell_cmd(script, base)
    head = "照抄其一%s:" % ("" if repo else "(<站点仓库> 换成站点仓库的绝对路径)")
    return "%s\n  cd %s && %s\n  %s %s %s" % (head, shlex.quote(r) if repo else r, cmd, cmd, flag,
                                           shlex.quote(os.path.join(r, OPS_DIR)) if repo else r + "/" + OPS_DIR)


def host_key(url):
    """比较两个站点地址是不是同一个站用:主机名(小写、去 www.)+ 显式端口;协议不比。"""
    u = str(url or "").strip()
    p = urllib.parse.urlsplit(u if "://" in u else "http://" + u)
    host = (p.hostname or "").lower().rstrip(".")
    host = host[4:] if host.startswith("www.") else host
    try:
        port = p.port
    except ValueError:
        port = None
    return host, port


def same_site(a, b):
    return bool(a and b) and host_key(a) == host_key(b)


def resolve_ws(explicit, script, argv, flag="--ws", must_exist=True, repo=None):
    """→ 工作区绝对路径:explicit 给了用它,否则 ./seo-ops。
    落在 skill 安装目录里 → UsageError(调用方这时还什么都没写);must_exist 而目录不在 → UsageError,
    说清当前目录没有工作区、怎么指过去(不悄悄新建空工作区)。"""
    ws = os.path.abspath(explicit or OPS_DIR)
    if inside_skill(ws):
        stray = read_json(os.path.join(ws, "context", "profile.json"), {}) or {}
        known = repo or (stray.get("repo") if not inside_skill(stray.get("repo") or SKILL_ROOT) else None)
        extra = ""
        if stray and known and not os.path.exists(os.path.join(known, OPS_DIR)):
            extra = "\nskill 目录里已经有一份建错地方的工作区,先挪回站点仓库:mv %s %s" % (
                shlex.quote(ws), shlex.quote(os.path.join(known, OPS_DIR)))
        raise UsageError("工作区 %s 落在 seo-suite 自己的安装目录(%s)里,这次什么都没写。工作区要放在站点仓库里"
                         "(当前目录是 %s)。%s%s" % (ws, SKILL_ROOT, os.getcwd(),
                                                ws_fix_hint(script, argv, flag, known), extra))
    if must_exist and not os.path.isdir(ws):
        if explicit:
            raise UsageError("%s 指的工作区 %s 不存在(没新建)。还没开局先跑 onboard.py start --site <URL> --repo <站点仓库>;"
                             "开过局就把 %s 改成 <站点仓库>/seo-ops" % (flag, ws, flag))
        up = find_ws_up()
        hint = ("上级目录里有工作区:照抄 %s %s %s" % (shell_cmd(script, drop_ws_args(argv)), flag, shlex.quote(up))
                if up else ws_fix_hint(script, argv, flag, repo))
        raise UsageError("当前目录 %s 下没有工作区 seo-ops/(没新建)。%s" % (os.getcwd(), hint))
    return ws


# 档案的读取契约:别的工具(评测、其他 skill)按 _schema 找每个核心事实。事实存在 facts 列表里
# ({"key", "value", "status", ...}),_schema 的值是段列表,{"key": K} 表示「列表里 key 等于 K 的第一项」,
# 取到的对象再取 .value。阶段编号在 stage.value,另写一份 stage.id。
PROFILE_FACT_KEYS = ("product.name", "product.one_liner", "product.lines", "pricing.model",
                     "conversion.primary", "customers", "market.languages")
PROFILE_LIST_KEYS = ("product.lines", "customers", "market.languages")


def profile_format(prof):
    """写 profile.json 之前调:补 _schema 映射和 stage.id(和 stage.value 同值)。原地改,返回同一个对象。"""
    st = prof.get("stage")
    if isinstance(st, dict):
        if st.get("value") is not None:
            st["id"] = st["value"]
        else:
            st.pop("id", None)
    schema = {k: ["facts", {"key": k}] for k in PROFILE_FACT_KEYS}
    schema["stage"] = "stage.id"
    prof["_schema"] = schema
    return prof


def candidate_names(cands, names=None):
    """阶段候选 → 名字列表;候选可以是 {"id","name"},也可以是旧版写的阶段编号。"""
    if names is None:
        try:
            names = {s["id"]: s["name"] for s in load_rules()["stages"]}
        except UsageError:
            names = {}
    out = []
    for c in cands or []:
        if isinstance(c, dict):
            out.append(str(c.get("name") or names.get(c.get("id"), c.get("id"))))
        else:
            out.append(str(names.get(c, c)))
    return out


# ---------------------------------------------------------------------------
# 档案的形状与校验值(onboard / loops / plan 共用)
# ---------------------------------------------------------------------------

BANK_PATH = os.path.join(os.path.dirname(HERE), "data", "onboarding.json")
RING_KEYS = {"status": "pending", "answers": {}, "quotes": [], "asked_at": None, "confirmed_at": None}
RING_STATUSES = ("pending", "asking", "confirmed", "skipped")


def ring_prefixes():
    b = read_json(BANK_PATH, {}) or {}
    return {int(r["ring"]): tuple(r.get("fact_prefixes") or ()) for r in b.get("rings") or []}


def fact_ring(f, prefixes=None):
    """事实属于哪一环:写了 ring 就用它,否则按键前缀。"""
    r = f.get("ring") if isinstance(f, dict) else None
    if r is not None:
        try:
            return int(r)
        except (TypeError, ValueError):
            return None
    key = str((f or {}).get("key") or "")
    for ring, pre in (prefixes or ring_prefixes()).items():
        if pre and key.startswith(pre):
            return ring
    return None


def normalize_profile(prof):
    """手写或旧版档案缺键时补默认值(原地改);→ 补了什么的说明列表,空列表 = 合格。"""
    problems = []
    if not isinstance(prof, dict):
        raise UsageError("profile.json 顶层不是对象")
    rings = prof.get("rings")
    if isinstance(rings, list):
        conv = {}
        for i, r in enumerate(rings, 1):
            if isinstance(r, dict):
                conv[str(r.get("ring") or i)] = r
        rings = prof["rings"] = conv
        problems.append("rings 是列表,已按环号转成对象")
    if not isinstance(rings, dict):
        prof["rings"] = rings = {}
        problems.append("缺 rings(6 环状态),已按「都没开始」补上")
    for r in range(1, 7):
        cur = rings.get(str(r))
        if not isinstance(cur, dict):
            if str(r) in rings or rings:
                problems.append("rings 缺第 %d 环,已按「没开始」补上" % r)
            rings[str(r)] = cur = {}
        for k, v in RING_KEYS.items():
            if k not in cur or (k in ("answers", "quotes") and not isinstance(cur[k], type(v))):
                cur[k] = json.loads(json.dumps(v))
        if cur["status"] not in RING_STATUSES:
            problems.append("第 %d 环状态 %r 不认识,已改成「没开始」" % (r, cur["status"]))
            cur["status"] = "pending"
    st = prof.get("stage")
    if isinstance(st, (int, float)) and not isinstance(st, bool):
        prof["stage"] = {"value": int(st), "confirmed": False, "source": "手写档案"}
        problems.append("stage 是一个数字,已改成 {value: %d},待用户确认" % int(st))
    elif not isinstance(st, dict):
        prof["stage"] = {}
        problems.append("缺 stage(产品阶段),已按「未知」补上")
    facts = prof.get("facts")
    if not isinstance(facts, list):
        prof["facts"] = []
        problems.append("缺 facts,已按空列表补上")
    else:
        prof["facts"] = [f for f in facts if isinstance(f, dict) and f.get("key")]
        if len(prof["facts"]) != len(facts):
            problems.append("facts 里有 %d 条不是 {key, value} 形状,已忽略" % (len(facts) - len(prof["facts"])))
        for f in prof["facts"]:
            f.setdefault("status", "unconfirmed")
    for k, v in (("events", []), ("deny", []), ("metrics", {}), ("changelog", []), ("existing_context", [])):
        if not isinstance(prof.get(k), type(v)):
            prof[k] = json.loads(json.dumps(v))
    return problems


def _digest(obj):
    import hashlib
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _ring_parts(prof, prefixes):
    parts = {str(r): {"ring": (prof.get("rings") or {}).get(str(r)), "facts": []} for r in range(1, 7)}
    for f in prof.get("facts") or []:
        r = fact_ring(f, prefixes)
        if r is not None and str(r) in parts:
            parts[str(r)]["facts"].append(f)
    parts["1"]["stage"] = {k: v for k, v in (prof.get("stage") or {}).items() if k != "id"}
    parts["5"]["deny"] = prof.get("deny")
    return parts


# 不进校验值的键:校验值本身;_schema 是脚本按固定规则生成的映射(每次写入都重写),读档案的人照它取值,
# 有人照着评测说明在顶层补一份 _schema 不算改了档案内容
UNSEALED = ("_integrity", "_schema")


def seal_profile(prof):
    """写 profile.json 前最后一步:记整份和每一环的内容校验值(档案只能经脚本写)。原地改,返回同一个对象。"""
    prefixes = ring_prefixes()
    body = {k: v for k, v in prof.items() if k not in UNSEALED}
    prof["_integrity"] = {"by": "seo-suite", "sha256": _digest(body),
                          "rings": {r: _digest(p) for r, p in _ring_parts(prof, prefixes).items()}}
    return prof


def check_seal(prof):
    """→ None(没被手改)/ {"legacy": True}(没有校验值:旧版或手写)/ {"rings": [被改动的环], "other": bool}。"""
    seal = prof.get("_integrity")
    if not isinstance(seal, dict) or not seal.get("sha256"):
        return {"legacy": True, "rings": [], "other": False}
    body = {k: v for k, v in prof.items() if k not in UNSEALED}
    if _digest(body) == seal["sha256"]:
        return None
    old = seal.get("rings") or {}
    now_ = {r: _digest(p) for r, p in _ring_parts(prof, ring_prefixes()).items()}
    changed = sorted((int(r) for r in now_ if old.get(r) != now_[r]))
    return {"legacy": False, "rings": changed, "other": not changed}


def tamper_message(t):
    if not t or t.get("legacy"):
        return None
    where = ("第 %s 环" % "、".join(map(str, t["rings"]))) if t["rings"] else "环以外的部分(指标、事件等)"
    return ("profile.json 被手改过(%s和脚本最后一次写入时的校验值对不上)。档案只能经 onboard.py 写:"
            "改内容用 answer --correct / note;受影响的环要把改后的内容给用户看、用户确认后再往下" % where)


def norm_weeks(w):
    """路线条目的周数 → (起, 止) 整数;认 [1, 2]、["1", "2"]、"1"、"1-2"、"1–2"、"Week 3"、"第 2–4 周"、3;认不出 → None。"""
    if w is None or isinstance(w, bool):
        return None
    if isinstance(w, (int, float)):
        return (int(w), int(w))
    if isinstance(w, (list, tuple)):
        nums = []
        for x in w[:2]:
            r = norm_weeks(x)
            if r:
                nums.append(r[0])
        if not nums:
            return None
        a, b = nums[0], nums[-1]
        return (min(a, b), max(a, b))
    import re as _re
    nums = [int(x) for x in _re.findall(r"\d+", str(w))[:2]]
    if not nums:
        return None
    return (min(nums[0], nums[-1]), max(nums[0], nums[-1]))


# ---------------------------------------------------------------------------
# GSC 逐页导出(gsc-pages.csv 逐日、或两期「网页」界面导出 Pages_起_止.csv)
# ---------------------------------------------------------------------------

def gsc_dirs(ws, prof=None):
    """工作区附近放 GSC 导出的目录:<ws>/data、<ws 所在目录>/data、档案里 repo 的 data/。"""
    cands = [os.path.join(ws, "data"), os.path.join(os.path.dirname(os.path.abspath(ws)), "data")]
    repo = (prof or {}).get("repo")
    if repo:
        cands.append(os.path.join(repo, "data"))
    out = []
    for d in cands:
        d = os.path.abspath(d)
        if os.path.isdir(d) and d not in out:
            out.append(d)
    return out


def _csv_rows(path):
    import csv
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except (OSError, csv.Error, UnicodeDecodeError):
        return []


def _num(v):
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def read_daily_pages(path):
    """gsc-pages.csv(page,date,clicks,impressions)→ [(date, page, clicks, impressions)];读不了 → []。"""
    out = []
    for r in _csv_rows(path):
        low = {str(k).strip().lower(): v for k, v in r.items() if k}
        try:
            d = dt.date.fromisoformat(str(low.get("date") or "")[:10])
        except ValueError:
            continue
        out.append((d, str(low.get("page") or low.get("url") or ""), _num(low.get("clicks")), _num(low.get("impressions"))))
    return out


def find_daily_pages(ws, prof=None):
    for d in gsc_dirs(ws, prof):
        p = os.path.join(d, "gsc-pages.csv")
        rows = read_daily_pages(p) if os.path.isfile(p) else []
        if rows:
            return p, rows
    return None, []


def weekly_checkpoints(rows, window=28):
    """逐日行 → 每周一个检查点(从最后一天往回每 7 天),每点算近 28 天点击、展示和上一期 28 天点击;
    28 天窗口没被数据盖满的点不出。→ [{"at", "metrics"}](按日期升序)。"""
    if not rows:
        return []
    by_day = {}
    for d, _p, c, i in rows:
        a = by_day.setdefault(d, [0.0, 0.0])
        a[0] += c
        a[1] += i
    first, last = min(by_day), max(by_day)

    def tot(lo, hi, k):
        return sum(v[k] for d, v in by_day.items() if lo <= d <= hi)
    pts, cp = [], last
    while cp - dt.timedelta(days=window - 1) >= first:
        lo = cp - dt.timedelta(days=window - 1)
        m = {"gsc_clicks_28d": int(tot(lo, cp, 0)), "gsc_impressions_28d": int(tot(lo, cp, 1))}
        plo = lo - dt.timedelta(days=window)
        if plo >= first:
            m["gsc_clicks_prev_28d"] = int(tot(plo, lo - dt.timedelta(days=1), 0))
        pts.append({"at": cp.isoformat(), "metrics": m})
        cp -= dt.timedelta(days=7)
    return pts[::-1]


def page_group(url):
    """按网址归页型:评测 review、对比 vs / alternatives、榜单 best-;其余取第一段路径(/blog/、/shop/)。"""
    import urllib.parse as _up
    path = _up.urlsplit(url).path if "://" in url else url
    segs = [s for s in path.lower().split("/") if s]
    for s in segs:
        toks = s.split("-")
        if "review" in toks or "reviews" in toks:
            return "review(评测页)"
        if "vs" in toks or "versus" in toks or "alternative" in toks or "alternatives" in toks:
            return "vs(对比页)"
        if toks[0] == "best":
            return "best-(榜单页)"
    return ("/%s/" % segs[0]) if segs else "/(首页)"


def _period_exports(ws, prof):
    """两期「网页」界面导出 Pages_起_止.csv → (前一期 {url: clicks}, 这一期 {url: clicks}, 两期日期);缺 → None。"""
    import re as _re
    for d in gsc_dirs(ws, prof):
        got = []
        for f in sorted(os.listdir(d)):
            m = _re.match(r"^Pages_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.csv$", f)
            if m:
                rows = {}
                for r in _csv_rows(os.path.join(d, f)):
                    low = {str(k).strip().lower(): v for k, v in r.items() if k}
                    url = low.get("top pages") or low.get("page") or low.get("url") or ""
                    if url:
                        rows[url] = rows.get(url, 0.0) + _num(low.get("clicks"))
                got.append(((m.group(1), m.group(2)), rows, os.path.join(d, f)))
        if len(got) >= 2:
            (pa, prev, pf), (ca, cur, cf) = got[-2], got[-1]
            return prev, cur, (pa, ca), (pf, cf)
    return None


def page_drop(ws, prof=None):
    """两期按页点击 → 掉量按页型拆;→ None(没有导出)或
    {"prev","cur","delta_pct","groups":[{"group","prev","cur","delta","share"}](掉得最多的在前),"source"}。"""
    got = _period_exports(ws, prof)
    if got:
        prev, cur, periods, files = got
        src = "%s → %s" % (os.path.basename(files[0]), os.path.basename(files[1]))
    else:
        path, rows = find_daily_pages(ws, prof)
        if not rows:
            return None
        last = max(r[0] for r in rows)
        lo, plo = last - dt.timedelta(days=27), last - dt.timedelta(days=55)
        if min(r[0] for r in rows) > plo:
            return None
        prev, cur = {}, {}
        for d, p, c, _i in rows:
            if lo <= d <= last:
                cur[p] = cur.get(p, 0.0) + c
            elif plo <= d < lo:
                prev[p] = prev.get(p, 0.0) + c
        src = "%s(%s 前后两个 28 天)" % (os.path.basename(path), last.isoformat())
    tp, tc = sum(prev.values()), sum(cur.values())
    if not tp:
        return None
    groups = {}
    for url in set(prev) | set(cur):
        g = groups.setdefault(page_group(url), [0.0, 0.0])
        g[0] += prev.get(url, 0.0)
        g[1] += cur.get(url, 0.0)
    loss = tp - tc
    rows_ = [{"group": k, "prev": int(a), "cur": int(b), "delta": int(b - a),
              "share": round((a - b) / loss, 3) if loss > 0 else 0.0} for k, (a, b) in groups.items()]
    rows_.sort(key=lambda x: (x["delta"], x["group"]))
    return {"prev": int(tp), "cur": int(tc), "delta_pct": round((tc - tp) / tp * 100, 1), "groups": rows_, "source": src}


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
        repo_scan = scan.get("repo_scan") or {}
        plans = repo_scan.get("migration_plans") if isinstance(repo_scan, dict) else None
        if plans:
            ev["signals.migration_plans"] = list(plans)
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
        why = ["没给站点地址,只读了仓库:" + ("有 %d 条公开路由" % routes if routes else "没有公开路由")
               + ";站点已经上线的话补 --site 重跑"]
        cands = [0, 1, 2]
        plans = ev.get("signals.migration_plans") or []
        if plans and not events:
            why.insert(0, "仓库里有改版 / 迁移计划:%s" % "、".join(plans[:3]))
            sid, cands = 5, [5, 1, 2, 3, 4]
        res = {"stage": sid, "name": names[sid], "base_stage": None, "base_name": None, "confidence": "guess",
               "why": why, "candidates": [{"id": c, "name": names[c]} for c in cands], "missing": ["signals.site_live"],
               "conflicts": []}
        return _confirmed_override(res, prof, names)
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
    plans = ev.get("signals.migration_plans") or []
    if events:
        sid = 5
        why.insert(0, "档案声明了改版类事件:%s" % ",".join(events))
    elif plans:
        # 仓库里摆着改版 / 迁移计划(MIGRATION.md 这类):按「改版 / 迁移」猜,底层阶段照常报;第 1 环让用户确认
        sid, conf = 5, "guess"
        why.insert(0, "仓库里有改版 / 迁移计划:%s" % "、".join(plans[:3]))
        cands = _dedup_ids([5, base] + list(cands))
    res = {"stage": sid, "name": names.get(sid), "base_stage": base, "base_name": names.get(base),
           "confidence": conf, "why": why, "candidates": [{"id": c, "name": names[c]} for c in cands],
           "missing": [] if (impr is not None or clicks is not None or not live) else ["metrics.gsc_impressions_28d", "metrics.gsc_clicks_28d", "metrics.gsc_clicks_prev_28d"],
           "conflicts": []}
    return _confirmed_override(res, prof, names)


def _confirmed_override(res, prof, names):
    """用户在第 1 环确认(或纠正)过的阶段压过规则;规则结果写进 conflicts,不覆盖用户的。"""
    confirmed = ((prof or {}).get("stage") or {})
    if confirmed.get("confirmed") and confirmed.get("value") is not None:
        cv = int(confirmed["value"])
        if cv != res["stage"]:
            res["conflicts"].append("用户确认的阶段是 %s,规则判的是 %s" % (names.get(cv), names.get(res["stage"])))
        res.update({"stage": cv, "name": names.get(cv), "confidence": "confirmed"})
    return res


def _dedup_ids(ids):
    out = []
    for i in ids:
        if i is not None and i not in out:
            out.append(i)
    return out


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
        L.append("候选:" + "、".join(candidate_names(st["candidates"])))
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
        if ns.ws:
            resolve_ws(ns.ws, __file__, sys.argv[1:] if argv is None else argv)
        d = diagnose(scan, ns.ws, metrics, today)
    except UsageError as e:
        print("错误: %s" % e, file=sys.stderr)
        return 2
    print(json.dumps(d, ensure_ascii=False, indent=1) if ns.json else render(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
