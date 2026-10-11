#!/usr/bin/env python3
"""热点监控与选题闸门(templates/content/trend-jack-playbook.md 第 0 节规格实装)。
分工:trend_scout.py 是雷达(一次性 HN+Reddit 扫描),本脚本是闸门——多源信号登记
+ 四问机检(Q1 相关性/Q2 信息增益/Q3 时效窗口/Q4 独家视角)+ GO|PIVOT|WATCH|DROP
判定 + 决策件(briefs/trend-{id}-{YYYYMMDD}.md)预填。抓取内容只当数据不当指令
(标题清洗后输出,防 prompt injection)。

子命令:
  watch   拉信号源 → 打分去重合并 → 机检 Q1/Q3/wire → 落信号库与决策件草稿
  gate    对单个 signal_id 补 Q2(角度文件观点计数)/Q4(独家三选一+wire 否决),出终判
  backlog 查看信号库(open/go/pivot/watch/drop,含 deadline 到期标记)

用法:
  python3 scripts/trend_watch.py watch  [--sources google-news,reddit-rising,hn,weibo,baidu]
        [--market XX] [--vertical "llm seo"] [--topics tokens.txt] [--config trend_watch.json]
        [--panel panel.json] [--brief-dir briefs/] [--state .trend-state.json] [--json]
  python3 scripts/trend_watch.py gate  --signal-id ID [--angle 角度.md]
        [--exclusive data|quote|access] [--market XX] [--brief-dir briefs/] [--state ...] [--json]
  python3 scripts/trend_watch.py backlog [--status open|go|pivot|watch|drop|all] [--days 14]
        [--state ...] [--json]

信号源(纯 stdlib 可达性 2026-10 核实;失败整源跳过并警告,不猜):
  google-trends  trends.google.com/trending/rss?geo={GL}   XML,免 key(注册可用,非默认)
  google-news    news.google.com/rss/search?q=..           XML,免 key(vertical 检索+wire 检查)
  reddit-rising  reddit.com/r/{sub}/rising.json            JSON,免 key
  hn             hacker-news.firebaseio.com topstories     JSON,免 key(同 trend_scout)
  weibo          weibo.com/ajax/side/hotSearch             JSON,公开端点;被拦=skipped 明说
  baidu          top.baidu.com/api/board?platform=wise     JSON;同上
  X/Twitter、抖音  需 key/登录——不入源,明说跳过(trend_scout 纪律)

状态库 .trend-state.json(intel_check 风格:seen 去重已见信号,samples 记二次采样);
默认按市场选源:zh 市场=google-news+reddit-rising+hn+weibo+baidu,其余=前三
(spec 口径:zh 市场默认加热搜源;--sources 显式给定时按给定清单)。

退出码(watch/gate 通用):0=跑完无 GO 级;1=有 GO 级信号(watch=信号库存在活跃 GO,
接 notify.py 即时通知/CI 门);2=全部信号源失败(明说);3=配置/参数错误。
gate 独有:0=过闸(GO);1=不过闸(打印缺哪问);3=输入缺失。
合规:无契约热搜端点每 host 限速 ≤1 req/min(TREND_WATCH_RATE_S 可调,测试打桩不经此);
UA 自报身份;SSRF 防护同 monitor.py(仅 http(s)+私网拒连+重定向逐跳复查+TLS 恒验证)。"""
import argparse
import hashlib
import ipaddress
import json
import os
import re
import socket
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

UA = ("trend-watch/1.0 (seo-skills trend gate bot; "
      "+https://github.com/everyinfra/seo-skills)")
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".trend-state.json")
MARKETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "markets.json")
TIMEOUT = 15
MAX_BYTES = 2_000_000
HN_LIMIT = 15
REDDIT_SUBS = ["technology", "seo", "startups"]   # trend_scout 六 sub 的收敛版(限速考虑)
MAX_SIGNALS = 400                                  # monitor 同款保留纪律
SEEN_CAP = 50                                      # intel_check seen 同款上限
SAMPLE_CAP = 20

STOP = {"the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
        "how", "your", "you", "is", "are", "was", "it", "its", "this", "that",
        "what", "why", "who", "new", "now", "best", "using", "from"}

DEFAULT_THRESHOLDS = {
    "relevance_min": 25,          # Q1 ≥25 过;10-24 WATCH;<10 DROP
    "velocity_resample_min": 30,  # 二次采样最小间隔(分钟)
    "window_news_h": 24,          # <24h 且 rising → News 型
    "window_analysis_h": 72,      # 24-72h → Analysis 型;>72h → WATCH
    "wire_dominate_n": 3,         # wire 域名 ≥3 条且 <24h → 硬新闻否决
    "ig_views_min": 5,            # Q2 净新观点 ≥5
    "dedup_overlap_pct": 70,      # 词重叠 >70% → 合并/重复否决
}

# locale(hl, gl, ceid):Google News/Trends 检索参数,按市场(markets.json 18 市场)
LOCALE = {
    "zh": ("zh-CN", "CN", "CN:zh-Hans"), "en": ("en", "US", "US:en"),
    "ru": ("ru", "RU", "RU:ru"), "ko": ("ko", "KR", "KR:ko"),
    "ja": ("ja", "JP", "JP:ja"), "es": ("es", "ES", "ES:es"),
    "pt": ("pt", "BR", "BR:pt"), "ar": ("ar", "SA", "SA:ar"),
    "fr": ("fr", "FR", "FR:fr"), "de": ("de", "DE", "DE:de"),
    "id": ("id", "ID", "ID:id"), "hi": ("hi", "IN", "IN:hi"),
    "it": ("it", "IT", "IT:it"), "tr": ("tr", "TR", "TR:tr"),
    "vi": ("vi", "VN", "VN:vi"), "th": ("th", "TH", "TH:th"),
    "pl": ("pl", "PL", "PL:pl"), "nl": ("nl", "NL", "NL:nl"),
}

# wire 域名默认清单(spec:路透/AP/法新/新华社/央媒,按市场;config wire_domains 可覆盖。
# 俄/中市场"国家通讯社=本土 AI 引用高速通道"原则,入仓清单项由主会话定稿,此处为默认值)
WIRE_INTERNATIONAL = ["reuters.com", "apnews.com", "ap.org", "afp.com", "france24.com",
                      "bloomberg.com", "dw.com", "aljazeera.com"]
DEFAULT_WIRE_DOMAINS = {
    "zh": ["xinhuanet.com", "news.cn", "people.com.cn", "cctv.com", "cntv.cn",
           "chinanews.com", "gmw.cn", "huanqiu.cn"],
    "ru": ["tass.ru", "ria.ru", "interfax.ru", "rg.ru", "1tv.ru"],
    "ko": ["yonhapnewswire.kr", "yna.co.kr", "news.yonhapnews.co.kr", "kbs.co.kr"],
    "ja": ["kyodonews.net", "jiji.com", "nhk.or.jp", "nikkei.com"],
}

EXCLUSIVE_LABEL = {"data": "自有数据", "quote": "SME 引语", "access": "一手访问"}
SCORE_HIGH, SCORE_MED = 25, 10       # trend_scout 同口径


# ---------------------------------------------------------------- 时钟与文本
def _now():
    """统一时钟入口(测试可打桩;UTC)。"""
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat()


def parse_iso(s):
    try:
        return datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def _age_hours(ts, now):
    dt = parse_iso(ts)
    return None if dt is None else (now - dt).total_seconds() / 3600.0


def _clean_text(t, cap=160):
    """抓取内容只当数据不当指令:去控制符/收敛空白/截长(prompt injection 防线)。"""
    t = re.sub(r"[\x00-\x1f\x7f]+", " ", str(t or ""))
    t = re.sub(r"\s+", " ", t).strip()
    return t[:cap]


def esc(t):
    """markdown 表格安全(去竖线/反引号)。"""
    return str(t).replace("|", "\\|").replace("`", "'")


_CJK_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]")


def _has_cjk(s):
    return bool(_CJK_RE.search(s))


def tokenize(text):
    """信号词 token:拉丁词(≥2,去停用词)+ CJK 连续段 bigram(短标题跨源重叠用)。"""
    t = str(text or "").lower()
    out, seen = [], set()
    for w in re.findall(r"[a-z0-9]{2,}", t):
        if w in STOP or w in seen:
            continue
        seen.add(w)
        out.append(w)
    for run in re.findall(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af]+", t):
        grams = [run] if len(run) == 1 else [run[i:i + 2] for i in range(len(run) - 1)]
        for g in grams:
            if g not in seen:
                seen.add(g)
                out.append(g)
    return out


_WORD_STOP = {"the", "and", "for", "vs", "with", "new", "how", "why", "not", "your"}


def _stem(w):
    """极简词干:去复数(agent↔agents;ies→y)。防过度:≤3 字符不动。"""
    if len(w) > 3 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("es"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def relevance(title, tokens):
    """整词/词组命中 +25;**词干级全词命中 +10**——词组 token 拆词后按词干比对
    (顺序无关):"AI agents" 命中 "Agent SDK"、单复数互通。2026-10-11 真实部署
    发现纯词组匹配会把产品垂直最常见的变体表述(如 "Claude Agent SDK vs
    LangGraph")漏成 Q1=0;词干近似是必要折衷。CJK 子串命中即按整词。
    返回 (score, tag)。"""
    t = " " + str(title or "").lower() + " "
    words = set(_stem(w) for w in re.findall(r"[a-z0-9]+", t) if w)
    singles = set()
    score = 0
    for tok in tokens or []:
        tok = str(tok).lower().strip()
        if not tok:
            continue
        if _has_cjk(tok):
            if tok in t:
                score += SCORE_HIGH
        elif re.search(r"\b" + re.escape(tok) + r"\b", t):
            score += SCORE_HIGH                      # 词组/整词全命中
        else:
            tok_words = set(_stem(w) for w in re.findall(r"[a-z0-9]+", tok) if w)
            if tok_words and tok_words <= words:
                score += SCORE_MED                   # token 全部词的词干级命中
            else:
                for w in tok_words:                 # 单词级:显著词干命中各计一次
                    if len(w) >= 3 and w not in _WORD_STOP and w in words:
                        singles.add(w)
    score += len(singles) * 10
    if len(singles) >= 2:                            # ≥2 个不同垂类词 → 升 HIGH
        score = max(score, SCORE_HIGH)               # ("Claude Agent SDK"=agent+claude)
    tag = "HIGH" if score >= SCORE_HIGH else ("MED" if score > 0 else "")
    return score, tag


def word_overlap(a, b):
    """词重叠(重复否决/跨源合并口径):集合包含度 |A∩B|/min(|A|,|B|)——
    热搜标题短,常是长标题的子集,Jaccard 会低估,故用包含度。"""
    sa, sb = set(a or []), set(b or [])
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


def registrable_domain(url):
    """URL/host → 可注册域(monitor.py 同款)。"""
    host = urllib.parse.urlparse(str(url) or "").netloc.split("@")[-1].split(":")[0].lower()
    if not host:
        host = str(url or "").split("/")[0].lower()
    if host.startswith("www."):
        host = host[4:]
    parts = [p for p in host.split(".") if p]
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


# ---------------------------------------------------------------- 抓取(SSRF+限速)
class FetchError(Exception):
    pass


_ssrf_cache = {}


def ssrf_guard(host):
    """仅 http(s) + 拒私网/环回/链路本地;结果按 host 缓存(TLS 恒验证走默认 urlopen)。
    198.18.0.0/15(RFC2544 基准段)豁免:本机 fake-IP 代理会把一切域名解析到该段,
    实际连接经代理出网,TLS 验证仍生效;SEO_MONITOR_STRICT_SSRF=1 恢复全拒(monitor 同款)。"""
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
    """重定向逐跳 SSRF 复查(urlopen 自动跟 302,最终 host 必须复查——monitor 同款)。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urllib.parse.urlparse(newurl)
        if p.scheme not in ("http", "https"):
            raise FetchError("重定向到非 http(s) 被拒: %s" % newurl)
        ssrf_guard(p.hostname)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_RedirectGuard)

# 无契约公开热搜端点的礼貌限速(≤1 req/min/host);官方 JSON API(HN firebase)不限,
# 与 trend_scout 并发抓取先例一致。测试打桩 fetch_url,不经此路径。
_POLITE_HOSTS = {"news.google.com", "trends.google.com", "weibo.com", "top.baidu.com",
                 "www.reddit.com"}
_last_hit = {}


def fetch_url(url, timeout=TIMEOUT):
    """唯一网络出口(测试打桩点):scheme 检查 + SSRF 防护 + 礼貌限速 + 受控 opener。"""
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        raise FetchError("仅允许 http(s): %s" % url)
    ssrf_guard(p.hostname)
    host = p.hostname or ""
    interval = float(os.environ.get("TREND_WATCH_RATE_S", "60"))
    if host in _POLITE_HOSTS and host in _last_hit:
        wait = interval - (time.monotonic() - _last_hit[host])
        if wait > 0:
            time.sleep(wait)
    if host in _POLITE_HOSTS:
        _last_hit[host] = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with _opener.open(req, timeout=timeout) as r:
            return r.read(MAX_BYTES).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise FetchError("HTTP %s: %s" % (e.code, url.split("?")[0]))
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise FetchError("抓取失败 %s: %s" % (url.split("?")[0], e))


def _safe(fn, *args):
    """线程池里不能向调用方抛异常,包一层返回异常对象(trend_scout 同款)。"""
    try:
        return fn(*args)
    except Exception as e:
        return e


# ---------------------------------------------------------------- RSS/JSON 解析
def parse_rss_items(xml_text, limit=15):
    """RSS2/Atom 最近 N 条 → [{title, link, source_url, source_name}];解析失败返回 []。"""
    items = []
    try:
        root = ET.fromstring(re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", "&amp;", xml_text or ""))
    except ET.ParseError:
        return items
    for it in root.iter("item"):
        items.append({
            "title": _clean_text(it.findtext("title") or ""),
            "link": (it.findtext("link") or "").strip(),
            "source_url": ((it.find("source").get("url") if it.find("source") is not None
                            else None) or "").strip(),
            "source_name": _clean_text(it.findtext("source") or "", 40),
        })
    if not items:
        for e in root.iter("{http://www.w3.org/2005/Atom}entry"):
            link = ""
            for l in e.findall("{http://www.w3.org/2005/Atom}link"):
                link = l.get("href") or link
            items.append({"title": _clean_text(e.findtext("{http://www.w3.org/2005/Atom}title") or ""),
                          "link": link, "source_url": "", "source_name": ""})
    return [i for i in items if i["title"]][:limit]


def google_news_search_url(query, market):
    hl, gl, ceid = LOCALE.get(market, LOCALE["en"])
    return ("https://news.google.com/rss/search?q=%s&hl=%s&gl=%s&ceid=%s"
            % (urllib.parse.quote_plus(query), hl, gl, ceid))


def wire_check(title, market, wire_domains):
    """同事件 Google News RSS top 结果中 wire 域名条数(≥threshold 且 <24h=硬新闻否决)。
    返回 {n,total,domains[],checked_at,query} 或 None(fetch 失败,明说不猜)。"""
    q = _clean_text(title, 80)
    url = google_news_search_url(q, market)
    try:
        body = fetch_url(url)
    except FetchError:
        return None
    items = parse_rss_items(body, limit=10)
    domains = []
    for it in items:
        d = registrable_domain(it.get("source_url") or it.get("link") or "")
        if d:
            domains.append(d)
    wire_set = set(wire_domains)
    return {"n": sum(1 for d in domains if d in wire_set), "total": len(domains),
            "domains": domains, "checked_at": iso(_now()), "query": q}


# ---------------------------------------------------------------- 信号源(整源失败跳过)
def _strip_publisher(title):
    """Google News 标题尾巴 ' - Publisher' 去掉(wire 检查仍读 <source> 标签,不受影响)。"""
    return _clean_text(re.sub(r"\s+-\s+\S.{0,40}$", "", title)) if " - " in title else title


def _src_google_news(ctx):
    if not ctx["tokens"]:
        raise FetchError("google-news 源需 vertical 检索词(--vertical/--topics/config),本次跳过")
    q = " ".join(ctx["tokens"])
    body = fetch_url(google_news_search_url(q, ctx["market"]))
    return [{"title": _strip_publisher(i["title"]), "url": i["link"], "pos": n + 1}
            for n, i in enumerate(parse_rss_items(body, limit=10))]


def _src_google_trends(ctx):
    _hl, gl, _c = LOCALE.get(ctx["market"], LOCALE["en"])
    body = fetch_url("https://trends.google.com/trending/rss?geo=%s" % gl.upper())
    return [{"title": _clean_text(i["title"]), "url": i["link"], "pos": n + 1}
            for n, i in enumerate(parse_rss_items(body, limit=20))]


def _src_reddit_rising(ctx):
    out = []
    for sub in ctx["reddit_subs"]:
        data = json.loads(fetch_url("https://www.reddit.com/r/%s/rising.json?limit=10" % sub))
        for n, ch in enumerate((data.get("data") or {}).get("children") or []):
            d = ch.get("data") or {}
            if d.get("title"):
                out.append({"title": _clean_text(d["title"]),
                            "url": "https://www.reddit.com" + (d.get("permalink") or ""),
                            "pos": n + 1})
    return out


def _src_hn(ctx):
    ids = json.loads(fetch_url("https://hacker-news.firebaseio.com/v0/topstories.json"))
    items = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for n, raw in enumerate(pool.map(
                lambda i: _safe(fetch_url, "https://hacker-news.firebaseio.com/v0/item/%d.json" % i),
                ids[:HN_LIMIT])):
            if isinstance(raw, Exception):
                continue
            try:
                it = json.loads(raw)
            except ValueError:
                continue
            if it and it.get("title"):
                items.append({"title": _clean_text(it["title"]),
                              "url": it.get("url") or ("https://news.ycombinator.com/item?id=%s"
                                                       % it.get("id")), "pos": n + 1})
    return items


def _src_weibo(ctx):
    data = json.loads(fetch_url("https://weibo.com/ajax/side/hotSearch"))
    if data.get("ok") != 1:
        raise FetchError("weibo 返回 ok!=1(疑似被拦)")
    rt = (data.get("data") or {}).get("realtime") or []
    return [{"title": _clean_text(w.get("word")), "url": "https://s.weibo.com/weibo?q=%s"
             % urllib.parse.quote_plus(w.get("word") or ""), "pos": n + 1}
            for n, w in enumerate(rt) if w.get("word")]


def _src_baidu(ctx):
    data = json.loads(fetch_url("https://top.baidu.com/api/board?platform=wise"))
    if not data.get("success"):
        raise FetchError("baidu 返回 success!=1(疑似被拦)")
    out, pos = [], 0
    # 实测两种形状:cards[].content[]={word..}(简洁版)与 cards[].content[].content[]={word..}
    # (2026-10 实测 wise 端点嵌套两层:tab 包装层→词条层),两层都走,逐层取 word
    for card in (data.get("data") or {}).get("cards") or []:
        for group in card.get("content") or []:
            entries = group.get("content") or [group]
            for c in entries:
                if isinstance(c, dict) and c.get("word"):
                    pos += 1
                    out.append({"title": _clean_text(c["word"]),
                                "url": "https://top.baidu.com/board?name=%s"
                                       % urllib.parse.quote_plus(c["word"]),
                                "pos": pos})
    return out


SOURCE_FETCHERS = {
    "google-trends": ("Google Trends 每日热搜 RSS", _src_google_trends),
    "google-news": ("Google News RSS 检索(vertical+wire)", _src_google_news),
    "reddit-rising": ("Reddit rising(JSON)", _src_reddit_rising),
    "hn": ("HN topstories(同 trend_scout)", _src_hn),
    "weibo": ("微博热搜(公开端点)", _src_weibo),
    "baidu": ("百度热搜(公开端点)", _src_baidu),
}
DEFAULT_SOURCES = ["google-news", "reddit-rising", "hn"]
ZH_EXTRA_SOURCES = ["weibo", "baidu"]


# ---------------------------------------------------------------- 状态库(.trend-state.json)
def default_state():
    return {"checked_at": None, "sources": {}, "signals": {}, "seen": {}}


def load_state(path):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                st = json.load(f)
            for k, v in default_state().items():
                st.setdefault(k, v)
            return st
        except (ValueError, OSError) as e:
            print("[warn] 状态文件损坏,重建(%s): %s" % (path, e), file=sys.stderr)
    return default_state()


def save_state(path, state):
    state["checked_at"] = iso(_now())
    # 保留纪律(同 monitor 400 条):先淘汰 drop,再淘汰最旧的 watch
    sigs = state["signals"]
    if len(sigs) > MAX_SIGNALS:
        order = sorted(sigs.items(), key=lambda kv: (
            kv[1].get("status") == "drop",                     # drop 先走
            kv[1].get("status") in ("go", "pivot"),            # 活跃判定最后走(取反序)
            kv[1].get("last_seen") or ""))
        for sid, _ in order[:len(sigs) - MAX_SIGNALS]:
            if sigs[sid].get("status") not in ("go", "pivot"):
                del sigs[sid]
    for src in state["seen"]:
        state["seen"][src] = state["seen"][src][-SEEN_CAP:]
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def signal_id_of(src, title):
    norm = re.sub(r"\s+", " ", str(title or "").strip().lower())
    return hashlib.sha1(("%s|%s" % (src, norm)).encode("utf-8")).hexdigest()[:10]


def _history(sig, event, detail, now):
    sig.setdefault("history", []).append({"ts": iso(now), "event": event, "detail": detail[:120]})
    sig["history"] = sig["history"][-30:]


# ---------------------------------------------------------------- 四问机检
def compute_velocity(samples, now, resample_min):
    """velocity 三态:与 ≥resample_min 分钟前的最近一次采样比位置(位置小=更热)。
    样本不足/间隔不够 → None(不可判,Q3 退化为只看 first_seen——Method Notes 已知坑)。"""
    if len(samples) < 2:
        return None
    prev = None
    for s in reversed(samples[:-1]):
        dt = parse_iso(s.get("ts"))
        if dt and (now - dt).total_seconds() / 60.0 >= resample_min:
            prev = s
            break
    if prev is None:
        return None
    cur, old = samples[-1].get("pos"), prev.get("pos")
    if not isinstance(cur, int) or not isinstance(old, int):
        return None
    return "rising" if cur < old else ("fading" if cur > old else "peaked")


def q3_window(sig, now, th):
    """时效窗口:<24h 且 velocity 未降 → NEWS;24-72h → ANALYSIS;>72h 或 peaked/fading → LATE。"""
    age = _age_hours(sig.get("first_seen"), now)
    if age is None:
        return "UNKNOWN", "first_seen 缺失"
    v = sig.get("velocity")
    if v in ("peaked", "fading"):
        return "LATE", "velocity=%s(挂既有页刷新队列)" % v
    if age > th["window_analysis_h"]:
        return "LATE", "%.1fh>%.0fh(挂既有页刷新队列)" % (age, th["window_analysis_h"])
    if age < th["window_news_h"]:
        return "NEWS", "%.1fh%s" % (age, ",velocity=rising" if v == "rising" else "")
    return "ANALYSIS", "%.1fh(新闻位已占,分析位还空)" % age


def eval_status(sig, now, th):
    """watch 级机检判定(gate 下过判的信号 sticky,不再动);返回 (status, reason, deadline)。"""
    if sig.get("gated_at"):
        return sig["status"], sig.get("reason", ""), sig.get("deadline")
    score = sig.get("rel_score")
    if score is not None and score < SCORE_MED:
        return "drop", "Q1=%d<10(垂直无关)" % score, None
    if score is not None and score < th["relevance_min"]:
        return "watch", "Q1=%d 相关性不足(10-24,涨了再看)" % score, iso(now + timedelta(
            hours=th["window_analysis_h"]))
    if len(sig.get("sources") or []) < 2:
        return "watch", "单源(传闻;≥2 独立源才算事件)", iso(now + timedelta(hours=6))
    win, wre = q3_window(sig, now, th)
    sig["q3"], sig["q3_reason"] = win, wre
    if win == "LATE":
        return "watch", "窗口 %s" % wre, iso(now + timedelta(hours=th["window_analysis_h"]))
    return "open", "机检过(双源+Q1 %s+窗口 %s),待 gate 补 Q2/Q4" % (
        ("%d" % score) if score is not None else "未打分", win), None


def register_item(state, src, item, tokens, now, th):
    """登记一条原始信号:seen 去重 → 跨源词重叠合并 → 建新信号/补采样。
    返回 (signal|None, created:bool, merged:bool)。"""
    title = item.get("title") or ""
    if not title:
        return None, False, False
    seen = state["seen"].setdefault(src, [])
    is_new = title not in seen
    sig = state["signals"].get(signal_id_of(src, title))
    merged = False
    if sig is None and is_new:
        itoks = set(tokenize(title))
        exact, best, best_ov = None, None, 0.0
        for s in state["signals"].values():
            if itoks == set(s.get("tokens") or []):       # 同文/同题转载(跨源确认)
                exact = s
                break
            ov = word_overlap(itoks, s.get("tokens"))
            if ov > best_ov:
                best, best_ov = s, ov
        ov_th = th["dedup_overlap_pct"] / 100.0
        # 跨源同事件合并:词集相同;重复否决:仅并入活跃(go/pivot)判定的信号
        # (spec:与活跃信号词重叠>70%→合并不新开)——未激活的相似/超集事件各自登记,
        # gate 时再做重复否决(防 watch 阶段按包含度误吞近邻事件)
        if exact is not None:
            sig, merged = exact, True
        elif best is not None and best_ov > ov_th and best.get("status") in ("go", "pivot"):
            sig, merged = best, True
    if sig is None:
        if not is_new:
            return None, False, False            # 已见且信号已淘汰:只当旧闻
        score, tag = relevance(title, tokens) if tokens else (None, "")
        sig = {"signal_id": signal_id_of(src, title), "title": title,
               "tokens": tokenize(title), "sources": [src],
               "links": {src: item.get("url") or ""},
               "first_seen": iso(now), "last_seen": iso(now),
               "samples": [], "velocity": None, "market": None,
               "rel_score": score, "rel_tag": tag, "wire": None,
               "q3": None, "q3_reason": "", "q2": None, "q4": None,
               "status": "open", "reason": "", "deadline": None,
               "verdict_type": "", "gated_at": None, "angle_file": None,
               "existing": "[要追加: GSC/内链检索]", "history": []}
        state["signals"][sig["signal_id"]] = sig
        created = True
    else:
        created = False
        sig["last_seen"] = iso(now)
        if src not in sig["sources"]:
            sig["sources"].append(src)
            _history(sig, "merge-source", "并入 %s(词重叠合并)" % src, now)
        sig.setdefault("links", {})[src] = item.get("url") or ""
    sig["samples"] = (sig.get("samples") or [])[-(SAMPLE_CAP - 1):] + [
        {"ts": iso(now), "pos": item.get("pos"), "src": src}]
    if title not in seen:
        seen.append(title)
    return sig, created, merged


# ---------------------------------------------------------------- 决策件预填
def render_brief(sig, th, now):
    """按 trend-jack-playbook 占位符预填决策件(第 1/2 节机器半边;人工半边留 {{ }})。"""
    d_local = _now().astimezone().strftime("%Y-%m-%d %H:%M")
    src_lines = "; ".join("%s: %s — %s" % (s, esc(sig["title"][:60]),
                                           sig.get("links", {}).get(s, "")) for s in sig["sources"])
    score = sig.get("rel_score")
    q1 = ("PASS(%d,%s;≥%d)" % (score, sig.get("rel_tag") or "", th["relevance_min"])
          if score is not None and score >= th["relevance_min"] else
          ("MED(%d,10-24→WATCH)" % score if score is not None and score >= SCORE_MED else
           ("DROP(%d<10)" % score if score is not None else "UNKNOWN(未打分,需 --topics/--vertical)")))
    q2 = sig.get("q2") or "UNKNOWN(待人工;gate --angle 角度文件净新观点 ≥%d)" % th["ig_views_min"]
    q4 = (sig.get("q4") and "%s(%s)" % (sig["q4"], EXCLUSIVE_LABEL.get(sig["q4"], ""))) or \
         "UNKNOWN(待人工;--exclusive data|quote|access 三选一)"
    wire = sig.get("wire") or {}
    wire_line = ("未检(源失败,明说不猜)" if wire.get("n") is None and wire else
                 ("未查(gate 时补)" if not wire else
                  "%d/%d 条 wire 域名(≥%d 且 <24h=硬新闻否决)%s" % (
                      wire.get("n", 0), wire.get("total", 0), th["wire_dominate_n"],
                      " → " + ",".join(d for d in wire.get("domains", [])[:5]) if wire.get("n") else "")))
    verdict = (sig.get("status") or "open").upper()
    vshow = "%s(%s)" % (verdict, sig["verdict_type"]) if sig.get("verdict_type") else verdict
    return """# 判定 {vshow}:trend-{sid}({title})

> trend_watch.py 预填决策件(模板:templates/content/trend-jack-playbook.md);
> 四问的 Q2/Q4 人工半边由选题人补;数字缺失处标 [要追加: 数据源],不许编。
> For: {{{{选题人 · SME 复核人}}}} · Date: {date} · Market: {market} · Signal: {sid} · 判定: {verdict} · Data pulled: {pulled}

## The answer

{{{{一段独立成立:信号与来源、四问逐问结果(过/不过+一句依据)、判定(GO=型+发布截止 / PIVOT=转什么分析角度 / WATCH=何时重看 / DROP=为何放弃)、独家视角一句话、红线自查两条、置信度}}}}
机检速览:Q1 {q1m} / Q2 {q2} / Q3 {q3}({q3r}) / Q4 {q4} / wire {wire} / 判定 {vshow}({reason})

## 1. 信号登记表(固定第一节,脚本落盘)

| 信号项 | 数值 | 口径/阈值 |
|---|---|---|
| signal_id | {sid} | 源-主题词哈希;跨次运行幂等 |
| 信号源与链接 | {srcs} | ≥2 个独立源才算事件(当前 {nsrc} 源{single_note}) |
| first_seen / 采样时刻 | {first_seen} / {local} | UTC+本地双记;窗口(Q3)从 first_seen 起算 |
| velocity | {vel} | ≥{rs}min 二次采样;rising/peaked/fading |
| 垂直相关性分 | {rel} | trend_scout 同口径:HIGH 整词 +25/MED +10;≥{rmin} 过 Q1 |
| 同事件 wire 占位 | {wire_n} | Google News RSS top 结果 wire 域名条数;≥{wn} 且 <24h=硬新闻否决 |
| 我们既有覆盖 | {existing} | 站内已有相关页=优先刷新既有页而非新开 |
| 数据源与抓取时间 | trend_watch watch@{pulled} | 单源失败明说,不猜 |

## 2. 四问闸门(一票否决制;机检行=脚本,人工行=选题人)

- **Q1 相关性**: 机检 {q1}——人工: {{{{品牌错位一票否决?对照 brand-records.md 受众/"不服务谁"}}}}
- **Q2 信息增益**: 机检 {q2}——人工: {{{{净新观点清单 ≥{ig} 条(反共识/时效新鲜度/SME 引语/专有数据),写不满=不过}}}}
- **Q3 时效窗口**: 机检 {q3}({q3r})——发布后按 4-5 周仍有引用价值设计(写分析/数据层,不写转述层)
- **Q4 独家视角**: 机检 {q4}——人工: {{{{一句话独家视角,写不出=不过}}}};wire 否决: {wire}
- 角度文件: {angle}

## 判定:{vshow}({reason};deadline={deadline})

## 5. 合规红线自查(起草前必读)
1. 量产蹭热点=scaled content abuse:同一事件 >2 篇/日、模板化改写——本信号只允许一个活跃 GO 决策件(trend_watch 重复否决)。{{{{自查}}}}
2. 真实性与署名:每个数字有来源、引语可归属一手;拿不准写 [要追加: 待核] 阻塞发布。{{{{自查}}}}
""".format(
        sid=sig["signal_id"], title=esc(sig["title"][:60]), verdict=verdict, vshow=vshow,
        date=_now().strftime("%Y-%m-%d"), market=sig.get("market") or "-",
        pulled=sig.get("last_seen") or iso(now),
        srcs=src_lines or "-", nsrc=len(sig.get("sources") or []),
        single_note="(单源=传闻,只 WATCH)" if len(sig.get("sources") or []) < 2 else "",
        first_seen=sig.get("first_seen") or "-", local=d_local,
        vel=sig.get("velocity") or "不可判(样本不足,退化只看 first_seen)",
        rs=th["velocity_resample_min"],
        rel=("%d(%s)" % (score, sig.get("rel_tag") or "")) if score is not None else "未打分",
        rmin=th["relevance_min"], wire=wire_line,
        wire_n=("%d/%d" % (wire.get("n"), wire.get("total"))) if wire else "未查",
        wn=th["wire_dominate_n"], existing=sig.get("existing") or "[要追加: GSC/内链检索]",
        q1=q1, q1m=("%d 分" % score) if score is not None else "未打分",
        q2=q2, q3=sig.get("q3") or "-", q3r=sig.get("q3_reason") or "-",
        q4=q4, ig=th["ig_views_min"],
        angle=sig.get("angle_file") or "{{要追加: 角度文档(gate --angle)}}",
        reason=sig.get("reason") or "-", deadline=sig.get("deadline") or "无")


def write_brief(sig, brief_dir, th, now):
    os.makedirs(brief_dir, exist_ok=True)
    path = os.path.join(brief_dir, "trend-%s-%s.md" % (sig["signal_id"], now.strftime("%Y%m%d")))
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(render_brief(sig, th, now))
        return path
    except OSError as e:
        print("[warn] 决策件写盘失败(%s): %s" % (path, e), file=sys.stderr)
        return None


# ---------------------------------------------------------------- 配置
def load_config(path, market):
    """config JSON → (tokens, wire_domains, thresholds, reddit_subs, 注意事项);
    非法 config 抛 ValueError(调用方 exit 3)。"""
    cfg = {}
    if path:
        try:
            with open(path, encoding="utf-8") as f:
                cfg = json.load(f)
        except (ValueError, OSError) as e:
            raise ValueError("--config 读取失败: %s" % e)
        if not isinstance(cfg, dict):
            raise ValueError("--config 顶层必须是 JSON 对象")
    tokens = [t for t in (cfg.get("vertical_tokens") or []) if isinstance(t, str) and t.strip()]
    wd = cfg.get("wire_domains") or {}
    if isinstance(wd, dict):
        wire = [d.lower() for d in (wd.get(market) or wd.get("default") or []) if isinstance(d, str)]
    else:
        wire = [d.lower() for d in wd if isinstance(d, str)]
    if not wire:
        wire = list(DEFAULT_WIRE_DOMAINS.get(market, WIRE_INTERNATIONAL))
    th = dict(DEFAULT_THRESHOLDS)
    for k, v in (cfg.get("thresholds") or {}).items():
        if k in th and isinstance(v, (int, float)):
            th[k] = v
    subs = [s for s in (cfg.get("reddit_subs") or REDDIT_SUBS) if isinstance(s, str) and s]
    return tokens, wire, th, subs, cfg


def read_tokens_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        raise ValueError("--topics 读取失败: %s" % e)
    return [t for t in re.split(r"[\s,;]+", raw.lower()) if t]


def validate_market(market):
    """市场码必须是 markets.json 18 市场之一(markets 数据层);文件缺失时警告放行。"""
    if not os.path.exists(MARKETS_FILE):
        print("[warn] markets.json 缺失,市场码不再校验: %s" % market, file=sys.stderr)
        return
    try:
        with open(MARKETS_FILE, encoding="utf-8") as f:
            codes = set(json.load(f).get("markets", {}).keys())
    except (ValueError, OSError):
        print("[warn] markets.json 解析失败,市场码不再校验", file=sys.stderr)
        return
    if market not in codes:
        raise ValueError("未知市场码 %s(须为 markets.json 18 市场之一)" % market)


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def panel_coverage(panel_path, sig):
    """--panel(citation_panel 面板,可选):命中=已有覆盖,优先刷新既有页;容错不阻塞。"""
    try:
        with open(panel_path, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        return None
    toks = sig.get("tokens") or []
    for s in _strings(data):
        if len(s) >= 4 and word_overlap(toks, tokenize(s)) >= 0.7:
            return "panel 命中:%s → 优先刷新既有页" % _clean_text(s, 60)
    return None


def count_angle_points(text):
    """Q2 机检:角度文件的净新观点计数——优先数表格行(| n | …|,playbook 2.2 节表格),
    无表格时数列表项。规格的"3-gram 竞品文集重叠"粗筛需竞品语料,零依赖 CLI 不拉,
    净新性验证留给人工半边(playbook Q2 人工行),此处只计数。"""
    rows = re.findall(r"(?m)^\s*\|\s*\d+\s*\|", text or "")
    if rows:
        return len(rows)
    return len(re.findall(r"(?m)^\s*(?:\d+[.)]|[-*+])\s+\S+", text or ""))


# ---------------------------------------------------------------- watch
def cmd_watch(a):
    try:
        validate_market(a.market)
        cfg_tokens, wire_domains, th, subs, _cfg = load_config(a.config, a.market)
    except ValueError as e:
        print("[error] %s" % e, file=sys.stderr)
        return 3
    tokens = []
    try:
        if a.topics:
            tokens = read_tokens_file(a.topics)
        elif a.vertical and a.vertical.strip():
            tokens = [t for t in re.split(r"[\s,;]+", a.vertical.strip().lower()) if t]
    except ValueError as e:
        print("[error] %s" % e, file=sys.stderr)
        return 3
    tokens = tokens or cfg_tokens
    sources = ([s.strip().lower() for s in a.sources.split(",") if s.strip()]
               if a.sources else (DEFAULT_SOURCES + (ZH_EXTRA_SOURCES if a.market == "zh" else [])))
    bad = [s for s in sources if s not in SOURCE_FETCHERS]
    if bad:
        print("[error] 未知信号源 %s(可选:%s)" % (",".join(bad), ",".join(SOURCE_FETCHERS)),
              file=sys.stderr)
        return 3

    state = load_state(a.state)
    now = _now()
    ctx = {"market": a.market, "tokens": tokens, "reddit_subs": subs}
    ok, failed, skipped = [], {}, {}
    raw_items = []
    for name in sources:
        label, fn = SOURCE_FETCHERS[name]
        try:
            items = fn(ctx)
            if not items:
                skipped[name] = "%s 返回 0 条" % label
                state["sources"][name] = {"ts": iso(now), "ok": False, "items": 0, "error": "0 条"}
                continue
            ok.append(name)
            state["sources"][name] = {"ts": iso(now), "ok": True, "items": len(items), "error": None}
            raw_items.extend((name, it) for it in items)
        except (FetchError, ValueError, KeyError, TypeError) as e:   # 整源失败:跳过并警告,不崩
            failed[name] = "%s: %s" % (type(e).__name__, e)
            state["sources"][name] = {"ts": iso(now), "ok": False, "items": 0,
                                      "error": str(e)[:120]}
            print("[warn] 源失败(跳过) %s: %s" % (name, e), file=sys.stderr)

    # 登记 + 跨源合并 + 二次采样
    touched, created_sigs, merged_n = [], [], 0
    for src, item in raw_items:
        sig, created, merged = register_item(state, src, item, tokens, now, th)
        if sig is None:
            continue
        if created:
            sig["market"] = a.market
            created_sigs.append(sig)
        if merged:
            merged_n += 1
        if sig not in touched:
            touched.append(sig)

    # 机检三件:velocity / Q3 窗口 / watch 级判定;--panel 已有覆盖标记
    for sig in touched:
        sig["velocity"] = compute_velocity(sig.get("samples") or [], now,
                                           th["velocity_resample_min"])
        prev_status = sig.get("status")
        status, reason, deadline = eval_status(sig, now, th)
        if status != prev_status:
            _history(sig, "status", "%s → %s(%s)" % (prev_status, status, reason), now)
        sig["status"], sig["reason"], sig["deadline"] = status, reason, deadline
        if a.panel:
            cov = panel_coverage(a.panel, sig)
            if cov:
                sig["existing"] = cov

    # wire 机检(每 run 至多 1 条:礼貌限速下 news.google.com 二次请求要隔 60s,
    # 其余候选 gate 时补检——规格"watch 机检 Q1/Q3/wire"的降频实现,明说)
    wire_done = 0
    cands = [s for s in touched if s["status"] == "open"
             and (s.get("rel_score") or 0) >= th["relevance_min"]
             and s.get("q3") == "NEWS" and not s.get("wire")]
    for sig in sorted(cands, key=lambda s: (-(s.get("rel_score") or 0), s.get("first_seen") or "")):
        sig["wire"] = wire_check(sig["title"], sig.get("market") or a.market, wire_domains)
        wire_done += 1
        _history(sig, "wire", "n=%s" % (sig["wire"] or {}).get("n"), now)
        if wire_done >= 1:
            break

    # 决策件草稿(drop 不出件)
    briefs = []
    for sig in touched:
        if sig["status"] in ("open", "watch", "go", "pivot"):
            p = write_brief(sig, a.brief_dir, th, now)
            if p:
                briefs.append(p)

    save_state(a.state, state)

    active_go = [s["signal_id"] for s in state["signals"].values() if s.get("status") == "go"]
    new_payload = [{"signal_id": s["signal_id"], "title": s["title"],
                    "sources": s["sources"], "rel_score": s["rel_score"],
                    "rel_tag": s["rel_tag"],
                    "age_h": round(_age_hours(s["first_seen"], now) or 0, 2),
                    "velocity": s["velocity"], "q3": s.get("q3"),
                    "status": s["status"], "reason": s["reason"], "deadline": s["deadline"]}
                   for s in created_sigs]
    payload = {"ran_at": iso(now), "market": a.market, "vertical_tokens": tokens,
               "sources_ok": ok, "sources_failed": failed, "sources_skipped": skipped,
               "new_signals": new_payload, "created": len(created_sigs), "merged": merged_n,
               "wire_checked": wire_done, "active_go": active_go, "briefs": briefs}

    if a.json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print("=== trend_watch watch(market=%s;ok: %s;failed: %s;skipped: %s)===" % (
            a.market, ",".join(ok) or "无",
            ",".join(failed) or "无", ",".join(skipped) or "无"))
        print("新信号 %d 条(另:跨源合并 %d / wire 检 %d):" % (len(new_payload), merged_n, wire_done))
        print("| signal_id | 源 | 标题 | Q1 | age | velocity | 窗口 | 状态 |")
        print("|---|---|---|---|---|---|---|---|")
        for s in new_payload:
            print("| %s | %s | %s | %s | %sh | %s | %s | %s(%s) |" % (
                s["signal_id"], "+".join(s["sources"]), esc(s["title"][:48]),
                ("%d(%s)" % (s["rel_score"], s["rel_tag"])) if s["rel_score"] is not None else "-",
                s["age_h"], s["velocity"] or "不可判", s["q3"] or "-",
                s["status"], esc((s["reason"] or "")[:40])))
        for sid in active_go:
            print("[GO 活跃] trend-%s(已过闸待发布;exit 1 接 notify/CI)" % sid)
        for p in briefs[:5]:
            print("决策件草稿: %s" % p)
        print("注:X/Twitter、抖音需 key——明说跳过不猜;热搜快照无历史,first_seen=我方首见,窗口判断偏保守是特性。")
    if not ok and (failed or skipped) and sources:
        print("[error] 全部信号源失败/空(%s)" % ",".join(failed or skipped), file=sys.stderr)
        return 2
    return 1 if active_go else 0


# ---------------------------------------------------------------- gate
def _gate_verdict(sig, q2_count, exclusive, wire, dup, now, th):
    """四问闸门判定矩阵(playbook 2.5)→ (verdict, verdict_type, reason, deadline, reasons[])。"""
    score = sig.get("rel_score")
    reasons = []
    if score is not None and score < SCORE_MED:
        return "drop", "", "Q1=%d<10(垂直无关)" % score, None, ["Q1 DROP(相关性 %d<10)" % score]
    if score is not None and score < th["relevance_min"]:
        return "watch", "", "Q1=%d 相关性不足(10-24)" % score, iso(now + timedelta(
            hours=th["window_analysis_h"])), ["Q1 WATCH(相关性 %d<%d)" % (score, th["relevance_min"])]
    if score is None:
        return "watch", "", "Q1 未打分(watch 需 --vertical/--topics 后重采样)", iso(now + timedelta(
            hours=th["window_analysis_h"])), ["Q1 UNKNOWN(未打分)"]
    if dup:
        return "drop", "", "重复否决:与活跃判定信号 trend-%s 词重叠>70%%(合并,不新开)" % dup, None, [
            "重复否决(overlap>70%% vs trend-%s)" % dup]
    if q2_count is None:
        return "watch", "", "Q2 待核(未提供 --angle;人工补 %d 净新观点)" % th["ig_views_min"], \
               iso(now + timedelta(hours=th["window_news_h"])), ["Q2 UNKNOWN(无角度文件)"]
    if q2_count < th["ig_views_min"]:
        return "watch", "", "Q2=%d 观点 <%d(信息增益不可行,等证据)" % (q2_count, th["ig_views_min"]), \
               iso(now + timedelta(hours=th["window_news_h"])), [
                   "Q2 FAIL(%d<%d 净新观点)" % (q2_count, th["ig_views_min"])]
    age = _age_hours(sig.get("first_seen"), now) or 0
    if wire and wire.get("n") is not None and wire["n"] >= th["wire_dominate_n"] and age < th["window_news_h"]:
        return "pivot", "", "硬新闻否决:wire %d 条且 %.1fh(<24h)——时效位让给 wire,转分析角度" % (
            wire["n"], age), iso(parse_iso(sig["first_seen"]) + timedelta(
                hours=th["window_analysis_h"])), [
            "wire 否决(%d 条 wire,%0.1fh)" % (wire["n"], age), "转分析角度(playbook 第 3 节)"]
    if not exclusive:
        return "pivot", "", "Q4 无独家视角(三选一缺)——转分析角度,不硬跟", iso(
            parse_iso(sig["first_seen"]) + timedelta(hours=th["window_analysis_h"])), [
            "Q4 UNKNOWN(无 --exclusive)", "转分析角度(playbook 第 3 节)"]
    win, wre = q3_window(sig, now, th)
    sig["q3"], sig["q3_reason"] = win, wre
    if win == "NEWS":
        return "go", "News 型", "四问全过(%s);24h 内发,news sitemap 48h 窗口" % wre, iso(
            parse_iso(sig["first_seen"]) + timedelta(hours=th["window_news_h"])), [
            "Q3 NEWS(%s)" % wre, "独家=%s(%s)" % (exclusive, EXCLUSIVE_LABEL.get(exclusive, ""))]
    if win == "ANALYSIS":
        return "go", "Analysis 型", "四问全过(%s);新闻位已占,做分析位" % wre, iso(
            parse_iso(sig["first_seen"]) + timedelta(hours=th["window_analysis_h"])), [
            "Q3 ANALYSIS(%s)" % wre, "独家=%s(%s)" % (exclusive, EXCLUSIVE_LABEL.get(exclusive, ""))]
    return "watch", "", "窗口 %s——只 WATCH,挂既有页刷新队列(8-12 周分层)" % wre, iso(
        now + timedelta(hours=th["window_analysis_h"])), ["Q3 LATE(%s)" % wre]


def cmd_gate(a):
    try:
        _cfg_tokens, wire_domains, th, _subs, _cfg = load_config(a.config, a.market or "en")
    except ValueError as e:
        print("[error] %s" % e, file=sys.stderr)
        return 3
    state = load_state(a.state)
    sig = state["signals"].get((a.signal_id or "").strip())
    if sig is None:
        print("[error] signal_id 不在信号库:%s(backlog 先查;exit 3=输入缺失)" % a.signal_id,
              file=sys.stderr)
        return 3
    now = _now()
    market = a.market or sig.get("market") or "en"
    angle_text = None
    if a.angle:
        try:
            with open(a.angle, encoding="utf-8") as f:
                angle_text = f.read()
        except OSError as e:
            print("[error] --angle 文件读取失败: %s(exit 3=输入缺失)" % e, file=sys.stderr)
            return 3
    q2_count = None if angle_text is None else count_angle_points(angle_text)

    # wire 否决机检(优先级最高;源失败=未检,明说不猜,按未触发处理)
    sig["wire"] = wire_check(sig["title"], market, wire_domains)
    if sig["wire"] is None:
        print("[warn] wire 检查源失败:未检(不猜,按未触发;人工核 Google News)", file=sys.stderr)

    dup = None
    ov_th = th["dedup_overlap_pct"] / 100.0
    for s in state["signals"].values():
        if s["signal_id"] != sig["signal_id"] and s.get("status") in ("go", "pivot") \
                and word_overlap(sig.get("tokens"), s.get("tokens")) > ov_th:
            dup = s["signal_id"]
            break

    verdict, vtype, reason, deadline, reasons = _gate_verdict(
        sig, q2_count, a.exclusive, sig["wire"], dup, now, th)
    prev = sig.get("status")
    sig.update({"status": verdict, "verdict_type": vtype, "reason": reason,
                "deadline": deadline, "gated_at": iso(now),
                "q2": (None if q2_count is None else
                       ("PASS(%d≥%d)" % (q2_count, th["ig_views_min"]) if q2_count >= th["ig_views_min"]
                        else "FAIL(%d<%d)" % (q2_count, th["ig_views_min"]))),
                "q4": a.exclusive})
    if a.angle:
        sig["angle_file"] = a.angle
    _history(sig, "gate", "%s → %s(%s)" % (prev, verdict, reason), now)
    save_state(a.state, state)
    brief = write_brief(sig, a.brief_dir, th, now)

    age = _age_hours(sig.get("first_seen"), now)
    wire = sig["wire"] or {}
    wire_vetoed = (wire.get("n") is not None and wire["n"] >= th["wire_dominate_n"]
                   and (age or 0) < th["window_news_h"])
    lines = {
        "q1": ("PASS(%d,%s)" % (sig["rel_score"], sig["rel_tag"])) if (
            (sig.get("rel_score") or 0) >= th["relevance_min"]) else (
            "DROP(%d<10)" % sig["rel_score"] if (sig.get("rel_score") is not None and
                                                 sig["rel_score"] < SCORE_MED) else
            ("MED(%d,10-24)" % sig["rel_score"] if sig.get("rel_score") is not None else "UNKNOWN(未打分)")),
        "q2": ("UNKNOWN(未提供 --angle)" if q2_count is None else
               ("PASS(%d 观点 ≥%d)" % (q2_count, th["ig_views_min"]) if q2_count >= th["ig_views_min"]
                else "FAIL(%d 观点 < %d)" % (q2_count, th["ig_views_min"]))),
        "q3": "%s(%s)" % (sig.get("q3") or "-", sig.get("q3_reason") or "-"),
        "q4": ("%s(%s)" % (a.exclusive, EXCLUSIVE_LABEL.get(a.exclusive, ""))
               if a.exclusive else "UNKNOWN(未提供 --exclusive)"),
        "wire": (("触发(%d/%d 条 wire,%.1fh<%dh→硬新闻)"
                  % (wire["n"], wire.get("total") or 0, age or 0, th["window_news_h"])) if wire_vetoed
                 else ("未触发(%d/%d)" % (wire.get("n") or 0, wire.get("total") or 0)
                       if wire.get("n") is not None else "未检(源失败,明说不猜)")),
    }
    if a.json:
        print(json.dumps({"signal_id": sig["signal_id"], "title": sig["title"],
                          "verdict": verdict, "verdict_type": vtype, "reason": reason,
                          "deadline": deadline, "reasons": reasons,
                          "q": lines, "brief": brief}, ensure_ascii=False, indent=1))
    else:
        print("=== gate: trend-%s · %s ===" % (sig["signal_id"], sig["title"]))
        print("Q1 相关性 : %s" % lines["q1"])
        print("Q2 信息增益: %s" % lines["q2"])
        print("Q3 时效窗口: %s" % lines["q3"])
        print("Q4 独家视角: %s" % lines["q4"])
        print("wire 否决  : %s" % lines["wire"])
        print("判定       : %s%s —— %s" % (verdict.upper(), ("(%s)" % vtype) if vtype else "", reason))
        if deadline:
            print("deadline   : %s" % deadline)
        if brief:
            print("决策件已更新: %s" % brief)
    return 0 if verdict == "go" else 1


# ---------------------------------------------------------------- backlog
_STATUS_ORDER = {"go": 0, "pivot": 1, "open": 2, "watch": 3, "drop": 4}


def cmd_backlog(a):
    state = load_state(a.state)
    now = _now()
    rows = []
    for sig in state["signals"].values():
        if a.status not in (None, "all") and sig.get("status") != a.status:
            continue
        last_age_d = _age_hours(sig.get("last_seen"), now)
        if a.days and last_age_d is not None and last_age_d / 24.0 > a.days \
                and sig.get("status") not in ("go", "pivot"):
            continue
        flags = []
        if len(sig.get("sources") or []) < 2 and sig.get("status") in ("open", "watch"):
            flags.append("单源")
        dl = sig.get("deadline")
        if dl and parse_iso(dl) and parse_iso(dl) < now and sig.get("status") in ("go", "pivot", "watch"):
            flags.append("到期未处理" + (";GO 过期→建议降级 WATCH/挂刷新队列,停止写作"
                                          if sig.get("status") == "go" else ";重看或清退"))
        rows.append({"signal_id": sig["signal_id"], "status": sig.get("status", "open"),
                     "title": sig.get("title", ""), "sources": sig.get("sources") or [],
                     "rel_score": sig.get("rel_score"), "q3": sig.get("q3"),
                     "velocity": sig.get("velocity"),
                     "age_h": round(_age_hours(sig.get("first_seen"), now) or 0, 1),
                     "deadline": dl, "verdict_type": sig.get("verdict_type") or "",
                     "reason": sig.get("reason") or "", "flags": flags})
    rows.sort(key=lambda r: (_STATUS_ORDER.get(r["status"], 9), r["deadline"] or "9999"))
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    if a.json:
        print(json.dumps({"ran_at": iso(now), "total": len(rows), "counts": counts,
                          "signals": rows}, ensure_ascii=False, indent=1))
        return 0
    print("=== backlog(%d 条;open/go/pivot/watch/drop = %s)===" % (
        len(rows), "/".join(str(counts.get(s, 0)) for s in ("open", "go", "pivot", "watch", "drop"))))
    print("| signal_id | 状态 | 标题 | 源 | Q1 | 窗口 | age | deadline | 标记 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print("| %s | %s%s | %s | %s | %s | %s | %sh | %s | %s |" % (
            r["signal_id"], r["status"], ("(%s)" % r["verdict_type"]) if r["verdict_type"] else "",
            esc(r["title"][:44]), "+".join(r["sources"]),
            r["rel_score"] if r["rel_score"] is not None else "-", r["q3"] or "-",
            r["age_h"], (r["deadline"] or "-")[:16], ";".join(r["flags"]) or "-"))
    expired = [r for r in rows if any(f.startswith("到期") for f in r["flags"])]
    if expired:
        print("[info] %d 条 deadline 到期(升退级提示):%s" % (
            len(expired), ",".join(r["signal_id"] for r in expired)))
    return 0


# ---------------------------------------------------------------- CLI
class _ArgParser(argparse.ArgumentParser):
    """argparse 参数错误 → exit 3(规格:3=配置/参数错误),不走默认 exit 2。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        print("[error] 参数错误: %s(exit 3)" % message, file=sys.stderr)
        sys.exit(3)


def build_parser():
    p = _ArgParser(prog="trend_watch.py",
                   description="热点监控与选题闸门(四问闸门+决策件;规格=trend-jack-playbook.md 第 0 节)")
    sub = p.add_subparsers(dest="cmd")

    w = sub.add_parser("watch", help="拉信号源→登记去重→Q1/Q3/wire 机检→决策件草稿")
    w.add_argument("--sources", default=None,
                   help="逗号分隔信号源(%s;默认按市场:zh=全部热搜源,其余=前三)"
                        % ",".join(SOURCE_FETCHERS))
    w.add_argument("--market", default="en", help="市场码(markets.json 18 市场;决定热搜源/wire 域名/locale)")
    w.add_argument("--vertical", default=None, help="垂直词(空格分隔 token;HIGH 整词+25/MED 部分+10)")
    w.add_argument("--topics", default=None, help="垂直词文件(优先于 --vertical;与 config vertical_tokens 同源)")
    w.add_argument("--config", default=None, help="trend_watch.json(signal_sources/wire_domains/thresholds 等)")
    w.add_argument("--panel", default=None, help="可选 citation_panel 面板(已有覆盖→优先刷新既有页)")
    w.add_argument("--brief-dir", default="briefs", help="决策件目录(默认 briefs/)")
    w.add_argument("--state", default=STATE_FILE, help="状态库路径(默认 .trend-state.json)")
    w.add_argument("--json", action="store_true", help="机读输出")
    w.set_defaults(func=cmd_watch)

    g = sub.add_parser("gate", help="对单个 signal_id 补 Q2/Q4 机检,出终判")
    g.add_argument("--signal-id", required=True, help="信号 ID(watch/backlog 查)")
    g.add_argument("--angle", "--angle-file", dest="angle", default=None,
                   help="角度文档(净新观点清单;playbook 2.2 表格或列表,≥ig_views_min 条过 Q2)")
    g.add_argument("--exclusive", default=None, choices=["data", "quote", "access"],
                   help="独家三选一:data=自有数据 / quote=SME 引语 / access=一手访问")
    g.add_argument("--market", default=None, help="市场码(默认用信号登记时的市场)")
    g.add_argument("--config", default=None)
    g.add_argument("--brief-dir", default="briefs")
    g.add_argument("--state", default=STATE_FILE)
    g.add_argument("--json", action="store_true")
    g.set_defaults(func=cmd_gate)

    b = sub.add_parser("backlog", help="信号库总览(open/go/pivot/watch/drop;deadline 到期标记)")
    b.add_argument("--status", default="all",
                   choices=["open", "go", "pivot", "watch", "drop", "all"])
    b.add_argument("--days", type=int, default=14, help="回看窗口(按 last_seen;0=全部)")
    b.add_argument("--state", default=STATE_FILE)
    b.add_argument("--json", action="store_true")
    b.set_defaults(func=cmd_backlog)
    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    a = build_parser().parse_args(argv)   # -h/--help 由 argparse 处理(exit 0)
    if not getattr(a, "cmd", None):
        build_parser().print_help()
        return 3
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
