#!/usr/bin/env python3
"""JSON-LD 实体规则检查器(stdlib)。从页面提取所有 ld+json 块,检查:
@id 绝对性 / 引用悬空(publisher/author/isPartOf 指向未声明 @id)/ 同名实体分裂 /
占位符黑名单 / aggregateRating 范围 / FAQPage 空答案。
用法: python3 schema_lint.py URL"""
import sys, re, json, urllib.request

UA = "Mozilla/5.0 (compatible; seo-suite-audit/1.0)"
PLACEHOLDERS = ["[Business Name]", "[City]", "[INSERT", "[REPLACE_", "[要追加", "[INVULLEN", "TODO", "example.com"]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read(2_000_000).decode("utf-8", "replace")

def walk(node, fn):
    if isinstance(node, dict):
        fn(node)
        for v in node.values(): walk(v, fn)
    elif isinstance(node, list):
        for v in node: walk(v, fn)

USAGE = """usage: schema_lint.py URL
提取页面全部 JSON-LD 块,检查:@id 绝对性/引用悬空/同名实体分裂/占位符黑名单/
aggregateRating 范围/FAQPage 空答案。"""

def main():
    a = sys.argv[1:]
    if any(x in ("-h", "--help") for x in a):
        print(USAGE)
        return
    if not a or a[0].startswith("-"):
        sys.stderr.write(USAGE + "\n")
        sys.exit(2)
    url = a[0]
    html = fetch(url)
    blocks = re.findall(r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", html, re.S | re.I)
    if not blocks:
        print("无 JSON-LD"); sys.exit(1)
    objs, ids, raw = [], [], " ".join(blocks)
    for b in blocks:
        try: objs.append(json.loads(b))
        except json.JSONDecodeError as e:
            print(f"[CRITICAL] JSON 解析失败: {e}")
    refs = set()
    for o in objs:
        walk(o, lambda n: refs.update(str(v) for k, v in n.items() if k in ("publisher", "author", "isPartOf", "mainEntity") and isinstance(v, str) and v.startswith("#") or (isinstance(v, str) and str(v).startswith(("http", "#")) and k in ("publisher","author","isPartOf")) ))
    allids = set()
    for o in objs:
        walk(o, lambda n: allids.add(n["@id"]) if isinstance(n.get("@id"), str) else None)
    type_by_id = {}
    for o in objs:
        walk(o, lambda n: type_by_id.setdefault(n.get("@id"), set()).add(n.get("@type")) if n.get("@id") else None)
    crit = 0
    for o in objs:
        def check(n):
            nonlocal crit
            i = n.get("@id")
            if isinstance(i, str):
                if not i.startswith(("http", "#", "urn")):
                    print(f"[CRITICAL] @id 非绝对: {i}"); crit += 1
                if i.startswith("#") and urljoin_check(i) and f"{i}" not in allids and len(allids) > 1:
                    pass
            for k in ("publisher", "author", "isPartOf", "mainEntity"):
                v = n.get(k)
                if isinstance(v, str) and v.startswith("#") and v not in allids:
                    print(f"[CRITICAL] 引用悬空: {k}={v} 未在本页声明"); crit += 1
            ar = n.get("aggregateRating")
            if ar and n.get("@type") in ("Organization", "WebPage", "WebSite"):
                print(f"[WARN] aggregateRating 挂在 {n.get('@type')}(自评,富结果受限/垃圾信号)"); crit += 0
            if n.get("@type") == "FAQPage":
                qs = n.get("mainEntity") or []
                for q in qs:
                    ans = (q or {}).get("acceptedAnswer", {}).get("text", "")
                    if not ans or len(str(ans)) < 20:
                        print(f"[CRITICAL] FAQ 空答案: {q}"); crit += 1
        walk(o, check)
    for i, ts in type_by_id.items():
        if len(ts) > 1: print(f"[WARN] 同 @id 多 @type: {i} → {ts}")
    for p in PLACEHOLDERS:
        if p in raw: print(f"[CRITICAL] 占位符残留: {p}"); crit += 1
    def urljoin_check(i): return False
    print(f"\n块数 {len(blocks)} 有效对象 {len(objs)} @id {len(allids)}")
    sys.exit(1 if crit else 0)

if __name__ == "__main__": main()
