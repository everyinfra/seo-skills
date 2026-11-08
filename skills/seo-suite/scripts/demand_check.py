#!/usr/bin/env python3
"""demand_check.py — 想法阶段的需求验证和起名核对(RQ-237 第 2 批;stdlib only,不要 key)。

需求验证(--seeds / --seed):对每个种子词,从三家公开联想接口(Google、Bing、DuckDuckGo)取联想词,
再加问题词和商业修饰词(how / best / vs / 价格 / 推荐…)各取一轮,汇总成:
  - 有没有人搜:几家引擎返回了联想、一共多少条不重复的联想词 → 信号 强 / 弱 / 没有
  - 搜什么:问题词、比较词、价格词各几条(意图分布)
  - 结果里已经是谁:联想词里反复出现、种子里没有的词(多半是品牌或品类名)
联想词数量不是搜索量,只是「有人在搜」的信号,报告里标 [est];有关键词工具导出的,用
--volumes keyword,volume 的 CSV 补月搜索量(标 [real])。

起名核对(--names a,b):每个名字查 RDAP(rdap.org)看各后缀域名有没有被注册(404 = 没查到注册记录,
多半可注册,以注册商为准),再看搜这个名字时的联想是不是已经被别的东西占满。

用法:
  python3 demand_check.py --seeds seeds.txt [--seed "invoice software"] [--market en] [--no-modifiers]
                          [--volumes vol.csv] [--names petledger,pawbook --tlds com,io,app] [--json|--md] [--out FILE]
退出码:0 正常;2 输入错。网络失败的接口记进 errors,不中断。
"""
import argparse
import collections
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) seo-suite-demand-check"
DELAY = 0.25
TIMEOUT = 10

HL = {"zh": ("zh-CN", "cn", "zh-CN"), "en": ("en", "us", "en-US"), "ja": ("ja", "jp", "ja-JP"),
      "ko": ("ko", "kr", "ko-KR"), "ru": ("ru", "ru", "ru-RU"), "es": ("es", "es", "es-ES"),
      "pt": ("pt-BR", "br", "pt-BR"), "fr": ("fr", "fr", "fr-FR"), "de": ("de", "de", "de-DE"),
      "it": ("it", "it", "it-IT"), "id": ("id", "id", "id-ID"), "tr": ("tr", "tr", "tr-TR"),
      "vi": ("vi", "vn", "vi-VN"), "th": ("th", "th", "th-TH"), "pl": ("pl", "pl", "pl-PL"),
      "nl": ("nl", "nl", "nl-NL"), "ar": ("ar", "sa", "ar-SA"), "hi": ("hi", "in", "hi-IN")}

# 修饰词:按意图分;没有的市场退回英文
MODIFIERS = {
    "en": {"question": ["how to", "what is", "why"], "compare": ["vs", "alternative", "best"],
           "price": ["pricing", "free", "cost"]},
    "zh": {"question": ["怎么", "是什么", "如何"], "compare": ["哪个好", "推荐", "对比"],
           "price": ["价格", "免费", "多少钱"]},
    "ja": {"question": ["とは", "やり方"], "compare": ["おすすめ", "比較"], "price": ["料金", "無料"]},
    "es": {"question": ["como", "que es"], "compare": ["mejor", "alternativa"], "price": ["precio", "gratis"]},
}
QUESTION_RE = re.compile(r"^(how|what|why|when|where|which|who|can|is|are|does|do)\b|\?$|怎么|如何|是什么|为什么|哪|吗$|とは|やり方|como\b|que es|qué", re.I)
COMPARE_RE = re.compile(r"\bvs\.?\b|versus|alternative|compare|comparison|\bbest\b|\btop\b|对比|哪个好|推荐|排行|比較|おすすめ|mejor|alternativa", re.I)
PRICE_RE = re.compile(r"pric|cost|\bfree\b|cheap|价格|免费|多少钱|收费|料金|無料|precio|gratis", re.I)
STOP = set("the a an of for to in on and or with how what is are why best vs free pricing cost near me app apps "
           "online software tool tools api 的 是 吗 怎么 如何".split())


class Net:
    def __init__(self, errors):
        self.errors = errors
        self.n = 0

    def get(self, url):
        if self.n:
            time.sleep(DELAY)
        self.n += 1
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,*/*"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, ""
        except Exception as e:  # noqa: BLE001 — 网络层什么都可能抛
            self.errors.append("请求失败 %s: %s" % (urllib.parse.urlsplit(url).netloc, e))
            return None, ""


def _osjson(body):
    try:
        d = json.loads(body)
        return [s for s in d[1] if isinstance(s, str)] if isinstance(d, list) and len(d) > 1 else []
    except (ValueError, TypeError, IndexError):
        return []


def suggest(net, q, market):
    hl, gl, mkt = HL.get(market, (market, "", market))
    out = {}
    eq = urllib.parse.quote(q)
    st, b = net.get("https://suggestqueries.google.com/complete/search?client=firefox&hl=%s&gl=%s&q=%s" % (hl, gl, eq))
    out["google"] = _osjson(b) if st == 200 else None
    st, b = net.get("https://api.bing.com/osjson.aspx?query=%s&mkt=%s" % (eq, mkt))
    out["bing"] = _osjson(b) if st == 200 else None
    st, b = net.get("https://duckduckgo.com/ac/?q=%s&type=list&kl=%s" % (eq, (gl + "-" + hl.split("-")[0]).lower() if gl else "wt-wt"))
    out["duckduckgo"] = _osjson(b) if st == 200 else None
    return out


def norm(s):
    return " ".join(s.lower().split())


def tokens(s):
    if re.search(r"[一-鿿぀-ヿ]", s):
        return [w for w in re.split(r"[\s,，、/|]+", s) if w]
    return re.findall(r"[a-z0-9][a-z0-9.\-]+", s.lower())


def seed_report(net, seed, market, modifiers=True):
    queries = [seed]
    mods = MODIFIERS.get(market, MODIFIERS["en"])
    if modifiers:
        for kind in ("question", "compare", "price"):
            for m in mods[kind]:
                queries.append("%s %s" % (m, seed) if kind == "question" and market in ("en", "es") else "%s %s" % (seed, m))
    per_engine = collections.defaultdict(set)
    allsug = collections.OrderedDict()
    for q in queries:
        for eng, lst in suggest(net, q, market).items():
            if lst is None:
                continue
            for s in lst:
                n = norm(s)
                if n == norm(q):
                    continue
                per_engine[eng].add(n)
                allsug.setdefault(n, set()).add(eng)
    base = suggest_base_count = len({s for e in per_engine.values() for s in e})
    engines_with = sorted(e for e, v in per_engine.items() if len(v) >= 3)
    if len(engines_with) >= 2 and base >= 10:
        signal = "强"
    elif base >= 3:
        signal = "弱"
    else:
        signal = "没有"
    sugs = list(allsug)
    qs = [s for s in sugs if QUESTION_RE.search(s)]
    cs = [s for s in sugs if COMPARE_RE.search(s)]
    ps = [s for s in sugs if PRICE_RE.search(s)]
    seed_tok = set(tokens(seed))
    cnt = collections.Counter()
    for s in sugs:
        for t in set(tokens(s)) - seed_tok:
            if t not in STOP and len(t) > 2 and not t.isdigit():
                cnt[t] += 1
    names = [w for w, c in cnt.most_common(12) if c >= 2]
    core = [t for t in seed_tok if t not in STOP]
    on = [s for s in sugs if all(t in s for t in core)] if core else sugs
    on_topic = round(len(on) / len(sugs), 2) if sugs else None
    drift = None
    if on_topic is not None and on_topic < 0.4 and names:
        drift = "联想里只有 %d%% 同时含「%s」,常和别的词一起出现:%s——这个叫法可能被理解成别的东西,换个叫法再验" % (
            int(on_topic * 100), " ".join(core), "、".join(names[:3]))
    return {"seed": seed, "signal": signal, "on_topic": on_topic, "drift": drift, "suggestions": suggest_base_count, "engines": engines_with,
            "agree": sorted(s for s, e in allsug.items() if len(e) >= 2)[:20],
            "intent": {"question": len(qs), "compare": len(cs), "price": len(ps)},
            "examples": {"question": qs[:6], "compare": cs[:6], "price": ps[:6], "other": [s for s in sugs if s not in qs + cs + ps][:8]},
            "recurring_terms": names, "queries": len(queries)}


def rdap(net, name, tlds):
    out = {}
    for t in tlds:
        dom = "%s.%s" % (name.lower(), t.strip(".").lower())
        st, _ = net.get("https://rdap.org/domain/" + urllib.parse.quote(dom))
        out[dom] = "已注册" if st == 200 else ("没查到注册记录(多半可注册,以注册商为准)" if st == 404 else "查不到(%s)" % st)
    return out


def name_report(net, name, tlds, market):
    sug = suggest(net, name, market)
    lst = sorted({norm(s) for v in sug.values() if v for s in v if norm(s) != norm(name)})
    nm = norm(name)
    starts = [s for s in lst if s.startswith(nm + " ") or s == nm]
    other = [s for s in lst if nm not in s.replace(" ", "")] if lst else []
    if not lst:
        crowd = "空(搜这个名字时没有联想,好占)"
    elif len(starts) >= 5:
        crowd = "满(已经有东西叫这个名字,联想以它开头的有 %d 条)" % len(starts)
    else:
        crowd = "少量(%d 条联想)" % len(lst)
    return {"name": name, "domains": rdap(net, name, tlds), "autocomplete": crowd, "examples": lst[:8],
            "unrelated": other[:5]}


def load_volumes(path):
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if len(row) >= 2 and row[1].strip().replace(",", "").isdigit():
                out[norm(row[0])] = int(row[1].strip().replace(",", ""))
    return out


def read_seeds(path, extra):
    seeds = []
    if path:
        with open(path, encoding="utf-8") as f:
            seeds += [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    seeds += [s for s in (extra or []) if s.strip()]
    return list(collections.OrderedDict.fromkeys(seeds))


def build(seeds, market="en", names=None, tlds=("com",), volumes=None, modifiers=True):
    errors = []
    net = Net(errors)
    rep = {"schema": 1, "market": market, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "basis": "联想词数量是「有人在搜」的信号,不是搜索量 [est];volume 列来自用户给的关键词工具导出 [real]",
           "seeds": [], "names": [], "errors": errors}
    for s in seeds:
        r = seed_report(net, s, market, modifiers)
        if volumes is not None:
            r["volume"] = volumes.get(norm(s))
        rep["seeds"].append(r)
    for n in names or []:
        rep["names"].append(name_report(net, n, tlds, market))
    strong = [r["seed"] for r in rep["seeds"] if r["signal"] == "强"]
    none_ = [r["seed"] for r in rep["seeds"] if r["signal"] == "没有"]
    rep["summary"] = {"seeds": len(seeds), "strong": strong, "none": none_,
                      "engines_failed": sorted({e.split()[1] for e in errors if e.startswith("请求失败")})}
    return rep


def render_md(rep):
    L = ["# 需求验证(市场 %s)" % rep["market"], "", "> " + rep["basis"], ""]
    if rep["seeds"]:
        L += ["| 种子词 | 信号 | 联想词 | 引擎 | 问题 / 比较 / 价格 | 反复出现的词 |" + (" 月搜索量 |" if "volume" in rep["seeds"][0] else ""),
              "|---|---|---|---|---|---|" + ("---|" if "volume" in rep["seeds"][0] else "")]
        for r in rep["seeds"]:
            i = r["intent"]
            row = "| %s | %s | %d [est] | %s | %d / %d / %d | %s |" % (
                r["seed"], r["signal"], r["suggestions"], ",".join(r["engines"]) or "—",
                i["question"], i["compare"], i["price"], "、".join(r["recurring_terms"][:6]) or "—")
            if "volume" in r:
                row += " %s |" % ("%s [real]" % r["volume"] if r["volume"] is not None else "—")
            L.append(row)
        L.append("")
        for r in rep["seeds"]:
            ex = r["examples"]
            L.append("**%s**:问题 %s;比较 %s;价格 %s" % (r["seed"], "、".join(ex["question"][:4]) or "—",
                                                     "、".join(ex["compare"][:4]) or "—", "、".join(ex["price"][:4]) or "—"))
            if r.get("drift"):
                L.append("  - 注意:" + r["drift"])
        L.append("")
    if rep["names"]:
        L += ["## 起名核对", "", "| 名字 | 域名 | 搜这个名字时 |", "|---|---|---|"]
        for n in rep["names"]:
            L.append("| %s | %s | %s |" % (n["name"], ";".join("%s %s" % (d, s) for d, s in n["domains"].items()),
                                           n["autocomplete"]))
        L.append("")
    s = rep["summary"]
    L += ["结论:%d 个种子词里信号强 %d 个(%s),没有信号 %d 个(%s)。" % (
        s["seeds"], len(s["strong"]), "、".join(s["strong"]) or "—", len(s["none"]), "、".join(s["none"]) or "—")]
    if rep["errors"]:
        L += ["", "接口问题:"] + ["- " + e for e in rep["errors"][:8]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="想法阶段:联想词验证需求 + 起名核对(不要 key)")
    ap.add_argument("--seeds", help="种子词文件,一行一个")
    ap.add_argument("--seed", action="append", help="种子词,可多次")
    ap.add_argument("--market", default="en")
    ap.add_argument("--no-modifiers", action="store_true", help="只查种子词本身,不加问题和商业修饰词")
    ap.add_argument("--volumes", help="关键词工具导出 CSV:keyword,volume")
    ap.add_argument("--names", help="候选名字,逗号分隔")
    ap.add_argument("--tlds", default="com,io,ai,app,dev")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--out")
    ns = ap.parse_args(argv)
    try:
        seeds = read_seeds(ns.seeds, ns.seed)
        vols = load_volumes(ns.volumes) if ns.volumes else None
    except OSError as e:
        print("错误:%s" % e, file=sys.stderr)
        return 2
    names = [n.strip() for n in (ns.names or "").split(",") if n.strip()]
    if not seeds and not names:
        print("错误:至少给 --seeds / --seed 或 --names", file=sys.stderr)
        return 2
    rep = build(seeds, ns.market, names, [t for t in ns.tlds.split(",") if t.strip()], vols, not ns.no_modifiers)
    text = render_md(rep) if ns.md and not ns.json else json.dumps(rep, ensure_ascii=False, indent=1)
    if ns.out:
        with open(ns.out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
