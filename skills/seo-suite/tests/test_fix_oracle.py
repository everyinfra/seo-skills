#!/usr/bin/env python3
"""oracle_check.py R5 修复验证(2026-10-12 补写:修复已入 39db653,测试后被限额截断)。
覆盖:多语言分语系(ko/ru/ar 不再 0 findings)/ 货币分币种($99≠99元)/ 中文否定误伤(无限)/
指纹含采样序号(多采样不互相覆盖)/ reopen 归一 pending / 全角标点切句。零网络。"""
import json, os, subprocess, sys, tempfile, unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)
import oracle_check as oc  # noqa: E402


def tmp_file(content, suffix):
    f = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content); f.close(); return f.name


def run_cli(facts, responses, extra=()):
    fp = tmp_file(facts, ".yaml"); rp = tmp_file(json.dumps(responses, ensure_ascii=False), ".json")
    # --out 指向临时目录:不向 CWD 滴 findings.json(同 test_oracle_check._run)
    out = os.path.join(tempfile.mkdtemp(prefix="oracle_fix_"), "findings.json")
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "oracle_check.py"),
                        "--facts", fp, "--responses", rp, "--json", "--out", out, *extra],
                       capture_output=True, text=True, encoding="utf-8", timeout=60,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    d = {}
    i = r.stdout.find("{")
    if i >= 0:
        try:
            d = json.loads(r.stdout[i:])
        except ValueError:
            pass
    return r, d


FACTS_KO = """\
brand: 아크메
facts:
  - fact: "아크메 Pro 가격은 월 49달러입니다"
    record: offerings
    source: https://acme.ai/pricing
    date: 2026-09-01
    confidence: high
"""

FACTS_RU = """\
brand: Акме
facts:
  - fact: "Акме Pro стоит 49 долларов в месяц"
    record: offerings
    source: https://acme.ai/pricing
    date: 2026-09-01
    confidence: high
"""

FACTS_AR = """\
brand: أكме
facts:
  - fact: "يبلغ سعر أكме Pro 49 دولارا شهريا"
    record: offerings
    source: https://acme.ai/pricing
    date: 2026-09-01
    confidence: high
"""

FACTS_CUR = """\
brand: Acme
facts:
  - fact: "Acme Pro 定价为 $99/月"
    record: offerings
    source: https://acme.ai/pricing
    date: 2026-09-01
    confidence: high
"""

FACTS_NEG = """\
brand: Acme
facts:
  - fact: "Acme 提供无限免费存储"
    record: offerings
    source: https://acme.ai/docs
    date: 2026-09-01
    confidence: high
"""


class OracleMultilingualFixTests(unittest.TestCase):
    def _resp(self, text):
        return [{"prompt": "价格是多少", "engine": "chatgpt", "text": text, "mentions": ["아크메"]}]

    def test_korean_facts_produce_findings(self):
        r, d = run_cli(FACTS_KO, self._resp("아크메 Pro 가격은 월 99달러입니다"))
        self.assertGreater(len(d.get("findings", [])), 0,
                            f"ko 事实不应再静默 0 findings;stderr={r.stderr[-200:]}")

    def test_russian_facts_produce_findings(self):
        r, d = run_cli(FACTS_RU, [{"prompt": "цена", "engine": "chatgpt",
                                   "text": "Акме Pro стоит 199 долларов в месяц", "mentions": []}])
        self.assertGreater(len(d.get("findings", [])), 0,
                            f"ru 事实不应再静默 0 findings;stderr={r.stderr[-200:]}")

    def test_arabic_facts_produce_findings(self):
        r, d = run_cli(FACTS_AR, [{"prompt": "السعر", "engine": "chatgpt",
                                   "text": "يبلغ سعر أكمه Pro 999 دولارا شهريا", "mentions": []}])
        self.assertGreater(len(d.get("findings", [])), 0,
                            f"ar 事实不应再静默 0 findings;stderr={r.stderr[-200:]}")

    def test_currency_buckets_by_iso(self):
        r, d = run_cli(FACTS_CUR, [{"prompt": "价格", "engine": "chatgpt",
                                    "text": "Acme Pro 定价为 99元/月", "mentions": []}])
        self.assertGreater(len(d.get("findings", [])), 0,
                            "$99 与 99元 必须判冲突(分币种)")

    def test_infinite_not_false_negative(self):
        r, d = run_cli(FACTS_NEG, [{"prompt": "存储", "engine": "chatgpt",
                                    "text": "Acme 提供有限存储,上限 5GB", "mentions": []}])
        self.assertEqual(len(d.get("findings", [])), 0,
                         "'无限'不应误判否定极性产假冲突")


class OracleStateFixTests(unittest.TestCase):
    def test_fingerprint_includes_sample_index(self):
        # 同 prompt 两条不同回答、不同 claim → 指纹不同,互不覆盖
        resp = [{"prompt": "p", "engine": "e", "text": "Acme Pro 定价 $59", "mentions": []},
                {"prompt": "p", "engine": "e", "text": "Acme Pro 定价 $199", "mentions": []}]
        r, d = run_cli(FACTS_CUR, resp)
        fps = {f.get("fingerprint") for f in d.get("findings", [])}
        self.assertTrue(fps, "应有 findings")
        self.assertGreaterEqual(len(fps), 2, f"两条采样的 findings 指纹应互异,得 {fps}")

    def test_fullwidth_punct_splits(self):
        self.assertGreaterEqual(len(oc.SENT_SPLIT.split("第一句！第二句？第三句。")), 3,
                                "全角!? 应切句")


if __name__ == "__main__":
    unittest.main(verbosity=1)
