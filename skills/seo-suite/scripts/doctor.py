#!/usr/bin/env python3
"""环境自检 + 凭证分层探测(claude-seo doctor 口径,纯 stdlib,默认零网络)。

detect_tier 只做本地文件/环境变量存在性判断——零网络请求,绝不读取或打印
凭证值(gsc.json 只探测顶层键名,值不出探测函数):

  T0 无任何凭证 → 纯静态审计可用(site_audit/health_score 等本地能力)
  T1 环境变量 PSI_API_KEY 或 CRUX_API_KEY 存在(非空) → +PageSpeed/CrUX
  T2 ~/.config/seo-suite/gsc.json 存在且含 credentials 键 → +GSC
  T3 gsc.json 另含 ga4_property_id 键 → +GA4
  输出 {tier, capabilities[](逐层累加), missing:"配置 X 可解锁 Y"} 升级指引

自检项:Python ≥3.9 / markets.json 可解析且市场数=18 / 模板类目录齐全 /
scripts/*.py 全部可编译(py_compile 静默批量) / tests 可发现 /
通知渠道配置存在性(只报渠道名与已配/未配,绝不打印值) /
--net 可选网络可达性(HEAD https://developers.google.com,5s 超时;
失败只警告,不影响 ready)。

redact 纪律(claude-seo doctor 口径):所有输出过 redact()——
home 路径→<home> / email→<redacted-email> / token·password·secret·api_key
值→<redacted>(键名保留);detail 构造时只用 basename,双保险。
输出 intentionally omits absolute paths and environment values。

用法:
  python3 doctor.py            # 人读逐行报告(Python:/markets:/templates:/
                               #  scripts:/tests:/channels:/tier:/ready:)
  python3 doctor.py --json     # {ready, tier, checks:[{id,pass,detail}], reasons[]}
  python3 doctor.py --fix-tips # 对每个 fail 附一条修复建议(人读模式)
  python3 doctor.py --net      # 附网络可达性探测(可选,默认零网络)

退出码:0=ready / 3=需处理(doctor 契约;channels/tier/net 为信息项不影响 ready)。
"""
import argparse
import glob
import json
import os
import py_compile
import re
import sys
import tempfile
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GSC_REL = os.path.join(".config", "seo-suite", "gsc.json")
EXPECTED_MARKETS = 18
TEMPLATE_DIRS = ("audit", "content", "monitor", "research")
NET_URL = "https://developers.google.com"
NET_TIMEOUT = 5
# 影响退出码的硬检查;channels(信息)/net(仅警告)不在其列
HARD_IDS = frozenset({"python", "markets", "templates", "scripts", "tests"})
# 通知渠道探测(notify.py 渠道型;secret 只经 env 注入,doctor 只看存在性)
CHANNEL_ENVS = (("slack", ("SEO_MONITOR_SLACK_WEBHOOK",)),
                ("discord", ("SEO_MONITOR_DISCORD_WEBHOOK",)),
                ("telegram", ("SEO_MONITOR_TG_TOKEN", "SEO_MONITOR_TG_CHAT")),
                ("webhook", ("SEO_MONITOR_WEBHOOK_URL",)))
EMAIL_ENV = "SEO_MONITOR_SMTP_PASS"
CHANNEL_ORDER = ("slack", "discord", "telegram", "webhook", "email")

# ---------- redact 三连(claude-seo doctor 口径;email/secret 两式与 notify.py 同源) ----------

_REDACT_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_REDACT_SECRET_KV = re.compile(
    r"""(?i)(["']?)\b([a-z0-9_-]*(?:api[_-]?key|token|password|passwd|secret)[a-z0-9_-]*)\b\1
        (\s*[:=]\s*)(["']?)[^\s"',;]+\4""", re.X)


def redact(s, home=None):
    """doctor 输出脱敏:1) home 绝对路径 → <home>;2) email → <redacted-email>;
    3) token/password/secret/api_key 键值对的值 → <redacted>(键名保留便于排查)。
    幂等:已脱敏文本再过一遍不变形。"""
    home = os.path.expanduser("~") if home is None else home
    s = str(s)
    if home and len(home) > 1:
        s = s.replace(home, "<home>")
    s = _REDACT_EMAIL.sub("<redacted-email>", s)
    s = _REDACT_SECRET_KV.sub(
        lambda m: "%s%s%s%s<redacted>%s" % (m.group(1), m.group(2), m.group(1),
                                            m.group(3), m.group(4)), s)
    return s


# ---------- 凭证分层探测(纯本地,零网络) ----------

def _gsc_key_names(gsc_path):
    """只返回 gsc.json 顶层键名集合(文件缺失 → None;不可解析 → 空集)。
    只探测存在与键名——值绝不离开本函数,更不进任何输出。"""
    if not os.path.isfile(gsc_path):
        return None
    try:
        with open(gsc_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return frozenset()
    return frozenset(data) if isinstance(data, dict) else frozenset()


def detect_tier(env=None, home=None):
    """T0 纯静态 → T1 PSI/CrUX key → T2 GSC credentials 键 → T3 ga4_property_id 键。
    各层独立探测、能力逐层累加,tier=已满足的最高层;missing 给下一层的升级指引。"""
    env = os.environ if env is None else env
    home = os.path.expanduser("~") if home is None else home
    caps = ["static-audit"]                      # T0:site_audit/health_score 等本地能力
    tier = 0
    has_psi, has_crux = bool(env.get("PSI_API_KEY")), bool(env.get("CRUX_API_KEY"))
    if has_psi or has_crux:
        tier = 1
        if has_psi:
            caps.append("psi")
        if has_crux:
            caps.append("crux")
    keys = _gsc_key_names(os.path.join(home, GSC_REL))
    if keys and "credentials" in keys:
        tier = max(tier, 2)
        caps.append("gsc")
        if "ga4_property_id" in keys:
            tier = 3
            caps.append("ga4")
    nxt = {0: "配置环境变量 PSI_API_KEY 或 CRUX_API_KEY 可解锁 PageSpeed/CrUX",
           1: "配置 ~/.config/seo-suite/gsc.json(含 credentials 键)可解锁 GSC",
           2: "gsc.json 补 ga4_property_id 键可解锁 GA4"}
    return {"tier": tier, "capabilities": caps, "missing": nxt.get(tier, "")}


# ---------- 自检项(全部返回 {id, pass, detail};detail 只用 basename/计数) ----------

def check_python():
    ok = sys.version_info >= (3, 9)
    return {"id": "python", "pass": ok,
            "detail": "%d.%d.%d(需要 ≥3.9)" % sys.version_info[:3]}


def check_markets(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        n = len(data.get("markets", {})) if isinstance(data, dict) else -1
    except (OSError, ValueError) as e:
        return {"id": "markets", "pass": False,
                "detail": "%s 不可解析(%s)" % (os.path.basename(path), type(e).__name__)}
    return {"id": "markets", "pass": n == EXPECTED_MARKETS,
            "detail": "可解析,%d/%d 市场" % (n, EXPECTED_MARKETS)}


def check_templates(base):
    tdir = os.path.join(base, "templates")
    counts = []
    for sub in TEMPLATE_DIRS:
        n = len([f for dp, _, fs in os.walk(os.path.join(tdir, sub))
                 for f in fs if f.endswith(".md")])
        counts.append(n)
    total, full = sum(counts), sum(1 for c in counts if c > 0)
    return {"id": "templates", "pass": total > 0 and full == len(TEMPLATE_DIRS),
            "detail": "%d 个模板 .md,%d/%d 类目录(%s)齐全"
                      % (total, full, len(TEMPLATE_DIRS), "/".join(TEMPLATE_DIRS))}


def check_scripts(scripts_dir):
    """py_compile 静默批量(字节码写临时目录,不污染 __pycache__);
    失败清单只列 basename(编译错误文本含绝对路径,不进 detail)。"""
    paths = sorted(glob.glob(os.path.join(scripts_dir, "*.py")))
    if not paths:
        return {"id": "scripts", "pass": False, "detail": "目录缺失或无 .py 文件"}
    failed = []
    with tempfile.TemporaryDirectory(prefix="doctor_pyc_") as td:
        for i, p in enumerate(paths):
            try:
                py_compile.compile(p, cfile=os.path.join(td, "c%d.pyc" % i), doraise=True)
            except Exception:
                failed.append(os.path.basename(p))
    if failed:
        return {"id": "scripts", "pass": False,
                "detail": "%d/%d 编译失败: %s"
                          % (len(failed), len(paths), "、".join(failed[:5]))}
    return {"id": "scripts", "pass": True, "detail": "%d 个 .py 全部可编译" % len(paths)}


def check_tests(base):
    tdir = os.path.join(base, "tests")
    n = len(glob.glob(os.path.join(tdir, "test_*.py")))
    has_runner = os.path.isfile(os.path.join(tdir, "run_tests.py"))
    return {"id": "tests", "pass": has_runner and n >= 1,
            "detail": "发现 %d 个 test_*.py%s" % (n, "" if has_runner else ",run_tests.py 缺失")}


def channel_states(env, config_path):
    """渠道已配/未配(env 存在性 + config 结构字段;只看键,不看值)。
    telegram 需 token+chat 两键;email 需 SMTP 密码 env + config 结构字段齐。"""
    ch = {}
    try:
        with open(config_path, encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict) and isinstance(raw.get("channels"), dict):
            ch = raw["channels"]
    except (OSError, ValueError):
        ch = {}
    states = {name: all(bool(env.get(k)) for k in envs) for name, envs in CHANNEL_ENVS}
    em = ch.get("email") if isinstance(ch.get("email"), dict) else {}
    states["email"] = bool(env.get(EMAIL_ENV)) and \
        all(bool(em.get(k)) for k in ("smtp_host", "from", "to"))
    return states


def check_channels(env, config_path):
    st = channel_states(env, config_path)
    detail = " ".join("%s=%s" % (n, "已配" if st[n] else "未配") for n in CHANNEL_ORDER)
    return {"id": "channels", "pass": True,        # 信息项:未配渠道不阻断 suite
            "detail": detail + "(只报渠道名与已配/未配,不打印值)"}


def check_net(timeout=NET_TIMEOUT):
    """可选网络探测:失败只警告,pass 恒 True(不影响 ready/退出码)。"""
    host = urllib.parse.urlsplit(NET_URL).netloc
    t0 = time.time()
    try:
        req = urllib.request.Request(NET_URL, method="HEAD",
                                     headers={"User-Agent": "seo-suite-doctor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            code = getattr(r, "status", None) or r.getcode()
        return {"id": "net", "pass": True,
                "detail": "HEAD %s %s(%dms)" % (host, code, int((time.time() - t0) * 1000))}
    except Exception as e:
        return {"id": "net", "pass": True,
                "detail": "HEAD %s 不可达(warn:%s——不影响 ready)" % (host, type(e).__name__)}


def run_checks(base=None, env=None, home=None,
               config_path=".seo-monitor/config.json", net=False):
    """收集全部自检项 + 凭证分层。base/env/home 可注入(测试用临时 HOME/环境)。"""
    base = BASE if base is None else base
    env = os.environ if env is None else env
    checks = [check_python(),
              check_markets(os.path.join(base, "scripts", "markets.json")),
              check_templates(base),
              check_scripts(os.path.join(base, "scripts")),
              check_tests(base),
              check_channels(env, config_path)]
    if net:
        checks.append(check_net())
    return checks, detect_tier(env=env, home=home)


# ---------- 输出 / CLI ----------

LABELS = {"python": "Python", "markets": "markets", "templates": "templates",
          "scripts": "scripts", "tests": "tests", "channels": "channels", "net": "net"}

FIX_TIPS = {
    "python": "升级到 Python ≥3.9(如 pyenv install 3.9+ 后 pyenv local 3.9.x)",
    "markets": "修复 scripts/markets.json——校验 JSON 语法,市场数须为 18(与 _meta 口径对齐)",
    "templates": "恢复 templates/ 四类子目录(audit/content/monitor/research 各 ≥1 个 .md;git checkout)",
    "scripts": "对报告点名的文件跑 python3 -m py_compile 定位语法错误并修复",
    "tests": "恢复 tests/run_tests.py 与 test_*.py 用例(self_check.py 依赖 golden 层)",
}

EPILOG = """\
凭证分层(纯本地判断,零网络,绝不读/打印凭证值):
  T0 无凭证 → 纯静态审计(site_audit/health_score 等)
  T1 PSI_API_KEY | CRUX_API_KEY 环境变量 → +PageSpeed/CrUX
  T2 ~/.config/seo-suite/gsc.json 含 credentials 键 → +GSC
  T3 另含 ga4_property_id 键 → +GA4

退出码: 0=ready / 3=需处理(channels/tier/net 不影响 ready)。"""


def build_parser():
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0], epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true",
                    help="输出 {ready, tier, checks:[{id,pass,detail}], reasons[]}")
    ap.add_argument("--fix-tips", action="store_true", dest="fix_tips",
                    help="人读模式下对每个 fail 附一条修复建议(--json 模式由 reasons 承担)")
    ap.add_argument("--net", action="store_true",
                    help="附网络可达性探测(HEAD developers.google.com,5s 超时;失败仅警告)")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    checks, tier = run_checks(net=args.net)
    hard = [c for c in checks if c["id"] in HARD_IDS and not c["pass"]]
    ready = not hard
    reasons = ["%s: %s" % (c["id"], c["detail"]) for c in hard]

    if args.json:
        print(redact(json.dumps({"ready": ready, "tier": tier, "checks": checks,
                                 "reasons": reasons}, ensure_ascii=False, indent=2)))
        return 0 if ready else 3

    for c in checks:
        print(redact("%s: %s %s" % (LABELS.get(c["id"], c["id"]), c["detail"],
                                    "✓" if c["pass"] else "✗")))
    line = "tier: T%d — capabilities: %s" % (tier["tier"], "+".join(tier["capabilities"]))
    print(redact(line + ("; missing: %s" % tier["missing"] if tier["missing"]
                         else "(全部能力已解锁)")))
    print(redact("ready: %s" % ("yes" if ready else "no")))
    if args.fix_tips:
        for c in hard:
            print(redact("fix-tip(%s): %s" % (LABELS.get(c["id"], c["id"]),
                                              FIX_TIPS.get(c["id"], "查看 detail 并修复"))))
    print("(输出 intentionally omits absolute paths and environment values)")
    return 0 if ready else 3


if __name__ == "__main__":
    sys.exit(main())
