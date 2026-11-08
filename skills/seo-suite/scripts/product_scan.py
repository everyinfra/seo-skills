#!/usr/bin/env python3
"""product_scan.py — 开局第一步「agent 先自己把产品读透」:读站点和/或产品仓库,产出一份带出处的事实草稿 JSON
(stdlib only)。下游 onboard.py 用它起草产品档案、判断产品阶段,所以输出契约固定(见 build_report / 文件尾注释)。

站点部分(--site):首页页面特征;robots.txt(全封判定、声明的 sitemap);sitemap(robots 声明的 + /sitemap.xml,
递归 sitemapindex,子 sitemap ≤20 个,URL 去重计数,超 --max-urls 截断);/llms.txt、/llms-full.txt;
按 URL 路径归类页面类型(先剥语言前缀,语言前缀单独计数);每个关键类型抽 1 页抓特征;Wayback 最早快照日期。
仓库部分(--repo):框架、渲染方式、路由、内容文件数、语言目录、SEO 文件、埋点、README 摘要、package 元信息。
已有上下文:repo(没给就当前目录)下 .agents/product-marketing*.md、.claude/product-marketing-context.md。

抓取全部走 site_crawl.robust_fetch(逐跳 SSRF 守卫 + 传输层重试);--allow-local 只多放行本机回环。
网络失败不崩:记进 errors,能产出多少产出多少。

facts 的 kind:"fact" = 页面/文件上原文就有;"inferred" = 推出来的(归类、计数、判断)。

退出码: 0 正常(含部分抓取失败)/ 2 参数错(没给 --site 也没给 --repo、repo 目录不存在、站点不是 http(s))。

用法: python3 product_scan.py --site https://example.com [--repo DIR] [--max-pages 20] [--max-urls 50000]
                              [--allow-local] [--no-wayback] [--out FILE] [--md]
"""
import argparse
import gzip
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import site_crawl as sc  # noqa: E402

SCHEMA = 1
DEFAULT_MAX_PAGES = 20
DEFAULT_MAX_URLS = 50_000
SITEMAP_CHILD_MAX = 20           # 递归 sitemapindex 时最多抓多少个子 sitemap
FETCH_TIMEOUT = 15.0
POLITE_DELAY = 0.3               # 两次请求之间的礼貌间隔(秒);走 sc._sleep,测试打桩为零延时
H2_MAX = 12
PRICES_MAX = 10
CTAS_MAX = 10
ROUTES_MAX = 200
README_MAX = 300
SAMPLE_TYPES = ("pricing", "about", "docs", "blog", "product", "compare", "integrations")
SKIP_DIRS = {"node_modules", ".git", ".next", "dist", "build", ".nuxt", ".output", ".svelte-kit",
             ".astro", ".turbo", ".vercel", ".cache", "coverage", "__pycache__", ".venv", "venv", "out"}
SOURCE_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".html", ".htm", ".vue", ".svelte", ".astro",
              ".php", ".liquid", ".njk", ".hbs", ".erb", ".twig")
SOURCE_SCAN_MAX_FILES = 6000
SOURCE_SCAN_MAX_BYTES = 512 * 1024

# ---- 页面类型(URL 路径归类)----
# 先按首段整段命中(精确),再按首段 "-" 分词命中;compare 另认任意段里的 -vs- / alternative(s)。
PAGE_TYPE_RULES = (
    ("pricing", ("pricing", "price", "prices", "plans", "plan", "定价", "precios", "tarifs", "preise")),
    ("compare", ("vs", "compare", "comparison", "comparisons", "alternatives", "alternative", "versus")),
    ("docs", ("docs", "doc", "documentation", "reference", "guide", "guides", "quickstart", "tutorials",
              "tutorial", "manual", "learn")),
    ("blog", ("blog", "blogs", "news", "articles", "article", "posts", "post", "insights", "stories",
              "resources", "博客")),
    ("changelog", ("changelog", "changelogs", "releases", "release-notes", "updates", "whats-new", "what-s-new")),
    ("integrations", ("integrations", "integration", "apps", "plugins", "plugin", "connectors", "marketplace",
                      "extensions")),
    ("customers", ("customers", "customer", "case-studies", "case-study", "testimonials", "success-stories",
                   "showcase")),
    ("about", ("about", "about-us", "company", "team", "contact", "contact-us", "press", "partners", "关于")),
    ("careers", ("careers", "career", "jobs", "join-us", "hiring")),
    ("legal", ("legal", "privacy", "privacy-policy", "terms", "terms-of-service", "terms-of-use", "tos",
               "cookies", "cookie-policy", "imprint", "impressum", "gdpr", "dpa", "refund", "refund-policy",
               "aup", "acceptable-use")),
    ("help", ("help", "support", "faq", "faqs", "kb", "knowledge-base", "help-center", "helpcenter", "status")),
    ("api", ("api", "apis", "developers", "developer", "sdk", "sdks", "openapi")),
    ("product", ("product", "products", "features", "feature", "solutions", "solution", "platform",
                 "platforms", "use-cases", "usecases", "tools", "tool", "services", "capabilities")),
    ("category", ("category", "categories", "collections", "collection", "c", "tag", "tags", "topics", "topic")),
)
PAGE_TYPES = tuple(t for t, _ in PAGE_TYPE_RULES) + ("other",)
TOKEN_RULES = (("compare", ("vs", "alternative", "alternatives", "versus")),
               ("pricing", ("pricing",)),
               ("api", ("api", "sdk")),
               ("docs", ("docs",)),
               ("integrations", ("integration", "integrations")))

# ISO 639-1 常见语言码(语言前缀识别用白名单——避免把 /vs/、/go/、/c/ 当语言)
LANG_CODES = set((
    "en zh es fr de ja ko pt ru it ar nl pl tr vi id th hi sv da fi no nb nn cs sk uk he iw el hu ro bg hr sr sl "
    "lt lv et ms fa bn ta te ur mr gu kn ml pa sw tl fil ca eu gl af sq hy az be bs ka kk km lo mk mn my ne si uz "
    "is ga cy mt lb yi am zu xh").split())
LOCALE_RE = re.compile(r"^([a-z]{2,3})(?:[-_]([a-z]{2}|[a-z]{4}|\d{3}))?$", re.I)

# ---- 页面特征抽取用 ----
PRICE_RES = (
    re.compile(r"(?:US\$|A\$|C\$|HK\$|S\$|R\$|[$€£¥￥₹₩])\s?\d[\d,]*(?:\.\d+)?"
               r"(?:\s?(?:/|per\s)\s?(?:mo|month|yr|year|user|seat|1k|1,000|k|月|年|次))?", re.I),
    re.compile(r"(?<![\d.,\-/:])\d[\d,]*(?:\.\d+)?\s?(?:美元|元|欧元|英镑|USD|EUR|GBP|CNY|RMB|dólares|euros)"
               r"(?:\s?/\s?(?:月|年|mo|month|mes|año))?", re.I),
)
CTA_WORDS = (
    # en
    "sign up", "signup", "sign-up", "register", "log in", "login", "sign in", "signin", "get started", "start free",
    "start now", "start for free", "try", "free trial", "buy", "purchase", "subscribe", "contact sales",
    "talk to sales", "book a demo", "request a demo", "get a demo", "demo", "get api key", "get your api key",
    "create account", "create an account", "join", "upgrade", "get access",
    # zh
    "注册", "登录", "登入", "试用", "免费试", "购买", "开始", "立即", "联系销售", "预约演示", "获取", "订阅", "开通",
    # es
    "regístrate", "registrate", "registrarse", "iniciar sesión", "inicia sesión", "prueba", "comprar", "empezar",
    "empieza", "comenzar", "comienza", "contactar ventas", "contacta ventas", "hablar con ventas", "crear cuenta",
    "suscribirse",
)
CTA_TEXT_MAX = 48
PRODUCT_SECTION_RE = re.compile(r"\b(products?|services?|solutions?|offerings?|plans?|features?)\b|产品|服务|方案|功能|productos|servicios", re.I)
CTA_KINDS = (
    ("注册", re.compile(r"sign ?up|register|create (an )?account|start (for )?free|get started free|免费开始|注册|regístr|registr|crear cuenta|first_screen=register", re.I)),
    ("登录", re.compile(r"log ?in|sign ?in|登录|登入|iniciar sesi", re.I)),
    ("联系销售", re.compile(r"contact sales|talk to sales|联系销售|contactar ventas|hablar con ventas", re.I)),
    ("预约演示", re.compile(r"demo|预约演示|演示", re.I)),
    ("试用", re.compile(r"free trial|try |试用|prueba", re.I)),
    ("付费 / 充值", re.compile(r"buy|purchase|subscribe|upgrade|pricing|购买|订阅|开通|充值|comprar|suscrib", re.I)),
    ("拿 API key", re.compile(r"api key|获取.*key|clave api", re.I)),
)
ANALYTICS_PATTERNS = (
    ("gtag", re.compile(r"\bgtag\s*\(|gtag/js")),
    ("ga4", re.compile(r"['\"=/]G-[A-Z0-9]{6,12}\b")),
    ("googletagmanager", re.compile(r"googletagmanager\.com|GTM-[A-Z0-9]{4,10}\b")),
    ("plausible", re.compile(r"plausible\.io|plausible-tracker|next-plausible", re.I)),
    ("posthog", re.compile(r"posthog", re.I)),
    ("umami", re.compile(r"\bumami\b", re.I)),
    ("vercel-analytics", re.compile(r"@vercel/analytics|/_vercel/insights")),
)
FREE_RE = re.compile(r"\bfree\b|免费|gratis|\$0(?![\d.,])", re.I)
BRAND_SPLIT = re.compile(r"\s+[|\u2013\u2014\u00b7\-:»]\s+|\s*[|｜:：]\s*")


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dedup(seq):
    seen, out = set(), []
    for x in seq:
        k = json.dumps(x, sort_keys=True, ensure_ascii=False) if not isinstance(x, str) else x
        if k not in seen:
            seen.add(k)
            out.append(x)
    return out


# ===========================================================================
# 抓取
# ===========================================================================

class Fetcher:
    """sc.robust_fetch 的薄封装:失败记 errors 返回 None;请求间隔走 sc._sleep。"""

    def __init__(self, errors):
        self.errors = errors
        self.n = 0

    def get(self, url, quiet_404=False):
        if self.n:
            sc._sleep(POLITE_DELAY)
        self.n += 1
        try:
            r = sc.robust_fetch(url, timeout=FETCH_TIMEOUT)
        except (sc.GuardError, sc.FetchError) as e:
            self.errors.append("抓取失败 %s: %s" % (url, e))
            return None
        except Exception as e:  # noqa: BLE001 — 网络层什么都可能抛,不崩
            self.errors.append("抓取异常 %s: %s" % (url, e))
            return None
        st = r.get("status")
        if st and st >= 400 and not quiet_404:
            self.errors.append("HTTP %s %s" % (st, url))
        return r


# ===========================================================================
# 页面特征
# ===========================================================================

class FeatureParser(sc.PageParser):
    """在 site_crawl.PageParser 上多收:h2、og:site_name、JSON-LD 原文、<button> 文本。"""

    def __init__(self):
        super().__init__()
        self.h2s, self._h2_buf = [], None
        self.og_site_name = None
        self.jsonld_raw, self._ld_buf = [], None
        self.buttons, self._btn_buf = [], None

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        a = {k.lower(): (v if v is not None else "") for k, v in attrs}
        if tag == "h2":
            self._h2_buf = []
        elif tag == "meta":
            nm = (a.get("property") or a.get("name") or "").strip().lower()
            if nm == "og:site_name" and self.og_site_name is None:
                self.og_site_name = (a.get("content") or "").strip() or None
        elif tag == "script" and (a.get("type") or "").strip().lower() == "application/ld+json":
            self._ld_buf = []
        elif tag == "button":
            self._btn_buf = []

    def handle_endtag(self, tag):
        super().handle_endtag(tag)
        if tag == "h2" and self._h2_buf is not None:
            t = " ".join("".join(self._h2_buf).split())
            if t:
                self.h2s.append(t)
            self._h2_buf = None
        elif tag == "script" and self._ld_buf is not None:
            self.jsonld_raw.append("".join(self._ld_buf))
            self._ld_buf = None
        elif tag == "button" and self._btn_buf is not None:
            t = " ".join("".join(self._btn_buf).split())
            if t:
                self.buttons.append(t)
            self._btn_buf = None

    def handle_data(self, d):
        if self._ld_buf is not None:
            self._ld_buf.append(d)
            return
        super().handle_data(d)
        if self._h2_buf is not None:
            self._h2_buf.append(d)
        if self._btn_buf is not None:
            self._btn_buf.append(d)


def _jsonld_nodes(raw_blocks):
    """JSON-LD 原文块 → 节点列表(展开顶层数组与 @graph);坏 JSON 跳过。"""
    nodes = []

    def walk(x):
        if isinstance(x, list):
            for i in x:
                walk(i)
        elif isinstance(x, dict):
            nodes.append(x)
            if "@graph" in x:
                walk(x["@graph"])
    for raw in raw_blocks:
        try:
            walk(json.loads(raw.strip()))
        except (ValueError, TypeError):
            continue
    return nodes


def _types_of(node):
    t = node.get("@type")
    if isinstance(t, str):
        return [t]
    if isinstance(t, list):
        return [x for x in t if isinstance(x, str)]
    return []


def is_cta(text):
    t = (text or "").strip().lower()
    if not t or len(t) > CTA_TEXT_MAX:
        return False
    for w in CTA_WORDS:
        if re.search(r"[\u3400-\u9fff]", w):
            if w in t:
                return True
        elif re.search(r"(?<![\w])" + re.escape(w) + r"(?![\w])", t):
            return True
    return False


def extract_prices(text):
    found = []
    for rx in PRICE_RES:
        for m in rx.finditer(text):
            s = " ".join(m.group(0).split()).rstrip(",.")
            found.append((m.start(), s))
    found.sort()
    return _dedup([s for _, s in found])[:PRICES_MAX]


def page_features(resp, url):
    """抓取结果 → 契约里的页面特征 dict;resp 为 None 时给空壳(status=None)。"""
    feat = {"url": url, "final_url": None, "status": None, "title": None, "description": None, "h1": [],
            "h2": [], "lang": None, "hreflang_count": 0, "og_site_name": None, "jsonld_types": [],
            "same_as": [], "prices": [], "ctas": [], "noindex": False, "word_count": 0}
    if not resp:
        return feat, {}
    feat["status"] = resp.get("status")
    feat["final_url"] = resp.get("final_url") or url
    body = resp.get("body") or ""
    base = feat["final_url"]
    p = FeatureParser()
    try:
        p.feed(body[:sc.PAGE_READ_CAP])
    except Exception:  # noqa: BLE001 — 坏 HTML 不抛
        pass
    feat["title"] = p.title
    feat["description"] = next((d for d in p.descriptions if d), None)
    feat["h1"] = [h for h in p.h1s if h]
    feat["h2"] = _dedup(p.h2s)[:H2_MAX]
    feat["lang"] = p.lang or None
    feat["hreflang_count"] = len(p.hreflangs)
    feat["og_site_name"] = p.og_site_name
    nodes = _jsonld_nodes(p.jsonld_raw)
    types, same_as, org_name = [], [], None
    for n in nodes:
        ts = _types_of(n)
        types.extend(ts)
        if any(t in ("Organization", "Corporation", "Person", "LocalBusiness", "OnlineBusiness") for t in ts):
            sa = n.get("sameAs")
            if isinstance(sa, str):
                same_as.append(sa)
            elif isinstance(sa, list):
                same_as.extend(x for x in sa if isinstance(x, str))
            if org_name is None and "Person" not in ts and isinstance(n.get("name"), str):
                org_name = n["name"].strip() or None
    feat["jsonld_types"] = _dedup(types)
    feat["same_as"] = _dedup(same_as)
    text = " ".join(" ".join(p.text).split())
    feat["prices"] = extract_prices(text)
    ctas = []
    for href, anchor in zip(p.hrefs, p.anchors):
        if is_cta(anchor):
            ctas.append({"text": anchor, "href": urllib.parse.urljoin(base, href)})
    for b in p.buttons:
        if is_cta(b):
            ctas.append({"text": b, "href": None})
    feat["ctas"] = _dedup(ctas)[:CTAS_MAX]
    names = set()
    for v in p.robots_meta:
        names |= sc.robots_names(v)
    xrt = sc._header(resp.get("headers"), "x-robots-tag")
    if xrt:
        names |= sc.header_robots(xrt)
    feat["noindex"] = "noindex" in names or "none" in names
    feat["word_count"] = len(sc._TOKEN_RE.findall(text))
    extra = {"org_name": org_name, "hreflangs": [c for c, _ in p.hreflangs], "hrefs": p.hrefs, "text": text,
             "html": body}
    return feat, extra


# ===========================================================================
# URL 归类
# ===========================================================================

def split_locale(path):
    """路径 → (locale|None, 剥掉语言前缀后的段列表)。"""
    segs = [s for s in urllib.parse.unquote(path or "/").split("/") if s]
    if segs:
        m = LOCALE_RE.match(segs[0])
        if m and m.group(1).lower() in LANG_CODES and segs[0].lower() not in ("vs",):
            return segs[0].lower().replace("_", "-"), segs[1:]
    return None, segs


LINE_ROUTE_SEGS = {"products", "product", "features", "feature", "solutions", "solution", "tools", "apps", "modules"}


def route_lines(paths):
    """/products/<x>、/features/<x>、/solutions/<x> 这类一层子页 → 产品线名(按路由取,语言前缀剥掉、去重)。
    动态段([slug]、:id)和列表页不算。"""
    out, seen = [], set()
    for path in paths or []:
        _, segs = split_locale(urllib.parse.urlsplit(path).path)
        if len(segs) != 2 or segs[0].lower() not in LINE_ROUTE_SEGS:
            continue
        slug = segs[1]
        if not slug or slug.startswith(("[", ":")) or "." in slug:
            continue
        name = re.sub(r"[-_]+", " ", slug).strip()
        key = name.lower()
        if key and key not in seen:
            seen.add(key)
            out.append(name[:1].upper() + name[1:])
    return out


def classify_segments(segs):
    if not segs:
        return "other"
    first = segs[0].lower()
    for t, words in PAGE_TYPE_RULES:
        if first in words:
            return t
    for seg in segs:                       # 任意段里的 x-vs-y / x-alternatives → compare
        toks = seg.lower().split("-")
        if len(toks) > 1 and ("vs" in toks or "versus" in toks or "alternative" in toks or "alternatives" in toks):
            return "compare"
    toks = first.split("-")
    for t, words in TOKEN_RULES:
        if any(w in toks for w in words):
            return t
    return "other"


def classify_url(url):
    loc, segs = split_locale(urllib.parse.urlsplit(url).path)
    return loc, classify_segments(segs)


# ===========================================================================
# 站点扫描
# ===========================================================================

def _maybe_gunzip(blob):
    if blob[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(blob)[:sc.SITEMAP_MAX_BYTES]
        except OSError:
            return blob
    return blob


def scan_sitemaps(fetcher, seeds, max_urls, errors, declared):
    """seeds 广度优先;sitemapindex 递归,子 sitemap 总数 ≤ SITEMAP_CHILD_MAX;URL 去重。"""
    urls, seen_urls, sources, visited = [], set(), [], set()
    queue = [(u, 0, u in declared) for u in seeds]
    children_fetched, truncated, full = 0, False, False
    while queue and not full:
        sm, depth, loud = queue.pop(0)
        if sm in visited:
            continue
        visited.add(sm)
        r = fetcher.get(sm, quiet_404=not loud)
        if not r or not r.get("status") or r["status"] >= 400:
            continue
        blob = _maybe_gunzip(r.get("body_bytes") or (r.get("body") or "").encode("utf-8"))
        try:
            kind, locs, children = sc.parse_sitemap_bytes(blob)
        except ValueError as e:
            if loud or not sc._looks_html(r.get("body") or ""):
                errors.append("sitemap 解析失败 %s: %s" % (sm, e))
            continue
        if kind == "unknown":
            continue
        sources.append(sm)
        for loc in locs:
            if loc in seen_urls:
                continue
            if len(urls) >= max_urls:
                truncated = full = True
                break
            seen_urls.add(loc)
            urls.append(loc)
        if depth < sc.SITEMAP_DEPTH_MAX:
            for ch in children:
                if ch in visited:
                    continue
                if children_fetched >= SITEMAP_CHILD_MAX:
                    truncated = True          # 子 sitemap 超上限:后面的不抓,已入队的照常解析
                    break
                children_fetched += 1
                queue.append((ch, depth + 1, True))
    return urls, sources, truncated


def cta_kind(text, href):
    """按钮 → 转化类型;登录、文档、快速开始这类不算转化 → None。"""
    blob = "%s %s" % (text, href)
    for name, rx in CTA_KINDS:
        if rx.search(blob):
            return None if name == "登录" else name
    return None


def scan_llms(fetcher, origin):
    out = {"llms_txt": False, "llms_full": False, "title": None, "summary": None}
    lines_h2, src = [], None
    sections, cur = {}, None
    r = fetcher.get(origin + "/llms.txt", quiet_404=True)
    if r and r.get("status") == 200 and not sc._looks_html(r.get("body") or ""):
        out["llms_txt"] = True
        src = r.get("final_url") or origin + "/llms.txt"
        for ln in (r.get("body") or "").splitlines():
            s = ln.strip()
            if out["title"] is None and re.match(r"^#\s+\S", s):
                out["title"] = s[1:].strip()
            elif out["summary"] is None and s.startswith(">"):
                out["summary"] = s.lstrip(">").strip() or None
            elif re.match(r"^##\s+\S", s):
                cur = s[2:].strip()
                lines_h2.append(cur)
                sections[cur] = []
            elif cur is not None and s.startswith(("-", "*")):
                m = re.match(r"^[-*]\s+\[([^\]]{1,80})\]", s)
                if m:
                    sections[cur].append(m.group(1).strip())
    r = fetcher.get(origin + "/llms-full.txt", quiet_404=True)
    if r and r.get("status") == 200 and not sc._looks_html(r.get("body") or ""):
        out["llms_full"] = True
    out["sections"] = sections
    return out, lines_h2, src


def wayback_first_seen(fetcher, host):
    api = "https://archive.org/wayback/available?url=%s&timestamp=19960101" % urllib.parse.quote(host)
    r = fetcher.get(api)
    if not r or r.get("status") != 200:
        return None, api
    try:
        ts = json.loads(r.get("body") or "{}")["archived_snapshots"]["closest"]["timestamp"]
        return "%s-%s-%s" % (ts[0:4], ts[4:6], ts[6:8]), api
    except (ValueError, KeyError, TypeError):
        return None, api


def pick_samples(urls, host, max_pages):
    """每个关键类型取 1 个:同主机、优先无语言前缀、再按路径最短。"""
    best = {}
    for u in urls:
        pu = urllib.parse.urlsplit(u)
        if (pu.hostname or "").lower() != host:
            continue
        loc, t = classify_url(u)
        if t not in SAMPLE_TYPES:
            continue
        key = (loc is not None, len(pu.path), u)
        if t not in best or key < best[t][0]:
            best[t] = (key, u)
    out = []
    for t in SAMPLE_TYPES:
        if t in best and len(out) < max_pages:
            out.append((t, best[t][1]))
    return out


def site_framework_hint(html, headers):
    """无仓库时从首页 HTML/响应头粗判框架(inferred)。"""
    h = (html or "")[:400_000]
    xp = (sc._header(headers, "x-powered-by") or "").lower()
    if "/_next/" in h or "__NEXT_DATA__" in h or "next.js" in xp:
        return "next"
    if "/_nuxt/" in h or "__NUXT__" in h:
        return "nuxt"
    if "wp-content" in h:
        return "wordpress"
    if "/_astro/" in h:
        return "astro"
    if "___gatsby" in h:
        return "gatsby"
    if "__sveltekit" in h or "/_app/immutable/" in h:
        return "sveltekit"
    m = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)', h, re.I)
    if m:
        g = m.group(1).lower()
        for k in ("hugo", "jekyll", "wordpress", "astro", "gatsby", "docusaurus", "webflow", "framer", "wix"):
            if k in g:
                return k
    return None


def analytics_in_text(text):
    return [name for name, rx in ANALYTICS_PATTERNS if rx.search(text or "")]


def scan_site(site, max_pages, max_urls, wayback, errors):
    fetcher = Fetcher(errors)
    pu = urllib.parse.urlsplit(site)
    origin = "%s://%s" % (pu.scheme, pu.netloc)
    host = (pu.hostname or "").lower()
    res = {"reachable": False, "homepage": None,
           "robots": {"status": None, "disallow_all": False, "sitemaps": []},
           "sitemap": {"url_count": 0, "sources": [], "truncated": False},
           "llms": {"llms_txt": False, "llms_full": False, "title": None, "summary": None},
           "page_types": {}, "locales": {}, "samples": [], "first_seen": None}
    ctx = {"origin": origin, "host": host}

    r = fetcher.get(site)
    home, hx = page_features(r, site)
    res["homepage"] = home
    ctx["home_extra"] = hx
    ctx["home_headers"] = r.get("headers") if r else None
    res["reachable"] = bool(r and r.get("status") and r["status"] < 400)
    if r and r.get("final_url"):                      # 首页跳到别的主机(apex → www)时以落地主机为准
        fh = (urllib.parse.urlsplit(r["final_url"]).hostname or "").lower()
        if fh and fh != host and res["reachable"]:
            fp = urllib.parse.urlsplit(r["final_url"])
            origin, host = "%s://%s" % (fp.scheme, fp.netloc), fh
            ctx.update(origin=origin, host=host)

    rr = fetcher.get(origin + "/robots.txt", quiet_404=True)
    declared = []
    if rr:
        res["robots"]["status"] = rr.get("status")
        body = rr.get("body") or ""
        if rr.get("status") == 200 and not sc._looks_html(body):
            doc = sc.parse_robots(body)
            if doc:
                declared = _dedup([urllib.parse.urljoin(origin + "/", s) for s in doc["sitemaps"]])
                g = doc["groups"].get("*") or {}
                res["robots"]["disallow_all"] = "/" in g.get("disallow", []) and not any(
                    a in ("/", "/*") for a in g.get("allow", []))
    res["robots"]["sitemaps"] = declared
    ctx["robots_url"] = origin + "/robots.txt"

    seeds = _dedup(declared + [origin + "/sitemap.xml"])
    urls, sources, truncated = scan_sitemaps(fetcher, seeds, max_urls, errors, set(declared))
    res["sitemap"] = {"url_count": len(urls), "sources": sources, "truncated": truncated}
    pool, pool_src = urls, (sources[0] if sources else None)
    if not urls and r:                                 # 没有 sitemap:退回首页站内链接做归类和抽样
        links = []
        for h in hx.get("hrefs", []):
            a = urllib.parse.urljoin(home["final_url"] or site, h).split("#")[0]
            if (urllib.parse.urlsplit(a).hostname or "").lower() == host:
                links.append(a)
        pool, pool_src = _dedup(links), home["final_url"] or site
    ctx["pool_src"] = pool_src
    ctx["pool_paths"] = [urllib.parse.urlsplit(u).path for u in pool]
    types, locales = {}, {}
    for u in pool:
        loc, t = classify_url(u)
        types[t] = types.get(t, 0) + 1
        if loc:
            locales[loc] = locales.get(loc, 0) + 1
    res["page_types"] = dict(sorted(types.items(), key=lambda kv: (-kv[1], kv[0])))
    res["locales"] = dict(sorted(locales.items(), key=lambda kv: (-kv[1], kv[0])))

    llms, h2s, llms_src = scan_llms(fetcher, origin)
    res["llms"] = llms
    ctx["llms_h2"], ctx["llms_src"] = h2s, llms_src

    ctx["sample_extra"] = {}
    home_final = home.get("final_url") or site
    for t, u in pick_samples(pool, host, max_pages):
        if u.rstrip("/") == home_final.rstrip("/"):
            continue
        sr = fetcher.get(u)
        f, fx = page_features(sr, u)
        res["samples"].append(dict({"type": t}, **f))
        ctx["sample_extra"][u] = fx

    if wayback:
        res["first_seen"], ctx["wayback_src"] = wayback_first_seen(fetcher, host)
    return res, ctx


# ===========================================================================
# 仓库扫描
# ===========================================================================

def _walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for f in sorted(files):
            yield os.path.join(d, f)


def _read(path, cap=SOURCE_SCAN_MAX_BYTES):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read(cap)
    except OSError:
        return ""


def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _find_app_root(repo):
    """有框架依赖的 package.json 所在目录:先 repo 根,再一层子目录(monorepo 的 web/、site/、apps/*)。"""
    cands = [repo]
    try:
        subs = sorted(x for x in os.listdir(repo) if os.path.isdir(os.path.join(repo, x)) and x not in SKIP_DIRS
                      and not x.startswith("."))
    except OSError:
        subs = []
    cands += [os.path.join(repo, s) for s in subs]
    for s in ("apps", "packages"):
        p = os.path.join(repo, s)
        if os.path.isdir(p):
            cands += [os.path.join(p, x) for x in sorted(os.listdir(p)) if os.path.isdir(os.path.join(p, x))]
    first_pkg = None
    for c in cands:
        pj = os.path.join(c, "package.json")
        if os.path.isfile(pj):
            data = _load_json(pj) or {}
            if first_pkg is None:
                first_pkg = (c, data)
            if _framework_from_deps(_deps(data)):
                return c, data
    return first_pkg if first_pkg else (repo, None)


def _deps(pkg):
    d = {}
    for k in ("dependencies", "devDependencies", "peerDependencies"):
        if isinstance((pkg or {}).get(k), dict):
            d.update(pkg[k])
    return d


def _framework_from_deps(deps):
    if "next" in deps:
        return "next"
    if "nuxt" in deps or "nuxt3" in deps:
        return "nuxt"
    if "astro" in deps:
        return "astro"
    if "gatsby" in deps:
        return "gatsby"
    if "@sveltejs/kit" in deps:
        return "sveltekit"
    if any(k.startswith("@remix-run/") for k in deps) or "@react-router/dev" in deps:
        return "remix"
    if "vite" in deps and ("react" in deps or "vue" in deps or "svelte" in deps or "solid-js" in deps):
        return "spa"
    if "react-scripts" in deps:
        return "spa"
    return None


def _config_text(root, stem):
    for ext in (".ts", ".mjs", ".js", ".cjs", ".mts"):
        p = os.path.join(root, stem + ext)
        if os.path.isfile(p):
            return p, _read(p)
    return None, ""


def _rel(repo, p):
    return os.path.relpath(p, repo).replace(os.sep, "/")


def next_app_routes(app_dir):
    routes = []
    for p in _walk(app_dir):
        if not re.match(r"^page\.(?:t|j)sx?$|^page\.mdx?$", os.path.basename(p)):
            continue
        segs = []
        skip = False
        for s in os.path.relpath(os.path.dirname(p), app_dir).split(os.sep):
            if s in ("", "."):
                continue
            if s.startswith("(") and s.endswith(")"):
                if s.startswith("(."):            # 拦截路由不是独立页面
                    skip = True
                continue                         # 路由组不进 URL
            if s.startswith("@") or s.startswith("_"):
                skip = True                       # 并行路由插槽 / 私有目录
                break
            segs.append(s)
        if not skip:
            routes.append("/" + "/".join(segs))
    return routes


def file_routes(pages_dir, exts, skip_api=True):
    routes = []
    for p in _walk(pages_dir):
        rel = os.path.relpath(p, pages_dir).replace(os.sep, "/")
        base, ext = os.path.splitext(rel)
        if ext not in exts:
            continue
        parts = base.split("/")
        if any(x.startswith("_") for x in parts):
            continue
        if skip_api and parts[0] == "api":
            continue
        if parts[-1] == "index":
            parts = parts[:-1]
        routes.append("/" + "/".join(parts))
    return routes


SEO_FILE_RES = {
    "robots": re.compile(r"^robots(?:\.txt)?(?:\.(?:ts|tsx|js|jsx|mjs|cjs|txt|astro|xml))?$", re.I),
    "sitemap": re.compile(r"^(?:sitemap[\w.-]*\.(?:ts|tsx|js|jsx|mjs|cjs|xml|astro)|sitemap\.xml|"
                          r"next-sitemap\.config\.(?:js|cjs|mjs|ts))$", re.I),
    "llms": re.compile(r"^llms(?:-full)?\.txt(?:\.(?:ts|js|mjs))?$", re.I),
}


def scan_repo(repo):
    out = {"framework": "unknown", "rendering": "unknown", "routes": [], "route_count": 0, "content_files": 0,
           "locales": [], "seo_files": {"robots": None, "sitemap": None, "llms": None}, "analytics": [],
           "readme_summary": None, "package": {"name": None, "description": None, "homepage": None}}
    ev = {}                                         # 出处(facts 用)
    app_root, pkg = _find_app_root(repo)
    out["app_root"] = _rel(repo, app_root)
    pkg_path = os.path.join(app_root, "package.json")
    if pkg is not None:
        out["package"] = {k: (pkg.get(k) if isinstance(pkg.get(k), str) else None)
                          for k in ("name", "description", "homepage")}
        ev["package"] = _rel(repo, pkg_path)
    deps = _deps(pkg)
    fw = _framework_from_deps(deps)
    if fw:
        ev["framework"] = _rel(repo, pkg_path)
    else:
        if os.path.isfile(os.path.join(repo, "hugo.toml")) or (
                os.path.isfile(os.path.join(repo, "config.toml")) and os.path.isdir(os.path.join(repo, "content"))):
            fw = "hugo"
            ev["framework"] = "hugo.toml" if os.path.isfile(os.path.join(repo, "hugo.toml")) else "config.toml"
        elif os.path.isfile(os.path.join(repo, "_config.yml")):
            fw, ev["framework"] = "jekyll", "_config.yml"
        elif os.path.isdir(os.path.join(repo, "wp-content")):
            fw, ev["framework"] = "wordpress", "wp-content/"
    out["framework"] = fw or "unknown"

    rendering = "unknown"
    if fw == "next":
        cp, ct = _config_text(app_root, "next.config")
        if re.search(r"output\s*:\s*['\"]export['\"]", ct):
            rendering = "ssg"
        else:
            rendering = "ssr"
        ev["rendering"] = _rel(repo, cp) if cp else ev.get("framework")
    elif fw == "astro":
        cp, ct = _config_text(app_root, "astro.config")
        rendering = "ssr" if re.search(r"output\s*:\s*['\"](?:server|hybrid)['\"]", ct) else "ssg"
        ev["rendering"] = _rel(repo, cp) if cp else ev.get("framework")
    elif fw in ("nuxt", "sveltekit", "remix", "wordpress"):
        rendering, ev["rendering"] = "ssr", ev.get("framework")
    elif fw in ("gatsby", "hugo", "jekyll"):
        rendering, ev["rendering"] = "ssg", ev.get("framework")
    elif fw == "spa":
        rendering, ev["rendering"] = "spa", ev.get("framework")
    out["rendering"] = rendering

    routes = []
    if fw != "astro":
        for d in ("app", "src/app"):
            p = os.path.join(app_root, d)
            if os.path.isdir(p):
                routes += next_app_routes(p)
                ev.setdefault("routes", _rel(repo, p) + "/")
        for d in ("pages", "src/pages"):
            p = os.path.join(app_root, d)
            if os.path.isdir(p):
                routes += file_routes(p, {".tsx", ".ts", ".jsx", ".js", ".mdx", ".md"})
                ev.setdefault("routes", _rel(repo, p) + "/")
    if fw == "astro":
        p = os.path.join(app_root, "src/pages")
        if os.path.isdir(p):
            routes += file_routes(p, {".astro", ".md", ".mdx", ".html"}, skip_api=False)
            ev.setdefault("routes", _rel(repo, p) + "/")
    routes = sorted(set(routes), key=lambda r: (r.count("/"), r))
    out["route_count"] = len(routes)
    out["routes"] = routes[:ROUTES_MAX]

    n_content = 0
    content_dirs = []
    for base in _dedup([repo, app_root]):
        for d in ("content", "posts", "_posts", "src/content"):
            p = os.path.join(base, d)
            if os.path.isdir(p) and p not in content_dirs:
                content_dirs.append(p)
    for p in content_dirs:
        n_content += sum(1 for f in _walk(p) if f.lower().endswith((".md", ".mdx")))
    out["content_files"] = n_content
    if content_dirs:
        ev["content_files"] = _rel(repo, content_dirs[0]) + "/"

    locs, loc_src = set(), None
    for base in _dedup([app_root, repo]):
        for d in ("messages", "locales", "locale", "i18n", "lang", "langs", "translations", "public/locales",
                  "src/locales", "src/i18n", "src/messages", "src/lang", "src/i18n/locales"):
            p = os.path.join(base, d)
            if not os.path.isdir(p):
                continue
            for x in sorted(os.listdir(p)):
                stem = os.path.splitext(x)[0] if os.path.isfile(os.path.join(p, x)) else x
                m = LOCALE_RE.match(stem)
                if m and m.group(1).lower() in LANG_CODES:
                    locs.add(stem.replace("_", "-"))
                    loc_src = loc_src or (_rel(repo, p) + "/")
    out["locales"] = sorted(locs)
    if loc_src:
        ev["locales"] = loc_src

    seo = {"robots": [], "sitemap": [], "llms": []}
    analytics, an_src = [], {}
    n_src = 0
    readme = None
    for p in _walk(repo):
        rel = _rel(repo, p)
        comps = rel.split("/")
        for k, rx in SEO_FILE_RES.items():
            if any(rx.match(c) for c in comps):
                seo[k].append(rel)
        if rel.lower() in ("readme.md", "readme", "readme.markdown", "readme.txt") and readme is None:
            readme = p
        if (p.endswith(SOURCE_EXT) and n_src < SOURCE_SCAN_MAX_FILES
                and not re.search(r"\.(?:test|spec)\.|(?:^|/)(?:tests?|__tests__|e2e)/", rel)):
            n_src += 1
            for name in analytics_in_text(_read(p)):
                if name not in an_src:
                    an_src[name] = rel
    for name in ("vercel-analytics", "posthog", "plausible", "umami"):
        dep = {"vercel-analytics": "@vercel/analytics", "posthog": "posthog-js", "plausible": "plausible-tracker",
               "umami": "@umami/node"}[name]
        if (dep in deps or (name == "posthog" and "posthog-node" in deps)) and name not in an_src:
            an_src[name] = ev.get("package") or "package.json"
    analytics = [n for n, _ in ANALYTICS_PATTERNS if n in an_src]
    out["analytics"] = analytics
    out["analytics_sources"] = an_src
    out["seo_files"] = {k: (sorted(v) if v else None) for k, v in seo.items()}

    if readme:
        out["readme_summary"] = readme_summary(_read(readme, 64 * 1024))
        ev["readme"] = _rel(repo, readme)
    out["_ev"] = ev
    return out


def readme_summary(text):
    paras, buf = [], []
    for ln in text.splitlines() + [""]:
        if ln.strip():
            buf.append(ln.strip())
        elif buf:
            paras.append(buf)
            buf = []
    for para in paras:
        first = para[0]
        if first.startswith("#") or first.startswith("<") or first.startswith("![") or first.startswith("[!["):
            continue
        if first.startswith(("```", "|", "---", "===", "- ", "* ", ">")):
            continue
        s = " ".join(para)
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s).strip()
        if len(s) < 8:
            continue
        return s[:README_MAX]
    return None


def scan_existing_context(base):
    out = []
    for rel in (".agents/product-marketing.md", ".agents/product-marketing-context.md",
                ".claude/product-marketing-context.md"):
        p = os.path.join(base, rel)
        if os.path.isfile(p):
            txt = _read(p, 2_000_000)
            heads = [ln.lstrip("#").strip() for ln in txt.splitlines() if re.match(r"^#{1,6}\s+\S", ln)]
            out.append({"path": rel, "headings": heads, "chars": len(txt)})
    return out


# ===========================================================================
# facts / signals
# ===========================================================================

def brand_from_title(title, host):
    if not title:
        return None
    parts = [x.strip() for x in BRAND_SPLIT.split(title) if x.strip()]
    if not parts:
        return None
    hostkey = re.sub(r"[^a-z0-9]", "", (host or "").lower())
    for x in parts:
        k = re.sub(r"[^a-z0-9]", "", x.lower())
        if k and len(k) >= 3 and k in hostkey:
            return x
    return parts[-1] if len(parts) > 1 and len(parts[-1]) <= len(parts[0]) else parts[0]


def build_facts(site_scan, ctx, repo_scan, existing):
    facts = []

    def add(key, value, source, kind):
        if value in (None, "", [], {}):
            return
        facts.append({"key": key, "value": value, "source": source, "kind": kind})

    ss, hx = site_scan, (ctx or {}).get("home_extra") or {}
    home = (ss or {}).get("homepage") or {}
    home_src = home.get("final_url") or home.get("url")
    samples = (ss or {}).get("samples") or []
    by_type = {s["type"]: s for s in samples}
    ev = (repo_scan or {}).get("_ev") or {}
    pkg = (repo_scan or {}).get("package") or {}

    # product.name
    if ss and home.get("status") and home["status"] < 400:
        if home.get("og_site_name"):
            add("product.name", home["og_site_name"], home_src, "fact")
        elif hx.get("org_name"):
            add("product.name", hx["org_name"], home_src, "fact")
        else:
            add("product.name", brand_from_title(home.get("title"), ctx.get("host")), home_src, "inferred")
    if not any(f["key"] == "product.name" for f in facts) and pkg.get("name"):
        add("product.name", pkg["name"], ev.get("package"), "inferred")

    # product.one_liner
    llms = (ss or {}).get("llms") or {}
    if llms.get("summary"):
        add("product.one_liner", llms["summary"], ctx.get("llms_src"), "fact")
    elif home.get("description"):
        add("product.one_liner", home["description"], home_src, "fact")
    elif home.get("h1"):
        add("product.one_liner", home["h1"][0], home_src, "fact")
    elif pkg.get("description"):
        add("product.one_liner", pkg["description"], ev.get("package"), "fact")
    elif (repo_scan or {}).get("readme_summary"):
        add("product.one_liner", repo_scan["readme_summary"], ev.get("readme"), "fact")

    # product.lines:llms.txt 里「产品 / 服务 / 方案」那一节的条目 > /products/<x> 这类路由 > 首页 h2(llms 的 ## 标题多半是栏目名,不是产品)
    llms_sections = ((ss or {}).get("llms") or {}).get("sections") or {}
    prod_sec = next((v for k, v in llms_sections.items() if v and PRODUCT_SECTION_RE.search(k)), None)
    rl_site = route_lines((ctx or {}).get("pool_paths"))
    rl_repo = route_lines((repo_scan or {}).get("routes"))
    if prod_sec:
        add("product.lines", prod_sec[:8], ctx.get("llms_src") if ctx else None, "fact")
    elif rl_site or rl_repo:                      # 路由比首页小标题可靠:h2 多半是「为什么选我们」这类卖点句
        add("product.lines", (rl_site or rl_repo)[:8],
            (ctx or {}).get("pool_src") if rl_site else ev.get("routes"), "inferred")
    elif home.get("h2"):
        add("product.lines", home["h2"], home_src, "inferred")

    # pricing.prices / pricing.model
    pp = by_type.get("pricing")
    price_page = pp if pp and pp.get("prices") else (home if home.get("prices") else None)
    if price_page:
        add("pricing.prices", price_page["prices"], price_page.get("final_url") or price_page.get("url"), "fact")
    if ss:
        ref = pp or home
        ref_src = (ref.get("final_url") or ref.get("url")) if ref else home_src
        txt = ""
        if pp:
            txt = ((ctx.get("sample_extra") or {}).get(pp["url"]) or {}).get("text", "")
        txt += " " + hx.get("text", "")
        cta_txt = " ".join(c["text"] for c in (home.get("ctas") or []) + ((pp or {}).get("ctas") or []))
        has_prices = bool((pp or {}).get("prices") or home.get("prices"))
        has_free = bool(FREE_RE.search(txt) or FREE_RE.search(cta_txt))
        contact = bool(re.search(r"contact sales|talk to sales|联系销售|contactar ventas|hablar con ventas|"
                                 r"book a demo|request a demo|预约演示", (txt + " " + cta_txt).lower()))
        if has_prices:
            model = "freemium" if has_free else "paid"
        elif contact:
            model = "contact"
        elif has_free:
            model = "free"
        else:
            model = "unknown"
        if home.get("status") or pp:
            add("pricing.model", model, ref_src, "inferred")

    # conversion.ctas:按钮归成转化类型(注册 / 付费 / 试用 / 联系销售 / 演示);登录、文档入口不算转化
    ctas = home.get("ctas") or []
    if ctas:
        kinds = []
        for c in ctas:
            k = cta_kind(c.get("text") or "", c.get("href") or "")
            if k and k not in kinds:
                kinds.append(k)
        if kinds:
            add("conversion.ctas", kinds, home_src, "inferred")
        add("conversion.buttons", ["%s → %s" % (c["text"], c["href"]) if c.get("href") else c["text"] for c in ctas],
            home_src, "fact")

    # market.languages
    if hx.get("hreflangs"):
        add("market.languages", _dedup(hx["hreflangs"]), home_src, "fact")
    elif ss and ss.get("locales"):
        add("market.languages", list(ss["locales"].keys()), ctx.get("pool_src"), "inferred")
    elif home.get("lang"):
        add("market.languages", [home["lang"]], home_src, "fact")
    if repo_scan and repo_scan.get("locales"):
        add("market.languages", repo_scan["locales"], ev.get("locales"), "inferred")

    # site.page_types / site.url_count
    if ss and ss.get("page_types"):
        add("site.page_types", ["%s:%d" % kv for kv in ss["page_types"].items()], ctx.get("pool_src"), "inferred")
    if ss and ss["sitemap"]["url_count"]:
        add("site.url_count", str(ss["sitemap"]["url_count"]) + ("+" if ss["sitemap"]["truncated"] else ""),
            ss["sitemap"]["sources"][0], "inferred")

    # tech.framework / tech.rendering
    if repo_scan and repo_scan["framework"] != "unknown":
        add("tech.framework", repo_scan["framework"], ev.get("framework"), "fact")
    elif ss and hx.get("html"):
        hint = site_framework_hint(hx["html"], ctx.get("home_headers"))
        add("tech.framework", hint, home_src, "inferred")
    if repo_scan and repo_scan["rendering"] != "unknown":
        add("tech.rendering", repo_scan["rendering"], ev.get("rendering"), "inferred")

    # measurement.analytics
    if repo_scan and repo_scan.get("analytics"):
        srcs = repo_scan.get("analytics_sources") or {}
        add("measurement.analytics", repo_scan["analytics"], srcs.get(repo_scan["analytics"][0]), "fact")
    site_an = analytics_in_text(hx.get("html", "")) if ss else []
    if site_an:
        add("measurement.analytics", site_an, home_src, "fact")

    # entity.same_as / history.first_seen / context.existing
    if home.get("same_as"):
        add("entity.same_as", home["same_as"], home_src, "fact")
    if ss and ss.get("first_seen"):
        add("history.first_seen", ss["first_seen"], ctx.get("wayback_src"), "inferred")
    if existing:
        add("context.existing", [e["path"] for e in existing], existing[0]["path"], "fact")
    return facts


def build_signals(site_scan, ctx, repo_scan):
    ss = site_scan or {}
    home = ss.get("homepage") or {}
    hx = (ctx or {}).get("home_extra") or {}
    an = list((repo_scan or {}).get("analytics") or [])
    for n in (analytics_in_text(hx.get("html", "")) if site_scan else []):
        if n not in an:
            an.append(n)
    jtypes = list(home.get("jsonld_types") or [])
    for s in ss.get("samples") or []:
        for t in s.get("jsonld_types") or []:
            if t not in jtypes:
                jtypes.append(t)
    return {
        "site_live": bool(site_scan and ss.get("reachable") and home.get("status") == 200) if site_scan else None,
        "homepage_noindex": bool(home.get("noindex")) if site_scan else None,
        "robots_block_all": bool(ss.get("robots", {}).get("disallow_all")) if site_scan else None,
        "url_count": ss.get("sitemap", {}).get("url_count") if site_scan else None,
        "first_seen": ss.get("first_seen"),
        "repo_public_routes": repo_scan.get("route_count") if repo_scan else None,
        "analytics": an,
        "has_llms_txt": bool(ss.get("llms", {}).get("llms_txt")) if site_scan else None,
        "has_jsonld": bool(jtypes) if site_scan else None,
        "jsonld_types": jtypes,
        "hreflang_locales": _dedup(hx.get("hreflangs") or []),
        "same_as": home.get("same_as") or [],
    }


def build_report(site, repo, max_pages=DEFAULT_MAX_PAGES, max_urls=DEFAULT_MAX_URLS, wayback=True, cwd=None):
    errors = []
    site_scan, ctx, repo_scan = None, {}, None
    if site:
        try:
            site_scan, ctx = scan_site(site, max_pages, max_urls, wayback, errors)
        except Exception as e:  # noqa: BLE001 — 兜底:任何意外不让整份报告丢失
            errors.append("站点扫描中断: %s: %s" % (type(e).__name__, e))
    if repo:
        try:
            repo_scan = scan_repo(repo)
        except Exception as e:  # noqa: BLE001
            errors.append("仓库扫描中断: %s: %s" % (type(e).__name__, e))
    base = repo or cwd or os.getcwd()
    existing = scan_existing_context(base)
    facts = build_facts(site_scan, ctx, repo_scan, existing)
    signals = build_signals(site_scan, ctx, repo_scan)
    if repo_scan:
        repo_scan.pop("_ev", None)
    return {"schema": SCHEMA, "generated_at": now_iso(), "site": site, "repo": repo,
            "site_scan": site_scan, "repo_scan": repo_scan, "existing_context": existing,
            "errors": errors, "facts": facts, "signals": signals}


# ===========================================================================
# 人读摘要
# ===========================================================================

def _short(v, n=160):
    s = ", ".join(map(str, v)) if isinstance(v, list) else str(v)
    return s if len(s) <= n else s[:n - 1] + "…"


def render_md(rep, elapsed=None):
    L = ["# 产品速读(product_scan)", ""]
    L.append("- 站点: %s | 仓库: %s | 生成: %s%s" % (rep["site"] or "-", rep["repo"] or "-", rep["generated_at"],
                                                 (" | 耗时 %.1fs" % elapsed) if elapsed is not None else ""))
    sg = rep["signals"]
    L.append("- 信号: 在线=%s noindex=%s robots全封=%s URL数=%s 首次出现=%s llms.txt=%s JSON-LD=%s 路由=%s 埋点=%s" % (
        sg["site_live"], sg["homepage_noindex"], sg["robots_block_all"], sg["url_count"], sg["first_seen"],
        sg["has_llms_txt"], sg["has_jsonld"], sg["repo_public_routes"], ",".join(sg["analytics"]) or "-"))
    ss = rep.get("site_scan")
    if ss:
        L.append("- 页面类型: %s" % (_short(["%s:%s" % kv for kv in ss["page_types"].items()], 300) or "-"))
        L.append("- 语言前缀: %s" % (_short(["%s:%s" % kv for kv in ss["locales"].items()], 300) or "-"))
    L += ["", "## 事实(每条带出处)", ""]
    for f in rep["facts"]:
        L.append("- **%s** [%s] %s  ← %s" % (f["key"], f["kind"], _short(f["value"]), f["source"]))
    if rep["errors"]:
        L += ["", "## 抓取问题(%d)" % len(rep["errors"]), ""]
        L += ["- %s" % e for e in rep["errors"][:20]]
        if len(rep["errors"]) > 20:
            L.append("- …另 %d 条见 JSON errors" % (len(rep["errors"]) - 20))
    return "\n".join(L) + "\n"


# ===========================================================================
# CLI
# ===========================================================================

def build_parser():
    ap = argparse.ArgumentParser(
        prog="product_scan.py",
        description="开局读透产品:读站点和/或产品仓库,产出带出处的事实草稿 JSON(下游 onboard.py 消费)。")
    ap.add_argument("--site", help="站点 URL(省略 scheme 时补 https://)")
    ap.add_argument("--repo", help="产品仓库目录")
    ap.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES, help="抽样页上限(默认 20)")
    ap.add_argument("--max-urls", type=int, default=DEFAULT_MAX_URLS, help="sitemap URL 计数上限(默认 50000)")
    ap.add_argument("--allow-local", action="store_true", help=sc.LOCAL_HINT)
    ap.add_argument("--no-wayback", action="store_true", help="不查 Wayback 最早快照")
    ap.add_argument("--out", help="JSON 写到文件(默认 stdout)")
    ap.add_argument("--md", action="store_true", help="另在 stderr 打一屏人读摘要")
    return ap


def main(argv=None):
    ns = build_parser().parse_args(argv)       # 用法错 argparse 自带退出码 2
    if not ns.site and not ns.repo:
        sys.stderr.write("[product_scan] 至少给 --site 或 --repo 之一\n")
        return 2
    if ns.max_pages < 0 or ns.max_urls < 1:
        sys.stderr.write("[product_scan] --max-pages 须 ≥0、--max-urls 须 ≥1\n")
        return 2
    site = None
    if ns.site:
        site = ns.site.strip()
        if "://" not in site:
            site = "https://" + site
        p = urllib.parse.urlsplit(site)
        if p.scheme.lower() not in ("http", "https") or not p.hostname:
            sys.stderr.write("[product_scan] --site 须是 http(s) URL: %s\n" % ns.site)
            return 2
        if not p.path:
            site += "/"
    repo = None
    if ns.repo:
        repo = os.path.abspath(os.path.expanduser(ns.repo))
        if not os.path.isdir(repo):
            sys.stderr.write("[product_scan] --repo 不是目录: %s\n" % ns.repo)
            return 2
    sc.ALLOW_LOCAL = bool(ns.allow_local)
    t0 = time.monotonic()
    rep = build_report(site, repo, ns.max_pages, ns.max_urls, wayback=not ns.no_wayback)
    elapsed = time.monotonic() - t0
    text = json.dumps(rep, ensure_ascii=False, indent=2)
    if ns.out:
        os.makedirs(os.path.dirname(os.path.abspath(ns.out)), exist_ok=True)
        with open(ns.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")
    if ns.md:
        sys.stderr.write(render_md(rep, elapsed))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        sys.exit(130)
