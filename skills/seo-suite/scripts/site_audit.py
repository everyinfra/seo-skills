#!/usr/bin/env python3
"""单页/多页 SEO 审计器(stdlib only)。整合百仓深扫的阈值:
title/desc 限值按 markets.json 市场单位(chars/fullwidth/grapheme)/ H1 唯一 /
词数 CJK·天城文·泰文字素感知 / 链接>100 / alt 覆盖 / canonical·robots·og·lang·JSON-LD /
llms.txt·sitemap / AI 爬虫放行 / staging 子域。
S2 实测修复(2026-10-09):title 收集只在 <title>…</title> 内(script/JSON-LD 不再吞入);
泰文字素计长、天城文按字符计词、拉丁扩展(越南/波兰/土耳其等)词不被 ASCII 正则切碎;
--market 接线 markets.json 阈值(18 市场)。
S3 扩展(2026-10-10,borrow-specs A3/A4):AI Search Health 独立子分(Semrush 8 bot 名单/
llms.txt/Last-Modified>183 天/语义 HTML 比值/词数>15000/BLUF 密度,--json 新增 ai_search_health 节)+
rendering 5 检查(geo-aeo-tracker 源码口径:CSR/noscript/JS 重量/服务端内容/H1-H2)。
用法: python3 site_audit.py URL [URL...] [--market ja|en|zh|th|hi|vi|pl|tr|...]
判定: CRITICAL 存在则退出码 1。"""
import sys, os, re, json, math, unicodedata, urllib.error, urllib.request
from datetime import datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (compatible; seo-suite-audit/1.1)"
# Semrush 官方 8 bot 检查名单(AI Search Health 口径,查这 8 个而非 27 个全量):
# 4 个搜索引用 + Googlebot + Google-Extended + Perplexity-User + Claude-User。
# Google-Extended 是 robots token 不是爬虫 → 单列(WARN 级);GPTBot/ClaudeBot 训练型
# 不影响搜索可见性 → 不进失败项,被禁只出 notice(INFO)。
SEARCH_BOTS = ["ChatGPT-User", "OAI-SearchBot", "Googlebot", "Google-Extended",
               "Perplexity-User", "PerplexityBot", "Claude-User", "Claude-SearchBot"]
TRAINING_BOTS = ["GPTBot", "ClaudeBot"]          # 训练型:只提示不计失败(borrow-specs A3)
RETRIEVAL_BOTS = SEARCH_BOTS                     # 向后兼容别名(旧 4 bot ⊂ 新 8 bot)
# 语义 HTML 标签集(Semrush 语义比值口径):header/nav/main/article/section/aside/footer/
# h1-h6/figure/time/mark/details
SEMANTIC_TAGS = frozenset(("header", "nav", "main", "article", "section", "aside", "footer",
                           "figure", "time", "mark", "details")) | {f"h{i}" for i in range(1, 7)}
SEMANTIC_MIN_RATIO = 0.10       # 比值<10% 触发——阈值自定[推断],官方未公开
CONTENT_MAX_WORDS = 15000       # 词数>15000 触发内容过长——阈值自定[推断],官方未公开
FRESHNESS_MAX_DAYS = 183        # Last-Modified>183 天(6 个月)→notice【Semrush 官方】
# AI Search Health 子分权重(bots 0.4/llms 0.15/freshness 0.15/semantic 0.15/content 0.15)
# ——通过率加权,权重自定[推断];bluf 进 checks 仅记录不参与计分
AI_HEALTH_WEIGHTS = {"bots": 0.40, "llms_txt": 0.15, "freshness": 0.15,
                     "semantic_html": 0.15, "content_length": 0.15}
# CSR 空挂载点(geo-aeo-tracker 源码口径):#root/#app/#__next/#svelte
MOUNT_IDS = ("root", "app", "__next", "svelte")
# BLUF 直答短语正则(geo-aeo-tracker 源码公式,原样照抄)
BLUF_RE = re.compile(r"in short|tl;dr|summary|key takeaways|bottom line|the answer is|here's (what|how|why)", re.I)
STAGING = ("test.", "staging.", "dev.", "preview.", "beta.", "uat.")
# fetch 质量守卫:被挑战页/WAF 拦截时拒绝审计(输出 [SKIP],不算 CRITICAL)
MIN_BODY_BYTES = 200
CHALLENGE_MARKERS = ("just a moment", "attention required", "cf-chl", "cf-browser-verification",
                     "challenge-platform", "checking your browser", "verify you are human",
                     "unusual traffic", "access denied", "captcha", "ddos-guard", "perimeterx", "px-captcha")

USAGE = """usage: site_audit.py URL [URL...] [--market XX] [--json]
单页全项审计:title/desc 限值(市场单位)/H1/词数/链接/alt/canonical/robots/og/JSON-LD/
llms.txt/sitemap/AI 爬虫放行/staging 子域。
  --market XX  markets.json 18 市场阈值(chars/fullwidth/grapheme)
  --json       结构化输出(findings+meta+verdict+ai_search_health,供 agent 消费)
AI Search Health 子分(Semrush 8 bot 名单口径,与主审计并列输出):
  8 bot 放行(ChatGPT-User/OAI-SearchBot/Googlebot/Google-Extended/Perplexity-User/
  PerplexityBot/Claude-User/Claude-SearchBot;GPTBot/ClaudeBot 训练型只提示;
  Google-Extended 是 robots token 非 爬虫单列)/llms.txt 存在/Last-Modified>183 天/
  语义 HTML 比值<10%/词数>15000/BLUF 密度 → --json 每页 ai_search_health 节
  (score 0-100 通过率加权:bot 0.4/llms·freshness·semantic·content 各 0.15[推断])。
rendering 5 检查(geo-aeo-tracker 源码口径,WARN/INFO 级不产生 CRITICAL):
  CSR 空挂载点(#root/#app/#__next/#svelte + 纯文本<200 字或 text/HTML<0.02;
  __NEXT_DATA__/data-reactroot 赦免)/noscript 回退>20 字/JS 重量(外部>15 或内联>100KB)/
  服务端内容(纯文本>500 字且含 article/main/section)/H1==1 且 H2>=2。
判定:CRITICAL 存在则退出码 1;fetch 守卫触发输出 [SKIP] fetch guard: response too small /
likely challenge page 并拒绝审计结论(该 URL 不计失败,退出码不受影响)。"""

def looks_like_challenge(html):
    head = html[:4000].lower()
    return any(m in head for m in CHALLENGE_MARKERS)

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
        # S3:AI Search Health + rendering 5 检查所需信号
        self.semantic_tags, self.all_tags, self.sem_counts = 0, 0, {}
        self.li_count = 0
        self.ext_scripts, self.inline_js_bytes = 0, 0
        self.script_inline = False
        self.mounts, self.ssr_amnesty = set(), False   # CSR 挂载点 / SSR 赦免(__NEXT_DATA__·data-reactroot)
        self.in_noscript, self.noscript_text = False, []
        self.meta_last_modified = None                 # <meta http-equiv="Last-Modified" content=...>(头缺失时回退)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.all_tags += 1
        if tag in SEMANTIC_TAGS:
            self.semantic_tags += 1
            self.sem_counts[tag] = self.sem_counts.get(tag, 0) + 1
        tid = a.get("id")
        if tid in MOUNT_IDS: self.mounts.add(tid)
        if tid == "__NEXT_DATA__" or "data-reactroot" in a: self.ssr_amnesty = True
        if tag == "li": self.li_count += 1
        if tag == "noscript": self.in_noscript = True
        if tag == "html": self.lang = a.get("lang")
        if tag == "head": self.in_head = True
        if tag == "title" and self.in_head:
            self.title.append("")
            self.in_title = True
        if tag == "script":
            self.in_script = True
            self.script_ld = "ld+json" in (a.get("type") or "")
            self.script_inline = not self.script_ld and not a.get("src")
            if a.get("src"): self.ext_scripts += 1
            if self.script_ld: self.ld_buf = []
        if tag == "meta":
            k = a.get("name") or a.get("property") or ""
            v = a.get("content") or ""
            self.meta_props[k.lower()] = v
            if k.lower() == "description": self.desc = v
            if k.lower() == "robots": self.meta_robots = v
            if k.lower().startswith("og:"): self.og[k.lower()] = v
            if (a.get("http-equiv") or "").lower() == "last-modified":
                self.meta_last_modified = a.get("content")
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
            self.script_inline = False
            self.in_script = False
        if tag == "noscript": self.in_noscript = False
        if tag == "head": self.in_head = self.in_title = False
    def handle_data(self, d):
        # S2 修复:title 只收集 <title>…</title> 内的文本——head 内 script/JSON-LD/
        # style 的数据一律不吞(此前 title 开过后 head 内全部裸文本都被拼进 title,
        # 6+ 站触发 2-75 万字符假 title)。
        if self.in_script:
            if self.script_ld: self.ld_buf.append(d)
            elif self.script_inline: self.inline_js_bytes += len(d)
            return
        if self.in_noscript: self.noscript_text.append(d)
        if self.in_title and self.title:
            self.title[-1] = (self.title[-1] or "") + d

def get_header(hdrs, name):
    """大小写不敏感取响应头(dict(r.headers) 键大小写随服务器)。"""
    for k, v in (hdrs or {}).items():
        if k.lower() == name.lower():
            return v
    return None

def parse_robots_groups(txt):
    """自写 robots.txt 解析(RFC 9309 简化):BOM 剥离/注释剥离/连续 User-agent 行合并同组/
    规则后出现的 User-agent 开新组/Sitemap·Crawl-delay 等忽略。
    返回 {ua小写: [(前缀长, 是否Allow, 前缀小写), ...]};不支持 * $ 通配(按字面前缀处理)。"""
    groups, uas, seen_rule = {}, [], False
    for raw in txt.lstrip("\ufeff").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            if seen_rule:
                uas, seen_rule = [], False
            if v:
                uas.append(v.lower())
                groups.setdefault(v.lower(), [])
        elif k in ("allow", "disallow") and uas:
            seen_rule = True
            for ua in uas:
                groups[ua].append((len(v), k == "allow", v.lower()))
    return groups

def robots_allows(groups, ua, url):
    """最长匹配判定:bot 专属组优先于 *;组内取匹配路径的最长前缀规则(同长 Allow 胜);
    无匹配规则/无组 → 默认放行(urllib.robotparser 首条命中即返回,这里改为 RFC 9309 最长匹配)。"""
    if not groups:
        return True
    rules = groups.get(ua.lower()) or groups.get("*", [])
    pu = urlparse(url)
    path = (pu.path or "/") + (("?" + pu.query) if pu.query else "")
    best_len, allowed = -1, True
    for rlen, is_allow, prefix in rules:
        if prefix and path.lower().startswith(prefix):
            if rlen > best_len or (rlen == best_len and is_allow):
                best_len, allowed = rlen, is_allow
    return allowed

def last_modified_days(hdrs, meta_lm):
    """Last-Modified 距今天数:响应头优先,缺失回退 meta http-equiv;都没有/解析失败 → None(跳过)。"""
    v = get_header(hdrs, "last-modified") or meta_lm
    if not v:
        return None
    try:
        dt = parsedate_to_datetime(v)          # RFC 2822:"Wed, 21 Oct 2015 07:28:00 GMT"
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(v.strip())
        except (TypeError, ValueError):
            return None
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return max(0, (datetime.now() - dt).days)

def semantic_ratio(sem_count, all_count):
    """语义 HTML 比值 = 语义标签数 ÷ 非语义标签数(Semrush 口径;<10% 触发,阈值自定[推断]官方未公开)。
    非语义=0 时:有语义标签→1.0(全语义),否则 0.0。"""
    non = all_count - sem_count
    if non > 0:
        return sem_count / non
    return 1.0 if sem_count > 0 else 0.0

def bluf_score(plain, li_count):
    """BLUF 密度(geo-aeo-tracker 源码公式):first_chunk=前 max(20%×文本长, 400) 字符;
    score=min(1,(直答短语命中 + li数>3 + 首块>100字)/2);pass≥0.5。返回 (score, detail)。"""
    if not plain:
        return 0.0, "无纯文本"
    chunk = plain[:max(int(len(plain) * 0.2), 400)]
    phrase = bool(BLUF_RE.search(chunk))
    lis = li_count > 3
    first_long = len(chunk) > 100
    score = min(1.0, (phrase + lis + first_long) / 2)
    detail = (f"首块 {len(chunk)} 字({'>' if first_long else '≤'}100),"
              f"直答短语{'命中' if phrase else '未见'},li {li_count} 个({'>' if lis else '≤'}3)")
    return score, detail

def detect_csr(page, plain, html_len):
    """CSR 检测(geo-aeo-tracker 源码口径):存在空挂载点 #root/#app/#__next/#svelte 且
    (纯文本<200 字 或 text/HTML 比<0.02);有 __NEXT_DATA__/data-reactroot → SSR 赦免返回 None。"""
    if page.ssr_amnesty or not page.mounts:
        return None
    ratio = (len(plain) / html_len) if html_len else 0.0
    if len(plain) < 200 or ratio < 0.02:
        return {"mounts": sorted(page.mounts), "text_chars": len(plain), "ratio": round(ratio, 4)}
    return None

def ai_health_score(checks):
    """AI Search Health 子分(0-100):通过率加权 Σ(权重×pass);
    bluf 进 checks 仅记录不参与计分(权重表无该项)[推断]。"""
    by_id = {c["id"]: c["pass"] for c in checks}
    return round(100 * sum(w for k, w in AI_HEALTH_WEIGHTS.items() if by_id.get(k)))

def audit(url, market="en"):
    F = []  # (severity, area, msg)
    mk = load_market(market)
    tl, dl = mk["title_limit"], mk["desc_limit"]
    host = urlparse(url).netloc.lower()
    if host.startswith(STAGING): F.append(("CRITICAL", "staging", "staging 子域公开可访问"))
    try:
        st, hdrs, html = fetch(url)
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429, 503):
            return [("SKIP", "fetch guard",
                     f"response too small / likely challenge page (HTTP {e.code}); refusing to audit")], {}, None
        return [("CRITICAL", "fetch", f"{e}")], {}, None
    except Exception as e:
        return [("CRITICAL", "fetch", f"{e}")], {}, None
    # fetch 质量守卫:<200 bytes 或挑战页特征 → 拒绝审计结论([SKIP],不报 CRITICAL)
    if len(html.strip()) < MIN_BODY_BYTES:
        return [("SKIP", "fetch guard",
                 f"response too small / likely challenge page ({len(html)} bytes, HTTP {st}); refusing to audit")], {}, None
    if looks_like_challenge(html):
        return [("SKIP", "fetch guard",
                 f"response too small / likely challenge page (challenge markers, HTTP {st}); refusing to audit")], {}, None
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
    # ---- rendering 5 检查(geo-aeo-tracker 源码口径;全部 WARN/INFO 级,不产生 CRITICAL) ----
    plain = re.sub(r"\s+", " ", text).strip()   # 规范化纯文本(字符类指标用)
    h2n = sum(1 for h in p.headings if h == 2)
    csr = detect_csr(p, plain, len(html))
    if csr:
        F.append(("WARN", "rendering",
                  f"CSR 疑似:空挂载点 {csr['mounts']} 且纯文本 {csr['text_chars']} 字/"
                  f"text-HTML 比 {csr['ratio']}(阈值:文本<200 字或比值<0.02)——AI 爬虫多不执行 JS"))
    nos = re.sub(r"\s+", " ", "".join(p.noscript_text)).strip()
    if len(nos) <= 20:
        F.append(("INFO", "rendering", "无 noscript 回退(或去标签文本≤20 字)——无 JS 客户端拿到空页"))
    if p.ext_scripts > 15 or p.inline_js_bytes > 100 * 1024:
        F.append(("WARN", "rendering",
                  f"JS 重量:外部 script {p.ext_scripts} 个(>15)/内联 JS {p.inline_js_bytes // 1024}KB(>100KB)"
                  "——易超 AI 爬虫抓取预算"))
    if not (len(plain) > 500 and any(p.sem_counts.get(t) for t in ("article", "main", "section"))):
        F.append(("INFO", "rendering",
                  f"服务端内容弱:纯文本 {len(plain)} 字(需>500)或无 article/main/section"))
    if h2n < 2:  # 检查项为 H1==1 且 H2>=2;H1 问题上方既有检查已按自身级别报告,此处只补 H2 缺口
        F.append(("INFO", "headings", f"H2 仅 {h2n} 个(<2)——AI 分块依赖标题层级(H1==1 且 H2>=2)"))
    # ---- BLUF 密度(geo-aeo-tracker 源码公式;失败出 INFO,并进 ai_search_health.checks) ----
    b_score, b_detail = bluf_score(plain, p.li_count)
    if b_score < 0.5:
        F.append(("INFO", "bluf", "BLUF 密度不足,答案前置可提升 AI 引用"))
    # ---- 根文件:robots.txt(8 bot 名单判定)/sitemap/llms.txt ----
    root = f"{urlparse(url).scheme}://{host}"
    robots_groups, llms_ok = {}, False
    for path, name in (("/robots.txt", "robots"), ("/sitemap.xml", "sitemap"), ("/llms.txt", "llms.txt")):
        try:
            s2, _, body2 = fetch(root + path)
            if s2 == 200 and name == "robots":
                robots_groups = parse_robots_groups(body2)
            if s2 == 200 and name == "llms.txt":
                llms_ok = True
        except Exception:
            F.append(("INFO", name, f"/{path} 不可达"))
    allowed, blocked = [], []
    for b in SEARCH_BOTS:
        (allowed if robots_allows(robots_groups, b, url) else blocked).append(b)
    for b in blocked:
        if b == "Google-Extended":
            F.append(("WARN", "ai-bots",
                      "Google-Extended 被禁——robots token 非爬虫(单列),影响 Gemini 训练/落地引用"))
        else:
            F.append(("CRITICAL", "ai-bots", f"{b} 被禁——逐出该 AI 答案"))
    for b in TRAINING_BOTS:  # 训练型:不影响搜索可见性,只 notice 不计失败
        if robots_groups and not robots_allows(robots_groups, b, url):
            F.append(("INFO", "ai-bots", f"{b} 被禁(训练型,不影响搜索可见性,仅提示)"))
    # ---- AI Search Health 独立子分(Semrush 8 bot 名单口径) ----
    lm_days = last_modified_days(hdrs, p.meta_last_modified)
    ratio = semantic_ratio(p.semantic_tags, p.all_tags)
    checks = [
        {"id": "bots", "pass": not blocked,
         "detail": f"被禁: {', '.join(blocked)}" if blocked else
                   (f"8 bot 全放行(Semrush 名单)" if robots_groups else "robots.txt 不可达,默认放行")},
        {"id": "llms_txt", "pass": llms_ok,
         "detail": "llms.txt 存在" if llms_ok else "/llms.txt 缺失/404(notice)"},
        {"id": "freshness", "pass": lm_days is None or lm_days <= FRESHNESS_MAX_DAYS,
         "detail": "无 Last-Modified(头/meta),跳过" if lm_days is None else
                   f"Last-Modified {lm_days} 天前(>183 天=6 个月触发,Semrush 官方)"},
        {"id": "semantic_html", "pass": ratio >= SEMANTIC_MIN_RATIO,
         "detail": f"语义标签比值 {ratio:.1%}(<10% 触发;阈值自定[推断],官方未公开)"},
        {"id": "content_length", "pass": W <= CONTENT_MAX_WORDS,
         "detail": f"词数 {W}(>15000 触发内容过长;阈值自定[推断])"},
        {"id": "bluf", "pass": b_score >= 0.5, "detail": f"score {b_score:.2f}(pass≥0.5);{b_detail}"},
    ]
    ai_health = {"score": ai_health_score(checks),
                 "bots": {"allowed": allowed, "blocked": blocked},
                 "last_modified_days": lm_days,
                 "semantic_ratio": round(ratio, 4),
                 "checks": checks}
    if lm_days is not None and lm_days > FRESHNESS_MAX_DAYS:
        F.append(("INFO", "freshness", f"Last-Modified {lm_days} 天前 >183(6 个月,Semrush 官方)"))
    if p.all_tags and ratio < SEMANTIC_MIN_RATIO:
        F.append(("INFO", "semantic-html", f"语义 HTML 比值 {ratio:.1%} <10%(阈值自定,官方未公开)"))
    if W > CONTENT_MAX_WORDS:
        F.append(("WARN", "content", f"词数 {W} >15000 内容过长(AI 上下文过载,阈值自定[推断])"))
    return F, {"title": t, "title_len": f"{tn} {tl['unit']}/{tl['value']}",
               "desc_len": f"{dn} {dl['unit']}/{dl['value']}",
               "words": W, "h1": p.h1, "jsonld": p.jsonld, "links": p.links}, ai_health

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read(2_000_000).decode("utf-8", "replace")

def main():
    args = sys.argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(USAGE)
        return
    market, as_json = "en", False
    if "--market" in args: i = args.index("--market"); market = args[i+1]; del args[i:i+2]
    if "--json" in args: as_json = True; args = [a for a in args if a != "--json"]
    load_market(market)  # 提前校验,未知市场列出可用值
    urls = [a for a in args if not a.startswith("-")]
    if not urls:
        sys.stderr.write(USAGE + "\n")
        sys.exit(2)
    crit = 0
    results = {}
    for url in urls:
        F, meta, ai_h = audit(url, market)
        print(f"\n== {url} ==")
        for sev, area, msg in F:
            print(f"[{sev}] {area}: {msg}")
            crit += sev == "CRITICAL"
        if meta: print("meta:", json.dumps(meta, ensure_ascii=False))
        if ai_h:  # AI Search Health 子分:与主审计结果并列展示
            parts = ", ".join(f"{c['id']}:{'✓' if c['pass'] else '✗'}" for c in ai_h["checks"])
            print(f"ai_search_health: {ai_h['score']}/100 [{parts}]")
        if as_json:
            results[url] = {
                "verdict": "refused" if any(s == "SKIP" for s, _, _ in F)
                           else ("fail" if any(s == "CRITICAL" for s, _, _ in F) else "pass"),
                "findings": [{"severity": s, "area": a, "message": m} for s, a, m in F],
                "meta": meta,
                "ai_search_health": ai_h}
    if as_json:
        print(json.dumps({"audited": len(urls), "critical": crit, "results": results},
                         ensure_ascii=False, indent=1))
    sys.exit(1 if crit else 0)

if __name__ == "__main__": main()
