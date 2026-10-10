#!/usr/bin/env python3
"""跨语言关键词变体归组(stdlib)。stdin 每行一词 → 分组输出 group_id: [words]。
归一链(顺序固定):
① NFKC 全/半角归一(ＳＥＯ→SEO、ｱﾏｿﾞﾝ→アマゾン);
② 土耳其 İ 陷阱:先 replace('İ','i') 再 casefold(避免 İ→i̇ 双码点),并去残留 U+0307;
③ 俄语 ё→е(casefold 后 Ё 已成 ё);
④ 阿拉伯正字归一:أ/إ/ٱ→ا、ى→ي、ة→ه、去 tatweel ـ(U+0640);
⑤ 越南声调剥离:词含越南专用字母(ăâđêôơư 或 U+1EA0-1EF9)时 NFD 去 combining
("không"→"khong")——归组但提示"有调/无调意图不同,排名当独立词跟踪"。
用法: cat words.txt | python3 keyword_variants.py [--json]"""
import sys, json, unicodedata

AR_MAP = {"أ": "ا", "إ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"}
TATWEEL = "\u0640"
VI_BASE = set("ăâđêôơưĂÂĐÊÔƠƯ")

def is_viet(w):
    return any(c in VI_BASE or 0x1EA0 <= ord(c) <= 0x1EF9 for c in w)

def canon(word):
    """→ (canonical, applied_rules)"""
    rules = []
    orig = word.strip()
    w = unicodedata.normalize("NFKC", orig)
    if w != orig:
        rules.append("fullwidth/halfwidth(NFKC)")
    if "İ" in w:
        rules.append("tr-İ")
    w = w.replace("İ", "i")
    w = w.casefold()
    if "\u0307" in w:  # İ 折叠残留的组合点
        w = w.replace("\u0307", "")
    if "ё" in w:
        rules.append("ru-ё→е")
        w = w.replace("ё", "е")
    if any(c in AR_MAP for c in w) or TATWEEL in w:
        rules.append("ar-ortho")
        w = w.replace(TATWEEL, "")
        w = "".join(AR_MAP.get(c, c) for c in w)
    if is_viet(w):
        stripped = "".join(c for c in unicodedata.normalize("NFD", w) if unicodedata.combining(c) == 0)
        nd = unicodedata.normalize("NFC", stripped)
        if nd != w:
            rules.append("vi-tone")
            w = nd
    return w, rules

USAGE = """usage: cat words.txt | keyword_variants.py [--json]
跨语言变体归组(阿正书/越声调/全半角/土 İ/俄 ё);--json 输出分组结构。"""

def main():
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(USAGE)
        return
    as_json = "--json" in sys.argv
    words = [ln.strip() for ln in sys.stdin if ln.strip() and not ln.startswith("#")]
    groups = {}
    for w in words:
        c, rules = canon(w)
        groups.setdefault(c, []).append((w, rules))
    rows = []
    for i, (c, ws) in enumerate(sorted(groups.items(), key=lambda kv: (-len(set(x[0] for x in kv[1])), kv[0])), 1):
        uniq = list(dict.fromkeys(w for w, _ in ws))
        rules = sorted({r for _, rs in ws for r in rs})
        rows.append(("g%d" % i, uniq, c, rules))
    if as_json:
        print(json.dumps({gid: {"canonical": c, "words": ws, "rules": r} for gid, ws, c, r in rows},
                         ensure_ascii=False, indent=1))
        return
    merged = sum(len(ws) - 1 for _, ws, _, _ in rows)
    for gid, ws, c, rules in rows:
        print("%s: %s  canon=%s%s" % (gid, ws, c, "  rules=%s" % rules if rules else ""))
        if any("vi-tone" in r for r in rules):
            print("    ⚠ 越南有调/无调意图可能不同——归组便于研究,排名当独立词跟踪")
        if any("fullwidth" in r for r in rules):
            print("    ⚠ 全/半角变体归组——SERP 与工具计数以半角为准")
    print("\n%d 词 → %d 组(%d 处合并)" % (len(words), len(rows), merged))

if __name__ == "__main__":
    main()
