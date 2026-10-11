#!/usr/bin/env python3
"""market_fit.py — 市场进入决策:优先级矩阵(R3-8,国际化管线"市场决策"缺口的工具化;stdlib only)。
规格:references/overview/pipeline-completeness.md R3-8(GSC 国别流量×markets.json→市场组合
优先级矩阵)+ 国际化审计行(市场决策=纯知识,无工具)。

输入:
  --gsc-country gsc.csv   GSC 按 Country 维度导出(Country,Clicks,Impressions,CTR,Position;
                          utf-8-sig 容 BOM,列头大小写/中文变体容忍)。缺省=无需求数据模式。
  --markets ja,ko,de      候选市场(逗号分隔;缺省=markets.json 全部 18 个)
  --source-lang en        源语言市场码(语言成本=与源语言文字系的距离;默认 en)
  --json                  结构化输出(agent 消费;人读矩阵仍是默认 markdown)

模型(决策支持启发式,各因子证据全部打印,不当真值):
  适配度(0-100)= 需求信号 × 竞争密度 × 语言成本 × 合规成本
  ① 需求信号:该市场国家的现有流量(绝对量分档 0.4-1.0 + 份额 15% 封顶,6:4 加权);
     无 GSC 国别数据→全候选等权 0.5 并显著标注"缺数据按结构因素"(诚实降级,不编数字);
     有数据但该国别无记录→0.1(现有足迹≈0,另挂机会注,零足迹≠零机会)。
  ② 竞争密度:该市场引擎格局复杂度(markets.json engines)——无本地引擎:≤2 家 1.0 /
     ≤4 家 0.9 / 更多答案面 0.8;含本地引擎(naver/baidu/yandex/yahoo-japan/coc-coc 等):
     1 家 0.65 / 2 家 0.55 / ≥3 家 0.50(韩日俄中"独立学科"),并注明生态位(本地引擎
     外站竞争密度低、引用池本地化——减分在复杂度,不在机会)。
  ③ 语言成本:与源语言文字系距离的内容产能假设(latin 同系 1.0;→cyrillic 0.6;
     →han/hangul/devanagari 0.35-0.40;→thai/arabic 0.30 无空格分词/RTL 全链另注;
     zh↔ja 汉字共享 0.60)。RTL/全角/字素/换行切句等标注从 markets.json 阈值单位推导。
  ④ 合规成本:扫 markets.json 该市场 special_checks+notes+formality 文本,按合规
     关键词模式(Bill 96/OQLF、152-ФЗ、备案、GAMR/TDRA、LGPD、PDPA、PIPA、
     景表法/ステマ規制、Impressum/DDG/Abmahnung、CONAR)罚分——事实留在 markets.json,
     本脚本只持模式(数据与逻辑分离:markets.json 删掉某合规事实,罚分自动消失)。

输出:优先级矩阵(推荐进入 Top3 + 暂缓及理由)+ 因子证据 + 机会注(小语种唯一源红利,
引 references/research/multilingual-geo-evidence.md U5)。

用法: python3 market_fit.py [--gsc-country gsc.csv] [--markets ja,ko,de] [--source-lang en] [--json]
退出码: 0 正常(决策支持,非闸门;暂缓不是失败) / 2 输入或用法错。"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_VERSION = 1

# GSC Country 维度导出为英文国名 → 市场码(主归属;混语国见 AMBIGUOUS_NOTES,
# 未映射国家不丢弃——进"未映射"清单由人裁决)
COUNTRY_MARKET = {
    "ja": ("Japan",),
    "ko": ("South Korea", "Korea", "Republic of Korea"),
    "zh": ("China", "Taiwan", "Hong Kong", "Macau"),
    "de": ("Germany", "Austria", "Switzerland", "Liechtenstein"),
    "fr": ("France", "Belgium", "Monaco", "Luxembourg"),
    "es": ("Spain", "Mexico", "Argentina", "Colombia", "Chile", "Peru", "Venezuela",
           "Ecuador", "Guatemala", "Cuba", "Bolivia", "Uruguay", "Paraguay",
           "Costa Rica", "Panama", "Honduras", "El Salvador", "Nicaragua",
           "Dominican Republic", "Puerto Rico"),
    "pt": ("Brazil", "Portugal", "Angola", "Mozambique"),
    "ru": ("Russia", "Kazakhstan", "Belarus", "Uzbekistan", "Kyrgyzstan"),
    "it": ("Italy", "San Marino", "Vatican City"),
    "tr": ("Turkey", "Türkiye"),
    "pl": ("Poland",),
    "nl": ("Netherlands",),
    "id": ("Indonesia",),
    "vi": ("Vietnam",),
    "th": ("Thailand",),
    "hi": ("India", "Nepal", "Bhutan"),
    "en": ("United States", "United Kingdom", "Canada", "Australia", "Ireland",
           "New Zealand", "South Africa"),
    "ar": ("Saudi Arabia", "Egypt", "United Arab Emirates", "Morocco", "Algeria",
           "Tunisia", "Jordan", "Qatar", "Kuwait", "Oman", "Bahrain", "Iraq",
           "Lebanon", "Libya", "Sudan", "Yemen"),
}
AMBIGUOUS_NOTES = (
    "Canada→en(英语多数;fr-CA 义务按 Bill 96 域内处理,不靠流量归属)",
    "Switzerland→de / Belgium→fr(多语国按最大语区归属,另一语区流量被低估)",
    "India→hi(与 en-IN 混流,国别口径不可拆;真实查询量在 Hinglish)",
    "Singapore 等中英混市未映射(进未映射清单人工裁决)",
)

# 引擎格局:本地引擎=独立索引/独立站长生态(非 Google 索引复用)
LOCAL_ENGINES = {"baidu", "sogou", "quark", "yuanbao", "doubao", "naver", "daum",
                 "naver-ai-briefing", "yandex", "alice", "neuro", "dzen",
                 "yahoo-japan", "coc-coc", "yazeka"}

# 文字系(语言成本=产能假设:翻译+审校+格式规范的全链人力)
SCRIPT_OF = {"en": "latin", "de": "latin", "fr": "latin", "es": "latin", "pt": "latin",
             "it": "latin", "nl": "latin", "pl": "latin", "tr": "latin", "id": "latin",
             "vi": "latin", "ru": "cyrillic", "zh": "han", "ja": "jamix",
             "ko": "hangul", "hi": "devanagari", "th": "thai", "ar": "arabic"}
# (源文字系, 目标文字系) → 产能系数(1=同系可直迁;越低越贵)。未列的跨系组合默认 0.35
PAIR_COST = {
    ("latin", "cyrillic"): 0.60, ("cyrillic", "latin"): 0.70,
    ("latin", "han"): 0.35, ("han", "latin"): 0.50,
    ("latin", "hangul"): 0.40, ("hangul", "latin"): 0.50,
    ("latin", "devanagari"): 0.40, ("devanagari", "latin"): 0.50,
    ("latin", "thai"): 0.30, ("thai", "latin"): 0.40,
    ("latin", "arabic"): 0.30, ("arabic", "latin"): 0.40,
    ("han", "jamix"): 0.60, ("jamix", "han"): 0.60,       # zh↔ja 汉字共享,假名/敬语另学
    ("han", "hangul"): 0.45, ("hangul", "han"): 0.50,     # 汉字词共享
}

# 合规关键词模式(事实在 markets.json;模式只负责识别在场)→ (regex, 标签, 罚分)
COMPLIANCE_PATTERNS = [
    (r"Bill 96|OQLF", "Bill 96/OQLF(fr-CA 法语义务+罚则)", 0.25),
    (r"152-ФЗ|Metrica", "152-ФЗ 数据本地化(GA 实际不可用)", 0.25),
    (r"备案", "ICP 备案(空壳备案清理常态化)", 0.25),
    (r"GAMR|TDRA|UAE 广告主许可证|AED 10", "海湾广告主许可证(GAMR/TDRA)", 0.20),
    (r"LGPD", "LGPD 选择加入同意", 0.15),
    (r"PDPA", "PDPA 明示同意", 0.15),
    (r"PIPA", "PIPA cookie 同意+跨境披露", 0.15),
    (r"景表法|ステマ規制", "景表法/ステマ規制(广告与评价规制)", 0.15),
    (r"Impressum|DDG|Abmahnung", "Impressum(§5 DDG)+Abmahnung 风险", 0.15),
    (r"CONAR|publieditorial", "CONAR 软文披露", 0.10),
]
U5_REF = "references/research/multilingual-geo-evidence.md U5"


class UsageError(Exception):
    """输入/用法错(退出码 2)。"""


def load_markets():
    with open(os.path.join(BASE, "markets.json"), encoding="utf-8") as f:
        return json.load(f)["markets"]


def parse_gsc_country(path):
    """GSC Country 维度导出 → ({国名: {clicks, impressions}}, 总点击, 总展示)。"""
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    except OSError as e:
        raise UsageError("GSC 国别导出不可读: %s" % e)
    if not rows:
        raise UsageError("GSC 国别导出为空(须含表头行 Country,Clicks,Impressions,…)")
    keys = [k for k in (rows[0].keys() or []) if k]
    ccol = next((k for k in keys if k.strip().lower() in ("country", "countries", "国家")), None)
    if not ccol:
        raise UsageError("GSC 国别导出缺 Country 列;实际列: %s" % ", ".join(keys))
    kcol = next((k for k in keys if k.strip().lower() in ("clicks", "点击量", "点击")), None)
    icol = next((k for k in keys if k.strip().lower() in ("impressions", "展示次数", "展示")), None)
    by, tc, ti = {}, 0, 0
    for r in rows:
        name = (r.get(ccol) or "").strip()
        if not name:
            continue

        def num(col):
            v = (r.get(col) or "").strip().replace(",", "")
            try:
                return int(float(v)) if v else 0
            except ValueError:
                return 0
        clicks = num(kcol) if kcol else 0
        impr = num(icol) if icol else 0
        agg = by.setdefault(name, {"clicks": 0, "impressions": 0})
        agg["clicks"] += clicks
        agg["impressions"] += impr
        tc += clicks
        ti += impr
    return by, tc, ti


def demand_factor(market, by_country, total_clicks, has_gsc):
    """①需求信号:现有该国流量占比与绝对量;无 GSC→等权 0.5(缺数据按结构因素)。"""
    if not has_gsc:
        return {"score": 0.5, "neutral": True,
                "evidence": "无 GSC 国别数据——等权 0.5(缺数据按结构因素)", "clicks": None,
                "impressions": None, "share": None, "countries": [], "no_evidence": False}
    want = COUNTRY_MARKET.get(market, ())
    hits = sorted(c for c in want if c in by_country)
    clicks = sum(by_country[c]["clicks"] for c in hits)
    impr = sum(by_country[c]["impressions"] for c in hits)
    share = (clicks / total_clicks) if total_clicks else 0.0
    if not hits:
        return {"score": 0.1, "neutral": False, "no_evidence": True,
                "evidence": "国别无记录(现有足迹≈0;见机会注)", "clicks": 0, "impressions": 0,
                "share": 0.0, "countries": []}
    if clicks >= 1000:
        abs_s = 1.0
    elif clicks >= 200:
        abs_s = 0.85
    elif clicks >= 50:
        abs_s = 0.70
    elif clicks >= 10:
        abs_s = 0.55
    elif clicks >= 1:
        abs_s = 0.40
    else:
        abs_s = 0.25 if impr > 0 else 0.15     # 零点击但有曝光=需求存在的弱证据
    share_s = min(1.0, share / 0.15)
    score = round(0.6 * abs_s + 0.4 * share_s, 3)
    ev = "点击 %d(份额 %.1f%%,曝光 %d;计入国家 %s)" % (
        clicks, share * 100, impr, "+".join(hits) if hits else "—")
    return {"score": score, "neutral": False, "no_evidence": False, "evidence": ev,
            "clicks": clicks, "impressions": impr, "share": round(share, 4),
            "countries": hits}


def competition_factor(cfg):
    """②竞争密度:引擎格局复杂度(本地引擎减分但注明生态位)。"""
    engines = list(cfg.get("engines", []))
    local = [e for e in engines if e in LOCAL_ENGINES]
    if not local:
        if len(engines) <= 2:
            score, note = 1.0, "Google 主导(%s)——经典 SEO/内容打法可迁移" % "+".join(engines)
        elif len(engines) <= 4:
            score = 0.9
            note = "Google 主导+%d 个答案面(%s)——答案层逐个验证" % (len(engines), "+".join(engines))
        else:
            score = 0.8
            note = "%d 个答案面(%s)——AI 引用/答案层逐个验证,维护面大" % (len(engines), "+".join(engines))
    else:
        score = 0.65 if len(local) == 1 else (0.55 if len(local) == 2 else 0.50)
        note = ("本地引擎 %s(%s)——独立学科:多引擎生态要单独投入;但生态位在:外站竞争密度低、"
                "引用池本地化(如 Naver 生态/Alice 取自然 top-10)" % ("+".join(local), "+".join(engines)))
    return {"score": score, "engines": engines, "local_engines": local, "evidence": note}


def language_factor(market, cfg, source_lang):
    """③语言成本:与源语言文字系距离(内容产能假设,非难度定论)。"""
    src_f, tgt_f = SCRIPT_OF.get(source_lang), SCRIPT_OF.get(market)
    if src_f == tgt_f:
        score = 1.0
        base = "同文字系(%s→%s)——翻译+人审产能可直迁" % (src_f, tgt_f)
    else:
        score = PAIR_COST.get((src_f, tgt_f), 0.35)
        base = "文字系距离 %s→%s(系数 %.2f;产能假设=翻译+审校+格式规范全链)" % (src_f, tgt_f, score)
    assumptions = []
    if cfg.get("direction") == "rtl":
        assumptions.append("RTL 全链(dir/逻辑 CSS/镜像布局)")
    tl, dl = cfg.get("title_limit", {}), cfg.get("desc_limit", {})
    if "fullwidth" in (tl.get("unit"), dl.get("unit")):
        assumptions.append("全角阈值规范(ja/ko 口径)")
    if "grapheme" in (tl.get("unit"), dl.get("unit")):
        assumptions.append("字素计数(th 无词间空格)")
    if cfg.get("sentence_split") == "newline":
        assumptions.append("无空格分词(Intl.Segmenter 前置)")
    return {"score": score, "source_script": src_f, "target_script": tgt_f,
            "evidence": base + (";" + ";".join(assumptions) if assumptions else ""),
            "assumptions": assumptions}


def compliance_factor(cfg):
    """④合规成本:扫 markets.json 文本按关键词模式罚分(事实留在 markets.json)。"""
    text = " ".join(cfg.get("special_checks", [])) + " " + cfg.get("notes", "") \
        + " " + cfg.get("formality", "")
    flags = [(label, pen) for pat, label, pen in COMPLIANCE_PATTERNS if re.search(pat, text)]
    score = max(0.4, round(1.0 - sum(p for _, p in flags), 2))
    ev = ";".join(l for l, _ in flags) if flags else "markets.json 未见合规关键词(成本≈0)"
    return {"score": score, "flags": [l for l, _ in flags], "evidence": ev}


def evaluate(candidates, markets, by_country, total_clicks, has_gsc, source_lang):
    rows, unmapped = [], []
    mapped = set()
    for m, cs in COUNTRY_MARKET.items():
        mapped.update(cs)
    if has_gsc:
        unmapped = sorted(set(by_country) - mapped)
    for m in candidates:
        cfg = markets[m]
        d = demand_factor(m, by_country, total_clicks, has_gsc)
        c = competition_factor(cfg)
        l = language_factor(m, cfg, source_lang)
        p = compliance_factor(cfg)
        fit = round(d["score"] * c["score"] * l["score"] * p["score"] * 100, 1)
        rows.append({"market": m, "fit": fit, "demand": d, "competition": c,
                     "language": l, "compliance": p})
    rows.sort(key=lambda r: (-r["fit"], r["market"]))
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        r["verdict"] = "进入" if i < 3 else "暂缓"
        if i >= 3:
            facs = {"需求": r["demand"], "竞争": r["competition"],
                    "语言": r["language"], "合规": r["compliance"]}
            weakest = min(facs, key=lambda k: facs[k]["score"])
            r["reason"] = "%s是最短板(%.2f):%s" % (weakest, facs[weakest]["score"],
                                                  facs[weakest]["evidence"])
        else:
            r["reason"] = "Top3:需求 %.2f × 竞争 %.2f × 语言 %.2f × 合规 %.2f" % (
                d_score(r, "demand"), d_score(r, "competition"),
                d_score(r, "language"), d_score(r, "compliance"))
    return rows, unmapped


def d_score(row, key):
    return row[key]["score"]


def opportunity_notes(rows, has_gsc):
    notes = []
    if has_gsc:
        zero = [r["market"] for r in rows if r["demand"].get("no_evidence")]
        for m in zero:
            notes.append("%s 国别无流量记录——零足迹≠零机会:小语种引用池小而浅,原创数据/深度页"
                         "可成整池唯一可用源(唯一源红利>堆反链,%s)" % (m, U5_REF))
        if not zero:
            notes.append("全部候选均有国别足迹;新市场进入仍适用唯一源红利选题法(%s)" % U5_REF)
    else:
        notes.append("无 GSC 国别数据,零足迹市场不可判;补 --gsc-country 后小语种候选适用"
                     "唯一源红利选题法(%s)" % U5_REF)
    return notes


def render_markdown(rows, unmapped, notes, opts, has_gsc, total_clicks, n_countries, source_lang):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if has_gsc:
        basis = ("GSC 国别导出 `%s`(总点击 %d / 国家 %d 个);源语言 %s" %
                 (opts.gsc_country, total_clicks, n_countries, source_lang))
    else:
        basis = "未提供 GSC 国别导出——需求信号全候选等权 0.5,缺数据按结构因素(竞争/语言/合规)"
    L = ["# 市场进入优先级矩阵 — %d 候选(源语言 %s,%s)" % (len(rows), source_lang, now),
         "",
         "数据基线: %s" % basis,
         "模型: 适配度 = 需求信号 × 竞争密度 × 语言成本 × 合规成本(0-100;决策支持启发式,因子证据见下)",
         "",
         "| 优先 | 市场 | 适配度 | 需求 | 竞争 | 语言 | 合规 | 判定 | 关键理由 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| %d | %s | %.1f | %.2f | %.2f | %.2f | %.2f | %s | %s |" % (
            r["rank"], r["market"], r["fit"], r["demand"]["score"], r["competition"]["score"],
            r["language"]["score"], r["compliance"]["score"], r["verdict"], r["reason"]))
    L += ["", "推荐进入(Top 3): %s" % " / ".join(r["market"] for r in rows[:3]),
          "暂缓: %s" % (";".join("%s(%s)" % (r["market"], r["reason"][:40] + ("…" if len(r["reason"]) > 40 else ""))
                                 for r in rows[3:]) or "—"),
          "", "## 因子证据", ""]
    for r in rows:
        L.append("- **%s**:需求 %s | 竞争 %s | 语言 %s | 合规 %s" % (
            r["market"], r["demand"]["evidence"], r["competition"]["evidence"],
            r["language"]["evidence"], r["compliance"]["evidence"]))
    L += ["", "## 机会注", ""]
    L += ["- %s" % n for n in notes]
    if unmapped:
        L += ["", "未映射国家(不丢弃,人工裁决): %s" % ", ".join(unmapped[:10])]
    L += ["", "国别口径注记: %s" % " / ".join(AMBIGUOUS_NOTES),
          "下一步: 进入市场 → market_batch.py 批量 lint+占位监控;hreflang_cluster.py 校验区域码。",
          "复测纪律: 因子证据半衰期随 markets.json 复审轮更新(review_cycle);决策月度重跑。"]
    return "\n".join(L)


def build_json(rows, unmapped, notes, opts, has_gsc, total_clicks, n_countries, source_lang, markets):
    return {
        "tool": "market_fit.py", "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_lang": source_lang,
        "demand_basis": ("gsc-country:%s" % opts.gsc_country) if has_gsc else "structural-only(缺数据按结构因素)",
        "candidates": [r["market"] for r in rows],
        "gsc": {"file": opts.gsc_country if has_gsc else None,
                "total_clicks": total_clicks if has_gsc else None,
                "countries_seen": n_countries if has_gsc else None,
                "unmapped_countries": unmapped},
        "markets": [{"market": r["market"], "fit": r["fit"], "verdict": r["verdict"],
                     "rank": r["rank"], "reason": r["reason"],
                     "factors": {"demand": r["demand"], "competition": r["competition"],
                                 "language": r["language"], "compliance": r["compliance"]}}
                    for r in rows],
        "recommended": [{"market": r["market"], "fit": r["fit"]} for r in rows[:3]],
        "deferred": [{"market": r["market"], "fit": r["fit"], "reason": r["reason"]}
                     for r in rows[3:]],
        "opportunity_notes": notes,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gsc-country", help="GSC 按 Country 维度导出 CSV(缺省=结构因素模式)")
    ap.add_argument("--markets", help="候选市场逗号分隔(缺省=markets.json 全部市场)")
    ap.add_argument("--source-lang", default="en", help="源语言市场码(语言成本基准,默认 en)")
    ap.add_argument("--json", action="store_true", help="结构化输出")
    ns = ap.parse_args(argv)

    markets = load_markets()
    if ns.markets:
        cands = [c.strip() for c in ns.markets.split(",") if c.strip()]
        if not cands:
            print("market_fit.py: --markets 为空(逗号分隔市场码,如 ja,ko,de)", file=sys.stderr)
            return 2
    else:
        cands = sorted(markets)
    bad = [c for c in cands if c not in markets]
    if bad:
        print("market_fit.py: 未知市场 %s;可用: %s" % (",".join(bad), ", ".join(sorted(markets))),
              file=sys.stderr)
        return 2
    if ns.source_lang not in markets:
        print("market_fit.py: 未知 --source-lang %s;可用: %s"
              % (ns.source_lang, ", ".join(sorted(markets))), file=sys.stderr)
        return 2

    has_gsc = ns.gsc_country is not None
    by_country, total_clicks, _ti = ({}, 0, 0)
    if has_gsc:
        by_country, total_clicks, _ti = parse_gsc_country(ns.gsc_country)

    rows, unmapped = evaluate(cands, markets, by_country, total_clicks, has_gsc, ns.source_lang)
    notes = opportunity_notes(rows, has_gsc)
    if ns.json:
        print(json.dumps(build_json(rows, unmapped, notes, ns, has_gsc, total_clicks,
                                    len(by_country), ns.source_lang, markets),
                         ensure_ascii=False, indent=1))
    else:
        print(render_markdown(rows, unmapped, notes, ns, has_gsc, total_clicks,
                              len(by_country), ns.source_lang))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except UsageError as e:
        print("market_fit.py: %s" % e, file=sys.stderr)
        sys.exit(2)
