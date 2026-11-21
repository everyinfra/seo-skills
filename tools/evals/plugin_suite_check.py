#!/usr/bin/env python3
"""插件形态的静态校验(发版门跑;不调模型、不联网,只看文件)。

查四样东西,规则来自 Claude Code 官方文档(plugin-evals、plugins-reference、slash-commands、sub-agents、hooks):
  1. evals/ 评测套件(`claude plugin eval` 用):有 prompt.md 或 case.yaml 的目录才算一个用例;
     prompt.md frontmatter 只许官方字段(多一个键就是错);每个用例至少一个判分器;判分器 type 是六种之一、
     各自要的选项齐;arm 只能是 both / with-only;case.yaml 要 schema_version "1.1" 和 name;
     scaffold_script 指的文件存在;正则判分器能编译;`results/` 在 .gitignore 里。
  2. commands/:7 个命令文件都在,frontmatter 有 description;正文里 `${CLAUDE_PLUGIN_ROOT}/…` 指的文件都在。
  3. agents/:3 个子代理都在,frontmatter 有 name(和文件名一致、不含冒号)和 description,
     不写插件里不生效的键(permissionMode、hooks、mcpServers);禁止再开子代理(disallowedTools 含 Agent 或 tools 里没有 Agent)。
  4. hooks/hooks.json:顶层是 {"hooks": {事件: [...]}},事件名认识,命令里 `${CLAUDE_PLUGIN_ROOT}/…` 指的脚本存在。
退出码:0 全过;1 有不过。也可 `--root 别的目录` 校验别处的插件(单元测试用)。
"""
import argparse
import json
import os
import re
import sys

COMMANDS = ("start", "lifecycle", "weekly", "launch", "site-move", "teach", "report")
AGENTS = ("researcher", "auditor", "red-team")
PROMPT_KEYS = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "model",
               "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env"}
CASE_KEYS = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "context",
             "execution", "graders", "prompt"}
GRADER_REQUIRED = {"regex": ("pattern",), "tool_used": ("tool",), "tool_order": ("before", "after"),
                   "file_exists": ("path",), "llm": (), "baseline": ("baseline_file",)}
ARMS = {"both", "with-only"}
CMD_KEYS = {"description", "argument-hint", "allowed-tools", "model", "disable-model-invocation", "name",
            "when_to_use", "user-invocable", "effort", "context", "agent", "hooks", "paths", "shell", "arguments"}
AGENT_KEYS = {"name", "description", "tools", "disallowedTools", "model", "effort", "maxTurns", "skills", "memory",
              "background", "omitClaudeMd", "isolation", "color", "initialPrompt"}
AGENT_IGNORED = {"permissionMode", "hooks", "mcpServers"}
HOOK_EVENTS = {"SessionStart", "SessionEnd", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PostToolUseFailure",
               "PermissionRequest", "Notification", "Stop", "StopFailure", "SubagentStart", "SubagentStop",
               "PreCompact", "PostCompact", "InstructionsLoaded", "ConfigChange", "CwdChanged", "FileChanged",
               "WorktreeCreate", "WorktreeRemove", "TaskCreated", "TaskCompleted", "TeammateIdle", "Elicitation",
               "ElicitationResult"}
REF_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s`\"')\]]+)")


def _scalar(v):
    v = v.strip()
    if not v:
        return ""
    if v[0] in "\"'" and v[-1] == v[0] and len(v) >= 2:
        return v[1:-1]
    if v[0] == "[" and v.endswith("]"):
        return [_scalar(x) for x in _split_top(v[1:-1]) if x.strip()]
    if v[0] == "{" and v.endswith("}"):
        out = {}
        for part in _split_top(v[1:-1]):
            if ":" in part:
                k, _, val = part.partition(":")
                out[k.strip()] = _scalar(val)
        return out
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    if v in ("true", "false"):
        return v == "true"
    return v


def _split_top(s):
    parts, depth, cur, q = [], 0, "", None
    for ch in s:
        if q:
            cur += ch
            if ch == q:
                q = None
            continue
        if ch in "\"'":
            q = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
            continue
        cur += ch
    parts.append(cur)
    return parts


def mini_yaml(text):
    """够用的 YAML 子集:顶层 `键: 值`(值可以是行内列表/映射/带引号字符串),和一层缩进的子映射、`- 项` 列表。"""
    out, cur_key = {}, None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw[0].isspace():
            k, sep, v = raw.partition(":")
            if not sep:
                raise ValueError("看不懂这一行:%r" % raw)
            cur_key = k.strip()
            out[cur_key] = _scalar(v) if v.strip() else {}
            continue
        if cur_key is None:
            raise ValueError("缩进行前面没有键:%r" % raw)
        s = raw.strip()
        if s.startswith("- "):
            if not isinstance(out[cur_key], list):
                out[cur_key] = []
            out[cur_key].append(_scalar(s[2:]))
        else:
            k, _, v = s.partition(":")
            if not isinstance(out[cur_key], dict):
                raise ValueError("%s 下面混了列表和映射" % cur_key)
            out[cur_key][k.strip()] = _scalar(v)
    return out


def frontmatter(path):
    """→ (frontmatter dict, 正文)。没有 frontmatter → ({}, 全文)。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    return mini_yaml(m.group(1)), m.group(2)


def _refs_exist(root, text, where, check):
    for ref in sorted(set(REF_RE.findall(text))):
        ref = ref.rstrip(".,;:")
        if any(c in ref for c in "<>*{"):
            continue
        check("%s 引用的 %s 存在" % (where, ref), os.path.exists(os.path.join(root, ref)))


def check_grader(name, g, case_dir, check):
    t = g.get("type")
    check("%s 判分器类型认识(%s)" % (name, t), t in GRADER_REQUIRED)
    if t not in GRADER_REQUIRED:
        return
    miss = [k for k in GRADER_REQUIRED[t] if k not in g]
    check("%s 判分器选项齐" % name, not miss, "缺 %s" % miss)
    if "arm" in g:
        check("%s 判分器 arm 合法" % name, g["arm"] in ARMS, str(g["arm"]))
    if "weight" in g:
        check("%s 判分器 weight 是正数" % name, isinstance(g["weight"], (int, float)) and g["weight"] > 0)
    for k in ("min", "max"):
        if k in g:
            check("%s 判分器 %s 是非负整数" % (name, k), isinstance(g[k], int) and g[k] >= 0)
    if t == "regex":
        try:
            re.compile(g["pattern"])
            ok = True
        except (re.error, TypeError):
            ok = False
        check("%s 正则能编译" % name, ok, str(g.get("pattern")))
        tgt = g.get("target", "last_message")
        if isinstance(tgt, dict):
            check("%s target 写成 {source: file, path}" % name, tgt.get("source") == "file" and tgt.get("path"))
        else:
            check("%s target 认识" % name, tgt in ("last_message", "trace", "files", "mock_calls"), str(tgt))
    if t == "tool_used" and "input_match" in g:
        try:
            re.compile(g["input_match"])
            ok = True
        except (re.error, TypeError):
            ok = False
        check("%s input_match 能编译" % name, ok)
    if t == "llm":
        check("%s llm 判分器有评分标准" % name, bool(g.get("criteria") or g.get("_body", "").strip()))
    if t == "baseline":
        check("%s baseline_file 存在" % name, os.path.isfile(os.path.join(case_dir, g["baseline_file"])))


def check_evals(root, check):
    ev = os.path.join(root, "evals")
    check("evals/ 目录存在", os.path.isdir(ev))
    if not os.path.isdir(ev):
        return
    gi = os.path.join(root, ".gitignore")
    text = open(gi, encoding="utf-8").read() if os.path.isfile(gi) else ""
    check(".gitignore 排除 evals/results/", re.search(r"^/?evals/results/?\s*$", text, re.M) is not None)
    cases = []
    for dirpath, dirnames, filenames in os.walk(ev):
        dirnames[:] = sorted(d for d in dirnames if d not in ("results", "mocks", "graders"))
        if "prompt.md" in filenames or "case.yaml" in filenames:
            cases.append(dirpath)
            dirnames[:] = []
    check("evals/ 至少有一个用例", bool(cases))
    for cd in cases:
        name = os.path.relpath(cd, ev)
        case = {}
        if os.path.isfile(os.path.join(cd, "case.yaml")):
            try:
                case = mini_yaml(open(os.path.join(cd, "case.yaml"), encoding="utf-8").read())
                ok = True
            except ValueError as e:
                ok, case = False, {"_err": str(e)}
            check("%s/case.yaml 能解析" % name, ok, case.get("_err", ""))
            check("%s/case.yaml schema_version 是 \"1.1\"" % name, str(case.get("schema_version")) == "1.1")
            check("%s/case.yaml 有 name" % name, bool(case.get("name")))
            extra = set(case) - CASE_KEYS
            check("%s/case.yaml 没有不认识的键" % name, not extra, str(sorted(extra)))
            ctx = case.get("context") or {}
            if isinstance(ctx, dict) and ctx.get("scaffold_script"):
                sp = os.path.join(cd, ctx["scaffold_script"])
                check("%s scaffold_script 存在" % name, os.path.isfile(sp))
            if isinstance(ctx, dict) and ctx.get("history_file"):
                check("%s history_file 存在" % name, os.path.isfile(os.path.join(cd, ctx["history_file"])))
        if os.path.isfile(os.path.join(cd, "prompt.md")):
            try:
                fm, body = frontmatter(os.path.join(cd, "prompt.md"))
                ok = True
            except ValueError as e:
                fm, body, ok = {}, "", False
                check("%s/prompt.md frontmatter 能解析" % name, False, str(e))
            if ok:
                extra = set(fm) - PROMPT_KEYS
                check("%s/prompt.md 没有不认识的键" % name, not extra, str(sorted(extra)))
                check("%s/prompt.md 正文不空" % name, bool(body.strip()))
                env = fm.get("env") or {}
                check("%s env 键都以 EVAL_ 开头" % name, all(str(k).startswith("EVAL_") for k in env))
        gdir = os.path.join(cd, "graders")
        graders = []
        if os.path.isdir(gdir):
            for fn in sorted(os.listdir(gdir)):
                if fn.endswith(".md"):
                    try:
                        g, body = frontmatter(os.path.join(gdir, fn))
                    except ValueError as e:
                        check("%s/graders/%s 能解析" % (name, fn), False, str(e))
                        continue
                    g["_body"] = body
                    graders.append(("%s/graders/%s" % (name, fn[:-3]), g))
        for i, g in enumerate(case.get("graders") or []):
            if isinstance(g, dict):
                graders.append(("%s/case.yaml#%d" % (name, i), g))
        check("%s 至少一个判分器" % name, bool(graders))
        for gname, g in graders:
            check_grader(gname, g, cd, check)


def check_commands(root, check):
    for c in COMMANDS:
        p = os.path.join(root, "commands", c + ".md")
        check("命令 /%s 在 commands/" % c, os.path.isfile(p))
        if not os.path.isfile(p):
            continue
        fm, body = frontmatter(p)
        check("命令 %s 有 description" % c, bool(fm.get("description")))
        extra = set(fm) - CMD_KEYS
        check("命令 %s frontmatter 没有不认识的键" % c, not extra, str(sorted(extra)))
        _refs_exist(root, body, "命令 %s" % c, check)


def check_agents(root, check):
    for a in AGENTS:
        p = os.path.join(root, "agents", a + ".md")
        check("子代理 %s 在 agents/" % a, os.path.isfile(p))
        if not os.path.isfile(p):
            continue
        fm, body = frontmatter(p)
        check("子代理 %s name 和文件名一致、不含冒号" % a, fm.get("name") == a and ":" not in str(fm.get("name")))
        check("子代理 %s 有 description" % a, bool(fm.get("description")))
        extra = set(fm) - AGENT_KEYS
        check("子代理 %s 没有不认识的键" % a, not extra, str(sorted(extra)))
        check("子代理 %s 没写插件里不生效的键" % a, not (set(fm) & AGENT_IGNORED))
        tools = [t.strip() for t in str(fm.get("tools", "")).split(",") if t.strip()]
        deny = [t.strip() for t in str(fm.get("disallowedTools", "")).split(",") if t.strip()]
        check("子代理 %s 不能再开子代理" % a, "Agent" in deny or (tools and "Agent" not in tools and "Task" not in tools))
        _refs_exist(root, body, "子代理 %s" % a, check)


def check_hooks(root, check):
    p = os.path.join(root, "hooks", "hooks.json")
    check("hooks/hooks.json 存在", os.path.isfile(p))
    if not os.path.isfile(p):
        return
    try:
        d = json.load(open(p, encoding="utf-8"))
    except ValueError as e:
        check("hooks.json 是合法 JSON", False, str(e))
        return
    hooks = d.get("hooks") if isinstance(d, dict) else None
    check("hooks.json 顶层有 hooks", isinstance(hooks, dict))
    if not isinstance(hooks, dict):
        return
    for ev, groups in hooks.items():
        check("hook 事件 %s 认识" % ev, ev in HOOK_EVENTS)
        for g in groups if isinstance(groups, list) else []:
            for h in g.get("hooks") or []:
                check("hook %s 处理器 type 是 command" % ev, h.get("type") in ("command", "http", "prompt", "agent"))
                text = " ".join([str(h.get("command", ""))] + [str(x) for x in h.get("args") or []])
                _refs_exist(root, text, "hook %s" % ev, check)


def checks(root):
    out = []

    def check(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    check_evals(root, check)
    check_commands(root, check)
    check_agents(root, check)
    check_hooks(root, check)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ap.add_argument("-q", "--quiet", action="store_true", help="只打印不过的项")
    ns = ap.parse_args(argv)
    res = checks(ns.root)
    for name, ok, detail in res:
        if not ok or not ns.quiet:
            print("%s %s%s" % ("✅" if ok else "❌", name, "" if ok else "  " + str(detail)[:300]))
    bad = [r for r in res if not r[1]]
    print("插件静态校验 %d/%d 过" % (len(res) - len(bad), len(res)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
