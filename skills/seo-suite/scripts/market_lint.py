#!/usr/bin/env python3
"""多语言市场 lint v2(stdlib,规则读 markets.json——18 市场数据与逻辑分离)。
v1 保留:① title/desc 长度按市场单位(chars|fullwidth|grapheme;ja/ko 全角、th 字素);
② 句长按 sentence_ideal;③ 营销词>3 警告;④ fr :;!? 前窄空格/de 数字逆序;
⑤ de Sie/du、ja ですます、ko 합니다体;⑥ zh 简繁混检。
v2 新增:
⑦ special_checks 动态机检——逐市场读 markets.json 的 special_checks 数组,按语义归类映射到
  机检规则真实执行(ar RTL/dir+双向隔离+阿印数字、ja 正文300全角/AI臭指纹/全角英数字/nosnippet/
  换算通胀、ru 法定透明层、de Impressum、tr İ/i、vi 有调无调+句长方差、hi 天城文罗马化+lakh分组、
  th ครับ/ค่ะ、es ¿H2/es-419),不可机检项以 [MANUAL] 前缀输出人工清单;
⑧ 常开机检(不在 special_checks 但按市场语义应检):ru 西里尔占比+拉丁混排、ko 과/와 助词搭配。
--report:输出该市场全部 special_checks 的 [AUTO-OK]/[AUTO-FAIL]/[MANUAL] 三态清单。
用法: python3 market_lint.py --market ja FILE [--url URL] [--report]
FILE=HTML(<title>+meta description)或纯文本(title:/desc: 前缀行,其余正文;无前缀则第 1 行 title、第 2 行 desc)。
超限即 CRITICAL,退出码 1。"""
import sys, os, re, json, math, unicodedata, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (compatible; seo-suite-marketlint/2.0)"
# 常用繁体专用字(均有异体简体字形;简繁同形字不列)——zh 简繁混检用
HANT = set("們來對時開間問聞門書學長樂車馬鳥龍風雲電話語體頭條動務醫錢銀導業圓圖絲億憶邊變辯佈參殘層廠塵陳襯稱誠遲衝處觸傳純辭從達帶貸單擔膽彈當黨燈敵遞點墊澱釣調疊訂棟凍鬥獨隊噸奪墮鵝額惡兒爾餌發罰閥釩煩飯範訪紡廢費墳奮憤豐馮縫諷鳳膚撫輔賦婦該蓋幹趕鋼鴿閣給貢構購夠顧關觀慣廣歸龜規櫃貴滾鍋國過駭漢號鶴賀轟紅後壺護華劃畫話懷壞歡環還緩換喚煥揮輝匯會諱誨繪渾餛幾機積譏緝躋劑濟計記紀際繼薊劍薦艦濺漸諫將漿蔣槳獎講醬膠澆驕嬌攪鉸矯餃繳絞轎較階節潔結誡屆緊謹錦進晉燼經莖驚鯨蘇釋飾試勢適視親請慶瓊窮趨麗議羅顏雜讚髒鑿棗責滯築鑄狀錐諮資濁總縱鄒誣內區嘆灣選遷韓顆攏糧療齡靈領陸爐錄慮倫論賣邁滿貓夢個這戶級幫東見產網訊頻連認識驗擇確頁線壓腦續統質價標說讀寫習誤聽維營銷優帳數據庫讓為於麼裡沒準難雙愛願險錯團")
# ja「AI 臭」指纹词(固定字符串表——命中即标)
JA_FP = ["種明かしをすると", "と言っても過言ではありません", "の秘密に迫り", "欠かせない存在",
         "について徹底解説", "まとめると", "簡単に言うと", "最近よく聞く"]
# vi 无调形(正字必有调,正文出现 ASCII 形=有调/无调并存)
VI_UNACC = {"va", "cua", "khong", "duoc", "nguoi", "nhung", "voi", "nay", "tai", "neu",
            "nhieu", "hon", "quoc", "khach", "dich", "dong", "tuyen", "phong", "duong", "den"}
VI_ACC = set("àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ")
# ru 商业页法定透明层 6 类(HTML 内链文本/锚点匹配)
RU_LEGAL = ["оферта", "реквизит", "пользовательское соглашение", "политика конфиденциальности", "контакт", "возврат"]

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
    is_html = bool(re.search(r"<(title|meta|body|html)\b", text, re.I))
    if is_html:
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
        title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        d = (re.search(r"<meta[^>]+name=[\"']description[\"'][^>]*content=[\"']([^\"']*)[\"']", text, re.I)
             or re.search(r"<meta[^>]+content=[\"']([^\"']*)[\"'][^>]*name=[\"']description[\"']", text, re.I))
        desc = re.sub(r"\s+", " ", d.group(1)).strip() if d else ""
        body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S | re.I)
        body = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
        return title, desc, body, True, text
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
    return title, desc, " ".join(lines), False, None

def split_sents(body, rule):
    if rule == "newline":   # 泰文句号罕见,按换行
        parts = body.splitlines()
    elif rule == "cjk":     # zh/ja
        parts = re.split(r"[。!?!?]+", body)
    else:
        parts = re.split(r"[.!?]+", body)
    return [p.strip() for p in parts if p.strip()]

def hreflangs(raw):
    return re.findall(r"""hreflang\s*=\s*["']([^"']+)["']""", raw, re.I) if raw else []

# ---------- special_checks → 机检规则(语义归类)----------
# 每条:(rule_id, market, 匹配 special_checks 文本的 regex);执行体在 RUNNERS。
# 归类要求:同一 market 内各 regex 互斥(一条 special_check 至多命中一条规则)。
AUTO_RULES = [
    ("zh_script_mix", "zh", r"简繁"),
    ("marketing_cap", "zh", r"营销词"),
    ("ja_len", "ja", r"全角阈值"),
    ("ja_keigo", "ja", r"です/ます"),
    ("ja_ai", "ja", r"AI 臭"),
    ("ja_nosnippet", "ja", r"nosnippet"),
    ("ja_fwalnum", "ja", r"全角英数字"),
    ("ja_conv", "ja", r"换算通胀"),
    ("ar_rtl", "ar", r"RTL 方向位"),
    ("ar_bidi", "ar", r"裸 LTR"),
    ("ar_digits", "ar", r"阿-印数字"),
    ("ru_legal", "ru", r"法定透明层"),
    ("de_ansprache", "de", r"Ansprache|Sie/du"),
    ("de_impressum", "de", r"Impressum"),
    ("fr_nbsp", "fr", r"U\+202F"),
    ("tr_dotted_i", "tr", r"İ/i"),
    ("vi_tones", "vi", r"有调/无调"),
    ("vi_variance", "vi", r"句长方差"),
    ("hi_mix", "hi", r"Hinglish"),
    ("hi_num", "hi", r"lakh/crore"),
    ("th_polite", "th", r"ครับ"),
    ("th_grapheme", "th", r"字素计数"),
    ("es_h2q", "es", r"倒问号"),
    ("es_419", "es", r"唯一 UN 区域码"),
]
# 已由 ①-⑥ 核心段诊断并计数的规则(⑦ 正常模式只补清单行,不重复计 WARN)
COVERED = {"zh_script_mix", "marketing_cap", "ja_keigo", "fr_nbsp", "de_ansprache"}

def classify(market, sc):
    for rid, mkt, pat in AUTO_RULES:
        if mkt == market and re.search(pat, sc):
            return rid
    return None

def r_zh_script(ctx):
    body, raw, is_html = ctx["body"], ctx["raw"], ctx["is_html"]
    han = [c for c in body if "\u4e00" <= c <= "\u9fff"]
    issues, notes = [], []
    if han:
        r = sum(1 for c in han if c in HANT) / len(han)
        if 0.05 < r < 0.35:
            issues.append("简繁混用(繁体 %d/%d,%.0f%%>5%%)" % (sum(1 for c in han if c in HANT), len(han), r * 100))
        elif r >= 0.35:
            notes.append("繁体占比 %.0f%%——确认 zh-Hant locale" % (r * 100))
        else:
            notes.append("简体一致")
    elif body:
        issues.append("正文无汉字(疑似语言/市场错配)")
    if is_html:
        vals = hreflangs(raw)
        bad = sorted({v for v in vals if re.fullmatch(r"(?i)zh-(CN|TW|HK|SG|MO)", v)})
        zhv = sorted({v for v in vals if v.lower().startswith("zh-")})
        if bad:
            issues.append("hreflang 裸区域码 %s——应用 zh-Hans/zh-Hant 文字码" % bad)
        elif zhv:
            notes.append("hreflang %s" % zhv)
        else:
            notes.append("未见 zh* hreflang(站点级核验)")
    else:
        notes.append("hreflang 需 HTML 输入")
    return ("FAIL" if issues else "OK"), ";".join(issues or notes)

def r_marketing(ctx):
    n = ctx.get("mw_hits", 0)
    return ("OK" if n <= 3 else "FAIL"), "营销词命中 %d/3(>3 换具体事实)" % n

def r_ja_len(ctx):
    cfg, t, d, b = ctx["cfg"], ctx["title"], ctx["desc"], ctx["body"]
    tl, dl = cfg["title_limit"]["value"], cfg["desc_limit"]["value"]
    tn, dn, bn = unit_len(t, "fullwidth"), unit_len(d, "fullwidth"), unit_len(b, "fullwidth")
    issues = []
    if tn > tl:
        issues.append("title %d/%d 全角" % (tn, tl))
    if dn > dl:
        issues.append("desc %d/%d 全角" % (dn, dl))
    if bn < 300:
        issues.append("正文 %d/300 全角(薄页)" % bn)
    return ("FAIL" if issues else "OK"), "title %d/%d,desc %d/%d,正文 %d/300 全角(visible_length 口径)" % (tn, tl, dn, dl, bn)

def r_ja_keigo(ctx):
    a = ctx["alltext"]
    polite = re.search(r"です|ます", a)
    plain = re.search(r"である|[ぁ-ん]だ[。、!?!?]|[^だ]だ。", a)
    if polite and plain:
        return "FAIL", "です/ます 与 だ/である 体混用——全站统一(学术栏可用である体)"
    if plain:
        return "FAIL", "常体(だ/である)——营销页应ですます体(学术栏除外)"
    return ("OK" if polite else "OK"), "です/ます 体一致" if polite else "未见敬体标记"

def r_ja_ai(ctx):
    a = ctx["alltext"]
    contrast = re.findall(r"[一-龯ぁ-んァ-ヶa-zA-Z0-9]{1,10}ではなく", a)
    fp = [w for w in JA_FP if w in a]
    if len(contrast) > 3 or fp:
        return "FAIL", "AI 臭:对比构文「AではなくB」%d 处(≤3)%s" % (len(contrast), (";指纹词 " + "/".join(fp)) if fp else "")
    return "OK", "对比构文 %d/3,指纹词 0" % len(contrast)

def r_ja_nosnippet(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入"
    raw = ctx["raw"]
    m = (re.search(r"""<meta[^>]+name=["']robots["'][^>]+content=["']([^"']*)["']""", raw, re.I)
         or re.search(r"""<meta[^>]+content=["']([^"']*)["'][^>]+name=["']robots["']""", raw, re.I))
    if (m and "nosnippet" in m.group(1).lower()) or re.search(r"""name=["']nosnippet["']""", raw, re.I):
        return "FAIL", "nosnippet 在场——该页内容将退出 AIO/AI Mode 输入(要进 AI 的页勿设)"
    return "OK", "robots meta 未见 nosnippet"

def r_ja_fwalnum(ctx):
    a, raw, is_html = ctx["alltext"], ctx["raw"], ctx["is_html"]
    issues, notes = [], []
    fw = re.findall(r"[０-９Ａ-Ｚａ-ｚ]+", a)
    if fw and re.search(r"[0-9A-Za-z]", a):
        issues.append("全角英数字混在 %d 处: %s——统一半角" % (len(fw), fw[:3]))
    elif fw:
        notes.append("全角英数字 %d 处(无半角对照,仍建议半角)" % len(fw))
    if is_html:
        if not re.search(r"<html[^>]*\blang\s*=", raw, re.I):
            issues.append("<html> 缺 lang 声明")
        if not re.search(r"charset\s*=", raw, re.I):
            issues.append("缺 charset 声明")
    else:
        notes.append("charset/lang 需 HTML 输入")
    return ("FAIL" if issues else "OK"), ";".join(issues or notes) or "全角半角/声明正常"

def r_ja_conv(ctx):
    marks = re.findall(r"月額|年額|日額|月あたり|年あたり|日あたり", ctx["alltext"])
    if len(marks) > 2:
        return "FAIL", "换算通胀:月/年/日换算表述 %d 处(≤2): %s" % (len(marks), sorted(set(marks)))
    return "OK", "换算表述 %d/2" % len(marks)

def r_ar_rtl(ctx):
    ratio = ctx["ar_ratio"]
    if ratio <= 0.3:
        return "FAIL", "阿文占比 %.0f%%<30%%——语言/市场错配?" % (ratio * 100)
    if not ctx["is_html"]:
        return "MANUAL", "纯文本无 dir 属性可检(HTML 输入可机检);逻辑 CSS/镜像布局须人工核验"
    if re.search(r"""dir\s*=\s*["']rtl["']""", ctx["raw"], re.I):
        return "OK", 'dir="rtl" 在场(占比 %.0f%%);逻辑 CSS 属性+镜像布局人工核验' % (ratio * 100)
    return "FAIL", '阿文占比 %.0f%% 但未见 dir="rtl"——全链 RTL 缺方向位' % (ratio * 100)

def r_ar_bidi(ctx):
    body, a = ctx["body"], ctx["alltext"]
    bare = re.findall(r"[\u0600-\u06FF][()\[\]{}]|[()\[\]{}][\u0600-\u06FF]", body)
    iso = sum(a.count(c) for c in "\u2066\u2067")
    if bare:
        return "FAIL", "阿文语境裸 LTR 标点 %d 处(%s)——用 U+2066 LRI/U+2067 RLI 隔离" % (len(bare), bare[:3])
    return "OK", "裸标点 0;双向隔离符 %d 处" % iso

def r_ar_digits(ctx):
    body = ctx["body"]
    east = [c for c in body if c in "٠١٢٣٤٥٦٧٨٩"]
    west = [c for c in body if c in "0123456789"]
    if east and west:
        return "FAIL", "阿-印数字(٠-٩)与西文(0-9)并存——全页统一一套"
    if east:
        return "OK", "统一阿-印数字 ٠-٩"
    if west:
        return "OK", "统一西文数字 0-9(决策记录:未用阿-印)"
    return "OK", "无数字"

def r_ru_legal(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入(检 6 类法定页链接)"
    low = ctx["raw"].lower()
    missing = [c for c in RU_LEGAL if c not in low]
    if missing:
        return "FAIL", "法定透明层缺 %d/%d 类: %s(IndexLift 口径)" % (len(missing), len(RU_LEGAL), missing)
    return "OK", "6 类法定字段链接在场"

def r_de_ansprache(ctx):
    a = ctx["alltext"]
    du = re.findall(r"\b[Dd]u\b|\b[Dd]ich\b|\b[Dd]ir\b|\b[Dd]ein\w*\b", a)
    sie = re.findall(r"\bSie\b|\bIhnen\b|\bIhr\w*\b", a)
    b2b = re.search(r"\bB2B\b|[Gg]eschäftskunden|[Ff]irmenkunden|[Uu]nternehmen|gewerblich", a)
    if du and b2b:
        return "FAIL", "B2B 文案用 du 称谓 %d 处——DACH B2B 默认 Sie" % len(du)
    if du and sie:
        return "FAIL", "Sie(%d)/du(%d) 混用——Ansprache/Tonalität 两字段全站一致" % (len(sie), len(du))
    if sie:
        return "OK", "Sie 称谓一致(%d 处)" % len(sie)
    if du:
        return "OK", "du 称谓一致(%d 处;确认非 B2B 语境)" % len(du)
    return "OK", "未见称谓"

def r_de_impressum(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入(检 Impressum 链接)"
    if "impressum" in ctx["raw"].lower():
        return "OK", "Impressum(§5 DDG)法定页链接在场"
    return "FAIL", "未见 Impressum(§5 DDG)法定页链接"

def r_fr_nbsp(ctx):
    a = ctx["alltext"]
    bad = [a[max(0, i - 6):i + 2] for i, c in enumerate(a)
           if c in ":;!?" and (i == 0 or a[i - 1] not in "\u202f\u00a0")]
    if bad:
        return "FAIL", ":;!? 前缺 U+202F/U+00A0 %d 处: %s" % (len(bad), " | ".join(repr(b) for b in bad[:5]))
    if any(c in a for c in ":;!?"):
        return "OK", ":;!? 前窄/不换行空格齐全"
    return "OK", "未见 :;!?"

def r_tr_dotted_i(ctx):
    body = ctx["body"]
    susp = re.findall(r"\bI[a-zçğışöü]\w*", body)
    if susp:
        return "FAIL", "ASCII 大写 I+小写 %d 处: %s——土耳其语应为 İ(Istanbul→İstanbul)或 ı" % (len(susp), susp[:5])
    if "İ" in body or "ı" in body:
        return "OK", "İ/ı 码点正确;关键词 İ/i 双码点归组前先做 İ→i̇ 替换再 casefold"
    return "OK", "未见 İ/ı 与可疑 ASCII I——大写场景请人工复核"

def r_vi_tones(ctx):
    body = ctx["body"]
    if not body:
        return "MANUAL", "正文为空"
    low = body.lower()
    acc = sum(1 for c in low if c in VI_ACC)
    hits = sorted({t for t in re.findall(r"[a-z]+", low) if t in VI_UNACC})
    if acc == 0:
        return "FAIL", "无任何带调字符——疑似未本地化"
    if hits:
        return "FAIL", "无调形与有调文本并存 %d 种: %s——有调/无调双轨当独立词跟踪" % (len(hits), hits[:8])
    return "OK", "声调一致(无调形变体须另开 GSC 双轨跟踪)"

def r_vi_variance(ctx):
    sents = split_sents(ctx["body"], "latin")
    lens = [len(s.split()) for s in sents]
    if len(lens) < 5:
        return "MANUAL", "句数 %d<5,方差不可判" % len(lens)
    mean = sum(lens) / len(lens)
    sd = math.sqrt(sum((x - mean) ** 2 for x in lens) / len(lens))
    cv = sd / mean if mean else 0
    if cv < 0.25:
        return "FAIL", "句长变异系数 %.2f(<0.25)——句长过于均匀,AI 文风信号(mona-seo-check-vi 口径)" % cv
    return "OK", "句长 CV %.2f(均值 %.1f 词/句)" % (cv, mean)

def r_hi_mix(ctx):
    body, letters = ctx["body"], ctx["letters"]
    if not letters:
        return "MANUAL", "正文无字母"
    dev = sum(1 for c in letters if "\u0900" <= c <= "\u097F") / len(letters)
    latin_w = re.findall(r"[A-Za-z]{2,}", body)
    lr = len(latin_w) / max(len(body.split()), 1)
    if dev < 0.2:
        return "FAIL", "天城文占比 %.0f%% 过低——hi 页应以 Devanagari 为主(en-IN 分开评分)" % (dev * 100)
    if lr > 0.3:
        return "FAIL", "Devanagari %.0f%%+罗马化 %d 词(%.0f%%)混排——Hinglish 三写变体归组需 GSC regex" % (dev * 100, len(latin_w), lr * 100)
    return "OK", "天城文 %.0f%%;拉丁词 %d(品牌/术语容忍)" % (dev * 100, len(latin_w))

def r_hi_num(ctx):
    a = ctx["alltext"]
    indian = re.findall(r"\d{1,2},\d{2},\d{3}(?:\.\d+)?", a)
    western = re.findall(r"\d{1,3},\d{3},\d{3}(?:\.\d+)?", a)
    if western and not indian:
        return "FAIL", "西方分组 %s——lakh/crore 口径应为 1,23,456.78" % western[:3]
    if indian:
        return "OK", "lakh/crore 分组 %s" % indian[:3]
    return "OK", "未见大数分组"

def r_th_polite(ctx):
    body = ctx["body"]
    kr, kha = "ครับ" in body, "ค่ะ" in body
    if kr and kha:
        return "FAIL", "ครับ(男)/ค่ะ(女)礼貌尾词并存——性别不一致"
    if kr:
        return "OK", "ครับ 一致"
    if kha:
        return "OK", "ค่ะ 一致"
    return "OK", "未见礼貌尾词"

def r_th_grapheme(ctx):
    return "OK", "本工具 title/desc 计数已按字素口径(组合符号不计独立字符)"

def r_es_h2q(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入"
    h2s = [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<h2[^>]*>(.*?)</h2>", ctx["raw"], re.S | re.I)]
    qs = [h for h in h2s if "¿" in h]
    if not h2s:
        return "MANUAL", "无 H2 可判"
    if not qs:
        return "FAIL", "%d 个 H2 无一 ¿ 倒问号疑问式——至少 1 个信息需求型 H2" % len(h2s)
    return "OK", "¿ 疑问式 H2 %d/%d" % (len(qs), len(h2s))

def r_es_419(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入"
    vals = hreflangs(ctx["raw"])
    if "es-419" in vals:
        return "OK", "es-419 在场(唯一 UN 区域码)"
    es = sorted({v for v in vals if v.lower().startswith("es-")})
    if es:
        return "FAIL", "有 %s 而无 es-419" % es
    return "MANUAL", "未见 hreflang,须站点级核验"

RUNNERS = {
    "zh_script_mix": r_zh_script, "marketing_cap": r_marketing, "ja_len": r_ja_len,
    "ja_keigo": r_ja_keigo, "ja_ai": r_ja_ai, "ja_nosnippet": r_ja_nosnippet,
    "ja_fwalnum": r_ja_fwalnum, "ja_conv": r_ja_conv, "ar_rtl": r_ar_rtl,
    "ar_bidi": r_ar_bidi, "ar_digits": r_ar_digits, "ru_legal": r_ru_legal,
    "de_ansprache": r_de_ansprache, "de_impressum": r_de_impressum, "fr_nbsp": r_fr_nbsp,
    "tr_dotted_i": r_tr_dotted_i, "vi_tones": r_vi_tones, "vi_variance": r_vi_variance,
    "hi_mix": r_hi_mix, "hi_num": r_hi_num, "th_polite": r_th_polite,
    "th_grapheme": r_th_grapheme, "es_h2q": r_es_h2q, "es_419": r_es_419,
}

def main():
    args = sys.argv[1:]
    if "--market" not in args:
        sys.exit(__doc__)
    market = args[args.index("--market") + 1]
    url = args[args.index("--url") + 1] if "--url" in args else None
    report = "--report" in args
    path = next((a for a in args if not a.startswith("--") and a not in (market, url)), None)
    cfg = load_rules(market)
    if url:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        text = urllib.request.urlopen(req, timeout=15).read(2_000_000).decode("utf-8", "replace")
    elif path and path != "-":
        text = open(path, encoding="utf-8").read()
    else:
        text = sys.stdin.read()
    title, desc, body, is_html, raw = parse_src(text)
    letters = [c for c in body if unicodedata.category(c)[0] == "L"]
    ar_ratio = (sum(1 for c in letters if "\u0600" <= c <= "\u06FF") / len(letters)) if letters else 0
    alltext = " ".join([title, desc, body])
    ctx = {"market": market, "cfg": cfg, "title": title, "desc": desc, "body": body,
           "alltext": alltext, "is_html": is_html, "raw": raw, "letters": letters, "ar_ratio": ar_ratio}
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
    folded = alltext.casefold()
    hits = []
    for w in mw:
        c = folded.count(w.casefold())
        hits.extend([w] * c)
    ctx["mw_hits"] = len(hits)
    if len(hits) > 3:
        warn_out("营销词命中 %d 处(>3/页上限,换具体事实): %s" % (len(hits), sorted(set(hits))))
    elif hits:
        print("✓ 营销词 %d/3: %s" % (len(hits), sorted(set(hits))))

    # ④ 格式
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
    if ar_ratio > 0.3 and market != "ar":
        warn_out("市场 %s 的正文是阿文(占比 %.0f%%)——疑似语言/市场错配" % (market, ar_ratio * 100))

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

    # ⑥b 常开机检(不在 special_checks 文本内,按市场语义应检)
    if market == "ru" and len(letters) >= 20:
        cr = sum(1 for c in letters if "\u0400" <= c <= "\u04FF") / len(letters)
        latin_w = re.findall(r"[A-Za-z]{3,}", body)
        if cr >= 0.5:
            if len(latin_w) > 3:
                warn_out("俄语页拉丁混排 %d 词(西里尔 %.0f%%): %s——确认非必要借词/未翻译残留" % (len(latin_w), cr * 100, latin_w[:5]))
            else:
                print("✓ 西里尔 %.0f%%,拉丁混排 %d 词" % (cr * 100, len(latin_w)))
        elif cr >= 0.1:
            warn_out("西里尔占比 %.0f%% 偏低(拉丁 %.0f%%)——混排/语言错配核查" % (cr * 100, (1 - cr) * 100))
        else:
            warn_out("西里尔占比 %.0f%%——语言/市场错配?" % (cr * 100))
    if market == "ko" and body:
        viol = []
        for i, c in enumerate(body):
            if c in "과와" and i > 0 and 0xAC00 <= ord(body[i - 1]) <= 0xD7A3:
                nxt = body[i + 1] if i + 1 < len(body) else ""
                if not (0xAC00 <= ord(nxt) <= 0xD7A3 if nxt else False):  # 助词用法:后接非谚文(词中 과일/와인 跳过)
                    final = (ord(body[i - 1]) - 0xAC00) % 28  # 终声(받침)
                    want = "와" if final == 0 else "과"
                    if c != want:
                        viol.append(body[max(0, i - 4):i + 2])
        if viol:
            warn_out("과/와 助词搭配错误 %d 处(终声有无判 과/와): %s" % (len(viol), viol[:3]))
        elif "과" in body or "와" in body:
            print("✓ 과/와 助词搭配(收音+과/无收音+와)无误")

    # ⑦ special_checks 动态机检/人工清单(--report 输出三态)
    checks = cfg.get("special_checks", [])
    if checks:
        print("\n%s" % ("⑦ special_checks 三态清单(--report)" if report else "⑦ special_checks 机检 + 人工清单"))
        ok = fail = man = 0
        for sc in checks:
            rid = classify(market, sc)
            if not rid:
                man += 1
                print("[MANUAL] " + sc)
                continue
            state, detail = RUNNERS[rid](ctx)
            if state == "FAIL":
                fail += 1
                if rid not in COVERED:
                    warn += 1
                if report:
                    print("[AUTO-FAIL] %s —— %s" % (sc, detail))
                elif rid in COVERED:
                    print("[AUTO-FAIL] %s —— %s(与上方核心检查同源,不重复计数)" % (sc, detail))
                else:
                    print("[WARN] [AUTO] %s —— %s" % (sc, detail))
            elif state == "OK":
                ok += 1
                print("%s %s%s" % ("[AUTO-OK] " if report else "✓ [AUTO] ", sc, " —— " + detail if detail else ""))
            else:  # 规则降级 MANUAL(输入不满足机检前提)
                man += 1
                print("[MANUAL] %s —— %s" % (sc, detail))
        print("special_checks: AUTO-OK %d / AUTO-FAIL %d / MANUAL %d(共 %d)" % (ok, fail, man, len(checks)))

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
