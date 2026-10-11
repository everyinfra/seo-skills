#!/usr/bin/env python3
"""BYO(自带数据)解析归一入口(pipeline-completeness R2-6,stdlib only)。
把第三方工具导出的三种常见 CSV 归一成统一 schema,消灭"每工具一格式"的手工搬运:
  --kind frog  Screaming Frog internal.csv 导出(千列全量只取常用 20 列)
  --kind serp  SERP top10 导出(各工具逗号/分号混杂的长表或宽表)→ query,url,position
  --kind kws   关键词表 kws.csv(keyword,search_volume,position[,cpc,kd] 变体)
--kind 省略时自动嗅探(按表头特征判 frog→kws→serp;判不出 exit 2)。
列头容错:大小写/前后空格/全半角(NFKC)/SF 数字后缀(Title 1/H1-1/Meta Description 1)
/同义词(Search Volume/Volume/Qty、Position/Rank/排名 等)。
frog 输出直接可喂 site_audit --json 的消费思路(做为批量审计的 URL 清单与预取元数据源):
  python3 byo_import.py internal.csv --kind frog --urls-only \
    | xargs python3 scripts/site_audit.py --market de --json
  即:--urls-only 产一行一 URL 的清单充当 site_audit 的多 URL 入参(批量审计免逐页粘贴);
  归一 CSV 的 status_code/title/meta_description/canonical/word_count 等预取元数据可
  与审计 findings 按地址连接对照(爬虫已抓过的元数据不再二次抓取,离线复核 title 超限/
  canonical 异常/字数分布),--json 汇总供 agent 编排消费。
用法: python3 byo_import.py INPUT [--kind frog|serp|kws] [--out FILE] [--urls-only] [--json]
退出码: 0 成功(行数≥0 皆可);2 输入不可读/格式嗅探失败/必需列缺失/未知 --kind。"""
import csv
import io
import json
import re
import sys
import unicodedata

SCHEMA_VERSION = 1
BASE = __file__

# ---- 三种格式的规范化输出列(fixed schema,缺列输出空值) ----
FROG_COLS = ["address", "status_code", "status_message", "content_type", "title",
             "meta_description", "h1", "h2", "canonical", "meta_robots", "word_count",
             "text_ratio", "crawl_depth", "inlinks", "outlinks", "external_outlinks",
             "response_time", "last_modified", "indexability", "indexability_status"]
SERP_COLS = ["query", "url", "position"]
KWS_COLS = ["keyword", "search_volume", "position", "cpc", "kd"]

# ---- 列头同义词表(键=归一化表头:小写+非字母数字→空格+去尾部纯数字 token) ----
_FROG_SYN = {
    "address": ["address", "url", "page", "page url", "网页地址"],
    "status_code": ["status code", "status", "http status", "response status", "状态码"],
    "status_message": ["status message", "status text", "状态消息"],
    "content_type": ["content type", "content", "mime type", "类型"],
    "title": ["title", "page title", "html title", "标题"],
    "meta_description": ["meta description", "meta desc", "description", "描述"],
    "h1": ["h1"], "h2": ["h2"],
    "canonical": ["canonical link element", "canonical", "canonical url", "rel canonical"],
    "meta_robots": ["meta robots", "robots", "robots tag"],
    "word_count": ["word count", "words", "text words", "词数"],
    "text_ratio": ["text ratio", "text to html ratio"],
    "crawl_depth": ["crawl depth", "depth", "深度"],
    "inlinks": ["inlinks", "in links", "internal inlinks", "入链"],
    "outlinks": ["outlinks", "out links", "internal outlinks", "出链"],
    "external_outlinks": ["external outlinks", "ext outlinks"],
    "response_time": ["response time", "response time ms", "响应时间"],
    "last_modified": ["last modified", "last modified date", "最后修改"],
    "indexability": ["indexability", "indexable"],
    "indexability_status": ["indexability status", "indexability reason"],
}
_QUERY_SYN = {"query": ["query", "keyword", "keywords", "search term", "term", "关键词", "搜索词", "查询词"]}
_URL_SYN = {"url": ["url", "urls", "link", "result url", "result", "ranking url", "top url",
                    "top urls", "top 10 url", "top 10 urls", "serp urls", "landing page", "页面", "网址"]}
_POS_SYN = {"position": ["position", "pos", "rank", "ranking", "serp position", "排名", "位置"]}
_KWS_SYN = {
    "keyword": ["keyword", "keywords", "query", "search term", "term", "关键词", "搜索词"],
    "search_volume": ["search volume", "volume", "volumes", "avg monthly searches",
                      "monthly volume", "msv", "qty", "quantity", "搜索量", "月搜索量"],
    "position": ["position", "pos", "rank", "ranking", "current position", "排名"],
    "cpc": ["cpc", "avg cpc", "top of page bid", "click price"],
    "kd": ["kd", "keyword difficulty", "difficulty", "competition", "seo difficulty", "竞争度", "难度"],
}
SYNONYMS = {"frog": _FROG_SYN, "serp": {**_QUERY_SYN, **_URL_SYN, **_POS_SYN},
            "kws": _KWS_SYN}


def norm_header(h):
    """表头归一:NFKC(全半角)→小写→非字母数字(CJK 保留)→空格→去尾部纯数字 token(SF 的 Title 1/H1-1)。"""
    h = unicodedata.normalize("NFKC", h or "").lower()
    toks = [t for t in re.split(r"[^0-9a-z\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+", h) if t]
    if len(toks) > 1 and toks[-1].isdigit():
        toks = toks[:-1]
    return " ".join(toks)


def build_lookup(kind):
    """归一化表头 → 规范列名(含同义词);后写入者优先(具体同义词覆盖宽泛同义词)。"""
    lk = {}
    for canon, names in SYNONYMS[kind].items():
        for n in names:
            lk[norm_header(n)] = canon
    return lk


def map_headers(headers, kind):
    """表头列表 → {列序号: 规范列名};重复命中取首个(多余重复列忽略)。"""
    lk = build_lookup(kind)
    out = {}
    for i, h in enumerate(headers):
        c = lk.get(norm_header(h))
        if c and c not in out.values():
            out[i] = c
    return out


def _count_outside_quotes(line, d):
    """统计分隔符 d 在引号外出现的次数(CSV 引号内的另一分隔符不算证据;"" 双写按进出各一次抵消)。"""
    n = inq = 0
    for ch in line:
        if ch == '"':
            inq = not inq
        elif ch == d and not inq:
            n += 1
    return n


def detect_delimiter(text):
    """delimiter 嗅探:前 5 个非空行按候选(逗号/分号/制表符)计引号外出现数,
    取众数计数为主分(列数证据多者优先)、行间一致性为次分——兼容分号 locale 导出、
    表头无 delimiter 线索的宽表(query 单列表头)与引号内夹另一分隔符的常规 CSV。"""
    lines = [ln for ln in text.splitlines() if ln.strip()][:5]
    best, best_score = ",", (-1, -1.0)
    for d in (",", ";", "\t"):
        counts = [_count_outside_quotes(ln, d) for ln in lines]
        if not any(counts):
            continue
        mode = max(sorted(set(counts)), key=lambda c: (counts.count(c), c))
        score = (mode, counts.count(mode) / len(counts))
        if score > best_score:
            best, best_score = d, score
    return best


def read_rows(path):
    """读任意分隔符 CSV → (表头 list, 行 list);BOM 容错,空行剔除。"""
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            text = f.read()
    except OSError as e:
        sys.stderr.write("[ERROR] 输入不可读 %s: %s\n" % (path, e))
        raise SystemExit(2)
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=detect_delimiter(text)) if r]
    if not rows:
        sys.stderr.write("[ERROR] %s 无有效数据行\n" % path)
        raise SystemExit(2)
    return rows[0], rows[1:]


# ---- 嗅探(frog → kws → serp;判定特征从特异到宽泛) ----

def sniff_kind(headers):
    ns = {norm_header(h) for h in headers}
    def hit(kind, canon):
        return any(norm_header(n) in ns for n in SYNONYMS[kind][canon])
    if hit("frog", "address") and (hit("frog", "indexability")
                                   or (hit("frog", "status_code") and hit("frog", "inlinks"))):
        return "frog"
    if hit("kws", "keyword") and hit("kws", "search_volume"):
        return "kws"
    if hit("serp", "query") and hit("serp", "url"):
        return "serp"
    return None


URL_TOKEN_RE = re.compile(r"^[\w.-]+\.[a-z]{2,}([/?#][^\s]*)?$|^https?://", re.I)


def split_url_cell(value):
    """宽表 URL 串(u1;u2;u3 / u1, u2 / 空白分隔)→ URL 列表。"""
    toks = [t.strip() for t in re.split(r"[;,\s]+", value or "") if t.strip()]
    return [t for t in toks if URL_TOKEN_RE.match(t)]


def normalize_volume(v):
    """搜索量归一:去千分位(逗号/空格/窄 nbsp)→纯数字串;解析失败保留原值(去空白)。"""
    s = re.sub(r"[\s,\u00a0\u202f]", "", (v or "").strip())
    return s if re.fullmatch(r"\d+(?:\.\d+)?", s) else (v or "").strip()


def convert_frog(headers, rows):
    m = map_headers(headers, "frog")
    need = {"address"}
    missing = sorted(need - set(m.values()))
    if missing:
        sys.stderr.write("[ERROR] frog 格式缺必需列: %s(表头: %s)\n" % (", ".join(missing), ", ".join(headers)))
        raise SystemExit(2)
    out, skipped = [], 0
    for r in rows:
        rec = {c: "" for c in FROG_COLS}
        for i, canon in m.items():
            rec[canon] = r[i].strip() if i < len(r) else ""
        if not rec["address"]:
            skipped += 1
            continue
        out.append(rec)
    return out, skipped


def convert_serp(headers, rows):
    m = map_headers(headers, "serp")
    if "query" not in m.values():
        sys.stderr.write("[ERROR] serp 格式缺必需列: query(表头: %s)\n" % ", ".join(headers))
        raise SystemExit(2)
    qi = next(i for i, c in m.items() if c == "query")
    ui = next((i for i, c in m.items() if c == "url"), None)
    pi = next((i for i, c in m.items() if c == "position"), None)
    out, skipped = [], 0
    for r in rows:
        query = r[qi].strip() if qi < len(r) else ""
        if not query:
            skipped += 1
            continue
        # URL 来源两路:①映射的 url 列(格内可再塞 ;/, 分隔的 top10 串)②无表头的多余 URL 格
        # (分号宽表 query;u1;u2;… 的行比表头长——未映射格按位置序收编)
        mapped = split_url_cell(r[ui]) if (ui is not None and ui < len(r)) else []
        extras = [c.strip() for j, c in enumerate(r)
                  if j not in (qi, pi, ui) and URL_TOKEN_RE.match(c.strip())]
        urls, seen = [], set()
        for u in mapped + extras:
            if u not in seen:
                seen.add(u)
                urls.append(u)
        if not urls:
            skipped += 1
            continue
        if len(urls) == 1:
            # 长表:单 URL 行带 position 列用列值;无 position 列退 "1"(唯一结果即第 1)
            pos = (r[pi].strip() if pi is not None and pi < len(r) and r[pi].strip() else "1")
            out.append({"query": query, "url": urls[0], "position": pos})
        else:
            # 宽表:多 URL 按出现顺序枚举 position=1..N(top10 表口径)
            for pos, u in enumerate(urls, 1):
                out.append({"query": query, "url": u, "position": str(pos)})
    return out, skipped


def convert_kws(headers, rows):
    m = map_headers(headers, "kws")
    missing = sorted({"keyword", "search_volume"} - set(m.values()))
    if missing:
        sys.stderr.write("[ERROR] kws 格式缺必需列: %s(表头: %s)\n" % (", ".join(missing), ", ".join(headers)))
        raise SystemExit(2)
    out, skipped = [], 0
    for r in rows:
        rec = {c: "" for c in KWS_COLS}
        for i, canon in m.items():
            v = r[i].strip() if i < len(r) else ""
            rec[canon] = normalize_volume(v) if canon == "search_volume" else v
        if not rec["keyword"]:
            skipped += 1
            continue
        out.append(rec)
    return out, skipped


CONVERTERS = {"frog": (convert_frog, FROG_COLS), "serp": (convert_serp, SERP_COLS),
              "kws": (convert_kws, KWS_COLS)}


def emit(records, cols, out_path):
    """规范化 CSV 写出(stdout 或 --out);返回序列化行数。"""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for rec in records:
        w.writerow(rec)
    data = buf.getvalue()
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            f.write(data)
    else:
        sys.stdout.write(data)
    return len(records)


def main():
    args = sys.argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print(__doc__.strip())
        return
    kind = out_path = urls_only = as_json = None
    it = iter(args)
    positional = []
    for a in it:
        if a == "--kind":
            kind = next(it, None)
        elif a == "--out":
            out_path = next(it, None)
        elif a == "--urls-only":
            urls_only = True
        elif a == "--json":
            as_json = True
        elif a.startswith("--"):
            sys.stderr.write("[ERROR] 未知参数 %s\n\n%s\n" % (a, __doc__.strip()))
            raise SystemExit(2)
        else:
            positional.append(a)
    if not positional:
        sys.stderr.write("[ERROR] 缺输入文件\n\n" + __doc__.strip() + "\n")
        raise SystemExit(2)
    if kind is not None and kind not in CONVERTERS:
        sys.stderr.write("[ERROR] 未知 --kind %s;可用: frog|serp|kws\n" % kind)
        raise SystemExit(2)

    # 阶段一:逐文件嗅探+转换(先全部判格式,混格式在写任何输出前拒绝)
    payload_rows, all_records, all_urls, kinds_seen = [], [], [], []
    total_skipped = 0
    for path in positional:
        headers, rows = read_rows(path)
        k = kind or sniff_kind(headers)
        if k is None:
            sys.stderr.write("[ERROR] 无法嗅探格式(表头: %s)。嗅探特征:"
                             " frog=地址+Indexability(或 Status Code+Inlinks);"
                             " kws=关键词+搜索量;serp=查询词+URL。请显式 --kind。\n" % ", ".join(headers))
            raise SystemExit(2)
        kinds_seen.append(k)
        conv, cols = CONVERTERS[k]
        records, skipped = conv(headers, rows)
        total_skipped += skipped
        all_records.extend(records)
        payload_rows.append({"input": path, "kind": k, "columns": cols,
                             "rows": len(records), "skipped": skipped})
        sys.stderr.write("[byo_import] %s → kind=%s, %d 行(+%d 跳过)\n" % (path, k, len(records), skipped))

    if len(set(kinds_seen)) > 1:
        sys.stderr.write("[ERROR] 多个输入文件嗅探出不同格式(%s)——请分批归一\n" % ", ".join(kinds_seen))
        raise SystemExit(2)
    k = kinds_seen[0]
    if k == "frog":   # URL 清单去重保序(--urls-only / --json urls 的来源)
        seen = set()
        for rec in all_records:
            if rec["address"] not in seen:
                seen.add(rec["address"])
                all_urls.append(rec["address"])

    # --urls-only:仅出一行一 URL 清单(site_audit 批量审计入口,见文件头消费思路)
    if urls_only:
        if k != "frog":
            sys.stderr.write("[ERROR] --urls-only 仅支持 frog(serp/kws 无页面地址列)\n")
            raise SystemExit(2)
        if out_path:   # 同时要归一 CSV 文件时照写,URL 清单走 stdout
            emit(all_records, FROG_COLS, out_path)
        sys.stdout.write("\n".join(all_urls) + ("\n" if all_urls else ""))
        return

    # 常规路径:CSV → --out 文件;无 --out 时 CSV 走 stdout(--json 模式除外,JSON 独占 stdout)
    if out_path or not as_json:
        emit(all_records, CONVERTERS[k][1], out_path)

    if as_json:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "kind": k, "inputs": payload_rows,
                          "total_rows": len(all_records), "skipped": total_skipped,
                          "urls": all_urls}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
