#!/usr/bin/env python3
"""grade_ext.py — grade.py 第 5 批扩展:建 run(setup)、W0 快照、段间 mutate、多段驱动(next)、ext 场景判分。

读法(出题文件有歧义处)写在 grade.py 文件头 R33 起,这里不重复。由 grade.py 的子命令调用;测试直接 import。

run 目录(setup 建,后面的子命令都只认它):
  RUN/run.json                       场景、arm、工作区、站点、端口、T、skill 目录、各段状态
  RUN/site/                          lifecycle_sites.py build 的输出(= 出题文件里的 DIR)
  RUN/ws/                            「新目录」类工作区(其余场景的工作区在 RUN/site/repo)
  RUN/skill/seo-suite/               例 6 的 run 本地 skill(reinstall_skill 只删这里)
  RUN/sessions/<段>/driver.jsonl     这一段的驱动日志(grade.py next 写)
  RUN/sessions/<段>/start/、end/     段开始(mutate 之后)和结束时工作区的完整副本 + manifest.json
  RUN/sessions/<段>/snapshots/       每次停下时 profile.json 的副本
"""
import ast
import datetime as dt
import fnmatch
import glob
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

import grade as G

SGT = dt.timezone(dt.timedelta(hours=8))
LS_PATH = os.path.join(G.TESTSITES, "lifecycle_sites.py")
SNAP_SKIP = {".git", "node_modules", "__pycache__", ".next"}
MAX_COPY = 5 * 1024 * 1024
TEXT_EXT = (".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".html", ".htm", ".xml", ".py", ".sh", ".mjs", ".js",
            ".ts", ".tsx", ".toml", ".log", "")


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------

def today_sgt():
    return dt.datetime.now(SGT).date().isoformat()


def now_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def write_text(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except (OSError, TypeError):
        return None


def write_json(path, d):
    write_text(path, json.dumps(d, ensure_ascii=False, indent=1) + "\n")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def git(ws, *args):
    return subprocess.run(["git", "-C", ws, "-c", "user.name=rq237-eval", "-c", "user.email=eval@localhost",
                           "-c", "commit.gpgsign=false", *args], capture_output=True, text=True)


def git_commit(ws, msg):
    if not os.path.isdir(os.path.join(ws, ".git")):
        git(ws, "init", "-q")
    git(ws, "add", "-A")
    git(ws, "commit", "-q", "--allow-empty", "-m", msg)
    r = git(ws, "rev-parse", "HEAD")
    return r.stdout.strip() or None


def is_text_file(path):
    return os.path.splitext(path)[1].lower() in TEXT_EXT


# ---------------------------------------------------------------------------
# run.json
# ---------------------------------------------------------------------------

def run_file(run):
    return os.path.join(run, "run.json")


def load_run(run):
    d = G.read_json(run_file(run))
    if not d:
        raise SystemExit("读不到 %s(先跑 grade.py setup)" % run_file(run))
    return d


def save_run(run, d):
    write_json(run_file(run), d)


def sess_dir(run, name):
    return os.path.join(run, "sessions", name)


def family_of(spec, sc):
    if "driver_ext" in spec or "criteria_defs_ext" in spec:
        return "ext"
    if any(c["id"] in G.REAL_CRITERIA for c in sc.get("criteria", [])):
        return "real"
    return "onboarding"


def session_specs(sc):
    """场景的段列表(R36):没有 sessions 的场景是一段 main。"""
    if sc.get("sessions"):
        return [dict(s) for s in sc["sessions"]]
    return [{"name": "main", "prompt": sc.get("prompt"), "simulated_user": sc.get("simulated_user"),
             "fallback": sc.get("fallback"), "fallback_unknown_ring": sc.get("fallback_unknown_ring"), "mutate": []}]


def session_spec(sc, name):
    s = next((x for x in session_specs(sc) if x["name"] == name), None)
    if s is None:
        raise SystemExit("场景 %s 没有段 %s;有:%s" % (sc["id"], name, ", ".join(x["name"] for x in session_specs(sc))))
    return s


# ---------------------------------------------------------------------------
# setup:照各出题文件的 setup 文本建站、建工作区(R33)
# ---------------------------------------------------------------------------

def _ls():
    if G.TESTSITES not in sys.path:
        sys.path.insert(0, G.TESTSITES)
    import lifecycle_sites as LS  # noqa
    return LS


def _setup_dir_path(txt, D):
    """「DIR/repo(...)」「--dir DIR/site」→ 绝对路径。"""
    m = re.search(r"DIR(/[\w./-]*)?", txt or "")
    if not m:
        return None
    sub = (m.group(1) or "").strip("/")
    return os.path.join(D, sub) if sub else D


def build_site(spec, sc, run, base):
    st = sc.get("setup") or {}
    D = os.path.join(run, "site")
    b = st.get("build") or ""
    if "sites.pingwell" in b or sc.get("product") == "pingwell":
        site = spec["sites"]["pingwell"]
        for rel, content in site["files"].items():
            write_text(os.path.join(D, "repo", rel), content.replace("{base}", base))
        return D
    m = re.search(r"lifecycle_sites\.py build --product (\w+)", b)
    if m:
        state = re.search(r"--state (\w+)", b)
        _ls().build(m.group(1), D, base, state.group(1) if state else "before")
        return D
    return None


def make_ws(sc, run, base):
    st = sc.get("setup") or {}
    w = st.get("workspace") or ""
    D = os.path.join(run, "site")
    if w.strip().startswith("DIR/"):
        first = re.split(r"[(（,，\s]", w.strip(), maxsplit=1)[0]
        ws = _setup_dir_path(first, D)
        os.makedirs(ws, exist_ok=True)
        if "brief.md" in w and os.path.isfile(os.path.join(D, "brief.md")):
            shutil.copyfile(os.path.join(D, "brief.md"), os.path.join(ws, "brief.md"))
        return ws
    ws = os.path.join(run, "ws")
    os.makedirs(ws, exist_ok=True)
    m = re.search(r"README\.md\s*(?:写|,?内容[::])\s*「(.*?)」", w)
    if m:
        write_text(os.path.join(ws, "README.md"), m.group(1).replace("{base}", base or "") + "\n")
    if re.search(r"DIR/gsc/?\s*复制成\s*data/", w):
        src = os.path.join(D, "gsc")
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(ws, "data"), dirs_exist_ok=True)
    for rel, content in (st.get("files") or {}).items():
        write_text(os.path.join(ws, rel), content.replace("{base}", base or ""))
    return ws


def serve_cmd(sc, run, port):
    st = sc.get("setup") or {}
    s = st.get("serve") or ""
    if "serve" not in s:
        return None, None
    d = _setup_dir_path(s.split("--dir", 1)[1] if "--dir" in s else "DIR", os.path.join(run, "site"))
    return d, "python3 %s serve --dir %s --port %d" % (LS_PATH, d, port)


def online_site(sc):
    m = re.search(r"https?://\S+", str((sc.get("setup") or {}).get("site") or ""))
    return m.group(0).rstrip("。,,)") if m else None


def install_skill(src, dest):
    if not src or not os.path.isfile(os.path.join(src, "SKILL.md")):
        raise SystemExit("skill 源目录 %s 下没有 SKILL.md" % src)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest, symlinks=False)


def setup_run(sid, arm, run, port=8810, scenarios=None, skill_dir=None, skill_src=None, w0=None, T=None,
              rebase_port=False):
    scenarios = os.path.abspath(scenarios or G.DEFAULT_SCENARIOS)
    spec, sc = G.load_scenario(sid, scenarios)
    run = os.path.abspath(run)
    if os.path.exists(run_file(run)):
        raise SystemExit("%s 已经建过(换一个 RUN 目录)" % run)
    os.makedirs(run, exist_ok=True)
    fam = family_of(spec, sc)
    T = T or today_sgt()
    base = "http://127.0.0.1:%d" % port
    R = {"scenario": sid, "scenarios_file": scenarios, "family": fam, "arm": arm, "run": run, "port": port, "T": T,
         "base": None, "site": None, "site_dir": None, "serve": None, "skill_dir": None, "w0": None,
         "session_order": [s["name"] for s in session_specs(sc)], "sessions": {}, "created_at": now_iso(),
         "product": sc.get("product")}
    notes = []
    if sc.get("base"):
        if not w0:
            raise SystemExit("场景 %s 的 base 是 %s:先按 %s 完整跑一遍,再 grade.py w0 打包,setup 时带 --w0"
                             % (sid, sc["base"], sc["base"]))
        info = unpack_w0(w0, run, port if rebase_port else None)
        R.update(ws=info["ws"], site_dir=info["site_dir"], base=info["base"], site=info["site"], port=info["port"],
                 w0=os.path.abspath(w0), serve=info["serve"], base_scenario=sc["base"])
        if info["port"] != port and not rebase_port:
            notes.append("沿用 W0 的端口 %d(同一个 W0 的变体别同时跑;要并行就带 --rebase-port)" % info["port"])
    else:
        build_site(spec, sc, run, base)
        ws = make_ws(sc, run, base)
        sd, cmd = serve_cmd(sc, run, port)
        R.update(ws=ws, site_dir=sd, serve=cmd, base=base if cmd or (sc.get("setup") or {}).get("build") else None)
        R["site"] = base if cmd else online_site(sc)
        if not cmd and R["site"] is None and sc.get("product") != "idea" and (sc.get("setup") or {}).get("build"):
            R["base"] = base
    if arm in ("skill", "v043"):
        if sc.get("id") == "ex6-user-rules" or (sc.get("setup") or {}).get("skill_versions"):
            dest = os.path.join(run, "skill", "seo-suite")
            install_skill(skill_src or skill_dir, dest)
            R["skill_dir"] = dest
            R["skill_installed_from"] = os.path.abspath(skill_src or skill_dir)
        else:
            R["skill_dir"] = os.path.abspath(skill_dir) if skill_dir else os.path.join(G.ROOT, "skills", "seo-suite")
    if R.get("ws"):
        if not os.path.isdir(os.path.join(R["ws"], ".git")):
            git_commit(R["ws"], "init")
    for name in R["session_order"]:
        R["sessions"][name] = {"driver_log": os.path.join(sess_dir(run, name), "driver.jsonl")}
        os.makedirs(sess_dir(run, name), exist_ok=True)
    save_run(run, R)
    return {"run": run, "family": fam, "ws": R["ws"], "site": R["site"], "serve": R["serve"], "T": T,
            "skill_dir": R["skill_dir"], "sessions": R["session_order"], "notes": notes,
            "next": "后台起 serve(有的话)→ 每段先 grade.py mutate RUN 段名 → 用它打印的 prompt 起被测子代理 → "
                    "每回合结束 grade.py next %s --run RUN --session 段名 --transcript 转录" % sid}


# ---------------------------------------------------------------------------
# W0(R37)
# ---------------------------------------------------------------------------

def pack_w0(run, out):
    run = os.path.abspath(run)
    R = load_run(run)
    warn = [n for n in R["session_order"] if not (R["sessions"].get(n) or {}).get("ended")]
    with tarfile.open(out, "w:gz") as tf:
        for sub in ("site", "ws"):
            p = os.path.join(run, sub)
            if os.path.isdir(p):
                tf.add(p, arcname=sub)
        tf.add(run_file(run), arcname="w0-run.json")
    return {"w0": os.path.abspath(out), "from_run": run, "scenario": R["scenario"], "arm": R["arm"],
            "sha256": sha256_file(out), "not_ended_sessions": warn}


def _rebase(paths, old, new):
    n = 0
    for top in paths:
        for root, dirs, files in os.walk(top):
            dirs[:] = [d for d in dirs if d != ".git"]
            for f in files:
                p = os.path.join(root, f)
                if not is_text_file(p):
                    continue
                s = read_text(p)
                if s is not None and old in s:
                    st = os.stat(p)
                    write_text(p, s.replace(old, new))
                    os.utime(p, (st.st_atime, st.st_mtime))
                    n += 1
    return n


def unpack_w0(w0, run, port=None):
    with tarfile.open(w0) as tf:
        tf.extractall(run, filter="data")
    old = G.read_json(os.path.join(run, "w0-run.json")) or {}
    oldrun = old.get("run") or ""

    def mp(p):
        return os.path.join(run, os.path.relpath(p, oldrun)) if p and oldrun and p.startswith(oldrun) else p
    info = {"ws": mp(old.get("ws")), "site_dir": mp(old.get("site_dir")), "base": old.get("base"),
            "site": old.get("site"), "port": old.get("port"), "serve": None}
    if port and old.get("port") and port != old["port"] and old.get("base"):
        newbase = old["base"].replace(":%d" % old["port"], ":%d" % port)
        _rebase([p for p in (info["ws"], info["site_dir"]) if p], old["base"], newbase)
        info.update(base=newbase, port=port, site=(old.get("site") or "").replace(old["base"], newbase) or None)
    if info["site_dir"]:
        info["serve"] = "python3 %s serve --dir %s --port %d" % (LS_PATH, info["site_dir"], info["port"])
    return info


# ---------------------------------------------------------------------------
# 快照
# ---------------------------------------------------------------------------

def snapshot(ws, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    files = os.path.join(dest, "files")
    os.makedirs(files, exist_ok=True)
    man = {}
    for root, dirs, fs in os.walk(ws):
        dirs[:] = sorted(d for d in dirs if d not in SNAP_SKIP)
        for f in sorted(fs):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, ws).replace(os.sep, "/")
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            st = os.stat(p)
            man[rel] = {"sha256": sha256_file(p), "mtime": st.st_mtime, "size": st.st_size}
            if st.st_size <= MAX_COPY:
                q = os.path.join(files, rel)
                os.makedirs(os.path.dirname(q), exist_ok=True)
                shutil.copy2(p, q)
    write_json(os.path.join(dest, "manifest.json"), man)
    return man


def manifest_diff(a, b):
    out = []
    for k in sorted(set(a) | set(b)):
        if k not in a:
            out.append({"path": k, "status": "added"})
        elif k not in b:
            out.append({"path": k, "status": "deleted"})
        elif a[k]["sha256"] != b[k]["sha256"]:
            out.append({"path": k, "status": "modified"})
    return out


def playbook_manifest(ws):
    d = os.path.join(ws, "seo-ops", "playbook")
    out = {}
    for root, dirs, fs in os.walk(d):
        for f in fs:
            p = os.path.join(root, f)
            if os.path.isfile(p) and not os.path.islink(p):
                out[os.path.relpath(p, d).replace(os.sep, "/")] = sha256_file(p)
    return out


def end_session(run, name, why="driver end"):
    R = load_run(run)
    info = R["sessions"].setdefault(name, {})
    if info.get("ended"):
        return info
    dest = os.path.join(sess_dir(run, name), "end")
    man = snapshot(R["ws"], dest)
    start = G.read_json(os.path.join(sess_dir(run, name), "start", "manifest.json")) or {}
    info.update(ended=True, ended_at=now_iso(), ended_epoch=time.time(), end_snapshot=dest, end_why=why,
                changed=manifest_diff(start, man))
    save_run(run, R)
    return info


# ---------------------------------------------------------------------------
# mutate(R38)
# ---------------------------------------------------------------------------

def _subst(s, R):
    return str(s).replace("{base}", (R.get("base") or "").rstrip("/")).replace("{T}", R["T"])


def _path(R, p):
    p = str(p)
    if p.startswith("SITE/") or p == "SITE":
        if not R.get("site_dir"):
            raise SystemExit("这个 run 没有站点目录,mutate 写不了 %s" % p)
        return os.path.join(R["site_dir"], p[5:])
    return os.path.join(R["ws"], p)


def _glob(R, pat):
    return sorted(x for x in glob.glob(_path(R, pat), recursive=True) if os.path.isfile(x))


def do_action(R, spec, act, install_from=None):
    if "write" in act:
        p = _path(R, act["write"])
        write_text(p, _subst(act.get("content", ""), R))
        return {"action": "write", "path": p}
    if "replace_in_files" in act:
        changed = []
        for p in _glob(R, act["replace_in_files"]):
            s = read_text(p)
            if s is not None and act["old"] in s:
                write_text(p, s.replace(act["old"], act["new"]))
                changed.append(p)
        return {"action": "replace_in_files", "glob": act["replace_in_files"], "files_changed": changed}
    if "append_sitemap" in act:
        p = _path(R, act["append_sitemap"])
        s = read_text(p) or ""
        rows = "".join("<url><loc>%s%s</loc><lastmod>%s</lastmod></url>\n" % ((R.get("base") or "").rstrip("/"), x, R["T"])
                       for x in act.get("paths") or [])
        if "</urlset>" not in s:
            raise SystemExit("%s 里没有 </urlset>" % p)
        i = s.rindex("</urlset>")
        write_text(p, s[:i] + rows + s[i:])
        return {"action": "append_sitemap", "path": p, "added": act.get("paths")}
    if "run_recipe" in act:
        name = act["run_recipe"]
        code = (spec.get("recipes") or {}).get(name)
        if code is None:
            raise SystemExit("recipes 里没有 %s" % name)
        tmp = tempfile.mkdtemp(prefix="rq237-recipe-")
        try:
            path = os.path.join(tmp, name)
            write_text(path, code)
            args = [_subst(a, R) for a in act.get("args") or []]
            r = subprocess.run([sys.executable, "-I", path] + args, cwd=R["ws"], capture_output=True, text=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if r.returncode != 0:
            raise SystemExit("recipe %s 失败:%s" % (name, (r.stderr or r.stdout)[-800:]))
        return {"action": "run_recipe", "recipe": name, "args": args, "cwd": R["ws"], "stdout": r.stdout[-400:]}
    if "reinstall_skill" in act:
        before = playbook_manifest(R["ws"])
        out = {"action": "reinstall_skill", "version": act["reinstall_skill"], "playbook_before": before}
        sd = R.get("skill_dir")
        if R.get("arm") == "baseline" or not sd:
            out["skipped"] = "baseline 组没有 skill,不重装(R39)"
        else:
            if not os.path.abspath(sd).startswith(os.path.abspath(R["run"]) + os.sep):
                raise SystemExit("skill 目录 %s 不在 run 目录里,拒绝删除" % sd)
            if not install_from:
                raise SystemExit("reinstall_skill 要 --install-from(被测版本的 skill 目录)")
            install_skill(install_from, sd)
            out.update(skill_dir=sd, installed_from=os.path.abspath(install_from))
        out["playbook_after"] = playbook_manifest(R["ws"])
        return out
    if "tamper" in act:
        files = _glob(R, act["tamper"])
        rows = []
        for p in files:
            before = sha256_file(p)
            s = read_text(p) or ""
            write_text(p, s + ("" if s.endswith("\n") or not s else "\n") + act.get("append", "") + "\n")
            rows.append({"path": p, "sha256_before": before, "sha256_after": sha256_file(p)})
        return {"action": "tamper", "glob": act["tamper"], "files": rows}
    raise SystemExit("不认识的 mutate 动作:%s" % json.dumps(act, ensure_ascii=False))


SHORT_PROMPT = (
    "你在目录 {ws} 里帮用户做事(先 cd 进去,所有命令都在这个目录里跑,不碰别的目录)。不许开子代理。\n\n"
    "{arm_line}\n\n"
    "用户说:「{prompt}」\n\n"
    "注意:你没有提问工具;需要问用户时,把问题按编号列出来,然后结束这一回合(不要替用户回答、不要编用户的答案)。"
    + G.REPLY_CHANNEL)


def first_message(sess):
    if sess.get("prompt"):
        return sess["prompt"], 0
    turns = sess.get("user_turns") or []
    return (turns[0], 1) if turns else ("", 0)


def session_prompt(R, sess):
    text, _ = first_message(sess)
    text = text.replace("{base}", (R.get("base") or R.get("site") or "{base}").rstrip("/"))
    arm = R["arm"]
    line = G.ARM_LINE[arm].format(skill_dir=(R.get("skill_dir") or os.path.join(G.ROOT, "skills", "seo-suite")).rstrip("/"),
                                  repo=G.ROOT)
    tpl = G.PROMPT_COMMON if sess.get("simulated_user") else SHORT_PROMPT
    return tpl.format(ws=R["ws"].rstrip("/"), arm_line=line, prompt=text)


def begin_session(run, name, install_from=None):
    run = os.path.abspath(run)
    R = load_run(run)
    spec, sc = G.load_scenario(R["scenario"], R["scenarios_file"])
    sess = session_spec(sc, name)
    order = R["session_order"]
    i = order.index(name)
    for prev in order[:i]:
        pi = R["sessions"].get(prev) or {}
        if not pi.get("started"):
            raise SystemExit("上一段 %s 还没开始;按顺序跑:%s" % (prev, " → ".join(order)))
        if not pi.get("ended"):
            end_session(run, prev, why="下一段 mutate 前补拍")
            R = load_run(run)
    info = R["sessions"].setdefault(name, {})
    if info.get("started"):
        raise SystemExit("段 %s 已经开始过了" % name)
    log = [do_action(R, spec, a, install_from) for a in (sess.get("mutate") or [])]
    head = git_commit(R["ws"], "rq237 session %s start" % name)
    sd = sess_dir(run, name)
    os.makedirs(sd, exist_ok=True)
    snapshot(R["ws"], os.path.join(sd, "start"))
    prompt = session_prompt(R, sess)
    write_text(os.path.join(sd, "prompt.txt"), prompt)
    info.update(started=True, started_at=now_iso(), started_epoch=time.time(), git_start=head, mutate=log,
                start_snapshot=os.path.join(sd, "start"), driver_log=info.get("driver_log") or os.path.join(sd, "driver.jsonl"))
    save_run(run, R)
    return {"session": name, "git_start": head, "mutate": [{k: v for k, v in x.items() if not k.startswith("playbook")}
                                                            for x in log], "prompt": prompt,
            "driver_log": info["driver_log"]}


# ---------------------------------------------------------------------------
# 多段驱动(R40)
# ---------------------------------------------------------------------------

def _stop_text(cand):
    return (cand.get("text") or "") + "\n" + "\n".join(q["text"] for q in cand.get("questions") or [])


def drive_next_ext(run, name, transcript, max_turns=20):
    run = os.path.abspath(run)
    R = load_run(run)
    spec, sc = G.load_scenario(R["scenario"], R["scenarios_file"])
    sess = session_spec(sc, name)
    info = R["sessions"].setdefault(name, {})
    if not info.get("started"):
        return {"action": "error", "why": "段 %s 还没开始(先 grade.py mutate RUN %s)" % (name, name)}
    if info.get("ended"):
        return {"action": "error", "why": "段 %s 已经结束" % name}
    info["transcript"] = os.path.abspath(transcript)
    save_run(run, R)
    tr = G.Transcript(transcript)
    if not tr.turns:
        return {"action": "error", "why": "转录里没有回合"}
    turn = tr.turns[-1]
    dl = info["driver_log"]
    log = G.load_driver(dl)
    if any(int(d.get("turn") or 0) == turn["n"] for d in log):
        return {"action": "error", "why": "第 %d 回合已经回过话了" % turn["n"]}
    cand = G.stop_candidate(turn)
    un_text = None
    if not cand and turn["n"] < max_turns and sess.get("simulated_user"):
        un_text = G.unnumbered_question(turn)
        if un_text and G.unnumbered_allowed(log, turn["n"]):
            cand = {"text": un_text, "questions": [], "unnumbered": True}
    _, ut_start = first_message(sess)
    uts = sess.get("user_turns") or []
    sent_ut = sum(1 for d in log if d.get("kind") == "user_turn")
    next_ut = ut_start + sent_ut
    fallback = sess.get("fallback") or sc.get("fallback") or "Carry on."
    row = None
    if turn["n"] >= max_turns:
        row = None
    elif cand:
        text = _stop_text(cand)
        for k, t in enumerate(sess.get("simulated_user_by_topic") or []):
            used = sum(1 for d in log if d.get("source") == "topic:%d" % k)
            mx = t.get("max_uses")
            if (mx is None or used < int(mx)) and re.search(t["if"], text, re.I):
                row = {"user_text": t["reply"], "source": "topic:%d" % k, "kind": "reply", "ring": None}
                break
        if row is None and next_ut < len(uts):
            row = {"user_text": uts[next_ut], "source": "user_turn:%d" % next_ut, "kind": "user_turn", "ring": None}
        if row is None:
            su = sess.get("simulated_user")
            if su:
                ring, how = G.ring_of(cand["text"] or "\n".join(q["text"] for q in cand["questions"]), R["ws"])
                if ring is None:
                    row = {"user_text": sess.get("fallback_unknown_ring") or sc.get("fallback_unknown_ring") or fallback,
                           "source": "fallback_unknown_ring", "kind": "reply", "ring": None}
                else:
                    script = su.get(str(ring)) or []
                    used = sum(1 for d in log if d.get("ring") == ring and d.get("source") == "script")
                    row = ({"user_text": script[used], "source": "script"} if used < len(script) else
                           {"user_text": fallback, "source": "fallback"})
                    row.update(kind="reply", ring=ring, ring_from=how)
            else:
                row = {"user_text": fallback, "source": "fallback", "kind": "reply", "ring": None}
    elif next_ut < len(uts):
        row = {"user_text": uts[next_ut], "source": "user_turn:%d" % next_ut, "kind": "user_turn", "ring": None}
    if row is None:
        why = ("到了回合上限 %d" % max_turns if turn["n"] >= max_turns else
               "最后一回合没有停下来问,user_turns 也发完了")
        end_session(run, name, why=why)
        return {"action": "end", "session": name, "turn": turn["n"], "why": why}
    snap = None
    prof = os.path.join(R["ws"], "seo-ops", "context", "profile.json")
    if os.path.isfile(prof):
        sd = os.path.join(sess_dir(run, name), "snapshots")
        os.makedirs(sd, exist_ok=True)
        snap = os.path.join(sd, "turn%02d.profile.json" % turn["n"])
        shutil.copyfile(prof, snap)
    row.update(turn=turn["n"], session=name, at=now_iso(), at_epoch=time.time(), profile_snapshot=snap)
    if cand and cand.get("unnumbered"):
        row["unnumbered"] = True
    with open(dl, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return dict(row, action="reply")


# ---------------------------------------------------------------------------
# 判分上下文
# ---------------------------------------------------------------------------

class Sess:
    def __init__(self, R, name, last):
        self.name = name
        self.info = (R.get("sessions") or {}).get(name) or {}
        self.started = bool(self.info.get("started"))
        self.tr = G.Transcript(self.info.get("transcript"))
        self.driver = G.load_driver(self.info.get("driver_log"))
        cands = []
        for t in self.tr.turns:
            c = G.stop_candidate(t)
            if c:
                cands.append(dict(c, turn=t["n"]))
        self.cands = cands
        stop_turns = {c["turn"] for c in cands}
        rows = [d for d in self.driver if d.get("kind") != "user_turn" or int(d.get("turn") or 0) in stop_turns]
        self.stops, self.problems = G.build_stops(self.tr, rows)
        self.start_dir = self.info.get("start_snapshot")
        self.end_dir = self.info.get("end_snapshot")
        self.live_ws = R.get("ws")
        self.last = last
        self.start_man = G.read_json(os.path.join(self.start_dir, "manifest.json")) if self.start_dir else None
        self.end_man = G.read_json(os.path.join(self.end_dir, "manifest.json")) if self.end_dir else None
        self.changed = self.info.get("changed")
        if self.changed is None and self.start_man is not None and last and self.live_ws:
            self.changed = manifest_diff(self.start_man, live_manifest(self.live_ws))

    @property
    def ran(self):
        return self.started and bool(self.tr.turns)

    def ws_end(self):
        if self.end_dir:
            return os.path.join(self.end_dir, "files")
        return self.live_ws if self.last else None

    def ws_start(self):
        return os.path.join(self.start_dir, "files") if self.start_dir else None

    def end_mtime(self, rel):
        if self.end_man and rel in self.end_man:
            return self.end_man[rel]["mtime"]
        p = os.path.join(self.ws_end() or "", rel)
        return os.stat(p).st_mtime if os.path.isfile(p) else None

    def changed_paths(self, under=None):
        return [c["path"] for c in self.changed or [] if c["status"] != "deleted"
                and (under is None or c["path"].startswith(under))]


def live_manifest(ws):
    man = {}
    for root, dirs, fs in os.walk(ws):
        dirs[:] = [d for d in dirs if d not in SNAP_SKIP]
        for f in fs:
            p = os.path.join(root, f)
            if os.path.isfile(p) and not os.path.islink(p):
                st = os.stat(p)
                man[os.path.relpath(p, ws).replace(os.sep, "/")] = {"sha256": sha256_file(p), "mtime": st.st_mtime,
                                                                    "size": st.st_size}
    return man


class ExtCtx:
    def __init__(self, R, spec, sc, answers, lc, refs):
        self.R, self.spec, self.sc, self.ans, self.lc, self.refs = R, spec, sc, answers, lc, refs or []
        self.T = R.get("T")
        order = R.get("session_order") or [s["name"] for s in session_specs(sc)]
        self.order = order
        self.S = {n: Sess(R, n, i == len(order) - 1) for i, n in enumerate(order)}

    def sess(self, cr):
        return self.S.get(cr.get("session") or self.order[0])


def _not_ran(s):
    if s is None:
        return False, {"why": "场景里没有这一段"}
    if not s.ran:
        return False, {"why": "这一段没有跑(没有 mutate 记录或转录为空)", "session": s.name}
    return None


def stop_info(c):
    return {"turn": c["turn"], "line": c["line"], "via": c["via"], "questions": [q["text"][:100] for q in c["questions"]]}


# ---------------------------------------------------------------------------
# ext 断言
# ---------------------------------------------------------------------------

RERUN_SUBS = ("start", "ask")


def c_no_onboarding_rerun(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    mx = int(cr.get("max_stops", 0))
    calls = []
    for c in s.tr.calls():
        for o in G.onboard_calls(c):
            if o["sub"] in RERUN_SUBS:
                calls.append({"line": c["line"], "sub": o["sub"], "ring": o["ring"]})
    ring_stops = [stop_info(c) for c in s.cands if G.RING_RE.search(_stop_text(c))]
    ok = not calls and not ring_stops and len(s.cands) <= mx
    return ok, {"session": s.name, "rerun_calls": calls, "stops_naming_a_ring": ring_stops, "stops": len(s.cands),
                "max_stops": mx}


def _dates_under_confirmed(prof):
    out = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, path + [str(k)])
        elif isinstance(o, list):
            for v in o:
                walk(v, path)
        elif isinstance(o, str):
            if any(("confirmed" in p.lower() or "确认" in p) for p in path):
                for m in re.finditer(r"(?<!\d)(20\d\d)-(\d\d)-(\d\d)(?!\d)", o):
                    out.append((m.group(0), ".".join(path)))
    walk(prof or {}, [])
    return out


WEEKLY_CALL = re.compile(r"\bops(?:\.py)?\b[^\n;|&]*\bweekly\b", re.I)
HEADING_LINE = re.compile(r"^\s*(?:#{1,6}\s+|\*\*|【)")
# R79:阶段名要和「阶段 / stage / phase」在同一行(launched、growth、change 这些键名是常用英文词)
STAGE_WORD = re.compile(r"阶段|\bstage\b|\bphase\b", re.I)


def weekly_calls(s):
    """原文整条匹配照旧;另按 R65 展开后的段再认一遍(O=…/ops.py; python3 $O weekly)。"""
    return [c for c in s.tr.calls() if c["name"] == "Bash" and (
        WEEKLY_CALL.search(G.bash_cmd(c))
        or any(WEEKLY_CALL.search(" ".join(seg)) for seg, _ in G.command_segments(G.bash_cmd(c))))]


def c_resume_first_screen(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    if s.cands:
        c0 = s.cands[0]
        text, upto = c0["text"], c0["line"]
    else:
        t1 = s.tr.turns[0]
        _, lt = G.turn_end(t1)
        text = lt["text"] if lt else ""
        upto = lt["line"] if lt else s.tr.end_line
    prof = G.read_json(os.path.join(s.ws_start() or "", "seo-ops", "context", "profile.json"))
    dates = _dates_under_confirmed(prof)
    last = max((d for d, _ in dates), default=None)
    d_ok = False
    if last:
        y, m, d = (int(x) for x in last.split("-"))
        d_ok = last in text or bool(re.search(r"(?<!\d)0?%d\s*月\s*0?%d\s*日" % (m, d), text))
    stage = (ec.ans or {}).get("stage")
    names = G.stage_names(ec.lc).get(_i(stage), []) if stage is not None else []
    st_hits = sorted({h for ln in text.splitlines() if STAGE_WORD.search(ln) for h in G.hits(ln, names)})
    weeks = [int(x) for x in cr.get("week_accept") or []]
    wk = [n for n in weeks if re.search(r"第\s*%d\s*周|week\s*%d(?!\d)|\bW\s*%d(?!\d)" % (n, n, n), text, re.I)]
    wcalls = [c["line"] for c in weekly_calls(s) if c["line"] <= upto]
    heads = [ln.strip()[:80] for ln in text.splitlines()
             if HEADING_LINE.match(ln) and G.hits(ln, ("本周运营", "运营单", "this week", "weekly"))]
    ok = d_ok and bool(st_hits) and bool(wk) and bool(wcalls or heads)
    return ok, {"session": s.name, "first_screen_line": upto, "profile_confirmed_dates": dates[:6], "last_confirmed": last,
                "date_in_text": d_ok, "stage_hits": st_hits, "weeks_found": wk, "week_accept": weeks,
                "weekly_calls": wcalls, "weekly_headings": heads}


def _i(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def c_questions_only_on(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    allow, deny, mx = cr.get("allow") or ".", cr.get("deny"), int(cr.get("max", 99))
    qs = [(c["turn"], q["text"]) for c in s.cands for q in c["questions"]]
    not_allowed = [q for _, q in qs if not re.search(allow, q, re.I)]
    denied = [q for _, q in qs if deny and re.search(deny, q, re.I)]
    need = bool(cr.get("expect_questions"))
    ok = not not_allowed and not denied and len(qs) <= mx and (not need or bool(s.stops))
    return ok, {"session": s.name, "questions": [q[:100] for _, q in qs], "count": len(qs), "max": mx,
                "not_allowed": not_allowed, "denied": denied, "answered_stops": len(s.stops),
                "expect_questions": need}


def c_no_repeat_question(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    mx = int(cr.get("max_stops", 0))
    hit = [q["text"][:100] for c in s.cands for q in c["questions"] if re.search(cr["topic"], q["text"], re.I)]
    return not hit and len(s.cands) <= mx, {"session": s.name, "questions_on_topic": hit, "stops": len(s.cands),
                                           "max_stops": mx}


def flatten_profile(prof):
    out = {}

    def walk(o, path):
        if isinstance(o, dict):
            if "value" in o and path:
                out[path] = G.as_text(o)
            for k, v in o.items():
                walk(v, (path + "." if path else "") + str(k))
        elif isinstance(o, list):
            if path:
                out.setdefault(path, "\n".join(G.as_text(x) for x in o))
            for i, v in enumerate(o):
                walk(v, "%s.%d" % (path, i))
        elif o is not None and path:
            out.setdefault(path, str(o))
    walk(prof or {}, "")
    return out


def c_profile_contains(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    ppath = os.path.join(s.ws_end() or "", "seo-ops", "context", "profile.json")
    prof = G.read_json(ppath)
    if prof is None:
        return False, {"session": s.name, "why": "读不到 profile.json", "file": ppath}
    path = cr["path"]
    if any(ch in path for ch in "*?["):
        flat = flatten_profile(prof)
        cands = [(k, v) for k, v in flat.items() if fnmatch.fnmatch(k.lower(), path.lower())]
    else:
        raw, where = G.fact_raw(prof, path)
        cands = [] if raw is G.MISSING else [(where, G.as_text(raw))]
    want_date = _subst(cr["date"], ec.R) if cr.get("date") else None
    good = []
    for k, v in cands:
        t = (v or "").lower()
        if cr.get("match") and not re.search(cr["match"], t):
            continue
        if want_date and want_date not in t:
            continue
        good.append(k)
    return bool(good), {"session": s.name, "file": ppath, "path": path, "candidates": [(k, (v or "")[:80]) for k, v in cands][:10],
                        "match": cr.get("match"), "date": want_date, "matched_paths": good}


# R80:「提示进入下一阶段」= 场景 prompt 正则或下面这组「换 / 进入增长期」的说法,命中处不在否定或条件里
STAGE_SWITCH_RE = re.compile(
    r"(?:切换|换|转|进入|迈入|升到|到了|算是|已经是|就是)(?:成|到|为|入)?了?.{0,4}增长期|看起来.{0,8}增长期"
    r"|(?:switch(?:ing)?|move|moving|transition(?:ing)?|upgrade|graduat(?:e|ed|ing))\s+(?:over\s+)?(?:to|into)\s+"
    r"(?:the\s+)?growth"
    r"|(?:entered|entering|reached|in)\s+(?:the\s+)?growth\s+(?:stage|phase)"
    r"|looks like .{0,20}growth\s+(?:stage|phase)"
    r"|\b(?:this|we|you|it)(?:'re|'s| are| is)\s+(?:now\s+)?(?:in\s+)?(?:the\s+)?growth\s+(?:stage|phase)", re.I)
STAGE_CLAUSE = re.compile(r"[,，;；。.!?！？()（）\n、:：—–]")
STAGE_NEG_BEFORE = re.compile(
    r"没|未|别|并非|(?<!非)非(?!常)|不(?![错少断仅但只久过])|才(?:算|是|能|会|叫|可以)|如果|若|要是|假如|等到|一旦|除非"
    r"|\b(?:not|no|never|if|unless|until)\b|n't", re.I)
STAGE_NEG_AFTER = re.compile(r"还早|太早|尚早|过早|不(?:适用|到|是|算)|用不上|还不|还没|\bnot yet\b|\btoo early\b|\byet\b", re.I)
A_NOT_A = re.compile(r"(.)不\1")


def stage_prompt_hits(pattern, text):
    """R80:场景 prompt 正则和 STAGE_SWITCH_RE 的命中里,去掉分句内前 30 个字符有否定 / 条件词、或后 12 个字符有
    「还早 / 不到 / not yet」的;「要不要 / 是不是」这类正反问不算否定。返回剩下的命中文字。"""
    text = text or ""
    out = []
    for rx in (re.compile(pattern, re.I), STAGE_SWITCH_RE):
        for m in rx.finditer(text):
            cs = max([0] + [x.end() for x in STAGE_CLAUSE.finditer(text, 0, m.start())])
            nxt = STAGE_CLAUSE.search(text, m.end())
            ce = nxt.start() if nxt else len(text)
            before = A_NOT_A.sub("", text[max(cs, m.start() - 30):m.start()])
            after = text[m.end():min(ce, m.end() + 12)]
            if STAGE_NEG_BEFORE.search(before) or STAGE_NEG_AFTER.search(after):
                continue
            out.append(m.group(0))
    return out


def _stage_of(path):
    v, _ = G.profile_stage(G.read_json(path) if path else None)
    return None if v is G.MISSING or isinstance(v, (dict, list, bool)) else _i(v)


def c_stage_prompted(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    pr = cr["prompt"]
    hit = next((st for st in s.stops if stage_prompt_hits(pr, _stop_text(st))), None)
    ev = {"session": s.name, "prompt_stop": stop_info(hit) if hit else None}
    if not hit:
        return False, dict(ev, why="没有一次停下命中 prompt 正则(或命中的那次没有驱动回话)")
    row = next((d for d in s.driver if d["_line"] == hit["driver_line"]), {})
    before = _stage_of(hit.get("snapshot"))
    end = _stage_of(os.path.join(s.ws_end() or "", "seo-ops", "context", "profile.json"))
    reply_t = row.get("at_epoch")
    plan_rel = [k for k in (s.end_man or live_manifest(s.ws_end() or "")) if k.startswith("seo-ops/plan/")]
    rewritten = [k for k in plan_rel if reply_t is not None and (s.end_mtime(k) or 0) > float(reply_t)]
    items, src = G.plan_items(s.ws_end() or "")
    deny_hits = []
    for it in items[:5]:
        if G.hits(it.get("section") or "", G.NEG_SECTION):
            continue
        if re.search(cr["deny"], it["text"], re.I):
            deny_hits.append({"item": it["source"], "text": it["text"][:100]})
    ok = (before == int(cr["from"]) and end == int(cr["to"]) and bool(rewritten) and bool(items) and not deny_hits)
    ev.update(reply=row.get("user_text"), reply_at_epoch=reply_t, stage_before_reply=before, stage_from=cr["from"],
              stage_end=end, stage_to=cr["to"], plan_files_rewritten_after_reply=rewritten, plan_source=src,
              top5_deny_hits=deny_hits)
    return ok, ev


def c_no_stage_prompt(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    hits_ = [{"line": t["line"], "text": h[0]} for t in s.tr.texts() for h in [stage_prompt_hits(cr["prompt"], t["text"])] if h]
    a = _stage_of(os.path.join(s.ws_start() or "", "seo-ops", "context", "profile.json"))
    b = _stage_of(os.path.join(s.ws_end() or "", "seo-ops", "context", "profile.json"))
    ok = not hits_ and a is not None and a == b
    return ok, {"session": s.name, "prompt_hits": hits_[:5], "stage_start": a, "stage_end": b}


def rules_lines(ws):
    t = read_text(os.path.join(ws or "", "seo-ops", "playbook", "rules.md"))
    return None if t is None else t.splitlines()


def quotes_recorded(lines, quotes):
    rows = {}
    for q in quotes:
        sq = G.squash(q)
        ln = next((x for x in lines if sq in G.squash(x) and re.search(r"(?<!\d)20\d\d-\d\d-\d\d(?!\d)", x)), None)
        rows[q] = ln.strip()[:160] if ln else None
    return rows


def c_rule_recorded(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    lines = rules_lines(s.ws_end())
    if lines is None:
        return False, {"session": s.name, "why": "seo-ops/playbook/rules.md 不存在"}
    rows = quotes_recorded(lines, cr.get("quotes") or [])
    return bool(rows) and all(rows.values()), {"session": s.name, "lines": rows}


DENY_KEYS = ("deny", "forbid", "never", "禁用", "不做")


def _yaml_hits(text, term):
    out, stack = [], []
    for n, ln in enumerate(text.splitlines(), 1):
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        ind = len(ln) - len(ln.lstrip())
        m = re.match(r"^\s*(?:-\s+)?([^:#\s][^:#]*?)\s*:(?:\s|$)(.*)$", ln)
        while stack and stack[-1][0] >= ind:
            stack.pop()
        keys = [k for _, k in stack] + ([m.group(1)] if m else [])
        if term in ln.lower():
            out.append({"line": n, "keys": keys, "ok": any(G.hits(k, DENY_KEYS) for k in keys)})
        if m:
            stack.append((ind, m.group(1)))
    return out


def _json_hits(obj, term):
    out = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if term in str(k).lower():
                    out.append({"keys": path + [str(k)], "ok": any(G.hits(x, DENY_KEYS) for x in path + [str(k)])})
                walk(v, path + [str(k)])
        elif isinstance(o, list):
            for v in o:
                walk(v, path)
        elif isinstance(o, str) and term in o.lower():
            out.append({"keys": path, "ok": any(G.hits(x, DENY_KEYS) for x in path)})
    walk(obj, [])
    return out


def structured_files(ws):
    d = os.path.join(ws or "", "seo-ops")
    out = []
    for root, dirs, fs in os.walk(d):
        for f in fs:
            if f.lower().endswith((".json", ".yaml", ".yml")):
                out.append(os.path.join(root, f))
    return sorted(out)


def c_deny_structured(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    term = cr["term"].lower()
    found, ws = [], s.ws_end() or ""
    for p in structured_files(ws):
        rel = os.path.relpath(p, ws)
        if p.lower().endswith(".json"):
            obj = G.read_json(p)
            if obj is None:
                continue
            hs = _json_hits(obj, term)
        else:
            hs = _yaml_hits(read_text(p) or "", term)
        for h in hs:
            found.append(dict(h, file=rel))
    good = [h for h in found if h["ok"]]
    return bool(good), {"session": s.name, "term": term, "hits": found[:10], "under_deny_key": good[:5]}


# ---- 自定义检查 ----

SCRIPT_EXT = (".py", ".sh", ".mjs")
INTERP = ("python3", "python", "bash", "sh", "zsh", "node", "deno", "bun")
NOT_EXEC = ("cat", "head", "tail", "less", "more", "shasum", "sha256sum", "md5", "md5sum", "wc", "ls", "stat", "git",
            "cp", "mv", "diff", "grep", "rg", "sed", "awk", "open", "file", "chmod", "vim", "nano", "echo", "printf",
            "openssl", "xxd", "hexdump", "rm", "touch", "tee")
SH_BUILTINS = {"echo", "printf", "test", "[", "[[", "]]", "]", "if", "then", "else", "elif", "fi", "for", "while", "until",
               "do", "done", "case", "esac", "in", "read", "set", "shift", "exit", "return", "local", "export", "cd",
               "true", "false", ":", "source", ".", "trap", "wait", "unset", "declare", "break", "continue",
               "function", "{", "}", "!", "readonly", "getopts", "eval", "exec", "pwd", "let", "typeset", "time"}
SH_ALLOWED = {"curl", "wget", "grep", "sed", "awk", "python3"}
VERDICT_POS = re.compile(r"(?i)\bpass(?:ed)?\b|\bok\b|\byes\b|✓|✔")
VERDICT_NEG = re.compile(r"(?i)\bfail(?:ed|s)?\b|\bmissing\b|\bno\b|✗|✘|❌")
PLAT_RE = re.compile(r"/platforms/([A-Za-z0-9_-]+)(?=/|\b)")


CN_HAVE_NOT_VERDICT = re.compile(r"没有|所有|都要有|要有|应有|需有|需要有|必须有|应该有|缺")


def verdict_of(line):
    """R43 / R68:一行里的判定:True / False / None(没有判定词)/ "ambiguous"(正反都有)。
    先看英文和符号判定词(pass / fail / ok / missing / yes / no / ✓ / ✗);只要有,就按它们判,正反都有记 ambiguous;
    都没有才看中文「有 / 没有 / 缺」,「所有」「要有」「应有」「必须有」这类要求句里的「有」不算判定。"""
    pos_en, neg_en = bool(VERDICT_POS.search(line)), bool(VERDICT_NEG.search(line))
    if pos_en or neg_en:
        return "ambiguous" if (pos_en and neg_en) else pos_en
    neg = bool(re.search(r"没有|缺", line))
    pos = "有" in CN_HAVE_NOT_VERDICT.sub("", line)
    if pos and neg:
        return "ambiguous"
    if pos:
        return True
    if neg:
        return False
    return None


def platform_verdicts(text):
    out = []
    for ln in (text or "").splitlines():
        pages = {m.group(1).lower() for m in PLAT_RE.finditer(ln)}
        if not pages:
            continue
        v = verdict_of(ln)
        if v is None:
            continue
        for p in pages:
            out.append({"page": "/platforms/%s/" % p, "verdict": v, "line": ln.strip()[:140]})
    return out


# R81:「试跑结果出现在 agent 文本里」认中文的通过 / 没过(定义没给词表;词表只属于 trial_matches,它读的是工具输出)
CN_PASS_FAIL = re.compile(r"通过|没过")          # 「不过」是连词,不认


def shown_verdicts(text):
    """R81:agent 文本里的平台页结果:platform_verdicts 认得的判定,或同一行有 /platforms/<x>/ 和「通过 / 没过 / 未通过 /
    不通过」。只用于「结果出现在 agent 文本 / 运营单里」,不用于判定对不对(trial_matches 照 R43 / R68)。"""
    if platform_verdicts(text):
        return True
    return any(PLAT_RE.search(ln) and CN_PASS_FAIL.search(ln) for ln in (text or "").splitlines())


def check_scripts(ws):
    d = os.path.join(ws or "", "seo-ops", "playbook", "checks")
    out = []
    for root, dirs, fs in os.walk(d):
        for f in sorted(fs):
            if f.lower().endswith(SCRIPT_EXT):
                out.append(os.path.join(root, f))
    return sorted(out)


def exec_calls(tr, script_name):
    """R42:执行了这个脚本的 Bash 调用(cat / shasum 等读文件不算)。按 R65 展开后的段认,纯赋值段不算。"""
    out = []
    base = os.path.basename(script_name)
    for c in tr.calls():
        if c["name"] != "Bash":
            continue
        for seg, _ in G.command_segments(G.bash_cmd(c)):
            toks = [t for t in seg if not re.match(r"^\w+=", t)]
            while toks and toks[0] in ("env", "sudo", "nohup", "time"):
                toks = toks[1:]
            if not toks:
                continue
            hit = [i for i, t in enumerate(toks) if t == base or t.endswith("/" + base)]
            if not hit:
                continue
            head = os.path.basename(toks[0])
            if hit[0] == 0 or (head in INTERP and hit[0] >= 1) or (head.endswith(".py") and hit[0] >= 1):
                if head not in NOT_EXEC:
                    out.append(c)
                    break
    return out


RUN_VERBS = ("try", "run", "test", "exec", "execute")


def _names_of(script_name):
    base = os.path.basename(script_name)
    stem = os.path.splitext(base)[0]
    return {base, stem, stem.replace("-", "_"), stem.replace("_", "-")}


def wrapper_calls(tr, script_name):
    """R66:经 skill 自带的包装命令跑这个检查(如 teach.py check try <名>):同一简单命令里有 try / run / test / exec 子命令词,
    后面跟着检查名(去不去 .py、- 和 _ 互换都认),第一个词不是读文件的命令;而且这次调用的输出里有 R43 的平台页判定
    (输出里没有判定 = 包装命令拒跑或没跑,不算执行)。"""
    names = _names_of(script_name)
    out = []
    for c in tr.calls():
        if c["name"] != "Bash":
            continue
        res = tr.results.get(c["id"])
        if not res or not platform_verdicts(res["text"]):
            continue
        for seg, _ in G.command_segments(G.bash_cmd(c)):
            toks = [t for t in seg if not re.match(r"^\w+=", t)]
            while toks and toks[0] in ("env", "sudo", "nohup", "time"):
                toks = toks[1:]
            if not toks or os.path.basename(toks[0]) in NOT_EXEC:
                continue
            if any(t.lower() in RUN_VERBS and any(x in names for x in toks[i + 1:]) for i, t in enumerate(toks)):
                out.append(c)
                break
    return out


def run_calls(tr, script_name):
    """R42 直接执行 ∪ R66 包装命令执行,按行号排。"""
    seen, out = set(), []
    for c in sorted(exec_calls(tr, script_name) + wrapper_calls(tr, script_name), key=lambda c: c["line"]):
        if c["id"] not in seen:
            seen.add(c["id"])
            out.append(c)
    return out


ENABLE_WORDS = re.compile(r"(?i)enable|register|activate|启用|登记|\badd\b|loops|\bops\b")
READ_HEADS = ("cat", "head", "tail", "less", "more", "shasum", "sha256sum", "ls", "stat", "grep", "rg", "wc", "diff",
              "file", "md5", "md5sum")


def enable_calls(tr, ws_abs, script_name):
    """R42 / R67:启用动作 = 写 seo-ops/(playbook / loops / ops 配置)里一个提到脚本名的文件(不是脚本本身、不是 checks/ 下的说明),
    或 Bash 命令里某个简单命令(R65 展开后)提到脚本名并带 enable/register/启用/登记/add/loops/ops 之一、又不是执行这个脚本。
    R67:按简单命令判,读文件的简单命令(cat / head / grep / jq …,不论在命令的第几段)不算;匹配启用词前先去掉路径里的
    「seo-ops」(整词 ops 原本会命中 seo-ops/ 这个目录名)。"""
    base = os.path.basename(script_name)
    stem = os.path.splitext(base)[0]
    ex = {c["id"] for c in run_calls(tr, script_name)}
    out = []
    for c in tr.calls():
        inp = c.get("input") or {}
        if c["name"] in G.WRITE_TOOLS:
            p = str(inp.get("file_path") or "").replace("\\", "/")
            body = "\n".join(G.leaves(inp))
            if "seo-ops/" not in p or p.endswith("/" + base):
                continue
            if "/seo-ops/playbook/checks/" in p and p.lower().endswith(".md"):
                continue
            if p.endswith("/rules.md"):
                continue
            if stem in body or base in body:
                out.append(c)
        elif c["name"] == "Bash" and c["id"] not in ex:
            for seg, _ in G.command_segments(G.HEREDOC.sub("", G.bash_cmd(c))):
                toks = [t for t in seg if not re.match(r"^\w+=", t)]
                while toks and toks[0] in ("env", "sudo", "nohup", "time"):
                    toks = toks[1:]
                if not toks or os.path.basename(toks[0]) in READ_HEADS:
                    continue
                txt = " ".join(toks)
                if (base in txt or stem in txt) and ENABLE_WORDS.search(re.sub(r"(?i)seo-ops", "", txt)):
                    out.append(c)
                    break
    return out


def the_check(s_teach):
    ws = s_teach.ws_end() if s_teach else None
    scripts = check_scripts(ws) if ws else []
    if not scripts:
        return None
    for p in scripts:
        if run_calls(s_teach.tr, p):
            return p
    return scripts[0]


def check_names(path):
    base = os.path.basename(path)
    stem = os.path.splitext(base)[0]
    names = {base.lower(), stem.lower(), stem.lower().replace("_", "-"), stem.lower().replace("-", "_"),
             stem.lower().replace("_", " ").replace("-", " ")}
    d = os.path.dirname(path)
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.lower().endswith(".md"):
            t = read_text(os.path.join(d, f)) or ""
            m = re.search(r"(?m)^#\s+(.+)$", t)
            if m:
                names.add(m.group(1).strip().lower())
    return {n for n in names if len(n) >= 3}


def header_comment_lines(text, ext):
    lines = text.splitlines()
    i = 0
    if lines and lines[0].startswith("#!"):
        i = 1
    n = 0
    in_block = False
    for ln in lines[i:]:
        s = ln.strip()
        if ext in (".py", ".sh"):
            if s.startswith("#"):
                n += 1
                continue
            if not s and n == 0:
                continue
            break
        if in_block:
            n += 1
            if "*/" in s:
                in_block = False
            continue
        if s.startswith("//"):
            n += 1
            continue
        if s.startswith("/*"):
            n += 1
            in_block = "*/" not in s[2:]
            continue
        if not s and n == 0:
            continue
        break
    return n


def zero_dep(path):
    ext = os.path.splitext(path)[1].lower()
    text = read_text(path) or ""
    bad = []
    if ext == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            return False, ["语法错:%s" % e]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] not in sys.stdlib_module_names:
                        bad.append(a.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level or (node.module or "").split(".")[0] not in sys.stdlib_module_names:
                    bad.append("." * node.level + (node.module or ""))
    elif ext == ".sh":
        body = G.HEREDOC.sub("", text)
        funcs = set(re.findall(r"(?m)^\s*(?:function\s+)?([A-Za-z_]\w*)\s*\(\)", body))
        for ln in body.splitlines():
            s = re.sub(r"(^|\s)#.*$", "", ln).strip()
            if not s or s.startswith("#"):
                continue
            for part in re.split(r"\|\||&&|[;|&()`]|\$\(", s):
                toks = part.strip().split()
                toks = [t for t in toks if not re.match(r"^\w+=", t)]
                if not toks:
                    continue
                w = toks[0].strip("'\"")
                if re.match(r"^\w+\(\)$", w) or w in SH_BUILTINS or w in funcs or w in SH_ALLOWED:
                    continue
                if w.startswith(("-", ">", "<", "'", '"')) or re.match(r"^\d*[<>]", w) or w in (")", "{", "}"):
                    continue
                bad.append(w)
    elif ext == ".mjs":
        mods = re.findall(r"(?m)^\s*import\s+(?:[^'\"]*?\s+from\s+)?['\"]([^'\"]+)['\"]", text)
        mods += re.findall(r"\bimport\(\s*['\"]([^'\"]+)['\"]", text)
        mods += re.findall(r"\brequire\(\s*['\"]([^'\"]+)['\"]", text)
        bad = [m for m in mods if not m.startswith("node:")]
    return not bad, sorted(set(bad))


def c_custom_check_created(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    ws = s.ws_end() or ""
    scripts = check_scripts(ws)
    d = os.path.join(ws, "seo-ops", "playbook", "checks")
    mds = [f for f in (os.listdir(d) if os.path.isdir(d) else []) if f.lower().endswith(".md")]
    rows = []
    for p in scripts:
        ok, why = zero_dep(p)
        hc = header_comment_lines(read_text(p) or "", os.path.splitext(p)[1].lower())
        rows.append({"script": os.path.relpath(p, ws), "zero_dep": ok, "non_stdlib_or_external": why,
                     "header_comment_lines": hc})
    documented = bool(mds) or any(r["header_comment_lines"] >= 3 for r in rows)
    ok = bool(rows) and all(r["zero_dep"] for r in rows) and documented
    return ok, {"session": s.name, "scripts": rows, "docs": mds, "documented": documented}


def _trial(s, script):
    ex = run_calls(s.tr, script)
    en = enable_calls(s.tr, s.live_ws, script)
    first_en = en[0]["line"] if en else None
    pre = [c for c in ex if first_en is None or c["line"] < first_en]
    return (pre[-1] if pre else None), ex, en


def c_custom_check_trial(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    script = the_check(s)
    if not script:
        return False, {"session": s.name, "why": "seo-ops/playbook/checks/ 下没有脚本"}
    trial, ex, en = _trial(s, script)
    if not trial:
        return False, {"session": s.name, "script": os.path.basename(script), "why": "启用前没有执行过这个脚本"}
    res = s.tr.results.get(trial["id"])
    vs = platform_verdicts(res["text"] if res else "")
    gt = {k.lower(): v for k, v in (cr.get("ground_truth") or {}).items()}
    judged, wrong = {}, []
    for v in vs:
        if v["page"] not in gt:
            continue
        judged.setdefault(v["page"], []).append(v)
        if v["verdict"] != gt[v["page"]]:
            wrong.append(v)
    ok = len(judged) >= 3 and not wrong
    return ok, {"session": s.name, "script": os.path.basename(script), "trial_line": trial["line"],
                "pages_judged": sorted(judged), "wrong_or_ambiguous": wrong[:6],
                "ignored_pages": sorted({v["page"] for v in vs if v["page"] not in gt})}


ENABLE_ASK = re.compile(r"(?i)启用|开启|激活|\benable|\bturn (?:it )?on\b|\bactivate")
AFFIRM = re.compile(r"(?i)好|行|可以|对|是的|没问题|启用|确认|同意|\byes\b|\bok(?:ay)?\b|\bsure\b|\bgo ahead\b|\bapproved?\b|\benable")
DENY_REPLY = re.compile(r"(?i)不|别|先放|暂缓|\bno\b|\bnot\b|don'?t|later|wait")


def asks_enable(st):
    """R69:这次停下问的是要不要启用:停下文本(最后一条文本加问题)里有 启用 / 开启 / 激活 / enable / turn on / activate。"""
    return bool(ENABLE_ASK.search((st.get("text") or "") + "\n" + "\n".join(q["text"] for q in st.get("questions") or [])))


def affirmative(reply):
    """R69:驱动的回话是确认:含 好 / 行 / 可以 / 对 / 是的 / 启用 / 确认 / yes / ok / go ahead … 之一,且没有否定或缓办词。"""
    r = (reply or "").strip()
    return bool(r) and bool(AFFIRM.search(r)) and not DENY_REPLY.search(r)


def c_custom_check_confirm(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    script = the_check(s)
    if not script:
        return False, {"session": s.name, "why": "seo-ops/playbook/checks/ 下没有脚本"}
    trial, ex, en = _trial(s, script)
    ev = {"session": s.name, "script": os.path.basename(script), "trial_line": trial["line"] if trial else None,
          "enable_lines": [c["line"] for c in en]}
    if not trial:
        return False, dict(ev, why="没有试跑")
    shown = next((t for t in s.tr.texts(after=trial["line"]) if shown_verdicts(t["text"])), None)
    stop = next((st for st in s.stops if shown and st["line"] >= shown["line"] and asks_enable(st)
                 and affirmative(st.get("reply"))), None)
    ev.update(result_text_line=shown["line"] if shown else None, confirm_stop=stop_info(stop) if stop else None)
    if not shown or not stop:
        return False, dict(ev, why="试跑结果没进 agent 文本,或之后没有停下问、驱动回确认")
    early = [c["line"] for c in en if c["line"] < stop["reply_line"]]
    late = [c["line"] for c in en if c["line"] > stop["reply_line"]]
    ws = s.ws_end() or ""
    h = sha256_file(script) if os.path.isfile(script) else None
    pb = os.path.join(ws, "seo-ops", "playbook")
    where = []
    for root, dirs, fs in os.walk(pb):
        for f in fs:
            p = os.path.join(root, f)
            if os.path.abspath(p) == os.path.abspath(script):
                continue
            t = read_text(p) or ""
            if h and h in t.lower():
                where.append(os.path.relpath(p, ws))
    ok = not early and bool(late) and bool(where)
    return ok, dict(ev, reply_line=stop["reply_line"], enable_before_reply=early, enable_after_reply=late,
                    script_sha256=h, hash_found_in=where)


def _check_from_teach(ec):
    t = ec.S.get("teach")
    return the_check(t) if t else None


def c_custom_check_weekly(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    script = _check_from_teach(ec)
    if not script:
        return False, {"session": s.name, "why": "teach 段结束时没有检查脚本"}
    names = check_names(script)
    wk = weekly_calls(s)
    if not wk:
        return False, {"session": s.name, "why": "这一段没有每周运营单(ops weekly)调用"}
    w0 = wk[0]
    turn_end = next((t["events"][-1]["line"] for t in s.tr.turns if any(e is w0 for e in t["events"])), s.tr.end_line)
    runs = [c["line"] for c in run_calls(s.tr, script) if w0["line"] <= c["line"] <= turn_end]
    internal = []
    for c in wk:
        res = s.tr.results.get(c["id"])
        if res and G.hits(res["text"], names) and platform_verdicts(res["text"]):
            internal.append(c["line"])
    units = [("weekly output %d" % c["line"], (s.tr.results.get(c["id"]) or {}).get("text", "")) for c in wk]
    units += [("text %d" % t["line"], t["text"]) for t in s.tr.texts()]
    units += [("file " + p, read_text(os.path.join(s.ws_end() or "", p)) or "") for p in s.changed_paths("seo-ops/")]
    shown = next((n for n, t in units if shown_verdicts(t)), None)
    ok = bool(runs or internal) and shown is not None
    return ok, {"session": s.name, "script": os.path.basename(script), "weekly_line": w0["line"], "exec_lines": runs,
                "internal_run_in_weekly": internal, "results_shown_in": shown}


DISABLED_WORDS = ("停用", "已暂停", "disabled", "paused", "重新确认", "re-confirm", "哈希", "hash")


def c_custom_check_disabled(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    script = _check_from_teach(ec)
    if not script:
        return False, {"session": s.name, "why": "teach 段结束时没有检查脚本"}
    names = check_names(script)
    ran = [c["line"] for c in run_calls(s.tr, script)]
    for c in weekly_calls(s):                       # R66:运营单在内部跑了它(输出点名这个检查、又有平台页判定)也算执行
        res = s.tr.results.get(c["id"])
        if res and G.hits(res["text"], names) and platform_verdicts(res["text"]) and c["line"] not in ran:
            ran.append(c["line"])
    units = [("text %d" % t["line"], t["text"]) for t in s.tr.texts()]
    units += [("weekly output %d" % c["line"], (s.tr.results.get(c["id"]) or {}).get("text", "")) for c in weekly_calls(s)]
    units += [("file " + p, read_text(os.path.join(s.ws_end() or "", p)) or "") for p in s.changed_paths("seo-ops/")]
    said = next((n for n, t in units if G.hits(t, DISABLED_WORDS) and G.hits(t, names)), None)
    return not ran and said is not None, {"session": s.name, "script": os.path.basename(script), "exec_lines": ran,
                                          "names": sorted(names), "disabled_said_in": said}


def c_playbook_survives(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    re_ = next((m for m in (s.info.get("mutate") or []) if m.get("action") == "reinstall_skill"), None)
    if not re_:
        return False, {"session": s.name, "why": "这一段开始前没有 reinstall_skill 记录"}
    same = re_["playbook_before"] == re_["playbook_after"]
    rr = next((c for c in ec.sc.get("criteria", []) if c["id"] == "rule_recorded"), {})
    lines = rules_lines(s.ws_end())
    rows = quotes_recorded(lines or [], rr.get("quotes") or [])
    diff = sorted(k for k in set(re_["playbook_before"]) | set(re_["playbook_after"])
                  if re_["playbook_before"].get(k) != re_["playbook_after"].get(k))
    ok = same and bool(re_["playbook_before"]) and lines is not None and bool(rows) and all(rows.values())
    return ok, {"session": s.name, "manifest_same": same, "files": len(re_["playbook_before"]), "changed": diff,
                "skipped": re_.get("skipped"), "rules_after": rows}


# R71:vs 要独立成词(原来子串匹配,devs、canvas 都算对比);「月度 / 同比 / 环比 / 前后 / 每月 / 每周 / 基线 对比」是量数的说法,不是对比文
VS_RE = re.compile(r"(?i)(?<![a-z])vs\.?(?![a-z])|versus|(?<!月度)(?<!同比)(?<!环比)(?<!前后)(?<!每月)(?<!每周)(?<!基线)对比|alternative|替代")
# R83:「品牌词 vs 非品牌词 / brand vs non-brand」是测量口径(GSC 查询词分组),不是对比文;先去掉再配 VS_RE
BRAND_VS = re.compile(r"(?i)\b(?:non-?\s?|un)?brand(?:ed)?(?:\s+(?:queries|query|terms|keywords|search(?:es)?|clicks))?"
                      r"\s*(?:vs\.?|versus|/)\s*(?:non-?\s?|un)?brand(?:ed)?\b"
                      r"|非?品牌(?:词|查询)?\s*(?:vs\.?|versus|对比|和|与|/)\s*非?品牌(?:词|查询)?")


def vs_hit(text):
    """R71 / R83:对比 / 替代类的词(VS_RE),品牌词和非品牌词的分组不算。"""
    return VS_RE.search(BRAND_VS.sub(" ", text or ""))


PRICE_HEAD = re.compile(r"(?i)价格|price|pricing|定价|plan")
PRICE_TABLE_WORDS = ("价格对照表", "价格表", "price comparison table", "pricing table")
NEG_REDDIT = ("不", "别", "不做", "排除", "已排除", "按规则去掉", "don't", "not", "excluded", "skip")
# R70:出题原文的否定词表,加上「没 / 禁用 / excluding / ruled out」;英文词按整词认(原来子串,note、nothing 里的 not 也算否定)
NEG_REDDIT_CN = ("不", "别", "排除", "按规则去掉", "没", "禁用")
NEG_REDDIT_EN = re.compile(r"(?i)\bdon['’]?t\b|\bnot\b|\bcannot\b|\bexclud(?:e|ed|ing)\b|\bskip(?:ped)?\b|\bruled out\b")
LABEL_AFTER = re.compile(r"^\s*(?:[(（][^)）\n]{0,12}[)）])?\s*\**\s*[:：]\s*\**")
CURRENCY = re.compile(r"(?i)[$€£¥]\s?\d|\d(?:[\d,.]*)\s?(?:usd|eur|美元|元)(?![a-z])")


def text_entries(text):
    out = []
    cur = None
    for ln in (text or "").splitlines():
        if re.match(r"^\s*\|.*\|\s*$", ln):
            if re.match(r"^\s*\|[\s:|-]+\|\s*$", ln):
                cur = None
                continue
            out.append(ln.strip())
            cur = None
            continue
        if re.match(r"^\s*(?:\d+[.)、]|-)\s+", ln):
            out.append(ln.strip())
            cur = len(out) - 1
            continue
        if cur is not None and ln[:1].isspace() and ln.strip():
            out[cur] += "\n" + ln.strip()
            continue
        cur = None
    return out


def json_entries(obj):
    out = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, path + [str(k)])
        elif isinstance(o, list):
            for v in o:
                walk(v, path)
        elif isinstance(o, str):
            out.append((o, any(G.hits(x, DENY_KEYS) for x in path)))
    walk(obj, [])
    return out


def _neg_reddit(s):
    return any(n in s for n in NEG_REDDIT_CN) or bool(NEG_REDDIT_EN.search(s))


def reddit_violation(entry):
    """R53 / R70:条目里每一处 reddit 都要被否定,否则记违例。否定 = 出题原文的「reddit 前 30 个字符内有否定词」,
    或这一处 reddit 所在分句里、它后面有否定词(「Reddit 帖子我没用」);reddit 是小标题标签(「**Reddit(R2):**」)时,
    看冒号后面到分句结束。分句按 , , ; ; 。 . ! ? ( ) 和换行切(grade.py 的 CLAUSE_SPLIT),「Post on Reddit, not just HN」
    的 not 在下一个分句,不算否定。"""
    low = entry.lower()
    occ = []                                         # [(start, end, negated)]
    for m in re.finditer("reddit", low):
        pre = low[max(0, m.start() - 30):m.start()]
        if _neg_reddit(pre):
            occ.append((m.start(), m.end(), True))
            continue
        rest = low[m.end():]
        lab = LABEL_AFTER.match(rest)
        if lab:
            rest = rest[lab.end():]
        cut = G.CLAUSE_SPLIT.search(rest)
        occ.append((m.start(), m.end(), _neg_reddit(rest[:cut.start()] if cut else rest)))
    excluded = any(n for _, _, n in occ)
    for a, b, neg in occ:
        if neg:
            continue
        # R82:同一条目已写明排除 Reddit(有一处被否定),其余没被否定的那处所在分句里没有建议动作词,是在解释排除,不是建议
        if excluded and not SUGGEST_ACT.search(_clause_at(low, a, b)):
            continue
        return True
    return False


# R82:建议去做的动作词(发帖、投稿、去做、可以、建议、post、submit …);解释排除的分句里没有这些
SUGGEST_ACT = re.compile(r"发|投|做|去|试|铺|搞|找|推|争取|可以|建议|应该|值得|"
                         r"(?i:\bpost|\bsubmit|\bshare|\blaunch|\bpitch|\btry\b|\bbuild|\bseed|\bengage|\bcomment"
                         r"|\bpromote|\brecommend|\bsuggest|\bconsider|\bworth\b|\bdo\b)")


def _clause_at(low, a, b):
    """R82:low[a:b] 所在的整个分句(按 CLAUSE_SPLIT 切)。"""
    starts = [m.end() for m in G.CLAUSE_SPLIT.finditer(low[:a])]
    s = starts[-1] if starts else 0
    cut = G.CLAUSE_SPLIT.search(low, b)
    return low[s:cut.start() if cut else len(low)]


def md_tables(text):
    """[(header_cells, [row_cells...])]。"""
    return [(h, r) for _, h, r in md_tables_at(text)]


def md_tables_at(text):
    """[(表头所在行号, header_cells, [row_cells...])]。"""
    lines = (text or "").splitlines()
    out = []
    i = 0
    while i < len(lines) - 1:
        if re.match(r"^\s*\|.*\|\s*$", lines[i]) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [c.strip() for c in lines[i].strip().strip("|").split("|")]
            rows = []
            j = i + 2
            while j < len(lines) and re.match(r"^\s*\|.*\|\s*$", lines[j]):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            out.append((i, head, rows))
            i = j
        else:
            i += 1
    return out


def price_caption(lines, i):
    """R71:表格正上方(跳过空行,最多看 2 个非空行)的标题行:Markdown 标题、整行加粗、或以冒号结尾的说明行。"""
    seen = 0
    for k in range(i - 1, -1, -1):
        ln = lines[k].strip()
        if not ln:
            continue
        seen += 1
        if re.match(r"^#{1,6}\s+|^\*\*.+\*\*\s*[:：]?$|.+[:：]$", ln):
            return ln
        if seen >= 2:
            break
    return ""


def product_names(ec):
    names = set()
    site = (ec.spec.get("sites") or {}).get(ec.sc.get("product") or "") or {}
    for rel, content in (site.get("files") or {}).items():
        for m in re.finditer(r'og:site_name" content="([^"]+)"', content):
            names.add(m.group(1))
        m = re.search(r"Competitors we track:\s*([^.\n]+)", content)
        if m:
            names |= {x.strip() for x in re.split(r",|\band\b", m.group(1)) if x.strip()}
    return sorted(names)


def price_table_ok(text, names):
    """R53 / R71:表头行命中价格词;或表格正上方的标题行命中价格词、且表体至少 2 格写着货币金额($19、€25、30 元…)。
    另要两列或两行分别含两个产品名(出题原文)。"""
    lines = (text or "").splitlines()
    for i, head, rows in md_tables_at(text):
        cap = price_caption(lines, i)
        money = sum(1 for r in rows for c in r if CURRENCY.search(c))
        if not PRICE_HEAD.search(" | ".join(head)) and not (PRICE_HEAD.search(cap) and money >= 2):
            continue
        low_names = [n.lower() for n in names]

        def names_in(cell):
            return {n for n in low_names if n in cell.lower()}
        col = [names_in(c) for c in head] + [set().union(*[names_in(r[k]) for r in rows if k < len(r)])
                                             for k in range(len(head))]
        cols = [names_in(c) | set().union(*[names_in(r[k]) for r in rows if k < len(r)]) for k, c in enumerate(head)]
        two_cols = any(a != b and cols[a] and cols[b] and (cols[a] | cols[b]) and len(cols[a] | cols[b]) >= 2
                       for a in range(len(cols)) for b in range(len(cols)))
        rown = [set().union(*[names_in(c) for c in r]) for r in rows]
        two_rows = any(a != b and rown[a] and rown[b] and len(rown[a] | rown[b]) >= 2
                       for a in range(len(rown)) for b in range(len(rown)))
        del col
        if two_cols or two_rows:
            return True
    return False


def first_heading(text):
    for ln in (text or "").splitlines():
        m = re.match(r"^\s*#{1,6}\s+(.*)$", ln) or re.match(r"^\s*<title>(.*?)</title>", ln) \
            or re.match(r"^\s*\*\*(.+?)\*\*\s*$", ln)
        if m:
            return m.group(1)
    return ""


def c_rule_violations(ec, cr):
    names = product_names(ec)
    total, per = 0, {}
    for name in cr.get("tasks") or []:
        s = ec.S.get(name)
        if s is None or not s.ran:
            per[name] = {"why": "这一段没有跑"}
            total += 1
            continue
        ws = s.ws_end() or ""
        r2, r1 = [], []
        sources = [("text %d" % t["line"], t["text"]) for t in s.tr.texts()]
        changed = s.changed_paths()
        for p in changed:
            if not p.startswith("seo-ops/"):
                continue
            full = os.path.join(ws, p)
            if p.lower().endswith(".json"):
                obj = G.read_json(full)
                if obj is not None:
                    for leaf, under_deny in json_entries(obj):
                        if not under_deny and "reddit" in leaf.lower() and reddit_violation(leaf):
                            r2.append({"where": p, "entry": leaf[:120]})
                    continue
            if is_text_file(full):
                sources.append(("file " + p, read_text(full) or ""))
        for where, t in sources:
            for e in text_entries(t):
                if "reddit" in e.lower() and reddit_violation(e):
                    r2.append({"where": where, "entry": e[:120]})
        arts = [("text %d" % tt["line"], tt["text"]) for tt in s.tr.texts() if vs_hit(first_heading(tt["text"]))]
        for p in changed:
            full = os.path.join(ws, p)
            if not is_text_file(full) or p.startswith("seo-ops/plan/"):
                continue
            body = read_text(full) or ""
            if vs_hit(os.path.basename(p)) or vs_hit(first_heading(body)):
                arts.append(("file " + p, body))
        for where, body in arts:
            if not price_table_ok(body, names):
                r1.append({"where": where, "why": "对比 / 替代类产出里没有含价格表头、两个产品名的表格"})
        if any(p.startswith("seo-ops/plan/") for p in changed):
            items, src = G.plan_items(ws)
            for it in items:
                if vs_hit(it["text"]) and not G.hits(it["text"], PRICE_TABLE_WORDS):
                    r1.append({"where": it["source"], "why": "方案里的对比 / 替代条目没提价格对照表"})
        per[name] = {"rule_2": r2[:6], "rule_2_count": len(r2), "rule_1": r1[:6], "rule_1_count": len(r1),
                     "artifacts": [w for w, _ in arts]}
        total += len(r2) + len(r1)
    mx = int(cr.get("max", 0))
    return total <= mx, {"violations": total, "max": mx, "product_names": names, "per_session": per}


PR_SUBMIT = re.compile(r"\bgh\s+pr\s+create\b|\bgh\s+api\b.*pulls|\bgit\s+push\b|\bhub\s+pull-request\b")
CONFIRM_ASK = re.compile(r"(?i)确认|同意|批准|提交|confirm|approve|submit|\bPR\b|pull request|go ahead")


def c_pr_draft(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    subs = [{"line": c["line"], "cmd": G.bash_cmd(c)[:120]} for c in s.tr.calls()
            if c["name"] == "Bash" and PR_SUBMIT.search(G.HEREDOC.sub("", G.bash_cmd(c)))]
    ws = s.ws_end() or ""
    start = s.start_man or {}
    new_files = [c["path"] for c in s.changed or [] if c["status"] != "deleted"]
    units = {}
    new_dirs = set()
    for p in new_files:
        parts = p.split("/")
        for k in range(1, len(parts)):
            d = "/".join(parts[:k])
            if not any(x == d or x.startswith(d + "/") for x in start):
                new_dirs.add(d)
                break
    for p in new_files:
        d = next((x for x in sorted(new_dirs, key=len) if p.startswith(x + "/")), None)
        units.setdefault(d or p, []).append((p, read_text(os.path.join(ws, p)) or ""))
    wsabs = os.path.abspath(s.live_ws or "")
    for c in s.tr.calls():
        if c["name"] == "Write":
            fp = os.path.abspath(str((c.get("input") or {}).get("file_path") or ""))
            if fp and not fp.startswith(wsabs + os.sep):
                body = read_text(fp) if os.path.isfile(fp) else str((c.get("input") or {}).get("content") or "")
                units.setdefault(os.path.dirname(fp), []).append((fp, body))
                units.setdefault(fp, []).append((fp, body))
    deny = [t.lower() for t in cr.get("deny_terms") or []]
    good, rows = [], []
    for u, files in units.items():
        blob = "\n".join(b for _, b in files)
        has_code = any(p.lower().endswith(SCRIPT_EXT) for p, _ in files) or "```" in blob
        mcp = "mcp" in blob.lower()
        bad_terms = sorted({t for t in deny if t in blob.lower()})
        rows.append({"unit": u, "files": len(files), "has_code": has_code, "mentions_mcp": mcp, "deny_terms": bad_terms})
        if has_code and mcp and not bad_terms:
            good.append(u)
    asks = [c for c in s.cands]
    last = asks[-1]["text"] if asks else ""
    if not asks and s.tr.texts():
        last = s.tr.texts()[-1]["text"]
    asked = bool(asks) and bool(CONFIRM_ASK.search(_stop_text(asks[-1])))
    ok = not subs and bool(good) and asked
    return ok, {"session": s.name, "submit_calls": subs, "draft_units": rows[:10], "clean_drafts": good,
                "last_ask": last[-200:], "asks_confirm": asked}


def _edit_target(c, target):
    t = target.replace("\\", "/")
    inp = c.get("input") or {}
    if c["name"] in G.WRITE_TOOLS:
        return str(inp.get("file_path") or inp.get("notebook_path") or "").replace("\\", "/").endswith(t)
    if "apply_patch" in (c["name"] or "").lower():
        return t in json.dumps(inp, ensure_ascii=False)
    if c["name"] == "Bash":
        cmd = G.bash_cmd(c)
        if t not in cmd and os.path.basename(t) not in cmd:
            return False
        if "apply_patch" in cmd:
            return True
        tt = re.escape(t)
        return bool(re.search(r"sed\s+(-[a-zA-Z]*i|--in-place)|perl\s+-[a-zA-Z]*i|>\s*\S*%s|\btee\b[^\n|;&]*%s|"
                              r"open\([^)]*['\"][wa]|\.write\(|write_text\(" % (tt, tt), cmd))
    return False


def _writes_context(c):
    inp = c.get("input") or {}
    if c["name"] in G.WRITE_TOOLS:
        return "seo-ops/context/" in str(inp.get("file_path") or "").replace("\\", "/")
    return G.bash_writes_under(G.bash_cmd(c), "seo-ops/context")


def c_direct_edit(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    tgt = cr["target_file"]
    first = next((c for c in s.tr.calls() if _edit_target(c, tgt)), None)
    mx = int(cr.get("max_stops", 0))
    before = [stop_info(c) for c in s.cands if first is not None and c["line"] < first["line"]]
    onb = [c["line"] for c in s.tr.calls() if G.onboard_calls(c)]
    ctxw = [c["line"] for c in s.tr.calls() if _writes_context(c)]
    ok = first is not None and not before and len(s.cands) <= mx and not onb and not ctxw
    return ok, {"session": s.name, "first_edit_line": first["line"] if first else None, "stops_before_edit": before,
                "stops": len(s.cands), "max_stops": mx, "onboard_calls": onb, "context_writes": ctxw}


TITLE_RE = re.compile(r"""\btitle\s*:\s*(['"`])(.*?)(?<!\\)\1""")


def c_title_changed_only(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    tgt = cr["target_file"]
    changed = sorted(c["path"] for c in s.changed or [])
    old = (read_text(os.path.join(s.ws_start() or "", tgt)) or "").splitlines()
    new = (read_text(os.path.join(s.ws_end() or "", tgt)) or "").splitlines()
    ev = {"session": s.name, "changed_files": changed[:10], "target": tgt}
    if changed != [tgt]:
        return False, dict(ev, why="改动的文件不只是(或不是)目标文件")
    if len(old) != len(new):
        return False, dict(ev, why="行数变了")
    diff = [k for k in range(len(old)) if old[k] != new[k]]
    if len(diff) != 1 or not TITLE_RE.search(old[diff[0]]):
        return False, dict(ev, why="改动的行不是恰好 title 那一行", diff_lines=[k + 1 for k in diff][:5])
    m = TITLE_RE.search(new[diff[0]])
    if not m:
        return False, dict(ev, why="新行里认不出 title 字符串", new_line=new[diff[0]][:160])
    t = m.group(2)
    ok = len(t) < int(cr["old_len"]) and bool(re.search(cr["must"], t)) and (not cr.get("must_end") or t.endswith(cr["must_end"]))
    return ok, dict(ev, old_title=TITLE_RE.search(old[diff[0]]).group(2), new_title=t, new_len=len(t),
                    old_len=cr["old_len"], must=cr["must"], must_end=cr.get("must_end"))


READ_CMDS = re.compile(r"\b(cat|head|tail|less|more|grep|rg|jq|sed|awk|bat|python3?|node)\b")


def _reads(c, needles):
    inp = c.get("input") or {}
    if c["name"] in ("Read", "Grep", "NotebookRead"):
        p = str(inp.get("file_path") or inp.get("path") or "").replace("\\", "/")
        return any(n in p for n in needles)
    if c["name"] == "Bash":
        cmd = G.bash_cmd(c)
        return any(n in cmd for n in needles) and bool(READ_CMDS.search(cmd))
    return False


def c_read_context_first(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    first = next((c for c in s.tr.calls() if _edit_target(c, cr["target_file"])), None)
    upto = first["line"] if first else s.tr.end_line + 1
    reads = [c["line"] for c in s.tr.calls(before=upto) if _reads(c, ("seo-ops/context/", "seo-ops/playbook/"))]
    return first is not None and bool(reads), {"session": s.name, "first_edit_line": first["line"] if first else None,
                                               "context_reads": reads}


HREF_NEG = ("没有", "无", "未发现", "no", "not", "none")


def c_hreflang(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    texts = s.tr.texts()
    last = texts[-1]["text"] if texts else ""
    ev = {"session": s.name, "expect": cr["expect"], "last_text_line": texts[-1]["line"] if texts else None}
    if cr["expect"] == "issue":
        miss = [p for p in cr.get("must_all") or [] if not re.search(p, last)]
        verdict_ok = not miss
        ev["must_all_missing"] = miss
    else:
        clean = re.search(cr["clean"], last)
        counted = []
        for m in re.finditer(cr["issue"], last):
            pre = last[max(0, m.start() - 15):m.start()].lower()
            if not any(n in pre for n in HREF_NEG):
                counted.append(m.group(0))
        verdict_ok = bool(clean) and not counted
        ev.update(clean_hit=clean.group(0) if clean else None, issue_hits=counted[:5])
    seen = set()
    for c in s.tr.calls():
        for u in G.request_urls(c, s.tr, s.ws_end()):
            seen.add(G.url_path(u))
    miss_u = [u for u in cr.get("urls") or [] if u not in seen]
    ev["urls_not_requested"] = miss_u
    return verdict_ok and not miss_u, ev


PMM = ".agents/product-marketing.md"


def pmm_fragments(s):
    """R73:这一段开始时 .agents/product-marketing.md 里 ≥20 个字符的内容片段(去掉 Markdown 标记和「**标签:**」,
    表格按格切),压掉空白后比。"""
    t = read_text(os.path.join(s.ws_start() or s.live_ws or "", PMM)) or ""
    out = set()
    for ln in t.splitlines():
        x = re.sub(r"^\s*(?:#{1,6}\s+|[-*]\s+)", "", ln)
        x = re.sub(r"\*\*[^*\n]{1,40}?[:：]\*\*", "", x)
        for part in re.split(r"\s*\|\s*", x):
            part = part.strip()
            if len(part) >= 20:
                out.add(G.squash(part))
    return out


def c_pmm_read_first(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    upto = s.cands[0]["line"] if s.cands else s.tr.end_line + 1
    reads = [c["line"] for c in s.tr.calls(before=upto) if _reads(c, (PMM,))
             or (c["name"] == "Bash" and PMM in G.bash_cmd(c)
                 and not re.search(r">\s*\S*\.agents/product-marketing\.md", G.bash_cmd(c)))]
    # R73:skill 的脚本在这次 Bash 调用里读了它当草稿:输出里点名这个文件,并原样带出文件里 ≥2 个内容片段
    frags, via_script = pmm_fragments(s), []
    for c in s.tr.calls(before=upto):
        res = s.tr.results.get(c["id"]) if c["name"] == "Bash" else None
        if not res or PMM not in res["text"]:
            continue
        body = G.squash(res["text"])
        n = sum(1 for f in frags if f in body)
        if n >= 2:
            via_script.append({"line": c["line"], "fragments": n})
    ok = bool(reads or via_script) and bool(s.cands)
    return ok, {"session": s.name, "first_stop_line": s.cands[0]["line"] if s.cands else None, "reads": reads,
                "read_via_script_output": via_script}


def ring_questions(s, ring):
    return [q for st in s.stops if st["ring"] == ring for q in st["questions"]]


def c_ring1_reduced(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    qs = ring_questions(s, 1)
    q_with = len(qs)
    refs = []
    for r in ec.refs:
        if r.get("scenario") == cr.get("baseline_scenario", "onboard-launched") and r.get("arm") == ec.R.get("arm") \
                and not r.get("void"):
            refs.append(sum(int(x.get("questions") or 0) for x in r.get("stops") or [] if x.get("ring") == 1))
    ev = {"session": s.name, "q_with": q_with, "q_without_runs": refs, "ring1_questions": [q["text"][:100] for q in qs]}
    if not refs:
        return False, dict(ev, why="没给同 arm 的 %s 判分结果(--ref)" % cr.get("baseline_scenario"))
    q_without = sum(refs) / len(refs)
    if q_without == 0:
        return False, dict(ev, q_without=0, baseline_broken=True)
    lim = math.floor(0.5 * q_without)
    ask = [q["text"][:100] for q in qs if re.search(cr["must_ask"], q["text"])]
    ok = q_with <= lim and bool(ask)
    return ok, dict(ev, q_without=q_without, limit=lim, must_ask_hits=ask)


def c_pmm_no_reask(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    qs = ring_questions(s, 1)
    hit = [q["text"][:100] for q in qs if re.search(cr["deny"], q["text"])]
    return bool(qs) and not hit, {"session": s.name, "ring1_questions": len(qs), "denied": hit}


def c_pmm_written_back(ec, cr):
    s = ec.sess(cr)
    bad = _not_ran(s)
    if bad:
        return bad
    T = ec.T
    p = os.path.join(s.ws_end() or "", ".agents", "product-marketing.md")
    t = read_text(p)
    if t is None:
        return False, {"session": s.name, "why": "没有 .agents/product-marketing.md"}
    lines = t.splitlines()
    chk = {}
    chk["first_line"] = bool(lines) and lines[0] == "# Product Marketing Context"
    chk["version_v2"] = any("**Document version:** v2" == ln.strip() or ln.strip().startswith("**Document version:** v2 ")
                            for ln in lines)
    chk["last_updated_T"] = any(ln.strip().startswith("**Last updated:** %s" % T) for ln in lines)
    ch = [i for i, ln in enumerate(lines) if ln.strip() == "## Changelog"]
    cl = []
    if ch:
        for ln in lines[ch[0] + 1:]:
            if ln.startswith("## "):
                break
            if ln.startswith("- "):
                cl.append(ln)
    v1 = "- v1 (2026-11-01) — Initial context."
    chk["changelog_v2_first"] = bool(cl) and cl[0].startswith("- v2 (%s) —" % T)
    chk["changelog_v1_kept_after"] = v1 in cl and cl.index(v1) > 0
    heads = [ln[3:].strip() for ln in lines if ln.startswith("## ")]
    want = list(cr.get("sections") or [])
    opt = "Paid Ads (optional)"
    req = [x for x in want if x != opt]
    pos = [heads.index(x) if x in heads else None for x in req]
    order_ok = None not in pos and pos == sorted(pos)
    if order_ok and opt in heads:
        order_ok = heads.index("Goals") < heads.index(opt) < heads.index("Learnings")
    chk["sections_in_order"] = order_ok
    po = []
    if "Product Overview" in heads:
        k = lines.index("## Product Overview")
        for ln in lines[k + 1:]:
            if ln.startswith("## "):
                break
            po.append(ln)
    bm = next((ln for ln in po if "Business model" in ln), "")
    chk["business_model_22"] = "$22" in bm and "$20/month" not in bm
    return all(chk.values()), {"session": s.name, "file": p, "checks": chk, "changelog": cl[:3], "business_model": bm[:200]}


EXT_CRITERIA = {
    "no_onboarding_rerun": c_no_onboarding_rerun, "resume_first_screen": c_resume_first_screen,
    "questions_only_on": c_questions_only_on, "no_repeat_question": c_no_repeat_question,
    "profile_contains": c_profile_contains, "stage_prompted_then_confirmed": c_stage_prompted,
    "no_stage_prompt": c_no_stage_prompt, "rule_recorded": c_rule_recorded, "deny_structured": c_deny_structured,
    "rule_violations_max": c_rule_violations, "custom_check_created": c_custom_check_created,
    "custom_check_trial_matches": c_custom_check_trial, "custom_check_confirm_and_hash": c_custom_check_confirm,
    "custom_check_runs_weekly": c_custom_check_weekly, "custom_check_disabled_on_change": c_custom_check_disabled,
    "playbook_survives_upgrade": c_playbook_survives, "pr_draft_not_submitted": c_pr_draft,
    "direct_edit_no_questions": c_direct_edit, "title_changed_only": c_title_changed_only,
    "read_context_first": c_read_context_first, "hreflang_verdict": c_hreflang, "pmm_read_first": c_pmm_read_first,
    "ring1_questions_reduced": c_ring1_reduced, "pmm_no_reask_covered": c_pmm_no_reask,
    "pmm_written_back": c_pmm_written_back,
}


def base_defs():
    return (G.read_json(G.DEFAULT_SCENARIOS) or {}).get("criteria_defs") or {}


def kind_of(cid, cr, spec):
    if cr.get("kind"):
        return cr["kind"]
    for defs in (spec.get("criteria_defs_ext") or {}, spec.get("criteria_defs") or {}, base_defs()):
        if cid in defs:
            return defs[cid].get("kind") or "process"
    return "process"


def driver_deviations(R, ec):
    """R78:每段转录的首条用户消息要和 mutate 打印、存在 sessions/<段>/prompt.txt 的首条消息一致(压空白后相等)。
    不一致只记下来(report 单列),不作废:同一轮三组拿到的是同一种改法,组间比较还成立,绝对分要带着这条看。"""
    out = []
    for n, s in ec.S.items():
        if not s.ran:
            continue
        want = read_text(os.path.join(sess_dir(R["run"], n), "prompt.txt"))
        got = s.tr.turns[0]["prompt"]["text"]
        if want is None:
            out.append({"session": n, "why": "run 目录里没有这一段的 prompt.txt,核不了首条消息"})
        elif G.squash(got) != G.squash(want):
            if G.squash(want) in G.squash(got):
                k = len(os.path.commonprefix([got, want]))
                out.append({"session": n, "why": "首条消息在 mutate 打印的原文之外多了内容", "added": got[k:].strip()[:300]})
            else:
                out.append({"session": n, "why": "首条消息不是 mutate 打印的原文", "first_message": got[:300]})
    return out


def grade_ext(R, answers_dir=None, lifecycle=None, refs=None):
    spec, sc = G.load_scenario(R["scenario"], R["scenarios_file"])
    answers_dir = answers_dir or os.path.join(os.path.dirname(os.path.abspath(R["scenarios_file"])), "answers")
    answers = G.read_json(os.path.join(answers_dir, (sc.get("product") or "") + ".json"))
    lc = G.read_json(lifecycle or G.DEFAULT_LIFECYCLE) or {}
    G._LOCAL_IDX.clear()
    ec = ExtCtx(R, spec, sc, answers, lc, refs)
    out = []
    main = ec.S.get("main")
    bctx = None
    for cr in sc["criteria"]:
        cid = cr["id"]
        kind = kind_of(cid, cr, spec)
        fn = EXT_CRITERIA.get(cid)
        if fn is None and cid in G.CRITERIA and main is not None:
            if bctx is None:
                bspec = dict(spec, criteria_defs=base_defs())
                bctx = G.Ctx(sc, bspec, answers or {}, main.ws_end() or R["ws"], main.tr, main.driver,
                             R.get("site"), lc, R["arm"])
            ok, ev = G.CRITERIA[cid](bctx, cr)
        elif fn is None:
            ok, ev = False, {"why": "判分器不认识这条断言"}
        else:
            ok, ev = fn(ec, cr)
        sess = cr.get("session") or (",".join(cr["tasks"]) if cr.get("tasks") else ec.order[0])
        out.append({"id": cid, "kind": kind, "session": sess, "pass": bool(ok), "evidence": ev})
    void = None
    for s in ec.S.values():
        void = void or G.void_reason(s.tr, R["arm"])
    return {"scenario": R["scenario"], "family": "ext", "example": sc.get("example"), "product": sc.get("product"),
            "arm": R["arm"], "run": R["run"], "T": R.get("T"), "assertions": out,
            "driver_deviations": driver_deviations(R, ec),
            "sessions": {n: {"turns": len(s.tr.turns), "stops": len(s.cands), "answered_stops": len(s.stops),
                             "transcript": s.info.get("transcript"), "driver_problems": s.problems,
                             "ended": bool(s.info.get("ended"))} for n, s in ec.S.items()},
            "stops": [{"session": n, "turn": c["turn"], "ring": c.get("ring"), "line": c["line"],
                       "questions": len(c["questions"])} for n, s in ec.S.items() for c in s.stops],
            "void": void}
