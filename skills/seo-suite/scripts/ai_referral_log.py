#!/usr/bin/env python3
"""AI 引用流量日志分析(下界口径)。stdlib-only。

读 apache/nginx combined 日志(stdin 或文件),按 AI referrer 域归因请求:
  chatgpt.com / perplexity.ai / gemini.google.com / copilot.microsoft.com /
  claude.ai / grok.com(含子域)。

输出:
  - 每域请求数 + 独立路径数
  - 全站热门路径 top20(按命中)
  - 无 referrer 请求数 → 提示:App 内打开常不带 referrer,测得的是下界
  - --bot-ua:同时统计 AI 爬虫 UA(GPTBot / OAI-SearchBot / ChatGPT-User /
    ClaudeBot / Claude-SearchBot / PerplexityBot)的到访(先行指标:先爬后引)

combined 格式:
  IP - user [time] "METHOD path HTTP/x" status bytes "referer" "user-agent"

用法:
  cat access.log | python3 ai_referral_log.py
  python3 ai_referral_log.py access.log [--top 20] [--bot-ua]
  python3 ai_referral_log.py --self-test
"""
import argparse
import re
import sys
import traceback
from collections import Counter

AI_REFERRER_DOMAINS = ("chatgpt.com", "perplexity.ai", "gemini.google.com",
                       "copilot.microsoft.com", "claude.ai", "grok.com")
BOT_UAS = ("GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot",
           "Claude-SearchBot", "PerplexityBot")

LOG_RE = re.compile(
    r'^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"([^"]*)"\s+(\d{3})\s+(\S+)'
    r'(?:\s+"([^"]*)"\s+"([^"]*)")?')

BOT_UA_RE = re.compile("|".join(re.escape(b) for b in BOT_UAS))


def parse_line(line):
    m = LOG_RE.match(line)
    if not m:
        return None
    ip, ts, request, status, _bytes, referer, ua = m.groups()
    parts = (request or "").split(" ")
    path = parts[1] if len(parts) >= 2 else (parts[0] if parts else "-")
    return {"ip": ip, "ts": ts, "path": path, "status": status,
            "referer": referer or "-", "ua": ua or "-"}


def referrer_host(referer):
    if not referer or referer == "-":
        return ""
    host = referer.strip().lower()
    if "://" in host:
        host = host.split("://", 1)[1]
    return host.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]


def match_ai_domain(host):
    """host 命中 AI 引用域(精确或子域)→ 返回该域,否则 None。"""
    if not host:
        return None
    for d in AI_REFERRER_DOMAINS:
        if host == d or host.endswith("." + d):
            return d
    return None


def analyze(lines, with_bots=False):
    stats = {d: {"hits": 0, "paths": Counter()} for d in AI_REFERRER_DOMAINS}
    all_paths = Counter()
    total = parsed = no_ref = 0
    bots = {b: {"hits": 0, "ips": set(), "first": None, "last": None} for b in BOT_UAS}
    for line in lines:
        line = (line or "").rstrip("\n")
        if not line.strip():
            continue
        total += 1
        rec = parse_line(line)
        if rec is None:
            continue
        parsed += 1
        all_paths[rec["path"]] += 1
        host = referrer_host(rec["referer"])
        if not host:
            no_ref += 1
        dom = match_ai_domain(host)
        if dom:
            stats[dom]["hits"] += 1
            stats[dom]["paths"][rec["path"]] += 1
        if with_bots:
            m = BOT_UA_RE.search(rec["ua"])
            if m:
                b = m.group(0)
                bots[b]["hits"] += 1
                bots[b]["ips"].add(rec["ip"])
                bots[b]["first"] = bots[b]["first"] or rec["ts"]
                bots[b]["last"] = rec["ts"]
    return {"total": total, "parsed": parsed, "no_ref": no_ref,
            "stats": stats, "all_paths": all_paths, "bots": bots,
            "ai_total": sum(s["hits"] for s in stats.values())}


def render(res, top=20, with_bots=False):
    L = ["== AI 引用流量日志分析 =="]
    L.append("日志行 %d | 可解析 %d | 无 referrer %d"
             % (res["total"], res["parsed"], res["no_ref"]))
    L.append("-- AI referrer 域(请求数 / 独立路径数)--")
    any_hit = False
    for d in AI_REFERRER_DOMAINS:
        s = res["stats"][d]
        if s["hits"]:
            any_hit = True
        L.append("  %-26.26s %6d  %6d" % (d, s["hits"], len(s["paths"])))
    L.append("  合计 AI referrer 请求: %d" % res["ai_total"])
    L.append("-- 热门路径 top%d(全站,含非 AI)--" % top)
    for path, cnt in res["all_paths"].most_common(top):
        L.append("  %-50.50s %d" % (path, cnt))
    if not any_hit:
        L.append("  [i] 未检出任何 AI referrer 命中")
    L.append("[!] App 内打开常不带 referrer——测得的是下界;"
             "AI 实际引流 >= 此处数字")
    if with_bots:
        L.append("-- AI 爬虫到访(先行指标:先爬后引) --")
        any_bot = False
        for b in BOT_UAS:
            s = res["bots"][b]
            if s["hits"]:
                any_bot = True
                L.append("  %-18.18s hits=%-5d ip=%-4d first=%s last=%s"
                         % (b, s["hits"], len(s["ips"]),
                            (s["first"] or "")[:11], (s["last"] or "")[:11]))
        if not any_bot:
            L.append("  [i] 未检出已知 AI 爬虫 UA")
        L.append("  [i] 爬虫到访 ≠ 已被引用;引用看 referrer,到访看 UA")
    return "\n".join(L)


SAMPLE_LOG = "\n".join([
    '1.2.3.4 - - [09/Oct/2026:10:00:00 +0800] "GET /pricing HTTP/1.1" 200 512 "https://chatgpt.com/" "Mozilla/5.0"',
    '5.6.7.8 - - [09/Oct/2026:10:05:00 +0800] "GET /blog/geo HTTP/1.1" 200 1024 "https://www.perplexity.ai/search?q=crm" "Mozilla/5.0"',
    '9.9.9.9 - - [09/Oct/2026:10:06:00 +0800] "GET /pricing HTTP/1.1" 200 256 "https://gemini.google.com/app" "Mozilla/5.0"',
    '1.2.3.4 - - [09/Oct/2026:10:07:00 +0800] "GET / HTTP/1.1" 200 128 "https://claude.ai/chat/abc" "Mozilla/5.0"',
    '2.2.2.2 - - [09/Oct/2026:10:08:00 +0800] "GET /x HTTP/1.1" 200 64 "-" "Mozilla/5.0"',
    '3.3.3.3 - - [09/Oct/2026:11:00:00 +0800] "GET /api/data HTTP/1.1" 200 32 "-" "Mozilla/5.0 (compatible; GPTBot/1.0; +https://openai.com/gptbot)"',
    '4.4.4.4 - - [09/Oct/2026:11:01:00 +0800] "GET /api/data HTTP/1.1" 200 32 "-" "Mozilla/5.0 (compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexity-bot)"',
    'garbage line that does not parse',
])


def _self_test():
    lines = SAMPLE_LOG.splitlines()
    res = analyze(lines, with_bots=True)
    assert res["total"] == 8 and res["parsed"] == 7      # 1 行垃圾
    assert res["stats"]["chatgpt.com"]["hits"] == 1
    assert res["stats"]["perplexity.ai"]["hits"] == 1    # www 子域命中
    assert res["stats"]["gemini.google.com"]["hits"] == 1
    assert res["stats"]["claude.ai"]["hits"] == 1
    assert res["stats"]["copilot.microsoft.com"]["hits"] == 0
    assert res["stats"]["grok.com"]["hits"] == 0
    assert res["ai_total"] == 4
    assert res["no_ref"] == 3
    assert res["all_paths"]["/pricing"] == 2 and res["all_paths"]["/api/data"] == 2
    assert res["stats"]["perplexity.ai"]["paths"]["/blog/geo"] == 1
    assert res["bots"]["GPTBot"]["hits"] == 1 and res["bots"]["PerplexityBot"]["hits"] == 1
    assert len(res["bots"]["GPTBot"]["ips"]) == 1
    assert res["bots"]["GPTBot"]["last"].startswith("09/Oct/2026:11:00")
    # referrer 提取
    assert referrer_host("https://www.perplexity.ai/search?q=crm") == "www.perplexity.ai"
    assert referrer_host("-") == "" and referrer_host("") == ""
    assert match_ai_domain("www.perplexity.ai") == "perplexity.ai"
    assert match_ai_domain("perplexity.ai") == "perplexity.ai"
    assert match_ai_domain("evil-perplexity.ai.example.com") is None
    assert match_ai_domain("notai.com") is None
    out = render(res, top=20, with_bots=True)
    assert "下界" in out and "GPTBot" in out and "chatgpt.com" in out
    assert "未检出" not in out.split("AI 爬虫到访")[1].split("[i]")[0]
    print("[self-test] PASS ai_referral_log(7 行解析,4 域命中,无 referrer=3,"
          "bot UA 先行指标,子域匹配,anti 误匹配)")


def read_lines(args_input):
    if args_input and args_input != "-":
        with open(args_input, encoding="utf-8", errors="replace") as f:
            return f.readlines()
    return sys.stdin.readlines()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", nargs="?", default=None,
                    help="日志文件(缺省读 stdin)")
    ap.add_argument("--top", type=int, default=20, help="热门路径 top N(默认 20)")
    ap.add_argument("--bot-ua", dest="bot_ua", action="store_true",
                    help="同时统计 AI 爬虫 UA 到访(先行指标)")
    ap.add_argument("--self-test", action="store_true", help="冒烟自测(不联网)")
    args = ap.parse_args(argv)
    if args.self_test:
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL ai_referral_log")
            return 1
    if args.input is None and sys.stdin.isatty():
        ap.error("需要日志文件参数,或通过管道传入(如 cat access.log | %s)"
                 % sys.argv[0])
    res = analyze(read_lines(args.input), with_bots=args.bot_ua)
    print(render(res, top=args.top, with_bots=args.bot_ua))
    return 0


if __name__ == "__main__":
    sys.exit(main())
