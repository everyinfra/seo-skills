#!/usr/bin/env python3
"""content_queue.py 子命令 --help 回归测试(2026-10-21 用参数核对脚本扫参考文件时发现,修前红、修后绿)。

期望值来源:脚本自己的契约——cmd_collect 里的注释写明「参数错/--help 由 argparse 处理」,
也就是 `content_queue.py collect --help` 应该打印 collect 子命令的参数(--gsc、--serp-out……),
而不是总帮助;参考文件里写的 `content_queue.py collect --gsc cur.csv --gsc prev.csv` 要能从 --help 查到。
用法: python3 tests/test_content_queue_help.py(tests/run_tests.py 自动发现本文件)"""
import os
import subprocess
import sys
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(BASE, "scripts", "content_queue.py")


def run(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True,
                          encoding="utf-8", env=env)


class ContentQueueSubcommandHelp(unittest.TestCase):
    def test_collect_help_lists_collect_flags(self):
        r = run(["collect", "--help"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--gsc", r.stdout)
        self.assertIn("--serp-out", r.stdout)

    def test_track_help_lists_track_flags(self):
        r = run(["track", "--help"])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("--status", r.stdout)

    def test_top_level_help_still_lists_subcommands(self):
        r = run(["--help"])
        self.assertEqual(r.returncode, 0, r.stderr)
        for sub in ("collect", "plan", "track", "report"):
            self.assertIn(sub, r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
