#!/usr/bin/env python3
"""B55 monitor.ping_heartbeat 与 B57 market_fit U5 标注回归(stdlib unittest,零网络)。

期望值来源:
- B55 healthchecks.io Pinging API 原文(https://healthchecks.io/docs/http_api/,2026-10-21 打开核对):
  Success = `https://hc-ping.com/<uuid>`(无后缀);Failure = `https://hc-ping.com/<uuid>/fail`。
  修前成功时 ping `<url>/ok`——该路径不在官方端点表里。
- B57 references/research/multilingual-geo-evidence.md:U5「唯一可用源红利」状态为「假设」
  (2026-10-21 复核:无来源,降级为假设)。脚本输出引用 U5 时必须写「假设，未证实」。
用法: python3 tests/test_s3_monitor_fit.py(tests/run_tests.py 自动发现本文件)"""
import json
import os
import subprocess
import sys
import unittest
from unittest import mock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

import monitor  # noqa: E402

UUID_URL = "https://hc-ping.com/5bf66975-d4c7-4bf5-bcc8-b8d8a82ea278"


class _Resp:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self, n=-1):
        return b"OK"


class HeartbeatTests(unittest.TestCase):
    def _pinged(self, url, ok):
        seen = []

        def fake_urlopen(req, timeout=None):
            seen.append(req.full_url)
            return _Resp()
        with mock.patch.object(monitor.urllib.request, "urlopen", fake_urlopen):
            monitor.ping_heartbeat(url, ok)
        return seen

    def test_success_pings_bare_url(self):
        self.assertEqual(self._pinged(UUID_URL, True), [UUID_URL])
        self.assertEqual(self._pinged(UUID_URL + "/", True), [UUID_URL])

    def test_failure_pings_fail_suffix(self):
        self.assertEqual(self._pinged(UUID_URL, False), [UUID_URL + "/fail"])

    def test_no_ok_suffix_anywhere_in_help(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "monitor.py"), "init", "--help"],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertNotIn("/ok", r.stdout)


class MarketFitU5Tests(unittest.TestCase):
    def test_u5_notes_marked_hypothesis(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "market_fit.py"), "--json"],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        notes = [n for n in json.loads(r.stdout)["opportunity_notes"] if "U5" in n]
        self.assertTrue(notes)
        for n in notes:
            self.assertIn("假设，未证实", n)


if __name__ == "__main__":
    unittest.main()
