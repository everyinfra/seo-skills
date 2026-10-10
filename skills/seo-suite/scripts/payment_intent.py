#!/usr/bin/env python3
"""支付即意图标注(stdlib)。stdin 每行一个关键词 → keyword→payment 意图标签表
(意图分类的 payment 维度:命中支付词=高商业交易意图细分)。
词表读 markets.json payment_words:mx=oxxo/efectivo;ar=cuotas/dólar/financiamiento/precio;
co-pe=contra entrega/transferencia;br=pix/boleto/parcelamento(葡语属 pt 市场但按支付区域 BR 标注);
cn=货到付款/分期;mena=cod/الدفع عند الاستلام;generic=free shipping/免费配送 等。
匹配用折叠形(NFKC+İ 修正+casefold+去变音符:dólar≈dolar)。
用法: cat kw.txt | python3 payment_intent.py"""
import sys, os, json, unicodedata

BASE = os.path.dirname(os.path.abspath(__file__))

def fold(s):
    w = unicodedata.normalize("NFKC", s).replace("İ", "i").casefold()
    w = "".join(c for c in unicodedata.normalize("NFD", w) if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", w)

USAGE = """usage: cat kw.txt | payment_intent.py
stdin 每行一个关键词 → payment 意图标签(词表读 markets.json payment_words,含 OXXO/cuotas/Pix/COD…)。"""

def main():
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(USAGE)
        return
    with open(os.path.join(BASE, "markets.json"), encoding="utf-8") as f:
        table = json.load(f)["payment_words"]
    pats, seen = [], set()
    for region, terms in table.items():  # 折叠后同形只保留一个(dólar≈dolar 去重)
        for term in terms:
            ft = fold(term)
            if ft not in seen:
                seen.add(ft)
                pats.append((region, ft, term))
    kws = [ln.strip() for ln in sys.stdin if ln.strip() and not ln.startswith("#")]
    tagged = 0
    for kw in kws:
        fk = fold(kw)
        labels = ["payment:%s:%s" % (region, term) for region, ft, term in pats if ft in fk]
        if labels:
            tagged += 1
        print("%-40s → %s" % (kw, " | ".join(labels) if labels else "-"))
    print("\n%d/%d 关键词带支付意图信号" % (tagged, len(kws)))

if __name__ == "__main__":
    main()
