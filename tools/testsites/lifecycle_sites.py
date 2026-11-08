#!/usr/bin/env python3
"""RQ-237 例 4 / 例 9 / 例 10 用的 5 个合成产品(stdlib only)。第 6 个产品(增长期)是真实的 everyinfra.com,不造。

每个产品一个目录:
  brief.md       产品说明(出题人和模拟用户的事实真源;idea 产品给被测 agent 看,其余默认不给,见 product.json)
  product.json   机器可读的元数据:上线日期、首次提交日期、哪些目录存在(不含任何答案)
  repo/          站点仓库(可选;评测驱动自己 git init,和 harness.setup 一致,这里不建 .git)
  site/          本地静态站(可选;serve 起服务。change 产品的 repo/ 本身就是站点目录)
  gsc/           假 Search Console 导出(可选):两个 28 天周期的「网页」导出(界面导出格式)
                 + 逐日 gsc-pages.csv(page,date,clicks,impressions;和 harness 的 drop 场景同格式,逐日加总 = 周期合计)

  idea       宠账本 PetLedger:只有产品说明和空仓库(只有 README)。
  prelaunch  Quillbill:Next.js 仓库(8 个 page.tsx、app/sitemap.ts)+ 本地预览站,robots.txt Disallow: /。
  launched   Northfold Coffee:上线 3 周的咖啡豆电商,robots 放行、有 sitemap,近 28 天展示 < 1000。
  mature     Trailmark Guides:徒步内容站,36 篇文章,上一期点击 1,850,这一期 1,450(-21.6%)。
  change     Soilsense:30 页的双语站仓库 + MIGRATION.md;--state after 预埋 10 个迁移问题(PLANTS),
             其余迁移是正确的(DECOYS,误报判据)。

用法:
  python3 lifecycle_sites.py build --product <id> --out DIR [--base http://127.0.0.1:PORT] [--state before|after]
  python3 lifecycle_sites.py serve --dir DIR --port N      # 认 _status、_redirects({path: [code, target]})
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hard_site  # noqa: E402  复用它的 Handler / serve(认 [code, target] 重定向、_status、缺页 404)

TODAY = datetime.date(2026, 11, 8)                       # 评测基准日(SGT);两个 28 天周期以它为界
CUR = (datetime.date(2026, 10, 11), datetime.date(2026, 11, 7))
PREV = (datetime.date(2026, 9, 13), datetime.date(2026, 10, 10))
PRODUCTS = ("idea", "prelaunch", "launched", "mature", "change")


# ---------------------------------------------------------------- 通用
def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def para(*sentences):
    return "<p>%s</p>" % " ".join(sentences)


def page(base, path, *, title, desc, h1, body, site, lang="en", alts=None, canonical=None, noindex=False,
         jsonld=None, nav=(), analytics=False, og_image=True, updated=None):
    """一页干净的 HTML:title、description、canonical、og、JSON-LD、单个 h1、h2 层级正确。"""
    head = ['<meta charset="utf-8">', "<title>%s</title>" % title,
            '<meta name="description" content="%s">' % desc,
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<link rel="canonical" href="%s">' % (canonical or base + path)]
    if noindex:
        head.append('<meta name="robots" content="noindex">')
    for hl, p in (alts or {}).items():
        head.append('<link rel="alternate" hreflang="%s" href="%s%s">' % (hl, base, p))
    head += ['<meta property="og:site_name" content="%s">' % site, '<meta property="og:title" content="%s">' % title,
             '<meta property="og:description" content="%s">' % desc, '<meta property="og:url" content="%s%s">' % (base, path)]
    if og_image:
        head.append('<meta property="og:image" content="%s/og.png">' % base)
    objs = [{"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": base + path,
             **({"dateModified": updated} if updated else {})}] + list(jsonld or [])
    for o in objs:
        head.append('<script type="application/ld+json">%s</script>' % json.dumps(o, ensure_ascii=False))
    if analytics:
        head.append("<script async src=\"https://www.googletagmanager.com/gtag/js?id=G-TEST000001\"></script>"
                    "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}"
                    "gtag('js',new Date());gtag('config','G-TEST000001');</script>")
    links = " ".join('<a href="%s">%s</a>' % (p, t) for p, t in nav)
    return ('<!doctype html><html lang="%s"><head>%s</head><body><header><nav>%s</nav></header>'
            "<main><h1>%s</h1>%s</main><footer><p>%s</p></footer></body></html>\n"
            % (lang, "".join(head), links, h1, body, site))


def org(name, url, same_as, desc):
    o = {"@context": "https://schema.org", "@type": "Organization", "name": name, "url": url, "description": desc}
    if same_as:
        o["sameAs"] = same_as
    return o


def write_site(out, base, pages, *, robots, sitemap_paths=None, lastmod=None, llms=None, redirects=None, status=None):
    for path, html in pages.items():
        write(os.path.join(out, path.strip("/"), "index.html"), html)
    write(os.path.join(out, "robots.txt"), robots)
    lm = lastmod or {}
    rows = "".join("<url><loc>%s%s</loc><lastmod>%s</lastmod></url>\n" % (base, p, lm.get(p, "2026-10-20"))
                   for p in (sitemap_paths if sitemap_paths is not None else pages))
    write(os.path.join(out, "sitemap.xml"), '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + "</urlset>\n")
    if llms:
        write(os.path.join(out, "llms.txt"), llms)
    write(os.path.join(out, "_redirects"), json.dumps(redirects or {}, indent=1))
    write(os.path.join(out, "_status"), json.dumps(status or {}, indent=1))
    with open(os.path.join(out, "og.png"), "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")


def write_meta(out, meta):
    write(os.path.join(out, "product.json"), json.dumps(meta, ensure_ascii=False, indent=1) + "\n")


def daterange(a, b):
    d = a
    while d <= b:
        yield d
        d += datetime.timedelta(days=1)


def write_gsc(out, base, cur, prev, start=None):
    """cur / prev: {path: (clicks, impressions, position)} 两个 28 天周期合计。start:站点首次有数据的日期。
    写两份界面导出(Top pages,Clicks,Impressions,CTR,Position)+ 逐日 gsc-pages.csv(逐日加总 = 周期合计)。"""
    g = os.path.join(out, "gsc")
    os.makedirs(g, exist_ok=True)
    daily = ["page,date,clicks,impressions"]
    for (a, b), data in ((PREV, prev), (CUR, cur)):
        rows = ["Top pages,Clicks,Impressions,CTR,Position"]
        for p, (c, i, pos) in sorted(data.items(), key=lambda kv: -kv[1][0]):
            rows.append("%s%s,%d,%d,%.2f%%,%.1f" % (base, p, c, i, 100.0 * c / i if i else 0, pos))
            days = [d for d in daterange(a, b) if not start or d >= start]
            for k, d in enumerate(days):                      # 平均摊到每天,余数给前几天;确定性,不随机
                dc = c // len(days) + (1 if k < c % len(days) else 0)
                di = i // len(days) + (1 if k < i % len(days) else 0)
                if dc or di:
                    daily.append("%s%s,%s,%d,%d" % (base, p, d.isoformat(), dc, di))
        write(os.path.join(g, "Pages_%s_%s.csv" % (a.isoformat(), b.isoformat())), "\n".join(rows) + "\n")
    write(os.path.join(g, "gsc-pages.csv"), "\n".join(daily) + "\n")
    tot = lambda d: {"clicks": sum(v[0] for v in d.values()), "impressions": sum(v[1] for v in d.values())}  # noqa: E731
    return {"current": dict(tot(cur), period=[CUR[0].isoformat(), CUR[1].isoformat()]),
            "previous": dict(tot(prev), period=[PREV[0].isoformat(), PREV[1].isoformat()])}


# ---------------------------------------------------------------- 0 idea:宠账本
IDEA_BRIEF = """# 宠账本 PetLedger — 产品说明(2026-11 草稿)

一句话:给养猫养狗的年轻人用的宠物健康记账 App——疫苗驱虫按时提醒、病历和化验单拍照存档、附近宠物医院价格对比。

## 现在的状态
- 只有想法和这份说明,还没写代码,仓库里只有 README。
- 域名还没买,候选:petledger.cn、chongzhangben.com。名字「宠账本」也还没定死,备选「毛孩子病历本」。
- 技术还没选:倾向先做微信小程序 + 一个官网落地页,App(iOS / Android)第二期;官网用 Next.js 还是小程序自带页面没定。

## 产品线(计划)
1. 健康提醒:疫苗、驱虫、体检按时间表推送提醒(微信服务通知)。
2. 病历档案:病历、化验单、处方拍照存档,OCR 提取关键指标,换医院时一键分享。
3. 医院比价:附近宠物医院的常见项目价格(绝育、疫苗、洗牙)对比,用户上传账单众包。

## 收费
- 基础版免费(1 只宠物、提醒 + 本地存档)。
- 会员 ¥18/月 或 ¥168/年:多只宠物、云端病历、医院比价、家人共享。

## 转化
- 上线前:加入候补名单(留手机号 / 关注公众号)。
- 上线后:注册并添加第一只宠物;付费转化是开通会员。

## 目标客户
- 中国一二线城市 22–35 岁、养猫或狗的上班族(主要)。
- 多宠家庭、刚领养的新手主人(次要)。

## 语言和市场
- 只做简体中文、中国大陆;用户主要在百度、小红书、微信里搜。
"""


def build_idea(out, base):
    write(os.path.join(out, "brief.md"), IDEA_BRIEF)
    write(os.path.join(out, "repo", "README.md"), "# petledger\n\n宠账本。还没开始写代码,产品说明见 brief.md。\n")
    write_meta(out, {"product": "idea", "name": "宠账本 PetLedger", "brief_visible_to_agent": True,
                     "has": {"repo": True, "site": False, "gsc": False}, "repo_dir": "repo",
                     "first_commit_date": "2026-11-02", "domain": None})


# ---------------------------------------------------------------- 1 prelaunch:Quillbill
QB_ROUTES = [  # (路由, page.tsx 目录, title, h1, 正文要点)
    ("/", "", "Quillbill — invoicing and time tracking for freelance designers",
     "Get paid for creative work without chasing clients",
     ["Quillbill is invoicing, time tracking and a client portal built for freelance designers, illustrators "
      "and small creative studios.", "Start a 14-day free trial of Pro, no card needed."]),
    ("/pricing/", "pricing", "Quillbill pricing: Free, Pro $12/month, Studio $29 per seat",
     "Simple pricing for freelancers and studios",
     ["Free: up to 3 clients, unlimited invoices.", "Pro: $12 per month or $120 per year, unlimited clients, "
      "automatic payment reminders and the client portal.", "Studio: $29 per seat per month for teams of 2 to 10, "
      "shared time sheets and roles.", "Every paid plan starts with a 14-day free trial, no card needed."]),
    ("/features/invoicing/", "features/invoicing", "Branded invoices with Stripe and PayPal payment links | Quillbill",
     "Invoices clients pay on time",
     ["Send branded invoices with Stripe and PayPal payment links.", "Quillbill sends polite automatic reminders "
      "before and after the due date, and supports USD, GBP, CAD and EUR."]),
    ("/features/time-tracking/", "features/time-tracking", "Time tracking that turns into invoice lines | Quillbill",
     "Track time, bill it in one click", ["Run a timer per project and turn tracked hours into invoice line items."]),
    ("/features/client-portal/", "features/client-portal", "A client portal for proofs, approvals and invoices | Quillbill",
     "One link for every client", ["Clients approve proofs, see invoices and pay from one portal link."]),
    ("/blog/", "blog", "Quillbill blog: getting paid as a freelance designer", "The Quillbill blog",
     ["Notes on pricing creative work, writing payment terms and chasing late invoices. First posts coming at launch."]),
    ("/about/", "about", "About Quillbill: a two-person team from Bristol", "About Quillbill",
     ["Quillbill is built by two former studio designers in Bristol, UK, for freelancers in the US, UK and Canada."]),
    ("/signup/", "signup", "Start your free Quillbill trial", "Start your 14-day free trial",
     ["Create your account with an email address. No card needed for the trial."]),
]
QB_BRIEF = """# Quillbill — product brief (pre-launch, 2026-11)

One line: invoicing, time tracking and a client portal for freelance designers and small creative studios.

## Status
- Code is written (Next.js 15 app router, `trailingSlash: true`), running as a local preview only.
- Domain quillbill.com is bought but not pointed at the app; public launch planned for 2026-12-01.
- robots.txt blocks everything on the preview on purpose. No analytics installed yet. No Search Console yet.

## Product lines
1. Invoicing: branded invoices, Stripe and PayPal payment links, automatic reminders, USD/GBP/CAD/EUR.
2. Time tracking: per-project timer, tracked hours become invoice line items.
3. Client portal: proofs, approvals, invoices and payment in one link.

## Pricing
- Free: up to 3 clients. Pro: $12/month or $120/year. Studio: $29 per seat per month (2-10 seats).
- 14-day free trial of Pro, no card needed.

## Conversion
- Primary: start the 14-day free trial (sign-up at /signup/). Paid conversion = trial to Pro/Studio.

## Customers
- Freelance designers and illustrators (main); small creative studios of 2-10 people.
- Markets: US, UK, Canada. Language: English only.
"""


def qb_page(base, path, title, h1, lines):
    nav = [(p, t.split(" — ")[0].split(" |")[0][:28]) for p, _, t, _, _ in QB_ROUTES[:6]]
    jl = [org("Quillbill", "https://quillbill.com", [], "Invoicing and time tracking for freelance designers")] \
        if path == "/" else []
    body = "".join(para(x) for x in lines) + "<h2>Why freelancers pick Quillbill</h2>" + para(
        "Freelance designers lose hours every month writing invoices and chasing payments.",
        "Quillbill keeps clients, tracked time and invoices in one place so the work gets paid.",
        "It was built by designers who ran a studio and hated the spreadsheet at month end.")
    return page(base, path, title=title, desc=lines[0][:150], h1=h1, body=body, site="Quillbill", jsonld=jl, nav=nav)


def build_prelaunch(out, base):
    write(os.path.join(out, "brief.md"), QB_BRIEF)
    r = os.path.join(out, "repo")
    write(os.path.join(r, "package.json"), json.dumps({
        "name": "quillbill-web", "version": "0.9.0", "private": True,
        "scripts": {"dev": "next dev", "build": "next build", "start": "next start"},
        "dependencies": {"next": "15.0.3", "react": "19.0.0", "react-dom": "19.0.0"},
        "devDependencies": {"typescript": "5.6.3", "@types/react": "19.0.0"}}, indent=2) + "\n")
    write(os.path.join(r, "next.config.js"), "/** @type {import('next').NextConfig} */\n"
          "module.exports = { trailingSlash: true };\n")
    write(os.path.join(r, "README.md"), "# quillbill-web\n\nMarketing site and app shell for Quillbill. "
          "Preview: `npm run dev`. Launch planned 2026-12-01 on quillbill.com.\n")
    write(os.path.join(r, "app", "layout.tsx"),
          "export const metadata = { metadataBase: new URL('https://quillbill.com'), openGraph: { siteName: 'Quillbill' } };\n"
          "export default function RootLayout({ children }: { children: React.ReactNode }) {\n"
          "  return (<html lang=\"en\"><body>{children}</body></html>);\n}\n")
    for path, d, title, h1, lines in QB_ROUTES:
        comp = "Page" if not d else "".join(w.capitalize() for w in d.replace("/", "-").split("-")) + "Page"
        body = "\n".join("      <p>%s</p>" % x for x in lines)
        write(os.path.join(r, "app", d, "page.tsx"),
              "export const metadata = {\n  title: %s,\n  description: %s,\n  alternates: { canonical: %s },\n};\n\n"
              "export default function %s() {\n  return (\n    <main>\n      <h1>%s</h1>\n%s\n    </main>\n  );\n}\n"
              % (json.dumps(title), json.dumps(lines[0][:150]), json.dumps(path), comp, h1, body))
    write(os.path.join(r, "app", "sitemap.ts"),
          "import type { MetadataRoute } from 'next';\n\nconst routes = %s;\n\n"
          "export default function sitemap(): MetadataRoute.Sitemap {\n"
          "  return routes.map((r) => ({ url: `https://quillbill.com${r}`, lastModified: '2026-11-01' }));\n}\n"
          % json.dumps([p for p, *_ in QB_ROUTES]))
    write(os.path.join(r, "app", "robots.ts"),
          "import type { MetadataRoute } from 'next';\n\n// Pre-launch: keep the preview out of every index. Flip before launch.\n"
          "export default function robots(): MetadataRoute.Robots {\n"
          "  return { rules: { userAgent: '*', disallow: '/' }, sitemap: 'https://quillbill.com/sitemap.xml' };\n}\n")
    s = os.path.join(out, "site")
    pages = {p: qb_page(base, p, t, h, ls) for p, _, t, h, ls in QB_ROUTES}
    write_site(s, base, pages, robots="User-agent: *\nDisallow: /\n\nSitemap: %s/sitemap.xml\n" % base,
               lastmod={p: "2026-11-01" for p in pages})
    write_meta(out, {"product": "prelaunch", "name": "Quillbill", "brief_visible_to_agent": False,
                     "has": {"repo": True, "site": True, "gsc": False}, "repo_dir": "repo", "site_dir": "site",
                     "first_commit_date": "2026-08-04", "domain": "quillbill.com", "planned_launch": "2026-12-01"})


# ---------------------------------------------------------------- 2 launched:Northfold Coffee
NF_PAGES = [  # (path, title, h1, lines)
    ("/", "Northfold Coffee — small-batch specialty coffee roasted in Portland, Maine",
     "Fresh single-origin coffee, roasted to order",
     ["Northfold Coffee roasts single-origin beans in small batches in Portland, Maine and ships them across the US "
      "within 48 hours of roasting.", "Buy a bag, start a monthly subscription from $22, or pick up a pour-over kit.",
      "Free US shipping on orders over $40."]),
    ("/shop/", "Shop single-origin coffee beans | Northfold Coffee", "Shop coffee beans",
     ["Three single origins in rotation, 12 oz bags from $18 to $26, whole bean or ground to order."]),
    ("/shop/ethiopia-guji/", "Ethiopia Guji washed coffee beans, 12 oz — $22 | Northfold Coffee", "Ethiopia Guji",
     ["Jasmine, peach and black tea. Light roast. $22 for a 12 oz bag."]),
    ("/shop/colombia-huila/", "Colombia Huila coffee beans, 12 oz — $18 | Northfold Coffee", "Colombia Huila",
     ["Caramel, red apple, milk chocolate. Medium roast. $18 for a 12 oz bag."]),
    ("/shop/kenya-nyeri/", "Kenya Nyeri AA coffee beans, 12 oz — $26 | Northfold Coffee", "Kenya Nyeri AA",
     ["Blackcurrant, grapefruit, cane sugar. Light roast. $26 for a 12 oz bag."]),
    ("/subscription/", "Coffee subscription from $22/month | Northfold Coffee", "The Northfold coffee subscription",
     ["A fresh 12 oz bag every month from $22, two bags for $40. Skip, swap or cancel any time from your account."]),
    ("/gear/", "Pour-over brewing gear | Northfold Coffee", "Brewing gear",
     ["The few tools we use every day: dripper, filters, a scale and a gooseneck kettle."]),
    ("/gear/v60-starter-kit/", "V60 pour-over starter kit — $45 | Northfold Coffee", "V60 starter kit",
     ["Hario V60 02 dripper, 100 filters, a 12 oz bag of your choice. $45."]),
    ("/brew-guides/", "Coffee brew guides | Northfold Coffee", "Brew guides",
     ["Step-by-step recipes for the three ways most of our customers brew at home."]),
    ("/brew-guides/v60/", "How to brew V60 pour-over coffee at home | Northfold Coffee", "V60 pour-over recipe",
     ["15 g coffee, 250 g water at 94 °C, a 45 second bloom and a total time near three minutes."]),
    ("/brew-guides/french-press/", "French press coffee recipe | Northfold Coffee", "French press recipe",
     ["30 g coarse coffee, 500 g water, four minutes, break the crust, then pour slowly."]),
    ("/brew-guides/aeropress/", "AeroPress coffee recipe | Northfold Coffee", "AeroPress recipe",
     ["Inverted method: 15 g coffee, 220 g water, two minutes, press for 30 seconds."]),
    ("/about/", "About Northfold Coffee | Northfold Coffee", "About us",
     ["Two roasters, one 5 kg roaster, opened online on October 18, 2026."]),
    ("/shipping/", "Shipping and returns | Northfold Coffee", "Shipping",
     ["Ships within 48 hours of roasting. Free US shipping over $40, otherwise $5.95."]),
]
NF_BRIEF = """# Northfold Coffee — product brief

One line: small-batch single-origin coffee roasted to order in Portland, Maine, sold online across the US.

## Status
- Online store launched 2026-10-18 at northfold.coffee (about three weeks ago). robots open, sitemap submitted.
- Search Console verified on launch day; GA4 installed on every page.

## Product lines
1. Single-origin beans: Ethiopia Guji $22, Colombia Huila $18, Kenya Nyeri AA $26 (12 oz bags).
2. Monthly subscription: one bag $22/month, two bags $40/month, skip or cancel any time.
3. Brewing gear: V60 starter kit $45 and a few tools.
- Free US shipping over $40.

## Conversion
- Primary: purchase (checkout completed). The subscription start is the one we care about most.

## Customers
- US home brewers who grind at home and brew pour-over, French press or AeroPress; gift buyers in Q4.
- Language: English (US) only. Ships to the US only.
"""


def build_launched(out, base):
    write(os.path.join(out, "brief.md"), NF_BRIEF)
    nav = [("/shop/", "Shop"), ("/subscription/", "Subscription"), ("/gear/", "Gear"), ("/brew-guides/", "Brew guides"),
           ("/about/", "About")]
    pages = {}
    for path, title, h1, lines in NF_PAGES:
        jl = [org("Northfold Coffee", "https://northfold.coffee", ["https://www.instagram.com/northfoldcoffee"],
                  "Small-batch specialty coffee roasted in Portland, Maine")] if path == "/" else []
        if path.startswith("/shop/") and path != "/shop/":
            price = lines[0].split("$")[1].split(" ")[0]
            jl.append({"@context": "https://schema.org", "@type": "Product", "name": h1, "brand": "Northfold Coffee",
                       "offers": {"@type": "Offer", "price": price, "priceCurrency": "USD"}})
        body = "".join(para(x) for x in lines) + "<h2>Roasted to order</h2>" + para(
            "Every bag is roasted the week it ships and dated on the label.",
            "We roast on Mondays and Thursdays and ship the same day, so beans reach most of the US within three days.",
            "If a bag is not to your taste, write to us and we will send a different origin.")
        pages[path] = page(base, path, title=title, desc=lines[0][:155], h1=h1, body=body, site="Northfold Coffee",
                           jsonld=jl, nav=nav, analytics=True, updated="2026-10-18")
    s = os.path.join(out, "site")
    write_site(s, base, pages, robots="User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % base,
               lastmod={p: "2026-10-18" for p in pages})
    # 上线 10-18,10-19 起有数据:上一期(9-13~10-10)没有任何行;这一期展示合计 640 < 1000
    cur = {"/": (6, 210, 18.4), "/shop/ethiopia-guji/": (3, 96, 24.1), "/brew-guides/v60/": (4, 120, 31.0),
           "/subscription/": (2, 64, 27.5), "/shop/colombia-huila/": (1, 52, 33.2), "/brew-guides/aeropress/": (1, 48, 38.9),
           "/shop/kenya-nyeri/": (0, 30, 41.0), "/gear/v60-starter-kit/": (1, 20, 36.3)}
    totals = write_gsc(out, base, cur, {}, start=datetime.date(2026, 10, 19))
    write_meta(out, {"product": "launched", "name": "Northfold Coffee", "brief_visible_to_agent": False,
                     "has": {"repo": False, "site": True, "gsc": True}, "site_dir": "site", "domain": "northfold.coffee",
                     "launch_date": "2026-10-18", "gsc_totals": totals})


# ---------------------------------------------------------------- 4 mature:Trailmark Guides
TM_POSTS = (  # (slug, 类型, 标题)
    [("trail-%s" % s, "trail", "%s: trail guide, distance, elevation and permits" % n) for s, n in [
        ("half-dome", "Half Dome via the Mist Trail"), ("angels-landing", "Angels Landing"),
        ("enchantments", "The Enchantments thru-hike"), ("maroon-bells-loop", "Four Pass Loop at Maroon Bells"),
        ("john-muir-trail", "John Muir Trail in 21 days"), ("wonderland-trail", "Wonderland Trail around Rainier"),
        ("presidential-traverse", "Presidential Traverse"), ("teton-crest", "Teton Crest Trail"),
        ("grand-canyon-rim-to-rim", "Grand Canyon rim to rim"), ("lost-coast", "Lost Coast Trail"),
        ("zion-narrows", "Zion Narrows top-down"), ("glacier-highline", "Highline Trail in Glacier")]]
    + [("review-%s" % s, "review", "%s review: tested for 300 miles" % n) for s, n in [
        ("osprey-exos-58", "Osprey Exos 58"), ("gregory-focal-48", "Gregory Focal 48"), ("zpacks-duplex", "Zpacks Duplex"),
        ("big-agnes-copper-spur", "Big Agnes Copper Spur HV UL2"), ("thermarest-neoair-xlite", "Therm-a-Rest NeoAir XLite"),
        ("enlightened-revelation", "Enlightened Equipment Revelation quilt"), ("altra-lone-peak-8", "Altra Lone Peak 8"),
        ("salomon-x-ultra-4", "Salomon X Ultra 4"), ("garmin-inreach-mini-2", "Garmin inReach Mini 2"),
        ("sawyer-squeeze", "Sawyer Squeeze filter"), ("jetboil-flash", "Jetboil Flash"),
        ("black-diamond-spot-400", "Black Diamond Spot 400"), ("patagonia-nano-puff", "Patagonia Nano Puff"),
        ("leki-makalu", "Leki Makalu poles"), ("rei-flash-55", "REI Flash 55"), ("nemo-tensor", "NEMO Tensor pad")]]
    + [("%s-vs-%s" % (a, b), "vs", "%s vs %s: which one should you buy?" % (na, nb)) for a, b, na, nb in [
        ("osprey-exos", "gregory-focal", "Osprey Exos", "Gregory Focal"),
        ("zpacks-duplex", "copper-spur", "Zpacks Duplex", "Big Agnes Copper Spur"),
        ("altra-lone-peak", "salomon-x-ultra", "Altra Lone Peak", "Salomon X Ultra"),
        ("inreach-mini", "zoleo", "Garmin inReach Mini 2", "ZOLEO")]]
    + [("best-%s" % s, "buying", "Best %s of 2025" % n) for s, n in [
        ("ultralight-tents", "ultralight tents"), ("backpacking-packs", "backpacking packs"),
        ("trail-runners-for-hiking", "trail runners for hiking"), ("water-filters", "backpacking water filters")]]
)
TM_BRIEF = """# Trailmark Guides — product brief

One line: independent trail guides and hands-on gear reviews for US backpackers and day hikers.

## Status
- Site trailmarkguides.com online since 2022-03 (about 4 years and 8 months). 36 articles, last updated 2026-07-02.
- Search Console and GA4 connected since 2022. Clicks fell from 1,850 (2026-09-13 to 10-10) to 1,450
  (2026-10-11 to 11-07), down 21.6 %; the drop is concentrated in the gear review and "best of" pages.

## Product lines
1. Trail guides (free): 12 long-form route guides with distance, elevation, permits and maps.
2. Gear reviews and buying guides: 16 reviews, 4 head-to-head comparisons, 4 "best of" guides,
   with affiliate links to REI and Backcountry.
3. Trailmark Pro membership: offline GPX maps and printable permit checklists, $5/month or $48/year.

## Revenue and conversion
- About 70 % of revenue is affiliate commission. Primary conversion: affiliate click-out to a retailer.
- Secondary: Trailmark Pro sign-up, newsletter sign-up (8,400 subscribers).

## Customers
- US backpackers and day hikers planning a specific trip, beginner to intermediate; gear buyers comparing models.
- Language: English only.
"""


def build_mature(out, base):
    write(os.path.join(out, "brief.md"), TM_BRIEF)
    nav = [("/blog/", "Guides and reviews"), ("/pro/", "Trailmark Pro"), ("/newsletter/", "Newsletter"), ("/about/", "About")]
    site = "Trailmark Guides"
    jl_org = org(site, "https://trailmarkguides.com", ["https://www.instagram.com/trailmarkguides",
                                                      "https://www.youtube.com/@trailmarkguides",
                                                      "https://www.pinterest.com/trailmarkguides"],
                 "Independent trail guides and gear reviews for US backpackers")
    lastmod, pages = {}, {}
    filler = para("We hike every route and carry every piece of gear before we write about it.",
                  "Each guide lists distance, elevation gain, permits, water sources and the best season.",
                  "Gear reviews are based on at least 300 trail miles and say clearly who should not buy the item.")
    core = [("/", "Trailmark Guides — trail guides and gear reviews for backpackers", "Plan the hike, pick the gear",
             "Trail guides and tested gear reviews for US backpackers and day hikers."),
            ("/blog/", "All trail guides and gear reviews | Trailmark Guides", "Guides and reviews",
             "Every route guide, gear review, comparison and buying guide in one list."),
            ("/pro/", "Trailmark Pro: offline GPX maps for $5/month | Trailmark Guides", "Trailmark Pro",
             "Offline GPX maps and printable permit checklists for every guide. $5 per month or $48 per year."),
            ("/newsletter/", "The Trailmark newsletter | Trailmark Guides", "Newsletter",
             "One email a week with a route, a gear deal and a trip report. 8,400 hikers read it."),
            ("/about/", "About Trailmark Guides | Trailmark Guides", "About",
             "Two hikers from Boulder, Colorado, writing since March 2022. We earn affiliate commission from REI and "
             "Backcountry; it never decides what we recommend.")]
    for i, (path, title, h1, lead) in enumerate(core):
        body = para(lead) + "<h2>How we test</h2>" + filler
        if path == "/blog/":
            body += "<ul>%s</ul>" % "".join('<li><a href="/blog/%s/">%s</a></li>' % (s, t) for s, _, t in TM_POSTS)
        pages[path] = page(base, path, title=title, desc=lead[:155], h1=h1, body=body, site=site, nav=nav,
                           jsonld=[jl_org] if path == "/" else [], analytics=True, updated="2026-07-02")
        lastmod[path] = "2026-07-02"
    d0 = datetime.date(2022, 3, 14)
    for i, (slug, kind, title) in enumerate(TM_POSTS):
        path = "/blog/%s/" % slug
        mod = min(d0 + datetime.timedelta(days=45 * i), datetime.date(2026, 7, 2)).isoformat()
        lead = {"trail": "A complete route guide with distance, elevation, permits and the best season.",
                "review": "Our hands-on review after 300 trail miles, with who should and should not buy it.",
                "vs": "We carried both on the same trips. Here is how they compare and which one to buy.",
                "buying": "The models we would buy today, tested on real trips, with a pick for every budget."}[kind]
        body = para(lead) + "<h2>The short answer</h2>" + filler + "<h2>Details</h2>" + filler
        if kind != "trail":
            body += para('<a href="https://www.rei.com/" rel="sponsored nofollow">Check the price at REI</a>')
        jl = [{"@context": "https://schema.org", "@type": "Article", "headline": title, "datePublished":
               min(d0 + datetime.timedelta(days=45 * i), datetime.date(2026, 6, 1)).isoformat(),
               "dateModified": mod, "author": {"@type": "Person", "name": "Maya Lindqvist"}}]
        pages[path] = page(base, path, title=title + " | Trailmark Guides", desc=lead, h1=title, body=body, site=site,
                           nav=nav, jsonld=jl, analytics=True, updated=mod)
        lastmod[path] = mod
    write_site(os.path.join(out, "site"), base, pages, robots="User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % base,
               lastmod=lastmod)
    prev, cur = {"/": (120, 6100, 6.2), "/pro/": (14, 900, 12.0), "/newsletter/": (6, 400, 15.3)}, \
        {"/": (118, 6000, 6.3), "/pro/": (13, 880, 12.4), "/newsletter/": (6, 410, 15.0)}
    for i, (slug, kind, _) in enumerate(TM_POSTS):
        p = "/blog/%s/" % slug
        if kind == "trail":
            c = 40 - i
            prev[p] = (c, c * 48, 8.0 + i * 0.3)
            cur[p] = (c - 1, (c - 1) * 48, 8.1 + i * 0.3)
        else:                                                 # 评测和「best of」页掉量:位置后退、点击少约 35%
            c = 54 - (i - 12) * 1
            prev[p] = (c, c * 60, 6.5 + (i - 12) * 0.2)
            cur[p] = (round(c * 0.63), round(c * 60 * 0.82), 9.8 + (i - 12) * 0.25)
    # 把合计校准到事先写定的 1,850 / 1,450(差额记在首页上,不随机)
    sp, sc = sum(v[0] for v in prev.values()), sum(v[0] for v in cur.values())
    prev["/"] = (prev["/"][0] + 1850 - sp, prev["/"][1], prev["/"][2])
    cur["/"] = (cur["/"][0] + 1450 - sc, cur["/"][1], cur["/"][2])
    totals = write_gsc(out, base, cur, prev)
    assert totals["previous"]["clicks"] == 1850 and totals["current"]["clicks"] == 1450, totals
    write_meta(out, {"product": "mature", "name": "Trailmark Guides", "brief_visible_to_agent": False,
                     "has": {"repo": False, "site": True, "gsc": True}, "site_dir": "site",
                     "domain": "trailmarkguides.com", "launch_date": "2022-03-14", "gsc_totals": totals})


# ---------------------------------------------------------------- 5 change:Soilsense
SS_EN_POSTS = ["soil-moisture-basics", "watering-schedule", "indoor-plants-light", "fertilizer-guide", "compost-at-home",
               "pest-control", "repotting-guide", "overwatering-signs", "seed-starting", "winter-care"]
SS_DE_POSTS = {"zimmerpflanzen-licht": "indoor-plants-light", "duenger-ratgeber": "fertilizer-guide",
               "winterpflege": "winter-care", "giessplan": "watering-schedule", "kompost-zuhause": "compost-at-home"}
SS_PRODUCTS = {"sensor-mini": ("Soilsense Sensor Mini", 29, "soil moisture"),
               "sensor-pro": ("Soilsense Sensor Pro", 59, "soil moisture, light and temperature"),
               "hub": ("Soilsense Hub", 79, "Wi-Fi bridge for up to 16 sensors")}

# 预埋的 10 个迁移问题(开工前写定)。(编号, 类型, 判对时可以落在的 URL, 问题描述里应出现的词(正则), 怎么埋)
PLANTS = [
    ("M1", "missing_301", ["/blog/soil-moisture-basics/"], r"404|301|重定向|redirect|映射|missing|漏",
     "旧文章 /blog/soil-moisture-basics/ 没有任何重定向,直接 404(新页 /articles/soil-moisture-basics/ 是 200)"),
    ("M2", "redirect_chain", ["/blog/watering-schedule/", "/articles/watering-schedule-2025/"],
     r"链|chain|多跳|两次|hop", "/blog/watering-schedule/ → 301 /articles/watering-schedule-2025/ → 301 /articles/watering-schedule/"),
    ("M3", "canonical_old", ["/articles/indoor-plants-light/"], r"canonical|规范",
     "新页 /articles/indoor-plants-light/ 的 canonical 还指向旧址 /blog/indoor-plants-light/"),
    ("M4", "hreflang_broken", ["/de/articles/duenger-ratgeber/", "/articles/fertilizer-guide/"],
     r"hreflang|回链|互指|return|reciproc|alternate",
     "/de/articles/duenger-ratgeber/ 的 hreflang=en 指向旧址 /blog/fertilizer-guide/(301),英德两页不再互指"),
    ("M5", "sitemap_old", ["/blog/compost-at-home/", "/articles/compost-at-home/"], r"sitemap|站点地图",
     "sitemap.xml 列的是旧址 /blog/compost-at-home/,新址 /articles/compost-at-home/ 没列"),
    ("M6", "internal_link_old", ["/articles/", "/blog/pest-control/"], r"内链|链接|link|href",
     "/articles/ 列表页链向旧址 /blog/pest-control/(要经 301 才到新页)"),
    ("M7", "noindex_new", ["/products/sensor-pro/"], r"noindex", "新页 /products/sensor-pro/ 带 meta robots noindex"),
    ("M8", "redirect_302", ["/product/hub/"], r"302|临时|temporary", "/product/hub/ 用 302 跳到 /products/hub/,应为 301"),
    ("M9", "redirect_home", ["/product/sensor-mini/"], r"首页|home|/ |根|soft ?404|homepage",
     "/product/sensor-mini/ 301 到首页 /,而不是 /products/sensor-mini/"),
    ("M10", "case_mismatch", ["/de/blog/winterpflege/", "/de/articles/Winterpflege/"],
     r"大小写|case|Winterpflege|404", "/de/blog/winterpflege/ 301 到 /de/articles/Winterpflege/(大写 W,404),真页是小写"),
]
PLANT_URLS = sorted({u for _, _, us, _, _ in PLANTS for u in us})


def ss_new(path):
    """改版计划里的映射规则(MIGRATION.md 写的就是它)。"""
    for old, new in (("/de/blog/", "/de/articles/"), ("/blog/", "/articles/"), ("/de/product/", "/de/products/"),
                     ("/product/", "/products/")):
        if path.startswith(old):
            return new + path[len(old):]
    return path


def ss_old_paths():
    ps = ["/", "/about/", "/pricing/", "/contact/", "/products/", "/blog/"] + ["/blog/%s/" % s for s in SS_EN_POSTS] \
        + ["/product/%s/" % k for k in SS_PRODUCTS] + ["/de/", "/de/pricing/", "/de/blog/"] \
        + ["/de/blog/%s/" % s for s in SS_DE_POSTS] + ["/de/product/%s/" % k for k in SS_PRODUCTS]
    assert len(ps) == 30, len(ps)
    return ps


def ss_alts(path, mapped):
    """hreflang 簇(以旧结构描述,mapped 把它换成当前状态的 URL)。"""
    pairs = [("/", "/de/"), ("/pricing/", "/de/pricing/"), ("/blog/", "/de/blog/")] \
        + [("/product/%s/" % k, "/de/product/%s/" % k) for k in SS_PRODUCTS] \
        + [("/blog/%s/" % en, "/de/blog/%s/" % de) for de, en in SS_DE_POSTS.items()]
    for en, de in pairs:
        if path in (en, de):
            return {"en": mapped(en), "de": mapped(de), "x-default": mapped(en)}
    return None


SS_BRIEF = """# Soilsense — product brief

One line: smart soil sensors that tell home gardeners and houseplant owners exactly when to water.

## Status
- Site soilsense.io online since 2024-05 (English and German, 30 pages). GA4 installed.
  Search Console exists but no export or access is shared for this project; AI referrals and citations are not measured.
- Planned change (see MIGRATION.md): move /blog/<slug>/ to /articles/<slug>/, merge /product/* into /products/*,
  same for /de/. Launch window 2026-11-24.

## Product lines
1. Soilsense Sensor Mini: soil moisture, $29.
2. Soilsense Sensor Pro: soil moisture, light and temperature, $59.
3. Soilsense Hub: Wi-Fi bridge for up to 16 sensors, $79; the app is free, app Premium (history and alerts) $3/month.

## Conversion
- Primary: online store purchase (checkout completed).

## Customers
- Home gardeners and houseplant owners in the US and Germany (DACH); plant-shop resellers are secondary.
- Languages: English and German.
"""


def ss_page(base, path, mapped, state):
    de = path.startswith("/de/")
    lang = "de" if de else "en"
    old = path if state == "before" else None
    kind_path = old or path
    seg = kind_path.strip("/").split("/")
    if kind_path in ("/", "/de/"):
        title = "Soilsense — Bodensensoren, die sagen, wann gegossen wird" if de else \
            "Soilsense — smart soil sensors that tell you when to water"
        lead = ("Soilsense misst Bodenfeuchte, Licht und Temperatur und sagt dir, wann deine Pflanzen Wasser brauchen."
                if de else "Soilsense measures soil moisture, light and temperature and tells you when each plant needs water.")
    elif seg[-1] in SS_PRODUCTS:
        n, price, what = SS_PRODUCTS[seg[-1]]
        title, lead = "%s — $%d | Soilsense" % (n, price), "%s measures %s. $%d, free app." % (n, what, price)
    elif seg[-1] in ("pricing",):
        title = "Preise | Soilsense" if de else "Soilsense prices: Sensor Mini $29, Sensor Pro $59, Hub $79"
        lead = "Sensor Mini $29, Sensor Pro $59, Hub $79. App free, Premium $3/month."
    elif seg[-1] in ("blog", "articles"):
        title = "Ratgeber | Soilsense" if de else "Plant care articles | Soilsense"
        lead = "Practical plant care: watering, light, soil and seasons."
    elif seg[-1] == "products":
        title, lead = "All Soilsense products | Soilsense", "Sensor Mini, Sensor Pro and the Hub, compared on one page."
    elif seg[-1] in ("about", "contact"):
        title = "%s | Soilsense" % seg[-1].capitalize()
        lead = "Soilsense is a team of six in Leipzig and Austin building sensors for people who keep plants alive."
    else:
        title = "%s | Soilsense" % seg[-1].replace("-", " ").capitalize()
        lead = ("Ein praktischer Ratgeber zur Pflanzenpflege." if de else
                "A practical guide to %s for home gardeners." % seg[-1].replace("-", " "))
    nav_items = ["/", "/products/", "/pricing/", "/blog/", "/about/"] if not de else ["/de/", "/de/pricing/", "/de/blog/"]
    nav = [(mapped(p), p.strip("/").split("/")[-1] or "Home") for p in nav_items]
    body = para(lead) + "<h2>%s</h2>" % ("Details" if not de else "Details") + para(
        "Soilsense sensors sit in the pot or bed and report every 15 minutes to the free app.",
        "The app learns each plant and sends one alert when it is time to water, not a stream of numbers.")
    listing = None
    if seg[-1] in ("blog", "articles"):
        listing = ["/de/blog/%s/" % s for s in SS_DE_POSTS] if de else ["/blog/%s/" % s for s in SS_EN_POSTS]
    if seg[-1] == "products":
        listing = ["/product/%s/" % k for k in SS_PRODUCTS]
    alts = ss_alts(old or _back(path), mapped)
    canonical = None
    noindex = False
    if listing:
        links = [mapped(u) for u in listing]
        if state == "after" and path == "/articles/":                               # M6
            links = [("/blog/pest-control/" if u == "/articles/pest-control/" else u) for u in links]
        body += "<ul>%s</ul>" % "".join('<li><a href="%s">%s</a></li>' % (u, u.strip("/").split("/")[-1]) for u in links)
    if state == "after":
        if path == "/articles/indoor-plants-light/":                               # M3
            canonical = base + "/blog/indoor-plants-light/"
        if path == "/de/articles/duenger-ratgeber/":                               # M4
            alts = dict(alts, en="/blog/fertilizer-guide/")
        if path == "/products/sensor-pro/":                                       # M7
            noindex = True
    jl = [org("Soilsense", "https://soilsense.io", ["https://www.instagram.com/soilsense",
                                                     "https://www.youtube.com/@soilsense"],
              "Smart soil sensors for home gardeners")] if path in ("/", "/de/") else []
    return page(base, path, title=title, desc=lead[:155], h1=title.split(" | ")[0], body=body, site="Soilsense",
                lang=lang, alts=alts, canonical=canonical, noindex=noindex, jsonld=jl, nav=nav, analytics=True)


_BACK = {}


def _back(new_path):
    return _BACK.get(new_path, new_path)


def migration_md(olds):
    rows = "".join("| %s | %s |\n" % (o, ss_new(o)) for o in olds if ss_new(o) != o)
    return ("# Soilsense URL 改版计划\n\n目标上线日:2026-11-24。\n\n## 规则\n\n"
            "1. `/blog/<slug>/` 改成 `/articles/<slug>/`,`/blog/` 列表改成 `/articles/`。\n"
            "2. `/product/<name>/` 合并进 `/products/<name>/`(`/products/` 列表页保留)。\n"
            "3. 德语同样:`/de/blog/*` → `/de/articles/*`,`/de/product/*` → `/de/products/*`。\n"
            "4. 每个旧 URL 一跳 301 到新 URL;canonical、hreflang、sitemap、站内链接全部换成新 URL。\n"
            "5. 其余页面(/、/about/、/pricing/、/contact/、/de/、/de/pricing/)不动。\n\n"
            "## 映射表(旧 → 新)\n\n| 旧 | 新 |\n|---|---|\n" + rows)


def build_change(out, base, state):
    write(os.path.join(out, "brief.md"), SS_BRIEF)
    repo = os.path.join(out, "repo")
    olds = ss_old_paths()
    if state == "before":
        mapped = lambda p: p  # noqa: E731
        pages = {p: ss_page(base, p, mapped, "before") for p in olds}
        write_site(repo, base, pages, robots="User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % base,
                   llms="# Soilsense\n\n> Smart soil sensors for home gardeners.\n\n" +
                   "".join("- [%s](%s%s)\n" % (p, base, p) for p in olds))
    else:
        _BACK.clear()
        _BACK.update({ss_new(o): o for o in olds})
        news = [ss_new(o) for o in olds]
        pages = {p: ss_page(base, p, ss_new, "after") for p in news}
        redirects = {o: [301, ss_new(o)] for o in olds if ss_new(o) != o}
        status = {}
        del redirects["/blog/soil-moisture-basics/"]                                          # M1
        redirects["/blog/watering-schedule/"] = [301, "/articles/watering-schedule-2025/"]     # M2
        redirects["/articles/watering-schedule-2025/"] = [301, "/articles/watering-schedule/"]
        redirects["/product/hub/"] = [302, "/products/hub/"]                                  # M8
        redirects["/product/sensor-mini/"] = [301, "/"]                                       # M9
        redirects["/de/blog/winterpflege/"] = [301, "/de/articles/Winterpflege/"]             # M10
        status["/de/articles/Winterpflege/"] = 404          # macOS 文件系统不分大小写,显式写死 404,和线上 Linux 一致
        status["/blog/soil-moisture-basics/"] = 404
        smap = [("/blog/compost-at-home/" if p == "/articles/compost-at-home/" else p) for p in news]   # M5
        write_site(repo, base, pages, robots="User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % base,
                   sitemap_paths=smap, redirects=redirects, status=status,
                   llms="# Soilsense\n\n> Smart soil sensors for home gardeners.\n\n" +
                   "".join("- [%s](%s%s)\n" % (p, base, p) for p in news))
    write(os.path.join(repo, "MIGRATION.md"), migration_md(olds))
    write(os.path.join(repo, "README.md"), "# soilsense-site\n\nStatic site for soilsense.io (EN + DE). "
          "Server config: `_redirects` ({path: [code, target]}) and `_status`. URL change plan: MIGRATION.md.\n")
    write_meta(out, {"product": "change", "name": "Soilsense", "brief_visible_to_agent": False, "state": state,
                     "has": {"repo": True, "site": True, "gsc": False}, "repo_dir": "repo", "site_dir": "repo",
                     "domain": "soilsense.io", "launch_date": "2024-05-06", "first_commit_date": "2024-05-06",
                     "plants": [p[0] for p in PLANTS] if state == "after" else []})


# ---------------------------------------------------------------- 入口
def build(product, out, base, state="before"):
    base = base.rstrip("/")
    os.makedirs(out, exist_ok=True)
    {"idea": build_idea, "prelaunch": build_prelaunch, "launched": build_launched, "mature": build_mature}.get(
        product, lambda o, b: build_change(o, b, state))(out, base)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--product", choices=PRODUCTS, required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--base", default="http://127.0.0.1:8801")
    b.add_argument("--state", choices=("before", "after"), default="before", help="只对 change 有效")
    s = sub.add_parser("serve")
    s.add_argument("--dir", required=True)
    s.add_argument("--port", type=int, default=8801)
    ns = ap.parse_args(argv)
    if ns.cmd == "build":
        print(build(ns.product, ns.out, ns.base, ns.state))
    else:
        hard_site.serve(ns.dir, ns.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
