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
  python3 doctor.py --wizard [--want a,b,c]
                               # 数据接入清单向导(非交互):对每个分析目标列
                               # 数据源/是否已配/获取(data-onboarding.md 锚)/降级;
                               # 结尾报当前 tier 与立即可跑能力数;复用 tier 探测
                               # (零网络/只看存在性);不改 ready 判定与退出码契约
  python3 doctor.py --keys --print-env
                               # env 模板:全部支持键名+一行注释的 shell 模板(值留空,
                               # 可整段粘进 shell profile;键集=data-onboarding.md T1-T4
                               # + SEO_MONITOR_* 通知/监控组,R2-9)
  python3 doctor.py --keys --check [--json]
                               # 逐键校验已配置项(只探存在性不读值,复用 redact);
                               # keys 模式独立 exit 0,不做 ready 判定

退出码:0=ready / 3=需处理(doctor 契约;channels/tier/net 为信息项不影响 ready;
--keys 模式独立 exit 0)。
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


# ---------- 数据接入向导(--wizard;非交互清单,复用 tier 探测只看存在性) ----------
# 用户视角对应文档:references/overview/data-onboarding.md(每个条目带锚点,内链由测试守护)

ONBOARDING_DOC = "references/overview/data-onboarding.md"
WANT_CHOICES = ("seo-audit", "rank", "backlinks", "cwv", "keywords", "geo", "logs", "local")


def _p_t0(t):
    return (True, "已配(T0 即可用,零数据门槛)")


def _p_gsc(t):
    return ((True, "已配(GSC API 凭证在场)") if "gsc" in t["capabilities"]
            else (False, "未配——GSC 效果报告 CSV 导出零门槛,可先手动导出"))


def _p_gsc_partial(t):
    return ((True, "部分已配(GSC 链接报告可出部分画像)") if "gsc" in t["capabilities"]
            else (False, "未配——GSC 链接报告免费可出部分画像;全量需付费工具导出"))


def _p_cwv(t):
    ok = "psi" in t["capabilities"] or "crux" in t["capabilities"]
    return ((True, "已配(PSI/CrUX key 在场)") if ok
            else (False, "未配——PSI 网页版手动查询免费,导出 CSV 即可先跑"))


def _p_self(t):
    return (False, "自备导出文件,无凭证可探测(非 key 问题,拿到文件即可跑)")


WANT_ITEMS = {
    "seo-audit": {
        "label": "全站体检", "probe": _p_t0,
        "sources": "site_crawl+site_audit+health_score(URL 实时抓取;零数据门槛)",
        "anchor": "want-seo-audit",
        "how": "无需凭证:site_crawl --domain → site_audit → health_score 链路现即可跑",
        "fallback": "不需要降级;WAF/挑战页按 [SKIP] 拒审,不算 CRITICAL、不进分母"},
    "rank": {
        "label": "排名与点击", "probe": _p_gsc,
        "sources": "GSC(免费:CSV 导出零门槛;API 需 OAuth)",
        "anchor": "want-rank",
        "how": "Search Console → 效果(Performance)→ 导出 CSV;API 配 gsc.json(含 credentials 键)",
        "fallback": "无 GSC 时蚕食/同源判断改用 serp_overlap 抓取样,结论标 [est];monitor 不猜流量数"},
    "backlinks": {
        "label": "外链画像", "probe": _p_gsc_partial,
        "sources": "Ahrefs/Semrush 等导出(付费)或 GSC 链接报告(免费,覆盖不全)",
        "anchor": "want-backlinks",
        "how": "付费工具导 referring_domains/DR 分布/锚文本;GSC → 链接(Links)报告导出",
        "fallback": "cite_domain 未观测字段=unknown 不当 0;竞品被引用 citation_gaps 同 cell 代理标 [推断]"},
    "cwv": {
        "label": "CWV 现场数据", "probe": _p_cwv,
        "sources": "PSI / CrUX API(免费 key)",
        "anchor": "want-cwv",
        "how": "Google Cloud 控制台(凭据→API 密钥)启用 PageSpeed Insights API,export PSI_API_KEY(约 5 分钟)",
        "fallback": "无 key 用 PSI 网页版手动查再导出;traffic_funnel 缺 CWV 时 good_ux=N/A 不计入"},
    "keywords": {
        "label": "关键词搜索量", "probe": _p_self,
        "sources": "Keyword Planner(免费,需 Ads 账号)或 Ahrefs/Semrush/DataForSEO(付费)",
        "anchor": "want-keywords",
        "how": "Google Ads → 工具 → 关键字规划师导出量级;付费工具导 kws.csv(词+search_volume+position)",
        "fallback": "Never invent search volumes:forecast 对无量词不预测(缺列 N/A),不设搜索量"},
    "geo": {
        "label": "AI 可见性(GEO)", "probe": _p_t0,
        "sources": "citation_panel 人工采样(免费·零门槛)或厂商面板(付费)",
        "anchor": "want-geo",
        "how": "citation_panel init 建 prompt 面板 → 各引擎真实提问 → record 粘贴真实回答(严禁模拟)",
        "fallback": "采样 <3 次不下结论;面板 <10 prompts 只当方向;GSC AI Performance 报告可作佐证"},
    "logs": {
        "label": "日志分析(AI 到访)", "probe": _p_self,
        "sources": "server access log(自带导出)",
        "anchor": "want-logs",
        "how": "从主机/CDN(Nginx/Cloudflare/AWS)拉 access log(combined 或 JSON 行)喂 ai_referral_log",
        "fallback": "无日志则 AI 到访只能靠探针+GSC AI 报告侧写;日志口径本就是下界"},
    "local": {
        "label": "本地商家", "probe": _p_self,
        "sources": "Google Business Profile(免费,自带导出)",
        "anchor": "want-local",
        "how": "GBP 商家后台读绩效/导 CSV;网格排名用 Text Search API 采集 rank_data.csv",
        "fallback": "grid_rank 无 CSV 不可跑(不补测不外推);GBP 无导出则后台人工读数并注明口径"},
}


def parse_want(raw):
    """"a,b,c" → 去空白去重的合法枚举序列;空 → 全列;非法值 ValueError(调用方转 argparse error)。"""
    if not raw or not raw.strip():
        return list(WANT_CHOICES)
    seen, out = set(), []
    for tok in raw.split(","):
        w = tok.strip().lower()
        if w not in WANT_ITEMS:
            raise ValueError(w)
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


def wizard_report(want, env=None, home=None):
    """逐项清单:数据源/是否已配(只消费 detect_tier 能力徽章,零额外探测零读值)/
    获取(data-onboarding.md 锚)/降级一句话;附 tier 与可跑能力计数。"""
    tier = detect_tier(env=env, home=home)
    items = []
    for wid in want:
        spec = WANT_ITEMS[wid]
        configured, status = spec["probe"](tier)
        items.append({"id": wid, "label": spec["label"], "sources": spec["sources"],
                      "configured": configured, "status": status,
                      "how": spec["how"], "anchor": spec["anchor"], "doc": ONBOARDING_DOC,
                      "fallback": spec["fallback"]})
    return tier, {"want": list(want), "items": items,
                  "runnable_capabilities": len(tier["capabilities"]),
                  "items_ready": sum(1 for i in items if i["configured"]),
                  "items_total": len(items)}


def _print_wizard(wiz, tier):
    print(redact("wizard: 数据接入清单(%d 项;探测零网络,只看存在性不读值)" % wiz["items_total"]))
    for i, it in enumerate(wiz["items"], 1):
        mark = "✓" if it["configured"] else "✗"
        print(redact("[%d/%d] %s — %s" % (i, wiz["items_total"], it["id"], it["label"])))
        print(redact("  数据: %s" % it["sources"]))
        print(redact("  状态: %s %s" % (mark, it["status"])))
        print(redact("  获取: %s(%s#%s)" % (it["how"], it["doc"], it["anchor"])))
        print(redact("  降级: %s" % it["fallback"]))
    print(redact("tier: T%d — 立即可跑能力 %d 项(%s);清单就绪 %d/%d(其余按各降级路径执行)"
                 % (tier["tier"], wiz["runnable_capabilities"],
                    "+".join(tier["capabilities"]), wiz["items_ready"], wiz["items_total"])))


# ---------- keys manifest(--keys 模式;R2-9:env 模板生成+校验) ----------
# 键全集梳自 data-onboarding.md T1-T4 凭证阶梯 + SEO_MONITOR_* 通知/监控组
# (notify.py 渠道与 monitor.py 心跳的实测 env 消费者;gsc_api.py 的 GSC_SA_FILE 寻径)。
# 探测纪律与 detect_tier 同源:只看键名存在性,绝不读值;输出全过 redact。

# (env 名, tier 组, 一行注释)
KEY_MANIFEST = (
    ("PSI_API_KEY", "T1", "PageSpeed Insights API key(免费;GCP 控制台→凭据→API 密钥,约 5 分钟)"),
    ("CRUX_API_KEY", "T1", "Chrome UX Report API key(免费;与 PSI 同路径申请)"),
    ("GSC_SA_FILE", "T2", "GSC 服务账号 JSON 文件路径(gsc_api.py 寻径 --sa > --key > $GSC_SA_FILE > gsc.json)"),
    ("BING_WMT_KEY", "T4", "Bing Webmaster Tools API key(免费;bing_wmt.py 读取)"),
    ("SEO_MONITOR_SLACK_WEBHOOK", "notify", "Slack 告警 webhook(notify.py 渠道)"),
    ("SEO_MONITOR_SLACK_CONTENT_WEBHOOK", "notify", "Slack 内容类告警第二 webhook(P0-3 建议路由用)"),
    ("SEO_MONITOR_DISCORD_WEBHOOK", "notify", "Discord 告警 webhook(notify.py 渠道)"),
    ("SEO_MONITOR_TG_TOKEN", "notify", "Telegram bot token(与 SEO_MONITOR_TG_CHAT 成对)"),
    ("SEO_MONITOR_TG_CHAT", "notify", "Telegram chat id(与 SEO_MONITOR_TG_TOKEN 成对)"),
    ("SEO_MONITOR_WEBHOOK_URL", "notify", "通用 webhook,Apprise 式(jsons:// forms:// texts:// 裸 https)"),
    ("SEO_MONITOR_SMTP_PASS", "notify", "email 渠道 SMTP 密码(结构字段在 .seo-monitor/config.json)"),
    ("SEO_MONITOR_HEARTBEAT_URL", "monitor", "dead-man 心跳 URL(monitor.py 周期存活探测)"),
)

KEY_GROUP_LABELS = {
    "T1": "T1 CWV 现场数据 key(免费;data-onboarding.md 凭证阶梯)",
    "T2": "T2 GSC(CSV 导出零门槛;API 自动化走 OAuth)",
    "T4": "T4 商业/平台 API(按量计费或免费申请)",
    "notify": "SEO_MONITOR_* 通知组(notify.py 渠道;secret 只经 env 注入)",
    "monitor": "SEO_MONITOR_* 监控组(monitor.py)",
}


def keys_env_template():
    """--keys --print-env:全部支持 env 名的 shell 模板(键名+一行注释,值留空)。
    纯 # 注释与空值 export,可整段粘进 shell profile;键名与顺序由 KEY_MANIFEST 唯一决定。"""
    L = ["# seo-suite env 模板(doctor.py --keys --print-env 生成;R2-9 keys manifest)",
         "# 纪律:key 只进环境变量或 ~/.config/seo-suite/(chmod 600),永不进 git/日志/报告",
         "#(data-onboarding.md §三;doctor 全输出过 redact,只探存在性不读值)",
         ""]
    last = None
    for env_name, tier, note in KEY_MANIFEST:
        if tier != last:
            L.append("# --- %s ---" % KEY_GROUP_LABELS[tier])
            last = tier
        L.append('export %s=""  # %s' % (env_name, note))
    return "\n".join(L) + "\n"


def keys_check(env=None):
    """--keys --check:逐键存在性探测(非空即已配;绝不读值)。
    返回 [{env,tier,note,configured}](顺序同 KEY_MANIFEST)。"""
    env = os.environ if env is None else env
    return [{"env": k, "tier": tier, "note": note, "configured": bool(env.get(k))}
            for k, tier, note in KEY_MANIFEST]


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

--keys 键清单模式(R2-9):--print-env 出模板 / --check 校验;
  键全集 = T1-T4(PSI/CRUX/GSC_SA_FILE/BING_WMT_KEY)+ SEO_MONITOR_* 组。

退出码: 0=ready / 3=需处理(channels/tier/net 不影响 ready;--keys 模式独立 exit 0)。"""


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
    ap.add_argument("--wizard", action="store_true",
                    help="数据接入清单向导(非交互):逐项列 数据源/是否已配/获取(onboarding 锚)/"
                         "降级;结尾报当前 tier 与立即可跑能力数;复用 tier 探测,不改 ready 判定")
    ap.add_argument("--want", default="", metavar="a,b,c",
                    help="向导枚举过滤(须与 --wizard 同用):%s;默认全列" % "/".join(WANT_CHOICES))
    ap.add_argument("--keys", action="store_true",
                    help="env 键清单模式(R2-9):须与 --print-env 或 --check 同用;"
                         "键全集=data-onboarding.md T1-T4 + SEO_MONITOR_* 组;独立 exit 0")
    ap.add_argument("--print-env", action="store_true", dest="print_env",
                    help="须与 --keys 同用:输出全部支持 env 名+一行注释的 shell 模板(值留空)")
    ap.add_argument("--check", action="store_true",
                    help="须与 --keys 同用:校验已配置项(只探存在性,不读值;复用 redact)")
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    want = None
    if args.wizard or args.want:
        try:
            want = parse_want(args.want)
        except ValueError as bad:
            build_parser().error("--want 未知项: %s(合法: %s)" % (bad, "/".join(WANT_CHOICES)))
        if not args.wizard:
            build_parser().error("--want 需与 --wizard 同用")
    if (args.print_env or args.check) and not args.keys:
        build_parser().error("--print-env/--check 需与 --keys 同用")

    if args.keys:                                       # keys 模式:独立 exit 0,不做 ready 判定
        if args.wizard or args.want:
            build_parser().error("--keys 与 --wizard 互斥(单模式运行)")
        if args.print_env and args.check:
            build_parser().error("--keys 的 --print-env 与 --check 互斥(二选一)")
        if not args.print_env and not args.check:
            build_parser().error("--keys 需与 --print-env(env 模板)或 --check(已配校验)同用")
        if args.print_env:
            print(redact(keys_env_template()), end="")  # 键名+注释,值留空,无泄密面
            return 0
        items = keys_check()
        done = sum(1 for i in items if i["configured"])
        if args.json:
            print(redact(json.dumps({"keys": items, "configured": done,
                                     "total": len(items)},
                                    ensure_ascii=False, indent=2)))
        else:
            print(redact("keys: 已配置 %d/%d(只探存在性,不读值)" % (done, len(items))))
            for i in items:
                print(redact("  [%s] %s — %s %s" % ("✓" if i["configured"] else "✗",
                                                    i["env"], i["tier"], i["note"])))
            print("(输出 intentionally omits absolute paths and environment values)")
        return 0

    checks, tier = run_checks(net=args.net)
    hard = [c for c in checks if c["id"] in HARD_IDS and not c["pass"]]
    ready = not hard
    reasons = ["%s: %s" % (c["id"], c["detail"]) for c in hard]

    if args.wizard:                                   # 向导不改 ready 判定/退出码契约
        wtier, wiz = wizard_report(want)
        if args.json:
            print(redact(json.dumps({"ready": ready, "tier": wtier, "wizard": wiz,
                                     "reasons": reasons}, ensure_ascii=False, indent=2)))
        else:
            _print_wizard(wiz, wtier)
            print(redact("ready: %s" % ("yes" if ready else "no")))
            print("(输出 intentionally omits absolute paths and environment values)")
        return 0 if ready else 3

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
