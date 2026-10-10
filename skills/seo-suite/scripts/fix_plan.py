#!/usr/bin/env python3
"""审计→修复物生成器(audit → fix artifacts;geo-optimizer 源码口径 borrow-specs C3,安全第一)。
跑(--url,内部调用 site_audit.audit)或读(--audit,site_audit --json 输出文件)单站点审计,
按缺陷生成 6 类修复物 FixItem{category, description, content, file_name, action}:
  robots/llms/schema/meta/ai_discovery(可选类,默认关)/content(只出提纲不自动重写)。
安全契约:默认 dry-run 只打印(每文件预览前 30 行);--apply 才写盘且只写 ./seo-fixes/
隔离目录(从不触碰站点文件);审计失败(fetch guard SKIP)不生成任何修复并退出码 2。
用法: python3 fix_plan.py --url https://example.com [--only robots,llms] [--estimate] [--json] [--apply]
       python3 fix_plan.py --audit audit.json [--only ...] [--estimate] [--json] [--apply]"""
import html
import json
import os
import re
import sys
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import site_audit as sa        # 只读复用:fetch(同一网络代码路径/守卫)/Page 解析/AI_HEALTH_WEIGHTS
import robots_posture as rp    # 只读复用:AI_BOTS 27 bot 三层名单/analyze/fix_robots 三行格式

CATEGORIES = ("robots", "llms", "schema", "meta", "ai_discovery", "content")
DEFAULT_ON = tuple(c for c in CATEGORIES if c != "ai_discovery")  # ai_discovery 可选类默认不生成
FIX_DIR = "seo-fixes"           # --apply 隔离目录(相对 CWD;从不触碰站点文件)
PREVIEW_LINES = 30              # dry-run 每文件预览行数

# 收益预估:类别满分 = ai_search_health 权重 ×100(复用 site_audit.AI_HEALTH_WEIGHTS)。
# 映射:robots→bots / llms→llms_txt / content→content_length 直接对应;
# schema→semantic_html 为代理映射[推断](JSON-LD 补的是结构化语义信号);
# meta(经典 SEO)与 ai_discovery(实验端点)不在 AI 子分权重表内 → 满分 0,不进收益。
CHECK_OF_CATEGORY = {"robots": "bots", "llms": "llms_txt", "schema": "semantic_html",
                     "content": "content_length"}
CATEGORY_MAX = {c: 0 for c in CATEGORIES}
CATEGORY_MAX.update({c: round(100 * sa.AI_HEALTH_WEIGHTS[chk]) for c, chk in CHECK_OF_CATEGORY.items()})

SCHEMA_FAQ_NOTE = ("FAQPage 不生成:Google FAQ 富结果 2026-05-07 全站退役"
                   "(borrow-specs E5 过时信号表;存量保留勿新增,真实问答内容用 QAPage)")


class BadInput(Exception):
    """输入非法(缺参/未知参数/未知类别/审计文件不可读)→ 退出码 2。"""


class AuditRefused(Exception):
    """审计失败(fetch guard SKIP / 页面不可达)→ 不生成任何修复,退出码 2。"""


class FixItem(dict):
    """dataclass 风格的 FixItem(dict):固定五字段;category/action 只取合法值。"""

    def __init__(self, category, description, content, file_name, action):
        if category not in CATEGORIES:
            raise ValueError("未知类别 %r;合法值: %s" % (category, ", ".join(CATEGORIES)))
        if action not in ("create", "append", "snippet"):
            raise ValueError("未知动作 %r;合法值: create, append, snippet" % action)
        if os.path.basename(file_name) != file_name or file_name in (".", ".."):
            raise ValueError("file_name 只允许裸文件名(写入隔离目录 seo-fixes/): %r" % file_name)
        super().__init__(category=category, description=description, content=content,
                         file_name=file_name, action=action)


def preview(content, limit=PREVIEW_LINES):
    """dry-run 预览:前 limit 行 + "... (N remaining lines)";不足 limit 行时原样返回。"""
    lines = content.splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    return "\n".join(lines[:limit]) + "\n... ({} remaining lines)".format(len(lines) - limit)


def llms_structure_issues(t):
    """llms.txt 结构检查——判定正则与 llmstxt.py validate 同源(只读复用,不改其行为):
    H1 存在且唯一 / blockquote 摘要 / 链接>=3 / 无水印字符。"""
    issues = []
    if not re.match(r"^# ", t):
        issues.append("缺 H1")
    if len(re.findall(r"^# ", t, re.M)) > 1:
        issues.append("多个 H1")
    if not re.search(r"^>", t, re.M):
        issues.append("缺 blockquote 摘要")
    links = re.findall(r"^- \[([^\]]+)\]\(([^)]+)\)", t, re.M)
    if len(links) < 3:
        issues.append(f"链接仅 {len(links)} 条(<3)")
    if re.search(r"[\u200b\ufeff]", t):
        issues.append("含 Unicode 水印字符")
    return issues


def _fix_block_body(raw):
    """剥掉 rp.fix_robots 首行标题(其"只打印不写盘"口径属于 robots_posture;fix_plan 产物
    写入 ./seo-fixes/ 隔离目录,人审后部署),保留其分层结构体(三层标题 + "# 描述 /
    User-agent: token / Allow: /"三行格式,与 --fix-robots 输出一致)。"""
    lines = raw.splitlines()
    if lines and lines[0].startswith("== robots.txt 修复建议"):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# 6 类修复物生成器(纯函数:view → FixItem | None)
# ---------------------------------------------------------------------------
def build_robots_fix(view):
    rep = view.get("robots_report")
    if rep is None:  # robots.txt 不可达 → 按缺失处理,给 27 bot 三层全量模板
        synth = {"bots": [dict(b, state="missing", via_wildcard=False) for b in rp.AI_BOTS]}
        body = _fix_block_body(rp.fix_robots(synth))
        content = "\n".join([
            "# robots.txt 全量模板(fix_plan.py 生成——审计发现 /robots.txt 不可达,按缺失处理)。",
            "# 三层名单与三行格式复用 robots_posture.py(27 bot = training 12/search 10/user 5);",
            "# 引用 5 bot(OAI-SearchBot/Claude-SearchBot/PerplexityBot/Googlebot/Applebot)已有专属规则;",
            "# training 层是授权决策——不想喂训练可整组删除,不影响搜索可见性。",
            "Sitemap: " + view["root"] + "/sitemap.xml",
            ""]) + body
        return FixItem("robots", "robots.txt 缺失 → 27 bot 三层模板(引用 5 bot 专属规则)",
                       content, "robots.txt", "create")
    failures = [b["token"] for b in rep["bots"]
                if b["tier"] in ("search", "user") and b["state"] != "allowed"]
    if not failures:  # 封 training 只是授权决策,不触发修复
        return None
    content = ("# 追加到现有 robots.txt 末尾(fix_plan.py 产物,人审后部署;同长规则 Allow 平局胜出,\n"
               "# 追加 Allow: / 即可翻转该 bot 的既有 Disallow: /)。\n\n"
               + _fix_block_body(rp.fix_robots(rep)))
    head = ", ".join(failures[:5]) + ("…" if len(failures) > 5 else "")
    return FixItem("robots", f"引用/按需层 {len(failures)} 个 bot 未放行({head}) → 追加放行块",
                   content, "robots-append.txt", "append")


def build_llms_fix(view):
    ll = view["llms"]
    if ll["exists"] and not ll["issues"]:
        return None
    why = "/llms.txt 缺失" if not ll["exists"] else "llms.txt 结构缺陷(" + "; ".join(ll["issues"]) + ")"
    title = view["page"].get("title") or "YOUR_SITE_NAME"
    desc = view["page"].get("desc") or "YOUR_SITE_DESCRIPTION"
    locs = view["sitemap_locs"][:50]
    L = ["# " + title, "", "> " + desc, "", "## Pages", ""]
    if locs:
        for u in locs:
            L.append("- [%s](%s): YOUR_PAGE_DESCRIPTION" % (u.rsplit("/", 1)[-1] or u, u))
        note = f"{len(locs)} 条来自 sitemap.xml"
    else:
        for i in (1, 2, 3):
            L.append(f"- [YOUR_PAGE_NAME_{i}]({view['root']}/YOUR_PAGE_PATH_{i}): YOUR_PAGE_DESCRIPTION")
        note = "3 条占位(审计未见 sitemap URL)"
    L += ["", f"<!-- 骨架由 fix_plan.py 生成(llmstxt.py generate 同构;{note})——"
          "上线前补每条冒号后的说明,并用 llmstxt.py validate 校验 -->", ""]
    return FixItem("llms", why + " → llms.txt 骨架(H1+blockquote 摘要+## Pages)",
                   "\n".join(L), "llms.txt", "create")


def build_schema_fix(view):
    pg = view["page"]
    jsonld = pg.get("jsonld") or view["meta"].get("jsonld") or 0
    if jsonld > 0 and not any(f.get("area") == "schema" for f in view["findings"]):
        # 已有 JSON-LD 且审计未报缺——是否含 WebSite/Organization 审计不可见,不误报
        return None
    name = pg.get("title") or "YOUR_ORG_NAME"
    root = view["root"]
    website = {"@context": "https://schema.org", "@type": "WebSite", "name": name, "url": root}
    org = {"@context": "https://schema.org", "@type": "Organization", "name": name, "url": root,
           "logo": root + "/YOUR_LOGO_URL", "sameAs": ["https://YOUR_SOCIAL_PROFILE"]}
    L = ["<!-- JSON-LD 片段:粘贴到全站 <head>(审计:无 JSON-LD/缺基础实体)。只补 WebSite+Organization;"
         + SCHEMA_FAQ_NOTE + " -->",
         '<script type="application/ld+json">',
         json.dumps(website, ensure_ascii=False, indent=2),
         "</script>",
         '<script type="application/ld+json">',
         json.dumps(org, ensure_ascii=False, indent=2),
         "</script>", ""]
    return FixItem("schema", "无 JSON-LD → WebSite+Organization 片段(FAQPage 已退役,不生成)",
                   "\n".join(L), "schema-jsonld.html", "snippet")


def build_meta_fix(view):
    pg = view["page"]
    esc = html.escape
    title, desc, canon = pg.get("title"), pg.get("desc"), pg.get("canonical")
    og = pg.get("og") or {}
    missing = []
    if view["source"] == "live":     # live:页面解析真值驱动
        if not title:
            missing.append("title")
        if desc is None:
            missing.append("description")
        if not canon:
            missing.append("canonical")
        for k in ("og:title", "og:description", "og:image"):
            if k not in og:
                missing.append(k)
    else:                            # audit 文件:只有 findings 证据(页面正文不在 JSON 里)
        for f in view["findings"]:
            msg = f.get("message", "")
            if "缺失" not in msg:
                continue
            if f.get("area") == "title":
                missing.append("title")
            elif f.get("area") == "description":
                missing.append("description")
            elif f.get("area") == "canonical":
                missing.append("canonical")
            elif f.get("area") == "og":
                missing.append(msg.split()[0])      # "og:title 缺失" → og:title
    missing = list(dict.fromkeys(missing))
    if not missing:
        return None
    root, url = view["root"], view["url"]
    L = [f"<!-- meta 补全片段:只含缺失的 {len(missing)} 项({', '.join(missing)});"
         "值取页面现有内容或 YOUR_* 占位符,已全部 html.escape -->"]
    if "title" in missing:
        L.append("<title>%s</title>" % esc(title or "YOUR_TITLE"))
    if "description" in missing:
        L.append('<meta name="description" content="%s">' % esc(desc or "YOUR_DESCRIPTION"))
    if "canonical" in missing:
        L.append('<link rel="canonical" href="%s">' % esc(canon or url))  # 缺失时默认自指 canonical
    if "og:title" in missing:
        L.append('<meta property="og:title" content="%s">' % esc(title or "YOUR_TITLE"))
    if "og:description" in missing:
        L.append('<meta property="og:description" content="%s">' % esc(desc or "YOUR_DESCRIPTION"))
    if "og:image" in missing:
        L.append('<meta property="og:image" content="%s">' % esc(og.get("og:image") or root + "/YOUR_OG_IMAGE.png"))
    L.append("")
    return FixItem("meta", f"meta 缺失 {len(missing)} 项({', '.join(missing)}) → 补全片段",
                   "\n".join(L), "meta-tags.html", "snippet")


def build_ai_discovery_fix(view):
    pg = view["page"]
    payload = {
        "_note": f"实验性 AI 发现端点骨架——非公认标准;人审后再决定是否部署到 {view['root']}/ai/summary.json",
        "site_name": pg.get("title") or "YOUR_SITE_NAME",
        "description": pg.get("desc") or "YOUR_SITE_DESCRIPTION",
        "canonical": view["root"],
        "language": "YOUR_LANG(e.g. en/zh/ja)",
        "topics": ["YOUR_TOPIC_1", "YOUR_TOPIC_2"],
        "key_pages": [{"title": "YOUR_PAGE_NAME",
                       "url": view["root"] + "/YOUR_PAGE_PATH",
                       "summary": "YOUR_PAGE_SUMMARY(一句话,目标是被 AI 逐字引用)"}],
    }
    return FixItem("ai_discovery",
                   "可选类(默认不生成,--only ai_discovery 显式开启):ai/summary.json 骨架",
                   json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                   "ai-summary.json", "create")


def build_content_fix(view):
    F = view["findings"]
    checks = {c["id"]: c for c in (view["ai_health"] or {}).get("checks", [])}
    weak = [f for f in F if f.get("area") == "content"]
    too_long = checks.get("content_length", {}).get("pass") is False
    bluf_weak = checks.get("bluf", {}).get("pass") is False
    if not weak and not too_long and not bluf_weak:
        return None
    reasons = ["[%s] content: %s" % (f["severity"], f["message"]) for f in weak]
    if too_long:
        reasons.append("[WARN] content_length: " + checks["content_length"].get("detail", "过长"))
    if bluf_weak:
        reasons.append("[INFO] bluf: " + checks["bluf"].get("detail", "BLUF 不足"))
    words = view["meta"].get("words")
    title = view["page"].get("title") or "YOUR_PAGE_TITLE"
    L = [
        f"# 内容重写提纲:{title}", "",
        "> fix_plan.py 只生成提纲,不做自动重写——人工扩写/改写后重跑 site_audit 验证。", "",
        "## 审计依据(内容信号弱)", "",
        *[f"- {r}" for r in reasons], "",
        "## 重写目标", "",
        (f"- 词数:当前 {words}(soft-thin <200 需扩写;>15000 需拆分成块,AI 上下文过载)"
         if words is not None else "- 词数:按 soft-thin(<200)/过长(>15000)对号处理"),
        "- 首段直答(BLUF):前 100 词内先给答案与事实锚点(AI 引用 38-40% 来自前 100 词,borrow-specs C1)",
        "- 分块:段落独立可解(non-chunked 修复),H1 唯一且 H2>=2", "",
        "## 建议结构(骨架)", "",
        "## <直接回答:一句话核心事实+适用条件>", "",
        "## <展开:机制/步骤/数据>", "",
        "## <常见问题>(真问答用 QAPage;FAQPage 富结果 2026-05 已退役)", "",
        "## 完成检查清单", "",
        "- [ ] 首段 100 词内含直接答案",
        "- [ ] H1 唯一、H2>=2、段落均长 50-200 字符",
        "- [ ] 重跑 python3 scripts/site_audit.py 验证词数与 BLUF 检查", "",
    ]
    return FixItem("content", f"内容信号弱({len(reasons)} 条审计依据) → content-rewrite.md 提纲",
                   "\n".join(L), "content-rewrite.md", "create")


BUILDERS = {"robots": build_robots_fix, "llms": build_llms_fix, "schema": build_schema_fix,
            "meta": build_meta_fix, "ai_discovery": build_ai_discovery_fix,
            "content": build_content_fix}


def build_fixes(view, only=DEFAULT_ON):
    """按规范类别顺序生成所选类别的修复物(触发条件不满足的类别返回 None 被跳过)。"""
    fixes = []
    for cat in CATEGORIES:
        if cat not in only:
            continue
        fx = BUILDERS[cat](view)
        if fx:
            fixes.append(fx)
    return fixes


def estimate(view, fixes):
    """收益预估:修复前 X/100 → 修复后预估 Y/100。
    Y = X + Σ(该类别满分 - 当前得分),封顶 100;类别满分取 ai_search_health 权重
    (CATEGORY_MAX);当前得分 = 对应检查 pass → 满分,fail → 0(通过率加权口径)。
    ai_health 缺失(旧版审计输出)→ None。"""
    ai = view.get("ai_health")
    if not ai:
        return None
    before = ai["score"]
    passed = {c["id"]: c["pass"] for c in ai.get("checks", [])}
    gain, breakdown = 0, []
    for cat in dict.fromkeys(f["category"] for f in fixes):   # 去重保序
        chk = CHECK_OF_CATEGORY.get(cat)
        if chk is None:
            continue
        mx = CATEGORY_MAX[cat]
        cur = mx if passed.get(chk) else 0
        if mx > cur:
            gain += mx - cur
            breakdown.append(f"{cat}:+{mx - cur}")
    after = min(100, before + gain)
    return {"before": before, "after": after, "gain": after - before, "breakdown": breakdown}


def apply_fixes(fixes, out_dir=FIX_DIR):
    """--apply 写盘:只写隔离目录 ./seo-fixes/(file_name 已在 FixItem 校验为裸文件名),
    从不触碰站点文件。返回写入路径列表。"""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for fx in fixes:
        path = os.path.join(out_dir, fx["file_name"])
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fx["content"])
        written.append(path)
    return written


# ---------------------------------------------------------------------------
# 审计视图:--url 现场跑(site_audit.audit)或 --audit 读 site_audit --json 输出
# ---------------------------------------------------------------------------
def _root_of(url):
    pu = urlparse(url)
    return f"{pu.scheme}://{pu.netloc.lower()}"


def view_from_live(url, market="en"):
    """现场审计:内部调用 site_audit.audit(同一 fetch/守卫/解析代码路径);
    sa.fetch 临时换成带记忆的包装,页面与根文件各只抓一次,结果供修复物取值复用。
    SSRF 口径照抄 site_audit:全部网络经 sa.fetch(同 UA/2MB 上限/超时/挑战页守卫),
    --url 仅接受 http(s)://,不另开抓取通道。"""
    if urlparse(url).scheme not in ("http", "https"):
        raise BadInput("--url 仅接受 http(s):// 目标(与 site_audit 同口径;拒绝 file:// 等)")
    root = _root_of(url)
    cache = {}
    orig = sa.fetch

    def cached(u, timeout=15):
        if u not in cache:
            cache[u] = orig(u, timeout)
        return cache[u]

    sa.fetch = cached
    try:
        F, meta, ai = sa.audit(url, market)
    finally:
        sa.fetch = orig
    verdict = ("refused" if any(s == "SKIP" for s, _, _ in F)
               else ("fail" if any(s == "CRITICAL" for s, _, _ in F) else "pass"))
    page = {"title": None, "desc": None, "canonical": None, "og": {}, "jsonld": 0}
    entry = cache.get(url)
    if entry:
        p = sa.Page()
        p.feed(entry[2])
        page = {"title": re.sub(r"\s+", " ", (p.title[0] if p.title else "")).strip() or None,
                "desc": p.desc, "canonical": p.canonical, "og": dict(p.og), "jsonld": p.jsonld}
    robots_entry = cache.get(root + "/robots.txt")
    robots_report = rp.analyze(robots_entry[2]) if robots_entry and robots_entry[0] == 200 else None
    llms_entry = cache.get(root + "/llms.txt")
    llms_ok = bool(llms_entry and llms_entry[0] == 200)
    llms = {"exists": llms_ok,
            "issues": llms_structure_issues(llms_entry[2]) if llms_ok else []}
    locs = []
    sm = cache.get(root + "/sitemap.xml")
    if sm and sm[0] == 200:
        locs = re.findall(r"<loc>([^<]+)</loc>", sm[2])[:50]
    return {"source": "live", "url": url, "root": root, "verdict": verdict,
            "findings": [{"severity": s, "area": a, "message": m} for s, a, m in F],
            "meta": meta or {}, "ai_health": ai,
            "page": page, "robots_report": robots_report, "llms": llms, "sitemap_locs": locs}


def view_from_audit_file(path):
    """读 site_audit --json 输出(离线零网络)。页面正文不在 JSON 里 → meta 值用占位符,
    robots 由 8 bot 放行名单合成 robots_posture 报告,缺失/结构不可见处一律保守不臆断。"""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"审计文件不可读 {path}: {e}")
    results = data.get("results") or {}
    if not results:
        raise BadInput("审计文件无 results 节(需要 site_audit --json 的输出结构)")
    url, r = next(iter(results.items()))          # 单站点:取第一个 URL
    F = r.get("findings") or []
    meta = r.get("meta") or {}
    ai = r.get("ai_search_health") or None
    robots_missing = any(f.get("area") == "robots" and "不可达" in f.get("message", "") for f in F)
    blocked = ((ai or {}).get("bots") or {}).get("blocked", [])
    if robots_missing:
        robots_report = None                        # → build_robots_fix 走全量模板分支
    else:
        robots_report = {"bots": [dict(b, state=("blocked" if b["token"] in blocked else "allowed"),
                                       via_wildcard=False) for b in rp.AI_BOTS]}
    if ai:
        llms_exists = next((c.get("pass") for c in ai.get("checks", [])
                            if c.get("id") == "llms_txt"), False)
    else:                                           # 旧版输出:退回 findings 证据
        llms_exists = not any(f.get("area") == "llms.txt" and "不可达" in f.get("message", "")
                              for f in F)
    return {"source": "audit", "url": url, "root": _root_of(url),
            "verdict": r.get("verdict", "pass"), "findings": F, "meta": meta, "ai_health": ai,
            "page": {"title": meta.get("title") or None, "desc": None, "canonical": None,
                     "og": {}, "jsonld": meta.get("jsonld", 0)},
            "robots_report": robots_report, "llms": {"exists": llms_exists, "issues": []},
            "sitemap_locs": []}


def ensure_auditable(view):
    """审计失败守卫:fetch guard SKIP / 页面不可达 → 拒绝生成任何修复(borrow-specs C3)。"""
    if view["verdict"] == "refused":
        raise AuditRefused("fetch guard SKIP:审计被拒(挑战页/响应过小/HTTP 401·403·429·503)")
    for f in view["findings"]:
        if f.get("severity") == "CRITICAL" and f.get("area") == "fetch":
            raise AuditRefused("fetch 失败:页面不可达(%s)" % f.get("message", ""))


# ---------------------------------------------------------------------------
# 输出:markdown(默认,dry-run 预览)/ --json(FixItem 列表 + estimate)
# ---------------------------------------------------------------------------
def _indent_code(text):
    return ["    " + ln if ln else "" for ln in text.splitlines()] + [""]


def render_markdown(view, fixes, est, applied, show_estimate):
    ai = view["ai_health"] or {}
    L = [f"# SEO Fix Plan — {view['url']}", ""]
    src = "site_audit 内部运行(--url)" if view["source"] == "live" else "审计文件(--audit)"
    L.append(f"- 审计来源: {src} · verdict: **{view['verdict']}** · findings {len(view['findings'])} 条"
             + (f" · AI Search Health **{ai['score']}/100**" if ai else ""))
    if applied:
        L.append("- 模式: **--apply 已写盘** → 隔离目录 `seo-fixes/`(从不触碰站点文件)")
    else:
        L.append("- 模式: **dry-run**(默认只打印;`--apply` 才写盘,且只写 `./seo-fixes/`)")
    if not fixes:
        L += ["", "所选类别全部通过——无需生成修复。"]
        return "\n".join(L) + "\n"
    for n, fx in enumerate(fixes, 1):
        L += ["", f"## [{n}] {fx['category']} — {fx['action']}", "",
              fx["description"] + ".", "",
              f"目标文件: `seo-fixes/{fx['file_name']}`", ""]
        L += _indent_code(preview(fx["content"]))
    if show_estimate and est:
        br = (";" + ", ".join(est["breakdown"])) if est["breakdown"] else ""
        L += ["", f"**收益预估**: 修复前 {est['before']}/100 → 修复后预估 {est['after']}/100 "
              f"(+{est['gain']}{br};类别满分取 ai_search_health 权重,封顶 100)"]
    if applied:
        L += ["", "已写入:"] + [f"- `{p}`" for p in applied]
    return "\n".join(L) + "\n"


USAGE = f"""usage: fix_plan.py (--url URL | --audit audit.json) [--only CATS] [--apply] [--estimate] [--json]
审计→修复物生成器:跑(--url,内部调用 site_audit)或读(--audit,site_audit --json 输出)
审计结果,产出 6 类 FixItem {{category, description, content, file_name, action(create|append|snippet)}}。

输入(二选一):
  --url URL          现场审计(网络全部经 site_audit.fetch 同一代码路径;仅接受 http(s)://)
  --audit audit.json 读 site_audit --json 的输出文件(离线零网络)

修复类别(--only 逗号过滤;合法值: {", ".join(CATEGORIES)};默认全选除 ai_discovery):
  robots        robots.txt 缺失 → 27 bot 三层全量模板;引用/按需层 bot 被封 → 追加放行块
                (复用 robots_posture 27 bot 名单与 --fix-robots 三行格式;封 training 是授权
                决策不算失败,封 search/user 才触发)
  llms          /llms.txt 缺失或缺结构(缺 H1/摘要/链接<3) → llms.txt 骨架(llmstxt 同构)
  schema        无 JSON-LD → WebSite+Organization JSON-LD 片段。FAQPage 不生成——富结果
                2026-05-07 全站退役(存量保留勿新增,真问答用 QAPage)
  meta          title/description/canonical/og 缺失 → meta-tags.html 片段
                (值取页面现有内容或 YOUR_* 占位符,一律 html.escape)
  ai_discovery  可选类,默认不生成;--only ai_discovery 显式开启 → ai/summary.json 骨架
  content       内容信号弱(词数<200 soft-thin/>15000/BLUF<0.5) → content-rewrite.md
                提纲,不做自动重写

安全设计(核心):
  默认 dry-run 只打印;每文件预览前 {PREVIEW_LINES} 行 + "... (N remaining lines)";
  --apply 才写盘,且只写 ./seo-fixes/ 隔离目录(从不触碰/覆盖站点文件);
  审计失败(fetch guard SKIP / 页面不可达)→ 不生成任何修复,退出码 2。

  --estimate    收益预估:修复前 X/100 → 修复后预估 Y/100
                (Y=X+Σ(类别满分-当前得分),封顶 100;类别满分取 ai_search_health 权重:
                robots=bots {CATEGORY_MAX['robots']} / llms=llms_txt {CATEGORY_MAX['llms']} /
                schema=semantic_html {CATEGORY_MAX['schema']}[推断] / content={CATEGORY_MAX['content']};
                meta 与 ai_discovery 不在权重表内 → 满分 0 不进收益)
  --json        结构化输出(FixItem 列表 + estimate;--apply 时附 applied_files)
退出码: 0 正常(含"无需修复"); 2 输入非法/未知类别/审计失败。"""


def _val(args, i, flag):
    if i + 1 >= len(args) or args[i + 1].startswith("-"):
        raise BadInput(f"{flag} 需要一个值")
    return args[i + 1]


def parse_only(arg):
    """--only 解析:逗号分隔;非法类别报错并列出全部合法值;返回按规范顺序去重的元组。"""
    if arg is None:
        return DEFAULT_ON
    cats = tuple(c.strip() for c in arg.split(",") if c.strip())
    if not cats:
        raise BadInput("--only 值为空;合法修复类别: " + ", ".join(CATEGORIES))
    bad = [c for c in cats if c not in CATEGORIES]
    if bad:
        raise BadInput("未知修复类别 %s;合法值: %s" % (", ".join(bad), ", ".join(CATEGORIES)))
    return tuple(c for c in CATEGORIES if c in cats)


def parse_args(argv):
    url = audit_path = only_arg = None
    do_apply = do_estimate = as_json = False
    i = 0
    while i < len(argv):
        x = argv[i]
        if x in ("-h", "--help"):
            return {"help": True}
        elif x == "--url":
            url = _val(argv, i, "--url"); i += 2
        elif x == "--audit":
            audit_path = _val(argv, i, "--audit"); i += 2
        elif x == "--only":
            only_arg = _val(argv, i, "--only"); i += 2
        elif x == "--apply":
            do_apply = True; i += 1
        elif x == "--estimate":
            do_estimate = True; i += 1
        elif x == "--json":
            as_json = True; i += 1
        else:
            raise BadInput(f"未知参数 {x}")
    if bool(url) == bool(audit_path):
        raise BadInput("必须且只能给一个输入:--url URL(现场审计)或 --audit audit.json(读审计输出)")
    return {"url": url, "audit": audit_path, "only": parse_only(only_arg),
            "apply": do_apply, "estimate": do_estimate, "json": as_json, "help": False}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        opts = parse_args(argv)
    except BadInput as e:
        sys.stderr.write(f"[fix_plan] {e}\n{USAGE}\n")
        return 2
    if opts["help"]:
        print(USAGE)
        return 0
    try:
        view = view_from_live(opts["url"]) if opts["url"] else view_from_audit_file(opts["audit"])
        ensure_auditable(view)
    except (BadInput, AuditRefused) as e:
        sys.stderr.write(f"[fix_plan] {e}\n不生成任何修复。\n")
        if opts["json"]:
            print(json.dumps({"error": str(e), "fixes": []}, ensure_ascii=False))
        return 2
    fixes = build_fixes(view, opts["only"])
    est = estimate(view, fixes)
    applied = apply_fixes(fixes) if (opts["apply"] and fixes) else []
    if opts["json"]:
        payload = {"site": view["url"], "source": view["source"], "verdict": view["verdict"],
                   "ai_search_health_score": (view["ai_health"] or {}).get("score"),
                   "dry_run": not opts["apply"], "only": list(opts["only"]),
                   "estimate": est, "fixes": fixes}
        if opts["apply"]:
            payload["applied_files"] = applied
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        print(render_markdown(view, fixes, est, applied, opts["estimate"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
