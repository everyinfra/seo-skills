#!/usr/bin/env python3
"""seo-suite 的输出格式能不能被判分器读到(只验格式,不验 agent 行为)。

真跑 skill 的脚本(onboard.py start / answer、site_move.py baseline、plan.py build)读本地测试站
(lifecycle_sites.py 的改版站 before 状态),把脚本的真实输出原样放进一份转录(agent 只是把屏幕上的问题原样转给用户),
再用 grade.py 判 onboard-change 场景。期望值的来处:
  - 档案事实:answers/change.json(第 0 批出题人写定);阶段 5 也取自它;
  - 问题格式:criteria_defs 的 questions_per_ring_max 和 grade.py 文件头 R4、R16;
  - 页面类型:criteria_defs 的 ring1_not_skipped(min_page_types=4)和 R21;
  - 基线:scenarios.json 的 baseline_first(30 个旧 URL 抓过 ≥28 个)和 R29;
  - 方案:criteria_defs 的 must_do_hits_min(读 plan.json 的 items)、R12、R25;
  - 例 6 的 rules.md、试跑判定:scenarios_ext.json 的 rule_recorded、custom_check_trial_matches 原文。
没有网络;测试站起在 127.0.0.1 的随机端口。python3 -m unittest tools/evals/onboarding/test_skill_format.py
"""
import functools
import http.server
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SCRIPTS = os.path.join(ROOT, "skills", "seo-suite", "scripts")
LS = os.path.join(ROOT, "tools", "testsites", "lifecycle_sites.py")
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fixtures"))
import build as B  # noqa: E402
import grade as G  # noqa: E402

ANSWERS = os.path.join(HERE, "answers")
PY = sys.executable


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def run(args, cwd):
    p = subprocess.run([PY] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        raise AssertionError("%s 退出码 %s:%s" % (args[0], p.returncode, (p.stderr or p.stdout)[-600:]))
    return p.stdout


def questions_block(screen):
    """agent 照屏幕转给用户的问题:从「## 问用户」到「## 停」之前。"""
    a = screen.index("## 问用户")
    return screen[a:screen.index("## 停", a)].strip()


class SkillOutputReadable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="skillfmt_")
        cls.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=cls.tmp))
        base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        site = os.path.join(cls.tmp, "site")
        run([LS, "build", "--product", "change", "--state", "before", "--out", site, "--base", base], ROOT)
        repo = os.path.join(site, "repo")
        cls.httpd.RequestHandlerClass = functools.partial(Quiet, directory=repo)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.base, cls.repo = base, repo
        with open(os.path.join(ANSWERS, "change.json"), encoding="utf-8") as f:
            cls.ans = json.load(f)
        with open(os.path.join(HERE, "scenarios.json"), encoding="utf-8") as f:
            sc = next(s for s in json.load(f)["scenarios"] if s["id"] == "onboard-change")
        cls.reply1 = sc["simulated_user"]["1"][0]
        ob = os.path.join(SCRIPTS, "onboard.py")
        fx = cls.ans["facts"]
        cmd_start = ["onboard.py", "start", "--site", base, "--repo", ".", "--allow-local", "--no-wayback"]
        cls.out_start = run([ob] + cmd_start[1:], repo)
        cmd_base = ["site_move.py", "baseline", "--site", base, "--allow-local", "--out", "seo-ops/baselines/before.json"]
        cls.out_base = run([os.path.join(SCRIPTS, "site_move.py")] + cmd_base[1:], repo)
        quote = cls.reply1.strip()[:14]
        cmd_ans = ["onboard.py", "answer", "--ring", "1", "--set", "profile_ok=有几处要改",
                   "--set", "conversion=" + fx["conversion.primary"], "--set", "customers=" + ";".join(fx["customers"]),
                   "--set", "main_line=Sensor Pro", "--correct", "product.lines=" + "、".join(fx["product.lines"]),
                   "--correct", "pricing.model=" + fx["pricing.model"], "--correct", "stage=%d" % cls.ans["stage"],
                   "--quote", quote, "--confirm"]
        cls.out_ans = run([ob] + cmd_ans[1:], repo)
        cls.out_plan = run([os.path.join(SCRIPTS, "plan.py"), "build", "--ws", "seo-ops"], repo)
        ctx = os.path.join(repo, "seo-ops")
        with open(os.path.join(ctx, "context", "profile.json"), encoding="utf-8") as f:
            cls.profile = json.load(f)
        with open(os.path.join(ctx, "plan", "plan.json"), encoding="utf-8") as f:
            plan_json = json.load(f)
        with open(os.path.join(ctx, "plan", "plan.md"), encoding="utf-8") as f:
            plan_md = f.read()
        sh = lambda c: " ".join("'%s'" % x if (" " in x or ";" in x or "(" in x) else x for x in c)  # noqa: E731
        ex = {"scenario": "onboard-change", "site": base, "profile": cls.profile, "plan_json": plan_json,
              "plan_md": plan_md, "scenarios": os.path.join(HERE, "scenarios.json"), "turns": [
                  {"events": [{"bash": "python3 " + sh(cmd_start), "out": cls.out_start},
                              {"bash": "python3 " + sh(cmd_base), "out": cls.out_base},
                              {"text": questions_block(cls.out_start)}],
                   "reply": {"ring": 1, "text": cls.reply1}},
                  {"events": [{"bash": "python3 " + sh(cmd_ans), "out": cls.out_ans},
                              {"bash": "python3 plan.py build --ws seo-ops", "out": cls.out_plan},
                              {"tool": "Write", "input": {"file_path": os.path.join(repo, "seo-ops", "redirects-301.csv"),
                                                          "content": "old,new\n/blog/a/,/articles/a/\n"}},
                              {"text": "方案草稿写好了。"}], "reply": None}]}
        cls.paths = B.materialize(ex, os.path.join(cls.tmp, "run"))
        res = G.grade("onboard-change", cls.paths["ws"], cls.paths["transcript"], cls.paths["driver_log"],
                      scenarios=cls.paths["scenarios"], answers_dir=ANSWERS, site=base)
        cls.res = {a["id"]: a for a in res["assertions"]}

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # 1. profile.json 的 _schema:事实和阶段按 R8–R10 取得到
    def test_profile_facts_read_through_schema(self):
        a = self.res["facts_error_max"]
        self.assertTrue(a["pass"], json.dumps(a["evidence"], ensure_ascii=False)[:1500])
        for key in self.ans["facts"]:
            self.assertIn(key, self.profile["_schema"])
        for key in ("product.lines", "customers", "market.languages"):
            raw, _ = G.fact_raw(self.profile, key)
            self.assertIsInstance(G.unwrap(raw), list, key)

    def test_profile_stage_is_number(self):
        got, where = G.profile_stage(self.profile)
        self.assertEqual(got, self.ans["stage"])
        self.assertEqual(where, "_schema")
        self.assertEqual(self.res["stage_correct"]["evidence"]["got"], self.ans["stage"])

    # 3. 文本提问:问题行「数字.」+ 问号,每问带 A/B 选项或「我猜」
    def test_text_questions_have_choices(self):
        a = self.res["questions_per_ring_max"]
        self.assertTrue(a["pass"], json.dumps(a["evidence"], ensure_ascii=False))
        self.assertGreater(a["evidence"]["stops"], 0)
        self.assertNotIn("选项:", self.out_start)

    # 4. 开局抓页:robots.txt、sitemap、llms.txt 等逐条列出,数得出 ≥4 种页面类型
    def test_fetched_urls_give_page_types(self):
        pt = self.res["ring1_not_skipped"]["evidence"]["page_types"]
        for t in ("首页", "robots.txt", "sitemap", "llms.txt"):
            self.assertIn(t, pt)
        self.assertGreaterEqual(len(pt), 4)

    # 5. site_move 基线:30 个旧 URL 在 301 映射文件之前列出 ≥28 个
    def test_baseline_lists_old_urls(self):
        ev = self.res["baseline_first"]["evidence"]
        self.assertEqual(ev["of"], 30)
        self.assertGreaterEqual(ev["old_urls_fetched"], 28, ev)
        self.assertIn("seo-ops/baselines/before.json", self.out_base)

    # 2. 方案:plan.json 的 items,plan.md 的编号列表是同一份
    def test_plan_items_read(self):
        ev = self.res["must_do_hits_min"]["evidence"]
        self.assertEqual(ev["plan_source"], "plan.json")
        self.assertGreater(ev["items_seen"], 0)
        md = G.md_first_list(os.path.join(G.plan_dir(self.paths["ws"]), "plan.md"))
        items, _ = G.plan_items(self.paths["ws"])
        self.assertEqual(len(md), len(items))

    def test_plan_md_lists_guesses_first(self):
        # R25:方案开头 30 行内有「未确认 / 猜测 / 假设」,后面 ≥3 条列表项(这里有未确认的事实)
        lines, src = G.plan_doc_lines(self.paths["ws"])
        self.assertTrue(src.endswith("plan.md"))
        ok, ev = G.c_skip_outcome(type("CX", (), {"ws": self.paths["ws"]})(), {})
        self.assertTrue(ok, ev)


class Example6Formats(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, SCRIPTS)
        self.tmp = tempfile.mkdtemp(prefix="ex6fmt_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_rule_line_has_quote_and_date(self):
        # rule_recorded:rules.md 里有一行同时含原话(去空白后逐字)和一个 YYYY-MM-DD 日期
        import playbook as PB
        quote = "对比文里一定要放价格对照表"
        PB.append_rule(self.tmp, quote, [], [])
        with open(PB.rules_path(self.tmp), encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.assertTrue(any(quote in ln and re.search(r"\d{4}-\d{2}-\d{2}", ln) for ln in lines), lines)

    def test_trial_rows_have_verdict_words(self):
        # custom_check_trial_matches:同一行含页面路径和 pass / fail / ok / missing / yes / no / ✓ / ✗ / 有 / 没有 / 缺 之一
        import teach
        rows = [{"url": "http://127.0.0.1:1/platforms/weibo/", "result": "pass", "findings": []},
                {"url": "http://127.0.0.1:1/platforms/zhihu/", "result": "fail", "findings": []}]
        buf = io.StringIO()
        with redirect_stdout(buf):
            teach.print_rows("price-table", rows)
        verdict = re.compile(r"pass|fail|ok|missing|yes|no|✓|✗|有|没有|缺", re.I)
        for r in rows:
            line = next(ln for ln in buf.getvalue().splitlines() if "/platforms/" in ln and r["url"] in ln)
            self.assertRegex(line, verdict)
        self.assertIn("pass", next(ln for ln in buf.getvalue().splitlines() if "weibo" in ln))
        self.assertIn("fail", next(ln for ln in buf.getvalue().splitlines() if "zhihu" in ln))


if __name__ == "__main__":
    unittest.main()
