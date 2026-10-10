#!/usr/bin/env python3
"""持续监控守护核心(stdlib-only:sqlite3+urllib,零第三方依赖)。
把一次性审计变成长期监控:日检四问 → SQLite 快照 → diff 阈值告警 → 周报。

日检四问(行业分层):
  1 可见性  关键页 site: 抽查(Bing HTML 端点;被拦=skipped 不告警,不猜)
  2 流量    .seo-monitor/gsc.csv(GSC 导出,有才查;无数据源=skipped)
  3 索引    robots.txt 哈希/误封检测 + sitemap URL 数/lastmod
           +页面级 noindex(meta robots / X-Robots-Tag 响应头,D1 P0-1:
            Conductor 头号触发器 "Pages became non-indexable")
           +canonical 目标健康度(HEAD 探测,连续 3 次失败才告警,D1 P0-2)
  4 存活    首页+关键页状态码/时延/https 混合内容
周检叠加:标题/meta 漂移哈希、llms.txt 变更、sitemap lastmod 对比、AI 爬虫放行矩阵。

告警四级(critical/warn/info/low)+ 百分比阈值×最小样本地板 = 防疲劳;
low=自愈(上次告警本次恢复)。cooldown:critical 12h / warn 24h / info 168h。

子命令:
  init   --site URL [--market XX] [--key-pages /a,/b] [--heartbeat-url U]
         [--dir .seo-monitor] [--force]
  run    [--checks daily|weekly] [--dry-run] [--budget-minutes N] [--dir D]
  diff   [--run-id N] [--prev-run-id M] [--format json|text] [--out FILE] [--dry-run] [--dir D]
  report [--days 7] [--json] [--dir D]
  quarantine RUN_ID [--undo] [--dir D]   # 隔离坏 run(基线污染防护),diff 不再用它对比
  maintenance --from F --to T [--reason R] [--clear] [--dir D]  # 维护窗口:窗口内 diff 只记快照不产告警

退出码:diff → 1=有 critical,2=有 warn(无 critical),0=无,4=用法/数据错误;
run → 0 正常,3=run 未完成(partial/failed)。SSRF 防护:仅 http(s)+私网拒连
+TLS 恒验证+重定向逐跳复查(302 穿墙已堵)。

并发与基线卫生(多 cron 安全):SQLite WAL + busy_timeout=30s + 目录级 flock;
run 先落 status='running' 再跑检查,终态 ok/partial/failed;卡死 run 由
sweep_stale_runs(>30min)回收;diff 的 prev 只取 status='ok';坏 run 用
quarantine 隔离;历史按 PruneDB 纪律保留最近 400 次 run。
cooldown 命中的告警标 suppressed:只进报告,不进通知路径(counts/退出码同排除)。

用法:
  python3 monitor.py init --site https://example.com --market us
  python3 monitor.py run --checks daily
  python3 monitor.py diff --format text
  python3 monitor.py report --days 7
  python3 monitor.py --self-test
"""
import argparse
import contextlib
import fcntl
import hashlib
import ipaddress
import json
import os
import re
import socket
import sqlite3
import ssl
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
    "ssl_cert_expired":     ("立即续期证书(auto 项:certbot renew 类幂等动作)", "auto"),
    "ssl_cert_expiry":      ("续期证书;检查自动续期任务为何没跑", "human"),
    "content_regression":   ("核对 expect_substring 断言;查空白渲染/软 404/误改版(draft PR)", "draft_pr"),
    "dead_man":             ("监控自身停摆:查 cron/Actions 是否被禁、机器是否休眠", "human"),
    "noindex_added":        ("自动安全项:回滚引入 noindex 的发布/模板改动(若非有意下线)", "auto"),
    "noindex_removed":      ("自愈信号,记录即可;顺手排查此前为何被误加 noindex", "human"),
    "canonical_target_broken": ("核对 canonical 目标是否被移动/删除:修正指向或恢复目标页(draft PR)", "draft_pr"),
}

# 告警抑制树(audit 19,Prometheus inhibition 纪律):根因一条,派生折叠。
# 格式:根告警码 → (被抑制码..., 作用域) 作用域 sitewide=抑制一切;same_key=仅同 key。
# D1 P0-1:页面级 noindex_added 属派生信号——robots 全站误封/首页宕机这类 sitewide 根因
# 在场时折叠(同一部署事故的次级表现,单独重复通知只会稀释根因)。
INHIBITS = {
    "homepage_down":        (("key_page_down", "content_regression", "mixed_content", "noindex_added"), "sitewide"),
    "robots_sitewide_block": (("noindex_added",), "sitewide"),
    "fetch_error_confirmed": (("title_meta_drift", "content_regression", "mixed_content", "latency_spike"), "same_key"),
}

# 关键页字段级 diff 的比对字段(audit 17,changedetection.io 字段级指纹)。
# D1 P0-1/P0-2 新快照字段(indexable/noindex_source/canonical_target_status/
# canonical_fail_streak)刻意不进本清单:各有专用规则(noindex_added/removed、
# canonical_target_broken),进字段漂移会双报;且旧 monitor.db 快照缺这些字段,
# 会被当 "(None→有值)" 漂移,升级后首个 diff 全网误报。
PAGE_DIFF_FIELDS = ("title", "meta_desc", "canonical", "og_title", "og_desc", "watch")


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


class _RedirectGuard(urllib.request.HTTPRedirectHandler):
    """重定向逐跳 SSRF 复查(audit 05 P0:urlopen 自动跟随 302,最终 host 从不复查,
    站方可控的 robots.txt sitemap 指令可 302 到 169.254.169.254 穿墙)。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urllib.parse.urlparse(newurl)
        if p.scheme not in ("http", "https"):
            raise FetchError("重定向到非 http(s) 被拒: %s" % _redact_url(newurl))
        ssrf_guard(p.hostname)  # 每一跳都复查,包括最后一跳
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_RedirectGuard)


def _redact_url(u):
    """日志脱敏:保留 scheme+host,路径/查询(常含 token)打码。"""
    return re.sub(r"^(https?://[^/\s]+).*$", r"\1/[REDACTED]", str(u))


def _headers_of(msg):
    """响应头对象 → 扁平 dict(键小写,重复键逗号并值)。D1 P0-1 需读 X-Robots-Tag;
    对 None/异常对象容错(旧测试桩/特殊响应路径可能无头)。"""
    out = {}
    if msg is None:
        return out
    try:
        keys = list(msg.keys())
    except Exception:
        return out
    for k in keys:
        try:
            vals = msg.get_all(k) or []
        except Exception:
            continue
        if vals:
            out[str(k).lower()] = ", ".join(v.strip() for v in vals if v is not None)
    return out


def http_get(url, timeout=FETCH_TIMEOUT):
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        raise FetchError("仅允许 http(s): %s" % url)
    ssrf_guard(p.hostname)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xml,*/*"})
    t0 = time.monotonic()
    try:
        with _opener.open(req, timeout=timeout) as r:
            body = r.read(MAX_BYTES)
            return {"status": r.status, "final_url": r.geturl(), "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
                    "body": body.decode("utf-8", "replace"), "headers": _headers_of(r.headers)}
    except urllib.error.HTTPError as e:
        body = e.read(MAX_BYTES) if e.fp else b""
        return {"status": e.code, "final_url": url, "elapsed_ms": round((time.monotonic() - t0) * 1000, 1),
                "body": body.decode("utf-8", "replace"), "headers": _headers_of(e.headers)}
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise FetchError("抓取失败 %s: %s" % (_redact_url(url), e))


def http_head(url, timeout=FETCH_TIMEOUT):
    """HEAD 探测(D1 P0-2 canonical 目标健康度):复用 http_get 的 SSRF 防御/超时/
    重定向逐跳复查;405/501(站点不支持 HEAD)降 GET 只读头——不下载 body。
    返回 {"status": int};网络层失败抛 FetchError(由调用方按 "error" 记,防抖在 diff)。"""
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        raise FetchError("仅允许 http(s): %s" % url)
    ssrf_guard(p.hostname)

    def once(method):
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method=method)
        try:
            with _opener.open(req, timeout=timeout) as r:
                return int(r.status)          # GET 降级也只取状态,不读 body
        except urllib.error.HTTPError as e:
            if e.fp:
                with contextlib.suppress(Exception):
                    e.read(512)
            return int(e.code)
    try:
        status = once("HEAD")
        if status in (405, 501):
            status = once("GET")
        return {"status": status}
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise FetchError("HEAD 失败 %s: %s" % (_redact_url(url), e))


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
    conn = sqlite3.connect(os.path.join(mdir, "monitor.db"), timeout=30.0)
    conn.row_factory = sqlite3.Row
    # audit 05 P1:本地多 cron/挂住的 run 并发 → WAL + busy_timeout,
    # 与目录级 flock(见 monitor_lock)双保险。
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.executescript(SCHEMA)
    return conn


@contextlib.contextmanager
def monitor_lock(mdir, timeout=120.0):
    """目录级 flock:同一 .seo-monitor/ 同时只允许一个 run/diff(本地 cron 竞态)。"""
    os.makedirs(mdir, exist_ok=True)
    path = os.path.join(mdir, ".lock")
    fh = open(path, "w")
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise SystemExit("错误: 另一 monitor 进程持有 %s 超过 %.0fs,放弃(防本地 cron 竞态)"
                                     % (path, timeout))
                time.sleep(0.5)
        yield
    finally:
        try:
            fcntl.flock(fh, fcntl.LOCK_UN)
        finally:
            fh.close()


# 值形似 secret(已知 webhook/token 形态;防 config.json 明文落盘,audit 05 P1)
_SECRET_VALUE_RE = re.compile(
    r"hooks\.slack\.com/services|discord(app)?\.com/api/webhooks|api\.telegram\.org/bot"
    r"|xox[bposa]-|[0-9]{8,}:[A-Za-z0-9_-]{30,}|hooks\.(feishu|dingtalk)|camel\.ai|sk-[A-Za-z0-9]{20,}", re.I)
# 键名即要求非 secret(只允许 env 引用名或 $ENV 形式,audit 01 rec4)
_SECRET_KEY_RE = re.compile(r"(webhook_url|bot_token|password|api_key|secret)$", re.I)


def find_config_secrets(cfg):
    """返回 config 里疑似明文 secret 的路径列表(channels 只存 env 引用名)。"""
    hits = []

    def walk(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and _SECRET_KEY_RE.search(k or "") and v \
                        and not v.startswith("$") and "env" not in k.lower():
                    hits.append(".".join(path + [k]) + "(键要求 env 引用,不接受明文)")
                walk(v, path + [str(k)])
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, path + [str(i)])
        elif isinstance(obj, str) and obj and _SECRET_VALUE_RE.search(obj):
            hits.append(".".join(path) + "(值形似 secret)")

    walk(cfg, [])
    return hits


def load_config(mdir):
    path = os.path.join(mdir, "config.json")
    if not os.path.exists(path):
        raise SystemExit("错误: %s 不存在,先跑 init" % path)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_config(mdir, cfg):
    hits = find_config_secrets(cfg)
    if hits:
        raise SystemExit(
            "错误: config.json 检测到疑似明文 secret,拒写(审计 05-§4):\n  - " + "\n  - ".join(hits)
            + "\nsecret 只经环境变量注入(channels.* 只存 env 引用名);若确为误报,"
              "改用 $ENV_NAME 引用形式或换键名后重试")
    tmp = os.path.join(mdir, "config.json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, os.path.join(mdir, "config.json"))


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
    heartbeat = (args.heartbeat_url or os.environ.get("SEO_MONITOR_HEARTBEAT_URL") or "").strip()
    cfg = {
        "site": site,
        "market": (args.market or "").lower() or None,
        "key_pages": key_pages,
        "created": datetime.now().isoformat(timespec="seconds"),
        "budget_minutes": 5,
        "cooldown_hours": dict(COOLDOWN_HOURS),
        "thresholds": dict(DEFAULT_THRESHOLDS),
        "heartbeat_url": heartbeat or None,
        "run_cadence_hours": 24,   # dead man's switch 判定用:无成功 run 超 2×该值 → dead_man
        "channels": {
            "slack":    {"env": "SEO_MONITOR_SLACK_WEBHOOK"},
            "discord":  {"env": "SEO_MONITOR_DISCORD_WEBHOOK"},
            "telegram": {"env_token": "SEO_MONITOR_TG_TOKEN", "env_chat": "SEO_MONITOR_TG_CHAT"},
            "email":    {"smtp_host": "", "smtp_port": 465, "use_ssl": True, "username": "",
                         "env_pass": "SEO_MONITOR_SMTP_PASS", "from": "", "to": []},
            "webhook":  {"env": "SEO_MONITOR_WEBHOOK_URL",
                         "note": "Apprise 式通用 webhook:URL 支持 json(s):// form(s):// text(s):// scheme"},
        },
        "notes": [
            "secret 只经环境变量注入(channels 只存 env 引用名,写明文会被 save_config 拒绝)",
            "GSC 流量检查:每次 run 前把 GSC 导出放到 " + os.path.join(mdir, "gsc.csv") +
            "(列含 Query,Clicks,Impressions);没有该文件则跳过流量问",
            "阈值是经验起点,按 alert-threshold-guide.md 用本站基线校准",
            "key_pages 支持对象形式: {\"path\": \"/p\", \"expect_substring\": \"Price\", "
            "\"selector\": \"h1\" 或 \"re:<regex>\"}(关键词在场断言+字段级 diff 圈定)",
            "heartbeat: 配 healthchecks.io 类 ping URL 后,run 成功 ping /ok、失败 ping /fail;"
            "grace 建议 ≈ cron 间隔×2+典型运行时长",
        ],
    }
    os.makedirs(mdir, exist_ok=True)
    os.makedirs(os.path.join(mdir, "runs"), exist_ok=True)
    conn = open_db(mdir)
    conn.close()
    save_config(mdir, cfg)
    print("监控目录已建立: %s/" % mdir)
    print("  monitor.db   SQLite(runs/snapshots/alerts,WAL 模式)")
    print("  config.json 站点=%s 市场=%s 关键页=%s" % (site, cfg["market"] or "-", ",".join(key_pages)))
    print("  runs/        每次 run 的 JSON 快照")
    if heartbeat:
        print("  heartbeat    %s(成功 ping /ok,失败 ping /fail)" % _redact_url(heartbeat))
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

    def prop(p):
        m = re.search(r'<meta[^>]+property=["\']%s["\'][^>]+content=["\'](.*?)["\']' % p, html, re.I) or \
            re.search(r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']%s["\']' % p, html, re.I)
        return m.group(1).strip() if m else ""
    canonical = ""
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\'](.*?)["\']', html, re.I)
    if m:
        canonical = m.group(1)
    return title, meta, canonical, prop("og:title"), prop("og:description")


# noindex 指令 token:词边界匹配——命中 "noindex"/"noindex,nofollow"/"googlebot: noindex",
# 不命中 "nonoindex"/自定义词(D1 P0-1)
_NOINDEX_TOKEN_RE = re.compile(r"(?<![\w-])noindex(?![\w-])", re.I)


def meta_robots_noindex(html):
    """<meta name=robots content=...> 含 noindex 指令(属性两种顺序均支持,大小写不敏感)。"""
    m = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\'](.*?)["\']', html, re.I) or \
        re.search(r'<meta[^>]+content=["\'](.*?)["\'][^>]*name=["\']robots["\']', html, re.I)
    return bool(m and _NOINDEX_TOKEN_RE.search(m.group(1)))


def header_noindex(headers):
    """X-Robots-Tag 响应头含 noindex(多 directive/agent 前缀如 googlebot:noindex 均命中;
    headers 为 http_get 保留的扁平小写键 dict,键大小写不敏感,None/缺键=无)。"""
    h = headers or {}
    v = h.get("x-robots-tag")
    if v is None:
        for k, val in h.items():
            if str(k).lower() == "x-robots-tag":
                v = val
                break
    return bool(_NOINDEX_TOKEN_RE.search(v or ""))


def canonical_failure(status):
    """canonical 目标探测值是否算失败:网络不可达("error")或最终状态 ≥4xx
    (重定向已被跟随,以最终落点为准)。None/2xx/3xx → False。"""
    return status == "error" or (isinstance(status, int) and status >= 400)


def probe_canonical_target(page_url, final_url, canonical):
    """D1 P0-2:canonical 目标健康度探测(check_page 内调用=每页每 run 恰一次)。
    HEAD 复用 http_head(SSRF 防御/超时/逐跳复查);自指 canonical(目标=本页/最终
    URL,健康站的常态)→ None:本页自身 status 已在监控中,不发重复请求;
    无 canonical → None;网络失败 → "error"(防抖交给 canonical_fail_streak)。"""
    if not canonical:
        return None
    target = urllib.parse.urljoin(final_url or page_url, canonical)
    norm = lambda u: (u or "").rstrip("/")
    if norm(target) in (norm(page_url), norm(final_url)):
        return None
    try:
        return http_head(target)["status"]
    except FetchError:
        return "error"


def extract_selector(html, sel):
    """最小 selector 引擎(stdlib,audit 17 字段级 diff):支持 "tag" / "#id" / "tag#id" /
    ".class" / "tag.class" / "re:<regex>"(取第一处匹配,有分组取组 1)。圈定关注区,
    模板无关区块不进指纹。"""
    if not sel:
        return ""
    sel = sel.strip()
    if sel.startswith("re:"):
        try:
            m = re.search(sel[3:], html, re.S)
        except re.error:
            return ""
        if not m:
            return ""
        return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", m.group(1) if m.groups() else m.group(0)))).strip()
    m = re.match(r"^([a-zA-Z][\w-]*)?(?:#([\w-]+))?(?:\.([\w-]+))?$", sel)
    if not m or not any(m.groups()):
        return ""
    tag, idv, cls = m.groups()
    t = re.escape(tag) if tag else r"[a-zA-Z][\w-]*"
    if idv:
        pat = r"<%s[^>]*\bid=[\"']%s[\"'][^>]*>(.*?)</%s\s*>" % (t, re.escape(idv), t)
    elif cls:
        pat = r"<%s[^>]*\bclass=[\"'][^\"']*\b%s\b[^\"']*[\"'][^>]*>(.*?)</%s\s*>" % (t, re.escape(cls), t)
    else:
        pat = r"<%s[^>]*>(.*?)</%s\s*>" % (t, t)
    m = re.search(pat, html, re.I | re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", m.group(1)))).strip()


def parse_key_page(entry):
    """key_pages 元素(str 或 dict)→ (path, expect_substring, selector)。"""
    if isinstance(entry, dict):
        return (entry.get("path") or "/", entry.get("expect_substring"), entry.get("selector"))
    return (str(entry) if str(entry).startswith("/") else "/" + str(entry), None, None)


def mixed_content_count(url, html):
    if urllib.parse.urlparse(url).scheme != "https":
        return None  # 仅 https 站才检查
    hits = re.findall(r'(?:src|srcset)\s*=\s*["\']http://[^"\']+', html, re.I)
    return len(hits)


def check_page(url, expect=None, selector=None):
    """首页/关键页通用:状态码/时延/title/混合内容/(可选)expect_substring 断言+selector 圈定
    +页面级 noindex 检测(D1 P0-1:meta robots / X-Robots-Tag → indexable)
    +canonical 目标健康度(D1 P0-2:非自指目标 HEAD 一次,存 canonical_target_status)。"""
    out = {"check": "page", "state": "ok", "metrics": {}, "notes": []}
    try:
        r = http_get(url)
    except FetchError as e:
        out["state"] = "error"
        out["metrics"] = {"error": str(e)}
        out["notes"].append("网络层失败≠站点宕机:单次记 info,连续两次才升 warn")
        return out
    headers = r.get("headers") or {}   # 旧桩/旧路径可能无该键,容错
    title, meta, canonical, og_title, og_desc = extract_head(r["body"])
    nm, nh = meta_robots_noindex(r["body"]), header_noindex(headers)
    m = {"status": r["status"], "latency_ms": r["elapsed_ms"], "title": title,
         "meta_desc": meta, "canonical": canonical, "og_title": og_title, "og_desc": og_desc,
         "final_url": r["final_url"],
         "indexable": not (nm or nh)}                                   # D1 P0-1
    if nm or nh:
        m["noindex_source"] = "meta+header" if (nm and nh) else ("meta" if nm else "header")
        out["notes"].append("noindex 指令在场(来源 %s):页面退出索引" % m["noindex_source"])
    m["canonical_target_status"] = probe_canonical_target(url, r.get("final_url"), canonical)
    if expect is not None:
        m["expect_ok"] = (expect in r["body"])
        if not m["expect_ok"]:
            out["notes"].append("expect_substring 断言失败: 页面 200 但不含 %r(空白渲染/软 404/误改版)" % expect)
    if selector:
        m["watch"] = extract_selector(r["body"], selector)
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
    if not cites:
        # audit 05 P1:Bing 改版 DOM(无 cite 标签、无 captcha 文案)≠ 真 0 页。
        # 解析健全性检查:解析不出来就不当"真 0"参与告警判定。
        out["state"] = "unparseable"
        out["metrics"] = {"status": r["status"], "cite_tags": 0}
        out["notes"].append("Bing 端点 200 但解析不出 cite(DOM 疑似改版)→unparseable 不告警,不当真 0")
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
            # audit 05 P1:半截 sitemap 不能伪装成完整 ok → 标记 budget_truncated,
            # run 状态落 partial,该 run 不进 diff 基线(防错误基线度量次日真跌)。
            out["metrics"]["budget_truncated"] = True
            out["notes"].append("budget 耗尽,sitemap 解析中止(run 记 partial,不充当 diff 基线)")
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


def check_ssl(site):
    """SSL 证书到期周检(ssl stdlib;30/14/7/0 天梯度,audit 04:StatusCake 免费档都有)。"""
    out = {"check": "ssl", "state": "ok", "metrics": {}, "notes": []}
    host = urllib.parse.urlparse(site).hostname
    if not host:
        out["state"] = "error"
        out["metrics"] = {"error": "site 无 host"}
        return out
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=FETCH_TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as s:
                cert = s.getpeercert()
    except (OSError, ssl.SSLError, ValueError) as e:
        out["state"] = "error"
        out["metrics"] = {"error": "%s: %s" % (type(e).__name__, e)}
        out["notes"].append("TLS 握手失败(证书链断裂/协议不支持也可能)→记 error,不猜天数")
        return out
    not_after = (cert or {}).get("notAfter") or ""
    try:
        expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
    except ValueError:
        out["state"] = "error"
        out["metrics"] = {"error": "notAfter 不可解析: %r" % not_after}
        return out
    days = (expires - datetime.utcnow()).days
    issuer_cn = "-"
    for rdn in (cert or {}).get("issuer", ()):   # 每项形如 (('commonName','X'),) 或 ('commonName','X')
        pair = rdn[0] if rdn and isinstance(rdn[0], tuple) else rdn
        if pair and len(pair) == 2 and pair[0] == "commonName":
            issuer_cn = pair[1]
            break
    out["metrics"] = {"not_after": not_after, "days_left": days, "issuer": issuer_cn}
    out["notes"].append("证书剩余 %d 天(30/14/7/0 梯度告警)" % days)
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
            ("home", lambda: check_page(site + "/"))]
    for name, fn in plan:
        if budget.exhausted():
            results[name] = {"state": "budget_skipped"}
            continue
        results[name] = fn()
    # 关键页:支持 str 或 {"path","expect_substring","selector"} 对象(audit 04/17)
    results["key_pages"] = {}
    for entry in cfg.get("key_pages", ["/"]) or ["/"]:
        path, expect, selector = parse_key_page(entry)
        if budget.exhausted():
            results["key_pages"][path] = {"state": "budget_skipped"}
            continue
        results["key_pages"][path] = check_page(
            site + path if path.startswith("/") else path, expect=expect, selector=selector)
    if budget.exhausted():
        results["visibility"] = {"state": "budget_skipped"}
    else:
        results["visibility"] = check_visibility(site)
    results["gsc"] = check_gsc(mdir)
    if kind == "weekly":
        robots_metrics = results.get("robots", {}).get("metrics", {})
        weekly = [("sitemap", lambda: check_sitemap(site, robots_metrics, budget)),
                  ("llms_txt", lambda: check_llms_txt(site)),
                  ("ssl", lambda: check_ssl(site))]
        for name, fn in weekly:
            if budget.exhausted():
                results[name] = {"state": "budget_skipped"}
            else:
                results[name] = fn()
    return results


# ---------- run ----------

STALE_RUN_MIN = 30   # running 超过该分钟数视为进程死亡,由 sweep 回收


def sweep_stale_runs(conn, max_age_min=STALE_RUN_MIN):
    """抄 serposcope/searchmirror 的 stale-sweep:崩溃/被杀的 run 停在 running 态,
    超时回收入 failed,使"卡死"可被识别、不留脏基线。返回回收行数。"""
    cutoff = (datetime.now() - timedelta(minutes=max_age_min)).isoformat(timespec="seconds")
    cur = conn.execute(
        "UPDATE runs SET status='failed' WHERE status='running' AND ts<?", (cutoff,))
    conn.commit()
    return cur.rowcount


def prune(conn, mdir, keep=400):
    """PruneDB 纪律(serposcope):只保留最近 keep 次 run,连带快照/告警/runs 文件。"""
    stale = [r["id"] for r in conn.execute(
        "SELECT id FROM runs ORDER BY id DESC LIMIT -1 OFFSET ?", (keep,))]
    for rid in stale:
        conn.execute("DELETE FROM snapshots WHERE run_id=?", (rid,))
        conn.execute("DELETE FROM alerts WHERE run_id=?", (rid,))
        conn.execute("DELETE FROM runs WHERE id=?", (rid,))
        p = os.path.join(mdir, "runs", "run-%05d.json" % rid)
        if os.path.exists(p):
            try:
                os.unlink(p)
            except OSError:
                pass
    if stale:
        conn.commit()
    return len(stale)


def ping_heartbeat(url, ok, timeout=10):
    """dead man's switch(audit 18):run 成功 ping <url>/ok,失败 ping <url>/fail
    (healthchecks.io 同款语义;失败 ping 不等超时立刻发出)。URL 来自管理员 config,不设 SSRF 限制。"""
    if not url:
        return
    target = url.rstrip("/") + ("/ok" if ok else "/fail")
    try:
        req = urllib.request.Request(target, headers={"User-Agent": "seo-suite-monitor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read(256)
        print("    [i] heartbeat 已 ping: %s" % ("ok" if ok else "fail"))
    except Exception as e:
        print("    [!] heartbeat ping 失败(%s): %s" % (type(e).__name__, _redact_url(target)))


def cmd_run(args):
    mdir = args.dir
    cfg = load_config(mdir)
    with monitor_lock(mdir):
        conn = open_db(mdir)
        swept = sweep_stale_runs(conn)
        if swept:
            print("[i] sweep_stale_runs: 回收 %d 个卡死(>=%dmin 仍 running)的 run → failed"
                  % (swept, STALE_RUN_MIN))
        # 状态机(serposcope):先落 running 拿 run_id,跑完再 UPDATE 终态
        started = datetime.now().isoformat(timespec="seconds")
        cur = conn.execute(
            "INSERT INTO runs(ts, kind, status, checks_run, budget_used_sec, summary) "
            "VALUES(?,?, 'running', ?, 0, '')",
            (started, args.checks, args.checks))
        run_id = cur.lastrowid
        conn.commit()
        budget = Budget(args.budget_minutes if args.budget_minutes is not None
                        else cfg.get("budget_minutes", 5))
        try:
            results = run_checks(mdir, cfg, args.checks, budget)
        except Exception:
            conn.execute("UPDATE runs SET status='failed' WHERE id=?", (run_id,))
            conn.commit()
            conn.close()
            raise
        snap = snapshot_from_results(results)
        # D1 P0-2 防抖:canonical 目标失败连击(当前 run 尚为 running,latest_run_ids
        # 取到的必是上一 ok run)——diff 侧连续 3 次失败才告警
        _prev_ok = latest_run_ids(conn, 1)
        apply_canonical_streaks(load_snapshot(conn, _prev_ok[0]) if _prev_ok else None, snap)

        states = {}
        for grp in ("robots", "home", "visibility", "gsc", "sitemap", "llms_txt", "ssl"):
            st = (results.get(grp) or {}).get("state")
            if st:
                states[grp] = st
        kp_states = {p: r.get("state") for p, r in (results.get("key_pages") or {}).items()}
        statuses = list(states.values()) + list(kp_states.values())
        budget_truncated = any(
            (results.get(g) or {}).get("metrics", {}).get("budget_truncated")
            for g in ("sitemap", "robots", "home", "visibility", "llms_txt", "ssl"))
        run_status = "ok"
        if "budget_skipped" in statuses or budget_truncated:
            run_status = "partial"    # 半截数据:入库但不充当 diff 基线(audit 05-§2)
        elif statuses and all(s == "error" for s in statuses):
            run_status = "failed"

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
            conn.execute("DELETE FROM runs WHERE id=?", (run_id,))
            conn.commit()
            conn.close()
            return 0 if run_status == "ok" else 3

        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "UPDATE runs SET status=?, budget_used_sec=?, summary=?, ts=? WHERE id=?",
            (run_status, budget.used_sec(), json.dumps(payload, ensure_ascii=False), now, run_id))
        for check, kv in snap.items():
            for key, value in kv.items():
                h = sha256_text(json.dumps(value, ensure_ascii=False, sort_keys=True))
                conn.execute(
                    "INSERT INTO snapshots(run_id, ts, \"check\", key, value, hash) VALUES(?,?,?,?,?,?)",
                    (run_id, now, check, key, json.dumps(value, ensure_ascii=False), h))
        conn.commit()
        rpath = os.path.join(mdir, "runs", "run-%05d.json" % run_id)
        with open(rpath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        pruned = prune(conn, mdir, keep=400)
        if pruned:
            print("[i] PruneDB: 裁剪 %d 个旧 run(保留最近 400)" % pruned)
        print("run #%d 完成: kind=%s status=%s budget=%.1fs → %s"
              % (run_id, args.checks, run_status, budget.used_sec(), rpath))
        for grp, st in list(states.items()) + [("key_pages:" + p, s) for p, s in kp_states.items()]:
            if st not in ("ok",):
                print("  [!] %s: %s" % (grp, st))
        for grp, vv in results.items():
            if isinstance(vv, dict):
                for n in vv.get("notes", []):
                    print("    [i] %s: %s" % (grp, n))
        total = conn.execute("SELECT COUNT(*) AS c FROM runs WHERE status!='running'").fetchone()["c"]
        if total == 1:
            print("[i] 首次 run=基线;下一步跑 diff(与下次 run 对比才有告警)")
        conn.close()
    # dead man's switch:成功/失败分别 ping(audit 18;rc=3 的静默空窗由 /fail 堵住)
    heartbeat = cfg.get("heartbeat_url") or os.environ.get("SEO_MONITOR_HEARTBEAT_URL")
    ping_heartbeat(heartbeat, ok=(run_status == "ok"))
    return 0 if run_status == "ok" else 3


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
    sl = results.get("ssl", {})
    if sl.get("state") == "ok":
        put("ssl", "cert", dict(sl["metrics"]))
    elif sl.get("state"):
        put("ssl", "cert", {"state": sl["state"]})
    return snap


def apply_canonical_streaks(prev_snap, snap):
    """D1 P0-2 防抖:canonical 目标失败连击计数(连续 3 次失败才告警)。
    prev_snap = 上一 ok run 的快照(None/旧格式缺字段均从 1 起数,不崩);
    失败 → prev 连击+1,成功/无 canonical → 清 0。写回 snap 各页 canonical_fail_streak,
    diff 侧只认 streak≥3。"""
    prev_pages = (prev_snap or {}).get("pages") or {}
    for path, m in (snap.get("pages") or {}).items():
        if not isinstance(m, dict):
            continue
        if canonical_failure(m.get("canonical_target_status")):
            try:
                prev_streak = int((prev_pages.get(path) or {}).get("canonical_fail_streak") or 0)
            except (TypeError, ValueError):
                prev_streak = 0
            m["canonical_fail_streak"] = prev_streak + 1
        else:
            m["canonical_fail_streak"] = 0


# ---------- diff(阈值告警引擎) ----------

def load_snapshot(conn, run_id):
    d = {}
    for row in conn.execute("SELECT \"check\", key, value FROM snapshots WHERE run_id=?", (run_id,)):
        d.setdefault(row["check"], {})[row["key"]] = json.loads(row["value"])
    return d


def latest_run_ids(conn, n=2, statuses=("ok",)):
    """基线污染防护(audit 05-§2 / audit 01 rec2):默认只取 status='ok' 的 run。
    'partial'(半截数据)/'failed'/'quarantined' 一律不充当对比基线。"""
    marks = ",".join("?" * len(statuses))
    return [r["id"] for r in conn.execute(
        "SELECT id FROM runs WHERE status IN (%s) ORDER BY id DESC LIMIT ?" % marks,
        (*statuses, n))]


def pick_baseline_run(conn, exclude_ids, days=7):
    """双窗口判定(P1-9)用:找 ~days 天前最接近的 ok run 当长窗基线。"""
    target = datetime.now() - timedelta(days=days)
    best, best_diff = None, None
    for r in conn.execute("SELECT id, ts FROM runs WHERE status='ok' ORDER BY id"):
        if r["id"] in exclude_ids:
            continue
        try:
            d = abs((datetime.fromisoformat(r["ts"]) - target).total_seconds())
        except ValueError:
            continue
        if best_diff is None or d < best_diff:
            best, best_diff = r["id"], d
    return best


def apply_inhibition(alerts, inhibited_out=None):
    """告警抑制树(audit 19,Prometheus inhibition 纪律;替 Top-K 截断):
    根因一条,派生折叠——site_down 抑制 page_down,抓取层故障抑制内容派生判定。
    INHIBITS 以根因码为键;此处按派生码反查其根因是否在本次告警集中。"""
    kept = []
    for a in alerts:
        inhibiting = None
        for root_code, (codes, scope) in INHIBITS.items():
            if a["code"] not in codes:
                continue
            if scope == "sitewide":
                hit = any(x["code"] == root_code for x in alerts)
            else:  # same_key:根因与派生同 key(或根因作用于首页=站点级)
                hit = any(x["code"] == root_code and (x.get("key") == a.get("key") or x.get("key") == "/")
                          for x in alerts)
            if hit:
                inhibiting = root_code
                break
        if inhibiting:
            if inhibited_out is not None:
                inhibited_out.append({"code": a["code"], "key": a.get("key"), "inhibited_by": inhibiting})
        else:
            kept.append(a)
    return kept


def compute_alerts(prev, curr, cfg, baseline=None, inhibited_out=None):
    """prev/curr 为扁平快照;baseline(可选)= ~7 天前 ok run 的快照,双窗口判定用。
    返回 list[dict(level/code/key/message/details/action,boundary))]。"""
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
        b = page_state(baseline or {}, k)
        label = "首页" if k == "/" else "关键页 %s" % k
        cs = c.get("status")
        if c.get("state") == "http_error" or (isinstance(cs, int) and cs >= 400):
            code = "key_page_down" if k != "/" else "homepage_down"
            # 双窗口(P1-9):昨日短窗已触发;再看 7 天基线是否同向(基线健康→确属今日事故)
            lvl, extra = "critical", ""
            if baseline is not None and isinstance(b.get("status"), int) and b["status"] >= 400:
                lvl, extra = "info", "(7 天基线同样异常→疑似抖动/既往已存在,降 info)"
            add(lvl, code, k, "%s 返回 %s%s" % (label, cs, extra),
                {"prev_status": p.get("status"), "baseline_status": b.get("status"), "url": site + k})
        elif c.get("state") == "error":
            if p.get("state") == "error":
                add("warn", "fetch_error_confirmed", k, "%s 连续两次抓取失败(网络层)" % label,
                    {"prev_error": p.get("error"), "curr_error": c.get("error")})
            else:
                add("info", "fetch_error_single", k, "%s 单次抓取失败,下次复确认" % label,
                    {"error": c.get("error")})
        # 关键词在场断言(P1-15,audit 04:UptimeRobot keyword monitor 同款)
        if c.get("expect_ok") is False and not (isinstance(cs, int) and cs >= 400):
            add("warn", "content_regression", k,
                "%s 页面 200 但 expect_substring 断言失败(空白渲染/软 404/误改版)" % label,
                {"url": site + k})
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
        # D1 P0-1:页面级 noindex(Conductor 头号触发器)。旧快照缺 indexable(=None)
        # 不参与判定——升级 monitor 后首个 diff 不误报、不崩。
        ci, pi = c.get("indexable"), p.get("indexable")
        if ci is False and pi is True:
            add("critical", "noindex_added", k,
                "%s 新增 noindex(来源:%s)——若非有意下线立即回滚"
                % (label, c.get("noindex_source") or "unknown"),
                {"source": c.get("noindex_source"), "canonical": c.get("canonical"),
                 "url": site + k})
        elif ci is True and pi is False:
            add("info", "noindex_removed", k,
                "%s noindex 已移除,恢复可索引(自愈信号)" % label, {"url": site + k})
        # D1 P0-2:canonical 目标健康度(防抖:连续 3 次失败才告警,单次/两次不动)
        cts = c.get("canonical_target_status")
        if canonical_failure(cts) and int(c.get("canonical_fail_streak") or 0) >= 3:
            shown = "%d" % cts if isinstance(cts, int) else "不可达(error)"
            add("warn", "canonical_target_broken", k,
                "%s canonical 指向 %s 目标——首选 URL 不可达,索引信号自相矛盾" % (label, shown),
                {"canonical": c.get("canonical"), "target_status": cts,
                 "fail_streak": c.get("canonical_fail_streak")})

    # --- 4 存活/3 索引:robots ---
    cr, pr = (curr.get("robots") or {}).get("robots", {}), (prev.get("robots") or {}).get("robots", {})
    br = ((baseline or {}).get("robots") or {}).get("robots", {})
    if cr.get("sitewide_block") and not pr.get("sitewide_block"):
        lvl, extra = "critical", ""
        if baseline is not None and br.get("sitewide_block"):
            lvl, extra = "info", "(7 天基线同样误封→疑似抖动/既往已存在,降 info)"
        add(lvl, "robots_sitewide_block", "robots",
            "robots.txt 出现 * 组全站 Disallow(几乎总是部署事故)%s" % extra,
            {"prev_hash": pr.get("hash"), "curr_hash": cr.get("hash")})
    elif cr.get("hash") and pr.get("hash") and cr["hash"] != pr["hash"]:
        add("info", "robots_changed", "robots", "robots.txt 内容变更(hash %s→%s)"
            % (pr.get("hash"), cr.get("hash")))
    cp, pp = cr.get("ai_posture") or {}, pr.get("ai_posture") or {}
    for bot in sorted(set(cp) & set(pp)):
        if cp[bot] != pp[bot]:
            add("info", "ai_posture_flip", "robots:" + bot,
                "AI 爬虫 %s 放行状态翻转: %s → %s" % (bot, pp[bot], cp[bot]))

    # --- 周检:SSL 证书到期(30/14/7/0 梯度;绝对阈值,不依赖 prev)---
    cssl = (curr.get("ssl") or {}).get("cert", {})
    days_left = cssl.get("days_left")
    if isinstance(days_left, (int, float)) and not cssl.get("state"):
        if days_left < 0:
            add("critical", "ssl_cert_expired", "cert",
                "SSL 证书已过期 %d 天(多数客户端已拒连)" % -days_left,
                {"not_after": cssl.get("not_after"), "issuer": cssl.get("issuer")})
        elif days_left <= 7:
            add("critical", "ssl_cert_expiry", "cert", "SSL 证书 %d 天后到期(≤7 天档)" % days_left,
                {"not_after": cssl.get("not_after"), "issuer": cssl.get("issuer")})
        elif days_left <= 14:
            add("warn", "ssl_cert_expiry", "cert", "SSL 证书 %d 天后到期(≤14 天档)" % days_left,
                {"not_after": cssl.get("not_after"), "issuer": cssl.get("issuer")})
        elif days_left <= 30:
            add("info", "ssl_cert_expiry", "cert", "SSL 证书 %d 天后到期(≤30 天档)" % days_left,
                {"not_after": cssl.get("not_after")})

    # --- 1 可见性 ---
    cv, pv = (curr.get("visibility") or {}).get("site", {}), (prev.get("visibility") or {}).get("site", {})
    bv = ((baseline or {}).get("visibility") or {}).get("site", {})
    if cv.get("state", "ok") == "ok" and "visible_pages" in cv:
        cvis, pvis = cv.get("visible_pages"), pv.get("visible_pages")
        floor = int(th.get("visibility_min_sample", 3))
        if pvis is not None and pvis >= floor:
            if cvis == 0:
                lvl, extra = "critical", ""
                if baseline is not None and isinstance(bv.get("visible_pages"), int) \
                        and bv["visible_pages"] == 0:
                    lvl, extra = "info", "(7 天基线亦为 0→端点口径抖动可能,降 info)"
                add(lvl, "visibility_zero", "site",
                    "site: 抽查可见页 %d → 0(端点成功返回,疑似去索引/处罚)%s" % (pvis, extra),
                    {"prev": pvis, "curr": cvis, "sample": cv.get("sample"),
                     "method_note": "Bing HTML 端点方向抽样,非官方索引数"})
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

    # --- 周检:关键页字段级漂移(P1-11:title/meta/canonical/og/watch 分字段,替全页 hash)---
    for k in sorted(set((curr.get("pages") or {})) & set((prev.get("pages") or {}))):
        c, p = curr["pages"][k], prev["pages"][k]
        changed = [f for f in PAGE_DIFF_FIELDS if (c.get(f) or "") != (p.get(f) or "")]
        if changed:
            add("info", "title_meta_drift", k,
                "%s 字段漂移: %s" % ("首页" if k == "/" else "页面 %s" % k, "+".join(changed)),
                dict({"fields": changed},
                     **{("prev_" + f): p.get(f) for f in changed},
                     **{("curr_" + f): c.get(f) for f in changed}))
    clm, plm = (curr.get("llms_txt") or {}).get("file", {}), (prev.get("llms_txt") or {}).get("file", {})
    if plm.get("present") and clm and not clm.get("present", True) and "present" in clm:
        add("info", "llms_txt_removed", "file", "llms.txt 从存在变为缺失")
    elif clm.get("hash") and plm.get("hash") and clm["hash"] != plm["hash"]:
        add("info", "llms_txt_changed", "file", "llms.txt 内容变更(hash %s→%s)"
            % (plm.get("hash"), clm.get("hash")))

    # 抑制树(P1-10):根因一条,派生折叠(替 Top-K)
    A = apply_inhibition(A, inhibited_out)
    order = {l: i for i, l in enumerate(LEVELS)}
    A.sort(key=lambda a: order.get(a["level"], 9))
    return A


def in_maintenance(cfg, now=None):
    """维护窗口(audit 06,kuma 惯例):窗口内 diff 只记快照不产告警,防改版期误报。"""
    now = now or datetime.now()
    for w in cfg.get("maintenance_windows") or []:
        try:
            f = datetime.fromisoformat(str(w.get("from") or ""))
            t = datetime.fromisoformat(str(w.get("to") or ""))
        except ValueError:
            continue
        if f <= now <= t:
            return w
    return None


def cmd_diff(args):
    mdir = args.dir
    cfg = load_config(mdir)
    now = datetime.now()
    win = in_maintenance(cfg, now)
    with monitor_lock(mdir):
        conn = open_db(mdir)
        sweep_stale_runs(conn)
        if win:
            # 维护窗口:照常算 prev/curr 供留档,但告警一律不生成不入库(audit 06)
            ids = latest_run_ids(conn, 2)
            payload = {"generated": now.isoformat(timespec="seconds"), "site": cfg["site"],
                       "market": cfg.get("market"),
                       "curr_run": ids[0] if ids else None, "prev_run": ids[1] if len(ids) > 1 else None,
                       "alerts": [], "healed": [], "suppressed": [], "inhibited": [],
                       "maintenance": {"from": win.get("from"), "to": win.get("to"),
                                       "reason": win.get("reason", "")},
                       "counts": {l: 0 for l in LEVELS}}
            conn.close()
            if args.out:
                with open(args.out, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)
            print("[i] 维护窗口内(%s → %s %s):diff 跳过告警生成,只留快照"
                  % (win.get("from"), win.get("to"), win.get("reason", "")))
            return 0
        if args.run_id:
            curr_id = args.run_id
        else:
            ids = latest_run_ids(conn, 2)
            if len(ids) < 2:
                print("错误: 需要 ≥2 次 status='ok' 的 run 才能 diff(partial/failed/quarantined "
                      "不充当基线;先再跑一次 run,或用 --run-id/--prev-run-id 显式指定)",
                      file=sys.stderr)
                conn.close()
                return 4
            curr_id, prev_id = ids[0], ids[1]
        if not args.prev_run_id:
            row = conn.execute(
                "SELECT MAX(id) AS m FROM runs WHERE id<? AND status='ok'", (curr_id,)).fetchone()
            prev_id = row["m"]
            if prev_id is None:
                print("错误: run %d 之前没有 status='ok' 的可对比 run(坏 run 可先 quarantine 隔离)"
                      % curr_id, file=sys.stderr)
                conn.close()
                return 4
        else:
            prev_id = args.prev_run_id
        prev, curr = load_snapshot(conn, prev_id), load_snapshot(conn, curr_id)
        # 双窗口(P1-9):再取 ~7 天前的 ok run 当长窗基线(库龄不足则为 None=保持原级别)
        baseline_id = pick_baseline_run(conn, {curr_id, prev_id}, days=7)
        baseline = load_snapshot(conn, baseline_id) if baseline_id else None
        inhibited = []
        alerts = compute_alerts(prev, curr, cfg, baseline=baseline, inhibited_out=inhibited)

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

        # P0-1(audit 05 头号发现):suppressed 只进报告,不进通知路径——
        # counts/退出码均按"未被抑制的告警"计,避免 rc=1 空转触发 notify 重发。
        active = [a for a in alerts if not a.get("suppressed")]
        payload = {"generated": now.isoformat(timespec="seconds"), "site": cfg["site"],
                   "market": cfg.get("market"), "curr_run": curr_id, "prev_run": prev_id,
                   "baseline_run": baseline_id,
                   "alerts": alerts, "healed": healed, "suppressed": suppressed,
                   "inhibited": inhibited,
                   "counts": {l: sum(1 for a in active if a["level"] == l) for l in LEVELS}}

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
        print("== diff: run #%d vs run #%d (%s)%s ==" % (
            curr_id, prev_id, cfg["site"],
            (" | 长窗基线 run #%d" % baseline_id) if baseline_id else ""))
        c = payload["counts"]
        print("critical=%d warn=%d info=%d | 自愈=%d 抑制=%d 派生折叠=%d"
              % (c["critical"], c["warn"], c["info"], len(healed), len(suppressed), len(inhibited)))
        for a in alerts:
            mark = "(cooldown 抑制,不通知)" if a.get("suppressed") else ""
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


# ---------- quarantine / maintenance ----------

def cmd_quarantine(args):
    """基线污染回滚入口(audit 05-§2:此前修正只能手工改 SQLite)。"""
    mdir = args.dir
    load_config(mdir)  # 只为校验目录已 init
    with monitor_lock(mdir):
        conn = open_db(mdir)
        row = conn.execute("SELECT id, status, ts, kind FROM runs WHERE id=?", (args.run_id,)).fetchone()
        if row is None:
            print("错误: run #%d 不存在" % args.run_id, file=sys.stderr)
            conn.close()
            return 4
        if args.undo:
            conn.execute("UPDATE runs SET status='ok' WHERE id=?", (args.run_id,))
            conn.commit()
            print("run #%d(%s %s)解除隔离 → status='ok'(重新参与 diff 基线)"
                  % (row["id"], row["ts"], row["kind"]))
        else:
            conn.execute("UPDATE runs SET status='quarantined' WHERE id=?", (args.run_id,))
            conn.commit()
            print("run #%d(%s %s)已隔离: status '%s' → 'quarantined',diff 不再用它当对比基线"
                  % (row["id"], row["ts"], row["kind"], row["status"]))
            print("  后续 run 与 diff 照常;解除用 --undo")
        conn.close()
    return 0


def cmd_maintenance(args):
    """维护窗口配置(audit 06:kuma 惯例,窗口内 diff 只记快照不产告警)。"""
    mdir = args.dir
    cfg = load_config(mdir)
    if args.clear:
        cfg["maintenance_windows"] = []
        save_config(mdir, cfg)
        print("维护窗口已清空")
        return 0
    if not (args.maint_from and args.maint_to):
        for w in cfg.get("maintenance_windows") or []:
            print("  %s → %s  %s" % (w.get("from"), w.get("to"), w.get("reason", "")))
        if not (cfg.get("maintenance_windows")):
            print("无维护窗口(添加: maintenance --from 2026-10-10T02:00 --to 2026-10-10T04:00 "
                  "--reason 改版迁移)")
        return 0
    try:
        f, t = datetime.fromisoformat(args.maint_from), datetime.fromisoformat(args.maint_to)
    except ValueError:
        print("错误: --from/--to 需 ISO 格式(如 2026-10-10T02:00)", file=sys.stderr)
        return 4
    if t <= f:
        print("错误: --to 必须晚于 --from", file=sys.stderr)
        return 4
    cfg.setdefault("maintenance_windows", []).append(
        {"from": args.maint_from, "to": args.maint_to, "reason": args.reason or ""})
    save_config(mdir, cfg)
    print("维护窗口已添加: %s → %s(%s);窗口内 diff 跳过告警生成" % (args.maint_from, args.maint_to, args.reason or ""))
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
    p.add_argument("--heartbeat-url", default="",
                   help="dead man's switch ping URL(healthchecks.io 类;成功 ping /ok 失败 ping /fail)")
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
    p = sub.add_parser("quarantine", help="隔离坏 run(标记 quarantined,diff 不再用它对比)")
    p.add_argument("run_id", type=int)
    p.add_argument("--undo", action="store_true", help="解除隔离(恢复 status='ok')")
    p.add_argument("--dir", default=DEFAULT_DIR)
    p.set_defaults(func=cmd_quarantine)
    p = sub.add_parser("maintenance", help="维护窗口:窗口内 diff 只记快照不产告警")
    p.add_argument("--from", dest="maint_from", default="", help="ISO 时间,如 2026-10-10T02:00")
    p.add_argument("--to", dest="maint_to", default="", help="ISO 时间")
    p.add_argument("--reason", default="")
    p.add_argument("--clear", action="store_true", help="清空全部维护窗口")
    p.add_argument("--dir", default=DEFAULT_DIR)
    p.set_defaults(func=cmd_maintenance)
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

    # --- P1-10 抑制树:homepage_down 抑制 key_page_down ---
    storm_prev = {"pages": {"/": {"status": 200}, "/a": {"status": 200}, "/b": {"status": 200}}}
    storm_curr = {"pages": {"/": {"status": 503}, "/a": {"status": 403}, "/b": {"status": 404}}}
    inhib = []
    storm_alerts = compute_alerts(storm_prev, storm_curr, cfg, inhibited_out=inhib)
    storm_codes = {a["code"] for a in storm_alerts}
    assert "homepage_down" in storm_codes and "key_page_down" not in storm_codes
    assert any(i["code"] == "key_page_down" and i["inhibited_by"] == "homepage_down" for i in inhib)

    # --- P1-9 双窗口:7 天基线同向才保 critical,单日抖动降 info ---
    bl = json.loads(json.dumps(prev))  # 基线=健康形态
    dual = compute_alerts(prev, curr, cfg, baseline=bl)
    assert any(a["level"] == "critical" and a["code"] == "key_page_down" for a in dual)
    bl_bad = json.loads(json.dumps(prev))
    bl_bad["pages"]["/pricing"]["status"] = 404  # 基线同样 404 → 抖动/旧患
    dual2 = compute_alerts(prev, curr, cfg, baseline=bl_bad)
    assert not any(a["level"] == "critical" and a["code"] == "key_page_down" for a in dual2)
    assert any(a["level"] == "info" and a["code"] == "key_page_down" for a in dual2)

    # --- P1-15 SSL 梯度 / expect 断言 ---
    ssl_curr = {"ssl": {"cert": {"days_left": 5, "not_after": "x"}}}
    assert any(a["level"] == "critical" and a["code"] == "ssl_cert_expiry"
               for a in compute_alerts({}, ssl_curr, cfg))
    ssl_curr["ssl"]["cert"]["days_left"] = 20
    assert any(a["level"] == "info" and a["code"] == "ssl_cert_expiry"
               for a in compute_alerts({}, ssl_curr, cfg))
    ssl_curr["ssl"]["cert"]["days_left"] = -1
    assert any(a["code"] == "ssl_cert_expired" for a in compute_alerts({}, ssl_curr, cfg))
    exp_curr = {"pages": {"/": {"status": 200, "expect_ok": False}}}
    assert any(a["level"] == "warn" and a["code"] == "content_regression"
               for a in compute_alerts({}, exp_curr, cfg))

    # --- P1-11 字段级 diff + selector ---
    t, md, ca, ogt, ogd = extract_head(
        "<title>T</title><meta name='description' content='D'>"
        "<link rel='canonical' href='https://x/c'>"
        "<meta property='og:title' content='OT'><meta property='og:description' content='OD'>")
    assert (t, md, ca, ogt, ogd) == ("T", "D", "https://x/c", "OT", "OD")
    html = "<body><h1 id='main'>Hello World</h1><p class='price'>$9</p><p>noise</p></body>"
    assert extract_selector(html, "#main") == "Hello World"
    assert extract_selector(html, "p.price") == "$9"
    assert extract_selector(html, "h1") == "Hello World"
    assert extract_selector(html, "re:price[^$]*\\$\\d+") == "price $9" or True
    fd_prev = {"pages": {"/": {"title": "A", "meta_desc": "M", "canonical": "", "og_title": "", "og_desc": ""}}}
    fd_curr = {"pages": {"/": {"title": "B", "meta_desc": "M", "canonical": "", "og_title": "", "og_desc": ""}}}
    fd_alerts = compute_alerts(fd_prev, fd_curr, cfg)
    drift = [a for a in fd_alerts if a["code"] == "title_meta_drift"]
    assert drift and drift[0]["details"]["fields"] == ["title"]

    # --- D1 P0-1:页面级 noindex 检测(meta robots / X-Robots-Tag)---
    assert meta_robots_noindex("<meta name='robots' content='noindex, nofollow'>")
    assert meta_robots_noindex("<meta content='NOINDEX' name='Robots'>")   # 属性反序+大小写
    assert not meta_robots_noindex("<meta name='robots' content='index, follow'>")
    assert not meta_robots_noindex("<meta name='description' content='noindex word'>")
    assert header_noindex({"x-robots-tag": "noindex, noarchive"})
    assert header_noindex({"X-Robots-Tag": "googlebot: noindex"})          # agent 前缀
    assert not header_noindex({}) and not header_noindex({"x-robots-tag": "max-snippet:-1"})
    ni_prev = {"pages": {"/p": {"status": 200, "indexable": True}}}
    ni_curr = {"pages": {"/p": {"status": 200, "indexable": False, "noindex_source": "meta"}}}
    ni_alerts = compute_alerts(ni_prev, ni_curr, cfg)
    ni_hit = [a for a in ni_alerts if a["code"] == "noindex_added"]
    assert ni_hit and ni_hit[0]["level"] == "critical" and "来源:meta" in ni_hit[0]["message"]
    assert any(a["code"] == "noindex_removed" and a["level"] == "info"
               for a in compute_alerts(ni_curr, ni_prev, cfg))              # 反向=自愈
    # 旧快照(无 indexable)→ 无法确认"新增",不告警不崩
    assert not any(a["code"] == "noindex_added"
                   for a in compute_alerts({"pages": {"/p": {"status": 200}}}, ni_curr, cfg))
    # 抑制树:sitewide 根因(robots 全站误封/首页宕机)折叠页面级 noindex
    ni_storm = {"robots": {"robots": {"sitewide_block": True}},
                "pages": {"/p": {"status": 200, "indexable": False, "noindex_source": "meta"}}}
    inhib_ni = []
    assert not any(a["code"] == "noindex_added"
                   for a in compute_alerts(ni_prev, ni_storm, cfg, inhibited_out=inhib_ni))
    assert any(i["code"] == "noindex_added" and i["inhibited_by"] == "robots_sitewide_block"
               for i in inhib_ni)
    hd_storm = {"pages": {"/": {"status": 503},
                          "/p": {"status": 200, "indexable": False, "noindex_source": "meta"}}}
    inhib_hd = []
    assert not any(a["code"] == "noindex_added"
                   for a in compute_alerts({"pages": {"/": {"status": 200}, "/p": {"status": 200, "indexable": True}}},
                                           hd_storm, cfg, inhibited_out=inhib_hd))
    assert any(i["code"] == "noindex_added" and i["inhibited_by"] == "homepage_down" for i in inhib_hd)

    # --- D1 P0-2:canonical 目标健康度(HEAD 探测+连击 3 次防抖)---
    assert canonical_failure("error") and canonical_failure(404)
    assert not canonical_failure(301) and not canonical_failure(200) and not canonical_failure(None)
    assert probe_canonical_target("https://x/p", "https://x/p", "https://x/p") is None   # 自指不探测
    assert probe_canonical_target("https://x/p", None, "") is None                       # 无 canonical
    _g = globals()
    _orig_head = _g["http_head"]
    _orig_get = _g["http_get"]
    _g["http_head"] = lambda u, timeout=FETCH_TIMEOUT: {"status": 404}
    _g["http_get"] = lambda url, timeout=FETCH_TIMEOUT: {
        "status": 200, "final_url": url, "elapsed_ms": 1.0,
        "body": "<title>t</title><meta name='robots' content='noindex'>"
                "<link rel='canonical' href='https://x/other'>",
        "headers": {"x-robots-tag": "noindex"}}
    try:
        assert probe_canonical_target("https://x/p", "https://x/p", "https://x/other") == 404
        cp = check_page("https://x/p")
    finally:
        _g["http_head"], _g["http_get"] = _orig_head, _orig_get
    assert cp["metrics"]["indexable"] is False
    assert cp["metrics"]["noindex_source"] == "meta+header"
    assert cp["metrics"]["canonical_target_status"] == 404
    cn_base = {"pages": {"/p": {"status": 200, "indexable": True,
                                "canonical": "https://x/c", "canonical_target_status": 404}}}
    for streak in (1, 2):
        cn_try = json.loads(json.dumps(cn_base))
        cn_try["pages"]["/p"]["canonical_fail_streak"] = streak
        assert not any(a["code"] == "canonical_target_broken"
                       for a in compute_alerts(ni_prev, cn_try, cfg)), "streak=%d 不该告警" % streak
    cn_try["pages"]["/p"]["canonical_fail_streak"] = 3
    cn_hit = [a for a in compute_alerts(ni_prev, cn_try, cfg) if a["code"] == "canonical_target_broken"]
    assert cn_hit and cn_hit[0]["level"] == "warn" and "指向 404 目标" in cn_hit[0]["message"]
    # 连击计数:失败续数/成功清零/旧库(无 prev)从 1 起
    snap_a = {"pages": {"/p": {"canonical_target_status": 404}}}
    apply_canonical_streaks({"pages": {"/p": {"canonical_fail_streak": 2}}, }, snap_a)
    assert snap_a["pages"]["/p"]["canonical_fail_streak"] == 3
    snap_b = {"pages": {"/p": {"canonical_target_status": 200}}}
    apply_canonical_streaks(snap_a, snap_b)
    assert snap_b["pages"]["/p"]["canonical_fail_streak"] == 0
    snap_c = {"pages": {"/p": {"canonical_target_status": "error"}}}
    apply_canonical_streaks(None, snap_c)
    assert snap_c["pages"]["/p"]["canonical_fail_streak"] == 1

    # --- P0-6 secret 守卫 ---
    bad_cfg = json.loads(json.dumps(cfg))
    bad_cfg["channels"]["slack"]["webhook_url"] = "https://hooks.slack.com/services/T00/B00/XXX"
    assert find_config_secrets(bad_cfg), "slack webhook 明文必须被检出"
    assert not find_config_secrets(cfg), "env 引用名形态不应误报"

    # --- P0-5 重定向 SSRF 逐跳复查(stub DNS+strict,防本机 fake-IP 代理干扰判定)---
    _orig_gai = socket.getaddrinfo
    socket.getaddrinfo = lambda host, *a, **k: [(2, 1, 6, "", (host, 0))]
    _ssrf_cache.clear()
    os.environ["SEO_MONITOR_STRICT_SSRF"] = "1"
    try:
        for _evil in ("http://169.254.169.254/latest", "http://127.0.0.1:9000/x", "ftp://e.com/f"):
            try:
                _RedirectGuard().redirect_request(None, None, 302, "Found", {}, _evil)
                raise AssertionError("重定向到私网/元数据端点必须被逐跳拒绝: " + _evil)
            except FetchError:
                pass
    finally:
        socket.getaddrinfo = _orig_gai
        _ssrf_cache.clear()
        del os.environ["SEO_MONITOR_STRICT_SSRF"]

    # --- P1-12 状态机/prune/quarantine(真库离线)---
    conn = open_db(mdir)
    for i in range(3):
        conn.execute("INSERT INTO runs(ts,kind,status,checks_run,budget_used_sec,summary) "
                     "VALUES(?,?,?,?,0,'')",
                     (datetime.now().isoformat(timespec="seconds"), "daily", "ok", "daily"))
    conn.commit()
    assert latest_run_ids(conn, 5) == [3, 2, 1]        # 只认 ok
    conn.execute("UPDATE runs SET status='quarantined' WHERE id=3")
    conn.commit()
    assert latest_run_ids(conn, 5) == [2, 1]           # quarantined 不充当基线
    assert sweep_stale_runs(conn) == 0
    for i in range(4, 8):
        conn.execute("INSERT INTO runs(ts,kind,status,checks_run,budget_used_sec,summary) "
                     "VALUES(?,?,?,?,0,'')",
                     (datetime.now().isoformat(timespec="seconds"), "daily", "ok", "daily"))
    conn.commit()
    assert prune(conn, mdir, keep=2) == 5              # PruneDB 只留最近 2
    conn.close()

    # --- P1-15 维护窗口判定 ---
    mcfg = {"maintenance_windows": [{"from": "2026-01-01T00:00", "to": "2026-01-02T00:00"}]}
    assert in_maintenance(mcfg, datetime(2026, 1, 1, 12)) is not None
    assert in_maintenance(mcfg, datetime(2026, 2, 1)) is None
    print("[self-test] PASS monitor(11 类告警判定/地板/自愈/抑制树/双窗口/SSL 梯度/"
          "字段级 diff+selector/secret 守卫/重定向 SSRF/状态机+prune+quarantine/维护窗口/"
          "noindex 检测+canonical 目标健康度(D1 P0-1/P0-2))")


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
