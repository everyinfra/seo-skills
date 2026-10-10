#!/usr/bin/env python3
"""市场 SERP 占位审计(stdlib)。用法:
  python3 serp_occupancy.py --market tr "google.com,eksisozluk.com,www.donanimhaber.com,..."
对照 markets.json serp_occupancy 内置占位表(tr/th/in/kr/jp/vn/ru),输出:
UGC/比价/投诉/Q&A/目录平台占位数 + 品牌词审计提示(şikayetvar/Pantip/ReclameAqui 同构)。
域名列表也可走 stdin;子域/https/www 均归一匹配;支持全角域名 NFKC 归一。"""
import sys, os, json, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))

def norm(d):
    d = unicodedata.normalize("NFKC", d.strip().strip(",;"))
    d = d.split("//", 1)[-1].split("/")[0].split(":")[0].split("?")[0]
    return d[4:] if d.startswith("www.") else d.lower()

USAGE = """usage: serp_occupancy.py --market XX "dom1,dom2,..."   (域名列表也可走 stdin)
对照 markets.json serp_occupancy 内置占位表(tr/th/in/kr/jp/vn/ru),输出
UGC/比价/投诉/Q&A/目录平台占位数 + 品牌词审计提示。"""

def main():
    args = sys.argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(USAGE)
        return
    market = args[args.index("--market") + 1] if "--market" in args else None
    pos = [a for a in args if not a.startswith("--") and a != market]
    raw = " ".join(pos) if pos else sys.stdin.read()
    domains = [norm(x) for x in raw.replace(",", " ").split() if norm(x)]
    with open(os.path.join(BASE, "markets.json"), encoding="utf-8") as f:
        data = json.load(f)
    table = data["serp_occupancy"]
    if not market or market not in table:
        sys.stderr.write(USAGE + "\n--market 必填且须在占位表内;可用: %s\n" % ", ".join(table))
        sys.exit(2)
    if not domains:
        sys.exit("未输入域名;位置参数传逗号分隔的前10域名,或走 stdin")
    occ = table[market]
    cats, hits = {}, []
    for i, d in enumerate(domains, 1):
        m = next((k for k in occ if d == k or d.endswith("." + k)), None)
        if m:
            cat = occ[m].split("(")[0]
            cats[cat] = cats.get(cat, 0) + 1
            hits.append("  #%-2d %-28s → %s" % (i, d, occ[m]))
    ugc = sum(v for k, v in cats.items() if "ugc" in k)
    price = cats.get("price-compare", 0)
    complaint = sum(v for k, v in cats.items() if "complaint" in k or "review" in k)
    print("市场 %s:SERP %d 席 → 占位表命中 %d" % (market, len(domains), len(hits)))
    print("\n".join(hits) if hits else "  (无占位表域名命中)")
    if cats:
        print("类别统计: %s" % cats)
    print("UGC 平台 %d 席 | 比价 %d 席 | 投诉/评测 %d 席" % (ugc, price, complaint))
    print("非占位表域名 %d 席(品牌/媒体/电商自营——自建内容的机会位)" % (len(domains) - len(hits)))
    print()
    print("⚠ 品牌词审计必查本国投诉站占位(同构平台,占位=信任面失守):")
    for region, sites in data.get("complaint_lookalikes", {}).items():
        if region == "_note":
            print("  (%s)" % sites)
        else:
            print("  %s: %s" % (region, ", ".join(sites)))

if __name__ == "__main__":
    main()
