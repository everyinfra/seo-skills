#!/usr/bin/env python3
"""本地格式校验(stdlib,市场惯例读 markets.json)。用法:
  python3 local_format.py --market de "采样文本"   (文本也可走 stdin)
de: 数字 1.234,56 ✓ / 1,234.56 ✗(英式逆序);
fr: :;!? 前须窄/不换行空格 U+202F 或 U+00A0;
ar: ٠-٩ 阿拉伯-印度数字与 0-9 混用检测(统一即可,混用 ✗)+ dir=rtl 提示;
zh: 日期 2026年10月9日 ✓ / 10/9/2026 ✗;
通用: 电话 +7/+82/+86… 前缀按 markets.json formats.phone_prefix 对照(错配仅提示 ⚠)。
输出逐条 ✓/✗,有 ✗ 退出码 1。"""
import sys, os, re, json, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))

def main():
    args = sys.argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(__doc__.strip())
        return
    if "--market" not in args:
        sys.stderr.write(__doc__.strip() + "\n")
        sys.exit(2)
    market = args[args.index("--market") + 1]
    pos = [a for a in args if not a.startswith("--") and a != market]
    text = " ".join(pos) if pos else sys.stdin.read()
    with open(os.path.join(BASE, "markets.json"), encoding="utf-8") as f:
        data = json.load(f)
    cfg = data["markets"].get(market)
    if not cfg:
        sys.exit("未知市场 %s;可用: %s" % (market, ", ".join(data["markets"])))
    res = []  # (True✓/False✗/None⚠, msg)

    if market == "de":
        eng = re.findall(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", text)
        ger = re.findall(r"\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?", text)
        for n in eng:
            res.append((False, "数字 %s 是英式千分位——德式应为 1.000,00(千分点+逗号小数)" % n))
        for n in ger:
            res.append((True, "数字 %s 符合德式 1.000,00" % n))
        if not eng and not ger:
            res.append((True, "未检出千分位数字(无从校验)"))

    if market == "fr":
        found = False
        for i, c in enumerate(text):
            if c in ":;!?":
                found = True
                prev = text[i - 1] if i else ""
                ctx = text[max(0, i - 8):i + 2]
                if prev not in ("\u202f", "\u00a0"):
                    res.append((False, "「%s」的 %s 前缺窄/不换行空格(U+202F 或 U+00A0)" % (ctx, c)))
                else:
                    res.append((True, "「%s」前有空格(%s)" % (c, "U+202F 窄不换行" if prev == "\u202f" else "U+00A0 不换行")))
        if not found:
            res.append((True, "未出现 :;!?(无从校验)"))

    if market == "ar":
        east = sum(1 for c in text if "\u0660" <= c <= "\u0669")
        west = len(re.findall(r"[0-9]", text))
        if east and west:
            res.append((False, "数字混用:阿拉伯-印度 ٠-٩ ×%d 与欧洲 0-9 ×%d——全页统一其一" % (east, west)))
        elif east:
            res.append((True, "阿拉伯-印度数字 ×%d 统一" % east))
        elif west:
            res.append((True, "欧洲数字 ×%d 统一(可接受;传统/金融排版可用 ٠-٩)" % west))
        letters = [c for c in text if unicodedata.category(c)[0] == "L"]
        if letters and sum(1 for c in letters if "\u0600" <= c <= "\u06ff") / len(letters) > 0.3:
            res.append((True, "检测阿文 → 全链 RTL:dir=\"rtl\"+逻辑 CSS+双向文本"))

    if market == "zh":
        ymd = re.findall(r"\d{4}年\d{1,2}月\d{1,2}日", text)
        slash = re.findall(r"(?<![\d/])\d{1,2}/\d{1,2}/\d{2,4}(?![\d/])", text)
        iso = re.findall(r"\d{4}-\d{2}-\d{2}", text)
        for d in ymd:
            res.append((True, "日期 %s 符合中文格式" % d))
        for d in slash:
            res.append((False, "日期 %s 是斜杠式——中文用 2026年10月9日" % d))
        for d in iso:
            res.append((True, "日期 %s ISO 8601(可接受;面向用户建议年月日)" % d))
        if not (ymd or slash or iso):
            res.append((True, "未检出日期(无从校验)"))

    exp = (cfg.get("formats") or {}).get("phone_prefix")
    for p in re.findall(r"\+\d{1,3}[\s-]?\d{2,4}", text):
        code = "+" + re.match(r"\+(\d{1,3})", p).group(1)
        if exp and code != exp:
            res.append((None, "电话 %s 前缀 %s ≠ 市场惯例 %s——确认是否跨境号码" % (p, code, exp)))
        elif exp:
            res.append((True, "电话 %s 前缀符合 %s" % (p, exp)))

    fail = sum(1 for ok, _ in res if ok is False)
    for ok, msg in res:
        print(("%s " % ("✓" if ok is True else "✗" if ok is False else "⚠")) + msg)
    if not res:
        print("✓ 市场 %s 无专用格式规则命中(markets.json formats:%s)" % (market, cfg.get("formats")))
    print("\n%s:%d ✓ / %d ✗" % (market, sum(1 for ok, _ in res if ok is True), fail))
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
