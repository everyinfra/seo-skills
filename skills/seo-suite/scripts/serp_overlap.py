#!/usr/bin/env python3
"""SERP 重叠聚类判据器(stdlib)。输入 CSV: keyword,top10 URL(分号分隔),
按四档判据输出:7-10 同文 / 4-6 同簇 / 2-3 互链 / 0-1 分开。
用法: python3 serp_overlap.py input.csv"""
import sys, csv

def jaccard(a, b):
    A, B = set(a), set(b)
    return len(A & B) / len(A | B) if A | B else 0

def main():
    rows = list(csv.reader(open(sys.argv[1], encoding='utf-8-sig')))
    data = {r[0].strip(): [u.strip() for u in r[1].split(";") if u.strip()] for r in rows if len(r) >= 2}
    ks = list(data)
    print(f"{'关键词对':<50}{'共享':<4}{'判据'}")
    for i in range(len(ks)):
        for j in range(i+1, len(ks)):
            a, b = data[ks[i]], data[ks[j]]
            shared = len(set(a) & set(b))
            if shared == 0: continue
            verdict = "同一篇文章" if shared >= 7 else "同簇(一页可服务)" if shared >= 4 else "互链" if shared >= 2 else "分开"
            print(f"{ks[i][:22]} × {ks[j][:22]:<24}{shared:<4}{verdict}")

if __name__ == "__main__": main()
