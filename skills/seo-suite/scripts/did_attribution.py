#!/usr/bin/env python3
"""DiD 对照归因(stdlib)。GSC 页面级导出两期 CSV(Page,Clicks[,Date]),
估计处理组"若无变化本应有的点击",归因增量。

模型:
    expectedAfter = treated_pre × (controlAfter / controlBefore)   controlBefore<=0 → null
    lift          = treated_post − expectedAfter
    SE            = √expectedAfter(泊松近似)
    95% CI        = lift ± 1.96·SE → likely_positive / likely_negative / inconclusive

闸门:控制页≥3 / 控制页 pre 点击≥5(不满足自动回退 site 级并注明);
      treated pre 点击≥5(不满足直接判数据不足)。
注意:server-side A/B 是唯一真因果检验,DiD 只是观测估计。
GSC 断代:窗口若与 2025-05-13 ~ 2026-04-30 重叠 → impressions 不可靠。
用法:
    python3 did_attribution.py --treated-page https://s.com/guides/ \
        --control-page https://s.com/blog/ --pre pre.csv --post post.csv \
        [--pre-start 2025-05-01 --pre-end 2025-06-01 \
         --post-start 2026-07-01 --post-end 2026-10-01] [--json]
退出码:0=出结果(含 inconclusive/null);1=结果为 null;2=闸门/文件错误。"""
import argparse
import csv
import json
import math
import re
import sys
from datetime import date, timedelta

EPOCH_START, EPOCH_END = date(2025, 5, 13), date(2026, 4, 30)  # GSC 数据断代
GATE_MIN_CTRL_PAGES = 3
GATE_MIN_CLICKS = 5
Z = 1.96


def die(msg, code=2):
    print(f"[error] {msg}", file=sys.stderr)
    sys.exit(code)


def load_gsc_csv(path):
    """返回 ({page: clicks}, 有 Date 列时的 (min_date, max_date))。"""
    try:
        f = open(path, encoding="utf-8-sig", newline="")
    except OSError as e:
        die(f"无法读取 {path}: {e}")
    with f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames:
            die(f"{path}: 空 CSV")
        cols = {c.strip().lower(): c for c in rdr.fieldnames if c}
        page_k = next((cols[k] for k in ("page", "url", "landing page") if k in cols), None)
        click_k = next((cols[k] for k in ("clicks",) if k in cols), None)
        date_k = next((cols[k] for k in ("date",) if k in cols), None)
        if not page_k or not click_k:
            die(f"{path}: 需要 Page 和 Clicks 列,实际列={list(rdr.fieldnames)}")
        pages, dates = {}, []
        for row in rdr:
            url = (row.get(page_k) or "").strip()
            if not url:
                continue
            m = re.search(r"-?\d+(?:\.\d+)?", (row.get(click_k) or "0").replace(",", ""))
            try:
                c = max(0, int(float(m.group()))) if m else 0
            except ValueError:
                c = 0
            pages[url] = pages.get(url, 0) + c
            if date_k and row.get(date_k):
                try:
                    dates.append(date.fromisoformat(row[date_k].strip()[:10]))
                except ValueError:
                    pass
    span = (min(dates), max(dates)) if dates else None
    return pages, span


def pick(pages, prefix, exclude_prefix=None):
    out = {}
    for url, c in pages.items():
        if url.startswith(prefix) and (exclude_prefix is None or not url.startswith(exclude_prefix)):
            out[url] = c
    return out


def overlaps_epoch(win):
    if not win:
        return False, None
    s, e = win if win[1] >= win[0] else (win[1], win[0])
    hit = s <= EPOCH_END and e >= EPOCH_START
    return hit, (s, e)


def main():
    ap = argparse.ArgumentParser(description="DiD 对照归因(GSC 页面级两期导出)")
    ap.add_argument("--treated-page", required=True, help="处理组 URL 前缀")
    ap.add_argument("--control-page", required=True, help="对照组 URL 前缀")
    ap.add_argument("--pre", required=True, help="pre 期 GSC 页面级 CSV")
    ap.add_argument("--post", required=True, help="post 期 GSC 页面级 CSV")
    ap.add_argument("--pre-start"); ap.add_argument("--pre-end")
    ap.add_argument("--post-start"); ap.add_argument("--post-end")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()

    pre, pre_span_file = load_gsc_csv(a.pre)
    post, post_span_file = load_gsc_csv(a.post)

    def span(args_, file_span):
        p = [date.fromisoformat(x) for x in args_ if x] or list(file_span or [])
        return (min(p), max(p)) if p else None

    try:
        pre_win, post_win = span([a.pre_start, a.pre_end], pre_span_file), span([a.post_start, a.post_end], post_span_file)
    except ValueError:
        die("--pre/--post-start/end 需要 YYYY-MM-DD")

    treated_pre_pages = pick(pre, a.treated_page)
    treated_post_pages = pick(post, a.treated_page)
    ctrl_pre_pages = pick(pre, a.control_page)
    ctrl_post_pages = pick(post, a.control_page)

    treated_pre = sum(treated_pre_pages.values())
    treated_post = sum(treated_post_pages.values())

    # 闸门:treated pre 基线不足 → 无法归因
    if treated_pre < GATE_MIN_CLICKS:
        die(f"闸门未过:treated 组 pre 点击={treated_pre} < {GATE_MIN_CLICKS},基线流量不足以归因", 2)

    # 闸门:控制池不足 → 自动回退 site 级(全站非处理页),并注明
    fallback = False
    if len(ctrl_pre_pages) < GATE_MIN_CTRL_PAGES or sum(ctrl_pre_pages.values()) < GATE_MIN_CLICKS:
        fallback = True
        ctrl_pre_pages = {u: c for u, c in pre.items() if not u.startswith(a.treated_page)}
        ctrl_post_pages = {u: c for u, c in post.items() if not u.startswith(a.treated_page)}
        ctrl_label = f"site 级回退(全站 {len(ctrl_pre_pages)} 个非处理页)"
    else:
        ctrl_label = f"前缀 {a.control_page}({len(ctrl_pre_pages)} 页)"

    ctrl_before = sum(ctrl_pre_pages.values())
    ctrl_after = sum(ctrl_post_pages.values())

    # 断代检测
    epoch_hits, spans = [], (pre_win, post_win)
    for w in spans:
        hit, s = overlaps_epoch(w)
        if hit:
            epoch_hits.append(f"{s[0]}~{s[1]}")
    epoch_warn = (f"窗口 {', '.join(epoch_hits)} 与 GSC 断代区间 "
                  f"{EPOCH_START}~{EPOCH_END} 重叠:impressions 不可靠"
                  if epoch_hits else
                  ("未提供窗口日期且 CSV 无 Date 列,断代检测跳过" if not (pre_win or post_win) else None))

    r = {
        "treated_prefix": a.treated_page, "control": ctrl_label, "control_fallback": fallback,
        "treated_pre": treated_pre, "treated_post": treated_post,
        "controlBefore": ctrl_before, "controlAfter": ctrl_after,
        "gates": {"treated_pre_clicks": treated_pre,
                  "control_pages": len(ctrl_pre_pages),
                  "control_pre_clicks": ctrl_before},
    }

    if ctrl_before <= 0:
        r.update(verdict="null", reason="controlBefore<=0,对照比率无定义")
        emit(r, a, epoch_warn, null=True)
        sys.exit(1)

    ratio = ctrl_after / ctrl_before
    expected = treated_pre * ratio
    lift = treated_post - expected
    se = math.sqrt(expected)
    lo, hi = lift - Z * se, lift + Z * se
    verdict = "likely_positive" if lo > 0 else "likely_negative" if hi < 0 else "inconclusive"
    r.update(expectedAfter=round(expected, 2), lift=round(lift, 2), se=round(se, 3),
             ci_low=round(lo, 2), ci_high=round(hi, 2), control_ratio=round(ratio, 4),
             verdict=verdict)
    emit(r, a, epoch_warn)
    sys.exit(0)


def emit(r, a, epoch_warn, null=False):
    if a.json:
        print(json.dumps({**r, "epoch_warning": epoch_warn,
                          "caveat": "server-side A/B 是唯一真因果检验;DiD 为观测估计"},
                         ensure_ascii=False, indent=2))
        if null:
            print(f"[null] {r['reason']}", file=sys.stderr)
        return
    W = 64
    print("=" * W); print("DiD 对照归因".center(W)); print("=" * W)
    print(f"treated 前缀 : {r['treated_prefix']}")
    print(f"对照池       : {r['control']}" + ("   <-- 控制页不足,已自动回退" if r["control_fallback"] else ""))
    print(f"数据         : pre={a.pre}  post={a.post}")
    g = r["gates"]
    print(f"[闸门] treated pre 点击 : {g['treated_pre_clicks']:>8}  (>=5)")
    print(f"[闸门] 控制页数量       : {g['control_pages']:>8}  (>=3)")
    print(f"[闸门] 控制页 pre 点击  : {g['control_pre_clicks']:>8}  (>=5)")
    print("-" * W)
    if null:
        print(f"结果:null —— {r['reason']}")
    else:
        print(f"controlBefore={r['controlBefore']}  controlAfter={r['controlAfter']}  "
              f"control ratio={r['control_ratio']}")
        print(f"expectedAfter = treated_pre × ratio = {r['treated_pre']} × {r['control_ratio']} "
              f"= {r['expectedAfter']}")
        print(f"lift          = treated_post − expectedAfter = {r['treated_post']} − "
              f"{r['expectedAfter']} = {r['lift']}")
        print(f"SE(泊松√expectedAfter) = {r['se']}   95% CI = [{r['ci_low']}, {r['ci_high']}]")
        mark = {"likely_positive": "CI 下界>0", "likely_negative": "CI 上界<0", "inconclusive": "CI 跨 0"}[r["verdict"]]
        print(f"判定          : {r['verdict'].upper()}  ({mark})")
    print("-" * W)
    print("caveats:")
    print("  * server-side A/B 是唯一真因果检验;本结果为观测性 DiD 估计,")
    print("    混杂(季节性/外链/算法更新)未被排除。")
    if epoch_warn:
        print(f"  * [GSC 断代] {epoch_warn}。本脚本只用 Clicks(仍可用),")
        print("    但该窗口内任何 impressions/CTR 结论不要引用。")
    print("=" * W)


if __name__ == "__main__":
    main()
