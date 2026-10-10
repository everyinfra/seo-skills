#!/usr/bin/env python3
"""llms.txt 生成/校验器(stdlib)。适配 v2 规范:H1+摘要+H2 节+[name](url): desc。
用法:
  python3 llmstxt.py validate FILE        # 校验结构
  python3 llmstxt.py check https://site   # 探测 /llms.txt /llms-full.txt .md 孪生
  python3 llmstxt.py generate --sitemap URL [--title T] [--desc D]   # 从 sitemap 生成骨架"""
import sys, re, urllib.request

UA = "Mozilla/5.0 (compatible; seo-suite-audit/1.0)"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status, r.read(3_000_000).decode("utf-8", "replace")

def validate(path):
    t = open(path, encoding="utf-8").read()
    issues = []
    if not re.match(r"^# ", t): issues.append("缺 H1(唯一必需元素)")
    if len(re.findall(r"^# ", t, re.M)) > 1: issues.append("多个 H1")
    if not re.search(r"^>", t, re.M): issues.append("缺 blockquote 摘要")
    links = re.findall(r"^- \[([^\]]+)\]\(([^)]+)\)(.*)$", t, re.M)
    if len(links) < 3: issues.append(f"链接仅 {len(links)} 条(<3,指南建议 10-30)")
    bad = [l for _, u, l in [(0, ln[1], ln[2]) for ln in links] if not u.startswith(("http", "/", "#"))]
    if bad: issues.append(f"非绝对 URL: {bad[:3]}")
    if re.search(r"[\u200b\ufeff]", t): issues.append("含 Unicode 水印字符")
    sections = re.findall(r"^## (.+)$", t, re.M)
    print(f"H1 ✓  链接 {len(links)}  节 {sections}")
    for i in issues: print("[问题]", i)
    sys.exit(1 if issues else 0)

def check(root):
    root = root.rstrip("/")
    for p in ("/llms.txt", "/llms-full.txt", "/index.md", "/index.html.md"):
        try:
            s, body = fetch(root + p)
            head = body.lstrip()
            if head[:1] == "<" or re.search(r"<(html|head|body|!DOCTYPE)\b", head[:2000], re.I):
                print(f"{p:<18} {s}  [FAIL] llms.txt is HTML not markdown")
            else:
                print(f"{p:<18} {s}  [PASS] {body[:80].replace(chr(10), ' ')}")
        except Exception as e:
            print(f"{p:<18} ✗ {type(e).__name__}")

def generate(sitemap, title, desc):
    s, xml = fetch(sitemap)
    locs = re.findall(r"<loc>([^<]+)</loc>", xml)[:50]
    print(f"# {title}\n\n> {desc}\n")
    print("## Pages\n")
    for u in locs:
        print(f"- [{u.rsplit('/', 1)[-1] or u}]({u})")
    print(f"\n<!-- 从 {sitemap} 生成 {len(locs)} 条;请补每条冒号后的说明再上线 -->")

def main():
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__.strip())
        sys.exit(0)
    if a[0] == "validate" and len(a) > 1: validate(a[1])
    elif a[0] == "check" and len(a) > 1: check(a[1])
    elif a[0] == "generate" and "--sitemap" in a:
        i = a.index("--sitemap"); sm = a[i+1]
        t = a[a.index("--title")+1] if "--title" in a else "Site"
        d = a[a.index("--desc")+1] if "--desc" in a else "Site description"
        generate(sm, t, d)
    else:
        print(__doc__.strip(), file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__": main()
