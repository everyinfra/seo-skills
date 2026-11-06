#!/usr/bin/env python3
"""site_crawl.py — 全站发现与爬取器(stdlib only)。

发现链(unlighthouse 官方优先级,references/monitoring/ci-gates.md §四,取到即止):
  ① --urls 手工清单文件(给出即关闭 ②③④)
  ② robots.txt:解析 Disallow 做排除 + Sitemap: 指令入队
  ③ sitemap:递归解析 sitemap index 嵌套;**≥50 条 loc 则关闭爬虫兜底**(代表性够,sitemap 优先);
     但站内链接指向、sitemap 没列的 URL 仍排在 sitemap 后面请求(source=link,同受 --max),记状态码和
     重定向跳数,断链/重定向链/分页深处的页才查得到;--sitemap-only 恢复「链接只进图不请求」
  ④ 爬虫兜底:BFS 从首页沿内链走,采集 <a href> 同域链接
(链⑤ 前端路由定义抽取不在本脚本范围——monitor.py sample-keypages 另议。)

子域发现(默认开启,--same-host 收紧到单主机):
  (a) robots Sitemap 指令/sitemap loc/内链里出现的其他同 registrable domain 子域(直接采信);
  (b) 常见子域 DNS 解析探测(www/m/blog/docs/shop/support/api/dev/staging,
      socket.getaddrinfo 解析成功且 HTTP 200 才收);
  (c) --subs ct 走 crt.sh JSON(https://crt.sh/?q=%.{domain}&output=json),失败优雅跳过。
  收下的子域仍须 DNS+200 验证(与 (b) 同一验收口),主机级 robots.txt 各自遵守。

礼貌与预算:robots.txt 默认遵守(RFC 9309:连续 UA 合并/最长匹配/Allow 平局胜;
crawl-delay 取 * 组,与 --delay 取大者;--ignore-robots 显式关);每 URL 传输层失败重试
2 次(带退避,4xx/5xx 是确定性响应不重试);重定向跟随记链(≤10 跳);--max 默认 500、
上限 5000(超出警告并截断,建议采样)。

SSRF 防御(照 monitor.py/traffic_funnel.py 惯例):仅 http(s)+拒私网/环回/链路本地/
保留/组播;重定向逐跳复查(站方可控的 Sitemap 指令可 302 到 169.254.169.254 穿墙);
198.18.0.0/15(RFC2544)豁免本机 fake-IP 代理,SEO_CRAWL_STRICT_SSRF=1 恢复全拒。
--allow-local:审本地开发版网站时只多放行本机回环(127.0.0.0/8、::1、localhost),
私网段(10/8、172.16/12、192.168/16)、链路本地、保留段照旧拒绝。

URL 归一:去 fragment/尾斜杠原样保留/参数默认保留(--strip-params 可开)/
大小写路径不合并/scheme+host 小写/去默认端口;已见集合去重。

输出:crawl.json(--out,默认 crawl.json)+ --urls-out 纯 URL 清单(直接喂
site_audit.py / traffic_funnel.py --urls)+ --json 打 stdout + markdown 人读摘要。
edges 形如 {src,dst,anchor}:anchor 键可缺(R3-5 锚文本采集;短于 2 字/无文本的锚
不落盘),下游读 src/dst 不受影响。不抓外链目标(只记);--check-external 可选对外
链域抽样 HEAD(默认关;用途:外链域存活抽检,验证指向是否已腐烂,不做外爬)。

退出码:0=正常;1=存在错误页(4xx/5xx 或重试后仍失败);2=输入/用法错;3=全部起点失败。

用法: python3 site_crawl.py https://example.com [--urls FILE] [--max N] [--json]
"""
from __future__ import annotations

import argparse
import gzip
import ipaddress
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from collections import Counter, deque
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hreflang_cluster import check_lang  # noqa: E402  语言码校验唯一实现(sitemap_audit 同款)

UA = "Mozilla/5.0 (compatible; seo-suite-crawl/1.0)"   # 套件 UA 惯例:seo-suite-<tool>/1.0
UA_TOKEN = "seo-suite-crawl"                            # robots.txt 自我标识 token
SCHEMA_VERSION = 1
MAX_BYTES = 2_000_000            # 单响应字节上限(site_audit 同款)
SITEMAP_MAX_BYTES = 50 * 1024 * 1024 + 1   # sitemap / robots 类文本:Google 单个 sitemap 上限 50MB(未压缩)
SITEMAP_EXT = (".xml", ".xml.gz", ".gz", ".txt")
ROBOTS_MAX_BYTES = 500_000       # RFC 9309:robots.txt 至少按前 500KiB 处理
RETRIES = 2                      # 每 URL 传输层失败重试 2 次(共 3 次尝试)
REDIRECT_HOPS_MAX = 10
SITEMAP_DEPTH_MAX = 3            # sitemap index 递归层数上限
SITEMAP_CHILD_CAP = 100          # 单个 index 的子 sitemap 上限
SITEMAP_LOC_CAP = 50_000         # loc 总量护栏
SITEMAP_CLOSES_CRAWL = 50        # ≥50 条 loc 关闭爬虫兜底(ci-gates §四 unlighthouse 口径)
# 口径核对(B56,2026-10-21):unlighthouse 文档 URL Discovery 页写「over 50 paths」会关爬虫,
# 但源码 packages/core/src/discovery/routes.ts 是 `sitemapUrls.length >= 50`(main 分支)。
# 行为以源码为准,保持 ≥50;文档与源码的差异记在这里,不改阈值。
DEFAULT_MAX_PAGES = 500
HARD_MAX_PAGES = 5_000           # --max 上限(超出警告+截断,建议采样)
DEFAULT_DELAY = 1.0
COMMON_SUBS = ("www", "m", "blog", "docs", "shop", "support", "api", "dev", "staging")
CT_PROBE_CAP = 30                # crt.sh 候选逐个 DNS+200 验收的数目上限
SUB_PROBE_BUDGET_S = 30           # 常见子域探测总预算(秒);超时剩余跳过
EXTERNAL_SAMPLE = 10             # --check-external 抽样域数
EXTERNAL_TOP = 50                # external_domains 聚合表保留 Top N
EXTERNAL_URL_SAMPLE = 50         # --check-external 外链 URL 3xx 抽检个数(按引用页数取前 N)
# ---- Ahrefs Site Audit 补项(2026-11-06,RQ-229 例 11):阈值出处见各行 ----
HTML_LIMIT = 2 * 1024 * 1024     # Oversized HTML (>2MB);Googlebot「crawls the first 2MB of a supported file type」
PAGE_READ_CAP = HTML_LIMIT + 1   # 页面最多读 2MB+1 字节:读满即判超限
SLOW_MS_DEFAULT = 3000           # Slow page:Ahrefs 未公布阈值(帮助文 2570529 只说看 Loading time);本套件口径 3 秒,--slow-ms 可改
IMAGE_MAX_BYTES = 100 * 1024     # Image file size too large:100 KB(Ahrefs Webmaster Tools 应用内说明,二手转录;官方帮助无数字)
HTML_LARGE_BYTES = 300 * 1024    # Ahrefs「HTML file size too large」:博客写 250-300KB 起,取上沿
CSS_MAX_BYTES = 15 * 1024        # CSS file size too large:「CSS files that are larger than 15 kB」(help.ahrefs.com/en/articles/2760432)
RESOURCE_CHECK_CAP = 300         # --check-resources 最多查多少个资源 URL(按引用页数取前 N)
EXTRA_PROBE_CAP = 200            # canonical / hreflang 指向但没抓到的 URL,最多补抓多少个
NEAR_DUP_JACCARD = 0.9           # 近似重复:5 词 shingle 估算 Jaccard ≥0.9(Ahrefs「exact or very similar」未公布阈值;
                                 # Screaming Frog 近似重复默认 90%)
DUP_MIN_WORDS = 50               # 正文少于 50 词的页不参与重复内容判定(空壳页互相「重复」没有意义)
SKIP_HREF_SCHEMES = ("javascript:", "mailto:", "tel:", "data:", "ftp:")
ANCHOR_MAX_LEN = 80               # R3-5:锚文本截断长度(去空白后)
ANCHOR_MIN_LEN = 2                # R3-5:短于 2 字的锚不落盘(无信号;亦保持 edges 旧快照兼容,anchor 键可缺)


class GuardError(Exception):
    """SSRF 守卫拒绝(非 http(s)/私网/环回/链路本地/保留/组播)。"""


class FetchError(Exception):
    """传输层失败(重试耗尽)。"""


_sleep = time.sleep               # 模块级可打桩(测试零网络/零真实延时)


# ---------------------------------------------------------------------------
# SSRF 守卫(照抄 monitor.py/traffic_funnel.py:仅 http(s)+拒内网,结果按 host 缓存)
# ---------------------------------------------------------------------------

_ssrf_cache = {}
ALLOW_LOCAL = False               # --allow-local:只多放行本机回环(审本地开发站),私网/链路本地照旧拒
LOCAL_HINT = "审本机开发站加 --allow-local(只放行 127.0.0.0/8、::1、localhost)"


def _is_loopback(ip):
    """127.0.0.0/8、::1,以及 IPv4 映射的 ::ffff:127.x。"""
    if ip.is_loopback:
        return True
    mapped = getattr(ip, "ipv4_mapped", None)
    return bool(mapped and mapped.is_loopback)


def dns_resolve(host):
    """DNS 解析(socket.getaddrinfo)→ IP 字符串列表;失败抛 OSError。独立成函数便于打桩。"""
    infos = socket.getaddrinfo(host, None)
    return [i[4][0] for i in infos]


def ssrf_guard(host):
    """仅 http(s) 目标主机 + 拒私网/环回/链路本地/保留/组播;结果按 host 缓存。
    198.18.0.0/15(RFC2544 基准段)豁免:本机 fake-IP 代理(Surge/Clash 等)会把一切域名
    解析到该段,实际连接经代理出网,TLS 验证仍生效;SEO_CRAWL_STRICT_SSRF=1 恢复全拒。"""
    if not host:
        raise GuardError("empty host")
    key = (host, ALLOW_LOCAL)
    if key in _ssrf_cache:
        return
    try:
        ips = dns_resolve(host)
    except OSError as e:
        raise GuardError("DNS 解析失败 %s: %s" % (host, e))
    strict = bool(os.environ.get("SEO_CRAWL_STRICT_SSRF"))
    for raw in ips:
        try:
            ip = ipaddress.ip_address(str(raw).split("%", 1)[0])
        except ValueError:
            continue
        if ip in ipaddress.ip_network("198.18.0.0/15"):
            if not strict:
                continue
            raise GuardError("SSRF guard: 非公网地址 %s(strict 模式拒 fake-IP 段)" % ip)
        if _is_loopback(ip):
            if ALLOW_LOCAL:
                continue
            raise GuardError("SSRF guard: 本机回环地址 %s;%s" % (ip, LOCAL_HINT))
        if ip.is_private or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise GuardError("SSRF guard: 非公网地址 %s" % ip)
    _ssrf_cache[key] = True


def _redact(u):
    """日志脱敏:保留 scheme+host,路径/查询(常含 token)打码。"""
    return re.sub(r"^(https?://[^/\s]+).*$", r"\1/[REDACTED]", str(u))


# ---------------------------------------------------------------------------
# URL 归一
# ---------------------------------------------------------------------------

# 国家码顶级域下常见的二级注册后缀(co.jp、co.kr、or.kr、com.au、co.uk……)。
# 不带它时 www.yna.co.kr 会被归成 "co.kr",整个 .co.kr 都被当成自家子域(2026-10-24 韩国实测)。
_CC_SECOND_LEVEL = {"co", "or", "ne", "ac", "go", "gr", "ed", "lg", "re", "pe", "hs", "ms",
                    "com", "net", "org", "edu", "gov", "mil", "ltd", "plc", "sch", "nhs",
                    "gob", "gouv", "nom", "asso", "biz", "info"}


def registrable(host):
    """registrable domain 近似:取末两段;国家码顶级域(两字母)前是常见二级后缀时取末三段。
    不是完整的公共后缀表,覆盖 co.jp / co.kr / co.uk / com.au / com.br 这类常见情形。"""
    h = (host or "").lower().rstrip(".")
    if not h:
        return ""
    try:                                   # IP 字面量(本机开发站 127.0.0.1 等)没有「末两段」可言
        ipaddress.ip_address(h.strip("[]"))
        return h
    except ValueError:
        pass
    if h == "localhost" or h.endswith(".localhost"):
        return h
    labels = h.split(".")
    if len(labels) <= 2:
        return h
    if len(labels[-1]) == 2 and labels[-2] in _CC_SECOND_LEVEL:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def sample_children(children, k):
    """子 sitemap 超过 k 个时按位置均匀抽 k 个,首尾都在(与 sitemap_audit 同口径)。index 常按
    时间升序(spiegel.de 从 1947 年排到当月),只取前 k 个会只抓到最旧的归档。"""
    n = len(children)
    if k <= 0:
        return []
    if n <= k:
        return list(children)
    if k == 1:
        return [children[-1]]
    idx = sorted({round(i * (n - 1) / (k - 1)) for i in range(k)})
    return [children[i] for i in idx]


def normalize_url(u, base=None, strip_params=False):
    """归一:补 base/去 fragment/尾斜杠原样保留/参数默认保留
    (--strip_params 可开)/路径大小写不合并/scheme+host 小写/去默认端口。
    非 http(s) 或缺 host → None(调用方丢弃)。"""
    try:
        u = (u or "").strip()
        if base and not urllib.parse.urlsplit(u).scheme:
            u = urllib.parse.urljoin(base, u)
        p = urllib.parse.urlsplit(u)
        if p.scheme.lower() not in ("http", "https") or not p.netloc:
            return None
        scheme = p.scheme.lower()
        host = (p.hostname or "").lower()
        if not host:
            return None
        try:
            port = p.port
        except ValueError:
            return None
        netloc = host if (port is None or (scheme == "https" and port == 443)
                          or (scheme == "http" and port == 80)) else "%s:%d" % (host, port)
        # 非 ASCII 路径/参数(如 /tag/设计)按 UTF-8 百分号编码;已有的 %XX 保留。
        # 不转码时 http_fetch 抛 UnicodeEncodeError,不在重试捕获范围里,会让整次爬取作废。
        # 尾斜杠原样保留:/a 和 /a/ 是两个 URL(多数站一个 301 到另一个)。11-05 前去掉尾斜杠,
        # 链接都带斜杠的站(WordPress、nginx 目录)每页先吃一次 301,「重定向目标没有直接内链」全是误报。
        path = urllib.parse.quote(p.path or "/", safe="/%:@!$&'()*+,;=-._~")
        query = "" if strip_params else urllib.parse.quote(p.query, safe="=&%:@!$'()*+,;/?-._~")
        return urllib.parse.urlunsplit((scheme, netloc, path, query, ""))
    except ValueError:
        return None


def _looks_html(text):
    """正文开头是 HTML 文档(<!doctype html>/<html>/<head>/<body>)。robots.txt、sitemap 这类
    文本文件 200 却回页面壳时用(SPA 对任意路径回 200,sspai 2026-11-05 实测)。"""
    return bool(re.match(r"\s*(?:\ufeff)?\s*<(?:!doctype\s+html|html[\s>]|head[\s>]|body[\s>])",
                         text[:2048] or "", re.I))


def _redirect_kind(src, dst):
    """外链重定向分类:同站换协议/加去 www/尾斜杠 → 低优先;跳到别的站或别的路径 → 要人看
    (Ahrefs 301 文:「ignore things like HTTP to HTTPS redirects ... Look for redirects to different
    sites or pages」)。"""
    a, b = urllib.parse.urlsplit(src), urllib.parse.urlsplit(dst)
    ha = (a.hostname or "").lower()
    hb = (b.hostname or "").lower()
    strip = lambda h: h[4:] if h.startswith("www.") else h
    if strip(ha) != strip(hb):
        return "跳到别的站"
    if (a.path or "/").rstrip("/") != (b.path or "/").rstrip("/") or a.query != b.query:
        return "跳到别的路径"
    return "协议/www/尾斜杠规范化"


def _top_domains(counter, n):
    """外链域聚合 Top N:计数降序、同数按域名字典序——输出确定性
    (most_common 平局走 heapq,顺序随 set 迭代序漂移,受进程间 hash 随机影响)。"""
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:n]


def host_of(url):
    try:
        return (urllib.parse.urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


# ---------------------------------------------------------------------------
# HTTP(手动跟随重定向以记链 + 逐跳 SSRF 复查;传输层失败由 robust_fetch 重试)
# ---------------------------------------------------------------------------

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """禁用自动跟随重定向:链由 http_fetch 手动走,每一跳都过 SSRF 复查。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _header(headers, name):
    if not headers:
        return None
    try:
        v = headers.get(name)
        if v is None and isinstance(headers, dict):     # 普通 dict(桩、缓存)按大小写无关再找一次
            low = name.lower()
            v = next((val for k, val in headers.items() if str(k).lower() == low), None)
        return v
    except Exception:
        return None


def check_redirect(cur, nxt):
    """重定向逐跳 SSRF 复查(monitor.py P0 同款:urlopen 自动跟 302 时最终 host
    从不复查,站方可控的 robots.txt sitemap 指令可 302 到 169.254.169.254 穿墙)。"""
    p = urllib.parse.urlsplit(nxt)
    if p.scheme.lower() not in ("http", "https"):
        raise GuardError("重定向到非 http(s) 被拒: %s" % _redact(nxt))
    ssrf_guard(p.hostname)


def _decode(blob, enc, cap):
    """Content-Encoding gzip/deflate 解压(最多解出 cap 字节,防压缩炸弹);其余原样返回。"""
    enc = (enc or "").strip().lower()
    try:
        if enc in ("gzip", "x-gzip"):
            return zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(blob, cap)
        if enc == "deflate":
            try:
                return zlib.decompressobj().decompress(blob, cap)
            except zlib.error:
                return zlib.decompressobj(-zlib.MAX_WBITS).decompress(blob, cap)
    except zlib.error:
        return blob
    return blob


def _single(url, method, timeout):
    """单次请求(不跟随重定向);4xx/5xx 以 (status, headers, body) 返回,不抛。"""
    status, headers, body, _meta = _single_timed(url, method, timeout)
    return status, headers, body


def _single_timed(url, method, timeout):
    """同 _single,另返回 meta{ttfb_ms, load_ms, raw_bytes, encoding}(慢页、没压缩判定用)。"""
    p = urllib.parse.urlsplit(url)
    if p.scheme.lower() not in ("http", "https"):
        raise GuardError("仅允许 http(s): %s" % _redact(url))
    ssrf_guard(p.hostname)
    req = urllib.request.Request(url, method=method, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        # 只报 gzip/deflate(stdlib 解不了 br):这样「没压缩」才是服务器没压(Ahrefs Not compressed)
        "Accept-Encoding": "gzip, deflate",
    })
    # sitemap 可以远大于页面上限(spiegel.de 的 index 2.25MB),按 2MB 截断会让 XML 解析失败
    cap = SITEMAP_MAX_BYTES if p.path.lower().endswith(SITEMAP_EXT) else PAGE_READ_CAP
    t0 = time.monotonic()
    try:
        with _OPENER.open(req, timeout=timeout) as r:
            t1 = time.monotonic()
            raw = r.read(cap)
            t2 = time.monotonic()
            enc = _header(r.headers, "content-encoding")
            meta = {"ttfb_ms": round((t1 - t0) * 1000), "load_ms": round((t2 - t0) * 1000),
                    "raw_bytes": len(raw), "encoding": (enc or "").strip().lower() or None}
            return int(r.status), r.headers, _decode(raw, enc, cap), meta
    except urllib.error.HTTPError as e:
        try:
            body = e.read(MAX_BYTES)
        except Exception:
            body = b""
        enc = _header(getattr(e, "headers", None), "content-encoding")
        return int(e.code), getattr(e, "headers", None), _decode(body, enc, MAX_BYTES), {
            "ttfb_ms": round((time.monotonic() - t0) * 1000), "load_ms": round((time.monotonic() - t0) * 1000),
            "raw_bytes": len(body), "encoding": (enc or "").strip().lower() or None}
    # URLError/OSError/Timeout 向上抛给 robust_fetch 重试


def http_fetch(url, timeout=10.0, method="GET"):
    """GET/HEAD 并手动跟随重定向(≤10 跳,逐跳 SSRF 复查)。
    返回 {status, final_url, chain:[{status,location}], headers, body, body_bytes}。"""
    chain, cur = [], url
    status, headers, blob, meta = 200, None, b"", {}
    for _ in range(REDIRECT_HOPS_MAX + 1):
        status, headers, blob, meta = _single_timed(cur, method, timeout)
        if not (300 <= status < 400):
            break
        loc = _header(headers, "location")
        if not loc:
            break
        nxt = urllib.parse.urljoin(cur, loc)
        check_redirect(cur, nxt)          # 每一跳都复查,包括最后一跳
        chain.append({"status": status, "location": nxt})
        cur = nxt
    return {"status": status, "final_url": cur, "chain": chain, "headers": headers,
            "body": blob.decode("utf-8", "replace"), "body_bytes": blob, "meta": meta}


def _retry_after(headers):
    """Retry-After 秒数(只认整数秒,上限 60);没有或是日期格式 → None。"""
    try:
        v = (headers or {}).get("Retry-After") or (headers or {}).get("retry-after")
        return min(float(int(str(v).strip())), 60.0) if v is not None else None
    except (ValueError, TypeError, AttributeError):
        return None


def robust_fetch(url, timeout=10.0, method="GET", retries=RETRIES):
    """传输层失败(URLError/OSError/超时)重试 2 次带退避;SSRF 拒绝不重试直接抛;
    4xx/5xx 是确定性响应,由 http_fetch 正常返回、不进重试。耗尽抛 FetchError。"""
    last = None
    for attempt in range(retries + 1):
        try:
            return http_fetch(url, timeout=timeout, method=method)
        except GuardError:
            raise
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            last = e
            if attempt < retries:
                _sleep(0.5 * (attempt + 1))
    raise FetchError("抓取失败 %s: %s" % (_redact(url), last))


# ---------------------------------------------------------------------------
# robots.txt(RFC 9309 简化解析,思路借鉴 robots_posture.py,不 import)
# ---------------------------------------------------------------------------

def parse_robots(txt):
    """返回 {groups, sitemaps, crawl_delay} 或 None(txt 为空)。
    BOM 剥离/500KB 截断/注释剥离/连续 User-agent 行合并同组;groups 键为小写 token,
    值 {"allow":[], "disallow":[], "crawl_delay":float|None};crawl_delay 取 * 组。"""
    if txt.startswith("\ufeff"):
        txt = txt[1:]
    truncated = len(txt) > ROBOTS_MAX_BYTES
    if truncated:
        txt = txt[:ROBOTS_MAX_BYTES]
    groups, sitemaps = {}, []
    cur, last_was_ua = [], False
    for line in txt.splitlines():
        s = line.split("#", 1)[0].strip()
        if not s or ":" not in s:
            continue
        k, _, v = s.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "user-agent":
            if not last_was_ua:
                cur = []
            tok = v or "*"
            cur.append(tok)
            groups.setdefault(tok.lower(), {"allow": [], "disallow": [], "crawl_delay": None})
            last_was_ua = True
        elif k in ("allow", "disallow") and cur:
            for t in cur:
                groups.setdefault(t.lower(), {"allow": [], "disallow": [], "crawl_delay": None})[k].append(v)
            last_was_ua = False
        elif k == "crawl-delay" and cur:
            for t in cur:
                g = groups.setdefault(t.lower(), {"allow": [], "disallow": [], "crawl_delay": None})
                if g["crawl_delay"] is None:
                    try:
                        g["crawl_delay"] = float(v)
                    except ValueError:
                        pass
            last_was_ua = False
        elif k == "sitemap" and v:
            sitemaps.append(v)
            last_was_ua = False
        elif k:
            last_was_ua = False
    if not groups and not sitemaps:
        return None
    return {"groups": groups, "sitemaps": sitemaps,
            "crawl_delay": groups.get("*", {}).get("crawl_delay"), "truncated": truncated}


_ROBOTS_SAFE = "/?=&*$%:@!'()+,;-._~"


def robots_rule_match(rule, path):
    """RFC 9309 §2.2.2:`*` 匹配任意字符序列,结尾 `$` 锚定路径结尾,区分大小写;
    规则和路径都先百分号编码,两边口径一致。"""
    rule = urllib.parse.quote(rule, safe=_ROBOTS_SAFE)
    path = urllib.parse.quote(path, safe=_ROBOTS_SAFE)
    anchored = rule.endswith("$")
    body = rule[:-1] if anchored else rule
    rx = "".join(".*" if c == "*" else re.escape(c) for c in body) + ("$" if anchored else "")
    return re.match(rx, path) is not None


def robots_allows(doc, url):
    """最长匹配判定(自 token 组优先,回退 * 组;同长 Allow 平局胜出;支持 `*`/`$`,
    区分大小写;空 Disallow 值=允许一切(RFC 9309);无匹配规则/无组默认放行)。"""
    if not doc or not doc["groups"]:
        return True
    g = doc["groups"].get(UA_TOKEN) or doc["groups"].get("*")
    if not g:
        return True
    pu = urllib.parse.urlsplit(url)
    path = (pu.path or "/") + (("?" + pu.query) if pu.query else "")
    best_len, allowed = -1, True
    for kind in ("allow", "disallow"):
        for rule in g.get(kind, []):
            if not rule:                      # 空规则是无操作(RFC 9309),不参与匹配
                continue
            if robots_rule_match(rule, path):
                n = len(rule)
                if n > best_len or (n == best_len and kind == "allow"):
                    best_len, allowed = n, kind == "allow"
    return allowed


# ---------------------------------------------------------------------------
# sitemap 解析(惯例借鉴 sitemap_audit.py:命名空间容错 + gzip 魔数)
# ---------------------------------------------------------------------------

def _ln(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def parse_text_sitemap(blob):
    """文本 sitemap:一行一个完整 URL(sitemaps.org「Text file」一节)。11-05 第三轮留出站 oschina:
    robots 声明的 sitemap.txt 被报成「XML 解析失败」。以 < 开头的不算;非空行过半是 http(s) URL 才认。"""
    try:
        text = blob.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None
    if text.lstrip().startswith("<"):
        return None
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    urls = [x for x in lines if re.match(r"^https?://\S+$", x, re.I)]
    if not urls or len(urls) * 2 < len(lines):
        return None
    return urls


def parse_sitemap_bytes(blob):
    """sitemap 字节流 → (kind, [{loc,lastmod}], [child_sitemap_url]);解析失败抛 ValueError。"""
    try:
        root = ET.fromstring(blob)
    except ET.ParseError as e:
        urls = parse_text_sitemap(blob)
        if urls is None:
            raise ValueError("XML 解析失败: %s" % e)
        return "urlset", urls, []
    kind = _ln(root.tag)
    if kind not in ("urlset", "sitemapindex"):
        return "unknown", [], []
    urls, children = [], []
    for node in root.iter():
        t = _ln(node.tag)
        if t == "url":
            loc = ""
            for c in node:
                if _ln(c.tag) == "loc" and c.text and c.text.strip():
                    loc = c.text.strip()
            if loc:
                urls.append(loc)
        elif t == "sitemap":
            for c in node:
                if _ln(c.tag) == "loc" and c.text and c.text.strip():
                    children.append(c.text.strip())
    return kind, urls, children


# ---------------------------------------------------------------------------
# 页面解析(title / canonical / <a href>)
# ---------------------------------------------------------------------------

class PageParser(HTMLParser):
    """一次解析拿全站审计要的页面信号:title/canonical/<a href>(带 rel=nofollow)、robots meta、description、
    H1、html lang、hreflang、og:url、meta refresh、图片/JS/CSS 资源、正文文本(重复内容判定用)。"""
    TEXT_SKIP = ("script", "style", "noscript", "template", "svg")

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonical = None
        self.hrefs = []
        self.anchors = []             # R3-5:与 hrefs 平行——每个 <a> 的锚文本(去空白截 80 字)
        self.rel_nofollow = []        # 与 hrefs 平行——<a rel> 里有 nofollow
        self._in_title = False
        self._title_buf = []
        self._a_buf = None            # 当前 <a> 的文本缓冲(None=不在带 href 的 <a> 内)
        self.title_count = 0
        self.robots_meta = []         # name=robots / googlebot 的 content
        self.descriptions = []
        self.h1s, self._h1_buf = [], None
        self.lang = None
        self.hreflangs = []           # [(code, href)]
        self.og_url = None
        self.refresh = None
        self.resources = []           # [(type, url)] type ∈ image/js/css
        self.text, self._text_len, self._skip = [], 0, 0
        self._svg = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v if v is not None else "") for k, v in attrs}
        if tag in self.TEXT_SKIP:
            self._skip += 1
        if tag == "svg":
            self._svg += 1
        if tag == "html" and self.lang is None and "lang" in a:
            self.lang = a["lang"].strip()
        if tag == "title" and not self._svg:
            self._in_title = True
            self.title_count += 1
        elif tag == "link":
            rel = (a.get("rel") or "").lower().split()
            if "canonical" in rel:
                if a.get("href") and not self.canonical:
                    self.canonical = a["href"]
            if "alternate" in rel and a.get("hreflang") and a.get("href"):
                self.hreflangs.append((a["hreflang"].strip(), a["href"].strip()))
            if "stylesheet" in rel and a.get("href"):
                self.resources.append(("css", a["href"].strip()))
        elif tag == "meta":
            nm = (a.get("name") or a.get("property") or "").strip().lower()
            if nm in ("robots", "googlebot"):
                self.robots_meta.append(a.get("content") or "")
            elif nm == "description":
                self.descriptions.append((a.get("content") or "").strip())
            elif nm == "og:url":
                self.og_url = (a.get("content") or "").strip()
            if (a.get("http-equiv") or "").strip().lower() == "refresh":
                self.refresh = a.get("content") or ""
        elif tag == "img" and a.get("src"):
            self.resources.append(("image", a["src"].strip()))
        elif tag == "script" and a.get("src"):
            self.resources.append(("js", a["src"].strip()))
        elif tag == "h1":
            self._h1_buf = []
        elif tag == "a":
            h = a.get("href")
            if h:
                self.hrefs.append(h)
                self.anchors.append("")
                self.rel_nofollow.append("nofollow" in (a.get("rel") or "").lower().split())
                self._a_buf = []      # R3-5:嵌套标签(<a><b>文</b></a>)的文本也计入

    def handle_endtag(self, tag):
        if tag in self.TEXT_SKIP and self._skip:
            self._skip -= 1
        if tag == "svg" and self._svg:
            self._svg -= 1
        if tag == "title":
            self._in_title = False
        elif tag == "h1" and self._h1_buf is not None:
            self.h1s.append(" ".join("".join(self._h1_buf).split()))
            self._h1_buf = None
        elif tag == "a" and self._a_buf is not None:
            self.anchors[-1] = " ".join("".join(self._a_buf).split())[:ANCHOR_MAX_LEN]
            self._a_buf = None

    def handle_data(self, d):
        if self._in_title:
            self._title_buf.append(d)
            return
        if self._a_buf is not None:
            self._a_buf.append(d)
        if self._h1_buf is not None:
            self._h1_buf.append(d)
        if not self._skip and self._text_len < 300_000:
            self.text.append(d)
            self._text_len += len(d)

    @property
    def title(self):
        return " ".join("".join(self._title_buf).split()) or None


def parse_page(body, base):
    """完整解析(给 fetch_page 用);坏 HTML 不抛。"""
    p = PageParser()
    try:
        p.feed(body[:PAGE_READ_CAP])
    except Exception:
        pass
    return p


def extract_links(body, base):
    """返回 (title, canonical_abs, [(href_abs_norm...)], [anchor...])——link 归一/过滤在调用方;
    anchors 与 hrefs 等长平行(R3-5,无文本/未闭合时为空串)。"""
    p = parse_page(body, base)
    canonical = None
    if p.canonical:
        canonical = normalize_url(p.canonical, base=base)
    return p.title, canonical, p.hrefs, p.anchors


# ---------------------------------------------------------------------------
# 页面信号小工具(Ahrefs 补项)
# ---------------------------------------------------------------------------

def robots_names(*values):
    """robots 指令串 → 指令名集合(小写;逗号/空白分隔;max-snippet:20 → max-snippet)。"""
    out = set()
    for v in values:
        for part in re.split(r"[,\s]+", re.sub(r"\s*:\s*", ":", v or "")):
            if part.strip():
                out.add(part.strip().lower().split(":")[0])
    return out


def header_robots(value):
    """X-Robots-Tag → 对 Google 生效的指令名集合(「bingbot: noindex」只对 Bing 生效,不算)。"""
    m = re.match(r"\s*([a-z][\w-]*)\s*:\s*(.+)$", value or "", re.I)
    if m and m.group(1).lower() not in ("max-snippet", "max-image-preview", "max-video-preview",
                                        "unavailable_after"):
        return robots_names(m.group(2)) if m.group(1).lower() == "googlebot" else set()
    return robots_names(value)


def refresh_target(content, base):
    m = re.search(r"url\s*=\s*['\"]?([^'\";]+)", content or "", re.I)
    if not m:
        return None
    tgt = urllib.parse.urljoin(base, m.group(1).strip()).split("#")[0]
    return tgt if tgt != base.split("#")[0] else None


def lang_primary(code):
    return (code or "").strip().replace("_", "-").split("-")[0].lower()


_TOKEN_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]|[^\W_]+", re.U)


# ---- 软 404(soft 404)----
# Google Search Central「A soft 404 error is when a URL that returns a page telling the user that the page does not
# exist and also a 200 (success) status code. In some cases, it might be a page with no main content or empty page.」
# https://developers.google.com/search/docs/crawling-indexing/troubleshoot-crawling-errors#soft-404-errors(2026-11-06 读取)
# 判法照 Screaming Frog「Soft 404 Pages」:「identified by looking for common error text used on pages, such as 'Page Not
# Found', or '404 Page Can't Be Found'」https://www.screamingfrog.co.uk/seo-spider/issues/content/soft-404-pages/
# 本脚本分两档,都只看 2xx、可索引(非 noindex)的 HTML 页:
#   ① title 或 H1 的某一段(按 | – — · : » 、「 - 」和句末 . ! 。切开)整段就是报错语(「How to fix 404 errors」这类文章标题不算);
#   ② 正文很短(<SOFT404_MAX_WORDS 词)且正文里有「页面找不到 / 不存在」这类专指页面的报错句。
_S404_FULL = re.compile(r"""^(?:
    (?:error\s*)?404(?:\s*error)?(?:\s*(?:page|-|:)?\s*(?:page\s+)?not\s+found)?
  | (?:error\s*)?(?:404\s*[-:]?\s*)?(?:page|file|url|content|product|article)?\s*not\s+found
  | (?:the\s+)?(?:page|url|product|article)\s+(?:you\s+requested\s+)?(?:does\s*n[o'\u2019]?t|does\s+not|no\s+longer)\s+exists?
  | (?:404\s*[-:]?\s*)?(?:the\s+)?page\s+(?:can(?:no|'|\u2019)?t|could\s*n[o'\u2019]?t|could\s+not)\s+be\s+found
  | (?:oops|sorry|uh[\s-]*oh)?[\s,.!]*(?:we\s+)?(?:can(?:no|'|\u2019)?t|could\s*n[o'\u2019]?t|could\s+not)\s+find\s+(?:that|this|the|your)\s+page
  | page\s+(?:unavailable|missing|gone)
  | 页面不存在|页面未找到|找不到(?:该|此|您要的|你要的)?页面|網頁不存在|頁面不存在|找不到(?:該|此)?網頁|404\s*(?:页面|頁面)
  | ページが見つかりません|お探しのページは見つかりませんでした|페이지를\s*찾을\s*수\s*없습니다
  | p[aá]gina\s+no\s+encontrada|p[aá]gina\s+n[aã]o\s+encontrada|seite\s+nicht\s+gefunden|page\s+introuvable|pagina\s+non\s+trovata
)$""", re.I | re.X)
_S404_BODY = re.compile(r"""(?:
    \bpage\s+not\s+found\b
  | \bpage\s+(?:you\s+(?:were\s+|are\s+)?(?:looking|searching)\s+for\s+|you\s+requested\s+)?(?:does\s*n[o'\u2019]?t|does\s+not|no\s+longer)\s+exists?\b
  | \b(?:can(?:no|'|\u2019)?t|could\s*n[o'\u2019]?t|could\s+not)\s+find\s+(?:that|this|the)\s+page\b
  | \bpage\s+(?:you\s+(?:were\s+|are\s+)?(?:looking|searching)\s+for\s+)?(?:can(?:no|'|\u2019)?t|could\s*n[o'\u2019]?t|could\s+not)\s+be\s+found\b
  | 页面不存在|页面未找到|找不到(?:该|此|您要的|你要的)?页面|網頁不存在|頁面不存在|ページが見つかりません|페이지를\s*찾을\s*수\s*없습니다
  | p[aá]gina\s+no\s+encontrada|p[aá]gina\s+n[aã]o\s+encontrada|seite\s+nicht\s+gefunden|page\s+introuvable|pagina\s+non\s+trovata
)""", re.I | re.X)
_S404_SPLIT = re.compile(r"\s*(?:[|\u2013\u2014\u00b7:\u00bb]|\s-\s|[.!。](?=\s|$))\s*")
SOFT404_MAX_WORDS = 300          # 正文档的「很短」:带导航和页脚的典型报错页在 100-250 词;本套件口径,Google/SF 都没给数字


def soft404_evidence(title, h1s, text):
    """返回软 404 的证据(「title: …」「H1: …」「正文: …」)或 None。只看文字,状态码和 noindex 由调用方判。"""
    def full(seg):
        seg = re.sub(r"^[\W_]+|[\W_]+$", "", seg or "", flags=re.U)
        return bool(seg) and bool(_S404_FULL.match(seg))
    for seg in _S404_SPLIT.split(title or ""):
        if full(seg):
            return "title: %s" % title[:120]
    for h in h1s or ():
        if any(full(seg) for seg in _S404_SPLIT.split(h)):
            return "H1: %s" % h[:120]
    toks = _TOKEN_RE.findall((text or "").lower())
    if len(toks) < SOFT404_MAX_WORDS:
        m = _S404_BODY.search(" ".join((text or "").split()))
        if m:
            return "正文(%d 词): …%s…" % (len(toks), m.group(0)[:80])
    return None


def text_sketch(text, k=64):
    """正文 → (词数, 全文哈希, bottom-k 草图)。5 词 shingle,crc32 哈希,保留最小 k 个。"""
    toks = _TOKEN_RE.findall((text or "").lower())
    if len(toks) < DUP_MIN_WORDS:
        return len(toks), None, None
    full = zlib.crc32(" ".join(toks).encode("utf-8"))
    sh = {zlib.crc32(" ".join(toks[i:i + 5]).encode("utf-8")) for i in range(max(1, len(toks) - 4))}
    return len(toks), full, tuple(sorted(sh)[:k])


def sketch_jaccard(a, b, k=64):
    """bottom-k 估算 Jaccard:并集最小 k 个里,两边都有的占比。"""
    sa, sb = set(a), set(b)
    union = sorted(sa | sb)[:k]
    return sum(1 for h in union if h in sa and h in sb) / len(union) if union else 0.0


# ---------------------------------------------------------------------------
# 爬取器主体
# ---------------------------------------------------------------------------

class Crawler:
    def __init__(self, ns):
        self.ns = ns
        site = ns.site.strip()
        if "://" not in site:
            site = "https://" + site
        seed = normalize_url(site)
        if not seed:
            raise ValueError("无法解析站点 URL: %s" % ns.site)
        self.seed = seed
        self.seed_host = host_of(seed)
        self.reg = registrable(self.seed_host)
        self.scheme = urllib.parse.urlsplit(seed).scheme
        # --max 上限护栏:超出打警告建议采样并截断到 5000
        self.max_pages = ns.max_pages
        self.warnings = []
        if self.max_pages > HARD_MAX_PAGES:
            self.warnings.append("--max %d 超过上限 %d,已截断;大站建议采样"
                                 "(ci-gates §四 路由模板归一,每组≤8 样本∪手工钱页)"
                                 % (self.max_pages, HARD_MAX_PAGES))
            self.max_pages = HARD_MAX_PAGES
        # 运行态
        self.pages = {}                 # norm_url -> page record(插入序 = 发现序)
        self.order = []
        self.edges = set()              # (src, dst) 内链边(同源同目标去重)
        self.edge_anchor = {}           # (src, dst) -> 锚文本(R3-5;同边多锚首见优先)
        self.external = Counter()       # 外链 registrable domain -> 次数(页内去重后累计)
        self.accepted_subs = set()      # 已收子域(同 registrable、≠种子主机)
        self.counts = {"robots": 0, "sitemap": 0, "crawl": 0}   # 子域根页另记 "subdomain"(有才出现)
        self.crawl_fallback = False     # 链④ 是否开着(写进 discovery,摘要按它说话)
        self.links_followed = False     # 站内链接指向的 URL 是否请求(sitemap ≥50 时也请求,--sitemap-only 关)
        self.robots_status = {}         # origin -> HTTP 状态 / "html" / "error"(子域 robots 检查用)
        self.redirect_hops = {}         # url -> [(from, to, status)](HTTPS→HTTP 重定向检查用)
        self.external_urls = Counter()  # 外链完整 URL -> 引用页数(外链 3xx 抽检用)
        self.external_src = {}          # 外链 URL -> 首个引用页
        self.served = {}                # url -> 实际返回内容的最终 URL(判断页面协议)
        self.mode = None
        self.queue = deque()
        self.seen = set()
        self.skipped_robots = []
        self.errors = 0                 # 错误页:status None(传输失败)或 ≥400
        self.redirects = 0
        self.req_count = 0
        self.ok_origins = set()          # 页面返回过 2xx 的源站(之后再给 403/503 才可能是限流)
        self.rate_limited = 0            # 退避重试后仍像限流的页数(不算错误页,未判定)
        self.truncated = False
        self._robots_cache = {}
        # Ahrefs 补项状态
        self.edge_follow = {}           # (src, dst) -> 至少一条可跟随链接(无 rel=nofollow 且源页不是 nofollow 页)
        self.edge_nofollow_link = set() # (src, dst) 里有 rel=nofollow 的 <a>(Page has nofollow outgoing internal links)
        self.resources = {}             # 资源 URL -> {"type", "pages": [引用页]}
        self.sketch = {}                # url -> (词数, 全文哈希, bottom-k 草图)
        self.extra = {}                 # canonical/hreflang 指向但没在抓取集里的 URL -> {status, final_url, canonical, ...}
        self.slow_ms = getattr(ns, "slow_ms", None) or SLOW_MS_DEFAULT

    # ---- 基础设施 ----

    @staticmethod
    def _origin(url):
        p = urllib.parse.urlsplit(url)
        return "%s://%s" % (p.scheme, p.netloc)

    def _sleep_polite(self, origin):
        if self.req_count:
            _sleep(self.delay_for(origin))
        # 首个请求不延时

    def _request(self, url, method="GET"):
        origin = self._origin(url)
        self._sleep_polite(origin)
        self.req_count += 1
        r = robust_fetch(url, timeout=self.ns.timeout, method=method)
        if self._looks_rate_limited(origin, r["status"]):
            # 11-05 第二轮留出站 qiita:别的脚本同时压站,本脚本第 9–90 页连着拿 403,1 秒间隔重抓 81 个是 200。
            # 429,或同一源站先给过 2xx 后又给 403/503 → 退避(Retry-After,否则 10 秒)重试一次;仍然如此标「疑似限流」。
            _sleep(_retry_after(r.get("headers")) or max(10.0, 5 * self.delay_for(origin)))
            self.req_count += 1
            r = robust_fetch(url, timeout=self.ns.timeout, method=method)
            if self._looks_rate_limited(origin, r["status"]):
                r["rate_limited"] = True
        return r

    def _looks_rate_limited(self, origin, status):
        return status == 429 or (status in (403, 503) and origin in self.ok_origins)

    def delay_for(self, origin):
        """生效延时 = max(robots * 组 crawl-delay, --delay);--ignore-robots 或
        无 robots 时用 --delay(默认 1.0s)。"""
        d = self.ns.delay
        if not self.ns.ignore_robots:
            doc = self._robots_cache.get(origin)
            if doc and doc.get("crawl_delay") is not None:
                d = max(doc["crawl_delay"], d)
        return d

    def _robots(self, origin):
        """按 origin 缓存 robots.txt 文档;--ignore-robots/抓取失败/非 200 → None(全放行)。"""
        if self.ns.ignore_robots:
            return None
        if origin in self._robots_cache:
            return self._robots_cache[origin]
        doc = None
        try:
            r = self._request(origin + "/robots.txt")
            st = r["status"]
            if st == 200 and _looks_html(r["body"]):
                st = "html"               # 200 却是 HTML 页面:解析不出规则(软 404)
            self.robots_status[origin] = st
            if r["status"] == 200:
                doc = parse_robots(r["body"])
        except FetchError:
            doc = None
            self.robots_status[origin] = "error"
        except GuardError:
            doc = None
            self.robots_status[origin] = "error"
        self._robots_cache[origin] = doc
        return doc

    def allowed(self, url):
        if self.ns.ignore_robots:
            return True
        doc = self._robots(self._origin(url))
        return robots_allows(doc, url)

    def is_internal(self, host):
        h = (host or "").lower()
        if not h:
            return False
        if h == self.seed_host:
            return True
        if self.ns.same_host:
            return False
        return registrable(h) == self.reg

    def consider_host(self, host):
        """子域发现 (a):站点自身 robots/sitemap/内链里出现的同 registrable 子域直接采信。"""
        h = (host or "").lower()
        if self.ns.same_host:
            return
        if h != self.seed_host and registrable(h) == self.reg:
            self.accepted_subs.add(h)

    # ---- 发现链 ----

    def _parse_sitemap(self, url, depth=0):
        """递归解析 sitemap index 嵌套(≤SITEMAP_DEPTH_MAX 层,子表 ≤SITEMAP_CHILD_CAP);
        返回原始 loc 列表(归一/过滤在调用方)。"""
        if depth > SITEMAP_DEPTH_MAX:
            self.warnings.append("sitemap index 嵌套超过 %d 层,停止下钻: %s" % (SITEMAP_DEPTH_MAX, url))
            return []
        try:
            r = self._request(url)
        except FetchError as e:
            self.warnings.append("sitemap 抓取失败: %s" % e)
            return []
        if r["status"] != 200:
            self.warnings.append("sitemap HTTP %s: %s" % (r["status"], url))
            return []
        blob = r["body_bytes"]
        if blob[:2] == b"\x1f\x8b":
            try:
                blob = gzip.decompress(blob)
            except OSError:
                pass
        try:
            kind, urls, children = parse_sitemap_bytes(blob)
        except ValueError as e:
            self.warnings.append("sitemap %s" % e)
            return []
        if kind == "urlset":
            return urls
        if kind == "sitemapindex":
            out = []
            picked = sample_children(children, SITEMAP_CHILD_CAP)
            if len(children) > SITEMAP_CHILD_CAP:
                self.warnings.append("sitemapindex 含 %d 个子表,按位置均匀抽 %d 个(含首尾): %s"
                                     % (len(children), len(picked), url))
            for child in picked:
                out.extend(self._parse_sitemap(urllib.parse.urljoin(url, child), depth + 1))
            return out
        self.warnings.append("根元素非 urlset/sitemapindex: %s" % url)
        return []

    def discover(self):
        """链①→④:确定 mode、填初始队列;返回 (mode, crawl_fallback)。"""
        if self.ns.urls:
            self.mode = "urls"
            urls = []
            with open(self.ns.urls, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    u = normalize_url(line, strip_params=self.ns.strip_params)
                    if u:
                        urls.append(u)
            for u in urls:
                if u not in self.seen:
                    self.seen.add(u)
                    self.queue.append((u, "urls"))
            # 链①给出即关闭 ②③④:robots 仅作礼貌规则(Disallow/crawl-delay),不做发现
            self._robots(self._origin(self.seed))
            self.links_followed = False          # 手工清单:只审给定的 URL
            return self.mode, False

        seed_doc = self._robots(self._origin(self.seed))
        sm_urls = []
        if seed_doc:
            for s in seed_doc["sitemaps"]:
                sm_urls.append(urllib.parse.urljoin(self.seed, s))
                self.consider_host(host_of(sm_urls[-1]))
        self.counts["robots"] = len(sm_urls)
        locs_raw = []
        picked = sample_children(sm_urls, SITEMAP_CHILD_CAP)
        if len(sm_urls) > SITEMAP_CHILD_CAP:
            # 11-05 第三轮留出站 oschina:robots 声明 1,134 条,逐条抓用了 75 分钟;和 index 子表同一上限
            self.warnings.append("robots.txt 声明了 %d 个 sitemap,按位置均匀抽 %d 个(含首尾)"
                                 % (len(sm_urls), len(picked)))
        for su in picked:                       # 链②:robots 的 Sitemap 行
            locs_raw.extend(self._parse_sitemap(su))
        fallback = self._origin(self.seed) + "/sitemap.xml"
        if not sm_urls:                          # 链③:robots 无指令 → 直接 /sitemap.xml
            locs_raw.extend(self._parse_sitemap(fallback))
        elif not locs_raw and fallback not in sm_urls:
            # 声明的全取不到条目(oschina 几乎全 404):退回 /sitemap.xml,不让后面的链接分析只剩首页
            self.warnings.append("robots.txt 声明的 sitemap 没取到任何条目,退回 %s" % fallback)
            locs_raw.extend(self._parse_sitemap(fallback))
        locs, seen_loc = [], set()
        for raw in locs_raw[:SITEMAP_LOC_CAP]:
            u = normalize_url(raw, strip_params=self.ns.strip_params)
            if not u or u in seen_loc:
                continue
            h = host_of(u)
            if not self.is_internal(h):
                continue                          # 跨域 loc(交叉提交)不入内页集
            self.consider_host(h)
            seen_loc.add(u)
            locs.append(u)
        self.counts["sitemap"] = len(locs)
        if locs:
            self.mode = "robots+sitemap" if sm_urls else "sitemap"
        else:
            self.mode = "crawl"
        for u in locs:
            self.seen.add(u)
            self.queue.append((u, "sitemap"))
        if self.mode in ("robots+sitemap", "sitemap") and self.seed not in self.seen:
            # sitemap 模式也先抓首页:首页是站内最大的入链来源,不抓它孤儿判定全是假阳性
            # (2026-10-24 asahi.com 实测:40 篇首页直链的文章全被判孤儿)
            self.seen.add(self.seed)
            self.queue.appendleft((self.seed, "seed"))
        if self.mode == "crawl":                 # 链④:BFS 从首页走
            self.seen.add(self.seed)
            self.queue.append((self.seed, "crawl"))
        # ≥50 条 loc 关闭爬虫兜底,只走 sitemap;<50 则 sitemap ∪ 爬虫补量
        crawl_fallback = self.mode == "crawl" or (
            self.mode in ("robots+sitemap", "sitemap")
            and self.counts["sitemap"] < SITEMAP_CLOSES_CRAWL)
        self.crawl_fallback = crawl_fallback
        self.links_followed = crawl_fallback or not getattr(self.ns, "sitemap_only", False)
        return self.mode, crawl_fallback

    # ---- 子域发现 ----

    def _accept_probed_host(self, host):
        """(b)/(c) 候选验收:DNS 解析成功且根路径 HTTP 200 才收。
        探测请求必须廉价:短超时(≤4s)+零重试——2026-10-11 真实爬取发现解析成功
        但 HTTP 挂起的子域(泛解析)会各吃满 超时×重试+礼貌延时,9 个候选拖垮整轮。"""
        try:
            dns_resolve(host)
        except OSError:
            return False
        url = normalize_url("%s://%s/" % (self.scheme, host))
        try:
            r = robust_fetch(url, timeout=min(self.ns.timeout, 4.0), retries=0)
        except FetchError:
            return False
        return r["status"] == 200

    def discover_subdomains(self):
        """(b) 常见子域 DNS 探测 + (c) --subs ct 走 crt.sh;收下的子域根页入队(source=crawl)。"""
        if self.ns.same_host or self.mode == "urls":
            return
        probed = []
        deadline = time.monotonic() + SUB_PROBE_BUDGET_S   # 探测总预算,防整轮被拖垮
        for s in COMMON_SUBS:                     # (b)
            host = "%s.%s" % (s, self.reg)
            if host == self.seed_host or host in self.accepted_subs:
                continue
            if time.monotonic() > deadline:
                self.warnings.append("子域探测超预算(%ss),剩余候选跳过" % SUB_PROBE_BUDGET_S)
                break
            if self._accept_probed_host(host):
                self.accepted_subs.add(host)
                probed.append(host)
        if "ct" in (self.ns.subs or ""):          # (c)
            probed.extend(self._crtsh_subdomains())
        for host in probed:
            url = normalize_url("%s://%s/" % (self.scheme, host))
            if url and url not in self.seen:
                self.seen.add(url)
                self.queue.append((url, "crawl"))
                # 子域根页单独计数:修前记进 counts["crawl"],摘要把它说成「loc<50 兜底开着」
                # (everyinfra 2769 条 loc、plausible 167 条 loc 都被这样误写,2026-11-05 评分)
                self.counts["subdomain"] = self.counts.get("subdomain", 0) + 1

    def _crtsh_subdomains(self):
        """crt.sh CT 日志子域发现(https://crt.sh/?q=%.{domain}&output=json);失败优雅跳过。"""
        url = "https://crt.sh/?q=%%25.%s&output=json" % self.reg
        try:
            r = self._request(url)
        except FetchError as e:
            self.warnings.append("crt.sh 不可达,CT 子域发现跳过: %s" % e)
            return []
        if r["status"] != 200:
            self.warnings.append("crt.sh HTTP %s,CT 子域发现跳过" % r["status"])
            return []
        try:
            items = json.loads(r["body"])
        except ValueError:
            self.warnings.append("crt.sh 返回非 JSON,CT 子域发现跳过")
            return []
        names = set()
        for item in items if isinstance(items, list) else []:
            for n in re.split(r"[\n\s]+", str(item.get("name_value", ""))):
                n = n.strip().lstrip("*.").lower().rstrip(".")
                if n and n.endswith("." + self.reg) and n != self.reg:
                    names.add(n)
        accepted = []
        for host in sorted(names)[:CT_PROBE_CAP]:
            if host == self.seed_host or host in self.accepted_subs:
                continue
            if self._accept_probed_host(host):
                self.accepted_subs.add(host)
                accepted.append(host)
        return accepted

    # ---- 页面抓取 ----

    def fetch_page(self, url, source):
        """抓单页:状态/重定向链/title/canonical/链接分类与计数;返回 (record, internal_targets)。"""
        rec = {"url": url, "status": None, "title": None, "canonical": None, "depth": None,
               "inlinks": 0, "out_internal": 0, "out_external": 0, "source": source}
        internal_targets, externals = set(), set()
        page_ext_urls = set()
        try:
            r = self._request(url)
        except FetchError as e:
            rec["error"] = str(e)
        except GuardError as e:
            rec["error"] = str(e)
        else:
            rec["status"] = r["status"]
            if 200 <= r["status"] < 300:                 # 只认页面给过 2xx(robots、sitemap 200 不算)
                self.ok_origins.add(self._origin(url))
            if r.get("rate_limited"):
                rec["rate_limited"] = True
                rec["error"] = "疑似限流(HTTP %s,退避重试后仍是),未判定" % r["status"]
            elif r["status"] >= 400:
                rec["error"] = "HTTP %s" % r["status"]
            if r["chain"]:
                self.redirects += 1
                if r["final_url"] != url:
                    rec["final_url"] = r["final_url"]
                hops, prev = [], url
                for h in r["chain"]:
                    hops.append((prev, h["location"], h["status"]))
                    prev = h["location"]
                self.redirect_hops[url] = hops
            self.served[url] = r["final_url"]
            pp = parse_page(r["body"], r["final_url"])
            title, hrefs, anchors = pp.title, pp.hrefs, pp.anchors
            canonical = normalize_url(pp.canonical, base=r["final_url"]) if pp.canonical else None
            rec["title"], rec["canonical"] = title, canonical
            page_nofollow = self._page_signals(rec, r, pp)
            for i, h in enumerate(hrefs):
                hl = h.strip()
                if not hl or hl.startswith("#"):
                    continue
                if hl.lower().startswith(SKIP_HREF_SCHEMES):
                    continue
                absu = normalize_url(urllib.parse.urljoin(r["final_url"], hl),
                                     strip_params=self.ns.strip_params)
                if not absu:
                    continue
                h2 = host_of(absu)
                if self.is_internal(h2):
                    self.consider_host(h2)
                    internal_targets.add(absu)
                    rel_nf = pp.rel_nofollow[i] if i < len(pp.rel_nofollow) else False
                    if rel_nf:
                        self.edge_nofollow_link.add((url, absu))
                    if not rel_nf and not page_nofollow:
                        self.edge_follow[(url, absu)] = True
                    else:
                        self.edge_follow.setdefault((url, absu), False)
                    atext = anchors[i] if i < len(anchors) else ""
                    if len(atext) >= ANCHOR_MIN_LEN:   # R3-5:锚文本配对进边(首见优先)
                        self.edge_anchor.setdefault((url, absu), atext)
                else:
                    if absu not in page_ext_urls:
                        page_ext_urls.add(absu)
                        self.external_urls[absu] += 1
                        self.external_src.setdefault(absu, url)
                    ed = registrable(h2)
                    if ed == self.reg:
                        # --same-host 下跨子域链接记外链:聚合键用完整主机
                        # (否则自家 registrable domain 会冒充"外链域")
                        ed = h2
                    if ed:
                        externals.add(ed)
            rec["out_internal"] = len(internal_targets)
            rec["out_external"] = len(externals)
        if rec.get("rate_limited"):
            self.rate_limited += 1
        elif rec["status"] is None or rec["status"] >= 400:
            self.errors += 1
        for t in internal_targets:
            self.edges.add((url, t))
        for ed in externals:
            self.external[ed] += 1
        self.pages[url] = rec
        self.order.append(url)
        return rec, internal_targets

    def _page_signals(self, rec, r, pp):
        """把 Ahrefs 补项要用的页面信号写进 rec(只写有值的键,旧下游不受影响);返回本页是否 nofollow。"""
        base = r["final_url"]
        meta = r.get("meta") or {}
        hdr = r.get("headers")
        html_names = robots_names(*pp.robots_meta)
        hdr_names = header_robots(_header(hdr, "x-robots-tag") or "")
        ni = lambda n: bool(n & {"noindex", "none"})
        nf = lambda n: bool(n & {"nofollow", "none"})
        if ni(html_names) or ni(hdr_names):
            rec["noindex"] = True
        if nf(html_names) or nf(hdr_names):
            rec["nofollow"] = True
        both = [d for d, f in (("noindex", ni), ("nofollow", nf)) if f(html_names) and f(hdr_names)]
        if both:
            rec["robots_in_html_and_header"] = both
        if pp.title_count > 1:
            rec["title_count"] = pp.title_count
        if pp.descriptions:
            rec["description"] = pp.descriptions[0][:300]
            if len(pp.descriptions) > 1:
                rec["description_count"] = len(pp.descriptions)
        if pp.h1s:
            rec["h1"] = pp.h1s[0][:200]
        if pp.lang is not None:
            rec["lang"] = pp.lang
        if pp.hreflangs:
            rec["hreflang"] = [[c, normalize_url(urllib.parse.urljoin(base, h))] for c, h in pp.hreflangs][:50]
        if pp.og_url:
            rec["og_url"] = pp.og_url
        if pp.refresh is not None:
            tgt = refresh_target(pp.refresh, base)
            if tgt:
                rec["meta_refresh"] = tgt
        size = max(len(r.get("body_bytes") or b""), 0)
        if size:
            rec["bytes"] = size
        if meta.get("load_ms") is not None:
            rec["load_ms"] = meta["load_ms"]
        if meta.get("ttfb_ms") is not None:
            rec["ttfb_ms"] = meta["ttfb_ms"]
        ctype = (_header(hdr, "content-type") or "").lower()
        is_html = (not ctype and _looks_html(r.get("body") or "")) or "html" in ctype
        if is_html:
            rec["html"] = True
            enc = meta.get("encoding") or (_header(hdr, "content-encoding") or "").strip().lower() or None
            if meta and "encoding" in meta or _header(hdr, "content-encoding") is not None:
                rec["encoding"] = enc or "identity"
            scripts = 0
            for typ, src in pp.resources:
                if src.lower().startswith("data:"):
                    continue
                ru = urllib.parse.urljoin(base, src).split("#")[0]
                if not ru.lower().startswith(("http://", "https://")):
                    continue
                scripts += typ == "js"
                slot = self.resources.setdefault(ru, {"type": typ, "pages": []})
                if rec["url"] not in slot["pages"]:
                    slot["pages"].append(rec["url"])
            if scripts:
                rec["scripts"] = scripts
            if 200 <= r["status"] < 300 and not r["chain"]:   # 被重定向的 URL 内容属于目标页,不重复计
                body_text = " ".join(pp.text)
                self.sketch[rec["url"]] = text_sketch(body_text)
                ev = soft404_evidence(pp.title, pp.h1s, body_text)
                if ev:
                    rec["soft404"] = ev
        return bool(rec.get("nofollow"))

    def crawl(self, crawl_fallback):
        """统一抓取循环:初始队列(②③产物/①清单/子域根页)→ 逐页抓取 →
        crawl_fallback 时沿内链续队(链④)。--max 截断记 truncated。
        sitemap ≥50 条(爬虫兜底关闭)时,站内链接指向、sitemap 没列的 URL 仍要请求:排在 sitemap 后面
        (source=link),同受 --max 预算,记状态码和重定向跳数,它们的出链也照样续队。没有这一步,
        链到 404 的站内链接、被链接引用的重定向链、只从分页页链出去的页面都查不到(RQ-229 例 7)。
        --sitemap-only 恢复旧口径(链接只进图,不请求)。"""
        link_q = deque()
        follow_links = self.links_followed
        while (self.queue or link_q) and len(self.pages) < self.max_pages:
            url, source = self.queue.popleft() if self.queue else link_q.popleft()
            if not self.allowed(url):
                self.skipped_robots.append(url)
                continue
            rec, internal_targets = self.fetch_page(url, source)
            if source == "link":
                self.counts["link"] = self.counts.get("link", 0) + 1
            if rec["status"] is None:
                continue                          # 传输失败无链接可走
            if crawl_fallback:
                for tgt in sorted(internal_targets):
                    if tgt not in self.seen:
                        self.seen.add(tgt)
                        self.queue.append((tgt, "crawl"))
                        self.counts["crawl"] += 1
            elif follow_links:
                for tgt in sorted(internal_targets):
                    if tgt not in self.seen:
                        self.seen.add(tgt)
                        link_q.append((tgt, "link"))
        self.truncated = bool(self.queue or link_q)
        if self.queue:
            self.warnings.append("发现 %d+ URL 超过 --max %d,已截断——大站建议采样"
                                 "(ci-gates §四:路由模板归一后每组抽 ≤8 ∪ 手工钱页)"
                                 % (len(self.pages) + len(self.queue) + len(link_q), self.max_pages))
        elif link_q:
            self.warnings.append("sitemap 已抓完,站内链接指向的另外 %d 个 URL 超出 --max %d 没请求:"
                                 "断链、重定向链、孤儿页只覆盖已抓部分,加大 --max 再抓" % (len(link_q), self.max_pages))

    def check_external_domains(self):
        """--check-external:对 Top 外链域抽样 HEAD 根路径(只记状态,不外爬)。"""
        out = []
        for domain, _n in _top_domains(self.external, EXTERNAL_SAMPLE):
            url = normalize_url("%s://%s/" % (self.scheme, domain))
            if not url:
                continue
            try:
                r = self._request(url, method="HEAD")
                out.append({"domain": domain, "status": r["status"]})
            except FetchError as e:
                out.append({"domain": domain, "status": None, "error": str(e)})
        return out

    # ---- Ahrefs 站点审计补项(2026-11-05 RQ-229 第 3 批;判据原文与 URL 见各段注释) ----

    def link_issues(self, inlinks_direct):
        """跨页链接/重定向问题。inlinks_direct: 页面 → 直接指向它的内链数(不经重定向)。
        返回 dict,写进 crawl.json 的 link_issues 节。"""
        out = {}
        # ① Redirected page has no incoming internal links(Ahrefs:「This issue reports pages that
        #    are only linked via a redirect」;只对想排名的可索引页有意义——本脚本不判可索引性,
        #    结果里写明。https://help.ahrefs.com/en/articles/2754350,2026-11-05 读取)
        #    判法:重定向的目标页(站内、最终 200、非首页)没有任何直接内链,只能经重定向到达。
        seed_final = self.served.get(self.seed, self.seed)
        via = {}
        for u in self.order:
            rec = self.pages[u]
            fu = rec.get("final_url")
            if not fu or not self.is_internal(host_of(fu)) or rec.get("status") != 200:
                continue
            if fu in (self.seed, seed_final):
                continue
            via.setdefault(fu, []).append(u)
        rows = []
        for tgt, srcs in via.items():
            if inlinks_direct.get(tgt, 0) == 0:
                rows.append({"target": tgt, "via": sorted(srcs),
                             "links_to_redirects": sum(inlinks_direct.get(x, 0) for x in srcs)})
        out["redirect_target_no_direct_inlinks"] = sorted(rows, key=lambda r: r["target"])
        # ② 协议混用的内链:HTTP 页链到 HTTPS(Ahrefs「HTTP page has internal links to HTTPS」,
        #    官方帮助文无单篇;Ahrefs 首席 Patrick Stox SERP Conf 2024 演讲「Links (Indexable)」
        #    列此项),反向 HTTPS 页链到 HTTP(「This issue reports HTTPS pages linking to HTTP URLs
        #    on your website」https://help.ahrefs.com/en/articles/2614035)。
        #    页面协议按实际返回内容的最终 URL 判(http 页 301 到 https 时,链接出自 https 页)。
        h2s, s2h = {}, {}
        for src, dst in self.edges:
            served = self.served.get(src, src)
            sch_src = urllib.parse.urlsplit(served).scheme
            sch_dst = urllib.parse.urlsplit(dst).scheme
            if sch_src == "http" and sch_dst == "https":
                h2s.setdefault(served, set()).add(dst)
            elif sch_src == "https" and sch_dst == "http":
                s2h.setdefault(served, set()).add(dst)
        out["http_page_links_to_https"] = [{"page": k, "links": sorted(v)[:20], "count": len(v)}
                                           for k, v in sorted(h2s.items())]
        out["https_page_links_to_http"] = [{"page": k, "links": sorted(v)[:20], "count": len(v)}
                                           for k, v in sorted(s2h.items())]
        # ③ HTTPS to HTTP redirect(Ahrefs:「pages on your website on a HTTPS protocol but are now
        #    being redirected to a page with HTTP protocol」https://help.ahrefs.com/en/articles/2442569)
        rows = []
        for u in self.order:
            for frm, to, st in self.redirect_hops.get(u, ()):
                if (urllib.parse.urlsplit(frm).scheme == "https"
                        and urllib.parse.urlsplit(to).scheme == "http"):
                    rows.append({"url": u, "from": frm, "to": to, "status": st})
        out["https_to_http_redirects"] = rows
        return out

    def check_external_redirects(self, limit=EXTERNAL_URL_SAMPLE):
        """--check-external:外链 URL 抽检 3xx(Ahrefs「External 3XX redirect」:站点链出的外部 URL
        跳到了别处;「The URL could have been redirected after you had added a link to it ...
        the link from your website might be pointing elsewhere now」
        https://help.ahrefs.com/en/articles/2724308;External pages 报告的该项见
        https://ahrefs.com/blog/301-redirects/ 第 9 节)。只发 HEAD(405/501 回退 GET),不跟进外站内容。
        取引用页数最多的 limit 个 URL(同数按字典序),输出写明查了几个、共几个。"""
        picked = sorted(self.external_urls.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
        rows = []
        for u, n in picked:
            try:
                r = self._request(u, method="HEAD")
                if r["status"] in (405, 501):
                    r = self._request(u)
            except (FetchError, GuardError) as e:
                rows.append({"url": u, "status": None, "error": str(e), "linked_from": n,
                             "example_source": self.external_src.get(u)})
                continue
            if r["chain"]:
                first = r["chain"][0]
                rows.append({"url": u, "status": first["status"], "location": first["location"],
                             "final_url": r["final_url"], "final_status": r["status"],
                             "kind": _redirect_kind(u, r["final_url"]), "linked_from": n,
                             "example_source": self.external_src.get(u)})
            elif r["status"] >= 400:                    # Ahrefs「External 4XX」;11-05 评审:外链 404 原来直接丢掉
                rows.append({"url": u, "status": r["status"], "broken": True, "linked_from": n,
                             "example_source": self.external_src.get(u)})
        return {"checked": len(picked), "total": len(self.external_urls),
                "redirects": [x for x in rows if x.get("status") is not None and not x.get("broken")],
                "broken": [x for x in rows if x.get("broken")],
                "errors": [x for x in rows if x.get("status") is None]}

    # ---- Ahrefs 站点审计补项(2026-11-06,RQ-229 例 11:脚本实跑覆盖 ≥90%)。判据原文见各段注释 ----

    def probe_extra(self):
        """canonical / hreflang 指向、但不在抓取集里的站内 URL:补抓一次(≤EXTRA_PROBE_CAP),拿状态码、
        是否重定向、它自己的 canonical 与 html lang。Ahrefs 会抓 canonical 目标(Canonical points to 4XX/5XX/
        redirect、Non-canonical page specified as canonical 都要看目标页本身)。"""
        want = []
        for u in self.order:
            rec = self.pages[u]
            if rec.get("status") is None or rec["status"] >= 400 or rec.get("final_url"):
                continue
            c = rec.get("canonical")
            if c and c != u:
                want.append(c)
            want.extend(h for _c, h in rec.get("hreflang", []) if h)
        todo, seen = [], set()
        for w in want:
            if w in self.pages or w in seen or not self.is_internal(host_of(w)):
                continue
            seen.add(w)
            todo.append(w)
        if len(todo) > EXTRA_PROBE_CAP:
            self.warnings.append("canonical/hreflang 指向的未抓 URL 有 %d 个,只补抓前 %d 个"
                                 % (len(todo), EXTRA_PROBE_CAP))
            todo = todo[:EXTRA_PROBE_CAP]
        for u in todo:
            if not self.allowed(u):
                self.extra[u] = {"status": None, "error": "robots Disallow,未抓"}
                continue
            try:
                r = self._request(u)
            except (FetchError, GuardError) as e:
                self.extra[u] = {"status": None, "error": str(e)}
                continue
            ent = {"status": r["status"]}
            if r["chain"]:
                ent["final_url"] = r["final_url"]
                ent["first_status"] = r["chain"][0]["status"]
            if r["status"] < 400:
                pp = parse_page(r["body"], r["final_url"])
                if pp.canonical:
                    ent["canonical"] = normalize_url(pp.canonical, base=r["final_url"])
                if pp.lang is not None:
                    ent["lang"] = pp.lang
                names = robots_names(*pp.robots_meta) | header_robots(_header(r.get("headers"), "x-robots-tag") or "")
                if names & {"noindex", "none"}:
                    ent["noindex"] = True
            self.extra[u] = ent

    def check_resources(self, limit=RESOURCE_CHECK_CAP):
        """--check-resources:页面引用的图片/JS/CSS 逐个 HEAD(405/501 或没有 Content-Length 时 GET),
        记状态、是否重定向、大小。Ahrefs 帮助文:Image broken / JavaScript broken / CSS broken
        「return one of the 4xx or 5xx status codes」(articles 2628254、2750495、2759921)。
        按引用页数取前 limit 个,输出写明查了几个、共几个。"""
        picked = sorted(self.resources.items(), key=lambda kv: (-len(kv[1]["pages"]), kv[0]))[:limit]
        out = {}
        for u, info in picked:
            if self.is_internal(host_of(u)) and not self.allowed(u):
                out[u] = {"status": None, "error": "robots Disallow,未查"}
                continue
            try:
                r = self._request(u, method="HEAD")
                clen = _header(r.get("headers"), "content-length")
                if r["status"] in (405, 501) or (r["status"] < 300 and clen is None):
                    r = self._request(u)
                    clen = _header(r.get("headers"), "content-length")
            except (FetchError, GuardError) as e:
                out[u] = {"status": None, "error": str(e)}
                continue
            ent = {"status": r["status"]}
            if r["chain"]:
                ent["final_url"] = r["final_url"]
                ent["first_status"] = r["chain"][0]["status"]
            try:
                size = int(clen) if clen is not None else None
            except ValueError:
                size = None
            if size is None and r.get("body_bytes"):
                size = (r.get("meta") or {}).get("raw_bytes") or len(r["body_bytes"])
            if size is not None:
                ent["bytes"] = size
            out[u] = ent
        return {"checked": len(picked), "total": len(self.resources), "status": out}

    def site_issues(self, direct, resource_check=None):
        """Ahrefs Site Audit 各项的站级清单(crawl.json 的 site_issues 节)。每个键对应一项 Ahrefs 问题,
        值是受影响 URL 行(最多 100 行)+ counts 里写全量数。只读已抓数据,不再发请求。"""
        P = self.pages
        out, counts = {}, {}

        def put(key, rows):
            counts[key] = len(rows)
            out[key] = rows[:100]

        ok = [u for u in self.order if P[u].get("status") and 200 <= P[u]["status"] < 300 and not P[u].get("final_url")]
        linked_from = {}                                   # 目标 URL → 链到它的站内页(报问题时带上来源页)
        for src_, dst_ in self.edges:
            if src_ != dst_:
                linked_from.setdefault(dst_, []).append(src_)

        def sources(u, k=5):
            return sorted(linked_from.get(u, ()))[:k]
        ok_set = set(ok)
        html_ok = [u for u in ok if P[u].get("html")]

        def indexable(u):
            r = P[u]
            c = r.get("canonical")
            return u in ok_set and not r.get("noindex") and (not c or c == u)

        def target(u):
            return P.get(u) or self.extra.get(u)

        def scheme(u):
            return urllib.parse.urlsplit(u).scheme.lower()

        # -- Internal pages --
        # Double slash in URL:「URLs that contain a double slash (after the domain part)」(help 2596665)
        cand = set(self.order) | {d for _s, d in self.edges}
        put("double_slash_in_url", sorted(u for u in cand if "//" in urllib.parse.urlsplit(u).path
                                          and self.is_internal(host_of(u))))
        # Oversized HTML (>2MB) / HTML file size too large:Googlebot 只抓前 2MB
        put("oversized_html", [{"url": u, "bytes": P[u]["bytes"]} for u in html_ok if P[u].get("bytes", 0) > HTML_LIMIT])
        # HTML file size too large:Ahrefs 未公布阈值,只说「a large html size of 250-300KB or more is usually accompanied by
        # different performance issues」(ahrefs.com/blog/site-audit-issues-update-september-2021/)→ 取 300KB(解压后)
        put("html_file_size_too_large", [{"url": u, "bytes": P[u]["bytes"]} for u in html_ok
                                         if HTML_LARGE_BYTES < P[u].get("bytes", 0)])
        # -- Indexability --
        put("noindex_page", [u for u in ok if P[u].get("noindex")])
        put("nofollow_page", [u for u in ok if P[u].get("nofollow")])       # help 2478724
        put("noindex_in_html_and_header", [u for u in ok if "noindex" in P[u].get("robots_in_html_and_header", ())])
        put("nofollow_in_html_and_header", [u for u in ok if "nofollow" in P[u].get("robots_in_html_and_header", ())])
        c4, c5, cr, ch2s, cs2h, chain, cni = [], [], [], [], [], [], []
        for u in ok:
            c = P[u].get("canonical")
            if not c or c == u:
                continue
            ps, cs = scheme(self.served.get(u, u)), scheme(c)
            if ps == "https" and cs == "http":
                cs2h.append({"url": u, "canonical": c})       # help 2434581
            elif ps == "http" and cs == "https":
                ch2s.append({"url": u, "canonical": c})       # help 2478867
            t = target(c)
            if not t or t.get("status") is None:
                continue
            st = t["status"]
            if t.get("final_url") and t.get("final_url") != c:
                cr.append({"url": u, "canonical": c, "redirects_to": t["final_url"]})   # help 2753767
            elif 400 <= st < 500:
                c4.append({"url": u, "canonical": c, "status": st})                      # help 2427853
            elif st >= 500:
                c5.append({"url": u, "canonical": c, "status": st})                      # help 2491113
            elif t.get("noindex"):
                # canonical 指向 noindex 页:Screaming Frog「Non-Indexable Canonical」——「Pages with a canonical URL
                # specified that is non-indexable ... are 'noindex'」,「search engines are being instructed to consolidate
                # indexing and link signals to a non-indexable page, which often leads to them ignoring the canonical」
                # (https://www.screamingfrog.co.uk/seo-spider/issues/canonicals/non-indexable-canonical/)。
                # noindex 认 meta robots/googlebot 和 X-Robots-Tag 两处
                cni.append({"url": u, "canonical": c, "linked_from": sources(u)})
            elif t.get("canonical") and t["canonical"] != c:
                # Non-canonical page specified as canonical:「pages specified as canonical on other pages ...
                # have a rel=canonical link to a different page」(help 2526305)
                chain.append({"url": u, "canonical": c, "canonical_of_canonical": t["canonical"]})
        put("canonical_points_to_4xx", c4)
        put("canonical_points_to_5xx", c5)
        put("canonical_points_to_redirect", cr)
        put("canonical_from_http_to_https", ch2s)
        put("canonical_from_https_to_http", cs2h)
        put("non_canonical_page_specified_as_canonical", chain)
        put("canonical_points_to_noindex", cni)
        # -- Duplicates --
        idx = [u for u in html_ok if indexable(u)]

        def dup_groups(field):
            g = {}
            for u in idx:
                v = " ".join((P[u].get(field) or "").split()).lower()
                if v:
                    g.setdefault(v, []).append(u)
            return [{"value": P[us[0]].get(field)[:120], "urls": us} for _v, us in sorted(g.items()) if len(us) > 1]
        put("duplicate_title", dup_groups("title"))
        put("duplicate_meta_description", dup_groups("description"))
        put("duplicate_h1", dup_groups("h1"))
        groups = self._content_groups([u for u in html_ok if u in self.sketch and self.sketch[u][2]])
        bad, without = [], []
        for grp in groups:
            canon = {P[u].get("canonical") or u for u in grp}
            alts = all(set(grp) - {u} <= {h for _c, h in P[u].get("hreflang", [])} for u in grp)
            if len(canon) == 1 or alts:
                continue                                  # 好的重复:canonical 指向同一页,或互为 hreflang 版本
            bad.append({"urls": grp})
            # Ahrefs 2021-09 修:加了「Is Noindex = false」条件,noindex 页不报缺 canonical
            without.extend(u for u in grp if not P[u].get("canonical") and not P[u].get("noindex"))
        # Duplicate content (bad duplicates):「Pages with duplicate content that is not properly handled with their
        # canonical, hreflang or pagination setups」(help 2115215);Duplicate pages without canonical:「pages that have
        # duplicate content but do not declare their canonical version」(help 2596742)
        put("duplicate_content_bad", bad)
        put("duplicate_pages_without_canonical", sorted(set(without)))
        # -- Links --
        seed_final = self.served.get(self.seed, self.seed)
        canon_targets = {P[u]["canonical"] for u in ok if P[u].get("canonical") and P[u]["canonical"] != u}
        canon_set = canon_targets | {u for u in ok if P[u].get("source") == "sitemap" and indexable(u)}
        # Canonical URL has no incoming internal links:「URLs in the website's sitemap files that have no incoming
        # internal links」(help 2595174);本脚本另把被别页声明为 canonical 的 URL 也算进来
        # --max 截断时样本外的页可能正链着它(everyinfra.com 实跑 80/5580+ 页误报 1 条):截断就不判,写进 partial
        put("canonical_url_no_incoming_internal_links",
            [] if self.truncated else
            sorted(u for u in canon_set if direct.get(u, 0) == 0 and u not in (self.seed, seed_final)
                   and self.is_internal(host_of(u))))
        inbound = {}
        for (src, dst), followed in self.edge_follow.items():
            if src != dst:
                inbound.setdefault(dst, [0, 0])[0 if followed else 1] += 1
        only, mixed = [], []
        for u in idx:
            f, n = inbound.get(u, (0, 0))
            if n and not f:
                only.append({"url": u, "nofollow_inlinks": n})     # help 2746992
            elif n and f:
                mixed.append({"url": u, "dofollow_inlinks": f, "nofollow_inlinks": n})   # help 2734983
        put("nofollow_incoming_internal_links_only", only)
        put("nofollow_and_dofollow_incoming_internal_links", mixed)
        nf_out = {}
        for src, dst in self.edge_nofollow_link:
            nf_out.setdefault(src, []).append(dst)
        put("nofollow_outgoing_internal_links", [{"url": k, "links": sorted(v)[:20], "count": len(v)}
                                                 for k, v in sorted(nf_out.items())])
        # Page has no outgoing links:「pages that have no outgoing links」(help 2734700)
        put("no_outgoing_links", [u for u in html_ok if not P[u].get("out_internal") and not P[u].get("out_external")])
        to_redir, to_broken = {}, {}
        for src, dst in self.edges:
            t = P.get(dst)
            if not t or src == dst:
                continue
            if t.get("final_url") and t["final_url"] != dst:
                to_redir.setdefault(src, []).append(dst)              # help 2724308(站内部分)
            elif t.get("status") in (404, 410):
                # help 2721106;Ahrefs 2021-09 更新:「We now only include 404 and 410 URLs in this issue」
                # (ahrefs.com/blog/site-audit-issues-update-september-2021/),其他 4xx/5xx 仍在 pages[].status 里
                to_broken.setdefault(src, []).append({"url": dst, "status": t["status"]})
        put("links_to_redirect", [{"url": k, "links": sorted(v)[:20], "count": len(v)} for k, v in sorted(to_redir.items())])
        put("links_to_broken_page", [{"url": k, "links": v[:20], "count": len(v)} for k, v in sorted(to_broken.items())])
        # 链到 4xx 的站内链接(按目标列,带来源页):Google「All 4xx errors, except 429, are treated the same: Google crawlers
        # inform the next processing system that the content doesn't exist」
        # (https://developers.google.com/search/docs/crawling-indexing/http-network-errors)→ 除 429 外的 4xx 都算;
        # 经重定向落到 4xx 的链接也算(终点不存在)。Ahrefs 口径的 404/410 子集仍在 links_to_broken_page
        to_4xx = []
        for dst in sorted(linked_from):
            t = P.get(dst)
            if not t or not self.is_internal(host_of(dst)):
                continue
            st = t.get("status")
            if st is not None and 400 <= st < 500 and st != 429 and not t.get("rate_limited"):
                row = {"url": dst, "status": st, "linked_from": sources(dst, 20), "count": len(linked_from[dst])}
                if t.get("final_url"):
                    row["redirects_to"] = t["final_url"]
                to_4xx.append(row)
        put("links_to_4xx_page", to_4xx)
        # -- Redirects --
        r302, broken, h2s = [], [], []
        for u in self.order:
            hops = self.redirect_hops.get(u, ())
            if not hops or not self.is_internal(host_of(u)):
                continue
            if any(st == 302 for _f, _t, st in hops):
                r302.append({"url": u, "to": P[u].get("final_url")})          # help 2427783
            fst = P[u].get("status")
            if fst is not None and fst >= 400:
                broken.append({"url": u, "to": P[u].get("final_url"), "final_status": fst})   # help 2456799
            if any(scheme(f) == "http" and scheme(t) == "https" for f, t, _st in hops):
                h2s.append(u)
        put("redirect_302", r302)
        put("broken_redirect", broken)
        # Redirect chain / Redirect chain too long:Ahrefs 2021-09 起拆成两项——「"Redirect chain" (Importance: Notice) for
        # redirect chains URLs ≤ 5」「"Redirect chain too long" (Importance: Error) for redirect chains URLs > 5」
        # (https://ahrefs.com/blog/site-audit-issues-update-september-2021/);链 = 起点经 ≥2 跳才到终点。
        # Google:「keep the number of redirects in the chain low, ideally no more than 3 and fewer than 5」
        # (https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)。
        # 每行带起点、逐跳 URL、终点状态和链到起点的站内来源页(要改的是来源页里的链接,直接写终点)
        chains = []
        for u in self.order:
            hops = self.redirect_hops.get(u, ())
            if len(hops) < 2 or not self.is_internal(host_of(u)):
                continue
            chains.append({"url": u, "hops": len(hops), "chain": [u] + [t for _f, t, _st in hops],
                           "statuses": [st for _f, _t, st in hops], "final_status": P[u].get("status"),
                           "linked_from": sources(u), "in_sitemap": P[u].get("source") == "sitemap"})
        chains.sort(key=lambda r: (-r["hops"], r["url"]))
        put("redirect_chain", [r for r in chains if r["hops"] + 1 <= 5])
        put("redirect_chain_too_long", [r for r in chains if r["hops"] + 1 > 5])
        put("http_to_https_redirect", h2s)
        put("meta_refresh_redirect", [{"url": u, "to": P[u]["meta_refresh"]} for u in ok if P[u].get("meta_refresh")])
        # -- 软 404:2xx、非 noindex 的 HTML 页,title/H1 就是报错语或很短的正文里有「页面找不到」(判法与出处见 soft404_evidence)
        put("soft_404", [{"url": u, "evidence": P[u]["soft404"], "linked_from": sources(u)}
                         for u in html_ok if P[u].get("soft404") and not P[u].get("noindex")])
        # -- Content --
        put("multiple_title_tags", [{"url": u, "count": P[u]["title_count"]} for u in ok if P[u].get("title_count", 1) > 1])
        put("multiple_meta_description_tags", [{"url": u, "count": P[u]["description_count"]}
                                               for u in ok if P[u].get("description_count", 1) > 1])
        # -- Social --
        ogm = []
        for u in ok:
            og, c = P[u].get("og_url"), P[u].get("canonical")
            if og and c and re.match(r"^https?://", og, re.I) and normalize_url(og) != c:
                ogm.append({"url": u, "og_url": og, "canonical": c})   # ahrefs.com/blog/canonical-tags/ 第 10 条
        put("og_url_not_matching_canonical", ogm)
        # -- Localization --
        bad_lang = []
        for u in html_ok:
            lang = P[u].get("lang")
            if lang is None:
                continue
            probs = check_lang(lang) if lang.strip().lower() != "x-default" else ["x-default 不是语言码"]
            if probs:
                bad_lang.append({"url": u, "lang": lang, "problem": probs[0]})   # help 2601025
        put("html_lang_invalid", bad_lang)
        ann = {}
        # Ahrefs 2021-09:「We now ignore hreflangs on non-canonical pages」→ 只看 canonical 自指或没写 canonical 的页
        for u in ok:
            if P[u].get("canonical") and P[u]["canonical"] != u:
                continue
            for code, h in P[u].get("hreflang", []):
                if h and code.strip().lower() != "x-default":
                    ann.setdefault(h, []).append((u, code))
        multi, mismatch, to_noncanon = [], [], {}
        for h, refs in sorted(ann.items()):
            langs = sorted({lang_primary(c) for _u, c in refs})
            if len(langs) > 1:
                multi.append({"url": h, "languages": langs, "referenced_from": sorted({u for u, _c in refs})[:10]})
            t = target(h)
            tl = (t or {}).get("lang")
            if tl and not check_lang(tl) and any(lang_primary(c) != lang_primary(tl) for _u, c in refs):
                mismatch.append({"url": h, "html_lang": tl, "hreflang": sorted({c for _u, c in refs})})
            if t and not t.get("final_url") and t.get("canonical") and t["canonical"] != h:
                for u, _c in refs:
                    to_noncanon.setdefault(u, []).append({"hreflang_url": h, "canonical": t["canonical"]})
        put("page_referenced_for_more_than_one_language", multi)    # help 2747339
        put("hreflang_and_html_lang_mismatch", mismatch)            # help 2598523
        put("hreflang_to_non_canonical", [{"url": k, "targets": v[:10]} for k, v in sorted(to_noncanon.items())])  # help 2608450
        # -- Usability and performance --
        put("slow_page", [{"url": u, "load_ms": P[u]["load_ms"]} for u in html_ok if P[u].get("load_ms", 0) > self.slow_ms])
        put("not_compressed", [u for u in html_ok if P[u].get("encoding") == "identity"])
        # -- AI Discoverability:Too slow/heavy for AI crawlers(Ahrefs 只公布了名称,未公布判法)。AI 爬虫只取 HTML、
        #    不跑 JS,所以按两条可量的原因判:HTML 下载慢于 --slow-ms、HTML >2MB。外部 script 个数不算
        #    (everyinfra.com 实跑:Next.js 每页 18-19 个 script,80/80 页都被报,与 AI 爬虫取页无关)
        heavy = []
        for u in html_ok:
            why = []
            if P[u].get("load_ms", 0) > self.slow_ms:
                why.append("加载 %dms" % P[u]["load_ms"])
            if P[u].get("bytes", 0) > HTML_LIMIT:
                why.append("HTML %.1fMB" % (P[u]["bytes"] / 1048576))
            if why:
                heavy.append({"url": u, "reasons": why})
        put("too_slow_or_heavy_for_ai_crawlers", heavy)
        # -- 资源:HTTPS 页引用 HTTP 的图片/JS/CSS(不用请求就能判)--
        for typ, key in (("image", "image"), ("js", "javascript"), ("css", "css")):
            rows = {}
            for ru, info in self.resources.items():
                if info["type"] != typ or scheme(ru) != "http":
                    continue
                for pg in info["pages"]:
                    if scheme(self.served.get(pg, pg)) == "https":
                        rows.setdefault(pg, []).append(ru)
            put("https_page_links_to_http_" + key, [{"url": k, "resources": v[:10]} for k, v in sorted(rows.items())])
        if resource_check is not None:
            stat = resource_check["status"]
            limits = {"image": IMAGE_MAX_BYTES, "css": CSS_MAX_BYTES}
            for typ, key in (("image", "image"), ("js", "javascript"), ("css", "css")):
                items = [(u, self.resources[u], stat[u]) for u in stat if self.resources.get(u, {}).get("type") == typ]
                brk = [(u, i, e) for u, i, e in items if e.get("status") is not None and e["status"] >= 400]
                put(key + "_broken", [{"url": u, "status": e["status"], "pages": len(i["pages"])} for u, i, e in brk])
                pages = {}
                for u, i, e in brk:
                    for pg in i["pages"]:
                        pages.setdefault(pg, []).append(u)
                put("page_has_broken_" + key, [{"url": k, "resources": v[:10]} for k, v in sorted(pages.items())])
                put(key + "_redirects", [{"url": u, "to": e["final_url"], "status": e.get("first_status")}
                                         for u, i, e in items if e.get("final_url") and e["final_url"] != u])
                if typ in limits:
                    put(key + "_file_size_too_large", [{"url": u, "bytes": e["bytes"]} for u, i, e in items
                                                       if e.get("bytes", 0) > limits[typ] and (e.get("status") or 0) < 400])
        if self.truncated:
            out["partial"] = {"skipped": ["canonical_url_no_incoming_internal_links"],
                              "reason": "--max 截断,入链数只算样本内的页;没有站内入链这一项不判。"
                                        "nofollow 入链两项只看样本内的链接,可能偏少"}
        out["counts"] = counts
        return out

    def _content_groups(self, urls):
        """完全重复(全文哈希相同)∪ 近似重复(bottom-k 估算 Jaccard ≥NEAR_DUP_JACCARD)→ 分组(并查集)。
        候选对:最小 8 个 shingle 哈希里有共同项的页面才比,避免 n² 全比。"""
        parent = {u: u for u in urls}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra
        by_full, buckets = {}, {}
        for u in urls:
            _n, full, sk = self.sketch[u]
            by_full.setdefault(full, []).append(u)
            for h in sk[:8]:
                buckets.setdefault(h, []).append(u)
        for us in by_full.values():
            for v in us[1:]:
                union(us[0], v)
        seen = set()
        for us in buckets.values():
            if len(us) > 50:          # 模板公共段落(页脚)命中太多页,不当候选
                continue
            for i, a in enumerate(us):
                for b in us[i + 1:]:
                    if (a, b) in seen or find(a) == find(b):
                        continue
                    seen.add((a, b))
                    if sketch_jaccard(self.sketch[a][2], self.sketch[b][2]) >= NEAR_DUP_JACCARD:
                        union(a, b)
        groups = {}
        for u in urls:
            groups.setdefault(find(u), []).append(u)
        return [sorted(g) for g in groups.values() if len(g) > 1]

    def subdomain_robots(self):
        """各子域各自的 robots.txt(GEO 补项)。判据:BingBot「looks at the root of the host」
        取 robots.txt,host 是完整子域;子域没有 robots.txt 时「BingBot will not try to fall back to
        any other file in your domain, meaning it will consider itself allowed anywhere on the
        subdomain」(https://blogs.bing.com/webmaster/2012/5/To-crawl-or-not-to-crawl,-that-is-BingBot-s-questi/);
        Google 同口径「A robots.txt on a subdomain is only valid for that subdomain」
        (https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec)。
        抓得到才判:网络失败/5xx 记「未判定」。--ignore-robots 时不抓,返回 None。"""
        if self.ns.ignore_robots or self.ns.same_host:
            return None
        main_origin = self._origin(self.seed)
        main_doc = self._robots(main_origin)
        main_rules = 0
        if main_doc:
            main_rules = sum(len([x for x in g.get("disallow", []) if x])
                             for g in main_doc.get("groups", {}).values())
        rows = []
        for host in sorted(self.accepted_subs):
            origin = "%s://%s" % (self.scheme, host)
            self._robots(origin)
            st = self.robots_status.get(origin)
            if st == 200:
                verdict = "有"
            elif st == "html":
                verdict = "返回 HTML(不是 robots.txt,读不出规则,等于全放行)"
            elif st in (404, 410):
                verdict = "缺失(该子域全放行;主域 robots.txt 不覆盖子域)"
            elif isinstance(st, int) and 400 <= st < 500:
                verdict = "HTTP %d(RFC 9309:4xx 视同没有 robots.txt,全放行)" % st
            else:
                verdict = "未判定(%s)" % ("抓取失败" if st in (None, "error") else "HTTP %s" % st)
            rows.append({"host": host, "status": st, "verdict": verdict})
        return {"main_host": self.seed_host, "main_status": self.robots_status.get(main_origin),
                "main_rules": main_rules, "hosts": rows}

    # ---- 汇总 ----

    def build_report(self, duration_s):
        def _targets(dst):
            """边的目标 → 计入入链的已抓页面:原样命中的页面,以及去掉查询参数后命中的页面
            (站内链接常带 ?iref= 之类跟踪参数,sitemap 里是干净 URL;不认这种对应,
            干净 URL 永远收不到入链。2026-10-24 asahi.com 实测)。"""
            out = set()
            if dst in self.pages:
                out.add(dst)
            sp = urllib.parse.urlsplit(dst)
            if sp.query:
                bare = urllib.parse.urlunsplit((sp.scheme, sp.netloc, sp.path, "", ""))
                if bare in self.pages:
                    out.add(bare)
            return out
        inlinks = Counter()
        for src, dst in self.edges:
            for t in _targets(dst):
                if t != src or t == dst:          # 带参数的自链不算别人给的入链
                    inlinks[t] += 1
        adjacency = {}
        for src, dst in self.edges:
            adjacency.setdefault(src, []).extend(_targets(dst) or [dst])
        depths = {}
        if self.seed in self.pages:
            dq = deque([self.seed])
            depths[self.seed] = 0
            while dq:
                u = dq.popleft()
                for v in adjacency.get(u, ()):
                    if v not in depths:
                        depths[v] = depths[u] + 1
                        dq.append(v)
        pages = []
        for url in self.order:
            rec = dict(self.pages[url])
            rec["inlinks"] = inlinks.get(url, 0)
            rec["depth"] = depths.get(url)
            pages.append(rec)
        # 被重定向的 URL(含 www./api. 子域 301 到主站)不算孤儿:内链该指向重定向目标
        redirected = {u for u in self.order
                      if self.pages[u].get("final_url") and self.pages[u]["final_url"] != u}
        orphans = [u for u in self.order
                   if inlinks.get(u, 0) == 0 and u != self.seed and u not in redirected]
        out_int = sum(p["out_internal"] for p in pages)
        out_ext = sum(p["out_external"] for p in pages)
        total_out = out_int + out_ext
        edges_out = []
        for s, d in sorted(self.edges):
            e = {"src": s, "dst": d}
            a = self.edge_anchor.get((s, d))
            if a:
                e["anchor"] = a          # R3-5:锚文本可缺(短锚/旧数据),下游须容忍无 anchor 键
            edges_out.append(e)
        report = {
            "schema_version": SCHEMA_VERSION,
            "domain": self.reg,
            "subdomains": sorted(self.accepted_subs),
            "discovery": {"mode": self.mode, "counts": dict(self.counts)},
            "pages": pages,
            "edges": edges_out,
            "orphans": orphans,
            "external_domains": dict(_top_domains(self.external, EXTERNAL_TOP)),
            "stats": {
                "pages": len(pages),
                "total_inlinks": sum(inlinks.get(u, 0) for u in self.order),
                "total_outlinks": total_out,          # 总出链 = 内链出链 + 外链出链
                "total_out_internal": out_int,
                "total_out_external": out_ext,
                "redirected_pages": len(redirected),  # 不计入孤儿
                "errors": self.errors,
                "redirects": self.redirects,
                "duration_s": round(duration_s, 2),
            },
            "warnings": list(self.warnings),
        }
        # 抓取被 --max 截断时,孤儿只在已抓样本内判定(入链来源页可能没抓到),不等于站内孤儿
        # (追加在末尾,不改动既有输出契约的键序)
        report["orphans_partial"] = bool(self.truncated)
        report["rate_limited_pages"] = self.rate_limited     # 疑似限流、未判定(不算错误页)
        report["discovery"]["crawl_fallback"] = bool(self.crawl_fallback)
        report["discovery"]["links_followed"] = bool(self.links_followed)   # link_graph 据此判断入链是否欠采样
        direct = Counter()
        for src, dst in self.edges:
            if dst == src:
                continue
            direct[dst] += 1
            sp = urllib.parse.urlsplit(dst)
            if sp.query:                          # 带跟踪参数的链接也算直接指向干净 URL(同 _targets)
                direct[urllib.parse.urlunsplit((sp.scheme, sp.netloc, sp.path, "", ""))] += 1
        report["link_issues"] = self.link_issues(direct)
        report["site_issues"] = self.site_issues(direct, getattr(self, "resource_check", None))
        if getattr(self, "resource_check", None) is not None:
            rc_ = self.resource_check
            report["resource_check"] = {"checked": rc_["checked"], "total": rc_["total"]}
        if self.rate_limited:
            report["warnings"].append(
                "%d 页疑似被站点限流(429,或先 200 后 403/503,退避重试后仍是),未判定,不算错误页;"
                "加大 --delay 或错开同时跑的脚本再抓" % self.rate_limited)
        if self.skipped_robots:
            report["warnings"].append(
                "robots Disallow 跳过 %d URL(如 %s);--ignore-robots 可显式关闭遵守"
                % (len(self.skipped_robots), self.skipped_robots[0]))
            report["robots_skipped"] = self.skipped_robots
        return report

    def run(self):
        """主流程:发现 → 子域 → 抓取 → (可选外链域抽检)→ 报告;返回 (report, exit_code)。"""
        t0 = time.monotonic()
        mode, crawl_fallback = self.discover()
        self.discover_subdomains()
        self.crawl(crawl_fallback)
        self.probe_extra()
        self.resource_check = self.check_resources() if getattr(self.ns, "check_resources", False) else None
        report = self.build_report(time.monotonic() - t0)
        if self.ns.check_external:
            report["external_check"] = self.check_external_domains()
            report["external_redirects"] = self.check_external_redirects()
            # Page has links to redirect / links to broken page 的外链部分(help 2724308、2721106:internal and external)
            si = report["site_issues"]
            for key, rows in (("external_links_to_redirect", report["external_redirects"]["redirects"]),
                              ("external_links_to_broken", report["external_redirects"]["broken"])):
                si[key] = rows[:100]
                si["counts"][key] = len(rows)
        sub = self.subdomain_robots()
        if sub is not None:
            report["subdomain_robots"] = sub
        reached = [p for p in report["pages"] if p["status"] is not None]
        if not reached:                      # 全起点失败(所有抓取尝试均传输失败)
            rc = 3
        elif self.errors:
            rc = 1                           # 有错误页(4xx/5xx 或重试后仍失败)
        else:
            rc = 0
        return report, rc


# ---------------------------------------------------------------------------
# 渲染与 CLI
# ---------------------------------------------------------------------------

def render_markdown(report):
    st = report["stats"]
    disc = report["discovery"]
    c = disc["counts"]
    L = ["## site_crawl: %s" % report["domain"], ""]
    src_desc = {
        "robots+sitemap": "链② robots Sitemap 指令 %d 条 → 链③ sitemap loc %d" % (c["robots"], c["sitemap"]),
        "sitemap": "链③ sitemap loc %d(robots 无 Sitemap 指令)" % c["sitemap"],
        "crawl": "链④ 爬虫兜底(robots/sitemap 均无产出)",
        "urls": "链① --urls 手工清单 %d 条" % st["pages"],
    }.get(disc["mode"], disc["mode"])
    # 摘要按 discovery.crawl_fallback 说话:修前把子域根页(counts.crawl 里)说成「loc<50 兜底开着」,
    # everyinfra 实际 2769 条 loc、plausible 167 条 loc,兜底根本没开(2026-11-05 评分)。
    fallback = disc.get("crawl_fallback")
    if fallback is None:                        # 旧版 crawl.json 没有该键:按规则推
        fallback = disc["mode"] == "crawl" or c.get("sitemap", 0) < SITEMAP_CLOSES_CRAWL
    if disc["mode"] in ("robots+sitemap", "sitemap"):
        if fallback:
            src_desc += " ∪ 链④ 爬虫补量 %d(loc %d<%d,爬虫补量开着)" % (
                c["crawl"], c["sitemap"], SITEMAP_CLOSES_CRAWL)
        elif disc.get("links_followed"):
            src_desc += "(loc ≥%d,先抓 sitemap;站内链接指向、sitemap 没列的 URL 排在后面补抓 %d 个)" % (
                SITEMAP_CLOSES_CRAWL, c.get("link", 0))
        else:
            src_desc += "(loc ≥%d,爬虫补量关闭,站内链接只进图不请求)" % SITEMAP_CLOSES_CRAWL
    elif disc["mode"] == "crawl":
        src_desc = "链④ 爬虫兜底(robots/sitemap 均无产出)发现 %d 页" % c["crawl"]
    if c.get("subdomain"):
        src_desc += " ∪ 子域根页 %d" % c["subdomain"]
    L.append("- 发现模式: %s(%s)" % (disc["mode"], src_desc))
    subs = report["subdomains"]
    L.append("- 子域 %d 个: %s" % (len(subs), ", ".join(subs) if subs else "-"))
    err_rate = (st["errors"] / st["pages"]) if st["pages"] else 0.0
    out_int = st.get("total_out_internal")
    out_ext = st.get("total_out_external")
    if out_int is None or out_ext is None:      # 旧版 crawl.json 只有总出链
        links = "总出链 %d(旧版报告未分内外链)" % st["total_outlinks"]
    else:
        links = "出链:内链 %d,外链 %d,总出链 %d" % (out_int, out_ext, st["total_outlinks"])
    L.append("- 页面 %d:错误 %d(错误率 %.1f%%),重定向 %d,%s;已抓页面收到的入链 %d,耗时 %.1fs"
             % (st["pages"], st["errors"], err_rate * 100, st["redirects"], links,
                st["total_inlinks"], st["duration_s"]))
    top = list(report["external_domains"].items())[:10]
    if top:
        L.append("- Top 外链域: " + ", ".join("%s×%d" % (d, n) for d, n in top))
    orphans = report["orphans"]
    if report.get("orphans_partial"):
        L.append("- ⚠ 抓取被 --max 截断:下面的孤儿只表示「已抓样本内 0 入链」,入链来源页可能没抓到;"
                 "要下孤儿结论,用 --max 覆盖全站,或用 --urls 给出栏目页再抓")
    L.append("- 孤儿页 %d(0 入链、非首页、未被重定向;重定向页 %d 个不计):%s"
             % (len(orphans), st.get("redirected_pages", 0),
                ", ".join(orphans[:10]) if orphans else "无"))
    for w in report.get("warnings", []):
        L.append("- ⚠ %s" % w)
    if report.get("external_check"):
        L.append("- 外链域抽检(--check-external,HEAD 根路径): "
                 + ", ".join("%s=%s" % (e["domain"], e["status"]) for e in report["external_check"]))
    L.extend(render_link_issues(report))
    return "\n".join(L)


def render_link_issues(report):
    """Ahrefs 补项与子域 robots 的人读行(crawl.json 的 link_issues / external_redirects /
    subdomain_robots 节)。"""
    L = []
    li = report.get("link_issues")
    if li is not None:
        part = "(抓取被 --max 截断,只代表已抓样本)" if report.get("orphans_partial") else ""
        rows = li.get("redirect_target_no_direct_inlinks", [])
        L.append("- 重定向目标页没有直接内链 %d%s(只能经重定向到达;只对想排名的可索引页要紧,本脚本不判可索引性):%s"
                 % (len(rows), part, ", ".join("%s(经 %s)" % (r["target"], r["via"][0]) for r in rows[:5]) or "无"))
        rows = li.get("http_page_links_to_https", [])
        L.append("- HTTP 页链到 HTTPS %d 页:%s" % (len(rows), ", ".join(r["page"] for r in rows[:5]) or "无"))
        rows = li.get("https_page_links_to_http", [])
        L.append("- HTTPS 页链到 HTTP %d 页:%s" % (len(rows), ", ".join(r["page"] for r in rows[:5]) or "无"))
        rows = li.get("https_to_http_redirects", [])
        L.append("- HTTPS→HTTP 重定向 %d:%s" % (len(rows), ", ".join("%s → %s" % (r["from"], r["to"])
                                                                 for r in rows[:5]) or "无"))
    ex = report.get("external_redirects")
    if ex is not None:
        reds = ex["redirects"]
        L.append("- 外链 3xx(抽检 %d/%d 个外链 URL,按引用页数取前 %d):%d 个%s"
                 % (ex["checked"], ex["total"], EXTERNAL_URL_SAMPLE, len(reds),
                    (":" + ", ".join("%s → %s [%s]" % (r["url"], r["final_url"], r["kind"])
                                     for r in reds[:5])) if reds else ""))
        bad = ex.get("broken") or []
        L.append("- 外链 4xx(同一批抽检):%d 个%s" % (len(bad), (":" + ", ".join(
            "%s [%s]" % (r["url"], r["status"]) for r in bad[:5])) if bad else ""))
    else:
        L.append("- 外链 3xx:未检查(加 --check-external 才抽检外链 URL)")
    L.extend(render_site_issues(report))
    sub = report.get("subdomain_robots")
    if sub is not None and sub["hosts"]:
        main = ("主域 %s 的 %d 条 Disallow 不覆盖子域" % (sub["main_host"], sub["main_rules"])
                if sub["main_rules"] else "主域 %s 没有 Disallow 规则,子域缺 robots.txt 也是全放行" % sub["main_host"])
        L.append("- 子域 robots.txt(每个子域各读自己的一份;%s):%s"
                 % (main, "; ".join("%s=%s" % (h["host"], h["verdict"]) for h in sub["hosts"])))
    return L


# site_issues 键 → (Ahrefs 问题名, 人读说明);渲染顺序即本表顺序(按 Ahrefs 报告分类)
SITE_ISSUE_LABELS = [
    ("double_slash_in_url", "Double slash in URL", "URL 路径有 //"),
    ("oversized_html", "Oversized HTML (>2MB)", "HTML 超过 2MB(Googlebot 只抓前 2MB)"),
    ("html_file_size_too_large", "HTML file size too large", "HTML 解压后 >300KB(Ahrefs 未公布阈值,博客写 250-300KB 起)"),
    ("noindex_page", "Noindex page", "noindex 页"),
    ("nofollow_page", "Nofollow page", "nofollow 页"),
    ("noindex_in_html_and_header", "Noindex in HTML and HTTP header", "noindex 同时写在 meta 和 X-Robots-Tag"),
    ("nofollow_in_html_and_header", "Nofollow in HTML and HTTP header", "nofollow 同时写在 meta 和 X-Robots-Tag"),
    ("canonical_points_to_4xx", "Canonical points to 4XX", "canonical 指向 4xx"),
    ("canonical_points_to_5xx", "Canonical points to 5XX", "canonical 指向 5xx"),
    ("canonical_points_to_redirect", "Canonical points to redirect", "canonical 指向会重定向的 URL"),
    ("canonical_from_http_to_https", "Canonical from HTTP to HTTPS", "HTTP 页 canonical 指向 HTTPS"),
    ("canonical_from_https_to_http", "Canonical from HTTPS to HTTP", "HTTPS 页 canonical 指向 HTTP"),
    ("non_canonical_page_specified_as_canonical", "Non-canonical page specified as canonical",
     "canonical 指向的页自己又 canonical 到别处(canonical 链)"),
    ("canonical_points_to_noindex", "Non-Indexable Canonical(noindex)", "canonical 指向 noindex 页(meta 或 X-Robots-Tag)"),
    ("duplicate_pages_without_canonical", "Duplicate pages without canonical", "内容重复且没写 canonical 的页"),
    ("duplicate_content_bad", "Duplicate content (bad duplicates)", "内容重复且没用 canonical/hreflang 处理的组"),
    ("duplicate_title", "Duplicate title tag", "可索引页 title 重复的组"),
    ("duplicate_meta_description", "Duplicate meta description", "可索引页 description 重复的组"),
    ("duplicate_h1", "Duplicate H1", "可索引页 H1 重复的组"),
    ("canonical_url_no_incoming_internal_links", "Canonical URL has no incoming internal links",
     "sitemap 里或被声明为 canonical 的 URL 没有站内入链"),
    ("nofollow_incoming_internal_links_only", "Page has nofollow incoming internal links only", "只有 nofollow 站内入链"),
    ("nofollow_and_dofollow_incoming_internal_links", "Page has nofollow and dofollow incoming internal links",
     "站内入链 nofollow 与 dofollow 混用"),
    ("nofollow_outgoing_internal_links", "Page has nofollow outgoing internal links", "页内有 rel=nofollow 的站内链接"),
    ("no_outgoing_links", "Page has no outgoing links", "没有任何出链(死胡同页)"),
    ("links_to_redirect", "Page has links to redirect", "链到会重定向的站内 URL"),
    ("links_to_broken_page", "Page has links to broken page", "链到 404/410 站内 URL(Ahrefs 2021-09 起只算这两种)"),
    ("links_to_4xx_page", "Internal links to 4XX", "被站内链接引用的 4xx URL(除 429;按目标列,带来源页)"),
    ("external_links_to_redirect", "Page has links to redirect(外链)", "外链 3xx(--check-external 抽检)"),
    ("external_links_to_broken", "External 4XX / links to broken page(外链)", "外链 4xx/5xx(--check-external 抽检)"),
    ("redirect_302", "302 redirect", "站内 URL 用 302 跳转"),
    ("broken_redirect", "Broken redirect", "跳转终点 4xx/5xx"),
    ("redirect_chain", "Redirect chain", "≥2 跳才到终点的重定向链(链上 URL ≤5;带起点和来源页)"),
    ("redirect_chain_too_long", "Redirect chain too long", "链上 URL >5 的重定向链"),
    ("http_to_https_redirect", "HTTP to HTTPS redirect", "HTTP 跳 HTTPS(提示,内链宜直接写 HTTPS)"),
    ("meta_refresh_redirect", "Meta refresh redirect", "meta refresh 客户端跳转"),
    ("soft_404", "Soft 404", "返回 2xx 但页面是「找不到页面」(软 404)"),
    ("multiple_title_tags", "Multiple title tags", "一页多个 <title>"),
    ("multiple_meta_description_tags", "Multiple meta description tags", "一页多个 meta description"),
    ("og_url_not_matching_canonical", "Open Graph URL not matching canonical", "og:url 与 canonical 不一致"),
    ("html_lang_invalid", "HTML lang attribute invalid", "html lang 不是 ISO 639-1(+ISO 3166-1)"),
    ("hreflang_and_html_lang_mismatch", "Hreflang and HTML lang mismatch", "hreflang 写的语言与目标页 html lang 不一致"),
    ("page_referenced_for_more_than_one_language", "Page referenced for more than one language in hreflang",
     "同一 URL 被 hreflang 标成多种语言"),
    ("hreflang_to_non_canonical", "Hreflang to non-canonical", "hreflang 指向非 canonical 页"),
    ("slow_page", "Slow page", "HTML 下载慢于 --slow-ms"),
    ("not_compressed", "Not compressed", "HTML 没压缩"),
    ("too_slow_or_heavy_for_ai_crawlers", "Too slow/heavy for AI crawlers", "对 AI 爬虫太慢或太重"),
    ("https_page_links_to_http_image", "HTTPS page links to HTTP image", "HTTPS 页引用 HTTP 图片"),
    ("https_page_links_to_http_javascript", "HTTPS page links to HTTP JavaScript", "HTTPS 页引用 HTTP 脚本"),
    ("https_page_links_to_http_css", "HTTPS page links to HTTP CSS", "HTTPS 页引用 HTTP 样式表"),
    ("image_broken", "Image broken", "图片 4xx/5xx"),
    ("page_has_broken_image", "Page has broken image", "页面引用坏图片"),
    ("image_redirects", "Image redirects", "图片 URL 会重定向"),
    ("image_file_size_too_large", "Image file size too large", "图片 >100KB"),
    ("javascript_broken", "JavaScript broken", "JS 文件 4xx/5xx"),
    ("page_has_broken_javascript", "Page has broken JavaScript", "页面引用坏 JS"),
    ("javascript_redirects", "JavaScript redirects", "JS URL 会重定向"),
    ("css_broken", "CSS broken", "CSS 文件 4xx/5xx"),
    ("page_has_broken_css", "Page has broken CSS", "页面引用坏 CSS"),
    ("css_redirects", "CSS redirects", "CSS URL 会重定向"),
    ("css_file_size_too_large", "CSS file size too large", "CSS >15KB"),
]


def _row_text(row):
    if isinstance(row, str):
        return row
    lf = row.get("linked_from")
    src = ("(来源 %s)" % ", ".join(lf[:2])) if isinstance(lf, list) and lf else ""
    if "chain" in row:
        return "%s 跳:%s [终点 %s]%s" % (row["hops"], " → ".join(row["chain"]), row.get("final_status"), src)
    if "evidence" in row:
        return "%s(%s)%s" % (row["url"], row["evidence"], src)
    if "status" in row and isinstance(lf, list):
        return "%s [%s]%s" % (row["url"], row["status"], src)
    if "canonical" in row and isinstance(lf, list):
        return "%s → canonical %s" % (row["url"], row["canonical"])
    if "urls" in row:
        return " = ".join(row["urls"][:3]) + (" …" if len(row["urls"]) > 3 else "")
    return row.get("url") or json.dumps(row, ensure_ascii=False)[:100]


def render_site_issues(report):
    """site_issues 的人读行:只列命中的项(各带全量数和前 3 例);没命中的合成一行。"""
    si = report.get("site_issues")
    if not si:
        return []
    counts = si.get("counts", {})
    L, clean = ["- Ahrefs 站点审计各项(site_issues;规则与出处见 references/technical/ahrefs-site-audit-coverage.md):"], []
    for key, name, desc in SITE_ISSUE_LABELS:
        if key not in counts:
            continue
        n = counts[key]
        if not n:
            clean.append(name)
            continue
        extra = ""
        if key == "links_to_redirect":                     # 几百页都链到同一个跳转 URL(导航里的购物车等)时一眼看出来
            tc = Counter(t for r in si[key] for t in r.get("links", ()))
            extra = "(按被链目标:%s)" % ", ".join("%s×%d" % kv for kv in tc.most_common(3))
        L.append("  - [%s] %s %d%s:%s" % (name, desc, n, extra, "; ".join(_row_text(r) for r in si[key][:3])))
    if clean:
        L.append("  - 未命中 %d 项:%s" % (len(clean), ", ".join(clean)))
    if si.get("partial"):
        L.append("  - ⚠ 截断:%s" % si["partial"]["reason"])
    rc = report.get("resource_check")
    if rc:
        L.append("  - 资源检查:查了 %d/%d 个图片/JS/CSS URL(按引用页数取前 %d)" % (rc["checked"], rc["total"], RESOURCE_CHECK_CAP))
    else:
        L.append("  - 图片/JS/CSS 坏链、重定向、体积:未检查(加 --check-resources)")
    return L


USAGE_EPILOG = """\
发现链(unlighthouse 优先级,取到即止):① --urls 手工清单(关闭②③④)→ ② robots.txt
Sitemap 指令 → ③ sitemap(递归 index;≥50 loc 关闭爬虫)→ ④ BFS 爬虫兜底。
子域:同 registrable domain 采信(robots/sitemap/内链出现)+ 常见子域 DNS+200 探测
+ --subs ct 走 crt.sh;--same-host 收紧到单主机。
礼貌:robots.txt 默认遵守(Disallow 排除/crawl-delay 取 * 组与 --delay 取大);
每 URL 传输层失败重试 2 次;--max 默认 500(上限 5000,超出警告并截断)。
SSRF:仅 http(s),拒私网/环回/链路本地,重定向逐跳复查(同 site_audit/monitor 惯例);
审本机开发站加 --allow-local(只放行回环,私网照旧拒)。
输出:crawl.json(--out)+ --urls-out 纯 URL 清单(喂 site_audit/traffic_funnel --urls)
+ markdown 摘要;--json 打 stdout。不抓外链目标;--check-external 只对外链域抽样 HEAD。
退出码:0 正常 / 1 有错误页(4xx/5xx 或重试后仍失败) / 2 输入错 / 3 全部起点失败。\
"""


def build_parser():
    ap = argparse.ArgumentParser(
        prog="site_crawl.py",
        description="全站发现与爬取器:robots/sitemap/爬虫三链发现 + 子域探测 + 内外链图 "
                    "+ 孤儿页检测(stdlib only;发现链口径 references/monitoring/ci-gates.md §四)",
        epilog=USAGE_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site", help="站点 URL 或裸域名(自动补 https://),如 example.com")
    ap.add_argument("--urls", metavar="FILE",
                    help="手工 URL 清单(每行一条,# 注释);给出即关闭 robots/sitemap/爬虫发现(链①);"
                         "robots 礼貌规则仍生效,除非 --ignore-robots")
    ap.add_argument("--max", dest="max_pages", type=int, default=DEFAULT_MAX_PAGES, metavar="N",
                    help="抓取页数预算(默认 %d,上限 %d,超出警告+截断)" % (DEFAULT_MAX_PAGES, HARD_MAX_PAGES))
    ap.add_argument("--delay", type=float, default=DEFAULT_DELAY, metavar="SEC",
                    help="请求间隔下限(默认 %.1fs;robots Crawl-delay 更大时以其为准)" % DEFAULT_DELAY)
    ap.add_argument("--ignore-robots", action="store_true",
                    help="显式关闭 robots.txt 遵守(Disallow 不排除/crawl-delay 不采用)")
    ap.add_argument("--strip-params", action="store_true",
                    help="URL 归一时丢弃查询参数(默认保留参数;两种口径的页数不可直接比较)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--include-subdomains", dest="include_subdomains", action="store_true",
                   default=True, help="子域发现默认开启(默认行为,显式确认用)")
    g.add_argument("--same-host", dest="same_host", action="store_true",
                   help="收紧到单主机:不做子域发现,跨子域链接按外链记")
    ap.add_argument("--subs", default="dns", metavar="dns[,ct]",
                    help="子域补充来源:dns=常见子域探测(默认)/ct=crt.sh CT 日志(失败优雅跳过)")
    ap.add_argument("--check-external", action="store_true",
                    help="对 Top 外链域抽样 HEAD 验活(默认关;用途:验证外链指向是否腐烂,不外爬)")
    ap.add_argument("--check-resources", action="store_true",
                    help="页面引用的图片/JS/CSS 逐个 HEAD(按引用页数取前 %d 个):坏资源、资源重定向、"
                         "图片 >100KB、CSS >15KB(Ahrefs Images/JavaScript/CSS 各项;默认关)" % RESOURCE_CHECK_CAP)
    ap.add_argument("--slow-ms", type=int, default=SLOW_MS_DEFAULT, metavar="MS",
                    help="慢页阈值:HTML 下载完用时超过它记 slow_page(默认 %(default)s;Ahrefs 未公布阈值)")
    ap.add_argument("--out", default="crawl.json", metavar="FILE", help="crawl.json 输出路径(默认 %(default)s)")
    ap.add_argument("--urls-out", metavar="FILE", help="纯 URL 清单输出(2xx/3xx 页,喂下游脚本)")
    ap.add_argument("--json", action="store_true", help="报告 JSON 打 stdout(替代 markdown 摘要)")
    ap.add_argument("--timeout", type=float, default=10.0, metavar="SEC", help="单请求超时(默认 10s)")
    ap.add_argument("--sitemap-only", action="store_true",
                    help="sitemap ≥50 条时只抓 sitemap(旧口径:站内链接只进图、不请求;断链和重定向链查不到)")
    ap.add_argument("--allow-local", action="store_true",
                    help="审本机开发站:只多放行回环地址(127.0.0.0/8、::1、localhost),私网段照旧拒绝")
    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)          # 用法错 argparse 自带退出码 2
    if args.max_pages <= 0:
        ap.error("--max 必须为正整数")
    if args.delay < 0:
        ap.error("--delay 不能为负")
    bad_subs = [t for t in (args.subs or "").split(",") if t.strip() not in ("dns", "ct")]
    if bad_subs:
        ap.error("--subs 仅接受 dns/ct 逗号组合,未知项: %s" % ",".join(bad_subs))
    if args.urls and not os.path.isfile(args.urls):
        ap.error("--urls 文件不存在: %s" % args.urls)
    global ALLOW_LOCAL
    ALLOW_LOCAL = bool(args.allow_local)
    try:
        crawler = Crawler(args)
    except ValueError as e:
        ap.error(str(e))
    try:                                 # 起点先过一次守卫:本机/内网站点直接报用法错,不进抓取
        ssrf_guard(urllib.parse.urlsplit(crawler.seed).hostname)
    except GuardError as e:
        if not str(e).startswith("DNS 解析失败"):      # 解析不了照旧走抓取,按「全部起点失败」退 3
            ap.error(str(e))
    report, rc = crawler.run()
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    if args.urls_out:
        # 喂下游的清单用站点声明的原始 URL(重定向审计另有 redirect_chain.py);
        # 只收 2xx/3xx 页——4xx/传输失败页喂给 site_audit 只会再失败一次。
        live = [p["url"] for p in report["pages"]
                if p["status"] is not None and p["status"] < 400]
        with open(args.urls_out, "w", encoding="utf-8") as f:
            f.write("\n".join(live) + ("\n" if live else ""))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        print(render_markdown(report))
    for w in report.get("warnings", []):
        sys.stderr.write("[site_crawl] ⚠ %s\n" % w)
    return rc


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        sys.exit(130)
