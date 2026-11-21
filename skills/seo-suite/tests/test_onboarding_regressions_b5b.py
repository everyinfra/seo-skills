#!/usr/bin/env python3
"""开局流程第 5 批修复后第 2 次试跑记下的回归,逐条单测(stdlib unittest,零外网;本机回环上起临时站)。

期望值的来源(不从实现反推):
- 试跑转录里被测 agent 跑过的原命令:在 skill 目录里跑 start --repo <别处> --allow-local、之后 show / metric 不带 --ws;
  project.py run triage --site <URL> --allow-local;answer --ring 4 不带 --confirm 记了大半答案;
  站点已上线的改版场景整场没跑体检就确认了第 4 环;
- 试跑里页面原文和屏幕原文:「Free US shipping on orders over $40」被写成免费档;「收费方式(页面原文):unknown」;
  产品线来自 brief.md 却写「产品线是我按网址推的」;metric 之后 agent 自己改写整块、丢了「**开局第 1 环 · …**」标题;
- 本轮修复清单写明的行为:工作区默认 <repo>/seo-ops、不许落在 skill 安装目录、当前目录没有工作区就报错不新建;
  run triage 接受 --site / --ws;第 4 环「agent 先做」打印完整体检命令;只答了一部分时脚本把没答的题原样再打一遍;
  站点已上线时确认第 4 环要有体检记录(改版阶段另要基线),逃生口 --no-audit 的原因进档案、屏幕和方案。
"""
import functools
import http.server
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)
import product_scan  # noqa: E402

BLOCK_START = "===== 下面这块原样发给用户"
BLOCK_END = "===== 原样发给用户到这里为止"
QLINE = re.compile(r"^(\d+)\. ")


def run(script, args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", env=env)


def skill_files():
    """skill 目录下的文件清单(不含 __pycache__:跑脚本时解释器自己会写字节码)。"""
    out = set()
    for d, dirs, files in os.walk(BASE):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        out |= {os.path.relpath(os.path.join(d, f), BASE) for f in files}
    return out


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


HOME = """<!doctype html><html lang="en"><head><title>Northbrew Coffee</title>
<meta name="description" content="Small-batch coffee roasted in Maine and shipped across the US within 48 hours.">
</head><body><h1>Small-batch coffee, shipped fresh</h1>
<p>Buy a bag or start a monthly subscription from $22. Free US shipping on orders over $40.</p>
<a href="/shop/">Shop</a> <a href="/about/">About</a></body></html>"""
PAGE = "<!doctype html><html lang=\"en\"><head><title>%s</title></head><body><h1>%s</h1><a href=\"/\">Home</a></body></html>"


def make_site(t, home=HOME):
    """临时站:首页 + 两个子页 + robots + sitemap,挂在 127.0.0.1 的随机端口上。"""
    root = os.path.realpath(tempfile.mkdtemp(prefix="b5b_site_"))
    t.addCleanup(shutil.rmtree, root, True)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=root))
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    files = {"index.html": home, "shop/index.html": PAGE % ("Shop", "Shop"),
             "about/index.html": PAGE % ("About", "About us"),
             "robots.txt": "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % base,
             "sitemap.xml": "<?xml version=\"1.0\"?><urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
                            + "".join("<url><loc>%s%s</loc></url>" % (base, p) for p in ("/", "/shop/", "/about/"))
                            + "</urlset>"}
    for rel, body in files.items():
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    t.addCleanup(httpd.server_close)
    t.addCleanup(httpd.shutdown)
    return base


def base_scan(lines=("Invoicing", "Time tracking", "Client portal"), pricing=None):
    facts = [{"key": "product.name", "value": "Acme", "source": "https://acme.example/", "kind": "fact"},
             {"key": "product.one_liner", "value": "Invoices for freelancers", "source": "https://acme.example/",
              "kind": "fact"},
             {"key": "market.languages", "value": ["en"], "source": "https://acme.example/", "kind": "fact"}]
    if lines is not None:
        facts.append({"key": "product.lines", "value": list(lines), "source": "https://acme.example/sitemap.xml",
                      "kind": "inferred"})
    if pricing is not None:
        facts.append(pricing)
    sig = {"site_live": True, "robots_block_all": False, "homepage_noindex": False, "url_count": 120,
           "first_seen": "2024-03-01", "has_llms_txt": True}
    return {"schema": 1, "site": "https://acme.example", "signals": sig,
            "site_scan": {"page_types": {"pricing": 1, "blog": 10}}, "facts": facts, "errors": []}


class Ws:
    """一个临时站点仓库;cwd 默认就是仓库根。"""

    def __init__(self, t, scan=None, site=None):
        self.t = t
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="obb5b_"))
        t.addCleanup(shutil.rmtree, self.tmp, True)
        self.ws = os.path.join(self.tmp, "seo-ops")
        if site:
            self.site = site
            self.start = self.ok(self.ob("start", "--site", site, "--repo", ".", "--allow-local", "--no-wayback",
                                         "--max-pages", "5"))
        else:
            self.site = "https://acme.example"
            with open(os.path.join(self.tmp, "scan.json"), "w", encoding="utf-8") as f:
                json.dump(scan or base_scan(), f, ensure_ascii=False)
            self.start = self.ok(self.ob("start", "--site", self.site, "--scan", "scan.json"))

    def ok(self, r):
        self.t.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.t.assertNotIn("Traceback", r.stderr)
        return r

    def ob(self, *a, cwd=None):
        return run("onboard.py", list(a), cwd or self.tmp)

    def prof(self):
        with open(os.path.join(self.ws, "context", "profile.json"), encoding="utf-8") as f:
            return json.load(f)

    def ring1(self, *extra):
        return self.ok(self.ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册",
                               "--set", "customers=自由职业设计师", "--set", "main_line=Invoicing", *extra,
                               "--quote", "都对,要注册,客户是自由职业设计师,先做 Invoicing", "--confirm"))

    def to_ring4(self, *ring1_extra):
        self.ring1(*ring1_extra)
        for r_, sets in {2: ["jargon=开票"], 3: ["real_competitors=Rival", "compliance=没有"]}.items():
            self.ok(self.ob("show", "--ring", str(r_)))
            self.ok(self.ob("answer", "--ring", str(r_), *sum((["--set", s] for s in sets), []),
                            "--quote", "第 %d 环的回答是 %s" % (r_, ";".join(sets)), "--confirm"))
        return self.ok(self.ob("show", "--ring", "4")).stdout


def user_block(screen):
    a = screen.index(BLOCK_START)
    return screen[screen.index("\n", a) + 1:screen.index(BLOCK_END, a)]


def qlines(text):
    return [ln for ln in text.splitlines() if QLINE.match(ln)]


def has_choice(ln):
    return bool(re.search(r"\bA\. ", ln) or "我猜:" in ln)


# ---------------------------------------------------------------------------
# A. 工作区写错目录
# ---------------------------------------------------------------------------

class WorkspaceLocationTests(unittest.TestCase):
    def test_start_in_skill_dir_with_repo_elsewhere_lands_in_repo(self):
        """转录原命令:先 cd 到 skill 目录,再 start --site <本机站> --repo <站点仓库绝对路径> --allow-local。"""
        site = make_site(self)
        repo = os.path.realpath(tempfile.mkdtemp(prefix="b5b_repo_"))
        self.addCleanup(shutil.rmtree, repo, True)
        before = skill_files()
        r = run("onboard.py", ["start", "--site", site, "--repo", repo, "--allow-local", "--no-wayback",
                               "--max-pages", "5"], BASE)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        ws = os.path.join(repo, "seo-ops")
        self.assertTrue(os.path.isfile(os.path.join(ws, "context", "profile.json")))
        self.assertFalse(os.path.exists(os.path.join(BASE, "seo-ops")))
        self.assertEqual(skill_files() - before, set(), "skill 目录里多出了文件")
        first = r.stdout.splitlines()[0]
        self.assertIn("工作区:" + ws, first)
        self.assertIn("--ws", first)
        self.assertIn(BLOCK_START, r.stdout)
        # 屏幕上教的 answer 命令带着工作区绝对路径:在 skill 目录里照抄也写对地方
        self.assertIn("--ws %s" % shlex.quote(ws), r.stdout)

        # 之后在 skill 目录里不带 --ws 跑 show / metric:退出码 2、什么都不写、给照抄命令
        for args in (["show"], ["metric", "--set", "gsc_clicks_28d=10", "--source", "x.csv"], ["status"]):
            res = run("onboard.py", args, BASE)
            self.assertEqual(res.returncode, 2, args)
            self.assertIn("seo-suite 自己的安装目录", res.stderr)
            self.assertIn("cd <站点仓库> && python3 %s" % os.path.join(SCRIPTS, "onboard.py"), res.stderr)
            self.assertIn("--ws <站点仓库>/seo-ops", res.stderr)
        self.assertEqual(skill_files() - before, set())
        ok = run("onboard.py", ["show", "--ws", ws], BASE)
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_explicit_ws_inside_skill_dir_refused_nothing_written(self):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="b5b_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        with open(os.path.join(tmp, "scan.json"), "w", encoding="utf-8") as f:
            json.dump(base_scan(), f)
        before = skill_files()
        r = run("onboard.py", ["start", "--site", "https://acme.example", "--scan", "scan.json",
                               "--ws", os.path.join(BASE, "seo-ops")], tmp)
        self.assertEqual(r.returncode, 2)
        self.assertIn("这次什么都没写", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(BASE, "seo-ops")))
        self.assertEqual(skill_files() - before, set())
        for script, args in (("project.py", ["init", "--site", "https://acme.example", "--dir",
                                             os.path.join(BASE, "seo-ops")]),
                             ("plan.py", ["build", "--ws", os.path.join(BASE, "seo-ops")])):
            res = run(script, args, tmp)
            self.assertEqual(res.returncode, 2, script + res.stderr)
            self.assertIn("seo-suite 自己的安装目录", res.stderr)
        self.assertFalse(os.path.exists(os.path.join(BASE, "seo-ops")))

    def test_no_workspace_in_cwd_says_so_and_creates_nothing(self):
        empty = os.path.realpath(tempfile.mkdtemp(prefix="b5b_empty_"))
        self.addCleanup(shutil.rmtree, empty, True)
        cases = [("onboard.py", ["show"]), ("onboard.py", ["status"]),
                 ("onboard.py", ["note", "--ring", "1", "--key", "product.name", "--value", "X", "--source", "a.md"]),
                 ("onboard.py", ["answer", "--ring", "1", "--set", "conversion=注册", "--quote", "要的是注册这个结果"]),
                 ("onboard.py", ["metric", "--set", "gsc_clicks_28d=1", "--source", "x.csv"]),
                 ("plan.py", ["build"]), ("loops.py", ["status"]),
                 ("site_move.py", ["baseline", "--site", "http://127.0.0.1:9"]),
                 ("project.py", ["run", "triage"])]
        for script, args in cases:
            r = run(script, args, empty)
            self.assertEqual(r.returncode, 2, "%s %s:%s" % (script, args, r.stderr))
            self.assertIn("下没有工作区", r.stderr, script)
            self.assertIn("--ws" if script != "project.py" else "--dir", r.stderr, script)
            self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(os.listdir(empty), [], "当前目录里不该新建任何东西")

    def test_subdir_hint_points_to_workspace_above(self):
        w = Ws(self)
        sub = os.path.join(w.tmp, "src", "pages")
        os.makedirs(sub)
        r = w.ob("show", cwd=sub)
        self.assertEqual(r.returncode, 2)
        self.assertIn("上级目录里有工作区", r.stderr)
        self.assertIn("--ws %s" % w.ws, r.stderr)
        self.assertFalse(os.path.exists(os.path.join(sub, "seo-ops")))


# ---------------------------------------------------------------------------
# B. run triage --site / --ws;第 4 环打印完整体检命令
# ---------------------------------------------------------------------------

class TriageCommandTests(unittest.TestCase):
    def test_run_triage_accepts_site_and_ws(self):
        site = make_site(self)
        w = Ws(self, site=site)
        r = run("project.py", ["run", "triage", "--site", site, "--allow-local", "--ws", w.ws, "--max", "5"], w.tmp)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        self.assertNotIn("unrecognized arguments", r.stderr)
        # 转录原命令(在仓库根、不带 --dir)
        r = run("project.py", ["run", "triage", "--site", site, "--allow-local", "--max", "5"], w.tmp)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        bad = run("project.py", ["run", "triage", "--site", "https://other.example", "--ws", w.ws], w.tmp)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("工作区", bad.stderr)
        self.assertIn(site, bad.stderr)

    def test_ring4_screen_prints_copyable_triage_command(self):
        site = make_site(self)
        w = Ws(self, site=site)
        screen = w.to_ring4()
        line = next(ln for ln in screen.splitlines() if ln.startswith("- 体检"))
        cmd = line.split(":", 1)[1]
        argv = shlex.split(cmd)
        self.assertEqual(argv[1], os.path.join(SCRIPTS, "project.py"))
        self.assertEqual(argv[2:4], ["run", "triage"])
        self.assertEqual(argv[argv.index("--dir") + 1], w.ws)
        self.assertIn("--allow-local", argv)
        r = subprocess.run([sys.executable] + argv[1:] + ["--max", "5"], cwd="/", capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        again = w.ok(w.ob("show", "--ring", "4")).stdout
        self.assertRegex(again, r"现在:已有体检记录 history/")


# ---------------------------------------------------------------------------
# C. 只答了一部分:没答的题原样再打一遍,已答的题不追问
# ---------------------------------------------------------------------------

class PartialAnswerTests(unittest.TestCase):
    def test_unanswered_questions_reprinted_with_same_numbers_and_options(self):
        w = Ws(self)
        screen = w.to_ring4()
        shown = {QLINE.match(ln).group(1): ln for ln in qlines(user_block(screen))}
        r = w.ok(w.ob("answer", "--ring", "4", "--set", "capacity=两个人,每周一篇", "--set", "history=没有处罚、没买过链接",
                      "--quote", "Two of us, one brew guide a week. No penalties, no bought links."))
        out = r.stdout
        self.assertIn("已记答案", out)
        self.assertIn("第 1 题(capacity)", out)
        block = user_block(out)
        lines = qlines(block)
        self.assertEqual([QLINE.match(ln).group(1) for ln in lines], ["3", "4"])
        for ln in lines:
            self.assertEqual(ln, shown[QLINE.match(ln).group(1)], "没答的题要原样(编号、选项、猜测不变)")
            self.assertTrue(has_choice(ln), ln)
        self.assertIn("不追问", out)
        self.assertIn("--unknown", out)
        self.assertEqual(w.prof()["rings"]["4"]["status"], "asking")

    def test_all_answered_prints_confirm_command(self):
        w = Ws(self)
        w.to_ring4()
        quote = "Two of us, weekly. No penalties. Nobody signs off. GA4 and GSC are set up."
        r = w.ok(w.ob("answer", "--ring", "4", "--set", "capacity=两个人,每周一篇", "--set", "history=没有",
                      "--set", "team_budget=没有预算(谁拍板:未说)", "--set", "access=都有", "--quote", quote))
        self.assertNotIn(BLOCK_START, r.stdout)
        self.assertIn("未说", r.stdout)
        cmd = next(ln.strip() for ln in r.stdout.splitlines() if "--confirm" in ln and "answer --ring 4" in ln)
        argv = shlex.split(cmd)
        self.assertEqual(argv[argv.index("--quote") + 1], quote)
        self.assertEqual(argv[argv.index("--ws") + 1], w.ws)

    def test_ring4_partial_screen_has_no_invented_questions(self):
        """被测自己编的追问(「开发每周能投几个小时」「谁拍板」)不在脚本打的块里:块里只有问题库里没答的题。"""
        w = Ws(self)
        w.to_ring4()
        r = w.ok(w.ob("answer", "--ring", "4", "--set", "capacity=两个人", "--quote", "Two of us, one guide a week."))
        self.assertEqual(len(qlines(user_block(r.stdout))), 3)


# ---------------------------------------------------------------------------
# D. 站点已上线:第 4 环确认前要有体检记录(改版另要基线);--no-audit 逃生口
# ---------------------------------------------------------------------------

class AuditGateTests(unittest.TestCase):
    def test_live_site_ring4_confirm_needs_triage(self):
        site = make_site(self)
        w = Ws(self, site=site)
        w.to_ring4()
        quote = "Two of us, one brew guide a week, no penalties"
        r = w.ob("answer", "--ring", "4", "--set", "capacity=两个人", "--quote", quote, "--confirm")
        self.assertEqual(r.returncode, 2)
        self.assertIn("run triage --dir %s --allow-local" % w.ws, r.stderr)
        self.assertEqual(w.prof()["rings"]["4"]["status"], "asking")
        self.assertEqual(w.prof()["rings"]["4"]["answers"].get("capacity"), "两个人", "答案照样存下")
        tri = next(ln for ln in r.stderr.splitlines() if "run triage" in ln).strip()
        self.assertTrue(tri.startswith("python3 "), tri)
        t = subprocess.run([sys.executable] + shlex.split(tri, comments=True)[1:] + ["--max", "5"],
                           capture_output=True, text=True)
        self.assertIn(t.returncode, (0, 1), t.stderr)
        again = next(ln for ln in r.stderr.splitlines() if "--confirm" in ln).strip()
        ok = subprocess.run([sys.executable] + shlex.split(again)[1:], capture_output=True, text=True, cwd="/")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        p = w.prof()
        self.assertEqual(p["rings"]["4"]["status"], "confirmed")
        self.assertTrue(p["audit"]["ran"])

    def test_change_stage_also_needs_baseline(self):
        site = make_site(self)
        w = Ws(self, site=site)
        w.to_ring4("--correct", "stage=5")
        screen = w.ok(w.ob("show", "--ring", "4")).stdout
        base_line = next(ln for ln in screen.splitlines() if ln.startswith("- 改版前存基线"))
        tri_line = next(ln for ln in screen.splitlines() if ln.startswith("- 体检"))
        t = subprocess.run([sys.executable] + shlex.split(tri_line.split(":", 1)[1])[1:] + ["--max", "5"],
                           capture_output=True, text=True)
        self.assertIn(t.returncode, (0, 1), t.stderr)
        r = w.ob("answer", "--ring", "4", "--set", "capacity=三个人", "--quote", "Three people on the site", "--confirm")
        self.assertEqual(r.returncode, 2)
        self.assertIn("site_move.py baseline --site %s --ws %s --allow-local" % (site, w.ws), r.stderr)
        b = subprocess.run([sys.executable] + shlex.split(base_line.split(":", 1)[1])[1:], capture_output=True,
                           text=True, cwd="/")
        self.assertEqual(b.returncode, 0, b.stderr)
        self.assertTrue(os.listdir(os.path.join(w.ws, "baselines")))
        w.ok(w.ob("answer", "--ring", "4", "--quote", "Three people on the site", "--confirm"))

    def test_no_audit_reason_recorded_and_shown(self):
        w = Ws(self)
        w.to_ring4()
        r = w.ob("answer", "--ring", "4", "--set", "capacity=每月 4 篇", "--quote", "每月 4 篇内容", "--confirm")
        self.assertEqual(r.returncode, 2)
        w.ok(w.ob("answer", "--ring", "4", "--quote", "每月 4 篇内容", "--no-audit", "站点要登录才能打开", "--confirm"))
        p = w.prof()
        self.assertEqual(p["audit"]["ran"], False)
        self.assertEqual(p["audit"]["reason"], "站点要登录才能打开")
        self.assertEqual(p["audit"]["status"], "unconfirmed")
        self.assertIn("体检没跑:站点要登录才能打开", w.ok(w.ob("status")).stdout)
        self.assertIn("体检没跑:站点要登录才能打开", user_block(w.ok(w.ob("show", "--ring", "5")).stdout))
        w.ok(w.ob("answer", "--ring", "5", "--set", "market_first=en", "--set", "deny_topics=没有",
                  "--quote", "先做英文市场,没有不做的", "--confirm"))
        b = run("plan.py", ["build", "--ws", w.ws], w.tmp)
        self.assertEqual(b.returncode, 0, b.stderr)
        self.assertIn("体检没跑:站点要登录才能打开", b.stdout)
        for fn in ("plan.md", "strategy-book.zh.md"):
            with open(os.path.join(w.ws, "plan", fn), encoding="utf-8") as f:
                self.assertIn("体检没跑:站点要登录才能打开", f.read(), fn)

    def test_idea_stage_not_gated(self):
        scan = base_scan()
        scan["signals"]["site_live"] = False
        w = Ws(self, scan)
        w.to_ring4("--correct", "stage=0")
        screen = w.ok(w.ob("show", "--ring", "4")).stdout
        self.assertNotIn("run triage", screen)
        w.ok(w.ob("answer", "--ring", "4", "--set", "capacity=一个人", "--quote", "就我一个人,每周一篇", "--confirm"))


# ---------------------------------------------------------------------------
# E. 第 1 环的整块重打、产品线出处、收费方式没读到、免运费不算免费档
# ---------------------------------------------------------------------------

class Ring1WordingTests(unittest.TestCase):
    def test_metric_reprints_whole_block_with_title(self):
        w = Ws(self)
        r = w.ok(w.ob("metric", "--set", "gsc_clicks_28d=18", "--set", "gsc_clicks_prev_28d=0",
                      "--set", "gsc_impressions_28d=640", "--source", "data/Pages.csv"))
        self.assertIn("上一版作废,贴这一版", r.stdout)
        block = user_block(r.stdout)
        self.assertIn("**开局第 1 环 · 产品是什么**", block)
        self.assertIn("## 问用户", block)
        self.assertIn(BLOCK_END, r.stdout)

    def test_note_reprints_block_and_names_real_source(self):
        w = Ws(self, base_scan(lines=None))
        r = w.ok(w.ob("note", "--ring", "1", "--key", "product.lines", "--value", "健康提醒;病历档案;医院比价",
                      "--source", "brief.md"))
        self.assertIn("上一版作废,贴这一版", r.stdout)
        q1 = qlines(user_block(r.stdout))[0]
        self.assertIn("产品线是我从 brief.md 读的", q1)
        self.assertNotIn("按网址推的", q1)

    def test_url_inferred_lines_still_say_by_url(self):
        w = Ws(self)
        q1 = qlines(user_block(w.start.stdout))[0]
        self.assertIn("按网址推的", q1)

    def test_pricing_unknown_not_shown_raw(self):
        scan = base_scan(pricing={"key": "pricing.model", "value": "unknown", "source": "https://acme.example/",
                                  "kind": "inferred", "enum": "unknown"})
        w = Ws(self, scan)
        block = user_block(w.start.stdout)
        self.assertNotRegex(block, r"收费方式[^\n]*:unknown")
        self.assertIn("收费方式(页面原文):没读到", block)
        self.assertIn("没读到收费方式", qlines(block)[0])

    def test_product_scan_no_prices_leaves_pricing_unread(self):
        site = make_site(self, home=PAGE % ("Trail Guides", "Trail guides and gear reviews"))
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="b5b_scan_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        out = os.path.join(tmp, "scan.json")
        r = run("product_scan.py", ["--site", site, "--allow-local", "--no-wayback", "--max-pages", "3",
                                    "--out", out], tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(out, encoding="utf-8") as f:
            f_ = next(x for x in json.load(f)["facts"] if x["key"] == "pricing.model")
        self.assertIsNone(f_["value"])
        self.assertEqual(f_["kind"], "unknown")

    def test_free_shipping_is_not_free_tier(self):
        text = "Buy a bag, start a monthly subscription from $22, or pick up a pour-over kit. " \
               "Free US shipping on orders over $40."
        modes = product_scan.billing_modes(text)
        self.assertIn("订阅", modes)
        self.assertNotIn("免费档 / 免费额度", modes)
        for t in ("Free shipping on all orders", "免运费", "全场包邮", "免费配送", "Free returns within 30 days",
                  "Envío gratis en pedidos de más de 40 €"):
            self.assertNotIn("免费档 / 免费额度", product_scan.billing_modes(t), t)
        self.assertIn("免费档 / 免费额度", product_scan.billing_modes("Free plan with 100 free requests a month"))

    def test_free_shipping_site_scan_billing(self):
        site = make_site(self)
        w = Ws(self, site=site)
        line = next(ln for ln in user_block(w.start.stdout).splitlines() if ln.startswith("- 收费方式"))
        self.assertNotIn("免费档", line)


if __name__ == "__main__":
    unittest.main()
