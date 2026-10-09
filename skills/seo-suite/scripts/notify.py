#!/usr/bin/env python3
"""告警通知器(stdlib-only)。读 monitor.py diff 产出的告警 JSON,按级别路由:

  critical → 立即发(所有已配置渠道)
  warn     → 日批(暂存 pending,--flush warn 时发摘要)
  info     → 周批(暂存 pending,--flush info 时发摘要)
  low      → 静默(自愈只进 report,永不打扰)

渠道(config.json channels,secrets 留空则读环境变量):
  slack    webhook_url / env SEO_MONITOR_SLACK_WEBHOOK
  discord  webhook_url / env SEO_MONITOR_DISCORD_WEBHOOK
  telegram bot_token+chat_id / env SEO_MONITOR_TG_TOKEN + SEO_MONITOR_TG_CHAT
  email    smtp_host/port/use_ssl/username/from/to + env SEO_MONITOR_SMTP_PASS

用法:
  python3 notify.py --dir .seo-monitor --alerts .seo-monitor/alerts.json      # 路由 critical
  python3 notify.py --dir .seo-monitor --alerts ... --flush warn              # + 发送 warn 日批
  python3 notify.py --dir .seo-monitor --alerts ... --flush info              # + 发送 info 周批
  python3 notify.py --dir .seo-monitor --alerts ... --flush all --dry-run     # 全部演练,不联网
  cat alerts.json | python3 notify.py --dir .seo-monitor --stdin
  python3 notify.py --self-test

退出码:0=发送成功或无待发;1=发送失败(渠道报错);4=输入错误。
"""
import argparse
import json
import os
import smtplib
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


# ---------- 渠道发送(全部返回 (ok, detail);异常不抛出,由调用方汇总) ----------

def _post_json(url, payload, timeout=15):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "User-Agent": "seo-suite-notify/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(2000).decode("utf-8", "replace")


def env_or(cfg_value, env_name):
    return os.environ.get(env_name, "") or (cfg_value or "")


def channel_targets(cfg):
    """返回 [(渠道名, 发送函数)]——只收已配置的渠道。"""
    ch = cfg.get("channels", {})
    out = []

    if env_or(ch.get("slack", {}).get("webhook_url"), "SEO_MONITOR_SLACK_WEBHOOK"):
        out.append(("slack", lambda msg: _post_json(
            env_or(ch["slack"]["webhook_url"], "SEO_MONITOR_SLACK_WEBHOOK"),
            {"text": msg})))

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
    results = []
    for name, fn in targets:
        if dry_run:
            results.append((name, True, "dry-run 未发送"))
            continue
        try:
            st, detail = fn(msg)
            ok = 200 <= int(st) < 300 or int(st) == 250
            results.append((name, ok, "HTTP %s %s" % (st, detail[:200])))
        except Exception as e:
            results.append((name, False, "%s: %s" % (type(e).__name__, e)))
    return results


# ---------- 状态(日批/周批暂存) ----------

def load_state(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"pending_warn": [], "pending_info": [], "updated": None}


def save_state(path, st):
    st["updated"] = datetime.now().isoformat(timespec="seconds")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


def route_alerts(alerts, state):
    """分级抑制的核心路由:返回 immediate 列表,并把 warn/info 暂存进 state。"""
    immediate, nw, ni = [], 0, 0
    seen_fp = {p.get("fp") for p in state["pending_warn"]} | \
              {p.get("fp") for p in state["pending_info"]}
    for a in alerts:
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
    return immediate, nw, ni


# ---------- 主流程 ----------

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
    elif args.alerts:
        with open(args.alerts, encoding="utf-8") as f:
            payload = json.load(f)
    else:
        print("错误: 需要 --alerts FILE 或 --stdin", file=sys.stderr)
        return 4
    alerts = payload.get("alerts", [])
    site = payload.get("site") or cfg.get("site", "(site 未配置)")

    state = load_state(os.path.join(mdir, STATE_FILE))
    immediate, nw, ni = route_alerts(alerts, state)
    targets = channel_targets(cfg)
    rc = 0

    print("路由: critical=%d(即时) warn+%d(暂存日批,共 %d) info+%d(暂存周批,共 %d) low=%d(静默)"
          % (len(immediate), nw, len(state["pending_warn"]), ni,
             len(state["pending_info"]), sum(1 for a in alerts if a.get("level") == "low")))
    if not targets:
        print("[i] 无已配置渠道(config.json channels 全空)——只暂存不发送;"
              "webhook 可用环境变量注入(见 config notes)")

    if immediate:
        msg = format_alerts(site, immediate, "CRITICAL 即时告警")
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
        for name, ok, detail in send_all(targets, msg, args.dry_run):
            print("  [%s] %s: %s" % ("OK" if ok else "FAIL", name, detail))
            rc = rc or (0 if ok else 1)
        if not args.dry_run:
            state[key] = []

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
    p.add_argument("--dry-run", action="store_true", help="只打印路由与消息,不联网不写盘")
    p.set_defaults(func=cmd_notify)
    return ap


def _self_test():
    tmp = tempfile.mkdtemp(prefix="notify_selftest_")
    mdir = os.path.join(tmp, ".seo-monitor")
    os.makedirs(mdir)
    with open(os.path.join(mdir, "config.json"), "w", encoding="utf-8") as f:
        json.dump({"site": "https://example.com", "channels": {
            "slack": {"webhook_url": ""},
            "discord": {"webhook_url": ""},
            "telegram": {"bot_token": "", "chat_id": ""},
            "email": {"smtp_host": "", "from": "", "to": []},
        }}, f)

    # 分级路由:critical 即时 / warn·info 暂存去重 / low 静默
    st = load_state(os.path.join(mdir, STATE_FILE))
    alerts = [
        {"level": "critical", "code": "key_page_down", "key": "/pricing", "message": "404", "action": "x"},
        {"level": "warn", "code": "gsc_clicks_drop", "key": "file", "message": "-30%"},
        {"level": "warn", "code": "gsc_clicks_drop", "key": "file", "message": "-30%"},
        {"level": "info", "code": "title_meta_drift", "key": "/", "message": "hash 变"},
        {"level": "low", "code": "x_resolved", "key": "/", "message": "自愈"},
    ]
    imm, nw, ni = route_alerts(alerts, st)
    assert len(imm) == 1 and imm[0]["level"] == "critical"
    assert nw == 1 and ni == 1                       # 重复 warn 指纹只暂存一次
    assert len(st["pending_warn"]) == 1 and not any(p["level"] == "low" for p in st["pending_info"])
    imm2, nw2, _ = route_alerts(alerts, st)
    assert len(imm2) == 1 and nw2 == 0               # 第二轮同指纹不再暂存
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
        json.dump({"site": "https://example.com", "alerts": alerts}, f)
    rc = cmd_notify(build_parser().parse_args(
        ["run", "--dir", mdir, "--alerts", alerts_file, "--flush", "all", "--dry-run"]))
    assert rc == 0, rc
    # flush 后批清空(非 dry-run)
    rc = cmd_notify(build_parser().parse_args(
        ["run", "--dir", mdir, "--alerts", alerts_file, "--flush", "all"]))
    assert rc == 0
    st3 = load_state(os.path.join(mdir, STATE_FILE))
    assert st3["pending_warn"] == [] and st3["pending_info"] == []
    # --alerts 缺失 → 4
    rc = cmd_notify(build_parser().parse_args(["run", "--dir", mdir]))
    assert rc == 4
    print("[self-test] PASS notify(分级路由/指纹去重/env 注入/分块转义/flush 清批/dry-run)")


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
