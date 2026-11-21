#!/usr/bin/env python3
"""teach.py — 用户按自己的想法教 seo-suite:规则、禁用清单、自己的检查、提回开源仓(RQ-237 第 4 批;stdlib only)。

全部写在站点仓的 seo-ops/playbook/(skill 目录之外,升级不覆盖)。格式和流程见 references/overview/playbook.md。

规则:
  rule add --quote "<用户原话>" [--deny 关键词 ...] [--item 名字] [--applies brief,plan,weekly,outreach]
      原话带日期写进 playbook/rules.md。原话像「不做 X / 别再 / 不要」时必须给 --deny(X 的关键词,推荐代码按它过滤)
      或 --no-deny(说明这条不是禁用);两样都没给退出码 3,不替用户猜。
  rule list [--json]
  rule remove R2 --quote "<用户原话>"      撤销(rules.md 里留痕,deny.json 里对应的禁用项失效)
检查(用户脚本当不可信代码:只在用户确认后跑,子进程、超时、输出当数据):
  check new <名> --desc "说明" [--match 正则]       生成 checks/<名>.py 模板和 <名>.md 说明,agent 按用户的话改脚本
  check try <名> --url U1 --url U2 --url U3 [--allow-local]   先在 ≥3 个页面上跑,把结果给用户看
  check enable <名> --quote "<用户原话>"            用户看过结果、说可以以后才算启用;记下脚本 sha256
  check disable <名> [--quote …]
  check list [--json]                                 脚本内容和启用时不一样 = 自动停用(changed),等用户再确认
  check run [--url …] [--json]                        跑所有已启用的检查(每周运营单也会跑)
提回开源仓:
  export <检查名> [--out DIR]       整理成 seo-skills 的 PR 草稿目录:域名、品牌名、产品名(从档案取)换成占位符并列出;
                                     只生成文件,给一行 gh pr create --draft 建议命令,不提交、不推送
总览:
  show [--json]                      规则、禁用清单、检查、自定义打法、数据源一屏

公共参数 --ws seo-ops(默认从当前目录往上找)。退出码:0 正常;2 用法错;3 被门挡住(缺原话、没试跑就启用等)。
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lifecycle as LC  # noqa: E402
import playbook as PB  # noqa: E402

CHECK_TEMPLATE = '''#!/usr/bin/env python3
"""seo-ops 自定义检查:%(desc)s

由 teach.py check new 生成。约定(references/overview/playbook.md 第三节):
  - stdin 是一个 JSON:{"url", "final_url", "status", "html"};不要自己联网、不要读写别的文件。
  - stdout 打印一个 JSON:{"pass": true/false, "findings": ["没过的原因", ...]}。
  - 只用标准库。teach.py 用子进程跑它,有超时,不给环境变量。
"""
import json
import re
import sys

page = json.load(sys.stdin)
html = page.get("html") or ""
findings = []

# TODO:按用户的原话改下面这段判定
if not re.search(r"%(pattern)s", html, re.I):
    findings.append("页面上没找到:%(desc)s")

print(json.dumps({"pass": not findings, "findings": findings}, ensure_ascii=False))
'''

CHECK_DOC = """# 检查:%(name)s

- 做什么:%(desc)s
- 用户原话:%(quote)s
- 跑在哪些页面:%(match)s
- 输入 / 输出:stdin 一个 JSON(url、final_url、status、html);stdout 一个 JSON(pass、findings)
- 启用:`teach.py check try %(name)s --url … ×3` 给用户看结果 → `teach.py check enable %(name)s --quote "<原话>"`
- 脚本改了会自动停用,运营单里提示再确认
"""


def ws_of(ns, create=False):
    ws = PB.find_ws(None, ns.ws)
    if ws and LC.inside_skill(ws):
        LC.resolve_ws(ws, __file__, sys.argv[1:])     # 落在 skill 安装目录里:报错给照抄命令,不写
    if ws:
        return ws
    if create:
        ws = LC.resolve_ws(ns.ws, __file__, sys.argv[1:], must_exist=False)
        os.makedirs(PB.pb_dir(ws), exist_ok=True)
        return ws
    raise PB.PlaybookError("找不到 seo-ops/ 工作区(在站点仓根目录跑,或用 --ws 指定)")


def need_quote(q):
    if not (q or "").strip():
        raise PB.GateError("必须用 --quote 带上用户原话(用户没说过的不写进 playbook)")
    return q.strip()


# ---------------------------------------------------------------------------
# rule
# ---------------------------------------------------------------------------

def guess_item(quote, terms):
    m = re.search(r"(?:别再建议我们去做|别再建议|别再做|不要做|不用做|不做|不要|别再|don'?t do|stop doing|no more)\s*"
                  r"([^,\uff0c\u3002.;\uff1b!\uff01]+)", quote, re.I)
    item = (m.group(1).strip() if m else "") or " ".join(terms)
    item = re.sub(r"(了|啦|吧|呢)$", "", item).strip()
    return item[:40] or " ".join(terms)


def cmd_rule(ns):
    if ns.action == "list":
        ws = ws_of(ns)
        rules = PB.parse_rules(PB.read_rules(ws))
        deny = PB.load_deny(ws)
        if ns.json:
            print(json.dumps({"rules": rules, "deny": deny}, ensure_ascii=False, indent=1))
            return 0
        for r in rules:
            print("%s%s\n%s\n" % (r["head"], "(已撤销)" if r["removed"] else "", r["body"]))
        print("禁用清单:" + ("、".join("%s(%s,来自 %s)" % (d["item"], "/".join(d["terms"]), d.get("source"))
                                    for d in deny) or "无"))
        return 0
    if ns.action == "remove":
        ws = ws_of(ns)
        if not ns.id:
            raise PB.PlaybookError("rule remove 要给规则编号,如 R2")
        n = PB.remove_rule(ws, ns.id, need_quote(ns.quote))
        print("撤销 %s;对应禁用项失效 %d 条" % (ns.id, n))
        return 0
    quote = need_quote(ns.quote)
    terms = [t.strip() for x in ns.deny or [] for t in x.split(",") if t.strip()]
    if PB.looks_negative(quote) and not terms and not ns.no_deny:
        raise PB.GateError("原话像「不做 X」:用 --deny 写出 X 的关键词(比如 --deny reddit),推荐代码按它过滤;"
                           "这条不是禁用就加 --no-deny。不替用户猜。")
    ws = ws_of(ns, create=True)
    applies = [a.strip() for a in (ns.applies or "").split(",") if a.strip()]
    items = []
    rid = PB.next_rule_id(PB.read_rules(ws) or PB.RULES_HEAD)
    if terms:
        item = ns.item or guess_item(quote, terms)
        items.append(PB.add_deny(ws, item, terms, quote, rid))
    rid = PB.append_rule(ws, quote, applies, items)
    print("记下 %s(%s):「%s」" % (rid, PB.rules_path(ws), quote))
    for d in items:
        print("禁用清单 + %s(关键词 %s)。之后 plan、每周运营单、link_intel、prioritize、fix_plan、content_queue "
              "出的建议和外联候选都按它过滤" % (d["item"], "/".join(d["terms"])))
    print("请把这一条念给用户确认;说错了用 teach.py rule remove %s --quote … 撤掉重写。" % rid)
    return 0


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------

VERDICT = {"pass": "✓ pass 过", "fail": "✗ fail 没过", "error": "error 出错"}


def _summary(rows):
    return {k: sum(r["result"] == k for r in rows) for k in ("pass", "fail", "error")}


def print_rows(name, rows):
    print("检查 %s 在 %d 个页面上的结果:" % (name, len(rows)))
    for r in rows:
        extra = r.get("error") or ";".join(r["findings"][:3]) or "—"
        print("  [%s] %s  %s" % (VERDICT[r["result"]], r["url"], extra))


def cmd_check(ns):
    ws = ws_of(ns, create=ns.action == "new")
    if ns.action == "list":
        rows = PB.list_checks(ws)
        if ns.json:
            print(json.dumps([{k: v for k, v in r.items() if k != "entry"} for r in rows], ensure_ascii=False, indent=1))
            return 0
        zh = {"enabled": "已启用", "changed": "脚本改过、已自动停用(等再确认)", "tried": "试跑过、没启用",
              "draft": "草稿", "disabled": "已停用", "missing": "脚本不在了"}
        for r in rows:
            print("- %s:%s%s" % (r["name"], zh[r["state"]], ("(%s)" % r["entry"].get("desc")) if r["entry"].get("desc") else ""))
        if not rows:
            print("还没有自定义检查(teach.py check new <名> --desc …)")
        return 0
    if ns.action == "run":
        urls = ns.url or []
        res = PB.run_enabled(ws, urls, allow_local=ns.allow_local) if urls else {"ran": [], "changed": [], "skipped": []}
        if not urls:
            print("check run 要给 --url(每周运营单会自动给本周轻检过的页面)")
        if ns.json:
            print(json.dumps(res, ensure_ascii=False, indent=1))
        else:
            for c in res["ran"]:
                print_rows(c["name"], c["results"])
            for c in res["changed"]:
                print("- %s 的脚本改过(启用时 %s,现在 %s),已自动停用,等用户再确认" % (c["name"], c["enabled_sha"], c["now_sha"]))
        return 0
    name = ns.name
    if not name:
        raise PB.PlaybookError("check %s 要给检查名" % ns.action)
    script, doc = PB.check_paths(ws, name)
    reg = PB.registry(ws)
    ent = reg["checks"].setdefault(name, {})
    if ns.action == "new":
        if os.path.exists(script):
            raise PB.PlaybookError("%s 已经有了;要改就直接改脚本(改完要重新 try + enable)" % script)
        desc = (ns.desc or "").strip()
        if not desc:
            raise PB.PlaybookError("check new 要 --desc(这个检查查什么,用用户的话写)")
        os.makedirs(os.path.dirname(script), exist_ok=True)
        pat = re.escape(ns.pattern or desc.split()[0]).replace('"', '\\"')
        with open(script, "w", encoding="utf-8") as f:
            f.write(CHECK_TEMPLATE % {"desc": desc.replace('"""', "'''"), "pattern": pat})
        with open(doc, "w", encoding="utf-8") as f:
            f.write(CHECK_DOC % {"name": name, "desc": desc, "quote": ("「%s」" % ns.quote) if ns.quote else "(待补)",
                                 "match": ns.match or "所有页面(建议用 --match 限定,比如 /platforms/)"})
        ent.update({"desc": desc, "created_at": PB.now(), "match": ns.match, "quote": ns.quote})
        PB.save_registry(ws, reg)
        print("写了 %s 和 %s。按用户的话改好判定后,先 check try 在 3 个页面上跑给用户看。" % (script, doc))
        return 0
    if not os.path.isfile(script):
        raise PB.PlaybookError("没有 %s(先 check new %s)" % (script, name))
    if ns.action == "try":
        urls = ns.url or []
        if len(urls) < 3:
            raise PB.GateError("先在至少 3 个页面上试跑(--url 给 3 次),把结果给用户看")
        sha = PB.sha256_file(script)
        rows = [PB.run_check(script, PB.fetch_page(u, ns.allow_local)) for u in urls]
        ent.setdefault("tries", []).append({"at": PB.now(), "sha256": sha, "urls": urls, "summary": _summary(rows),
                                            "results": rows})
        ent["tries"] = ent["tries"][-5:]
        PB.save_registry(ws, reg)
        if ns.json:
            print(json.dumps({"name": name, "sha256": sha, "results": rows}, ensure_ascii=False, indent=1))
        else:
            print_rows(name, rows)
            print("把上面的结果原样给用户看,问对不对;用户说可以,再 teach.py check enable %s --quote \"<原话>\"。"
                  "没启用前每周运营单不跑它。" % name)
        return 0
    if ns.action == "enable":
        quote = need_quote(ns.quote)
        sha = PB.sha256_file(script)
        tries = ent.get("tries") or []
        if not tries or tries[-1].get("sha256") != sha:
            raise PB.GateError("这份脚本还没试跑过(或试跑后改过):先 check try %s --url … ×3 给用户看结果" % name)
        ent["enabled"] = {"sha256": sha, "at": PB.now(), "quote": quote, "tried_at": tries[-1]["at"]}
        ent.pop("disabled", None)
        PB.save_registry(ws, reg)
        print("启用 %s(sha256 %s…)。每周运营单会跑它;脚本内容一变就自动停用,等你再确认。" % (name, sha[:12]))
        return 0
    if ns.action == "disable":
        ent["disabled"] = {"at": PB.now(), "quote": ns.quote}
        ent.pop("enabled", None)
        PB.save_registry(ws, reg)
        print("停用 %s" % name)
        return 0
    raise PB.PlaybookError("未知动作 %s" % ns.action)


# ---------------------------------------------------------------------------
# export:整理成开源仓的 PR 草稿
# ---------------------------------------------------------------------------

def site_specific_terms(ws):
    """从档案取站点专属的词:域名、品牌名、产品名 / 产品线 → [(原文, 占位符)],长的在前。"""
    prof = PB.read_json(os.path.join(ws, "context", "profile.json"), {}) or {}
    proj = {}
    try:
        with open(os.path.join(ws, "project.yaml"), encoding="utf-8") as f:
            for ln in f:
                if ":" in ln and not ln.startswith("#"):
                    k, v = ln.split(":", 1)
                    proj[k.strip()] = v.strip().strip("'\"")
    except OSError:
        pass
    pairs = []
    site = prof.get("site") or proj.get("site") or ""
    host = re.sub(r"^[a-z][a-z0-9+.-]*://", "", site, flags=re.I).split("/")[0].split(":")[0].lower()
    if host:
        pairs.append((host, "example.com"))
        bare = host[4:] if host.startswith("www.") else host
        if bare != host:
            pairs.append((bare, "example.com"))
        label = bare.split(".")[0]
        if len(label) >= 3:
            pairs.append((label, "{{BRAND}}"))

    def facts(key):
        for f in prof.get("facts") or []:
            if f.get("key") == key and f.get("value"):
                v = f["value"]
                return v if isinstance(v, list) else [v]
        return []
    for v in facts("product.name"):
        pairs.append((str(v), "{{BRAND}}"))
    for i, v in enumerate(facts("product.lines"), 1):
        if isinstance(v, dict):
            v = v.get("name") or v.get("value") or ""
        if len(str(v)) >= 3:
            pairs.append((str(v), "{{PRODUCT_LINE_%d}}" % i))
    seen, out = set(), []
    for a, b in sorted(pairs, key=lambda p: -len(p[0])):
        if a.lower() not in seen and a.strip():
            seen.add(a.lower())
            out.append((a, b))
    return out


def scrub(text, pairs):
    hits = []
    for a, b in pairs:
        n = len(re.findall(re.escape(a), text, re.I))
        if n:
            text = re.sub(re.escape(a), b, text, flags=re.I)
            hits.append({"from": a, "to": b, "count": n})
    return text, hits


def cmd_export(ns):
    ws = ws_of(ns)
    script, doc = PB.check_paths(ws, ns.name)
    if not os.path.isfile(script):
        raise PB.PlaybookError("没有检查 %s" % ns.name)
    st = PB.check_state(ws, ns.name)
    pairs = site_specific_terms(ws)
    out = os.path.abspath(ns.out or PB.pb_dir(ws, "export", ns.name))
    dest = os.path.join(out, "skills", "seo-suite", "examples", "playbook-checks", ns.name)
    os.makedirs(dest, exist_ok=True)
    report = []
    for src, name in ((script, "check.py"), (doc, "README.md")):
        if not os.path.isfile(src):
            continue
        with open(src, encoding="utf-8") as f:
            text, hits = scrub(f.read(), pairs)
        with open(os.path.join(dest, name), "w", encoding="utf-8") as f:
            f.write(text)
        report += [dict(h, file=name) for h in hits]
    left = sorted({m.group(0).lower() for f in os.listdir(dest)
                   for m in re.finditer(r"\b[a-z0-9-]+\.(?:com|io|ai|app|dev|net|org|co|cn)\b",
                                        open(os.path.join(dest, f), encoding="utf-8").read(), re.I)}
                  - {"example.com"})
    tries = (st.get("entry") or {}).get("tries") or []
    summ = tries[-1]["summary"] if tries else None
    title = "examples: 用户检查 %s" % ns.name
    body = ["## 做什么", "", (st.get("entry") or {}).get("desc") or "(见 README.md)", "",
            "## 从哪来", "", "站点仓 seo-ops/playbook/checks/ 里用户自己写的检查,用 teach.py export 整理。",
            "", "## 去掉的站点专属内容", ""]
    body += ["- %s:`%s` → `%s`(%d 处)" % (h["file"], h["from"], h["to"], h["count"]) for h in report] or ["- 没有"]
    if left:
        body += ["", "**还剩这些域名,提交前确认能公开:** " + "、".join(left)]
    body += ["", "## 验证", "", ("在原站 %d 个页面上试跑:过 %d、没过 %d、出错 %d(页面地址不随 PR 提交)。" % (
        sum(summ.values()), summ["pass"], summ["fail"], summ["error"])) if summ else "还没试跑过。",
             "", "- [ ] 只用标准库", "- [ ] 没有密钥、客户数据、站点专属内容"]
    with open(os.path.join(out, "PR.md"), "w", encoding="utf-8") as f:
        f.write("# %s\n\n%s\n" % (title, "\n".join(body)))
    print("PR 草稿目录:%s" % out)
    print("换掉的站点专属内容:" + ("、".join("%s→%s(%s,%d 处)" % (h["from"], h["to"], h["file"], h["count"])
                                         for h in report) or "无"))
    if left:
        print("⚠ 还剩这些域名,给用户看过再提:" + "、".join(left))
    print("没有提交、没有推送。用户确认后,把 %s 拷进 seo-skills 的 fork 分支并提交,再跑:" % os.path.join(out, "skills"))
    print('  gh pr create --draft --repo everyinfra/seo-skills --title "%s" --body-file "%s"'
          % (title, os.path.join(out, "PR.md")))
    return 0


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------

def cmd_show(ns):
    ws = ws_of(ns)
    rules = [r for r in PB.parse_rules(PB.read_rules(ws)) if not r["removed"]]
    deny = PB.load_deny(ws)
    checks = PB.list_checks(ws)
    plays = (PB.read_json(PB.pb_dir(ws, "plays.json"), {}) or {}).get("plays") or []
    srcs, bad = PB.load_sources(ws)
    if ns.json:
        print(json.dumps({"ws": ws, "rules": rules, "deny": deny,
                          "checks": [{k: v for k, v in c.items() if k != "entry"} for c in checks],
                          "plays": [p.get("id") for p in plays], "sources": [s["name"] for s in srcs],
                          "source_problems": bad}, ensure_ascii=False, indent=1))
        return 0
    print("seo-ops/playbook(%s)" % PB.pb_dir(ws))
    print("- 规则 %d 条:%s" % (len(rules), ";".join(r["id"] for r in rules) or "无"))
    print("- 禁用清单:%s" % ("、".join(d["item"] for d in deny) or "无"))
    print("- 自定义检查:%s" % ("、".join("%s(%s)" % (c["name"], c["state"]) for c in checks) or "无"))
    print("- 自定义打法:%s" % ("、".join(str(p.get("id")) for p in plays) or "无"))
    print("- 数据源:%s" % ("、".join("%s(%s)" % (s["name"], "付费" if s["paid"] else "免费") for s in srcs) or "无"))
    for b in bad:
        print("  ⚠ " + b)
    return 0


def build_parser():
    ap = argparse.ArgumentParser(description="用户按自己的想法教 seo-suite(规则、禁用清单、检查、提回开源仓)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rule")
    r.add_argument("action", choices=("add", "list", "remove"))
    r.add_argument("id", nargs="?")
    r.add_argument("--quote")
    r.add_argument("--deny", action="append", help="禁用关键词(可多次或逗号分隔),推荐代码按它过滤")
    r.add_argument("--item", help="禁用项的名字(默认从原话里取)")
    r.add_argument("--no-deny", action="store_true", help="这条不是「不做 X」")
    r.add_argument("--applies", help="适用:brief,plan,weekly,outreach(默认全部)")
    r.add_argument("--json", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("action", choices=("new", "try", "enable", "disable", "list", "run"))
    c.add_argument("name", nargs="?")
    c.add_argument("--desc")
    c.add_argument("--pattern", help="check new:模板里先放的匹配词")
    c.add_argument("--match", help="只在网址匹配这个正则的页面上跑(运营单用)")
    c.add_argument("--url", action="append")
    c.add_argument("--quote")
    c.add_argument("--allow-local", action="store_true")
    c.add_argument("--json", action="store_true")
    e = sub.add_parser("export")
    e.add_argument("name")
    e.add_argument("--out")
    s = sub.add_parser("show")
    s.add_argument("--json", action="store_true")
    for p in (r, c, e, s):
        p.add_argument("--ws", help="seo-ops 工作区(默认从当前目录往上找)")
    return ap


def main(argv=None):
    ns = build_parser().parse_args(argv)
    try:
        return {"rule": cmd_rule, "check": cmd_check, "export": cmd_export, "show": cmd_show}[ns.cmd](ns)
    except (PB.PlaybookError, PB.GateError) as e:
        print("错误:%s" % e, file=sys.stderr)
        return e.code
    except LC.UsageError as e:
        print("错误:%s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
