#!/usr/bin/env python3
"""自有词集 SERP 波动分(Semrush Sensor 口径的自有词集版,stdlib-only)。

对多日排名数据(GSC 导出或 Date,Query,Position 三列表)计算逐日 SERP 波动分:
  D_k     = |pos_{d-1} - pos_d| / 20   (Top-20 口径[推断]:≥20 位变动按满幅 1.0 计)
            丢失(前日有今日无)= 1.0;新进(前日无今日有)= 1.0
  score_d = clamp(round(10 × mean_k(D_k), 1), 0, 10)   (线性缩放)
分档【Semrush 官方】: 0-2 low / 2-5 normal / 5-8 high / 8-10 very high;
score ≥ 8 触发"疑似重大算法更新"提示。
deviation(Sensor Deviations 口径[推断]): z30(d) = (score_d − mean(前置≤30 天窗)) / std,
基线 <2 天或 std=0 → null;|z| ≥ 2 标异常日。
公式注释:Semrush 官方公式未公开,此为对齐其分档的自研口径。

--context 模式:供 monitor.py 的 gsc/visibility 类告警作 source 调用,输出单行
JSON {date,score,band,z30,verdict};verdict=high_volatility(score≥8 或 |z30|≥2)时
在告警 message 里附注"当日 SERP 高波动(z=+X.X),疑似算法更新而非站点问题"。

用法:
  python3 sensor_volatility.py --gsc gsc.csv                  # GSC 导出(列含 Date/Query/Position,可含 Clicks/Impressions/CTR)
  python3 sensor_volatility.py --positions pos.csv [--json]   # Date,Query,Position 三列
  python3 sensor_volatility.py --gsc gsc.csv --context --date 2026-10-09
  python3 sensor_volatility.py --gsc gsc.csv --top 20         # Top 涨跌查询条数
退出码:0 正常;2 用法/数据错误(单日数据无法算波动、缺列、--date 无分数等)。
词集 <10 个查询 → 警告"词集过小,分数不稳定"(stderr + 输出内均带)。
"""
import argparse
import csv
import json
import sys
from datetime import datetime

POS_SCALE = 20.0        # Top-20 口径:分母 N[推断]
Z_WINDOW = 30           # deviation 基线窗(近 30 天)
Z_THRESHOLD = 2.0       # |z|≥2 = 异常日
Z_MIN_BASELINE = 2      # 基线至少 2 天才有 std
MIN_QUERIES = 10        # 词集过小警告阈值
CHART_MAX_COLS = 60     # ASCII 图最多列数

BAND_EDGES = [(2.0, "low"), (5.0, "normal"), (8.0, "high"), (float("inf"), "very high")]
BANDS_DOC = "0-2 low / 2-5 normal / 5-8 high / 8-10 very high"

DATE_COLS = ("date", "日期")
QUERY_COLS = ("query", "top queries", "keyword", "查询", "关键字")
POS_COLS = ("position", "avg. position", "avg position", "排名", "平均排名")

METHOD = ("D_k=|pos_{d-1}-pos_d|/20(Top-20 口径:丢失=新进=1.0,单查询≥20 位变动按 1.0 计);"
          "score=clamp(round(10×mean_k(D_k),1),0,10);"
          "z30=(score−前置≤30 天均值)/std(基线<2 天或 std=0→null)。"
          "Semrush 官方公式未公开,此为对齐其分档(0-2/2-5/5-8/8-10【官方】)的自研口径")


# ---------------------------------------------------------------- CSV 读取(对齐 gsc_mining.py 惯例)
def pick(row, *names):
    """按前缀匹配取列(键已 strip+lower),与 gsc_mining.get 同形。"""
    for n in names:
        for k in row:
            if k.startswith(n):
                return row[k]
    return ""


def norm_date(v):
    """常见导出日期格式 → ISO;无法解析返回 None。"""
    v = (v or "").strip()
    if not v:
        return None
    try:
        return datetime.strptime(v[:10] if len(v) > 10 and v[4] == "-" else v,
                                 "%Y-%m-%d").date().isoformat()
    except ValueError:
        pass
    for fmt in ("%Y/%m/%d", "%m/%d/%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(v, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def read_position_rows(path):
    """CSV → [(date_iso, query, pos)],跳过无日期/无词/非正数位次的行。"""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        norm = {k.strip().lower(): (v or "") for k, v in r.items() if k}
        d = norm_date(pick(norm, *DATE_COLS))
        q = pick(norm, *QUERY_COLS).strip()
        try:
            pos = float(pick(norm, *POS_COLS))
        except ValueError:
            continue
        if not d or not q or pos <= 0:
            continue
        out.append((d, q, pos))
    return out


def aggregate(rows):
    """[(date,query,pos)] → {date: {query: 均值位次}}(同日同词多行取均值,GSC 矩阵导出安全)。"""
    acc = {}
    for d, q, p in rows:
        cell = acc.setdefault(d, {}).setdefault(q, [0.0, 0])
        cell[0] += p
        cell[1] += 1
    return {d: {q: v[0] / v[1] for q, v in m.items()} for d, m in acc.items()}


# ---------------------------------------------------------------- 波动分核心
def day_deltas(prev, cur):
    """单日各查询的 D_k:并集口径,丢失/新进=1.0,其余 |Δpos|/20 封顶 1.0。"""
    out = {}
    for q in set(prev) | set(cur):
        if q not in prev or q not in cur:
            out[q] = 1.0
        else:
            out[q] = min(1.0, abs(prev[q] - cur[q]) / POS_SCALE)
    return out


def score_from_deltas(deltas):
    """10 × mean(D_k) 线性缩放,round 1 位,clamp 0-10。"""
    if not deltas:
        return 0.0
    mean = sum(deltas.values()) / len(deltas)
    return min(10.0, max(0.0, round(10.0 * mean, 1)))


def band_of(score):
    """分档【官方】:0-2 low / 2-5 normal / 5-8 high / 8-10 very high(边界值归上档)。"""
    for edge, name in BAND_EDGES:
        if score < edge:
            return name
    return "very high"


def zscore(score, baseline):
    """z=(score−mean)/std,总体 std;基线<2 天或 std=0 → None[推断:Sensor Deviations 口径]。"""
    if len(baseline) < Z_MIN_BASELINE:
        return None
    mean = sum(baseline) / len(baseline)
    std = (sum((x - mean) ** 2 for x in baseline) / len(baseline)) ** 0.5
    if std < 1e-9:
        return None
    return round((score - mean) / std, 2)


def compute_days(pos_by_date):
    """逐日波动分。day_0 无前日不评分;相邻可用日对比(GSC 缺日时与最近可用日比[推断])。"""
    dates = sorted(pos_by_date)
    days, scores = [], []
    for i in range(1, len(dates)):
        prev, cur = pos_by_date[dates[i - 1]], pos_by_date[dates[i]]
        score = score_from_deltas(day_deltas(prev, cur))
        z = zscore(score, scores[-Z_WINDOW:])
        days.append({"date": dates[i], "score": score, "band": band_of(score),
                     "z30": z, "abnormal": z is not None and abs(z) >= Z_THRESHOLD})
        scores.append(score)
    return days


def top_movers(prev, cur, limit=10):
    """最新可比日的 Top 涨跌:涨=位次数字变小;delta=cur-prev。"""
    rose, fell, lost, new = [], [], [], []
    for q in set(prev) | set(cur):
        if q not in cur:
            lost.append({"query": q, "prev_pos": round(prev[q], 1)})
        elif q not in prev:
            new.append({"query": q, "cur_pos": round(cur[q], 1)})
        else:
            delta = round(cur[q] - prev[q], 1)
            if delta < 0:
                rose.append({"query": q, "prev": round(prev[q], 1),
                             "cur": round(cur[q], 1), "delta": delta})
            elif delta > 0:
                fell.append({"query": q, "prev": round(prev[q], 1),
                             "cur": round(cur[q], 1), "delta": delta})
    rose.sort(key=lambda r: r["delta"])
    fell.sort(key=lambda r: -r["delta"])
    lost.sort(key=lambda r: r["query"])
    new.sort(key=lambda r: r["query"])
    lim = max(0, limit)
    return {"rose": rose[:lim], "fell": fell[:lim], "lost": lost[:lim], "new": new[:lim]}


# ---------------------------------------------------------------- 输出
def fmt_z(z):
    return "—" if z is None else f"{z:+.1f}"


def ascii_chart(days, max_cols=CHART_MAX_COLS):
    """逐日 score 的 ASCII 折线(点图):行=1.0 分带(上界标注),列=可评分日。"""
    pts = days[-max_cols:]
    n = len(pts)
    lines = []
    for level in range(10, 0, -1):
        cells = "".join("*" if min(10, int(d["score"]) + 1) == level else " " for d in pts)
        lines.append(f"{level:>2d} |{cells}")
    lines.append("   +" + "-" * n)
    first, last = pts[0]["date"], pts[-1]["date"]
    if n >= len(first) + len(last) + 2:
        lab = list(" " * n)
        lab[0:len(first)] = list(first)
        lab[n - len(last):n] = list(last)
        if n >= 40:
            mid = pts[n // 2]["date"]
            s = n // 2 - len(mid) // 2
            if s > len(first) + 1 and s + len(mid) < n - len(last) - 1:
                lab[s:s + len(mid)] = list(mid)
        lines.append("     " + "".join(lab))
    else:
        lines.append(f"     {first} … {last}")
    return "\n".join(lines)


def render_markdown(src, dates, days, qcount, warnings, movers):
    L = ["# 自有词集 SERP 波动分", ""]
    L.append(f"- 数据源: `{src}`")
    L.append(f"- 日期范围: {dates[0]} → {dates[-1]}(数据日 {len(dates)},可评分日 {len(days)})")
    L.append(f"- 词集: {qcount} 个查询" + ("(词集过小,分数不稳定)" if qcount < MIN_QUERIES else ""))
    for w in warnings:
        L.append(f"- 警告: {w}")
    L.append(f"- 口径: {METHOD}")
    L.append(f"- 分档【官方】: {BANDS_DOC};score≥8 触发疑似重大算法更新提示")
    L.append("")
    L.append("## 逐日分数")
    L.append("")
    L.append("| 日期 | score | 分档 | z30 | 备注 |")
    L.append("|---|---|---|---|---|")
    for d in days:
        notes = []
        if d["score"] >= 8:
            notes.append("疑似重大算法更新")
        if d["abnormal"]:
            notes.append(f"异常日(|z|≥{Z_THRESHOLD:g})")
        L.append(f"| {d['date']} | {d['score']:.1f} | {d['band']} | {fmt_z(d['z30'])} | "
                 + ("; ".join(notes) if notes else "—") + " |")
    L.append("")
    trunc = f"(仅显示最近 {CHART_MAX_COLS} 天)" if len(days) > CHART_MAX_COLS else ""
    L.append(f"## 波动图(score 0-10;* = 当日分,每列一个可评分日{trunc})")
    L.append("")
    L.append("```")
    L.append(ascii_chart(days))
    L.append("```")
    L.append("")
    L.append(f"## 异常日(|z|≥{Z_THRESHOLD:g})")
    L.append("")
    ab = [d for d in days if d["abnormal"]]
    if ab:
        for d in ab:
            L.append(f"- {d['date']}: score {d['score']:.1f}({d['band']}),z30 {fmt_z(d['z30'])}"
                     "——显著偏离近 30 天基线,疑似算法更新而非站点问题")
    else:
        L.append("无")
    L.append("")
    upd = [d for d in days if d["score"] >= 8]
    if upd:
        L.append("## 疑似重大算法更新(score≥8)")
        L.append("")
        for d in upd:
            L.append(f"- {d['date']}: score {d['score']:.1f}(very high 档)"
                     "——建议对照 Semrush Sensor 与 Google Search Status Dashboard 核实")
        L.append("")
    L.append(f"## Top 涨跌查询({dates[-1]} vs {dates[-2]})")
    L.append("")
    L.append("涨(位次上升):")
    if movers["rose"]:
        for r in movers["rose"]:
            L.append(f"- {r['query']}: {r['prev']} → {r['cur']}(+{-r['delta']:.1f} 位)")
    else:
        L.append("- 无")
    L.append("")
    L.append("跌(位次下降):")
    if movers["fell"]:
        for r in movers["fell"]:
            L.append(f"- {r['query']}: {r['prev']} → {r['cur']}(-{r['delta']:.1f} 位)")
    else:
        L.append("- 无")
    L.append("")
    L.append("丢失(前日在、今日无,按满幅波动计):")
    L.append("- " + ", ".join(r["query"] for r in movers["lost"]) if movers["lost"] else "- 无")
    L.append("")
    L.append("新进(前日无、今日有,按满幅波动计):")
    L.append("- " + ", ".join(r["query"] for r in movers["new"]) if movers["new"] else "- 无")
    L.append("")
    return "\n".join(L)


def build_payload(src, dates, days, qcount, warnings, movers):
    return {
        "tool": "sensor_volatility",
        "source": src,
        "date_range": {"first": dates[0], "last": dates[-1],
                       "data_days": len(dates), "scored_days": len(days)},
        "query_count": qcount,
        "warnings": warnings,
        "method": METHOD,
        "bands": BANDS_DOC,
        "days": days,
        "abnormal_days": [d["date"] for d in days if d["abnormal"]],
        "algorithm_update_suspected": any(d["score"] >= 8 for d in days),
        "algorithm_update_days": [d["date"] for d in days if d["score"] >= 8],
        "top_movers": dict(movers, date=dates[-1], prev_date=dates[-2]),
    }


# ---------------------------------------------------------------- 入口
def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="sensor_volatility.py",
        description="自有词集 SERP 波动分(Semrush Sensor 口径的自研版):"
                    "逐日 D_k=|Δpos|/20(丢失/新进=1.0)→ score 0-10 + 分档 + z30 异常日。"
                    "Semrush 官方公式未公开,此为对齐其分档的自研口径。",
        epilog="示例: sensor_volatility.py --gsc gsc.csv --json | "
               "sensor_volatility.py --gsc gsc.csv --context --date 2026-10-09")
    ap.add_argument("--gsc", metavar="FILE",
                    help="GSC 导出 CSV(列含 Date/Query/Position,可含 Clicks/Impressions/CTR)")
    ap.add_argument("--positions", metavar="FILE",
                    help="三列表 CSV: Date,Query,Position")
    ap.add_argument("--json", action="store_true", help="结构化 JSON 输出")
    ap.add_argument("--context", action="store_true",
                    help="上下文模式:单行 JSON {date,score,band,z30,verdict}"
                         "(供 monitor 的 gsc/visibility 告警附注用)")
    ap.add_argument("--date", metavar="YYYY-MM-DD",
                    help="--context 的目标日(默认最新可评分日;需为数据内且非首日)")
    ap.add_argument("--top", type=int, default=10, metavar="N",
                    help="Top 涨跌查询条数(默认 10)")
    args = ap.parse_args(argv)

    if args.date and not args.context:
        ap.error("--date 仅可与 --context 同用")
    if bool(args.gsc) == bool(args.positions):
        ap.error("需且仅需 --gsc 或 --positions 之一")
    src = args.gsc or args.positions

    try:
        rows = read_position_rows(src)
    except OSError as e:
        print(f"[!] 无法读取 {src}: {e}", file=sys.stderr)
        return 2
    if not rows:
        print("[!] 无有效数据行(需 Date/Query/Position 列,Position 为正数)", file=sys.stderr)
        return 2
    pos_by_date = aggregate(rows)
    dates = sorted(pos_by_date)
    if len(dates) < 2:
        print(f"[!] 单日数据({dates[0] if dates else '无日期'})→ 无法计算日波动"
              "(每日分需前一日词表对比,至少两个日期)", file=sys.stderr)
        return 2

    days = compute_days(pos_by_date)
    qcount = len({q for m in pos_by_date.values() for q in m})
    warnings = []
    if qcount < MIN_QUERIES:
        w = f"词集过小({qcount}<{MIN_QUERIES}),分数不稳定"
        warnings.append(w)
        print(f"[!] {w}", file=sys.stderr)

    if args.context:
        target = args.date or days[-1]["date"]
        day = next((d for d in days if d["date"] == target), None)
        if day is None:
            print(f"[!] {target} 无波动分(需为数据内日期且非首个数据日)", file=sys.stderr)
            return 2
        verdict = "high_volatility" if (day["score"] >= 8
                                        or (day["z30"] is not None and abs(day["z30"]) >= Z_THRESHOLD)) \
            else "normal"
        print(json.dumps({"date": day["date"], "score": day["score"], "band": day["band"],
                          "z30": day["z30"], "verdict": verdict}, ensure_ascii=False))
        return 0

    movers = top_movers(pos_by_date[dates[-2]], pos_by_date[dates[-1]], args.top)
    if args.json:
        print(json.dumps(build_payload(src, dates, days, qcount, warnings, movers),
                         ensure_ascii=False, indent=1))
    else:
        print(render_markdown(src, dates, days, qcount, warnings, movers))
    return 0


if __name__ == "__main__":
    sys.exit(main())
