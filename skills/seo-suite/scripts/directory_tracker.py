#!/usr/bin/env python3
"""目录提交执行器(directory submission tracker;R4-2;stdlib only)。
吃 references/research/directory-submissions.md 的追踪 CSV schema:
init --directories <该 md> 解析"追踪 CSV 字段"列定义生成空模板(骨=文档 14 列,
工具补 ID/Cost 两个管理列——verify --entry 与付费目录记账需要);add 登记目录 →
verify 现场核验(HEAD/GET 目录页:提交仍在 + rel=nofollow 检查,目标页当不可信
输入:仅 http(s)+ 私网/环回/元数据 SSRF 拒绝)→ quarterly 季度复检队列(上次
Backlink Verified >90d——"目录可能悄悄把全部外链转 nofollow 而不通知")→
import/export CSV round-trip。

数据文件 CSV(默认当前目录 directory-submissions.csv,--file 可指定),列(init 实测):
  ID, Directory, Tier, URL, Category, DR, Dofollow, Cost, Submission Date, Status,
  Live URL, Backlink Verified, Positioning Variant Used, Tags Used, Account Email, Notes
  Dofollow: "?"(未知,默认)| dofollow | nofollow | sponsored | ugc(verify 现场改写;
  后三者是 Google 链接限定属性,同一锚点多个时按 nofollow>sponsored>ugc 取一)
  Status: pending(未提交)| submitted | live | removed(verify 现场改写)
  Tier: 1-13(文档 13 层目录结构 T1..T13)

用法: python3 directory_tracker.py <init|add|list|verify|quarterly|export|import> [选项]
退出码: 0 正常 / 1 verify 发现问题(removed/nofollow/sponsored/ugc/找不到链接/不可达)或
quarterly 队列非空(cron 消费,照 trend_watch 口径接 notify) / 2 输入或参数错误。

并发口径(R5,照 remediation.py):save_store 原子写(tempfile + os.replace)+
文件级 flock;add/verify/import 的 load→改→save 全程持锁。verify 网络走模块级
fetch()(单点,便于测试打桩)。"""
import contextlib
import csv
try:
    import fcntl
except ImportError:  # Windows 没有 fcntl,改用 msvcrt.locking 加同样的排他锁
    fcntl = None
    import msvcrt
import ipaddress
import json
import os
import re
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SCHEMA_VERSION = 1
DEFAULT_FILE = "directory-submissions.csv"
STATUSES = ("pending", "submitted", "live", "removed")
# Google 链接限定属性(qualify-outbound-links):三者都让链接不传权,分别记录(B60)。
# 一个锚点带多个时按此优先级落 Dofollow 列;checks.rel_qualifiers 列全。
REL_QUALIFIERS = ("nofollow", "sponsored", "ugc")
DOFOLLOW_VALUES = ("?", "dofollow") + REL_QUALIFIERS
TIERS = range(1, 14)                       # 文档 13 层 T1..T13
QUARTERLY_DAYS = 90                        # 季度复检窗
RECHECK_STATUSES = ("submitted", "live")   # 需要复检的在途状态
FETCH_TIMEOUT = 20
UA = "Mozilla/5.0 (compatible; seo-suite-directory-tracker/1.0)"
ID_RE = re.compile(r"^DIR-(\d+)$")
# 文档追踪 CSV 的 14 列骨(init 解析失败时的兜底,与 md §三钉死的列一致)
FALLBACK_DOC_COLUMNS = ["Directory", "Tier", "URL", "Category", "DR", "Dofollow",
                        "Submission Date", "Status", "Live URL", "Backlink Verified",
                        "Positioning Variant Used", "Tags Used", "Account Email", "Notes"]
SL_TLD = {"co.uk", "org.uk", "ac.uk", "gov.uk", "com.au", "net.au", "co.jp", "ne.jp",
          "or.jp", "com.cn", "net.cn", "org.cn", "com.br", "com.mx", "com.tr",
          "co.kr", "co.in", "co.za", "com.sg", "com.hk"}


class FetchError(Exception):
    pass


USAGE = """usage: directory_tracker.py <init|add|list|verify|quarterly|export|import> [选项]
目录提交执行器(吃 references/research/directory-submissions.md 的追踪 CSV schema):
init 模板 → add 登记目录 → verify 现场核验(HEAD/GET + rel=nofollow)→ quarterly
季度复检(>90d)→ import/export CSV round-trip。

数据文件 CSV(默认当前目录,--file 可指定),列:
  ID, Directory, Tier, URL, Category, DR, Dofollow, Cost, Submission Date, Status,
  Live URL, Backlink Verified, Positioning Variant Used, Tags Used, Account Email, Notes
  (骨=文档 14 列;ID/Cost 为工具管理列)
  Dofollow: ?|dofollow|nofollow|sponsored|ugc / Status: pending|submitted|live|removed / Tier: 1-13

子命令:
  init --directories directory-submissions.md [--file F] [--json]
      解析文档"追踪 CSV 字段"列定义 → 生成空模板 CSV(Dofollow 后插 Cost、首位加
      ID);文件已存在 → 退出码 2(不覆写既有数据)。
  add --directory https://d.com --tier 2 [--dofollow ?] [--cost 0] [--dr N]
      [--category X] [--notes "..."] [--email a@b.c] [--live-url U] [--status pending]
      [--date YYYY-MM-DD] [--file F] [--json]
      登记目录:Directory=--directory 的可注册域,URL 原样;--dofollow 缺省 "?"
      (未知,待 verify);--cost 付费目录记账(默认 0);同域已登记 → 退出码 2。
  list [--status X] [--file F] [--json]
      表格(ID/Directory/Tier/Dofollow/Status/提交日/复检日)。
  verify --entry DIR-001 --target https://mysite.com [--file F] [--json]
      现场核验(模块级 fetch,测试打桩点):HEAD 目录页(liveness)→ GET 正文找
      指向 --target 的 <a>,查其 rel 限定属性(nofollow/sponsored/ugc,多值按空白拆;
      JSON checks.rel_qualifiers 列全)。200+dofollow → Status=live、
      Dofollow=dofollow、Backlink Verified=今天(退出码 0);404/410 → Status=
      removed(1);发现 nofollow/sponsored/ugc(1,result=<属性>_found)/ 找不到指向目标的链接(1,不盖 verified 章)/
      不可达(1,行不动)。SSRF:仅 http(s),私网/环回/链路本地/元数据地址拒。
  quarterly [--file F] [--json]
      季度复检队列:Status ∈ submitted/live 且(Backlink Verified 空 → 从未核验,
      或距今 >90d);非空 → 退出码 1(cron 消费,接 notify)。
  export [--out path] [--file F]
      导出 CSV 到 --out(缺省 stdout)。
  import --csv path [--file F] [--json]
      导入 CSV(列集须一致);按 ID 合并(已有 ID 替换、新 ID 追加);重复 ID → 2。

并发(R5,照 remediation.py):CSV 原子写 + flock;add/verify/import 全程持锁。

退出码: 0 正常 / 1 verify 有问题或 quarterly 队列非空 / 2 输入或参数错误。"""


def die(msg, with_usage=False):
    sys.stderr.write(msg + ("\n" + USAGE if with_usage else "") + "\n")
    sys.exit(2)


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0)


def today_str():
    return now_utc().date().isoformat()


def parse_date(s):
    """YYYY-MM-DD → date;非法 → None。"""
    try:
        return datetime.strptime((s or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_doc_columns(md_path):
    """解析 directory-submissions.md 的"追踪 CSV 字段:`A, B, ...`"行 → 列名列表。
    找不到 → 退出码 2(schema 是本工具的契约源头,不静默兜底)。"""
    try:
        with open(md_path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        die("读不了 --directories 文档: %s" % e)
    m = re.search(r"追踪\s*CSV\s*字段[：:]\s*`([^`]+)`", text)
    if not m:
        die("--directories 文档里找不到「追踪 CSV 字段:`...`」行(schema 契约源头): %s"
            % md_path)
    cols = [c.strip() for c in m.group(1).split(",") if c.strip()]
    need = {"Directory", "Tier", "URL", "Dofollow", "Status", "Live URL",
            "Backlink Verified"}
    missing = sorted(need - set(cols))
    if missing:
        die("文档追踪 CSV 列缺 %s(本工具依赖这些列): %s" % (",".join(missing), md_path))
    return cols


def template_columns(doc_cols):
    """文档 14 列骨 → 工具模板:首位加 ID,Dofollow 后插 Cost(主表 schema 的列)。"""
    cols = list(doc_cols)
    if "Cost" not in cols:
        cols.insert(cols.index("Dofollow") + 1, "Cost")
    return ["ID"] + cols


COLUMNS = template_columns(FALLBACK_DOC_COLUMNS)


def registrable_domain(url):
    """URL/域名 → 可注册域(照 citation_gaps.py 近似:末两段;双段后缀取三段)。"""
    host = (url or "").strip().lower()
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
    if "@" in host:
        host = host.split("@")[-1]
    if ":" in host:
        host = host.split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]
    parts = [p for p in host.split(".") if p]
    if not parts:
        return ""
    if len(parts) >= 3 and ".".join(parts[-2:]) in SL_TLD:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return parts[0]


def norm_url(u):
    """目录 URL 归一:缺 scheme 补 https://;非 http(s) 拒。"""
    u = (u or "").strip()
    if not u:
        return ""
    if "://" not in u:
        u = "https://" + u
    scheme = urllib.parse.urlparse(u).scheme.lower()
    if scheme not in ("http", "https"):
        die("--directory 仅接受 http(s) URL(或裸域名),得到 %r" % u)
    return u


# ---------------------------------------------------------------------------
# CSV 存取(load/save + 原子写 + flock,照 remediation.py)
# ---------------------------------------------------------------------------
def check_row(row, where):
    """单行最小校验;返回错误文案或 None。"""
    if not isinstance(row, dict):
        return "%s 不是对象" % where
    if not (row.get("ID") or "").strip():
        return "%s 缺 ID" % where
    if row.get("Status") not in STATUSES:
        return "%s 的 Status 非法(%r;合法值: %s)" % (where, row.get("Status"),
                                                    "|".join(STATUSES))
    if row.get("Dofollow") not in DOFOLLOW_VALUES:
        return "%s 的 Dofollow 非法(%r;合法值: %s)" % (where, row.get("Dofollow"),
                                                       "|".join(DOFOLLOW_VALUES))
    return None


def load_store(path, create=False):
    """读 CSV → (columns, rows);create=True 且不存在 → (None, []);结构不符 → 2。"""
    if not os.path.exists(path):
        if create:
            return None, []
        die("数据文件不存在: %s(先运行 init 生成模板)" % path)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            die("数据文件是空 CSV(缺表头): %s" % path)
        cols = [h.strip() for h in header]
        if set(cols) != set(COLUMNS) or len(cols) != len(COLUMNS):
            die("数据文件列集不符(应为 init 模板列): %s" % path)
        rows = []
        for n, raw in enumerate(reader, 2):
            if not raw or all(not c.strip() for c in raw):
                continue                                  # 空行跳过
            if len(raw) != len(cols):
                die("数据文件第 %d 行列数 %d ≠ %d: %s" % (n, len(raw), len(cols), path))
            rows.append(dict(zip(cols, (c.strip() for c in raw))))
    for n, row in enumerate(rows, 1):
        err = check_row(row, "第 %d 行" % n)
        if err:
            die("数据文件格式不符: %s(%s)" % (err, path))
    return cols, rows


def save_store(path, rows, cols=None):
    """原子写 CSV(tempfile + os.replace,照 remediation.py)。"""
    cols = cols or COLUMNS
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".tmp-", dir=d)
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for r in rows:
                w.writerow([r.get(c, "") for c in cols])
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


@contextlib.contextmanager
def data_lock(path, timeout=120.0):
    """文件级 flock(照 remediation.py data_lock);超时 → 警告并跳过本次写。"""
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    lock_path = os.path.join(d, "." + os.path.basename(path) + ".lock")
    fh = open(lock_path, "w")
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                if fcntl:
                    fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                else:
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise SystemExit(
                        "警告: 另一 directory_tracker 进程持有 %s 超过 %.0fs,"
                        "跳过本次写(防并发覆盖丢失)" % (lock_path, timeout))
                time.sleep(0.5)
        yield
    finally:
        try:
            if fcntl:
                fcntl.flock(fh, fcntl.LOCK_UN)
            else:
                try:
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:  # 等锁超时、没拿到锁时解锁会报错;close 也会释放锁
                    pass
        finally:
            fh.close()


def next_id(rows):
    mx = 0
    for r in rows:
        m = ID_RE.match((r.get("ID") or "").strip())
        if m:
            mx = max(mx, int(m.group(1)))
    return "DIR-%03d" % (mx + 1)


def sort_key(row):
    m = ID_RE.match((row.get("ID") or "").strip())
    return (0, int(m.group(1)), "") if m else (1, 0, row.get("ID", ""))


# ---------------------------------------------------------------------------
# 网络层(verify 现场核验;fetch 为模块级单点,测试打桩点)
# ---------------------------------------------------------------------------
def _ssrf_guard(hostname):
    """仅 http(s) 可达公网:私网/环回/链路本地/元数据地址拒(照 monitor.py 精简)。"""
    try:
        infos = socket.getaddrinfo(hostname or "", None)
    except OSError as e:
        raise FetchError("DNS 解析失败 %s: %s" % (hostname, e))
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified):
            raise FetchError("SSRF 拒绝: %s 解析到非公网地址 %s" % (hostname, ip))


class _RedirectGuard(urllib.request.HTTPRedirectHandler):
    """重定向逐跳复查目标 host(照 monitor.py:_RedirectGuard 同思路)。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p = urllib.parse.urlparse(newurl)
        if p.scheme not in ("http", "https"):
            raise FetchError("重定向到非 http(s): %s" % newurl)
        _ssrf_guard(p.hostname)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_RedirectGuard)


def _request(url, method, timeout):
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https"):
        raise FetchError("仅允许 http(s): %s" % url)
    _ssrf_guard(p.hostname)
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "text/html,*/*"},
                                 method=method)
    try:
        with _OPENER.open(req, timeout=timeout) as r:
            body = r.read(2 * 1024 * 1024) if method == "GET" else b""
            return {"status": r.status, "final_url": r.geturl(),
                    "body": body.decode("utf-8", "replace")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "final_url": url, "body": ""}
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise FetchError("抓取失败 %s: %s" % (url, e))


def fetch(url, timeout=FETCH_TIMEOUT):
    """目录页核验取数:HEAD 查 liveness → 200/405/501 再 GET 正文(dofollow 检查)。
    返回 {"head_status", "status", "body"};网络层失败抛 FetchError。"""
    head = _request(url, "HEAD", timeout)
    res = {"head_status": head["status"], "status": head["status"], "body": ""}
    if head["status"] in (200, 405, 501):
        got = _request(url, "GET", timeout)
        res["status"], res["body"] = got["status"], got["body"]
    return res


ANCHOR_RE = re.compile(r"<a\b([^>]*)>", re.I)
HREF_RE = re.compile(r"""href\s*=\s*["']?([^"'>\s]+)""", re.I)
REL_RE = re.compile(r"""rel\s*=\s*["']?([^"'>]+)["']?""", re.I)


def _target_rels(body, target):
    """正文 → 指向 target 域的每个 <a> 的 rel token 集合列表;target 无域 → None。"""
    tdom = registrable_domain(target)
    if not tdom:
        return None
    out = []
    for m in ANCHOR_RE.finditer(body or ""):
        attrs = m.group(1)
        hm = HREF_RE.search(attrs)
        if not hm or not hm.group(1):
            continue
        h = registrable_domain(hm.group(1))
        if h != tdom and not h.endswith("." + tdom):
            continue
        rm = REL_RE.search(attrs)
        out.append(set(rm.group(1).lower().split()) if rm else set())   # 多值按空白拆
    return out


def rel_qualifiers(body, target):
    """指向 target 的锚点上出现过的限定属性(按 REL_QUALIFIERS 顺序,去重)。"""
    seen = set().union(*(_target_rels(body, target) or [set()]))
    return [q for q in REL_QUALIFIERS if q in seen]


def check_dofollow(body, target):
    """正文 → (anchor_found, "dofollow"|"nofollow"|"sponsored"|"ugc"):找 href 指向
    target 域的 <a>,查其 rel 的限定属性(B60 修:Google 文档三个限定属性 sponsored/
    ugc/nofollow 都不是 dofollow;修前只认 nofollow)。多处锚点不一致时保守:任一锚点
    带限定属性就按限定记,多个时按 REL_QUALIFIERS 优先级取一个,全部见 rel_qualifiers()。"""
    rels = _target_rels(body, target)
    if not rels:
        return False, "?"
    quals = rel_qualifiers(body, target)
    return True, (quals[0] if quals else "dofollow")


# ---------------------------------------------------------------------------
# 子命令
# ---------------------------------------------------------------------------
def _parse(rest, cmd, val_spec, flag_spec):
    val = dict(val_spec, **{"--file": DEFAULT_FILE})
    flag = dict(flag_spec)
    i = 0
    while i < len(rest):
        a = rest[i]
        if a in val:
            if i + 1 >= len(rest):
                die("%s 需要一个值" % a, with_usage=True)
            val[a] = rest[i + 1]; i += 2
        elif a in flag:
            flag[a] = True; i += 1
        else:
            die("未知参数 %r(%s 子命令)" % (a, cmd), with_usage=True)
    return val, flag


def cmd_init(rest):
    val, flag = _parse(rest, "init", {"--directories": None}, {"--json": False})
    if not val["--directories"]:
        die("缺少 --directories(指向 references/research/directory-submissions.md,"
            "本工具的 CSV schema 契约源头)\n" + USAGE)
    if os.path.exists(val["--file"]):
        die("数据文件已存在,不覆写: %s" % val["--file"])
    doc_cols = parse_doc_columns(val["--directories"])
    cols = template_columns(doc_cols)
    with data_lock(val["--file"]):
        save_store(val["--file"], [], cols)
    if flag["--json"]:
        print(json.dumps({"schema_version": SCHEMA_VERSION,
                          "file": os.path.abspath(val["--file"]), "columns": cols,
                          "doc_columns": doc_cols, "rows": 0},
                         ensure_ascii=False, indent=1))
    else:
        print("init: 模板 → %s(骨=文档 %d 列 + ID/Cost 管理列,共 %d 列,0 行)"
              % (os.path.abspath(val["--file"]), len(doc_cols), len(cols)))
    return 0


def cmd_add(rest):
    val, flag = _parse(
        rest, "add",
        {"--directory": None, "--tier": None, "--dofollow": "?", "--cost": "0",
         "--dr": "", "--category": "", "--notes": "", "--email": "",
         "--live-url": "", "--status": "pending", "--date": ""},
        {"--json": False})
    if not val["--directory"]:
        die("缺少 --directory\n" + USAGE)
    url = norm_url(val["--directory"])
    domain = registrable_domain(url)
    if not domain or "." not in domain:
        die("--directory 解析不出可注册域: %r" % val["--directory"])
    try:
        tier = int(val["--tier"])
    except (TypeError, ValueError):
        die("--tier 需为 1-13 的整数(文档 13 层目录结构)")
    if tier not in TIERS:
        die("--tier 超出 1-13: %r" % val["--tier"])
    dof = (val["--dofollow"] or "?").strip().lower()
    if dof not in DOFOLLOW_VALUES:
        die("--dofollow 非法 %r;合法值: %s" % (val["--dofollow"], "|".join(DOFOLLOW_VALUES)))
    try:
        cost = float(val["--cost"])
    except (TypeError, ValueError):
        die("--cost 需为数字: %r" % val["--cost"])
    if cost < 0:
        die("--cost 不能为负: %r" % val["--cost"])
    status = val["--status"]
    if status not in STATUSES:
        die("--status 非法 %r;合法值: %s" % (status, "|".join(STATUSES)))
    if val["--dr"]:
        try:
            int(val["--dr"])
        except (TypeError, ValueError):
            die("--dr 需为整数(DR 是近似值,提交前用 Ahrefs/Moz 复核——文档诚实条款)")
    sub_date = val["--date"] or (today_str() if status in ("submitted", "live") else "")
    if sub_date and not parse_date(sub_date):
        die("--date 需为 YYYY-MM-DD: %r" % sub_date)
    row = None
    with data_lock(val["--file"]):
        _, rows = load_store(val["--file"], create=True)
        if any((r.get("Directory") or "").lower() == domain for r in rows):
            die("目录 %s 已登记(同域不重复)" % domain)
        row = {"ID": next_id(rows), "Directory": domain, "Tier": str(tier), "URL": url,
               "Category": val["--category"], "DR": val["--dr"], "Dofollow": dof,
               "Cost": ("%g" % cost), "Submission Date": sub_date, "Status": status,
               "Live URL": val["--live-url"], "Backlink Verified": "",
               "Positioning Variant Used": "", "Tags Used": "",
               "Account Email": val["--email"], "Notes": val["--notes"]}
        rows.append(row)
        save_store(val["--file"], rows)
    if flag["--json"]:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "added": row},
                       ensure_ascii=False, indent=1))
    else:
        print("add: %s [%s] tier=%s dofollow=%s cost=%g status=%s → %s"
              % (row["ID"], domain, row["Tier"], dof, cost, status,
                 os.path.abspath(val["--file"])))
    return 0


def cmd_list(rest):
    val, flag = _parse(rest, "list", {"--status": None}, {"--json": False})
    if val["--status"] is not None and val["--status"] not in STATUSES:
        die("--status 非法 %r;合法值: %s" % (val["--status"], "|".join(STATUSES)))
    _, rows = load_store(val["--file"])
    sel = [r for r in sorted(rows, key=sort_key)
           if val["--status"] is None or r["Status"] == val["--status"]]
    if flag["--json"]:
        print(json.dumps({"schema_version": SCHEMA_VERSION,
                          "file": os.path.abspath(val["--file"]),
                          "count": len(sel), "items": sel}, ensure_ascii=False, indent=1))
        return 0
    cols = ("ID", "DIRECTORY", "T", "DOFOLLOW", "STATUS", "SUBMITTED", "VERIFIED", "COST")
    table = [[r["ID"], r["Directory"], r["Tier"], r["Dofollow"], r["Status"],
              r.get("Submission Date") or "-", r.get("Backlink Verified") or "-",
              r.get("Cost") or "0"] for r in sel]
    widths = [len(c) for c in cols]
    for r in table:
        for n, v in enumerate(r):
            widths[n] = max(widths[n], len(v))
    L = [" ".join(c.ljust(widths[n]) for n, c in enumerate(cols)).rstrip(),
         " ".join("-" * w for w in widths)]
    for r in table:
        L.append(" ".join(v.ljust(widths[n]) for n, v in enumerate(r)).rstrip())
    print("\n".join(L))
    print("共 %d 条%s" % (len(sel),
                          " → %s" % val["--file"] if val["--file"] != DEFAULT_FILE else ""))
    return 0


def cmd_verify(rest):
    val, flag = _parse(rest, "verify", {"--entry": None, "--target": None},
                       {"--json": False})
    tid = val["--entry"]
    if tid is None:
        die("缺少 --entry(verify --entry DIR-001 --target https://mysite.com)\n" + USAGE)
    if not val["--target"]:
        die("缺少 --target(核验 dofollow 要知道找哪个站的锚点)\n" + USAGE)
    listing = None
    with data_lock(val["--file"]):
        _, rows = load_store(val["--file"])
        row = next((r for r in rows if r["ID"] == tid), None)
        if row is None:
            die("找不到条目 %r(%s 中共 %d 条)" % (tid, val["--file"], len(rows)))
        listing = (row.get("Live URL") or "").strip() or (row.get("URL") or "").strip()
        if not listing:
            die("条目 %s 无 Live URL/URL 可核验" % tid)
        try:
            res = fetch(listing)
        except FetchError as e:
            if flag["--json"]:
                print(json.dumps({"schema_version": SCHEMA_VERSION, "entry": tid,
                                  "result": "unreachable", "error": str(e)},
                                 ensure_ascii=False, indent=1))
            else:
                print("verify: %s 不可达(%s)——行未改动,稍后重试" % (tid, e))
            return 1
        checks = {"reachable": res["status"] < 400,
                  "status_code": res["status"],
                  "anchor_found": False, "dofollow": "?", "rel_qualifiers": []}
        if res["status"] >= 400:
            row["Status"] = "removed"
            row["Backlink Verified"] = today_str()      # 核验过:确实没了
            row["Notes"] = (row.get("Notes") or "") + ("; " if row.get("Notes") else "") \
                + "verify %s: HTTP %d" % (today_str(), res["status"])
            result = "removed"
        else:
            anchor_found, dof = check_dofollow(res["body"], val["--target"])
            checks["anchor_found"], checks["dofollow"] = anchor_found, dof
            checks["rel_qualifiers"] = rel_qualifiers(res["body"], val["--target"])
            if not anchor_found:
                result = "anchor_missing"              # 页在但找不到指向目标的链接
            elif dof in REL_QUALIFIERS:
                row["Status"] = "live"
                row["Dofollow"] = dof
                row["Backlink Verified"] = today_str()
                row["Notes"] = (row.get("Notes") or "") + ("; " if row.get("Notes") else "") \
                    + "verify %s: 转 %s(文档诚实条款:目录可能悄悄转)" % (
                        today_str(), " ".join(checks["rel_qualifiers"]))
                result = dof + "_found"
            else:
                row["Status"] = "live"
                row["Dofollow"] = "dofollow"
                row["Backlink Verified"] = today_str()
                result = "verified"
        save_store(val["--file"], rows)
    if flag["--json"]:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "entry": tid,
                          "directory": row["Directory"], "listing": listing,
                          "result": result, "checks": checks, "row": row},
                         ensure_ascii=False, indent=1))
    else:
        msg = {"verified": "在链 + dofollow(Backlink Verified=%s)" % today_str(),
               "removed": "目录页 HTTP %d → 已标 removed" % res["status"],
               "nofollow_found": "页在但锚点 rel=nofollow(目录悄悄转 nofollow)",
               "sponsored_found": "页在但锚点 rel=sponsored(付费链接,不传权)",
               "ugc_found": "页在但锚点 rel=ugc(用户生成内容链接,不传权)",
               "anchor_missing": "页在但未找到指向 %s 的链接(不盖 verified 章)"
                                 % registrable_domain(val["--target"])}[result]
        print("verify: %s [%s] %s" % (tid, row["Directory"], msg))
    return 0 if result == "verified" else 1


def cmd_quarterly(rest):
    val, flag = _parse(rest, "quarterly", {}, {"--json": False})
    _, rows = load_store(val["--file"])
    today = now_utc().date()
    queue = []
    for r in sorted(rows, key=sort_key):
        if r["Status"] not in RECHECK_STATUSES:
            continue
        bv = parse_date(r.get("Backlink Verified"))
        if bv is None:
            reason, days = "从未核验", None
        else:
            days = (today - bv).days
            if days <= QUARTERLY_DAYS:
                continue
            reason = "上次核验 %dd 前(>%dd)" % (days, QUARTERLY_DAYS)
        queue.append({"id": r["ID"], "directory": r["Directory"], "tier": r["Tier"],
                      "status": r["Status"], "dofollow": r["Dofollow"],
                      "backlink_verified": r.get("Backlink Verified") or "",
                      "stale_days": days, "reason": reason,
                      "live_url": (r.get("Live URL") or r.get("URL") or "")})
    if flag["--json"]:
        print(json.dumps({"schema_version": SCHEMA_VERSION,
                          "file": os.path.abspath(val["--file"]),
                          "queue": len(queue), "threshold_days": QUARTERLY_DAYS,
                          "items": queue}, ensure_ascii=False, indent=1))
    else:
        print("季度复检队列(上次 verified >%d 天 或 从未核验,%d 条):"
              % (QUARTERLY_DAYS, len(queue)))
        for q in queue:
            print("- %s [%s|T%s|%s] %s — %s" % (q["id"], q["directory"], q["tier"],
                                                q["status"], q["reason"],
                                                "python3 directory_tracker.py verify "
                                                "--entry %s --target <site>" % q["id"]))
        if not queue:
            print("  (空;全部条目在 %d 天内核验过)" % QUARTERLY_DAYS)
    return 1 if queue else 0


def cmd_export(rest):
    val, flag = _parse(rest, "export", {"--out": None}, {})
    cols, rows = load_store(val["--file"])
    if val["--out"]:
        save_store(val["--out"], rows, cols)
        print("export: %d 条 → %s" % (len(rows), os.path.abspath(val["--out"])))
    else:
        w = csv.writer(sys.stdout, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow([r.get(c, "") for c in cols])
    return 0


def cmd_import(rest):
    val, flag = _parse(rest, "import", {"--csv": None}, {"--json": False})
    if not val["--csv"]:
        die("缺少 --csv\n" + USAGE)
    src_cols, src_rows = load_store(val["--csv"])
    seen = set()
    for r in src_rows:
        if r["ID"] in seen:
            die("导入文件 ID 重复: %s" % r["ID"])
        seen.add(r["ID"])
    merged = None
    with data_lock(val["--file"]):
        _, rows = load_store(val["--file"], create=True)
        by_id = {r["ID"]: r for r in rows}
        replaced = added = 0
        for r in src_rows:
            if r["ID"] in by_id:
                by_id[r["ID"]] = r
                replaced += 1
            else:
                by_id[r["ID"]] = r
                added += 1
        merged = sorted(by_id.values(), key=sort_key)
        save_store(val["--file"], merged)
    if flag["--json"]:
        print(json.dumps({"schema_version": SCHEMA_VERSION, "imported": len(src_rows),
                          "replaced": replaced, "added": added, "total": len(merged)},
                         ensure_ascii=False, indent=1))
    else:
        print("import: %d 条(替换 %d / 新增 %d)→ 共 %d 条(%s)"
              % (len(src_rows), replaced, added, len(merged),
                 os.path.abspath(val["--file"])))
    return 0


COMMANDS = {"init": cmd_init, "add": cmd_add, "list": cmd_list, "verify": cmd_verify,
            "quarterly": cmd_quarterly, "export": cmd_export, "import": cmd_import}


def main():
    argv = sys.argv[1:]
    if any(a in ("-h", "--help") for a in argv):
        print(USAGE)
        return 0
    if not argv:
        sys.stderr.write("缺少子命令\n" + USAGE + "\n")
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd not in COMMANDS:
        die("未知子命令 %r;合法值: %s" % (cmd, "|".join(COMMANDS)), with_usage=True)
    return COMMANDS[cmd](rest)


if __name__ == "__main__":
    sys.exit(main())
