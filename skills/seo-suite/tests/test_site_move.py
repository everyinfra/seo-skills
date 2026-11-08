#!/usr/bin/env python3
"""site_move.py 回归(RQ-237 第 3 批;stdlib unittest,只连本机回环)。

期望值来源:需求卡 RQ-237 例 10(Echo 11-08 确认)——改版前存基线、改后对比,
预埋 10 个迁移问题找到 ≥ 9 个,没预埋的地方 0 误报。预埋清单是测试站 tools/testsites/lifecycle_sites.py
的 PLANTS(在写 site_move.py 之前写定);脚本只拿产品说明和 MIGRATION.md 当输入,不看 PLANTS。
测试站目录不在装好的 Skill 里(只在源码仓),找不到就跳过。
"""
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
TESTSITES = os.path.join(os.path.dirname(os.path.dirname(BASE)), "tools", "testsites")


def run(args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "site_move.py"), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", env=env)


@unittest.skipUnless(os.path.isfile(os.path.join(TESTSITES, "lifecycle_sites.py")), "测试站只在源码仓")
class ChangeSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, TESTSITES)
        import hard_site
        import lifecycle_sites as ls
        cls.ls = ls
        cls.tmp = os.path.realpath(tempfile.mkdtemp(prefix="site_move_test_"))

        class Quiet(hard_site.Handler):
            def log_message(self, *a):
                pass

        cls.srv, urls = [], {}
        for state in ("before", "after"):
            d = os.path.join(cls.tmp, state)
            os.makedirs(os.path.join(d, "repo"))
            srv = http.server.ThreadingHTTPServer(
                ("127.0.0.1", 0), lambda *a, _d=os.path.join(d, "repo"), **k: Quiet(*a, directory=_d, **k))
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            cls.srv.append(srv)
            urls[state] = "http://127.0.0.1:%d" % srv.server_address[1]
            ls.build("change", d, urls[state], state)
        cls.urls = urls
        r = run(["baseline", "--site", urls["before"], "--allow-local", "--out", os.path.join(cls.tmp, "base.json")], cls.tmp)
        assert r.returncode == 0, r.stderr + r.stdout
        r = run(["compare", "--baseline", os.path.join(cls.tmp, "base.json"), "--new-site", urls["after"],
                 "--map", os.path.join(cls.tmp, "after", "repo", "MIGRATION.md"), "--allow-local", "--json"], cls.tmp)
        cls.code, cls.rep = r.returncode, json.loads(r.stdout)

    @classmethod
    def tearDownClass(cls):
        for s in cls.srv:
            s.shutdown()
        shutil.rmtree(cls.tmp, True)

    def matched(self, plant):
        _, _, urls, pat, _ = plant
        return [i for i in self.rep["issues"]
                if i["url"] in urls and re.search(pat, i["label"] + " " + i["detail"], re.I)]

    def test_recall_at_least_9_of_10(self):
        missed = [p[0] for p in self.ls.PLANTS if not self.matched(p)]
        self.assertLessEqual(len(missed), 1, "漏报 %s" % missed)
        self.assertEqual(self.code, 1)                  # 有 block 级问题

    def test_no_false_positive_outside_plants(self):
        fp = [i for i in self.rep["issues"] if i["url"] not in self.ls.PLANT_URLS]
        self.assertEqual(fp, [])

    def test_unchanged_site_is_clean(self):
        r = run(["compare", "--baseline", os.path.join(self.tmp, "base.json"), "--new-site", self.urls["before"],
                 "--allow-local", "--json"], self.tmp)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(json.loads(r.stdout)["issues"], [])


class MapParseTests(unittest.TestCase):
    def test_markdown_and_csv_maps(self):
        sys.path.insert(0, SCRIPTS)
        import site_move
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        md, cs = os.path.join(d, "m.md"), os.path.join(d, "m.csv")
        with open(md, "w", encoding="utf-8") as f:
            f.write("| 旧 | 新 |\n|---|---|\n| `/blog/a/` | `/articles/a/` |\n| https://old.example/p/x | /products/x/ |\n")
        with open(cs, "w", encoding="utf-8") as f:
            f.write("old,new\n/blog/a/,/articles/a/\n")
        self.assertEqual(site_move.load_map(md), {"/blog/a/": "/articles/a/", "/p/x": "/products/x/"})
        self.assertEqual(site_move.load_map(cs), {"/blog/a/": "/articles/a/"})


if __name__ == "__main__":
    unittest.main()
