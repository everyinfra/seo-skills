#!/usr/bin/env python3
"""tools/evals/plugin_suite_check.py 先校准再用:标准样子必过、坏样子必不过(stdlib unittest,零网络)。

期望值来源:Claude Code 官方文档 Test plugins with evals(code.claude.com/docs/en/plugin-evals):
「prompt.md frontmatter……An unknown key is an error」「a case without at least one grader fails to load」
「case.yaml……requires schema_version: "1.1" and name」;以及任务说明第 12 项「结构对、引用的文件都存在」。
"""
import os
import shutil
import sys
import tempfile
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(BASE))
sys.path.insert(0, os.path.join(ROOT, "tools", "evals"))
import plugin_suite_check as C  # noqa: E402


def failed(root):
    return [n for n, ok, _ in C.checks(root) if not ok]


class SuiteCheckTests(unittest.TestCase):
    def test_repo_passes(self):
        self.assertEqual(failed(ROOT), [])

    def broken_copy(self):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="suitecheck_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        for d in ("evals", "commands", "agents", "hooks", "skills"):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(tmp, d), symlinks=True,
                            ignore=shutil.ignore_patterns("results", "__pycache__", "tests", "references", "templates"))
        shutil.copytree(os.path.join(ROOT, "skills", "seo-suite", "references"),
                        os.path.join(tmp, "skills", "seo-suite", "references"))
        shutil.copytree(os.path.join(ROOT, "skills", "seo-suite", "templates"),
                        os.path.join(tmp, "skills", "seo-suite", "templates"))
        shutil.copy(os.path.join(ROOT, ".gitignore"), tmp)
        self.assertEqual(failed(tmp), [])                      # 复制品本身是好的
        return tmp

    def test_unknown_prompt_key_and_missing_graders_fail(self):
        tmp = self.broken_copy()
        case = os.path.join(tmp, "evals", "bad-case")
        os.makedirs(case)
        with open(os.path.join(case, "prompt.md"), "w", encoding="utf-8") as f:
            f.write("---\ndescription: x\nmax_turn: 5\n---\n\nhello\n")
        bad = failed(tmp)
        self.assertIn("bad-case/prompt.md 没有不认识的键", bad)
        self.assertIn("bad-case 至少一个判分器", bad)

    def test_bad_grader_case_yaml_and_missing_refs_fail(self):
        tmp = self.broken_copy()
        g = os.path.join(tmp, "evals", "start-first-screen", "graders", "x.md")
        with open(g, "w", encoding="utf-8") as f:
            f.write("---\ntype: tool_used\n---\n")               # tool_used 要 tool
        with open(os.path.join(tmp, "evals", "teach-deny-rule", "case.yaml"), "w", encoding="utf-8") as f:
            f.write('schema_version: "1.0"\nname: teach-deny-rule\ncontext:\n  scaffold_script: nope.sh\n')
        os.remove(os.path.join(tmp, "skills", "seo-suite", "scripts", "teach.py"))
        os.remove(os.path.join(tmp, "agents", "red-team.md"))
        bad = failed(tmp)
        self.assertIn("start-first-screen/graders/x 判分器选项齐", bad)
        self.assertIn('teach-deny-rule/case.yaml schema_version 是 "1.1"', bad)
        self.assertIn("teach-deny-rule scaffold_script 存在", bad)
        self.assertIn("命令 teach 引用的 skills/seo-suite/scripts/teach.py 存在", bad)
        self.assertIn("子代理 red-team 在 agents/", bad)


if __name__ == "__main__":
    unittest.main()
