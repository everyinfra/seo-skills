#!/usr/bin/env python3
"""SEO 六阶段流量漏斗(stdlib only;判定口径=Lumar 官方,见 references/research/borrow-specs.md A1)。
嵌套过滤:availability(HTTP 200 可达)⊃ indexability(无 noindex meta/X-Robots-Tag、未被
robots 屏蔽、canonical 自指)⊃ uniqueness(primary=唯一或重复集内 DeepRank 最高)⊃
in_serps(GSC impressions>0)⊃ with_clicks(GSC clicks>0)⊃ good_ux(LCP≤2.5 且 CLS≤0.1 且
DCL≤1.5;缺 CWV 数据则 N/A 不计入)。
输入:--audit(site_audit.py --json 输出,提供前两层判定;meta.links 为列表时作内链图)/
--gsc(GSC 页面导出 Page/Impressions/Clicks;缺省则漏斗截断到 uniqueness 并输出截断声明)/
--cwv(URL,LCP,CLS,DCL,可选)/ --urls(sitemap 清单:配 --audit 作全站基数输出 coverage
声明[Ryte 官方:样本分不可与全站分直接比较];单独使用时只做可达性抽测)。
uniqueness 实现:每页 title+description 自实现 64 位 Simhash,汉明距离≤3 判重复组
(阈值 3 为自定[推断]——Lumar 未公开相似度算法与阈值);组内 DeepRank=简化 PageRank
(每页初始 1.0,沿内链图迭代 20 轮,值=入链之和;无 links 列表字段时按 URL 深度 1/depth),
最高者为 primary,其余 dropped。SSRF 防御照抄 monitor.py(site_audit.py 未内建):仅
http(s)+拒内网/环回/链路本地,重定向逐跳复查。
用法: python3 traffic_funnel.py --audit audit.json [--gsc gsc.csv] [--cwv cwv.csv] [--urls urls.txt] [--json]
       python3 traffic_funnel.py --urls urls.txt [--json](只做可达性抽测)
判定: 正常输出退出码 0;无 --audit 且无 --urls 退出码 2。"""
import csv
import hashlib
import ipaddress
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; seo-suite-funnel/1.0)"
FETCH_TIMEOUT = 10
UX_LIMITS = {"lcp": 2.5, "cls": 0.1, "dcl": 1.5}     # Lumar good_ux 官方阈值
DEEPRANK_ROUNDS = 20
SIMHASH_BITS = 64
DUP_HAMMING = 3                                      # 自定[推断]:Lumar 未公开
BAR_WIDTH = 24

USAGE = """usage: traffic_funnel.py --audit audit.json [--gsc gsc.csv] [--cwv cwv.csv] [--urls urls.txt] [--json]
       traffic_funnel.py --urls urls.txt [--json]
Lumar 六阶段 SEO 流量漏斗(官方判定):
  availability(HTTP 200)⊃ indexability(无 noindex/未被 robots 屏蔽/canonical 自指)⊃
  uniqueness(Simhash 聚类,组内 DeepRank 最高者为 primary)⊃ in_serps(impressions>0)⊃
  with_clicks(clicks>0)⊃ good_ux(LCP≤2.5 且 CLS≤0.1 且 DCL≤1.5;缺 CWV 数据 N/A 不计入)
  --audit PATH  site_audit.py --json 输出(提供前两层判定;meta.links 为列表时作内链图)
  --gsc   PATH  GSC 页面导出 CSV(Page/Impressions/Clicks);缺省则漏斗截断到 uniqueness 并声明
  --cwv   PATH  Core Web Vitals CSV(URL,LCP,CLS,DCL),可选
  --urls  PATH  sitemap URL 清单:配 --audit 作全站基数出 coverage 声明(Ryte:样本分
                不可与全站分直接比较);单独使用时只做可达性抽测(UA+10s 超时+SSRF 防御)
  --json       结构化输出(stages/coverage/截断声明,供 agent 消费)
每阶段输出 pages_in/pages_through/dropped/drop_rate/cumulative_rate+流失 URL 前 20。"""


# ---------- 工具:URL 归一化 / Simhash / 聚类 / DeepRank ----------

def norm_url(u):
    """跨源 join 归一化:小写 scheme/host、去 fragment、非根路径去尾斜杠;保留 params/query。"""
    p = urllib.parse.urlparse(str(u).strip())
    path = p.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urllib.parse.urlunparse((p.scheme.lower(), p.netloc.lower(), path, p.params, p.query, ""))


def simhash(text, bits=SIMHASH_BITS):
    r"""64 位 Simhash(自实现):token→md5 前 8 字节当 64 位指纹,逐位 ±1 加权,
    各位符号即输出指纹。token=\w+ 序列(小写化;标点/空白差异不改变指纹)。"""
    v = [0] * bits
    for tok in re.findall(r"\w+", text.lower()):
        h = int.from_bytes(hashlib.md5(tok.encode("utf-8")).digest()[:8], "big")
        for i in range(bits):
            v[i] += 1 if h >> i & 1 else -1
    f = 0
    for i in range(bits):
        if v[i] > 0:
            f |= 1 << i
    return f


def hamming(a, b):
    return bin(a ^ b).count("1")


def cluster_by_simhash(sigs, threshold=DUP_HAMMING):
    """单链并查集聚类:汉明距离≤threshold 视为重复(传递闭包:A~B 且 B~C 则同组)。
    返回组列表(组内按 URL 升序,保证确定性)。"""
    parent = {u: u for u in sigs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    urls = sorted(sigs)
    for i, a in enumerate(urls):
        for b in urls[i + 1:]:
            if hamming(sigs[a], sigs[b]) <= threshold:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[rb] = ra
    groups = {}
    for u in urls:
        groups.setdefault(find(u), []).append(u)
    return list(groups.values())


def url_depth(u):
    """URL 深度:"/"=1,每加一段路径 +1("/a"=2,"/a/b"=3)——无内链图时的静态 DeepRank 基数。"""
    segs = [s for s in urllib.parse.urlparse(u).path.split("/") if s]
    return len(segs) + 1 if segs else 1


def deeprank(pages, rounds=DEEPRANK_ROUNDS):
    """简化 PageRank(spec 口径,无阻尼系数):每页初始 1.0,每轮新值=入链之和;
    audit JSON 任一页提供 links 列表字段(本页出链)即启用图迭代,否则静态 1/depth。
    注意:无阻尼下 DAG 尾部 20 轮后衰减到 0(导航环——真实站常见——保持稳定);
    指向集合外/自指的边忽略;平票由调用方按 URL 序决,保证确定性。"""
    urls = list(pages)
    incoming = {u: [] for u in urls}                 # target -> [source]
    known = {norm_url(u) for u in urls}
    has_graph = False
    for u, e in pages.items():
        links = e.get("links")
        if not isinstance(links, list):
            links = (e.get("meta") or {}).get("links")
        if isinstance(links, list):
            has_graph = True
            for tgt in links:
                t = norm_url(urllib.parse.urljoin(u, str(tgt)))
                if t in known and t != norm_url(u):
                    incoming[t].append(u)
    if not has_graph:
        return {u: 1.0 / url_depth(u) for u in urls}
    rank = {u: 1.0 for u in urls}
    for _ in range(rounds):
        rank = {u: sum(rank[src] for src in incoming[u]) for u in urls}
    return rank


# ---------- 输入加载 ----------

def load_audit(path):
    """site_audit.py --json 输出(注意其 stdout 在 JSON 块前还有逐 URL 文本行,
    故先整体 parse,失败再从行首 '{' 处截取)。返回 {url: entry} 保序 dict。"""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    data = None
    for start in (0, raw.find("\n{"), raw.rfind("\n{")):
        if start < 0:
            continue
        try:
            data = json.loads(raw[start:] if start else raw)
            break
        except ValueError:
            continue
    if not isinstance(data, dict):
        sys.exit("audit JSON 无法解析:期望 site_audit.py --json 的 {results:{url:entry}} 结构")
    results = data["results"] if "results" in data else data
    if not isinstance(results, dict):
        sys.exit("audit JSON 无法解析:results 非页面对象")
    return results


def load_gsc(path):
    """GSC 页面级导出:列 Page/Impressions/Clicks(大小写不敏感,列序无关);
    同 URL 多行(按词导出)累加。"""
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        cols = {c.strip().lower(): c for c in rd.fieldnames or [] if c}
        pc = cols.get("page") or cols.get("url")
        ic, cc = cols.get("impressions"), cols.get("clicks")
        if not (pc and ic and cc):
            sys.exit("GSC CSV 缺 Page/Impressions/Clicks 列(实际列:%s)" % (rd.fieldnames,))
        for row in rd:
            u = norm_url(row.get(pc) or "")
            if not u:
                continue
            d = out.setdefault(u, {"impressions": 0.0, "clicks": 0.0})
            d["impressions"] += _num(row.get(ic))
            d["clicks"] += _num(row.get(cc))
    return out


def _num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


def load_cwv(path):
    """CWV CSV:URL,LCP,CLS,DCL(带表头;空单元格→None=该指标缺失)。"""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.reader(f) if r and any(c.strip() for c in r)]
    if rows and any(c.strip().lower() in ("url", "page", "lcp", "cls", "dcl") for c in rows[0]):
        rows = rows[1:]
    out = {}
    for r in rows:
        vals = []
        for c in r[1:4]:
            c = (c or "").strip()
            vals.append(float(c.replace(",", "")) if c else None)
        out[norm_url(r[0])] = dict(zip(("lcp", "cls", "dcl"), vals + [None] * (3 - len(vals))))
    return out


def load_urls(path):
    """sitemap URL 清单:每行一个 URL,空行/# 注释跳过。"""
    with open(path, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]


# ---------- 六阶段判定 ----------

def page_text(entry):
    m = entry.get("meta") or {}
    return "%s %s" % (entry.get("title") or m.get("title") or "",
                      entry.get("description") or m.get("desc") or m.get("description") or "")


def availability(entry):
    """availability=HTTP 200 可达:site_audit verdict refused(挑战页守卫)或 fetch 告警 → 不可达。"""
    if entry.get("available") is False:
        return False, "available=false(显式标记)"
    if entry.get("verdict") == "refused":
        return False, "refused(fetch guard:疑似挑战页/响应过小,拒绝判定)"
    for f in entry.get("findings") or []:
        if (f.get("area") or "") == "fetch":
            return False, "fetch: %s" % f.get("message", "")
    return True, None


def indexability(entry, url):
    """indexability:无 noindex(meta/X-Robots-Tag)、未被 robots 屏蔽、canonical 自指。
    判定来源=site_audit findings + 可选显式字段(indexable/robots_blocked/meta.canonical)。"""
    if entry.get("indexable") is False:
        return False, "indexable=false(显式标记)"
    if entry.get("robots_blocked"):
        return False, "robots 屏蔽(显式标记)"
    for f in entry.get("findings") or []:
        area = (f.get("area") or "").lower()
        msg = (f.get("message") or "").lower()
        if area == "robots":
            if "noindex" in msg:
                return False, "noindex(meta robots / X-Robots-Tag)"
            if any(k in msg for k in ("被禁", "屏蔽", "blocked", "disallow")):
                return False, "robots 屏蔽: %s" % f.get("message", "")
        if area == "canonical" and "指向外域" in msg:
            return False, "canonical 指向外域(非自指)"
    canon = entry.get("canonical") or (entry.get("meta") or {}).get("canonical")
    if canon and norm_url(urllib.parse.urljoin(url, str(canon))) != norm_url(url):
        return False, "canonical 非自指 → %s" % canon
    return True, None


def ux_state(url, cwv):
    """good_ux:LCP≤2.5 且 CLS≤0.1 且 DCL≤1.5;任一指标缺失 → N/A 不计入本阶段。"""
    m = (cwv or {}).get(norm_url(url))
    if not m or any(m.get(k) is None for k in UX_LIMITS):
        return "na", "缺 CWV 数据(LCP/CLS/DCL 不全)→ N/A 不计入"
    fails = ["%s %g>%g" % (k.upper(), m[k], v) for k, v in UX_LIMITS.items() if m[k] > v]
    return ("fail", "; ".join(fails)) if fails else ("pass", None)


def compute_funnel(pages, gsc=None, cwv=None):
    """六阶段嵌套过滤;返回 (stages, funnel_truncated_at)。"""
    entered = list(pages)
    total = len(entered)
    ranks = deeprank(pages)
    stages, cur, truncated = [], entered[:], None

    def add(name, inp, keep, reasons, extra=None):
        keepset = set(keep)
        dropped = [u for u in inp if u not in keepset]
        rec = {"stage": name, "pages_in": len(inp), "pages_through": len(keep),
               "dropped": len(dropped),
               "drop_rate": round(len(dropped) / len(inp), 4) if inp else None,
               "cumulative_rate": round(len(keep) / total, 4) if total else None,
               "dropped_total": len(dropped),
               "dropped_urls": [{"url": u, "reason": reasons.get(u, "")} for u in dropped[:20]]}
        if extra:
            rec.update(extra)
        stages.append(rec)
        return [u for u in inp if u in keepset]

    keep, reasons = [], {}
    for u in cur:
        ok, why = availability(pages[u])
        (keep.append(u) if ok else reasons.__setitem__(u, why))
    cur = add("availability", cur, keep, reasons)

    keep, reasons = [], {}
    for u in cur:
        ok, why = indexability(pages[u], u)
        (keep.append(u) if ok else reasons.__setitem__(u, why))
    cur = add("indexability", cur, keep, reasons)

    # uniqueness:title+description Simhash 聚类;空文本页不参与聚类(缺 title/desc≠重复)
    sigs = {u: (simhash(page_text(pages[u])) if page_text(pages[u]).strip() else None) for u in cur}
    reasons = {}
    for group in cluster_by_simhash({u: s for u, s in sigs.items() if s is not None}):
        if len(group) < 2:
            continue
        primary = max(group, key=lambda u: ranks[u])   # 平票取 URL 序在前(max 取首个最大)
        for u in group:
            if u != primary:
                reasons[u] = "重复组(×%d)非 primary:DeepRank %g,primary %s=%g" % (
                    len(group), ranks[u], primary, ranks[primary])
    cur = add("uniqueness", cur, [u for u in cur if u not in reasons], reasons)

    if gsc is None:                                    # 无 GSC → 截断声明,后续阶段 null
        truncated = "uniqueness"
        for name in ("in_serps", "with_clicks", "good_ux"):
            stages.append({"stage": name, "pages_in": None, "pages_through": None,
                           "dropped": None, "drop_rate": None, "cumulative_rate": None,
                           "dropped_total": None, "dropped_urls": []})
        return stages, truncated

    keep, reasons = [], {}
    for u in cur:
        if gsc.get(norm_url(u), {}).get("impressions", 0.0) > 0:
            keep.append(u)
        else:
            reasons[u] = ("GSC impressions=0" if norm_url(u) in gsc
                          else "不在 GSC 导出(按 impressions=0)")
    cur = add("in_serps", cur, keep, reasons)

    keep, reasons = [], {}
    for u in cur:
        if gsc.get(norm_url(u), {}).get("clicks", 0.0) > 0:
            keep.append(u)
        else:
            reasons[u] = "GSC clicks=0"
    cur = add("with_clicks", cur, keep, reasons)

    evaluated = [u for u in cur if ux_state(u, cwv)[0] != "na"]
    keep, reasons, na = [], {}, 0
    for u in cur:
        st, why = ux_state(u, cwv)
        if st == "na":
            na += 1
        elif st == "pass":
            keep.append(u)
        else:
            reasons[u] = why
    extra = {"pages_na": na}
    if na:
        extra["note"] = "%d 页缺 CWV 数据(LCP/CLS/DCL 不全):N/A 不计入本阶段" % na
    add("good_ux", evaluated, keep, reasons, extra)
    return stages, truncated


def compute_report(pages, gsc=None, cwv=None):
    stages, truncated = compute_funnel(pages, gsc, cwv)
    entered = len(pages)
    evaluated = [s for s in stages if s["pages_in"]]   # 最后一个真正评估过的阶段
    through = evaluated[-1]["pages_through"] if evaluated else 0
    return {"tool": "traffic_funnel", "mode": "funnel", "entered": entered, "through": through,
            "cumulative_rate": round(through / entered, 4) if entered else None,
            "funnel_truncated_at": truncated, "coverage": None, "stages": stages}


# ---------- --urls 模式:可达性抽测(SSRF 防御照抄 monitor.py) ----------

class GuardError(Exception):
    pass


_ssrf_cache = {}


def ssrf_guard(host):
    """仅 http(s)+拒私网/环回/链路本地/保留/组播;结果按 host 缓存。
    198.18.0.0/15(RFC2544)豁免本机 fake-IP 代理;SEO_FUNNEL_STRICT_SSRF=1 恢复全拒。"""
    if not host:
        raise GuardError("empty host")
    if host in _ssrf_cache:
        return
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError as e:
        raise GuardError("DNS 解析失败 %s: %s" % (host, e))
    strict = bool(os.environ.get("SEO_FUNNEL_STRICT_SSRF"))
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if ip in ipaddress.ip_network("198.18.0.0/15"):
            if not strict:
                continue
            raise GuardError("SSRF guard: 非公网地址 %s(strict 模式拒 fake-IP 段)" % ip)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise GuardError("SSRF guard: 非公网地址 %s" % ip)
    _ssrf_cache[host] = True


class _RedirectGuard(urllib.request.HTTPRedirectHandler):
    """重定向逐跳 SSRF 复查(照抄 monitor.py:urlopen 自动跟 302 时最终 host 从不复查)。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urllib.parse.urlparse(newurl)
        if p.scheme not in ("http", "https"):
            raise GuardError("重定向到非 http(s) 被拒: %s" % newurl)
        ssrf_guard(p.hostname)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_RedirectGuard)


def fetch(url, timeout=FETCH_TIMEOUT):
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        raise GuardError("仅允许 http(s): %s" % url)
    ssrf_guard(p.hostname)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with _opener.open(req, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read(2_000_000).decode("utf-8", "replace")


def availability_sample(urls, timeout=FETCH_TIMEOUT):
    """--urls 模式:无 audit JSON,只做可达性抽测;输出单阶段漏斗+样本口径声明。"""
    keep, reasons, checked = [], {}, []
    for u in urls:
        try:
            st, _, _ = fetch(u, timeout=timeout)
            ok = st == 200
            reasons[u] = None if ok else "HTTP %s(非 200)" % st
        except urllib.error.HTTPError as e:
            ok, reasons[u] = False, "HTTP %s" % e.code
        except Exception as e:
            ok, reasons[u] = False, "%s" % e
        if ok:
            keep.append(u)
        checked.append({"url": u, "ok": ok, "reason": reasons[u] or ""})
    entered = len(urls)
    rec = {"stage": "availability", "pages_in": entered, "pages_through": len(keep),
           "dropped": entered - len(keep),
           "drop_rate": round((entered - len(keep)) / entered, 4) if entered else None,
           "cumulative_rate": round(len(keep) / entered, 4) if entered else None,
           "dropped_total": entered - len(keep),
           "dropped_urls": [{"url": u, "reason": reasons[u] or ""} for u in urls
                            if reasons.get(u)][:20]}
    return {"tool": "traffic_funnel", "mode": "availability_sample", "entered": entered,
            "through": len(keep),
            "cumulative_rate": round(len(keep) / entered, 4) if entered else None,
            "funnel_truncated_at": None,
            "coverage": {"sample": entered, "site": None, "coverage_ratio": None,
                         "note": "可达性抽测为样本口径(Ryte):样本分不可与全站分直接比较"},
            "stages": [rec], "checked_urls": checked}


def coverage_note(sample, site):
    """样本<全站时的 Ryte 官方降级声明:两次分数不可比,必须显式输出 coverage_ratio。"""
    if not site or sample >= site:
        return None
    return {"sample": sample, "site": site, "coverage_ratio": round(sample / site, 4),
            "note": "审计样本 %d/%d 页<全站清单(Ryte 官方):样本分不可与全站分直接比较" % (sample, site)}


# ---------- 渲染 ----------

def pct(x):
    return "n/a" if x is None else "%.1f%%" % (x * 100)


def render_markdown(rep):
    L = []
    L.append("## 可达性抽测(--urls 模式)" if rep.get("mode") == "availability_sample"
             else "## SEO 流量漏斗(Lumar 六阶段判定)")
    L.append("")
    L.append("进入 %d 页 → 最终通过 %d 页(累计通过率 %s)" % (
        rep["entered"], rep["through"], pct(rep["cumulative_rate"])))
    L.append("")
    for s in rep["stages"]:
        name = s["stage"].ljust(14)
        if s["pages_in"] is None:
            L.append("%s(截断:null)" % name)
            continue
        frac = s["pages_through"] / rep["entered"] if rep["entered"] else 0
        bar = "█" * int(round(BAR_WIDTH * frac))
        L.append("%s%-*s %d/%d 通过 · 流失 %d(%s)· 累计 %s" % (
            name, BAR_WIDTH, bar, s["pages_through"], s["pages_in"], s["dropped"],
            pct(s["drop_rate"]), pct(s["cumulative_rate"])))
        if s.get("pages_na"):
            L.append("              ↳ %d 页缺 CWV 数据:N/A 不计入本阶段" % s["pages_na"])
    if rep.get("funnel_truncated_at"):
        L.append("")
        L.append("> ⚠ 漏斗截断于 %s:未提供 --gsc(GSC 数据缺席),in_serps/with_clicks/good_ux 判定为 null"
                 % rep["funnel_truncated_at"])
    cov = rep.get("coverage")
    if cov:
        L.append("")
        if cov.get("coverage_ratio") is not None:
            L.append("> 覆盖率声明(Ryte):样本 %d/%d 页(coverage_ratio %s)——样本分不可与全站分直接比较"
                     % (cov["sample"], cov["site"], cov["coverage_ratio"]))
        else:
            L.append("> 覆盖率声明(Ryte):%s" % cov.get("note", ""))
    shown = [s for s in rep["stages"] if s.get("dropped")]
    if shown:
        L.append("")
        L.append("### 流失 URL 清单(每阶段前 20)")
        for s in shown:
            L.append("")
            L.append("#### %s:流失 %d" % (s["stage"], s["dropped"]))
            for d in s["dropped_urls"]:
                L.append("- %s — %s" % (d["url"], d["reason"]))
    if rep.get("mode") == "availability_sample":
        L.append("")
        L.append("### 逐 URL 抽测结果")
        for c in rep["checked_urls"]:
            L.append("- %s %s%s" % ("✓" if c["ok"] else "✗", c["url"],
                                    "" if c["ok"] else " — %s" % c["reason"]))
    return "\n".join(L)


# ---------- main ----------

def main():
    args = sys.argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(USAGE)
        return 0
    want = {"--audit": None, "--gsc": None, "--cwv": None, "--urls": None}
    as_json = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--json":
            as_json = True
        elif a in want:
            if i + 1 >= len(args):
                sys.exit("usage 错误:%s 需要一个路径参数(见 --help)" % a)
            want[a] = args[i + 1]
            i += 1
        else:
            sys.stderr.write("未知参数 %s\n%s\n" % (a, USAGE))
            return 2
        i += 1
    if not want["--audit"] and not want["--urls"]:
        sys.stderr.write("需要 --audit 或 --urls 至少一项\n\n" + USAGE + "\n")
        return 2
    if want["--audit"]:
        pages = load_audit(want["--audit"])
        gsc = load_gsc(want["--gsc"]) if want["--gsc"] else None
        cwv = load_cwv(want["--cwv"]) if want["--cwv"] else None
        rep = compute_report(pages, gsc, cwv)
        if want["--urls"]:
            rep["coverage"] = coverage_note(len(pages), len(load_urls(want["--urls"])))
    else:
        rep = availability_sample(load_urls(want["--urls"]))
    if as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(render_markdown(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
