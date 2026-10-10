#!/usr/bin/env python3
"""site_audit --json(或 audit_compare --json 的 diff)→ CI 消费格式(stdlib only)。
- sarif 2.1.0: 每条失败 finding(CRITICAL/WARN/INFO;SKIP 拒审不算)一个 result;
  ruleId={area}-{rule 简名}(消息前导稳定 ASCII 标识如 noindex/og:title/ChatGPT-User,
  纯中文/数字开头时退化为 area);level 三档 error(CRITICAL)/warning(WARN)/note(INFO);
  locations[].physicalLocation.artifactLocation.uri=被审计 URL;
  helpUri 仅在 HELP_URIS 有真实文档 URL 时条件添加(空串/占位会崩 Code Scanning);
  invocations[].properties 带 {ai_search_health, main_score}。
- junit: 每个 area 一个 testsuite;主 testcase"类目得分低于 50% 满分即 failure"
  (类目得分=(未命中该 area 的可评分 URL 数÷可评分 URL 数)×100,满分 100);
  顶层 properties 注入 audit.score/ai_search_health。
- github: ::error|warning|notice title=SEO:: 注解;每 URL 至多前 10 行,
  超出截断并提示(防刷屏)。
纯函数可测: to_sarif(audit_json)->dict / to_junit(audit_json)->str / to_github(audit_json)->str。
用法: python3 ci_format.py audit.json [--format sarif|junit|github|json]
退出码: 0(格式化本身不判成败;门禁用 action 的 min-score 或 audit_compare 的
--baseline-gate)。"""
import json
import re
import sys
from xml.sax.saxutils import escape

SEV_LEVEL = {"CRITICAL": "error", "WARN": "warning", "INFO": "note"}
GH_CMD = {"CRITICAL": "error", "WARN": "warning", "INFO": "notice"}
GH_PER_URL_LIMIT = 10                     # 每 URL 注解行上限(防刷屏)
JUNIT_AREA_FAIL_BELOW = 50                # 主 testcase 失败线:类目得分<50(满分 100)
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
TOOL_URI = "https://github.com/everyinfra/seo-skills"
# area→真实文档 URL 的登记表;没有文档就保持空——helpUri 空串/占位符会让
# Code Scanning 上传崩溃,故只在确有 URL 时条件添加(测试覆盖该条件分支)。
HELP_URIS = {}
_SUB_RULE_RE = re.compile(r"[A-Za-z][A-Za-z0-9:_.-]*")

USAGE = """usage: ci_format.py audit.json [--format sarif|junit|github|json]
site_audit.py --json(或 audit_compare.py --json 的 diff:new_issues 逐条转 findings)
→ CI 消费格式:
  sarif   每条失败 finding 一个 result;ruleId={area}-{rule 简名}(消息前导稳定
          ASCII 标识,无则退化 area);level error/warning/note;uri=被审计 URL;
          helpUri 仅在有真实文档 URL 时添加(空串会崩 Code Scanning);
          invocations[].properties 带 {ai_search_health, main_score}
  junit   每个 area 一个 testsuite;主 testcase"类目得分<50% 满分即 failure"
          (类目得分=未命中该 area 的可评分 URL 占比×100);顶层 properties 注入
          audit.score / ai_search_health
  github  ::error|warning|notice title=SEO:: 注解;每 URL 前十行截断防刷屏
  json    原样回显(默认;供 action 直接落盘)
退出码: 0(门禁请用 action min-score / audit_compare --baseline-gate)。"""


def _die(msg):
    sys.stderr.write(msg + "\n")
    sys.exit(2)


def load_payload(path):
    """读输入文件:容忍 site_audit --json 输出前部的逐 URL 文本行(从每个 '{' 起点
    试解,取含 results 字典或 new_issues 的候选);也容忍 audit_compare --json diff。
    解析不出即退出码 2。"""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        _die("读不了 %s: %s" % (path, e))
    cands = []
    try:
        cands.append(json.loads(text))
    except json.JSONDecodeError:
        pass
    for i, ch in enumerate(text):
        if ch == "{":
            try:
                cands.append(json.loads(text[i:]))
            except json.JSONDecodeError:
                continue
    for cand in cands:
        if isinstance(cand, dict) and (isinstance(cand.get("results"), dict)
                                       or "new_issues" in cand):
            return cand
    _die("无法从 %s 解析出含 results/new_issues 的 JSON(应为 site_audit.py --json "
         "或 audit_compare.py --json 的输出)" % path)


def normalize(payload):
    """audit_compare --json diff(含 new_issues)→ 合成 site_audit 形:new_issues
    逐条变 findings(rule→area);已是 site_audit 形(含 results)则原样返回。"""
    if isinstance(payload, dict) and "new_issues" in payload and "results" not in payload:
        results = {}
        for it in payload.get("new_issues", []):
            r = results.setdefault(it.get("url", "unknown"),
                                   {"verdict": "pass", "findings": [], "meta": {},
                                    "ai_search_health": None})
            r["findings"].append({"severity": it.get("severity", "INFO"),
                                  "area": it.get("rule", "unknown"),
                                  "message": it.get("message", "")})
            if it.get("severity") == "CRITICAL":
                r["verdict"] = "fail"
        return {"audited": len(results), "critical": 0, "results": results}
    return payload


def main_score(audit):
    """主分【Ahrefs 官方】:(无 CRITICAL 的 URL 数÷可评分 URL 数)×100;
    verdict=refused 不进分母;无可评分 URL → None。"""
    scored = [r for r in audit["results"].values() if r.get("verdict") != "refused"]
    if not scored:
        return None
    crit = sum(1 for r in scored if r.get("verdict") == "fail")
    return round((len(scored) - crit) / len(scored) * 100, 1)


def ai_health_mean(audit):
    """AI Search Health 均值(0-100);无数据 → None。"""
    vals = [r["ai_search_health"]["score"] for r in audit["results"].values()
            if isinstance(r.get("ai_search_health"), dict)
            and r["ai_search_health"].get("score") is not None]
    return round(sum(vals) / len(vals), 1) if vals else None


def _iter_findings(audit):
    """(url, finding) 迭代;SKIP(fetch guard 拒审)不是失败 finding,不进任何格式。"""
    for url, r in audit["results"].items():
        for f in r.get("findings", []):
            if f.get("severity") in SEV_LEVEL:
                yield url, f


def rule_id_of(area, message):
    """ruleId = {area}-{rule 简名}:消息前导的稳定 ASCII 标识(noindex/og:title/
    ChatGPT-User 等)作子规则简名;无稳定标识(纯中文/数字开头)时退化为 area。"""
    m = _SUB_RULE_RE.match(message or "")
    if not m:
        return str(area)
    slug = re.sub(r"[^A-Za-z0-9-]", "-", m.group(0)).strip("-")
    if not slug or slug.lower() == str(area).lower():
        return str(area)
    return "%s-%s" % (area, slug)


def to_sarif(audit):
    """audit(dict)→ SARIF 2.1.0 dict。纯函数。"""
    audit = normalize(audit)
    results, rules = [], {}
    for url, f in _iter_findings(audit):
        area = str(f.get("area", "unknown"))
        rid = rule_id_of(area, f.get("message", ""))
        results.append({
            "ruleId": rid,
            "level": SEV_LEVEL[f["severity"]],
            "message": {"text": "[%s] %s: %s" % (f["severity"], area, f.get("message", ""))},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": url}}}],
        })
        rule = rules.setdefault(rid, {"id": rid})
        doc = HELP_URIS.get(area)
        if doc and "helpUri" not in rule:      # 条件添加:仅真实文档 URL,空串会崩
            rule["helpUri"] = doc
    ms, ai = main_score(audit), ai_health_mean(audit)
    return {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "seo-suite-site-audit",
                                 "informationUri": TOOL_URI,
                                 "rules": [rules[k] for k in sorted(rules)]}},
            "invocations": [{"executionSuccessful": True,
                             "properties": {"main_score": ms, "ai_search_health": ai}}],
            "results": results,
        }],
    }


def _x(s):
    """XML 属性/文本转义(& < > 与引号)。"""
    return escape(str(s), {'"': "&quot;", "'": "&apos;"})


def to_junit(audit):
    """audit(dict)→ JUnit XML 字符串。每个 area 一个 testsuite,主 testcase
    "类目得分<50% 满分即 failure";顶层 properties 注入 audit.score/ai_search_health。"""
    audit = normalize(audit)
    total = sum(1 for r in audit["results"].values() if r.get("verdict") != "refused")
    by_area = {}
    for url, f in _iter_findings(audit):
        by_area.setdefault(str(f.get("area", "unknown")), set()).add(url)
    ms, ai = main_score(audit), ai_health_mean(audit)
    suites, ntests, nfail = [], 0, 0
    if total == 0:
        suites.append('  <testsuite name="seo-audit" tests="1" failures="1">\n'
                      '    <testcase name="no-scored-urls" classname="seo.audit">'
                      '<failure type="AuditRefused" message="%s"/></testcase>\n'
                      '  </testsuite>' % _x("无可评分 URL(全部拒审)"))
        ntests, nfail = 1, 1
    elif not by_area:
        suites.append('  <testsuite name="seo-audit" tests="1" failures="0">\n'
                      '    <testcase name="no-findings" classname="seo.audit"/>\n'
                      '  </testsuite>')
        ntests = 1
    else:
        for area in sorted(by_area):
            hit = len(by_area[area])
            score = round((total - hit) / total * 100, 1)
            fail = score < JUNIT_AREA_FAIL_BELOW
            msg = "%s 类目得分 %s %s %d(命中 %d/%d 可评分 URL)" % (
                area, score, "<" if fail else ">=", JUNIT_AREA_FAIL_BELOW, hit, total)
            if fail:
                tc = ('    <testcase name="%s-score" classname="seo.audit.%s">'
                      '<failure type="AreaScoreBelow50" message="%s"/></testcase>'
                      % (_x(area), _x(area), _x(msg)))
                nfail += 1
            else:
                tc = '    <testcase name="%s-score" classname="seo.audit.%s"/>' % (_x(area), _x(area))
            suites.append('  <testsuite name="%s" tests="1" failures="%d">\n%s\n  </testsuite>'
                          % (_x(area), 1 if fail else 0, tc))
            ntests += 1
    props = ('  <properties>\n'
             '    <property name="audit.score" value="%s"/>\n'
             '    <property name="ai_search_health" value="%s"/>\n'
             '  </properties>' % ("" if ms is None else ms, "" if ai is None else ai))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<testsuites name="seo-site-audit" tests="%d" failures="%d">\n%s\n%s\n</testsuites>\n'
            % (ntests, nfail, props, "\n".join(suites)))


def _gh_escape(s):
    """workflow command 消息转义:% → %25、CR → %0D、LF → %0A。"""
    return str(s).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def to_github(audit):
    """audit(dict)→ GitHub Actions 注解文本(逐行 ::error|warning|notice)。
    每 URL 至多前 10 行,超出截断并以 notice 提示,防止注解刷屏。"""
    audit = normalize(audit)
    ms, ai = main_score(audit), ai_health_mean(audit)
    out = ["::notice title=SEO::audited=%d main_score=%s ai_search_health=%s"
           % (len(audit["results"]), ms, ai)]
    for url, r in audit["results"].items():
        fs = [f for f in r.get("findings", []) if f.get("severity") in GH_CMD]
        for i, f in enumerate(fs):
            if i >= GH_PER_URL_LIMIT:
                out.append("::notice title=SEO::[truncated] %s: 其余 %d 条注解截断"
                           "(每 URL 限 %d 行防刷屏)" % (url, len(fs) - GH_PER_URL_LIMIT,
                                                        GH_PER_URL_LIMIT))
                break
            out.append("::%s title=SEO::[%s] %s (%s)"
                       % (GH_CMD[f["severity"]], f.get("area", "unknown"),
                          _gh_escape(f.get("message", "")), url))
    return "\n".join(out)


def main():
    argv = sys.argv[1:]
    if any(a in ("-h", "--help") for a in argv):
        print(USAGE)
        return
    fmt, inp = "json", None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a.startswith("-"):
            _die("未知参数 %r\n%s" % (a, USAGE))
        elif inp is None:
            inp = a; i += 1
        else:
            _die("多余参数 %r\n%s" % (a, USAGE))
    if not inp:
        _die("缺少输入文件\n" + USAGE)
    if fmt not in ("json", "sarif", "junit", "github"):
        _die("未知 --format %r(可用: json|sarif|junit|github)" % fmt)
    payload = load_payload(inp)
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    elif fmt == "sarif":
        print(json.dumps(to_sarif(payload), ensure_ascii=False, indent=1))
    elif fmt == "junit":
        print(to_junit(payload))
    else:
        print(to_github(payload))
    sys.exit(0)


if __name__ == "__main__":
    main()
