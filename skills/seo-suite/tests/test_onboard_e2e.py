#!/usr/bin/env python3
"""开局 6 环端到端回归:5 个合成产品各走一遍 start → show / answer ×6 → plan.py build(stdlib unittest,零外网)。

为什么要这一层:单元测试只验单个函数,上一轮单测全绿、行为评测却回退了(第 1 环事实缺键、列表存成一整条字符串、
问题块的阶段名不对、单市场方案仍出 hreflang、确认过的阶段被改回、档案被判手改)。这里把脚本当黑盒按 agent 的
走法走一遍,断言只看脚本落盘的东西和「原样发给用户」那一块。

期望值来源(不从实现反推):
- tools/evals/onboarding/scenarios.json(独立出题人写的):每个场景的工作区搭法、模拟用户每环的回话、方案 must_not 的
  top / max;
- tools/evals/onboarding/answers/<产品>.json(同上):stage、stage_must_not_match;
- 判定直接调 tools/evals/onboarding/grade.py 的函数(question_lines、has_choice、hits、fact_raw、unwrap、profile_stage、
  plan_items、c_must_not),和评测用同一把尺子;判分器读不到的(块里的「← 出处」、编号行)按 criteria_defs 的原文写断言。
- 测试扮演 agent:每环把屏幕上「原样发给用户」那一块当贴出的文本,答案从模拟用户的原话里摘(PLAYS),用屏幕上教的
  写法和分隔符调 answer / note;屏幕说本机站点要加 --allow-local 就加。launched、mature 两场用户没列产品线,
  agent 照站点导航补产品线的那条 --correct 用的是第 5 批第 2 轮试跑转录里被测的原命令(含它用的分隔符)。
- 7 个事实键是评测 prompt 写明「至少含这些键」的那 7 个;「列表字段是多项列表」按评测 prompt 的「product.lines(列表)、
  customers(列表)」:值是列表、没有一项里还夹着分隔符;用户或材料给了几条产品线的,条数 ≥ 2。
"""
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import types
import unittest
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
ROOT = os.path.dirname(os.path.dirname(BASE))
EVAL = os.path.join(ROOT, "tools", "evals", "onboarding")
LS = os.path.join(ROOT, "tools", "testsites", "lifecycle_sites.py")
sys.path.insert(0, EVAL)
import grade as G  # noqa: E402

PY = sys.executable
BLOCK_START = "===== 下面这块原样发给用户"
BLOCK_END = "===== 原样发给用户到这里为止"
FACT_KEYS = ("product.name", "product.one_liner", "product.lines", "pricing.model", "conversion.primary",
             "customers", "market.languages")
LIST_KEYS = ("product.lines", "customers", "market.languages")
SEPS = re.compile(r"[;；|｜、\n]")

with open(os.path.join(EVAL, "scenarios.json"), encoding="utf-8") as _f:
    SCENARIOS = {s["product"]: s for s in json.load(_f)["scenarios"]}
with open(os.path.join(BASE, "data", "lifecycle.json"), encoding="utf-8") as _f:
    STAGE_NAMES = {s["id"]: s["name"] for s in json.load(_f)["stages"]}

# agent 从模拟用户每环的回话里摘出的答案(键 = 问题 id;列表值按屏幕教的分隔符拼)。
# 回话里没说到的问题记 --unknown(屏幕:用户说不知道加 --unknown)。
# brief:只有 idea 的工作区里有 brief.md(scenarios.json 的 setup),agent 照屏幕「档案还缺」的键从里面摘。
PLAYS = {
    "idea": {
        "brief": {"product.name": "宠账本 PetLedger",
                  "product.one_liner": "给养猫养狗的年轻人用的宠物健康记账 App——疫苗驱虫按时提醒、病历和化验单拍照存档、附近宠物医院价格对比",
                  "product.lines": ["健康提醒", "病历档案", "医院比价"],
                  "pricing.model": "基础版免费(1 只宠物);会员 ¥18/月 或 ¥168/年",
                  "customers": ["中国一二线城市 22–35 岁、养猫或狗的上班族(主要)", "多宠家庭、刚领养的新手主人(次要)"],
                  "market.languages": ["zh-CN"]},
        "stage_from_reply": 0,
        1: {"profile_ok": "A", "main_line": "健康提醒", "conversion": "上线前攒候补名单,先攒 2000 个",
            "customers": "一二线城市养猫狗的上班族"},
        2: {"jargon": "毛孩子、铲屎官、猫三联、狂犬疫苗",
            "pre_purchase_questions": ["猫咪疫苗时间表", "狗狗驱虫多久一次", "附近宠物医院多少钱"]},
        3: {"real_competitors": ["宠物医院自己的小程序", "宠物服务平台"]},
        4: {"capacity": "一个人加一个兼职设计,每周 1 篇", "history": "没有", "team_budget": "每月预算 2000 元以内",
            "access": "都没有"},
        5: {"market_first": "中国大陆、简体中文", "deny_topics": "看病诊断类内容"},
        6: {"approve_plan": "可以", "kpi_target": "上线前 3 个月候补名单 2000 人"},
    },
    "prelaunch": {
        "stage_from_reply": 1, "triage": True,
        1: {"profile_ok": "A", "main_line": "Invoicing", "conversion": "注册(trial sign-ups)",
            "customers": ["Freelance designers and illustrators", "studios"]},
        2: {"jargon": ["invoice template for designers", "how to charge clients as a freelancer",
                       "freelance time tracker", "getting paid", "chasing invoices"]},
        3: {"real_competitors": ["FreshBooks", "Bonsai", "HoneyBook"]},
        4: {"capacity": "two people, about 2 posts a month", "history": "没有", "team_budget": "budget is basically zero",
            "access": "都没有"},
        5: {"market_first": "US first, then UK and Canada, English only", "deny_topics": "tax or legal advice content"},
        6: {"approve_plan": "可以", "kpi_target": "300 trial sign-ups from organic search in the first 90 days after launch"},
    },
    "launched": {
        "stage_from_reply": 2,
        "correct1": ["product.lines=Monthly subscription;Single-origin bags (one-off);Pour-over kits and gear"],
        1: {"profile_ok": "A", "main_line": "Monthly subscription", "conversion": "付费 / 下单(subscription starts)",
            "customers": "US home brewers"},
        2: {"jargon": ["v60 ratio", "french press ratio", "best coffee subscription", "pour-over", "light roast",
                       "single origin"]},
        3: {"real_competitors": ["Trade Coffee", "Onyx", "Counter Culture", "Blue Bottle"], "ignore": "Amazon listings"},
        4: {"capacity": "two people, one brew guide a week", "history": "没有", "access": "都有"},
        5: {"market_first": "US only, English", "deny_topics": "caffeine health claims"},
        6: {"approve_plan": "可以", "kpi_target": "30 new subscriptions a month from organic search by the end of Q1 2027"},
    },
    "mature": {
        "stage_from_reply": 4,
        "correct1": ["product.lines=Gear reviews|Trail guides|Trailmark Pro"],
        1: {"profile_ok": "A", "main_line": "Gear reviews", "conversion": "Affiliate click-outs",
            "customers": "US backpackers and day hikers"},
        2: {"jargon": ["best ultralight tent", "osprey exos vs gregory focal", "trail name plus permit", "base weight",
                       "thru-hike", "ultralight"]},
        3: {"real_competitors": ["OutdoorGearLab", "CleverHiker", "Switchback Travel", "REI Expert Advice"]},
        4: {"capacity": "me and one freelancer, about 4 updates a month", "history": "没有", "access": "都有"},
        5: {"market_first": "US first; UK and Canada English readers later",
            "deny_topics": "sponsored posts dressed up as reviews"},
        6: {"approve_plan": "可以", "kpi_target": "back to 1,800 clicks per 28 days within 90 days"},
    },
    "change": {
        "stage_from_reply": 5,
        1: {"profile_ok": "A", "main_line": "Sensor Pro", "conversion": "付费 / 下单(store sales)",
            "customers": "home gardeners and houseplant owners in the US and Germany"},
        2: {"jargon": ["when to water houseplants", "soil moisture sensor", "Bodenfeuchtesensor", "overwatering",
                       "Gießen"]},
        3: {"real_competitors": ["Xiaomi Mi Flora", "Ecowitt", "Parrot"]},
        4: {"capacity": "three people, about 2 articles a month", "history": "没有",
            "access": "部分有(GA4 on, no Search Console access)"},
        5: {"market_first": "US and Germany, English and German", "deny_topics": "Don't touch the pricing page copy"},
        6: {"approve_plan": "可以", "kpi_target": "no more than a 5% drop in organic clicks in the first 4 weeks"},
    },
}


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def user_block(screen):
    a = screen.index(BLOCK_START)
    b = screen.index(BLOCK_END, a)
    return screen[screen.index("\n", a) + 1:b]


class Flow:
    """一个场景的工作区、本机站点和 agent 走法。"""

    def __init__(self, tc, product):
        self.tc, self.product = tc, product
        self.sc, self.play = SCENARIOS[product], PLAYS[product]
        with open(os.path.join(EVAL, "answers", product + ".json"), encoding="utf-8") as f:
            self.ans = json.load(f)
        self.tmp = os.path.realpath(tempfile.mkdtemp(prefix="e2e_%s_" % product))
        tc.addCleanup(shutil.rmtree, self.tmp, True)
        self.proc = None
        self.setup()

    # ---- 搭场景(照 scenarios.json 的 setup)
    def setup(self):
        setup = self.sc["setup"]
        out = os.path.join(self.tmp, "product")
        port = free_port()
        self.site = "http://127.0.0.1:%d" % port if "serve" in setup else None
        cmd = [PY, LS, "build", "--product", self.product, "--out", out]
        if self.site:
            cmd += ["--base", self.site]
        if self.product == "change":
            cmd += ["--state", "before"]
        subprocess.run(cmd, check=True, capture_output=True)
        if self.product in ("idea", "prelaunch", "change"):
            self.ws = os.path.join(out, "repo")
            if self.product == "idea":
                shutil.copy(os.path.join(out, "brief.md"), self.ws)
        else:                                       # 新目录:README 写站点地址,GSC 导出复制成 data/
            self.ws = os.path.join(self.tmp, "ws")
            os.makedirs(self.ws)
            name = {"launched": "Northfold Coffee 官网", "mature": "Trailmark Guides"}[self.product]
            with open(os.path.join(self.ws, "README.md"), "w", encoding="utf-8") as f:
                f.write("%s,站点在 %s\n" % (name, self.site))
            shutil.copytree(os.path.join(out, "gsc"), os.path.join(self.ws, "data"))
        if self.site:
            serve_dir = os.path.join(out, "repo" if self.product == "change" else "site")
            self.proc = subprocess.Popen([PY, LS, "serve", "--dir", serve_dir, "--port", str(port)],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.tc.addCleanup(self.stop)
            for _ in range(100):
                try:
                    urllib.request.urlopen(self.site + "/", timeout=1).read()
                    break
                except Exception:  # noqa: BLE001
                    time.sleep(0.1)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()                  # 按 PID 停自己起的服务
            self.proc.wait(5)

    def run(self, script, args):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        return subprocess.run([PY, os.path.join(SCRIPTS, script), *args], cwd=self.ws, capture_output=True,
                              text=True, encoding="utf-8", env=env)

    def ob(self, *args):
        r = self.run("onboard.py", list(args))
        self.tc.assertEqual(r.returncode, 0, "%s onboard.py %s\n%s%s" % (self.product, " ".join(args)[:300],
                                                                        r.stdout[-800:], r.stderr[-800:]))
        return r

    # ---- agent 的走法
    def start(self):
        args = ["start"] + (["--site", self.site] if self.site else []) + ["--repo", "."]
        r = self.run("onboard.py", args)
        said = r.stdout + r.stderr
        if "--allow-local" in said and ("SSRF" in said or r.returncode == 2):
            r = self.run("onboard.py", args + ["--allow-local"])   # 屏幕说本机站点加 --allow-local
        self.tc.assertEqual(r.returncode, 0, r.stdout[-800:] + r.stderr[-800:])
        return r.stdout

    def sep(self, screen):
        m = re.search(r"列表项用「(.+?)」", screen)
        return m.group(1) if m else ";"

    def val(self, v, sep):
        return sep.join(v) if isinstance(v, list) else v

    def notes_from_brief(self, screen):
        brief = self.play.get("brief") or {}
        m = re.search(r"档案还缺:([A-Za-z._、,, ]+)", screen)
        missing = [k.strip() for k in re.split(r"[、,,\s]+", m.group(1)) if k.strip()] if m else []
        sep = self.sep(screen)
        for k in missing:
            if k in brief:
                self.ob("note", "--ring", "1", "--key", k, "--value", self.val(brief[k], sep), "--source", "brief.md")
        return missing

    def ids(self, screen):
        m = re.search(r"问题编号对应的 id[^:]*:(.*)", screen)
        return re.findall(r"\[id=([a-z_]+)\]", m.group(1)) if m else []

    def answer(self, r, screen, block):
        sep = self.sep(screen)
        reply = self.sc["simulated_user"][str(r)][0]
        args = ["answer", "--ring", str(r)]
        asked = self.ids(screen)
        mine = self.play.get(r) or {}
        for k in asked:
            if k in mine:
                args += ["--set", "%s=%s" % (k, self.val(mine[k], sep))]
            elif k != "main_line":
                args += ["--unknown", k]
        if r == 1:
            for c in self.play.get("correct1") or []:
                args += ["--correct", c]
            want = self.play.get("stage_from_reply")
            line = next((ln for ln in block.splitlines() if ln.startswith("- 产品阶段")), "")
            if want is not None and STAGE_NAMES[want] not in line.split("←")[0]:
                args += ["--correct", "stage=%d" % want]   # 用户回话里说了阶段,和草稿的猜测不同就改
        return self.ob(*(args + ["--quote", reply, "--confirm"]))

    def profile(self):
        with open(os.path.join(self.ws, "seo-ops", "context", "profile.json"), encoding="utf-8") as f:
            return json.load(f)

    # ---- 断言
    def check_block(self, r, block):
        tc, p = self.tc, self.product
        tail = block[block.index("## 问用户"):] if "## 问用户" in block else ""
        tc.assertTrue(tail, "%s 第 %d 环的块里没有问题" % (p, r))
        qs = G.question_lines(tail)
        tc.assertTrue(qs, "%s 第 %d 环没有编号问题:\n%s" % (p, r, tail))
        for ln in tail.splitlines()[1:]:
            if "?" in ln or "？" in ln:
                tc.assertRegex(ln, r"^\d+\. ", "%s 第 %d 环有不是「数字. 问题?」的问句行:%s" % (p, r, ln))
        bad = [q["text"] for q in qs if not q["has_choice"]]
        tc.assertEqual(bad, [], "%s 第 %d 环这些问题没带同一行选项也没带下一行「我猜」" % (p, r))
        for ln in block.splitlines():
            if ln.startswith("- "):
                tc.assertIn("←", ln, "%s 第 %d 环事实行没有「← 出处」:%s" % (p, r, ln))
        if r == 1:
            name = STAGE_NAMES[self.ans["stage"]]
            tc.assertTrue(G.hits(block, [name]), "%s 第 1 环的块里没有阶段名「%s」:\n%s" % (p, name, block))

    def check_ring1_profile(self):
        tc, p = self.tc, self.product
        prof = self.profile()
        for k in FACT_KEYS:
            raw, where = G.fact_raw(prof, k)
            tc.assertIsNot(raw, G.MISSING, "%s 第 1 环确认后档案缺 %s" % (p, k))
        for k in LIST_KEYS:
            v = G.unwrap(G.fact_raw(prof, k)[0])
            if v is None or v is G.MISSING:
                continue
            tc.assertIsInstance(v, list, "%s %s 不是列表:%r" % (p, k, v))
            joined = [x for x in v if SEPS.search(str(x))]
            tc.assertEqual(joined, [], "%s %s 有一项里还夹着分隔符(整条没拆):%r" % (p, k, v))
        lines = G.unwrap(G.fact_raw(prof, "product.lines")[0])
        tc.assertIsInstance(lines, list, "%s product.lines 没有值" % p)
        tc.assertGreaterEqual(len(lines) if isinstance(lines, list) else 0, 2, "%s product.lines 应是多项:%r" % (p, lines))
        st = self.ob("status")
        first = st.stdout.splitlines()[0]
        sid = (prof.get("stage") or {}).get("value")
        tc.assertIn(STAGE_NAMES[sid], first, "%s 确认的阶段是 %s,status 显示:%s" % (p, STAGE_NAMES[sid], first))

    def check_end(self):
        tc, p = self.tc, self.product
        prof = self.profile()
        tc.assertIsInstance(prof.get("_schema"), dict, "%s 档案没有 _schema" % p)
        got, where = G.profile_stage(prof)
        tc.assertEqual(where, "_schema")
        tc.assertEqual(got, prof["stage"]["value"])
        st = self.ob("status")
        tc.assertNotIn("手改", st.stdout + st.stderr, "%s status 报手改:%s" % (p, st.stderr))
        items, src = G.plan_items(self.ws)
        tc.assertTrue(items, "%s 没有方案条目" % p)
        cr = next(c for c in self.sc["criteria"] if c["id"] == "must_not_hits_max")
        cx = types.SimpleNamespace(items=items, items_src=src, ans=self.ans)
        ok, ev = G.c_must_not(cx, cr)
        tc.assertTrue(ok, "%s 方案命中 must_not:%s" % (p, json.dumps(ev["hits"], ensure_ascii=False)[:800]))

    def go(self):
        screen = self.start()
        if self.notes_from_brief(screen):
            screen = self.ob("show", "--ring", "1").stdout
        for r in range(1, 7):
            if r > 1:
                if r == 4 and self.play.get("triage"):
                    self.triage()
                if r == 6:
                    b = self.run("plan.py", ["build", "--ws", "seo-ops"])
                    self.tc.assertEqual(b.returncode, 0, b.stderr[-600:])
                screen = self.ob("show", "--ring", str(r)).stdout
                if r == 4 and self.audit_from_screen(screen):
                    screen = self.ob("show", "--ring", str(r)).stdout
            block = user_block(screen)
            self.check_block(r, block)
            self.answer(r, screen, block)
            if r == 1:
                self.check_ring1_profile()
        b = self.run("plan.py", ["build", "--ws", "seo-ops"])
        self.tc.assertEqual(b.returncode, 0, b.stderr[-600:])
        self.check_end()

    def audit_from_screen(self, screen):
        """照第 4 环「agent 先做」打印的完整命令跑体检(改版阶段还有基线);站点已上线的场景必须打印出来。"""
        ran = []
        for ln in screen.splitlines():
            m = re.match(r"^- (体检|改版前存基线)[^:]*:(python3 .+)$", ln)
            if not m:
                continue
            for cmd in m.group(2).split(" && "):
                argv = shlex.split(cmd)
                if "triage" in argv:
                    argv += ["--max", "10"]
                r = subprocess.run([PY] + argv[1:], cwd=self.ws, capture_output=True, text=True, encoding="utf-8")
                self.tc.assertNotEqual(r.returncode, 2, "%s 照抄 %s 报用法错:%s" % (self.product, cmd, r.stderr[-600:]))
            ran.append(m.group(1))
        live = self.ans["stage"] >= 2
        self.tc.assertEqual("体检" in ran, live, "%s 第 4 环体检命令:%s" % (self.product, ran))
        self.tc.assertEqual("改版前存基线" in ran, self.ans["stage"] == 5, "%s 第 4 环基线命令:%s" % (self.product, ran))
        if live and self.site and "127.0.0.1" in self.site:
            tri = next(ln for ln in screen.splitlines() if ln.startswith("- 体检"))
            self.tc.assertIn("--allow-local", tri)
        return ran

    def triage(self):
        """上线前的本机预览站 robots 全封:体检不被它挡住,「robots 全封」作为一条发现报出来。"""
        r = self.run("project.py", ["run", "triage", "--dir", "seo-ops", "--allow-local", "--max", "10", "--json"])
        self.tc.assertNotEqual(r.returncode, 2, r.stderr[-600:])
        tri = json.loads(r.stdout)
        crawl = next(s for s in tri["steps"] if s["name"] == "crawl")
        self.tc.assertTrue(crawl["ok"], crawl)
        audit = next(s for s in tri["steps"] if s["name"] == "audit")
        self.tc.assertTrue(audit["ok"], audit)
        found = json.dumps(tri.get("findings") or [], ensure_ascii=False)
        self.tc.assertIn("robots", found)
        self.tc.assertIn("Disallow", found)


class _Soft:
    """E2E_SOFT=1 时断言失败只记下、接着走(看一个场景一共红在哪几处;默认关)。"""

    def __init__(self, tc):
        self._tc, self.failures = tc, []

    def __getattr__(self, name):
        attr = getattr(self._tc, name)
        if not name.startswith("assert"):
            return attr

        def soft(*a, **k):
            try:
                return attr(*a, **k)
            except AssertionError as e:
                self.failures.append(str(e).splitlines()[0][:300])
        return soft


def _go(tc, product):
    if os.environ.get("E2E_SOFT") != "1":
        return Flow(tc, product).go()
    soft = _Soft(tc)
    try:
        Flow(soft, product).go()
    except Exception as e:  # noqa: BLE001
        soft.failures.append("中断:%s: %s" % (type(e).__name__, str(e)[:300]))
    tc.assertFalse(soft.failures, "\n".join(["%s 一共 %d 处:" % (product, len(soft.failures))] + soft.failures))


class OnboardEndToEnd(unittest.TestCase):
    def test_idea(self):
        _go(self, "idea")

    def test_prelaunch(self):
        _go(self, "prelaunch")

    def test_launched(self):
        _go(self, "launched")

    def test_mature(self):
        _go(self, "mature")

    def test_change(self):
        _go(self, "change")


if __name__ == "__main__":
    unittest.main()
