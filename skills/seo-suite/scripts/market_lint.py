#!/usr/bin/env python3
"""多语言市场 lint v3(stdlib,规则读 markets.json——18 市场数据与逻辑分离)。
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
v3 新增(2026-10-09,检查函数注册表 24→64):
⑨ special_checks 第二批机检映射 +28 条(ko nosourceinfo/标签-值网格/연관채널、ja 星5つQR王道、
  en 段落级可引性四要素、es 词汇分流/支付词层、pt CNPJ/PIX骗局/软文披露、de Werbung 双披露、
  fr courriel 术语表、id 安全区/baku-gaul/EYD V、hi 语音助词、it it-CH/P.IVA/估算声明、
  tr tanıtım 披露、vi 标题词前30字符、th 佛历/词中截断、pl 变音/sierotki、nl je-u/INVULLEN/KvK);
⑩ v3 常开机检注册表 12 项(全市场):内容类(营销词密度/句长CV/FAQ问句密度/有源数字密度)、
  结构类(H2 疑问式占比/列表密度/标题关键词位次)、格式类(日期格式/电话前缀/货币符号)、
  语言类(ru 西里尔/ko 谚文/th 泰文字符占比)、robots 类(页面级 noai/noimageai/nosnippet)。
--report 尾部打印该市场 special_checks 的 AUTO 比例(AUTO-OK+AUTO-FAIL / 总数)。
用法: python3 market_lint.py --market ja FILE [--url URL] [--report]
FILE=HTML(<title>+meta description)或纯文本(title:/desc: 前缀行,其余正文;无前缀则第 1 行 title、第 2 行 desc)。
超限即 CRITICAL,退出码 1。"""
import sys, os, re, json, math, unicodedata, urllib.request
from collections import Counter

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
# ---------- v3 词表(⑨⑩ 用)----------
ID_GAUL = {"banget", "gak", "nggak", "santuy", "udah", "doang", "gimana", "kayaknya"}  # gaul 口语判别词
ID_EYD = [("resiko", "risiko"), ("azas", "asas"), ("ijin", "izin"), ("aktifitas", "aktivitas"),
          ("praktek", "praktik"), ("hipotesa", "hipotesis"), ("analisa", "analisis"),
          ("obyek", "objek"), ("atifisial", "artifisial")]  # EYD V 旧拼法→新拼法
PL_STRIPPED = ["mozliwosci", "bedzie", "wiecej", "stworzyc", "tlumaczyc", "piekny", "krolik", "zloty", "zlobek"]
PL_ORPHAN = r"(w|i|o|a|u|z|we|ze|do|na|po|za|od|albo|lub)\s*$"  # sierotki:行尾单双字母虚词
HI_VOICE = ["kaise", "konsa", "batao", "kahan", "kitna", "kyun"]  # 语音层罗马化助词
TH_MONTHS = "มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม"
SRC_CUES = ["据", "根据", "来源", "统计", "according to", "source:", "based on", "survey", "study",
            "によると", "による", "에 따르면", "según", "fuente", "selon", "laut", "secondo", "volgens"]  # 有源数字同句线索
H2_Q_RE = r"^(?:¿\s*|[?？]|什么|怎么|如何|为什么|哪|何以|何が|なぜ|why\b|how\b|what\b|which\b|wie\b|was\b|warum\b|wann\b|comment\b|pourquoi\b|quel\b|qué\b|cómo\b|cuál\b|apa\b|bagaimana\b|mengapa\b|neden\b|nasıl\b|jak\b|czym\b|co\b|wat\b|hoe\b|waarom\b|perché\b)"
DATE_STYLE = {"zh": "cjk", "ja": "cjk", "ko": "cjk", "de": "dot", "ru": "dot", "tr": "dot", "pl": "dot",
              "nl": "dash", "es": "slash", "pt": "slash", "fr": "slash", "it": "slash", "id": "slash",
              "vi": "slash", "en": "en", "hi": "name", "th": "be", "ar": "name"}
CUR_LOCAL = {"zh": ("¥", "￥", "元"), "ja": ("円", "￥"), "ko": ("원", "￦"), "de": ("€",), "fr": ("€",),
             "es": ("€",), "it": ("€",), "nl": ("€",), "pt": ("R$",), "en": ("$", "£"), "ru": ("₽",),
             "tr": ("₺",), "pl": ("zł",), "id": ("Rp",), "hi": ("₹",), "vi": ("đ",), "th": ("฿",),
             "ar": ("ر.س", "د.إ")}  # ar 多国:SAR/AED 均容忍
SCRIPT_RANGE = {"ru": ("\u0400", "\u04FF"), "ko": ("\uAC00", "\uD7A3"), "th": ("\u0E00", "\u0E7F")}  # v3 语言占比输出

def robots_meta_content(raw):
    """meta name=robots 的 content 值(name/content 两种属性顺序)。"""
    m = (re.search(r"""<meta[^>]+name=["']robots["'][^>]+content=["']([^"']*)["']""", raw, re.I)
         or re.search(r"""<meta[^>]+content=["']([^"']*)["'][^>]+name=["']robots["']""", raw, re.I))
    return m.group(1) if m else None

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
    # ---------- v3 第二批映射(2026-10-09):special_checks 中可机检项 ----------
    ("ko_nosourceinfo", "ko", r"nosourceinfo"),
    ("ko_grid", "ko", r"标签-值网格"),
    ("ko_channel", "ko", r"연관채널"),
    ("ja_qr", "ja", r"星5つ"),
    ("en_citability", "en", r"段落级可引性|四要素在场"),
    ("es_variant", "es", r"coche/carro|词汇分流"),
    ("es_payment", "es", r"OXXO|支付词"),
    ("pt_cnpj", "pt", r"CNPJ|执业凭证"),
    ("pt_payment", "pt", r"PIX/boleto"),
    ("pt_sponsored", "pt", r"publieditorial"),
    ("de_werbung", "de", r"软文 Werbung"),
    ("fr_terms", "fr", r"courriel"),
    ("id_safezone", "id", r"安全区"),
    ("id_baku", "id", r"baku/gaul"),
    ("id_eyd", "id", r"EYD"),
    ("hi_voice", "hi", r"语音层|助词词库"),
    ("it_ch", "it", r"it-CH 独立 locale"),
    ("it_piva", "it", r"P\.IVA"),
    ("it_estval", "it", r"测量值 vs 估算值|声明降级"),
    ("tr_tanitim", "tr", r"tanıtım"),
    ("vi_kw30", "vi", r"前 30 字符|防 AI 改写"),
    ("th_buddhist", "th", r"佛历年"),
    ("th_trunc", "th", r"词中截断"),
    ("pl_diacritics", "pl", r"变音字母"),
    ("pl_sierotki", "pl", r"sierotki|孤字"),
    ("nl_tone", "nl", r"je/u tone"),
    ("nl_placeholder", "nl", r"INVULLEN"),
    ("nl_kvk", "nl", r"KvK"),
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

# ---------- v3 runner:⑨ special_checks 第二批 ----------
def r_ko_nosourceinfo(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入"
    m = robots_meta_content(ctx["raw"])
    if (m and "nosourceinfo" in m.lower()) or re.search(r"""name=["']nosourceinfo["']""", ctx["raw"], re.I):
        return "FAIL", "nosourceinfo 在场——该页退出 Naver AI Briefing(全球唯一官方 AI 引用退出 meta;退出决策须显式记录)"
    return "OK", "未见 nosourceinfo——页面在 AI Briefing 引用池内(如需退出须显式决策记录)"

def r_ko_grid(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入(检 table/dl 标签-值网格)"
    raw = ctx["raw"]
    grids = len(re.findall(r"<(table|dl)\b", raw, re.I))
    links = len(re.findall(r"<a\b[^>]+href=[\"']https?://", raw, re.I))
    if grids == 0:
        return "FAIL", "无 table/dl 网格结构——AI Briefing 引用条件:标签-值网格>散文块"
    if links == 0:
        return "FAIL", "标签-值网格 %d 处但无外链——一手来源声明并链接原文缺失" % grids
    return "OK", "标签-值网格 %d 处+外链 %d(一手来源可链)" % (grids, links)

def r_ko_channel(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入(检 연관채널/sameAs)"
    raw_l = ctx["raw"].lower()
    sameas = "sameas" in raw_l
    domains = [d for d in ("blog.naver.com", "cafe.naver.com", "chzzk.naver.com", "daangn.com", "tistory.com", "brunch.co.kr") if d in raw_l]
    if sameas or domains:
        return "OK", "연관채널 线索:sameAs=%s,官方域 %s(치지직/당근 含官方域名清单口径)" % (sameas, domains[:3] or "无")
    return "FAIL", "未见 sameAs/官方域链接——연관채널 channel markup 缺失(Search Advisor 实体绑定断)"

def r_ja_qr(ctx):
    if re.search(r"星5つ|星５つ|5つ星|レビューをお願い", ctx["alltext"]):
        return "FAIL", "「星5つで」类评价指定话术在场——景表法 QR 王道违法(评价征集须中立提示)"
    return "OK", "未见星5つ指定话术"

def r_en_citability(ctx):
    body = ctx["body"]
    props = len(set(re.findall(r"\b[A-Z][a-z]{2,}\b", body)))          # 主体:专名密度
    nums = len(re.findall(r"\d[\d.,]*", body)) >= 3                      # 数字
    asof = bool(re.search(r"as of|as-of|updated|\b(19|20)\d{2}\b", body, re.I))  # as-of 日期
    method = bool(re.search(r"\bmethod(?:ology)?\b|\bsample\b|\bsurvey\b|N\s*=\s*\d|\bstudy\b|\bmeasured\b|\baccording to\b", body, re.I))
    hits = sum([props >= 3, nums, asof, method])
    if hits < 3:
        return "FAIL", "可引性四要素 %d/4(专名 %d/数字 %s/日期 %s/方法学 %s)——段落级自包含才可被引用" % (
            hits, props, nums, asof, method)
    return "OK", "四要素 %d/4 在场(专名 %d/数字 %s/日期 %s/方法学 %s)" % (hits, props, nums, asof, method)

def r_es_variant(ctx):
    a = ctx["alltext"].lower()
    es_es = len(re.findall(r"\bcoche?s?\b", a))
    latam = len(re.findall(r"\bcarro?s?\b|\bautos?\b", a))
    if es_es and latam:
        return "FAIL", "es-ES(coche %d)与 es-419(carro/auto %d)词汇混用——按变体组分流" % (es_es, latam)
    if es_es:
        return "OK", "es-ES 词汇(coche %d)——确认目标变体" % es_es
    if latam:
        return "OK", "es-419 词汇(carro/auto %d)" % latam
    return "OK", "未检出车辆类判别词(词汇分流失活,人工按品类核)"

def r_es_payment(ctx):
    a = ctx["alltext"].lower()
    hits = sorted({w for w in ("oxxo", "cuotas", "contra entrega", "efectivo", "transferencia", "envío gratis", "envio gratis") if w in a})
    if hits:
        return "OK", "支付词命中 %s——交易意图层标注(payment_intent.py 词表同源)" % hits
    if re.search(r"\$|€|precio|\bmxn\b|\bcop\b", a):
        return "FAIL", "有价格信号但无支付方式词(OXXO/cuotas/contra entrega)——支付即意图层缺失"
    return "OK", "无商业信号,支付词层失活(非交易页)"

def r_pt_cnpj(ctx):
    a = ctx["alltext"]
    cnpj = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", a)
    reg = re.search(r"OAB[/\s-]*\d+|CRM[/\s-]*\d+", a, re.I)
    if cnpj or reg:
        return "OK", "执业凭证在场(%s)——OAB/CRM 委员会号+CNPJ 信任层" % (cnpj.group(0) if cnpj else reg.group(0))
    if re.search(r"R\$|preço|comprar|advocacia|consult", a, re.I):
        return "FAIL", "商业信号在场但无 CNPJ/OAB/CRM 凭证字段——信任与合规缺口"
    return "MANUAL", "无商业信号可判(内容页凭证非必需)"

def r_pt_payment(ctx):
    a = ctx["alltext"].lower()
    pix, boleto = "pix" in a, "boleto" in a
    card = "cartão" in a or "cartao" in a
    if (pix or boleto) and not card:
        return "FAIL", "仅收 PIX/boleto 类无卡支付——骗局信号核查:披露完整支付矩阵(卡通道在场即破)"
    if pix or boleto or card:
        return "OK", "支付矩阵含卡通道(pix=%s/boleto=%s/cartão=%s)" % (pix, boleto, card)
    if re.search(r"r\$|comprar|loja", a):
        return "OK", "交易页未见支付词——支付披露层人工补核"
    return "OK", "非交易页"

def r_pt_sponsored(ctx):
    a = ctx["alltext"].lower()
    if not re.search(r"publieditorial|publicidade|patrocinad|publicitári", a):
        return "OK", "未见软文标记词(普通内容页)"
    if not ctx["is_html"]:
        return "MANUAL", "检出 publieditorial 词——rel=sponsored 披露须 HTML 机检"
    if re.search(r"""rel=["'][^"']*(sponsored|nofollow)[^"']*""", ctx["raw"], re.I):
        return "OK", "软文在场且链接带 rel=sponsored/nofollow 披露"
    return "FAIL", "publieditorial 在场但无 rel=sponsored 披露——CONAR+搜索引擎双重风险"

def r_de_werbung(ctx):
    a = ctx["alltext"].lower()
    if not re.search(r"\bwerbung\b|\banzeige\b|gesponsert", a):
        return "OK", "未见软文标记词"
    if not ctx["is_html"]:
        return "MANUAL", "检出 Werbung/gesponsert——标签与 rel 须 HTML 机检"
    raw = ctx["raw"]
    lab = (re.search(r">\s*(?:Werbung|Anzeige|Gesponsert)\b", raw, re.I)
           or re.search(r"""class=["'][^"']*(?:label|badge|ad-marker)[^"']*["']""", raw, re.I))
    rel = re.search(r"""rel=["'][^"']*(sponsored|nofollow)[^"']*""", raw, re.I)
    if lab and rel:
        return "OK", "软文双披露在场(文字标签+rel)——OLG Köln 2024 口径达标"
    if lab or rel:
        return "FAIL", "软文披露半套(%s)——文字标签与 rel=sponsored 双要(Abmahnung 风险先于 Google 惩罚)" % ("标签" if lab else "rel")
    return "FAIL", "Werbung/gesponsert 在场但无标签无 rel=sponsored——Abmahnung 律师函风险"

def r_fr_terms(ctx):
    a = ctx["alltext"].lower()
    m = {"email": "courriel", "podcast": "balado", "shopping": "magasinage"}
    hits = sorted(w for w in m if re.search(r"\b%s\b" % w, a))
    if not hits:
        return "OK", "未见 anglicism(OQLF 术语表不触发)"
    is_ca = ctx["is_html"] and re.search(r"""lang=["']fr[-_]CA""", ctx["raw"], re.I)
    if is_ca:
        return "FAIL", "fr-CA 页用 anglicism %s——OQLF 术语表:%s" % (hits, [m[w] for w in hits])
    return "OK", "fr-FR 容忍 anglicism %s;fr-CA 须换 %s(分流决策记录)" % (hits, [m[w] for w in hits])

def r_id_safezone(ctx):
    d = ctx["desc"]
    sz = ctx["cfg"]["desc_limit"].get("safe_zone", 120)
    if not d:
        return "MANUAL", "无 desc 可判"
    return "OK", "desc 前 %d 字符安全区:「%s」关键信息须前置在此(截断风险区外)" % (sz, d[:sz])

def r_id_baku(ctx):
    words = set(re.findall(r"[a-z']+", ctx["body"].lower()))
    gaul = sorted(words & ID_GAUL)
    if gaul:
        return "FAIL", "gaul 口语词 %s 在正文——关键词跟手指(baku/gaul 双轨),正文跟词典(baku)" % gaul
    return "OK", "正文 baku 一致(gaul 变体若在关键词层另开双轨)"

def r_id_eyd(ctx):
    a = ctx["alltext"].lower()
    old = [o for o, n in ID_EYD if re.search(r"\b%s\b" % o, a)]
    new = [n for o, n in ID_EYD if re.search(r"\b%s\b" % n, a)]
    if old and new:
        return "FAIL", "EYD V 新旧拼法并存(旧 %s/新 %s)——全站统一新拼法,旧拼法关键词层兼收" % (old[:3], new[:3])
    if old:
        return "FAIL", "EYD V 旧拼法 %s——按新拼法 %s(关键词层旧拼法兼收)" % (old, [n for o, n in ID_EYD if o in old])
    if new:
        return "OK", "EYD V 新拼法在场 %s" % new[:3]
    return "OK", "未检出新旧拼法判别词"

def r_hi_voice(ctx):
    a = ctx["alltext"].lower()
    hits = sorted({w for w in HI_VOICE if re.search(r"\b%s\b" % w, a)})
    if hits:
        return "OK", "语音助词形态 %s 命中——并入语音层关键词(助词词库×产品词)" % hits
    return "OK", "未检出罗马化语音助词(语音层关键词另行构建)"

def r_it_ch(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入(canonical/og:url 域判)"
    raw = ctx["raw"]
    ch = bool(re.search(r"""(?:canonical|og:url)[^>]*\.ch/""", raw, re.I))
    chf = "CHF" in raw
    if ch and chf:
        return "OK", ".ch 域+CHF 价在场——it-CH 独立 locale 成立(混德法词另人工核)"
    if ch and not chf:
        return "FAIL", ".ch 域在场但无 CHF 定价——疑似直接复制 it-IT"
    if chf and not ch:
        return "FAIL", "CHF 价在场但 canonical 非 .ch——it-CH 信号分裂"
    return "OK", "非 it-CH 页(it-IT 常规);it-CH 站须 .ch+CHF+混德法词独立做"

def r_it_piva(ctx):
    m = re.search(r"P\.?\s?IVA[\s::-]*\d{8,11}", ctx["alltext"], re.I)
    if m:
        return "OK", "P.IVA 在场(%s)——可链 Registro Imprese(ATECO+省)竞品链" % m.group(0)
    if re.search(r"azienda|impresa|servizi|contatt", ctx["alltext"], re.I):
        return "FAIL", "商业页未见 P.IVA——Registro Imprese 竞品链断"
    return "MANUAL", "非商业页,P.IVA 不适用"

def r_it_estval(ctx):
    body = ctx["body"]
    nums = len(re.findall(r"\d[\d.,]*", body))
    est = re.findall(r"\bcirca\b|\bstimat[oi]\b|~|secondo stime|approssimat", body, re.I)
    if nums >= 3 and not est:
        return "FAIL", "数字 %d 处无估算声明(circa/stimato)——测量值 vs 估算值须降级标注(数据阶梯)" % nums
    if est:
        return "OK", "估算声明在场 %d 处——测量值/估算值分级达标" % len(est)
    return "OK", "数字 %d 处(<3,声明判失活)" % nums

def r_tr_tanitim(ctx):
    if "tanıtım" not in ctx["alltext"].lower():
        return "OK", "未见 tanıtım yazısı 标记词"
    if not ctx["is_html"]:
        return "MANUAL", "检出 tanıtım——链路披露须 HTML 机检"
    if re.search(r"""rel=["'][^"']*(sponsored|nofollow|ugc)[^"']*""", ctx["raw"], re.I):
        return "OK", "tanıtım 链接带 rel 披露(非西式 guest post,链路披露必须)"
    return "FAIL", "tanıtım yazısı 在场但链接无 rel=sponsored 披露"

def r_vi_kw30(ctx):
    t, kw = ctx["title"], ctx.get("proxy_kw")
    lim = ctx["cfg"]["title_limit"].get("keyword_first_chars", 30)
    if not t:
        return "MANUAL", "无 title 可判"
    if not kw:
        return "MANUAL", "正文高频词不可用(正文过短,关键词人工给)"
    pos = t.lower().find(kw)
    if pos == -1:
        return "FAIL", "正文高频词「%s」不在 title——t0mmy 规则:标题词进前 %d 字符防 AI 改写" % (kw, lim)
    return ("OK" if pos < lim else "FAIL"), "「%s」位次 %d/前 %d 字符(%s)" % (kw, pos, lim, "达标" if pos < lim else "超出")

def r_th_buddhist(ctx):
    a = ctx["alltext"]
    be = re.search(r"พ\.?\s?ศ\.?\s*\d{4}|พุทธศักราช\s*\d{4}", a)
    greg = re.search(r"(?:%s)\s*2\d{3}|2\d{3}\s*(?:%s)" % (TH_MONTHS, TH_MONTHS), a)
    if be:
        return "OK", "佛历(พ.ศ.)纪年在场:%s" % be.group(0)
    if greg:
        return "FAIL", "泰月名配公历年(%s)——泰市场日期用佛历 พ.ศ.=公历+543" % greg.group(0)
    return "OK", "未检出泰文日期(佛历检查失活)"

def r_th_trunc(ctx):
    cfg = ctx["cfg"]
    nt, nd = unit_len(ctx["title"], "grapheme"), unit_len(ctx["desc"], "grapheme")
    risky = []
    if nt >= cfg["title_limit"]["value"] - 5:
        risky.append("title %d/%d" % (nt, cfg["title_limit"]["value"]))
    if nd >= cfg["desc_limit"]["value"] - 10:
        risky.append("desc %d/%d" % (nd, cfg["desc_limit"]["value"]))
    if risky:
        return "FAIL", "无空格文字词中截断风险:%s——meta 在词中间被截,逐页人工复核截断点" % ",".join(risky)
    return "OK", "title %d/desc %d 距限有余量,词中截断风险低" % (nt, nd)

def r_pl_diacritics(ctx):
    low = ctx["body"].lower()
    stripped = sorted({w for w in PL_STRIPPED if w in low})
    if stripped:
        return "FAIL", "剥变音残留词 %s——恢复 ą/ę/ł(剥字母伤品牌与 AI 保真)" % stripped
    if any(c in low for c in "ąćęłńóśźż"):
        return "OK", "变音字母在场(ą/ę/ł 保留)"
    return "OK", "未检出波兰语变音依赖词"

def r_pl_sierotki(ctx):
    lines = ctx.get("lines") or []
    hits = [ln[-25:] for ln in lines if re.search(PL_ORPHAN, ln)]
    if hits:
        return "FAIL", "行尾孤字 %d 处(%s…)——单双字母虚词不悬行尾(sierotki:NBSP/构建层)" % (len(hits), hits[0])
    if not lines:
        return "MANUAL", "需保留换行的输入(HTML 已折行,孤字判失活)"
    return "OK", "行尾无孤字(sierotki 达标)"

def r_nl_tone(ctx):
    a = ctx["alltext"]
    je = len(re.findall(r"\b[Jj]e\b|\bjouw\b|\b[Jj]ij\b", a))
    u_ = len(re.findall(r"\buw?\b", a))
    if je and u_:
        return "FAIL", "je(%d)/u(%d) 混用——nl-NL=je(连 B2B)、nl-BE=u(句中小写),全站单轨" % (je, u_)
    if je:
        return "OK", "je 体一致(nl-NL 口径)"
    if u_:
        return "OK", "u 体一致(确认 nl-BE 目标)"
    return "OK", "未见称谓"

def r_nl_placeholder(ctx):
    hits = re.findall(r"\[INVULLEN\]|INVULLEN|\[TODO\]|\[PLACEHOLDER\]|\bTBD\b|\bLorem\b|XXX", ctx["alltext"])
    if hits:
        return "FAIL", "占位符 %d 处(%s)——[INVULLEN] 占位制:发布前替换+虚构拒绝(数字不编造)" % (len(hits), sorted(set(hits))[:3])
    return "OK", "无占位符残留"

def r_nl_kvk(ctx):
    m = re.search(r"KvK[-\s:]?\d{8}", ctx["alltext"], re.I)
    if m:
        return "OK", "KvK 商会号在场(%s)——GBP 描述 750 字符用满另人工核" % m.group(0)
    if re.search(r"bedrijf|zakelijk|offerte|diensten", ctx["alltext"], re.I):
        return "FAIL", "商业页未见 KvK 号——荷兰商会信任层缺口"
    return "MANUAL", "非商业页,KvK 不适用"

# ---------- v3 runner:⑩ 常开机检注册表(全市场)----------
def g_mw_rate(ctx):
    hits = ctx.get("mw_hits", 0)
    if not hits:
        return "OK", "营销词命中 0"
    body, cfg = ctx["body"], ctx["cfg"]
    if cfg.get("sentence_split") == "cjk":
        denom, unit = max(len(body), 1) / 1000.0, "千字"
    else:
        denom, unit = max(len(body.split()), 1) / 1000.0, "千词"
    return ("FAIL" if hits > 3 else "OK"), "营销词命中 %d,密度 %.1f/%s(页上限 3,计数已进报告)" % (hits, hits / denom, unit)

def g_sent_cv(ctx):
    cfg = ctx["cfg"]
    su = cfg["sentence_ideal"].get("unit", "words")
    sents = split_sents(ctx["body"], cfg.get("sentence_split", "latin"))
    lens = [l for l in (len(s) if su == "chars" else len(s.split()) for s in sents) if l > 0]
    if len(lens) < 5:
        return "MANUAL", "句数 %d<5,CV 不可判" % len(lens)
    mean = sum(lens) / len(lens)
    sd = math.sqrt(sum((x - mean) ** 2 for x in lens) / len(lens))
    cv = sd / mean if mean else 0
    return ("FAIL" if cv < 0.25 else "OK"), "句长 CV %.2f(均值 %.1f%s/句;AI 均匀签名阈值 0.25)" % (cv, mean, "字" if su == "chars" else "词")

def g_faq_density(ctx):
    body = ctx["body"]
    qs = len(re.findall(r"[?？¿]", body))
    sents = split_sents(body, ctx["cfg"].get("sentence_split", "latin"))
    ratio = qs / max(len(sents), 1) * 100
    if qs == 0:
        return "OK", "问句 0,密度 %.1f%%——FAQ/PAA 层建议配问答块(密度值供阈值判定)" % ratio
    return "OK", "问句 %d,密度 %.1f%%(每百句;供 FAQ 块阈值判定)" % (qs, ratio)

def g_num_density(ctx):
    body, cfg = ctx["body"], ctx["cfg"]
    su = cfg["sentence_ideal"].get("unit", "words")
    sents = split_sents(body, cfg.get("sentence_split", "latin"))
    total = len(re.findall(r"\d[\d.,]*", body))
    num_sents = [s for s in sents if re.search(r"\d", s)]
    if not num_sents:
        return "OK", "数字 0(有源数字密度判失活)"
    denom = (max(len(body), 1) / 1000.0) if su == "chars" else (max(len(body.split()), 1) / 1000.0)
    sourced = sum(1 for s in num_sents if any(c in s for c in SRC_CUES))
    share = sourced / len(num_sents) * 100
    state = "FAIL" if total >= 5 and share < 30 else "OK"
    return state, "数字 %d 处,密度 %.1f/%s;有源(同句来源线索)%d/%d=%.0f%%(<30%% 且数字≥5=无源数字堆砌)" % (
        total, total / denom, "千字" if su == "chars" else "千词", sourced, len(num_sents), share)

def g_h2_question(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入"
    h2s = [re.sub(r"<[^>]+>", "", h).strip() for h in re.findall(r"<h2[^>]*>(.*?)</h2>", ctx["raw"], re.S | re.I)]
    if not h2s:
        return "MANUAL", "无 H2 可判"
    qs = [h for h in h2s if re.match(H2_Q_RE, h, re.I)]
    ratio = len(qs) / len(h2s) * 100
    return ("FAIL" if len(h2s) >= 4 and not qs else "OK"), "疑问式 H2 %d/%d(%.0f%%;H2≥4 且全陈述式→FAIL)" % (len(qs), len(h2s), ratio)

def g_list_density(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入"
    raw = ctx["raw"]
    li = len(re.findall(r"<li\b", raw, re.I))
    p = len(re.findall(r"<p\b", raw, re.I))
    if li + p == 0:
        return "MANUAL", "无 li/p 可判"
    d = li / (li + p)
    return ("FAIL" if p >= 6 and d < 0.1 else "OK"), "列表密度 li/(li+p)=%.2f(li %d/p %d;长文全无列表=可扫性差)" % (d, li, p)

def g_title_kw(ctx):
    t, kw = ctx["title"], ctx.get("proxy_kw")
    if not t:
        return "MANUAL", "无 title"
    if not kw:
        return "MANUAL", "正文高频词不可用(正文过短)"
    lim = ctx["cfg"]["title_limit"].get("keyword_first_chars", 30)
    pos = t.lower().find(kw)
    if pos == -1:
        return "FAIL", "正文高频词「%s」不在 title(位次 -1)——标题未锚定主题词" % kw
    return ("OK" if pos < lim else "FAIL"), "「%s」位次 %d(理想前 %d 字符,vi t0mmy 口径)" % (kw, pos, lim)

def g_date_fmt(ctx):
    mkt, a = ctx["market"], ctx["alltext"]
    style = DATE_STYLE.get(mkt)
    expect = ctx["cfg"].get("formats", {}).get("date", "?")
    cjk = re.findall(r"\d{4}年\d{1,2}月\d{1,2}日|\d{4}년\s*\d{1,2}월", a)
    dot = re.findall(r"\b\d{1,2}\.\d{1,2}\.\d{4}\b", a)
    dash = re.findall(r"\b\d{1,2}-\d{1,2}-\d{4}\b", a)
    slash = re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b", a)
    if style == "cjk":
        native, foreign = cjk, slash + dot + dash
    elif style == "dot":
        native, foreign = dot, slash + dash
    elif style == "dash":
        native, foreign = dash, slash + dot
    elif style == "slash":
        native, foreign = slash, cjk + dot + dash
    elif style == "en":
        native, foreign = slash + re.findall(r"[A-Z][a-z]+ \d{1,2}, \d{4}", a), cjk
    else:  # name/be/未知:仅判 CJK 格式入侵
        native, foreign = [], cjk
    if foreign:
        return "FAIL", "日期 %s 与市场规范不符(%s 期望 %s;ISO 8601 容忍)" % (foreign[:3], mkt, expect)
    if native:
        return "OK", "市场格式日期在场 %s(%s)" % (native[:2], expect)
    return "OK", "未检出冲突日期(ISO/纪年判失活;期望 %s)" % expect

def g_phone_prefix(ctx):
    want = ctx["cfg"].get("formats", {}).get("phone_prefix", "").lstrip("+")
    phones = re.findall(r"\+(\d{1,3})[\s-]?\d{2,4}[\s-]?\d{3,4}", ctx["alltext"])
    if not phones:
        return "OK", "未检出国际电话(前缀核验失活;市场期望 +%s)" % want
    bad = sorted({p for p in phones if p != want})
    if bad:
        return "FAIL", "电话前缀 +%s 与市场 +%s 不符(共 %d 号,异前缀 %s)——落地页信任信号" % (
            "/+".join(bad), want, len(phones), bad)
    return "OK", "电话前缀一致 +%s(共 %d 号)" % (want, len(phones))

def g_currency(ctx):
    a, local = ctx["alltext"], CUR_LOCAL.get(ctx["market"], ())
    found = [m.group(0) for m in re.finditer(r"R\$|€|£|¥|￥|₽|₺|₹|฿|zł|Rp\b|CHF|\$", a)]
    found += [t for t in ("元", "円", "원", "đ") if t in a]
    if not found:
        return "OK", "未检出货币符号(本地化核验失活;市场符号 %s)" % ("/".join(local) or "?")
    fset = set(found)
    foreign = sorted(fset - set(local))
    if foreign:
        present = sorted(fset & set(local))
        if not present:
            return "FAIL", "货币符号 %s 非本市场(期望 %s)——价格未本地化" % (foreign, "/".join(local))
        return "FAIL", "货币混用:本地 %s+外币 %s——多币种页须显式标注币种" % (present, foreign)
    return "OK", "货币符号本地化一致(%s)" % sorted(fset)

def g_script_ratio(ctx):
    rng = SCRIPT_RANGE.get(ctx["market"])
    letters = ctx["letters"]
    if not rng or not letters:
        return "MANUAL", "本市场不在 v3 语言占比清单(ru/ko/th)或正文为空"
    lo, hi = rng
    n = sum(1 for c in letters if lo <= c <= hi)
    r = n / len(letters)
    if r < 0.3:
        return "FAIL", "母语字符占比 %.0f%%<30%%——语言/市场错配?" % (r * 100)
    return "OK", "母语字符占比 %.0f%%(%d/%d 字母;数值供阈值判定)" % (r * 100, n, len(letters))

def g_ai_meta(ctx):
    if not ctx["is_html"]:
        return "MANUAL", "机检需 HTML 输入"
    m = robots_meta_content(ctx["raw"])
    if not m:
        return "OK", "robots meta 未设置(默认进 AI 答案输入)"
    low = m.lower()
    exits = [t for t in ("noai", "noimageai", "nosnippet", "max-snippet:0") if t in low]
    if exits:
        return "FAIL", "robots meta 含 %s——页面退出 AI 答案输入(要进 AI 的页须移除;ko nosourceinfo/ja nosnippet 同层)" % exits
    return "OK", "robots meta=%s(无 AI 退出指令)" % m

V3_CHECKS = [
    ("v3_mw_rate", "营销词密度", g_mw_rate),
    ("v3_sent_cv", "句长 CV", g_sent_cv),
    ("v3_faq", "FAQ 问句密度", g_faq_density),
    ("v3_num", "有源数字密度", g_num_density),
    ("v3_h2q", "H2 疑问式占比", g_h2_question),
    ("v3_list", "列表密度", g_list_density),
    ("v3_titlekw", "标题关键词位次", g_title_kw),
    ("v3_date", "日期格式", g_date_fmt),
    ("v3_phone", "电话前缀", g_phone_prefix),
    ("v3_currency", "货币符号", g_currency),
    ("v3_script", "母语字符占比", g_script_ratio),
    ("v3_aimeta", "AI 退出 meta", g_ai_meta),
]

RUNNERS = {
    "zh_script_mix": r_zh_script, "marketing_cap": r_marketing, "ja_len": r_ja_len,
    "ja_keigo": r_ja_keigo, "ja_ai": r_ja_ai, "ja_nosnippet": r_ja_nosnippet,
    "ja_fwalnum": r_ja_fwalnum, "ja_conv": r_ja_conv, "ar_rtl": r_ar_rtl,
    "ar_bidi": r_ar_bidi, "ar_digits": r_ar_digits, "ru_legal": r_ru_legal,
    "de_ansprache": r_de_ansprache, "de_impressum": r_de_impressum, "fr_nbsp": r_fr_nbsp,
    "tr_dotted_i": r_tr_dotted_i, "vi_tones": r_vi_tones, "vi_variance": r_vi_variance,
    "hi_mix": r_hi_mix, "hi_num": r_hi_num, "th_polite": r_th_polite,
    "th_grapheme": r_th_grapheme, "es_h2q": r_es_h2q, "es_419": r_es_419,
    # v3 第二批
    "ko_nosourceinfo": r_ko_nosourceinfo, "ko_grid": r_ko_grid, "ko_channel": r_ko_channel,
    "ja_qr": r_ja_qr, "en_citability": r_en_citability, "es_variant": r_es_variant,
    "es_payment": r_es_payment, "pt_cnpj": r_pt_cnpj, "pt_payment": r_pt_payment,
    "pt_sponsored": r_pt_sponsored, "de_werbung": r_de_werbung, "fr_terms": r_fr_terms,
    "id_safezone": r_id_safezone, "id_baku": r_id_baku, "id_eyd": r_id_eyd,
    "hi_voice": r_hi_voice, "it_ch": r_it_ch, "it_piva": r_it_piva,
    "it_estval": r_it_estval, "tr_tanitim": r_tr_tanitim, "vi_kw30": r_vi_kw30,
    "th_buddhist": r_th_buddhist, "th_trunc": r_th_trunc, "pl_diacritics": r_pl_diacritics,
    "pl_sierotki": r_pl_sierotki, "nl_tone": r_nl_tone, "nl_placeholder": r_nl_placeholder,
    "nl_kvk": r_nl_kvk,
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
           "alltext": alltext, "is_html": is_html, "raw": raw, "letters": letters, "ar_ratio": ar_ratio,
           "lines": [] if is_html else [l for l in text.splitlines() if l.strip()]}
    # v3:正文高频词代理(标题关键词位次检查用;CJK 用 2 字符 n-gram,拉丁用 ≥5 字母词)
    if market in ("zh", "ja"):
        grams = [g for g in re.findall(r"[\u4e00-\u9fff]{2}", body)]
    else:
        grams = [w.lower() for w in re.findall(r"[^\W\d_]{5,}", body)]
    ctx["proxy_kw"] = Counter(grams).most_common(1)[0][0] if grams else None
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

    # ⑦/⑨ special_checks 动态机检/人工清单(--report 输出三态;v3 第二批映射同池执行)
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
        auto = ok + fail
        print("special_checks: AUTO-OK %d / AUTO-FAIL %d / MANUAL %d(共 %d)" % (ok, fail, man, len(checks)))
        print("AUTO 比例: %d/%d = %.0f%%" % (auto, len(checks), auto * 100.0 / max(len(checks), 1)))

    # ⑩ v3 常开机检(内容/结构/格式/语言/robots 五类注册表,全市场)
    v3_ok = v3_fail = v3_man = 0
    print("\n⑩ v3 常开机检(内容/结构/格式/语言/robots,%d 项)" % len(V3_CHECKS))
    for cid, title_, fn in V3_CHECKS:
        state, detail = fn(ctx)
        if state == "FAIL":
            v3_fail += 1
            warn += 1
            print("[v3-FAIL] %s —— %s" % (title_, detail))
        elif state == "MANUAL":
            v3_man += 1
            print("[v3-MANUAL] %s —— %s" % (title_, detail))
        else:
            v3_ok += 1
            print("[v3-OK] %s —— %s" % (title_, detail))
    print("v3 常开机检: OK %d / FAIL %d / MANUAL %d(共 %d)" % (v3_ok, v3_fail, v3_man, len(V3_CHECKS)))

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
