#!/usr/bin/env python3
"""合成控制法(synthetic control)——did_attribution.py 的 DiD 升级,干预时点分析。
stdlib-only。规格: references/overview/pipeline-completeness.md R6 归因实验。

思路(Abadie/Gapminder 一系): 处理组在干预前的走势,用 donor pool 加权合成一个
"反事实孪生";干预后 处理组−合成组 的差 = 因果效应估计(平行趋势假设被
"合成出同一条 pre 轨迹"替代,不再要求单一对照组走势相似)。

求解(简化,诚实标注):
  * 权重约束在 simplex 上(非负、和=1),目标 = pre 期 RMSE 最小;
  * 坐标下降: 固定其余权重,对每一对 (i,j) 在 w_i+w_j=c 内闭式解一维最优并
    clamp 到 [0,c],默认 10 轮(simplified simplex——**不是** CausalImpact 的
    BSTS/状态空间;不建模趋势项/季节项/自相关,pre 期残差自相关时点估计偏乐观);
  * 闭式推导: w_j=c−w_i 代入后 f(w_i)=‖r−c·d_j−w_i(d_i−d_j)‖²,
    w_i* = Σ diff_t·(r_t−c·d_{j,t}) / Σ diff_t²。

推断(placebo / in-space permutation test):
  * 把每个 donor 轮流当"假处理组",donor pool = 其余 donor(真处理组不入池——
    否则干预效应泄漏进安慰剂对照);
  * p 值 = 假效应 ≥ 真效应的比例(真效应为负时取 ≤;另报 |假|≥|真| 的
    双侧口径 p_abs);donor 数<5 时安慰剂分布分辨率粗,只当方向参考。

闸门: 干预日前必须有 ≥6 个 pre 日期点、≥1 个 post 日期点、≥2 个 donor
(=2 时安慰剂池只剩 1 个 donor,照样跑但标注 weak);序列按日期交集对齐,
缺日期的日期点整点丢弃并计数报告。

输入 CSV: Date,Metric 两列(列名大小写不敏感,同日多行按 Clicks 语义累加)。
诚实边界: 合成控制是观测性估计——donor 池若同受干预波及(外溢/同业同时改版),
效应被吸收进反事实;server-side A/B 仍是唯一真因果检验(did_attribution 同注)。

用法:
  python3 synthetic_control.py --treated treated.csv --donors d1.csv,d2.csv,d3.csv \
      --intervention 2026-08-01 [--rounds 10] [--json]
  python3 synthetic_control.py --self-test
退出码: 0=出结果(含 inconclusive);1=无可分析数据(日期交集/pre 点不足到 null);
        2=闸门/文件/参数错误。"""
import argparse
import csv
import json
import math
import sys
import traceback
from datetime import date

Z = 1.96
MIN_PRE_POINTS = 6        # pre 期最少日期点(坐标下降至少要有东西可拟合)
MIN_DONORS = 2            # 2 个 donor 才谈"合成"(1 个=直接对照,允许但降级标注)
WEAK_PLACEBO_DONORS = 5   # donor<5 → 安慰剂分布粗,只当方向
DEFAULT_ROUNDS = 10       # 坐标下降轮数(规格: 简化 simplex 10 轮)


def die(msg, code=2):
    print("[error] %s" % msg, file=sys.stderr)
    sys.exit(code)


# ---------- 数据载入 ----------

def load_series_csv(path):
    """Date,Metric CSV → {date: float}(同日累加,按 Metric 数值解析)。"""
    try:
        f = open(path, encoding="utf-8-sig", newline="")
    except OSError as e:
        die("无法读取 %s: %s" % (path, e))
    with f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames:
            die("%s: 空 CSV" % path)
        cols = {(c or "").strip().lower(): c for c in rdr.fieldnames if c}
        date_k = next((cols[k] for k in ("date", "day", "日期") if k in cols), None)
        metric_k = next((cols[k] for k in ("metric", "clicks", "value", "sessions",
                                          "数值") if k in cols), None)
        if not date_k or not metric_k:
            die("%s: 需要 Date 和 Metric 列,实际列=%s" % (path, list(rdr.fieldnames)))
        out = {}
        for row in rdr:
            ds = (row.get(date_k) or "").strip()[:10]
            if not ds:
                continue
            try:
                d = date.fromisoformat(ds)
            except ValueError:
                die("%s: Date 无法解析: %r(需 YYYY-MM-DD)" % (path, ds))
            raw = (row.get(metric_k) or "0").replace(",", "")
            try:
                v = float(raw)
            except ValueError:
                die("%s: Metric 无法解析为数值: %r" % (path, row.get(metric_k)))
            out[d] = out.get(d, 0.0) + v
        if not out:
            die("%s: 没有有效数据行" % path)
        return out


def align_series(treated, donors):
    """treated + 全部 donor 的日期交集(升序);报告被丢弃的日期数。"""
    common = set(treated)
    for d in donors:
        common &= set(d)
    dropped = (len(set(treated)) - len(common)) + sum(
        len(set(d) - common) for d in donors)
    return sorted(common), dropped


# ---------- 简化 simplex 求解(坐标下降,10 轮) ----------

def synth_at(donors, weights, t_idx):
    return sum(w * donors[i][t_idx] for i, w in enumerate(weights))


def solve_weights(y_pre, donors_pre, rounds=DEFAULT_ROUNDS):
    """坐标下降求 simplex 权重(非负、和=1),最小化 pre 期 RMSE。
    简化求解——非 CausalImpact BSTS(见模块 docstring)。确定性: 同输入同输出。"""
    k = len(donors_pre)
    n = len(y_pre)
    w = [1.0 / k] * k
    for _ in range(rounds):
        for i in range(k):
            for j in range(i + 1, k):
                c = w[i] + w[j]                     # 对内和守恒 → 总和恒 1
                diff = [donors_pre[i][t] - donors_pre[j][t] for t in range(n)]
                denom = sum(x * x for x in diff)
                if denom <= 1e-12:                  # 两 donor pre 完全同形 → 无方向可优化
                    continue
                num = 0.0
                for t in range(n):
                    other = sum(w[l] * donors_pre[l][t]
                                for l in range(k) if l not in (i, j))
                    r_t = y_pre[t] - other - c * donors_pre[j][t]
                    num += diff[t] * r_t
                wi = num / denom
                wi = min(max(wi, 0.0), c)           # clamp 回 [0, c]
                w[i], w[j] = wi, c - wi
    total = sum(w)
    return [x / total for x in w] if total > 0 else w  # 数值漂移兜底归一


def rmse(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a)) if a else 0.0


# ---------- 分析 ----------

def run_scm(treated_map, donor_maps, intervention, rounds=DEFAULT_ROUNDS):
    """单次合成控制: {date: value} 序列 → 结果 dict(不打印)。"""
    dates, dropped = align_series(treated_map, donor_maps)
    pre = [d for d in dates if d < intervention]
    post = [d for d in dates if d >= intervention]
    y_pre = [treated_map[d] for d in pre]
    y_post = [treated_map[d] for d in post]
    donors_pre = [[m[d] for d in pre] for m in donor_maps]
    weights = solve_weights(y_pre, donors_pre, rounds=rounds)
    synth_pre = [synth_at(donors_pre, weights, t) for t in range(len(pre))]
    synth_post = [synth_at([[m[d] for d in post] for m in donor_maps], weights, t)
                  for t in range(len(post))]
    gaps = [a - b for a, b in zip(y_post, synth_post)]
    # 数值尘埃守卫: |gap| 相对序列尺度 <1e-9 视为 0——否则零噪声合成数据会被
    # 描述性 CI(se≈1e-10)误判 likely_negative
    scale = max([abs(v) for v in y_pre + y_post] + [1.0])
    gaps = [(0.0 if abs(g) < 1e-9 * scale else g) for g in gaps]
    mean_gap = sum(gaps) / len(gaps) if gaps else 0.0
    var = sum((g - mean_gap) ** 2 for g in gaps) / (len(gaps) - 1) if len(gaps) > 1 else 0.0
    se = math.sqrt(var / len(gaps)) if gaps else None    # 描述性 SE,未做自相关校正
    pre_rmse = rmse(y_pre, synth_pre)
    pre_mean = sum(y_pre) / len(y_pre) if y_pre else 0.0
    post_mean = sum(y_post) / len(y_post) if y_post else 0.0
    lo = hi = None
    verdict = "no_post_data"
    if se is not None:
        lo, hi = mean_gap - Z * se, mean_gap + Z * se
        verdict = ("likely_positive" if lo > 0 else
                   "likely_negative" if hi < 0 else "inconclusive")
    synth_post_mean = sum(synth_post) / len(synth_post) if synth_post else 0.0
    return {"dates": dates, "pre_dates": [d.isoformat() for d in pre],
            "post_dates": [d.isoformat() for d in post], "dropped_dates": dropped,
            "rounds": rounds,
            "weights": weights, "pre_rmse": pre_rmse,
            "pre_rmse_pct": (pre_rmse / pre_mean * 100) if pre_mean else None,
            "y_pre": y_pre, "synth_pre": synth_pre, "y_post": y_post,
            "synth_post": synth_post, "gaps": gaps,
            "mean_gap": mean_gap, "total_gap": sum(gaps),
            "rel_lift_pct": (mean_gap / synth_post_mean * 100) if synth_post_mean else None,
            "se": se, "ci_low": lo, "ci_high": hi, "verdict": verdict,
            "post_mean": post_mean, "pre_mean": pre_mean}


def analyze(treated_map, donor_maps, intervention, rounds=DEFAULT_ROUNDS):
    """主分析 + in-space placebo(每个 donor 当假处理组,真处理组不入池)。"""
    res = run_scm(treated_map, donor_maps, intervention, rounds=rounds)
    true_gap = res["mean_gap"]
    placebos = []
    for i, pseudo in enumerate(donor_maps):
        pool = [m for j, m in enumerate(donor_maps) if j != i]
        if not pool:                            # 单 donor → 假处理组无池可合成
            placebos.append({"donor_index": i, "mean_gap": None,
                             "pre_rmse": None,
                             "note": "安慰剂池为空(单 donor)"})
            continue
        pres = run_scm(pseudo, pool, intervention, rounds=rounds)
        placebos.append({"donor_index": i, "mean_gap": pres["mean_gap"],
                         "pre_rmse": pres["pre_rmse"]})
    valid = [pl for pl in placebos if pl["mean_gap"] is not None]
    n_pl = len(valid)
    if n_pl:
        if true_gap >= 0:
            p_val = sum(1 for pl in valid if pl["mean_gap"] >= true_gap) / n_pl
        else:
            p_val = sum(1 for pl in valid if pl["mean_gap"] <= true_gap) / n_pl
        p_abs = sum(1 for pl in valid
                    if abs(pl["mean_gap"]) >= abs(true_gap)) / n_pl
    else:
        p_val = p_abs = None
    res["placebo"] = {"placebos": placebos, "n": n_pl, "n_donors": len(donor_maps),
                      "p_value": p_val, "p_abs": p_abs,
                      "weak": n_pl < WEAK_PLACEBO_DONORS}
    return res


# ---------- 渲染 ----------

_SPARK = "▁▂▃▄▅▆▇█"


def sparkline(vals):
    """gap 序列 → 8 档块字符(只作肉眼曲线,不作数值依据)。"""
    if not vals:
        return ""
    m = max(abs(v) for v in vals) or 1.0
    return "".join(_SPARK[min(len(_SPARK) - 1,
                              int(abs(v) / m * (len(_SPARK) - 0.001)))] for v in vals)


def render(res, treated_path, donor_paths, intervention):
    W = 68
    L = ["=" * W, "合成控制(synthetic control,DiD 升级——干预时点分析)".center(W),
         "=" * W]
    L.append("干预日       : %s(pre %d 点 / post %d 点 / 对齐丢弃 %d 日期点)"
             % (intervention, len(res["y_pre"]), len(res["y_post"]), res["dropped_dates"]))
    L.append("treated      : %s" % treated_path)
    for i, p in enumerate(donor_paths):
        L.append("donor %-2d     : %s(w=%.4f)" % (i + 1, p, res["weights"][i]))
    L.append("求解         : 简化 simplex 坐标下降 %d 轮(非 CausalImpact BSTS;"
             "不建模趋势/季节/自相关)" % res["rounds"])
    L.append("-" * W)
    L.append("[pre 拟合优度] RMSE = %.4f(= treated pre 均值的 %s)"
             % (res["pre_rmse"], "%.1f%%" % res["pre_rmse_pct"]
                if res["pre_rmse_pct"] is not None else "N/A"))
    if res["pre_rmse_pct"] is not None and res["pre_rmse_pct"] > 20:
        L.append("  [!] pre RMSE>20%% 均值: 合成组没跟上 pre 轨迹,post 差不可当效应读")
    L.append("[post 因果效应估计] 处理组 − 合成组")
    L.append("  均值 gap = %+.4f / 日(累计 %+.1f,相对反事实 post 均值 %s)"
             % (res["mean_gap"], res["total_gap"],
                "%+.1f%%" % res["rel_lift_pct"] if res["rel_lift_pct"] is not None else "N/A"))
    if res["se"] is not None:
        L.append("  描述性 95%% CI = [%+.4f, %+.4f](SE=√var/n,未做自相关校正)"
                 % (res["ci_low"], res["ci_high"]))
    L.append("  判定       : %s" % res["verdict"].upper())
    pl = res["placebo"]
    L.append("[placebo 检验] 每个 donor 当假处理组跑同法(有效 %d/%d,真处理组不入池)"
             % (pl["n"], pl["n_donors"]))
    for p in pl["placebos"]:
        if p["mean_gap"] is None:
            L.append("  donor %-2d %s" % (p["donor_index"] + 1, p.get("note", "无效安慰剂")))
        else:
            L.append("  donor %-2d 假效应 = %+.4f(pre RMSE %.4f)"
                     % (p["donor_index"] + 1, p["mean_gap"], p["pre_rmse"]))
    if pl["p_value"] is not None:
        L.append("  p 值 = 假效应≥真效应比例 = %.3f(|假|≥|真| 双侧口径 p_abs=%.3f)"
                 % (pl["p_value"], pl["p_abs"]))
    else:
        L.append("  p 值 = N/A(无有效安慰剂)")
    if pl["weak"] and pl["n"]:
        L.append("  [!] 有效安慰剂 %d<%d: 分布分辨率粗,p 只当方向参考"
                 % (pl["n"], WEAK_PLACEBO_DONORS))
    L.append("-" * W)
    L.append("[效应曲线 post 期] 日期 | treated | synthetic | gap | 累计")
    cum = 0.0
    for ds, yt, st, g in zip(res["post_dates"], res["y_post"], res["synth_post"],
                             res["gaps"]):
        cum += g
        L.append("  %s | %10.2f | %9.2f | %+8.2f | %+10.2f"
                 % (ds, yt, st, g, cum))
    L.append("  gap 曲线(块字符,|值| 归一): %s" % sparkline(res["gaps"]))
    L.append("-" * W)
    L.append("诚实边界: 观测性估计——donor 池若同受干预波及(外溢/同业同时改版),")
    L.append("  效应被吸收进反事实;server-side A/B 仍是唯一真因果检验。")
    L.append("=" * W)
    return "\n".join(L)


def to_json_payload(res, treated_path, donor_paths, intervention):
    return {"tool": "synthetic_control", "intervention": intervention.isoformat(),
            "treated": treated_path, "donors": donor_paths,
            "solver": "coordinate-descent-simplex-r%d(简化求解,非 CausalImpact BSTS)"
                      % res["rounds"],
            "weights": [round(w, 6) for w in res["weights"]],
            "pre_fit": {"rmse": round(res["pre_rmse"], 6),
                        "rmse_pct_of_pre_mean": (round(res["pre_rmse_pct"], 4)
                                                 if res["pre_rmse_pct"] is not None
                                                 else None),
                        "n_pre_points": len(res["y_pre"]),
                        "dropped_dates": res["dropped_dates"]},
            "effect": {"n_post_points": len(res["y_post"]),
                       "mean_gap": round(res["mean_gap"], 6),
                       "total_gap": round(res["total_gap"], 4),
                       "rel_lift_pct": (round(res["rel_lift_pct"], 4)
                                        if res["rel_lift_pct"] is not None else None),
                       "se": (round(res["se"], 6) if res["se"] is not None else None),
                       "ci_low": (round(res["ci_low"], 6)
                                  if res["ci_low"] is not None else None),
                       "ci_high": (round(res["ci_high"], 6)
                                   if res["ci_high"] is not None else None),
                       "verdict": res["verdict"]},
            "effect_curve": [{"date": ds, "treated": round(yt, 4),
                              "synthetic": round(st, 4), "gap": round(g, 4)}
                             for ds, yt, st, g in zip(res["post_dates"], res["y_post"],
                                                      res["synth_post"], res["gaps"])],
            "placebo": {"n": res["placebo"]["n"],
                        "p_value": (round(res["placebo"]["p_value"], 4)
                                    if res["placebo"]["p_value"] is not None else None),
                        "p_abs": (round(res["placebo"]["p_abs"], 4)
                                  if res["placebo"]["p_abs"] is not None else None),
                        "weak": res["placebo"]["weak"],
                        "placebos": [{"donor_index": p["donor_index"],
                                      "mean_gap": (round(p["mean_gap"], 6)
                                                   if p["mean_gap"] is not None else None),
                                      "pre_rmse": (round(p["pre_rmse"], 6)
                                                   if p["pre_rmse"] is not None else None),
                                      **({"note": p["note"]}
                                         if p.get("note") else {})}
                                     for p in res["placebo"]["placebos"]]},
            "caveat": "观测性估计;donor 池同受干预波及时效应被吸收;非 BSTS"}


# ---------- 自测 ----------

def _mk_series(base_fn, days, lift_fn=None):
    """合成序列 helper: date → value(lift_fn 只作用于干预后)。"""
    from datetime import timedelta
    d0 = date(2026, 7, 1)
    out = {}
    for i in range(days):
        d = d0 + timedelta(days=i)
        v = base_fn(i)
        if lift_fn and i >= days // 2:
            v += lift_fn(i)
        out[d] = v
    return out


def _self_test():
    # 已知干预效应回收: treated = 0.5d1+0.3d2+0.2d3(donor 形状互异,非共线),
    # post 期加性 +20/日 → 均值 gap 精确回收,rel_lift = 20/base_post_mean
    from datetime import timedelta
    d0 = date(2026, 7, 1)
    n = 30
    iv = d0 + timedelta(days=20)
    s1 = lambda i: 100 + 2 * i                    # 趋势
    s2 = lambda i: 80 + 15 * math.sin(2 * math.pi * i / 7)   # 周周期
    s3 = lambda i: 60 + (i - 15) ** 2 * 0.3       # U 形
    mk = lambda f: {d0 + timedelta(days=i): f(i) for i in range(n)}
    d1, d2, d3 = mk(s1), mk(s2), mk(s3)
    base = {d: 0.5 * d1[d] + 0.3 * d2[d] + 0.2 * d3[d] for d in d1}
    treated = {d: (v + 20 if d >= iv else v) for d, v in base.items()}
    res = analyze(treated, [d1, d2, d3], iv)
    assert all(abs(w - t) < 1e-3 for w, t in zip(res["weights"], [0.5, 0.3, 0.2])), res["weights"]
    assert res["pre_rmse"] < 1e-4, res["pre_rmse"]
    assert abs(res["mean_gap"] - 20.0) < 1e-6, res["mean_gap"]
    exp_rel = 20.0 / (sum(base[d] for d in base if d >= iv) / 10) * 100
    assert abs(res["rel_lift_pct"] - exp_rel) < 1e-6, (res["rel_lift_pct"], exp_rel)
    assert res["verdict"] == "likely_positive"
    assert res["placebo"]["p_value"] is not None and res["placebo"]["p_value"] <= 1 / 3
    # null 世界: treated=合成本体,零噪声 → gap≈0 / inconclusive / p 不小于真效应案例
    rn = analyze(base, [d1, d2, d3], iv)
    assert abs(rn["mean_gap"]) < 1e-6 and rn["verdict"] == "inconclusive"
    assert rn["placebo"]["p_value"] >= 1 / 3
    # 单 donor: 允许,安慰剂池为空 → p=N/A
    r1 = analyze(treated, [d1], iv)
    assert len(r1["weights"]) == 1 and r1["placebo"]["n"] == 0
    assert r1["placebo"]["p_value"] is None
    # sparkline 确定性
    assert sparkline([1, -2, 3]) == sparkline([1, -2, 3]) and sparkline([]) == ""
    print("[self-test] PASS synthetic_control(权重回收 0.5/0.3/0.2,pre RMSE≈0,"
          "+20/日效应回收,placebo p,null 世界 inconclusive,单 donor 降级)")


# ---------- CLI ----------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="合成控制法(synthetic control)——DiD 升级,干预时点分析"
                    "(donor pool 加权合成反事实 + placebo 检验;stdlib)")
    ap.add_argument("--treated", default="", help="处理组 CSV(Date,Metric)")
    ap.add_argument("--donors", default="",
                    help="donor pool CSV,逗号分隔(如 d1.csv,d2.csv)")
    ap.add_argument("--intervention", default="", help="干预日 YYYY-MM-DD")
    ap.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS,
                    help="坐标下降轮数(默认 %d)" % DEFAULT_ROUNDS)
    ap.add_argument("--json", action="store_true", help="输出 JSON(默认 markdown)")
    ap.add_argument("--self-test", action="store_true", help="冒烟自测(不联网)")
    args = ap.parse_args(argv)
    if args.self_test:
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL synthetic_control")
            return 1
    missing = [k for k, v in (("--treated", args.treated), ("--donors", args.donors),
                              ("--intervention", args.intervention)) if not v]
    if missing:
        die("缺少必选参数: %s" % ", ".join(missing))
    try:
        iv = date.fromisoformat(args.intervention)
    except ValueError:
        die("--intervention 需要 YYYY-MM-DD,得到 %r" % args.intervention)
    treated_map = load_series_csv(args.treated)
    donor_paths = [p.strip() for p in args.donors.split(",") if p.strip()]
    if not donor_paths:
        die("--donors 至少需要一个 CSV")
    donor_maps = [load_series_csv(p) for p in donor_paths]
    dates, dropped = align_series(treated_map, donor_maps)
    if not dates:
        die("treated 与 donors 无公共日期", 1)
    pre_n = sum(1 for d in dates if d < iv)
    post_n = len(dates) - pre_n
    if pre_n == 0 or post_n == 0:
        die("干预日 %s 之外无数据: pre=%d 点 post=%d 点(需两侧都有数据)"
            % (iv, pre_n, post_n))
    if pre_n < MIN_PRE_POINTS:
        die("闸门未过: pre 期 %d 点<%d,不足以拟合权重" % (pre_n, MIN_PRE_POINTS))
    if len(donor_maps) < MIN_DONORS:
        print("[i] donor 数 %d<%d: 无合成可言,退化为单对照;placebo 仅 1 个"
              % (len(donor_maps), MIN_DONORS), file=sys.stderr)
    res = analyze(treated_map, donor_maps, iv, rounds=args.rounds)
    if args.json:
        print(json.dumps(to_json_payload(res, args.treated, donor_paths, iv),
                         ensure_ascii=False, indent=2))
    else:
        print(render(res, args.treated, donor_paths, iv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
