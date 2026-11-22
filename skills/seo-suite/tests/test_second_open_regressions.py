#!/usr/bin/env python3
"""「第二次打开」这条路上的回归(第 3 次试跑重跑后的修复;stdlib unittest,零外网,本机回环上起临时站)。

期望值的来源(不从实现反推):
- 试跑转录里被测 agent 实际做的事:第二次打开先跑 onboard status、lifecycle diagnose --ws(印「阶段:未知」)、
  ops weekly(本机站不带 --allow-local 先报错重跑一回合);自己写摘要,首屏漏了档案核对日、阶段、方案周次;
  同一天再开时 cat 旧的 agenda.md 又问了一遍档案;用户回「Nothing has changed, carry on.」后没落档;
  运营单 2.5 节在「产品变了」循环根本没跑时印「循环都查了,没事」,sitemap 里多了一个栏目也没问;
  第 6 节在 data/ 里明明有 GSC 导出时印「跳过:缺 GSC」;34 天的逐日导出、展示每天约 200,阶段门槛循环判「不到 4 次」;
  开局时用旧导出记的一条指标(来源文件已被新导出换掉)写成了当天,排在最后;
  路线项缺平台主页链接、工作区没有站点源码,被测把它们和「要不要起草」列成一串编号问题,每回合重问。
- 本轮修复清单写明的行为:ops weekly 输出最前面一块等号框住的「原样发给用户」首屏 + 给 agent 一段;
  每个循环问题带选项和照抄的 loops.py resolve 命令;问过没答的下次不重问;缺材料写陈述句、不编号不带问号、去重;
  起草类直接做;本机站点开局带过 --allow-local 的记进工作区;部分窗口超过上限算超过、没超过记未知;
  一次冲高不触发换阶段;小任务在没有远端的仓库里把推分支和开 PR 的命令当交付印出来;
  用户规则要求的产出元素在 brief 和大纲阶段就画出来。
"""
import datetime as dt
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

BLOCK_START = "===== 下面这块原样发给用户"
BLOCK_END = "===== 原样发给用户到这里为止"
TODAY = dt.datetime.now(dt.timezone.utc).date()          # onboard.py 用 UTC 日期盖确认戳
NO_AUDIT = ["--no-audit", "测试用的临时站,不跑体检"]


def d(n):
    return (TODAY + dt.timedelta(days=n)).isoformat()


def run(script, args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", GSC_SA_FILE="", HOME=cwd)
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", env=env)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


HOME_HTML = """<!doctype html><html lang="en"><head><title>Ridgeway Tea</title>
<meta name="description" content="Loose-leaf tea from small farms, shipped across the US.">
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Ridgeway Tea"}</script>
</head><body><header><nav>%s</nav></header><h1>Loose-leaf tea from small farms</h1>
<p>Buy a tin or start a monthly tea subscription from $18.</p></body></html>"""
PAGE = "<!doctype html><html lang=\"en\"><head><title>%s</title></head><body><h1>%s</h1><a href=\"/\">Home</a></body></html>"
PAGES = {"/shop/": "Shop", "/shop/green-sencha/": "Green sencha", "/shop/black-assam/": "Black assam",
         "/subscription/": "Tea subscription", "/guides/": "Brewing guides", "/guides/green-tea/": "How to brew green tea",
         "/about/": "About"}


class Site:
    """临时静态站:首页导航 + sitemap;add_section 之后 sitemap 和导航里多一个栏目。"""

    def __init__(self, t):
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="so_site_"))
        t.addCleanup(shutil.rmtree, self.root, True)
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=self.root))
        self.base = "http://127.0.0.1:%d" % self.httpd.server_address[1]
        self.pages = dict(PAGES)
        self.nav = ["/shop/", "/subscription/", "/guides/", "/about/"]
        self.write()
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        t.addCleanup(self.httpd.server_close)
        t.addCleanup(self.httpd.shutdown)

    def write(self):
        files = {"index.html": HOME_HTML % "".join('<a href="%s">%s</a>' % (p, self.pages[p]) for p in self.nav),
                 "robots.txt": "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % self.base,
                 "sitemap.xml": "<?xml version=\"1.0\"?><urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">"
                                + "".join("<url><loc>%s%s</loc></url>" % (self.base, p) for p in ["/"] + list(self.pages))
                                + "</urlset>"}
        for p, title in self.pages.items():
            files[p.strip("/") + "/index.html"] = PAGE % (title, title)
        for rel, body in files.items():
            path = os.path.join(self.root, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(body)

    def add_section(self):
        self.pages["/wholesale/"] = "Wholesale tea for cafés and offices"
        self.pages["/wholesale/apply/"] = "Apply for a wholesale account"
        self.nav.append("/wholesale/")
        self.write()


class Ws:
    """开局 6 环做完的临时站点仓库(仓库里只有 README 和 seo-ops/,没有页面源码)。"""

    def __init__(self, t, site):
        self.t, self.site = t, site
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="so_ws_"))
        t.addCleanup(shutil.rmtree, self.tmp, True)
        self.ws = os.path.join(self.tmp, "seo-ops")
        with open(os.path.join(self.tmp, "README.md"), "w", encoding="utf-8") as f:
            f.write("# Ridgeway Tea SEO\n")
        self.ok(self.ob("start", "--site", site.base, "--repo", ".", "--allow-local", "--no-wayback", "--max-pages", "8"))
        self.ok(self.ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=订阅开通",
                        "--set", "customers=美国家庭泡茶的人", "--set", "main_line=订阅", "--quote", "都对", "--confirm"))
        for r_, sets in {2: ["jargon=loose leaf"], 3: ["real_competitors=Rival Tea", "compliance=没有"],
                         4: ["capacity=每周 1 篇"], 5: ["market_first=en", "deny_topics=没有"]}.items():
            self.ok(self.ob("show", "--ring", str(r_)))
            self.ok(self.ob("answer", "--ring", str(r_), *sum((["--set", s] for s in sets), []),
                            "--quote", "第 %d 环就按这些答" % r_, *(NO_AUDIT if r_ == 4 else []), "--confirm"))
        self.ok(self.ob("show", "--ring", "6"))
        self.ok(run("plan.py", ["build", "--ws", self.ws], self.tmp))
        self.ok(self.ob("answer", "--ring", "6", "--set", "approve_plan=可以", "--quote", "可以", "--confirm"))

    def ok(self, r):
        self.t.assertIn(r.returncode, (0, 1), r.stderr + r.stdout)
        self.t.assertNotIn("Traceback", r.stderr)
        return r

    def ob(self, *a):
        return run("onboard.py", list(a), self.tmp)

    def ops(self, *a, allow_local=True):
        args = ["ops", "weekly", "--ws", self.ws, "--workers", "2"] + (["--allow-local"] if allow_local else []) + list(a)
        return run("project.py", args, self.tmp)

    def prof(self):
        with open(os.path.join(self.ws, "context", "profile.json"), encoding="utf-8") as f:
            return json.load(f)

    def write_data(self, name, text):
        os.makedirs(os.path.join(self.tmp, "data"), exist_ok=True)
        with open(os.path.join(self.tmp, "data", name), "w", encoding="utf-8") as f:
            f.write(text)


def stage_names():
    with open(os.path.join(BASE, "data", "lifecycle.json"), encoding="utf-8") as f:
        return {s["id"]: s["name"] for s in json.load(f)["stages"]}


def user_block(out):
    a = out.index(BLOCK_START)
    return out[out.index("\n", a) + 1:out.index(BLOCK_END, a)]


def agent_part(out):
    a = out.index(BLOCK_END)
    return out[a:out.index("# 每周 运营单", a)]


def daily_csv(base, days, per_day, pages=("/", "/shop/", "/guides/green-tea/"), spikes=None):
    """逐日 gsc-pages.csv:从 days 天前到昨天,每天总展示 per_day(按页均分);spikes={离今天几天: 那天的总展示}。"""
    L = ["page,date,clicks,impressions"]
    for k in range(days, 0, -1):
        day = TODAY - dt.timedelta(days=k)
        tot = (spikes or {}).get(k, per_day)
        for i, p in enumerate(pages):
            share = tot // len(pages) + (tot % len(pages) if i == 0 else 0)
            L.append("%s%s,%s,%d,%d" % (base, p, day.isoformat(), max(1, share // 100), share))
    return "\n".join(L) + "\n"


class _Shared(unittest.TestCase):
    """开局一次,各测试拷一份工作区(开局 6 环每个测试都跑会太慢)。"""

    @classmethod
    def setUpClass(cls):
        cls._cleanups = []

        class _T(unittest.TestCase):
            def runTest(self):
                pass
        cls._t = _T()
        cls.site = Site(cls._t)
        cls.tpl = Ws(cls._t, cls.site)

    @classmethod
    def tearDownClass(cls):
        cls._t.doCleanups()

    def fresh(self):
        """拷一份开局做完的工作区;站点用同一个(只读)。"""
        w = Ws.__new__(Ws)
        w.t, w.site = self, self.site
        w.tmp = os.path.realpath(tempfile.mkdtemp(prefix="so_ws_"))
        self.addCleanup(shutil.rmtree, w.tmp, True)
        shutil.rmtree(w.tmp)
        shutil.copytree(self.tpl.tmp, w.tmp)
        w.ws = os.path.join(w.tmp, "seo-ops")
        return w


# ---------------------------------------------------------------------------
# A / B:一条命令给首屏;本机站点不用再带 --allow-local;diagnose --ws 不印「未知」
# ---------------------------------------------------------------------------

class FirstScreenTests(_Shared):
    def test_ops_weekly_starts_with_user_block(self):
        w = self.fresh()
        r = w.ok(w.ops("--date", d(8)))
        self.assertTrue(r.stdout.startswith(BLOCK_START), r.stdout[:300])
        blk = user_block(r.stdout)
        names = stage_names()
        stage = names[w.prof()["stage"]["value"]]
        self.assertIn(TODAY.isoformat(), blk)                  # 档案上次核对日
        self.assertIn(stage, blk)                              # 产品阶段
        self.assertIn("第 2 周", blk)                           # 方案第几周
        self.assertIn("这周做", blk)
        self.assertIn("这周不需要你回答", blk)                    # 没有循环问题时写明
        self.assertNotRegex(blk, r"第\s*[1-6]\s*环")              # 首屏不点名开局的环
        ag = agent_part(r.stdout)
        self.assertIn("给 agent", ag)
        self.assertIn("不停", ag)

    def test_same_day_rerun_recomputes_block_and_agenda_is_archive(self):
        w = self.fresh()
        w.ok(w.ops("--date", d(8)))
        r = w.ok(w.ops("--date", d(8)))
        self.assertTrue(r.stdout.startswith(BLOCK_START))
        with open(os.path.join(w.ws, "runs", d(8), "agenda.md"), encoding="utf-8") as f:
            head = f.readline()
        self.assertIn("存档", head)
        self.assertIn("ops weekly", head)

    def test_local_site_needs_no_allow_local_after_start(self):
        w = self.fresh()
        with open(os.path.join(w.ws, "project.yaml"), encoding="utf-8") as f:
            self.assertIn("allow_local: true", f.read())
        r = w.ops("--date", d(8), allow_local=False)
        self.assertIn(r.returncode, (0, 1), r.stderr)
        self.assertNotIn("--allow-local", r.stderr)

    def test_old_workspace_without_allow_local_key_still_runs(self):
        w = self.fresh()
        p = os.path.join(w.ws, "project.yaml")
        with open(p, encoding="utf-8") as f:
            text = f.read()
        with open(p, "w", encoding="utf-8") as f:
            f.write(re.sub(r"(?m)^allow_local:.*\n", "", text))
        r = w.ops("--date", d(8), allow_local=False)
        self.assertIn(r.returncode, (0, 1), r.stderr)

    def test_onboard_status_points_to_ops_weekly(self):
        w = self.fresh()
        r = w.ok(w.ob("status", "--ws", w.ws))
        self.assertIn("ops weekly --ws", r.stdout)

    def test_diagnose_ws_reads_workspace_scan(self):
        w = self.fresh()
        r = w.ok(run("lifecycle.py", ["diagnose", "--ws", w.ws], w.tmp))
        self.assertNotIn("未知", r.stdout.splitlines()[0])

    def test_diagnose_keeps_confirmed_stage_without_scan(self):
        w = self.fresh()
        os.remove(os.path.join(w.ws, "context", "scan.json"))
        names = stage_names()
        r = w.ok(run("lifecycle.py", ["diagnose", "--ws", w.ws], w.tmp))
        self.assertIn(names[w.prof()["stage"]["value"]], r.stdout.splitlines()[0])


# ---------------------------------------------------------------------------
# F:问题带选项和照抄的 resolve;答了落档不再问;问过没答下次不重问
# ---------------------------------------------------------------------------

class ResolveTests(_Shared):
    def test_profile_review_resolve_then_not_asked_again(self):
        w = self.fresh()
        r = w.ok(w.ops("--date", d(31)))
        blk = user_block(r.stdout)
        q = [ln for ln in blk.splitlines() if re.match(r"^\d+\. ", ln)]
        self.assertEqual(len(q), 1, blk)
        self.assertIn("A. ", q[0])                              # 带选项
        m = re.search(r"(python3 \S+loops\.py resolve --ws (\S+) profile-review --quote \"<用户原话>\")", r.stdout)
        self.assertTrue(m, agent_part(r.stdout))
        self.assertEqual(shlex.split(m.group(2))[0], os.path.abspath(w.ws))
        cmd = shlex.split(m.group(1).replace("<用户原话>", "Nothing has changed, carry on.")) + ["--today", d(31)]
        rr = subprocess.run([sys.executable] + cmd[1:], cwd=w.tmp, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(rr.returncode, 0, rr.stderr)
        self.assertEqual(w.prof().get("profile_confirmed_at"), d(31))
        r2 = w.ok(w.ops("--date", d(32)))
        blk2 = user_block(r2.stdout)
        self.assertIn("这周不需要你回答", blk2)
        self.assertNotIn("没核过", blk2)

    def test_asked_but_unanswered_is_not_reasked_next_open(self):
        w = self.fresh()
        w.ok(w.ops("--date", d(31)))
        r = w.ok(w.ops("--date", d(32)))
        self.assertNotIn("没核过", user_block(r.stdout))
        ag = agent_part(r.stdout)
        self.assertIn("问过", ag)
        self.assertIn("profile-review --quote", ag)


# ---------------------------------------------------------------------------
# C:运营单里真跑「产品变了」;没跑的写「没查」
# ---------------------------------------------------------------------------

class NewSectionTests(_Shared):
    def setUp(self):
        self.site2 = Site(self)
        self.w = Ws(self, self.site2)

    def test_new_section_asked_and_resolved_with_add(self):
        w = self.w
        self.site2.add_section()
        r = w.ok(w.ops("--date", d(8)))
        blk = user_block(r.stdout)
        q = [ln for ln in blk.splitlines() if re.match(r"^\d+\. ", ln)]
        self.assertTrue(any("/wholesale/" in ln for ln in q), blk)
        self.assertIn("product-change --quote", agent_part(r.stdout))
        before = next(f["value"] for f in w.prof()["facts"] if f["key"] == "product.lines")
        w.ok(run("loops.py", ["resolve", "--ws", w.ws, "product-change", "--quote", "Yes, wholesale for cafés is new.",
                              "--add", "product.lines=Wholesale", "--today", d(8)], w.tmp))
        after = next(f["value"] for f in w.prof()["facts"] if f["key"] == "product.lines")
        self.assertEqual(after, list(before) + ["Wholesale"])
        r2 = w.ok(w.ops("--date", d(9)))
        self.assertNotIn("/wholesale/", user_block(r2.stdout))

    def test_old_workspace_falls_back_to_history_urls(self):
        w = self.w
        p = os.path.join(w.ws, "context", "scan.json")
        with open(p, encoding="utf-8") as f:
            scan = json.load(f)
        (scan.get("site_scan") or {}).pop("sections", None)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(scan, f)
        h = os.path.join(w.ws, "history", "20260101-000000")
        os.makedirs(h, exist_ok=True)
        with open(os.path.join(h, "urls.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(self.site2.base + u for u in ["/"] + list(PAGES)) + "\n")
        self.site2.add_section()
        r = w.ok(w.ops("--date", d(8)))
        self.assertIn("/wholesale/", user_block(r.stdout))

    def test_skipped_loop_is_not_reported_as_all_checked(self):
        w = self.w
        r = w.ok(w.ops("--date", d(8), "--no-net"))
        sec = r.stdout[r.stdout.index("## 2.5"):r.stdout.index("## 3.")]
        self.assertNotIn("循环都查了,没事", sec)
        self.assertIn("没查:产品变了", sec)


# ---------------------------------------------------------------------------
# D / E:4–5 周的逐日导出也判得出阶段门槛;一次冲高不提示;运营单读 data/ 的导出
# ---------------------------------------------------------------------------

class StageAndExportTests(_Shared):
    def stage_id(self, w):
        return w.prof()["stage"]["value"]

    def test_34_days_over_threshold_prompts_next_stage(self):
        w = self.fresh()
        self.assertEqual(self.stage_id(w), 2)
        w.write_data("gsc-pages.csv", daily_csv(self.site.base, 34, 200))
        with open(os.path.join(w.ws, "context", "metrics_history.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"at": d(0), "metrics": {"gsc_clicks_28d": 18, "gsc_impressions_28d": 640},
                                "source": "data/Pages_%s_%s.csv vs 前一期" % (d(-42), d(-15))}) + "\n")
        r = w.ok(w.ops("--date", d(0)))
        blk = user_block(r.stdout)
        self.assertIn("增长期", blk)
        self.assertIn("stage-threshold --quote", agent_part(r.stdout))

    def test_one_spike_inside_four_windows_does_not_prompt(self):
        w = self.fresh()
        w.write_data("gsc-pages.csv", daily_csv(self.site.base, 70, 12, spikes={23: 2400}))
        r = w.ok(w.ops("--date", d(0)))
        with open(os.path.join(w.ws, "ledger", "loops.jsonl"), encoding="utf-8") as f:
            st = [json.loads(x) for x in f if '"stage-threshold"' in x][-1]
        self.assertEqual(st["result"], "quiet", st)
        self.assertNotIn("增长期", r.stdout.split("# 每周 运营单")[0])

    def _rows(self, text):
        import lifecycle as LC
        p = os.path.join(tempfile.mkdtemp(prefix="so_csv_"), "gsc-pages.csv")
        self.addCleanup(shutil.rmtree, os.path.dirname(p), True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return LC.read_daily_pages(p)

    def test_partial_window_checkpoints_match_the_ruling(self):
        """出题人口径:数据从 34 天前起,起始日之前按 0 算;最近 4 个检查点 2600/4000/5400/5600(都 > 1000)要提示,
        只冲高一次的那组 247/380/513/2013(只有最后一个 > 1000)不提示。"""
        import lifecycle as LC
        flat = LC.weekly_checkpoints(self._rows(daily_csv("https://shop.example", 34, 200)), min_days=7)
        self.assertEqual([p["metrics"]["gsc_impressions_28d"] for p in flat[-4:]], [2600, 4000, 5400, 5600])
        spike = LC.weekly_checkpoints(self._rows(daily_csv("https://shop.example", 34, 19, spikes={6: 1500})), min_days=7)
        self.assertEqual([p["metrics"]["gsc_impressions_28d"] for p in spike[-4:]], [247, 380, 513, 2013])

    def test_ruling_spike_series_does_not_prompt(self):
        w = self.fresh()
        w.write_data("gsc-pages.csv", daily_csv(self.site.base, 34, 19, spikes={6: 1500}))
        r = w.ok(w.ops("--date", d(0)))
        with open(os.path.join(w.ws, "ledger", "loops.jsonl"), encoding="utf-8") as f:
            st = [json.loads(x) for x in f if '"stage-threshold"' in x][-1]
        self.assertEqual(st["result"], "quiet", st)
        self.assertNotIn("增长期", r.stdout.split("# 每周 运营单")[0])

    def test_young_site_over_threshold_still_prompts(self):
        """站龄 35 天、展示连续 4 周超过上限:站龄不拦提示(需求卡:展示数连续 4 周超过阶段 2 的上限 → 提示)。"""
        w = self.fresh()
        p = os.path.join(w.ws, "context", "scan.json")
        with open(p, encoding="utf-8") as f:
            scan = json.load(f)
        scan.setdefault("signals", {})["first_seen"] = d(-35)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(scan, f)
        w.write_data("gsc-pages.csv", daily_csv(self.site.base, 34, 200))
        r = w.ok(w.ops("--date", d(0)))
        self.assertIn("增长期", user_block(r.stdout))
        self.assertEqual(w.prof()["stage"]["value"], 2)          # 用户确认前档案不改

    def test_diagnose_ws_uses_data_export_and_says_what_the_prompt_follows(self):
        """diagnose 和运营单首屏用同一份数(data/ 最新导出),判定和确认的阶段不一致时写明以确认的为准、提示按 4 个检查点走。"""
        w = self.fresh()
        w.write_data("gsc-pages.csv", daily_csv(self.site.base, 34, 200))
        r = w.ok(run("lifecycle.py", ["diagnose", "--ws", w.ws, "--today", d(0)], w.tmp))
        head = r.stdout.split("## 成熟度")[0]
        self.assertIn("gsc-pages.csv 截至 %s" % d(-1), head)
        self.assertIn("产品阶段:刚上线", head)
        self.assertIn("以你确认的阶段为准", head)
        self.assertIn("最近 4 个每周检查点都超过上限才提示", head)

    def test_diagnose_rule_does_not_hold_young_site_with_impressions_at_stage_2(self):
        import lifecycle as LC
        rules = LC.load_rules()
        ev = {"signals.site_live": True, "signals.age_days": 35, "metrics.gsc_impressions_28d": 5600,
              "metrics.gsc_clicks_28d": 56}
        self.assertNotEqual(LC.stage(rules, ev, {})["stage"], 2)
        ev_low = dict(ev, **{"metrics.gsc_impressions_28d": 640})
        self.assertEqual(LC.stage(rules, ev_low, {})["stage"], 2)
        ev_none = {"signals.site_live": True, "signals.age_days": 35}
        self.assertEqual(LC.stage(rules, ev_none, {})["stage"], 2)  # 没有 GSC 时站龄照样兜底

    def test_metric_from_period_export_is_dated_by_data_end(self):
        w = self.fresh()
        w.ok(w.ob("metric", "--ws", w.ws, "--set", "gsc_impressions_28d=640", "--set", "gsc_clicks_28d=18",
                  "--source", "data/Pages_2026-10-11_2026-11-07.csv vs Pages_2026-09-13_2026-10-10.csv"))
        with open(os.path.join(w.ws, "context", "metrics_history.jsonl"), encoding="utf-8") as f:
            last = [json.loads(x) for x in f if x.strip()][-1]
        self.assertEqual(last["at"], "2026-11-07")

    def test_ops_reads_daily_export_in_data_dir(self):
        w = self.fresh()
        w.write_data("gsc-pages.csv", daily_csv(self.site.base, 34, 200))
        r = w.ok(w.ops("--date", d(0)))
        self.assertNotIn("跳过:缺 GSC", r.stdout)
        self.assertIn("Google 近 7 天", r.stdout)
        self.assertIn("data/gsc-pages.csv", r.stdout)
        self.assertNotIn("流量 × 抓取交叉:缺 GSC", r.stdout)

    def test_ops_reads_period_exports_in_data_dir(self):
        w = self.fresh()
        b = self.site.base
        w.write_data("Pages_%s_%s.csv" % (d(-56), d(-29)), "Top pages,Clicks,Impressions,CTR,Position\n%s/,2,90,2%%,20\n" % b)
        w.write_data("Pages_%s_%s.csv" % (d(-28), d(-1)),
                     "Top pages,Clicks,Impressions,CTR,Position\n%s/,6,210,2.86%%,18.4\n%s/shop/,3,120,2.5%%,25\n" % (b, b))
        r = w.ok(w.ops("--date", d(0)))
        self.assertNotIn("跳过:缺 GSC", r.stdout)


# ---------------------------------------------------------------------------
# G:缺材料写陈述句、不编号不带问号、去重;缺了做不了的路线项先跳过;运营单末尾的固定指引
# ---------------------------------------------------------------------------

class MaterialsTests(_Shared):
    def test_plan_items_carry_needs(self):
        with open(os.path.join(self.tpl.ws, "plan", "plan.json"), encoding="utf-8") as f:
            plan = json.load(f)
        ent = [it for it in plan["items"] if it["id"] == "entity-profiles"]
        self.assertTrue(ent)
        self.assertIn("entity.profiles", ent[0].get("needs") or [])

    def test_missing_links_listed_as_statements_and_item_skipped(self):
        w = self.fresh()
        with open(os.path.join(w.ws, "plan", "plan.json"), encoding="utf-8") as f:
            plan = json.load(f)
        wk1 = [it for it in plan["items"] if (it.get("weeks") or [99])[0] <= 1]
        self.assertTrue(any(it["id"] == "entity-profiles" for it in wk1))
        r = w.ok(w.ops("--date", d(1)))
        blk = user_block(r.stdout)
        self.assertIn("待你补的材料", blk)
        mats = blk[blk.index("待你补的材料"):].split("\n\n")[0].splitlines()[1:]
        self.assertTrue(any("主页链接" in m for m in mats), blk)
        for m in mats:
            self.assertTrue(m.startswith("- "), m)               # 陈述句清单,不编号
            self.assertNotIn("?", m)
            self.assertNotIn("?", m)
        todo = [ln for ln in blk.splitlines() if ln.startswith("- 这周做")][0]
        self.assertNotIn("实体档案", todo)                        # 缺主页链接的那项先放着,做下一件能做的
        q = [ln for ln in blk.splitlines() if re.match(r"^\d+\. ", ln)]
        self.assertEqual(q, [])
        r2 = w.ok(w.ops("--date", d(2)))
        self.assertNotIn("待你补的材料", user_block(r2.stdout))    # 同一项不再列
        self.assertIn("已经列过", agent_part(r2.stdout))

    def test_agenda_ends_with_fixed_guidance(self):
        w = self.fresh()
        r = w.ok(w.ops("--date", d(8)))
        tail = r.stdout[r.stdout.index("## 8. 做完运营单以后"):]
        self.assertIn("起草类直接做", tail)
        self.assertIn("改动稿", tail)                             # 工作区里没有站点源码
        self.assertIn("carry on", tail)


# ---------------------------------------------------------------------------
# 出题人裁定后仍要做到的:小任务没远端时印推送命令;规则要求的元素在 brief 阶段画出来
# ---------------------------------------------------------------------------

class SmallTaskTests(unittest.TestCase):
    def test_pr_suggestion_prints_push_when_repo_has_no_remote(self):
        import fix_plan
        repo = os.path.realpath(tempfile.mkdtemp(prefix="so_repo_"))
        self.addCleanup(shutil.rmtree, repo, True)
        subprocess.run(["git", "init", "-q", repo], check=True)
        cwd = os.getcwd()
        os.chdir(repo)
        self.addCleanup(os.chdir, cwd)
        view = {"url": "https://shop.example/", "verdict": "fix"}
        pr = fix_plan.pr_suggestion(view, [{"category": "title", "description": "改标题"}], None,
                                    {"branch": "seo/title-fix", "original": "main", "commit": "abc", "files": []})
        self.assertIn("git push -u origin seo/title-fix", pr.get("push") or "")
        self.assertIn("git remote add origin", pr.get("push") or "")

    def test_playbook_context_asks_to_draw_required_elements(self):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="so_pb_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        os.makedirs(os.path.join(tmp, "seo-ops"))
        with open(os.path.join(tmp, "seo-ops", "project.yaml"), "w", encoding="utf-8") as f:
            f.write("site: https://shop.example\n")
        r = run("teach.py", ["rule", "add", "--quote", "以后我们的对比文都要放一张价格对照表", "--no-deny",
                             "--applies", "brief,plan", "--ws", os.path.join(tmp, "seo-ops")], tmp)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        r = run("playbook.py", ["context", "--ws", os.path.join(tmp, "seo-ops")], tmp)
        self.assertIn("表头", r.stdout)

    def test_skill_md_startup_protocol_names_the_new_rules(self):
        with open(os.path.join(BASE, "SKILL.md"), encoding="utf-8") as f:
            text = f.read()
        proto = text[text.index("## 启动协议"):text.index("## 使用原则")]
        self.assertIn("ops weekly", proto)
        self.assertIn("loops.py resolve", proto)
        self.assertIn("carry on", proto.split("2. **有**")[1])
        self.assertIn("git push", proto)


if __name__ == "__main__":
    unittest.main()
