#!/usr/bin/env python3
"""envelope.py 回归(stdlib unittest,合成数据,零网络,standalone——
助手照抄 run_tests.py 顶部,不 import run_tests,被其 test_*.py 自动发现加载)。
口径钉死 references/research/borrow-specs.md E4(claude-seo envelope+落盘契约):
统一 audit-data.json(summary/categories/action_plan.phases 三段结构)/三源映射
(site_audit=发现源,health_score=主分分档,prioritize=impact 与修复文案)/
health·priority 缺失降级 source_missing 不失败/每类别即落盘 findings/*.md(人读表+
文末 envelope-category-v1 机器回读行)/全部分派完才写 audit-data.json 与 REPORT.md/
--resume 跳过已有 category(自落盘回读,过期文件不混入)/--json 只打 stdout 不落盘/
phases 分派(CRITICAL→立即;WARN 且 impact≥1.0→短期;其余→持续)。"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)


def run_script(name, args=(), stdin=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, name), *args],
                          input=stdin, capture_output=True, text=True,
                          encoding="utf-8", env=env)


def tmp_file(content):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


def make_audit(by_url, metas=None, ai=None):
    """合成 site_audit --json 输出:by_url={url:[(sev,area,msg)]},metas={url:{...}},
    ai={url:ai_search_health.score}(缺省的 URL 不带该节,模拟拒审页)。"""
    results = {}
    for url, findings in by_url.items():
        rec = {
            "verdict": "fail" if any(s == "CRITICAL" for s, _, _ in findings)
                       else ("refused" if any(s == "SKIP" for s, _, _ in findings) else "pass"),
            "findings": [{"severity": s, "area": a, "message": m} for s, a, m in findings],
            "meta": (metas or {}).get(url, {})}
        if ai and url in ai:
            rec["ai_search_health"] = {"score": ai[url], "bots": {"allowed": [], "blocked": []},
                                       "last_modified_days": None, "semantic_ratio": 0.2,
                                       "checks": []}
        results[url] = rec
    return json.dumps({"audited": len(results), "critical": 0, "results": results},
                      ensure_ascii=False)


def make_health(main_score=80.0, band="Good", urls_total=3):
    """合成 health_score.py --json 摘要(envelope 只读 main_score/band,其余照实形状)。"""
    return json.dumps({"schema_version": "1.0", "main_score": main_score, "band": band,
                       "composite_score": 78.0, "warn_score": 50.0, "info_score": 100.0,
                       "category_scores": {}, "impacts": [], "ignored": [], "unmapped": [],
                       "coverage_note": "基于样本", "urls_total": urls_total,
                       "urls_clean": urls_total, "urls_refused": 0}, ensure_ascii=False)


def prio_item(rule, sev="WARN", hits=1, total=4, impact=0.5, fix="修复文案"):
    """合成 prioritize.py --json 的一条 fix_now 项。"""
    return {"rule": rule, "category": "imported", "severity": sev, "hit_urls": hits,
            "total_urls": total, "impact": impact, "amplifier": None, "conditional": None,
            "fix_instruction": fix, "url_query": []}


def make_priority(items):
    return json.dumps({"schema_version": "1.0", "input_format": "site_audit", "segment": None,
                       "urls_total": 4, "urls_matched_segment": 4, "urls_refused": 0,
                       "context": {"gsc": False, "pagerank_compare": False,
                                   "field_coverage": {}},
                       "fix_now": items, "explore": [], "no_hit_rules": [],
                       "degraded_rules": [], "degradation_notes": [],
                       "coverage_note": "基于样本"}, ensure_ascii=False)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def phase_items(env, name):
    ph = next(p for p in env["action_plan"]["phases"] if p["name"] == name)
    return ph["items"]


def cat_findings(env, name):
    return next(c for c in env["categories"] if c["name"] == name)["findings"]


def flat_items(env):
    return [i for p in env["action_plan"]["phases"] for i in p["items"]]


class EnvelopeCase(unittest.TestCase):
    """公共助手:每用例独立 out-dir,输入临时文件自动清理。"""

    def setUp(self):
        self.out = tempfile.mkdtemp(prefix="envelope-test-")
        self.addCleanup(shutil.rmtree, self.out, ignore_errors=True)

    def write_input(self, text):
        p = tmp_file(text)
        self.addCleanup(os.unlink, p)
        return p

    def run_envelope(self, audit_json, health_json=None, priority_json=None,
                     resume=False, as_json=False):
        paths = {"audit": self.write_input(audit_json)}
        if health_json is not None:
            paths["health"] = self.write_input(health_json)
        if priority_json is not None:
            paths["priority"] = self.write_input(priority_json)
        args = []
        for k in ("audit", "health", "priority"):
            if paths.get(k):
                args += ["--" + k, paths[k]]
        extra = (["--resume"] if resume else []) + (["--json"] if as_json else [])
        return run_script("envelope.py", args + ["--out-dir", self.out] + extra)

    def load_env(self):
        with open(os.path.join(self.out, "audit-data.json"), encoding="utf-8") as f:
            return json.load(f)


class EnvelopeCLITests(EnvelopeCase):
    """--help / 退出码 2 家族(缺参/坏 JSON/格式不符不静默降级)"""

    def test_help_works(self):
        r = run_script("envelope.py", ["--help"])
        self.assertEqual(r.returncode, 0)
        self.assertIn("usage: envelope.py", r.stdout)
        self.assertIn("--resume", r.stdout)
        self.assertIn("source_missing", r.stdout)

    def test_missing_audit_exits_2(self):
        r = run_script("envelope.py", ["--out-dir", self.out])
        self.assertEqual(r.returncode, 2)
        self.assertIn("缺少 --audit", r.stderr)

    def test_bad_audit_json_exits_2(self):
        r = self.run_envelope("根本不是 JSON")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--audit", r.stderr)

    def test_wrong_shape_health_exits_2(self):
        # 显式提供但格式不符 → 响亮失败(把 audit 文件误传成 health)
        audit = make_audit({"https://s.com/a": []})
        r = self.run_envelope(audit, health_json=audit)
        self.assertEqual(r.returncode, 2)
        self.assertIn("--health", r.stderr)

    def test_wrong_shape_priority_exits_2(self):
        r = self.run_envelope(make_audit({"https://s.com/a": []}),
                              priority_json=make_health())
        self.assertEqual(r.returncode, 2)
        self.assertIn("--priority", r.stderr)


class EnvelopeStructureTests(EnvelopeCase):
    """envelope 三段结构 / 三源映射(audit=发现,health=主分,priority=impact 文案)"""

    def test_envelope_structure_and_three_source_mapping(self):
        audit = make_audit(
            {"https://s.com/a": [("CRITICAL", "robots", "noindex"),
                                 ("WARN", "og", "og:title 缺失")],
             "https://s.com/b": [("WARN", "og", "og:title 缺失")],
             "https://s.com/c": [],
             "https://s.com/guard": [("SKIP", "fetch guard", "refusing to audit")]},
            ai={"https://s.com/a": 40, "https://s.com/b": 90, "https://s.com/c": 65})
        # priority:og 走恒等映射(health_score 摘要输入路径下 area 原样透传)
        prio = make_priority([prio_item("og", hits=2, total=3, impact=1.5,
                                        fix="补 og 三件套(自定义)")])
        r = self.run_envelope(audit, make_health(main_score=66.7, band="Fair"), prio)
        self.assertEqual(r.returncode, 0, r.stderr)
        env = self.load_env()
        # 顶层结构与降级标记节
        self.assertEqual(set(env), {"schema_version", "generated_at", "source_urls",
                                    "inputs", "summary", "categories", "action_plan"})
        self.assertEqual(env["schema_version"], 1)
        self.assertIn("T", env["generated_at"])
        self.assertEqual(env["inputs"], {"audit": "ok", "health": "ok", "priority": "ok"})
        # audit 源:source_urls 含拒审 URL;类别=Lumar 顺序;发现聚合
        self.assertEqual(env["source_urls"], ["https://s.com/a", "https://s.com/b",
                                              "https://s.com/c", "https://s.com/guard"])
        self.assertEqual([c["name"] for c in env["categories"]],
                         ["indexability", "rankability"])
        robots = cat_findings(env, "indexability")[0]
        og = cat_findings(env, "rankability")[0]
        self.assertEqual(set(robots), {"rule_id", "title", "severity", "description",
                                       "recommendation", "affected_urls", "affected"})
        self.assertEqual((robots["rule_id"], robots["severity"], robots["affected"]),
                         ("robots", "CRITICAL", 1))
        self.assertEqual((og["rule_id"], og["severity"], og["affected"]), ("og", "WARN", 2))
        self.assertIn("2/3", og["description"])          # 分母=可评分 URL(拒审不进)
        self.assertEqual(og["affected_urls"], ["https://s.com/a", "https://s.com/b"])
        self.assertIn("最常见表现: og:title 缺失", og["description"])
        # priority 源:og 命中规则供给 impact 与修复文案
        self.assertEqual(og["recommendation"], "补 og 三件套(自定义)")
        # health 源:主分/分档;audit 源:AI Search Health 均值 (40+90+65)/3
        s = env["summary"]
        self.assertEqual((s["main_score"], s["band"]), (66.7, "Fair"))
        self.assertEqual(s["ai_search_health"], 65.0)
        # top_findings 前三:severity×受影响面排序
        self.assertEqual([f["rule_id"] for f in s["top_findings"]], ["robots", "og"])
        # phases 三段名恒定;robots CRITICAL→立即;og WARN+priority impact 1.5→短期
        self.assertEqual([p["name"] for p in env["action_plan"]["phases"]],
                         ["立即(本周)", "短期(月内)", "持续"])
        self.assertEqual([i["rule_id"] for i in phase_items(env, "立即(本周)")], ["robots"])
        self.assertEqual([i["rule_id"] for i in phase_items(env, "短期(月内)")], ["og"])
        self.assertEqual(phase_items(env, "持续"), [])

    def test_unmapped_area_goes_to_other_category(self):
        audit = make_audit({"https://s.com/a": [("CRITICAL", "future-rule", "x")]})
        r = self.run_envelope(audit)
        self.assertEqual(r.returncode, 0, r.stderr)
        env = self.load_env()
        self.assertEqual([c["name"] for c in env["categories"]], ["other"])
        f = cat_findings(env, "other")[0]
        self.assertEqual(f["rule_id"], "future-rule")       # 未映射 area 不崩,归 other
        self.assertIn("site_audit", f["recommendation"])    # 兜底文案指向 audit 报告
        self.assertTrue(os.path.isfile(os.path.join(self.out, "findings", "other.md")))

    def test_affected_urls_capped_at_20(self):
        by_url = {f"https://s.com/p{i}": [("WARN", "og", "og:title 缺失")]
                  for i in range(25)}
        r = self.run_envelope(make_audit(by_url))
        self.assertEqual(r.returncode, 0, r.stderr)
        f = cat_findings(self.load_env(), "rankability")[0]
        self.assertEqual(f["affected"], 25)                  # 计数不封顶
        self.assertEqual(len(f["affected_urls"]), 20)        # 清单封顶 20
        body = read(os.path.join(self.out, "findings", "rankability.md"))
        self.assertIn("| og | WARN | 25/25 |", body)         # 人读表显示真实计数

    def test_empty_findings_envelope(self):
        r = self.run_envelope(make_audit({"https://s.com/a": []}), make_health())
        self.assertEqual(r.returncode, 0, r.stderr)
        env = self.load_env()
        self.assertEqual(env["categories"], [])
        self.assertEqual(env["summary"]["top_findings"], [])
        self.assertEqual(env["summary"]["quick_wins"], [])
        for p in env["action_plan"]["phases"]:
            self.assertEqual(p["items"], [])
        # 无类别时 findings/ 目录为空,但 envelope 与 REPORT 恒产出
        self.assertEqual(os.listdir(os.path.join(self.out, "findings")), [])
        self.assertTrue(os.path.isfile(os.path.join(self.out, "REPORT.md")))


class EnvelopeDegradationTests(EnvelopeCase):
    """health/priority 缺失 → source_missing 降级,envelope 不失败"""

    def test_missing_health_and_priority_degrades_but_succeeds(self):
        r = self.run_envelope(make_audit({"https://s.com/a": [("WARN", "title", "18 chars <20")]}))
        self.assertEqual(r.returncode, 0, r.stderr)
        env = self.load_env()
        self.assertEqual(env["inputs"], {"audit": "ok", "health": "source_missing",
                                         "priority": "source_missing"})
        self.assertEqual(env["summary"]["main_score"], "source_missing")
        self.assertEqual(env["summary"]["band"], "source_missing")
        self.assertEqual(env["summary"]["ai_search_health"], "source_missing")  # audit 无该节
        # impact 降级为估算:1/1 URL WARN → 1.0×2 = 2.0;文案走本地 RECO 兜底
        item = flat_items(env)[0]
        self.assertEqual((item["rule_id"], item["impact"], item["impact_source"]),
                         ("title", 2.0, "estimated"))
        self.assertIn("50-60", item["action"])

    def test_priority_present_but_rule_uncovered_stays_estimated(self):
        # priority 在场但只覆盖 og:headings 无命中规则 → 估算,og → priority 口径
        by_url = {"https://s.com/a": [("WARN", "og", "og:title 缺失"),
                                      ("WARN", "headings", "跳级 h1→h3")],
                  "https://s.com/b": [("WARN", "og", "og:title 缺失")]}
        prio = make_priority([prio_item("og", hits=2, total=2, impact=2.0, fix="补 og")])
        r = self.run_envelope(make_audit(by_url), priority_json=prio)
        env = self.load_env()
        items = {i["rule_id"]: i for i in flat_items(env)}
        self.assertEqual((items["og"]["impact"], items["og"]["impact_source"]), (2.0, "priority"))
        self.assertEqual(items["headings"]["impact_source"], "estimated")
        # prioritize 特有规则(url_long 无对应 audit 检查)不进 envelope
        self.assertNotIn("url_long", items)


class EnvelopePhasesTests(EnvelopeCase):
    """phases 分派:CRITICAL→立即;WARN+impact≥1.0→短期;其余→持续"""

    def test_phase_dispatch_estimated_impact(self):
        by_url = {
            "https://s.com/a": [("CRITICAL", "robots", "noindex"),
                                ("WARN", "og", "og:title 缺失"),
                                ("WARN", "headings", "跳级 h1→h3")],
            "https://s.com/b": [("WARN", "og", "og:title 缺失")],
            "https://s.com/c": [("INFO", "sitemap", "/sitemap.xml 不可达")],
            "https://s.com/d": []}
        r = self.run_envelope(make_audit(by_url))
        self.assertEqual(r.returncode, 0, r.stderr)
        env = self.load_env()
        got = {p["name"]: [i["rule_id"] for i in p["items"]]
               for p in env["action_plan"]["phases"]}
        self.assertEqual(got["立即(本周)"], ["robots"])            # CRITICAL → 立即
        self.assertEqual(got["短期(月内)"], ["og"])                # WARN 2/4×2=1.0 恰达阈 → 短期
        self.assertEqual(sorted(got["持续"]), ["headings", "sitemap"])  # 0.5/0.25 → 持续
        self.assertTrue(all(i["impact_source"] == "estimated" for i in flat_items(env)))

    def test_phase_dispatch_priority_impact_override(self):
        by_url = {
            "https://s.com/a": [("CRITICAL", "robots", "noindex"),
                                ("WARN", "og", "og:title 缺失"),
                                ("WARN", "headings", "跳级 h1→h3")],
            "https://s.com/b": [("WARN", "og", "og:title 缺失")],
            "https://s.com/c": [("INFO", "sitemap", "/sitemap.xml 不可达")],
            "https://s.com/d": []}
        # priority 桥接规则:noindex_intent→robots,title_short/desc_short 同理;
        # headings 走恒等映射(health_score 摘要路径下原样透传)
        prio = make_priority([
            prio_item("noindex_intent", sev="WARN", hits=1, total=4, impact=0.2,
                      fix="按意图判定 noindex(条件依赖型)"),
            prio_item("og", hits=2, total=4, impact=0.4, fix="补 og"),
            prio_item("headings", hits=1, total=4, impact=2.5, fix="先修标题层级(自定义)")])
        r = self.run_envelope(make_audit(by_url), priority_json=prio)
        self.assertEqual(r.returncode, 0, r.stderr)
        env = self.load_env()
        got = {p["name"]: {i["rule_id"]: i for i in p["items"]}
               for p in env["action_plan"]["phases"]}
        # robots:priority impact 0.2<1.0,但 audit 实测 CRITICAL → 仍立即(严重度不降级)
        self.assertIn("robots", got["立即(本周)"])
        self.assertEqual(got["立即(本周)"]["robots"]["impact"], 0.2)
        self.assertEqual(got["立即(本周)"]["robots"]["action"], "按意图判定 noindex(条件依赖型)")
        # og:priority impact 0.4 压过估算 1.0 → 降为持续
        self.assertIn("og", got["持续"])
        self.assertEqual(got["持续"]["og"]["impact_source"], "priority")
        # headings:priority impact 2.5 拉进短期,且采用其修复文案
        self.assertIn("headings", got["短期(月内)"])
        self.assertEqual(got["短期(月内)"]["headings"]["action"], "先修标题层级(自定义)")
        # sitemap:priority 未覆盖 → 估算 0.25 → 持续
        self.assertEqual(got["持续"]["sitemap"]["impact_source"], "estimated")


class EnvelopeQuickWinTests(EnvelopeCase):
    """quick_wins:高 impact(≥1.0)且易修(文案/模板级),至多 3 条"""

    def test_quick_wins_exclude_hard_fixes(self):
        by_url = {
            "https://s.com/a": [("WARN", "og", "og:title 缺失"),
                                ("WARN", "rendering", "CSR 疑似")],
            "https://s.com/b": [("WARN", "og", "og:title 缺失"),
                                ("WARN", "rendering", "CSR 疑似")]}
        r = self.run_envelope(make_audit(by_url))
        env = self.load_env()
        qw = env["summary"]["quick_wins"]
        # og 与 rendering 估算 impact 同为 2.0(2/2×WARN2),但 rendering 非易修 → 不进
        self.assertEqual([q["rule_id"] for q in qw], ["og"])
        self.assertEqual((qw[0]["impact"], qw[0]["impact_source"]), (2.0, "estimated"))

    def test_quick_wins_use_priority_impact(self):
        by_url = {"https://s.com/a": [("WARN", "og", "og:title 缺失")],
                  "https://s.com/b": [("WARN", "og", "og:title 缺失")]}
        prio = make_priority([prio_item("og", hits=2, total=2, impact=3.0, fix="补 og")])
        r = self.run_envelope(make_audit(by_url), priority_json=prio)
        qw = self.load_env()["summary"]["quick_wins"]
        self.assertEqual(qw[0]["impact"], 3.0)
        self.assertEqual(qw[0]["impact_source"], "priority")

    def test_quick_wins_empty_below_threshold(self):
        # 1/3 URL WARN → 估算 1/3×2≈0.67 < 1.0:诚实留空,不硬凑
        by_url = {"https://s.com/a": [("WARN", "og", "og:title 缺失")],
                  "https://s.com/b": [], "https://s.com/c": []}
        r = self.run_envelope(make_audit(by_url))
        self.assertEqual(self.load_env()["summary"]["quick_wins"], [])


class EnvelopePersistTests(EnvelopeCase):
    """部分落盘契约:逐类别 findings/*.md,最后 audit-data.json + REPORT.md"""

    AUDIT = make_audit({
        "https://s.com/a": [("CRITICAL", "robots", "noindex"),
                            ("WARN", "og", "og:title 缺失")],
        "https://s.com/b": [("WARN", "og", "og:title 缺失")]})

    def test_partial_persist_writes_category_files_content(self):
        r = self.run_envelope(self.AUDIT)
        self.assertEqual(r.returncode, 0, r.stderr)
        idx = os.path.join(self.out, "findings", "indexability.md")
        rank = os.path.join(self.out, "findings", "rankability.md")
        self.assertTrue(os.path.isfile(idx))
        self.assertTrue(os.path.isfile(rank))
        body = read(idx)
        self.assertIn("# findings: indexability", body)     # 人读表
        self.assertIn("| robots | CRITICAL | 1/2 |", body)
        self.assertIn("- recommendation:", body)
        self.assertIn("envelope-category-v1", body)         # 机器回读标记行
        rank_body = read(rank)
        self.assertIn("| og | WARN | 2/2 |", rank_body)
        # 全部分派完才有 envelope 与 REPORT;stdout 摘要列出落盘清单
        self.assertTrue(os.path.isfile(os.path.join(self.out, "audit-data.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.out, "REPORT.md")))
        self.assertIn("audit-data.json", r.stdout)
        self.assertIn("findings/indexability.md", r.stdout)

    def test_resume_reads_back_from_disk_and_skips_rebuild(self):
        r1 = self.run_envelope(self.AUDIT)
        self.assertEqual(r1.returncode, 0, r1.stderr)
        rank = os.path.join(self.out, "findings", "rankability.md")
        # 模拟"中断后已有部分落盘":篡改落盘 payload 的 title + 追加标记行;
        # --resume 若真跳过重建,篡改应原样进 envelope 且文件不被重写
        body = read(rank)
        self.assertIn('"title":"og 标签缺失"', body)
        with open(rank, "w", encoding="utf-8") as f:
            f.write(body.replace('"title":"og 标签缺失"', '"title":"TAMPERED"')
                    + "\nMANUAL-EDIT\n")
        r2 = self.run_envelope(self.AUDIT, resume=True)
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIn("跳过 2 个已有 category", r2.stdout)
        env2 = self.load_env()
        og = cat_findings(env2, "rankability")[0]
        self.assertEqual(og["title"], "TAMPERED")           # 明细自落盘回读,而非重算
        with open(rank, encoding="utf-8") as f:
            self.assertIn("MANUAL-EDIT", f.read())          # 文件未被重写
        # 不带 --resume 重跑 → 完成时覆盖,篡改清除
        r3 = self.run_envelope(self.AUDIT)
        env3 = self.load_env()
        self.assertEqual(cat_findings(env3, "rankability")[0]["title"], "og 标签缺失")
        with open(rank, encoding="utf-8") as f:
            self.assertNotIn("MANUAL-EDIT", f.read())

    def test_resume_rebuilds_missing_and_ignores_stale(self):
        r1 = self.run_envelope(self.AUDIT)
        self.assertEqual(r1.returncode, 0, r1.stderr)
        # 场景 1:部分落盘后中断(删一个类别文件),--resume 只补缺失的
        os.unlink(os.path.join(self.out, "findings", "indexability.md"))
        r2 = self.run_envelope(self.AUDIT, resume=True)
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIn("跳过 1 个已有 category", r2.stdout)
        env2 = self.load_env()
        self.assertEqual([c["name"] for c in env2["categories"]],
                         ["indexability", "rankability"])   # 缺的重建,在的回读
        # 场景 2:换 audit(不再有 indexability 发现)——旧 run 遗留文件不混入 envelope
        audit2 = make_audit({"https://s.com/b": [("WARN", "og", "og:title 缺失")]})
        r3 = self.run_envelope(audit2, resume=True)
        env3 = self.load_env()
        self.assertEqual([c["name"] for c in env3["categories"]], ["rankability"])
        # --resume 信任落盘:rankability 明细来自旧 run 的盘上数据(og 受影响=a,b);
        # 若误重算只会是 audit2 的 [b]——此处钉死"盘上数据赢"
        self.assertEqual(cat_findings(env3, "rankability")[0]["affected_urls"],
                         ["https://s.com/a", "https://s.com/b"])
        # 过期文件留在盘上(不删用户数据)但不进 envelope
        self.assertTrue(os.path.isfile(os.path.join(self.out, "findings",
                                                    "indexability.md")))

    def test_report_md_summary(self):
        r = self.run_envelope(self.AUDIT, make_health(main_score=50.0, band="Fair"))
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.out, "REPORT.md"), encoding="utf-8") as f:
            rep = f.read()
        self.assertIn("50.0(Fair)", rep)
        self.assertIn("Top findings", rep)
        self.assertIn("noindex/robots 屏蔽", rep)
        self.assertIn("### 立即(本周)", rep)
        self.assertIn("### 短期(月内)", rep)
        self.assertIn("### 持续", rep)
        self.assertIn("findings/<category>.md", rep)
        self.assertIn("indexability", rep)

    def test_report_marks_source_missing_without_health(self):
        r = self.run_envelope(make_audit({"https://s.com/a": [("WARN", "og", "og:title 缺失")]}))
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.out, "REPORT.md"), encoding="utf-8") as f:
            rep = f.read()
        self.assertIn("source_missing", rep)
        self.assertIn("未提供 --health", rep)
        self.assertIn("未提供 --priority", rep)


class EnvelopeJsonFlagTests(EnvelopeCase):
    """--json:envelope 只打 stdout,不落盘任何文件"""

    def test_json_prints_envelope_without_persisting(self):
        r = self.run_envelope(
            make_audit({"https://s.com/a": [("WARN", "og", "og:title 缺失")]},
                       ai={"https://s.com/a": 55}),
            make_health(), as_json=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        env = json.loads(r.stdout)                          # stdout 只有 envelope JSON
        self.assertEqual(env["schema_version"], 1)
        self.assertEqual(env["summary"]["main_score"], 80.0)
        self.assertEqual(env["summary"]["ai_search_health"], 55.0)
        self.assertEqual(os.listdir(self.out), [])          # 未创建任何文件


if __name__ == "__main__":
    unittest.main(verbosity=1)
