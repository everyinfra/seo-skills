#!/usr/bin/env python3
"""JSON-LD 实体规则检查器(stdlib)。从页面提取所有 ld+json 块,检查:
@id 绝对性 / 引用悬空(publisher/author/isPartOf 指向未声明 @id)/ 同名实体分裂 /
占位符黑名单 / 评分范围(ratingValue 超出 worstRating..bestRating)/ FAQPage 空答案 /
Google 富结果必填属性(Ahrefs「Structured data Google rich results validation error」:Site Audit
「cover checks for the required mandatory rules listed in Google's guidelines」,help.ahrefs.com/en/articles/8223239)。
用法: python3 schema_lint.py URL
退出码(脚本末行也会写明):
  0 = 没有 CRITICAL、没有富结果错误(WARN 不影响)
  1 = 有 CRITICAL(JSON 坏、引用悬空、占位符、@id 非绝对、FAQ 空答案)或富结果必填缺失/评分越界
  2 = 用法错,或页面抓不到(网络、SSRF 拒连、非 http(s))
  3 = 页面里没有 JSON-LD(没东西可查,不算错)
安全:仅 http(s)(拒 file:///ftp://);私网/环回/链路本地/保留段拒连;重定向逐跳复查。"""
import ipaddress, json, os, re, socket, sys, urllib.parse, urllib.request

UA = "Mozilla/5.0 (compatible; seo-suite-audit/1.0)"
PLACEHOLDERS = ["[Business Name]", "[City]", "[INSERT", "[REPLACE_", "[要追加", "[INVULLEN", "TODO", "example.com"]


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


def fetch(url):
    """唯一网络出口(测试打桩点):scheme 检查(仅 http(s))+ SSRF 防护 + 受控 opener。"""
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        raise FetchError("仅允许 http(s): %s" % url)
    ssrf_guard(p.hostname)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with _opener.open(req, timeout=15) as r:
        return r.read(2_000_000).decode("utf-8", "replace")

def walk(node, fn):
    if isinstance(node, dict):
        fn(node)
        for v in node.values(): walk(v, fn)
    elif isinstance(node, list):
        for v in node: walk(v, fn)

# ---- Google 富结果必填属性(developers.google.com/search/docs/appearance/structured-data/<类型>,2026-11-06 读取
# 「Required properties」表)。FAQPage 富结果 Google 已下线(faqpage 文档跳到 search/updates#removing-faq-rich-result),
# 不再按富结果校验;Article 系列没有必填项。
RICH_REQUIRED = {
    "Recipe": ("name", "image"),
    "Event": ("name", "startDate", "location"),
    "JobPosting": ("title", "description", "datePosted", "hiringOrganization"),
    "LocalBusiness": ("name", "address"),
    "VideoObject": ("name", "thumbnailUrl", "uploadDate"),
    "Dataset": ("name", "description"),
    "Product": ("name",),
    "SoftwareApplication": ("name",),
    "Review": ("author", "reviewRating"),
    "AggregateRating": ("ratingValue",),
    "BreadcrumbList": ("itemListElement",),
}
SUBTYPE_OF = {"Restaurant": "LocalBusiness", "Store": "LocalBusiness", "MedicalBusiness": "LocalBusiness",
              "MobileApplication": "SoftwareApplication", "WebApplication": "SoftwareApplication",
              "VideoGame": "SoftwareApplication", "ProductGroup": "Product"}
REVIEWABLE = ("review", "aggregateRating")
# 只把这些位置上的节点当富结果候选(白名单):顶层、@graph、页面主体、ItemList 列表项、被评对象的评价。
# 挂在 publisher/author/brand/itemReviewed 等属性下的实体只是引用,不单独出富结果,不按富结果必填查。
RICH_POSITIONS = (None, "@graph", "mainEntity", "hasPart", "itemListElement", "review", "aggregateRating")


def _types(n):
    t = n.get("@type")
    ts = t if isinstance(t, list) else [t]
    return [SUBTYPE_OF.get(str(x), str(x)) for x in ts if x]


def _num(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def rich_result_errors(node, parent_key=None):
    """单个节点的 Google 富结果必填缺失 → 消息列表。parent_key:它挂在上级哪个属性下
    (Review/AggregateRating 嵌在被评对象里时不需要 itemReviewed)。"""
    errs = []
    if parent_key not in RICH_POSITIONS:
        return errs
    for t in _types(node):
        req = RICH_REQUIRED.get(t)
        if req is None:
            continue
        miss = [k for k in req if node.get(k) in (None, "", [], {})]
        if t == "JobPosting" and node.get("jobLocation") in (None, "", [], {}) \
                and str(node.get("jobLocationType", "")).upper().find("TELECOMMUTE") < 0:
            miss.append("jobLocation(远程岗位改写 jobLocationType=TELECOMMUTE)")
        if t == "Product" and not any(node.get(k) for k in ("review", "aggregateRating", "offers")):
            miss.append("review / aggregateRating / offers 三选一")
        if t == "SoftwareApplication":
            offers = node.get("offers")
            o = offers[0] if isinstance(offers, list) and offers else offers
            if not isinstance(o, dict) or o.get("price") in (None, ""):
                miss.append("offers.price")
            if not any(node.get(k) for k in REVIEWABLE):
                miss.append("aggregateRating / review 二选一")
        if t in ("Review", "AggregateRating") and parent_key not in REVIEWABLE and not node.get("itemReviewed"):
            miss.append("itemReviewed(不嵌在被评对象里时必填)")
        if t == "AggregateRating" and not (node.get("ratingCount") or node.get("reviewCount")):
            miss.append("ratingCount / reviewCount 二选一")
        if t == "Review" and isinstance(node.get("reviewRating"), dict) and node["reviewRating"].get("ratingValue") in (None, ""):
            miss.append("reviewRating.ratingValue")
        if t == "BreadcrumbList":
            items = node.get("itemListElement")
            items = items if isinstance(items, list) else [items] if items else []
            for i, it in enumerate(items):
                if not isinstance(it, dict):
                    continue
                last = i == len(items) - 1
                need = ["position"] + ([] if last else ["item"])
                if not it.get("name") and not (isinstance(it.get("item"), dict) and it["item"].get("name")):
                    need.append("name")
                gone = [k for k in need if k != "name" and it.get(k) in (None, "", {})] + (["name"] if "name" in need else [])
                if gone:
                    miss.append("itemListElement[%d].%s" % (i, "/".join(gone)))
        if miss:
            errs.append("%s 缺 Google 富结果必填: %s" % (t, ", ".join(miss)))
    return errs


def rating_range_errors(node):
    """评分越界:ratingValue 超出 worstRating..bestRating(Google 默认 1..5,review-snippet 文档)。"""
    if not any(t in ("Rating", "AggregateRating") for t in _types(node)) and "ratingValue" not in node:
        return []
    v = _num(node.get("ratingValue"))
    if v is None:
        return []
    best = _num(node.get("bestRating")) if node.get("bestRating") is not None else 5.0
    worst = _num(node.get("worstRating")) if node.get("worstRating") is not None else 1.0
    if best is None or worst is None:
        return []
    if v > best or v < worst:
        return ["ratingValue %s 超出范围 %s..%s(没写 bestRating/worstRating 时 Google 按 1..5)"
                % (node.get("ratingValue"), node.get("worstRating", 1), node.get("bestRating", 5))]
    return []


def walk_ctx(node, fn, key=None):
    """walk 的带上级属性名版本:fn(node, parent_key)。"""
    if isinstance(node, dict):
        fn(node, key)
        for k, v in node.items():
            walk_ctx(v, fn, k)
    elif isinstance(node, list):
        for v in node:
            walk_ctx(v, fn, key)


USAGE = """usage: schema_lint.py URL
提取页面全部 JSON-LD 块,检查:@id 绝对性/引用悬空/同名实体分裂/占位符黑名单/
评分范围/FAQPage 空答案/Google 富结果必填属性。
安全:仅 http(s) URL;私网/环回/链路本地拒连;重定向逐跳复查(SSRF 防护)。
退出码:0 无 CRITICAL 且无富结果错误 / 1 有 CRITICAL 或富结果错误 / 2 用法错或页面抓不到 / 3 页面没有 JSON-LD。"""

def main():
    a = sys.argv[1:]
    if any(x in ("-h", "--help") for x in a):
        print(USAGE)
        return
    if not a or a[0].startswith("-"):
        sys.stderr.write(USAGE + "\n")
        sys.exit(2)
    url = a[0]
    try:
        html = fetch(url)
    except FetchError as e:
        sys.stderr.write("[error] %s\n" % e)
        sys.exit(2)
    except Exception as e:
        sys.stderr.write("抓取失败 %s: %s\n" % (url, e))
        sys.exit(2)
    blocks = re.findall(r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", html, re.S | re.I)
    if not blocks:
        print("无 JSON-LD")
        print("结论: 退出码 3(页面没有 JSON-LD,没东西可查)")
        sys.exit(3)
    objs, ids, raw = [], [], " ".join(blocks)
    crit_json = 0
    for b in blocks:
        try: objs.append(json.loads(b))
        except json.JSONDecodeError as e:
            print(f"[CRITICAL] JSON 解析失败: {e}"); crit_json += 1
    refs = set()
    for o in objs:
        walk(o, lambda n: refs.update(str(v) for k, v in n.items() if k in ("publisher", "author", "isPartOf", "mainEntity") and isinstance(v, str) and v.startswith("#") or (isinstance(v, str) and str(v).startswith(("http", "#")) and k in ("publisher","author","isPartOf")) ))
    allids = set()
    for o in objs:
        walk(o, lambda n: allids.add(n["@id"]) if isinstance(n.get("@id"), str) else None)
    type_by_id = {}
    for o in objs:
        # 只有 @id 没有 @type 的节点是对同页实体的引用({"@id": "…#organization"}),不是另一种类型
        # (11-05 第三轮留出站 fly.io:publisher/provider/isPartOf 里的纯引用被报「同 @id 多 @type」)
        walk(o, lambda n: type_by_id.setdefault(n.get("@id"), set()).add(",".join(map(str, n["@type"])) if isinstance(n["@type"], list) else str(n["@type"]))
             if n.get("@id") and n.get("@type") else None)
    crit = crit_json
    for o in objs:
        def check(n):
            nonlocal crit
            i = n.get("@id")
            if isinstance(i, str):
                if not i.startswith(("http", "#", "urn")):
                    print(f"[CRITICAL] @id 非绝对: {i}"); crit += 1
                if i.startswith("#") and urljoin_check(i) and f"{i}" not in allids and len(allids) > 1:
                    pass
            for k in ("publisher", "author", "isPartOf", "mainEntity"):
                v = n.get(k)
                if isinstance(v, str) and v.startswith("#") and v not in allids:
                    print(f"[CRITICAL] 引用悬空: {k}={v} 未在本页声明"); crit += 1
            ar = n.get("aggregateRating")
            if ar and n.get("@type") in ("Organization", "WebPage", "WebSite"):
                print(f"[WARN] aggregateRating 挂在 {n.get('@type')}(自评,富结果受限/垃圾信号)"); crit += 0
            if n.get("@type") == "FAQPage":
                qs = n.get("mainEntity") or []
                for q in qs:
                    ans = (q or {}).get("acceptedAnswer", {}).get("text", "")
                    if not ans or len(str(ans)) < 20:
                        print(f"[CRITICAL] FAQ 空答案: {q}"); crit += 1
        walk(o, check)
    rich = 0
    for o in objs:
        def rich_check(n, parent_key):
            nonlocal rich
            for m in rich_result_errors(n, parent_key) + rating_range_errors(n):
                print(f"[ERROR] 富结果校验: {m}")
                rich += 1
        walk_ctx(o, rich_check)
    for i, ts in type_by_id.items():
        if len(ts) > 1: print(f"[WARN] 同 @id 多 @type: {i} → {ts}")
    for p in PLACEHOLDERS:
        if p in raw: print(f"[CRITICAL] 占位符残留: {p}"); crit += 1
    def urljoin_check(i): return False
    print(f"\n块数 {len(blocks)} 有效对象 {len(objs)} @id {len(allids)};CRITICAL {crit} 条,富结果错误 {rich} 条")
    rc = 1 if (crit or rich) else 0
    print("结论: 退出码 %d(%s)" % (rc, "有 CRITICAL 或富结果错误" if rc else "没有 CRITICAL、没有富结果错误;WARN 不影响退出码"))
    sys.exit(rc)

if __name__ == "__main__": main()
