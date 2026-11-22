#!/usr/bin/env python3
"""grade_blind.py — 例 3 盲比(rubric_example3.json)的准备和汇总。评判本身由主会话另起独立子代理跑,这里不调模型。

  grade.py blind prepare --product P --round ROUND --new-run RUN_NEW --old-run RUN_OLD --out OUT
        [--scenarios F] [--answers-dir D] [--new-skill-dir D] [--old-skill-dir D] [--rubric F]
     → OUT/record.json(种子、A/B 映射、归一化清单、C1–C3 机械分和 unclear,评审看不到)
       OUT/judge_prompt.md(给评判子代理;不提版本)、OUT/evidence_A.txt、OUT/evidence_B.txt
       OUT/cf/new_ws、OUT/cf/old_ws、OUT/cf/prompts.json(反事实检验两次新会话的工作区和首条消息)
  grade.py blind tally --out OUT --judge JUDGE.json [--cf-new-ws WS] [--cf-old-ws WS --cf-old-transcript T]
        [--blind-broken] [--result FILE]
     → 按 rubric.verdict 算「新版 5 项赢 ≥4」和反事实「没跟着变」条数;写 OUT/verdict.json(type=blind_verdict)

读法见 grade.py 文件头 R60。
"""
import argparse
import hashlib
import json
import os
import re
import shutil

import grade as G

RUBRIC = os.path.join(G.HERE, "rubric_example3.json")
GENERIC = {"template", "templates", "tool", "tools", "guide", "guides", "blog", "review", "reviews", "pricing", "price",
           "comparison", "alternative", "landing", "page", "content", "keyword", "index", "search", "free",
           "subscription", "subscri", "plan", "trial", "sign-up", "signup", "注册", "订阅", "试用", "付费", "paid", "工具",
           "博客", "模板", "指南", "ai", "pro", "upgrade", "升级", "monitor", "监控", "editor", "video", "视频"}
NAME_STOP = {"Business", "Competitors", "Competitor", "Whoever", "Ignore", "We", "Our", "The", "They", "Yes", "No",
             "In", "On", "For", "Search", "Reddit", "Garden", "Amazon"}
NEG_C2 = ("不", "别", "暂缓", "先不", "don't", "avoid", "later")
C3_PAGE = ("首页", "定价页", "产品页", "功能页", "对比页", "替代页", "博客", "文章", "文档", "落地页", "分类页", "工具页", "home",
           "pricing", "product page", "landing", "blog", "docs", "category", "template")
C3_METRIC = ("展示", "点击", "CTR", "排名", "收录", "注册", "试用", "订阅", "首充", "下单", "转化", "流量", "引用", "引荐",
             "impressions", "clicks", "rank", "indexed", "sign-up", "trial", "conversion", "traffic", "citation", "referral")
C3_MEASURE = ("GSC", "Search Console", "GA4", "Bing Webmaster", "日志", "log", "rank tracker", "排名跟踪", "对比", "基线",
              "baseline", "前后对比", "A/B", "抽查", "手工检查", "site:")
C3_WEEK = re.compile(r"第\s*\d+\s*[-~–到至]?\s*\d*\s*周|week\s*\d+|W\d+|\d+\s*-\s*\d+\s*weeks?|第\s*\d+\s*个?月|month\s*\d+",
                     re.I)
C3_PATH = re.compile(r"(?:^|[\s(（「:：])/[\w./-]*")
EMOJI = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF️‍]")
SEC_WORDS = ("建议", "推荐", "priorit", "recommend")


def load_rubric(path=None):
    r = G.read_json(path or RUBRIC)
    if not r:
        raise SystemExit("读不到打分表 %s" % (path or RUBRIC))
    return r


# ---------------------------------------------------------------------------
# 取方案条目(rubric.inputs.plan_source)
# ---------------------------------------------------------------------------

LIST_NUM = re.compile(r"^(\s*)\d+[.)、]\s*(.*)$")
LIST_ANY = re.compile(r"^(\s*)(?:\d+[.)、]|[-*•])\s+(.*)$")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEP = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def list_items(lines, numbered=True, start=0):
    pat = LIST_NUM if numbered else LIST_ANY
    items, started = [], False
    i = start
    while i < len(lines):
        ln = lines[i]
        if not numbered and not started and TABLE_ROW.match(ln) and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            j = i + 2
            while j < len(lines) and TABLE_ROW.match(lines[j]):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                items.append({"text": "".join("%s: %s;" % (h, c) for h, c in zip(head, cells) if c), "section": ""})
                j += 1
            return items
        m = pat.match(ln)
        if m:
            started = True
            items.append({"text": m.group(2), "section": ""})
        elif started:
            if ln.strip() == "" and i + 1 < len(lines) and (pat.match(lines[i + 1]) or lines[i + 1][:1].isspace()):
                i += 1
                continue
            if ln[:1].isspace() and ln.strip():
                items[-1]["text"] += "\n" + ln.strip()
            else:
                break
        i += 1
    return items


def section_list(text):
    lines = (text or "").splitlines()
    for i, ln in enumerate(lines):
        if re.match(r"^\s*(?:#{1,6}\s+|\*\*|【)", ln) and G.hits(ln, SEC_WORDS):
            items = list_items(lines, numbered=False, start=i + 1)
            if items:
                return items
    return []


def old_plan_items(tr, ws):
    texts = tr.texts()
    if texts:
        last = texts[-1]["text"]
        items = list_items(last.splitlines(), True)
        if items:
            return items, "最后一条 assistant 文本的第一个编号列表(第 %d 行)" % texts[-1]["line"]
        items = section_list(last)
        if items:
            return items, "最后一条 assistant 文本「建议 / 推荐」小节下的列表(第 %d 行)" % texts[-1]["line"]
    for c in tr.calls():
        p = str((c.get("input") or {}).get("file_path") or "")
        if c["name"] == "Write" and p.lower().endswith(".md"):
            items = list_items(str(c["input"].get("content") or "").splitlines(), True)
            if items:
                return items, "会话写出的 %s" % p
    for root, dirs, fs in os.walk(ws or ""):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for f in sorted(fs):
            if f.lower().endswith(".md"):
                try:
                    with open(os.path.join(root, f), encoding="utf-8") as fh:
                        items = list_items(fh.read().splitlines(), True)
                except OSError:
                    items = []
                if items:
                    return items, os.path.join(root, f)
    return [], None


def new_plan_items(ws):
    pj = G.read_json(os.path.join(G.plan_dir(ws), "plan.json"))
    if isinstance(pj, dict) and isinstance(pj.get("items"), list):
        out = []
        for it in pj["items"]:
            sec = " ".join(str(it.get(f) or "") for f in ("section", "group", "status")) if isinstance(it, dict) else ""
            out.append({"text": "; ".join(G.leaves(it)), "section": sec})
        return out, "plan.json items"
    items, src = G.plan_items(ws)
    return [{"text": it["text"], "section": it.get("section") or ""} for it in items], src


# ---------------------------------------------------------------------------
# 归一化(rubric.normalize)
# ---------------------------------------------------------------------------

def flatten(text):
    s = "\n".join(ln.strip() for ln in (text or "").splitlines())
    s = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"(?m)^\s*#{1,6}\s+", "", s)
    s = re.sub(r"(?m)^\s*(?:[-*•]|\d+[.)、])\s+", "", s)
    s = s.replace("**", "").replace("__", "").replace("`", "")
    s = re.sub(r"(?<![\w*])\*(?!\s)([^*\n]+?)\*(?!\w)", r"\1", s)
    s = re.sub(r"(?<!\w)_([^_\n]+?)_(?!\w)", r"\1", s)
    s = EMOJI.sub("", s)
    return re.sub(r"\s+", " ", s).strip()


def strip(s, patterns):
    for p in patterns:
        s = re.sub(p, "", s, flags=re.I)
    return re.sub(r"\s+", " ", s).strip()


def normalize(items, rubric):
    pats = rubric["normalize"]["strip_patterns"]
    n = int(rubric["inputs"].get("top_n", 10))
    out = []
    for it in items[:n]:
        s = strip(flatten(it["text"]), pats)[:400]
        s = re.sub(r"[。.]+$", "", s).strip()
        out.append({"text": s, "section": strip(flatten(it.get("section") or ""), pats)})
    return out


def render(lst):
    return "\n".join("%d. %s" % (i + 1, x["text"]) for i, x in enumerate(lst))


def seed_of(product, round_id):
    h = hashlib.sha256((str(product) + str(round_id)).encode("utf-8")).hexdigest()[:8]
    return h, int(h, 16)


def cjk_share(lst):
    t = " ".join(x["text"] for x in lst)
    cjk = len(re.findall(r"[㐀-鿿]", t))
    lat = len(re.findall(r"[A-Za-z]", t))
    return cjk / (cjk + lat) if cjk + lat else 0.0


# ---------------------------------------------------------------------------
# C1–C3 机械分
# ---------------------------------------------------------------------------

def competitor_names(sc):
    reply = " ".join((sc.get("simulated_user") or {}).get("3") or [])
    names = []
    for sent in re.split(r"[.。;;!?！？]\s*", reply):
        if re.search(r"(?i)ignore|don't|do not|not |不管|不在乎|不关心", sent):
            continue
        for m in re.finditer(r"[A-Z][\w.'’-]*(?:\s+[A-Z][\w.'’-]*)*", sent):
            w = m.group(0).strip(".")
            parts = w.split()
            while parts and parts[0] in NAME_STOP:
                parts = parts[1:]
            w = " ".join(parts)
            if len(w) >= 3 and w not in NAME_STOP:
                names.append(w)
        for m in re.finditer(r"(?:对手是|竞品是|对手有|竞品有)([^;;。]+)", sent):
            for x in re.split(r"[、,,和与及]|还有", m.group(1)):
                x = x.strip()
                if 2 <= len(x) <= 20 and not re.search(r"[A-Za-z]", x):
                    names.append(x)
    return sorted(set(names))


def fact_nouns(ans):
    f = ans.get("facts") or {}
    pname = str(f.get("product.name") or "")
    vals = []
    for k in ("product.lines", "product.one_liner"):
        v = f.get(k)
        vals += v if isinstance(v, list) else [v] if v else []
    out = set()
    for v in vals:
        for m in re.finditer(r"\b[A-Z][a-z0-9]*[A-Z][\w]*\b|\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*\b", str(v)):
            w = m.group(0)
            if w.lower() != pname.lower() and w.lower() not in GENERIC and w not in NAME_STOP:
                out.add(w)
    return sorted(out)


def c1_items(lst, ans, comps, nouns):
    fm = ans.get("facts_match") or {}
    rows = []
    for i, it in enumerate(lst):
        hw = []
        for k in ("product.lines", "customers", "conversion.primary"):
            for g in fm.get(k) or []:
                hw += G.hits(it["text"], g)
        hw += G.hits(it["text"], comps) + G.hits(it["text"], nouns)
        hit = bool(hw)
        rows.append({"n": i + 1, "hit": hit, "words": sorted(set(hw)),
                     "unclear": hit and all(str(w).lower() in GENERIC for w in hw)})
    return rows


def _neg_before(text, words, span=20):
    low = text.lower()
    occ = []
    for w in words:
        wl = str(w).lower()
        k = low.find(wl)
        while k >= 0:
            occ.append(k)
            k = low.find(wl, k + 1)
    return bool(occ) and all(any(n in low[max(0, k - span):k] for n in NEG_C2) for k in occ)


def c2_items(lst, ans):
    md, mn = ans.get("stage_must_do_match") or [], ans.get("stage_must_not_match") or []
    covered, rows = set(), []
    for i, it in enumerate(lst):
        cov = [k for k, groups in enumerate(md) if G.covers(it["text"], groups)]
        covered |= set(cov)
        viol, unclear, excl = [], [], []
        for k, groups in enumerate(mn):
            if not G.covers(it["text"], groups):
                continue
            if G.hits(it.get("section") or "", G.NEG_SECTION + ("以后",)) or any(
                    _neg_before(it["text"], G.hits(it["text"], g)) for g in groups):
                excl.append(k)
            elif G.hits(it["text"], NEG_C2):
                unclear.append(k)
            else:
                viol.append(k)
        rows.append({"n": i + 1, "covers": cov, "violates": viol, "unclear_must_not": unclear, "negated": excl})
    return rows, sorted(covered)


def c3_items(lst):
    rows = []
    for i, it in enumerate(lst):
        t = it["text"]
        f = {"page": bool(C3_PATH.search(t) or G.hits(t, C3_PAGE)), "metric": bool(G.hits(t, C3_METRIC)),
             "measure": bool(G.hits(t, C3_MEASURE)), "week": bool(C3_WEEK.search(t))}
        miss = [k for k, v in f.items() if not v]
        rows.append({"n": i + 1, "fields": f, "ok": not miss,
                     "unclear": len(miss) == 1 and miss[0] in ("measure", "metric")})
    return rows


def mech(lst, ans, sc):
    comps, nouns = competitor_names(sc), fact_nouns(ans)
    c2, covered = c2_items(lst, ans)
    return {"C1": c1_items(lst, ans, comps, nouns), "C2": c2, "C2_covered": covered, "C3": c3_items(lst),
            "competitors": comps, "nouns": nouns}


# ---------------------------------------------------------------------------
# 证据包、反事实
# ---------------------------------------------------------------------------

def evidence_text(run_info, rubric, sc):
    pats = rubric["normalize"]["strip_patterns"]
    parts = []
    tr = G.Transcript(run_info.get("transcript"))
    for k, r in enumerate(tr.results.values(), 1):
        parts.append("## 工具结果 %d\n%s" % (k, strip_keep_lines(r["text"], pats)))
    n = 0
    for sub in ("seo-ops", "data"):
        d = os.path.join(run_info["ws"], sub)
        for root, dirs, fs in os.walk(d):
            for f in sorted(fs):
                p = os.path.join(root, f)
                try:
                    with open(p, encoding="utf-8") as fh:
                        body = fh.read()
                except (OSError, UnicodeDecodeError):
                    continue
                n += 1
                parts.append("## 文件 %d(%s)\n%s" % (n, os.path.splitext(f)[1] or "无扩展名", strip_keep_lines(body, pats)))
    return "\n\n".join(parts) + "\n"


def strip_keep_lines(text, pats):
    return "\n".join(strip(ln, pats) for ln in (text or "").splitlines())


def cf_profile(product, rubric, spec):
    p = (rubric.get("counterfactual") or {}).get("profiles", {}).get(product)
    if p is None:
        p = (spec.get("example3_counterfactuals") or {}).get(product)
    return p


def _walk_parent(obj, path):
    """和 grade.resolve 同一套路径规则,返回 (父容器, 键);找不到返回 (None, None)。"""
    if isinstance(path, list):
        cur, parent, key = obj, None, None
        for seg in path:
            parent = cur
            if isinstance(seg, dict):
                (fk, fv), = list(seg.items())[:1]
                idx = next((i for i, x in enumerate(cur) if isinstance(x, dict) and x.get(fk) == fv), None) \
                    if isinstance(cur, list) else None
                if idx is None:
                    return None, None
                key = idx
            elif isinstance(cur, list) and str(seg).isdigit():
                key = int(seg)
                if key >= len(cur):
                    return None, None
            elif isinstance(cur, dict) and seg in cur:
                key = seg
            else:
                return None, None
            cur = cur[key]
        return parent, key

    def walk(o, rest):
        if isinstance(o, dict):
            for k in sorted(o, key=lambda x: -len(str(x))):
                ks = str(k)
                if rest == ks:
                    return o, k
                if rest.startswith(ks + "."):
                    r = walk(o[k], rest[len(ks) + 1:])
                    if r[0] is not None:
                        return r
        elif isinstance(o, list):
            head, _, tail = rest.partition(".")
            if head.isdigit() and int(head) < len(o):
                return (o, int(head)) if not tail else walk(o[int(head)], tail)
        return None, None
    return walk(obj, str(path))


def _assign(parent, key, val):
    cur = parent[key]
    if isinstance(cur, dict) and "value" in cur:
        cur["value"] = val
    else:
        parent[key] = val


def rewrite_profile(prof, cf):
    done = []
    schema = prof.get("_schema") if isinstance(prof.get("_schema"), dict) else {}
    for key in ("product.name", "product.one_liner", "product.lines", "pricing.model", "conversion.primary", "customers"):
        if key not in cf:
            continue
        for path in ([schema[key]] if key in schema else []) + ["facts." + key, key]:
            parent, k = _walk_parent(prof, path)
            if parent is not None:
                _assign(parent, k, cf[key])
                done.append(key)
                break
    comp = []

    def walk(o):
        if isinstance(o, dict):
            for k in list(o):
                if "compet" in str(k).lower() and k != "_schema":
                    _assign(o, k, list(cf.get("competitors") or []))
                    comp.append(k)
                else:
                    walk(o[k])
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(prof)
    return done, comp


def build_cf(out, product, new_ws, old_ws, cf, orig_name, args):
    cfd = os.path.join(out, "cf")
    nw, ow = os.path.join(cfd, "new_ws"), os.path.join(cfd, "old_ws")
    for src, dst in ((new_ws, nw), (old_ws, ow)):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git"))
    log = {}
    pp = os.path.join(nw, "seo-ops", "context", "profile.json")
    prof = G.read_json(pp)
    if isinstance(prof, dict):
        done, comp = rewrite_profile(prof, cf)
        with open(pp, "w", encoding="utf-8") as f:
            json.dump(prof, f, ensure_ascii=False, indent=1)
        log.update(profile_keys=done, competitor_keys=comp)
    other = []
    ctx = os.path.join(nw, "seo-ops", "context")
    for root, dirs, fs in os.walk(ctx):
        for f in fs:
            p = os.path.join(root, f)
            if os.path.abspath(p) == os.path.abspath(pp) or not orig_name:
                continue
            try:
                with open(p, encoding="utf-8") as fh:
                    s = fh.read()
            except (OSError, UnicodeDecodeError):
                continue
            if orig_name.lower() in s.lower():
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(re.sub(re.escape(orig_name), cf["product.name"], s, flags=re.I))
                other.append(os.path.relpath(p, nw))
    log["other_context_files_name_replaced"] = other
    shutil.rmtree(os.path.join(nw, "seo-ops", "plan"), ignore_errors=True)
    E = G._sub("grade_ext")
    mk = lambda arm, ws, sd, text: E.SHORT_PROMPT.format(  # noqa: E731
        ws=ws, arm_line=G.ARM_LINE[arm].format(skill_dir=(sd or "").rstrip("/"), repo=G.ROOT), prompt=text)
    prompts = {"new": mk("skill", nw, args.new_skill_dir, "产品信息更新了,按现在的产品信息重新出方案"),
               "old": mk("v043", ow, args.old_skill_dir, cf["as_user_message"] + "\n\n按这些信息重新给 SEO 建议。"),
               "if_it_asks": "停下来问时,按场景的 fallback 原文回话,最多 3 次"}
    with open(os.path.join(cfd, "prompts.json"), "w", encoding="utf-8") as f:
        json.dump(dict(prompts, rewrite=log), f, ensure_ascii=False, indent=1)
    return {"new_ws": nw, "old_ws": ow, "rewrite": log}


# ---------------------------------------------------------------------------
# 反事实相似度
# ---------------------------------------------------------------------------

STOP_W = {"the", "and", "for", "with", "who", "from", "that", "their", "at", "in", "on", "of", "to", "a", "an", "or",
          "by", "is", "are", "our"}


def proper_words(ans, sc, cf):
    phrases = []
    f = (ans or {}).get("facts") or {}
    for k in ("product.name", "product.lines", "customers"):
        v = f.get(k)
        phrases += v if isinstance(v, list) else [v] if v else []
    phrases += competitor_names(sc)
    for k in ("product.name", "product.lines", "customers", "competitors"):
        v = (cf or {}).get(k)
        phrases += v if isinstance(v, list) else [v] if v else []
    words = set()
    for ph in phrases:
        for w in re.findall(r"[A-Za-z][\w'’.-]*", str(ph)):
            w = w.strip(".")
            if len(w) > 2 and w.lower() not in STOP_W:
                words.add(w)
        for run in re.findall(r"[㐀-鿿]{2,}", str(ph)):
            words.add(run)
    return sorted(words, key=len, reverse=True)


def mask(text, words):
    for w in words:
        if re.match(r"[A-Za-z]", w):
            text = re.sub(r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(w), "<P>", text, flags=re.I)
        else:
            text = text.replace(w, "<P>")
    return text


def tokens(text):
    t = text.lower()
    out = set(re.findall(r"<p>|[a-z0-9]+(?:['’][a-z]+)?", t))
    for run in re.findall(r"[㐀-鿿぀-ヿ가-힯]+", t):
        out |= {run[i:i + 2] for i in range(len(run) - 1)} if len(run) > 1 else {run}
    return out


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def cf_unchanged(orig, cfl, words, thr):
    A = [tokens(mask(x["text"], words)) for x in orig]
    B = [tokens(mask(x["text"], words)) for x in cfl]
    pairs = sorted(((jaccard(a, b), i, j) for i, a in enumerate(A) for j, b in enumerate(B)), reverse=True)
    ui, uj, match = set(), set(), {}
    for s, i, j in pairs:
        if i in ui or j in uj:
            continue
        ui.add(i)
        uj.add(j)
        match[i] = (j, round(s, 3))
    same = sorted(i + 1 for i, (j, s) in match.items() if s >= thr)
    return same, {str(i + 1): {"cf_item": j + 1, "jaccard": s} for i, (j, s) in sorted(match.items())}


# ---------------------------------------------------------------------------
# prepare / tally
# ---------------------------------------------------------------------------

def _run_info(run):
    E = G._sub("grade_ext")
    R = E.load_run(run)
    m = (R.get("sessions") or {}).get("main") or {}
    return {"ws": R["ws"], "transcript": m.get("transcript"), "arm": R["arm"], "scenario": R["scenario"],
            "scenarios_file": R["scenarios_file"]}


def judge_prompt(rubric, product, ans, stage, lists, mechs, unclear):
    crit = {c["id"]: c for c in rubric["criteria"]}
    pre = crit["C4_sequencing"].get("prerequisites", {}).get(str(stage), [])
    lines = [
        "# 比较两份 SEO 方案(产品 %s)" % product, "",
        "你是独立评审。下面是同一个产品的两份 SEO 方案,已统一成纯文本清单,分别叫 A 和 B。只比较这两份方案本身。", "",
        "## 方案 A", render(lists["A"]) or "(空)", "", "## 方案 B", render(lists["B"]) or "(空)", "",
        "## 产品事实(答案表)", "```json",
        json.dumps({k: ans.get(k) for k in ("facts", "facts_match", "stage", "stage_must_do", "stage_must_do_match",
                                            "stage_must_not", "stage_must_not_match")}, ensure_ascii=False, indent=1),
        "```", "",
        "## 打分表", "",
        "C1、C2、C3 已由脚本按规则算好(见下面「脚本分」)。你只复核标了 unclear 的条目:每条给出 是 / 否 和一句理由,"
        "理由引用条目原文里的词;不要改其他条目的分。", "",
    ]
    for cid in ("C1_product_grounding", "C2_stage_fit", "C3_actionability"):
        c = crit[cid]
        lines += ["### %s %s" % (cid, c["name"]), c["what"], "规则:" + c["how_mechanical"], "unclear:" + c["unclear"], ""]
    lines += ["### C4_sequencing " + crit["C4_sequencing"]["name"], crit["C4_sequencing"]["what"],
              "规则:" + crit["C4_sequencing"]["judge_rule"],
              "这个产品阶段的前置关系(「A 必须在 B 之前」):" + "; ".join("「%s」在「%s」之前" % (a, b) for a, b in pre), "",
              "### C5_no_fabrication " + crit["C5_no_fabrication"]["name"], crit["C5_no_fabrication"]["what"],
              "规则:" + crit["C5_no_fabrication"]["judge_rule"],
              "证据包:方案 A 的在同目录 evidence_A.txt,方案 B 的在 evidence_B.txt;模拟用户的回话见下。", ""]
    lines += ["## 脚本分(C1–C3)", "```json", json.dumps(mechs, ensure_ascii=False, indent=1), "```", "",
              "## 要你复核的 unclear 条目", "```json", json.dumps(unclear, ensure_ascii=False, indent=1), "```", "",
              "## 输出(只输出这一个 JSON,不要别的文字)", "```json",
              json.dumps({"unclear": {"C1:A3": {"判定": "是", "理由": "引用条目原文"}},
                          "C4": {"A": {"items": {"1": {"类别": ["…"]}}, "violations": 0},
                                 "B": {"items": {}, "violations": 0}},
                          "C5": {"A": {"items": {"1": {"判定": "有据", "理由": "…"}}, "fabrications": 0},
                                 "B": {"items": {}, "fabrications": 0}},
                          "summary": {"C4": {"A分": 0, "B分": 0, "胜者": "tie"},
                                      "C5": {"A分": 0, "B分": 0, "胜者": "tie"}}}, ensure_ascii=False, indent=1),
              "```", "unclear 的键照上面「要你复核」列表里的写;C4 的 violations、C5 的 fabrications 是整数。"]
    return "\n".join(lines) + "\n"


def prepare(args):
    rubric = load_rubric(args.rubric)
    new, old = _run_info(args.new_run), _run_info(args.old_run)
    scenarios = args.scenarios or new["scenarios_file"]
    spec, sc = G.load_scenario(new["scenario"], scenarios)
    answers_dir = args.answers_dir or os.path.join(os.path.dirname(os.path.abspath(scenarios)), "answers")
    ans = G.read_json(os.path.join(answers_dir, sc["product"] + ".json"))
    if not ans:
        raise SystemExit("读不到答案表")
    product = args.product or sc["product"]
    ni, nsrc = new_plan_items(new["ws"])
    oi, osrc = old_plan_items(G.Transcript(old["transcript"]), old["ws"])
    nl, ol = normalize(ni, rubric), normalize(oi, rubric)
    h, seed = seed_of(product, args.round)
    new_is_a = seed % 2 == 1
    lists = {"A": nl if new_is_a else ol, "B": ol if new_is_a else nl}
    mechs = {k: mech(v, ans, sc) for k, v in lists.items()}
    unclear = []
    for side in ("A", "B"):
        for r in mechs[side]["C1"]:
            if r["unclear"]:
                unclear.append({"key": "C1:%s%d" % (side, r["n"]), "问": "命中的词是不是在指这个产品的这条线 / 这类客户",
                                "words": r["words"]})
        for r in mechs[side]["C2"]:
            if r["unclear_must_not"]:
                unclear.append({"key": "C2:%s%d" % (side, r["n"]), "问": "这条是不是真的在建议做禁做项(是=违例)",
                                "must_not": [ans["stage_must_not"][k] for k in r["unclear_must_not"]]})
        for r in mechs[side]["C3"]:
            if r["unclear"]:
                miss = [k for k, v in r["fields"].items() if not v]
                unclear.append({"key": "C3:%s%d" % (side, r["n"]), "问": "条目里有没有「%s」的等价写法(是=合格)" % miss[0]})
    sa, sb = cjk_share(lists["A"]), cjk_share(lists["B"])
    broken = (sa >= 0.5) != (sb >= 0.5) or not nl or not ol
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "judge_prompt.md"), "w", encoding="utf-8") as f:
        f.write(judge_prompt(rubric, product, ans, ans.get("stage"), lists, mechs, unclear))
    for side, info in (("A", new if new_is_a else old), ("B", old if new_is_a else new)):
        with open(os.path.join(args.out, "evidence_%s.txt" % side), "w", encoding="utf-8") as f:
            f.write(evidence_text(info, rubric, sc) + "\n## 模拟用户脚本\n" +
                    json.dumps(sc.get("simulated_user"), ensure_ascii=False, indent=1))
    cf = cf_profile(product, rubric, spec)
    cfo = build_cf(args.out, product, new["ws"], old["ws"], cf, (ans.get("facts") or {}).get("product.name"), args) \
        if cf else None
    rec = {"type": "blind_record", "product": product, "round": args.round, "seed_hex": h, "seed": seed,
           "new_is": "A" if new_is_a else "B", "new_run": os.path.abspath(args.new_run),
           "old_run": os.path.abspath(args.old_run), "new_source": nsrc, "old_source": osrc,
           "lists": lists, "mech": mechs, "unclear": unclear, "cjk_share": {"A": round(sa, 3), "B": round(sb, 3)},
           "blind_broken_auto": broken, "counterfactual": cfo, "cf_profile": cf, "scenarios": os.path.abspath(scenarios),
           "answers_dir": os.path.abspath(answers_dir)}
    with open(os.path.join(args.out, "record.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    return {"out": os.path.abspath(args.out), "judge_prompt": os.path.join(args.out, "judge_prompt.md"),
            "unclear": len(unclear), "blind_broken_auto": broken, "counterfactual": cfo,
            "note": "评判子代理只给 judge_prompt.md 和 evidence_A/B.txt,不给 record.json"}


def _judge_json(path):
    s = open(path, encoding="utf-8").read()
    try:
        return json.loads(s)
    except ValueError:
        m = re.search(r"\{.*\}", s, re.S)
        return json.loads(m.group(0)) if m else {}


def resolve_unclear(judge, key, default):
    v = ((judge or {}).get("unclear") or {}).get(key)
    if not isinstance(v, dict):
        return default, "评审没给,按脚本默认"
    return str(v.get("判定") or "").strip() == "是", v.get("理由")


def side_scores(side, rec, judge, unchanged):
    m = rec["mech"][side]
    c1 = 0
    for r in m["C1"]:
        ok = r["hit"]
        if r["unclear"]:
            ok, _ = resolve_unclear(judge, "C1:%s%d" % (side, r["n"]), True)
        if ok and r["n"] not in unchanged:
            c1 += 1
    viol = 0
    for r in m["C2"]:
        viol += len(r["violates"])
        if r["unclear_must_not"]:
            yes, _ = resolve_unclear(judge, "C2:%s%d" % (side, r["n"]), True)
            viol += len(r["unclear_must_not"]) if yes else 0
    c2 = len(m["C2_covered"]) - 2 * viol
    c3 = 0
    for r in m["C3"]:
        ok = r["ok"]
        if r["unclear"]:
            ok, _ = resolve_unclear(judge, "C3:%s%d" % (side, r["n"]), False)
        c3 += bool(ok)
    c4 = ((judge.get("C4") or {}).get(side) or {}).get("violations")
    c5 = ((judge.get("C5") or {}).get(side) or {}).get("fabrications")
    return {"C1_product_grounding": c1, "C2_stage_fit": c2, "C3_actionability": c3,
            "C4_sequencing": G._int(c4) if c4 is not None else None,
            "C5_no_fabrication": G._int(c5) if c5 is not None else None}


def tally(args):
    rubric = load_rubric(args.rubric)
    rec = G.read_json(os.path.join(args.out, "record.json"))
    if not rec:
        raise SystemExit("读不到 %s/record.json(先跑 blind prepare)" % args.out)
    judge = _judge_json(args.judge)
    spec, sc = G.load_scenario(_run_info(rec["new_run"])["scenario"], rec["scenarios"])
    ans = G.read_json(os.path.join(rec["answers_dir"], sc["product"] + ".json"))
    words = proper_words(ans, sc, rec.get("cf_profile"))
    thr = float(rubric["counterfactual"].get("similarity_threshold", 0.6))
    new_side = rec["new_is"]
    old_side = "B" if new_side == "A" else "A"
    cf = {}
    if args.cf_new_ws:
        items, src = new_plan_items(args.cf_new_ws)
        cf["new"] = cf_unchanged(rec["lists"][new_side], normalize(items, rubric), words, thr) + (src,)
    if args.cf_old_transcript:
        items, src = old_plan_items(G.Transcript(args.cf_old_transcript), args.cf_old_ws)
        cf["old"] = cf_unchanged(rec["lists"][old_side], normalize(items, rubric), words, thr) + (src,)
    unchanged = {new_side: cf["new"][0] if "new" in cf else [], old_side: cf["old"][0] if "old" in cf else []}
    scores = {s: side_scores(s, rec, judge, unchanged[s]) for s in ("A", "B")}
    lower_better = ("C4_sequencing", "C5_no_fabrication")
    crit, new_wins, missing = {}, 0, []
    for c in rubric["criteria"]:
        a, b = scores["A"][c["id"]], scores["B"][c["id"]]
        if a is None or b is None:
            win = None
            missing.append(c["id"])
        elif a == b:
            win = "tie"
        elif (a < b) == (c["id"] in lower_better):
            win = "A"
        else:
            win = "B"
        jw = (((judge.get("summary") or {}).get(c["id"].split("_")[0]) or {}).get("胜者"))
        crit[c["id"]] = {"A": a, "B": b, "winner": win, "new_wins": win == new_side, "judge_said": jw}
        new_wins += win == new_side
    broken = bool(rec.get("blind_broken_auto") or args.blind_broken)
    cf_missing = [k for k in ("new", "old") if k not in cf]
    ok = new_wins >= 4 and not missing and not cf_missing and not broken
    v = {"type": "blind_verdict", "product": rec["product"], "round": rec["round"],
         "mapping": {"seed_hex": rec["seed_hex"], "new": new_side, "old": old_side}, "criteria": crit,
         "new_wins": new_wins, "pass": ok, "blind_broken": broken,
         "counterfactual_unchanged": {"new": len(unchanged[new_side]) if "new" in cf else None,
                                      "old": len(unchanged[old_side]) if "old" in cf else None,
                                      "new_target_max": 2},
         "counterfactual_detail": {k: {"unchanged_items": x[0], "pairs": x[1], "source": x[2]} for k, x in cf.items()},
         "missing": {"judge_scores": missing, "counterfactual": cf_missing}}
    path = args.result or os.path.join(args.out, "verdict.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(v, f, ensure_ascii=False, indent=1)
    return v


def main(argv):
    ap = argparse.ArgumentParser(prog="grade.py blind")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--product")
    p.add_argument("--round", required=True, help="评测轮次 id(和产品 id 一起算种子)")
    p.add_argument("--new-run", required=True, help="被测新版(skill 组)那次开局 run 的目录")
    p.add_argument("--old-run", required=True, help="0.43.0(v043 组)那次开局 run 的目录")
    p.add_argument("--out", required=True)
    p.add_argument("--scenarios")
    p.add_argument("--answers-dir")
    p.add_argument("--new-skill-dir")
    p.add_argument("--old-skill-dir")
    p.add_argument("--rubric")
    t = sub.add_parser("tally")
    t.add_argument("--out", required=True)
    t.add_argument("--judge", required=True, help="评判子代理输出的 JSON(文件里可以夹别的字,取第一个 {...})")
    t.add_argument("--cf-new-ws")
    t.add_argument("--cf-old-ws")
    t.add_argument("--cf-old-transcript")
    t.add_argument("--blind-broken", action="store_true", help="主会话肉眼判定仍能看出版本时加上")
    t.add_argument("--result")
    t.add_argument("--rubric")
    ns = ap.parse_args(argv)
    r = prepare(ns) if ns.cmd == "prepare" else tally(ns)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0
