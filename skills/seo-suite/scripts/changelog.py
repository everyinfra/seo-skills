#!/usr/bin/env python3
"""changelog.py — 页面变更审计追踪(Conductor Changelog 官方口径,stdlib only)。

用途(根因诊断): 回答"流量下跌那天,页面改了什么"。对每 URL 的快照时间序列做
字段级 diff,产出可检索的变更事件流。与 gsc_mining.py --decay(28d vs 前 28d
流量衰退检测)联动: gsc_mining 找到衰退页与衰退起点日之后,用
    python3 changelog.py --db monitor.db --url <衰退页> --from <衰退起点>
列出该窗内该页的全部字段变更(noindex/canonical/title…),即第一嫌疑清单;
再加 --summary 看"哪类字段变得最多"——批量误操作(如整站 canonical 改写)会
在频次表上直接现形。

输入(二选一,对齐 monitor.py 的 snapshots 表导出;只读不写库):
  --db monitor.db     monitor.py 的 SQLite 库(读 snapshots 表 check='pages' 行,
                      value 为页面指标 JSON: status/title/meta_desc/canonical/
                      indexable/noindex_source…,run_id 存入事件 snapshot 供溯源)
  --snaps snaps.json  独立格式: [{url, ts, fields{title, description, h1, canonical,
                      indexable, noindex_source, hreflang[], page_type, status?}}]

事件 schema【Conductor 官方】{url, ts, change_type, property, old, new, snapshot},
  change_type 5 枚举【官方】:
    changed     属性变(白名单字段级 diff;仅两个快照均 2xx 才 diff——4xx/5xx 页字段不可信)
    added       新页首见(该 URL 时间序列的第一个快照)
    removed     连续 4xx/消失(快照转入 4xx 时记一条;恢复 2xx 记 changed(status))
    redirected  3xx
    other       5xx/不可达(网络层 error)
  追踪字段白名单: title / meta description / H1 / canonical / indexable /
    noindex_source / hreflang 列表(比较忽略顺序) / page type
  不追踪【官方口径"仅当前值无历史"】: 入链 / 出链 / PageSpeed——输入里出现
    这些字段时跳过并在报告头提示(只有当前值,没有可比历史,不产事件);
    其余非白名单字段(latency/og_*/final_url/hash 等 monitor 内部量)静默忽略。

检索: --from/--to(含端点)窗 + --url 子串过滤 + --type changed,added 枚举过滤;
  粒度规则【官方】: 近 14 天按日;更早按周,同周同 URL 同字段多变更折叠保留
  最后一次 + 计数(×N)。粒度基准 = --to 的日期(缺省今天)。

输出: markdown 时间轴(按 URL 分组,每事件一行 时间|类型|字段 old→new);
  --json 结构化;--summary 每字段变更频次表(哪类变更最多——root cause 线索)。

退出码: 0 正常(含零事件) / 2 输入或参数错误。"""
import argparse
import json
import os
import sqlite3
import sys
import urllib.parse
from datetime import date, datetime

CHANGE_TYPES = ("changed", "added", "removed", "redirected", "other")

# 输入别名 → 统一属性名(monitor.py 的 meta_desc 与 snaps.json 的 description 同归一)
TRACKED_ALIASES = {
    "title": "title",
    "meta_desc": "meta_description", "description": "meta_description",
    "meta_description": "meta_description",
    "h1": "h1",
    "canonical": "canonical",
    "indexable": "indexable",
    "noindex_source": "noindex_source",
    "hreflang": "hreflang",
    "page_type": "page_type", "page type": "page_type", "pagetype": "page_type",
}
PROP_ORDER = ["title", "meta_description", "h1", "canonical", "indexable",
              "noindex_source", "hreflang", "page_type"]

# 不追踪清单【Conductor 官方口径: 入链/出链/PageSpeed 仅当前值无历史】——出现即跳过并提示
NOT_TRACKED = {"inlinks": "入链", "in_links": "入链", "internal_links": "入链",
               "outlinks": "出链", "out_links": "出链", "external_links": "出链",
               "pagespeed": "PageSpeed", "page_speed": "PageSpeed"}

USAGE = """usage: changelog.py (--db monitor.db | --snaps snaps.json) [过滤/输出项]
页面变更审计追踪(Conductor Changelog 官方口径): 对每 URL 的快照时间序列做
字段级 diff → 事件流 {url, ts, change_type, property, old, new, snapshot}。
change_type 枚举: changed(属性变)/ added(新页首见)/ removed(4xx 消失)/
redirected(3xx)/ other(5xx 或不可达)。
追踪白名单: title / meta description / H1 / canonical / indexable /
noindex_source / hreflang 列表 / page type;
不追踪(官方口径"仅当前值无历史"): 入链 / 出链 / PageSpeed(出现即跳过并提示)。
选项:
  --db PATH       monitor.py 的 SQLite 库(只读;读 snapshots 表 check='pages')
  --snaps PATH    独立快照 JSON: [{url, ts, fields{...}}]
  --from DATE     窗口起(含;YYYY-MM-DD 或 ISO 时间)
  --to DATE       窗口止(含;亦是 14 天/周 粒度基准,缺省今天)
  --url SUB       URL 子串过滤(大小写不敏感)
  --type LIST     change_type 逗号列表,如 changed,added
  --summary       追加每字段变更频次表(root-cause 线索)
  --json          结构化输出(默认 markdown 时间轴)
退出码: 0 正常(含零事件) / 2 输入或参数错误。

根因联动: gsc_mining.py --decay 找到衰退页与起点日 →
  changelog.py --url <该页> --from <起点日>  即"流量下跌那天页面改了什么"清单。"""


def _die(msg):
    sys.stderr.write("[changelog] %s\n" % msg)
    sys.exit(2)


def parse_ts(s):
    """ISO 时间/日期字符串 → datetime;解析失败即输入错误(exit 2)。"""
    try:
        return datetime.fromisoformat(str(s).strip())
    except ValueError:
        _die("无法解析时间戳 %r(应为 ISO 格式,如 2026-10-10T09:00:00)" % s)


def parse_date_arg(s):
    """"2026-09-01" 或完整 ISO → date;空 → None。"""
    if not s:
        return None
    return parse_ts(s).date()


# ---------- 载入(只读) ----------

def _record(url, ts, fields, snapshot):
    fields = fields if isinstance(fields, dict) else {}
    return {"url": url, "ts": str(ts), "ts_dt": parse_ts(ts),
            "fields": fields, "status": fields.get("status"), "snapshot": snapshot}


def load_db(path):
    """monitor.py 的 monitor.db(URI 只读,绝不写入/建库)→ records。
    snapshots 表: (run_id, ts, "check"='pages', key=路径, value=指标 JSON)。"""
    if not os.path.exists(path):
        _die("数据库不存在: %s(monitor.py 的 --dir 目录下的 monitor.db)" % path)
    uri = "file:" + urllib.parse.quote(os.path.abspath(path)) + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=30.0)
    try:
        has = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='snapshots'"
        ).fetchone()
        if not has:
            _die("%s 里没有 snapshots 表(应为 monitor.py 产生的库)" % path)
        rows = conn.execute(
            'SELECT run_id, ts, key, value FROM snapshots WHERE "check"=\'pages\' '
            "ORDER BY run_id").fetchall()
    finally:
        conn.close()
    records = []
    for run_id, ts, key, value in rows:
        try:
            fields = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            continue  # 个别坏行跳过,不阻断整条审计流
        records.append(_record(key, ts, fields, run_id))
    return records


def load_snaps(path):
    """独立格式 [{url, ts, fields{...}}] → records(status 可在 fields 或顶层)。"""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        _die("读不了 %s: %s" % (path, e))
    except json.JSONDecodeError as e:
        _die("%s 不是合法 JSON: %s" % (path, e))
    if not isinstance(data, list):
        _die("%s 应为 JSON 数组: [{url, ts, fields{...}}]" % path)
    records = []
    for i, rec in enumerate(data):
        if not isinstance(rec, dict) or not rec.get("url"):
            _die("第 %d 条缺 url(格式: {url, ts, fields})" % i)
        fields = rec.get("fields") or {}
        if not isinstance(fields, dict):
            _die("第 %d 条 fields 应为对象" % i)
        if rec.get("status") is not None and "status" not in fields:
            fields = dict(fields, status=rec["status"])
        records.append(_record(rec["url"], rec.get("ts") or rec.get("date"),
                               fields, rec.get("snapshot", i)))
    return records


# ---------- 事件生成 ----------

def snapshot_class(rec):
    """快照健康分类 → ok / redirected / removed / other(5xx 或不可达)。"""
    st = rec.get("status")
    if isinstance(st, bool):
        return "ok"
    if isinstance(st, (int, float)):
        if st >= 500:
            return "other"
        if st >= 400:
            return "removed"
        if st >= 300:
            return "redirected"
        return "ok"
    if isinstance(st, str):
        s = st.strip().lower()
        if s in ("error", "timeout", "unreachable"):
            return "other"
        try:
            return snapshot_class(dict(rec, status=float(s)))
        except ValueError:
            return "ok"
    # status 缺失: monitor 网络层失败页带 {"state":"error","error":...} → 不可达
    if (rec.get("fields") or {}).get("error"):
        return "other"
    return "ok"


def status_disp(rec):
    """status 展示值: 数字原样;不可达 → "unreachable"。"""
    st = rec.get("status")
    if st is None:
        return "unreachable" if snapshot_class(rec) == "other" else None
    return st


def tracked_value(fields, prop):
    """白名单属性取值(别名归一);缺 → None。"""
    for alias, p in TRACKED_ALIASES.items():
        if p == prop and alias in fields:
            return fields[alias]
    return None


def _values_equal(a, b):
    if isinstance(a, list) and isinstance(b, list):
        return sorted(map(str, a)) == sorted(map(str, b))  # hreflang 顺序无关
    return a == b


def _event(rec, ctype, prop, old, new):
    return {"url": rec["url"], "ts": rec["ts"], "change_type": ctype,
            "property": prop, "old": old, "new": new,
            "snapshot": rec.get("snapshot")}


def generate_events(records):
    """每 URL 快照时间序列 → 事件列表 + 命中的不追踪字段名(供提示)。
    首个快照 → added;转入 4xx/3xx/5xx/不可达 → removed/redirected/other;
    两快照均 ok → 白名单字段级 diff → changed(从错误态恢复也记 changed(status))。"""
    by_url = {}
    for rec in records:
        by_url.setdefault(rec["url"], []).append(rec)
    events, skipped = [], set()
    for url in sorted(by_url):
        recs = sorted(by_url[url], key=lambda r: (r["ts_dt"], r.get("snapshot") or 0))
        prev = None
        for rec in recs:
            fields = rec["fields"]
            for k in fields:
                if k.lower() in NOT_TRACKED:
                    skipped.add(NOT_TRACKED[k.lower()])
            if prev is None:  # 新页首见
                first = fields.get("title")
                new = first if first is not None else status_disp(rec)
                events.append(_event(rec, "added", None, None, new))
            else:
                cls = snapshot_class(rec)
                if cls == "ok":
                    if snapshot_class(prev) != "ok":  # 恢复 2xx(404/500 → 200)
                        events.append(_event(rec, "changed", "status",
                                             status_disp(prev), status_disp(rec)))
                    else:  # 字段 diff 仅在两快照均 ok 时(错误态页字段不可信/缺失)
                        for prop in PROP_ORDER:
                            old = tracked_value(prev["fields"], prop)
                            new = tracked_value(fields, prop)
                            if not _values_equal(old, new):
                                events.append(_event(rec, "changed", prop, old, new))
                else:  # 进入 3xx/4xx/5xx/不可达: 单条状态事件,不 diff 字段
                    events.append(_event(rec, cls, "status",
                                         status_disp(prev), status_disp(rec)))
            prev = rec
    return events, sorted(skipped)


# ---------- 检索/粒度 ----------

def apply_filters(events, t_from=None, t_to=None, url_sub="", types=None):
    """窗(含端点)+ URL 子串 + change_type 集合过滤。"""
    out = []
    for e in events:
        d = parse_ts(e["ts"]).date()
        if t_from and d < t_from:
            continue
        if t_to and d > t_to:
            continue
        if url_sub and url_sub.lower() not in e["url"].lower():
            continue
        if types and e["change_type"] not in types:
            continue
        out.append(e)
    return out


def week_label(d):
    y, w, _ = d.isocalendar()
    return "%04d-W%02d" % (y, w)


def bucket_events(events, ref):
    """粒度【官方】: 距 ref<14 天 → 日粒度;更早 → 周粒度,同周同 URL 同字段
    折叠保留最后一次 + 计数 count。返回按 (url, ts) 排序的事件列表。"""
    daily, weeks = [], {}
    for e in events:
        d = parse_ts(e["ts"]).date()
        if (ref - d).days < 14:
            daily.append(dict(e, granularity="day", bucket=d.isoformat(), count=1))
        else:
            key = (week_label(d), e["url"], e["property"])
            weeks.setdefault(key, []).append(e)
    folded = []
    for key, grp in weeks.items():
        grp.sort(key=lambda e: (parse_ts(e["ts"]), e.get("snapshot") or 0))
        last = dict(grp[-1], granularity="week", bucket=key[0], count=len(grp))
        folded.append(last)
    out = daily + folded
    out.sort(key=lambda e: (e["url"], parse_ts(e["ts"])))
    return out


def summarize(events):
    """每字段变更频次(周折叠事件按 count 计)→ root-cause 线索。
    top_property 只在真实字段里选(added 的 "(page)" 伪字段留表不夺冠)。"""
    by_prop, by_type = {}, {}
    for e in events:
        n = e.get("count", 1)
        by_prop[e["property"] or "(page)"] = by_prop.get(e["property"] or "(page)", 0) + n
        by_type[e["change_type"]] = by_type.get(e["change_type"], 0) + n
    real = {k: v for k, v in by_prop.items() if k != "(page)"}
    top = sorted(real.items(), key=lambda kv: (-kv[1], kv[0]))[0] if real else None
    return {"by_property": by_prop, "by_change_type": by_type,
            "top_property": top[0] if top else None,
            "top_count": top[1] if top else 0}


# ---------- 渲染 ----------

def fmt_val(v):
    if v is None:
        return "(无)"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return ", ".join(str(x) for x in v) or "(空列表)"
    s = str(v).replace("|", "\\|")
    return s if len(s) <= 60 else s[:57] + "..."


def render_markdown(payload):
    lines = ["页面变更审计 changelog(Conductor Changelog 口径)"]
    win = payload["window"]
    conds = "窗 %s → %s" % (win["from"] or "(全部)", win["to"] or "(全部)")
    if win["url_filter"]:
        conds += " · url~%s" % win["url_filter"]
    if win["types"]:
        conds += " · type∈%s" % ",".join(win["types"])
    lines.append("%s · %d 事件 · %d URL · 粒度: 近14天按日,更早按周(同周同字段折叠保留最后一次+计数)"
                 % (conds, payload["n_events"], payload["n_urls"]))
    if payload["skipped_not_tracked"]:
        lines.append("")
        lines.append("[i] 不追踪字段(官方口径\"仅当前值无历史\"): %s——输入中出现,已跳过"
                     % "、".join(payload["skipped_not_tracked"]))
    events = payload["events"]
    if not events:
        lines.append("")
        lines.append("窗内无匹配事件。")
    for url in sorted({e["url"] for e in events}):
        lines.append("")
        lines.append("## %s" % url)
        lines.append("")
        lines.append("| 时间 | 类型 | 字段 | old → new |")
        lines.append("|---|---|---|---|")
        for e in [x for x in events if x["url"] == url]:
            prop = e["property"] or "(页面)"
            if e.get("count", 1) > 1:
                prop += " (×%d)" % e["count"]
            new_disp = e["new"]
            if e["change_type"] == "added" and e["new"] is not None:
                new_disp = "首见(%s)" % e["new"]
            lines.append("| %s | %s | %s | %s → %s |"
                         % (e["bucket"], e["change_type"], prop,
                            fmt_val(e["old"]), fmt_val(new_disp)))
    s = payload.get("summary")
    if s:
        lines.append("")
        lines.append("## 变更频次(--summary,root-cause 线索)")
        lines.append("")
        lines.append("| 字段 | 次数 |")
        lines.append("|---|---|")
        for k, v in sorted(s["by_property"].items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append("| %s | %d |" % (k, v))
        lines.append("")
        if s["top_property"]:
            lines.append("最多变更字段: %s(%d 次)——优先排查该字段的变更(谁在批量改它?)"
                         % (s["top_property"], s["top_count"]))
        else:
            lines.append("最多变更字段: (无——窗内只有新页首见,无字段级变更)")
        dist = " · ".join("%s %d" % (t, s["by_change_type"].get(t, 0)) for t in CHANGE_TYPES)
        lines.append("类型分布: %s" % dist)
    return "\n".join(lines)


# ---------- CLI ----------

def build_parser():
    ap = argparse.ArgumentParser(
        prog="changelog.py",
        description="页面变更审计追踪(Conductor Changelog 口径): 快照时间序列 → "
                    "字段级 diff 事件流,回答\"流量下跌那天页面改了什么\"。",
        epilog=USAGE, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--db", default="", metavar="PATH",
                     help="monitor.py 的 SQLite 库(只读;读 snapshots 表 check='pages')")
    src.add_argument("--snaps", default="", metavar="PATH",
                     help="独立快照 JSON: [{url, ts, fields{...}}]")
    ap.add_argument("--from", dest="t_from", default="", metavar="DATE",
                    help="窗口起(含;YYYY-MM-DD 或 ISO 时间)")
    ap.add_argument("--to", dest="t_to", default="", metavar="DATE",
                    help="窗口止(含;亦是 14 天/周 粒度基准,缺省今天)")
    ap.add_argument("--url", default="", metavar="SUB", help="URL 子串过滤(大小写不敏感)")
    ap.add_argument("--type", dest="types", default="", metavar="LIST",
                    help="change_type 逗号列表,如 changed,added")
    ap.add_argument("--summary", action="store_true", help="追加每字段变更频次表")
    ap.add_argument("--json", action="store_true", help="结构化输出(默认 markdown)")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    types = None
    if args.types:
        types = set()
        for t in args.types.split(","):
            t = t.strip().lower()
            if t not in CHANGE_TYPES:
                _die("未知 change_type %r(枚举: %s)" % (t, ",".join(CHANGE_TYPES)))
            types.add(t)
    records = load_db(args.db) if args.db else load_snaps(args.snaps)
    t_from = parse_date_arg(args.t_from)
    t_to = parse_date_arg(args.t_to)
    ref = t_to or date.today()
    events, skipped = generate_events(records)
    events = apply_filters(events, t_from, t_to, args.url, types)
    events = bucket_events(events, ref)
    payload = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "window": {"from": args.t_from or None, "to": args.t_to or None,
                   "url_filter": args.url or None,
                   "types": sorted(types) if types else None},
        "granularity_rule": "近14天按日;更早按周(同周同URL同字段折叠保留最后一次+计数);基准=%s"
                            % ref.isoformat(),
        "n_events": len(events),
        "n_urls": len({e["url"] for e in events}),
        "skipped_not_tracked": skipped,
        "events": events,
    }
    if args.summary:
        payload["summary"] = summarize(events)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
