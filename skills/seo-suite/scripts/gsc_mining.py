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
import sys, csv

EXP_CTR = [(1,.28),(2,.15),(3,.11),(5,.07),(10,.03),(20,.01),(999,.005)]
def expected_ctr(pos):
    for lim, c in EXP_CTR:
        if pos <= lim: return c
    return .005

def parse_ctr(v):
    v = (v or "").strip().replace("%", "")
    try: return float(v)/100 if float(v) > 1 else float(v)
    except ValueError: return 0.0

def read(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    return [{k.strip().lower(): v for k, v in r.items()} for r in rows]

def get(r, *names):
    for n in names:
        for k in r:
            if k.startswith(n): return r[k]
    return ""

def main():
    a = sys.argv[1:]
    decay = "--decay" in a; matrix = "--mode" in a and "matrix" in a
    a = [x for x in a if not x.startswith("--")]
    if decay and len(a) >= 2:
        cur, prev = read(a[0]), read(a[1])
        pc = {}
        for r in prev:
            q = get(r, "query", "top queries")
            pc[q] = pc.get(q, 0) + float(get(r, "clicks") or 0)
        out = []
        for r in cur:
            q = get(r, "query", "top queries")
            c = float(get(r, "clicks") or 0)
            if pc.get(q, 10) >= 10 and pc[q] > 0 and (c - pc[q]) / pc[q] <= -0.25:
                out.append((q, int(pc[q]), int(c), f"{(c-pc[q])/pc[q]:.0%}"))
        out.sort(key=lambda x: x[1]-x[2], reverse=True)
        print("== 流量衰退(28d vs 28d, ≤-25%) ==")
        for q, p, c, d in out[:30]: print(f"{q:<40} {p:>6}→{c:<6} {d}")
        return
    rows = read(a[0])
    if not matrix:
        sd, lw = [], []
        for r in rows:
            try:
                pos = float(get(r, "position")); impr = float(get(r, "impressions"))
                clk = float(get(r, "clicks") or 0); ctr = parse_ctr(get(r, "ctr"))
            except ValueError: continue
            if 5 <= pos <= 20 and impr >= 20: sd.append((get(r, "query"), pos, impr, clk))
            if 11 <= pos <= 20 and impr >= 50:
                gap = expected_ctr(pos) - ctr
                if gap > 0.02: lw.append((get(r, "query"), pos, impr, ctr, gap))
        sd.sort(key=lambda x: -x[2]); lw.sort(key=lambda x: -x[4]*x[2])
        print(f"== striking distance(pos5-20, 曝光≥20): {len(sd)} 词 ==")
        for q, p, i, c in sd[:30]: print(f"{q:<40} pos{p:<5.1f} impr{int(i):<7} clicks{int(c)}")
        print(f"\n== 低CTR机会(期望-实际>2pp): {len(lw)} 词 ==")
        for q, p, i, c, g in lw[:30]: print(f"{q:<40} pos{p:<5.1f} CTR{c:.1%} 差{g:.1%}")
    else:
        byq = {}
        for r in rows:
            q = get(r, "query")
            try: byq.setdefault(q, []).append((get(r, "page"), float(get(r, "position")), float(get(r, "impressions") or 0)))
            except ValueError: pass
        cann = []
        for q, pages in byq.items():
            if len(pages) >= 2 and max(p[2] for p in pages) >= 20:
                tot = sum(p[2] for p in pages)
                wpos = sum(p[1]*p[2] for p in pages)/tot
                cann.append((q, len(pages), wpos))
        cann.sort(key=lambda x: -x[2])
        print(f"== 蚕食(同query≥2页, 加权位次): {len(cann)} 组 ==")
        for q, n, w in cann[:30]: print(f"{q:<40} {n}页 加权pos{w:.1f}")

if __name__ == "__main__": main()
