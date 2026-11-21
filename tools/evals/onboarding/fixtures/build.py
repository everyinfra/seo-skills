#!/usr/bin/env python3
"""把 fixtures/gold/*.json(手写的标准答案)展开成判分器要的三样东西:工作区 seo-ops/、转录 JSONL、驱动日志 JSONL。

gold 文件是「模板」:手写档案、方案、每一环的停下文本;模拟用户的回话按场景文件的 simulated_user 顺序取,
确认调用(onboard answer --ring N … --quote「回话前 14 个字」--confirm)由这里补上。也可以直接写 turns(显式回合)。
转录按 Claude Code 子代理 JSONL 的真实格式写:assistant / user 行、tool_use / tool_result 块,续跑的用户回话是
isMeta + origin.kind=coordinator 的行(SendMessage 续跑的格式);另外掺几行 attachment、api-request-blob 重放和
系统通知,判分器必须忽略它们。

  expand(gold) → 显式结构(反例就是在这一步之后改几处)
  materialize(explicit, out_dir) → {"ws","transcript","driver_log","site","scenarios"}
"""
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ONB = os.path.dirname(HERE)
SKILL = "/skill/seo-suite/scripts"


def load(name):
    with open(os.path.join(HERE, "gold", name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def scenario_of(g):
    path = os.path.join(HERE, g["scenarios_file"]) if g.get("scenarios_file") else os.path.join(ONB, "scenarios.json")
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    return path, next(s for s in spec["scenarios"] if s["id"] == g["scenario"])


def confirm_event(ring, reply, extra=""):
    q = reply.strip()[:14].replace('"', "")
    return {"bash": 'python3 %s/onboard.py answer --ring %d --set a=b%s --quote "%s" --confirm' % (SKILL, ring, extra, q),
            "out": "第 %d 环记答案 1 条,确认。" % ring}


def expand(g):
    """模板 → 显式回合。"""
    g = copy.deepcopy(g)
    path, sc = scenario_of(g)
    ex = {k: g.get(k) for k in ("scenario", "site", "profile", "profile_ring1", "plan_json", "plan_md", "diagnosis",
                                "plan_files")}
    ex["scenarios"] = path
    if g.get("turns"):
        ex["turns"] = g["turns"]
        for t in ex["turns"]:
            if t.get("reply") and "text" not in t["reply"]:
                r = t["reply"]
                r["text"] = sc["simulated_user"][str(r["ring"])][r.get("index", 0)]
        return ex
    turns = []
    t1 = {"events": list(g.get("first_events") or []) + [{"text": g["first_screen"]}],
          "reply": {"ring": 1, "text": sc["simulated_user"]["1"][0]}}
    turns.append(t1)
    for r in range(2, 7):
        prev = turns[-1]["reply"]
        evs = [confirm_event(r - 1, prev["text"]),
               {"bash": "python3 %s/onboard.py show --ring %d" % (SKILL, r), "out": "# 开局第 %d 环" % r}]
        evs += (g.get("ring_events") or {}).get(str(r), [])
        evs.append({"text": g["ring_texts"][str(r)]})
        turns.append({"events": evs, "reply": {"ring": r, "text": sc["simulated_user"][str(r)][0]}})
    last = turns[-1]["reply"]
    turns.append({"events": [confirm_event(6, last["text"])] + list(g.get("final_events") or []) +
                  [{"text": g["final_text"]}], "reply": None})
    ex["turns"] = turns
    return ex


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def materialize(ex, out):
    ws = os.path.join(out, "ws")
    ctx = os.path.join(ws, "seo-ops", "context")
    plan = os.path.join(ws, "seo-ops", "plan")
    os.makedirs(ctx, exist_ok=True)
    os.makedirs(plan, exist_ok=True)
    if ex.get("profile") is not None:
        _write_json(os.path.join(ctx, "profile.json"), ex["profile"])
    if ex.get("diagnosis") is not None:
        _write_json(os.path.join(ctx, "diagnosis.json"), ex["diagnosis"])
    if ex.get("plan_json") is not None:
        _write_json(os.path.join(plan, "plan.json"), ex["plan_json"])
    if ex.get("plan_md") is not None:
        with open(os.path.join(plan, "plan.md"), "w", encoding="utf-8") as f:
            f.write(ex["plan_md"])
    snap_src = ex.get("profile_ring1") if ex.get("profile_ring1") is not None else ex.get("profile")
    lines, drv = [], []
    seq = [0]

    def add(d):
        seq[0] += 1
        d.setdefault("timestamp", "2026-11-21T10:%02d:%02d.000Z" % (seq[0] // 60 % 60, seq[0] % 60))
        d.setdefault("isSidechain", True)
        d.setdefault("uuid", "u%05d" % seq[0])
        lines.append(d)

    _, sc = scenario_of({"scenario": ex["scenario"], "scenarios_file": os.path.relpath(ex["scenarios"], HERE)
                         if os.path.dirname(ex["scenarios"]) == HERE else None})
    first_prompt = sc["prompt"].replace("{base}", ex.get("site") or "")
    call_no = [0]
    for n, t in enumerate(ex["turns"], 1):
        if n == 1:
            add({"type": "user", "message": {"role": "user", "content": first_prompt}, "userType": "external"})
            add({"type": "attachment", "attachment": {"type": "skill_listing"}})
            add({"type": "api-request-blob", "message": {"role": "user", "content": [{"type": "text", "text": first_prompt}]}})
        else:
            prev = ex["turns"][n - 2]["reply"]
            add({"type": "user", "isMeta": True, "origin": {"kind": "coordinator"},
                 "message": {"role": "user", "content": "The coordinator sent a message while you were working:\n" + prev["text"]}})
            add({"type": "user", "message": {"role": "user", "content": "[SYSTEM NOTIFICATION - NOT USER INPUT]\nbackground task done"}})
        for ev in t["events"]:
            if "text" in ev:
                add({"type": "assistant", "message": {"id": "m%05d" % seq[0], "role": "assistant",
                                                      "content": [{"type": "text", "text": ev["text"]}]}})
                continue
            call_no[0] += 1
            cid = "toolu_%04d" % call_no[0]
            if "bash" in ev:
                name, inp = "Bash", {"command": ev["bash"]}
            else:
                name, inp = ev["tool"], ev.get("input") or {}
            block = {"type": "tool_use", "id": cid, "name": name, "input": inp}
            add({"type": "assistant", "message": {"id": "m%05d" % seq[0], "role": "assistant", "content": [block]}})
            add({"type": "api-request-blob", "message": {"role": "assistant", "content": [block]}})
            res = {"type": "tool_result", "tool_use_id": cid, "content": ev.get("out", "ok")}
            if ev.get("error"):
                res["is_error"] = True
            add({"type": "user", "message": {"role": "user", "content": [res]}})
        if t.get("reply"):
            snap = None
            if snap_src is not None:
                snap = os.path.join(out, "snapshots", "turn%02d.profile.json" % n)
                _write_json(snap, snap_src)
            drv.append({"turn": n, "ring": t["reply"]["ring"], "user_text": t["reply"]["text"], "source": "script",
                        "at": "2026-11-21T10:00:%02dZ" % n, "profile_snapshot": snap})
    tr = os.path.join(out, "transcript.jsonl")
    with open(tr, "w", encoding="utf-8") as f:
        for d in lines:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    dl = os.path.join(out, "driver.jsonl")
    with open(dl, "w", encoding="utf-8") as f:
        for d in drv:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return {"ws": ws, "transcript": tr, "driver_log": dl, "site": ex.get("site"), "scenarios": ex["scenarios"]}


if __name__ == "__main__":
    import sys
    g = load(sys.argv[1])
    print(json.dumps(materialize(expand(g), sys.argv[2]), ensure_ascii=False))
