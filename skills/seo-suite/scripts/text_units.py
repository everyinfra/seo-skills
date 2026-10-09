#!/usr/bin/env python3
"""文本单位换算器:给一段文字按目标市场的计量单位统计(scoring-rubric 市场差异节的执行器)。
用法:python3 text_units.py <market>   (从 stdin 读文本;market ∈ en|zh|ja|th|ko|ru|id)
全角=1、半角=0.5 向上取整(日/韩);泰文按字素(grapheme 近似:基字符+组合标记计 1)。"""
import sys, unicodedata

def visible_length(t):  # 全角口径
    n = 0.0
    for ch in t:
        n += 1.0 if unicodedata.east_asian_width(ch) in 'WF' else 0.5
    return int(-(-n // 1)) if False else int(n + 0.999)

def grapheme_approx(t):  # 泰文等组合文字:合并标记不计
    return sum(1 for ch in t if not unicodedata.combining(ch))

def words(t):
    return len(t.split())

market = sys.argv[1] if len(sys.argv) > 1 else 'en'
t = sys.stdin.read()
stats = {'chars': len(t), 'visible_fullwidth': visible_length(t), 'graphemes': grapheme_approx(t), 'words': words(t)}
unit = {'ja': 'visible_fullwidth', 'ko': 'visible_fullwidth', 'th': 'graphemes', 'zh': 'chars', 'en': 'words', 'ru': 'words', 'id': 'words'}.get(market, 'chars')
print(f"market={market} unit={unit} value={stats[unit]}  (all: {stats})")
