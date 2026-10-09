#!/usr/bin/env python3
"""自包含 HTML 报告生成器(stdlib)。输入 findings.json:
    {"title": 结论句, "summary": <2500 字符,
     "findings": [{"area","problem","change","expected","evidence","severity"}]}

硬约束(生成器负责执行):
  * 禁外部资源、禁 <script>;图 = 内联 SVG 横条,数字同时印在文字里;
  * 标题 = 结论句(答案式),直接渲染为 <h1>/<title>;
  * summary <2500 字符,超出截断并警告;
  * findings >20 条 → 警告"失败报告"并截断到 20;
  * 收尾固定节 "How this report was made";目标 <80KB,超出警告。

用法: python3 report_build.py --findings findings.json --out report.html
退出码:0=生成(含警告);2=输入错误。"""
import argparse
import html
import json
import sys
from collections import Counter
from datetime import datetime, timezone

MAX_SUMMARY = 2500
MAX_FINDINGS = 20
SIZE_TARGET = 80 * 1024
SEV_ORDER = ["high", "medium", "low"]
SEV_COLOR = {"high": "#b3261e", "medium": "#b26a00", "low": "#1a73e8"}


def die(msg):
    print(f"[error] {msg}", file=sys.stderr)
    sys.exit(2)


def esc(s):
    return html.escape(str(s), quote=True)


def load_findings(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        die(f"无法读取 {path}: {e}")
    except json.JSONDecodeError as e:
        die(f"{path} 不是合法 JSON: {e}")
    if not isinstance(data, dict):
        die("顶层必须是对象 {title, summary, findings}")
    problems = []
    title, summary, findings = data.get("title"), data.get("summary"), data.get("findings")
    if not isinstance(title, str) or not title.strip():
        problems.append("title: 必须是非空结论句(答案式)")
    if not isinstance(summary, str) or not summary.strip():
        problems.append("summary: 必须是非空字符串")
    if not isinstance(findings, list) or not findings:
        problems.append("findings: 必须是非空数组")
    req = ["area", "problem", "change", "expected", "evidence", "severity"]
    if isinstance(findings, list):
        for i, fd in enumerate(findings):
            if not isinstance(fd, dict):
                problems.append(f"findings[{i}] 必须是对象")
                continue
            for k in req:
                if k not in fd or not str(fd[k]).strip():
                    problems.append(f"findings[{i}].{k} 缺失或为空")
    if problems:
        die("findings.json 校验失败:\n  - " + "\n  - ".join(problems))
    return title.strip(), summary.strip(), findings


def bar_chart_svg(rows, caption):
    """rows: [(label, value, color)];数字同时以文字返回,由调用方印出。"""
    if not rows:
        return "<p>(无数据)</p>", f"{caption}:无数据"
    width, label_w, bar_h, gap = 640, 170, 22, 8
    chart_w = width - label_w - 70
    total_h = gap + len(rows) * (bar_h + gap)
    maxv = max(v for _, v, _ in rows) or 1
    parts = [f'<svg class="chart" viewBox="0 0 {width} {total_h}" width="{width}" '
             f'height="{total_h}" role="img" aria-label="{esc(caption)}">']
    for i, (label, value, color) in enumerate(rows):
        y = gap + i * (bar_h + gap)
        w = max(2, round(chart_w * value / maxv))
        parts.append(f'<text x="{label_w - 8}" y="{y + bar_h - 6}" text-anchor="end" '
                     f'font-size="13" fill="#202124">{esc(label)}</text>')
        parts.append(f'<rect x="{label_w}" y="{y}" width="{w}" height="{bar_h}" '
                     f'fill="{color}" rx="3"></rect>')
        parts.append(f'<text x="{label_w + w + 8}" y="{y + bar_h - 6}" '
                     f'font-size="13" fill="#202124">{value}</text>')
    parts.append("</svg>")
    text_line = f"{caption}:" + ", ".join(f"{esc(l)}={v}" for l, v, _ in rows)
    return "".join(parts), text_line


def main():
    ap = argparse.ArgumentParser(description="自包含 HTML 报告生成器(findings.json → report.html)")
    ap.add_argument("--findings", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    title, summary, findings = load_findings(a.findings)

    if len(summary) >= MAX_SUMMARY:
        print(f"[warn] summary {len(summary)} 字符 ≥ {MAX_SUMMARY},截断(硬约束 summary <{MAX_SUMMARY})")
        summary = summary[: MAX_SUMMARY - 1] + "…"
    if len(findings) > MAX_FINDINGS:
        print(f"[warn] {len(findings)} 条 findings > {MAX_FINDINGS} —— 这是一份\"失败报告\":")
        print("       问题太多说明一次改动面过大/病灶未定位,先收敛再交付;已截断为前 "
              f"{MAX_FINDINGS} 条。")
        findings = findings[:MAX_FINDINGS]

    sev_of = lambda f: str(f.get("severity", "")).lower()
    sev_counts = Counter(sev_of(f) for f in findings)
    area_counts = Counter(str(f.get("area", "")).strip() or "(未分类)" for f in findings)
    known_sev = [s for s in SEV_ORDER if sev_counts.get(s)]
    unknown_sev = sorted(k for k in sev_counts if k not in SEV_ORDER)

    svg_sev, txt_sev = bar_chart_svg(
        [(f"severity: {s}", sev_counts[s], SEV_COLOR[s]) for s in known_sev], "按严重度")
    svg_area, txt_area = bar_chart_svg(
        [(k, v, "#5f6368") for k, v in sorted(area_counts.items(), key=lambda kv: -kv[1])],
        "按领域")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    H = []
    H.append("<!doctype html><html lang=\"zh\"><head><meta charset=\"utf-8\">")
    H.append(f"<title>{esc(title)}</title>")
    H.append("<style>body{font:15px/1.65 -apple-system,'Segoe UI',Roboto,sans-serif;"
             "color:#202124;max-width:760px;margin:2rem auto;padding:0 1rem}"
             "h1{font-size:1.55rem;line-height:1.35}h2{border-bottom:1px solid #dadce0;"
             "padding-bottom:.3rem;margin-top:2rem}.finding{border:1px solid #dadce0;"
             "border-left-width:5px;border-radius:6px;padding:.8rem 1rem;margin:1.2rem 0}"
             ".badge{display:inline-block;font-size:.75rem;font-weight:700;padding:.1rem .5rem;"
             "border-radius:99px;color:#fff}.muted{color:#5f6368;font-size:.85rem}"
             ".chart{max-width:100%;height:auto}code,.ev{font-size:.85rem}</style></head><body>")
    H.append(f"<h1>{esc(title)}</h1>")
    H.append(f"<p>{esc(summary)}</p>")
    H.append("<h2>数字总览</h2>")
    H.append(f"<p>共 {len(findings)} 条 finding。文字版(与图中数字一致):{esc(txt_sev)};{esc(txt_area)}。</p>")
    if unknown_sev:
        H.append(f"<p class='muted'>未识别 severity 值(按原样计数):{esc(', '.join(unknown_sev))}</p>")
    H.append(svg_sev)
    H.append(svg_area)
    H.append("<h2>Findings(Problem → Change → Expected effect)</h2>")
    for i, f in enumerate(findings, 1):
        s = sev_of(f)
        color = SEV_COLOR.get(s, "#5f6368")
        H.append(f"<div class='finding' style='border-left-color:{color}'>")
        H.append(f"<p><strong>#{i} {esc(f['area'])}</strong> "
                 f"<span class='badge' style='background:{color}'>{esc(f['severity'])}</span></p>")
        H.append(f"<p><strong>Problem</strong> — {esc(f['problem'])}</p>")
        H.append(f"<p><strong>Change</strong> — {esc(f['change'])}</p>")
        H.append(f"<p><strong>Expected effect</strong> — {esc(f['expected'])}</p>")
        ev = str(f["evidence"]).strip()
        H.append(f"<p class='ev muted'>Evidence: <code>{esc(ev)}</code></p></div>")
    H.append("<h2>How this report was made</h2>")
    H.append(f"<p>本报告由 <code>report_build.py</code>(Python 标准库,无第三方依赖)于 {esc(now)} "
             f"从 <code>{esc(a.findings)}</code> 生成:输入格式为 "
             "<code>{title, summary, findings:[{area,problem,change,expected,evidence,severity}]}</code>。"
             "报告为单文件自包含 HTML:不引用任何外部资源(无外链 CSS/图片/字体),"
             "不含任何 <code>&lt;script&gt;</code>;图表为内联 SVG 横条,其数字同时在"
             "\"数字总览\"一节以纯文字重复给出;每条 finding 固定为 Problem / Change / "
             "Expected effect 三段。生成器硬约束:summary &lt; 2500 字符;"
             "findings &gt; 20 条即判为\"失败报告\"并截断;文件目标 &lt; 80KB。</p>")
    H.append("</body></html>")
    doc = "\n".join(H)

    forbidden = []
    if "<script" in doc.lower():
        forbidden.append("<script>")
    if "src=\"http" in doc.lower() or "href=\"http" in doc.lower():
        forbidden.append("外部 src/href")
    if forbidden:
        die(f"自检失败,出现被禁元素: {forbidden}")

    with open(a.out, "w", encoding="utf-8") as f:
        f.write(doc)
    size = len(doc.encode("utf-8"))
    print(f"[ok] 写出 {a.out}({size} 字节,{len(findings)} 条 findings,severity 分布: {txt_sev})")
    if size > SIZE_TARGET:
        print(f"[warn] {size} 字节超出 {SIZE_TARGET} 自包含目标 —— 削减 evidence 长度或拆分报告。")
    sys.exit(0)


if __name__ == "__main__":
    main()
