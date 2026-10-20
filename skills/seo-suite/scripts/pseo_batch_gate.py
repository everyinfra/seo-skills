#!/usr/bin/env python3
"""pSEO 批次质量闸门(stdlib only;规格=references/overview/pipeline-completeness.md R3-2,
闸门数字=references/technical/programmatic-seo-gates.md)。流水线位置:数据层产出
batch.jsonl(每行 {key, axis_values{...}, facts:[{value,source,as_of,quality_score}],
title, desc, h1, body})→ 本脚本六闸判定 → PASS/WARNING/STOP(STOP 阻断发布并退回数据层)。
六闸:①数据闸 key 重复/必填(key/title/desc/h1/body)缺失→该记录不生成(列清单,非
fatal);fact 缺 source/as_of→剔除+警告;quality_score<0.6(默认)→警告②爆炸预警 axis
组合空间 ∏|distinct values|(含 locale)与记录数之比 >10× →警告(组合≫记录=覆盖缺口;
记录≫组合=无差异化重复生成)③唯一度 title+首段 Simhash 两两(>2000 条签名 4×16bit 分桶
降 O(n²),鸽笼保证 hamming≤3 不漏);必须不同区块(title+h1)全同→STOP;批次唯一度
<30%→STOP(增强规则)、<40%→WARNING(薄内容);近重复对/标题集重复→WARNING④样板比
跨记录公共 5-gram 占正文 n-gram 比 >60%→WARNING⑤页型地板 正文词数(CJK 按字计)<地板
(product 400/article 800 默认)→FAIL(STOP)⑥判定 任一 STOP、警告≥100(未复核)、或
唯一度 30-40%→exit 1;警告≥500 硬停(需用户明确批准);警告<100→exit 0 带报告。
Simhash 借鉴 scripts/traffic_funnel.py 思路自实现(不 import):token→md5 前 8 字节当
64 位指纹,逐位 ±1 加权。分词混合:拉丁 [A-Za-z0-9_]+ 小写词 + CJK 连续字流 bigram——
中文整句在 \\w+ 下坍缩成单 token,两页不同的中文正文→各一个"独有"token→唯一度假高、
全同漏检;bigram 把粒度压到字对修复。批次唯一度=各记录(独有 token 出现次数/总 token
出现次数,对照批内其余全部记录)的均值。
用法: python3 pseo_batch_gate.py --records batch.jsonl [--rendered dir/] [--json]
       python3 pseo_batch_gate.py --records batch.jsonl --min-quality 0.6 --floor product=400,article=800
退出码:0=PASS / 1=STOP·WARNING(阻断发布) / 2=用法或输入错(套件契约,ci-gates.md)。"""
import hashlib
import json
import os
import re
import unicodedata
import sys
from collections import Counter, defaultdict
from html.parser import HTMLParser

SIMHASH_BITS = 64
DUP_HAMMING = 3            # 近重复汉明阈值(自定[推断],沿用 traffic_funnel 口径)
PAIRWISE_MAX = 2000        # 超过 → 签名分桶(4×16bit band;hamming≤3 至多污 3 band,鸽笼不漏)
BANDS = 4
NGRAM_N = 5                # 样板 n-gram 阶数
MIN_QUALITY = 0.6          # fact quality_score 阈值(--min-quality 覆盖)
UNIQUE_STOP = 0.30         # 页间唯一内容 <30% → 硬停(增强规则)
UNIQUE_WARN = 0.40         # <40% → 薄内容标记
WARN_COUNT = 100           # 未复核 100+ → 发布前须内容审计
STOP_COUNT = 500           # 500+ → 硬停(需用户明确批准)
BOILER_WARN = 0.60         # 模板样板 >60% → 风险页
EXPLOSION_FACTOR = 10      # 组合空间与记录数比 >10× → 警告
PAGE_FLOORS = {"product": 400, "article": 800}   # 页型地板(词数)
REQUIRED = ("key", "title", "desc", "h1", "body")
MUST_DIFFER = ("title", "h1")                    # 两页这些区块全同 → STOP(批次标题集唯一性)

USAGE = """usage: pseo_batch_gate.py --records batch.jsonl [--rendered dir/] [--json] [选项]
       pseo_batch_gate.py --records batch.jsonl --min-quality 0.6 --floor product=400,article=800
pSEO 批次质量闸门(R3-2;数字=references/technical/programmatic-seo-gates.md):
  ①数据闸   key 重复/必填(key/title/desc/h1/body)缺失 → 该记录不生成(列清单,非 fatal);
            fact 缺 source/as_of → 剔除+警告;quality_score<阈值(默认 0.6)→ 警告
  ②爆炸预警 axis 组合空间 ∏|distinct values|(含 locale)vs 记录数,>10× 差异 → 警告
            (组合≫记录=覆盖缺口;记录≫组合=无差异化重复生成)
  ③唯一度   批内 title+首段 Simhash 两两(>2000 条签名 4×16bit 分桶降 O(n²));
            必须不同区块(title+h1)全同 → STOP;批次唯一度 <30% → STOP、<40% → WARNING;
            近重复对(汉明≤3)/标题集重复 → WARNING
  ④样板比   跨记录公共 5-gram 占正文 n-gram 比 >60% → WARNING(模板样板风险页)
  ⑤页型地板 正文词数(CJK 按字计)< 页型地板 → FAIL(STOP);缺 --rendered 按记录 body 计
  ⑥判定     任一 STOP、警告≥100(未复核)、或唯一度 30-40% → exit 1 阻断发布并退回数据层
            记录清单;警告≥500 硬停;警告<100 → exit 0 带报告
  --records PATH    批次 JSONL(每行一条记录;空行跳过)
  --rendered  DIR   渲染产物目录(按 key.html 逐个读:缺文件→警告+按 body 判;词数以
                    渲染产物为准——它才是真正发布的内容)
  --min-quality F   fact quality_score 阈值(默认 0.6)
  --floor T=N,...   页型地板覆盖(默认 product=400,article=800;未知页型按 product)
  --json            结构化输出 {verdict, stats, stop_items, warnings, dropped_records}
退出码:0=PASS / 1=STOP·WARNING(阻断发布) / 2=用法或输入错(套件契约)。"""


# ---------- 工具:分词 / Simhash / 分桶 ----------

LATIN_RE = re.compile(r"[A-Za-z0-9_]+")
CJK_RUN = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uac00-\ud7af]+")


def tokens(text):
    """混合分词:拉丁 [A-Za-z0-9_]+ 小写词 + CJK 连续字流 bigram(单字流保留单字)。
    中文整句在 \\w+ 下坍缩成单 token(两页不同中文正文 → 各一个"独有"token → 唯一度
    假高、全同漏检);bigram 把粒度压到字对修复。顺序:先拉丁后 CJK(词袋,顺序无关)。"""
    out = [m.group().lower() for m in LATIN_RE.finditer(text)]
    for run in CJK_RUN.findall(text):
        if len(run) == 1:
            out.append(run)
        else:
            out.extend(run[i:i + 2] for i in range(len(run) - 1))
    return out


def wc(text):
    """词数。同 site_audit.wc(B47)口径(B61 修,2026-10-21):CJK 逐字计;其余文字字母/数字
    连续段为一词,组合符号(Mn/Mc/Me,如天城体 matra/virama)附着在词内,空格与标点断词,
    「बेस्ट लैपटॉप कैसे खरीदें」=4。不 import site_audit:CJK 判定沿用本脚本 CJK_RUN(含扩展 A/兼容区);下划线照旧连词(snake_case=1)。修前只认 ASCII,印地语计 0。"""
    text = text.replace("İ", "i").replace("I\u0307", "i").replace("\u0307", "")
    perchar = words = 0
    prev = False  # 前一字符是否处于词内
    for c in text:
        if CJK_RUN.fullmatch(c):
            perchar += 1
            prev = False
            continue
        cat = unicodedata.category(c)
        is_l = cat[0] in ("L", "N") or c == "_"
        if is_l and not prev:
            words += 1
        prev = is_l or ((c in "'’" or cat[0] == "M") and prev)
    return perchar + words


def simhash(toks, bits=SIMHASH_BITS):
    r"""64 位 Simhash(自实现,借鉴 traffic_funnel.py):token→md5 前 8 字节当 64 位
    指纹,逐位 ±1 加权,各位符号即输出指纹。"""
    v = [0] * bits
    for tok in toks:
        h = int.from_bytes(hashlib.md5(tok.encode("utf-8")).digest()[:8], "big")
        for i in range(bits):
            v[i] += 1 if h >> i & 1 else -1
    f = 0
    for i in range(bits):
        if v[i] > 0:
            f |= 1 << i
    return f


def hamming(a, b):
    return bin(a ^ b).count("1")


def first_para(body):
    """首段:按空行分段的首个非空段;无空行则整个 body 即首段。"""
    for chunk in re.split(r"\n\s*\n", body or ""):
        c = chunk.strip()
        if c:
            return c
    return ""


def near_dup_pairs(sigs, threshold=DUP_HAMMING, force_bands=False):
    """近重复对(汉明≤threshold)。记录 ≤2000 全两两;>2000(或 force_bands)走
    4×16bit band 分桶:两条签名至多差 threshold≤3 位 → 至多污 3 个 band → 至少一个
    band 值相同(鸽笼),桶内再逐对汉明复核——候选生成完备且假阳性被复核滤掉
    (band 哈希冲突容忍)。返回按键序排序的 (a,b) 对列表。"""
    keys = sorted(sigs)
    if not (force_bands or len(keys) > PAIRWISE_MAX):
        out = []
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                if hamming(sigs[a], sigs[b]) <= threshold:
                    out.append((a, b))
        return out
    bands = defaultdict(list)
    for k in keys:
        s = sigs[k]
        for bi in range(BANDS):
            bands[(bi, (s >> (16 * bi)) & 0xFFFF)].append(k)
    cand = set()
    for members in bands.values():
        if len(members) < 2:
            continue
        members.sort()
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                cand.add((a, b))
    return [(a, b) for a, b in sorted(cand) if hamming(sigs[a], sigs[b]) <= threshold]


def ngrams(seq, n=NGRAM_N):
    return [tuple(seq[i:i + n]) for i in range(len(seq) - n + 1)]


class _TextExtract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, d):
        self.parts.append(d)


def strip_html(html):
    """渲染产物 → 纯文本(去标签/实体,空白折叠);解析器异常时标签正则兜底。"""
    p = _TextExtract()
    try:
        p.feed(html)
        p.close()
    except Exception:
        return " ".join(re.sub(r"<[^>]+>", " ", html).split())
    return " ".join("".join(p.parts).split())


def die(msg, code=2):
    sys.stderr.write("%s\n" % msg)
    sys.exit(code)


# ---------- ① 数据闸:加载 + 清洗 ----------

def load_batch(path):
    """JSONL → (records, dropped)。解析失败/缺 key/必填缺失/key 重复(后者丢弃)→
    dropped 列清单(非 fatal:其余记录照常过闸);facts 清洗在 clean_facts。"""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError as e:
        return die("records 文件无法读取 %s: %s" % (path, e))
    records, dropped, seen = [], [], {}
    for ln, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s:
            continue
        try:
            obj = json.loads(s)
        except ValueError as e:
            dropped.append({"key": None, "line": ln, "reason": "JSON 解析失败: %s" % e})
            continue
        if not isinstance(obj, dict):
            dropped.append({"key": None, "line": ln, "reason": "记录非 JSON 对象"})
            continue
        key = obj.get("key")
        if not isinstance(key, str) or not key.strip():
            dropped.append({"key": None, "line": ln, "reason": "必填缺失: key"})
            continue
        miss = [f for f in REQUIRED if f != "key" and not str(obj.get(f) or "").strip()]
        if miss:
            dropped.append({"key": key, "line": ln, "reason": "必填缺失: %s" % ",".join(miss)})
            continue
        if key in seen:
            dropped.append({"key": key, "line": ln,
                            "reason": "key 重复(首见行 %d,该记录不生成)" % seen[key]})
            continue
        seen[key] = ln
        records.append(obj)
    return records, dropped


def clean_facts(rec, min_quality=MIN_QUALITY):
    """①数据闸 fact 清洗:缺 source 或 as_of → 剔除+警告;quality_score<阈值 → 警告
    (fact 保留,数据层需补证)。返回 (保留 facts, 警告列表)。"""
    facts, key = rec.get("facts"), rec.get("key")
    if facts is None:
        return [], []
    if not isinstance(facts, list):
        return [], [{"kind": "facts_invalid", "key": key, "message": "facts 非列表,按空处理"}]
    kept, warns = [], []
    for f in facts:
        if not isinstance(f, dict):
            warns.append({"kind": "fact_dropped", "key": key, "message": "fact 非对象,剔除"})
            continue
        miss = [k for k in ("source", "as_of") if not str(f.get(k) or "").strip()]
        if miss:
            warns.append({"kind": "fact_dropped", "key": key,
                          "message": "fact(value=%r)缺 %s → 剔除" % (f.get("value"), "+".join(miss))})
            continue
        q = f.get("quality_score")
        if isinstance(q, (int, float)) and not isinstance(q, bool) and q < min_quality:
            warns.append({"kind": "fact_quality_low", "key": key,
                          "message": "fact(value=%r)quality_score %s<%s" % (f.get("value"), q, min_quality)})
        kept.append(f)
    return kept, warns


# ---------- ②-⑥ 六闸主流程 ----------

def run_gates(records, dropped, rendered=None, min_quality=MIN_QUALITY, floors=None):
    """六闸判定;返回报告 dict({verdict, stats, stop_items, warnings, dropped_records})。"""
    floors = dict(floors or PAGE_FLOORS)
    warnings, stop_items = [], []

    # ① 数据闸:fact 清洗 + 轴归一(locale 顶层字段并入轴空间)
    facts_total = facts_dropped = facts_low = 0
    for rec in records:
        raw = rec.get("facts")
        if isinstance(raw, list):
            facts_total += len(raw)
        kept, warns = clean_facts(rec, min_quality)
        for w in warns:
            if w["kind"] == "fact_dropped":
                facts_dropped += 1
            elif w["kind"] == "fact_quality_low":
                facts_low += 1
        warnings.extend(warns)
        rec["_facts"] = kept
        av = rec.get("axis_values")
        if av is None:
            axes = {}
        elif isinstance(av, dict):
            axes = {str(k): str(v) for k, v in av.items()}
        else:
            warnings.append({"kind": "axis_invalid", "key": rec.get("key"),
                             "message": "axis_values 非对象,忽略(不进爆炸预警)"})
            axes = {}
        loc = rec.get("locale")
        if loc is not None and "locale" not in axes:
            axes["locale"] = str(loc)
        rec["_axes"] = axes

    # ② 爆炸预警:组合空间 ∏|distinct axis values| vs 记录数,>10× 双向警告
    n = len(records)
    space = None
    axes_all = sorted({a for r in records for a in r["_axes"]})
    if axes_all:
        space = 1
        for a in axes_all:
            space *= len({r["_axes"][a] for r in records if a in r["_axes"]})
        if space > EXPLOSION_FACTOR * n:
            warnings.append({"kind": "axis_gap", "key": None,
                             "message": "axis 组合空间 %d vs 记录 %d(%.1f×)>10×:覆盖缺口,批内仅生成 %.1f%% 组合"
                                        % (space, n, space / n, 100.0 * n / space)})
        elif n > EXPLOSION_FACTOR * space:
            warnings.append({"kind": "axis_explosion", "key": None,
                             "message": "记录 %d vs axis 组合空间 %d(%.1f×)>10×:疑似无差异化重复生成"
                                        % (n, space, n / space)})

    # 渲染产物:逐 key.html 读(缺 → 警告,正文按记录 body 判)
    rendered_text = {}
    if rendered:
        for rec in records:
            key = rec["key"]
            if os.path.basename(key) != key or key in (".", ".."):
                warnings.append({"kind": "rendered_unsafe_key", "key": key,
                                 "message": "key 含路径分隔符,跳过渲染产物读取(正文按 body 判)"})
                continue
            p = os.path.join(rendered, key + ".html")
            if not os.path.isfile(p):
                warnings.append({"kind": "rendered_missing", "key": key,
                                 "message": "渲染产物缺失 %s.html(正文按记录 body 判)" % key})
                continue
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    rendered_text[key] = strip_html(f.read())
            except OSError as e:
                warnings.append({"kind": "rendered_unreadable", "key": key,
                                 "message": "渲染产物读取失败: %s" % e})

    # 内容 token 化:唯一度=title+h1+body;Simhash 签名=title+首段;样板=body 5-gram
    for rec in records:
        rec["_tok"] = tokens("%s %s %s" % (rec.get("title") or "", rec.get("h1") or "",
                                           rec.get("body") or ""))
        rec["_sig"] = simhash(tokens("%s %s" % (rec.get("title") or "",
                                                first_para(rec.get("body")))))
        rec["_grams"] = ngrams(tokens(rec.get("body") or ""))

    # ③ 唯一度:必须不同区块(title+h1)全同 → STOP;标题集重复 → WARNING
    md_groups = {}
    for rec in records:
        md_groups.setdefault((rec.get("title") or "", rec.get("h1") or ""), []).append(rec["key"])
    gid = {}
    for gi, members in enumerate(md_groups.values()):
        if len(members) >= 2:
            stop_items.append({"kind": "must_differ_duplicate", "keys": sorted(members),
                               "message": "必须不同区块(%s)全同:页与页无差异(doorway 风险)"
                                          % "+".join(MUST_DIFFER)})
            for k in members:
                gid[k] = gi
    title_groups = {}
    for rec in records:
        title_groups.setdefault(rec.get("title") or "", []).append(rec["key"])
    for title, members in title_groups.items():
        free = [k for k in members if k not in gid]
        for k in free[1:]:
            warnings.append({"kind": "title_dup", "key": k,
                             "message": "标题集非唯一(title=%r 共 %d 条,批次标题须唯一)"
                                        % (title, len(members))})

    # ③ 唯一度:Simhash 近重复对(title+首段,>2000 分桶);已 STOP 的全同对不重复告警
    sigs = {r["key"]: r["_sig"] for r in records}
    pairs = near_dup_pairs(sigs, DUP_HAMMING)
    for a, b in pairs:
        if gid.get(a) is not None and gid.get(a) == gid.get(b):
            continue
        warnings.append({"kind": "near_dup", "key": a,
                         "message": "与 %s Simhash 汉明距离 %d≤%d(title+首段近重复候选)"
                                    % (b, hamming(sigs[a], sigs[b]), DUP_HAMMING)})

    # ③ 唯一度:批次均值(独有 token 出现次数/总次数,对照批内其余全部记录)
    type_count = Counter()
    for rec in records:
        for t in set(rec["_tok"]):
            type_count[t] += 1
    uniq_vals = []
    for rec in records:
        seq = rec["_tok"]
        if seq:
            uniq_vals.append(sum(1 for t in seq if type_count[t] == 1) / len(seq))
    uniq_mean = (sum(uniq_vals) / len(uniq_vals)) if len(records) >= 2 and uniq_vals else None
    if uniq_mean is not None:
        if uniq_mean < UNIQUE_STOP:
            stop_items.append({"kind": "uniqueness_hard_stop",
                               "keys": sorted(r["key"] for r in records),
                               "message": "批次唯一度 %.1f%%<30%%(增强规则硬停):整批退回数据层"
                                          % (uniq_mean * 100)})
        elif uniq_mean < UNIQUE_WARN:
            warnings.append({"kind": "uniqueness_thin", "key": None,
                             "message": "批次唯一度 %.1f%%<40%%:薄内容标记(scaled-content 惩罚风险)"
                                        % (uniq_mean * 100)})

    # ④ 样板比:跨记录公共 5-gram 占该记录正文 n-gram 出现次数比 >60% → WARNING
    boiler_mean = None
    if len(records) >= 2:
        common = None
        for rec in records:
            gs = set(rec["_grams"])
            common = gs if common is None else (common & gs)
        common = common or set()
        ratios = []
        for rec in records:
            grams = rec["_grams"]
            if not grams:
                continue
            ratio = sum(1 for g in grams if g in common) / len(grams)
            ratios.append(ratio)
            if ratio > BOILER_WARN:
                warnings.append({"kind": "boilerplate", "key": rec["key"],
                                 "message": "模板样板比 %.0f%%>60%%(公共 %d-gram 占比,风险页型)"
                                            % (ratio * 100, NGRAM_N)})
        boiler_mean = (sum(ratios) / len(ratios)) if ratios else None

    # ⑤ 页型地板:正文词数(渲染产物优先)< 地板 → FAIL(STOP)
    wcs = {}
    for rec in records:
        text = rendered_text.get(rec["key"])
        src = "rendered" if text is not None else "body"
        if text is None:
            text = rec.get("body") or ""
        cnt = wc(text)
        wcs[rec["key"]] = cnt
        ptype = str(rec.get("page_type") or rec.get("type") or "product").lower()
        floor = floors.get(ptype, floors["product"])
        if cnt < floor:
            stop_items.append({"kind": "page_floor", "keys": [rec["key"]],
                               "message": "正文词数 %d < %s 地板 %d(来源 %s)→ FAIL 不发布"
                                          % (cnt, ptype, floor, src)})

    # ⑥ 判定:警告 ≥500 硬停 → STOP;≥100 或唯一度 30-40% → WARNING;否则 PASS
    if len(warnings) >= STOP_COUNT:
        stop_items.append({"kind": "warning_overload_500",
                           "keys": sorted(r["key"] for r in records),
                           "message": "警告 %d≥500(无正当理由页硬停):需用户明确批准+薄内容审计"
                                      % len(warnings)})
    if stop_items:
        verdict = "STOP"
    elif len(warnings) >= WARN_COUNT or (uniq_mean is not None and uniq_mean < UNIQUE_WARN):
        verdict = "WARNING"
    else:
        verdict = "PASS"

    stats = {
        "records_in": len(records) + len(dropped),
        "records_kept": n,
        "records_dropped": len(dropped),
        "facts_total": facts_total,
        "facts_dropped": facts_dropped,
        "facts_low_quality": facts_low,
        "axis_space": space,
        "axis_ratio": round(space / n, 2) if space and n else None,
        "uniqueness_pct": round(uniq_mean * 100, 1) if uniq_mean is not None else None,
        "boilerplate_pct": round(boiler_mean * 100, 1) if boiler_mean is not None else None,
        "word_count_min": min(wcs.values()) if wcs else None,
        "word_count_mean": round(sum(wcs.values()) / len(wcs), 1) if wcs else None,
        "near_dup_pairs": len(pairs),
        "warnings": len(warnings),
        "return_to_data": sorted({k for s in stop_items for k in s["keys"]}),
    }
    return {"verdict": verdict, "stats": stats, "stop_items": stop_items,
            "warnings": warnings, "dropped_records": dropped}


# ---------- 渲染 ----------

def _pct(x):
    return "n/a" if x is None else "%.1f%%" % x


def render_markdown(rep):
    st = rep["stats"]
    tag = {"STOP": "STOP(阻断发布)", "WARNING": "WARNING(阻断发布,发布前须内容审计)",
           "PASS": "PASS"}[rep["verdict"]]
    L = ["## pSEO 批次闸门:" + tag, "",
         "记录 %d 进 → 保留 %d / 不生成 %d · 唯一度 %s(40%% 警 / 30%% 停)· 样板比 %s(>60%% 警)"
         % (st["records_in"], st["records_kept"], st["records_dropped"],
            _pct(st["uniqueness_pct"]), _pct(st["boilerplate_pct"])),
         "axis 组合空间 %s · 近重复对 %d · 警告 %d(100 警 / 500 停)· 词数 min/mean %s/%s"
         % (st["axis_space"], st["near_dup_pairs"], st["warnings"],
            st["word_count_min"], st["word_count_mean"])]
    if rep["stop_items"]:
        L += ["", "### STOP 项(%d)" % len(rep["stop_items"])]
        for s in rep["stop_items"]:
            L.append("- [%s] %s — %s" % (s["kind"], " × ".join(s["keys"]), s["message"]))
        L += ["", "退回数据层记录(%d):%s" % (len(st["return_to_data"]),
                                            ", ".join(st["return_to_data"]) or "-")]
    if rep["warnings"]:
        L += ["", "### WARNING(%d,列前 30)" % len(rep["warnings"])]
        for w in rep["warnings"][:30]:
            L.append("- [%s] %s — %s" % (w["kind"], w.get("key") or "-", w["message"]))
    if rep["dropped_records"]:
        L += ["", "### 不生成记录(%d,列前 30;非 fatal)" % len(rep["dropped_records"])]
        for d in rep["dropped_records"][:30]:
            L.append("- 行 %d %s — %s" % (d["line"], d.get("key") or "-", d["reason"]))
    return "\n".join(L)


# ---------- main ----------

def parse_floors(val):
    floors = dict(PAGE_FLOORS)
    for part in val.split(","):
        t, _, num = part.strip().partition("=")
        try:
            if not t or not num:
                raise ValueError
            floors[t] = int(num)
        except ValueError:
            return None
    return floors


def main():
    args = sys.argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(USAGE)
        return 0
    want = {"--records": None, "--rendered": None}
    as_json = False
    min_quality = MIN_QUALITY
    floors = dict(PAGE_FLOORS)
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--json":
            as_json = True
        elif a in want:
            if i + 1 >= len(args):
                return die("usage 错误:%s 需要一个路径参数(见 --help)" % a)
            want[a] = args[i + 1]
            i += 1
        elif a == "--min-quality":
            if i + 1 >= len(args):
                return die("usage 错误:%s 需要一个数值参数(见 --help)" % a)
            try:
                min_quality = float(args[i + 1])
            except ValueError:
                return die("--min-quality 无法解析: %r" % args[i + 1])
            i += 1
        elif a == "--floor":
            if i + 1 >= len(args):
                return die("usage 错误:%s 需要 type=int,... 参数(见 --help)" % a)
            parsed = parse_floors(args[i + 1])
            if parsed is None:
                return die("--floor 无法解析: %r(期望 product=400,article=800 形态)" % args[i + 1])
            floors = parsed
            i += 1
        else:
            sys.stderr.write("未知参数 %s\n%s\n" % (a, USAGE))
            return 2
        i += 1
    if not want["--records"]:
        sys.stderr.write("需要 --records(批次 JSONL 路径)\n\n" + USAGE + "\n")
        return 2
    if want["--rendered"] and not os.path.isdir(want["--rendered"]):
        return die("--rendered 不是目录: %s" % want["--rendered"])
    records, dropped = load_batch(want["--records"])
    rep = run_gates(records, dropped, rendered=want["--rendered"],
                    min_quality=min_quality, floors=floors)
    if as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(render_markdown(rep))
    return 0 if rep["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
