#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""trust_signals.py — 页面信任信号四维计分 (仅标准库).

用法:
  python3 trust_signals.py https://example.com
  python3 trust_signals.py https://example.com --timeout 20

模型 (满分 100):
  证言 testimonials   <=35: blockquote 或引号长文本(>=40 字符)达 >=3 段 -> 25 分;
                          其中含数字 且 有署名/头衔 -> 再 +10
  社会证明 social     <=30: 客户/用户数、trusted by/服务过、结果类数字、百分比成果,
                          命中 3 类 -> 30, 2 类 -> 20, 1 类 -> 10
  风险反转 risk       <=25: 4 类 (free trial / no credit card / cancel anytime /
                          guarantee 及中文对应) 中 >=3 类即 strong 拿满 25;
                          2 类 15, 1 类 8
  权威 authority      <=10: 资质认证 / 奖项 / 媒体提及 / 案例品牌, 命中 >=2 类 10 分, 1 类 5 分

评级: >=75 强 / 50-74 中等 / <50 弱.

退出码: >=50 -> 0; <50 -> 1; 抓取失败 -> 2.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; SEOSkill-TrustSignals/1.0)"

BLOCK_TAGS = {"p", "div", "br", "li", "tr", "section", "article", "header", "footer",
              "nav", "main", "aside", "table", "ul", "ol", "h1", "h2", "h3", "h4",
              "blockquote", "figure", "figcaption"}

RISK_PATTERNS = [
    ("free trial", re.compile(r"free trial|start(?:ing)? for free|\d+[- ]day free|免费试用|免费体验", re.I)),
    ("no credit card", re.compile(r"no credit card(?: required)?|without credit card|无需信用卡|不用信用卡|免信用卡", re.I)),
    ("cancel anytime", re.compile(r"cancel (?:anytime|at any time)|随时取消|随时退订|随时停用", re.I)),
    ("guarantee", re.compile(r"guarantee[ds]?|money[- ]back|退款保证|保证退款|无条件退款|\d+\s*天无理由|担保", re.I)),
]

SOCIAL_PATTERNS = [
    ("客户/用户数", re.compile(
        r"\d[\d,.\uFF0C]*\s*(?:万|亿|[kKmM]\+?|\+)?\s*"
        r"(?:customers|users|clients|companies|teams|brands|businesses|developers|stores|sites|人|家|名|企业|客户|用户|商户|开发者)", re.I)),
    ("trusted by/服务过", re.compile(r"trusted by|used by|服务(?:过|超过)|超过\s*\d|被.{0,12}(?:使用|信赖)", re.I)),
    ("结果类数字", re.compile(
        r"(?:increas|boost|grew|improv|reduc|sav|提升|增长|提高|降低|节省|节省)[^.\n]{0,50}?\d[\d.,]*\s*%?", re.I)),
    ("百分比成果", re.compile(r"\d[\d.,]*\s*%")),
]

AUTHORITY_PATTERNS = [
    ("资质/认证", re.compile(r"certified|certification|ISO\s?\d{4,}|SOC\s?2|GDPR|HIPAA|认证|资质|合规", re.I)),
    ("奖项", re.compile(r"award|winner|won (?:the )?best|top\s?\d+|获奖|奖项|冠军", re.I)),
    ("媒体/评测", re.compile(
        r"(?:as seen in|featured in|mentioned in|reviewed by)|\b(?:TechCrunch|Forbes|Wired|Gartner|CNET|PCMag|Bloomberg)\b|媒体报道|权威媒体|上榜", re.I)),
    ("案例/合作品牌", re.compile(r"case stud|customer stor|成功案例|客户案例|合作伙伴", re.I)),
]

ATTRIBUTION_RE = re.compile(
    r"—|──|——|–|\bby\b|\bCEO\b|\bCTO\b|\bCFO\b|co[- ]?founder|founder|director|"
    r"创始人|联合创始人|首席执行官|总裁|总监|经理|负责人|作者", re.I)
QUOTE_SPAN_RE = re.compile(r"“([^”]{40,})”|\"([^\"]{40,})\"")


class TrustParser(HTMLParser):
    """收集可见文本与 blockquote 文本."""

    SKIP = {"script", "style", "noscript", "template", "svg", "title"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text_parts = []
        self.blockquotes = []
        self._skip_depth = 0
        self._bq_depth = 0
        self._bq_parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "blockquote":
            self._bq_depth += 1
            if self._bq_depth == 1:
                self._bq_parts = []
        elif tag in BLOCK_TAGS:
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag == "blockquote":
            if self._bq_depth == 1:
                txt = re.sub(r"\s+", " ", "".join(self._bq_parts)).strip()
                if len(txt) >= 40:
                    self.blockquotes.append(txt)
            self._bq_depth = max(0, self._bq_depth - 1)

    def handle_data(self, data):
        if self._skip_depth:
            return
        self.text_parts.append(data)
        if self._bq_depth:
            self._bq_parts.append(data)


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


def score_testimonials(blockquotes, visible_text):
    """<=35: >=3 段长引文本体 25 分; 其中含数字且有署名再 +10."""
    quoted = [m.group(1) or m.group(2) or "" for m in QUOTE_SPAN_RE.finditer(visible_text)]
    candidates = [re.sub(r"\s+", " ", q).strip() for q in blockquotes + quoted]
    candidates = [c for c in candidates if len(c) >= 40]
    if len(candidates) < 3:
        return 0, "合格证言段(>=40 字符)仅 {0} 段, 不足 3 段 -> 0 分".format(len(candidates)), candidates
    score = 25
    has_digit = any(re.search(r"\d", c) for c in candidates)
    has_attr = any(ATTRIBUTION_RE.search(c) for c in candidates)
    detail = "{0} 段证言 -> 25 分".format(len(candidates))
    if has_digit and has_attr:
        score += 10
        detail += "; 含数字+署名 -> +10"
    else:
        detail += "; 数字:{0} 署名:{1} (两者齐备才 +10)".format(
            "有" if has_digit else "无", "有" if has_attr else "无")
    return score, detail, candidates


def score_social(visible_text):
    hits = [name for name, rx in SOCIAL_PATTERNS if rx.search(visible_text)]
    n = len(hits)
    score = {0: 0, 1: 10, 2: 20}.get(n, 30)
    return score, "命中 {0}/4 类: {1} -> {2} 分".format(
        n, ", ".join(hits) if hits else "无", score)


def score_risk(visible_text):
    hits = [name for name, rx in RISK_PATTERNS if rx.search(visible_text)]
    n = len(hits)
    if n >= 3:
        score, tag = 25, "strong(拿满)"
    elif n == 2:
        score, tag = 15, "中等"
    elif n == 1:
        score, tag = 8, "弱"
    else:
        score, tag = 0, "无"
    return score, "命中 {0}/4 类: {1} -> {2} 分 ({3})".format(
        n, ", ".join(hits) if hits else "无", score, tag), hits


def score_authority(visible_text):
    hits = [name for name, rx in AUTHORITY_PATTERNS if rx.search(visible_text)]
    n = len(hits)
    score = 10 if n >= 2 else (5 if n == 1 else 0)
    return score, "命中 {0}/4 类: {1} -> {2} 分".format(
        n, ", ".join(hits) if hits else "无", score)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="trust_signals.py",
        description="页面信任信号计分: 证言/社会证明/风险反转/权威 (stdlib only)")
    ap.add_argument("url", help="待检页面 URL")
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

    parser = TrustParser()
    try:
        parser.feed(decode(body)[:500000])
    except Exception as e:
        print("[WARN] HTML 解析异常(继续用已解析部分): {0}".format(e), file=sys.stderr)
    visible_text = re.sub(r"[ \t\r\f\v]+", " ", "".join(parser.text_parts))
    visible_text = re.sub(r"\n{2,}", "\n", visible_text)

    t_score, t_detail, candidates = score_testimonials(parser.blockquotes, visible_text)
    s_score, s_detail = score_social(visible_text)
    r_score, r_detail, risk_hits = score_risk(visible_text)
    a_score, a_detail = score_authority(visible_text)

    total = t_score + s_score + r_score + a_score
    grade = "强" if total >= 75 else ("中等" if total >= 50 else "弱")

    print("=" * 76)
    print("trust_signals | {0} (HTTP {1})".format(final, status))
    print("-" * 76)
    print("{0:<14} {1:>8}   详情".format("维度(上限)", "得分"))
    print("{0:<14} {1:>8}   {2}".format("证言(35)", t_score, t_detail))
    print("{0:<14} {1:>8}   {2}".format("社会证明(30)", s_score, s_detail))
    print("{0:<14} {1:>8}   {2}".format("风险反转(25)", r_score, r_detail))
    print("{0:<14} {1:>8}   {2}".format("权威(10)", a_score, a_detail))
    print("-" * 76)
    print("总分: {0} / 100 -> {1}".format(total, grade))

    tips = []
    if t_score < 25:
        tips.append("证言: 补足 >=3 段 40 字符以上的 blockquote/引号证言, 带数字与署名可拿满 35")
    if s_score < 30:
        tips.append("社会证明: 加客户/用户规模数字、结果百分比或 trusted by 说法")
    if r_score < 25:
        missing = [n for n, _rx in RISK_PATTERNS if n not in risk_hits]
        tips.append("风险反转: 4 类中拿 3 类即满 (free trial/no credit card/cancel anytime/guarantee); 缺: {0}".format(
            ", ".join(missing) if missing else "无"))
    if a_score < 10:
        tips.append("权威: 补资质认证/奖项/媒体提及/客户案例任两类")
    if tips:
        print("\n建议:")
        for t in tips:
            print("  - {0}".format(t))
    return 0 if total >= 50 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]", file=sys.stderr)
        sys.exit(130)
