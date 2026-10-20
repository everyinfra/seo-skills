#!/usr/bin/env python3
"""跨语言关键词变体归组(stdlib)。stdin 每行一词 → 分组输出 group_id: [words]。
归一链(顺序固定):
① NFKC 全/半角归一(ＳＥＯ→SEO、ｱﾏｿﾞﾝ→アマゾン);
② 土耳其 İ 陷阱:先 replace('İ','i') 再 casefold(避免 İ→i̇ 双码点),并去残留 U+0307;
③ 俄语 ё→е(casefold 后 Ё 已成 ё);
④ 阿拉伯正字归一:أ/إ/ٱ→ا、ى→ي、ة→ه、去 tatweel ـ(U+0640);
⑤ 越南声调剥离:词含越南专用字母(ăâđêôơư 或 U+1EA0-1EF9)时 NFD 去 combining
("không"→"khong"),đ→d——归组但提示"有调/无调意图不同,排名当独立词跟踪";
⑥ 拉丁变音折叠:拉丁字母 NFD 去组合符号,另对 NFD 分解不掉的字母显式映射
(đ→d、ł→l、ø→o、ħ→h、ı→i、æ→ae、œ→oe、þ→th、ð→d;ß 已由 casefold 变 ss)——
"łódź"/"lodz"、"đường"/"duong" 同组;只动拉丁字母,西里尔 й、假名 が 等不动(B52 修,2026-10-21)。
用法: cat words.txt | python3 keyword_variants.py [--json]"""
import sys, json, unicodedata

AR_MAP = {"أ": "ا", "إ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"}
TATWEEL = "\u0640"
VI_BASE = set("ăâđêôơưĂÂĐÊÔƠƯ")
# NFD 分解不掉的拉丁字母(casefold 之后的小写形)。ß 由 casefold 处理成 ss。
LATIN_LETTER_MAP = {"đ": "d", "ł": "l", "ø": "o", "ħ": "h", "ı": "i", "æ": "ae", "œ": "oe",
                    "þ": "th", "ð": "d", "ŧ": "t", "ŀ": "l"}


def _is_latin(c):
    try:
        return "LATIN" in unicodedata.name(c)
    except ValueError:
        return False


def latin_fold(w):
    """拉丁字母去变音 + 显式映射;非拉丁字符原样保留。"""
    out = []
    for c in w:
        if not _is_latin(c):
            out.append(c)
            continue
        if c in LATIN_LETTER_MAP:
            out.append(LATIN_LETTER_MAP[c])
            continue
        out.append("".join(x for x in unicodedata.normalize("NFD", c) if unicodedata.combining(x) == 0))
    return "".join(out)

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
        nd = latin_fold(w)
        if nd != w:
            rules.append("vi-tone")
            w = nd
    nd = unicodedata.normalize("NFC", latin_fold(w))
    if nd != w:
        rules.append("latin-diacritics")
        w = nd
    return w, rules

USAGE = """usage: cat words.txt | keyword_variants.py [--json]
跨语言变体归组(阿正书/越声调/全半角/土 İ/俄 ё/拉丁变音 đ ł ø);--json 输出分组结构。"""

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
        if any("latin-diacritics" in r for r in rules):
            print("    ⚠ 有/无变音写法归组——搜索意图可能不同,排名当独立词跟踪")
        if any("fullwidth" in r for r in rules):
            print("    ⚠ 全/半角变体归组——SERP 与工具计数以半角为准")
    print("\n%d 词 → %d 组(%d 处合并)" % (len(words), len(rows), merged))

if __name__ == "__main__":
    main()
