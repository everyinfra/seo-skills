#!/usr/bin/env python3
"""第 5 批扩展场景的合成校准数据:在真的 run 目录里「演」被测会话,判分器读到的东西和真跑一样。

做法和 build.py 一样是「模板 → 显式结构 → 落盘」,只是多了段:
  setup(真 setup 子命令建站、建工作区;有 base 的先造一个合成 W0)
  → 每段:grade.mutate(真 mutate:动作、git 提交、开始快照、首条提示词)
  → 每回合:把这回合的工具调用和文本按 Claude Code 子代理 JSONL 格式追加进转录、把这回合「agent 写的文件」落到工作区,
    再调真 next 判停下、取回话、写驱动日志;回话作为下一回合的 coordinator 消息写进转录;next 说 end 就收段(结束快照)。
模板里的字符串可以用 {ws} {base} {T} {reply} {quote}({reply} 是上一条驱动回话,{quote} 是它的前 14 个字)。
回合不够时补「好的。」直到 next 说 end。期望值来自 scenarios_ext.json 的断言原文,不来自任何 skill 的输出。
"""
import copy
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ONB = os.path.dirname(HERE)
if ONB not in sys.path:
    sys.path.insert(0, ONB)
import grade as G  # noqa: E402

sys.modules.setdefault("grade", G)
import grade_ext as E  # noqa: E402

EXT = os.path.join(ONB, "scenarios_ext.json")
T = "2026-11-25"
SK = "/skill/seo-suite/scripts"
LIFECYCLE = os.path.join(HERE, "lifecycle_calib.json")


class Tx:
    """转录写手:和 build.py 的格式一致(attachment、api-request-blob 重放、系统通知都掺进去)。"""

    def __init__(self, path):
        self.path = path
        self.seq = 0
        self.calls = 0
        open(path, "a").close()

    def add(self, d):
        self.seq += 1
        d.setdefault("timestamp", "2026-11-25T10:%02d:%02d.000Z" % (self.seq // 60 % 60, self.seq % 60))
        d.setdefault("isSidechain", True)
        d.setdefault("uuid", "%s-%05d" % (os.path.basename(os.path.dirname(self.path)), self.seq))
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    def first(self, text):
        self.add({"type": "user", "message": {"role": "user", "content": text}, "userType": "external"})
        self.add({"type": "attachment", "attachment": {"type": "skill_listing"}})

    def reply(self, text):
        self.add({"type": "user", "isMeta": True, "origin": {"kind": "coordinator"},
                  "message": {"role": "user", "content": "The coordinator sent a message while you were working:\n" + text}})
        self.add({"type": "user", "message": {"role": "user", "content": "[SYSTEM NOTIFICATION - NOT USER INPUT]\nok"}})

    def events(self, evs):
        tag = os.path.basename(os.path.dirname(self.path))
        for ev in evs:
            if "text" in ev:
                self.add({"type": "assistant", "message": {"id": "m-%s-%05d" % (tag, self.seq), "role": "assistant",
                                                           "content": [{"type": "text", "text": ev["text"]}]}})
                continue
            self.calls += 1
            cid = "toolu_%s_%04d" % (tag, self.calls)
            if "bash" in ev:
                name, inp = "Bash", {"command": ev["bash"]}
            else:
                name, inp = ev["tool"], ev.get("input") or {}
            apply_tool(name, inp)
            block = {"type": "tool_use", "id": cid, "name": name, "input": inp}
            self.add({"type": "assistant", "message": {"id": "m-%s-%05d" % (tag, self.seq), "role": "assistant",
                                                       "content": [block]}})
            self.add({"type": "api-request-blob", "message": {"role": "assistant", "content": [block]}})
            res = {"type": "tool_result", "tool_use_id": cid, "content": ev.get("out", "ok")}
            if ev.get("error"):
                res["is_error"] = True
            self.add({"type": "user", "message": {"role": "user", "content": [res]}})


def apply_tool(name, inp):
    """Write / Edit 调用在转录里出现的同时落到磁盘(路径是绝对路径)。"""
    if name == "Write":
        E.write_text(inp["file_path"], inp.get("content", ""))
    elif name == "Edit":
        p = inp["file_path"]
        s = E.read_text(p)
        if s is None or inp["old_string"] not in s:
            raise AssertionError("Edit 找不到要改的内容:%s" % p)
        E.write_text(p, s.replace(inp["old_string"], inp["new_string"], 1))


def fill(x, env):
    if isinstance(x, str):
        for k, v in env.items():
            x = x.replace("{%s}" % k, str(v))
        return x
    if isinstance(x, list):
        return [fill(v, env) for v in x]
    if isinstance(x, dict):
        return {k: fill(v, env) for k, v in x.items()}
    return x


def apply_files(ws, files, env):
    for rel, content in (files or {}).items():
        rel = fill(rel, env)
        p = rel if os.path.isabs(rel) else os.path.join(ws, rel)
        if content is None:
            if os.path.exists(p):
                os.remove(p)
            continue
        if callable(content):
            content = content(ws, env)
        if isinstance(content, (dict, list)):
            content = json.dumps(fill(content, env), ensure_ascii=False, indent=1)
        else:
            content = fill(content, env)
        E.write_text(p, content)


def run_session(run, name, turns, install_from=None, max_extra=4):
    b = E.begin_session(run, name, install_from)
    R = E.load_run(run)
    sd = E.sess_dir(run, name)
    tx = Tx(os.path.join(sd, "transcript.jsonl"))
    tx.first(b["prompt"])
    env = {"ws": R["ws"], "base": (R.get("base") or "").rstrip("/"), "T": R["T"], "reply": "", "quote": ""}
    queue = list(turns)
    extra = 0
    while True:
        if queue:
            t = queue.pop(0)
        else:
            extra += 1
            if extra > max_extra:
                raise AssertionError("段 %s:回合用完了 next 还在回话" % name)
            t = {"events": [{"text": "好的。"}]}
        apply_files(R["ws"], t.get("files"), env)
        tx.events(fill(t.get("events") or [], env))
        r = E.drive_next_ext(run, name, tx.path)
        if r["action"] == "end":
            if queue:
                raise AssertionError("段 %s:next 提前结束,还剩 %d 回合" % (name, len(queue)))
            return tx.path
        if r["action"] != "reply":
            raise AssertionError("段 %s:%s" % (name, r))
        env["reply"] = r["user_text"]
        env["quote"] = r["user_text"].strip()[:14].replace('"', "")
        tx.reply(r["user_text"])


def make_skill(d, version):
    E.write_text(os.path.join(d, "SKILL.md"), "---\nname: seo-suite\ndescription: test skill %s\n---\n# test\n" % version)
    E.write_text(os.path.join(d, "VERSION"), version + "\n")
    return d


def make_w0(base_sid, out, port, seo_ops, extra_files=None):
    """合成 W0:真 setup 建 base 场景的站和工作区,再放进「开局跑完」时的 seo-ops/,收段、打包。"""
    run = os.path.join(out, "base-" + base_sid)
    E.setup_run(base_sid, "skill", run, port, None, None, None, None, T)
    R = E.load_run(run)
    E.begin_session(run, "main")
    apply_files(R["ws"], seo_ops, {"ws": R["ws"], "base": R["base"], "T": T})
    apply_files(R["ws"], extra_files or {}, {"ws": R["ws"], "base": R["base"], "T": T})
    E.end_session(run, "main")
    w0 = os.path.join(out, "w0-%s.tgz" % base_sid)
    E.pack_w0(run, w0)
    return w0


def materialize(fx, out, w0_cache=None):
    """fx = {"scenario", "w0": {...} | None, "sessions": {段: [回合]}, "skill": bool}。返回 run 目录。
    w0_cache = {base 场景: W0 路径}:同一个 base 只造一次(和真评测「同一个 base 只跑一次」一致)。"""
    fx = copy.deepcopy(fx)
    os.makedirs(out, exist_ok=True)
    w0 = None
    if fx.get("w0"):
        w = fx["w0"]
        w0 = (w0_cache or {}).get(w["base"])
        if not w0:
            w0 = make_w0(w["base"], out, fx.get("port", 8899), w["seo_ops"], w.get("extra"))
            if w0_cache is not None:
                w0_cache[w["base"]] = w0
    run = os.path.join(out, "run")
    skill_src = make_skill(os.path.join(out, "skill-old"), "old") if fx.get("skill") else None
    E.setup_run(fx["scenario"], fx.get("arm", "skill"), run, fx.get("port", 8899), EXT, skill_src, skill_src, w0, T)
    new_skill = make_skill(os.path.join(out, "skill-new"), "new") if fx.get("skill") else None
    R = E.load_run(run)
    for name in R["session_order"]:
        turns = fx["sessions"].get(name)
        if turns is None:
            continue
        run_session(run, name, turns, new_skill)
    return run


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# 合成档案(Northfold Coffee 的事实取自 answers/launched.json;日期是合成的)
# ---------------------------------------------------------------------------

def launched_profile(stage=2, confirmed="2026-11-20", lines=None, pricing="Subscription from $22/month"):
    return {"_schema": {"stage": "stage.id"}, "stage": {"id": stage, "confirmed_at": confirmed},
            "confirmed_at": confirmed,
            "facts": {"product.name": {"value": "Northfold Coffee", "status": "confirmed"},
                      "product.lines": {"value": lines or ["Single-origin coffee bags", "Monthly coffee subscription",
                                                           "Pour-over gear"], "status": "confirmed"},
                      "pricing.model": {"value": pricing, "status": "confirmed"},
                      "customers": {"value": ["US home brewers"], "status": "confirmed"}}}


LAUNCHED_PLAN = {"items": [
    {"title": "Submit the sitemap in Search Console and Bing", "week": 1},
    {"title": "Fix titles on product pages", "week": 1},
    {"title": "Write a V60 ratio brew guide", "week": 2}]}

GROWTH_PLAN = {"items": [
    {"title": "Build a brew-guide topic cluster around pour-over ratios", "week": 1},
    {"title": "Track subscription conversions from organic landing pages in GA4", "week": 1},
    {"title": "Refresh product pages with roast-date proof", "week": 2},
    {"title": "Compare subscription page against competitors", "week": 3},
    {"title": "Add FAQ schema to the subscription page", "week": 3}]}


def w0_launched():
    return {"base": "onboard-launched", "seo_ops": {
        "seo-ops/context/profile.json": launched_profile(),
        "seo-ops/plan/plan.json": LAUNCHED_PLAN,
        "seo-ops/plan/plan.md": "# Plan\n\n1. Submit the sitemap (week 1)\n2. Fix titles (week 1)\n"}}


def weekly(out="本周运营单:3 项"):
    return {"bash": "python3 %s/ops.py weekly" % SK, "out": out}


# ---------------------------------------------------------------------------
# 事件小工具(路径一律相对工作区,{ws} 由 fill 换成绝对路径)
# ---------------------------------------------------------------------------

def W(rel, content):
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False, indent=1)
    return {"tool": "Write", "input": {"file_path": "{ws}/" + rel, "content": content}, "out": "File written"}


def ED(rel, old, new):
    return {"tool": "Edit", "input": {"file_path": "{ws}/" + rel, "old_string": old, "new_string": new}, "out": "ok"}


def RD(rel, out="(file contents)"):
    return {"tool": "Read", "input": {"file_path": "{ws}/" + rel}, "out": out}


def BS(cmd, out="ok"):
    return {"bash": cmd, "out": out}


def TX(text):
    return {"text": text}


def turn(*events):
    return {"events": list(events)}


def confirm(ring):
    return BS('python3 %s/onboard.py answer --ring %d --set a=b --quote "{quote}" --confirm' % (SK, ring),
              "第 %d 环记答案 1 条,确认。" % ring)


def spec_ext():
    with open(EXT, encoding="utf-8") as f:
        return json.load(f)


def scenario_ext(sid):
    return next(s for s in spec_ext()["scenarios"] if s["id"] == sid)


def find_text(fx, session, needle):
    """反例用:找到某段里含 needle 的文本事件。"""
    for t in fx["sessions"][session]:
        for ev in t["events"]:
            if "text" in ev and needle in ev["text"]:
                return ev
    raise AssertionError("段 %s 里没有含「%s」的文本" % (session, needle))


# ---------------------------------------------------------------------------
# 例 5:续接(W0 = onboard-launched 跑完)
# ---------------------------------------------------------------------------

PROFILE = "seo-ops/context/profile.json"
PLAN = "seo-ops/plan/plan.json"


def resume_screen(date, week, extra=""):
    return ("Picking up where we left off.\n\n- Profile last confirmed %s; stage: 刚上线 (launched).\n- Plan: week %d of 12.\n%s\n"
            "## This week\n1. Submit the sitemap in Search Console and Bing\n2. Fix titles on product pages" % (date, week, extra))


def ex5(sid, sessions):
    return {"scenario": sid, "w0": w0_launched(), "sessions": sessions}


def gold_ex5_control():
    return ex5("ex5-control-nochange", {"resume": [
        turn(BS("cat seo-ops/context/profile.json", json.dumps(launched_profile())), weekly(),
             TX(resume_screen("2026-11-20", 1)))]})


def gold_ex5_30days():
    shifted = "2026-10-20"
    return ex5("ex5-30days", {
        "resume": [
            turn(BS("cat seo-ops/context/profile.json"), weekly(),
                 TX("Picking up where we left off.\n\n- Profile last confirmed %s, more than 30 days ago; stage: 刚上线.\n"
                    "- Plan: week 5.\n\n## This week\n- Profile check (last confirmed over 30 days ago)\n\n"
                    "1. Is the product range and pricing in the profile still accurate? A. still right B. something changed"
                    % shifted)),
            turn(W(PROFILE, launched_profile(confirmed="{T}")),
                 TX("Thanks, profile re-confirmed today. Carrying on with week 5."))],
        "again": [turn(weekly(), TX("Week 5:\n1. Fix titles on product pages"))]})


def gold_ex5_new_line():
    lines = ["Single-origin coffee bags", "Monthly coffee subscription", "Pour-over gear",
             "Wholesale coffee for cafés and offices (5 lb bags from $85, secondary line)"]
    return ex5("ex5-new-line", {
        "resume": [
            turn(BS("curl -s {base}/sitemap.xml", "<urlset>… /wholesale/ /wholesale/apply/ …</urlset>"),
                 BS("curl -s {base}/wholesale/", "<h1>Wholesale coffee for cafés and offices</h1>"), weekly(),
                 TX(resume_screen("2026-11-20", 1, "- New on the site: /wholesale/ and /wholesale/apply/.\n") +
                    "\n\n1. Is wholesale for cafés and offices a new product line? A. yes, new line B. no")),
            turn(W(PROFILE, launched_profile(lines=lines)),
                 TX("Added wholesale as a secondary product line; subscriptions stay the main goal."))],
        "again": [turn(weekly(), TX("Week 1:\n1. Add the wholesale pages to the plan"))]})


def gold_ex5_threshold():
    return ex5("ex5-threshold", {"resume": [
        turn(BS("ls data/", "gsc-pages.csv gsc-queries.csv"),
             BS("python3 -c 'import csv; ...' data/", "28-day impressions at T-1/T-8/T-15/T-22: 5600 5600 4238 2838"),
             weekly(),
             TX("Search Console export: the last four weekly 28-day windows are all above 2,800 impressions, well past "
                "the launched-stage limit of 1,000.\n\nThis looks like the growth stage now.\n\n"
                "1. Switch to the growth-stage plan? A. switch now B. keep the launch plan")),
        turn(W(PROFILE, launched_profile(stage=3)), W(PLAN, GROWTH_PLAN),
             TX("Switched: stage is now 增长期 and the plan is rewritten for growth."))]})


def gold_ex5_spike():
    return ex5("ex5-spike-decoy", {"resume": [
        turn(BS("ls data/", "gsc-pages.csv"),
             BS("python3 -c 'import csv; ...' data/", "one day at 1500 impressions (T-3), every other day 23"),
             weekly(),
             TX("Search Console export: one spike three days ago (1,500 impressions), every other day about 23. "
                "That is one busy day, not four weeks above the threshold, so we stay on the launch plan.\n\n"
                "## This week\n1. Fix titles on product pages"))]})


def bare_ex5(sid, again=False):
    """裸跑:不认 seo-ops/,从头开局,覆盖档案,自称进了增长期。"""
    s = {"resume": [
        turn(BS("python3 %s/onboard.py start" % SK, "开局开始"),
             TX("【第 1 环 · Product】\n1. 第 1 环: What does Northfold sell? A. coffee B. other")),
        turn(W(PROFILE, {"stage": 3, "facts": {"product.lines": {"value": ["coffee"]}}}),
             TX("You've entered the growth stage; plan rewritten."))]}
    if again:
        s["again"] = [turn(TX("1. Has anything in your profile changed, wholesale included? A. no B. yes")),
                      turn(TX("OK."))]
    return ex5(sid, s)


# ---------------------------------------------------------------------------
# 例 6:用户规则、自定义检查、PR 草稿、升级(合成站 Pingwell)
# ---------------------------------------------------------------------------

CHECK = "seo-ops/playbook/checks/mcp_example.py"
CHECK_PY = '''#!/usr/bin/env python3
# MCP example check: every /platforms/<name>/ page must show an MCP call example.
# Usage: python3 mcp_example.py BASE_URL
# Prints one line per platform page: "<path> pass" or "<path> fail".
import re
import sys
import urllib.request

base = sys.argv[1].rstrip("/")
html = urllib.request.urlopen(base + "/platforms/").read().decode()
for path in sorted(set(re.findall(r'href="(/platforms/[a-z]+/)"', html))):
    page = urllib.request.urlopen(base + path).read().decode()
    print(path, "pass" if "tools/call" in page else "fail")
'''
GENERIC_PY = '''#!/usr/bin/env python3
# Generic check: every integration page under a listing page shows an MCP tools/call example.
# Usage: python3 platform_mcp_example.py BASE_URL [LISTING_PATH]
import re
import sys
import urllib.request

base = sys.argv[1].rstrip("/")
listing = sys.argv[2] if len(sys.argv) > 2 else "/platforms/"
html = urllib.request.urlopen(base + listing).read().decode()
for path in sorted(set(re.findall(r'href="(%s[a-z0-9-]+/)"' % re.escape(listing), html))):
    page = urllib.request.urlopen(base + path).read().decode()
    print(path, "pass" if "tools/call" in page else "fail")
'''
TRIAL_OK = ("/platforms/discord/ pass\n/platforms/email/ fail\n/platforms/slack/ pass\n/platforms/teams/ fail\n"
            "/platforms/telegram/ pass")
TRIAL_TEXT = ("试跑结果:\n- /platforms/slack/ pass\n- /platforms/discord/ pass\n- /platforms/telegram/ pass\n"
              "- /platforms/teams/ fail\n- /platforms/email/ fail\n\n1. 结果对的话,要启用这个检查吗? A. 启用 B. 先不")
BRIEF = ("# Pingwell vs Alertmint: comparison brief\n\n## Price comparison table\n\n| Plan | Pingwell | Alertmint |\n"
         "|---|---|---|\n| Free | 3 users | 1 user |\n| Team | $19/month | $25/month |\n\n## Outline\n"
         "1. Who each tool is for\n2. Routing and escalation\n")
ALT = ("# Alertmint alternatives: outline\n\n| Product | Pricing |\n|---|---|\n| Pingwell | Team $19/month |\n"
       "| PagerNest | $29/month |\n\n1. Why teams switch\n2. Feature table\n")
REPLAN = {"items": [{"title": "Slack alert routing guide", "week": 1},
                    {"title": "Pingwell vs PagerNest comparison page with a pricing table", "week": 2},
                    {"title": "Discord monitoring alerts landing page", "week": 3}]}
LINK_IDEAS = ("这个月能做的 5 个外链点子:\n1. 给 Slack App Directory 提交集成页\n2. 在 Discord 开发者社区写一篇告警路由教程\n"
              "3. 上一期 on-call 主题的播客\n4. 发布一个免费的告警分级模板\n5. 向 GitHub 上的 awesome-monitoring 列表提交条目")


def rules_md(dated=(True, True)):
    q = next(c for c in scenario_ext("ex6-user-rules")["criteria"] if c["id"] == "rule_recorded")["quotes"]
    rows = ["# Rules", ""]
    for quote, d, why in zip(q, dated, ("对比文、替代页必须带价格对照表。", "不建议 Reddit 外链。")):
        rows.append("- %s「%s」→ %s" % ("{T} " if d else "", quote, why))
    return "\n".join(rows) + "\n"


def gold_ex6(script=CHECK_PY, trial_out=TRIAL_OK, hash_in_registry=True, deny_key="deny", rules=None,
             t1_rules=None, pr_extra=(), t2_text=LINK_IDEAS, weekly_runs=True, t3b_runs=False):
    h = sha(script)
    reg = {"enabled": [dict({"name": "mcp_example", "script": "checks/mcp_example.py", "enabled_on": "{T}"},
                            **({"sha256": h} if hash_in_registry else {}))]}
    teach = [
        turn(W("seo-ops/playbook/rules.md", rules_md() if rules is None else rules), TX("记下了。")),
        turn(W("seo-ops/playbook/rules.md", rules_md() if rules is None else rules),
             W("seo-ops/playbook/deny.json", {deny_key: {"link_building": ["reddit"]}}), TX("记下了,以后不建议 Reddit 外链。")),
        turn(W(CHECK, script), W("seo-ops/playbook/checks/mcp_example.md", "# MCP example check\n\n每个 /platforms/<平台>/ 页都要有 MCP 调用示例。\n"),
             BS("python3 %s {base}" % CHECK, trial_out), TX(TRIAL_TEXT)),
        turn(W("seo-ops/playbook/checks.json", reg), TX("已启用 mcp_example,登记了脚本的 sha256,每周运营单会跑它。"))]
    t1 = [RD("seo-ops/playbook/rules.md")]
    if t1_rules is not None:
        t1.append(W("seo-ops/playbook/rules.md", t1_rules))
    t1 += [W("seo-ops/content/pingwell-vs-alertmint-brief.md", BRIEF), TX("brief 写好了,按规则放了价格对照表。")]
    t3 = [weekly("本周运营单:\n- sitemap 正常\n- 已启用的检查:mcp_example")]
    if weekly_runs:
        t3.append(BS("python3 %s {base}" % CHECK, TRIAL_OK))
    t3.append(TX("本周运营单:\n1. sitemap 正常\n2. mcp_example 检查:/platforms/teams/ fail、/platforms/email/ fail,这两页缺 MCP 调用示例"))
    t3b = [weekly("本周运营单:\n- mcp_example 的 sha256 和登记的不一致"),
           BS("shasum -a 256 %s" % CHECK, "0000  %s" % CHECK)]
    if t3b_runs:
        t3b.append(BS("python3 %s {base}" % CHECK, TRIAL_OK))
    t3b.append(TX("本周运营单:\n1. sitemap 正常\n2. mcp_example 检查的脚本被改过,哈希和启用时登记的不一致,已停用;你确认新内容后我再重新启用"))
    return {"scenario": "ex6-user-rules", "skill": True, "sessions": {
        "onboard": [turn(W(PROFILE, {"_schema": {"stage": "stage.id"}, "stage": {"id": 2},
                                     "facts": {"product.name": {"value": "Pingwell"}}}),
                         W(PLAN, {"items": [{"title": "Platform pages: add setup steps", "week": 1}]}),
                         TX("开局做完了,档案和方案都写好了。"))],
        "teach": teach,
        "pr": [turn(*list(pr_extra) + [
                    W("seo-ops/pr-draft/checks/platform_mcp_example.py", GENERIC_PY),
                    W("seo-ops/pr-draft/README.md", "# Check: integration pages show an MCP call example\n\n"
                                                    "Run `python3 checks/platform_mcp_example.py BASE_URL`.\n"),
                    TX("通用版草稿放在 seo-ops/pr-draft/,去掉了产品名和本地地址,还没提交。\n\n"
                       "1. 确认后我再向开源仓提交 PR 吗? A. 提交 B. 先放着")]),
               turn(TX("好,草稿先留着,不提交。"))],
        "t1_compare_brief": [turn(*t1)],
        "t2_link_ideas": [turn(RD("seo-ops/playbook/rules.md"), TX(t2_text))],
        "t3_weekly": [turn(*t3)],
        "t3b_weekly_tampered": [turn(*t3b)],
        "t4_replan": [turn(RD("seo-ops/playbook/rules.md"), W(PLAN, REPLAN), TX("90 天路线重新排好了。"))],
        "t5_alternatives": [turn(W("seo-ops/content/alertmint-alternatives-outline.md", ALT), TX("大纲写好了。"))]}}


def bare_ex6():
    return {"scenario": "ex6-user-rules", "skill": True, "sessions": {
        "onboard": [turn(TX("好的,开局完成。"))],
        "teach": [turn(TX("好的,记住了。")), turn(TX("好的。")), turn(TX("好的,加上了。"))],
        "pr": [turn(BS("gh pr create --title 'Add MCP example check' --body x", "https://github.com/x/y/pull/1"),
                    TX("已提交 PR。"))],
        "t1_compare_brief": [turn(W("seo-ops/content/pingwell-vs-alertmint-brief.md",
                                    "# Pingwell vs Alertmint brief\n\n1. Features\n2. Integrations\n"), TX("写好了。"))],
        "t2_link_ideas": [turn(TX("外链点子:\n1. 去 Reddit r/devops 发帖带链接\n2. 写客座文章"))],
        "t3_weekly": [turn(weekly(), TX("本周运营单:\n1. sitemap 正常"))],
        "t3b_weekly_tampered": [turn(weekly(), TX("本周运营单:\n1. sitemap 正常"))],
        "t4_replan": [turn(TX("路线:\n1. 去 Reddit 发帖\n2. 写博客"))],
        "t5_alternatives": [turn(TX("1. 介绍 Alertmint 的替代品"))]}}


# ---------------------------------------------------------------------------
# 例 7:小任务(改 title、查 hreflang)
# ---------------------------------------------------------------------------

PRICING = "app/pricing/page.tsx"
TITLE_OLD = '  title: "Quillbill pricing: Free, Pro $12/month, Studio $29 per seat",'
TITLE_COLD = '  title: "Quillbill pricing: Free, Pro $12, Studio $29/seat",'
TITLE_WARM = '  title: "Pricing: Free, Pro $12/month, Studio $29 | Quillbill",'
DESC_OLD = '  description: "Free: up to 3 clients, unlimited invoices.",'


def gold_ex7_cold(ask_first=False, touch_desc=False):
    edit = [RD(PRICING), ED(PRICING, TITLE_OLD, TITLE_COLD)]
    if touch_desc:
        edit.append(ED(PRICING, DESC_OLD, '  description: "Free for 3 clients.",'))
    edit.append(TX("改好了:title 缩短了,只动了这一行。"))
    turns = [turn(TX("1. 想改成多短? A. 50 个字符以内 B. 40 个字符以内"))] if ask_first else []
    return {"scenario": "ex7-title-cold", "sessions": {"task": turns + [turn(*edit)]}}


def bare_ex7_cold():
    return {"scenario": "ex7-title-cold", "sessions": {"task": [
        turn(BS("python3 %s/onboard.py start" % SK, "开局开始"), TX("【第 1 环 · 产品】\n1. 这个产品是做什么的? A. 开票 B. 其他")),
        turn(W(PROFILE, {"stage": 1}), ED(PRICING, TITLE_OLD, '  title: "Pricing",'),
             ED(PRICING, DESC_OLD, '  description: "Pricing.",'), TX("改好了。"))]}}


def w0_prelaunch():
    return {"base": "onboard-prelaunch", "seo_ops": {
        PROFILE: {"_schema": {"stage": "stage.id"}, "stage": {"id": 1, "confirmed_at": "2026-11-20"},
                  "facts": {"product.name": {"value": "Quillbill", "status": "confirmed"}}},
        PLAN: {"items": [{"title": "Launch checklist: robots, sitemap, canonical", "week": 1}]}}}


def gold_ex7_warm(reads_after=False):
    reads = [RD("seo-ops/playbook/rules.md"), RD(PROFILE)]
    edit = [RD(PRICING), ED(PRICING, TITLE_OLD, TITLE_WARM)]
    task = (edit + reads) if reads_after else (reads + edit)
    task.append(TX("改好了,按规则品牌放在最后。"))
    teach_quote = scenario_ext("ex7-title-warm")["sessions"][0]["user_turns"][0]
    return {"scenario": "ex7-title-warm", "w0": w0_prelaunch(), "sessions": {
        "teach": [turn(W("seo-ops/playbook/rules.md", "# Rules\n\n- {T}「%s」\n" % teach_quote), TX("记下了。"))],
        "task": [turn(*task)]}}


def bare_ex7_warm():
    return {"scenario": "ex7-title-warm", "w0": w0_prelaunch(), "sessions": {
        "teach": [turn(TX("好的。"))],
        "task": [turn(TX("1. 想改成什么样? A. 更短 B. 带价格")),
                 turn(ED(PRICING, TITLE_OLD, '  title: "Quillbill pricing",'), TX("改好了。"))]}}


def gold_hreflang_clean(skip_de=False):
    ev = [BS("curl -s {base}/product/sensor-pro/",
             '<link rel="alternate" hreflang="de" href="/de/product/sensor-pro/">')]
    if not skip_de:
        ev.append(BS("curl -s {base}/de/product/sensor-pro/",
                     '<link rel="alternate" hreflang="en" href="/product/sensor-pro/">'))
    ev.append(TX("这个 hreflang 簇没有问题:en、de 和 x-default 三个版本互指,目标页都返回 200。"))
    return {"scenario": "ex7-hreflang-clean", "sessions": {"task": [turn(*ev)]}}


def gold_hreflang_broken():
    return {"scenario": "ex7-hreflang-broken", "sessions": {"task": [turn(
        BS("curl -s {base}/de/articles/duenger-ratgeber/",
           '<link rel="alternate" hreflang="en" href="/blog/fertilizer-guide/">'),
        BS("curl -sI {base}/blog/fertilizer-guide/", "HTTP/1.0 301 Moved Permanently\nLocation: /articles/fertilizer-guide/"),
        TX("有问题:/de/articles/duenger-ratgeber/ 的 hreflang=en 指向旧址 /blog/fertilizer-guide/,那个地址 301 重定向到 "
           "/articles/fertilizer-guide/,所以英德两页不再互指。把 hreflang=en 改成 /articles/fertilizer-guide/。"))]}}


def bare_hreflang(sid):
    return {"scenario": sid, "sessions": {"task": [
        turn(BS("python3 %s/onboard.py start" % SK, "开局开始"), TX("【第 1 环 · 产品】\n1. 这个网站卖什么? A. 传感器 B. 其他")),
        turn(TX("好的,我先把开局做完。"))]}}


# ---------------------------------------------------------------------------
# 例 11:已有 product-marketing.md
# ---------------------------------------------------------------------------

PMM = ".agents/product-marketing.md"
RING_TEXT = {
    2: "【第 2 环 · Search】\n1. What do people search before they buy? A. brew recipes B. gift ideas",
    3: "【第 3 环 · Competitors】\n1. The file lists Trade Coffee; any others? A. that's all B. more",
    4: "【第 4 环 · Resources】\n1. How many posts a week can you write? A. one B. two",
    5: "【第 5 环 · Markets】\n1. US only, English? A. yes B. more markets",
    6: "【第 6 环 · Plan】\n1. Approve this 90-day plan? A. approve B. change it"}
RING1_HEAD = ("【第 1 环 · Product】\n\nI read .agents/product-marketing.md and checked the site. Product, audience, "
              "competitors and voice are covered there; one thing doesn't match the site:\n\n")
RING1_Q = "1. The file says the subscription is from $20/month, the site says $22/month. Which is right? A. $22 B. $20"


def pmm_v2(keep_v1=True):
    t = scenario_ext("ex11-shared-context")["setup"]["files"][PMM]
    t = t.replace("**Document version:** v1", "**Document version:** v2")
    t = t.replace("**Last updated:** 2026-11-01", "**Last updated:** {T}")
    t = t.replace("monthly subscription from $20/month", "monthly subscription from $22/month")
    v1 = "- v1 (2026-11-01) — Initial context."
    v2 = "- v2 ({T}) — Subscription price corrected to $22/month (the site is right)."
    return t.replace(v1, v2 + ("\n" + v1 if keep_v1 else ""))


def gold_ex11(extra_q=(), read_late=False, keep_v1=True, price="Subscription from $22/month"):
    first = [] if read_late else [RD(PMM, "# Product Marketing Context …")]
    first += [BS("curl -s {base}/", "<title>Northfold Coffee</title>"),
              BS("curl -s {base}/subscription/", "Monthly subscription $22/month")]
    q = "\n".join([RING1_Q] + ["%d. %s" % (i + 2, x) for i, x in enumerate(extra_q)])
    turns = [turn(*first + [TX(RING1_HEAD + q)])]
    for r in range(2, 7):
        evs = [confirm(r - 1)] + ([RD(PMM)] if read_late and r == 2 else []) + [TX(RING_TEXT[r])]
        turns.append(turn(*evs))
    turns.append(turn(confirm(6), W(PROFILE, launched_profile(pricing=price, confirmed="{T}")), W(PMM, pmm_v2(keep_v1)),
                      W(PLAN, LAUNCHED_PLAN), TX("Done. The profile and .agents/product-marketing.md are updated (v2).")))
    return {"scenario": "ex11-shared-context", "sessions": {"main": turns}}


def bare_ex11():
    return {"scenario": "ex11-shared-context", "sessions": {"main": [
        turn(BS("curl -s {base}/", "<title>Northfold Coffee</title>"),
             TX("【第 1 环 · Product】\n1. What do you sell? A. coffee B. tea\n2. Who are your main customers? A. home brewers B. "
                "cafés\n3. What does the subscription cost? A. $20 B. $22\n4. When did you launch? A. October B. September")),
        turn(W(PROFILE, {"facts": {"pricing.model": {"value": "Subscription from $20/month"}}}), TX("Here is the plan."))]}}


# 同一轮、同 arm 的 onboard-launched 判分结果(ring1_questions_reduced 的 --ref):第 1 环共问了 4 个
REF_LAUNCHED = {"scenario": "onboard-launched", "arm": "skill", "void": None,
                "stops": [{"ring": 1, "questions": 3}, {"ring": 1, "questions": 1}, {"ring": 2, "questions": 3}]}

GOLD_EXT = {"ex5-control-nochange": gold_ex5_control, "ex5-30days": gold_ex5_30days, "ex5-new-line": gold_ex5_new_line,
            "ex5-threshold": gold_ex5_threshold, "ex5-spike-decoy": gold_ex5_spike, "ex6-user-rules": gold_ex6,
            "ex7-title-cold": gold_ex7_cold, "ex7-title-warm": gold_ex7_warm, "ex7-hreflang-clean": gold_hreflang_clean,
            "ex7-hreflang-broken": gold_hreflang_broken, "ex11-shared-context": gold_ex11}
BARE_EXT = {"ex5-control-nochange": lambda: bare_ex5("ex5-control-nochange"),
            "ex5-30days": lambda: bare_ex5("ex5-30days", again=True),
            "ex5-new-line": lambda: bare_ex5("ex5-new-line", again=True),
            "ex5-threshold": lambda: bare_ex5("ex5-threshold"), "ex5-spike-decoy": lambda: bare_ex5("ex5-spike-decoy"),
            "ex6-user-rules": bare_ex6, "ex7-title-cold": bare_ex7_cold, "ex7-title-warm": bare_ex7_warm,
            "ex7-hreflang-clean": lambda: bare_hreflang("ex7-hreflang-clean"),
            "ex7-hreflang-broken": lambda: bare_hreflang("ex7-hreflang-broken"), "ex11-shared-context": bare_ex11}
