#!/usr/bin/env python3
"""pSEO 模式挖掘器(stdlib,pSEO 生产线第 1 件)。GSC queries 导出 → 按正则模式聚类 →
每模式聚合(变体数/曝光证据/URL 覆盖度/addressable 估算)→ 按 gates §八权重打分 →
GO / WATCH / 白空间 三态判定。规格:references/overview/pipeline-completeness.md R3-1 +
references/technical/programmatic-seo-gates.md §八(模式评分权重 30/25/20/15/10) +
references/technical/programmatic-seo-playbook.md §一(查询模式正则表/收口门槛)。

用法:
  python3 pseo_pattern_mining.py --gsc queries.csv                       # 只聚类+打分
  python3 pseo_pattern_mining.py --gsc queries.csv --urls urls.txt       # + 自站 URL 覆盖度
  python3 pseo_pattern_mining.py --gsc queries.csv --sitemap https://example.com/sitemap.xml
  python3 pseo_pattern_mining.py --gsc queries.csv --urls urls.txt --json

管线:
  ① 查询逐条归一(NFKC 全半角/casefold/versus→vs/全角空格/尾标点,CJK 容错)后按
     PATTERNS 顺序首匹配聚类——每模式带捕获组(=数据轴:竞品名/人群/城市…)。
  ② 每模式聚合:变体数(去重查询)/总曝光/URL 覆盖度(--sitemap 或 --urls 的路径正则
     首匹配计账;/blog//news/ 编辑页按 gates §八排除)/addressable = 变体数×模式均量
     (均量=有曝光变体的均曝光;全有曝光时≈总曝光,GSC 只见已展示词,方向性下限)。
  ③ 打分(0-100,五维累加,gates §八权重):
       搜索需求 30(addressable 量分档 30/24/19/15/11/7/3/1)
       意图质量 25(vs/alternative=25 高购买…glossary=5 低,按模式常量)
       模板可行性 20(vs 蓝图=20/near me 仅真实本地存在=8,按模式常量)
       数据可得性 15(捕获组去重实体数 ≥5→15/≥3→12/==2→9/==1→6/0→0)
       竞争缺口 10(自站覆盖代理:0 覆盖→10/1-2→7/覆盖<变体→5/已盖满→2;
         真竞品缺口需竞品 sitemap 逆向,此处为方向性代理,明标)
  ④ 门槛:score≥50 且 变体≥3 → GO;变体<3 → 白空间(先 5-10 页手工验证需求,
     playbook §一收口:GSC 上看不到 ≥3 个同模式真实变体=白空间);其余 WATCH。

输出:模式排行 markdown(模式/变体/曝光/覆盖/addressable/score/判定)+ --json 结构化。
安全:--sitemap 仅 http(s)、SSRF 防护(私网/环回/链路本地拒连,重定向逐跳复查);
离线场景用 --urls 本地清单。退出码:0 正常;2 输入坏(缺 query 列/文件不可读/非 http(s))。
"""
import argparse
import csv
import ipaddress
import json
import os
import re
import socket
import sys
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

UA = "Mozilla/5.0 (compatible: seo-suite-pseo-pattern/1.0)"

# ─────────────────────────────────────────────────────────────────────────────
# 模式正则表(playbook §一查询表 + gates §八 URL 表 + CJK 基础表,顺序=优先级:
# 特异在前(vs/best-for/how-to-with 先于 best/for-y/local-in),查询与 URL 路径
# 同序首匹配。元组:(id, 标签, [(查询正则, 语种), …], 意图分, 模板分, 捕获组标签,
# URL 路径正则或 None)。中文变体与对应英文模式合一行——同模式同一批页面承接。
PATTERNS = [
    ("vs", "对比 vs",
     [(r"(.{1,50}?) vs\.? (.{1,50})", "en"),
      (r"(.{2,40}?)(?:和|与|还是)(.{2,40}?)(?:哪个好|哪个更好|怎么选|更值得)", "zh"),
      (r"(.{2,40}?)对比(.{2,40})", "zh")],
     25, 20, ("对比方", "被对比方"), r"/(?:vs|compare)(?:/|$)"),
    ("alternative", "替代 alternative",
     [(r"(.{1,50}?) alternatives?", "en"),
      (r"alternatives? to (.{1,50})", "en"),
      (r"(.{1,40}?)的?(?:替代品|平替|替代)", "zh")],
     25, 18, ("被替代品",), r"/alternatives?(?:/|-to|$)"),
    ("best_for", "垂直清单 best-for",
     [(r"best (.{1,40}?) for (.{1,40})", "en")],
     15, 14, ("对象", "人群"), r"/(?:for-|solutions?/)"),
    ("howto_with", "集成指南 how-to-with",
     [(r"how to (.{1,50}?) with (.{1,50})", "en"),
      (r"how to connect (.{1,40}?) to (.{1,40})", "en")],
     20, 16, ("任务", "工具"), r"/how-to"),
    ("integration", "集成 integrations",
     [(r"(.{1,50}?) integrations?", "en"),
      (r"(.{1,40}?) (.{1,40}?) integration", "en"),
      (r"(.{1,40}?)(?:集成|对接)", "zh")],
     20, 18, ("工具", "工具对"), r"/integrations?(?:/|$)"),
    ("worth", "值不值 is-worth",
     [(r"is (.{1,50}?) worth", "en"),
      (r"(.{1,40}?)(?:值得买吗|值得吗|好吗|怎么样)", "zh")],
     15, 13, ("标的",), r"(?:/|-)(?:worth|reviews?)(?:/|-|$)"),
    ("near_me", "本地 near-me",
     [(r"(.{1,50}?) near me", "en"),
      (r"(.{1,40}?)(?:附近|周边)", "zh")],
     20, 8, ("地点需求",), r"/(?:near-?me|locations?)(?:/|-|$)"),
    ("beginners", "新手 beginners",
     [(r"(.{1,50}?) for beginners", "en"),
      (r"(.{1,40}?)(?:新手入门|入门|新手)", "zh")],
     12, 14, ("主题",), r"for-beginners(?:/|$)|/beginners?(?:/|-|$)"),
    ("pricing", "价格 pricing",
     [(r"(.{1,50}?) (?:pricing|prices?|costs?)", "en"),
      (r"(.{1,40}?)(?:多少钱|价格|收费标准|收费|贵不贵|贵吗)", "zh")],
     23, 15, ("产品",), r"(?:^|/|-)(?:pricing|prices?|cost)(?:/|-|$)"),
    ("best", "清单 best",
     [(r"best (.{1,50})", "en"),
      (r"最好的?(.{1,40})", "zh"),
      (r"(.{1,40}?)(?:排行榜|排名|前十|推荐)", "zh")],
     12, 14, ("对象",), r"(?:^|/)(?:best|top)-"),
    ("glossary", "术语 what-is",
     [(r"what (?:is|are) (.{1,50})", "en"),
      (r"什么是(.{1,50})", "zh"),
      (r"(.{1,50}?)是什么", "zh")],
     5, 12, ("术语",), r"/(?:glossary|what-is)(?:/|-|$)"),
    ("howto", "教程 how-to",
     [(r"how to (.{1,60})", "en"),
      (r"如何(.{1,50})", "zh"),
      (r"(.{1,40}?)怎么用", "zh"),
      (r"(.{1,40}?)教程", "zh")],
     10, 15, ("任务",), r"(?:/|-)(?:how-to|guides?|tutorials?)(?:/|-|$)"),
    ("template", "模板 template",
     [(r"(.{1,50}?) templates?", "en"),
      (r"(.{1,50}?) examples?", "en"),
      (r"(.{1,40}?)(?:模板|范例|案例)", "zh")],
     12, 18, ("模板类型",), r"(?:^|/|-)(?:templates?|examples?)(?:/|-|$)"),
    ("conversion", "换算 x-to-y",
     [(r"(.{1,30}?) to (.{1,30})", "en")],
     8, 20, ("源值", "目标值"), r"(?:^|/|-)to(?:/|-|$)|/(?:convert\w*|calculator)(?:/|-|$)"),
    ("for_y", "垂直人群 for-y",
     [(r"(.{1,50}?) for (.{1,50})", "en")],
     15, 14, ("工具", "人群"), r"/(?:for-|solutions?/)"),  # 与 best_for 同路径:垂直页族,覆盖并计
    ("local_in", "本地 in-y",
     [(r"(.{1,50}?) in (.{1,50})", "en")],
     20, 8, ("对象", "城市"), None),  # 城市页路径无通用形,覆盖恒 0(缺口按全开计)
]
_PAT = [(i, lbl, [(re.compile(rx), lang) for rx, lang in rxs], it, fz, grp,
         re.compile(prx) if prx else None)
        for i, lbl, rxs, it, fz, grp, prx in PATTERNS]

# gates §八:/blog/.* 为编辑内容,排除出 pSEO 分析
EDITORIAL_RX = re.compile(r"/(?:blog|news|articles?)(?:/|$)")

# 路径正则完全相同的模式视为同一 URL 页族(如 best_for/for_y 同为 /for- 垂直页),
# 覆盖度并计;不同正则之间按 PATTERNS 顺序首匹配(如 /alternative-to-x 归 alternative 不归换算)
_PATH_GROUPS = None


def path_groups():
    global _PATH_GROUPS
    if _PATH_GROUPS is None:
        g = defaultdict(list)
        for pid, _lbl, _rxs, _it, _fz, _grp, prx in _PAT:
            if prx:
                g[prx.pattern].append(pid)
        _PATH_GROUPS = dict(g)
    return _PATH_GROUPS

# GSC 列头容错(前缀双向匹配,兼容中英 UI 导出与旧版"Top queries")
COL_ALIASES = {
    "query": ("query", "queries", "top queries", "热门查询", "查询", "查询词", "keyword", "关键词"),
    "impressions": ("impressions", "impr", "展示次数", "曝光次数", "曝光", "展示"),
    "clicks": ("clicks", "click", "点击次数", "点击"),
    "position": ("position", "pos", "平均排名", "排名"),
}

WEIGHTS = {"demand": 30, "intent": 25, "feasibility": 20, "data": 15, "gap": 10}


# ─────────────────────────────────────────────────────────────────────────────
# 查询归一与模式匹配(CJK 容错)
def normalize_query(q):
    """NFKC 全半角归一(ＶＳ→vs/全角空格)+ casefold + versus/vs. 折叠 + 尾标点剥离。"""
    s = unicodedata.normalize("NFKC", q or "")
    s = s.casefold()
    s = re.sub(r"\bversus\b", "vs", s)
    s = s.replace("vs.", "vs")
    s = re.sub(r"[\s\u3000]+", " ", s).strip()
    return s.rstrip("?!。.,!~·-—\u3000 ")


def match_query(q):
    """→ (pattern_id, [捕获组…], 语种) 或 None。顺序首匹配,特异模式在前。"""
    s = normalize_query(q)
    if not s:
        return None
    for pid, _lbl, rxs, _it, _fz, _grp, _prx in _PAT:
        for rx, lang in rxs:
            m = rx.search(s)
            if m:
                return pid, [g.strip() for g in m.groups() if g], lang
    return None


# ─────────────────────────────────────────────────────────────────────────────
# GSC 导出读取(列头容错)
def _match_col(headers, field):
    """按别名前缀双向匹配列名;→ 列索引或 None。"""
    for idx, h in enumerate(headers):
        key = normalize_query(h)
        for alias in COL_ALIASES[field]:
            a = normalize_query(alias)
            if key == a or (len(key) >= 2 and (key.startswith(a) or a.startswith(key))):
                return idx
    return None


def read_gsc(path):
    """→ ({query: {"impressions": n, "clicks": n}}, 列头行)。缺 query 列 → ValueError。"""
    with open(path, newline="", encoding="utf-8-sig") as f:
        first = f.readline()
        delim = max(",\t;", key=lambda d: first.count(d))
        f.seek(0)
        rows = list(csv.reader(f, delimiter=delim))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        raise ValueError("空文件")
    headers = rows[0]
    qi = _match_col(headers, "query")
    if qi is None:
        raise ValueError("缺 query 列(识别到的列头: %s)" % ",".join(h.strip() or "?" for h in headers))
    ii = _match_col(headers, "impressions")
    ci = _match_col(headers, "clicks")

    def num(cell):
        try:
            return float(re.sub(r"[,\s]", "", cell) or 0)
        except ValueError:
            return 0.0

    agg = {}
    for r in rows[1:]:
        if len(r) <= qi:
            continue
        q = r[qi].strip()
        if not q:
            continue
        d = agg.setdefault(q, {"impressions": 0.0, "clicks": 0.0})
        if ii is not None and len(r) > ii:
            d["impressions"] += num(r[ii])
        if ci is not None and len(r) > ci:
            d["clicks"] += num(r[ci])
    return agg, headers


# ─────────────────────────────────────────────────────────────────────────────
# URL 覆盖度(--urls 本地清单 / --sitemap SSRF 防护抓取)
class FetchError(Exception):
    pass


_ssrf_cache = {}


def ssrf_guard(host):
    """仅 http(s) + 拒私网/环回/链路本地/保留段(llmstxt.py 同款,内嵌不 import)。
    198.18.0.0/15 fake-IP 代理段豁免(SEO_MONITOR_STRICT_SSRF=1 恢复全拒)。"""
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
        if ip in ipaddress.ip_network("198.18.0.0/15") and not strict:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise FetchError("SSRF guard: 非公网地址 %s" % ip)
    _ssrf_cache[host] = True


class _RedirectGuard(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urllib.parse.urlparse(newurl)
        if p.scheme not in ("http", "https"):
            raise FetchError("重定向到非 http(s) 被拒: %s" % newurl)
        ssrf_guard(p.hostname)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_RedirectGuard)


def fetch(url, max_bytes=5_000_000, timeout=15.0):
    """唯一网络出口(测试打桩点)。仅 http(s) + SSRF 防护。"""
    if urllib.parse.urlparse(url).scheme not in ("http", "https"):
        raise FetchError("仅允许 http(s) URL: %s" % url)
    ssrf_guard(urllib.parse.urlparse(url).hostname)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with _opener.open(req, timeout=timeout) as r:
        return r.status, r.read(max_bytes).decode("utf-8", "replace")


def parse_locs(xml_text, max_locs=50000):
    """urlset/sitemapindex → loc 列表;index 递归一层由 fetch_sitemap 做,此处只解析一层。"""
    out = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return out
    is_index = root.tag.endswith("sitemapindex")
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == ("sitemap" if is_index else "url"):
            for c in el:
                if c.tag.rsplit("}", 1)[-1] == "loc" and c.text and c.text.strip():
                    out.append(c.text.strip())
                    if len(out) >= max_locs:
                        return out
    return out


def fetch_sitemap(url, max_locs=50000):
    """抓 sitemap(http(s) only);sitemapindex 递归 1 层(子层再嵌 index 不下钻,提示)。"""
    _status, body = fetch(url)
    locs = parse_locs(body)
    if not locs:  # 可能是 index(解析层已按 sitemapindex 分支出子 sitemap loc)
        return []
    children = [u for u in locs if u.split("?")[0].rstrip("/").endswith((".xml", ".xml.gz"))]
    if not children:
        return locs[:max_locs]
    all_locs, seen = [], set()
    for child in children:
        try:
            _s, cbody = fetch(child)
        except Exception as e:  # 子图不可达不致命
            print("[warn] 子 sitemap 不可达 %s: %s" % (child, e), file=sys.stderr)
            continue
        for loc in parse_locs(cbody):
            if loc not in seen:
                seen.add(loc)
                all_locs.append(loc)
                if len(all_locs) >= max_locs:
                    return all_locs
    return all_locs


def load_urls_file(path):
    """URL 清单(每行一条;绝对 URL 或裸路径均可)。"""
    out = []
    with open(path, encoding="utf-8-sig") as f:
        for ln in f:
            u = ln.strip()
            if u and not u.startswith("#"):
                out.append(u)
    return out


def url_path(u):
    """URL/裸路径 → 小写 path(query/fragment 剥离)。"""
    u = u.strip()
    if not u.lower().startswith(("http://", "https://")):
        return urllib.parse.urlparse("https://x.dev" + (u if u.startswith("/") else "/" + u)).path.lower()
    return urllib.parse.urlparse(u).path.lower() or "/"


def coverage_map(urls):
    """路径正则首匹配计账(顺序同 PATTERNS;编辑页先排除;同正则页族并计)。
    → (每模式 URL 数, 编辑排除数, 每模式样例路径)。"""
    cov = defaultdict(int)
    samples = defaultdict(list)
    groups = path_groups()
    editorial = 0
    for u in urls:
        p = url_path(u)
        if EDITORIAL_RX.search(p):
            editorial += 1
            continue
        for pid, _lbl, _rxs, _it, _fz, _grp, prx in _PAT:
            if prx and prx.search(p):
                for member in groups[prx.pattern]:
                    cov[member] += 1
                    if len(samples[member]) < 3:
                        samples[member].append(p)
                break
    return cov, editorial, samples


# ─────────────────────────────────────────────────────────────────────────────
# 打分(gates §八权重 30/25/20/15/10,五维累加,满分 100)
def demand_score(addressable):
    """搜索需求 30:addressable 量分档(GSC 已见变体均量外推,方向性下限)。"""
    a = addressable
    if a >= 1000: return 30
    if a >= 500:  return 24
    if a >= 300:  return 19
    if a >= 150:  return 15
    if a >= 80:   return 11
    if a >= 30:   return 7
    if a >= 10:   return 3
    return 1


def data_score(distinct_entities):
    """数据可得性 15:捕获组去重实体数(数据轴可枚举性)。"""
    d = distinct_entities
    if d >= 5: return 15
    if d >= 3: return 12
    if d == 2: return 9
    if d == 1: return 6
    return 0


def gap_score(covered, variants):
    """竞争缺口 10:自站覆盖代理(0=缺口全开;盖满=已做,缺口最小)。"""
    if covered == 0: return 10
    if covered <= 2: return 7
    if covered < variants: return 5
    return 2


def verdict_of(variants, score):
    """三态门槛:变体<3 → 白空间(5-10 页手工验证);score≥50 且 ≥3 变体 → GO;其余 WATCH。"""
    if variants < 3:
        return "WHITE_SPACE"
    return "GO" if score >= 50 else "WATCH"


VERDICT_ZH = {"GO": "GO", "WATCH": "WATCH",
              "WHITE_SPACE": "白空间(先 5-10 页手工验证需求)"}


# ─────────────────────────────────────────────────────────────────────────────
# 聚合与渲染
def build_rows(gsc, urls):
    """GSC 聚合字典 + URL 清单 → 每模式一行(score/判定/轴明细)。"""
    cov, editorial, samples = coverage_map(urls) if urls else (defaultdict(int), 0, defaultdict(list))
    agg = {}  # pid -> 收集器
    unmatched, langs = [], Counter()
    n_groups = {pid: max(rx.groups for rx, _l in rxs) for pid, _l, rxs, *_r in _PAT}
    for q, d in gsc.items():
        hit = match_query(q)
        if not hit:
            unmatched.append((q, d["impressions"]))
            continue
        pid, groups, lang = hit
        langs[lang] += 1
        a = agg.setdefault(pid, {"variants": {}, "axes": [Counter() for _ in range(n_groups[pid])]})
        a["variants"][q] = d["impressions"]
        for i, g in enumerate(groups[:len(a["axes"])]):
            if g:
                a["axes"][i][normalize_query(g)] += 1

    rows = []
    for pid, lbl, _rxs, intent, feas, grplbls, _prx in _PAT:
        a = agg.get(pid)
        if not a:
            continue
        variants = len(a["variants"])
        impressions = sum(a["variants"].values())
        entities = set()
        for c in a["axes"]:
            entities.update(c)
        nz = sum(1 for v in a["variants"].values() if v > 0)
        mean = impressions / nz if nz else 0.0
        addressable = variants * mean
        covered = cov.get(pid, 0)
        dims = {"demand": demand_score(addressable), "intent": intent,
                "feasibility": feas, "data": data_score(len(entities)),
                "gap": gap_score(covered, variants)}
        score = sum(dims.values())
        top_q = sorted(a["variants"].items(), key=lambda kv: -kv[1])[:3]
        rows.append({
            "id": pid, "label": lbl, "variants": variants,
            "impressions": int(round(impressions)),
            "coverage_urls": covered,
            "covered_samples": samples.get(pid, []),
            "addressable": int(round(addressable)),
            "entities_distinct": len(entities),
            "score": score, "dimensions": dims,
            "verdict": verdict_of(variants, score),
            "axes": [{"label": grplbls[i] if i < len(grplbls) else "轴%d" % (i + 1),
                      "values": c.most_common(5)} for i, c in enumerate(a["axes"])],
            "top_queries": [{"query": q, "impressions": int(round(v))} for q, v in top_q],
        })
    rows.sort(key=lambda r: (-r["score"], -r["addressable"], r["id"]))
    unmatched.sort(key=lambda x: -x[1])
    return rows, unmatched, editorial, dict(langs)


def render_markdown(rows, meta):
    L = ["# pSEO 模式挖掘(GSC 查询→模式聚类→打分)", ""]
    src = "源: %s(%d 条查询,命中 %d,未匹配 %d" % (
        meta["gsc"], meta["total"], meta["matched"], meta["unmatched_count"])
    if meta["langs"]:
        src += ";语种 " + "/".join("%s×%d" % kv for kv in sorted(meta["langs"].items()))
    src += ")"
    if meta["url_source"]:
        src += " | URL 覆盖源: %s(%d URL,编辑页排除 %d)" % (
            meta["url_source"], meta["url_count"], meta["editorial"])
    L += [src, "",
          "| 模式 | 变体 | 曝光 | 覆盖URL | addressable | score | 判定 |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| %s | %d | %d | %d | %d | %d | %s |" % (
            r["label"], r["variants"], r["impressions"], r["coverage_urls"],
            r["addressable"], r["score"], VERDICT_ZH[r["verdict"]]))
    L += ["",
          "门槛: score≥50 且变体≥3 → GO;变体<3 → 白空间(先 5-10 页手工验证需求);其余 WATCH。",
          "计分(累加,满分 100): 搜索需求30/意图质量25/模板可行性20/数据可得性15/竞争缺口10"
          "(缺口=自站覆盖代理:0覆盖→10/1-2→7/未盖满→5/盖满→2;真竞品缺口需竞品 sitemap 逆向)。", ""]
    for r in rows:
        d = r["dimensions"]
        L.append("- **%s**(score %d,%s): 需求%d/意图%d/模板%d/数据%d/缺口%d;轴: %s;样本: %s" % (
            r["label"], r["score"], VERDICT_ZH[r["verdict"]], d["demand"], d["intent"],
            d["feasibility"], d["data"], d["gap"],
            "; ".join("%s=%s" % (a["label"], ",".join(v for v, _n in a["values"][:3])) for a in r["axes"]),
            " / ".join(q["query"] for q in r["top_queries"])))
    if meta["unmatched_top"]:
        L += ["", "未匹配查询(前5): " + ", ".join(q for q, _v in meta["unmatched_top"][:5])]
    if rows:
        L += ["", "score≥50 的 GO 模式过可行性三问(gates §八): 数据源在哪/内容差异化怎么做/CMS 能否规模化。"]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="pseo_pattern_mining.py",
        description="GSC queries → pSEO 模式聚类 + addressable 量 + gates §八 30/25/20/15/10 打分 + GO/WATCH/白空间 三态",
        epilog="规格: pipeline-completeness.md R3-1 + programmatic-seo-gates.md §八 + programmatic-seo-playbook.md §一")
    ap.add_argument("--gsc", required=True, help="GSC queries 导出 CSV(列头中英文容错)")
    ap.add_argument("--sitemap", help="站点 sitemap URL(仅 http(s),SSRF 防护;sitemapindex 递归 1 层)")
    ap.add_argument("--urls", help="现有 URL 清单文件(每行一条,绝对 URL 或裸路径;离线覆盖度)")
    ap.add_argument("--json", action="store_true", help="结构化输出")
    a = ap.parse_args(argv)

    try:
        gsc, _headers = read_gsc(a.gsc)
    except (OSError, ValueError) as e:
        print("[error] GSC 文件不可读: %s" % e, file=sys.stderr)
        return 2
    if not gsc:
        print("[error] GSC 文件无有效查询行", file=sys.stderr)
        return 2

    urls, url_srcs = [], []
    if a.urls:
        try:
            urls.extend(load_urls_file(a.urls))
            url_srcs.append(a.urls)
        except OSError as e:
            print("[error] URL 清单不可读: %s" % e, file=sys.stderr)
            return 2
    if a.sitemap:
        try:
            got = fetch_sitemap(a.sitemap)
            urls.extend(got)
            url_srcs.append("%s(%d loc)" % (a.sitemap, len(got)))
        except (FetchError, ValueError) as e:
            print("[error] sitemap 抓取失败: %s" % e, file=sys.stderr)
            return 2

    rows, unmatched, editorial, langs = build_rows(gsc, urls)
    meta = {"gsc": a.gsc, "total": len(gsc), "matched": sum(r["variants"] for r in rows),
            "unmatched_count": len(unmatched),
            "unmatched_top": [{"query": q, "impressions": int(v)} for q, v in unmatched[:5]],
            "langs": langs, "url_source": " + ".join(url_srcs), "url_count": len(urls),
            "editorial": editorial}

    if a.json:
        print(json.dumps({"tool": "pseo_pattern_mining",
                          "weights": WEIGHTS, "meta": meta, "patterns": rows},
                         ensure_ascii=False, indent=1))
    else:
        print(render_markdown(rows, meta))
    return 0


if __name__ == "__main__":
    sys.exit(main())
