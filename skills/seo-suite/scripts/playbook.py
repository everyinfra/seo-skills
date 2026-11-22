#!/usr/bin/env python3
"""playbook.py — 用户自己的规则、禁用清单、检查和数据源(RQ-237 第 4 批;stdlib only)。

站点仓的 seo-ops/playbook/ 是用户按自己的想法改 skill 的地方,放在 skill 目录之外,升级 skill 不覆盖:
  rules.md          用户原话写成的规则(teach.py rule add 写,带日期和原话;可以手改)
  deny.json         结构化禁用清单:「不做 X」→ {"item", "terms", "quote", "at", "source"}。推荐代码按 terms 直接过滤,
                    不靠模型自觉。开局第 5 环写进 profile.json 的旧 deny 列表照样读,两份合并后只算一份
  checks/<名>.py    用户自己的检查(零依赖脚本)+ <名>.md 说明;checks/registry.json 记试跑、启用和启用时的 sha256
  plays.json        自定义打法,格式同 data/playbooks.json 的 plays(plan.py 读)
  loops.json        自定义循环(loops.py 读);lifecycle.json 覆盖阶段阈值(lifecycle.py 读)
  sources.json      登记的数据源(关键词量、SERP、外链、排名……),先免费后付费;doctor.py 列,demand_check.py 用

本文件是这些东西的唯一读写入口(teach.py、plan.py、ops.py、link_intel.py、prioritize.py、fix_plan.py、
content_queue.py、demand_check.py、doctor.py 都 import 它),另有两个子命令:
  python3 playbook.py hook        Claude Code SessionStart 钩子:从 stdin 读 {"cwd", "hook_event_name"},当前仓库有
                                  seo-ops/playbook/rules.md 或禁用清单时,把它们作为上下文注入(没有就什么都不输出)
  python3 playbook.py context [--ws seo-ops]   打印同一段上下文(其他宿主开工前手动跑)
  python3 playbook.py skill-dir   打印 seo-suite 实际装在哪(环境变量 → 插件根 → ~/.claude/skills → ~/.agents/skills)

用户写的检查脚本是不可信代码:只在用户确认后由 teach.py / ops.py 用子进程跑,设超时、不给环境变量,输出当数据。
"""
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
SCHEMA = 1
CONTEXT_MAX = 6000
CHECK_TIMEOUT = 20
CHECK_OUT_MAX = 64 * 1024
HTML_MAX = 2_000_000
SOURCE_TIMEOUT = 60
PROVIDES = ("keyword_volume", "serp", "backlinks", "rankings", "traffic", "other")
NEG_RE = re.compile(r"不做|别再|不要|别给|别建议|不用|不许|不准|停止|禁止|don'?t|do not|never|no more|stop\b", re.I)


class PlaybookError(Exception):
    code = 2


class GateError(Exception):
    code = 3


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today():
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, path)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 找工作区和 skill 目录
# ---------------------------------------------------------------------------

def _is_ws(d):
    return os.path.isdir(d) and any(os.path.exists(os.path.join(d, x))
                                    for x in ("project.yaml", "context", "playbook"))


def find_ws(start=None, explicit=None):
    """→ seo-ops 工作区的绝对路径或 None。explicit 给了就只认它;否则从 start(默认当前目录)往上找 seo-ops/。"""
    if explicit:
        p = os.path.abspath(explicit)
        return p if os.path.isdir(p) else None
    env = os.environ.get("SEO_OPS_WS")
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    cur = os.path.abspath(start or os.getcwd())
    if os.path.basename(cur) == "seo-ops" and _is_ws(cur):
        return cur
    home = os.path.expanduser("~")
    while True:
        cand = os.path.join(cur, "seo-ops")
        if _is_ws(cand):
            return cand
        parent = os.path.dirname(cur)
        if parent == cur or cur == home:
            return None
        cur = parent


def pb_dir(ws, *parts):
    return os.path.join(ws, "playbook", *parts)


def skill_dir_candidates(env=None, home=None):
    """seo-suite 可能装在哪,按顺序:SEO_SUITE_DIR → 插件根 → ~/.claude/skills → ~/.agents/skills。"""
    env = os.environ if env is None else env
    home = home or os.path.expanduser("~")
    out = []
    if env.get("SEO_SUITE_DIR"):
        out.append(env["SEO_SUITE_DIR"])
    if env.get("CLAUDE_PLUGIN_ROOT"):
        out.append(os.path.join(env["CLAUDE_PLUGIN_ROOT"], "skills", "seo-suite"))
    out += [os.path.join(home, ".claude", "skills", "seo-suite"), os.path.join(home, ".agents", "skills", "seo-suite")]
    return out


def resolve_skill_dir(env=None, home=None):
    for d in skill_dir_candidates(env, home):
        if os.path.isfile(os.path.join(d, "scripts", "project.py")):
            return os.path.abspath(d)
    return SKILL_DIR


def shell_find(script, installed=None, then=None):
    """生成一段 POSIX sh:按 skill_dir_candidates 的顺序找 scripts/<script>,最后退回安装时的绝对路径。
    then 给了就是找到后执行的命令(用 "$d" 指 skill 目录);不给就把 S 设成 scripts 目录。"""
    cands = ['"$SEO_SUITE_DIR"', '"$CLAUDE_PLUGIN_ROOT/skills/seo-suite"', '"$HOME/.claude/skills/seo-suite"',
             '"$HOME/.agents/skills/seo-suite"']
    if installed:
        home = os.path.expanduser("~").rstrip("/")
        inst = os.path.abspath(installed)
        if home and (inst + "/").startswith(home + "/"):      # 写进站点仓的命令不带用户名:用 $HOME 开头
            cands.append('"$HOME%s"' % re.sub(r'(["$`\\])', r"\\\1", inst[len(home):]))
        else:
            cands.append("'%s'" % inst.replace("'", "'\\''"))
    cands.append("$HOME/.claude/plugins/cache/*/seo-suite/*/skills/seo-suite")   # 插件装的:任一版本兜底
    body = then or 'S="$d/scripts"; break'
    return 'for d in %s; do if [ -f "$d/scripts/%s" ]; then %s; fi; done' % (" ".join(cands), script, body)


# ---------------------------------------------------------------------------
# 禁用清单
# ---------------------------------------------------------------------------

def _norm_entry(d, source):
    if isinstance(d, dict):
        item = str(d.get("item") or "").strip()
        terms = [str(t).strip().lower() for t in d.get("terms") or [] if str(t).strip()]
        out = dict(d, item=item, terms=terms or ([item.lower()] if item else []))
        out.setdefault("source", source)
        return out if item else None
    item = str(d or "").strip()
    return {"item": item, "terms": [item.lower()], "source": source} if item else None


def load_deny(ws, profile=None):
    """playbook/deny.json + 档案里开局第 5 环的 deny(旧位置,照样读),按 item 去重。"""
    out, seen = [], set()
    if ws:
        data = read_json(pb_dir(ws, "deny.json"), {}) or {}
        for d in data.get("deny") or []:
            e = _norm_entry(d, "teach")
            if e and not e.get("removed") and e["item"].lower() not in seen:
                seen.add(e["item"].lower())
                out.append(e)
        if profile is None:
            profile = read_json(os.path.join(ws, "context", "profile.json"), {}) or {}
    for d in (profile or {}).get("deny") or []:
        e = _norm_entry(d, "onboard")
        if e and e["item"].lower() not in seen:
            seen.add(e["item"].lower())
            out.append(e)
    return out


def _term_hit(term, text):
    if not term:
        return False
    if re.fullmatch(r"[a-z0-9][a-z0-9 ._-]*", term):
        return re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(term), text) is not None
    return term in text


def deny_match(text, tags, deny):
    """→ ("drop", item) 整条命中 / ("note", [items]) 只沾边 / None。
    整条命中:禁用项的任一关键词出现在文字或标签里;沾边:建议的某个标签(≥2 字)出现在禁用项里
    (比如禁了「Reddit 外链」,一条「外链」建议保留,注明「不含 Reddit 外链」)。"""
    text = (text or "").lower()
    tags = [str(t).lower() for t in tags or [] if str(t).strip()]
    notes = []
    for d in deny or []:
        e = d if isinstance(d, dict) and "terms" in d else _norm_entry(d, "inline")
        if not e:
            continue
        il = e["item"].lower()
        if il in tags or il in text or any(t in tags or _term_hit(t, text) for t in e["terms"]):
            return ("drop", e["item"])
        if any(t in il for t in tags if len(t) >= 2):
            notes.append(e["item"])
    return ("note", notes) if notes else None


def apply_deny(items, deny, text_of, tags_of=None):
    """→ (保留的, 去掉的)。保留的里沾边的加 deny_notes;去掉的每条是 {"item": 原条目, "denied_by": 禁用项}。"""
    kept, dropped = [], []
    for it in items or []:
        m = deny_match(text_of(it), tags_of(it) if tags_of else [], deny)
        if m and m[0] == "drop":
            dropped.append({"item": it, "denied_by": m[1]})
            continue
        if m and isinstance(it, dict):
            it = dict(it, deny_notes=m[1])
        kept.append(it)
    return kept, dropped


def filter_for(ws_hint, items, text_of, tags_of=None, explicit_ws=None):
    """脚本用的一行版:找工作区、读禁用清单、过滤。→ (保留的, 去掉的, 禁用清单)。没有工作区时原样返回。"""
    ws = find_ws(ws_hint, explicit_ws)
    deny = load_deny(ws) if ws else []
    if not deny:
        return list(items or []), [], []
    kept, dropped = apply_deny(items, deny, text_of, tags_of)
    return kept, dropped, deny


def deny_report(dropped, what="建议"):
    if not dropped:
        return ""
    by = {}
    for d in dropped:
        by[d["denied_by"]] = by.get(d["denied_by"], 0) + 1
    return "按禁用清单去掉 %d 条%s(%s)" % (len(dropped), what, "、".join("%s %d" % kv for kv in by.items()))


def add_deny(ws, item, terms, quote, rule_id=None):
    path = pb_dir(ws, "deny.json")
    data = read_json(path, {}) or {}
    data.setdefault("schema", SCHEMA)
    lst = data.setdefault("deny", [])
    for d in lst:
        if str(d.get("item", "")).lower() == item.lower() and not d.get("removed"):
            d["terms"] = sorted(set(d.get("terms") or []) | {t.lower() for t in terms})
            write_json(path, data)
            return d
    e = {"item": item, "terms": sorted({t.lower() for t in terms}), "quote": quote, "at": now(),
         "source": "teach", "rule": rule_id}
    lst.append(e)
    write_json(path, data)
    return e


# ---------------------------------------------------------------------------
# 规则(rules.md)
# ---------------------------------------------------------------------------

RULES_HEAD = ("# seo-ops 规则(用户原话)\n\n"
              "<!-- teach.py 维护:每条规则一个「## R<编号>」小节。可以手改文字;「不做 X」类规则同时写进 deny.json,"
              "推荐代码按它过滤。升级 seo-suite 不会动这个文件。 -->\n")
RULE_RE = re.compile(r"^## (R\d+)\b.*$", re.M)


def rules_path(ws):
    return pb_dir(ws, "rules.md")


def read_rules(ws):
    try:
        with open(rules_path(ws), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def parse_rules(text):
    """→ [{"id", "head", "body", "removed"}]。"""
    out = []
    ms = list(RULE_RE.finditer(text or ""))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        body = text[m.end():end].strip("\n")
        out.append({"id": m.group(1), "head": m.group(0)[3:].strip(), "body": body,
                    "removed": "- 状态:已撤销" in body})
    return out


SCOPE_WORDS = {"plan": ("plan", "方案", "路线"), "brief": ("brief",), "weekly": ("weekly", "每周运营单", "运营单"),
               "outreach": ("outreach", "外联")}


def rules_for(ws, scope, include_deny=False):
    """适用范围含 scope(plan / brief / weekly / outreach)、没撤销的规则 → [{"id","quote","applies"}]。
    「适用」写的是默认的「所有建议…」或没写,算全部适用。include_deny=False 时不含「不做 X」类
    (那类已经由禁用清单逐条过滤)。规则只有原话,没有结构化的触发条件,所以不逐条匹配建议。"""
    out = []
    words = SCOPE_WORDS.get(scope, (scope,))
    for r in parse_rules(read_rules(ws)) if ws else []:
        if r["removed"]:
            continue
        body = r["body"]
        m = re.search(r"^- 适用:(.*)$", body, re.M)
        applies = m.group(1).strip() if m else ""
        everywhere = not applies or applies.startswith("所有")
        if not everywhere and not any(w in applies.lower() for w in words):
            continue
        deny = re.search(r"^- 禁用:(.*)$", body, re.M)
        if not include_deny and deny and not deny.group(1).strip().startswith("无"):
            continue
        q = re.search(r"^- 原话:「(.*)」", body, re.M)
        out.append({"id": r["id"], "quote": q.group(1) if q else r["head"],
                    "applies": "全部" if everywhere else applies})
    return out


def next_rule_id(text):
    ids = [int(r["id"][1:]) for r in parse_rules(text)]
    return "R%d" % (max(ids) + 1 if ids else 1)


def append_rule(ws, quote, applies, deny_items):
    text = read_rules(ws) or RULES_HEAD
    rid = next_rule_id(text)
    lines = ["", "## %s · %s" % (rid, today()), "- 原话:「%s」(%s)" % (quote.strip(), today()),
             "- 适用:%s" % ("、".join(applies) if applies else "所有建议、brief、方案和每周运营单")]
    if deny_items:
        lines.append("- 禁用:%s(结构化,见 deny.json;推荐代码直接过滤)" % "、".join(
            "%s → %s" % (d["item"], "/".join(d["terms"])) for d in deny_items))
    else:
        lines.append("- 禁用:无")
    new = text.rstrip("\n") + "\n" + "\n".join(lines) + "\n"
    os.makedirs(pb_dir(ws), exist_ok=True)
    tmp = rules_path(ws) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(new)
    os.replace(tmp, rules_path(ws))
    return rid


def remove_rule(ws, rid, quote):
    text = read_rules(ws)
    rules = {r["id"]: r for r in parse_rules(text)}
    if rid not in rules:
        raise PlaybookError("没有规则 %s(有:%s)" % (rid, "、".join(rules) or "无"))
    m = re.search(r"^## %s\b.*$" % re.escape(rid), text, re.M)
    nxt = RULE_RE.search(text, m.end())
    end = nxt.start() if nxt else len(text)
    block = text[m.start():end].rstrip("\n") + "\n- 状态:已撤销 %s,原话:「%s」\n" % (today(), quote.strip())
    new = text[:m.start()] + block + ("\n" if nxt else "") + text[end:].lstrip("\n")
    with open(rules_path(ws), "w", encoding="utf-8") as f:
        f.write(new)
    data = read_json(pb_dir(ws, "deny.json"), {}) or {}
    n = 0
    for d in data.get("deny") or []:
        if d.get("rule") == rid and not d.get("removed"):
            d["removed"] = now()
            n += 1
    if n:
        write_json(pb_dir(ws, "deny.json"), data)
    return n


def looks_negative(quote):
    return bool(NEG_RE.search(quote or ""))


# ---------------------------------------------------------------------------
# 用户检查
# ---------------------------------------------------------------------------

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def check_paths(ws, name):
    if not NAME_RE.match(name or ""):
        raise PlaybookError("检查名只能用小写字母、数字、- 和 _:%r" % name)
    return pb_dir(ws, "checks", name + ".py"), pb_dir(ws, "checks", name + ".md")


REG_CORRUPT_STATE = "unreadable"


def registry_problem(ws):
    """registry.json 存在但读不了(不是合法 JSON、顶层不是对象、checks 不是对象)→ 一句原因(带行号);
    文件不存在或读得了 → None。"""
    path = pb_dir(ws, "checks", "registry.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except ValueError as e:
        return "第 %s 行:%s" % (getattr(e, "lineno", "?"), getattr(e, "msg", str(e)))
    except OSError as e:
        return "打不开:%s" % e
    if not isinstance(data, dict):
        return "顶层不是对象"
    if not isinstance(data.get("checks", {}), dict):
        return "checks 不是对象"
    return None


def registry(ws):
    """→ {"schema", "checks": {...}}。文件不存在 = 空表;存在但读不了 → 空表外加 "unreadable"(原因),
    这时所有检查按「已停用、等用户重新确认」处理(check_state 给 unreadable),写入一律拒绝(save_registry)。"""
    bad = registry_problem(ws)
    data = {} if bad else (read_json(pb_dir(ws, "checks", "registry.json"), {}) or {})
    data.setdefault("schema", SCHEMA)
    data.setdefault("checks", {})
    if bad:
        data["unreadable"] = bad
    return data


def reconfirm_hint(name=None):
    n = name or "<名>"
    return ("重新确认:teach.py check try %s --url … ×3 把结果给用户看,用户说可以再 "
            "teach.py check enable %s --quote \"<原话>\"" % (n, n))


def unreadable_message(ws, name=None):
    return ("checks/registry.json 读不了(%s):启用记录和启用时的校验值都读不到,所有自定义检查按已停用处理,"
            "等用户重新确认。%s" % (registry_problem(ws) or "已修好", reconfirm_hint(name)))


def save_registry(ws, data, recover=False):
    """写 registry.json。磁盘上的那份读不了时拒写(不把它覆盖成空表);recover=True(重新确认的 try)
    先把读不了的原文件原样改名留下(registry.json.unreadable-<时间>),新表里记下当时有哪些检查要重新确认。"""
    path = pb_dir(ws, "checks", "registry.json")
    bad = registry_problem(ws)
    if bad and not recover:
        raise GateError(unreadable_message(ws) + ";这次什么都没写")
    data = {k: v for k, v in data.items() if k != "unreadable"}
    if bad:
        keep = "%s.unreadable-%s" % (path, now().replace(":", ""))
        os.replace(path, keep)
        d = pb_dir(ws, "checks")
        names = sorted(f[:-3] for f in os.listdir(d) if f.endswith(".py") and NAME_RE.match(f[:-3]))
        data["recovered"] = {"at": now(), "why": bad, "kept_as": os.path.basename(keep), "reconfirm": names}
    write_json(path, data)


def check_state(ws, name, reg=None):
    """→ {"name", "state", "sha256", ...}。state:missing / draft / tried / enabled / changed / disabled / unreadable。
    changed = 启用后脚本内容变了 → 自动停用,等用户再确认。unreadable = registry.json 读不了(或读不了之后
    还没重新确认)→ 一样按停用处理。"""
    reg = reg or registry(ws)
    script, _ = check_paths(ws, name)
    ent = reg["checks"].get(name) or {}
    if not os.path.isfile(script):
        return {"name": name, "state": "missing", "entry": ent}
    sha = sha256_file(script)
    en = ent.get("enabled")
    if reg.get("unreadable"):
        return {"name": name, "state": REG_CORRUPT_STATE, "sha256": sha, "entry": ent, "why": reg["unreadable"]}
    rec = reg.get("recovered") or {}
    if name in (rec.get("reconfirm") or []) and not (en and en.get("at", "") >= rec.get("at", "")):
        return {"name": name, "state": REG_CORRUPT_STATE, "sha256": sha, "entry": ent,
                "why": "%s;原文件留在 checks/%s,这个检查还没重新启用" % (rec.get("why"), rec.get("kept_as"))}
    if en:
        st = "enabled" if en.get("sha256") == sha else "changed"
    elif ent.get("disabled"):
        st = "disabled"
    elif ent.get("tries"):
        st = "tried"
    else:
        st = "draft"
    return {"name": name, "state": st, "sha256": sha, "entry": ent}


def list_checks(ws):
    names = set(registry(ws)["checks"])
    d = pb_dir(ws, "checks")
    if os.path.isdir(d):
        names |= {f[:-3] for f in os.listdir(d) if f.endswith(".py") and NAME_RE.match(f[:-3])}
    reg = registry(ws)
    return [check_state(ws, n, reg) for n in sorted(names)]


def fetch_page(url, allow_local=False, timeout=15):
    """→ {"url", "final_url", "status", "html"}。走 site_crawl 的抓取(只 http(s)、拒私网、逐跳复查重定向)。"""
    sys.path.insert(0, HERE)
    import site_crawl as SC  # noqa: E402
    SC.ALLOW_LOCAL = bool(allow_local)
    try:
        r = SC.robust_fetch(url, timeout=timeout)
    except Exception as e:  # noqa: BLE001 — 抓取失败当结果记下
        return {"url": url, "final_url": url, "status": None, "html": "", "error": str(e)[:300]}
    return {"url": url, "final_url": r.get("final_url") or url, "status": r.get("status"),
            "html": (r.get("body") or "")[:HTML_MAX]}


def run_check(script, page, timeout=CHECK_TIMEOUT):
    """在子进程里跑用户检查:stdin 给 {"url","final_url","status","html"},不带环境变量、cwd 是空临时目录。
    脚本 stdout 要么是 JSON {"pass": bool, "findings": [...]},要么是纯文本(退出码 0 = 过)。输出只当数据。"""
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8", "PYTHONIOENCODING": "utf-8"}
    payload = json.dumps({k: page.get(k) for k in ("url", "final_url", "status", "html")}, ensure_ascii=False)
    with tempfile.TemporaryDirectory(prefix="seo-check-") as tmp:
        try:
            p = subprocess.run([sys.executable or "python3", "-I", os.path.abspath(script)], input=payload,
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=timeout, cwd=tmp, env=env)
        except subprocess.TimeoutExpired:
            return {"url": page.get("url"), "result": "error", "findings": [], "error": "超时(%d 秒)" % timeout}
        except OSError as e:
            return {"url": page.get("url"), "result": "error", "findings": [], "error": str(e)[:200]}
    out = (p.stdout or "")[:CHECK_OUT_MAX]
    res = {"url": page.get("url"), "findings": []}
    try:
        data = json.loads(out)
    except ValueError:
        data = None
    if isinstance(data, dict) and "pass" in data:
        res["result"] = "pass" if data.get("pass") is True else "fail"
        for f in (data.get("findings") or [])[:50]:
            res["findings"].append(str(f.get("message") if isinstance(f, dict) else f)[:300])
    elif p.returncode in (0, 1):
        res["result"] = "pass" if p.returncode == 0 else "fail"
        res["findings"] = [ln[:300] for ln in out.splitlines() if ln.strip()][:20]
    else:
        res["result"] = "error"
        res["error"] = ("退出码 %s:%s" % (p.returncode, (p.stderr or out)[-300:])).strip()
    if page.get("error"):
        res.update({"result": "error", "error": "抓取失败:%s" % page["error"]})
    return res


def run_enabled(ws, urls, fetch=None, allow_local=False, sample=10):
    """每周运营单用:跑所有已启用(sha 对得上)的检查。→ {"ran": [...], "changed": [...], "skipped": [...]}。
    每个检查只在 registry 里 match(正则)命中的 URL 上跑,最多 sample 个;没写 match 就用前 sample 个。"""
    fetch = fetch or (lambda u: fetch_page(u, allow_local))
    out = {"ran": [], "changed": [], "skipped": [], "unreadable": []}
    cache = {}
    for st in list_checks(ws):
        if st["state"] == REG_CORRUPT_STATE:
            out["unreadable"].append({"name": st["name"], "why": st.get("why")})
            continue
        if st["state"] == "changed":
            out["changed"].append({"name": st["name"], "enabled_sha": st["entry"]["enabled"]["sha256"][:12],
                                   "now_sha": st["sha256"][:12]})
            continue
        if st["state"] != "enabled":
            continue
        ent = st["entry"]
        rx = ent.get("match")
        pick = [u for u in urls if not rx or re.search(rx, u)][: int(ent.get("sample") or sample)]
        if not pick:
            out["skipped"].append({"name": st["name"], "why": "本周没有匹配 %s 的页面" % (rx or "任何")})
            continue
        script, _ = check_paths(ws, st["name"])
        rows = []
        for u in pick:
            if u not in cache:
                cache[u] = fetch(u)
            rows.append(run_check(script, cache[u], int(ent.get("timeout") or CHECK_TIMEOUT)))
        out["ran"].append({"name": st["name"], "desc": ent.get("desc", ""), "results": rows,
                           "pass": sum(r["result"] == "pass" for r in rows),
                           "fail": sum(r["result"] == "fail" for r in rows),
                           "error": sum(r["result"] == "error" for r in rows)})
    return out


# ---------------------------------------------------------------------------
# 数据源登记(sources.json)
# ---------------------------------------------------------------------------

def load_sources(ws):
    """→ (合法的源[免费在前、付费在后], 问题列表)。格式见 references/overview/playbook.md 第五节。"""
    data = read_json(pb_dir(ws, "sources.json"), {}) if ws else {}
    good, bad = [], []
    for i, s in enumerate((data or {}).get("sources") or []):
        why = validate_source(s)
        if why:
            bad.append("第 %d 个源 %s:%s" % (i + 1, (s or {}).get("name", "?") if isinstance(s, dict) else "?", why))
            continue
        good.append(dict(s, _order=i))
    good.sort(key=lambda s: (bool(s.get("paid")), float(s.get("cost_per_call_usd") or 0), s["_order"]))
    return good, bad


def validate_source(s):
    if not isinstance(s, dict):
        return "不是对象"
    if not NAME_RE.match(str(s.get("name") or "")):
        return "name 只能用小写字母、数字、- 和 _"
    prov = s.get("provides")
    if not isinstance(prov, list) or not prov or any(p not in PROVIDES for p in prov):
        return "provides 要是列表,取值 %s" % "/".join(PROVIDES)
    kind = s.get("kind")
    if kind == "command":
        if not isinstance(s.get("command"), list) or not s["command"] or not all(isinstance(x, str) for x in s["command"]):
            return "command 要是字符串列表(不经 shell)"
    elif kind == "http":
        u = str(s.get("url") or "")
        if not u.startswith(("https://", "http://")):
            return "url 要以 http(s):// 开头"
    else:
        return "kind 只能是 command 或 http"
    if not isinstance(s.get("paid"), bool):
        return "paid 必须写 true 或 false"
    if s["paid"] and not isinstance(s.get("cost_per_call_usd"), (int, float)):
        return "付费源要写 cost_per_call_usd(单次成本,美元)"
    return None


def pick_source(ws, provides, allow_paid=()):
    """→ (源, 没选上的原因列表)。免费的按登记顺序先用;付费的只有名字在 allow_paid 里才用。"""
    srcs, bad = load_sources(ws)
    why = list(bad)
    for s in srcs:
        if provides not in s["provides"]:
            continue
        if s["paid"] and s["name"] not in set(allow_paid or ()):
            why.append("%s 是付费源(单次 $%s),命令里没用 --allow-paid %s,不用" % (
                s["name"], s.get("cost_per_call_usd"), s["name"]))
            continue
        return s, why
    return None, why


def _subst(text, params, quote=False):
    def rep(m):
        v = str(params.get(m.group(1), ""))
        return urllib.parse.quote(v) if quote else v
    return re.sub(r"\{(\w+)\}", rep, text)


def call_source(src, params, timeout=None):
    """调一次登记的源,→ 解析好的 JSON。command 不经 shell;http 只 GET,头里的 ${ENV} 从环境变量取。"""
    timeout = int(src.get("timeout") or timeout or SOURCE_TIMEOUT)
    if src["kind"] == "command":
        argv = [_subst(a, params) for a in src["command"]]
        p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        if p.returncode != 0:
            raise PlaybookError("源 %s 退出码 %s:%s" % (src["name"], p.returncode, (p.stderr or "")[-200:]))
        body = p.stdout
    else:
        url = _subst(src["url"], params, quote=True)
        headers = {"User-Agent": "seo-suite-sources/1.0", "Accept": "application/json"}
        for k, v in (src.get("headers") or {}).items():
            headers[k] = re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), ""), str(v))
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(5_000_000).decode("utf-8", "replace")
    try:
        return json.loads(body)
    except ValueError:
        raise PlaybookError("源 %s 的输出不是 JSON(约定:stdout / 响应体是一个 JSON)" % src["name"])


def volume_from(data, keyword):
    """keyword_volume 源的两种输出:{"volume": N} 或 {"results": [{"keyword", "volume"}]}。"""
    if isinstance(data, dict) and isinstance(data.get("volume"), (int, float)):
        return int(data["volume"])
    rows = data.get("results") if isinstance(data, dict) else data if isinstance(data, list) else None
    for r in rows or []:
        if isinstance(r, dict) and str(r.get("keyword", "")).strip().lower() == keyword.strip().lower() \
                and isinstance(r.get("volume"), (int, float)):
            return int(r["volume"])
    return None


# ---------------------------------------------------------------------------
# 注入的上下文(钩子 / 其他宿主)
# ---------------------------------------------------------------------------

def context_text(ws):
    """→ 一段给 agent 看的上下文;没有规则也没有禁用清单时返回 ""。"""
    if not ws:
        return ""
    rules = [r for r in parse_rules(read_rules(ws)) if not r["removed"]]
    deny = load_deny(ws)
    checks = list_checks(ws) if os.path.isdir(pb_dir(ws, "checks")) else []
    if not rules and not deny and not any(c["state"] == REG_CORRUPT_STATE for c in checks):
        return ""
    L = ["seo-suite:这个仓库有用户自己定的 SEO 规则(%s)。出任何建议、brief、方案、外联候选前先遵守它们;"
         "「不做」的事不要再建议,沾边的写明不含它。" % pb_dir(ws, "rules.md")]
    for r in rules:
        quote = re.search(r"- 原话:「(.*)」", r["body"])
        L.append("- %s:%s" % (r["id"], quote.group(1) if quote else r["body"].splitlines()[0] if r["body"] else r["head"]))
    if deny:
        L.append("禁用清单(推荐脚本会按关键词直接过滤):" + ";".join(
            "%s(%s)" % (d["item"], "/".join(d["terms"])) for d in deny))
    en = [c["name"] for c in checks if c["state"] == "enabled"]
    ch = [c["name"] for c in checks if c["state"] == "changed"]
    bad = [c for c in checks if c["state"] == REG_CORRUPT_STATE]
    if bad:
        L.append("已停用:registry.json 读不了,等用户重新确认的检查:%s(%s;%s)" % (
            "、".join(c["name"] for c in bad), bad[0].get("why"), reconfirm_hint()))
    if en:
        L.append("已启用的自定义检查(每周运营单会跑):" + "、".join(en))
    if ch:
        L.append("脚本改过、已自动停用、等用户再确认的检查:" + "、".join(ch) + "(teach.py check try 再 enable)")
    if rules:
        L.append("规则要求产出必须有的元素(表格、清单、某一节):brief 和大纲阶段就画出来——表格写好表头和行名,"
                 "数还没有就留空格;不能只写一句「第 N 节放某某表」。")
    L.append("改规则用 teach.py(rule add / rule remove),不要手改 deny.json。")
    text = "\n".join(L)
    return text[:CONTEXT_MAX]


def cmd_hook():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    try:
        cwd = (event or {}).get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        text = context_text(find_ws(cwd))
    except Exception:  # noqa: BLE001 — 钩子出错不卡住会话
        return 0
    if text:
        name = (event or {}).get("hook_event_name") or "SessionStart"
        print(json.dumps({"hookSpecificOutput": {"hookEventName": name, "additionalContext": text}},
                         ensure_ascii=False))
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    if argv[0] == "hook":
        return cmd_hook()
    if argv[0] == "skill-dir":
        print(resolve_skill_dir())
        return 0
    if argv[0] == "context":
        explicit = argv[argv.index("--ws") + 1] if "--ws" in argv and argv.index("--ws") + 1 < len(argv) else None
        text = context_text(find_ws(None, explicit))
        print(text or "(这个仓库没有 seo-ops/playbook 规则或禁用清单)")
        return 0
    sys.stderr.write("未知子命令 %s(hook / context / skill-dir)\n" % argv[0])
    return 2


if __name__ == "__main__":
    sys.exit(main())
