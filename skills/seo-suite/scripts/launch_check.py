#!/usr/bin/env python3
"""launch_check.py — 上线清单:能自动查的查掉,查不了的列出来写负责人(RQ-237 第 2 批;stdlib only)。

清单在 data/launch-checklist.json(auto 项脚本查,manual 项列负责人和截止日)。在本地预览、预发环境或
刚上线的正式站上都能跑;本地预览加 --allow-local(只放行本机回环,和 site_crawl 同一套 SSRF 守卫)。
--prod-host 写正式域名时,canonical 指向别的域名(比如 localhost、预发域名)会判不通过——这是上线前
最常见的错。负责人:默认用清单里的角色,seo-ops/plan/launch-owners.json({"<id>": "名字", "<id>@due": "日期"})
或 --owners 文件覆盖。

用法:
  python3 launch_check.py --url http://localhost:3000 --allow-local --prod-host example.com [--sample 8]
                          [--ws seo-ops] [--owners owners.json] [--json] [--md] [--strict] [--out FILE]
退出码:0 正常(--strict 时有 block 项不通过返回 1);2 输入错。
"""
import argparse
import json
import os
import random
import string
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import site_crawl as sc  # noqa: E402

CHECKLIST = os.path.join(os.path.dirname(HERE), "data", "launch-checklist.json")
AI_BOTS = ("gptbot", "oai-searchbot", "chatgpt-user", "claudebot", "claude-searchbot", "perplexitybot",
           "google-extended", "ccbot", "applebot-extended", "bytespider")
SPEED_MS = 800
LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1", "[::1]")


class UsageError(Exception):
    pass


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


class HeadParser(sc.PageParser):
    """site_crawl.PageParser 之外多收:viewport、og:title、og:image、favicon、JSON-LD 类型。"""

    def __init__(self):
        super().__init__()
        self.viewport = False
        self.og_title = None
        self.og_image = None
        self.favicon = False
        self.ld_raw, self._ld = [], None

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        a = {k.lower(): (v if v is not None else "") for k, v in attrs}
        if tag == "meta":
            nm = (a.get("name") or a.get("property") or "").strip().lower()
            if nm == "viewport":
                self.viewport = True
            elif nm == "og:title" and self.og_title is None:
                self.og_title = (a.get("content") or "").strip()
            elif nm == "og:image" and self.og_image is None:
                self.og_image = (a.get("content") or "").strip()
        elif tag == "link" and "icon" in (a.get("rel") or "").lower().split():
            self.favicon = True
        elif tag == "script" and (a.get("type") or "").strip().lower() == "application/ld+json":
            self._ld = []

    def handle_endtag(self, tag):
        super().handle_endtag(tag)
        if tag == "script" and self._ld is not None:
            self.ld_raw.append("".join(self._ld))
            self._ld = None

    def handle_data(self, d):
        if self._ld is not None:
            self._ld.append(d)
            return
        super().handle_data(d)


def ld_types(raw_blocks):
    out = []

    def walk(n):
        if isinstance(n, list):
            for x in n:
                walk(x)
        elif isinstance(n, dict):
            t = n.get("@type")
            out.extend(t if isinstance(t, list) else [t] if t else [])
            for k in ("@graph",):
                if k in n:
                    walk(n[k])
    for b in raw_blocks:
        try:
            walk(json.loads(b))
        except ValueError:
            continue
    return [t for t in out if isinstance(t, str)]


class Site:
    def __init__(self, base, errors):
        self.base = base.rstrip("/")
        self.errors = errors

    def get(self, path_or_url):
        url = path_or_url if path_or_url.startswith("http") else self.base + path_or_url
        t0 = time.monotonic()
        try:
            r = sc.robust_fetch(url, timeout=15)
        except (sc.GuardError, sc.FetchError) as e:
            self.errors.append("抓取失败 %s: %s" % (url, e))
            return None
        r["elapsed_ms"] = int((time.monotonic() - t0) * 1000)
        return r


def parse_page(resp):
    p = HeadParser()
    try:
        p.feed((resp.get("body") or "")[:sc.PAGE_READ_CAP])
    except Exception:  # noqa: BLE001 — 坏 HTML 不抛
        pass
    names = set()
    for v in p.robots_meta:
        names |= sc.robots_names(v)
    xrt = sc._header(resp.get("headers"), "x-robots-tag")
    if xrt:
        names |= sc.header_robots(xrt)
    return {"url": resp.get("final_url"), "status": resp.get("status"), "title": (p.title or "").strip() or None,
            "description": next((d for d in p.descriptions if d), None), "h1": len([h for h in p.h1s if h]),
            "canonical": p.canonical, "noindex": "noindex" in names or "none" in names, "lang": p.lang,
            "hreflangs": p.hreflangs, "viewport": p.viewport, "og_title": p.og_title, "og_image": p.og_image,
            "favicon": p.favicon, "ld_types": ld_types(p.ld_raw), "hrefs": p.hrefs}


def sitemap_urls(site, robots):
    seeds = list((robots or {}).get("sitemaps") or []) or [site.base + "/sitemap.xml"]
    urls, seen, declared = [], set(), bool((robots or {}).get("sitemaps"))
    queue = list(seeds)
    while queue and len(seen) < 10:
        u = queue.pop(0)
        if u in seen:
            continue
        seen.add(u)
        r = site.get(u)
        if not r or (r.get("status") or 0) >= 400:
            continue
        body = r.get("body") or ""
        locs = [x.strip() for x in __import__("re").findall(r"<loc>\s*([^<\s]+)\s*</loc>", body)]
        if "<sitemapindex" in body:
            queue.extend(locs)
        else:
            urls.extend(locs)
    return urls, declared, seeds


def pick_sample(urls, base, n):
    """首页之外按第一段路径分组各取一条,保证不同模板都抽到。"""
    host = urllib.parse.urlsplit(base).netloc
    groups = {}
    for u in urls:
        s = urllib.parse.urlsplit(u)
        seg = (s.path.strip("/").split("/") or [""])[0]
        groups.setdefault(seg, []).append(u)
    out = []
    for seg in sorted(groups, key=lambda k: -len(groups[k])):
        out.append(groups[seg][0])
        if len(out) >= n:
            break
    # sitemap 里写的是正式域名、在本地预览上跑时,换成预览地址抓
    fixed = []
    for u in out:
        s = urllib.parse.urlsplit(u)
        if s.netloc != host:
            u = urllib.parse.urlunsplit(urllib.parse.urlsplit(base)[:2] + s[2:])
        fixed.append(u)
    return fixed


def run_checks(base, prod_host=None, sample=8):
    errors = []
    site = Site(base, errors)
    host = urllib.parse.urlsplit(base).hostname or ""
    is_local = host in LOCAL_HOSTS or host.endswith(".localhost")
    res = {}

    def put(id_, status, evidence):
        res[id_] = {"status": status, "evidence": evidence}

    home_r = site.get("/")
    if not home_r or home_r.get("status") != 200:
        put("reachable", "fail", "首页状态 %s" % (home_r or {}).get("status"))
        return res, errors, []
    put("reachable", "pass", "首页 200,%d ms" % home_r["elapsed_ms"])
    home = parse_page(home_r)

    # https
    if is_local:
        put("https", "skip", "本地预览不查,正式站上线后再跑一次")
    elif base.startswith("https://"):
        hr = site.get("http://" + base.split("://", 1)[1] + "/")
        if hr and (hr.get("final_url") or "").startswith("https://"):
            put("https", "pass", "HTTP 跳到 %s" % hr.get("final_url"))
        else:
            put("https", "fail", "HTTP 没有跳到 HTTPS")
    else:
        put("https", "fail", "正式站不是 HTTPS")

    # robots
    rr = site.get("/robots.txt")
    robots = sc.parse_robots(rr.get("body") or "") if rr and rr.get("status") == 200 else None
    if not robots:
        put("robots", "fail", "robots.txt 不存在或为空")
    else:
        star = robots["groups"].get("*", {})
        if "/" in [d.strip() for d in star.get("disallow", [])] and "/" not in [a.strip() for a in star.get("allow", [])]:
            put("robots", "fail", "User-agent: * 下有 Disallow: /(预发环境的封锁要在上线时撤掉)")
        else:
            put("robots", "pass", "robots.txt 存在,没有全站封锁")

    # sitemap + 抽样
    urls, declared, seeds = sitemap_urls(site, robots)
    if urls:
        put("sitemap", "pass" if declared else "warn",
            "%d 条 URL;%s" % (len(urls), "robots.txt 里声明了" if declared else "robots.txt 没声明 Sitemap:"))
    else:
        put("sitemap", "fail", "读不到 sitemap(试了 %s)" % ", ".join(seeds))
    pages = [home]
    for u in pick_sample(urls, base, sample):
        if u.rstrip("/") == base.rstrip("/"):
            continue
        r = site.get(u)
        if r and r.get("status") == 200:
            pages.append(parse_page(r))
    n = len(pages)

    blocked = [p["url"] for p in pages if p["noindex"]]
    put("noindex", "fail" if blocked else "pass",
        ("noindex:" + ", ".join(blocked[:5])) if blocked else "%d 页都没有 noindex" % n)

    bad = []
    for p in pages:
        c = p["canonical"]
        if not c:
            bad.append("%s 没有 canonical" % p["url"])
            continue
        cs = urllib.parse.urlsplit(c)
        if not cs.scheme:
            bad.append("%s 的 canonical 不是绝对地址:%s" % (p["url"], c))
        elif prod_host and (cs.hostname or "") != prod_host:
            bad.append("%s 的 canonical 指向 %s,不是正式域名 %s" % (p["url"], cs.hostname, prod_host))
        elif not prod_host and (cs.hostname or "") in LOCAL_HOSTS:
            bad.append("%s 的 canonical 指向本机 %s" % (p["url"], cs.hostname))
    put("canonical", "fail" if bad else "pass", "; ".join(bad[:4]) if bad else "%d 页 canonical 正常" % n)

    miss = [p["url"] for p in pages if not p["title"] or not p["description"]]
    titles = [p["title"] for p in pages if p["title"]]
    dup = sorted({t for t in titles if titles.count(t) > 1})
    if miss or dup:
        put("titles", "fail", "; ".join((["缺 title 或描述:" + ", ".join(miss[:4])] if miss else []) +
                                        (["重复 title:" + " | ".join(dup[:3])] if dup else [])))
    else:
        put("titles", "pass", "%d 页 title 和描述齐全、不重复" % n)

    h1bad = ["%s(%d 个)" % (p["url"], p["h1"]) for p in pages if p["h1"] != 1]
    put("h1", "warn" if h1bad else "pass", ("H1 不是 1 个:" + ", ".join(h1bad[:4])) if h1bad else "%d 页各 1 个 H1" % n)
    put("lang", "pass" if home["lang"] else "fail", "lang=%s" % home["lang"] if home["lang"] else "html 没写 lang")

    hl = [p for p in pages if p["hreflangs"]]
    if not hl:
        put("hreflang", "skip", "抽查页没有 hreflang(单语言站不需要)")
    else:
        # Google:每个语言版本必须列出自身和其他版本(硬要求);x-default 是建议(localized-versions 文档)
        prob, soft = [], []
        for p in hl:
            codes = [c.lower() for c, _ in p["hreflangs"]]
            hrefs = [h for _, h in p["hreflangs"]]
            path = urllib.parse.urlsplit(p["url"]).path.rstrip("/")
            if not any(urllib.parse.urlsplit(h).path.rstrip("/") == path for h in hrefs):
                prob.append("%s 的 hreflang 不含自身" % p["url"])
            if any(not urllib.parse.urlsplit(h).scheme for h in hrefs):
                prob.append("%s 的 hreflang 不是完整地址" % p["url"])
            if "x-default" not in codes:
                soft.append("%s 缺 x-default(建议加)" % p["url"])
        if prob:
            put("hreflang", "fail", "; ".join((prob + soft)[:4]))
        elif soft:
            put("hreflang", "warn", "; ".join(soft[:4]))
        else:
            put("hreflang", "pass", "%d 页 hreflang 含自身和 x-default" % len(hl))

    types = set(home["ld_types"])
    put("jsonld", "pass" if types & {"Organization", "WebSite", "Corporation", "OnlineBusiness"} else "warn",
        "首页结构化数据类型:%s" % (", ".join(sorted(types)) or "无"))
    og_ok = bool(home["og_title"] and home["og_image"] and home["og_image"].startswith("http"))
    og_note = ""
    if og_ok and prod_host and (urllib.parse.urlsplit(home["og_image"]).hostname or "") not in (prod_host, ""):
        og_ok, og_note = False, "(og:image 不在正式域名下,上线后会裂图)"
    put("og", "pass" if og_ok else "warn",
        "og:title=%s,og:image=%s%s" % (bool(home["og_title"]), home["og_image"] or "无", og_note))
    put("viewport", "pass" if home["viewport"] else "fail", "有 viewport" if home["viewport"] else "没有 viewport meta")

    junk = "/" + "".join(random.choice(string.ascii_lowercase) for _ in range(12)) + "-launch-check"
    nf = site.get(junk)
    st = (nf or {}).get("status")
    put("not_found", "pass" if st == 404 or st == 410 else "fail", "%s 返回 %s" % (junk, st))

    ms = home_r["elapsed_ms"]
    put("speed", "pass" if ms < SPEED_MS else "warn",
        "首页 %d ms%s" % (ms, "(本地预览,只作参考)" if is_local else ""))

    lr = site.get("/llms.txt")
    put("llms_txt", "pass" if lr and lr.get("status") == 200 and (lr.get("body") or "").strip() else "info",
        "有 llms.txt" if lr and lr.get("status") == 200 else "没有 llms.txt(可选)")

    if robots:
        named = sorted(b for b in AI_BOTS if b in robots["groups"])
        put("ai_crawlers", "pass" if named else "info",
            ("robots.txt 单独写了:" + ", ".join(named)) if named else "robots.txt 没单独写 AI 爬虫,按 * 组处理;确认这是有意的")
    else:
        put("ai_crawlers", "info", "没有 robots.txt,AI 爬虫全放行;确认这是有意的")

    fav = home["favicon"]
    if not fav:
        fr = site.get("/favicon.ico")
        fav = bool(fr and fr.get("status") == 200)
    put("favicon", "pass" if fav else "info", "有 favicon" if fav else "没找到 favicon")
    return res, errors, [p["url"] for p in pages]


def load_owners(ws, owners_path):
    out = {}
    for p in ([os.path.join(ws, "plan", "launch-owners.json")] if ws else []) + ([owners_path] if owners_path else []):
        d = read_json(p, {})
        if isinstance(d, dict):
            out.update({str(k): str(v) for k, v in d.items()})
    return out


def build(base, prod_host=None, sample=8, ws=None, owners_path=None):
    cl = read_json(CHECKLIST)
    if not cl:
        raise UsageError("读不到清单 %s" % CHECKLIST)
    res, errors, sampled = run_checks(base, prod_host, sample)
    owners = load_owners(ws, owners_path)
    items = []
    for it in cl["items"]:
        r = res.get(it["id"]) if it["kind"] == "auto" else None
        if it["kind"] == "auto" and r is None:
            r = {"status": "skip", "evidence": "首页打不开,没查"}
        status = r["status"] if r else "manual"
        items.append({"id": it["id"], "area": it["area"], "kind": it["kind"], "severity": it["severity"],
                      "title": it["title"], "title_en": it["title_en"], "status": status,
                      "evidence": r["evidence"] if r else "", "owner": owners.get(it["id"], it["owner"]),
                      "owner_is_default": it["id"] not in owners, "due": owners.get(it["id"] + "@due", "")})
    blockers = [i["id"] for i in items if i["severity"] == "block" and i["status"] == "fail"]
    auto = [i for i in items if i["kind"] == "auto" and i["status"] not in ("skip",)]
    summary = {"auto_total": len(auto), "auto_pass": sum(1 for i in auto if i["status"] == "pass"),
               "blockers": blockers, "manual": sum(1 for i in items if i["kind"] == "manual"),
               "ready": not blockers}
    return {"schema": 1, "url": base, "prod_host": prod_host, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "sampled": sampled, "summary": summary, "items": items, "errors": errors}


MARK = {"pass": "✅", "fail": "❌", "warn": "⚠️", "info": "ℹ️", "skip": "—", "manual": "☐"}


def render_md(rep):
    s = rep["summary"]
    L = ["# 上线清单:%s" % rep["url"], "",
         "- 自动项通过 %d / %d;手动项 %d 条" % (s["auto_pass"], s["auto_total"], s["manual"]),
         "- 能不能上线:%s" % ("可以(没有 block 项不通过)" if s["ready"] else "不行,先修:" + "、".join(s["blockers"])),
         "- 抽查了 %d 页:%s" % (len(rep["sampled"]), ", ".join(rep["sampled"][:8])), "",
         "| | 项 | 级别 | 结果 | 负责人 | 截止 |", "|---|---|---|---|---|---|"]
    for i in rep["items"]:
        owner = i["owner"] + ("(默认角色,请改成具体的人)" if i["owner_is_default"] else "")
        L.append("| %s | %s:%s | %s | %s | %s | %s |" % (MARK.get(i["status"], i["status"]), i["area"], i["title"],
                                                      i["severity"], (i["evidence"] or "手动核对").replace("|", "/"),
                                                      owner, i["due"] or "—"))
    if rep["errors"]:
        L += ["", "抓取问题:"] + ["- " + e for e in rep["errors"][:10]]
    L += ["", "负责人和截止日写进 `seo-ops/plan/launch-owners.json`:`{\"gsc_verify\": \"张三\", \"gsc_verify@due\": \"2026-12-01\"}`。"]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="上线清单:自动项脚本查,手动项写负责人")
    ap.add_argument("--url", required=True, help="预览、预发或正式站根地址")
    ap.add_argument("--prod-host", help="正式域名(例 example.com);canonical 必须指向它")
    ap.add_argument("--sample", type=int, default=8, help="首页之外从 sitemap 按模板抽几页(默认 8)")
    ap.add_argument("--allow-local", action="store_true", help=sc.LOCAL_HINT)
    ap.add_argument("--ws", help="seo-ops 工作区(读 plan/launch-owners.json)")
    ap.add_argument("--owners", help="负责人 JSON")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--strict", action="store_true", help="有 block 项不通过时退出码 1")
    ns = ap.parse_args(argv)
    sc.ALLOW_LOCAL = bool(ns.allow_local)
    try:
        rep = build(ns.url, ns.prod_host, max(0, ns.sample), ns.ws, ns.owners)
    except UsageError as e:
        print("错误:%s" % e, file=sys.stderr)
        return 2
    text = json.dumps(rep, ensure_ascii=False, indent=1) if (ns.json or not ns.md) else render_md(rep)
    if ns.out:
        with open(ns.out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)
    return 1 if (ns.strict and rep["summary"]["blockers"]) else 0


if __name__ == "__main__":
    sys.exit(main())
