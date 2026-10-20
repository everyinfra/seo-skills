#!/usr/bin/env python3
"""llms.txt 生成/校验器(stdlib)。适配 v2 规范:H1+摘要+H2 节+[name](url): desc。
用法:
  python3 llmstxt.py validate FILE        # 校验结构
  python3 llmstxt.py check https://site   # 探测 /llms.txt /llms-full.txt .md 孪生
  python3 llmstxt.py generate --sitemap URL [--title T] [--desc D]   # 从 sitemap 生成骨架
安全:网络仅限 http(s);私网/环回/链路本地/保留段拒连;重定向逐跳复查(SSRF 防护)。"""
import ipaddress, os, re, socket, sys, urllib.parse, urllib.request

UA = "Mozilla/5.0 (compatible; seo-suite-audit/1.0)"


# ---------------------------------------------------------------- SSRF 防护
class FetchError(Exception):
    pass


_ssrf_cache = {}


def ssrf_guard(host):
    """仅 http(s) + 拒私网/环回/链路本地/保留段;结果按 host 缓存(trend_watch.py 同款,
    内嵌不 import)。198.18.0.0/15(RFC2544 基准段)豁免:本机 fake-IP 代理会把一切域名
    解析到该段,实际连接经代理出网,TLS 验证仍生效;SEO_MONITOR_STRICT_SSRF=1 恢复全拒。"""
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
    """重定向逐跳 SSRF 复查(urlopen 自动跟 302,每一跳的新 host 必须复查)。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urllib.parse.urlparse(newurl)
        if p.scheme not in ("http", "https"):
            raise FetchError("重定向到非 http(s) 被拒: %s" % newurl)
        ssrf_guard(p.hostname)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_RedirectGuard)


def require_http_url(url):
    """入口 URL 校验:仅 http(s)(拒 file:///ftp:// 等)。"""
    if urllib.parse.urlparse(url).scheme not in ("http", "https"):
        raise FetchError("仅允许 http(s) URL: %s" % url)


def fetch(url):
    """唯一网络出口(测试打桩点):scheme 检查 + SSRF 防护 + 受控 opener。"""
    require_http_url(url)
    ssrf_guard(urllib.parse.urlparse(url).hostname)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with _opener.open(req, timeout=15) as r:
        return r.status, r.read(3_000_000).decode("utf-8", "replace")

def validate(path):
    t = open(path, encoding="utf-8").read()
    # llmstxt.org v2 Format:文件以「可选 BOM」开头,随后才是 H1。开头 BOM 合法,先剥掉再查,
    # 不判缺 H1、也不算水印字符(修前 BOM 文件同时报「H1 ✓」和「缺 H1」)。
    if t.startswith("\ufeff"):
        t = t[1:]
    issues = []
    has_h1 = bool(re.match(r"^# ", t))
    if not has_h1: issues.append("缺 H1(唯一必需元素)")
    if len(re.findall(r"^# ", t, re.M)) > 1: issues.append("多个 H1")
    if not re.search(r"^>", t, re.M): issues.append("缺 blockquote 摘要")
    links = re.findall(r"^- \[([^\]]+)\]\(([^)]+)\)(.*)$", t, re.M)
    if len(links) < 3: issues.append(f"链接仅 {len(links)} 条(<3,指南建议 10-30)")
    # 只认 http(s):// 绝对 URL(llms-txt-guide.md「链接用绝对 URL」;规范示例全是绝对 URL)。
    # 修前 startswith(("http","/","#")) 放过 /docs、#anchor,打印的还是描述而不是 URL。
    bad = [u for _, u, _ in links if not re.match(r"^https?://", u.strip(), re.I)]
    if bad: issues.append(f"非绝对 URL: {bad[:3]}")
    if re.search(r"[\u200b\ufeff]", t): issues.append("含 Unicode 水印字符")
    sections = re.findall(r"^## (.+)$", t, re.M)
    print(f"H1 {'✓' if has_h1 else '✗'}  链接 {len(links)}  节 {sections}")
    for i in issues: print("[问题]", i)
    sys.exit(1 if issues else 0)

def check(root):
    try:
        require_http_url(root)
    except FetchError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(2)
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
    try:
        require_http_url(sitemap)
        s, xml = fetch(sitemap)
    except FetchError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)
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
