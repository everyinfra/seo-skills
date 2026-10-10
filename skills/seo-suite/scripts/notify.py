#!/usr/bin/env python3
"""告警通知器(stdlib-only)。读 monitor.py diff 产出的告警 JSON,按级别路由:

  critical → 立即发(所有已配置渠道)
  warn     → 日批(暂存 pending,--flush warn 时发摘要)
  info     → 周批(暂存 pending,--flush info 时发摘要)
  low      → 静默(自愈只进报告,永不打扰)
  suppressed → 冷却期内重复指纹:只进报告,绝不进通知路径(audit 05 P0 修复)

渠道(config.json channels,secret 只经 env 引用注入,明文会被 monitor 拒写):
  slack    env SEO_MONITOR_SLACK_WEBHOOK
  discord  env SEO_MONITOR_DISCORD_WEBHOOK
  telegram env SEO_MONITOR_TG_TOKEN + SEO_MONITOR_TG_CHAT
  email    smtp_host/port/use_ssl/username/from/to + env SEO_MONITOR_SMTP_PASS
  webhook  env SEO_MONITOR_WEBHOOK_URL —— Apprise 式通用 webhook 抽象:
           URL scheme 决定载荷:json(s)://=POST {"text":...};form(s)://=POST 表单
           text=text;text(s)://=POST 纯文本;裸 https:// 默认 JSON(新渠道一行配置)

按告警类型路由(P0-3,Conductor per-definition 收件人模型):
  channels 各渠道可加可选 "route": {"codes": ["robots_*", ...]}(fnmatch 前缀通配)——
  code 命中模式的渠道才收;未配 route 的渠道照收全部(向后兼容)。
  同型多渠道用自定义键名 + "type" 字段 per-definition 定义(如 slack-tech / slack-content)。
  级别节奏不变(critical 即时/warn 日批/info 周批),route 只决定"去哪";
  `notify.py routes` 打印建议路由表注释模板(技术/内容/性能三类,不强制)。

告警生命周期(Conductor 口径保守子集):
  发出的告警附 incident_key(code+主对象指纹,消息里 id: 段),记录进 notify-incidents.json
  (独立 JSON,不动 monitor.db schema),发出超 24h 自动过期;恢复时 `notify.py resolve`
  按 key 清单向当初收到告警的渠道发 RESOLVED 消息并关闭 incident(本处渠道皆单向,
  双向渠道才可只记日志)。

防疲劳/自守恒纪律:
  --max-age N   拒发陈旧 alerts.json(默认 30 分钟;防"run 失败→notify 读昨天文件重发")
  渠道故障隔离  每渠道独立 try,一家失败不阻断其余;失败 detail 脱敏(token 不进日志)
  flush 保批    日批/周批只在全部渠道发送成功后才清空,失败保留 pending(不丢告警)
  dead_man      无成功 run 超 2×周期 → 主动发 dead_man 告警(监控器自身停摆可感知)

用法:
  python3 notify.py run --dir .seo-monitor --alerts .seo-monitor/alerts.json
  python3 notify.py run --dir .seo-monitor --alerts ... --flush warn
  python3 notify.py run --dir .seo-monitor --alerts ... --flush info
  python3 notify.py run --dir .seo-monitor --alerts ... --flush all --dry-run
  cat alerts.json | python3 notify.py run --dir .seo-monitor --stdin
  python3 notify.py resolve --dir .seo-monitor noindex_added@ab12cd34ef56  # 恢复通知
  python3 notify.py resolve --dir .seo-monitor --file resolved-keys.txt
  python3 notify.py routes                                                 # 建议路由表模板
  python3 notify.py --self-test

退出码:0=发送成功或无待发;1=发送失败(渠道报错);4=输入错误(含 alerts 文件过期)。
        resolve 对未知/已过期(>24h)的 key 只提示跳过,不判错。
"""
import argparse
import fnmatch
import hashlib
import json
import os
import re
import smtplib
import sqlite3
import ssl
import sys
import tempfile
import time
import traceback
import urllib.parse
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import formataddr

STATE_FILE = "notify-state.json"
INCIDENTS_FILE = "notify-incidents.json"   # 告警生命周期记录(独立 JSON,不动 monitor.db)
INCIDENT_TTL_HOURS = 24                    # Conductor 口径:24h 无新增即自动关闭
LEVELS = ("critical", "warn", "info", "low")
DISCORD_LIMIT, TELEGRAM_LIMIT = 1900, 3800
KNOWN_CHANNELS = ("slack", "discord", "telegram", "webhook", "email")

# P0-3 默认建议路由表:config 生成/init 时的注释模板,不强制(不配 route 的渠道照收全部)。
ROUTE_TEMPLATE = """\
建议路由表(P0-3,Conductor per-definition 收件人模型;注释模板,不强制——
不配 route 的渠道照收全部告警,级别节奏不受路由影响,route 只决定"去哪"):
  "channels": {
    "slack":  {"env": "SEO_MONITOR_SLACK_WEBHOOK",
               "route": {"codes": ["robots_*", "noindex_*", "canonical_*", "site_down", "ssl_*"]}},
    "slack-content": {"type": "slack", "env": "SEO_MONITOR_SLACK_CONTENT_WEBHOOK",
                      "route": {"codes": ["title_*", "meta_*", "content_*"]}},
    "webhook": {"env": "SEO_MONITOR_WEBHOOK_URL",
                "route": {"codes": ["cwv_*", "latency"]}}
  }
  # 技术类(robots/noindex/canonical/site_down/ssl)→ 技术渠道;内容类(title/meta/content)
  # → 内容渠道;性能类(cwv_/latency)→ 前端渠道。code 模式为 fnmatch 前缀通配。
  # 同型多渠道用自定义键名 + "type" 字段 per-definition 定义;secret 仍只经 env 引用注入。
  # 建议保留至少一个无 route 的兜底渠道(或为每类告警配齐 route):
  # 未命中任何 route 的告警只进日志,不发送。"""


# ---------- 工具 ----------

# 日志脱敏三连(audit 05-§4 + claude-seo doctor 口径),应用于所有日志打印路径:
_REDACT_URL = re.compile(r"(https?://[^/\s'\"]+)[^\s'\"]*")
_REDACT_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_REDACT_SECRET_KV = re.compile(
    r"""(?i)(["']?)\b([a-z0-9_-]*(?:api[_-]?key|token|password|passwd|secret)[a-z0-9_-]*)\b\1
        (\s*[:=]\s*)(["']?)[^\s"',;]+\4""", re.X)


def redact(s):
    """日志脱敏(P0-3 强化,claude-seo 口径):
    1) URL:保留 scheme+host,路径查询(含 token)打码——渠道 URL 里的 token 参数由这层
       处理,后两层不再重复碰 URL;
    2) email → <redacted-email>(SMTP 报错里的收发件人);
    3) token/password/secret/api_key 类键值对的值 → <redacted>(键名保留便于排查,
       兼顾 env 裸键与 JSON 引号键两种形态)。
    幂等:已脱敏文本再过一遍不变形。"""
    s = _REDACT_URL.sub(r"\1/[REDACTED]", str(s))
    s = _REDACT_EMAIL.sub("<redacted-email>", s)
    s = _REDACT_SECRET_KV.sub(
        lambda m: "%s%s%s%s<redacted>%s" % (m.group(1), m.group(2), m.group(1),
                                            m.group(3), m.group(4)), s)
    return s


def env_or(cfg_value, env_name):
    return os.environ.get(env_name, "") or (cfg_value or "")


# ---------- 渠道发送(全部返回 (ok, detail);异常不抛出,由调用方汇总) ----------

def _post_json(url, payload, timeout=15):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "User-Agent": "seo-suite-notify/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(2000).decode("utf-8", "replace")


def _post_raw(url, data, content_type, timeout=15):
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": content_type,
                                 "User-Agent": "seo-suite-notify/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(2000).decode("utf-8", "replace")


def send_generic_webhook(url, msg, timeout=15):
    """Apprise 式通用 webhook(P1-14,audit 17):scheme 决定载荷形态。
    json://host/path → http+JSON;jsons:// → https+JSON;form(s):// → 表单 text=msg;
    text(s):// → 纯文本 body;裸 http(s):// → 默认 JSON {"text": msg}。"""
    m = re.match(r"^(json|form|text)(s?)://(.+)$", url, re.I)
    if m:
        kind, secured, rest = m.group(1).lower(), m.group(2), m.group(3)
        real = ("https" if secured else "http") + "://" + rest
    else:
        kind, real = "json", url
    if kind == "json":
        return _post_json(real, {"text": msg}, timeout=timeout)
    if kind == "form":
        return _post_raw(real, urllib.parse.urlencode({"text": msg}).encode("utf-8"),
                         "application/x-www-form-urlencoded", timeout=timeout)
    return _post_raw(real, msg.encode("utf-8"), "text/plain; charset=utf-8", timeout=timeout)


_DEFAULT_ENV = {"slack": "SEO_MONITOR_SLACK_WEBHOOK",
                "discord": "SEO_MONITOR_DISCORD_WEBHOOK",
                "webhook": "SEO_MONITOR_WEBHOOK_URL"}


def _env_name(conf, ctype, key="env"):
    """渠道的 env 引用名:优先 conf 里的 env/env_token/env_chat(per-definition 可自定义),回退该渠道型默认。"""
    return conf.get(key) or _DEFAULT_ENV.get(ctype, "")


def _build_channel(name, ctype, conf):
    """装配单个渠道定义(固定渠道键或 per-definition type 条目);未配置返回 None。
    P0-3:渠道名(name)用于 route 匹配,固定键与自定义键名(slack-tech 等)一视同仁。"""
    if ctype == "slack":
        url = env_or(conf.get("webhook_url"), _env_name(conf, "slack"))
        if url:
            return name, lambda msg: _post_json(url, {"text": msg})

    elif ctype == "discord":
        url = env_or(conf.get("webhook_url"), _env_name(conf, "discord"))
        if url:
            def send_discord(msg):
                sent = ""
                for chunk in _chunk(msg, DISCORD_LIMIT):
                    st, body = _post_json(url, {"content": chunk})
                    sent += body
                return st, sent
            return name, send_discord

    elif ctype == "telegram":
        token = env_or(conf.get("bot_token"), conf.get("env_token") or "SEO_MONITOR_TG_TOKEN")
        chat = env_or(conf.get("chat_id"), conf.get("env_chat") or "SEO_MONITOR_TG_CHAT")
        if token and chat:
            def send_tg(msg):
                api = "https://api.telegram.org/bot%s/sendMessage" % token
                sent = ""
                for chunk in _chunk(_tg_escape(msg), TELEGRAM_LIMIT):
                    st, body = _post_json(api, {"chat_id": chat, "text": chunk, "parse_mode": "HTML"})
                    sent += body
                return st, sent
            return name, send_tg

    elif ctype == "webhook":
        url = env_or(conf.get("url") or conf.get("webhook_url"), _env_name(conf, "webhook"))
        if url:
            return name, lambda msg: send_generic_webhook(url, msg)

    elif ctype == "email":
        if conf.get("smtp_host") and conf.get("from") and conf.get("to"):
            em = conf
            def send_mail(msg):
                m = MIMEText(msg, "plain", "utf-8")
                m["Subject"] = "[seo-monitor] %s" % msg.splitlines()[0][:120]
                m["From"] = formataddr(("seo-monitor", em["from"]))
                m["To"] = ", ".join(em["to"])
                pw = os.environ.get("SEO_MONITOR_SMTP_PASS", "")
                if em.get("use_ssl", True):
                    s = smtplib.SMTP_SSL(em["smtp_host"], int(em.get("smtp_port", 465)),
                                         timeout=20,
                                         context=ssl.create_default_context())
                else:
                    s = smtplib.SMTP(em["smtp_host"], int(em.get("smtp_port", 587)), timeout=20)
                    s.starttls(context=ssl.create_default_context())
                try:
                    if em.get("username"):
                        s.login(em["username"], pw)
                    s.sendmail(em["from"], em["to"], m.as_string())
                finally:
                    s.quit()
                return 250, "smtp sent"
            return name, send_mail
    return None


def channel_targets(cfg):
    """返回 [(渠道名, 发送函数)]——只收已配置的渠道;渠道间故障隔离由 send_all 保证。
    P0-3(Conductor per-definition):channels 支持两种条目——固定渠道键
    (slack/discord/telegram/webhook/email)与带 "type" 字段的自定义键名定义
    (如 slack-tech/slack-content,同型多渠道各配各的 route);固定键顺序保持向后兼容。"""
    ch = cfg.get("channels", {})
    out = []
    if not isinstance(ch, dict):
        return out
    ordered = [k for k in KNOWN_CHANNELS if k in ch] + \
              [k for k in ch if k not in KNOWN_CHANNELS]
    for name in ordered:
        conf = ch.get(name)
        if not isinstance(conf, dict):
            continue
        ctype = conf.get("type") or (name if name in KNOWN_CHANNELS else None)
        if not ctype:
            continue  # 未知渠道型(拼写错误等):忽略不炸
        built = _build_channel(name, str(ctype), conf)
        if built:
            out.append(built)
    return out


def _chunk(text, limit):
    """按行切块;超长单行(无换行)按字符硬切,不炸渠道长度上限。"""
    out, buf = [], ""
    for line in text.splitlines(True):
        while len(line) > limit:            # 硬切超长行
            if buf:
                out.append(buf)
                buf = ""
            out.append(line[:limit])
            line = line[limit:]
        if len(buf) + len(line) > limit and buf:
            out.append(buf)
            buf = line
        else:
            buf += line
    if buf:
        out.append(buf)
    return out or [""]


def _tg_escape(msg):
    # 用 HTML parse_mode 时只转义 < > &,其余保持
    return msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------- 消息格式 ----------

def format_alerts(site, alerts, header):
    lines = ["[%s] %s" % (header, site), "时间: %s" % datetime.now().isoformat(timespec="seconds"), ""]
    for a in alerts:
        lines.append("[%s] %s: %s" % (a.get("level", "?").upper(), a.get("code", "?"), a.get("message", "")))
        if a.get("action"):
            lines.append("  -> %s (%s)" % (a["action"], a.get("boundary", "human")))
        if a.get("incident_key"):
            lines.append("  id: %s(恢复时: notify.py resolve <此 key>)" % a["incident_key"])
    lines.append("")
    lines.append("-- 分级抑制:critical 即时 / warn 日批 / info 周批 / low 静默 --")
    return "\n".join(lines)


def send_all(targets, msg, dry_run):
    """渠道故障隔离(P1-14,audit 02/TrendWatch):逐渠道 try,一家失败不阻断其余;
    失败 detail 过 redact(),webhook token 不进日志。"""
    results = []
    for name, fn in targets:
        if dry_run:
            results.append((name, True, "dry-run 未发送"))
            continue
        try:
            st, detail = fn(msg)
            ok = 200 <= int(st) < 300 or int(st) == 250
            results.append((name, ok, "HTTP %s %s" % (st, redact(detail)[:200])))
        except Exception as e:
            results.append((name, False, "%s: %s" % (type(e).__name__, redact(e))))
    return results


# ---------- 按告警类型路由(P0-3,Conductor per-definition 收件人模型)----------

def channel_routes(cfg):
    """读各渠道可选 route 字段 → {渠道名: [code 模式]}。只返回配了 route.codes 的渠道;
    未配 route 的渠道不出现(= 收全部,向后兼容)。模式为 fnmatch 语义(robots_* 前缀通配)。"""
    out = {}
    ch = cfg.get("channels", {})
    if isinstance(ch, dict):
        for name, conf in ch.items():
            if not isinstance(conf, dict):
                continue
            codes = (conf.get("route") or {}).get("codes")
            if isinstance(codes, list) and codes:
                out[name] = [str(c) for c in codes if c]
    return out


def code_matches(code, patterns):
    return any(fnmatch.fnmatch(code or "", p) for p in patterns)


def targets_for_code(targets, routes, code):
    """code 命中渠道 route 模式 → 收;未配 route 的渠道 → 照收(向后兼容)。"""
    return [t for t in targets
            if t[0] not in routes or code_matches(code, routes[t[0]])]


def group_by_recipients(alerts, targets, routes):
    """按"可达渠道集合"把告警分组(保序),返回 [(子 targets, [告警])]。
    路由只决定"去哪":级别节奏(critical 即时/warn 日批/info 周批)由上游 route_alerts 决定,
    不受此处分组影响;空组(全被 route 筛掉)由调用方记日志。"""
    buckets, order = {}, []
    for a in alerts:
        sub = tuple(targets_for_code(targets, routes, a.get("code", "")))
        if sub not in buckets:
            buckets[sub] = []
            order.append(sub)
        buckets[sub].append(a)
    return [(list(sub), buckets[sub]) for sub in order]


# ---------- 状态(日批/周批暂存) ----------

def load_state(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"pending_warn": [], "pending_info": [], "updated": None}


def save_state(path, st):
    """原子写(tmp+os.replace,P0-3):两个 notify 并发时不会留下半截 state 文件。"""
    st["updated"] = datetime.now().isoformat(timespec="seconds")
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".notify-state-", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ---------- 告警生命周期(P0-3,Conductor 口径保守子集)----------

def incident_key(alert):
    """incident_key = code + 主对象指纹(sha256 前 12 位,跨进程稳定,非内置 hash())。
    形如 noindex_added@ab12cd34ef56,消息 id: 段透出,resolve 子命令据此对账。"""
    raw = "%s\x00%s" % (alert.get("code", ""), alert.get("key", ""))
    fp = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return "%s@%s" % (alert.get("code", "?") or "?", fp)


def load_incidents(path):
    """读 incidents 记录(独立 JSON,不动 SQLite schema);发出超 24h 的自动过期剔除。"""
    data = {"incidents": {}}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict) and isinstance(raw.get("incidents"), dict):
                data = raw
        except (OSError, ValueError):
            data = {"incidents": {}}
    now = datetime.now()
    live = {}
    for k, v in data["incidents"].items():
        try:
            sent = datetime.fromisoformat(str((v or {}).get("sent_at")))
        except (ValueError, TypeError):
            continue
        if (now - sent).total_seconds() <= INCIDENT_TTL_HOURS * 3600:
            live[k] = v
    return {"incidents": live}


def save_incidents(path, data):
    """原子写(同 save_state 惯例)。"""
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".notify-incidents-", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"incidents": data.get("incidents", {})}, f,
                      ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def record_incidents(mdir, alerts, dry_run=False):
    """发送成功后落 {incident_key: {code,key,level,sent_at}}(resolve 子命令的依据)。
    同 key 重发刷新 sent_at——24h 窗口自最后一次发出计(Conductor:24h 无新增即关闭)。
    dry-run 或未实际送达(渠道全败)不记录。"""
    if dry_run or not alerts:
        return
    path = os.path.join(mdir, INCIDENTS_FILE)
    data = load_incidents(path)
    now = datetime.now().isoformat(timespec="seconds")
    for a in alerts:
        data["incidents"][incident_key(a)] = {
            "code": a.get("code", ""), "key": a.get("key", ""),
            "level": a.get("level", ""), "message": str(a.get("message", ""))[:200],
            "sent_at": now}
    save_incidents(path, data)


def format_resolved(site, items):
    """恢复通知消息(items: [(incident_key, 记录)])。渠道皆单向,恢复也走发送;
    若接入双向渠道,可改为只在日志记录(见 docstring)。"""
    lines = ["[RESOLVED 恢复] %s" % site,
             "时间: %s" % datetime.now().isoformat(timespec="seconds"), ""]
    for ik, inc in items:
        lines.append("[RESOLVED] %s: %s 已恢复(告警解除)"
                     % (inc.get("code", "?"), inc.get("key", "")))
        if inc.get("message"):
            lines.append("  原告警: %s" % inc["message"])
        lines.append("  incident_key: %s" % ik)
    lines.append("")
    lines.append("-- Conductor 口径:恢复即关闭;发出超 24h 无新增亦自动过期 --")
    return "\n".join(lines)


def route_alerts(alerts, state):
    """分级抑制的核心路由:返回 immediate 列表,并把 warn/info 暂存进 state。
    P0-1(audit 05 头号发现):suppressed(冷却命中)只进报告不进通知——
    路由前直接剔除,即使上游忘了过滤也不会重发。"""
    immediate, nw, ni, ns = [], 0, 0, 0
    seen_fp = {p.get("fp") for p in state["pending_warn"]} | \
              {p.get("fp") for p in state["pending_info"]}
    for a in alerts:
        if a.get("suppressed"):
            ns += 1
            continue
        lvl = a.get("level")
        fp = "%s:%s" % (a.get("code"), a.get("key"))
        if lvl == "critical":
            immediate.append(a)  # 事件型:即时,不做批
        elif lvl == "warn":
            if fp not in seen_fp:
                state["pending_warn"].append({**a, "fp": fp, "since":
                                              datetime.now().isoformat(timespec="seconds")})
                seen_fp.add(fp)
                nw += 1
        elif lvl == "info":
            if fp not in seen_fp:
                state["pending_info"].append({**a, "fp": fp, "since":
                                              datetime.now().isoformat(timespec="seconds")})
                seen_fp.add(fp)
                ni += 1
        # low:静默,只进 report
    return immediate, nw, ni, ns


# ---------- dead man's switch(P1-8,audit 18)----------

def dead_man_alert(mdir, cfg):
    """距上次成功 run 超 2×周期 → 返回 dead_man 告警(即时发);监控器自身停摆可感知。
    周期取 config run_cadence_hours(默认 24)。"""
    db = os.path.join(mdir, "monitor.db")
    if not os.path.exists(db):
        return None
    cadence = float(cfg.get("run_cadence_hours", 24) or 24)
    try:
        conn = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(db), uri=True, timeout=5)
    except sqlite3.Error:
        return None
    try:
        row = conn.execute(
            "SELECT ts FROM runs WHERE status IN ('ok','partial') ORDER BY id DESC LIMIT 1").fetchone()
    except sqlite3.Error:
        return None
    finally:
        conn.close()
    if not row:
        return None
    try:
        hours = (datetime.now() - datetime.fromisoformat(row[0])).total_seconds() / 3600.0
    except ValueError:
        return None
    if hours <= 2 * cadence:
        return None
    return {"level": "warn", "code": "dead_man", "key": "monitor",
            "message": "监控自身停摆: 距上次成功 run %.1f 小时(>2×周期 %.0fh)——查 cron/Actions 是否被禁"
                       % (hours, cadence),
            "details": {"hours_since_last_run": round(hours, 1), "cadence_hours": cadence},
            "action": "检查 cron/Actions 调度、机器休眠、SQLite 锁与 heartbeat 服务", "boundary": "human"}


# ---------- 主流程 ----------

def alerts_age_minutes(payload, path):
    """alerts.json 的年龄:优先 payload.generated,回退文件 mtime。"""
    for cand in (payload.get("generated"),):
        if cand:
            try:
                return (datetime.now() - datetime.fromisoformat(str(cand))).total_seconds() / 60.0
            except ValueError:
                pass
    try:
        return (time.time() - os.path.getmtime(path)) / 60.0
    except OSError:
        return None


def cmd_notify(args):
    mdir = args.dir
    cfg_path = os.path.join(mdir, "config.json")
    if not os.path.exists(cfg_path):
        print("错误: %s 不存在,先跑 monitor.py init" % cfg_path, file=sys.stderr)
        return 4
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)

    if args.stdin:
        payload = json.load(sys.stdin)
        src = "<stdin>"
    elif args.alerts:
        with open(args.alerts, encoding="utf-8") as f:
            payload = json.load(f)
        src = args.alerts
    else:
        print("错误: 需要 --alerts FILE 或 --stdin", file=sys.stderr)
        return 4

    # P0-2(audit 05-§3):陈旧 alerts.json 拒发——run 失败(rc=3)时 notify 不该把
    # 昨天的 critical 原样重发一遍。默认 30 分钟。
    if not args.stdin and args.max_age is not None and args.max_age > 0:
        age = alerts_age_minutes(payload, args.alerts)
        if age is not None and age > args.max_age:
            print("错误: %s 已陈旧(%.0f 分钟前生成,> --max-age %d),拒发防旧告警重播"
                  % (src, age, args.max_age), file=sys.stderr)
            return 4

    alerts = payload.get("alerts", [])
    site = payload.get("site") or cfg.get("site", "(site 未配置)")

    state = load_state(os.path.join(mdir, STATE_FILE))
    immediate, nw, ni, ns = route_alerts(alerts, state)

    # dead man's switch:监控器自身停摆也算"即时"级事件(audit 18)
    dm = dead_man_alert(mdir, cfg)
    if dm:
        immediate.append(dm)

    targets = channel_targets(cfg)
    routes = channel_routes(cfg)
    rc = 0

    print("路由: critical=%d(即时) warn+%d(暂存日批,共 %d) info+%d(暂存周批,共 %d) "
          "low=%d(静默) suppressed=%d(冷却期内,不通知)%s%s"
          % (len(immediate) - (1 if dm else 0), nw, len(state["pending_warn"]), ni,
             len(state["pending_info"]), sum(1 for a in alerts if a.get("level") == "low"),
             ns, " dead_man=1(监控停摆)" if dm else "",
             " 按类型路由=%d 渠道" % len(routes) if routes else ""))
    if not targets:
        print("[i] 无已配置渠道(config.json channels 全空)——只暂存不发送;"
              "webhook 可用环境变量注入(见 config notes)")
    elif len(targets) >= 2 and not routes:
        print("[i] 已配多渠道但无 route(按告警类型路由):notify.py routes 打印建议路由表模板(不强制)")

    if immediate:
        header = "CRITICAL 即时告警" if not dm else "即时告警(含 dead_man)"
        for a in immediate:                      # Conductor 生命周期口径:发出的告警附 key
            a.setdefault("incident_key", incident_key(a))
        for sub, group in group_by_recipients(immediate, targets, routes):
            if not sub:
                if targets:
                    print("  [!] %d 条即时告警未命中任何渠道的 route,只进日志不发送" % len(group))
                continue
            msg = format_alerts(site, group, header)
            results = send_all(sub, msg, args.dry_run)
            for name, ok, detail in results:
                print("  [%s] %s: %s" % ("OK" if ok else "FAIL", name, detail))
                rc = rc or (0 if ok else 1)
            if any(ok for _, ok, _ in results):
                record_incidents(mdir, group, args.dry_run)

    flush = (args.flush or "")
    digests = []
    if flush in ("warn", "all") and state["pending_warn"]:
        digests.append(("warn 日批摘要", state["pending_warn"], "pending_warn"))
    if flush in ("info", "all") and state["pending_info"]:
        digests.append(("info 周批摘要", state["pending_info"], "pending_info"))
    for title, batch, key in digests:
        for a in batch:
            a.setdefault("incident_key", incident_key(a))
        sent_all_ok = True                       # 含"本无渠道/组内无渠道"情形(维持旧清批口径)
        for sub, group in group_by_recipients(batch, targets, routes):
            if not sub:
                if targets:
                    print("  [!] %d 条 %s 告警未命中任何渠道的 route,只进日志" % (len(group), title))
                continue
            msg = format_alerts(site, group, title)
            results = send_all(sub, msg, args.dry_run)
            for name, ok, detail in results:
                print("  [%s] %s: %s" % ("OK" if ok else "FAIL", name, detail))
                rc = rc or (0 if ok else 1)
            if any(ok for _, ok, _ in results):
                record_incidents(mdir, group, args.dry_run)
            if not all(ok for _, ok, _ in results):
                sent_all_ok = False
        # P1-14(audit 05-§3 反向问题):只在全部渠道成功(或本无渠道)后清批,
        # 渠道失败保留 pending——绝不因发送失败而丢告警。
        if not args.dry_run:
            if sent_all_ok:
                state[key] = []
            else:
                print("  [!] %s 有渠道失败,pending 保留(下次 flush 重试,不丢告警)" % title)

    if not args.dry_run:
        save_state(os.path.join(mdir, STATE_FILE), state)
    else:
        print("[dry-run] 状态未写盘")
    return rc


# ---------- CLI / 自测 ----------

def cmd_resolve(args):
    """resolve 子命令:输入 incident_key 清单,向当初收到告警的渠道发恢复通知。
    按记录里的 code 走同一路由(P0-3);送达后关闭 incident,失败保留待重试;
    未知/发出超 24h 的 key 只提示跳过,不判错。"""
    mdir = args.dir
    cfg_path = os.path.join(mdir, "config.json")
    if not os.path.exists(cfg_path):
        print("错误: %s 不存在,先跑 monitor.py init" % cfg_path, file=sys.stderr)
        return 4
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)

    keys = [k for k in (args.keys or []) if k]
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            keys += [ln.strip() for ln in f
                     if ln.strip() and not ln.strip().startswith("#")]
    if not keys:
        print("错误: 需要 incident_key 清单(位置参数或 --file),key 见告警消息 id: 段",
              file=sys.stderr)
        return 4

    path = os.path.join(mdir, INCIDENTS_FILE)
    data = load_incidents(path)                  # 顺带剔除超 24h 的过期记录
    uniq = list(dict.fromkeys(keys))
    resolved = [(k, data["incidents"][k]) for k in uniq if k in data["incidents"]]
    for k in uniq:
        if k not in data["incidents"]:
            print("[i] %s: 未记录或发出超 24h 已过期,跳过(不判错)" % k)

    targets = channel_targets(cfg)
    routes = channel_routes(cfg)
    if not targets:
        print("[i] 无已配置渠道——恢复通知无处可发,只记日志")
    rc = 0
    groups = {}
    for item in resolved:
        sub = tuple(targets_for_code(targets, routes, item[1].get("code", "")))
        groups.setdefault(sub, []).append(item)
    for sub, items in groups.items():
        if not sub:
            print("[!] %d 条恢复未命中任何渠道,只进日志" % len(items))
            continue
        msg = format_resolved(cfg.get("site", "(site 未配置)"), items)
        results = send_all(sub, msg, args.dry_run)
        for name, ok, detail in results:
            print("  [%s] %s: %s" % ("OK" if ok else "FAIL", name, detail))
            rc = rc or (0 if ok else 1)
        if not args.dry_run and any(ok for _, ok, _ in results):
            for ik, _ in items:                  # 恢复送达 → 关闭 incident
                data["incidents"].pop(ik, None)
    if not args.dry_run and (resolved or os.path.exists(path)):
        save_incidents(path, data)
    return rc


def cmd_routes(args):
    """routes 子命令:打印默认建议路由表注释模板(P0-3,不强制;monitor.py init 冻结,
    模板由此处与 --help epilog 透出)。"""
    print(ROUTE_TEMPLATE)
    return 0


def build_parser():
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0], epilog=ROUTE_TEMPLATE,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true", help="离线自测(不联网)")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("run", help="路由并发送告警")
    p.add_argument("--dir", default=".seo-monitor")
    p.add_argument("--alerts", default="", help="monitor.py diff --out 产出的 JSON")
    p.add_argument("--stdin", action="store_true", help="改从 stdin 读告警 JSON")
    p.add_argument("--flush", choices=["warn", "info", "all"], default="",
                   help="顺带发送并清空对应批次(warn=日批 info=周批)")
    p.add_argument("--max-age", type=int, default=30, dest="max_age",
                   help="alerts.json 最大年龄(分钟),过期拒发防旧告警重播;0=不检查")
    p.add_argument("--dry-run", action="store_true", help="只打印路由与消息,不联网不写盘")
    p.set_defaults(func=cmd_notify)

    p = sub.add_parser("resolve", help="按 incident_key 发恢复通知(24h 内发出的告警)")
    p.add_argument("--dir", default=".seo-monitor")
    p.add_argument("keys", nargs="*", help="incident_key 清单(告警消息里 id: 段)")
    p.add_argument("--file", default="", help="从文件读 key 清单(每行一个,# 为注释)")
    p.add_argument("--dry-run", action="store_true", help="只打印不联网不写盘")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("routes", help="打印建议路由表注释模板(P0-3,不强制)")
    p.set_defaults(func=cmd_routes)
    return ap


def _self_test():
    tmp = tempfile.mkdtemp(prefix="notify_selftest_")
    mdir = os.path.join(tmp, ".seo-monitor")
    os.makedirs(mdir)
    with open(os.path.join(mdir, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"site": "https://example.com",
                   "run_cadence_hours": 24,
                   "channels": {
                       "slack": {}, "discord": {}, "telegram": {},
                       "email": {"smtp_host": "", "from": "", "to": []},
                       "webhook": {"env": "SEO_MONITOR_WEBHOOK_URL"},
                   }}, f)

    # 分级路由:critical 即时 / warn·info 暂存去重 / low 静默 / suppressed 不进通知(P0-1)
    st = load_state(os.path.join(mdir, STATE_FILE))
    alerts = [
        {"level": "critical", "code": "key_page_down", "key": "/pricing", "message": "404", "action": "x"},
        {"level": "critical", "code": "homepage_down", "key": "/", "message": "503(冷却中)",
         "suppressed": True},
        {"level": "warn", "code": "gsc_clicks_drop", "key": "file", "message": "-30%"},
        {"level": "warn", "code": "gsc_clicks_drop", "key": "file", "message": "-30%"},
        {"level": "info", "code": "title_meta_drift", "key": "/", "message": "hash 变"},
        {"level": "low", "code": "x_resolved", "key": "/", "message": "自愈"},
    ]
    imm, nw, ni, ns = route_alerts(alerts, st)
    assert len(imm) == 1 and imm[0]["level"] == "critical"
    assert ns == 1 and not any(a.get("code") == "homepage_down" for a in imm)  # suppressed 被剔除
    assert nw == 1 and ni == 1                       # 重复 warn 指纹只暂存一次
    assert len(st["pending_warn"]) == 1 and not any(p["level"] == "low" for p in st["pending_info"])
    imm2, nw2, _, ns2 = route_alerts(alerts, st)
    assert len(imm2) == 1 and nw2 == 0 and ns2 == 1  # 第二轮同指纹不再暂存,suppressed 仍不进
    save_state(os.path.join(mdir, STATE_FILE), st)
    st2 = load_state(os.path.join(mdir, STATE_FILE))
    assert len(st2["pending_warn"]) == 1

    # 渠道装配:全空配置 → 无渠道
    cfg = json.load(open(os.path.join(mdir, "config.json"), encoding="utf-8"))
    assert channel_targets(cfg) == []
    # slack 环境变量注入
    os.environ["SEO_MONITOR_SLACK_WEBHOOK"] = "https://hooks.slack.test/x"
    tg = channel_targets(cfg)
    assert [n for n, _ in tg] == ["slack"]
    del os.environ["SEO_MONITOR_SLACK_WEBHOOK"]
    # 通用 webhook:Apprise 式 scheme 解析(mock 网络层,零联网)
    os.environ["SEO_MONITOR_WEBHOOK_URL"] = "jsons://hooks.example.test/abc"
    assert [n for n, _ in channel_targets(cfg)] == ["webhook"]
    calls = []
    notify_mod = sys.modules[__name__]
    orig_json, orig_raw = notify_mod._post_json, notify_mod._post_raw
    notify_mod._post_json = lambda url, payload, timeout=15: (
        calls.append(("json", url, payload)) or (200, "ok"))
    notify_mod._post_raw = lambda url, data, ct, timeout=15: (
        calls.append(("raw", url, (data, ct))) or (200, "ok"))
    try:
        assert send_generic_webhook("jsons://hooks.example.test/abc", "hello")[0] == 200
        assert calls[-1] == ("json", "https://hooks.example.test/abc", {"text": "hello"})
        send_generic_webhook("form://h.test/p", "a=b")
        assert calls[-1][0] == "raw" and calls[-1][1] == "http://h.test/p" \
            and calls[-1][2] == (b"text=a%3Db", "application/x-www-form-urlencoded")
        send_generic_webhook("texts://h.test/t", "plain")
        assert calls[-1][2] == (b"plain", "text/plain; charset=utf-8")
    finally:
        notify_mod._post_json, notify_mod._post_raw = orig_json, orig_raw
    del os.environ["SEO_MONITOR_WEBHOOK_URL"]
    # 脱敏:token 段不出现
    leaked = redact("urlopen failed: https://api.telegram.org/bot123:ABC-DEF/messages")
    assert "123:ABC-DEF" not in leaked and "api.telegram.org" in leaked
    # P0-3 脱敏强化:email / token·password·secret·api_key 键值 / 幂等
    r2 = redact("SMTP auth failed for ops@example.com (535) token=abc123 password: hunter2")
    assert "ops@example.com" not in r2 and "<redacted-email>" in r2
    assert "abc123" not in r2 and "hunter2" not in r2
    assert redact(leaked) == leaked                      # 已脱敏文本不再变形

    # P0-3 按类型路由:fnmatch 前缀 / 无 route 渠道照收 / 分组保序
    rcfg = {"channels": {"slack-tech": {"type": "slack",
                                        "route": {"codes": ["robots_*", "noindex_*"]}}}}
    assert channel_routes(rcfg) == {"slack-tech": ["robots_*", "noindex_*"]}
    assert channel_routes(cfg) == {}                     # 无 route → 空(全渠道照收)
    tgts = [("slack-tech", None), ("slack-all", None)]
    rts = {"slack-tech": ["robots_*"]}
    assert [n for n, _ in targets_for_code(tgts, rts, "robots_changed")] == ["slack-tech", "slack-all"]
    assert [n for n, _ in targets_for_code(tgts, rts, "title_missing")] == ["slack-all"]
    grp = group_by_recipients(
        [{"code": "robots_changed"}, {"code": "title_missing"}, {"code": "robots_removed"}],
        tgts, rts)
    assert [tuple(n for n, _ in sub) for sub, _ in grp] == \
        [("slack-tech", "slack-all"), ("slack-all",)]
    assert [a["code"] for a in grp[0][1]] == ["robots_changed", "robots_removed"]

    # P0-3 告警生命周期:incident_key 稳定 / 记录 / 24h 过期 / resolve 子命令
    a1 = {"code": "noindex_added", "key": "/pricing", "level": "critical", "message": "x"}
    a2 = {"code": "noindex_added", "key": "/blog", "level": "critical", "message": "x"}
    k1, k2 = incident_key(a1), incident_key(a2)
    assert k1 == incident_key(dict(a1)) and k1 != k2 and k1.startswith("noindex_added@")
    record_incidents(mdir, [a1], dry_run=True)
    assert not os.path.exists(os.path.join(mdir, INCIDENTS_FILE))   # dry-run 不落盘
    record_incidents(mdir, [a1, a2])
    inc = load_incidents(os.path.join(mdir, INCIDENTS_FILE))["incidents"]
    assert set(inc) == {k1, k2}
    inc[k1]["sent_at"] = "2020-01-01T00:00:00"
    save_incidents(os.path.join(mdir, INCIDENTS_FILE), {"incidents": inc})
    assert k1 not in load_incidents(os.path.join(mdir, INCIDENTS_FILE))["incidents"]  # 超 24h 剔除
    resolve_sent = []
    orig_ct = notify_mod.channel_targets
    notify_mod.channel_targets = lambda c: [
        ("slack", lambda msg: resolve_sent.append(msg) or (200, "ok"))]
    try:
        assert main(["resolve", "--dir", mdir, k2]) == 0
        assert resolve_sent and "已恢复" in resolve_sent[0] and k2 in resolve_sent[0]
        assert k2 not in load_incidents(os.path.join(mdir, INCIDENTS_FILE))["incidents"]
        assert main(["resolve", "--dir", mdir, k2]) == 0     # 已关闭 → 跳过不判错
        assert len(resolve_sent) == 1
        assert main(["resolve", "--dir", mdir]) == 4         # 空 key 清单 → 输入错误
    finally:
        notify_mod.channel_targets = orig_ct
    assert "robots_*" in ROUTE_TEMPLATE and "fnmatch" in ROUTE_TEMPLATE

    # 分块与转义
    chunks = _chunk("a" * 4500, TELEGRAM_LIMIT)
    assert len(chunks) == 2 and sum(len(c) for c in chunks) == 4500
    assert _tg_escape("<b>&") == "&lt;b&gt;&amp;"
    # 消息格式含动作边界
    msg = format_alerts("https://example.com", imm, "CRITICAL 即时告警")
    assert "[CRITICAL] key_page_down" in msg and "-> x" in msg

    # CLI dry-run 全链路(无渠道,rc=0)
    alerts_file = os.path.join(mdir, "alerts.json")
    with open(alerts_file, "w", encoding="utf-8") as f:
        json.dump({"site": "https://example.com", "generated":
                   datetime.now().isoformat(timespec="seconds"), "alerts": alerts}, f)
    rc = cmd_notify(build_parser().parse_args(
        ["run", "--dir", mdir, "--alerts", alerts_file, "--flush", "all", "--dry-run"]))
    assert rc == 0, rc
    # flush 后批清空(非 dry-run)
    rc = cmd_notify(build_parser().parse_args(
        ["run", "--dir", mdir, "--alerts", alerts_file, "--flush", "all"]))
    assert rc == 0
    st3 = load_state(os.path.join(mdir, STATE_FILE))
    assert st3["pending_warn"] == [] and st3["pending_info"] == []
    # --max-age:陈旧文件拒发(P0-2)
    with open(alerts_file, "w", encoding="utf-8") as f:
        json.dump({"site": "https://example.com",
                   "generated": "2020-01-01T00:00:00", "alerts": alerts}, f)
    rc = cmd_notify(build_parser().parse_args(
        ["run", "--dir", mdir, "--alerts", alerts_file]))
    assert rc == 4, "陈旧 alerts.json 必须 rc=4 拒发"
    rc = cmd_notify(build_parser().parse_args(
        ["run", "--dir", mdir, "--alerts", alerts_file, "--max-age", "0"]))
    assert rc == 0, "--max-age 0 关闭年龄检查"
    # --alerts 缺失 → 4
    rc = cmd_notify(build_parser().parse_args(["run", "--dir", mdir]))
    assert rc == 4
    # dead_man:库龄超 2×周期 → 注入即时告警
    import sqlite3 as _s3
    conn = _s3.connect(os.path.join(mdir, "monitor.db"))
    conn.execute("CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY, ts TEXT, kind TEXT, status TEXT)")
    conn.execute("INSERT INTO runs(ts,kind,status) VALUES('2020-01-01T00:00:00','daily','ok')")
    conn.commit()
    conn.close()
    dm = dead_man_alert(mdir, cfg)
    assert dm and dm["code"] == "dead_man"
    print("[self-test] PASS notify(分级路由/suppressed 剔除/指纹去重/env 注入/通用 webhook/"
          "URL 脱敏/分块转义/flush 保批/陈旧拒发/dead_man/P0-3 按类型路由+per-definition/"
          "redact 强化/incident 生命周期+resolve)")


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)
    if getattr(args, "self_test", False):
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL notify")
            return 1
    if not getattr(args, "cmd", None):
        ap.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
