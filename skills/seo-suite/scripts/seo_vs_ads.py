#!/usr/bin/env python3
"""SEO vs 付费广告四桶 join(stdlib)。GSC queries 导出 × Ads search terms 导出,
默认双方覆盖同一个 ~90 天窗口。

四桶:
  double_paying     自然位≤3 且同词在投(自己花钱买本就免费的点击)。
                    品牌词无竞价者时最浪费 → HIGH(自己的 search terms 报告
                    看不到竞对竞价,需 auction insights 复核,脚本注明)。
  defensible        竞对在投(词里出现竞对品牌,自然位≤10,值得防御性出价)。
                    需 --competitors 列表,无则明说跳过、不猜。
  paid_only_winners 花过钱(Cost>0 且有点击)但自然位>10/无自然存在
                    → "被钱预验证的内容路线图"。
  organic_only      在 GSC 有自然点击、Ads 未投的词。

省额估算 = double_paying 成本 × 自然点击保留率 50%~70%,两档输出,
明示为估算区间(estimate range),非实测。
缺 Ads 侧时明确列出缺什么、能算什么,不猜。

用法:
    python3 seo_vs_ads.py --gsc queries.csv [--ads searchterms.csv] \
        [--brand "acme,initrode"] [--competitors "rival1,rival2"]
退出码:0=跑完(含 Ads 缺失降级);2=GSC 文件/格式错误。"""
import argparse
import csv
import re
import sys

RETENTION_LOW, RETENTION_HIGH = 0.50, 0.70  # 明示为估算区间


def norm(q):
    return re.sub(r"\s+", " ", (q or "").strip().lower())


def num(s):
    m = re.search(r"-?\d+(?:\.\d+)?", (s or "").replace(",", ""))
    return float(m.group()) if m else 0.0


def find_col(fieldnames, names):
    low = {c.strip().lower(): c for c in fieldnames if c}
    return next((low[n] for n in names if n in low), None)


def load_csv(path, required, spec):
    """spec: {逻辑名: [候选列名]};返回 [ {逻辑名: 值} ]。"""
    try:
        f = open(path, encoding="utf-8-sig", newline="")
    except OSError as e:
        return None, f"无法读取 {path}: {e}"
    with f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames:
            return None, f"{path}: 空 CSV"
        cols = {k: find_col(rdr.fieldnames, v) for k, v in spec.items()}
        missing = [k for k in required if not cols[k]]
        if missing:
            return None, f"{path}: 缺列 {missing},实际列={list(rdr.fieldnames)}"
        rows = []
        for row in rdr:
            rows.append({k: (row.get(c) or "").strip() if c else "" for k, c in cols.items()})
        return rows, None


def main():
    ap = argparse.ArgumentParser(description="SEO vs Ads 四桶 join(GSC queries × Ads search terms)")
    ap.add_argument("--gsc", required=True, help="GSC queries 导出 CSV(需 Query/Position/Clicks)")
    ap.add_argument("--ads", help="Google Ads search terms 导出 CSV(需 Search term/Cost/Clicks);缺省时明说缺什么")
    ap.add_argument("--brand", default="", help="自家品牌词(逗号分隔),用于 double_paying 里判 HIGH")
    ap.add_argument("--competitors", default="", help="竞对词列表(逗号分隔);不提供则 defensible 桶跳过")
    a = ap.parse_args()

    gsc, err = load_csv(a.gsc, ["query", "position", "clicks"],
                        {"query": ["query", "top queries", "queries", "keyword"],
                         "position": ["position", "avg. position", "average position"],
                         "clicks": ["clicks"]})
    if err:
        print(f"[error] {err}", file=sys.stderr)
        sys.exit(2)

    g = {}
    for r in gsc:
        q = norm(r["query"])
        if q:
            g[q] = {"position": num(r["position"]), "clicks": num(r["clicks"])}

    brand_toks = [norm(t) for t in a.brand.split(",") if norm(t)]
    comp_toks = [norm(t) for t in a.competitors.split(",") if norm(t)]

    ads = None
    ads_missing = []
    if not a.ads:
        ads_missing.append("--ads 未提供:double_paying / defensible / paid_only_winners 均需要 Ads search terms 数据")
    else:
        ads, err = load_csv(a.ads, ["term", "cost", "clicks"],
                            {"term": ["search term", "search terms", "query", "keyword"],
                             "cost": ["cost", "spend", "花费"],
                             "clicks": ["clicks"]})
        if err:
            ads_missing.append(f"Ads 文件不可用:{err}(不猜,跳过 Ads 侧)")
            ads = None

    W = 72
    print("=" * W); print("SEO vs Ads 四桶对照".center(W)); print("=" * W)
    print(f"GSC queries : {len(g)} 个词(文件 {a.gsc})")
    if ads is not None:
        paid = {}
        for r in ads:
            t = norm(r["term"])
            if not t:
                continue
            p = paid.setdefault(t, {"cost": 0.0, "clicks": 0.0})
            p["cost"] += num(r["cost"]); p["clicks"] += num(r["clicks"])
        print(f"Ads terms   : {len(paid)} 个词(文件 {a.ads})")
        print("[前提] 假定两侧导出覆盖同一 ~90 天窗口;若日期范围未对齐,")
        print("       join 结果不可信,请先对齐导出窗口再跑。")
    else:
        paid = None
        print("Ads terms   : 缺失")
        for m in ads_missing:
            print(f"[missing] {m}")
        print("[说明] 缺 Ads 侧时不做任何 Ads 相关推断;仅输出 GSC 侧概览。")

    if paid is None:
        top = sorted(g.items(), key=lambda kv: -kv[1]["clicks"])[:10]
        print("-" * W)
        print("GSC 侧概览(点击 Top 10,organic_only 需 Ads 侧才能定义,不猜):")
        for q, v in top:
            print(f"  pos={v['position']:>5.1f}  clicks={v['clicks']:>7.0f}  {q}")
        print("=" * W)
        sys.exit(0)

    # ---- 桶 1: double_paying ----
    double = []
    for q, v in g.items():
        if v["position"] <= 3 and q in paid:
            sev = "HIGH" if any(t in q for t in brand_toks) else "MED"
            double.append((q, v, paid[q], sev))
    double.sort(key=lambda x: -x[2]["cost"])

    # ---- 桶 2: defensible ----
    print("-" * W)
    print(f"桶 1  double_paying(自然位≤3 且同词在投):{len(double)} 词")
    if double:
        print("  这些点击本可能免费获得,是当前最直接的浪费:")
        for q, v, p, sev in double:
            line = f"  [{sev:>4}] pos={v['position']:.0f} cost={p['cost']:.2f} " \
                   f"ads_clicks={p['clicks']:.0f}  {q}"
            print(line)
            if sev == "HIGH":
                print("         └ 品牌词:自家导出看不到竞对是否在投(auction insights 才能确认);")
                print("           若确认无竞价者,这批花费接近纯浪费 → HIGH。")
        total_cost = sum(p["cost"] for _, _, p, _ in double)
        print(f"  合计成本:{total_cost:.2f}(币种按导出原样)")
        print(f"  省额估算 = Cost × 自然点击保留率(估算区间 {RETENTION_LOW:.0%}~{RETENTION_HIGH:.0%},非实测):")
        print(f"    保守档({RETENTION_LOW:.0%}): {total_cost * RETENTION_LOW:.2f}")
        print(f"    乐观档({RETENTION_HIGH:.0%}): {total_cost * RETENTION_HIGH:.2f}")
        print("  验证方式:挑非品牌词做暂停 holdout 实测保留率后再全量。")
    else:
        print("  (无:没有自然位≤3 且同时付费的词)")

    print("-" * W)
    if comp_toks:
        defens = [(q, v) for q, v in g.items()
                  if any(t in q for t in comp_toks) and v["position"] <= 10]
        print(f"桶 2  defensible(词含竞对品牌、自然位≤10):{len(defens)} 词")
        if defens:
            print("  竞对在投语境(词中含竞对名),值得防御性内容/出价守住 SERP:")
            for q, v in sorted(defens, key=lambda kv: -kv[1]["clicks"])[:15]:
                tag = "已付费" if q in paid else "未付费"
                print(f"  [{tag}] pos={v['position']:.0f} clicks={v['clicks']:.0f}  {q}")
    else:
        print("桶 2  defensible:SKIPPED —— 未提供 --competitors 列表;")
        print("  竞对在投与否本脚本无法从现有数据推断,不猜。补列表后重跑。")

    # ---- 桶 3: paid_only_winners ----
    winners = [(t, p) for t, p in paid.items()
               if p["cost"] > 0 and p["clicks"] > 0
               and (t not in g or g[t]["position"] > 10)]
    winners.sort(key=lambda x: -x[1]["cost"])
    print("-" * W)
    print(f"桶 3  paid_only_winners(花钱验证过、自然位>10 或无自然位):{len(winners)} 词")
    print("  = 被钱预验证的内容路线图:愿意花钱买说明有转化价值,自然侧缺位:")
    if winners:
        for t, p in winners[:20]:
            pos = f"{g[t]['position']:.0f}" if t in g else "无自然存在"
            print(f"  cost={p['cost']:>8.2f} clicks={p['clicks']:>5.0f} pos={pos:>6}  {t}")
        if len(winners) > 20:
            print(f"  ...(其余 {len(winners) - 20} 个按 cost 降序省略)")
    else:
        print("  (无)")

    # ---- 桶 4: organic_only ----
    organic_only = [(q, v) for q, v in g.items() if q not in paid]
    organic_only.sort(key=lambda kv: -kv[1]["clicks"])
    print("-" * W)
    print(f"桶 4  organic_only(GSC 有、Ads 未投):{len(organic_only)} / {len(g)} 词")
    for q, v in organic_only[:10]:
        print(f"  pos={v['position']:>5.1f} clicks={v['clicks']:>7.0f}  {q}")
    if len(organic_only) > 10:
        print(f"  ...(其余 {len(organic_only) - 10} 个省略)")
    print("=" * W)
    print("caveat:省额为估算区间;双花省额只有在 holdout 实测保留率后才可承诺;")
    print("       Ads search terms 只含触发过的词,不是全部在投词。")
    sys.exit(0)


if __name__ == "__main__":
    main()
