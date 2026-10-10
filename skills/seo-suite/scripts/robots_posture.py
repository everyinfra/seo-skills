#!/usr/bin/env python3
"""robots.txt AI 爬虫姿势分析器(stdlib)。读取 robots.txt,按 RFC 9309(连续 UA 合并/
最长匹配/Allow 平局胜出)对 27 个 AI bot 三层名单(training/search/user)做四态判定
(allowed/blocked/partial/missing),检测 Cloudflare 注入块,输出两级引用评分
(citation_bots_ok / citation_bots_explicit)、分层统计、Content-Signal 建议与警告,
可选 --fix-robots 打印修复建议块(只打印不写盘)。geo-optimizer 源码口径(borrow-specs C3)。
用法: python3 robots_posture.py https://example.com/robots.txt [--signal visibility|protect-ip] [--json] [--fix-robots]"""
import json, sys, urllib.request

UA = "Mozilla/5.0 (compatible; seo-suite-audit/1.0)"
MAX_BYTES = 500_000  # RFC 9309: 超过 500KiB 的 robots.txt 至少按前 500KiB 处理

# ---------------------------------------------------------------------------
# 27 bot 三层名单(模块级常量,geo-optimizer docs/ai-bots-reference.md 口径;
# 分类证据见 references/technical/ai-crawler-policy.md)
#   training: 基础模型训练——封禁是授权决策,不影响搜索/AI 答案可见性
#   search:   搜索/答案索引——决定 AI 引用,封禁=逐出 AI 答案
#   user:     按用户请求抓取(对话里用户点名某个 URL 时去取)——封禁=用户实测不可达
# ---------------------------------------------------------------------------
AI_BOTS = [
    # --- training(12;合计 27 bot=12+10+5。ai-crawler-policy.md 全局训练名单仅 GPTBot/
    #     ClaudeBot/CCBot,无更全者可补;MistralAI-Training 属法语区市场专属,不入全局名单) ---
    {"token": "GPTBot",               "desc": "OpenAI GPT 模型训练(禁它不影响 ChatGPT 引用,引用走 OAI-SearchBot)", "tier": "training"},
    {"token": "ClaudeBot",            "desc": "Anthropic Claude 模型训练(引用走 Claude-SearchBot)",                "tier": "training"},
    {"token": "Google-Extended",      "desc": "Google Gemini 训练(不是 AI Overviews 开关)",                         "tier": "training"},
    {"token": "Google-CloudVertexBot","desc": "Google Vertex AI 训练/评估",                                          "tier": "training"},
    {"token": "Applebot-Extended",    "desc": "Apple Intelligence 训练(与 Applebot 收录分离)",                      "tier": "training"},
    {"token": "cohere-ai",            "desc": "Cohere 模型训练",                                                     "tier": "training"},
    {"token": "Bytespider",           "desc": "字节跳动模型训练(抖音/豆包)",                                          "tier": "training"},
    {"token": "meta-externalagent",   "desc": "Meta AI 模型训练",                                                    "tier": "training"},
    {"token": "PetalBot",             "desc": "华为 Petal 搜索/AI 抓取",                                              "tier": "training"},
    {"token": "AI2Bot",               "desc": "Allen AI(OLMo/Semantic Scholar)训练抓取",                            "tier": "training"},
    {"token": "AI2Bot-Dolma",         "desc": "Allen AI Dolma 数据集训练",                                           "tier": "training"},
    {"token": "CCBot",                "desc": "Common Crawl 训练数据源",                                              "tier": "training"},
    # --- search(10,决定 AI 引用) ---
    {"token": "OAI-SearchBot",        "desc": "OpenAI ChatGPT 搜索索引(AI 引用入口)",                                "tier": "search"},
    {"token": "Claude-SearchBot",     "desc": "Anthropic Claude 搜索索引(AI 引用入口)",                              "tier": "search"},
    {"token": "PerplexityBot",        "desc": "Perplexity 搜索/引用(不训练)",                                         "tier": "search"},
    {"token": "Googlebot",            "desc": "Google 通用收录+AI Overviews",                                        "tier": "search"},
    {"token": "Applebot",             "desc": "Apple Siri/Spotlight 收录",                                           "tier": "search"},
    {"token": "Bingbot",              "desc": "Bing 收录(喂 Copilot,无独立 Copilot bot)",                            "tier": "search"},
    {"token": "DuckAssistBot",        "desc": "DuckDuckGo Duck.ai 答案抓取",                                         "tier": "search"},
    {"token": "YouBot",               "desc": "You.com 搜索/AI 答案",                                                "tier": "search"},
    {"token": "Amazonbot",            "desc": "Amazon Alexa/Rufus 索引",                                             "tier": "search"},
    {"token": "xAI-Bot",              "desc": "xAI Grok 检索索引",                                                   "tier": "search"},
    # --- user(5,按用户请求抓取) ---
    {"token": "ChatGPT-User",         "desc": "OpenAI 按用户请求抓取(ChatGPT;厂商声明可能无视 robots)",              "tier": "user"},
    {"token": "Claude-User",          "desc": "Anthropic 按用户请求抓取(Claude)",                                     "tier": "user"},
    {"token": "Perplexity-User",      "desc": "Perplexity 按用户请求抓取",                                            "tier": "user"},
    {"token": "Meta-ExternalFetcher", "desc": "Meta AI 按用户请求抓取",                                               "tier": "user"},
    {"token": "facebookexternalhit",  "desc": "Meta 链接预览抓取",                                                    "tier": "user"},
]

# 引用型 5 bot(刻意排除纯训练的 ClaudeBot:禁 ClaudeBot 不阻止 Claude 引用,引用走 Claude-SearchBot)
CITATION_BOTS = ["OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "Googlebot", "Applebot"]

TIER_LABELS = {"search": "检索", "user": "按需", "training": "训练"}
TIER_ORDER = ("search", "user", "training")  # 展示顺序:先可见性攸关层,后授权决策层
SIGNALS = {"visibility": "search=yes, ai-input=yes, ai-train=yes",
           "protect-ip": "search=yes, ai-input=yes, ai-train=no"}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read(MAX_BYTES).decode("utf-8", "replace")

# ---------------------------------------------------------------------------
# 旧版简单解析器(冻结契约:tests/run_tests.py 直接消费,勿改行为)
# ---------------------------------------------------------------------------
def parse_groups(txt):
    groups, cur, order = {}, "*", []
    for line in txt.splitlines():
        s = line.split("#")[0].strip()
        if not s: continue
        k, _, v = s.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            cur = v or "*"
            groups.setdefault(cur, {"allow": [], "disallow": []}); order.append(cur)
        elif k in ("allow", "disallow") and cur:
            groups[cur][k].append(v)
    return groups, order

# ---------------------------------------------------------------------------
# RFC 9309 解析强化:BOM 剥离 / 500KB 截断 / 连续 User-agent 行合并成规则组 /
# 提取 crawl-delay(取 * 组)与 Sitemap 指令
# ---------------------------------------------------------------------------
def parse_robots(txt):
    """返回 {groups, sitemaps, crawl_delay, truncated}。
    groups 键为小写 token(token 匹配大小写不敏感),值为
    {"token": 原样名, "allow": [path], "disallow": [path], "crawl_delay": float|None}。"""
    if txt.startswith("\ufeff"):          # BOM 剥离
        txt = txt[1:]
    truncated = len(txt) > MAX_BYTES  # 500KB 截断守卫
    if truncated:
        txt = txt[:MAX_BYTES]
    groups, sitemaps = {}, []
    cur, last_was_ua = [], False      # 连续 UA 行共享后续规则;规则行之后的新 UA 开新组
    for line in txt.splitlines():
        s = line.split("#", 1)[0].strip()
        if not s: continue
        k, _, v = s.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            if not last_was_ua:
                cur = []
            tok = v or "*"
            cur.append(tok)
            groups.setdefault(tok.lower(), {"token": tok, "allow": [], "disallow": [], "crawl_delay": None})
            last_was_ua = True
        elif k in ("allow", "disallow") and cur:
            for t in cur:
                groups.setdefault(t.lower(), {"token": t, "allow": [], "disallow": [], "crawl_delay": None})[k].append(v)
            last_was_ua = False
        elif k == "crawl-delay" and cur:
            for t in cur:
                g = groups.setdefault(t.lower(), {"token": t, "allow": [], "disallow": [], "crawl_delay": None})
                if g["crawl_delay"] is None:
                    try: g["crawl_delay"] = float(v)
                    except ValueError: pass
            last_was_ua = False
        elif k == "sitemap" and v:
            sitemaps.append(v)
            last_was_ua = False
        elif k:
            last_was_ua = False
    return {"groups": groups, "sitemaps": sitemaps,
            "crawl_delay": groups.get("*", {}).get("crawl_delay"), "truncated": truncated}

def rule_matches(rule, path):
    """RFC 9309 前缀匹配:空值匹配一切。"""
    return rule == "" or path.startswith(rule)

def effective_rule(group, path="/"):
    """最长规则匹配;同长时 Allow 平局胜出(RFC 9309 最具体的规则赢,平局归 Allow)。
    无任何匹配规则时默认允许。返回 ("allow"|"disallow", 匹配长度),无匹配为 -1。"""
    best_type, best_len = "allow", -1
    for kind in ("allow", "disallow"):
        for rule in group.get(kind, []):
            if not rule_matches(rule, path): continue
            n = len(rule)
            if n > best_len or (n == best_len and kind == "allow"):
                best_type, best_len = kind, n
    return best_type, best_len

def classify(doc, bot):
    """四态判定(站点根 '/' 口径)+ via_wildcard 标记。
    missing  : 既无专属组也无 * 组(robots 对它只字未提,不算放行)
    allowed  : 根路径裁定为允许(专属组或 * 组)
    blocked  : 根路径裁定为禁止且无开洞
    partial  : Disallow: / 但有具体 Allow 路径(>1)开洞——只放行部分路径
    via_wildcard: True=结论来自 * 组而非 bot 专属规则(通配符 Allow 也行,但拿不到全分)。"""
    groups = doc["groups"]
    own = groups.get(bot.lower())
    star = groups.get("*")
    if own is not None:
        g, via = own, False
    elif star is not None:
        g, via = star, True
    else:
        return {"state": "missing", "via_wildcard": False}
    verdict, _ = effective_rule(g, "/")
    if verdict == "allow":
        state = "allowed"
    elif any(len(a) > 1 for a in g.get("allow", [])):
        state = "partial"
    else:
        state = "blocked"
    return {"state": state, "via_wildcard": via}

def citation_report(doc):
    """两级评分(geo-optimizer 口径):
    ok       = 5 个引用 bot 全部 allowed(含靠 * 通配)→ 部分分
    explicit = 5 个都有专属规则(非仅靠 `*` 通配)且 allowed → 满分
    (通配符 Allow 也行,但拿不到全分)"""
    states = {b: classify(doc, b) for b in CITATION_BOTS}
    ok = all(s["state"] == "allowed" for s in states.values())
    explicit = all(s["state"] == "allowed" and not s["via_wildcard"] for s in states.values())
    return {"ok": ok, "explicit": explicit,
            "allowed_count": sum(1 for s in states.values() if s["state"] == "allowed"),
            "explicit_count": sum(1 for s in states.values() if s["state"] == "allowed" and not s["via_wildcard"]),
            "bots": states}

def analyze(txt, mode="visibility"):
    """全量分析:27 bot 四态矩阵 + 分层统计 + 两级引用评分 + 指令提取。"""
    doc = parse_robots(txt)
    bots = []
    for item in AI_BOTS:
        c = classify(doc, item["token"])
        bots.append({"token": item["token"], "desc": item["desc"], "tier": item["tier"],
                     "state": c["state"], "via_wildcard": c["via_wildcard"]})
    buckets = {s: [b["token"] for b in bots if b["state"] == s]
               for s in ("allowed", "blocked", "missing", "partial")}
    tiers = {}
    for tier in ("training", "search", "user"):
        sub = [b for b in bots if b["tier"] == tier]
        tiers[tier] = {"total": len(sub)}
        tiers[tier].update({s: sum(1 for b in sub if b["state"] == s)
                            for s in ("allowed", "blocked", "missing", "partial")})
    return {
        "schema_version": "2",
        "cloudflare_injected": "# BEGIN Cloudflare Managed content" in txt,
        "deprecated_tokens": [t for t in ("anthropic-ai", "Claude-Web", "ChatGPT-Plugins") if t in txt],
        "truncated": doc["truncated"],
        "crawl_delay": doc["crawl_delay"],
        "sitemaps": doc["sitemaps"],
        "bots": bots,
        "bots_allowed": buckets["allowed"], "bots_blocked": buckets["blocked"],
        "bots_missing": buckets["missing"], "bots_partial": buckets["partial"],
        "tiers": tiers,
        "citation": citation_report(doc),
        # answers vs training 分层:封 search/user 才是可见性失败;封 training 只是授权决策不扣分
        "visibility_failures": [b["token"] for b in bots
                                if b["tier"] in ("search", "user") and b["state"] in ("blocked", "partial")],
        "content_signal": SIGNALS.get(mode, SIGNALS["visibility"]),
    }

# ---------------------------------------------------------------------------
# --fix-robots:修复建议块(缺失/被封的 bot 逐个 "# {desc}\nUser-agent: {token}\nAllow: /";
# 同长规则 Allow 平局胜出,故追加 Allow: / 即可翻转既有 Disallow: /;只打印不写盘)
# ---------------------------------------------------------------------------
def fix_robots(report):
    lines = ["== robots.txt 修复建议(追加到现有 robots.txt 末尾;只打印不写盘)==", ""]
    headers = {"search": "# —— 引用层(search):被封/缺失=逐出 AI 答案,建议追加 ——",
               "user":   "# —— 按需层(user):封禁=用户端不可达,建议追加 ——",
               "training": "# —— 训练层(training):封禁是授权决策而非错误,仅在你决定开放时追加 ——"}
    for tier in TIER_ORDER:
        need = [b for b in report["bots"] if b["tier"] == tier and b["state"] != "allowed"]
        if not need: continue
        lines.append(headers[tier])
        for b in need:
            lines += [f"# {b['desc']}", f"User-agent: {b['token']}", "Allow: /", ""]
    wild = [b for b in report["bots"] if b["token"] in CITATION_BOTS
            and b["state"] == "allowed" and b["via_wildcard"]]
    if wild:  # 通配符放行的引用 bot:补专属规则才拿得到 citation 满分
        lines.append("# —— 专属规则补全:通配符 Allow 也行,但 citation 评分拿不到全分 ——")
        for b in wild:
            lines += [f"# {b['desc']}", f"User-agent: {b['token']}", "Allow: /", ""]
    if len(lines) == 2:
        return "== robots.txt 修复建议:无需修复(引用/按需层全部放行,引用 5 bot 均有专属规则)=="
    return "\n".join(lines).rstrip() + "\n"

STATUS = {
    "search":   {"allowed": "✅", "blocked": "❌ 禁(逐出AI答案)", "partial": "◐ 部分(仅Allow路径)", "missing": "❓ 未提及"},
    "user":     {"allowed": "✅", "blocked": "❌ 禁(用户端不可达)", "partial": "◐ 部分(仅Allow路径)", "missing": "❓ 未提及"},
    "training": {"allowed": "放行", "blocked": "禁(不影响搜索,授权决策)", "partial": "部分(仅Allow路径)", "missing": "未提及(默认放行)"},
}

def render(report):
    out = []
    if report["cloudflare_injected"]:
        out.append("⚠ Cloudflare 边缘注入块存在(站长源文件看不到)——去 Security→Bot traffic 关闭 block training")
    out.append(f"{'bot':<22}{'类别':<8}状态")
    for tier in TIER_ORDER:
        for b in report["bots"]:
            if b["tier"] != tier: continue
            mark = STATUS[tier][b["state"]]
            if b["state"] == "allowed" and b["via_wildcard"] and tier != "training":
                mark = "✅(靠 * 通配)"
            out.append(f"{b['token']:<22}{TIER_LABELS[tier]:<8}{mark}")
    out.append("")
    for s in ("allowed", "blocked", "missing", "partial"):
        lst = report[f"bots_{s}"]
        out.append(f"bots_{s}({len(lst)}): " + (", ".join(lst) if lst else "-"))
    t = report["tiers"]
    out.append(f"\n分层统计: training {t['training']['allowed']}/{t['training']['total']} 放行"
               f" | search {t['search']['allowed']}/{t['search']['total']} 放行"
               f" | user {t['user']['allowed']}/{t['user']['total']} 放行")
    c = report["citation"]
    out.append(f"citation_bots_ok: {'✅' if c['ok'] else '❌'} {c['allowed_count']}/5 放行"
               + ("(基础分)" if c["ok"] else "(可见性失败:引用 bot 被封/未被放行)"))
    out.append(f"citation_bots_explicit: {'✅' if c['explicit'] else '⚠'} {c['explicit_count']}/5 专属规则"
               + ("(满分)" if c["explicit"] else "(未满分:通配符 Allow 也行,但拿不到全分)"))
    if report["visibility_failures"]:
        out.append(f"可见性失败: {', '.join(report['visibility_failures'])}(封 search/user 才是可见性失败;"
                   f"封 training 只是授权决策,不扣分)")
    else:
        out.append("可见性结论: ✅ 引用(search)与按需(user)bot 无封禁;training 封禁属授权决策,不扣分")
    out.append("\n过时 token 检查: " + (", ".join(report["deprecated_tokens"]) if report["deprecated_tokens"] else "无"))
    sm = report["sitemaps"]
    out.append("Sitemap 行: " + (f"有({len(sm)} 条)" if sm else "❌ 缺"))
    out.append("Crawl-delay(* 组): " + (str(report["crawl_delay"]) if report["crawl_delay"] is not None else "无"))
    out.append(f"\n建议 Content-Signal(业务决策,Googlebot 不遵守、非排名因素):\n  Content-Signal: {report['content_signal']}")
    return "\n".join(out)

USAGE = """usage: robots_posture.py URL [--signal visibility|protect-ip] [--json] [--fix-robots]
URL 通常是 https://site/robots.txt(给站点根也行,自动拼 /robots.txt;file:// 本地文件亦可)。
读取 robots.txt,输出 27 bot 三层矩阵(training/search/user)+四态判定(allowed/blocked/
partial/missing)+两级引用评分(citation_bots_ok/citation_bots_explicit)+分层统计
+bots_allowed/bots_blocked/bots_missing/bots_partial 四列表+Cloudflare 注入检测
+Crawl-delay/Sitemap 提取+Content-Signal 建议。封 training 不扣分(授权决策),
封 search/user 才是可见性失败。
--signal      visibility|protect-ip(Content-Signal 建议)
--json        结构化输出(同上字段,供 agent 消费)
--fix-robots  打印修复建议块(# 描述 + User-agent: {token} + Allow: /,可追加到现有
              robots.txt;只打印不写盘)"""

def main():
    a = sys.argv[1:]
    if any(x in ("-h", "--help") for x in a):
        print(USAGE); return
    url, mode = None, None
    as_json, fix = "--json" in a, "--fix-robots" in a
    i = 0
    while i < len(a):
        x = a[i]
        if x == "--signal":
            mode = a[i + 1] if i + 1 < len(a) and not a[i + 1].startswith("-") else "visibility"
            i += 2
        elif x in ("--json", "--fix-robots"):
            i += 1
        elif x.startswith("-") or url is not None:
            sys.stderr.write(USAGE + "\n"); sys.exit(2)
        else:
            url = x; i += 1
    if not url:
        sys.stderr.write(USAGE + "\n"); sys.exit(2)
    url = url.rstrip("/") + "/robots.txt" if not url.rstrip("/").endswith("robots.txt") else url
    try:
        txt = fetch(url)
    except Exception as e:
        sys.stderr.write(f"抓取失败 {url}: {e}\n"); sys.exit(1)
    report = analyze(txt, mode or "visibility")
    if as_json:
        payload = dict(report)
        if fix:
            payload["fix_robots"] = fix_robots(report)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(render(report))
    if fix:
        print("\n" + fix_robots(report))

if __name__ == "__main__": main()
