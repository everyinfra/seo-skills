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
  python3 notify.py --self-test

退出码:0=发送成功或无待发;1=发送失败(渠道报错);4=输入错误(含 alerts 文件过期)。
"""
import argparse
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
LEVELS = ("critical", "warn", "info", "low")
DISCORD_LIMIT, TELEGRAM_LIMIT = 1900, 3800


# ---------- 工具 ----------

def redact(s):
    """URL 脱敏(audit 05-§4/TrendWatch 惯例):保留 scheme+host,路径查询(含 token)打码,
    防 webhook token 经 GH Actions 日志泄漏。"""
    return re.sub(r"(https?://[^/\s'\"]+)[^\s'\"]*", r"\1/[REDACTED]", str(s))


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


def channel_targets(cfg):
    """返回 [(渠道名, 发送函数)]——只收已配置的渠道;渠道间故障隔离由 send_all 保证。"""
    ch = cfg.get("channels", {})
    out = []

    slack_url = env_or(ch.get("slack", {}).get("webhook_url"), "SEO_MONITOR_SLACK_WEBHOOK")
    if slack_url:
        out.append(("slack", lambda msg: _post_json(slack_url, {"text": msg})))

    if env_or(ch.get("discord", {}).get("webhook_url"), "SEO_MONITOR_DISCORD_WEBHOOK"):
        url = env_or(ch["discord"]["webhook_url"], "SEO_MONITOR_DISCORD_WEBHOOK")

        def send_discord(msg):
            sent = ""
            for chunk in _chunk(msg, DISCORD_LIMIT):
                st, body = _post_json(url, {"content": chunk})
                sent += body
            return st, sent
        out.append(("discord", send_discord))

    tg = ch.get("telegram", {})
    token = env_or(tg.get("bot_token"), "SEO_MONITOR_TG_TOKEN")
    chat = env_or(tg.get("chat_id"), "SEO_MONITOR_TG_CHAT")
    if token and chat:
        def send_tg(msg):
            api = "https://api.telegram.org/bot%s/sendMessage" % token
            sent = ""
            for chunk in _chunk(_tg_escape(msg), TELEGRAM_LIMIT):
                st, body = _post_json(api, {"chat_id": chat, "text": chunk, "parse_mode": "HTML"})
                sent += body
            return st, sent
        out.append(("telegram", send_tg))

    gw = ch.get("webhook") or {}
    gw_url = env_or(gw.get("url") or gw.get("webhook_url"), "SEO_MONITOR_WEBHOOK_URL")
    if gw_url:
        out.append(("webhook", lambda msg: send_generic_webhook(gw_url, msg)))

    em = ch.get("email", {})
    if em.get("smtp_host") and em.get("from") and em.get("to"):
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
        out.append(("email", send_mail))
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
    rc = 0

    print("路由: critical=%d(即时) warn+%d(暂存日批,共 %d) info+%d(暂存周批,共 %d) "
          "low=%d(静默) suppressed=%d(冷却期内,不通知)%s"
          % (len(immediate) - (1 if dm else 0), nw, len(state["pending_warn"]), ni,
             len(state["pending_info"]), sum(1 for a in alerts if a.get("level") == "low"),
             ns, " dead_man=1(监控停摆)" if dm else ""))
    if not targets:
        print("[i] 无已配置渠道(config.json channels 全空)——只暂存不发送;"
              "webhook 可用环境变量注入(见 config notes)")

    if immediate:
        msg = format_alerts(site, immediate, "CRITICAL 即时告警" if not dm else "即时告警(含 dead_man)")
        for name, ok, detail in send_all(targets, msg, args.dry_run):
            print("  [%s] %s: %s" % ("OK" if ok else "FAIL", name, detail))
            rc = rc or (0 if ok else 1)

    flush = (args.flush or "")
    digests = []
    if flush in ("warn", "all") and state["pending_warn"]:
        digests.append(("warn 日批摘要", state["pending_warn"], "pending_warn"))
    if flush in ("info", "all") and state["pending_info"]:
        digests.append(("info 周批摘要", state["pending_info"], "pending_info"))
    for title, batch, key in digests:
        msg = format_alerts(site, batch, title)
        results = send_all(targets, msg, args.dry_run)
        for name, ok, detail in results:
            print("  [%s] %s: %s" % ("OK" if ok else "FAIL", name, detail))
            rc = rc or (0 if ok else 1)
        # P1-14(audit 05-§3 反向问题):只在全部渠道成功(或本无渠道)后清批,
        # 渠道失败保留 pending——绝不因发送失败而丢告警。
        if not args.dry_run:
            if all(ok for _, ok, _ in results):
                state[key] = []
            else:
                print("  [!] %s 有渠道失败,pending 保留(下次 flush 重试,不丢告警)" % title)

    if not args.dry_run:
        save_state(os.path.join(mdir, STATE_FILE), state)
    else:
        print("[dry-run] 状态未写盘")
    return rc


# ---------- CLI / 自测 ----------

def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
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
          "URL 脱敏/分块转义/flush 保批/陈旧拒发/dead_man)")


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
