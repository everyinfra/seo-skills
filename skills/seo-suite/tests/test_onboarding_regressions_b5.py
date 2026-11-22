#!/usr/bin/env python3
"""开局流程第 5 批第 2 轮试跑记下的回归,逐条单测(stdlib unittest,零外网)。

期望值的来源(不从实现反推):
- 试跑转录里被测 agent 跑过的原命令和原参数:note 记产品线用的「健康提醒;病历档案;医院比价」、
  --correct 补产品线用的「Gear reviews|Trail guides|Trailmark Pro」、补价格用的
  「Monthly subscription;Single-origin bags (one-off);Pour-over kits and gear」、禁用项
  「Don't touch the pricing page copy (/pricing/, /de/pricing/)」、第 5 环市场回答「中国大陆、简体中文」;
- 本轮修复清单写明的行为:列表按屏幕教的分隔符拆、禁用项一句话不拆;每个问题同一行带选项或猜测;
  用户确认的阶段重算不改回;档案顶层 _schema 映射不算手改;本机站没加 --allow-local 直接报错、什么都不写,
  加了重跑会重新读;仓库里摆着改版计划按「改版」猜;上线前预览站 robots 全封不挡体检、记成一条发现;
  只给仓库时也读出定价和语言;单一市场的方案不提 hreflang。
"""
import functools
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
# 扫描文件造的站没有真站可体检:第 4 环走逃生口(站点已上线时确认第 4 环要体检记录)
NO_AUDIT = ["--no-audit", "测试用扫描文件造的站,没有真站可体检"]

with open(os.path.join(BASE, "data", "lifecycle.json"), encoding="utf-8") as _f:
    STAGE_NAMES = {s["id"]: s["name"] for s in json.load(_f)["stages"]}

BLOCK_START = "===== 下面这块原样发给用户"
BLOCK_END = "===== 原样发给用户到这里为止"


def run(script, args, cwd):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8", env=env)


def base_scan(lines=("Invoicing", "Time tracking", "Client portal")):
    facts = [{"key": "product.name", "value": "Acme", "source": "https://acme.example/", "kind": "fact"},
             {"key": "product.one_liner", "value": "Invoices for freelancers", "source": "https://acme.example/",
              "kind": "fact"},
             {"key": "conversion.ctas", "value": ["注册"], "source": "https://acme.example/", "kind": "inferred"},
             {"key": "market.languages", "value": ["en"], "source": "https://acme.example/", "kind": "fact"}]
    if lines is not None:
        facts.append({"key": "product.lines", "value": list(lines), "source": "https://acme.example/llms.txt",
                      "kind": "fact"})
    sig = {"site_live": True, "robots_block_all": False, "homepage_noindex": False, "url_count": 120,
           "first_seen": "2024-03-01", "has_llms_txt": True}
    return {"schema": 1, "site": "https://acme.example", "signals": sig,
            "site_scan": {"page_types": {"pricing": 1, "blog": 10}}, "facts": facts, "errors": []}


class Ws:
    def __init__(self, t, scan=None):
        self.t = t
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="obb5_"))
        t.addCleanup(shutil.rmtree, self.tmp, True)
        self.ws = os.path.join(self.tmp, "seo-ops")
        self.write_scan(scan or base_scan())
        self.start = self.ok(self.ob("start", "--site", "https://acme.example", "--scan", "scan.json"))

    def write_scan(self, scan):
        with open(os.path.join(self.tmp, "scan.json"), "w", encoding="utf-8") as f:
            json.dump(scan, f, ensure_ascii=False)

    def ok(self, r):
        self.t.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.t.assertNotIn("Traceback", r.stderr)
        return r

    def ob(self, *a):
        return run("onboard.py", list(a), self.tmp)

    def prof(self):
        with open(os.path.join(self.ws, "context", "profile.json"), encoding="utf-8") as f:
            return json.load(f)

    def fact(self, key):
        return next((f.get("value") for f in self.prof()["facts"] if f["key"] == key), None)

    def ring1(self, *extra):
        return self.ok(self.ob("answer", "--ring", "1", "--set", "profile_ok=都对", "--set", "conversion=注册",
                               "--set", "customers=自由职业设计师", "--set", "main_line=Invoicing", *extra,
                               "--quote", "都对,要注册,客户是自由职业设计师,先做 Invoicing", "--confirm"))

    def rest(self, market="en", deny="没有"):
        answers = {2: ["jargon=开票"], 3: ["real_competitors=Rival", "compliance=没有"], 4: ["capacity=每月 4 篇"],
                   5: ["market_first=%s" % market, "deny_topics=%s" % deny]}
        for r_, sets in answers.items():
            self.ok(self.ob("show", "--ring", str(r_)))
            self.ok(self.ob("answer", "--ring", str(r_), *sum((["--set", s] for s in sets), []),
                            "--quote", "第 %d 环的回答是 %s" % (r_, ";".join(sets)), *(NO_AUDIT if r_ == 4 else []),
                            "--confirm"))
        self.ok(self.ob("show", "--ring", "6"))


def user_block(screen):
    a = screen.index(BLOCK_START)
    return screen[screen.index("\n", a) + 1:screen.index(BLOCK_END, a)]


QLINE = re.compile(r"^\s*\d+[.、]")


# ---------------------------------------------------------------------------
# #3 列表按屏幕教的分隔符拆;禁用项一句话不拆
# ---------------------------------------------------------------------------

class ListSplitTests(unittest.TestCase):
    def test_screen_teaches_separator(self):
        w = Ws(self)
        self.assertRegex(w.start.stdout, r"列表项用「;」")

    def test_note_value_with_semicolons_is_a_list(self):
        w = Ws(self, base_scan(lines=None))
        w.ok(w.ob("note", "--ring", "1", "--key", "product.lines", "--value", "健康提醒;病历档案;医院比价",
                  "--source", "brief.md"))
        self.assertEqual(w.fact("product.lines"), ["健康提醒", "病历档案", "医院比价"])

    def test_correct_with_pipes_is_a_list(self):
        w = Ws(self, base_scan(lines=None))
        w.ring1("--correct", "product.lines=Gear reviews|Trail guides|Trailmark Pro")
        self.assertEqual(w.fact("product.lines"), ["Gear reviews", "Trail guides", "Trailmark Pro"])

    def test_parentheses_kept_inside_one_item(self):
        w = Ws(self, base_scan(lines=None))
        w.ring1("--correct", "product.lines=Monthly subscription;Single-origin bags (one-off);Pour-over kits and gear")
        self.assertEqual(w.fact("product.lines"),
                         ["Monthly subscription", "Single-origin bags (one-off)", "Pour-over kits and gear"])

    def test_deny_sentence_with_commas_not_split(self):
        w = Ws(self)
        w.ring1()
        w.rest(deny="Don't touch the pricing page copy (/pricing/, /de/pricing/)")
        self.assertEqual([d["item"] for d in w.prof()["deny"]],
                         ["Don't touch the pricing page copy (/pricing/, /de/pricing/)"])


# ---------------------------------------------------------------------------
# #4 每个问题同一行带选项或猜测;禁用项问题有 A、B 两个选项
# ---------------------------------------------------------------------------

def has_choice(line):
    return ("我猜" in line) or (re.search(r"\bA\.", line) and re.search(r"\bB\.", line))


class QuestionChoiceTests(unittest.TestCase):
    def check(self, screen):
        qs = [ln for ln in user_block(screen).splitlines() if QLINE.match(ln)]
        self.assertTrue(qs, screen)
        for ln in qs:
            self.assertTrue(has_choice(ln), "问题行没带选项或猜测: %r" % ln)

    def test_ring1_questions_carry_choice_on_same_line(self):
        self.check(Ws(self).start.stdout)

    def test_ring5_deny_question_has_two_options(self):
        w = Ws(self)
        w.ring1()
        for r_, sets in {2: ["jargon=开票"], 3: ["real_competitors=Rival", "compliance=没有"],
                         4: ["capacity=每月 4 篇"]}.items():
            w.ok(w.ob("show", "--ring", str(r_)))
            w.ok(w.ob("answer", "--ring", str(r_), *sum((["--set", s] for s in sets), []),
                      "--quote", "第 %d 环的回答是 %s" % (r_, ";".join(sets)), *(NO_AUDIT if r_ == 4 else []), "--confirm"))
        self.check(w.ok(w.ob("show", "--ring", "5")).stdout)


# ---------------------------------------------------------------------------
# #7 用户确认的阶段,重算不改回
# ---------------------------------------------------------------------------

class ConfirmedStageTests(unittest.TestCase):
    def test_stage_corrected_after_ring1_survives_status(self):
        w = Ws(self)
        w.ring1()
        self.assertNotIn(STAGE_NAMES[5], w.ok(w.ob("status")).stdout)
        w.ok(w.ob("answer", "--ring", "1", "--correct", "stage=5", "--quote", "其实我们正在改版,换了新域名"))
        self.assertEqual(w.prof()["stage"]["value"], 5)
        self.assertIn(STAGE_NAMES[5], w.ok(w.ob("status")).stdout)

    def test_stage_confirmed_in_ring1_survives_status(self):
        w = Ws(self)
        w.ring1("--correct", "stage=5")
        self.assertIn(STAGE_NAMES[5], w.ok(w.ob("status")).stdout)


# ---------------------------------------------------------------------------
# #8 档案顶层 _schema 映射不算手改
# ---------------------------------------------------------------------------

class SchemaNotTamperTests(unittest.TestCase):
    def test_agent_added_schema_mapping_not_flagged(self):
        w = Ws(self)
        w.ring1()
        p = os.path.join(w.ws, "context", "profile.json")
        prof = w.prof()
        prof["_schema"] = {"product.name": ["facts", {"key": "product.name"}, "value"],
                           "stage": ["stage", "value"]}   # 被测在 change 转录里自己加的那种映射
        with open(p, "w", encoding="utf-8") as f:
            json.dump(prof, f, ensure_ascii=False, indent=1)
        r = w.ok(w.ob("status"))
        self.assertNotRegex(r.stdout + r.stderr, r"被手改|手改过")
        self.assertEqual(w.prof()["rings"]["1"]["status"], "confirmed")


# ---------------------------------------------------------------------------
# #1 #2 本机站没加 --allow-local:直接报错、什么都不写;重跑 start 重新读
# ---------------------------------------------------------------------------

class StartRescanTests(unittest.TestCase):
    def test_loopback_without_allow_local_writes_nothing(self):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="obb5_lo_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        r = run("onboard.py", ["start", "--site", "http://127.0.0.1:9/", "--repo", "."], tmp)
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("--allow-local", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(tmp, "seo-ops", "context", "profile.json")))

    def test_rerun_start_before_ring1_rescans(self):
        w = Ws(self, base_scan(lines=None))
        self.assertIsNone(w.fact("product.lines"))
        w.write_scan(base_scan())
        w.ok(w.ob("start", "--site", "https://acme.example", "--scan", "scan.json"))
        self.assertEqual(w.fact("product.lines"), ["Invoicing", "Time tracking", "Client portal"])


# ---------------------------------------------------------------------------
# #1 #5 只给仓库:读出名字、定价、语言;仓库里有改版计划按「改版」猜
# ---------------------------------------------------------------------------

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class RepoOnlyTests(unittest.TestCase):
    def repo(self, migration=False):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="obb5_repo_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        write(os.path.join(tmp, "package.json"), json.dumps({"name": "ledgerly", "dependencies": {"next": "14.2.0"}}))
        write(os.path.join(tmp, "app", "layout.tsx"),
              'export const metadata = { title: "Ledgerly", description: "Invoices for small studios" };\n'
              'export default function RootLayout({ children }) {\n'
              '  return <html lang="en"><body>{children}</body></html>;\n}\n')
        write(os.path.join(tmp, "app", "page.tsx"),
              "export default function Home() { return <main><h1>Ledgerly</h1></main>; }\n")
        write(os.path.join(tmp, "app", "pricing", "page.tsx"),
              "export default function Pricing() {\n  return <main><h1>Pricing</h1>"
              "<p>Starter $9/month</p><p>Studio $29/month</p></main>;\n}\n")
        if migration:
            write(os.path.join(tmp, "MIGRATION.md"),
                  "# Domain migration plan\n\nMove from old-ledgerly.example to ledgerly.example; 301 every URL.\n")
        return tmp

    def scan(self, repo):
        r = run("product_scan.py", ["--repo", repo, "--out", os.path.join(repo, "scan.json")], repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(repo, "scan.json"), encoding="utf-8") as f:
            return json.load(f)

    def test_repo_only_scan_reads_name_pricing_languages(self):
        s = self.scan(self.repo())
        facts = {f["key"]: f.get("value") for f in s["facts"]}
        self.assertEqual(str(facts.get("product.name")).lower(), "ledgerly")
        self.assertTrue(facts.get("pricing.model"), facts)
        self.assertEqual(facts.get("market.languages"), ["en"])

    def test_migration_plan_in_repo_guesses_change_stage(self):
        repo = self.repo(migration=True)
        r = run("onboard.py", ["start", "--repo", "."], repo)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(repo, "seo-ops", "context", "profile.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["stage"]["value"], 5)
        self.assertIn(STAGE_NAMES[5], user_block(r.stdout))


# ---------------------------------------------------------------------------
# #6 用户确认只做一个市场(「中国大陆、简体中文」)→ 方案里不出 hreflang
# ---------------------------------------------------------------------------

def leaves(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from leaves(v)
    elif isinstance(x, list):
        for v in x:
            yield from leaves(v)
    elif isinstance(x, str):
        yield x


class SingleMarketPlanTests(unittest.TestCase):
    def test_one_market_plan_has_no_hreflang(self):
        w = Ws(self)
        w.ring1("--correct", "stage=0")      # 想法阶段:方案带「技术选型先过 SEO 约束」那条
        w.rest(market="中国大陆、简体中文")
        r = run("plan.py", ["build", "--ws", w.ws], w.tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(w.ws, "plan", "plan.json"), encoding="utf-8") as f:
            plan = json.load(f)
        hits = [t for it in plan["items"] for t in leaves(it) if "hreflang" in t.lower()]
        self.assertEqual(hits, [])


# ---------------------------------------------------------------------------
# #9 上线前预览站 robots 全封:体检照爬,全封记成一条发现
# ---------------------------------------------------------------------------

class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class TriageRobotsTests(unittest.TestCase):
    def test_local_robots_block_all_is_finding_not_blocker(self):
        tmp = os.path.realpath(tempfile.mkdtemp(prefix="obb5_robots_"))
        self.addCleanup(shutil.rmtree, tmp, True)
        site = os.path.join(tmp, "site")
        write(os.path.join(site, "index.html"),
              '<!doctype html><html lang="en"><head><title>Preview</title>'
              '<meta name="description" content="A local preview"></head><body><h1>Hi</h1>'
              '<a href="/about.html">About</a></body></html>')
        write(os.path.join(site, "about.html"),
              '<!doctype html><html lang="en"><head><title>About</title></head><body><h1>About</h1></body></html>')
        write(os.path.join(site, "robots.txt"), "User-agent: *\nDisallow: /\n")
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=site))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        url = "http://127.0.0.1:%d/" % srv.server_address[1]
        ws = os.path.join(tmp, "seo-ops")
        self.assertEqual(run("project.py", ["init", "--site", url, "--dir", ws], tmp).returncode, 0)
        r = run("project.py", ["run", "triage", "--dir", ws, "--allow-local", "--max", "3", "--json"], tmp)
        out = json.loads(r.stdout)
        crawl = next(s for s in out["steps"] if s["name"] == "crawl")
        self.assertTrue(crawl["ok"], crawl)
        self.assertIn("robots", json.dumps(out.get("findings") or out.get("summary", {}).get("findings"),
                                           ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
