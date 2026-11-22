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
import ipaddress
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
PRICE_SNIPPETS_MAX = 8          # 定价原文最多留几句
LINES_MAX = 8                   # 路由推出的「产品线」超过这个数,多半是条目清单(工具、商品),不当产品线
CTAS_MAX = 10
ROUTES_MAX = 200
README_MAX = 300
SAMPLE_TYPES = ("pricing", "about", "docs", "blog", "product", "compare", "integrations")
SECTION_SAMPLES_MAX = 4          # 没归进上面几类的一级目录,最多再各抽 1 页
SECTION_LABEL_MAX = 40           # 栏目页大标题超过这么长多半是一句卖点,不拿来当产品线名
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
# 计费方式:页面原文里出现这些说法就记下(档案里和原文价格一起给用户确认)
BILLING_RES = (
    ("预充值", re.compile(r"top[- ]?ups?\b|prepaid|pre-paid|充值|预付|预存|recarga", re.I)),
    ("按次 / 按量", re.compile(r"pay[- ]as[- ]you[- ]go|usage[- ]based|metered|按次|按量|每次|每千次|每 ?1,?000 ?次|"
                           r"per (request|call|query|search|use|unit|1k|1,000|thousand|million|token|image|page|minute|gb)\b|"
                           r"(?<=\d)\s?/\s?(request|call|1k|k)\b|por (solicitud|uso|consulta)", re.I)),
    ("额度包", re.compile(r"credit packs?|credits? bundles?|\bpacks? of\b|额度包|点数包|积分包|流量包|"
                       r"\d[\d,]* credits\b|paquetes? de cr[eé]ditos", re.I)),
    ("订阅", re.compile(r"(?<=\d)\s?/\s?(mo|month|yr|year)\b|per (month|year|seat|user)\b|monthly|annual(ly)?|yearly|"
                      r"subscription|subscribe|包月|包年|/月|/年|每月|每年|月付|年付|suscripci|mensual|anual", re.I)),
    ("免费档 / 免费额度", re.compile(r"free (tier|plan|quota|credits?|requests?|calls?|searches?)|\d[\d,]* free\b|"
                               r"\bfree\b(?!\s*trial)|免费额度|免费次数|免费版|免费套餐|gratis|plan gratuito", re.I)),
    ("试用", re.compile(r"free trial|\btrial\b|试用|prueba (gratis|gratuita)", re.I)),
    ("一次性购买", re.compile(r"one[- ]time|lifetime|一次性|买断|pago [uú]nico", re.I)),
)
# 免运费、免费配送、免费退换这类说法不是免费档:算收费方式之前先去掉
SHIPPING_FREE_RE = re.compile(
    r"\bfree\s+(?:[\w$€£.,-]+\s+){0,3}?(?:shipping|delivery|returns?|exchanges?)\b|"
    r"\b(?:shipping|delivery|returns?)\s+(?:is\s+|are\s+)?(?:always\s+)?free\b|"
    r"免运费|包邮|免邮|免费(?:配送|送货|快递|邮寄|退换货?|退货|换货|运送)|"
    r"env[ií]o\s+gratis|env[ií]o\s+gratuito|gratis\s+env[ií]o|devoluci[oó]n(?:es)?\s+gratis|"
    r"kostenlose[rn]?\s+(?:versand|lieferung|r[üu]cksendung)|versandkostenfrei|livraison\s+gratuite", re.I)
SENT_SPLIT = re.compile(r"(?<=[.!?。!?])\s+")
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
        self.log = []                  # 实际请求过的每个 URL:{"url", "status"}(失败 status=None)

    def get(self, url, quiet_404=False):
        if self.n:
            sc._sleep(POLITE_DELAY)
        self.n += 1
        rec = {"url": url, "status": None}
        self.log.append(rec)
        try:
            r = sc.robust_fetch(url, timeout=FETCH_TIMEOUT)
        except (sc.GuardError, sc.FetchError) as e:
            self.errors.append("抓取失败 %s: %s" % (url, e))
            return None
        except Exception as e:  # noqa: BLE001 — 网络层什么都可能抛,不崩
            self.errors.append("抓取异常 %s: %s" % (url, e))
            return None
        st = r.get("status")
        rec["status"] = st
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
    chunks = [" ".join(t.split()) for t in p.text if t and t.strip()]
    extra = {"org_name": org_name, "hreflangs": [c for c, _ in p.hreflangs], "hrefs": p.hrefs, "text": text,
             "chunks": chunks, "html": body}
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


def section_label(name, head=None):
    """一级目录的候选产品线名:栏目页(/shop/)的大标题短、不是一句话就用它(「Shop coffee beans」),
    读不到或像一句卖点就用目录名(「Shop」)。"""
    base = re.sub(r"[-_]+", " ", name).strip()
    base = base[:1].upper() + base[1:]
    h = " ".join(str((head or {}).get("h1") or "").split())
    if not h or len(h) > SECTION_LABEL_MAX or re.search(r"[。!?!?,,;;::|]|\.(\s|$)", h):
        return base
    return h


def section_lines(paths, samples=None, heads=None):
    """没归进已知类型、下面有子页的一级目录(/shop/<x>、/gear/<x>)→ 候选产品线(页数多的在前)。
    名字先取栏目页的大标题(heads:目录名 → {"h1"}),读不到用目录名;两个目录取到同一个标题时都退回目录名。
    只有一页的目录(/about/、/shipping/ 这类)不算。读站点时抽过这些目录的页(samples 里 type=section):
    有的抽样页上有价格、有的没有,就只留有价格的(卖东西的目录),都没有价格就全留。"""
    dirs = {}
    for path in paths or []:
        _, segs = split_locale(urllib.parse.urlsplit(path).path)
        if len(segs) < 2 or classify_segments(segs) not in ("other", "category"):
            continue
        name = segs[0]
        if name.startswith(("[", ":")) or "." in name:
            continue
        dirs.setdefault(name.lower(), [name, set()])[1].add("/".join(segs[1:]).lower())
    priced = {}
    for s in samples or []:
        if s.get("type") != "section":
            continue
        _, segs = split_locale(urllib.parse.urlsplit(s.get("url") or "").path)
        if segs:
            priced[segs[0].lower()] = bool(s.get("prices"))
    if any(priced.values()):
        dirs = {k: v for k, v in dirs.items() if priced.get(k, True)}
    ranked = sorted(dirs.items(), key=lambda kv: (-len(kv[1][1]), kv[0]))
    labels = [section_label(name, (heads or {}).get(key)) for key, (name, _) in ranked]
    seen = {}
    for x in labels:
        seen[x.lower()] = seen.get(x.lower(), 0) + 1
    return [x if seen[x.lower()] == 1 else section_label(name)
            for x, (_, (name, _)) in zip(labels, ranked)]


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


def is_local_host(host):
    """本机或私网主机(localhost、*.localhost、回环、私网、链路本地):这类站不拿去问外部历史服务。"""
    h = (host or "").strip().strip("[]").lower().rstrip(".")
    if not h:
        return False
    if h == "localhost" or h.endswith(".localhost"):
        return True
    try:
        ip = ipaddress.ip_address(h.split("%", 1)[0])
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private or ip.is_link_local


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
    """每个关键类型取 1 个:同主机、优先无语言前缀、再按路径最短;没归类的一级目录再各抽 1 页(type=section)。"""
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
    # 目录名不在上面几类里的站(/shop/、/brew-guides/、/subscription/ 这类):按一级目录各抽 1 页,
    # 页数多的目录先抽;目录下有子页就抽子页(看得到卖的、写的是什么),只有一页就抽那一页
    sections = {}
    for u in urls:
        pu = urllib.parse.urlsplit(u)
        if (pu.hostname or "").lower() != host:
            continue
        loc, segs = split_locale(pu.path)
        if not segs or classify_segments(segs) not in ("other", "category"):
            continue
        sections.setdefault(segs[0].lower(), []).append((loc is not None, len(segs) < 2, len(pu.path), u))
    ranked = sorted(sections.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for name, items in ranked[:SECTION_SAMPLES_MAX]:
        if len(out) >= max_pages:
            break
        out.append(("section", min(items)[3]))
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
           "page_types": {}, "locales": {}, "samples": [], "first_seen": None, "fetched": fetcher.log}
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
    if urls:                                           # 一级栏目页数:以后每周运营单拿 sitemap 和它比,认新栏目
        from lifecycle import section_counts
        res["sections"] = dict(sorted(section_counts(urls).items()))

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
    # 没归类的一级目录:抽到的是子页(/shop/<x>)时再读一次栏目页(/shop/),拿它的大标题给候选产品线起名
    ctx["section_heads"] = {}
    for s in [x for x in res["samples"] if x.get("type") == "section"]:
        su = urllib.parse.urlsplit(s["url"])
        parts = [x for x in su.path.split("/") if x]
        _, segs = split_locale(su.path)
        if not segs:
            continue
        head = s
        if len(segs) > 1:
            idx = "%s://%s/%s/" % (su.scheme, su.netloc, "/".join(parts[:len(parts) - len(segs) + 1]))
            head, _ = page_features(fetcher.get(idx, quiet_404=True), idx)
        if head.get("status") == 200 and head.get("h1"):
            ctx["section_heads"][segs[0].lower()] = {"h1": head["h1"][0], "url": head.get("final_url") or head.get("url")}

    if wayback and is_local_host(host):
        errors.append("本机 / 私网站点(%s)不查 Wayback 最早快照" % host)
    elif wayback:
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


PAGE_FILES = {"home": ("app/page", "src/app/page", "pages/index", "src/pages/index"),
              "pricing": ("app/pricing/page", "src/app/pricing/page", "pages/pricing", "pages/pricing/index",
                          "src/pages/pricing", "src/pages/pricing/index"),
              "layout": ("app/layout", "src/app/layout", "pages/_document", "src/pages/_document", "pages/_app")}
PAGE_EXTS = (".tsx", ".jsx", ".ts", ".js", ".mdx", ".md", ".astro", ".vue", ".svelte")
MIGRATION_FILE_RE = re.compile(r"^(?:migration|site[-_]?migration|url[-_]?migration|redirect[-_]?(?:map|plan)|"
                               r"replatform(?:ing)?|relaunch)[\w.-]*\.(?:md|markdown|txt|csv)$", re.I)


def _find_page(app_root, kind):
    for stem in PAGE_FILES[kind]:
        for ext in PAGE_EXTS:
            p = os.path.join(app_root, stem + ext)
            if os.path.isfile(p):
                return p
    return None


def _js_string(raw):
    try:
        return json.loads('"%s"' % raw.replace('"', '\\"')) if "\\u" in raw else raw
    except ValueError:
        return raw


def page_source_facts(text):
    """页面源码(Next / Astro / 一般 JSX)里读得出的:metadata 的 title / description、siteName、<html lang>、可见文字块。"""
    out = {}
    for key in ("title", "description", "siteName"):
        m = re.search(r"\b%s\s*:\s*([\"'`])((?:\\.|(?!\1).){2,400})\1" % key, text)
        if m:
            out[key] = _js_string(m.group(2)).strip()
    m = re.search(r"<html\b[^>]*\blang=[\"']([A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?)[\"']", text)
    if m:
        out["lang"] = m.group(1)
    chunks = []
    for m in re.finditer(r">([^<>{}]{3,600})<", text):
        t = re.sub(r"\s+", " ", m.group(1)).strip()
        if len(t) >= 3 and re.search(r"[A-Za-z一-鿿]", t) and t not in chunks:
            chunks.append(t)
    out["chunks"] = chunks
    return out


def repo_pages(repo, app_root):
    """仓库里首页、定价页、根布局的源码事实(没有站点或站点读不到时当草稿);→ {kind: {"src", ...}}。"""
    out = {}
    for kind in PAGE_FILES:
        p = _find_page(app_root, kind)
        if p:
            out[kind] = dict(page_source_facts(_read(p, 256 * 1024)), src=_rel(repo, p))
    return out


def migration_plans(repo):
    """仓库根和 docs/ 下的改版 / 迁移计划文件(MIGRATION.md、redirect-map.csv 这类)→ 相对路径列表。"""
    found = []
    for d in (repo, os.path.join(repo, "docs")):
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        for n in names:
            if MIGRATION_FILE_RE.match(n) and os.path.isfile(os.path.join(d, n)):
                found.append(_rel(repo, os.path.join(d, n)))
    return found


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
        rtext = _read(readme, 64 * 1024)
        out["readme_summary"] = readme_summary(rtext)
        m = re.search(r"^#\s+(.+?)\s*#*\s*$", rtext, re.M)
        out["readme_title"] = m.group(1).strip() if m else None
        ev["readme"] = _rel(repo, readme)
    out["pages"] = repo_pages(repo, app_root)
    out["migration_plans"] = migration_plans(repo)
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


def _has_price(s):
    return any(rx.search(s) for rx in PRICE_RES)


def pricing_snippets(chunks):
    """定价页的文字块 → 写到价格或计费方式的原句(保留档位名;短标题接到下一句前面),最多 PRICE_SNIPPETS_MAX 句。"""
    out, label = [], None
    for ch in chunks or []:
        if len(ch) <= 40 and not _has_price(ch) and not re.search(r"[.!?。!?]$", ch):
            label = ch
            continue
        used = False
        for sent in SENT_SPLIT.split(ch):
            sent = sent.strip()
            if not sent or len(sent) > 240:
                continue
            if _has_price(sent) or any(rx.search(sent) for _, rx in BILLING_RES):
                if label and not used and ":" not in sent[:40] and ":" not in sent[:40]:
                    sent = "%s: %s" % (label, sent)
                used = True
                if sent not in out:
                    out.append(sent)
        if used or not _has_price(ch):
            label = None
        if len(out) >= PRICE_SNIPPETS_MAX:
            break
    return out[:PRICE_SNIPPETS_MAX]


def strip_shipping(text):
    return SHIPPING_FREE_RE.sub(" ", text or "")


def billing_modes(text):
    text = strip_shipping(text)
    return [name for name, rx in BILLING_RES if rx.search(text)]


def build_facts(site_scan, ctx, repo_scan, existing):
    facts = []

    def add(key, value, source, kind, **extra):
        if value in (None, "", [], {}):
            return
        facts.append(dict({"key": key, "value": value, "source": source, "kind": kind}, **extra))

    ss, hx = site_scan, (ctx or {}).get("home_extra") or {}
    home = (ss or {}).get("homepage") or {}
    home_src = home.get("final_url") or home.get("url")
    samples = (ss or {}).get("samples") or []
    by_type = {s["type"]: s for s in samples}
    ev = (repo_scan or {}).get("_ev") or {}
    pkg = (repo_scan or {}).get("package") or {}

    rp = (repo_scan or {}).get("pages") or {}
    rhome, rlayout, rprice = rp.get("home") or {}, rp.get("layout") or {}, rp.get("pricing") or {}

    def has(key):
        return any(f["key"] == key for f in facts)

    def unknown(key, note, *looked):
        # 读不到也留下这个键(值为空、标 unknown、写明查过哪里),开局第 1 环拿它问用户;不让键整个缺掉
        if has(key) or not (ss or repo_scan):
            return
        src = _dedup([x for x in looked if x])
        facts.append({"key": key, "value": None, "kind": "unknown", "note": note,
                      "source": ("查过:" + "、".join(src)) if src else "没读到可靠出处"})

    # product.name:站点 og:site_name / Organization / title > 仓库根布局的 siteName > package.json name > README 标题
    if ss and home.get("status") and home["status"] < 400:
        if home.get("og_site_name"):
            add("product.name", home["og_site_name"], home_src, "fact")
        elif hx.get("org_name"):
            add("product.name", hx["org_name"], home_src, "fact")
        else:
            add("product.name", brand_from_title(home.get("title"), ctx.get("host")), home_src, "inferred")
    if not has("product.name") and (rlayout.get("siteName") or rhome.get("siteName")):
        src = rlayout if rlayout.get("siteName") else rhome
        add("product.name", src["siteName"], src["src"], "fact")
    if not has("product.name") and pkg.get("name"):
        add("product.name", pkg["name"], ev.get("package"), "inferred")
    if not has("product.name") and (repo_scan or {}).get("readme_title"):
        add("product.name", repo_scan["readme_title"], ev.get("readme"), "inferred")
    unknown("product.name", "首页、package.json、README 都没读到产品名", home_src, ev.get("package"), ev.get("readme"))

    # product.one_liner
    llms = (ss or {}).get("llms") or {}
    if llms.get("summary"):
        add("product.one_liner", llms["summary"], ctx.get("llms_src"), "fact")
    elif home.get("description"):
        add("product.one_liner", home["description"], home_src, "fact")
    elif home.get("h1"):
        add("product.one_liner", home["h1"][0], home_src, "fact")
    elif rhome.get("description"):                 # 站点读不到时:仓库首页源码的 metadata description
        add("product.one_liner", rhome["description"], rhome["src"], "fact")
    elif pkg.get("description"):
        add("product.one_liner", pkg["description"], ev.get("package"), "fact")
    elif (repo_scan or {}).get("readme_summary"):
        add("product.one_liner", repo_scan["readme_summary"], ev.get("readme"), "fact")
    unknown("product.one_liner", "首页、llms.txt、仓库都没读到一句话介绍", home_src, rhome.get("src"), ev.get("readme"))

    # product.lines:llms.txt 里「产品 / 服务 / 方案」那一节的条目 > /products/<x> 这类路由 > 首页 h2(llms 的 ## 标题多半是栏目名,不是产品)
    llms_sections = ((ss or {}).get("llms") or {}).get("sections") or {}
    prod_sec = next((v for k, v in llms_sections.items() if v and PRODUCT_SECTION_RE.search(k)), None)
    rl_site = route_lines((ctx or {}).get("pool_paths"))
    rl_repo = route_lines((repo_scan or {}).get("routes"))
    # 首页 h2 多半是「为什么选我们」这类卖点句,不拿来兜底;路由推的只算推测,条目太多(工具、商品清单)不算产品线。
    # 拿不准就留一条「未知」,开局第 1 环问用户。
    rl = rl_site or rl_repo
    sl = [] if rl else section_lines((ctx or {}).get("pool_paths"), samples, (ctx or {}).get("section_heads"))
    if prod_sec:
        add("product.lines", prod_sec[:LINES_MAX], ctx.get("llms_src") if ctx else None, "fact")
    elif rl and len(rl) <= LINES_MAX:
        add("product.lines", rl, (ctx or {}).get("pool_src") if rl_site else ev.get("routes"), "inferred")
    elif sl and len(sl) <= LINES_MAX:
        add("product.lines", sl, (ctx or {}).get("pool_src"), "inferred",
            note="按 sitemap 里有子页的一级目录猜的(名字取栏目页的大标题,读不到就用目录名)")
    elif ss or repo_scan:
        if sl and not rl:
            note = "sitemap 里有 %d 个带子页的一级目录(例:%s),太多,不当产品线" % (len(sl), "、".join(sl[:3]))
        elif rl:
            note = "网址里有 %d 个同一层的子页(例:%s),像是条目清单,不当产品线" % (len(rl), "、".join(rl[:3]))
        elif home.get("h2"):
            note = "llms.txt 没有产品段,网址里没有 /products/<x> 这类子页;首页的 %d 个小标题多半是卖点句,不当产品线" % len(home["h2"])
        else:
            note = "llms.txt 没有产品段,网址里也没有 /products/<x> 这类子页"
        looked = [x for x in ((ctx or {}).get("llms_src"), (ctx or {}).get("pool_src"), home_src, ev.get("routes")) if x]
        facts.append({"key": "product.lines", "value": None, "kind": "unknown", "note": note,
                      "source": "查过:" + "、".join(_dedup(looked)) if looked else "没读到可靠出处"})

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
        has_free = bool(FREE_RE.search(strip_shipping(txt)) or FREE_RE.search(strip_shipping(cta_txt)))
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
        page_chunks = ((ctx.get("sample_extra") or {}).get(pp["url"]) or {}).get("chunks") if pp else None
        snips = pricing_snippets(page_chunks) if page_chunks else []
        snip_src = ref_src
        if not snips:
            snips = [x for x in pricing_snippets(hx.get("chunks")) if _has_price(x)]
            snip_src = home_src
        modes = billing_modes(" ".join(snips) + " " + txt)
        if snips:                                  # 原文价格、档位、计费方式;枚举只作附加字段
            add("pricing.model", " / ".join(snips), snip_src, "fact", enum=model, billing=modes)
        elif (home.get("status") or pp) and model != "unknown":   # 没读到就留给下面的 unknown(),不把内部值当原文
            add("pricing.model", model, ref_src, "inferred", enum=model, billing=modes)
    if not has("pricing.model") and rprice.get("chunks"):   # 站点读不到时:仓库定价页源码里的原文
        snips = pricing_snippets(rprice["chunks"])
        if snips:
            rtxt = " ".join(rprice["chunks"])
            prices = _dedup([p for c in rprice["chunks"] for p in extract_prices(c)])[:PRICES_MAX]
            if prices and not has("pricing.prices"):
                add("pricing.prices", prices, rprice["src"], "fact")
            ftxt = strip_shipping(rtxt)
            model = ("freemium" if FREE_RE.search(ftxt) else "paid") if prices else ("free" if FREE_RE.search(ftxt) else "unknown")
            add("pricing.model", " / ".join(snips), rprice["src"], "fact", enum=model,
                billing=billing_modes(" ".join(snips) + " " + rtxt))
    unknown("pricing.model", "定价页、首页、仓库里都没读到价格或收费方式的原文",
            (pp or {}).get("final_url") or (pp or {}).get("url"), home_src, rprice.get("src"), rhome.get("src"))

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
    if not has("market.languages") and rlayout.get("lang"):
        add("market.languages", [rlayout["lang"]], rlayout["src"], "fact")
    unknown("market.languages", "页面没写 lang / hreflang,仓库里也没有语言目录", home_src, rlayout.get("src"))

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


def fetched_lines(rep, indent=""):
    """实际请求过的 URL,一行一个(含 robots.txt、sitemap、llms.txt、抽样页)。"""
    log = ((rep or {}).get("site_scan") or {}).get("fetched") or []
    if not log:
        return []
    return ["%s请求过的 URL(%d 个):" % (indent, len(log))] + [
        "%s- %s %s" % (indent, x.get("status") or "失败", x["url"]) for x in log]


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
    if ss:
        L += [""] + fetched_lines(rep)
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
        print("\n".join(fetched_lines(rep) + ["写到 %s" % ns.out]))
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
