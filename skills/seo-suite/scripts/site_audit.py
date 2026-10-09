#!/usr/bin/env python3
"""单页/多页 SEO 审计器(stdlib only)。整合百仓深扫的阈值:
title 20-60 / desc 80-160 / H1 唯一 / 词数 CJK 感知 / 链接>100 / alt 覆盖 /
canonical·robots·og·lang·JSON-LD / llms.txt·sitemap / AI 爬虫放行 / staging 子域。
用法: python3 site_audit.py URL [URL...] [--market ja|en|zh]
判定: CRITICAL 存在则退出码 1。"""
import sys, re, json, urllib.request, urllib.robotparser
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

UA = "Mozilla/5.0 (compatible; seo-suite-audit/1.0)"
RETRIEVAL_BOTS = ["OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "PerplexityBot"]
STAGING = ("test.", "staging.", "dev.", "preview.", "beta.", "uat.")

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read(2_000_000).decode("utf-8", "replace")

def is_cjk(ch):
    o = ord(ch)
    return 0x4E00 <= o <= 0x9FFF or 0x3040 <= o <= 0x30FF or 0xAC00 <= o <= 0xD7AF

def wc(text):
    cjk = sum(1 for c in text if is_cjk(c))
    latin = len(re.findall(r"[A-Za-z0-9']+", text))
    return cjk + latin

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self.desc, self.canonical, self.lang = [], None, None, None
        self.h1, self.headings, self.meta_robots = 0, [], None
        self.og, self.links, self.imgs, self.img_noalt = {}, 0, 0, 0
        self.jsonld, self.in_ld, self.ld_buf = 0, False, []
        self.in_head, self.meta_props = True, {}
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html": self.lang = a.get("lang")
        if tag == "title" and self.in_head: self.title.append("")
        if tag == "meta":
            k = a.get("name") or a.get("property") or ""
            v = a.get("content") or ""
            self.meta_props[k.lower()] = v
            if k.lower() == "description": self.desc = v
            if k.lower() == "robots": self.meta_robots = v
            if k.lower().startswith("og:"): self.og[k.lower()] = v
        if tag == "link" and a.get("rel") == "canonical": self.canonical = a.get("href")
        if tag in ("h1",): self.h1 += 1
        if re.fullmatch(r"h[1-6]", tag): self.headings.append(int(tag[1]))
        if tag == "a" and a.get("href", "").startswith(("http", "/", "#")): self.links += 1
        if tag == "img":
            self.imgs += 1
            if not a.get("alt"): self.img_noalt += 1
        if tag == "script" and "ld+json" in (a.get("type") or ""):
            self.in_ld, self.ld_buf = True, []
        if tag == "body": self.in_head = False
    def handle_endtag(self, tag):
        if tag == "script" and self.in_ld:
            self.jsonld += 1; self.in_ld = False
        if tag == "title": pass
    def handle_data(self, d):
        if self.in_ld: self.ld_buf.append(d)
        if self.title and not d.isspace() and self.in_head: self.title[-1] = (self.title[-1] or "") + d

def audit(url, market="en"):
    F = []  # (severity, area, msg)
    host = urlparse(url).netloc.lower()
    if host.startswith(STAGING): F.append(("CRITICAL", "staging", "staging 子域公开可访问"))
    try:
        st, hdrs, html = fetch(url)
    except Exception as e:
        return [("CRITICAL", "fetch", f"{e}")], {}
    p = Page(); p.feed(html)
    t = (p.title[0] if p.title else "").strip()
    if not t: F.append(("CRITICAL", "title", "缺失"))
    elif len(t) < 20: F.append(("WARN", "title", f"{len(t)} 字符 <20"))
    elif len(t) > (32 if market == "ja" else 60): F.append(("WARN", "title", f"{len(t)} 超上限"))
    if p.desc is None: F.append(("CRITICAL", "description", "缺失"))
    elif len(p.desc) < 80: F.append(("WARN", "description", f"{len(p.desc)} <80"))
    elif len(p.desc) > (120 if market == "ja" else 160): F.append(("WARN", "description", f"{len(p.desc)} 超上限"))
    if p.h1 == 0: F.append(("CRITICAL", "h1", "无 H1"))
    elif p.h1 > 1: F.append(("WARN", "h1", f"{p.h1} 个 H1"))
    for i, h in enumerate(p.headings[1:], 1):
        if p.headings[i-1] and h - p.headings[i-1] > 1:
            F.append(("WARN", "headings", f"跳级 h{p.headings[i-1]}→h{h}")); break
    if p.canonical:
        if not p.canonical.startswith(("http", "/")): F.append(("CRITICAL", "canonical", "相对 URL"))
        c = urljoin(url, p.canonical)
        if urlparse(c).netloc and urlparse(c).netloc != host: F.append(("INFO", "canonical", "指向外域(联合发布?让渡权重)"))
    else: F.append(("WARN", "canonical", "缺失"))
    mr = (p.meta_robots or "").lower() + "," + (hdrs.get("X-Robots-Tag", "") or "").lower()
    if "noindex" in mr: F.append(("CRITICAL", "robots", "noindex"))
    if "nosnippet" in mr: F.append(("WARN", "robots", "nosnippet(会限制 AI 特性)"))
    for k in ("og:title", "og:description", "og:image"):
        if k not in p.og: F.append(("WARN", "og", f"{k} 缺失"))
    if p.og.get("og:image") and not p.og["og:image"].startswith("http"): F.append(("WARN", "og", "og:image 非绝对 URL"))
    if not p.lang: F.append(("WARN", "a11y", "html 无 lang"))
    text = re.sub(r"<[^>]+>", " ", html)
    W = wc(text)
    if W < 200: F.append(("WARN", "content", f"词数 {W} <200(soft-thin)"))
    if p.links > 100: F.append(("WARN", "links", f"{p.links} 链接 >100"))
    if p.imgs and p.img_noalt / p.imgs > 0.2: F.append(("WARN", "images", f"alt 缺失 {p.img_noalt}/{p.imgs}"))
    if p.jsonld == 0: F.append(("WARN", "schema", "无 JSON-LD"))
    root = f"{urlparse(url).scheme}://{host}"
    for path, name in (("/robots.txt", "robots"), ("/sitemap.xml", "sitemap"), ("/llms.txt", "llms.txt")):
        try:
            s2, _, _ = fetch(root + path)
            if s2 == 200 and name == "robots":
                rp = urllib.robotparser.RobotFileParser(); rp.parse(html_lines := fetch(root + "/robots.txt")[2].splitlines())
                for b in RETRIEVAL_BOTS:
                    if not rp.can_fetch(b, url): F.append(("CRITICAL", "ai-bots", f"{b} 被禁——逐出该 AI 答案"))
        except Exception:
            F.append(("INFO", name, f"/{path} 不可达"))
    return F, {"title": t, "words": W, "h1": p.h1, "jsonld": p.jsonld, "links": p.links}

def main():
    args = sys.argv[1:]
    market = "en"
    if "--market" in args: i = args.index("--market"); market = args[i+1]; del args[i:i+2]
    crit = 0
    for url in args:
        F, meta = audit(url, market)
        print(f"\n== {url} ==")
        for sev, area, msg in F:
            print(f"[{sev}] {area}: {msg}")
            crit += sev == "CRITICAL"
        if meta: print("meta:", json.dumps(meta, ensure_ascii=False))
    sys.exit(1 if crit else 0)

if __name__ == "__main__": main()
