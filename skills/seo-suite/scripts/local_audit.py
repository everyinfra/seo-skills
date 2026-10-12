#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_audit.py — 本地 SEO 四节体检(NAP / GBP / 本地 schema / 落地页本地信号;站型卡④;stdlib only)。

用法:
  python3 local_audit.py --url https://example.com --name "Acme Plumbing" \
      --addr "123 Main St, Suite 4, Austin, TX 78701" [--city Austin] \
      [--phone "+1 512 555 0100"] [--timeout 15] [--json]
  --url 也可传 GBP 页(google.*/maps|place 等)——§2 逐项抓取,§3/§4 自动转 unverified
  (GBP 页内没有站内 JSON-LD/落地页信号,不硬判)。

口径(references/overview/site-type-playbooks.md 卡④ + technical/site-type-templates.md):
  §1 NAP 一致性 —— 页内 name/addr/电话与参数比对。归一化:NFKC 全半角折叠;套房号
      变体(suite/ste/apt/apartment/unit/room/rm/floor/fl/#/室/号/栋/幢/楼 及其后随
      编号整簇剔除)后 token 比对;电话仅取数字(>10 位取末 10 位,US 中心口径);
      店名剔除 LLC/Inc/Ltd/Co/Corp/有限公司 等法律后缀。
  §2 GBP 页抓取检查 —— 类别/评价数/营业时间块/照片数。GBP 是 JS 重页面:抓得到什么
      查什么,拿不到一律 unverified——不猜、不因抓取形态打 FAIL。
  §3 本地 schema —— 页内 JSON-LD LocalBusiness(含常见子类)必填六件:
      name/address/telephone/geo/openingHours(或 openingHoursSpecification)/url;
      schema.url 与页面 host 不一致 → WARN。
  §4 落地页本地信号 —— city(--city,缺省从 --addr 推断 "City, ST 12345" 形态)在
      <title>/H1 的命中 + 正文密度(次/千字符:≥1.5 ✓ / >0 ⚠ / 0 ✗——城市页正文
      零城市提及是 doorway 信号)。

输出四节检查表(✓/⚠/✗/－unverified)+ --json;
退出码: 0 无 FAIL / 1 有 FAIL / 2 输入错或页面不可达。
网络走模块级 http_fetch()(单点,测试打桩;SSRF:仅 http(s),私网/环回/链路本地/
保留段拒)。"""
import argparse
import ipaddress
import json
import re
import socket
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

SCHEMA_VERSION = 1
UA = "Mozilla/5.0 (compatible; seo-suite-local-audit/1.0)"
FETCH_TIMEOUT = 15.0
PASS, WARN, FAIL, UNVERIFIED = "pass", "warn", "fail", "unverified"
SYMBOL = {PASS: "✓", WARN: "⚠", FAIL: "✗", UNVERIFIED: "－"}

LEGAL_SUFFIXES = {"llc", "inc", "co", "corp", "ltd", "llp", "plc", "gmbh",
                  "company", "limited", "有限公司", "有限责任公司", "股份有限公司", "公司"}
SUITE_MARKERS = {"suite", "ste", "apt", "apartment", "unit", "room", "rm",
                 "floor", "fl", "室", "号", "栋", "幢", "楼"}
LB_SUBTYPES = {
    "restaurant", "foodestablishment", "cafeorcoffeeshop", "bakery", "butchershop",
    "barorpub", "brewery", "winery", "hotel", "hostel", "motel", "bedandbreakfast",
    "dentist", "physician", "medicalclinic", "physiotherapy", "veterinarycare",
    "pharmacy", "plumber", "electrician", "locksmith", "roofingcontractor",
    "hvacbusiness", "housepainter", "movingcompany", "generalcontractor",
    "homeandconstructionbusiness", "legalservice", "attorney", "notary",
    "financialservice", "insuranceagency", "realestateagent", "autorepair",
    "autowash", "gasstation", "hairsalon", "nailsalon", "beautysalon", "dayspa",
    "healthandbeautybusiness", "exercisegym", "drycleaningorlaundry", "petstore",
    "selfstorage", "funeralhome", "church", "school", "store", "boutique",
}
GBP_DAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
            "sunday", "周一", "周二", "周三", "周四", "周五", "周六", "周日"}


class FetchError(Exception):
    pass


# ---------------------------------------------------------------------------
# 网络单点(测试打桩点)+ SSRF 守卫
# ---------------------------------------------------------------------------
def _guard_url(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ("http", "https"):
        raise FetchError("仅接受 http(s) URL,得到 scheme=%r" % (p.scheme or "(空)"))
    host = p.hostname or ""
    if not host:
        raise FetchError("URL 缺主机名")
    try:
        infos = socket.getaddrinfo(host, 443 if p.scheme == "https" else 80)
    except OSError as e:
        raise FetchError("DNS 解析失败 %s: %s" % (host, e))
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified):
            raise FetchError("目标 %s(%s) 属私网/保留/环回段,已拒绝(SSRF 防护)" % (host, ip))


def _decode(raw, headers):
    ct = ""
    try:
        ct = headers.get("Content-Type") or "" if headers else ""
    except Exception:
        ct = ""
    charset = None
    if ct:
        m = re.search(r"charset=([\w\-]+)", ct, re.I)
        if m:
            charset = m.group(1)
    if not charset and raw:
        m = re.search(rb'charset=["\']?([\w\-]+)', raw[:4096], re.I)
        if m:
            charset = m.group(1).decode("ascii", "replace")
    for enc in (charset, "utf-8", "gb18030", "latin-1"):
        if not enc:
            continue
        try:
            return raw.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", "replace")


def http_fetch(url, timeout=FETCH_TIMEOUT, max_bytes=5_000_000):
    """单点网络入口(测试打桩点)。返回 (status, final_url, body_str)。"""
    _guard_url(url)
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.geturl(), _decode(resp.read(max_bytes), resp.headers)
    except urllib.error.HTTPError as e:
        try:
            body = e.read(65536)
        except Exception:
            body = b""
        return e.code, url, _decode(body, getattr(e, "headers", None))


# ---------------------------------------------------------------------------
# HTML 解析(title/H1/正文/tel:/JSON-LD)
# ---------------------------------------------------------------------------
class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.h1_text = ""
        self.text_parts = []
        self.tel_links = []
        self.jsonld = []
        self._in_title = False
        self._in_h1 = 0
        self._skip = 0
        self._ld_buf = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag in ("script", "style"):
            self._skip += 1
            if tag == "script" and "ld+json" in (a.get("type") or "").lower():
                self._ld_buf = []
        elif tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 += 1
        elif tag == "a":
            href = a.get("href") or ""
            if href.lower().startswith("tel:"):
                self.tel_links.append(href[4:])

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self._skip = max(0, self._skip - 1)
            if tag == "script" and self._ld_buf is not None:
                self.jsonld.append("".join(self._ld_buf))
                self._ld_buf = None
        elif tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = max(0, self._in_h1 - 1)

    def handle_data(self, data):
        if self._ld_buf is not None:
            self._ld_buf.append(data)
        if self._skip:
            return
        if self._in_title:
            self.title += data
        if self._in_h1:
            self.h1_text += data
        self.text_parts.append(data)

    @property
    def text(self):
        return " ".join(self.text_parts)


# ---------------------------------------------------------------------------
# 归一化
# ---------------------------------------------------------------------------
def text_tokens(s):
    s = unicodedata.normalize("NFKC", s or "").casefold()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    return s.split()


def norm_name(s):
    toks = [t for t in text_tokens(s) if t not in LEGAL_SUFFIXES]
    return " ".join(toks)


def addr_core_tokens(s):
    """套房号变体(suite/ste/#/室… 及其后随编号)整簇剔除后的核心 token。"""
    toks = text_tokens(s)
    out, i = [], 0
    while i < len(toks):
        if toks[i] in SUITE_MARKERS:
            i += 2                                    # 跳过标记 + 其后的编号/字母
            continue
        out.append(toks[i])
        i += 1
    return out


def canon_phone(s):
    s = unicodedata.normalize("NFKC", s or "")
    digits = re.sub(r"\D", "", s)
    if len(digits) > 10:
        digits = digits[-10:]
    return digits or None


def page_phone_candidates(tel_links, text):
    """tel: 链接 + 正文电话形态;先 NFKC 折叠(全角数字/连字符/＋ 照 §1 同口径)。"""
    flat = unicodedata.normalize("NFKC", text or "")
    cands = [unicodedata.normalize("NFKC", x) for x in tel_links]
    cands += re.findall(r"\+?\d[\d\s().\-–—]{7,}\d", flat)
    out, seen = [], set()
    for c in (canon_phone(x) for x in cands):
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def infer_city(addr):
    for pat in (r",\s*([^,]+?)\s*,\s*[A-Z]{2}\s+\d{5}",
                r",\s*([^,]+?)\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?"):
        m = re.search(pat, addr or "")
        if m:
            return m.group(1).strip()
    return None


def fold(s):
    """NFKC 全半角折叠 + casefold(与 §1 同口径,供 §4 命中检测)。"""
    return unicodedata.normalize("NFKC", s or "").casefold()


def url_host(u):
    try:
        return (urllib.parse.urlsplit(u).hostname or "").lower()
    except ValueError:
        return ""


def detect_url_type(u):
    host = url_host(u)
    if re.search(r"(^|\.)google\.[a-z.]+$", host, re.I) or host == "g.co":
        path = (urllib.parse.urlsplit(u).path or "").lower()
        if not path or "/maps" in path or "/place" in path or "/search" in path:
            return "gbp"
    return "website"


# ---------------------------------------------------------------------------
# GBP 抽取(启发式;拿不到 → None → unverified)
# ---------------------------------------------------------------------------
def _num(x):
    try:
        return int(float(x.replace(",", "")))
    except (TypeError, ValueError):
        return 0


def gbp_signals(html):
    out = {}
    m = re.search(r'"(?:primary_?category|category)"\s*:\s*'
                  r'(?:"([^"]+)"|\{\s*"@type"[^}]*?"name"\s*:\s*"([^"]+)")', html)
    out["category"] = (m.group(1) or m.group(2)).strip() if m else None
    nums = [_num(n) for n in re.findall(
        r"([\d.,]+)\s*(?:reviews?|则评价|条评价|rezensionen?|レビュー)", html, re.I)]
    out["reviews"] = max(nums) if nums else None
    flat = re.sub(r"<[^>]+>", " ", html).casefold()
    out["hours"] = sum(1 for d in GBP_DAYS if d in flat) >= 3
    ph = re.findall(r"([\d.,]+)\s*(?:photos?|张照片|张相片)", html, re.I)
    out["photos"] = max((_num(n) for n in ph), default=None)
    return out


# ---------------------------------------------------------------------------
# LocalBusiness schema
# ---------------------------------------------------------------------------
def find_localbusiness(blocks):
    found, bad = [], 0

    def walk(node):
        if isinstance(node, dict):
            t = node.get("@type")
            types = t if isinstance(t, list) else [t]
            for ty in types:
                if ty and str(ty).split(":")[-1].strip().lower() in ({"localbusiness"} | LB_SUBTYPES):
                    found.append(node)
                    break
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for b in blocks:
        try:
            walk(json.loads(b))
        except Exception:
            bad += 1
    return found, bad


def check_schema(blocks, page_url):
    items = []
    found, bad = find_localbusiness(blocks)
    if bad:
        items.append(dict(id="schema.invalid_jsonld", status=WARN,
                          detail="%d 块 JSON-LD 解析失败(已跳过)" % bad))
    if not found:
        items.append(dict(id="schema.localbusiness", status=FAIL,
                          detail="页内未见 LocalBusiness(含子类)JSON-LD——本地实体六件无处声明"))
        return items
    lb = found[0]
    if len(found) > 1:
        items.append(dict(id="schema.multiple", status=WARN,
                          detail="检出 %d 个 LocalBusiness 节点,取第一个核验" % len(found)))
    req = [("name", ("name",)), ("address", ("address",)),
           ("telephone", ("telephone",)), ("geo", ("geo",)),
           ("openingHours", ("openingHours", "openingHoursSpecification")),
           ("url", ("url",))]
    for label, keys in req:
        val = next((lb.get(k) for k in keys if lb.get(k)), None)
        if not val:
            items.append(dict(id="schema.%s" % label, status=FAIL,
                              detail="LocalBusiness 缺必填 %s(%s)" % (
                                  label, "/".join(keys))))
            continue
        if label == "url":
            h1, h2 = url_host(str(val)), url_host(page_url)
            if h1 and h2 and h1 != h2:
                items.append(dict(id="schema.url", status=WARN,
                                  detail="schema.url host %s ≠ 页面 host %s" % (h1, h2)))
            else:
                items.append(dict(id="schema.url", status=PASS, detail=str(val)[:80]))
        else:
            items.append(dict(id="schema.%s" % label, status=PASS,
                              detail="%s: %s" % (label, json.dumps(val, ensure_ascii=False)[:80])))
    return items


# ---------------------------------------------------------------------------
# 四节构建
# ---------------------------------------------------------------------------
def section_nap(page, name, addr, phone):
    items = []
    page_toks = text_tokens(page.text)
    page_joined = " " + " ".join(page_toks) + " "
    # name
    nn = norm_name(name)
    if not nn:
        items.append(dict(id="nap.name", status=UNVERIFIED, detail="未提供店名参数"))
    elif (" %s " % nn) in page_joined:
        items.append(dict(id="nap.name", status=PASS, detail="页内店名一致(%s)" % nn))
    else:
        items.append(dict(id="nap.name", status=FAIL,
                          detail="页内未见店名 %r(归一化后 %r)" % (name, nn)))
    # address
    core = addr_core_tokens(addr)
    if not core:
        items.append(dict(id="nap.address", status=UNVERIFIED, detail="地址参数归一化后为空"))
    else:
        pset = set(page_toks)
        missing = [t for t in core if t not in pset]
        ratio = 1 - len(missing) / len(core)
        if not missing:
            items.append(dict(id="nap.address", status=PASS,
                              detail="页内地址一致(%d token,套房号已归一)" % len(core)))
        elif ratio >= 0.6:
            items.append(dict(id="nap.address", status=WARN,
                              detail="地址部分匹配 %.0f%%,页内缺 token: %s" % (
                                  ratio * 100, " ".join(missing[:6]))))
        else:
            items.append(dict(id="nap.address", status=FAIL,
                              detail="地址不匹配(仅 %.0f%% token 在页内),缺: %s" % (
                                  ratio * 100, " ".join(missing[:6]))))
    # phone
    cands = page_phone_candidates(page.tel_links, page.text)
    if phone:
        pc = canon_phone(phone)
        if pc and pc in cands:
            items.append(dict(id="nap.phone", status=PASS,
                              detail="页内电话一致(末 10 位 %s)" % pc))
        elif pc and cands:
            items.append(dict(id="nap.phone", status=FAIL,
                              detail="参数电话 %s 不在页内候选(%s)" % (
                                  pc, ", ".join(cands[:3]))))
        else:
            items.append(dict(id="nap.phone", status=FAIL,
                              detail="页内未检出任何电话(tel: 或文本)"))
    else:
        if cands:
            items.append(dict(id="nap.phone", status=UNVERIFIED,
                              detail="未提供 --phone;页内检出 %d 个号码(未比对)" % len(cands)))
        else:
            items.append(dict(id="nap.phone", status=WARN,
                              detail="未提供 --phone 且页内未检出电话——NAP 电话缺位"))
    return items


def section_gbp(url_type, html):
    note_skip = "传入 URL 非 GBP 页——类别/评价数/营业时间/照片需用 GBP 页 URL 复核"
    if url_type != "gbp":
        return [dict(id="gbp.%s" % k, status=UNVERIFIED, detail=note_skip)
                for k in ("category", "reviews", "hours", "photos")]
    sig = gbp_signals(html)
    out = []
    out.append(dict(id="gbp.category", status=PASS if sig["category"] else UNVERIFIED,
                    detail=("类别: %s" % sig["category"]) if sig["category"]
                    else "未抓到类别(JS 重页面常见)——人工在 GBP 后台核对主类目"))
    out.append(dict(id="gbp.reviews", status=PASS if sig["reviews"] else UNVERIFIED,
                    detail=("评价数: %d" % sig["reviews"]) if sig["reviews"]
                    else "未抓到评价数——人工核对(基准线 10 条)"))
    out.append(dict(id="gbp.hours", status=PASS if sig["hours"] else UNVERIFIED,
                    detail="营业时间块在场(≥3 个星期名)" if sig["hours"]
                    else "未抓到营业时间块——人工核对"))
    out.append(dict(id="gbp.photos", status=PASS if sig["photos"] else UNVERIFIED,
                    detail=("照片数: %d" % sig["photos"]) if sig["photos"]
                    else "未抓到照片数——人工核对"))
    return out


def section_local_signals(url_type, page, city):
    if url_type == "gbp":
        note = "GBP 页不承载落地页信号——用官网 URL 复核"
        return [dict(id="local.%s" % k, status=UNVERIFIED, detail=note)
                for k in ("title", "h1", "density")]
    if not city:
        note = "city 未知(--city 缺省且 --addr 推断不出 City, ST ZIP 形态)"
        return [dict(id="local.%s" % k, status=UNVERIFIED, detail=note)
                for k in ("title", "h1", "density")]
    c = fold(city)
    items = []
    title = page.title.strip()
    if not title:
        items.append(dict(id="local.title", status=WARN, detail="无 <title>"))
    else:
        hit = c in fold(title)
        items.append(dict(id="local.title",
                          status=PASS if hit else WARN,
                          detail="title %s: %r" % ("含 city" if hit else "不含 city", title[:60])))
    h1 = page.h1_text.strip()
    if not h1:
        items.append(dict(id="local.h1", status=WARN, detail="无 H1"))
    else:
        hit = c in fold(h1)
        items.append(dict(id="local.h1", status=PASS if hit else WARN,
                          detail="H1 %s: %r" % ("含 city" if hit else "不含 city", h1[:60])))
    text = page.text
    if not text.strip():
        items.append(dict(id="local.density", status=FAIL, detail="正文为空"))
    else:
        dens = fold(text).count(c) / len(text) * 1000
        if dens >= 1.5:
            st, d = PASS, "%.2f 次/千字符" % dens
        elif dens > 0:
            st, d = WARN, "%.2f 次/千字符(<1.5,本地相关性偏弱)" % dens
        else:
            st, d = FAIL, "正文 0 次提及 %s——城市页零本地信号是 doorway 形态" % city
        items.append(dict(id="local.density", status=st, detail=d))
    return items


def render(sections, meta):
    print("=" * 64)
    print("local_audit | %s(%s)" % (meta["url"], "GBP 页" if meta["url_type"] == "gbp" else "官网"))
    titles = {"nap": "§1 NAP 一致性", "gbp": "§2 GBP 页抓取检查",
              "schema": "§3 本地 schema(LocalBusiness 必填)", "local": "§4 落地页本地信号"}
    counts = {PASS: 0, WARN: 0, FAIL: 0, UNVERIFIED: 0}
    for sec in sections:
        print("\n-- %s --" % titles.get(sec["id"], sec["id"]))
        for it in sec["items"]:
            counts[it["status"]] += 1
            print("%s %-14s %s" % (SYMBOL[it["status"]], it["id"], it["detail"]))
    print("\n==== 结果: %d ✓ / %d ⚠ / %d ✗ / %d unverified => %s ====" % (
        counts[PASS], counts[WARN], counts[FAIL], counts[UNVERIFIED],
        "FAIL(退出码 1)" if counts[FAIL] else "PASS(退出码 0)"))
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="local_audit.py",
        description="本地 SEO 四节体检:NAP 一致性 / GBP 抓取 / LocalBusiness schema / 落地页本地信号(stdlib)")
    ap.add_argument("--url", required=True, help="GBP 页或官网 URL(http/https)")
    ap.add_argument("--name", "--n", dest="name", required=True, help="店名(与页内 NAP 比对)")
    ap.add_argument("--addr", dest="addr", required=True, help="地址(套房号变体会归一)")
    ap.add_argument("--city", help="城市名(缺省从 --addr 的 City, ST ZIP 形态推断)")
    ap.add_argument("--phone", help="电话(仅取数字末 10 位比对;缺省只报告页内检出)")
    ap.add_argument("--timeout", type=float, default=FETCH_TIMEOUT, help="抓取超时秒(默认 15)")
    ap.add_argument("--json", dest="as_json", action="store_true", help="结构化输出")
    args = ap.parse_args(argv)

    p = urllib.parse.urlsplit(args.url)
    if p.scheme not in ("http", "https") or not p.netloc:
        sys.stderr.write("[FATAL] --url 仅接受 http(s) URL: %r\n" % args.url)
        return 2
    try:
        status, final_url, html = http_fetch(args.url, timeout=args.timeout)
    except FetchError as e:
        sys.stderr.write("[FATAL] %s\n" % e)
        return 2
    except Exception as e:
        sys.stderr.write("[FATAL] 抓取失败 %s: %s\n" % (args.url, e))
        return 2
    if status != 200:
        sys.stderr.write("[FATAL] 页面 HTTP %d,无法体检\n" % status)
        return 2

    page = PageParser()
    try:
        page.feed(html)
    except Exception:
        pass
    url_type = detect_url_type(final_url or args.url)
    city = args.city or infer_city(args.addr)

    sections = [
        {"id": "nap", "items": section_nap(page, args.name, args.addr, args.phone)},
        {"id": "gbp", "items": section_gbp(url_type, html)},
        {"id": "schema", "items": (
            [dict(id="schema.localbusiness", status=UNVERIFIED,
                  detail="GBP 页不承载站内 JSON-LD——用官网 URL 复核")]
            if url_type == "gbp" else check_schema(page.jsonld, final_url or args.url))},
        {"id": "local", "items": section_local_signals(url_type, page, city)},
    ]
    counts = {s: sum(1 for sec in sections for it in sec["items"] if it["status"] == s)
              for s in (PASS, WARN, FAIL, UNVERIFIED)}
    if args.as_json:
        print(json.dumps({
            "schema_version": SCHEMA_VERSION, "tool": "local_audit",
            "url": args.url, "final_url": final_url, "url_type": url_type,
            "city": city, "counts": counts, "sections": sections,
        }, ensure_ascii=False, indent=1))
    else:
        render(sections, {"url": args.url, "url_type": url_type})
    return 1 if counts[FAIL] else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.stderr.write("\n[interrupted]\n")
        sys.exit(130)
