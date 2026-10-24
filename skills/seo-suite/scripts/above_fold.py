#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""above_fold.py — 首屏"5 秒测试": 前 700 字符四元素加权评分 (仅标准库).

用法:
  python3 above_fold.py https://example.com
  python3 above_fold.py https://example.com --chars 700 --timeout 15

模型 (总分 100, >= 70 过):
  headline   权重 0.35 : 取首个 h1/h2/h3 为 headline;
                          命中弱标题正则 ^(Welcome to|The (best|ultimate|complete)|
                          Introducing|We (help|offer|provide)) 扣 30 分;
                          含数字 / 问号 / 动作动词各 +10 (封顶 100); 无任何标题得 0
  value_prop 权重 0.25 : 前 200 字符含具体数字 (2 位以上数字, 或 数字+单位/%/万/倍/元...)
  cta        权重 0.25 : 前 300 字符出现动作动词 (start|get|try|begin|download|book|
                          schedule|开始|免费) 得满; 其次早期链接锚文本含动作动词;
                          再次仅存在早期链接给部分分
  trust      权重 0.15 : 出现 免费试用/免费额度/无需信用卡/随时取消/保证/失败不扣费/
                          按成功计费/退款/free trial/no credit card/cancel anytime/
                          guarantee/refund/not charged for failed 中 >= 1 个

说明: "首屏文本" = 页面可见文本(跳过 script/style 等)按文档顺序的前 N 字符,
      是对真实渲染首屏的近似 (无布局引擎时的保守做法). 取样跳过站点外壳:
      nav、role=navigation/menu/menubar、aria-hidden=true 或 hidden 的下拉、
      Cookie/同意横幅(id/class/aria-label 含 cookie/consent/gdpr/onetrust 等),
      以及 main/article 之外不含 h1 的 <header>(站点页眉菜单).

退出码: >=70 -> 0; <70 -> 1; 抓取失败 -> 2.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; SEOSkill-AboveFold/1.0)"
WEIGHTS = {"headline": 0.35, "value_prop": 0.25, "cta": 0.25, "trust": 0.15}
WEAK_HEADLINE_RE = re.compile(
    r"^(welcome to|the (?:best|ultimate|complete)|introducing|we (?:help|offer|provide))", re.I)
CTA_VERB_RE = re.compile(
    r"\b(?:start|get|try|begin|download|book|schedule)\b|开始|免费", re.I)
HEADLINE_VERB_RE = re.compile(
    r"\b(?:start|get|try|begin|download|book|schedule|learn|discover|master|build)\b|开始|立即|免费|了解|注册|下载|预约|联系", re.I)
SPEC_NUM_RE = re.compile(
    r"\d[\d,.\uFF0C]*\s*(?:%|万|亿|[kKmM]\b|\+|x|X|倍|元|块|\$|€|£|USD|EUR|RMB|天|小时|分钟|秒|人|家|国|城|次|words|users|customers|clients|teams)"
    r"|\d{2,}")
TRUST_RE = re.compile(
    r"免费试用|免费额度|无需信用卡|随时取消|保证|失败不(?:扣费|收费|计费)|按成功(?:计费|收费)|退款|"
    r"free trial|free tier|no credit card|cancel anytime|guarantee|refund|"
    r"not (?:be )?charged for (?:failed|unsuccessful)|pay only for success", re.I)
BLOCK_TAGS = {"p", "div", "br", "li", "tr", "section", "article", "header", "footer",
              "nav", "main", "aside", "table", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6",
              "blockquote", "figure"}


CHROME_ROLES = {"navigation", "menu", "menubar", "menuitem", "alertdialog"}
CONSENT_RE = re.compile(r"cookie|consent|gdpr|onetrust|cookiebot|\bcmp\b|cmp[-_]|cc[-_]banner|privacy[-_]banner", re.I)
# 「跳到正文」链接(WCAG 2.4.1 Bypass Blocks):页内锚点 + 跳过类措辞。平时视觉隐藏,不是首屏内容。
SKIP_LINK_RE = re.compile(
    r"skip\b|jump to|跳过|跳到|跳至|略过|とばして|飛ばして|本文へ|본문|바로가기|"
    r"zum inhalt|inhalt springen|zur navigation|aller au contenu|passer au contenu|"
    r"saltar al|ir al contenido|pular para|vai al contenuto|перейти к", re.I)
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
             "source", "track", "wbr", "param"}


def is_chrome(tag, attrs):
    """站点外壳(菜单/隐藏下拉/同意横幅)—— 首屏取样整段跳过."""
    d = {k.lower(): (v or "") for k, v in attrs}
    if tag == "nav":
        return True
    if d.get("role", "").strip().lower() in CHROME_ROLES:
        return True
    if d.get("aria-hidden", "").strip().lower() == "true" or "hidden" in d:
        return True
    # 初始隐藏、靠脚本按条件显示的块(Alpine.js x-cloak;内联 display:none):不是首屏内容
    # (2026-10-24 spiegel.de:x-cloak 的 404 提示被当成首屏文本)
    if "x-cloak" in d or re.search(r"display\s*:\s*none|visibility\s*:\s*hidden", d.get("style", ""), re.I):
        return True
    ident = " ".join(d.get(k, "") for k in ("id", "class", "aria-label", "data-testid"))
    return bool(CONSENT_RE.search(ident))


class FoldParser(HTMLParser):
    """按文档顺序收集可见文本 / 链接锚文本 / 标题(跳过站点外壳,见 is_chrome)."""

    SKIP = {"script", "style", "noscript", "template", "svg", "title"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text_parts = []
        self.links = []
        self.headings = []
        self._skip_depth = 0
        self._link_buf = None
        self._heading_buf = None
        self._chrome = None          # [tag, 同名嵌套深度]:外壳区内一律不收
        self._content_depth = 0      # main/article 嵌套深度(其外的 <header> 视为站点页眉)
        self._header = None          # [深度, 缓冲 text, 缓冲 links, 缓冲 headings]
        self._main = None            # 进入页眉缓冲时暂存主列表

    def _enter_header(self):
        self._main = (self.text_parts, self.links, self.headings)
        self.text_parts, self.links, self.headings = [], [], []
        self._header = [1]

    def _leave_header(self):
        text, links, heads = self.text_parts, self.links, self.headings
        self.text_parts, self.links, self.headings = self._main
        self._header = self._main = None
        if any(t == "h1" for t, _ in heads):     # 页眉里放了 h1 = 首屏 hero,保留
            self.text_parts.extend(text)
            self.links.extend(links)
            self.headings.extend(heads)

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if self._chrome is not None:
            if tag == self._chrome[0]:
                self._chrome[1] += 1
            return
        if tag not in VOID_TAGS and is_chrome(tag, attrs):
            self._chrome = [tag, 1]
            return
        if tag in ("main", "article"):
            self._content_depth += 1
        if tag == "header":
            if self._header is not None:
                self._header[0] += 1
            elif self._content_depth == 0:
                self._enter_header()
        if tag == "a":
            self._link_buf = []
            d = {k.lower(): (v or "") for k, v in attrs}
            href = d.get("href", "").strip()
            self._link_start = len(self.text_parts)
            self._link_skip_hint = href.startswith("#") and len(href) > 1
            self._link_title = d.get("title", "") + " " + d.get("aria-label", "")
        elif tag in ("h1", "h2", "h3", "h4"):
            self._heading_buf = [tag, []]
        elif tag in BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if self._chrome is not None:
            if tag == self._chrome[0]:
                self._chrome[1] -= 1
                if self._chrome[1] <= 0:
                    self._chrome = None
            return
        if tag in ("main", "article"):
            self._content_depth = max(0, self._content_depth - 1)
        if tag == "header" and self._header is not None:
            self._header[0] -= 1
            if self._header[0] <= 0:
                self._leave_header()
            return
        if tag == "a" and self._link_buf is not None:
            txt = re.sub(r"\s+", " ", "".join(self._link_buf)).strip()
            if getattr(self, "_link_skip_hint", False) and SKIP_LINK_RE.search(
                    txt + " " + getattr(self, "_link_title", "")):
                del self.text_parts[self._link_start:]      # 跳转链接:文本与链接都不计
            elif txt:
                self.links.append(txt)
            self._link_buf = None
            self._link_skip_hint = False
        elif tag in ("h1", "h2", "h3", "h4") and self._heading_buf is not None:
            txt = re.sub(r"\s+", " ", "".join(self._heading_buf[1])).strip()
            if txt:
                self.headings.append((self._heading_buf[0], txt))
            self._heading_buf = None

    def flush(self):
        """文档结束时 <header> 仍未闭合(畸形 HTML):缓冲内容原样并回,不丢正文."""
        if self._header is not None:
            text, links, heads = self.text_parts, self.links, self.headings
            self.text_parts, self.links, self.headings = self._main
            self._header = self._main = None
            self.text_parts.extend(text)
            self.links.extend(links)
            self.headings.extend(heads)

    def handle_data(self, data):
        if self._skip_depth or self._chrome is not None:
            return
        self.text_parts.append(data)
        if self._link_buf is not None:
            self._link_buf.append(data)
        if self._heading_buf is not None:
            self._heading_buf[1].append(data)


def fetch(url, timeout=15.0, max_bytes=3_000_000):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.geturl(), resp.read(max_bytes)
    except urllib.error.HTTPError as e:
        try:
            body = e.read(65536)
        except Exception:
            body = b""
        return e.code, url, body


def decode(body):
    m = re.search(rb'charset=["\']?([\w\-]+)', body[:4096], re.I)
    for enc in ((m.group(1).decode("ascii", "replace") if m else None), "utf-8", "gb18030", "latin-1"):
        if not enc:
            continue
        try:
            return body.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", "replace")


def score_headline(headings):
    """返回 (0-100, 说明)."""
    if not headings:
        return 0, "未找到任何 h1-h4 标题"
    tag, h = headings[0]
    notes = ["首个标题({0}): \"{1}\"".format(tag, h[:60])]
    score = 100
    if WEAK_HEADLINE_RE.match(h):
        score -= 30
        notes.append("命中弱标题模式, 扣 30")
    bonus = 0
    if re.search(r"\d", h):
        bonus += 10
        notes.append("含数字 +10")
    if "?" in h:
        bonus += 10
        notes.append("含问号 +10")
    if HEADLINE_VERB_RE.search(h):
        bonus += 10
        notes.append("含动作动词 +10")
    score += min(bonus, 20)
    return max(0, min(100, score)), "; ".join(notes)


def score_value_prop(fold):
    head = fold[:200]
    m = SPEC_NUM_RE.search(head)
    if m:
        return 100, "前 200 字符含具体数字 \"{0}\"".format(m.group(0))
    return 0, "前 200 字符未见具体数字 (量化价值主张缺失)"


def score_cta(fold, links):
    head = fold[:300]
    m = CTA_VERB_RE.search(head)
    if m:
        return 100, "前 300 字符出现动作动词 \"{0}\"".format(m.group(0))
    for anchor in links[:10]:
        if CTA_VERB_RE.search(anchor):
            return 80, "早期链接锚文本含动作动词: \"{0}\"".format(anchor[:40])
    if links:
        return 40, "前 300 字符无动作动词, 仅存在链接: \"{0}\"".format(links[0][:40])
    return 0, "前 300 字符无动作动词, 也无链接"


def score_trust(fold):
    hits = TRUST_RE.findall(fold[:700])
    if hits:
        return 100, "命中信任语: {0}".format(", ".join(sorted(set(hits))[:4]))
    return 0, "首屏 700 字符无风险反转/信任语"


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="above_fold.py",
        description="首屏 5 秒测试: 前 700 字符 headline/value_prop/cta/trust 四元素加权评分 (stdlib only)")
    ap.add_argument("url", help="待检页面 URL")
    ap.add_argument("--chars", type=int, default=700, help="首屏文本窗口字符数 (默认 700)")
    ap.add_argument("--timeout", type=float, default=15.0, help="抓取超时秒数 (默认 15)")
    args = ap.parse_args(argv)

    url = args.url.strip()
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url

    try:
        status, final, body = fetch(url, args.timeout)
    except Exception as e:
        print("[FATAL] 抓取失败 {0}: {1}: {2}".format(url, type(e).__name__, e), file=sys.stderr)
        return 2
    if status != 200:
        print("[FATAL] HTTP {0} (最终 URL: {1})".format(status, final), file=sys.stderr)
        return 2

    parser = FoldParser()
    try:
        parser.feed(decode(body)[:500000])
    except Exception as e:
        print("[WARN] HTML 解析异常(继续用已解析部分): {0}".format(e), file=sys.stderr)
    parser.flush()

    fold = re.sub(r"\s+", " ", "".join(parser.text_parts)).strip()
    window = fold[:args.chars]

    h_score, h_note = score_headline(parser.headings)
    v_score, v_note = score_value_prop(window)
    c_score, c_note = score_cta(window, parser.links)
    t_score, t_note = score_trust(window)
    scores = {"headline": h_score, "value_prop": v_score, "cta": c_score, "trust": t_score}
    notes = {"headline": h_note, "value_prop": v_note, "cta": c_note, "trust": t_note}

    total = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)
    passed = total >= 70

    print("=" * 76)
    print("above_fold 5 秒测试 | {0} (HTTP {1})".format(final, status))
    print("首屏文本预览: {0}".format(window[:160] + ("..." if len(window) > 160 else "")))
    print("-" * 76)
    print("{0:<12} {1:>6} {2:>7} {3:>7}  说明".format("元素", "权重", "得分", "加权"))
    for k in ("headline", "value_prop", "cta", "trust"):
        print("{0:<12} {1:>6.2f} {2:>7.0f} {3:>7.2f}  {4}".format(
            k, WEIGHTS[k], scores[k], WEIGHTS[k] * scores[k], notes[k]))
    print("-" * 76)
    print("总分: {0:.1f} / 100 -> {1} (阈值 70)".format(
        total, "PASS" if passed else "FAIL"))

    tips = []
    if scores["headline"] < 70:
        tips.append("headline: 换成含数字/问号/动作动词的具体标题, 避开 Welcome to/Introducing 类弱标题")
    if scores["value_prop"] == 0:
        tips.append("value_prop: 在前 200 字符内加入具体数字 (效果/规模/价格/时限)")
    if scores["cta"] < 80:
        tips.append("cta: 在前 300 字符或首个链接里放动作动词 (开始/免费试用/Get started/Book...)")
    if scores["trust"] == 0:
        tips.append("trust: 首屏写一条你真实提供的风险反转 (如免费额度/试用、失败不扣费、按成功计费、退款规则);"
                    "做不到的承诺不要写")
    if tips:
        print("\n建议:")
        for t in tips:
            print("  - {0}".format(t))
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        sys.exit(130)
