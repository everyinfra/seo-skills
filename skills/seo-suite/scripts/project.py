#!/usr/bin/env python3
"""project.py — 项目工作区与管线编排器(R1-1/R1-2,references/overview/pipeline-completeness.md;stdlib only)。

给"链只存在于 SKILL.md 散文里、状态散落 6 处"的问题一个 project 实体:

工作区 `<slug>.seo/`(R1-2 归一):
  project.yaml   站点实体——受限 YAML 子集(顶层标量 + references 列表,照
                 oracle_check.parse_facts_yaml 风格自实现,不依赖 PyYAML):
                 site/market/type/created/history_dir + 状态收敛说明 + references
                 指回 6 处旧状态位置(**不迁移**)
  history/       按日期的快照目录 `<YYYYMMDD-HHMMSS>/`(对标 niubigeo Baseline 冻结
                 语义:每轮产物只落新目录不改写旧轮,分数趋势按目录名字典序读)

子命令:
  init          建工作区(幂等刷新:site 相同只更新 market/type,保留 created/history)
  adopt         列出 --from 目录(默认 cwd)下 6 处可迁移的散落状态——只列不迁,
                迁移由用户人工执行(R1-2:不做隐式搬家)
  run triage    一条命令到策略首答(R1-7,30 分钟口径):site_crawl(子进程,
                --max 50 + 默认 1s 礼貌限速)→ site_audit(前 5 个 2xx/3xx URL)
                → health_score → prioritize → envelope——全部子进程调既有脚本
                (编排器只编排不重实现),产物落 history/<date>/;任何一步失败
                续跑其余并汇总(triage.json 记录逐步完整命令/退出码/产物/耗时);
                末尾输出站型建议 + 该做的三件事 + 理由(envelope summary ×
                audit-rule-catalog 严重度聚合:CRITICAL>WARN>INFO,同档按受影响
                面降序取前三,简单规则)
  next          五阶段状态机(体检→优先级→修复→验证→监控):读 history/ 与修复
                工单判定当前阶段,输出下一条**精确命令行**(remediation/monitor
                的既有 CLI,直接可粘贴执行)
  status        一屏:五阶段各自最近产物 + 主分趋势(history 各轮 health.json 的
                分数序列)+ remediation 工单开/闭数(若有)

设计纪律:重活全部子进程调既有脚本,本脚本只编排不重实现;失败容错(单步失败
不终止,依赖该步的下游标 skipped 并给原因);并发安全不要求(单人工具)。

环境变量: SEO_PROJECT_SCRIPTS_DIR 覆盖被编排脚本的目录(默认本脚本所在目录;
测试打桩用。markets.json 校验恒读本脚本同目录,不受打桩影响)。

退出码: 0 正常 / 1 triage 有步骤失败或被跳过 / 2 输入或用法错。

用法: python3 project.py init --site https://example.com [--market en] [--type 站型]
       python3 project.py run triage [--dir <slug>.seo] [--max 50]
       python3 project.py next|status [--dir <slug>.seo]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from datetime import datetime, timezone

SCHEMA_VERSION = 1
PY = sys.executable or "python3"
HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.abspath(os.environ.get("SEO_PROJECT_SCRIPTS_DIR") or HERE)

TRIAGE_MAX_PAGES = 50        # R1-7:首答轮爬取预算(大站建议后续另跑全量 site_crawl)
TRIAGE_AUDIT_URLS = 5        # 体检样本:爬取发现序前 5 个 2xx/3xx URL
TRIAGE_DELAY_S = "1.0"       # site_crawl 默认礼貌限速,显式传出使 triage.json 自解释
STEP_TIMEOUT_S = {"crawl": 900, "audit": 600, "health": 120, "prioritize": 120, "envelope": 180}
STEP_ORDER = ("crawl", "audit", "health", "prioritize", "envelope")
# 各步"成功的退出码":1 的语义是 site_crawl=存在错误页 / site_audit=存在 CRITICAL /
# health_score=主分 Weak 档——发现问题的**成功运行**;2(输入/用法错)、3(全部起点
# 失败)或超时才算编排步骤失败。
OK_RC = {"crawl": (0, 1), "audit": (0, 1), "health": (0, 1), "prioritize": (0,), "envelope": (0,)}

SEV_ORDER = {"CRITICAL": 0, "WARN": 1, "INFO": 2}

# R1-2 状态收敛:6 处散落状态(pipeline-completeness.md §一)。init 不迁移,只在
# project.yaml references 指回;adopt 列出;监控阶段建议收敛到 <ws>/.seo-monitor/。
SCATTERED_STATE = (
    (".seo-monitor/", "monitor.py 监控工作区(SQLite+config)"),
    ("panel.json", "citation_panel.py GEO 面板"),
    ("remediations.json", "remediation.py 修复工单"),
    (".trend-state.json", "trend_watch.py 热点状态库"),
    (".intel-state.json", "intel_check.py 信源状态库"),
    ("seo-fixes/", "fix_plan.py --apply 隔离目录"),
)

# 站型建议信号(R1-4 URL 型谱的简化版,口径见 site-type-playbooks.md 各卡「识别信号」)。
# S2a B1(2026-10-21):按**路径段**精确匹配(不再子串:"/production" 不算 "/product");
# 段内以 "-" 分词的 token 也参与(如 "tiktok-api" 含 api);开发者站另认标题里的 API/SDK 词。
# 电商须有交易佐证(cart/checkout/basket 或 PLP 段 collections/category/c)才计 PDP 段——
# 判型规则原文「PLP 与 PDP 并存,cart/checkout 路径存在」;只有 /products/ 的 API/SaaS 站不算电商。
SITE_TYPE_SIGNALS = (
    ("电商(DTC)", ("products", "product", "p", "shop", "cart", "checkout", "collections", "c", "basket")),
    ("文档 / 开发者站", ("docs", "doc", "api", "apis", "reference", "guide", "guides", "documentation",
                     "changelog", "sdk", "sdks", "v1", "v2", "v3", "openapi", "quickstart")),
    ("媒体 / 新闻 / 内容站", ("blog", "news", "article", "articles", "post", "posts", "category")),
    ("SaaS / 软件营销站", ("pricing", "features", "demo", "signup", "trial", "solutions", "compare",
                        "vs", "alternatives", "integrations", "templates", "customers")),
    ("本地服务", ("location", "locations", "near-me", "contact-us")),
    ("Marketplace / 平台型", ("listings", "sell", "users")),
)
ECOM_PROOF = ("cart", "checkout", "basket", "collections", "c", "category")
TOKEN_SIGNALS = {"文档 / 开发者站": ("api", "sdk", "docs")}   # 段内 "-" 分词 token
TITLE_SIGNALS = {"文档 / 开发者站": re.compile(r"\b(?:API|SDK|API key|API reference)\b")}
SITE_TYPE_AMBIGUOUS = 0.30   # 首位占比低于此 → 模糊,列前二(R1-4"模糊列前二确认"口径)

STAGES = ("体检", "优先级", "修复", "验证", "监控")   # 五阶段状态机
OPEN_PRE = ("proposed", "accepted", "in_progress")     # 工单未完成(修复阶段口径)
CLOSED = ("verified", "wontfix")                       # 工单已关闭


class UsageError(Exception):
    """输入/用法错(退出码 2)。"""


def die(msg):
    raise UsageError(msg)


def now_utc_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def script_path(name):
    return os.path.join(SCRIPTS_DIR, name)


def me_path():
    return os.path.abspath(__file__)


# ---------------------------------------------------------------------------
# 受限 YAML 子集(照 oracle_check 风格自实现;顶层标量 + 单层字符串列表)
# ---------------------------------------------------------------------------

def _unquote(v):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_project_yaml(path):
    """解析 project.yaml 受限子集 → dict。顶层 `key: value` 标量(值取首个冒号后
    整段,# 注释行忽略,引号剥离);空值键开列表,后续缩进 `- item` 续行入列。"""
    data, cur_list = {}, None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            m_item = re.match(r"^\s+-\s+(.+?)\s*$", line)
            m_kv = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            if m_item and cur_list is not None:
                cur_list.append(_unquote(m_item.group(1).strip()))
            elif m_kv:
                k, v = m_kv.group(1), m_kv.group(2).strip()
                if v == "":
                    cur_list = []
                    data[k] = cur_list
                else:
                    cur_list = None
                    data[k] = _unquote(v)
    return data


def write_project_yaml(path, site, market, site_type, created):
    """写 project.yaml(受限子集,人可读注释带状态收敛说明)。"""
    L = ["# seo-suite 项目工作区(project.py;受限 YAML 子集:顶层标量 + references 列表)",
         "site: %s" % site,
         "market: %s" % market,
         "type: %s" % (site_type or ""),
         "created: %s" % created,
         "history_dir: history",
         "# 状态收敛说明(R1-2):本工作区收敛 project 实体与 history/ 快照;下列既有",
         "# 散落状态不自动迁移,references 指回旧位置;`project.py adopt` 列可迁移文件。",
         "references:"]
    for name, _desc in SCATTERED_STATE:
        L.append("  - %s" % name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def known_markets():
    """markets.json 市场代码集(恒读本脚本同目录,不受 SEO_PROJECT_SCRIPTS_DIR 影响);
    文件缺失 → None(跳过校验)。"""
    path = os.path.join(HERE, "markets.json")
    try:
        with open(path, encoding="utf-8") as f:
            return set(json.load(f).get("markets", {}))
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------------------
# 工作区
# ---------------------------------------------------------------------------

def site_slug(site):
    """站点 URL → (slug, 规范 site)。host 小写去 www./尾点,非 [a-z0-9] 折叠为 '-'。"""
    raw = site if "://" in site else "https://" + site
    p = urllib.parse.urlsplit(raw)
    host = (p.hostname or "").lower().strip(".")
    if not host or "." not in host or not re.match(r"^[a-z0-9.-]+$", host):
        raise UsageError("无法从 --site 解析出公网主机: %s" % site)
    if host.startswith("www."):
        host = host[4:]
    slug = re.sub(r"[^a-z0-9]+", "-", host).strip("-")
    if not slug:
        raise UsageError("slug 为空: %s" % site)
    return slug, "%s://%s" % (p.scheme or "https", host)


def find_workspace(explicit):
    """定位工作区:--dir 显式 > cwd 下唯一 *.seo/(含 project.yaml);无 → 2,多个 → 2。"""
    if explicit:
        ws = os.path.abspath(explicit)
        if not os.path.isfile(os.path.join(ws, "project.yaml")):
            die("--dir 指定的目录缺 project.yaml(不是 project 工作区): %s" % ws)
        return ws
    cands = sorted(d for d in glob.glob("*.seo")
                   if os.path.isdir(d) and os.path.isfile(os.path.join(d, "project.yaml")))
    if not cands:
        die("当前目录未发现 *.seo/ 工作区;先运行: python3 %s init --site <URL>"
            % os.path.relpath(me_path(), os.getcwd() if os.getcwd() != HERE else "."))
    if len(cands) > 1:
        die("发现多个工作区(%s);请用 --dir 指定其一" % ", ".join(cands))
    return os.path.abspath(cands[0])


def load_project(ws):
    data = parse_project_yaml(os.path.join(ws, "project.yaml"))
    if not data.get("site"):
        die("project.yaml 缺 site: %s" % ws)
    return data


def history_runs(ws):
    """history/ 快照目录列表(名字典典序 = 时间序;YYYYMMDD-HHMMSS 定长)。"""
    root = os.path.join(ws, "history")
    if not os.path.isdir(root):
        return []
    return sorted(os.path.join(root, d) for d in os.listdir(root)
                  if os.path.isdir(os.path.join(root, d)))


def latest_artifact(ws, rel):
    """最新一个含 <rel> 产物的 history 轮 → 绝对路径;无 → None。"""
    for run in reversed(history_runs(ws)):
        p = os.path.join(run, rel)
        if os.path.isfile(p):
            return p
    return None


def new_history_dir(ws):
    root = os.path.join(ws, "history")
    os.makedirs(root, exist_ok=True)
    name = datetime.now().strftime("%Y%m%d-%H%M%S")
    d = os.path.join(root, name)
    n = 2
    while os.path.exists(d):                    # 同秒重复 triage 不覆盖旧轮
        d = os.path.join(root, "%s-%d" % (name, n))
        n += 1
    os.makedirs(d)
    return d


def load_json_tolerant(path):
    """容忍前部人读文本行(site_audit --json 的 stdout 形态):整读失败则从每个
    '{' 起点 raw_decode(health_score.load_audit 同款口径,读借鉴不 import)。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        return json.loads(text)
    except ValueError:
        pass
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                return dec.raw_decode(text[i:])[0]
            except ValueError:
                continue
    raise UsageError("JSON 不可解析: %s" % path)


# ---------------------------------------------------------------------------
# init / adopt
# ---------------------------------------------------------------------------

def cmd_init(ns):
    slug, site = site_slug(ns.site)
    mk = known_markets()
    if mk is not None and ns.market not in mk:
        die("未知市场 %s;可用: %s" % (ns.market, ", ".join(sorted(mk))))
    ws = os.path.abspath(ns.dir or ("%s.seo" % slug))
    ypath = os.path.join(ws, "project.yaml")
    created = now_utc_iso()
    if os.path.isfile(ypath):                   # 幂等刷新:同 site 保留 created/history
        old = parse_project_yaml(ypath)
        if old.get("site") != site:
            die("工作区已存在且 site 不同(%s ≠ %s);换 --dir 或先迁移旧工作区"
                % (old.get("site"), site))
        created = old.get("created") or created
    os.makedirs(os.path.join(ws, "history"), exist_ok=True)
    write_project_yaml(ypath, site, ns.market, ns.type, created)
    summary = {"workspace": ws, "project_yaml": ypath, "site": site, "market": ns.market,
               "type": ns.type or "", "created": created, "history_dir": os.path.join(ws, "history"),
               "migrated": False,
               "note": "不迁移既有散落状态;references 指回 6 处旧位置,可运行 adopt 列出可迁移文件"}
    if ns.json:
        print(json.dumps(summary, ensure_ascii=False, indent=1))
    else:
        print("## init: %s" % site)
        print("- 工作区: %s(project.yaml + history/)" % ws)
        print("- market=%s type=%s created=%s" % (ns.market, ns.type or "-", created))
        print("- 状态收敛: 不迁移散落状态;%d 处旧位置记于 references;`adopt` 可列可迁移文件"
              % len(SCATTERED_STATE))
    return 0


def cmd_adopt(ns):
    """列出散落状态(只列不迁,R1-2:迁移人工执行,避免隐式搬家双写)。"""
    base = os.path.abspath(ns.from_dir)
    found = []
    for name, desc in SCATTERED_STATE:
        p = os.path.join(base, name.rstrip("/"))
        if os.path.isdir(p):
            n = sum(1 for _ in os.scandir(p))
            found.append({"name": name, "kind": "目录(%d 项)" % n, "desc": desc, "path": p})
        elif os.path.isfile(p):
            found.append({"name": name, "kind": "文件(%dB)" % os.path.getsize(p),
                          "desc": desc, "path": p})
    if ns.json:
        print(json.dumps({"base": base, "found": found, "migrated": False},
                         ensure_ascii=False, indent=1))
        return 0
    print("## adopt: %s 下的散落状态(只列不迁,迁移人工执行)" % base)
    if not found:
        print("- 未发现 6 处已知散落状态;无需迁移")
        return 0
    for f in found:
        print("- %-18s %-12s %s" % (f["name"], f["kind"], f["desc"]))
    print("提示: 确认后人工迁移(示例: cp -r <上面某项> <工作区>/),迁移完删除旧址避免双写;")
    print("      监控阶段的新状态建议直接收敛到 <工作区>/.seo-monitor/(project.py next 会给命令)")
    return 0


# ---------------------------------------------------------------------------
# run triage
# ---------------------------------------------------------------------------

def run_step(name, cmd, ok_rc=(0,), timeout=120, stdout_to=None):
    """子进程跑一步既有脚本;失败不抛(容错续跑),结果与错误尾行记入 rec。"""
    rec = {"name": name, "cmd": cmd, "rc": None, "ok": False, "skipped": None,
           "artifact": stdout_to, "error": None, "duration_s": 0.0}
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        rec["error"] = "超时(>%ss)被终止" % timeout
        return rec
    rec["duration_s"] = round(time.monotonic() - t0, 2)
    rec["rc"] = p.returncode
    if stdout_to and p.stdout:
        with open(stdout_to, "w", encoding="utf-8") as f:
            f.write(p.stdout)
    if p.returncode not in ok_rc:
        tail = [ln for ln in (p.stderr or p.stdout or "").strip().splitlines() if ln.strip()][-3:]
        rec["error"] = (" | ".join(tail)[:400]) or ("退出码 %s(无输出)" % p.returncode)
        for ln in tail:
            sys.stderr.write("[triage:%s] %s\n" % (name, ln))
    rec["ok"] = p.returncode in ok_rc
    return rec


def pick_audit_urls(crawl_json, site, n=TRIAGE_AUDIT_URLS):
    """体检样本:爬取发现序前 n 个 2xx/3xx 页(与 site_crawl --urls-out 同款口径——
    4xx/传输失败页喂 site_audit 只会再失败一次);无 crawl 产物时退回站点根。"""
    if crawl_json and os.path.isfile(crawl_json):
        try:
            pages = (load_json_tolerant(crawl_json) or {}).get("pages") or []
        except UsageError:
            pages = []
        urls = [p["url"] for p in pages if isinstance(p, dict) and p.get("url")
                and p.get("status") is not None and p["status"] < 400]
        if urls:
            return urls[:n]
    return [site]


def _segments(url):
    path = urllib.parse.urlparse(url).path if "://" in url else url.split("?")[0]
    return [seg.lower() for seg in path.split("/") if seg]


def _page_hits(name, sigs, segs, title, ecom_ok):
    if name == "电商(DTC)" and not ecom_ok:
        return False
    if any(seg in sigs for seg in segs):
        return True
    toks = TOKEN_SIGNALS.get(name)
    if toks and any(t in toks for seg in segs for t in seg.split("-")):
        return True
    rx = TITLE_SIGNALS.get(name)
    return bool(rx and title and rx.search(title))


def suggest_site_type(crawl, declared=None):
    """站型建议(URL 型谱简化版):路径段命中计数 → 首位占比;占比低于阈值或
    无信号 → 模糊/未识别,列前二请用户确认(R1-4:模糊列前二)。
    S2a B1:自报站型优先——有自报时 suggested=自报值,URL 型谱只作参考信号写进 note,
    不给出与自报相反的建议。"""
    pages = [p for p in ((crawl or {}).get("pages") or []) if isinstance(p, dict)]
    rows = [(_segments(str(p.get("url") or "")), str(p.get("title") or "")) for p in pages]
    total = len(rows) or 1
    all_segs = {seg for segs, _ in rows for seg in segs}
    ecom_ok = bool(all_segs & set(ECOM_PROOF))
    scores = []
    for name, sigs in SITE_TYPE_SIGNALS:
        n = sum(1 for segs, title in rows if _page_hits(name, sigs, segs, title, ecom_ok))
        if n:
            scores.append((n, name))
    scores.sort(key=lambda t: (-t[0], t[1]))
    if declared:
        cands = [declared]
        if scores:
            share = scores[0][0] / total
            sig = "URL 型谱首位 %s 占比 %.0f%%(%d/%d 页,仅作参考)" % (
                scores[0][1], share * 100, scores[0][0], total)
            if scores[0][1] != declared:
                cands.append(scores[0][1])
        else:
            share, sig = 0.0, "URL 型谱无命中"
        return {"suggested": declared, "share": round(share, 3), "candidates": cands,
                "note": "自报站型: %s(以自报为准);%s" % (declared, sig)}
    if not scores:
        return {"suggested": None, "share": 0.0, "candidates": [],
                "note": "URL 型谱无命中——请 init --type 自报站型(8 张站型卡见 site-type-playbooks.md)"}
    share = scores[0][0] / total
    cands = [scores[0][1]]
    note = "信号占比 %.0f%%(%d/%d 页)" % (share * 100, scores[0][0], total)
    if share < SITE_TYPE_AMBIGUOUS:
        if len(scores) > 1:
            cands.append(scores[1][1])
        note = "模糊(首位占比 %.0f%% < %.0f%%),列前二请确认;信号: %s" % (
            share * 100, SITE_TYPE_AMBIGUOUS * 100, note)
    return {"suggested": cands[0], "share": round(share, 3), "candidates": cands, "note": note}


def top_actions(envelope_path, audit_path, n=3):
    """该做的三件事 + 理由:envelope findings(优先,自带 recommendation 文案)
    → audit-rule-catalog 严重度聚合兜底(CRITICAL>WARN>INFO,同档受影响面降序)。"""
    if envelope_path and os.path.isfile(envelope_path):
        env = load_json_tolerant(envelope_path)
        flat = []
        for cat in env.get("categories") or []:
            if not isinstance(cat, dict):
                continue
            for f in cat.get("findings") or []:
                if not isinstance(f, dict):
                    continue
                sev = f.get("severity") if f.get("severity") in SEV_ORDER else "INFO"
                flat.append({
                    "rule_id": str(f.get("rule_id") or f.get("title") or "?"),
                    "title": str(f.get("title") or f.get("rule_id") or "?"),
                    "severity": sev,
                    "affected": int(f.get("affected") or len(f.get("affected_urls") or []) or 0),
                    "category": str(cat.get("name") or "-"),
                    "reason": str(f.get("recommendation") or f.get("description") or "").strip(),
                })
        flat.sort(key=lambda d: (SEV_ORDER[d["severity"]], -d["affected"], d["rule_id"]))
        return flat[:n], "envelope summary"
    if audit_path and os.path.isfile(audit_path):
        audit = load_json_tolerant(audit_path)
        agg = {}
        for url, rec in (audit.get("results") or {}).items():
            if not isinstance(rec, dict):
                continue
            for f in rec.get("findings") or []:
                key = (f.get("severity") if f.get("severity") in SEV_ORDER else "INFO",
                       str(f.get("area") or "?"))
                agg.setdefault(key, set()).add(url)
        flat = [{"rule_id": a, "title": a, "severity": s, "affected": len(us),
                 "category": "-", "reason": "audit-rule-catalog 严重度聚合(envelope 未产出)"}
                for (s, a), us in agg.items()]
        flat.sort(key=lambda d: (SEV_ORDER[d["severity"]], -d["affected"], d["rule_id"]))
        return flat[:n], "audit 严重度聚合(envelope 未产出)"
    return [], "无(审计链未产出结果)"


def cmd_run_triage(ns):
    if ns.max <= 0:
        die("--max 必须为正整数")
    ws = find_workspace(ns.dir)
    proj = load_project(ws)
    site = proj["site"]
    market = proj.get("market") or "en"
    hist = new_history_dir(ws)

    crawl_json = os.path.join(hist, "crawl.json")
    urls_txt = os.path.join(hist, "urls.txt")
    audit_json = os.path.join(hist, "audit.json")
    health_json = os.path.join(hist, "health.json")
    prio_json = os.path.join(hist, "priority.json")
    env_dir = os.path.join(hist, "envelope")
    steps = []
    ok_so_far = {}

    def step(name, cmd, stdout_to=None, after=()):
        if any(not ok_so_far.get(up, True) for up in after):
            rec = {"name": name, "cmd": cmd, "rc": None, "ok": False,
                   "skipped": "上游未成功: %s" % ", ".join(after), "artifact": stdout_to,
                   "error": None, "duration_s": 0.0}
            steps.append(rec)
            ok_so_far[name] = False                # 跳过的步同样阻断其下游
            return rec
        rec = run_step(name, cmd, ok_rc=OK_RC[name], timeout=STEP_TIMEOUT_S[name],
                       stdout_to=stdout_to)
        steps.append(rec)
        ok_so_far[name] = rec["ok"]
        return rec

    step("crawl", [PY, script_path("site_crawl.py"), site,
                   "--max", str(ns.max), "--delay", TRIAGE_DELAY_S,
                   "--out", crawl_json, "--urls-out", urls_txt])
    audit_urls = pick_audit_urls(crawl_json if ok_so_far.get("crawl") else None, site)
    step("audit", [PY, script_path("site_audit.py"), *audit_urls,
                   "--market", market, "--json"], stdout_to=audit_json, after=("crawl",))
    r_health = step("health", [PY, script_path("health_score.py"),
                               "--input", audit_json, "--json"],
                    stdout_to=health_json, after=("audit",))
    r_prio = step("prioritize", [PY, script_path("prioritize.py"),
                                 "--audit", audit_json, "--json"],
                  stdout_to=prio_json, after=("audit",))
    env_cmd = [PY, script_path("envelope.py"), "--audit", audit_json, "--out-dir", env_dir]
    if r_health["ok"]:                          # 缺输入的下游照跑(envelope 容忍缺源)
        env_cmd += ["--health", health_json]
    if r_prio["ok"]:
        env_cmd += ["--priority", prio_json]
    step("envelope", env_cmd, after=("audit",))

    crawl = None
    if ok_so_far.get("crawl") and os.path.isfile(crawl_json):
        try:
            crawl = load_json_tolerant(crawl_json)
        except UsageError:
            crawl = None
    site_type = suggest_site_type(crawl, proj.get("type") or None)
    # 只消费成功步骤的产物:失败步可能已写半截文件(envelope 逐类别先落盘的契约),
    # 半截结果不进首答判定
    env_artifact = (os.path.join(env_dir, "audit-data.json")
                    if ok_so_far.get("envelope") else None)
    audit_artifact = audit_json if ok_so_far.get("audit") else None
    actions, basis = top_actions(env_artifact, audit_artifact)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now_utc_iso(),
        "site": site, "market": market, "run_dir": hist,
        "steps": steps,
        "verdict": {"site_type": site_type, "top_actions": actions, "basis": basis,
                    "recheck": "python3 %s run triage --dir %s" % (me_path(), ws)},
    }
    with open(os.path.join(hist, "triage.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    n_ok = sum(1 for s in steps if s["ok"])
    if ns.json:
        print(json.dumps(summary, ensure_ascii=False, indent=1))
    else:
        print("## triage: %s → %s(%d/%d 步成功)" % (site, os.path.relpath(hist, ws),
                                                 n_ok, len(steps)))
        for s in steps:
            mark = "✓" if s["ok"] else ("⊘" if s["skipped"] else "✗")
            info = s["skipped"] or ("rc=%s %.1fs" % (s["rc"], s["duration_s"])
                                    + (" %s" % os.path.basename(s["artifact"])
                                       if s.get("artifact") else ""))
            if s["error"]:
                info += " — %s" % s["error"]
            print("  %-10s %s %s" % (s["name"], mark, info))
        st = site_type
        if st["suggested"]:
            print("站型建议: %s —— %s" % (st["suggested"], st["note"]))
        else:
            print("站型建议: 未识别 —— %s" % st["note"])
        print("该做的三件事(依据 %s;严重度序→受影响面序):" % basis)
        if actions:
            for i, a in enumerate(actions, 1):
                why = a["reason"] or "见 envelope REPORT.md"
                print("  %d. [%s] %s(类别 %s,影响 %d 页)—— %s"
                      % (i, a["severity"], a["title"], a["category"], a["affected"], why))
        else:
            print("  (审计链未产出结果;先看上方失败步骤)")
        print("验证方式: 修复后重跑 `%s run triage --dir %s`," % (me_path(), ws))
        print("           再用 remediation.py verify 对照两轮 audit 自动核销工单")
    return 0 if n_ok == len(steps) else 1


# ---------------------------------------------------------------------------
# next(五阶段状态机)
# ---------------------------------------------------------------------------

def find_remediations(ws):
    """工单位置:工作区根优先(收敛方向),退回 cwd(R1-2 迁移前的旧位置)。"""
    for base in (ws, os.getcwd()):
        p = os.path.join(base, "remediations.json")
        if os.path.isfile(p):
            return os.path.abspath(p)
    return None


def stage_state(ws, proj):
    """五阶段判定(只读 history/ 与工单,不重实现任何链路):
    体检(无 envelope)→ 优先级(有 envelope 无工单)→ 修复(工单有未完成项)→
    验证(全部 implemented 待核销)→ 监控(工单全部关闭/为空)。"""
    runs = history_runs(ws)
    envelope = latest_artifact(ws, os.path.join("envelope", "audit-data.json"))
    audits = [(os.path.join(r, "audit.json"), r) for r in runs
              if os.path.isfile(os.path.join(r, "audit.json"))]
    if envelope is None:
        why = "history/ 无 envelope 快照(共 %d 轮)" % len(runs) if runs else "history/ 为空"
        return "体检", {"why": why, "ws": ws, "proj": proj}
    rem = find_remediations(ws)
    if rem is None:
        return "优先级", {"why": "envelope 已产出(%s)且尚无修复工单" % os.path.relpath(envelope, ws),
                        "envelope": envelope, "ws": ws, "proj": proj}
    items = []
    try:
        items = load_json_tolerant(rem).get("items") or []
    except UsageError:
        pass
    open_items = [it for it in items if it.get("status") in OPEN_PRE]
    implemented = [it for it in items if it.get("status") == "implemented"]
    if open_items or implemented:
        if open_items:
            first = min(open_items, key=lambda it: str(it.get("id") or ""))
            tgt = {"proposed": "accepted", "accepted": "in_progress",
                   "in_progress": "implemented"}[first.get("status")]
            return "修复", {"why": "工单 %s 项未完成(下一单: %s %s→%s)"
                            % (len(open_items), first.get("id"), first.get("status"), tgt),
                    "rem": rem, "item": first, "target": tgt, "ws": ws, "proj": proj}
        rem_m = os.path.getmtime(rem)
        newer = [p for p, _r in audits if os.path.getmtime(p) > rem_m]
        if newer:
            older = [p for p, _r in audits if os.path.getmtime(p) <= rem_m]
            env_run_audit = os.path.join(os.path.dirname(os.path.dirname(envelope)),
                                         "audit.json")
            old = older[-1] if older else (env_run_audit if os.path.isfile(env_run_audit)
                                           else newer[-1])
            return "验证", {"why": "工单全部 implemented(%d 单),已有更新体检可核销" % len(implemented),
                            "rem": rem, "old": old, "new": newer[-1], "ws": ws, "proj": proj}
        return "验证", {"why": "工单全部 implemented(%d 单),尚无更新体检" % len(implemented),
                        "rem": rem, "envelope": envelope, "ws": ws, "proj": proj}
    closed = [it for it in items if it.get("status") in CLOSED]
    why = "工单全部关闭(verified/wontfix %d 单)" % len(closed) if items else "工单为空(无需修复)"
    return "监控", {"why": why, "ws": ws, "proj": proj}


def next_command(stage, info):
    ws, proj = info["ws"], info["proj"]
    market = proj.get("market") or "en"
    if stage == "体检":
        return [PY, me_path(), "run", "triage", "--dir", ws], None
    if stage == "优先级":
        return [PY, script_path("remediation.py"), "init",
                "--envelope", info["envelope"]], None
    if stage == "修复":
        return [PY, script_path("remediation.py"), "update",
                str(info["item"].get("id") or ""), info["target"], "--file", info["rem"]], None
    if stage == "验证":
        if "new" in info:
            return ([PY, script_path("remediation.py"), "verify",
                     "--old", info["old"], "--new", info["new"], "--file", info["rem"]], None)
        hint = ("复体检产出新 audit 后: %s verify --old %s --new <新 audit> --file %s"
                % (script_path("remediation.py"),
                   latest_artifact(ws, "audit.json") or "<旧 audit>", info["rem"]))
        return [PY, me_path(), "run", "triage", "--dir", ws], hint
    mon = os.path.join(ws, ".seo-monitor")
    if not os.path.isdir(mon):
        return ([PY, script_path("monitor.py"), "init", "--site", proj["site"],
                 "--market", market, "--dir", mon], None)
    return [PY, script_path("monitor.py"), "run", "--dir", mon], None


def cmd_next(ns):
    ws = find_workspace(ns.dir)
    proj = load_project(ws)
    stage, info = stage_state(ws, proj)
    cmd, hint = next_command(stage, info)
    idx = STAGES.index(stage) + 1
    if ns.json:
        print(json.dumps({"stage": stage, "stage_index": "%d/5" % idx, "why": info["why"],
                          "command": cmd, "hint": hint}, ensure_ascii=False, indent=1))
    else:
        print("## 当前阶段: %d/5 %s" % (idx, stage))
        print("依据: %s" % info["why"])
        print("下一条命令:")
        print("  " + " ".join(cmd))
        if hint:
            print("随后: %s" % hint)
    return 0


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def cmd_status(ns):
    ws = find_workspace(ns.dir)
    proj = load_project(ws)
    runs = history_runs(ws)

    audit = latest_artifact(ws, "audit.json")
    row1 = os.path.relpath(audit, ws) if audit else "—(无体检快照)"
    n_audited = None
    if audit:
        try:
            n_audited = load_json_tolerant(audit).get("audited")
        except UsageError:
            pass
    if n_audited is not None:
        row1 += "(%s URL)" % n_audited

    envelope = latest_artifact(ws, os.path.join("envelope", "audit-data.json"))
    row2 = os.path.relpath(envelope, ws) if envelope else "—(无 envelope;run triage 产出)"

    row3 = row4 = "—(无工单)"
    rem = find_remediations(ws)
    items = []
    if rem:
        try:
            items = load_json_tolerant(rem).get("items") or []
        except UsageError:
            items = []
        n_open = sum(1 for it in items if it.get("status") in OPEN_PRE)
        n_closed = sum(1 for it in items if it.get("status") in CLOSED)
        row3 = "开 %d / 闭 %d(%s)" % (n_open, n_closed, os.path.relpath(rem, ws))
        n_impl = sum(1 for it in items if it.get("status") == "implemented")
        n_ver = sum(1 for it in items if it.get("status") == "verified")
        closed_ts = [str(it.get("closed") or "") for it in items if it.get("closed")]
        row4 = "待核销 %d / 已核销 %d" % (n_impl, n_ver)
        if closed_ts:
            row4 += "(最近 closed %s)" % max(closed_ts)

    mon = os.path.join(ws, ".seo-monitor")
    row5 = "已建立(.seo-monitor/)" if os.path.isdir(mon) else "—(.seo-monitor/ 未建立;见 next)"

    trend = []
    for r in runs:
        hp = os.path.join(r, "health.json")
        if os.path.isfile(hp):
            try:
                h = load_json_tolerant(hp)
                trend.append("%s(%s)" % (h.get("main_score"), h.get("band")))
            except UsageError:
                pass
    row_trend = " → ".join(trend) if trend else "—(无健康分;run triage 产出)"

    if ns.json:
        print(json.dumps({"site": proj.get("site"), "market": proj.get("market"),
                          "type": proj.get("type"), "created": proj.get("created"),
                          "workspace": ws, "history_runs": len(runs),
                          "stages": {"体检": row1, "优先级": row2, "修复": row3,
                                     "验证": row4, "监控": row5},
                          "score_trend": trend}, ensure_ascii=False, indent=1))
    else:
        print("## project: %s(%s @ %s;创建 %s;history %d 轮)"
              % (proj.get("site"), proj.get("type") or "站型未报", proj.get("market") or "-",
                 proj.get("created") or "-", len(runs)))
        print("- ① 体检     %s" % row1)
        print("- ② 优先级   %s" % row2)
        print("- ③ 修复     %s" % row3)
        print("- ④ 验证     %s" % row4)
        print("- ⑤ 监控     %s" % row5)
        print("- 主分趋势(history 各轮): %s" % row_trend)
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

USAGE_EPILOG = """\
示例:
  python3 project.py init --site https://example.com --market en --type "SaaS / 软件营销站"
  python3 project.py adopt                     # 列 cwd 下 6 处可迁移散落状态(只列不迁)
  python3 project.py run triage                # 体检→优先级一条链,产物落 history/<date>/
  python3 project.py next                      # 五阶段状态机 → 下一条精确命令行
  python3 project.py status                    # 一屏:五阶段产物+主分趋势+工单开闭

工作区 <slug>.seo/:project.yaml(受限 YAML 子集)+ history/<YYYYMMDD-HHMMSS>/ 快照。
编排纪律:重活全部子进程调既有脚本(site_crawl/site_audit/health_score/prioritize/
envelope/remediation/monitor),本脚本只编排不重实现;单步失败续跑其余并汇总。
退出码: 0 正常 / 1 triage 有步骤失败或被跳过 / 2 输入或用法错。\
"""


def build_parser():
    ap = argparse.ArgumentParser(
        prog="project.py",
        description="项目工作区与管线编排器(R1-1/R1-2):<slug>.seo/ 收敛 project 实体与 "
                    "history/ 快照;run triage 一条命令到策略首答;next/status 按五阶段"
                    "状态机(体检→优先级→修复→验证→监控)导航(stdlib only)",
        epilog=USAGE_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="建立/刷新 <slug>.seo/ 工作区(project.yaml+history/;幂等)")
    p.add_argument("--site", required=True, metavar="URL", help="站点 URL 或裸域名(自动补 https://)")
    p.add_argument("--market", default="en", metavar="XX", help="市场代码(markets.json 18 市场,默认 en)")
    p.add_argument("--type", default="", metavar="站型", help="站型自报(8 张站型卡名,见 site-type-playbooks.md)")
    p.add_argument("--dir", metavar="WS", help="工作区路径(默认 <slug>.seo/)")
    p.add_argument("--json", action="store_true", help="结果 JSON 打 stdout")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("adopt", help="列出散落状态文件(只列不迁;迁移人工执行)")
    p.add_argument("--from", dest="from_dir", default=".", metavar="DIR",
                   help="扫描目录(默认 cwd;查 6 处已知散落状态)")
    p.add_argument("--json", action="store_true", help="清单 JSON 打 stdout")
    p.set_defaults(func=cmd_adopt)

    p = sub.add_parser("run", help="运行管线(目前: triage 技术审计链)")
    p.add_argument("action", choices=("triage",), help="triage=体检→优先级一条链(R1-7)")
    p.add_argument("--dir", metavar="WS", help="工作区路径(默认自动发现 cwd 下唯一 *.seo/)")
    p.add_argument("--max", type=int, default=TRIAGE_MAX_PAGES, metavar="N",
                   help="爬取页数预算(默认 %d;site_audit 取前 %d 个 2xx/3xx URL)"
                        % (TRIAGE_MAX_PAGES, TRIAGE_AUDIT_URLS))
    p.add_argument("--json", action="store_true", help="triage.json 内容打 stdout")
    p.set_defaults(func=cmd_run_triage)

    p = sub.add_parser("next", help="五阶段状态机 → 输出下一条精确命令行")
    p.add_argument("--dir", metavar="WS", help="工作区路径(默认自动发现)")
    p.add_argument("--json", action="store_true", help="结果 JSON 打 stdout")
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("status", help="一屏:五阶段最近产物+主分趋势+工单开闭")
    p.add_argument("--dir", metavar="WS", help="工作区路径(默认自动发现)")
    p.add_argument("--json", action="store_true", help="结果 JSON 打 stdout")
    p.set_defaults(func=cmd_status)
    return ap


def main(argv=None):
    ns = build_parser().parse_args(argv)      # 用法错 argparse 自带退出码 2
    try:
        return ns.func(ns)
    except UsageError as e:
        sys.stderr.write("[project] %s\n" % e)
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        sys.exit(130)
