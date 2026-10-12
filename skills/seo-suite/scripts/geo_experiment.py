#!/usr/bin/env python3
"""geo_experiment.py——分国别(geo)增量实验,Meridian GeoX 思路薄封装。stdlib-only。
规格: references/overview/pipeline-completeness.md R6 归因实验。

Meridian GeoX(Google Meridian 市场组合模型的 geo-experiment 思路)的极薄版本:
  * assign: 把国家分进 treated/control 两组(显式点名或按干预前流量自动对半),
    并做平衡性检查——干预前两组日均 Clicks 的 Welch t 检验,p>0.1 才 PASS
    (分不动就别硬分,FAIL 时先换分组再谈 DiD);
  * analyze: 双重差分 DiD——组×期交互项,手写 OLS 2×2
    (y = β0 + β1·treated + β2·post + β3·treated×post,观测=Country×Date 行;
    正规方程 4×4 高斯消元手解,SE 用 (X'X)⁻¹ 对角线 × 残差方差,不做聚类稳健),
    另给分国别异质性(每国 post−pre 日均差,再减对照组同差做对照调整)。

诚实边界(必须随结果输出,引 references/monitoring/kpi-definitions.md):
  * SEO 无法做索引级 holdout——Google 不允许"一半索引暂停收录/可见性",
    索引与排名是全市场共享的;geo 实验只能测**分国别可暂停的活动**
    (某国的内容发布节奏/可下线的分国别落地页/分国别的 crawl 预算或投放),
    且要求该活动在处理国可整体暂停、不影响他国(无外溢);
  * kpi-definitions 口径: geo holdout 是 Incrementality 范式
    ("两个渠道争同一转化时的终审");AI 引荐流量经 branded search/direct 进入,
    referrer 日志只见下界——geo DiD 测的是该国总增量,不区分渠道。

输入 --geo-matrix CSV: Country,Clicks,Date[,group](列名大小写不敏感;
Country/country/geo/market,Clicks/clicks/metric,Date/date/day,group/arm/
treatment 均认;group 值 treated/control(或 treatment/control、1/0))。
同 Country×Date 多行按 Clicks 累加。

用法:
  python3 geo_experiment.py assign --geo-matrix geo.csv --intervention 2026-08-01 \
      [--treated-geo US,DE] [--out assigned.csv] [--json]
      # 无 --treated-geo: 按干预前总 Clicks 降序 snake 对半(0→T,1→C,2→C,3→T…)
  python3 geo_experiment.py analyze --geo-matrix assigned.csv --intervention 2026-08-01 [--json]
  python3 geo_experiment.py --self-test
退出码: 0=正常出结果;1=平衡性 FAIL 仍出结果(assign 时提示先换分组);
        2=闸门/文件/参数错误(analyze 无 group 列等)。"""
import argparse
import csv
import json
import math
import sys
import traceback
from datetime import date

BALANCE_ALPHA = 0.1     # 平衡性闸门: pre 期 Welch t 检验 p>0.1 才 PASS
MIN_PRE_DAYS = 7        # 干预前至少 7 个日期点(平衡性检验的最低样本)
Z95 = 0.975             # t 分双侧 95% 分位(数值法求)


def die(msg, code=2):
    print("[error] %s" % msg, file=sys.stderr)
    sys.exit(code)


# ---------- t 分布(stdlib 手写: 不完全 beta 函数连分式) ----------

def _betacf(a, b, x, itmax=300, eps=3e-12):
    """正则化不完全 beta 函数的连分式(Numerical Recipes betacf)。"""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _betai(a, b, x):
    """正则化不完全 beta I_x(a,b)。"""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_bt = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
             + a * math.log(x) + b * math.log(1.0 - x))
    bt = math.exp(ln_bt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_two_sided_p(t, df):
    """t 统计量双侧 p 值 = I_{df/(df+t²)}(df/2, 1/2);df<=0 → None。"""
    if df <= 0:
        return None
    if t == 0:
        return 1.0
    return _betai(df / 2.0, 0.5, df / (df + t * t))


def t_critical_975(df):
    """t_{0.975,df}(双侧 95% 临界): 双侧 p(t)=0.05 的根,单调二分求。"""
    if df <= 0:
        return None
    lo, hi = 0.0, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_two_sided_p(mid, df) > 0.05:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def welch_ttest(a, b):
    """Welch 两样本 t 检验(不等方差)→ (t, df, p_two_sided);任一侧空/零方差 → None。"""
    if len(a) < 2 or len(b) < 2:
        return None
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    sea, seb = va / len(a), vb / len(b)
    se2 = sea + seb
    if se2 <= 0:
        return None                        # 两组都常数且同值 → 无差异可检
    t = (ma - mb) / math.sqrt(se2)
    df = se2 * se2 / (sea * sea / (len(a) - 1) + seb * seb / (len(b) - 1)) \
        if (sea > 0 or seb > 0) else None
    p = t_two_sided_p(abs(t), df) if df else None
    return t, df, p


# ---------- 数据载入 ----------

def load_geo_matrix(path):
    """geo CSV → [{country, clicks, date, group}]。group 列可缺(assign 用)。"""
    try:
        f = open(path, encoding="utf-8-sig", newline="")
    except OSError as e:
        die("无法读取 %s: %s" % (path, e))
    with f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames:
            die("%s: 空 CSV" % path)
        cols = {(c or "").strip().lower(): c for c in rdr.fieldnames if c}
        c_k = next((cols[k] for k in ("country", "geo", "market", "国家") if k in cols), None)
        k_k = next((cols[k] for k in ("clicks", "metric", "value", "sessions") if k in cols), None)
        d_k = next((cols[k] for k in ("date", "day", "日期") if k in cols), None)
        g_k = next((cols[k] for k in ("group", "arm", "treatment", "分组") if k in cols), None)
        if not c_k or not k_k or not d_k:
            die("%s: 需要 Country,Clicks,Date 列,实际列=%s" % (path, list(rdr.fieldnames)))
        rows = []
        for row in rdr:
            country = (row.get(c_k) or "").strip()
            if not country:
                continue
            try:
                d = date.fromisoformat((row.get(d_k) or "").strip()[:10])
            except ValueError:
                die("%s: Date 无法解析: %r" % (path, row.get(d_k)))
            raw = (row.get(k_k) or "0").replace(",", "")
            try:
                v = float(raw)
            except ValueError:
                die("%s: Clicks 无法解析为数值: %r" % (path, row.get(k_k)))
            grp = ""
            if g_k:
                grp = normalize_group(row.get(g_k))
                if grp is None:
                    die("%s: group 值无法识别(treated/control 或 1/0): %r"
                        % (path, row.get(g_k)))
            rows.append({"country": country, "clicks": v, "date": d, "group": grp})
        if not rows:
            die("%s: 没有有效数据行" % path)
        return rows


def normalize_group(v):
    """group 值归一 → treated/control;无法识别 → None。"""
    s = (v or "").strip().lower()
    if s in ("treated", "treatment", "treat", "1", "test"):
        return "treated"
    if s in ("control", "holdout", "c", "0"):
        return "control"
    if s in ("", "-"):
        return ""
    return None


# ---------- 聚合 ----------

def pre_rows(rows, intervention):
    return [r for r in rows if r["date"] < intervention]


def post_rows(rows, intervention):
    return [r for r in rows if r["date"] >= intervention]


def country_daily(rows):
    """{country: {date: clicks}}(同日累加)。"""
    out = {}
    for r in rows:
        out.setdefault(r["country"], {})
        out[r["country"]][r["date"]] = out[r["country"]].get(r["date"], 0.0) + r["clicks"]
    return out


def group_daily_series(rows, group, dates):
    """某组逐日总 Clicks(按给定日期序,缺日补 0)。"""
    agg = {d: 0.0 for d in dates}
    for r in rows:
        if r["group"] == group:
            agg[r["date"]] = agg.get(r["date"], 0.0) + r["clicks"]
    return [agg.get(d, 0.0) for d in dates]


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


# ---------- assign ----------

def auto_split(countries, pre_totals):
    """按干预前总 Clicks 降序 snake 对半: 序位 0→T,1→C,2→C,3→T,4→T,5→C,6→C,7→T…
    (snake draft: 每轮两头交替挑,大流量国家交错分摊,两组规模差 ≤1)。
    返回 {country: group}。"""
    order = sorted(countries, key=lambda c: (-pre_totals.get(c, 0.0), c))
    out = {}
    for idx, c in enumerate(order):
        out[c] = "treated" if idx % 4 in (0, 3) else "control"
    return out


def compute_balance(rows, intervention):
    """既有分组上的平衡性检查(不重新分组,不改 rows)。"""
    pre = pre_rows(rows, intervention)
    dates = sorted({r["date"] for r in pre})
    t_ser = group_daily_series(pre, "treated", dates)
    c_ser = group_daily_series(pre, "control", dates)
    countries = sorted({r["country"] for r in rows})
    groups = {r["country"]: r["group"] for r in rows}
    wt = welch_ttest(t_ser, c_ser)
    n_t = sum(1 for c in countries if groups.get(c) == "treated")
    n_c = sum(1 for c in countries if groups.get(c) == "control")
    balance = {"test": "welch-t(daily clicks pre)", "n_treated_geos": n_t,
               "n_control_geos": n_c,
               "treated_pre_daily_mean": mean(t_ser),
               "control_pre_daily_mean": mean(c_ser)}
    if wt is None:
        balance.update(t=None, df=None, p=None, status="UNTESTABLE",
                       note="pre 期天数或方差不足,或两组 pre 序列零方差,"
                            "平衡性无法检验")
    else:
        t, df, p = wt
        balance.update(t=round(t, 4), df=round(df, 2),
                       p=round(p, 4),
                       status="PASS" if p > BALANCE_ALPHA else "FAIL")
    return balance


def assign_groups(rows, intervention, treated_geo=None):
    """分组(会写回 rows 的 group 字段)+ 平衡性检查 → 结果 dict。"""
    pre = pre_rows(rows, intervention)
    dates = sorted({r["date"] for r in pre})
    cd = country_daily(pre)
    pre_totals = {c: sum(m.values()) for c, m in cd.items()}
    countries = sorted(cd)
    if treated_geo:
        wanted = [g.strip() for g in treated_geo.split(",") if g.strip()]
        unknown = [g for g in wanted if g not in countries]
        if unknown:
            die("--treated-geo 含矩阵中不存在的国家: %s(可用: %s)"
                % (",".join(unknown), ",".join(countries)))
        groups = {c: ("treated" if c in wanted else "control") for c in countries}
        method = "explicit(--treated-geo %s)" % ",".join(wanted)
    else:
        groups = auto_split(countries, pre_totals)
        method = "auto-snake(按干预前总 Clicks 降序对半)"
    for r in rows:
        r["group"] = groups[r["country"]]
    balance = compute_balance(rows, intervention)
    per_country = [{"country": c, "group": groups[c],
                    "pre_daily_mean": mean(cd[c].values()),
                    "pre_total": pre_totals[c]}
                   for c in sorted(countries, key=lambda c: (-pre_totals[c], c))]
    return {"intervention": intervention, "method": method,
            "pre_days": len(dates), "groups": groups,
            "per_country": per_country, "balance": balance}


def render_assign(asg):
    W = 68
    L = ["=" * W, "geo 实验分组(Meridian GeoX 思路薄封装)".center(W), "=" * W]
    L.append("干预日     : %s(pre %d 天)" % (asg["intervention"], asg["pre_days"]))
    L.append("分组方法   : %s" % asg["method"])
    L.append("-- 分组表(按干预前日均排序) --")
    L.append("  %-10s %-9s %12s %12s" % ("Country", "group", "pre 日均", "pre 总量"))
    for row in asg["per_country"]:
        L.append("  %-10s %-9s %12.2f %12.1f"
                 % (row["country"], row["group"], row["pre_daily_mean"], row["pre_total"]))
    b = asg["balance"]
    L.append("-- 平衡性检查(干预前各组日均差 Welch t 检验;p>%.1f 才 PASS) --"
             % BALANCE_ALPHA)
    L.append("  treated(%d 国) 日均 %.2f vs control(%d 国) 日均 %.2f"
             % (b["n_treated_geos"], b["treated_pre_daily_mean"],
                b["n_control_geos"], b["control_pre_daily_mean"]))
    if b["p"] is not None:
        L.append("  Welch t = %+.4f, df = %.2f, p = %.4f → %s"
                 % (b["t"], b["df"], b["p"], b["status"]))
    else:
        L.append("  %s(%s)" % (b["status"], b["note"]))
    if b["status"] == "FAIL":
        L.append("  [!] 平衡性 FAIL: 两组干预前基线不同,DiD 的平行趋势起点不齐,")
        L.append("      先换分组(挑流量相近的国家对)再谈因果")
    if asg["pre_days"] < MIN_PRE_DAYS:
        L.append("  [!] pre 仅 %d 天<%d: 平衡性检验功效不足" % (asg["pre_days"], MIN_PRE_DAYS))
    L.append("-" * W)
    L.append(HONESTY_FOOTER)
    L.append("=" * W)
    return "\n".join(L)


HONESTY_FOOTER = ("诚实边界: SEO 无法做索引级 holdout——索引/排名是全市场共享的,"
                  "不允许“一半索引暂停收录”;geo 实验只能测分国别可暂停的活动"
                  "(分国别的内容发布/落地页/crawl 预算,且须无外溢);"
                  "参照 references/monitoring/kpi-definitions.md"
                  "(geo holdout=Incrementality 终审;AI 引荐经 branded search/direct 进入,"
                  "referrer 只见下界,geo DiD 测该国总增量不区分渠道)。")


# ---------- analyze: 手写 OLS 2×2 ----------

def solve_linear(a, b):
    """解 a·x=b(高斯消元+列主元;a 为 n×n list of list);奇异 → None。"""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            return None
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for r in range(n):
            if r != col and m[r][col] != 0:
                f = m[r][col] / pv
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    return [m[i][n] / m[i][i] for i in range(n)]


def invert_matrix(a):
    """Gauss-Jordan 求逆(增广单位阵);奇异 → None。"""
    n = len(a)
    m = [row[:] + [1.0 if i == j else 0.0 for j in range(n)]
         for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            return None
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        m[col] = [x / pv for x in m[col]]
        for r in range(n):
            if r != col and m[r][col] != 0:
                f = m[r][col]
                m[r] = [x - f * y for x, y in zip(m[r], m[col])]
    return [row[n:] for row in m]


def did_ols(rows, intervention):
    """DiD 2×2: y = β0+β1·treated+β2·post+β3·treated×post(观测=Country×Date)。
    手写正规方程:X'X·β=X'y(高斯消元),Var(β3)=σ²·(X'X)⁻¹[3][3],
    σ²=RSS/(n−4);不做聚类稳健 SE(国家数<10 时 SE 偏乐观,已注明)。"""
    X, y = [], []
    for r in rows:
        if not r["group"]:
            continue
        t = 1.0 if r["group"] == "treated" else 0.0
        post = 1.0 if r["date"] >= intervention else 0.0
        X.append([1.0, t, post, t * post])
        y.append(r["clicks"])
    n = len(y)
    if n < 6:
        return None
    k = 4
    xtx = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
    beta = solve_linear(xtx, xty)
    if beta is None:
        return None
    rss = sum((y[i] - sum(beta[a] * X[i][a] for a in range(k))) ** 2 for i in range(n))
    df = n - k
    sigma2 = rss / df
    inv = invert_matrix(xtx)
    se3 = math.sqrt(sigma2 * inv[3][3]) if inv else None
    t3 = beta[3] / se3 if se3 and se3 > 0 else None
    p3 = t_two_sided_p(abs(t3), df) if t3 is not None else None
    crit = t_critical_975(df)
    return {"beta": beta, "n_obs": n, "df": df, "rss": rss,
            "se_beta3": se3, "t_beta3": (t3 if t3 is not None else None),
            "p_beta3": p3,
            "ci_low": (beta[3] - crit * se3) if (crit and se3) else None,
            "ci_high": (beta[3] + crit * se3) if (crit and se3) else None}


def naive_2x2(rows, intervention):
    """朴素 2×2 单元均值(**每国日均再组内平均**,与 OLS β3 同为每国口径):
    diff-in-diff of (post−pre)。平衡面板时与 OLS β3 一致;不平衡时两者口径不同
    (OLS 按 Country×Date 行加权,此处分国等权),并排展示。"""
    out = {}
    for grp in ("treated", "control"):
        grp_rows = [r for r in rows if r["group"] == grp]
        cd = country_daily(grp_rows)
        for period, pred in (("pre", lambda d: d < intervention),
                             ("post", lambda d: d >= intervention)):
            per_country = [mean([v for d, v in m.items() if pred(d)])
                           for m in cd.values()]
            out["%s_%s" % (grp, period)] = mean(per_country)
    out["did"] = (out["treated_post"] - out["treated_pre"]) \
        - (out["control_post"] - out["control_pre"])
    return out


def per_country_heterogeneity(rows, intervention):
    """分国别: 各国 post−pre 日均差,再减对照组同差(对照调整)。"""
    cd = country_daily(rows)
    ctrl_delta = None
    ctrl_rows = [r for r in rows if r["group"] == "control"]
    if ctrl_rows:
        n2 = naive_2x2(rows, intervention)
        ctrl_delta = n2["control_post"] - n2["control_pre"]
    out = []
    for c, m in cd.items():
        grp = next(r["group"] for r in rows if r["country"] == c)
        pre = [v for d, v in m.items() if d < intervention]
        post = [v for d, v in m.items() if d >= intervention]
        delta = mean(post) - mean(pre)
        out.append({"country": c, "group": grp,
                    "pre_daily_mean": mean(pre), "post_daily_mean": mean(post),
                    "delta": delta,
                    "adjusted_delta": (delta - ctrl_delta) if ctrl_delta is not None else None})
    out.sort(key=lambda x: -(x["adjusted_delta"] if x["adjusted_delta"] is not None
                             else x["delta"]))
    return out


def analyze_geo(rows, intervention):
    if any(not r["group"] for r in rows):
        die("矩阵存在未分组行: 先 assign(或补 group 列);缺 group 的国家: %s"
            % ",".join(sorted({r["country"] for r in rows if not r["group"]})[:5]))
    pre_dates = sorted({r["date"] for r in pre_rows(rows, intervention)})
    post_dates = sorted({r["date"] for r in post_rows(rows, intervention)})
    if not pre_dates or not post_dates:
        die("干预日 %s 两侧都需要数据(pre %d 天 / post %d 天)"
            % (intervention, len(pre_dates), len(post_dates)))
    ols = did_ols(rows, intervention)
    if ols is None:
        die("OLS 无法求解(观测不足或 X 奇异): n=%d" % len(rows))
    naive = naive_2x2(rows, intervention)
    hetero = per_country_heterogeneity(rows, intervention)
    balance = compute_balance(rows, intervention)    # 既有分组上的平衡性复检(不重分)
    sig = (ols["p_beta3"] is not None and ols["p_beta3"] < 0.05)
    verdict = ("significant" if sig else
               "directional" if ols["p_beta3"] is not None and ols["p_beta3"] < 0.2
               else "inconclusive")
    return {"intervention": intervention, "n_obs": ols["n_obs"], "df": ols["df"],
            "ols": {"beta_intercept": ols["beta"][0], "beta_treated": ols["beta"][1],
                    "beta_post": ols["beta"][2], "beta_interaction": ols["beta"][3],
                    "se_beta3": ols["se_beta3"], "t_beta3": ols["t_beta3"],
                    "p_beta3": ols["p_beta3"], "ci_low": ols["ci_low"],
                    "ci_high": ols["ci_high"]},
            "naive_2x2": naive, "balance": balance,
            "per_country": hetero, "verdict": verdict,
            "n_pre_days": len(pre_dates), "n_post_days": len(post_dates)}


def render_analyze(an):
    W = 68
    o, nv = an["ols"], an["naive_2x2"]
    L = ["=" * W, "geo DiD 分析(组×期交互项,手写 OLS 2×2)".center(W), "=" * W]
    L.append("干预日 %s | 观测 %d(Country×Date 行,df=%d)| pre %d 天 / post %d 天"
             % (an["intervention"], an["n_obs"], an["df"], an["n_pre_days"],
                an["n_post_days"]))
    b = an["balance"]
    if b["p"] is not None:
        L.append("平衡性复检: p=%.4f(%s)" % (b["p"], b["status"]))
        if b["status"] != "PASS":
            L.append("  [!] 基线不齐: 下述 DiD 的平行趋势假设起点已存疑")
    else:
        L.append("平衡性复检: %s" % b["status"])
    L.append("-- DiD 回归 y = β0 + β1·treated + β2·post + β3·treated×post --")
    L.append("  β0=%.4f  β1(treated)=%.4f  β2(post)=%.4f"
             % (o["beta_intercept"], o["beta_treated"], o["beta_post"]))
    L.append("  β3(交互项=DiD 估计)= %+.4f" % o["beta_interaction"])
    if o["se_beta3"]:
        L.append("  SE=%.4f  t=%+.3f  p=%.4f  95%%CI=[%+.4f, %+.4f]"
                 % (o["se_beta3"], o["t_beta3"], o["p_beta3"],
                    o["ci_low"], o["ci_high"]))
    L.append("  判定: %s(significant=p<0.05)" % an["verdict"].upper())
    L.append("  [i] SE 未做国家级聚类稳健: 国家数<10 时 p 偏乐观,只当方向+量级")
    L.append("-- 朴素 2×2(组级日均 diff-in-diff,平衡面板时应=β3)--")
    L.append("  treated pre %.2f → post %.2f(Δ%+.2f)"
             % (nv["treated_pre"], nv["treated_post"],
                nv["treated_post"] - nv["treated_pre"]))
    L.append("  control pre %.2f → post %.2f(Δ%+.2f)"
             % (nv["control_pre"], nv["control_post"],
                nv["control_post"] - nv["control_pre"]))
    L.append("  naive DiD = %+.4f(vs OLS β3 %+.4f)"
             % (nv["did"], o["beta_interaction"]))
    L.append("-- 分国别异质性(post−pre 日均差;adjusted=再减对照组同差)--")
    L.append("  %-10s %-9s %10s %10s %10s %11s"
             % ("Country", "group", "pre 日均", "post 日均", "Δ", "adjusted Δ"))
    for h in an["per_country"]:
        L.append("  %-10s %-9s %10.2f %10.2f %+10.2f %+11.2f"
                 % (h["country"], h["group"], h["pre_daily_mean"],
                    h["post_daily_mean"], h["delta"],
                    h["adjusted_delta"] if h["adjusted_delta"] is not None else float("nan")))
    L.append("-" * W)
    L.append(HONESTY_FOOTER)
    L.append("=" * W)
    return "\n".join(L)


# ---------- 自测 ----------

def _self_test():
    from datetime import timedelta
    d0 = date(2026, 7, 1)
    iv = d0 + timedelta(days=14)
    # 平行趋势合成面板(组级日总量平衡,日噪声非零): treated 国 post +30/日
    spec = (("US", 100.0, 3.0, 0.0, "treated"),    # 偶数日 +3
            ("JP", 80.0, -3.0, 0.0, "treated"),    # 偶数日 −3 → 组日总量 180+2i
            ("FR", 97.0, 0.0, 2.0, "control"),     # 奇数日 +2
            ("DE", 83.0, 0.0, 1.0, "control"))     # 奇数日 +1 → 组日总量 180+2i+3
    rows = []
    for c, base, even_n, odd_n, grp in spec:
        for i in range(22):          # post 窗 8 天=4 偶 4 奇,与 pre 同奇偶构成 → β3 精确
            d = d0 + timedelta(days=i)
            v = base + i * 2.0 + (even_n if i % 2 == 0 else odd_n)
            if grp == "treated" and d >= iv:
                v += 30.0
            rows.append({"country": c, "clicks": v, "date": d, "group": grp})
    an = analyze_geo(rows, iv)
    assert abs(an["ols"]["beta_interaction"] - 30.0) < 1e-6, an["ols"]
    assert abs(an["naive_2x2"]["did"] - 30.0) < 1e-6
    assert an["ols"]["p_beta3"] is not None and an["ols"]["p_beta3"] < 1e-6
    assert an["verdict"] == "significant"
    assert an["balance"]["status"] == "PASS", an["balance"]   # pre 组均值差≈0 → p>0.1
    # 分国别异质性: treated 国 adjusted Δ≈30,control 国 ≈0
    het = {h["country"]: h for h in an["per_country"]}
    assert abs(het["US"]["adjusted_delta"] - 30.0) < 1.0
    assert abs(het["JP"]["adjusted_delta"] - 30.0) < 1.0
    assert abs(het["FR"]["adjusted_delta"]) < 1.0
    assert abs(het["DE"]["adjusted_delta"]) < 1.0
    # t 分布抽查: t=0 → p=1;大 t → p≈0;df=1 的 97.5% 分位≈12.706
    assert t_two_sided_p(0.0, 10) == 1.0
    assert t_two_sided_p(30.0, 50) < 1e-20
    assert abs(t_critical_975(1) - 12.7062) < 1e-3
    assert abs(t_critical_975(10) - 2.2281) < 1e-3
    # Welch: 两样本同分布 → p 大;悬殊 → p 小
    w = welch_ttest([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    assert w is None or w[2] > 0.9                  # 零方差双侧 → None
    w2 = welch_ttest([10.0, 11, 12, 13, 14, 15], [1.0, 2, 3, 4, 5, 6])
    # 手算: 均值差 9,se=√(3.5/6+3.5/6)=1.0801 → t=8.3324;df=10(Welch)
    assert abs(w2[0] - 8.3324) < 1e-3 and abs(w2[1] - 10.0) < 1e-9 and w2[2] < 0.001
    # auto snake: 4 国对半,大流量交错
    g = auto_split(["A", "B", "C", "D"], {"A": 100, "B": 80, "C": 60, "D": 40})
    assert g == {"A": "treated", "B": "control", "C": "control", "D": "treated"}, g
    # OLS 线性解器/求逆: 对角系统手算对照
    assert solve_linear([[2, 0], [0, 4]], [4, 8]) == [2.0, 2.0]
    inv = invert_matrix([[4, 0], [0, 2]])
    assert inv[0][0] == 0.25 and inv[1][1] == 0.5
    print("[self-test] PASS geo_experiment(β3=30 精确回收,p<1e-6,平衡 PASS,"
          "分国别异质性,t 分位点/Welch/snake 对半/线性代数抽查)")


# ---------- CLI ----------

def build_parser():
    ap = argparse.ArgumentParser(
        description="geo_experiment——分国别增量实验(Meridian GeoX 思路薄封装):"
                    "assign 分组+平衡性检查,analyze DiD(手写 OLS 2×2)+分国别异质性;"
                    "stdlib-only")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("assign", "analyze"):
        p = sub.add_parser(name, help=("分组+平衡性检查" if name == "assign"
                                       else "DiD 分析+分国别异质性"))
        p.add_argument("--geo-matrix", default="",
                       help="geo CSV(Country,Clicks,Date[,group])")
        p.add_argument("--intervention", default="", help="干预日 YYYY-MM-DD")
        if name == "assign":
            p.add_argument("--treated-geo", default="",
                           help="处理组国家列表(逗号分隔,如 US,DE);缺省按干预前"
                                "流量自动对半(snake)")
            p.add_argument("--out", default="",
                           help="把 group 列写回的输出 CSV 路径(不覆盖输入文件)")
        p.add_argument("--json", action="store_true", help="输出 JSON(默认 markdown)")
    ap.add_argument("--self-test", action="store_true", help="冒烟自测(不联网)")
    return ap


def write_assigned_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Country", "Clicks", "Date", "group"])
        for r in rows:
            w.writerow([r["country"], r["clicks"], r["date"].isoformat(), r["group"]])


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.self_test:
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL geo_experiment")
            return 1
    if args.cmd not in ("assign", "analyze"):
        ap.print_help()
        return 2
    if not args.geo_matrix:
        die("需要 --geo-matrix geo.csv(Country,Clicks,Date[,group])")
    if not args.intervention:
        die("需要 --intervention YYYY-MM-DD")
    try:
        iv = date.fromisoformat(args.intervention)
    except ValueError:
        die("--intervention 需要 YYYY-MM-DD,得到 %r" % args.intervention)
    rows = load_geo_matrix(args.geo_matrix)
    if args.cmd == "assign":
        pre_n = len({r["date"] for r in pre_rows(rows, iv)})
        if not pre_n:
            die("干预日 %s 之前没有数据,无法做平衡性检查" % iv)
        if len({r["country"] for r in rows}) < 2:
            die("至少需要 2 个国家才能分组")
        asg = assign_groups(rows, iv, treated_geo=(getattr(args, "treated_geo", None) or None))
        if pre_n < MIN_PRE_DAYS:
            print("[i] pre 仅 %d 天<%d: 平衡性检验功效不足" % (pre_n, MIN_PRE_DAYS),
                  file=sys.stderr)
        if args.out:
            write_assigned_csv(args.out, rows)
            print("[i] 分组已写回: %s" % args.out, file=sys.stderr)
        if args.json:
            payload = dict(asg)
            payload["intervention"] = iv.isoformat()
            payload["groups"] = asg["groups"]
            payload["honesty"] = HONESTY_FOOTER
            print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        else:
            print(render_assign(asg))
        return 1 if asg["balance"]["status"] == "FAIL" else 0
    # analyze
    if any(not r["group"] for r in rows):
        die("analyze 需要矩阵带 group 列(先跑 assign --out,或手工补列)")
    an = analyze_geo(rows, iv)
    if args.json:
        payload = {k: v for k, v in an.items()}
        payload["intervention"] = iv.isoformat()
        payload["honesty"] = HONESTY_FOOTER
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        print(render_analyze(an))
    return 0


if __name__ == "__main__":
    sys.exit(main())
