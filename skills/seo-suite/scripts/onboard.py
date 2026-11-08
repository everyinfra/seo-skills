#!/usr/bin/env python3
"""onboard.py — 开局 6 环:先吃透产品,再一环一环问用户(RQ-237;stdlib only)。

流程:
  start    建工作区(没有就调 project.py init)→ product_scan.py 读站点和仓库 → lifecycle.py 判阶段和成熟度
           → 起草产品档案 seo-ops/context/profile.json + product.md → 打印第 1 环
  show     打印某一环(默认当前环):agent 先做什么、草稿事实(带出处)、问题(带猜测和选项)、停下的指令
  note     agent 把自己查到的东西记进档案(一律「未确认」,用户确认前不当事实用)
  answer   记用户的回答:--quote 必须是用户原话;--confirm 确认这一环(必答题答齐、这一环问过才行)
  skip     用户说「别问了」:第 1 环没确认就拒绝(退出码 3),确认过就把剩下的环标「跳过」、用猜测补齐
  event    记改版类事件(migration / new_product_line …),阶段会切到「改版 / 迁移 / 转型」
  status   一屏:每环状态、档案版本、阶段
  diagnose 重跑阶段 × 成熟度诊断

规矩(红队 11-08):
  - 第 1 环必须由用户确认:没有 --quote 不能确认;这一环没 show 过不能确认。
  - 网页上抓来的东西只当草稿(status=unconfirmed),用户确认这一环后才变 confirmed。
  - 敏感答案(处罚史、预算、审批人)存 context/private/,该目录写进 seo-ops/.gitignore。
  - 第 5 环「明确不做」的答案进 profile.deny(结构化禁用清单),下游推荐按它过滤。

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
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lifecycle  # noqa: E402

PY = sys.executable or "python3"
BANK_PATH = os.path.join(os.path.dirname(HERE), "data", "onboarding.json")
SCHEMA = 1
PRIVATE_IGNORE = "context/private/"


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
    return os.path.abspath(ns.ws or "seo-ops")


def ctx(ws, *parts):
    return os.path.join(ws, "context", *parts)


def load_profile(ws):
    p = read_json(ctx(ws, "profile.json"))
    if p is None:
        raise UsageError("还没开局:先跑 onboard.py start --site <URL>(工作区 %s)" % ws)
    if int(p.get("schema") or 0) > SCHEMA:
        raise UsageError("档案是更新版本的 seo-suite 写的(schema %s),先升级 skill" % p.get("schema"))
    return p


def save_profile(ws, prof, change):
    prof["version"] = int(prof.get("version") or 0) + 1
    prof["updated"] = now()
    prof.setdefault("changelog", []).append({"version": prof["version"], "at": prof["updated"], "change": change})
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
        out.append({"key": key, "value": f.get("value"), "source": f.get("source"),
                    "kind": f.get("kind") or "inferred", "status": "unconfirmed", "ring": ring, "at": now()})
    return out


def run_json(cmd, out_path):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    data = read_json(out_path) if out_path and os.path.isfile(out_path) else None
    return p.returncode, data, (p.stderr or "")[-800:]


def cmd_start(ns):
    ws = ws_dir(ns)
    if not ns.site and not ns.repo:
        raise UsageError("至少给 --site 或 --repo")
    if os.path.isfile(ctx(ws, "profile.json")) and not ns.force:
        print("已经开过局(%s);接着问用 onboard.py show,要从头来加 --force" % ctx(ws, "profile.json"))
        return cmd_show(argparse.Namespace(ws=ns.ws, ring=None, json=False))
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
            "site": ns.site, "repo": os.path.abspath(ns.repo) if ns.repo else None, "market": ns.market,
            "rings": {str(r): {"status": "pending", "answers": {}, "quotes": [], "asked_at": None,
                               "confirmed_at": None} for r in range(1, 7)},
            "facts": facts_from_scan(scan), "stage": {}, "events": [], "metrics": {}, "deny": [],
            "existing_context": scan.get("existing_context") or [], "changelog": []}
    save_profile(ws, prof, "开局:从 product_scan 起草 %d 条事实(全部未确认)" % len(prof["facts"]))
    diag = lifecycle.diagnose(scan, ws)
    write_json(ctx(ws, "diagnosis.json"), diag)
    prof = load_profile(ws)
    prof["stage"] = {"value": diag["stage"]["stage"], "rule_value": diag["stage"]["stage"],
                     "confidence": diag["stage"]["confidence"], "confirmed": False}
    save_profile(ws, prof, "阶段初判:%s(%s)" % (diag["stage"]["name"], diag["stage"]["confidence"]))
    if errors:
        print("读取时有 %d 个错误(已记进 scan.json):%s" % (len(errors), ";".join(map(str, errors[:3]))))
    return cmd_show(argparse.Namespace(ws=ns.ws, ring=1, json=ns.json))


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------

def site_type_of(prof):
    return str(fact_value(prof, "site.type") or "")


def question_applies(q, prof):
    cond = q.get("when")
    if not cond:
        return True
    if cond.startswith("site_type in "):
        allowed = cond[len("site_type in "):].split(",")
        st = site_type_of(prof).lower()
        return not st or any(a.strip() in st for a in allowed)
    return True


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
            return fmt_val(v[:1]), "来自草稿 %s 第一项" % src
        if v:
            return fmt_val(v), "来自草稿 %s" % src
    return None, None


def ring_view(prof, r):
    d = bank()[r]
    qs = []
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
        qs.append({"id": q["id"], "text": q["text"], "options": opts[:5], "guess": g, "guess_from": gsrc,
                   "required": bool(q.get("required")), "sensitive": bool(q.get("sensitive")),
                   "deny": bool(q.get("deny"))})
    facts = ring_facts(prof, d)
    view = {"ring": r, "title": d["title"], "goal": d["goal"], "must_confirm": d.get("must_confirm"),
            "status": prof["rings"][str(r)]["status"], "agent_steps": d["agent_steps"],
            "facts": facts, "questions": qs}
    return view


def render_ring(prof, view, ws):
    r = view["ring"]
    L = ["# 开局第 %d 环 · %s%s" % (r, view["title"], "(这一环必须确认完才往下)" if view["must_confirm"] else ""), "",
         "目标:" + view["goal"], ""]
    prev = [str(i) for i in range(1, r) if prof["rings"][str(i)]["status"] == "confirmed"]
    if prev:
        L.append("前面已确认:第 %s 环(档案 v%s)。" % ("、".join(prev), prof.get("version")))
        L.append("")
    if r == 1:
        diag = read_json(ctx(ws, "diagnosis.json"), {}) or {}
        st = diag.get("stage") or {}
        if st:
            tag = {"guess": "猜测", "unknown": "证据不够", "rule": "按规则", "confirmed": "已确认"}.get(st.get("confidence"), "")
            L.append("【产品阶段】%s(%s):%s" % (st.get("name"), tag, ";".join(st.get("why") or [])))
            if st.get("candidates"):
                L.append("  候选:" + "、".join(c["name"] for c in st["candidates"]) + "——在第 1 个问题里请用户确认")
            L.append("")
        if prof.get("existing_context"):
            L += ["已有产品上下文文件(先读它当草稿):" + "、".join(c.get("path", "") for c in prof["existing_context"]), ""]
    L.append("## agent 先做(做完再问)")
    L += ["- " + s for s in view["agent_steps"]]
    L.append("")
    if view["facts"]:
        L += ["## 草稿(每条带出处;未确认的不当事实用)", "", "| 项 | 内容 | 出处 | 状态 |", "|---|---|---|---|"]
        for f in view["facts"]:
            L.append("| %s | %s | %s | %s |" % (f["key"], fmt_val(f.get("value"))[:160].replace("|", "/"),
                                              f.get("source") or "—",
                                              {"unconfirmed": "未确认" + ("(推测)" if f.get("kind") == "inferred" else ""),
                                               "confirmed": "已确认", "corrected": "用户改过",
                                               "unknown": "用户不知道"}.get(f.get("status"), f.get("status"))))
        L.append("")
    L.append("## 问用户(最多 %d 个;每个带你的猜测)" % len(view["questions"]))
    for i, q in enumerate(view["questions"], 1):
        line = "%d. %s%s" % (i, q["text"], "(必答)" if q["required"] else "")
        if q["options"]:
            line += "\n   选项:" + " | ".join(q["options"])
        if q["guess"]:
            line += "\n   我的猜测:%s(%s)" % (q["guess"], q["guess_from"])
        if q["sensitive"]:
            line += "\n   (答案只存本地 context/private/,不进 git)"
        line += "\n   [id=%s]" % q["id"]
        L.append(line)
    L += ["", "## 停",
          "现在停下来等用户回答,不要先给建议、不要替用户答。",
          "- Claude Code:用提问工具(AskUserQuestion)把上面的问题发出去,你的猜测放第一个选项。",
          "- 没有提问工具的宿主:把问题按编号列出来,然后结束这一回合。",
          "用户回了以后:python3 %s answer --ring %d --set <id>=<答案> ... --quote \"<用户原话>\" --confirm"
          % (os.path.join(HERE, "onboard.py"), r),
          "用户纠正草稿:加 --correct <项>=<改后的值>;用户说不知道:加 --unknown <id>。"]
    if r > 1:
        L.append("用户说「别问了」:python3 %s skip --quote \"<用户原话>\"(剩下的环用猜测补齐、写明未确认)"
                 % os.path.join(HERE, "onboard.py"))
    else:
        L.append("用户说「别问了」也要先把这一环答完:把问题压到最少(上面的必答题),说明原因再问一次。")
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
    if ring["status"] in ("pending",):
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
    prof["facts"].append({"key": ns.key, "value": ns.value, "source": ns.source, "kind": "inferred",
                          "status": "unconfirmed", "ring": ns.ring, "at": now()})
    save_profile(ws, prof, "agent 记:%s(第 %s 环,未确认)" % (ns.key, ns.ring))
    print("记下 %s(未确认)" % ns.key)
    return 0


def cmd_answer(ns):
    ws = ws_dir(ns)
    prof = load_profile(ws)
    r = ns.ring
    if not 1 <= r <= 6:
        raise UsageError("--ring 只能是 1–6")
    if not (ns.quote or "").strip():
        raise GateError("必须用 --quote 带上用户原话(用户没回话就不能记答案)")
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
    private = read_json(ctx(ws, "private", "answers.json"), {}) or {}
    for k, v in sets.items():
        q = qmap[k]
        if q.get("sensitive"):
            private[k] = {"value": v, "at": now(), "ring": r}
            ring["answers"][k] = "(已答,存在 context/private/)"
        else:
            ring["answers"][k] = v
        if q.get("deny") and v and v not in ("没有", "无", "none"):
            for item in [x.strip() for x in v.replace(";", ",").replace(",", ",").replace("、", ",").split(",") if x.strip()]:
                if item not in [x["item"] for x in prof["deny"]]:
                    prof["deny"].append({"item": item, "at": now(), "quote": ns.quote})
    for k in ns.unknown or []:
        if k not in qmap:
            raise UsageError("第 %d 环没有问题 %s" % (r, k))
        ring["answers"][k] = "(用户不知道)"
    if private:
        write_json(ctx(ws, "private", "answers.json"), private)
        ensure_private_ignored(ws)
    for k, v in parse_kv(ns.correct, "--correct").items():
        hit = False
        for f in prof["facts"]:
            if f["key"] == k:
                f.update({"value": v, "status": "corrected", "quote": ns.quote, "at": now(),
                          "source": "用户纠正"})
                hit = True
        if not hit:
            prof["facts"].append({"key": k, "value": v, "source": "用户纠正", "kind": "fact",
                                  "status": "corrected", "ring": r, "quote": ns.quote, "at": now()})
        if k == "stage":
            prof["stage"].update({"value": int(v), "confirmed": True})
    if any(qmap[k].get("sensitive") for k in sets):
        import hashlib
        h = hashlib.sha256(ns.quote.encode("utf-8")).hexdigest()[:12]
        private.setdefault("_quotes", []).append({"at": now(), "ring": r, "text": ns.quote, "sha": h})
        write_json(ctx(ws, "private", "answers.json"), private)
        ring["quotes"].append({"at": now(), "text": "(含敏感内容,原话存 context/private/,sha %s)" % h})
    else:
        ring["quotes"].append({"at": now(), "text": ns.quote})
    msg = "第 %d 环记答案 %d 条" % (r, len(sets) + len(ns.unknown or []))
    if ns.confirm:
        missing = [q["id"] for q in d["questions"] if q.get("required") and q["id"] not in ring["answers"]]
        if missing:
            save_profile(ws, prof, msg)
            raise GateError("第 %d 环还有必答题没答:%s" % (r, ", ".join(missing)))
        ring["status"] = "confirmed"
        ring["confirmed_at"] = now()
        for f in ring_facts(prof, d):
            if f.get("status") == "unconfirmed":
                f["status"] = "confirmed"
                f["confirmed_at"] = now()
        if r == 1 and not prof["stage"].get("confirmed"):
            prof["stage"]["confirmed"] = True
        msg += ",确认"
    save_profile(ws, prof, msg)
    if ns.confirm:
        diag = lifecycle.diagnose(read_json(ctx(ws, "scan.json")), ws)
        write_json(ctx(ws, "diagnosis.json"), diag)
    nxt = current_ring(prof)
    print("%s。%s" % (msg, ("下一环:onboard.py show --ring %d" % nxt) if nxt else "6 环都完成了。"))
    return 0


def cmd_skip(ns):
    ws = ws_dir(ns)
    prof = load_profile(ws)
    if not (ns.quote or "").strip():
        raise GateError("必须用 --quote 带上用户原话")
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
    diag = lifecycle.diagnose(read_json(ctx(ws, "scan.json")), ws)
    write_json(ctx(ws, "diagnosis.json"), diag)
    prof = load_profile(ws)
    if not prof["stage"].get("confirmed"):
        prof["stage"].update({"value": diag["stage"]["stage"], "rule_value": diag["stage"]["stage"],
                              "confidence": diag["stage"]["confidence"]})
        save_profile(ws, prof, "阶段按新指标重判:%s" % diag["stage"]["name"])
    print("记下。阶段:%s(%s)" % (diag["stage"]["name"], diag["stage"]["confidence"]))
    return 0


def cmd_status(ns):
    ws = ws_dir(ns)
    prof = load_profile(ws)
    diag = read_json(ctx(ws, "diagnosis.json"), {}) or {}
    b = bank()
    rows = [{"ring": r, "title": b[r]["title"], "status": prof["rings"][str(r)]["status"],
             "confirmed_at": prof["rings"][str(r)].get("confirmed_at")} for r in range(1, 7)]
    out = {"version": prof.get("version"), "updated": prof.get("updated"), "rings": rows,
           "stage": (diag.get("stage") or {}).get("name"), "current_ring": current_ring(prof),
           "unconfirmed": sum(1 for f in prof["facts"] if f.get("status") == "unconfirmed"),
           "deny": [d["item"] for d in prof.get("deny") or []]}
    if ns.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    zh = {"pending": "没开始", "asking": "问了在等回答", "confirmed": "已确认", "skipped": "跳过(按猜测)"}
    print("档案 v%s(更新 %s);阶段:%s;未确认事实 %d 条" % (out["version"], out["updated"], out["stage"], out["unconfirmed"]))
    for row in rows:
        print("  第 %d 环 %-8s %s%s" % (row["ring"], row["title"], zh.get(row["status"], row["status"]),
                                    (" " + row["confirmed_at"]) if row["confirmed_at"] else ""))
    if out["deny"]:
        print("明确不做:" + "、".join(out["deny"]))
    return 0


def cmd_diagnose(ns):
    ws = ws_dir(ns)
    load_profile(ws)
    diag = lifecycle.diagnose(read_json(ctx(ws, "scan.json")), ws)
    write_json(ctx(ws, "diagnosis.json"), diag)
    print(json.dumps(diag, ensure_ascii=False, indent=1) if ns.json else lifecycle.render(diag))
    return 0


def render_product_md(prof):
    b = bank()
    L = ["# 产品档案(seo-suite 开局)", "",
         "> 由 onboard.py 生成,别手改;改内容用 onboard.py answer --correct。版本 v%s,更新 %s。"
         % (prof.get("version"), prof.get("updated")), "",
         "站点:%s;仓库:%s;阶段:%s%s" % (prof.get("site") or "—", prof.get("repo") or "—",
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
    p = sub.add_parser("status")
    add_ws(p)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("diagnose")
    add_ws(p)
    p.add_argument("--json", action="store_true")
    return ap


def main(argv=None):
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
