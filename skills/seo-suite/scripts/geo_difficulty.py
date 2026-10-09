#!/usr/bin/env python3
"""GEO 绝对难度计算器(stdlib-only)。

公式:score = 0.35·KD + 0.40·median(竞品页 UR) + 0.25·targeting%
(targeting 传 0-1,如 0.3 = 30%。)

band:<40 低 / 40-59 中 / 60-79 高 / ≥80 极高。

客户相对三档(结合 --position / --aio-cited 判定当前档位):
  WON         已 top3 或已被 AI Overviews 引用 → 守住(新鲜度+可引用块+监控份额)
  FOOTHOLD    4-10 位 → 强化 quotable 块/对比表/一手数据,争取 AIO 拉引
  NOT RANKING 未排/11+ → 附差距:达到 --target(默认 60)所需 median UR,
              与 --client-ur 的差值;若 KD+targeting 项已吃满 target 则说明
              UR 单独拉不动,先攻低难度长尾或借高 UR 平台。

用法:
  python3 geo_difficulty.py --kd 45 --ur-median 60 --targeting 0.3
  python3 geo_difficulty.py --kd 45 --ur-median 60 --targeting 0.3 \
      --position 15 --client-ur 55 [--target 60] [--aio-cited]
  python3 geo_difficulty.py --self-test
"""
import argparse
import sys
import traceback

W_KD, W_UR, W_TGT = 0.35, 0.40, 0.25


def compute(kd, ur_median, targeting):
    return W_KD * kd + W_UR * ur_median + W_TGT * (targeting * 100)


def needed_ur(kd, targeting, target):
    """其他两项固定时,达到 target 分所需的 median UR。"""
    return (target - W_KD * kd - W_TGT * targeting * 100) / W_UR


def band(score):
    return ("极高" if score >= 80 else "高" if score >= 60 else
            "中" if score >= 40 else "低")


def tier(position, aio_cited):
    if aio_cited or (position is not None and 1 <= position <= 3):
        return "WON"
    if position is not None and 4 <= position <= 10:
        return "FOOTHOLD"
    return "NOT RANKING"


ADVICE = {
    "WON": "守住:内容新鲜度 + 结构化可引用块 + 持续监控 AIO 引用份额(单次检查=掷硬币)",
    "FOOTHOLD": "强化 quotable 块/对比表/一手数据,补实体信号,争取被 AI Overviews 拉引",
    "NOT RANKING": "先攻低难度长尾建立 topical authority,或借高 UR 平台(目录/评测/UGC)间接进入答案",
}


def render(kd, ur_median, targeting, position, aio_cited, client_ur, target):
    score = compute(kd, ur_median, targeting)
    t = tier(position, aio_cited)
    L = ["== GEO 绝对难度 =="]
    L.append("score = 0.35×KD + 0.40×median竞品UR + 0.25×targeting%")
    L.append("     = 0.35×%.1f + 0.40×%.1f + 0.25×%.0f%%"
             % (kd, ur_median, targeting * 100))
    L.append("     = %.2f + %.2f + %.2f = %.2f  → band: %s"
             % (W_KD * kd, W_UR * ur_median, W_TGT * targeting * 100, score, band(score)))
    L.append("-- 客户相对三档建议 --")
    for name in ("WON", "FOOTHOLD", "NOT RANKING"):
        mark = "→ 当前档位" if name == t else "          "
        cond = {"WON": "top3 或被 AIO 引用", "FOOTHOLD": "4-10 位",
                "NOT RANKING": "未排名/11+"}[name]
        L.append("  %-12.12s(%s)%s" % (name, cond, mark if name == t else ""))
    L.append("  建议: %s" % ADVICE[t])
    if t == "NOT RANKING":
        need = needed_ur(kd, targeting, target)
        L.append("  差距: 达到 target=%.0f 分需 median 竞品 UR ≈ %s"
                 % (target, "%.1f" % need if need > 0 else "0(KD+targeting 项已超 target)"))
        if need <= 0:
            L.append("  [i] KD+targeting 两项已吃满 target 分:UR 单独拉不动,"
                     "换词或先做低难度长尾")
        elif client_ur is not None:
            gap = need - client_ur
            L.append("  差距: 客户当前 UR=%.1f → 还差 %.1f 点 UR 等价物"
                     % (client_ur, gap))
            if gap <= 0:
                L.append("  [i] 客户 UR 已达所需:检查内容可引用性与索引,而非权威度")
    return "\n".join(L)


def _self_test():
    assert abs(compute(45, 60, 0.3) - 47.25) < 1e-9
    assert abs(compute(0, 0, 0.0)) < 1e-9
    assert abs(compute(100, 100, 1.0) - 100.0) < 1e-9
    assert band(39.9) == "低" and band(40) == "中" and band(59.9) == "中"
    assert band(60) == "高" and band(80) == "极高"
    assert tier(1, False) == "WON" and tier(None, True) == "WON"
    assert tier(7, False) == "FOOTHOLD" and tier(4, False) == "FOOTHOLD"
    assert tier(11, False) == "NOT RANKING" and tier(None, False) == "NOT RANKING"
    # needed_ur: target 60, kd 45, targeting 0.3 → (60-15.75-7.5)/0.4 = 91.875
    assert abs(needed_ur(45, 0.3, 60) - 91.875) < 1e-9
    assert needed_ur(100, 1.0, 60) == 0          # KD+targeting 恰好吃满 target
    assert needed_ur(100, 1.0, 55) < 0           # KD+targeting 已超 target
    out = render(45, 60, 0.3, 15, False, 55, 60)
    assert "47.25" in out and "NOT RANKING" in out and "91.9" in out and "36.9" in out
    out2 = render(45, 60, 0.3, 2, False, None, 60)
    assert "WON" in out2 and "当前档位" in out2
    out3 = render(45, 60, 0.3, 7, False, None, 60)
    assert "FOOTHOLD" in out3
    print("[self-test] PASS geo_difficulty(45/60/0.3 → 47.25;三档判定;"
          "needed UR=91.875、差距 36.9;band 边界)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kd", type=float, default=None, help="关键词难度 0-100")
    ap.add_argument("--ur-median", dest="ur_median", type=float, default=None,
                    help="SERP 竞品页 UR 中位数 0-100")
    ap.add_argument("--targeting", type=float, default=None,
                    help="意图匹配度/定位分 0-1(0.3=30%%)")
    ap.add_argument("--position", type=int, default=None, help="客户当前排名(可选)")
    ap.add_argument("--aio-cited", action="store_true", help="客户已被 AIO 引用")
    ap.add_argument("--client-ur", dest="client_ur", type=float, default=None,
                    help="客户页 UR(NOT RANKING 时算差距)")
    ap.add_argument("--target", type=float, default=60.0,
                    help="进攻目标分(默认 60)")
    ap.add_argument("--self-test", action="store_true", help="冒烟自测")
    args = ap.parse_args(argv)
    if args.self_test:
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL geo_difficulty")
            return 1
    if None in (args.kd, args.ur_median, args.targeting):
        ap.error("需要 --kd / --ur-median / --targeting(或 --self-test)")
    if not (0 <= args.kd <= 100 and 0 <= args.ur_median <= 100):
        ap.error("--kd 与 --ur-median 需在 0-100")
    if not (0 <= args.targeting <= 1):
        ap.error("--targeting 需在 0-1(0.3=30%%)")
    print(render(args.kd, args.ur_median, args.targeting, args.position,
                 args.aio_cited, args.client_ur, args.target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
