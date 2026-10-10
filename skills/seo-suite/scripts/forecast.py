#!/usr/bin/env python3
"""SEO 流量与收入预测(seoClarity 六步官方方法论,stdlib 零网络)。
六步(官方,口径见 references/research/borrow-specs.md E1):
  1 CTR 曲线:--ctr 给自有 GSC 90 天曲线(官方建议,预测只用非品牌);
    不给则用内置行业默认曲线——估算 [est],锚点与 gsc_mining.py EXP_CTR 同源,
    锚点间线性插值
  2 估算:est_traffic = Σ search_volume × CTR(current_position)(全部词)
  3 校准:--actual {GA 真实月流量} → calibration_factor = actual/est;
    --save-calibration 持久化,下次 --load-calibration 自动套用
    (四家方法论中唯一明示的"模型自校准"环节)
  4 CPC 竞争:acquisition_value = traffic × CPC(等效付费成本)
  5 三情景【官方枚举】(>30 位的词不预测——官方口径"Google 认为相关但不权威"
    区间之外):
      rank3  全部词到第 3 位(已优于该位的保持原位,不预测退步)
      pct10  位次提升 10%(保守默认)
      pos2   每词升 2 位
    orders = traffic × CVR;value = orders × AOV(或 --lead-value)
  6 汇报:商业提案双结构(省钱:Traffic Potential×CPC=等效付费成本,提案只投
    10%;赚钱:流量×CVR×AOV)+ ROI 五法清单;管理层模板 templates/monitor/forecast-report.md

用法:
  python3 forecast.py --kws kws.csv [--ctr ctr.csv] [--cvr 0.02] [--aov 100]
      [--lead-value V] [--scenario pct10|pos2|rank3|rankN|pctN|posN]
      [--actual N] [--save-calibration calibration.json]
      [--load-calibration calibration.json] [--invest M] [--json]
kws.csv 列:keyword, search_volume, current_position[, cpc];无 cpc 列时
acquisition_value 记 N/A。ctr.csv 列:position, ctr(接受 '3.2%' 或 0.032)。
--json 输出带 schema_version。
退出码:0=跑完;2=文件/格式/参数错误。"""
import argparse
import csv
import json
import re
import sys
from datetime import date

SCHEMA_VERSION = 1
EXCLUDE_ABOVE = 30        # 官方口径:>30 位("相关但不权威")不预测
PROPOSE_PAID_SHARE = 0.10  # 省钱结构提案:只投等效付费成本的 10%
# 与 gsc_mining.py EXP_CTR 同源锚点(行业默认估算 [est]);本脚本在锚点间线性插值
DEFAULT_CTR = [(1, 0.28), (2, 0.15), (3, 0.11), (5, 0.07),
               (10, 0.03), (20, 0.01), (999, 0.005)]
CANONICAL_SCENARIOS = [("pct", 10), ("pos", 2), ("rank", 3)]  # 保守→中档→目标

ROI_FIVE_METHODS = [
    ("实际转化", "上线后用真实 orders×AOV 对比投入(最硬口径,滞后一个周期)"),
    ("Traffic Value", "流量 × 平均 CPC 的等效媒体价值(步 4 已列)"),
    ("相对付费省钱", "同等点击若走付费的 Cost − SEO 投入(省钱结构的直接兑现)"),
    ("付费 CVR 估算", "无自有 CVR 时用付费搜索 CVR 作代理估算自然转化"),
    ("按项目 tag 归因", "SEO 落地页打 campaign tag,GA 按项目归因收入"),
]

ASSUMPTIONS = [
    "CTR 模型是估算 [est]:默认为行业 benchmark;官方建议用自有 GSC 90 天 "
    "移动/桌面 × 品牌/非品牌 曲线(预测只用非品牌)",
    f">{EXCLUDE_ABOVE} 位的词不预测(官方口径:\"Google 认为相关但不权威\"区间之外)",
    "位次情景是目标态假设,不是承诺;CTR 沿曲线插值,AIO/广告位会压低实际 CTR",
    "校准系数只修正总量级,不修正词间分布;CVR/AOV 为全局常数,未按词分段",
]


class DataError(Exception):
    """输入文件/参数错误 → exit 2。"""


# ---------- CSV 载入(列名宽容,与 seo_vs_ads.py 同套路) ----------

def _find_col(fieldnames, names):
    low = {c.strip().lower(): c for c in fieldnames if c}
    return next((low[n] for n in names if n in low), None)


def _load_csv(path, required, spec):
    """spec: {逻辑名: [候选列名]};返回 [ {逻辑名: 值} ] 或抛 DataError。"""
    try:
        f = open(path, encoding="utf-8-sig", newline="")
    except OSError as e:
        raise DataError(f"无法读取 {path}: {e}")
    with f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames:
            raise DataError(f"{path}: 空 CSV")
        cols = {k: _find_col(rdr.fieldnames, v) for k, v in spec.items()}
        missing = [k for k in required if not cols[k]]
        if missing:
            raise DataError(f"{path}: 缺列 {missing},实际列={list(rdr.fieldnames)}")
        return [{k: (row.get(c) or "").strip() if c else "" for k, c in cols.items()}
                for row in rdr]


def _num(s, what, lineno):
    try:
        return float((s or "").replace(",", ""))
    except ValueError:
        raise DataError(f"kws.csv 行 {lineno}: {what} 非数值: {s!r}")


def load_kws(path):
    rows = _load_csv(path, ["keyword", "volume", "position"],
                     {"keyword": ["keyword", "query", "top queries", "关键词"],
                      "volume": ["search_volume", "volume", "searches",
                                 "monthly_searches", "搜索量", "月搜索量"],
                      "position": ["current_position", "position",
                                   "avg. position", "average position",
                                   "当前位次", "排名"],
                      "cpc": ["cpc", "avg cpc", "avg. cpc", "平均cpc"]})
    kws, has_cpc = [], False
    for i, r in enumerate(rows, 2):
        kw = r["keyword"]
        if not kw:
            continue
        vol = _num(r["volume"], "search_volume", i)
        pos = _num(r["position"], "current_position", i)
        if pos <= 0:
            raise DataError(f"kws.csv 行 {i}: current_position 必须 >0(得到 {pos})")
        if vol < 0:
            raise DataError(f"kws.csv 行 {i}: search_volume 不能为负(得到 {vol})")
        cpc = 0.0
        if r["cpc"]:
            has_cpc = True
            cpc = _num(r["cpc"], "cpc", i)
        kws.append({"keyword": kw, "volume": vol, "position": pos, "cpc": cpc})
    if not kws:
        raise DataError(f"{path}: 无有效关键词行")
    return kws, has_cpc


def parse_ctr(v):
    """'3.2%' 或 0.032 双格式(与 gsc_mining.parse_ctr 同口径)。
    带 % 后缀的一律除以 100——否则 '1%' 这类边界值会被当成 100%。"""
    s = (v or "").strip()
    if s.endswith("%"):
        try:
            return float(s[:-1]) / 100
        except ValueError:
            raise DataError(f"ctr.csv: ctr 非数值: {s!r}")
    try:
        f = float(s)
    except ValueError:
        raise DataError(f"ctr.csv: ctr 非数值: {s!r}")
    return f / 100 if f > 1 else f


def load_curve(path):
    rows = _load_csv(path, ["position", "ctr"],
                     {"position": ["position", "pos", "排名"],
                      "ctr": ["ctr", "点击率", "click_through_rate"]})
    anchors = {}
    for i, r in enumerate(rows, 2):
        try:
            p = float((r["position"] or "").replace(",", ""))
        except ValueError:
            raise DataError(f"ctr.csv 行 {i}: position 非数值: {r['position']!r}")
        c = parse_ctr(r["ctr"])
        if not 0 < c <= 1:
            raise DataError(f"ctr.csv 行 {i}: ctr 须在 (0,1]: {c}")
        anchors[p] = c
    if not anchors:
        raise DataError(f"{path}: 无有效曲线锚点")
    return sorted(anchors.items())


def ctr_at(pos, anchors=None):
    """锚点间线性插值;曲线两端 clamp。"""
    if anchors is None:
        anchors = DEFAULT_CTR
    if pos <= anchors[0][0]:
        return anchors[0][1]
    if pos >= anchors[-1][0]:
        return anchors[-1][1]
    for (p1, c1), (p2, c2) in zip(anchors, anchors[1:]):
        if p1 <= pos <= p2:
            if p2 == p1:
                return c2
            f = (pos - p1) / (p2 - p1)
            return c1 + f * (c2 - c1)
    return anchors[-1][1]


# ---------- 情景(seoClarity 官方枚举) ----------

def parse_scenario(s):
    """'rank3'/'pct10'/'pos2'(及任意 rankN/pctN/posN)→ (kind, n, 规则文本)。"""
    s = (s or "").strip().lower()
    m = re.fullmatch(r"(rank|pct|pos)(\d+)", s)
    if not m:
        raise DataError(f"未知 --scenario: {s!r};官方枚举形如 rank3 / pct10 / pos2"
                        "(也接受任意 rankN/pctN/posN)")
    kind, n = m.group(1), int(m.group(2))
    if kind == "rank" and n < 1:
        raise DataError("rankN 的 N 须 ≥1")
    if kind == "pct" and not 1 <= n <= 99:
        raise DataError("pctN 的 N 须在 1-99(官方保守档 10-15)")
    if kind == "pos" and n < 1:
        raise DataError("posN 的 N 须 ≥1")
    rule = {"rank": f"全部词到第 {n} 位(已优于该位的保持原位)",
            "pct": f"位次提升 {n}%" + ("(保守默认)" if n == 10 else ""),
            "pos": f"每词升 {n} 位"}[kind]
    return kind, n, rule


def new_position(kind, n, pos):
    """目标位次(不劣于当前):rank→min(pos,N);pct→pos×(1−N%);pos→pos−N;均 clamp≥1。"""
    if kind == "rank":
        return min(pos, float(n))
    if kind == "pct":
        return max(1.0, pos * (1 - n / 100.0))
    return max(1.0, pos - n)


def run_scenario(kind, n, rule, eligible, anchors, factor, cvr, vpc, invest,
                 has_cpc, baseline_traffic):
    raw = acq_raw = 0.0
    for k in eligible:
        np_ = new_position(kind, n, k["position"])
        t = k["volume"] * ctr_at(np_, anchors)
        raw += t
        acq_raw += t * k["cpc"]
    traffic = raw * factor
    orders = traffic * cvr
    value = orders * vpc
    return {"name": f"{kind}{n}", "rule": rule,
            "traffic": round(traffic, 2),
            "uplift_traffic": round(traffic - baseline_traffic, 2),
            "orders": round(orders, 2), "value": round(value, 2),
            "acquisition_value": round(acq_raw * factor, 2) if has_cpc else None,
            "roi": round((value - invest) / invest, 4) if invest else None}


# ---------- 校准(步 3:模型自校准) ----------

def save_calibration(path, factor, actual, est, kw_count):
    payload = {"schema_version": 1, "calibration_factor": round(factor, 4),
               "actual": actual, "est_traffic": round(est, 2),
               "kw_count": kw_count, "saved_at": date.today().isoformat()}
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
    except OSError as e:
        raise DataError(f"无法写 {path}: {e}")
    return payload


def load_calibration(path):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise DataError(f"无法读取校准文件 {path}: {e}")
    f = d.get("calibration_factor")
    if not isinstance(f, (int, float)) or f <= 0:
        raise DataError(f"{path}: calibration_factor 缺失或非正数")
    return float(f), d


# ---------- 输出 ----------

def fmt(x, nd=1):
    return f"{x:,.{nd}f}" if x is not None else "N/A"


def print_text(rep):
    W = 80
    inp, cal, base = rep["inputs"], rep["calibration"], rep["baseline"]
    prim = rep["primary"]
    print("=" * W)
    print("SEO 流量与收入预测 · seoClarity 六步".center(W))
    print("=" * W)
    vlabel = "AOV" if inp["value_label"] == "aov" else "lead-value"
    print(f"输入: {inp['kws_file']} · {inp['kw_count']} 词 · CTR 曲线: "
          f"{inp['ctr_curve']['source']} · CVR {inp['cvr']:.1%} · "
          f"{vlabel} {inp['value_per_conversion']:g}"
          + (f" · 投入 {inp['invest']:g}" if inp["invest"] else ""))
    print(f"主情景: {rep['primary_scenario']} · 入榜 {base['eligible_kws']} 词"
          f"(>{EXCLUDE_ABOVE} 位不预测,排除 {base['excluded_gt30']} 词)")
    print("-" * W)
    print(f"步1 CTR 曲线: {inp['ctr_curve']['source']};官方建议自有 GSC 90 天"
          "非品牌曲线,行业默认为估算 [est]")
    print(f"步2 估算    : est_traffic = {fmt(rep['est_traffic'])}/月"
          f"(全部 {inp['kw_count']} 词,Σ 量×CTR(当前位),未校准)")
    print(f"步3 校准    : {cal['note']}")
    print("步4 CPC 竞争: acquisition_value(当前,等效付费成本)= "
          + (fmt(rep["step4_current_acquisition"]) + "/月 [est]"
             if rep["step4_current_acquisition"] is not None
             else "N/A(--kws 无 cpc 列)"))
    print("步5 三情景  : 见下表;orders=traffic×CVR,value=orders×"
          f"{vlabel};>30 位不预测")
    print("步6 汇报    : 管理层模板 templates/monitor/forecast-report.md")
    print("-" * W)
    print(f"情景对照(当前基线流量 {fmt(base['traffic'])}/月,"
          f"订单 {fmt(base['orders'])}/月,价值 {fmt(base['value'])}/月):")
    print(f"  {'情景':<8}{'规则':<30}{'流量/月':>9} {'Δ流量':>9} "
          f"{'订单/月':>8} {'价值/月':>10} {'等效付费/月':>10} {'ROI':>8}")
    for s in rep["scenarios"]:
        star = "*" if s["name"] == rep["primary_scenario"] else ""
        roi = f"{s['roi']:+.0%}" if s["roi"] is not None else "-"
        print(f"  {s['name'] + star:<8}{s['rule']:<30}{s['traffic']:>9,.1f} "
              f"{s['uplift_traffic']:>+9,.1f} {s['orders']:>8,.1f} "
              f"{s['value']:>10,.1f} {fmt(s['acquisition_value']):>10} {roi:>8}")
    print(f"  (*=本次主情景;ROI=(价值−投入)/投入,需 --invest;"
          f"无 cpc 列时等效付费为 N/A)")
    print("-" * W)
    print("商业提案 · 双结构")
    sm = rep["proposal"]["save_money"]
    if sm["equivalent_paid_cost"] is not None:
        print(f"  [省钱] Traffic Potential × CPC = 等效付费成本")
        print(f"         {prim['name']} 预测流量 {fmt(prim['traffic'])}/月 × 自有 CPC → "
              f"{fmt(sm['equivalent_paid_cost'])}/月 [est]")
        print(f"         提案:只投其 10% ≈ {fmt(sm['propose_invest_10pct'])}/月,"
              "拿到同等自然流量即打平付费成本")
    else:
        print("  [省钱] N/A:--kws 无 cpc 列;补 CPC 后可算等效付费成本"
              "(投 10% 的提案口径依赖它)")
    mm = rep["proposal"]["make_money"]
    print("  [赚钱] 流量 × CVR × " + vlabel)
    print(f"         {prim['name']} 流量 {fmt(prim['traffic'])}/月 × "
          f"CVR {inp['cvr']:.1%} × {vlabel} {inp['value_per_conversion']:g} → "
          f"订单 {fmt(mm['orders'])}/月,价值 {fmt(mm['value'])}/月")
    if rep["primary"]["roi"] is not None:
        print(f"         ROI = ({fmt(mm['value'])} − {inp['invest']:g}) / "
              f"{inp['invest']:g} = {rep['primary']['roi']:+.0%}")
    print("ROI 五法")
    for i, (m, how) in enumerate(ROI_FIVE_METHODS, 1):
        print(f"  {i}. {m:<14}: {how}")
    print("-" * W)
    print("假设与局限")
    for a in rep["assumptions"]:
        print(f"  - {a}")
    print("=" * W)


# ---------- 主流程 ----------

def build_rep(a):
    kws, has_cpc = load_kws(a.kws)
    if a.ctr:
        anchors = load_curve(a.ctr)
        curve_src = f"custom({a.ctr},自有 GSC 曲线[官方建议])"
    else:
        anchors = DEFAULT_CTR
        curve_src = "内置行业默认 [est](官方建议换自有 GSC 90 天非品牌曲线)"

    vpc, vlabel = (a.lead_value, "lead_value") if a.lead_value is not None \
        else (a.aov, "aov")

    # 步 2:估算(全部词,未校准)
    est = sum(k["volume"] * ctr_at(k["position"], anchors) for k in kws)

    # 步 3:校准(--actual 优先于 --load-calibration)
    factor, cal_src, actual, cal_note = 1.0, "none", None, \
        "未校准(factor=1.00)—— --actual {GA 真实月流量} 可自校准并 --save-calibration 持久化"
    if a.load_calibration:
        factor, d = load_calibration(a.load_calibration)
        cal_src, actual = f"loaded({a.load_calibration})", d.get("actual")
        cal_note = (f"factor={factor:.2f}(loaded: {a.load_calibration},"
                    f"saved_at={d.get('saved_at', '?')})")
    if a.actual is not None:
        if est <= 0:
            raise DataError("无法校准:估算流量为 0")
        factor = a.actual / est
        cal_src, actual = "actual", a.actual
        cal_note = f"factor={factor:.2f}(actual={a.actual:g} vs est={est:.2f})"
    if a.save_calibration:
        if a.actual is None:
            raise DataError("--save-calibration 须与 --actual 同用(保存本次新校准系数)")
        save_calibration(a.save_calibration, factor, a.actual, est, len(kws))
        cal_note += f" → 已持久化 {a.save_calibration}(下次 --load-calibration 自动套用)"

    eligible = [k for k in kws if k["position"] <= EXCLUDE_ABOVE]
    excluded = len(kws) - len(eligible)

    base_raw = sum(k["volume"] * ctr_at(k["position"], anchors) for k in eligible)
    base_traffic = base_raw * factor
    baseline = {"eligible_kws": len(eligible), "excluded_gt30": excluded,
                "traffic": round(base_traffic, 2),
                "orders": round(base_traffic * a.cvr, 2),
                "value": round(base_traffic * a.cvr * vpc, 2),
                "acquisition_value": round(sum(k["volume"] * ctr_at(k["position"], anchors)
                                                * k["cpc"] for k in eligible) * factor, 2)
                if has_cpc else None}

    scen = []
    for kind, n in CANONICAL_SCENARIOS:
        scen.append(run_scenario(kind, n, parse_scenario(f"{kind}{n}")[2], eligible,
                                 anchors, factor, a.cvr, vpc, a.invest, has_cpc,
                                 base_traffic))
    pkind, pn, prule = parse_scenario(a.scenario)
    primary_name = f"{pkind}{pn}"
    by_name = {s["name"]: s for s in scen}
    if primary_name not in by_name:
        by_name[primary_name] = run_scenario(pkind, pn, prule, eligible, anchors,
                                             factor, a.cvr, vpc, a.invest, has_cpc,
                                             base_traffic)
        scen.append(by_name[primary_name])
    prim = by_name[primary_name]

    step4_acq = round(sum(k["volume"] * ctr_at(k["position"], anchors) * k["cpc"]
                          for k in kws) * factor, 2) if has_cpc else None
    sm_eq = prim["acquisition_value"]
    rep = {
        "schema_version": SCHEMA_VERSION,
        "method": "seoClarity-six-step",
        "inputs": {"kws_file": a.kws, "kw_count": len(kws), "cvr": a.cvr,
                   "value_per_conversion": vpc, "value_label": vlabel,
                   "invest": a.invest, "scenario": primary_name,
                   "ctr_curve": {"source": curve_src,
                                 "anchors": [[p, c] for p, c in anchors]}},
        "calibration": {"factor": round(factor, 4), "source": cal_src,
                        "actual": actual, "est_traffic_calibrated": round(est * factor, 2),
                        "note": cal_note},
        "est_traffic": round(est, 2),
        "step4_current_acquisition": step4_acq,
        "baseline": baseline,
        "scenarios": scen,
        "primary_scenario": primary_name,
        "primary": prim,
        "proposal": {
            "save_money": {
                "equivalent_paid_cost": sm_eq,
                "propose_invest_10pct": round(sm_eq * PROPOSE_PAID_SHARE, 2)
                if sm_eq is not None else None,
                "note": "Traffic Potential × CPC = 等效付费成本;提案只投其 10%"
                        f"(={PROPOSE_PAID_SHARE:.0%})"},
            "make_money": {"orders": prim["orders"], "value": prim["value"],
                           "formula": "traffic × CVR × " + vlabel},
            "roi_five_methods": [{"method": m, "how": h} for m, h in ROI_FIVE_METHODS]},
        "assumptions": list(ASSUMPTIONS),
    }
    return rep


def build_parser():
    ap = argparse.ArgumentParser(
        prog="forecast.py",
        description="SEO 流量与收入预测(seoClarity 六步官方方法论):"
                    "CTR 曲线→估算→GA 校准→CPC 竞争→三情景→汇报",
        epilog="情景为官方枚举:rank3=全部词到第 3 位 / pct10=位次提升 10%(保守默认)"
               "/ pos2=每词升 2 位;>30 位的词不预测。示例:\n"
               "  python3 forecast.py --kws kws.csv --ctr gsc_ctr.csv --cvr 0.02 "
               "--aov 100 --actual 4200 --save-calibration calibration.json --json")
    ap.add_argument("--kws", required=True,
                    help="关键词 CSV:keyword, search_volume, current_position[, cpc]")
    ap.add_argument("--ctr",
                    help="自有 CTR 曲线 CSV(position, ctr;官方建议用 GSC 90 天非品牌曲线);"
                         "缺省用内置行业默认曲线 [est]")
    ap.add_argument("--cvr", type=float, default=0.02, help="转化率(默认 0.02)")
    ap.add_argument("--aov", type=float, default=100.0, help="客单价(默认 100)")
    ap.add_argument("--lead-value", type=float, default=None,
                    help="每线索价值(替代 --aov 的赚钱口径,如 B2B 线索站)")
    ap.add_argument("--scenario", default="pct10",
                    help="主情景:rank3 / pct10(默认) / pos2(也接受任意 rankN/pctN/posN)")
    ap.add_argument("--actual", type=float, default=None,
                    help="GA 真实月自然流量 → 算校准系数(步 3 模型自校准)")
    ap.add_argument("--save-calibration",
                    help="把本次校准系数持久化为 JSON(须与 --actual 同用)")
    ap.add_argument("--load-calibration",
                    help="载入历史校准系数自动套用")
    ap.add_argument("--invest", type=float, default=None,
                    help="SEO 月投入 → 输出 ROI=(价值−投入)/投入")
    ap.add_argument("--json", action="store_true", help="结构化输出(带 schema_version)")
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        rep = build_rep(a)
    except DataError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print_text(rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
