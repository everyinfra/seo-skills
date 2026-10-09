#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""grid_rank.py — 本地网格排名(geo-grid)三指标计算器(仅标准库).

执行 references/monitoring/local-grid-ranking.md 的源码级口径:
  ARP   = Σ rank(命中点) ÷ 命中点数, 1 位小数;全未命中 → null
  ATRP  = Σ (rank ?? 21) ÷ 全部格点数, 1 位小数(未找到按 21 惩罚,永不 null)
  SoLV  = count(rank ≤ 3) ÷ 全部格点数 × 100, 1 位小数
  found_in = 命中点数/总点数(如 6/9)
  盲区 = ATRP − ARP(差值越大:「进榜时排名尚可,但大片区域根本找不到」越严重)

输入 CSV(rank_data.csv)列: keyword, grid_point, rank
  * rank 留空(或 null/none/-)= 该格点未找到
  * rank > 20 视同未找到并告警:Text Search maxResultCount=20,排在 20 名开外
    与不在结果里在格点层面不可区分——这是「21 惩罚」的来源
  * 多关键词自动分组;同关键词同格点重复取最后一条并告警
  * ARP 与 ATRP 必须同时报:只报 ARP 会把大片盲区美化成正常

用法:
  python3 grid_rank.py [rank_data.csv] [--detail] [--json]
  python3 grid_rank.py - < rank_data.csv        # 从 stdin 读

退出码: 0 正常; 2 致命(文件不存在/表头缺列)。
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import unicodedata
from pathlib import Path

NOT_FOUND_PENALTY = 21   # ATRP 未命中惩罚值(口径见 local-grid-ranking.md)
TOP_N = 3                # SoLV 统计 rank ≤ TOP_N(本地包前三)
MAX_VISIBLE_RANK = 20    # Text Search maxResultCount;>20 视同未找到
DEFAULT_CSV = "rank_data.csv"
REQUIRED_COLS = ("keyword", "grid_point", "rank")
NULL_TOKENS = ("", "null", "none", "-")
RETEST_NOTE = "复测口径: 同网格、同词表、同半径(中心/gridSize/spacing/语言参数不变);未命中按 21 计;年同比优先"


def fatal(msg):
    print(f"[error] {msg}", file=sys.stderr)
    sys.exit(2)


def dwidth(s):
    """CJK 对齐用显示宽度(全角记 2)。"""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def pad(s, w):
    return s + " " * max(0, w - dwidth(s))


def load_rows(src):
    """读 CSV → (rows[(keyword, grid_point, rank_or_None)], warnings, 来源名)"""
    warnings = []
    if src == "-":
        reader = csv.DictReader(sys.stdin)
        name = "stdin"
    else:
        p = Path(src)
        if not p.is_file():
            fatal(f"CSV 不存在: {p}")
        name = str(p)
        reader = csv.DictReader(p.open(encoding="utf-8-sig", newline=""))
    if not reader.fieldnames:
        fatal("CSV 为空(缺表头,需要 keyword,grid_point,rank)")
    fieldmap = {}
    for col in reader.fieldnames or []:
        c = (col or "").strip().lower()
        if c in REQUIRED_COLS and c not in fieldmap:
            fieldmap[c] = col
    missing = [c for c in REQUIRED_COLS if c not in fieldmap]
    if missing:
        fatal(f"表头缺列 {missing}(需要 {list(REQUIRED_COLS)},大小写不敏感)")

    rows = []
    for lineno, rec in enumerate(reader, start=2):
        get = lambda k: (rec.get(fieldmap[k]) or "").strip()
        kw, gp, raw = get("keyword"), get("grid_point"), get("rank")
        if not kw and not gp and not raw:
            continue  # 整行空
        if not kw:
            warnings.append(f"第 {lineno} 行 keyword 为空,已跳过")
            continue
        rank = None
        if raw.lower() not in NULL_TOKENS:
            try:
                rank = int(raw)
            except ValueError:
                warnings.append(f"第 {lineno} 行 rank 无法解析({raw!r}),按未找到计")
                rank = None
            else:
                if rank <= 0:
                    warnings.append(f"第 {lineno} 行 rank={rank} 非法(≤0),按未找到计")
                    rank = None
                elif rank > MAX_VISIBLE_RANK:
                    warnings.append(
                        f"第 {lineno} 行 rank={rank} 超出可见上限 {MAX_VISIBLE_RANK}"
                        f"(>20 与未找到不可区分),按未找到计")
                    rank = None
        rows.append((kw, gp, rank))
    return rows, warnings, name


def group_rows(rows, warnings):
    """按关键词分组(保持出现顺序),返回 [(keyword, [(grid_point, rank), ...])]"""
    order, data = [], {}
    for kw, gp, rank in rows:
        if kw not in data:
            data[kw] = {}
            order.append(kw)
        label = gp or f"#{len(data[kw]) + 1}"
        if label in data[kw]:
            warnings.append(f"关键词「{kw}」格点「{label}」重复,取最后一条")
        data[kw][label] = rank
    return [(kw, list(data[kw].items())) for kw in order]


def metrics(points):
    """points = [(label, rank_or_None)] → 指标 dict(盲区按四舍五入后的 ARP/ATRP 相减,对齐文档算例)。"""
    n = len(points)
    ranks = [r for _, r in points]
    hits = [r for r in ranks if r is not None]
    h = len(hits)
    top = sum(1 for r in hits if r <= TOP_N)
    arp = round(sum(hits) / h, 1) if h else None
    atrp = round((sum(hits) + NOT_FOUND_PENALTY * (n - h)) / n, 1) if n else None
    solv = round(top / n * 100, 1) if n else None
    blind = round(atrp - arp, 1) if (arp is not None and atrp is not None) else None
    return {
        "points": n, "found": h, "arp": arp, "atrp": atrp, "blind": blind,
        "solv": solv, "found_in": f"{h}/{n}", "top3_points": top,
    }


def fmt(v, suffix=""):
    return "null" if v is None else f"{v}{suffix}"


def main():
    ap = argparse.ArgumentParser(
        description="本地网格排名(geo-grid)ARP/ATRP/SoLV 计算器(口径: local-grid-ranking.md)")
    ap.add_argument("csv", nargs="?", default=DEFAULT_CSV,
                    help=f"CSV 路径,列 keyword,grid_point,rank(留空=未找到);默认 {DEFAULT_CSV};- = stdin")
    ap.add_argument("--detail", action="store_true", help="附每关键词格点明细")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    a = ap.parse_args()

    rows, warnings, name = load_rows(a.csv)
    groups = group_rows(rows, warnings)
    if not groups:
        fatal("CSV 中没有有效数据行")
    results = [(kw, pts, metrics(pts)) for kw, pts in groups]

    if a.json:
        print(json.dumps({
            "source": name, "not_found_penalty": NOT_FOUND_PENALTY,
            "retest_note": RETEST_NOTE, "warnings": warnings,
            "keywords": [
                {"keyword": kw, **m, "ranks": {gp: r for gp, r in pts}}
                for kw, pts, m in results
            ],
        }, ensure_ascii=False, indent=2))
        return

    kw_w = min(max([dwidth(kw) for kw, _, _ in results] + [12]), 40)
    W = kw_w + 52
    print("=" * W)
    print(f"本地网格排名计算(ARP/ATRP/SoLV)— 数据: {name} | 关键词 {len(results)} 个 | 格点共 {sum(m['points'] for _, _, m in results)} 个")
    print(RETEST_NOTE)
    print("=" * W)
    print(" | ".join([
        pad("关键词", kw_w), pad("点数", 4), pad("命中", 4), pad("ARP", 6),
        pad("ATRP", 6), pad("盲区", 6), pad("SoLV%", 7), "found_in"]))
    print("-" * W)
    for kw, _, m in results:
        print(" | ".join([
            pad(kw[:38], kw_w), pad(str(m["points"]), 4), pad(str(m["found"]), 4),
            pad(fmt(m["arp"]), 6), pad(fmt(m["atrp"]), 6), pad(fmt(m["blind"]), 6),
            pad(fmt(m["solv"]), 7), m["found_in"]]))
    print("-" * W)
    print(f"盲区 = ATRP − ARP:差值越大,「进榜时排名尚可但大片区域找不到」越严重;SoLV 回答「进前三的地理覆盖率」。")
    print(f"ARP 与 ATRP 必须同时报;未命中按 {NOT_FOUND_PENALTY} 计;排名 >{MAX_VISIBLE_RANK} 与未收录不可区分。")

    if a.detail:
        for kw, pts, _ in results:
            print(f"\n明细「{kw}」(grid_point=rank,- = 未找到):")
            for i in range(0, len(pts), 6):
                print("  " + "  ".join(f"{gp}={r if r is not None else '-'}" for gp, r in pts[i:i + 6]))

    if warnings:
        print(f"\n数据告警 {len(warnings)} 条:")
        for w in warnings:
            print(f"  [warn] {w}")
    sys.exit(0)


if __name__ == "__main__":
    main()
