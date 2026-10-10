#!/usr/bin/env python3
"""ai_views.py — AI 视图层生成器(Scrunch AXP 本地等价物,纯 stdlib 静态净化)。
口径:references/research/borrow-specs.md E9——对重点页产出去 chrome 的**语义版 HTML**与
**Markdown** 两个视图,写到 ./ai-views/<slug>/{ai-view.html, ai-view.md, stats.json};
block 级 before/after(token 估算 len//4 + 转换/移除/保留计数);--diff 对 ai-views/ 里的
上一版本出 section(## 级)变更清单。

定位(边界,写死不放松):给 AI bot 的低噪版本,**人审后自行部署**到如 /ai/ 路径;
本工具只生成本地隔离目录、**从不部署**(部署由人完成)。llms.txt 非可见性杠杆(三份实证,
见 references/research/competitive-landscape.md §llms.txt 裁决:Otterly 90 天实验 0.1% 请求率 /
Ahrefs 13.7 万域研究 97% 文件整月零请求 / Google 官方"非必需")——本工具同理
**不承诺引用提升**,只承诺 token 缩减与语义降噪。

对标:Scrunch AXP 官方实测 123,916→1,355 tokens(98.9% 缩减);本工具为 stdlib 静态净化,
达不到时如实报,不虚标。

用法:
  python3 ai_views.py --url https://example.com/post [--diff] [--apply] [--json]
  python3 ai_views.py --html page.html [--diff] [--apply] [--json]
退出码:0 正常;1 fetch 错误;2 用法错误 / fetch 守卫拒绝(响应过小或挑战页,
守卫口径复制自 site_audit.py,不 import 以保持本脚本独立)。"""
import hashlib
import html as _html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin, urlparse

UA = "Mozilla/5.0 (compatible; seo-suite-ai-views/1.0)"
VIEW_DIR = "ai-views"        # --apply 隔离目录(相对 CWD;从不触碰/覆盖站点文件)
PREVIEW_LINES = 30           # dry-run 每文件预览行数(契约同 fix_plan.py)
MIN_BODY_BYTES = 200         # fetch 质量守卫(复制自 site_audit.py,口径一致)
CHALLENGE_MARKERS = ("just a moment", "attention required", "cf-chl", "cf-browser-verification",
                     "challenge-platform", "checking your browser", "verify you are human",
                     "unusual traffic", "access denied", "captcha", "ddos-guard", "perimeterx",
                     "px-captcha")
# Scrunch AXP 官方实测(borrow-specs E9)——仅作对标参照,不作本工具承诺
SCRUNCH_BEFORE, SCRUNCH_AFTER, SCRUNCH_PCT = 123916, 1355, 98.9

# ---- 净化规则表 ----
DROP_WITH_CONTENT = frozenset(("script", "style", "noscript", "iframe", "svg", "template",
                               "object", "embed", "canvas", "audio", "video", "map"))
DROP_FORM_CONTROLS = frozenset(("input", "select", "textarea"))   # 无文本价值,整块移除
KEEP_ATTRS = frozenset(("href", "aria-label"))                    # 仅此两项存活(href 仅 <a>)
META_OG_KEEP = ("og:title", "og:description", "og:image")         # og 三件套
BLOCK_TAGS = frozenset(("header", "nav", "main", "article", "section", "aside", "footer",
                        "h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "li", "dl", "dt",
                        "dd", "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption",
                        "figure", "figcaption", "blockquote", "pre", "hr", "br", "address",
                        "details", "summary"))
INLINE_TAGS = frozenset(("a", "strong", "em", "b", "i", "code", "small", "mark", "time"))
VOID_TAGS = frozenset(("area", "base", "br", "col", "embed", "hr", "img", "input", "link",
                       "meta", "param", "source", "track", "wbr"))
HEAD_TAGS = frozenset(("h1", "h2", "h3", "h4", "h5", "h6"))

USAGE = """usage: ai_views.py (--url URL | --html FILE) [--apply] [--diff] [--json]
AI 视图层生成器(Scrunch AXP 本地等价物):对重点页产出去 chrome 的语义版 HTML + Markdown
两个视图,写到 ./%s/<slug>/{ai-view.html, ai-view.md, stats.json}。
  --url URL     在线抓取(fetch 守卫同 site_audit:响应过小/挑战页特征 → 拒产出 [SKIP])
  --html FILE   离线读本地 HTML fixture(零网络)
  --apply       写盘(默认 dry-run 只打印预览;只写 ./%s/ 隔离目录——从不部署,部署由人完成)
  --diff        ./%s/ 已有上一版本时输出 section(## 级)变更清单(新增/删除/内容变更)
  --json        结构化输出(tokens/blocks/meta/diff,供 agent 消费)
净化规则:去 script/style/noscript/iframe/svg/注释/内联事件属性/追踪属性(data-* 全删,
aria-* 只留 aria-label);header/nav/main/article/section/h1-h6/dl/dt/dd/table 语义骨架保留,
装饰 class 全剥;meta 只留 title/description/canonical/og 三件套;图片转 [image: alt] 占位;
表单按钮去交互留文本(input/select/textarea 整块移除)。
token 口径:len(text)//4;输出 original: {{N}} tokens → ai-view: {{M}} tokens ({{pct}}%% 缩减),
对标 Scrunch 官方实测 98.9%%(123,916→1,355)——达不到时如实报,不虚标。
定位:给 AI bot 的低噪版本,人审后自行部署到如 /ai/ 路径;llms.txt 非可见性杠杆(三份实证:
Otterly 90 天 0.1%% 请求率/Ahrefs 13.7 万域 97%% 整月零请求/Google 官方"非必需"),
本工具同理不承诺引用提升。
退出码:0 正常;1 fetch 错误;2 用法错误或 fetch 守卫拒绝。""" % (VIEW_DIR, VIEW_DIR, VIEW_DIR)


# ---- fetch 守卫(小函数复制自 site_audit.py,只读复用其口径,不 import) ----

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read(2_000_000).decode("utf-8", "replace")


def looks_like_challenge(html_text):
    head = html_text[:4000].lower()
    return any(m in head for m in CHALLENGE_MARKERS)


# ---- 轻量节点树(HTMLParser 流式构建) ----

class Node:
    __slots__ = ("tag", "attrs", "children")

    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []          # 元素项为 Node,文本项为 str


def _clean(s):
    return re.sub(r"\s+", " ", s)


def _esc(s, quote=False):
    return _html.escape(s, quote=quote)


def _raw_text(node):
    """pre 子树的原文(不折叠空白)。"""
    if isinstance(node, str):
        return node
    return "".join(_raw_text(c) for c in node.children)


class Purifier(HTMLParser):
    """语义净化器:DROP 集(含内容)整块移除;语义骨架保留但剥装饰/追踪属性;
    img→[image: alt] 占位;表单去交互留文本;meta 白名单外丢弃。"""

    def __init__(self, base_url=None):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.root = Node("#root")
        self.stack = [("#root", self.root)]      # (tag, node|None);None=解包透传
        self._skip_tag = None
        self._skip_depth = 0
        self._title_buf = None
        self.meta = {"title": None, "description": None, "canonical": None, "og": {}}
        self.lang = None
        self.stats = {"converted": 0, "removed": 0, "kept": 0,
                      "attrs_stripped": 0, "meta_dropped": 0}

    def _parent(self):
        for _, node in reversed(self.stack):
            if node is not None:
                return node
        return self.root

    # -- 事件 --
    def handle_starttag(self, tag, attrs):
        if self._skip_tag:
            if tag == self._skip_tag and tag not in VOID_TAGS:
                self._skip_depth += 1
            return
        d = {}
        for k, v in attrs:
            d[k] = v if v is not None else ""
        if tag in DROP_WITH_CONTENT:
            self._skip_tag, self._skip_depth = tag, 1
            self.stats["removed"] += 1
            return
        if tag in DROP_FORM_CONTROLS:
            # input 无子内容;select/textarea 连子树一起移除(否则 option 文本会漏进视图)
            self.stats["removed"] += 1
            if tag == "input":
                return
            self._skip_tag, self._skip_depth = tag, 1
            return
        if tag == "html":
            if d.get("lang"):
                self.lang = d["lang"].strip()
            return
        if tag in ("head", "body"):
            return                                   # 骨架自建,原文档骨架解包
        if tag == "title":
            self.stack.append(("title", None))
            self._title_buf = []
            return
        if tag == "meta":
            name = d.get("name", "").lower()
            prop = d.get("property", "").lower()
            if name == "description" and not self.meta["description"]:
                self.meta["description"] = d.get("content", "")
            elif prop in META_OG_KEEP and prop not in self.meta["og"]:
                self.meta["og"][prop] = d.get("content", "")
            else:
                self.stats["meta_dropped"] += 1
            return
        if tag == "link":
            if d.get("rel", "").lower().strip() == "canonical" and not self.meta["canonical"]:
                self.meta["canonical"] = d.get("href", "")
            else:
                self.stats["meta_dropped"] += 1
            return
        if tag == "img":
            alt = d.get("alt", "").strip()
            self._parent().children.append("[image: %s]" % alt if alt else "[image]")
            self.stats["converted"] += 1
            return
        if tag == "br":
            self._parent().children.append(Node("br"))
            self.stats["kept"] += 1
            return
        if tag == "hr":
            self._parent().children.append(Node("hr"))
            self.stats["kept"] += 1
            return
        if tag in BLOCK_TAGS or tag in INLINE_TAGS:
            keep = {}
            if tag == "a" and d.get("href"):
                keep["href"] = (urljoin(self.base_url, d["href"])
                                if self.base_url else d["href"])
            if d.get("aria-label"):
                keep["aria-label"] = d["aria-label"]
            self.stats["attrs_stripped"] += len(d) - len(keep)
            node = Node(tag, keep)
            self._parent().children.append(node)
            self.stats["kept"] += 1
            self.stack.append((tag, node))
            return
        # 其余(div/span/form/button/label 等非语义包装):解包,子内容上提
        self.stats["converted"] += 1
        self.stack.append((tag, None))

    def handle_endtag(self, tag):
        if self._skip_tag:
            if tag == self._skip_tag:
                self._skip_depth -= 1
                if self._skip_depth <= 0:
                    self._skip_tag = None
            return
        if tag == "title" and self._title_buf is not None:
            self.meta["title"] = _clean("".join(self._title_buf)).strip()
            self._title_buf = None
            for i in range(len(self.stack) - 1, 0, -1):
                if self.stack[i][0] == "title":
                    del self.stack[i:]
                    break
            return
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]                   # 自动闭合未关子元素
                return
        # 无匹配结束标签:忽略

    def handle_data(self, data):
        if self._skip_tag:
            return
        if self._title_buf is not None:
            self._title_buf.append(data)
            return
        if data:
            self._parent().children.append(data)

    def handle_comment(self, data):
        if not self._skip_tag:
            self.stats["removed"] += 1


# ---- 语义 HTML 视图渲染 ----

def _render_html_node(node):
    if isinstance(node, str):
        return _esc(_clean(node))
    tag = node.tag
    if tag == "br":
        return "<br>"
    if tag == "hr":
        return "\n<hr>"
    attrs = ""
    if tag == "a" and node.attrs.get("href"):
        attrs += ' href="%s"' % _esc(node.attrs["href"], quote=True)
    if node.attrs.get("aria-label"):
        attrs += ' aria-label="%s"' % _esc(node.attrs["aria-label"], quote=True)
    if tag == "pre":
        return "\n<pre>%s</pre>" % _esc(_raw_text(node))
    inner = "".join(_render_html_node(c) for c in node.children)
    out = "<%s%s>%s</%s>" % (tag, attrs, inner, tag)
    return "\n" + out if tag in BLOCK_TAGS else out


def render_document(p):
    m = p.meta
    lines = ["<!doctype html>",
             '<html lang="%s">' % _esc(p.lang or "", quote=True) if p.lang else "<html>",
             "<head>", '<meta charset="utf-8">']
    if m["title"] is not None:
        lines.append("<title>%s</title>" % _esc(m["title"]))
    if m["description"]:
        lines.append('<meta name="description" content="%s">' % _esc(m["description"], quote=True))
    if m["canonical"]:
        lines.append('<link rel="canonical" href="%s">' % _esc(m["canonical"], quote=True))
    for k in META_OG_KEEP:
        if k in m["og"]:
            lines.append('<meta property="%s" content="%s">' % (k, _esc(m["og"][k], quote=True)))
    lines.append("</head>")
    lines.append("<body>")
    body = re.sub(r"\n{2,}", "\n",
                  "".join(_render_html_node(c) for c in p.root.children).strip())
    if body:
        lines.append(body)
    lines.append("</body>")
    lines.append("</html>")
    return "\n".join(lines) + "\n"


# ---- Markdown 视图渲染 ----

def _heading_md(tag, title_present):
    n = int(tag[1])
    if title_present and n == 1:
        n = 2          # title 已占 H1;正文 h1 降为 h2(h2-h6 原级映射)
    return min(n, 6)


def _md_inline(nodes):
    parts = []
    for c in nodes:
        if isinstance(c, str):
            parts.append(_clean(c))
            continue
        t = c.tag
        if t == "br":
            parts.append("\n")
        elif t == "a":
            txt = _md_inline(c.children).strip()
            href = c.attrs.get("href", "")
            if txt and href:
                parts.append("[%s](%s)" % (txt, href))
            elif href:
                parts.append("<%s>" % href)
            else:
                parts.append(txt)
        elif t in ("strong", "b"):
            inner = _md_inline(c.children).strip()
            if inner:
                parts.append("**%s**" % inner)
        elif t in ("em", "i"):
            inner = _md_inline(c.children).strip()
            if inner:
                parts.append("*%s*" % inner)
        elif t == "code":
            parts.append("`%s`" % _md_inline(c.children).strip())
        else:
            parts.append(_md_inline(c.children))
    return "".join(parts)


def _md_list(node, ordered, indent, out, title_present):
    idx = 1
    for c in node.children:
        if not (isinstance(c, Node) and c.tag == "li"):
            continue
        marker = "%d. " % idx if ordered else "- "
        inline_items, extra_blocks = [], []
        for x in c.children:
            if isinstance(x, Node) and x.tag in BLOCK_TAGS and x.tag != "br":
                extra_blocks.append(x)
            else:
                inline_items.append(x)
        out.append((indent + marker + _md_inline(inline_items).strip()).rstrip())
        for b in extra_blocks:
            if b.tag in ("ul", "ol"):
                _md_list(b, b.tag == "ol", indent + "    ", out, title_present)
            elif b.tag in HEAD_TAGS or b.tag == "p":
                t = _md_inline(b.children).strip()
                if t:
                    out.append(indent + "    " + t)
            else:
                sub = []
                _md_block(b, sub, title_present)
                for ln in sub:
                    out.append(indent + "    " + ln)
        idx += 1


def _md_dl(node, out):
    dt = None
    for c in node.children:
        if not isinstance(c, Node):
            continue
        if c.tag == "dt":
            t = _md_inline(c.children).strip()
            if t:
                dt = t
        elif c.tag == "dd":
            out.append("- **%s**: %s" % (dt or "—", _md_inline(c.children).strip()))
            dt = None


def _md_table(node, out):
    rows = []

    def walk(n):
        for c in n.children:
            if isinstance(c, Node):
                if c.tag == "tr":
                    rows.append(c)
                elif c.tag in ("thead", "tbody", "tfoot"):
                    walk(c)

    walk(node)
    cells_rows = []
    for tr in rows:
        cells = [_md_inline(c.children).strip().replace("|", "\\|")
                 for c in tr.children if isinstance(c, Node) and c.tag in ("th", "td")]
        if cells:
            cells_rows.append(cells)
    if not cells_rows:
        return
    width = max(len(r) for r in cells_rows)
    for r in cells_rows:
        r.extend([""] * (width - len(r)))
    out.append("| " + " | ".join(cells_rows[0]) + " |")
    out.append("| " + " | ".join(["---"] * width) + " |")
    for r in cells_rows[1:]:
        out.append("| " + " | ".join(r) + " |")


def _md_container(children, out, title_present, prefix=""):
    """容器下钻:连续 inline 流(文本+行内标签)积成段落,块级子元素递归。"""
    buf = []

    def flush():
        txt = _md_inline(buf).strip()
        buf.clear()
        if txt:
            for ln in txt.splitlines():
                out.append((prefix + ln).rstrip())

    for c in children:
        if isinstance(c, str) or (isinstance(c, Node) and (c.tag in INLINE_TAGS or c.tag == "br")):
            buf.append(c)
        elif isinstance(c, Node):
            flush()
            _md_block(c, out, title_present)
    flush()


def _md_block(node, out, title_present):
    tag = node.tag
    if tag in HEAD_TAGS:
        txt = _md_inline(node.children).strip()
        if txt:
            out.append("%s %s" % ("#" * _heading_md(tag, title_present), txt))
    elif tag == "p":
        _md_container(node.children, out, title_present)
    elif tag in ("ul", "ol"):
        _md_list(node, tag == "ol", "", out, title_present)
    elif tag == "dl":
        _md_dl(node, out)
    elif tag == "table":
        _md_table(node, out)
    elif tag == "blockquote":
        _md_container(node.children, out, title_present, prefix="> ")
    elif tag == "pre":
        out.append("```\n%s\n```" % _raw_text(node).strip("\n"))
    elif tag == "hr":
        out.append("---")
    elif tag == "br":
        pass
    elif tag in INLINE_TAGS:
        txt = _md_inline([node]).strip()
        if txt:
            out.append(txt)
    else:   # header/nav/main/article/section/aside/footer/figure 等语义容器:透明下钻
        _md_container(node.children, out, title_present)


def render_markdown(p):
    title = p.meta["title"]
    blocks = []
    _md_container(p.root.children, blocks, bool(title))
    md = "# %s\n\n" % title if title else ""
    md += "\n\n".join(b for b in blocks if b.strip()) + "\n"
    return re.sub(r"\n{3,}", "\n\n", md)


# ---- 统计 / diff / 杂项 ----

def estimate_tokens(text):
    return len(text) // 4


def make_slug(url=None, html_path=None):
    if url:
        u = urlparse(url)
        segs = [s for s in u.path.split("/") if s]
        base = os.path.splitext(unquote(segs[-1]))[0] if segs else (u.netloc or "page")
    else:
        base = os.path.splitext(os.path.basename(html_path or "") or "page")[0]
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", base).strip("-").lower()
    return s[:60].strip("-") or "page"


def md_sections(md):
    """section = ## 级标题切分的区块(标题→正文 sha1 前 10 位)。"""
    order, hashes = [], {}
    cur, buf = None, []
    for line in md.splitlines():
        m = re.match(r"^## (.+)$", line)
        if m:
            if cur is not None:
                hashes[cur] = hashlib.sha1("\n".join(buf).encode("utf-8")).hexdigest()[:10]
            cur = m.group(1).strip()
            order.append(cur)
            buf = []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        hashes[cur] = hashlib.sha1("\n".join(buf).encode("utf-8")).hexdigest()[:10]
    return order, hashes


def diff_sections(old_md, new_md):
    _, old = md_sections(old_md)
    order_new, new = md_sections(new_md)
    return {"added": [h for h in order_new if h not in old],
            "removed": [h for h in old if h not in new],
            "changed": [h for h in order_new if h in old and old[h] != new[h]]}


def preview(text, limit=PREVIEW_LINES):
    """dry-run 预览:前 limit 行 + "... (N remaining lines)"(契约同 fix_plan.py)。"""
    lines = text.splitlines()
    if len(lines) <= limit:
        return text
    return "\n".join(lines[:limit]) + "\n... (%d remaining lines)" % (len(lines) - limit)


def build_views(html_text, base_url=None):
    p = Purifier(base_url=base_url)
    p.feed(html_text)
    p.close()
    return p, render_document(p), render_markdown(p)


def _bench_note(pct):
    if pct >= SCRUNCH_PCT:
        return "达到 Scrunch 官方实测口径(98.9%)"
    return ("低于 Scrunch 官方实测 98.9%(123,916→1,355 tokens)——如实报:"
            "纯 stdlib 静态净化无其全量管线,勿对外虚标")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if any(a in ("-h", "--help") for a in args):
        print(USAGE)
        return 0
    if not args:
        sys.stderr.write(USAGE + "\n")
        return 2
    url = html_path = None
    do_apply = do_diff = as_json = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--url" and i + 1 < len(args):
            url = args[i + 1]; i += 2
        elif a == "--html" and i + 1 < len(args):
            html_path = args[i + 1]; i += 2
        elif a == "--apply":
            do_apply = True; i += 1
        elif a == "--diff":
            do_diff = True; i += 1
        elif a == "--json":
            as_json = True; i += 1
        else:
            sys.stderr.write("未知参数: %s\n%s\n" % (a, USAGE))
            return 2
    if bool(url) == bool(html_path):
        sys.stderr.write("必须且只能提供 --url 或 --html 之一\n" + USAGE + "\n")
        return 2

    # 取页面(fetch 守卫口径同 site_audit:过小/挑战页拒绝产出,不算页面失败)
    if url:
        source = url
        try:
            _, html_text = fetch(url)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429, 503):
                print("[SKIP] fetch guard: response too small / likely challenge page "
                      "(HTTP %d); refusing to generate" % e.code)
                return 2
            print("[CRITICAL] fetch: %s" % e)
            return 1
        except Exception as e:
            print("[CRITICAL] fetch: %s" % e)
            return 1
    else:
        source = html_path
        try:
            with open(html_path, encoding="utf-8", errors="replace") as f:
                html_text = f.read()
        except OSError as e:
            sys.stderr.write("读 %s 失败: %s\n" % (html_path, e))
            return 2
    if len(html_text.strip()) < MIN_BODY_BYTES:
        print("[SKIP] fetch guard: response too small / likely challenge page "
              "(%d bytes); refusing to generate" % len(html_text))
        return 2
    if looks_like_challenge(html_text):
        print("[SKIP] fetch guard: response too small / likely challenge page "
              "(challenge markers); refusing to generate")
        return 2

    slug = make_slug(url=url, html_path=html_path)
    out_dir = os.path.join(VIEW_DIR, slug)
    p, ai_html, ai_md = build_views(html_text, base_url=url)

    orig_t = estimate_tokens(html_text)
    html_t = estimate_tokens(ai_html)
    md_t = estimate_tokens(ai_md)
    pct = round((1 - html_t / orig_t) * 100, 1) if orig_t else 0.0
    tokens = {"original": orig_t, "ai_html": html_t, "ai_md": md_t,
              "reduction_pct": pct}

    # --diff:与 ai-views/ 里上一版本比较(读旧文件须在写盘之前)
    old_path = os.path.join(out_dir, "ai-view.md")
    old_md = None
    if do_diff and os.path.isfile(old_path):
        with open(old_path, encoding="utf-8") as f:
            old_md = f.read()
    diff = diff_sections(old_md, ai_md) if old_md is not None else None

    stats_payload = {"tool": "ai_views", "source": source, "slug": slug,
                     "generated": datetime.now().isoformat(timespec="seconds"),
                     "deploy": "manual-only(从不部署,人审后自行部署到如 /ai/ 路径)",
                     "tokens": tokens, "blocks": p.stats,
                     "meta": dict(p.meta, lang=p.lang)}
    files = {"ai-view.html": ai_html, "ai-view.md": ai_md,
             "stats.json": json.dumps(stats_payload, ensure_ascii=False, indent=1) + "\n"}

    applied = {}
    if do_apply:
        os.makedirs(out_dir, exist_ok=True)
        for name, content in files.items():
            fp = os.path.join(out_dir, name)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            applied[name] = fp

    if as_json:
        print(json.dumps({
            "tool": "ai_views", "source": source, "slug": slug, "out_dir": out_dir,
            "mode": "applied" if do_apply else "dry-run",
            "deploy": "manual-only",
            "files": applied if do_apply else {k: None for k in files},
            "tokens": tokens,
            "benchmark": {"scrunch_pct": SCRUNCH_PCT, "ours_pct": pct,
                          "meets": pct >= SCRUNCH_PCT},
            "blocks": p.stats, "meta": dict(p.meta, lang=p.lang),
            "diff": (diff if diff is not None
                     else ("no-previous" if do_diff else None)),
        }, ensure_ascii=False, indent=1))
        return 0

    print("== ai_views: %s → ./%s/%s/ ==" % (source, VIEW_DIR, slug))
    print("[定位] 给 AI bot 的低噪版本;人审后自行部署到如 /ai/ 路径——本工具从不部署,部署由人完成")
    print('[口径] llms.txt 非可见性杠杆(三份实证:Otterly 90 天 0.1% 请求率/'
          'Ahrefs 13.7 万域 97% 整月零请求/Google 官方"非必需");本工具同理不承诺引用提升')
    print("original: %d tokens → ai-view: %d tokens (%s%% 缩减)(%s)"
          % (orig_t, html_t, pct, _bench_note(pct)))
    print("markdown 视图: %d tokens" % md_t)
    print("blocks: 转换 %d / 移除 %d / 保留 %d(属性剥离 %d 项,head 元素移除 %d 项)"
          % (p.stats["converted"], p.stats["removed"], p.stats["kept"],
             p.stats["attrs_stripped"], p.stats["meta_dropped"]))
    if do_diff:
        if diff is None:
            print("[diff] 无上一版本(./%s 不存在),跳过" % old_path)
        else:
            print("[diff] vs 上一版本(section=## 级): 新增 %d / 删除 %d / 内容变更 %d"
                  % (len(diff["added"]), len(diff["removed"]), len(diff["changed"])))
            for h in diff["added"]:
                print("  + " + h)
            for h in diff["removed"]:
                print("  - " + h)
            for h in diff["changed"]:
                print("  ~ " + h)
    print("--- ai-view.html(预览前 %d 行)---" % PREVIEW_LINES)
    print(preview(ai_html))
    print("--- ai-view.md(预览前 %d 行)---" % PREVIEW_LINES)
    print(preview(ai_md))
    if do_apply:
        for name, fp in applied.items():
            print("[写盘] %s" % fp)
        print("模式: --apply 已写盘 → ./%s/(从不部署,人审后自行部署)" % out_dir)
    else:
        print("模式: dry-run(--apply 才写盘,只写 ./%s/;从不部署)" % VIEW_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
