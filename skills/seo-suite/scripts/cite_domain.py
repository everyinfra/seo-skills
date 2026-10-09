#!/usr/bin/env python3
"""CITE 域名评级(结构化输入版,40 项基准的可机判切片)。stdlib-only。

四组(权重):C 引用 .35 / I 身份 .20 / T 信任 .25 / E 显赫 .20。
计分:Pass=10 / Partial=5 / Fail=0;未观测字段 = unknown,不计组内均值;
某组全 unknown 时,该组权重在已知组间按比例重分配。

输入 JSON(--input answers.json),模板:
{
  "referring_domains": 1200,
  "dr_distribution": {"0-30": 400, "30-50": 400, "50-70": 300, "70-100": 100},
  "anchor_exact_ratio": 0.25,
  "c_block_concentration": 0.15,
  "months": [{"month": "2026-01", "links": 40}, {"month": "2026-02", "links": 45}],
  "engines_cited": {"chatgpt": 25, "perplexity": 12, "gemini": 3},
  "reviews": ["Acme is great", "..."],
  "brand": "Acme",
  "outbound_links": 800,
  "editorial_ratio": 0.65,
  "link_traffic_coherent": true,
  "manual_penalty": false
}
(dr_distribution 也接受 [{"dr": 55, "count": 100}, ...];reviews 也接受整数计数;
比例字段接受 0.25 或 25。)

机判项:
  C1 引域≥500 / C2 DR50+ 份额≥20% / C3 出链<1000 / C4 无月份>3×月均 /
  C5 ≥2 引擎≥10 查询被引 / C6 60% 编辑链
  I1 品牌词行数(reviews 中含品牌词的行 ≥5)/ I2 品牌词行占比 ≥50%
  T1 C-block 集中度≤20% / T2 精确匹配锚文本比≤30% / T3 链接·流量相干性(人工标记) /
  T4 无人工处罚记录
  E1 引擎被引查询总量 / E2 评论量

VETO(信任组,人工红线):C-block>20%=PBN;链接·流量相干性人工标记=false;
人工处罚=true。1 个 veto → 总分封顶 59;≥2 个 → BLOCK(拒绝出分,退出码 2)。

用法:
  python3 cite_domain.py --input answers.json
  python3 cite_domain.py --template            # 打印输入 JSON 模板
  python3 cite_domain.py --self-test
"""
import argparse
import json
import re
import sys
import traceback

WEIGHTS = {"C": 0.35, "I": 0.20, "T": 0.25, "E": 0.20}
PASS, PARTIAL, FAIL = 10, 5, 0
TEMPLATE = {
    "referring_domains": 1200,
    "dr_distribution": {"0-30": 400, "30-50": 400, "50-70": 300, "70-100": 100},
    "anchor_exact_ratio": 0.25,
    "c_block_concentration": 0.15,
    "months": [{"month": "2026-01", "links": 40}],
    "engines_cited": {"chatgpt": 25, "perplexity": 12, "gemini": 3},
    "reviews": ["Acme 好用", "not bad"],
    "brand": "Acme",
    "outbound_links": 800,
    "editorial_ratio": 0.65,
    "link_traffic_coherent": True,
    "manual_penalty": False,
}


def as_ratio(v):
    """0.25 / 25 / '25%' → 0.25;None → None。"""
    if v is None or v == "":
        return None
    if isinstance(v, str):
        v = v.strip().rstrip("%")
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x / 100 if x > 1 else x


def as_bool(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("1", "true", "yes", "y", "是")


def dr50_share(dist):
    """dr_distribution → DR50+ 份额;解析失败返回 None。"""
    if not isinstance(dist, (dict, list)):
        return None
    total = hi = 0.0
    pairs = dist.items() if isinstance(dist, dict) else \
        [(d.get("dr"), d.get("count")) for d in dist if isinstance(d, dict)]
    for key, cnt in pairs:
        try:
            cnt = float(cnt)
        except (TypeError, ValueError):
            return None
        nums = [int(n) for n in re.findall(r"\d+", str(key))]
        if not nums:
            return None
        lower = nums[0]  # "50-70"/"50+"/"70-100" 的下界
        total += cnt
        if lower >= 50:
            hi += cnt
    return (hi / total) if total else None


def grade(value, rules):
    """rules = [((lo, hi), pts, label), ...] 自上而下首个命中区间者胜;
    (None, None) 为兜底区间。value=None → unknown(不计均值)。"""
    if value is None:
        return None, "unknown"
    for (lo, hi), pts, label in rules:
        if (lo is None or value >= lo) and (hi is None or value <= hi):
            return pts, label
    return rules[-1][1], rules[-1][2]


def evaluate(d):
    """返回 (items, vetoes)。item = {group, code, name, pts, label, value}。"""
    items, vetoes = [], []

    def add(group, code, name, pts, label, value):
        items.append({"group": group, "code": code, "name": name,
                      "pts": pts, "label": label, "value": value})

    # ---- C 引用 ----
    rd = d.get("referring_domains")
    rd = float(rd) if isinstance(rd, (int, float)) and rd >= 0 else None
    pts, label = grade(rd, [((500, None), PASS, "≥500"),
                            ((100, None), PARTIAL, "100-499"),
                            ((-1, None), FAIL, "<100")])
    add("C", "C1", "引用域数量", pts, label, rd)
    share50 = dr50_share(d.get("dr_distribution"))
    pts, label = grade(share50, [((0.20, None), PASS, "DR50+ ≥20%"),
                                 ((0.10, None), PARTIAL, "DR50+ 10-20%"),
                                 ((-1, None), FAIL, "DR50+ <10%")])
    add("C", "C2", "DR50+ 份额", pts, label, share50)
    ob = d.get("outbound_links")
    ob = float(ob) if isinstance(ob, (int, float)) and ob >= 0 else None
    pts, label = grade(None if ob is None else -ob,
                       [((-1000 + 1e-9, None), PASS, "出链<1000"),
                        ((-3000 + 1e-9, None), PARTIAL, "出链 1000-3000"),
                        ((None, None), FAIL, "出链>3000")])
    add("C", "C3", "出站链接数", pts, label, ob)
    months = d.get("months") or []
    ratio = None
    if isinstance(months, list) and months:
        links = []
        for m in months:
            try:
                links.append(float(m.get("links", m.get("count"))))
            except (AttributeError, TypeError, ValueError):
                links = []
                break
        if links:
            mean = sum(links) / len(links)
            ratio = max(links) / mean if mean else None
    pts, label = grade(None if ratio is None else -ratio,
                       [((-3 - 1e-9, None), PASS, "峰值≤3×月均"),
                        ((-5 - 1e-9, None), PARTIAL, "峰值 3-5×月均"),
                        ((None, None), FAIL, "峰值>5×月均")])
    add("C", "C4", "链接增速平滑度", pts, label, ratio)
    eng = d.get("engines_cited")
    strong = None
    if isinstance(eng, dict) and eng:
        try:
            strong = sum(1 for v in eng.values() if float(v) >= 10)
        except (TypeError, ValueError):
            strong = None
    pts, label = grade(strong, [((2, None), PASS, "≥2 引擎≥10 查询被引"),
                                ((1, None), PARTIAL, "1 引擎≥10"),
                                ((-1, None), FAIL, "无")])
    add("C", "C5", "跨引擎被引广度", pts, label, strong)
    ed = as_ratio(d.get("editorial_ratio"))
    pts, label = grade(ed, [((0.60, None), PASS, "编辑链≥60%"),
                            ((0.40, None), PARTIAL, "编辑链 40-60%"),
                            ((-1, None), FAIL, "编辑链<40%")])
    add("C", "C6", "编辑链占比", pts, label, ed)

    # ---- I 身份 ----
    brand = d.get("brand")
    reviews = d.get("reviews")
    rows = brand_rows = None
    if isinstance(reviews, list):
        rows = [str(r) for r in reviews]
        if brand:
            b = str(brand).lower()
            brand_rows = sum(1 for r in rows if b in r.lower())
    pts, label = grade(brand_rows, [((5, None), PASS, "品牌词行 ≥5"),
                                    ((1, None), PARTIAL, "品牌词行 1-4"),
                                    ((-1, None), FAIL, "品牌词行 0")])
    add("I", "I1", "品牌词行数(reviews)", pts, label, brand_rows)
    ratio_ib = (brand_rows / len(rows)) if rows and brand_rows is not None and rows else None
    pts, label = grade(ratio_ib, [((0.50, None), PASS, "占比≥50%"),
                                  ((0.20, None), PARTIAL, "占比 20-50%"),
                                  ((-1, None), FAIL, "占比<20%")])
    add("I", "I2", "品牌词行占比", pts, label, ratio_ib)

    # ---- T 信任 ----
    cb = as_ratio(d.get("c_block_concentration"))
    if cb is not None and cb > 0.20:
        vetoes.append("T-VETO C-block 集中度 %.0f%% >20%% → PBN 信号" % (100 * cb))
    pts, label = grade(cb, [((0, 0.20), PASS, "≤20%"),
                            ((0, 0.35), PARTIAL, "20-35%"),
                            ((-1, None), FAIL, ">35%")])
    add("T", "T1", "C-block 集中度", pts, label, cb)
    ae = as_ratio(d.get("anchor_exact_ratio"))
    pts, label = grade(ae, [((0, 0.30), PASS, "精确锚≤30%"),
                            ((0, 0.60), PARTIAL, "精确锚 30-60%"),
                            ((-1, None), FAIL, "精确锚>60%")])
    add("T", "T2", "精确匹配锚文本比", pts, label, ae)
    ltc = as_bool(d.get("link_traffic_coherent"))
    if ltc is False:
        vetoes.append("T-VETO 链接·流量相干性人工标记 = 不相干(人工 veto)")
    add("T", "T3", "链接·流量相干性(人工标记)",
        {True: PASS, False: FAIL}.get(ltc), {True: "相干", False: "不相干"}.get(ltc, "unknown"), ltc)
    pen = as_bool(d.get("manual_penalty"))
    if pen is True:
        vetoes.append("T-VETO 人工处罚记录(人工 veto)")
    add("T", "T4", "人工处罚记录",
        {True: FAIL, False: PASS}.get(pen), {True: "有处罚", False: "无"}.get(pen, "unknown"), pen)

    # ---- E 显赫 ----
    total_q = None
    if isinstance(eng, dict) and eng:
        try:
            total_q = sum(float(v) for v in eng.values())
        except (TypeError, ValueError):
            total_q = None
    pts, label = grade(total_q, [((50, None), PASS, "被引查询 ≥50"),
                                 ((20, None), PARTIAL, "被引查询 20-50"),
                                 ((-1, None), FAIL, "被引查询 <20")])
    add("E", "E1", "跨引擎被引查询总量", pts, label, total_q)
    nrev = len(reviews) if isinstance(reviews, list) else \
        (float(reviews) if isinstance(reviews, (int, float)) else None)
    pts, label = grade(nrev, [((10, None), PASS, "评论 ≥10"),
                              ((3, None), PARTIAL, "评论 3-10"),
                              ((-1, None), FAIL, "评论 <3")])
    add("E", "E2", "公开评论量", pts, label, nrev)
    return items, vetoes


def score(items, vetoes):
    groups = {}
    for g in WEIGHTS:
        gi = [i for i in items if i["group"] == g and i["pts"] is not None]
        groups[g] = (sum(i["pts"] for i in gi) / len(gi) * 10) if gi else None
    known = {g: s for g, s in groups.items() if s is not None}
    total = None
    if known:
        wsum = sum(WEIGHTS[g] for g in known)
        total = sum(WEIGHTS[g] * s for g, s in known.items()) / wsum
    capped = False
    if len(vetoes) == 1 and total is not None and total > 59:
        total, capped = 59.0, True
    band = None if total is None else \
        "A(优)" if total >= 80 else "B(良)" if total >= 60 else \
        "C(中)" if total >= 40 else "D(差)"
    return {"groups": groups, "total": total, "capped": capped,
            "band": band, "blocked": len(vetoes) >= 2}


def render(items, vetoes, sc):
    gname = {"C": "C 引用(.35)", "I": "I 身份(.20)",
             "T": "T 信任(.25)", "E": "E 显赫(.20)"}
    L = ["== CITE 域名评级(结构化输入;Pass10/Partial5/Fail0,unknown 不计均值) =="]
    for g in ("C", "I", "T", "E"):
        gs = sc["groups"][g]
        L.append("[%s] %s" % (gname[g], "N/A(全 unknown)" if gs is None else "%.1f" % gs))
        for i in items:
            if i["group"] == g:
                val = "" if i["value"] is None else " | 观测值=%s" % i["value"]
                pts = "unknown" if i["pts"] is None else "%d" % i["pts"]
                L.append("  %-4.4s %-22.22s %-7.7s %-16.16s%s"
                         % (i["code"], i["name"], pts, i["label"], val))
    if vetoes:
        L.append("VETO:")
        for v in vetoes:
            L.append("  [X] %s" % v)
    else:
        L.append("VETO: 无")
    if sc["blocked"]:
        L.append("总分 = BLOCK(≥2 个 veto:进入人工复核,本工具拒绝出分)")
    else:
        L.append("总分 = %s%s" % ("N/A(无任何已观测项)" if sc["total"] is None
                                  else "%.1f → band %s" % (sc["total"], sc["band"]),
                                  "(1 个 veto,封顶 59)" if sc["capped"] else ""))
    return "\n".join(L)


def _self_test():
    d = {
        "referring_domains": 1200,
        "dr_distribution": {"0-30": 400, "30-50": 400, "50-70": 300, "70-100": 100},
        "anchor_exact_ratio": 0.25,
        "c_block_concentration": 0.15,
        "months": [{"month": "2026-%02d" % i, "links": 40 + i} for i in range(1, 13)],
        "engines_cited": {"chatgpt": 25, "perplexity": 12, "gemini": 3},
        "reviews": ["Acme is great", "Acme saved us", "Acme support is good",
                    "love Acme", "Acme forever", "meh", "ok", "Acme again"],
        "brand": "Acme",
        "outbound_links": 800,
        "editorial_ratio": 0.65,
        "link_traffic_coherent": True,
        "manual_penalty": False,
    }
    items, vetoes = evaluate(d)
    sc = score(items, vetoes)
    pts = {i["code"]: i["pts"] for i in items}
    assert not vetoes
    assert pts["C1"] == 10 and pts["C2"] == 10          # 引域 1200;DR50+ = 33.3%
    assert abs(dr50_share(d["dr_distribution"]) - 400 / 1200) < 1e-9
    assert pts["C3"] == 10 and pts["C4"] == 10          # 出链 800;峰值 52/40.5 < 3×
    assert pts["C5"] == 10                              # chatgpt+perplexity ≥10
    assert pts["C6"] == 10                              # 0.65 编辑链
    assert pts["I1"] == 10 and pts["I2"] == 10          # 品牌词 6 行 / 8 行
    assert pts["T1"] == 10 and pts["T2"] == 10 and pts["T3"] == 10 and pts["T4"] == 10
    assert pts["E1"] == 5 and pts["E2"] == 5            # 总量 40 → partial;评论 8 → partial
    assert abs(sc["total"] - 90.0) < 1e-9, sc["total"]  # .35*100+.20*100+.25*100+.20*50
    assert sc["band"].startswith("A") and not sc["blocked"]

    # 1 veto → 封顶 59
    d2 = dict(d, c_block_concentration=0.30, dr_distribution={"0-30": 900, "30-50": 300})
    _, v2 = evaluate(d2)
    assert any("PBN" in x for x in v2) and len(v2) == 1
    sc2 = score(evaluate(d2)[0], v2)
    assert sc2["total"] == 59.0 and sc2["capped"] and not sc2["blocked"]

    # 2 veto → BLOCK
    d3 = dict(d, c_block_concentration=0.30, manual_penalty=True)
    _, v3 = evaluate(d3)
    assert len(v3) == 2
    assert score(evaluate(d3)[0], v3)["blocked"]

    # unknown 不计均值:去掉 reviews/brand
    d4 = {k: v for k, v in d.items() if k not in ("reviews", "brand", "engines_cited")}
    items4, _ = evaluate(d4)
    sc4 = score(items4, [])
    assert sc4["groups"]["I"] is None and sc4["groups"]["E"] is None
    assert abs(sc4["total"] - 100.0) < 1e-9              # 权重重分配后 C/T 满分
    # 比例字段弹性
    assert as_ratio(25) == 0.25 and as_ratio("25%") == 0.25 and as_ratio(0.25) == 0.25
    assert as_ratio(None) is None
    print("[self-test] PASS cite_domain(总分 90;1 veto 封顶 59;2 veto BLOCK;"
          "unknown 重分配;比例字段弹性)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", help="结构化输入 JSON 路径")
    ap.add_argument("--template", action="store_true", help="打印输入 JSON 模板")
    ap.add_argument("--self-test", action="store_true", help="冒烟自测(不联网)")
    args = ap.parse_args(argv)
    if args.self_test:
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL cite_domain")
            return 1
    if args.template:
        print(json.dumps(TEMPLATE, ensure_ascii=False, indent=2))
        return 0
    if not args.input:
        ap.error("需要 --input answers.json(或 --template / --self-test)")
    try:
        with open(args.input, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError) as e:
        print("错误: 无法读取 %s: %s" % (args.input, e), file=sys.stderr)
        return 1
    items, vetoes = evaluate(d)
    sc = score(items, vetoes)
    print(render(items, vetoes, sc))
    return 2 if sc["blocked"] else 0


if __name__ == "__main__":
    sys.exit(main())
