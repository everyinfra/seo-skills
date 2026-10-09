#!/usr/bin/env python3
"""文本度量与反 AI 腔检测(stdlib)。CJK 感知词数/句长节奏(metronomic 检测)/
em-dash 密度/中英 slop 词/Unicode 水印扫描与清除/FAQ 问句计数。
用法: cat page.txt | python3 text_metrics.py [--market zh|en|ja] [--scrub]
清除水印输出到 stdout,分析输出到 stderr。"""
import sys, re, unicodedata

WATERMARK = ["\u200b", "\ufeff", "\u200c", "\u200d", "\u2060", "\u2061", "\u2062", "\u2063", "\u2064", "\u180e", "\u202f"]
ZH_SLOP = ["创新领先", "卓越", "全方位", "一站式", "极致", "颠覆", "最佳", "赋能", "引领", "匠心"]
EN_SLOP = ["delve", "tapestry", "seamless", "effortless", "leverage", "holistic", "bespoke",
           "revolutionize", "supercharge", "unlock the", "in today's fast-paced",
           "it's important to note", "game-changer", "cutting-edge", "countless", "myriad"]
VAGUE_CLAIMS = ["行业领先", "业内首创", "best-in-class", "industry-leading"]

def is_cjk(c):
    o = ord(c)
    return 0x4E00 <= o <= 0x9FFF or 0x3040 <= o <= 0x30FF or 0xAC00 <= o <= 0xD7AF

def sentences(text, market):
    if market in ("zh", "ja"):
        parts = re.split(r"[。!?!?]+", text)
    else:
        parts = re.split(r"[.!?]+", text)
    return [p.strip() for p in parts if len(p.strip()) > 3]

def wc(text):
    cjk = sum(1 for c in text if is_cjk(c))
    return cjk + len(re.findall(r"[A-Za-z0-9']+", text))

def main():
    args = sys.argv[1:]
    market = "zh" if "--market" not in args else args[args.index("--market")+1]
    scrub = "--scrub" in args
    text = sys.stdin.read()
    wm = {c: text.count(c) for c in set(WATERMARK) if c in text}
    if scrub:
        for c in wm: text = text.replace(c, "")
        sys.stdout.write(text)
    err = sys.stderr
    err.write(f"词数(CJK感知): {wc(text)}\n")
    sents = sentences(text, market)
    if len(sents) >= 5:
        lens = [wc(s) for s in sents]
        mean = sum(lens)/len(lens)
        var = sum((l-mean)**2 for l in lens)/len(lens)
        sd = var**0.5
        err.write(f"句数 {len(sents)} 句长均值 {mean:.1f} 标准差 {sd:.1f}\n")
        if sd < 0.25*mean: err.write("⚠ metronomic:句长过于均匀(AI 节奏签名,人类写作节奏剧变)\n")
        long_ratio = sum(1 for l in lens if l > 37.5)/len(lens)
        if long_ratio > 0.2: err.write(f"⚠ {long_ratio:.0%} 句子超 37.5 词(超 25 词上限的 1.5 倍)\n")
    emd = text.count("—") + text.count("–")
    if emd >= 3: err.write(f"⚠ em/en-dash {emd} 次(一篇一次是风格,三次是签名)\n")
    zh_hits = [w for w in ZH_SLOP if w in text]
    en_hits = [w for w in EN_SLOP if re.search(re.escape(w), text, re.I)]
    if zh_hits: err.write(f"⚠ 中文营销词 {len(zh_hits)} 个(>3/页→换具体事实): {zh_hits}\n")
    if en_hits: err.write(f"⚠ 英文 slop 词 {len(en_hits)} 个: {en_hits}\n")
    for v in VAGUE_CLAIMS:
        if v in text.lower(): err.write(f"⚠ 无指涉声明: {v}——换可验证事实\n"); break
    if wm: err.write(f"⚠ Unicode 水印字符: { {'U+%04X'%ord(c):n for c,n in wm.items()} }{'(已清除)' if scrub else '(--scrub 清除)'}\n")
    q = sum(1 for s in sents if s.endswith(("?", "?")))
    err.write(f"问句数: {q}\n")

if __name__ == "__main__": main()
