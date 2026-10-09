#!/usr/bin/env python3
"""持续监控守护核心(stdlib-only:sqlite3+urllib,零第三方依赖)。
把一次性审计变成长期监控:日检四问 → SQLite 快照 → diff 阈值告警 → 周报。

日检四问(行业分层):
  1 可见性  关键页 site: 抽查(Bing HTML 端点;被拦=skipped 不告警,不猜)
  2 流量    .seo-monitor/gsc.csv(GSC 导出,有才查;无数据源=skipped)
  3 索引    robots.txt 哈希/误封检测 + sitemap URL 数/lastmod
  4 存活    首页+关键页状态码/时延/https 混合内容
周检叠加:标题/meta 漂移哈希、llms.txt 变更、sitemap lastmod 对比、AI 爬虫放行矩阵。

告警四级(critical/warn/info/low)+ 百分比阈值×最小样本地板 = 防疲劳;
low=自愈(上次告警本次恢复)。cooldown:critical 12h / warn 24h / info 168h。

子命令:
  init   --site URL [--market XX] [--key-pages /a,/b] [--dir .seo-monitor] [--force]
  run    [--checks daily|weekly] [--dry-run] [--budget-minutes N] [--dir D]
  diff   [--run-id N] [--prev-run-id M] [--format json|text] [--out FILE] [--dry-run] [--dir D]
  report [--days 7] [--json] [--dir D]

退出码:diff → 1=有 critical,2=有 warn(无 critical),0=无,4=用法/数据错误;
run → 0 正常,3=run 未完成(budget 耗尽/全部检查 error)。SSRF 防护:仅 http(s)+
私网拒连+TLS 恒验证。

用法:
  python3 monitor.py init --site https://example.com --market us
  python3 monitor.py run --checks daily
  python3 monitor.py diff --format text
  python3 monitor.py report --days 7
  python3 monitor.py --self-test
"""
import argparse
import hashlib
import ipaddress
import json
import os
import re
import socket
import sqlite3
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from html import unescape

UA = "Mozilla/5.0 (compatible; seo-suite-monitor/1.0; +https://example.com/bot)"
DEFAULT_DIR = ".seo-monitor"
FETCH_TIMEOUT = 15
MAX_BYTES = 2_000_000
SITEMAP_CAP = 5000          # loc→lastmod 字典上限(防大库)
SITEMAP_INDEX_CAP = 5       # sitemap index 递归层数上限

AI_CRAWLERS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot",
               "PerplexityBot", "CCBot", "Google-Extended", "Bytespider", "Meta-ExternalAgent"]
MARKET_BOTS = {"ru": ["YandexBot", "YandexAdditional"], "kr": ["Yeti"], "cn": ["Baiduspider"]}

LEVELS = ("critical", "warn", "info", "low")
COOLDOWN_HOURS = {"critical": 12, "warn": 24, "info": 168}

DEFAULT_THRESHOLDS = {
    "visibility_drop_pct": 30,     "visibility_min_sample": 3,
    "sitemap_urls_drop_pct": 15,   "sitemap_min_sample": 20,
    "gsc_clicks_drop_pct": 20,     "gsc_min_clicks": 5,
    "latency_increase_pct": 100,   "latency_min_ms": 500,
    "mixed_content_min": 3,
}

# report 用:告警码 → 修复动作与安全边界(自动=可直接执行;draft PR=人审)
PLAYBOOK = {
    "homepage_down":        ("自动安全项:回滚最近发布/检查 CDN 与源站健康", "auto"),
    "key_page_down":        ("查 URL 是否被移动→301 映射(draft PR 人审重定向表)", "draft_pr"),
    "visibility_zero":      ("按 alert-threshold-guide 排查顺序 L1→L5;先查 robots/noindex/处罚", "human"),
    "visibility_drop":      ("GSC 分层定位(query/page/device);对照 Search Status Dashboard", "human"),
    "robots_sitewide_block":("自动安全项:立即修正 robots.txt 误封(回滚该行)", "auto"),
    "sitemap_urls_drop":    ("sitemap_audit.py 复核;核实是否生成管道断裂", "human"),
    "gsc_clicks_drop":      ("五层根因协议(L1 数据→L5 外部);did_attribution.py 归因", "human"),
    "mixed_content":        ("把 http:// 子资源改 https(draft PR 批量替换)", "draft_pr"),
    "fetch_error_confirmed":("连续两次抓取失败:查本机网络→DNS→站点防火墙是否拦爬虫", "human"),
    "title_meta_drift":     ("确认变更是否有意;无意则恢复基线(draft PR)", "draft_pr"),
    "llms_txt_changed":     ("diff llms.txt 变更;llmstxt.py validate 复核", "draft_pr"),
    "llms_txt_removed":     ("确认为何被删;需要则 llmstxt.py generate 重建(draft PR)", "draft_pr"),
    "robots_changed":       ("复核 robots 变更意图;robots_posture.py 全量复查", "human"),
    "ai_posture_flip":      ("确认 AI 爬虫放行翻转是否有意(visibility/protect-ip 取向)", "human"),
    "latency_spike":        ("CWV 分档核对;查最近部署", "human"),
    "gsc_clicks_spike":     ("记录归因(营销活动/季节性/SERP 变化)", "human"),
}


class FetchError(Exception):
    pass


# ---------- 基础工具 ----------

def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()[:16]


def norm_site(url):
    url = (url or "").strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url.rstrip("/")


def registrable_domain(url):
    host = urllib.parse.urlparse(url).netloc.split("@")[-1].split(":")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    parts = [p for p in host.split(".") if p]
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host or ""


_ssrf_cache = {}


def ssrf_guard(host):
    """仅 http(s) + 拒私网/环回/链路本地;结果按 host 缓存(TLS 恒验证走默认 urlopen)。
    198.18.0.0/15(RFC2544 基准段)豁免:本机 fake-IP 代理(Surge/Clash 等)会把一切域名
    解析到该段,实际连接经代理出网,TLS 验证仍生效;设 SEO_MONITOR_STRICT_SSRF=1 恢复全拒。"""
    if not host:
        raise FetchError("empty host")
    if host in _ssrf_cache:
        return
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError as e:
        raise FetchError("DNS 解析失败 %s: %s" % (host, e))
    strict = bool(os.environ.get("SEO_MONITOR_STRICT_SSRF"))
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if ip in ipaddress.ip_network("198.18.0.0/15"):
            if not strict:
                continue
            raise FetchError("SSRF guard: 非公网地址 %s(strict 模式拒 fake-IP 段)" % ip)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise FetchError("SSRF guard: 非公网地址 %s" % ip)
    _ssrf_cache[host] = True


def http_get(url, timeout=FETCH_TIMEOUT):
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        raise FetchError("仅允许 http(s): %s" % url)
    ssrf_guard(p.hostname)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xml,*/*"})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(MAX_BYTES)
            return {"status": r.status, "final_url": r.geturl(), "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
                    "body": body.decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        body = e.read(MAX_BYTES) if e.fp else b""
        return {"status": e.code, "final_url": url, "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
                "body": body.decode("utf-8", "replace")}
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise FetchError("抓取失败 %s: %s" % (url, e))


def pct_drop(prev_v, curr_v):
    """返回下降比例(0~1);prev 无/为 0 → None(不猜)。"""
    if prev_v is None or curr_v is None or prev_v <= 0:
        return None
    return (prev_v - curr_v) / prev_v


# ---------- 存储层 ----------

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT, status TEXT,
  checks_run TEXT, budget_used_sec REAL, summary TEXT);
CREATE TABLE IF NOT EXISTS snapshots(
  run_id INTEGER, ts TEXT, "check" TEXT, key TEXT, value TEXT, hash TEXT);
CREATE TABLE IF NOT EXISTS alerts(
  id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER, ts TEXT, level TEXT,
  code TEXT, key TEXT, message TEXT, details TEXT, suppressed INTEGER DEFAULT 0,
  resolved INTEGER DEFAULT 0, resolved_run INTEGER);
CREATE INDEX IF NOT EXISTS idx_snap_run ON snapshots(run_id);
CREATE INDEX IF NOT EXISTS idx_alert_fp ON alerts(code, key, resolved);
"""


def open_db(mdir):
    os.makedirs(mdir, exist_ok=True)
    conn = sqlite3.connect(os.path.join(mdir, "monitor.db"))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def load_config(mdir):
    path = os.path.join(mdir, "config.json")
    if not os.path.exists(path):
        raise SystemExit("错误: %s 不存在,先跑 init" % path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_config(mdir, cfg):
    with open(os.path.join(mdir, "config.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ---------- init ----------

def cmd_init(args):
    mdir = args.dir
    cfg_path = os.path.join(mdir, "config.json")
    if os.path.exists(cfg_path) and not args.force:
        print("错误: %s 已存在(用 --force 重建,会保留 monitor.db 之外的文件覆盖)"
              % cfg_path, file=sys.stderr)
        return 1
    site = norm_site(args.site)
    key_pages = [p.strip() for p in (args.key_pages or "/").split(",") if p.strip()]
    cfg = {
        "site": site,
        "market": (args.market or "").lower() or None,
        "key_pages": key_pages,
        "created": datetime.now().isoformat(timespec="seconds"),
        "budget_minutes": 5,
        "cooldown_hours": dict(COOLDOWN_HOURS),
        "thresholds": dict(DEFAULT_THRESHOLDS),
        "channels": {
            "slack":    {"webhook_url": "", "env": "SEO_MONITOR_SLACK_WEBHOOK"},
            "discord":  {"webhook_url": "", "env": "SEO_MONITOR_DISCORD_WEBHOOK"},
            "telegram": {"bot_token": "", "chat_id": "",
                         "env_token": "SEO_MONITOR_TG_TOKEN", "env_chat": "SEO_MONITOR_TG_CHAT"},
            "email":    {"smtp_host": "", "smtp_port": 465, "use_ssl": True, "username": "",
                         "env_pass": "SEO_MONITOR_SMTP_PASS", "from": "", "to": []},
        },
        "notes": [
            "webhook/secrets 留空时 notify.py 会读 channels.*.env 指定的环境变量",
            "GSC 流量检查:每次 run 前把 GSC 导出放到 " + os.path.join(mdir, "gsc.csv") +
            "(列含 Query,Clicks,Impressions);没有该文件则跳过流量问",
            "阈值是经验起点,按 alert-threshold-guide.md 用本站基线校准",
        ],
    }
    os.makedirs(mdir, exist_ok=True)
    os.makedirs(os.path.join(mdir, "runs"), exist_ok=True)
    conn = open_db(mdir)
    conn.close()
    save_config(mdir, cfg)
    print("监控目录已建立: %s/" % mdir)
    print("  monitor.db   SQLite(runs/snapshots/alerts)")
    print("  config.json 站点=%s 市场=%s 关键页=%s" % (site, cfg["market"] or "-", ",".join(key_pages)))
    print("  runs/        每次 run 的 JSON 快照")
    print("下一步: python3 %s run --checks daily(先建基线,再部署 cron)"
          % os.path.basename(sys.argv[0]))
    return 0


# ---------- 检查实现(每项返回 {check, state, metrics, notes}) ----------

def extract_head(html):
    def one(pattern):
        m = re.search(pattern, html, re.I | re.S)
        return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", m.group(1)))).strip() if m else ""
    title = one(r"<title[^>]*>(.*?)</title>")
    meta = one(r'<meta[^>]+name=["\']description["\'][^>]*content=["\'](.*?)["\']') or \
           one(r'<meta[^>]+content=["\'](.*?)["\'][^>]*name=["\']description["\']')
    canonical = ""
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\'](.*?)["\']', html, re.I)
    if m:
        canonical = m.group(1)
    return title, meta, canonical


def mixed_content_count(url, html):
    if urllib.parse.urlparse(url).scheme != "https":
        return None  # 仅 https 站才检查
    hits = re.findall(r'(?:src|srcset)\s*=\s*["\']http://[^"\']+', html, re.I)
    return len(hits)


def check_page(url):
    """首页/关键页通用:状态码/时延/title/混合内容。"""
    out = {"check": "page", "state": "ok", "metrics": {}, "notes": []}
    try:
        r = http_get(url)
    except FetchError as e:
        out["state"] = "error"
        out["metrics"] = {"error": str(e)}
        out["notes"].append("网络层失败≠站点宕机:单次记 info,连续两次才升 warn")
        return out
    title, meta, canonical = extract_head(r["body"])
    m = {"status": r["status"], "latency_ms": r["elapsed_ms"], "title": title,
         "meta_desc": meta, "canonical": canonical, "final_url": r["final_url"]}
    mc = mixed_content_count(url, r["body"])
    if mc is not None:
        m["mixed_content"] = mc
        if mc:
            out["notes"].append("混合内容: %d 个 http:// 子资源" % mc)
    out["metrics"] = m
    if r["status"] >= 400:
        out["state"] = "http_error"
    return out


def check_robots(site, market=None):
    out = {"check": "robots", "state": "ok", "metrics": {}, "notes": []}
    try:
        r = http_get(site + "/robots.txt")
    except FetchError as e:
        out["state"] = "error"
        out["metrics"] = {"error": str(e)}
        return out
    if r["status"] >= 400:
        out["state"] = "absent"
        out["metrics"] = {"status": r["status"], "hash": sha256_text("")}
        out["notes"].append("无 robots.txt(=默认全放行,合法;仅记录)")
        return out
    txt = r["body"]
    groups, order = {}, []
    cur = None
    for line in txt.splitlines():
        s = line.split("#")[0].strip()
        if not s:
            continue
        k, _, v = s.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            cur = v or "*"
            groups.setdefault(cur, {"allow": [], "disallow": []})
            order.append(cur)
        elif k in ("allow", "disallow") and cur:
            groups[cur][k].append(v)
    star = groups.get("*", {"allow": [], "disallow": []})
    sitewide = any(d in ("", "/") for d in star["disallow"])
    sitemaps = [v for line in txt.splitlines()
                if line.split(":")[0].strip().lower() == "sitemap"
                for v in [line.split(":", 1)[1].strip()] if v]
    posture = ai_posture(groups)
    for bot in MARKET_BOTS.get((market or "").lower(), []):
        posture[bot] = ai_posture({bot: groups[bot]})[bot] if bot in groups else "no_rule(=放行)"
    out["metrics"] = {"status": r["status"], "hash": sha256_text(txt), "sitewide_block": sitewide,
                      "sitemaps": sitemaps, "groups": len(groups), "ai_posture": posture}
    if sitewide:
        out["notes"].append("robots * 组含 Disallow: / → 全站拒抓")
    return out


def ai_posture(groups_raw):
    """robots 原文 → AI 爬虫放行矩阵(近似:组内出现根路径 disallow 即 blocked)。"""
    posture = {}
    for bot in AI_CRAWLERS:
        g = groups_raw.get(bot)
        if g is None:
            posture[bot] = "no_rule(=放行)"
        elif any(d in ("", "/") for d in g["disallow"]):
            posture[bot] = "blocked"
        elif g["allow"]:
            posture[bot] = "allowed(显式)"
        else:
            posture[bot] = "allowed(空规则)"
    return posture


def check_visibility(site):
    out = {"check": "visibility", "state": "ok", "metrics": {}, "notes": []}
    host = urllib.parse.urlparse(site).netloc
    reg = registrable_domain(site)
    q = "https://www.bing.com/search?q=" + urllib.parse.quote("site:" + host)
    try:
        r = http_get(q)
    except FetchError as e:
        out["state"] = "skipped"
        out["metrics"] = {"error": str(e)}
        out["notes"].append("可见性端点抓取失败→skipped 不告警(不猜)")
        return out
    if r["status"] != 200:
        out["state"] = "blocked"
        out["metrics"] = {"status": r["status"]}
        out["notes"].append("site: 端点返回 %d→blocked 不告警" % r["status"])
        return out
    cites = re.findall(r"<cite[^>]*>(.*?)</cite>", r["body"], re.S)
    if not cites and re.search(r"captcha|unusual traffic|verify you", r["body"], re.I):
        out["state"] = "blocked"
        out["metrics"] = {"status": r["status"]}
        out["notes"].append("site: 端点疑似人机验证→blocked 不告警")
        return out
    sample, visible = [], 0
    for c in cites[:10]:
        u = unescape(re.sub(r"<[^>]+>", "", c)).replace(" › ", "/")
        if reg and reg in u:
            visible += 1
            if len(sample) < 5:
                sample.append(u)
    out["metrics"] = {"status": r["status"], "visible_pages": visible, "sample": sample}
    out["notes"].append("方法限制:Bing HTML 端点无 SLA,非官方索引数;仅作抽查方向")
    return out


def check_gsc(mdir):
    out = {"check": "gsc", "state": "skipped", "metrics": {}, "notes": []}
    path = os.path.join(mdir, "gsc.csv")
    if not os.path.exists(path):
        out["notes"].append("未找到 gsc.csv(GSC 导出)→流量问跳过,不猜数")
        return out
    import csv as _csv
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = [r for r in _csv.DictReader(f) if r]
    except (OSError, UnicodeDecodeError) as e:
        out["metrics"] = {"error": str(e)}
        return out
    if not rows:
        out["metrics"] = {"error": "gsc.csv 为空"}
        return out
    cols = {(k or "").strip().lower(): k for k in rows[0]}
    click_col = cols.get("clicks")
    if not click_col:
        out["metrics"] = {"error": "gsc.csv 缺 Clicks 列"}
        return out
    total = 0
    for row in rows:
        try:
            total += int(float((row.get(click_col) or "0").replace(",", "")))
        except ValueError:
            pass
    out["state"] = "ok"
    out["metrics"] = {"clicks_total": total, "queries": len(rows),
                      "file_mtime": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(timespec="seconds")}
    out["notes"].append("口径:导出文件全期合计;每次 run 前刷新文件,比较的是两次 run 之间")
    return out


def check_sitemap(site, robots_metrics, budget):
    out = {"check": "sitemap", "state": "ok", "metrics": {}, "notes": []}
    urls = list(robots_metrics.get("sitemaps") or [])
    if not urls:
        urls = [site + "/sitemap.xml"]
        out["notes"].append("robots 无 Sitemap 指令,试探 /sitemap.xml")
    locs, lastmod_max = {}, ""
    idx = 0
    queue = list(urls[:3])
    while queue:
        if budget.exhausted():
            out["notes"].append("budget 耗尽,sitemap 解析中止(已解析部分照常入库)")
            break
        u = queue.pop(0)
        idx += 1
        if idx > SITEMAP_INDEX_CAP + 3:
            break
        try:
            r = http_get(u)
        except FetchError as e:
            out["notes"].append("sitemap 抓取失败 %s: %s" % (u, e))
            continue
        if r["status"] >= 400:
            out["notes"].append("sitemap %s → %d" % (u, r["status"]))
            continue
        found_locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", r["body"], re.I | re.S)
        is_index = "<sitemapindex" in r["body"].lower()
        if is_index:
            queue.extend(found_locs[:SITEMAP_INDEX_CAP])
            continue
        mods = re.findall(r"<url>.*?</url>", r["body"], re.I | re.S)
        mod_by_loc = {}
        for blk in mods:
            lm = re.search(r"<lastmod>\s*(.*?)\s*</lastmod>", blk, re.I)
            lc = re.search(r"<loc>\s*(.*?)\s*</loc>", blk, re.I)
            if lc:
                mod_by_loc[lc.group(1)] = (lm.group(1) if lm else "")
        if not mod_by_loc and found_locs:
            mod_by_loc = {l: "" for l in found_locs}
        for l, lm in list(mod_by_loc.items())[:SITEMAP_CAP]:
            locs[l] = lm
            if lm > lastmod_max:
                lastmod_max = lm
    if not locs:
        out["state"] = "absent"
        out["metrics"] = {"url_count": 0}
        out["notes"].append("未取到任何 sitemap URL(小站可能无 sitemap,合法)")
        return out
    out["metrics"] = {"url_count": len(locs), "lastmod_max": lastmod_max,
                      "locs": dict(list(locs.items())[:SITEMAP_CAP])}
    return out


def check_llms_txt(site):
    out = {"check": "llms_txt", "state": "ok", "metrics": {}, "notes": []}
    try:
        r = http_get(site + "/llms.txt")
    except FetchError as e:
        out["state"] = "error"
        out["metrics"] = {"error": str(e)}
        return out
    if r["status"] >= 400:
        out["state"] = "absent"
        out["metrics"] = {"present": False, "status": r["status"]}
        return out
    body = r["body"]
    out["metrics"] = {"present": True, "status": r["status"], "hash": sha256_text(body),
                      "h1_sections": len(re.findall(r"^# ", body, re.M))}
    return out


class Budget:
    """单次运行时长上限(学 geo-score 的 budget 思路):超即中止后续检查。"""

    def __init__(self, minutes):
        self.limit = minutes * 60.0 if minutes is not None else None
        self.t0 = time.monotonic()

    def exhausted(self):
        return self.limit is not None and (time.monotonic() - self.t0) > self.limit

    def used_sec(self):
        return round(time.monotonic() - self.t0, 1)


def run_checks(mdir, cfg, kind, budget):
    site = cfg["site"]
    market = cfg.get("market")
    results = {}
    plan = [("robots", lambda: check_robots(site, market)),
            ("home", lambda: check_page(site + "/")),
            ("key_pages", None)]
    for name, fn in plan:
        if budget.exhausted():
            results[name] = {"state": "budget_skipped"}
            continue
        if name == "key_pages":
            results["key_pages"] = {}
            for p in cfg.get("key_pages", ["/"]):
                if budget.exhausted():
                    results["key_pages"][p] = {"state": "budget_skipped"}
                    continue
                results["key_pages"][p] = check_page(site + p if p.startswith("/") else p)
            continue
        results[name] = fn()
    if budget.exhausted():
        results["visibility"] = {"state": "budget_skipped"}
    else:
        results["visibility"] = check_visibility(site)
    results["gsc"] = check_gsc(mdir)
    if kind == "weekly":
        robots_metrics = results.get("robots", {}).get("metrics", {})
        for name, fn in [("sitemap", lambda: check_sitemap(site, robots_metrics, budget)),
                         ("llms_txt", lambda: check_llms_txt(site))]:
            if budget.exhausted():
                results[name] = {"state": "budget_skipped"}
            else:
                results[name] = fn()
    return results


# ---------- run ----------

def snapshot_from_results(results):
    """检查结果 → 扁平快照 dict: {check: {key: value}}(value 可 JSON 化)。"""
    snap = {}

    def put(check, key, value):
        snap.setdefault(check, {})[key] = value

    r = results.get("robots", {})
    if r.get("state") == "ok":
        m = dict(r["metrics"])
        m.pop("sitemaps", None)  # sitemap 列表属 run 详情,不进对比快照
        put("robots", "robots", m)
    elif r.get("state"):
        put("robots", "robots", {"state": r["state"]})
    h = results.get("home", {})
    if h.get("state") == "ok":
        m = dict(h["metrics"])
        m["title_meta_hash"] = sha256_text(
            (m.get("title", "") + "|" + m.get("meta_desc", "") + "|" + m.get("canonical", "")))
        put("pages", "/", m)
    elif h.get("state"):
        put("pages", "/", {"state": h["state"], **h.get("metrics", {})})
    for p, pr in (results.get("key_pages") or {}).items():
        if pr.get("state") == "ok":
            m = dict(pr["metrics"])
            m["title_meta_hash"] = sha256_text(
                (m.get("title", "") + "|" + m.get("meta_desc", "") + "|" + m.get("canonical", "")))
            put("pages", p, m)
        elif pr.get("state"):
            put("pages", p, {"state": pr["state"], **pr.get("metrics", {})})
    v = results.get("visibility", {})
    if v.get("state") == "ok":
        put("visibility", "site", dict(v["metrics"]))
    elif v.get("state"):
        put("visibility", "site", {"state": v["state"]})
    g = results.get("gsc", {})
    if g.get("state") == "ok":
        put("gsc", "file", dict(g["metrics"]))
    s = results.get("sitemap", {})
    if s.get("state") == "ok":
        put("sitemap", "index", dict(s["metrics"]))
    elif s.get("state"):
        put("sitemap", "index", {"state": s["state"]})
    l = results.get("llms_txt", {})
    if l.get("state") == "ok":
        put("llms_txt", "file", dict(l["metrics"]))
    elif l.get("state"):
        put("llms_txt", "file", {"state": l["state"]})
    return snap


def cmd_run(args):
    mdir = args.dir
    cfg = load_config(mdir)
    conn = open_db(mdir)
    budget = Budget(args.budget_minutes if args.budget_minutes is not None
                    else cfg.get("budget_minutes", 5))
    results = run_checks(mdir, cfg, args.checks, budget)
    snap = snapshot_from_results(results)

    states = {}
    for grp in ("robots", "home", "visibility", "gsc", "sitemap", "llms_txt"):
        st = (results.get(grp) or {}).get("state")
        if st:
            states[grp] = st
    kp_states = {p: r.get("state") for p, r in (results.get("key_pages") or {}).items()}
    statuses = list(states.values()) + list(kp_states.values())
    run_status = "ok"
    if "budget_skipped" in statuses:
        run_status = "budget_exhausted"
    elif statuses and all(s == "error" for s in statuses):
        run_status = "all_error"

    payload = {"site": cfg["site"], "market": cfg.get("market"), "kind": args.checks,
               "status": run_status, "budget_used_sec": budget.used_sec(),
               "checks": {k: {"state": vv.get("state"), "notes": vv.get("notes", [])}
                          for k, vv in results.items() if isinstance(vv, dict) and "state" in vv},
               "key_pages": kp_states, "snapshot": snap}

    if args.dry_run:
        print("[dry-run] 不写库。状态=%s budget=%.1fs" % (run_status, budget.used_sec()))
        for grp, st in list(states.items()) + [("key_pages:" + p, s) for p, s in kp_states.items()]:
            print("  %-22s %s" % (grp, st))
        for grp, vv in results.items():
            if isinstance(vv, dict):
                for n in vv.get("notes", []):
                    print("    [i] %s: %s" % (grp, n))
        conn.close()
        return 0 if run_status == "ok" else 3

    cur = conn.execute(
        "INSERT INTO runs(ts, kind, status, checks_run, budget_used_sec, summary) VALUES(?,?,?,?,?,?)",
        (datetime.now().isoformat(timespec="seconds"), args.checks, run_status,
         args.checks, budget.used_sec(), json.dumps(payload, ensure_ascii=False)))
    run_id = cur.lastrowid
    ts = datetime.now().isoformat(timespec="seconds")
    for check, kv in snap.items():
        for key, value in kv.items():
            h = sha256_text(json.dumps(value, ensure_ascii=False, sort_keys=True))
            conn.execute("INSERT INTO snapshots(run_id, ts, \"check\", key, value, hash) VALUES(?,?,?,?,?,?)",
                         (run_id, ts, check, key, json.dumps(value, ensure_ascii=False), h))
    conn.commit()
    rpath = os.path.join(mdir, "runs", "run-%05d.json" % run_id)
    with open(rpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("run #%d 完成: kind=%s status=%s budget=%.1fs → %s"
          % (run_id, args.checks, run_status, budget.used_sec(), rpath))
    for grp, st in list(states.items()) + [("key_pages:" + p, s) for p, s in kp_states.items()]:
        if st not in ("ok",):
            print("  [!] %s: %s" % (grp, st))
    for grp, vv in results.items():
        if isinstance(vv, dict):
            for n in vv.get("notes", []):
                print("    [i] %s: %s" % (grp, n))
    if len(conn.execute("SELECT 1 FROM runs").fetchall()) == 1:
        print("[i] 首次 run=基线;下一步跑 diff(与下次 run 对比才有告警)")
    conn.close()
    return 0 if run_status == "ok" else 3


# ---------- diff(阈值告警引擎) ----------

def load_snapshot(conn, run_id):
    d = {}
    for row in conn.execute("SELECT \"check\", key, value FROM snapshots WHERE run_id=?", (run_id,)):
        d.setdefault(row["check"], {})[row["key"]] = json.loads(row["value"])
    return d


def latest_run_ids(conn, n=2):
    return [r["id"] for r in conn.execute(
        "SELECT id FROM runs ORDER BY id DESC LIMIT ?", (n,))]


def compute_alerts(prev, curr, cfg):
    """prev/curr 为扁平快照;返回 list[dict(level/code/key/message/details/action,boundary))]。"""
    th = cfg.get("thresholds", DEFAULT_THRESHOLDS)
    site = cfg.get("site", "")
    A = []

    def add(level, code, key, message, details=None):
        action, boundary = PLAYBOOK.get(code, ("按 continuous-operations.md 对应级别 playbook", "human"))
        A.append({"level": level, "code": code, "key": key, "message": message,
                  "details": details or {}, "action": action, "boundary": boundary})

    def page_state(snap, key):
        return ((snap.get("pages") or {}).get(key) or {})

    # --- 4 存活:首页/关键页 ---
    keys = set((curr.get("pages") or {}).keys()) | set((prev.get("pages") or {}).keys())
    for k in sorted(keys):
        c, p = page_state(curr, k), page_state(prev, k)
        label = "首页" if k == "/" else "关键页 %s" % k
        cs = c.get("status")
        if c.get("state") == "http_error" or (isinstance(cs, int) and cs >= 400):
            add("critical", "key_page_down" if k != "/" else "homepage_down", k,
                "%s 返回 %s" % (label, cs),
                {"prev_status": p.get("status"), "url": site + k})
        elif c.get("state") == "error":
            if p.get("state") == "error":
                add("warn", "fetch_error_confirmed", k, "%s 连续两次抓取失败(网络层)" % label,
                    {"prev_error": p.get("error"), "curr_error": c.get("error")})
            else:
                add("info", "fetch_error_single", k, "%s 单次抓取失败,下次复确认" % label,
                    {"error": c.get("error")})
        # 混合内容(https 站)
        cmc, pmc = c.get("mixed_content"), p.get("mixed_content")
        if isinstance(cmc, int) and cmc >= int(th.get("mixed_content_min", 3)) and (pmc or 0) < cmc:
            add("warn", "mixed_content", k, "%s 混合内容 %d 个 http:// 子资源(上次 %s)"
                % (label, cmc, pmc if pmc is not None else "无记录"), {"curr": cmc, "prev": pmc})
        # 时延
        cl, pl = c.get("latency_ms"), p.get("latency_ms")
        d = pct_drop(pl, cl) if pl else None  # 负值=增长
        if isinstance(d, float) and d < 0 and -d * 100 >= int(th.get("latency_increase_pct", 100)) \
                and max(pl or 0, cl or 0) >= int(th.get("latency_min_ms", 500)):
            add("info", "latency_spike", k, "%s 时延 %.0fms→%.0fms(+%.0f%%)"
                % (label, pl, cl, -d * 100), {"prev_ms": pl, "curr_ms": cl})

    # --- 4 存活/3 索引:robots ---
    cr, pr = (curr.get("robots") or {}).get("robots", {}), (prev.get("robots") or {}).get("robots", {})
    if cr.get("sitewide_block") and not pr.get("sitewide_block"):
        add("critical", "robots_sitewide_block", "robots",
            "robots.txt 出现 * 组全站 Disallow(几乎总是部署事故)",
            {"prev_hash": pr.get("hash"), "curr_hash": cr.get("hash")})
    elif cr.get("hash") and pr.get("hash") and cr["hash"] != pr["hash"]:
        add("info", "robots_changed", "robots", "robots.txt 内容变更(hash %s→%s)"
            % (pr.get("hash"), cr.get("hash")))
    cp, pp = cr.get("ai_posture") or {}, pr.get("ai_posture") or {}
    for bot in sorted(set(cp) & set(pp)):
        if cp[bot] != pp[bot]:
            add("info", "ai_posture_flip", "robots:" + bot,
                "AI 爬虫 %s 放行状态翻转: %s → %s" % (bot, pp[bot], cp[bot]))

    # --- 1 可见性 ---
    cv, pv = (curr.get("visibility") or {}).get("site", {}), (prev.get("visibility") or {}).get("site", {})
    if cv.get("state", "ok") == "ok" and "visible_pages" in cv:
        cvis, pvis = cv.get("visible_pages"), pv.get("visible_pages")
        floor = int(th.get("visibility_min_sample", 3))
        if pvis is not None and pvis >= floor:
            if cvis == 0:
                add("critical", "visibility_zero", "site",
                    "site: 抽查可见页 %d → 0(端点成功返回,疑似去索引/处罚)" % pvis,
                    {"prev": pvis, "curr": cvis, "sample": cv.get("sample")})
            else:
                d = pct_drop(pvis, cvis)
                if d is not None and d * 100 >= int(th.get("visibility_drop_pct", 30)):
                    add("warn", "visibility_drop", "site",
                        "site: 抽查可见页 %d → %d(−%.0f%%)" % (pvis, cvis, d * 100),
                        {"prev": pvis, "curr": cvis})
        elif pvis is None:
            A.append({"level": "info", "code": "visibility_baseline", "key": "site",
                      "message": "可见性基线建立: %d 页(下次 run 才参与告警)" % cvis,
                      "details": {"visible_pages": cvis},
                      "action": "记录基线,无需动作", "boundary": "auto"})

    # --- 2 流量 ---
    cg, pg = (curr.get("gsc") or {}).get("file", {}), (prev.get("gsc") or {}).get("file", {})
    cc, pc = cg.get("clicks_total"), pg.get("clicks_total")
    if cc is not None and pc is not None:
        floor = int(th.get("gsc_min_clicks", 5))
        d = pct_drop(pc, cc)
        if d is not None and min(pc, cc) >= floor and d * 100 >= int(th.get("gsc_clicks_drop_pct", 20)):
            add("warn", "gsc_clicks_drop", "file", "GSC 点击 %d → %d(−%.0f%%,地板 %d)"
                % (pc, cc, d * 100, floor), {"prev": pc, "curr": cc})
        elif d is not None and d < -0.5 and pc >= floor:
            add("info", "gsc_clicks_spike", "file", "GSC 点击 %d → %d(+%.0f%%)"
                % (pc, cc, -d * 100), {"prev": pc, "curr": cc})

    # --- 周检:sitemap ---
    csm, psm = (curr.get("sitemap") or {}).get("index", {}), (prev.get("sitemap") or {}).get("index", {})
    cuc, puc = csm.get("url_count"), psm.get("url_count")
    if isinstance(cuc, int) and isinstance(puc, int):
        d = pct_drop(puc, cuc)
        if d is not None and puc >= int(th.get("sitemap_min_sample", 20)) \
                and d * 100 >= int(th.get("sitemap_urls_drop_pct", 15)):
            add("warn", "sitemap_urls_drop", "index", "sitemap URL 数 %d → %d(−%.0f%%)"
                % (puc, cuc, d * 100), {"prev": puc, "curr": cuc})
        elif cuc > puc:
            A.append({"level": "info", "code": "sitemap_urls_grew", "key": "index",
                      "message": "sitemap URL 数 %d → %d(+%d)" % (puc, cuc, cuc - puc),
                      "details": {}, "action": "记录,无需动作", "boundary": "auto"})

    # --- 周检:title/meta 漂移 + llms.txt ---
    for k in sorted(set((curr.get("pages") or {})) & set((prev.get("pages") or {}))):
        ch, ph = curr["pages"][k].get("title_meta_hash"), prev["pages"][k].get("title_meta_hash")
        if ch and ph and ch != ph:
            add("info", "title_meta_drift", k, "%s 的 title/meta/canonical 漂移(hash %s→%s)"
                % ("首页" if k == "/" else "页面 %s" % k, ph, ch),
                {"prev_title": prev["pages"][k].get("title"), "curr_title": curr["pages"][k].get("title")})
    clm, plm = (curr.get("llms_txt") or {}).get("file", {}), (prev.get("llms_txt") or {}).get("file", {})
    if plm.get("present") and clm and not clm.get("present", True) and "present" in clm:
        add("info", "llms_txt_removed", "file", "llms.txt 从存在变为缺失")
    elif clm.get("hash") and plm.get("hash") and clm["hash"] != plm["hash"]:
        add("info", "llms_txt_changed", "file", "llms.txt 内容变更(hash %s→%s)"
            % (plm.get("hash"), clm.get("hash")))

    order = {l: i for i, l in enumerate(LEVELS)}
    A.sort(key=lambda a: order.get(a["level"], 9))
    return A


def cmd_diff(args):
    mdir = args.dir
    cfg = load_config(mdir)
    conn = open_db(mdir)
    if args.run_id:
        curr_id = args.run_id
    else:
        ids = latest_run_ids(conn, 2)
        if len(ids) < 2:
            print("错误: 需要 ≥2 次 run 才能 diff(先再跑一次 run)", file=sys.stderr)
            conn.close()
            return 4
        curr_id, prev_id = ids[0], ids[1]
    if not args.prev_run_id:
        row = conn.execute("SELECT MAX(id) AS m FROM runs WHERE id<?", (curr_id,)).fetchone()
        prev_id = row["m"]
        if prev_id is None:
            print("错误: run %d 之前没有可对比的 run" % curr_id, file=sys.stderr)
            conn.close()
            return 4
    else:
        prev_id = args.prev_run_id
    prev, curr = load_snapshot(conn, prev_id), load_snapshot(conn, curr_id)
    alerts = compute_alerts(prev, curr, cfg)

    now = datetime.now()
    cooldowns = cfg.get("cooldown_hours", COOLDOWN_HOURS)
    cur_fps = {("%s:%s" % (a["code"], a["key"])) for a in alerts}
    unresolved = conn.execute(
        "SELECT id, code, key, level, ts FROM alerts WHERE resolved=0 AND level!='low'").fetchall()
    healed, suppressed = [], []
    for a in alerts:
        fp = "%s:%s" % (a["code"], a["key"])
        for row in unresolved:
            if row["code"] + ":" + row["key"] == fp:
                try:
                    age = (now - datetime.fromisoformat(row["ts"])).total_seconds() / 3600
                except ValueError:
                    age = 1e9
                if age < cooldowns.get(a["level"], 24):
                    a["suppressed"] = True
                    a["suppressed_since"] = row["ts"]
                    suppressed.append(fp)
                break
    for row in unresolved:
        fp = row["code"] + ":" + row["key"]
        if fp not in cur_fps:
            healed.append(fp)

    payload = {"generated": now.isoformat(timespec="seconds"), "site": cfg["site"],
               "market": cfg.get("market"), "curr_run": curr_id, "prev_run": prev_id,
               "alerts": alerts, "healed": healed, "suppressed": suppressed,
               "counts": {l: sum(1 for a in alerts if a["level"] == l) for l in LEVELS}}

    if not args.dry_run:
        for a in alerts:
            if a.get("suppressed"):
                continue  # 冷却期内的重复指纹不重复入库(原未结行已代表它)
            conn.execute(
                "INSERT INTO alerts(run_id, ts, level, code, key, message, details, suppressed) "
                "VALUES(?,?,?,?,?,?,?,0)",
                (curr_id, now.isoformat(timespec="seconds"), a["level"], a["code"], a["key"],
                 a["message"], json.dumps({"details": a.get("details"), "action": a.get("action"),
                                           "boundary": a.get("boundary")}, ensure_ascii=False)))
        for row in unresolved:
            if row["code"] + ":" + row["key"] not in cur_fps:
                conn.execute("UPDATE alerts SET resolved=1, resolved_run=? WHERE id=?",
                             (curr_id, row["id"]))
                conn.execute(
                    "INSERT INTO alerts(run_id, ts, level, code, key, message, details) "
                    "VALUES(?,?,?,?,?,?,?)",
                    (curr_id, now.isoformat(timespec="seconds"), "low",
                     row["code"] + "_resolved", row["key"],
                     "自愈: %s 的问题已消失(上次 %s)" % (row["key"], row["ts"]),
                     json.dumps({"prev_level": row["level"]}, ensure_ascii=False)))
        conn.commit()
    conn.close()

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print("[i] 告警 JSON 已写入 %s" % args.out)
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("== diff: run #%d vs run #%d (%s) ==" % (curr_id, prev_id, cfg["site"]))
        c = payload["counts"]
        print("critical=%d warn=%d info=%d | 自愈=%d 抑制=%d"
              % (c["critical"], c["warn"], c["info"], len(healed), len(suppressed)))
        for a in alerts:
            mark = "(cooldown 抑制)" if a.get("suppressed") else ""
            print("  [%s] %s: %s %s" % (a["level"].upper(), a["code"], a["message"], mark))
            if a.get("action"):
                print("         → %s[%s]" % (a["action"], a.get("boundary")))
        for fp in healed:
            print("  [LOW] 自愈: %s" % fp)
        if not alerts and not healed:
            print("  (无告警;指标在阈值内)")
    if payload["counts"]["critical"]:
        return 1
    if payload["counts"]["warn"]:
        return 2
    return 0


# ---------- report ----------

def cmd_report(args):
    mdir = args.dir
    cfg = load_config(mdir)
    conn = open_db(mdir)
    since = (datetime.now() - timedelta(days=args.days)).isoformat(timespec="seconds")
    runs = conn.execute("SELECT * FROM runs WHERE ts>=? ORDER BY id", (since,)).fetchall()
    alerts = conn.execute("SELECT * FROM alerts WHERE ts>=? ORDER BY id", (since,)).fetchall()
    if not runs:
        print("近 %d 天无 run 记录。" % args.days)
        conn.close()
        return 0
    lines = []
    lines.append("== 持续监控周报: %s(市场 %s,近 %d 天)==" % (cfg["site"], cfg.get("market") or "-", args.days))
    lines.append("runs: %d 次(%s)| 状态分布: %s" % (
        len(runs), ",".join(sorted({r["kind"] for r in runs})),
        ",".join("%s=%d" % (s, sum(1 for r in runs if r["status"] == s))
                 for s in sorted({r["status"] for r in runs}))))
    if args.json:
        trend = {}
        for metric, check, key in [("visible_pages", "visibility", "site"),
                                   ("url_count", "sitemap", "index"),
                                   ("latency_ms", "pages", "/")]:
            series = []
            for row in conn.execute(
                    "SELECT run_id, value FROM snapshots WHERE \"check\"=? AND key=? AND ts>=? ORDER BY run_id",
                    (check, key, since)):
                v = json.loads(row["value"]).get(metric)
                if isinstance(v, (int, float)):
                    series.append(v)
            trend[metric] = series
        out = {"site": cfg["site"], "days": args.days, "runs": len(runs),
               "alerts": [{"level": a["level"], "code": a["code"], "message": a["message"],
                           "suppressed": bool(a["suppressed"]), "resolved": bool(a["resolved"])}
                          for a in alerts],
               "trend": trend}
        conn.close()
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    lines.append("-- 告警汇总 --")
    by_level = {l: [a for a in alerts if a["level"] == l] for l in LEVELS}
    if not alerts:
        lines.append("  (无)")
    for l in LEVELS:
        if by_level[l]:
            sup = sum(1 for a in by_level[l] if a["suppressed"])
            res = sum(1 for a in by_level[l] if a["resolved"])
            lines.append("  %-8s %d 条(抑制 %d / 已自愈 %d)" % (l, len(by_level[l]), sup, res))
            for a in by_level[l][:10]:
                lines.append("    - %s: %s" % (a["code"], a["message"]))
    lines.append("-- 趋势(从快照取值)--")
    for label, check, key, metric in [("可见页", "visibility", "site", "visible_pages"),
                                      ("sitemap URL 数", "sitemap", "index", "url_count"),
                                      ("首页时延 ms", "pages", "/", "latency_ms")]:
        series = []
        for row in conn.execute(
                "SELECT value FROM snapshots WHERE \"check\"=? AND key=? AND ts>=? ORDER BY run_id",
                (check, key, since)):
            v = json.loads(row["value"]).get(metric)
            if isinstance(v, (int, float)):
                series.append(v)
        if series:
            arrow = ""
            if len(series) >= 2 and series[0]:
                chg = (series[-1] - series[0]) / series[0] * 100
                arrow = "  首末 %+.0f%%" % chg
            lines.append("  %-14s %s%s" % (label, " → ".join("%.0f" % v for v in series[-8:]), arrow))
    lines.append("-- 建议 PR 列表(自动安全项可直接执行;draft PR 项须人审)--")
    seen, prs = set(), []
    for a in sorted(alerts, key=lambda x: LEVELS.index(x["level"]) if x["level"] in LEVELS else 9):
        if a["level"] in ("low",) or a["resolved"]:
            continue
        det = json.loads(a["details"] or "{}")
        action, boundary = det.get("action"), det.get("boundary")
        code = a["code"]
        if code in seen or not action:
            continue
        seen.add(code)
        prs.append((a["level"], code, action, boundary))
    if prs:
        for lv, code, action, boundary in prs:
            lines.append("  [%s/%s] %s → %s" % (lv, boundary or "human", code, action))
    else:
        lines.append("  (无待办;健康)")
    lines.append("-- 月校准提醒 --")
    lines.append("  阈值/冷却期按 alert-threshold-guide.md 月度复盘:噪音多→放宽或加连续触发;")
    lines.append("  漏报→查信号;改版后重建基线。")
    print("\n".join(lines))
    conn.close()
    return 0


# ---------- CLI / 自测 ----------

def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true", help="离线冒烟自测(不联网)")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("init", help="建立 .seo-monitor/(SQLite+config)")
    p.add_argument("--site", required=True)
    p.add_argument("--market", default="")
    p.add_argument("--key-pages", default="/", help="逗号分隔路径,默认 /")
    p.add_argument("--dir", default=DEFAULT_DIR)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("run", help="跑一轮检查并写库")
    p.add_argument("--checks", choices=["daily", "weekly"], default="daily")
    p.add_argument("--dry-run", action="store_true", help="执行但不写库")
    p.add_argument("--budget-minutes", type=float, default=None, help="单次运行时长上限(默认取 config)")
    p.add_argument("--dir", default=DEFAULT_DIR)
    p.set_defaults(func=cmd_run)
    p = sub.add_parser("diff", help="与上次 run 对比,超阈值才告警")
    p.add_argument("--run-id", type=int, default=None)
    p.add_argument("--prev-run-id", type=int, default=None)
    p.add_argument("--format", choices=["json", "text"], default="text")
    p.add_argument("--out", default="", help="把告警 JSON 写到文件(供 notify.py)")
    p.add_argument("--dry-run", action="store_true", help="计算但不落 alerts 表")
    p.add_argument("--dir", default=DEFAULT_DIR)
    p.set_defaults(func=cmd_diff)
    p = sub.add_parser("report", help="周报:趋势+告警汇总+建议 PR")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--json", action="store_true")
    p.add_argument("--dir", default=DEFAULT_DIR)
    p.set_defaults(func=cmd_report)
    return ap


def _self_test():
    tmp = tempfile.mkdtemp(prefix="monitor_selftest_")
    mdir = os.path.join(tmp, ".seo-monitor")
    rc = cmd_init(build_parser().parse_args(
        ["init", "--site", "https://example.com", "--market", "us", "--dir", mdir]))
    assert rc == 0 and os.path.exists(os.path.join(mdir, "config.json"))
    cfg = load_config(mdir)
    assert cfg["site"] == "https://example.com" and cfg["market"] == "us"
    assert cfg["thresholds"]["gsc_clicks_drop_pct"] == 20

    # 快照/告警引擎(离线合成,零网络)
    prev = {
        "pages": {"/": {"status": 200, "latency_ms": 800.0, "title": "Old", "mixed_content": 0,
                        "title_meta_hash": "aaa"},
                  "/pricing": {"status": 200, "title": "P", "title_meta_hash": "bbb"}},
        "robots": {"robots": {"status": 200, "hash": "h1", "sitewide_block": False,
                              "ai_posture": {"GPTBot": "no_rule(=放行)", "CCBot": "allowed(显式)"}}},
        "visibility": {"site": {"state": "ok", "visible_pages": 5, "sample": []}},
        "gsc": {"file": {"clicks_total": 100}},
        "sitemap": {"index": {"url_count": 100}},
        "llms_txt": {"file": {"present": True, "hash": "l1"}},
    }
    curr = {
        "pages": {"/": {"status": 200, "latency_ms": 1900.0, "title": "New", "mixed_content": 4,
                        "title_meta_hash": "zzz"},
                  "/pricing": {"status": 404, "title": "", "title_meta_hash": ""}},
        "robots": {"robots": {"status": 200, "hash": "h2", "sitewide_block": True,
                              "ai_posture": {"GPTBot": "blocked", "CCBot": "allowed(显式)"}}},
        "visibility": {"site": {"state": "ok", "visible_pages": 0, "sample": []}},
        "gsc": {"file": {"clicks_total": 70}},
        "sitemap": {"index": {"url_count": 50}},
        "llms_txt": {"file": {"present": True, "hash": "l2"}},
    }
    alerts = compute_alerts(prev, curr, cfg)
    codes = {(a["level"], a["code"]) for a in alerts}
    assert ("critical", "key_page_down") in codes                 # /pricing 200→404
    assert ("critical", "robots_sitewide_block") in codes         # robots 误封
    assert ("critical", "visibility_zero") in codes               # 5→0,过地板 3
    assert ("warn", "gsc_clicks_drop") in codes                   # 100→70 −30%,过地板 5
    assert ("warn", "sitemap_urls_drop") in codes                 # 100→50 −50%,过地板 20
    assert ("warn", "mixed_content") in codes                     # 0→4 ≥3
    assert ("info", "title_meta_drift") in codes                  # 首页 hash 变
    assert ("info", "robots_changed") not in codes                # 已升 critical,不再 info
    assert ("info", "ai_posture_flip") in codes                   # GPTBot 放行→封锁
    assert ("info", "llms_txt_changed") in codes
    assert ("info", "latency_spike") in codes                     # 800→1900 +137% 过地板
    lv = {a["code"]: a["level"] for a in alerts}
    assert lv["sitemap_urls_drop"] == "warn"
    # 最小样本地板:小站不告警(防疲劳)
    small_prev = {"visibility": {"site": {"state": "ok", "visible_pages": 2}}}
    small_curr = {"visibility": {"site": {"state": "ok", "visible_pages": 0}}}
    alerts2 = compute_alerts(small_prev, small_curr, cfg)
    assert not any(a["code"] == "visibility_zero" for a in alerts2)
    # pct_drop 不猜:prev=0/None → None
    assert pct_drop(0, 5) is None and pct_drop(None, 1) is None
    # 混合内容仅 https 统计
    assert mixed_content_count("http://x/", "<img src='http://a/b'>") is None
    assert mixed_content_count("https://x/", "<img src='http://a/b'>x") == 1
    # robots 解析:sitewide 检测 + market bots
    g = {"*": {"allow": [], "disallow": ["/"]}}
    pos = ai_posture(g)
    assert pos["GPTBot"] == "no_rule(=放行)"
    g2 = {"GPTBot": {"allow": [], "disallow": [""]}}
    assert ai_posture(g2)["GPTBot"] == "blocked"
    # 自愈路径:critical 消失 → low
    healed_curr = json.loads(json.dumps(prev))  # 与 prev 相同→无告警
    alerts3 = compute_alerts(prev, healed_curr, cfg)
    assert not any(a["level"] == "critical" for a in alerts3)
    # Budget:0 分钟立刻耗尽
    b = Budget(0)
    time.sleep(0.01)
    assert b.exhausted()
    print("[self-test] PASS monitor(11 类告警判定/最小样本地板/自愈/混合内容/robots 解析/budget)")


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if getattr(args, "self_test", False):
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL monitor")
            return 1
    if not getattr(args, "cmd", None):
        ap.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
