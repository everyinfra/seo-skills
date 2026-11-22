#!/usr/bin/env python3
"""grade_hosts.py — hosts_static.json(Claude Code 以外 4 个宿主)的静态检查。不调模型、不联网。

  grade.py hosts --skill-dir DIR --plugin-root ROOT [--readme FILE ...] [--label L] [--out FILE] [--hosts-file F]

每个宿主先跑 common 8 条,再跑自己的条目;must 不过 → fail,should 不过 → warn;没有对应文件的可选项 → n/a。
输出 {"type":"hosts_static","hosts":{宿主:{"verdict","checks":{id:{"result","level","evidence"}}}}}。读法见 grade.py R61。
"""
import argparse
import json
import os
import re

try:
    import tomllib
except ImportError:  # pragma: no cover
    tomllib = None

import grade as G

HOSTS_FILE = os.path.join(G.HERE, "hosts_static.json")
ENTRIES = ("start", "lifecycle", "weekly", "launch", "site-move", "teach", "report")
HOST_HEAD = {"codex": r"codex", "cursor": r"cursor", "gemini_cli": r"gemini", "vscode_copilot": r"vs\s?code|copilot"}
SCRIPT_EXT = (".py", ".sh", ".mjs", ".js", ".ts", ".cjs", ".bash")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def read(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def frontmatter(text):
    """SKILL.md 开头 --- … --- 之间的简单 YAML:顶层 key: value,认引号和 > | 块。"""
    lines = (text or "").splitlines()
    if not lines or lines[0].strip() != "---":
        return None, 0
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None, 0
    fm, i = {}, 1
    while i < end:
        ln = lines[i]
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", ln)
        if not m:
            i += 1
            continue
        k, v = m.group(1), m.group(2).strip()
        if v in (">", "|", ">-", "|-", ">+", "|+"):
            buf = []
            i += 1
            while i < end and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                buf.append(lines[i].strip())
                i += 1
            fm[k] = (" " if v.startswith(">") else "\n").join(x for x in buf).strip()
            continue
        if v == "":
            sub = {}
            i += 1
            while i < end and lines[i].startswith((" ", "\t")):
                mm = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*)$", lines[i])
                if mm:
                    sub[mm.group(1)] = _scalar(mm.group(2))
                i += 1
            fm[k] = sub
            continue
        fm[k] = _scalar(v)
        i += 1
    return fm, end + 1


def _scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        return v[1:-1]
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    return v


def sections(texts, pat):
    out = []
    for name, t in texts:
        lines = (t or "").splitlines()
        i = 0
        while i < len(lines):
            m = re.match(r"^(#{1,6})\s+(.*)$", lines[i])
            if m and re.search(pat, m.group(2), re.I):
                lvl = len(m.group(1))
                j = i + 1
                while j < len(lines):
                    mm = re.match(r"^(#{1,6})\s+", lines[j])
                    if mm and len(mm.group(1)) <= lvl:
                        break
                    j += 1
                out.append((name, i + 1, "\n".join(lines[i:j])))
                i = j
                continue
            i += 1
    return out


def scripts_in(d):
    out = []
    for root, dirs, fs in os.walk(d):
        dirs[:] = [x for x in dirs if x not in (".git", "__pycache__", "node_modules", "tests")]
        for f in sorted(fs):
            if f.endswith(SCRIPT_EXT):
                out.append(os.path.join(root, f))
    return out


class Pkg:
    def __init__(self, skill_dir, root, readmes):
        self.skill = os.path.abspath(skill_dir)
        self.root = os.path.abspath(root)
        self.skill_md_path = os.path.join(self.skill, "SKILL.md")
        self.skill_md = read(self.skill_md_path) or ""
        self.fm, self.body_start = frontmatter(self.skill_md)
        rs = readmes or [p for p in (os.path.join(self.root, x) for x in ("README.md", "HOSTS.md", "README.zh-CN.md"))
                         if os.path.isfile(p)]
        self.readmes = [(os.path.relpath(p, self.root), read(p) or "") for p in rs]
        self.scripts = scripts_in(self.skill)

    def rel(self, p):
        return os.path.relpath(p, self.root)

    def host_sections(self, host):
        return sections(self.readmes, HOST_HEAD[host])

    def host_text(self, host):
        return "\n".join(t for _, _, t in self.host_sections(host))

    def onboarding_docs(self):
        out = [(self.rel(self.skill_md_path), self.skill_md)]
        for root, dirs, fs in os.walk(self.skill):
            for f in sorted(fs):
                if f.endswith(".md") and "onboard" in f.lower():
                    p = os.path.join(root, f)
                    out.append((self.rel(p), read(p) or ""))
        return out


def res(result, evidence, level="must"):
    return {"result": result, "level": level, "evidence": evidence}


def pf(ok, evidence, level="must"):
    return res("pass" if ok else ("fail" if level == "must" else "warn"), evidence, level)


def _grep(pkg, pats, files=None):
    hits_ = []
    for p in files if files is not None else pkg.scripts:
        for n, ln in enumerate((read(p) or "").splitlines(), 1):
            if any(re.search(x, ln) for x in pats):
                hits_.append("%s:%d %s" % (pkg.rel(p), n, ln.strip()[:120]))
    return hits_


# ---- common ----

def s1(pkg):
    fm = pkg.fm or {}
    name = fm.get("name")
    d = os.path.basename(pkg.skill.rstrip("/"))
    ok = isinstance(name, str) and 1 <= len(name) <= 64 and bool(NAME_RE.match(name)) and name == d
    return pf(ok, {"file": pkg.rel(pkg.skill_md_path), "name": name, "dir": d, "frontmatter": pkg.fm is not None})


def s2(pkg):
    d = (pkg.fm or {}).get("description")
    n = len(d) if isinstance(d, str) else 0
    return pf(isinstance(d, str) and 1 <= n <= 1024, {"chars": n})


def s3(pkg, spec):
    d = str((pkg.fm or {}).get("description") or "")
    kws = spec.get("keywords") or []
    got = [k for k in kws if re.search(k, d, re.I)]
    front = bool(re.search("seo", d[:100], re.I))
    return pf(front and len(got) >= 6, {"seo_in_first_100": front, "keywords_hit": got, "need": 6})


def s4(pkg):
    lines = pkg.skill_md.splitlines()
    body = "\n".join(lines[pkg.body_start:])
    refs = sorted(set(re.findall(r"\]\(([^)#\s]+)\)", body) + re.findall(r"`((?:references|scripts|data|templates|"
                                                                          r"examples)/[^`\s]+)`", body)))
    refs = [r for r in refs if not re.match(r"https?://|mailto:", r)]
    bad = [r for r in refs if r.startswith(("/", "~")) or r.count("/") > 1]
    chain = []
    for r in refs:
        p = os.path.join(pkg.skill, r)
        if r.endswith(".md") and os.path.isfile(p):
            inner = re.findall(r"\]\(((?!https?://)[^)#\s]+\.md)\)", read(p) or "")
            if inner:
                chain.append(r)
    ok = len(lines) <= 500 and not bad and not chain
    return pf(ok, {"lines": len(lines), "refs": len(refs), "not_one_level": bad[:10], "refs_that_reference_more": chain[:10]},
              "should")


def s5(pkg):
    pats = [r"~/\.claude", r"\$HOME/\.claude", r"expanduser\(\s*['\"]~/\.claude", r"Path\.home\(\)\s*/\s*['\"]\.claude"]
    h = _grep(pkg, pats)
    return pf(not h, {"hits": h[:10], "scripts_scanned": len(pkg.scripts)})


def s6(pkg):
    """R61:静态启发式。记下由 __file__ / $0 / import.meta.url 推出来的变量,写操作那一行用到它们 → 判失败。"""
    sus = []
    for p in pkg.scripts:
        t = read(p) or ""
        names = set()
        for _ in range(3):
            for m in re.finditer(r"(?m)^\s*([A-Za-z_]\w*)\s*=\s*(.+)$", t):
                rhs = m.group(2)
                if "__file__" in rhs or "import.meta.url" in rhs or re.search(r"\$\(dirname\s+\"?\$0|BASH_SOURCE", rhs) \
                        or any(re.search(r"\b%s\b" % re.escape(n), rhs) for n in names):
                    names.add(m.group(1))
        for n, ln in enumerate(t.splitlines(), 1):
            if re.search(r"open\(.*?,\s*(?:mode\s*=\s*)?['\"][wax][bt+]?['\"]|write_text\(|write_bytes\(|mkdir|makedirs|>>?|\btee\b|"
                         r"writeFileSync|appendFileSync|mkdirSync", ln):
                if "__file__" in ln or any(re.search(r"\b%s\b" % re.escape(x), ln) for x in names):
                    if re.search(r"^\s*(#|//)", ln):
                        continue
                    sus.append("%s:%d %s" % (pkg.rel(p), n, ln.strip()[:120]))
    return pf(not sus, {"writes_near_skill_dir": sus[:10], "scripts_scanned": len(pkg.scripts),
                        "method": "静态启发式(R61)"})


def s7(pkg):
    found = []
    for name, t in pkg.onboarding_docs():
        for _, ln, sec in sections([(name, t)], r".") or [(name, 1, t)]:
            for para in re.split(r"\n\s*\n", sec):
                if (re.search(r"没有提问工具|无提问工具|没有\s*AskUserQuestion|no (AskUserQuestion|question tool)|"
                              r"without (an? |the )?(AskUserQuestion|question tool)", para, re.I)
                        and re.search(r"编号|numbered", para, re.I) and re.search(r"选项|猜测|option|guess", para, re.I)
                        and re.search(r"结束(这一)?回合|等(用户)?回话|end (the |your )?turn|wait for", para, re.I)):
                    found.append({"file": name, "section_line": ln, "para": para.strip()[:200]})
    cc = any(re.search(r"Claude Code", f["para"]) and "AskUserQuestion" in f["para"] for f in found) or any(
        re.search(r"Claude Code[^\n]{0,80}AskUserQuestion|AskUserQuestion[^\n]{0,80}Claude Code", t)
        for _, t in pkg.onboarding_docs())
    return pf(bool(found) and cc, {"paragraphs": found[:3], "claude_code_only_mentioned": cc})


ROUTE_WORDS = re.compile(r"说|讲|输入|say|type|ask|→|->|进|route|use|用|触发|trigger", re.I)


def entry_routes(pkg, host):
    texts = [(pkg.rel(pkg.skill_md_path), pkg.skill_md)] + [(n, t) for n, ln, t in
                                                            [(a, b, c) for a, b, c in pkg.host_sections(host)]]
    out = {}
    skills_dir = os.path.join(pkg.root, "skills")
    for e in ENTRIES:
        ev = None
        sd = os.path.join(skills_dir, "seo-suite-%s" % e)
        if os.path.isfile(os.path.join(sd, "SKILL.md")):
            ev = "独立 skill " + pkg.rel(sd)
        if not ev and host == "gemini_cli":
            for base in (os.path.join(pkg.root, "commands", "seo-suite"), os.path.join(pkg.root, ".gemini", "commands",
                                                                                       "seo-suite")):
                p = os.path.join(base, e + ".toml")
                if os.path.isfile(p):
                    ev = "命令文件 " + pkg.rel(p)
        if not ev:
            for name, t in texts:
                for n, ln in enumerate((t or "").splitlines(), 1):
                    if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(e), ln) and ROUTE_WORDS.search(ln):
                        ev = "%s:%d %s" % (name, n, ln.strip()[:100])
                        break
                if ev:
                    break
        out[e] = ev
    return out


def s8(pkg, host):
    r = entry_routes(pkg, host)
    return pf(all(r.values()), {"entries": r})


# ---- 各宿主 ----

def _install(pkg, host, locs, forbid=()):
    txt = pkg.host_text(host)
    if not txt:
        return False, {"why": "README / HOSTS.md 里没有这个宿主的安装段"}
    got = [l for l in locs if l in txt]
    bad = [f for f in forbid if f in txt]
    return bool(got) and not bad, {"section": [(n, ln) for n, ln, _ in pkg.host_sections(host)], "locations_found": got,
                                   "forbidden_found": bad}


def cx1(pkg):
    ok, ev = _install(pkg, "codex", (".agents/skills", "/etc/codex/skills", "plugin.json"), ("~/.codex/skills",))
    return pf(ok, ev)


def cx2(pkg):
    p = os.path.join(pkg.skill, "agents", "openai.yaml")
    t = read(p)
    if t is None:
        return res("pass", {"file": None, "why": "没有 agents/openai.yaml"}, "should")
    bad = re.search(r"(?m)^\s*allow_implicit_invocation\s*:\s*false\b", t)
    parsable = not re.search(r"\t", t)
    return pf(parsable and not bad, {"file": pkg.rel(p), "allow_implicit_invocation_false": bool(bad), "parsable": parsable},
              "should")


def _files(root, pat, top=None):
    out = []
    for r, dirs, fs in os.walk(root):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules")]
        for f in fs:
            p = os.path.join(r, f)
            if re.search(pat, os.path.relpath(p, root).replace(os.sep, "/")):
                out.append(p)
    return sorted(out)


def cx3(pkg):
    prompts = _files(pkg.root, r"(^|/)(\.codex/)?prompts/[^/]+\.md$")
    routes = entry_routes(pkg, "codex")
    ev = {"entries_routed": sum(1 for v in routes.values() if v), "prompt_files": [pkg.rel(p) for p in prompts]}
    ok = all(routes.values())
    if prompts:
        nested = [pkg.rel(p) for p in prompts if re.search(r"prompts/.+/", pkg.rel(p))]
        nodesc = [pkg.rel(p) for p in prompts if not (frontmatter(read(p))[0] or {}).get("description")]
        dep = bool(re.search(r"弃用|deprecated", pkg.host_text("codex"), re.I))
        ev.update(nested=nested, no_description=nodesc, readme_says_deprecated=dep)
        ok = ok and not nested and not nodesc and dep
    return pf(ok, ev)


def cx4(pkg):
    cands = [p for p in (os.path.join(pkg.root, "plugin.json"), os.path.join(pkg.root, ".codex-plugin", "plugin.json"))
             if os.path.isfile(p)]
    if not cands:
        return res("n/a", {"why": "不以 Codex 插件分发(没有 plugin.json / .codex-plugin/plugin.json)"}, "should")
    d = G.read_json(cands[0])
    skills = (d or {}).get("skills")
    decl = isinstance(skills, str) and skills.rstrip("/") in ("./skills", "skills") or \
        isinstance(skills, list) and any(str(x).rstrip("/") in ("./skills", "skills") for x in skills)
    has = os.path.isfile(os.path.join(pkg.root, "skills", "seo-suite", "SKILL.md"))
    return pf(d is not None and decl and has, {"file": pkg.rel(cands[0]), "skills": skills, "skill_md_exists": has}, "should")


def cx5(pkg):
    txt = pkg.host_text("codex")
    if "AGENTS.md" not in txt:
        return res("n/a", {"why": "Codex 安装段不靠 AGENTS.md"}, "should")
    i = txt.index("AGENTS.md")
    blocks = re.findall(r"```[^\n]*\n(.*?)```", txt[i:], re.S)
    shipped = _files(pkg.root, r"(^|/)[^/]*AGENTS[^/]*\.(md|txt)$")
    size = len(blocks[0].encode("utf-8")) if blocks else max((os.path.getsize(p) for p in shipped), default=0)
    return pf(0 < size <= 8192, {"bytes": size, "limit": 8192}, "should")


def cu1(pkg):
    ok, ev = _install(pkg, "cursor", (".agents/skills", ".cursor/skills", "~/.agents/skills", "~/.cursor/skills",
                                      ".claude/skills", ".codex/skills"))
    txt = pkg.host_text("cursor")
    warn = bool(re.search(r"~/\.claude/skills", txt) and re.search(r"不要|别|don't|do not|avoid|duplicate|重复|同名", txt, re.I))
    ev["duplicate_warning"] = warn
    return pf(ok and warn, ev)


def cu2(pkg):
    fm = pkg.fm or {}
    bad = fm.get("disable-model-invocation") is True or str(fm.get("disable-model-invocation")).lower() == "true"
    return pf(not bad and "paths" not in fm, {"disable-model-invocation": fm.get("disable-model-invocation"),
                                              "paths": fm.get("paths")})


def cu3(pkg):
    old = _files(pkg.root, r"(^|/)\.cursor/commands/[^/]+\.md$")
    legacy = bool(re.search(r"旧版|老版本|legacy|older version|2\.4", pkg.host_text("cursor"), re.I))
    routes = entry_routes(pkg, "cursor")
    ok = all(routes.values()) and (not old or legacy)
    return pf(ok, {"cursor_command_files": [pkg.rel(p) for p in old], "readme_says_legacy": legacy,
                   "entries_routed": sum(1 for v in routes.values() if v)})


def cu4(pkg):
    t = pkg.host_text("cursor")
    ok = bool(re.search(r"cloud agent", t, re.I) and "~/.cursor/skills" in t and re.search(r"sync", t, re.I))
    return pf(ok, {"mentions_cloud_agents": bool(re.search(r"cloud agent", t, re.I))}, "should")


def gm1(pkg):
    ok, ev = _install(pkg, "gemini_cli", ("~/.gemini/skills", "~/.agents/skills", ".gemini/skills", ".agents/skills",
                                          "gemini skills install", "gemini extensions install"))
    txt = pkg.host_text("gemini_cli")
    for m in re.finditer(r"gemini skills install\s+(\S+)([^\n]*)", txt):
        root_is_skill = os.path.isfile(os.path.join(pkg.root, "SKILL.md"))
        pm = re.search(r"--path\s+[`'\"]?([^\s`'\"]+)", m.group(2))
        good = root_is_skill or (pm and os.path.isfile(os.path.join(pkg.root, pm.group(1).strip("/"), "SKILL.md")))
        ev.setdefault("install_cmds", []).append({"cmd": m.group(0)[:120], "path_ok": bool(good)})
        ok = ok and bool(good)
    return pf(ok, ev)


def toml_files(pkg):
    return _files(pkg.root, r"(^|/)(\.gemini/)?commands/.*\.toml$")


def gm2(pkg):
    fs = toml_files(pkg)
    if not fs:
        return res("n/a", {"why": "没带 Gemini 命令文件(入口靠 skill)"})
    bad = []
    for p in fs:
        try:
            d = tomllib.loads(read(p) or "")
        except Exception as e:  # noqa: BLE001
            bad.append({"file": pkg.rel(p), "why": "TOML 解析失败:%s" % e})
            continue
        pr = d.get("prompt")
        if not isinstance(pr, str) or not pr.strip():
            bad.append({"file": pkg.rel(p), "why": "没有字符串 prompt"})
            continue
        if "description" in d and (not isinstance(d["description"], str) or "\n" in d["description"].strip()):
            bad.append({"file": pkg.rel(p), "why": "description 不是一行"})
        if "!{" in pr:
            bad.append({"file": pkg.rel(p), "why": "prompt 里用了 !{...}"})
        if "$ARGUMENTS" in pr:
            bad.append({"file": pkg.rel(p), "why": "传参用了 $ARGUMENTS,应为 {{args}}"})
    return pf(not bad, {"files": [pkg.rel(p) for p in fs], "bad": bad})


def gm3(pkg):
    fs = toml_files(pkg)
    if not fs:
        return res("n/a", {"why": "没带 Gemini 命令文件"})
    bad = [pkg.rel(p) for p in fs if not re.search(r"commands/seo-suite/[^/]+\.toml$", pkg.rel(p).replace(os.sep, "/"))]
    return pf(not bad, {"files": [pkg.rel(p) for p in fs], "not_under_commands_seo_suite": bad})


def gm4(pkg):
    p = os.path.join(pkg.root, "gemini-extension.json")
    if not os.path.isfile(p):
        return res("n/a", {"why": "不以 Gemini 扩展分发"}, "should")
    d = G.read_json(p) or {}
    name = d.get("name")
    ok = (isinstance(name, str) and bool(NAME_RE.match(name)) and name == os.path.basename(pkg.root.rstrip("/"))
          and bool(d.get("version")) and bool(d.get("description"))
          and os.path.isfile(os.path.join(pkg.root, "skills", "seo-suite", "SKILL.md")))
    return pf(ok, {"file": "gemini-extension.json", "name": name, "dir": os.path.basename(pkg.root.rstrip("/")),
                   "version": d.get("version")}, "should")


def gm5(pkg, s6r):
    t = pkg.host_text("gemini_cli")
    ok = bool(re.search(r"授权|consent|确认|approve|permission", t, re.I)) and s6r["result"] == "pass"
    return pf(ok, {"mentions_consent": bool(re.search(r"授权|consent|确认|approve|permission", t, re.I)),
                   "S6": s6r["result"]}, "should")


def vs1(pkg):
    ok, ev = _install(pkg, "vscode_copilot", (".github/skills/seo-suite", "~/.copilot/skills/seo-suite"))
    return pf(ok, ev)


def vs2(pkg):
    bad = []
    for p in _files(pkg.root, r"(^|/)SKILL\.md$"):
        fm, _ = frontmatter(read(p))
        n = (fm or {}).get("name")
        if not isinstance(n, str) or not NAME_RE.match(n) or re.search(r"[:/.]", n):
            bad.append({"file": pkg.rel(p), "name": n})
    return pf(not bad, {"bad_names": bad[:10]})


def vs3(pkg):
    fm = pkg.fm or {}
    ui, dm = fm.get("user-invocable"), fm.get("disable-model-invocation")
    ok = not (ui is False or str(ui).lower() == "false") and not (dm is True or str(dm).lower() == "true")
    return pf(ok, {"user-invocable": ui, "disable-model-invocation": dm})


def vs4(pkg):
    fs = _files(pkg.root, r"\.prompt\.md$")
    if not fs:
        return res("pass", {"why": "没带提示文件"}, "should")
    bad = [pkg.rel(p) for p in fs if not pkg.rel(p).replace(os.sep, "/").startswith(".github/prompts/")
           or frontmatter(read(p))[0] is None]
    local = bool(re.search(r"Local|弃用|deprecated", pkg.host_text("vscode_copilot")))
    return pf(not bad and local, {"files": [pkg.rel(p) for p in fs], "bad": bad, "readme_says_local_only": local}, "should")


HOST_CHECKS = {"codex": {"CX1_install_path": cx1, "CX2_openai_yaml": cx2, "CX3_commands": cx3, "CX4_plugin_manifest": cx4,
                         "CX5_agents_md_budget": cx5},
               "cursor": {"CU1_install_path": cu1, "CU2_frontmatter_flags": cu2, "CU3_commands": cu3,
                          "CU4_cloud_agents": cu4},
               "gemini_cli": {"GM1_install_path": gm1, "GM2_command_toml": gm2, "GM3_command_namespace": gm3,
                              "GM4_extension_manifest": gm4, "GM5_consent_scope": None},
               "vscode_copilot": {"VS1_install_path": vs1, "VS2_name_no_colon": vs2, "VS3_invocation_flags": vs3,
                                  "VS4_prompt_files": vs4}}


def run_checks(skill_dir, root, readmes=None, hosts_file=None, label=None):
    spec = G.read_json(hosts_file or HOSTS_FILE)
    pkg = Pkg(skill_dir, root, readmes)
    common = {c["id"]: c for c in spec["common"]}
    base = {"S1_frontmatter_name": s1(pkg), "S2_description_length": s2(pkg),
            "S3_description_front_loaded": s3(pkg, common["S3_description_front_loaded"]),
            "S4_skill_body_size": s4(pkg), "S5_no_hardcoded_home": s5(pkg), "S6_state_outside_skill_dir": s6(pkg),
            "S7_stop_without_question_tool": s7(pkg)}
    out = {}
    for host, hs in spec["hosts"].items():
        checks = dict(base)
        checks["S8_command_entries_reachable"] = s8(pkg, host)
        fns = HOST_CHECKS.get(host, {})
        for c in hs["checks"]:
            fn = fns.get(c["id"])
            if c["id"] == "GM5_consent_scope":
                r = gm5(pkg, base["S6_state_outside_skill_dir"])
            elif fn is None:
                r = res("fail", {"why": "判分器不认识这条检查"}, c.get("level", "must"))
            else:
                r = fn(pkg)
            r["level"] = c.get("level", r["level"])
            if r["result"] == "fail" and r["level"] == "should":
                r["result"] = "warn"
            checks[c["id"]] = r
        for cid, c in common.items():
            checks[cid]["level"] = c.get("level", "must")
            if checks[cid]["result"] == "fail" and checks[cid]["level"] == "should":
                checks[cid]["result"] = "warn"
        verdict = "fail" if any(v["result"] == "fail" for v in checks.values()) else "pass"
        out[host] = {"verdict": verdict, "checks": checks}
    return {"type": "hosts_static", "label": label, "skill_dir": pkg.skill, "plugin_root": pkg.root,
            "readmes": [n for n, _ in pkg.readmes], "hosts": out}


def main(argv):
    ap = argparse.ArgumentParser(prog="grade.py hosts")
    ap.add_argument("--skill-dir", required=True)
    ap.add_argument("--plugin-root", required=True)
    ap.add_argument("--readme", action="append", help="安装说明文件(默认插件根的 README.md、HOSTS.md、README.zh-CN.md)")
    ap.add_argument("--hosts-file")
    ap.add_argument("--label")
    ap.add_argument("--out")
    ns = ap.parse_args(argv)
    r = run_checks(ns.skill_dir, ns.plugin_root, ns.readme, ns.hosts_file, ns.label)
    G._emit(r, ns.out)
    return 0
