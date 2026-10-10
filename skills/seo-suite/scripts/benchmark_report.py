#!/usr/bin/env python3
"""匿名基准聚合器(State of GEO 式,stdlib only)。
把多站的审计/监控分数聚合成一张匿名分布报告(borrow-specs E8:"State of GEO 式
基准可由 monitor.db 匿名聚合,报告照抄其偏差自白")。三种输入可任组合:
  --audits DIR        目录内每个 *.json = 一站(site_audit.py --json 输出)
  --monitor-db PATH   monitor.py 的 monitor.db(可重复传,每个 = 一站);--period 按月选 run
  --scores FILE       CSV(列: site,score[,ai_search_health];site 列读入即丢弃)
聚合:样本数 N 站 / 主分分布 P25·P50·P75·均值 / AI Search Health 分布 /
Top 失败规则频次(按"命中站数"排序,哪类问题最普遍)/ ASCII 分位数条形。

主分口径(按来源):
  audits    【Ahrefs 官方,与 health_score.py 同公式】(无 CRITICAL 的 URL 数÷可评分
            URL 数)×100;fetch guard 拒审(verdict=refused/SKIP)不进分母;
            AI 子分 = 站内各 URL ai_search_health.score 的均值。
  monitor-db 一次 run 的标准检查组 ok 占比:ok/(ok+error)×100;skipped/blocked/
            unparseable/budget_skipped 属"缺数据"(Lumar N/A 语义)不计分母不罚分;
            key_pages 不进主分(各站配置页数不同,跨站权重不可比)。
  scores    外部给定(0-100),不重算。

== 匿名化纪律(强制)==
只聚合数字:站点标识——audits results 的 URL 键、monitor summary 的 site 字段、
CSV 的 site 列、输入文件名——在解析时即丢弃,绝不进入任何输出(含 --json);
输出仅含统计量与规则 id(site_audit 的 area / monitor 的告警 code)。
错误提示只报"第 i 个输入",不回显文件名(文件名可能就是域名)。

== 偏差自白(geo-optimizer 纪律,报告首尾各一次,照抄) ==
**自选样本(主动跑审计的团队),方向性信号而非全网普查**;样本随时间增长,历史报告可比性递减

用法: python3 benchmark_report.py --audits dir/ [--monitor-db a.db ...] [--scores s.csv]
              [--period 2026-10] [--min-sites 5] [--json] [--out [benchmark-YYYYMM.md]]
退出码: 0 正常 / 2 输入错误或样本 < --min-sites(拒绝出报告)。"""
import argparse
import csv
import json
import math
import os
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime

SCHEMA_VERSION = 1            # --json 顶层 schema 版本(评分契约,borrow-specs E8)
DEFAULT_MIN_SITES = 5         # 样本<5 拒绝出报告(小样本分位数误导)
TOP_RULES = 10                # Top 失败规则条数
BAR_WIDTH = 20                # ASCII 条形宽度(字符)
FAIL_SEVS = ("CRITICAL", "WARN")          # audits 进失败频次的严重度(INFO=提示不进)
MON_FAIL_LEVELS = ("critical", "warn")    # monitor 告警进失败频次的级别
PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
# monitor 检查组状态:ok=通过;"缺数据"态不计分母(Lumar N/A 语义,与
# monitor.py 的 skipped/blocked/unparseable/budget_skipped 一致);其余含 error=失败。
MON_NA_STATES = frozenset(("skipped", "blocked", "unparseable", "budget_skipped", "no_data"))
# 偏差自白原文(borrow-specs E8 照抄;报告首尾各一次)
BIAS_CONFESSION = ("**自选样本(主动跑审计的团队),方向性信号而非全网普查**;"
                   "样本随时间增长,历史报告可比性递减")


def die(msg, code=2):
    """输入/参数错误 → stderr + 退出(与 health_score.py 同纪律:2=输入侧错误)。"""
    sys.stderr.write(msg + "\n")
    sys.exit(code)


# ---------- 统计基元(纯函数,测试钉死) ----------

def percentile(vals, p):
    """线性插值分位数(n=1 时三点同值;空列表 None)。"""
    s = sorted(v for v in vals if v is not None)
    if not s:
        return None
    if len(s) == 1:
        return float(s[0])
    k = (len(s) - 1) * p / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return float(s[int(k)])
    return float(s[lo] + (s[hi] - s[lo]) * (k - lo))


def stats_block(vals):
    """[0-100] 分数列表 → {n,min,p25,p50,p75,mean,max}(1 位小数);空 → None。"""
    vs = [float(v) for v in vals if v is not None]
    if not vs:
        return None
    r = lambda x: round(x, 1)   # noqa: E731  (局部圆整助手)
    return {"n": len(vs), "min": r(min(vs)), "max": r(max(vs)),
            "p25": r(percentile(vs, 25)), "p50": r(percentile(vs, 50)),
            "p75": r(percentile(vs, 75)), "mean": r(sum(vs) / len(vs))}


def ascii_bar(value, width=BAR_WIDTH):
    """0-100 值 → 定宽 ASCII 条(#=实,.=空);越界值截到 [0,100]。"""
    v = 0.0 if value is None else max(0.0, min(100.0, float(value)))
    fill = int(round(v / 100.0 * width))
    return "#" * fill + "." * (width - fill)


def top_failed_rules(samples, limit=TOP_RULES):
    """按"命中站数"聚合失败规则(哪类问题最普遍);并列按规则名排序(确定性)。
    samples: [{main, ai, rules:set}, ...];share 分母 = 全部样本 N(含无规则站)。"""
    n = len(samples)
    cnt = Counter()
    for s in samples:
        for rule in s.get("rules") or ():
            cnt[rule] += 1
    ranked = sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    return [{"rule": r, "sites": c, "share": round(c / n, 3) if n else 0.0}
            for r, c in ranked]


# ---------- 输入解析(匿名化纪律:标识在此丢弃) ----------

def _parse_audit_blob(text):
    """site_audit --json 输出(文件前部可能混有逐 URL 文本行)→ 含 results 的 dict。
    与 health_score.load_audit 同策略:从每个 '{' 试解,取末位含 results 字典者。"""
    try:
        cand = json.loads(text)
        if isinstance(cand, dict) and isinstance(cand.get("results"), dict):
            return cand
    except json.JSONDecodeError:
        pass
    found = None
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            cand = json.loads(text[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(cand, dict) and isinstance(cand.get("results"), dict):
            found = cand   # 末位的完整 blob 赢过早位的 meta 行片段
    return found


def sample_from_audit(data):
    """一站的 audit JSON → sample;无可评分 URL(全拒审/空)→ None。
    匿名化:results 的 URL 键只作遍历索引,绝不落入返回值。"""
    scored = []        # (has_critical, rules, ai_score)
    for url, r in (data.get("results") or {}).items():   # url 丢弃
        if not isinstance(r, dict):
            continue
        findings = r.get("findings") or []
        if r.get("verdict") == "refused" or any(f.get("severity") == "SKIP" for f in findings):
            continue                    # 拒审≠失败,不进分母【site_audit 官方语义】
        rules = {f.get("area") for f in findings
                 if f.get("severity") in FAIL_SEVS and f.get("area")}
        ai = (r.get("ai_search_health") or {}).get("score")
        scored.append((any(f.get("severity") == "CRITICAL" for f in findings), rules, ai))
    if not scored:
        return None
    crit = sum(1 for c, _, _ in scored if c)
    ai_vals = [a for _, _, a in scored if isinstance(a, (int, float))]
    return {"main": round((len(scored) - crit) / len(scored) * 100, 1),
            "ai": round(sum(ai_vals) / len(ai_vals), 1) if ai_vals else None,
            "rules": set().union(*(rg for _, rg, _ in scored)) if scored else set()}


def load_audits(dirpath, skipped):
    """目录内 *.json 各 = 一站;坏文件计 skipped['unparsable'](提示按序号,不报文件名)。"""
    samples = []
    try:
        names = sorted(n for n in os.listdir(dirpath)
                       if n.lower().endswith(".json")
                       and os.path.isfile(os.path.join(dirpath, n)))
    except OSError as e:
        die("错误: 读不了审计目录 %s: %s" % (dirpath, e))
    for i, name in enumerate(names, 1):     # name 丢弃(可能是域名)
        try:
            with open(os.path.join(dirpath, name), encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            skipped["unparsable"] += 1
            sys.stderr.write("[!] 第 %d 个审计文件读不了: %s\n" % (i, type(e).__name__))
            continue
        data = _parse_audit_blob(text)
        sample = sample_from_audit(data) if data else None
        if sample is None:
            skipped["unparsable"] += 1
            sys.stderr.write("[!] 第 %d 个审计文件解析不出可评分 URL(site_audit --json 输出?)\n" % i)
            continue
        samples.append(sample)
    return samples


def _month_sql(period):
    """period '2026-10' → SQL LIKE 参数 '2026-10%'(ts 为 ISO 文本,前缀可比)。"""
    return period + "%"


def run_score_from_summary(summary_text):
    """run.summary JSON → 主分(ok/(ok+error)×100);缺数据态不计分母。
    匿名化:summary 首字段即 site URL,只取 checks 各组 state,其余全丢。"""
    try:
        payload = json.loads(summary_text or "")
    except (json.JSONDecodeError, TypeError):
        return None
    checks = payload.get("checks") if isinstance(payload, dict) else None
    if not isinstance(checks, dict) or not checks:
        return None
    ok = fail = 0
    for grp, v in checks.items():          # grp=检查组名(robots/home/...),非标识
        state = (v or {}).get("state") if isinstance(v, dict) else None
        if state == "ok":
            ok += 1
        elif state in MON_NA_STATES:
            continue                       # 缺数据=N/A 不罚分(Lumar 语义)
        elif state and "error" in str(state):
            fail += 1
    denom = ok + fail
    return round(ok / denom * 100, 1) if denom else None


def load_monitor_db(path, period, skipped):
    """一个 monitor.db = 一站:取周期内(默认不限)最新 status='ok' 的 run 当样本;
    失败规则 = 周期窗内该站触发过的 critical/warn 告警 code(suppressed 不计)。
    匿名化:runs.summary 的 site、config 均不读出库,只取检查态与告警 code。"""
    if not os.path.exists(path):
        die("错误: monitor-db 不存在: %s" % path)
    try:
        # 只读语义靠"仅 SELECT"保证(存在性已先验,不会误建空库);不用 file: URI,
        # 避免路径含 ?/# 等保留字符时被当 URI 转义。
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        runs = conn.execute(
            "SELECT id, ts, summary FROM runs WHERE status='ok' ORDER BY id DESC").fetchall()
    except sqlite3.Error as e:
        die("错误: %s 不是可读的 monitor.db(runs 表缺失?): %s" % (path, e))
    try:
        window = [r for r in runs if not period or str(r["ts"] or "").startswith(period)]
        if not window:
            skipped["no_qualifying_run"] += 1
            sys.stderr.write("[!] 一个 monitor-db 在周期 %s 内无 ok run,跳过(不猜分)\n"
                             % (period or "全部"))
            return None
        latest, main = None, None
        for r in window:                     # 新→旧,取首个可评分 run(空 summary 的陈旧 run 跳过)
            main = run_score_from_summary(r["summary"])
            if main is not None:
                latest = r
                break
        if latest is None:
            skipped["no_qualifying_run"] += 1
            sys.stderr.write("[!] 一个 monitor-db 在周期 %s 内的 ok run 均无可评分检查态,跳过\n"
                             % (period or "全部"))
            return None
        # 失败规则:窗口内(周期=该月;无周期=全部 ok run)该站触发过的告警 code
        ids = [r["id"] for r in window]
        marks = ",".join("?" * len(ids))
        levels = ",".join("?" * len(MON_FAIL_LEVELS))
        codes = {row["code"] for row in conn.execute(
            "SELECT DISTINCT a.code FROM alerts a WHERE a.suppressed=0 "
            "AND a.level IN (%s) AND a.run_id IN (%s)" % (levels, marks),
            (*MON_FAIL_LEVELS, *ids))}
        return {"main": main, "ai": None, "rules": codes}   # monitor 无 AI 子分
    finally:
        conn.close()


def load_scores_csv(path, skipped):
    """CSV(列 site,score[,ai_search_health]) → samples。
    匿名化:site 列读入即丢弃(仅确认列在场);坏行按行号提示。"""
    if not os.path.exists(path):
        die("错误: scores CSV 不存在: %s" % path)
    samples = []
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            cols = {(c or "").strip().lower() for c in (reader.fieldnames or [])}
            if "site" not in cols or "score" not in cols:
                die("错误: scores CSV 需含 site,score 列(实际表头: %s)"
                    % ",".join(sorted(c for c in cols if c)))
            for ln, row in enumerate(reader, 2):    # 表头后第 1 数据行 = 行号 2
                try:
                    score = float((row.get("score") or "").strip())
                    if not 0 <= score <= 100:
                        raise ValueError
                    raw_ai = (row.get("ai_search_health") or "").strip()
                    ai = round(float(raw_ai), 1) if raw_ai else None
                    if ai is not None and not 0 <= ai <= 100:
                        raise ValueError
                except (TypeError, ValueError):
                    skipped["bad_rows"] += 1
                    sys.stderr.write("[!] scores CSV 第 %d 行 score/ai_search_health 非法,跳过\n" % ln)
                    continue
                # row["site"] 存在性由表头保证;值到此即弃,不进 sample
                samples.append({"main": round(score, 1), "ai": ai, "rules": set()})
    except OSError as e:
        die("错误: 读不了 scores CSV: %s" % e)
    return samples


# ---------- 报告渲染 ----------

def _dist_lines(block, label):
    """一个分布块 → markdown 行(统计行 + 四条 ASCII 分位数条形)。"""
    if not block:
        return ["- %s: 无数据(monitor-db 来源不产 AI 子分/CSV 未提供)" % label]
    lines = ["- %s: P25 %s / P50 %s / P75 %s / 均值 %s(最小 %s ~ 最大 %s,n=%d)"
             % (label, block["p25"], block["p50"], block["p75"], block["mean"],
                block["min"], block["max"], block["n"])]
    for key, name in (("p25", "P25"), ("p50", "P50"), ("p75", "P75"), ("mean", "均值")):
        lines.append("  %s %6s |%s" % (name, block[key], ascii_bar(block[key])))
    return lines


def build_markdown(payload):
    """聚合结果 → 匿名基准报告(偏差自白首尾各一次)。"""
    p = payload
    head = "# 匿名基准报告(State of GEO 式)%s\n\n> 偏差自白:%s" % (
        ("· " + p["period"]) if p["period"] else "", BIAS_CONFESSION)
    lines = [head]
    lines.append("")
    lines.append("## 样本")
    src = p["by_source"]
    lines.append("- 样本数 **%d 站**(audits %d / monitor-db %d / scores %d)"
                 % (p["n_sites"], src["audits"], src["monitor_db"], src["scores"]))
    sk = p["skipped"]
    if any(sk.values()):
        lines.append("- 跳过: 解析失败 %d / 无合格 run %d / 坏行 %d"
                     % (sk["unparsable"], sk["no_qualifying_run"], sk["bad_rows"]))
    lines.append("- 采样窗: %s" % (p["period"] or "全部(未指定 --period)"))
    lines.append("")
    lines.append("## 主分分布(0-100)")
    lines.extend(_dist_lines(p["main"], "主分"))
    lines.append("")
    lines.append("## AI Search Health 分布")
    lines.extend(_dist_lines(p["ai_search_health"], "AI 子分"))
    lines.append("")
    lines.append("## Top 失败规则(按命中站数;哪类问题最普遍)")
    rules = p["top_failed_rules"]
    if rules:
        lines.append("| 规则 | 命中站数 | 占比 |")
        lines.append("|---|---|---|")
        for r in rules:
            lines.append("| %s | %d/%d | %.1f%% |"
                         % (r["rule"], r["sites"], p["n_sites"], r["share"] * 100))
    else:
        lines.append("- 无失败规则记录")
    lines.append("")
    lines.append("## 方法与匿名化")
    lines.append("- 只聚合数字:站点标识(URL/域名/site 列/文件名)解析时即丢弃,输出仅含统计量与规则 id")
    lines.append("- 主分口径: audits=Ahrefs 公式(无 CRITICAL URL 占比,拒审不进分母)/ "
                 "monitor-db=检查组 ok 占比(缺数据态按 N/A 剔除)/ scores=外部给定")
    lines.append("- 失败规则: audits=CRITICAL+WARN 的 area / monitor-db=critical+warn 告警 code"
                 "(suppressed 不计),按『命中站数』而非出现次数计数")
    lines.append("")
    lines.append("> 偏差自白:%s" % BIAS_CONFESSION)
    return "\n".join(lines) + "\n"


def build_payload(samples, by_source, skipped, period, min_sites):
    """samples → 聚合 payload(markdown 与 --json 共用,全匿名)。"""
    main_vals = [s["main"] for s in samples if s.get("main") is not None]
    ai_vals = [s["ai"] for s in samples if s.get("ai") is not None]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "period": period,
        "min_sites": min_sites,
        "n_sites": len(samples),
        "by_source": by_source,
        "skipped": skipped,
        "main": stats_block(main_vals),
        "ai_search_health": stats_block(ai_vals),
        "top_failed_rules": top_failed_rules(samples),
        "bias_confession": BIAS_CONFESSION,
    }


# ---------- CLI ----------

def build_parser():
    ap = argparse.ArgumentParser(
        prog="benchmark_report.py",
        description="匿名基准聚合(State of GEO 式):多站分数 → 分布报告,"
                    "偏差自白照抄 geo-optimizer 纪律,输出绝不含 URL/域名。",
        epilog="示例: benchmark_report.py --audits audits/ --scores s.csv --json | "
               "benchmark_report.py --monitor-db a.db --monitor-db b.db --period 2026-10 "
               "--out  (默认文件名 benchmark-YYYYMM.md)")
    ap.add_argument("--audits", metavar="DIR",
                    help="审计目录:每个 *.json = 一站(site_audit.py --json 输出)")
    ap.add_argument("--monitor-db", metavar="DB", action="append", default=[],
                    help="monitor.py 的 monitor.db(可重复传多个,每个 = 一站)")
    ap.add_argument("--scores", metavar="CSV",
                    help="分数 CSV(列: site,score[,ai_search_health];site 读取后即弃)")
    ap.add_argument("--period", metavar="YYYY-MM",
                    help="monitor-db 模式按月过滤(选该月最新 ok run);亦标注在报告头")
    ap.add_argument("--min-sites", type=int, default=DEFAULT_MIN_SITES, metavar="N",
                    help="最小样本数,低于即拒绝出报告(默认 %d,退出码 2)" % DEFAULT_MIN_SITES)
    ap.add_argument("--json", action="store_true", help="结构化 JSON 输出(全匿名)")
    ap.add_argument("--out", nargs="?", const="auto", metavar="FILE",
                    help="写文件而非 stdout;裸 --out = benchmark-YYYYMM.md(周期月)")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not (args.audits or args.monitor_db or args.scores):
        die("错误: 需至少一种输入(--audits / --monitor-db / --scores);--help 看口径")
    if args.period and not PERIOD_RE.match(args.period):
        die("错误: --period 需为 YYYY-MM(如 2026-10)")
    if args.min_sites < 1:
        die("错误: --min-sites 需 ≥1")
    if args.json and args.out:
        die("错误: --json 与 --out 互斥(stdout 只能有一个去向)")

    skipped = {"unparsable": 0, "no_qualifying_run": 0, "bad_rows": 0}
    samples, by_source = [], {"audits": 0, "monitor_db": 0, "scores": 0}
    if args.audits:
        got = load_audits(args.audits, skipped)
        by_source["audits"] = len(got)
        samples += got
    for db in args.monitor_db:
        got = load_monitor_db(db, args.period, skipped)
        if got:
            by_source["monitor_db"] += 1
            samples.append(got)
    if args.scores:
        got = load_scores_csv(args.scores, skipped)
        by_source["scores"] = len(got)
        samples += got

    if len(samples) < args.min_sites:
        die("错误: 样本 %d 站 < 最小样本阈值 %d,拒绝出报告——小样本分位数误导;"
            "偏差自白:%s\n(合并更多来源或显式 --min-sites %d 降低门槛后重试)"
            % (len(samples), args.min_sites, BIAS_CONFESSION, max(1, len(samples))))

    payload = build_payload(samples, by_source, skipped, args.period, args.min_sites)
    body = json.dumps(payload, ensure_ascii=False, indent=1) if args.json \
        else build_markdown(payload)

    if args.out:
        fname = args.out
        if fname == "auto":
            month = (args.period or datetime.now().strftime("%Y-%m")).replace("-", "")
            fname = "benchmark-%s.md" % month
        with open(fname, "w", encoding="utf-8") as f:
            f.write(body if body.endswith("\n") else body + "\n")
        sys.stderr.write("[i] 报告已写入 %s(匿名聚合,含偏差自白)\n" % fname)
    else:
        print(body, end="" if body.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
