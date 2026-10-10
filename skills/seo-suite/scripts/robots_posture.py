#!/usr/bin/env python3
"""robots.txt AI 爬虫姿势分析器(stdlib)。读取 robots.txt,分类检索/训练爬虫放行状态,
检测 Cloudflare 注入块,输出 Content-Signal 建议与警告。合并百仓深扫的爬虫矩阵。
用法: python3 robots_posture.py https://example.com/robots.txt [--signal visibility|protect-ip]"""
import sys, urllib.request

UA = "Mozilla/5.0 (compatible; seo-suite-audit/1.0)"
TIER1 = ["OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "Claude-User", "PerplexityBot"]
TIER2 = ["Google-Extended", "GoogleOther", "Applebot-Extended", "Amazonbot", "FacebookBot"]
TRAIN = ["GPTBot", "ClaudeBot", "CCBot", "anthropic-ai", "cohere-ai", "Bytespider", "Meta-ExternalAgent"]
SIGNALS = {"visibility": "search=yes, ai-input=yes, ai-train=yes",
           "protect-ip": "search=yes, ai-input=yes, ai-train=no"}

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read(500_000).decode("utf-8", "replace")

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

def matches(rule, dummy_path="/"):
    return rule in ("", "/")

USAGE = """usage: robots_posture.py URL [--signal visibility|protect-ip]
URL 通常是 https://site/robots.txt(给站点根也行,自动拼 /robots.txt)。
读取 robots.txt,输出检索/建议/训练三类爬虫放行矩阵+Cloudflare 注入检测+Content-Signal 建议。"""

def main():
    a = sys.argv[1:]
    if any(x in ("-h", "--help") for x in a):
        print(USAGE)
        return
    if not a or a[0].startswith("-"):
        sys.stderr.write(USAGE + "\n")
        sys.exit(2)
    url = a[0].rstrip("/") + "/robots.txt" if not a[0].rstrip("/").endswith("robots.txt") else a[0]
    mode = "visibility"
    if "--signal" in sys.argv:
        mode = sys.argv[sys.argv.index("--signal")+1]
    txt = fetch(url)
    if "# BEGIN Cloudflare Managed content" in txt:
        print("⚠ Cloudflare 边缘注入块存在(站长源文件看不到)——去 Security→Bot traffic 关闭 block training")
    groups, order = parse_groups(txt)
    star = groups.get("*", {"allow": [], "disallow": []})
    def blocked(bot):
        g = groups.get(bot) or groups.get(bot.lower()) or star
        if any(matches(d) for d in g["disallow"]): return True
        if any(matches(a) for a in g["allow"]): return False
        return any(matches(d) for d in star["disallow"])
    print(f"{'bot':<22}{'类别':<8}状态")
    for b in TIER1: print(f"{b:<22}{'检索':<8}{'❌ 禁(逐出AI答案)' if blocked(b) else '✅'}")
    for b in TIER2: print(f"{b:<22}{'建议':<8}{'❌ 禁' if blocked(b) else '✅'}")
    for b in TRAIN: print(f"{b:<22}{'训练':<8}{'禁(不影响搜索)' if blocked(b) else '放行'}")
    print("\n过时 token 检查:", [t for t in ("anthropic-ai", "Claude-Web", "ChatGPT-Plugins") if t in txt] or "无")
    print("Sitemap 行:", "有" if "sitemap:" in txt.lower() else "❌ 缺")
    print(f"\n建议 Content-Signal(业务决策,Googlebot 不遵守、非排名因素):\n  Content-Signal: {SIGNALS.get(mode, SIGNALS['visibility'])}")

if __name__ == "__main__": main()
