#!/usr/bin/env python3
"""grounding_page.py 测试(品牌实体事实页生成器,合成 YAML,零网络)。
覆盖 Rankscale 11 条逐条:单 H1/首段中英文一句定义/dl 不用 table/FAQ 5-10 且每答含名/
volatile 独立区块+Last reviewed/is-NOT 生成与占位/JSON-LD 镜像+sameAs+--type+无 FAQPage/
hub-spoke 与 URL 打印提示/谓词注释/--json 形状/--check 模式(生成页全过 + 不合规页抓 FAIL)。
standalone(自带 run_script 助手): python3 tests/test_grounding_page.py
亦被 tests/run_tests.py 按 test_*.py 独立测试文件自动发现加载。"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import grounding_page as gp  # noqa: E402  (需先入 SCRIPTS 路径;import 期无副作用)


def run_script(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "grounding_page.py"), *args],
                          capture_output=True, text=True, encoding="utf-8", env=env)


def tmp_file(content, suffix):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


FACTS_ZH = """\
brand: Acme
facts:
  - fact: "Acme 是一家客户关系管理(CRM)软件公司,总部在柏林"
    record: company
    source: https://acme.ai/about
    date: 2026-08-12
    confidence: high
  - fact: "Acme 成立于 2015 年"
    record: company
    source: https://acme.ai/about
    date: 2026-08-12
    confidence: high
  - fact: "Acme 的差异化是“部署 10 分钟上手”,不是“企业套件大而全”"
    record: company
    source: https://acme.ai/positioning
    date: 2026-09-28
    confidence: high
  - fact: "Acme 所在类目是中小团队 CRM,不是企业级 CRM 套件"
    record: market
    source: https://acme.ai/positioning
    date: 2026-09-28
    confidence: high
  - fact: "Acme 的主要竞对是 HubSpot、Pipedrive 与 Zoho CRM"
    record: market
    source: https://acme.ai/positioning
    date: 2026-09-28
    confidence: high
  - fact: "产品线两条:Starter 与 Business"
    record: offerings
    source: https://acme.ai/pricing
    date: 2026-10-01
    confidence: high
  - fact: "Acme Business 定价为 $49/月,按年计费为 $39/月"
    record: offerings
    source: https://acme.ai/pricing
    date: 2026-10-01
    confidence: high
  - fact: "Acme 支持 SSO 登录,仅 Business 计划"
    record: offerings
    source: https://docs.acme.ai/sso
    date: 2026-07-20
    confidence: high
  - fact: "Acme 的官方领英档案是 https://www.linkedin.com/company/acme"
    record: execution
    source: https://www.linkedin.com/company/acme
    date: 2026-09-01
    confidence: high
  - fact: "首要客户画像:10-50 人的 B2B 销售团队"
    record: audience
    source: https://acme.ai/positioning
    date: 2026-09-28
    confidence: high
  - fact: "消歧:Acme 不是 Acme Corp(美国保险集团),同名不同实体"
    record: company
    source: https://acme.ai/about
    date: 2026-08-12
    confidence: high
"""

# 无消歧记录、无社媒链接、无竞对/差异点的最小 facts(占位路径)
FACTS_MIN = """\
brand: Solo
facts:
  - fact: "Solo 是一家个人记账工具"
    record: company
    source: https://solo.app/about
    date: 2026-09-01
    confidence: high
  - fact: "Solo 成立于 2022 年"
    record: company
    source: https://solo.app/about
    date: 2026-09-01
    confidence: high
  - fact: "Solo 的创始人是李某"
    record: company
    source: https://solo.app/about
    date: 2026-09-01
    confidence: high
  - fact: "Solo 定价为 $5/月"
    record: offerings
    source: https://solo.app/pricing
    date: 2026-10-02
    confidence: high
  - fact: "Solo 支持 iOS 与 Android"
    record: offerings
    source: https://solo.app/mobile
    date: 2026-08-15
    confidence: high
"""

FACTS_EN = """\
brand: Nimbus
facts:
  - fact: "Nimbus is a team wiki software company for distributed teams"
    record: company
    source: https://nimbus.io/about
    date: 2026-09-01
    confidence: high
  - fact: "Nimbus is headquartered in Toronto"
    record: company
    source: https://nimbus.io/about
    date: 2026-09-01
    confidence: high
  - fact: "Nimbus was founded in 2019"
    record: company
    source: https://nimbus.io/about
    date: 2026-09-01
    confidence: high
  - fact: "Nimbus differentiator is real-time collaborative editing"
    record: company
    source: https://nimbus.io/positioning
    date: 2026-09-20
    confidence: high
  - fact: "Nimbus Pro pricing is $10 per user per month"
    record: offerings
    source: https://nimbus.io/pricing
    date: 2026-10-02
    confidence: high
  - fact: "Nimbus supports Windows, macOS and Linux"
    record: offerings
    source: https://docs.nimbus.io/desktop
    date: 2026-08-15
    confidence: high
"""

BAD_PAGE = """\
# BadCo

BadCo is a thing.

## Overview

<table><tr><td>Founded</td><td>2019</td></tr></table>

## FAQ

<p><strong>What is the price?</strong> It costs $49 per month.</p>
<p><strong>Where is it based?</strong> In Berlin.</p>
<p><strong>When was it founded?</strong> In 2019.</p>
<p><strong>Does it support SSO?</strong> Yes, on the Pro plan.</p>
<p><strong>Is there a free tier?</strong> No, there is not.</p>

<script type="application/ld+json">
{"@context": "https://schema.org", "@type": "FAQPage", "name": "BadCo"}
</script>

最后复核:2020-01-01

# BadCo Again
"""


def faq_pairs(page):
    """从生成页抽 FAQ (问题, 答案) 对。"""
    m = re.search(r'<section id="faq">(.*?)</section>', page, re.S)
    pairs = []
    for p in re.finditer(r"<p>(.*?)</p>", m.group(1), re.S):
        q = re.search(r"<strong>(.*?)</strong>", p.group(1))
        pairs.append((q.group(1), p.group(1)[q.end():].strip()))
    return pairs


class GroundingPageTests(unittest.TestCase):
    """合成 fixtures:中文全量 / 最小占位 / 英文句式,生成 + --check 两模式。"""

    @classmethod
    def setUpClass(cls):
        cls.facts = tmp_file(FACTS_ZH, ".yaml")
        cls.facts_min = tmp_file(FACTS_MIN, ".yaml")
        cls.facts_en = tmp_file(FACTS_EN, ".yaml")
        cls.tmpdir = tempfile.mkdtemp(prefix="grounding_")

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.facts)
        os.unlink(cls.facts_min)
        os.unlink(cls.facts_en)
        for n in os.listdir(cls.tmpdir):
            os.unlink(os.path.join(cls.tmpdir, n))
        os.rmdir(cls.tmpdir)

    def _gen(self, *extra, facts=None):
        return run_script(["--facts", facts or self.facts, *extra])

    # ---- 基础 ----

    def test_help_exits_zero(self):
        r = run_script(["--help"])
        self.assertEqual(r.returncode, 0)
        for token in ("--facts", "--name", "--type", "--check", "--json"):
            self.assertIn(token, r.stdout)

    def test_yaml_subset_parser(self):
        brand, facts, warnings = gp.parse_facts_yaml(self.facts)
        self.assertEqual(brand, "Acme")
        self.assertEqual(len(facts), 11)
        self.assertEqual(facts[0]["record"], "company")
        self.assertEqual(facts[0]["confidence"], "high")
        self.assertIn("柏林", facts[0]["fact"])          # 引号被正确剥离
        self.assertTrue(not facts[0]["fact"].endswith('"'))

    # ---- 11 条逐条(1-3) ----

    def test_h1_unique_and_lead_sentence(self):
        r = self._gen("--name", "Acme")
        self.assertEqual(r.returncode, 0)
        h1s = [l for l in r.stdout.splitlines() if l.startswith("# ")]
        self.assertEqual(h1s, ["# Acme"])               # 1 唯一 H1=实体名,不加修饰
        self.assertIn("Acme 是一家客户关系管理(CRM)软件公司,"
                      "以部署 10 分钟上手为差异化。", r.stdout)   # 2 中文一句式
        # --name 缺省回退 YAML brand
        r2 = self._gen()
        self.assertIn("# Acme", r2.stdout)

    def test_core_facts_dl_no_table(self):
        r = self._gen("--name", "Acme")
        self.assertIn("<dl>", r.stdout)                 # 3 dl 而非 table
        self.assertNotIn("<table", r.stdout)
        for dt, dd in (("类目", "中小团队 CRM"), ("成立", "2015 年"), ("总部", "柏林"),
                       ("主要竞对", "HubSpot、Pipedrive 与 Zoho CRM"),
                       ("首要客户", "10-50 人的 B2B 销售团队"), ("产品线", "Starter 与 Business")):
            self.assertIn("<dt>%s</dt><dd>%s</dd>" % (dt, dd), r.stdout)

    # ---- 11 条逐条(4-5) ----

    def test_faq_5_to_10_every_answer_contains_name(self):
        r = self._gen("--name", "Acme")
        pairs = faq_pairs(r.stdout)
        self.assertTrue(5 <= len(pairs) <= 10, "FAQ %d 条不在 5-10" % len(pairs))
        for q, a in pairs:
            self.assertIn("Acme", a)                    # 4 每条答案含实体名
            self.assertTrue(q.endswith("?"))
            self.assertNotIn("FAQPage", "".join(
                re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                           r.stdout, re.S)))           # 不生成 FAQPage JSON-LD
        self.assertIn("2026-05", r.stdout)              # 退役注释注明

    def test_volatile_block_separate_with_last_reviewed(self):
        r = self._gen("--name", "Acme")
        before, after = r.stdout.split('<section id="volatile">', 1)
        self.assertIn("<dt>成立</dt>", before)          # 稳定事实在 volatile 之外
        self.assertNotIn("$49", before)
        self.assertIn("<h2>易变事实", after)            # 5 独立区块
        self.assertIn("$49/月", after)
        self.assertRegex(after, r"Last reviewed:\s*\d{4}-\d{2}-\d{2}")
        self.assertIn("(2026-10-01 复核)", after)

    # ---- 11 条逐条(6-7) ----

    def test_is_not_block_and_placeholder(self):
        r = self._gen("--name", "Acme")
        sec = re.search(r'<section id="is-not">(.*?)</section>', r.stdout, re.S).group(1)
        self.assertIn("Acme 不是 Acme Corp(美国保险集团)", sec)   # 6 消歧生成
        self.assertIn("同名不同实体", sec)
        # 无消歧记录→占位注释提示人工填
        r2 = self._gen("--name", "Solo", facts=self.facts_min)
        sec2 = re.search(r'<section id="is-not">(.*?)</section>', r2.stdout, re.S).group(1)
        self.assertIn("人工填写", sec2)
        self.assertIn("Solo 不是", r2.stdout)

    def test_jsonld_type_sameas_mirror(self):
        r = self._gen("--name", "Acme")
        ld = json.loads(re.search(r'<script type="application/ld\+json">\n(.*?)\n</script>',
                                  r.stdout, re.S).group(1))
        self.assertEqual(ld["@type"], "Organization")   # 7 @type 按 --type(默认)
        self.assertEqual(ld["name"], "Acme")
        self.assertEqual(ld["foundingDate"], "2015")    # 只镜像页面可见事实
        self.assertIn("https://www.linkedin.com/company/acme", ld["sameAs"])
        self.assertIn("Acme 是一家", ld["description"])
        # --type 覆盖
        r2 = self._gen("--name", "Acme", "--type", "SoftwareApplication")
        ld2 = json.loads(re.search(r'<script type="application/ld\+json">\n(.*?)\n</script>',
                                   r2.stdout, re.S).group(1))
        self.assertEqual(ld2["@type"], "SoftwareApplication")
        self.assertIn("Entity type: SoftwareApplication", r2.stdout)

    # ---- 11 条逐条(8-11) ----

    def test_hub_spoke_and_url_hints_and_predicates(self):
        r = self._gen("--name", "Acme")
        self.assertIn("检测到 2 个产品", r.stderr)      # 8 spoke 候选打印,不自动拆
        self.assertIn("- Starter", r.stderr)
        self.assertIn("- Business", r.stderr)
        self.assertIn("不自动拆", r.stderr)
        self.assertIn("/about 或 /brand", r.stderr)     # 11 URL 简短建议
        self.assertIn("/acme", r.stderr)
        self.assertIn("isPartOf", r.stdout)             # 9 谓词建议以注释输出
        self.assertIn("hasPart", r.stdout)
        self.assertIn("≤6 个月", r.stdout)              # 10 注释在场
        self.assertRegex(r.stdout, r"最后复核:%s ·" % date.today().isoformat())

    # ---- --json 形状 ----

    def test_json_output_shape(self):
        r = self._gen("--name", "Acme", "--json")
        self.assertEqual(r.returncode, 0)
        payload = json.loads(r.stdout)
        for key in ("schema_version", "mode", "entity", "lead_definition", "core_facts",
                    "volatile_facts", "faq", "is_not", "jsonld", "sameas",
                    "faqpage_jsonld", "spoke_candidates", "review_date", "review_expiry",
                    "hints", "warnings", "markdown"):
            self.assertIn(key, payload)
        self.assertEqual(payload["mode"], "generate")
        self.assertEqual(payload["entity"], {"name": "Acme", "type": "Organization",
                                             "language": "zh"})
        self.assertEqual(payload["review_date"], date.today().isoformat())
        self.assertTrue(5 <= len(payload["faq"]) <= 10)
        self.assertTrue(all("Acme" in f["answer"] for f in payload["faq"]))
        self.assertEqual(payload["spoke_candidates"], ["Starter", "Business"])
        self.assertTrue(payload["is_not"]["found"])
        self.assertIn("retired 2026-05-07", payload["faqpage_jsonld"])

    # ---- 英文句式 ----

    def test_english_lead_and_faq(self):
        r = self._gen("--name", "Nimbus", facts=self.facts_en)
        self.assertIn("# Nimbus", r.stdout)
        self.assertIn("Nimbus is a team wiki software company for distributed teams "
                      "that is differentiated by real-time collaborative editing.",
                      r.stdout)                          # 2 英文 "{name} is a {category} that {function}"
        self.assertIn("<dt>Founded</dt><dd>2019</dd>", r.stdout)
        self.assertIn("<dt>Headquarters</dt><dd>Toronto</dd>", r.stdout)
        pairs = faq_pairs(r.stdout)
        self.assertTrue(5 <= len(pairs) <= 10, "en FAQ %d 条" % len(pairs))
        self.assertTrue(all("Nimbus" in a for _, a in pairs))

    # ---- --check 模式 ----

    def test_check_generated_page_all_pass(self):
        page = os.path.join(self.tmpdir, "generated.md")
        self._gen("--name", "Acme", "--out", page)
        r = run_script(["--check", page, "--name", "Acme"])
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("[FAIL]", r.stdout)
        for no in (1, 2, 3, 4, 5, 6, 7, 9, 10):
            self.assertIn("[PASS] %02d" % no, r.stdout)
        self.assertIn("[MANUAL] 08", r.stdout)          # hub-and-spoke 需人工判断
        self.assertIn("[MANUAL] 11", r.stdout)          # URL 无法从文件判定
        # 检查模式 --json
        rj = run_script(["--check", page, "--name", "Acme", "--json"])
        self.assertEqual(rj.returncode, 0)
        cj = json.loads(rj.stdout)
        self.assertTrue(cj["ok"])
        self.assertEqual(cj["fail_count"], 0)
        self.assertEqual(len(cj["checks"]), 11)

    def test_check_bad_page_fails(self):
        page = tmp_file(BAD_PAGE, ".md")
        try:
            r = run_script(["--check", page, "--name", "BadCo"])
            self.assertEqual(r.returncode, 1)
            self.assertIn("[FAIL] 01", r.stdout)        # 双 H1
            self.assertIn("H1 数量=2", r.stdout)
            self.assertIn("[FAIL] 03", r.stdout)        # table 且无 dl
            self.assertIn("[FAIL] 04", r.stdout)        # FAQ 答案不含名
            self.assertIn("含名率 0/5", r.stdout)
            self.assertIn("[FAIL] 05", r.stdout)        # 缺 volatile 区块
            self.assertIn("[FAIL] 06", r.stdout)        # 缺 is-NOT 区块
            self.assertIn("[FAIL] 07", r.stdout)        # FAQPage JSON-LD 已退役
            self.assertIn("[FAIL] 10", r.stdout)        # 复核日期超 6 个月
            self.assertIn("2020-01-01", r.stdout)
            self.assertIn("183", r.stdout)
        finally:
            os.unlink(page)

    def test_review_date_age_boundary(self):
        """今天生成的页 age=0 通过;check 的年龄计算与 ≤183 天口径。"""
        page = os.path.join(self.tmpdir, "fresh.md")
        self._gen("--name", "Acme", "--out", page)
        r = run_script(["--check", page, "--name", "Acme"])
        self.assertIn("距今 0 天", r.stdout)
        stale = tmp_file(BAD_PAGE.replace("2020-01-01", date.today().isoformat()).replace(
            "最后复核", "最后复核"), ".md")
        try:
            r2 = run_script(["--check", stale, "--name", "BadCo"])
            self.assertIn("距今 0 天 ≤ 183", r2.stdout)   # 当日复核→第 10 条过
        finally:
            os.unlink(stale)


if __name__ == "__main__":
    unittest.main(verbosity=1)
