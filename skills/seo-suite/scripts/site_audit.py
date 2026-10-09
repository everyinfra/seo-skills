#!/usr/bin/env python3
"""单页/多页 SEO 审计器(stdlib only)。整合百仓深扫的阈值:
title/desc 限值按 markets.json 市场单位(chars/fullwidth/grapheme)/ H1 唯一 /
词数 CJK·天城文·泰文字素感知 / 链接>100 / alt 覆盖 / canonical·robots·og·lang·JSON-LD /
llms.txt·sitemap / AI 爬虫放行 / staging 子域。
S2 实测修复(2026-10-09):title 收集只在 <title>…</title> 内(script/JSON-LD 不再吞入);
泰文字素计长、天城文按字符计词、拉丁扩展(越南/波兰/土耳其等)词不被 ASCII 正则切碎;
--market 接线 markets.json 阈值(18 市场)。
用法: python3 site_audit.py URL [URL...] [--market ja|en|zh|th|hi|vi|pl|tr|...]
判定: CRITICAL 存在则退出码 1。"""
import sys, os, re, json, math, unicodedata, urllib.request, urllib.robotparser
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (compatible; seo-suite-audit/1.1)"
RETRIEVAL_BOTS = ["OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "PerplexityBot"]
STAGING = ("test.", "staging.", "dev.", "preview.", "beta.", "uat.")

def load_market(market):
    """markets.json 市场规则(与 market_lint.py 同源);未知市场直接退出。"""
    with open(os.path.join(BASE, "markets.json"), encoding="utf-8") as f:
        ms = json.load(f)["markets"]
    if market not in ms:
        sys.exit("未知市场 %s;可用: %s" % (market, ", ".join(ms)))
    return ms[market]

def unit_len(s, unit):
    """按市场单位计长:chars=len()/fullwidth=EAW W/F 计 1 其余 0.5 向上取整/
    grapheme=combining==0 且非 Mn/Cf(泰文字素近似,组合元音/声调符不独立计数)。"""
    if unit == "fullwidth":
        return math.ceil(sum(1.0 if unicodedata.east_asian_width(c) in ("W", "F") else 0.5 for c in s))
    if unit == "grapheme":
        return sum(1 for c in s if unicodedata.combining(c) == 0
                   and unicodedata.category(c) not in ("Mn", "Cf"))
    return len(s)

def is_cjk(ch):
    o = ord(ch)
    return 0x4E00 <= o <= 0x9FFF or 0x3040 <= o <= 0x30FF or 0xAC00 <= o <= 0xD7AF

def is_thai(ch):
    return 0x0E00 <= ord(ch) <= 0x0E7F

def is_devanagari(ch):
    return 0x0900 <= ord(ch) <= 0x097F

def is_grapheme_base(ch):
    """字素近似基字符(markets.json units.grapheme 口径)——泰文组合标记不计。"""
    return unicodedata.combining(ch) == 0 and unicodedata.category(ch) not in ("Mn", "Cf")

def wc(text):
    """词数(CJK 感知 + S2 修复):
    - CJK 逐字计(原有);
    - 天城文(0x0900-0x097F)逐字计——此前记 0;
    - 泰文按字素近似计(组合元音/声调符不计)——此前记 0;
    - 其余表音文字(拉丁/西里尔/希腊/希伯来/阿拉伯等一切 Unicode 字母)按"词字符
      连续段"计——此前 ASCII 正则 [A-Za-z0-9'] 把越南(0x1EA0-1EF9)/波兰
      (0x0100-1D7F)/土耳其(İ ı ş ğ)变音词切碎,阿文/俄文整段记 0;
    - 土耳其 İ:先 replace('İ','i') 再清洗 U+0307 组合点(casefold 前替换口径,
      避免分解形 I+U+0307 把一个词劈成两个)。"""
    text = text.replace("İ", "i").replace("I\u0307", "i").replace("\u0307", "")
    perchar = words = 0
    prev = False  # 前一字符是否处于词内
    for c in text:
        if is_cjk(c) or is_devanagari(c):
            perchar += 1
            prev = False
        elif is_thai(c):
            if is_grapheme_base(c):
                perchar += 1
            prev = False
        else:
            is_l = unicodedata.category(c)[0] == "L" or c.isdigit()
            if is_l and not prev:
                words += 1
            prev = is_l or ((c == "'" or unicodedata.category(c) == "Mn") and prev)
    return perchar + words

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self.desc, self.canonical, self.lang = [], None, None, None
        self.h1, self.headings, self.meta_robots = 0, [], None
        self.og, self.links, self.imgs, self.img_noalt = {}, 0, 0, 0
        self.jsonld, self.ld_buf = 0, []
        self.in_head, self.meta_props = True, {}
        self.in_title = self.in_script = self.script_ld = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html": self.lang = a.get("lang")
        if tag == "head": self.in_head = True
        if tag == "title" and self.in_head:
            self.title.append("")
            self.in_title = True
        if tag == "script":
            self.in_script = True
            self.script_ld = "ld+json" in (a.get("type") or "")
            if self.script_ld: self.ld_buf = []
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
        if tag == "body": self.in_head = self.in_title = False
    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False
        if tag == "script":
            if self.script_ld:
                self.jsonld += 1
                self.script_ld = False
            self.in_script = False
        if tag == "head": self.in_head = self.in_title = False
    def handle_data(self, d):
        # S2 修复:title 只收集 <title>…</title> 内的文本——head 内 script/JSON-LD/
        # style 的数据一律不吞(此前 title 开过后 head 内全部裸文本都被拼进 title,
        # 6+ 站触发 2-75 万字符假 title)。
        if self.in_script:
            if self.script_ld: self.ld_buf.append(d)
            return
        if self.in_title and self.title:
            self.title[-1] = (self.title[-1] or "") + d

def audit(url, market="en"):
    F = []  # (severity, area, msg)
    mk = load_market(market)
    tl, dl = mk["title_limit"], mk["desc_limit"]
    host = urlparse(url).netloc.lower()
    if host.startswith(STAGING): F.append(("CRITICAL", "staging", "staging 子域公开可访问"))
    try:
        st, hdrs, html = fetch(url)
    except Exception as e:
        return [("CRITICAL", "fetch", f"{e}")], {}
    p = Page(); p.feed(html)
    t = re.sub(r"\s+", " ", (p.title[0] if p.title else "")).strip()
    tn = unit_len(t, tl["unit"])
    if not t: F.append(("CRITICAL", "title", "缺失"))
    elif tn < 20: F.append(("WARN", "title", f"{tn} {tl['unit']} <20"))
    elif tn > tl["value"]:
        F.append(("WARN", "title", f"{tn} {tl['unit']} 超上限 {tl['value']}({tl.get('note', '')})"))
    dn = unit_len(p.desc or "", dl["unit"])
    if p.desc is None: F.append(("CRITICAL", "description", "缺失"))
    elif dn < 80: F.append(("WARN", "description", f"{dn} {dl['unit']} <80"))
    elif dn > dl["value"]:
        F.append(("WARN", "description", f"{dn} {dl['unit']} 超上限 {dl['value']}"))
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
    body = re.sub(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", body)
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
    return F, {"title": t, "title_len": f"{tn} {tl['unit']}/{tl['value']}",
               "desc_len": f"{dn} {dl['unit']}/{dl['value']}",
               "words": W, "h1": p.h1, "jsonld": p.jsonld, "links": p.links}

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read(2_000_000).decode("utf-8", "replace")

def main():
    args = sys.argv[1:]
    market = "en"
    if "--market" in args: i = args.index("--market"); market = args[i+1]; del args[i:i+2]
    load_market(market)  # 提前校验,未知市场列出可用值
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
