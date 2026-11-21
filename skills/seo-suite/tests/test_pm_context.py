#!/usr/bin/env python3
"""pm_context.py:开局确认后写回 .agents/product-marketing.md(RQ-237 例 11;stdlib unittest,零网络)。

期望值来源:
- 需求卡例 11 原文:「仓库里已经有 marketingskills 写的 .agents/product-marketing.md……开局第 1 环直接读它当草稿……
  改了的内容写回两边,格式不坏」。
- 上游格式和更新规矩来自 coreyhaines31/marketingskills 的 skills/product-marketing/SKILL.md(第 3、4 步):
  文件头 `# Product Marketing Context`、`**Document version:** vN`、`**Last updated:** 日期`;
  每段 `## 段名` 下一行一个 `**标签:** 值`;更新时版本号 +1、Last updated 改成今天、在 `## Changelog`
  最上面加一行「- vN (日期) — 改了什么、为什么」,旧条目不重排。上游没有校验脚本,所以「格式不坏」在这里落成:
  上面这些结构都还在、没动的段落逐字节相同。
- 任务说明第 11 项:只改对应段落,不认识的段落原样保留;文件不存在不新建。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
import pm_context as PM  # noqa: E402

# 按上游模板写的一份(含一个上游模板里没有的自定义段「Sales Notes」)
DOC = """# Product Marketing Context

**Document version:** v3
**Last updated:** 2026-07-16

## Product Overview
**One-liner:** Invoicing for small finance teams
**What it does:** Send invoices, chase payments, reconcile.
**Product category:** Invoicing software
**Product type:** SaaS
**Business model:** Subscription, $12/mo per seat

## Target Audience
**Target companies:** Agencies with 5-50 staff
**Decision-makers:** Finance lead

## Sales Notes
- Our reps say: "never discount annual plans".
**Weird label:** keep me exactly

## Goals
**Business goal:** 1,000 paying teams
**Conversion action:** [What you want visitors to do]
**Current metrics:** 300 teams

## Learnings
- Comparison pages convert best.

## Changelog
*Newest first. One line per revision: what changed and why.*
- v3 (2026-07-16) — Added pricing after the June change.
- v2 (2026-05-02) — Rewrote target audience.
"""


def section_bytes(text, name):
    lines = text.split("\n")
    secs = PM.sections(lines)
    a, b = secs[name]
    return "\n".join(lines[a:b])


class WriteBackFormatTests(unittest.TestCase):
    def setUp(self):
        self.new, self.changed = PM.update_text(DOC, {("Goals", "Conversion action"): "Start a free trial",
                                                      ("Target Audience", "Target companies"): "Agencies with 5-200 staff"},
                                                "seo-suite onboarding ring 1: user corrected", today="2026-11-21")

    def test_header_version_and_last_updated(self):
        self.assertTrue(self.new.startswith("# Product Marketing Context\n"))
        self.assertIn("**Document version:** v4\n", self.new)
        self.assertIn("**Last updated:** 2026-11-21\n", self.new)
        self.assertNotIn("v3\n**Last updated:** 2026-07-16", self.new)

    def test_changelog_newest_first_old_entries_untouched(self):
        log = section_bytes(self.new, "Changelog").split("\n")
        self.assertEqual(log[1], "*Newest first. One line per revision: what changed and why.*")
        self.assertTrue(log[2].startswith("- v4 (2026-11-21) — "), log[2])
        self.assertIn("Goals / Conversion action", log[2])
        self.assertEqual(log[3:5], ["- v3 (2026-07-16) — Added pricing after the June change.",
                                    "- v2 (2026-05-02) — Rewrote target audience."])

    def test_only_matching_lines_change(self):
        self.assertIn("**Conversion action:** Start a free trial\n", self.new)
        self.assertIn("**Target companies:** Agencies with 5-200 staff\n", self.new)
        for sec in ("Product Overview", "Sales Notes", "Learnings"):
            self.assertEqual(section_bytes(self.new, sec), section_bytes(DOC, sec), sec)
        # 同段里没改的行逐字相同
        self.assertIn("**Decision-makers:** Finance lead\n", self.new)
        self.assertIn("**Business goal:** 1,000 paying teams\n**Conversion action:** Start a free trial\n"
                      "**Current metrics:** 300 teams\n", self.new)
        # 除了改的两行、版本、日期和新加的 changelog 一行,其余每行都在、顺序不变
        old_lines = [ln for ln in DOC.split("\n") if not ln.startswith(("**Conversion action", "**Target companies",
                                                                        "**Document version", "**Last updated"))]
        new_lines = [ln for ln in self.new.split("\n") if not ln.startswith(("**Conversion action", "**Target companies",
                                                                             "**Document version", "**Last updated",
                                                                             "- v4 (2026-11-21)"))]
        self.assertEqual(old_lines, new_lines)

    def test_section_order_unchanged(self):
        self.assertEqual(list(PM.sections(self.new.split("\n"))), list(PM.sections(DOC.split("\n"))))

    def test_no_change_no_bump(self):
        same, changed = PM.update_text(DOC, {("Product Overview", "One-liner"): "Invoicing for small finance teams"},
                                       "x", today="2026-11-21")
        self.assertEqual(changed, [])
        self.assertEqual(same, DOC)

    def test_crlf_preserved(self):
        crlf = DOC.replace("\n", "\r\n")
        new, _ = PM.update_text(crlf, {("Goals", "Conversion action"): "Book a demo"}, "x", today="2026-11-21")
        self.assertNotIn("\n", new.replace("\r\n", ""))
        self.assertIn("**Conversion action:** Book a demo\r\n", new)

    def test_template_placeholder_not_read_as_fact(self):
        got = PM.read_fields(DOC)
        self.assertNotIn("Goals/Conversion action", got)          # 「[What you want visitors to do]」是模板占位
        self.assertEqual(got["Product Overview/One-liner"], "Invoicing for small finance teams")


class WriteBackFileTests(unittest.TestCase):
    def setUp(self):
        self.repo = os.path.realpath(tempfile.mkdtemp(prefix="pmctx_"))
        self.addCleanup(shutil.rmtree, self.repo, True)

    def test_missing_file_not_created(self):
        self.assertIsNone(PM.write_back(self.repo, {("Goals", "Conversion action"): "x"}, "r"))
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".agents")))

    def test_cli_write_and_untouched_bytes(self):
        os.makedirs(os.path.join(self.repo, ".agents"))
        p = os.path.join(self.repo, ".agents", "product-marketing.md")
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(DOC)
        r = subprocess.run([sys.executable, os.path.join(BASE, "scripts", "pm_context.py"), "write", "--repo", self.repo,
                            "--set", "Goals/Conversion action=Start a free trial"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["changed"][0]["new"], "Start a free trial")
        with open(p, encoding="utf-8", newline="") as f:
            new = f.read()
        for sec in ("Product Overview", "Target Audience", "Sales Notes", "Learnings"):
            self.assertEqual(section_bytes(new, sec), section_bytes(DOC, sec), sec)


class OnboardRoundTripTests(unittest.TestCase):
    """例 11 两个方向走一遍真实开局:第 1 环把文件当草稿读进来;确认后把用户改的写回去。"""

    def test_ring1_reads_draft_and_writes_back(self):
        repo = os.path.realpath(tempfile.mkdtemp(prefix="pmctx_ob_"))
        self.addCleanup(shutil.rmtree, repo, True)
        os.makedirs(os.path.join(repo, ".agents"))
        p = os.path.join(repo, ".agents", "product-marketing.md")
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(DOC)
        scan = {"schema": 1, "site": "https://acme.example",
                "signals": {"site_live": True, "robots_block_all": False, "homepage_noindex": False, "url_count": 40,
                            "first_seen": "2025-06-01", "has_llms_txt": True, "analytics": ["gtag"]},
                "site_scan": {"page_types": {"pricing": 1, "blog": 10}},
                "facts": [{"key": "product.name", "value": "Acme", "source": "https://acme.example/", "kind": "fact"}],
                "errors": []}
        with open(os.path.join(repo, "scan.json"), "w", encoding="utf-8") as f:
            json.dump(scan, f)
        ob = lambda *a: subprocess.run([sys.executable, os.path.join(BASE, "scripts", "onboard.py"), *a], cwd=repo,  # noqa: E731
                                       capture_output=True, text=True, encoding="utf-8")
        r = ob("start", "--site", "https://acme.example", "--scan", "scan.json", "--market", "en")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(os.path.join(repo, "seo-ops", "context", "profile.json"), encoding="utf-8") as f:
            prof = json.load(f)
        one = next(x for x in prof["facts"] if x["key"] == "product.one_liner")
        self.assertEqual((one["value"], one["source"]), ("Invoicing for small finance teams", PM.PATH))
        self.assertEqual(one.get("status"), "unconfirmed")
        r = ob("answer", "--ring", "1", "--set", "profile_ok=ok", "--set", "conversion=Start a free trial",
               "--set", "customers=Agencies with 5-200 staff", "--set", "main_line=Invoicing", "--quote", "ok", "--confirm")
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        with open(p, encoding="utf-8", newline="") as f:
            new = f.read()
        self.assertIn("**Conversion action:** Start a free trial\n", new)
        self.assertIn("**Target companies:** Agencies with 5-200 staff\n", new)
        self.assertIn("**Document version:** v4\n", new)
        for sec in ("Product Overview", "Sales Notes", "Learnings"):
            self.assertEqual(section_bytes(new, sec), section_bytes(DOC, sec), sec)


if __name__ == "__main__":
    unittest.main()
