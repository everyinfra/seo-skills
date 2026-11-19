#!/usr/bin/env python3
"""SERP 抓取器(GoAnyAPI 版,stdlib-only):把查询集的 Google 前 N 有机结果抓到
`keyword,url1;url2;…` CSV,直喂 serp_overlap / content_queue 的既有输入契约。

为什么需要它:serp_overlap.py 的输入是 `keyword,top10 URL(分号分隔)`,而本套件
不出售、不代抓 SERP——没有 SERP 数据时 serp_overlap 直接 exit 2(绝不虚构)。
本脚本只做「取证」这一件事:走用户自备 Key 的 GoAnyAPI `serp-stable` 端点
(GET /api/v1/serp-stable,1 credit/次),把真实抓到的 top-N 落成 CSV,
抓不到的词**不写行**,只在报告里记 empty/failed(空结果是有效响应、照常计费,
但不等于有数据)。

与 monitor.py 的 serp_source 源适配层的关系:那一层只内置零 key 的 bing/duckduckgo,
付费源是「注册位未接入」(见 SERP_SOURCE_TABLE)。本脚本不接管 monitor 的可见性
巡检,只产出离线 SERP 样本表——即 data-onboarding.md 里 T4「自带 Key 的 SERP API
→ 拼 keyword,top10 CSV 喂 serp_overlap」这条路径的可执行客户端。

用法:
  export GOANYAPI_API_KEY=...          # 或用 --key-file(默认 ~/.config/seo-suite/goanyapi.key)
  python3 serp_pull.py --keywords kws.txt --out serp.csv
  python3 serp_pull.py --keywords kws.txt --out serp.csv --gl tr --hl tr --top 20
  python3 serp_pull.py --keywords kws.txt --out serp.csv --dry-run      # 只算要花多少 credit
  python3 serp_pull.py --keywords kws.txt --out serp.csv --json report.json --max-credits 50

参数口径:
  --gl      结果国家(两位码,如 us / tr / de),默认 us
  --hl      界面语言(en / zh-cn …),默认 en
  --device  desktop|mobile,默认 desktop(与查 SERP 特征时固定条件同理)
  --top     每个词取前几条有机结果,默认 10(serp_overlap 的四档判据按 top-10 定义)
  --max-credits  本次最多花多少 credit(默认 50);预算用尽即停,已抓到的照常落盘
  --cache   响应缓存 JSON(默认 <out>.cache.json),重跑不重复花钱;--refresh 强制重抓
  --rps     每秒最多几次请求,默认 1

退出码:0 全部请求成功(empty 也算成功响应,但报告里单列)/ 2 参数或输入错误
  (缺 Key、无关键词)/ 3 有词 failed 或 skipped(预算用尽),CSV 只含已观测行。

纪律(与 data-source-contract 反编造列一致):
  - 只写真实抓到的 URL;某词 empty/failed 就不出现该行,不拿竞品页或历史样本补齐;
  - 不自动在 serp-stable / serp-standard / serp 之间降级重试(GoAnyAPI 不会自动
    换版本,换版本单价 1/2/3 credit 不同),要换版本请显式 --edition;
  - 401/402/403 立刻中止:先修 Key 与余额,继续跑只是浪费时间(失败请求不计费,
    但空结果与缓存命中照常计费)。
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://api.goanyapi.com/api/v1"
ENDPOINTS = {  # 版次 → (路径, 单价 credit, 查询参数名)
    "stable": ("/serp-stable", 1, "query"),
    "standard": ("/serp-standard", 2, "q"),
    "multi": ("/serp", 3, "q"),
}
DEFAULT_EDITION = "stable"
DEFAULT_KEY_FILE = "~/.config/seo-suite/goanyapi.key"
FATAL_CODES = (401, 402, 403)
RETRY_CODES = (429, 500, 502, 503, 504)

USAGE = __doc__.split("用法:")[0].strip() + """

usage: serp_pull.py --keywords kws.txt --out serp.csv [--gl us] [--hl en]
                    [--device desktop] [--top 10] [--edition stable]
                    [--max-credits 50] [--cache PATH] [--refresh] [--rps 1]
                    [--dry-run] [--json report.json] [--header]

Key: GOANYAPI_API_KEY 环境变量,或 --key-file(默认 ~/.config/seo-suite/goanyapi.key)。"""


def read_key(path):
    """Key 来源:--key-file > 环境变量 > 默认文件。返回 (key, 来源说明)。"""
    if path:
        p = os.path.expanduser(path)
        if not os.path.exists(p):
            return None, "key file not found: %s" % p
        with open(p, encoding="utf-8") as f:
            return f.read().strip(), p
    env = os.environ.get("GOANYAPI_API_KEY", "").strip()
    if env:
        return env, "env GOANYAPI_API_KEY"
    p = os.path.expanduser(DEFAULT_KEY_FILE)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read().strip(), p
    return None, "no key (env GOANYAPI_API_KEY / --key-file / %s)" % DEFAULT_KEY_FILE


def read_keywords(path):
    """一行一个关键词;跳过空行与 # 注释;保留原顺序去重。"""
    out, seen = [], set()
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            kw = line.strip()
            if not kw or kw.startswith("#"):
                continue
            if kw not in seen:
                seen.add(kw)
                out.append(kw)
    return out


def build_url(query, gl, hl, device, edition):
    path, _, param = ENDPOINTS[edition]
    qs = urllib.parse.urlencode({param: query, "gl": gl, "hl": hl,
                                 "device": device, "start": 0})
    return BASE_URL + path + "?" + qs


def _http_get_json(url, key, timeout=45):
    """单次 GET。返回 (status, payload);网络层错误返回 (None, {"error": ...})。"""
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + key,
        "Accept": "application/json",
        "User-Agent": "seo-suite/serp_pull (+https://goanyapi.com)",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status = getattr(r, "status", 200)
            body = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
        return e.code, _try_json(body) or {"error": str(e)}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return None, {"error": str(e)}
    return status, _try_json(body) or {}


def _try_json(body):
    try:
        return json.loads(body) if body else None
    except ValueError:
        return None


def extract_organic(payload, top):
    """从 serp-stable 响应取前 top 条有机 URL。

    路径:data.result.results[] —— 每项 url / rank / type(注意 stable 用 results+url,
    serp-standard 才是 organic_results+link,serp(multi)是 organic[],三者不通用)。
    只保留有 url 的项;同一 URL 只留首次出现的名次。取不到就返回 [],绝不补位。
    """
    result = ((payload or {}).get("data") or {}).get("result") or {}
    items = result.get("results") or result.get("organic_results") or result.get("organic") or []
    urls, seen = [], set()
    for it in items:
        if not isinstance(it, dict):
            continue
        url = it.get("url") or it.get("link")
        if not url or url in seen:
            continue
        kind = (it.get("type") or "").lower()
        if kind and kind not in ("organic", "organic_result"):
            continue          # 广告/本地包/图片等不算有机结果
        seen.add(url)
        urls.append(url)
        if len(urls) >= top:
            break
    return urls


def credits_used(payload, edition):
    """以响应里的 data.costCredits 为准,缺失时按版次单价保守计入。"""
    data = (payload or {}).get("data") or {}
    c = data.get("costCredits")
    return c if isinstance(c, int) and c >= 0 else ENDPOINTS[edition][1]


def fetch_one(query, key, gl, hl, device, top, edition, retries=1):
    """抓一个词 → (状态, urls, credits, note)。状态 ok / empty / failed / fatal。"""
    url = build_url(query, gl, hl, device, edition)
    last_note = ""
    for attempt in range(retries + 1):
        status, payload = _http_get_json(url, key)
        if status in FATAL_CODES:
            note = (payload or {}).get("message") or (payload or {}).get("error") or "HTTP %s" % status
            return "fatal", [], 0, "HTTP %s: %s" % (status, note)
        if status in RETRY_CODES and attempt < retries:
            last_note = "HTTP %s, retrying" % status
            time.sleep(2 * (attempt + 1))
            continue
        if status is None:
            return "failed", [], 0, "network: %s" % ((payload or {}).get("error") or "?")
        if status != 200:
            return "failed", [], 0, "HTTP %s: %s" % (status, (payload or {}).get("message") or "")
        code = (payload or {}).get("code")
        if code not in (None, 0, 200):
            return "failed", [], 0, "api code %s: %s" % (code, (payload or {}).get("message") or "")
        urls = extract_organic(payload, top)
        used = credits_used(payload, edition)
        if not urls:
            return "empty", [], used, "空结果是有效响应(照常计费),本词不写入 CSV"
        return "ok", urls, used, ""
    return "failed", [], 0, last_note or "retries exhausted"


def load_cache(path):
    if path and os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except ValueError:
            return {}
    return {}


def save_cache(path, cache):
    if not path:
        return
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, path)


def cache_key(query, gl, hl, device, top, edition):
    return "%s|%s|%s|%s|%s|%s" % (query, gl, hl, device, top, edition)


def run(args):
    kws = read_keywords(args.keywords)
    if not kws:
        sys.stderr.write("no keywords in %s\n" % args.keywords)
        return 2
    edition = args.edition
    unit = ENDPOINTS[edition][1]
    if args.max_credits < unit:
        sys.stderr.write("--max-credits %s < 单价 %s credit(edition=%s)\n"
                         % (args.max_credits, unit, edition))
        return 2
    if args.dry_run:
        print("dry-run: %d keywords × %d credit(%s 版)= %d credit 上限;请求形如:\n  %s"
              % (len(kws), unit, edition, min(args.max_credits, unit * len(kws)),
                 build_url(kws[0], args.gl, args.hl, args.device, edition)))
        return 0
    key, src = read_key(args.key_file)
    if not key:
        sys.stderr.write("missing API key: %s\n" % src)
        return 2

    cache_path = args.cache or (args.out + ".cache.json")
    cache = {} if args.refresh else load_cache(cache_path)
    rows, report = [], []
    spent = 0
    fatal = None
    for i, kw in enumerate(kws, 1):
        ck = cache_key(kw, args.gl, args.hl, args.device, args.top, edition)
        if ck in cache:
            urls = cache[ck]
            status, used, note = ("ok" if urls else "empty"), 0, "cache hit"
        else:
            if spent + unit > args.max_credits:
                report.append({"keyword": kw, "status": "skipped",
                               "note": "预算用尽(--max-credits %s)" % args.max_credits})
                continue
            status, urls, used, note = fetch_one(kw, key, args.gl, args.hl,
                                                 args.device, args.top, edition)
            spent += used
            if status == "fatal":
                report.append({"keyword": kw, "status": "failed", "credits": used,
                               "note": note + "(凭证/余额类错误,已中止)"})
                fatal = note
                break
            if status in ("ok", "empty"):
                cache[ck] = urls
                save_cache(cache_path, cache)
        report.append({"keyword": kw, "status": status, "credits": used,
                       "urls": len(urls), "note": note})
        if status == "ok":
            rows.append((kw, urls))
        if i < len(kws) and status != "cache hit":
            time.sleep(max(0.0, 1.0 / args.rps))

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        if args.header:
            f.write("keyword,top%d\n" % args.top)
        for kw, urls in rows:
            f.write("%s,%s\n" % (kw.replace(",", " "), ";".join(urls)))

    ok = sum(1 for r in report if r["status"] == "ok")
    empty = sum(1 for r in report if r["status"] == "empty")
    failed = sum(1 for r in report if r["status"] == "failed")
    skipped = sum(1 for r in report if r["status"] == "skipped")
    summary = {"endpoint": "/api/v1" + ENDPOINTS[edition][0], "edition": edition,
               "gl": args.gl, "hl": args.hl, "device": args.device, "top": args.top,
               "keywords": len(kws), "ok": ok, "empty": empty, "failed": failed,
               "skipped": skipped, "credits_spent": spent,
               "key_source": src, "out": args.out, "cache": cache_path}
    print("SERP 抓取:%d 词 → ok %d / empty %d / failed %d / skipped %d;花 %d credit"
          % (len(kws), ok, empty, failed, skipped, spent))
    print("CSV:%s(只含已观测的 %d 行;empty/failed 不补位)" % (args.out, len(rows)))
    if args.json:
        payload = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                   "summary": summary, "keywords": report}
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
    if fatal:
        sys.stderr.write("aborted: %s\n" % fatal)
        return 3
    return 3 if (failed or skipped) else 0


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--keywords", "-k")
    ap.add_argument("--out", "-o")
    ap.add_argument("--gl", default="us")
    ap.add_argument("--hl", default="en")
    ap.add_argument("--device", default="desktop", choices=("desktop", "mobile"))
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--edition", default=DEFAULT_EDITION, choices=tuple(ENDPOINTS))
    ap.add_argument("--max-credits", type=int, default=50)
    ap.add_argument("--cache")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--rps", type=float, default=1.0)
    ap.add_argument("--key-file")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--header", action="store_true")
    ap.add_argument("--help", "-h", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        sys.stderr.write(USAGE + "\n")
        return 2
    if args.help or not args.keywords or not args.out:
        print(USAGE)
        return 0 if args.help else 2
    if args.top < 1 or args.rps <= 0:
        sys.stderr.write("--top 必须 ≥1,--rps 必须 >0\n")
        return 2
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
