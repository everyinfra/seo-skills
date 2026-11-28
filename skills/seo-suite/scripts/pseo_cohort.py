#!/usr/bin/env python3
"""pSEO cohort 追踪器(stdlib,pSEO 生产线第 3 件)。规格=references/overview/
pipeline-completeness.md R3-3 + references/technical/programmatic-seo-playbook.md
第八章(cohort 测量/预注册判读/90 天淘汰阶梯)。流水线位置:pseo_pattern_mining(§一
选词)→ 数据层 schema(§二)→ pseo_batch_gate(R3-2 六闸)→ 分批发布(§六,每批一个
cohort id)→ 本脚本周喂 GSC → 判读 → 90 天零展示三选一处置 → 工单交 remediation.py。

cohort 定义(playbook §八):一批发布、同一模板版本、同一数据快照的页面集合。
全站平均会掩盖"一个模板 -90%、整体 -30%"的塌方,所以索引率/展示/点击全部按
cohort 口径聚合,不看全站。

预注册判读(防事后移动球门):cohort init 时把"什么算成/什么算败"写死入档
(playbook §八.2),默认 = 8 周索引率[est] ≥60% 且展示周环比连续为正 2 次;
--criteria JSON 可在建档时覆盖(weeks/min_index_rate/consec_pos_wow 三键),init
之后冻结——同 id 重复 init 直接拒绝,不提供任何改标准的入口;要看新标准=开新
cohort(模板一改=新 cohort,§四.4)。

索引口径(明示):**有曝光=已索引的代理口径 [est]**——GSC 页面导出里某 URL 当周
impressions>0 即计入;这不是 Search Console URL Inspection 的精确口径(已发现未
索引/已索引未展示都会被低估),所有索引率输出一律带 [est] 标注。周快照按 URL∈
cohort 聚合(归一匹配:尾斜杠/大小写容错),cohort 外的行忽略。

90 天淘汰阶梯(playbook §八.3):0-30 天不动 → 31-60 天零展示补内链 → 61-90 天
仍零展示数据增强 → 90 天仍零展示三选一(301 并入最近聚合页/noindex 留功能/410
下线并移出 sitemap)。301 建议目标 = 同 cohort 高曝光**同轴页**(轴无法从 GSC 拿
到,用 URL 目录代理:优先同父目录,次同首段路径——/apps/{a}/integrations/{b} 的
同父目录即同值 a)。红线 NO-GO:有外链页(--backlinks 导入列)或有过排名词展示史
的页默认只标注不处置("批量 410 前确认无外链与转化,防误杀长尾",playbook §八.3)。

数据文件 pseo_cohorts.json(默认当前目录,--state 可指定;R0-7 纪律:状态落
cwd/project 工作区,不写 skill 安装目录):{schema_version, cohorts:[{cohort_id,
template_version, created, expected, urls[], criteria{}, criteria_source,
criteria_frozen, weeks:[{week(周一 ISO 日期), label(ISO 周标), ingested_at,
source_rows, matched_urls, pages{url:{clicks,impressions,position}}}], log[]}]}。
并发口径(R5):save 原子写(tempfile+os.replace)+ 数据文件级 flock(照 remediation.py
data_lock 惯例),init/ingest 的 load→改→save 全程持锁。

用法:
  pseo_cohort.py init --cohort_id NAME --template-version v1 --urls urls.txt \
                     [--expected 500] [--criteria '{"weeks":8,"min_index_rate":0.6,"consec_pos_wow":2}']
  pseo_cohort.py ingest --cohort NAME --gsc gsc_pages.csv [--week 2026-10-06]
  pseo_cohort.py report --cohort NAME            # 判定 FAIL → exit 1
  pseo_cohort.py prune --cohort NAME [--backlinks bl.csv] [--as-of 2027-01-10] [--as-remediation]
  pseo_cohort.py summary                         # 多 cohort 汇总
全部子命令支持 --json;--as-remediation 输出 remediations.json 同 schema 的
{items:[...]}(remediation.py list --file 可直接消费)。
退出码:0 正常 / 1 report 判定 FAIL 或 prune 产出处置工单(需人动作)/ 2 输入或
参数错(套件契约,ci-gates.md)。"""
import argparse
import contextlib
import csv
try:
    import fcntl
except ImportError:  # Windows 没有 fcntl,改用 msvcrt.locking 加同样的排他锁
    fcntl = None
    import msvcrt
import json
import os
import sys
import tempfile
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

SCHEMA_VERSION = 1
DEFAULT_STATE = "pseo_cohorts.json"

# 预注册判读默认标准(playbook §八.2 原文:"8 周索引率≥60% 且展示周环比两次为正")。
DEFAULT_CRITERIA = {"weeks": 8, "min_index_rate": 0.60, "consec_pos_wow": 2}
CRITERIA_KEYS = ("weeks", "min_index_rate", "consec_pos_wow")

PRUNE_WINDOW_DAYS = 90          # 90 天零展示窗口(playbook §八.3 阶梯终点)
BACKLINK_COLS = ("backlinks", "backlink", "links", "ref_domains", "refdomains", "external")
PAGE_COLS = ("page", "top pages", "url", "landing page")
REDIRECT_ID_PREFIX = "PSEO"     # 工单 id 前缀(与 REM- 命名空间区分,避免并库冲突)

USAGE_EPILOG = """\
预注册纪律:判读标准 init 时写死入档(默认 8 周索引率[est]≥60% 且展示周环比连续
正 2 次),--criteria 只能在 init 时覆盖,之后冻结——看完数据再挑标准=移动球门,
禁止;要换标准请开新 cohort。
索引口径:有曝光=已索引 [est](非 URL Inspection 精确口径,输出一律带标注)。
prune 红线:有外链(--backlinks 列>0)或有过展示史(有排名词代理)的页默认 NO-GO
只标注,不自动处置;410 恒需人工确认无转化。
退出码:0 正常 / 1 FAIL 判定或有处置工单 / 2 输入或参数错。"""


def die(msg, code=2):
    """输入/参数错误 → stderr + 退出码 2(套件契约)。"""
    sys.stderr.write(msg + "\n")
    sys.exit(code)


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_day(s, what):
    """YYYY-MM-DD → date;非法 → die(2)。"""
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        die("%s 非法: %r(需 YYYY-MM-DD)" % (what, s))


def monday(d):
    """归一到所在 ISO 周的周一(周快照键)。"""
    return d - timedelta(days=d.weekday())


def week_label(d):
    y, w, _ = d.isocalendar()
    return "%d-W%02d" % (y, w)


def url_norm(u):
    """匹配归一:scheme+host 小写 + 去尾斜杠(根路径保留 "/")——防 GSC 导出与
    urls.txt 的尾斜杠/大小写漂移造成假"未匹配"。"""
    u = (u or "").strip()
    if "://" in u:
        scheme, rest = u.split("://", 1)
        host, _, tail = rest.partition("/")
        u = scheme.lower() + "://" + host.lower() + ("/" + tail if tail else "")
    if len(u) > 1:
        u = u.rstrip("/") or u
    return u


def url_parts(u):
    """轴代理:首段路径 + 父目录(同父目录≈同值 1;/apps/a/integrations/b 与
    /apps/a/integrations/c 同父目录即同轴 a)。"""
    path = urllib.parse.urlsplit(u).path or "/"
    segs = [s for s in path.split("/") if s]
    d = path[:path.rfind("/")] if path.rfind("/") > 0 else ""
    return {"first": segs[0] if segs else "", "dir": d}


# ───────────────────────── 状态文件(原子写 + flock,R5 口径) ─────────────────────────

def load_state(path, create=False):
    if not os.path.exists(path):
        if create:
            return {"schema_version": SCHEMA_VERSION, "cohorts": []}
        die("状态文件不存在: %s(先运行 init)" % path)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        die("读不了状态文件 %s: %s" % (path, e))
    if not isinstance(data.get("cohorts"), list):
        die("状态文件格式不符: 缺 cohorts 列表(%s)" % path)
    return data


def save_state(path, data):
    """原子写(tempfile+os.replace,照 remediation.save_data):中断/并发不落半截
    文件;写失败自动清理临时文件。"""
    d = os.path.dirname(os.path.abspath(path)) or "."
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
def state_lock(path, timeout=30.0):
    """数据文件级 flock(照 remediation.data_lock):周喂多为单人节奏,仍防本地
    cron/agent 两进程交替写覆盖;超时 → 放弃本次写(SystemExit),不静默丢数据。"""
    d = os.path.dirname(os.path.abspath(path)) or "."
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
                    raise SystemExit("警告: 另一进程持有 %s 超过 %.0fs,跳过本次写" % (lock_path, timeout))
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


def get_cohort(state, name):
    for c in state["cohorts"]:
        if c.get("cohort_id") == name:
            return c
    die("cohort 不存在: %s(先 init;可用 summary 查看已登记 cohort)" % name)


def add_log(c, text):
    c.setdefault("log", []).append("%s %s" % (now_utc().isoformat(), text))


# ───────────────────────── CSV 解析(复用 gsc_mining 容错思路) ─────────────────────────

def read_csv_rows(path, what):
    """utf-8-sig + DictReader + 列名 strip/lower(GSC 导出带 BOM、列名有大小写与
    'Top pages' 变体),与 gsc_mining.read 同法。"""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        die("读不了 %s: %s" % (what, e))
    return [{k.strip().lower(): v for k, v in r.items() if k is not None} for r in rows]


def col(row, *names):
    """前缀匹配取列(gsc_mining.get 同法:'Top pages'→'page' 前缀不命中,故枚举
    常见变体;impressions/position 同)。"""
    for n in names:
        for k in row:
            if k.startswith(n):
                return row[k]
    return None


def parse_num(v):
    v = (v or "").strip().replace(",", "")
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def parse_gsc_pages(path):
    """GSC 页面导出(Page/Clicks/Impressions/Position)→ [(url, clicks, impr, pos)];
    缺列 → die(2);数值坏行跳过并计数。CTR 列存在与否不影响。"""
    rows = read_csv_rows(path, "GSC 页面导出(--gsc)")
    if not rows:
        die("GSC 导出为空: %s" % path)
    if col(rows[0], *PAGE_COLS) is None:
        die("GSC 导出缺 Page 列(接受 Page/Top pages/URL/Landing page;%s)" % path)
    if col(rows[0], "impressions", "impr") is None:
        die("GSC 导出缺 Impressions 列(%s)" % path)
    out, bad = [], 0
    for r in rows:
        u = (col(r, *PAGE_COLS) or "").strip()
        clicks = parse_num(col(r, "clicks"))
        impr = parse_num(col(r, "impressions", "impr"))
        pos = parse_num(col(r, "position", "avg. position", "avg position"))
        if not u or clicks is None or impr is None or pos is None:
            bad += 1
            continue
        out.append((u, int(clicks), int(impr), pos))
    if not out:
        die("GSC 导出无可解析行(%s)" % path)
    return out, bad


def parse_backlinks(path):
    """外链导出 → {url_norm: 数量};列接受 url/page/target + backlinks/links/
    ref_domains 等变体;值>0 才是红线。"""
    rows = read_csv_rows(path, "外链导出(--backlinks)")
    if not rows:
        die("外链导出为空: %s" % path)
    if col(rows[0], "url", "page", "target") is None:
        die("外链导出缺 URL 列(接受 url/page/target;%s)" % path)
    if col(rows[0], *BACKLINK_COLS) is None:
        die("外链导出缺外链数列(接受 %s;%s)" % ("/".join(BACKLINK_COLS[:3]), path))
    out = {}
    for r in rows:
        u = (col(r, "url", "page", "target") or "").strip()
        n = parse_num(col(r, *BACKLINK_COLS))
        if u and n is not None:
            out[url_norm(u)] = int(n)
    return out


# ───────────────────────── 子命令:init ─────────────────────────

def validate_criteria(crit, source):
    """--criteria 覆盖校验:只认三键,类型/范围错 → die(2)——标准要冻结,先验后存。"""
    out = dict(DEFAULT_CRITERIA)
    for k, v in crit.items():
        if k not in CRITERIA_KEYS:
            die("--criteria 非法键: %r(只接受 %s)" % (k, "/".join(CRITERIA_KEYS)))
        out[k] = v
    if not isinstance(out["weeks"], int) or isinstance(out["weeks"], bool) or out["weeks"] < 1:
        die("--criteria.weeks 需为 ≥1 整数")
    if not isinstance(out["min_index_rate"], (int, float)) or isinstance(out["min_index_rate"], bool) \
            or not 0 < out["min_index_rate"] <= 1:
        die("--criteria.min_index_rate 需为 (0,1] 数数")
    if not isinstance(out["consec_pos_wow"], int) or isinstance(out["consec_pos_wow"], bool) \
            or out["consec_pos_wow"] < 1:
        die("--criteria.consec_pos_wow 需为 ≥1 整数")
    out["min_index_rate"] = round(float(out["min_index_rate"]), 4)
    return out


def cmd_init(a):
    try:
        with open(a.urls, encoding="utf-8-sig") as f:
            lines = f.read().splitlines()
    except OSError as e:
        die("读不了 urls 文件: %s" % e)
    urls, seen, dups = [], set(), 0
    for ln in lines:
        u = ln.strip()
        if not u or u.startswith("#"):
            continue
        if url_norm(u) in seen:
            dups += 1
            continue
        seen.add(url_norm(u))
        urls.append(u)
    if not urls:
        die("urls 文件无有效 URL: %s" % a.urls)
    crit = dict(DEFAULT_CRITERIA)
    if a.criteria:
        try:
            parsed = json.loads(a.criteria)
        except json.JSONDecodeError as e:
            die("--criteria 不是合法 JSON: %s" % e)
        if not isinstance(parsed, dict):
            die("--criteria 需为 JSON 对象,如 '{\"weeks\":8,\"min_index_rate\":0.6,\"consec_pos_wow\":2}'")
        crit = validate_criteria(parsed, "override")
    expected = a.expected if a.expected is not None else len(urls)
    if expected < len(urls):
        die("--expected(%d) 小于 urls 清单数(%d),口径矛盾" % (expected, len(urls)))
    with state_lock(a.state):
        state = load_state(a.state, create=True)
        if any(c.get("cohort_id") == a.cohort_id for c in state["cohorts"]):
            die("cohort 已存在: %s(判读标准已冻结;改标准=开新 cohort,禁止同 id 重建)" % a.cohort_id)
        cohort = {
            "cohort_id": a.cohort_id,
            "template_version": a.template_version,
            "created": now_utc().isoformat(),
            "expected": expected,
            "urls": urls,
            "criteria": crit,
            "criteria_source": "override" if a.criteria else "default",
            "criteria_frozen": True,
            "weeks": [],
            "log": [],
        }
        add_log(cohort, "init: %d URL(去重 %d),expected=%d,标准=%s并冻结"
                % (len(urls), dups, expected, "覆盖" if a.criteria else "默认"))
        state["cohorts"].append(cohort)
        save_state(a.state, state)
    payload = {"schema_version": SCHEMA_VERSION, "command": "init", "cohort": a.cohort_id,
               "template_version": a.template_version, "urls": len(urls), "duplicates_dropped": dups,
               "expected": expected, "criteria": crit, "criteria_source": cohort["criteria_source"],
               "criteria_frozen": True}
    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print("cohort 已登记: %s(模板 %s)" % (a.cohort_id, a.template_version))
        print("  URL %d 条(去重丢弃 %d)  expected=%d" % (len(urls), dups, expected))
        print("  预注册判读(已冻结,防事后移动球门): %d 周索引率[est]≥%.0f%% 且展示周环比连续为正 %d 次"
              % (crit["weeks"], crit["min_index_rate"] * 100, crit["consec_pos_wow"]))
    return 0


# ───────────────────────── 子命令:ingest ─────────────────────────

def cmd_ingest(a):
    gsc_rows, bad = parse_gsc_pages(a.gsc)
    wday = parse_day(a.week, "--week") if a.week else monday(now_utc().date())
    wkey = monday(wday).isoformat()
    with state_lock(a.state):
        state = load_state(a.state)
        c = get_cohort(state, a.cohort)
        index = {url_norm(u): u for u in c["urls"]}
        agg, matched_rows = {}, 0
        for u, clicks, impr, pos in gsc_rows:
            canon = index.get(url_norm(u))
            if canon is None:
                continue
            matched_rows += 1
            d = agg.setdefault(canon, {"clicks": 0, "impressions": 0, "pos_w": 0.0, "pos_n": 0})
            d["clicks"] += clicks
            d["impressions"] += impr
            if impr > 0:                       # 位次按曝光加权(GSC 页面维度同 URL 多行时)
                d["pos_w"] += pos * impr
                d["pos_n"] += impr
        pages = {u: {"clicks": d["clicks"], "impressions": d["impressions"],
                     "position": round(d["pos_w"] / d["pos_n"], 1) if d["pos_n"] else None}
                 for u, d in agg.items()}
        replaced = any(w["week"] == wkey for w in c["weeks"])
        c["weeks"] = [w for w in c["weeks"] if w["week"] != wkey]
        c["weeks"].append({"week": wkey, "label": week_label(monday(wday)),
                           "ingested_at": now_utc().isoformat(),
                           "source_rows": len(gsc_rows), "bad_rows": bad,
                           "matched_urls": len(pages), "pages": pages})
        c["weeks"].sort(key=lambda w: w["week"])
        add_log(c, "ingest: %s %d 行(匹配 %d URL,坏行 %d)%s"
                % (wkey, len(gsc_rows), len(pages), bad, ",覆盖旧快照" if replaced else ""))
        save_state(a.state, state)
    payload = {"schema_version": SCHEMA_VERSION, "command": "ingest", "cohort": a.cohort,
               "week": wkey, "label": week_label(monday(wday)), "replaced": replaced,
               "source_rows": len(gsc_rows), "bad_rows": bad, "matched_urls": len(pages),
               "indexed_proxy_est": sum(1 for p in pages.values() if p["impressions"] > 0),
               "impressions": sum(p["impressions"] for p in pages.values()),
               "clicks": sum(p["clicks"] for p in pages.values())}
    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print("已喂 %s 周 %s: %d 行 → 匹配 %d/%d URL(坏行 %d)%s"
              % (a.cohort, wkey, len(gsc_rows), len(pages), len(c["urls"]), bad,
                 "(覆盖旧快照)" if replaced else ""))
        print("  当周有曝光[est]=已索引代理: %d URL;展示 %d;点击 %d"
              % (payload["indexed_proxy_est"], payload["impressions"], payload["clicks"]))
    return 0


# ───────────────────────── 判读核心(report/prune/summary 共用) ─────────────────────────

def week_series(c):
    """周序列:逐周 matched/当周有曝光/累计有曝光(索引爬坡期数据抖动,累计口径
    更稳:某 URL 一周有曝光即计入此后各周)/索引率[est]/展示/点击/WoW。"""
    cum, out = set(), []
    prev_impr = None
    for w in sorted(c["weeks"], key=lambda x: x["week"]):
        pages = w.get("pages", {})
        impr = sum(p["impressions"] for p in pages.values())
        clicks = sum(p["clicks"] for p in pages.values())
        cum.update(u for u, p in pages.items() if p["impressions"] > 0)
        out.append({"week": w["week"], "label": w.get("label", ""),
                    "matched": len(pages),
                    "indexed_week_est": sum(1 for p in pages.values() if p["impressions"] > 0),
                    "indexed_cum_est": len(cum),
                    "index_rate_cum_est": round(len(cum) / c["expected"], 4) if c["expected"] else 0.0,
                    "impressions": impr, "clicks": clicks,
                    "wow_impressions": (impr - prev_impr) if prev_impr is not None else None})
        prev_impr = impr
    return out


def max_pos_run(series):
    """展示周环比**连续**为正的最长次数(0 差不计正;判读要的是连续势头)。"""
    run = best = 0
    for s in series:
        d = s["wow_impressions"]
        if d is not None and d > 0:
            run += 1
            best = max(best, run)
        elif d is not None:
            run = 0
    return best


def judge(c):
    """预注册判读三态:NOT_DUE(未到期)/PASS/FAIL。到期(喂满 weeks 周)才判:
    累计索引率[est] ≥ min_index_rate 且 WoW 连续正 run ≥ consec_pos_wow → PASS。"""
    crit = c["criteria"]
    series = week_series(c)
    n = len(series)
    if n < crit["weeks"]:
        return {"state": "NOT_DUE", "due": False, "weeks_evaluated": n,
                "weeks_required": crit["weeks"], "criteria": crit, "checks": None}
    rate = series[-1]["index_rate_cum_est"]
    run = max_pos_run(series)
    checks = {"index_rate_cum_est": {"value": rate, "threshold": crit["min_index_rate"],
                                     "pass": rate >= crit["min_index_rate"]},
              "consec_pos_wow": {"value": run, "required": crit["consec_pos_wow"],
                                 "pass": run >= crit["consec_pos_wow"]}}
    return {"state": "PASS" if all(v["pass"] for v in checks.values()) else "FAIL",
            "due": True, "weeks_evaluated": n, "weeks_required": crit["weeks"],
            "criteria": crit, "checks": checks}


# ───────────────────────── 子命令:report ─────────────────────────

EST_NOTE = "索引口径: 当周有曝光=已索引 [est](非 Search Console URL Inspection 精确口径)"


def cmd_report(a):
    state = load_state(a.state)
    c = get_cohort(state, a.cohort)
    series = week_series(c)
    j = judge(c)
    totals = {"impressions": sum(s["impressions"] for s in series),
              "clicks": sum(s["clicks"] for s in series)}
    payload = {"schema_version": SCHEMA_VERSION, "command": "report", "cohort": a.cohort,
               "template_version": c["template_version"], "created": c["created"],
               "expected": c["expected"], "urls": len(c["urls"]), "criteria": c["criteria"],
               "criteria_source": c.get("criteria_source"), "criteria_frozen": True,
               "judgment": j, "series": series, "totals": totals,
               "disclaimers": [EST_NOTE]}
    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 1 if j["state"] == "FAIL" else 0
    crit = c["criteria"]
    print("## pSEO cohort 报告: %s(模板 %s,expected %d,%d 周)" % (a.cohort, c["template_version"], c["expected"], len(series)))
    if j["state"] == "NOT_DUE":
        print("判定: 未到期(已喂 %d/%d 周;预注册标准 init 时冻结,防事后移动球门)"
              % (j["weeks_evaluated"], j["weeks_required"]))
    else:
        ck = j["checks"]
        print("判定: %s(到期判读: 累计索引率[est] %.1f%% %s %.0f%%;展示周环比连续为正 %d 次 %s %d)"
              % (j["state"], ck["index_rate_cum_est"]["value"] * 100,
                 "≥" if ck["index_rate_cum_est"]["pass"] else "<", crit["min_index_rate"] * 100,
                 ck["consec_pos_wow"]["value"], "≥" if ck["consec_pos_wow"]["pass"] else "<",
                 crit["consec_pos_wow"]))
        print("  预注册标准(init 冻结,来源 %s): weeks=%d, min_index_rate=%.2f, consec_pos_wow=%d"
              % (c.get("criteria_source"), crit["weeks"], crit["min_index_rate"], crit["consec_pos_wow"]))
    print("周序列(%s):" % EST_NOTE)
    print("%-9s %8s %13s %8s %9s %8s %9s" % ("week", "matched", "indexed[est]", "cum", "rate", "impr", "clicks"))
    for s in series:
        print("%-9s %8d %13d %8d %8.1f%% %8d %9d" % (s["label"] or s["week"], s["matched"],
              s["indexed_week_est"], s["indexed_cum_est"], s["index_rate_cum_est"] * 100,
              s["impressions"], s["clicks"]))
    print("累计: 展示 %d / 点击 %d" % (totals["impressions"], totals["clicks"]))
    return 1 if j["state"] == "FAIL" else 0


# ───────────────────────── 子命令:prune ─────────────────────────

def ladder_hint(age_days):
    """playbook §八.3 阶梯:90 天前三段不处置,只提示;到 90 天才开三选一工单。"""
    if age_days < 31:
        return "0-30 天: 不动(索引爬坡期)"
    if age_days < 61:
        return "31-60 天: 零展示 → 检查索引状态与入链,补内链/并入 hub"
    if age_days < PRUNE_WINDOW_DAYS:
        return "61-90 天: 仍零展示 → 数据增强一次(补事实字段/proof 块)重渲染"
    return "≥90 天: 三选一处置(301/noindex/410)"


def pick_target(page_url, healthy):
    """301 目标 = 同 cohort 高曝光同轴页:同父目录(同值 1)> 同首段路径;同分值下
    按展示量取高。轴信息 GSC 拿不到,用 URL 目录代理(playbook §八.3);**无同轴
    健康页(tier 0)不承接**——跨轴 301 会把死页流量倒给语义无关页,此时回落 noindex。"""
    pp = url_parts(page_url)
    best_url, best_key = None, None
    for u, impr in sorted(healthy, key=lambda x: -x[1]):
        cp = url_parts(u)
        tier = 2 if pp["dir"] and cp["dir"] == pp["dir"] else (1 if pp["first"] and cp["first"] == pp["first"] else 0)
        if tier == 0:
            continue
        key = (tier, impr)
        if best_key is None or key > best_key:
            best_url, best_key = u, key
    return best_url


def cmd_prune(a):
    state = load_state(a.state)
    c = get_cohort(state, a.cohort)
    as_of = parse_day(a.as_of, "--as-of") if a.as_of else now_utc().date()
    created = datetime.fromisoformat(c["created"])
    created_day = created.date() if created.tzinfo else created.replace(tzinfo=timezone.utc).date()
    age = (as_of - created_day).days
    if age < 0:
        die("--as-of(%s) 早于 cohort 创建(%s)" % (as_of, created_day))
    window_start = as_of - timedelta(days=PRUNE_WINDOW_DAYS)
    weeks = sorted(c["weeks"], key=lambda w: w["week"])
    in_window = [w for w in weeks if datetime.strptime(w["week"], "%Y-%m-%d").date() >= window_start]
    if not in_window:
        die("无最近 %d 天内的周快照(先 ingest;prune 是处置建议,缺数据不猜)" % PRUNE_WINDOW_DAYS)
    backlinks = parse_backlinks(a.backlinks) if a.backlinks else {}
    # 90 天窗口内逐 URL 展示;全史展示=有排名词史(零展示窗内页曾有词排名 → 红线)
    window_impr, ever_impr = {u: 0 for u in c["urls"]}, {u: 0 for u in c["urls"]}
    for w in weeks:
        for u, p in w.get("pages", {}).items():
            ever_impr[u] = ever_impr.get(u, 0) + p["impressions"]
        if w in in_window:
            for u, p in w.get("pages", {}).items():
                window_impr[u] = window_impr.get(u, 0) + p["impressions"]
    zero_pages = [u for u in c["urls"] if window_impr.get(u, 0) == 0]
    healthy = sorted(((u, n) for u, n in ever_impr.items() if n > 0), key=lambda x: -x[1])
    due = age >= PRUNE_WINDOW_DAYS
    tickets = []
    for u in zero_pages:
        no_go, bl = [], backlinks.get(url_norm(u), 0)
        if bl > 0:
            no_go.append("backlinks(外链 %d 条)" % bl)
        if ever_impr.get(u, 0) > 0:
            no_go.append("ranking_history(曾有展示=有排名词史,防误杀长尾)")
        target = pick_target(u, healthy) if not no_go else None
        if no_go:
            recommended = "review"
        elif target:
            recommended = "301"
        else:
            recommended = "noindex"
        tickets.append({"url": u, "age_days": age, "weeks_zero_in_window": len(in_window),
                        "backlinks": bl, "no_go": no_go, "recommended": recommended,
                        "options": {"301": {"target": target} if target else None,
                                    "noindex": "noindex 留功能(不 301/410)",
                                    "410": "410 下线并移出 sitemap(需人工确认无转化)"}})
    tickets.sort(key=lambda t: (bool(t["no_go"]), t["url"]))
    tickets = tickets if due else []       # 未到期只报数不开单(阶梯 0-90 天不处置)
    payload = {"schema_version": SCHEMA_VERSION, "command": "prune", "cohort": a.cohort,
               "as_of": as_of.isoformat(), "cohort_age_days": age,
               "window_days": PRUNE_WINDOW_DAYS, "window_weeks": len(in_window),
               "ladder": ladder_hint(age), "due_for_disposition": due,
               "zero_impression_pages": len(zero_pages),
               "no_go_pages": sum(1 for t in tickets if t["no_go"]),
               "tickets": tickets,
               "disclaimers": [EST_NOTE, "批量 410 前确认无外链与转化(playbook §八.3)"]}
    if a.as_remediation:
        print(json.dumps({"items": remediation_items(c, tickets, as_of)}, ensure_ascii=False, indent=1))
        return 1 if tickets else 0
    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print("## pSEO prune: %s(as-of %s,cohort 龄 %d 天,%d 周快照在 90 天窗口内)"
              % (a.cohort, as_of, age, len(in_window)))
        print("阶梯: %s | 90 天零展示页: %d%s" % (ladder_hint(age), len(zero_pages),
              "" if due else "(未到期不开工单)"))
        if not due:
            if zero_pages:
                print("  零展示页(暂不处置,按阶梯行动): " + ", ".join(u for u in zero_pages[:10]) +
                      (" …" if len(zero_pages) > 10 else ""))
            return 0
        for t in tickets:
            if t["no_go"]:
                print("  [NO-GO] %s → 需人审(%s)" % (t["url"], "; ".join(t["no_go"])))
            elif t["recommended"] == "301":
                print("  [301]   %s → %s(同 cohort 高曝光同轴页)" % (t["url"], t["options"]["301"]["target"]))
            else:
                print("  [%s]  %s" % (t["recommended"], t["url"]))
        print("红线: 有外链/有排名词史页默认 NO-GO 标注,不自动处置;410 恒需人工确认无转化。")
    return 1 if tickets else 0


def remediation_items(c, tickets, as_of):
    """--as-remediation:转 remediations.json 同 schema 工单(remediation.py list
    --file 可直接消费;id 用 PSEO- 前缀避免与 REM- 编号并库冲突)。NO-GO 页也建
    单但 action=人审,status 一律 proposed——接受/推进由 remediation 状态机管。"""
    items = []
    for n, t in enumerate(tickets, 1):
        if t["no_go"]:
            action = "人审后三选一(301/noindex/410): NO-GO %s" % "; ".join(t["no_go"])
        elif t["recommended"] == "301":
            action = "301 → %s(同 cohort 高曝光同轴页)" % t["options"]["301"]["target"]
        else:
            action = "noindex 保留功能(无同轴承接页,不 301/410)"
        items.append({
            "id": "%s-%03d" % (REDIRECT_ID_PREFIX, n),
            "rule_id": "pseo-prune-90d-zero-impressions",
            "area": "indexability",
            "action": action,
            "phase": "month",
            "severity": "WARN",
            "affected_urls": [t["url"]],
            "status": "proposed",
            "created": as_of.isoformat(),
            "deadline": (as_of + timedelta(days=30)).isoformat(),
            "closed": None,
            "verify_hint": "处置后该 URL 从 GSC 页面导出消失/并入目标页即核销",
            "note": "cohort=%s 模板=%s;90 天窗口 %d 周零展示;外链 %d 条;NO-GO=%s"
                    % (c["cohort_id"], c["template_version"], t["weeks_zero_in_window"],
                       t["backlinks"], ",".join(t["no_go"]) or "无"),
        })
    return items


# ───────────────────────── 子命令:summary ─────────────────────────

def cmd_summary(a):
    state = load_state(a.state, create=True)
    rows = []
    for c in state["cohorts"]:
        series = week_series(c)
        j = judge(c)
        rows.append({"cohort": c["cohort_id"], "template_version": c["template_version"],
                     "created": c["created"][:10], "expected": c["expected"], "urls": len(c["urls"]),
                     "weeks": len(series),
                     "index_rate_cum_est": series[-1]["index_rate_cum_est"] if series else None,
                     "impressions": sum(s["impressions"] for s in series),
                     "clicks": sum(s["clicks"] for s in series),
                     "judgment": j["state"]})
    rows.sort(key=lambda r: r["cohort"])
    payload = {"schema_version": SCHEMA_VERSION, "command": "summary", "cohorts": rows,
               "totals": {"cohorts": len(rows), "expected": sum(r["expected"] for r in rows),
                          "impressions": sum(r["impressions"] for r in rows),
                          "clicks": sum(r["clicks"] for r in rows)}}
    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
        return 0
    print("## pSEO cohort 汇总(%d 个;索引率=累计有曝光 [est])" % len(rows))
    if not rows:
        print("(无 cohort,先 init)")
        return 0
    print("%-14s %-5s %5s %4s %12s %9s %7s %8s" % ("cohort", "模板", "URL", "周", "索引率[est]", "展示", "点击", "判定"))
    for r in rows:
        rate = "%.1f%%" % (r["index_rate_cum_est"] * 100) if r["index_rate_cum_est"] is not None else "-"
        print("%-14s %-5s %5d %4d %12s %9d %7d %8s" % (r["cohort"], r["template_version"],
              r["urls"], r["weeks"], rate, r["impressions"], r["clicks"], r["judgment"]))
    t = payload["totals"]
    print("合计: cohort %d / expected %d / 展示 %d / 点击 %d" % (t["cohorts"], t["expected"], t["impressions"], t["clicks"]))
    return 0


# ───────────────────────── CLI ─────────────────────────

def _sub_state(p):
    """子命令级 --state(SUPPRESS:不给时不覆盖顶层已解析的值——argparse 只在
    属性缺席时才落默认,顶层 default 恒在,故两种位置均可传)。"""
    p.add_argument("--state", default=argparse.SUPPRESS, help=argparse.SUPPRESS)


def build_parser():
    ap = argparse.ArgumentParser(
        prog="pseo_cohort.py",
        description="pSEO cohort 周喂追踪:预注册判读 + 90 天零展示三选一处置"
                    "(规格 pipeline-completeness.md R3-3 + programmatic-seo-playbook §八)",
        epilog=USAGE_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state", default=DEFAULT_STATE,
                    help="状态文件(默认当前目录 %s;R0-7:不写 skill 安装目录)" % DEFAULT_STATE)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="登记 cohort:预注册判读标准写死入档并冻结")
    _sub_state(p)
    p.add_argument("--cohort_id", required=True, help="cohort 标识(=批次 id;模板一改=新 cohort)")
    p.add_argument("--template-version", required=True, help="模板版本号(如 v1;cohort 分组键)")
    p.add_argument("--urls", required=True, help="URL 清单文件(每行一条;# 注释/空行跳过)")
    p.add_argument("--expected", type=int, default=None,
                   help="已提交页数(分母;缺省=清单条数)")
    p.add_argument("--criteria", default=None,
                   help='判读标准 JSON,仅 init 时可给(默认 {"weeks":8,"min_index_rate":0.6,'
                        '"consec_pos_wow":2}),此后冻结')
    p.add_argument("--json", action="store_true", help="结构化输出")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("ingest", help="周喂 GSC 页面导出(Page/Clicks/Impressions/Position)")
    _sub_state(p)
    p.add_argument("--cohort", required=True)
    p.add_argument("--gsc", required=True, help="GSC 页面导出 CSV(utf-8-sig/列名容错)")
    p.add_argument("--week", default=None, help="该快照的周(YYYY-MM-DD,归一到周一;"
                                                "缺省=当前周;同周重喂=覆盖)")
    p.add_argument("--json", action="store_true", help="结构化输出")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("report", help="索引率[est]曲线 + 展示/点击趋势 + 预注册判读三态")
    _sub_state(p)
    p.add_argument("--cohort", required=True)
    p.add_argument("--json", action="store_true", help="结构化输出")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("prune", help="90 天零展示 → 301/noindex/410 三选一工单草稿")
    _sub_state(p)
    p.add_argument("--cohort", required=True)
    p.add_argument("--backlinks", default=None,
                   help="外链导出 CSV(url/page/target + backlinks/links/ref_domains 列;"
                        "值>0 = NO-GO 红线)")
    p.add_argument("--as-of", default=None, help="基准日 YYYY-MM-DD(回放/测试;缺省=今天)")
    p.add_argument("--as-remediation", action="store_true",
                   help="输出 remediations.json 同 schema 的 {items:[...]}"
                        "(remediation.py list --file 直接消费)")
    p.add_argument("--json", action="store_true", help="结构化输出")
    p.set_defaults(func=cmd_prune)

    p = sub.add_parser("summary", help="多 cohort 汇总")
    _sub_state(p)
    p.add_argument("--json", action="store_true", help="结构化输出")
    p.set_defaults(func=cmd_summary)
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
