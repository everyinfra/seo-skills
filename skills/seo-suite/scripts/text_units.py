#!/usr/bin/env python3
"""文本单位换算器:给一段文字按目标市场的计量单位统计(scoring-rubric 市场差异节的执行器)。
用法:python3 text_units.py <market>   (从 stdin 读文本;market ∈ en|zh|ja|th|ko|ru|id)
全角=1、半角=0.5 向上取整(日/韩);泰文按字素近似(基字符+组合标记计 1)。
泰文字素是近似值,不是完整 UAX #29 扩展字素簇实现,与 Intl.Segmenter('th') 可能不一致;
stdlib 没有泰语分词,词数(words)只按空格切。B53(2026-10-21):修前用 unicodedata.combining()
判组合标记,泰文上方元音 U+0E31/U+0E34–0E37、U+0E47、U+0E4C–0E4E 的 combining class 为 0
被当成基字符,U+0E33 SARA AM(SpacingMark)也单独计数,样例比 Intl.Segmenter 多 6 个;
现按 Unicode 类别 M* 与 SpacingMark 并入前字,样例与 Intl.Segmenter grapheme 一致(33)。"""
import sys, unicodedata

def visible_length(t):  # 全角口径
    n = 0.0
    for ch in t:
        n += 1.0 if unicodedata.east_asian_width(ch) in 'WF' else 0.5
    return int(-(-n // 1)) if False else int(n + 0.999)

SPACING_MARKS = {"\u0e33", "\u0eb3"}   # 泰/老挝 SARA AM:Grapheme_Cluster_Break=SpacingMark


def grapheme_approx(t):  # 字素近似:组合符号(Mn/Mc/Me)与 SpacingMark 并入前字,不单独计
    return sum(1 for ch in t
               if unicodedata.category(ch)[0] != "M" and ch not in SPACING_MARKS)

def words(t):
    return len(t.split())

USAGE = """usage: cat text | text_units.py <market>
按目标市场的计量单位统计文本(market ∈ en|zh|ja|th|ko|ru|id);
全角=1、半角=0.5 向上取整(日/韩),泰文按字素近似(基字符+组合标记计 1;
不是完整 UAX #29 实现,与 Intl.Segmenter('th') 可能有出入;stdlib 无泰语分词)。"""

def main():
    a = sys.argv[1:]
    if any(x in ("-h", "--help") for x in a):
        print(USAGE)
        return
    market = a[0] if a and not a[0].startswith("-") else 'en'
    t = sys.stdin.read()
    stats = {'chars': len(t), 'visible_fullwidth': visible_length(t), 'graphemes': grapheme_approx(t), 'words': words(t)}
    unit = {'ja': 'visible_fullwidth', 'ko': 'visible_fullwidth', 'th': 'graphemes', 'zh': 'chars', 'en': 'words', 'ru': 'words', 'id': 'words'}.get(market, 'chars')
    note = "  [近似:字素按组合符号合并估算,非完整 UAX #29;精确值用 Intl.Segmenter('th')]" if unit == 'graphemes' else ""
    print(f"market={market} unit={unit} value={stats[unit]}  (all: {stats}){note}")

if __name__ == "__main__":
    main()
