#!/usr/bin/env python3
"""Googlebot 会话追踪(access.log 按需分析,非常驻;R4 监控对标③,pipeline-completeness §五)。

把服务器访问日志按 IP + UA 前缀 + 时间窗拼成"一次爬取会话",回答排障三问:
Googlebot 这趟从哪进 / 爬了多深 / 有没有掉进陷阱(facet 参数循环、超深路径、超长会话)。
适用:收录异常排查、爬虫陷阱定位、算法更新事后取证(与 templates/monitor/postmortem.md
时间线互证;对拍 Google Search Console 的"抓取统计信息"会话口径)。

会话口径(排序+窗口切分):
  - 先按 --ua 过滤(UA 内词边界前缀匹配,大小写不敏感;默认 Googlebot;
    --ua "" = 不过滤,用于 CLF 行——CLF 无 UA 字段,默认过滤会全部漏掉)
  - 按 (IP, 时刻) 排序后线性扫描(日志乱序安全:先排序再切分):
    同 IP 且与上一条间隔 ≤ --window → 同一会话;间隔 > window 或换 IP → 新会话
  - 每会话输出:入口页(首条路径)/页数(去 query 去重后的路径数)/最大深度
    (URL 路径段数,根页 "/"=1)/离开页(末条路径)/命中率(200 占比)
  - 陷阱特征三判(严格大于,任一命中即标记):
      param_loop   同一路径带参数的请求 >10 次(筛选/facet 参数循环)
      deep_crawl   会话内出现路径深度 >8 的请求
      volume       会话请求总数 >500

汇总:会话数 / 平均最大深度 / 陷阱会话清单 / Top 入口页(--top N,默认 10)。

日志格式:apache/nginx combined 与 CLF(无 referer/UA 字段)两种都解析
(正则与 ai_referral_log.py 同源);解析失败的行计数上报,不猜。

用法:
  python3 log_session.py --log access.log                              # Googlebot/30m/markdown
  python3 log_session.py --log access.log --ua Googlebot --window 30m --json
  python3 log_session.py --log access.log --ua "" --window 1h          # 不过滤 UA(CLF 行)
  python3 log_session.py --self-test
"""
import argparse
import json
import re
import sys
import traceback
from collections import Counter
from datetime import datetime
from urllib.parse import urlsplit

# combined/CLF 共用(ip ident user [ts] "req" status bytes ["referer" ["ua"]]——
# 尾部两组可选,CLF 无 referer/UA 也能命中;与 ai_referral_log.LOG_RE 同源)
LOG_RE = re.compile(
    r'^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"([^"]*)"\s+(\d{3})\s+\S+'
    r'(?:\s+"([^"]*)"\s+"([^"]*)")?')

# 陷阱阈值(pipeline-completeness 监控对标③规格:同路径参数循环>10 次/深度>8/会话>500 请求)
PARAM_LOOP_LIMIT = 10     # 同一路径带参数请求超过该数 → param_loop
DEPTH_LIMIT = 8           # 路径深度超过该数 → deep_crawl
VOLUME_LIMIT = 500        # 会话请求总数超过该数 → volume

WINDOW_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*([smhd]?)$", re.I)
WINDOW_UNITS = {"": 60.0, "s": 1.0, "m": 60.0, "h": 3600.0, "d": 86400.0}


def parse_window(spec):
    """'30m'/'90s'/'2h'/'1d'/裸数字(=分钟)→ 秒;非法 → None。"""
    m = WINDOW_RE.match((spec or "").strip())
    if not m:
        return None
    return float(m.group(1)) * WINDOW_UNITS[m.group(2).lower()]


def parse_ts(ts):
    """CLF 时间 '12/Oct/2026:10:00:00 +0000' → aware datetime;失败 → None。"""
    try:
        return datetime.strptime(ts, "%d/%b/%Y:%H:%M:%S %z")
    except (ValueError, TypeError):
        return None


def ua_matches(ua, prefix):
    """UA 前缀匹配:词边界起点(不命中 'Smartbot'/'xGooglebot');prefix 空 = 全过。"""
    if not prefix:
        return True
    return re.search(r"(?<![\w-])" + re.escape(prefix), ua or "", re.I) is not None


def path_depth(path):
    """URL 路径深度 = 非空路径段数,根页 "/" 记 1(任何真实页面至少一层)。"""
    return max(1, len([s for s in (path or "/").split("/") if s]))


def parse_line(line):
    """一行 combined/CLF → 记录 dict;解析失败/时间非法 → None(调用方计数,不猜)。"""
    m = LOG_RE.match((line or "").strip())
    if not m:
        return None
    ip, ts_raw, request, status, _referer, ua = m.groups()
    ts = parse_ts(ts_raw)
    if ts is None:
        return None
    parts = (request or "").split(" ")
    target = parts[1] if len(parts) >= 2 else (parts[0] if parts else "-")
    sp = urlsplit(target)
    try:
        st = int(status)
    except (TypeError, ValueError):
        return None
    return {"ip": ip, "ts": ts, "path": sp.path or "/", "query": sp.query,
            "status": st, "ua": ua or "-"}


def build_sessions(records, window_sec):
    """已过滤记录 → 会话列表(按 (ip, ts) 排序后窗口切分;间隔>window 或换 IP 断开)。"""
    sessions = []
    for rec in sorted(records, key=lambda r: (r["ip"], r["ts"])):
        if sessions and sessions[-1]["ip"] == rec["ip"] \
                and (rec["ts"] - sessions[-1]["ts_last"]).total_seconds() <= window_sec:
            cur = sessions[-1]
            cur["requests"].append(rec)
            cur["ts_last"] = rec["ts"]
        else:
            sessions.append({"ip": rec["ip"], "requests": [rec],
                             "ts_first": rec["ts"], "ts_last": rec["ts"]})
    return [session_metrics(s) for s in sessions]


def session_metrics(sess):
    """原始会话 → 指标 dict(入口/页数/最大深度/离开/命中率/陷阱特征)。"""
    reqs = sess["requests"]
    paths = [r["path"] for r in reqs]
    param_hits = Counter(r["path"] for r in reqs if r["query"])
    max_depth = max(path_depth(p) for p in paths)
    traps, detail = [], {}
    worst_path, worst_n = max(param_hits.items(), key=lambda kv: kv[1]) if param_hits else ("", 0)
    if worst_n > PARAM_LOOP_LIMIT:
        traps.append("param_loop")
        detail["param_loop"] = {"path": worst_path, "param_requests": worst_n}
    if max_depth > DEPTH_LIMIT:
        traps.append("deep_crawl")
        detail["deep_crawl"] = {"max_depth": max_depth}
    if len(reqs) > VOLUME_LIMIT:
        traps.append("volume")
        detail["volume"] = {"requests": len(reqs)}
    return {
        "ip": sess["ip"],
        "start": sess["ts_first"].isoformat(),
        "end": sess["ts_last"].isoformat(),
        "requests": len(reqs),
        "pages": len(set(paths)),                       # 去 query 去重
        "max_depth": max_depth,
        "entry": paths[0],
        "exit": paths[-1],
        "hit_rate": round(sum(1 for r in reqs if r["status"] == 200) / len(reqs), 3),
        "traps": traps,
        "trap_detail": detail,
    }


def analyze(lines, ua_prefix, window_sec):
    """日志行迭代器 → 结果 dict(parsed/matched/unparsed + sessions + summary)。"""
    records, unparsed = [], 0
    for line in lines:
        if not (line or "").strip():
            continue
        rec = parse_line(line)
        if rec is None:
            unparsed += 1
            continue
        records.append(rec)
    matched = [r for r in records if ua_matches(r["ua"], ua_prefix)]
    sessions = build_sessions(matched, window_sec)
    entry_counter = Counter(s["entry"] for s in sessions)
    trap_sessions = [{"ip": s["ip"], "start": s["start"], "traps": s["traps"]}
                     for s in sessions if s["traps"]]
    return {
        "ua_filter": ua_prefix,
        "window_seconds": window_sec,
        "parsed": len(records),
        "matched": len(matched),
        "unparsed": unparsed,
        "sessions": sessions,
        "summary": {
            "session_count": len(sessions),
            "avg_max_depth": round(sum(s["max_depth"] for s in sessions) / len(sessions), 1)
            if sessions else 0.0,
            "trap_session_count": len(trap_sessions),
            "trap_sessions": trap_sessions,
            "top_entries": entry_counter.most_common(),
        },
    }


def render_markdown(res, top):
    """结果 → markdown 汇总(每会话一行明细 + 陷阱清单 + Top 入口页)。"""
    s = res["summary"]
    lines = ["# Googlebot 会话追踪",
             "",
             "- 日志: 解析 %d 行 / 匹配 UA %r %d 行 / 解析失败 %d 行"
             % (res["parsed"], res["ua_filter"], res["matched"], res["unparsed"]),
             "- 窗口: %g 秒 · 会话数: %d · 平均最大深度: %s · 陷阱会话: %d"
             % (res["window_seconds"], s["session_count"], s["avg_max_depth"],
                s["trap_session_count"]),
             ""]
    if res["matched"] == 0:
        lines.append("UA 过滤后 0 行命中:CLF 日志无 UA 字段时用 `--ua \"\"`;"
                     "或该 UA 在日志期未到访(不猜,如实报 0)。")
        return "\n".join(lines) + "\n"
    lines += ["## 会话明细", "",
              "| IP | 开始 | 请求 | 页数 | 最大深度 | 入口 | 离开 | 命中率 | 陷阱 |",
              "|---|---|---|---|---|---|---|---|---|"]
    for x in res["sessions"]:
        lines.append("| %s | %s | %d | %d | %d | %s | %s | %.1f%% | %s |"
                     % (x["ip"], x["start"], x["requests"], x["pages"], x["max_depth"],
                        x["entry"], x["exit"], x["hit_rate"] * 100,
                        ",".join(x["traps"]) or "-"))
    lines += ["", "## 陷阱会话清单", ""]
    if s["trap_sessions"]:
        for t in s["trap_sessions"]:
            lines.append("- %s(开始 %s): %s" % (t["ip"], t["start"], ",".join(t["traps"])))
    else:
        lines.append("(无 param_loop/deep_crawl/volume 命中)")
    lines += ["", "## Top 入口页(top %d)" % top, "", "| 入口页 | 会话数 |", "|---|---|"]
    for path, n in s["top_entries"][:top]:
        lines.append("| %s | %d |" % (path, n))
    return "\n".join(lines) + "\n"


def _self_test():
    """合成日志自检:窗口切分边界/三陷阱判定/UA 过滤/CLF 解析(测试层另有 19 例)。"""
    base = '66.249.66.1 - - [12/Oct/2026:10:00:00 +0000] "GET %s HTTP/1.1" %d 1024 "-" "%s"'
    gbot = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    rows = [
        base % ("/a", 200, gbot),
        '66.249.66.1 - - [12/Oct/2026:10:30:00 +0000] "GET /b HTTP/1.1" 200 1024 "-" "%s"' % gbot,
        '66.249.66.1 - - [12/Oct/2026:11:00:01 +0000] "GET /c HTTP/1.1" 404 1024 "-" "%s"' % gbot,
        base % ("/x", 200, "Mozilla/5.0 (compatible; bingbot/2.0)"),
    ]
    res = analyze(rows, "Googlebot", 30 * 60)
    assert [s["requests"] for s in res["sessions"]] == [2, 1], res["sessions"]  # 间隔恰=窗口并入,>窗口切开
    assert res["summary"]["session_count"] == 2 and res["matched"] == 3
    assert res["sessions"][0]["hit_rate"] == 1.0 and res["sessions"][1]["hit_rate"] == 0.0
    deep = analyze([base % ("/" + "/".join("d%d" % i for i in range(9)), 200, gbot)],
                   "Googlebot", 1800)
    assert deep["sessions"][0]["traps"] == ["deep_crawl"], deep["sessions"][0]
    vol = analyze([base % ("p", 200, gbot)] * 501, "Googlebot", 60)
    assert vol["sessions"][0]["traps"] == ["volume"]
    clf = analyze(['10.0.0.1 - - [12/Oct/2026:10:00:00 +0000] "GET /z HTTP/1.1" 200 512'],
                  "", 1800)
    assert clf["summary"]["session_count"] == 1 and clf["sessions"][0]["entry"] == "/z"
    print("self-test OK")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Googlebot 会话追踪:access.log 按 IP+UA 前缀+时间窗拼会话,输出入口/深度/命中率/陷阱特征"
                    "(param_loop>10 同路径参数请求、deep_crawl 深度>8、volume>500 请求)")
    ap.add_argument("--log", help="访问日志路径(CLF/combined;- 读 stdin)")
    ap.add_argument("--ua", default="Googlebot",
                    help='UA 前缀过滤(词边界匹配,默认 Googlebot;空串 "" = 不过滤,CLF 行用)')
    ap.add_argument("--window", default="30m",
                    help="会话切分窗口(如 30m/90s/2h/1d,裸数字=分钟;间隔≤窗口算同一会话)")
    ap.add_argument("--top", type=int, default=10, help="Top 入口页条数(默认 10)")
    ap.add_argument("--json", action="store_true", help="JSON 输出(默认 markdown)")
    ap.add_argument("--self-test", action="store_true", help="内置自检(合成日志)")
    args = ap.parse_args(argv)

    if args.self_test:
        _self_test()
        return 0
    window_sec = parse_window(args.window)
    if window_sec is None or window_sec <= 0:
        print("错误: --window 无法解析(期望 30m/90s/2h/1d 或裸数字分钟): %r" % args.window,
              file=sys.stderr)
        return 4
    if not args.log:
        print("错误: 需要 --log FILE(或 - 读 stdin;--self-test 自检)", file=sys.stderr)
        return 4
    try:
        if args.log == "-":
            lines = sys.stdin.readlines()
        else:
            with open(args.log, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
    except OSError as e:
        print("错误: 读日志失败 %s: %s" % (args.log, e), file=sys.stderr)
        return 4
    res = analyze(lines, args.ua, window_sec)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(res, max(1, args.top)), end="")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:                                   # pragma: no cover
        traceback.print_exc()
        sys.exit(3)
