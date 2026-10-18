#!/usr/bin/env python3
"""GSC 导出挖掘器(stdlib)。从 Search Console 导出的 CSV(无需 API)直接挖:
striking distance(pos 5-20 且曝光≥20)/ quick wins(pos 11-20+曝光≥50+低CTR)/
低 CTR(期望CTR曲线差>2pp)/ 蚕食(同 query ≥2 页)/ 流量衰退(当前28d vs 前28d 两文件)。
用法:
  python3 gsc_mining.py queries.csv [--mode query]        # 单表: Query,Clicks,Impressions,CTR,Position
  python3 gsc_mining.py matrix.csv --mode matrix          # Query,Page,Clicks,Impressions,CTR,Position
  python3 gsc_mining.py cur.csv prev.csv --decay          # 两期对比
CTR 接受 '3.2%' 或 0.032。

────────────────────────────────────────────────────────────────────────────
可代码化规则参考(R3 组深读,2026-10-09;来源与完整语境见
references/research/keyword-intent-taxonomy.md"深读补充"节)——扩本脚本时的判据:

[衰退双口径] ericosiu/ai-marketing-skills content_attack_brief.py:
  28d vs 90d 归一化衰退: c90_norm = clicks_90d * (28/90); 仅 c90_norm > 5 才判;
  衰退 = c28 < c90_norm * 0.7 (即降幅 >30%)。比本脚本 28v28 更平滑(抗单周波动)。

[评分双轴] 同上, Impact(0-10) × Confidence(0-10) = 优先级:
  Impact = 量档(>=10k+3 / >=2k+2 / >=500+1) + CPC档($15+3 / $5+2 / $1+1)
           + 漏斗(BOFU+2 / MOFU+1) + 趋势(trend>50%+2 / >20%+1)
  Confidence = KD档(<=10+4 / <=20+3 / <=35+2 / <=50+1) + 现有位次(<=10+3 / <=30+2 / <=50+1)
               + 主题权威(词落在本站内容指纹主题且计数>5, +2)

[趋势判读] 12 个月量史: 首3月均值 vs 末3月均值 →
  >50% Surging / >20% Rising / >5% Growing / ±5% Stable / >=-20% Declining / 其余 Falling

[漏斗词表] BOFU: agency services hire pricing tools software best vs alternative
  platform cost price company firms consultant consultancy outsource
  MOFU: how to guide strategy examples case study roi tutorial template checklist
  tips framework what is explained overview comparison; 商业/交易意图标志优先于词表

[执行路径分派] KD<=20 且无排名页→全自动新建; 已有页且 KD<=50→全自动刷新;
  KD<=40→半自动(AI 起草+人审); KD<=60→人写 AI 优化; 更高→专家写+外链

[竞品 gap 硬阈值] Ryze competitor-gap: 对手位 <=20 且我 >50/零曝光才算 gap;
  竞品品牌词默认排除(除非做 vs/alternative 页)

[趋势雷达联动] scripts/trend_scout.py 已实现 HN+Reddit 源;Google Trends RSS
  (trends.google.com/trending/rss?geo=US) 与 Brave site:twitter.com 查询可再补两源
────────────────────────────────────────────────────────────────────────────
"""
import sys, csv, json, re

USAGE = """usage: gsc_mining.py queries.csv [--mode query] [--brand REGEX] [--json]   # 单表: Query(或 Top queries),Clicks,Impressions,CTR,Position
       gsc_mining.py matrix.csv --mode matrix [--brand REGEX] [--json]  # Query,Page,Clicks,Impressions,CTR,Position
       gsc_mining.py cur.csv prev.csv --decay [--brand REGEX] [--json]  # 两期对比
GSC 导出挖掘(本套件口径,只用来排序):
  striking distance:排名 5–20、展示 ≥20;
  低 CTR:排名 1–10、展示 ≥50、低于内置期望 CTR 曲线 2 个百分点以上(曲线是本套件口径,不是官方数据);
  蚕食:同一查询 ≥2 个页面且最大展示 ≥20;
  衰退:上期点击 ≥10、本期下降 ≥25%(本期消失的查询按 0 计)。
CTR 接受 '3.2%'(带 % 一律 /100)或小数 0.032。--brand:命中的查询不参与挖掘。
--json: 结构化输出(sections 数组,供 agent 消费)。"""

EXP_CTR = [(1,.28),(2,.15),(3,.11),(5,.07),(10,.03),(20,.01),(999,.005)]
def expected_ctr(pos):
    for lim, c in EXP_CTR:
        if pos <= lim: return c
    return .005

def parse_ctr(v):
    """带 % 的一律 /100(GSC 网页导出 "0.5%" 是 0.005);不带 % 的按小数(API 输出 0.032)。"""
    s = (v or "").strip()
    try:
        return float(s[:-1]) / 100 if s.endswith("%") else float(s)
    except ValueError:
        return 0.0

def read(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    return [{k.strip().lower(): v for k, v in r.items()} for r in rows]

def get(r, *names):
    for n in names:
        for k in r:
            if k.startswith(n): return r[k]
    return ""


def get_query(r):
    """查询列:API 规范化输出是 Query,GSC 网页导出是 Top queries。"""
    return get(r, "query", "top queries")

def main():
    a = sys.argv[1:]
    if any(x in ("-h", "--help") for x in a):
        print(USAGE)
        return
    as_json = "--json" in a
    decay = "--decay" in a; matrix = "--mode" in a and "matrix" in a
    brand = None
    if "--brand" in a:
        i = a.index("--brand")
        if i + 1 >= len(a):
            sys.stderr.write("--brand 需要一个正则\n"); sys.exit(2)
        try:
            brand = re.compile(a[i + 1], re.I)
        except re.error as e:
            sys.stderr.write("--brand 不是合法正则: %s\n" % e); sys.exit(2)
        del a[i:i + 2]
    if "--mode" in a:
        i = a.index("--mode")
        del a[i:i + 2]
    a = [x for x in a if not x.startswith("--")]
    is_brand = (lambda q: bool(brand.search(q))) if brand else (lambda q: False)
    if not a:
        sys.stderr.write(USAGE + "\n")
        sys.exit(2)
    if decay and len(a) >= 2:
        cur, prev = read(a[0]), read(a[1])
        pc, cc = {}, {}
        for r in prev:
            q = get_query(r)
            if is_brand(q): continue
            pc[q] = pc.get(q, 0) + float(get(r, "clicks") or 0)
        for r in cur:
            q = get_query(r)
            if is_brand(q): continue
            cc[q] = cc.get(q, 0) + float(get(r, "clicks") or 0)
        out = []
        for q, p in pc.items():          # 只看上期有的查询:本期新出现的不算衰退;本期消失的按 0 计
            c = cc.get(q, 0.0)
            if p >= 10 and (c - p) / p <= -0.25:
                out.append({"query": q, "prev": int(p), "cur": int(c),
                            "delta": f"{(c-p)/p:.0%}"})
        out.sort(key=lambda x: x["prev"]-x["cur"], reverse=True)
        if as_json:
            print(json.dumps({"schema_version": 1, "mode": "decay", "declined": out[:30]}, ensure_ascii=False, indent=1))
            return
        print("== 流量衰退(28d vs 28d, ≤-25%) ==")
        for o in out[:30]: print(f"{o['query']:<40} {o['prev']:>6}→{o['cur']:<6} {o['delta']}")
        return
    rows = read(a[0])
    if not matrix:
        sd, lw = [], []
        for r in rows:
            try:
                pos = float(get(r, "position")); impr = float(get(r, "impressions"))
                clk = float(get(r, "clicks") or 0); ctr = parse_ctr(get(r, "ctr"))
            except ValueError: continue
            q = get_query(r)
            if is_brand(q): continue
            if 5 <= pos <= 20 and impr >= 20: sd.append((q, pos, impr, clk))
            if 1 <= pos <= 10 and impr >= 50:      # 低 CTR 只在前 10 名有意义:第二页的期望 CTR 只有 1%
                gap = round(expected_ctr(pos) - ctr, 6)   # 取整防浮点:0.07-0.05 不应算成 >0.02
                if gap > 0.02: lw.append((q, pos, impr, ctr, gap))
        sd.sort(key=lambda x: -x[2]); lw.sort(key=lambda x: -x[4]*x[2])
        if as_json:
            print(json.dumps({"schema_version": 1, "mode": "query",
                              "striking_distance": [{"query": q, "pos": p, "impressions": int(i), "clicks": int(c)} for q, p, i, c in sd[:30]],
                              "low_ctr": [{"query": q, "pos": p, "impressions": int(i), "ctr": round(c, 4), "gap": round(g, 4)} for q, p, i, c, g in lw[:30]]},
                             ensure_ascii=False, indent=1))
            return
        print(f"== striking distance(pos5-20, 曝光≥20): {len(sd)} 词 ==")
        for q, p, i, c in sd[:30]: print(f"{q:<40} pos{p:<5.1f} impr{int(i):<7} clicks{int(c)}")
        print(f"\n== 低CTR机会(排名1-10, 期望-实际>2pp): {len(lw)} 词 ==")
        for q, p, i, c, g in lw[:30]: print(f"{q:<40} pos{p:<5.1f} CTR{c:.1%} 差{g:.1%}")
    else:
        byq = {}
        for r in rows:
            q = get_query(r)
            if is_brand(q): continue
            try: byq.setdefault(q, []).append((get(r, "page"), float(get(r, "position")), float(get(r, "impressions") or 0)))
            except ValueError: pass
        cann = []
        for q, pages in byq.items():
            if len(pages) >= 2 and max(p[2] for p in pages) >= 20:
                tot = sum(p[2] for p in pages)
                wpos = sum(p[1]*p[2] for p in pages)/tot
                cann.append({"query": q, "pages": len(pages), "weighted_pos": round(wpos, 1)})
        cann.sort(key=lambda x: -x["weighted_pos"])
        if as_json:
            print(json.dumps({"schema_version": 1, "mode": "matrix", "cannibalization": cann[:30]}, ensure_ascii=False, indent=1))
            return
        print(f"== 蚕食(同query≥2页, 加权位次): {len(cann)} 组 ==")
        for o in cann[:30]: print(f"{o['query']:<40} {o['pages']}页 加权pos{o['weighted_pos']}")

if __name__ == "__main__": main()
