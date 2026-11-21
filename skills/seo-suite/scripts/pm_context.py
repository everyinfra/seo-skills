#!/usr/bin/env python3
"""pm_context.py — 和 marketingskills 的 product-marketing 共用产品上下文(RQ-237 例 11;stdlib only)。

文件:站点仓的 .agents/product-marketing.md(coreyhaines31/marketingskills 的 product-marketing skill 写的,
格式照它 SKILL.md 第 3、4 步:`# Product Marketing Context`、`**Document version:** vN`、`**Last updated:** 日期`、
`## 段名` 下面一行一个 `**标签:** 值`、文末 `## Changelog` 新的在上)。

两个方向:
  读  开局第 1 环把它当草稿:FIELDS 里的标签有值就成为档案里的草稿事实(来源写这份文件,仍是「未确认」)
  写  开局某一环确认或纠正后,把改过的条目写回这份文件:只改对应那一行的值,别的段落、不认识的段落字节不变;
      照对方的规矩升版本号、改 Last updated、在 Changelog 最上面加一行;文件没有就不建(建文件归对方的 skill)

用法(onboard.py 会自动调;也可以手动):
  python3 pm_context.py read  [--repo .] [--json]
  python3 pm_context.py write --repo . --set "Goals/Conversion action=Sign up" [--reason "…"] [--dry-run]
"""
import argparse
import datetime as dt
import json
import os
import re
import sys

PATH = os.path.join(".agents", "product-marketing.md")
# 档案字段 → (段, 标签)。只放一一对应、单行的字段;对不上的(产品线列表等)不硬塞。
FIELDS = {
    "product.one_liner": ("Product Overview", "One-liner"),
    "pricing.model": ("Product Overview", "Business model"),
    "answer.customers": ("Target Audience", "Target companies"),
    "answer.conversion": ("Goals", "Conversion action"),
}
# 读回来当草稿时用的档案键(answer.* 不是事实,换成第 1 环能看到的前缀)
DRAFT_KEYS = {"product.one_liner": "product.one_liner", "pricing.model": "pricing.model",
              "answer.customers": "context.pm_customers", "answer.conversion": "conversion.pm_action"}
EMPTY_RE = re.compile(r"^\s*(\[[^\]]*\]|-|—|n/?a|tbd)?\s*$", re.I)


def path_in(repo):
    return os.path.join(os.path.abspath(repo or "."), PATH)


def _split(text):
    """→ (换行符, 行列表(不含换行), 末尾有没有换行)。"""
    nl = "\r\n" if "\r\n" in text else "\n"
    trailing = text.endswith(("\n", "\r\n"))
    lines = text.split(nl)
    if trailing:
        lines = lines[:-1]
    return nl, lines, trailing


def sections(lines):
    """→ {段名: (起始行号, 结束行号)},段 = `## 段名` 到下一个 `## ` 之前。"""
    out, cur, start = {}, None, None
    for i, ln in enumerate(lines):
        m = re.match(r"^##\s+(.+?)\s*$", ln)
        if m and not ln.startswith("###"):
            if cur is not None:
                out.setdefault(cur, (start, i))
            cur, start = re.sub(r"\s*\(optional\)\s*$", "", m.group(1), flags=re.I), i
    if cur is not None:
        out.setdefault(cur, (start, len(lines)))
    return out


def _label_re(label):
    return re.compile(r"^(\s*\*\*%s:?\*\*:?)(.*)$" % re.escape(label), re.I)


def read_fields(text):
    """→ {"Product Overview/One-liner": "值"}(只收非空、不是模板占位的)。"""
    _, lines, _ = _split(text)
    out = {}
    for sec, (a, b) in sections(lines).items():
        for ln in lines[a + 1:b]:
            m = re.match(r"^\s*\*\*([^*]+?):?\*\*:?\s*(.*)$", ln)
            if m and not EMPTY_RE.match(m.group(2)):
                out["%s/%s" % (sec, m.group(1).strip())] = m.group(2).strip()
    return out


def read_file(repo):
    p = path_in(repo)
    try:
        with open(p, encoding="utf-8", newline="") as f:
            return f.read()
    except OSError:
        return None


def draft_facts(repo):
    """开局用:→ [{"key","value","source","kind"}](值来自这份文件,onboard 一律标「未确认」)。"""
    text = read_file(repo)
    if text is None:
        return []
    got = read_fields(text)
    out = []
    for key, (sec, label) in FIELDS.items():
        v = got.get("%s/%s" % (sec, label))
        if v:
            out.append({"key": DRAFT_KEYS[key], "value": v, "source": PATH, "kind": "fact"})
    return out


def update_text(text, updates, reason, today=None):
    """updates:{(段, 标签): 新值}。→ (新文本, 实际改了的 [(段, 标签, 旧值, 新值)])。
    只改对应那一行;段里没有这个标签就加在段尾;没有这个段就加在 Learnings / Changelog 之前。"""
    today = today or dt.date.today().isoformat()
    nl, lines, trailing = _split(text)
    changed = []
    for (sec, label), value in updates.items():
        value = " ".join(str(value).split())
        secs = sections(lines)
        if sec not in secs:
            anchor = next((secs[s][0] for s in ("Learnings", "Changelog") if s in secs), len(lines))
            block = ["## %s" % sec, "**%s:** %s" % (label, value), ""]
            if anchor > 0 and lines[anchor - 1].strip():
                block = [""] + block
            lines[anchor:anchor] = block
            changed.append((sec, label, None, value))
            continue
        a, b = secs[sec]
        rx = _label_re(label)
        hit = next((i for i in range(a + 1, b) if rx.match(lines[i])), None)
        if hit is None:
            j = b
            while j > a + 1 and not lines[j - 1].strip():
                j -= 1
            lines.insert(j, "**%s:** %s" % (label, value))
            changed.append((sec, label, None, value))
            continue
        m = rx.match(lines[hit])
        old = m.group(2).strip()
        if old == value:
            continue
        lines[hit] = "%s %s" % (m.group(1), value)
        changed.append((sec, label, old or None, value))
    if not changed:
        return text, []
    ver = None
    for i, ln in enumerate(lines):
        m = re.match(r"^(\*\*Document version:\*\*\s*)v?(\d+)(.*)$", ln)
        if m:
            ver = int(m.group(2)) + 1
            lines[i] = "%sv%d%s" % (m.group(1), ver, m.group(3))
            break
    for i, ln in enumerate(lines):
        m = re.match(r"^(\*\*Last updated:\*\*\s*).*$", ln)
        if m:
            lines[i] = m.group(1) + today
            break
    touched = "; ".join("%s / %s" % (s, l) for s, l, _, _ in changed)
    entry = ("- v%d (%s) — %s: %s." % (ver, today, reason, touched) if ver
             else "- %s — %s: %s." % (today, reason, touched))
    secs = sections(lines)
    if "Changelog" in secs:
        a, b = secs["Changelog"]
        j = a + 1
        while j < b and (not lines[j].strip() or lines[j].lstrip().startswith("*")):
            j += 1
        lines.insert(j, entry)
    else:
        if lines and lines[-1].strip():
            lines.append("")
        lines += ["## Changelog", "*Newest first. One line per revision: what changed and why.*", entry]
    out = nl.join(lines) + (nl if trailing else "")
    return out, changed


def write_back(repo, updates, reason, today=None, dry_run=False):
    """→ {"path", "changed", "written"};文件不存在 → None(不建)。"""
    text = read_file(repo)
    if text is None:
        return None
    new, changed = update_text(text, updates, reason, today)
    if changed and not dry_run:
        p = path_in(repo)
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(new)
        os.replace(tmp, p)
    return {"path": PATH, "changed": [{"section": s, "label": l, "old": o, "new": n} for s, l, o, n in changed],
            "written": bool(changed) and not dry_run}


def updates_from_profile(prof, ring):
    """开局某一环确认后要写回的条目:这一环纠正 / 确认过的事实,和第 1 环的 customers、conversion 回答。"""
    out = {}
    for key, (sec, label) in FIELDS.items():
        if key.startswith("answer."):
            v = ((prof.get("rings") or {}).get(str(ring)) or {}).get("answers", {}).get(key.split(".", 1)[1])
            if v and not str(v).startswith("("):
                out[(sec, label)] = v
            continue
        for f in prof.get("facts") or []:
            if f.get("key") == key and f.get("status") in ("corrected", "confirmed") and f.get("value") \
                    and (f.get("ring") in (ring, None)) and not isinstance(f.get("value"), (list, dict)):
                out[(sec, label)] = f["value"]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="读写 .agents/product-marketing.md(和 marketingskills 共用产品上下文)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read")
    r.add_argument("--repo", default=".")
    r.add_argument("--json", action="store_true")
    w = sub.add_parser("write")
    w.add_argument("--repo", default=".")
    w.add_argument("--set", action="append", required=True, help='"段/标签=值",如 "Goals/Conversion action=Sign up"')
    w.add_argument("--reason", default="seo-suite onboarding: user-confirmed update")
    w.add_argument("--dry-run", action="store_true")
    ns = ap.parse_args(argv)
    if ns.cmd == "read":
        text = read_file(ns.repo)
        if text is None:
            print("没有 %s" % path_in(ns.repo))
            return 0
        got = read_fields(text)
        print(json.dumps(got, ensure_ascii=False, indent=1) if ns.json else
              "\n".join("%s: %s" % kv for kv in got.items()) or "(没有填了值的标签)")
        return 0
    ups = {}
    for s in ns.set:
        if "=" not in s or "/" not in s.split("=", 1)[0]:
            print("错误:--set 要写成 \"段/标签=值\":%r" % s, file=sys.stderr)
            return 2
        k, v = s.split("=", 1)
        sec, label = k.split("/", 1)
        ups[(sec.strip(), label.strip())] = v.strip()
    res = write_back(ns.repo, ups, ns.reason, dry_run=ns.dry_run)
    if res is None:
        print("没有 %s,不建(建这份文件归 product-marketing skill)" % path_in(ns.repo))
        return 0
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
