#!/usr/bin/env python3
"""多语言市场 lint 核心(stdlib,规则读 markets.json——18 市场数据与逻辑分离)。
① title/desc 长度按市场单位(chars|fullwidth|grapheme;ja/ko 全角、th 字素)判超限;
② 句长按 sentence_ideal(分句:zh/ja 。!?;th 换行;其余 .!?);
③ 营销词命中 >3 警告;④ 格式:fr :;!? 前须 U+202F/U+00A0、de 1.000,00 逆序、
阿文占比>30% → 裸 LTR 标点 + dir=rtl 提示;⑤ 称谓:de du/dich×B2B→Sie、
ja ですます×だ/である 混用、ko 합니다×해요 混用;⑥ zh 简繁混检(繁体>5%)。
用法: python3 market_lint.py --market ja FILE [--url URL]
FILE=HTML(<title>+meta description)或纯文本(title:/desc: 前缀行,其余正文;无前缀则第 1 行 title、第 2 行 desc)。
超限即 CRITICAL,退出码 1。"""
import sys, os, re, json, math, unicodedata, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (compatible; seo-suite-marketlint/1.0)"
# 常用繁体专用字(均有异体简体字形;简繁同形字不列)——zh 简繁混检用
HANT = set("們來對時開間問聞門書學長樂車馬鳥龍風雲電話語體頭條動務醫錢銀導業圓圖絲億憶邊變辯佈參殘層廠塵陳襯稱誠遲衝處觸傳純辭從達帶貸單擔膽彈當黨燈敵遞點墊澱釣調疊訂棟凍鬥獨隊噸奪墮鵝額惡兒爾餌發罰閥釩煩飯範訪紡廢費墳奮憤豐馮縫諷鳳膚撫輔賦婦該蓋幹趕鋼鴿閣給貢構購夠顧關觀慣廣歸龜規櫃貴滾鍋國過駭漢號鶴賀轟紅後壺護華劃畫話懷壞歡環還緩換喚煥揮輝匯會諱誨繪渾餛幾機積譏緝躋劑濟計記紀際繼薊劍薦艦濺漸諫將漿蔣槳獎講醬膠澆驕嬌攪鉸矯餃繳絞轎較階節潔結誡屆緊謹錦進晉燼經莖驚鯨蘇釋飾試勢適視親請慶瓊窮趨麗議羅顏雜讚髒鑿棗責滯築鑄狀錐諮資濁總縱鄒誣內區嘆灣選遷韓顆攏糧療齡靈領陸爐錄慮倫論賣邁滿貓夢個這戶級幫東見產網訊頻連認識驗擇確頁線壓腦續統質價標說讀寫習誤聽維營銷優帳數據庫讓為於麼裡沒準難雙愛願險錯團")

def load_rules(market):
    with open(os.path.join(BASE, "markets.json"), encoding="utf-8") as f:
        data = json.load(f)
    ms = data["markets"]
    if market not in ms:
        sys.exit("未知市场 %s;可用: %s" % (market, ", ".join(ms)))
    return ms[market]

def unit_len(s, unit):
    if unit == "fullwidth":  # EAW W/F=1,A 与半角=0.5,向上取整
        return math.ceil(sum(1.0 if unicodedata.east_asian_width(c) in ("W", "F") else 0.5 for c in s))
    if unit == "grapheme":   # 泰文字素:非组合且非 Mn/Cf 的码点
        return sum(1 for c in s if unicodedata.combining(c) == 0 and unicodedata.category(c) not in ("Mn", "Cf"))
    return len(s)

def parse_src(text):
    if re.search(r"<(title|meta|body|html)\b", text, re.I):
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
        title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        d = (re.search(r"<meta[^>]+name=[\"']description[\"'][^>]*content=[\"']([^\"']*)[\"']", text, re.I)
             or re.search(r"<meta[^>]+content=[\"']([^\"']*)[\"'][^>]*name=[\"']description[\"']", text, re.I))
        desc = re.sub(r"\s+", " ", d.group(1)).strip() if d else ""
        body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S | re.I)
        body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
        return title, desc, body
    title, desc, lines = "", "", []
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        mt = re.match(r"(?i)^title\s*[:：]\s*(.*)$", s)
        md = re.match(r"(?i)^(?:desc|description)\s*[:：]\s*(.*)$", s)
        if mt:
            title = mt.group(1)
        elif md:
            desc = md.group(1)
        else:
            lines.append(s)
    if not title and lines:
        title = lines.pop(0)
    if not desc and lines:
        desc = lines.pop(0)
    return title, desc, " ".join(lines)

def split_sents(body, rule):
    if rule == "newline":   # 泰文句号罕见,按换行
        parts = body.splitlines()
    elif rule == "cjk":     # zh/ja
        parts = re.split(r"[。!?!?]+", body)
    else:
        parts = re.split(r"[.!?]+", body)
    return [p.strip() for p in parts if p.strip()]

def main():
    args = sys.argv[1:]
    if "--market" not in args:
        sys.exit(__doc__)
    market = args[args.index("--market") + 1]
    url = args[args.index("--url") + 1] if "--url" in args else None
    path = next((a for a in args if not a.startswith("--") and a not in (market, url)), None)
    cfg = load_rules(market)
    if url:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        text = urllib.request.urlopen(req, timeout=15).read(2_000_000).decode("utf-8", "replace")
    elif path and path != "-":
        text = open(path, encoding="utf-8").read()
    else:
        text = sys.stdin.read()
    title, desc, body = parse_src(text)
    crit = warn = 0

    def crit_out(msg):
        nonlocal crit
        print("[CRITICAL] " + msg); crit += 1

    def warn_out(msg):
        nonlocal warn
        print("[WARN] " + msg); warn += 1

    # ① 长度限(单位按市场)
    for name, val, lim in (("title", title, cfg["title_limit"]), ("desc", desc, cfg["desc_limit"])):
        unit = lim["unit"]
        n = unit_len(val, unit)
        tag = "%s %d/%d %s(%s)" % (name, n, lim["value"], unit, len(val))
        if n > lim["value"]:
            crit_out("%s 超限,超出 %d" % (tag, n - lim["value"]))
        elif lim.get("ideal_min") and n < lim["ideal_min"]:
            print("[INFO] %s 低于理想下限 %d(浪费)" % (tag, lim["ideal_min"]))
        else:
            print("✓ " + tag)
        if lim.get("note"):
            print("    note: " + lim["note"])
    tl, dl = cfg["title_limit"], cfg["desc_limit"]
    if market == "vi" and tl.get("keyword_first_chars") and title:
        print("[INFO] t0mmy 规则:标题词须进前 %d 字符——当前: 「%s」" % (tl["keyword_first_chars"], title[:tl["keyword_first_chars"]]))
    if market == "id" and dl.get("safe_zone") and desc:
        print("[INFO] id meta 前 %d 字符安全区(截断风险): 「%s」" % (dl["safe_zone"], desc[:dl["safe_zone"]]))

    # ② 句长
    ideal = cfg["sentence_ideal"]
    sents = split_sents(body, cfg.get("sentence_split", "latin"))
    su = ideal.get("unit", "words")
    lens = [len(s) if su == "chars" else len(s.split()) for s in sents]
    if lens:
        over = [(s, l) for s, l in zip(sents, lens) if l > ideal["max"]]
        unit_cn = "字" if su == "chars" else "词"
        if over:
            warn_out("句长超市场上限 %d%s:%d/%d 句;最长 %d%s" % (ideal["max"], unit_cn, len(over), len(lens), max(l for _, l in over), unit_cn))
            for s, l in sorted(over, key=lambda x: -x[1])[:3]:
                print("    [%d] %s%s" % (l, s[:40], "…" if len(s) > 40 else ""))
        else:
            print("✓ 句长 %d 句,均值 %.1f(理想 %d-%d%s)" % (len(sents), sum(lens) / len(lens), ideal["min"], ideal["max"], unit_cn))
    if market == "th":
        print("[INFO] 泰文无词间空格:句长按空格短语近似,精确分词须 Intl.Segmenter('th')")

    # ③ 营销词(命中>3 警告)
    mw = cfg.get("marketing_words", [])
    folded = (" ".join([body, title, desc])).casefold()
    hits = []
    for w in mw:
        c = folded.count(w.casefold())
        hits.extend([w] * c)
    if len(hits) > 3:
        warn_out("营销词命中 %d 处(>3/页上限,换具体事实): %s" % (len(hits), sorted(set(hits))))
    elif hits:
        print("✓ 营销词 %d/3: %s" % (len(hits), sorted(set(hits))))

    # ④ 格式
    alltext = " ".join([title, desc, body])
    if market == "fr":
        bad = [alltext[max(0, i - 6):i + 2] for i, c in enumerate(alltext)
               if c in ":;!?" and (i == 0 or alltext[i - 1] not in "\u202f\u00a0")]
        if bad:
            warn_out("法语 :;!? 前缺窄/不换行空格(U+202F/U+00A0)%d 处: %s" % (len(bad), " | ".join(repr(b) for b in bad[:5])))
        elif any(c in alltext for c in ":;!?"):
            print("✓ 法语 :;!? 前窄/不换行空格齐全")
    if market == "de":
        eng = re.findall(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", alltext)
        ger = re.findall(r"\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?", alltext)
        if eng:
            warn_out("德式数字逆序(英式 %s → 应为 1.000,00 千分点+逗号小数)" % eng[:5])
        elif ger:
            print("✓ 德式数字 %s" % ger[:3])
    letters = [c for c in body if unicodedata.category(c)[0] == "L"]
    ar_ratio = (sum(1 for c in letters if "\u0600" <= c <= "\u06FF") / len(letters)) if letters else 0
    if ar_ratio > 0.3:
        print("✓ 检测阿文文本(占比 %.0f%%)——全链 RTL:dir=\"rtl\"+逻辑 CSS+镜像布局" % (ar_ratio * 100))
        bare = re.findall(r"[\u0600-\u06FF][()\[\]{}]|[()\[\]{}][\u0600-\u06FF]", body)
        if bare:
            warn_out("阿文语境裸 LTR 标点(方向问题)%d 处——用 U+2066 LRI/U+2067 RLI 隔离: %s" % (len(bare), bare[:3]))
        if market != "ar":
            warn_out("市场 %s 的正文是阿文——疑似语言/市场错配" % market)

    # ⑤ 称谓/语域
    if market == "de":
        du = len(re.findall(r"\b[Dd]u\b|\b[Dd]ich\b|\b[Dd]ir\b|\b[Dd]ein\w*\b", alltext))
        sie = len(re.findall(r"\bSie\b|\bIhnen\b|\bIhr\w*\b", alltext))
        b2b = re.search(r"\bB2B\b|[Gg]eschäftskunden|[Ff]irmenkunden|[Uu]nternehmen|gewerblich", alltext)
        if du and b2b:
            warn_out("德语 B2B 文案用 du 称谓(%d 处)——DACH B2B 默认 Sie" % du)
        elif du and sie:
            warn_out("Sie(%d)/du(%d) 混用——Ansprache 全站一致" % (sie, du))
        elif sie and not du:
            print("✓ Sie 称谓一致(%d 处)" % sie)
    if market == "ja":
        polite = re.search(r"です|ます", alltext)
        plain = re.search(r"である|[ぁ-ん]だ[。、!?!?]|[^だ]だ。", alltext)
        if polite and plain:
            warn_out("です/ます 与 だ/である 体混用——全站统一(学术栏可用である体)")
        elif polite:
            print("✓ です/ます 体一致")
    if market == "ko":
        hae = re.findall(r"[아야어여]요[\s.!?]|해요|예요|이에요", alltext)
        ham = re.findall(r"습니다|ㅂ니다|입니다", alltext)
        if hae and ham:
            warn_out("해요체(%d)与 합니다体(%d)混用——敬语体系统一" % (len(hae), len(ham)))
        elif ham:
            print("✓ 합니다体一致(%d 处)" % len(ham))

    # ⑥ zh 简繁混检
    if market == "zh":
        han = [c for c in body if "\u4e00" <= c <= "\u9fff"]
        hant = [c for c in han if c in HANT]
        if han:
            r = len(hant) / len(han)
            if 0.05 < r < 0.35:
                warn_out("简繁混用:繁体字 %d/%d(%.0f%%>5%%)——zh-Hans 页统一简体" % (len(hant), len(han), r * 100))
            elif r >= 0.35:
                print("[INFO] 繁体占比 %.0f%%——确认目标 locale 为 zh-Hant(配 zh-Hant hreflang)或统一为简体" % (r * 100))
            else:
                print("✓ 简体一致")

    # 支柱页长度(体裁提示)
    pm, pu = cfg.get("pillar_min"), cfg.get("pillar_unit", "words")
    if pm and body:
        n = len(body) if pu == "chars" else len(body.split())
        if n < pm:
            note = ";%s" % cfg["pillar_note"] if cfg.get("pillar_note") else ""
            print("[INFO] 正文 %d %s < 支柱建议 %d %s%s" % (n, pu, pm, pu, note))

    print("\n市场 %s:CRITICAL %d / WARN %d" % (market, crit, warn))
    print("引擎必查: %s" % ", ".join(cfg["engines"]))
    print("实体源候选: %s" % ", ".join(cfg["entity_sources"][:5]))
    sys.exit(1 if crit else 0)

if __name__ == "__main__":
    main()
