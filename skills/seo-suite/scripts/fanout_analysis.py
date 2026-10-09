#!/usr/bin/env python3
"""query fan-out 三桶分析器(stdlib-only)。

判定口径(elmo 实现,百仓扫描核对):
  added      查询 token 不在 prompt 中
  dropped    prompt token 不在查询中
  preserved  两边都在
分词 = 小写;ASCII 连续字母数字为一个 token;CJK 逐字一个 token;
  ASCII 单字符 token 丢弃(a/i/5…);CJK 单字保留(否则中文无法比较)。
排除两类:与 prompt 完全相同(忽略大小写与首尾空白)的查询;"unavailable" 哨兵。
停用词表刻意不含 best/top/review/vs/年份——它们是 fan-out 信号本体,不做停用。
avgPerExecution = 有效查询数 / 有 fan-out 的 prompt 数。

用法:
  python3 fanout_analysis.py input.csv [--top 20]
  python3 fanout_analysis.py --self-test
CSV 两列: prompt, web_query(表头可选;列名 prompt/web_query/query 均可)
"""
import argparse
import csv
import os
import re
import sys
import tempfile
import traceback
from collections import Counter

TOKEN_RE = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]")
SENTINELS = {"", "unavailable", "n/a", "na", "none", "-"}


def tokenize(text):
    """小写分词;ASCII 单字符 token 丢弃,CJK 单字保留。"""
    return [t for t in TOKEN_RE.findall((text or "").lower())
            if len(t) > 1 or "\u4e00" <= t <= "\u9fff"]


def read_rows(path):
    """返回 [(prompt, web_query), ...];自动识别表头与列位。"""
    with open(path, newline="", encoding="utf-8-sig") as f:
        raw = [r for r in csv.reader(f) if r and any(c.strip() for c in r)]
    if not raw:
        return []
    heads = [(h or "").strip().lower() for h in raw[0]]
    pi = qi = None
    if "prompt" in heads:
        pi = heads.index("prompt")
    for name in ("web_query", "webquery", "query", "search_query"):
        if name in heads:
            qi = heads.index(name)
            break
    body = raw[1:] if (pi is not None or qi is not None) else raw
    if pi is None:
        pi = 0
    if qi is None:
        qi = 1 if len(raw[0]) >= 2 else 0
    rows = []
    for r in body:
        if len(r) <= max(pi, qi):
            continue
        rows.append((r[pi].strip(), r[qi].strip()))
    return rows


def analyze(rows):
    added, dropped, preserved = Counter(), Counter(), Counter()
    excluded_same = excluded_sentinel = 0
    fanout_prompts = set()
    total_queries = 0
    for prompt, query in rows:
        q = query.strip().lower()
        if q in SENTINELS:
            excluded_sentinel += 1
            continue
        if q == prompt.strip().lower():
            excluded_same += 1
            continue
        total_queries += 1
        fanout_prompts.add(prompt.strip().lower())
        pt, qt = set(tokenize(prompt)), set(tokenize(query))
        added.update(qt - pt)
        dropped.update(pt - qt)
        preserved.update(qt & pt)
    per_exec = (total_queries / len(fanout_prompts)) if fanout_prompts else None
    return {"added": added, "dropped": dropped, "preserved": preserved,
            "excluded_same": excluded_same, "excluded_sentinel": excluded_sentinel,
            "total_queries": total_queries, "fanout_prompts": len(fanout_prompts),
            "avg_per_execution": per_exec, "rows": len(rows)}


def render(res, top=20):
    L = ["== query fan-out 三桶 =="]
    L.append("行数 %d(有效 %d;排除:与 prompt 完全相同 %d,哨兵 %d)"
             % (res["rows"], res["total_queries"], res["excluded_same"],
                res["excluded_sentinel"]))
    if res["avg_per_execution"] is None:
        L.append("无有效 fan-out 查询")
        return "\n".join(L)
    L.append("avgPerExecution = %d / %d = %.2f"
             % (res["total_queries"], res["fanout_prompts"], res["avg_per_execution"]))
    for name, counter, desc in (
            ("added(查询有,prompt 无——引擎补充的词)", res["added"], "added"),
            ("dropped(prompt 有,查询无——被丢掉的词)", res["dropped"], "dropped"),
            ("preserved(两边都在)", res["preserved"], "preserved")):
        L.append("-- %s | 独立 token %d --" % (name, len(counter)))
        for tok, cnt in counter.most_common(top):
            L.append("  %-24.24s %d" % (tok, cnt))
    return "\n".join(L)


def _self_test():
    assert tokenize("Best CRM for a Small Biz 2026") == \
        ["best", "crm", "for", "small", "biz", "2026"]        # a 被去单字符
    assert tokenize("CRM 软件 对比") == ["crm", "软", "件", "对", "比"]  # CJK 单字保留
    rows = [
        ("best crm for small business", "best crm for small business"),   # 排除:完全相同
        ("best crm for small business", "top rated crm software 2026 pricing"),
        ("best crm for small business", "acme vs beta crm comparison"),
        ("crm 软件对比", "crm 系统价格对比 2026"),
        ("how to choose helpdesk software", "helpdesk software buying guide"),
    ]
    res = analyze(rows)
    assert res["rows"] == 5 and res["total_queries"] == 4
    assert res["excluded_same"] == 1 and res["excluded_sentinel"] == 0
    assert res["fanout_prompts"] == 3                     # 3 个 prompt 发生了 fan-out
    assert abs(res["avg_per_execution"] - 4 / 3) < 1e-9   # 4 条查询 / 3 个 prompt
    # 行 2: added={top,rated,software,2026,pricing} dropped={best,for,small,business} preserved={crm}
    assert res["added"]["software"] == 1 and res["added"]["pricing"] == 1
    # 行 3: added={acme,vs,beta} dropped={best,for,small,business} preserved={crm}
    assert res["added"]["vs"] == 1 and res["added"]["acme"] == 1
    assert res["dropped"]["best"] == 2 and res["dropped"]["business"] == 2
    assert res["preserved"]["crm"] == 3
    # 行 4(中文): added={系,统,价,格,2026} dropped={软,件} preserved={crm,对,比}
    assert res["added"]["价"] == 1 and res["dropped"]["软"] == 1
    assert res["preserved"]["对"] == 1 and res["preserved"]["比"] == 1
    assert res["added"]["2026"] == 2
    # 行 5: added={buying,guide} dropped={how,to,choose} preserved={helpdesk,software}
    assert res["added"]["guide"] == 1 and res["dropped"]["choose"] == 1
    assert res["preserved"]["software"] == 1
    # 哨兵排除
    res2 = analyze([("p", "unavailable"), ("p", "q word")])
    assert res2["excluded_sentinel"] == 1 and res2["total_queries"] == 1
    out = render(res, top=20)
    assert "avgPerExecution = 4 / 3 = 1.33" in out and "preserved" in out
    # CSV 读取路径
    tmp = tempfile.mkdtemp(prefix="fanout_")
    path = os.path.join(tmp, "in.csv")
    with open(path, "w", encoding="utf-8") as f:
        f.write("prompt,web_query\n")
        for p, q in rows:
            f.write('"%s","%s"\n' % (p, q))
    assert read_rows(path) == rows
    print("[self-test] PASS fanout_analysis(5 行 CSV,三桶词频,avgPerExecution=1.33,"
          "排除同文查询/哨兵,CJK 单字,vs 刻意不停用)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", nargs="?", help="CSV(prompt,web_query 两列)")
    ap.add_argument("--top", type=int, default=20, help="每桶显示 top N(默认 20)")
    ap.add_argument("--self-test", action="store_true", help="冒烟自测(不联网)")
    args = ap.parse_args(argv)
    if args.self_test:
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL fanout_analysis")
            return 1
    if not args.input:
        ap.error("需要 input.csv 或 --self-test")
    rows = read_rows(args.input)
    if not rows:
        print("错误: %s 中没有读到 (prompt, web_query) 行" % args.input, file=sys.stderr)
        return 1
    print(render(analyze(rows), top=args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
