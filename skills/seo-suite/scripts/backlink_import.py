#!/usr/bin/env python3
"""外链导出统一导入器(BYO 三格式解析器,pipeline-completeness.md R2-3;stdlib-only)。

Ahrefs Backlinks / Semrush Backlinks / GSC Links 三家导出 CSV → 统一 schema:
  {referring_domain, url, dr_or_urgency, anchor, first_seen, last_seen, dofollow, type}
- 格式自动嗅探(列头特征;--format 可显式指定 auto|ahrefs|semrush|gsc|unified);
- 列头变体容错(Referring Page/referring page/DR/Domain Rating/Anchor/Anchor text/
  First Seen/First discovered/Last Checked/Last seen/… 均归一到 canonical 列);
- 分隔符自动检测(逗号/Ahrefs,分号/Semrush 常见,制表符);
- 去重:同一 referring url 只留首行(统计进 dedup_dropped;无 url 的域级行按
  域名+锚文本作 key,不误合并);
- referring_domain 缺列时从 url host 推导(裸注册域,www. 剥离);
- dofollow 值归一(Dofollow/follow/yes/true/1→dofollow;Nofollow/no/false/0→nofollow;
  缺列时从 type 含 nofollow 反推);
- 嗅探/读取失败退出码 2(数据错误,不猜)。

直喂兼容(cite_domain 证据清单思路,同 CITATION_EVIDENCE 的"评级证据字段建议"纪律):
  --json 的 summary.cite_domain_feed 按 cite_domain --input 模板的机判字段一一产出——
    referring_domains   ← 唯一引荐域计数(C1)
    dr_distribution     ← {"0-30","30-50","50-70","70-100"} 计数(C2)
    months              ← first_seen 按月的新链计数(C4 增速平滑度)
    anchor_exact_ratio  ← 需 --brand 给品牌词才计(T2;缺省 null 不猜)
    dofollow_ratio      ← 观测旁证(editorial_ratio 仍需人工判,不冒充)
  即:本工具输出的形状可直接人工拼进 cite_domain answers.json 的对应字段
  (engines_cited/reviews/outbound_links 等三类来源分离字段仍按 cite_domain 的
  provider_citation 口径人工采集,本工具不越界代填)。
  monitor.py 月检(R2-4)同样消费本格式:check_backlinks 直接 import 本模块
  parse_export(),backlinks.csv 放任意一家原始导出或统一格式均可。

用法:
  python3 backlink_import.py export.csv                      # 统一 CSV → stdout
  python3 backlink_import.py export.csv --out unified.csv   # 统一 CSV → 文件
  python3 backlink_import.py export.csv --json payload.json # 结构化 JSON(行+摘要+喂点)
  python3 backlink_import.py export.csv --brand Acme        # 附 anchor_exact_ratio
  python3 backlink_import.py --self-test

退出码:0 正常;2 数据错误(读不了/嗅探不出/无有效行)。
"""
import argparse
import csv
import json
import os
import re
import sys
import tempfile
import traceback
from datetime import date, datetime, timedelta

UNIFIED_FIELDS = ["referring_domain", "url", "dr_or_urgency", "anchor",
                  "first_seen", "last_seen", "dofollow", "type"]

# canonical 列 → 原始列头变体(全部 lowercase+去空格归一后匹配)。
# Ahrefs Backlinks 导出:Referring Page/Domain Rating/First Seen/Last Checked/Anchor/Type;
# Semrush Backlinks 导出(分号分隔常见):Domain/Rating(AS)/Anchor text/Page URL|Link URL/
#   First seen/Last seen/Type/Dofollow;
# GSC Links 导出(简易表):无表头两列(referrer,target)或有 Linking Page/Target 表头。
ALIASES = {
    "url": ("referring page", "referring page url", "url of referring page",
            "referring url", "page url", "source url", "url", "linking page",
            "link url", "ref page", "referrer url", "源页面"),
    "referring_domain": ("referring domain", "referring domains", "ref domain",
                         "ref domains", "domain", "source domain", "linking domain",
                         "target domain", "引荐域"),
    "dr": ("domain rating", "dr", "domainrating", "rating", "authority score", "as",
           "domain authority", "da", "urgency", "dr_or_urgency", "domain score"),
    "anchor": ("anchor", "anchor text", "anchors", "anchor_text", "锚文本"),
    "first_seen": ("first seen", "first_seen", "first discovered", "first detected",
                   "first found", "date detected"),
    "last_seen": ("last seen", "last_seen", "last checked", "last detected",
                  "last updated"),
    "dofollow": ("dofollow", "do follow", "follow", "dofollow /nofollow",
                 "dofollow/nofollow", "dofollow / nofollow", "rel"),
    "type": ("type", "link type", "link_type", "link types", "链接类型"),
}

# 被忽略但属常见导出的列(target 一侧 = 本站页面,不进引荐侧 schema)
_DELIMITERS = (",", ";", "\t")

DOFOLLOW_TRUE = re.compile(r"^(dofollow|follow|yes|true|1)$", re.I)
DOFOLLOW_FALSE = re.compile(r"^(nofollow|no|false|0)$", re.I)


def _norm_col(name):
    """列头归一:strip+BOM+引号+前导 #,lowercase,内部空白折叠。"""
    s = (name or "").strip().lstrip("\ufeff").strip().strip('"').strip()
    if s.startswith("#"):
        s = s[1:].strip()
    return re.sub(r"\s+", " ", s).lower()


def _canonical_map(cols):
    """原始列头列表 → {col_index: canonical};未识别列不入 map(被忽略)。"""
    out = {}
    for i, raw in enumerate(cols):
        n = _norm_col(raw)
        if not n:
            continue
        for canon, variants in ALIASES.items():
            if n in variants:
                out[i] = canon
                break
    return out


def detect_delimiter(header_line):
    """表头行 → 最可能分隔符(切出非空列最多者;平手按 , ; \\t 顺序)。"""
    best, best_n = ",", -1
    for d in _DELIMITERS:
        try:
            fields = next(csv.reader([header_line], delimiter=d))
        except (csv.Error, StopIteration):
            continue
        n = len([f for f in fields if _norm_col(f)])
        if n > best_n:
            best, best_n = d, n
    return best


def sniff_format(cols, delim):
    """归一列头 + 分隔符 → 'unified'|'ahrefs'|'semrush'|'gsc';识别不出抛 ValueError。
    特征优先级:统一 schema(8 列精确特征)> Semrush(分号 + url/域 + DR/锚文本)
    > Ahrefs(Referring Page + Domain Rating/First Seen)> GSC(有 URL 列的简易表)。"""
    raw = {_norm_col(c) for c in cols if _norm_col(c)}
    if set(UNIFIED_FIELDS) <= raw:
        return "unified"
    canon = set(_canonical_map(cols).values())
    if delim == ";" and (canon & {"url", "referring_domain"}) and (canon & {"dr", "anchor"}):
        return "semrush"
    if "url" in canon and (canon & {"dr", "first_seen"}):
        return "ahrefs"
    if canon & {"url", "referring_domain"}:
        return "gsc"
    raise ValueError("无法嗅探导出格式:列头特征不匹配 ahrefs/semrush/gsc/统一 schema(%s)"
                     % ", ".join(sorted(raw))[:200])


def parse_date(value):
    """first_seen/last_seen 值 → date;支持 ISO 前缀/点分/斜杠常见形态;解不出 → None。"""
    s = (value or "").strip()
    if not s:
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)          # 2026-03-15 / ISO 时间戳
    if m:
        y, mo, d = (int(g) for g in m.groups())
    else:
        m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", s)    # 15.03.2026(欧式)
        if m:
            d, mo, y = (int(g) for g in m.groups())
        else:
            m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)   # 3/15/2026 或 15/3/2026
            if not m:
                return None
            a, b, y = (int(g) for g in m.groups())
            d, mo = (a, b) if a > 12 else (b, a)          # 月/日歧义按大数=日
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def parse_dr(value):
    """DR/AS/URGency 值 → 0-100 整数字符串;解不出 → ''。"""
    m = re.search(r"\d+", (value or "").replace(",", "."))
    if not m:
        return ""
    try:
        n = int(float(m.group(0)))
    except ValueError:
        return ""
    return str(min(100, max(0, n)))


def parse_dofollow(value, type_value=""):
    """dofollow 列值(+type 列旁证)→ 'dofollow'|'nofollow'|''(unknown 不猜)。"""
    v = (value or "").strip().lower()
    if DOFOLLOW_TRUE.search(v):
        return "dofollow"
    if DOFOLLOW_FALSE.search(v) or "nofollow" in v:
        return "nofollow"
    t = (type_value or "").strip().lower()
    if "nofollow" in t:
        return "nofollow"
    if "dofollow" in t or "follow" in t:
        return "dofollow"
    return ""


def derive_domain(url):
    """url → 裸注册域(小写,去 www./端口/用户名;两级后缀近似,同 monitor 口径)。"""
    host = re.sub(r"^[a-z][a-z0-9+.-]*://", "", (url or "").strip(), flags=re.I)
    host = host.split("/")[0].split("@")[-1].split(":")[0].strip().lower()
    if host.startswith("www."):
        host = host[4:]
    parts = [p for p in host.split(".") if p]
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _looks_like_url(s):
    return bool(re.match(r"^https?://", (s or "").strip(), re.I))


def parse_export(path, fmt="auto"):
    """导出文件 → {"format", "rows", "input_rows", "dedup_dropped", "bad_rows"}。
    rows 为统一 schema dict 列表(全字段 str,缺失为 "");同一 referring url 去重留首行。
    嗅探失败/无 URL 可用的行 → ValueError(调用方决定退出码/不猜)。"""
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    if not lines:
        raise ValueError("导出文件为空: %s" % path)
    delim = detect_delimiter(lines[0])
    try:
        records = [row for row in csv.reader(lines, delimiter=delim) if row]
    except csv.Error as e:
        raise ValueError("CSV 解析失败(%s, 分隔符 %r): %s" % (path, delim, e))
    header = records[0]
    headerless = _looks_like_url(header[0] if header else "")
    if headerless:
        # GSC Latest links 简易表:无表头,首列=引荐页 URL(其余列=目标页,忽略)
        cmap = {0: "url"}
        sniffed = "gsc"
    else:
        cmap = _canonical_map(header)
        sniffed = sniff_format(header, delim)
    if fmt != "auto" and not headerless:
        sniffed = fmt                                        # 显式指定优先(仍需列可映射)
    if "url" not in cmap.values() and "referring_domain" not in cmap.values():
        raise ValueError("列头无 referring page/domain 可映射(%s)" % ", ".join(
            _norm_col(c) for c in header)[:200])

    rows, seen, dropped, bad = [], {}, 0, 0
    for raw in (records if headerless else records[1:]):
        rec = {f: "" for f in UNIFIED_FIELDS}
        for i, canon in cmap.items():
            field = "dr_or_urgency" if canon == "dr" else canon    # canonical→schema 字段
            if field in rec and i < len(raw):
                rec[field] = (raw[i] or "").strip()
        rec["dr_or_urgency"] = parse_dr(rec["dr_or_urgency"])
        rec["dofollow"] = parse_dofollow(rec["dofollow"], rec["type"])
        if not rec["referring_domain"] and rec["url"]:
            rec["referring_domain"] = derive_domain(rec["url"])
        if not rec["url"] and not rec["referring_domain"]:
            bad += 1                                        # 空 URL 又空域名:坏行不计
            continue
        key = rec["url"] or "dom|%s|%s" % (rec["referring_domain"], rec["anchor"])
        if key in seen:
            dropped += 1
            continue
        seen[key] = True
        rows.append(rec)
    if not rows:
        raise ValueError("无有效数据行(全部缺 referring page/domain)")
    return {"format": sniffed, "rows": rows, "input_rows": len(records) - (0 if headerless else 1),
            "dedup_dropped": dropped, "bad_rows": bad}


def cite_domain_feed(rows, brand=None):
    """统一行 → cite_domain --input 的证据字段(直喂兼容;见模块 docstring)。
    anchor_exact_ratio 需品牌词才计(精确匹配锚=锚文本全等品牌词);months 按
    first_seen 月份计新链数(解不出日期的行不计,不猜)。"""
    domains = {r["referring_domain"] for r in rows if r["referring_domain"]}
    dist = {"0-30": 0, "30-50": 0, "50-70": 0, "70-100": 0}
    months = {}
    anchors = [r["anchor"] for r in rows if r["anchor"]]
    n_df = n_known = 0
    for r in rows:
        if r["dr_or_urgency"]:
            try:
                dr = int(r["dr_or_urgency"])
            except ValueError:
                dr = None
            if dr is not None:
                bucket = "0-30" if dr < 30 else "30-50" if dr < 50 else \
                         "50-70" if dr < 70 else "70-100"
                dist[bucket] += 1
        d = parse_date(r["first_seen"])
        if d:
            months.setdefault(d.strftime("%Y-%m"), 0)
            months[d.strftime("%Y-%m")] += 1
        if r["dofollow"] in ("dofollow", "nofollow"):
            n_known += 1
            n_df += r["dofollow"] == "dofollow"
    ratio = None
    if brand:
        b = str(brand).strip().lower()
        ratio = (sum(1 for a in anchors if a.lower() == b) / len(anchors)) if anchors else None
    return {
        "referring_domains": len(domains),
        "dr_distribution": dist,
        "months": [{"month": m, "links": months[m]} for m in sorted(months)],
        "anchor_exact_ratio": ratio,
        "dofollow_ratio": (n_df / n_known) if n_known else None,
        "note": "直喂 cite_domain --input:referring_domains/dr_distribution/months/"
                "anchor_exact_ratio 字段一一对应;engines_cited/reviews/outbound_links/"
                "editorial_ratio 等仍按 cite_domain 三类来源分离口径人工采集",
    }


def build_payload(input_path, parsed, brand=None):
    return {"tool": "backlink_import.py",
            "input": os.path.abspath(input_path) if input_path else None,
            "format": parsed["format"],
            "input_rows": parsed["input_rows"],
            "dedup_dropped": parsed["dedup_dropped"],
            "bad_rows": parsed["bad_rows"],
            "rows": parsed["rows"],
            "summary": {
                "unique_urls": len(parsed["rows"]),
                "referring_domains": len({r["referring_domain"] for r in parsed["rows"]
                                          if r["referring_domain"]}),
                "cite_domain_feed": cite_domain_feed(parsed["rows"], brand),
            }}


def _write_unified_csv(rows, fh):
    w = csv.DictWriter(fh, fieldnames=UNIFIED_FIELDS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)


def _self_test():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "ahrefs.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write('"#","Referring Page","Domain Rating","First Seen","Last Checked",'
                    '"Anchor","Type"\n'
                    '"1","https://blog.example-a.com/post-1","62","2026-09-03 10:00:00",'
                    '"2026-10-01 10:00:00","best crm tools","Text"\n'
                    '"2","https://news.example-b.org/page","31","2026-08-11",'
                    '"2026-09-30","crm comparison","Nofollow"\n')
        out = parse_export(p)
        assert out["format"] == "ahrefs" and len(out["rows"]) == 2
        r1, r2 = out["rows"]
        assert r1["referring_domain"] == "example-a.com"       # 从 url 推导
        assert (r1["dr_or_urgency"], r2["dr_or_urgency"]) == ("62", "31")
        assert r1["dofollow"] == "" and r2["dofollow"] == "nofollow"  # 无 dofollow 列:type
        # 只反推 nofollow("Text" 不携带 follow 状态 → unknown 不猜;dofollow 需显式列)
        assert parse_date(r1["first_seen"]) == date(2026, 9, 3)

        # 列头变体容错:大小写/空格/别名
        p2 = os.path.join(tmp, "ahrefs_variant.csv")
        with open(p2, "w", encoding="utf-8") as f:
            f.write("referring page url,Domain rating,Anchor Text,first_seen,last seen,dofollow\n"
                    "https://x.example.net/a,88,acme,2026-01-02,2026-02-03,Yes\n")
        out2 = parse_export(p2)
        assert out2["format"] == "ahrefs"
        assert out2["rows"][0]["dr_or_urgency"] == "88"
        assert out2["rows"][0]["dofollow"] == "dofollow"

        # Semrush:分号 + 引号内逗号
        p3 = os.path.join(tmp, "semrush.csv")
        with open(p3, "w", encoding="utf-8") as f:
            f.write("Domain;Rating;Anchor text;Page URL;First seen;Last seen;Type;Dofollow\n"
                    '"shop.example-c.de";45;"acme, inc review";https://shop.example-c.de/reviews;'
                    '2026-07-04;2026-09-28;Text;Yes\n'
                    "forum.example-d.com;12;acme thread;https://forum.example-d.com/t/9;"
                    "15.03.2026;01.10.2026;Text;No\n")
        out3 = parse_export(p3)
        assert out3["format"] == "semrush" and len(out3["rows"]) == 2
        s1 = out3["rows"][0]
        assert s1["anchor"] == "acme, inc review"             # 分号格式内逗号保留
        assert s1["referring_domain"] == "shop.example-c.de" and s1["dr_or_urgency"] == "45"
        assert parse_date(out3["rows"][1]["first_seen"]) == date(2026, 3, 15)

        # GSC 简易表:无表头两列
        p4 = os.path.join(tmp, "gsc.csv")
        with open(p4, "w", encoding="utf-8") as f:
            f.write("https://ref-1.example.com/page,https://www.mysite.com/a\n"
                    "https://ref-2.example.org/x,https://www.mysite.com/b\n")
        out4 = parse_export(p4)
        assert out4["format"] == "gsc"
        assert out4["rows"][0]["referring_domain"] == "example.com"
        assert out4["rows"][0]["dr_or_urgency"] == "" and out4["rows"][0]["first_seen"] == ""

        # 去重:同 referring url 留首行
        p5 = os.path.join(tmp, "dup.csv")
        with open(p5, "w", encoding="utf-8") as f:
            f.write("Referring Page,Anchor\nhttps://d.example.com/p,first\n"
                    "https://d.example.com/p,second\nhttps://e.example.com/q,x\n")
        out5 = parse_export(p5)
        assert len(out5["rows"]) == 2 and out5["dedup_dropped"] == 1
        assert out5["rows"][0]["anchor"] == "first"

        # 嗅探失败
        p6 = os.path.join(tmp, "junk.csv")
        with open(p6, "w", encoding="utf-8") as f:
            f.write("foo,bar,baz\n1,2,3\n")
        try:
            parse_export(p6)
            raise AssertionError("乱表头必须嗅探失败")
        except ValueError:
            pass

        # 直喂摘要
        feed = cite_domain_feed(out["rows"], brand="best crm tools")
        assert feed["referring_domains"] == 2
        assert feed["dr_distribution"] == {"0-30": 0, "30-50": 1, "50-70": 1, "70-100": 0}
        assert feed["months"] == [{"month": "2026-08", "links": 1}, {"month": "2026-09", "links": 1}]
        assert feed["anchor_exact_ratio"] == 0.5
        assert cite_domain_feed(out["rows"])["anchor_exact_ratio"] is None
        assert cite_domain_feed(out4["rows"])["months"] == []   # GSC 无 first_seen 不猜
    # 小函数
    assert parse_dr("DR 77.5") == "77" and parse_dr("") == ""
    assert derive_domain("https://WWW.Example.co.uk:8443/a?b") == "co.uk"  # 两级近似口径
    assert parse_dofollow("TRUE") == "dofollow" and parse_dofollow("", "Image nofollow") == "nofollow"
    assert detect_delimiter("a;b;c") == ";" and detect_delimiter("a,b") == ","
    print("[self-test] PASS backlink_import(ahrefs/semrush/gsc/unified 四格式嗅探+列头变体"
          "+分隔符检测+去重+dofollow 归一+直喂 cite_domain 摘要)")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="外链导出统一导入器(Ahrefs/Semrush/GSC → 统一 schema,R2-3)",
        epilog="嗅探不出格式/读不了文件 → 退出码 2(数据错误,不猜)")
    ap.add_argument("input", nargs="?", help="导出 CSV 路径(或 --self-test)")
    ap.add_argument("--format", dest="fmt", choices=["auto", "ahrefs", "semrush", "gsc", "unified"],
                    default="auto", help="导出格式(默认按列头特征自动嗅探)")
    ap.add_argument("--out", default="", help="统一 CSV 输出路径(缺省打印到 stdout)")
    ap.add_argument("--json", dest="json_out", default="", help="结构化 JSON 输出路径(行+摘要)")
    ap.add_argument("--brand", default="", help="品牌词(计 cite_domain anchor_exact_ratio)")
    ap.add_argument("--self-test", action="store_true", help="离线冒烟自测(不联网)")
    args = ap.parse_args(argv)
    if args.self_test:
        try:
            _self_test()
            return 0
        except Exception:
            traceback.print_exc()
            print("[self-test] FAIL backlink_import")
            return 1
    if not args.input:
        ap.error("需要导出 CSV 路径(或 --self-test)")
    try:
        parsed = parse_export(args.input, fmt=args.fmt)
    except (OSError, ValueError) as e:
        print("错误: %s" % e, file=sys.stderr)
        return 2
    payload = build_payload(args.input, parsed, args.brand or None)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="") as f:
            _write_unified_csv(parsed["rows"], f)
        print("[i] 统一 CSV → %s" % args.out, file=sys.stderr)
    else:
        _write_unified_csv(parsed["rows"], sys.stdout)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print("[i] JSON → %s" % args.json_out, file=sys.stderr)
    s = payload["summary"]
    print("[i] 格式=%s 行 %d(去重 %d,坏行 %d)→ 唯一 URL %d,引荐域 %d"
          % (parsed["format"], parsed["input_rows"], parsed["dedup_dropped"],
             parsed["bad_rows"], s["unique_urls"], s["referring_domains"]), file=sys.stderr)
    print("[i] 直喂 cite_domain: referring_domains=%s, DR50+=%d/%d, months=%s"
          % (s["cite_domain_feed"]["referring_domains"],
             s["cite_domain_feed"]["dr_distribution"]["50-70"]
             + s["cite_domain_feed"]["dr_distribution"]["70-100"],
             sum(s["cite_domain_feed"]["dr_distribution"].values()),
             len(s["cite_domain_feed"]["months"])), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
