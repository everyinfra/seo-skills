#!/usr/bin/env python3
"""外展状态库(outreach ticket tracker;R4-1;stdlib only)。
链路:citation_gaps.py --json 找到候选域 → add 建条目(priority/outreach_tip 原样
搬入)→ update 状态机推进 → due 复查日到期清单(cron 接 notify:退出码 1=有到期,
照 trend_watch R0-6 口径)→ report 转化漏斗与平均回复天数。

数据文件 outreach.json(默认当前目录,--file 可指定):{items:[...]},每项:
  {id:"OUT-001", domain, status:"candidate|drafted|sent|replied|linked|refused",
   priority:"High|Standard|…"("原样"来自 gaps 的 domains[].priority), outreach_tip
   ("原样"来自 gaps 的 outreach_tips[domain]), source(来源 gaps.json 路径或 "manual"),
   created, updated, next_review(复查日;candidate/linked/refused 为 null), url(产出
   链接,--url 记录), note, history:[{ts, from, to, note?}]}

状态机(跳级/回退/同态拒绝):candidate→drafted→sent→replied→linked;refused 仅
replied 可进(拒绝即回复);linked/refused 为终态,不可再转换。

复查日(REVIEW_DAYS,add/update 按 status 设/重设):
  drafted +14d(草稿太久该发)/ sent +7d(发出该催)/ replied +3d(回复该收链);
  candidate(未动手)/ linked·refused(终态)无复查日。

用法: python3 outreach_tracker.py <add|list|update|due|report> [选项]
退出码: 0 正常 / 1 due 有到期条目(cron 消费,接 notify) / 2 输入或参数错误。

并发口径(R5,照 remediation.py):save_data 原子写(tempfile + os.replace)+
数据文件级 flock(data_lock);add/update 的 load→改→save 全程持锁——两进程交替
写也不覆盖丢单。所有子命令支持 --json。"""
import contextlib
try:
    import fcntl
except ImportError:  # Windows 没有 fcntl,改用 msvcrt.locking 加同样的排他锁
    fcntl = None
    import msvcrt
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone

SCHEMA_VERSION = 1
DEFAULT_FILE = "outreach.json"
STATUSES = ("candidate", "drafted", "sent", "replied", "linked", "refused")
ACTIVE_STATUSES = ("candidate", "drafted", "sent", "replied")     # 非终态
TERMINAL_STATUSES = ("linked", "refused")                          # 终态
TRANSITIONS = {("candidate", "drafted"), ("drafted", "sent"),
               ("sent", "replied"), ("replied", "linked"),
               ("replied", "refused")}        # refused 仅 replied 可进(拒绝即回复)
REVIEW_DAYS = {"drafted": 14, "sent": 7, "replied": 3}             # 复查日偏移
REVIEW_ACTION = {"drafted": "该发了(草稿已压 %d 天)",
                 "sent": "该催了(发出 %d 天无下文)",
                 "replied": "该收链了(回复后 %d 天未落链)"}
FUNNEL_STAGES = ("candidate", "sent", "replied", "linked")
ID_RE = re.compile(r"^OUT-(\d+)$")

USAGE = """usage: outreach_tracker.py <add|list|update|due|report> [选项]
外展状态库:citation_gaps --json 的候选域 → add 条目(outreach.json)→ update 状态机
→ due 复查清单(退出码 1 接 notify)→ report 转化漏斗。

数据文件 outreach.json(默认当前目录,--file 可指定):{items:[{id:"OUT-001", domain,
  status, priority, outreach_tip, source, created, updated, next_review, url, note,
  history:[...]}]}
  status: candidate → drafted → sent → replied → linked;refused 仅 replied 可进;
          linked/refused 终态(跳级/回退/同态拒绝)
  next_review: drafted+14d / sent+7d / replied+3d(add·update 按新 status 重设;
               candidate 与终态为 null)

子命令:
  add --domain a.com [--source gaps.json] [--file F] [--json]
      登记候选域(与 citation_gaps 闭环):--source 为 citation_gaps.py --json 输出,
      从中取该域的 priority 与 outreach_tip 原样记入(source=该文件路径);无 --source
      时手工登记(priority=Standard,tip 空)。同域重复 → 退出码 2。
  list [--status X] [--due] [--file F] [--json]
      表格(id/domain/status/priority/next_review/url);到期行 next_review 后标 [!];
      --status 过滤;--due 只看到期。
  update OUT-001 --status drafted|sent|replied|linked|refused [--note "..."]
         [--url 产出链接] [--file F] [--json]
      状态机推进(逐级;跳级/回退/同态拒绝;终态不可再转);--note 覆写备注(并随
      history 留档);--url 记录产出链接;next_review 按新 status 重设。
  due [--file F] [--json]
      复查日到期清单("该跟进谁":按 status 给动作文案);有到期 → 退出码 1
      (cron 消费,照 trend_watch 口径接 notify)。
  report [--file F] [--json]
      转化漏斗:候选→发送→回复→获得链接逐级比率 + 平均回复天数(replied_ts-sent_ts
      均值,天,1 位小数;无样本 N/A)。

并发(R5,照 remediation.py):原子写 + flock;add/update 全程持锁。

退出码: 0 正常 / 1 due 有到期条目 / 2 输入或参数错误。"""


def die(msg, with_usage=False):
    sys.stderr.write(msg + ("\n" + USAGE if with_usage else "") + "\n")
    sys.exit(2)


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_dt(s):
    """ISO 时间戳 → aware datetime;无法解析 → None;naive 视作 UTC。"""
    if not isinstance(s, str) or not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def load_json_tolerant(path, what):
    """容错读 JSON(与 remediation/health_score 同法);读不了 → 退出码 2。"""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        die("读不了 %s: %s" % (what, e))
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    die("无法从 %s 解析出 JSON 对象: %s" % (what, path))


def check_item(it, where):
    """单条外展条目的最小结构校验;返回错误文案或 None。"""
    if not isinstance(it, dict):
        return "%s 不是对象" % where
    if not isinstance(it.get("id"), str) or not it["id"]:
        return "%s 缺 id 字符串" % where
    if not isinstance(it.get("domain"), str) or not it["domain"]:
        return "%s 缺 domain 字符串" % where
    if it.get("status") not in STATUSES:
        return "%s 的 status 非法(%r;合法值: %s)" % (where, it.get("status"),
                                                    "|".join(STATUSES))
    return None


def load_data(path, create=False):
    """读数据文件;create=True 且不存在 → 空库(供 add 首建);结构不符 → 退出码 2。"""
    if not os.path.exists(path):
        if create:
            return {"items": []}
        die("数据文件不存在: %s(先运行 add 登记候选域)" % path)
    data = load_json_tolerant(path, "数据文件(--file)")
    items = data.get("items")
    if not isinstance(items, list):
        die("数据文件格式不符: 缺 items 列表(%s)" % path)
    for n, it in enumerate(items, 1):
        err = check_item(it, "items[%d]" % n)
        if err:
            die("数据文件格式不符: %s(%s)" % (err, path))
    return data


def save_data(path, data):
    """原子写(tempfile + os.replace,照 remediation.py;中断/并发不落半截文件)。"""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".tmp-", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


@contextlib.contextmanager
def data_lock(path, timeout=120.0):
    """数据文件级 flock(照 remediation.py data_lock);超时 → 警告并跳过本次写。"""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    lock_path = os.path.join(d, "." + os.path.basename(path) + ".lock")
    fh = open(lock_path, "w")
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                if fcntl:
                    fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise SystemExit(
                        "警告: 另一 outreach_tracker 进程持有 %s 超过 %.0fs,"
                        "跳过本次写(防并发覆盖丢失)" % (lock_path, timeout))
                time.sleep(0.5)
        yield
    finally:
        try:
            if fcntl:
                fcntl.flock(fh, fcntl.LOCK_UN)
            else:
                try:
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:  # 等锁超时、没拿到锁时解锁会报错;close 也会释放锁
                    pass
        finally:
            fh.close()


def next_id(items):
    """顺延编号:现有最大 OUT-<N> 的 N+1,零填充三位。"""
    mx = 0
    for it in items:
        m = ID_RE.match(str(it.get("id", "")))
        if m:
            mx = max(mx, int(m.group(1)))
    return "OUT-%03d" % (mx + 1)


def sort_key(it):
    m = ID_RE.match(str(it.get("id", "")))
    return (0, int(m.group(1)), "") if m else (1, 0, str(it.get("id", "")))


def norm_domain(d):
    """域名归一:小写去空白(照 citation_gaps 的域名口径,已是可注册域)。"""
    return (d or "").strip().lower()


def next_review_for(status, ts):
    """按 status 设复查日(REVIEW_DAYS);candidate/终态 → None(无跟进义务)。"""
    days = REVIEW_DAYS.get(status)
    return (ts + timedelta(days=days)).isoformat() if days else None


def entered_at(item, status):
    """条目首次进入某状态的时间(状态机无回退 → 至多一次);未进入 → None。"""
    for h in item.get("history") or []:
        if isinstance(h, dict) and h.get("to") == status:
            return parse_dt(h.get("ts"))
    return None


# ---------------------------------------------------------------------------
# add:登记候选域(与 citation_gaps --json 闭环)
# ---------------------------------------------------------------------------
def cmd_add(rest):
    val = {"--domain": None, "--source": None, "--file": DEFAULT_FILE}
    flag = {"--json": False}
    i = 0
    while i < len(rest):
        a = rest[i]
        if a in val:
            if i + 1 >= len(rest):
                die("%s 需要一个值" % a, with_usage=True)
            val[a] = rest[i + 1]; i += 2
        elif a in flag:
            flag[a] = True; i += 1
        else:
            die("未知参数 %r(add 子命令)" % a, with_usage=True)
    if not val["--domain"]:
        die("缺少 --domain\n" + USAGE)
    domain = norm_domain(val["--domain"])
    if not domain:
        die("--domain 不能为空")
    priority, tip, source = "Standard", "", "manual"
    if val["--source"]:
        gaps = load_json_tolerant(val["--source"], "--source(gaps.json)")
        rows = gaps.get("domains")
        if not isinstance(rows, list):
            die("--source 格式不符: 缺 domains 列表(应为 citation_gaps.py --json 输出)")
        row = next((g for g in rows if isinstance(g, dict)
                    and norm_domain(g.get("domain")) == domain), None)
        if row is None:
            die("域 %r 不在 %s 的 domains 中(先跑 citation_gaps.py --json,或去掉 --source 手工登记)"
                % (domain, val["--source"]))
        priority = row.get("priority") if isinstance(row.get("priority"), str) else "Standard"
        tip = row.get("outreach_tip") or ""
        if not tip:                       # 兜底:citation_gaps 的顶层 outreach_tips
            tips = gaps.get("outreach_tips") or {}
            if isinstance(tips, dict):
                tip = tips.get(val["--domain"]) or tips.get(domain) or ""
        source = os.path.abspath(val["--source"])
    data = None
    with data_lock(val["--file"]):
        data = load_data(val["--file"], create=True)
        if any(norm_domain(it.get("domain")) == domain for it in data["items"]):
            die("域 %s 已在库中(同域不重复建条目)" % domain)
        ts = now_utc()
        item = {"id": next_id(data["items"]), "domain": domain, "status": "candidate",
                "priority": priority, "outreach_tip": tip, "source": source,
                "created": ts.isoformat(), "updated": ts.isoformat(),
                "next_review": None, "url": None, "note": "", "history": []}
        data["items"].append(item)
        save_data(val["--file"], data)
    if flag["--json"]:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "added": item},
                         ensure_ascii=False, indent=1))
    else:
        print("add: %s [%s] %s(priority=%s, source=%s)→ %s"
              % (item["id"], domain, "(tip: %s) " % tip if tip else "",
                 priority, source, os.path.abspath(val["--file"])))
    return 0


# ---------------------------------------------------------------------------
# list:表格 + 到期标记
# ---------------------------------------------------------------------------
def is_due(item, now):
    nr = parse_dt(item.get("next_review"))
    return nr is not None and nr <= now


def cmd_list(rest):
    val = {"--status": None, "--file": DEFAULT_FILE}
    flag = {"--due": False, "--json": False}
    i = 0
    while i < len(rest):
        a = rest[i]
        if a in val:
            if i + 1 >= len(rest):
                die("%s 需要一个值" % a, with_usage=True)
            val[a] = rest[i + 1]; i += 2
        elif a in flag:
            flag[a] = True; i += 1
        else:
            die("未知参数 %r(list 子命令)" % a, with_usage=True)
    if val["--status"] is not None and val["--status"] not in STATUSES:
        die("--status 非法 %r;合法值: %s" % (val["--status"], "|".join(STATUSES)))
    data = load_data(val["--file"])
    now = now_utc()
    rows = []
    for it in sorted(data["items"], key=sort_key):
        if val["--status"] is not None and it["status"] != val["--status"]:
            continue
        due = is_due(it, now)
        if flag["--due"] and not due:
            continue
        rows.append((it, due))
    due_n = sum(1 for _, d in rows if d)
    if flag["--json"]:
        payload = {"schema_version": SCHEMA_VERSION, "file": os.path.abspath(val["--file"]),
                   "count": len(rows), "due": due_n,
                   "items": [dict(it, due=d) for it, d in rows]}
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        cols = ("ID", "DOMAIN", "STATUS", "PRIORITY", "NEXT_REVIEW", "URL")
        table = [[it["id"], it["domain"], it["status"], str(it.get("priority") or ""),
                  (str(it.get("next_review") or "")[:10] or "-") + (" [!]" if d else ""),
                  str(it.get("url") or "-")] for it, d in rows]
        widths = [len(c) for c in cols]
        for r in table:
            for n, v in enumerate(r):
                widths[n] = max(widths[n], len(v))
        L = [" ".join(c.ljust(widths[n]) for n, c in enumerate(cols)).rstrip(),
             " ".join("-" * w for w in widths)]
        for r in table:
            L.append(" ".join(v.ljust(widths[n]) for n, v in enumerate(r)).rstrip())
        print("\n".join(L))
        print("共 %d 条(到期 %d)%s" % (len(rows), due_n,
                                       " → %s" % val["--file"] if val["--file"] != DEFAULT_FILE else ""))
    return 0


# ---------------------------------------------------------------------------
# update:状态机推进
# ---------------------------------------------------------------------------
def cmd_update(rest):
    tid = None
    val = {"--status": None, "--note": None, "--url": None, "--file": DEFAULT_FILE}
    flag = {"--json": False}
    i = 0
    while i < len(rest):
        a = rest[i]
        if a in val:
            if i + 1 >= len(rest):
                die("%s 需要一个值" % a, with_usage=True)
            val[a] = rest[i + 1]; i += 2
        elif a in flag:
            flag[a] = True; i += 1
        elif a.startswith("-"):
            die("未知参数 %r(update 子命令)" % a, with_usage=True)
        elif tid is None:
            tid = a; i += 1
        else:
            die("多余的定位参数 %r(update 只接受一个条目 id)" % a, with_usage=True)
    if tid is None:
        die("缺少条目 id\n" + USAGE)
    if val["--status"] is None:
        die("缺少 --status\n" + USAGE)
    new = val["--status"]
    if new not in STATUSES:
        die("--status 非法 %r;合法值: %s" % (new, "|".join(STATUSES)))
    if new == "candidate":
        die("candidate 是初始态,不可作为转换目标(状态机只前进:candidate→drafted→"
            "sent→replied→linked;refused 仅 replied 可进)")
    item = None
    with data_lock(val["--file"]):
        data = load_data(val["--file"])
        item = next((it for it in data["items"] if it.get("id") == tid), None)
        if item is None:
            die("找不到条目 %r(%s 中共 %d 条)" % (tid, val["--file"], len(data["items"])))
        cur = item["status"]
        if cur in TERMINAL_STATUSES:
            die("%s 已是终态 %s,不可再转换" % (tid, cur))
        if (cur, new) not in TRANSITIONS:
            die("非法状态转换 %s → %s;合法链 candidate→drafted→sent→replied→linked"
                "(逐级前进,跳级/回退/同态拒绝);refused 仅 replied 可进(拒绝即回复)"
                % (cur, new))
        ts = now_utc()
        entry = {"ts": ts.isoformat(), "from": cur, "to": new}
        if val["--note"] is not None:
            entry["note"] = val["--note"]
        item.setdefault("history", []).append(entry)
        item["status"] = new
        item["next_review"] = next_review_for(new, ts)
        if val["--note"] is not None:
            item["note"] = val["--note"]
        if val["--url"] is not None:
            item["url"] = val["--url"]
        item["updated"] = ts.isoformat()
        save_data(val["--file"], data)
    if flag["--json"]:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "updated": item},
                         ensure_ascii=False, indent=1))
    else:
        print("update: %s %s → %s(下次复查 %s)%s"
              % (tid, cur, new, str(item["next_review"])[:10] or "-",
                 " url=%s" % item["url"] if val["--url"] is not None else ""))
        if new == "linked" and not item.get("url"):
            print("[i] linked 未带 --url:建议补记产出链接(report 不依赖,但追溯需要)")
    return 0


# ---------------------------------------------------------------------------
# due:复查日到期清单(退出码 1 接 notify)
# ---------------------------------------------------------------------------
def cmd_due(rest):
    val = {"--file": DEFAULT_FILE}
    flag = {"--json": False}
    i = 0
    while i < len(rest):
        a = rest[i]
        if a in val:
            if i + 1 >= len(rest):
                die("%s 需要一个值" % a, with_usage=True)
            val[a] = rest[i + 1]; i += 2
        elif a in flag:
            flag[a] = True; i += 1
        else:
            die("未知参数 %r(due 子命令)" % a, with_usage=True)
    data = load_data(val["--file"])
    now = now_utc()
    rows = []
    for it in sorted(data["items"], key=sort_key):
        nr = parse_dt(it.get("next_review"))
        if nr is None or nr > now:
            continue                       # candidate/终态无复查日,未到期不入
        days = max((now - nr).days, 0)
        tmpl = REVIEW_ACTION.get(it["status"], "复查(%d 天)")
        rows.append({"id": it["id"], "domain": it["domain"], "status": it["status"],
                     "next_review": it["next_review"], "overdue_days": days,
                     "priority": it.get("priority"), "action": tmpl % days,
                     "tip": it.get("outreach_tip") or "", "note": it.get("note") or ""})
    if flag["--json"]:
        payload = {"schema_version": SCHEMA_VERSION, "file": os.path.abspath(val["--file"]),
                   "due": len(rows), "items": rows}
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print("该跟进谁(复查日到期 %d 条):" % len(rows))
        for r in rows:
            L = ["- %s [%s|%s] %s — %s(复查日 %s,过 %d 天)"
                 % (r["id"], r["domain"], r["priority"], r["status"],
                    r["action"], str(r["next_review"])[:10], r["overdue_days"])]
            if r["tip"]:
                L.append("    tip: %s" % r["tip"])
            if r["note"]:
                L.append("    note: %s" % r["note"])
            print("\n".join(L))
        if not rows:
            print("  (无到期;下次自动跟进见 next_review)")
    return 1 if rows else 0


# ---------------------------------------------------------------------------
# report:转化漏斗 + 平均回复天数
# ---------------------------------------------------------------------------
def _rate(num, den):
    return round(num / den, 3) if den else None


def cmd_report(rest):
    val = {"--file": DEFAULT_FILE}
    flag = {"--json": False}
    i = 0
    while i < len(rest):
        a = rest[i]
        if a in val:
            if i + 1 >= len(rest):
                die("%s 需要一个值" % a, with_usage=True)
            val[a] = rest[i + 1]; i += 2
        elif a in flag:
            flag[a] = True; i += 1
        else:
            die("未知参数 %r(report 子命令)" % a, with_usage=True)
    data = load_data(val["--file"])
    items = data["items"]
    counts = {s: 0 for s in STATUSES}
    for it in items:
        counts[it["status"]] += 1
    # 漏斗按"曾到达"口径(history 首次进入该状态的时间;无回退 → 至多一次)
    n_cand = len(items)
    n_sent = sum(1 for it in items if entered_at(it, "sent"))
    n_replied = sum(1 for it in items if entered_at(it, "replied"))
    n_linked = counts["linked"]
    n_refused = counts["refused"]
    reply_days = []
    for it in items:
        st, rp = entered_at(it, "sent"), entered_at(it, "replied")
        if st and rp and rp >= st:
            reply_days.append((rp - st).total_seconds() / 86400.0)
    avg_reply = round(sum(reply_days) / len(reply_days), 1) if reply_days else None
    funnel = {"candidates": n_cand, "sent": n_sent, "replied": n_replied,
              "linked": n_linked,
              "rates": {"candidate_to_sent": _rate(n_sent, n_cand),
                        "sent_to_replied": _rate(n_replied, n_sent),
                        "replied_to_linked": _rate(n_linked, n_replied)},
              "avg_days_to_reply": avg_reply, "reply_samples": len(reply_days),
              "refused": n_refused, "in_flight": {s: counts[s] for s in ACTIVE_STATUSES}}
    if flag["--json"]:
        payload = {"schema_version": SCHEMA_VERSION, "file": os.path.abspath(val["--file"]),
                   "counts": counts, "funnel": funnel}
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        pct = lambda r: ("%.0f%%" % (r * 100)) if r is not None else "N/A"
        L = ["# 外展转化漏斗报告", "",
             "- 条目: %d(数据文件 %s)" % (n_cand, os.path.abspath(val["--file"])),
             "- 在途: candidate %d / drafted %d / sent %d / replied %d;终态: linked %d / refused %d"
             % (counts["candidate"], counts["drafted"], counts["sent"],
                counts["replied"], n_linked, n_refused),
             "- 漏斗(按曾到达口径): 候选 %d → 发送 %d(%s)→ 回复 %d(%s)→ 获得链接 %d(%s)"
             % (n_cand, n_sent, pct(funnel["rates"]["candidate_to_sent"]),
                n_replied, pct(funnel["rates"]["sent_to_replied"]),
                n_linked, pct(funnel["rates"]["replied_to_linked"])),
             "- 平均回复天数: %s(发出→首次回复,%d 个样本)"
             % (avg_reply if avg_reply is not None else "N/A", len(reply_days))]
        print("\n".join(L))
    return 0


COMMANDS = {"add": cmd_add, "list": cmd_list, "update": cmd_update,
            "due": cmd_due, "report": cmd_report}


def main():
    argv = sys.argv[1:]
    if any(a in ("-h", "--help") for a in argv):
        print(USAGE)
        return 0
    if not argv:
        sys.stderr.write("缺少子命令\n" + USAGE + "\n")
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd not in COMMANDS:
        die("未知子命令 %r;合法值: %s" % (cmd, "|".join(COMMANDS)), with_usage=True)
    return COMMANDS[cmd](rest)


if __name__ == "__main__":
    sys.exit(main())
