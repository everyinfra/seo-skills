#!/usr/bin/env python3
"""例 7 规模场景测试站(stdlib only):约 300 页的英文电商目录站,问题埋在分页深处。

为什么要它:hard_site 的两个站各 15 页左右,装不装 skill 都能一眼看完;联网时考新事实的题基线也能查到。
这个站的答案只在站里:要全站抓取、对 sitemap、跟重定向、比 title 才能找全。

同一个生成器,种子和主题不同 → 问题位置不同(h_scale 用 outdoor,h_scale_cn 用 kitchen)。
期望值只来自本文件的预埋清单 plan(seed, theme).plants / .decoys,判分不读 skill 的实现。

结构:首页 → 8 个分类(每类 30 个商品,每页 8 个,只有「上一页 / 下一页」)→ 商品页(互链前后两个邻居);
指南列表每页 5 篇、共 6 页。第 3 页以后的商品和指南点击深度 ≥4。

预埋问题(12 个,类别和数目在开跑前写定,见 scenarios_hard.json 的 criteria):
  O1-O3  sitemap 里的孤儿页(无任何站内入链)            3
  S1-S2  sitemap 里的 URL 实际 301                      2
  R1     ≥3 跳的重定向链,被深层商品页的站内链接引用     1
  C1     canonical 指向 noindex 页                      1
  D1-D2  两对深层页 title 和 description 完全重复        2(按对计,报出任意一页即算)
  F1     软 404(200,正文是 Page not found)             1
  B1     深层页里链到 404 的站内链接                     1
  X1     在 sitemap 里但响应头 X-Robots-Tag: noindex     1
诱饵(4 个,都是正确用法):站内搜索页 noindex 且不在 sitemap;分页页 canonical 自指;
打印版 canonical 指回原文;不在 sitemap 的 /cart/ 302 到登录页。

用法:
  python3 scale_site.py build --out DIR --seed N --theme outdoor|kitchen [--base http://127.0.0.1:8801]
  python3 scale_site.py plants --seed N --theme T             # 打印预埋清单
  python3 scale_site.py selfcheck --seed N --theme T          # 起站、用独立的小爬虫核对站点里恰好是这些问题
服务器复用 hard_site.Handler(认 _status / _redirects / _headers)。
"""
import argparse
import html as _html
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hard_site as HS  # noqa: E402

PER_PAGE, PER_CAT, GUIDES, GUIDES_PER_PAGE = 8, 30, 30, 5

# ---------------------------------------------------------------- 词表
SERIES = ["Ridgeline", "Cascade", "Summit", "Alder", "Basalt", "Cirque", "Talus", "Moraine", "Ptarmigan", "Larch",
          "Juniper", "Granite", "Kestrel", "Tamarack", "Sierra", "Bramble", "Fjord", "Highline", "Switchback", "Tarn",
          "Aspen", "Bluff", "Cobalt", "Driftwood", "Ember", "Flint", "Glacier", "Harbor", "Ironwood", "Keystone",
          "Lumen", "Meridian", "Nimbus", "Oxbow", "Pinyon", "Quarry", "Rowan", "Saddle", "Thistle", "Umber",
          "Vista", "Willow", "Yarrow", "Zephyr", "Beacon", "Cinder", "Dune", "Estuary", "Fern", "Gully"]
SUFFIX = ["", "Lite", "Pro", "2", "3", "Plus", "Classic", "Trail", "XL", "Mini", "Edge", "Core"]

THEMES = {
    "outdoor": {
        "brand": "Ridgeway Outfitters", "domain_word": "outdoor gear",
        "cats": [
            ("jackets", "Jacket", "Jackets", ["3-layer nylon", "recycled polyester", "waxed cotton", "softshell", "down-filled ripstop"],
             ["pit zips for venting on steep climbs", "a helmet-compatible hood", "taped seams", "a two-way front zip",
              "hand pockets placed above a hip belt", "a hem drawcord you can reach with gloves on", "a packable chest pocket"]),
            ("base-layers", "Base Layer", "Base Layers", ["merino wool", "merino-nylon blend", "polyester grid fleece", "silk-weight synthetic"],
             ["flatlock seams that do not rub under a pack", "a longer back hem", "thumb loops", "odour control that lasts several days",
              "a quarter zip for venting", "raglan sleeves"]),
            ("hiking-boots", "Hiking Boot", "Hiking Boots", ["full-grain leather", "suede and mesh", "synthetic nubuck"],
             ["a waterproof membrane", "a lugged rubber outsole", "a rockplate under the forefoot", "a gusseted tongue",
              "locking eyelets at the ankle", "a heel brake for descents", "a wide toe box"]),
            ("backpacks", "Backpack", "Backpacks", ["robic nylon", "ultra-high-molecular polyethylene fabric", "waxed canvas", "coated polyester"],
             ["an adjustable torso length", "hip-belt pockets", "a hydration sleeve", "a lid that converts to a summit pack",
              "side compression straps", "a stretch front pocket", "a frame sheet you can remove"]),
            ("tents", "Tent", "Tents", ["silnylon", "polyester fly with nylon mesh", "Dyneema composite fabric"],
             ["two doors and two vestibules", "colour-coded poles", "a fly that pitches first in rain", "ceiling vents",
              "guy-out points on every panel", "a footprint sold separately"]),
            ("sleeping-bags", "Sleeping Bag", "Sleeping Bags", ["800-fill goose down", "650-fill duck down", "synthetic insulation"],
             ["a draft collar", "a contoured hood", "a full-length zip that does not snag", "a stash pocket for a phone",
              "a trapezoid foot box", "a compression sack"]),
            ("trekking-poles", "Trekking Pole", "Trekking Poles", ["carbon fibre", "aluminium 7075", "carbon and aluminium"],
             ["flick locks that hold under load", "cork grips", "extended foam below the grip", "carbide tips",
              "a folding Z design", "interchangeable baskets"]),
            ("headlamps", "Headlamp", "Headlamps", ["aluminium housing", "polycarbonate housing", "magnesium housing"],
             ["a red night-vision mode", "a lockout so it does not switch on in your pack", "USB-C charging",
              "a reactive beam that dims near objects", "a battery gauge", "an IPX7 rating"]),
        ],
        "guide_topics": ["layering for shoulder-season hikes", "fitting a pack to your torso", "breaking in leather boots",
                         "choosing a tent for wind", "storing down sleeping bags", "setting trekking pole length",
                         "picking a headlamp beam", "washing merino base layers", "re-proofing a rain jacket",
                         "packing for a three-day trek", "camp kitchens that weigh under a kilo", "hiking in early snow",
                         "planning water on dry trails", "caring for waterproof membranes", "resoling hiking boots",
                         "drying gear in a wet camp", "choosing a sleeping pad R-value", "navigation without a phone",
                         "leave-no-trace basics", "first-aid kit checklist", "hiking with a dog", "photographing at dawn",
                         "pitching a tent on rock", "cold-weather battery care", "fixing a broken zip on the trail",
                         "reading a weather forecast for ridges", "keeping feet dry on long days", "sizing a down jacket",
                         "hut-to-hut trekking", "packing a bear canister", "choosing gaiters", "trail running versus hiking shoes"],
    },
    "kitchen": {
        "brand": "Copperleaf Kitchen", "domain_word": "cookware",
        "cats": [
            ("skillets", "Skillet", "Skillets", ["pre-seasoned cast iron", "carbon steel", "tri-ply stainless steel", "hard-anodised aluminium"],
             ["a helper handle", "pour spouts on both sides", "a flat base for induction", "a riveted stay-cool handle",
              "flared sides for tossing", "an oven-safe rating to 260 °C"]),
            ("saucepans", "Saucepan", "Saucepans", ["tri-ply stainless steel", "copper with tin lining", "enamelled steel"],
             ["measurement marks inside", "a tight glass lid", "a rolled rim for drip-free pouring", "an encapsulated base",
              "a long balanced handle", "a lid that fits the matching skillet"]),
            ("chef-knives", "Chef Knife", "Chef Knives", ["VG-10 steel", "German X50CrMoV15 steel", "carbon steel", "powder steel"],
             ["a full tang", "a hand-sharpened 15-degree edge", "a pakkawood handle", "a bolster that leaves the heel free",
              "a granton edge", "a blade guard in the box"]),
            ("cutting-boards", "Cutting Board", "Cutting Boards", ["end-grain walnut", "edge-grain maple", "teak", "composite fibre"],
             ["a juice groove", "rubber feet", "handholds cut into the ends", "a reversible flat side",
              "a food-safe oil finish", "a weight that stops it sliding"]),
            ("dutch-ovens", "Dutch Oven", "Dutch Ovens", ["enamelled cast iron", "bare cast iron", "ceramic"],
             ["self-basting lid spikes", "wide loop handles", "a light interior enamel", "a stainless knob safe to 260 °C",
              "a heavy base for even browning"]),
            ("baking-sheets", "Baking Sheet", "Baking Sheets", ["aluminised steel", "commercial aluminium", "stainless steel"],
             ["rolled edges that resist warping", "a ridged texture for airflow", "a matching cooling rack",
              "half-sheet sizing", "no non-stick coating to wear off"]),
            ("mixing-bowls", "Mixing Bowl", "Mixing Bowls", ["stainless steel", "tempered glass", "stoneware", "melamine"],
             ["a non-slip base", "a pouring lip", "measurement marks", "nesting sizes", "snap-on lids"]),
            ("kettles", "Kettle", "Kettles", ["brushed stainless steel", "borosilicate glass", "enamelled steel"],
             ["a gooseneck spout for pour-over", "variable temperature settings", "a keep-warm mode", "a 360-degree base",
              "a removable limescale filter", "an auto shut-off"]),
        ],
        "guide_topics": ["seasoning cast iron", "searing without sticking", "sharpening a chef knife", "oiling a wooden board",
                         "braising in a dutch oven", "baking sheets that do not warp", "choosing a first knife set",
                         "induction-ready cookware", "cleaning burnt stainless steel", "storing knives safely",
                         "pour-over water temperatures", "caring for copper pans", "stock pots versus dutch ovens",
                         "proofing bread in a bowl", "making pan sauces", "restoring a rusty skillet",
                         "cookware for small kitchens", "carbon steel patina", "batch cooking on sheet pans",
                         "holding a knife correctly", "when to replace non-stick", "descaling a kettle",
                         "choosing mixing bowls for baking", "cooking acidic food in iron", "oven temperatures explained",
                         "honing versus sharpening", "slow cooking on the stove", "stacking pans without scratches",
                         "cleaning a wooden board after raw meat", "deglazing basics", "fermenting in stoneware",
                         "picking a saucepan size"],
    },
}
FIRST = ["Maya", "Tom", "Priya", "Lucas", "Hana", "Owen", "Sofia", "Ravi", "Elena", "Jonas", "Aiko", "Marco", "Grace",
         "Diego", "Nora", "Felix", "Leila", "Sam", "Ines", "Kai"]
CITY = ["Leeds", "Denver", "Cork", "Otago", "Calgary", "Bergen", "Hobart", "Asheville", "Bend", "Kendal", "Inverness",
        "Boulder", "Wanaka", "Chamonix", "Banff", "Tromsø"]


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def esc(s):
    return _html.escape(s, quote=True)


# ---------------------------------------------------------------- 规划
class Site:
    """一个站的全部事实:页面、重定向、响应头、sitemap、预埋问题和诱饵。base 无关,写文件时再拼。"""

    def __init__(self, seed, theme):
        self.seed, self.theme = seed, theme
        self.T = THEMES[theme]
        self.rng = random.Random("%s:%s" % (seed, theme))
        self.pages = {}          # path -> dict(kind, title, desc, ...)
        self.redirects = {}      # path -> [code, target]
        self.headers = {}        # path -> {name: value}
        self.sitemap = []
        self.plants = []         # (pid, [paths], kw_regex, desc)
        self.decoys = []         # (did, [paths], desc)
        self._plan()

    # ---- 商品
    def _products(self):
        rng = self.rng
        used = set()
        cats = []
        for slug, noun, plural, materials, features in self.T["cats"]:
            items = []
            while len(items) < PER_CAT:
                name = ("%s %s %s" % (rng.choice(SERIES), noun, rng.choice(SUFFIX))).strip()
                if name in used:
                    continue
                used.add(name)
                mat = rng.choice(materials)
                feats = rng.sample(features, min(4, len(features)))
                items.append({"name": name, "slug": slugify(name), "material": mat, "features": feats,
                              "price": rng.choice([29, 39, 49, 59, 79, 89, 119, 149, 179, 229, 289, 349]) + rng.choice([0, 0.5]),
                              "sku": "%s-%04d" % (slug[:3].upper(), rng.randrange(1000, 9999)),
                              "weight": rng.randrange(80, 2400), "cat": slug, "noun": noun})
            cats.append({"slug": slug, "noun": noun, "plural": plural, "items": items})
        return cats

    def _plan(self):
        rng = self.rng
        T = self.T
        cats = self._products()
        self.cats = cats
        # 每类第 17 个以后(第 3、4 页)是深层位置;从这里抽预埋位置,互不重叠
        deep = [(ci, k) for ci in range(len(cats)) for k in range(17, PER_CAT - 1)]
        rng.shuffle(deep)
        picks = iter(deep)

        def take(n=1, same_cat=False):
            out = []
            for ci, k in picks:
                if same_cat and out and ci != out[0][0]:
                    continue
                if any(ci == c and abs(k - kk) <= 1 for c, kk in taken):
                    continue                       # 邻居互链,预埋位置不挨着,免得一页带两类问题
                out.append((ci, k))
                taken.append((ci, k))
                if len(out) == n:
                    return out
            raise RuntimeError("深层位置不够")
        taken = []

        def item(pos):
            return cats[pos[0]]["items"][pos[1]]

        orphans = [item(p) for p in take(3)]
        moved = [item(p) for p in take(2)]                 # sitemap 里还是旧网址,旧网址 301 到现网址
        chain_from = item(take()[0])                       # 正文链到一个三跳重定向链
        canon_a = item(take()[0])                          # canonical 指向一个 noindex 页
        dup1 = [item(p) for p in take(2, same_cat=True)]
        dup2 = [item(p) for p in take(2, same_cat=True)]
        soft = item(take()[0])                             # 已下架,回 200 + Page not found
        broken_from = item(take()[0])                      # 正文链到不存在的商品

        for o in orphans:
            o["orphan"] = True
        for m in moved:
            m["old_slug"] = slugify("%s %s" % (m["name"], rng.choice(["2024", "old", "v1", "legacy"])))
        soft["soft404"] = True
        broken_ghost = "/p/%s/" % slugify("%s %s %s" % (rng.choice(SERIES), broken_from["noun"], "Original"))
        broken_from["extra_link"] = (broken_ghost, "the original %s this one replaced" % broken_from["noun"].lower())
        dup1[1]["dup_of"] = dup1[0]
        dup2[1]["dup_of"] = dup2[0]
        # canonical 目标:同款「套装页」,上架前 noindex 一直没撤;只从 A 链过去,不在 sitemap
        bundle = "/p/%s-bundle/" % canon_a["slug"]
        canon_a["canonical"] = bundle
        canon_a["extra_link"] = (bundle, "the %s bundle with a carry case" % canon_a["name"])

        # ---- 指南
        topics = rng.sample(T["guide_topics"], GUIDES)
        guides = []
        for t in topics:
            title = t[0].upper() + t[1:]
            guides.append({"topic": t, "title": title, "slug": slugify(t)})
        self.guides = guides
        deep_guides = list(range(2 * GUIDES_PER_PAGE, GUIDES))          # 第 3 页起,深度 ≥4
        rng.shuffle(deep_guides)
        g_noindex = guides[deep_guides[0]]
        g_chain = guides[deep_guides[1]]
        printable = [guides[i] for i in rng.sample([i for i in range(GUIDES) if guides[i] not in (g_noindex, g_chain)], 6)]
        for g in printable:
            g["print"] = True
        hop_tail = rng.choice(["2023", "old", "archive"])
        chain = ["/guides/%s-%s/" % (g_chain["slug"], hop_tail), "/guides/%s/" % g_chain["slug"].replace("-", "_"),
                 "/blog/%s/" % g_chain["slug"], "/guides/%s/" % g_chain["slug"]]
        for a, b in zip(chain, chain[1:]):
            self.redirects[a] = [301, b]
        chain_from["extra_link"] = (chain[0], g_chain["title"].lower())

        # ---- 页面
        self._page("/", "home")
        for c in cats:
            listed = [p for p in c["items"] if not p.get("orphan")]
            c["listed"] = listed
            pages = [listed[i:i + PER_PAGE] for i in range(0, len(listed), PER_PAGE)]
            c["npages"] = len(pages)
            for n, chunk in enumerate(pages, 1):
                path = "/c/%s/" % c["slug"] if n == 1 else "/c/%s/page/%d/" % (c["slug"], n)
                self._page(path, "listing", cat=c, n=n, chunk=chunk)
            for i, p in enumerate(listed):
                p["prev"] = listed[i - 1] if i else None
                p["next"] = listed[i + 1] if i + 1 < len(listed) else None
            for p in c["items"]:
                self._page("/p/%s/" % p["slug"], "product", p=p, cat=c)
        self._page(bundle, "bundle", p=canon_a)
        gpages = [guides[i:i + GUIDES_PER_PAGE] for i in range(0, GUIDES, GUIDES_PER_PAGE)]
        self.guide_npages = len(gpages)
        for n, chunk in enumerate(gpages, 1):
            self._page("/guides/" if n == 1 else "/guides/page/%d/" % n, "guide_list", n=n, chunk=chunk)
        for i, g in enumerate(guides):
            g["rel"] = [cats[(i + j) % len(cats)]["listed"][rng.randrange(0, PER_PAGE)] for j in (0, 3)]
            self._page("/guides/%s/" % g["slug"], "guide", g=g)
            if g.get("print"):
                self._page("/print/guides/%s/" % g["slug"], "print", g=g)
        for path, kind in (("/about/", "about"), ("/contact/", "contact"), ("/shipping/", "shipping"),
                           ("/returns/", "returns"), ("/search/", "search"), ("/login/", "login")):
            self._page(path, kind)
        self.redirects["/cart/"] = [302, "/login/?next=/cart/"]
        self.headers["/guides/%s/" % g_noindex["slug"]] = {"X-Robots-Tag": "noindex"}
        for m in moved:
            self.redirects["/p/%s/" % m["old_slug"]] = [301, "/p/%s/" % m["slug"]]

        # ---- sitemap:首页、分类和分页、商品(改名的两个写旧网址)、指南和分页、静态页
        sm = ["/"]
        for c in cats:
            sm += ["/c/%s/" % c["slug"]] + ["/c/%s/page/%d/" % (c["slug"], n) for n in range(2, c["npages"] + 1)]
            sm += ["/p/%s/" % (p.get("old_slug") or p["slug"]) for p in c["items"]]
        sm += ["/guides/"] + ["/guides/page/%d/" % n for n in range(2, self.guide_npages + 1)]
        sm += ["/guides/%s/" % g["slug"] for g in guides]
        sm += ["/about/", "/contact/", "/shipping/", "/returns/"]
        self.sitemap = sm

        P = lambda x: "/p/%s/" % x["slug"]  # noqa: E731
        orphan_kw = (r"orphan|孤儿|孤立|孤页|入链|inlink|in-link|inbound|incoming|internal link|not linked|unlinked|no links|"
                     r"没有.{0,8}链接|无.{0,6}链接|不可达|unreachable|not reachable|链不到|只在.{0,6}sitemap|仅.{0,6}sitemap|"
                     r"only (?:in|via|from|listed in) (?:the )?sitemap")
        redir_kw = r"301|redirect|重定向|跳转"
        self.plants = [
            ("O1", [P(orphans[0])], orphan_kw, "sitemap 里的孤儿页 %s" % P(orphans[0])),
            ("O2", [P(orphans[1])], orphan_kw, "sitemap 里的孤儿页 %s" % P(orphans[1])),
            ("O3", [P(orphans[2])], orphan_kw, "sitemap 里的孤儿页 %s" % P(orphans[2])),
            ("S1", ["/p/%s/" % moved[0]["old_slug"], P(moved[0])], redir_kw, "sitemap 列 /p/%s/,301 到 %s" % (moved[0]["old_slug"], P(moved[0]))),
            ("S2", ["/p/%s/" % moved[1]["old_slug"], P(moved[1])], redir_kw, "sitemap 列 /p/%s/,301 到 %s" % (moved[1]["old_slug"], P(moved[1]))),
            ("R1", [P(chain_from)] + chain, r"chain|链|hop|跳|redirect|重定向|301",
             "%s 正文链到 %s,三跳 301 才到 %s" % (P(chain_from), chain[0], chain[-1])),
            ("C1", [P(canon_a), bundle], r"canonical|规范", "%s 的 canonical 指向 noindex 的 %s" % (P(canon_a), bundle)),
            ("D1", [P(dup1[0]), P(dup1[1])], r"duplicate|dup|重复|相同|一样|identical|same title|同样|雷同",
             "%s 与 %s title、description 完全相同" % (P(dup1[0]), P(dup1[1]))),
            ("D2", [P(dup2[0]), P(dup2[1])], r"duplicate|dup|重复|相同|一样|identical|same title|同样|雷同",
             "%s 与 %s title、description 完全相同" % (P(dup2[0]), P(dup2[1]))),
            ("F1", [P(soft)], r"soft|软|404|not found|不存在|找不到|下架|discontinued|no longer",
             "%s 回 200,正文是 Page not found(软 404)" % P(soft)),
            ("B1", [P(broken_from), broken_ghost], r"404|broken|dead|死链|坏链|失效|断链|不存在|not found",
             "%s 正文链到 404 的 %s" % (P(broken_from), broken_ghost)),
            ("X1", ["/guides/%s/" % g_noindex["slug"]], r"noindex|x-robots",
             "/guides/%s/ 在 sitemap 里,响应头 X-Robots-Tag: noindex" % g_noindex["slug"]),
        ]
        self.decoys = [
            ("Q1", ["/search/"], "站内搜索页:meta noindex,不在 sitemap(正确)"),
            ("Q2", [p for p in self.pages if "/page/" in p], "分页页 canonical 自指(正确)"),
            ("Q3", ["/print/guides/%s/" % g["slug"] for g in printable], "打印版 canonical 指回原文、不在 sitemap(正确)"),
            ("Q4", ["/cart/", "/login/"], "/cart/ 不在 sitemap,302 到 /login/?next=/cart/,登录页 noindex(正确)"),
        ]

    def _page(self, path, kind, **kw):
        assert path not in self.pages, path
        kw["kind"] = kind
        self.pages[path] = kw

    # ---------------------------------------------------------------- 渲染
    def render(self, base, path):
        d = self.pages[path]
        kind = d["kind"]
        T = self.T
        brand = T["brand"]
        r = random.Random("%s:%s:%s" % (self.seed, self.theme, path))      # 每页自己的随机源,页面之间文字不同
        robots = ""
        canon = path
        crumbs = []
        if kind == "home":
            title = "%s — %s tested on real trips and kept for years" % (brand, T["domain_word"])
            desc = "%s sells %s across %d categories, with field notes and care guides written by our staff." % (
                brand, T["domain_word"], len(self.cats))
            body = "<h1>%s</h1><p>%s</p><h2>Shop by category</h2><ul>%s</ul><h2>From the guides</h2><ul>%s</ul>" % (
                esc(brand), esc(self._para(r, "home")),
                "".join('<li><a href="/c/%s/">%s</a></li>' % (c["slug"], esc(c["plural"])) for c in self.cats),
                "".join('<li><a href="/guides/%s/">%s</a></li>' % (g["slug"], esc(g["title"])) for g in self.guides[:3]))
        elif kind == "listing":
            c, n = d["cat"], d["n"]
            title = "%s — %s" % (c["plural"], brand) if n == 1 else "%s — page %d of %d — %s" % (c["plural"], n, c["npages"], brand)
            desc = "Browse %d %s from %s%s: materials, weights and prices side by side." % (
                len(c["listed"]), c["plural"].lower(), brand, "" if n == 1 else ", page %d" % n)
            cards = "".join('<li><a href="/p/%s/">%s</a> — %s, $%.2f</li>' % (p["slug"], esc(p["name"]), esc(p["material"]), p["price"])
                            for p in d["chunk"])
            nav = []
            if n > 1:
                nav.append('<a rel="prev" href="%s">Previous</a>' % ("/c/%s/" % c["slug"] if n == 2 else "/c/%s/page/%d/" % (c["slug"], n - 1)))
            if n < c["npages"]:
                nav.append('<a rel="next" href="/c/%s/page/%d/">Next</a>' % (c["slug"], n + 1))
            intro = self._para(r, "listing", noun=c["noun"].lower(), plural=c["plural"].lower()) if n == 1 else ""
            body = "<h1>%s%s</h1><p>%s</p><ul class=\"grid\">%s</ul><nav class=\"pager\">%s</nav>" % (
                esc(c["plural"]), "" if n == 1 else " — page %d" % n, esc(intro), cards, " ".join(nav))
            crumbs = [("/", "Home")] + ([] if n == 1 else [("/c/%s/" % c["slug"], c["plural"])])
        elif kind == "product":
            p, c = d["p"], d["cat"]
            src = p.get("dup_of") or p
            title = "%s — %s | %s" % (src["name"], src["material"], brand)
            desc = "%s in %s with %s. $%.2f, free returns within 60 days." % (src["name"], src["material"], src["features"][0], src["price"])
            if p.get("soft404"):
                title = "Page not found | %s" % brand
                desc = "The page you are looking for could not be found."
                body = ("<h1>Page not found</h1><p>Sorry, we couldn't find the page you were looking for. It may have been "
                        "moved or is no longer available.</p><p><a href=\"/c/%s/\">Browse %s</a> or <a href=\"/search/\">search the shop</a>.</p>"
                        % (c["slug"], esc(c["plural"].lower())))
            else:
                if p.get("canonical"):
                    canon = p["canonical"]
                feats = "".join("<li>%s</li>" % esc(f[0].upper() + f[1:]) for f in p["features"])
                rel = [x for x in (p.get("prev"), p.get("next")) if x]
                rel_html = "".join('<li><a href="/p/%s/">%s</a></li>' % (x["slug"], esc(x["name"])) for x in rel)
                extra = ""
                if p.get("extra_link"):
                    href, text = p["extra_link"]
                    extra = "<p>%s <a href=\"%s\">%s</a>.</p>" % (esc(r.choice(["Before you buy, read", "Also worth a look:", "See"])), href, esc(text))
                body = ("<h1>%s</h1><p class=\"price\">$%.2f</p><p>%s</p><h2>Features</h2><ul>%s</ul>"
                        "<h2>Specifications</h2><table><tr><th>Material</th><td>%s</td></tr><tr><th>Weight</th><td>%d g</td></tr>"
                        "<tr><th>SKU</th><td>%s</td></tr></table><h2>Care</h2><p>%s</p>%s<h2>Reviews</h2>%s"
                        "<h2>Related</h2><ul>%s</ul>") % (
                    esc(p["name"]), p["price"], esc(self._para(r, "product", noun=p["noun"].lower(), name=p["name"], mat=p["material"],
                                                               feat=p["features"][1])),
                    feats, esc(p["material"]), p["weight"], p["sku"], esc(self._para(r, "care", mat=p["material"], noun=p["noun"].lower())),
                    extra, self._reviews(r, p), rel_html)
            crumbs = [("/", "Home"), ("/c/%s/" % c["slug"], c["plural"])]
        elif kind == "bundle":
            p = d["p"]
            title = "%s bundle with carry case | %s" % (p["name"], brand)
            desc = "The %s together with a padded carry case and spare parts kit." % p["name"]
            robots = '<meta name="robots" content="noindex">'
            body = "<h1>%s bundle</h1><p>%s</p><p><a href=\"/p/%s/\">Back to the %s</a></p>" % (
                esc(p["name"]), esc(self._para(r, "product", noun=p["noun"].lower(), name=p["name"], mat=p["material"],
                                                 feat=p["features"][0])), p["slug"], esc(p["name"]))
        elif kind == "guide_list":
            n = d["n"]
            title = "Guides and field notes — %s" % brand if n == 1 else "Guides and field notes — page %d — %s" % (n, brand)
            desc = "How-to guides from the %s team%s." % (brand, "" if n == 1 else ", page %d of %d" % (n, self.guide_npages))
            items = "".join('<li><a href="/guides/%s/">%s</a></li>' % (g["slug"], esc(g["title"])) for g in d["chunk"])
            nav = []
            if n > 1:
                nav.append('<a rel="prev" href="%s">Previous</a>' % ("/guides/" if n == 2 else "/guides/page/%d/" % (n - 1)))
            if n < self.guide_npages:
                nav.append('<a rel="next" href="/guides/page/%d/">Next</a>' % (n + 1))
            body = "<h1>Guides%s</h1><ul>%s</ul><nav class=\"pager\">%s</nav>" % ("" if n == 1 else " — page %d" % n, items, " ".join(nav))
            crumbs = [("/", "Home")]
        elif kind in ("guide", "print"):
            g = d["g"]
            title = "%s — a %s guide" % (g["title"], brand)
            desc = "%s: what we learned from years of %s, step by step." % (g["title"], r.choice(["field testing", "workshop repairs", "customer questions", "staff trips"]))
            if kind == "print":
                title = "%s (print version)" % g["title"]
                canon = "/guides/%s/" % g["slug"]
            sents = [x.format(topic=g["topic"], city=r.choice(CITY), n=r.randrange(2, 9), name=r.choice(FIRST))
                     for x in r.sample(self.SENT["guide"], 10)]
            paras = "".join("<p>%s</p>" % esc(" ".join(sents[i:i + 3])) for i in range(0, 9, 3))
            steps = "".join("<li>%s</li>" % esc(x) for x in r.sample(self.SENT["step"], r.randrange(4, 7)))
            rel = "".join('<li><a href="/p/%s/">%s</a></li>' % (p["slug"], esc(p["name"])) for p in g["rel"])
            pr = '<p><a href="/print/guides/%s/">Print version</a></p>' % g["slug"] if kind == "guide" and g.get("print") else ""
            body = "<h1>%s</h1>%s<h2>Step by step</h2><ol>%s</ol><h2>Gear mentioned</h2><ul>%s</ul>%s" % (
                esc(g["title"]), paras, steps, rel, pr)
            crumbs = [("/", "Home"), ("/guides/", "Guides")]
        else:
            title, desc, body = self._static(kind, r, brand)
            if kind in ("search", "login"):
                robots = '<meta name="robots" content="noindex, follow">'
        head_nav = "".join('<a href="/c/%s/">%s</a> ' % (c["slug"], esc(c["plural"])) for c in self.cats)
        head_nav += '<a href="/guides/">Guides</a> <a href="/search/">Search</a> <a href="/cart/">Cart</a>'
        foot = ('<a href="/about/">About</a> <a href="/contact/">Contact</a> <a href="/shipping/">Shipping</a> '
                '<a href="/returns/">Returns</a>')
        bc = ""
        if crumbs:
            bc = '<nav class="crumbs">%s</nav>' % " › ".join('<a href="%s">%s</a>' % (h, esc(t)) for h, t in crumbs)
        return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>%s</title>'
                '<meta name="description" content="%s">%s<meta name="viewport" content="width=device-width, initial-scale=1">'
                '<link rel="canonical" href="%s%s"></head><body><header><a href="/">%s</a><nav>%s</nav></header>%s'
                "<main>%s</main><footer>%s <span>© 2026 %s</span></footer></body></html>"
                % (esc(title), esc(desc), robots, base, canon, esc(brand), head_nav, bc, body, foot, esc(brand)))

    def _static(self, kind, r, brand):
        if kind == "search":
            return ("Search — %s" % brand, "Search %s products and guides." % brand,
                    '<h1>Search</h1><form action="/search/"><input name="q" placeholder="Search"><button>Go</button></form>')
        if kind == "login":
            return ("Sign in — %s" % brand, "Sign in to see your orders and saved carts.",
                    '<h1>Sign in</h1><form method="post" action="/login/"><input name="email"><input name="password" type="password"><button>Sign in</button></form>')
        text = {
            "about": ("About %s" % brand, "Who runs %s, where we test gear and how we pick what to sell." % brand),
            "contact": ("Contact %s" % brand, "Email, phone and workshop hours for %s customer support." % brand),
            "shipping": ("Shipping rates and times — %s" % brand, "Delivery options, rates and cut-off times for %s orders." % brand),
            "returns": ("Returns and repairs — %s" % brand, "Our 60-day returns policy and how %s handles repairs." % brand),
        }[kind]
        body = "<h1>%s</h1>%s" % (esc(text[0]), "".join("<p>%s</p>" % esc(self._para(r, kind)) for _ in range(3)))
        return text[0], text[1], body

    def _reviews(self, r, p):
        out = []
        for _ in range(r.randrange(1, 4)):
            out.append("<blockquote>%s <cite>— %s, %s</cite></blockquote>" % (
                esc(self._para(r, "review", noun=p["noun"].lower(), feat=r.choice(p["features"]))), r.choice(FIRST), r.choice(CITY)))
        return "".join(out)

    SENT = {
        "home": ["We started as a repair bench and still fix most of what we sell.",
                 "Every item here has been used by someone on staff for at least a season.",
                 "Prices include free returns for sixty days and repairs at cost after that.",
                 "Our guides cover the questions customers ask us most often at the counter."],
        "listing": ["Every {noun} on this page has been used by our staff before it went on sale.",
                    "Filter by weight if you carry your kit far, or by material if you care about repairs.",
                    "Most {plural} here ship within two working days.",
                    "If you are unsure which {noun} fits, our returns policy gives you sixty days to decide."],
        "product": ["The {name} is built from {mat} and comes with {feat}.",
                    "We picked the {name} because it held up after a full season of daily use.",
                    "Compared with other {noun}s at this price, it gives up a little weight for a lot more durability.",
                    "Customers who return it usually wanted something lighter, not something stronger.",
                    "It is the {noun} our repair bench sees least often.",
                    "Expect {feat}, and a fit that suits most people without adjustment.",
                    "The {mat} ages well and can be repaired rather than replaced."],
        "care": ["Clean {mat} gently and let it dry away from direct heat.",
                 "Store the {noun} somewhere dry and out of direct sun.",
                 "Check seams and fixings once a season; small repairs are free in our workshop.",
                 "Avoid harsh detergents, which shorten the life of {mat}.",
                 "If something fails in normal use within two years, send it back and we will fix it."],
        "review": ["Used it for three months and {feat} is the part I notice most.",
                   "Better than my last {noun}; the fit was right out of the box.",
                   "A little heavier than I expected, but it has not let me down.",
                   "Bought it as a gift and ended up getting a second one for myself.",
                   "Took a week to get used to, now I would not swap it.",
                   "Solid {noun}; having {feat} is what sold it for me."],
        "guide": ["Most problems with {topic} come from rushing the first step.",
                  "Our staff have different habits for {topic}, but they agree on the basics below.",
                  "If you only remember one thing about {topic}, make it the check at the end.",
                  "You do not need special tools for {topic}; what you already own is usually enough.",
                  "We wrote this after the same question about {topic} came up at the counter every week.",
                  "Weather, time and budget all change the right approach to {topic}.",
                  "Plan ten extra minutes for {topic} the first time you try it.",
                  "When {topic} goes wrong, it is rarely the gear and usually the order of steps.",
                  "{name} from our {city} shop has done this for years and still starts with a checklist.",
                  "A customer in {city} asked us about {topic} after a bad first attempt, and this guide grew from that reply.",
                  "We tested {n} different approaches to {topic} over one season and kept the two that worked.",
                  "The cheapest fix is usually the right one; spend money only after you have tried the basics.",
                  "Read the manufacturer's notes first, then use this guide to fill the gaps they leave.",
                  "Do it at home before you need it outdoors or in a hurry.",
                  "Bring the item into the shop if you want a second opinion; we look at it for free.",
                  "Most people get {topic} right on the second try, so do not judge the method by your first attempt.",
                  "If you are short on time, steps two and three matter most."],
        "step": ["Start with everything clean and dry.", "Work in good light and take your time.",
                 "Check the result before you move on.", "Repeat the last step if the first pass looks uneven.",
                 "Write down what worked so next time is faster.", "Ask in the shop if anything looks off.",
                 "Lay out every part before you begin.", "Test on a small area first.",
                 "Leave it overnight before using it again.", "Compare against the photo in the manual."],
        "about": ["We are a small team of testers, fitters and repair technicians.",
                  "Everything we sell is used by staff before it is listed.",
                  "Our workshop repairs several hundred items a year at cost."],
        "contact": ["Email us any day; we reply within one working day.",
                    "The workshop is open Tuesday to Saturday for fittings and repairs.",
                    "For order questions, have your order number ready."],
        "shipping": ["Standard delivery takes two to four working days.",
                     "Orders placed before noon ship the same day.",
                     "International orders are sent tracked and duty paid."],
        "returns": ["You have sixty days to return anything unused.",
                    "Used items can still be returned if they failed in normal use.",
                    "Repairs after the return window are charged at cost."],
    }

    def _para(self, r, key, **kw):
        sents = self.SENT[key]
        k = min(len(sents), r.randrange(2, 4) if key != "step" else 1)
        return " ".join(s.format(**kw) for s in r.sample(sents, k))

    # ---------------------------------------------------------------- 写盘
    def build(self, out, base):
        os.makedirs(out, exist_ok=True)
        for path in self.pages:
            HS._write(out, path, self.render(base, path))
        HS._json(out, "_redirects", self.redirects)
        HS._json(out, "_headers", self.headers)
        HS._common(out, base, self.sitemap)
        return out


def plan(seed, theme):
    return Site(int(seed), theme)


def build(out, base, seed, theme):
    return plan(seed, theme).build(out, base)


# ---------------------------------------------------------------- 自检:独立的小爬虫,核对站点里恰好是预埋的这些问题
def selfcheck(seed, theme):
    import socket
    import tempfile
    import threading
    import urllib.request
    import urllib.error
    import http.server
    from html.parser import HTMLParser

    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    base = "http://127.0.0.1:%d" % port
    d = tempfile.mkdtemp(prefix="scale_site_")
    site = plan(seed, theme)
    site.build(d, base)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), lambda *a, **k: HS.Handler(*a, directory=d, **k))
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    class NoRedir(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    opener = urllib.request.build_opener(NoRedir)

    def get(path):
        try:
            resp = opener.open(base + path, timeout=5)
            return resp.status, dict(resp.headers), resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read().decode("utf-8", "replace")

    class P(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links, self.canon, self.robots, self.title, self.desc, self._t = [], None, "", "", "", False

        def handle_starttag(self, tag, a):
            a = dict(a)
            if tag == "a" and a.get("href", "").startswith("/"):
                self.links.append(a["href"].split("?")[0])
            elif tag == "link" and a.get("rel") == "canonical":
                self.canon = re.sub(r"^https?://[^/]+", "", a.get("href", ""))
            elif tag == "meta" and a.get("name") == "robots":
                self.robots = a.get("content", "")
            elif tag == "meta" and a.get("name") == "description":
                self.desc = a.get("content", "")
            elif tag == "title":
                self._t = True

        def handle_endtag(self, tag):
            if tag == "title":
                self._t = False

        def handle_data(self, data):
            if self._t:
                self.title += data

    info, inlinks, depth = {}, {}, {"/": 0}
    queue = ["/"]
    while queue:
        path = queue.pop(0)
        if path in info:
            continue
        st, hd, body = get(path)
        info[path] = {"status": st, "loc": hd.get("Location"), "xrobots": hd.get("X-Robots-Tag", ""), "html": None}
        if st == 200:
            p = P()
            p.feed(body)
            info[path]["html"] = p
            for l in p.links:
                inlinks.setdefault(l, set()).add(path)
                if l not in depth:
                    depth[l] = depth[path] + 1
                    queue.append(l)
        elif st in (301, 302) and info[path]["loc"]:
            l = info[path]["loc"].split("?")[0]
            if l not in depth:
                depth[l] = depth[path]
                queue.append(l)
    smap = re.findall(r"<loc>https?://[^/]+([^<]*)</loc>", get("/sitemap.xml")[2])
    for path in smap:
        if path not in info:
            st, hd, body = get(path)
            p = None
            if st == 200:
                p = P()
                p.feed(body)
            info[path] = {"status": st, "loc": hd.get("Location"), "xrobots": hd.get("X-Robots-Tag", ""), "html": p}
    srv.shutdown()

    found = {}
    found["orphan"] = sorted(p for p in smap if info[p]["status"] == 200 and not (inlinks.get(p, set()) - {p}))
    found["sitemap_3xx"] = sorted(p for p in smap if info[p]["status"] in (301, 302, 307, 308))
    chains = []                                     # 被 <a> 引用的 3xx,按实际响应逐跳数
    for src in inlinks:
        hops, cur = 0, src
        while cur in info and info[cur]["status"] in (301, 302, 307, 308) and hops < 10:
            cur = info[cur]["loc"].split("?")[0]
            hops += 1
        if hops >= 3:
            chains.append(src)
    found["chain_linked"] = sorted(chains)
    found["canon_noindex"] = sorted(p for p, v in info.items() if v["html"] and v["html"].canon and v["html"].canon != p
                                    and info.get(v["html"].canon, {}).get("html") is not None
                                    and ("noindex" in info[v["html"].canon]["html"].robots
                                         or "noindex" in info[v["html"].canon]["xrobots"].lower()))
    groups = {}
    for p, v in info.items():
        if v["html"] and v["status"] == 200:
            groups.setdefault((v["html"].title, v["html"].desc), []).append(p)
    found["dup_pairs"] = sorted(tuple(sorted(g)) for g in groups.values() if len(g) > 1)
    found["soft404"] = sorted(p for p, v in info.items() if v["status"] == 200 and v["html"] and "not found" in v["html"].title.lower())
    found["broken_targets"] = sorted(p for p, v in info.items() if v["status"] == 404 and p in inlinks)
    found["sitemap_xrobots_noindex"] = sorted(p for p in smap if "noindex" in info[p]["xrobots"].lower())

    pl = {pid: paths for pid, paths, _, _ in site.plants}
    want = {
        "orphan": sorted(pl[k][0] for k in ("O1", "O2", "O3")),
        "sitemap_3xx": sorted(pl[k][0] for k in ("S1", "S2")),
        "chain_linked": [pl["R1"][1]],
        "canon_noindex": [pl["C1"][0]],
        "dup_pairs": sorted(tuple(sorted(pl[k])) for k in ("D1", "D2")),
        "soft404": [pl["F1"][0]],
        "broken_targets": [pl["B1"][1]],
        "sitemap_xrobots_noindex": [pl["X1"][0]],
    }
    bad = [k for k in want if [tuple(x) if isinstance(x, (list, tuple)) else x for x in found[k]] != want[k]]
    # 深度:能到达的预埋页都在 ≥4 层
    reach = {"S1": pl["S1"][1], "S2": pl["S2"][1], "R1": pl["R1"][0], "C1": pl["C1"][0], "D1a": pl["D1"][0],
             "D1b": pl["D1"][1], "D2a": pl["D2"][0], "D2b": pl["D2"][1], "F1": pl["F1"][0], "B1": pl["B1"][0], "X1": pl["X1"][0]}
    shallow = {k: depth.get(v) for k, v in reach.items() if depth.get(v) is None or depth[v] < 4}
    # 诱饵:搜索页、登录页 noindex 且不在 sitemap;分页 canonical 自指;打印版 canonical 指回原文;/cart/ 302
    dec = {did: paths for did, paths, _ in site.decoys}
    decoy_bad = []
    if "/search/" in smap or "noindex" not in info["/search/"]["html"].robots:
        decoy_bad.append("Q1")
    if any(info[p]["html"].canon != p for p in dec["Q2"]):
        decoy_bad.append("Q2")
    if any(info[p]["html"].canon != p.replace("/print", "", 1) or p in smap for p in dec["Q3"]):
        decoy_bad.append("Q3")
    if info["/cart/"]["status"] != 302 or "/cart/" in smap or "/login/" in smap:
        decoy_bad.append("Q4")
    n200 = sum(1 for v in info.values() if v["status"] == 200)
    rep = {"seed": seed, "theme": theme, "pages_200": n200, "urls_seen": len(info), "sitemap": len(smap),
           "max_depth": max(v for v in depth.values() if v is not None), "mismatch": {k: (found[k], want[k]) for k in bad},
           "shallow_plants": shallow, "decoy_bad": decoy_bad, "ok": not bad and not shallow and not decoy_bad}
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("build", "plants", "selfcheck"):
        a = sub.add_parser(name)
        a.add_argument("--seed", type=int, required=True)
        a.add_argument("--theme", choices=sorted(THEMES), required=True)
        if name == "build":
            a.add_argument("--out", required=True)
            a.add_argument("--base", default="http://127.0.0.1:8801")
    ns = ap.parse_args(argv)
    if ns.cmd == "build":
        build(ns.out, ns.base, ns.seed, ns.theme)
    elif ns.cmd == "plants":
        s = plan(ns.seed, ns.theme)
        print(json.dumps({"pages": len(s.pages), "sitemap": len(s.sitemap),
                          "plants": [{"id": a, "paths": b, "kw": c, "desc": d} for a, b, c, d in s.plants],
                          "decoys": [{"id": a, "paths": b[:3] + (["…%d 个" % len(b)] if len(b) > 3 else []), "desc": c}
                                     for a, b, c in s.decoys]}, ensure_ascii=False, indent=1))
    else:
        rep = selfcheck(ns.seed, ns.theme)
        print(json.dumps(rep, ensure_ascii=False, indent=1))
        return 0 if rep["ok"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
