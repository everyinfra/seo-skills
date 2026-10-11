#!/usr/bin/env python3
"""CAPABILITY_MATRIX 机器可读矩阵守护测试(niubigeo N10 治理格式的落地;standalone 零网络)。

被守护对象:data/capability-matrix.json(113 条 = 76 脚本 + 24 模板 + 13 references 主干
与人读版 CAPABILITY_MATRIX.md。五检:
  ① MatrixFileCoverageTests   双向文件覆盖:矩阵每个 script 真实存在;scripts/ 每个
     .py(除 __pycache__)都在矩阵;模板/references 路径亦须真实存在;
  ② MatrixTestsFileTests      每个 tests_file 真实存在(null 合法);
  ③ MatrixSchemaTests         type/status/outputs_schema/fallback_mode 枚举合法,
     summary 计数与条目一致,无重名;
  ④ MatrixContractAlignmentTests  与 references/overview/data-source-contract.md 三列
     粗对齐(抽查 10 条:data_source 至少一个片段命中合同"数据"列 + 降级模式字符
     命中合同"降级"列;不要求逐字);
  ⑤ MatrixTemplateCountTests  模板恰 23 个,且与 templates/ 磁盘 .md 集合完全一致。

standalone:`python3 tests/test_capability_matrix.py` 全绿退出 0;
亦被 tests/run_tests.py 按 test_*.py 自动发现加载(本文件勿做 import 期副作用)。
scripts/self_check.py 的 check_capability_matrix 以
`test_capability_matrix.py MatrixFileCoverageTests MatrixTestsFileTests` 只跑 ①②。

维护规则(见 CAPABILITY_MATRIX.md):新增脚本/模板必须同步更新矩阵,否则本测试变红。
"""
import glob
import json
import os
import re
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRIX = os.path.join(BASE, "data", "capability-matrix.json")
CONTRACT = os.path.join(BASE, "references", "overview", "data-source-contract.md")
SCRIPTS_DIR = os.path.join(BASE, "scripts")

VALID_TYPE = {"script", "template", "reference"}
VALID_STATUS = {"stable", "beta", "draft"}
VALID_OUTPUTS = {"json", "markdown", "csv"}
VALID_FALLBACK = set("①②③④")

with open(MATRIX, encoding="utf-8") as _f:
    DATA = json.load(_f)
ENTRIES = DATA["entries"]
SCRIPT_ENTRIES = [e for e in ENTRIES if e["type"] == "script"]
TEMPLATE_ENTRIES = [e for e in ENTRIES if e["type"] == "template"]

# ④ 抽查 10 条(覆盖 8 个脚本组里吃数据/降级路径最典型的脚本;不要求逐字)
CONTRACT_SAMPLE = [
    "site_audit.py", "gsc_mining.py", "market_lint.py", "citation_panel.py", "monitor.py",
    "doctor.py", "grid_rank.py", "redirect_chain.py", "oracle_check.py", "forecast.py",
]


def _norm(s):
    """粗对齐归一:去空白/反引号/加粗标记。"""
    return re.sub(r"[\s`*]+", "", s or "")


def _contract_rows():
    """解析 data-source-contract.md 全部表格行 → {script: (数据列, 降级列)}。"""
    rows = {}
    with open(CONTRACT, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\|\s*`([\w.-]+\.py)`\s*\|([^|]*)\|([^|]*)\|", line)
            if m:
                rows[m.group(1)] = (m.group(2), m.group(3))
    return rows


class MatrixFileCoverageTests(unittest.TestCase):
    """① 矩阵 ↔ 文件系统 双向覆盖。"""

    def test_every_matrix_script_exists_on_disk(self):
        missing = [e["script"] for e in SCRIPT_ENTRIES
                   if not os.path.isfile(os.path.join(SCRIPTS_DIR, e["script"]))]
        self.assertEqual(missing, [], "矩阵收录但 scripts/ 无此文件")

    def test_every_disk_script_is_in_matrix(self):
        disk = {f for f in os.listdir(SCRIPTS_DIR)
                if f.endswith(".py") and f != "__pycache__"}
        listed = {e["script"] for e in SCRIPT_ENTRIES}
        self.assertEqual(sorted(disk - listed), [], "scripts/ 存在但未入矩阵(新增脚本必须同步更新矩阵)")
        self.assertEqual(sorted(listed - disk), [], "矩阵收录但文件不存在")

    def test_template_and_reference_paths_exist(self):
        missing = [e["path"] for e in ENTRIES
                   if e["type"] != "script" and not os.path.isfile(os.path.join(BASE, e["path"]))]
        self.assertEqual(missing, [], "矩阵收录的模板/主干路径不存在")


class MatrixTestsFileTests(unittest.TestCase):
    """② 每个 tests_file 真实存在(null 合法)。"""

    def test_every_tests_file_exists(self):
        missing = []
        for e in ENTRIES:
            tf = e.get("tests_file")
            if tf and not os.path.isfile(os.path.join(BASE, tf)):
                missing.append("%s -> %s" % (e.get("script") or e.get("path"), tf))
        self.assertEqual(missing, [], "矩阵指向的 tests_file 不存在")


class MatrixSchemaTests(unittest.TestCase):
    """③ 枚举合法 + summary 计数一致 + 无重名。"""

    def test_enums_counts_and_uniqueness(self):
        problems = []
        names = []
        counts = {"script": 0, "template": 0, "reference": 0,
                  "stable": 0, "beta": 0, "draft": 0}
        for e in ENTRIES:
            key = e.get("script") or e.get("path")
            names.append(key)
            if e.get("type") not in VALID_TYPE:
                problems.append("%s: type 非法" % key)
            if e.get("status") not in VALID_STATUS:
                problems.append("%s: status 非法" % key)
            if e.get("outputs_schema") not in VALID_OUTPUTS:
                problems.append("%s: outputs_schema 非法" % key)
            fb = e.get("fallback_mode")
            if fb is not None and (not isinstance(fb, str)
                                   or not set(fb) <= (VALID_FALLBACK | {"+"})):
                problems.append("%s: fallback_mode 非法" % key)
            if e["type"] == "script" and not e.get("inputs"):
                problems.append("%s: 脚本条目缺 inputs" % key)
            counts[e["type"]] += 1
            counts[e["status"]] += 1
        self.assertEqual(problems, [])
        self.assertEqual(len(names), len(set(names)), "矩阵条目重名")
        self.assertEqual(counts, DATA["summary"],
                         "summary 计数与条目实际不符(改条目必须同步改 summary)")

    def test_fallback_primary_mode_first(self):
        """fallback_mode 首字符必须是①-④之一(主模式在前,如 '③+②')。"""
        bad = [e.get("script") or e.get("path") for e in ENTRIES
               if e.get("fallback_mode") is not None
               and e["fallback_mode"][0] not in VALID_FALLBACK]
        self.assertEqual(bad, [])


class MatrixContractAlignmentTests(unittest.TestCase):
    """④ 与 data-source-contract.md 三列粗对齐(抽查 10 条,不要求逐字)。"""

    def test_sampled_entries_coarsely_match_contract(self):
        rows = _contract_rows()
        problems = []
        for name in CONTRACT_SAMPLE:
            entry = next((e for e in SCRIPT_ENTRIES if e["script"] == name), None)
            self.assertIsNotNone(entry, "抽查样本 %s 不在矩阵" % name)
            self.assertIn(name, rows, "%s 未出现在 data-source-contract" % name)
            data_cell, fallback_cell = rows[name]
            # data_source:归一化后按标点切片,至少一个 ≥4 字符片段命中合同"数据"列
            frags = [fr for fr in re.split(r"[()。;:,、+/—\[\]①②③④]",
                                           _norm(entry["data_source"]))
                     if len(fr) >= 4]
            self.assertTrue(frags, "%s data_source 无有效片段" % name)
            if not any(fr in _norm(data_cell) for fr in frags):
                problems.append("%s: data_source 片段未命中合同数据列" % name)
            # fallback:全部①-④模式字符都应出现在合同"降级"列
            modes = set(entry["fallback_mode"]) & VALID_FALLBACK
            miss = modes - set(_norm(fallback_cell))
            if miss:
                problems.append("%s: 降级模式 %s 未命中合同降级列"
                                % (name, "".join(sorted(miss))))
        self.assertEqual(problems, [])


class MatrixTemplateCountTests(unittest.TestCase):
    """⑤ 模板 24 个,且与 templates/ 磁盘集合完全一致。"""

    def test_template_count_is_24_and_matches_disk(self):
        self.assertEqual(len(TEMPLATE_ENTRIES), 24, "模板数必须为 24(新增模板须同步更新矩阵)")
        disk = {os.path.relpath(p, BASE).replace(os.sep, "/")
                for p in glob.glob(os.path.join(BASE, "templates", "**", "*.md"),
                                   recursive=True)}
        listed = {e["path"] for e in TEMPLATE_ENTRIES}
        self.assertEqual(sorted(disk - listed), [], "templates/ 有文件未入矩阵")
        self.assertEqual(sorted(listed - disk), [], "矩阵收录的模板不在 templates/")


if __name__ == "__main__":
    unittest.main(verbosity=2)
