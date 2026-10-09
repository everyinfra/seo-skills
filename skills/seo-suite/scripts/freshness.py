#!/usr/bin/env python3
"""证据保鲜检查(stdlib)。扫描 *.md 头部(默认前 40 行)的日期标记:
    Updated: YYYY-MM-DD / verified_at: YYYY-MM-DD / 建于 YYYY-MM-DD / 复核于 YYYY-MM-DD
>90 天 → stale;未来日期 → error;一个文件取头部最新日期为准。
正则为规格四分支的超集:另容忍"建立于"变体与 markdown 加粗(**2026-01-01**)。

用法: python3 freshness.py [DIR] [--lines 40] [--fail-stale]
      DIR 默认 references/
退出码:0=全部新鲜/无日期;1=存在 stale 且 --fail-stale;2=存在未来日期 error。"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

DATE_RE = re.compile(
    r"Updated[:：]\s*(\d{4}-\d{2}-\d{2})"
    r"|verified_at[\"']?\s*[:：]\s*[\"']?(\d{4}-\d{2}-\d{2})"
    r"|建(?:立)?于\s*[*_]{0,2}\s*(\d{4}-\d{2}-\d{2})"
    r"|复核[于]?\s*[*_]{0,2}\s*(\d{4}-\d{2}-\d{2})"
)
STALE_DAYS = 90
DEFAULT_DIR = "references/"
HEADER_LINES = 40


def scan_file(p, header_lines):
    """返回 (状态, 日期或None, 说明)。状态: fresh/stale/error/no_date/invalid"""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return "no_date", None, f"读取失败: {e}"
    head = "\n".join(text.splitlines()[:header_lines])
    dates = [m for m in DATE_RE.finditer(head)]
    if not dates:
        return "no_date", None, "头部未找到 Updated/verified_at/建于/复核 日期"
    parsed = []
    for m in dates:
        raw = next(g for g in m.groups() if g)
        try:
            parsed.append(date.fromisoformat(raw))
        except ValueError:
            return "invalid", None, f"正则命中但日期非法: {raw}"
    latest = max(parsed)
    return None, latest, ""  # 状态在 judge() 里定


def main():
    ap = argparse.ArgumentParser(description="references 证据保鲜检查(>90 天 stale,未来日期 error)")
    ap.add_argument("dir", nargs="?", default=DEFAULT_DIR, help=f"扫描目录,默认 {DEFAULT_DIR}")
    ap.add_argument("--lines", type=int, default=HEADER_LINES, help="头部扫描行数,默认 40")
    ap.add_argument("--fail-stale", action="store_true", help="存在 stale 时退出码 1")
    a = ap.parse_args()

    root = Path(a.dir)
    if not root.is_dir():
        print(f"[error] 目录不存在: {root}", file=sys.stderr)
        sys.exit(2)
    files = sorted(root.rglob("*.md"))
    if not files:
        print(f"[warn] {root} 下没有 *.md")

    today = date.today()
    rows = []  # (sort_key, path, status, d, note)
    counts = {"fresh": 0, "stale": 0, "error": 0, "no_date": 0, "invalid": 0}
    for p in files:
        status, d, note = scan_file(p, a.lines)
        if status is None:
            if d > today:
                status, note = "error", f"未来日期 {d}(今天 {today})"
            elif (today - d).days > STALE_DAYS:
                status, note = "stale", f"距今 {(today - d).days} 天 > {STALE_DAYS} 天"
            else:
                status, note = "fresh", f"距今 {(today - d).days} 天"
        counts[status] += 1
        rows.append((d or date.min, p, status, d, note))

    rows.sort(key=lambda r: (r[2] != "error", r[2] != "invalid", r[2] != "stale",
                             r[2] == "no_date", r[0]))
    W = 72
    print("=" * W); print(f"证据保鲜检查: {root}".center(W)); print("=" * W)
    print(f"今天 {today};stale 阈值 >{STALE_DAYS} 天;扫描 {len(files)} 个 *.md(头部前 {a.lines} 行)")
    print("-" * W)
    for _, p, status, d, note in rows:
        ds = d.isoformat() if d else "--"
        print(f"[{status.upper():<7}] {ds}  {str(p):<58} {note}")
    print("-" * W)
    print(f"汇总: fresh={counts['fresh']}  stale={counts['stale']}  "
          f"error(未来日期)={counts['error']}  invalid={counts['invalid']}  no_date={counts['no_date']}")
    dated = [r for r in rows if r[3]]
    if dated:
        old = min(dated, key=lambda r: r[0])
        print(f"最旧文件: {old[1]}({old[3]},距今 {(today - old[3]).days} 天)")
    if counts["error"] or counts["invalid"]:
        print("[error] 存在非法/未来日期,先修数据。")
        sys.exit(2)
    if counts["stale"]:
        print(f"[stale] {counts['stale']} 个文件过期" + ("→ --fail-stale 已开启,退出 1" if a.fail_stale else "(未开启 --fail-stale,退出 0)"))
        sys.exit(1 if a.fail_stale else 0)
    print("[ok] 无过期证据。")
    sys.exit(0)


if __name__ == "__main__":
    main()
