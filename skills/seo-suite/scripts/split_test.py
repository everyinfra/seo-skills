#!/usr/bin/env python3
"""页面级增量实验(split test)+功效计算(stdlib 零网络,不引 scipy)。

规格:pipeline-completeness.md 第五节 R6"归因实验:split_test+功效计算(最足)";
SearchPilot 口径(references/monitoring/seo-drift-monitoring.md:"server-side
page-level split test 是唯一真因果检验";program-management.md PRD 第 6 件:
主指标 + 对照构造 + 预注册判读防事后移动球门,证据库归档)。

统计口径(注释级,全部手写):
  * 设计 = 页面级随机 + 周期切换(crossover,第 N 周组间互换)的 SEO split test;
  * 分析样本 = 页×周(每个页面每周一个观测;功效计算假设页×周独立——同页跨周
    相关会使真实功效略低于本估计,已列入假设清单);
  * 点击计数按泊松近似 var = φ·mean(φ=--dispersion,默认 1.0;GSC 实数据常过散,
    可按 周方差/周均值 实测值调大);
  * 功效/样本量 = 双样本 t 检验的正态近似(z 法,Cohen 口径);
  * 判读 = Welch t + Welch–Satterthwaite df(两臂页数/方差可不等),t 分布分位数
    由手写正则化不完全贝塔函数(连分式)求出。

三个子命令:
  plan    功效计算:给定 MDE 的统计功效 + 所需最少页数/周数组合表(功效梯度
         0.6/0.8/0.9)+ MDE 下限(当前样本在功效 0.8 下能检出的最小相对效应)
         + 预注册写档(--save-plan 冻结判读口径)/核验(--verify-plan 参数漂移即报)
  assign  分层随机分配:按 URL 目录首段分层(防模板偏斜),层内 seed shuffle 均分
         treatment/control + crossover 计划(第 N 周组间互换,输出两期分配表)
  analyze 两样本对比:页面级点击聚合,均值差 + 95% CI + Welch t + Cohen's d;
         预处理剔除零流量页并报比例;每臂 <10 页 → insufficient_data,只给
         "当前样本只能检测 >X% 效应"提示,不猜方向;--plan 读预注册档按冻结口径判读

用法:
  python3 split_test.py plan --pages 120 --baseline-clicks 2.5 --weeks 8 \
      [--mde 0.1 --alpha 0.05 --ratio 0.5 --dispersion 1.0 \
       --save-plan plan.json --verify-plan plan.json] [--json]
  python3 split_test.py assign --urls urls.txt [--ratio 0.5 --seed 42 --crossover 4] [--json]
  python3 split_test.py analyze --treated gsc1.csv --control gsc2.csv \
      [--weeks 2 --alpha 0.05 --plan plan.json] [--json]
兼容 `--plan --pages ...`(首个 --plan/--assign/--analyze 归一为子命令)。
CSV 口径同 did_attribution.py:Page/URL + Clicks(+可选 Date 列,用于推断窗口周数)。
退出码:0=出结果;1=insufficient_data / 预注册参数漂移;2=输入/参数错误。"""
import argparse
import csv
import json
import math
import random
import sys
from datetime import date, datetime, timezone
from functools import lru_cache
from statistics import NormalDist, fmean, variance
from urllib.parse import urlparse

SCHEMA_VERSION = 1
ND = NormalDist()
MIN_PAGES_PER_ARM = 10          # 判读闸门:每臂有效页 <10 → insufficient_data(不猜)
POWER_TARGETS = (0.60, 0.80, 0.90)   # 梯度
POWER_FOR_FLOOR = 0.80          # MDE 下限的目标功效口径
WEEK_GRID = (2, 4, 6, 8, 12)    # 页数×周数组合表的周数列
MAX_ASSIGN_ROWS_PRINT = 50

ASSUMPTIONS = [
    "样本=页×周,功效按页×周独立近似;同页跨周相关(排名自相关)会使真实功效低于估计",
    "点击计数按泊松近似 var=φ·mean(φ=--dispersion);GSC 实数据常过散,φ=2 时所需样本约翻倍",
    "功效/样本量用双样本 t 检验的正态近似(z 法);判读用 Welch t(不要求两臂方差齐)",
    "crossover 减模板/目录层混杂,不改变本方差口径;周期切换前后各留 1 周洗脱更稳",
    "季节性/算法更新未被排除:判读窗口撞算法 rollout 时冻结顺延(seo-drift-monitoring 第五节)",
    "GSC 窗口若与 2025-05-13~2026-04-27 断代重叠,只信 Clicks(did_attribution 同口径)",
]


class DataError(Exception):
    """输入文件/参数错误 → exit 2。"""


# ---------- 手写 t 分布(正则化不完全贝塔,连分式;stdlib only) ----------

def _betacf(a, b, x):
    """不完全贝塔的连分式(Numerical Recipes 口径)。"""
    MAXIT, EPS, FPMIN = 300, 3e-14, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def betainc(a, b, x):
    """正则化不完全贝塔 I_x(a,b)。"""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    ln_front = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                + a * math.log(x) + b * math.log(1.0 - x))
    front = math.exp(ln_front)
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_two_sided_p(t, df):
    """P(|T| ≥ t),t 分布。"""
    if df <= 0:
        return 1.0
    if math.isinf(t):
        return 0.0
    return betainc(df / 2.0, 0.5, df / (df + t * t))


def t_cdf(t, df):
    if t == 0.0:
        return 0.5
    tail = 0.5 * betainc(df / 2.0, 0.5, df / (df + t * t))
    return 1.0 - tail if t > 0 else tail


@lru_cache(maxsize=512)
def t_ppf(p, df):
    """t 分布分位数(二分求逆;df 调用点先 round 以命中缓存)。"""
    if not 0.0 < p < 1.0:
        raise DataError(f"t_ppf p 须在 (0,1): {p}")
    lo, hi = -1e3, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-10:
            break
    return (lo + hi) / 2.0


def t_crit_two_sided(alpha, df):
    """双侧 α 的 t 临界值;df 取 4 位小数进缓存键(误差 << CI 显示精度)。"""
    return t_ppf(round(1.0 - alpha / 2.0, 12), round(df, 4))


# ---------- 功效/样本量(z 法近似;口径见模块 docstring) ----------

def sigma_of(baseline_clicks, dispersion):
    """页·周点击标准差:泊松近似 var=φ·mean。"""
    return math.sqrt(dispersion * baseline_clicks)


def power_two_sample(delta, sigma, n1, n2, alpha):
    """双样本正态近似功效:Φ(λ−z)+Φ(−λ−z),λ=delta/SE。"""
    if n1 <= 0 or n2 <= 0 or sigma <= 0 or delta <= 0:
        return 0.0
    se = sigma * math.sqrt(1.0 / n1 + 1.0 / n2)
    lam = delta / se
    z = ND.inv_cdf(1.0 - alpha / 2.0)
    return ND.cdf(lam - z) + ND.cdf(-lam - z)


def page_weeks_total_needed(delta, sigma, alpha, power, ratio):
    """达标所需双臂合计页·周数:解 λ=z_α/2+z_power(等臂比 r 展开为 1/r+1/(1−r))。"""
    if delta <= 0 or sigma <= 0 or not 0.5 <= power < 1.0:
        return None
    z_a = ND.inv_cdf(1.0 - alpha / 2.0)
    z_p = ND.inv_cdf(power)
    n = sigma ** 2 * (1.0 / ratio + 1.0 / (1.0 - ratio)) * (z_a + z_p) ** 2 / delta ** 2
    return math.ceil(n)


def mde_floor(sigma, n1, n2, alpha, power, baseline):
    """当前样本在目标功效下的最小可检相对效应(绝对 δ/基线)。"""
    if n1 <= 0 or n2 <= 0 or baseline <= 0:
        return None
    se = sigma * math.sqrt(1.0 / n1 + 1.0 / n2)
    delta = (ND.inv_cdf(1.0 - alpha / 2.0) + ND.inv_cdf(power)) * se
    return delta / baseline


# ---------- Welch 两样本对比 ----------

def welch(xs, ys, alpha=0.05):
    """Welch t + Welch–Satterthwaite df + 双侧 p + CI。"""
    n1, n2 = len(xs), len(ys)
    if n1 < 2 or n2 < 2:
        raise DataError("每臂至少 2 个有效页面观测才能算 Welch t")
    m1, m2 = fmean(xs), fmean(ys)
    v1, v2 = variance(xs), variance(ys)
    a1, a2 = v1 / n1, v2 / n2
    se = math.sqrt(a1 + a2)
    diff = m1 - m2
    df = (a1 + a2) ** 2 / (a1 ** 2 / (n1 - 1) + a2 ** 2 / (n2 - 1))
    if se == 0.0:                     # 两臂全常数:退化为确定性差
        p = 0.0 if diff != 0 else 1.0
        return {"n1": n1, "n2": n2, "mean1": m1, "mean2": m2,
                "var1": v1, "var2": v2, "diff": diff, "se": 0.0,
                "t": math.inf if diff > 0 else (-math.inf if diff < 0 else 0.0),
                "df": df, "p": p, "t_crit": 0.0,
                "ci_lo": diff, "ci_hi": diff, "alpha": alpha}
    t = diff / se
    p = t_two_sided_p(abs(t), df)
    tc = t_crit_two_sided(alpha, df)
    sp = math.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
    return {"n1": n1, "n2": n2, "mean1": m1, "mean2": m2, "var1": v1, "var2": v2,
            "diff": diff, "se": se, "t": t, "df": df, "p": p, "t_crit": tc,
            "ci_lo": diff - tc * se, "ci_hi": diff + tc * se,
            "cohen_d": (diff / sp) if sp > 0 else None, "alpha": alpha}


# ---------- 输入 ----------

def load_clicks_csv_with_dates(path):
    """GSC 页面级 CSV → ({page: clicks 窗口合计}, Date 跨度或 None)。
    列名宽容(Page/URL/Landing Page + Clicks),口径同 did_attribution.load_gsc_csv。"""
    try:
        f = open(path, encoding="utf-8-sig", newline="")
    except OSError as e:
        raise DataError(f"无法读取 {path}: {e}")
    with f:
        rdr = csv.DictReader(f)
        if not rdr.fieldnames:
            raise DataError(f"{path}: 空 CSV")
        cols = {c.strip().lower(): c for c in rdr.fieldnames if c}
        page_k = next((cols[k] for k in ("page", "url", "landing page") if k in cols), None)
        click_k = next((cols[k] for k in ("clicks",) if k in cols), None)
        date_k = next((cols[k] for k in ("date",) if k in cols), None)
        if not page_k or not click_k:
            raise DataError(f"{path}: 需要 Page 和 Clicks 列,实际列={list(rdr.fieldnames)}")
        pages, dates = {}, []
        for row in rdr:
            url = (row.get(page_k) or "").strip()
            if not url:
                continue
            raw = (row.get(click_k) or "0").replace(",", "")
            neg = raw.startswith("-")
            digits = raw.lstrip("-")
            try:
                c = float(digits)
            except ValueError:
                c = 0.0
            pages[url] = pages.get(url, 0) + max(0.0, -c if neg else c)
            if date_k and (row.get(date_k) or "").strip():
                try:
                    dates.append(date.fromisoformat(row[date_k].strip()[:10]))
                except ValueError:
                    pass
    if not pages:
        raise DataError(f"{path}: 无有效页面行")
    span = (min(dates), max(dates)) if dates else None
    return pages, span


def load_urls(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except OSError as e:
        raise DataError(f"无法读取 {path}: {e}")
    if not lines:
        raise DataError(f"{path}: 无 URL 行")
    seen, dup = set(), 0
    urls = []
    for u in lines:
        if u in seen:
            dup += 1
            continue
        seen.add(u)
        urls.append(u)
    return urls, dup


def stratum_of(url):
    """URL 目录首段(小写):模板/页面族的代理变量,分层防模板偏斜。"""
    path = urlparse(url).path if "://" in url else url
    for seg in path.split("/"):
        if seg:
            return seg.lower()
    return "(root)"


# ---------- 预注册档 ----------

PLAN_PARAM_KEYS = ("pages", "weeks", "baseline_clicks", "mde", "alpha", "ratio", "dispersion")


def write_plan_file(path, payload):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
    except OSError as e:
        raise DataError(f"无法写 {path}: {e}")


def read_plan_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise DataError(f"无法读取预注册档 {path}: {e}")
    params = d.get("params")
    if not isinstance(params, dict) or any(k not in params for k in PLAN_PARAM_KEYS):
        raise DataError(f"{path}: 预注册档缺 params({list(PLAN_PARAM_KEYS)})")
    return d


# ---------- 子命令:plan ----------

def cmd_plan(a):
    if a.baseline_clicks <= 0:
        raise DataError("--baseline-clicks 须 >0(页面周均基线点击)")
    if a.mde <= 0:
        raise DataError("--mde 须 >0(相对最小可检效应)")
    if not 0.0 < a.alpha < 1.0:
        raise DataError("--alpha 须在 (0,1)")
    if not 0.0 < a.ratio < 1.0:
        raise DataError("--ratio 须在 (0,1)(treatment 占比)")
    if a.dispersion <= 0:
        raise DataError("--dispersion 须 >0(泊松=1.0)")
    if a.pages <= 0 or a.weeks <= 0:
        raise DataError("--pages / --weeks 须为正整数")

    sigma = sigma_of(a.baseline_clicks, a.dispersion)
    n_total = a.pages * a.weeks
    n1 = n_total * a.ratio
    n2 = n_total * (1.0 - a.ratio)
    delta = a.mde * a.baseline_clicks
    power = power_two_sample(delta, sigma, n1, n2, a.alpha)
    floor = mde_floor(sigma, n1, n2, a.alpha, POWER_FOR_FLOOR, a.baseline_clicks)

    reqs = []
    for tp in POWER_TARGETS:
        n_need = page_weeks_total_needed(delta, sigma, a.alpha, tp, a.ratio)
        reqs.append({"power": tp, "page_weeks_total": n_need,
                     "pages_at_current_weeks": math.ceil(n_need / a.weeks),
                     "weeks_at_current_pages": math.ceil(n_need / a.pages)})
    grid_rows = []
    for tp in POWER_TARGETS:
        n_need = page_weeks_total_needed(delta, sigma, a.alpha, tp, a.ratio)
        grid_rows.append({"power": tp,
                          "pages": [math.ceil(n_need / w) for w in WEEK_GRID]})

    rep = {
        "schema_version": SCHEMA_VERSION,
        "tool": "split_test-plan",
        "design": "页面级随机 + 周期切换(split test),样本=页×周,双样本 t 近似(z 法)",
        "inputs": {"pages": a.pages, "weeks": a.weeks,
                   "baseline_clicks": a.baseline_clicks, "mde": a.mde,
                   "alpha": a.alpha, "ratio": a.ratio, "dispersion": a.dispersion},
        "sigma": round(sigma, 6),
        "sample": {"page_weeks_total": n_total,
                   "per_arm_treated": n1, "per_arm_control": n2,
                   "per_arm_pages_treated": a.pages * a.ratio},
        "power_at_mde": {"mde": a.mde, "delta_clicks": round(delta, 6),
                         "power": round(power, 4),
                         "adequate": power >= 0.80},
        "mde_floor": {"target_power": POWER_FOR_FLOOR, "value": round(floor, 4)},
        "requirements": [{"power": r["power"],
                          "page_weeks_total": r["page_weeks_total"],
                          "pages_at_current_weeks": r["pages_at_current_weeks"],
                          "weeks_at_current_pages": r["weeks_at_current_pages"]}
                         for r in reqs],
        "grid": {"weeks": list(WEEK_GRID), "rows": grid_rows},
        "assumptions": list(ASSUMPTIONS),
        "plan_file": a.save_plan,
    }

    if a.save_plan:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "tool": "split_test",
            "kind": "preregistration",
            "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "design": "页面级随机 + 周期切换(split test),样本=页×周",
            "params": {k: getattr(a, k) for k in PLAN_PARAM_KEYS},
            "planned_power": round(power, 4),
            "mde_floor_power80": round(floor, 4),
            "judgement": {
                "metric": "页面级周均点击均值差(treated − control)",
                "alpha": a.alpha, "mde": a.mde, "direction": "positive",
                "rules": ("CI 下界>0 且相对提升≥MDE → significant_positive;"
                          "CI 上界<0 → significant_negative;跨 0 → inconclusive;"
                          f"每臂有效页<{MIN_PAGES_PER_ARM} → insufficient_data(不猜方向)"),
                "read_when": f"第 {a.weeks} 周窗口关闭后一次性判读;窗口内不得中途读数",
            },
            "anti_peeking": ("判读口径已冻结:analyze --plan 按本档 alpha/mde 判读;"
                             "plan --verify-plan 核参数漂移;中途改口径=移动球门"),
        }
        write_plan_file(a.save_plan, payload)
        rep["plan_written"] = a.save_plan

    drift_rc = 0
    if a.verify_plan:
        frozen = read_plan_file(a.verify_plan)
        drift = [k for k in PLAN_PARAM_KEYS
                 if abs(float(frozen["params"][k]) - float(getattr(a, k))) > 1e-9]
        rep["verify"] = {"file": a.verify_plan,
                         "frozen_at": frozen.get("frozen_at"),
                         "consistent": not drift, "drifted_params": drift}
        if drift:
            drift_rc = 1

    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print_plan(rep)
    return drift_rc


def print_plan(rep):
    W = 76
    inp, s = rep["inputs"], rep["sample"]
    print("=" * W)
    print("SEO Split Test 功效计算(页面级随机+周期切换,样本=页×周)".center(W))
    print("=" * W)
    print(f"输入: {inp['pages']} 页 × {inp['weeks']} 周 · 基线 {inp['baseline_clicks']:g} "
          f"点击/页/周 · treatment 占比 {inp['ratio']:g} · α {inp['alpha']:g}"
          f" · 离散度 φ {inp['dispersion']:g}(泊松=1)")
    print(f"样本: 双臂合计 {s['page_weeks_total']} 页·周(treatment {s['per_arm_treated']:g} / "
          f"control {s['per_arm_control']:g}) · σ=√(φ·λ)={rep['sigma']:.4f} 点击/页·周")
    print("-" * W)
    pm = rep["power_at_mde"]
    print(f"给定 MDE +{pm['mde'] * 100:.1f}%(Δ={pm['delta_clicks']:.4g} 点击/页·周)")
    flag = "" if pm["adequate"] else "   [<0.80 不足——按下一表加量,或接受更宽 MDE]"
    print(f"  → 统计功效 = {pm['power']:.4f}{flag}")
    mf = rep["mde_floor"]
    vs = "比目标 MDE 宽 → 当前样本检不出目标效应" if mf["value"] > pm["mde"] else "已覆盖目标 MDE"
    print(f"MDE 下限(功效 {mf['target_power']:.2f})= +{mf['value'] * 100:.2f}%   [{vs}]")
    print("-" * W)
    print("达标所需最少样本(双臂合计页·周;z 法):")
    print(f"  {'目标功效':<8}{'最少页数@当前' + str(inp['weeks']) + '周':>16}"
          f"{'最少周数@当前' + str(inp['pages']) + '页':>18}")
    for r in rep["requirements"]:
        print(f"  {r['power']:<8}{r['pages_at_current_weeks']:>16}"
              f"{r['weeks_at_current_pages']:>18}"
              + (f"   ← {r['page_weeks_total']} 页·周" if r["power"] == 0.8 else ""))
    print("页数×周数组合表(格=所需最少总页数;行=功效,列=周数):")
    head = "".join(f"{w:>7}" for w in rep["grid"]["weeks"])
    corner = "功效\\周数"   # 反斜杠不能写进 f-string 表达式(3.12 前 SyntaxError)
    print(f"  {corner:<10}{head}")
    for row in rep["grid"]["rows"]:
        cells = "".join(f"{p:>7}" for p in row["pages"])
        print(f"  {row['power']:<10}{cells}")
    if rep.get("plan_written") or "verify" in rep:
        print("-" * W)
    if rep.get("plan_written"):
        print(f"预注册档已冻结: {rep['plan_written']}(判读口径写死;"
              "窗口关闭前不得中途读数,防 peeking)")
    if "verify" in rep:
        v = rep["verify"]
        if v["consistent"]:
            print(f"预注册核验: {v['file']} 参数一致(冻结有效,"
                  f"frozen_at={v['frozen_at']})")
        else:
            print(f"预注册核验: {v['file']} 参数漂移 → {v['drifted_params']}"
                  "  [判读口径已被改动=移动球门,须按原档或重开实验]")
    print("-" * W)
    print("假设与局限:")
    for x in rep["assumptions"]:
        print(f"  - {x}")
    print("=" * W)


# ---------- 子命令:assign ----------

def stratified_assign(urls, ratio, seed):
    """按目录首段分层,层内 sorted+shuffle 均分;确定性=(urls,ratio,seed)。"""
    strata = {}
    for u in urls:
        strata.setdefault(stratum_of(u), []).append(u)
    rng = random.Random(seed)
    assign = {}
    for st in sorted(strata):
        members = sorted(strata[st])
        rng.shuffle(members)
        k = int(math.floor(len(members) * ratio + 0.5))
        for u in members[:k]:
            assign[u] = "treatment"
        for u in members[k:]:
            assign[u] = "control"
    strata_summary = {st: {"pages": len(us),
                           "treatment": sum(1 for u in us if assign[u] == "treatment"),
                           "control": sum(1 for u in us if assign[u] == "control")}
                      for st, us in strata.items()}
    return assign, strata_summary


def cmd_assign(a):
    if not 0.0 < a.ratio < 1.0:
        raise DataError("--ratio 须在 (0,1)(treatment 占比)")
    if a.crossover is not None and a.crossover < 2:
        raise DataError("--crossover 须 ≥2(第 N 周组间互换,之前至少留 1 周)")
    urls, dup = load_urls(a.urls)
    assign, strata = stratified_assign(urls, a.ratio, a.seed)
    swap = {"treatment": "control", "control": "treatment"}
    period2 = {u: (swap[g] if a.crossover else g) for u, g in assign.items()}
    rep = {
        "schema_version": SCHEMA_VERSION,
        "tool": "split_test-assign",
        "design": "按 URL 目录首段分层(防模板偏斜),层内 seed shuffle 均分",
        "urls_file": a.urls, "seed": a.seed, "ratio": a.ratio,
        "duplicates_dropped": dup,
        "crossover_week": a.crossover,
        "period1_weeks": f"1-{a.crossover - 1}" if a.crossover else None,
        "period2_weeks": f"{a.crossover}+" if a.crossover else None,
        "strata": {st: strata[st] for st in sorted(strata)},
        "counts": {"pages": len(urls),
                   "treatment": sum(1 for g in assign.values() if g == "treatment"),
                   "control": sum(1 for g in assign.values() if g == "control")},
        "assignments": [{"url": u, "stratum": stratum_of(u),
                         "period1": assign[u], "period2": period2[u]} for u in urls],
        "notes": ["层内 |treatment−control| ≤ 1(round 均分);跨层比例可能有 ±1 页偏差",
                  "crossover:第 N 周起组间互换,吸收模板/目录层时间趋势"],
    }
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print_assign(rep)
    return 0


def print_assign(rep):
    W = 76
    c = rep["counts"]
    print("=" * W)
    print("SEO Split Test 分层随机分配(目录首段分层,层内 shuffle 均分)".center(W))
    print("=" * W)
    print(f"输入: {rep['urls_file']} · {c['pages']} URL · {len(rep['strata'])} 层"
          f" · seed {rep['seed']} · treatment 占比 {rep['ratio']:g}"
          + (f" · 去重剔除 {rep['duplicates_dropped']} 条" if rep["duplicates_dropped"] else ""))
    print(f"全局: treatment {c['treatment']} / control {c['control']}"
          f" (实际比例 {c['treatment'] / c['pages']:.3f})")
    print("-" * W)
    print(f"  {'层':<18}{'页数':>6}{'treatment':>11}{'control':>9}")
    for st, s in rep["strata"].items():
        print(f"  {st[:16]:<18}{s['pages']:>6}{s['treatment']:>11}{s['control']:>9}")
    if rep["crossover_week"]:
        print("-" * W)
        print(f"crossover 计划:第 {rep['crossover_week']} 周起组间互换"
              f"(P1={rep['period1_weeks']} 周,P2={rep['period2_weeks']} 周)"
              "——互换吸收模板/目录层时间趋势,判读按两期合并")
    else:
        print("-" * W)
        print("crossover 计划: 未启用(--crossover N 可生成第 N 周互换的两期分配)")
    print("-" * W)
    rows = rep["assignments"]
    p2_head = f"P2(周{rep['period2_weeks']})" if rep["crossover_week"] else "P2"
    print(f"  {'URL':<52}{'层':<12}{'P1':<11}{p2_head}")
    for r in rows[:MAX_ASSIGN_ROWS_PRINT]:
        print(f"  {r['url'][:50]:<52}{r['stratum'][:10]:<12}{r['period1']:<11}{r['period2']}")
    if len(rows) > MAX_ASSIGN_ROWS_PRINT:
        print(f"  ...(其余 {len(rows) - MAX_ASSIGN_ROWS_PRINT} 行见 --json)")
    print("-" * W)
    for n in rep["notes"]:
        print(f"  * {n}")
    print("=" * W)


# ---------- 子命令:analyze ----------

def cmd_analyze(a):
    if not 0.0 < a.alpha < 1.0:
        raise DataError("--alpha 须在 (0,1)")
    treated, t_span = load_clicks_csv_with_dates(a.treated)
    control, c_span = load_clicks_csv_with_dates(a.control)

    # 窗口周数:--weeks 优先 → Date 跨度推断 → 1
    if a.weeks:
        weeks, wsrc = a.weeks, "arg"
    else:
        span = t_span or c_span
        if span:
            weeks = max(1, math.ceil(((span[1] - span[0]).days + 1) / 7))
            wsrc = "date-span"
        else:
            weeks, wsrc = 1, "default"

    # 预处理:剔除零流量页(无点击信号,计入只会虚增样本量/假功效),报比例
    def arm(pages):
        raw = len(pages)
        kept = {u: c for u, c in pages.items() if c > 0}
        return kept, raw, raw - len(kept)

    t_pages, t_raw, t_zero = arm(treated)
    c_pages, c_raw, c_zero = arm(control)

    prereg, warnings = None, []
    alpha = a.alpha
    if a.plan:
        prereg = read_plan_file(a.plan)
        j = prereg.get("judgement", {})
        alpha = float(j.get("alpha", prereg["params"]["alpha"]))
        if abs(alpha - a.alpha) > 1e-9:
            warnings.append(f"α 按预注册档冻结为 {alpha:g}(CLI 传入 {a.alpha:g} 被忽略)")
        plan_weeks = prereg["params"].get("weeks")
        if int(plan_weeks) != int(weeks):
            warnings.append(f"判读窗口 {weeks} 周 ≠ 预注册 {int(plan_weeks)} 周:"
                            "窗口漂移(peeking 风险),判读口径仍按预注册 α/MDE")

    rep = {
        "schema_version": SCHEMA_VERSION,
        "tool": "split_test-analyze",
        "files": {"treated": a.treated, "control": a.control},
        "weeks": weeks, "weeks_source": wsrc, "alpha_used": alpha,
        "preprocess": {
            "treated": {"pages_raw": t_raw, "zero_click_removed": t_zero,
                        "pages_used": len(t_pages)},
            "control": {"pages_raw": c_raw, "zero_click_removed": c_zero,
                        "pages_used": len(c_pages)},
            "rule": "剔除窗口内 0 点击页(无信号,计入虚增样本量);对负向效应检出偏乐观,已列 caveats",
        },
        "preregistered": bool(a.plan), "plan_file": a.plan,
        "warnings": warnings,
    }

    insufficient = len(t_pages) < MIN_PAGES_PER_ARM or len(c_pages) < MIN_PAGES_PER_ARM
    stats = welch(list(t_pages.values()), list(c_pages.values()), alpha) \
        if len(t_pages) >= 2 and len(c_pages) >= 2 else None

    if stats:
        mean_c = stats["mean2"]
        lift = (stats["diff"] / mean_c) if mean_c > 0 else None
        # MDE 下限(观测 SE 口径,功效 0.80):相对控制组均值
        se_rel = (stats["se"] / mean_c) if mean_c > 0 else None
        floor = ((ND.inv_cdf(1 - alpha / 2) + ND.inv_cdf(POWER_FOR_FLOOR)) * se_rel
                 if se_rel is not None else None)
        if insufficient:
            verdict = "insufficient_data"
        elif stats["ci_lo"] > 0:
            verdict = "significant_positive"
        elif stats["ci_hi"] < 0:
            verdict = "significant_negative"
        else:
            verdict = "inconclusive"
        meets = None
        if prereg and verdict == "significant_positive":
            meets = lift is not None and lift >= float(prereg["params"]["mde"])
        rep.update({
            "n_treated": stats["n1"], "n_control": stats["n2"],
            "means": {"treated_window": round(stats["mean1"], 4),
                      "control_window": round(stats["mean2"], 4),
                      "treated_weekly": round(stats["mean1"] / weeks, 4),
                      "control_weekly": round(stats["mean2"] / weeks, 4)},
            "diff": round(stats["diff"], 4),
            "diff_weekly": round(stats["diff"] / weeks, 4),
            "relative_lift": round(lift, 4) if lift is not None else None,
            "se": round(stats["se"], 4),
            "ci95": [round(stats["ci_lo"], 4), round(stats["ci_hi"], 4)],
            "t": round(stats["t"], 4) if math.isfinite(stats["t"]) else None,
            "df": round(stats["df"], 2),
            "p_value": (round(stats["p"], 6) if stats["p"] >= 1e-6
                        else float(f"{stats['p']:.1e}")),
            "cohen_d": round(stats["cohen_d"], 4) if stats.get("cohen_d") is not None else None,
            "mde_floor_power80": round(floor, 4) if floor is not None else None,
            "verdict": verdict,
        })
        if meets is not None:
            rep["meets_preregistered_mde"] = meets
    else:
        rep.update({"verdict": "insufficient_data",
                    "reason": "有效页 <2,无法计算 Welch t"})

    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print_analyze(rep)
    return 1 if rep["verdict"] == "insufficient_data" else 0


def print_analyze(rep):
    W = 76
    pp = rep["preprocess"]
    print("=" * W)
    print("SEO Split Test 两样本判读(页面级点击聚合,Welch t)".center(W))
    print("=" * W)
    print(f"数据: treated={rep['files']['treated']}  control={rep['files']['control']}"
          f" · 窗口 {rep['weeks']} 周({rep['weeks_source']}) · α={rep['alpha_used']:g}"
          + (" · 预注册判读" if rep["preregistered"] else ""))
    for side, key in (("treated", "treated"), ("control", "control")):
        s = pp[key]
        pct = (s["zero_click_removed"] / s["pages_raw"] * 100) if s["pages_raw"] else 0
        print(f"预处理[{side}]: {s['pages_raw']} 页 → 剔除零流量 {s['zero_click_removed']} 页"
              f"({pct:.1f}%) → 有效 {s['pages_used']} 页")
    print("-" * W)
    for w in rep.get("warnings", []):
        print(f"[预注册警告] {w}")
    if rep.get("verdict") == "insufficient_data" and "n_treated" not in rep:
        print(f"判定: insufficient_data —— {rep.get('reason')}")
        print("=" * W)
        return
    if rep.get("verdict") == "insufficient_data":
        print(f"[闸门] 每臂有效页 {rep['n_treated']}/{rep['n_control']} < {MIN_PAGES_PER_ARM}"
              " → insufficient_data(不猜方向)")
        if rep.get("mde_floor_power80") is not None:
            print(f"  当前样本在功效 {POWER_FOR_FLOOR:.2f} 下只能检测 "
                  f"> +{rep['mde_floor_power80'] * 100:.1f}% 的相对效应"
                  f"(MDE 下限;plan 子命令可算达标页数/周数组合)")
        print("  建议:加页数、延长窗口,或接受更宽 MDE——而不是对噪声猜方向")
    else:
        m = rep["means"]
        print(f"均值(点击/页/窗口): treated {m['treated_window']:.4g} vs "
              f"control {m['control_window']:.4g}   (周均 {m['treated_weekly']:.4g}"
              f" vs {m['control_weekly']:.4g})")
        lift = rep.get("relative_lift")
        lift_s = f"{lift * 100:+.2f}%" if lift is not None else "N/A"
        print(f"均值差 = {rep['diff']:+.4g} 点击/页({lift_s})"
              f"   95% CI [{rep['ci95'][0]:+.4g}, {rep['ci95'][1]:+.4g}]")
        t_s = f"{rep['t']:.4g}" if rep.get("t") is not None else "∞"
        print(f"Welch t = {t_s}(df {rep['df']:.1f},p {rep['p_value']:g})"
              f"   Cohen's d = {rep['cohen_d'] if rep.get('cohen_d') is not None else 'N/A'}")
        if rep.get("mde_floor_power80") is not None:
            print(f"MDE 下限(功效 {POWER_FOR_FLOOR:.2f})= "
                  f"+{rep['mde_floor_power80'] * 100:.2f}% 相对效应")
        verdicts = {"significant_positive": "CI 下界>0", "significant_negative": "CI 上界<0",
                    "inconclusive": "CI 跨 0"}
        print(f"判定: {rep['verdict'].upper()}  ({verdicts[rep['verdict']]})")
        if rep["preregistered"]:
            mtxt = ("是" if rep.get("meets_preregistered_mde") else
                    "否" if "meets_preregistered_mde" in rep else "不适用")
            print(f"[预注册] {rep['plan_file']}:α/MDE 冻结;达到预注册 MDE: {mtxt}"
                  "——即使显著但未达 MDE,只报实测效应,不抬杠到 MDE")
    print("-" * W)
    print("caveats:")
    print("  * 剔零流量页对负向效应检出偏乐观(处理组零点击页已被移出)")
    print("  * 页×周独立近似;同页跨周相关会低估 SE(判读偏宽松)")
    print("  * 服务器端页面级 split test 是唯一真因果检验;算法 rollout 撞窗冻结顺延")
    print("  * 结论请按 program-management.md 第四节归档进证据库(不归档=实验白做)")
    print("=" * W)


# ---------- CLI ----------

def build_parser():
    ap = argparse.ArgumentParser(
        prog="split_test.py",
        description="页面级增量实验(split test)+功效计算:"
                    "plan 功效/样本量/预注册 · assign 分层随机+crossover · analyze Welch 判读",
        epilog="口径:页面级随机+周期切换,样本=页×周;泊松 var=φ·mean;"
               "功效=z 法近似,判读=Welch t。示例:\n"
               "  python3 split_test.py plan --pages 120 --baseline-clicks 2.5 --weeks 8"
               " --save-plan plan.json\n"
               "  python3 split_test.py assign --urls urls.txt --seed 42 --crossover 4\n"
               "  python3 split_test.py analyze --treated gsc1.csv --control gsc2.csv"
               " --weeks 2 --plan plan.json --json")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="功效计算+最少样本组合表+MDE 下限+预注册写档/核验")
    p.add_argument("--pages", type=int, required=True, help="实验总页数(两臂合计)")
    p.add_argument("--baseline-clicks", type=float, required=True,
                   help="基线周均点击/页(页×周计)")
    p.add_argument("--weeks", type=int, required=True, help="判读窗口周数")
    p.add_argument("--mde", type=float, default=0.1,
                   help="最小可检相对效应(默认 0.1=+10%%)")
    p.add_argument("--alpha", type=float, default=0.05, help="双侧显著性水平(默认 0.05)")
    p.add_argument("--ratio", type=float, default=0.5, help="treatment 页占比(默认 0.5)")
    p.add_argument("--dispersion", type=float, default=1.0,
                   help="过散度 φ,var=φ·mean(泊松=1;GSC 实数据常 1.5-3)")
    p.add_argument("--save-plan", help="预注册写档:冻结判读口径(防 peeking)")
    p.add_argument("--verify-plan", help="预注册核验:对比当前参数与冻结档(漂移→exit 1)")
    p.add_argument("--json", action="store_true", help="结构化输出(带 schema_version)")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("assign", help="分层随机分配(目录首段分层)+crossover 两期表")
    p.add_argument("--urls", required=True, help="URL 清单文件(每行一条)")
    p.add_argument("--ratio", type=float, default=0.5, help="treatment 占比(默认 0.5)")
    p.add_argument("--seed", type=int, default=42, help="随机种子(默认 42,可复现)")
    p.add_argument("--crossover", type=int, default=4,
                   help="第 N 周组间互换(默认 4;0=不启用)")
    p.add_argument("--json", action="store_true", help="结构化输出")
    p.set_defaults(func=cmd_assign)

    p = sub.add_parser("analyze", help="两样本对比:均值差+95%% CI+Welch t+效应量")
    p.add_argument("--treated", required=True, help="处理组 GSC 页面级 CSV(Page,Clicks)")
    p.add_argument("--control", required=True, help="对照组 GSC 页面级 CSV")
    p.add_argument("--weeks", type=int, default=None,
                   help="窗口周数(缺省从 Date 列推断,再缺省 1)")
    p.add_argument("--alpha", type=float, default=0.05,
                   help="双侧 α(默认 0.05;--plan 在场时按冻结 α)")
    p.add_argument("--plan", default=None, help="预注册档:按冻结 α/MDE 判读+漂移警告")
    p.add_argument("--json", action="store_true", help="结构化输出")
    p.set_defaults(func=cmd_analyze)
    return ap


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("--plan", "--assign", "--analyze"):
        argv[0] = argv[0][2:]          # 兼容 `--plan --pages ...` 写法
    a = build_parser().parse_args(argv)
    try:
        return a.func(a)
    except DataError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
