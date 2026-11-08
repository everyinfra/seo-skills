#!/usr/bin/env python3
"""site_move.py — 改版 / 迁移保护:改动前存基线,改动后逐条对比(RQ-237 第 3 批;stdlib only)。

  baseline  改动前抓一遍:sitemap + 站内链接能到的页面,每页记状态码、title、H1、canonical、hreflang、
            结构化数据类型、noindex、站内链接;可选 --gsc-pages 合进每页近 28 天点击。
  compare   改动后对比:旧 URL 在新站上怎么跳(一跳 301 到映射表里的地址才算对),新页面的 canonical、
            hreflang、站内链接、sitemap 是不是还指向旧址或跳转;结构化数据、noindex、title 有没有丢。
            映射表 --map 可以是 CSV(old,new)或 Markdown 表(| 旧 | 新 |,比如 MIGRATION.md)。

查的问题(type):
  missing_redirect   旧 URL 在新站上直接 404 / 410(漏 301)
  redirect_chain     旧 URL 跳了不止一跳
  temporary_redirect 用了 302 / 303 / 307(不是 301 / 308)
  bad_target         跳转终点不是 200
  wrong_target       跳到了映射表以外的地址
  to_homepage        深层旧 URL 被跳到首页(软 404 风险)
  not_moved          映射表说要改的旧 URL 还返回 200(新旧两份)
  canonical_old      新页面 canonical 指向旧址或指向跳转 / 404 的地址
  hreflang_broken    hreflang 指向跳转 / 404,或缺回链(A 列了 B,B 没列 A)
  noindex_added      基线里能收录的页,改后带了 noindex
  schema_lost        基线里有的结构化数据类型改后没了
  title_lost         title 或 H1 改后为空
  link_to_redirect   站内链接还指向会跳转 / 404 的旧地址
  sitemap_stale      新 sitemap 里有会跳转 / 404 的地址
用法:
  python3 site_move.py baseline --site https://old.example [--allow-local] [--max 2000] [--gsc-pages pages.csv] --out seo-ops/baselines/2026-11-20.json
  python3 site_move.py compare --baseline seo-ops/baselines/2026-11-20.json --new-site https://new.example \
          [--old-origin https://old.example] [--map MIGRATION.md] [--allow-local] [--json|--md] [--out FILE]
退出码:0 没有 block 级问题;1 有 block 级问题;2 输入错。
"""
import argparse
import collections
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import site_crawl as sc  # noqa: E402
import launch_check as LK  # noqa: E402

SEVERITY = {"missing_redirect": "block", "bad_target": "block", "to_homepage": "block", "wrong_target": "block",
            "not_moved": "block", "canonical_old": "block", "noindex_added": "block", "hreflang_broken": "block",
            "redirect_chain": "warn", "temporary_redirect": "warn", "schema_lost": "warn", "title_lost": "warn",
            "link_to_redirect": "warn", "sitemap_stale": "warn"}
TYPE_ZH = {"missing_redirect": "漏 301", "redirect_chain": "链式跳转", "temporary_redirect": "临时跳转",
           "bad_target": "跳转终点不是 200", "wrong_target": "跳到映射表以外", "to_homepage": "跳到首页",
           "not_moved": "旧地址没跳转", "canonical_old": "canonical 指向旧址 / 跳转", "hreflang_broken": "hreflang 断簇",
           "noindex_added": "新加了 noindex", "schema_lost": "结构化数据丢了", "title_lost": "title / H1 丢了",
           "link_to_redirect": "站内链接指向跳转", "sitemap_stale": "sitemap 里有旧地址"}


class UsageError(Exception):
    pass


def path_of(u):
    p = urllib.parse.urlsplit(u).path or "/"
    return p


def origin_of(u):
    s = urllib.parse.urlsplit(u)
    return "%s://%s" % (s.scheme, s.netloc)


class Fetch:
    def __init__(self, polite):
        self.cache, self.errors, self.polite, self.n = {}, [], polite, 0

    def get(self, url):
        url = urllib.parse.urldefrag(url)[0]
        if url in self.cache:
            return self.cache[url]
        if self.polite and self.n:
            time.sleep(self.polite)
        self.n += 1
        try:
            r = sc.robust_fetch(url, timeout=15)
        except (sc.GuardError, sc.FetchError) as e:
            self.errors.append("抓取失败 %s: %s" % (url, e))
            r = None
        self.cache[url] = r
        return r


def page_record(r):
    p = LK.parse_page(r)
    return {"status": r.get("status"), "final_url": r.get("final_url"), "hops": len(r.get("chain") or []),
            "title": p["title"], "h1": p["h1"], "canonical": p["canonical"], "noindex": p["noindex"],
            "hreflang": p["hreflangs"], "ld_types": sorted(set(p["ld_types"])), "links": p["hrefs"]}


def sitemap_list(fetch, origin):
    rr = fetch.get(origin + "/robots.txt")
    robots = sc.parse_robots(rr.get("body") or "") if rr and rr.get("status") == 200 else None
    site = LK.Site(origin, fetch.errors)
    site.get = lambda u: fetch.get(u if u.startswith("http") else origin + u)  # 复用 Fetch 的缓存
    urls, _, _ = LK.sitemap_urls(site, robots)
    return urls


def internal(href, base, host):
    u = urllib.parse.urljoin(base, href)
    s = urllib.parse.urlsplit(u)
    if s.scheme not in ("http", "https") or s.netloc != host:
        return None
    return urllib.parse.urlunsplit((s.scheme, s.netloc, s.path or "/", s.query, ""))


def crawl(fetch, site, limit):
    origin = origin_of(site)
    host = urllib.parse.urlsplit(site).netloc
    seeds = [origin + "/"] + [urllib.parse.urlunsplit(urllib.parse.urlsplit(origin)[:2] + urllib.parse.urlsplit(u)[2:])
                              for u in sitemap_list(fetch, origin)]
    seen, queue, pages = set(), list(dict.fromkeys(seeds)), {}
    while queue and len(pages) < limit:
        u = queue.pop(0)
        if u in seen:
            continue
        seen.add(u)
        r = fetch.get(u)
        if not r:
            continue
        rec = page_record(r) if (r.get("status") == 200) else {"status": r.get("status"), "final_url": r.get("final_url"),
                                                                "hops": len(r.get("chain") or [])}
        pages[path_of(u)] = rec
        if r.get("status") == 200:
            for h in rec["links"]:
                v = internal(h, r.get("final_url") or u, host)
                if v and v not in seen:
                    queue.append(v)
    return pages


def load_gsc_pages(path):
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            k = {x.lower(): x for x in row}
            page = row.get(k.get("page") or k.get("top pages") or k.get("网页") or "", "")
            clicks = row.get(k.get("clicks") or k.get("点击次数") or "", "0")
            if page:
                try:
                    out[path_of(page)] = out.get(path_of(page), 0) + int(float(str(clicks).replace(",", "") or 0))
                except ValueError:
                    pass
    return out


def load_map(path):
    """CSV(old,new)或 Markdown 表(| /old/ | /new/ |)。只认以 / 或 http 开头的单元格。"""
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()
    rows = []
    if "|" in text:
        for line in text.splitlines():
            cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                rows.append(cells[:2])
    else:
        rows = [r[:2] for r in csv.reader(text.splitlines()) if len(r) >= 2]
    for a, b in rows:
        if re.match(r"^(/|https?://)", a) and re.match(r"^(/|https?://)", b):
            out[path_of(a) if a.startswith("http") else a] = path_of(b) if b.startswith("http") else b
    return out


def cmd_baseline(ns):
    fetch = Fetch(0 if ns.allow_local else 0.2)
    pages = crawl(fetch, ns.site, ns.max)
    if not pages:
        raise UsageError("一页都没抓到:%s" % "; ".join(fetch.errors[:3]))
    if ns.gsc_pages:
        clicks = load_gsc_pages(ns.gsc_pages)
        for p, rec in pages.items():
            rec["clicks28"] = clicks.get(p, 0)
    base = {"schema": 1, "site": ns.site.rstrip("/"), "taken_at": dt.datetime.now().isoformat(timespec="seconds"),
            "pages": pages, "sitemap": [path_of(u) for u in sitemap_list(fetch, origin_of(ns.site))],
            "errors": fetch.errors}
    out = ns.out or os.path.join("seo-ops", "baselines", dt.date.today().isoformat() + ".json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=1)
    ok = sum(1 for r in pages.values() if r.get("status") == 200)
    print("基线:%d 个 URL(%d 个 200),写到 %s" % (len(pages), ok, out))
    return 0


def compare(baseline, new_site, old_origin=None, mapping=None, polite=0.0):
    fetch = Fetch(polite)
    new_origin = origin_of(new_site)
    old_host = urllib.parse.urlsplit(baseline["site"]).netloc
    new_host = urllib.parse.urlsplit(new_site).netloc
    probe = (old_origin or new_origin).rstrip("/")
    mapping = mapping or {}
    issues = []
    seen_issue = set()

    def add(t, url, detail, clicks=0):
        key = (t, url)
        if key in seen_issue:
            return
        seen_issue.add(key)
        issues.append({"type": t, "label": TYPE_ZH[t], "severity": SEVERITY[t], "url": url, "detail": detail,
                       "clicks28": clicks})

    def resolve(u):
        """站内地址 → 在新站上的抓取结果(旧域名的地址也映到新站上查)。"""
        s = urllib.parse.urlsplit(u)
        if s.netloc in (old_host, new_host) or not s.netloc:
            u = new_origin + (s.path or "/") + (("?" + s.query) if s.query else "")
        return fetch.get(u)

    old_ok = {p: r for p, r in baseline["pages"].items() if r.get("status") == 200}
    retained, total_clicks = 0, 0
    new_pages = {}
    # 1. 旧 URL 在新站上怎么跳
    for p, old in sorted(old_ok.items()):
        clicks = old.get("clicks28") or 0
        r = fetch.get(probe + p)
        if not r:
            continue
        chain = r.get("chain") or []
        final = path_of(r.get("final_url") or "")
        st = r.get("status")
        want = mapping.get(p)
        moved = want is not None and want != p
        if not chain:
            if st in (404, 410):
                add("missing_redirect", p, "返回 %s%s" % (st, (",映射表要求跳到 %s" % want) if want else ""), clicks)
                continue
            if st == 200 and moved:
                add("not_moved", p, "还返回 200,映射表要求 301 到 %s" % want, clicks)
            if st != 200 and not moved:
                add("bad_target", p, "返回 %s" % st, clicks)
                continue
        else:
            if len(chain) > 1:
                add("redirect_chain", p, "跳了 %d 跳:%s" % (len(chain), " → ".join([p] + [path_of(c["location"]) for c in chain])), clicks)
            tmp = [c["status"] for c in chain if c["status"] in (302, 303, 307)]
            if tmp:
                add("temporary_redirect", p, "用了 %s" % ",".join(map(str, tmp)), clicks)
            if st != 200:
                hint = ""
                if want and final != want and final.lower() == want.lower():
                    hint = "(和映射表的 %s 只差大小写)" % want
                add("bad_target", p, "跳到 %s,终点返回 %s%s" % (final, st, hint), clicks)
                continue
            if final == "/" and p != "/" and want != "/":
                add("to_homepage", p, "深层地址跳到了首页 /%s" % ((",映射表是 %s" % want) if want else ""), clicks)
            elif want and final != want:
                add("wrong_target", p, "跳到 %s,映射表是 %s" % (final, want), clicks)
        if st == 200:
            rec = page_record(r)
            new_pages[final] = rec
            total_clicks += clicks
            if not old.get("noindex") and rec["noindex"]:
                add("noindex_added", final, "基线里能收录(旧址 %s),改后带了 noindex" % p, clicks)
            lost = sorted(set(old.get("ld_types") or []) - set(rec["ld_types"]))
            if lost:
                add("schema_lost", final, "丢了 %s(旧址 %s)" % ("、".join(lost), p), clicks)
            if (old.get("title") and not rec["title"]) or (old.get("h1") and not rec["h1"]):
                add("title_lost", final, "title 或 H1 为空(旧址 %s)" % p, clicks)
            if not [i for i in issues if i["url"] in (p, final) and i["severity"] == "block"]:
                retained += clicks
    # 2. 新 sitemap
    new_sm = sitemap_list(fetch, new_origin)
    cap = int(len(old_ok) * 1.2) + 50          # 新增页最多多抓这么多,和基线规模相当;旧地址一律查
    for u in new_sm:
        if path_of(u) not in old_ok and path_of(u) not in mapping and len(new_pages) >= cap:
            continue
        r = resolve(u)
        if not r:
            continue
        if r.get("chain") or r.get("status") != 200:
            add("sitemap_stale", path_of(u), "sitemap 列了它,但它%s" % (
                "跳到 %s" % path_of(r.get("final_url") or "") if r.get("chain") else "返回 %s" % r.get("status")))
        elif path_of(u) not in new_pages:
            new_pages[path_of(u)] = page_record(r)
    # 3. 新页面的 canonical、hreflang、站内链接
    link_bad = collections.defaultdict(set)
    for p, rec in sorted(new_pages.items()):
        base = new_origin + p
        c = rec.get("canonical")
        if c:
            cu = urllib.parse.urljoin(base, c)
            cs = urllib.parse.urlsplit(cu)
            if old_host != new_host and cs.netloc == old_host:
                add("canonical_old", p, "canonical 指向旧域名 %s" % cu)
            else:
                cr = resolve(cu)
                if cr and (cr.get("chain") or cr.get("status") != 200):
                    add("canonical_old", p, "canonical 指向 %s,它%s" % (path_of(cu), "会跳转" if cr.get("chain") else "返回 %s" % cr.get("status")))
        alts = rec.get("hreflang") or []
        for code, href in alts:
            hu = urllib.parse.urljoin(base, href)
            hr = resolve(hu)
            if not hr:
                continue
            if hr.get("chain") or hr.get("status") != 200:
                add("hreflang_broken", p, "hreflang %s 指向 %s,它%s" % (code, path_of(hu), "会跳转" if hr.get("chain") else "返回 %s" % hr.get("status")))
                continue
            ap = path_of(hr.get("final_url") or hu)
            if ap == p:
                continue
            arec = new_pages.get(ap) or page_record(hr)
            back = {path_of(urllib.parse.urljoin(new_origin + ap, h)) for _, h in arec.get("hreflang") or []}
            if p not in back:
                add("hreflang_broken", p, "hreflang %s → %s,但 %s 没有回链到 %s" % (code, ap, ap, p))
        for h in rec.get("links") or []:
            v = internal(h, base, new_host) or internal(h, base, old_host)
            # 只查基线里的旧地址和映射表里的地址:迁移问题只出在这些地址上,全站链接逐条请求太慢
            if not v or (path_of(v) not in old_ok and path_of(v) not in mapping):
                continue
            lr = resolve(v)
            if lr and (lr.get("chain") or (lr.get("status") or 0) >= 400):
                link_bad[path_of(v)].add(p)
    for target, srcs in sorted(link_bad.items()):
        add("link_to_redirect", target, "%d 个页面的站内链接指向它(%s),它会跳转或打不开;例:%s" % (
            len(srcs), "旧地址" if target in old_ok else "地址", "、".join(sorted(srcs)[:3])))
    by_type = collections.Counter(i["type"] for i in issues)
    return {"schema": 1, "baseline": baseline["site"], "baseline_taken_at": baseline.get("taken_at"),
            "new_site": new_site.rstrip("/"), "checked_at": dt.datetime.now().isoformat(timespec="seconds"),
            "old_urls": len(old_ok), "new_pages_checked": len(new_pages), "mapping_rows": len(mapping),
            "click_retention_est": round(retained / total_clicks, 3) if total_clicks else None,
            "summary": {"block": sum(1 for i in issues if i["severity"] == "block"),
                        "warn": sum(1 for i in issues if i["severity"] == "warn"), "by_type": dict(by_type)},
            "issues": issues, "errors": fetch.errors}


def render_md(rep):
    s = rep["summary"]
    L = ["# 改版对比:%s → %s" % (rep["baseline"], rep["new_site"]), "",
         "- 基线 %s,旧 URL %d 个;新站查了 %d 页;映射表 %d 行" % (rep["baseline_taken_at"], rep["old_urls"],
                                                          rep["new_pages_checked"], rep["mapping_rows"]),
         "- 问题:block %d、warn %d(%s)" % (s["block"], s["warn"], "、".join("%s %d" % (TYPE_ZH[k], v) for k, v in s["by_type"].items()) or "无")]
    if rep.get("click_retention_est") is not None:
        L.append("- 有点击的旧页里,没有 block 问题的点击占比:%.0f%% [est]" % (100 * rep["click_retention_est"]))
    L += ["", "| 级别 | 问题 | 地址 | 说明 |", "|---|---|---|---|"]
    for i in sorted(rep["issues"], key=lambda i: (i["severity"] != "block", -i["clicks28"], i["type"], i["url"])):
        L.append("| %s | %s | %s | %s |" % (i["severity"], i["label"], i["url"], i["detail"].replace("|", "/")))
    if rep["errors"]:
        L += ["", "抓取问题:"] + ["- " + e for e in rep["errors"][:10]]
    return "\n".join(L) + "\n"


def cmd_compare(ns):
    with open(ns.baseline, encoding="utf-8") as f:
        base = json.load(f)
    mapping = load_map(ns.map) if ns.map else None
    rep = compare(base, ns.new_site, ns.old_origin, mapping, 0 if ns.allow_local else 0.2)
    text = render_md(rep) if ns.md and not ns.json else json.dumps(rep, ensure_ascii=False, indent=1)
    if ns.out:
        with open(ns.out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)
    return 1 if rep["summary"]["block"] else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="改版 / 迁移保护:存基线、改后对比")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("baseline")
    b.add_argument("--site", required=True)
    b.add_argument("--max", type=int, default=2000)
    b.add_argument("--gsc-pages", help="GSC 网页导出 CSV(page, clicks)")
    b.add_argument("--out")
    b.add_argument("--allow-local", action="store_true", help=sc.LOCAL_HINT)
    c = sub.add_parser("compare")
    c.add_argument("--baseline", required=True)
    c.add_argument("--new-site", required=True)
    c.add_argument("--old-origin", help="旧 URL 去哪里请求(换域名时写旧域名;默认新站)")
    c.add_argument("--map", help="映射表:CSV 或含 | 旧 | 新 | 表格的 Markdown")
    c.add_argument("--allow-local", action="store_true", help=sc.LOCAL_HINT)
    c.add_argument("--json", action="store_true")
    c.add_argument("--md", action="store_true")
    c.add_argument("--out")
    ns = ap.parse_args(argv)
    sc.ALLOW_LOCAL = bool(getattr(ns, "allow_local", False))
    try:
        return {"baseline": cmd_baseline, "compare": cmd_compare}[ns.cmd](ns)
    except (UsageError, OSError, ValueError) as e:
        print("错误:%s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
