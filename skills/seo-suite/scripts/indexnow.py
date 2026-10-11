#!/usr/bin/env python3
"""IndexNow 提交器(零 key 门槛/免费,pipeline-completeness.md R2-5;stdlib-only)。

IndexNow(indexnow.org)是 Bing/Yandex/Naver/Seznam/Yep 共同参与的变更通知协议:
站方在站点根目录放一个 key 文件证明主权,POST 变更 URL,参与引擎共享收链,
新页分钟级被发现("秒收")。**Google 不支持 IndexNow**——套件事实口径
(routing-rules.md 控制语义表:"IndexNow 只是通知(且不含 Google)";
programmatic-seo-playbook.md §IndexNow,官方 indexnow.org 核实于 2026-10-09;
multilingual-workflow.md 发布闸门与 ci-gates.md 部署配方同口径:IndexNow ping
要打进发布流水线,手工 ping 必然停摆)——Google 侧收录靠 sitemap
lastmod 准确度 + 高质量内链 + GSC 提交,本工具帮不上。另两条纪律(playbook):
只提交"可索引且内容实际变更"的 URL(拿它当日更心跳 = 自毁信用);IndexNow
只是通知,不保证收录。

用法:
  python3 indexnow.py key [--out DIR]        # 生成 key(uuid4 形态)+ 部署指引
  python3 indexnow.py submit --host example.com --key K \\
      [--urls urls.txt | --url U ...] [--endpoint bing|yandex|naver|indexnow] [--json]

key 部署(协议 Option 1,官方强烈推荐):
  1) key 子命令生成 32 位小写十六进制 key(uuid4 形态;协议要求 8-128 位,
     字符集 a-z A-Z 0-9 连字符);
  2) 在站点根目录放 UTF-8 文本文件 https://{host}/{key}.txt,内容恰为 key 本身;
  3) 引擎首次收到提交后抓该文件验证主权——202 Accepted = 已收到但 key 校验
     未完成(校验完成前提交可能被忽略,属正常,无需重试;部署好 key 文件后
     再提交一批看到 200 即验证通过)。

submit 契约:
  - POST JSON {"host","key","keyLocation","urlList"} 到引擎端点;默认
    api.indexnow.org 共享端点(一份提交广播全部参与引擎),--endpoint 可指定
    bing/yandex/naver 专属端点(对 Naver/Yandex 市场尤其值得,markets/ko.md 口径);
  - 单批 ≤10000 URL(协议上限),超出自动分批;
  - URL 必须属于 --host(引擎对不属于 host 的 URL 返 422,本地先拒省一个来回);
  - 响应判读:200/202=ok;422=key 文件未部署/内容不匹配或 URL 不属该 host;
    429=限速(疑似 spam,退避降频);403=key 无效;400=格式错。

SSRF 防御(套件惯例,照 gsc_api.py 端点固定思路):仅 https + 端点域白名单
(api.indexnow.org / bing.com / yandex.com / searchadvisor.naver.com 及 www 变体);
端点表内置,不接受任意 URL 注入。

退出码:0 全部批次 ok;1 有批次失败(网络/HTTP);2 用法错(参数/SSRF 拒)。
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

SCHEMA_VERSION = 1               # --json 顶层 schema 版本(输出契约)
UA = "seo-suite-indexnow/1.0"
BATCH_LIMIT = 10000              # 协议:单次 POST ≤10000 URL
DEFAULT_TIMEOUT = 15
KEY_RE = re.compile(r"[A-Za-z0-9-]{8,128}")     # 协议 key 字符集与长度

# 端点表(--endpoint 的 choices;官方 searchengines.json + meta.json 核实于 2026-10-12)
ENDPOINTS = {
    "indexnow": "https://api.indexnow.org/indexnow",          # 共享端点,广播全部参与引擎
    "bing": "https://www.bing.com/indexnow",
    "yandex": "https://yandex.com/indexnow",
    "naver": "https://searchadvisor.naver.com/indexnow",
}
# SSRF 白名单:仅这些域可被连(端点表内置;守卫仍独立复查,纵深防御)
ALLOWED_HOSTS = frozenset({
    "api.indexnow.org",
    "www.bing.com", "bing.com",
    "yandex.com", "www.yandex.com",
    "searchadvisor.naver.com",
})

# Google 不支持 IndexNow 的口径串(--json note_google 与人读尾注共用)
NOTE_GOOGLE = ("Google 不支持 IndexNow(参与方 Bing/Yandex/Naver/Seznam/Yep,"
               "官方 indexnow.org 核实 2026-10-09);Google 侧靠 sitemap lastmod "
               "准确度 + 高质量内链 + GSC 提交;IndexNow 只是通知,不保证收录")

VERDICT_LABEL = {"ok": "OK", "fail": "失败", "network_error": "失败(网络)"}


class UsageError(Exception):
    """参数校验失败——用法错(exit 2)。"""


class GuardError(Exception):
    """端点白名单拒(SSRF 防御)——用法级错误(exit 2)。"""


# ---------- key:生成 / 校验 ----------

def generate_key():
    """uuid4 形态 key:uuid4().hex = 32 位小写十六进制,恒满足协议 8-128 hex 上限。"""
    return uuid.uuid4().hex


def validate_key(key):
    if not KEY_RE.fullmatch(key or ""):
        raise UsageError("key 需 8-128 位[a-zA-Z0-9-](协议要求;先用 key 子命令生成)"
                         " 实得 %r" % (key or ""))
    return key


def key_location(host, key):
    """协议 Option 1:key 文件固定放站点根目录 https://{host}/{key}.txt。"""
    return "https://%s/%s.txt" % (host, key)


def mask_key(key):
    return (key[:6] + "…" + key[-4:]) if key and len(key) > 12 else "…"


# ---------- SSRF 防御(端点固定,白名单域即可;照 gsc_api.guard_googleapis) ----------

def guard_endpoint(url):
    """端点守卫:仅 https + 白名单端点域。端点表内置本不应有外部输入,
    守卫独立复查作纵深防御(防日后端点表被改动引入任意 URL)。"""
    p = urllib.parse.urlsplit(url or "")
    host = (p.hostname or "").lower()
    if p.scheme != "https" or not host:
        raise GuardError("SSRF 守卫:仅允许 https 端点: %s" % url)
    if host not in ALLOWED_HOSTS:
        raise GuardError("SSRF 守卫:端点域不在白名单(%s): %s"
                         % ("/".join(sorted(ALLOWED_HOSTS)), url))
    return True


# ---------- URL 收集与属主预检 ----------

def load_urls_file(path):
    """一行一个 URL;# 注释与空行跳过。"""
    try:
        with open(path, encoding="utf-8-sig") as f:
            lines = f.read().splitlines()
    except OSError as e:
        raise UsageError("读不了 --urls 文件 %s: %s" % (path, e))
    out = []
    for ln in lines:
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            out.append(ln)
    return out


def collect_urls(url_args, urls_path):
    """合并 --url(...)与 --urls 文件,去重保序;空 → 用法错(引擎对空 urlList 返 400)。"""
    urls = list(url_args or [])
    if urls_path:
        urls.extend(load_urls_file(urls_path))
    seen, uniq = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    if not uniq:
        raise UsageError("没有可提交的 URL:--url U(可重复)或 --urls urls.txt 至少给一个"
                         "(空 urlList 引擎返 400)")
    return uniq


def normalize_host(host):
    """--host 接受裸域名(example.com)或带 scheme 的 URL(https://example.com/)。"""
    host = (host or "").strip()
    if not host:
        raise UsageError("--host 必填(裸域名即可,如 example.com)")
    if "://" in host:
        p = urllib.parse.urlsplit(host)
        if p.scheme not in ("http", "https") or not p.hostname:
            raise UsageError("--host 需域名或 http(s) URL,实得 %r" % host)
        if p.path not in ("", "/") or p.query or p.fragment:
            raise UsageError("--host 只要域名,不带路径/查询: %r" % host)
        return p.hostname.lower()
    if "/" in host or "?" in host or "#" in host:
        raise UsageError("--host 只要域名(不带路径/查询),实得 %r" % host)
    return host.lower()


def check_urls_belong(urls, host):
    """URL 必须属于 host(引擎 422 的主因之一;本地先拒,免一个网络来回)。
    严格同名匹配:host=example.com 时 www.example.com 的 URL 不算——引擎按
    host 字段判属主,跨子域提交不会被受理,请对每个子域单独跑一次。"""
    bad = []
    for u in urls:
        p = urllib.parse.urlsplit(u)
        if p.scheme not in ("http", "https") or (p.hostname or "").lower() != host:
            bad.append(u)
    if bad:
        raise UsageError("%d 个 URL 不属于 host %s(引擎会拒):%s\n"
                         "  每个域名/子域单独跑一次(--host 与 URL 的域名须完全一致)"
                         % (len(bad), host, ", ".join(bad[:5]) + ("…" if len(bad) > 5 else "")))
    return True


# ---------- HTTP(唯一网络出口;测试打桩点) ----------

def _http_post(endpoint_url, payload, timeout=DEFAULT_TIMEOUT):
    """POST JSON;返回 HTTP 状态码(int)。HTTPError 同样只关心 code
    (IndexNow 端点 4xx/5xx 响应体为空或纯文案,状态码即全部语义)。
    URLError 原样上抛(网络不可达,调用方计为失败批次)。"""
    req = urllib.request.Request(
        endpoint_url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def verdict_for_status(code, host=None, key=None):
    """协议响应码 → (verdict, note)。200/202=ok;其余失败并给可执行提示
    (422 指到具体 key 文件 URL,host/key 由 post_batch 传入)。"""
    if code == 200:
        return "ok", "URL 提交成功(引擎已收到;只是通知,不保证收录)"
    if code == 202:
        return "ok", ("已接收,key 校验待完成——校验完成前本批可能被忽略(协议常态,不必重试);"
                      "key 文件部署好之后再提交一批,看到 200 即验证通过")
    if code == 400:
        return "fail", "请求格式无效(检查 URL 是否 RFC-3986 规范、批量是否 ≤10000)"
    if code == 403:
        return "fail", "key 无效(key 文件不存在,或文件内容不含本 key)"
    if code == 422:
        loc = "(https://%s/%s.txt)" % (host, key) if host and key else ""
        return "fail", ("key 未部署或 URL 不属该 host:确认 key 文件%s 可公开访问且 UTF-8"
                        "内容恰为 key 本身;urlList 的域名须与 --host 完全一致" % loc)
    if code == 429:
        return "fail", "限速(疑似 spam):退避几分钟再试,并把提交频率降到内容实际变更时"
    return "fail", "意外响应码 %d(非协议表内状态;稍后重试或查端点公告)" % code


def post_batch(endpoint_url, host, key, urls, timeout=DEFAULT_TIMEOUT):
    """提交一批(调用方保证 ≤BATCH_LIMIT);返回 {status, verdict, note, urls}。
    网络异常 → verdict=network_error(不抛,由调用方汇总退出码)。"""
    guard_endpoint(endpoint_url)
    payload = {"host": host, "key": key, "keyLocation": key_location(host, key),
               "urlList": list(urls)}
    try:
        code = _http_post(endpoint_url, payload, timeout=timeout)
    except urllib.error.URLError as e:
        return {"status": None, "verdict": "network_error",
                "note": "网络不可达: %s" % e, "urls": len(urls)}
    verdict, note = verdict_for_status(code, host, key)
    return {"status": code, "verdict": verdict, "note": note, "urls": len(urls)}


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


# ---------- 子命令 ----------

def cmd_key(args):
    key = generate_key()
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, key + ".txt")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(key)                     # 协议:内容恰为 key(无尾换行)
        print("key 文件已写: %s(拷到站点根目录,UTF-8 原样)" % path)
    print("IndexNow key: %s" % key)
    print()
    print("部署(一次性,协议 Option 1):")
    print("  1) 在站点根目录放 UTF-8 文本文件: https://<你的域名>/%s.txt" % key)
    print("     文件内容恰为 key 本身(上面那串,无多余字符/换行)")
    print("  2) 保留该文件(引擎会反复抓取验证;换 key = 换文件名+内容)")
    print("  3) 首次提交通常收到 202(key 校验待完成),部署正确后再提交会转 200")
    print()
    print("提交示例:")
    print("  python3 indexnow.py submit --host example.com --key %s \\" % key)
    print("      --url https://example.com/new-page")
    print()
    print("注: %s" % NOTE_GOOGLE)
    if args.json:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "key": key,
                          "key_file": "/%s.txt(站点根目录,内容=key)" % key,
                          "note_google": NOTE_GOOGLE},
                         ensure_ascii=False, indent=1))
    return 0


def cmd_submit(args):
    host = normalize_host(args.host)
    key = validate_key(args.key)
    urls = collect_urls(args.url, args.urls)
    check_urls_belong(urls, host)
    endpoint_url = ENDPOINTS[args.endpoint]
    guard_endpoint(endpoint_url)

    results = [post_batch(endpoint_url, host, key, batch, timeout=args.timeout)
               for batch in chunked(urls, BATCH_LIMIT)]
    ok_batches = [r for r in results if r["verdict"] == "ok"]
    failed = [r for r in results if r["verdict"] != "ok"]

    if args.json:
        print(json.dumps({
            "schema_version": SCHEMA_VERSION, "ok": not failed,
            "host": host, "endpoint": args.endpoint, "endpoint_url": endpoint_url,
            "key": mask_key(key), "key_location": key_location(host, key),
            "submitted_urls": sum(r["urls"] for r in results),
            "batches": [{"batch": i + 1, "urls": r["urls"], "status": r["status"],
                         "verdict": r["verdict"], "note": r["note"]}
                        for i, r in enumerate(results)],
            "failed_batches": len(failed), "note_google": NOTE_GOOGLE,
        }, ensure_ascii=False, indent=1))
        return 0 if not failed else 1

    print("== IndexNow 提交 ==")
    print("host     : %s" % host)
    print("endpoint : %s(%s;参与引擎共享收链)" % (endpoint_url, args.endpoint))
    print("key 文件 : %s(引擎抓取验证主权)" % key_location(host, key))
    for i, r in enumerate(results):
        print("批次 %d/%d: %d URL → %s %s" % (
            i + 1, len(results), r["urls"],
            r["status"] if r["status"] is not None else "网络错误",
            VERDICT_LABEL.get(r["verdict"], r["verdict"])))
        if r["verdict"] != "ok":
            print("  └ %s" % r["note"])
    print("共 %d URL(%d 批 ok,%d 批失败)" % (len(urls), len(ok_batches), len(failed)))
    for r in results:                        # ok 批的提示只挑 202 等有信息量的
        if r["verdict"] == "ok" and r["status"] == 202:
            print("  202: %s" % r["note"])
    print("注: %s" % NOTE_GOOGLE)
    return 0 if not failed else 1


def build_parser():
    p = argparse.ArgumentParser(
        prog="indexnow.py",
        description="IndexNow 提交器(零 key 门槛,Bing/Yandex/Naver 秒收协议;"
                    "R2-5)——key 生成/部署指引 + 批量 POST 提交。Google 不支持 IndexNow。",
        epilog="key 部署: https://{host}/{key}.txt(根目录,UTF-8 内容恰为 key)。\n"
               "响应: 200/202=ok(202=key 校验待完成);422=key 未部署/URL 不属 host;\n"
               "429=限速;403=key 无效。单批 ≤10000 自动分批。\n"
               "退出码: 0 全部 ok / 1 有批次失败 / 2 用法错。",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", metavar="{key,submit}")

    pk = sub.add_parser("key", help="生成 key(uuid4 形态)+ key 文件放置指引")
    pk.add_argument("--out", metavar="DIR",
                    help="顺手把 {key}.txt 写到该目录(内容=key,拷去站点根目录)")
    pk.add_argument("--json", action="store_true", help="附结构化输出(schema_version=1)")

    ps = sub.add_parser("submit", help="批量 POST JSON {host,key,keyLocation,urlList}",
                        description="批量 POST JSON {host,key,keyLocation,urlList} 到引擎端点。"
                                    "\n%s" % NOTE_GOOGLE,
                        epilog="key 部署: https://{host}/{key}.txt(根目录,UTF-8 内容恰为 key)。\n"
                               "响应: 200/202=ok(202=key 校验待完成);422=key 未部署/URL 不属 host;\n"
                               "429=限速;403=key 无效。单批 ≤10000 自动分批。",
                        formatter_class=argparse.RawDescriptionHelpFormatter)
    ps.add_argument("--host", required=True, help="站点域名(example.com;URL 须属它)")
    ps.add_argument("--key", required=True, help="IndexNow key(key 子命令生成)")
    ps.add_argument("--url", action="append", default=[], metavar="U",
                    help="要提交的 URL(可重复)")
    ps.add_argument("--urls", metavar="FILE", help="URL 清单文件(一行一个;# 注释跳过)")
    ps.add_argument("--endpoint", choices=sorted(ENDPOINTS), default="indexnow",
                    help="端点(默认 indexnow=api.indexnow.org 共享端点,广播全部参与"
                         "引擎;bing/yandex/naver 为引擎专属端点)")
    ps.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help="单请求超时秒数(默认 %d)" % DEFAULT_TIMEOUT)
    ps.add_argument("--json", action="store_true", help="结构化输出(schema_version=1)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not args.cmd:
        build_parser().print_help(sys.stderr)
        return 2
    handlers = {"key": cmd_key, "submit": cmd_submit}
    try:
        return handlers[args.cmd](args)
    except UsageError as e:
        sys.stderr.write("[用法] %s\n" % e)
        return 2
    except GuardError as e:
        sys.stderr.write("[拒] %s\n" % e)
        return 2
    except OSError as e:
        sys.stderr.write("[错误] %s\n" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
