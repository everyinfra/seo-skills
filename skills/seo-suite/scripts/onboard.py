#!/usr/bin/env python3
"""onboard.py — 开局 6 环:先吃透产品,再一环一环问用户(RQ-237;stdlib only)。

流程:
  start    建工作区(没有就调 project.py init)→ product_scan.py 读站点和仓库 → lifecycle.py 判阶段和成熟度
           → 起草产品档案 seo-ops/context/profile.json + product.md → 打印第 1 环
  show     打印某一环(默认当前环):agent 先做什么、草稿事实(带出处)、问题(带猜测和选项)、停下的指令
  note     agent 把自己查到的东西记进档案(一律「未确认」,用户确认前不当事实用)
  answer   记用户的回答:--quote 必须是用户这次回话的原文(太短的只收「对 / Yes」这类确认词,且不能带 --correct);
           --confirm 确认这一环(必答题答齐、这一环问过才行);列表字段的 --correct 只写一项时只换那一项
  skip     用户明确说要跳过(「跳过」「skip」「不用问了」):第 1 环没确认就拒绝(退出码 3),确认过就把剩下的环标
           「跳过」、用猜测补齐;「按你的判断来 / best guess / carry on」不是跳过,也拒绝(退出码 3)
  event    记改版类事件(migration / new_product_line …),阶段会切到「改版 / 迁移 / 转型」
  status   一屏:每环状态、档案版本、阶段
  diagnose 重跑阶段 × 成熟度诊断

规矩(红队 11-08):
  - 第 1 环必须由用户确认:没有 --quote 不能确认;这一环没 show 过不能确认。
  - show 打印一整块「原样发给用户」的停下文本(编号问题、选项、事实出处),agent 原样贴出,不改写。
  - 档案只经脚本写:每次写入记内容校验值,读到手改过的档案就报警,受影响的环退回待确认。
  - 网页上抓来的东西只当草稿(status=unconfirmed),用户确认这一环后才变 confirmed。
  - 敏感答案(处罚史、预算、审批人)存 context/private/,该目录写进 seo-ops/.gitignore。
  - 第 5 环「明确不做」的答案进 profile.deny(结构化禁用清单),下游推荐按它过滤(playbook.load_deny 和
    teach.py 记的 seo-ops/playbook/deny.json 合并成一份)。
  - 仓库里有 marketingskills 的 .agents/product-marketing.md:开局读它当草稿;某一环确认或纠正后,
    把改过的条目写回去(pm_context.py:只改对应那一行,别的段落字节不变,照对方规矩升版本、加 Changelog)。

状态文件:seo-ops/context/profile.json(schema 1)、product.md(人读,带版本和变更记录)、
scan.json、diagnosis.json、private/answers.json。不写 project.yaml,不改工作区 schema 版本。

用法:
  python3 onboard.py start --site https://example.com [--repo .] [--market en] [--ws seo-ops] [--allow-local] [--scan FILE]
  python3 onboard.py show [--ring N] [--json]
  python3 onboard.py note --ring 3 --key competitors.serp --value "a.com,b.com" --source "serp_overlap.py 2026-11-08"
  python3 onboard.py answer --ring 1 --set conversion=注册 --set customers="做 AI agent 的团队" \\
          --correct product.one_liner="…" --quote "用户原话" --confirm
  python3 onboard.py skip --quote "别问了,直接给方案"
  python3 onboard.py event add migration --note "要把 /blog 改成 /articles"
  python3 onboard.py metric --set gsc_clicks_28d=1200 --set gsc_clicks_prev_28d=1000 --set gsc_impressions_28d=50000 \\
          --source "gsc_api.py 2026-10-11..11-07"
  python3 onboard.py status [--json]
退出码:0 正常;2 用法 / 工作区错;3 被门挡住(第 1 环没确认就想跳过、没问过就想确认、必答题没答齐)。
"""
import argparse
import datetime as dt
import ipaddress
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lifecycle  # noqa: E402
import pm_context  # noqa: E402

PY = sys.executable or "python3"
BANK_PATH = os.path.join(os.path.dirname(HERE), "data", "onboarding.json")
SCHEMA = 1
PRIVATE_IGNORE = "context/private/"
BLOCK_START = "===== 下面这块原样发给用户"
BLOCK_END = "===== 原样发给用户到这里为止"
ARGV = []                                          # 这次的命令行(报错里给照抄命令用;main 填)


class UsageError(Exception):
    code = 2


class GateError(Exception):
    code = 3


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def bank():
    b = read_json(BANK_PATH)
    if not b:
        raise UsageError("读不到问题库 %s" % BANK_PATH)
    return {r["ring"]: r for r in b["rings"]}


def ws_dir(ns):
    """--ws 给了用它,否则 ./seo-ops;落在 skill 安装目录里、或当前目录没有工作区 → 退出码 2,不新建。"""
    return lifecycle.resolve_ws(ns.ws, __file__, ARGV)


def start_ws(ns):
    """start 的工作区:--ws > <--repo>/seo-ops > ./seo-ops;不许落在 skill 安装目录里(这时什么都还没写)。"""
    repo = os.path.abspath(ns.repo) if ns.repo else None
    explicit = ns.ws or (os.path.join(repo, lifecycle.OPS_DIR) if repo else None)
    return lifecycle.resolve_ws(explicit, __file__, ARGV, must_exist=False,
                                repo=repo if repo and not lifecycle.inside_skill(repo) else None)


def ob_cmd(ws, *args):
    """屏幕上教 agent 的 onboard.py 命令:脚本绝对路径 + 参数 + --ws <工作区绝对路径>(在哪个目录跑都对)。"""
    return "python3 %s %s --ws %s" % (os.path.join(HERE, "onboard.py"), " ".join(args), shlex.quote(ws))


def ctx(ws, *parts):
    return os.path.join(ws, "context", *parts)


def warn(msg):
    print("注意: %s" % msg, file=sys.stderr)


def load_profile(ws):
    path = ctx(ws, "profile.json")
    if not os.path.isfile(path):
        raise UsageError("还没开局:先跑 onboard.py start --site <URL>(工作区 %s)" % ws)
    try:
        with open(path, encoding="utf-8") as f:
            p = json.load(f)
    except ValueError as e:
        raise UsageError("profile.json 不是合法的 JSON(%s)。档案只能经 onboard.py 写;"
                         "从 git 恢复上一版,或 start --force 重新开局" % e)
    except OSError as e:
        raise UsageError("读不了 %s:%s" % (path, e))
    try:
        if int(p.get("schema") or 0) > SCHEMA:
            raise UsageError("档案是更新版本的 seo-suite 写的(schema %s),先升级 skill" % p.get("schema"))
    except (TypeError, ValueError, AttributeError):
        raise UsageError("profile.json 的 schema 不是数字")
    tamper = lifecycle.check_seal(p)
    problems = lifecycle.normalize_profile(p)
    want = lifecycle.profile_format(json.loads(json.dumps(p)))["_schema"]
    schema_fixed = p.get("_schema") != want and not (tamper and tamper.get("legacy"))
    for msg in problems:
        warn("档案不合格:" + msg)
    changes = []
    if problems:
        changes.append("补默认值:" + ";".join(problems))
    if schema_fixed:
        warn("顶层 _schema 和脚本写的映射不一样,已写回脚本那份(_schema 由脚本维护,不算手改;事实在 facts[])")
        changes.append("_schema 写回脚本的映射")
    if tamper and tamper.get("legacy"):
        warn("档案没有校验值(旧版 seo-suite 写的或手写的);从这次起由脚本记校验值,以后手改会被发现")
        changes.append("补校验值")
    elif tamper:
        warn(lifecycle.tamper_message(tamper))
        reopened = reopen_rings(p, tamper["rings"])
        if reopened:
            warn("要重新确认:第 %s 环(onboard.py show --ring %d,把改后的内容给用户看,用户确认后再 answer --confirm)"
                 % ("、".join(map(str, reopened)), reopened[0]))
        changes.append("发现手改(第 %s 环),%s" % ("、".join(map(str, tamper["rings"])) or "环以外",
                                                ("退回待确认:第 %s 环" % "、".join(map(str, reopened))) if reopened else "没有要退回的环"))
    if changes:
        save_profile(ws, p, ";".join(changes))
    return p


def reopen_rings(prof, rings):
    """手改过、原来已确认或跳过的环退回「问了在等回答」,这一环的已确认事实退回未确认;→ 退回的环号。"""
    out = []
    pre = lifecycle.ring_prefixes()
    for r in rings:
        ring = prof["rings"].get(str(r))
        if not ring or ring.get("status") not in ("confirmed", "skipped"):
            continue
        ring.update({"status": "asking", "asked_at": None, "confirmed_at": None,
                     "reopened": {"at": now(), "why": "档案被手改"}})
        for f in prof.get("facts") or []:
            if lifecycle.fact_ring(f, pre) == r and f.get("status") == "confirmed":
                f["status"] = "unconfirmed"
        if r == 1 and isinstance(prof.get("stage"), dict):
            prof["stage"]["confirmed"] = False
        out.append(r)
    return out


def save_profile(ws, prof, change):
    lifecycle.profile_format(prof)
    prof["version"] = int(prof.get("version") or 0) + 1
    prof["updated"] = now()
    prof.setdefault("changelog", []).append({"version": prof["version"], "at": prof["updated"], "change": change})
    if isinstance(prof.get("rings"), dict):
        prof["current_ring"] = current_ring(prof)
    lifecycle.seal_profile(prof)
    write_json(ctx(ws, "profile.json"), prof)
    with open(ctx(ws, "product.md"), "w", encoding="utf-8") as f:
        f.write(render_product_md(prof))


def ensure_private_ignored(ws):
    gi = os.path.join(ws, ".gitignore")
    try:
        text = open(gi, encoding="utf-8").read()
    except OSError:
        text = ""
    if PRIVATE_IGNORE not in text.split():
        with open(gi, "a", encoding="utf-8") as f:
            if text and not text.endswith("\n"):
                f.write("\n")
            f.write("# 开局里的敏感答案(处罚史、预算、审批人),不进 git\n%s\n" % PRIVATE_IGNORE)


def current_ring(prof):
    for r in range(1, 7):
        st = prof["rings"][str(r)]["status"]
        if st not in ("confirmed", "skipped"):
            return r
    return None


def ring_facts(prof, ring_def):
    pre = tuple(ring_def.get("fact_prefixes") or ())
    return [f for f in prof.get("facts") or [] if f.get("ring") == ring_def["ring"]
            or (pre and str(f.get("key", "")).startswith(pre) and f.get("ring") is None)]


def fact_value(prof, key):
    for f in prof.get("facts") or []:
        if f.get("key") == key:
            return f.get("value")
    return None


# 第 1 环这两问的回答同时记成事实(档案 _schema 按事实键找它们);列表类事实拆成列表存
ANSWER_FACTS = {"customers": "customers", "conversion": "conversion.primary"}
LIST_SEP = ";"                                   # 屏幕上教 agent 用的分隔符
STRONG_SEPS = ";\uff1b|\uff5c\u3001\n"            # ; ; | | 、 换行:出现就只按它们拆
SOFT_SEPS = ",\uff0c"                             # 逗号:一项里可能自带(「Portland, Maine」),没有强分隔符时才拆
DENY_SEPS = ";\uff1b|\uff5c\u3001\n"               # 禁用项是一句话:不按英文逗号拆


def _split_on(text, seps):
    out, buf, depth = [], "", 0
    for ch in text:
        if ch in "(\uff08[":
            depth += 1
        elif ch in ")\uff09]" and depth:
            depth -= 1
        if ch in seps and not depth:
            if buf.strip():
                out.append(buf.strip())
            buf = ""
            continue
        buf += ch
    if buf.strip():
        out.append(buf.strip())
    return out


def split_list(v):
    """「A;B(x, y)|C」→ [A, B(x, y), C]。有分号、竖线、顿号、换行就只按它们拆;都没有才按逗号拆,
    而且要拆出三段以上、每段都像一个条目(不超过 60 个字符),否则当一整项。括号里的不拆。已是列表原样返回。"""
    if isinstance(v, list):
        return v
    text = str(v)
    depth_free = re.sub(r"[(\uff08\[][^)\uff09\]]*[)\uff09\]]", "", text)
    if any(ch in depth_free for ch in STRONG_SEPS):
        return _split_on(text, STRONG_SEPS)
    parts = _split_on(text, SOFT_SEPS)
    if len(parts) >= 3 and all(len(x) <= 60 for x in parts):
        return parts                              # 三项以上的逗号串才当清单;两段的(「Portland, Maine」)当一整项
    return [text.strip()] if text.strip() else []


def split_deny(v):
    """第 5 环「明确不做」:一句完整的话不拆;只按分号、竖线、换行分成几条(括号里的不拆)。"""
    return _split_on(str(v), DENY_SEPS)


def fact_shape(key, v):
    return split_list(v) if key in lifecycle.PROFILE_LIST_KEYS and v not in (None, "") else v


def upsert_fact(prof, key, value, status, ring, quote, source):
    """同 key 的第一条事实改成新值(没有就加一条);别的同 key 条目不动。"""
    rec = {"value": fact_shape(key, value), "status": status, "quote": quote, "at": now(), "source": source}
    f = next((x for x in prof["facts"] if x.get("key") == key), None)
    if f is None:
        f = {"key": key, "kind": "fact", "ring": ring}
        prof["facts"].append(f)
    if f.get("value") not in (None, "", []) and status == "unknown":
        f["guess"] = f.get("value")
    f.update(rec)
    return f


def fmt_val(v):
    if isinstance(v, list):
        return "、".join(str(x) if not isinstance(x, dict) else (x.get("text") or json.dumps(x, ensure_ascii=False)) for x in v[:8])
    if isinstance(v, dict):
        return "、".join("%s %s" % (k, v[k]) for k in list(v)[:10])
    return str(v)


# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------

def facts_from_scan(scan):
    """scan 的事实 → 档案事实;全部 unconfirmed,标所属环(按 key 前缀)。"""
    b = bank()
    out = []
    for f in (scan or {}).get("facts") or []:
        key = str(f.get("key") or "")
        ring = next((r for r, d in b.items() if key.startswith(tuple(d.get("fact_prefixes") or ()))), None)
        rec = {"key": key, "value": f.get("value"), "source": f.get("source"),
               "kind": f.get("kind") or "inferred", "status": "unconfirmed", "ring": ring, "at": now()}
        for extra in ("note", "enum", "billing"):
            if f.get(extra):
                rec[extra] = f[extra]
        out.append(rec)
    return out


def merge_pm_facts(facts, repo):
    """.agents/product-marketing.md 里填了的条目当草稿:同 key 的用它的值(人写的,比抓来的准),抓来的值留在 site_value。"""
    b = bank()
    for pf in pm_context.draft_facts(repo):
        ring = next((r for r, d in b.items() if pf["key"].startswith(tuple(d.get("fact_prefixes") or ()))), None)
        cur = next((f for f in facts if f["key"] == pf["key"]), None)
        if cur:
            if known_value(cur.get("value")) and fmt_val(cur.get("value")) != fmt_val(pf["value"]):
                cur["site_value"], cur["site_source"] = cur.get("value"), cur.get("source")
            cur.pop("note", None)
            cur.update({"value": pf["value"], "source": pf["source"], "kind": "fact"})
        else:
            facts.append({"key": pf["key"], "value": pf["value"], "source": pf["source"], "kind": "fact",
                          "status": "unconfirmed", "ring": ring, "at": now()})
    return facts


def sync_pm_context(ws, prof, ring):
    """某一环确认后,把改过的条目写回 .agents/product-marketing.md(没有这份文件就什么都不做)。"""
    repo = lifecycle.profile_repo(ws, prof) or os.path.dirname(ws)
    ups = pm_context.updates_from_profile(prof, ring)
    if not ups:
        return None
    res = pm_context.write_back(repo, ups, "seo-suite onboarding ring %d: user-confirmed" % ring)
    if res and res["changed"]:
        text = pm_context.read_file(repo) or ""
        import hashlib
        prof["context_sync"] = {"path": res["path"], "at": now(), "ring": ring,
                                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                                "fields": ["%s/%s" % (c["section"], c["label"]) for c in res["changed"]]}
    return res


def run_json(cmd, out_path):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    data = read_json(out_path) if out_path and os.path.isfile(out_path) else None
    return p.returncode, data, (p.stderr or "")[-800:]


def ws_banner(ws, to_stderr=False):
    """start 第一屏的第一行:工作区在哪、后面的命令在哪跑。"""
    msg = ("工作区:%s(档案、体检、方案都写在这里)。后面的命令在 %s 里跑,或者每条都带 --ws %s;"
           "下面打印的命令已经带上了。" % (ws, os.path.dirname(ws), shlex.quote(ws)))
    print(msg, file=sys.stderr if to_stderr else sys.stdout)


def cmd_start(ns):
    if not ns.site and not ns.repo:
        raise UsageError("至少给 --site 或 --repo")
    host = (urllib.parse.urlsplit(ns.site if "://" in (ns.site or "") else "http://%s" % (ns.site or "")).hostname or "")
    if ns.site and is_loopback(host) and not ns.allow_local:
        # 本机地址不加 --allow-local 一页都读不到,起出来的草稿只有仓库那一半;先停,这次什么都不写
        raise UsageError("站点 %s 是本机地址:审本机开发站加 --allow-local 重跑(%s);这次什么都没写"
                         % (ns.site, lifecycle.shell_cmd(__file__, ARGV + ["--allow-local"])))
    ws = start_ws(ns)
    if os.path.isfile(ctx(ws, "profile.json")) and not ns.force:
        old = read_json(ctx(ws, "profile.json"), {}) or {}
        if not ring1_touched(old):
            print("第 1 环还没有用户的回答,按这次的参数重新读产品(档案里没有要保留的用户答案)")
        else:
            ws_banner(ws, ns.json)
            print("已经开过局(%s);接着问用 %s,要从头来加 --force" % (ctx(ws, "profile.json"), ob_cmd(ws, "show")))
            return cmd_show(argparse.Namespace(ws=ws, ring=None, json=False))
    if not os.path.isfile(os.path.join(ws, "project.yaml")):
        if not ns.site:
            os.makedirs(ws, exist_ok=True)
        else:
            init = [PY, os.path.join(HERE, "project.py"), "init", "--site", ns.site, "--dir", ws]
            if ns.market:
                init += ["--market", ns.market]
            p = subprocess.run(init, capture_output=True, text=True, encoding="utf-8")
            if p.returncode != 0:
                raise UsageError("project.py init 失败:%s" % (p.stderr or p.stdout)[-400:])
    os.makedirs(ctx(ws), exist_ok=True)
    ensure_private_ignored(ws)
    if ns.allow_local:
        remember_allow_local(ws)
    scan_path = ctx(ws, "scan.json")
    errors = []
    if ns.scan:
        scan = read_json(ns.scan)
        if scan is None:
            raise UsageError("读不到 --scan %s" % ns.scan)
        write_json(scan_path, scan)
    else:
        cmd = [PY, os.path.join(HERE, "product_scan.py"), "--out", scan_path, "--max-pages", str(ns.max_pages)]
        if ns.site:
            cmd += ["--site", ns.site]
        if ns.repo:
            cmd += ["--repo", ns.repo]
        if ns.allow_local:
            cmd.append("--allow-local")
        if ns.no_wayback:
            cmd.append("--no-wayback")
        rc, scan, err = run_json(cmd, scan_path)
        if scan is None:
            raise UsageError("product_scan.py 没产出结果(退出码 %s):%s" % (rc, err))
    errors += scan.get("errors") or []
    prof = {"schema": SCHEMA, "version": 0, "created": now(), "updated": None,
            "site": ns.site, "repo": lifecycle.repo_for_profile(ws, ns.repo), "market": ns.market,
            "rings": {str(r): {"status": "pending", "answers": {}, "quotes": [], "asked_at": None,
                               "confirmed_at": None} for r in range(1, 7)},
            "facts": merge_pm_facts(facts_from_scan(scan), ns.repo or os.path.dirname(ws)),
            "stage": {}, "events": [], "metrics": {}, "deny": [],
            "existing_context": scan.get("existing_context") or [], "changelog": []}
    save_profile(ws, prof, "开局:从 product_scan 起草 %d 条事实(全部未确认)" % len(prof["facts"]))
    gsc = lifecycle.gsc_export_metrics(ws, prof)
    if gsc:                                        # data/ 里已经有 GSC 导出:当场读进指标,阶段按真实数据判
        prof["metrics"].update(gsc["metrics"])
        prof.setdefault("metric_sources", {}).update({k: gsc["source"] for k in gsc["metrics"]})
        save_profile(ws, prof, "记指标 %s(来源 %s)" % (",".join(gsc["metrics"]), gsc["source"]))
        import loops as _loops
        _loops.append_metrics(ws, gsc["metrics"], gsc["source"], gsc["at"])
    diag = lifecycle.diagnose(scan, ws)
    write_json(ctx(ws, "diagnosis.json"), diag)
    prof = load_profile(ws)
    prof["stage"] = {"value": diag["stage"]["stage"], "rule_value": diag["stage"]["stage"],
                     "confidence": diag["stage"]["confidence"], "confirmed": False}
    save_profile(ws, prof, "阶段初判:%s(%s)" % (diag["stage"]["name"], diag["stage"]["confidence"]))
    ws_banner(ws, ns.json)
    if not ns.json:
        print_fetched(scan)
    if errors:
        print("读取时有 %d 个错误(已记进 scan.json):%s" % (len(errors), ";".join(map(str, errors[:3]))),
              file=sys.stderr if ns.json else sys.stdout)
    return cmd_show(argparse.Namespace(ws=ws, ring=1, json=ns.json))


def remember_allow_local(ws):
    """本机预览站开局时带了 --allow-local:记进 project.yaml(allow_local: true),之后的运营单、循环不用再带。"""
    path = os.path.join(ws, "project.yaml")
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        text = ""
    if re.search(r"(?m)^allow_local:", text):
        text = re.sub(r"(?m)^allow_local:.*$", "allow_local: true", text)
    else:
        text = text + ("" if not text or text.endswith("\n") else "\n") + "allow_local: true\n"
    os.makedirs(ws, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def is_loopback(host):
    """127.0.0.0/8、::1、localhost(--allow-local 放行的就是这些)。"""
    h = (host or "").strip("[]").lower().rstrip(".")
    if h == "localhost" or h.endswith(".localhost"):
        return True
    try:
        return ipaddress.ip_address(h).is_loopback
    except ValueError:
        return False


def ring1_touched(prof):
    """档案里有没有用户给过的东西(任何一环的回答、原话,或 agent 记过的 note):有就不能悄悄重开。"""
    for r in (prof.get("rings") or {}).values():
        if isinstance(r, dict) and (r.get("answers") or r.get("quotes") or r.get("status") in ("confirmed", "skipped")):
            return True
    return any(isinstance(f, dict) and (f.get("by") == "agent" or f.get("status") not in (None, "unconfirmed"))
               for f in prof.get("facts") or []) or bool(prof.get("events") or prof.get("metrics"))


def print_fetched(scan):
    """把 product_scan 实际请求过的 URL 一行一个列出来(robots.txt、sitemap、llms.txt、抽样页都在里面)。"""
    log = ((scan or {}).get("site_scan") or {}).get("fetched") or []
    if log:
        print("读站点时请求过的 URL(%d 个):" % len(log))
        for x in log:
            print("- %s %s" % (x.get("status") or "失败", x["url"]))
        print("")


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------

def missing_core(prof):
    """评测和下游都要读的 7 个事实键里,扫描没读到值的(conversion.primary、customers 由第 1 环的回答填)。"""
    out = []
    for key in lifecycle.PROFILE_FACT_KEYS:
        if key in ("conversion.primary", "customers"):
            continue
        if not any(f.get("key") == key and known_value(f.get("value")) for f in prof.get("facts") or []):
            out.append(key)
    return out


def site_type_of(prof):
    return str(fact_value(prof, "site.type") or "")


def question_applies(q, prof):
    cond = q.get("when")
    if cond and cond.startswith("site_type in "):
        allowed = cond[len("site_type in "):].split(",")
        st = site_type_of(prof).lower()
        if st and not any(a.strip() in st for a in allowed):
            return False
    return not covered_fact(q, prof)


def covered_fact(q, prof):
    """这一问已经由已有上下文文件(.agents/product-marketing.md)给出 → 那条事实;否则 None。"""
    for key in q.get("covered_by") or []:
        f = next((x for x in prof.get("facts") or [] if x.get("key") == key and has_value(x.get("value"))), None)
        if f:
            return f
    return None


def has_value(v):
    if v is None:
        return False
    if isinstance(v, (list, tuple, dict)):
        return bool(v)
    return bool(str(v).strip())


def known_value(v):
    """有值、而且不是扫描器的内部占位值 unknown。"""
    return has_value(v) and not (isinstance(v, str) and v.strip().lower() == "unknown")


def lines_state(prof):
    """产品线草稿:"missing"(没有或未知)/ "inferred"(按网址推的)/ "known"。"""
    f = next((x for x in prof.get("facts") or [] if x.get("key") == "product.lines"), None)
    if not f or not has_value(f.get("value")) or f.get("status") == "unknown" or f.get("kind") == "unknown":
        return "missing"
    if f.get("kind") == "inferred" and f.get("status") == "unconfirmed":
        return "inferred"
    return "known"


def question_required(q, prof):
    if q.get("required"):
        return True
    key = q.get("required_if_missing")
    return bool(key == "product.lines" and lines_state(prof) == "missing")


def question_text(q, prof):
    if q.get("id") == "main_line":
        st = lines_state(prof)
        if st == "missing" and q.get("text_missing"):
            return q["text_missing"]
        if st == "inferred" and q.get("text_inferred"):
            f = next((x for x in prof.get("facts") or [] if x.get("key") == "product.lines"), {})
            if f.get("by") == "agent":              # agent 从材料里记的:写实际出处,不说「按网址推的」
                return "产品线是我从 %s 读的(见上面草稿),对吗?最想先做哪条?" % (f.get("source") or "材料")
            return q["text_inferred"]
    text = q["text"]
    if q.get("id") == "profile_ok":
        for f, c in conflict_facts(prof):
            text += " " + conflict_question(f, c)
        if not known_value(fact_value(prof, "pricing.model")):
            text += " 没读到收费方式:你们靠什么收钱(订阅、一次性购买、广告或联盟佣金……)?"
    return text


def guess_for(q, prof):
    ans = None
    for r in prof["rings"].values():
        if q["id"] in (r.get("answers") or {}):
            ans = r["answers"][q["id"]]
    if ans is not None:
        return ans, "已答"
    src = q.get("options_from")
    if src:
        v = fact_value(prof, src)
        if isinstance(v, list) and v:
            return fmt_val(v[:1]), "草稿里 %s 的第一项" % FACT_LABELS.get(src, src)
        if v:
            return fmt_val(v), "来自草稿 %s" % FACT_LABELS.get(src, src)
    return None, None


def ring_view(prof, r):
    d = bank()[r]
    qs, merged = [], []
    for q in d["questions"]:
        if not question_applies(q, prof):
            continue
        g, gsrc = guess_for(q, prof)
        opts = list(q.get("options") or [])
        src = q.get("options_from")
        if src:
            v = fact_value(prof, src)
            if isinstance(v, list):
                opts = [fmt_val([x]) for x in v[:4]] + [o for o in opts if o not in v][:2]
        item = {"id": q["id"], "text": question_text(q, prof), "options": opts[:5], "guess": g, "guess_from": gsrc,
                "required": question_required(q, prof), "sensitive": bool(q.get("sensitive")),
                "deny": bool(q.get("deny")), "ids": [q["id"]]}
        (merged if q.get("merge_into") else qs).append((q.get("merge_into"), item))
    qs = [x for _, x in qs]
    for host_id, m in merged:                      # 并进同一行问(第 1 环最多 3 问)
        host = next((x for x in qs if x["id"] == host_id), None)
        if host is None:
            qs.append(m)
            continue
        host["text"] = "%s %s" % (host["text"], m["text"])
        host["ids"].append(m["id"])
        host["required"] = host["required"] or m["required"]
        host.setdefault("merged", []).append(m)
    covered = [{"id": q["id"], "fact": covered_fact(q, prof)} for q in d["questions"] if covered_fact(q, prof)]
    facts = ring_facts(prof, d)
    return {"ring": r, "title": d["title"], "goal": d["goal"], "must_confirm": d.get("must_confirm"),
            "status": prof["rings"][str(r)]["status"], "agent_steps": d["agent_steps"],
            "facts": facts, "questions": qs, "covered": covered}


FACT_LABELS = {"product.name": "产品名", "product.one_liner": "一句话介绍", "product.lines": "产品线",
               "pricing.model": "收费方式(页面原文)", "pricing.prices": "页面上的价格", "conversion.ctas": "页面上的转化入口",
               "conversion.buttons": "按钮原文", "conversion.primary": "主转化", "conversion.pm_action": "转化动作",
               "context.pm_customers": "主要客户", "context.existing": "已有产品上下文文件", "customers": "主要客户",
               "market.languages": "语言", "site.page_types": "页面类型", "site.url_count": "网址数",
               "tech.framework": "框架", "tech.rendering": "渲染方式", "measurement.analytics": "统计工具",
               "entity.same_as": "官方账号", "history.first_seen": "最早出现"}
STATUS_ZH = {"unconfirmed": "未确认", "confirmed": "已确认", "corrected": "你改过", "unknown": "未知,待你说"}


PRICE_AMOUNT_RE = re.compile(r"(?:[$€£¥₹]\s?\d[\d.,]*|\d[\d.,]*\s?(?:[$€£¥₹]|usd|eur|gbp|cny|rmb|元))", re.I)


def _amounts(text):
    """文字里的金额 → {(币种符号, 数值)};「$20/month」「20 USD」都认。"""
    out = set()
    for m in PRICE_AMOUNT_RE.finditer(str(text or "")):
        s = m.group(0).lower()
        cur = re.sub(r"[\d.,\s]", "", s) or "?"
        num = re.search(r"\d[\d.,]*", s).group(0).rstrip(".,")
        num = num.replace(",", "") if re.search(r",\d{3}(?!\d)", num) else num.replace(",", ".")
        try:
            out.add((cur, float(num)))
        except ValueError:
            pass
    return out


def _clauses(text):
    return [c.strip() for c in re.split(r"[;；|]|\s/\s|,\s+|(?<=[.!?。])\s+", str(text or "")) if c.strip()]


def fact_conflict(f):
    """已有上下文文件的值和站点读到的值对不上 → {site_clause, file_clause, site_only};否则 None。
    对不上 = 站点上写着、文件里没有的金额(站点只写了一部分价格不算);措辞不同、没有金额的不算。
    用户已经纠正或确认过的不再算。"""
    if f.get("status") != "unconfirmed" or not known_value(f.get("site_value")):
        return None
    site, mine = fmt_val(f["site_value"]), fmt_val(f.get("value"))
    sa, fa = _amounts(site), _amounts(mine)
    only = sa - fa
    if not sa or not fa or not only:
        return None
    sc = next((c for c in _clauses(site) if _amounts(c) & only), site)
    fcs = [c for c in _clauses(mine) if _amounts(c)] or [mine]
    st = _tokens(re.sub(PRICE_AMOUNT_RE, " ", sc))
    fc = max(fcs, key=lambda c: (len(st & _tokens(re.sub(PRICE_AMOUNT_RE, " ", c))), -fcs.index(c)))
    return {"site_clause": sc[:160], "file_clause": fc[:160], "site_source": f.get("site_source") or "站点",
            "file_source": f.get("source") or "已有上下文文件",
            "site_only": [m.group(0) for m in PRICE_AMOUNT_RE.finditer(sc) if _amounts(m.group(0)) & only]}


def conflict_facts(prof, keys=None):
    out = []
    for f in prof.get("facts") or []:
        c = fact_conflict(f)
        if c and (keys is None or f.get("key") in keys):
            out.append((f, c))
    return out


def conflict_question(f, c):
    label = FACT_LABELS.get(f["key"], f["key"]).split("(")[0]
    return "%s对不上:%s 写「%s」,%s 写「%s」,哪个对?" % (label, c["file_source"], c["file_clause"],
                                                    c["site_source"], c["site_clause"])


def fact_line(f):
    label = FACT_LABELS.get(f["key"], f["key"])
    c = fact_conflict(f)
    if c:
        return "- %s:对不上(站点写了 %s,文件里没有;在第 1 问里请你定)\n  文件写:%s ← %s\n  站点写:%s ← %s" % (
            label, "、".join(c["site_only"]), fmt_val(f.get("value"))[:320], c["file_source"],
            fmt_val(f.get("site_value"))[:320], c["site_source"])
    st = STATUS_ZH.get(f.get("status"), f.get("status") or "未确认")
    if f.get("status") == "unconfirmed" and f.get("kind") == "inferred":
        st += ",推测"
    if not known_value(f.get("value")):
        ask = f["key"] in ("product.lines", "pricing.model")
        return "- %s:%s%s ← %s(%s)" % (label, "没读到" if f["key"] == "pricing.model" else "未知",
                                      ("(%s)" % f["note"]) if f.get("note") else "",
                                      f.get("source") or "没读到可靠出处", "第 1 环请你说" if ask else st)
    extra = ""
    if f.get("billing"):
        extra = ";页面写到的计费方式:%s" % "、".join(f["billing"])
    return "- %s:%s ← %s(%s%s)" % (label, fmt_val(f.get("value"))[:320], f.get("source") or "没有出处,推测", st, extra)


def recap_lines(prof, r):
    """前面已确认的内容(第 1 环的产品事实 + 各环答案);纠正过的显示新值。"""
    b = bank()
    L = []
    r1 = prof["rings"]["1"]
    if r1["status"] in ("confirmed", "asking") and r1.get("confirmed_at"):
        names = {s["id"]: s["name"] for s in lifecycle.load_rules()["stages"]}
        stv = (prof.get("stage") or {}).get("value")
        if stv is not None:
            L.append("- 产品阶段:%s ← 第 1 环你确认的" % names.get(stv, stv))
        for key in ("product.name", "product.one_liner", "product.lines", "pricing.model"):
            f = best_fact(prof, key)
            if f and has_value(f.get("value")):
                L.append("- %s:%s ← %s" % (FACT_LABELS[key], fmt_val(f["value"])[:240], recap_src(f, 1)))
    for i in range(1, r):
        ring = prof["rings"][str(i)]
        if ring["status"] == "skipped":
            L.append("- 第 %d 环 %s:跳过了,用的是猜测(未确认) ← 第 %d 环你说的" % (i, b[i]["title"], i))
            continue
        if ring["status"] != "confirmed" and not ring.get("answers"):
            continue
        qtext = {q["id"]: q["text"] for q in b[i]["questions"]}
        for k, v in (ring.get("answers") or {}).items():
            if k == "profile_ok":
                continue
            label = ANSWER_LABELS.get(k) or qtext.get(k, k).split("?")[0][:24]
            corrected = any(f.get("key") == ANSWER_FACTS.get(k) and f.get("status") == "corrected" for f in prof["facts"])
            L.append("- %s:%s ← 第 %d 环你%s" % (label, fmt_val(v)[:200], i, "纠正过" if corrected else "答的"))
    skipped = audit_skipped(prof)
    if skipped and r > 4:
        L.append("- 体检没跑:%s ← 第 4 环记的(未确认)" % skipped)
    return L


def audit_skipped(prof):
    """第 4 环走了 --no-audit → 原因;否则 None。"""
    a = prof.get("audit") or {}
    return a.get("reason") if a.get("ran") is False else None


ANSWER_LABELS = {"conversion": "SEO 要带来的结果", "customers": "主要客户", "main_line": "最先做的产品线",
                 "market_first": "先做的市场", "deny_topics": "明确不做", "kpi_target": "业务目标"}


def best_fact(prof, key):
    best = None
    for f in prof.get("facts") or []:
        if f.get("key") == key and (best is None or f.get("status") in ("confirmed", "corrected")):
            best = f
    return best


def recap_src(f, ring):
    if f.get("status") == "corrected":
        return "你纠正过(原话:「%s」)" % str(f.get("quote") or "")[:60]
    if f.get("status") == "confirmed":
        return "第 %d 环你确认的(出处 %s)" % (ring, f.get("source") or "—")
    return "%s(还没确认)" % (f.get("source") or "推测")


def stage_line(ws):
    diag = read_json(ctx(ws, "diagnosis.json"), {}) or {}
    st = diag.get("stage") or {}
    if not st:
        return None
    tag = {"guess": "猜测,待确认", "unknown": "证据不够,待确认", "rule": "按规则推测,待确认",
           "confirmed": "已确认"}.get(st.get("confidence"), "待确认")
    line = "- 产品阶段:%s(%s)← 依据:%s" % (st.get("name") or "未知", tag, ";".join(st.get("why") or []) or "—")
    if st.get("candidates"):
        line += ";候选:" + "、".join(lifecycle.candidate_names(st["candidates"])) + "(在第 1 个问题里一起确认)"
    return line


def render_question(i, q):
    line = "%d. %s%s" % (i, q["text"], "(必答)" if q["required"] else "")
    opts = q["options"] or ([] if (q["guess"] or q.get("merged")) else ["我直接写", "不知道(先记未确认)"])
    if opts:
        line += "　" + "　".join("%s. %s" % (chr(65 + j), o) for j, o in enumerate(opts[:26]))
    guesses = []
    if q["guess"]:
        guesses.append("%s(%s)" % (q["guess"], q["guess_from"]))
    for m in q.get("merged") or []:
        if m["guess"]:
            guesses.append("最想先做 %s(%s)" % (m["guess"], m["guess_from"]))
    if guesses:                                    # 猜测和选项都留在问题这一行:贴的时候选项被挪到下一行,猜测也还在
        head, sep, tail = line.partition("　")
        line = head + "　我猜:" + ";".join(guesses) + (sep + tail if sep else "")
    if q["sensitive"]:
        line += "\n   (答案只存本地 context/private/,不进 git)"
    return line


# ---------------------------------------------------------------------------
# 第 4 环的体检门:站点已上线,确认前工作区里要有一次成功的体检(改版阶段另要改动前基线)
# ---------------------------------------------------------------------------

_host_key = lifecycle.host_key
same_site = lifecycle.same_site


def stage_value(prof):
    return (prof.get("stage") or {}).get("value")


def audit_needed(prof, ws):
    """站点已上线(阶段 2–5;阶段没定时看 start 读没读到页面)→ 第 4 环确认前要体检。想法、上线前(0、1)不要。"""
    st = stage_value(prof)
    if st in (0, 1):
        return False
    if st in (2, 3, 4, 5):
        return True
    sig = (read_json(ctx(ws, "scan.json"), {}) or {}).get("signals") or {}
    return bool(prof.get("site") and sig.get("site_live"))


def triage_record(ws, site):
    """最近一次成功的体检(project.py run triage 写的 history/<时间>/triage.json,爬取和审计两步都成功、
    站点和档案一致)→ 相对工作区的目录;没有 → None。"""
    root = os.path.join(ws, "history")
    if not os.path.isdir(root):
        return None
    for d in sorted(os.listdir(root), reverse=True):
        tri = read_json(os.path.join(root, d, "triage.json"))
        if not isinstance(tri, dict):
            continue
        ok = {s.get("name"): bool(s.get("ok")) for s in tri.get("steps") or [] if isinstance(s, dict)}
        if ok.get("crawl") and ok.get("audit") and (not site or same_site(tri.get("site"), site)):
            return os.path.join("history", d)
    return None


def baseline_record(ws, site):
    """改动前基线(site_move.py baseline 写的 baselines/*.json:schema 1、站点和档案一致、至少一个 200 页面)→ 相对路径。"""
    root = os.path.join(ws, "baselines")
    if not os.path.isdir(root):
        return None
    for fn in sorted(os.listdir(root), reverse=True):
        b = read_json(os.path.join(root, fn)) if fn.endswith(".json") else None
        if not isinstance(b, dict) or not isinstance(b.get("pages"), dict):
            continue
        if any(isinstance(r, dict) and r.get("status") == 200 for r in b["pages"].values()) \
                and (not site or same_site(b.get("site"), site)):
            return os.path.join("baselines", fn)
    return None


def audit_cmds(prof, ws):
    """体检(和改版阶段的基线)要跑的完整命令:脚本绝对路径、实际工作区;本机站点自动带 --allow-local。"""
    site = prof.get("site")
    loc = " --allow-local" if site and is_loopback(_host_key(site)[0]) else ""
    q = shlex.quote(ws)
    out = []
    if not os.path.isfile(os.path.join(ws, "project.yaml")):
        out.append("python3 %s init --site %s --dir %s" % (os.path.join(HERE, "project.py"),
                                                          shlex.quote(site) if site else "<线上站点地址>", q))
    out.append("python3 %s run triage --dir %s%s" % (os.path.join(HERE, "project.py"), q, loc))
    base = None
    if stage_value(prof) == 5:
        base = "python3 %s baseline --site %s --ws %s%s" % (os.path.join(HERE, "site_move.py"),
                                                            shlex.quote(site) if site else "<改版前的站点地址>", q, loc)
    return out, base


def audit_steps(prof, ws):
    """第 4 环「agent 先做」里的体检那几行:照抄的命令、现在有没有记录、跑不了时的逃生口。"""
    if not audit_needed(prof, ws):
        return ["- 这个阶段还没有线上站:不跑体检,改成看技术选型(上面那条);第 4 环确认不查体检记录"]
    site = prof.get("site")
    tri, base_cmd = audit_cmds(prof, ws)
    L = ["- 体检(站点已上线,确认这一环之前必须跑过,脚本会查):" + " && ".join(tri)]
    rec = triage_record(ws, site)
    L.append("  现在:" + ("已有体检记录 %s" % rec if rec else "还没有成功的体检记录"))
    if base_cmd:
        L.append("- 改版前存基线(改版阶段确认这一环之前必须有):" + base_cmd)
        b = baseline_record(ws, site)
        L.append("  现在:" + ("已有基线 %s" % b if b else "还没有基线"))
    L.append("- 站点打不开、没权限这类真跑不了的情况才用逃生口:answer 加 --no-audit \"<原因>\"(原因记进档案、标未确认,"
             "之后的屏幕和方案里都写「体检没跑:原因」)")
    return L


PLAN_ITEMS_SHOWN = 10


def plan_file(ws):
    return os.path.join(ws, "plan", "plan.json")


def plan_cmd(ws):
    return "python3 %s build --ws %s" % (os.path.join(HERE, "plan.py"), shlex.quote(ws))


def ensure_plan(ws):
    """第 6 环发给用户之前方案必须已经生成:没有就在这里跑 plan.py build(不交给 agent 记着跑)。
    已有的方案不重出(用户可能改过、定过稿)。返回 (方案, 这次是不是新出的, 出错信息)。"""
    plan = read_json(plan_file(ws))
    if plan:
        return plan, False, None
    r = subprocess.run([sys.executable, os.path.join(HERE, "plan.py"), "build", "--ws", ws],
                       capture_output=True, text=True)
    plan = read_json(plan_file(ws)) if r.returncode == 0 else None
    if not plan:
        return None, False, (r.stderr or r.stdout or "").strip()[-600:]
    return plan, True, None


def plan_lines(ws):
    """第 6 环那一块里的方案摘要:策略、路线前几条、不做什么。用户确认的是这几行,不是一个文件路径。"""
    plan = read_json(plan_file(ws))
    if not plan:
        return []
    L = ["方案草稿(全文在 seo-ops/plan/;每行后面是出处):"]
    names = [x.get("name") for x in plan.get("strategies") or [] if x.get("name")]
    if names:
        L.append("- 策略:%s ← plan/plan.md" % "、".join(names))
    items = plan.get("items") or []
    for it in items[:PLAN_ITEMS_SHOWN]:
        w = it.get("weeks") or []
        wk = ("第 %s 周" % w[0] if w[0] == w[-1] else "第 %s–%s 周" % (w[0], w[-1])) if w else "周数未排"
        L.append("- 路线 %s:%s(%s;看 %s) ← plan/roadmap.md" % (it.get("rank"), it.get("title"), wk,
                                                           it.get("metric") or "未定"))
    if len(items) > PLAN_ITEMS_SHOWN:
        L.append("- 另有 %d 条 ← plan/roadmap.md" % (len(items) - PLAN_ITEMS_SHOWN))
    for r in plan.get("user_rules") or []:
        L.append("- 按你的规则 %s:「%s」 ← playbook/rules.md" % (r.get("id"), r.get("quote")))
    deny = [d if isinstance(d, str) else d.get("item") for d in plan.get("deny") or []]
    if deny:
        L.append("- 不做:%s ← 你说过不做的" % ";".join(str(d) for d in deny if d))
    return L + [""]


def render_block(prof, view, ws):
    """「原样发给用户」那一整块(含首尾两行等号);show、note、metric 打印的是同一块。"""
    r = view["ring"]
    L = [BLOCK_START + "(到下面那行等号为止;不改写、不删「← 出处」和选项、不合并问题)=====",
         "**开局第 %d 环 · %s**%s" % (r, view["title"], "(这一环要你确认完才往下)" if view["must_confirm"] else ""), ""]
    rec = recap_lines(prof, r) if r > 1 else []
    if rec:
        L += ["前面已确认的(档案第 %s 版;不对直接说):" % prof.get("version")] + rec + [""]
    if r == 6:
        L += plan_lines(ws)
    facts = list(view["facts"])
    sl = stage_line(ws) if r == 1 else None
    if sl or facts:
        L.append("我读到的草稿(每条带出处,都还没确认):")
        if sl:
            L.append(sl)
        L += [fact_line(f) for f in facts]
        L.append("")
    for c in view.get("covered") or []:
        L.append("(「%s」已经写在 %s 里:%s;没问题就在第 1 问一起确认,不再单独问)"
                 % (ANSWER_LABELS.get(c["id"], c["id"]), c["fact"].get("source"), fmt_val(c["fact"]["value"])[:160]))
    if view.get("covered"):
        L.append("")
    L.append("## 问用户(这一环 %d 个问题;每个带我的猜测或 A/B 选项)" % len(view["questions"]))
    for i, q in enumerate(view["questions"], 1):
        L.append(render_question(i, q))
    L.append(BLOCK_END + " =====")
    return L


def render_ring(prof, view, ws):
    r = view["ring"]
    L = ["# 开局第 %d 环 · %s%s" % (r, view["title"], "(这一环必须确认完才往下)" if view["must_confirm"] else ""), "",
         "目标:" + view["goal"], "", "## agent 先做(做完再问)"]
    L += ["- " + s for s in view["agent_steps"]]
    if r == 1 and prof.get("existing_context"):
        L.append("- 已有产品上下文文件(先读它当草稿):" + "、".join(c.get("path", "") for c in prof["existing_context"]))
    msrc = prof.get("metric_sources") or {}
    if r == 1 and msrc.get("gsc_clicks_28d"):
        m = prof.get("metrics") or {}
        L.append("- GSC 指标已经读进档案(不用再跑 metric):近 28 天点击 %s%s、展示 %s ← %s" % (
            m.get("gsc_clicks_28d"), (",上一期 %s" % m["gsc_clicks_prev_28d"]) if "gsc_clicks_prev_28d" in m else "",
            m.get("gsc_impressions_28d", "—"), msrc["gsc_clicks_28d"]))
    if r == 1 and conflict_facts(prof):
        L.append("- 已有上下文文件和站点对不上的 %d 处,脚本已经在草稿里两边都列出来、并写进第 1 问:%s;"
                 "用户定了哪个就用 --correct <键>=<对的值> 记" % (
                     len(conflict_facts(prof)), "、".join(FACT_LABELS.get(f["key"], f["key"]).split("(")[0]
                                                         for f, _ in conflict_facts(prof))))
    if r == 1:
        miss = missing_core(prof)
        if miss:
            L.append("- 档案还缺:%s(产品说明、brief、README 这类材料里读得到就先记下再贴:%s;列表项用「%s」隔开;"
                     "读不到就留着,第 1 问里请用户说)"
                     % ("、".join(miss), ob_cmd(ws, "note --ring 1 --key <键> --value <值> --source <文件>"), LIST_SEP))
        if lines_state(prof) == "missing":
            L.append("- 产品线是未知的:用户回话里说了几条就用 --correct product.lines=<A%sB%sC> 记;只说了最重要的一条,"
                     "从站点导航 / sitemap 里挑出产品类目一起写进去,下一环开头复述给用户" % (LIST_SEP, LIST_SEP))
    if r == 4:
        L += audit_steps(prof, ws)
    facts = list(view["facts"])
    L += [""] + render_block(prof, view, ws)
    L += ["", "## 停",
          "把上面那一块原样发给用户(连同编号、选项、「← 出处」),现在停下等用户回答;不要先给建议、不要替用户答、"
          "不要改写成自己的话。只剩 1 个问题也照样编号。",
          "排版也照原样:每个问题一行「数字. 问题?　我猜:…　A. …　B. …」,选项和「我猜」不要挪到下一行"
          "(另起一行的「A.」会被当成下一个问题,这一问就成了没带选项),不加粗、不加前缀。",
          "- Claude Code:可以改用提问工具(AskUserQuestion),但每问的选项和你的猜测都要带上,猜测放第一个选项。",
          "- 没有提问工具的宿主:贴完那一块就结束这一回合。",
          "问题编号对应的 id(记答案用):" + ";".join("%d → %s" % (i, "+".join("[id=%s]" % x for x in q["ids"]))
                                             for i, q in enumerate(view["questions"], 1)),
          "纠正草稿时用的键:" + "、".join("%s=%s" % (FACT_LABELS.get(f["key"], f["key"]), f["key"]) for f in facts[:12]),
          "用户回了以后:" + ob_cmd(ws, "answer --ring %d --set <id>=<答案> ... --quote \"<用户这次回话的原文>\" --confirm" % r),
          "用户纠正草稿:加 --correct <键>=<改后的值>(列表只改其中一项:写那一项的新值,或 <键>[N]=<新值>;"
          "整份换就写全部项,列表项用「%s」隔开);" % LIST_SEP +
          "用户只是说哪条产品线最重要:用 --set main_line=<那条>,不要改 product.lines;用户说不知道:加 --unknown <id>。",
          "用户只答了一部分:答到的题用 --set 记,答到的题里没说到的细节写「未说」,不另编追问;没答到的题,"
          "不带 --confirm 跑一次 answer,脚本会把没答的题原样打出来再问。",
          "用户说「按你的判断来 / 按你的猜测来 / best guess / carry on / 好」:意思是按草稿确认这一环——"
          "answer --ring %d --set <id>=<上面我猜的值> --quote \"<原话>\" --confirm,再 show 下一环;这不是跳过。" % r]
    if r > 1:
        L.append("用户明确说要跳过(「跳过」「skip」「不用问了」「直接出方案」):%s"
                 "(剩下的环用猜测补齐、写明未确认)" % ob_cmd(ws, "skip --quote \"<用户原话>\""))
    else:
        L.append("用户说「别问了」也要先把这一环答完:第 1 环最多这 %d 问,说明原因再问一次。" % len(view["questions"]))
    return "\n".join(L)


def cmd_show(ns):
    ws = ws_dir(ns)
    prof = load_profile(ws)
    r = ns.ring or current_ring(prof)
    if r is None:
        print("开局 6 环都已完成(确认或跳过)。下一步:按第 6 环的路线做;每周跑 project.py ops weekly。")
        return 0
    if not 1 <= r <= 6:
        raise UsageError("--ring 只能是 1–6")
    if r > 1 and prof["rings"]["1"]["status"] != "confirmed":
        raise GateError("第 1 环还没确认,不能先问第 %d 环" % r)
    view = ring_view(prof, r)
    ring = prof["rings"][str(r)]
    if r == 6 and not ns.json and current_ring(prof) == 6:      # 前 5 环都完了才出方案;提前看第 6 环不出
        plan, built, err = ensure_plan(ws)
        if not plan:
            raise UsageError("第 6 环要先有方案,方案没生成出来,这一环还没发给用户,不要先问。先把下面的错处理掉,跑:\n  %s\n"
                             "再重跑:\n  %s\n%s" % (plan_cmd(ws), ob_cmd(ws, "show --ring 6"), err or ""))
        print("%s:%s(plan.json、plan.md、roadmap.md、中英战略书)。摘要已经在下面那块里;档案改了要重出,跑:%s"
              % ("方案刚生成" if built else "方案已有(%s 生成,状态 %s)" % (plan.get("generated_at"), plan.get("status")),
                 os.path.join(ws, "plan"), plan_cmd(ws)))
    if ring["status"] == "pending" or (ring["status"] == "asking" and not ring.get("asked_at")):
        # 退回待确认的环(档案被手改)asked_at 是空的:重新发给用户时同样记一次,否则这一环永远确认不了
        ring["status"] = "asking"
        ring["asked_at"] = now()
        save_profile(ws, prof, "第 %d 环发给用户" % r)
    if ns.json:
        print(json.dumps(view, ensure_ascii=False, indent=1))
    else:
        print(render_ring(prof, view, ws))
    return 0


# ---------------------------------------------------------------------------
# note / answer / skip / event
# ---------------------------------------------------------------------------

def parse_kv(items, what):
    out = {}
    for it in items or []:
        if "=" not in it:
            raise UsageError("%s 要写成 key=value:%r" % (what, it))
        k, v = it.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def cmd_note(ns):
    ws = ws_dir(ns)
    prof = load_profile(ws)
    if not ns.source:
        raise UsageError("note 必须带 --source(脚本输出、URL 或文件路径)")
    prof["facts"] = [f for f in prof["facts"] if not (f["key"] == ns.key and f.get("status") == "unconfirmed")]
    prof["facts"].append({"key": ns.key, "value": fact_shape(ns.key, ns.value), "source": ns.source, "kind": "inferred",
                          "status": "unconfirmed", "ring": ns.ring, "at": now(), "by": "agent"})
    save_profile(ws, prof, "agent 记:%s(第 %s 环,未确认)" % (ns.key, ns.ring))
    v = fact_value(prof, ns.key)
    print("记下 %s(未确认)%s" % (ns.key, (":%d 项 %s" % (len(v), " | ".join(map(str, v)))) if isinstance(v, list) else ""))
    if ns.ring == current_ring(prof):
        reprint_block(ws)
    return 0


def reprint_block(ws):
    """当前环发给用户以后、确认以前,草稿变了(note、metric):把更新后的整块再打一遍,旧的那块作废。"""
    prof = load_profile(ws)
    r = current_ring(prof)
    if r is None:
        return
    ring = prof["rings"][str(r)]
    if not ring.get("asked_at") or (r > 1 and prof["rings"]["1"]["status"] != "confirmed"):
        return
    print("草稿变了:上一版作废,贴这一版(两行等号之间整块原样发给用户,标题行也要):")
    print("\n".join(render_block(prof, ring_view(prof, r), ws)))


# --quote 的长度:中文一个字按 1.5 算,合计不到 6 就太短(中文少于 4 个字、英文少于 6 个字符)。
# 太短的只收确认词(对 / 是的 / 好 / 可以 / yes / ok …),而且这次调用不能带 --correct / --unknown:
# 用户只回了一个「对」,纠正的内容就不可能是他的原话。
CONFIRM_WORDS = {"对", "对的", "是", "是的", "好", "好的", "行", "可以", "嗯", "没问题", "都对", "确认", "同意", "没错",
                 "yes", "y", "yep", "yeah", "ok", "okay", "sure", "correct", "right", "approved", "confirmed",
                 "agreed", "lgtm", "si", "sí", "vale", "claro", "correcto"}


def quote_weight(q):
    s = re.sub(r"\s+", "", q)
    cjk = len(re.findall(r"[㐀-鿿豈-﫿]", s))
    return cjk * 1.5 + (len(s) - cjk)


def check_quote(q, corrections):
    s = (q or "").strip()
    if not s:
        raise GateError("必须用 --quote 带上用户原话(用户没回话就不能记答案)")
    if quote_weight(s) >= 6:
        return
    core = re.sub(r"[\W_]+", "", s.lower())
    if core in CONFIRM_WORDS and not s.endswith(("?", "？")):
        if corrections:
            raise GateError("--quote %r 只是一句确认,不能拿来记纠正(--correct / --unknown);带上用户说出纠正内容的那句原话" % s)
        return
    raise GateError("--quote %r 太短(中文至少 4 个字、英文至少 6 个字符;只回「对 / Yes」这类确认词的,"
                    "只能用来确认草稿,不能带 --correct)。传用户这次回话的原文,不要缩写" % s)


# skip 只认明确要跳过的话;「按你的判断来 / best guess / carry on / 好」是按草稿继续,不是跳过
SKIP_RE = re.compile(r"跳过|略过|不用问了|别问了|不要再问|别再问|不用再问|不想回答|直接(出|给)(方案|计划|路线)|直接出|"
                     r"\bskip\b|\bskip(ping)? the rest\b|stop asking|no more questions|don'?t ask (me )?(any )?more|"
                     r"just give me the plan|straight to the plan|saltar|omitir|no (me )?preguntes m[aá]s", re.I)
NOT_SKIP_RE = re.compile(r"不要跳过|别跳过|不跳过|don'?t skip|do not skip|no skip|no saltes", re.I)
SKIP_HINT = ("这句话的意思是按草稿继续下一环:用 answer 确认当前环(--set <id>=<你猜的值> --quote \"<原话>\" --confirm),"
             "再 show 下一环。只有用户明确说要跳过(「跳过」「skip」「不用问了」「直接出方案」)才用 skip")


def is_skip_request(q):
    return bool(SKIP_RE.search(q or "")) and not NOT_SKIP_RE.search(q or "")


IMPORTANT_RE = re.compile(r"最重要|最想先做|最主要|主推|重点是|先做|most important|main (one|line|focus|product)|"
                          r"\bprimary\b|focus on|priority|the key part|más importante|principal", re.I)


def _tokens(s):
    s = str(s).lower()
    words = set(re.findall(r"[a-z0-9]+", s))
    cjk = re.findall(r"[㐀-鿿]", s)
    return words | {a + b for a, b in zip(cjk, cjk[1:])}


def corrected_list(key, cur, raw, quote, replace_all=False):
    """列表字段的纠正:写全部项 → 整份换;只写一项 → 只换最像的那一项(或 key[N] 指定第几项)。"""
    m = re.match(r"^(.*)\[(\d+)\]$", key)
    idx = int(m.group(2)) if m else None
    new = split_list(raw)
    cur = [x for x in (cur if isinstance(cur, list) else split_list(cur) if has_value(cur) else [])]
    if idx is not None:
        if not 1 <= idx <= max(len(cur), 1) + 1:
            raise UsageError("%s 只有 %d 项" % (m.group(1), len(cur)))
        out = list(cur)
        if idx > len(out):
            out.append(raw.strip())
        else:
            out[idx - 1] = raw.strip()
        return out
    if replace_all or len(new) > 1 or len(cur) <= 1:
        return new
    if key == "product.lines" and IMPORTANT_RE.search(quote or ""):
        raise GateError("用户说的是哪条产品线最重要:用 --set main_line=%s 记,product.lines 不动(%s);"
                        "真要改其中一项写 product.lines[N]=<新值>" % (raw.strip(), "、".join(map(str, cur))))
    if key == "customers" and re.search(r"主要|最重要|main|primary|most important", quote or "", re.I):
        return [raw.strip()] + [x for x in cur if str(x).strip().lower() != raw.strip().lower()]
    nt = _tokens(raw)
    scored = sorted(((len(nt & _tokens(x)) / float(len(nt | _tokens(x)) or 1), i) for i, x in enumerate(cur)), reverse=True)
    if not scored or scored[0][0] == 0 or (len(scored) > 1 and scored[0][0] == scored[1][0]):
        raise UsageError("%s 现在有 %d 项(%s),看不出「%s」要换掉哪一项:写 %s[N]=<新值> 指定第几项,"
                         "或者把全部项写出来整份换" % (key, len(cur), ";".join("%d. %s" % (i + 1, x) for i, x in enumerate(cur)),
                                              raw.strip(), key))
    out = list(cur)
    out[scored[0][1]] = raw.strip()
    return out


def apply_correction(prof, r, key, v, quote):
    base = re.sub(r"\[\d+\]$", "", key)
    if base == "stage":
        try:
            sid = int(str(v).strip())
        except ValueError:
            raise UsageError("stage 要写成阶段编号 0–5(0 想法 … 5 改版),收到 %r" % v)
        prof["stage"].update({"value": sid, "confirmed": True})
    if base in lifecycle.PROFILE_LIST_KEYS:
        cur = fact_value(prof, base)
        value = corrected_list(key, cur, v, quote)
    else:
        value = fact_shape(base, v)
    hit = False
    for f in prof["facts"]:
        if f["key"] == base:
            f.update({"value": value, "status": "corrected", "quote": quote, "at": now(), "source": "用户纠正"})
            f.pop("note", None)
            hit = True
    if not hit:
        prof["facts"].append({"key": base, "value": value, "source": "用户纠正", "kind": "fact",
                              "status": "corrected", "ring": r, "quote": quote, "at": now()})
    for qid, fkey in ANSWER_FACTS.items():          # 第 1 环答案和事实是同一件事:改一处,两处一起变
        if fkey == base:
            prof["rings"]["1"]["answers"][qid] = fmt_val(value) if isinstance(value, list) else value
    return base


def merge_customers(prof, v):
    """「主要客户是谁」的回答放第一项;草稿里(还没确认的)别的客户群留在后面,和回答说的是同一群的去掉。"""
    new = split_list(v)
    cur = next((f for f in prof.get("facts") or [] if f.get("key") == "customers"), None)
    if not cur or cur.get("status") != "unconfirmed" or not isinstance(cur.get("value"), list):
        return new
    def same(a, b):
        ta, tb = _tokens(a), _tokens(b)
        return bool(ta and tb) and len(ta & tb) / float(min(len(ta), len(tb))) >= 0.4
    return new + [x for x in cur["value"] if not any(same(x, n) for n in new)]


def fill_from_draft(prof, r, d, ring):
    """确认时:已有上下文文件覆盖的问题取那份文件的值;并进第 1 问、没单独答的取猜测。→ 补了哪些 id。"""
    filled = []
    for q in d["questions"]:
        if q["id"] in ring["answers"]:
            continue
        f = covered_fact(q, prof)
        if f:
            ring["answers"][q["id"]] = fmt_val(f["value"])
            ring.setdefault("from_context", []).append(q["id"])
            filled.append(q["id"])
        elif q.get("merge_into") and not question_required(q, prof):
            g, _ = guess_for(q, prof)
            if g:
                ring["answers"][q["id"]] = g
                ring.setdefault("defaults", []).append(q["id"])
                filled.append(q["id"])
    for k in filled:
        if k in ANSWER_FACTS:
            upsert_fact(prof, ANSWER_FACTS[k], ring["answers"][k], "confirmed", r, None, "用户确认第 %d 环(取草稿)" % r)
    return filled


def cmd_answer(ns):
    ws = ws_dir(ns)
    prof = load_profile(ws)
    r = ns.ring
    if not 1 <= r <= 6:
        raise UsageError("--ring 只能是 1–6")
    check_quote(ns.quote, bool(ns.correct or ns.unknown))
    if r > 1 and prof["rings"]["1"]["status"] != "confirmed":
        raise GateError("第 1 环还没确认,不能记第 %d 环" % r)
    ring = prof["rings"][str(r)]
    if not ring.get("asked_at"):
        raise GateError("第 %d 环还没发给用户(先 onboard.py show --ring %d)" % (r, r))
    d = bank()[r]
    qmap = {q["id"]: q for q in d["questions"]}
    sets = parse_kv(ns.set, "--set")
    for k in sets:
        if k not in qmap:
            raise UsageError("第 %d 环没有问题 %s;有:%s" % (r, k, ", ".join(qmap)))
    corrections = parse_kv(ns.correct, "--correct")
    staged = json.loads(json.dumps(prof))         # 纠正先在副本上做:被挡住时档案不动
    for k, v in corrections.items():
        apply_correction(staged, r, k, v, ns.quote)
    prof.clear()
    prof.update(staged)
    ring = prof["rings"][str(r)]
    private = read_json(ctx(ws, "private", "answers.json"), {}) or {}
    for k, v in sets.items():
        q = qmap[k]
        if q.get("sensitive"):
            private[k] = {"value": v, "at": now(), "ring": r}
            ring["answers"][k] = "(已答,存在 context/private/)"
        else:
            ring["answers"][k] = v
            if k in ANSWER_FACTS:
                fv = merge_customers(prof, v) if k == "customers" else v
                upsert_fact(prof, ANSWER_FACTS[k], fv, "confirmed", r, ns.quote, "用户回答(第 %d 环 %s)" % (r, k))
        if q.get("deny") and v and v.strip().lower() not in ("没有", "无", "none", "no", "a", "a.", "a. 没有"):
            for item in split_deny(v):
                if item not in [x["item"] for x in prof["deny"]]:
                    prof["deny"].append({"item": item, "at": now(), "quote": ns.quote})
    if corrections:                                # 纠正了草稿的某几条、没否认其余:「草稿对不对」那一问算答了
        for q in d["questions"]:
            if q.get("answered_by_corrections") and q["id"] not in sets and q["id"] not in ring["answers"]:
                labels = "、".join(FACT_LABELS.get(re.sub(r"\[\d+\]$", "", k), k).split("(")[0] for k in corrections)
                ring["answers"][q["id"]] = "有几处要改:%s(按用户原话改了;其余照草稿,用户没否认)" % labels
                ring.setdefault("from_corrections", []).append(q["id"])
    for k in ns.unknown or []:
        if k not in qmap:
            raise UsageError("第 %d 环没有问题 %s" % (r, k))
        ring["answers"][k] = "(用户不知道)"
        f = upsert_fact(prof, ANSWER_FACTS.get(k, "answer." + k), None, "unknown", r, ns.quote, "用户不知道")
        f["id"] = k
    if private:
        write_json(ctx(ws, "private", "answers.json"), private)
        ensure_private_ignored(ws)
    if any(qmap[k].get("sensitive") for k in sets):
        import hashlib
        h = hashlib.sha256(ns.quote.encode("utf-8")).hexdigest()[:12]
        private.setdefault("_quotes", []).append({"at": now(), "ring": r, "text": ns.quote, "sha": h})
        write_json(ctx(ws, "private", "answers.json"), private)
        ring["quotes"].append({"at": now(), "text": "(含敏感内容,原话存 context/private/,sha %s)" % h})
    else:
        ring["quotes"].append({"at": now(), "text": ns.quote})
    msg = "第 %d 环记答案 %d 条" % (r, len(sets) + len(ns.unknown or []) + len(
        [q for q in d["questions"] if q.get("answered_by_corrections") and corrections and q["id"] not in sets
         and q["id"] in (ring.get("from_corrections") or [])]))
    if corrections:
        msg += ",纠正 %s" % "、".join(corrections)
    for key in lifecycle.PROFILE_LIST_KEYS:          # 列表字段拆成了几项,打出来让 agent 当场核对
        if key in [re.sub(r"\[\d+\]$", "", k) for k in corrections] or (
                key == "customers" and "customers" in sets):
            v = fact_value(prof, key)
            if isinstance(v, list):
                print("%s 记成 %d 项:%s" % (key, len(v), " | ".join(map(str, v))))
    if ns.confirm:
        missing = [q["id"] for q in d["questions"]
                   if question_required(q, prof) and q["id"] not in ring["answers"] and not covered_fact(q, prof)]
        if missing:
            save_profile(ws, prof, msg)
            hint = ""
            if "main_line" in missing and lines_state(prof) == "missing":
                hint = "(产品线草稿是未知:用户说的产品线用 --correct product.lines=<A、B、C> 记,最重要的那条用 --set main_line=<那条>)"
            raise GateError("第 %d 环还有必答题没答:%s%s" % (r, ", ".join(missing), hint))
        if r == 4:
            audit_gate(ws, prof, ns, msg)
        if r == 6 and not read_json(plan_file(ws)):
            ring["asked_at"] = None                 # 用户回话时还没有方案:出了方案重新发一次再确认
            save_profile(ws, prof, msg)
            raise UsageError("第 6 环确认的是方案,工作区里还没有 plan/plan.json;这次答案已存下,这一环没确认。照抄跑:\n  %s\n"
                             "它会生成方案并打印带方案摘要的那一块:原样发给用户,等他看过回话再确认"
                             % ob_cmd(ws, "show --ring 6"))
        filled = fill_from_draft(prof, r, d, ring)
        if filled:
            msg += ",按草稿补 %s" % "、".join(filled)
        ring["status"] = "confirmed"
        ring["confirmed_at"] = now()
        ring.pop("reopened", None)
        for f in ring_facts(prof, d):
            if f.get("status") == "unconfirmed":
                f["status"] = "confirmed"
                f["confirmed_at"] = now()
        if r == 1 and prof["stage"].get("value") is None:
            save_profile(ws, prof, msg)
            raise GateError("产品阶段还是未知:先问用户在哪个阶段(0 想法 … 5 改版),用 --correct stage=N 记下再确认")
        if r == 1 and not prof["stage"].get("confirmed"):
            prof["stage"]["confirmed"] = True
        msg += ",确认"
    save_profile(ws, prof, msg)
    if ns.confirm:
        res = sync_pm_context(ws, prof, r)
        if res and res["changed"]:
            save_profile(ws, prof, "写回 %s:%s" % (res["path"], "、".join(prof["context_sync"]["fields"])))
            print("已写回 %s(改了 %s;别的段落没动)" % (res["path"], "、".join(prof["context_sync"]["fields"])))
    if ns.confirm or any(re.sub(r"\[\d+\]$", "", k) == "stage" for k in corrections):
        diag = refresh_diagnosis(ws)
        if "stage" in corrections:
            print("阶段改成:%s(用户确认,之后重算不会改回)" % diag["stage"]["name"])
    if ns.confirm and r == 6:
        plan_path = os.path.join(ws, "plan", "plan.json")
        plan = read_json(plan_path)
        ok = str(ring["answers"].get("approve_plan", "")).strip()
        if plan and ok.startswith("可以"):
            plan.update({"status": "approved", "approved_at": now(), "approved_quote": ns.quote})
            write_json(plan_path, plan)
            print("方案已定稿(plan/plan.json status=approved)。")
        elif plan:
            print("用户要改方案:按原话改 seo-ops/playbook/plays.json 或档案后重跑 plan.py build,再发给用户确认。")
    if not ns.confirm:
        print(msg + "(这一环还没确认)。")
        print(partial_report(prof, r, ws, ns.quote))
        return 0
    nxt = current_ring(prof)
    print("%s。%s" % (msg, ("下一环:%s" % ob_cmd(ws, "show --ring %d" % nxt)) if nxt else "6 环都完成了。"))
    if nxt:
        print("这句原话只确认了刚才的第 %d 环。第 %d 环要把 show 打印的那一块原样发给用户、停下,等到用户新的回话"
              "再记答案和确认;不能拿同一句话接着确认第 %d 环。" % (r, nxt, nxt))
    return 0


def audit_gate(ws, prof, ns, msg):
    """第 4 环确认前:站点已上线就要有成功的体检记录(改版阶段另要基线);没有就停(退出码 2),答案照样存下。
    --no-audit "<原因>" 是逃生口:原因记进档案 audit,标未确认。"""
    if not audit_needed(prof, ws):
        prof.pop("audit", None)
        return
    site = prof.get("site")
    tri = triage_record(ws, site)
    base = baseline_record(ws, site) if stage_value(prof) == 5 else None
    need_base = stage_value(prof) == 5 and not base
    if tri and not need_base:
        prof["audit"] = {"ran": True, "triage": tri, "baseline": base, "at": now()}
        if ns.no_audit:
            warn("体检记录已经有了(%s),--no-audit 没用上" % tri)
        return
    reason = (ns.no_audit or "").strip()
    if reason:
        prof["audit"] = {"ran": False, "reason": reason, "status": "unconfirmed", "at": now(), "quote": ns.quote,
                         "triage": tri, "baseline": base}
        return
    save_profile(ws, prof, msg)
    tri_cmds, base_cmd = audit_cmds(prof, ws)
    todo = []                                   # 每行一条能直接粘进 shell 的命令,说明放在行尾 # 后面
    if not tri:
        todo.append(" && ".join(tri_cmds) + "  # 体检")
    if need_base:
        todo.append(base_cmd + "  # 改版前基线")
    again = ob_cmd(ws, "answer --ring 4 --quote %s --confirm" % shlex.quote(ns.quote or ""))
    raise UsageError("站点已上线,第 4 环确认前工作区里要有%s;这次答案已存下,这一环没确认。照抄跑:\n  %s\n跑完再确认:\n  %s\n"
                     "真跑不了(站点打不开、没权限)才加 --no-audit \"<原因>\" 确认,原因会写进档案和方案"
                     % ("一次成功的体检记录" + ("和改动前基线" if need_base else "") if not tri else "改动前基线",
                        "\n  ".join(todo), again))


def question_answered(q, answers):
    """一个编号问题(可能并了几个 id)算答了:主 id 有答案,并进来的必答 id 也有。"""
    if q["id"] not in answers:
        return False
    return all(m["id"] in answers for m in q.get("merged") or [] if m.get("required"))


def unanswered_part(q, answers):
    """一问并了几个 id、主问已经答了:只留没答的必答部分(文字、猜测、选项取那一部分的),已答的不再问。"""
    if q["id"] not in answers:
        return q
    rest = [m for m in q.get("merged") or [] if m.get("required") and m["id"] not in answers]
    if not rest:
        return q
    m = dict(rest[0], merged=[])
    for extra in rest[1:]:
        m["text"] = "%s %s" % (m["text"], extra["text"])
    return m


def partial_report(prof, r, ws, quote):
    """answer 不带 --confirm:哪几题记了、还没答的题原样再问(编号、选项、猜测不变)、怎么确认。"""
    view = ring_view(prof, r)
    answers = prof["rings"][str(r)].get("answers") or {}
    done = [(i, q) for i, q in enumerate(view["questions"], 1) if question_answered(q, answers)]
    todo = [(i, q) for i, q in enumerate(view["questions"], 1) if not question_answered(q, answers)]
    half = [(i, q) for i, q in todo if q["id"] in answers]
    L = ["已记答案:" + ("、".join("第 %d 题(%s)" % (i, "+".join(q["ids"])) for i, q in done) if done else "没有")
         + "".join(";第 %d 题答了 %s,只差 %s" % (i, q["id"], "、".join(
             m["id"] for m in q.get("merged") or [] if m.get("required") and m["id"] not in answers))
             for i, q in half)]
    rule = ("已答的题里用户没说到的细节不追问、不另编问题:在那一题的答案里写「未说」,或用 --unknown <id>,"
            "然后直接 --confirm。")
    if todo:
        L += ["还没答的题 %d 个:把下面这块原样发给用户,停下等回答(编号、选项和猜测照原样,不加别的问题)。" % len(todo), "",
              BLOCK_START + "(到下面那行等号为止;不改写、不删选项、不合并问题)=====",
              "**开局第 %d 环 · %s**(还没答的题)" % (r, view["title"]), ""]
        L += [render_question(i, unanswered_part(q, answers)) for i, q in todo]
        L += [BLOCK_END + " =====", "", rule,
              "用户回了以后:" + ob_cmd(ws, "answer --ring %d --set <id>=<答案> ... --quote \"<用户这次回话的原文>\" --confirm" % r),
              "用户说「按你的猜测来」:没答的题用上面的猜测 --set,或 --unknown <id>,带 --confirm。"]
    else:
        L += ["这一环的题都有答案了。" + rule, "确认这一环,照抄:",
              "  " + ob_cmd(ws, "answer --ring %d --quote %s --confirm" % (r, shlex.quote(quote or "")))]
    return "\n".join(L)


def cmd_skip(ns):
    ws = ws_dir(ns)
    prof = load_profile(ws)
    if not (ns.quote or "").strip():
        raise GateError("必须用 --quote 带上用户原话")
    if not is_skip_request(ns.quote):
        raise GateError("「%s」不是要跳过。%s" % (ns.quote.strip()[:80], SKIP_HINT))
    if prof["rings"]["1"]["status"] != "confirmed":
        raise GateError("第 1 环(产品是什么、客户是谁、转化算什么)必须先确认;"
                        "把第 1 环压到必答题再问一次:onboard.py show --ring 1")
    skipped = []
    for r in range(2, 7):
        ring = prof["rings"][str(r)]
        if ring["status"] not in ("confirmed", "skipped"):
            ring["status"] = "skipped"
            ring["quotes"].append({"at": now(), "text": ns.quote})
            skipped.append(r)
    save_profile(ws, prof, "用户要求跳过第 %s 环;这些环的内容按猜测补齐,方案开头要列出" % "、".join(map(str, skipped)))
    unconf = [f["key"] for f in prof["facts"] if f.get("status") == "unconfirmed"]
    print("跳过第 %s 环。方案开头必须列出这些没确认的猜测:%s" % ("、".join(map(str, skipped)) or "无",
                                                     "、".join(unconf) or "无"))
    return 0


def cmd_event(ns):
    ws = ws_dir(ns)
    prof = load_profile(ws)
    allowed = lifecycle.load_rules(ws).get("change_events") or []
    if ns.kind not in allowed:
        raise UsageError("事件只能是:%s" % ", ".join(allowed))
    if ns.action == "add":
        if ns.kind not in prof["events"]:
            prof["events"].append(ns.kind)
        prof.setdefault("event_notes", []).append({"kind": ns.kind, "note": ns.note, "at": now()})
    else:
        prof["events"] = [e for e in prof["events"] if e != ns.kind]
    save_profile(ws, prof, "事件 %s %s" % (ns.action, ns.kind))
    diag = lifecycle.diagnose(read_json(ctx(ws, "scan.json")), ws)
    write_json(ctx(ws, "diagnosis.json"), diag)
    print("记下。现在的阶段:%s" % diag["stage"]["name"])
    return 0


def cmd_metric(ns):
    ws = ws_dir(ns)
    prof = load_profile(ws)
    vals = parse_kv(ns.set, "--set")
    if not vals:
        raise UsageError("至少一个 --set key=value(如 gsc_clicks_28d=1200)")
    if not ns.source:
        raise UsageError("metric 必须带 --source(gsc_api.py 输出、导出文件或数据库表名)")
    for k, v in vals.items():
        try:
            num = float(v)
            v = int(num) if num.is_integer() else num
        except ValueError:
            v = {"true": True, "false": False}.get(v.lower(), v)
        prof.setdefault("metrics", {})[k] = v
    prof.setdefault("metric_sources", {}).update({k: ns.source for k in vals})
    save_profile(ws, prof, "记指标 %s(来源 %s)" % (",".join(vals), ns.source))
    import loops as _loops
    _loops.append_metrics(ws, {k: prof["metrics"][k] for k in vals}, ns.source, ns.at)
    diag = lifecycle.diagnose(read_json(ctx(ws, "scan.json")), ws)
    write_json(ctx(ws, "diagnosis.json"), diag)
    prof = load_profile(ws)
    if not prof["stage"].get("confirmed"):
        prof["stage"].update({"value": diag["stage"]["stage"], "rule_value": diag["stage"]["stage"],
                              "confidence": diag["stage"]["confidence"]})
        save_profile(ws, prof, "阶段按新指标重判:%s" % diag["stage"]["name"])
    print("记下。阶段:%s(%s)" % (diag["stage"]["name"], diag["stage"]["confidence"]))
    reprint_block(ws)
    return 0


def cmd_status(ns):
    ws = ws_dir(ns)
    prof = load_profile(ws)
    diag = refresh_diagnosis(ws)                  # 现算,不读旧的 diagnosis.json:用户确认或纠正过的阶段压过规则
    b = bank()
    rows = [{"ring": r, "title": b[r]["title"], "status": prof["rings"][str(r)]["status"],
             "confirmed_at": prof["rings"][str(r)].get("confirmed_at")} for r in range(1, 7)]
    out = {"version": prof.get("version"), "updated": prof.get("updated"), "rings": rows,
           "stage": (diag.get("stage") or {}).get("name"), "current_ring": current_ring(prof),
           "unconfirmed": sum(1 for f in prof["facts"] if f.get("status") == "unconfirmed"),
           "deny": [d["item"] for d in prof.get("deny") or []], "audit": prof.get("audit")}
    if ns.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    zh = {"pending": "没开始", "asking": "问了在等回答", "confirmed": "已确认", "skipped": "跳过(按猜测)"}
    print("档案 v%s(更新 %s);阶段:%s;未确认事实 %d 条" % (out["version"], out["updated"], out["stage"], out["unconfirmed"]))
    print("工作区:%s" % ws)
    if audit_skipped(prof):
        print("体检没跑:%s(未确认)" % audit_skipped(prof))
    for row in rows:
        print("  第 %d 环 %-8s %s%s" % (row["ring"], row["title"], zh.get(row["status"], row["status"]),
                                    (" " + row["confirmed_at"]) if row["confirmed_at"] else ""))
    if out["deny"]:
        print("明确不做:" + "、".join(out["deny"]))
    print("档案的键:事实在 facts[](每条 key / value / status / source),顶层 _schema 是脚本写好的映射"
          "(%s → facts 里 key 等于它的那一条;stage → stage.id);读档案按它取,不用手加。" % "、".join(lifecycle.PROFILE_FACT_KEYS))
    if all(row["status"] in ("confirmed", "skipped") for row in rows):
        print("开局已完成。第二次打开只跑这一条,把它最前面「原样发给用户」那一块原样贴出:%s"
              % lifecycle.shell_cmd(os.path.join(HERE, "project.py"), ["ops", "weekly", "--ws", ws]))
    return 0


def refresh_diagnosis(ws):
    diag = lifecycle.diagnose(read_json(ctx(ws, "scan.json")), ws)
    write_json(ctx(ws, "diagnosis.json"), diag)
    return diag


def cmd_diagnose(ns):
    ws = ws_dir(ns)
    load_profile(ws)
    diag = lifecycle.diagnose(read_json(ctx(ws, "scan.json")), ws)
    write_json(ctx(ws, "diagnosis.json"), diag)
    print(json.dumps(diag, ensure_ascii=False, indent=1) if ns.json else lifecycle.render(diag))
    return 0


def repo_label(repo):
    """产品档案里仓库那一栏:相对路径(工作区就在仓库里)写成人话,不把 .. 打给用户。"""
    if not repo:
        return "—"
    return repo if os.path.isabs(repo) else "工作区所在的仓库(%s)" % repo


def render_product_md(prof):
    b = bank()
    L = ["# 产品档案(seo-suite 开局)", "",
         "> 由 onboard.py 生成,别手改;改内容用 onboard.py answer --correct。版本 v%s,更新 %s。"
         % (prof.get("version"), prof.get("updated")), "",
         "站点:%s;仓库:%s;阶段:%s%s" % (prof.get("site") or "—", repo_label(prof.get("repo")),
                                    (prof.get("stage") or {}).get("value", "—"),
                                    "(已确认)" if (prof.get("stage") or {}).get("confirmed") else "(未确认)"), ""]
    for r in range(1, 7):
        d, ring = b[r], prof["rings"][str(r)]
        L += ["## 第 %d 环 · %s(%s)" % (r, d["title"], ring["status"]), ""]
        for f in ring_facts(prof, d):
            L.append("- %s:%s(%s,出处 %s)" % (f["key"], fmt_val(f.get("value"))[:200], f.get("status"), f.get("source") or "—"))
        for k, v in (ring.get("answers") or {}).items():
            L.append("- 答 %s:%s" % (k, v))
        L.append("")
    if prof.get("deny"):
        L += ["## 明确不做(禁用清单)", ""] + ["- %s(%s)" % (x["item"], x["at"][:10]) for x in prof["deny"]] + [""]
    L += ["## 变更记录", ""] + ["- v%s %s %s" % (c["version"], c["at"], c["change"]) for c in prof.get("changelog") or []]
    return "\n".join(L) + "\n"


def build_parser():
    ap = argparse.ArgumentParser(description="开局 6 环:先吃透产品,再一环一环问用户")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_ws(p):
        p.add_argument("--ws", help="seo-ops 工作区(默认 ./seo-ops)")
    p = sub.add_parser("start")
    add_ws(p)
    p.add_argument("--site")
    p.add_argument("--repo")
    p.add_argument("--market")
    p.add_argument("--scan", help="用现成的 product_scan.json,不再抓")
    p.add_argument("--max-pages", type=int, default=20)
    p.add_argument("--allow-local", action="store_true")
    p.add_argument("--no-wayback", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("show")
    add_ws(p)
    p.add_argument("--ring", type=int)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("note")
    add_ws(p)
    p.add_argument("--ring", type=int, required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--value", required=True)
    p.add_argument("--source", required=True)
    p = sub.add_parser("answer")
    add_ws(p)
    p.add_argument("--ring", type=int, required=True)
    p.add_argument("--set", action="append")
    p.add_argument("--correct", action="append")
    p.add_argument("--unknown", action="append")
    p.add_argument("--quote")
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--no-audit", metavar="原因",
                   help="第 4 环:站点已上线但真跑不了体检时用,原因写进档案、标未确认")
    p = sub.add_parser("skip")
    add_ws(p)
    p.add_argument("--quote")
    p = sub.add_parser("event")
    add_ws(p)
    p.add_argument("action", choices=("add", "remove"))
    p.add_argument("kind")
    p.add_argument("--note", default="")
    p = sub.add_parser("metric")
    add_ws(p)
    p.add_argument("--set", action="append")
    p.add_argument("--source")
    p.add_argument("--at", help="这批指标的截止日 YYYY-MM-DD(默认从 --source 里的 Pages_起_止.csv 取「止」,取不到用今天;记进指标历史,阶段门槛循环用)")
    p = sub.add_parser("status")
    add_ws(p)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("diagnose")
    add_ws(p)
    p.add_argument("--json", action="store_true")
    return ap


def main(argv=None):
    global ARGV
    ARGV = list(sys.argv[1:] if argv is None else argv)
    ns = build_parser().parse_args(argv)
    fn = {"start": cmd_start, "show": cmd_show, "note": cmd_note, "answer": cmd_answer, "skip": cmd_skip,
          "event": cmd_event, "metric": cmd_metric, "status": cmd_status, "diagnose": cmd_diagnose}[ns.cmd]
    try:
        return fn(ns)
    except (UsageError, GateError, lifecycle.UsageError) as e:
        print("错误: %s" % e, file=sys.stderr)
        return getattr(e, "code", 2)


if __name__ == "__main__":
    sys.exit(main())
